using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using MetroBxl.Sim.Line;
using MetroBxl.Sim.Physics;
using MetroBxl.Sim.Signalling;
using MetroBxl.Sim.Train;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace MetroBxl.Sim.Tests;

/// <summary>
/// Ochrona pociągu i jazda dwóch składów w trybie <c>classic_2026</c>.
///
/// <para>To jest miejsce, w którym T-313 spotyka się z T-311 i T-312: krzywa hamowania
/// jest **ta sama**, którą prowadzi się skład, a blokada drzwi wisi na tym samym
/// warunku zatrzymania, co cykl drzwi.</para>
/// </summary>
[TestClass]
public sealed class ClassicSignallingScenarioTests
{
    private static readonly VehicleModel Model = VehicleModel.M7;

    private static readonly double TrainLengthM =
        VehicleRegistry.M7.RequireValue("parameters.length_m", ParameterStatus.Spec);

    private static RunConditions Level() => RunConditions.Level(Model, TrainLoad.Aw0);

    private static SignallingPlan Plan(bool requireRoute = false) =>
        SignallingPlanTests.SyntheticPlan(requireRoute, 0.0, 600.0, 1400.0, 2000.0);

    private static TrainProtection Protection(SignallingPlan plan) => new(plan, Model);

    // --- krzywa hamowania -------------------------------------------------------------

    /// <summary>
    /// Zasada 4 z T-313: ATP nie ma własnej fizyki. Prędkość dopuszczalna wyznaczona
    /// przez ochronę musi zgadzać się z drogą hamowania solvera z T-311 co do metra,
    /// a nie „mniej więcej".
    /// </summary>
    [TestMethod]
    public void Predkosc_dopuszczalna_jest_odwrotnoscia_krzywej_z_T_311()
    {
        var plan = Plan();
        var protection = Protection(plan);
        var solver = new BrakingPointSolver(Model);

        foreach (var distance in new[] { 10.0, 50.0, 120.0, 300.0, 700.0 })
        {
            var permitted = protection.PermittedSpeedMps(distance);
            if (permitted >= plan.PermittedSpeedMps)
            {
                Assert.IsTrue(
                    solver.Solve(plan.PermittedSpeedMps, 0.0, Model.DesignServiceBrakeMps2).DistanceM <= distance,
                    $"{distance:F0} m: limit planu ma się zmieścić w authority");
                continue;
            }

            var need = solver.Solve(permitted, 0.0, Model.DesignServiceBrakeMps2).DistanceM;
            Assert.IsTrue(need <= distance + 1e-6, $"{distance:F0} m: droga {need:F6} m nie mieści się w authority");

            var faster = solver.Solve(permitted + 0.01, 0.0, Model.DesignServiceBrakeMps2).DistanceM;
            Assert.IsTrue(faster > distance, $"{distance:F0} m: o 0,01 m/s szybciej wciąż by się mieściło");
        }
    }

    [TestMethod]
    public void Predkosc_dopuszczalna_spada_do_zera_na_koncu_authority()
    {
        var protection = Protection(Plan());

        Assert.AreEqual(0.0, protection.PermittedSpeedMps(0.0), 0.0);
        Assert.IsTrue(protection.PermittedSpeedMps(1.0) > 0.0);
        Assert.IsTrue(protection.PermittedSpeedMps(1.0) < protection.PermittedSpeedMps(100.0));
    }

    // --- ingerencja --------------------------------------------------------------------

    /// <summary>Scenariusz „overspeed ponad curve → intervention".</summary>
    [TestMethod]
    public void Predkosc_ponad_krzywa_wywoluje_ostrzezenie_i_ingerencje()
    {
        var plan = Plan();
        var system = new FixedBlockSystem(plan);
        var protection = Protection(plan);
        system.RegisterTrain("A", 1400.0, TrainLengthM);
        system.RegisterTrain("B", 200.0, TrainLengthM);

        var authority = system.Authority("B");
        var permitted = protection.PermittedSpeedMps(authority.DistanceM);
        var before = system.Events.Count;

        var calm = protection.Supervise(system, "B", permitted * 0.5);
        Assert.AreEqual(ProtectionAction.None, calm.Action);
        Assert.IsFalse(calm.Overspeed);

        var decision = protection.Supervise(system, "B", permitted * 1.05);
        Assert.IsTrue(decision.Overspeed);
        Assert.AreEqual(ProtectionAction.ServiceIntervention, decision.Action);
        Assert.IsTrue(decision.BrakeDemandMps2 > 0.0);
        Assert.IsTrue(decision.BrakeDemandMps2 <= Model.DesignServiceBrakeMps2);

        var kinds = system.Events.Skip(before).Select(e => e.Kind).ToList();
        CollectionAssert.Contains(kinds, SignallingEventKind.OverspeedWarning);
        CollectionAssert.Contains(kinds, SignallingEventKind.OverspeedIntervention);
    }

