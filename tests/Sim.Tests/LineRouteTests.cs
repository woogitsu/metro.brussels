using System;
using System.Collections.Generic;
using System.Linq;
using MetroBxl.Sim.Line;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace MetroBxl.Sim.Tests;

/// <summary>
/// Trasa linii złożona z pakietów (T-320).
///
/// `reports/network-chainage.md` mówi wprost: **„nie ma czegoś takiego jak kilometraż
/// linii 1"** — jest kilometraż pakietu A i pakietu B, a między nimi odcinek, którego
/// nie ma w `data/track/`. Rozkład z T-113 opisuje natomiast całe linie, więc bez
/// sklejenia pakietów nie da się porównać rdzenia ze zmierzonym rozkładem.
/// </summary>
[TestClass]
public sealed class LineRouteTests
{
    /// <summary>Merode → Montgomery: jedyna przerwa linii 1. OBIE liczby zmierzone.</summary>
    /// <remarks>
    /// Długość 708,9 m — łamana źródłowa STIB `ACTU_LIGNES_BRUTES`, linia `001m` v1
    /// (`reports/packages-BF-alignment.md` §8). Czas 63 s — mediana z GTFS
    /// (`build/timetable.json`, segment MERODE → MONTGOMERY, T-113).
    /// </remarks>
    private static readonly RouteGap MerodeMontgomery =
        new("Merode", "Montgomery", 708.9, 63.0);

    private static TrackAxis Axis(string id, double lengthM, params (string Name, double At)[] stations)
    {
        var stops = string.Join(",", stations.Select((s, i) =>
            $"{{\"name\":\"{s.Name}\",\"chainage_m\":{s.At.ToString(System.Globalization.CultureInfo.InvariantCulture)},\"stop_id\":\"{i}\"}}"));
        var json = $$"""
        {"id":"{{id}}","crs":"EPSG:31370",
         "points":[[0,0,0],[{{lengthM.ToString(System.Globalization.CultureInfo.InvariantCulture)}},0,0]],
         "stations":[{{stops}}]}
        """;
        return TrackAxis.FromJson(json);
    }

    private static LineRoute L1() => new(
        "L1",
        new[]
        {
            Axis("L1_A", 6686.4, ("Gare de l'Ouest", 0.0), ("Merode", 6686.4)),
            Axis("L1_B", 5083.2, ("Montgomery", 0.0), ("Stockel", 5083.2)),
        },
        new[] { MerodeMontgomery });

    [TestMethod]
    public void TheLineIsTheSumOfItsPackagesAndTheGapBetweenThem()
    {
        // 6686,4 + 708,9 + 5083,2 = 12 478,5 m. Każdy składnik zmierzony osobno.
        var route = L1();
        Assert.AreEqual(12478.5, route.LengthM, 1e-6);
        Assert.AreEqual(11769.6, route.AxisLengthM, 1e-6);
        Assert.AreEqual(708.9, route.GapLengthM, 1e-6);
        Assert.AreEqual(route.AxisLengthM + route.GapLengthM, route.LengthM, 1e-9);
    }

    [TestMethod]
    public void TheGapIsLongerThanTheStraightLineBetweenItsEnds()
    {
        // `reports/network-chainage.md` podaje dla tej pary 703,0 m, ale to CIĘCIWA,
        // czyli odległość w linii prostej i dolne ograniczenie. Tor skręca, więc jest
        // dłuższy. Gdyby ktoś podstawił cięciwę, linia byłaby o 5,9 m za krótka —
        // i wyglądałoby to zupełnie normalnie.
        Assert.IsTrue(MerodeMontgomery.LengthM > 703.0,
            $"{MerodeMontgomery.LengthM} m nie jest dłuższe od cięciwy 703,0 m");
    }

    [TestMethod]
    public void TheGapRunTimeSitsBetweenItsNeighboursWhenScaledByDistance()
    {
        // Druga niezależna droga do tej samej liczby. Zmierzone sąsiedztwo z GTFS:
        //   SCHUMAN     -> MERODE             1219,0 m / 90 s = 48,8 km/h
        //   MONTGOMERY  -> JOSEPH.-CHARLOTTE   535,0 m / 54 s = 35,7 km/h
        // Odcinek Merode → Montgomery ma leżeć między nimi, bo jest między nimi
        // długością. Gdyby czas jazdy albo długość były zmyślone, prędkość wypadłaby
        // poza ten przedział.
        var speedKmh = MerodeMontgomery.LengthM / MerodeMontgomery.MedianRunSeconds * 3.6;
        Assert.IsTrue(speedKmh > 35.7 && speedKmh < 48.8,
            $"{speedKmh:F1} km/h wypada poza zmierzone sąsiedztwo 35,7 … 48,8 km/h");
    }

