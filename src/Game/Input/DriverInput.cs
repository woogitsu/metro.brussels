using System;
using Godot;
using MetroBxl.Sim.Train;

namespace MetroBxl.Game.Input;

/// <summary>
/// Klawiatura na <see cref="DriverCommand"/>. Cała warstwa wejścia zadania T-400.
///
/// Klasa **nie liczy fizyki** i nie zna prędkości: zamienia trzymane klawisze na
/// położenie nastawnika i hamulca, a co z tego wynika, decyduje
/// <see cref="TrainController"/> w rdzeniu.
///
/// Klawisze są odczytywane fizycznie (<see cref="Godot.Input.IsPhysicalKeyPressed"/>),
/// czyli po położeniu na klawiaturze, a nie po znaku — układ AZERTY, w Brukseli
/// nieprzypadkowy, nie przestawia wtedy sterowania. Mapa akcji <c>InputMap</c>
/// z konfiguracją w projekcie należy do zadania o sterowaniu, nie do pierwszego przejazdu.
/// </summary>
public sealed class DriverInput
{
    private readonly double _ratePerSecond;

    /// <summary>Wejście z zadanym tempem przestawiania nastawnika.</summary>
    public DriverInput(double ratePerSecond)
    {
        if (!double.IsFinite(ratePerSecond) || ratePerSecond <= 0.0)
        {
            throw new ArgumentOutOfRangeException(nameof(ratePerSecond), ratePerSecond,
                "Tempo przestawiania nastawnika musi być dodatnie.");
        }

        _ratePerSecond = ratePerSecond;
    }

    /// <summary>Bieżące położenie nastawnika i hamulca.</summary>
    public DriverCommand Command { get; private set; } = DriverCommand.Coast;

    /// <summary>Opis sterowania do wypisania w HUD.</summary>
    public const string Help = "W ciąg  ·  S hamulec  ·  X wybieg  ·  C widok  ·  R od nowa  ·  Esc wyjście";

    /// <summary>
    /// Przelicza stan klawiatury na nowe położenie nastawników.
    /// </summary>
    /// <param name="deltaSeconds">Czas od poprzedniego wywołania.</param>
    public DriverCommand Poll(double deltaSeconds)
    {
        var stepValue = _ratePerSecond * deltaSeconds;
        var throttle = Command.Throttle;
        var brake = Command.Brake;

        if (Godot.Input.IsPhysicalKeyPressed(Key.W) || Godot.Input.IsPhysicalKeyPressed(Key.Up))
        {
            // Ciąg zdejmuje hamulec, zanim zacznie narastać — na M7 nie ma pozycji
            // „ciągnij i hamuj naraz" i model jej nie udaje.
            brake = Math.Max(0.0, brake - stepValue);
            if (brake <= 0.0)
            {
                throttle = Math.Min(1.0, throttle + stepValue);
            }
        }
        else if (Godot.Input.IsPhysicalKeyPressed(Key.S) || Godot.Input.IsPhysicalKeyPressed(Key.Down))
        {
            throttle = Math.Max(0.0, throttle - stepValue);
            if (throttle <= 0.0)
            {
                brake = Math.Min(1.0, brake + stepValue);
            }
        }
        else if (Godot.Input.IsPhysicalKeyPressed(Key.X))
        {
            throttle = Math.Max(0.0, throttle - stepValue);
            brake = Math.Max(0.0, brake - stepValue);
        }

        Command = new DriverCommand(throttle, brake).Clamped();
        return Command;
    }

    /// <summary>Ustawia położenie nastawników wprost — do resetu przejazdu.</summary>
    public void Set(DriverCommand command) => Command = command.Clamped();
}
