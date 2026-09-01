using System;
using System.Collections.Generic;
using System.Globalization;

namespace MetroBxl.Sim.Physics;

/// <summary>Jedna próbka profilu prędkości.</summary>
/// <param name="Steps">Numer kroku, w którym pobrano próbkę.</param>
/// <param name="TimeSeconds">Czas = <c>Steps · dt</c>.</param>
/// <param name="SpeedMps">Prędkość w m/s.</param>
/// <param name="DistanceM">Droga od początku przebiegu.</param>
public readonly record struct SpeedSample(long Steps, double TimeSeconds, double SpeedMps, double DistanceM)
{
    /// <summary>Prędkość w km/h — do raportów.</summary>
    public double SpeedKmh => Units.MpsToKmh(SpeedMps);

    /// <inheritdoc/>
    public override string ToString() => string.Create(
        CultureInfo.InvariantCulture,
        $"{TimeSeconds:F3} s  {SpeedKmh:F2} km/h  {DistanceM:F2} m");
}

/// <summary>
/// Profil prędkości przebiegu: prędkość i droga w funkcji czasu, spróbkowane co
/// <see cref="SampleEverySteps"/> kroków. Próbkowanie jest wyłącznie obserwacją —
/// nie wolno mu zmienić wyniku przebiegu i pilnuje tego osobny test.
/// </summary>
public sealed class SpeedProfile
{
    private readonly List<SpeedSample> _samples;

    internal SpeedProfile(int sampleEverySteps, List<SpeedSample> samples)
    {
        SampleEverySteps = sampleEverySteps;
        _samples = samples;
    }

    /// <summary>Profil pusty — przebieg bez próbkowania.</summary>
    public static SpeedProfile Empty { get; } = new(0, new List<SpeedSample>());

    /// <summary>Co ile kroków pobierano próbkę; 0 oznacza brak próbkowania.</summary>
    public int SampleEverySteps { get; }

    /// <summary>Próbki w kolejności rosnącego czasu.</summary>
    public IReadOnlyList<SpeedSample> Samples => _samples;

    /// <summary>Najwyższa zarejestrowana prędkość, w m/s.</summary>
    public double PeakSpeedMps
    {
        get
        {
            var peak = 0.0;
            foreach (var sample in _samples)
            {
                if (sample.SpeedMps > peak)
                {
                    peak = sample.SpeedMps;
                }
            }

            return peak;
        }
    }

    /// <summary>
    /// Pierwsza próbka, w której prędkość osiągnęła zadany próg. <c>null</c>, jeśli
    /// przebieg nigdy tego progu nie dosięgnął.
    /// </summary>
    public SpeedSample? FirstAtLeast(double speedMps)
    {
        foreach (var sample in _samples)
        {
            if (sample.SpeedMps >= speedMps)
            {
                return sample;
            }
        }

        return null;
    }

    internal static List<SpeedSample> NewBuffer(int sampleEverySteps)
    {
        if (sampleEverySteps < 0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(sampleEverySteps), sampleEverySteps, "Odstęp próbkowania nie może być ujemny.");
        }

        return new List<SpeedSample>();
    }
}
