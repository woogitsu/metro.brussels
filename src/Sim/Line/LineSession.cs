using System;
using System.Collections.Generic;
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

    /// <summary>Indeks składu obserwowanego w <see cref="LineCore.Trains"/>.</summary>
    public int ObservedIndex => _core.Trains.Count == 0
        ? 0
        : Math.Clamp(_observed, 0, _core.Trains.Count - 1);

    /// <summary>Skład obserwowany — do niego idzie dźwignia maszynisty.</summary>
    public LineTrain Observed => _core.Trains[ObservedIndex];

    /// <summary>Przyspieszenie składu obserwowanego w ostatnim kroku, m/s².</summary>
    public double AccelerationMps2 { get; private set; }

    /// <summary>Polecenie składu obserwowanego w ostatnim kroku.</summary>
    public DriverCommand Command { get; private set; } = DriverCommand.Coast;

    /// <summary>
    /// Następny skład na liście jako obserwowany — klawisz <c>N</c>.
    /// </summary>
    /// <returns>Identyfikator składu, który jest obserwowany po zmianie.</returns>
    public string ObserveNext()
    {
        _observed = (ObservedIndex + 1) % _core.Trains.Count;
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
            Command = DriverCommand.Coast;
            AccelerationMps2 = 0.0;
            return true;
        }

        var observed = Observed;
        var before = observed.Drive?.State.SpeedMps ?? 0.0;
        if (observed.Owner == ControlOwner.Driver)
        {
            _core.Drive(observed.Id, _notch.Advance(keys, _step));
            _notchTrainId = observed.Id;
        }

        if (_dispatcher is null)
            _core.Step((id, point) => _commands[id] = point.Command);
        else
            _dispatcher.Step((id, point) => _commands[id] = point.Command);

        observed = Observed;
        if (_commands.TryGetValue(observed.Id, out var command))
        {
            Command = command;
        }

        AccelerationMps2 = observed.Drive is { } drive
            ? (drive.State.SpeedMps - before) / _step.Seconds
            : 0.0;
        return true;
    }

    /// <summary>
    /// Wiersz telemetrii składu obserwowanego, albo <c>null</c>, gdy skład nie wszedł
    /// jeszcze na plan i nie ma czego opisać.
    /// </summary>
    /// <returns>Wiersz zgodny z <see cref="DriveTelemetry.Header"/>.</returns>
    public string? TelemetryRow() => Observed.Drive is { } drive
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
