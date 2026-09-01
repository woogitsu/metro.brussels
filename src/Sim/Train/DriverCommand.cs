using System;
using System.Globalization;

namespace MetroBxl.Sim.Train;

/// <summary>
/// Położenie nastawnika jazdy i hamulca w jednym kroku symulacji.
///
/// Obie wartości są w [0, 1] i są **poleceniem maszynisty**, a nie siłą. Przełożenie
/// polecenia na siłę należy do <see cref="TrainController"/>, żeby warstwa wejścia
/// (klawiatura, dżojstik, autopilot) nie musiała wiedzieć nic o fizyce.
///
/// Hamulec ma pierwszeństwo: przy <see cref="Brake"/> większym od zera trakcja jest
/// zerowana. Jednoczesne ciągnięcie i hamowanie nie jest stanem, który maszynista może
/// osiągnąć na M7, i nie ma powodu, żeby model go dopuszczał.
/// </summary>
/// <param name="Throttle">Nastawnik jazdy, 0 = wybieg, 1 = pełna trakcja.</param>
/// <param name="Brake">Hamulec służbowy, 0 = odpuszczony, 1 = pełne hamowanie służbowe.</param>
public readonly record struct DriverCommand(double Throttle, double Brake)
{
    /// <summary>Wybieg: bez trakcji i bez hamulca.</summary>
    public static DriverCommand Coast => new(0.0, 0.0);

    /// <summary>Pełna trakcja.</summary>
    public static DriverCommand FullPower => new(1.0, 0.0);

    /// <summary>Pełne hamowanie służbowe.</summary>
    public static DriverCommand FullServiceBrake => new(0.0, 1.0);

    /// <summary>Skuteczny nastawnik jazdy po pierwszeństwie hamulca.</summary>
    public double EffectiveThrottle => Brake > 0.0 ? 0.0 : Throttle;

    /// <summary>Polecenie po obcięciu obu wartości do [0, 1]. NaN jest odrzucane.</summary>
    public DriverCommand Clamped()
    {
        if (!double.IsFinite(Throttle) || !double.IsFinite(Brake))
        {
            throw new ArgumentOutOfRangeException(
                nameof(Throttle), $"{Throttle};{Brake}", "Nastawnik i hamulec muszą być skończone.");
        }

        return new DriverCommand(Math.Clamp(Throttle, 0.0, 1.0), Math.Clamp(Brake, 0.0, 1.0));
    }

    /// <inheritdoc/>
    public override string ToString() => string.Create(
        CultureInfo.InvariantCulture, $"throttle {Throttle:F2}, brake {Brake:F2}");
}
