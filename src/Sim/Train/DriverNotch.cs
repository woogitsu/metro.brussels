using System;
using MetroBxl.Sim.Physics;

namespace MetroBxl.Sim.Train;

/// <summary>
/// Nastawnik jazdy i hamulca jako dźwignia, którą maszynista przesuwa trzymając
/// klawisz. Zamienia <see cref="DriverKeys"/> na <see cref="DriverCommand"/>
/// **raz na krok symulacji**.
///
/// <para><b>Krok, nie klatka — i to jest cała treść tej klasy.</b> Arytmetyka
/// przesuwu mieszkała do 05.09.2026 w <c>src/Game/Input/DriverInput.Poll(delta)</c>
/// i była wołana raz na KLATKĘ, z czasem klatki. Wszystkie kroki tej klatki dostawały
/// potem to samo polecenie. Zmierzone przeciw <c>src/Sim</c> (30 s trzymanego W, potem
/// 30 s trzymanego S, tempo 0,80 1/s, limit 70 km/h):</para>
///
/// <code>
///   fps        kroki      droga [m]
/// 120.00         7200     566.407284
///  60.00         7200     566.641450   Δ = +0.234166 m
///  59.94         7199     566.178225   Δ = -0.229059 m
///  30.00         7200     566.485619   Δ = +0.078335 m
/// 144.00         7199     566.502278   Δ = +0.094993 m
/// </code>
///
/// <para>Ta sama sekwencja klawiszy, pięć różnych przejazdów. Bramki tego repozytorium
/// porównują telemetrię przy progu <b>0</b>, więc rozjazd 0,23 m jest dla nich
/// nieskończony. <c>docs/01-architecture.md</c> §Determinizm mówi o tym wprost:
/// „wejścia gracza ze znacznikiem kroku, nie czasu ściennego".</para>
///
/// <para><b>Co się dzieje, gdy jedna klatka obejmuje wiele kroków — decyzja modelowa.</b>
/// Klatka obejmująca N kroków wykonuje N razy <see cref="Advance"/> z <b>tym samym</b>
/// stanem klawiszy i za każdym razem przesuwa dźwignię o <c>tempo · krok.Seconds</c>.
/// Czyli: <i>stan klawiszy jest stały w obrębie klatki, położenie nastawnika — nie</i>.</para>
///
/// <para>Dlaczego tak, a nie „jedno polecenie na całą klatkę":</para>
/// <list type="number">
/// <item><b>Klawiatura nie ma historii wewnątrz klatki.</b> Silnik daje jeden odczyt na
/// klatkę i nie istnieje żadne źródło, z którego dałoby się uczciwie wyprowadzić, że
/// klawisz puszczono w połowie. Udawanie zmiany byłoby zmyślaniem danych.</item>
/// <item><b>Dźwignia ma historię.</b> Jej położenie jest funkcją czasu SYMULACJI,
/// przez jaki klawisz był trzymany, czyli <c>liczba kroków · krok.Seconds</c>. Ta
/// liczba nie zależy od tego, jak kroki rozłożyły się na klatki — a przesuw o
/// <c>tempo · Δt_klatki</c> raz na klatkę zależy, bo wtedy o położeniu dźwigni decyduje
/// LICZBA KLATEK. To jest dokładnie ta usterka, którą mierzy tabela wyżej.</item>
/// </list>
///
/// <para>Przybite testami <c>DriverNotchTests.FrameCoveringManyStepsMovesNotchOncePerStep</c>
/// i <c>...GivesTheSameNotchRegardlessOfHowStepsSplitIntoFrames</c>.</para>
/// </summary>
public sealed class DriverNotch
{
    private readonly double _ratePerSecond;