    /// <summary>
    /// Próg ingerencji awaryjnej nie jest przyjętym marginesem — jest policzony:
    /// wypada tam, gdzie hamulec służbowy przestaje wystarczać na pozostałą drogę.
    /// </summary>
    [TestMethod]
    public void Gdy_hamulec_sluzbowy_nie_wystarcza_ingerencja_jest_awaryjna()
    {
        var plan = Plan();
        var system = new FixedBlockSystem(plan);
        var protection = Protection(plan);
        system.RegisterTrain("A", 1400.0, TrainLengthM);
        system.RegisterTrain("B", 600.0, TrainLengthM);

        var authority = system.Authority("B");
        Assert.IsTrue(authority.DistanceM < 50.0, $"do końca authority zostało {authority.DistanceM:F2} m");

        var decision = protection.Supervise(system, "B", Units.KmhToMps(60.0));
        Assert.AreEqual(ProtectionAction.EmergencyIntervention, decision.Action);
        Assert.AreEqual(Model.DesignEmergencyBrakeMps2, decision.BrakeDemandMps2, 0.0);
        Assert.IsTrue(
            system.Events.Any(e => e.Kind == SignallingEventKind.EmergencyIntervention),
            "ingerencja awaryjna musi zostawić ślad w zapisie");
    }

    /// <summary>
    /// Sam próg służbowy → awaryjny, a nie tylko jego okolice.
    ///
    /// <para>Zmierzone 02.09.2026 mutacją: podmiana warunku
    /// <c>need &lt;= _serviceBrakeMps2</c> na <c>need &lt;= _emergencyBrakeMps2</c> —
    /// czyli zgoda na ingerencję służbową tam, gdzie służbowy nie wystarcza —
    /// przechodziła przez cały zestaw (Passed: 255). Istniejące testy używają
    /// prędkości tak wysokich, że potrzebne opóźnienie przekracza także hamulec
    /// awaryjny; obie strony podmienionego warunku dają wtedy ten sam wynik.</para>
    ///
    /// <para>Ten test kalibruje się na rzeczywistej odległości authority: liczy
    /// potrzebne opóźnienie solverem z T-311, a potem buduje ochronę tak, żeby ta
    /// liczba wypadła DOKŁADNIE między hamulcem służbowym a awaryjnym. To jedyne
    /// miejsce, w którym oba warunki się rozchodzą.</para>
    /// </summary>
    [TestMethod]
    public void Prog_miedzy_sluzbowym_a_awaryjnym_wypada_tam_gdzie_sluzbowy_przestaje_wystarczac()
    {
        var plan = Plan();
        var system = new FixedBlockSystem(plan);
        system.RegisterTrain("A", 1400.0, TrainLengthM);
        system.RegisterTrain("B", 200.0, TrainLengthM);

        var solver = new BrakingPointSolver(Model);
        var distance = system.Authority("B").DistanceM;
        var speed = Units.KmhToMps(40.0);
        var need = solver.RequiredDeceleration(speed, 0.0, distance).DecelerationMps2;
        Assert.IsTrue(need > 0.0, $"potrzebne opóźnienie {need:F4} m/s² nie nadaje się na próg");

        // Hamulec służbowy poniżej potrzeby, awaryjny powyżej — czyli dokładnie
        // sytuacja „służbowy nie wystarcza, ale awaryjny tak".
        var tooWeak = new TrainProtection(plan, solver, need * 0.5, need * 2.0);
        var escalated = tooWeak.Supervise(system, "B", speed);
        Assert.AreEqual(ProtectionAction.EmergencyIntervention, escalated.Action,
            $"potrzeba {need:F4} m/s², służbowy {need * 0.5:F4} m/s²");
        StringAssert.Contains(escalated.Reason, "service-brake-insufficient");
        Assert.AreEqual(need * 2.0, escalated.BrakeDemandMps2, 0.0);

        // Ta sama sytuacja z hamulcem służbowym mocniejszym od potrzeby: bez eskalacji.
        // Nie żądam tu ingerencji służbowej, bo mocniejszy hamulec podnosi też samą
        // krzywą — skład może się zmieścić pod nią i nie być w ogóle w nadmiernej
        // prędkości. Istotne jest, że hamulec awaryjny NIE wchodzi.
        var strongEnough = new TrainProtection(plan, solver, need * 2.0, need * 4.0);
        var served = strongEnough.Supervise(system, "B", speed);
        Assert.AreNotEqual(ProtectionAction.EmergencyIntervention, served.Action,
            $"potrzeba {need:F4} m/s², służbowy {need * 2.0:F4} m/s²");
    }

