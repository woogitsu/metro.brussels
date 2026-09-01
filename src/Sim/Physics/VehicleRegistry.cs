using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Globalization;
using System.IO;
using System.Reflection;
using System.Text.Json;

namespace MetroBxl.Sim.Physics;

/// <summary>Jeden wpis rejestru: wartość, jej status pochodzenia i identyfikator źródła.</summary>
public sealed class RegistryEntry
{
    internal RegistryEntry(string path, double? number, ParameterStatus status, string? sourceId)
    {
        Path = path;
        Number = number;
        Status = status;
        SourceId = sourceId;
    }

    /// <summary>Ścieżka w rejestrze, np. <c>parameters.empty_mass_kg</c>.</summary>
    public string Path { get; }

    /// <summary>Wartość liczbowa, jeśli wpis jest liczbą.</summary>
    public double? Number { get; }

    /// <summary>Pochodzenie wartości.</summary>
    public ParameterStatus Status { get; }

    /// <summary>Identyfikator źródła pierwotnego; <c>null</c> dla wartości bez źródła.</summary>
    public string? SourceId { get; }

    /// <summary>Wartość liczbowa albo wyjątek — brak liczby w miejscu, gdzie fizyka jej wymaga, jest błędem danych.</summary>
    public double RequireNumber() =>
        Number ?? throw new InvalidDataException($"Wpis rejestru '{Path}' nie jest liczbą.");
}

/// <summary>
/// Canonical ground truth M7 (<c>data/vehicle/m7-spec.json</c>) wczytany z zasobu
/// osadzonego w assembly.
///
/// Dlaczego zasób osadzony, a nie odczyt pliku z <c>data/</c> w czasie działania:
/// rdzeń ma działać w Godocie i w testach bez katalogu <c>data/</c> na dysku
/// (<c>docs/01-architecture.md</c>), a jednocześnie nie wolno przepisywać liczb do
/// kodu, bo wtedy rejestr i symulator rozjeżdżają się bez ostrzeżenia. Osadzenie
/// tego samego pliku w czasie kompilacji spełnia oba warunki: jedna kopia w repo,
/// zero plików wymaganych w runtime.
/// </summary>
public sealed class VehicleRegistry
{
    private const string ResourceName = "MetroBxl.Sim.Data.m7-spec.json";
    private static readonly string[] Sections = { "parameters", "reference_model" };

    private readonly ReadOnlyDictionary<string, RegistryEntry> _entries;

    private VehicleRegistry(
        string vehicleId,
        string asOf,
        int schemaVersion,
        IReadOnlyList<string> sourceIds,
        Dictionary<string, RegistryEntry> entries)
    {
        VehicleId = vehicleId;
        AsOf = asOf;
        SchemaVersion = schemaVersion;
        SourceIds = sourceIds;
        _entries = new ReadOnlyDictionary<string, RegistryEntry>(entries);

        var paths = new List<string>(entries.Keys);
        paths.Sort(StringComparer.Ordinal);
        Paths = paths;
    }

    /// <summary>Rejestr M7 wczytany raz, przy pierwszym użyciu.</summary>
    public static VehicleRegistry M7 { get; } = Load();

    /// <summary>Identyfikator pojazdu z rejestru.</summary>
    public string VehicleId { get; }

    /// <summary>Data audytu rejestru.</summary>
    public string AsOf { get; }

    /// <summary>Wersja schematu rejestru.</summary>
    public int SchemaVersion { get; }

    /// <summary>Identyfikatory źródeł, posortowane porządkiem ordinalnym.</summary>
    public IReadOnlyList<string> SourceIds { get; }

    /// <summary>
    /// Wszystkie ścieżki wpisów, posortowane porządkiem ordinalnym. Kolejność jest
    /// jawnie ustalona, żeby żaden przebieg nie zależał od kolejności iteracji po
    /// słowniku ani od bieżącej kultury.
    /// </summary>
    public IReadOnlyList<string> Paths { get; }

