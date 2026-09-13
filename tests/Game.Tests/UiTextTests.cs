using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.RegularExpressions;
using MetroBxl.Game.Input;
using MetroBxl.Game.UI;
using MetroBxl.Sim.Train;
using Godot;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace MetroBxl.Game.Tests;

/// <summary>
/// Katalog tekstów interfejsu jest kompletny, a w metodach HUD-u nie ma słów — 6.D83.
///
/// <para><b>Skąd.</b> Zmierzone 09.09.2026 i przeliczone 10.09.2026: trzy napisy
/// interfejsu niosły cztery słowa językowe wpisane wprost w ciało <c>Hud.Update</c>,
/// a przeszukanie warstwy gry pod wywołania funkcji tłumaczącej, pliki katalogu
/// tekstów i sekcję <c>[internationalization]</c> dało <b>zero</b> trafień.</para>
///
/// <para><b>Rozszerzenie z 10.09.2026 (6.D99).</b> Katalog objął pozostałe wiersze tego
/// samego panelu, więc skan kluczy przestał czytać <c>Hud.cs</c> i czyta CAŁE
/// <c>src/Game/</c>. Powód jest usterką, którą ta zmiana zobaczyła u siebie: dopóki
/// „kto woła klucz" znaczyło „woła go <c>Hud.cs</c>", pierwsze 27 kluczy wołanych
/// z <c>FirstRun</c> i z <c>Input/</c> było dla testu martwe — a test miał rację, bo
/// pytał o zły plik. Wąska rodzina plików zamienia „nikt nie woła" na „nie patrzę
/// tam", i to jest ta sama choroba, co przyrząd meldujący sprawdzenie, którego nie
/// zrobił.</para>
/// </summary>
[TestClass]
public sealed class UiTextTests
{
    /// <summary>
    /// Wzorzec wywołania katalogu. Jedna kopia: ten sam wzorzec rozstrzyga i test
    /// kompletności, i test martwych wpisów, a dwie kopie rozjechałyby się cicho.
    /// </summary>
    private const string WzorzecWywolania =
        "UiText[.](?:Format|Get)[(]\\s*\"([^\"]+)\"";

    /// <summary>
    /// Nazwy klawiszy, które ZOSTAJĄ w kodzie — 6.D99.
    ///
    /// <para>Jedna pozycja, bo nazwy jednoliterowe („W", „S", „X", „C", „R") i tak nie
    /// mają dwóch liter pod rząd, więc skan ich nie widzi. „Esc" jest napisem
    /// wytłoczonym na klawiszu, nie zdaniem po polsku — inaczej niż „Spacja", która
    /// na klawiszu nie jest napisana nigdzie i dlatego poszła do katalogu
    /// (<c>input.key.space</c>).</para>
    ///
    /// <para><b>ROZSTRZYGNIĘCIE 6.D142: lista ZOSTAJE jako UBEZPIECZENIE — nie jako
    /// działający filtr — i ma odtąd PRZEDMIOT.</b> Pozycja wzięła się z kontroli KN-4
    /// przy 6.D130: zdjęcie „Esc" z tej listy daje <b>233/233</b>, czyli zielono.
    /// Wpis 6.D130 wyjaśnił tę zieleń tym, że napis mieszka od 6.D116
    /// w <c>KeyNames.cs</c>, którego bramka literałów nie skanuje. <b>To wyjaśnienie
    /// jest nieprawdziwe i zostało zmierzone jako takie 11.09.2026</b>: zielono
    /// byłoby także wtedy, gdyby „Esc" stało wprost w pliku skanowanym.</para>
    ///
    /// <para><b>Zmierzony powód: dla swojego JEDYNEGO wpisu wyjątek jest BEZCZYNNY.</b>
    /// Sito „czy to słowo" pyta nie o literał, tylko o
    /// <c>BezJednostek(BezDziur(literał))</c>, a <c>Jednostki</c> niosą <c>"s"</c> —
    /// więc z „Esc" zostaje <c>"E c"</c>, czego <see cref="WzorzecSlowa"/> nie łapie.
    /// Gdyby wyjątku nie było, „Esc" i tak nie zostałoby zgłoszone. Zmierzone bramką,
    /// nie wywnioskowane: przy liście PUSTEJ <c>SlowaWKodzie("var t = \"Esc\";")</c>
    /// nadal daje pustą listę, a z całego zestawu zapala się wyłącznie zapadka na
    /// długość listy (KN-2 z 6.D142).</para>
    ///
    /// <para><b>Argument o nieprawdziwym komunikacie, który stał tu przedtem, ODPADA
    /// razem z tamtym.</b> Mówił, że bez wyjątku „Esc" byłoby odrzucane z powodem
    /// „literał językowy zamiast klucza katalogu", czyli nieprawdziwym, bo
    /// <c>Godot.Key</c> zna <c>Escape</c>, a <c>Esc</c> nie. Odrzucane nie byłoby
    /// wcale — zdanie o powodzie nie ma kiedy paść. <c>PowodOdrzucenia</c> zostaje
    /// nietknięte tam, gdzie je postawiło 6.D130: dotyczy literałów naprawdę
    /// zgłoszonych, a takim „Esc" nie jest.</para>
    ///
    /// <para><b>Dlaczego mimo to ZOSTAJE.</b> Ta sama decyzja, co przy kolejności
    /// <see cref="Jednostki"/> (kontrola KN-3 z 6.D115, wyszła zielona): mechanizm
    /// kosztuje zero i jest OSIĄGALNY — dla nazwy klawisza, która słowem zostaje,
    /// działa. Zmierzone na ośmiu: <c>Enter</c>, <c>Tab</c>, <c>Shift</c>,
    /// <c>Ctrl</c>, <c>Alt</c>, <c>Del</c>, <c>Ins</c> i <c>Escape</c> są dziś
    /// zgłaszane, więc każde z nich wyjątek by przepuścił. Bezczynność akurat wpisu
    /// „Esc" wisi na CUDZEJ liście: zdjęcie <c>"s"</c> z <c>Jednostki</c> czyni go
    /// natychmiast działającym. Skasowany trzeba by go wtedy odtworzyć, nie wiedząc
    /// po co — a zdanie o nim ma mówić, ile jest warte, i od tej pozycji mówi.</para>
    ///
    /// <para><b>Czego brakowało i co doszło.</b> Wyjątek nie był z niczym związany —
    /// gdyby „Esc" zniknęło z <c>KeyNames.cs</c>, lista zostałaby jako zdanie o kodzie,
    /// którego nikt nie czyta. Test <c>Wyjatek_na_nazwy_klawiszy_ma_PRZEDMIOT_w_KeyNames</c>
    /// żąda, żeby każda pozycja tej listy była nazwą, którą <c>KeyNames</c> naprawdę
    /// zwraca — więc wyjątek umiera razem ze swoim przedmiotem, a nie po cichu.</para>
    /// </summary>
    private static readonly string[] NazwyKlawiszy = { "Esc" };

    /// <summary>
    /// Nazwy klawiszy, które bramka literałów DZIŚ ZGŁASZA — 6.D142.
    ///
    /// <para>Nie jest to lista wyjątków ani propozycja takiej listy: to materiał
    /// pomiaru pokazującego, że wyjątek <see cref="NazwyKlawiszy"/> jest osiągalny,
    /// mimo że dla swojego jedynego wpisu jest bezczynny. Zmierzone 11.09.2026 —
    /// każda z tych ośmiu przechodzi przez sito słowa i zostaje zgłoszona.</para>
    /// </summary>
    private static readonly string[] NazwyKlawiszyZglaszane =
        { "Enter", "Tab", "Shift", "Ctrl", "Alt", "Del", "Ins", "Escape" };

    /// <summary>
    /// Nazwy członków <c>Godot.Key</c> — 193 na dzień 11.09.2026, czytane z silnika,
    /// nie przepisane.
    ///
    /// <para><b>Po co, skoro bramka i tak odrzuca.</b> Bo odrzuca z DWÓCH różnych
    /// powodów i mówiła o obu jednym zdaniem. Zmierzone 11.09.2026 przy 6.D116:
    /// podmiana <c>"Esc"</c> na <c>"Escape"</c> zapalała
    /// <c>W_plikach_sterowania_nie_ma_ani_jednego_slowa</c> komunikatem „stoi literał
    /// językowy" — a <c>Escape</c> polskim słowem nie jest. Zapaliło się dlatego, że
    /// napis nie stoi w <c>NazwyKlawiszy</c>, czyli z innego powodu, niż mówiło
    /// zdanie, i kierowało szukającego w złe miejsce.</para>
    ///
    /// <para><b>To nie jest lista słów i dlatego wolno jej tu być.</b> Pole „Wyjście"
    /// 6.D130 dopuszczało też pomiar pokazujący, że bez listy słów rozróżnić się nie
    /// da. Da się: <c>Godot.Key</c> jest <b>wyliczeniem silnika</b>, nie czyimś
    /// wyborem, i rośnie razem z Godotem, a nie razem z tekstem interfejsu.</para>
    ///
    /// <para><b>Ryzyko kolizji mierzone NA KORPUSIE BRAMKI — akapit jest przepisany,
    /// a nie dopisany obok (6.D153, 12.09.2026).</b> Poprzednia wersja mówiła, że
    /// w całym <c>src/Game/</c> stoi <b>948</b> literałów (746 różnych), a nazwą
    /// klawisza jest <b>sześć</b>: <c>Escape</c>, <c>F1</c>, <c>F2</c>,
    /// <c>Forward</c>, <c>Right</c>, <c>Up</c>. Liczba jest odtwarzalna, ale
    /// <b>policzona poza zasięgiem przyrządu</b>: razem z komentarzami i razem
    /// z <c>UiText.cs</c>, których bramka nie czyta.</para>
    ///
    /// <para><b>Co bramka widzi naprawdę.</b> Jej korpus to <see cref="ZrodlaGry"/>
    /// — <b>21</b> plików, bez <c>.godot</c> i bez <c>UiText.cs</c>. Akapit jest
    /// przepisany, a nie dopisany obok (6.D184): do 13.09.2026 stało tu, że korpus
    /// jest „przepuszczony przez obcinacz komentarzy", i to już nieprawda. Obcinacz
    /// wierszowy został zdjęty z szesnastu miejsc, bo od 6.D182 <see cref="Literaly"/>
    /// pomija komentarze sam, leksykalnie — zmierzone: <b>480</b> literałów z nim
    /// i <b>480</b> bez, różnica w <b>zero</b> plikach z dwudziestu jeden. Stoi w nim
    /// <b>521</b> literałów (<b>395</b> różnych), a nazwą klawisza jest
    /// <b>siedem</b>: <c>C</c>, <c>F1</c>, <c>F2</c>, <c>R</c>, <c>S</c>, <c>W</c>,
    /// <c>X</c>. Cztery z tamtej szóstki — <c>Escape</c>, <c>Forward</c>,
    /// <c>Right</c>, <c>Up</c> — nie są w ogóle literałami kodu: <c>Escape</c> stoi
    /// w cudzysłowie w komentarzu <c>KeyNames.cs</c>, a pozostałe trzy są
    /// wartościami atrybutu <c>&lt;param name="..."&gt;</c> w <c>SceneAxis.cs</c>.
    /// Pięciu jednoliterowych, które w kodzie naprawdę stoją, tamto zdanie nie
    /// wymieniało. Ocena liczona szerzej niż zasięg przyrządu zawyżała ryzyko
    /// i jednocześnie pomijała to, które istnieje.</para>
    ///
    /// <para><b>Ile tego ryzyka jest: ZERO — i to jest wynik pomiaru, nie jego
    /// brak.</b> Do <see cref="PowodOdrzucenia"/> trafia wyłącznie literał
    /// ZGŁOSZONY, a zgłasza go <see cref="WzorzecSlowa"/>, który żąda dwóch liter
    /// pod rząd. Żadna z tych siedmiu nazw dwóch liter pod rząd nie ma — pięć jest
    /// jednoliterowych, a <c>F1</c> i <c>F2</c> niosą literę i cyfrę. Kolizja
    /// w zasięgu bramki jest więc dziś NIEOSIĄGALNA, i to ze względu strukturalnego,
    /// a nie przez szczęśliwy dobór napisów. W korpusie szerszym jest odwrotnie:
    /// wszystkie cztery nazwy widziane tylko w komentarzach są zgłaszalne, więc
    /// gdyby któraś zeszła z komentarza do kodu, kolizja stałaby się natychmiast
    /// realna. Pilnuje tego
    /// <see cref="Ocena_ryzyka_kolizji_jest_mierzona_na_korpusie_bramki"/>.</para>
    ///
    /// <para>Żadna ze 193 nazw nie niesie polskiego znaku diakrytycznego.</para>
    /// </summary>
    private static readonly HashSet<string> NazwyKlawiszySilnika =
        Enum.GetNames(typeof(Key)).ToHashSet(StringComparer.Ordinal);

    /// <summary>
    /// Nazwy członów <c>Godot.Key</c>, które stoją w KORPUSIE BRAMKI — 6.D153.
    ///
    /// <para><b>Przybity jest ZBIÓR, a nie liczba literałów, i to jest pomiar, nie
    /// gust.</b> Zmierzone 12.09.2026 na <b>40</b> rewizjach <c>src/Game</c>: para
    /// (literały, różne) zmienia się w <b>29</b> przejściach na 39, a ten zbiór —
    /// w <b>dwóch</b>. Zapadka na liczbach zapalałaby się w trzech rewizjach na
    /// cztery i zostałaby wyłączona; zapadka na zbiorze pilnuje dokładnie tego,
    /// o czym mówi akapit o ryzyku przy <see cref="NazwyKlawiszySilnika"/>.</para>
    /// </summary>
    private static readonly string[] NazwyKlawiszyWZasieguBramki =
        { "C", "F1", "F2", "R", "S", "W", "X" };

    /// <summary>
    /// Nazwy klawiszy widoczne dopiero SZERZEJ niż bramka — 6.D153.
    ///
    /// <para>Nie jest to lista wyjątków: to materiał pomiaru. Każda z tych czterech
    /// jest zgłaszalna przez <see cref="WzorzecSlowa"/>, a mimo to nie stoi
    /// w korpusie bramki — bo stoi w komentarzu. Gdyby któraś zeszła do kodu,
    /// kolizja byłaby realna, i stąd druga połowa testu.</para>
    /// </summary>
    private static readonly string[] NazwyKlawiszyTylkoWKomentarzach =
        { "Escape", "Forward", "Right", "Up" };

    /// <summary>Ile plików ma korpus bramki — dolne ostrze, zmierzone 12.09.2026.</summary>
    private const int PlikowWZasieguBramki = 21;

    /// <summary>Ile literałów — dolne ostrze, zmierzone 12.09.2026.</summary>
    private const int LiteralowWZasieguBramki = 480;

    /// <summary>Ile różnych — dolne ostrze, zmierzone 12.09.2026.</summary>
    private const int RoznychLiteralowWZasieguBramki = 362;

    /// <summary>
    /// Dlaczego ten literał został odrzucony — dwa różne zdania, nie jedno — 6.D130.
    /// </summary>
    private static string PowodOdrzucenia(string literal) =>
        NazwyKlawiszySilnika.Contains(literal)
            ? "nazwa klawisza silnika spoza `NazwyKlawiszy`"
            : "literał językowy zamiast klucza katalogu";

    /// <summary>Lista odrzuconych literałów z powodem przy każdym — 6.D130.</summary>
    private static string ZPowodami(IEnumerable<string> zle) =>
        string.Join(" | ", zle.Select(z => $"\"{z}\" ({PowodOdrzucenia(z)})"));

    /// <summary>Metody <c>FirstRun.cs</c>, które 6.D99 wyczyściło ze słów.</summary>
    private static readonly string[] MetodyFirstRun =
    {
        "private string StationLine()",
        "private static string Faza(DoorPhase phase)",
        "private string HelpLine()",
    };

