using System;
using MetroBxl.Sim.Line;
using MetroBxl.Sim.Physics;
using MetroBxl.Sim.Train;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace MetroBxl.Sim.Tests;

/// <summary>
/// Okno zatrzymania w <see cref="LineDrive"/> jest JEDNOSTRONNE, a w
/// <see cref="StationService"/> DWUSTRONNE — i to jest wybrana odpowiedź 6.M2, przybita
/// tu z obu stron na TYM SAMYM postoju.
///
/// <para><b>Dlaczego jeden postój, a nie dwa zestawy.</b> <c>WindowIsTwoSidedUnlikeTheAutopilot</c>
/// w <see cref="StationServiceTests"/> nazywał różnicę tylko po jednej stronie i sprawdzał
/// ją stanem podanym wprost; po stronie <see cref="LineDrive"/> nie pilnował jej nic.
/// Tutaj skład jest naprawdę PROWADZONY ręcznie na linii i staje 50 m za punktem
/// zatrzymania — a potem ten sam stan ocenia druga klasa. Różnica przestaje być opisem
/// w komentarzu i staje się dwoma werdyktami o jednym stanie.</para>
///
/// <para><b>Dlaczego jednostronne zostaje.</b> Dwustronne okno w <see cref="LineDrive"/>
/// wymagałoby reguły, której żaden dokument nie podaje: co robi skład, który stanął
/// ZA oknem, a <c>_next</c> się nie posunął. <see cref="StationService"/> ma na to
/// rejestr <c>Missed</c>; <see cref="LineDrive"/> go nie ma, a odjazd bez obsługi
/// z MB-08 jest gałęzią TRWAJĄCEGO postoju — bez założonego postoju nie ma jak
/// zadziałać. Ślad sześciu osi zostaje przy tym bez zmiany co do bajtu, bo autopilot
/// nigdy nie przestrzeliwuje.</para>
/// </summary>
[TestClass]
public sealed class StopWindowParityTests
{
    private const string TrainId = "A";
    private const double WindowM = 5.0;
    private const double OvershootM = 50.0;

    private static readonly double[] Stations = { 0.0, 600.0, 1400.0, 2000.0 };

    private static LineCore Line() => LineCore.M7(
        SignallingPlanTests.SyntheticPlan(requireRoute: false, Stations),
        SignallingPlanTests.SyntheticAxis(Stations),
        RunConditions.Level(VehicleModel.M7, TrainLoad.Aw0),
        new LineRunSettings(Units.KmhToMps(60.0), 10.0, 1.0, WindowM));

    /// <summary>
    /// Maszynista celujący w <paramref name="aimM"/> zamiast w punkt zatrzymania.
    /// Ten sam sufit prędkości co w <see cref="ManualDoorsOnLineTests"/>, tylko cel
    /// przesunięty — bo autopilot za peronem nie stanie nigdy, a o to pyta pozycja.
    /// </summary>
    private static DriverCommand DriverAimingAt(LineDrive drive, double aimM)
    {
        var remaining = aimM - drive.ChainageM;
        if (remaining <= 0.0)
        {
            return DriverCommand.FullServiceBrake;
        }

        var speed = drive.State.SpeedMps;
        var stopping = speed * speed / (2.0 * 1.1);
        var cap = remaining > 60.0 ? 12.0 : remaining > 10.0 ? 3.0 : 0.6;
        return speed > cap || remaining <= stopping + 0.10
            ? DriverCommand.FullServiceBrake
            : new DriverCommand(0.5, 0.0);
    }

    /// <summary>Prowadzi ręcznie do zatrzymania w okolicy <paramref name="aimM"/> i trzyma hamulec.</summary>
    private static LineTrain DriveAndStop(double aimM) => DriveAndStopOnLine(aimM).Train;

    /// <summary>To samo co <see cref="DriveAndStop"/>, z linią — dla poleceń drzwi i oddania sterowania.</summary>
    private static (LineCore Line, LineTrain Train) DriveAndStopOnLine(double aimM)
    {
        var line = Line();
        line.Add(TrainId, 0L);
        line.Step();
        var train = line.TakeControl(TrainId);
        Assert.AreEqual(ControlOwner.Driver, train.Owner,
            "bez przejęcia skład prowadzi autopilot, a ten za peronem nie staje");

        var stoodFor = 0;
        for (var i = 0; i < 40_000 && stoodFor < 200; i++)
        {
            line.Drive(TrainId, DriverAimingAt(train.Drive!, aimM));
            line.Step();
            stoodFor = train.Drive!.State.SpeedMps <= 0.0 && train.Drive.ChainageM > 1.0
                ? stoodFor + 1
                : 0;
        }

        Assert.AreEqual(200, stoodFor,
            $"skład nie stanął w okolicy {aimM:F1} m, kilometraż {train.Drive!.ChainageM:F2} m");
        return (line, train);
    }

