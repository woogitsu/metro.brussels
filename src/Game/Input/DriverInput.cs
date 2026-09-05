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
/// <para>Klawisze idą przez <b>akcje <c>InputMap</c></b>, a nie po kodach klawiszy.
/// Do 05.09.2026 stało tu <c>Godot.Input.IsPhysicalKeyPressed(Key.W)</c> i pięć
/// podobnych wierszy; zmiana klawisza wymagała wtedy poprawki w tym pliku,
/// w <c>FirstRun.HandleViewKeys</c> i w opisie sterowania — w trzech miejscach, które
/// nic o sobie nie wiedziały. Teraz nazwy akcji i klawisze pod nimi są jedną tabelą
/// w <see cref="DriverActions"/>, a przypisania siedzą w <c>project.godot</c>.</para>
///
/// <para>Odczyt fizyczny NIE ZNIKA — przenosi się do <c>project.godot</c>, gdzie każde
/// zdarzenie ma <c>physical_keycode</c> przy <c>keycode</c> równym zeru. Klawisz jest
/// więc dalej brany po położeniu, a nie po znaku, i układ AZERTY, w Brukseli
/// nieprzypadkowy, dalej nie przestawia sterowania.</para>
/// </summary>
public sealed class DriverInput
{
    /// <summary>
    /// Opis sterowania wypisywany w HUD-zie — składany z tej samej tabeli
    /// <see cref="DriverActions.All"/>, z której biorą się przypisania klawiszy.
    ///
    /// <para><b>Do 05.09.2026 była to stała MARTWA</b>: nic jej nie wołało, więc gracz
    /// nie miał skąd wiedzieć, czym prowadzi, a napis mógł opisywać klawisze, których
    /// scena nie czytała — i opisywał, bo hamulec awaryjny dopisano do niego „na zapas".
    /// Teraz wiersz wychodzi na ekran (<c>Hud.Update</c>, siódmy wiersz) i nie jest
    /// osobnym napisem: zmiana klawisza w tabeli przechodzi do opisu i do
    /// <c>project.godot</c> naraz albo nie przechodzi nigdzie.</para>
    /// </summary>
    public static string Help => DriverActions.Help;

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
        // Warianty klawiszy (strzałki obok liter) siedzą w przypisaniu akcji, a nie
        // w tym `||`. Jedna akcja to jedno pytanie do silnika, bez względu na to, ile
        // klawiszy jest pod nią podpiętych — i to jest cała różnica wobec wersji
        // sprzed 05.09.2026.
        Keys = new DriverKeys(
            Godot.Input.IsActionPressed(DriverActions.Power),
            Godot.Input.IsActionPressed(DriverActions.Brake),
            Godot.Input.IsActionPressed(DriverActions.Coast),

            // Spacja, bo jest jedynym dużym klawiszem poza zestawem już zajętym
            // (W/S/X prowadzenie, C widok, R od nowa, Esc wyjście) i trafia się w nią
            // bez patrzenia — a hamulec awaryjny jest gestem, w którym patrzenie na
            // klawiaturę jest dokładnie tym, czego się nie robi. Sam klawisz stoi
            // w `DriverActions.All`, tu jest tylko nazwa akcji.
            Godot.Input.IsActionPressed(DriverActions.Emergency));
        return Keys;
    }

    /// <summary>Zapomina odczytany stan — do resetu przejazdu.</summary>
    public void Clear() => Keys = DriverKeys.None;
}