    /// <summary>
    /// Człony <c>KeyNames.cs</c>, które bramka literałów SKANUJE — 6.D143.
    ///
    /// <para><b>Skąd pozycja.</b> Od 6.D116 napisy klawiszy mieszkają w tym pliku,
    /// a nie skanował go nikt — i to jest powód, dla którego objawu opisanego
    /// w 6.D130 nie dało się odtworzyć. Plik niesie dokładnie tę rodzinę, o którą
    /// bramce chodzi: napis widziany przez gracza w wierszu pomocy.</para>
    ///
    /// <para><b>Skanowana jest TABLICA, a nie plik, i to jest ta sama decyzja co przy
    /// <see cref="MetodyFirstRun"/>.</b> Zmierzone 11.09.2026: plik ma <b>trzy</b>
    /// literały, z czego dwa stoją w tablicy, a trzeci jest komunikatem wyjątku
    /// <c>KeyNotFoundException</c> w <c>For</c>. Skan całego pliku zapaliłby się na
    /// nim i zostałby wyłączony — czyli bramka zniknęłaby razem z tym, czego miała
    /// pilnować.</para>
    ///
    /// <para><b>Rozważona i odrzucona druga droga: skan całego pliku z komunikatem
    /// wpisanym na listę wyjątków.</b> Tu byłoby to wykonalne — wyjątek byłby JEDEN,
    /// inaczej niż w `FirstRun.cs`. Przegrywa, bo lista wyjątków rośnie z każdym
    /// nowym <c>throw</c> i jest drogą powrotną dla tego, co bramka miała wykluczyć
    /// (ten sam powód, dla którego sito identyfikatorów silnika jest REGUŁĄ, a nie
    /// listą nazw). Granica po członie mówi natomiast coś prawdziwego i trwałego:
    /// <b>tablica jest tekstem, a <c>throw</c> jest diagnostyką</b>.</para>
    ///
    /// <para><b>Skala, dla której ta granica w ogóle istnieje, jest zmierzona, nie
    /// oszacowana.</b> Gdyby bramkę puścić na całe <c>src/Game/</c>, zgłosiłaby
    /// <b>347</b> literałów w <b>16</b> plikach, z czego <b>22</b> stoją w <c>throw</c>,
    /// a reszta to wypisy diagnostyczne, prozą opisane założenia projektowe i nazwy
    /// pól JSON. `KeyNames.cs` ma z tych 347 dokładnie <b>jeden</b>.</para>
    ///
    /// <para><b>Było tu <b>348</b> i akapit jest przepisany, a nie dopisany obok —
    /// 6.D182.</b> Ta liczba wyszła z czytnika, który rozcinał napisy interpolowane
    /// z zagnieżdżonym cudzysłowem i napisy surowe (patrz <see cref="Literaly"/>).
    /// Z bazy odchodzą <b>cztery</b> pozycje z <c>RunPlan.cs</c>, które literałami
    /// nie były — dwa kawałki urwane na <c>{string.Join(</c> i dwa ogony w rodzaju
    /// <c>, KnownArguments)}</c> — a dochodzą <b>trzy</b> literały prawdziwe: te same
    /// dwa w całości i napis surowy z <c>FirstRun.cs</c>. <b>Liczba plików była
    /// podana jako 21, czyli jako WIELKOŚĆ KORPUSU, a nie jako liczba plików
    /// zgłaszających</b>; zgłasza <b>16</b> i tak jest tu odtąd napisane.</para>
    ///
    /// <para><b>Rodzin liczonych po TREŚCI literału ta poprawka NIE rusza, i to jest
    /// pomiar, nie oczekiwanie</b> (6.D182): prefiks w nawiasie, identyfikator wąski
    /// i szeroki oraz obecność polskiego znaku dają na obu czytnikach liczby
    /// <b>równe co do jedynki</b>. Cztery pozycje odchodzące i trzy dochodzące leżą
    /// poza każdą z tych rodzin albo — jak para <c>[ARGUMENT]</c> — odchodzą
    /// i wracają z tym samym prefiksem. Rozpisane w
    /// <c>reports/6d182-uciete-literaly.md</c>.</para>
    /// </summary>
    private static readonly string[] CzlonyKeyNames =
    {
        "IReadOnlyDictionary<Key, string> Nazwy",
    };

    /// <summary>Ile literałów ma CAŁY <c>KeyNames.cs</c> — zmierzone 11.09.2026.</summary>
    private const int LiteralowWKeyNames = 3;

    /// <summary>Ile z nich wpada w skanowane człony — zmierzone 11.09.2026.</summary>
    private const int LiteralowWTablicyKeyNames = 2;

    private static string Zrodlo(params string[] czesci) =>
        File.ReadAllText(Path.Combine(RepositoryRoot(), Path.Combine(czesci)));

    private static string HudSource() => Zrodlo("src", "Game", "UI", "Hud.cs");

    /// <summary>
    /// Wszystkie pliki <c>src/Game/</c> poza wygenerowanymi przez Godota i poza samym
    /// katalogiem. <c>UiText.cs</c> jest wyłączony, bo klucz stoi w nim jako WPIS,
    /// a nie jako wywołanie — liczenie go za wołającego uczyniłoby każdy wpis żywym
    /// z samego faktu istnienia.
    /// </summary>
    private static List<string> ZrodlaGry()
    {
        var korzen = Path.Combine(RepositoryRoot(), "src", "Game");
        var katalog = Path.Combine(korzen, "UI", "UiText.cs");
        return Directory.GetFiles(korzen, "*.cs", SearchOption.AllDirectories)
            .Where(p => !p.Split(Path.DirectorySeparatorChar).Contains(".godot"))
            .Where(p => !string.Equals(p, katalog, StringComparison.Ordinal))
            .OrderBy(p => p, StringComparer.Ordinal)
            .ToList();
    }

    /// <summary>Klucze wołane z warstwy gry, jako pary (plik, klucz).</summary>
    private static List<(string Plik, string Klucz)> WolaneKlucze() =>
        ZrodlaGry()
            .SelectMany(p => Regex
                .Matches(File.ReadAllText(p), WzorzecWywolania)
                .Select(m => (Plik: Path.GetFileName(p), Klucz: m.Groups[1].Value)))
            .ToList();

    /// <summary>Ciało metody wskazanej nagłówkiem: blok w klamrach albo do średnika.</summary>
    private static string CialoMetody(string source, string naglowek)
    {
        var start = source.IndexOf(naglowek, StringComparison.Ordinal);
        Assert.IsTrue(start >= 0,
            $"nie ma metody `{naglowek}` — skan mierzyłby nie tę metodę albo nic");

        var klamra = source.IndexOf('{', start);
        var srednik = source.IndexOf(';', start);
        if (srednik >= 0 && (klamra < 0 || srednik < klamra))
        {
            return source[start..srednik];       // metoda wyrażeniowa bez bloku
        }

        var glebia = 0;
        for (var i = klamra; i < source.Length; i++)
        {
            glebia += source[i] == '{' ? 1 : source[i] == '}' ? -1 : 0;
            if (glebia == 0)
            {
                return source[start..(i + 1)];
            }
        }

        Assert.Fail($"nie domknięto ciała metody `{naglowek}`");
        throw new InvalidOperationException();
    }


    /// <summary>
    /// Wzorzec, którym literały czytano DO 6.D182 — zostaje WYŁĄCZNIE jako wejście
    /// kontroli negatywnej.
    ///
    /// <para>Nie czyta go dziś żadna bramka. Stoi tu dlatego, że bez niego
    /// <see cref="Czytnik_literalow_czyta_leksykalnie_a_nie_wzorcem"/> nie umiałby
    /// pokazać, że nowy czytnik robi coś, czego stary nie robił — a kontrola, która
    /// nie odróżnia mechanizmu od jego braku, jest zielona zawsze i nie znaczy nic
    /// (ta sama pułapka, co przy 6.D147 KN-6 i 6.D148 KN-4).</para>
    /// </summary>
    private const string WzorzecStaregoCzytnika = "\"((?:[^\"\\\\]|\\\\.)*)\"";

    /// <summary>Stary czytnik — tylko jako wejście kontroli, patrz wyżej.</summary>
    /// <summary>Obcinacz WIERSZOWY, dziś używany WYŁĄCZNIE jako wejście
    /// starego czytnika — 6.D184.</summary>
    /// <remarks>
    /// <para><b>Był w siedemnastu miejscach, został w jednym, i to jest wynik
    /// pomiaru.</b> Usuwa każdy wiersz zaczynający się od <c>//</c>, nie pytając,
    /// czy stoi w kodzie, czy w środku napisu wielowierszowego. Odkąd
    /// <see cref="Literaly"/> pomija komentarze sam, leksykalnie (6.D182), dla
    /// żywych czytników nie zmienia <b>niczego</b>: zmierzone na korpusie
    /// <see cref="ZrodlaGry"/> — <b>480</b> literałów z obcinaczem i <b>480</b>
    /// bez, <b>347</b> zgłoszeń <see cref="SlowaWKodzie"/> z i bez, różnica
    /// w <b>zero</b> plikach z dwudziestu jeden.</para>
    /// <para><b>A szkodzić potrafi.</b> Na napisie surowym, którego drugi wiersz
    /// zaczyna się od <c>//</c>, obcinacz skraca literał z <b>33</b> znaków do
    /// <b>18</b> — po cichu, bez żadnego zgłoszenia. Dziś takiego napisu w drzewie
    /// nie ma; <c>FirstRun.cs</c> niesie literał czterdziestowierszowy i wystarczy
    /// w nim jedno pole w rodzaju <c>"url": "//host/x"</c>.</para>
    /// <para><b>Dlaczego mimo to ZOSTAJE w jednym miejscu.</b> Karmi
    /// <see cref="StaryCzytnik"/>, czyli wejście kontroli negatywnej. Bez obcinacza
    /// stary czytnik daje <b>861</b> pozycji zamiast <b>521</b>, bo łapie cudzysłowy
    /// w komentarzach — a <see cref="PozycjiStaregoCzytnika"/> opisuje korpus tak,
    /// jak widział go dawny kod. Obcinanie literału jest tu nieszkodliwe: ten czytnik
    /// ma być zły, o to w nim chodzi.</para>
    /// </remarks>
    private static string KodBezKomentarzyDlaStaregoCzytnika(string source) =>
        string.Join("\n", source.Split('\n')
            .Where(l => !l.TrimStart().StartsWith("//", StringComparison.Ordinal)));

    private static List<string> StaryCzytnik(string kod) =>
        Regex.Matches(kod, WzorzecStaregoCzytnika)
             .Select(m => m.Groups[1].Value).ToList();

    /// <summary>
    /// Literały napisowe pliku — czytnik LEKSYKALNY, od 6.D182.
    ///
    /// <para><b>Do 12.09.2026 czytało to wyrażenie regularne</b>
    /// <see cref="WzorzecStaregoCzytnika"/>, i ten akapit jest przepisany, a nie
    /// dopisany obok. Wzorzec zakłada, że cudzysłowy w pliku stoją parami, a w C#
    /// nie stoją: dziura interpolacji może nieść własny napis, napis surowy zamyka
    /// się dopiero tyloma cudzysłowami, iloma się otworzył, napis dosłowny pisze
    /// cudzysłów jako <c>""</c>, a literał znakowy <c>'"'</c> niesie cudzysłów
    /// pojedynczy. Wzorzec urywał wtedy literał na pierwszym cudzysłowie ze środka
    /// i zwracał KAWAŁEK KODU jako drugi „literał".</para>
    ///
    /// <para><b>Skala, zmierzona 12.09.2026 na korpusie <see cref="ZrodlaGry"/>
    /// kodem samej bramki.</b> Stary czytnik zwracał <b>521</b> pozycji: <b>475</b>
    /// literałów w całości, <b>3</b> urwane kawałki i <b>43</b> pozycje, które
    /// literałami nie były w ogóle. Literałów jest naprawdę <b>480</b>, więc
    /// <b>5</b> z nich nie docierało do żadnej bramki w całości. Dotknięte były
    /// <b>dwa</b> pliki z dwudziestu jeden: <c>RunPlan.cs</c> — dwa napisy
    /// interpolowane z zagnieżdżonym cudzysłowem, każdy dawał jeden kawałek urwany
    /// na <c>{string.Join(</c> i jeden ogon, który literałem nie jest — oraz
    /// <c>FirstRun.cs</c>, gdzie JEDEN napis surowy <c>$$"""</c> z czterdziestu
    /// wierszy JSON-a rozpadał się na <b>42</b> pozycje.</para>
    ///
    /// <para><b>Rozstrzygnięcie pozycji 6.D182: czytnik da się naprawić BEZ rozbioru
    /// składni C#.</b> Wszystkie cztery konstrukcje są LEKSYKALNE — o tym, gdzie
    /// kończy się napis, rozstrzyga sam ciąg znaków, a nie to, czym jest otaczające
    /// wyrażenie. Wystarczy więc lekser ze stanem (komentarz wierszowy, komentarz
    /// blokowy, literał znakowy, napis zwykły, dosłowny, surowy, dziura
    /// interpolacji), a parser jest niepotrzebny. Roslyn byłby zależnością,
    /// a <c>CLAUDE.md</c> §8 każe przy dodaniu zależności przerwać i zapytać.</para>
    ///
    /// <para><b>Co to rusza w liczbach.</b> Baza <b>348</b> zgłoszeń całego
    /// <c>src/Game/</c> jest po naprawie <b>347</b>: odchodzi z niej sześć pozycji,
    /// które literałami nie były, a dochodzą trzy literały prawdziwe. Rozpisane
    /// w <c>reports/6d182-uciete-literaly.md</c> razem z tym, których rodzin
    /// z 6.D154…6.D179 to dotyczy, a których nie.</para>
    ///
    /// <para><b>Literały z dziur interpolacji ZWRACANE SĄ TEŻ</b>, i to jest wybór:
    /// <c>" --"</c> w <c>$"… {string.Join(" --", …)}"</c> jest literałem tego pliku
    /// tak samo jak napis, w którym stoi. Kolejność jest kolejnością CUDZYSŁOWU
    /// OTWIERAJĄCEGO, więc napis zewnętrzny stoi przed swoimi zagnieżdżonymi.</para>
    /// </summary>
    private static List<string> Literaly(string kod)
    {
        var wynik = new List<string>();
        CzytajKod(kod, 0, kod.Length, wynik);
        return wynik;
    }

    /// <summary>
    /// Długość przedrostka <c>[@$]*</c> stojącego przed cudzysłowem, albo <c>-1</c>,
    /// gdy pod <paramref name="i"/> nie zaczyna się literał napisowy.
    /// </summary>
    private static int PrefiksLiteralu(string s, int i, int koniec)
    {
        var j = i;
        while (j < koniec && (s[j] == '@' || s[j] == '$'))
        {
            j++;
        }

        return j < koniec && s[j] == '"' ? j - i : -1;
    }

    /// <summary>Przesuwa za komentarz albo literał znakowy; zwraca nową pozycję.</summary>
    private static int PominNieNapis(string s, int i, int koniec)
    {
        if (s[i] == '/' && i + 1 < koniec && s[i + 1] == '/')
        {
            while (i < koniec && s[i] != '\n')
            {
                i++;
            }

            return i;
        }

        if (s[i] == '/' && i + 1 < koniec && s[i + 1] == '*')
        {
            i += 2;
            while (i + 1 < koniec && !(s[i] == '*' && s[i + 1] == '/'))
            {
                i++;
            }

            return Math.Min(i + 2, koniec);
        }

        if (s[i] == '\'')
        {
            i++;
            while (i < koniec && s[i] != '\'')
            {
                i += s[i] == '\\' ? 2 : 1;
            }

            return i + 1;
        }

        return i;
    }

    /// <summary>Skan kodu: wszystko, co nie jest napisem, jest pomijane.</summary>
    private static void CzytajKod(string s, int od, int koniec, List<string> wynik)
    {
        var i = od;
        while (i < koniec)
        {
            var po = PominNieNapis(s, i, koniec);
            if (po != i)
            {
                i = po;
                continue;
            }

            if (PrefiksLiteralu(s, i, koniec) >= 0)
            {
                i = CzytajLiteral(s, i, koniec, wynik);
                continue;
            }

            i++;
        }
    }

