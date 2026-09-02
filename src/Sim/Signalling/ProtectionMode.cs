using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Globalization;
using System.IO;
using System.Text.Json;

namespace MetroBxl.Sim.Signalling;

/// <summary>
/// Stan wdrożenia trybu ochrony pociągu w chwili <see cref="ProtectionModeRegistry.AsOf"/>.
///
/// <para>Nazwy przepisane wprost z <c>data/signalling/ground-truth.json</c>, pole
/// <c>historical_status</c>. Nie ma tu wartości domyślnej: nieznany stan jest błędem,
/// bo rozstrzyga o tym, czy tryb wolno uznać za historyczny.</para>
/// </summary>
public enum ProtectionModeStatus
{
    /// <summary>To jest to, czym sieć realnie jeździła.</summary>
    OperationalBaseline,

    /// <summary>Instalacja i testy — istnieje, ale nie w ruchu pasażerskim.</summary>
    InstallationAndValidation,

    /// <summary>Scenariusz przyszły. Nie wydarzył się.</summary>
    FutureScenario,
}

/// <summary>Zamiana napisów z ground truth na <see cref="ProtectionModeStatus"/>, bez tolerancji.</summary>
public static class ProtectionModeStatusParser
{
    /// <summary>Nieznany stan jest błędem, a nie założeniem.</summary>
    public static ProtectionModeStatus Parse(string status) => status switch
    {
        "operational_baseline" => ProtectionModeStatus.OperationalBaseline,
        "installation_and_validation" => ProtectionModeStatus.InstallationAndValidation,
        "future_scenario" => ProtectionModeStatus.FutureScenario,
        _ => throw new FormatException($"Nieznany historical_status trybu ochrony: '{status}'."),
    };

    /// <summary>Napis dokładnie taki, jaki stoi w ground truth.</summary>
    public static string ToGroundTruthString(ProtectionModeStatus status) => status switch
    {
        ProtectionModeStatus.OperationalBaseline => "operational_baseline",
        ProtectionModeStatus.InstallationAndValidation => "installation_and_validation",
        ProtectionModeStatus.FutureScenario => "future_scenario",
        _ => throw new ArgumentOutOfRangeException(nameof(status), status, "Nieobsłużony stan."),
    };
}

/// <summary>
/// Jeden tryb ochrony pociągu z rejestru R-003.
///
/// <para><b>Czego ten typ NIE zawiera:</b> ani jednej liczby opisującej działanie CBTC.
/// Algorytm movement authority, bufor ochronny, krzywe ATO, protokół radiowy i parametry
/// lokalizacji są w <c>unknown_parameters</c> ground truth — STIB ich nie publikuje.
/// <see cref="DesignModelRequired"/> wypisuje je z nazwy właśnie po to, żeby było widać,
/// czego trzeba by dopisać, i żeby nikt nie dopisał tego po cichu.</para>
/// </summary>
/// <param name="Id">Identyfikator z ground truth, np. <c>classic_2026</c>.</param>
/// <param name="HistoricalDefault">Czy to jest tryb scenariusza historycznego.</param>
/// <param name="Status">Stan wdrożenia.</param>
/// <param name="PassengerServiceNetworkWide">
/// Czy tryb był w ruchu pasażerskim w całej sieci; <c>null</c>, gdy ground truth nie stawia tej tezy.
/// </param>
/// <param name="Lines">Linie, których tryb dotyczy; puste, gdy ground truth ich nie wylicza.</param>
/// <param name="SourceFactIds">Fakty z ground truth, na których tryb stoi.</param>
/// <param name="DesignModelRequired">Czego symulator musiałby dopisać jako <c>design_model</c>.</param>
public sealed record ProtectionMode(
    string Id,
    bool HistoricalDefault,
    ProtectionModeStatus Status,
    bool? PassengerServiceNetworkWide,
    IReadOnlyList<int> Lines,
    IReadOnlyList<string> SourceFactIds,
    IReadOnlyList<string> DesignModelRequired)
{
    /// <summary>
    /// Czy tryb opiera się na CBTC. Rozstrzyga o tym prefiks identyfikatora z ground truth,
    /// a nie osobna flaga, żeby dopisanie trybu do danych nie wymagało edycji kodu.
    /// </summary>
    public bool IsCbtc => Id.StartsWith("cbtc", StringComparison.Ordinal);

    /// <inheritdoc/>
    public override string ToString() => string.Create(
        CultureInfo.InvariantCulture,
        $"{Id} ({ProtectionModeStatusParser.ToGroundTruthString(Status)})" +
        $"{(HistoricalDefault ? ", historyczny" : string.Empty)}");
}

