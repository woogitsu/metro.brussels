using System;
using System.Collections.Generic;
using System.Linq;
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

        Assert.AreEqual("step-budget", dispatcher.Run(releaseStep - 1),
            "budzet N-1 powinien zatrzymac zegar przed pierwszym kursem");
        Assert.AreEqual(releaseStep - 1, line.Steps,
            "zegar musi zatrzymac sie na granicy budzetu N-1");
        Assert.AreEqual(0, dispatcher.RegisteredEntries,
            "kurs nie moze byc zgloszony w kroku N-1");
        Assert.AreEqual(0, line.Trains.Count,
            "przed releaseStep linia nie moze miec zaplanowanego skladu");

        Assert.AreEqual("step-budget", dispatcher.Run(releaseStep),
            "budzet N powinien zatrzymac sie przed wykonaniem kroku N");
        Assert.AreEqual(releaseStep, line.Steps,
            "zegar powinien dojsc dokladnie do releaseStep");
        Assert.AreEqual(0, dispatcher.RegisteredEntries,
            "budzet konczacy sie na releaseStep nie wykonuje jeszcze tego kroku");
        Assert.AreEqual(0, line.Trains.Count,
            "budzet N nie moze utworzyc skladu przed wykonaniem kroku N");

        dispatcher.Step();
        Assert.AreEqual(releaseStep + 1, line.Steps,
            "wykonanie kroku N powinno przesunac zegar do N+1");
        Assert.AreEqual(1, dispatcher.RegisteredEntries,
            "kurs ma zostac zgloszony podczas wykonania kroku N");
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

    [TestMethod]
    public void Sesja_linii_czeka_na_pierwszy_wjazd_i_uzywa_tego_samego_zegara()
    {
        var axis = SignallingPlanTests.PackageAAxis();
        // Syntetyczne identyfikatory; tylko stop_id i geometria pochodzą z L1_A.
        var schedule = Schedule(axis, Entry("synthetic-west", "synthetic-a", "8733", 2) + "," +
            Entry("synthetic-beek", "synthetic-b", "8742", 55));
        var line = Line(axis);
        var dispatcher = new LineEntryDispatcher(line, schedule, schedule.ServiceDay);
        var session = new LineSession(line, new DriverNotch(0.5), FixedStep.Simulation, dispatcher);
        Assert.ThrowsException<InvalidOperationException>(() => session.ObserveNext(),
            "przed pierwszym wjazdem nie wolno przełączać nieistniejącego składu");
        var firstStep = schedule.Entries[0].ReleaseStep;
        while (line.Steps < firstStep)
        {
            Assert.IsTrue(session.Step(DriverKeys.None), "zegar sesji musi czekać na pierwszy wjazd");
            Assert.AreEqual(0, line.Trains.Count, "przed terminem nie wolno dodać składu");
            Assert.IsFalse(session.Finished, "przyszły kurs utrzymuje sesję aktywną");
        }
        Assert.IsTrue(session.Step(DriverKeys.None), "pierwszy kurs ma wejść o czasie");
        Assert.AreEqual(1, line.Trains.Count, "tylko pierwszy kurs jest już należny");
        Assert.AreEqual(firstStep, line.Trains[0].EnteredAtStep, "fizyczny wjazd jest punktualny");
        while (line.Steps <= schedule.Entries[1].ReleaseStep)
            Assert.IsTrue(session.Step(DriverKeys.None), "sesja musi dotrwać do drugiego terminu");
        Assert.AreEqual(2, line.Trains.Count, "oba kursy są w planie linii");
        Assert.AreEqual(2, dispatcher.RegisteredEntries, "dyspozytor zgłosił oba kursy");
    }

    [TestMethod]
    public void Pierwszy_krok_wjazdu_raportuje_rzeczywiste_polecenie_i_przyspieszenie()
    {
        var axis = SignallingPlanTests.PackageAAxis();
        var schedule = Schedule(axis, Entry("west", "block-west", "8733", 0));
        var line = Line(axis);
        var session = new LineSession(line, new DriverNotch(0.5), FixedStep.Simulation,
            new LineEntryDispatcher(line, schedule, schedule.ServiceDay));

        Assert.IsTrue(session.Step(DriverKeys.None), "sesja ma wykonać krok rozkładowego wjazdu");
        var drive = line.Trains[0].Drive;
        Assert.IsNotNull(drive, "wolny peron musi wpuścić skład w tym samym kroku");
        Assert.AreNotEqual(DriverCommand.Coast, drive.LastCommand,
            "test wymaga niezerowego polecenia już w kroku wjazdu");
        Assert.AreEqual(drive.LastCommand, session.Command,
            "telemetria musi użyć polecenia z wykonanego kroku");
        Assert.AreEqual(drive.State.SpeedMps / FixedStep.Simulation.Seconds,
            session.AccelerationMps2, 1e-9,
            "przyspieszenie pierwszego kroku musi wynikać z rzeczywistej zmiany prędkości");
    }

    [TestMethod]
    public void Kamera_przechodzi_na_drugi_sklad_gdy_pierwszy_zjezdza_z_planu()
    {
        var axis = SignallingPlanTests.PackageAAxis();
        var schedule = Schedule(axis, Entry("west", "block-west", "8733", 0) + "," +
            Entry("beek", "block-beek", "8742", 55));
        var line = Line(axis);
        var session = new LineSession(line, new DriverNotch(0.5), FixedStep.Simulation,
            new LineEntryDispatcher(line, schedule, schedule.ServiceDay));
        while (!line.Trains.Any(t => t.LeftPlan) && line.Steps < 200_000L)
            Assert.IsTrue(session.Step(DriverKeys.None), "sesja musi dojść do zjazdu pierwszego składu");

        Assert.IsTrue(line.Trains[0].LeftPlan, "pierwszy skład musi zjechać z planu");
        Assert.IsTrue(line.Trains[1].OnLine, "drugi skład musi być jeszcze na planie");
        Assert.AreEqual(1, session.ActiveObservedIndex, "obserwacja ma przejść na czynny skład");
        Assert.AreEqual("beek", session.Observed.Id, "obserwowany musi być drugi skład");
        Assert.IsNotNull(session.TelemetryRow(), "telemetria ma śledzić drugi skład");
        Assert.IsNull(session.NextActiveTrainId(), "samotnego czynnego składu nie można przełączyć na zjechany");
        Assert.AreEqual(0.0, session.AccelerationMps2, 0.0,
            "przy zmianie składu nie wolno odejmować jego prędkości od prędkości pierwszego");
    }

    [TestMethod]
    public void Kamera_i_telemetria_czekaja_na_przyszly_kurs_po_zjezdzie_pierwszego()
    {
        var axis = SignallingPlanTests.PackageAAxis();
        var schedule = Schedule(axis, Entry("west", "block-west", "8733", 0) + "," +
            Entry("beek", "block-beek", "8742", 2000));
        var line = Line(axis);
        var session = new LineSession(line, new DriverNotch(0.5), FixedStep.Simulation,
            new LineEntryDispatcher(line, schedule, schedule.ServiceDay));
        while (!line.Trains.Any(t => t.LeftPlan) && line.Steps < 200_000L)
            Assert.IsTrue(session.Step(DriverKeys.None), "sesja musi dojść do zjazdu przed późniejszym kursem");

        Assert.IsTrue(line.Trains[0].LeftPlan, "pierwszy skład musi opuścić plan");
        Assert.IsNull(session.ActiveObservedIndex, "widok nie może śledzić zjechanego składu");
        Assert.IsNull(session.TelemetryRow(), "zjechany skład nie może emitować dalszej telemetrii");
        Assert.AreEqual(DriverCommand.Coast, session.Command, "bez składu komenda ma być neutralna");
        Assert.AreEqual(0.0, session.AccelerationMps2, 0.0, "bez składu przyspieszenie ma być zerowe");
        Assert.IsNull(session.NextActiveTrainId(), "bez składu nie ma kolejnego celu obserwacji");
        while (line.Trains.Count < 2 && line.Steps < schedule.Entries[1].ReleaseStep + 1)
            Assert.IsTrue(session.Step(DriverKeys.None), "zegar musi doczekać drugiego kursu");
        Assert.AreEqual(1, session.ActiveObservedIndex, "kamera ma przejąć nowy skład po wjeździe");
        Assert.AreEqual("beek", session.Observed.Id, "kamera ma śledzić późniejszy kurs");
        Assert.IsNotNull(session.TelemetryRow(), "telemetria ma wrócić wraz z nowym składem");
    }
}
