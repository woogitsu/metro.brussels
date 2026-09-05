using System;
using System.Collections.Generic;
using System.Globalization;
using System.Text.Json;

namespace MetroBxl.Sim.Line;

/// <summary>Punkt osi w lokalnym układzie metrycznym pakietu (1 jednostka = 1 metr, Z w górę).</summary>
/// <param name="X">Współrzędna wschodnia względem kotwicy pakietu.</param>
/// <param name="Y">Współrzędna północna względem kotwicy pakietu.</param>
/// <param name="Z">Rzędna. Dla wszystkich pakietów jest to 0 — profil pionowy jest zablokowany (T-112).</param>
public readonly record struct AxisPoint(double X, double Y, double Z);

/// <summary>Stacja rzutowana na oś.</summary>
/// <param name="Name">Nazwa dwujęzyczna FR|NL, tak jak w <c>data/track/*.json</c>.</param>
/// <param name="ChainageM">Chainage rzutu przystanku na oś.</param>
/// <param name="StopId">
/// Identyfikator peronu z GTFS STIB. Jest tu po to, żeby zestawienie z rozkładem szło
/// **po identyfikatorze, a nie po nazwie**: nazwa na osi jest dwujęzyczna i ma
/// diakrytyki (<c>Étangs Noirs|Zwarte Vijvers</c>), a w GTFS jest jedna, wersalikami
/// i bez nich. Pusty łańcuch, gdy oś go nie podaje.
/// </param>
public readonly record struct AxisStation(string Name, double ChainageM, string StopId);

/// <summary>
/// Oś trasy pakietu: łamana ze STIB, zagęszczona **dokładnie tak samo**, jak robi to
/// generator tunelu (<c>tools/blender/sweep.py: catmull_rom</c>).
///
/// Dlaczego rdzeń, a nie warstwa silnika: <c>docs/01-architecture.md</c> przypisuje oś
/// do <c>Sim/Line</c>, a nie do <c>Game/</c>. Gdyby oś mieszkała w Godocie, chainage
/// składu — czyli stan symulacji — zależałby od kodu widoku, a rdzeń nie miałby jak
/// odpowiedzieć na pytanie „gdzie jest pociąg".
///
/// Dlaczego zagęszczanie w ogóle: geometria tunelu pakietu A powstaje z osi zagęszczonej
/// krokiem 5 m. Jazda po surowej łamanej rozjeżdżałaby się z osią tunelu o zmierzone
/// 0,1064 m (<c>docs/21-measured-vs-assumed.md</c> §4). Ta klasa liczy tę samą krzywą,
/// więc skład jedzie po osi tunelu, a nie obok niej.
///
/// Klasa nie czyta plików: dostaje treść JSON-a. Rdzeń ma działać bez katalogu
/// <c>data/</c> na dysku (ten sam powód, dla którego rejestr M7 jest zasobem osadzonym).
/// </summary>
public sealed class TrackAxis
{
    /// <summary>Krok zagęszczania z <c>tools/blender/sweep.py: DEFAULT_RING_STEP_M</c>.</summary>
    public const double DefaultRingStepM = 5.0;

    /// <summary>
    /// Tolerancja porównań kilometrażu. Nie jest zapasem bezpieczeństwa — jest granicą,
    /// poniżej której dwie liczby <c>double</c> opisujące to samo miejsce na osi nie mają
    /// prawa być uznane za różne.
    ///
    /// <para><b>Dlaczego stoi przy osi, a nie przy tym, kto porównuje.</b> Kilometraż
    /// jest współrzędną tej klasy (<see cref="ChainagesM"/>, <see cref="AxisStation.ChainageM"/>),
    /// więc granica jego rozdzielczości jest własnością osi, a nie warstwy, która akurat
    /// pyta. Do 05.09.2026 ta sama liczba stała w dwóch egzemplarzach — w
    /// <c>Signalling.FixedBlockSystem</c> i w <c>Train.LineDrive</c> — a ich równości nie
    /// pilnowało nic poza komentarzem „ta sama co w <c>FixedBlockSystem</c>". Rozjazd nie
    /// dałby ani błędu kompilacji, ani czerwonego testu; dałby dwa różne progi „to jest to
    /// samo miejsce" w dwóch warstwach jednego modelu (raport
    /// <c>reports/mutacje-rdzen-sygnalizacji.md</c> §9.2).</para>
    ///
    /// <para><b>Dlaczego nie sklejono ich ze sobą.</b> <c>Signalling</c> zależy dziś od
    /// <c>Train</c> (<c>TrainProtection.Apply</c> zwraca <c>DriverCommand</c>), a
    /// <c>Train</c> od <c>Signalling</c> nie zależy w ani jednym miejscu kodu — i jest to
    /// świadome: <c>LineDrive.AuthorityEndM</c> przyjmuje goły <c>double?</c>, a nie
    /// <c>MovementAuthority</c>, żeby prowadzenie nie wiedziało o sygnalizacji. Odesłanie
    /// z <c>LineDrive</c> do <c>FixedBlockSystem</c> cofnęłoby tę decyzję dla stałej.
    /// Obie warstwy zależą natomiast od <c>Line</c>, więc tutaj liczba może być jedna
    /// i nie przybywa ani jedna krawędź w grafie zależności.</para>
    /// </summary>
    public const double PositionEpsilonM = 1e-9;

