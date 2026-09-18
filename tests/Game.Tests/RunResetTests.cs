using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using MetroBxl.Game.Input;
using MetroBxl.Sim.Line;
using MetroBxl.Sim.Physics;
using MetroBxl.Sim.Signalling;
using MetroBxl.Sim.Train;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace MetroBxl.Game.Tests;

/// <summary>
/// Reset przejazdu (akcja <c>run_reset</c>, klawisz <c>R</c>) — zadanie G-4
/// z <c>reports/droga-do-grywalnosci.md</c>.
///
/// <para><b>Co te testy pilnują.</b> Nie tego, że reset zeruje prędkość — tego, że
/// zeruje <b>cały</b> przejazd. Do 05.09.2026 zerował stan dynamiczny składu
/// i nie dotykał <c>StationService</c>: skład wracał na 94,0 m z kolejką stacji
/// ustawioną tam, dokąd zdążył dojechać, a trwający cykl drzwi szedł dalej
/// z poprzedniego przejazdu (§5.4 tamtego raportu). Decyzja „co reset obejmuje"
/// mieszkała w metodzie węzła Godota, więc nie było czym jej wywołać ani czym
/// sprawdzić; teraz mieszka w <see cref="RunReset.Apply"/> i jest wołana stąd.</para>
///
/// <para><b>Pomiar, nie deklaracja.</b> <see cref="ResetStopsTheDoorCycleCounterAtZero"/>
/// nie ustawia stanu ręcznie: przejeżdża tę samą sekwencję klawiszy, co wzorzec
/// <c>tests/data/manual-keys.log</c> (W od kroku 0, S od kroku 2800), zatrzymuje skład
/// na Beekkant i mierzy licznik postoju przed resetem i po nim. Zatrzymanie wychodzi
/// na 509,707 m przy błędzie −0,023 m, czyli dokładnie tam, gdzie zapisał to komentarz
/// tamtego pliku — a jest to liczba policzona dwiema niezależnymi drogami
/// (<c>docs/06-worked-example.md</c> §Wzór na dowód).</para>
/// </summary>
[TestClass]
public sealed class RunResetTests
{
    /// <summary>Krok, od którego wzorzec <c>manual-keys.log</c> trzyma hamulec.</summary>
    private const long BrakeFromStep = 2800L;

    /// <summary>Czas klatki pomiaru. 59,94 kl./s, żeby akumulator miał nierozliczoną resztę.</summary>
    private const double FrameSeconds = 1.0 / 59.94;

    /// <summary>
    /// Kabina w trybie ręcznym bez Godota: te same obiekty rdzenia i ta sama kolejność
    /// ich wołania, co w <c>FirstRun.StepOnce</c> — odczyt klawiszy po numerze kroku,
    /// zapis wejść, nastawnik, filtr stacji, kontroler.
    ///
    /// <para>Jest to <b>przyrząd pomiarowy</b>, a nie druga kopia sceny: produkcyjna
    /// pętla zostaje w <c>FirstRun</c>, a tutaj chodzi o to, żeby stan, który reset ma
    /// wyzerować, powstał z prawdziwego przejazdu, a nie z przypisań w teście.</para>
    /// </summary>
    private sealed class Cab
    {
        private readonly FixedStep _step = FixedStep.Simulation;
        private readonly TrainController _controller = new(VehicleModel.M7);
        private readonly RunConditions _conditions;
        private readonly double _startChainageM;
        private readonly double _limitMps;

        public Cab(TrackAxis axis, double startChainageM, double limitMps)
        {
            _conditions = new RunConditions(
                VehicleModel.M7.MassKg(TrainLoad.Aw2),
                0.0,
                VehicleModel.M7.Adhesion(RailCondition.Dry),
                TrackEnvironment.Tunnel);
            _startChainageM = startChainageM;
            _limitMps = limitMps;

            Accumulator = new StepAccumulator(_step);
            Notch = new DriverNotch(DesignAssumptions.ControlNotchRatePerSecond);
            Input = new DriverInput();
            Stations = new StationService(
                axis.Stations,
                new DoorCycle(DesignAssumptions.PassengerExchangeSeconds),
                _step,
                DesignAssumptions.StationStopWindowM);
            Recorder = new InputLogRecorder();
            Telemetry = new List<string> { DriveTelemetry.Header };
        }

