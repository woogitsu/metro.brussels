using System;
using Godot;
using MetroBxl.Game.World;
using MetroBxl.Sim.Line;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace MetroBxl.Game.Tests;

/// <summary>
/// Most między układem danych a układem sceny. To jest najbardziej krytyczna
/// arytmetyka tej warstwy: gdyby przeliczenie było złe, tunel i skład wylądowałyby
/// w różnych miejscach, a bramka zrzutów zobaczyłaby normalnie wyglądający kadr.
///
/// Audyt mutacyjny 02.09.2026: mutacje `TrackOffsetM 2.10→0.0` i
/// `CabEyeHeightM 2.20→0.0` PRZEŻYŁY cały `godot-first-run.yml`. Kontrola zgodności
/// osi z manifestem (tolerancja 1e-3 m, kod wyjścia 10) porównuje DŁUGOŚĆ osi,
/// a nie odsunięcie toru od niej ani wysokość oka nad główką szyny.
/// </summary>
[TestClass]
public sealed class SceneAxisTests
{
    /// <summary>Prosta wzdłuż X. Z zawsze 0 — profil pionowy ma status not_modelled.</summary>
    private static TrackAxis StraightAxis() => TrackAxis.FromJson("""
        {"id":"TEST","crs":"EPSG:31370",
         "points":[[0,0,0],[100,0,0],[200,0,0],[300,0,0]],
         "stations":[]}
        """);

    private static SceneAxis Scene(double offsetM) => new(StraightAxis(), offsetM);

    [TestMethod]
    public void FixtureBeyondPlayableEndFollowsContinuationCurveAndStopsAtItsEnd()
    {
        var route = Scene(2.10);
        var tail = new SceneAxis(TrackAxis.FromJson("""
            {"id":"TAIL","points":[[300,0,0],[310,0,0],[320,10,0],[330,20,0]],"stations":[]}
            """), 2.10);
        var fixture = route.FixturePoint(route.Axis.LengthM + 25.0, tail, 0.0, 3.35);
        Assert.IsTrue(fixture.HasValue);
        Assert.IsTrue(fixture.Value.Z < -10.0f,
            "oprawa ma skręcać z osią scenerii, a nie iść prostą za osią jazdy");
        Assert.IsNull(route.FixturePoint(route.Axis.LengthM + tail.Axis.LengthM + 1.0,
            tail, 0.0, 3.35), "po końcu zmierzonej scenerii nie wolno dopisywać lamp");
        Assert.IsNull(route.FixturePoint(route.Axis.LengthM + 1.0, null, 0.0, 3.35),
            "bez geometrii scenerii nie wolno zgadywać przebiegu lamp");
    }

    [TestMethod]
    public void ToSceneSwapsDataAxesIntoGodotAxes()
    {
        // Dane mają Z w górę, Godot ma Y w górę i −Z do przodu: (X, Z, −Y).
        var scene = SceneAxis.ToScene(new AxisPoint(10.0, 20.0, 3.0));
        Assert.AreEqual(10.0f, scene.X, 1e-6f, "X zostaje X");
        Assert.AreEqual(3.0f, scene.Y, 1e-6f, "Z danych staje się Y sceny (w górę)");
        Assert.AreEqual(-20.0f, scene.Z, 1e-6f, "Y danych staje się −Z sceny");
    }

    [TestMethod]
    public void TheSwapIsNotTheIdentity()
    {
        // Kontrola negatywna do testu wyżej: gdyby ToScene przepisywało współrzędne
        // jeden do jednego, tamten test przechodziłby dla punktu leżącego na osi X.
        var scene = SceneAxis.ToScene(new AxisPoint(0.0, 7.0, 0.0));
        Assert.AreNotEqual(7.0f, scene.Y, "Y danych nie może zostać Y sceny");
        Assert.AreEqual(-7.0f, scene.Z, 1e-6f);
    }

    [TestMethod]
    public void CentreLinePointIsTheRouteAxisWithoutTheTrackOffset()
    {
        // Dokumentacja metody mówi wprost „bez przesunięcia na tor" — więc odsunięcie
        // NIE może tu przeciekać, choćby konstruktor je dostał.
        var offset = Scene(2.10);
        var point = offset.CentreLinePoint(150.0);
        Assert.AreEqual(150.0f, point.X, 1e-3f);
        Assert.AreEqual(0.0f, point.Y, 1e-3f, "Z danych to 0, więc Y sceny to 0");
        Assert.AreEqual(0.0f, point.Z, 1e-3f, "oś trasy, nie oś toru");
    }