    /// <summary>
    /// Indeks OSTATNIEJ klamry zamykającej dziurę interpolacji otwartej klamrą
    /// o indeksie <paramref name="ostatniaOtwierajaca"/>.
    /// </summary>
    private static int KoniecDziury(string s, int ostatniaOtwierajaca, int koniec, int klamer)
    {
        var glebia = 1;
        var k = ostatniaOtwierajaca + 1;
        while (k < koniec)
        {
            var po = PominNieNapis(s, k, koniec);
            if (po != k)
            {
                k = po;
                continue;
            }

            if (PrefiksLiteralu(s, k, koniec) >= 0)
            {
                k = CzytajLiteral(s, k, koniec, new List<string>());
                continue;
            }

            if (s[k] == '{')
            {
                glebia++;
            }
            else if (s[k] == '}')
            {
                glebia--;
                if (glebia == 0)
                {
                    return k + klamer - 1;
                }
            }

            k++;
        }

        return koniec - 1;
    }

    /// <summary>
    /// Czyta JEDEN literał napisowy od pozycji <paramref name="i"/>; dopisuje go do
    /// <paramref name="wynik"/> razem z literałami z jego dziur i zwraca pozycję za
    /// cudzysłowem zamykającym.
    /// </summary>
    private static int CzytajLiteral(string s, int i, int koniec, List<string> wynik)
    {
        var dlPrefiksu = PrefiksLiteralu(s, i, koniec);
        var prefiks = s.Substring(i, dlPrefiksu);
        var doslowny = prefiks.Contains('@');
        var klamer = prefiks.Count(z => z == '$');
        var cudzyslowow = 0;
        while (i + dlPrefiksu + cudzyslowow < koniec && s[i + dlPrefiksu + cudzyslowow] == '"')
        {
            cudzyslowow++;
        }

        var surowy = cudzyslowow >= 3;
        var otwierajacych = surowy ? cudzyslowow : 1;
        var tresc = new StringBuilder();
        var zagniezdzone = new List<string>();
        var j = i + dlPrefiksu + otwierajacych;
        while (j < koniec)
        {
            var znak = s[j];
            if (znak == '"')
            {
                if (surowy)
                {
                    var n = 0;
                    while (j + n < koniec && s[j + n] == '"')
                    {
                        n++;
                    }

                    if (n >= otwierajacych)
                    {
                        break;
                    }

                    tresc.Append(s, j, n);
                    j += n;
                    continue;
                }

                if (doslowny && j + 1 < koniec && s[j + 1] == '"')
                {
                    tresc.Append("\"\"");
                    j += 2;
                    continue;
                }

                break;
            }

            if (!doslowny && !surowy && znak == '\\' && j + 1 < koniec)
            {
                tresc.Append(s[j]).Append(s[j + 1]);
                j += 2;
                continue;
            }

            if (klamer > 0 && znak == '{')
            {
                var pod = 0;
                while (j + pod < koniec && s[j + pod] == '{')
                {
                    pod++;
                }

                // Napis NIESUROWY: `{{` jest klamrą dosłowną. Napis SUROWY: dziura
                // otwiera się dopiero tyloma klamrami, ile jest znaków `$`, a krótszy
                // ciąg jest tekstem — dlatego `$$"""` niesie JSON-owe `{` wprost.
                if (!surowy && pod >= 2)
                {
                    tresc.Append("{{");
                    j += 2;
                    continue;
                }

                if (pod >= klamer)
                {
                    var koniecDziury = KoniecDziury(s, j + klamer - 1, koniec, klamer);
                    tresc.Append(s, j, koniecDziury - j + 1);
                    CzytajKod(s, j + klamer, koniecDziury - klamer + 1, zagniezdzone);
                    j = koniecDziury + 1;
                    continue;
                }
            }

            tresc.Append(znak);
            j++;
        }

        wynik.Add(tresc.ToString());
        wynik.AddRange(zagniezdzone);
        return surowy ? j + otwierajacych : j + 1;
    }

    [TestMethod]
    public void Kazdy_klucz_wolany_z_warstwy_gry_jest_w_katalogu_domyslnym()
    {
        var wolane = WolaneKlucze();

        // Dolne ostrze na SAM SKAN. Zmierzone 10.09.2026 po 6.D99: 29 wywołań
        // w 4 plikach. Bez tych dwóch liczb literówka we wzorcu daje pustą listę,
        // a pusta lista przechodzi pętlę niżej bez ani jednego sprawdzenia.
        Assert.IsTrue(wolane.Count >= 29,
            $"skan widzi {wolane.Count} wywołań katalogu w `src/Game/` — wzorzec "
            + "rozjechał się z kodem, więc pętla niżej sprawdzałaby nic");
        var pliki = wolane.Select(w => w.Plik).Distinct().Count();
        Assert.IsTrue(pliki >= 4,
            $"skan widzi wywołania w {pliki} plikach — katalog woła `Hud.cs`, "
            + "`FirstRun.cs`, `DriverActions.cs` i `EmergencyBrake.cs`");

        foreach (var (plik, klucz) in wolane)
        {
            Assert.IsTrue(UiText.Keys.Contains(klucz),
                $"`{plik}` woła klucz `{klucz}`, którego katalog "
                + $"({UiText.DefaultLanguage}) nie zna");
        }
    }

    [TestMethod]
    public void Katalog_nie_ma_wpisow_martwych()
    {
        // Wpis, którego nikt nie woła, jest zdaniem o interfejsie, które przestało być
        // prawdziwe — ta sama choroba, co martwa stała z 6.B29. Pytamy CAŁĄ warstwę
        // gry, a nie `Hud.cs`: do 6.D99 pytanie o jeden plik nazywało martwym każdy
        // klucz wołany skądinąd, czyli myliło „nikt nie woła" z „nie patrzę tam".
        var wolane = WolaneKlucze().Select(w => w.Klucz).ToHashSet(StringComparer.Ordinal);

        foreach (var klucz in UiText.Keys)
        {
            Assert.IsTrue(wolane.Contains(klucz),
                $"katalog ma klucz `{klucz}`, którego nikt nie woła — zdejmij go albo użyj");
        }
    }

    [TestMethod]
    public void Brak_klucza_jest_bledem_a_nie_napisem_z_nazwa_klucza()
    {
        // Tego wprost żąda pole „Skończone, gdy": usunięcie używanego klucza ma
        // WYWRÓCIĆ test, a nie wyświetlić cicho nazwę klucza. Katalog zwracający
        // `hud.position` wygląda na ekranie jak usterka tekstu i tak też zostaje
        // zgłoszony — po dwóch dniach i przez kogoś innego.
        var wyjatek = Assert.ThrowsException<KeyNotFoundException>(
            () => UiText.Get("hud.nie-ma-takiego"));
        StringAssert.Contains(wyjatek.Message, "hud.nie-ma-takiego");
        StringAssert.Contains(wyjatek.Message, UiText.DefaultLanguage);
    }

    /// <summary>
    /// Literały danego kodu, które są SŁOWEM, a nie kluczem, ścieżką ani formatem.
    ///
    /// <para>Słowo to co najmniej dwie litery pod rząd. Jednostki (<c>m</c>, <c>s</c>),
    /// separatory i formaty liczb (<c>F1</c>, <c>+0.00;-0.00;0.00</c>) zostają — pole
    /// „Skończone, gdy" 6.D83 mówi wprost, że jednostki i formaty liczb zostają.</para>
    /// </summary>
    /// <summary>
    /// Literał bez dziur interpolacji — 6.D99. <c>$"{binding.KeyName} {binding.Meaning}"</c>
    /// nie niesie ani jednego słowa dla człowieka, a bez tego cięcia skan czytałby
    /// nazwy zmiennych z wnętrza dziur i zgłaszał je jako polszczyznę.
    /// </summary>
    private static string BezDziur(string literal) =>
        Regex.Replace(literal, "[{][^{}]*[}]", string.Empty);

    /// <summary>
    /// Kształt ścieżki węzła sceny — segmenty rozdzielone <c>/</c>, każdy identyfikator.
    ///
    /// <para><b>Do 11.09.2026 odsiewane było KAŻDE wystąpienie ukośnika</b> i to jest
    /// usterka, którą zamyka 6.D115: pod tę regułę wpadał też
    /// <c>"{…} km/h     a = {…} m/s²"</c> z <c>Hud.Update</c>, czyli napis wypisywany
    /// graczowi. Bramka mówiła wtedy „w `Hud.cs` nie ma literału językowego" i nie
    /// miała do tego podstaw — a odsianie było JEDYNYM powodem, dla którego skan
    /// przechodził przed 6.D99 (usterka dziur interpolacji nie wyszła w 6.D83
    /// właśnie przez nie).</para>
    ///
    /// <para>Ścieżka węzła to segmenty będące identyfikatorami: bez spacji, bez cyfr
    /// formatu, bez znaków spoza <c>[A-Za-z0-9_]</c>. Napis z jednostką ma inny
    /// kształt i od tej pozycji przez to sito nie przechodzi.</para>
    /// </summary>
    private const string SciezkaWezla =
        @"^[A-Za-z_][A-Za-z0-9_]*(?:/[A-Za-z_][A-Za-z0-9_]*)+$";

    /// <summary>
    /// Symbole jednostek, zdejmowane przed pytaniem „czy to słowo" — 6.D115.
    ///
    /// <para><b>Zbiór jest ZAMKNIĘTY i wyprowadzony z pomiaru</b>, nie z wyobraźni:
    /// po zawężeniu odsiania ścieżek skan zgłosił dokładnie JEDEN literał w całym
    /// <c>src/Game/</c> i są to jednostki z niego. Pole „Skończone, gdy" 6.D83 mówi
    /// wprost, że jednostki i formaty liczb zostają — a reguła „słowo to dwie litery
    /// pod rząd" przepuszczała je dotąd tylko dlatego, że <c>m</c> i <c>s</c> są
    /// jednoliterowe. <c>km</c> nie jest, i bez tego zbioru zgłaszałoby się jako
    /// polszczyzna.</para>
    ///
    /// <para><b>Kolejność: najdłuższe najpierw — i to jest UBEZPIECZENIE, nie
    /// zmierzona konieczność.</b> Pierwsza wersja tego komentarza twierdziła, że bez
    /// niej z <c>km/h</c> zostałby wiszący <c>/h</c>; kontrola negatywna KN-3
    /// (kolejność odwrócona) wyszła <b>ZIELONA na 229 testach</b>, bo <c>/h</c> ma
    /// jedną literę i pytania „czy to słowo" i tak nie przechodzi. Żadne dzisiejsze
    /// wejście obu kolejności nie odróżnia. Porządek zostaje, bo kosztuje zero,
    /// a przy jednostce, której zdjęcie zostawiłoby dwie litery pod rząd, zacząłby
    /// być potrzebny — ale zdanie o nim ma mówić, ile jest warte.</para>
    /// </summary>
    private static readonly string[] Jednostki = { "km/h", "m/s\u00b2", "km", "m", "s" };

    /// <summary>
    /// „Słowo" to co najmniej dwie litery pod rząd — 6.D83, w stałej od 6.D142.
    ///
    /// <para>Wzorzec stoi w jednym miejscu, bo od 6.D142 pyta o niego także test
    /// bezczynności wyjątku <c>NazwyKlawiszy</c>. Dwie kopie rozjechałyby się cicho:
    /// test pilnowałby wtedy wzorca, którego bramka już nie używa — ten sam powód,
    /// co przy <see cref="WzorzecWywolania"/>.</para>
    /// </summary>
    private const string WzorzecSlowa = @"\p{L}{2,}";

    /// <summary>Literał bez symboli jednostek — patrz <see cref="Jednostki"/>.</summary>
    private static string BezJednostek(string literal)
    {
        foreach (var jednostka in Jednostki)
        {
            literal = literal.Replace(jednostka, " ", StringComparison.Ordinal);
        }

        return literal;
    }

    private static List<string> SlowaWKodzie(string kod)
    {
        var zle = new List<string>();
        foreach (var literal in Literaly(kod))
        {
            if (Regex.IsMatch(literal, SciezkaWezla))
            {
                continue;                       // ścieżka węzła sceny
            }

            // Identyfikator silnika: nazwa akcji `InputMap` (`driver_power`) albo nazwa
            // właściwości motywu (`font_size`). Reguła zamiast listy nazw, bo lista
            // rośnie z każdą akcją, a rosnąca lista wyjątków jest drogą powrotną dla
            // tego, co bramka miała wykluczyć. Polskie zdanie nie ma tego kształtu.
            if (Regex.IsMatch(literal, "^[a-z][a-z0-9]*(?:_[a-z0-9]+)+$"))
            {
                continue;
            }

            if (NazwyKlawiszy.Contains(literal, StringComparer.Ordinal))
            {
                continue;                       // napis wytłoczony na klawiszu
            }

            if (UiText.Keys.Contains(literal))
            {
                continue;                       // klucz katalogu, nie słowo
            }

            if (Regex.IsMatch(BezJednostek(BezDziur(literal)), WzorzecSlowa))
            {
                zle.Add(literal);
            }
        }

        return zle;
    }

    [TestMethod]
    public void Odsianie_sciezki_wezla_rozroznia_sciezke_od_napisu_z_jednostka()
    {
        // 6.D115. Wejście syntetyczne, bo na dzisiejszym `src/Game/` obie reguły —
        // dawna („jest ukośnik") i dzisiejsza („ma kształt ścieżki") — dają ten sam
        // werdykt dla wszystkiego poza JEDNYM literałem. Na samym drzewie kontrola
        // nie odróżniłaby więc jednej od drugiej.
        Assert.AreEqual(0, SlowaWKodzie("GetNode<Label>(\"Panel/Rows/Speed\");").Count,
            "ścieżka węzła sceny przestała być odsiewana");
        Assert.AreEqual(0, SlowaWKodzie("x = \"Hud/Panel\";").Count,
            "dwusegmentowa ścieżka węzła przestała być odsiewana");

        // Ten literał stoi w `Hud.Update` i przechodził WYŁĄCZNIE dlatego, że niesie
        // ukośnik. Dziś przechodzi z powodu, który o nim coś mówi: po zdjęciu dziur
        // interpolacji i symboli jednostek nie zostaje ani jedno słowo.
        Assert.AreEqual(
            0,
            SlowaWKodzie("$\"{speedKmh,6:F1} km/h     a = {accelerationMps2,6:F2} m/s\u00b2\";").Count,
            "napis z jednostkami został wzięty za polszczyznę");

        // Druga strona, bez której pierwsza nie znaczy nic: napis z UKOŚNIKIEM,
        // który ścieżką nie jest, ma zostać zgłoszony. Dawna reguła przepuszczała go
        // tak samo cicho jak literał prędkości.
        var zeSlowem = SlowaWKodzie("var t = \"Pr\u0119dko\u015b\u0107/godzin\u0119\";");
        Assert.AreEqual(1, zeSlowem.Count,
            "napis ze słowem i ukośnikiem przeszedł jako ścieżka węzła: "
            + string.Join(" | ", zeSlowem));

        // Segment ze spacją to nie identyfikator, więc to nie ścieżka.
        var zeSpacja = SlowaWKodzie("var t = \"Panel/Rows Pr\u0119dko\u015b\u0107\";");
        Assert.AreEqual(1, zeSpacja.Count,
            "napis z ukośnikiem i spacją przeszedł jako ścieżka: "
            + string.Join(" | ", zeSpacja));

        // Porządek tablicy jednostek jest UBEZPIECZENIEM, nie warunkiem werdyktu
        // (KN-3 wyszła zielona) — ale skoro jest wyborem, to niech będzie sprawdzalny.
        var dlugosci = Jednostki.Select(j => j.Length).ToList();
        CollectionAssert.AreEqual(dlugosci.OrderByDescending(d => d).ToList(), dlugosci,
            "tablica jednostek przestała być uporządkowana od najdłuższej: "
            + string.Join(" | ", Jednostki));

        // Jednostka nie zjada słowa stojącego obok niej.
        var zJednostkaISlowem = SlowaWKodzie("var t = \"{d} km do stacji\";");
        Assert.AreEqual(1, zJednostkaISlowem.Count,
            "zdjęcie jednostek połknęło słowo: " + string.Join(" | ", zJednostkaISlowem));
    }

