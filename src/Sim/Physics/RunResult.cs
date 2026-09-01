using System.Globalization;

namespace MetroBxl.Sim.Physics;

/// <summary>Powód zakończenia przebiegu.</summary>
public enum RunOutcome
{
    /// <summary>Osiągnięto prędkość docelową (rozruch) albo postój (hamowanie).</summary>
    TargetReached,

    /// <summary>Przebieg przerwał limit czasu — model utknął, np. na zbyt stromym pochyleniu.</summary>
    TimeLimit,
}

/// <summary>
/// Wynik jednego przebiegu. Czas jest wyliczony z liczby kroków, nie zsumowany,
/// więc dwa identyczne scenariusze dają identyczny czas co do bitu.
/// </summary>
public sealed class RunResult
{
    internal RunResult(
        long steps,
        FixedStep step,
        double distanceM,
        double finalSpeedMps,
        RunOutcome outcome,
        EnergyAccount? energy,
        SpeedProfile profile)
    {
        Steps = steps;
        Step = step;
        DistanceM = distanceM;
        FinalSpeedMps = finalSpeedMps;
        Outcome = outcome;
        Energy = energy;
        Profile = profile;
    }

    /// <summary>Liczba wykonanych kroków symulacji.</summary>
    public long Steps { get; }

    /// <summary>Krok czasowy przebiegu.</summary>
    public FixedStep Step { get; }

    /// <summary>Czas przebiegu w sekundach.</summary>
    public double TimeSeconds => Step.TimeAt(Steps);

    /// <summary>Droga przebyta w metrach.</summary>
    public double DistanceM { get; }

    /// <summary>Prędkość na końcu przebiegu, w m/s.</summary>
    public double FinalSpeedMps { get; }

    /// <summary>Prędkość na końcu przebiegu, w km/h.</summary>
    public double FinalSpeedKmh => Units.MpsToKmh(FinalSpeedMps);

    /// <summary>Powód zakończenia.</summary>
    public RunOutcome Outcome { get; }

    /// <summary>Czy przebieg dobiegł do celu, zamiast wpaść w limit czasu.</summary>
    public bool ReachedTarget => Outcome == RunOutcome.TargetReached;

    /// <summary>
    /// Bilans energii. <c>null</c> dla przebiegów kinematycznych, w których model nie
    /// zna sił — nie ma z czego policzyć pracy, a zero byłoby kłamstwem.
    /// </summary>
    public EnergyAccount? Energy { get; }

    /// <summary>Profil prędkości; pusty, jeśli przebieg nie był próbkowany.</summary>
    public SpeedProfile Profile { get; }

    /// <inheritdoc/>
    public override string ToString() => string.Create(
        CultureInfo.InvariantCulture,
        $"{Outcome}: t = {TimeSeconds:F1} s, s = {DistanceM:F1} m, v = {FinalSpeedKmh:F2} km/h");
}