    [TestMethod]
    public void StationsAreRenumberedIntoRouteChainageNotPackageChainage()
    {
        var route = L1();
        var names = route.Stations.Select(s => s.Name).ToArray();
        CollectionAssert.AreEqual(
            new[] { "Gare de l'Ouest", "Merode", "Montgomery", "Stockel" }, names);

        // Montgomery jest na 0,0 m WŁASNEGO pakietu, ale na 7395,3 m trasy.
        var montgomery = route.Stations.Single(s => s.Name == "Montgomery");
        Assert.AreEqual(6686.4 + 708.9, montgomery.ChainageM, 1e-6);
        Assert.AreEqual("L1_B", montgomery.AxisId);
    }

    [TestMethod]
    public void StationChainagesNeverGoBackwards()
    {
        var route = L1();
        for (var i = 1; i < route.Stations.Count; i++)
        {
            Assert.IsTrue(route.Stations[i].ChainageM > route.Stations[i - 1].ChainageM,
                $"{route.Stations[i].Name} cofa się względem {route.Stations[i - 1].Name}");
        }
    }

    [TestMethod]
    public void AChainageInsideTheGapIsRecognisedAsSuch()
    {
        var route = L1();
        Assert.IsFalse(route.IsInGap(3000.0), "środek pakietu A");
        Assert.IsTrue(route.IsInGap(6686.4 + 300.0), "środek przerwy");
        Assert.IsFalse(route.IsInGap(6686.4 + 708.9 + 100.0), "wnętrze pakietu B");
    }

    [TestMethod]
    public void TheRouteRefusesToInventGeometryInsideTheGap()
    {
        // TO JEST TEN TEST. Interpolacja między krańcami pakietów dałaby prostą tam,
        // gdzie tor skręca — i wyglądałaby dokładnie tak samo jak prawdziwa geometria.
        // Długość i czas jazdy tego odcinka są zmierzone; jego PRZEBIEG nie.
        var route = L1();
        var exception = Assert.ThrowsException<InvalidOperationException>(
            () => route.PointAt(6686.4 + 300.0));
        StringAssert.Contains(exception.Message, "Merode");
        StringAssert.Contains(exception.Message, "geometrii");
    }

    [TestMethod]
    public void GeometryStillWorksInsideThePackagesThemselves()
    {
        // Kontrola negatywna do testu wyżej: odmowa ma dotyczyć WYŁĄCZNIE przerwy.
        var route = L1();
        var inA = route.PointAt(3000.0);
        Assert.AreEqual(3000.0, inA.X, 1e-3);

        var inB = route.PointAt(6686.4 + 708.9 + 1000.0);
        Assert.AreEqual(1000.0, inB.X, 1e-3, "pakiet B ma własny kilometraż od zera");
    }

    [TestMethod]
    public void GluingTwoPackagesWithoutAGapIsRefused()
    {
        // Bez przerwy linia byłaby o 708,9 m za krótka, a wszystkie stacje pakietu B
        // wylądowałyby o tyle za blisko. Żaden pojedynczy pomiar by tego nie pokazał.
        var axes = new[] { Axis("L1_A", 6686.4, ("x", 0.0)), Axis("L1_B", 5083.2, ("y", 0.0)) };
        Assert.ThrowsException<ArgumentOutOfRangeException>(
            () => new LineRoute("L1", axes, Array.Empty<RouteGap>()));
    }

    [TestMethod]
    public void AGapWithoutALengthIsRefused()
    {
        var axes = new[] { Axis("L1_A", 6686.4, ("x", 0.0)), Axis("L1_B", 5083.2, ("y", 0.0)) };
        foreach (var bad in new[] { 0.0, -1.0, double.NaN })
        {
            Assert.ThrowsException<ArgumentOutOfRangeException>(
                () => new LineRoute("L1", axes, new[] { new RouteGap("a", "b", bad, 63.0) }),
                $"długość {bad} przeszła");
        }
    }

    [TestMethod]
    public void ASingleAxisRouteNeedsNoGaps()
    {
        var route = new LineRoute("L2", new[] { Axis("L2_E", 9020.8, ("Elisabeth", 0.0)) },
                                  Array.Empty<RouteGap>());
        Assert.AreEqual(9020.8, route.LengthM, 1e-6);
        Assert.AreEqual(0.0, route.GapLengthM, 1e-9);
    }
}
