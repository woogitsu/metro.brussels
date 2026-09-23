using System;
using MetroBxl.Sim.Physics;
using MetroBxl.Sim.Train;

namespace MetroBxl.Game.UI;

/// <summary>Advisory brake cue for a manually driven station approach.</summary>
public static class BrakingCue
{
    /// <summary>Small allowance for reading and reacting to the cue, in seconds.</summary>
    public const double ReactionLeadSeconds = 0.5;

    /// <summary>
    /// The core solver covers the brake's physical jerk. Clearing the current power
    /// notch takes additional time before the driver's brake command can take effect.
    /// This is a display hint only; it never changes the train command.
    /// </summary>
    public static double AdvisoryDistanceM(
        double speedMps, double throttle, double notchRatePerSecond,
        double serviceBrakeMps2, BrakingPointSolver solver)
    {
        ArgumentNullException.ThrowIfNull(solver);
        if (!double.IsFinite(speedMps) || speedMps < 0.0)
            throw new ArgumentOutOfRangeException(nameof(speedMps));
        if (!double.IsFinite(throttle) || throttle < 0.0 || throttle > 1.0)
            throw new ArgumentOutOfRangeException(nameof(throttle));
        if (!double.IsFinite(notchRatePerSecond) || notchRatePerSecond <= 0.0)
            throw new ArgumentOutOfRangeException(nameof(notchRatePerSecond));
        if (!double.IsFinite(serviceBrakeMps2) || serviceBrakeMps2 <= 0.0)
            throw new ArgumentOutOfRangeException(nameof(serviceBrakeMps2));
        if (speedMps == 0.0)
            return 0.0;

        var braking = solver.Solve(speedMps, 0.0, serviceBrakeMps2).DistanceM;
        var leadSeconds = throttle / notchRatePerSecond + ReactionLeadSeconds;
        return braking + speedMps * leadSeconds;
    }

    /// <summary>True when a moving train is close enough to advise braking now.</summary>
    public static bool ShouldPrompt(
        double distanceToStopM, double speedMps, double throttle, double brake,
        double notchRatePerSecond, double serviceBrakeMps2, BrakingPointSolver solver) =>
        double.IsFinite(distanceToStopM) && distanceToStopM > 0.0 && speedMps > 0.5 &&
        brake <= 0.0 &&
        distanceToStopM <= AdvisoryDistanceM(
            speedMps, throttle, notchRatePerSecond, serviceBrakeMps2, solver);

    /// <summary>The line HUD advises only the train currently driven by the player.</summary>
    public static bool ShouldPromptOnLine(
        bool driverControls, DriverCommand command, double distanceToStopM,
        double speedMps, double notchRatePerSecond, double serviceBrakeMps2,
        BrakingPointSolver solver) =>
        driverControls && ShouldPrompt(
            distanceToStopM, speedMps, command.Throttle, command.Brake,
            notchRatePerSecond, serviceBrakeMps2, solver);
}
