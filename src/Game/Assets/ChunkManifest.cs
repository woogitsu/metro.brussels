using System;
using System.Collections.Generic;
using System.Globalization;
using System.Text.Json;

namespace MetroBxl.Game.Assets;

/// <summary>Jeden chunk tunelu, tak jak opisuje go manifest streamingowy.</summary>
/// <param name="Id">Identyfikator chunka, np. <c>L1_A_flat_preview_c05</c>.</param>
/// <param name="File">Nazwa pliku GLB poziomu 0.</param>
/// <param name="StartM">Początek zakresu chainage.</param>
/// <param name="EndM">Koniec zakresu chainage.</param>
public readonly record struct ChunkEntry(string Id, string File, double StartM, double EndM);

/// <summary>
/// Odczyt manifestu <c>*-chunks.json</c> wyprodukowanego przez
/// <c>tools/blender/tunnel_sweep.py</c>.
///
/// Scena czyta manifest, a nie zawartość katalogu, bo to manifest jest umową: niesie
/// zakresy chainage, listę poziomów LOD, bryły kolizyjne i domyślne okno streamowania.
/// Wyliczanie plików z katalogu działałoby dopóty, dopóki w katalogu nie znajdzie się
/// coś jeszcze — a wtedy scena wczytałaby to bez pytania.
///
/// <b>Ten pierwszy przejazd nie streamuje.</b> Wczytuje wszystkie chunki poziomu 0 naraz
/// i trzyma je w pamięci. Uzasadnienie i miara są w <c>reports/T-400-first-run.md</c>;
/// predykat okna (<c>sweep.chunks_for_train</c>, <c>lod.lod_plan</c>) czeka na osobne
/// zadanie razem z testami, które go pilnują po stronie Pythona.
/// </summary>
public sealed class ChunkManifest
{
    private readonly ChunkEntry[] _chunks;

    private ChunkManifest(
        string id,
        string name,
        string variant,
        bool productionReady,
        string profile,
        double profileWidthM,
        double profileHeightM,
        double axisLengthM,
        int triangles,
        double defaultAheadM,
        double defaultBehindM,
        ChunkEntry[] chunks)
    {
        Id = id;
        Name = name;
        Variant = variant;
        ProductionReady = productionReady;
        Profile = profile;
        ProfileWidthM = profileWidthM;
        ProfileHeightM = profileHeightM;
        AxisLengthM = axisLengthM;
        Triangles = triangles;
        DefaultAheadM = defaultAheadM;
        DefaultBehindM = defaultBehindM;
        _chunks = chunks;
    }

    /// <summary>Identyfikator pakietu.</summary>
    public string Id { get; }

    /// <summary>Nazwa wariantu w scenie.</summary>
    public string Name { get; }

    /// <summary>Wariant geometrii: <c>flat-preview</c> albo <c>production</c>.</summary>
    public string Variant { get; }

    /// <summary>Czy geometria jest produkcyjna. Dopóki T-112 jest otwarte — nie.</summary>
    public bool ProductionReady { get; }

    /// <summary>Nazwa profilu przekroju.</summary>
    public string Profile { get; }

    /// <summary>Szerokość profilu w metrach.</summary>
    public double ProfileWidthM { get; }

    /// <summary>Wysokość profilu w metrach.</summary>
    public double ProfileHeightM { get; }

    /// <summary>Długość zagęszczonej osi, po której zamiatany jest tunel.</summary>
    public double AxisLengthM { get; }

    /// <summary>Liczba trójkątów poziomu 0 na całym pakiecie.</summary>
    public int Triangles { get; }

    /// <summary>Domyślne okno streamowania przed składem (na razie nieużywane).</summary>
    public double DefaultAheadM { get; }

    /// <summary>Domyślne okno streamowania za składem (na razie nieużywane).</summary>
    public double DefaultBehindM { get; }

    /// <summary>Chunki w kolejności chainage.</summary>
    public IReadOnlyList<ChunkEntry> Chunks => _chunks;

    /// <summary>Manifest z treści pliku JSON.</summary>
    public static ChunkManifest FromJson(string json)
    {
        ArgumentNullException.ThrowIfNull(json);
        using var document = JsonDocument.Parse(json);
        var root = document.RootElement;

        var size = root.GetProperty("profile_size_m");
        var streaming = root.GetProperty("streaming");

        var chunks = new List<ChunkEntry>();
        foreach (var chunk in root.GetProperty("chunks").EnumerateArray())
        {
            chunks.Add(new ChunkEntry(
                chunk.GetProperty("id").GetString() ?? "?",
                chunk.GetProperty("file").GetString() ?? "?",
                chunk.GetProperty("start_m").GetDouble(),
                chunk.GetProperty("end_m").GetDouble()));
        }

        chunks.Sort(static (a, b) => a.StartM.CompareTo(b.StartM));

        return new ChunkManifest(
            root.GetProperty("id").GetString() ?? "?",
            root.GetProperty("name").GetString() ?? "?",
            root.GetProperty("variant").GetString() ?? "?",
            root.GetProperty("production_ready").GetBoolean(),
            root.GetProperty("profile").GetString() ?? "?",
            size[0].GetDouble(),
            size[1].GetDouble(),
            root.GetProperty("axis_length_m").GetDouble(),
            root.GetProperty("totals").GetProperty("triangles").GetInt32(),
            streaming.GetProperty("default_ahead_m").GetDouble(),
            streaming.GetProperty("default_behind_m").GetDouble(),
            chunks.ToArray());
    }

    /// <inheritdoc/>
    public override string ToString() => string.Create(
        CultureInfo.InvariantCulture,
        $"{Id} ({Variant}): {_chunks.Length} chunków, {AxisLengthM:F3} m, profil {Profile} {ProfileWidthM:F2}×{ProfileHeightM:F2} m, {Triangles} trójkątów");
}