    [TestMethod]
    public void ChordMovesTheTrackSidewaysByExactlyTheOffset()
    {
        // Dokładnie ta liczba, którą psuła przeżywająca mutacja TrackOffsetM 2.10→0.0.
        var centred = Scene(0.0).Chord(140.0, 160.0);
        var offset = Scene(2.10).Chord(140.0, 160.0);

        Assert.AreEqual(centred.Origin.X, offset.Origin.X, 1e-3f,
            "odsunięcie toru nie może przesuwać wzdłuż osi");
        Assert.AreEqual(centred.Origin.Y, offset.Origin.Y, 1e-3f,
            "odsunięcie toru nie może podnosić toru");
        Assert.AreEqual(2.10f, Math.Abs(offset.Origin.Z - centred.Origin.Z), 1e-3f,
            "odsunięcie ma być w bok i wynosić 2,10 m");
    }

    [TestMethod]
    public void ZeroOffsetPutsTheTrackOnTheRouteAxis()
    {
        var frame = Scene(0.0).Chord(100.0, 120.0);
        Assert.AreEqual(0.0f, frame.Origin.Z, 1e-3f);
    }

    [TestMethod]
    public void ChordFrameIsRightHandedAndOrthonormal()
    {
        var frame = Scene(2.10).Chord(100.0, 120.0);
        foreach (var (name, axis) in new[]
                 { ("forward", frame.Forward), ("right", frame.Right), ("up", frame.Up) })
        {
            Assert.AreEqual(1.0f, axis.Length(), 1e-4f, $"{name} nie jest jednostkowy");
        }

        Assert.AreEqual(0.0f, frame.Forward.Dot(frame.Right), 1e-4f);
        Assert.AreEqual(0.0f, frame.Forward.Dot(frame.Up), 1e-4f);
        Assert.AreEqual(0.0f, frame.Right.Dot(frame.Up), 1e-4f);
    }

    [TestMethod]
    public void AZeroLengthChordIsRefusedInsteadOfProducingGarbage()
    {
        // Cięciwa zerowej długości dałaby kierunek NaN i bryłę w losowej orientacji.
        Assert.ThrowsException<InvalidOperationException>(() => Scene(0.0).Chord(100.0, 100.0));
    }

    [TestMethod]
    public void CabPointSitsAboveTheRailHeadByTheGivenHeight()
    {
        // Druga liczba, którą psuła przeżywająca mutacja: CabEyeHeightM 2.20→0.0.
        var axis = Scene(2.10);
        var (low, _) = axis.CabPoint(150.0, 1.80, 0.0, 0.0);
        var (high, _) = axis.CabPoint(150.0, 1.80, 2.20, 0.0);
        Assert.AreEqual(2.20f, high.Y - low.Y, 1e-3f, "oko ma być 2,20 m nad główką szyny");
    }

    [TestMethod]
    public void CabPointSetbackMovesTheEyeBackAlongTheAxisNotSideways()
    {
        var axis = Scene(0.0);
        var (nose, _) = axis.CabPoint(150.0, 0.0, 2.20, 0.0);
        (var behind, _) = axis.CabPoint(150.0, 1.80, 2.20, 0.0);
        Assert.AreEqual(1.80f, nose.X - behind.X, 1e-2f, "odsunięcie ma cofać wzdłuż osi");
        Assert.AreEqual(nose.Z, behind.Z, 1e-3f, "odsunięcie nie może przesuwać w bok");
    }

    [TestMethod]
    public void BodyTransformKeepsTheBodyLengthItWasGiven()
    {
        // Bryła osadzona na cięciwie ma zachować swoją długość: transformacja jest
        // obrotem i przesunięciem, nie skalowaniem.
        var axis = Scene(2.10);
        var transform = axis.BodyTransform(100.0, 0.0, 15.667);
        foreach (var column in new[] { transform.Basis.X, transform.Basis.Y, transform.Basis.Z })
        {
            Assert.AreEqual(1.0f, column.Length(), 1e-4f, "baza skaluje bryłę");
        }
    }

