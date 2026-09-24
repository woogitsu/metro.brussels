using System;
using MetroBxl.Game;
using MetroBxl.Game.UI;
using MetroBxl.Sim.Physics;
using MetroBxl.Sim.Train;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace MetroBxl.Game.Tests;

/// <summary>The advisory cue follows the actual M7 brake model and driver notch.</summary>
[TestClass]
public sealed class BrakingCueTests
{
    private static readonly BrakingPointSolver Solver = new(VehicleModel.M7);
    private static readonly double ServiceBrake = new TrainController(VehicleModel.M7).ServiceBrakeMps2;

    [TestMethod]
    public void First_station_cue_appears_near_measured_braking_point()
    {
        // The committed manual replay changes W to S near 182 m to Beekkant.
        var speed = 63.86431008242766 / 3.6;
        var distance = BrakingCue.AdvisoryDistanceM(
            speed, 1.0, DesignAssumptions.ControlNotchRatePerSecond,
            ServiceBrake, Solver);

        Assert.IsTrue(distance > 185.0 && distance < 190.0,
            $"M7 brake cue drifted away from the measured first stop: {distance:F2} m");
        Assert.IsFalse(BrakingCue.ShouldPrompt(250.0, speed, 1.0, 0.0,
            DesignAssumptions.ControlNotchRatePerSecond, ServiceBrake, Solver),
            "at 250 m the first stop is still outside the advisory distance");
        Assert.IsTrue(BrakingCue.ShouldPrompt(182.0, speed, 1.0, 0.0,
            DesignAssumptions.ControlNotchRatePerSecond, ServiceBrake, Solver),
            "the measured brake change near 182 m must be within the cue window");
    }

    [TestMethod]
    public void Cue_is_silent_at_rest_and_after_the_stop()
    {
        Assert.IsFalse(BrakingCue.ShouldPrompt(416.0, 0.0, 0.0, 0.0,
            DesignAssumptions.ControlNotchRatePerSecond, ServiceBrake, Solver),
            "a stationary train must not receive a brake cue");
        Assert.IsFalse(BrakingCue.ShouldPrompt(-2.0, 10.0, 0.0, 0.0,
            DesignAssumptions.ControlNotchRatePerSecond, ServiceBrake, Solver),
            "a passed stop must not receive a brake cue");
    }

    [TestMethod]
    public void Power_notch_needs_earlier_cue_than_coasting()
    {
        var powered = BrakingCue.AdvisoryDistanceM(18.0, 1.0,
            DesignAssumptions.ControlNotchRatePerSecond, ServiceBrake, Solver);
        var coasting = BrakingCue.AdvisoryDistanceM(18.0, 0.0,
            DesignAssumptions.ControlNotchRatePerSecond, ServiceBrake, Solver);
        Assert.AreEqual(22.5, powered - coasting, 1e-9,
            "Clearing full power takes 1.25 s at the actual notch rate");
    }

