using System;
using System.Collections.Generic;
using MetroBxl.Sim.Line;
using MetroBxl.Sim.Physics;
using MetroBxl.Sim.Train;
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
        Assert.AreEqual(new DateOnly(2026, 9, 2), plan.ServiceDay,
            "Dzień służby musi być poprawną datą kalendarzową.");
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
        Assert.AreEqual(new DateOnly(2026, 9, 2), plan.ServiceDay,
            "Kurs o 25:00 nadal należy do poprzedniego dnia służby.");
    }

    [TestMethod]
    public void Plan_odrzuca_nieistniejacy_dzien_sluzby()
    {
        var axis = SignallingPlanTests.PackageAAxis();
        var json = EntryProjectionJson(EntryRunJson("late", "block-a", "8733", 90000))
            .Replace("20260902", "20260230", StringComparison.Ordinal);

        Assert.ThrowsException<ArgumentException>(
            () => LineEntrySchedule.FromJson(json, axis, FixedStep.Simulation),
            "Nieistniejąca data nie może identyfikować służby.");
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

    [TestMethod]
    public void Dwa_rozkladowe_wejscia_na_prawdziwy_plan_nie_dziela_bloku_i_dojezdzaja()
    {
        // Dwa różne obiegi na prawdziwej osi i planie wymagającym ryglowania tras.
        // Godziny są syntetyczne: test sprawdza połączenie adaptera z sygnalizacją,
        // nie odtworzenie dwóch wybranych kursów STIB ani politykę dyspozytora.
        var axis = SignallingPlanTests.PackageAAxis();
        var schedule = LineEntrySchedule.FromJson(EntryProjectionJson(
            EntryRunJson("west", "block-west", "8733", 0) + "," +
            EntryRunJson("beek", "block-beek", "8742", 55)),
            axis, FixedStep.Simulation);
        var line = LineCore.M7(SignallingPlanTests.PackageAPlan(), axis,
            new RunConditions(VehicleModel.M7.MassKg(TrainLoad.Aw2), 0.0,
                VehicleModel.M7.Adhesion(RailCondition.Dry), TrackEnvironment.Tunnel),
            new LineRunSettings(Units.KmhToMps(70.0), 8.0, 1.0, 5.0));
        var gate = new LineEntryGate(line, schedule, schedule.ServiceDay);

        var next = 0;
        var bothOnLineChecks = 0;
        var sharedBlockChecks = 0;
        while (!line.Finished && line.Steps < 200_000L)
        {
            if (next < schedule.Entries.Count &&
                schedule.Entries[next].ReleaseStep == line.Steps)
            {
                gate.QueueDue(schedule.Entries[next]);
                next++;
            }
            gate.Step();
            if (line.Trains.Count < 2 || !line.Trains[0].OnLine || !line.Trains[1].OnLine)
                continue;

            bothOnLineChecks++;
            var firstBlocks = new HashSet<string>(line.Signalling.BlocksOccupiedBy("west"),
                StringComparer.Ordinal);
            foreach (var block in line.Signalling.BlocksOccupiedBy("beek"))
                if (firstBlocks.Contains(block)) sharedBlockChecks++;
        }

        Assert.AreEqual(2, next, "oba rozkładowe wjazdy muszą zostać zgłoszone");
        Assert.AreEqual(2, line.Trains.Count, "każdy trip_id tworzy jeden skład");
        Assert.IsTrue(line.Finished, $"oba składy nie dojechały w budżecie: krok {line.Steps}");
        Assert.IsTrue(bothOnLineChecks > 0, "składy nigdy nie były jednocześnie na osi");
        Assert.AreEqual(0, sharedBlockChecks, "dwa składy zajęły ten sam blok");
        Assert.AreEqual(0L, line.Trains[0].EnteredAtStep, "Gare de l'Ouest wjeżdża w kroku zero");
        Assert.IsTrue(line.Trains[1].EnteredAtStep > schedule.Entries[1].ReleaseStep,
            "Zajęty blok Beekkant musi opóźnić fizyczny wjazd po zgłoszeniu rozkładowym");
        Assert.AreEqual(0, line.Trains[0].EntryStationIndex);
        Assert.AreEqual(1, line.Trains[1].EntryStationIndex);
        var westDrive = line.Trains[0].Drive!;
        var beekDrive = line.Trains[1].Drive!;
        Assert.AreEqual(11, westDrive.Calls.Count);
        Assert.AreEqual(10, beekDrive.Calls.Count);
        Assert.AreEqual("Merode", westDrive.Calls[^1].Name);
        Assert.AreEqual("Merode", beekDrive.Calls[^1].Name);
        Assert.IsTrue(line.Trains[0].LeftPlan, "pierwszy skład musi zwolnić Merode dla drugiego");
    }
}