    [TestMethod]
    public void LineDrive_liczy_postoj_50_m_ZA_peronem_a_StationService_ten_sam_stan_uznaje_za_MINIETY()
    {
        var target = Stations[1];
        var train = DriveAndStop(target + OvershootM);
        var drive = train.Drive!;
        var stoppedAt = drive.ChainageM;

        // Przyrząd: skład naprawdę stoi za oknem, i to wyraźnie — inaczej ten test
        // mierzyłby postój w oknie, który obie klasy liczą tak samo.
        Assert.IsTrue(stoppedAt > target + WindowM + 40.0,
            $"skład stanął {stoppedAt - target:F2} m za punktem zatrzymania — za blisko okna");
        Assert.IsTrue(stoppedAt < Stations[2] - WindowM, "skład dojechał pod następną stację");

        // LineDrive: postój SIĘ LICZY. Wywołanie trafia do tej stacji, a błąd zatrzymania
        // jest zapisany uczciwie, z plusem — to on, a nie brak wywołania, niesie
        // informację o przestrzeleniu.
        Assert.IsTrue(drive.AtStation, "LineDrive nie założył postoju za peronem");
        Assert.AreEqual(1, drive.Calls.Count, "LineDrive miał odnotować dokładnie jedno wywołanie");
        Assert.AreEqual(target, drive.Calls[0].ChainageM, 1e-9, "wywołanie trafiło do innej stacji");
        Assert.AreEqual(stoppedAt - target, drive.Calls[0].StopErrorM, 1e-9,
            "błąd zatrzymania nie jest odległością czoła od punktu zatrzymania");
        Assert.IsTrue(drive.Calls[0].StopErrorM > OvershootM - 1.0,
            $"błąd zatrzymania {drive.Calls[0].StopErrorM:F2} m, oczekiwany około +{OvershootM:F0} m");

        // StationService, ten sam stan: postój się NIE liczy, stacja jest minięta.
        var axis = SignallingPlanTests.SyntheticAxis(Stations);
        var service = new StationService(axis.Stations, new DoorCycle(10.0), FixedStep.Simulation, WindowM);
        service.Filter(drive.State, DriverCommand.FullServiceBrake, stoppedAt);

        Assert.IsFalse(service.AtStation, "StationService założył postój za oknem");
        Assert.AreEqual(0, service.Calls.Count, "StationService odnotował wywołanie za oknem");
        Assert.AreEqual(1, service.Missed.Count, "stacja za składem nie trafiła do Missed");
        Assert.AreEqual(target, service.Missed[0].ChainageM, 1e-9, "minięta jest inna stacja niż ta za składem");
    }

    [TestMethod]
    public void Od_dolu_okno_jest_to_samo_w_obu_klasach_sklad_stojacy_PRZED_oknem_nie_ma_postoju()
    {
        // Druga strona tej samej odpowiedzi: jednostronność dotyczy WYŁĄCZNIE górnej
        // granicy. Gdyby dolna też się rozjechała, test wyżej przeszedłby dalej, a
        // różnica byłaby szersza, niż mówią komentarze w obu klasach.
        var target = Stations[1];
        // Cel 15 m przed punktem zatrzymania, a nie tuż przed oknem: ręczny maszynista
        // z tego pliku przestrzeliwuje swój cel o kilka metrów (zmierzone: celując
        // w −6 m, stanął na −1,76 m, czyli już W oknie), więc zapas musi być większy
        // niż ten rozrzut, żeby test mierzył skład PRZED oknem.
        var train = DriveAndStop(target - 15.0);
        var drive = train.Drive!;
        var stoppedAt = drive.ChainageM;

        Assert.IsTrue(stoppedAt < target - WindowM,
            $"skład stanął {stoppedAt - target:F2} m od punktu zatrzymania — już w oknie");
        Assert.IsTrue(stoppedAt > target - 20.0,
            $"skład stanął {stoppedAt - target:F2} m od punktu zatrzymania — za daleko od okna");

        Assert.IsFalse(drive.AtStation, "LineDrive założył postój przed oknem");
        Assert.AreEqual(0, drive.Calls.Count, "LineDrive odnotował wywołanie przed oknem");

        var axis = SignallingPlanTests.SyntheticAxis(Stations);
        var service = new StationService(axis.Stations, new DoorCycle(10.0), FixedStep.Simulation, WindowM);
        service.Filter(drive.State, DriverCommand.FullServiceBrake, stoppedAt);

        Assert.IsFalse(service.AtStation, "StationService założył postój przed oknem");
        Assert.AreEqual(0, service.Calls.Count, "StationService odnotował wywołanie przed oknem");
        Assert.AreEqual(0, service.Missed.Count, "stacja przed składem została uznana za miniętą");
    }

