using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using MetroBxl.Sim.Line;
using MetroBxl.Sim.Physics;
using MetroBxl.Sim.Signalling;
using MetroBxl.Sim.Train;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace MetroBxl.Sim.Tests;

/// <summary>
/// Kabina pod sygnalizacją: człowiek prowadzi, ATP pilnuje (G-5).
///
/// <para>Testy stoją na dwóch nogach i obie są potrzebne. Pierwsza to <b>tożsamość</b>:
/// przejazd, w którym maszynista niczego nie łamie, ma być pod ochroną IDENTYCZNY co do
/// bitu z tym samym przejazdem bez ochrony. Bez tego wpięcie ATP po cichu przepisałoby
/// każdą dotychczasową bramkę trybu ręcznego. Druga to <b>ingerencja</b>: przejazd,
/// w którym maszynista limit przekracza, ma się skończyć gdzie indziej — i to musi być
/// widać jako liczba, nie jako wrażenie.</para>
///
/// <para><b>Pętla kroku jest tu przepisana z <c>FirstRun.StepOnce</c> i z
/// <c>Sim.Runner.Replay</c> jeden do jednego</b>, i to jest warunek sensu tych pomiarów:
/// klawisze po numerze kroku, kilometraż do filtra stacji ze stanu SPRZED kroku, nadzór
/// przed krokiem, ochrona jako OSTATNI filtr polecenia, meldunek ruchu po kroku. Zamiana
/// którejkolwiek z tych rzeczy miejscami daje przejazd, który wygląda tak samo, a nie
/// jest ten sam.</para>
/// </summary>
[TestClass]
public sealed class CabProtectionTests
{
    /// <summary>Ten sam identyfikator, którego używa scena i <c>Sim.Runner</c>.</summary>
    private const string TrainId = "KABINA";

    /// <summary>Czoło składu na starcie przejazdu ręcznego; ogon leży wtedy na 0,0 m.</summary>
    private const double StartChainageM = 94.0;

    /// <summary>Tempo nastawnika i okno zatrzymania — te same liczby, co podaje scena.</summary>
    private const double NotchRatePerSecond = 0.80;

    private const double ExchangeSeconds = 8.0;

    private const double StopWindowM = 5.0;

    /// <summary>Wynik jednego przejazdu ręcznego: to, co da się o nim zmierzyć.</summary>
    /// <param name="Steps">Wykonane kroki.</param>
    /// <param name="ChainageM">Kilometraż czoła na końcu.</param>
    /// <param name="TopSpeedKmh">Największa prędkość przejazdu.</param>
    /// <param name="Calls">Obsłużone stacje.</param>
    /// <param name="Missed">Stacje przejechane bez zatrzymania.</param>
    /// <param name="Warnings">Kroki nad prędkością dopuszczalną.</param>
    /// <param name="ServiceInterventions">Kroki z ingerencją hamulcem służbowym.</param>
    /// <param name="EmergencyInterventions">Kroki z ingerencją awaryjną.</param>
    /// <param name="LockedRoutes">Trasy zaryglowane przez nastawnię.</param>
    /// <param name="Telemetry">Ślad przejazdu, wiersz na krok; do porównania co do bitu.</param>
    private sealed record ManualRun(
        long Steps,
        double ChainageM,
        double TopSpeedKmh,
        IReadOnlyList<StationCall> Calls,
        IReadOnlyList<AxisStation> Missed,
        long Warnings,
        long ServiceInterventions,
        long EmergencyInterventions,
        int LockedRoutes,
        IReadOnlyList<string> Telemetry);

    private static string RepositoryRoot() =>
        MetroBxl.Tests.Shared.KorzenRepozytorium.Sciezka;

    private static InputLog Keys(string name) => InputLog.Parse(
        File.ReadAllText(Path.Combine(RepositoryRoot(), "tests", "data", name)));

