using System.Collections.Generic;
using Godot;
using MetroBxl.Game.UI;

namespace MetroBxl.Game.Input;

/// <summary>
/// Nazwa klawisza dla kodu fizycznego — jedno miejsce dla nazw, których nie da się
/// wyprowadzić z samego kodu.
///
/// <para><b>Skąd ta klasa (6.D116).</b> Do 11.09.2026 <c>DriverActionsTests</c>
/// porównywało nazwę klawisza z <c>physical_keycode</c> wyłącznie dla nazw
/// JEDNOZNAKOWYCH — kod fizyczny litery jest jej kodem ASCII, więc porównanie robi się
/// bez żadnej tablicy. Dla „Esc" i „Spacji" takiego wyprowadzenia nie ma i obie nazwy
/// stały poza kontrolą: podmiana <c>"Esc"</c> na <c>"Escape"</c> nie zapalała żadnej
/// bramki, a wiersz pomocy zaczynał nazywać klawisz inaczej, niż nazywa go
/// <c>InputMap</c>.</para>
///
/// <para><b>Granica z 6.D83 zostaje nietknięta i to ona dzieli tę tabelę na pół.</b>
/// Na klawiszu Esc jest napisane „Esc" — to odczyt z klawiatury, nie polszczyzna, więc
/// stoi tutaj jako literał. Na spacji nie jest napisane nic, a „Spacja" jest polskim
/// rzeczownikiem, więc przychodzi z katalogu (<c>input.key.space</c>). Tabela wiąże
/// obie z kodem fizycznym, nie zmieniając tego, skąd każda pochodzi.</para>
///
/// <para><b>Czego ta klasa NIE robi:</b> nie wyprowadza nazw liter. Gdyby je
/// wyprowadzała, test porównujący nazwę z kodem porównywałby wynik jednej funkcji
/// z nią samą — a ten test jest dziś jedynym miejscem, w którym litera z wiersza pomocy
/// spotyka się z kodem z <c>project.godot</c>.</para>
/// </summary>
public static class KeyNames
{
    /// <summary>
    /// Kod fizyczny → nazwa klawisza. Zbiór ZAMKNIĘTY: wyłącznie klawisze, których
    /// nazwy nie da się odczytać z kodu.
    /// </summary>
    private static readonly IReadOnlyDictionary<Key, string> Nazwy =
        new Dictionary<Key, string>
        {
            [Key.Escape] = "Esc",
            [Key.Space] = UiText.Get("input.key.space"),
        };

    /// <summary>Kody, dla których tabela ma nazwę — do kontroli, nie do pętli kodu.</summary>
    public static IEnumerable<Key> Znane => Nazwy.Keys;

    /// <summary>
    /// Nazwa klawisza albo wyjątek. Brak wpisu jest ODMOWĄ, nie napisem zastępczym:
    /// nazwa zastępcza w wierszu pomocy wygląda na ekranie jak usterka tekstu i tak
    /// też zostaje zgłoszona — po dwóch dniach i przez kogoś innego (ten sam powód,
    /// dla którego <see cref="UiText.Get"/> rzuca przy braku klucza).
    /// </summary>
    public static string For(Key key) =>
        Nazwy.TryGetValue(key, out var nazwa)
            ? nazwa
            : throw new KeyNotFoundException(
                $"nie ma nazwy dla klawisza o kodzie fizycznym {(int)key} ({key})");
}
