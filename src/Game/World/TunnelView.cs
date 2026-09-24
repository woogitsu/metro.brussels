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
    private readonly Dictionary<string, Node3D> _detailPrototypes = new(StringComparer.Ordinal);
    private bool _detailsPreloaded;
    private Node3D? _visualContinuation;

    /// <summary>Liczba chunków rezydentnych w tej chwili.</summary>
    public int LoadedChunks => _levels.Count;

    /// <summary>Łączna liczba węzłów siatki w tunelu.</summary>
    public int MeshNodes { get; private set; }

    /// <summary>Liczba siatek rezydentnych chunków osi jazdy, bez scenerii za końcem osi.</summary>
    public int ResidentMeshNodes
    {
        get
        {
            var count = 0;
            foreach (var id in _levels.Keys)
            {
                if (GetNodeOrNull<Node3D>(id) is { } chunk)
                    count += CountMeshes(chunk);
            }
            return count;
        }
    }

    /// <summary>Siatki osobnej scenerii za osią jazdy, łącznie z detalem toru.</summary>
    public int VisualContinuationMeshNodes =>
        _visualContinuation is null ? 0 : CountMeshes(_visualContinuation);

    /// <summary>Obwiednia scenerii za osią jazdy; brak pary zasobów daje null.</summary>
    public Aabb? VisualContinuationBounds() =>
        _visualContinuation is null ? null : BoundsFor(_visualContinuation);

    /// <summary>
    /// Keep measured route scenery visible beyond the last playable stop. This
    /// does not enter the chunk manifest, driving axis, collision or simulation.
    /// Zero means an older asset set without the optional pair; -1 means a
    /// partial or unreadable pair.
    /// </summary>
    public int LoadVisualContinuation(string tunnelPath, string detailPath,
        StandardMaterial3D material)
    {
        var hasTunnel = FileAccess.FileExists(tunnelPath);
        var hasDetail = FileAccess.FileExists(detailPath);
        if (!hasTunnel && !hasDetail)
            return 0;
        if (!hasTunnel || !hasDetail)
            return -1;

        var tunnel = GlbLoader.Load(tunnelPath);
        var detail = GlbLoader.Load(detailPath);
        if (tunnel is null || detail is null)
        {
            tunnel?.Free();
            detail?.Free();
            return -1;
        }

        GlbLoader.ApplyNeutralMaterial(tunnel, material);
        AddChild(tunnel);
        tunnel.AddChild(detail);
        _visualContinuation = tunnel;
        MeshNodes = CountMeshes(this);
        return CountMeshes(tunnel);
    }

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
        // Detale toru są niewielkie, ale parsowanie GLB podczas jazdy powoduje
        // wyraźne przycięcie na granicy chunku. Przygotuj je przed pierwszą klatką.
        if (!_detailsPreloaded)
        {
            foreach (var chunk in manifest.Chunks)
            {
                var path = assetDirectory.TrimEnd('/') + "/" + chunk.Id + "_detail.glb";
                if (FileAccess.FileExists(path) && GlbLoader.Load(path) is { } prototype)
                    _detailPrototypes.Add(chunk.Id, prototype);
            }

            _detailsPreloaded = true;
        }

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
            // Blender exports design-preview track furniture in world coordinates
            // alongside each tunnel chunk. Keep its individual rail, ballast and
            // light materials: applying the tunnel override would make everything
            // the same gray again. Older asset sets without detail still load.
            if (_detailPrototypes.TryGetValue(chunk.Id, out var prototype))
            {
                var detail = (Node3D)prototype.Duplicate();
                detail.Name = "TrackDetail";
                scene.AddChild(detail);
            }
            _levels[chunk.Id] = level;
            Loaded++;
        }

        MeshNodes = CountMeshes(this);
        return _levels.Count;
    }

    /// <summary>Zwalnia przygotowane siatki po zamknięciu sceny.</summary>
    public override void _ExitTree()
    {
        foreach (var prototype in _detailPrototypes.Values)
            prototype.Free();
        _detailPrototypes.Clear();
        base._ExitTree();
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
    /// Obwiednia rezydentnych chunków przejezdnej osi w układzie świata.
    ///
    /// Metryka obrazowa nie wykryje przesunięcia całej sceny, bo kamera jedzie razem
    /// z nią — dokładnie ta sama pułapka, którą <c>tools/visual/compare.py</c> opisuje
    /// dla renderów Blenderowych. Dlatego bbox trafia do metadanych zrzutu i jest
    /// porównywany liczbowo, a nie na obrazku.
    /// </summary>
    public Aabb LoadedBounds()
    {
        Aabb? merged = null;
        foreach (var id in _levels.Keys)
        {
            if (GetNodeOrNull<Node3D>(id) is not { } chunk)
                continue;
            var box = BoundsFor(chunk);
            if (box is not null)
                merged = merged is null ? box : merged.Value.Merge(box.Value);
        }

        return merged ?? new Aabb();
    }

    private static Aabb? BoundsFor(Node root)
    {
        Aabb? merged = null;
        foreach (var instance in MeshInstances(root))
        {
            var box = instance.GlobalTransform * instance.GetAabb();
            merged = merged is null ? box : merged.Value.Merge(box);
        }
        return merged;
    }

    private static IEnumerable<MeshInstance3D> MeshInstances(Node node)
    {
        if (node is MeshInstance3D instance)
            yield return instance;
        foreach (var child in node.GetChildren())
        {
            foreach (var nested in MeshInstances(child))
                yield return nested;
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