/// <summary>
/// Rejestr trybów ochrony wczytany z <c>data/signalling/ground-truth.json</c> (R-003).
///
/// <para><b>Po co ta warstwa.</b> Kryterium ukończenia T-314 brzmi: „tryb CBTC nie jest
/// aktywny w scenariuszu historycznym 31.08.2026 bez potwierdzenia pełnego uruchomienia
/// STIB". Rejestr czyta tę odpowiedź z danych zamiast ją kodować:
/// <c>cbtc_lines_1_5_full_service</c> ma wartość <c>false</c>, a jedyny tryb
/// z <c>historical_default</c> to <c>classic_2026</c>.</para>
///
/// <para><b>Dwie drogi do trybu, świadomie rozdzielone.</b> <see cref="ForHistoricalDate"/>
/// odpowiada na pytanie „czym sieć jeździła tego dnia" i nie da się nim włączyć CBTC.
/// <see cref="Named"/> daje dowolny tryb do scenariuszy „co by było gdyby" — i właśnie
/// dlatego jest osobno, a nie jako argument tej pierwszej. Gdyby wybór trybu szedł jedną
/// ścieżką z parametrem, przypadkowe włączenie CBTC w przejeździe historycznym byłoby
/// odległe o jedną literówkę.</para>
///
/// <para>Ground truth jest zasobem osadzonym z tego samego powodu co rejestr M7
/// (<c>docs/01-architecture.md</c>): rdzeń ma działać bez katalogu <c>data/</c> na dysku,
/// a jednocześnie nie wolno przepisywać liczb do kodu.</para>
/// </summary>
public sealed class ProtectionModeRegistry
{
    private const string ResourceName = "MetroBxl.Sim.Data.signalling-ground-truth.json";

    private readonly ReadOnlyDictionary<string, ProtectionMode> _modes;

    private ProtectionModeRegistry(
        DateOnly asOf,
        int schemaVersion,
        Dictionary<string, ProtectionMode> modes,
        ProtectionMode historicalDefault,
        IReadOnlyList<string> unknownParameters)
    {
        AsOf = asOf;
        SchemaVersion = schemaVersion;
        _modes = new ReadOnlyDictionary<string, ProtectionMode>(modes);
        HistoricalDefault = historicalDefault;
        UnknownParameters = unknownParameters;

        var ids = new List<string>(modes.Keys);
        ids.Sort(StringComparer.Ordinal);
        ModeIds = ids;
    }

    /// <summary>Rejestr wczytany raz, przy pierwszym użyciu.</summary>
    public static ProtectionModeRegistry Current { get; } = Load();

    /// <summary>
    /// Data, na którą fakty zostały zweryfikowane. Poza nią rejestr nie odpowiada —
    /// patrz <see cref="ForHistoricalDate"/>.
    /// </summary>
    public DateOnly AsOf { get; }

    /// <summary>Wersja schematu ground truth.</summary>
    public int SchemaVersion { get; }

    /// <summary>Identyfikatory trybów, porządek ordinalny.</summary>
    public IReadOnlyList<string> ModeIds { get; }

    /// <summary>Tryb scenariusza historycznego. Dokładnie jeden w rejestrze.</summary>
    public ProtectionMode HistoricalDefault { get; }

    /// <summary>Parametry, których ground truth świadomie nie zawiera.</summary>
    public IReadOnlyList<string> UnknownParameters { get; }

    /// <summary>Tryb po identyfikatorze — droga dla scenariuszy „co by było gdyby".</summary>
    public ProtectionMode Named(string modeId)
    {
        ArgumentNullException.ThrowIfNull(modeId);
        return _modes.TryGetValue(modeId, out var mode)
            ? mode
            : throw new KeyNotFoundException(
                $"Ground truth nie zna trybu '{modeId}'. Znane: {string.Join(", ", ModeIds)}.");
    }

    /// <summary>
    /// Tryb, którym sieć jeździła w zadanym dniu.
    ///
    /// <para>Rejestr odpowiada wyłącznie do dnia <see cref="AsOf"/> włącznie. Dalej
    /// każda odpowiedź byłaby zgadywaniem: <c>cbtc_jacques_brel_merode_2026_plan</c>
    /// i <c>cbtc_herrmann_debroux_plan</c> to <b>plany</b>, a plan nie jest dowodem
    /// uruchomienia — ground truth mówi to wprost w polu <c>limitations</c>.</para>
    /// </summary>
    public ProtectionMode ForHistoricalDate(DateOnly date)
    {
        if (date > AsOf)
        {
            throw new ArgumentOutOfRangeException(
                nameof(date), date,
                $"Ground truth R-003 jest zweryfikowany na {AsOf:yyyy-MM-dd}. " +
                "Dla późniejszej daty rejestr nie ma faktu, a plan wdrożenia nie jest " +
                "dowodem uruchomienia — użyj Named() i nazwij scenariusz przyszłym.");
        }

        return HistoricalDefault;
    }

