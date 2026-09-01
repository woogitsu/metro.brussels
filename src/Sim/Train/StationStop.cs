using System;
using System.Collections.Generic;
using System.Globalization;
using MetroBxl.Sim.Physics;

namespace MetroBxl.Sim.Train;

/// <summary>
/// Postój na stacji: cykl drzwi wpięty w krok symulacji, z blokadą trakcji.
///
/// <para><b>Dlaczego to nie jest część <see cref="TrainController"/>.</b> Kontroler
/// odpowiada na pytanie „co robi skład, gdy maszynista da tyle nastawnika i tyle
/// hamulca". Postój odpowiada na inne: „czy maszynista w ogóle może dać nastawnik".
/// Wpięcie blokady do kontrolera oznaczałoby, że każdy przebieg bez stacji — w tym
/// przebieg referencyjny T-310 i przejazd T-400 — musiałby przenosić stan drzwi,
/// którego nie używa. Blokada jest więc **filtrem polecenia** przed kontrolerem,
/// a nie gałęzią w środku niego.</para>
///
/// <para><b>Zatrzymanie liczy się od PRĘDKOŚCI ZERO, nie od kilometrażu peronu.</b>
/// Drzwi otwierają się po zatrzymaniu, a nie po dojechaniu — skład, który minął
/// punkt zatrzymania i wciąż się toczy, ma drzwi zamknięte. Dlatego cykl startuje
/// od pierwszego kroku, w którym prędkość jest zerowa.</para>
/// </summary>
public sealed class StationStop
{
    private readonly DoorCycle _cycle;
    private readonly FixedStep _step;
    private long _stepsSinceStopped = -1;

    /// <summary>Postój z zadanym cyklem drzwi i krokiem symulacji.</summary>
    public StationStop(DoorCycle cycle, FixedStep step)
    {
        ArgumentNullException.ThrowIfNull(cycle);
        step.RequireValid();
        _cycle = cycle;
        _step = step;
    }

    /// <summary>Cykl drzwi tego postoju.</summary>
    public DoorCycle Cycle => _cycle;

    /// <summary>Czy postój się rozpoczął, czyli czy skład już stanął.</summary>
    public bool Started => _stepsSinceStopped >= 0;

    /// <summary>Czas od zatrzymania; ujemny znaczy „jeszcze nie stanął".</summary>
    public double SecondsSinceStopped =>
        _stepsSinceStopped < 0 ? -1.0 : _step.TimeAt(_stepsSinceStopped);

    /// <summary>Faza drzwi w bieżącym kroku.</summary>
    public DoorPhase Phase => _stepsSinceStopped < 0
        ? DoorPhase.Closed
        : _cycle.At(SecondsSinceStopped).Phase;

    /// <summary>Czy postój się domknął — cykl przeszedł i trakcja jest wolna.</summary>
    public bool Finished => Started && SecondsSinceStopped >= _cycle.DwellSeconds;

    /// <summary>
    /// Jeden krok postoju. Zwraca polecenie, które wolno podać kontrolerowi.
    ///
    /// Dopóki cykl trwa, nastawnik jest zerowany niezależnie od tego, co podał
    /// maszynista — to jest cała blokada jazdy z <c>docs/02-simulation.md</c>.
    /// Hamulec **nie** jest zerowany: skład ma stać, a nie toczyć się przy otwartych
    /// drzwiach.
    /// </summary>
    /// <param name="state">Stan składu przed krokiem.</param>
    /// <param name="requested">Polecenie maszynisty.</param>
    /// <returns>Polecenie po blokadzie.</returns>
    public DriverCommand Filter(DriveState state, DriverCommand requested)
    {
        if (_stepsSinceStopped < 0)
        {
            if (state.SpeedMps > 0.0)
            {
                return requested;
            }

            _stepsSinceStopped = 0;
        }
        else
        {
            _stepsSinceStopped++;
        }

        return DoorCycle.TractionAllowed(Phase)
            ? requested
            : requested with { Throttle = 0.0 };
    }

    /// <summary>Przebieg całego postoju bez symulacji ruchu — do tablic i testów.</summary>
    /// <param name="cycle">Cykl drzwi.</param>
    /// <param name="step">Krok symulacji.</param>
    /// <returns>Kolejne fazy z czasem ich zakończenia, w sekundach od zatrzymania.</returns>
    public static IReadOnlyList<(DoorPhase Phase, double EndsAtSeconds)> Timeline(DoorCycle cycle, FixedStep step)
    {
        ArgumentNullException.ThrowIfNull(cycle);
        step.RequireValid();
        var rows = new List<(DoorPhase, double)>();
        var elapsed = 0.0;
        foreach (var phase in DoorCycle.Sequence)
        {
            elapsed += cycle.PhaseSeconds(phase);
            rows.Add((phase, elapsed));
        }

        return rows;
    }

    /// <inheritdoc/>
    public override string ToString() => string.Create(
        CultureInfo.InvariantCulture,
        $"postój: {(Started ? $"{SecondsSinceStopped:F2} s, faza {Phase}" : "jeszcze w ruchu")}, " +
        $"pełny cykl {_cycle.DwellSeconds:F1} s");
}
