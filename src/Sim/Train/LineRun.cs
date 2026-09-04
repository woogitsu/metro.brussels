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

    /// <summary>
    /// Przejazd osi od pierwszej do ostatniej stacji.
    /// </summary>
    /// <param name="axis">Oś z chainage stacji.</param>
    /// <param name="conditions">Masa, pochylenie, przyczepność, otoczenie toru.</param>
    /// <param name="settings">Założenia przejazdu — wszystkie bez źródła, patrz <see cref="LineRunSettings"/>.</param>
    /// <param name="stepBudget">Bezpiecznik pętli.</param>
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

        var drive = new LineDrive(axis, conditions, settings, _controller, _solver, _step);
        while (drive.Steps < stepBudget && !drive.Finished)
        {
            drive.Step(trace);
        }

        return drive.Result(drive.Finished ? "arrived" : "step-budget");
    }

}