    [TestMethod]
    public void Wyczerpane_authority_przy_ruchu_to_zawsze_ingerencja_awaryjna()
    {
        var plan = Plan();
        var system = new FixedBlockSystem(plan);
        var protection = Protection(plan);
        system.RegisterTrain("A", 1400.0, TrainLengthM);
        system.RegisterTrain("B", 200.0, TrainLengthM);
        system.MoveTrain("B", system.Authority("B").EndChainageM);

        Assert.AreEqual(0.0, system.Authority("B").DistanceM, 0.0);
        var decision = protection.Supervise(system, "B", 1.0);

        Assert.AreEqual(ProtectionAction.EmergencyIntervention, decision.Action);
        StringAssert.Contains(decision.Reason, "authority-exhausted");
    }

    /// <summary>
    /// Scenariusz „stopping curve pozwala zatrzymać przed endpointem": skład rusza
    /// z prędkością dokładnie dopuszczalną i hamuje wyłącznie tym, czego żąda ATP.
    /// Sprawdzamy, że **fizyka z T-310** faktycznie mieści się w tej drodze.
    /// </summary>
    [TestMethod]
    public void Hamowanie_na_zadanie_ATP_konczy_sie_przed_koncem_authority()
    {
        var plan = Plan();
        var system = new FixedBlockSystem(plan);
        var protection = Protection(plan);
        var controller = new TrainController(Model);
        var step = FixedStep.Simulation;

        system.RegisterTrain("A", 1400.0, TrainLengthM);
        system.RegisterTrain("B", 200.0, TrainLengthM);

        var endpoint = system.Authority("B").EndChainageM;
        var state = new DriveState(0, protection.PermittedSpeedMps(endpoint - 200.0), 0.0, 0.0);
        Assert.IsTrue(state.SpeedMps > 5.0, $"scenariusz bez sensu przy {state.SpeedMps:F2} m/s");

        while (state.SpeedMps > 0.01 && state.Steps < 120 * 600)
        {
            var decision = protection.Supervise(system, "B", state.SpeedMps);
            var command = new DriverCommand(0.0, decision.BrakeCommandFraction(controller.ServiceBrakeMps2));
            state = controller.Advance(state, Level(), command, plan.PermittedSpeedMps, step, out _);
            system.MoveTrain("B", 200.0 + state.DistanceM);
        }

        var stoppedAt = system.FrontOf("B");
        Assert.IsTrue(
            stoppedAt <= endpoint,
            $"skład stanął na {stoppedAt:F3} m, a authority kończy się na {endpoint:F3} m");
        Assert.IsFalse(
            system.Events.Any(e => e.Kind == SignallingEventKind.AuthorityViolation),
            "hamowanie w granicach krzywej nie może naruszyć authority");
    }

    // --- drzwi i KCV --------------------------------------------------------------------

    [TestMethod]
    public void Drzwi_zwalniaja_sie_tylko_na_postoju_w_bloku_peronowym()
    {
        var plan = Plan();
        var system = new FixedBlockSystem(plan);
        var protection = Protection(plan);
        system.RegisterTrain("A", 600.0, TrainLengthM);

        Assert.IsTrue(protection.DoorRelease(system, "A", 0.0, kcvAvailable: false).Released,
            "skład stoi w bloku peronowym P02");

        var moving = protection.DoorRelease(system, "A", 3.0, kcvAvailable: false);
        Assert.IsFalse(moving.Released);
        Assert.AreEqual("moving", moving.Reason);

        system.MoveTrain("A", 800.0);
        var offPlatform = protection.DoorRelease(system, "A", 0.0, kcvAvailable: false);
        Assert.IsFalse(offPlatform.Released);
        StringAssert.Contains(offPlatform.Reason, "not-at-platform");

        var kinds = system.Events.Select(e => e.Kind).ToList();
        CollectionAssert.Contains(kinds, SignallingEventKind.DoorRelease);
        CollectionAssert.Contains(kinds, SignallingEventKind.DoorInhibit);
    }

