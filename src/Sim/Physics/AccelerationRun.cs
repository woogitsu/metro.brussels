using System;
using System.Collections.Generic;
using System.Globalization;

namespace MetroBxl.Sim.Physics;

/// <summary>
/// Rozruch przy pełnej trakcji do zadanej prędkości. Odpowiednik <c>sim_accel</c>
/// z <c>tools/physics/reference.py</c>: ta sama kolejność działań, ten sam krok
/// stały i ten sam limit czasu, więc wynik ma być tą samą liczbą, a nie liczbą podobną.
/// </summary>
public sealed class AccelerationRun
{
    /// <summary>
    /// Limit czasu przebiegu. To bezpiecznik pętli, a nie parametr pojazdu: chroni przed
    /// nieskończonym przebiegiem, gdy siła pociągowa nie pokonuje oporów i pochylenia.
    /// Wartość jest ta sama co w referencji.
    /// </summary>
    public const double DefaultTimeLimitSeconds = 300.0;

    private readonly TrainDynamics _dynamics;

    /// <summary>Rozruch dla zadanego modelu pojazdu.</summary>
    public AccelerationRun(VehicleModel model)
    {
        ArgumentNullException.ThrowIfNull(model);
        Model = model;
        _dynamics = new TrainDynamics(model);
    }

    /// <summary>Rozruch M7.</summary>
    public static AccelerationRun M7 { get; } = new(VehicleModel.M7);

    /// <summary>Model pojazdu użyty przez przebieg.</summary>
    public VehicleModel Model { get; }

    /// <summary>Dynamika użyta przez przebieg.</summary>
    public TrainDynamics Dynamics => _dynamics;

    /// <summary>
    /// Rozpędzanie od postoju do <paramref name="targetSpeedKmh"/>.
    /// </summary>
    /// <param name="conditions">Masa, pochylenie, przyczepność i otoczenie toru.</param>
    /// <param name="targetSpeedKmh">Prędkość docelowa; musi mieścić się w (0, Vmax modelu].</param>
    /// <param name="step">Krok całkowania; domyślnie krok rdzenia 1/120 s.</param>
    /// <param name="sampleEverySteps">Co ile kroków zapisać próbkę profilu; 0 wyłącza próbkowanie.</param>
    /// <param name="timeLimitSeconds">Bezpiecznik pętli.</param>
    public RunResult ToSpeed(
        RunConditions conditions,
        double targetSpeedKmh,
        FixedStep step = default,
        int sampleEverySteps = 0,
        double timeLimitSeconds = DefaultTimeLimitSeconds)
    {
        ArgumentNullException.ThrowIfNull(conditions);

        if (step == default)
        {
            step = FixedStep.Simulation;
        }

        step.RequireValid();
        RequireTargetInRange(targetSpeedKmh);

        if (sampleEverySteps < 0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(sampleEverySteps), sampleEverySteps, "Odstęp próbkowania nie może być ujemny.");
        }

        var target = Units.KmhToMps(targetSpeedKmh);
        var maxSteps = step.StepsWithin(timeLimitSeconds);
        var effectiveMass = _dynamics.EffectiveMassKg(conditions.MassKg);

        var state = TrainState.AtRest;
        var tractionWork = 0.0;
        var resistanceWork = 0.0;
        var gradeWork = 0.0;
        var discretization = 0.0;
        var clamped = 0.0;

        var samples = SpeedProfile.NewBuffer(sampleEverySteps);
        if (sampleEverySteps > 0)
        {
            samples.Add(new SpeedSample(0, 0.0, 0.0, 0.0));
        }

        while (state.SpeedMps < target && state.Steps < maxSteps)
        {
            var previousSpeed = state.SpeedMps;
            state = _dynamics.Advance(state, conditions, target, step, out var forces);

            // Praca liczona po prędkości z końca kroku — tą samą prędkością, którą
            // referencja całkuje drogę. Dzięki temu bilans energii i droga opisują
            // ten sam przebieg, a nie dwa różne.
            var travelled = state.SpeedMps * step.Seconds;
            tractionWork += forces.TractionN * travelled;
            resistanceWork += forces.ResistanceN * travelled;
            gradeWork += forces.GradeN * travelled;

            var deltaSpeed = state.SpeedMps - previousSpeed;
            discretization += 0.5 * effectiveMass * deltaSpeed * deltaSpeed;

            // Ile z siły wypadkowej model wyrzucił, obcinając przyrost prędkości —
            // przy dojściu do prędkości docelowej i przy zakazie ujemnego przyspieszenia.
            clamped += (forces.NetN - (effectiveMass * deltaSpeed / step.Seconds)) * travelled;

            if (sampleEverySteps > 0 && state.Steps % sampleEverySteps == 0)
            {
                samples.Add(new SpeedSample(state.Steps, step.TimeAt(state.Steps), state.SpeedMps, state.DistanceM));
            }
        }

        if (sampleEverySteps > 0 && (samples.Count == 0 || samples[^1].Steps != state.Steps))
        {
            samples.Add(new SpeedSample(state.Steps, step.TimeAt(state.Steps), state.SpeedMps, state.DistanceM));
        }

        var energy = new EnergyAccount(
            tractionWork,
            resistanceWork,
            gradeWork,
            0.5 * effectiveMass * state.SpeedMps * state.SpeedMps,
            discretization,
            clamped);

        return new RunResult(
            state.Steps,
            step,
            state.DistanceM,
            state.SpeedMps,
            state.SpeedMps >= target ? RunOutcome.TargetReached : RunOutcome.TimeLimit,
            energy,
            sampleEverySteps > 0 ? new SpeedProfile(sampleEverySteps, samples) : SpeedProfile.Empty);
    }

    private void RequireTargetInRange(double targetSpeedKmh)
    {
        if (!double.IsFinite(targetSpeedKmh) || targetSpeedKmh <= 0.0 || targetSpeedKmh > Model.DesignMaxSpeedKmh)
        {
            throw new ArgumentOutOfRangeException(
                nameof(targetSpeedKmh), targetSpeedKmh, string.Create(
                    CultureInfo.InvariantCulture,
                    $"Prędkość docelowa musi leżeć w (0, {Model.DesignMaxSpeedKmh:R}] km/h."));
        }
    }
}
