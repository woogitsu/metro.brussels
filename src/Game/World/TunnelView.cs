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
    private readonly List<string> _loaded = new();

    /// <summary>Liczba wczytanych chunków.</summary>
    public int LoadedChunks => _loaded.Count;

    /// <summary>Łączna liczba węzłów siatki w tunelu.</summary>
    public int MeshNodes { get; private set; }

    /// <summary>
    /// Wczytuje wszystkie chunki poziomu 0 z manifestu. Zwraca liczbę wczytanych plików.
    ///
    /// <b>Bez streamowania.</b> Cały pakiet A to 12 plików, 867 kB i 16176 trójkątów —
    /// mniej niż jeden budżetowy próg czegokolwiek. Predykat okna z
    /// <c>tools/blender/sweep.py</c> jest gotowy i przetestowany **po stronie Pythona**;
    /// przepisanie go tutaj bez przeniesienia jego testów dałoby drugą implementację
    /// bez kontroli, a to jest gorsze niż jawny brak streamowania.
    /// </summary>
    public int LoadAll(ChunkManifest manifest, string assetDirectory, StandardMaterial3D material)
    {
        foreach (var chunk in manifest.Chunks)
        {
            var path = assetDirectory.TrimEnd('/') + "/" + chunk.File;
            var scene = GlbLoader.Load(path);
            if (scene is null)
            {
                continue;
            }

            scene.Name = chunk.Id;
            AddChild(scene);
            MeshNodes += GlbLoader.ApplyNeutralMaterial(scene, material);
            _loaded.Add(chunk.Id);
        }

        return _loaded.Count;
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
        $"[TUNEL] {manifest.Id} {manifest.Variant}: wczytano {LoadedChunks}/{manifest.Chunks.Count} chunków, " +
        $"{MeshNodes} siatek, profil {manifest.Profile} {manifest.ProfileWidthM:F2}×{manifest.ProfileHeightM:F2} m, " +
        $"production_ready={manifest.ProductionReady}");
}