    /// <summary>
    /// Przejazd ręczny odtworzony z zapisu wejść — ta sama kolejność działań, co
    /// w scenie i w <c>Sim.Runner</c>.
    /// </summary>
    /// <param name="log">Zapis wejść maszynisty.</param>
    /// <param name="axis">Oś przejazdu.</param>
    /// <param name="cab">Ochrona pociągu albo <c>null</c> dla przejazdu bez niej.</param>
    /// <param name="ceilingMps">Sufit maszynisty podawany kontrolerowi.</param>
    private static ManualRun Drive(InputLog log, TrackAxis axis, CabProtection? cab, double ceilingMps)
    {
        var model = VehicleModel.M7;
        var step = FixedStep.Simulation;
        var conditions = new RunConditions(
            model.MassKg(TrainLoad.Aw2), 0.0, model.Adhesion(RailCondition.Dry), TrackEnvironment.Tunnel);
        var controller = new TrainController(model);
        var notch = new DriverNotch(NotchRatePerSecond);
        var stations = new StationService(
            axis.Stations, new DoorCycle(ExchangeSeconds), step, StopWindowM);

        var state = DriveState.AtRest;
        var acceleration = 0.0;
        var top = 0.0;
        var telemetry = new List<string>(checked((int)log.Steps) + 1);

        double Chainage() => StartChainageM + state.DistanceM;

        telemetry.Add(DriveTelemetry.Row(
            state, step, Chainage(), acceleration, DriverCommand.Coast, DriveTelemetry.ManualPhase));

        while (state.Steps < log.Steps)
        {
            cab?.Supervise(state.Steps, Chainage(), state.SpeedMps);
            var requested = notch.Advance(log.KeysAt(state.Steps), step);
            var effective = stations.Filter(state, requested, Chainage());
            effective = cab is null ? effective : cab.Apply(effective);
            state = controller.Advance(state, conditions, effective, ceilingMps, step, out var forces);
            acceleration = forces.AccelerationMps2;
            cab?.Move(Chainage());
            if (state.SpeedMps > top)
            {
                top = state.SpeedMps;
            }

            telemetry.Add(DriveTelemetry.Row(
                state, step, Chainage(), acceleration, effective, DriveTelemetry.ManualPhase));
        }

        return new ManualRun(
            state.Steps,
            Chainage(),
            Units.MpsToKmh(top),
            stations.Calls,
            stations.Missed,
            cab?.Warnings ?? 0L,
            cab?.ServiceInterventions ?? 0L,
            cab?.EmergencyInterventions ?? 0L,
            cab?.Dispatcher.Locked ?? 0,
            telemetry);
    }

    private static CabProtection PackageACab() =>
        CabProtection.M7(SignallingPlanTests.PackageAPlan(), TrainId, StartChainageM);

    // --- tożsamość ------------------------------------------------------------------

    [TestMethod]
    public void PodLimitemPlanuOchronaNieRuszaAniJednegoKroku()
    {
        // Wzorzec `manual-keys.log` to przejazd prowadzony poprawnie: rozpęd do
        // 65,39 km/h, hamowanie, zatrzymanie w oknie Beekkantu, cykl drzwi. Nic w nim
        // nie przekracza ani limitu planu (72,00 km/h), ani krzywej do końca autorytetu.
        // Ochrona ma więc nie zrobić NIC — a „nic" znaczy tu ślad identyczny co do bitu,
        // nie „tyle samo sekund".
        var axis = SignallingPlanTests.PackageAAxis();
        var log = Keys("manual-keys.log");
        var ceiling = SignallingPlanTests.PackageAPlan().PermittedSpeedMps;

        var bez = Drive(log, axis, cab: null, ceiling);
        var z = Drive(log, axis, PackageACab(), ceiling);

        Console.WriteLine(string.Create(
            CultureInfo.InvariantCulture,
            $"[BEZ ATP] kroki={bez.Steps} chainage={bez.ChainageM:F3} m szczyt={bez.TopSpeedKmh:F3} km/h " +
            $"obsłużone={bez.Calls.Count} minięte={bez.Missed.Count}"));
        Console.WriteLine(string.Create(
            CultureInfo.InvariantCulture,
            $"[Z ATP]   kroki={z.Steps} chainage={z.ChainageM:F3} m szczyt={z.TopSpeedKmh:F3} km/h " +
            $"obsłużone={z.Calls.Count} minięte={z.Missed.Count} " +
            $"ostrzeżeń={z.Warnings} służbowych={z.ServiceInterventions} awaryjnych={z.EmergencyInterventions} " +
            $"tras={z.LockedRoutes}"));

        Assert.AreEqual(0L, z.Warnings, "ochrona ostrzegła przejazd, który nic nie łamie");
        Assert.AreEqual(0L, z.ServiceInterventions, "ochrona zahamowała przejazd, który nic nie łamie");
        Assert.AreEqual(0L, z.EmergencyInterventions, "ochrona zahamowała awaryjnie przejazd, który nic nie łamie");
        CollectionAssert.AreEqual(
            (System.Collections.ICollection)bez.Telemetry,
            (System.Collections.ICollection)z.Telemetry,
            "ślad pod ochroną różni się od śladu bez niej, choć ochrona nie ingerowała ani razu");
    }

