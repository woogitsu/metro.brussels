using System;
using System.Globalization;

namespace MetroBxl.Sim.Physics;

/// <summary>
/// Stały krok czasowy symulacji. <c>docs/01-architecture.md</c>: rdzeń linii działa
/// krokiem stałym 1/120 s. Czas w rdzeniu jest funkcją liczby kroków (liczby
/// całkowitej), a nie sumą przyrostów — sumowanie <c>t += dt</c> dryfuje wraz z
/// długością przebiegu, licznik kroków nie dryfuje nigdy.
/// </summary>
public readonly struct FixedStep : IEquatable<FixedStep>
{
    /// <summary>Częstotliwość rdzenia z <c>docs/01-architecture.md</c>.</summary>
    public const int SimulationHertz = 120;

    private FixedStep(double seconds, int hertz)
    {
        Seconds = seconds;
        Hertz = hertz;
    }

    /// <summary>Długość kroku w sekundach. Po poprawnej konstrukcji zawsze dodatnia i skończona.</summary>
    public double Seconds { get; }

    /// <summary>Częstotliwość w Hz, jeśli krok powstał z <see cref="FromHertz"/>; inaczej 0.</summary>
    public int Hertz { get; }

    /// <summary>Krok rdzenia symulacji: 1/120 s.</summary>
    public static FixedStep Simulation => FromHertz(SimulationHertz);

    /// <summary>Krok z częstotliwości. <paramref name="hertz"/> musi być dodatnie.</summary>
    public static FixedStep FromHertz(int hertz)
    {
        if (hertz <= 0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(hertz), hertz, "Częstotliwość kroku musi być dodatnia.");
        }

        return new FixedStep(1.0 / hertz, hertz);
    }

    /// <summary>Krok podany wprost w sekundach. Zero, wartość ujemna, NaN i nieskończoność są odrzucane.</summary>
    public static FixedStep FromSeconds(double seconds)
    {
        if (!double.IsFinite(seconds) || seconds <= 0.0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(seconds), seconds, "Krok czasowy musi być dodatnią, skończoną liczbą sekund.");
        }

        return new FixedStep(seconds, 0);
    }

    /// <summary>Czas po <paramref name="steps"/> krokach: jedno mnożenie, więc bez dryfu sumowania.</summary>
    public double TimeAt(long steps)
    {
        RequireValid();
        if (steps < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(steps), steps, "Liczba kroków nie może być ujemna.");
        }

        return steps * Seconds;
    }

    /// <summary>Liczba pełnych kroków mieszczących się w zadanym czasie.</summary>
    public long StepsWithin(double seconds)
    {
        RequireValid();
        if (!double.IsFinite(seconds) || seconds < 0.0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(seconds), seconds, "Limit czasu musi być nieujemny i skończony.");
        }

        return (long)(seconds / Seconds);
    }

    /// <summary>
    /// <c>default(FixedStep)</c> ma <see cref="Seconds"/> równe zero — strukturę w C#
    /// zawsze da się utworzyć z pominięciem konstruktora, więc każdy, kto całkuje,
    /// musi ten przypadek odrzucić jawnie. Krok zerowy to nieskończona pętla, nie „szybka symulacja".
    /// </summary>
    public void RequireValid()
    {
        if (!double.IsFinite(Seconds) || Seconds <= 0.0)
        {
            throw new ArgumentException(
                "Krok czasowy nie został zainicjowany (Seconds <= 0). Użyj FixedStep.Simulation albo FixedStep.FromSeconds.",
                nameof(FixedStep));
        }
    }

    /// <summary>
    /// Równość po <see cref="Seconds"/>, bit w bit. Krok 1/120 s zbudowany dwiema
    /// różnymi drogami jest tym samym krokiem tylko wtedy, gdy wyszła z nich ta sama
    /// liczba — porównanie z tolerancją ukryłoby dryf zegara, który ta struktura ma
    /// wykluczać.
    /// </summary>
    /// <param name="other">Krok do porównania.</param>
    /// <returns>Prawda, gdy oba kroki mają identyczną długość w sekundach.</returns>
    public bool Equals(FixedStep other) => Seconds.Equals(other.Seconds);

    /// <summary>Równość dla świata nietypowanego; wszystko, co nie jest krokiem, jest różne.</summary>
    /// <param name="obj">Dowolny obiekt, także null.</param>
    /// <returns>Prawda tylko dla <see cref="FixedStep"/> o tej samej długości.</returns>
    public override bool Equals(object? obj) => obj is FixedStep other && Equals(other);

    /// <summary>Skrót liczony z <see cref="Seconds"/>, żeby zgadzał się z <see cref="Equals(FixedStep)"/>.</summary>
    /// <returns>Skrót długości kroku.</returns>
    public override int GetHashCode() => Seconds.GetHashCode();

    /// <summary>
    /// Zapis diagnostyczny w kulturze niezmiennej i w formacie <c>R</c>, czyli
    /// odtwarzalny co do bitu. Kropka dziesiętna jest tu wymuszona celowo: log
    /// przejazdu ma wyjść identyczny na każdej maszynie.
    /// </summary>
    /// <returns>Napis postaci <c>FixedStep(0.008333333333333333 s)</c>.</returns>
    public override string ToString() =>
        string.Create(CultureInfo.InvariantCulture, $"FixedStep({Seconds:R} s)");

    /// <summary>Ta sama równość co <see cref="Equals(FixedStep)"/>.</summary>
    /// <param name="left">Lewy krok.</param>
    /// <param name="right">Prawy krok.</param>
    /// <returns>Prawda, gdy oba kroki mają identyczną długość w sekundach.</returns>
    public static bool operator ==(FixedStep left, FixedStep right) => left.Equals(right);

    /// <summary>Zaprzeczenie <see cref="op_Equality(FixedStep, FixedStep)"/>.</summary>
    /// <param name="left">Lewy krok.</param>
    /// <param name="right">Prawy krok.</param>
    /// <returns>Prawda, gdy kroki różnią się długością.</returns>
    public static bool operator !=(FixedStep left, FixedStep right) => !left.Equals(right);
}
