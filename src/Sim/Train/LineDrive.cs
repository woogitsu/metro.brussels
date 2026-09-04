using System;
using System.Collections.Generic;
using MetroBxl.Sim.Line;
using MetroBxl.Sim.Physics;

namespace MetroBxl.Sim.Train;

/// <summary>
/// Jeden prowadzony skład, krokowany **z zewnątrz**.
///
/// <para><b>Po co to istnieje.</b> <see cref="LineRun"/> trzyma pętlę wewnątrz siebie:
/// woła się raz i wraca dopiero po całym przejeździe. Dla jednego składu to wystarcza,
/// ale T-320 potrzebuje **wielu składów na jednym zegarze** — a dwóch pętli, z których
/// każda wie tylko o sobie, nie da się zsynchronizować co krok. Żeby skład mógł zobaczyć
/// inny skład przed sobą, ktoś musi mieć prawo powiedzieć „wszyscy o jeden krok".</para>
///
/// <para><b>Czym to NIE jest.</b> To nie jest nowy model jazdy. Ciało kroku jest
/// przeniesione z <see cref="LineRun"/> bez zmiany kolejności działań — dowodem jest
/// ślad co krok, identyczny co do bajtu na sześciu osiach przed refaktorem i po nim.
/// Sam <see cref="LineRun"/> po tej zmianie jest pętlą <c>while</c> nad tą klasą
/// i niczym więcej.</para>
///
/// <para><b>Czego tu nadal nie ma.</b> Ani jeden skład nie wie o żadnym innym. Ta klasa
/// tylko **umożliwia** wspólny zegar; sprzężenie między składami — autorytet jazdy
/// z T-313, takt, turnback — jest osobnym krokiem i częściowo czeka na decyzje,
/// których nie ma w żadnym dokumencie (`docs/TASKS.md`, T-320, sekcja STOP).</para>
/// </summary>
public sealed class LineDrive
{
    private readonly TrainController _controller;
    private readonly BrakingPointSolver _solver;
    private readonly FixedStep _step;
    private readonly IReadOnlyList<AxisStation> _stations;
    private readonly RunConditions _conditions;
    private readonly LineRunSettings _settings;
    private readonly DoorCycle _cycle;
    private readonly double _start;
    private readonly double _trigger;
    private readonly List<StationCall> _calls;

    private DriveState _state = DriveState.AtRest;
    private int _next = 1;
    private double _topSpeed;
    private double _departedAtSeconds;
    private double _departedFromM;
    private bool _braking;
    private StationStop? _stop;

    /// <summary>Skład postawiony na początku osi, gotowy do pierwszego kroku.</summary>
    /// <param name="axis">Oś z kilometrażem stacji.</param>
    /// <param name="conditions">Masa, pochylenie, przyczepność, otoczenie toru.</param>
    /// <param name="settings">Założenia przejazdu — wszystkie bez źródła.</param>
    /// <param name="controller">Kontroler z T-310.</param>
    /// <param name="solver">Solver punktu hamowania z T-311.</param>
    /// <param name="step">Krok stały.</param>
    public LineDrive(
        TrackAxis axis,
        RunConditions conditions,
        LineRunSettings settings,
        TrainController controller,
        BrakingPointSolver solver,
        FixedStep step)
    {
        ArgumentNullException.ThrowIfNull(axis);
        ArgumentNullException.ThrowIfNull(conditions);
        ArgumentNullException.ThrowIfNull(settings);
        ArgumentNullException.ThrowIfNull(controller);
        ArgumentNullException.ThrowIfNull(solver);
        step.RequireValid();

        if (axis.Stations.Count < 2)
        {
            throw new ArgumentOutOfRangeException(
                nameof(axis), axis.Stations.Count,
                "Przejazd z zatrzymaniami wymaga co najmniej dwóch stacji na osi.");
        }

        AxisId = axis.Id;
        _stations = axis.Stations;
        _conditions = conditions;
        _settings = settings;
        _controller = controller;
        _solver = solver;
        _step = step;

        _start = _stations[0].ChainageM;
        _cycle = new DoorCycle(settings.PassengerExchangeSeconds);
        _trigger = settings.BrakeUsageFraction * controller.ServiceBrakeMps2;
        _calls = new List<StationCall>(_stations.Count);
        _departedFromM = _start;
    }

