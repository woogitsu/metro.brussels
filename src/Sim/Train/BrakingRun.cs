using System;
using System.Collections.Generic;
using System.Globalization;
using MetroBxl.Sim.Physics;

namespace MetroBxl.Sim.Train;

/// <summary>Wynik przebiegu hamowania z oporami ruchu.</summary>
public sealed class BrakingRunResult
{
    internal BrakingRunResult(
        long steps,
        FixedStep step,
        double distanceM,
        double finalSpeedMps,
        RunOutcome outcome,
        double demandedDecelerationMps2,
        double appliedDecelerationMps2,
        bool adhesionLimited,
        BrakingEnergyAccount energy,
        SpeedProfile profile)
    {
        Steps = steps;
        Step = step;
        DistanceM = distanceM;
        FinalSpeedMps = finalSpeedMps;
        Outcome = outcome;
        DemandedDecelerationMps2 = demandedDecelerationMps2;
        AppliedDecelerationMps2 = appliedDecelerationMps2;
        AdhesionLimited = adhesionLimited;
        Energy = energy;
        Profile = profile;
    }

    /// <summary>Liczba wykonanych kroków symulacji.</summary>
    public long Steps { get; }

    /// <summary>Krok czasowy przebiegu.</summary>
    public FixedStep Step { get; }

    /// <summary>Czas przebiegu; wyliczony z liczby kroków, nie zsumowany.</summary>
    public double TimeSeconds => Step.TimeAt(Steps);

    /// <summary>Droga hamowania w metrach.</summary>
    public double DistanceM { get; }

    /// <summary>Prędkość na końcu przebiegu, w m/s.</summary>
    public double FinalSpeedMps { get; }

    /// <summary>Prędkość na końcu przebiegu, w km/h.</summary>
    public double FinalSpeedKmh => Units.MpsToKmh(FinalSpeedMps);

    /// <summary>Powód zakończenia.</summary>
    public RunOutcome Outcome { get; }

    /// <summary>Czy przebieg dobiegł do prędkości docelowej.</summary>
    public bool ReachedTarget => Outcome == RunOutcome.TargetReached;

    /// <summary>Opóźnienie zadane przez maszynistę albo przez krzywą.</summary>
    public double DemandedDecelerationMps2 { get; }

    /// <summary>Opóźnienie naprawdę użyte, po obcięciu sufitem przyczepnościowym.</summary>
    public double AppliedDecelerationMps2 { get; }

    /// <summary>Czy sufit przyczepnościowy obciął żądanie.</summary>
    public bool AdhesionLimited { get; }

    /// <summary>Bilans energii przebiegu — druga droga do tej samej drogi hamowania.</summary>
    public BrakingEnergyAccount Energy { get; }

    /// <summary>Profil prędkości; pusty, jeśli przebieg nie był próbkowany.</summary>
    public SpeedProfile Profile { get; }

    /// <inheritdoc/>
    public override string ToString() => string.Create(
        CultureInfo.InvariantCulture,
        $"{Outcome}: b = {AppliedDecelerationMps2:F4} m/s², s = {DistanceM:F3} m, t = {TimeSeconds:F3} s" +
        $"{(AdhesionLimited ? " (obcięte przyczepnością)" : string.Empty)}");
}