    [TestMethod]
    public void SkladWchodziNaPlanZBlokuKtoryZajmujeOgonem()
    {
        // Przejazd ręczny zaczyna się z czołem na 94,000 m — bo cały skład ma stać na osi
        // (`DriveScenario.PackageAFirstRun`) — a to na pakiecie A jest już blok SZLAKOWY
        // S01; w peronowym P01 stoi wtedy OGON. Dopóki nastawnia pytała wyłącznie o blok
        // czoła, nie zamawiała ani jednej trasy: autorytet kończył się na 462,730 m
        // z powodem `BlockNotReserved`, a ochrona hamowała skład awaryjnie, zanim ten
        // dojechał do pierwszej stacji.
        var plan = SignallingPlanTests.PackageAPlan();
        var cab = PackageACab();

        Assert.AreEqual("S01", plan.BlockAt(StartChainageM).Id, "czoło startu nie leży już w S01");
        CollectionAssert.AreEquivalent(
            new[] { "P01", "S01" },
            (System.Collections.ICollection)cab.Signalling.BlocksOccupiedBy(TrainId),
            "skład o długości 94 m ma zajmować dwa bloki");

        var decision = cab.Supervise(0L, StartChainageM, 0.0);
        var authority = cab.Authority!.Value;

        Console.WriteLine(string.Create(
            CultureInfo.InvariantCulture,
            $"[WEJŚCIE] tras={cab.Dispatcher.Locked} odmów={cab.Dispatcher.Refused} " +
            $"autorytet do {authority.EndChainageM:F3} m ({authority.Reason}, blok {authority.LimitBlockId}) " +
            $"v_dop={Units.MpsToKmh(decision.PermittedSpeedMps):F2} km/h"));

        Assert.AreEqual(1, cab.Dispatcher.Locked, "nastawnia nie zaryglowała trasy z bloku, który skład zajmuje");
        Assert.AreEqual(0, cab.Dispatcher.Refused, "żądanie trasy zostało odrzucone");
        Assert.AreEqual(
            plan.BlockById("P02").EndM, authority.EndChainageM, 1e-9,
            "autorytet nie sięga do końca bloku docelowego zaryglowanej trasy R01");

        // Powód mówi o bloku PIERWSZYM ZA autorytetem, nie o ostatnim w nim: trasa
        // kończy się na P02, a S02 nie jest pod nią zarezerwowany. Tak samo wygląda
        // autorytet składu w `LineCore` między stacjami — to jest normalny stan planu
        // wymagającego tras, a nie brak zezwolenia na jazdę.
        Assert.AreEqual(AuthorityLimit.BlockNotReserved, authority.Reason);
        Assert.AreEqual("S02", authority.LimitBlockId);
        Assert.IsTrue(authority.AllowsMovement, "skład dostał autorytet zerowy — czyli stoi");
    }

