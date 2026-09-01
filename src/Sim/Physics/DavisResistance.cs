using System;

namespace MetroBxl.Sim.Physics;

/// <summary>
/// Opory ruchu wg <c>docs/02-simulation.md</c>:
/// <c>r = a + b·v + c_coef·c·v²</c> w kgf na tonę, przy <c>v</c> w km/h,
/// gdzie <c>c = 1,40</c> w tunelu i <c>1,00</c> na powierzchni.
///
/// Wszystkie współczynniki są <c>design_model</c> do kalibracji i nie pochodzą
/// od CAF ani STIB. Kolejność działań jest taka sama jak w
/// <c>tools/physics/reference.py</c> — przy liczbach zmiennoprzecinkowych
/// kolejność jest częścią wyniku, nie stylem zapisu.
/// </summary>
public sealed class DavisResistance
{
    private readonly double _a;
    private readonly double _b;
    private readonly double _c;
    private readonly double _tunnelMultiplier;
    private readonly double _surfaceMultiplier;

    /// <summary>Model oporów zbudowany ze współczynników modelu pojazdu.</summary>
    public DavisResistance(VehicleModel model)
    {
        ArgumentNullException.ThrowIfNull(model);
        _a = model.DesignDavisA;
        _b = model.DesignDavisB;
        _c = model.DesignDavisC;
        _tunnelMultiplier = model.DesignTunnelResistanceMultiplier;
        _surfaceMultiplier = model.DesignSurfaceResistanceMultiplier;
    }

    /// <summary>Opory dla M7.</summary>
    public static DavisResistance M7 { get; } = new(VehicleModel.M7);

    /// <summary>Mnożnik członu aerodynamicznego dla otoczenia toru.</summary>
    public double Multiplier(TrackEnvironment environment) => environment switch
    {
        TrackEnvironment.Tunnel => _tunnelMultiplier,
        TrackEnvironment.Surface => _surfaceMultiplier,
        _ => throw new ArgumentOutOfRangeException(nameof(environment), environment, "Nieznane otoczenie toru."),
    };

    /// <summary>Opór jednostkowy w kgf na tonę przy prędkości w km/h.</summary>
    public double SpecificResistanceKgfPerTonne(double speedKmh, TrackEnvironment environment)
    {
        var c = Multiplier(environment);
        return _a + (_b * speedKmh) + (_c * c * speedKmh * speedKmh);
    }

    /// <summary>Siła oporu ruchu w niutonach. Zawsze przeciwna do kierunku jazdy.</summary>
    public double ForceN(double massKg, double speedMps, TrackEnvironment environment)
    {
        var speedKmh = Units.MpsToKmh(speedMps);
        var r = SpecificResistanceKgfPerTonne(speedKmh, environment);
        return r * (massKg / 1000.0) * Units.StandardGravityMps2;
    }
}
