using System;
using System.Collections.Generic;
using System.Linq;
using System.Globalization;
using System.Security.Cryptography;
using System.Text;
using MetroBxl.Sim.Physics;
using MetroBxl.Sim.Train;

namespace MetroBxl.Sim.Line;

/// <summary>
/// Przejazd linii z maszynistą przy JEDNYM ze składów — wspólna droga sceny
/// i <c>Sim.Runner replay --line</c> (6.M1).
///
/// <para><b>Dlaczego klasa w rdzeniu, a nie dwie kopie kroku.</b> Do 6.M1 krok linii
/// z dźwignią maszynisty istniał wyłącznie w <c>FirstRun.StepOnce</c>, a polecenia
/// przejęcia i drzwi — wyłącznie w <c>FirstRun.HandleTrainKeys</c>. Odtworzenie w
/// rdzeniu musiałoby je przepisać, a dwie kopie tej samej kolejności faz rozjeżdżają
/// się po cichu: porównanie sceny z rdzeniem co do bitu byłoby wtedy zgodnością dwóch
/// kopii, a nie dowodem determinizmu. Tutaj stoi JEDNA kolejność: polecenia przed
/// krokiem, dźwignia składu obserwowanego, krok linii.</para>
///
/// <para><b>Warunki poleceń są TE SAME, co przy klawiaturze</b> — przejęcie tylko
/// składu, który jest na planie i jedzie pod autopilotem; oddanie tylko składu
/// prowadzonego przez maszynistę; drzwi pytane zawsze, bo rdzeń odmawia sam. Polecenie
/// niewykonalne jest więc zapisywane i odtwarzane tak samo jak wykonalne: w obu
/// przebiegach nie robi nic, i to jest cała zgodność, której trzeba.</para>
/// </summary>
public sealed class LineSession
{
    /// <summary>
    /// Identyfikator składu zerowego — tego, który scena pokazuje z kabiny od startu.
    /// Ten sam napis w scenie i w <c>Sim.Runner</c>, bo zdarzenia linii w zapisie wejść
    /// wskazują skład PO IDENTYFIKATORZE (6.M1).
    /// </summary>
    public const string CabTrainId = "KABINA";

    /// <summary>
    /// Identyfikator składu o danym indeksie w kolejności dodawania do linii: zerowy
    /// to <see cref="CabTrainId"/>, kolejne <c>SKLAD-02</c>, <c>SKLAD-03</c>…
    /// </summary>
    /// <param name="index">Indeks składu, od zera.</param>
    public static string TrainIdAt(int index) =>
        index == 0 ? CabTrainId : string.Create(
            System.Globalization.CultureInfo.InvariantCulture, $"SKLAD-{index + 1:00}");

    private readonly LineCore _core;
    private readonly DriverNotch _notch;
    private readonly FixedStep _step;
    private readonly LineEntryDispatcher? _dispatcher;
    private readonly Dictionary<string, DriverCommand> _commands = new(StringComparer.Ordinal);
    private int _observed;
    private string? _notchTrainId;

    /// <summary>Sesja na gotowej linii z dodanymi składami.</summary>
    /// <param name="core">Linia; składy dodaje wołający, przed pierwszym krokiem.</param>
    /// <param name="notch">Nastawnik maszynisty — ten sam obiekt, który czyta HUD.</param>
    /// <param name="step">Krok symulacji linii.</param>
    /// <param name="dispatcher">Opcjonalny zegar rozkładowych wjazdów.</param>
    public LineSession(LineCore core, DriverNotch notch, FixedStep step,
        LineEntryDispatcher? dispatcher = null)
    {
        _core = core ?? throw new ArgumentNullException(nameof(core));
        _notch = notch ?? throw new ArgumentNullException(nameof(notch));
        _step = step;
        _dispatcher = dispatcher;
    }

    /// <summary>All scheduled entries and their trips are complete.</summary>
    public bool Finished => _dispatcher?.Finished ?? _core.Finished;

    /// <summary>Linia, którą sesja prowadzi.</summary>
    public LineCore Core => _core;