    /// <summary>Nastawnik o zadanym tempie przesuwu.</summary>
    /// <param name="ratePerSecond">Tempo przesuwu dźwigni, część zakresu na sekundę; dodatnie i skończone.</param>
    /// <exception cref="ArgumentOutOfRangeException">Tempo nie jest dodatnią, skończoną liczbą.</exception>
    public DriverNotch(double ratePerSecond)
    {
        if (!double.IsFinite(ratePerSecond) || ratePerSecond <= 0.0)
        {
            throw new ArgumentOutOfRangeException(nameof(ratePerSecond), ratePerSecond,
                "Tempo przestawiania nastawnika musi być dodatnie.");
        }

        _ratePerSecond = ratePerSecond;
    }

    /// <summary>Tempo przesuwu dźwigni, część zakresu na sekundę.</summary>
    public double RatePerSecond => _ratePerSecond;

    /// <summary>Bieżące położenie nastawnika i hamulca.</summary>
    public DriverCommand Command { get; private set; } = DriverCommand.Coast;

    /// <summary>
    /// Przesuwa dźwignię o jeden krok symulacji i zwraca nowe położenie.
    ///
    /// <para>Pierwszeństwo klawiszy jest takie samo, jak było w <c>DriverInput.Poll</c>:
    /// ciąg, potem hamulec, potem wybieg. Ciąg zdejmuje hamulec, zanim zacznie narastać —
    /// na M7 nie ma pozycji „ciągnij i hamuj naraz" i model jej nie udaje.</para>
    ///
    /// <para><b><see cref="DriverKeys.Emergency"/> idzie PRZED wszystkimi i nie jest
    /// nowym stopniem hamowania.</b> Wynikiem jest dokładnie
    /// <see cref="DriverCommand.FullServiceBrake"/> — ta sama liczba, do której dochodzi
    /// trzymany <see cref="DriverKeys.Brake"/> po 1/<see cref="RatePerSecond"/> sekundy.
    /// Różni się wyłącznie tym, że dźwignia trafia tam OD RAZU, bez przesuwu: to jest
    /// gest maszynisty, nie osobna fizyka. Decyzja właściciela z 05.09.2026 mówi to
    /// wprost i tak samo mówi HUD — dokładanie trzeciego stopnia do
    /// <see cref="DriverCommand"/> byłoby wymyśleniem hamulca, którego rdzeń nie
    /// modeluje.</para>
    /// </summary>
    /// <param name="keys">Stan trzymanych klawiszy w tym kroku.</param>
    /// <param name="step">Krok symulacji; jego długość jest jedyną miarą czasu tutaj.</param>
    /// <returns>Położenie nastawnika po tym kroku.</returns>
    /// <exception cref="ArgumentException">Krok nie został zainicjowany.</exception>
    public DriverCommand Advance(DriverKeys keys, FixedStep step)
    {
        step.RequireValid();

        if (keys.Emergency)
        {
            Command = DriverCommand.FullServiceBrake;
            return Command;
        }

        var stepValue = _ratePerSecond * step.Seconds;
        var throttle = Command.Throttle;
        var brake = Command.Brake;

        if (keys.Power)
        {
            // The same step cannot spend its full travel twice while crossing neutral.
            var remaining = Math.Max(0.0, stepValue - brake);
            brake = Math.Max(0.0, brake - stepValue);
            if (brake <= 0.0)
            {
                throttle = Math.Min(1.0, throttle + remaining);
            }
        }
        else if (keys.Brake)
        {
            // Mirror the transition from power to braking.
            var remaining = Math.Max(0.0, stepValue - throttle);
            throttle = Math.Max(0.0, throttle - stepValue);
            if (throttle <= 0.0)
            {
                brake = Math.Min(1.0, brake + remaining);
            }
        }
        else if (keys.Coast)
        {
            throttle = Math.Max(0.0, throttle - stepValue);
            brake = Math.Max(0.0, brake - stepValue);
        }

        Command = new DriverCommand(throttle, brake).Clamped();
        return Command;
    }

    /// <summary>Ustawia położenie dźwigni wprost — do resetu i przejęcia innego składu.</summary>
    /// <param name="command">Położenie, od którego dźwignia ma iść dalej.</param>
    public void Set(DriverCommand command) => Command = command.Clamped();
}