    /// <summary>Identyfikator osi, po której jedzie ten skład.</summary>
    public string AxisId { get; }

    /// <summary>Stan dynamiczny po ostatnim kroku.</summary>
    public DriveState State => _state;

    /// <summary>Chainage czoła składu na osi.</summary>
    public double ChainageM => _start + _state.DistanceM;

    /// <summary>Liczba wykonanych kroków — czas jest funkcją tej liczby, nigdy sumą.</summary>
    public long Steps => _state.Steps;

    /// <summary>Zatrzymania odnotowane do tej pory.</summary>
    public IReadOnlyList<StationCall> Calls => _calls;

    /// <summary>Prawda, gdy skład zatrzymał się na ostatniej stacji osi.</summary>
    public bool Finished => _next >= _stations.Count;

    /// <summary>Prawda, gdy trwa postój na stacji.</summary>
    public bool AtStation => _stop is not null;

    /// <summary>
    /// Jeden krok stały. Ciało przeniesione z <see cref="LineRun"/> bez zmiany kolejności.
    /// </summary>
    /// <param name="trace">Ślad wołany po kroku, gdy podany.</param>
    /// <returns>Fałsz, gdy skład był już na końcu i krok się nie odbył.</returns>
    public bool Step(Action<LineRun.TracePoint>? trace = null)
    {
        if (Finished)
        {
            return false;
        }

        var chainage = _start + _state.DistanceM;
        var target = _stations[_next].ChainageM;

        if (_stop is null
            && _state.SpeedMps <= 0.0
            && chainage >= target - _settings.StopWindowM
            && chainage - _departedFromM >= _settings.StopWindowM)
        {
            _stop = new StationStop(_cycle, _step);
            _calls.Add(new StationCall(
                _stations[_next].Name,
                _stations[_next].StopId,
                target,
                chainage,
                chainage - target,
                _state.TimeSeconds(_step),
                double.NaN,
                _state.TimeSeconds(_step) - _departedAtSeconds,
                chainage - _departedFromM,
                _topSpeed));
        }

        if (_stop is not null)
        {
            // Postój. `Filter` jest jedynym miejscem, które posuwa licznik cyklu drzwi,
            // więc musi zostać zawołane dokładnie raz na krok. Hamulca nie zeruje
            // celowo — trzymanie składu na postoju należy do wołającego.
            var held = _stop.Filter(_state, DriverCommand.FullServiceBrake);
            var phase = _stop.Phase;
            _state = _controller.Advance(
                _state, _conditions, held, _settings.SpeedLimitMps, _step, out _);
            trace?.Invoke(new LineRun.TracePoint(
                _state.TimeSeconds(_step), _start + _state.DistanceM, _state.SpeedMps,
                _state.BrakeRateMps2, held, phase));

            if (_stop.Finished)
            {
                _calls[^1] = _calls[^1] with { DepartureSeconds = _state.TimeSeconds(_step) };
                _departedAtSeconds = _state.TimeSeconds(_step);
                _departedFromM = _start + _state.DistanceM;
                _topSpeed = 0.0;
                _braking = false;
                _stop = null;
                _next++;
            }

            return true;
        }

        var command = Command(target - chainage);
        _braking |= command.Brake > 0.0;
        _state = _controller.Advance(
            _state, _conditions, command, _settings.SpeedLimitMps, _step, out _);
        trace?.Invoke(new LineRun.TracePoint(
            _state.TimeSeconds(_step), _start + _state.DistanceM, _state.SpeedMps,
            _state.BrakeRateMps2, command, DoorPhase.Closed));
        if (_state.SpeedMps > _topSpeed)
        {
            _topSpeed = _state.SpeedMps;
        }

        return true;
    }

    /// <summary>Wynik przejazdu w postaci, jakiej oczekuje <see cref="LineRun"/>.</summary>
    /// <param name="reason">Dlaczego pętla wołającego się skończyła.</param>
    public LineRunResult Result(string reason)
    {
        var last = _calls.Count > 0 ? _calls[^1] : default;
        return new LineRunResult(
            AxisId,
            _calls,
            last.ArrivalSeconds,
            last.StoppedAtChainageM - _start,
            SumDwell(_calls),
            _state.Steps,
            reason);
    }