    [TestMethod]
    public void TrasaZBlokuKtoregoSkladNieZajmujeJestNadalOdmowa()
    {
        // Kontrola do testu wyżej, bo samo „zaryglowało się" nie mówi, czy warunek
        // wejścia w ogóle jeszcze działa. Rozszerzenie miało dodać bloki, które skład
        // ZAJMUJE — a nie znieść wymóg, że skład ma tam być.
        var plan = SignallingPlanTests.PackageAPlan();
        var system = new FixedBlockSystem(plan);
        system.RegisterTrain(TrainId, StartChainageM, 94.0);

        Assert.IsFalse(
            system.RequestRoute("R05", TrainId),
            "skład zaryglował trasę wychodzącą z peronu, na którym go nie ma");

        var odmowa = system.Events[^1];
        Console.WriteLine($"[ODMOWA] {odmowa}");
        Assert.AreEqual(SignallingEventKind.RouteRejected, odmowa.Kind);
        StringAssert.Contains(odmowa.Detail, "train-not-at-route-entry");
    }

    // --- ingerencja -----------------------------------------------------------------

    [TestMethod]
    public void AtpHamujeZaMaszynisteIPrzejazdKonczySieGdzieIndziej()
    {
        // TEN SAM zapis wejść, TEN SAM sufit maszynisty (76 km/h, czyli 4 km/h ponad
        // limit planu), różnica JEDNA: ochrona wpięta albo nie. To jest kontrola,
        // której nie da się zrobić z wiersza poleceń, bo `Sim.Runner` odmawia sufitu
        // bez `--atp` — i dlatego stoi tutaj.
        var axis = SignallingPlanTests.PackageAAxis();
        var log = Keys("manual-overspeed.log");
        var plan = SignallingPlanTests.PackageAPlan();
        var ceiling = Units.KmhToMps(76.0);

        var bez = Drive(log, axis, cab: null, ceiling);
        var z = Drive(log, axis, PackageACab(), ceiling);

        Console.WriteLine(string.Create(
            CultureInfo.InvariantCulture,
            $"[BEZ ATP] kroki={bez.Steps} chainage={bez.ChainageM:F3} m szczyt={bez.TopSpeedKmh:F3} km/h " +
            $"obsłużone={bez.Calls.Count} minięte={bez.Missed.Count}"));
        Console.WriteLine(string.Create(
            CultureInfo.InvariantCulture,
            $"[Z ATP]   kroki={z.Steps} chainage={z.ChainageM:F3} m szczyt={z.TopSpeedKmh:F3} km/h " +
            $"obsłużone={z.Calls.Count} minięte={z.Missed.Count} " +
            $"ostrzeżeń={z.Warnings} służbowych={z.ServiceInterventions} awaryjnych={z.EmergencyInterventions} " +
            $"tras={z.LockedRoutes}"));
        Console.WriteLine(string.Create(
            CultureInfo.InvariantCulture,
            $"[RÓŻNICA] droga {bez.ChainageM - z.ChainageM:F3} m, " +
            $"szczyt {bez.TopSpeedKmh - z.TopSpeedKmh:F3} km/h"));

        // 1. Maszynista PROSI o 76 km/h i bez ochrony tyle dostaje.
        Assert.AreEqual(76.0, bez.TopSpeedKmh, 1e-3, "przejazd bez ochrony nie dobił do sufitu maszynisty");

        // 2. Pod ochroną nie dostaje. Limit planu staje się faktycznym pułapem —
        //    z dokładnością do jednego kroku, bo ochrona ingeruje PO przekroczeniu,
        //    a nie zamiast niego (`docs/15-classic-signalling.md` §5).
        var limitKmh = Units.MpsToKmh(plan.PermittedSpeedMps);
        Assert.IsTrue(
            z.TopSpeedKmh < bez.TopSpeedKmh,
            $"szczyt pod ochroną {z.TopSpeedKmh} km/h nie jest niższy od {bez.TopSpeedKmh} km/h");
        Assert.IsTrue(
            z.TopSpeedKmh - limitKmh < 0.1,
            $"szczyt pod ochroną {z.TopSpeedKmh} km/h wyszedł ponad limit planu {limitKmh} km/h o więcej niż 0,1");

        // 3. Ochrona naprawdę ingerowała, i to hamulcem SŁUŻBOWYM — czyli decyzją
        //    właściciela z 04.09.2026 („ostrzeżenie, potem hamulec służbowy"), a nie
        //    tylko awaryjną ścieżką przy końcu autorytetu.
        Assert.IsTrue(z.Warnings > 0L, "ochrona nie odnotowała ani jednego przekroczenia");
        Assert.IsTrue(z.ServiceInterventions > 0L, "ochrona nie ingerowała hamulcem służbowym ani razu");

        // 4. Przejazd kończy się GDZIE INDZIEJ, i to jest ta liczba, którą widać.
        Assert.IsTrue(
            bez.ChainageM - z.ChainageM > 100.0,
            $"ochrona skróciła przejazd tylko o {bez.ChainageM - z.ChainageM:F3} m");

        // 5. Drzwi NIE otwierają się poza oknem ±5,0 m — także wtedy, gdy ochrona
        //    wchodzi w polecenie. Okno `StationService` jest dwustronne i ochrona go
        //    nie dotyka, ale przejazd, w którym skład staje z pełnego hamulca ATP tuż
        //    za peronem, jest dokładnie tym, na czym taka reguła by się wywróciła.
        foreach (var call in z.Calls)
        {
            Console.WriteLine(string.Create(
                CultureInfo.InvariantCulture,
                $"[STACJA] {call.Name}: błąd zatrzymania {call.StopErrorM:+0.000;-0.000;0.000} m, " +
                $"postój {call.ArrivalSeconds:F3}–{call.DepartureSeconds:F3} s"));
            Assert.IsTrue(
                Math.Abs(call.StopErrorM) <= StopWindowM,
                $"{call.Name}: drzwi otwarte {call.StopErrorM:F3} m od peronu, czyli poza oknem ±{StopWindowM:F1} m");
        }

        Assert.IsTrue(z.Calls.Count > 0, "przejazd nie obsłużył ani jednej stacji, więc nie sprawdza okna drzwi");
    }

