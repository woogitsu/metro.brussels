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
///
/// <para><b>Dwa tryby, jedna blokada trakcji</b> (MB-08). W trybie
/// <see cref="DoorControl.Automatic"/> — jedynym, jaki istniał do 14.09.2026, i nadal
/// domyślnym — cykl rusza sam i sam się kończy. W trybie <see cref="DoorControl.Manual"/>
/// nie rusza nigdy sam: otwiera go <see cref="RequestOpen"/>, zamyka
/// <see cref="RequestClose"/>, a między jednym a drugim drzwi stoją otwarte tak długo,
/// jak chce maszynista. <b>Blokada trakcji jest w obu trybach ta sama</b> i pochodzi
/// z tego samego zdania <see cref="DoorCycle.TractionAllowed"/>: nastawnik jest zerowany
/// poza fazą <see cref="DoorPhase.Closed"/>, niezależnie od tego, kto cykl prowadzi.
/// Gracz nie dostaje więc łagodniejszej reguły niż AI — dostaje tę samą regułę
/// z innym źródłem czasu.</para>
///
/// <para><b>Czas wymiany pasażerów w trybie ręcznym nie istnieje i to jest wybór.</b>
/// <see cref="DoorCycle.PassengerExchangeSeconds"/> nie ma źródła (powód wypisany przy
/// samym <see cref="DoorCycle"/>) i w cyklu automatycznym jest założeniem scenariusza.
/// W trybie ręcznym długość fazy <see cref="DoorPhase.Open"/> podaje CZŁOWIEK — trzymając
/// drzwi otwarte — więc podstawianie tam założenia byłoby udawaniem, że wie o niej coś
/// jeszcze ktoś inny. Fazy o stałym czasie (odryglowanie, otwieranie, sygnał, zamykanie,
/// kontrola) są w obu trybach te same i brane z tych samych stałych.</para>
/// </summary>
public sealed class StationStop
{
    private readonly DoorCycle _cycle;
    private readonly FixedStep _step;
    private readonly DoorControl _control;
    private long _stepsSinceStopped = -1;
    private DoorPhase _manualPhase = DoorPhase.Closed;
    private long _manualStepsInPhase;
    private bool _closeRequested;
    private bool _manualServed;

    /// <summary>Postój z cyklem automatycznym — tryb sprzed MB-08.</summary>
    public StationStop(DoorCycle cycle, FixedStep step)
        : this(cycle, step, DoorControl.Automatic)
    {
    }

    /// <summary>Postój z zadanym cyklem drzwi, krokiem symulacji i trybem sterowania drzwiami.</summary>
    /// <param name="cycle">Cykl drzwi.</param>
    /// <param name="step">Krok symulacji.</param>
    /// <param name="control">Kto prowadzi cykl drzwi.</param>
    public StationStop(DoorCycle cycle, FixedStep step, DoorControl control)
    {
        ArgumentNullException.ThrowIfNull(cycle);
        step.RequireValid();
        if (control is not (DoorControl.Automatic or DoorControl.Manual))
        {
            throw new ArgumentOutOfRangeException(
                nameof(control), control, "Nieznany tryb sterowania drzwiami.");
        }

        _cycle = cycle;
        _step = step;
        _control = control;
    }

    /// <summary>Cykl drzwi tego postoju.</summary>
    public DoorCycle Cycle => _cycle;

    /// <summary>Kto prowadzi cykl drzwi tego postoju.</summary>
    public DoorControl Control => _control;

    /// <summary>
    /// Czy postój się rozpoczął, czyli czy skład już stanął.
    ///
    /// <para>W obu trybach znaczy TO SAMO i mierzy TĘ SAMĄ rzecz — zatrzymanie składu,
    /// a nie ruch drzwi. W trybie automatycznym jedno pociąga za sobą drugie, bo cykl
    /// rusza z zatrzymaniem; w ręcznym nie pociąga, i o to, czy drzwi się ruszyły, pyta
    /// się <see cref="Phase"/>.</para>
    /// </summary>
    public bool Started => _stepsSinceStopped >= 0;

    /// <summary>Czas od zatrzymania; ujemny znaczy „jeszcze nie stanął".</summary>
    public double SecondsSinceStopped =>
        _stepsSinceStopped < 0 ? -1.0 : _step.TimeAt(_stepsSinceStopped);

