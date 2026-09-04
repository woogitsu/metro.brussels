using System;
using System.Collections.Generic;
using System.Globalization;
using Godot;
using MetroBxl.Game.Assets;

namespace MetroBxl.Game.World;

/// <summary>
/// Widok peronów: płyty i pasy ostrzegawcze wszystkich stacji pakietu, wczytane
/// z jednego GLB wyprodukowanego przez <c>tools/blender/station_kit.py</c>.
///
/// <b>Dlaczego bez transformacji i bez streamowania.</b> Bez transformacji z tego
/// samego powodu, co chunki tunelu: <c>station_kit.py</c> zamiata przekrój wzdłuż tej
/// samej osi, co <c>tunnel_sweep.py</c>, czyli bryły są w KILOMETRAŻU OSI, a eksporter
/// glTF przeliczył Z-w-górę na Y-w-górę przy zapisie. Każda transformacja tutaj byłaby
/// drugą zamianą układu i rozjechałaby peron z torem. Bez streamowania, bo dwanaście
/// stacji pakietu A to 48 brył, 3456 ścian i 294 kB — o dwa rzędy wielkości mniej niż
/// tunel, dla którego streamowanie powstało. Gdy dojdzie reszta sieci, ta decyzja
/// wróci na warsztat i to zdanie jest jej terminem ważności.
///
/// <b>Gdzie jest decyzja.</b> Nie tutaj. Pomiary — co stoi przy zatrzymaniu, jak
/// wysoko sięga płyta — liczy <see cref="PlatformFit"/>, który nie dotyka silnika
/// i ma testy w <c>tests/Game.Tests/PlatformFitTests.cs</c>. Tej klasie zostaje
/// wczytanie pliku i zebranie obwiedni brył.
/// </summary>
public sealed partial class StationView : Node3D
{
    private readonly List<Aabb> _slabs = new();

    /// <summary>Liczba brył peronowych trzymanych w scenie.</summary>
    public int SlabCount => _slabs.Count;

    /// <summary>Obwiednie brył w układzie świata; do pomiarów i do metadanych zrzutu.</summary>
    public IReadOnlyList<Aabb> Slabs => _slabs;

    /// <summary>
    /// Wczytuje GLB peronów i zapamiętuje obwiednię każdej bryły. Zwraca liczbę brył;
    /// zero znaczy „nie wczytałem nic" i wołający ma to sprawdzić.
    ///
    /// <para>Wynik wczytania NIE jest tu przemilczany ani podmieniany na wartość
    /// zastępczą — to ta sama pułapka, którą Issue #107 złapał na
    /// <c>TrainView.Load</c>: scena szła dalej bez składu, metadane opisywały tylko
    /// tunel i cały <c>godot-first-run.yml</c> zostawał zielony.</para>
    /// </summary>
    public int Load(string glbPath, StandardMaterial3D material)
    {
        var scene = GlbLoader.Load(glbPath);
        if (scene is null)
        {
            return 0;
        }

        scene.Name = "Platforms";
        AddChild(scene);
        GlbLoader.ApplyNeutralMaterial(scene, material);

        _slabs.Clear();
        foreach (var instance in MeshInstances(scene))
        {
            _slabs.Add(instance.GlobalTransform * instance.GetAabb());
        }

        return _slabs.Count;
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
    public string Describe()
    {
        var bounds = PlatformFit.Merge(_slabs);
        if (bounds is null)
        {
            return "[PERON] brak brył";
        }

        var box = bounds.Value;
        return string.Create(
            CultureInfo.InvariantCulture,
            $"[PERON] brył={_slabs.Count} góra płyty={box.End.Y:F3} m nad główką szyny, " +
            $"obwiednia {box.Size.X:F1} x {box.Size.Y:F2} x {box.Size.Z:F1} m");
    }
}