    [TestMethod]
    public void CabPointBeforeTheAxisStartUsesTheFirstChordInsteadOfThrowing()
    {
        // Znalezione URUCHOMIENIEM trybu `--line`, nie lekturą: przejazd całą linią
        // startuje na pierwszej stacji, czyli na kilometrażu 0, więc oko maszynisty
        // wypada na −1,8 m (odsunięcie z `DesignAssumptions.CabEyeSetbackM`). Okno
        // cięciwy [−2,8; −0,8] leżało wtedy CAŁE przed początkiem osi, `PointAt`
        // przycinał oba końce do tego samego punktu, a `Chord` rzucał
        // „zerowa cięciwa między 0 m a -0.8 m". Scena wypisywała trzynaście takich
        // wyjątków na przebieg i przebieg mimo to kończył się kodem 0.
        var scene = Scene(2.10);

        var (position, forward) = scene.CabPoint(0.0, 1.8, 2.20, 0.0);

        Assert.IsFalse(float.IsNaN(position.X) || float.IsNaN(position.Y) || float.IsNaN(position.Z));
        Assert.AreEqual(1.0f, forward.Length(), 1e-5f, "kierunek nie jest znormalizowany");

        // Oś testowa biegnie wzdłuż +X, więc w scenie kierunek to +X.
        Assert.AreEqual(1.0f, forward.X, 1e-5f, "kierunek na starcie nie jest pierwszą cięciwą osi");
        Assert.AreEqual(2.20f, position.Y, 1e-5f, "wysokość oka nad główką szyny się nie zgadza");
    }

    [TestMethod]
    public void CabPointDeepInsideTheAxisIsUnchangedByTheClamp()
    {
        // Kontrola po DRUGIEJ stronie: przycięcie nie ma prawa ruszyć położenia kamery
        // tam, gdzie okno cięciwy i tak leży w osi. Bez tego „naprawiłem start" nie
        // dałoby się odróżnić od „przesunąłem kamerę na całym przebiegu", a bramka
        // wizualna T-012 porównuje zrzuty co do piksela.
        var scene = Scene(2.10);
        var (position, forward) = scene.CabPoint(150.0, 1.8, 2.20, 0.0);

        Assert.AreEqual(150.0 - 1.8, position.X, 1e-4, "kamera przesunęła się wzdłuż osi");
        Assert.AreEqual(1.0f, forward.X, 1e-5f);
    }

    [TestMethod]
    public void SmoothCabPointSpreadsDirectionChangesAcrossTheCurve()
    {
        var route = TrackAxis.FromJson("""
            {"id":"BEND","crs":"EPSG:31370",
             "points":[[0,0,0],[20,0,0],[40,5,0],[60,20,0],[75,40,0],[80,60,0]],
             "stations":[]}
            """);
        var scene = new SceneAxis(route, 2.10);
        var largestSmoothStep = 0.0f;
        var largestRawStep = 0.0f;
        for (var at = 10.0; at <= route.LengthM - 11.0; at += 0.25)
        {
            var smoothA = scene.SmoothCabPoint(at, 0.0, 2.20, 0.0);
            var smoothB = scene.SmoothCabPoint(at + 0.25, 0.0, 2.20, 0.0);
            var rawA = scene.CabPoint(at, 0.0, 2.20, 0.0);
            var rawB = scene.CabPoint(at + 0.25, 0.0, 2.20, 0.0);
            largestSmoothStep = Math.Max(largestSmoothStep, smoothA.Forward.AngleTo(smoothB.Forward));
            largestRawStep = Math.Max(largestRawStep, rawA.Forward.AngleTo(rawB.Forward));
            Assert.AreEqual(2.20f, smoothA.Position.Y, 1e-3f,
                "wygładzanie nie może zmieniać wysokości oka");
            Assert.AreEqual(1.0f, smoothA.Forward.Length(), 1e-4f,
                "kierunek kamery musi pozostać wektorem jednostkowym");
        }

        Assert.IsTrue(largestSmoothStep < largestRawStep * 0.7f,
            $"Największy skok kierunku: wygładzony {largestSmoothStep}, surowy {largestRawStep}");
    }

