using System;
using System.Collections.Generic;
using System.Globalization;
using MetroBxl.Sim.Line;
using MetroBxl.Sim.Physics;

namespace MetroBxl.Sim.Train;

/// <summary>Jedno zatrzymanie: kiedy skład stanął, gdzie i jak długo jechał od poprzedniego.</summary>
/// <param name="Name">Nazwa stacji z osi.</param>
/// <param name="StopId">Identyfikator peronu z GTFS — klucz do zestawienia z rozkładem.</param>
/// <param name="ChainageM">Chainage stacji z <c>data/track/*.json</c>.</param>
/// <param name="StoppedAtChainageM">Chainage, na którym skład faktycznie stanął.</param>
/// <param name="StopErrorM">Błąd zatrzymania; dodatni = przejechał stację.</param>
/// <param name="ArrivalSeconds">Czas zatrzymania od początku przejazdu.</param>
/// <param name="DepartureSeconds">Czas ruszenia; różnica to pełny cykl drzwi.</param>
/// <param name="RunSecondsFromPrevious">Czas jazdy od ruszenia z poprzedniej stacji.</param>
/// <param name="DistanceFromPreviousM">Droga od poprzedniej stacji.</param>
/// <param name="TopSpeedMps">Najwyższa prędkość osiągnięta na tym odcinku.</param>
public readonly record struct StationCall(
    string Name,
    string StopId,
    double ChainageM,
    double StoppedAtChainageM,
    double StopErrorM,
    double ArrivalSeconds,
    double DepartureSeconds,
    double RunSecondsFromPrevious,
    double DistanceFromPreviousM,
    double TopSpeedMps)
{
    /// <summary>Jedna linia raportu; kultura niezmienna, żeby wyjście nie zależało od maszyny.</summary>
    public override string ToString() => string.Create(
        CultureInfo.InvariantCulture,
        $"{Name}: przyjazd {ArrivalSeconds:F2} s na {StoppedAtChainageM:F2} m " +
        $"(błąd {StopErrorM:+0.000;-0.000;0.000} m), jazda {RunSecondsFromPrevious:F2} s " +
        $"na {DistanceFromPreviousM:F2} m, szczyt {Units.MpsToKmh(TopSpeedMps):F2} km/h");
}

/// <summary>Wynik przejazdu z zatrzymaniami.</summary>
/// <param name="AxisId">Identyfikator osi.</param>
/// <param name="Calls">Zatrzymania w kolejności chainage.</param>
/// <param name="TotalSeconds">Czas od ruszenia z pierwszej stacji do zatrzymania na ostatniej.</param>
/// <param name="TotalDistanceM">Droga przebyta między pierwszą a ostatnią stacją.</param>
/// <param name="DwellSeconds">Suma postojów na stacjach pośrednich.</param>
/// <param name="Steps">Liczba kroków symulacji.</param>
/// <param name="FinishReason">Dlaczego pętla się skończyła.</param>
public readonly record struct LineRunResult(
    string AxisId,
    IReadOnlyList<StationCall> Calls,
    double TotalSeconds,
    double TotalDistanceM,
    double DwellSeconds,
    long Steps,
    string FinishReason);

/// <summary>
/// Przejazd całej osi z zatrzymaniem na **każdej** stacji: rozpęd, hamowanie liczone
/// solverem z T-311 i pełny cykl drzwi z T-312.
///
/// <para><b>Czym to się różni od <see cref="ScenarioDrive"/>.</b> Tamten wykonuje
/// **zapisany** scenariusz: polecenie jest funkcją chainage, wpisaną z góry. Tutaj
/// polecenia nie ma z góry — maszynista jest zamknięty w pętli sprzężenia zwrotnego:
/// w każdym kroku pyta solvera, jakiego opóźnienia wymaga odległość do najbliższej
/// stacji, i hamuje wtedy, gdy odpowiedź przekroczy próg. Punkt hamowania nie jest
/// więc parametrem — jest **wynikiem**, i to takim, który zmienia się z prędkością,
/// masą i pochyleniem, bo zmienia się razem z nimi wymagane opóźnienie.</para>
///
/// <para><b>Co to daje.</b> Czas jazdy między stacjami przestaje być liczbą wpisaną
/// do scenariusza i staje się przewidywaniem modelu — porównywalnym z rozkładem STIB
/// zmierzonym w T-113 (`build/timetable.json`, pole `segments`). Błąd zatrzymania jest
/// mierzony, a nie zakładany: skład staje tam, gdzie fizyka go zatrzyma.</para>
///
/// <para><b>Czego tu świadomie nie ma.</b> Ograniczeń prędkości wzdłuż osi — w
/// `data/track/*.json` pole `speed_limits` jest **pustą listą we wszystkich sześciu
/// pakietach** i nie ma dla nich źródła. Przejazd dostaje więc jedno ograniczenie na
/// całą oś, jako jawne założenie wołającego. Nie ma też sygnalizacji (T-313) ani
/// innych składów (T-320): ten przejazd jest sam na linii.</para>
/// </summary>
public sealed class LineRun
{
    /// <summary>
    /// Bezpiecznik pętli: godzina symulacji. Przejazd pakietu A z zatrzymaniami trwa
    /// ok. 11 minut, więc limit łapie tylko przebieg, który utknął.
    /// </summary>
    public const long DefaultStepBudget = 60 * 60 * FixedStep.SimulationHertz;

