using MetroBxl.Game.World;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace MetroBxl.Game.Tests;

[TestClass]
public sealed class StationWayfindingTests
{
    [TestMethod]
    public void MarkerUsesTheCompleteBilingualName()
    {
        const string fullName = "Comte de Flandre|Graaf van Vlaanderen";
        Assert.AreEqual("Comte de Flandre\nGraaf van Vlaanderen",
            StationView.NameMarkerText(fullName),
            "The sign must not use the abbreviated NameNl feed field");
        Assert.AreEqual("Beekkant", StationView.NameMarkerText("Beekkant"),
            "A single name stays on one line");
    }

    [TestMethod]
    public void TerminalMarkersStayInsideTheAxis()
    {
        const double lengthM = 6686.739;
        Assert.AreEqual(8.0, StationView.NameMarkerChainage(0.0, lengthM), 1e-9,
            "The first station gets an in-route marker");
        Assert.AreEqual(6671.739, StationView.NameMarkerChainage(lengthM, lengthM), 1e-9,
            "The last marker is visible before reaching the terminal stop");
        Assert.AreEqual(494.73, StationView.NameMarkerChainage(509.73, lengthM), 1e-9,
            "An interior marker appears before the stopping point");
        Assert.AreEqual(524.73, StationView.StopMarkerChainage(509.73, lengthM), 1e-9,
            "A second marker remains visible at the stopping point");
        Assert.AreEqual(15.0, StationView.StopMarkerChainage(0.0, lengthM), 1e-9,
            "The first station has two distinct in-route positions");
        Assert.AreEqual(6678.739, StationView.StopMarkerChainage(lengthM, lengthM), 1e-9,
            "The terminal's second marker stays inside the route");
        CollectionAssert.AreEqual(new[] { 494.73, 524.73 },
            StationView.NameMarkerPositions(509.73, lengthM),
            "An interior station has approach and stop markers");
        CollectionAssert.AreEqual(new[] { 6671.739 },
            StationView.NameMarkerPositions(lengthM, lengthM),
            "The terminal must not show overlapping duplicate markers");
        CollectionAssert.AreEqual(new[] { 8.0 },
            StationView.NameMarkerPositions(0.0, lengthM),
            "Clamped signs at the route start should not overlap");
    }
}