    [TestMethod]
    public void W_metodach_HUD_nie_ma_ani_jednego_literalu_jezykowego()
    {
        var zle = SlowaWKodzie(HudSource());

        Assert.AreEqual(0, zle.Count,
            "w `Hud.cs` stoi literał, którego katalog nie zna: " + ZPowodami(zle));
    }

    [TestMethod]
    public void W_wyczyszczonych_metodach_FirstRun_nie_ma_ani_jednego_slowa()
    {
        // 6.D99: `StationLine`, `Faza` i `HelpLine` — a nie cały `FirstRun.cs`.
        // Reszta pliku składa telemetrię i odmowy argumentów, i te są poza zakresem
        // tej pozycji; skan całego pliku zapaliłby się na nich i zostałby wyłączony,
        // czyli bramka zniknęłaby razem z tym, czego miała pilnować.
        var source = Zrodlo("src", "Game", "FirstRun.cs");
        foreach (var naglowek in MetodyFirstRun)
        {
            var zle = SlowaWKodzie(CialoMetody(source, naglowek));
            Assert.AreEqual(0, zle.Count,
                $"w `{naglowek}` stoi literał, którego katalog nie zna: "
                + ZPowodami(zle));
        }
    }

    /// <summary>
    /// Dwa odrzucone literały, dwa RÓŻNE zdania — 6.D130.
    ///
    /// <para><b>Skąd.</b> Podmiana <c>"Esc"</c> na <c>"Escape"</c> zapalała bramkę
    /// sterowania komunikatem „stoi literał językowy", a <c>Escape</c> polskim słowem
    /// nie jest — bramka odrzucała z innego powodu, niż mówiła, i kierowała
    /// szukającego w złe miejsce.</para>
    ///
    /// <para><b>Wejścia syntetyczne, bo na dzisiejszym drzewie obie bramki są
    /// zielone</b> i żadnego komunikatu nie widać. To jest ta sama konieczność, co
    /// przy 6.D115: kontrola na samym drzewie nie odróżniłaby zdania poprawionego od
    /// niepoprawionego.</para>
    /// </summary>
    [TestMethod]
    public void Odrzucony_literal_mowi_KTORY_z_dwoch_powodow_go_dotyczy()
    {
        var slowo = SlowaWKodzie("var t = \"Pr\u0119dko\u015b\u0107\";");
        var klawisz = SlowaWKodzie("var t = \"Escape\";");

        CollectionAssert.AreEqual(new[] { "Pr\u0119dko\u015b\u0107" }, slowo,
            "polskie słowo przestało być odrzucane — reszta tego testu mierzyłaby nic");
        CollectionAssert.AreEqual(new[] { "Escape" }, klawisz,
            "nazwa klawisza spoza `NazwyKlawiszy` przestała być odrzucana");

        var zdanieOSlowie = ZPowodami(slowo);
        var zdanieOKlawiszu = ZPowodami(klawisz);

        Assert.AreNotEqual(zdanieOSlowie, zdanieOKlawiszu,
            "oba odrzucenia dają to samo zdanie: " + zdanieOSlowie);
        StringAssert.Contains(zdanieOSlowie, "literał językowy",
            "odrzucone polskie słowo nie jest nazwane literałem językowym: "
            + zdanieOSlowie);
        StringAssert.Contains(zdanieOKlawiszu, "nazwa klawisza silnika",
            "odrzucona nazwa klawisza nadal opisana jako polszczyzna: "
            + zdanieOKlawiszu);
        Assert.IsFalse(zdanieOKlawiszu.Contains("literał językowy", StringComparison.Ordinal),
            "zdanie o klawiszu nadal niesie słowo o polszczyźnie: " + zdanieOKlawiszu);
    }

    /// <summary>
    /// Ocena ryzyka kolizji jest mierzona na KORPUSIE BRAMKI — 6.D153.
    ///
    /// <para><b>Skąd pozycja.</b> Docstring <see cref="NazwyKlawiszySilnika"/> podawał
    /// liczby policzone na <c>src/Game/</c> Z KOMENTARZAMI i z <c>UiText.cs</c>, czyli
    /// tam, gdzie bramka nie sięga. Ocena szersza niż zasięg przyrządu zawyża ryzyko
    /// i jednocześnie pomija to, które istnieje — a że brzmi jak pomiar, nikt jej nie
    /// sprawdza. Ten test zabiera jej możliwość rozjechania się po cichu.</para>
    ///
    /// <para><b>Pierwsza połowa wychodzi ZIELONA i to jest ODPOWIEDŹ, nie brak
    /// pomiaru.</b> W korpusie bramki nie ma dziś ani jednej OSIĄGALNEJ kolizji:
    /// wszystkie siedem nazw klawiszy, które w nim stoją, przechodzi przez
    /// <see cref="WzorzecSlowa"/> niezgłoszonych, bo nie mają dwóch liter pod rząd.
    /// Żeby ta zieleń nie znaczyła „bramka oślepła", stoi w parze z drugą połową:
    /// cztery nazwy widziane tylko w komentarzach są tą samą drogą ZGŁASZALNE.
    /// Para mierzy, że różnicę robi mechanizm, a nie zanik pilnowania.</para>
    /// </summary>
    [TestMethod]
    public void Ocena_ryzyka_kolizji_jest_mierzona_na_korpusie_bramki()
    {
        var zrodla = ZrodlaGry();
        var literaly = zrodla
            .SelectMany(sciezka => Literaly(File.ReadAllText(sciezka)))
            .ToList();

        // Dolne ostrza na SAM SKAN. Bez nich pusty korpus dałby „zero osiągalnych
        // kolizji" i test meldowałby sprawdzenie, którego nie zrobił (6.D27).
        Assert.IsTrue(zrodla.Count >= PlikowWZasieguBramki,
            $"korpus bramki ma {zrodla.Count} plików wobec zmierzonych "
            + $"{PlikowWZasieguBramki} — skan zawęził się i mierzy nie to co trzeba");
        Assert.IsTrue(literaly.Count >= LiteralowWZasieguBramki,
            $"korpus bramki ma {literaly.Count} literałów wobec zmierzonych "
            + $"{LiteralowWZasieguBramki} — akapit o ryzyku opisuje inny korpus");
        var roznych = literaly.Distinct(StringComparer.Ordinal).Count();
        Assert.IsTrue(roznych >= RoznychLiteralowWZasieguBramki,
            $"różnych literałów jest {roznych} wobec zmierzonych "
            + $"{RoznychLiteralowWZasieguBramki} — jak wyżej");

        // ZBIÓR, nie liczba: na 40 rewizjach `src/Game` liczby zmieniły się w 29
        // przejściach na 39, a ten zbiór w dwóch.
        var wKorpusie = literaly
            .Where(NazwyKlawiszySilnika.Contains)
            .Distinct(StringComparer.Ordinal)
            .OrderBy(nazwa => nazwa, StringComparer.Ordinal)
            .ToArray();
        CollectionAssert.AreEqual(NazwyKlawiszyWZasieguBramki, wKorpusie,
            "zbiór nazw klawiszy w korpusie bramki rozjechał się z akapitem "
            + "o ryzyku przy `NazwyKlawiszySilnika`: " + string.Join(", ", wKorpusie));

        // Połowa pierwsza: żadna z nich nie jest ZGŁASZALNA, więc do
        // `PowodOdrzucenia` nie ma jak trafić.
        var osiagalne = wKorpusie
            .Where(nazwa => SlowaWKodzie($"var t = \"{nazwa}\";").Count > 0)
            .ToArray();
        CollectionAssert.AreEqual(Array.Empty<string>(), osiagalne,
            "nazwa klawisza z korpusu bramki stała się zgłaszalna, więc kolizja "
            + "przestała być nieosiągalna: " + string.Join(", ", osiagalne));

        // Połowa druga — czerwona para do tamtej zieleni. Gdyby sito przestało
        // cokolwiek zgłaszać, powyższe zero brałoby się z zaniku pilnowania.
        foreach (var nazwa in NazwyKlawiszyTylkoWKomentarzach)
        {
            Assert.IsTrue(NazwyKlawiszySilnika.Contains(nazwa),
                $"`{nazwa}` przestało być nazwą członu `Godot.Key` — materiał "
                + "pomiaru zestarzał się i akapit o ryzyku mówi o nieistniejącym");
            Assert.AreEqual(1, SlowaWKodzie($"var t = \"{nazwa}\";").Count,
                $"`{nazwa}` przestało być zgłaszalne — wtedy zero wyżej nie mówi "
                + "o strukturze nazw, tylko o tym, że sito nic nie zgłasza");
            Assert.IsFalse(wKorpusie.Contains(nazwa, StringComparer.Ordinal),
                $"`{nazwa}` zeszło z komentarza do kodu skanowanego — kolizja "
                + "jest odtąd osiągalna i akapit o ryzyku wymaga przeliczenia");
        }
    }

    /// <summary>
    /// Kontrola przyrządu: zbiór nazw klawiszy jest CZYTANY z silnika — 6.D130.
    ///
    /// <para>Lista przepisana z ręki dałaby dziś ten sam werdykt dla
    /// <c>"Escape"</c> i rozjechałaby się przy pierwszej zmianie w Godocie. Liczba
    /// jest zmierzona: <b>193</b> nazwy na 11.09.2026.</para>
    /// </summary>
    [TestMethod]
    public void Zbior_nazw_klawiszy_pochodzi_z_wyliczenia_silnika()
    {
        Assert.IsTrue(NazwyKlawiszySilnika.Count > 150,
            $"nazw klawiszy jest {NazwyKlawiszySilnika.Count} — zbiór nie pochodzi "
            + "z wyliczenia silnika albo wyliczenie zniknęło");
        Assert.IsTrue(NazwyKlawiszySilnika.SetEquals(Enum.GetNames(typeof(Key))),
            "zbiór rozjechał się z `Enum.GetNames(typeof(Key))`");

        // `Esc` jest napisem WYTŁOCZONYM NA KLAWISZU i nazwą członka `Key` NIE jest —
        // to jest cała różnica między `NazwyKlawiszy` a tym zbiorem.
        Assert.IsFalse(NazwyKlawiszySilnika.Contains("Esc"),
            "`Esc` znalazł się w wyliczeniu silnika — oba zbiory przestały się różnić");
        Assert.IsTrue(NazwyKlawiszySilnika.Contains("Escape"),
            "`Escape` zniknął z wyliczenia silnika");

        // Żadna nazwa klawisza nie niesie polskiego znaku — zmierzone, nie założone.
        // Gdyby niosła, rozróżnienie z `PowodOdrzucenia` myliłoby się na niej.
        Assert.AreEqual(0,
            NazwyKlawiszySilnika.Count(n => Regex.IsMatch(n, "[\u0105\u0107\u0119\u0142\u0144\u00f3\u015b\u017a\u017c]")),
            "nazwa klawisza z polskim znakiem — rozróżnienie powodów myli się na niej");
    }

    /// <summary>Źródło <c>KeyNames.cs</c> — jedno miejsce, bo czytają je trzy testy.</summary>
    private static string KeyNamesSource() => Zrodlo("src", "Game", "Input", "KeyNames.cs");

    [TestMethod]
    public void W_tablicy_KeyNames_nie_ma_ani_jednego_slowa()
    {
        var source = KeyNamesSource();

        // Pusta lista członów przeprowadziłaby ten test przez pętlę bez ani jednego
        // sprawdzenia — zmierzone kontrolą KN-3 z 6.D143, która zapaliła WYŁĄCZNIE
        // test rozstrzygnięć. Bramka nie ma mieć dziury, którą łata sąsiad.
        Assert.AreEqual(1, CzlonyKeyNames.Length,
            $"skanowanych członów `KeyNames.cs` jest {CzlonyKeyNames.Length}, "
            + "a pomiar z 11.09.2026 dał jeden");

        foreach (var czlon in CzlonyKeyNames)
        {
            var cialo = CialoMetody(source, czlon);

            // Dolne ostrze na SAM SKAN, nie na wynik. Ciało wzięte nie tego członu
            // albo puste przeszłoby pętlę niżej bez ani jednego sprawdzenia — a to
            // jest dokładnie ta rodzina, którą projekt tropi od 6.D27.
            Assert.AreEqual(LiteralowWTablicyKeyNames, Literaly(cialo).Count,
                $"skan widzi {Literaly(cialo).Count} literałów w `{czlon}`, a pomiar "
                + $"z 11.09.2026 dał {LiteralowWTablicyKeyNames} — nagłówek się "
                + "rozjechał albo tablica urosła");

            var zle = SlowaWKodzie(cialo);
            Assert.AreEqual(0, zle.Count,
                $"w `{czlon}` stoi literał, którego katalog nie zna: " + ZPowodami(zle));
        }
    }

    /// <summary>
    /// Dla KAŻDEGO literału <c>KeyNames.cs</c> wiadomo, czy bramka go widzi — 6.D143.
    ///
    /// <para>Pole „Skończone, gdy" pozycji żądało tego z liczbą, nie z opinią. Liczba
    /// jest tu po obu stronach: trzy w pliku, dwa w zakresie, jeden poza — i suma ma
    /// się zgadzać, żeby literał dopisany gdziekolwiek w tym pliku musiał dostać
    /// rozstrzygnięcie, zamiast wpaść w szczelinę między testami.</para>
    ///
    /// <para><b>Trzeci literał jest tu pokazany jako ZGŁASZANY, a nie przemilczany.</b>
    /// Wyłączenie go z zakresu jest decyzją, a decyzja niewidoczna w teście
    /// nieodróżnialna jest od przeoczenia — więc test pokazuje, że gdyby skanować
    /// cały plik, bramka by się zapaliła, i dopiero potem mówi, dlaczego nie
    /// skanujemy.</para>
    /// </summary>
    [TestMethod]
    public void Kazdy_literal_KeyNames_ma_ROZSTRZYGNIECIE_czy_bramka_go_widzi()
    {
        var source = KeyNamesSource();
        var wPliku = Literaly(source);
        var wZakresie = CzlonyKeyNames
            .SelectMany(c => Literaly(CialoMetody(source, c)))
            .ToList();
        var pozaZakresem = wPliku.Except(wZakresie, StringComparer.Ordinal).ToList();

        Assert.AreEqual(LiteralowWKeyNames, wPliku.Count,
            $"`KeyNames.cs` ma {wPliku.Count} literałów, a pomiar z 11.09.2026 dał "
            + $"{LiteralowWKeyNames}: " + string.Join(" | ", wPliku));
        Assert.AreEqual(LiteralowWKeyNames, wZakresie.Count + pozaZakresem.Count,
            "podział na zakres i poza zakres przestał się sumować do pliku — literał "
            + "bez rozstrzygnięcia wpadłby w szczelinę między testami");

        // Dwa w zakresie, i KAŻDY przechodzi z innego powodu — to jest cała treść
        // rozróżnienia z 6.D130, tu wykonana na prawdziwym pliku.
        CollectionAssert.AreEqual(new[] { "Esc", "input.key.space" }, wZakresie,
            "tablica `Nazwy` niesie inne literały niż w pomiarze: "
            + string.Join(" | ", wZakresie));
        Assert.IsTrue(NazwyKlawiszy.Contains("Esc", StringComparer.Ordinal),
            "„Esc” przechodzi wyjątkiem `NazwyKlawiszy` i tak jest tu zapisane — "
            + "patrz rozstrzygnięcie 6.D142 o tym, ile ten wyjątek dziś robi");
        Assert.IsTrue(UiText.Keys.Contains("input.key.space"),
            "„input.key.space” przechodzi jako KLUCZ KATALOGU, nie jako wyjątek — "
            + "gdyby zniknął z katalogu, bramka zapaliłaby się na nim słusznie");

        // Jeden poza zakresem — i jest nim komunikat `throw`, a nie cokolwiek.
        Assert.AreEqual(1, pozaZakresem.Count,
            "poza zakresem stoi " + pozaZakresem.Count + " literałów zamiast jednego: "
            + string.Join(" | ", pozaZakresem));
        // Wzorzec, a nie dopasowanie napisu z wcięciem: przeformatowanie pliku nie
        // jest zmianą, o której to zdanie mówi, więc nie ma go zapalać.
        Assert.IsTrue(
            Regex.IsMatch(source,
                @"throw new KeyNotFoundException\(\s*\$""" + Regex.Escape(pozaZakresem[0])),
            "literał spoza zakresu przestał być komunikatem `throw` — granica członu "
            + "mówi „tablica to tekst, `throw` to diagnostyka” i właśnie przestała "
            + "być prawdziwa");

        // I dowód, że wyłączenie jest DECYZJĄ: skanowany, zapaliłby bramkę.
        CollectionAssert.AreEqual(new[] { pozaZakresem[0] },
            SlowaWKodzie(source),
            "cały plik przestał zgłaszać dokładnie ten jeden literał — jeśli zgłasza "
            + "zero, skan przestał działać; jeśli więcej, doszła diagnostyka i granicę "
            + "członu trzeba przeczytać jeszcze raz");
    }