        public StepAccumulator Accumulator { get; }

        public DriverNotch Notch { get; }

        public DriverInput Input { get; }

        public StationService Stations { get; }

        public InputLogRecorder Recorder { get; }

        public List<string> Telemetry { get; }

        public DriveState State { get; private set; } = DriveState.AtRest;

        public DriverCommand Command { get; private set; } = DriverCommand.Coast;

        public DriverCommand EffectiveCommand { get; private set; } = DriverCommand.Coast;

        public double AccelerationMps2 { get; private set; }

        public double ChainageM => _startChainageM + State.DistanceM;

        /// <summary>Klawisze wzorca: ciąg od kroku 0, hamulec od kroku 2800.</summary>
        public static DriverKeys KeysAt(long step)
            => step < BrakeFromStep ? DriverKeys.Powering : DriverKeys.Braking;

        /// <summary>Jedzie klatkami po 1/59,94 s, aż wykona co najmniej tyle kroków.</summary>
        public void DriveTo(long steps)
        {
            while (State.Steps < steps)
            {
                var wanted = Accumulator.StepsForFrame(FrameSeconds);
                for (var i = 0L; i < wanted; i++)
                {
                    StepOnce();
                }
            }
        }

        /// <summary>Reset przejazdu tą samą drogą, co scena: przez <see cref="RunReset"/>.</summary>
        public void Reset()
        {
            // Ochrona kabiny jest `null`, bo ten przyrząd jedzie BEZ `--signalling` —
            // tak samo jak wzorzec `manual-keys.log`, na którym stoi cały ten plik.
            // Że reset zeruje także ją, przybija `CabProtectionTests` po stronie rdzenia,
            // czyli tam, gdzie od G-5 mieszka odpowiedź „co reset zeruje" (`RunRestart`).
            var start = RunReset.Apply(
                Accumulator, Notch, Input, Stations, null, Recorder, Telemetry);
            State = start.Drive;
            Command = start.Command;
            EffectiveCommand = start.EffectiveCommand;
            AccelerationMps2 = start.AccelerationMps2;
        }

        /// <summary>
        /// Numer kroku w SESJI — jak `FirstRun._logStep`. Nie wraca po resecie, bo po nim
        /// indeksowany jest zapis wejść, a `State.Steps` zaczyna wtedy od zera.
        /// </summary>
        public long LogStep { get; private set; }

        private void StepOnce()
        {
            // DWA INDEKSY, bo to dwie różne rzeczy. Klawisze bierze się po numerze kroku
            // PRZEJAZDU, bo ten stanowisko modeluje maszynistę, który po resecie robi
            // DOKŁADNIE TO SAMO — inaczej „przejazd po resecie powtarza przejazd" nie
            // miałoby czego powtarzać. Zapis wejść idzie po numerze kroku SESJI, bo taki
            // jest format: jeden plik opisuje całą sesję, razem z resetem.
            var keys = KeysAt(State.Steps);
            Recorder.Record(LogStep, keys);
            Command = Notch.Advance(keys, _step);
            EffectiveCommand = Stations.Filter(State, Command, ChainageM);
            State = _controller.Advance(
                State, _conditions, EffectiveCommand, _limitMps, _step, out var forces);
            AccelerationMps2 = forces.AccelerationMps2;
            LogStep++;
            Telemetry.Add(State.Steps.ToString(CultureInfo.InvariantCulture));
        }
    }
    private static TrackAxis PackageAAxis()
        => TrackAxis.FromJson(
            File.ReadAllText(Path.Combine(MetroBxl.Tests.Shared.KorzenRepozytorium.Sciezka, "data", "track", "L1_A.json")));

    /// <summary>
    /// Prędkość dopuszczalna trybu ręcznego — z tego samego planu sygnalizacji, z którego
    /// bierze ją scena (<see cref="RunPlan.ManualSpeedLimitPlanPath"/>). Liczba wpisana
    /// tu wprost byłaby drugą kopią tej samej wiedzy.
    /// </summary>
    private static double ManualLimitMps()
        => SignallingPlan.FromJson(
            File.ReadAllText(Path.Combine(MetroBxl.Tests.Shared.KorzenRepozytorium.Sciezka, RunPlan.ManualSpeedLimitPlanPath)))
            .PermittedSpeedMps;

