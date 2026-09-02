using System;
using System.Globalization;

namespace MetroBxl.Sim.Physics;

/// <summary>
/// Zamiana nierównego czasu klatki na całkowitą liczbę kroków rdzenia, z resztą
/// przenoszoną dalej. Czysta arytmetyka: bez silnika, bez stanu symulacji.
/// </summary>
/// <remarks>
/// <para><b>Dlaczego to jest w rdzeniu, a nie w scenie.</b> <c>docs/01-architecture.md</c>
/// mówi, że <c>src/Game/</c> jest warstwą Godota <i>bez logiki</i>. Akumulator jest
/// logiką — decyduje, ile razy wykona się krok symulacji — a mieszkał jako prywatne
/// pole i prywatna metoda węzła <c>Node3D</c>, więc nie dawał się dotknąć żadnym
/// testem jednostkowym.</para>
/// <para><b>Issue #106.</b> Audyt mutacyjny: mutacje <c>FirstRun.cs:340-343</c> i
/// <c>:353</c> — w tym podmiana „120 kroków na klatkę" na „1 krok na klatkę" —
/// PRZEŻYWAŁY przy zielonym CI. Powód jest subtelny i wart zapamiętania: telemetria
/// próbkuje się po <c>_state.Steps</c>, czyli po liczniku kroków symulacji, a nie po
/// czasie ściennym. Wolniejszy przebieg produkuje więc DOKŁADNIE ten sam plik CSV,
/// tylko dłużej — porównanie z rdzeniem wychodzi identyczne co do bajtu i bramka
/// parytetu nie ma czego wykryć. Zepsuty byłby wyłącznie ruch na ekranie, którego
/// żadna bramka nie ogląda.</para>
/// <para>Reszta jest przenoszona, a nie odrzucana: przy 60 kl./s i kroku 1/120 s
/// każda klatka to dokładnie 2 kroki, ale przy 59,94 kl./s albo przy klatce dłuższej
/// od pozostałych odrzucanie reszty gubiłoby czas i przebieg dryfowałby wobec rdzenia.</para>
/// </remarks>
public sealed class StepAccumulator
{
    private readonly FixedStep _step;
    private double _carry;

    public StepAccumulator(FixedStep step)
    {
        step.RequireValid();
        _step = step;
    }

    /// <summary>Nierozliczona reszta czasu w sekundach. Zawsze w [0, <c>step.Seconds</c>).</summary>
    public double CarrySeconds => _carry;

    /// <summary>Ile kroków wykonano od utworzenia. Licznik, nie suma przyrostów.</summary>
    public long TotalSteps { get; private set; }

    /// <summary>
    /// Ile pełnych kroków mieści się w tej klatce razem z przeniesioną resztą.
    /// Czas niedodatni, NaN i nieskończoność dają zero kroków i nie ruszają reszty —
    /// Godot potrafi podać <c>delta</c> równą zeru w pierwszej klatce.
    /// </summary>
    public long StepsForFrame(double seconds)
    {
        if (!double.IsFinite(seconds) || seconds <= 0.0)
        {
            return 0;
        }

        _carry += seconds;
        var steps = (long)(_carry / _step.Seconds);
        if (steps <= 0)
        {
            return 0;
        }

        _carry -= steps * _step.Seconds;
        if (_carry < 0.0)
        {
            // Odejmowanie w zmiennoprzecinkowych potrafi zejść minimalnie poniżej zera.
            // Ujemna reszta opóźniłaby następny krok o cały krok, więc jest przycinana.
            _carry = 0.0;
        }

        TotalSteps += steps;
        return steps;
    }

    /// <summary>
    /// Zeruje resztę bez zerowania licznika. Wołane, gdy przebieg się skończył —
    /// niedokończona reszta nie ma się przenieść na następny przebieg.
    /// </summary>
    public void DropCarry() => _carry = 0.0;

    public override string ToString() => string.Create(
        CultureInfo.InvariantCulture,
        $"StepAccumulator(kroki={TotalSteps}, reszta={_carry:R} s)");
}
