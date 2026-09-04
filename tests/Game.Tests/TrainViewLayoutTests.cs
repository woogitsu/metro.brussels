using System;
using System.Collections.Generic;
using Godot;
using MetroBxl.Game.World;
using MetroBxl.Sim.Line;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace MetroBxl.Game.Tests;

/// <summary>
/// Rozkład brył składu na osi: co jest widoczne, co ukryte i co dostaje transformację.
///
/// <para><b>Skąd ten plik.</b> Pozycja 6.B12: <c>TrainView.PlaceAt</c> nie miał ani
/// jednego testu, bo test wymagałby wczytania GLB pod silnikiem, a <c>dotnet test</c>
/// silnikiem nie jest. Mutacja <c>body.Node.Visible = covered</c> → <c>= true</c>
/// przeżyła cały przegląd przy #212 — sprawdzone ponownie 04.09.2026 na commicie
/// <c>619b179</c>: po tej mutacji <c>dotnet test tests/Game.Tests</c> dawał 84/84
/// przeszło.</para>
///
/// <para>Decyzja siedzi teraz w <see cref="TrainLayout"/> i nie dotyka silnika, a po
/// stronie sceny został wyłącznie <c>TrainView.NodeBody</c> — dwie właściwości podane
/// do <c>Node3D</c>. Tu jest przybita ta decyzja: dla prawdziwych jedenastu brył M7
/// i dla liczb, które da się policzyć na piechotę.</para>
/// </summary>
[TestClass]
public sealed class TrainViewLayoutTests
{
    /// <summary>
    /// Prawdziwy podział wzdłużny M7 z <c>tools/blender/m7_shell.py</c>: sześć pudeł
    /// i pięć mieszków, w kolejności rosnącego lokalnego X (0 = ogon w kilometrażu).
    ///
    /// <para>Liczby pochodzą z <c>tools/blender/m7_layout.py</c> — równy podział 94,0 m
    /// na sześć członów (15,666667 m) i przeguby po 1,10 m wycinane po połowie z obu
    /// stron szwu. Są tu zaokrąglone do mikrometra, bo wszystkie granice, o które te
    /// testy pytają, leżą co najmniej metry od takiego zaokrąglenia. Kod produkcyjny
    /// nadal NIE przepisuje żadnej z tych liczb: <c>TrainView.Load</c> czyta zakresy
    /// z AABB wczytanej bryły.</para>
    /// </summary>
    private static readonly (string Name, double FromM, double ToM)[] M7Bodies =
    {
        ("M7_car_1", 0.000000, 15.116667),
        ("M7_articulation_1", 15.116667, 16.216667),
        ("M7_car_2", 16.216667, 30.783333),
        ("M7_articulation_2", 30.783333, 31.883333),
        ("M7_car_3", 31.883333, 46.450000),
        ("M7_articulation_3", 46.450000, 47.550000),
        ("M7_car_4", 47.550000, 62.116667),
        ("M7_articulation_4", 62.116667, 63.216667),
        ("M7_car_5", 63.216667, 77.783333),
        ("M7_articulation_5", 77.783333, 78.883333),
        ("M7_car_6", 78.883333, 94.000000),
    };

    /// <summary>Prosta wzdłuż X, 300 m. Z zawsze 0 — profil pionowy ma status not_modelled.</summary>
    private static TrackAxis StraightAxis() => TrackAxis.FromJson("""
        {"id":"TEST","crs":"EPSG:31370",
         "points":[[0,0,0],[100,0,0],[200,0,0],[300,0,0]],
         "stations":[]}
        """);

    private static SceneAxis Scene() => new(StraightAxis(), 2.10);

    private static FakeBody[] M7Train()
    {
        var bodies = new FakeBody[M7Bodies.Length];
        for (var index = 0; index < M7Bodies.Length; index++)
        {
            var (name, fromM, toM) = M7Bodies[index];
            bodies[index] = new FakeBody(name, fromM, toM);
        }

        return bodies;
    }

    private static FakeBody[] Train(params (double FromM, double ToM)[] spans)
    {
        var bodies = new FakeBody[spans.Length];
        for (var index = 0; index < spans.Length; index++)
        {
            bodies[index] = new FakeBody($"b{index}", spans[index].FromM, spans[index].ToM);
        }

        return bodies;
    }

    // --- długość i ogon ---------------------------------------------------------