    [TestMethod]
    public void Line_cue_needs_driver_control_and_disappears_when_braking_begins()
    {
        var speed = 18.0;
        var command = DriverCommand.FullPower;

        Assert.IsFalse(BrakingCue.ShouldPromptOnLine(
            false, command, 150.0, speed,
            DesignAssumptions.ControlNotchRatePerSecond, ServiceBrake, Solver),
            "autonomous trains must not tell the player to brake");
        Assert.IsTrue(BrakingCue.ShouldPromptOnLine(
            true, command, 150.0, speed,
            DesignAssumptions.ControlNotchRatePerSecond, ServiceBrake, Solver),
            "the same train must show the cue after manual takeover");
        Assert.IsFalse(BrakingCue.ShouldPromptOnLine(
            true, new DriverCommand(0.0, 0.01), 150.0, speed,
            DesignAssumptions.ControlNotchRatePerSecond, ServiceBrake, Solver),
            "the cue must disappear as soon as the brake command begins");
        Assert.IsFalse(BrakingCue.ShouldPrompt(
            150.0, speed, 0.0, 0.01,
            DesignAssumptions.ControlNotchRatePerSecond, ServiceBrake, Solver),
            "the manual single-train HUD follows the same brake rule");

        var rate = DesignAssumptions.ControlNotchRatePerSecond;
        var brakeAt = BrakingCue.AdvisoryDistanceM(speed, 0.0, rate, ServiceBrake, Solver);
        var prepareAt = BrakingCue.PreparationDistanceM(speed, 0.0, rate, ServiceBrake, Solver);
        Assert.IsTrue(prepareAt > brakeAt, "coasting also needs reading time");
        Assert.IsFalse(BrakingCue.ShouldPrepare(prepareAt + 0.001, speed, 0.0, 0.0,
            rate, ServiceBrake, Solver), "no preparation before the band");
        Assert.IsTrue(BrakingCue.ShouldPrepare(prepareAt, speed, 0.0, 0.0,
            rate, ServiceBrake, Solver), "preparation starts at its threshold");
        Assert.IsFalse(BrakingCue.ShouldPrompt(prepareAt, speed, 0.0, 0.0,
            rate, ServiceBrake, Solver), "the two messages cannot overlap");
        Assert.IsFalse(BrakingCue.ShouldPrepare(brakeAt, speed, 0.0, 0.0,
            rate, ServiceBrake, Solver), "preparation ends at the braking threshold");
        Assert.IsTrue(BrakingCue.ShouldPrompt(brakeAt, speed, 0.0, 0.0,
            rate, ServiceBrake, Solver), "braking starts at its threshold");
        Assert.IsFalse(BrakingCue.ShouldPrepare(prepareAt, speed, 0.0, 0.01,
            rate, ServiceBrake, Solver), "both messages disappear after brake onset");
        Assert.IsFalse(BrakingCue.ShouldPrepareOnLine(false, DriverCommand.Coast,
            prepareAt, speed, rate, ServiceBrake, Solver), "autopilot has no driver cue");
        Assert.IsTrue(BrakingCue.ShouldPrepareOnLine(true, DriverCommand.Coast,
            prepareAt, speed, rate, ServiceBrake, Solver), "player gets preparation");
        Assert.IsFalse(BrakingCue.ShouldPrepareOnLine(true, new DriverCommand(0.0, 0.01),
            prepareAt, speed, rate, ServiceBrake, Solver), "line cue also clears on brake");

        // The step of S input is earlier than the physical Brake > 0 step when
        // clearing full power. Replay and keyboard both write the accepted keys
        // into FirstRun._activeKeys before StationLine is composed.
        var notch = new DriverNotch(rate);
        notch.Set(DriverCommand.FullPower);
        var clearing = notch.Advance(DriverKeys.Braking, FixedStep.Simulation);
        Assert.IsTrue(clearing.Throttle > 0.0 && clearing.Brake == 0.0,
            "the test must exercise the notch-clearing interval");
        Assert.IsTrue(BrakingCue.MayAdvise(DriverKeys.Powering, DriverCommand.FullPower),
            "a powered approach still displays the advisory before S is pressed");
        Assert.IsFalse(BrakingCue.MayAdvise(DriverKeys.Braking, clearing),
            "S must clear the cue on its first accepted step, before Brake rises");
        Assert.IsFalse(BrakingCue.MayAdvise(DriverKeys.EmergencyBraking,
            DriverCommand.FullServiceBrake), "Space also clears the cue");
        Assert.IsFalse(BrakingCue.MayAdvise(DriverKeys.None,
            new DriverCommand(0.0, 0.01)), "an already applied brake keeps it hidden");
    }

    [TestMethod]
    public void Preparation_warns_before_a_late_full_service_stop()
    {
        var model = VehicleModel.M7;
        var controller = new TrainController(model);
        var conditions = RunConditions.Level(model, TrainLoad.Aw2);
        var step = FixedStep.Simulation;
        var rate = DesignAssumptions.ControlNotchRatePerSecond;
        var oldCueWasLate = false;

        foreach (var speedKmh in new[] { 10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 72.0, 80.0 })
        foreach (var throttle in new[] { 0.0, 0.5, 1.0 })
        {
            var speedMps = speedKmh / 3.6;
            var notch = new DriverNotch(rate);
            notch.Set(new DriverCommand(throttle, 0.0));
            var state = new DriveState(0, speedMps, 0.0, 0.0);

            // Read for 0.8 s without changing the present notch, then hold S.
            for (var i = 0; i < 96; i++)
                state = controller.Advance(state, conditions, notch.Command,
                    model.DesignMaxSpeedKmh / 3.6, step, out _);
            while (state.SpeedMps > 0.0 && state.Steps < 10000)
            {
                var command = notch.Advance(DriverKeys.Braking, step);
                state = controller.Advance(state, conditions, command,
                    model.DesignMaxSpeedKmh / 3.6, step, out _);
            }

            var oldDistance = BrakingCue.AdvisoryDistanceM(speedMps, throttle,
                rate, controller.ServiceBrakeMps2, Solver);
            var preparationDistance = BrakingCue.PreparationDistanceM(speedMps, throttle,
                rate, controller.ServiceBrakeMps2, Solver);
            oldCueWasLate |= state.DistanceM > oldDistance + 5.0;
            Assert.IsTrue(state.DistanceM <= preparationDistance + 5.0,
                $"{speedKmh:F0} km/h, throttle {throttle:F1}: warning is too late by "
                + $"{state.DistanceM - preparationDistance:F3} m");
        }

        Assert.IsTrue(oldCueWasLate, "the measured old failure keeps this test meaningful");
    }