    private static Cab NewCab()
    {
        var scenario = DriveScenario.PackageAFirstRun(VehicleModel.M7);
        Assert.AreEqual(94.0, scenario.StartChainageM, 1e-9, "czoło startuje na 94,000 m");
        return new Cab(PackageAAxis(), scenario.StartChainageM, ManualLimitMps());
    }

    // --- pomiar: licznik cyklu drzwi po resecie ------------------------------------

    /// <summary>
    /// USTERKA G-4, ZMIERZONA: trwający cykl drzwi przeżywał reset przejazdu.
    ///
    /// <para>Przejazd jest prawdziwy — 5400 kroków wzorcowej sekwencji klawiszy na osi
    /// L1_A. Mierzone jest to samo, co pokazuje HUD w wierszu stacji: faza drzwi,
    /// licznik postoju i blokada trakcji, najpierw w środku cyklu, potem zaraz po
    /// resecie.</para>
    /// </summary>
    [TestMethod]
    public void ResetStopsTheDoorCycleCounterAtZero()
    {
        var cab = NewCab();
        cab.DriveTo(5400L);

        // --- stan PRZED resetem. Bez tego pomiaru „po resecie zero" nie znaczy nic ---
        Assert.AreEqual(1, cab.Stations.Calls.Count,
            "przejazd nie obsłużył ani jednej stacji, więc nie ma czego resetować");
        var call = cab.Stations.Calls[0];
        Assert.AreEqual("Beekkant", call.Name);
        Assert.IsTrue(cab.Stations.AtStation, "cykl drzwi już się domknął — pomiar byłby pusty");
        Assert.IsTrue(cab.Stations.DwellRemainingSeconds > 0.0);
        Assert.IsFalse(cab.Stations.TractionAllowed);

        Console.WriteLine(string.Create(
            CultureInfo.InvariantCulture,
            $"[PRZED RESETEM] krok={cab.State.Steps} chainage={cab.ChainageM:F3} m " +
            $"droga={cab.State.DistanceM:F3} m v={cab.State.SpeedMps:F3} m/s\n" +
            $"[PRZED RESETEM] stacja={call.Name} blad={call.StopErrorM:+0.000;-0.000;0.000} m " +
            $"przyjazd={call.ArrivalSeconds:F3} s\n" +
            $"[PRZED RESETEM] drzwi={cab.Stations.Phase} postoj={cab.Stations.DwellRemainingSeconds:F3} s " +
            $"trakcja={(cab.Stations.TractionAllowed ? "WOLNA" : "ZABLOKOWANA")} " +
            $"obsluzone={cab.Stations.Calls.Count} minione={cab.Stations.Missed.Count}\n" +
            $"[PRZED RESETEM] nastawnik={cab.Command.Throttle:F3}/{cab.Command.Brake:F3} " +
            $"reszta={cab.Accumulator.CarrySeconds:R} s zapis={cab.Recorder.NextStep} krokow " +
            $"telemetria={cab.Telemetry.Count} wierszy"));

        // Zgodność z komentarzem wzorca `tests/data/manual-keys.log`: zatrzymanie na
        // 509,707 m, błąd −0,023 m. Druga droga do tej samej liczby.
        Assert.AreEqual(509.707, call.StoppedAtChainageM, 5e-4, "czoło stanęło gdzie indziej");
        Assert.AreEqual(-0.023, call.StopErrorM, 5e-4, "błąd zatrzymania");

        cab.Reset();

        Console.WriteLine(string.Create(
            CultureInfo.InvariantCulture,
            $"[PO RESECIE] krok={cab.State.Steps} chainage={cab.ChainageM:F3} m " +
            $"droga={cab.State.DistanceM:F3} m v={cab.State.SpeedMps:F3} m/s\n" +
            $"[PO RESECIE] drzwi={cab.Stations.Phase} postoj={cab.Stations.DwellRemainingSeconds:F3} s " +
            $"trakcja={(cab.Stations.TractionAllowed ? "WOLNA" : "ZABLOKOWANA")} " +
            $"obsluzone={cab.Stations.Calls.Count} minione={cab.Stations.Missed.Count} " +
            $"nastepna={cab.Stations.Approach(cab.ChainageM).Name}\n" +
            $"[PO RESECIE] nastawnik={cab.Command.Throttle:F3}/{cab.Command.Brake:F3} " +
            $"reszta={cab.Accumulator.CarrySeconds:R} s zapis={cab.Recorder.NextStep} krokow " +
            $"telemetria={cab.Telemetry.Count} wierszy"));

        // --- licznik cyklu drzwi NAPRAWDĘ stoi na zerze ---
        Assert.AreEqual(0.0, cab.Stations.DwellRemainingSeconds, 0.0,
            "licznik cyklu drzwi nie stoi po resecie na zerze");
        Assert.IsFalse(cab.Stations.AtStation, "trwający cykl drzwi przeżył reset");
        Assert.AreEqual(DoorPhase.Closed, cab.Stations.Phase);
        Assert.IsTrue(cab.Stations.TractionAllowed, "trakcja zablokowana po resecie");
        Assert.AreEqual(0, cab.Stations.Calls.Count);
        Assert.AreEqual(0, cab.Stations.Missed.Count);
        Assert.AreEqual("Beekkant", cab.Stations.Approach(cab.ChainageM).Name,
            "kolejka stacji nie wróciła na początek");

        // --- i reszta stanu przejazdu, w tej samej jednej operacji ---
        Assert.AreEqual(0L, cab.State.Steps);
        Assert.AreEqual(0.0, cab.State.DistanceM, 0.0);
        Assert.AreEqual(0.0, cab.State.SpeedMps, 0.0);
        Assert.AreEqual(94.0, cab.ChainageM, 1e-9);
        Assert.AreEqual(0.0, cab.AccelerationMps2, 0.0);
        Assert.AreEqual(DriverCommand.Coast, cab.Command);
        Assert.AreEqual(DriverCommand.Coast, cab.EffectiveCommand);
        Assert.AreEqual(DriverCommand.Coast, cab.Notch.Command, "dźwignia została tam, gdzie była");
        Assert.AreEqual(DriverKeys.None, cab.Input.Keys);
        Assert.AreEqual(0.0, cab.Accumulator.CarrySeconds, 0.0, "reszta czasu klatki przeżyła reset");
        // ZAPIS WEJŚĆ NIE JEST ZEROWANY — i to zdanie jest przepisane, a nie dopisane obok.
        // Do 05.09.2026 stało tu `Assert.AreEqual(0L, …, "zapis wejść nadpisywałby numery
        // kroków")`, bo reset kasował zapis. Decyzja właściciela (wariant W1) rozdzieliła
        // numer kroku SESJI od numeru kroku PRZEJAZDU: pierwszy nie wraca nigdy, drugi
        // wraca do zera — więc zapis idzie dalej i niesie reset jako wpis.
        Assert.AreEqual(5401L, cab.Recorder.NextStep, "numer kroku sesji cofnął się po resecie");
        Assert.AreEqual(1, cab.Recorder.ResetCount, "reset nie trafił do zapisu wejść");
        Assert.IsTrue(cab.Recorder.EntryCount > 0, "zapis wejść został wykasowany razem z przejazdem");
        Assert.AreEqual(1, cab.Telemetry.Count, "próbki poprzedniego przejazdu zostały w telemetrii");
        Assert.AreEqual(DriveTelemetry.Header, cab.Telemetry[0], "nagłówek telemetrii zniknął");
    }

