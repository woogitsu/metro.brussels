using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Text;
using System.Text.Json;
using MetroBxl.Sim.Line;
using MetroBxl.Sim.Physics;

namespace MetroBxl.Sim.Signalling;

/// <summary>
/// Wariant ochrony pociągu dla trybu <c>classic_2026</c>.
///
/// Nazwy pochodzą wprost z <c>data/signalling/ground-truth.json</c>,
/// <c>modes.classic_2026</c>: <c>lines_1_5 = legacy_fixed_block</c>,
/// <c>lines_2_6 = legacy_with_kcv</c>. To rozróżnienie **nie jest kosmetyczne** —
/// KCV jest potwierdzony przez STIB dla linii 2/6 i tylko dla nich. Plan pakietu A
/// (L1_A, czyli linia 1) nie ma prawa deklarować KCV.
/// </summary>
public enum ProtectionVariant
{
    /// <summary>Linie 1/5: bloki stałe bez KCV.</summary>
    LegacyFixedBlock,

    /// <summary>Linie 2/6: bloki stałe plus interfejs KCV.</summary>
    LegacyWithKcv,
}

/// <summary>
/// Jedno założenie planu sygnalizacji. Odpowiednik <c>BrakingAssumption</c> z T-311,
/// ale z wartością tekstową: część założeń to liczby, a część to **reguły** („jeden
/// blok na międzystacje"), których nie da się zapisać jako <c>double</c>.
/// </summary>
/// <param name="Name">Nazwa pola planu albo reguły.</param>
/// <param name="Value">Wartość albo opis reguły.</param>
/// <param name="Reason">Dlaczego taka i czego brakuje, żeby przestała być założeniem.</param>
public readonly record struct SignallingAssumption(string Name, string Value, string Reason)
{
    /// <inheritdoc/>
    public override string ToString() => $"{Name} = {Value} — {Reason}";
}

/// <summary>
/// Plan bloków i tras dla jednej osi pakietu w trybie <c>classic_2026</c>.
///
/// <para><b>To jest <c>design_model</c> w całości i plik mówi to wprost.</b>
/// <c>docs/10-signalling-ground-truth.md</c>: „Nie ma podstawy do nazywania naszej
/// tabeli bloków «rzeczywistym planem STIB»". Dlatego plan mieszka w
/// <c>data/design/signalling/</c>, a nie w <c>data/network/</c> ani w
/// <c>data/track/</c>, i dlatego <see cref="FromJson"/> **odmawia wczytania** planu,
/// który podaje status inny niż <c>design_model</c> bez identyfikatora źródła.</para>
///
/// <para><b>Skąd wzięły się granice bloków.</b> Z reguły, nie z liczb: blok peronowy
/// długości jednego składu M7 (94,0 m, <c>parameters.length_m</c>, status <c>spec</c>)
/// wyśrodkowany na kilometrażu stacji, a między dwoma blokami peronowymi dokładnie
/// jeden blok szlakowy. Reguła daje więc podział, w którym jedyną liczbą spoza danych
/// jest sama reguła — kilometraże stacji pochodzą z <c>data/track/*.json</c>, a długość
/// składu z rejestru M7. <see cref="FromAxis"/> jest wykonaniem tej reguły i to on
/// wyprodukował plik w <c>data/design/signalling/</c>.</para>
///
/// <para><b>Wymienialność.</b> Kod nie zna ani jednej granicy bloku: wszystkie wchodzą
/// z pliku. Podmiana pliku na plan z prawdziwym źródłem nie wymaga zmiany w
/// <c>src/Sim/</c> — wymaga skasowania jednego testu, który przypina bieżący plan do
/// reguły generowania, i to jest jedyne miejsce, w którym reguła jest zapisana na stałe.</para>
/// </summary>
public sealed class SignallingPlan
{
    /// <summary>Wersja schematu pliku planu.</summary>
    public const int CurrentSchemaVersion = 1;

    /// <summary>Zaokrąglenie granic bloków w pliku: milimetr.</summary>
    public const int BoundaryDecimals = 3;