    private const double DedupeEpsilonM = 1e-6;

    private readonly AxisPoint[] _source;
    private readonly AxisPoint[] _points;
    private readonly double[] _chainages;
    private readonly AxisStation[] _stations;

    private TrackAxis(
        string id,
        double declaredLengthM,
        string verticalStatus,
        AxisPoint[] source,
        AxisPoint[] points,
        double[] chainages,
        AxisStation[] stations)
    {
        Id = id;
        DeclaredLengthM = declaredLengthM;
        VerticalStatus = verticalStatus;
        _source = source;
        _points = points;
        _chainages = chainages;
        _stations = stations;
    }

    /// <summary>Identyfikator pakietu, np. <c>L1_A</c>.</summary>
    public string Id { get; }

    /// <summary>Długość zadeklarowana w pliku osi (łamana źródłowa).</summary>
    public double DeclaredLengthM { get; }

    /// <summary>
    /// Status profilu pionowego z pliku osi. Dopóki jest to <c>not_modelled</c>,
    /// oś leży na Z = 0 i **pochylenia nie wolno z niej wyprowadzać** — patrz T-112 (#10).
    /// </summary>
    public string VerticalStatus { get; }

    /// <summary>Czy profil pionowy jest zamodelowany. Dla wszystkich pakietów: nie.</summary>
    public bool IsVerticalModelled =>
        !string.Equals(VerticalStatus, "not_modelled", StringComparison.Ordinal);

    /// <summary>Surowa łamana STIB, po usunięciu powtórzonych punktów.</summary>
    public IReadOnlyList<AxisPoint> SourcePoints => _source;

    /// <summary>Oś zagęszczona — ta sama krzywa, po której zamiatany jest tunel.</summary>
    public IReadOnlyList<AxisPoint> Points => _points;

    /// <summary>Chainage kolejnych punktów zagęszczonej osi.</summary>
    public IReadOnlyList<double> ChainagesM => _chainages;

    /// <summary>Stacje rzutowane na oś, w kolejności chainage.</summary>
    public IReadOnlyList<AxisStation> Stations => _stations;

    /// <summary>Długość zagęszczonej osi. To ona, a nie <see cref="DeclaredLengthM"/>,
    /// odpowiada <c>axis_length_m</c> z manifestu chunków.</summary>
    public double LengthM => _chainages[^1];

    /// <summary>Oś z treści pliku <c>data/track/*.json</c>.</summary>
    /// <param name="json">Zawartość pliku osi.</param>
    /// <param name="ringStepM">Krok zagęszczania; wartość ≤ 0 zostawia surową łamaną.</param>
    public static TrackAxis FromJson(string json, double ringStepM = DefaultRingStepM)
    {
        ArgumentNullException.ThrowIfNull(json);

        using var document = JsonDocument.Parse(json);
        var root = document.RootElement;

        var id = root.TryGetProperty("id", out var idElement)
            ? idElement.GetString() ?? "?"
            : "?";
        var declaredLength = root.TryGetProperty("length_m", out var lengthElement)
            ? lengthElement.GetDouble()
            : 0.0;
        var verticalStatus = "unknown";
        if (root.TryGetProperty("vertical", out var vertical) &&
            vertical.TryGetProperty("status", out var status))
        {
            verticalStatus = status.GetString() ?? "unknown";
        }

        var raw = new List<AxisPoint>();
        foreach (var point in root.GetProperty("points").EnumerateArray())
        {
            raw.Add(new AxisPoint(point[0].GetDouble(), point[1].GetDouble(), point[2].GetDouble()));
        }

        var source = Dedupe(raw);
        if (source.Length < 2)
        {
            throw new ArgumentException("oś musi mieć co najmniej 2 różne punkty", nameof(json));
        }

        var densified = CatmullRom(source, ringStepM);
        var chainages = Chainages(densified);

        var stations = new List<AxisStation>();
        if (root.TryGetProperty("stations", out var stationArray))
        {
            foreach (var station in stationArray.EnumerateArray())
            {
                stations.Add(new AxisStation(
                    station.GetProperty("name").GetString() ?? "?",
                    station.GetProperty("chainage_m").GetDouble(),
                    station.TryGetProperty("stop_id", out var stopId)
                        ? stopId.GetString() ?? string.Empty
                        : string.Empty));
            }
        }

        stations.Sort(static (a, b) => a.ChainageM.CompareTo(b.ChainageM));

        return new TrackAxis(id, declaredLength, verticalStatus, source, densified, chainages, stations.ToArray());
    }