    [TestMethod]
    public void W_plikach_sterowania_nie_ma_ani_jednego_slowa()
    {
        foreach (var plik in new[] { "DriverActions.cs", "EmergencyBrake.cs" })
        {
            var zle = SlowaWKodzie(
                Zrodlo("src", "Game", "Input", plik));
            Assert.AreEqual(0, zle.Count,
                $"w `{plik}` stoi literał, którego katalog nie zna: " + ZPowodami(zle));
        }
    }

    /// <summary>
    /// Trzy wiersze złożone z katalogu brzmią CO DO ZNAKU tak, jak przed 6.D99.
    ///
    /// <para><b>Oczekiwane napisy są tu wpisane z ręki i to jest wybór.</b> Reszta tego
    /// pliku pilnuje, żeby tekstu nie było w dwóch miejscach; tutaj druga kopia jest
    /// całą treścią sprawdzenia — pole „Skończone, gdy" 6.D99 żąda wypisu tego samego
    /// co do znaku, a porównanie z napisem złożonym z tego samego katalogu nie
    /// sprawdziłoby niczego. Napisy pochodzą z drzewa sprzed przeniesienia
    /// (<c>3b896d2</c>); trzy pozostałe wiersze panelu — stacji, drzwi i pozycji —
    /// są sprawdzone zrzutem ekranu, bo je widać.</para>
    /// </summary>
    [TestMethod]
    public void Wiersze_zlozone_z_katalogu_brzmia_co_do_znaku_tak_jak_przed_przenosinami()
    {
        Assert.AreEqual(
            "W ciąg  ·  S hamulec  ·  X wybieg  ·  "
            + "Spacja hamulec awaryjny (= pełny służbowy)  ·  C widok  ·  R od nowa  ·  "
            + "Esc wyjście",
            DriverActions.Help);

        Assert.AreEqual(
            "C widok  ·  Esc wyjście  ·  "
            + "prowadzi rdzeń: W, S, X, Spacja, R nie działają",
            DriverActions.HelpWhenTheCoreDrives);

        Assert.AreEqual(
            "HAMULEC AWARYJNY (Spacja) = pełny hamulec SŁUŻBOWY 1.00 — "
            + "model nie ma osobnego stopnia awaryjnego",
            EmergencyBrake.Notice(DriverKeys.EmergencyBraking, DriverCommand.FullServiceBrake));
    }

    [TestMethod]
    public void Wycinanie_ciala_metody_bierze_te_metode_a_nie_nastepna()
    {
        // Kontrola przyrządu dla `CialoMetody`. Dwa kształty, bo w drzewie są dwa:
        // metoda z blokiem i metoda wyrażeniowa. Gdyby wycinanie brało za dużo,
        // test wyżej zapalałby się na słowach z sąsiedniej metody; gdyby brało za
        // mało — nie zapalałby się nigdy i byłby zielony z niewiedzy.
        const string Syntetyk = """
            private string Blokowa()
            {
                if (x) { return "w bloku"; }
                return "koniec bloku";
            }

            private string Wyrazeniowa() => "wyrażeniowa";

            private string Dalsza() => "nie ta metoda";
            """;

        var blok = CialoMetody(Syntetyk, "private string Blokowa()");
        StringAssert.Contains(blok, "koniec bloku");
        Assert.IsFalse(blok.Contains("wyrażeniowa", StringComparison.Ordinal),
            "wycięte ciało sięga poza metodę: " + blok);

        var wyrazenie = CialoMetody(Syntetyk, "private string Wyrazeniowa()");
        StringAssert.Contains(wyrazenie, "wyrażeniowa");
        Assert.IsFalse(wyrazenie.Contains("nie ta metoda", StringComparison.Ordinal),
            "metoda wyrażeniowa wycięta razem z następną: " + wyrazenie);
    }

    [TestMethod]
    public void Skan_literalow_widzi_te_ktore_sa_i_nie_bierze_sciezki_wezla_za_slowo()
    {
        // Kontrola przyrządu: pusta lista wyżej byłaby zielona także wtedy, gdyby
        // wzorzec przestał cokolwiek łapać albo gdyby odsianie odsiewało wszystko.
        var kod = HudSource();
        var literaly = Literaly(kod);
        Assert.IsTrue(literaly.Count >= 10,
            $"skan widzi {literaly.Count} literałów w `Hud.cs` — wzorzec się rozjechał");
        Assert.IsTrue(literaly.Any(l => l.Contains("Panel/Rows", StringComparison.Ordinal)),
            "skan nie widzi ścieżek węzłów, więc nie ma czego odsiewać");
        Assert.IsTrue(literaly.Contains("font_size"),
            "skan nie widzi nazw właściwości motywu");

        // I że wzorzec „słowa" NAPRAWDĘ łapie słowo: to on rozstrzyga cały test wyżej.
        Assert.IsTrue(Regex.IsMatch("chainage {0} m", @"\p{L}{2,}"));
        Assert.IsTrue(Regex.IsMatch("ciąg {0}", @"\p{L}{2,}"));
        Assert.IsFalse(Regex.IsMatch("   ", @"\p{L}{2,}"));
        Assert.IsFalse(Regex.IsMatch("{0} m / {1} m", @"\p{L}{2,}"),
            "sama jednostka `m` nie jest słowem — jednostki mają zostać");

        // 6.D99: odsianie identyfikatorów silnika ODSIEWA je i NIE odsiewa zdania.
        // Bez drugiej połowy reguła „to identyfikator" mogłaby zjeść cały werdykt.
        CollectionAssert.AreEqual(
            new List<string>(),
            SlowaWKodzie("\"driver_power\" \"view_toggle\" \"font_size\" \"Esc\" \"F1\""),
            "odsianie nie objęło nazwy akcji, motywu albo napisu na klawiszu");
        CollectionAssert.AreEqual(
            new List<string> { "koniec przejazdu", "od nowa" },
            SlowaWKodzie("\"koniec przejazdu\" \"od nowa\""),
            "odsianie zjadło zdanie po polsku — werdykt byłby zielony z niewiedzy");

        // Cięcie dziur tnie DZIURY, a nie tekst wokół nich.
        Assert.AreEqual(" ", BezDziur("{binding.KeyName} {binding.Meaning}"));
        Assert.AreEqual("brak dalszych stacji   ", BezDziur("brak dalszych stacji   {0}"));
    }

    private static string RepositoryRoot()
    {
        var directory = new DirectoryInfo(AppContext.BaseDirectory);
        while (directory is not null)
        {
            if (File.Exists(Path.Combine(directory.FullName, "CLAUDE.md")))
            {
                return directory.FullName;
            }

            directory = directory.Parent;
        }

        Assert.Inconclusive("Test uruchomiony poza drzewem repozytorium.");
        throw new InvalidOperationException();
    }

    /// <summary>
    /// Wyjątek na nazwy klawiszy ma PRZEDMIOT — 6.D142.
    ///
    /// <para>Każda pozycja <c>NazwyKlawiszy</c> musi być nazwą, którą
    /// <c>KeyNames</c> naprawdę zwraca. Bez tego wiązania wyjątek przeżyłby swój
    /// przedmiot: „Esc" zniknęłoby z <c>KeyNames.cs</c>, a lista zostałaby jako
    /// zdanie o kodzie, którego nikt już nie czyta — dokładnie ta rodzina, którą
    /// projekt tropi od 6.D27.</para>
    ///
    /// <para>Zawieranie, a nie równość: <c>KeyNames</c> zwraca też „Spacja",
    /// czyli wartość z katalogu, którą bramka przepuszcza z INNEGO powodu
    /// (<c>UiText.Keys.Contains</c>). Żądanie równości zmusiłoby do wpisania jej
    /// tutaj i zrobiłoby z wyjątku drugą kopię katalogu.</para>
    /// </summary>
    [TestMethod]
    public void Wyjatek_na_nazwy_klawiszy_ma_PRZEDMIOT_w_KeyNames()
    {
        var zKeyNames = KeyNames.Znane.Select(KeyNames.For).ToHashSet(StringComparer.Ordinal);

        Assert.IsTrue(zKeyNames.Count >= 2,
            $"`KeyNames` zwraca {zKeyNames.Count} nazw — zbiór skurczył się i reszta "
            + "tego testu nie mierzyłaby niczego");

        var bezPrzedmiotu = NazwyKlawiszy.Where(n => !zKeyNames.Contains(n)).ToArray();
        Assert.AreEqual(0, bezPrzedmiotu.Length,
            "wyjątek na nazwy klawiszy wymienia napis, którego `KeyNames` nie zwraca: "
            + string.Join(", ", bezPrzedmiotu)
            + " — wyjątek ma umierać razem ze swoim przedmiotem, nie po nim");

        Assert.AreEqual(1, NazwyKlawiszy.Length,
            $"lista ma {NazwyKlawiszy.Length} pozycji, a pomiar z 11.09.2026 mówił jedną");
    }

    /// <summary>
    /// Wyjątek na „Esc" jest BEZCZYNNY, a mechanizm jest OSIĄGALNY — 6.D142.
    ///
    /// <para><b>Obie połowy w jednym teście, bo dopiero razem są rozstrzygnięciem.</b>
    /// Osobno pierwsza brzmi jak wniosek „skasować", a druga jak „zostawić";
    /// rozstrzygnięcie z <see cref="NazwyKlawiszy"/> bierze się z ich zestawienia.</para>
    ///
    /// <para><b>Bezczynność ma zmierzoną PRZYCZYNĘ i przyczyna leży poza tą listą.</b>
    /// Z „Esc" zostaje po zdjęciu jednostek <c>"E c"</c> — jednostka <c>"s"</c> zjada
    /// mu literę — więc do pytania „czy stoi w <c>NazwyKlawiszy</c>" wynik i tak się
    /// nie przykłada. Ten test pilnuje właśnie tego wiązania: gdy <c>"s"</c> zniknie
    /// z <see cref="Jednostki"/>, wyjątek stanie się działający, a zdanie
    /// o bezczynności — nieprawdziwe. Zapali się wtedy tutaj, nie po dwóch dniach.</para>
    ///
    /// <para><b>Osiem nazw, a nie jedna</b>, bo jedna nie odróżniłaby „mechanizm
    /// działa" od „akurat ta nazwa jest słowem". Wszystkie osiem zmierzone
    /// 11.09.2026 jako zgłaszane.</para>
    /// </summary>
    [TestMethod]
    public void Wyjatek_na_Esc_jest_BEZCZYNNY_a_mechanizm_jest_OSIAGALNY()
    {
        // 1. Przyczyna bezczynności — i to ona, nie sam wynik, jest tu pilnowana.
        Assert.IsTrue(Regex.IsMatch("Esc", WzorzecSlowa),
            "„Esc” przestało być słowem samo z siebie — wtedy bezczynność wyjątku "
            + "`NazwyKlawiszy` nie bierze się z `Jednostki` i akapit o niej jest "
            + "nieprawdziwy");
        var escBezJednostek = BezJednostek("Esc");
        Assert.AreEqual("E c", escBezJednostek,
            $"`BezJednostek(\"Esc\")` daje teraz \"{escBezJednostek}\", a nie „E c” — "
            + "jeśli `Jednostki` straciły „s”, wyjątek `NazwyKlawiszy` WŁAŚNIE STAŁ SIĘ "
            + "DZIAŁAJĄCY i rozstrzygnięcie 6.D142 trzeba przeczytać jeszcze raz");
        Assert.IsFalse(Regex.IsMatch(BezJednostek(BezDziur("Esc")), WzorzecSlowa),
            "po zdjęciu jednostek „Esc” znów przechodzi przez sito słowa — wyjątek "
            + "przestał być bezczynny, a `NazwyKlawiszy` opisuje go jako bezczynny");

        // 2. Ten sam wniosek zmierzony BRAMKĄ, nie złożony z jej części.
        var zWyjatkiem = SlowaWKodzie("var t = \"Esc\";");
        CollectionAssert.AreEqual(System.Array.Empty<string>(), zWyjatkiem,
            "napis wytłoczony na klawiszu przestał być przepuszczany: "
            + ZPowodami(zWyjatkiem));

        // 3. Mechanizm jest osiągalny — dla nazwy klawisza, która słowem zostaje.
        foreach (var nazwa in NazwyKlawiszyZglaszane)
        {
            var zgloszone = SlowaWKodzie($"var t = \"{nazwa}\";");
            CollectionAssert.AreEqual(new[] { nazwa }, zgloszone,
                $"„{nazwa}” przestało być zgłaszane ({ZPowodami(zgloszone)}) — wyjątek "
                + "`NazwyKlawiszy` nie miałby dla czego zostawać i argument "
                + "z rozstrzygnięcia 6.D142 przestaje działać");
        }

        // 4. Kontrola przyrządu: napis, który NIE jest nazwą klawisza, nadal pada.
        var obcy = SlowaWKodzie("var t = \"Prędkość\";");
        CollectionAssert.AreEqual(new[] { "Prędkość" }, obcy,
            "polskie słowo przestało być odrzucane — reszta tego testu mierzyłaby nic");
    }

    /// <summary>
    /// Ile pozycji zwracał na korpusie STARY czytnik — zmierzone 12.09.2026.
    /// </summary>
    private const int PozycjiStaregoCzytnika = 521;

    /// <summary>
    /// Ile PLIKÓW korpusu stary czytnik czytał inaczej niż leksykalny — 6.D182.
    /// </summary>
    private const int PlikowRozcietychPrzezStaryCzytnik = 2;

