using System.Globalization;
using Godot;
using MetroBxl.Game.UI;
using MetroBxl.Sim.Train;

namespace MetroBxl.Game.Input;

/// <summary>
/// Hamulec awaryjny jako <b>gest sterowania</b> i jako <b>zdanie w HUD-zie</b> — i nic
/// poza tym.
///
/// <para><b>Czego tu nie ma i dlaczego.</b> Hamulec awaryjny jako polecenie maszynisty
/// w tym modelu nie istnieje: <see cref="DriverCommand"/> ma nastawnik i hamulec
/// SŁUŻBOWY, a <c>Brake = 1</c> to pełne hamowanie służbowe — rdzeń mówi to wprost.
/// Decyzja właściciela z 05.09.2026: gracz dostaje osobny klawisz, który robi
/// <b>dokładnie to samo</b> co pełny hamulec, a HUD ma to powiedzieć wprost, zamiast
/// udawać fizykę, której nie ma. Osobny stopień w <see cref="DriverCommand"/> byłby
/// tym udawaniem.</para>
///
/// <para><b>Dlaczego to jest osobny plik BEZ GODOTA.</b> Ta sama decyzja i ten sam powód,
/// co przy <see cref="RunPlan"/> i <see cref="RunHeader"/>: napis, który ma mówić prawdę
/// o liczbie, da się przybić testem tylko wtedy, gdy złożenie tego napisu nie wymaga
/// uruchomionego silnika. <c>tests/Game.Tests</c> woła <see cref="Notice"/> wprost
/// i porównuje liczbę w napisie z poleceniem, które w tym samym kroku wyszło
/// z <see cref="DriverNotch"/>.</para>
/// </summary>
public static class EmergencyBrake
{
    /// <summary>
    /// Nazwa klawisza w opisie sterowania i w wierszu HUD-u. Jedna kopia napisu:
    /// <see cref="DriverInput.Help"/> skleja go z tej stałej, a nie wpisuje obok.
    ///
    /// <para><b>Ta jedna nazwa klawisza idzie z katalogu tekstów</b> (6.D99), a nazwy
    /// w <see cref="DriverActions.All"/> — nie. Różnica jest w klawiaturze, nie
    /// w kodzie: na klawiszu Esc napisane jest „Esc", a na spacji nie jest napisane
    /// nic, więc „Spacja" to polski rzeczownik i jako taki należy do katalogu. Stała
    /// przestała być <c>const</c>, bo katalog czyta się w czasie wykonania; nikt jej
    /// nie używa w miejscu wymagającym stałej kompilacji.</para>
    /// </summary>
    public static readonly string KeyName = KeyNames.For(Key.Space);

    /// <summary>
    /// Wiersz HUD-u dla trzymanego hamulca awaryjnego; pusty napis, gdy klawisz nie
    /// jest trzymany.
    ///
    /// <para><b>Liczba w napisie pochodzi z POLECENIA</b>, którym w tym kroku pojechał
    /// kontroler, a nie ze stałej 1,00 wpisanej w tekst. Ta sama zasada, co
    /// w <see cref="RunHeader"/>: napis obok liczby rozjeżdża się z nią przy pierwszej
    /// zmianie, a napis o hamulcu awaryjnym rozjechałby się cicho — hamulec i tak
    /// hamuje, więc nikt by nie zauważył, że mówi o innej wartości.</para>
    /// </summary>
    /// <param name="keys">Stan klawiszy w tym kroku.</param>
    /// <param name="command">Polecenie, które z tego stanu wyszło.</param>
    /// <param name="driverControls">Czy klawisz steruje obserwowanym składem.</param>
    /// <returns>Wiersz do pokazania albo pusty napis.</returns>
    public static string Notice(DriverKeys keys, DriverCommand command, bool driverControls = true)
        => driverControls && keys.Emergency
            ? UiText.Format(
                "hud.emergency-brake",
                KeyName,
                command.Brake.ToString("F2", CultureInfo.InvariantCulture))
            : string.Empty;
}
