using System;
using System.Collections.Generic;
using Godot;
using MetroBxl.Game.World;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace MetroBxl.Game.Tests;

/// <summary>
/// Pomiar brył peronu. Jedyna kontrola peronu w scenie przed 04.09.2026 byłaby
/// zrzutem ekranu — a zrzut nie odróżnia peronu, którego nie ma, od peronu
/// wczytanego 1000 m dalej: oba dają kadr pustego tunelu.
///
/// <para>Bryły są dobrane tak, jak stoją naprawdę na pakiecie A: płyta biegnie od
/// 3,53 m od osi trasy (2,10 m odsunięcia toru + 1,35 m połowy szerokości M7
/// + 0,08 m szczeliny) do 7,50 m, a jej górna powierzchnia leży 1,03 m nad główką
/// szyny — na wysokości podłogi M7.</para>
/// </summary>
[TestClass]
public sealed class PlatformFitTests
{
    [TestMethod]
    public void CameraFootprintUsesCurvedSurfaceOnEitherSideAndRejectsEmptySpace()
    {
        // Two straight pieces joined at a right angle stand in for a swept bend.
        // Their union's box also covers (7, 7), where no platform exists.
        var curved = new PlatformFit.Footprint(
            new Aabb(new Vector3(0, 0, 0), new Vector3(10, 1, 10)),
            new Vector3[]
            {
                new(0, 1, 0), new(10, 1, 0), new(0, 1, 2),
                new(10, 1, 0), new(10, 1, 2), new(0, 1, 2),
                new(0, 1, 2), new(2, 1, 2), new(0, 1, 10),
                new(2, 1, 2), new(2, 1, 10), new(0, 1, 10),
            });
        var otherSide = new PlatformFit.Footprint(
            new Aabb(new Vector3(0, 0, -10), new Vector3(10, 1, 2)),
            new Vector3[]
            {
                new(0, 1, -10), new(10, 1, -10), new(0, 1, -8),
                new(10, 1, -10), new(10, 1, -8), new(0, 1, -8),
            });

        Assert.IsFalse(PlatformFit.Covers(new[] { curved }, new Vector3(7, 2.7f, 7)),
            "obwiednia łuku obejmuje pustkę, lecz trójkąty płyty jej nie obejmują");
        Assert.IsTrue(PlatformFit.Covers(new[] { curved }, new Vector3(1, 2.7f, 7)),
            "kamera nad zakrzywioną płytą zostaje zaakceptowana");
        Assert.IsTrue(PlatformFit.Covers(new[] { otherSide }, new Vector3(5, 2.7f, -9)),
            "płyta po drugiej stronie osi też jest możliwym miejscem kamery");
        Assert.IsFalse(PlatformFit.Covers(Array.Empty<PlatformFit.Footprint>(),
            new Vector3(5, 2.7f, -9)), "między stacjami nie ma płyty");
        var right = new Vector3(1, 2.7f, 7);
        var left = new Vector3(5, 2.7f, -9);
        var fallback = new Vector3(5, 2.0f, -4.2f);
        Assert.AreEqual(right, PlatformFit.CameraPosition(new[] { curved, otherSide },
            right, left, fallback), "gdy są obie płyty, kamera wybiera pierwszą");
        Assert.AreEqual(left, PlatformFit.CameraPosition(new[] { otherSide },
            right, left, fallback), "po odrzuceniu pustej obwiedni wybiera drugą płytę");
        Assert.AreEqual(fallback, PlatformFit.CameraPosition(
            Array.Empty<PlatformFit.Footprint>(), right, left, fallback),
            "bez płyty wraca do widoku bocznego");
    }

    /// <summary>Płyta peronu po prawej stronie osi, o zadanym zakresie wzdłuż X.</summary>
    private static Aabb Slab(float fromX, float toX, float side = 1.0f) => new(
        new Vector3(fromX, 0.0f, side > 0 ? 3.53f : -7.50f),
        new Vector3(toX - fromX, 1.031f, 3.97f));

    private static IReadOnlyList<Aabb> Beekkant() => new[]
    {
        Slab(462.73f, 556.73f, 1.0f),
        Slab(462.73f, 556.73f, -1.0f),
    };

    [TestMethod]
    public void HorizontalDistanceIgnoresHeight()
    {
        // Oko maszynisty jest na 2,20 m, góra płyty na 1,03 m. Gdyby pomiar szedł
        // w trzech wymiarach, peron pod nogami raportowałby odległość 1,17 m i nie
        // dałoby się jej odróżnić od peronu odsuniętego o tyle samo w bok.
        var slab = Slab(0.0f, 94.0f);
        var nad = new Vector3(47.0f, 2.20f, 5.0f);
        Assert.AreEqual(0.0, PlatformFit.HorizontalDistanceM(slab, nad), 1e-6,
            "punkt nad płytą leży w jej rzucie, więc odległość pozioma to zero");
    }

    [TestMethod]
    public void HorizontalDistanceIsTheGapToTheNearestFace()
    {
        // Oś trasy (Z = 0) wobec płyty zaczynającej się 3,53 m od niej.
        var slab = Slab(0.0f, 94.0f);
        var naOsi = new Vector3(47.0f, 0.0f, 0.0f);
        Assert.AreEqual(3.53, PlatformFit.HorizontalDistanceM(slab, naOsi), 1e-4);
    }

