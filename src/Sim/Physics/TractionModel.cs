using System;

namespace MetroBxl.Sim.Physics;

/// <summary>
/// Charakterystyka trakcyjna modelu wg <c>docs/02-simulation.md</c>: stała siła
/// <c>F0</c> do punktu przejścia, potem stała moc ograniczona do mocy zainstalowanej,
/// a na końcu ograniczenie przyczepnościowe <c>F ≤ μ · m · (4/6) · g</c>.
///
/// Moc zainstalowana (2160 kW) jest <c>spec</c>. Wszystko pozostałe — F0, udział masy
/// napędzanej i μ — jest <c>design_model</c>, więc wynikowy punkt przejścia
/// (~31,24 km/h) jest pochodną modelu, a nie prędkością bazową M7.
/// </summary>
public sealed class TractionModel
{
    /// <summary>
    /// Dolne ograniczenie prędkości w mianowniku hiperboli mocy. Przy <c>v → 0</c>
    /// stała moc dawałaby nieskończoną siłę; w praktyce gałąź mocy i tak nie
    /// obowiązuje poniżej punktu przejścia, ale wartość musi być zdefiniowana,
    /// bo <see cref="ForceN"/> jest funkcją publiczną. Taka sama jak w referencji.
    /// </summary>
    public const double MinimumSpeedForPowerBranchMps = 0.01;

    private readonly double _startupForceN;
    private readonly double _installedPowerW;
    private readonly double _poweredMassFraction;

    /// <summary>Model trakcji zbudowany z parametrów pojazdu.</summary>
    public TractionModel(VehicleModel model)
    {
        ArgumentNullException.ThrowIfNull(model);
        _startupForceN = model.DesignStartupForceN;
        _installedPowerW = model.InstalledPowerW;
        _poweredMassFraction = model.DesignPoweredMassFraction;
        TransitionSpeedMps = model.DesignForcePowerTransitionSpeedMps;
    }

    /// <summary>Trakcja M7.</summary>
    public static TractionModel M7 { get; } = new(VehicleModel.M7);

    /// <summary>Prędkość przejścia siła stała → moc stała, w m/s.</summary>
    public double TransitionSpeedMps { get; }

    /// <summary>Siła dostępna z charakterystyki, jeszcze bez ograniczenia przyczepnością.</summary>
    public double CharacteristicForceN(double speedMps) =>
        speedMps <= TransitionSpeedMps
            ? _startupForceN
            : _installedPowerW / Math.Max(speedMps, MinimumSpeedForPowerBranchMps);

    /// <summary>
    /// Największa siła, jaką da się przenieść przez styk koło–szyna:
    /// <c>μ · m · (4/6) · g</c>. Udział 4/6 jest tylko parametrem tego limitu i nie
    /// opisuje układu napędu M7.
    /// </summary>
    public double AdhesionLimitN(double massKg, double adhesion) =>
        adhesion * massKg * _poweredMassFraction * Units.StandardGravityMps2;

    /// <summary>Siła pociągowa faktycznie dostępna: mniejsza z charakterystyki i z przyczepności.</summary>
    public double ForceN(double speedMps, double massKg, double adhesion) =>
        Math.Min(CharacteristicForceN(speedMps), AdhesionLimitN(massKg, adhesion));

    /// <summary>Czy przy tych warunkach siłę ogranicza przyczepność, a nie charakterystyka.</summary>
    public bool IsAdhesionLimited(double speedMps, double massKg, double adhesion) =>
        AdhesionLimitN(massKg, adhesion) < CharacteristicForceN(speedMps);
}
