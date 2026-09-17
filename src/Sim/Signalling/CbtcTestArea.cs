using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Text.Json;
using MetroBxl.Sim.Line;
using MetroBxl.Sim.Physics;

namespace MetroBxl.Sim.Signalling;

/// <summary>Etap testów CBTC. Kolejność z <c>cbtc_test_method_and_beekkant.test_sequence</c>.</summary>
public enum CbtcTestStage
{
    /// <summary>Testy łączności bez jazdy.</summary>
    StaticCommunications,

    /// <summary>Testy z jadącym składem.</summary>
    DynamicTrainRunning,
}

/// <summary>
/// Miejsce testów dynamicznych.
///
/// <para><b>Dlaczego etykieta, a nie data.</b> Źródło mówi „started_late_may_2026"
/// i „planned_summer_2026". To jest miesiąc i pora roku, nie data. Zamiana tego na
/// <c>DateOnly</c> wymagałaby wybrania dnia, którego nikt nie opublikował — a zmyślona
/// data wygląda dokładnie tak samo jak prawdziwa. Etykieta jedzie więc dalej jako
/// napis, dokładnie taki, jaki stoi w rejestrze.</para>
/// </summary>
/// <param name="StationName">Stacja, przy której testy się odbywają; puste dla pnia wspólnego.</param>
/// <param name="Scope">Zakres, gdy nie jest to pojedyncza stacja (np. <c>common_trunk</c>).</param>
/// <param name="StartedLabel">Etykieta rozpoczęcia, przepisana ze źródła bez interpretacji.</param>
/// <param name="StartedDateStatus">Dlaczego to nie jest data.</param>
public readonly record struct CbtcDynamicTestSite(
    string StationName,
    string Scope,
    string StartedLabel,
    string StartedDateStatus)
{
    /// <inheritdoc/>
    public override string ToString() =>
        $"{(StationName.Length > 0 ? StationName : Scope)}: {StartedLabel} ({StartedDateStatus})";
}

/// <summary>
/// Zasięg strefy testowej rzutowany na konkretną oś.
///
/// <para><b>Przycięcie nie jest ukrywane.</b> Odcinek testowy jest opisany stacjami
/// końcowymi całych linii 1 i 5, a osie w repo to pakiety — pakiet A kończy się na
/// Merode, daleko przed Stockel. Rzut takiego zasięgu na taką oś MUSI zostać przycięty
/// i te dwie flagi mówią, że tak się stało. Bez nich „strefa testowa pokrywa całą oś"
/// znaczyłoby dwie różne rzeczy: że tak wynika z danych albo że oś jest za krótka.</para>
/// </summary>
/// <param name="AxisId">Oś, na którą rzutowano.</param>
/// <param name="StartM">Początek zasięgu na tej osi.</param>
/// <param name="EndM">Koniec zasięgu na tej osi.</param>
/// <param name="ClippedAtStart">Czy stacja początkowa leży poza tą osią.</param>
/// <param name="ClippedAtEnd">Czy stacja końcowa leży poza tą osią.</param>
public readonly record struct CbtcTestSpan(
    string AxisId,
    double StartM,
    double EndM,
    bool ClippedAtStart,
    bool ClippedAtEnd)
{
    /// <summary>Długość zasięgu na tej osi.</summary>
    public double LengthM => EndM - StartM;

    /// <summary>Czy zasięg jest przycięty z którejkolwiek strony.</summary>
    public bool IsClipped => ClippedAtStart || ClippedAtEnd;

    /// <inheritdoc/>
    public override string ToString() => string.Create(
        CultureInfo.InvariantCulture,
        $"{AxisId} [{StartM:F2}, {EndM:F2}) {LengthM:F2} m" +
        $"{(IsClipped ? $" — przycięte (start: {ClippedAtStart}, koniec: {ClippedAtEnd})" : string.Empty)}");
}