    private readonly Block[] _blocks;
    private readonly Route[] _routes;
    private readonly double[] _starts;
    private readonly Dictionary<string, int> _byId;
    private readonly string[] _unknownParameters;

    private SignallingPlan(
        string planId,
        string mode,
        string axisId,
        ParameterStatus status,
        ProtectionVariant variant,
        bool requireRoute,
        double permittedSpeedMps,
        double authorityMarginM,
        double platformBlockLengthM,
        Block[] blocks,
        Route[] routes,
        string[] unknownParameters)
    {
        PlanId = planId;
        Mode = mode;
        AxisId = axisId;
        Status = status;
        Variant = variant;
        RequireRoute = requireRoute;
        PermittedSpeedMps = permittedSpeedMps;
        AuthorityMarginM = authorityMarginM;
        PlatformBlockLengthM = platformBlockLengthM;
        _blocks = blocks;
        _routes = routes;
        _unknownParameters = unknownParameters;

        _starts = new double[blocks.Length];
        _byId = new Dictionary<string, int>(blocks.Length, StringComparer.Ordinal);
        for (var i = 0; i < blocks.Length; i++)
        {
            _starts[i] = blocks[i].StartM;
            if (!_byId.TryAdd(blocks[i].Id, i))
            {
                throw new ArgumentException($"powtórzony identyfikator bloku: {blocks[i].Id}", nameof(blocks));
            }

            if (blocks[i].EndM <= blocks[i].StartM)
            {
                throw new ArgumentException($"blok {blocks[i].Id} ma niedodatnią długość", nameof(blocks));
            }

            if (i > 0 && Math.Abs(blocks[i].StartM - blocks[i - 1].EndM) > TrackAxis.PositionEpsilonM)
            {
                throw new ArgumentException(
                    $"bloki {blocks[i - 1].Id} i {blocks[i].Id} nie stykają się — plan musi być ciągły",
                    nameof(blocks));
            }
        }

        foreach (var route in routes)
        {
            foreach (var id in route.BlockIds)
            {
                if (!_byId.ContainsKey(id))
                {
                    throw new ArgumentException($"trasa {route.Id} wskazuje nieistniejący blok {id}", nameof(routes));
                }
            }
        }
    }

    /// <summary>Identyfikator planu.</summary>
    public string PlanId { get; }

    /// <summary>Tryb z <c>data/signalling/ground-truth.json</c>; dla T-313 zawsze <c>classic_2026</c>.</summary>
    public string Mode { get; }

    /// <summary>Identyfikator osi pakietu, np. <c>L1_A</c>.</summary>
    public string AxisId { get; }

    /// <summary>Pochodzenie planu. Dla każdego planu bez źródła: <see cref="ParameterStatus.DesignModel"/>.</summary>
    public ParameterStatus Status { get; }

    /// <summary>Wariant ochrony pociągu.</summary>
    public ProtectionVariant Variant { get; }

    /// <summary>
    /// Czy movement authority wymaga zaryglowanej trasy. Włączone znaczy, że sam brak
    /// konfliktu nie wystarcza do jazdy — trzeba mieć trasę, tak jak na linii z
    /// nastawniami.
    /// </summary>
    public bool RequireRoute { get; }

    /// <summary>
    /// Prędkość dopuszczalna planu. <c>design_model</c>: R-006 (<c>reports/R-006-line-speed.md</c>)
    /// pokazuje, że żaden dokument STIB nie podaje prędkości dopuszczalnej na torze,
    /// a 72 km/h wolno używać wyłącznie jako jawnie zadeklarowanego parametru scenariusza.
    /// </summary>
    public double PermittedSpeedMps { get; }

    /// <summary>
    /// Zapas między końcem authority a początkiem obszaru chronionego. Rzeczywistego
    /// overlapu STIB nie ma w żadnym źródle (<c>unknown_parameters</c>: „ATP/ATO braking
    /// curves and safety margins"), więc plan pakietu A ma tu **zero** — model nie
    /// wymyśla zapasu, którego nie zna. Pole istnieje po to, żeby dało się go wpisać,
    /// gdy źródło się znajdzie.
    /// </summary>
    public double AuthorityMarginM { get; }