    [TestMethod]
    public void OchronaJestOSTATNIMFiltremIMaszynistaJejNieNadpisuje()
    {
        // Issue #26: „nie można ominąć ATP przez input gracza". Test bierze decyzję
        // z ingerencją i sprawdza, że pełny ciąg maszynisty przez nią nie przechodzi —
        // a hamulec, który maszynista podał SAM, nie zostaje przez ochronę zluzowany.
        var plan = SignallingPlanTests.SyntheticPlan(requireRoute: false, 0.0, 600.0, 1400.0);
        var cab = new CabProtection(plan, VehicleModel.M7, TrainId, 94.0, 94.0);

        // Skład rozpędzony ponad limit planu na długim autorytecie: ochrona ma sięgnąć
        // po hamulec służbowy, a nie po awaryjny.
        var decision = cab.Supervise(0L, 94.0, Units.KmhToMps(90.0));
        Console.WriteLine($"[DECYZJA] {decision}");
        Assert.AreEqual(ProtectionAction.ServiceIntervention, decision.Action);

        var pelnyCiag = cab.Apply(DriverCommand.FullPower);
        Console.WriteLine(string.Create(
            CultureInfo.InvariantCulture,
            $"[POLECENIE] maszynista ciąg 1.00/hamulec 0.00 -> ATP ciąg {pelnyCiag.Throttle:F2}/hamulec {pelnyCiag.Brake:F2}"));
        Assert.AreEqual(0.0, pelnyCiag.Throttle, 1e-12, "ochrona przepuściła ciąg maszynisty");
        Assert.IsTrue(pelnyCiag.Brake > 0.0, "ochrona nie podała hamulca");

        // Hamulec maszynisty mocniejszy niż żądanie ochrony ZOSTAJE. Ochrona idzie
        // wyłącznie w stronę mocniejszego hamowania — inaczej ostrzeżenie luzowałoby
        // hamulec komuś, kto już hamuje.
        var pelnyHamulec = cab.Apply(DriverCommand.FullServiceBrake);
        Assert.AreEqual(1.0, pelnyHamulec.Brake, 1e-12, "ochrona zluzowała hamulec podany przez maszynistę");
    }