    /// <summary>
    /// KCV jako interfejs, nie jako urządzenie: w wariancie linii 2/6 brak potwierdzenia
    /// z KCV blokuje zwolnienie drzwi. Telegramów, balis ani protokołu tu nie ma i nie
    /// będzie — <c>ground-truth.json</c> wymienia je jako nieznane.
    /// </summary>
    [TestMethod]
    public void W_wariancie_KCV_brak_potwierdzenia_blokuje_drzwi()
    {
        var axis = SignallingPlanTests.SyntheticAxis(0.0, 600.0, 1400.0);
        var plan = SignallingPlan.FromAxis(
            axis, TrainLengthM, Units.KmhToMps(72.0), 0.0, ProtectionVariant.LegacyWithKcv, requireRoute: false);
        var system = new FixedBlockSystem(plan);
        var protection = new TrainProtection(plan, Model);
        system.RegisterTrain("A", 600.0, TrainLengthM);

        protection.RequireKcv();
        Assert.IsFalse(protection.DoorRelease(system, "A", 0.0, kcvAvailable: false).Released);
        Assert.AreEqual("kcv-unavailable", protection.DoorRelease(system, "A", 0.0, kcvAvailable: false).Reason);
        Assert.IsTrue(protection.DoorRelease(system, "A", 0.0, kcvAvailable: true).Released);
    }

    [TestMethod]
    public void Lista_funkcji_KCV_jest_dokladnie_ta_ktora_podaje_STIB() =>
        CollectionAssert.AreEqual(
            new[]
            {
                KcvFunction.SecureAutomaticDoorOpening,
                KcvFunction.StationAnnouncements,
                KcvFunction.WheelLubrication,
            },
            TrainProtection.SourceBackedKcvFunctions.ToArray());

    // --- dwa składy na pakiecie A ---------------------------------------------------------

