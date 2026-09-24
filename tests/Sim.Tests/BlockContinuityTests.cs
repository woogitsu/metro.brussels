using System;
using MetroBxl.Sim.Line;
using MetroBxl.Sim.Physics;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace MetroBxl.Sim.Tests;

[TestClass]
public sealed class BlockContinuityTests
{
    private static string RunWindow(string trip, string block, string first, string last,
        long release, long exit) =>
        $"{{\"trip_id\":\"{trip}\",\"block_id\":\"{block}\",\"first_stop_id\":\"{first}\",\"last_stop_id\":\"{last}\",\"release_s\":{release},\"exit_s\":{exit}}}";

    private static string ProjectionWindow(string runs) =>
        "{\"axis_id\":\"L1_A\",\"date\":\"20260902\",\"source_gtfs_sha256\":\"verified\",\"runs\":[" + runs + "]}";

    [TestMethod]
    public void Rozne_stacje_graniczne_pozostaja_jawnie_niewyjasnione()
    {
        var axis = SignallingPlanTests.PackageAAxis();
        var json = ProjectionWindow(RunWindow("a", "vehicle-duty", "8742", "8072", 100, 200) + "," +
            RunWindow("b", "vehicle-duty", "8733", "8072", 300, 400));

        var continuity = BlockContinuity.FromJson(json, axis, FixedStep.Simulation);

        Assert.AreEqual(1, continuity.Transitions.Count, "Dwa kursy jednego obiegu tworzą jedno przejście.");
        Assert.AreEqual("vehicle-duty", continuity.Transitions[0].BlockId,
            "Identyfikator obiegu pozostaje związany z pojazdem.");
        Assert.AreEqual(100L * 120, continuity.Transitions[0].GapSteps,
            "Odstęp wynika z wyjścia i następnego wejścia.");
        Assert.IsFalse(continuity.Transitions[0].SharesBoundaryStation,
            "Merode i Gare de l'Ouest nie tworzą udokumentowanego nawrotu.");
    }

    [TestMethod]
    public void Nakladajace_sie_kursy_tego_samego_obiegu_sa_odrzucone()
    {
        var axis = SignallingPlanTests.PackageAAxis();
        var json = ProjectionWindow(RunWindow("a", "same", "8733", "8072", 100, 300) + "," +
            RunWindow("b", "same", "8742", "8072", 200, 400));

        var error = Assert.ThrowsException<ArgumentException>(
            () => BlockContinuity.FromJson(json, axis, FixedStep.Simulation),
            "Jeden obieg nie może mieć dwóch nakładających się kursów.");
        StringAssert.Contains(error.Message, "same", "Odmowa wskazuje identyfikator obiegu.");
    }

    [TestMethod]
    public void Rozne_obiegi_moga_jechac_rownoczesnie()
    {
        var axis = SignallingPlanTests.PackageAAxis();
        var json = ProjectionWindow(RunWindow("a", "one", "8733", "8072", 100, 300) + "," +
            RunWindow("b", "two", "8742", "8072", 200, 400));

        var continuity = BlockContinuity.FromJson(json, axis, FixedStep.Simulation);

        Assert.AreEqual(0, continuity.Transitions.Count,
            "Równoczesne kursy różnych obiegów nie są konfliktem ciągłości pojazdu.");
    }
}