    [TestMethod]
    public void PrzedPierwszymNadzoremPolecenieIdzieBezZmiany()
    {
        // Ochrona bez odczytu autorytetu nie ma czego pilnować. Zgadywanie hamulca
        // byłoby wymyślaniem stanu sygnalizacji, a zerowanie ciągu — zatrzymaniem
        // składu na starcie z powodu, którego nikt nie policzył.
        var cab = PackageACab();

        Assert.IsNull(cab.Decision, "decyzja istnieje przed pierwszym nadzorem");
        Assert.IsNull(cab.Authority, "autorytet istnieje przed pierwszym nadzorem");
        Assert.AreEqual(DriverCommand.FullPower, cab.Apply(DriverCommand.FullPower));
    }

    // --- reset ----------------------------------------------------------------------

    [TestMethod]
    public void ResetCofaSkladNaPlanieRazemZResztaPrzejazdu()
    {
        // Bez tego reset przejazdu (klawisz R) byłby WYJĄTKIEM, a nie resetem:
        // `FixedBlockSystem.MoveTrain` odmawia cofnięcia czoła, więc pierwszy meldunek
        // ruchu po resecie wywaliłby pętlę klatek sceny.
        var cab = PackageACab();
        cab.Supervise(0L, StartChainageM, 0.0);
        cab.Move(600.0);
        cab.Supervise(120L, 600.0, Units.KmhToMps(90.0));

        Console.WriteLine(string.Create(
            CultureInfo.InvariantCulture,
            $"[PRZED RESETEM] czoło={cab.Signalling.FrontOf(TrainId):F3} m ostrzeżeń={cab.Warnings} " +
            $"tras={cab.Dispatcher.Locked} decyzja={cab.Decision!.Value.Action}"));

        var przedResetem = cab.Signalling.FrontOf(TrainId);
        var cofniecie = Assert.ThrowsException<ArgumentOutOfRangeException>(
            () => cab.Move(StartChainageM));
        StringAssert.Contains(cofniecie.Message, "cofnąć się");

        cab.Reset();

        Console.WriteLine(string.Create(
            CultureInfo.InvariantCulture,
            $"[PO RESECIE]    czoło={cab.Signalling.FrontOf(TrainId):F3} m ostrzeżeń={cab.Warnings} " +
            $"tras={cab.Dispatcher.Locked} decyzja={(cab.Decision is null ? "brak" : cab.Decision.Value.Action.ToString())}"));

        Assert.AreEqual(600.0, przedResetem, 1e-9);
        Assert.AreEqual(StartChainageM, cab.Signalling.FrontOf(TrainId), 1e-9, "skład nie wrócił na początek");
        Assert.AreEqual(0L, cab.Warnings);
        Assert.AreEqual(0L, cab.ServiceInterventions);
        Assert.AreEqual(0L, cab.EmergencyInterventions);
        Assert.AreEqual(0.0, cab.MaxBrakeDemandMps2, 1e-12);
        Assert.AreEqual(0, cab.Dispatcher.Locked, "nastawnia pamięta trasy sprzed resetu");
        Assert.IsNull(cab.Decision, "decyzja przeżyła reset");
        Assert.IsNull(cab.Authority, "autorytet przeżył reset");
        Assert.AreEqual(0, cab.Signalling.Events.Count - CountOfRegistrationEvents(cab),
            "strumień zdarzeń po resecie niesie coś sprzed niego");

        // I najważniejsze: po resecie meldunek ruchu z powrotem DZIAŁA.
        cab.Move(StartChainageM + 1.0);
    }

