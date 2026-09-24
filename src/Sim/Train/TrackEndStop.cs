using System;
using MetroBxl.Sim.Physics;

namespace MetroBxl.Sim.Train;

/// <summary>Service braking toward a terminal and the final traversable-axis guard.</summary>
public static class TrackEndStop
{
    /// <summary>
    /// Intervene on a powered terminal approach using the station autopilot's
    /// jerk-aware trigger and running brake command. The hard end clamp remains
    /// the fallback if service braking can no longer stop the train in time.
    /// </summary>
    public static DriverCommand ApproachCommand(
        DriveState state, double chainageM, double terminalStationM,
        RunConditions conditions, TrainController controller,
        BrakingPointSolver solver, double triggerMps2, DriverCommand requested,
        bool terminalSection, ref bool engaged)
    {
        ArgumentNullException.ThrowIfNull(conditions);
        ArgumentNullException.ThrowIfNull(controller);
        ArgumentNullException.ThrowIfNull(solver);

        if (!engaged)
        {
            if (!terminalSection || state.SpeedMps <= 0.0 || requested.Brake > 0.0)
                return requested;
            var remaining = terminalStationM - chainageM;
            if (remaining <= 0.0 ||
                !solver.TryRequiredDeceleration(state.SpeedMps, 0.0, remaining, out var need))
            {
                engaged = true;
                return DriverCommand.FullServiceBrake;
            }
            if (need.DecelerationMps2 < triggerMps2)
                return requested;
            engaged = true;
        }

        var distance = terminalStationM - chainageM;
        if (state.SpeedMps <= 0.0 || distance <= 0.0)
            return DriverCommand.FullServiceBrake;

        return RequiredBrake(state, distance, conditions, controller);
    }

    /// <summary>Brake already in progress: remaining distance uses v²/2d, without
    /// charging the jerk ramp a second time.</summary>
    public static DriverCommand RequiredBrake(DriveState state, double remainingM,
        RunConditions conditions, TrainController controller)
    {
        var required = state.SpeedMps * state.SpeedMps / (2.0 * remainingM);
        var resistance = controller.Dynamics.Resistance.ForceN(
            conditions.MassKg, state.SpeedMps, conditions.Environment);
        var grade = TrainDynamics.GradeForceN(conditions.MassKg, conditions.GradePercent);
        var passive = (resistance + grade) / controller.Dynamics.EffectiveMassKg(conditions.MassKg);
        return new DriverCommand(
            0.0, Math.Clamp((required - passive) / controller.ServiceBrakeMps2, 0.0, 1.0));
    }

    /// <summary>Whether the front of the train reached the traversable axis end.</summary>
    public static bool Reached(double chainageM, double axisLengthM) =>
        chainageM >= axisLengthM;

    /// <summary>Keep the train at rest on the final axis point, including on later power steps.</summary>
    public static DriveState Apply(DriveState state, double startChainageM, double axisLengthM)
    {
        if (!double.IsFinite(startChainageM) || !double.IsFinite(axisLengthM)
            || axisLengthM <= startChainageM)
        {
            throw new ArgumentOutOfRangeException(nameof(axisLengthM),
                "Track end must be finite and beyond the starting point.");
        }

        var lastDistanceM = axisLengthM - startChainageM;
        return state.DistanceM >= lastDistanceM
            ? state with { DistanceM = lastDistanceM, SpeedMps = 0.0, BrakeRateMps2 = 0.0 }
            : state;
    }
}
