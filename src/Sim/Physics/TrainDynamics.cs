using System;

namespace MetroBxl.Sim.Physics;

/// <summary>
/// Całkowanie ruchu składu przy pełnej trakcji, krokiem stałym.
///
/// Model jest wierną implementacją <c>tools/physics/reference.py</c>, razem z dwiema
/// rzeczami, które wyglądają na błąd, a są świadomym uproszczeniem modelu projektowego:
///
/// 1. Przyspieszenie liczy się od masy efektywnej (<c>m · 1,08</c>), ale opory i
///    składowa ciężaru liczą się od masy rzeczywistej. Współczynnik mas wirujących
///    opisuje bezwładność wirujących części napędu, a nie ich ciężar — masa wirująca
///    nie zwiększa nacisku na szynę ani składowej stycznej na pochyleniu.
/// 2. Przyspieszenie jest obcinane od dołu do zera. Model nie odtacza się w tył:
///    gdy siła pociągowa nie pokonuje oporów i pochylenia, skład stoi, a przebieg
///    kończy się limitem czasu. Ruch wsteczny wymagałby modelu hamulca postojowego,
///    którego w T-310 nie ma.
/// </summary>
public sealed class TrainDynamics
{
    private readonly TractionModel _traction;
    private readonly DavisResistance _resistance;
    private readonly double _effectiveMassFactor;

    /// <summary>Dynamika zbudowana z modelu pojazdu.</summary>
    public TrainDynamics(VehicleModel model)
        : this(new TractionModel(model), new DavisResistance(model), model?.DesignEffectiveMassFactor ?? 0.0)
    {
    }

    /// <summary>Dynamika ze złożonych osobno modeli składowych.</summary>
    public TrainDynamics(TractionModel traction, DavisResistance resistance, double effectiveMassFactor)
    {
        ArgumentNullException.ThrowIfNull(traction);
        ArgumentNullException.ThrowIfNull(resistance);
        if (!double.IsFinite(effectiveMassFactor) || effectiveMassFactor <= 0.0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(effectiveMassFactor), effectiveMassFactor,
                "Współczynnik mas wirujących musi być dodatni i skończony.");
        }

        _traction = traction;
        _resistance = resistance;
        _effectiveMassFactor = effectiveMassFactor;
    }

    /// <summary>Dynamika M7.</summary>
    public static TrainDynamics M7 { get; } = new(VehicleModel.M7);

    /// <summary>Model trakcji użyty przez tę dynamikę.</summary>
    public TractionModel Traction => _traction;

    /// <summary>Model oporów użyty przez tę dynamikę.</summary>
    public DavisResistance Resistance => _resistance;

    /// <summary>Współczynnik mas wirujących.</summary>
    public double EffectiveMassFactor => _effectiveMassFactor;

    /// <summary>Masa efektywna, czyli bezwładność widziana przez przyspieszenie.</summary>
    public double EffectiveMassKg(double massKg) => massKg * _effectiveMassFactor;

    /// <summary>
    /// Składowa styczna ciężaru na pochyleniu, liczona od masy rzeczywistej.
    /// Dodatnia pod górę, ujemna z góry.
    /// </summary>
    public static double GradeForceN(double massKg, double gradePercent) =>
        massKg * Units.StandardGravityMps2 * gradePercent / 100.0;

    /// <summary>Rozbicie sił dla zadanej prędkości i warunków, bez wykonywania kroku.</summary>
    public StepForces Forces(double speedMps, RunConditions conditions)
    {
        ArgumentNullException.ThrowIfNull(conditions);

        var traction = _traction.ForceN(speedMps, conditions.MassKg, conditions.Adhesion);
        var resistance = _resistance.ForceN(conditions.MassKg, speedMps, conditions.Environment);
        var grade = GradeForceN(conditions.MassKg, conditions.GradePercent);
        var net = traction - resistance - grade;
        var acceleration = Math.Max(0.0, net / EffectiveMassKg(conditions.MassKg));

        return new StepForces(traction, resistance, grade, net, acceleration);
    }

    /// <summary>
    /// Jeden krok całkowania. Prędkość jest obcinana do <paramref name="targetSpeedMps"/>,
    /// a droga liczona po prędkości z końca kroku (schemat semi-implicit) — tak samo
    /// jak w referencji.
    /// </summary>
    public TrainState Advance(
        TrainState state,
        RunConditions conditions,
        double targetSpeedMps,
        FixedStep step,
        out StepForces forces)
    {
        ArgumentNullException.ThrowIfNull(conditions);
        step.RequireValid();

        forces = Forces(state.SpeedMps, conditions);

        var speed = Math.Min(targetSpeedMps, state.SpeedMps + (forces.AccelerationMps2 * step.Seconds));
        var distance = state.DistanceM + (speed * step.Seconds);

        return new TrainState(state.Steps + 1, speed, distance);
    }
}