    [TestMethod]
    public void ResetPrzejazduIDZIEPRZEZRunRestartANieObokNiego()
    {
        // Od #255 reset jest WPISEM W ZAPISIE WEJŚĆ, a ten sam zapis odtwarzają dwie
        // strony bramki: scena i `Sim.Runner replay`. Odpowiedź „co reset zeruje" musi
        // więc być jedna i leżeć w rdzeniu. Ten test pilnuje, że ochrona kabiny jest
        // w tej odpowiedzi, a nie w osobnym wołaniu obok niej po stronie sceny —
        // bo osobne wołanie zerowałoby sygnalizację TYLKO w Godocie, a bramka przy
        // progu 0 zgadzałaby się dokładnie do pierwszego kroku z ingerencją.
        var cab = PackageACab();
        var notch = new DriverNotch(NotchRatePerSecond);
        var stations = new StationService(
            SignallingPlanTests.PackageAAxis().Stations,
            new DoorCycle(ExchangeSeconds),
            FixedStep.Simulation,
            StopWindowM);

        cab.Supervise(0L, StartChainageM, 0.0);
        cab.Move(600.0);
        cab.Supervise(120L, 600.0, Units.KmhToMps(90.0));

        Console.WriteLine(string.Create(
            CultureInfo.InvariantCulture,
            $"[PRZED RunRestart] czoło={cab.Signalling.FrontOf(TrainId):F3} m " +
            $"tras={cab.Dispatcher.Locked} ostrzeżeń={cab.Warnings}"));

        var start = RunRestart.Apply(notch, stations, cab, telemetry: null);

        Console.WriteLine(string.Create(
            CultureInfo.InvariantCulture,
            $"[PO RunRestart]   czoło={cab.Signalling.FrontOf(TrainId):F3} m " +
            $"tras={cab.Dispatcher.Locked} ostrzeżeń={cab.Warnings}"));

        Assert.AreEqual(DriveState.AtRest, start.Drive);
        Assert.AreEqual(
            StartChainageM, cab.Signalling.FrontOf(TrainId), 1e-9,
            "RunRestart nie cofnął składu na planie — reset sceny i reset rdzenia się rozjadą");
        Assert.AreEqual(0, cab.Dispatcher.Locked, "nastawnia pamięta trasy sprzed resetu");
        Assert.AreEqual(0L, cab.Warnings);
        Assert.IsNull(cab.Decision);

        // I meldunek ruchu znowu działa — bez tego pierwszy krok po resecie byłby
        // wyjątkiem, a nie krokiem.
        cab.Move(StartChainageM + 1.0);
    }

    [TestMethod]
    public void RunRestartBezOchronyNadalDzialaBoNieKazdyPrzejazdJaMa()
    {
        // Brak ochrony jest poprawnym stanem, a nie błędem: przejazd ręczny bez
        // `--signalling` i przejazd `--line` nie mają jej wcale. Reset, który by się na
        // tym przewracał, przewracałby scenę.
        var notch = new DriverNotch(NotchRatePerSecond);
        notch.Advance(DriverKeys.Powering, FixedStep.Simulation);

        var start = RunRestart.Apply(notch, stations: null, cab: null, telemetry: null);

        Assert.AreEqual(DriveState.AtRest, start.Drive);
        Assert.AreEqual(DriverCommand.Coast, notch.Command);
    }

    /// <summary>
    /// Ile zdarzeń wystawia samo wprowadzenie składu na plan: rejestracja, zajęcie
    /// każdego z bloków pod składem i pierwszy autorytet.
    /// </summary>
    private static int CountOfRegistrationEvents(CabProtection cab) =>
        2 + cab.Signalling.BlocksOccupiedBy(TrainId).Count;
}