    /// <summary>Wpis spod ścieżki <c>sekcja.nazwa</c>.</summary>
    public RegistryEntry Get(string path)
    {
        ArgumentNullException.ThrowIfNull(path);
        return _entries.TryGetValue(path, out var entry)
            ? entry
            : throw new KeyNotFoundException($"Rejestr M7 nie zawiera wpisu '{path}'.");
    }

    /// <summary>
    /// Wpis o wymuszonym statusie. Rdzeń nie dostaje liczby bez deklaracji, skąd
    /// pochodzi: awans <c>design_model</c> na <c>spec</c> (albo degradacja w drugą
    /// stronę) wywraca budowę modelu, zamiast po cichu zmienić znaczenie wyniku.
    /// </summary>
    public double RequireValue(string path, ParameterStatus expected)
    {
        var entry = Get(path);
        if (entry.Status != expected)
        {
            throw new InvalidDataException(string.Create(
                CultureInfo.InvariantCulture,
                $"Wpis '{path}' ma status '{ParameterStatusParser.ToRegistryString(entry.Status)}', " +
                $"a model wymaga '{ParameterStatusParser.ToRegistryString(expected)}'."));
        }

        return entry.RequireNumber();
    }

    /// <summary>Ścieżki wszystkich wpisów o zadanym statusie, w porządku ordinalnym.</summary>
    public IReadOnlyList<string> PathsWithStatus(ParameterStatus status)
    {
        var found = new List<string>();
        foreach (var path in Paths)
        {
            if (_entries[path].Status == status)
            {
                found.Add(path);
            }
        }

        return found;
    }

    /// <summary>Surowa treść osadzonego rejestru — do porównania z plikiem w <c>data/</c>.</summary>
    public static string ReadEmbeddedJson()
    {
        var assembly = typeof(VehicleRegistry).Assembly;
        using var stream = assembly.GetManifestResourceStream(ResourceName)
            ?? throw new InvalidOperationException(
                $"Brak zasobu '{ResourceName}' w assembly {assembly.GetName().Name}.");
        using var reader = new StreamReader(stream);
        return reader.ReadToEnd();
    }

    private static VehicleRegistry Load()
    {
        using var document = JsonDocument.Parse(ReadEmbeddedJson());
        var root = document.RootElement;

        var entries = new Dictionary<string, RegistryEntry>(StringComparer.Ordinal);
        foreach (var section in Sections)
        {
            foreach (var property in root.GetProperty(section).EnumerateObject())
            {
                var path = section + "." + property.Name;
                entries[path] = ReadEntry(path, property.Value);
            }
        }

        var sourceIds = new List<string>();
        foreach (var source in root.GetProperty("sources").EnumerateObject())
        {
            sourceIds.Add(source.Name);
        }

        sourceIds.Sort(StringComparer.Ordinal);

        return new VehicleRegistry(
            root.GetProperty("vehicle_id").GetString() ?? throw new InvalidDataException("Rejestr bez vehicle_id."),
            root.GetProperty("as_of").GetString() ?? throw new InvalidDataException("Rejestr bez as_of."),
            root.GetProperty("schema_version").GetInt32(),
            sourceIds,
            entries);
    }

    private static RegistryEntry ReadEntry(string path, JsonElement element)
    {
        var status = ParameterStatusParser.Parse(
            element.GetProperty("status").GetString()
            ?? throw new InvalidDataException($"Wpis '{path}' nie ma statusu."));

        double? number = element.GetProperty("value").ValueKind == JsonValueKind.Number
            ? element.GetProperty("value").GetDouble()
            : null;

        string? sourceId = element.TryGetProperty("source_id", out var source) && source.ValueKind == JsonValueKind.String
            ? source.GetString()
            : null;

        return new RegistryEntry(path, number, status, sourceId);
    }
}
