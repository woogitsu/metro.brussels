using System;
using MetroBxl.Sim.Physics;

namespace MetroBxl.Sim.Train;

/// <summary>
/// Jeden krok składu prowadzonego przez maszynistę.
///
/// <para><b>To nie jest druga fizyka.</b> Siła pociągowa, opory Davisa, składowa
/// pochylenia i masa efektywna pochodzą w całości z <c>MetroBxl.Sim.Physics</c> —
/// z tych samych obiektów, które w T-310 odtwarzają <c>tools/physics/reference.py</c>
/// co do bitu. Ta klasa dokłada dokładnie dwie rzeczy, których w rdzeniu nie było,
/// bo przebieg z T-310 nie miał maszynisty:</para>
///
/// <list type="number">
/// <item>trakcję częściową — <c>F = nastawnik · F_pełna</c>;</item>
/// <item>hamulec jako polecenie — kinematyczne opóźnienie z ograniczeniem zrywu.</item>
/// </list>
///
/// <para><b>Skąd różnica wobec <see cref="TrainDynamics.Advance"/>:</b> tamten krok
/// obcina przyspieszenie od dołu do zera, bo przebieg rozruchowy z definicji przyspiesza.
/// Prowadzony skład musi umieć zwalniać na wybiegu i pod hamulcem, więc tu obcięcia
/// nie ma; jest za to obcięcie prędkości do zera, czyli model nadal nie odtacza się
/// w tył (hamulca postojowego nie ma — to zakres T-311).</para>
///
/// <para><b>Parytet:</b> przy <c>throttle = 1</c>, <c>brake = 0</c> i rozruchu z postoju
/// przyspieszenie jest zawsze dodatnie, mnożenie przez 1,0 i odejmowanie 0,0 są dokładne,
/// a kolejność działań jest ta sama — więc przebieg wychodzi **co do bitu** taki sam
/// jak <see cref="AccelerationRun.ToSpeed"/>. Sprawdza to <c>src/Sim.Runner</c>.</para>
///
/// <para><b>Model hamulca</b> jest ten sam, co w <see cref="ServiceBrakingRun"/>: zadane
/// opóźnienie z <c>docs/02-simulation.md</c> (1,10 m/s² służbowe, zryw 0,75 m/s³),
/// **niezależne od masy i przyczepności**. To świadome uproszczenie modelu projektowego,
/// nie pominięcie — udział hamulca ED i P, wpływ masy i krzywe bezpieczeństwa to T-311.</para>
/// </summary>
public sealed class TrainController
{
    private readonly TrainDynamics _dynamics;
    private readonly double _serviceBrakeMps2;
    private readonly double _jerkMps3;

    /// <summary>Kontroler dla modelu pojazdu.</summary>
    public TrainController(VehicleModel model)
        : this(
            new TrainDynamics(model ?? throw new ArgumentNullException(nameof(model))),
            model.DesignServiceBrakeMps2,
            model.DesignJerkMps3)
    {
    }

    /// <summary>Kontroler ze złożonych osobno składników.</summary>
    /// <param name="dynamics">Dynamika z rdzenia — trakcja, opory, masa efektywna.</param>
    /// <param name="serviceBrakeMps2">Pełne opóźnienie hamulca służbowego.</param>
    /// <param name="jerkMps3">Ograniczenie zrywu przy narastaniu i zdejmowaniu hamulca.</param>
    public TrainController(TrainDynamics dynamics, double serviceBrakeMps2, double jerkMps3)
    {
        ArgumentNullException.ThrowIfNull(dynamics);
        if (!double.IsFinite(serviceBrakeMps2) || serviceBrakeMps2 <= 0.0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(serviceBrakeMps2), serviceBrakeMps2, "Opóźnienie hamulca musi być dodatnie i skończone.");
        }

        if (!double.IsFinite(jerkMps3) || jerkMps3 <= 0.0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(jerkMps3), jerkMps3, "Ograniczenie zrywu musi być dodatnie i skończone.");
        }

        _dynamics = dynamics;
        _serviceBrakeMps2 = serviceBrakeMps2;
        _jerkMps3 = jerkMps3;
    }

    /// <summary>Kontroler M7.</summary>
    public static TrainController M7 { get; } = new(VehicleModel.M7);

    /// <summary>Dynamika użyta przez ten kontroler.</summary>
    public TrainDynamics Dynamics => _dynamics;

    /// <summary>Pełne opóźnienie hamulca służbowego.</summary>
    public double ServiceBrakeMps2 => _serviceBrakeMps2;

    /// <summary>Ograniczenie zrywu hamulca.</summary>
    public double JerkMps3 => _jerkMps3;

    /// <summary>
    /// Jeden krok prowadzonego składu.
    /// </summary>
    /// <param name="state">Stan przed krokiem.</param>
    /// <param name="conditions">Masa, pochylenie, przyczepność, otoczenie toru.</param>
    /// <param name="command">Polecenie maszynisty w tym kroku.</param>
    /// <param name="speedLimitMps">Ograniczenie prędkości; prędkość jest do niego obcinana.</param>
    /// <param name="step">Krok stały symulacji.</param>
    /// <param name="forces">Rozbicie sił, jakie model naprawdę policzył w tym kroku.</param>
    /// <returns>Stan po kroku.</returns>
    public DriveState Advance(
        DriveState state,
        RunConditions conditions,
        DriverCommand command,
        double speedLimitMps,
        FixedStep step,
        out StepForces forces)
    {
        ArgumentNullException.ThrowIfNull(conditions);
        step.RequireValid();

        if (!double.IsFinite(speedLimitMps) || speedLimitMps < 0.0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(speedLimitMps), speedLimitMps, "Ograniczenie prędkości musi być nieujemne i skończone.");
        }

        var clamped = command.Clamped();
        var throttle = clamped.EffectiveThrottle;

        var tractionFull = _dynamics.Traction.ForceN(state.SpeedMps, conditions.MassKg, conditions.Adhesion);
        var traction = throttle * tractionFull;
        var resistance = _dynamics.Resistance.ForceN(conditions.MassKg, state.SpeedMps, conditions.Environment);
        var grade = TrainDynamics.GradeForceN(conditions.MassKg, conditions.GradePercent);
        var net = traction - resistance - grade;
        var mechanical = net / _dynamics.EffectiveMassKg(conditions.MassKg);

        var brakeRate = RampBrake(state.BrakeRateMps2, clamped.Brake * _serviceBrakeMps2, step.Seconds);
        var acceleration = mechanical - brakeRate;

        var speed = state.SpeedMps + (acceleration * step.Seconds);
        if (speed > speedLimitMps)
        {
            speed = speedLimitMps;
        }

        if (speed < 0.0)
        {
            speed = 0.0;
        }

        var distance = state.DistanceM + (speed * step.Seconds);

        forces = new StepForces(traction, resistance, grade, net, acceleration);
        return new DriveState(state.Steps + 1, speed, distance, brakeRate);
    }

    /// <summary>
    /// Narastanie i zdejmowanie hamulca z ograniczeniem zrywu. Skok opóźnienia w jednym
    /// kroku nie może przekroczyć <c>zryw · dt</c> — inaczej model dawałby nieskończony
    /// zryw, którego <c>docs/02-simulation.md</c> jawnie zabrania.
    /// </summary>
    private double RampBrake(double current, double target, double dt)
    {
        var maximumChange = _jerkMps3 * dt;
        var difference = target - current;
        if (difference > maximumChange)
        {
            return current + maximumChange;
        }

        if (difference < -maximumChange)
        {
            return current - maximumChange;
        }

        return target;
    }
}
