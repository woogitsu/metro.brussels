using System;
using System.Collections.Generic;
using MetroBxl.Sim.Line;
using MetroBxl.Sim.Physics;
using MetroBxl.Sim.Train;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace MetroBxl.Sim.Tests;

[TestClass]
public sealed class LineEntryDispatcherTests
{
    private static LineEntrySchedule Schedule(TrackAxis axis, string runs) =>
        LineEntrySchedule.FromJson(
            "{\"axis_id\":\"L1_A\",\"date\":\"20260902\",\"source_gtfs_sha256\":\"verified\",\"runs\":[" + runs + "]}",
            axis, FixedStep.Simulation);

    private static string Entry(string trip, string block, string stop, long seconds) =>
        $"{{\"trip_id\":\"{trip}\",\"block_id\":\"{block}\",\"first_stop_id\":\"{stop}\",\"release_s\":{seconds}}}";

    private static LineCore Line(TrackAxis axis) =>
        LineCore.M7(SignallingPlanTests.PackageAPlan(), axis,
            new RunConditions(VehicleModel.M7.MassKg(TrainLoad.Aw2), 0.0,
                VehicleModel.M7.Adhesion(RailCondition.Dry), TrackEnvironment.Tunnel),
            new LineRunSettings(Units.KmhToMps(70.0), 8.0, 1.0, 5.0));

    [TestMethod]
    public void Dwa_wjazdy_na_L1_A_są_zgłaszane_o_czasie_i_przejeżdżają_bez_wspólnego_bloku()
    {
        var axis = SignallingPlanTests.PackageAAxis();
        var schedule = Schedule(axis, Entry("west", "block-west", "8733", 0) + "," +
            Entry("beek", "block-beek", "8742", 55));
        var line = Line(axis);
        var dispatcher = new LineEntryDispatcher(line, schedule, schedule.ServiceDay);
        var simultaneous = 0;
        while (!dispatcher.Finished && line.Steps < 200_000L)
        {
            dispatcher.Step();
            if (line.Trains.Count != 2 || !line.Trains[0].OnLine || !line.Trains[1].OnLine)
                continue;
            simultaneous++;
            var occupied = new HashSet<string>(line.Signalling.BlocksOccupiedBy("west"),
                StringComparer.Ordinal);
            foreach (var block in line.Signalling.BlocksOccupiedBy("beek"))
                Assert.IsFalse(occupied.Contains(block), "dwa kursy nie mogą zajmować tego samego bloku");
        }

        Assert.IsTrue(dispatcher.Finished, "oba kursy muszą dojechać w budżecie");
        Assert.AreEqual(2, dispatcher.RegisteredEntries, "oba kursy muszą być zgłoszone");
        Assert.IsTrue(simultaneous > 0, "kursy muszą współdzielić oś w czasie");
        Assert.AreEqual(0L, line.Trains[0].EnteredAtStep, "pierwszy kurs wjeżdża od razu");
        Assert.IsTrue(line.Trains[1].EnteredAtStep > schedule.Entries[1].ReleaseStep,
            "zajęty blok opóźnia fizyczny wjazd drugiego kursu");
        Assert.AreEqual(0, line.Trains[0].EntryStationIndex, "pierwszy kurs wjeżdża od Gare de l'Ouest");
        Assert.AreEqual(1, line.Trains[1].EntryStationIndex, "drugi kurs wjeżdża od Beekkant");
        Assert.AreEqual("Merode", line.Trains[0].Drive!.Calls[^1].Name,
            "pierwszy kurs musi dojechać do Merode");
        Assert.AreEqual("Merode", line.Trains[1].Drive!.Calls[^1].Name,
            "drugi kurs musi dojechać do Merode");
    }

