using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using MetroBxl.Sim.Line;
using MetroBxl.Sim.Physics;
using MetroBxl.Sim.Train;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace MetroBxl.Sim.Tests;

/// <summary>
/// Skład krokowany z zewnątrz (T-320, pierwszy krok w stronę wielu składów).
///
/// <para>Testy pilnują dwóch rzeczy i tylko dwóch. Po pierwsze: <b>krokowanie z zewnątrz
/// daje dokładnie ten sam przejazd</b> co pętla zamknięta w <see cref="LineRun"/> —
/// bo gdyby dawało inny, cały refaktor byłby przepisaniem modelu pod pozorem
/// porządków. Po drugie: <b>krok to naprawdę jeden krok</b>, a nie „mniej więcej".</para>
///
/// <para>Czego tu NIE ma: sprzężenia między składami. Dwa składy na wspólnym zegarze
/// są dziś niezależne i ten fakt jest tu przypięty testem — żeby dzień, w którym
/// przestaną być niezależne, był widoczny jako zmiana zachowania, a nie przemknął
/// jako „przecież i tak działa".</para>
/// </summary>
[TestClass]
public sealed class LineDriveTests
{
    private static RunConditions Level() => RunConditions.Level(VehicleModel.M7, TrainLoad.Aw0);

    private static LineRunSettings Settings(
        double limitKmh = 60.0, double exchange = 10.0,
        double usage = 1.0, double window = 5.0) =>
        new(Units.KmhToMps(limitKmh), exchange, usage, window);

    private static TrackAxis Axis(params double[] stationChainages)
    {
        var length = stationChainages[^1] + 100.0;
        var stations = string.Join(",", stationChainages.Select((c, i) => string.Create(
            CultureInfo.InvariantCulture,
            $$"""{"name":"S{{i}}","chainage_m":{{c.ToString("R", CultureInfo.InvariantCulture)}},"stop_id":"P{{i}}"}""")));
        return TrackAxis.FromJson(string.Create(
            CultureInfo.InvariantCulture,
            $$"""
            {"id":"T","length_m":0.0,"vertical":{"status":"not_modelled"},
             "points":[[0.0,0.0,0.0],[{{length.ToString("R", CultureInfo.InvariantCulture)}},0.0,0.0]],
             "stations":[{{stations}}]}
            """), 0.0);
    }

    private static LineDrive Drive(TrackAxis axis, LineRunSettings settings) =>
        new(axis, Level(), settings,
            new TrainController(VehicleModel.M7),
            new BrakingPointSolver(VehicleModel.M7),
            FixedStep.Simulation);

    private static List<LineRun.TracePoint> RunToEnd(LineDrive drive)
    {
        var trace = new List<LineRun.TracePoint>();
        while (!drive.Finished && drive.Steps < LineRun.DefaultStepBudget)
        {
            drive.Step(trace.Add);
        }

        return trace;
    }

    // --- zgodność z pętlą zamkniętą ------------------------------------------

    [TestMethod]
    public void Krokowanie_z_zewnatrz_daje_ten_sam_slad_co_zamknieta_petla()
    {
        // To jest ten test. Ślad co krok, nie podsumowanie: podsumowanie zgodziłoby się
        // także wtedy, gdyby przejazd dojechał tam samo, ale inną drogą.
        var axis = Axis(0.0, 600.0, 1400.0, 2000.0);
        var settings = Settings();

        var closed = new List<LineRun.TracePoint>();
        LineRun.M7.Run(axis, Level(), settings, LineRun.DefaultStepBudget, closed.Add);
        var stepped = RunToEnd(Drive(axis, settings));

        Assert.AreEqual(closed.Count, stepped.Count, "różna liczba kroków");
        for (var i = 0; i < closed.Count; i++)
        {
            Assert.AreEqual(closed[i], stepped[i], $"rozjazd w kroku {i}");
        }
    }