    [TestMethod]
    public void SmoothCabPointKeepsBothAxisEndsAndJoinsInteriorWithoutAJump()
    {
        var route = TrackAxis.FromJson("""
            {"id":"ENDS","crs":"EPSG:31370",
             "points":[[0,0,0],[20,5,0],[40,20,0],[60,40,0]],
             "stations":[]}
            """);
        var scene = new SceneAxis(route, 2.10);
        foreach (var at in new[] { 0.0, route.LengthM })
        {
            var original = scene.CabPoint(at, 0.0, 2.20, 0.0);
            var smooth = scene.SmoothCabPoint(at, 0.0, 2.20, 0.0);
            var endChord = at == 0.0
                ? scene.Chord(0.0, Math.Min(route.LengthM, 1.0))
                : scene.Chord(Math.Max(0.0, route.LengthM - 1.0), route.LengthM);
            var expected = scene.CentreLinePoint(at)
                + endChord.Right * 2.10f + endChord.Up * 2.20f;
            Assert.AreEqual(expected.X, smooth.Position.X, 1e-5f,
                "oko musi leżeć na końcu osi, nie w środku ostatniej cięciwy");
            Assert.AreEqual(expected.Y, smooth.Position.Y, 1e-5f,
                "wysokość oka nad końcem osi musi pozostać dokładna");
            Assert.AreEqual(expected.Z, smooth.Position.Z, 1e-5f,
                "odsunięcie oka od toru na końcu osi musi pozostać dokładne");
            Assert.AreEqual(0.0f, original.Forward.AngleTo(smooth.Forward), 1e-5f,
                "kierunek kamery na końcu osi nie może się zmienić");
        }

        // Granica 9 m to koniec wygaszania filtra. Sąsiednie próbki nie mogą
        // przenieść kamery o wiele więcej niż przebyta odległość na osi.
        foreach (var boundary in new[] { 9.0, route.LengthM - 9.0 })
        {
            var left = scene.SmoothCabPoint(boundary - 0.01, 0.0, 2.20, 0.0);
            var right = scene.SmoothCabPoint(boundary + 0.01, 0.0, 2.20, 0.0);
            Assert.IsTrue(left.Position.DistanceTo(right.Position) < 0.03f,
                "kamera nie może przeskakiwać na granicy wygaszania filtra");
            Assert.IsTrue(left.Forward.AngleTo(right.Forward) < 0.01f,
                "kamera nie może obracać się skokowo na granicy filtra");
        }
    }

    [TestMethod]
    public void SmoothCabPointHasNoFirstOrLastFrameJumpOnRealAxesAt80Kmh()
    {
        var frameDistanceM = 80.0 / 3.6 / 120.0;
        foreach (var id in new[] { "L1_A", "L1_B", "L2_E", "L5_C", "L5_D", "L6_F" })
        {
            var route = TrackAxis.FromJson(
                MetroBxl.Tests.Shared.KorzenRepozytorium.Tresc("data", "track", id + ".json"));
            var scene = new SceneAxis(route, 2.10);
            var first = scene.SmoothCabPoint(0.0, 0.0, 2.20, 0.0);
            var afterFirst = scene.SmoothCabPoint(frameDistanceM, 0.0, 2.20, 0.0);
            var beforeLast = scene.SmoothCabPoint(route.LengthM - frameDistanceM, 0.0, 2.20, 0.0);
            var last = scene.SmoothCabPoint(route.LengthM, 0.0, 2.20, 0.0);
            var firstStep = first.Position.DistanceTo(afterFirst.Position);
            var lastStep = beforeLast.Position.DistanceTo(last.Position);
            Assert.IsTrue(firstStep < 0.22f && lastStep < 0.22f,
                $"{id}: oko przeskakuje na końcu osi: pierwszy krok {firstStep:F3} m, ostatni {lastStep:F3} m");
            Assert.AreEqual(0.0f, scene.CabPoint(0.0, 0.0, 2.20, 0.0).Forward.AngleTo(first.Forward),
                1e-5f, $"{id}: poprawka położenia nie może obracać kamery na starcie");
        }
    }

    [TestMethod]
    public void ConstructorRefusesAMissingAxis()
    {
        Assert.ThrowsException<ArgumentNullException>(() => new SceneAxis(null!, 2.10));
    }
}