    /// <summary>Długość bloku peronowego użyta przez regułę generowania.</summary>
    public double PlatformBlockLengthM { get; }

    /// <summary>Bloki w kolejności chainage; ciągłe i bez dziur.</summary>
    public IReadOnlyList<Block> Blocks => _blocks;

    /// <summary>Trasy w kolejności deklaracji.</summary>
    public IReadOnlyList<Route> Routes => _routes;

    /// <summary>Lista parametrów, których plan świadomie nie zawiera — przepisana z pliku.</summary>
    public IReadOnlyList<string> UnknownParameters => _unknownParameters;

    /// <summary>Chainage początku planu.</summary>
    public double StartM => _blocks[0].StartM;

    /// <summary>Chainage końca planu.</summary>
    public double EndM => _blocks[^1].EndM;

    /// <summary>Katalog założeń planu, w kolejności deklaracji — czyli stałej.</summary>
    public IReadOnlyList<SignallingAssumption> Assumptions => new[]
    {
        new SignallingAssumption(
            "block_boundaries",
            string.Create(CultureInfo.InvariantCulture, $"{_blocks.Length} bloków na osi {AxisId}"),
            "granice bloków STIB nie są publiczne (data/signalling/ground-truth.json: " +
            "\"exact fixed-block boundaries and lengths\"); podział wynika z reguły " +
            "blok peronowy + jeden blok szlakowy na międzystacje, a nie z planu STIB"),
        new SignallingAssumption(
            nameof(PlatformBlockLengthM),
            PlatformBlockLengthM.ToString("R", CultureInfo.InvariantCulture) + " m",
            "długość bloku peronowego przyjęta jako długość składu M7 z rejestru " +
            "(parameters.length_m, status spec). Sama liczba ma źródło, ale decyzja " +
            "\"blok peronowy ma długość jednego składu\" źródła nie ma"),
        new SignallingAssumption(
            nameof(PermittedSpeedMps),
            Units.MpsToKmh(PermittedSpeedMps).ToString("R", CultureInfo.InvariantCulture) + " km/h",
            "reports/R-006-line-speed.md: żaden dokument STIB nie podaje prędkości " +
            "dopuszczalnej na torze; 72 km/h wolno używać tylko jako jawnego parametru " +
            "scenariusza, a zmierzone dolne ograniczenie z T-401 to 58,68 km/h"),
        new SignallingAssumption(
            nameof(AuthorityMarginM),
            AuthorityMarginM.ToString("R", CultureInfo.InvariantCulture) + " m",
            "overlapu za sygnałem nie ma w żadnym źródle; zero znaczy \"model nie " +
            "wymyśla zapasu\", a nie \"STIB nie ma overlapu\""),
        new SignallingAssumption(
            "route_conflict_rule",
            "wspólny blok",
            "logika interlockingu STIB nie jest publiczna (\"station-specific " +
            "route-locking/interlocking logic\"); jedyny konflikt, jaki model zna, " +
            "to dzielony blok"),
    };

    /// <summary>Blok o zadanym identyfikatorze.</summary>
    public Block BlockById(string blockId) => _blocks[IndexOf(blockId)];

    /// <summary>Indeks bloku o zadanym identyfikatorze; wyjątek, gdy nie ma takiego bloku.</summary>
    public int IndexOf(string blockId)
    {
        ArgumentNullException.ThrowIfNull(blockId);
        return _byId.TryGetValue(blockId, out var index)
            ? index
            : throw new KeyNotFoundException($"plan {PlanId} nie ma bloku {blockId}");
    }

    /// <summary>Czy plan zna blok o tym identyfikatorze.</summary>
    public bool HasBlock(string blockId) => _byId.ContainsKey(blockId ?? throw new ArgumentNullException(nameof(blockId)));

    /// <summary>Trasa o zadanym identyfikatorze.</summary>
    public Route RouteById(string routeId)
    {
        ArgumentNullException.ThrowIfNull(routeId);
        foreach (var route in _routes)
        {
            if (string.Equals(route.Id, routeId, StringComparison.Ordinal))
            {
                return route;
            }
        }

        throw new KeyNotFoundException($"plan {PlanId} nie ma trasy {routeId}");
    }

