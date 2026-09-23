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
        Assert.IsFalse(BrakingCue.ShouldPrompt(250.0, speed, 1.0,
            DesignAssumptions.ControlNotchRatePerSecond, ServiceBrake, Solver));
        Assert.IsTrue(BrakingCue.ShouldPrompt(182.0, speed, 1.0,
            DesignAssumptions.ControlNotchRatePerSecond, ServiceBrake, Solver));
    }

    [TestMethod]
    public void Cue_is_silent_at_rest_and_after_the_stop()
    {
        Assert.IsFalse(BrakingCue.ShouldPrompt(416.0, 0.0, 0.0,
            DesignAssumptions.ControlNotchRatePerSecond, ServiceBrake, Solver));
        Assert.IsFalse(BrakingCue.ShouldPrompt(-2.0, 10.0, 0.0,
            DesignAssumptions.ControlNotchRatePerSecond, ServiceBrake, Solver));
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
}