/// <summary>
/// Hamowanie policzone **z oporami ruchu, pochyleniem i sufitem przyczepnościowym** —
/// w odróżnieniu od czysto kinematycznego <see cref="ServiceBrakingRun"/> z T-310,
/// który zadaje opóźnienie i nic poza tym nie zna.
///
/// <para><b>To nie jest trzecia fizyka.</b> Cały krok wykonuje
/// <see cref="TrainController"/> z T-400 — ten sam obiekt, który prowadzi przejazd
/// w Godocie i w <c>src/Sim.Runner</c>. Hamowanie z zadanym opóźnieniem <c>b</c> to
/// po prostu kontroler zbudowany z <c>b</c> jako pełnym hamulcem służbowym, prowadzony
/// poleceniem <see cref="DriverCommand.FullServiceBrake"/>. Dzięki temu droga hamowania
/// w tablicy referencyjnej i droga hamowania w grze są liczone **tym samym kodem**, a
/// nie dwoma podobnymi. Z tego samego powodu klasa leży w <c>Sim/Train</c>, a nie
/// w <c>Sim/Physics</c>: sam sufit przyczepnościowy i solver punktu hamowania są czystą
/// fizyką i zostały w <c>Physics</c>, ale przebieg wymaga kontrolera, a zależność
/// <c>Physics → Train</c> byłaby odwróceniem warstw.</para>
///
/// <para><b>Sufit przyczepnościowy jest opcjonalny i tak ma zostać.</b> Udziału osi
/// hamowanych M7 nie ma w żadnym źródle (<see cref="BrakingAssumptions"/>), więc
/// wpisanie jednego wariantu na stałe w kontroler byłoby wyborem liczby bez pokrycia
/// za właściciela repo. Kto chce sufit, podaje go jawnie.</para>
/// </summary>
public sealed class BrakingRun
{
    /// <summary>Bezpiecznik pętli. Ta sama wartość co w <see cref="ServiceBrakingRun"/>.</summary>
    public const double DefaultTimeLimitSeconds = 120.0;

    private readonly VehicleModel _model;

    /// <summary>Przebieg hamowania dla zadanego modelu pojazdu.</summary>
    public BrakingRun(VehicleModel model)
    {
        ArgumentNullException.ThrowIfNull(model);
        _model = model;
    }

    /// <summary>Hamowanie M7.</summary>
    public static BrakingRun M7 { get; } = new(VehicleModel.M7);

    /// <summary>Model pojazdu użyty przez przebieg.</summary>
    public VehicleModel Model => _model;

    /// <summary>Hamowanie do zatrzymania.</summary>
    public BrakingRunResult ToStop(
        RunConditions conditions,
        double startSpeedKmh,
        double decelerationMps2,
        BrakeAdhesionLimit? adhesionLimit = null,
        FixedStep step = default,
        int sampleEverySteps = 0,
        double timeLimitSeconds = DefaultTimeLimitSeconds) =>
        ToSpeed(conditions, startSpeedKmh, 0.0, decelerationMps2, adhesionLimit, step, sampleEverySteps, timeLimitSeconds);

