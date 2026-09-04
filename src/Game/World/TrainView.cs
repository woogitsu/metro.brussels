using System;
using System.Collections.Generic;
using System.Globalization;
using Godot;
using MetroBxl.Game.Assets;

namespace MetroBxl.Game.World;

/// <summary>
/// Widok składu M7: sześć pudeł i pięć mieszków ze skorupy z <c>tools/blender/m7_shell.py</c>,
/// każde ustawiane osobno na własnej cięciwie osi.
///
/// <b>Skąd biorą się zakresy członów.</b> Nie z przepisanych stałych, tylko z bryły
/// pojazdu: lokalny zakres X każdego węzła siatki jest odczytywany z jego AABB. Dzięki
/// temu warstwa silnika nie powtarza ani jednej liczby z <c>m7_layout.py</c> — ustawia
/// dokładnie tę geometrię, którą dostała, i przy zmianie podziału członów nie trzeba
/// tu niczego poprawiać. Skopiowana stała rozjeżdża się po cichu; odczytana nie.
/// </summary>
public sealed partial class TrainView : Node3D
{
    private readonly List<(Node3D Node, double FromM, double ToM)> _bodies = new();

    /// <summary>Długość składu zmierzona z wczytanej bryły.</summary>
    public double LengthM { get; private set; }

    /// <summary>Szerokość składu zmierzona z wczytanej bryły.</summary>
    public double WidthM { get; private set; }

    /// <summary>Wysokość górnej krawędzi bryły nad główką szyny.</summary>
    public double RoofHeightM { get; private set; }

    /// <summary>Liczba ustawianych brył (pudła + mieszki).</summary>
    public int BodyCount => _bodies.Count;

    /// <summary>Wczytuje skorupę i przygotowuje bryły do ustawiania. Zwraca liczbę brył.</summary>
    public int Load(string shellPath, StandardMaterial3D material)
    {
        var scene = GlbLoader.Load(shellPath);
        if (scene is null)
        {
            return 0;
        }

        var minX = double.PositiveInfinity;
        var maxX = double.NegativeInfinity;
        var minZ = double.PositiveInfinity;
        var maxZ = double.NegativeInfinity;
        var maxY = double.NegativeInfinity;

        foreach (var child in scene.GetChildren())
        {
            if (child is not MeshInstance3D mesh || mesh.Mesh is null)
            {
                continue;
            }

            var box = mesh.Mesh.GetAabb();
            minX = Math.Min(minX, box.Position.X);
            maxX = Math.Max(maxX, box.End.X);
            minZ = Math.Min(minZ, box.Position.Z);
            maxZ = Math.Max(maxZ, box.End.Z);
            maxY = Math.Max(maxY, box.End.Y);

            _bodies.Add((mesh, box.Position.X, box.End.X));
        }

        foreach (var body in _bodies)
        {
            // Właściciela trzeba zdjąć **przed** przepięciem, inaczej Godot ostrzega
            // o niespójnym owner: węzeł nadal należałby do sceny, której już nie ma.
            body.Node.Owner = null;
            scene.RemoveChild(body.Node);
            AddChild(body.Node);
        }

        scene.QueueFree();

        LengthM = maxX - minX;
        WidthM = maxZ - minZ;
        RoofHeightM = maxY;

        GlbLoader.ApplyNeutralMaterial(this, material);
        return _bodies.Count;
    }

    /// <summary>
    /// Ustawia wszystkie bryły dla zadanego chainage **czoła** składu.
    ///
    /// Ogon liczy się od czoła przez zmierzoną długość bryły, a nie przez 94,0 m
    /// wpisane w kod: jeśli generator kiedyś zmieni długość, skład nadal będzie stał
    /// całością na osi.
    /// </summary>
    public void PlaceAt(SceneAxis axis, double frontChainageM)
    {
        ArgumentNullException.ThrowIfNull(axis);
        var rear = frontChainageM - LengthM;
        foreach (var body in _bodies)
        {
            // Bryła leżąca CAŁA poza osią zostaje UKRYTA, a nie postawiona gdziekolwiek.
            // Przy przejeździe rozpoczętym na pierwszej stacji (kilometraż 0) ogon składu
            // wystaje 94 m przed początek osi; `TrackAxis.PointAt` przycina kilometraż,
            // więc oba końce takiej cięciwy dają ten sam punkt i ramki nie da się
            // zbudować. Ukrycie jest jedyną odpowiedzią, która nie zmyśla geometrii:
            // osi tam po prostu nie ma. Bryła wjeżdża na oś i pojawia się sama.
            var covered = axis.Axis.CoversChord(rear + body.FromM, rear + body.ToM);
            body.Node.Visible = covered;
            if (covered)
            {
                body.Node.Transform = axis.BodyTransform(rear, body.FromM, body.ToM);
            }
        }
    }

    /// <summary>Jedna linia do logu przejazdu.</summary>
    public string Describe() => string.Create(
        CultureInfo.InvariantCulture,
        $"[SKŁAD] brył={BodyCount} długość={LengthM:F3} m szerokość={WidthM:F3} m dach={RoofHeightM:F3} m nad główką szyny");
}
