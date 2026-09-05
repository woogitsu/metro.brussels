using System;
using System.Collections.Generic;
using System.Globalization;
using MetroBxl.Sim.Line;
using MetroBxl.Sim.Physics;

namespace MetroBxl.Sim.Train;

/// <summary>Stan obsługi najbliższej stacji — jedno pytanie, jedna odpowiedź dla widoku.</summary>
/// <param name="Name">Nazwa stacji albo puste, gdy nie ma już żadnej przed składem.</param>
/// <param name="StopId">Identyfikator przystanku z GTFS.</param>
/// <param name="ChainageM">Kilometraż punktu zatrzymania.</param>
/// <param name="DistanceM">Odległość czoła do punktu zatrzymania; ujemna, gdy minięty.</param>
/// <param name="WithinWindow">Czy czoło jest w oknie, w którym wolno otworzyć drzwi.</param>
public readonly record struct StationApproach(
    string Name,
    string StopId,
    double ChainageM,
    double DistanceM,
    bool WithinWindow)
{
    /// <summary>Czy przed składem jest jeszcze jakakolwiek stacja.</summary>
    public bool Exists => Name.Length > 0;
}

/// <summary>
/// Obsługa stacji dla składu prowadzonego RĘCZNIE: rozpoznanie zatrzymania, cykl drzwi,
/// blokada trakcji i rejestr wywołań.
///
/// <para><b>Dlaczego to nie jest <see cref="LineDrive"/>.</b> <c>LineDrive</c> jest
/// autopilotem — sam liczy polecenie z <see cref="BrakingPointSolver"/> i sam decyduje,
/// kiedy hamować. Kabina ma decydować o tym maszynistą, a mimo to potrzebuje dokładnie
/// tej samej wiedzy o stacjach. Ta klasa jest tą wiedzą bez autopilota: nie liczy ani
/// jednej siły i nie podaje ani jednego nastawnika, tylko FILTRUJE polecenie i mówi,
/// gdzie jest najbliższa stacja.</para>
///
/// <para><b>Okno zatrzymania jest DWUSTRONNE, i to jest różnica wobec autopilota.</b>
/// <c>LineDrive</c> uznaje zatrzymanie za wywołanie stacji, gdy czoło stanie w
/// <c>chainage &gt;= cel − okno</c>, bez ograniczenia z góry. Dla autopilota, który
/// staje z błędem 0,31 m, ten warunek nigdy nie wychodzi poza peron. Dla CZŁOWIEKA
/// wychodzi natychmiast: skład zatrzymany 200 m za stacją spełniałby go tak samo
/// dobrze i otworzyłby drzwi w tunelu. Tutaj wymagane jest
/// <c>|chainage − cel| &lt;= okno</c> po obu stronach.</para>
///
/// <para><b>Przejechana stacja jest przejechana na zawsze.</b> Skład nie ma biegu
/// wstecznego (<see cref="DriverCommand"/> ma nastawnik i hamulec, nie ma kierunku),
/// więc gdy czoło minie <c>cel + okno</c>, tej stacji nie da się już obsłużyć żadnym
/// późniejszym poleceniem. Kolejka przechodzi wtedy do następnej, a wywołanie ląduje
/// w <see cref="Missed"/>. Reguła jest monotoniczna — to jedyny sposób, żeby nie
/// zależała od tego, co gracz zrobi potem.</para>
///
/// <para><b>Granica okna należy do STACJI.</b> Zatrzymanie dokładnie w
/// <c>cel + okno</c> jest wywołaniem tej stacji; minięta jest dopiero od
/// <c>cel + okno + ε</c>. Wybór jest jawny, bo w tym projekcie granica bez decyzji
/// wraca potem jako pytanie (<c>docs/24</c>): „w oknie" ma znaczyć „w oknie włącznie
/// z jego brzegiem", a nie „w jego wnętrzu". Obie strony są przybite testami, osobno.</para>
///
/// <para><b><see cref="Filter"/> trzeba wołać DOKŁADNIE RAZ na krok symulacji.</b>
/// Ta sama umowa co <see cref="StationStop.Filter"/>, z tego samego powodu: licznik
/// cyklu drzwi posuwa się właśnie tam. Dwa wywołania na krok skróciłyby postój o połowę,
/// zero wywołań zawiesiłoby go na zawsze — a jedno i drugie wyglądałoby jak działający
/// cykl.</para>
/// </summary>
public sealed class StationService
{
    private readonly IReadOnlyList<AxisStation> _stations;
    private readonly DoorCycle _cycle;
    private readonly FixedStep _step;
    private readonly double _windowM;
    private readonly List<StationCall> _calls = new();
    private readonly List<AxisStation> _missed = new();