    /// <summary>
    /// Czytnik literałów czyta LEKSYKALNIE, a nie wzorcem — 6.D182.
    ///
    /// <para><b>Każdy przypadek pyta o DWIE rzeczy</b>: co zwraca dzisiejszy czytnik
    /// i co na tym samym wejściu zwracał stary. Bez drugiej połowy test byłby zielony
    /// także wtedy, gdyby ktoś przywrócił wzorzec — czyli pilnowałby niczego. Wejście
    /// jest SYNTETYCZNE, bo dla dwóch z czterech konstrukcji drzewo nie ma dziś
    /// przykładu (napis dosłowny, literał znakowy z cudzysłowem), a kontrola bez
    /// wejścia oddzielającego mechanizm od jego braku to pułapka z 6.D147 KN-6.</para>
    /// </summary>
    [TestMethod]
    public void Czytnik_literalow_czyta_leksykalnie_a_nie_wzorcem()
    {
        // 1. Napis interpolowany z zagnieżdżonym cudzysłowem — konstrukcja, która
        //    pozycję 6.D182 otworzyła. Stoi w `RunPlan.cs` dwa razy.
        var interpolowany = "var m = $\"Znane: --{string.Join(\" --\", K)}\";";
        CollectionAssert.AreEqual(
            new[] { "Znane: --{string.Join(\" --\", K)}", " --" },
            Literaly(interpolowany),
            "napis interpolowany z zagnieżdżonym cudzysłowem czytany jest inaczej "
            + "niż w pomiarze 6.D182: " + string.Join(" | ", Literaly(interpolowany)));
        CollectionAssert.AreEqual(
            new[] { "Znane: --{string.Join(", ", K)}" },
            StaryCzytnik(interpolowany),
            "stary czytnik przestał rozcinać to wejście, więc kontrola porównuje "
            + "dziś czytnik sam ze sobą i nie znaczy nic");

        // 2. Napis surowy `$$"""` — jeden taki stoi w `FirstRun.cs` i stary czytnik
        //    rozcinał go na 42 pozycje. Tu skrócony do dwóch wierszy JSON-a.
        var surowy = "var j = $$\"\"\"\n{ \"a\": \"{{X}}\" }\n\"\"\";";
        CollectionAssert.AreEqual(
            new[] { "\n{ \"a\": \"{{X}}\" }\n" },
            Literaly(surowy),
            "napis surowy przestał być JEDNYM literałem: "
            + string.Join(" | ", Literaly(surowy)));
        Assert.AreEqual(5, StaryCzytnik(surowy).Count,
            "stary czytnik przestał rozcinać napis surowy — patrz wyżej, kontrola "
            + "straciłaby wtedy przedmiot");

        // 3. Napis dosłowny `@"…"` z podwojonym cudzysłowem. Drzewo nie ma dziś ani
        //    jednego, więc to jest wejście syntetyczne i tak jest tu nazwane.
        var doslowny = "var v = @\"a \"\"b\"\" c\";";
        CollectionAssert.AreEqual(new[] { "a \"\"b\"\" c" }, Literaly(doslowny),
            "napis dosłowny przestał być JEDNYM literałem: "
            + string.Join(" | ", Literaly(doslowny)));
        Assert.AreEqual(3, StaryCzytnik(doslowny).Count,
            "stary czytnik przestał rozcinać napis dosłowny");

        // 4. Literał znakowy niosący cudzysłów. Jeden taki przesuwa parzystość
        //    cudzysłowów w całym pliku, więc psuje KAŻDY literał za sobą.
        var znakowy = "if (c == '\"') { x = \"ok\"; }";
        CollectionAssert.AreEqual(new[] { "ok" }, Literaly(znakowy),
            "literał znakowy z cudzysłowem przestał być pomijany: "
            + string.Join(" | ", Literaly(znakowy)));
        CollectionAssert.AreEqual(new[] { "') { x = " }, StaryCzytnik(znakowy),
            "stary czytnik przestał się mylić na literale znakowym");

        // 5. Komentarz z cudzysłowem — czytnik pomija go sam, bez obcinacza wierszy.
        var komentarz = "var x = 1; // powiedział \"cześć\"\nvar y = \"tak\";";
        CollectionAssert.AreEqual(new[] { "tak" }, Literaly(komentarz),
            "komentarz przestał być pomijany przez sam czytnik: "
            + string.Join(" | ", Literaly(komentarz)));
        Assert.AreEqual(2, StaryCzytnik(komentarz).Count,
            "stary czytnik przestał czytać literały z komentarza na końcu wiersza");
    }

    /// <summary>
    /// Korpus NADAL niesie konstrukcje, których stary czytnik nie czytał — 6.D182.
    ///
    /// <para>Test na prawdziwym drzewie, obok kontroli na wejściu syntetycznym.
    /// Mówi dwie rzeczy naraz: ile pozycji dawał stary czytnik i w ilu plikach obie
    /// drogi się rozchodzą. Gdyby <c>src/Game/</c> przestało nieść takie konstrukcje,
    /// ten test zapali się i powie o tym wprost — zamiast cicho stać się zielonym
    /// z niczego.</para>
    /// </summary>
    [TestMethod]
    public void Korpus_niesie_konstrukcje_ktorych_stary_czytnik_nie_czytal()
    {
        var stare = 0;
        var nowe = 0;
        var rozciete = new List<string>();
        foreach (var sciezka in ZrodlaGry())
        {
            var kod = File.ReadAllText(sciezka);
            var s = StaryCzytnik(KodBezKomentarzyDlaStaregoCzytnika(kod));
            var n = Literaly(kod);
            stare += s.Count;
            nowe += n.Count;
            if (!s.SequenceEqual(n, StringComparer.Ordinal))
            {
                rozciete.Add(Path.GetFileName(sciezka));
            }
        }

        Assert.AreEqual(PozycjiStaregoCzytnika, stare,
            $"stary czytnik daje dziś {stare} pozycji wobec zmierzonych "
            + $"{PozycjiStaregoCzytnika} — liczba w akapicie przy `Literaly` "
            + "opisuje inny korpus");
        Assert.AreEqual(LiteralowWZasieguBramki, nowe,
            $"czytnik leksykalny daje dziś {nowe} literałów wobec zmierzonych "
            + $"{LiteralowWZasieguBramki}");
        Assert.AreEqual(PlikowRozcietychPrzezStaryCzytnik, rozciete.Count,
            "pliki, na których obie drogi się rozchodzą, to dziś "
            + string.Join(", ", rozciete) + $" ({rozciete.Count}), a pomiar 6.D182 "
            + $"dał {PlikowRozcietychPrzezStaryCzytnik} — jeśli ZERO, korpus "
            + "przestał nieść konstrukcję, dla której ten czytnik powstał");
        CollectionAssert.AreEqual(new[] { "FirstRun.cs", "RunPlan.cs" },
            rozciete.OrderBy(n => n, StringComparer.Ordinal).ToList(),
            "rozchodzą się inne pliki niż w pomiarze: " + string.Join(", ", rozciete));
    }

    /// <summary>
    /// Ciało DEKLARACJI — bloku, wyrażenia albo inicjalizatora — 6.D183.
    ///
    /// <para><b>Dlaczego obok <see cref="CialoMetody"/>, a nie zamiast.</b>
    /// <c>CialoMetody</c> rozstrzyga formę po tym, co stoi pierwsze: <c>{</c> czy
    /// <c>;</c>. Na trzech członach z mapy <see cref="ZrodlaHud"/> myli się, bo obie
    /// odpowiedzi są złe: <c>public static string Help { get; } = string.Join(…);</c>
    /// ma <c>{</c> przed <c>;</c>, więc dostaje <c>{ get; }</c> i gubi CAŁY
    /// inicjalizator, w którym stoi szablon. <b>Nie jest to usterka ukryta —
    /// zapaliłaby asercję obecności znanych napisów</b> — ale cicho zwęziłaby zakres
    /// skanu, a bramka mierząca mniej, niż twierdzi, to usterka z rodziny 6.D27.</para>
    ///
    /// <para>Reguła jest mała i pokrywa wszystkie jedenaście członów mapy: jeśli
    /// <c>{</c> na głębokości zero stoi przed <c>=</c>, dopasuj klamry — a potem,
    /// jeśli zaraz za klamrą stoi <c>=</c>, ciągnij dalej do średnika na głębokości
    /// zero. Inaczej idź wprost do tego średnika. Napisy i komentarze pomija
    /// <see cref="PominNieNapis"/> i <see cref="CzytajLiteral"/> — te same prymitywy,
    /// które 6.D182 postawiło pod czytnik literałów, i bez nich średnik ze środka
    /// napisu kończyłby deklarację w złym miejscu.</para>
    /// </summary>
    private static string CialoDeklaracji(string source, string naglowek)
    {
        var start = source.IndexOf(naglowek, StringComparison.Ordinal);
        Assert.IsTrue(start >= 0,
            $"nie ma członu `{naglowek}` — skan mierzyłby nie ten człon albo nic");

        var glebia = 0;
        var i = start;
        var poKlamrze = -1;
        while (i < source.Length)
        {
            var po = PominNieNapis(source, i, source.Length);
            if (po != i)
            {
                i = po;
                continue;
            }

            if (PrefiksLiteralu(source, i, source.Length) >= 0)
            {
                i = CzytajLiteral(source, i, source.Length, new List<string>());
                continue;
            }

            var znak = source[i];
            if (znak == '=' && glebia == 0 && poKlamrze < 0)
            {
                // Forma wyrażeniowa albo inicjalizator: kończy średnik, nie klamra.
                break;
            }

            if (znak == '{')
            {
                glebia++;
            }
            else if (znak == '}')
            {
                glebia--;
                if (glebia == 0)
                {
                    poKlamrze = i;
                    // `{ get; } =` ciągnie się dalej; blok metody kończy się tutaj.
                    var j = i + 1;
                    while (j < source.Length && char.IsWhiteSpace(source[j]))
                    {
                        j++;
                    }

                    if (j >= source.Length || source[j] != '=')
                    {
                        return source[start..(i + 1)];
                    }
                }
            }

            i++;
        }

        while (i < source.Length)
        {
            var po = PominNieNapis(source, i, source.Length);
            if (po != i)
            {
                i = po;
                continue;
            }

            if (PrefiksLiteralu(source, i, source.Length) >= 0)
            {
                i = CzytajLiteral(source, i, source.Length, new List<string>());
                continue;
            }

            var znak = source[i];
            glebia += znak == '{' ? 1 : znak == '}' ? -1 : 0;
            if (znak == ';' && glebia == 0)
            {
                return source[start..i];
            }

            i++;
        }

        Assert.Fail($"nie domknięto deklaracji `{naglowek}`");
        throw new InvalidOperationException();
    }

    /// <summary>
    /// Argumenty napisowe <see cref="Hud"/>.<c>Update</c>, w kolejności sygnatury — 6.D183.
    /// </summary>
    private static readonly string[] ArgumentyNapisoweHud =
    {
        "nextStation", "mode", "station", "signalling", "view", "emergency", "help",
    };

    /// <summary>
    /// Skąd bierze się każdy argument napisowy <c>Hud.Update</c> — mapa prześledzona
    /// ręcznie 12.09.2026 i pilnowana trzema bramkami — 6.D183.
    ///
    /// <para><b>Dlaczego mapa WPISANA, a nie wyprowadzona.</b> Prześledzenie wartości
    /// przez pola, właściwości i metody w kilku plikach to analiza przepływu, a ta
    /// wymaga rozbioru składni C# — czyli zależności, przed którą <c>CLAUDE.md</c> §8
    /// każe przerwać. Mapa jest więc wpisana, ale NIE jest gołym twierdzeniem: pilnują
    /// jej <see cref="Kazde_przypisanie_Text_stoi_w_ciele_Hud_Update"/> (że droga na
    /// ekran jest JEDNA) i <see cref="Kazdy_argument_napisowy_Hud_Update_ma_zrodlo"/>
    /// (że argumentów jest dokładnie tyle, ile mapa opisuje). Ósmy argument dopisany
    /// do <c>Update</c> zapala drugą z nich, zamiast po cichu wypaść z pomiaru.</para>
    ///
    /// <para><b>Czego mapa NIE obejmuje i mówi o tym wprost:</b> wartości spoza kodu —
    /// nazwy stacji z <c>data/network/</c> (argument <c>nextStation</c>) — oraz nazwy
    /// członów wyliczeń renderowane przez <c>{…}</c> (<c>AuthorityLimit</c>,
    /// <c>ProtectionAction</c>, <c>DoorPhase</c>). Te drugie DOCIERAJĄ na ekran, ale
    /// literałami nie są, więc żadna rodzina liczona po literałach ich nie widzi.
    /// Osobna pozycja, nie cichy brak.</para>
    /// </summary>
    private static readonly (string Argument, string Plik, string Naglowek)[] ZrodlaHud =
    {
        ("nextStation", "FirstRun.cs", "private void UpdateHud()"),

        ("mode", "FirstRun.cs", "private string _mode ="),
        ("mode", "RunPlan.cs", "public string Mode =>"),

        ("station", "FirstRun.cs", "private string StationLine()"),
        ("station", "FirstRun.cs", "private static string Faza(DoorPhase phase)"),
        ("station", "FirstRun.cs", "private const string BladZatrzymaniaFormat ="),

        ("signalling", "FirstRun.cs", "private string SignallingLine()"),
        ("signalling", "SignallingHud.cs", "public const string WithoutSignalling ="),
        ("signalling", "SignallingHud.cs", "public const string NotOnPlanYet ="),
        ("signalling", "SignallingHud.cs", "public const string WithoutProtection ="),
        ("signalling", "SignallingHud.cs", "public const string BeforeFirstStep ="),
        ("signalling", "SignallingHud.cs", "public static string Line("),

        ("view", "World/ChaseCameraAim.cs", "public string Reason"),

        ("emergency", "Input/EmergencyBrake.cs", "public static string Notice("),

        ("help", "FirstRun.cs", "private string HelpLine()"),
        ("help", "Input/DriverInput.cs", "public static string Help =>"),
        ("help", "Input/DriverActions.cs", "public const string HelpSeparator ="),
        ("help", "Input/DriverActions.cs", "public static readonly IReadOnlyList<DriverBinding> All ="),
        ("help", "Input/DriverActions.cs", "public static string Help { get; } ="),
        ("help", "Input/DriverActions.cs", "private static string BuildCoreDrivesHelp()"),
    };

    /// <summary>Napisy, o których 6.D175 i 6.D179 wiedzą, że widzi je gracz.</summary>
    private static readonly string[] ZnanePlayerskie =
    {
        "koniec pakietu",
        "bez sygnalizacji — przejazd bez blokad (podaj --signalling)",
        "sygnalizacja: skład jeszcze nie wjechał na plan",
        "sygnalizacja: linia bez ochrony pociągu",
        "sygnalizacja: przed pierwszym krokiem",
    };

    /// <summary>Ile literałów dociera na ekran drogą <c>Hud.Update</c> — 6.D183.</summary>
    private const int LiteralowNaEkranie = 74;

    /// <summary>Ile z nich jest KLUCZEM katalogu, a nie tekstem — 6.D183.</summary>
    private const int KluczyKatalogunaEkranie = 28;

    /// <summary>
    /// Ile literałów z tej drogi niesie SŁOWO w rozumieniu bramki — 6.D183.
    ///
    /// <para>Pytane tym samym sitem, którym pyta <see cref="SlowaWKodzie"/>:
    /// <c>BezJednostek(BezDziur(literał))</c> wobec <see cref="WzorzecSlowa"/>.
    /// Reszta z 46 napisów w kodzie to formaty liczb (<c>F1</c>, <c>F0</c>,
    /// <c>+0.00;-0.00;0.00</c>), nazwy klawiszy, rozdzielacze i szablony złożone
    /// z samych dziur.</para>
    /// </summary>
    private const int ZeSlowemNaEkranie = 22;

    /// <summary>
    /// Ile z nich ma polski znak diakrytyczny — liczba PORÓWNAWCZA do 6.D175 — 6.D183.
    /// </summary>
    private const int ZDiakrytykiemNaEkranie = 7;

    /// <summary>Polskie znaki diakrytyczne — rodzina, którą mierzyło 6.D175.</summary>
    private const string ZnakiDiakrytyczne =
        "\u0105\u0107\u0119\u0142\u0144\u00f3\u015b\u017a\u017c"
        + "\u0104\u0106\u0118\u0141\u0143\u00d3\u015a\u0179\u017b";

    /// <summary>Ile przypisań <c>.Text =</c> ma cała warstwa gry — 6.D183.</summary>
    private const int PrzypisanText = 7;

    private static string ZrodloGry(string wzgledna) =>
        Zrodlo(new[] { "src", "Game" }.Concat(wzgledna.Split('/')).ToArray());

