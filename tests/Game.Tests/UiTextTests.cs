using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
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
    /// przepuszczone przez <see cref="KodBezKomentarzy"/> — <b>21</b> plików, bez
    /// <c>.godot</c> i bez <c>UiText.cs</c>, bez wierszy komentarza. Stoi w nim
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
    private const int LiteralowWZasieguBramki = 521;

    /// <summary>Ile różnych — dolne ostrze, zmierzone 12.09.2026.</summary>
    private const int RoznychLiteralowWZasieguBramki = 395;

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
    /// <b>348</b> literałów w <b>21</b> plikach, z czego <b>22</b> stoją w <c>throw</c>,
    /// a reszta to wypisy diagnostyczne, prozą opisane założenia projektowe i nazwy
    /// pól JSON. `KeyNames.cs` ma z tych 348 dokładnie <b>jeden</b>.</para>
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

    /// <summary>Kod pliku bez komentarzy — komentarze WOLNO pisać po polsku.</summary>
    private static string KodBezKomentarzy(string source) =>
        string.Join("\n", source.Split('\n')
            .Where(l => !l.TrimStart().StartsWith("//", StringComparison.Ordinal)));

    private static List<string> Literaly(string kod) =>
        Regex.Matches(kod, "\"((?:[^\"\\\\]|\\\\.)*)\"")
             .Select(m => m.Groups[1].Value).ToList();

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
        var zle = SlowaWKodzie(KodBezKomentarzy(HudSource()));

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
            var zle = SlowaWKodzie(KodBezKomentarzy(CialoMetody(source, naglowek)));
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
            .SelectMany(sciezka => Literaly(KodBezKomentarzy(File.ReadAllText(sciezka))))
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
            var cialo = KodBezKomentarzy(CialoMetody(source, czlon));

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
        var wPliku = Literaly(KodBezKomentarzy(source));
        var wZakresie = CzlonyKeyNames
            .SelectMany(c => Literaly(KodBezKomentarzy(CialoMetody(source, c))))
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
            SlowaWKodzie(KodBezKomentarzy(source)),
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
                KodBezKomentarzy(Zrodlo("src", "Game", "Input", plik)));
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
        var kod = KodBezKomentarzy(HudSource());
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
}