    [TestMethod]
    public void HorizontalDistanceMeasuresBothAxesAtOnce()
    {
        // Punkt poza bryłą i wzdłuż osi, i w bok: 3-4-5. Bez składowej X ten test
        // przechodziłby dla każdej odległości wzdłuż toru, a to jest właśnie ta
        // składowa, która odróżnia peron tej stacji od peronu następnej.
        var slab = Slab(0.0f, 94.0f);
        var point = new Vector3(-4.0f, 0.0f, 0.53f);
        Assert.AreEqual(5.0, PlatformFit.HorizontalDistanceM(slab, point), 1e-4);
    }

    [TestMethod]
    public void NearFindsBothSlabsOfTheStationYouStandOn()
    {
        var found = PlatformFit.Near(Beekkant(), new Vector3(509.43f, 0.0f, 0.0f), 20.0);
        CollectionAssert.AreEqual(new[] { 0, 1 }, (System.Collections.ICollection)found,
            "na peronie Beekkant scena stoi między obiema płytami");
    }

    [TestMethod]
    public void NearFindsNothingBetweenStations()
    {
        // Kontrola negatywna do testu wyżej. Gdyby `Near` zwracało wszystko, tamten
        // test przechodziłby tak samo dobrze — i bramka metadanych przestałaby
        // odróżniać „peron jest przy składzie" od „peron jest gdziekolwiek".
        var found = PlatformFit.Near(Beekkant(), new Vector3(976.0f, 0.0f, 0.0f), 20.0);
        Assert.AreEqual(0, found.Count,
            "między Beekkant a Étangs Noirs nie ma peronu i scena nie ma prawa go widzieć");
    }

    [TestMethod]
    public void NearRespectsTheRadius()
    {
        // Płyta zaczyna się 3,53 m od osi trasy, więc promień 3,5 m jej nie sięga,
        // a 3,6 m sięga. Ten test przybija, że promień jest UŻYWANY, a nie tylko
        // przekazywany: mutacja na stałą 0 albo na nieskończoność wywraca go.
        var slabs = Beekkant();
        var point = new Vector3(509.43f, 0.0f, 0.0f);
        Assert.AreEqual(0, PlatformFit.Near(slabs, point, 3.5).Count);
        Assert.AreEqual(2, PlatformFit.Near(slabs, point, 3.6).Count);
    }

    [TestMethod]
    public void NearRefusesANegativeRadius()
    {
        Assert.ThrowsException<ArgumentOutOfRangeException>(
            () => PlatformFit.Near(Beekkant(), Vector3.Zero, -1.0));
    }

    [TestMethod]
    public void MergeIsTheUnionOfTheBoxes()
    {
        var merged = PlatformFit.Merge(Beekkant());
        Assert.IsNotNull(merged);
        var box = merged!.Value;
        Assert.AreEqual(462.73f, box.Position.X, 1e-2f);
        Assert.AreEqual(556.73f, box.End.X, 1e-2f);
        Assert.AreEqual(-7.50f, box.Position.Z, 1e-2f, "obie strony osi razem");
        Assert.AreEqual(7.50f, box.End.Z, 1e-2f);
    }

    [TestMethod]
    public void MergeOfNothingIsNullAndNotAPointAtTheOrigin()
    {
        // `new Aabb()` to prostopadłościan zerowy zaczepiony w początku układu:
        // liczba, która wygląda jak pomiar i nią nie jest. Scena bez peronu ma
        // powiedzieć „nie było czego mierzyć", a nie podać zero.
        Assert.IsNull(PlatformFit.Merge(Array.Empty<Aabb>()));
        Assert.IsNull(PlatformFit.TopM(Array.Empty<Aabb>()));
    }

    [TestMethod]
    public void TopIsTheHighestPointOfTheSlabsNotTheLowest()
    {
        var top = PlatformFit.TopM(Beekkant());
        Assert.IsNotNull(top);
        Assert.AreEqual(1.031, top!.Value, 1e-3,
            "góra płyty razem z pasem ostrzegawczym, czyli wysokość podłogi M7 + 1 mm");
    }

    [TestMethod]
    public void TopOfTheSelectedSlabsOnlyIgnoresTheRest()
    {
        // Peron sąsiedniej stacji postawiony o metr wyżej nie ma prawa zmienić
        // wysokości peronu, na którym stoi skład.
        var slabs = new List<Aabb>(Beekkant())
        {
            new(new Vector3(1404.9f, 2.0f, 3.53f), new Vector3(94.0f, 1.031f, 3.97f)),
        };

        var only = PlatformFit.Near(slabs, new Vector3(509.43f, 0.0f, 0.0f), 20.0);
        Assert.AreEqual(1.031, PlatformFit.TopM(slabs, only)!.Value, 1e-3);
        Assert.AreEqual(3.031, PlatformFit.TopM(slabs)!.Value, 1e-3,
            "bez wyboru bryły pomiar obejmuje także tamten peron — i to jest różnica, "
            + "o którą chodzi w rozdzieleniu obu liczb w metadanych");
    }
}
