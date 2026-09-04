using System;
using System.Collections.Generic;
using System.Globalization;
using Godot;
using MetroBxl.Game.Assets;

namespace MetroBxl.Game.World;

/// <summary>
/// Widok tunelu: chunki pakietu A wczytane z <c>build/</c> i podwieszone pod jeden węzeł.
///
/// Geometria przychodzi z GLB **już w układzie Godota** — eksporter glTF przelicza
/// Z-w-górę na Y-w-górę przy zapisie. Dlatego chunki nie dostają tu żadnej transformacji:
/// każda byłaby drugą, niepotrzebną zamianą układu i rozjechałaby tunel z osią.
/// </summary>
public sealed partial class TunnelView : Node3D
{
    private readonly Dictionary<string, int> _levels = new(StringComparer.Ordinal);

    /// <summary>Liczba chunków rezydentnych w tej chwili.</summary>
    public int LoadedChunks => _levels.Count;

    /// <summary>Łączna liczba węzłów siatki w tunelu.</summary>
    public int MeshNodes { get; private set; }

    /// <summary>
    /// Doprowadza zawartość węzła do stanu, jakiego dla tego chainage żąda
    /// <see cref="StreamingPlan"/>: dokłada brakujące chunki, zwalnia te, które wypadły
    /// z okna, i przeładowuje te, którym zmienił się poziom szczegółowości.
    ///
    /// <para><b>Skąd ta zmiana.</b> W tym miejscu stało <c>LoadAll</c> z uzasadnieniem,
    /// że predykat okna jest przetestowany tylko po stronie Pythona, więc przepisanie go
    /// tutaj dałoby „drugą implementację bez kontroli, a to jest gorsze niż jawny brak
    /// streamowania". Zarzut był słuszny i został zdjęty osobno: <c>StreamingPlan</c>
    /// jest przybity do tej samej tablicy oczekiwań, co implementacja pythonowa
    /// (138 wierszy, oba kierunki jazdy, wszystkie 13 szwów), więc rozjazd którejkolwiek
    /// strony psuje jej własną bramkę. Dopiero to pozwala tu streamować.</para>
    ///
    /// <para>Zwraca liczbę chunków rezydentnych po tej klatce.</para>
    /// </summary>
    public int Stream(ChunkManifest manifest, string assetDirectory,
        StandardMaterial3D material, double chainageM, double heading = 1.0)
    {
        var plan = StreamingPlan.LodPlan(manifest, chainageM, heading);
        var window = StreamingPlan.Window(manifest, chainageM, heading);
        WindowLowM = window.LowM;
        WindowHighM = window.HighM;

        // Zwalnianie idzie w kolejności posortowanej — ta sama trasa przejechana
        // dwa razy ma zwalniać pamięć w tej samej kolejności, inaczej porównanie
        // dwóch przebiegów przestaje cokolwiek znaczyć.
        var departed = new List<string>();
        foreach (var (id, _level) in _levels)
        {
            if (!plan.TryGetValue(id, out var wanted) || wanted != _level)
            {
                departed.Add(id);
            }
        }

        departed.Sort(StringComparer.Ordinal);
        foreach (var id in departed)
        {
            var node = GetNodeOrNull<Node3D>(id);
            if (node is not null)
            {
                RemoveChild(node);
                node.QueueFree();
            }

            _levels.Remove(id);
            Freed++;
        }

        foreach (var chunk in StreamingPlan.ChunksForTrain(manifest, chainageM, heading))
        {
            if (_levels.ContainsKey(chunk.Id))
            {
                continue;
            }

            var level = plan[chunk.Id];
            var path = assetDirectory.TrimEnd('/') + "/" + chunk.Lod(level).File;
            var scene = GlbLoader.Load(path);
            if (scene is null)
            {
                // Brak pliku poziomu to NIE jest powód do cichego zejścia na poziom 0:
                // scena narysowałaby wtedy pełną siatkę na horyzoncie i nikt by tego
                // nie zauważył poza spadkiem klatek. Chunk zostaje niewczytany, a
                // `GlbLoader.Load` zdążył już zgłosić błąd.
                continue;
            }

            scene.Name = chunk.Id;
            AddChild(scene);
            GlbLoader.ApplyNeutralMaterial(scene, material);
            _levels[chunk.Id] = level;
            Loaded++;
        }

        MeshNodes = CountMeshes(this);
        return _levels.Count;
    }

    /// <summary>Poziom, w jakim wisi każdy rezydentny chunk. Do metadanych zrzutu.</summary>
    public IReadOnlyDictionary<string, int> ResidentLevels => _levels;

    /// <summary>Dolny koniec okna streamowania z ostatniej klatki.</summary>
    public double WindowLowM { get; private set; }

    /// <summary>Górny koniec okna streamowania z ostatniej klatki.</summary>
    public double WindowHighM { get; private set; }

    /// <summary>Ile razy w tym przejeździe coś wczytano.</summary>
    public int Loaded { get; private set; }

    /// <summary>Ile razy w tym przejeździe coś zwolniono.</summary>
    public int Freed { get; private set; }

    private static int CountMeshes(Node node)
    {
        var count = node is MeshInstance3D ? 1 : 0;
        foreach (var child in node.GetChildren())
        {
            count += CountMeshes(child);
        }

        return count;
    }

    /// <summary>
    /// Obwiednia wczytanej geometrii tunelu w układzie świata.
    ///
    /// Metryka obrazowa nie wykryje przesunięcia całej sceny, bo kamera jedzie razem
    /// z nią — dokładnie ta sama pułapka, którą <c>tools/visual/compare.py</c> opisuje
    /// dla renderów Blenderowych. Dlatego bbox trafia do metadanych zrzutu i jest
    /// porównywany liczbowo, a nie na obrazku.
    /// </summary>
    public Aabb LoadedBounds()
    {
        Aabb? merged = null;
        foreach (var instance in MeshInstances(this))
        {
            var box = instance.GlobalTransform * instance.GetAabb();
            merged = merged is null ? box : merged.Value.Merge(box);
        }

        return merged ?? new Aabb();
    }

    private static IEnumerable<MeshInstance3D> MeshInstances(Node node)
    {
        foreach (var child in node.GetChildren())
        {
            if (child is MeshInstance3D instance)
            {
                yield return instance;
            }

            foreach (var nested in MeshInstances(child))
            {
                yield return nested;
            }
        }
    }

    /// <summary>Jedna linia do logu przejazdu.</summary>
    public string Describe(ChunkManifest manifest) => string.Create(
        CultureInfo.InvariantCulture,
        $"[TUNEL] {manifest.Id} {manifest.Variant}: rezydentne {LoadedChunks}/{manifest.Chunks.Count} chunków " +
        $"w oknie [{WindowLowM:F1}, {WindowHighM:F1}] m, {MeshNodes} siatek, " +
        $"wczytań {Loaded} zwolnień {Freed}, profil {manifest.Profile} " +
        $"{manifest.ProfileWidthM:F2}×{manifest.ProfileHeightM:F2} m, " +
        $"production_ready={manifest.ProductionReady}");
}