    /// <summary>
    /// Exact digest of the line session's deterministic operational state. The fixed
    /// order is train registration order; driver-command map keys are sorted ordinally.
    /// Rendering, frame accumulator and file output are deliberately outside this state.
    /// </summary>
    public string StateSha256()
    {
        var hash = new StateHashWriter();
        hash.Add("line-session-v1");
        hash.Add(_core.AxisId);
        hash.Add(_core.Steps);
        hash.Add(_core.Finished);
        hash.Add(_core.ProtectionWarnings);
        hash.Add(_core.ServiceInterventions);
        hash.Add(_core.EmergencyInterventions);
        hash.Add(_core.MaxBrakeDemandMps2);
        hash.Add(_core.Dispatcher.StateSha256());
        hash.Add(_core.Signalling.StateDigest());
        _core.Signalling.AppendRuntimeState(hash);
        hash.Add(_dispatcher is not null);
        if (_dispatcher is not null) hash.Add(_dispatcher.RegisteredEntries);
        hash.Add(_observed);
        hash.Add(_notchTrainId);
        hash.Add(_notch.Command.Throttle);
        hash.Add(_notch.Command.Brake);
        hash.Add(Command.Throttle);
        hash.Add(Command.Brake);
        hash.Add(AccelerationMps2);
        foreach (var key in _commands.Keys.OrderBy(key => key, StringComparer.Ordinal))
        {
            hash.Add(key);
            hash.Add(_commands[key].Throttle);
            hash.Add(_commands[key].Brake);
        }
        hash.Add(_core.Trains.Count);
        foreach (var train in _core.Trains)
        {
            hash.Add(train.Id);
            hash.Add(train.ReleaseStep);
            hash.Add(train.EntryStationIndex);
            hash.Add(train.EnteredAtStep.HasValue);
            if (train.EnteredAtStep is long entered) hash.Add(entered);
            hash.Add(train.FinishedAtStep.HasValue);
            if (train.FinishedAtStep is long finished) hash.Add(finished);
            hash.Add(train.LeftPlan);
            hash.Add((long)train.Owner);
            hash.Add(train.DriverCommand.HasValue);
            if (train.DriverCommand is DriverCommand command)
            {
                hash.Add(command.Throttle);
                hash.Add(command.Brake);
            }
            hash.Add(train.Authority.HasValue);
            if (train.Authority is { } authority)
            {
                hash.Add(authority.FrontChainageM);
                hash.Add(authority.EndChainageM);
                hash.Add(authority.LimitBlockId);
                hash.Add((long)authority.Reason);
            }
            hash.Add(train.Protection.HasValue);
            if (train.Protection is { } protection)
            {
                hash.Add(protection.PermittedSpeedMps);
                hash.Add(protection.AuthorityDistanceM);
                hash.Add((long)protection.Action);
                hash.Add(protection.BrakeDemandMps2);
                hash.Add(protection.Overspeed);
                hash.Add(protection.Reason);
            }
            hash.Add(train.Drive is not null);
            train.Drive?.AppendState(hash);
            hash.Add(train.CompletedRuns.Count);
            foreach (var run in train.CompletedRuns)
            {
                hash.Add(run.AxisId);
                hash.Add(run.Steps);
                hash.Add(run.TotalSeconds);
                hash.Add(run.TotalDistanceM);
                hash.Add(run.DwellSeconds);
                hash.Add(run.FinishReason);
                hash.Add(run.Calls.Count);
                foreach (var call in run.Calls)
                {
                    hash.Add(call.Name);
                    hash.Add(call.StopId);
                    hash.Add(call.ChainageM);
                    hash.Add(call.StoppedAtChainageM);
                    hash.Add(call.StopErrorM);
                    hash.Add(call.ArrivalSeconds);
                    hash.Add(call.DepartureSeconds);
                    hash.Add(call.RunSecondsFromPrevious);
                    hash.Add(call.DistanceFromPreviousM);
                    hash.Add(call.TopSpeedMps);
                    hash.Add(call.TractionWorkFromPreviousJ.HasValue);
                    if (call.TractionWorkFromPreviousJ is double work) hash.Add(work);
                }
                hash.Add(run.Energy.TractionWorkJ);
                hash.Add(run.Energy.ResistanceWorkJ);
                hash.Add(run.Energy.GradeWorkJ);
                hash.Add(run.Energy.BrakeWorkJ);
                hash.Add(run.Energy.KineticEnergyDeltaJ);
                hash.Add(run.Energy.DiscretizationWorkJ);
                hash.Add(run.Energy.ClampedWorkJ);
            }
        }
        return hash.Sha256();
    }

    /// <summary>Indeks składu obserwowanego w <see cref="LineCore.Trains"/>.</summary>
    public int ObservedIndex => _core.Trains.Count == 0
        ? 0
        : ActiveObservedIndex ?? Math.Clamp(_observed, 0, _core.Trains.Count - 1);