    /// <summary>
    /// Kryterium G-4 wprost: przejazd po resecie ma tę samą sekwencję wywołań stacji,
    /// co ten sam przejazd bez resetu, przy progu <b>0</b> dla kilometrażu i błędu
    /// zatrzymania.
    ///
    /// <para>Próg zero jest dosłowny — <see cref="StationCall"/> jest rekordem, więc
    /// równość idzie po wszystkich polach naraz, razem z czasami i prędkością szczytową.
    /// Ten test odróżnia „reset wygląda na wykonany" od „reset postawił przejazd
    /// w punkcie, z którego wychodzi ten sam przebieg".</para>
    /// </summary>
    [TestMethod]
    public void RunAfterResetRepeatsTheRunBitForBit()
    {
        var wzorzec = NewCab();
        wzorzec.DriveTo(5400L);

        var zResetem = NewCab();
        zResetem.DriveTo(5400L);
        zResetem.Reset();
        zResetem.DriveTo(5400L);

        CollectionAssert.AreEqual(
            new List<StationCall>(wzorzec.Stations.Calls),
            new List<StationCall>(zResetem.Stations.Calls),
            "wywołania stacji po resecie: " + string.Join(" | ", zResetem.Stations.Calls));

        Assert.AreEqual(wzorzec.State, zResetem.State, "stan składu po resecie i przejeździe");
        Assert.AreEqual(wzorzec.ChainageM, zResetem.ChainageM, 0.0);
        Assert.AreEqual(wzorzec.Command, zResetem.Command);
        Assert.AreEqual(wzorzec.EffectiveCommand, zResetem.EffectiveCommand);
        // Liczniki SESJI mają się różnić dokładnie o długość przejazdu sprzed resetu —
        // to jest ta sama liczba widziana z drugiej strony, a nie rozjazd. Zapis
        // porzucony razem z przejazdem dałby tu równość i wyglądałby na poprawny.
        Assert.AreEqual(5401L, wzorzec.Recorder.NextStep);
        Assert.AreEqual(10802L, zResetem.Recorder.NextStep, "zapis sesji nie objął obu przejazdów");
        Assert.AreEqual(
            wzorzec.Recorder.NextStep * 2,
            zResetem.Recorder.NextStep,
            "zapis sesji nie jest sumą obu przejazdów");
        Assert.AreEqual(1, zResetem.Recorder.ResetCount);
        Assert.AreEqual(wzorzec.State.Steps, zResetem.State.Steps, "przejazd po resecie ma inną długość");
        Assert.AreEqual(wzorzec.Telemetry.Count, zResetem.Telemetry.Count);

        Console.WriteLine(string.Create(
            CultureInfo.InvariantCulture,
            $"[BEZ RESETU]  {wzorzec.Stations.Calls[0]}\n" +
            $"[PO RESECIE]  {zResetem.Stations.Calls[0]}\n" +
            $"[BEZ RESETU]  chainage={wzorzec.ChainageM:R} m kroki={wzorzec.State.Steps}\n" +
            $"[PO RESECIE]  chainage={zResetem.ChainageM:R} m kroki={zResetem.State.Steps}"));
    }

