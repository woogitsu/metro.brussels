using System;
using System.Globalization;

namespace MetroBxl.Sim.Physics;

/// <summary>
/// Hamowanie do zatrzymania w modelu projektowym: zadane opóźnienie z ograniczeniem
/// zrywu, narastające od zera.
///
/// <b>Ten model nie zależy od masy.</b> Nie jest to przeoczenie: w referencji
/// <c>sim_brake</c> nie przyjmuje masy w ogóle, więc AW0 i AW2 dają identyczny czas
/// i identyczną drogę. Hamowanie jest tu wielkością zadaną (opóźnienie i zryw), a nie
/// wynikiem bilansu sił, dlatego sygnatura też masy nie przyjmuje — parametr, który
/// jest po cichu ignorowany, kłamie gorzej niż jego brak.
///
/// Pełny model hamowania — udział hamulca elektrodynamicznego i pneumatycznego,
/// hamowanie awaryjne, krzywe bezpieczeństwa, wpływ masy i przyczepności — należy do
/// T-311. W T-310 hamowanie służbowe jest wyłącznie przypadkiem testowym parytetu.
/// </summary>
public sealed class ServiceBrakingRun
{
    /// <summary>Bezpiecznik pętli, ta sama wartość co w referencji.</summary>
    public const double DefaultTimeLimitSeconds = 120.0;

    /// <summary>Hamowanie dla zadanego modelu pojazdu.</summary>
    public ServiceBrakingRun(VehicleModel model)
    {
        ArgumentNullException.ThrowIfNull(model);
        Model = model;
    }

    /// <summary>Hamowanie M7.</summary>
    public static ServiceBrakingRun M7 { get; } = new(VehicleModel.M7);

    /// <summary>Model pojazdu, z którego pochodzą opóźnienia i zryw.</summary>
    public VehicleModel Model { get; }

    /// <summary>Hamowanie służbowe z prędkości początkowej do zatrzymania.</summary>
    public RunResult ToStop(
        double startSpeedKmh,
        FixedStep step = default,
        int sampleEverySteps = 0,
        double timeLimitSeconds = DefaultTimeLimitSeconds) =>
        ToStop(startSpeedKmh, Model.DesignServiceBrakeMps2, step, sampleEverySteps, timeLimitSeconds);

    /// <summary>
    /// Hamowanie z zadanym opóźnieniem docelowym. Zryw jest ograniczony wartością
    /// <c>design_model</c> z rejestru.
    /// </summary>
    /// <param name="startSpeedKmh">Prędkość początkowa; musi mieścić się w (0, Vmax modelu].</param>
    /// <param name="decelerationMps2">Docelowe opóźnienie, dodatnie.</param>
    /// <param name="step">Krok całkowania; domyślnie krok rdzenia 1/120 s.</param>
    /// <param name="sampleEverySteps">Co ile kroków zapisać próbkę profilu; 0 wyłącza próbkowanie.</param>
    /// <param name="timeLimitSeconds">Bezpiecznik pętli.</param>
    public RunResult ToStop(
        double startSpeedKmh,
        double decelerationMps2,
        FixedStep step = default,
        int sampleEverySteps = 0,
        double timeLimitSeconds = DefaultTimeLimitSeconds)
    {
        if (step == default)
        {
            step = FixedStep.Simulation;
        }

        step.RequireValid();

        if (!double.IsFinite(startSpeedKmh) || startSpeedKmh <= 0.0 || startSpeedKmh > Model.DesignMaxSpeedKmh)
        {
            throw new ArgumentOutOfRangeException(
                nameof(startSpeedKmh), startSpeedKmh, string.Create(
                    CultureInfo.InvariantCulture,
                    $"Prędkość początkowa musi leżeć w (0, {Model.DesignMaxSpeedKmh:R}] km/h."));
        }

        if (!double.IsFinite(decelerationMps2) || decelerationMps2 <= 0.0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(decelerationMps2), decelerationMps2, "Opóźnienie musi być dodatnie i skończone.");
        }

        if (sampleEverySteps < 0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(sampleEverySteps), sampleEverySteps, "Odstęp próbkowania nie może być ujemny.");
        }

        var jerk = Model.DesignJerkMps3;
        var maxSteps = step.StepsWithin(timeLimitSeconds);
        var state = new TrainState(0, Units.KmhToMps(startSpeedKmh), 0.0);
        var deceleration = 0.0;

        var samples = SpeedProfile.NewBuffer(sampleEverySteps);
        if (sampleEverySteps > 0)
        {
            samples.Add(new SpeedSample(0, 0.0, state.SpeedMps, 0.0));
        }

        while (state.SpeedMps > 0.0 && state.Steps < maxSteps)
        {
            deceleration = Math.Min(decelerationMps2, deceleration + (jerk * step.Seconds));
            var speed = Math.Max(0.0, state.SpeedMps - (deceleration * step.Seconds));
            var distance = state.DistanceM + (speed * step.Seconds);
            state = new TrainState(state.Steps + 1, speed, distance);

            if (sampleEverySteps > 0 && state.Steps % sampleEverySteps == 0)
            {
                samples.Add(new SpeedSample(state.Steps, step.TimeAt(state.Steps), state.SpeedMps, state.DistanceM));
            }
        }

        if (sampleEverySteps > 0 && (samples.Count == 0 || samples[^1].Steps != state.Steps))
        {
            samples.Add(new SpeedSample(state.Steps, step.TimeAt(state.Steps), state.SpeedMps, state.DistanceM));
        }

        return new RunResult(
            state.Steps,
            step,
            state.DistanceM,
            state.SpeedMps,
            state.SpeedMps <= 0.0 ? RunOutcome.TargetReached : RunOutcome.TimeLimit,
            // Model kinematyczny nie zna sił, więc nie ma z czego policzyć pracy.
            // Bilans energii hamowania i odzysku należy do T-311.
            energy: null,
            sampleEverySteps > 0 ? new SpeedProfile(sampleEverySteps, samples) : SpeedProfile.Empty);
    }
}