    /// <summary>
    /// Czas spędzony już w bieżącej fazie, sekundy.
    ///
    /// <para>W trybie ręcznym jest to jedyna miara długości fazy otwartej, bo tę fazę
    /// kończy polecenie, a nie stała. Autopilot dopilnowujący cudzego, ręcznie otwartego
    /// postoju czyta tę liczbę i po niej wie, kiedy zamknąć.</para>
    /// </summary>
    public double SecondsInPhase => _control == DoorControl.Manual
        ? _step.TimeAt(_manualStepsInPhase)
        : _stepsSinceStopped < 0
            ? 0.0
            : _cycle.At(SecondsSinceStopped).ElapsedInPhaseSeconds;

    /// <summary>Faza drzwi w bieżącym kroku.</summary>
    public DoorPhase Phase => _control == DoorControl.Manual
        ? _manualPhase
        : _stepsSinceStopped < 0
            ? DoorPhase.Closed
            : _cycle.At(SecondsSinceStopped).Phase;

    /// <summary>
    /// Czy postój się domknął — cykl przeszedł i trakcja jest wolna.
    ///
    /// <para>W trybie ręcznym postój domyka się dopiero po PEŁNYM cyklu: otwarciu,
    /// zamknięciu i kontroli. Postój, na którym maszynista nie otworzył drzwi, nie jest
    /// domknięty i nigdy sam się nie domknie — bo nikogo nie obsłużył. Ponowne otwarcie
    /// cofa ten stan, tak samo jak pierwsze go nie dawało.</para>
    /// </summary>
    public bool Finished => _control == DoorControl.Manual
        ? _manualServed
        : Started && SecondsSinceStopped >= _cycle.DwellSeconds;

    /// <summary>
    /// Polecenie otwarcia drzwi. Tylko w trybie <see cref="DoorControl.Manual"/>.
    ///
    /// <para><b>Odmowa jest wynikiem, nie wyjątkiem.</b> Naciśnięcie klawisza w złej
    /// chwili jest zwykłym zdarzeniem w grze i ma dostać zdanie na ekranie, a nie
    /// przerwać przebieg.</para>
    /// </summary>
    /// <param name="state">Stan składu; rozstrzyga o odmowie „w ruchu".</param>
    /// <returns>Przyjęcie albo odmowa z powodem.</returns>
    public DoorRequestResult RequestOpen(DriveState state)
    {
        if (_control != DoorControl.Manual)
        {
            return DoorRequestResult.Refused(DoorRefusal.AutomaticControl);
        }

        if (state.SpeedMps > 0.0)
        {
            return DoorRequestResult.Refused(DoorRefusal.TrainMoving);
        }

        if (_manualPhase != DoorPhase.Closed)
        {
            return DoorRequestResult.Refused(DoorRefusal.DoorsAlreadyOpen);
        }

        _manualServed = false;
        _closeRequested = false;
        EnterManualPhase(DoorPhase.Unlocking);
        return DoorRequestResult.Accepted;
    }

    /// <summary>
    /// Polecenie zamknięcia drzwi. Tylko w trybie <see cref="DoorControl.Manual"/>
    /// i tylko przy drzwiach OTWARTYCH.
    ///
    /// <para>Zamknięcia nie da się zakolejkować w trakcie otwierania i jest to decyzja,
    /// nie brak: skrzydła w ruchu zawracane w połowie drogi byłyby nowym zachowaniem
    /// mechanizmu, o którym <c>docs/02-simulation.md</c> nie mówi nic. Fazy stałe idą
    /// więc do końca, a maszynista zamyka drzwi otwarte.</para>
    /// </summary>
    /// <returns>Przyjęcie albo odmowa z powodem.</returns>
    public DoorRequestResult RequestClose()
    {
        if (_control != DoorControl.Manual)
        {
            return DoorRequestResult.Refused(DoorRefusal.AutomaticControl);
        }

        if (_manualPhase != DoorPhase.Open)
        {
            return DoorRequestResult.Refused(DoorRefusal.DoorsNotOpen);
        }

        _closeRequested = true;
        return DoorRequestResult.Accepted;
    }