    // --- 6.M3: okno DRZWI jest dwustronne (DECYZJA WŁAŚCICIELA 23.09.2026) ---------

    [TestMethod]
    public void Drzwi_50_m_ZA_peronem_sa_odmowione_z_powodem_poza_peronem()
    {
        var (line, train) = DriveAndStopOnLine(Stations[1] + OvershootM);
        var drive = train.Drive!;
        Assert.IsTrue(drive.AtStation, "przyrząd: bez postoju ten test nie pyta o drzwi na postoju");

        var odpowiedz = line.RequestDoorOpen(TrainId);

        Assert.IsFalse(odpowiedz.Ok, "drzwi otworzyły się 50 m za peronem");
        Assert.AreEqual(DoorRefusal.OutsidePlatformWindow, odpowiedz.Refusal,
            "odmowa ma nieść powód „skład stoi poza peronem”, a nie inny");
        for (var i = 0; i < 2_000; i++)
        {
            line.Drive(TrainId, DriverCommand.FullServiceBrake);
            line.Step();
            Assert.AreEqual(DoorPhase.Closed, drive.Phase, $"krok {i}: drzwi ruszyły mimo odmowy");
        }
    }

    [TestMethod]
    public void Po_odmowie_maszynista_odjezdza_a_stacja_zostaje_jako_odjazd_bez_obslugi()
    {
        var (line, train) = DriveAndStopOnLine(Stations[1] + OvershootM);
        var drive = train.Drive!;
        Assert.IsFalse(line.RequestDoorOpen(TrainId).Ok, "przyrząd: drzwi miały być odmówione");

        for (var i = 0; i < 400 && drive.AtStation; i++)
        {
            line.Drive(TrainId, new DriverCommand(0.5, 0.0));
            line.Step();
        }

        Assert.IsFalse(drive.AtStation, "maszynista nie zdołał odjechać spod peronu, za którym stanął");
        Assert.AreEqual(1, drive.Calls.Count, "stacja miała zostać odnotowana dokładnie raz");
        Assert.IsTrue(double.IsFinite(drive.Calls[0].DepartureSeconds), "odjazd bez obsługi nie ma czasu odjazdu");
        Assert.AreEqual(Stations[2], drive.NextStation!.Value.ChainageM, 1e-9,
            "po odjeździe kolejną stacją ma być następna na osi");
    }

    [TestMethod]
    public void Oddany_autopilotowi_za_peronem_odjezdza_bez_otwierania_drzwi()
    {
        // Autopilot dopilnowuje postojów ręcznych (MB-08) i woła `StationStop.RequestOpen`
        // wprost, z pominięciem odmowy maszynisty — więc bez 6.M3 otworzyłby drzwi
        // w tunelu, a z samą odmową stałby tam do końca przejazdu.
        var (line, train) = DriveAndStopOnLine(Stations[1] + OvershootM);
        var drive = train.Drive!;
        line.ReleaseControl(TrainId);
        Assert.AreEqual(ControlOwner.Autopilot, train.Owner, "przyrząd: sterowanie nie wróciło do autopilota");

        var otwarte = 0;
        for (var i = 0; i < 40_000 && drive.Calls.Count < 2; i++)
        {
            line.Step();
            if (drive.Calls.Count == 1 && drive.Phase != DoorPhase.Closed)
            {
                otwarte++;
            }
        }

        Assert.AreEqual(0, otwarte, "autopilot otworzył drzwi za peronem");
        Assert.AreEqual(2, drive.Calls.Count, "autopilot nie dojechał do następnej stacji");
        Assert.AreEqual(Stations[2], drive.Calls[1].ChainageM, 1e-9, "drugie wywołanie trafiło do innej stacji");
    }
}