    // --- co reset obejmuje, jako funkcja ------------------------------------------

    [TestMethod]
    public void FreshValuesAreZeroAcrossTheBoard()
    {
        var start = RunReset.Values;

        Assert.AreEqual(DriveState.AtRest, start.Drive);
        Assert.AreEqual(0L, start.Drive.Steps);
        Assert.AreEqual(0.0, start.Drive.DistanceM, 0.0);
        Assert.AreEqual(0.0, start.Drive.SpeedMps, 0.0);
        Assert.AreEqual(DriverKeys.None, start.Keys);
        Assert.AreEqual(DriverKeys.None, start.ActiveKeys);
        Assert.AreEqual(DriverCommand.Coast, start.Command);
        Assert.AreEqual(DriverCommand.Coast, start.EffectiveCommand);
        Assert.AreEqual(0.0, start.AccelerationMps2, 0.0);
    }

    /// <summary>
    /// Brak obsługi stacji, zapisu wejść i telemetrii jest poprawnym stanem, a nie
    /// błędem: tryb <c>--line</c> nie ma <c>StationService</c>, a przejazd bez
    /// <c>--input-log</c> nie ma czego nagrywać. Reset, który by się na tym przewracał,
    /// przewracałby scenę.
    /// </summary>
    [TestMethod]
    public void ResetWorksInAModeThatHasNoStationsNoRecorderAndNoTelemetry()
    {
        var accumulator = new StepAccumulator(FixedStep.Simulation);
        accumulator.StepsForFrame(FrameSeconds);
        var notch = new DriverNotch(DesignAssumptions.ControlNotchRatePerSecond);
        notch.Advance(DriverKeys.Powering, FixedStep.Simulation);

        var start = RunReset.Apply(accumulator, notch, new DriverInput(), null, null, null, null);

        Assert.AreEqual(DriveState.AtRest, start.Drive);
        Assert.AreEqual(0.0, accumulator.CarrySeconds, 0.0);
        Assert.AreEqual(DriverCommand.Coast, notch.Command);
    }