    /// <summary>
    /// Strażnik dla kodu, który tryb dostaje z zewnątrz: w scenariuszu historycznym
    /// wolno jechać wyłącznie trybem historycznym.
    ///
    /// <para>Sam <see cref="ForHistoricalDate"/> nie wystarcza, bo nic nie broni komuś
    /// wywołać <see cref="Named"/> i podać wynik dalej. Ten strażnik jest miejscem,
    /// w którym scenariusz przejazdu deklaruje, że jest historyczny.</para>
    /// </summary>
    public void RequireHistorical(ProtectionMode mode, DateOnly date)
    {
        ArgumentNullException.ThrowIfNull(mode);
        var expected = ForHistoricalDate(date);
        if (!string.Equals(mode.Id, expected.Id, StringComparison.Ordinal))
        {
            throw new InvalidOperationException(
                $"Scenariusz historyczny {date:yyyy-MM-dd} wymaga trybu '{expected.Id}', " +
                $"a dostał '{mode.Id}' ({ProtectionModeStatusParser.ToGroundTruthString(mode.Status)}). " +
                "CBTC na liniach 1 i 5 nie było w ruchu pasażerskim " +
                "(data/signalling/ground-truth.json: cbtc_lines_1_5_full_service = false).");
        }
    }

    /// <summary>Surowa treść osadzonego ground truth — do porównania z plikiem w <c>data/</c>.</summary>
    public static string ReadEmbeddedJson()
    {
        var assembly = typeof(ProtectionModeRegistry).Assembly;
        using var stream = assembly.GetManifestResourceStream(ResourceName)
            ?? throw new InvalidOperationException(
                $"Brak zasobu '{ResourceName}' w assembly {assembly.GetName().Name}.");
        using var reader = new StreamReader(stream);
        return reader.ReadToEnd();
    }

    private static ProtectionModeRegistry Load()
    {
        using var document = JsonDocument.Parse(ReadEmbeddedJson());
        var root = document.RootElement;

        var modes = new Dictionary<string, ProtectionMode>(StringComparer.Ordinal);
        foreach (var property in root.GetProperty("modes").EnumerateObject())
        {
            modes[property.Name] = ReadMode(property.Name, property.Value);
        }

        ProtectionMode? historical = null;
        foreach (var mode in modes.Values)
        {
            if (!mode.HistoricalDefault)
            {
                continue;
            }

            if (historical is not null)
            {
                throw new InvalidDataException(
                    $"Ground truth ma dwa tryby historyczne: '{historical.Id}' i '{mode.Id}'.");
            }

            historical = mode;
        }

        if (historical is null)
        {
            throw new InvalidDataException("Ground truth nie wskazuje żadnego trybu historycznego.");
        }

        var declared = root.GetProperty("historical_default").GetString();
        if (!string.Equals(declared, historical.Id, StringComparison.Ordinal))
        {
            // Pole `historical_default` na górze pliku i flaga przy trybie to dwa zapisy
            // tej samej rzeczy. Gdyby się rozjechały, rdzeń nie ma prawa wybrać jednego
            // z nich po cichu.
            throw new InvalidDataException(
                $"Ground truth deklaruje historical_default '{declared}', " +
                $"a flagę historical_default ma tryb '{historical.Id}'.");
        }

        var unknown = new List<string>();
        foreach (var element in root.GetProperty("unknown_parameters").EnumerateArray())
        {
            unknown.Add(element.GetString() ?? throw new InvalidDataException("pusty unknown_parameter"));
        }

        return new ProtectionModeRegistry(
            DateOnly.ParseExact(
                root.GetProperty("as_of").GetString() ?? throw new InvalidDataException("ground truth bez as_of"),
                "yyyy-MM-dd",
                CultureInfo.InvariantCulture),
            root.GetProperty("schema_version").GetInt32(),
            modes,
            historical,
            unknown);
    }

    private static ProtectionMode ReadMode(string id, JsonElement element)
    {
        var lines = new List<int>();
        if (element.TryGetProperty("lines", out var lineArray))
        {
            foreach (var line in lineArray.EnumerateArray())
            {
                lines.Add(line.GetInt32());
            }
        }

        bool? passengerService = element.TryGetProperty("passenger_service_network_wide", out var service)
            ? service.GetBoolean()
            : null;

        return new ProtectionMode(
            id,
            element.GetProperty("historical_default").GetBoolean(),
            ProtectionModeStatusParser.Parse(
                element.GetProperty("historical_status").GetString() ?? string.Empty),
            passengerService,
            lines,
            ReadStrings(element, "source_fact_ids"),
            ReadStrings(element, "design_model_required"));
    }

    private static IReadOnlyList<string> ReadStrings(JsonElement element, string property)
    {
        var values = new List<string>();
        if (!element.TryGetProperty(property, out var array))
        {
            return values;
        }

        foreach (var item in array.EnumerateArray())
        {
            values.Add(item.GetString() ?? throw new InvalidDataException($"pusty wpis w {property}"));
        }

        return values;
    }
}