    [TestMethod]
    public void LengthIsTheSpanOfTheBodiesAndTheM7ShellIs94Metres()
    {
        Assert.AreEqual(11, M7Train().Length, "sześć pudeł i pięć mieszków");
        Assert.AreEqual(94.0, TrainLayout.LengthM(M7Train()), 1e-9,
            "rozpiętość brył M7 to 94,0 m — data/vehicle/m7-spec.json");
    }

    [TestMethod]
    public void RearIsFrontMinusTheMeasuredLength()
    {
        // Ogon, nie czoło. Pomyłka tutaj przesuwa CAŁY skład o 94 m i nie zapala się
        // nigdzie indziej, bo scena nadal wygląda jak scena.
        Assert.AreEqual(0.0, TrainLayout.RearChainageM(M7Train(), 94.0), 1e-9);
        Assert.AreEqual(106.0, TrainLayout.RearChainageM(M7Train(), 200.0), 1e-9);
        Assert.AreEqual(-94.0, TrainLayout.RearChainageM(M7Train(), 0.0), 1e-9,
            "czoło na zerze znaczy ogon 94 m PRZED początkiem osi");
    }

    [TestMethod]
    public void PlanIsIndexedInBodyOrderAndCarriesTheChordItDecidedOn()
    {
        var bodies = M7Train();
        var plan = TrainLayout.Plan(StraightAxis(), bodies, 200.0);

        Assert.AreEqual(11, plan.Count);
        for (var index = 0; index < plan.Count; index++)
        {
            Assert.AreEqual(index, plan[index].Index, "plan trzyma kolejność brył");
            Assert.AreEqual(bodies[index].Span, plan[index].Span);
            Assert.AreEqual(106.0 + bodies[index].Span.FromM, plan[index].FromChainageM, 1e-9);
            Assert.AreEqual(106.0 + bodies[index].Span.ToM, plan[index].ToChainageM, 1e-9);
        }
    }

    // --- cztery zmierzone przypadki ---------------------------------------------

    [TestMethod]
    public void WholeTrainOnTheAxisShowsEveryBody()
    {
        var bodies = M7Train();
        var visible = TrainLayout.Place(Scene(), bodies, 200.0);

        Assert.AreEqual(11, visible, "skład cały na osi: wszystkie bryły widoczne");
        foreach (var body in bodies)
        {
            Assert.IsTrue(body.Visible, $"{body.Name} ma być widoczna");
            Assert.AreEqual(1, body.TransformWrites, $"{body.Name} ma dostać transformację");
        }
    }

    [TestMethod]
    public void MeasuredHiddenCountsForTheRealM7Train()
    {
        // Liczby są POLICZONE dla podziału M7 wyżej, nie zgadnięte i nie podane
        // nierównością. Bryła jest widoczna wtedy i tylko wtedy, gdy jej cięciwa ma na
        // osi niezerową długość, czyli gdy `ogon + ToM > 0`; przy czole na kilometrażu
        // f jest to `ToM > 94 − f`:
        //   f =  0 m → 94 −  0 = 94,0 → żadna bryła nie ma ToM > 94,0     → ukryte 11
        //   f = 20 m → 94 − 20 = 74,0 → car_5, articulation_5, car_6      → ukryte  8
        //   f = 50 m → 94 − 50 = 44,0 → car_3..car_6 z mieszkami (7 brył) → ukryte  4
        //   f = 94 m → 94 − 94 =  0,0 → wszystkie                         → ukryte  0
        var expected = new (double FrontM, int Hidden)[]
        {
            (0.0, 11),
            (20.0, 8),
            (50.0, 4),
            (94.0, 0),
        };

        foreach (var (frontM, hidden) in expected)
        {
            var plan = TrainLayout.Plan(StraightAxis(), M7Train(), frontM);
            Assert.AreEqual(hidden, TrainLayout.HiddenCount(plan),
                $"czoło na {frontM} m: ukrytych brył ma być {hidden}");
            Assert.AreEqual(11 - hidden, plan.Count - TrainLayout.HiddenCount(plan),
                $"czoło na {frontM} m: widocznych brył ma być {11 - hidden}");
        }
    }

    [TestMethod]
    public void HiddenBodiesAreTheOnesBehindTheStartOfTheAxis()
    {
        // Nie tylko ILE, ale KTÓRE: ukrywają się bryły od strony ogona, po kolei.
        // Sam licznik przeszedłby też wtedy, gdyby ukrywały się bryły od czoła.
        var plan = TrainLayout.Plan(StraightAxis(), M7Train(), 50.0);
        var expected = new[] { false, false, false, false, true, true, true, true, true, true, true };

        for (var index = 0; index < plan.Count; index++)
        {
            Assert.AreEqual(expected[index], plan[index].Visible,
                $"{M7Bodies[index].Name} przy czole na 50 m");
        }
    }

