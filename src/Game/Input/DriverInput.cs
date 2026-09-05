using Godot;
using MetroBxl.Sim.Train;

namespace MetroBxl.Game.Input;

/// <summary>
/// Odczyt klawiatury na <see cref="DriverKeys"/>. Cała warstwa wejścia zadania T-400.
///
/// <para><b>Ta klasa nie liczy już nic.</b> Do 05.09.2026 miała metodę
/// <c>Poll(deltaSeconds)</c>, która przesuwała nastawnik o <c>tempo · Δt_klatki</c>
/// i była wołana raz na KLATKĘ — czyli położenie dźwigni zależało od liczby klatek,
/// a nie od czasu symulacji. Zmierzony skutek: ta sama sekwencja klawiszy przez 60 s
/// dawała 566,407284 m przy 120 kl./s i 566,641450 m przy 60 kl./s, rozjazd 0,234166 m
/// przy bramkach porównujących telemetrię z progiem <b>0</b>
/// (<c>reports/droga-do-grywalnosci.md</c> §5.1).</para>
///
/// <para>Przesuw dźwigni przeniósł się do <see cref="DriverNotch"/> w rdzeniu i jest
/// wykonywany <b>raz na krok symulacji</b>. Tutaj zostało to, czego bez silnika zrobić
/// nie można: zapytanie klawiatury, co jest trzymane. To jest jedyna rzecz, której
/// silnik nie potrafi podać częściej niż raz na klatkę — i dlatego jedyna, która
/// zostaje po tej stronie.</para>
///
/// <para>Klawisze są odczytywane fizycznie (<see cref="Godot.Input.IsPhysicalKeyPressed"/>),
/// czyli po położeniu na klawiaturze, a nie po znaku — układ AZERTY, w Brukseli
/// nieprzypadkowy, nie przestawia wtedy sterowania. Mapa akcji <c>InputMap</c>
/// z konfiguracją w projekcie należy do zadania o sterowaniu (G-3), nie tutaj.</para>
/// </summary>
public sealed class DriverInput
{
    /// <summary>
    /// Opis sterowania do wypisania w HUD.
    ///
    /// <para>Nazwa klawisza hamulca awaryjnego jest sklejana z
    /// <see cref="EmergencyBrake.KeyName"/>, a nie wpisana tu drugi raz — wiersz HUD-u
    /// i ten opis mówią wtedy o tym samym klawiszu z definicji.</para>
    ///
    /// <para><b>Ta stała jest dziś martwa</b> — nic jej nie woła, i to jest zadanie G-3
    /// (mapa akcji <c>InputMap</c> plus wiersz pomocy), nie to. Nowy klawisz jest tu
    /// dopisany właśnie dlatego: stała bez niego rozjechałaby się ze sterowaniem
    /// jeszcze zanim ktokolwiek zacznie ją pokazywać.</para>
    /// </summary>
    public const string Help = "W ciąg  ·  S hamulec  ·  X wybieg  ·  "
        + EmergencyBrake.KeyName + " hamulec awaryjny (= pełny służbowy)  ·  "
        + "C widok  ·  R od nowa  ·  Esc wyjście";

    /// <summary>Stan klawiszy odczytany ostatnim <see cref="Read"/>.</summary>
    public DriverKeys Keys { get; private set; } = DriverKeys.None;

    /// <summary>
    /// Odczytuje trzymane klawisze. Wołane raz na klatkę — częściej się nie da, bo
    /// silnik nie ma historii klawiatury wewnątrz klatki, a zmyślanie jej byłoby
    /// wymyślaniem danych wejściowych gracza.
    /// </summary>
    /// <returns>Stan trzymanych klawiszy w tej klatce.</returns>
    public DriverKeys Read()
    {
        Keys = new DriverKeys(
            Godot.Input.IsPhysicalKeyPressed(Key.W) || Godot.Input.IsPhysicalKeyPressed(Key.Up),
            Godot.Input.IsPhysicalKeyPressed(Key.S) || Godot.Input.IsPhysicalKeyPressed(Key.Down),
            Godot.Input.IsPhysicalKeyPressed(Key.X),

            // Spacja, bo jest jedynym dużym klawiszem poza zestawem już zajętym
            // (W/S/X prowadzenie, C widok, R od nowa, Esc wyjście) i trafia się w nią
            // bez patrzenia — a hamulec awaryjny jest gestem, w którym patrzenie na
            // klawiaturę jest dokładnie tym, czego się nie robi. Odczyt jest FIZYCZNY,
            // tak samo jak reszta: na AZERTY spacja leży tam, gdzie na QWERTY.
            Godot.Input.IsPhysicalKeyPressed(Key.Space));
        return Keys;
    }

    /// <summary>Zapomina odczytany stan — do resetu przejazdu.</summary>
    public void Clear() => Keys = DriverKeys.None;
}