    /// <summary>
    /// Kryterium „skończone, gdy" z T-313: dwa składy na **rzeczywistej** osi pakietu A
    /// w trybie <c>classic_2026</c>, bez kolizji.
    ///
    /// <para>Skład <c>M1</c> stoi na Beekkant i jedzie do Étangs Noirs. Skład <c>M2</c>
    /// stoi na Gare de l'Ouest i chce jechać do Beekkant — ale nie dostanie trasy,
    /// dopóki M1 nie zwolni bloków. Cała regulacja odstępu wychodzi z ryglowania,
    /// a nie z rozkładu: żaden ze składów nie wie o drugim.</para>
    /// </summary>
    [TestMethod]
    public void Dwa_sklady_na_pakiecie_A_dojezdzaja_bez_kolizji()
    {
        var axis = SignallingPlanTests.PackageAAxis();
        var plan = SignallingPlanTests.PackageAPlan();
        var system = new FixedBlockSystem(plan);
        var protection = new TrainProtection(plan, Model);
        var fleet = new[]
        {
            new Runner("M1", axis, from: 1, to: 2),
            new Runner("M2", axis, from: 0, to: 1),
        };

        foreach (var runner in fleet)
        {
            system.RegisterTrain(runner.Id, runner.FrontM, TrainLengthM);
        }

        var step = FixedStep.Simulation;
        var budget = 120 * 900;
        var steps = 0;
        while (steps < budget && fleet.Any(r => !r.Done))
        {
            foreach (var runner in fleet)
            {
                runner.Step(system, protection, step);
            }

            var footprints = fleet
                .Select(r => (Rear: system.RearOf(r.Id), Front: system.FrontOf(r.Id)))
                .OrderBy(f => f.Front)
                .ToList();
            Assert.IsTrue(
                footprints[0].Front < footprints[1].Rear,
                $"krok {steps}: składy zeszły się — {footprints[0].Front:F2} m i {footprints[1].Rear:F2} m");

            steps++;
        }

        Assert.IsTrue(fleet.All(r => r.Done), $"przejazd nie domknął się w {budget} krokach");

        Assert.IsFalse(
            system.Events.Any(e => e.Kind == SignallingEventKind.AuthorityViolation),
            "naruszenie authority: " + string.Join("; ", system.Events
                .Where(e => e.Kind == SignallingEventKind.AuthorityViolation)
                .Select(e => e.ToString())));
        Assert.IsFalse(
            system.Events.Any(e => e.Kind == SignallingEventKind.EmergencyIntervention),
            "prowadzenie zgodne z krzywą nie powinno wywołać hamowania awaryjnego");

        foreach (var runner in fleet)
        {
            var target = axis.Stations[runner.To].ChainageM;
            Assert.IsTrue(
                Math.Abs(system.FrontOf(runner.Id) - target) < 0.5,
                string.Create(CultureInfo.InvariantCulture,
                    $"{runner.Id}: stanął na {system.FrontOf(runner.Id):F3} m zamiast {target:F3} m"));
        }

        var rejected = system.Events
            .Where(e => e.Kind == SignallingEventKind.RouteRejected && e.TrainId == "M2")
            .ToList();
        Assert.IsTrue(rejected.Count > 0, "M2 musi najpierw dostać odmowę — blok przed nim jest zajęty");
        StringAssert.Contains(rejected[0].Detail, "block-occupied");

        var lockedForM2 = system.Events.First(e => e.Kind == SignallingEventKind.RouteLocked && e.TrainId == "M2");
        var m1LeftPlatform = system.Events.First(e =>
            e.Kind == SignallingEventKind.BlockReleased && e.TrainId == "M1" && e.SubjectId == "P02");
        Assert.IsTrue(
            m1LeftPlatform.Sequence < lockedForM2.Sequence,
            "M2 dostał trasę dopiero po tym, jak M1 zwolnił blok peronowy Beekkant");

        // Liczby do raportu. Test nie zależy od nich — zależy od asercji powyżej.
        Console.WriteLine(string.Create(CultureInfo.InvariantCulture,
            $"pakiet A / classic_2026: {steps} kroków = {steps / (double)FixedStep.SimulationHertz:F2} s, " +
            $"{system.Events.Count} zdarzeń, {rejected.Count} odrzuconych żądań trasy, " +
            $"0 naruszeń authority; M1 stanął na {system.FrontOf("M1"):F3} m, M2 na {system.FrontOf("M2"):F3} m"));
    }

    /// <summary>
    /// Jeden prowadzony skład: pętla sprzężenia zwrotnego z <c>LineRun</c> ograniczona
    /// przez movement authority i nadzorowana przez ATP. Nie jest to symulator ruchu
    /// (to T-320) — jest to najmniejsze, co pozwala przejechać scenariusz z T-313.
    /// </summary>
    // --- ATP INGERUJE: decyzja właściciela z 04.09.2026 ---------------------
    //
    // „Ostrzeżenie, potem hamulec służbowy". Do tej pory `Supervise` liczyło decyzję,
    // a nikt jej nie stosował — HUD pokazywał liczbę i tyle. Poniżej testy tej jednej
    // rzeczy, która zamienia liczbę w zachowanie: `ProtectionDecision.Apply`.

    private static ProtectionDecision Decision(ProtectionAction action, double demand) =>
        new(0.0, 100.0, action, demand, action != ProtectionAction.None, "test");

    [TestMethod]
    public void Bez_ingerencji_polecenie_maszynisty_przechodzi_bez_zmiany()
    {
        // Samo przekroczenie prędkości jest OSTRZEŻENIEM, nie hamowaniem: dopóki krzywa
        // wyrabia, ochrona nie ma prawa odebrać jazdy. Gdyby `None` też hamowało,
        // przejazd z limitem planu przestałby być tym zweryfikowanym przejazdem.
        var wanted = new DriverCommand(0.65, 0.0);
        var passed = Decision(ProtectionAction.None, 0.0).Apply(wanted, 1.1);

        Assert.AreEqual(wanted.Throttle, passed.Throttle, 0.0, "trakcja ma przejść nietknięta");
        Assert.AreEqual(wanted.Brake, passed.Brake, 0.0, "hamulec ma przejść nietknięty");
    }

