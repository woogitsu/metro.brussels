using System;
using System.Globalization;

namespace MetroBxl.Sim.Physics;

/// <summary>Obciążenie modelowe składu.</summary>
public enum TrainLoad
{
    /// <summary>Skład pusty, ~170 t. Masa ze źródła pierwotnego STIB.</summary>
    Aw0,

    /// <summary>Modelowe obciążenie 742 × 70 kg. Nie jest to oficjalna definicja AW2.</summary>
    Aw2,
}

/// <summary>Stan szyny; wpływa wyłącznie na limit przyczepności.</summary>
public enum RailCondition
{
    /// <summary>Sucha szyna, μ = 0,25 (<c>design_model</c>).</summary>
    Dry,

    /// <summary>Mokra szyna, μ = 0,13 (<c>design_model</c>).</summary>
    Wet,
}

/// <summary>Otoczenie toru; wpływa na człon aerodynamiczny oporu ruchu.</summary>
public enum TrackEnvironment
{
    /// <summary>Tunel, c = 1,40 (<c>design_model</c>).</summary>
    Tunnel,

    /// <summary>Powierzchnia, c = 1,00 (<c>design_model</c>).</summary>
    Surface,
}

/// <summary>
/// Warunki jednego przebiegu: co jedzie, po czym i pod jakim pochyleniem.
/// Wszystko, co nie jest stanem ruchu, a wpływa na siły.
/// </summary>
public sealed class RunConditions
{
    /// <summary>Maksymalne pochylenie akceptowane przez model, w procentach.
    /// Powyżej tej wartości nie mamy ani danych o sieci, ani modelu — lepiej rzucić wyjątek
    /// niż policzyć przebieg po ścianie.</summary>
    public const double MaxAbsoluteGradePercent = 15.0;

    /// <param name="massKg">Masa rzeczywista składu.</param>
    /// <param name="gradePercent">Pochylenie w procentach; dodatnie = pod górę.</param>
    /// <param name="adhesion">Współczynnik przyczepności koło–szyna.</param>
    /// <param name="environment">Tunel albo powierzchnia.</param>
    public RunConditions(double massKg, double gradePercent, double adhesion, TrackEnvironment environment)
    {
        if (!double.IsFinite(massKg) || massKg <= 0.0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(massKg), massKg, "Masa składu musi być dodatnia i skończona.");
        }

        if (!double.IsFinite(gradePercent) || Math.Abs(gradePercent) > MaxAbsoluteGradePercent)
        {
            throw new ArgumentOutOfRangeException(
                nameof(gradePercent), gradePercent, string.Create(
                    CultureInfo.InvariantCulture,
                    $"Pochylenie musi być skończone i nie przekraczać ±{MaxAbsoluteGradePercent:R}%."));
        }

        if (!double.IsFinite(adhesion) || adhesion <= 0.0 || adhesion > 1.0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(adhesion), adhesion, "Współczynnik przyczepności musi leżeć w (0, 1].");
        }

        MassKg = massKg;
        GradePercent = gradePercent;
        Adhesion = adhesion;
        Environment = environment;
    }

    /// <summary>Warunki dla obciążenia modelowego, na poziomie, na suchej szynie, w tunelu.</summary>
    public static RunConditions Level(VehicleModel model, TrainLoad load)
    {
        ArgumentNullException.ThrowIfNull(model);
        return new RunConditions(model.MassKg(load), 0.0, model.Adhesion(RailCondition.Dry), TrackEnvironment.Tunnel);
    }

    /// <summary>Masa rzeczywista składu w kg.</summary>
    public double MassKg { get; }

    /// <summary>Pochylenie w procentach; dodatnie = pod górę.</summary>
    public double GradePercent { get; }

    /// <summary>Współczynnik przyczepności koło–szyna.</summary>
    public double Adhesion { get; }

    /// <summary>Otoczenie toru.</summary>
    public TrackEnvironment Environment { get; }

    /// <summary>Te same warunki z innym pochyleniem.</summary>
    public RunConditions WithGrade(double gradePercent) =>
        new(MassKg, gradePercent, Adhesion, Environment);

    /// <summary>Te same warunki z inną przyczepnością.</summary>
    public RunConditions WithAdhesion(double adhesion) =>
        new(MassKg, GradePercent, adhesion, Environment);

    /// <summary>Te same warunki w innym otoczeniu toru.</summary>
    public RunConditions WithEnvironment(TrackEnvironment environment) =>
        new(MassKg, GradePercent, Adhesion, environment);
}