    /// <summary>Czy plan zna trasę o tym identyfikatorze.</summary>
    public bool HasRoute(string routeId)
    {
        ArgumentNullException.ThrowIfNull(routeId);
        foreach (var route in _routes)
        {
            if (string.Equals(route.Id, routeId, StringComparison.Ordinal))
            {
                return true;
            }
        }

        return false;
    }

    /// <summary>
    /// Indeks bloku zawierającego zadany chainage. Wartości poza planem są przycinane
    /// do jego końców — tak samo jak <see cref="TrackAxis.PointAt"/> przycina oś.
    /// </summary>
    public int BlockIndexAt(double chainageM)
    {
        if (!double.IsFinite(chainageM))
        {
            throw new ArgumentOutOfRangeException(nameof(chainageM), chainageM, "Chainage musi być skończony.");
        }

        if (chainageM <= StartM)
        {
            return 0;
        }

        if (chainageM >= EndM)
        {
            return _blocks.Length - 1;
        }

        var low = 0;
        var high = _blocks.Length - 1;
        while (high - low > 0)
        {
            var mid = (low + high + 1) / 2;
            if (_starts[mid] <= chainageM)
            {
                low = mid;
            }
            else
            {
                high = mid - 1;
            }
        }

        return low;
    }

    /// <summary>Blok zawierający zadany chainage.</summary>
    public Block BlockAt(double chainageM) => _blocks[BlockIndexAt(chainageM)];

    /// <summary>
    /// Trasa prowadząca z bloku peronowego zawierającego <paramref name="fromChainageM"/>
    /// do następnego bloku peronowego, albo <c>null</c>, gdy takiej nie ma.
    /// </summary>
    public Route? NextRouteFrom(double fromChainageM)
    {
        var from = _blocks[BlockIndexAt(fromChainageM)].Id;
        foreach (var route in _routes)
        {
            if (string.Equals(route.FromBlockId, from, StringComparison.Ordinal))
            {
                return route;
            }
        }

        return null;
    }

    // --- reguła generowania -------------------------------------------------------

    /// <summary>
    /// Wykonanie reguły podziału na bloki dla zadanej osi.
    ///
    /// <para>Reguła, w całości:</para>
    /// <list type="number">
    /// <item>każda stacja osi dostaje blok peronowy długości
    ///   <paramref name="platformBlockLengthM"/> wyśrodkowany na jej kilometrażu,
    ///   przycięty od dołu do początku osi;</item>
    /// <item>między dwoma kolejnymi blokami peronowymi leży dokładnie jeden blok szlakowy;</item>
    /// <item>plan sięga od 0 do <c>max(długość osi, koniec ostatniego bloku peronowego)</c>;
    ///   gdy oś jest dłuższa niż ostatni peron, dochodzi blok szlakowy końcowy;</item>
    /// <item>trasa prowadzi z bloku peronowego przez blok szlakowy do następnego bloku
    ///   peronowego, więc dwie kolejne trasy dzielą blok peronowy — i przez to są
    ///   w konflikcie.</item>
    /// </list>
    ///
    /// <para><b>Dlaczego plan może sięgać dalej niż oś.</b> Ostatnia stacja pakietu
    /// leży <b>dokładnie na końcu osi</b>, a blok peronowy jest wyśrodkowany na
    /// kilometrażu stacji — więc jego dalsza połowa z konieczności wystaje za oś.
    /// Zmierzone na pakiecie A: <c>length_m</c> 6686,35 m, kilometraż Merode
    /// 6686,35 m, koniec ostatniego bloku 6733,35 m, czyli 47,00 m za osią — połowa
    /// 94-metrowego składu M7. Blok przycięty do końca osi nie zawierałby punktu
    /// zatrzymania po całej długości peronu, a od tego zależy zwolnienie drzwi.
    /// Plan idzie zatem do dalszego z dwóch końców.</para>
    ///
    /// <para>Do #86 (<c>4a03982</c>, 02.09.2026) ten akapit mówił co innego: że
    /// kilometraż Merode (6686,99 m) leży 0,25 m ZA końcem osi zagęszczonej
    /// (6686,739 m) i że jest to usterka danych. #86 przeliczyło kilometraże na osi,
    /// która trafia do pliku, i ta rozbieżność zniknęła — na wszystkich sześciu
    /// pakietach ostatnia stacja ma dziś kilometraż równy <c>length_m</c> co do
    /// setnej metra, a stacji ZA końcem osi nie ma ani jednej. Wniosek się nie
    /// zmienił, zmieniła się jego przesłanka; pilnuje tego
    /// <c>tools/tests/test_axis_claims.py</c>.</para>
    /// </summary>
    /// <param name="axis">Oś pakietu z kilometrażami stacji.</param>
    /// <param name="platformBlockLengthM">Długość bloku peronowego.</param>
    /// <param name="permittedSpeedMps">Prędkość dopuszczalna planu.</param>
    /// <param name="authorityMarginM">Zapas za końcem authority.</param>
    /// <param name="variant">Wariant ochrony pociągu.</param>
    /// <param name="requireRoute">Czy authority wymaga zaryglowanej trasy.</param>
    public static SignallingPlan FromAxis(
        TrackAxis axis,
        double platformBlockLengthM,
        double permittedSpeedMps,
        double authorityMarginM,
        ProtectionVariant variant,
        bool requireRoute)
    {
        ArgumentNullException.ThrowIfNull(axis);
        if (!double.IsFinite(platformBlockLengthM) || platformBlockLengthM <= 0.0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(platformBlockLengthM), platformBlockLengthM,
                "Długość bloku peronowego musi być dodatnia i skończona.");
        }

