using System;
using MetroBxl.Sim.Physics;

namespace MetroBxl.Sim.Train;

/// <summary>
/// Przejazd prowadzony przez zapisany scenariusz. Jedna pętla, dwóch gospodarzy:
/// scena Godota woła <see cref="Step"/> z pętli klatkowej, <c>src/Sim.Runner</c> woła
/// je z gołego <c>while</c>. Stan po N krokach jest z definicji ten sam, bo krok jest
/// stały, a polecenie zależy wyłącznie od stanu — nie od czasu ściennego ani od klatek.
/// </summary>
public sealed class ScenarioDrive
{
    /// <summary>
    /// Bezpiecznik pętli: 30 minut symulacji. Przejazd pakietu A trwa ok. 5,5 minuty,
    /// więc limit łapie tylko przebieg, który utknął — na przykład gdy trakcja nie
    /// pokonuje oporów. To ta sama rola, co limit 300 s w <see cref="AccelerationRun"/>.
    /// </summary>
    public const long DefaultStepBudget = 30 * 60 * FixedStep.SimulationHertz;

    private readonly TrainController _controller;
    private readonly DriveScenario _scenario;
    private readonly RunConditions _conditions;
    private readonly FixedStep _step;
    private readonly long _stepBudget;

    /// <summary>Przejazd M7 zbudowany z modelu pojazdu.</summary>
    public ScenarioDrive(
        VehicleModel model,
        DriveScenario scenario,
        RunConditions conditions,
        FixedStep step,
        long stepBudget = DefaultStepBudget)
        : this(new TrainController(model), scenario, conditions, step, stepBudget)
    {
    }

    /// <summary>Przejazd z gotowym kontrolerem.</summary>
    public ScenarioDrive(
        TrainController controller,
        DriveScenario scenario,
        RunConditions conditions,
        FixedStep step,
        long stepBudget = DefaultStepBudget)
    {
        ArgumentNullException.ThrowIfNull(controller);
        ArgumentNullException.ThrowIfNull(scenario);
        ArgumentNullException.ThrowIfNull(conditions);
        step.RequireValid();
        if (stepBudget <= 0)
        {
            throw new ArgumentOutOfRangeException(nameof(stepBudget), stepBudget, "Bezpiecznik pętli musi być dodatni.");
        }

        _controller = controller;
        _scenario = scenario;
        _conditions = conditions;
        _step = step;
        _stepBudget = stepBudget;

        State = DriveState.AtRest;
        Phase = scenario.SegmentAt(scenario.StartChainageM).Label;
        Command = scenario.SegmentAt(scenario.StartChainageM).Command;
    }

    /// <summary>Scenariusz prowadzący ten przejazd.</summary>
    public DriveScenario Scenario => _scenario;

    /// <summary>Warunki przebiegu.</summary>
    public RunConditions Conditions => _conditions;

    /// <summary>Krok stały użyty przez przejazd.</summary>
    public FixedStep TimeStep => _step;

    /// <summary>Stan ruchu.</summary>
    public DriveState State { get; private set; }

    /// <summary>Polecenie użyte w ostatnim wykonanym kroku.</summary>
    public DriverCommand Command { get; private set; }

    /// <summary>Nazwa fazy scenariusza w ostatnim kroku.</summary>
    public string Phase { get; private set; }

    /// <summary>Przyspieszenie z ostatniego kroku, ze znakiem.</summary>
    public double AccelerationMps2 { get; private set; }

    /// <summary>Chainage czoła składu.</summary>
    public double ChainageM => _scenario.StartChainageM + State.DistanceM;

    /// <summary>Czy przejazd się skończył.</summary>
    public bool Finished { get; private set; }

    /// <summary>Dlaczego się skończył: <c>stopped</c> albo <c>step-budget</c>.</summary>
    public string FinishReason { get; private set; } = string.Empty;

    /// <summary>
    /// Jeden krok. Zwraca <c>false</c>, gdy przejazd jest już skończony — wtedy stan
    /// nie zmienia się więcej, więc wołanie w pętli klatkowej jest bezpieczne.
    /// </summary>
    public bool Step()
    {
        if (Finished)
        {
            return false;
        }

        var segment = _scenario.SegmentAt(ChainageM);
        Phase = segment.Label;
        Command = segment.Command;

        var before = State;
        State = _controller.Advance(before, _conditions, Command, _scenario.SpeedLimitMps, _step, out var forces);
        AccelerationMps2 = forces.AccelerationMps2;

        // Zatrzymanie liczy się dopiero po ruszeniu: na starcie skład też stoi.
        if (State.SpeedMps <= 0.0 && before.DistanceM > 0.0)
        {
            Finished = true;
            FinishReason = "stopped";
        }
        else if (State.Steps >= _stepBudget)
        {
            Finished = true;
            FinishReason = "step-budget";
        }

        return true;
    }

    /// <summary>Wykonuje kroki aż do końca przejazdu; zwraca liczbę wykonanych kroków.</summary>
    public long RunToEnd()
    {
        var executed = 0L;
        while (Step())
        {
            executed++;
        }

        return executed;
    }
}