    private int _next;
    private StationStop? _stop;
    private double _departedAtSeconds;
    private double _departedFromM;
    private double _topSpeedMps;

    /// <summary>Obsługa stacji dla zadanej osi.</summary>
    /// <param name="stations">
    /// Stacje w kolejności kilometrażu. Pierwsza jest POMIJANA jako punkt startowy —
    /// tak samo jak w <see cref="LineDrive"/>, gdzie <c>_next</c> zaczyna od 1. Skład
    /// stoi na niej na początku przebiegu, więc „zatrzymanie" na niej nie jest
    /// wywołaniem stacji, tylko stanem początkowym.
    /// </param>
    /// <param name="cycle">Cykl drzwi.</param>
    /// <param name="step">Krok symulacji.</param>
    /// <param name="windowM">
    /// Połowa szerokości okna, w którym zatrzymanie liczy się jako wywołanie tej stacji.
    /// <b>Bez wartości domyślnej</b> — ta sama decyzja co w <see cref="LineRunSettings"/>:
    /// liczba bez źródła ma pochodzić z wołającego, który ją zadeklaruje jako założenie.
    /// Nie jest to dokładność zatrzymania M7; ta jest MIERZONA i wychodzi
    /// w <see cref="StationCall.StopErrorM"/>.
    /// </param>
    public StationService(
        IReadOnlyList<AxisStation> stations, DoorCycle cycle, FixedStep step, double windowM)
    {
        ArgumentNullException.ThrowIfNull(stations);
        ArgumentNullException.ThrowIfNull(cycle);
        step.RequireValid();
        if (!double.IsFinite(windowM) || windowM <= 0.0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(windowM), windowM, "Okno zatrzymania musi być dodatnie i skończone.");
        }

