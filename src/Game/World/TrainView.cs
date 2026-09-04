using System;
using System.Collections.Generic;
using System.Globalization;
using Godot;
using MetroBxl.Game.Assets;
using MetroBxl.Sim.Line;

namespace MetroBxl.Game.World;

/// <summary>Lokalny zakres X jednej bryły składu, tak jak go niesie jej AABB.</summary>
/// <param name="FromM">Koniec bliższy ogonowi składu.</param>
/// <param name="ToM">Koniec bliższy czołu składu.</param>
public readonly record struct BodySpan(double FromM, double ToM);

/// <summary>
/// Decyzja o jednej bryle: gdzie na osi leży jej cięciwa i czy wolno ją postawić.
/// </summary>
/// <param name="Index">Pozycja bryły w liście widoku.</param>
/// <param name="Span">Lokalny zakres X bryły — potrzebny do policzenia jej środka.</param>
/// <param name="FromChainageM">Chainage końca <c>Span.FromM</c>.</param>
/// <param name="ToChainageM">Chainage końca <c>Span.ToM</c>.</param>
/// <param name="Visible">Czy oś pokrywa tę cięciwę, czyli czy bryłę wolno postawić.</param>
public readonly record struct BodyPlacement(
    int Index,
    BodySpan Span,
    double FromChainageM,
    double ToChainageM,
    bool Visible);

/// <summary>
/// Bryła, którą widok składu ustawia: w scenie <c>Node3D</c>, w teście atrapa.
///
/// <para><b>Po co ten interfejs istnieje.</b> <c>dotnet test</c> nie jest silnikiem,
/// więc <c>Node3D</c> w teście nie powstanie, a <c>TrainView.PlaceAt</c> nie miał do
/// 04.09.2026 ani jednego testu — mutacja <c>Visible = covered</c> → <c>= true</c>
/// przeżyła przegląd przy #212. Interfejs przenosi całą pętlę ustawiania do kodu, który
/// da się zawołać bez silnika; po stronie sceny zostaje tylko przekazanie dwóch
/// właściwości do węzła (<c>TrainView.NodeBody</c>). To ta sama droga, którą repozytorium
/// przeszło dla modułów <c>bpy</c>: decyzja w czystym kodzie, wywołanie silnika cienkie
/// jak tylko da się je zrobić.</para>
/// </summary>
public interface ITrainBody
{
    /// <summary>Lokalny zakres X bryły.</summary>
    BodySpan Span { get; }

    /// <summary>Widoczność bryły w scenie.</summary>
    bool Visible { get; set; }

    /// <summary>Transformacja bryły w scenie.</summary>
    Transform3D Transform { get; set; }
}

/// <summary>
/// Rozkład brył składu na osi — cała decyzja o widoczności i o transformacie,
/// bez ani jednego wywołania silnika.
///
/// <para><c>TrackAxis.CoversChord</c> odpowiada na pytanie o JEDNĄ cięciwę i jest
/// przetestowany w <c>tests/Sim.Tests</c>. Brakowało strony wywołania: przy zadanym
/// kilometrażu czoła to tutaj powstaje lista decyzji dla wszystkich jedenastu brył M7,
/// razem z arytmetyką ogona. Ogon jest częścią decyzji, nie szczegółem pętli — pomyłka
/// w nim przesuwa cały skład o 94 m i nie zapala się nigdzie indziej.</para>
/// </summary>
public static class TrainLayout
{
    /// <summary>
    /// Długość składu jako rozpiętość zakresów brył. Liczona z geometrii, nie z 94,0 m
    /// wpisanych w kod: przy zmianie podziału członów nie ma tu czego poprawiać.
    /// </summary>
    public static double LengthM(IReadOnlyList<ITrainBody> bodies)
    {
        ArgumentNullException.ThrowIfNull(bodies);
        if (bodies.Count == 0)
        {
            return 0.0;
        }

        var min = double.PositiveInfinity;
        var max = double.NegativeInfinity;
        foreach (var body in bodies)
        {
            min = Math.Min(min, body.Span.FromM);
            max = Math.Max(max, body.Span.ToM);
        }

        return max - min;
    }

    /// <summary>Chainage ogona składu, którego czoło stoi w <paramref name="frontChainageM"/>.</summary>
    public static double RearChainageM(IReadOnlyList<ITrainBody> bodies, double frontChainageM) =>
        frontChainageM - LengthM(bodies);

    /// <summary>Decyzja o jednej bryle: jej cięciwa na osi i to, czy oś ją pokrywa.</summary>
    public static BodyPlacement PlacementFor(
        TrackAxis axis, BodySpan span, double rearChainageM, int index)
    {
        ArgumentNullException.ThrowIfNull(axis);

        // Bryła leżąca CAŁA poza osią zostaje UKRYTA, a nie postawiona gdziekolwiek.
        // Przy przejeździe rozpoczętym na pierwszej stacji (kilometraż 0) cały skład
        // leży 94 m przed początkiem osi; `TrackAxis.PointAt` przycina kilometraż, więc
        // oba końce takiej cięciwy dają ten sam punkt i ramki nie da się zbudować.
        // Ukrycie jest jedyną odpowiedzią, która nie zmyśla geometrii: osi tam po prostu
        // nie ma. Bryła wjeżdża na oś i pojawia się sama.
        var from = rearChainageM + span.FromM;
        var to = rearChainageM + span.ToM;
        return new BodyPlacement(index, span, from, to, axis.CoversChord(from, to));
    }

