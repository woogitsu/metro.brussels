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
/// SCENARIUSZE jazdy w trybie <c>classic_2026</c>: hamowanie na żądanie ATP i dwa
/// składy na rzeczywistej osi pakietu A.
///
/// <para>To jest miejsce, w którym T-313 spotyka się z T-311 i T-312: krzywa hamowania
/// jest **ta sama**, którą prowadzi się skład, a blokada drzwi wisi na tym samym
/// warunku zatrzymania, co cykl drzwi.</para>
///
/// <para><b>Czego tu już nie ma.</b> Testy samej klasy <c>TrainProtection</c> —
/// krzywa dopuszczalna, progi ingerencji, strażnicy argumentów, drzwi i KCV,
/// <c>ProtectionDecision.Apply</c> — przeniosły się 05.09.2026 do
/// <c>TrainProtectionTests</c>. Powód jest zmierzony, a nie porządkowy: rozsypane
/// po scenariuszach dawały tej klasie najgorsze pokrycie mutacyjne z całej piątki
/// rdzenia, bo scenariusz jedzie po środku dziedziny i nie zagląda w jej brzegi.</para>
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