    /// <summary>
    /// Polecenie maszynisty w jednym kroku jazdy między stacjami.
    ///
    /// Punkt hamowania nie jest tu parametrem. W każdym kroku solver z T-311 odpowiada,
    /// jakiego opóźnienia wymaga pozostała odległość przy bieżącej prędkości; hamowanie
    /// zaczyna się, gdy odpowiedź przekroczy próg, a jego siła jest tą odpowiedzią.
    /// Dlatego punkt hamowania przesuwa się sam wraz z prędkością, masą i pochyleniem.
    /// </summary>
    private DriverCommand Command(double remainingM)
    {
        if (remainingM <= 0.0)
        {
            // Stacja minięta z prędkością. Pełny hamulec; błąd zatrzymania to zmierzy
            // i wyjdzie w raporcie jako dodatni StopErrorM, a nie zniknie.
            return DriverCommand.FullServiceBrake;
        }

        if (_state.SpeedMps <= 0.0)
        {
            return DriverCommand.FullPower;
        }

        if (!_solver.TryRequiredDeceleration(_state.SpeedMps, 0.0, remainingM, out var need))
        {
            // Poniżej minimalnej drogi wynikającej ze zrywu rozwiązania nie ma — wtedy
            // nawet pełny hamulec nie zatrzyma składu na czas i „prawie" nie jest odpowiedzią.
            return DriverCommand.FullServiceBrake;
        }

        if (!_braking && need.DecelerationMps2 < _trigger)
        {
            return _state.SpeedMps < _settings.SpeedLimitMps
                ? DriverCommand.FullPower
                : DriverCommand.Coast;
        }

        // **Próg wyzwala hamowanie, ale nie steruje nim.** Raz zaczęte hamowanie idzie
        // za serwem aż do zatrzymania: siła hamulca jest w każdym kroku tą, której wymaga
        // pozostała odległość. Sprawdzanie progu również w trakcie hamowania było usterką
        // — opory ruchu hamują mocniej, niż zakłada wzór zamknięty z T-311 (ten jest
        // czysto kinematyczny), więc wymagane opóźnienie spadało poniżej progu, pętla
        // wracała do trakcji, odległość malała i hamulec wracał. W śladzie widać było
        // 3,12 s pełzania na 1,08 m: trzy sekundy doliczone do czasu jazdy przez
        // sterowanie, nie przez fizykę.
        // **Wzór zamknięty odpowiada na inne pytanie niż to, które ma serwo.** Droga
        // z T-311 zawiera człon narastania hamulca zrywem od ZERA — jest więc odpowiedzią
        // na „kiedy zacząć hamować". Gdy hamulec już działa, ten człon jest zaliczony
        // dwa razy: solver kredytuje narastanie, które się właśnie odbyło, więc żąda
        // mniejszego opóźnienia, skład jedzie dalej, i tak w kółko. W śladzie wychodziło
        // to jako łagodne dojeżdżanie do peronu i 3 s doliczone do czasu jazdy.
        //
        // Dlatego próg wyzwala hamowanie wzorem z narastaniem, a samo hamowanie prowadzi
        // czysta kinematyka v²/2d — hamulec już narósł, więc nie ma czego doliczać.
        var required = _state.SpeedMps * _state.SpeedMps / (2.0 * remainingM);

        // Polecenie to opóźnienie **hamulca**, a nie całkowite: skład zwalnia też oporami
        // ruchu i składową pochylenia, a te działają niezależnie od nastawy. Żeby sumaryczne
        // opóźnienie wyszło takie, o jakie prosi kinematyka, hamulec dostaje różnicę.
        var resistance = _controller.Dynamics.Resistance.ForceN(
            _conditions.MassKg, _state.SpeedMps, _conditions.Environment);
        var grade = TrainDynamics.GradeForceN(_conditions.MassKg, _conditions.GradePercent);
        var passive = (resistance + grade) / _controller.Dynamics.EffectiveMassKg(_conditions.MassKg);

        return new DriverCommand(
            0.0, Math.Clamp((required - passive) / _controller.ServiceBrakeMps2, 0.0, 1.0));
    }

    private static double SumDwell(IReadOnlyList<StationCall> calls)
    {
        var total = 0.0;
        foreach (var call in calls)
        {
            if (double.IsFinite(call.DepartureSeconds))
            {
                total += call.DepartureSeconds - call.ArrivalSeconds;
            }
        }

        return total;
    }
}
