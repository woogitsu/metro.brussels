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
    }
}