    [TestMethod]
    public void Coasting_does_not_make_preparation_disappear_on_the_real_Beekkant_approach()
    {
        var axis = MetroBxl.Sim.Line.TrackAxis.FromJson(
            MetroBxl.Tests.Shared.KorzenRepozytorium.Tresc("data", "track", "L1_A.json"));
        var stationM = axis.Stations[1].ChainageM;
        var model = VehicleModel.M7;
        var controller = new TrainController(model);
        var conditions = RunConditions.Level(model, TrainLoad.Aw2);
        var notch = new DriverNotch(DesignAssumptions.ControlNotchRatePerSecond);
        var state = DriveState.AtRest;
        var memory = new BrakingCueMemory();
        var firstPrepare = -1L;
        var firstNow = -1L;

        for (var i = 0; i < 4000; i++)
        {
            var keys = state.Steps <= 2701 ? DriverKeys.Powering : DriverKeys.Coasting;
            var command = notch.Advance(keys, FixedStep.Simulation);
            state = controller.Advance(state, conditions, command,
                model.DesignMaxSpeedKmh / 3.6, FixedStep.Simulation, out _);
            var phase = memory.Update("player", stationM, true, keys, command,
                stationM - 94.0 - state.DistanceM, state.SpeedMps,
                DesignAssumptions.ControlNotchRatePerSecond,
                controller.ServiceBrakeMps2, Solver);
            if (phase == BrakingCueStage.Prepare && firstPrepare < 0)
                firstPrepare = state.Steps;
            if (firstPrepare >= 0 && firstNow < 0)
                Assert.AreNotEqual(BrakingCueStage.None, phase,
                    $"warning disappeared during coast at step {state.Steps}");
            if (phase == BrakingCueStage.Now)
            {
                firstNow = state.Steps;
                break;
            }
        }

        Assert.AreEqual(2701L, firstPrepare,
            "preparation must appear at the measured Beekkant replay step");
        Assert.IsTrue(firstNow > firstPrepare,
            "braking phase must follow the preparation phase");
    }

    [TestMethod]
    public void Warning_memory_is_scoped_to_station_train_and_driver()
    {
        var memory = new BrakingCueMemory();
        var speed = 60.0 / 3.6;
        var prepareAt = BrakingCue.PreparationDistanceM(speed, 1.0, 0.8, ServiceBrake, Solver);
        BrakingCueStage Phase(string train, double station, bool driver, DriverKeys keys,
            DriverCommand command, double distance) =>
            memory.Update(train, station, driver, keys, command, distance, speed,
                0.8, ServiceBrake, Solver);

        Assert.AreEqual(BrakingCueStage.Prepare,
            Phase("train-A", 509.73, true, DriverKeys.Powering,
                DriverCommand.FullPower, prepareAt),
            "the first approach creates a preparation phase");
        Assert.AreEqual(BrakingCueStage.Prepare,
            Phase("train-A", 509.73, true, DriverKeys.Coasting,
                DriverCommand.Coast, prepareAt + 20.0), "coast retains the displayed phase");
        Assert.AreEqual(BrakingCueStage.Now,
            Phase("train-A", 509.73, true, DriverKeys.Powering,
                DriverCommand.FullPower,
                BrakingCue.AdvisoryDistanceM(speed, 1.0, 0.8, ServiceBrake, Solver)),
            "the current train advances to the braking phase");
        Assert.AreEqual(BrakingCueStage.Now,
            Phase("train-A", 509.73, true, DriverKeys.Coasting,
                DriverCommand.Coast, prepareAt + 20.0), "NOW cannot regress to PREP");
        Assert.AreEqual(BrakingCueStage.None,
            Phase("train-A", 1500.0, true, DriverKeys.Coasting,
                DriverCommand.Coast, prepareAt + 20.0), "next station starts fresh");
        Assert.AreEqual(BrakingCueStage.None,
            Phase("train-B", 509.73, true, DriverKeys.Coasting,
                DriverCommand.Coast, prepareAt + 20.0), "next observed train starts fresh");
        Assert.AreEqual(BrakingCueStage.None,
            Phase("train-A", 509.73, false, DriverKeys.Powering,
                DriverCommand.FullPower, prepareAt), "autopilot has no cue");
        Assert.AreEqual(BrakingCueStage.Prepare,
            Phase("train-A", 509.73, true, DriverKeys.Powering,
                DriverCommand.FullPower, prepareAt), "driver can receive a fresh cue");
        Assert.AreEqual(BrakingCueStage.None,
            Phase("train-A", 509.73, true, DriverKeys.Braking,
                DriverCommand.FullPower, prepareAt), "S hides it immediately");
        Assert.AreEqual(BrakingCueStage.None,
            Phase("train-A", 509.73, true, DriverKeys.EmergencyBraking,
                DriverCommand.FullServiceBrake, prepareAt), "E hides it immediately");
        memory.Reset();
        Assert.AreEqual(BrakingCueStage.None,
            Phase("train-A", 509.73, true, DriverKeys.Coasting,
                DriverCommand.Coast, prepareAt + 20.0), "restart clears memory");
    }
}
