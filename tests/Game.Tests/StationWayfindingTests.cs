using System;
using Godot;
using MetroBxl.Game.UI;
using MetroBxl.Game.World;
using MetroBxl.Sim.Line;
using MetroBxl.Sim.Physics;
using MetroBxl.Sim.Train;
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
        Assert.AreEqual(501.73, StationView.NameMarkerChainage(509.73, lengthM), 1e-9,
            "An interior marker is readable near the stopping point");
        Assert.AreEqual(521.73, StationView.StopMarkerChainage(509.73, lengthM), 1e-9,
            "A second marker is readable from the stopping point");
        Assert.AreEqual(12.0, StationView.StopMarkerChainage(0.0, lengthM), 1e-9,
            "The first station marker stays inside the route");
        Assert.AreEqual(6678.739, StationView.StopMarkerChainage(lengthM, lengthM), 1e-9,
            "The terminal's second marker stays inside the route");
        CollectionAssert.AreEqual(new[] { 479.73, 501.73, 521.73 },
            StationView.NameMarkerPositions(509.73, lengthM),
            "An interior station is named on entry, near the stop, and at the stop");
        CollectionAssert.AreEqual(new[] { 6671.739 },
            StationView.NameMarkerPositions(lengthM, lengthM),
            "The terminal must not show overlapping duplicate markers");
        CollectionAssert.AreEqual(new[] { 8.0 },
            StationView.NameMarkerPositions(0.0, lengthM),
            "Clamped signs at the route start should not overlap");
    }

    [TestMethod]
    public void NameBoardHangersReachTheStationCeiling()
    {
        Assert.AreEqual(0.14f, StationView.NameMarkerHangerLength(4.20f, 0.72f), 0.001f,
            "A suspended board must connect to the playable ceiling");
        Assert.AreEqual(0.25f, StationView.NameMarkerHangerLength(4.15f, 0.60f), 0.001f,
            "Hanger length follows the board's top edge");
        foreach (var bilingual in new[] { false, true })
        {
            var (centre, height) = StationView.NameMarkerVerticalLayout(bilingual);
            Assert.IsTrue(centre - height / 2 >= 3.60f + 0.30f + 0.019f,
                "Both board layouts must clear the M7 roof, its 0.30 m gauge reserve, and a 0.02 m buffer");
            Assert.IsTrue(centre + height / 2 <= 4.70f,
                "The board must stay below the playable tunnel ceiling");
            Assert.IsTrue(StationView.NameMarkerHangerLength(centre, height) > 0,
                "Each board must have room for a hanger beneath the ceiling");
        }
    }

    [TestMethod]
    public void TrainingStopTargetUsesExactInteriorStationCoordinateAndClearsTheTrain()
    {
        var axisLengthM = 6686.35;
        Assert.IsFalse(StationView.HasOverheadStopTarget(0.0, axisLengthM),
            "A board must not hang through the beginning of the tunnel");
        Assert.IsFalse(StationView.HasOverheadStopTarget(axisLengthM, axisLengthM),
            "A board must not hang through the terminal end wall");
        Assert.IsTrue(StationView.HasOverheadStopTarget(4075.66, axisLengthM),
            "Parc's axis stop coordinate has room for an overhead training cue");
        Assert.IsFalse(StationView.HasOverheadStopTarget(double.NaN, axisLengthM),
            "An invalid coordinate must never create geometry");

        var (centreM, plateHeightM) = StationView.StopTargetVerticalLayout();
        Assert.IsTrue(centreM - plateHeightM / 2 >= 3.60f + 0.30f + 0.019f,
            "The board must clear the M7 roof, reserve, and buffer");
        Assert.IsTrue(centreM + plateHeightM / 2 <= 4.70f,
            "The board must stay under the current station tunnel roof");
        Assert.IsTrue(StationView.NameMarkerHangerLength(centreM, plateHeightM) > 0,
            "The board must have room for a ceiling hanger");
    }

    [TestMethod]
    public void TrainingStopTargetIsCentredOverTheActiveTrackAtTheExactChainage()
    {
        var axis = TrackAxis.FromJson("""
            {"id":"STOP_TEST","points":[[0,0,0],[100,0,0],[200,50,0]],"stations":[]}
            """);
        var scene = new SceneAxis(axis, 2.10);
        var frame = scene.Chord(99.5, 100.5);
        var centre = StationView.StopTargetCentre(scene, 100.0);
        var fromRoute = centre - scene.CentreLinePoint(100.0);

        Assert.AreEqual(0.0f, fromRoute.Dot(frame.Forward), 0.001f,
            "The board must stay at the exact stop chainage");
        Assert.AreEqual(2.10f, fromRoute.Dot(frame.Right), 0.001f,
            "The board must be above the active track, not the route centre line");
        Assert.AreEqual(StationView.StopTargetVerticalLayout().CentreHeight,
            fromRoute.Dot(Vector3.Up), 0.001f,
            "The board must keep its measured roof clearance above the active track");
    }

    [TestMethod]
    public void TargetOutcomeFollowsValidStopDepartureMissAndReset()
    {
        var service = new StationService(new[]
        {
            new AxisStation("Start", 0.0, "s0"),
            new AxisStation("First", 500.0, "s1"),
            new AxisStation("Second", 1200.0, "s2"),
        }, new DoorCycle(0.0), FixedStep.Simulation, 5.0);

        Assert.AreEqual(StopTargetOutcome.Approach, StationView.StopTargetOutcomeFor(service, "s1"),
            "An untouched target starts amber");
        Assert.AreEqual(string.Empty, ManualStopOutcomeCue.For(service),
            "An untouched run has no stale cab outcome");
        service.Filter(new DriveState(0, 1.0, 500.0, 0.0), DriverCommand.Coast, 500.0);
        Assert.AreEqual(StopTargetOutcome.Approach, StationView.StopTargetOutcomeFor(service, "s1"),
            "Passing the target while moving cannot confirm arrival");

        service.Filter(new DriveState(1, 0.0, 500.0, 0.0), DriverCommand.Coast, 500.0);
        Assert.AreEqual(StopTargetOutcome.Confirmed, StationView.StopTargetOutcomeFor(service, "s1"),
            "Only StationService's valid call confirms arrival");
        StringAssert.Contains(ManualStopOutcomeCue.For(service), "POTWIERDZONY",
            "The driver must see confirmation while the overhead board is out of view");
        var lastStep = (long)Math.Ceiling(service.Cycle.DwellSeconds / FixedStep.Simulation.Seconds) + 5;
        for (var step = 2L; step <= lastStep; step++)
            service.Filter(new DriveState(step, 0.0, 500.0, 0.0), DriverCommand.Coast, 500.0);
        Assert.IsTrue(double.IsFinite(service.Calls[0].DepartureSeconds),
            "The domain call must actually record a completed departure");
        Assert.AreEqual(StopTargetOutcome.Served, StationView.StopTargetOutcomeFor(service, "s1"),
            "A completed door cycle changes the target to served");
        StringAssert.Contains(ManualStopOutcomeCue.For(service), "OBSŁUŻONY",
            "The cab must show the completed service outcome");

        service.Filter(new DriveState(lastStep + 1, 1.0, 1206.0, 0.0),
            DriverCommand.Coast, 1206.0);
        Assert.AreEqual(StopTargetOutcome.Missed, StationView.StopTargetOutcomeFor(service, "s2"),
            "Crossing beyond the stop window without a call marks the target missed");
        StringAssert.Contains(ManualStopOutcomeCue.For(service), "MINIĘTY",
            "The newest missed target must replace the older served cue");
        service.Reset();
        Assert.AreEqual(StopTargetOutcome.Approach, StationView.StopTargetOutcomeFor(service, "s1"),
            "Reset clears the served outcome");
        Assert.AreEqual(StopTargetOutcome.Approach, StationView.StopTargetOutcomeFor(service, "s2"),
            "Reset clears the missed outcome");
        Assert.AreEqual(string.Empty, ManualStopOutcomeCue.For(service),
            "Reset clears the in-cab outcome as well as the world board");
    }
}