    /// <summary>
    /// Punkt osi w zadanym chainage. Wartości poza osią są przycinane do jej końców —
    /// tak samo jak w <c>tools/blender/placement.py: frame_at</c>, bo skład dłuższy niż
    /// resztka osi ma się zatrzymać na jej końcu, a nie zniknąć.
    /// </summary>
    public AxisPoint PointAt(double chainageM)
    {
        if (!double.IsFinite(chainageM))
        {
            throw new ArgumentOutOfRangeException(nameof(chainageM), chainageM, "Chainage musi być skończony.");
        }

        var clamped = Math.Clamp(chainageM, 0.0, LengthM);
        var index = SegmentIndex(clamped);
        var span = _chainages[index + 1] - _chainages[index];
        var t = span <= 0.0 ? 0.0 : (clamped - _chainages[index]) / span;
        var a = _points[index];
        var b = _points[index + 1];
        return new AxisPoint(
            a.X + (t * (b.X - a.X)),
            a.Y + (t * (b.Y - a.Y)),
            a.Z + (t * (b.Z - a.Z)));
    }

    /// <summary>
    /// Czy cięciwa od <paramref name="fromM"/> do <paramref name="toM"/> jest na tej osi
    /// niezdegenerowana: oba kilometraże przyciśnięte do <c>[0, LengthM]</c> dają dwa
    /// RÓŻNE punkty. Dla nieskończoności i NaN zwraca <c>false</c>, bo z takiej cięciwy
    /// nie da się zbudować ramki tak samo jak z zerowej.
    ///
    /// <para><b>Po co to istnieje.</b> <see cref="PointAt"/> PRZYCINA kilometraż do osi,
    /// więc dwa różne kilometraże leżące oba przed początkiem albo oba za końcem dają
    /// TEN SAM punkt — a z niego cięciwę zerowej długości, z której nie da się zbudować
    /// ramki. Widok składu pytał o takie cięciwy przy przejeździe rozpoczętym na
    /// kilometrażu mniejszym niż długość składu: ogon leżał wtedy poza osią.
    /// <c>DriveScenario.PackageAFirstRun</c> obchodzi to startem na 94,0 m i mówi o tym
    /// wprost w komentarzu, ale przejazd całą linią startuje na pierwszej stacji, czyli
    /// na zerze, i obejście przestaje działać.</para>
    ///
    /// <para>Predykat jest tutaj, a nie w widoku, bo odpowiada na pytanie o ZASIĘG OSI,
    /// nie o rysowanie. Dzięki temu daje się sprawdzić bez silnika.</para>
    /// </summary>
    public bool CoversChord(double fromM, double toM)
    {
        if (!double.IsFinite(fromM) || !double.IsFinite(toM))
        {
            return false;
        }

        var length = LengthM;
        var a = Math.Clamp(fromM, 0.0, length);
        var b = Math.Clamp(toM, 0.0, length);
        return a != b;
    }

    /// <summary>
    /// Największa odległość punktu zagęszczonej osi od łamanej źródłowej — miara tego,
    /// ile interpolacja dołożyła do przebiegu STIB. Odpowiednik
    /// <c>tools/blender/sweep.py: max_deviation</c>; na pakiecie A wychodzi 0,1064 m.
    /// </summary>
    /// <returns>Odległość w metrach; zero, gdy oś nie została zagęszczona.</returns>
    public double MaxDeviationFromSourceM()
    {
        var worst = 0.0;
        foreach (var point in _points)
        {
            worst = Math.Max(worst, DistanceToPolylineM(point, _source));
        }

        return worst;
    }

    /// <inheritdoc/>
    public override string ToString() => string.Create(
        CultureInfo.InvariantCulture,
        $"{Id}: {_points.Length} punktów, {LengthM:F3} m, {_stations.Length} stacji");

    private int SegmentIndex(double chainageM)
    {
        var low = 0;
        var high = _chainages.Length - 1;
        while (high - low > 1)
        {
            var mid = (low + high) / 2;
            if (_chainages[mid] <= chainageM)
            {
                low = mid;
            }
            else
            {
                high = mid;
            }
        }

        return low;
    }

    // --- port 1:1 z tools/blender/sweep.py ---------------------------------------