    [TestMethod]
    public void Wynik_krokowany_zgadza_sie_z_wynikiem_petli_co_do_pola()
    {
        var axis = Axis(0.0, 700.0, 1500.0);
        var settings = Settings();

        var closed = LineRun.M7.Run(axis, Level(), settings);
        var drive = Drive(axis, settings);
        RunToEnd(drive);
        var stepped = drive.Result("arrived");

        Assert.AreEqual(closed.Steps, stepped.Steps);
        Assert.AreEqual(closed.TotalSeconds, stepped.TotalSeconds);
        Assert.AreEqual(closed.TotalDistanceM, stepped.TotalDistanceM);
        Assert.AreEqual(closed.DwellSeconds, stepped.DwellSeconds);
        CollectionAssert.AreEqual(
            closed.Calls.ToArray(), stepped.Calls.ToArray(), "zatrzymania się różnią");
    }

    [TestMethod]
    public void Szczyt_predkosci_jest_liczony_od_nowa_na_kazdym_odcinku()
    {
        // Kontrola, której brakowało. Na osi, gdzie KAŻDY odcinek dobija do limitu,
        // szczyt wychodzi ten sam niezależnie od tego, czy licznik jest resetowany —
        // i mutacja kasująca reset przechodzi przez wszystkie testy. Tutaj drugi
        // odcinek ma 200 m i do limitu nie dojeżdża, więc brak resetu przeniósłby
        // na niego szczyt z odcinka pierwszego i byłoby to widać.
        var axis = Axis(0.0, 1500.0, 1700.0);
        var drive = Drive(axis, Settings());
        RunToEnd(drive);
        var calls = drive.Result("arrived").Calls;

        Assert.AreEqual(2, calls.Count);
        Assert.IsTrue(calls[1].TopSpeedMps < calls[0].TopSpeedMps,
            $"odcinek 200 m pokazał szczyt {calls[1].TopSpeedMps:F3} m/s wobec " +
            $"{calls[0].TopSpeedMps:F3} m/s na odcinku 1500 m — licznik nie został wyzerowany");
    }

    // --- krok to jeden krok --------------------------------------------------

    [TestMethod]
    public void Jedno_wywolanie_posuwa_dokladnie_o_jeden_krok()
    {
        var drive = Drive(Axis(0.0, 800.0), Settings());
        Assert.AreEqual(0L, drive.Steps);

        for (var expected = 1L; expected <= 10L; expected++)
        {
            Assert.IsTrue(drive.Step());
            Assert.AreEqual(expected, drive.Steps, "krok posunął licznik o co innego niż 1");
        }
    }

    [TestMethod]
    public void Czas_jest_funkcja_liczby_krokow_a_nie_sumy()
    {
        // Kontrola do testu wyżej: gdyby czas był akumulowany dodawaniem, przy 1/120 s
        // narosłby błąd zaokrągleń i ta równość by nie zachodziła.
        var drive = Drive(Axis(0.0, 800.0), Settings());
        for (var i = 0; i < 1000; i++)
        {
            drive.Step();
        }

        Assert.AreEqual(1000L, drive.Steps);
        Assert.AreEqual(1000.0 / FixedStep.SimulationHertz, drive.State.TimeSeconds(FixedStep.Simulation), 0.0);
    }

    [TestMethod]
    public void Po_dojechaniu_krok_nie_robi_nic_i_mowi_o_tym()
    {
        var drive = Drive(Axis(0.0, 400.0), Settings());
        RunToEnd(drive);

        Assert.IsTrue(drive.Finished);
        var steps = drive.Steps;
        Assert.IsFalse(drive.Step(), "krok po dojechaniu powinien odmówić");
        Assert.AreEqual(steps, drive.Steps, "odmowa kroku i tak posunęła licznik");
    }

    // --- wspólny zegar -------------------------------------------------------