    /// <summary>
    /// Hamowanie z prędkości początkowej do docelowej.
    /// </summary>
    /// <param name="conditions">Masa, pochylenie, przyczepność i otoczenie toru.</param>
    /// <param name="startSpeedKmh">Prędkość początkowa; musi mieścić się w (0, Vmax modelu].</param>
    /// <param name="targetSpeedKmh">Prędkość docelowa; 0 dla zatrzymania.</param>
    /// <param name="decelerationMps2">Żądane opóźnienie na odcinku stałym.</param>
    /// <param name="adhesionLimit">
    /// Sufit przyczepnościowy; <c>null</c> oznacza brak obcięcia — czyli zachowanie
    /// modelu z T-400, w którym hamulec jest poleceniem niezależnym od przyczepności.
    /// </param>
    /// <param name="step">Krok całkowania; domyślnie krok rdzenia 1/120 s.</param>
    /// <param name="sampleEverySteps">Co ile kroków zapisać próbkę profilu; 0 wyłącza próbkowanie.</param>
    /// <param name="timeLimitSeconds">Bezpiecznik pętli.</param>
    public BrakingRunResult ToSpeed(
        RunConditions conditions,
        double startSpeedKmh,
        double targetSpeedKmh,
        double decelerationMps2,
        BrakeAdhesionLimit? adhesionLimit = null,
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

        if (!double.IsFinite(startSpeedKmh) || startSpeedKmh <= 0.0 || startSpeedKmh > _model.DesignMaxSpeedKmh)
        {
            throw new ArgumentOutOfRangeException(
                nameof(startSpeedKmh), startSpeedKmh, string.Create(
                    CultureInfo.InvariantCulture,
                    $"Prędkość początkowa musi leżeć w (0, {_model.DesignMaxSpeedKmh:R}] km/h."));
        }

        if (!double.IsFinite(targetSpeedKmh) || targetSpeedKmh < 0.0 || targetSpeedKmh >= startSpeedKmh)
        {
            throw new ArgumentOutOfRangeException(
                nameof(targetSpeedKmh), targetSpeedKmh,
                "Prędkość docelowa musi być nieujemna i mniejsza od początkowej.");
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

        var applied = adhesionLimit is null
            ? decelerationMps2
            : adhesionLimit.AchievableDecelerationMps2(decelerationMps2, conditions.Adhesion);
        var limited = adhesionLimit is not null && adhesionLimit.IsAdhesionLimited(decelerationMps2, conditions.Adhesion);

        var controller = new TrainController(new TrainDynamics(_model), applied, _model.DesignJerkMps3);
        var effectiveMass = controller.Dynamics.EffectiveMassKg(conditions.MassKg);
        var startMps = Units.KmhToMps(startSpeedKmh);
        var targetMps = Units.KmhToMps(targetSpeedKmh);
        var maxSteps = step.StepsWithin(timeLimitSeconds);

        var state = new DriveState(0, startMps, 0.0, 0.0);
        var resistanceWork = 0.0;
        var brakeWork = 0.0;
        var gradeWork = 0.0;
        var discretization = 0.0;

        var samples = SpeedProfile.NewBuffer(sampleEverySteps);
        if (sampleEverySteps > 0)
        {
            samples.Add(new SpeedSample(0, 0.0, state.SpeedMps, 0.0));
        }

        while (state.SpeedMps > targetMps && state.Steps < maxSteps)
        {
            var before = state;

            // Bez ograniczenia prędkości, i to jest świadome. Pierwsza wersja podawała
            // tu prędkość początkową i **zepsuło to bilans energii na pochyleniu −3 %**:
            // zanim hamulec narośnie zrywem, składowa ciężaru przewyższa opóźnienie
            // hamulca, więc skład przez chwilę przyspiesza — a obcięcie do prędkości
            // startowej zjadało tę część ruchu i bilans przestawał się domykać
            // (reszta względna 3·10⁻³ zamiast 10⁻¹⁶). Ograniczenie prędkości jest
            // sprawą sygnalizacji, a nie hamowania; przebieg hamowania ma pokazać,
            // co robi skład, a nie co wolno mu robić.
            state = controller.Advance(
                before, conditions, DriverCommand.FullServiceBrake, double.MaxValue, step, out var forces);

            var travelled = state.DistanceM - before.DistanceM;
            resistanceWork += forces.ResistanceN * travelled;
            brakeWork += effectiveMass * state.BrakeRateMps2 * travelled;
            gradeWork += forces.GradeN * travelled;

            var deltaSpeed = before.SpeedMps - state.SpeedMps;
            discretization += 0.5 * effectiveMass * deltaSpeed * deltaSpeed;

            if (sampleEverySteps > 0 && state.Steps % sampleEverySteps == 0)
            {
                samples.Add(new SpeedSample(state.Steps, step.TimeAt(state.Steps), state.SpeedMps, state.DistanceM));
            }
        }

        if (sampleEverySteps > 0 && (samples.Count == 0 || samples[^1].Steps != state.Steps))
        {
            samples.Add(new SpeedSample(state.Steps, step.TimeAt(state.Steps), state.SpeedMps, state.DistanceM));
        }

        var kineticLoss = 0.5 * effectiveMass * ((startMps * startMps) - (state.SpeedMps * state.SpeedMps));
        var energy = new BrakingEnergyAccount(kineticLoss, resistanceWork, brakeWork, gradeWork, discretization);

        return new BrakingRunResult(
            state.Steps,
            step,
            state.DistanceM,
            state.SpeedMps,
            state.SpeedMps <= targetMps ? RunOutcome.TargetReached : RunOutcome.TimeLimit,
            decelerationMps2,
            applied,
            limited,
            energy,
            sampleEverySteps > 0 ? new SpeedProfile(sampleEverySteps, samples) : SpeedProfile.Empty);
    }

    /// <summary>
    /// Tablica referencyjna: dla każdej prędkości początkowej droga hamowania bez
    /// oporów (model kinematyczny T-310), z oporami w tunelu i z oporami na powierzchni.
    /// Kolejność wierszy jest kolejnością wejścia, więc wyjście jest deterministyczne.
    /// </summary>
    public IReadOnlyList<BrakingReferenceRow> ReferenceTable(
        RunConditions conditions,
        IReadOnlyList<double> startSpeedsKmh,
        double decelerationMps2,
        FixedStep step = default)
    {
        ArgumentNullException.ThrowIfNull(conditions);
        ArgumentNullException.ThrowIfNull(startSpeedsKmh);

        if (step == default)
        {
            step = FixedStep.Simulation;
        }

        var rows = new List<BrakingReferenceRow>(startSpeedsKmh.Count);
        var kinematicRun = new ServiceBrakingRun(_model);
        var solver = new BrakingPointSolver(_model);
        var effectiveMass = new TrainDynamics(_model).EffectiveMassKg(conditions.MassKg);

        foreach (var speedKmh in startSpeedsKmh)
        {
            var kinematic = kinematicRun.ToStop(speedKmh, decelerationMps2, step);
            var tunnel = ToSpeed(
                conditions.WithEnvironment(TrackEnvironment.Tunnel), speedKmh, 0.0, decelerationMps2, null, step);
            var surface = ToSpeed(
                conditions.WithEnvironment(TrackEnvironment.Surface), speedKmh, 0.0, decelerationMps2, null, step);
            var closedForm = solver.Solve(Units.KmhToMps(speedKmh), 0.0, decelerationMps2);

            rows.Add(new BrakingReferenceRow(
                speedKmh,
                closedForm.DistanceM,
                kinematic.DistanceM,
                kinematic.TimeSeconds,
                tunnel.DistanceM,
                tunnel.TimeSeconds,
                surface.DistanceM,
                surface.TimeSeconds,
                tunnel.Energy.ResistanceShorteningM(effectiveMass, decelerationMps2),
                surface.Energy.ResistanceShorteningM(effectiveMass, decelerationMps2)));
        }

        return rows;
    }
}

/// <summary>Jeden wiersz tablicy referencyjnej hamowania.</summary>
/// <param name="StartSpeedKmh">Prędkość początkowa.</param>
/// <param name="ClosedFormDistanceM">Droga ze wzoru zamkniętego solvera (granica <c>dt → 0</c>, bez oporów).</param>
/// <param name="KinematicDistanceM">Droga modelu kinematycznego T-310, krokiem stałym, bez oporów.</param>
/// <param name="KinematicTimeSeconds">Czas modelu kinematycznego.</param>
/// <param name="TunnelDistanceM">Droga z oporami Davisa w tunelu (c = 1,40).</param>
/// <param name="TunnelTimeSeconds">Czas w tunelu.</param>
/// <param name="SurfaceDistanceM">Droga z oporami Davisa na powierzchni (c = 1,00).</param>
/// <param name="SurfaceTimeSeconds">Czas na powierzchni.</param>
/// <param name="TunnelShorteningFromEnergyM">Skrócenie w tunelu policzone z pracy oporów.</param>
/// <param name="SurfaceShorteningFromEnergyM">Skrócenie na powierzchni policzone z pracy oporów.</param>
public readonly record struct BrakingReferenceRow(
    double StartSpeedKmh,
    double ClosedFormDistanceM,
    double KinematicDistanceM,
    double KinematicTimeSeconds,
    double TunnelDistanceM,
    double TunnelTimeSeconds,
    double SurfaceDistanceM,
    double SurfaceTimeSeconds,
    double TunnelShorteningFromEnergyM,
    double SurfaceShorteningFromEnergyM)
{
    /// <summary>Zmierzone skrócenie drogi w tunelu wobec modelu bez oporów.</summary>
    public double TunnelShorteningM => KinematicDistanceM - TunnelDistanceM;

    /// <summary>Zmierzone skrócenie drogi na powierzchni wobec modelu bez oporów.</summary>
    public double SurfaceShorteningM => KinematicDistanceM - SurfaceDistanceM;

    /// <inheritdoc/>
    public override string ToString() => string.Create(
        CultureInfo.InvariantCulture,
        $"{StartSpeedKmh:F0} km/h: bez oporów {KinematicDistanceM:F3} m, tunel {TunnelDistanceM:F3} m, " +
        $"powierzchnia {SurfaceDistanceM:F3} m");
}