    /// <summary>
    /// Lista decyzji dla całego składu, którego czoło stoi w <paramref name="frontChainageM"/>.
    /// Kolejność odpowiada kolejności brył w liście.
    /// </summary>
    public static IReadOnlyList<BodyPlacement> Plan(
        TrackAxis axis, IReadOnlyList<ITrainBody> bodies, double frontChainageM)
    {
        ArgumentNullException.ThrowIfNull(axis);
        ArgumentNullException.ThrowIfNull(bodies);

        var rear = RearChainageM(bodies, frontChainageM);
        var plan = new List<BodyPlacement>(bodies.Count);
        for (var index = 0; index < bodies.Count; index++)
        {
            plan.Add(PlacementFor(axis, bodies[index].Span, rear, index));
        }

        return plan;
    }

    /// <summary>Liczba brył, których oś nie pokrywa — czyli tych ukrytych.</summary>
    public static int HiddenCount(IReadOnlyList<BodyPlacement> plan)
    {
        ArgumentNullException.ThrowIfNull(plan);

        var hidden = 0;
        foreach (var placement in plan)
        {
            if (!placement.Visible)
            {
                hidden++;
            }
        }

        return hidden;
    }

    /// <summary>
    /// Wykonuje gotowy plan: ustawia widoczność każdej bryły, a transformację **tylko**
    /// tym, które oś pokrywa. Bryła ukryta nie dostaje żadnej transformacji, bo nie ma
    /// jej z czego policzyć — <c>SceneAxis.Chord</c> rzuciłby na zerowej cięciwie.
    /// </summary>
    public static void Apply(
        SceneAxis axis, IReadOnlyList<ITrainBody> bodies, IReadOnlyList<BodyPlacement> plan)
    {
        ArgumentNullException.ThrowIfNull(axis);
        ArgumentNullException.ThrowIfNull(bodies);
        ArgumentNullException.ThrowIfNull(plan);
        if (plan.Count != bodies.Count)
        {
            throw new ArgumentException(
                $"plan ma {plan.Count} pozycji, a skład {bodies.Count} brył", nameof(plan));
        }

        for (var index = 0; index < bodies.Count; index++)
        {
            var placement = plan[index];
            bodies[index].Visible = placement.Visible;
            if (placement.Visible)
            {
                bodies[index].Transform = axis.BodyTransform(placement);
            }
        }
    }

    /// <summary>Plan i jego wykonanie w jednym kroku. Zwraca liczbę ustawionych brył.</summary>
    public static int Place(
        SceneAxis axis, IReadOnlyList<ITrainBody> bodies, double frontChainageM)
    {
        ArgumentNullException.ThrowIfNull(axis);

        var plan = Plan(axis.Axis, bodies, frontChainageM);
        Apply(axis, bodies, plan);
        return plan.Count - HiddenCount(plan);
    }
}

/// <summary>
/// Widok składu M7: sześć pudeł i pięć mieszków ze skorupy z <c>tools/blender/m7_shell.py</c>,
/// każde ustawiane osobno na własnej cięciwie osi.
///
/// <b>Skąd biorą się zakresy członów.</b> Nie z przepisanych stałych, tylko z bryły
/// pojazdu: lokalny zakres X każdego węzła siatki jest odczytywany z jego AABB. Dzięki
/// temu warstwa silnika nie powtarza ani jednej liczby z <c>m7_layout.py</c> — ustawia
/// dokładnie tę geometrię, którą dostała, i przy zmianie podziału członów nie trzeba
/// tu niczego poprawiać. Skopiowana stała rozjeżdża się po cichu; odczytana nie.
///
/// <b>Gdzie jest decyzja.</b> Nie tutaj. Widoczność i transformację liczy
/// <see cref="TrainLayout"/>, który nie dotyka silnika i jest przybity w
/// <c>tests/Game.Tests/TrainViewLayoutTests.cs</c>. Tej klasie zostaje wczytanie skorupy
/// i przekazanie dwóch właściwości do węzłów.
/// </summary>
public sealed partial class TrainView : Node3D
{
    private readonly List<NodeBody> _bodies = new();

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

            _bodies.Add(new NodeBody(mesh, new BodySpan(box.Position.X, box.End.X)));
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
    /// Ogon liczy się od czoła przez zmierzoną rozpiętość brył, a nie przez 94,0 m
    /// wpisane w kod: jeśli generator kiedyś zmieni długość, skład nadal będzie stał
    /// całością na osi. Cała arytmetyka i cała decyzja o widoczności są w
    /// <see cref="TrainLayout"/> — ta metoda nie ma własnego wariantu.
    /// </summary>
    public void PlaceAt(SceneAxis axis, double frontChainageM) =>
        TrainLayout.Place(axis, _bodies, frontChainageM);

    /// <summary>Jedna linia do logu przejazdu.</summary>
    public string Describe() => string.Create(
        CultureInfo.InvariantCulture,
        $"[SKŁAD] brył={BodyCount} długość={LengthM:F3} m szerokość={WidthM:F3} m dach={RoofHeightM:F3} m nad główką szyny");

    /// <summary>
    /// Węzeł sceny jako <see cref="ITrainBody"/>.
    ///
    /// <para>To jest CAŁA granica między decyzją a silnikiem — dwie właściwości
    /// przekazane do <c>Node3D</c> i nic więcej. Wszystko, co da się sprawdzić bez
    /// silnika, leży po drugiej stronie tej granicy, w <see cref="TrainLayout"/>.</para>
    /// </summary>
    private sealed class NodeBody : ITrainBody
    {
        internal NodeBody(Node3D node, BodySpan span)
        {
            Node = node;
            Span = span;
        }

        internal Node3D Node { get; }

        public BodySpan Span { get; }

        public bool Visible
        {
            get => Node.Visible;
            set => Node.Visible = value;
        }

        public Transform3D Transform
        {
            get => Node.Transform;
            set => Node.Transform = value;
        }
    }
}