    /// <summary>
    /// Każde przypisanie <c>.Text =</c> w warstwie gry stoi w ciele <c>Hud.Update</c>
    /// — 6.D183.
    ///
    /// <para><b>To jest przesłanka całej pozycji, wykonana, a nie założona.</b> Pole
    /// „Skąd" 6.D183 mówi, że jedynym sprawdzalnym kryterium „tekst dla gracza" jest
    /// DROGA WYWOŁANIA do <c>_hud.Update</c>. Zdanie to jest prawdziwe tylko wtedy,
    /// gdy nic innego nie pisze po ekranie — i dopiero ten test to sprawdza. Gdyby
    /// gdziekolwiek indziej stało <c>Label.Text = …</c>, cała odpowiedź pozycji
    /// opisywałaby jedną z dwóch dróg i nie mówiła o tym ani słowa.</para>
    /// </summary>
    [TestMethod]
    public void Kazde_przypisanie_Text_stoi_w_ciele_Hud_Update()
    {
        var cialo = CialoDeklaracji(HudSource(), "public void Update(");
        var wszystkie = new List<string>();
        var pozaCialem = new List<string>();
        foreach (var sciezka in ZrodlaGry())
        {
            var kod = File.ReadAllText(sciezka);
            foreach (Match trafienie in Regex.Matches(kod, @"\w+\.Text\s*="))
            {
                wszystkie.Add($"{Path.GetFileName(sciezka)}: {trafienie.Value}");
                if (!cialo.Contains(trafienie.Value, StringComparison.Ordinal))
                {
                    pozaCialem.Add($"{Path.GetFileName(sciezka)}: {trafienie.Value}");
                }
            }
        }

        // Dolne ostrze na SAM SKAN — bez niego literówka we wzorcu daje pustą listę,
        // a pusta lista przechodzi „zero poza ciałem" bez jednego sprawdzenia (6.D27).
        Assert.AreEqual(PrzypisanText, wszystkie.Count,
            $"skan widzi {wszystkie.Count} przypisań `.Text =` w `src/Game/` wobec "
            + $"zmierzonych {PrzypisanText}: " + string.Join(" | ", wszystkie));
        Assert.AreEqual(0, pozaCialem.Count,
            "po ekranie pisze coś spoza `Hud.Update`, więc kryterium „droga wywołania” "
            + "z 6.D183 opisuje JEDNĄ z dwóch dróg i nie mówi o tym: "
            + string.Join(" | ", pozaCialem));
    }

    /// <summary>
    /// Każdy argument napisowy <c>Hud.Update</c> ma w mapie źródło — 6.D183.
    ///
    /// <para>Bramka na STARZENIE SIĘ MAPY. Ósmy argument dopisany do <c>Update</c>
    /// nie wypada wtedy po cichu z pomiaru, tylko zapala ten test.</para>
    /// </summary>
    [TestMethod]
    public void Kazdy_argument_napisowy_Hud_Update_ma_zrodlo()
    {
        var naglowek = CialoDeklaracji(HudSource(), "public void Update(");
        var podpis = naglowek[..naglowek.IndexOf('{')];
        var wSygnaturze = Regex.Matches(podpis, @"\bstring\s+(\w+)")
            .Select(m => m.Groups[1].Value).ToList();

        CollectionAssert.AreEqual(ArgumentyNapisoweHud, wSygnaturze,
            "sygnatura `Hud.Update` niesie inne argumenty napisowe niż mapa 6.D183: "
            + string.Join(", ", wSygnaturze));

        var opisane = ZrodlaHud.Select(z => z.Argument).Distinct(StringComparer.Ordinal)
            .OrderBy(a => a, StringComparer.Ordinal).ToList();
        CollectionAssert.AreEqual(
            ArgumentyNapisoweHud.OrderBy(a => a, StringComparer.Ordinal).ToList(), opisane,
            "mapa `ZrodlaHud` opisuje inne argumenty niż sygnatura: "
            + string.Join(", ", opisane));
    }

    /// <summary>
    /// Ile literałów dociera na ekran drogą <c>Hud.Update</c> — 6.D183.
    ///
    /// <para><b>Podział na KLUCZ i TEKST jest tu treścią.</b> Literał stojący
    /// w <c>UiText.Get("hud.door.open")</c> też dociera drogą <c>Hud.Update</c>, ale
    /// tym, co widzi gracz, jest wtedy WPIS KATALOGU, a nie ten napis. Zlanie obu
    /// w jedną liczbę dałoby odpowiedź większą i nieprawdziwą.</para>
    /// </summary>
    [TestMethod]
    public void Literaly_docierajace_na_ekran_droga_Hud_Update()
    {
        var wszystkie = new List<string>();
        foreach (var (_, plik, czlon) in ZrodlaHud)
        {
            var kod = ZrodloGry(plik);
            wszystkie.AddRange(Literaly(CialoDeklaracji(kod, czlon)));
        }

        wszystkie.AddRange(Literaly(CialoDeklaracji(
            HudSource(), "public void Update(")));

        var klucze = wszystkie.Where(l => UiText.Keys.Contains(l)).ToList();
        var tekst = wszystkie.Where(l => !UiText.Keys.Contains(l)).ToList();

        Assert.AreEqual(LiteralowNaEkranie, wszystkie.Count,
            $"drogą `Hud.Update` dociera dziś {wszystkie.Count} literałów wobec "
            + $"zmierzonych {LiteralowNaEkranie}: " + string.Join(" | ", wszystkie));
        Assert.AreEqual(KluczyKatalogunaEkranie, klucze.Count,
            $"kluczy katalogu jest {klucze.Count} wobec zmierzonych "
            + $"{KluczyKatalogunaEkranie}: " + string.Join(" | ", klucze));

        // GŁÓWNA LICZBA POZYCJI. „Ile tekstu dla gracza" to nie „ile literałów":
        // z 46 napisów w kodzie większość to formaty liczb, nazwy klawiszy
        // i rozdzielacze. Pytam o nie tym samym sitem, co bramka.
        var zeSlowem = tekst
            .Where(l => Regex.IsMatch(BezJednostek(BezDziur(l)), WzorzecSlowa))
            .ToList();
        Assert.AreEqual(ZeSlowemNaEkranie, zeSlowem.Count,
            $"ze słowem jest {zeSlowem.Count} literałów wobec zmierzonych "
            + $"{ZeSlowemNaEkranie}: " + string.Join(" | ", zeSlowem));

        // Liczba PORÓWNAWCZA do 6.D175, które mierzyło rodzinę „polski znak
        // diakrytyczny" i odpowiedziało „trzy ze 140". Różnica między nią a liczbą
        // wyżej JEST odpowiedzią 6.D183, więc stoi w teście, a nie tylko w raporcie.
        var zDiakrytykiem = zeSlowem
            .Where(l => l.Any(z => ZnakiDiakrytyczne.Contains(z, StringComparison.Ordinal)))
            .ToList();
        Assert.AreEqual(ZDiakrytykiemNaEkranie, zDiakrytykiem.Count,
            $"z polskim znakiem jest {zDiakrytykiem.Count} wobec zmierzonych "
            + $"{ZDiakrytykiemNaEkranie}: " + string.Join(" | ", zDiakrytykiem));

        // Cztery napisy z 6.D175 i 6.D179 MUSZĄ tu być — pole „Weryfikacja" pozycji
        // mówi wprost: jeśli ich nie ma, prześledzenie pominęło argument.
        foreach (var znany in ZnanePlayerskie)
        {
            Assert.IsTrue(tekst.Contains(znany, StringComparer.Ordinal),
                $"napis „{znany}”, o którym wiadomo, że widzi go gracz, NIE wyszedł "
                + "z prześledzenia — mapa `ZrodlaHud` pominęła argument albo człon");
        }
    }

    /// <summary>Ile zgłoszeń daje <c>FirstRun.cs</c> liczony CAŁYM PLIKIEM — 6.D180.</summary>
    private const int ZgloszenFirstRunCalymPlikiem = 106;

    /// <summary>Ile daje ten sam plik liczony WIERSZ PO WIERSZU — 6.D180.</summary>
    private const int ZgloszenFirstRunWierszami = 118;

    /// <summary>Ile plików korpusu daje różne liczby obiema drogami — 6.D180.</summary>
    private const int PlikowZRoznicaDrog = 1;

    /// <summary>
    /// Zgłoszenia <see cref="SlowaWKodzie"/> liczone wiersz po wierszu.
    ///
    /// <para>Nie jest to droga używana przez żadną bramkę — stoi tu WYŁĄCZNIE jako
    /// druga strona porównania z 6.D180, tak samo jak <see cref="StaryCzytnik"/>
    /// przy 6.D182. Bez niej test porównywałby drogę samą ze sobą.</para>
    /// </summary>
    private static List<string> SlowaWierszPoWierszu(string kod) =>
        kod.Split('\n').SelectMany(w => SlowaWKodzie(w)).ToList();

    /// <summary>
    /// Różnica między liczeniem całym plikiem a wiersz po wierszu ma JEDEN powód —
    /// 6.D180.
    ///
    /// <para><b>ROZSTRZYGNIĘCIE: poprawne jest liczenie CAŁYM PLIKIEM.</b> Napisu
    /// wielowierszowego nie da się czytać wiersz po wierszu, bo rozcina go SAM podział
    /// na wiersze — niezależnie od czytnika. `FirstRun.cs:2232` niesie napis surowy
    /// <c>$$"""</c> długości czterdziestu wierszy; czytany w całości jest JEDNYM
    /// literałem, a czytany wierszami rozpada się na kawałki, w których cudzysłów
    /// zamykający nazwę pola JSON paruje się z otwierającym jego wartość. Wiersz
    /// <c>"engine": "godot",</c> daje wtedy DWA „literały" — <c>engine</c>
    /// i <c>godot</c> — choć w pliku obie te nazwy są TREŚCIĄ jednego napisu.</para>
    ///
    /// <para><b>Hipoteza z pola „Skąd" pozycji jest NIEPRAWDZIWA i tak jest tu
    /// zapisane.</b> Pozycja podejrzewała „literał sklejany przez kilka wierszy, na
    /// którym <c>BezDziur</c> rozstrzyga inaczej dla fragmentu niż dla całości".
    /// Literał sklejany <c>"a" + "b"</c> przez dwa wiersze daje obiema drogami
    /// TĘ SAMĄ liczbę — mierzy to
    /// <see cref="Rozciecie_bierze_sie_z_napisu_WIELOWIERSZOWEGO_a_nie_ze_sklejanego"/>
    /// na wejściu syntetycznym. <c>BezDziur</c> nie ma z tą różnicą nic wspólnego.</para>
    ///
    /// <para><b>Różnica wynosi dziś DWANAŚCIE, a nie trzynaście jak w pozycji.</b>
    /// Było <c>105</c> wobec <c>118</c>; jest <c>106</c> wobec <c>118</c>, bo 6.D182
    /// naprawiło czytnik i strona „całym plikiem" widzi odtąd ten napis surowy jako
    /// jeden literał zamiast kawałka. Strona „wierszami" nie drgnęła i drgnąć nie
    /// mogła — tam rozcina podział na wiersze, a nie czytnik.</para>
    /// </summary>
    [TestMethod]
    public void Roznica_miedzy_liczeniem_calym_plikiem_a_wierszami_ma_JEDEN_powod()
    {
        var rozne = new List<string>();
        var zerowe = 0;
        foreach (var sciezka in ZrodlaGry())
        {
            var kod = File.ReadAllText(sciezka);
            if (SlowaWKodzie(kod).Count == SlowaWierszPoWierszu(kod).Count)
            {
                zerowe++;
                continue;
            }

            rozne.Add(Path.GetFileName(sciezka));
        }

        // Na 20 z 21 plików obie drogi dają liczby RÓWNE CO DO ZERA, a nie „co do
        // jedynki", jak mówiła pozycja. Zapisane jako liczba, bo to zdanie o korpusie.
        Assert.AreEqual(ZrodlaGry().Count - PlikowZRoznicaDrog, zerowe,
            $"plików liczących tak samo obiema drogami jest {zerowe} — różnica "
            + "przestała być własnością JEDNEGO pliku i wyjaśnienie 6.D180 "
            + "opisuje wtedy co innego");
        CollectionAssert.AreEqual(new[] { "FirstRun.cs" }, rozne,
            "różnią się inne pliki niż w pomiarze 6.D180: " + string.Join(", ", rozne));

        var kodFirstRun = File.ReadAllText(Path.Combine(RepositoryRoot(), "src", "Game", "FirstRun.cs"));
        var caly = SlowaWKodzie(kodFirstRun);
        var wierszami = SlowaWierszPoWierszu(kodFirstRun);
        Assert.AreEqual(ZgloszenFirstRunCalymPlikiem, caly.Count,
            $"`FirstRun.cs` liczony całym plikiem daje {caly.Count} zgłoszeń wobec "
            + $"zmierzonych {ZgloszenFirstRunCalymPlikiem}");
        Assert.AreEqual(ZgloszenFirstRunWierszami, wierszami.Count,
            $"`FirstRun.cs` liczony wierszami daje {wierszami.Count} wobec "
            + $"zmierzonych {ZgloszenFirstRunWierszami}");

        // A TERAZ WYJAŚNIENIE, a nie sama liczba: KAŻDE zgłoszenie, które widzi
        // wyłącznie droga wierszowa, jest KAWAŁKIEM tego jednego napisu, który
        // wyłącznie ona gubi. To jest cała treść pozycji „co do literału,
        // a nie co do pliku".
        var pula = new List<string>(caly);
        var tylkoWierszami = new List<string>();
        foreach (var z in wierszami)
        {
            var i = pula.IndexOf(z);
            if (i >= 0)
            {
                pula.RemoveAt(i);
            }
            else
            {
                tylkoWierszami.Add(z);
            }
        }

        var najdluzszy = pula.OrderByDescending(l => l.Length).FirstOrDefault() ?? string.Empty;
        Assert.IsTrue(najdluzszy.Contains('\n'),
            "napis, który gubi droga wierszowa, przestał być WIELOWIERSZOWY — "
            + "wyjaśnienie 6.D180 stoi na tym, że rozcina go podział na wiersze: "
            + najdluzszy);
        foreach (var kawalek in tylkoWierszami)
        {
            Assert.IsTrue(najdluzszy.Contains(kawalek, StringComparison.Ordinal),
                $"zgłoszenie „{kawalek}”, które widzi TYLKO droga wierszowa, nie jest "
                + "kawałkiem gubionego napisu — różnica ma wtedy drugi powód, "
                + "którego 6.D180 nie nazwało");
        }

        Assert.AreEqual(ZgloszenFirstRunWierszami - ZgloszenFirstRunCalymPlikiem,
            tylkoWierszami.Count - pula.Count,
            "rozbicie różnicy przestało się sumować: "
            + $"tylko-wierszami {tylkoWierszami.Count}, tylko-całym {pula.Count}");
    }

    /// <summary>
    /// Rozcięcie bierze się z napisu WIELOWIERSZOWEGO, a nie ze sklejanego — 6.D180.
    ///
    /// <para>Wejście SYNTETYCZNE, bo pole „Weryfikacja" pozycji żąda pokazania
    /// MECHANIZMU, a nie liczby. Drzewo ma dziś dokładnie jeden napis wielowierszowy
    /// i ani jednego sklejanego przez wiersze w pliku, na którym różnica wychodzi —
    /// więc samo drzewo tych dwóch przypadków nie rozdziela.</para>
    /// </summary>
    [TestMethod]
    public void Rozciecie_bierze_sie_z_napisu_WIELOWIERSZOWEGO_a_nie_ze_sklejanego()
    {
        // 1. Napis WIELOWIERSZOWY — mechanizm różnicy. Całym plikiem: JEDEN literał,
        //    którego treścią są obie nazwy. Wierszami: dwa „literały", bo cudzysłów
        //    zamykający nazwę paruje się z otwierającym wartość.
        // Klamra zagnieżdżona jest tu KONIECZNA, nie ozdobna: `BezDziur` zdejmuje
        // `[{][^{}]*[}]`, więc płaski obiekt JSON zniknąłby w całości i strona
        // „całym plikiem" dałaby zero — zgodność dwóch zer, a nie mechanizm.
        var wielowierszowy =
            "var j = $$\"\"\"\n{ \"scene\": { \"peron\": 1 } }\n\"\"\";";
        var calymW = SlowaWKodzie(wielowierszowy);
        var wierszamiW = SlowaWierszPoWierszu(wielowierszowy);
        Assert.AreEqual(1, Literaly(wielowierszowy).Count,
            "czytnik przestał widzieć napis surowy jako JEDEN literał — bez tego "
            + "reszta tego testu mierzyłaby usterkę czytnika, a nie podziału na wiersze");
        CollectionAssert.AreEqual(
            new[] { "\n{ \"scene\": { \"peron\": 1 } }\n" }, calymW,
            "całym plikiem napis surowy przestał być JEDNYM zgłoszeniem: "
            + string.Join(" | ", calymW));
        CollectionAssert.AreEqual(new[] { "scene", "peron" }, wierszamiW,
            "wierszami napis surowy przestał się rozpadać na nazwę i wartość: "
            + string.Join(" | ", wierszamiW));

        // 2. Napis SKLEJANY przez dwa wiersze — HIPOTEZA POZYCJI. Obie drogi dają
        //    TO SAMO, więc hipoteza jest nieprawdziwa i to jest tu wykonane, a nie
        //    przyjęte na słowo.
        var sklejany = "var s = \"pierwszy człon \"\n    + \"drugi człon\";";
        CollectionAssert.AreEqual(SlowaWKodzie(sklejany), SlowaWierszPoWierszu(sklejany),
            "literał sklejany zaczął dawać różne liczby obiema drogami — hipoteza "
            + "z pola „Skąd" + "” 6.D180 przestałaby wtedy być nieprawdziwa");
        Assert.AreEqual(2, SlowaWKodzie(sklejany).Count,
            "wejście syntetyczne przestało nieść dwa człony, więc porównanie wyżej "
            + "mogłoby być zgodnością dwóch zer: " + string.Join(" | ", SlowaWKodzie(sklejany)));
    }