    [TestMethod]
    public void TrainRunningOffTheEndOfTheAxisHidesTheOverhangingBodies()
    {
        // Oś ma 300 m, czoło jedzie na 320 m: ogon stoi na 226 m, więc bryły o lokalnym
        // FromM ≥ 74,0 m leżą całe za końcem osi. To articulation_5 (77,783) i car_6
        // (78,883) — dwie.
        var plan = TrainLayout.Plan(StraightAxis(), M7Train(), 320.0);

        Assert.AreEqual(2, TrainLayout.HiddenCount(plan), "za koniec osi wystają dwie bryły");
        Assert.IsFalse(plan[9].Visible, "M7_articulation_5 jest już za końcem osi");
        Assert.IsFalse(plan[10].Visible, "M7_car_6 jest już za końcem osi");
        Assert.IsTrue(plan[8].Visible, "M7_car_5 jeszcze nie");

        // Skład, który zjechał z osi CAŁY, nie ma ani jednej widocznej bryły.
        var beyond = TrainLayout.Plan(StraightAxis(), M7Train(), 500.0);
        Assert.AreEqual(11, TrainLayout.HiddenCount(beyond));
    }

    [TestMethod]
    public void ABodyTouchingZeroWithItsEndIsHiddenButOneStraddlingZeroIsNot()
    {
        // Granica, o którą chodzi: cięciwa STYKAJĄCA się z zerem końcem daje po
        // przycięciu dwa razy ten sam punkt, więc ramki z niej nie ma. Cięciwa, której
        // zero wypada w środku, jest niezerowa i bryłę wolno postawić.
        // Trzy bryły po 10 m; czoło na 10 m znaczy ogon na −20 m.
        var touching = TrainLayout.Plan(
            StraightAxis(), Train((0.0, 10.0), (10.0, 20.0), (20.0, 30.0)), 10.0);
        Assert.IsFalse(touching[0].Visible, "[−20; −10] leży całe przed osią");
        Assert.IsFalse(touching[1].Visible, "[−10; 0] dotyka zera KOŃCEM — nadal zerowa cięciwa");
        Assert.IsTrue(touching[2].Visible, "[0; 10] leży na osi");
        Assert.AreEqual(2, TrainLayout.HiddenCount(touching));

        // Ten sam skład 5 m dalej: środkowa bryła ma teraz zero w środku.
        var straddling = TrainLayout.Plan(
            StraightAxis(), Train((0.0, 10.0), (10.0, 20.0), (20.0, 30.0)), 15.0);
        Assert.IsFalse(straddling[0].Visible, "[−15; −5] wciąż całe przed osią");
        Assert.IsTrue(straddling[1].Visible, "[−5; 5] przechodzi przez zero — bryłę wolno postawić");
        Assert.IsTrue(straddling[2].Visible);
        Assert.AreEqual(1, TrainLayout.HiddenCount(straddling));
    }

    // --- wykonanie planu -------------------------------------------------------

    [TestMethod]
    public void PlaceHidesTheBodiesThatTheAxisDoesNotCoverAndPlacesNoTransformOnThem()
    {
        // TO jest test, który zabija mutację `Visible = covered` → `= true`. Atrapy
        // startują widoczne, tak jak świeżo wczytany węzeł Godota, więc mutacja
        // zostawiłaby je widoczne i nikt by tego nie zauważył.
        var bodies = M7Train();
        var visible = TrainLayout.Place(Scene(), bodies, 20.0);

        Assert.AreEqual(3, visible, "czoło na 20 m: trzy bryły na osi");
        for (var index = 0; index < bodies.Length; index++)
        {
            var body = bodies[index];
            var shouldBeVisible = index >= 8;
            Assert.AreEqual(shouldBeVisible, body.Visible, $"{body.Name} widoczność");
            Assert.AreEqual(1, body.VisibleWrites, $"{body.Name} dostaje decyzję dokładnie raz");
            Assert.AreEqual(shouldBeVisible ? 1 : 0, body.TransformWrites,
                $"{body.Name}: bryła ukryta NIE dostaje transformacji");
        }
    }