    [TestMethod]
    public void Ingerencja_sluzbowa_zeruje_trakcje_i_podaje_zadany_hamulec()
    {
        // 0,55 m/s² przy hamulcu służbowym 1,10 m/s² to dokładnie połowa nastawnika.
        // Liczba jest wybrana tak, żeby dała się sprawdzić w głowie, a nie żeby zgodzić
        // się z implementacją.
        var passed = Decision(ProtectionAction.ServiceIntervention, 0.55)
            .Apply(new DriverCommand(1.0, 0.0), 1.1);

        Assert.AreEqual(0.0, passed.Throttle, 0.0, "trakcja przy ingerencji musi zniknąć");
        Assert.AreEqual(0.5, passed.Brake, 1e-12, "0,55 / 1,10 = połowa nastawnika hamulca");
    }

    [TestMethod]
    public void Ochrona_nie_odpuszcza_hamulca_ktory_maszynista_juz_podal()
    {
        // Ingerencja idzie TYLKO w stronę mocniejszego hamowania. Gdyby ochrona
        // wstawiała swój ułamek zamiast brać większy z dwóch, maszynista hamujący
        // pełnym hamulcem dostałby przy ostrzeżeniu hamulec SŁABSZY — czyli ochrona
        // przyspieszałaby skład, którego ma pilnować.
        var passed = Decision(ProtectionAction.ServiceIntervention, 0.55)
            .Apply(new DriverCommand(0.0, 1.0), 1.1);

        Assert.AreEqual(1.0, passed.Brake, 0.0,
            "pełny hamulec maszynisty ma zostać pełnym, a nie spaść do połowy");
    }

    [TestMethod]
    public void Ingerencja_awaryjna_daje_pelny_hamulec_niezaleznie_od_zadania()
    {
        foreach (var demand in new[] { 0.0, 0.4, 1.3, 9.9 })
        {
            var passed = Decision(ProtectionAction.EmergencyIntervention, demand)
                .Apply(new DriverCommand(1.0, 0.0), 1.1);
            Assert.AreEqual(0.0, passed.Throttle, 0.0, $"żądanie {demand:F1} m/s²");
            Assert.AreEqual(1.0, passed.Brake, 0.0, $"żądanie {demand:F1} m/s²");
        }
    }

    [TestMethod]
    public void Zadanie_ponad_hamulec_sluzbowy_jest_widoczne_a_nie_zamiecione()
    {
        // `BrakeCommandFraction` obcina ułamek do 1,0, więc żądanie 2,00 m/s² i żądanie
        // 1,10 m/s² dają ten sam nastawnik. Obcięcie jest poprawne — polecenie kończy
        // się na pełnym hamulcu — ale gdyby to była jedyna informacja, przekroczenie
        // stałoby się niewidoczne.
        var ledwo = Decision(ProtectionAction.ServiceIntervention, 1.1);
        var ponad = Decision(ProtectionAction.ServiceIntervention, 2.0);

        Assert.AreEqual(1.0, ledwo.BrakeCommandFraction(1.1), 1e-12);
        Assert.AreEqual(1.0, ponad.BrakeCommandFraction(1.1), 1e-12);
        Assert.IsFalse(ledwo.DemandExceedsServiceBrake(1.1),
            "żądanie równe pełnemu hamulcowi jeszcze go nie przekracza");
        Assert.IsTrue(ponad.DemandExceedsServiceBrake(1.1),
            "żądanie 2,00 m/s² przy hamulcu 1,10 m/s² przekracza go i musi to powiedzieć");
    }

    [TestMethod]
    public void Apply_i_DemandExceeds_odmawiaja_niedodatniego_hamulca()
    {
        var decision = Decision(ProtectionAction.ServiceIntervention, 0.55);
        foreach (var bad in new[] { 0.0, -1.1, double.NaN, double.PositiveInfinity })
        {
            Assert.ThrowsException<ArgumentOutOfRangeException>(
                () => decision.DemandExceedsServiceBrake(bad), $"{bad}");
            Assert.ThrowsException<ArgumentOutOfRangeException>(
                () => decision.Apply(new DriverCommand(1.0, 0.0), bad), $"{bad}");
        }
    }

    private sealed class Runner
    {
        private const double StopWindowM = 5.0;
        private const double PassengerExchangeSeconds = 10.0;

        private readonly TrainController _controller = new(Model);
        private readonly BrakingPointSolver _solver = new(Model);
        private readonly RunConditions _conditions = Level();
        private readonly DoorCycle _cycle = new(PassengerExchangeSeconds);
        private readonly TrackAxis _axis;
        private readonly double _startM;
        private DriveState _state = DriveState.AtRest;
        private StationStop? _stop;
        private bool _braking;
        private long _lastRequestStep = -FixedStep.SimulationHertz;