/// <summary>
/// Strefa testowa CBTC z <c>data/design/signalling/cbtc-test-2026.json</c>.
///
/// <para><b>Co jest faktem, a co modelem.</b> Faktem jest, że instalacja na odcinku
/// Erasme–Stockel jest ukończona i trwają testy, że sekwencja to najpierw łączność
/// statyczna, potem jazda, i że testy dynamiczne przy Beekkant ruszyły pod koniec maja
/// 2026 (<c>data/signalling/ground-truth.json</c>). Modelem jest WSZYSTKO, co ma
/// wymiar: granice strefy w kilometrażu, protokół radiowy, dokładność lokalizacji
/// i bufory bezpieczeństwa. Ground truth wprost mówi, że STIB ich nie publikuje.</para>
///
/// <para><b>Czego ta klasa nie robi.</b> Nie liczy movement authority, nie zna
/// separacji ruchomej i nie ma krzywych ATO. Tryb <c>cbtc_test</c> jest etykietą
/// scenariusza i zasięgiem — ochroną pociągu nadal steruje
/// <see cref="TrainProtection"/> na planie bloków z T-313, bo w chwili
/// <c>as_of</c> tym właśnie sieć jeździła.</para>
/// </summary>
public sealed class CbtcTestArea
{
    /// <summary>Wersja schematu pliku definicji, którą rdzeń rozumie.</summary>
    public const int CurrentSchemaVersion = 1;

    private CbtcTestArea(
        string areaId,
        string modeId,
        ParameterStatus status,
        DateOnly asOf,
        string fromStation,
        string toStation,
        IReadOnlyList<CbtcTestStage> stages,
        IReadOnlyList<CbtcDynamicTestSite> dynamicSites,
        IReadOnlyList<string> sourceFactIds,
        IReadOnlyList<string> unknownParameters)
    {
        AreaId = areaId;
        ModeId = modeId;
        Status = status;
        AsOf = asOf;
        FromStation = fromStation;
        ToStation = toStation;
        Stages = stages;
        DynamicTestSites = dynamicSites;
        SourceFactIds = sourceFactIds;
        UnknownParameters = unknownParameters;
    }

    /// <summary>Identyfikator strefy.</summary>
    public string AreaId { get; }

    /// <summary>Tryb, do którego strefa należy. Musi istnieć w rejestrze trybów.</summary>
    public string ModeId { get; }

    /// <summary>Pochodzenie definicji. Dla strefy testowej zawsze <c>design_model</c>.</summary>
    public ParameterStatus Status { get; }

    /// <summary>Data, na którą fakty zostały zweryfikowane.</summary>
    public DateOnly AsOf { get; }

    /// <summary>Nazwa stacji początkowej odcinka testowego, tak jak w <c>lines.json</c>.</summary>
    public string FromStation { get; }

    /// <summary>Nazwa stacji końcowej odcinka testowego.</summary>
    public string ToStation { get; }

    /// <summary>Etapy testów w kolejności ze źródła.</summary>
    public IReadOnlyList<CbtcTestStage> Stages { get; }

    /// <summary>Miejsca testów dynamicznych.</summary>
    public IReadOnlyList<CbtcDynamicTestSite> DynamicTestSites { get; }

    /// <summary>Fakty z ground truth, na których strefa stoi.</summary>
    public IReadOnlyList<string> SourceFactIds { get; }

    /// <summary>Parametry, których definicja świadomie nie zawiera.</summary>
    public IReadOnlyList<string> UnknownParameters { get; }

    /// <summary>Definicja z treści pliku <c>data/design/signalling/cbtc-test-2026.json</c>.</summary>
    public static CbtcTestArea FromJson(string json)
    {
        ArgumentNullException.ThrowIfNull(json);
        using var document = JsonText.Parse(json, "definicja strefy testowej CBTC");
        var root = document.RootElement;

        var schema = root.GetProperty("schema_version").GetInt32();
        if (schema != CurrentSchemaVersion)
        {
            throw new FormatException(
                $"definicja strefy testowej ma schema_version {schema}, a rdzeń zna {CurrentSchemaVersion}");
        }

        var status = ParameterStatusParser.Parse(root.GetProperty("status").GetString() ?? string.Empty);
        if (status != ParameterStatus.DesignModel)
        {
            // Ta sama reguła co przy planie bloków z T-313: awans bez identyfikatora
            // źródła jest tym, przed czym ostrzega docs/10-signalling-ground-truth.md.
            var sourceId = root.TryGetProperty("source_id", out var source) ? source.GetString() : null;
            if (string.IsNullOrWhiteSpace(sourceId))
            {
                throw new FormatException(
                    $"strefa {root.GetProperty("area_id").GetString()} ma status " +
                    $"'{ParameterStatusParser.ToRegistryString(status)}' bez source_id — " +
                    "granice bez źródła muszą zostać design_model");
            }
        }

        var extent = root.GetProperty("extent");
        var stages = new List<CbtcTestStage>();
        foreach (var element in root.GetProperty("stages").EnumerateArray())
        {
            stages.Add((element.GetProperty("id").GetString() ?? string.Empty) switch
            {
                "static_communications" => CbtcTestStage.StaticCommunications,
                "dynamic_train_running" => CbtcTestStage.DynamicTrainRunning,
                var other => throw new FormatException($"nieznany etap testów: '{other}'"),
            });
        }

        var sites = new List<CbtcDynamicTestSite>();
        foreach (var element in root.GetProperty("dynamic_test_locations").EnumerateArray())
        {
            sites.Add(new CbtcDynamicTestSite(
                Text(element, "station"),
                Text(element, "scope"),
                Text(element, "started_label"),
                Text(element, "started_date_status")));
        }

        return new CbtcTestArea(
            root.GetProperty("area_id").GetString() ?? throw new FormatException("strefa bez area_id"),
            root.GetProperty("mode").GetString() ?? throw new FormatException("strefa bez mode"),
            status,
            DateOnly.ParseExact(
                root.GetProperty("as_of").GetString() ?? throw new FormatException("strefa bez as_of"),
                "yyyy-MM-dd",
                CultureInfo.InvariantCulture),
            extent.GetProperty("from_station").GetString() ?? throw new FormatException("brak from_station"),
            extent.GetProperty("to_station").GetString() ?? throw new FormatException("brak to_station"),
            stages,
            sites,
            Strings(root, "source_fact_ids"),
            Strings(root, "unknown_parameters"));
    }