    [TestMethod]
    public void PlaceHidesEverythingWhenTheTrainStartsAtChainageZero()
    {
        // Przejazd całą linią startuje na pierwszej stacji, czyli na kilometrażu 0.
        // Cały skład leży wtedy przed początkiem osi i nie ma ani jednej bryły do
        // postawienia — obejście `DriveScenario.PackageAFirstRun` (start na 94,0 m)
        // właśnie dlatego istnieje.
        var bodies = M7Train();
        var visible = TrainLayout.Place(Scene(), bodies, 0.0);

        Assert.AreEqual(0, visible);
        foreach (var body in bodies)
        {
            Assert.IsFalse(body.Visible, $"{body.Name} nie ma na czym stać");
            Assert.AreEqual(0, body.TransformWrites, $"{body.Name} nie dostaje transformacji");
        }
    }

    [TestMethod]
    public void PlacedTransformSitsOnTheChordThePlanDecidedOn()
    {
        // Kontrola, że wykonanie planu bierze cięciwę Z PLANU, a nie liczy jej po raz
        // drugi: transformacja musi wyjść dokładnie taka, jak z jawnie podanego ogona.
        var bodies = M7Train();
        TrainLayout.Place(Scene(), bodies, 200.0);

        var expected = Scene().BodyTransform(106.0, M7Bodies[10].FromM, M7Bodies[10].ToM);
        var got = bodies[10].Transform;
        Assert.AreEqual(expected.Origin.X, got.Origin.X, 1e-4f, "X środka pudła");
        Assert.AreEqual(expected.Origin.Y, got.Origin.Y, 1e-4f, "Y środka pudła");
        Assert.AreEqual(expected.Origin.Z, got.Origin.Z, 1e-4f, "Z środka pudła");

        // I że to naprawdę jest ostatnie pudło składu. Origin transformacji jest
        // lokalnym zerem BRYŁY, czyli ogonem składu (106 m), a nie środkiem pudła —
        // środek trzeba dopiero przez tę transformację przepuścić. Wypada wtedy w
        // połowie cięciwy [184,883; 200,0], czyli na 192,442 m.
        Assert.AreEqual(106.0f, got.Origin.X, 1e-3f, "lokalne X = 0 ląduje na ogonie składu");
        var centre = got * new Vector3(
            (float)(0.5 * (M7Bodies[10].FromM + M7Bodies[10].ToM)), 0.0f, 0.0f);
        Assert.AreEqual(192.4417f, centre.X, 1e-3f, "środek car_6 w połowie własnej cięciwy");
        Assert.AreEqual(2.10f, centre.Z, 1e-3f, "pudło stoi na osi TORU, 2,10 m od osi trasy");
    }

    [TestMethod]
    public void ApplyRefusesAPlanOfADifferentLength()
    {
        var bodies = M7Train();
        var plan = TrainLayout.Plan(StraightAxis(), Train((0.0, 10.0)), 100.0);
        Assert.ThrowsException<ArgumentException>(() => TrainLayout.Apply(Scene(), bodies, plan));
    }

    [TestMethod]
    public void PlaceRefusesANullAxisAndANullTrain()
    {
        Assert.ThrowsException<ArgumentNullException>(
            () => TrainLayout.Place(null!, M7Train(), 100.0));
        Assert.ThrowsException<ArgumentNullException>(
            () => TrainLayout.Place(Scene(), null!, 100.0));
    }

    /// <summary>
    /// Bryła bez silnika: zapisuje, co jej ustawiono i ile razy.
    ///
    /// <para>Startuje WIDOCZNA, bo świeżo wczytany <c>Node3D</c> jest widoczny —
    /// atrapa zaczynająca od <c>false</c> przepuściłaby mutację, która zawsze pokazuje
    /// bryłę, i cały ten plik nie miałby sensu.</para>
    /// </summary>
    private sealed class FakeBody : ITrainBody
    {
        private bool _visible = true;
        private Transform3D _transform = Transform3D.Identity;

        internal FakeBody(string name, double fromM, double toM)
        {
            Name = name;
            Span = new BodySpan(fromM, toM);
        }

        internal string Name { get; }

        internal int VisibleWrites { get; private set; }

        internal int TransformWrites { get; private set; }

        public BodySpan Span { get; }

        public bool Visible
        {
            get => _visible;
            set
            {
                _visible = value;
                VisibleWrites++;
            }
        }

        public Transform3D Transform
        {
            get => _transform;
            set
            {
                _transform = value;
                TransformWrites++;
            }
        }
    }
}
