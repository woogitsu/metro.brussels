using System;
using System.Collections.Generic;
using System.Globalization;

namespace MetroBxl.Game.UI;

/// <summary>
/// Katalog szablonów wierszy interfejsu — 6.D83.
///
/// <para><b>Skąd.</b> Zmierzone 09.09.2026 i przeliczone 10.09.2026: trzy napisy
/// interfejsu niosły <b>cztery</b> słowa językowe (<c>chainage</c>, <c>za</c>,
/// <c>ciąg</c>, <c>hamulec</c>) wpisane wprost w ciało <see cref="Hud.Update"/>,
/// scena miała <b>siedem</b> literałów zastępczych, a przeszukanie całej warstwy gry
/// pod wywołania funkcji tłumaczącej (<c>Tr(</c>, <c>TranslationServer</c>), pliki
/// katalogu tekstów (<c>*.po</c>, <c>*.translation</c>) i sekcję
/// <c>[internationalization]</c> w <c>project.godot</c> dało <b>zero</b> trafień.</para>
///
/// <para><b>Czego ten katalog NIE robi.</b> Nie dodaje drugiego języka i niczego nie
/// tłumaczy — pole „Poza zakresem" pozycji 6.D83 mówi wprost: „ta pozycja robi
/// miejsce, nie treść". Jest tu jeden język, polski, i jest domyślnym. Napisy są
/// przeniesione <b>co do znaku</b>, razem z angielskim słowem <c>chainage</c>, bo
/// zmiana ich brzmienia byłaby treścią, a nie miejscem.</para>
///
/// <para><b>Formatowanie liczb zostaje w kodzie</b>, i to jest granica postawiona
/// świadomie. Szablon niesie SŁOWA i kolejność pól; <c>F1</c>, <c>F2</c>, szerokości
/// pól i jednostki (<c>km/h</c>, <c>m</c>, <c>m/s²</c>) zostają tam, gdzie były —
/// pole „Skończone, gdy" żąda tego wprost („jednostki i formaty liczb zostają").
/// Wpuszczenie formatów do katalogu znaczyłoby, że tłumacz może zmienić liczbę
/// miejsc po przecinku.</para>
///
/// <para><b>Brak klucza jest BŁĘDEM, nie napisem.</b> <see cref="Get"/> rzuca
/// wyjątkiem zamiast zwrócić nazwę klucza. Katalog, który przy braku wpisu wyświetla
/// <c>hud.position</c>, wygląda na ekranie jak usterka tekstu i tak też zostaje
/// zgłoszony — po dwóch dniach i przez kogoś innego. Tego wprost żąda pole
/// „Skończone, gdy": usunięcie używanego klucza ma wywrócić test, a nie wyświetlić
/// cicho nazwę klucza.</para>
/// </summary>
public static class UiText
{
    /// <summary>Język katalogu domyślnego. Jeden, i tak ma zostać do osobnej pozycji.</summary>
    public const string DefaultLanguage = "pl";

    /// <summary>
    /// Szablony wierszy. Pola <c>{0}</c>… dostają wartości JUŻ SFORMATOWANE — patrz
    /// akapit o granicy między słowami a formatami w opisie klasy.
    /// </summary>
    private static readonly Dictionary<string, string> Templates =
        new(StringComparer.Ordinal)
        {
            // „chainage" jest tu angielskie i takie zostaje: napis przeniesiony
            // co do znaku, bo ta pozycja robi miejsce, nie treść.
            ["hud.position"] = "chainage {0} m / {1} m     {2} za {3} m",
            ["hud.controls"] = "ciąg {0} {1}   hamulec {2} {3}   [{4}]{5}",
        };

    /// <summary>Klucze, które katalog zna. Kolejność nieistotna, zbiór — owszem.</summary>
    public static IReadOnlyCollection<string> Keys => Templates.Keys;

    /// <summary>Szablon spod klucza. Brak klucza rzuca, a nie zwraca jego nazwy.</summary>
    /// <exception cref="KeyNotFoundException">Gdy katalog domyślny nie zna klucza.</exception>
    public static string Get(string key)
    {
        if (!Templates.TryGetValue(key, out var template))
        {
            throw new KeyNotFoundException(
                $"katalog tekstów ({DefaultLanguage}) nie zna klucza `{key}` — "
                + "brak wpisu jest BŁĘDEM, a nie napisem do wyświetlenia");
        }

        return template;
    }

    /// <summary>Szablon spod klucza wypełniony wartościami; kultura niezmienna.</summary>
    public static string Format(string key, params object?[] values) =>
        string.Format(CultureInfo.InvariantCulture, Get(key), values);
}