    private readonly TrainController _controller;
    private readonly BrakingPointSolver _solver;
    private readonly FixedStep _step;

    /// <summary>Przejazd zbudowany z modelu pojazdu.</summary>
    public LineRun(VehicleModel model)
        : this(new TrainController(model), new BrakingPointSolver(model), FixedStep.Simulation)
    {
    }

    /// <summary>Przejazd ze złożonych osobno składników.</summary>
    public LineRun(TrainController controller, BrakingPointSolver solver, FixedStep step)
    {
        ArgumentNullException.ThrowIfNull(controller);
        ArgumentNullException.ThrowIfNull(solver);
        step.RequireValid();

        _controller = controller;
        _solver = solver;
        _step = step;
    }

    /// <summary>Przejazd M7.</summary>
    public static LineRun M7 { get; } = new(VehicleModel.M7);

    /// <summary>Kontroler prowadzący ten przejazd.</summary>
    public TrainController Controller => _controller;

    /// <summary>Krok stały użyty przez przejazd.</summary>
    public FixedStep TimeStep => _step;

    /// <summary>
    /// Przejazd osi od pierwszej do ostatniej stacji.
    /// </summary>
    /// <param name="axis">Oś z chainage stacji.</param>
    /// <param name="conditions">Masa, pochylenie, przyczepność, otoczenie toru.</param>
    /// <param name="settings">Założenia przejazdu — wszystkie bez źródła, patrz <see cref="LineRunSettings"/>.</param>
    /// <param name="stepBudget">Bezpiecznik pętli.</param>
    /// <summary>
    /// Ślad przejazdu: wołany po każdym kroku, gdy podany. Istnieje po to, żeby różnicę
    /// wobec profilu idealnego dało się **zobaczyć**, a nie tylko zmierzyć na końcu.
    /// </summary>
    /// <param name="TimeSeconds">Czas od początku przejazdu.</param>
    /// <param name="ChainageM">Chainage czoła składu.</param>
    /// <param name="SpeedMps">Prędkość po kroku.</param>
    /// <param name="BrakeRateMps2">Opóźnienie hamulca, jakie faktycznie działa.</param>
    /// <param name="Command">Polecenie użyte w tym kroku.</param>
    /// <param name="Phase">Faza drzwi, gdy trwa postój.</param>
    public readonly record struct TracePoint(
        double TimeSeconds, double ChainageM, double SpeedMps,
        double BrakeRateMps2, DriverCommand Command, DoorPhase Phase);