        _stations = stations;
        _cycle = cycle;
        _step = step;
        _windowM = windowM;
        StartFromScratch();
    }

    /// <summary>
    /// Zeruje obsługę stacji do stanu z chwili utworzenia: kolejka wraca na pierwszą
    /// stację po punkcie startowym, rejestry wywołań i minięć są puste, a trwający
    /// cykl drzwi przestaje istnieć.
    ///
    /// <para><b>Po co to jest.</b> Reset przejazdu w kabinie
    /// (<c>src/Game/FirstRun.cs</c>, akcja <c>run_reset</c>) cofał skład na początek
    /// osi i zerował stan dynamiczny, ale tej klasy nie dotykał. Skutek był taki, że
    /// skład stał na 94,0 m z kolejką ustawioną na stację, do której zdążył dojechać,
    /// a <see cref="_next"/> idzie tylko w przód — pominiętych peronów nie dało się już
    /// obsłużyć. Trwający cykl drzwi przeżywał reset i blokował trakcję w tunelu.
    /// Opisane w <c>reports/droga-do-grywalnosci.md</c> §5.4 i §G-4.</para>
    ///
    /// <para><b>Dlaczego metoda w rdzeniu, a nie budowanie obiektu od nowa w scenie.</b>
    /// Wołający musiałby wtedy trzymać u siebie wszystkie cztery argumenty konstruktora
    /// i składać je drugi raz — czyli drugą kopię wiedzy o tym, jak wygląda POCZĄTEK
    /// przejazdu. Tutaj początek jest jednym prywatnym
    /// <see cref="StartFromScratch"/>, wołanym i przez konstruktor, i przez tę metodę,
    /// więc stan po resecie nie ma jak różnić się od stanu po utworzeniu.</para>
    ///
    /// <para><b>Czego ta metoda NIE zmienia:</b> osi, cyklu drzwi, kroku ani okna
    /// zatrzymania. To są nastawy przejazdu, a nie jego stan — reset przejazdu nie jest
    /// zmianą scenariusza.</para>
    /// </summary>
    public void Reset() => StartFromScratch();

    /// <summary>
    /// Stan początkowy obsługi stacji. JEDNO miejsce dla konstruktora i dla
    /// <see cref="Reset"/> — patrz uzasadnienie przy <see cref="Reset"/>.
    /// </summary>
    private void StartFromScratch()
    {
        _calls.Clear();
        _missed.Clear();
        _stop = null;
        _next = _stations.Count > 0 ? 1 : 0;
        _departedAtSeconds = 0.0;
        _departedFromM = _stations.Count > 0 ? _stations[0].ChainageM : 0.0;
        _topSpeedMps = 0.0;
    }

    /// <summary>Cykl drzwi tej obsługi.</summary>
    public DoorCycle Cycle => _cycle;

    /// <summary>Połowa szerokości okna zatrzymania.</summary>
    public double WindowM => _windowM;

    /// <summary>Czy nie ma już żadnej stacji do obsłużenia.</summary>
    public bool Finished => _next >= _stations.Count;

    /// <summary>Czy skład stoi na stacji z trwającym cyklem drzwi.</summary>
    public bool AtStation => _stop is not null;

    /// <summary>Faza drzwi; <see cref="DoorPhase.Closed"/> poza postojem.</summary>
    public DoorPhase Phase => _stop?.Phase ?? DoorPhase.Closed;

    /// <summary>Czy trakcja jest w tej chwili zwolniona.</summary>
    public bool TractionAllowed => DoorCycle.TractionAllowed(Phase);

    /// <summary>Ile sekund postoju jeszcze zostało; zero poza postojem.</summary>
    public double DwellRemainingSeconds => _stop is null
        ? 0.0
        : Math.Max(0.0, _cycle.DwellSeconds - _stop.SecondsSinceStopped);

    /// <summary>Obsłużone wywołania stacji, w kolejności kilometrażu.</summary>
    public IReadOnlyList<StationCall> Calls => _calls;

    /// <summary>Stacje, których czoło minęło bez zatrzymania w oknie.</summary>
    public IReadOnlyList<AxisStation> Missed => _missed;

    /// <summary>Stan najbliższej stacji przed składem — to, co pokazuje HUD.</summary>
    /// <param name="chainageM">Kilometraż czoła składu.</param>
    public StationApproach Approach(double chainageM)
    {
        if (Finished)
        {
            return new StationApproach(string.Empty, string.Empty, double.NaN, double.NaN, false);
        }

        var station = _stations[_next];
        var distance = station.ChainageM - chainageM;
        return new StationApproach(
            station.Name, station.StopId, station.ChainageM, distance,
            Math.Abs(distance) <= _windowM);
    }

    /// <summary>
    /// Jeden krok obsługi stacji: rozpoznanie zatrzymania, cykl drzwi, blokada trakcji.
    ///
    /// Zwraca polecenie, które wolno podać <see cref="TrainController"/>. Hamulca
    /// <b>nie</b> zeruje ani nie dodaje — trzymanie składu na postoju należy do
    /// wołającego, tak samo jak w <see cref="StationStop.Filter"/>.
    /// </summary>
    /// <param name="state">Stan składu przed krokiem.</param>
    /// <param name="requested">Polecenie maszynisty.</param>
    /// <param name="chainageM">Kilometraż czoła składu.</param>
    public DriverCommand Filter(DriveState state, DriverCommand requested, double chainageM)
    {
        if (state.SpeedMps > _topSpeedMps)
        {
            _topSpeedMps = state.SpeedMps;
        }

        if (Finished)
        {
            return requested;
        }

        var station = _stations[_next];
        var now = state.TimeSeconds(_step);

        if (_stop is null)
        {
            if (state.SpeedMps <= 0.0 && Math.Abs(chainageM - station.ChainageM) <= _windowM)
            {
                _stop = new StationStop(_cycle, _step);
                _calls.Add(new StationCall(
                    station.Name, station.StopId, station.ChainageM, chainageM,
                    chainageM - station.ChainageM, now, double.NaN,
                    now - _departedAtSeconds, chainageM - _departedFromM, _topSpeedMps));
            }
            else if (chainageM > station.ChainageM + _windowM)
            {
                // Minięta. Nie ma biegu wstecznego, więc żadne późniejsze polecenie
                // tego nie odwróci — kolejka idzie dalej, a stacja ląduje w rejestrze.
                _missed.Add(station);
                _departedAtSeconds = now;
                _departedFromM = chainageM;
                _topSpeedMps = state.SpeedMps;
                _next++;
                return requested;
            }
            else
            {
                return requested;
            }
        }

        var held = _stop!.Filter(state, requested);

        if (_stop.Finished)
        {
            _calls[^1] = _calls[^1] with { DepartureSeconds = now };
            _departedAtSeconds = now;
            _departedFromM = chainageM;
            _topSpeedMps = state.SpeedMps;
            _stop = null;
            _next++;
        }

        return held;
    }

    /// <inheritdoc/>
    public override string ToString() => string.Create(
        CultureInfo.InvariantCulture,
        $"stacje: {_calls.Count} obsłużonych, {_missed.Count} przejechanych, " +
        $"{(Finished ? "koniec" : $"następna {_stations[_next].Name}")}, okno ±{_windowM:F1} m");
}