    private static AxisPoint[] Dedupe(IReadOnlyList<AxisPoint> points)
    {
        var output = new List<AxisPoint>(points.Count);
        foreach (var point in points)
        {
            if (output.Count == 0 || Norm(Sub(point, output[^1])) > DedupeEpsilonM)
            {
                output.Add(point);
            }
        }

        return output.ToArray();
    }

    /// <summary>
    /// Centripetal Catmull-Rom przez wszystkie punkty źródłowe. Kolejność działań jest
    /// przeniesiona z Pythona jeden do jednego — razem z tym, że zerowa odległość
    /// węzła jest zastępowana przez 1e-6 (w Pythonie robi to idiom <c>x or y</c>).
    /// </summary>
    private static AxisPoint[] CatmullRom(AxisPoint[] points, double step)
    {
        if (step <= 0.0 || points.Length < 3)
        {
            return (AxisPoint[])points.Clone();
        }

        var extended = new AxisPoint[points.Length + 2];
        extended[0] = Add(points[0], Sub(points[0], points[1]));
        Array.Copy(points, 0, extended, 1, points.Length);
        extended[^1] = Add(points[^1], Sub(points[^1], points[^2]));

        var output = new List<AxisPoint> { points[0] };
        for (var i = 1; i < extended.Length - 2; i++)
        {
            var p0 = extended[i - 1];
            var p1 = extended[i];
            var p2 = extended[i + 1];
            var p3 = extended[i + 2];

            var span = Norm(Sub(p2, p1));
            var count = Math.Max(1, (int)Math.Ceiling(span / step));

            const double t0 = 0.0;
            var t1 = t0 + Math.Sqrt(Norm(Sub(p1, p0)));
            t1 = t1 == 0.0 ? t0 + 1e-6 : t1;
            var t2 = t1 + Math.Sqrt(span);
            t2 = t2 == 0.0 ? t1 + 1e-6 : t2;
            var t3 = t2 + Math.Sqrt(Norm(Sub(p3, p2)));
            t3 = t3 == 0.0 ? t2 + 1e-6 : t3;

            for (var k = 1; k <= count; k++)
            {
                var t = t1 + ((t2 - t1) * k / count);
                var a1 = Add(Scale(p0, (t1 - t) / (t1 - t0)), Scale(p1, (t - t0) / (t1 - t0)));
                var a2 = Add(Scale(p1, (t2 - t) / (t2 - t1)), Scale(p2, (t - t1) / (t2 - t1)));
                var a3 = Add(Scale(p2, (t3 - t) / (t3 - t2)), Scale(p3, (t - t2) / (t3 - t2)));
                var b1 = Add(Scale(a1, (t2 - t) / (t2 - t0)), Scale(a2, (t - t0) / (t2 - t0)));
                var b2 = Add(Scale(a2, (t3 - t) / (t3 - t1)), Scale(a3, (t - t1) / (t3 - t1)));
                output.Add(Add(Scale(b1, (t2 - t) / (t2 - t1)), Scale(b2, (t - t1) / (t2 - t1))));
            }
        }

        return Dedupe(output);
    }

    private static double[] Chainages(AxisPoint[] points)
    {
        var output = new double[points.Length];
        output[0] = 0.0;
        for (var i = 1; i < points.Length; i++)
        {
            output[i] = output[i - 1] + Norm(Sub(points[i], points[i - 1]));
        }

        return output;
    }

    private static double DistanceToPolylineM(AxisPoint point, AxisPoint[] polyline)
    {
        var best = double.PositiveInfinity;
        for (var i = 0; i < polyline.Length - 1; i++)
        {
            var a = polyline[i];
            var d = Sub(polyline[i + 1], a);
            var segment = Dot(d, d);
            if (segment <= 0.0)
            {
                best = Math.Min(best, Norm(Sub(point, a)));
                continue;
            }

            var t = Math.Clamp(Dot(Sub(point, a), d) / segment, 0.0, 1.0);
            best = Math.Min(best, Norm(Sub(point, Add(a, Scale(d, t)))));
        }

        return best;
    }

    private static AxisPoint Sub(AxisPoint a, AxisPoint b) => new(a.X - b.X, a.Y - b.Y, a.Z - b.Z);

    private static AxisPoint Add(AxisPoint a, AxisPoint b) => new(a.X + b.X, a.Y + b.Y, a.Z + b.Z);

    private static AxisPoint Scale(AxisPoint a, double k) => new(a.X * k, a.Y * k, a.Z * k);

    private static double Dot(AxisPoint a, AxisPoint b) => (a.X * b.X) + (a.Y * b.Y) + (a.Z * b.Z);

    private static double Norm(AxisPoint a) => Math.Sqrt(Dot(a, a));
}
