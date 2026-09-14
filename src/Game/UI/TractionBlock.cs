using MetroBxl.Sim.Signalling;

namespace MetroBxl.Game.UI;

/// <summary>
/// Wiersz HUD-u o blokadzie trakcji: CZY nastawnik jazdy jest w tej chwili odcięty
/// i KTÓRY z dwóch filtrów go odcina.
///
/// <para><b>Dlaczego osobny plik BEZ GODOTA.</b> Ta sama decyzja i ten sam powód, co
/// przy <see cref="MetroBxl.Game.SignallingHud"/>, <c>RunPlan</c> i <c>RunHeader</c>:
/// napis złożony ze stanu przejazdu da się sprawdzić testem jednostkowym tylko wtedy,
/// gdy nie wymaga uruchomionego silnika.</para>
///
/// <para><b>Ten wiersz NICZEGO NIE LICZY — i to jest cała treść tego pliku.</b> Pole
/// „Czego NIE wolno zrobić" pozycji MB-03 zakazuje drugiego źródła prawdy
/// o hamowaniu; ta sama zasada dotyczy blokady jazdy. Filtry są w rdzeniu
/// i są DOKŁADNIE DWA — sprawdzone <c>grep</c>em po całym <c>src/Sim/</c>:</para>
/// <list type="number">
/// <item><see cref="MetroBxl.Sim.Train.StationStop.Filter"/> zeruje nastawnik, gdy
///   <c>DoorCycle.TractionAllowed(Phase)</c> jest fałszem
///   (<c>src/Sim/Train/StationStop.cs:84-86</c>, jedyne miejsce
///   <c>requested with { Throttle = 0.0 }</c>);</item>
/// <item><see cref="ProtectionDecision.Apply"/> podmienia całe polecenie przy
///   <see cref="ProtectionAction.ServiceIntervention"/> i
///   <see cref="ProtectionAction.EmergencyIntervention"/>
///   (<c>src/Sim/Signalling/TrainProtection.cs:108-114</c>).</item>
/// </list>
///
/// <para><b>Trzeciego filtru nie ma, a ograniczenie prędkości nim NIE JEST:</b>
/// <c>TrainController.Advance</c> obcina PRĘDKOŚĆ po kroku
/// (<c>src/Sim/Train/TrainController.cs:128-130</c>), nastawnika nie rusza.</para>
///
/// <para><b>Kolejność ramion jest kolejnością FILTRÓW, a nie gustem.</b>
/// <c>FirstRun.StepOnce</c> woła najpierw filtr stacji (<c>:1259</c>), a ochronę
/// OSTATNIĄ (<c>:1267</c>) — więc gdy blokują obie, poleceniem kontrolera rządzi
/// ochrona i to ona ma być nazwana. Odwrotna kolejność mówiłaby graczowi „zamknij
/// drzwi", gdy w rzeczywistości hamuje za niego ATP.</para>
/// </summary>
public static class TractionBlock
{
    /// <summary>
    /// Czy nastawnik jazdy jest odcięty — ODCZYT z dwóch właścicieli, nie rachunek.
    /// </summary>
    /// <param name="doorsAllowTraction">
    /// <c>StationService.TractionAllowed</c> z tego samego kroku. Poza postojem jest
    /// prawdą, bo <c>Phase</c> zwraca wtedy <c>DoorPhase.Closed</c>.
    /// </param>
    /// <param name="decision">
    /// <c>CabProtection.Decision</c> z tego samego kroku; <c>null</c> znaczy „przejazd
    /// bez sygnalizacji albo przed pierwszym krokiem", czyli ochrona nie ma czego
    /// odciąć.
    /// </param>
    public static bool Blocked(bool doorsAllowTraction, ProtectionDecision? decision) =>
        !doorsAllowTraction
        || (decision is ProtectionDecision d && d.Action != ProtectionAction.None);

    /// <summary>
    /// Wiersz dla gracza; PUSTY NAPIS, gdy trakcja jest wolna.
    ///
    /// <para><b>Milczenie znaczy tu „jedź", i to jest wybór, a nie brak.</b> Wiersz
    /// „trakcja wolna" wyświetlany przez cały przejazd zajmowałby pasmo pierwsze,
    /// nie niosąc ani jednej informacji — a to jest dokładnie ta pozycja, która
    /// rozstrzyga, co w paśmie pierwszym stoi. Pusty napis chowa etykietę
    /// (<c>Hud.Update</c> ustawia <c>Visible</c> po długości), więc wiersz pojawia się
    /// wtedy i tylko wtedy, gdy gracz ciągnie i nic się nie dzieje.</para>
    ///
    /// <para><b>Ramienia „nie wiem" tu nie ma i nie może być:</b> filtry są dwa,
    /// oba są sprawdzane, więc trzeci przypadek nie istnieje. Gdyby kiedyś powstał,
    /// zapali się bramka porównująca tę odpowiedź z zachowaniem prawdziwych filtrów
    /// (<c>TractionBlockTests</c>), a nie ten napis.</para>
    /// </summary>
    /// <param name="doorsAllowTraction">Jak w <see cref="Blocked"/>.</param>
    /// <param name="doorPhaseName">
    /// Nazwa fazy drzwi po polsku, złożona po stronie wołającego przez
    /// <c>FirstRun.Faza</c> — HUD jej NIE składa, bo druga kopia mapy faz rozjechałaby
    /// się z pierwszą (ta sama zasada, co przy wierszu stacji w <c>Hud.Update</c>).
    /// </param>
    /// <param name="decision">Jak w <see cref="Blocked"/>.</param>
    public static string Line(
        bool doorsAllowTraction, string doorPhaseName, ProtectionDecision? decision)
    {
        if (decision is ProtectionDecision d && d.Action != ProtectionAction.None)
        {
            // DWA wywołania, a nie jedno z kluczem za `?:`, i to jest rozstrzygnięcie
            // przeniesione żywcem z `FirstRun.StationLine` (6.D99): skan
            // `UiTextTests.Katalog_nie_ma_wpisow_martwych` czyta klucz jako literał
            // WPROST po `UiText.Get(`, więc klucza schowanego za operatorem
            // trójargumentowym NIE WIDZI i melduje go jako martwy. Zmierzone na tym
            // szkicu: wersja z `?:` wywraca tę bramkę na `hud.traction.atp-service`.
            if (d.Action == ProtectionAction.EmergencyIntervention)
            {
                return UiText.Get("hud.traction.atp-emergency");
            }

            return UiText.Get("hud.traction.atp-service");
        }

        if (!doorsAllowTraction)
        {
            return UiText.Format("hud.traction.doors", doorPhaseName);
        }

        return string.Empty;
    }
}