    /// <summary>
    /// Ile literałów korpusu <see cref="BezJednostek"/> w ogóle ZMIENIA — 6.D155.
    ///
    /// <para>Nie jest to liczba usterek, tylko ZASIĘG mechaniki: na tylu literałach
    /// zdejmowanie symboli cokolwiek robi z tekstem. Stoi tu, żeby dwie liczby niżej
    /// dało się z czymś porównać — 2 z 335 to inne zdanie niż 2 z 2.</para>
    /// </summary>
    private const int LiteralowDotknietychZdejmowaniem = 335;

    /// <summary>
    /// Ilu literałom zdejmowanie jednostek ZABIERA werdykt „to słowo" — 6.D155.
    /// </summary>
    private const int WerdyktowZabranychPrzezZdejmowanie = 2;

    /// <summary>
    /// Ilu literałom zdejmowanie werdykt DAJE — 6.D155. Zero, i nie jest to
    /// przypadek dzisiejszego drzewa: patrz
    /// <see cref="Zdejmowanie_jednostek_moze_werdykt_ODEBRAC_a_dac_nie_moze"/>.
    /// </summary>
    private const int WerdyktowDanychPrzezZdejmowanie = 0;

    /// <summary>Czy po zdjęciu dziur zostaje słowo — z jednostkami albo bez.</summary>
    private static bool JestSlowo(string literal, bool zdejmujJednostki)
    {
        var tekst = BezDziur(literal);
        return Regex.IsMatch(zdejmujJednostki ? BezJednostek(tekst) : tekst, WzorzecSlowa);
    }

    /// <summary>
    /// Ile kosztuje mechanika „jednostki zjadają litery ze środka" — 6.D155.
    ///
    /// <para><b>ODPOWIEDŹ: dwa werdykty na 335 dotkniętych literałów, i ani jednego
    /// w drugą stronę.</b> <see cref="BezJednostek"/> zdejmuje symbole bezwarunkowym
    /// <c>Replace</c>, więc kaleczy tekst szeroko — <c>"streaming"</c> staje się
    /// <c>" trea ing"</c>, <c>"name"</c> staje się <c>"na e"</c> — ale pytanie bramki
    /// brzmi „czy zostały dwie litery pod rząd", a na to okaleczenie prawie nigdy nie
    /// wpływa. Na dzisiejszym korpusie zmienia werdykt <b>dwóm</b> literałom.</para>
    ///
    /// <para><b>ROZSTRZYGNIĘCIE: nie warto, i to jest wynik pomiaru, a nie ostrożności.</b>
    /// Oba dotknięte werdykty są już rozstrzygnięte gdzie indziej i oba są POPRAWNE:
    /// <c>"Esc"</c> to przypadek, na którym stoi rozstrzygnięcie 6.D142 (wyjątek
    /// <see cref="NazwyKlawiszy"/> jest bezczynny dokładnie dlatego), a wiersz prędkości
    /// HUD-u milczy, bo po zdjęciu dziur i jednostek nie zostaje w nim ani jedno słowo
    /// — czyli **dokładnie z powodu, dla którego 6.D115 to zdejmowanie wprowadziło**.
    /// Zmiana na zdejmowanie warunkowe kosztowałaby przeczytanie decyzji 6.D142 od nowa
    /// i nie naprawiłaby ani jednego fałszywego werdyktu, bo fałszywych nie ma.</para>
    /// </summary>
    [TestMethod]
    public void Zdejmowanie_jednostek_kosztuje_dwa_werdykty_na_trzystu_trzydziestu_pieciu()
    {
        var dotkniete = 0;
        var zabrane = new List<string>();
        var dane = new List<string>();
        foreach (var sciezka in ZrodlaGry())
        {
            foreach (var literal in Literaly(File.ReadAllText(sciezka)))
            {
                var bezDziur = BezDziur(literal);
                if (!string.Equals(bezDziur, BezJednostek(bezDziur), StringComparison.Ordinal))
                {
                    dotkniete++;
                }

                var bez = JestSlowo(literal, zdejmujJednostki: false);
                var ze = JestSlowo(literal, zdejmujJednostki: true);
                if (bez && !ze)
                {
                    zabrane.Add(literal);
                }
                else if (!bez && ze)
                {
                    dane.Add(literal);
                }
            }
        }

        Assert.AreEqual(LiteralowDotknietychZdejmowaniem, dotkniete,
            $"zdejmowanie zmienia dziś {dotkniete} literałów wobec zmierzonych "
            + $"{LiteralowDotknietychZdejmowaniem} — zasięg mechaniki się przesunął");
        Assert.AreEqual(WerdyktowDanychPrzezZdejmowanie, dane.Count,
            "zdejmowanie DAŁO komuś werdykt „to słowo”, a dać go nie może — "
            + "podstawienie spacji rozdziela litery, więc nowej pary utworzyć nie "
            + "umie: " + string.Join(" | ", dane));
        Assert.AreEqual(WerdyktowZabranychPrzezZdejmowanie, zabrane.Count,
            $"zdejmowanie zabiera dziś werdykt {zabrane.Count} literałom wobec "
            + $"zmierzonych {WerdyktowZabranychPrzezZdejmowanie}: "
            + string.Join(" | ", zabrane));

        // I KTÓRE to są — bo pole „Skończone, gdy" pozycji pyta, czy któryś jest
        // tekstem dla gracza. Odpowiedź brzmi TAK, i jest tu wykonana, nie napisana.
        Assert.IsTrue(zabrane.Contains("Esc", StringComparer.Ordinal),
            "„Esc” przestał być jednym z dwóch — na nim stoi rozstrzygnięcie 6.D142: "
            + string.Join(" | ", zabrane));
        Assert.IsTrue(NazwyKlawiszy.Contains("Esc", StringComparer.Ordinal),
            "„Esc” wypadł z `NazwyKlawiszy`, więc zdanie o bezczynności wyjątku "
            + "z 6.D142 opisuje inny stan");

        var wHudUpdate = Literaly(CialoDeklaracji(
            HudSource(), "public void Update("));
        var drugi = zabrane.Single(l => !string.Equals(l, "Esc", StringComparison.Ordinal));
        Assert.IsTrue(wHudUpdate.Contains(drugi, StringComparer.Ordinal),
            $"drugi z dwóch literałów („{drugi}”) przestał stać w ciele `Hud.Update`, "
            + "więc odpowiedź „tak, jeden z nich to tekst dla gracza” przestała "
            + "wynikać z drogi wywołania prześledzonej w 6.D183");
        // CO w nim zostaje, a nie „czy zostaje słowo" — to drugie wynikałoby
        // z samego członkostwa w `zabrane` i byłoby zdaniem o sobie samym.
        // Zostaje JEDNA litera: `a`, symbol przyspieszenia. Reszta wiersza to dziury
        // interpolacji, jednostki, spacje i znak równości — czyli dokładnie to, co
        // pole „Skończone, gdy" 6.D83 kazało ZOSTAWIĆ w kodzie.
        var resztka = BezJednostek(BezDziur(drugi))
            .Replace(" ", string.Empty, StringComparison.Ordinal)
            .Replace("=", string.Empty, StringComparison.Ordinal);
        Assert.AreEqual("a", resztka,
            $"po zdjęciu dziur i jednostek w „{drugi}” zostaje „{resztka}” zamiast "
            + "samego symbolu przyspieszenia — wiersz prędkości niesie wtedy coś, "
            + "czego 6.D83 nie przewidziało, i milczenie bramki wymaga nowego powodu");
        Assert.AreEqual(1, resztka.Length,
            "resztka przestała być JEDNOLITEROWA, więc nie jest już oczywiste, "
            + "że wiersz nie ma słowa z własnego prawa");
    }

    /// <summary>
    /// Zdejmowanie jednostek może werdykt ODEBRAĆ, a dać nie może — 6.D155.
    ///
    /// <para>Wejście SYNTETYCZNE, bo zero z pomiaru jest zerem NA DZISIEJSZYM DRZEWIE
    /// i samo w sobie nie mówi, czy druga strona jest niemożliwa, czy tylko nie
    /// trafiła się. Mechanizm: <see cref="BezJednostek"/> podstawia SPACJĘ, a spacja
    /// rozdziela litery — więc pary, której nie było, utworzyć nie umie. Poniżej
    /// wykonane na obu kierunkach.</para>
    /// </summary>
    [TestMethod]
    public void Zdejmowanie_jednostek_moze_werdykt_ODEBRAC_a_dac_nie_moze()
    {
        // ODBIERA: trzy litery, z których środkowa jest jednostką.
        Assert.IsTrue(JestSlowo("Esc", zdejmujJednostki: false),
            "„Esc” przestał być słowem PRZED zdejmowaniem — kontrola mierzyłaby nic");
        Assert.IsFalse(JestSlowo("Esc", zdejmujJednostki: true),
            "„Esc” przestał tracić werdykt po zdejmowaniu — mechanika z 6.D142 znikła");

        // NIE DAJE: jednostka między literami zostaje zastąpiona SPACJĄ, więc
        // sąsiadami nie stają się one, tylko rozchodzą się jeszcze dalej.
        Assert.AreEqual("a b", BezJednostek("akmb"),
            "zdejmowanie przestało podstawiać spację — gdyby podstawiało pusty napis, "
            + "„akmb” dałoby „ab”, czyli parę liter STWORZONĄ przez sito");
        Assert.IsFalse(JestSlowo("akmb", zdejmujJednostki: true),
            "zdejmowanie utworzyło parę liter z dwóch rozdzielonych — kierunek, "
            + "który pomiar 6.D155 podaje jako niemożliwy, właśnie stał się możliwy");

        // I kontrola w drugą stronę na tym samym wejściu: BEZ zdejmowania „akmb”
        // słowem JEST, więc powyższy `IsFalse` nie jest zgodnością dwóch zer.
        Assert.IsTrue(JestSlowo("akmb", zdejmujJednostki: false),
            "„akmb” przestało być słowem bez zdejmowania, więc kontrola wyżej "
            + "przechodziłaby z niewłaściwego powodu");
    }
    /// <summary>Obcinacz wierszowy TNIE literał wielowierszowy, a czytnik go nie tnie —
    /// 6.D184.</summary>
    /// <remarks>
    /// <b>Wejście SYNTETYCZNE, bo drzewo takiego napisu dziś nie ma — i o to chodzi.</b>
    /// Gdyby ten test stał na korpusie, byłby zielony niezależnie od tego, czy obcinacz
    /// gdzieś wrócił: zmierzone 13.09.2026, obie drogi dają na dwudziestu jeden plikach
    /// <b>identyczny</b> wynik (480 literałów i 347 zgłoszeń, różnica w zero plikach).
    /// Różnicę widać dopiero na napisie, którego wiersz zaczyna się od <c>//</c>.
    /// </remarks>
    [TestMethod]
    public void Obcinacz_wierszowy_TNIE_literal_wielowierszowy_a_czytnik_nie()
    {
        var kod = "class X {\n"
                + "    const string J = @\"{\n"
                + "//host/sciezka\n"
                + "koniec pakietu\n"
                + "}\";\n"
                + "}\n";

        var czytnik = Literaly(kod);
        Assert.AreEqual(1, czytnik.Count, "czytnik ma znaleźć dokładnie jeden literał");
        Assert.AreEqual(33, czytnik[0].Length,
            $"czytnik zwrócił literał długości {czytnik[0].Length} zamiast 33 — "
            + "napis wielowierszowy stracił kawałek, choć nikt go nie obcinał");
        StringAssert.Contains(czytnik[0], "//host/sciezka",
            "czytnik zgubił wiersz zaczynający się od // ze środka napisu",
            StringComparison.Ordinal);

        var poObcinaczu = Literaly(KodBezKomentarzyDlaStaregoCzytnika(kod));
        Assert.AreEqual(1, poObcinaczu.Count,
            "obcinacz zgubił literał w całości zamiast go skrócić");
        Assert.AreEqual(18, poObcinaczu[0].Length,
            $"obcinacz wierszowy zostawił literał długości {poObcinaczu[0].Length} "
            + "zamiast 18 — jeśli przestał ciąć, ta pozycja straciła powód");
        Assert.AreNotEqual(czytnik[0], poObcinaczu[0],
            "obcinacz i czytnik dają ten sam wynik na napisie z wierszem `//` — "
            + "wtedy zdjęcie obcinacza z szesnastu miejsc było bez znaczenia");
    }

    /// <summary>Obcinacz wierszowy karmi WYŁĄCZNIE stary czytnik — 6.D184.</summary>
    /// <remarks>
    /// Bez tej bramki obcinacz mógłby wrócić na drogę żywego czytnika bez ani jednego
    /// czerwonego testu: na dzisiejszym korpusie obie drogi dają to samo, więc żadna
    /// liczba by się nie ruszyła. Zapadka jest RÓWNOŚCIOWA — drugie wywołanie ma
    /// zmusić do rozstrzygnięcia, a nie przejść samo.
    /// </remarks>
    [TestMethod]
    public void Obcinacz_wierszowy_stoi_w_DOKLADNIE_jednym_miejscu()
    {
        var cale = Zrodlo("tests", "Game.Tests", "UiTextTests.cs");

        // WŁASNA METODA WYCIĘTA ZE SKANU, i to nie jest wyjątek dla wygody: niżej stoją
        // wzorce, które tę nazwę WYMIENIAJĄ, więc bramka skanująca samą siebie liczyłaby
        // własne wzorce jako wywołania. Zmierzone: bez wycięcia wychodzą 4 zamiast 3.
        // Ta sama konstrukcja, co wycięcie własnej sekcji w `test_assertion_gate.py`.
        var znacznik = "public void " + nameof(Obcinacz_wierszowy_stoi_w_DOKLADNIE_jednym_miejscu);
        var granica = cale.IndexOf(znacznik, StringComparison.Ordinal);
        Assert.IsTrue(granica > 0, "nie znalazłem własnej metody w źródle");
        var zrodlo = cale.Substring(0, granica);

        var wystapien = Regex.Matches(zrodlo,
            @"KodBezKomentarzyDlaStaregoCzytnika\(").Count;
        var definicji = Regex.Matches(zrodlo,
            @"private static string KodBezKomentarzyDlaStaregoCzytnika\(").Count;
        Assert.AreEqual(1, definicji, "definicji obcinacza ma być jedna");
        Assert.AreEqual(3, wystapien,
            $"nazwa obcinacza pada {wystapien} razy poza tą metodą, a ma paść trzy: "
            + "definicja, wejście `StaryCzytnik` i wejście syntetyczne kontroli. "
            + "Każde kolejne wywołanie tnie literały wielowierszowe po cichu — 6.D184");
        StringAssert.Contains(zrodlo,
            "StaryCzytnik(KodBezKomentarzyDlaStaregoCzytnika(kod))",
            StringComparison.Ordinal);
        Assert.IsFalse(Regex.IsMatch(zrodlo, @"\bKodBezKomentarzy\("),
            "wrócił obcinacz pod dawną nazwą — zdjęty z szesnastu miejsc przy 6.D184");
    }

}