        if (axis.Stations.Count < 2)
        {
            throw new ArgumentOutOfRangeException(
                nameof(axis), axis.Stations.Count, "Plan bloków wymaga co najmniej dwóch stacji na osi.");
        }

        var half = platformBlockLengthM / 2.0;
        var stations = axis.Stations;
        var platforms = new (double Start, double End, string Name)[stations.Count];
        for (var i = 0; i < stations.Count; i++)
        {
            var start = Round(Math.Max(0.0, stations[i].ChainageM - half));
            var end = Round(stations[i].ChainageM + half);
            if (i > 0 && start <= platforms[i - 1].End)
            {
                throw new ArgumentOutOfRangeException(
                    nameof(platformBlockLengthM), platformBlockLengthM, string.Create(
                        CultureInfo.InvariantCulture,
                        $"bloki peronowe stacji {stations[i - 1].Name} i {stations[i].Name} zachodzą na siebie " +
                        $"— międzystacja {stations[i].ChainageM - stations[i - 1].ChainageM:F2} m jest krótsza " +
                        $"niż {platformBlockLengthM:F2} m"));
            }

            platforms[i] = (start, end, stations[i].Name);
        }

        var blocks = new List<Block>(2 * stations.Count);
        var routes = new List<Route>(stations.Count - 1);
        for (var i = 0; i < platforms.Length; i++)
        {
            if (i > 0)
            {
                blocks.Add(new Block(
                    SectionId(i), platforms[i - 1].End, platforms[i].Start, BlockKind.Interstation, string.Empty));
            }

            blocks.Add(new Block(
                PlatformId(i + 1), platforms[i].Start, platforms[i].End, BlockKind.Platform, platforms[i].Name));
        }

        var planEnd = Round(Math.Max(axis.LengthM, platforms[^1].End));
        if (planEnd > platforms[^1].End)
        {
            blocks.Add(new Block(
                SectionId(platforms.Length), platforms[^1].End, planEnd, BlockKind.Interstation, string.Empty));
        }

        for (var i = 1; i < platforms.Length; i++)
        {
            routes.Add(new Route(
                RouteId(i),
                PlatformId(i),
                PlatformId(i + 1),
                new[] { PlatformId(i), SectionId(i), PlatformId(i + 1) }));
        }

        return new SignallingPlan(
            $"classic-2026-{axis.Id}",
            "classic_2026",
            axis.Id,
            ParameterStatus.DesignModel,
            variant,
            requireRoute,
            permittedSpeedMps,
            authorityMarginM,
            platformBlockLengthM,
            blocks.ToArray(),
            routes.ToArray(),
            DefaultUnknownParameters());