    public LineRunResult Run(
        TrackAxis axis,
        RunConditions conditions,
        LineRunSettings settings,
        long stepBudget = DefaultStepBudget,
        Action<TracePoint>? trace = null)
    {
        ArgumentNullException.ThrowIfNull(axis);
        ArgumentNullException.ThrowIfNull(conditions);
        ArgumentNullException.ThrowIfNull(settings);
        if (axis.Stations.Count < 2)
        {
            throw new ArgumentOutOfRangeException(
                nameof(axis), axis.Stations.Count,
                "Przejazd z zatrzymaniami wymaga co najmniej dwóch stacji na osi.");
        }

        var stations = axis.Stations;
        var start = stations[0].ChainageM;
        var cycle = new DoorCycle(settings.PassengerExchangeSeconds);
        var trigger = settings.BrakeUsageFraction * _controller.ServiceBrakeMps2;

        var state = DriveState.AtRest;
        var calls = new List<StationCall>(stations.Count);
        var next = 1;
        var topSpeed = 0.0;
        var departedAtSeconds = 0.0;
        var departedFromM = start;
        var braking = false;
        StationStop? stop = null;

        while (state.Steps < stepBudget && next < stations.Count)
        {
            var chainage = start + state.DistanceM;
            var target = stations[next].ChainageM;

            if (stop is null
                && state.SpeedMps <= 0.0
                && chainage >= target - settings.StopWindowM
                && chainage - departedFromM >= settings.StopWindowM)
            {
                stop = new StationStop(cycle, _step);
                calls.Add(new StationCall(
                    stations[next].Name,
                    stations[next].StopId,
                    target,
                    chainage,
                    chainage - target,
                    state.TimeSeconds(_step),
                    double.NaN,
                    state.TimeSeconds(_step) - departedAtSeconds,
                    chainage - departedFromM,
                    topSpeed));
            }

            if (stop is not null)
            {
                // Postój. `Filter` jest jedynym miejscem, które posuwa licznik cyklu drzwi,
                // więc musi zostać zawołane dokładnie raz na krok. Hamulca nie zeruje
                // celowo — trzymanie składu na postoju należy do wołającego.
                var held = stop.Filter(state, DriverCommand.FullServiceBrake);
                var phase = stop.Phase;
                state = _controller.Advance(
                    state, conditions, held, settings.SpeedLimitMps, _step, out _);
                trace?.Invoke(new TracePoint(
                    state.TimeSeconds(_step), start + state.DistanceM, state.SpeedMps,
                    state.BrakeRateMps2, held, phase));

                if (stop.Finished)
                {
                    calls[^1] = calls[^1] with { DepartureSeconds = state.TimeSeconds(_step) };
                    departedAtSeconds = state.TimeSeconds(_step);
                    departedFromM = start + state.DistanceM;
                    topSpeed = 0.0;
                    braking = false;
                    stop = null;
                    next++;
                }

                continue;
            }

            var command = Drive(state, conditions, target - chainage, trigger, settings, braking);
            braking |= command.Brake > 0.0;
            state = _controller.Advance(
                state, conditions, command, settings.SpeedLimitMps, _step, out _);
            trace?.Invoke(new TracePoint(
                state.TimeSeconds(_step), start + state.DistanceM, state.SpeedMps,
                state.BrakeRateMps2, command, DoorPhase.Closed));
            if (state.SpeedMps > topSpeed)
            {
                topSpeed = state.SpeedMps;
            }
        }

        var reason = next >= stations.Count ? "arrived" : "step-budget";
        var last = calls.Count > 0 ? calls[^1] : default;
        return new LineRunResult(
            axis.Id,
            calls,
            last.ArrivalSeconds,
            last.StoppedAtChainageM - start,
            SumDwell(calls),
            state.Steps,
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
    private DriverCommand Drive(
        DriveState state, RunConditions conditions, double remainingM, double triggerMps2,
        LineRunSettings settings, bool alreadyBraking)
    {
        if (remainingM <= 0.0)
        {
            // Stacja minięta z prędkością. Pełny hamulec; błąd zatrzymania to zmierzy
            // i wyjdzie w raporcie jako dodatni StopErrorM, a nie zniknie.
            return DriverCommand.FullServiceBrake;
        }

        if (state.SpeedMps <= 0.0)
        {
            return DriverCommand.FullPower;
        }

        if (!_solver.TryRequiredDeceleration(state.SpeedMps, 0.0, remainingM, out var need))
        {
            // Poniżej minimalnej drogi wynikającej ze zrywu rozwiązania nie ma — wtedy
            // nawet pełny hamulec nie zatrzyma składu na czas i „prawie" nie jest odpowiedzią.
            return DriverCommand.FullServiceBrake;
        }

        if (!alreadyBraking && need.DecelerationMps2 < triggerMps2)
        {
            return state.SpeedMps < settings.SpeedLimitMps
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
        var required = state.SpeedMps * state.SpeedMps / (2.0 * remainingM);

        // Polecenie to opóźnienie **hamulca**, a nie całkowite: skład zwalnia też oporami
        // ruchu i składową pochylenia, a te działają niezależnie od nastawy. Żeby sumaryczne
        // opóźnienie wyszło takie, o jakie prosi kinematyka, hamulec dostaje różnicę.
        var resistance = _controller.Dynamics.Resistance.ForceN(
            conditions.MassKg, state.SpeedMps, conditions.Environment);
        var grade = TrainDynamics.GradeForceN(conditions.MassKg, conditions.GradePercent);
        var passive = (resistance + grade) / _controller.Dynamics.EffectiveMassKg(conditions.MassKg);

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
