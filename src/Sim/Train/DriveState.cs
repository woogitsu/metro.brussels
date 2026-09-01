using System.Globalization;
using MetroBxl.Sim.Physics;

namespace MetroBxl.Sim.Train;

/// <summary>
/// Stan prowadzonego składu. To <see cref="TrainState"/> plus jedno pole, którego
/// przebieg z T-310 nie potrzebował: aktualne opóźnienie hamulca.
///
/// Opóźnienie musi być w stanie, a nie liczone od nowa w każdym kroku, bo model
/// hamowania z <c>docs/02-simulation.md</c> ma ograniczenie zrywu — narastanie
/// hamowania zależy od tego, ile hamulca było krok wcześniej. Trzymanie go poza
/// stanem odbierałoby przebiegowi determinizm przy zapisie i odtworzeniu.
/// </summary>
/// <param name="Steps">Liczba wykonanych kroków symulacji.</param>
/// <param name="SpeedMps">Prędkość w m/s.</param>
/// <param name="DistanceM">Droga przebyta od początku przebiegu, w metrach.</param>
/// <param name="BrakeRateMps2">Aktualne opóźnienie hamulca, nieujemne.</param>
public readonly record struct DriveState(long Steps, double SpeedMps, double DistanceM, double BrakeRateMps2)
{
    /// <summary>Postój na początku odcinka, z odpuszczonym hamulcem.</summary>
    public static DriveState AtRest => new(0, 0.0, 0.0, 0.0);

    /// <summary>Ten sam stan widziany przez rdzeń fizyki z T-310.</summary>
    public TrainState Motion => new(Steps, SpeedMps, DistanceM);

    /// <summary>Prędkość w km/h — do raportów, nie do obliczeń.</summary>
    public double SpeedKmh => Units.MpsToKmh(SpeedMps);

    /// <summary>Czas od początku przebiegu przy zadanym kroku.</summary>
    public double TimeSeconds(FixedStep step) => step.TimeAt(Steps);

    /// <inheritdoc/>
    public override string ToString() => string.Create(
        CultureInfo.InvariantCulture,
        $"step {Steps}: v = {SpeedMps:F3} m/s, s = {DistanceM:F3} m, b = {BrakeRateMps2:F3} m/s²");
}