    /// <summary>
    /// Zasięg strefy na zadanej osi.
    ///
    /// <para>Stacje końcowe są rozwiązywane po nazwie. Gdy stacji nie ma na tej osi,
    /// zasięg jest przycinany do końca osi, a przycięcie trafia do wyniku — bo
    /// „strefa obejmuje całą oś" i „oś kończy się przed granicą strefy" to dwie różne
    /// rzeczy i nie wolno ich zapisać tą samą liczbą.</para>
    /// </summary>
    public CbtcTestSpan OnAxis(TrackAxis axis)
    {
        ArgumentNullException.ThrowIfNull(axis);

        var from = ChainageOf(axis, FromStation);
        var to = ChainageOf(axis, ToStation);

        var start = from ?? 0.0;
        var end = to ?? axis.LengthM;
        if (end < start)
        {
            // Oś może biec przeciwnie do kolejności z lines.json — kierunek osi nie jest
            // kierunkiem jazdy. Odwrócenie jest poprawne, przestawienie granic nie.
            (start, end) = (end, start);
        }

        return new CbtcTestSpan(axis.Id, start, end, from is null, to is null);
    }

    /// <summary>
    /// Czy dana stacja jest wymieniona jako miejsce testów dynamicznych.
    ///
    /// <para>Porównanie po pełnej nazwie z <c>lines.json</c>, bez skracania do jednego
    /// języka: „Beekkant" ma jedną nazwę, ale „Erasme|Erasmus" dwie i dopasowanie po
    /// części nazwy trafiałoby raz w jedną, raz w drugą.</para>
    /// </summary>
    public bool IsDynamicTestSite(string stationName)
    {
        ArgumentNullException.ThrowIfNull(stationName);
        foreach (var site in DynamicTestSites)
        {
            if (string.Equals(site.StationName, stationName, StringComparison.Ordinal))
            {
                return true;
            }
        }

        return false;
    }

    /// <inheritdoc/>
    public override string ToString() =>
        $"{AreaId} ({ModeId}, {ParameterStatusParser.ToRegistryString(Status)}): " +
        $"{FromStation} → {ToStation}, {Stages.Count} etapów, {DynamicTestSites.Count} miejsc testów";

    private static double? ChainageOf(TrackAxis axis, string stationName)
    {
        foreach (var station in axis.Stations)
        {
            if (string.Equals(station.Name, stationName, StringComparison.Ordinal))
            {
                return station.ChainageM;
            }
        }

        return null;
    }

    private static string Text(JsonElement element, string property) =>
        element.TryGetProperty(property, out var value) && value.ValueKind == JsonValueKind.String
            ? value.GetString() ?? string.Empty
            : string.Empty;

    private static IReadOnlyList<string> Strings(JsonElement element, string property)
    {
        var values = new List<string>();
        foreach (var item in element.GetProperty(property).EnumerateArray())
        {
            values.Add(item.GetString() ?? throw new InvalidDataException($"pusty wpis w {property}"));
        }

        return values;
    }
}