    [TestMethod]
    public void Zegar_czeka_na_przyszły_kurs_nawet_po_ukończeniu_pierwszego()
    {
        var axis = SignallingPlanTests.PackageAAxis();
        var schedule = Schedule(axis, Entry("west", "block-west", "8733", 0) + "," +
            Entry("beek", "block-beek", "8742", 2000));
        var line = Line(axis);
        var dispatcher = new LineEntryDispatcher(line, schedule, schedule.ServiceDay);
        while (!line.Finished && line.Steps < schedule.Entries[1].ReleaseStep)
            dispatcher.Step();

        Assert.IsTrue(line.Finished, "pierwszy kurs powinien skończyć przed drugim terminem");
        Assert.IsFalse(dispatcher.Finished, "przyszły kurs trzyma zegar aktywny");
        Assert.AreEqual(1, dispatcher.RegisteredEntries, "drugi kurs nie może być zgłoszony przed terminem");
        Assert.AreEqual("arrived", dispatcher.Run(400_000L), "dyspozytor powinien doczekać drugiego kursu");
        Assert.AreEqual(2, dispatcher.RegisteredEntries, "drugi kurs musi zostać zgłoszony");
        Assert.IsTrue(line.Trains[1].EnteredAtStep >= schedule.Entries[1].ReleaseStep,
            "drugi kurs nie może fizycznie wjechać przed terminem");
    }

    [TestMethod]
    public void Kurs_jest_zglaszany_dokladnie_na_granicy_release_step_a_budzet_jej_nie_przekracza()
    {
        var axis = SignallingPlanTests.PackageAAxis();
        var schedule = Schedule(axis, Entry("west", "block-west", "8733", 1));
        var line = Line(axis);
        var dispatcher = new LineEntryDispatcher(line, schedule, schedule.ServiceDay);
        var releaseStep = schedule.Entries[0].ReleaseStep;

        Assert.AreEqual("step-budget", dispatcher.Run(releaseStep - 1));
        Assert.AreEqual(releaseStep - 1, line.Steps);
        Assert.AreEqual(0, dispatcher.RegisteredEntries);
        Assert.AreEqual(0, line.Trains.Count);

        Assert.AreEqual("step-budget", dispatcher.Run(releaseStep));
        Assert.AreEqual(releaseStep, line.Steps);
        Assert.AreEqual(0, dispatcher.RegisteredEntries,
            "budzet konczacy sie na releaseStep nie wykonuje jeszcze tego kroku");
        Assert.AreEqual(0, line.Trains.Count);

        dispatcher.Step();
        Assert.AreEqual(releaseStep + 1, line.Steps);
        Assert.AreEqual(1, dispatcher.RegisteredEntries);
        Assert.AreEqual(releaseStep, line.Trains[0].EnteredAtStep,
            "wolny peron wpuszcza sklad w kroku releaseStep, bez opoznienia o jeden krok");
    }

    [TestMethod]
    public void Powtórzony_block_id_jest_odmową_przed_pierwszym_krokiem()
    {
        var axis = SignallingPlanTests.PackageAAxis();
        var schedule = Schedule(axis, Entry("west", "vehicle-a", "8733", 0) + "," +
            Entry("beek", "vehicle-a", "8742", 2000));
        var line = Line(axis);

        var error = Assert.ThrowsException<InvalidOperationException>(
            () => new LineEntryDispatcher(line, schedule, schedule.ServiceDay),
            "ponowny kurs tego samego obiegu wymaga polityki transferu pojazdu");
        StringAssert.Contains(error.Message, "vehicle-a", "odmowa powinna wskazać obieg");
        Assert.AreEqual(0L, line.Steps, "odmowa nie może przesunąć zegara");
        Assert.AreEqual(0, line.Trains.Count, "odmowa nie może zarejestrować połowy planu");
    }

    [TestMethod]
    public void Dyspozytor_odmawia_linii_z_juz_uruchomionym_zegarem_lub_skladem()
    {
        var axis = SignallingPlanTests.PackageAAxis();
        var schedule = Schedule(axis, Entry("west", "block-west", "8733", 0));
        var stepped = Line(axis);
        stepped.Step();
        Assert.ThrowsException<ArgumentException>(
            () => new LineEntryDispatcher(stepped, schedule, schedule.ServiceDay),
            "dyspozytor nie może pominąć wjazdu przypadającego przed bieżącym krokiem");

        var occupied = Line(axis);
        occupied.Add("existing", 0);
        var emptySchedule = Schedule(axis, "");
        Assert.ThrowsException<ArgumentException>(
            () => new LineEntryDispatcher(occupied, emptySchedule, emptySchedule.ServiceDay),
            "pusty plan nie może ogłosić końca linii mającej już aktywny skład");
    }
}