        static string PlatformId(int oneBased) => "P" + oneBased.ToString("D2", CultureInfo.InvariantCulture);
        static string SectionId(int oneBased) => "S" + oneBased.ToString("D2", CultureInfo.InvariantCulture);
        static string RouteId(int oneBased) => "R" + oneBased.ToString("D2", CultureInfo.InvariantCulture);
    }

    /// <summary>
    /// Parametry, których plan świadomie nie zawiera. Przepisane z
    /// <c>data/signalling/ground-truth.json</c>, sekcja <c>unknown_parameters</c>,
    /// zawężone do tych, których dotyczy plan bloków.
    /// </summary>
    public static string[] DefaultUnknownParameters() => new[]
    {
        "exact fixed-block boundaries and lengths",
        "complete signal aspect tables and placement",
        "station-specific route-locking/interlocking logic",
        "ATP/ATO braking curves and safety margins",
        "device reaction times",
    };

    // --- wczytanie i zapis --------------------------------------------------------

    /// <summary>Plan z treści pliku <c>data/design/signalling/*.json</c>.</summary>
    public static SignallingPlan FromJson(string json)
    {
        ArgumentNullException.ThrowIfNull(json);
        using var document = JsonDocument.Parse(json);
        var root = document.RootElement;

        var schema = root.GetProperty("schema_version").GetInt32();
        if (schema != CurrentSchemaVersion)
        {
            throw new FormatException(
                $"plan sygnalizacji ma schema_version {schema}, a rdzeń zna {CurrentSchemaVersion}");
        }

        var status = ParameterStatusParser.Parse(root.GetProperty("status").GetString() ?? string.Empty);
        if (status != ParameterStatus.DesignModel)
        {
            // Awans planu na spec/observed bez identyfikatora źródła jest dokładnie tym,
            // przed czym ostrzega docs/10-signalling-ground-truth.md: „Brak danych nie
            // jest powodem do awansu design_model → spec".
            var sourceId = root.TryGetProperty("source_id", out var source) ? source.GetString() : null;
            if (string.IsNullOrWhiteSpace(sourceId))
            {
                throw new FormatException(
                    $"plan {root.GetProperty("plan_id").GetString()} ma status " +
                    $"'{ParameterStatusParser.ToRegistryString(status)}' bez source_id — " +
                    "plan bez źródła musi zostać design_model");
            }
        }

        var variant = (root.GetProperty("protection_variant").GetString() ?? string.Empty) switch
        {
            "legacy_fixed_block" => ProtectionVariant.LegacyFixedBlock,
            "legacy_with_kcv" => ProtectionVariant.LegacyWithKcv,
            var other => throw new FormatException($"nieznany protection_variant: '{other}'"),
        };

        var generation = root.GetProperty("generation");
        var blocks = new List<Block>();
        foreach (var element in root.GetProperty("blocks").EnumerateArray())
        {
            blocks.Add(new Block(
                element.GetProperty("id").GetString() ?? throw new FormatException("blok bez id"),
                element.GetProperty("start_m").GetDouble(),
                element.GetProperty("end_m").GetDouble(),
                (element.GetProperty("kind").GetString() ?? string.Empty) switch
                {
                    "platform" => BlockKind.Platform,
                    "interstation" => BlockKind.Interstation,
                    var other => throw new FormatException($"nieznany rodzaj bloku: '{other}'"),
                },
                element.TryGetProperty("station", out var station) ? station.GetString() ?? string.Empty : string.Empty));
        }

        var routes = new List<Route>();
        foreach (var element in root.GetProperty("routes").EnumerateArray())
        {
            var ids = new List<string>();
            foreach (var id in element.GetProperty("blocks").EnumerateArray())
            {
                ids.Add(id.GetString() ?? throw new FormatException("trasa wskazuje blok bez identyfikatora"));
            }

            routes.Add(new Route(
                element.GetProperty("id").GetString() ?? throw new FormatException("trasa bez id"),
                element.GetProperty("from").GetString() ?? throw new FormatException("trasa bez from"),
                element.GetProperty("to").GetString() ?? throw new FormatException("trasa bez to"),
                ids.ToArray()));
        }

        var unknown = new List<string>();
        if (root.TryGetProperty("unknown_parameters", out var unknownArray))
        {
            foreach (var element in unknownArray.EnumerateArray())
            {
                unknown.Add(element.GetString() ?? string.Empty);
            }
        }

        return new SignallingPlan(
            root.GetProperty("plan_id").GetString() ?? "?",
            root.GetProperty("mode").GetString() ?? "?",
            root.GetProperty("axis_id").GetString() ?? "?",
            status,
            variant,
            root.GetProperty("require_route").GetBoolean(),
            Units.KmhToMps(DesignValue(root, "default_permitted_speed_kmh")),
            DesignValue(root, "authority_margin_m"),
            generation.GetProperty("platform_block_length_m").GetDouble(),
            blocks.ToArray(),
            routes.ToArray(),
            unknown.ToArray());
    }

    /// <summary>Plan wczytany z pliku.</summary>
    public static SignallingPlan FromFile(string path) => FromJson(File.ReadAllText(path));

    /// <summary>
    /// Zapis planu w formacie pliku <c>data/design/signalling/*.json</c>.
    ///
    /// Istnieje po to, żeby plik w <c>data/</c> był **wygenerowany, a nie napisany
    /// ręcznie** (reguła 2 z <c>CLAUDE.md</c>), i żeby test mógł sprawdzić, że wczytanie
    /// i zapis dają dokładnie tę samą treść — czyli że loader niczego z pliku nie gubi.
    /// </summary>
    public string ToJson()
    {
        var buffer = new MemoryStream();
        using (var writer = new Utf8JsonWriter(buffer, new JsonWriterOptions
        {
            Indented = true,
            Encoder = System.Text.Encodings.Web.JavaScriptEncoder.UnsafeRelaxedJsonEscaping,
        }))
        {
            writer.WriteStartObject();
            writer.WriteString("$comment",
                "T-313. Plan bloków i tras dla trybu classic_2026. CAŁOŚĆ JEST design_model: " +
                "STIB nie publikuje granic bloków, tabel aspektów ani logiki interlockingu " +
                "(data/signalling/ground-truth.json, unknown_parameters). Plik powstał z reguły " +
                "opisanej w polu generation, przez SignallingPlan.FromAxis — nie z planu STIB. " +
                "Podmiana na plan ze źródłem nie wymaga zmiany kodu w src/Sim/.");
            writer.WriteNumber("schema_version", CurrentSchemaVersion);
            writer.WriteString("plan_id", PlanId);
            writer.WriteString("mode", Mode);
            writer.WriteString("axis_id", AxisId);
            writer.WriteString("status", ParameterStatusParser.ToRegistryString(Status));
            writer.WriteString("protection_variant", Variant switch
            {
                ProtectionVariant.LegacyFixedBlock => "legacy_fixed_block",
                ProtectionVariant.LegacyWithKcv => "legacy_with_kcv",
                _ => throw new InvalidOperationException("nieobsłużony wariant ochrony"),
            });
            writer.WriteBoolean("require_route", RequireRoute);

            writer.WriteStartObject("default_permitted_speed_kmh");
            writer.WriteNumber("value", Round(Units.MpsToKmh(PermittedSpeedMps)));
            writer.WriteString("status", "design_model");
            writer.WriteString("basis",
                "reports/R-006-line-speed.md: żaden dokument STIB nie podaje prędkości dopuszczalnej " +
                "na torze; 72 km/h wolno używać wyłącznie jako jawnego parametru scenariusza. " +
                "Zmierzone dolne ograniczenie z T-401 to 58,68 km/h.");
            writer.WriteEndObject();

            writer.WriteStartObject("authority_margin_m");
            writer.WriteNumber("value", Round(AuthorityMarginM));
            writer.WriteString("status", "design_model");
            writer.WriteString("basis",
                "overlapu za końcem authority nie ma w żadnym źródle; zero znaczy, że model " +
                "nie wymyśla zapasu, a nie że STIB go nie ma.");
            writer.WriteEndObject();

            writer.WriteStartObject("generation");
            writer.WriteString("rule",
                "blok peronowy długości jednego składu M7 wyśrodkowany na kilometrażu stacji " +
                "(przycięty od dołu do początku osi), między dwoma peronami dokładnie jeden blok " +
                "szlakowy, plan sięga do dalszego z dwóch końców: długości osi albo końca " +
                "ostatniego bloku peronowego.");
            writer.WriteString("generator", "MetroBxl.Sim.Signalling.SignallingPlan.FromAxis");
            writer.WriteNumber("platform_block_length_m", PlatformBlockLengthM);
            writer.WriteString("platform_block_length_source",
                "data/vehicle/m7-spec.json parameters.length_m (status spec)");
            writer.WriteString("station_chainage_source", $"data/track/{AxisId}.json stations[].chainage_m");
            writer.WriteNumber("boundary_decimals", BoundaryDecimals);
            writer.WriteEndObject();

            writer.WriteStartArray("unknown_parameters");
            foreach (var item in _unknownParameters)
            {
                writer.WriteStringValue(item);
            }

            writer.WriteEndArray();

            writer.WriteStartArray("blocks");
            foreach (var block in _blocks)
            {
                writer.WriteStartObject();
                writer.WriteString("id", block.Id);
                writer.WriteString("kind", block.IsPlatform ? "platform" : "interstation");
                writer.WriteNumber("start_m", block.StartM);
                writer.WriteNumber("end_m", block.EndM);
                if (block.StationName.Length > 0)
                {
                    writer.WriteString("station", block.StationName);
                }

                writer.WriteEndObject();
            }

            writer.WriteEndArray();

            writer.WriteStartArray("routes");
            foreach (var route in _routes)
            {
                writer.WriteStartObject();
                writer.WriteString("id", route.Id);
                writer.WriteString("from", route.FromBlockId);
                writer.WriteString("to", route.ToBlockId);
                writer.WriteStartArray("blocks");
                foreach (var id in route.BlockIds)
                {
                    writer.WriteStringValue(id);
                }

                writer.WriteEndArray();
                writer.WriteEndObject();
            }

            writer.WriteEndArray();
            writer.WriteEndObject();
        }

        // Utf8JsonWriter wcina Environment.NewLine, więc bez tej normalizacji ten sam plan
        // dawałby inny plik na Windowsie i na Linuksie — a plik jest w repo i porównywany
        // co do znaku.
        return Encoding.UTF8.GetString(buffer.ToArray()).Replace("\r\n", "\n", StringComparison.Ordinal) + "\n";
    }

    /// <inheritdoc/>
    public override string ToString() => string.Create(
        CultureInfo.InvariantCulture,
        $"{PlanId}: {_blocks.Length} bloków, {_routes.Length} tras, {StartM:F1}–{EndM:F1} m, " +
        $"{Units.MpsToKmh(PermittedSpeedMps):F1} km/h, {Variant}");

    private static double Round(double value) => Math.Round(value, BoundaryDecimals, MidpointRounding.ToEven);

    /// <summary>
    /// Odczyt liczby, która **musi** deklarować swoje pochodzenie. Goła liczba w pliku
    /// planu jest błędem formatu, a nie wartością domyślną.
    /// </summary>
    private static double DesignValue(JsonElement root, string name)
    {
        var element = root.GetProperty(name);
        if (element.ValueKind != JsonValueKind.Object)
        {
            throw new FormatException(
                $"pole {name} musi być obiektem z polami value i status — goła liczba nie mówi, skąd pochodzi");
        }

        var status = ParameterStatusParser.Parse(element.GetProperty("status").GetString() ?? string.Empty);
        if (status != ParameterStatus.DesignModel &&
            (!element.TryGetProperty("source_id", out var source) || string.IsNullOrWhiteSpace(source.GetString())))
        {
            throw new FormatException($"pole {name} deklaruje status '{ParameterStatusParser.ToRegistryString(status)}' bez source_id");
        }

        return element.GetProperty("value").GetDouble();
    }
}