    /// <summary>An active view, or no train while all registered trips are off the line.</summary>
    public int? ActiveObservedIndex
    {
        get
        {
            if (_core.Trains.Count == 0)
                return null;
            var selected = Math.Clamp(_observed, 0, _core.Trains.Count - 1);
            // A not-yet-entered train may be selected explicitly by a replay event.
            // Only a train that has actually left the plan must lose its camera.
            if (!_core.Trains[selected].LeftPlan)
                return _core.Trains[selected].OnLine ? selected : null;
            for (var offset = 1; offset <= _core.Trains.Count; offset++)
            {
                var candidate = (selected + offset) % _core.Trains.Count;
                if (_core.Trains[candidate].OnLine)
                    return candidate;
            }
            return null;
        }
    }

    /// <summary>Next train currently on the line, for the player's N key.</summary>
    public string? NextActiveTrainId()
    {
        var count = _core.Trains.Count;
        var current = ActiveObservedIndex ?? Math.Clamp(_observed, 0, Math.Max(0, count - 1));
        for (var offset = 1; offset < count; offset++)
        {
            var candidate = (current + offset) % count;
            if (_core.Trains[candidate].OnLine)
                return _core.Trains[candidate].Id;
        }
        return null;
    }

    /// <summary>Skład obserwowany — do niego idzie dźwignia maszynisty.</summary>
    public LineTrain Observed => _core.Trains[ObservedIndex];

    /// <summary>Przyspieszenie składu obserwowanego w ostatnim kroku, m/s².</summary>
    public double AccelerationMps2 { get; private set; }

    /// <summary>Polecenie składu obserwowanego w ostatnim kroku.</summary>
    public DriverCommand Command { get; private set; } = DriverCommand.Coast;

    /// <summary>
    /// Następny skład obecny na linii jako obserwowany — klawisz <c>N</c>.
    /// </summary>
    /// <returns>Identyfikator składu, który jest obserwowany po zmianie.</returns>
    public string ObserveNext()
    {
        if (_core.Trains.Count == 0)
            throw new InvalidOperationException("Nie ma jeszcze składu do obserwowania.");
        var next = NextActiveTrainId();
        if (next is null)
            throw new InvalidOperationException("Nie ma składu na planie do obserwowania.");
        _observed = IndexOf(next);
        return Observed.Id;
    }

    /// <summary>
    /// Wykonuje polecenie maszynisty z zapisu albo z klawiatury — PRZED krokiem.
    /// </summary>
    /// <param name="lineEvent">Polecenie; jego numer kroku nie jest tu czytany.</param>
    /// <returns>
    /// Odpowiedź rdzenia na polecenie drzwi, albo <c>null</c> dla pozostałych poleceń.
    /// </returns>
    public DoorRequestResult? Execute(InputLogEvent lineEvent)
    {
        switch (lineEvent.Kind)
        {
            case LineEventKind.Observe:
                _observed = IndexOf(lineEvent.TrainId);
                if (Observed.Owner == ControlOwner.Driver &&
                    _notchTrainId is not null && _notchTrainId != Observed.Id &&
                    Observed.DriverCommand is { } held)
                {
                    _notch.Set(held);
                    _notchTrainId = Observed.Id;
                }
                Command = _commands.TryGetValue(Observed.Id, out var observedCommand)
                    ? observedCommand : DriverCommand.Coast;
                AccelerationMps2 = 0.0;
                return null;
            case LineEventKind.Take:
                var candidate = _core.Trains[IndexOf(lineEvent.TrainId)];
                if (candidate.Owner == ControlOwner.Autopilot && candidate.OnLine)
                {
                    _core.TakeControl(candidate.Id);
                    if (candidate == Observed && _notchTrainId is not null &&
                        _notchTrainId != candidate.Id && candidate.DriverCommand is { } captured)
                    {
                        _notch.Set(captured);
                        _notchTrainId = candidate.Id;
                    }
                }

                return null;
            case LineEventKind.Release:
                var driven = _core.Trains[IndexOf(lineEvent.TrainId)];
                if (driven.Owner == ControlOwner.Driver)
                {
                    _core.ReleaseControl(driven.Id);
                }

                return null;
            case LineEventKind.DoorOpen:
                return _core.RequestDoorOpen(lineEvent.TrainId);
            case LineEventKind.DoorClose:
                return _core.RequestDoorClose(lineEvent.TrainId);
            default:
                throw new ArgumentOutOfRangeException(
                    nameof(lineEvent), lineEvent.Kind, "nieznany rodzaj zdarzenia linii");
        }
    }

