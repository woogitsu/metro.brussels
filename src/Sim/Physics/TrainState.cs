using System.Globalization;

namespace MetroBxl.Sim.Physics;

/// <summary>
/// Stan ruchu składu w chwili kroku <see cref="Steps"/>. Czas nie jest polem stanu:
/// wynika z licznika kroków i długości kroku, więc dwa przebiegi o tej samej liczbie
/// kroków mają identyczny czas bez względu na to, jak długo trwały naprawdę.
/// </summary>
/// <param name="Steps">Liczba wykonanych kroków symulacji.</param>
/// <param name="SpeedMps">Prędkość w m/s.</param>
/// <param name="DistanceM">Droga przebyta od początku przebiegu, w metrach.</param>
public readonly record struct TrainState(long Steps, double SpeedMps, double DistanceM)
{
    /// <summary>Stan początkowy: postój na początku odcinka.</summary>
    public static TrainState AtRest => new(0, 0.0, 0.0);

    /// <summary>Prędkość w km/h — do raportów, nie do obliczeń.</summary>
    public double SpeedKmh => Units.MpsToKmh(SpeedMps);

    /// <summary>Czas od początku przebiegu przy zadanym kroku.</summary>
    public double TimeSeconds(FixedStep step) => step.TimeAt(Steps);

    /// <inheritdoc/>
    public override string ToString() => string.Create(
        CultureInfo.InvariantCulture,
        $"step {Steps}: v = {SpeedMps:F3} m/s, s = {DistanceM:F3} m");
}

/// <summary>
/// Rozbicie sił w jednym kroku. Wartości są zapisem tego, co model naprawdę policzył,
/// i służą do kontroli bilansu energii — nie do sterowania.
/// </summary>
/// <param name="TractionN">Siła pociągowa po ograniczeniu przyczepnością.</param>
/// <param name="ResistanceN">Opory ruchu (Davis), zawsze dodatnie.</param>
/// <param name="GradeN">Składowa styczna ciężaru; dodatnia pod górę.</param>
/// <param name="NetN">Siła wypadkowa przed obcięciem ujemnego przyspieszenia.</param>
/// <param name="AccelerationMps2">Przyspieszenie użyte w kroku, po obcięciu.</param>
public readonly record struct StepForces(
    double TractionN,
    double ResistanceN,
    double GradeN,
    double NetN,
    double AccelerationMps2);
