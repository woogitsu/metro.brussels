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
///
/// <para><b>Rozszerzenie z 10.09.2026 (6.D99).</b> Katalog objął pozostałe wiersze
/// TEGO SAMEGO panelu: <see cref="MetroBxl.Game.FirstRun"/> (<c>StationLine</c>,
/// <c>Faza</c>), <see cref="MetroBxl.Game.Input.DriverActions"/>
/// i <see cref="MetroBxl.Game.Input.EmergencyBrake"/>. Policzone z drzewa przed
/// zmianą: <b>38</b> segmentów językowych (25 + 9 + 4), po zmianie <b>zero</b>
/// w tych metodach, a katalog urósł z 2 do 29 kluczy. Zostało w nich osiem segmentów,
/// które słowami nie są: siedem nazw akcji <c>InputMap</c> i napis „Esc". Segmentem
/// jest spójny kawałek tekstu literału POMIĘDZY dziurami interpolacji, niosący dwie
/// litery pod rząd — ta sama definicja słowa, co w skanie <c>UiTextTests</c>, który
/// pilnuje
/// <c>Hud.cs</c> od 6.D83.</para>
///
/// <para><b>Granica druga: SŁOWO kontra NAPIS NA KLAWISZU.</b> W katalogu stoi to,
/// co klawisz ROBI (<c>input.power</c> = „ciąg"), a w tabeli
/// <see cref="MetroBxl.Game.Input.DriverActions.All"/> zostaje to, jak klawisz się
/// NAZYWA („W", „S", „X", „C", „R", „Esc"). Powód jest mierzalny, a nie estetyczny:
/// <c>DriverActionsTests</c> porównuje jednoliterowe nazwy z <c>physical_keycode</c>
/// w <c>project.godot</c>, więc nazwa jest odczytem z klawiatury, nie zdaniem po
/// polsku. Wyjątkiem jest <c>input.key.space</c>: na klawiszu Esc napisane jest
/// „Esc", a na spacji nie jest napisane nic — „Spacja" to polski rzeczownik i pod tą
/// samą regułą trafia do katalogu.</para>
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

            // Wiersz prędkości — MB-03. Do 13.09.2026 składał się WPROST w ciele
            // `Hud.Update` i nie niósł sufitu; sufit stał wyłącznie w wierszu
            // sygnalizacji, czyli w diagnostyce, którą MB-03 odsuwa na dół panelu.
            // Gracz reguluje prędkość w każdej sekundzie jazdy i musi wiedzieć,
            // kiedy przestać dodawać — bez tej liczby wiersz mówi „ile", a nie „ile wolno".
            //
            // Słowo brzmi `sufit`, a nie `limit`, i to jest słowo, którego repozytorium
            // już używa na tę wielkość (`FirstRun.cs`, wiersz `[LIMIT] … sufit maszynisty`).
            ["hud.speed"] = "{0} km/h   sufit {1} km/h     a = {2} m/s²",

            // DRUGI WARIANT, BEZ SUFITU — i to nie jest ozdoba, tylko jedyna poprawna
            // odpowiedź dla odtwarzania telemetrii. `RunHeader.SpeedLimitMps` RZUCA
            // w tym trybie, i rzuca świadomie: ruch jest zadany plikiem, a nie liczony,
            // więc żadna liczba nie byłaby tam wynikiem prowadzenia przebiegu.
            // Wpisanie czegokolwiek — zera, `NaN`, prędkości konstrukcyjnej — byłoby
            // dokładnie tą usterką, dla której `RunHeader` w ogóle powstał
            // (`limit=80.0 km/h` obok przejazdu jadącego 70).
            //
            // Dwa szablony, a nie jeden z pustym polem: pusty sufit zostawiłby
            // w wierszu dwie spacje i słowo „sufit" bez liczby. Ta sama decyzja i ten
            // sam powód, co przy dwóch wariantach cyklu drzwi w wierszu stacji (6.D99).
            ["hud.speed.no-limit"] = "{0} km/h     a = {1} m/s²",
            ["hud.controls"] = "ciąg {0} {1}   hamulec {2} {3}   [{4}]{5}",

            // --- wiersz stacji (`FirstRun.StationLine`) — 6.D99 -------------------
            // Dwa warianty cyklu drzwi, bo dwa tryby mówią co innego: przejazd po
            // linii nie ma blokady trakcji, przejazd gracza — ma i pokazuje ją
            // w nawiasie. Jeden szablon z pustym polem dałby w trybie liniowym dwa
            // odstępy i nawias bez treści, czyli napis inny co do znaku.
            ["hud.station.doors"] =
                "DRZWI {0}  jeszcze {1} s  błąd zatrzymania {2} m   obsłużone {3}",
            ["hud.station.doors-traction"] =
                "DRZWI {0}  jeszcze {1} s  ({2})  błąd zatrzymania {3} m   {4}",
            ["hud.station.run-over"] = "koniec przejazdu   obsłużone {0}",
            ["hud.station.next"] = "{0} za {1} m   obsłużone {2}",
            ["hud.station.counter"] = "obsłużone {0}  minięte {1}",
            ["hud.station.no-more"] = "brak dalszych stacji   {0}",
            ["hud.station.approach"] = "{0} za {1} m (okno ±{2} m){3}   {4}",
            ["hud.station.in-window"] = "  W OKNIE — zatrzymaj się",
            ["hud.station.brake-now"] = "  HAMUJ TERAZ",
            // --- drzwi RĘCZNE (`FirstRun.StationLine`, `FirstRun.PodpowiedzDrzwi`) — MB-08 ---
            // Trzeci wariant wiersza stacji, a nie czwarta dziura w dwóch istniejących.
            // Postój ręczny nie ma pola „jeszcze N s" — długość fazy otwartej podaje
            // człowiek i nikt jej nie zna z góry — więc szablon z tą dziurą musiałby
            // wypisać w niej albo zero (nieprawda), albo `NaN` (napis dla programisty).
            // Ta sama decyzja i ten sam powód, co przy dwóch wariantach wyżej (6.D99).
            ["hud.station.doors-manual"] =
                "DRZWI {0} (ręcznie)\n{1}\nbłąd zatrzymania {2} m   obsłużone {3}",

            // Przed obsługą peronu zamknięte drzwi pozwalają ruszyć, ale odjazd
            // pozostawiłby stację bez obsługi. HUD podaje właściwy następny krok
            // i osobno zachowuje prawdziwą informację o stanie trakcji.
            ["hud.doors.open-to-serve"] = "D: otwórz drzwi   trakcja WOLNA",
            ["hud.doors.prompt-close"] = "F zamyka drzwi",
            ["hud.doors.working"] = "skrzydła w ruchu — trakcja ZABLOKOWANA",
            ["hud.doors.refused"] = "ODMOWA: {0}",

            // Powody odmowy wchodzą tu dziurą z `FirstRun.PowodOdmowy`, tak samo jak
            // nazwy faz z `FirstRun.Faza` — bo `DoorRefusal` jest wyliczeniem RDZENIA,
            // a rdzeń nie pisze na ekran gracza.
            ["hud.doors.refusal.automatic"] = "drzwiami steruje automat",
            ["hud.doors.refusal.moving"] = "skład jest w ruchu",
            ["hud.doors.refusal.outside"] = "skład stoi poza peronem",
            ["hud.doors.refusal.already-open"] = "drzwi są już otwarte",
            ["hud.doors.refusal.not-open"] = "drzwi nie są otwarte",

            ["hud.traction.free"] = "trakcja WOLNA",
            ["hud.traction.locked"] = "trakcja ZABLOKOWANA",

            // --- wiersz blokady trakcji (`TractionBlock`) — MB-03 -----------------
            // Trzy wpisy, bo filtry nastawnika w rdzeniu są DWA, a ochrona ma dwa
            // stopnie. Nazwa fazy drzwi przychodzi dziurą z `FirstRun.Faza`, a nie
            // jest tu wpisana drugi raz — ta sama granica, co przy wierszu stacji.
            ["hud.traction.doors"] = "TRAKCJA ODCIĘTA — drzwi: {0}",
            ["hud.traction.atp-service"] = "TRAKCJA ODCIĘTA — ATP hamuje służbowo",
            ["hud.traction.atp-emergency"] = "TRAKCJA ODCIĘTA — ATP hamuje awaryjnie",

            // --- fazy cyklu drzwi (`FirstRun.Faza`) — 6.D99 -----------------------
            // Siedem, nie osiem: `DoorPhase` ma siedem wartości, a ósme ramię
            // (`_ => phase.ToString()`) jest wyjściem awaryjnym dla wartości spoza
            // wyliczenia i nazwy po polsku nie ma z definicji.
            ["hud.door.closed"] = "zamknięte",
            ["hud.door.unlocking"] = "odryglowanie",
            ["hud.door.opening"] = "otwieranie",
            ["hud.door.open"] = "otwarte",
            ["hud.door.closing-warning"] = "sygnał zamykania",
            ["hud.door.closing"] = "zamykanie",
            ["hud.door.checking"] = "kontrola zamknięcia",

            // --- co robi klawisz (`DriverActions`) — 6.D99 ------------------------
            // Tu stoi ZNACZENIE klawisza, a nie jego NAZWA: nazwa („W", „Esc") jest
            // napisem na klawiszu i zostaje w tabeli przypisań — patrz akapit
            // o tej granicy w opisie klasy.
            ["input.power"] = "ciąg",
            ["input.brake"] = "hamulec",
            ["input.coast"] = "wybieg",
            ["input.emergency"] = "hamulec awaryjny (= pełny służbowy)",
            ["input.view"] = "widok",
            ["input.reset"] = "od nowa",
            ["input.quit"] = "wyjście",

            // MB-07. Krótkie, bo wchodzą do wiersza pomocy obok siedmiu poprzednich,
            // a ten wiersz ma się dać przeczytać wzrokiem z fotela.
            ["input.train-next"] = "następny skład",
            ["input.train-take"] = "przejmij",
            ["input.train-release"] = "oddaj",

            // MB-08. Tak samo krótkie i z tego samego powodu.
            ["input.door-open"] = "otwórz drzwi",
            ["input.door-close"] = "zamknij drzwi",
            ["help.core-drives"] = "prowadzi rdzeń: {0} nie działają",

            // --- hamulec awaryjny (`EmergencyBrake`) — 6.D99 ----------------------
            // „Spacja" jest tu, a „Esc" nie, i to jest rozstrzygnięcie, nie
            // niekonsekwencja: na klawiszu Esc napisane jest „Esc", a na spacji nie
            // jest napisane nic. Pierwsze jest odczytem z klawiatury, drugie —
            // polskim rzeczownikiem.
            ["input.key.space"] = "Spacja",
            // --- panel wyniku sesji treningowej (`RunSummary`) — MB-02 ------------
            // Wynik to FAKTY, nie punkty (`docs/PLAYABILITY.md` §3), więc w katalogu
            // nie ma ani jednego słowa oceny: „zaliczone" mówi o warunku zadania,
            // a nie o graczu, i nie ma przy nim gwiazdek ani kar.
            ["summary.passed"] = "SESJA ZALICZONA",
            ["summary.failed.missed"] = "SESJA NIEZALICZONA — minięty cel",
            ["summary.targets"] = "cele: {0} z {1}",
            ["summary.target.served"] = "{0}  zatrzymanie {1} m",
            ["summary.target.missed"] = "{0}  minięty",
            ["summary.time"] = "czas: {0} s   droga: {1} m",
            ["summary.atp"] = "ochrona: {0} ostrzeżeń, {1} ingerencji ({2} awaryjnych)",
            ["summary.again"] = "[{0}] od nowa   [{1}] wyjście",

            ["hud.emergency-brake"] =
                "HAMULEC AWARYJNY ({0}) = pełny hamulec SŁUŻBOWY {1}"
                + " — model nie ma osobnego stopnia awaryjnego",
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