        public Runner(string id, TrackAxis axis, int from, int to)
        {
            Id = id;
            _axis = axis;
            To = to;
            _startM = axis.Stations[from].ChainageM;
        }

        public string Id { get; }

        public int To { get; }

        public double FrontM => _startM + _state.DistanceM;

        public bool Done { get; private set; }

        public void Step(FixedBlockSystem system, TrainProtection protection, FixedStep step)
        {
            if (Done)
            {
                return;
            }

            var plan = system.Plan;
            var decision = protection.Supervise(system, Id, _state.SpeedMps);
            var command = Command(system, plan, decision);

            if (decision.Action != ProtectionAction.None)
            {
                command = new DriverCommand(0.0, decision.BrakeCommandFraction(_controller.ServiceBrakeMps2));
            }

            _state = _controller.Advance(_state, _conditions, command, plan.PermittedSpeedMps, step, out _);
            system.MoveTrain(Id, FrontM);

            if (_stop is null &&
                _state.SpeedMps <= 0.0 &&
                Math.Abs(FrontM - _axis.Stations[To].ChainageM) <= StopWindowM &&
                _state.Steps > 1)
            {
                _stop = new StationStop(_cycle, step);
                Assert.IsTrue(
                    protection.DoorRelease(system, Id, _state.SpeedMps, kcvAvailable: false).Released,
                    $"{Id}: drzwi mają być zwolnione po zatrzymaniu na peronie");
            }
            else if (_stop is not null && _stop.Finished)
            {
                Done = true;
            }
        }

        private DriverCommand Command(FixedBlockSystem system, SignallingPlan plan, ProtectionDecision decision)
        {
            if (_stop is not null)
            {
                return _stop.Filter(_state, DriverCommand.FullServiceBrake);
            }

            if (system.RouteOf(Id) is null && _state.SpeedMps <= 0.0)
            {
                // Bez zaryglowanej trasy skład stoi. Żądanie idzie **raz na sekundę**,
                // a nie co krok: odmowa jest normalną odpowiedzią i trafia do zapisu,
                // więc pytanie 120 razy na sekundę zalałoby strumień zdarzeń niczym.
                if (_state.Steps - _lastRequestStep >= FixedStep.SimulationHertz &&
                    plan.NextRouteFrom(FrontM) is Route next)
                {
                    _lastRequestStep = _state.Steps;
                    system.RequestRoute(next.Id, Id);
                }

                if (system.RouteOf(Id) is null)
                {
                    return DriverCommand.FullServiceBrake;
                }
            }

            var target = Math.Min(_axis.Stations[To].ChainageM, system.Authority(Id).EndChainageM);
            var remaining = target - FrontM;
            if (remaining <= 0.0)
            {
                return DriverCommand.FullServiceBrake;
            }

            if (_state.SpeedMps <= 0.0)
            {
                _braking = false;
                return DriverCommand.FullPower;
            }

            if (!_solver.TryRequiredDeceleration(_state.SpeedMps, 0.0, remaining, out var need))
            {
                return DriverCommand.FullServiceBrake;
            }

            if (!_braking && need.DecelerationMps2 < _controller.ServiceBrakeMps2)
            {
                return _state.SpeedMps < decision.PermittedSpeedMps
                    ? DriverCommand.FullPower
                    : DriverCommand.Coast;
            }

            // Ten sam serwo, co w LineRun.Drive: raz zaczęte hamowanie idzie za kinematyką
            // v²/2d, a hamulec dostaje różnicę wobec oporów i pochylenia.
            _braking = true;
            var required = _state.SpeedMps * _state.SpeedMps / (2.0 * remaining);
            var resistance = _controller.Dynamics.Resistance.ForceN(
                _conditions.MassKg, _state.SpeedMps, _conditions.Environment);
            var grade = TrainDynamics.GradeForceN(_conditions.MassKg, _conditions.GradePercent);
            var passive = (resistance + grade) / _controller.Dynamics.EffectiveMassKg(_conditions.MassKg);

            return new DriverCommand(
                0.0, Math.Clamp((required - passive) / _controller.ServiceBrakeMps2, 0.0, 1.0));
        }
    }
}