    /// <summary>
    /// Jeden krok linii z dźwignią maszynisty na składzie obserwowanym.
    ///
    /// <para>Nastawnik posuwa się DOKŁADNIE RAZ na krok i tylko wtedy, gdy skład
    /// obserwowany prowadzi maszynista — tak jak w <c>FirstRun</c> przed 6.M1. Pod
    /// autopilotem dźwignia nie jest czytana, więc jej położenie nie zależy od tego,
    /// jak długo gracz trzymał klawisz przed przejęciem.</para>
    /// </summary>
    /// <param name="keys">Stan klawiszy maszynisty w tym kroku.</param>
    /// <returns><c>false</c>, gdy linia była już skończona i krok się nie odbył.</returns>
    public bool Step(DriverKeys keys)
    {
        if (Finished)
        {
            return false;
        }

        // The first scheduled trip is registered during dispatcher.Step. Before
        // that call there is no train for the driver's notch to address.
        if (_core.Trains.Count == 0)
        {
            _dispatcher!.Step((id, point) => _commands[id] = point.Command);
            // A train may enter and drive during this very step. Report that
            // step's actual command and acceleration, as on later steps.
            if (_core.Trains.Count > 0)
            {
                var entered = Observed;
                Command = _commands.TryGetValue(entered.Id, out var entryCommand)
                    ? entryCommand : DriverCommand.Coast;
                AccelerationMps2 = entered.Drive is { } entryDrive
                    ? entryDrive.State.SpeedMps / _step.Seconds : 0.0;
            }
            else
            {
                Command = DriverCommand.Coast;
                AccelerationMps2 = 0.0;
            }
            return true;
        }

        var observed = Observed;
        var before = observed.Drive?.State.SpeedMps ?? 0.0;
        if (observed.OnLine && observed.Owner == ControlOwner.Driver)
        {
            _core.Drive(observed.Id, _notch.Advance(keys, _step));
            _notchTrainId = observed.Id;
        }

        if (_dispatcher is null)
            _core.Step((id, point) => _commands[id] = point.Command);
        else
            _dispatcher.Step((id, point) => _commands[id] = point.Command);

        var switched = ObservedIndex != _observed;
        if (switched)
            _observed = ObservedIndex;
        if (ActiveObservedIndex is null)
        {
            Command = DriverCommand.Coast;
            AccelerationMps2 = 0.0;
            return true;
        }
        observed = Observed;
        if (_commands.TryGetValue(observed.Id, out var command))
        {
            Command = command;
        }

        AccelerationMps2 = !switched && observed.Drive is { } drive
            ? (drive.State.SpeedMps - before) / _step.Seconds
            : 0.0;
        return true;
    }

    /// <summary>
    /// Wiersz telemetrii składu obserwowanego, albo <c>null</c>, gdy na planie nie ma
    /// aktywnego składu.
    /// </summary>
    /// <returns>Wiersz zgodny z <see cref="DriveTelemetry.Header"/>.</returns>
    public string? TelemetryRow() => ActiveObservedIndex is not null && Observed.Drive is { } drive
        ? DriveTelemetry.Row(
            drive.State, _step, drive.ChainageM, AccelerationMps2, Command, DriveTelemetry.ManualPhase)
        : null;

    private int IndexOf(string trainId)
    {
        for (var i = 0; i < _core.Trains.Count; i++)
        {
            if (string.Equals(_core.Trains[i].Id, trainId, StringComparison.Ordinal))
            {
                return i;
            }
        }

        throw new ArgumentException(
            $"Zdarzenie linii dotyczy składu '{trainId}', którego na linii nie ma.", nameof(trainId));
    }
}

/// <summary>Unambiguous, culture-independent encoding of a simulation state.</summary>
internal sealed class StateHashWriter
{
    private readonly StringBuilder _text = new();

    public void Add(string? value)
    {
        if (value is null)
        {
            _text.Append("N;");
            return;
        }
        _text.Append('S').Append(value.Length.ToString(CultureInfo.InvariantCulture))
            .Append(':').Append(value).Append(';');
    }

    public void Add(long value) => _text.Append('I').Append(value.ToString(CultureInfo.InvariantCulture)).Append(';');

    public void Add(bool value) => _text.Append(value ? "T;" : "F;");

    // Exact IEEE-754 bits: no rounding, locale, NaN or signed-zero ambiguity.
    public void Add(double value) => _text.Append('D')
        .Append(BitConverter.DoubleToInt64Bits(value).ToString("X16", CultureInfo.InvariantCulture)).Append(';');

    public string Sha256() => Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(_text.ToString())))
        .ToLowerInvariant();
}
