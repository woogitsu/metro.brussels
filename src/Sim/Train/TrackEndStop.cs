using System;

namespace MetroBxl.Sim.Train;

/// <summary>Stops a manually driven train at the last point of its traversable axis.</summary>
public static class TrackEndStop
{
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