    /// <summary>
    /// Reset sceny PRZEKAZUJE ochronę kabiny do rdzenia, a nie zeruje jej u siebie.
    ///
    /// <para>Od G-5 tryb ręczny z <c>--signalling</c> ma sygnalizację: skład stoi na
    /// blokach i ma zaryglowane trasy. Od #255 reset jest wpisem w zapisie wejść, więc
    /// ten sam reset wykonuje <c>Sim.Runner replay</c> — a on <see cref="RunReset"/>
    /// nie widzi. Gdyby scena zerowała ochronę własnym wołaniem obok
    /// <see cref="RunRestart"/>, sygnalizacja wracałaby do początku TYLKO w Godocie,
    /// a bramka porównująca obie strony przy progu 0 zgadzałaby się dokładnie do
    /// pierwszego kroku, w którym ochrona ingeruje.</para>
    /// </summary>
    [TestMethod]
    public void ResetPassesTheCabProtectionDownToTheCore()
    {
        var axis = PackageAAxis();
        var plan = SignallingPlan.FromAxis(
            axis,
            VehicleRegistry.M7.RequireValue("parameters.length_m", ParameterStatus.Spec),
            Units.KmhToMps(72.0),
            0.0,
            ProtectionVariant.LegacyFixedBlock,
            requireRoute: true);
        var cab = CabProtection.M7(plan, "KABINA", 94.0);

        cab.Supervise(0L, 94.0, 0.0);
        cab.Move(600.0);
        cab.Supervise(120L, 600.0, Units.KmhToMps(90.0));

        Console.WriteLine(string.Create(
            CultureInfo.InvariantCulture,
            $"[PRZED RESETEM] czoło={cab.Signalling.FrontOf("KABINA"):F3} m " +
            $"tras={cab.Dispatcher.Locked} ostrzeżeń={cab.Warnings}"));

        RunReset.Apply(
            new StepAccumulator(FixedStep.Simulation),
            new DriverNotch(DesignAssumptions.ControlNotchRatePerSecond),
            new DriverInput(),
            null,
            cab,
            null,
            null);

        Console.WriteLine(string.Create(
            CultureInfo.InvariantCulture,
            $"[PO RESECIE]    czoło={cab.Signalling.FrontOf("KABINA"):F3} m " +
            $"tras={cab.Dispatcher.Locked} ostrzeżeń={cab.Warnings}"));

        Assert.AreEqual(
            94.0, cab.Signalling.FrontOf("KABINA"), 1e-9,
            "reset sceny nie cofnął składu na planie — scena i rdzeń zresetują dwie różne rzeczy");
        Assert.AreEqual(0, cab.Dispatcher.Locked, "nastawnia pamięta trasy sprzed resetu");
        Assert.AreEqual(0L, cab.Warnings);
        Assert.IsNull(cab.Decision);
    }

    [TestMethod]
    public void ResetRefusesToWorkWithoutTheObjectsEveryRunHas()
    {
        var accumulator = new StepAccumulator(FixedStep.Simulation);
        var notch = new DriverNotch(DesignAssumptions.ControlNotchRatePerSecond);

        Assert.ThrowsException<ArgumentNullException>(
            () => RunReset.Apply(null!, notch, new DriverInput(), null, null, null, null));
        Assert.ThrowsException<ArgumentNullException>(
            () => RunReset.Apply(accumulator, null!, new DriverInput(), null, null, null, null));
        Assert.ThrowsException<ArgumentNullException>(
            () => RunReset.Apply(accumulator, notch, null!, null, null, null, null));
    }

    /// <summary>
    /// Telemetria traci PRÓBKI, a nie nagłówek: po resecie numery kroków zaczynają się
    /// od zera, więc wiersze sprzed resetu opisywałyby inny przejazd tymi samymi
    /// numerami — a plik porównuje się przy progu 0.
    /// </summary>
    [TestMethod]
    public void TelemetryKeepsItsHeaderAndLosesTheSamples()
    {
        var telemetry = new List<string> { DriveTelemetry.Header, "0;...", "120;...", "240;..." };
        RunReset.DropSamples(telemetry);

        Assert.AreEqual(1, telemetry.Count);
        Assert.AreEqual(DriveTelemetry.Header, telemetry[0]);

        // Lista pusta znaczy „przejazd nie zbiera telemetrii" i taka zostaje.
        var brak = new List<string>();
        RunReset.DropSamples(brak);
        Assert.AreEqual(0, brak.Count);
        RunReset.DropSamples(null);
    }
}
