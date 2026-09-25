using System;
using MetroBxl.Sim.Physics;
using MetroBxl.Sim.Train;

namespace MetroBxl.Game.UI;

/// <summary>Advisory brake cue for a manually driven station approach.</summary>
public static class BrakingCue
{
    /// <summary>
    /// Hide the instruction on the very step in which the driver presses S or Space.
    /// From full power, S clears the traction notch for 1.25 s before Brake becomes
    /// positive; waiting for that value would keep telling the driver to press S.
    /// </summary>
    public static bool MayAdvise(DriverKeys keys, DriverCommand command) =>
        !keys.Brake && !keys.Emergency && command.Brake <= 0.0;

    /// <summary>Small allowance for reading and reacting to the cue, in seconds.</summary>
    public const double ReactionLeadSeconds = 0.5;

    /// <summary>Extra reading time before the braking instruction appears.</summary>
    public const double PreparationLeadSeconds = 0.3;

    /// <summary>
    /// Powered approach margin measured with the M7 AW2 tunnel model at 120 Hz.
    /// Holding S after 0.8 s reaction was late by at most 10.588 m in the
    /// 10–80 km/h, 0/half/full power sweep. Together with 0.3 s extra reading
    /// time, this covers that measured overshoot. The earlier message does not
    /// promise a stop inside the station window; the driver must modulate braking.
    /// </summary>
    public const double PoweredPreparationMarginM = 8.5;

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

    /// <summary>
    /// Earlier preparation band. A coasting train still gets time to read the warning;
    /// a powered train gets additional room to clear its notch before braking.
    /// </summary>
    public static double PreparationDistanceM(
        double speedMps, double throttle, double notchRatePerSecond,
        double serviceBrakeMps2, BrakingPointSolver solver) =>
        AdvisoryDistanceM(speedMps, throttle, notchRatePerSecond, serviceBrakeMps2, solver)
        + speedMps * PreparationLeadSeconds
        + throttle * PoweredPreparationMarginM;

    /// <summary>True only between the preparation and braking thresholds.</summary>
    public static bool ShouldPrepare(
        double distanceToStopM, double speedMps, double throttle, double brake,
        double notchRatePerSecond, double serviceBrakeMps2, BrakingPointSolver solver) =>
        double.IsFinite(distanceToStopM) && distanceToStopM > 0.0 && speedMps > 0.5 &&
        brake <= 0.0 &&
        distanceToStopM > AdvisoryDistanceM(
            speedMps, throttle, notchRatePerSecond, serviceBrakeMps2, solver) &&
        distanceToStopM <= PreparationDistanceM(
            speedMps, throttle, notchRatePerSecond, serviceBrakeMps2, solver);

    /// <summary>The line HUD advises only the train currently driven by the player.</summary>
    public static bool ShouldPromptOnLine(
        bool driverControls, DriverCommand command, double distanceToStopM,
        double speedMps, double notchRatePerSecond, double serviceBrakeMps2,
        BrakingPointSolver solver) =>
        driverControls && ShouldPrompt(
            distanceToStopM, speedMps, command.Throttle, command.Brake,
            notchRatePerSecond, serviceBrakeMps2, solver);

    /// <summary>The preparation warning also belongs only to the player-controlled train.</summary>
    public static bool ShouldPrepareOnLine(
        bool driverControls, DriverCommand command, double distanceToStopM,
        double speedMps, double notchRatePerSecond, double serviceBrakeMps2,
        BrakingPointSolver solver) =>
        driverControls && ShouldPrepare(
            distanceToStopM, speedMps, command.Throttle, command.Brake,
            notchRatePerSecond, serviceBrakeMps2, solver);
}

/// <summary>The visible step of the station braking hint.</summary>
public enum BrakingCueStage
{
    /// <summary>No hint is visible.</summary>
    None,
    /// <summary>Get ready to brake.</summary>
    Prepare,
    /// <summary>Begin service braking.</summary>
    Now
}

/// <summary>Keep a warning visible as the power notch moves toward coast.</summary>
public sealed class BrakingCueMemory
{
    private (string TrainId, double StationM)? _target;
    private BrakingCueStage _phase;

    /// <summary>Forget the warning when a run restarts.</summary>
    public void Reset()
    {
        _target = null;
        _phase = BrakingCueStage.None;
    }

    /// <summary>Advance the warning for one observed train and station.</summary>
    public BrakingCueStage Update(
        string trainId, double stationM, bool driverControls, DriverKeys keys,
        DriverCommand command, double distanceM, double speedMps,
        double notchRatePerSecond, double serviceBrakeMps2, BrakingPointSolver solver)
    {
        var target = (trainId, stationM);
        if (_target != target)
        {
            _target = target;
            _phase = BrakingCueStage.None;
        }

        if (!driverControls || !double.IsFinite(distanceM) || distanceM <= 0.0 ||
            speedMps <= 0.5)
        {
            Reset();
            return BrakingCueStage.None;
        }

        if (!BrakingCue.MayAdvise(keys, command))
            return BrakingCueStage.None;

        var candidate = BrakingCue.ShouldPrompt(distanceM, speedMps,
            command.Throttle, command.Brake, notchRatePerSecond, serviceBrakeMps2, solver)
            ? BrakingCueStage.Now
            : BrakingCue.ShouldPrepare(distanceM, speedMps,
                command.Throttle, command.Brake, notchRatePerSecond, serviceBrakeMps2, solver)
                ? BrakingCueStage.Prepare : BrakingCueStage.None;
        if (candidate > _phase)
            _phase = candidate;
        return _phase;
    }
}