    /// <summary>
    /// Jeden krok postoju. Zwraca polecenie, które wolno podać kontrolerowi.
    ///
    /// Dopóki cykl trwa, nastawnik jest zerowany niezależnie od tego, co podał
    /// maszynista — to jest cała blokada jazdy z <c>docs/02-simulation.md</c>.
    /// Hamulec **nie** jest zerowany: skład ma stać, a nie toczyć się przy otwartych
    /// drzwiach.
    ///
    /// <para><b>Licznik zatrzymania idzie w OBU trybach, a cykl ręczny idzie niezależnie
    /// od niego.</b> Wcześniejsza wersja wracała z tej metody wprost, gdy skład jeszcze
    /// się toczył; wynik był ten sam, bo przy niezerowej prędkości cykl automatyczny nie
    /// ruszył, faza jest <see cref="DoorPhase.Closed"/>, a trakcja wolna. Dla cyklu
    /// ręcznego ten sam skrót byłby jednak usterką: drzwi otwarte na składzie, który
    /// się STOCZYŁ, zamarłyby w fazie otwartej i nie doszły do kontroli zamknięcia,
    /// czyli ruch zdejmowałby cykl zamiast go dopilnować.</para>
    /// </summary>
    /// <param name="state">Stan składu przed krokiem.</param>
    /// <param name="requested">Polecenie maszynisty.</param>
    /// <returns>Polecenie po blokadzie.</returns>
    public DriverCommand Filter(DriveState state, DriverCommand requested)
    {
        if (_stepsSinceStopped < 0)
        {
            if (state.SpeedMps <= 0.0)
            {
                _stepsSinceStopped = 0;
            }
        }
        else
        {
            _stepsSinceStopped++;
        }

        if (_control == DoorControl.Manual)
        {
            AdvanceManual();
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

    /// <summary>Faza po zadanej w cyklu ręcznym. Faza otwarta nie ma następnej z czasu.</summary>
    private static DoorPhase NextManualPhase(DoorPhase phase) => phase switch
    {
        DoorPhase.Unlocking => DoorPhase.Opening,
        DoorPhase.Opening => DoorPhase.Open,
        DoorPhase.ClosingWarning => DoorPhase.Closing,
        DoorPhase.Closing => DoorPhase.Checking,
        DoorPhase.Checking => DoorPhase.Closed,
        _ => throw new ArgumentOutOfRangeException(
            nameof(phase), phase, "Ta faza nie kończy się z upływem czasu."),
    };

    /// <summary>
    /// Posuwa cykl ręczny o jeden krok.
    ///
    /// <para>Faza <see cref="DoorPhase.Open"/> jest jedyną, która nie ma własnej długości:
    /// wychodzi się z niej WYŁĄCZNIE przyjętym <see cref="RequestClose"/>. Pozostałe idą
    /// po stałych z <see cref="DoorCycle"/> i licznik każdej startuje od zera, więc długość
    /// fazy jest całkowitą liczbą kroków symulacji, a nie resztą po poprzedniej.</para>
    /// </summary>
    private void AdvanceManual()
    {
        if (_manualPhase == DoorPhase.Closed)
        {
            return;
        }

        _manualStepsInPhase++;

        if (_manualPhase == DoorPhase.Open)
        {
            if (_closeRequested)
            {
                _closeRequested = false;
                EnterManualPhase(DoorPhase.ClosingWarning);
            }

            return;
        }

        if (_step.TimeAt(_manualStepsInPhase) >= _cycle.PhaseSeconds(_manualPhase))
        {
            EnterManualPhase(NextManualPhase(_manualPhase));
        }
    }

    private void EnterManualPhase(DoorPhase phase)
    {
        _manualPhase = phase;
        _manualStepsInPhase = 0;
        if (phase == DoorPhase.Closed)
        {
            _manualServed = true;
        }
    }

    /// <inheritdoc/>
    /// <remarks>Zagnieżdżony literał niesie kulturę sam: formatuje się, zanim zewnętrzny
    /// <c>string.Create</c> go zobaczy (23.09.2026, 6.D365 — na kulturze pl-PL stało tu
    /// „0,24 s").</remarks>
    public override string ToString() => string.Create(
        CultureInfo.InvariantCulture,
        $"postój ({(_control == DoorControl.Manual ? "ręczny" : "automatyczny")}): " +
        $"{(Started ? string.Create(CultureInfo.InvariantCulture, $"{SecondsSinceStopped:F2} s, faza {Phase}") : "jeszcze w ruchu")}, " +
        $"pełny cykl {_cycle.DwellSeconds:F1} s");
}
