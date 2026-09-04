using System;
using System.Collections.Generic;
using System.Globalization;
using System.Text.Json;

namespace MetroBxl.Game.Assets;

/// <summary>Jeden poziom szczegółowości chunka: własny plik GLB, własna liczba trójkątów.</summary>
/// <param name="Level">Numer poziomu; 0 to pełna siatka.</param>
/// <param name="File">Nazwa pliku GLB tego poziomu.</param>
/// <param name="Triangles">Trójkąty tego poziomu.</param>
public readonly record struct ChunkLod(int Level, string File, int Triangles);

/// <summary>Jeden chunk tunelu, tak jak opisuje go manifest streamingowy.</summary>
/// <param name="Id">Identyfikator chunka, np. <c>L1_A_flat_preview_c05</c>.</param>
/// <param name="File">Nazwa pliku GLB poziomu 0.</param>
/// <param name="StartM">Początek zakresu chainage.</param>
/// <param name="EndM">Koniec zakresu chainage.</param>
/// <param name="Lods">Poziomy szczegółowości, rosnąco po <c>Level</c>.</param>
/// <param name="CollisionFile">Plik bryły kolizyjnej; osobny GLB, osobna decyzja o rezydencji.</param>
/// <param name="CollisionTriangles">Trójkąty bryły kolizyjnej.</param>
public readonly record struct ChunkEntry(
    string Id,
    string File,
    double StartM,
    double EndM,
    IReadOnlyList<ChunkLod> Lods,
    string? CollisionFile,
    int CollisionTriangles)
{
    /// <summary>Plik GLB dla żądanego poziomu; wyjątek, gdy manifest go nie zna.</summary>
    /// <remarks>
    /// Poziom spoza manifestu jest BŁĘDEM, a nie powodem do zejścia na poziom 0.
    /// Cichy powrót do poziomu 0 dałby scenę, która rysuje pełną siatkę na horyzoncie
    /// i nie ma jak tego zgłosić: klatki spadają, a manifest wygląda na uszanowany.
    /// </remarks>
    public ChunkLod Lod(int level)
    {
        foreach (var entry in Lods)
        {
            if (entry.Level == level)
            {
                return entry;
            }
        }

        throw new ArgumentOutOfRangeException(nameof(level), level,
            $"chunk {Id} nie ma poziomu {level}; manifest zna {Lods.Count}");
    }
}

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
    private readonly double[] _lodThresholds;

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
        double collisionRadiusM,
        double[] lodThresholds,
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
        CollisionRadiusM = collisionRadiusM;
        _lodThresholds = lodThresholds;
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

    /// <summary>Domyślny zasięg streamowania przed składem.</summary>
    public double DefaultAheadM { get; }

    /// <summary>Domyślny zasięg streamowania za składem.</summary>
    public double DefaultBehindM { get; }

    /// <summary>Promień, w którym trzeba mieć wczytaną bryłę kolizyjną.</summary>
    public double CollisionRadiusM { get; }

    /// <summary>
    /// Progi przełączania LOD: <c>[k]</c> to odległość, od której wolno poziom
    /// <c>k+1</c>. Poziom 0 progu nie ma, bo obowiązuje wszędzie poniżej pierwszego.
    /// </summary>
    public IReadOnlyList<double> LodThresholds => _lodThresholds;

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
            var lods = new List<ChunkLod>();
            if (chunk.TryGetProperty("lods", out var lodArray))
            {
                foreach (var lod in lodArray.EnumerateArray())
                {
                    lods.Add(new ChunkLod(
                        lod.GetProperty("level").GetInt32(),
                        lod.GetProperty("file").GetString() ?? "?",
                        lod.GetProperty("triangles").GetInt32()));
                }
            }

            lods.Sort(static (a, b) => a.Level.CompareTo(b.Level));

            string? collisionFile = null;
            var collisionTriangles = 0;
            if (chunk.TryGetProperty("collision", out var collision))
            {
                collisionFile = collision.GetProperty("file").GetString();
                collisionTriangles = collision.GetProperty("triangles").GetInt32();
            }

            chunks.Add(new ChunkEntry(
                chunk.GetProperty("id").GetString() ?? "?",
                chunk.GetProperty("file").GetString() ?? "?",
                chunk.GetProperty("start_m").GetDouble(),
                chunk.GetProperty("end_m").GetDouble(),
                lods,
                collisionFile,
                collisionTriangles));
        }

        chunks.Sort(static (a, b) => a.StartM.CompareTo(b.StartM));

        // Progi bierze się z `lod_levels`, pomijając poziom 0: on nie ma progu, bo
        // obowiązuje wszędzie poniżej pierwszego. Wpisanie go do listy przesunęłoby
        // wszystkie pozostałe o jeden i scena rysowałaby najgrubszą siatkę pod nosem.
        var levels = new List<(int Level, double Distance)>();
        if (root.TryGetProperty("lod_levels", out var levelArray))
        {
            foreach (var level in levelArray.EnumerateArray())
            {
                levels.Add((level.GetProperty("level").GetInt32(),
                            level.GetProperty("switch_distance_m").GetDouble()));
            }
        }

        levels.Sort(static (a, b) => a.Level.CompareTo(b.Level));
        var thresholds = new List<double>();
        foreach (var level in levels)
        {
            if (level.Level > 0)
            {
                thresholds.Add(level.Distance);
            }
        }

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
            streaming.TryGetProperty("collision_radius_m", out var radius)
                ? radius.GetDouble()
                : StreamingPlan.DefaultCollisionRadiusM,
            thresholds.ToArray(),
            chunks.ToArray());
    }

    /// <inheritdoc/>
    public override string ToString() => string.Create(
        CultureInfo.InvariantCulture,
        $"{Id} ({Variant}): {_chunks.Length} chunków, {AxisLengthM:F3} m, profil {Profile} {ProfileWidthM:F2}×{ProfileHeightM:F2} m, {Triangles} trójkątów");
}
