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

    [TestMethod]
    public void Reczna_trakcja_na_Merode_nie_wyjezdza_poza_koniec_osi()
    {
        // Ostatni peron jest o 0,25 m za końcem geometrii, jak na pakiecie A.
        var axis = TrackAxis.FromJson(
            """
            {"id":"END","length_m":0.0,"vertical":{"status":"not_modelled"},
             "points":[[0,0,0],[100,0,0]],
             "stations":[{"name":"Start","chainage_m":0,"stop_id":"P0"},
                         {"name":"Merode","chainage_m":100.25,"stop_id":"P1"}]}
            """, 0.0);
        var drive = Drive(axis, Settings(limitKmh: 30.0));
        drive.DoorControl = DoorControl.Manual;
        drive.DriverInput = DriverCommand.FullPower;
        var trace = new List<LineRun.TracePoint>();

        while (drive.ChainageM < axis.LengthM && drive.Steps < 20_000)
        {
            drive.Step(trace.Add);
            Assert.IsTrue(drive.ChainageM <= axis.LengthM,
                "nawet krok przekraczający koniec nie może ruszyć składu poza oś");
        }

        Assert.AreEqual(axis.LengthM, drive.ChainageM, 1e-9);
        Assert.AreEqual(0.0, drive.State.SpeedMps);
        Assert.AreEqual(0.0, trace[^1].SpeedMps,
            "ślad kroku granicznego musi pokazywać zatrzymanie, nie prędkość surową");
        Assert.AreEqual(0.0, trace[^1].Command.Throttle,
            "HUD ma pokazywać odcięty ciąg, choć nastawnik nadal jest na W");
        for (var i = 0; i < 100; i++)
        {
            drive.Step(trace.Add);
            Assert.AreEqual(axis.LengthM, drive.ChainageM, 1e-9);
            Assert.AreEqual(0.0, drive.State.SpeedMps);
            Assert.AreEqual(0.0, trace[^1].Command.Throttle);
        }

        Assert.IsTrue(drive.AtStation, "postój Merode musi powstać po zatrzymaniu");
        Assert.AreEqual("Merode", drive.Calls[^1].Name);
        Assert.AreEqual(-0.25, drive.Calls[^1].StopErrorM, 1e-9);
        Assert.IsFalse(drive.Finished, "ręczny postój czeka na obsługę drzwi");
        Assert.AreEqual(axis.LengthM, trace[^1].ChainageM, 1e-9);
        Assert.IsTrue(drive.Result("manual-stop").Energy.RelativeResidual < 1e-8,
            "bilans energii musi używać drogi i prędkości po ograniczeniu osi");
    }

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
        // naprzemiennie. GOŁE `LineDrive` są niezależne — o innych składach nie wie ani
        // jedno — więc wspólny zegar musi dać dokładnie to samo co dwa osobne przejazdy.
        //
        // Poprzednia wersja tego komentarza zapowiadała, że test zacznie padać, gdy dojdzie
        // sprzężenie z T-313. Zapowiedź była błędna i dlatego jest tu przepisana, a nie
        // dopisana obok: sprzężenie mieszka w `LineCore`, które trzyma sygnalizację i podaje
        // składom `AuthorityEndM`. Tutaj nikt tego nie ustawia, więc granica przebiega
        // dokładnie w tym miejscu i ten test ją trzyma: bez sygnalizacji składy pozostają
        // niezależne. Sprzężenie jest w `LineCoreTests`.
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

    // --- autorytet jazdy -----------------------------------------------------

    [TestMethod]
    public void Autorytet_dalej_niz_stacja_nie_zmienia_ani_jednego_kroku()
    {
        // Tożsamość, bez której wprowadzenie sygnalizacji byłoby cichą zmianą każdego
        // dotychczasowego przejazdu. Autorytet poza końcem osi to „droga wolna" — ślad
        // musi wyjść ten sam co bez autorytetu, co do bajtu.
        var axis = Axis(0.0, 600.0, 1400.0, 2000.0);
        var settings = Settings();

        var without = RunToEnd(Drive(axis, settings));

        var drive = Drive(axis, settings);
        drive.AuthorityEndM = 1e9;
        var with = RunToEnd(drive);

        Assert.AreEqual(without.Count, with.Count, "różna liczba kroków");
        CollectionAssert.AreEqual(without, with, "autorytet poza osią zmienił przejazd");
    }

    [TestMethod]
    public void Autorytet_blizej_niz_stacja_zatrzymuje_sklad_przed_nim()
    {
        // Stacja jest 800 m dalej, autorytet kończy się na 300 m. Skład ma stanąć przed
        // 300 m i tam ZOSTAĆ: nie dojechać do stacji, nie przekroczyć granicy i nie
        // pełznąć do niej centymetrami.
        const double Limit = 300.0;
        var drive = Drive(Axis(0.0, 800.0), Settings());
        drive.AuthorityEndM = Limit;

        var maxChainage = 0.0;
        for (var i = 0; i < 12000; i++)
        {
            drive.Step();
            maxChainage = Math.Max(maxChainage, drive.ChainageM);
        }

        Assert.IsFalse(drive.Finished, "skład dojechał do stacji mimo autorytetu przed nią");
        Assert.IsTrue(maxChainage <= Limit,
            $"czoło doszło do {maxChainage:F6} m, czyli za koniec autorytetu {Limit:F2} m");
        Assert.AreEqual(0.0, drive.State.SpeedMps, 0.0,
            $"skład przed końcem autorytetu jedzie {drive.State.SpeedMps:E3} m/s zamiast stać");
        Assert.IsTrue(drive.ChainageM > Limit - 5.0,
            $"skład stanął {Limit - drive.ChainageM:F2} m przed autorytetem — to jest " +
            "hamowanie do zupełnie innego celu, a nie do tej granicy");
    }

    [TestMethod]
    public void Postoj_przed_autorytetem_jest_naprawde_postojem_a_nie_pelzaniem()
    {
        // Kontrola do testu wyżej i jedyny powód, dla którego `Step` pyta o zatrzask
        // przed wywołaniem `Command`. Bez tego warunku skład po zatrzymaniu rusza co krok
        // pełną trakcją, robi 9 mm/s, hamuje do zera i powtarza — zmierzone 0,30 m w 58 s.
        // Tu jest zmierzone inaczej: po zatrzymaniu czoło nie drgnie ani o mikrometr
        // przez pełną minutę, a prędkość jest zerem dokładnym, nie „prawie".
        var drive = Drive(Axis(0.0, 800.0), Settings());
        drive.AuthorityEndM = 300.0;

        var settled = 0;
        while (drive.ChainageM < 100.0 || drive.State.SpeedMps > 0.0)
        {
            drive.Step();
            settled++;
            Assert.IsTrue(settled < 12000, "skład nie zatrzymał się przed autorytetem");
        }

        var stoppedAt = drive.ChainageM;
        for (var i = 0; i < 60 * FixedStep.SimulationHertz; i++)
        {
            drive.Step();
            Assert.AreEqual(stoppedAt, drive.ChainageM, 0.0,
                $"po {i + 1} krokach postoju czoło przesunęło się z {stoppedAt:F9} m " +
                $"na {drive.ChainageM:F9} m — to jest pełzanie do sygnału");
        }
    }

    [TestMethod]
    public void Otwarty_autorytet_puszcza_sklad_dalej_zamiast_zostawic_go_na_wybiegu()
    {
        // Druga kontrola: zatrzask hamowania musi zostać ZWOLNIONY, gdy cel odskoczy.
        // Zatrzask bez zwolnienia trzymałby się po otwarciu autorytetu — `Command` przy
        // zatrzasku nigdy nie wraca do trakcji — więc skład albo zjechałby z 300 m do
        // stacji samym wybiegiem, albo (z warunkiem postoju wyżej) nie ruszyłby wcale.
        var drive = Drive(Axis(0.0, 800.0), Settings());
        drive.AuthorityEndM = 300.0;
        while (drive.ChainageM < 100.0 || drive.State.SpeedMps > 0.0)
        {
            drive.Step();
            Assert.IsTrue(drive.Steps < 12000, "skład nie zatrzymał się przed autorytetem");
        }

        drive.AuthorityEndM = null;
        var freed = 0;
        while (!drive.Finished && freed < 12000)
        {
            drive.Step();
            freed++;
        }

        Assert.IsTrue(drive.Finished,
            $"po otwarciu autorytetu skład przejechał w {freed} krokach tylko do " +
            $"{drive.ChainageM:F2} m — zatrzask hamowania nie został zwolniony");
        var call = drive.Result("arrived").Calls[0];
        Assert.IsTrue(call.TopSpeedMps > 5.0,
            $"po otwarciu autorytetu szczyt wyniósł {call.TopSpeedMps:F3} m/s — " +
            "to jest wybieg, a nie rozpęd");
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
