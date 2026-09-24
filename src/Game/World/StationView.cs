using System;
using System.Collections.Generic;
using System.Globalization;
using Godot;
using MetroBxl.Game.Assets;

namespace MetroBxl.Game.World;

/// <summary>
/// Widok peronów: płyty i pasy ostrzegawcze wszystkich stacji pakietu, wczytane
/// z jednego GLB wyprodukowanego przez <c>tools/blender/station_kit.py</c>, oraz
/// neutralne tablice z nazwami stacji utworzone z danych osi.
///
/// <b>Dlaczego bez transformacji i bez streamowania.</b> Bez transformacji z tego
/// samego powodu, co chunki tunelu: <c>station_kit.py</c> zamiata przekrój wzdłuż tej
/// samej osi, co <c>tunnel_sweep.py</c>, czyli bryły są w KILOMETRAŻU OSI, a eksporter
/// glTF przeliczył Z-w-górę na Y-w-górę przy zapisie. Każda transformacja tutaj byłaby
/// drugą zamianą układu i rozjechałaby peron z torem. Bez streamowania, bo dwanaście
/// stacji pakietu A to 48 brył, 3456 ścian i 294 kB — o dwa rzędy wielkości mniej niż
/// tunel, dla którego streamowanie powstało. Małe tablice z nazwami stacji nie
/// zmieniają tej decyzji. Gdy dojdzie reszta sieci, ta decyzja
/// wróci na warsztat i to zdanie jest jej terminem ważności.
///
/// <b>Gdzie jest decyzja.</b> Nie tutaj. Pomiary — co stoi przy zatrzymaniu, jak
/// wysoko sięga płyta — liczy <see cref="PlatformFit"/>, który nie dotyka silnika
/// i ma testy w <c>tests/Game.Tests/PlatformFitTests.cs</c>. Tej klasie zostaje
/// wczytanie pliku, zebranie obwiedni brył i neutralne oznaczenie stacji.
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
        // The generated warning strips have their own `_edge` meshes. Give them
        // a readable, unbranded color instead of the slab's gray override.
        var edgeMaterial = GlbLoader.NeutralMaterial(new Color(0.92f, 0.74f, 0.28f), 0.85f);

        _slabs.Clear();
        foreach (var instance in MeshInstances(scene))
        {
            if (IsEdgeMeshName((string)instance.Name))
            {
                instance.MaterialOverride = edgeMaterial;
            }

            _slabs.Add(instance.GlobalTransform * instance.GetAabb());
        }

        return _slabs.Count;
    }

    /// <summary>Generator station_kit oznacza pasy przy krawędzi sufiksem `_edge`.</summary>
    public static bool IsEdgeMeshName(string name) =>
        name.AsSpan().EndsWith(['_', 'e', 'd', 'g', 'e']);

    /// <summary>Use the complete bilingual name, never abbreviated feed fields.</summary>
    public static string NameMarkerText(string axisName) => axisName.Replace('|', '\n');

    /// <summary>Show the name on approach while keeping terminal markers inside the route.</summary>
    public static double NameMarkerChainage(double stationM, double axisLengthM) =>
        Math.Clamp(stationM - 15.0, 8.0, axisLengthM - 8.0);

    /// <summary>Keep a second name visible from the stopping point.</summary>
    public static double StopMarkerChainage(double stationM, double axisLengthM) =>
        Math.Clamp(stationM + 15.0, 8.0, axisLengthM - 8.0);

    /// <summary>Avoid overlapping signs where route ends clamp the two positions together.</summary>
    public static double[] NameMarkerPositions(double stationM, double axisLengthM)
    {
        var approach = NameMarkerChainage(stationM, axisLengthM);
        var stop = StopMarkerChainage(stationM, axisLengthM);
        return stop - approach >= 15.0 ? [approach, stop] : [approach];
    }

    /// <summary>
    /// Place a neutral station-name marker above the tracks at each platform.
    /// The names come from the axis, not from copied operator signage.
    /// </summary>
    public int AddNameMarkers(SceneAxis sceneAxis, string plateGlbPath)
    {
        if (_slabs.Count == 0)
        {
            return 0;
        }

        var platePrototype = GlbLoader.Load(plateGlbPath);
        if (platePrototype is null)
        {
            return 0;
        }

        var count = 0;
        var boardMaterial = GlbLoader.NeutralMaterial(new Color(0.12f, 0.14f, 0.15f), 0.9f);
        foreach (var station in sceneAxis.Axis.Stations)
        {
            var names = station.Name.Split('|');
            var bilingual = names.Length == 2;
            var text = NameMarkerText(station.Name);
            var fontSize = bilingual ? 46 : 60;
            var pixelSize = bilingual ? 0.0095f : 0.016f;
            var longestLine = 0;
            foreach (var name in names)
            {
                longestLine = Math.Max(longestLine, name.Length);
            }
            var width = Math.Clamp(longestLine * fontSize * pixelSize * 0.62f + 0.9f,
                2.5f, 8.0f);
            // Keep at least 0.25 m above the 3.60 m vehicle roof and 0.35 m
            // below the 5.30 m chamber ceiling, including the two-line plate.
            var height = bilingual ? 1.1f : 0.8f;
            var centreHeight = bilingual ? 4.40f : 4.25f;
            foreach (var at in NameMarkerPositions(station.ChainageM, sceneAxis.Axis.LengthM))
            {
                var frame = sceneAxis.Chord(at - 0.5, at + 0.5);
                var centre = sceneAxis.CentreLinePoint(at) + frame.Up * centreHeight;
                var orientation = new Basis(frame.Right, frame.Up, -frame.Forward);
                var board = (Node3D)platePrototype.Duplicate();
                board.Transform = new Transform3D(
                    new Basis(orientation.X * width, orientation.Y * height, orientation.Z), centre);
                GlbLoader.ApplyNeutralMaterial(board, boardMaterial);
                AddChild(board);
                var label = new Label3D
                {
                    Text = text,
                    Transform = new Transform3D(orientation,
                        centre - frame.Up * (bilingual ? 0.12f : 0.0f) - frame.Forward * 0.04f),
                    FontSize = fontSize,
                    PixelSize = pixelSize,
                    Modulate = new Color(0.90f, 0.91f, 0.90f),
                    OutlineModulate = new Color(0.07f, 0.08f, 0.09f),
                    OutlineSize = 6,
                    DoubleSided = true,
                    NoDepthTest = false,
                };
                AddChild(label);
            }
            count++;
        }

        platePrototype.Free();
        return count;
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
