namespace MetroBxl.Sim.Physics;

/// <summary>
/// Jednostki wg <c>docs/04-conventions.md</c>: prędkość m/s, masa kg, czas s, pochylenie %.
/// Konwersje są wydzielone, żeby nigdzie w rdzeniu nie pojawiło się gołe 3,6.
/// </summary>
public static class Units
{
    /// <summary>
    /// Przyspieszenie normalne (CGPM 1901, ISO 80000-3). To stała fizyczna, a nie
    /// parametr pojazdu — nie ma jej w rejestrze M7 i nie ma statusu <c>design_model</c>.
    /// Referencja <c>tools/physics/reference.py</c> używa tej samej wartości.
    /// </summary>
    public const double StandardGravityMps2 = 9.80665;

    /// <summary>
    /// km/h → m/s. Dzielenie przez 3,6, dokładnie jak w referencji; mnożenie przez
    /// wyliczone 1/3,6 dałoby inny ostatni bit mantysy i rozjazd parytetu.
    /// </summary>
    public static double KmhToMps(double kmh) => kmh / 3.6;

    /// <summary>m/s → km/h.</summary>
    public static double MpsToKmh(double mps) => mps * 3.6;
}
