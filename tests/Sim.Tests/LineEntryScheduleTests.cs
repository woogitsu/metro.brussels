using System;
using MetroBxl.Sim.Line;
using MetroBxl.Sim.Physics;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace MetroBxl.Sim.Tests;

[TestClass]
public sealed class LineEntryScheduleTests
{
    private static string EntryProjectionJson(string runs) =>
        "{\"axis_id\":\"L1_A\",\"date\":\"20260902\",\"source_gtfs_sha256\":\"verified\",\"runs\":[" + runs + "]}";

    private static string EntryRunJson(string trip, string block, string stop, long seconds) =>
        $"{{\"trip_id\":\"{trip}\",\"block_id\":\"{block}\",\"first_stop_id\":\"{stop}\",\"release_s\":{seconds}}}";

    [TestMethod]
    public void Plan_mapuje_Gare_de_l_Ouest_i_Beekkant_na_stacje_oraz_kroki()
    {
        var axis = SignallingPlanTests.PackageAAxis();
        var json = EntryProjectionJson(EntryRunJson("west", "block-a", "8733", 20145) + "," +
            EntryRunJson("beek", "block-b", "8742", 19698));

        var plan = LineEntrySchedule.FromJson(json, axis, FixedStep.Simulation);

        Assert.AreEqual("20260902", plan.Date, "Data służby musi być zachowana.");
        Assert.AreEqual(2, plan.Entries.Count, "Oba kursy muszą pozostać w planie.");
        Assert.AreEqual(new ScheduledLineEntry("beek", "block-b", 1, 19698L * 120),
            plan.Entries[0], "Beekkant jest stacją 1 i wcześniejszym wjazdem.");
        Assert.AreEqual(new ScheduledLineEntry("west", "block-a", 0, 20145L * 120),
            plan.Entries[1], "Gare de l'Ouest jest stacją 0.");
    }

    [TestMethod]
    public void Plan_zachowuje_godziny_po_polnocy_i_porządkuje_remisy_po_trip_id()
    {
        var axis = SignallingPlanTests.PackageAAxis();
        var json = EntryProjectionJson(EntryRunJson("z", "block-a", "8733", 90000) + "," +
            EntryRunJson("a", "block-a", "8742", 90000));

        var plan = LineEntrySchedule.FromJson(json, axis, FixedStep.Simulation);

        Assert.AreEqual("a", plan.Entries[0].TripId, "Remis czasu sortuje się po trip_id.");
        Assert.AreEqual(90000L * 120, plan.Entries[0].ReleaseStep,
            "Godzina 25:00 nie zawija się do początku doby.");
    }

    [TestMethod]
    public void Plan_odrzuca_nieznana_stacje_i_duplikat_kursu()
    {
        var axis = SignallingPlanTests.PackageAAxis();
        Assert.ThrowsException<ArgumentException>(() => LineEntrySchedule.FromJson(
            EntryProjectionJson(EntryRunJson("bad", "block-a", "unknown", 100)), axis, FixedStep.Simulation),
            "Nieznane stop_id nie może wyznaczyć wejścia.");
        Assert.ThrowsException<ArgumentException>(() => LineEntrySchedule.FromJson(
            EntryProjectionJson(EntryRunJson("same", "block-a", "8733", 100) + "," +
                EntryRunJson("same", "block-b", "8742", 200)), axis, FixedStep.Simulation),
            "Powtórzony trip_id czyni plan niejednoznacznym.");
    }
}