    [TestMethod]
    public void Dwa_sklady_na_wspolnym_zegarze_jada_tak_samo_jak_kazdy_osobno()
    {
        // Własność, dla której ta klasa powstała: wołający może posuwać N składów
        // naprzemiennie. Dziś składy są niezależne, więc wspólny zegar musi dać
        // dokładnie to samo co dwa osobne przejazdy. Gdy dojdzie sprzężenie (T-313),
        // ten test zacznie padać — i to będzie poprawny sygnał, nie regres.
        var axis = Axis(0.0, 600.0, 1400.0);
        var settings = Settings();

        var alone = RunToEnd(Drive(axis, settings));

        var a = Drive(axis, settings);
        var b = Drive(axis, settings);
        var traceA = new List<LineRun.TracePoint>();
        var traceB = new List<LineRun.TracePoint>();
        while ((!a.Finished || !b.Finished) && a.Steps < LineRun.DefaultStepBudget)
        {
            a.Step(traceA.Add);
            b.Step(traceB.Add);
        }

        Assert.AreEqual(alone.Count, traceA.Count);
        CollectionAssert.AreEqual(alone, traceA, "skład A na wspólnym zegarze jedzie inaczej");
        CollectionAssert.AreEqual(alone, traceB, "skład B na wspólnym zegarze jedzie inaczej");
    }

    [TestMethod]
    public void Sklad_ktory_dojechal_nie_zatrzymuje_zegara_pozostalym()
    {
        // Krótsza oś kończy wcześniej. Pętla wołającego ma to znieść bez wyjątku
        // i bez cofania licznika dłuższego składu.
        var shortDrive = Drive(Axis(0.0, 300.0), Settings());
        var longDrive = Drive(Axis(0.0, 300.0, 1200.0, 2400.0), Settings());

        while (!longDrive.Finished && longDrive.Steps < LineRun.DefaultStepBudget)
        {
            shortDrive.Step();
            longDrive.Step();
        }

        Assert.IsTrue(shortDrive.Finished);
        Assert.IsTrue(longDrive.Finished);
        Assert.IsTrue(longDrive.Steps > shortDrive.Steps,
            $"dłuższa oś dała {longDrive.Steps} kroków, krótsza {shortDrive.Steps}");
    }

    // --- odmowy --------------------------------------------------------------

    [TestMethod]
    public void Os_z_jedna_stacja_jest_odrzucana()
    {
        Assert.ThrowsException<ArgumentOutOfRangeException>(
            () => Drive(Axis(0.0), Settings()));
    }

    [TestMethod]
    public void Brakujace_skladniki_sa_odrzucane()
    {
        var axis = Axis(0.0, 500.0);
        var settings = Settings();
        var controller = new TrainController(VehicleModel.M7);
        var solver = new BrakingPointSolver(VehicleModel.M7);

        Assert.ThrowsException<ArgumentNullException>(
            () => new LineDrive(null!, Level(), settings, controller, solver, FixedStep.Simulation));
        Assert.ThrowsException<ArgumentNullException>(
            () => new LineDrive(axis, null!, settings, controller, solver, FixedStep.Simulation));
        Assert.ThrowsException<ArgumentNullException>(
            () => new LineDrive(axis, Level(), null!, controller, solver, FixedStep.Simulation));
        Assert.ThrowsException<ArgumentNullException>(
            () => new LineDrive(axis, Level(), settings, null!, solver, FixedStep.Simulation));
        Assert.ThrowsException<ArgumentNullException>(
            () => new LineDrive(axis, Level(), settings, controller, null!, FixedStep.Simulation));
    }

    // --- stan widoczny z zewnątrz -------------------------------------------

    [TestMethod]
    public void Chainage_i_postoj_sa_widoczne_w_trakcie_jazdy()
    {
        // Wołający musi widzieć, GDZIE stoi skład i czy stoi na stacji — bez tego
        // nie da się później zapytać, czy blok przed nim jest wolny.
        var drive = Drive(Axis(0.0, 500.0, 1200.0), Settings());
        Assert.AreEqual(0.0, drive.ChainageM, 1e-9);
        Assert.IsFalse(drive.AtStation);

        var sawStation = false;
        var maxChainage = 0.0;
        while (!drive.Finished && drive.Steps < LineRun.DefaultStepBudget)
        {
            drive.Step();
            sawStation |= drive.AtStation;
            maxChainage = Math.Max(maxChainage, drive.ChainageM);
        }

        Assert.IsTrue(sawStation, "przejazd z dwoma zatrzymaniami nigdy nie pokazał postoju");
        Assert.IsTrue(maxChainage > 1190.0, $"czoło doszło tylko do {maxChainage:F1} m");
    }
}
