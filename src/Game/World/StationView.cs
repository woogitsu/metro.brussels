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
        using var edgeMaterial = GlbLoader.NeutralMaterial(new Color(0.76f, 0.60f, 0.24f), 0.90f);
        using var slabMaterial = GlbLoader.NeutralMaterial(new Color(0.48f, 0.48f, 0.46f), 0.95f);

        _slabs.Clear();
        foreach (var instance in MeshInstances(scene))
        {
            if (IsEdgeMeshName((string)instance.Name))
            {
                instance.MaterialOverride = edgeMaterial;
            }
            else if (IsPlatformMeshName((string)instance.Name))
            {
                instance.MaterialOverride = slabMaterial;
            }

            _slabs.Add(instance.GlobalTransform * instance.GetAabb());
        }

        return _slabs.Count;
    }

    /// <summary>Generator station_kit oznacza pasy przy krawędzi sufiksem `_edge`.</summary>
    public static bool IsEdgeMeshName(string name) =>
        name.AsSpan().EndsWith(['_', 'e', 'd', 'g', 'e']);

    /// <summary>Generator station_kit oznacza płyty peronowe sufiksem `_platform`.</summary>
    private static bool IsPlatformMeshName(string name) =>
        name.AsSpan().EndsWith(['_', 'p', 'l', 'a', 't', 'f', 'o', 'r', 'm']);

    /// <summary>Use the complete bilingual name, never abbreviated feed fields.</summary>
    public static string NameMarkerText(string axisName) => axisName.Replace('|', '\n');

    /// <summary>Keep the approach sign close enough to read at a stop, while
    /// retaining the earlier sign before the terminal where track ends.</summary>
    public static double NameMarkerChainage(double stationM, double axisLengthM)
    {
        // At Parc, the outside camera 12 m beyond the train showed the -15 m
        // board only 58 px wide at 1280 px. -8 m brought it to about 80 px;
        // keep -15 m at the terminal so its only sign remains earlier on approach.
        var beforeM = stationM >= axisLengthM - 15.0 ? 15.0 : 8.0;
        return Math.Clamp(stationM - beforeM, 8.0, axisLengthM - 8.0);
    }

    /// <summary>Keep a second name readable from the stopping point.</summary>
    public static double StopMarkerChainage(double stationM, double axisLengthM) =>
        // At Beekkant, +12 m makes the stopped cab label 135 px wide instead of
        // 113 px at +15 m; +8 m clips the board in the outside view.
        Math.Clamp(stationM + 12.0, 8.0, axisLengthM - 8.0);

    /// <summary>Repeat the name on the platform approach while keeping the stop signs.</summary>
    public static double[] NameMarkerPositions(double stationM, double axisLengthM)
    {
        // In the Parc cab frame 51 m before the stop, the existing -8 m board
        // is distant; a -30 m copy is readable before it, while both stop
        // frames remain unchanged. These are design placements, not a survey.
        var entry = Math.Clamp(stationM - 30.0, 8.0, axisLengthM - 8.0);
        var approach = NameMarkerChainage(stationM, axisLengthM);
        var stop = StopMarkerChainage(stationM, axisLengthM);
        if (approach - entry >= 15.0 && stop - approach >= 15.0)
        {
            return [entry, approach, stop];
        }
        return stop - approach >= 15.0 ? [approach, stop] : [approach];
    }

    /// <summary>Station chambers are not in the playable tunnel yet; its flat ceiling is 4.70 m.</summary>
    public static float NameMarkerHangerLength(float centreHeight, float plateHeight) =>
        4.70f - (centreHeight + plateHeight / 2);

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
        using var boardMaterial = GlbLoader.NeutralMaterial(new Color(0.12f, 0.14f, 0.15f), 0.9f);
        using var hangerMaterial = GlbLoader.NeutralMaterial(new Color(0.27f, 0.30f, 0.31f), 0.7f);
        foreach (var station in sceneAxis.Axis.Stations)
        {
            var names = station.Name.Split('|');
            var bilingual = names.Length == 2;
            var text = NameMarkerText(station.Name);
            // Two bilingual lines occupy about 2 * 44 * 0.009 = 0.792 m,
            // within the 0.82 m plate and the 4.70 m playable tunnel roof.
            var fontSize = bilingual ? 44 : 60;
            var pixelSize = bilingual ? 0.009f : 0.0095f;
            var longestLine = 0;
            foreach (var name in names)
            {
                longestLine = Math.Max(longestLine, name.Length);
            }
            var width = Math.Clamp(longestLine * fontSize * pixelSize * 0.62f + 0.9f,
                2.5f, 8.0f);
            // The playable tunnel still uses box_double at stations: roof 4.70 m.
            // Keep the plate above the 3.60 m train and below that actual roof.
            var height = bilingual ? 0.82f : 0.60f;
            var centreHeight = 4.15f;
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
                var hangerLength = NameMarkerHangerLength(centreHeight, height);
                foreach (var side in new[] { -1.0f, 1.0f })
                {
                    var hanger = new MeshInstance3D
                    {
                        Mesh = new BoxMesh { Size = new Vector3(0.08f, hangerLength, 0.08f) },
                        MaterialOverride = hangerMaterial,
                        Transform = new Transform3D(orientation,
                            centre + frame.Right * (side * width * 0.38f)
                            + frame.Up * (height / 2 + hangerLength / 2)),
                    };
                    AddChild(hanger);
                }
                foreach (var side in new[] { -1.0f, 1.0f })
                {
                    // Both approaches see the board face, not a blank back plate.
                    var face = side < 0
                        ? orientation
                        : new Basis(-orientation.X, orientation.Y, -orientation.Z);
                    var label = new Label3D
                    {
                        Text = text,
                        Transform = new Transform3D(face,
                            centre
                            + frame.Forward * (side * 0.04f)),
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
