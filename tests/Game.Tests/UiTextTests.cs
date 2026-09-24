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
    // MB-07 dokłada do korpusu bramki `N`, `O` i `T` — nazwy trzech klawiszy obsługi
    // linii. Zbiór, nie liczba, więc wpisane są nazwy, a nie licznik.
    // MB-08 dokłada `D` i `F` — drzwi na postoju ręcznym. Wniosek akapitu o ryzyku
    // przy `NazwyKlawiszySilnika` zostaje w mocy i to jest sprawdzone, a nie założone:
    // obie są JEDNOLITEROWE, więc `WzorzecSlowa` (dwie litery pod rząd) ich nie zgłasza
    // i kolizja pozostaje nieosiągalna ze względu strukturalnego. Druga połowa tego
    // testu nadal mierzy, że różnicę robi mechanizm, a nie zanik pilnowania.
    private static readonly string[] NazwyKlawiszyWZasieguBramki =
        { "C", "D", "F", "F1", "F2", "N", "O", "R", "S", "T", "W", "X" };

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

    /// <summary>
    /// Ile literałów — dolne ostrze, zmierzone 12.09.2026; 480 → 496 przy MB-02
    /// (`RunSummary.cs` i wpisy `summary.*` w katalogu).
    /// </summary>
    // 509 -> 521 (14.09.2026, MB-04): `FirstRun.AssetsRoot`, `DomyslnyZapisWejsc`
    // i wiersz `[ZAPISY]`. Liczba ZMIERZONA przyrzadem tego testu, a nie
    // przepisana z jego komunikatu o bledzie.
    // 521 -> 529 (14.09.2026, MB-05): `CabView.cs`, wiersz `[KABINA]`, stała
    // `ExitCabMissing` i wpięcie kabiny w `FirstRun`. Liczba ZMIERZONA
    // przyrzadem tego testu.
    // 529 -> 530 (14.09.2026, MB-05, poprawka `--cab` w KnownArguments).
    // 530 -> 543 (14.09.2026, MB-07): literały dołożone przez drugi skład —
    // nazwy argumentów `trains`/`headway-steps` w `RunPlan`, komunikaty odmowy
    // zakresu i nazwy węzłów widoków w `FirstRun`. Liczba jest PRZELICZONA
    // przebiegiem, a nie wyprowadzona z liczby dopisanych wierszy.
    // 543 -> 557 (14.09.2026, MB-07): trzy klawisze obsługi linii (N/T/O), wiersz
    // `[TUNEL koniec]` i komunikaty zakresu `--trains`. Liczba PRZELICZONA przebiegiem.
    // 557 -> 573 (14.09.2026, MB-08): dwa klawisze drzwi (D/F) z ich kluczami,
    // trzeci wariant wiersza stacji, podpowiedź drzwi i pięć powodów odmowy.
    // Liczba PRZELICZONA przebiegiem, a nie wyprowadzona z liczby dopisanych wierszy.
    // 573 -> 574 (17.09.2026, 6.D229): JEDEN literał — argument `what` przekazany
    // do `JsonText.Parse` w `src/Game/Assets/ChunkManifest.cs` ("manifest chunków").
    // Jest to napis, który trafia do WIERSZA ODMOWY widzianego przez gracza, więc
    // wchodzi do korpusu z tego samego powodu, co komunikaty `Abort` w `FirstRun`.
    // 574 -> 579 (22.09.2026, 6.D235): PIĘĆ literałów — komunikaty `Abort` dla pliku ZŁEGO
    // w `FirstRun`: po dwa przy osi i przy manifeście chunków, jeden przy planie
    // sygnalizacji. Liczba PRZELICZONA przebiegiem.
    // 579 -> 578 (23.09.2026, 6.M1): odtworzenie linii — zdarzenia w zapisie wejść, `ExecuteLineEvent` w `FirstRun` i nowa odmowa `--replay --line` bez `--signalling` w `RunPlan`. PRZELICZONE.
    // 578 -> 582 (23.09.2026, tory i światła): cztery ścieżki zasobów i lamp w scenie pierwszego przejazdu. PRZELICZONE.
    // Track-detail asset path and practical-light setup in FirstRun.cs add four
    // source literals; recounted against the current playable scene.
    // 582 -> 584 (24.09.2026, braking cue): klucz `hud.station.brake-now` w obu gałęziach dojazdu.
    // 584 -> 586 (24.09.2026, preparing to brake): second cue key in both approaches.
    // 586 -> 588 (24.09.2026, oznaczenia stacji): nazwa zasobu i odmowa jego braku.
    // 588 -> 589 (24.09.2026, HUD 800x600): klucz krótszego kilometrażu.
    // 589 -> 590 (24.09.2026, interaktywne R): komunikat odmowy przeładowania sceny.
    // 590 -> 592 (24.09.2026, krótki HUD chase): dystans i próg.
    // 592 -> 595 (24.09.2026, integracja pomocy linii): trzy literały testów pomocy.
    private const int LiteralowWZasieguBramki = 596;

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
        File.ReadAllText(Path.Combine(MetroBxl.Tests.Shared.KorzenRepozytorium.Sciezka, Path.Combine(czesci)));

    private static string HudSource() => Zrodlo("src", "Game", "UI", "Hud.cs");

    /// <summary>
    /// Wszystkie pliki <c>src/Game/</c> poza wygenerowanymi przez Godota i poza samym
    /// katalogiem. <c>UiText.cs</c> jest wyłączony, bo klucz stoi w nim jako WPIS,
    /// a nie jako wywołanie — liczenie go za wołającego uczyniłoby każdy wpis żywym
    /// z samego faktu istnienia.
    /// </summary>
    private static List<string> ZrodlaGry()
    {
        var korzen = Path.Combine(MetroBxl.Tests.Shared.KorzenRepozytorium.Sciezka, "src", "Game");
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
    /// <summary>
    /// Cztery postacie literału, na których rozstrzyga się „surowy czy werbatim" — 6.D215.
    ///
    /// <para>Kolumny: zapis, treść, którą ma zwrócić <see cref="Literaly"/>, i kod po
    /// <see cref="KodLeksykalnie"/>. Zbiór jest POŻYCZONY z `POSTACIE_LITERALU`
    /// w `tools/tests/test_csharp_test_methods.py` (6.D200) — te same cztery zapisy,
    /// bo pytanie jest to samo; oczekiwania są własne, bo czytniki są inne.</para>
    ///
    /// <para><b>Drzewo tych czytników na tej gałęzi NIE ĆWICZY</b> — zapis werbatim
    /// z potrójnym cudzysłowem stoi w `tests/` i `src/` raz i to w komentarzu. Dowodem
    /// może być więc wyłącznie wejście syntetyczne, tak jak przy 6.D200.</para>
    /// </summary>
    private static readonly (string Zapis, string Tresc, string PoMasce)[] PostacieLiteralu =
    {
        ("var x = @\"\"\"a\"; var y = 1;", "\"\"a", "var x =       ; var y = 1;"),
        ("var x = @\"a\"\"\"; var y = 1;", "a\"\"", "var x =       ; var y = 1;"),
        ("var x = \"\"\"a\"\"\"; var y = 1;", "a", "var x =        ; var y = 1;"),
        ("var x = $@\"\"\"a\"; var y = 1;", "\"\"a", "var x =        ; var y = 1;"),
    };

    [TestMethod]
    public void Czytnik_literalow_ROZROZNIA_werbatim_od_surowego_na_obu_galeziach()
    {
        var sprawdzonych = 0;
        foreach (var (zapis, tresc, poMasce) in PostacieLiteralu)
        {
            CollectionAssert.AreEqual(new[] { tresc }, Literaly(zapis),
                $"`Literaly` czyta `{zapis}` jako [{string.Join(" | ", Literaly(zapis))}] "
                + $"zamiast [{tresc}] — trzy cudzysłowy PO `@` to werbatim, nie literał "
                + "surowy, a pomylenie tego wciąga do literału resztę wiersza (6.D215)");
            Assert.AreEqual(poMasce, KodLeksykalnie(zapis),
                $"`KodLeksykalnie` maskuje `{zapis}` jako `{KodLeksykalnie(zapis)}` "
                + $"zamiast `{poMasce}`");
            sprawdzonych++;
        }

        Assert.AreEqual(PostacieLiteralu.Length, sprawdzonych,
            $"pętla po postaciach wykonała {sprawdzonych} obrotów przy "
            + $"{PostacieLiteralu.Length} postaciach — pusta pętla przechodzi każdą "
            + "asercję w środku");

        // ZBIÓR PRZEDROSTKÓW, nie ich liczba (6.D131). Kontrola negatywna pokazała, że
        // sama pętla nie broni tabeli: skreślenie jednej z czterech postaci przechodziło
        // na zielono, bo pętla po trzech wykonuje się poprawnie. Pytanie brzmi więc
        // wprost o to, KTÓRE cztery — bo każda odpowiada innej gałęzi czytnika.
        var przedrostki = PostacieLiteralu
            .Select(w => w.Zapis[(w.Zapis.IndexOf('=') + 2)..].Split('a')[0])
            .OrderBy(x => x, StringComparer.Ordinal)
            .ToList();
        CollectionAssert.AreEqual(
            new List<string> { "\"\"\"", "$@\"\"\"", "@\"", "@\"\"\"" }, przedrostki,
            "tabela postaci literału opisuje dziś przedrostki ["
            + string.Join(", ", przedrostki) + "] — cztery gałęzie czytnika to: werbatim "
            + "z potrójnym cudzysłowem NA POCZĄTKU, werbatim z potrójnym na KOŃCU, "
            + "literał SUROWY i werbatim INTERPOLOWANY; skreślenie którejkolwiek zdejmuje "
            + "jedną gałąź spod pomiaru (6.D215)");
    }

    [TestMethod]
    public void Obaj_wolajacy_biora_te_galaz_z_JEDNEGO_miejsca()
    {
        // Kontrola przyrządu i zarazem odpowiedź pozycji: czytników z tą gałęzią jest
        // JEDEN (`CzytajLiteral`), a `Literaly` i `KodLeksykalnie` są jego WOŁAJĄCYMI.
        // Gdyby któryś dorobił sobie własną kopię warunku, ta próbka nadal by przeszła,
        // ale źródło przestałoby mieć jedno miejsce — więc pytamy o nie wprost.
        var zrodlo = File.ReadAllText(Path.Combine(
            MetroBxl.Tests.Shared.KorzenRepozytorium.Sciezka, "tests", "Game.Tests", "UiTextTests.cs"));
        // Liczone po kodzie ZAMASKOWANYM, i to jest poprawka z pomiaru: pierwsza wersja
        // czytała plik surowo i dostała CZTERY zamiast jednego, bo łapała własne
        // komunikaty tej bramki. Czytnik, o który ta pozycja pyta, służy tu do zadania
        // pytania o samego siebie.
        var wystapien = Regex.Matches(KodLeksykalnie(zrodlo), @"cudzyslowow >= 3").Count;
        Assert.AreEqual(1, wystapien,
            $"warunek `cudzyslowow >= 3` stoi w {wystapien} miejscach — 6.D215 zmierzyło, "
            + "że jest JEDNO (`CzytajLiteral`), a `Literaly` i `KodLeksykalnie` tylko je "
            + "wołają; druga kopia rozjedzie się przy pierwszej poprawce");
        Assert.IsTrue(Regex.IsMatch(KodLeksykalnie(zrodlo), @"cudzyslowow >= 3 && !doslowny"),
            "warunek stracił człon `&& !doslowny` — wraca gałąź, na której `Literaly` "
            + "wciąga resztę wiersza, a `KodLeksykalnie` rzuca `IndexOutOfRangeException`");
    }

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

        // 6.D215: po `@` napisu SUROWEGO w C# nie ma — trzy cudzysłowy po `@` otwierają
        // werbatim o treści `"…`, a nie literał surowy. Do 15.09.2026 ten wiersz brał
        // każde trzy cudzysłowy za surowy, nie patrząc na przedrostek, i to jest ta sama
        // gałąź, którą 6.D200 naprawiło po stronie Pythona (`maska`). Zmierzone przed
        // poprawką na wejściu syntetycznym: `Literaly` wciągało do literału RESZTĘ
        // WIERSZA (`a"; var y = 1;`), a `KodLeksykalnie` rzucało
        // `IndexOutOfRangeException` — czyli awaria jest GŁOŚNA, nie cicha, i to jest
        // poprawka do przypuszczenia z pola pozycji, które bało się ciszy.
        var surowy = cudzyslowow >= 3 && !doslowny;
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

        // MB-07: pod autopilotem doszły trzy klawisze, które DZIAŁAJĄ — wybór składu
        // i przejęcie. Stoją przed zdaniem o klawiszach przejętych przez rdzeń, bo
        // zdanie „prowadzi rdzeń: … nie działają" ma kończyć wiersz.
        // MB-08: doszły `D` i `F`. Stoją po stronie DZIAŁAJĄCEJ, bo działają — `LineCore`
        // odpowiada na nie ODMOWĄ z powodem, a nie milczeniem, więc wiersz pomocy nie
        // obiecuje tu niczego, czego nie ma. Kolejność ta sama: zdanie o klawiszach
        // przejętych przez rdzeń kończy wiersz.
        Assert.AreEqual(
            "C widok  ·  R od nowa  ·  Esc wyjście  ·  N następny skład  ·  T przejmij  ·  O oddaj"
            + "  ·  D otwórz drzwi  ·  F zamknij drzwi"
            + "  ·  prowadzi rdzeń: W, S, X, Spacja nie działają",
            DriverActions.HelpWhenTheCoreDrives,
            "wiersz pomocy pod autopilotem rozjechał się z katalogiem");

        // Wiersz dla składu PRZEJĘTEGO: prowadzenie znów działa, R restartuje scenę,
        // a oddanie sterowania musi być widoczne — inaczej gracz nie ma
        // jak wrócić pod autopilota.
        Assert.AreEqual(
            "W ciąg  ·  S hamulec  ·  X wybieg  ·  "
            + "Spacja hamulec awaryjny (= pełny służbowy)  ·  C widok  ·  R od nowa  ·  Esc wyjście"
            + "  ·  N następny skład  ·  T przejmij  ·  O oddaj"
            + "  ·  D otwórz drzwi  ·  F zamknij drzwi",
            DriverActions.HelpWhenTheDriverHasTaken,
            "wiersz pomocy dla składu przejętego rozjechał się z katalogiem");

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
    // 521 -> 537 (13.09.2026, MB-02). Różnica między czytnikami zostaje ta sama co
    // do sztuki — rośnie tylko korpus.
    // 550 -> 562 (14.09.2026, MB-04): `FirstRun.AssetsRoot`, `DomyslnyZapisWejsc`
    // i wiersz `[ZAPISY]`. Liczba ZMIERZONA przyrzadem tego testu, a nie
    // przepisana z jego komunikatu o bledzie.
    // 562 -> 570 (14.09.2026, MB-05): `CabView.cs`, wiersz `[KABINA]`, stała
    // `ExitCabMissing` i wpięcie kabiny w `FirstRun`. Liczba ZMIERZONA
    // przyrzadem tego testu.
    // 570 -> 571 (14.09.2026, MB-05, poprawka `--cab` w KnownArguments).
    // 571 -> 584 (14.09.2026, MB-07): literały dołożone przez drugi skład —
    // nazwy argumentów `trains`/`headway-steps` w `RunPlan`, komunikaty odmowy
    // zakresu i nazwy węzłów widoków w `FirstRun`. Liczba jest PRZELICZONA
    // przebiegiem, a nie wyprowadzona z liczby dopisanych wierszy.
    // 584 -> 598 (14.09.2026, MB-07): trzy klawisze obsługi linii (N/T/O), wiersz
    // `[TUNEL koniec]` i komunikaty zakresu `--trains`. Liczba PRZELICZONA przebiegiem.
    // 598 -> 614 (14.09.2026, MB-08): ten sam korpus co wyżej, drugą drogą.
    // Liczba PRZELICZONA przebiegiem.
    // 614 -> 615 (17.09.2026, 6.D229): JEDEN literał — argument `what` przekazany
    // do `JsonText.Parse` w `src/Game/Assets/ChunkManifest.cs` ("manifest chunków").
    // Jest to napis, który trafia do WIERSZA ODMOWY widzianego przez gracza, więc
    // wchodzi do korpusu z tego samego powodu, co komunikaty `Abort` w `FirstRun`.
    // 615 -> 620 (22.09.2026, 6.D235): PIĘĆ literałów — komunikaty `Abort` dla pliku ZŁEGO
    // w `FirstRun`: po dwa przy osi i przy manifeście chunków, jeden przy planie
    // sygnalizacji. Liczba PRZELICZONA przebiegiem.
    // 620 -> 619 (23.09.2026, 6.M1): odtworzenie linii — zdarzenia w zapisie wejść, `ExecuteLineEvent` w `FirstRun` i nowa odmowa `--replay --line` bez `--signalling` w `RunPlan`. PRZELICZONE.
    // 619 -> 623 (23.09.2026, tory i światła): cztery pozycje źródłowe dodane do sceny. PRZELICZONE.
    // 623 -> 625 (24.09.2026, braking cue): klucz w obu gałęziach `FirstRun.StationLine`.
    // 625 -> 627 (24.09.2026, preparing to brake): second cue key in both approaches.
    // 627 -> 629 (24.09.2026, oznaczenia stacji): dwa nowe literały FirstRun.
    // 629 -> 630 (24.09.2026, HUD 800x600): nowy klucz krótkiej pozycji.
    // 630 -> 631 (24.09.2026, interaktywne R): ten sam nowy komunikat.
    // 631 -> 633 (24.09.2026, krótki HUD chase): te same dwa napisy.
    // 633 -> 636 (24.09.2026, integracja pomocy linii): trzy pozycje źródłowe testów.
    private const int PozycjiStaregoCzytnika = 637;

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

        // ÓSMY ARGUMENT — MB-02. Akapit wyżej zapowiadał go dosłownie („ósmy argument
        // dopisany do `Update` zapala drugą z nich, zamiast po cichu wypaść z pomiaru")
        // i dokładnie tak się stało: ta bramka zapaliła się pierwsza, zanim panel wyniku
        // pojawił się na ekranie.
        "summary",

        // DZIEWIĄTY — MB-03, wiersz blokady trakcji. KOLEJNOŚĆ jest tu treścią:
        // porównanie idzie `CollectionAssert.AreEqual`, czyli po kolejności sygnatury,
        // a nie po zbiorze. Wpisanie go obok `help` wywraca test, i słusznie —
        // argumenty `Hud.Update` mają jedną kolejność, nie dwie.
        "traction",
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
    /// Osobna pozycja, nie cichy brak — 6.D185, sekcja niżej: nazw dociera na ekran
    /// SZEŚĆ i DWIEMA drogami, a mapa zostaje mapą LITERAŁÓW.</para>
    /// </summary>
    private static readonly (string Argument, string Plik, string Naglowek)[] ZrodlaHud =
    {
        ("nextStation", "FirstRun.cs", "private void UpdateHud()"),

        ("mode", "FirstRun.cs", "private string _mode ="),
        ("mode", "RunPlan.cs", "public string Mode =>"),

        ("station", "FirstRun.cs", "private string StationLine()"),
        ("station", "FirstRun.cs", "private static string Faza(DoorPhase phase)"),
        ("station", "FirstRun.cs", "private const string BladZatrzymaniaFormat ="),

        // MB-08: podpowiedź drzwi ręcznych i nazwy powodów odmowy. Stoją w osobnym pliku
        // BEZ GODOTA (powód w opisie `DoorPrompt`), więc skan musi wskazać je z nazwy —
        // inaczej klucze `hud.doors.*` byłyby dla niego martwe, choć docierają na ekran
        // tą samą drogą, co reszta wiersza stacji.
        ("station", "UI/DoorPrompt.cs", "public static string For("),
        ("station", "UI/DoorPrompt.cs", "public static string Reason("),

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

        // MB-02: panel wyniku sesji treningowej. Droga jest krótka i to jest wybór —
        // `FirstRun.SummaryLine` zadaje JEDNO pytanie („czy wynik już jest"), a cały
        // tekst składa `RunSummary` z katalogu `UiText`, poza Godotem.
        ("summary", "FirstRun.cs", "private string SummaryLine()"),
        ("summary", "UI/RunSummary.cs", "public static string Compose("),
        ("summary", "UI/RunSummary.cs", "private static string Naglowek(TrainingEnding ending)"),

        // MB-03: wiersz blokady trakcji. Droga jest krótka i to jest wybór —
        // `FirstRun.TractionLine` podaje stan DWÓCH właścicieli blokady, a wybór
        // brzmienia robi `TractionBlock.Line` z katalogu `UiText`.
        ("traction", "FirstRun.cs", "private string TractionLine()"),
        ("traction", "UI/TractionBlock.cs", "public static string Line("),
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
    // 74 -> 87 (13.09.2026, MB-02): osiem kluczy `summary.*`, trzy formaty liczb
    // i dwa człony komunikatu wyjątku z ramienia domyślnego `RunSummary.Naglowek`.
    // 94 -> 101 (14.09.2026, MB-07): trzy klawisze obsługi linii (N/T/O), wiersz
    // `[TUNEL koniec]` i komunikaty zakresu `--trains`. Liczba PRZELICZONA przebiegiem.
    // 101 -> 106 (14.09.2026, MB-08): klucz `hud.station.doors-manual` oraz dwa
    // klawisze drzwi z katalogu (`D`, `input.door-open`, `F`, `input.door-close`).
    // Klucze podpowiedzi i odmów NIE wchodzą: `PodpowiedzDrzwi` i `PowodOdmowy`
    // nie stoją na mapie `ZrodlaHud`, a skan czyta ciała członów z tej mapy.
    // Liczba PRZELICZONA przebiegiem.
    // 106 -> 115 (14.09.2026, MB-08): dziewięć kluczy `DoorPrompt` — cztery
    // podpowiedzi i pięć powodów odmowy. Weszły do skanu razem z dopisaniem
    // tego pliku do mapy `ZrodlaHud`; bez tego dopisania byłyby dla bramki
    // MARTWE, choć docierają na ekran. Liczba PRZELICZONA przebiegiem.
    // 115 -> 117 (24.09.2026, braking cue): klucz dociera do `Hud.Update` z obu gałęzi.
    // 117 -> 119 (24.09.2026, preparing to brake): visible in both station approaches.
    // 119 -> 115 (24.09.2026, HUD 800x600): format pozycji przeniesiony do PositionLine.
    private const int LiteralowNaEkranie = 115;

    /// <summary>Ile z nich jest KLUCZEM katalogu, a nie tekstem — 6.D183.</summary>
    // 28 -> 36 (13.09.2026, MB-02): osiem kluczy `summary.*` panelu wyniku.
    // 36 -> 41 (14.09.2026, MB-03): `hud.speed`, `hud.speed.no-limit` i trzy klucze
    // `hud.traction.*`. Drugi wariant wiersza prędkości doszedł po regresji znalezionej
    // przebiegiem CI — patrz `Tryb_BEZ_SUFITU_nie_pyta_o_sufit…`.
    // 41 -> 44 (14.09.2026, MB-07): przeliczone przebiegiem.
    // 44 -> 47 (14.09.2026, MB-08): `hud.station.doors-manual`, `input.door-open`,
    // `input.door-close`. Przeliczone przebiegiem.
    // 47 -> 58 (24.09.2026, integracja): podpowiedź hamowania w obu gałęziach dojazdu.
    // 58 -> 60 (24.09.2026, preparing to brake): key in both approaches.
    // 60 -> 59 (24.09.2026, HUD 800x600): klucz pozycji jest wołany w PositionLine.
    private const int KluczyKatalogunaEkranie = 59;

    /// <summary>
    /// Ile literałów z tej drogi niesie SŁOWO w rozumieniu bramki — 6.D183.
    ///
    /// <para>Pytane tym samym sitem, którym pyta <see cref="SlowaWKodzie"/>:
    /// <c>BezJednostek(BezDziur(literał))</c> wobec <see cref="WzorzecSlowa"/>.
    /// Reszta z 46 napisów w kodzie to formaty liczb (<c>F1</c>, <c>F0</c>,
    /// <c>+0.00;-0.00;0.00</c>), nazwy klawiszy, rozdzielacze i szablony złożone
    /// z samych dziur.</para>
    /// </summary>
    // 22 -> 24 (13.09.2026, MB-02) — ale **liczba napisów DLA GRACZA zostaje 22**,
    // i ta różnica jest tu treścią, a nie zaokrągleniem. Dwa nowe literały to dwa
    // człony komunikatu WYJĄTKU z ramienia domyślnego `RunSummary.Naglowek`: ten tekst
    // nie dociera na ekran, tylko przerywa klatkę. Skan liczy je, bo `Naglowek` stoi
    // na mapie `ZrodlaHud` — czyli jest to trafienie FAŁSZYWE tego sita, dokładnie tej
    // samej rodziny co `FalszyweTrafieniaSkanu` przy 6.D185. Lista niżej je odejmuje,
    // żeby główna liczba pozycji 6.D183 dalej odpowiadała na swoje pytanie.
    private const int ZeSlowemNaEkranie = 24;

    /// <summary>
    /// Literały, które sito liczy jako „tekst ze słowem", a na ekran NIE DOCIERAJĄ —
    /// komunikaty wyjątków z metod stojących na mapie <see cref="ZrodlaHud"/>.
    ///
    /// <para>Lista, a nie liczba, bo to treść rozstrzyga, czy napis jest dla gracza,
    /// czy dla czytającego wyjątek. Gdyby kiedyś któryś z nich zaczął być WYŚWIETLANY,
    /// zdjęcie go stąd jest jawną zmianą, a nie przeliczeniem stałej.</para>
    /// </summary>
    private static readonly string[] NieDocierajaceNaEkran =
    {
        "panel wyniku nie ma nagłówka dla tego zakończenia — nowy człon ",
        "`TrainingEnding` ma dostać wpis w katalogu tekstów w tym samym commicie",
    };

    /// <summary>Ile napisów DLA GRACZA — 6.D183, po odjęciu listy wyżej.</summary>
    private const int DlaGraczaNaEkranie = 22;

    /// <summary>
    /// Ile z nich ma polski znak diakrytyczny — liczba PORÓWNAWCZA do 6.D175 — 6.D183.
    /// </summary>
    // 7 -> 9 (13.09.2026, MB-02) — te same dwa komunikaty wyjątku, co przy
    // `ZeSlowemNaEkranie`. Liczba porównawcza do 6.D175 liczona DLA GRACZA stoi niżej
    // i zostaje na siedmiu.
    private const int ZDiakrytykiemNaEkranie = 9;

    /// <summary>Ile z nich widzi gracz — po odjęciu <see cref="NieDocierajaceNaEkran"/>.</summary>
    private const int ZDiakrytykiemDlaGracza = 7;

    /// <summary>Polskie znaki diakrytyczne — rodzina, którą mierzyło 6.D175.</summary>
    private const string ZnakiDiakrytyczne =
        "\u0105\u0107\u0119\u0142\u0144\u00f3\u015b\u017a\u017c"
        + "\u0104\u0106\u0118\u0141\u0143\u00d3\u015a\u0179\u017b";

    /// <summary>
    /// Ile przypisań <c>.Text =</c> ma cała warstwa gry — 6.D183.
    ///
    /// <para><b>7 → 8 (13.09.2026, MB-02):</b> ósma etykieta to panel wyniku sesji
    /// treningowej. Droga na ekran jest nadal JEDNA — wszystkie osiem przypisań stoi
    /// w ciele <c>Hud.Update</c>, co pilnuje asercja niżej, i to ona jest treścią tej
    /// liczby, a nie sama liczba.</para>
    /// </summary>
    // 8 -> 9 (14.09.2026, MB-03): dziewiąta etykieta to wiersz blokady trakcji.
    // Droga na ekran zostaje JEDNA — wszystkie dziewięć przypisań stoi w ciele
    // `Hud.Update`, co pilnuje asercja niżej.
    private const int PrzypisanText = 9;

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

        // GŁÓWNA LICZBA POZYCJI 6.D183 PO ODJĘCIU TRAFIEŃ FAŁSZYWYCH. Bez tego odjęcia
        // „ile tekstu widzi gracz" rosłoby o każdy komunikat wyjątku dopisany
        // w metodzie stojącej na mapie — i przestałoby odpowiadać na swoje pytanie.
        var dlaGracza = zeSlowem
            .Where(l => !NieDocierajaceNaEkran.Contains(l, StringComparer.Ordinal))
            .ToList();
        Assert.AreEqual(DlaGraczaNaEkranie, dlaGracza.Count,
            $"napisów DLA GRACZA jest {dlaGracza.Count} wobec zmierzonych "
            + $"{DlaGraczaNaEkranie}: " + string.Join(" | ", dlaGracza));

        // KONTROLA PRZYRZĄDU listy odejmowanej: każdy jej wpis MUSI być wśród
        // znalezionych. Wpis, którego skan nie widzi, odejmowałby zero i lista
        // wyglądałaby na działającą — rodzina 6.D159.
        foreach (var nieekranowy in NieDocierajaceNaEkran)
        {
            Assert.IsTrue(zeSlowem.Contains(nieekranowy, StringComparer.Ordinal),
                $"literał „{nieekranowy}” z listy nieekranowych NIE został znaleziony "
                + "przez skan — lista odejmuje wtedy zero i nic nie mówi");
        }

        // Liczba PORÓWNAWCZA do 6.D175, które mierzyło rodzinę „polski znak
        // diakrytyczny" i odpowiedziało „trzy ze 140". Różnica między nią a liczbą
        // wyżej JEST odpowiedzią 6.D183, więc stoi w teście, a nie tylko w raporcie.
        var zDiakrytykiem = zeSlowem
            .Where(l => l.Any(z => ZnakiDiakrytyczne.Contains(z, StringComparison.Ordinal)))
            .ToList();
        Assert.AreEqual(ZDiakrytykiemNaEkranie, zDiakrytykiem.Count,
            $"z polskim znakiem jest {zDiakrytykiem.Count} wobec zmierzonych "
            + $"{ZDiakrytykiemNaEkranie}: " + string.Join(" | ", zDiakrytykiem));

        var zDiakrytykiemDlaGracza = zDiakrytykiem
            .Where(l => !NieDocierajaceNaEkran.Contains(l, StringComparer.Ordinal))
            .ToList();
        Assert.AreEqual(ZDiakrytykiemDlaGracza, zDiakrytykiemDlaGracza.Count,
            $"z polskim znakiem DLA GRACZA jest {zDiakrytykiemDlaGracza.Count} wobec "
            + $"zmierzonych {ZDiakrytykiemDlaGracza}: "
            + string.Join(" | ", zDiakrytykiemDlaGracza));

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
    // 106 -> 110 i 118 -> 122 (13.09.2026, MB-02). RÓŻNICA ZOSTAJE NA 12 i to ona
    // jest treścią tej pary, a nie żadna z liczb osobno.
    // 110 -> 120 (14.09.2026, MB-04): `FirstRun.AssetsRoot`, `DomyslnyZapisWejsc`
    // i wiersz `[ZAPISY]`. Liczba ZMIERZONA przyrzadem tego testu, a nie
    // przepisana z jego komunikatu o bledzie.
    // 120 -> 126 (14.09.2026, MB-05): `CabView.cs`, wiersz `[KABINA]`, stała
    // `ExitCabMissing` i wpięcie kabiny w `FirstRun`. Liczba ZMIERZONA
    // przyrzadem tego testu.
    // 126 -> 130 (14.09.2026, MB-07): literały dołożone przez drugi skład —
    // nazwy argumentów `trains`/`headway-steps` w `RunPlan`, komunikaty odmowy
    // zakresu i nazwy węzłów widoków w `FirstRun`. Liczba jest PRZELICZONA
    // przebiegiem, a nie wyprowadzona z liczby dopisanych wierszy.
    // 130 -> 134 (14.09.2026, MB-07): trzy klawisze obsługi linii (N/T/O), wiersz
    // `[TUNEL koniec]` i komunikaty zakresu `--trains`. Liczba PRZELICZONA przebiegiem.
    // 134 -> 139 (22.09.2026, 6.D235): PIĘĆ literałów — komunikaty `Abort` dla pliku ZŁEGO
    // w `FirstRun`: po dwa przy osi i przy manifeście chunków, jeden przy planie
    // sygnalizacji. Liczba PRZELICZONA przebiegiem.
    // 139 -> 137 (23.09.2026, 6.M1): odtworzenie linii — zdarzenia w zapisie wejść, `ExecuteLineEvent` w `FirstRun` i nowa odmowa `--replay --line` bez `--signalling` w `RunPlan`. PRZELICZONE.
    // 137 -> 138 (23.09.2026, tory i światła): nowy literał na drodze całego pliku. PRZELICZONE.
    // 138 -> 140 (24.09.2026, station-wayfinding): ścieżka tablicy i komunikat odmowy.
    // 140 -> 141 (24.09.2026, interaktywne R): odmowa przeładowania sceny.
    private const int ZgloszenFirstRunCalymPlikiem = 141;

    /// <summary>Ile daje ten sam plik liczony WIERSZ PO WIERSZU — 6.D180.</summary>
    // 122 -> 132 (14.09.2026, MB-04): `FirstRun.AssetsRoot`, `DomyslnyZapisWejsc`
    // i wiersz `[ZAPISY]`. Liczba ZMIERZONA przyrzadem tego testu.
    // 132 -> 138 (14.09.2026, MB-05): `CabView.cs` i wpięcie kabiny w `FirstRun`.
    // Liczba ZMIERZONA przyrzadem tego testu.
    // 138 -> 142 (14.09.2026, MB-07): jak wyżej — literały drugiego składu.
    // 142 -> 146 (14.09.2026, MB-07): przeliczone przebiegiem.
    // 146 -> 151 (22.09.2026, 6.D235): PIĘĆ literałów — komunikaty `Abort` dla pliku ZŁEGO
    // w `FirstRun`: po dwa przy osi i przy manifeście chunków, jeden przy planie
    // sygnalizacji. Liczba PRZELICZONA przebiegiem.
    // 151 -> 149 (23.09.2026, 6.M1): odtworzenie linii — zdarzenia w zapisie wejść, `ExecuteLineEvent` w `FirstRun` i nowa odmowa `--replay --line` bez `--signalling` w `RunPlan`. PRZELICZONE.
    // 149 -> 150 (23.09.2026, tory i światła): nowy literał na drodze wierszy. PRZELICZONE.
    // 150 -> 152 (24.09.2026, station-wayfinding): te same dwa literały tablicy.
    // 152 -> 153 (24.09.2026, interaktywne R): nowy komunikat błędu.
    private const int ZgloszenFirstRunWierszami = 153;

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

        var kodFirstRun = File.ReadAllText(Path.Combine(MetroBxl.Tests.Shared.KorzenRepozytorium.Sciezka, "src", "Game", "FirstRun.cs"));
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
    // 335 -> 348 (13.09.2026, MB-02). Zasięg mechaniki, nie liczba usterek: liczba
    // ZABRANYCH werdyktów niżej ma zostać na dwóch i to ona jest tu treścią.
    // 354 -> 363 (14.09.2026, MB-04): `FirstRun.AssetsRoot`, `DomyslnyZapisWejsc`
    // i wiersz `[ZAPISY]`. Liczba ZMIERZONA przyrzadem tego testu, a nie
    // przepisana z jego komunikatu o bledzie.
    // 363 -> 367 (14.09.2026, MB-05): `CabView.cs`, wiersz `[KABINA]`, stała
    // `ExitCabMissing` i wpięcie kabiny w `FirstRun`. Liczba ZMIERZONA
    // przyrzadem tego testu.
    // 367 -> 378 (14.09.2026, MB-07): literały dołożone przez drugi skład —
    // nazwy argumentów `trains`/`headway-steps` w `RunPlan`, komunikaty odmowy
    // zakresu i nazwy węzłów widoków w `FirstRun`. Liczba jest PRZELICZONA
    // przebiegiem, a nie wyprowadzona z liczby dopisanych wierszy.
    // 378 -> 381 (14.09.2026, MB-07): trzy klawisze obsługi linii (N/T/O), wiersz
    // `[TUNEL koniec]` i komunikaty zakresu `--trains`. Liczba PRZELICZONA przebiegiem.
    // 381 -> 393 (14.09.2026, MB-08): większy korpus, ta sama mechanika.
    // ROZSTRZYGNIĘCIE TEJ SEKCJI SIĘ NIE ZMIENIA i to jest sprawdzone poniżej,
    // a nie założone: liczba WERDYKTÓW zmienionych przez zdejmowanie jednostek
    // stoi na dwóch, więc nowe literały wchodzą pod mechanikę, a nie pod wyjątek.
    // 393 -> 394 (17.09.2026, 6.D229): JEDEN literał — argument `what` przekazany
    // do `JsonText.Parse` w `src/Game/Assets/ChunkManifest.cs` ("manifest chunków").
    // Jest to napis, który trafia do WIERSZA ODMOWY widzianego przez gracza, więc
    // wchodzi do korpusu z tego samego powodu, co komunikaty `Abort` w `FirstRun`.
    // 394 -> 399 (22.09.2026, 6.D235): PIĘĆ literałów — komunikaty `Abort` dla pliku ZŁEGO
    // w `FirstRun`: po dwa przy osi i przy manifeście chunków, jeden przy planie
    // sygnalizacji. Liczba PRZELICZONA przebiegiem.
    // 399 -> 400 (23.09.2026, 6.M1): odtworzenie linii — zdarzenia w zapisie wejść, `ExecuteLineEvent` w `FirstRun` i nowa odmowa `--replay --line` bez `--signalling` w `RunPlan`. PRZELICZONE.
    // 400 -> 402 (24.09.2026, braking cue): dwa użycia klucza po zdjęciu jednostek.
    // 402 -> 404 (24.09.2026, preparing to brake): two new catalog lookups.
    // 404 -> 406 (24.09.2026, station-wayfinding): dwa literały ścieżki i odmowy.
    // 406 -> 407 (24.09.2026, HUD 800x600): nowy klucz krótkiej pozycji.
    // 407 -> 408 (24.09.2026, interaktywne R): komunikat błędu.
    // 408 -> 410 (24.09.2026, krótki HUD chase): te same dwa napisy.
    // 410 -> 411 (24.09.2026, integracja pomocy linii): jeden dodatkowy literał.
    private const int LiteralowDotknietychZdejmowaniem = 412;

    /// <summary>
    /// Ilu literałom zdejmowanie jednostek ZABIERA werdykt „to słowo" — 6.D155.
    /// </summary>
    //
    // **2 -> 1 (14.09.2026, MB-03), i ta liczba SPADŁA z powodu, który trzeba
    // przeczytać, a nie przeliczyć.** Drugim z dwóch był literał wiersza prędkości
    // stojący w ciele `Hud.Update`: po zdjęciu dziur i jednostek zostawało z niego
    // samo `a`, czyli jedna litera, więc sito odbierało mu werdykt „to jest słowo".
    // MB-03 przeniosło ten wiersz do katalogu jako `hud.speed` i dołożyło do niego
    // słowo `sufit` — a wtedy resztka brzmi `ufita` (zmierzone: `sufit` traci `s`,
    // bo `s` JEST jednostką, i skleja się z `a` od `a =`). Dwie litery pod rząd
    // znaczą, że werdykt ZOSTAJE, więc literał wypada ze zbioru „zabranych".
    //
    // **To nie jest regres, tylko dokładnie ten ruch, o który chodziło 6.D83:**
    // wiersz prędkości przestał być napisem bez słów składanym w kodzie i stał się
    // wpisem katalogu niosącym polskie słowo. Zbiór „zabranych" kurczy się więc do
    // jednego elementu, którym jest `Esc` — nazwa klawisza, a nie tekst dla gracza.
    private const int WerdyktowZabranychPrzezZdejmowanie = 1;

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

        // I KTÓRY to jest — bo pole „Skończone, gdy" pozycji pyta, czy któryś jest
        // tekstem dla gracza. **Do 14.09.2026 odpowiedź brzmiała TAK i była tu
        // wykonana; po MB-03 brzmi NIE, i to też jest tu wykonane.** Zbiór ma dziś
        // jeden element i jest nim `Esc`, czyli NAPIS NA KLAWISZU — ta sama granica,
        // którą `UiText` stawia między „co klawisz robi" a „jak się nazywa".
        Assert.IsTrue(zabrane.Contains("Esc", StringComparer.Ordinal),
            "„Esc” przestał być w zbiorze — na nim stoi rozstrzygnięcie 6.D142: "
            + string.Join(" | ", zabrane));
        Assert.IsTrue(NazwyKlawiszy.Contains("Esc", StringComparer.Ordinal),
            "„Esc” wypadł z `NazwyKlawiszy`, więc zdanie o bezczynności wyjątku "
            + "z 6.D142 opisuje inny stan");

        // **Ten akapit jest PRZEPISANY przy MB-03, a nie dopisany obok.** Do 14.09.2026
        // stało tu wyszukanie „drugiego z dwóch" przez `zabrane.Single(…)` i asercja,
        // że stoi on w ciele `Hud.Update`. Po przeniesieniu wiersza prędkości do
        // katalogu drugiego nie ma, a `Single` RZUCAŁBY — czyli bramka padałaby
        // wyjątkiem zamiast komunikatem i nie powiedziałaby, co się zmieniło.
        //
        // Pytanie zostaje to samo, tylko zadane właściwej stronie: wiersz prędkości
        // ma dalej mieć w sobie SYMBOL PRZYSPIESZENIA i nic poza nim ponad słowa
        // katalogu. Bierzemy go więc stamtąd, gdzie teraz mieszka.
        var wierszPredkosci = UiText.Get("hud.speed");
        var wHudUpdate = Literaly(CialoDeklaracji(
            HudSource(), "public void Update("));
        Assert.IsFalse(wHudUpdate.Contains(wierszPredkosci, StringComparer.Ordinal),
            "wiersz prędkości wrócił do ciała `Hud.Update` — katalog przestaje być "
            + "jednym miejscem dokładnie w tym jednym wierszu, w którym nim nie był");
        // CO w nim zostaje, a nie „czy zostaje słowo". Zostaje `ufita`: `sufit` bez
        // litery `s` (bo `s` JEST jednostką i sito zjada ją także w środku wyrazu)
        // sklejone z `a` od `a =`. Zapadka stoi na WYNIKU PRZYRZĄDU, a nie na tym,
        // czego się po nim spodziewano — `sufita` byłoby zgadywaniem.
        var resztka = BezJednostek(BezDziur(wierszPredkosci))
            .Replace(" ", string.Empty, StringComparison.Ordinal)
            .Replace("=", string.Empty, StringComparison.Ordinal);
        Assert.AreEqual("ufita", resztka,
            $"po zdjęciu dziur i jednostek w „{wierszPredkosci}” zostaje „{resztka}” "
            + "zamiast `ufita` — wiersz prędkości niesie wtedy inne słowa, niż mówi "
            + "ten pomiar, i milczenie sita wymaga nowego powodu");
        Assert.IsTrue(resztka.Length > 1,
            $"resztka („{resztka}”) wróciła do JEDNEJ litery — wiersz prędkości stracił "
            + "słowo z własnego prawa, czyli `sufit`, i znów jest napisem bez słów");
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


    // --- 6.D185: nazwy członów wyliczeń na ekranie ---------------------------------

    /// <summary>
    /// Ile dziur interpolacji ma cała droga <c>Hud.Update</c> — zmierzone 13.09.2026.
    ///
    /// <para>Zapadka RÓWNOŚCIOWA i to jest jej treść: nazwa członu wyliczenia trafia
    /// na ekran przez dziurę, a nie przez literał, więc rodziny z 6.D154…6.D183 —
    /// wszystkie liczone po literałach — zobaczyć jej nie mogą. Dwudziesta pierwsza
    /// dziura zapala ten test i każe ją zaklasyfikować, zamiast wpaść po cichu.</para>
    /// </summary>
    //
    // **20 -> 18 (14.09.2026, MB-03), i ta liczba SPADŁA, a nie urosła.** Wiersz
    // prędkości był do tego dnia JEDYNYM, który składał się interpolacją WPROST
    // w ciele `Hud.Update` (`$"{speedKmh,6:F1} km/h … {accelerationMps2,6:F2} m/s²"`),
    // czyli omijał katalog. MB-03 przenosi go do `UiText` jako `hud.speed`, więc dwie
    // dziury znikają, a na ich miejsce wchodzą pola szablonu — czyli LITERAŁY, które
    // rodziny 6.D154…6.D183 już widzą. Spadek jest tu wynikiem pożądanym i dlatego
    // zapadka równościowa go pokazuje: gdyby ktoś wiersz prędkości złożył z powrotem
    // w kodzie, liczba wróciłaby do dwudziestu i ten test by o tym powiedział.
    // 18 -> 20 (14.09.2026, MB-07): trzy klawisze obsługi linii (N/T/O), wiersz
    // `[TUNEL koniec]` i komunikaty zakresu `--trains`. Liczba PRZELICZONA przebiegiem.
    private const int DziurNaEkranie = 20;

    /// <summary>
    /// Które z tych dziur wstawiają wartość wyliczenia — WPISANE, nie wyprowadzone.
    ///
    /// <para><b>Dlaczego wpisane.</b> Rozstrzygnięcie typu dziury to analiza typów
    /// C#, czyli ta sama zależność, przed którą <c>CLAUDE.md</c> §8 kazała przerwać
    /// przy mapie <see cref="ZrodlaHud"/>. Skan po NAZWIE, który stoi niżej, jest
    /// wyłącznie DETEKTOREM ZMIANY: bramka żąda, żeby dał dokładnie tę listę.
    /// Rozejście się jednej ze stron zapala test — i wtedy rozstrzyga człowiek.</para>
    /// </summary>
    private static readonly string[] DziuryZWyliczeniem =
    {
        "authority.Reason", "decision.Action",
    };

    /// <summary>
    /// Ile NAZW członów wyliczeń może dziś trafić na ekran — zmierzone 13.09.2026.
    ///
    /// <para>Cztery z <c>AuthorityLimit</c> (dziura bezwarunkowa, wszystkie cztery
    /// nadawane w <c>FixedBlockSystem</c>) plus DWIE z <c>ProtectionAction</c> —
    /// <b>nie trzy</b>. <c>None</c> na ekran nie dociera, bo przed dziurą stoi straż
    /// <c>decision.Action == ProtectionAction.None ? string.Empty : …</c>. Pole
    /// „Co gracz widzi” pozycji 6.D185 wymienia <c>None</c> razem z pozostałymi;
    /// pomiar tego nie potwierdza i dlatego liczba stoi tutaj, a nie tam.</para>
    /// </summary>
    private const int NazwCzlonowNaEkranie = 6;

    /// <summary>Ile członów ma <c>DoorPhase</c> w <c>src/Sim/Train/DoorCycle.cs</c>.</summary>
    private const int CzlonowDoorPhase = 7;

    /// <summary>
    /// Ile trafień daje skan po NAZWIE puszczony na CAŁE <c>src/Game/</c> — 6.D185.
    /// </summary>
    // 12 -> 13 (13.09.2026, MB-02). Trzynaste trafienie to `RunSummary.cs:action` —
    // i jest FAŁSZYWE tak samo jak `RunPlan.cs:view`: pod nazwą `action` stoi tam
    // `string`, a nie `ProtectionAction`. Liczba rośnie, a teza 6.D185 („skan po nazwie
    // myli się na połowie trafień") zostaje niezmieniona — trafień fałszywych przybyło
    // razem z wszystkimi.
    private const int TrafienSkanuWGame = 13;

    /// <summary>
    /// Dziury, na których skan po nazwie się MYLI — nazwa jest wyliczeniem gdzie
    /// indziej, a w tym miejscu stoi pod nią napis. Zmierzone 13.09.2026.
    ///
    /// <para><b>To jest powód, dla którego bramka 6.D185 kończy się na drodze
    /// <c>Hud.Update</c>, a nie obejmuje całego <c>src/Game/</c>.</b> Skan myli się
    /// na POŁOWIE trafień i nie jest to wąskie sito ani literówka we wzorcu: nazwa
    /// <c>Reason</c> nosi w tym drzewie i wyliczenie (<c>MovementAuthority.Reason</c>
    /// typu <c>AuthorityLimit</c>), i napis (<c>ChaseAvailability.Reason</c>,
    /// <c>ViewAssumption.Reason</c>); <c>Variant</c> — wyliczenie
    /// <c>ProtectionVariant</c> i napis <c>ChunkManifest.Variant</c>; <c>view</c> —
    /// <c>ViewKind</c> w <c>RunHeader</c> i surowy argument wiersza poleceń
    /// w <c>RunPlan</c>. Pomylenie się na nazwie nie jest więc możliwością, tylko
    /// stanem drzewa.</para>
    /// </summary>
    private static readonly string[] FalszyweTrafieniaSkanu =
    {
        "ChunkManifest.cs:Variant",
        "DesignAssumptions.cs:Reason",
        "FirstRun.cs:availability.Reason",
        "FirstRun.cs:_manifest.Variant",
        "RunPlan.cs:view",
        "TunnelView.cs:manifest.Variant",
    };

    /// <summary>
    /// Wyliczenia zadeklarowane w <c>src/</c> — nazwa typu na listę członów.
    ///
    /// <para><b>Czyta też <c>src/Sim/</c> i to jest odpowiedź pozycji 6.D185 na pytanie
    /// o granicę korpusu.</b> Granica przesuwa się dla DEKLARACJI, nie dla skanowanego
    /// tekstu: <c>AuthorityLimit</c> i <c>ProtectionAction</c> mieszkają w rdzeniu,
    /// więc bramka czytająca wyłącznie <c>src/Game/</c> nie wie, że to wyliczenia —
    /// i znajduje ZERO dziur, cicho i na zielono. Skanowanym korpusem zostaje droga
    /// <c>Hud.Update</c> w <c>src/Game/</c>; rdzeń jest tu SŁOWNIKIEM TYPÓW.</para>
    /// </summary>
    /// <summary>
    /// Wyliczenia <c>src/</c> czytane Z TEKSTU ZAMASKOWANEGO — 6.D212.
    ///
    /// <para><b>Do 15.09.2026 czytało z tekstu SUROWEGO, a zmiana nie bierze się
    /// z usterki w drzewie, tylko z pomiaru.</b> Oba czytniki dają dziś wynik
    /// identyczny — <b>20 wyliczeń surowo i 20 po masce, zero rozjazdów</b> — bo
    /// sito członów odrzuca wiersze zaczynające się od <c>/</c>. Zmierzone są
    /// natomiast <b>podstawienia, które je rozdzielają</b>, i jest ich trzy:
    /// komentarz blokowy PRZED członem w jego wierszu (<c>/* x */ Dry,</c> — surowy
    /// gubi człon), słowo <c>enum</c> w komentarzu blokowym i słowo <c>enum</c>
    /// w literale (surowy wymyśla CAŁE wyliczenie, którego w kodzie nie ma).</para>
    ///
    /// <para><b>Czwarte podstawienie NIE rozdziela ich i to jest poprawka do
    /// zapisanego zdania, a nie nowe ustalenie.</b> <c>reports/6d197-…</c> §6 mówi,
    /// że „komentarz członu w tym samym wierszu (<c>Dry, // sucha</c>) przesunąłby
    /// oba czytniki". Zmierzone: nie przesuwa — sito bierze PIERWSZE SŁOWO wiersza,
    /// a jest nim <c>Dry</c>. Raportu nie poprawiam (6.D108: raport jest historią);
    /// granica stoi tutaj.</para>
    ///
    /// <para><b>Maska nie jest nowym czytnikiem — i za pierwszym razem BYŁA, co
    /// poprawia 6.D213.</b> 6.D212 dopisało tu własne `Zamaskowany`, składające
    /// <see cref="PominNieNapis"/>, <see cref="PrefiksLiteralu"/> i
    /// <see cref="CzytajLiteral"/> — czyli dokładnie to, co robił już
    /// <see cref="KodLeksykalnie"/> z 6.D199, w TYM SAMYM pliku. Zmierzone przy
    /// 6.D213: oba czytniki dają wynik <b>identyczny znak w znak na każdym pliku
    /// <c>src/</c></b>, więc kopia poszła, a wołany jest czytnik, który był
    /// pierwszy.</para>
    /// </summary>
    private static Dictionary<string, List<string>> WyliczeniaZrodel()
    {
        var wynik = new Dictionary<string, List<string>>(StringComparer.Ordinal);
        foreach (var sciezka in PlikiZrodlowe())
        {
            foreach (var para in WyliczeniaZTekstu(File.ReadAllText(sciezka)))
            {
                wynik[para.Key] = para.Value;
            }
        }

        return wynik;
    }

    /// <summary>
    /// Kontrola PRZYRZĄDU, nie drzewa — 6.D212.
    ///
    /// <para>Rozjazd między czytnikiem surowym a maskującym wynosi dziś w całym
    /// <c>src/</c> <b>zero</b>, więc sam zielony przebieg nie mówi o masce nic:
    /// czytnik, który maski nie stosuje, odpowiedziałby tak samo. Próbki niżej są
    /// syntetyczne i każda z nich NAPRAWDĘ rozdziela oba czytniki — poza ostatnią,
    /// która jest tu po to, żeby pokazać, że ich NIE rozdziela.</para>
    /// </summary>
    [TestMethod]
    public void Czytnik_wyliczen_nie_daje_sie_nabrac_na_enum_w_komentarzu_ani_w_literale()
    {
        const string wKomentarzu =
            "/* public enum Duch { Alfa, } */\npublic enum Proba\n{\n    Dry,\n    Wet,\n}\n";
        const string wLiterale =
            "const string s = \"public enum Duch { Alfa, }\";\npublic enum Proba\n{\n    Dry,\n    Wet,\n}\n";
        const string komentarzPrzedCzlonem =
            "public enum Proba\n{\n    /* x */ Dry,\n    Wet,\n}\n";
        const string komentarzZaCzlonem =
            "public enum Proba\n{\n    Dry, // sucha\n    Wet,\n}\n";

        CollectionAssert.AreEqual(new[] { "Proba" }, WyliczeniaZTekstu(wKomentarzu).Keys.ToList(),
            "wyliczenie z KOMENTARZA weszło do wyniku — maska nie działa");
        CollectionAssert.AreEqual(new[] { "Proba" }, WyliczeniaZTekstu(wLiterale).Keys.ToList(),
            "wyliczenie z LITERAŁU weszło do wyniku — maska nie działa");
        CollectionAssert.AreEqual(new[] { "Dry", "Wet" },
            WyliczeniaZTekstu(komentarzPrzedCzlonem)["Proba"],
            "komentarz PRZED członem zjadł człon — maska nie działa");

        // Czwarta próbka jest granicą, a nie usterką: `Dry, // sucha` czyta się tak samo
        // z maską i bez niej, bo sito bierze PIERWSZE SŁOWO wiersza. Zdanie z §6 raportu
        // 6.D197, które mówi inaczej, jest tym pomiarem obalone.
        CollectionAssert.AreEqual(new[] { "Dry", "Wet" },
            WyliczeniaZTekstu(komentarzZaCzlonem)["Proba"], "komentarz ZA członem nie ma prawa nic zmienić");

        // I dopiero to mówi, że maska jest do czegoś potrzebna: czytnik SUROWY,
        // czyli dokładnie ten sprzed tej pozycji, daje na trzech pierwszych próbkach
        // inny wynik, a na czwartej ten sam.
        var surowy = new Func<string, Dictionary<string, List<string>>>(zrodlo =>
        {
            var wynik = new Dictionary<string, List<string>>(StringComparer.Ordinal);
            foreach (Match m in Regex.Matches(zrodlo, @"\benum\s+(\w+)\s*\{([^}]*)\}"))
            {
                wynik[m.Groups[1].Value] = Regex
                    .Matches(m.Groups[2].Value, @"^\s*(\w+)", RegexOptions.Multiline)
                    .Select(x => x.Groups[1].Value).ToList();
            }

            return wynik;
        });

        Assert.IsTrue(surowy(wKomentarzu).ContainsKey("Duch"),
            "czytnik surowy NIE dał się nabrać na komentarz — próbka przestała rozdzielać czytniki");
        Assert.IsTrue(surowy(wLiterale).ContainsKey("Duch"),
            "czytnik surowy NIE dał się nabrać na literał — próbka przestała rozdzielać czytniki");
        CollectionAssert.AreEqual(new[] { "Wet" }, surowy(komentarzPrzedCzlonem)["Proba"],
            "czytnik surowy NIE zgubił członu — próbka przestała rozdzielać czytniki");
        CollectionAssert.AreEqual(new[] { "Dry", "Wet" }, surowy(komentarzZaCzlonem)["Proba"],
            "czytnik surowy przeczytał `Dry, // sucha` inaczej niż maskujący — granica z §6 wróciła");
    }

    /// <summary>Wyliczenia jednego źródła — osobno, żeby kontrola przyrządu miała co wołać.</summary>
    private static Dictionary<string, List<string>> WyliczeniaZTekstu(string source)
    {
        var wynik = new Dictionary<string, List<string>>(StringComparer.Ordinal);
        foreach (Match m in Regex.Matches(
            KodLeksykalnie(source), @"\benum\s+(\w+)\s*\{([^}]*)\}"))
        {
            wynik[m.Groups[1].Value] = Regex
                .Matches(m.Groups[2].Value, @"^\s*(\w+)", RegexOptions.Multiline)
                .Select(x => x.Groups[1].Value).ToList();
        }

        return wynik;
    }

    /// <summary>Wszystkie pliki <c>.cs</c> pod <c>src/</c>, bez wygenerowanych.</summary>
    private static List<string> PlikiZrodlowe() =>
        Directory.GetFiles(Path.Combine(MetroBxl.Tests.Shared.KorzenRepozytorium.Sciezka, "src"), "*.cs",
                SearchOption.AllDirectories)
            .Where(p => !p.Split(Path.DirectorySeparatorChar).Contains(".godot"))
            .Where(p => !p.Split(Path.DirectorySeparatorChar).Contains("obj"))
            .Where(p => !p.Split(Path.DirectorySeparatorChar).Contains("bin"))
            .OrderBy(p => p, StringComparer.Ordinal)
            .ToList();

    /// <summary>
    /// Nazwy, pod którymi w <c>src/</c> zadeklarowano wartość typu wyliczeniowego.
    ///
    /// <para>Sito jest po NAZWIE, nie po typie, i mówi o tym wprost — zbiór wartości
    /// pokazuje, że jedna nazwa bywa dwuznaczna. Czym to grozi, mierzy
    /// <see cref="Skan_po_NAZWIE_myli_sie_na_POLOWIE_trafien_w_calym_src_Game"/>.</para>
    /// </summary>
    private static Dictionary<string, SortedSet<string>> NazwyOTypieWyliczeniowym()
    {
        var typy = WyliczeniaZrodel().Keys.OrderBy(t => t, StringComparer.Ordinal).ToList();
        var wynik = new Dictionary<string, SortedSet<string>>(StringComparer.Ordinal);
        foreach (var sciezka in PlikiZrodlowe())
        {
            var kod = File.ReadAllText(sciezka);
            foreach (var typ in typy)
            {
                foreach (Match m in Regex.Matches(kod, @"\b" + typ + @"\??\s+(\w+)\b"))
                {
                    if (!wynik.TryGetValue(m.Groups[1].Value, out var zbior))
                    {
                        wynik[m.Groups[1].Value] = zbior =
                            new SortedSet<string>(StringComparer.Ordinal);
                    }

                    zbior.Add(typ);
                }
            }
        }

        return wynik;
    }

    /// <summary>
    /// Wyrażenia z dziur interpolacji danego kodu, bez wyrównania i formatu.
    ///
    /// <para>Cięcie na <c>,</c> albo <c>:</c> liczy nawiasy, bo
    /// <c>{Units.MpsToKmh(decision.PermittedSpeedMps),5:F1}</c> ma przecinek i wewnątrz
    /// wywołania, i przed wyrównaniem — cięcie na pierwszym dałoby wyrażenie ucięte
    /// w środku argumentu.</para>
    /// </summary>
    private static List<string> DziuryInterpolacji(string kod)
    {
        var wynik = new List<string>();
        foreach (var literal in Literaly(kod))
        {
            foreach (Match m in Regex.Matches(literal, "[{][^{}]*[}]"))
            {
                var wnetrze = m.Value[1..^1];
                var ciecie = wnetrze.Length;
                var glebia = 0;
                for (var i = 0; i < wnetrze.Length; i++)
                {
                    var znak = wnetrze[i];
                    if (znak is '(' or '[')
                    {
                        glebia++;
                    }
                    else if (znak is ')' or ']')
                    {
                        glebia--;
                    }
                    else if (glebia == 0 && (znak == ',' || znak == ':'))
                    {
                        ciecie = i;
                        break;
                    }
                }

                wynik.Add(wnetrze[..ciecie].Trim());
            }
        }

        return wynik;
    }

    /// <summary>Wszystkie dziury interpolacji drogi <c>Hud.Update</c> — 6.D185.</summary>
    private static List<string> DziuryNaEkranie()
    {
        var wynik = new List<string>();
        foreach (var (_, plik, czlon) in ZrodlaHud)
        {
            wynik.AddRange(DziuryInterpolacji(CialoDeklaracji(ZrodloGry(plik), czlon)));
        }

        wynik.AddRange(DziuryInterpolacji(
            CialoDeklaracji(HudSource(), "public void Update(")));
        return wynik;
    }

    /// <summary>Ostatni człon wyrażenia dziury — <c>Reason</c> z <c>authority.Reason</c>.</summary>
    private static string OgonWyrazenia(string wyrazenie) => wyrazenie.Split('.')[^1];

    /// <summary>
    /// Dziury drogi <c>Hud.Update</c>, a wśród nich te wstawiające wyliczenie — 6.D185.
    ///
    /// <para>Bramka odpowiada na pole „Weryfikacja” pozycji wprost: lista znalezionych
    /// dziur ma zawierać <c>authority.Reason</c> i <c>decision.Action</c>. Żąda WIĘCEJ
    /// niż zawierania — żąda RÓWNOŚCI z listą wpisaną, bo lista dłuższa o trafienie
    /// fałszywe byłaby tak samo cicha jak krótsza o pominięte.</para>
    /// </summary>
    [TestMethod]
    public void Dziury_z_wyliczeniem_na_drodze_Hud_Update()
    {
        var dziury = DziuryNaEkranie();
        var nazwy = NazwyOTypieWyliczeniowym();

        // Dolne ostrze na SAM SKAN: literówka we wzorcu daje pustą listę, a pusta lista
        // przechodzi „nie ma żadnej dziury z wyliczeniem" bez jednego sprawdzenia (6.D27).
        Assert.AreEqual(DziurNaEkranie, dziury.Count,
            $"drogą `Hud.Update` biegnie dziś {dziury.Count} dziur interpolacji wobec "
            + $"zmierzonych {DziurNaEkranie}: " + string.Join(" | ", dziury));

        var zWyliczeniem = dziury
            .Where(d => nazwy.ContainsKey(OgonWyrazenia(d)))
            .Distinct(StringComparer.Ordinal)
            .OrderBy(d => d, StringComparer.Ordinal)
            .ToList();

        CollectionAssert.AreEqual(
            DziuryZWyliczeniem.OrderBy(d => d, StringComparer.Ordinal).ToList(),
            zWyliczeniem,
            "skan dziur daje dziś " + string.Join(", ", zWyliczeniem)
            + ", a wpisano " + string.Join(", ", DziuryZWyliczeniem)
            + " — jeśli lista jest pusta, skan patrzy nie tam; jeśli dłuższa, "
            + "doszła dziura z wyliczeniem albo skan złapał nazwę dwuznaczną");
    }

    /// <summary>
    /// <c>ProtectionAction.None</c> na ekran NIE dociera — 6.D185.
    ///
    /// <para>Pole „Co gracz widzi” pozycji wymienia <c>None</c> wśród identyfikatorów
    /// widzianych przez gracza. Straż w <c>SignallingHud.Line</c> mówi co innego
    /// i dlatego jest tu sprawdzana, a nie przyjęta: zdjęcie jej wpuszcza na ekran
    /// siódmą nazwę i ta bramka zapala się razem z liczbą niżej.</para>
    /// </summary>
    [TestMethod]
    public void Nazwy_czlonow_docierajace_na_ekran_liczone_ze_straza_przy_None()
    {
        var wyliczenia = WyliczeniaZrodel();
        var cialo = CialoDeklaracji(ZrodloGry("SignallingHud.cs"), "public static string Line(");

        var straz = Regex.IsMatch(cialo,
            @"decision\.Action\s*==\s*ProtectionAction\.None\s*\r?\n?\s*\?\s*string\.Empty");
        Assert.IsTrue(straz,
            "zniknęła straż `decision.Action == ProtectionAction.None ? string.Empty` "
            + "z `SignallingHud.Line` — wtedy `None` dociera na ekran i nazw jest siedem, "
            + "nie sześć (6.D185)");

        var zAuthorityLimit = wyliczenia["AuthorityLimit"].Count;
        var zProtectionAction = wyliczenia["ProtectionAction"].Count - 1;
        Assert.AreEqual(NazwCzlonowNaEkranie, zAuthorityLimit + zProtectionAction,
            $"na ekran może dziś trafić {zAuthorityLimit + zProtectionAction} nazw członów "
            + $"wobec zmierzonych {NazwCzlonowNaEkranie}: {zAuthorityLimit} z `AuthorityLimit` "
            + $"i {zProtectionAction} z `ProtectionAction` po odjęciu strzeżonego `None`");
    }

    /// <summary>
    /// <c>Faza</c> ma ramię dla KAŻDEGO członu <c>DoorPhase</c>, więc ramię domyślne
    /// z <c>phase.ToString()</c> jest dziś martwe — 6.D185.
    ///
    /// <para><b>Druga droga na ekran, i dziura jej nie łapie.</b> <c>phase.ToString()</c>
    /// nie stoi w żadnym literale, więc skan dziur go nie widzi — tak samo jak rodziny
    /// liczone po literałach nie widzą dziur. Łapie go co innego i bez żadnej heurystyki:
    /// ósmy człon <c>DoorPhase</c> bez ósmego ramienia ożywia ramię domyślne, a wtedy
    /// ta liczba przestaje się zgadzać. Bramka czyta <c>src/Sim/Train/DoorCycle.cs</c> —
    /// drugi raz w tej sekcji rdzeń jest źródłem DEKLARACJI, nie skanowanym tekstem.</para>
    /// </summary>
    [TestMethod]
    public void Faza_ma_ramie_dla_kazdego_czlonu_DoorPhase_wiec_ramie_domyslne_jest_martwe()
    {
        var czlony = WyliczeniaZrodel()["DoorPhase"];
        Assert.AreEqual(CzlonowDoorPhase, czlony.Count,
            $"`DoorPhase` ma dziś {czlony.Count} członów wobec zmierzonych "
            + $"{CzlonowDoorPhase}: " + string.Join(", ", czlony));

        var faza = CialoDeklaracji(
            ZrodloGry("FirstRun.cs"), "private static string Faza(DoorPhase phase)");
        var ramiona = Regex.Matches(faza, @"DoorPhase\.(\w+)\s*=>")
            .Select(m => m.Groups[1].Value).ToList();

        CollectionAssert.AreEquivalent(czlony, ramiona,
            "`Faza` ma ramiona na " + string.Join(", ", ramiona)
            + ", a `DoorPhase` niesie " + string.Join(", ", czlony)
            + " — człon bez ramienia idzie na ekran ramieniem domyślnym, czyli swoją "
            + "angielską nazwą (6.D185)");

        StringAssert.Contains(faza, "_ => phase.ToString(),",
            "zniknęło ramię domyślne — wtedy człon bez ramienia rzuca wyjątkiem "
            + "w czasie przejazdu, zamiast pokazać nazwę; to zmiana zachowania HUD-u, "
            + "a ta jest poza zakresem 6.D185",
            StringComparison.Ordinal);
    }

    /// <summary>
    /// Skan po NAZWIE myli się na POŁOWIE trafień w całym <c>src/Game/</c> — 6.D185.
    ///
    /// <para><b>To jest odpowiedź „nie da się i dlaczego” dla korpusu szerszego niż
    /// droga <c>Hud.Update</c>.</b> Bramka nie jest tu strażnikiem cudzego kodu, tylko
    /// zapisem POMIARU, który zabrania jej samej urosnąć: gdyby trafień fałszywych
    /// ubyło do zera, skan po nazwie wolno byłoby puścić szerzej — i wtedy ten test
    /// zapali się, żeby o tym powiedzieć. Rośnięcie liczby też zapala.</para>
    /// </summary>
    [TestMethod]
    public void Skan_po_NAZWIE_myli_sie_na_POLOWIE_trafien_w_calym_src_Game()
    {
        var nazwy = NazwyOTypieWyliczeniowym();
        var trafienia = new List<string>();
        var wszystkie = new List<string>();
        foreach (var sciezka in ZrodlaGry())
        {
            var plik = Path.GetFileName(sciezka);
            foreach (var dziura in DziuryInterpolacji(File.ReadAllText(sciezka)))
            {
                wszystkie.Add(dziura);
                if (nazwy.ContainsKey(OgonWyrazenia(dziura)))
                {
                    trafienia.Add($"{plik}:{dziura}");
                }
            }
        }

        // PIN NA SAM CZYTNIK DZIUR, i stoi w tej bramce, a nie w bramce drogi
        // `Hud.Update`, bo TAM nie ma czego pilnować: liczenie nawiasów
        // w `DziuryInterpolacji` rozstrzyga się na DWÓCH dziurach całego `src/Game/`
        // i obie leżą poza tamtą drogą. Zmierzone kontrolą KN-6: bez tego pinu cięcie
        // na pierwszym przecinku — z pominięciem nawiasów — przechodzi na zielono,
        // bo żadnej KLASYFIKACJI nie zmienia; zmienia tylko wypisywane wyrażenie.
        foreach (var pin in new[] { "string.Join(\", \", KnownViews)", "string.Join(\" --\", KnownArguments)" })
        {
            Assert.IsTrue(wszystkie.Contains(pin, StringComparer.Ordinal),
                $"czytnik dziur nie zwrócił `{pin}` — uciął wyrażenie na przecinku "
                + "ze ŚRODKA wywołania, zamiast na przecinku wyrównania");
        }

        Assert.AreEqual(TrafienSkanuWGame, trafienia.Count,
            $"skan po nazwie daje dziś {trafienia.Count} trafień w `src/Game/` wobec "
            + $"zmierzonych {TrafienSkanuWGame}: " + string.Join(" | ", trafienia));

        var falszywe = trafienia
            .Where(t => FalszyweTrafieniaSkanu.Contains(t, StringComparer.Ordinal))
            .Distinct(StringComparer.Ordinal)
            .OrderBy(t => t, StringComparer.Ordinal)
            .ToList();
        CollectionAssert.AreEqual(
            FalszyweTrafieniaSkanu.OrderBy(t => t, StringComparer.Ordinal).ToList(),
            falszywe,
            "trafienia fałszywe to dziś " + string.Join(", ", falszywe)
            + ", a wpisano " + string.Join(", ", FalszyweTrafieniaSkanu)
            + " — jeśli ich UBYŁO, sito po nazwie przestało być dwuznaczne "
            + "i wolno je puścić szerzej niż na drogę `Hud.Update`");

        // POŁOWA Z NAZWY TEJ BRAMKI JEST JUŻ SPRAWDZONA — przez dwie asercje wyżej razem:
        // trafień jest 12, fałszywych 6. Trzecia asercja `12 - 6 == 12 / 2` liczyłaby
        // wyłącznie na stałych, które te dwie właśnie przybiły, i przeszłaby zawsze.
        // Tautologia z rodziny 6.D160 — dlatego jej tu nie ma, a nie dlatego, że ktoś
        // zapomniał sprawdzić proporcję.
    }


    // --- 6.D186: trzynastka kluczy JSON-a i droga, którą ją policzono -----------------

    /// <summary>
    /// Wąska reguła „kształt identyfikatora" z 6.D173 — <c>^[a-z_][a-z0-9_]*$</c>.
    ///
    /// <para>Stoi tu, bo 6.D186 odtwarza pomiar 6.D181, a tamten liczył zgłoszenia
    /// właśnie tą regułą. Do 13.09.2026 nie stała w żadnym pliku — żyła wyłącznie
    /// w treści raportów, więc każde jej odtworzenie było przepisywaniem wzorca z tekstu,
    /// czyli tą samą reimplementacją, która przy 6.D179 dała <b>446</b> zamiast 348.</para>
    /// </summary>
    private const string WaskaRegulaKsztaltu = @"^[a-z_][a-z0-9_]*$";

    /// <summary>Markery kontekstu CZYTANIA JSON-a — to, co zmierzyło 6.D173.</summary>
    private static readonly string[] MarkeryCzytaniaJson =
    {
        "GetProperty", "GetString", "RootElement",
    };

    /// <summary>
    /// Ile zgłoszeń łapie KAŻDY z markerów z osobna — zmierzone 13.09.2026.
    ///
    /// <para><b>Z trzech markerów „kontekstu JSON-a" niesie liczbę JEDEN.</b>
    /// <c>GetProperty</c> daje sam wszystkie osiemnaście; <c>GetString</c> daje osiem
    /// i są to te same osiem (<c>chunk.GetProperty("id").GetString()</c> ma oba
    /// w jednym wierszu); <c>RootElement</c> daje <b>zero</b>, bo pada w kodzie raz —
    /// <c>var root = document.RootElement;</c> — a w tym wierszu nie ma ani jednego
    /// literału. „Kontekst JSON-a" 6.D173 jest więc w praktyce wierszem
    /// z <c>GetProperty</c>.</para>
    ///
    /// <para><b>Ta tabela stoi tu, bo bez niej kontrola negatywna była ZIELONA.</b>
    /// Zdjęcie <c>RootElement</c> z listy markerów nie ruszało żadnej liczby (KN-2),
    /// więc marker dało się usunąć bez jednego czerwonego testu. Nie jest to powód, by
    /// go usunąć — plik JSON może jutro być czytany przez <c>RootElement</c> wprost —
    /// ale jest powodem, by jego bezczynność była WIDOCZNA, a nie domniemana.</para>
    /// </summary>
    private static readonly (string Marker, int Ile)[] UdzialMarkerow =
    {
        ("GetProperty", 18), ("GetString", 8), ("RootElement", 0),
    };

    /// <summary>Zgłoszeń wąskiej reguły, gdy czytnik dostaje CAŁY plik — 6.D173/6.D186.</summary>
    // 96 -> 100 (14.09.2026, MB-04): `FirstRun.AssetsRoot`, `DomyslnyZapisWejsc`
    // i wiersz `[ZAPISY]`. Liczba ZMIERZONA przyrzadem tego testu, a nie
    // przepisana z jego komunikatu o bledzie.
    // 100 -> 101 (14.09.2026, MB-05): `CabView.cs`, wiersz `[KABINA]`, stała
    // `ExitCabMissing` i wpięcie kabiny w `FirstRun`. Liczba ZMIERZONA
    // przyrzadem tego testu.
    // 101 -> 102 (14.09.2026, MB-05, poprawka `--cab` w KnownArguments).
    // 102 -> 104 (14.09.2026, MB-07): literały dołożone przez drugi skład —
    // nazwy argumentów `trains`/`headway-steps` w `RunPlan`, komunikaty odmowy
    // zakresu i nazwy węzłów widoków w `FirstRun`. Liczba jest PRZELICZONA
    // przebiegiem, a nie wyprowadzona z liczby dopisanych wierszy.
    // 104 -> 105 (23.09.2026, 6.M1): odtworzenie linii — zdarzenia w zapisie wejść, `ExecuteLineEvent` w `FirstRun` i nowa odmowa `--replay --line` bez `--signalling` w `RunPlan`. PRZELICZONE.
    private const int ZgloszenWaskichCalymPlikiem = 105;

    /// <summary>Zgłoszeń wąskiej reguły, gdy czytnik dostaje WIERSZ — 6.D173/6.D186.</summary>
    // 108 -> 112 (14.09.2026, MB-04): `FirstRun.AssetsRoot`, `DomyslnyZapisWejsc`
    // i wiersz `[ZAPISY]`. Liczba ZMIERZONA przyrzadem tego testu, a nie
    // przepisana z jego komunikatu o bledzie.
    // 112 -> 113 (14.09.2026, MB-05): `CabView.cs`, wiersz `[KABINA]`, stała
    // `ExitCabMissing` i wpięcie kabiny w `FirstRun`. Liczba ZMIERZONA
    // przyrzadem tego testu.
    // 113 -> 114 (14.09.2026, MB-05, poprawka `--cab` w KnownArguments).
    // 114 -> 116 (14.09.2026, MB-07): literały dołożone przez drugi skład —
    // nazwy argumentów `trains`/`headway-steps` w `RunPlan`, komunikaty odmowy
    // zakresu i nazwy węzłów widoków w `FirstRun`. Liczba jest PRZELICZONA
    // przebiegiem, a nie wyprowadzona z liczby dopisanych wierszy.
    // 116 -> 117 (23.09.2026, 6.M1): odtworzenie linii — zdarzenia w zapisie wejść, `ExecuteLineEvent` w `FirstRun` i nowa odmowa `--replay --line` bez `--signalling` w `RunPlan`. PRZELICZONE.
    private const int ZgloszenWaskichWierszami = 117;

    /// <summary>
    /// Ile z nich stoi w kontekście CZYTANIA JSON-a — <b>18 obiema drogami</b>.
    ///
    /// <para>Liczba jest ta sama po obu stronach i to nie jest przypadek: każdy wiersz
    /// z markerem czytania jest wierszem POJEDYNCZYM, więc podział na wiersze nie ma
    /// tam czego rozciąć. Cała różnica 108 − 96 siedzi po stronie WYPISYWANIA.</para>
    /// </summary>
    private const int WKontekscieCzytaniaJson = 18;

    /// <summary>Trafień „klucz JSON-a wypisywanego" drogą WIERSZOWĄ — liczba 6.D181.</summary>
    private const int KluczyWypisywanychWierszami = 13;

    /// <summary>Trafień „klucz JSON-a wypisywanego" drogą CAŁOPLIKOWĄ — 6.D186.</summary>
    private const int KluczyWypisywanychCalymPlikiem = 1;

    /// <summary>
    /// Jedyne trafienie drogi całoplikowej — i NIE jest kluczem JSON-a.
    ///
    /// <para><c>FirstRun.cs:883</c> niesie <c>Argument("platforms")</c>, czyli nazwę
    /// argumentu wiersza poleceń. Sito „nazwa występuje w pliku w kształcie
    /// <c>"nazwa":</c>" trafia w nie tylko dlatego, że <b>gdzie indziej w tym samym
    /// pliku</b> — w napisie metadanych — stoi klucz o tej samej nazwie. Jest to
    /// kolizja nazw, a nie klucz, i to samo trafienie fałszywe stoi w trzynastce
    /// 6.D181.</para>
    /// </summary>
    private const string JedyneTrafienieCaloplikowe = "platforms";

    /// <summary>Kluczy RÓŻNYCH w napisie metadanych zrzutu — 6.D186.</summary>
    private const int KluczyJsonWypisywanego = 31;

    /// <summary>Wystąpień kluczy w tym samym napisie — 6.D186.</summary>
    private const int WystapienKluczyJson = 35;

    /// <summary>
    /// Które z tych 31 nazw w ogóle padają w korpusie zgłoszeń — i skąd — 6.D186.
    ///
    /// <para>Obie są nazwami argumentów wiersza poleceń (<c>--platforms</c>,
    /// <c>--view</c>), a nie kluczami. Rodzina „klucz JSON-a wypisywanego" liczy
    /// wśród zgłoszeń <b>zero</b>.</para>
    /// </summary>
    private static readonly string[] KluczeJsonObecneWKorpusie = { "platforms", "view" };

    /// <summary>Zgłoszenia wąskiej reguły jako pary (plik, literał), danym czytnikiem.</summary>
    private static List<(string Plik, string Literal)> ZgloszeniaWaskie(
        Func<string, List<string>> czytnik)
    {
        var wynik = new List<(string, string)>();
        foreach (var sciezka in ZrodlaGry())
        {
            var nazwa = Path.GetFileName(sciezka);
            foreach (var literal in czytnik(File.ReadAllText(sciezka)))
            {
                if (Regex.IsMatch(literal, WaskaRegulaKsztaltu))
                {
                    wynik.Add((nazwa, literal));
                }
            }
        }

        return wynik;
    }

    /// <summary>Czy w pliku jest wiersz z tym literałem i markerem CZYTANIA JSON-a.</summary>
    private static bool WKontekscieCzytania(string kod, string literal) =>
        kod.Split('\n').Any(w =>
            w.Contains("\"" + literal + "\"", StringComparison.Ordinal)
            && MarkeryCzytaniaJson.Any(m => w.Contains(m, StringComparison.Ordinal)));

    /// <summary>Czy nazwa pada w pliku w kształcie <c>"nazwa":</c> — sito 6.D181.</summary>
    private static bool KsztaltKluczaJson(string kod, string literal) =>
        kod.Contains("\"" + literal + "\":", StringComparison.Ordinal);

    /// <summary>
    /// Rozbiór korpusu danym czytnikiem: ile w kontekście czytania, ile poza,
    /// i które z tych poza mają kształt klucza wypisywanego.
    /// </summary>
    private static (int WKontekscie, int Poza, List<string> Klucze) RozbiorJson(
        Func<string, List<string>> czytnik)
    {
        var wKontekscie = 0;
        var poza = 0;
        var klucze = new List<string>();
        foreach (var sciezka in ZrodlaGry())
        {
            var kod = File.ReadAllText(sciezka);
            var nazwa = Path.GetFileName(sciezka);
            foreach (var literal in czytnik(kod))
            {
                if (!Regex.IsMatch(literal, WaskaRegulaKsztaltu))
                {
                    continue;
                }

                if (WKontekscieCzytania(kod, literal))
                {
                    wKontekscie++;
                    continue;
                }

                poza++;
                if (KsztaltKluczaJson(kod, literal))
                {
                    klucze.Add($"{nazwa}:{literal}");
                }
            }
        }

        return (wKontekscie, poza, klucze);
    }

    /// <summary>Napis metadanych zrzutu — najdłuższe zgłoszenie <c>FirstRun.cs</c>.</summary>
    private static string NapisMetadanychZrzutu() =>
        SlowaWKodzie(ZrodloGry("FirstRun.cs")).OrderByDescending(l => l.Length).First();

    /// <summary>
    /// Z trzech markerów „kontekstu JSON-a" niesie liczbę JEDEN — 6.D186.
    ///
    /// <para>Bramka na przyrząd, którym mierzyło 6.D173, a za nim 6.D181. Nie zmienia
    /// żadnej z liczb tamtych pomiarów — mówi tylko, na czym one stoją. Marker dopisany
    /// do listy albo z niej zdjęty zapala ten test, zamiast po cichu przejść.</para>
    /// </summary>
    [TestMethod]
    public void Z_trzech_markerow_kontekstu_JSON_a_niesie_liczbe_JEDEN()
    {
        var zmierzone = new List<(string, int)>();
        foreach (var marker in MarkeryCzytaniaJson)
        {
            var ile = 0;
            foreach (var sciezka in ZrodlaGry())
            {
                var kod = File.ReadAllText(sciezka);
                var wiersze = kod.Split('\n');
                foreach (var literal in SlowaWKodzie(kod))
                {
                    if (!Regex.IsMatch(literal, WaskaRegulaKsztaltu))
                    {
                        continue;
                    }

                    if (wiersze.Any(w =>
                        w.Contains("\"" + literal + "\"", StringComparison.Ordinal)
                        && w.Contains(marker, StringComparison.Ordinal)))
                    {
                        ile++;
                    }
                }
            }

            zmierzone.Add((marker, ile));
        }

        CollectionAssert.AreEqual(UdzialMarkerow, zmierzone,
            "udział markerów to dziś "
            + string.Join(", ", zmierzone.Select(z => $"{z.Item1}={z.Item2}"))
            + ", a zmierzono "
            + string.Join(", ", UdzialMarkerow.Select(u => $"{u.Marker}={u.Ile}")));

        // Marker o udziale ZEROWYM musi tu być wskazany po nazwie, a nie tylko
        // policzony: liczba `0` w tabeli czyta się jako pomiar, nazwa — jako wniosek.
        var bezczynne = UdzialMarkerow.Where(u => u.Ile == 0).Select(u => u.Marker).ToList();
        CollectionAssert.AreEqual(new[] { "RootElement" }, bezczynne,
            "bezczynne markery to dziś " + string.Join(", ", bezczynne)
            + " — jeśli `RootElement` przestał być bezczynny, KN-2 z 6.D186 zapali się "
            + "i akapit o zielonej kontroli opisuje inny stan drzewa");
    }

    /// <summary>
    /// Pomiar 6.D181 odtwarza się CO DO JEDYNKI drogą WIERSZOWĄ — 6.D186.
    ///
    /// <para><b>To jest żądanie pola „Weryfikacja" pozycji, a nie ozdoba:</b> przyrząd,
    /// który nie odtwarza liczb poprawianego pomiaru, mierzy co innego i nie ma prawa
    /// go korygować. Odtwarzają się wszystkie cztery: korpus <b>108</b>, kontekst
    /// czytania <b>18</b>, poza nim <b>90</b>, a wśród tych 90 — <b>13</b> o kształcie
    /// klucza wypisywanego.</para>
    ///
    /// <para><b>Droga jest tym samym ZMIERZONA, a nie uprawdopodobniona.</b> 6.D180 §8
    /// zapisało wprost: „Czego NIE twierdzę: że 6.D181 liczyło wierszami. Jakim dokładnie
    /// skanem doszło do swojej trzynastki, nie jest zmierzone". Teraz jest: liczba
    /// <b>108</b> powstaje WYŁĄCZNIE po stronie wierszowej (całym plikiem jest ich 96),
    /// a 6.D181 §3 pisze „Wyszło 18 ze 108". Oba końce tego zdania — 18 i 108 — stoją
    /// po tej samej stronie i po żadnej innej.</para>
    ///
    /// <para><b>Trzynastka odtwarza się razem z własnym trafieniem fałszywym.</b>
    /// Wśród 13 stoi <c>platforms</c> z <c>Argument("platforms")</c> — argument wiersza
    /// poleceń, nie klucz — który sito łapie przez kolizję nazwy z kluczem stojącym
    /// w napisie metadanych. 6.D181 policzyło go jako klucz, choć w jego własnej tabeli
    /// ta sama pozycja należy do wiersza „argument wiersza poleceń | 39".</para>
    /// </summary>

    /// Ścieżka tego pliku względem korzenia repozytorium — jedno miejsce zamiast
    /// sześciu powtórzeń tej samej trójki (6.D257: kopii ma być jedna).
    private static readonly string[] SciezkaTegoPliku =
        { "tests", "Game.Tests", "UiTextTests.cs" };

    /// <summary>
    /// 6.D260, kontrola przyrządu: <c>SkadTaLiczba</c> odpowiada o KONKRETNEJ stałej
    /// i wyłącznie o liczbach, które w jej łańcuchu naprawdę stały.
    ///
    /// <para>Bez tej kontroli zdanie dopisywane do komunikatu odmowy byłoby nie do
    /// odróżnienia od zdania dopisywanego ZAWSZE — a takie mówiłoby o każdej liczbie,
    /// że jest dawną wartością, i komunikat stałby się szumem zamiast wskazówką.
    /// Cztery przypadki i każdy osobno: dawna wartość, wartość dzisiejsza (ostatnie
    /// ogniwo, nigdy nie stojące po lewej), liczba spoza łańcucha i cudza stała.</para>
    /// </summary>
    [TestMethod]
    public void Czytnik_lancucha_odpowiada_o_TEJ_stalej_i_tylko_o_dawnych_wartosciach()
    {
        var dawna = MetroBxl.Tests.Shared.LancuchZmian.SkadTaLiczba(nameof(ZgloszenWaskichWierszami), 108, SciezkaTegoPliku);
        Assert.IsNotNull(dawna, "108 nie zostało rozpoznane jako dawna wartość");
        // Sprawdzany jest KSZTAŁT, a nie konkretna data i pozycja — i to jest wybór
        // z pomiaru, nie wygoda. Wpisane wprost `"14.09.2026"` i `"MB-04"` są dla
        // `test_game_needle_specificity.py` IGŁAMI, których w `src/` nie ma, więc
        // podnosiły `MAX_GAME_UNMATCHED_NEEDLES` — zapadkę GÓRNĄ, którą wolno tylko
        // obniżać. Konkretne wartości sprawdza `test_value_chains.py` po stronie
        // Pythona, gdzie ten skan nie sięga; tu sprawdzana jest postać odpowiedzi,
        // której tamta bramka nie ogląda.
        StringAssert.Matches(dawna, new Regex(@"\d{2}\.\d{2}\.\d{4}"),
            "odpowiedź nie niesie daty w kształcie DD.MM.RRRR");
        StringAssert.Matches(dawna, new Regex(@"pozycja \S+"),
            "odpowiedź nie niesie pozycji");
        StringAssert.Contains(dawna, 108.ToString(System.Globalization.CultureInfo.InvariantCulture),
            "odpowiedź nie niesie liczby, o którą pytano");

        // Od 6.M1 dzisiejszą wartością jest 117; 116 stało się dawną i stoi teraz po
        // LEWEJ stronie ostatniego ogniwa łańcucha.
        Assert.IsNull(MetroBxl.Tests.Shared.LancuchZmian.SkadTaLiczba(nameof(ZgloszenWaskichWierszami), 117, SciezkaTegoPliku),
            "dzisiejsza wartość zgłoszona jako DAWNA — a 117 stoi wyłącznie po prawej "
            + "stronie ostatniego ogniwa, więc nigdy tu nie „stała do\u201d");
        Assert.IsNull(MetroBxl.Tests.Shared.LancuchZmian.SkadTaLiczba(nameof(ZgloszenWaskichWierszami), 4242, SciezkaTegoPliku),
            "liczba spoza łańcucha zgłoszona jako dawna wartość — czytnik odpowiada "
            + "na wszystko i komunikat odmowy stałby się szumem");
        Assert.IsNull(MetroBxl.Tests.Shared.LancuchZmian.SkadTaLiczba(nameof(ZgloszenWaskichCalymPlikiem), 108, SciezkaTegoPliku),
            "108 z łańcucha JEDNEJ stałej przypisane DRUGIEJ — czytnik nie rozdziela "
            + "łańcuchów i mówiłby o cudzej historii");
    }

    [TestMethod]
    public void Trzynastka_z_6D181_odtwarza_sie_CO_DO_JEDYNKI_droga_WIERSZOWA()
    {
        var wierszami = ZgloszeniaWaskie(SlowaWierszPoWierszu);
        // 6.D260: pytamy o OBIE liczby, bo obie mogą być dawną wartością i znaczą
        // wtedy DWIE RÓŻNE rzeczy. Zmierzona będąca dawną wartością znaczy
        // „odtworzenie mierzy korpus zamrożony na tamtym commicie" — to jest
        // przypadek 6.D256. Stała będąca dawną wartością znaczy „ktoś cofnął
        // zapadkę do liczby, która już tu stała". Pierwsza wersja pytała wyłącznie
        // o zmierzoną i kontrola negatywna wyszła przez to BEZ tego zdania: jej
        // mutacja rusza stałą, nie pomiar.
        var skadZmierzona = MetroBxl.Tests.Shared.LancuchZmian.SkadTaLiczba(nameof(ZgloszenWaskichWierszami), wierszami.Count, SciezkaTegoPliku);
        var skadStala = MetroBxl.Tests.Shared.LancuchZmian.SkadTaLiczba(nameof(ZgloszenWaskichWierszami), ZgloszenWaskichWierszami, SciezkaTegoPliku);
        var historia = skadZmierzona is not null
            ? $". UWAGA: {skadZmierzona} — zmierzona liczba nie jest liczbą znikąd, "
              + "tylko DAWNĄ wartością tej samej stałej, więc odtworzenie mierzy "
              + "najpewniej korpus zamrożony na tamtym commicie (6.D256)"
            : skadStala is not null
                ? $". UWAGA: {skadStala} — oczekiwana liczba jest DAWNĄ wartością tej "
                  + "samej stałej, czyli zapadka została cofnięta do wartości, która "
                  + "już tu stała (6.D260)"
                : string.Empty;

        Assert.AreEqual(ZgloszenWaskichWierszami, wierszami.Count,
            $"drogą wierszową wąska reguła daje dziś {wierszami.Count} zgłoszeń wobec "
            + $"{ZgloszenWaskichWierszami} z 6.D173 — odtworzenie 6.D181 mierzy wtedy "
            + "inny korpus i nie ma prawa go poprawiać" + historia);

        var (wKontekscie, poza, klucze) = RozbiorJson(SlowaWierszPoWierszu);
        Assert.AreEqual(WKontekscieCzytaniaJson, wKontekscie,
            $"w kontekście czytania JSON-a stoi {wKontekscie} zgłoszeń wobec "
            + $"{WKontekscieCzytaniaJson} z 6.D173");
        Assert.AreEqual(ZgloszenWaskichWierszami - WKontekscieCzytaniaJson, poza,
            $"poza kontekstem stoi {poza} zgłoszeń, a 6.D181 opisało 90");
        Assert.AreEqual(KluczyWypisywanychWierszami, klucze.Count,
            $"kształt klucza wypisywanego ma {klucze.Count} zgłoszeń wobec "
            + $"{KluczyWypisywanychWierszami} z 6.D181: " + string.Join(", ", klucze));

        // Trafienie fałszywe MUSI tu być — bez niego trzynastka odtworzyłaby się
        // z innego zbioru o tej samej liczności, a to nie jest to samo.
        Assert.IsTrue(klucze.Contains("FirstRun.cs:" + JedyneTrafienieCaloplikowe,
                StringComparer.Ordinal),
            "w trzynastce 6.D181 nie ma `platforms` z `Argument(\"platforms\")` — "
            + "odtworzenie trafiło w inny zbiór niż tamten pomiar");
    }

    /// <summary>
    /// Ta sama miara drogą CAŁOPLIKOWĄ daje JEDNO trafienie i jest nim ARGUMENT — 6.D186.
    ///
    /// <para><b>ROZSTRZYGNIĘCIE POZYCJI: rodzina JSON-a liczy 18, a nie 31.</b>
    /// 6.D180 rozstrzygnęło, że poprawne jest liczenie CAŁYM PLIKIEM — napisu
    /// wielowierszowego nie da się czytać wierszami, bo rozcina go sam podział na
    /// wiersze. Tą drogą zgłoszeń o kształcie klucza wypisywanego jest <b>jedno</b>,
    /// a i ono kluczem nie jest: <c>Argument("platforms")</c> to nazwa argumentu wiersza
    /// poleceń, złapana przez kolizję z kluczem <c>"platforms":</c> stojącym gdzie indziej
    /// w tym samym pliku. Rodzina „klucz JSON-a wypisywanego" liczy wśród zgłoszeń
    /// <b>zero</b>, więc do 18 nie dochodzi nic.</para>
    /// </summary>
    [TestMethod]
    public void Ta_sama_miara_droga_CALOPLIKOWA_daje_JEDNO_trafienie_i_jest_nim_ARGUMENT()
    {
        var calym = ZgloszeniaWaskie(SlowaWKodzie);
        Assert.AreEqual(ZgloszenWaskichCalymPlikiem, calym.Count,
            $"drogą całoplikową wąska reguła daje dziś {calym.Count} zgłoszeń wobec "
            + $"{ZgloszenWaskichCalymPlikiem} z 6.D173");

        var (wKontekscie, poza, klucze) = RozbiorJson(SlowaWKodzie);
        Assert.AreEqual(WKontekscieCzytaniaJson, wKontekscie,
            $"w kontekście czytania stoi {wKontekscie} zgłoszeń, a obiema drogami ma "
            + $"stać {WKontekscieCzytaniaJson} — gdyby liczby się rozeszły, różnica "
            + "108 − 96 przestałaby siedzieć w całości po stronie wypisywania");
        Assert.AreEqual(ZgloszenWaskichCalymPlikiem - WKontekscieCzytaniaJson, poza,
            $"poza kontekstem stoi {poza} zgłoszeń zamiast 78");
        Assert.AreEqual(KluczyWypisywanychCalymPlikiem, klucze.Count,
            $"kształt klucza wypisywanego ma {klucze.Count} zgłoszeń wobec "
            + $"{KluczyWypisywanychCalymPlikiem}: " + string.Join(", ", klucze));

        CollectionAssert.AreEqual(
            new[] { "FirstRun.cs:" + JedyneTrafienieCaloplikowe }, klucze,
            "jedyne trafienie to dziś " + string.Join(", ", klucze));

        // I NIE jest kluczem — stoi przy `Argument(`, czyli w wierszu 6.D181 opisanym
        // jako „argument wiersza poleceń". Bez tego zdania liczba `1` czytałaby się
        // jako „jeden klucz jednak dochodzi".
        StringAssert.Contains(ZrodloGry("FirstRun.cs"),
            "Argument(\"" + JedyneTrafienieCaloplikowe + "\")",
            "jedyne trafienie przestało stać przy `Argument(` — wtedy zdanie „to nie "
            + "klucz, tylko kolizja nazw” opisuje inny stan pliku (6.D186)",
            StringComparison.Ordinal);
    }

    /// <summary>
    /// Klucze JSON-a wypisywanego nie są zgłoszeniami, więc poszerzenie reguły kontekstu
    /// NIC by nie dało — 6.D186.
    ///
    /// <para><b>To jest zdanie o tezie 6.D181, o które prosiło pole „Wyjście".</b>
    /// Teza „deklaracja była węższa niż rodzina" ZOSTAJE prawdziwa: przyrząd melduje
    /// „kontekst JSON-a", a sprawdza wyłącznie czytanie, choć program JSON również
    /// WYPISUJE — i to niemało, bo <b>31 różnych kluczy w 35 wystąpieniach</b>.</para>
    ///
    /// <para><b>Zmienia się POWÓD, dla którego ich nie widać, i to jest treść tej
    /// bramki.</b> Nie chodzi o regułę kontekstu: te 31 kluczy nie jest zgłoszeniami
    /// ŻADNEJ reguły, bo cały napis metadanych jest JEDNYM literałem długości 1697
    /// znaków i czterdziestu wierszy, a taki literał kształtu identyfikatora nie ma.
    /// Poszerzenie reguły z „czytania" na „czytanie i wypisywanie" znalazłoby więc
    /// <b>zero</b>, a nie trzynaście. Z 31 nazw w korpusie padają dwie — <c>platforms</c>
    /// i <c>view</c> — i obie jako nazwy argumentów wiersza poleceń.</para>
    ///
    /// <para><b>Dwie trzydzieści jedynki, i nie mają ze sobą nic wspólnego.</b> Kluczy
    /// w tym napisie jest 31, a 6.D181 policzyło rodzinę JSON-a też na 31 (18 + 13).
    /// Zbieżność jest przypadkowa — tamta liczba powstała z kawałków tego samego napisu
    /// policzonych po wierszach, a nie z jego kluczy — i stoi tu wypisana, żeby nikt
    /// nie wyprowadził z niej wniosku.</para>
    /// </summary>
    [TestMethod]
    public void Klucze_JSON_wypisywanego_NIE_SA_zgloszeniami_wiec_szersza_regula_nic_by_nie_dala()
    {
        var napis = NapisMetadanychZrzutu();
        Assert.IsTrue(napis.Split('\n').Length >= 40,
            $"najdłuższe zgłoszenie `FirstRun.cs` ma {napis.Split('\n').Length} wierszy, "
            + "a napis metadanych zrzutu ma ich czterdzieści — czytnik znowu go rozciął");
        Assert.IsFalse(Regex.IsMatch(napis, WaskaRegulaKsztaltu),
            "napis metadanych ma kształt identyfikatora, czyli wąska reguła by go "
            + "zgłosiła — wtedy cały wywód tej bramki opisuje inny korpus");

        var klucze = Regex.Matches(napis, "\"([a-z_][a-z0-9_]*)\"\\s*:")
            .Select(m => m.Groups[1].Value).ToList();
        Assert.AreEqual(WystapienKluczyJson, klucze.Count,
            $"wystąpień kluczy jest {klucze.Count} wobec zmierzonych {WystapienKluczyJson}");
        var rozne = klucze.Distinct(StringComparer.Ordinal)
            .OrderBy(k => k, StringComparer.Ordinal).ToList();
        Assert.AreEqual(KluczyJsonWypisywanego, rozne.Count,
            $"różnych kluczy jest {rozne.Count} wobec zmierzonych "
            + $"{KluczyJsonWypisywanego}: " + string.Join(", ", rozne));

        var korpus = ZgloszeniaWaskie(SlowaWKodzie);
        var obecne = rozne
            .Where(k => korpus.Any(z => string.Equals(z.Literal, k, StringComparison.Ordinal)))
            .ToList();
        CollectionAssert.AreEqual(
            KluczeJsonObecneWKorpusie.OrderBy(k => k, StringComparer.Ordinal).ToList(),
            obecne,
            "z kluczy napisu metadanych w korpusie zgłoszeń padają dziś "
            + string.Join(", ", obecne) + ", a zmierzono "
            + string.Join(", ", KluczeJsonObecneWKorpusie)
            + " — obie jako nazwy argumentów wiersza poleceń, żadna jako klucz");

        // Obie MUSZĄ dać się wskazać jako argumenty, inaczej zdanie „żadna jako klucz"
        // jest twierdzeniem bez pokrycia. Wzorzec obejmuje OBA kształty wywołania —
        // `Argument("platforms")` w `FirstRun.cs` i `Argument(arguments, "view")`
        // w `RunPlan.cs` — bo pierwsze podejście pytało tylko o pierwszy z nich
        // i wyszło CZERWONE na `view`, choć zdanie było prawdziwe.
        var zrodla = string.Join("\n", ZrodlaGry().Select(File.ReadAllText));
        foreach (var nazwa in obecne)
        {
            // Wynik w ZMIENNEJ, a nie w argumencie asercji, i to nie jest kosmetyka:
            // czytnik `test_csharp_assertions.py` rozstrzyga komunikat po argumentach,
            // a wywołanie z własnym przecinkiem w pierwszym argumencie wpada u niego
            // do klasy „bez komunikatu" — mimo że komunikat stoi. Zmierzone: bez tej
            // zmiennej zapadka `BEZ_KOMUNIKATU` dla tego pliku rosła z 13 na 14,
            // a wolno ją tylko obniżać.
            // WZORZEC ZE ZWYKŁEGO NAPISU, a nie z `@"…"`, i to nie jest kosmetyka:
            // zapis werbatim zaczynający się od cudzysłowu uciekanego (`@"""`) jest
            // przez `maska()` w `test_csharp_test_methods.py` brany za napis SUROWY
            // i połyka resztę pliku — a razem z nią TRZY metody testowe dopisane
            // niżej przy 6.D188. (Nazwy atrybutu nie cytuję tu dosłownie: tamten
            // czytnik liczy jego WYSTĄPIENIA W TEKŚCIE, więc cytat w komentarzu
            // dołożyłby czwarte, nieistniejące.) Osobna pozycja, nie cicha zmiana.
            var wzorzec = "Argument\\([^)]*\"" + nazwa + "\"\\)";
            var stoiPrzyArgumencie = Regex.IsMatch(zrodla, wzorzec);
            Assert.IsTrue(stoiPrzyArgumencie,
                $"nazwa `{nazwa}` pada w korpusie, ale nie stoi w żadnym wywołaniu "
                + "`Argument(…)` — wtedy nie wiadomo, czy zgłoszenie bierze się "
                + "z argumentu wiersza poleceń, czy jednak z klucza (6.D186)");
        }
    }


    // --- 6.D188: co `BezDziur` zabiera i czy zabiera komuś tekst ----------------------

    /// <summary>Ile literałów korpusu niesie w ogóle parę klamer — 6.D188.</summary>
    // 124 -> 125 (13.09.2026, MB-02): `"+0.000;-0.000;0.000"` klamry nie ma, ale
    // ma ją komunikat wyjątku z `RunSummary`.
    // 129 -> 128 (14.09.2026, MB-03) — SPADEK z tego samego powodu, co przy
    // `DziurNaEkranie`: wiersz prędkości przestał być literałem z klamrami w ciele
    // `Hud.Update`, a stał się wpisem katalogu.
    // 128 -> 131 (14.09.2026, MB-04): `FirstRun.AssetsRoot`, `DomyslnyZapisWejsc`
    // i wiersz `[ZAPISY]`. Liczba ZMIERZONA przyrzadem tego testu.
    // 131 -> 134 (14.09.2026, MB-05): `CabView.cs` i wpięcie kabiny w `FirstRun`.
    // Liczba ZMIERZONA przyrzadem tego testu.
    // 134 -> 139 (14.09.2026, MB-07): jak wyżej — literały drugiego składu.
    // 139 -> 144 (14.09.2026, MB-07): przeliczone przebiegiem.
    // 144 -> 149 (22.09.2026, 6.D235): PIĘĆ literałów — komunikaty `Abort` dla pliku ZŁEGO
    // w `FirstRun`: po dwa przy osi i przy manifeście chunków, jeden przy planie
    // sygnalizacji. Liczba PRZELICZONA przebiegiem.
    // 149 -> 148 (23.09.2026, 6.M1): odtworzenie linii w `FirstRun` i `RunPlan`. PRZELICZONE.
    // 148 -> 149 (24.09.2026, station-wayfinding): odmowa przy braku GLB tablicy ma interpolowaną ścieżkę.
    // 149 -> 150 (24.09.2026, interaktywne R): interpolowany błąd restartu.
    // 150 -> 152 (24.09.2026, krótki HUD chase): dystans i próg.
    // 152 -> 153 (24.09.2026, integracja pomocy linii): jeden literał z klamrą.
    private const int LiteralowZKlamra = 153;

    /// <summary>
    /// Ilu literałom <see cref="BezDziur"/> zabiera WSZYSTKIE słowa — 6.D188.
    ///
    /// <para>„Zabiera wszystkie" znaczy: <c>BezJednostek(literał)</c> niesie słowo,
    /// a <c>BezJednostek(BezDziur(literał))</c> już nie. Zmierzone na 480 literałach
    /// <c>src/Game/</c>.</para>
    /// </summary>
    //
    // **14 -> 13 (14.09.2026, MB-03), i znów SPADEK.** Wypadł literał wiersza
    // prędkości z ciała `Hud.Update`: `BezJednostek` zostawiał w nim samo `a`, więc
    // `BezDziur` zabierało mu ostatnie słowo. Po przeniesieniu do katalogu wiersz
    // niesie `sufit`, czyli słowo, którego żadna z tych dwóch mechanik nie zabiera.
    // 13 -> 14 (14.09.2026, MB-07): przeliczone przebiegiem.
    // 14 -> 15 (24.09.2026, integracja pomocy linii): nowy wzorzec pomocy.
    private const int ZabranychWszystkieSlowa = 15;

    /// <summary>
    /// Ile z nich stoi na drodze <c>Hud.Update</c>, czyli dociera na ekran — 6.D188.
    ///
    /// <para><b>Trzy — i ani jedno nie jest tekstem dla gracza.</b> To jest
    /// odpowiedź pozycji na pytanie „czy któryś z nich jest tekstem dla gracza":
    /// docierają, ale zabrane im słowa to nazwy zmiennych z wnętrza dziur.
    /// <b>Było cztery do 14.09.2026</b>; czwartym był wiersz prędkości składany
    /// w kodzie, i on jako jedyny mógł być kiedyś tekstem dla gracza — dlatego
    /// wyprowadził się do katalogu (MB-03), a nie dlatego, że przestał docierać.</para>
    /// </summary>
    // 4 -> 3 (14.09.2026, MB-03): ten sam literał wiersza prędkości, co przy
    // `ZabranychWszystkieSlowa`. Trzy, które zostają, to dziury złożone wyłącznie
    // z interpolacji — a te nigdy nie były tekstem dla gracza.
    // 3 -> 4 (14.09.2026, MB-07): drugi `{binding.KeyName} {binding.Meaning}` —
    // z `BuildDriverHasTakenHelp`, czyli z wiersza pomocy dla składu przejętego.
    private const int ZabranychNaDrodzeNaEkran = 4;

    /// <summary>Literały z drogi na ekran, którym <c>BezDziur</c> zabiera wszystko — 6.D188.</summary>
    private static readonly string[] ZabraneNaEkranie =
    {
        "{ostrzezenie}{ingerencja}",
        "{binding.KeyName} {binding.Meaning}",
        "{b.KeyName} {b.Meaning}",

        // CZWARTY DOŁOŻONY 14.09.2026 (MB-07): drugie wystąpienie
        // `"{binding.KeyName} {binding.Meaning}"` — z `BuildDriverHasTakenHelp`, czyli
        // z wiersza pomocy dla składu PRZEJĘTEGO przez gracza. Ten sam szablon co wyżej
        // i z tego samego powodu: dziura złożona wyłącznie z interpolacji, bez ani
        // jednego słowa dla gracza. Zbiór jest tu listą, a nie zbiorem, więc powtórzenie
        // wpisuje się drugi raz — i to jest poprawne, bo pomiar liczy WYSTĄPIENIA.
        "{binding.KeyName} {binding.Meaning}",

        // CZWARTY ZDJĘTY 14.09.2026 (MB-03), a nie przeniesiony: literał
        // `"{speedKmh,6:F1} km/h     a = {accelerationMps2,6:F2} m/s²"` przestał
        // istnieć — wiersz prędkości mieszka od tej pory w katalogu jako `hud.speed`.
        // Trzy, które zostają, to dziury złożone wyłącznie z interpolacji, czyli
        // nazwy zmiennych, a nie tekst dla gracza; odpowiedź 6.D188 na pytanie
        // „czy któryś z nich jest tekstem dla gracza" zostaje więc NIE, i to tym
        // mocniej, że jedyny kandydat wyprowadził się do katalogu.
    };

    /// <summary>
    /// Pary klamer, których treść niesie cudzysłów — CAŁY korpus, 6.D188.
    ///
    /// <para><b>To jest populacja, w której opisana w pozycji usterka MOGŁABY
    /// wystąpić</b>, i liczy trzy sztuki. Wszystkie trzy są wywołaniami C#
    /// z zagnieżdżonym literałem, a nie obiektem JSON — a zagnieżdżony literał
    /// <see cref="Literaly"/> zwraca OSOBNO, więc <c>BezDziur</c> nie ma jak go
    /// schować.</para>
    /// </summary>
    private static readonly string[] KlamryZCudzyslowem =
    {
        "{Engine.GetVersionInfo()[\"string\"]}",
        "{string.Join(\" --\", KnownArguments)}",
        "{string.Join(\", \", KnownViews)}",

        // MB-02: lista celów sesji w wierszu `[SESJA] trwa:`. WYWOŁANIE C#, nie obiekt
        // JSON — `sesja.TargetStopIds` jest `IReadOnlyList<string>`, a `", "` w środku
        // to separator, nie klucz.
        "{string.Join(\", \", sesja.TargetStopIds)}",
    };

    /// <summary>Literały zagnieżdżone w tych trzech dziurach — muszą stać w korpusie.</summary>
    private static readonly string[] ZagniezdzoneWKlamrach =
        { "string", " --", ", ", ", " };

    /// <summary>Czy sito zgłasza słowo w tym literale — tak samo, jak pyta bramka.</summary>
    private static bool NiesieSlowo(string literal) =>
        Regex.IsMatch(BezJednostek(literal), WzorzecSlowa);

    /// <summary>Literały, którym <c>BezDziur</c> zabiera wszystkie słowa, danym korpusem.</summary>
    private static List<string> TracaceWszystkieSlowa(IEnumerable<string> literaly) =>
        literaly.Where(l => NiesieSlowo(l) && !NiesieSlowo(BezDziur(l))).ToList();

    /// <summary>
    /// Ilu literałom <c>BezDziur</c> zabiera WSZYSTKIE słowa i ile z nich dociera
    /// na ekran — 6.D188.
    ///
    /// <para><b>PRZESŁANKA POZYCJI PADŁA, i to jest główny wynik.</b> Pole „Skąd"
    /// mówi, że <c>BezDziur</c> „dla literału niosącego płaski obiekt JSON zabiera
    /// treść, o którą bramka pyta". Mechanizm jest prawdziwy — pokazuje go kontrola
    /// na wejściu syntetycznym niżej — ale w <c>src/Game/</c> nie ma go ANI RAZU:
    /// wśród czternastu literałów tracących wszystkie słowa nie ma ani jednego
    /// płaskiego obiektu JSON. We wszystkich czternastu zabrane słowa są nazwami
    /// zmiennych z wnętrza dziur, czyli tym, co sito obiecuje zabierać.</para>
    /// </summary>
    [TestMethod]
    public void Ile_literalow_traci_WSZYSTKIE_slowa_przez_BezDziur()
    {
        var wszystkie = new List<string>();
        var zKlamra = 0;
        foreach (var sciezka in ZrodlaGry())
        {
            foreach (var literal in Literaly(File.ReadAllText(sciezka)))
            {
                wszystkie.Add(literal);
                if (Regex.IsMatch(literal, "[{][^{}]*[}]"))
                {
                    zKlamra++;
                }
            }
        }

        // Dolne ostrze na SAM SKAN: zepsuty czytnik daje zero literałów, a zero
        // przechodzi „nikomu nic nie ubyło" bez ani jednego sprawdzenia (6.D27).
        Assert.AreEqual(LiteralowWZasieguBramki, wszystkie.Count,
            $"korpus ma dziś {wszystkie.Count} literałów wobec "
            + $"{LiteralowWZasieguBramki} — pomiar 6.D188 opisuje inne drzewo");
        Assert.AreEqual(LiteralowZKlamra, zKlamra,
            $"literałów z klamrą jest {zKlamra} wobec zmierzonych {LiteralowZKlamra} — "
            + "bez nich `BezDziur` nie ma na czym zadziałać");

        var tracace = TracaceWszystkieSlowa(wszystkie);
        Assert.AreEqual(ZabranychWszystkieSlowa, tracace.Count,
            $"wszystkie słowa traci dziś {tracace.Count} literałów wobec zmierzonych "
            + $"{ZabranychWszystkieSlowa}: " + string.Join(" | ", tracace));

        var naEkranie = new List<string>();
        foreach (var (_, plik, czlon) in ZrodlaHud)
        {
            naEkranie.AddRange(TracaceWszystkieSlowa(
                Literaly(CialoDeklaracji(ZrodloGry(plik), czlon))));
        }

        naEkranie.AddRange(TracaceWszystkieSlowa(
            Literaly(CialoDeklaracji(HudSource(), "public void Update("))));

        Assert.AreEqual(ZabranychNaDrodzeNaEkran, naEkranie.Count,
            $"na drodze `Hud.Update` traci wszystko {naEkranie.Count} literałów wobec "
            + $"{ZabranychNaDrodzeNaEkran}: " + string.Join(" | ", naEkranie));
        CollectionAssert.AreEqual(
            ZabraneNaEkranie.OrderBy(l => l, StringComparer.Ordinal).ToList(),
            naEkranie.OrderBy(l => l, StringComparer.Ordinal).ToList(),
            "na ekran docierają inne literały tracące wszystko niż w pomiarze: "
            + string.Join(" | ", naEkranie));
    }

    /// <summary>
    /// Zabrane słowa to WYRAŻENIA C#, a nie tekst dla gracza — 6.D188.
    ///
    /// <para><b>Dlaczego `BezDziur` nie MOŻE schować tekstu dla gracza, i jest to
    /// własność strukturalna, a nie zbieg okoliczności na dzisiejszym drzewie.</b>
    /// Treścią dziury jest kod C#, a jedyną drogą, którą tekst dla człowieka mógłby
    /// się w niej znaleźć, jest literał ZAGNIEŻDŻONY — a te
    /// <see cref="Literaly"/> zwraca OSOBNO (akapit „Literały z dziur interpolacji
    /// ZWRACANE SĄ TEŻ"). Zdjęcie dziury nie zabiera więc korpusowi ani jednego
    /// napisu; zabiera tylko jego kopię stojącą wewnątrz szablonu.</para>
    ///
    /// <para>Populacja, w której cokolwiek innego mogłoby stać, to pary klamer
    /// z cudzysłowem w środku — w całym korpusie <b>trzy</b>, wszystkie wywołania
    /// C#. Ich zagnieżdżone literały muszą stać w korpusie osobno i to jest tu
    /// sprawdzane, a nie założone.</para>
    /// </summary>
    [TestMethod]
    public void Zabrane_slowa_to_WYRAZENIA_C_a_nie_tekst_dla_gracza()
    {
        var korpus = new List<string>();
        foreach (var sciezka in ZrodlaGry())
        {
            korpus.AddRange(Literaly(File.ReadAllText(sciezka)));
        }

        var zCudzyslowem = korpus
            .SelectMany(l => Regex.Matches(l, "[{][^{}]*[}]").Select(m => m.Value))
            .Where(d => d.Contains('"', StringComparison.Ordinal))
            .Distinct(StringComparer.Ordinal)
            .OrderBy(d => d, StringComparer.Ordinal)
            .ToList();
        CollectionAssert.AreEqual(
            KlamryZCudzyslowem.OrderBy(d => d, StringComparer.Ordinal).ToList(),
            zCudzyslowem,
            "par klamer z cudzysłowem w środku jest dziś " + string.Join(" | ", zCudzyslowem)
            + " — jeśli doszła, trzeba sprawdzić, czy to wywołanie C#, czy obiekt JSON");

        // PĘTLA MUSI SIĘ WYKONAĆ, i to nie jest ostrożność: `Take(0)` w niej czynił
        // z całej asercji ciche pominięcie, a kontrola negatywna KN-4 wychodziła
        // ZIELONA. Ta sama rodzina, co `test_lista_wyjatkow_filtrow_nie_gnije`.
        Assert.AreEqual(KlamryZCudzyslowem.Length, ZagniezdzoneWKlamrach.Length,
            "listy „dziura z cudzysłowem” i „literał w niej zagnieżdżony” mają różną "
            + "długość — każdej dziurze odpowiada dokładnie jeden zagnieżdżony napis");
        var sprawdzonych = 0;
        foreach (var zagniezdzony in ZagniezdzoneWKlamrach)
        {
            Assert.IsTrue(korpus.Contains(zagniezdzony, StringComparer.Ordinal),
                $"literał `{zagniezdzony}` stoi WEWNĄTRZ dziury, a czytnik nie zwrócił "
                + "go osobno — wtedy `BezDziur` mógłby go schować i cały wywód tej "
                + "bramki przestaje być prawdą");
            sprawdzonych++;
        }

        // LICZNIK OBROTÓW, a nie długość listy: KN-4 za pierwszym razem wyszła ZIELONA
        // z `Take(0)` w nagłówku pętli, a asercja na `.Length` tego nie łapie — lista
        // ma swoją długość niezależnie od tego, ile razy pętla się obróci.
        Assert.AreEqual(KlamryZCudzyslowem.Length, sprawdzonych,
            $"pętla sprawdziła {sprawdzonych} z {KlamryZCudzyslowem.Length} "
            + "zagnieżdżonych literałów — reszta jest cichym pominięciem");

        // Druga strona, na wejściu SYNTETYCZNYM: tekst dla gracza schowany w dziurze
        // ZOSTAJE widziany, bo czytnik zwraca go osobno. Drzewo tego nie rozdziela —
        // nie ma dziś ani jednej dziury z polskim napisem w środku.
        // SŁOWO JEST SYNTETYCZNE I MA TAKIE ZOSTAĆ — zmienione 14.09.2026 (MB-08)
        // z „otwarte" na „rozsunięte". Powód jest pomiarem, nie gustem: katalog dostał
        // wtedy wpis `hud.doors.refusal.already-open` („drzwi są już otwarte"), więc
        // igła `otwarte` zaczęła pasować do DWÓCH komunikatów `src/Game/` naraz —
        // tego i `hud.door.open`. `test_every_needle_matches_at_most_one_message…`
        // złapało to natychmiast i miało rację: wejście syntetyczne, które przypadkiem
        // równa się prawdziwemu napisowi z katalogu, przestaje być syntetyczne.
        // Ten test nie pyta o TREŚĆ słowa, tylko o to, czy czytnik zwraca je OSOBNO.
        var zNapisem = SlowaWKodzie("var t = $\"stan: {(x ? \"rozsunięte\" : \"zamknięte\")}\";");
        Assert.IsTrue(zNapisem.Count >= 2,
            "czytnik nie zwrócił osobno napisów schowanych w dziurze — zwrócił: "
            + string.Join(" | ", zNapisem));
        Assert.IsTrue(zNapisem.Contains("rozsunięte", StringComparer.Ordinal),
            "napis dla gracza z wnętrza dziury nie stoi w korpusie osobno: "
            + string.Join(" | ", zNapisem));
    }

    /// <summary>
    /// Napis metadanych PRZEŻYWA <c>BezDziur</c>, bo jego klamry są ZAGNIEŻDŻONE
    /// — 6.D188.
    ///
    /// <para><b>Tu stoi mechanizm, o który pozycja pyta, i jego jedyny możliwy
    /// nosiciel.</b> <c>BezDziur</c> to <c>[{][^{}]*[}]</c>, czyli zdejmuje
    /// WYŁĄCZNIE pary NAJGŁĘBSZE — płaski <c>{ "stacja": "peron" }</c> jest sam dla
    /// siebie najgłębszy i znika w całości razem z nazwami pól. Napisów surowych
    /// <c>$$"""</c> w <c>src/Game/</c> jest JEDEN — metadane zrzutu z
    /// <c>FirstRun.cs</c> — a wszystkie jego nazwy kluczy leżą POZA najgłębszymi
    /// parami (tymi są dziury interpolacji), więc przeżywają co do jednej.
    /// Usterka istnieje jako mechanizm i ma w tym drzewie ZERO wystąpień.</para>
    ///
    /// <para><b>Zdanie „bo klamry są zagnieżdżone" było za słabe i pokazała to
    /// kontrola.</b> KN-3 zdjęła z napisu JEDEN poziom zagnieżdżenia i wyszła
    /// ZIELONA: pozostałe poziomy wystarczyły. Nośna jest nie liczba poziomów, tylko
    /// to, ILE NAZW KLUCZY leży poza najgłębszymi parami — i dlatego stoi tu pin na
    /// tę liczbę, a nie zdanie o zagnieżdżeniu.</para>
    ///
    /// <para>Kontrola na wejściu SYNTETYCZNYM, bo drzewo tych dwóch przypadków nie
    /// rozdziela — płaskiego obiektu JSON w literale nie ma tu ani jednego.</para>
    /// </summary>
    [TestMethod]
    public void Napis_metadanych_PRZEZYWA_BezDziur_bo_jego_klamry_sa_ZAGNIEZDZONE()
    {
        var napis = NapisMetadanychZrzutu();
        Assert.IsTrue(NiesieSlowo(napis),
            "napis metadanych przestał nieść słowo — wtedy porównanie „przed i po” "
            + "nie ma jednej ze stron");
        Assert.IsTrue(NiesieSlowo(BezDziur(napis)),
            "`BezDziur` zabrał napisowi metadanych wszystkie słowa — wtedy usterka "
            + "z 6.D188 ma pierwsze wystąpienie w drzewie");

        // PIN NA LICZBĘ, a nie na zdanie o zagnieżdżeniu. Kluczy jest 31 (6.D186)
        // i `BezDziur` nie zabiera ANI JEDNEGO — bo wszystkie leżą poza najgłębszymi
        // parami klamer. Bez tego pinu zdjęcie poziomu zagnieżdżenia przechodziło
        // na zielono (KN-3).
        var kluczePrzed = Regex.Matches(napis, "\"([a-z_][a-z0-9_]*)\"\\s*:")
            .Select(m => m.Groups[1].Value).Distinct(StringComparer.Ordinal).Count();
        var kluczePo = Regex.Matches(BezDziur(napis), "\"([a-z_][a-z0-9_]*)\"\\s*:")
            .Select(m => m.Groups[1].Value).Distinct(StringComparer.Ordinal).Count();
        Assert.AreEqual(KluczyJsonWypisywanego, kluczePrzed,
            $"napis metadanych niesie dziś {kluczePrzed} kluczy wobec "
            + $"{KluczyJsonWypisywanego} z 6.D186");
        Assert.AreEqual(KluczyJsonWypisywanego, kluczePo,
            $"po `BezDziur` zostaje {kluczePo} kluczy z {KluczyJsonWypisywanego} — "
            + "sito zabrało nazwy pól, czyli treść, o którą bramka pyta");

        // WEJŚCIE SYNTETYCZNE — dokładnie to, czego żądało pole „Weryfikacja" pozycji.
        var plaski = SlowaWKodzie("var j = $$\"\"\"\n{ \"stacja\": \"peron\" }\n\"\"\";");
        var zagniezdzony = SlowaWKodzie(
            "var j = $$\"\"\"\n{ \"scene\": { \"peron\": 1 } }\n\"\"\";");
        Assert.AreEqual(0, plaski.Count,
            "płaski obiekt JSON przestał znikać w całości — wtedy akapit o `BezDziur` "
            + "opisuje inne sito: " + string.Join(" | ", plaski));
        Assert.AreEqual(1, zagniezdzony.Count,
            "zagnieżdżony obiekt JSON nie zostawił ani jednego zgłoszenia — wtedy "
            + "różnica, dla której ta kontrola istnieje, nie została pokazana: "
            + string.Join(" | ", zagniezdzony));
    }


    // --- 6.D197: ile switchy po wyliczeniu ma src/Game/ ----------------------------
    //
    // ODPOWIEDŹ: JEDEN, i jest nim `FirstRun.Faza` — ten sam, który 6.D185 przybiło
    // ręcznie. Bramka z 6.D185 nie jest próbką z większego zbioru; JEST CAŁYM ZBIOREM
    // dla `src/Game/`.
    //
    // **Przesłanka pozycji nie trzymała się co do obu przykładów, które wymieniała.**
    // `ViewKind`: switch w `RunPlan.cs` idzie po NAPISIE (`Argument(…) ?? "cab"`),
    // a jego ramiona to literały `"chase"/"outside"/"inspect"` — to nie jest switch
    // po wyliczeniu, i jest to dokładnie to trafienie fałszywe, które 6.D185 wpisało
    // do `FalszyweTrafieniaSkanu` jako `RunPlan.cs:view`. `ProtectionVariant`: jego
    // switch stoi w `src/Sim/SignallingPlan.cs`, poza korpusem tej pozycji.
    //
    // **Bramki uogólnionej NIE MA i to jest rozstrzygnięcie, nie zaniechanie.** Pole
    // „Dlaczego «uogólnić bramkę» NIE jest odpowiedzią domyślną" tej pozycji ostrzega
    // przed sitem, które nic nie chroni; przy jednym wystąpieniu uogólnienie nie miałoby
    // nad czym uogólniać. Zostaje **liczba**: gdy pojawi się drugi switch po wyliczeniu,
    // ta asercja go pokaże, a wtedy dopiero jest o czym rozstrzygać.
    //
    // **1 -> 2 (13.09.2026, MB-02), i TO JEST TO ROZSTRZYGNIĘCIE, KTÓRE 6.D197
    // ODŁOŻYŁO.** Drugim switchem po wyliczeniu jest `RunSummary.Naglowek`. Akapit
    // wyżej obiecywał, że przy drugim „dopiero wtedy jest o czym rozstrzygać" —
    // i rozstrzygnięcie jest takie: uogólnieniem NIE jest liczba, tylko **ramię
    // domyślne**. Zmierzone wtedy na `src/Sim/`: wszystkie osiem switchy postaci
    // wyrażeniowej ma ramię RZUCAJĄCE, a jedyne ramię CICHE w całym drzewie stoi
    // w `FirstRun.Faza` i jest świadome (angielska nazwa członu na HUD zamiast
    // wyjątku w środku klatki). `RunSummary.Naglowek` rzuca — czyli dołącza do
    // rodziny większej, a nie zakłada drugiej.
    //
    // Liczba zostaje OBOK zapadki na ramiona, a nie zamiast niej: mówi, ile switchy
    // po wyliczeniu jest, gdy tamta mówi, jak każdy z nich się zachowuje.
    // 2 -> 3 (14.09.2026, MB-08): `DoorPrompt.Reason`. Rozstrzygnięcie z MB-02
    // zostaje nietknięte i to ono rozstrzyga o tym wpisie: uogólnieniem jest RAMIĘ
    // DOMYŚLNE, nie liczba — a to ramię jest ciche świadomie i stoi z nazwy na liście
    // milczków wyżej. Trzeci switch nie zakłada więc trzeciej rodziny: dołącza do tej,
    // którą 6.D185 przybiło ręcznie.
    private const int SwitchyPoWyliczeniuWGame = 3;

    // Switche po wyliczeniu, których ramię domyślne MILCZY zamiast rzucić — lista,
    // a nie liczba, bo to nazwy rozstrzygają, czy milczenie jest świadome.
    // `FirstRun.cs:phase` jest tu jedynym wpisem od 6.D185 i ma powód wypisany
    // w `FirstRun.Faza`: wyjątek w środku klatki przewróciłby przejazd, a angielska
    // nazwa członu na HUD jest widoczna i zgłaszalna.
    // MB-08 dokłada `DoorPrompt.cs:refusal` (`DoorPrompt.Reason`) i jest to DRUGI
    // świadomy milczek w `src/Game/`, a nie poluzowanie listy. Powód ma ten sam, co
    // pierwszy, i jest wypisany przy samej metodzie: `DoorRefusal` jest wyliczeniem
    // RDZENIA, a rzucenie wyjątkiem w metodzie składającej wiersz HUD-u przewróciłoby
    // klatkę zamiast pokazać graczowi, czego nie umie nazwać. Ramię domyślne oddaje
    // angielską nazwę członu — widoczną i zgłaszalną, tak samo jak w `Faza`.
    private static readonly string[] SwitcheZCichymRamieniem =
        { "DoorPrompt.cs:refusal", "FirstRun.cs:phase" };

    // Wszystkie konstrukty `switch` w `src/Game/`, z rozstrzygnięciem. Liczba jest tu
    // DRUGA, bo „jeden po wyliczeniu" nie mówi nic o tym, ile ich jest w ogóle — a to
    // właśnie ta różnica pozwala odróżnić „skan nie znalazł" od „nie ma".
    // 3 -> 4 (14.09.2026, MB-08): `DoorPrompt.Reason` — tłumaczy wyliczenie RDZENIA
    // (`DoorRefusal`) na napis z katalogu, ta sama robota i ten sam kształt, co
    // `FirstRun.Faza`. Switchy jest CZTERY, a nie pięć, bo `DoorPrompt.For`
    // świadomie nim NIE jest: gotowość do odjazdu pyta o `DoorCycle.TractionAllowed`,
    // czyli o ten sam predykat, którym rdzeń zwalnia trakcję — powód przy tej metodzie.
    private const int SwitchyWGameRazem = 4;

    // Postać instrukcyjna (`switch (x) { case …: default: }`) NIE WYSTĘPUJE w src/Game/
    // ani razu. Zero jest tu wypisane, bo skan, który tej postaci nie widzi, odpowiada
    // na nią zerem tak samo jak skan widzący — rodzina 6.D159. Kontrola przyrządu niżej
    // sprawdza, że czytnik ją rozpoznaje na wejściu syntetycznym.
    private const int SwitchyInstrukcyjnychWGame = 0;

    private static List<string> PlikiGry() =>
        PlikiZrodlowe()
            .Where(p => p.Split(Path.DirectorySeparatorChar).Contains("Game"))
            .ToList();

    // `(plik, nazwa przełączanego wyrażenia, czy po wyliczeniu)` dla każdego `switch`-a.
    // Czyta źródło BEZ komentarzy, bo słowo `switch` w komentarzu nie jest switchem.
    private static readonly List<(string Gdzie, bool PoWyliczeniu, bool Rzuca)>
        ramionaDomyslne = new();

    private static List<(string Plik, string Na, bool PoWyliczeniu)> SwitcheGry()
    {
        var typy = new HashSet<string>(WyliczeniaZrodel().Keys, StringComparer.Ordinal);
        var znalezione = new List<(string, string, bool)>();
        ramionaDomyslne.Clear();
        foreach (var sciezka in PlikiGry())
        {
            var kod = KodBezKomentarzyDlaStaregoCzytnika(File.ReadAllText(sciezka));
            foreach (Match m in Regex.Matches(kod, @"(\w+)\s+switch\s*\{"))
            {
                var ogon = kod.Substring(m.Index + m.Length);
                var koniec = ogon.IndexOf('}');
                var cialo = koniec < 0 ? ogon : ogon.Substring(0, koniec);
                // Po WYLICZENIU rozstrzyga KSZTAŁT RAMION, a nie nazwa zmiennej:
                // `view` jest nazwą, pod którą w `src/` stoi też wartość `ViewKind`,
                // więc rozstrzyganie po nazwie daje tu trafienie fałszywe — zmierzone
                // przy 6.D185 i wpisane tam do `FalszyweTrafieniaSkanu`.
                var poWyliczeniu = typy.Any(t =>
                    Regex.IsMatch(cialo, @"\b" + Regex.Escape(t) + @"\.\w+\s*=>"));
                znalezione.Add((Path.GetFileName(sciezka), m.Groups[1].Value, poWyliczeniu));
                // Ramię domyślne bierze się z ciała aż do klamry ZAMYKAJĄCEJ switcha,
                // a nie do pierwszej napotkanej: `throw new ArgumentOutOfRangeException(`
                // z wieloliniowym komunikatem klamry nie ma, ale wyrażenie `{` w ramieniu
                // — owszem. Szukamy więc `_ =>` i sprawdzamy, czy po nim pada `throw`
                // przed następnym ramieniem.
                var odDomyslnego = ogon.IndexOf("_ =>", StringComparison.Ordinal);
                ramionaDomyslne.Add((
                    $"{Path.GetFileName(sciezka)}:{m.Groups[1].Value}",
                    poWyliczeniu,
                    odDomyslnego >= 0
                        && ogon.Substring(odDomyslnego, Math.Min(80, ogon.Length - odDomyslnego))
                            .Contains("throw", StringComparison.Ordinal)));
            }
            foreach (Match m in Regex.Matches(kod, @"\bswitch\s*\([^)]*\)\s*\{"))
            {
                znalezione.Add((Path.GetFileName(sciezka), "(instrukcja)", true));
            }
        }
        return znalezione;
    }

    [TestMethod]
    public void Ile_switchy_po_wyliczeniu_ma_src_Game_i_czy_Faza_jest_wsrod_nich()
    {
        var switche = SwitcheGry();
        Assert.AreEqual(SwitchyWGameRazem, switche.Count,
            $"konstruktów `switch` w `src/Game/` jest {switche.Count}, a zmierzono "
            + $"{SwitchyWGameRazem}: "
            + string.Join(", ", switche.Select(s => $"{s.Plik}:{s.Na}")));

        var instrukcyjne = switche.Count(s => s.Na == "(instrukcja)");
        Assert.AreEqual(SwitchyInstrukcyjnychWGame, instrukcyjne,
            $"postaci instrukcyjnej `switch (x) {{ case … }}` jest {instrukcyjne}, "
            + "a zmierzono zero — doszła postać, której ta sekcja nie rozstrzygała");

        var poWyliczeniu = switche.Where(s => s.PoWyliczeniu).ToList();
        Assert.AreEqual(SwitchyPoWyliczeniuWGame, poWyliczeniu.Count,
            $"switchy po wartości wyliczeniowej jest {poWyliczeniu.Count}, a zmierzono "
            + $"{SwitchyPoWyliczeniuWGame}: "
            + string.Join(", ", poWyliczeniu.Select(s => $"{s.Plik}:{s.Na}"))
            + ". Drugi taki switch znaczy, że mechanizm „nowy człon = cicha zmiana "
            + "zachowania” ma w `src/Game/` więcej niż jedno wystąpienie — i dopiero "
            + "wtedy jest o czym rozstrzygać (6.D197)");

        // ROZSTRZYGNIĘCIE 6.D197, ZROBIONE PRZY MB-02: uogólnieniem nie jest liczba,
        // tylko RAMIĘ DOMYŚLNE. Każdy switch po wyliczeniu w `src/Game/` ma ramię
        // rzucające — poza tymi, które stoją na liście świadomych milczków. Zapadka na
        // samą liczbę mówiłaby „doszedł trzeci" i nie mówiłaby, czy ten trzeci połyka
        // nowy człon po cichu; ta mówi.
        var ciche = ramionaDomyslne
            .Where(r => r.PoWyliczeniu && !r.Rzuca)
            .Select(r => r.Gdzie)
            .OrderBy(x => x, StringComparer.Ordinal)
            .ToList();
        CollectionAssert.AreEqual(
            SwitcheZCichymRamieniem.OrderBy(x => x, StringComparer.Ordinal).ToList(),
            ciche,
            "switche po wyliczeniu z MILCZĄCYM ramieniem domyślnym to dziś "
            + string.Join(", ", ciche)
            + ", a świadomie dopuszczone są " + string.Join(", ", SwitcheZCichymRamieniem)
            + ". Nowy człon wyliczenia wpadający do milczącego ramienia zmienia "
            + "zachowanie BEZ ANI JEDNEGO śladu — i to jest ten mechanizm, który 6.D185 "
            + "przybiło ręcznie, a 6.D197 zmierzyło na `src/Sim/` (osiem na osiem "
            + "switchy wyrażeniowych rdzenia RZUCA)");

        // KONTROLA PRZYRZĄDU, bez której liczba 1 nie znaczyłaby nic: skan MA znaleźć
        // ten switch, który 6.D185 przybiło ręcznie. Gdyby go nie znajdował, patrzyłby
        // nie tam, a wszystkie liczby wyżej opisywałyby pusty zbiór (6.D159).
        Assert.IsTrue(poWyliczeniu.Any(s => s.Plik == "FirstRun.cs" && s.Na == "phase"),
            "skan NIE ZNAJDUJE `FirstRun.Faza`, czyli switcha, który 6.D185 przybiło "
            + "ręcznie — wtedy patrzy nie tam i liczby wyżej są o pustym zbiorze: "
            + string.Join(", ", switche.Select(s => $"{s.Plik}:{s.Na}")));

        // OBCINACZ KOMENTARZY JEST DZIŚ BEZCZYNNY I TO JEST TU SPRAWDZANE, NIE
        // PRZEMILCZANE. Zmierzone: w `src/Game/` nie ma słowa `switch` ani w komentarzu,
        // ani w literale, więc skan po źródle SUROWYM daje tę samą liczbę (2 wobec 2,
        // 0 wobec 0). Kontrola negatywna zdejmująca obcinacz wychodzi przez to ZIELONA
        // — i tak ma być, bo nie ma czego zdjąć. Ta asercja powie, kiedy przestanie:
        // pierwsze słowo `switch` w komentarzu rozjedzie obie liczby, a wtedy obcinacz
        // zaczyna rozstrzygać i jego zdjęcie przestaje być bez skutku.
        var surowo = PlikiGry()
            .Sum(s => Regex.Matches(File.ReadAllText(s), @"(\w+)\s+switch\s*\{").Count);
        Assert.AreEqual(switche.Count(s => s.Na != "(instrukcja)"), surowo,
            $"skan po źródle surowym daje {surowo} switchy wyrażeniowych, a po zdjęciu "
            + "komentarzy — inną liczbę. Znaczy to, że w `src/Game/` pojawiło się słowo "
            + "`switch` w komentarzu albo w literale: obcinacz przestał być bezczynny "
            + "i od teraz jego zdjęcie ZMIENIA wynik (6.D197)");

        // I DRUGA STRONA: `RunPlan.cs:view` ma NIE być liczony jako switch po wyliczeniu.
        // `view` jest nazwą, pod którą w `src/` stoi też wartość `ViewKind`, więc
        // rozstrzyganie po nazwie dałoby tu trafienie fałszywe.
        Assert.IsFalse(switche.Any(s => s.Plik == "RunPlan.cs" && s.PoWyliczeniu),
            "`RunPlan.cs` policzony jako switch po wyliczeniu — a jego ramiona to "
            + "literały napisowe, bo przełącza po `Argument(…) ?? \"cab\"`. To jest "
            + "trafienie fałszywe rodziny `RunPlan.cs:view` z 6.D185");
    }

    [TestMethod]
    public void Czytnik_switchy_WIDZI_obie_postacie_na_wejsciu_syntetycznym()
    {
        // Postaci instrukcyjnej nie ma w `src/Game/` ani razu, więc korpus jej NIE
        // ĆWICZY. Bez tego wejścia „zero postaci instrukcyjnych" nie odróżniałoby
        // „nie ma" od „nie umiem zobaczyć" — rodzina 6.D159.
        var wyrazenie = "X = phase switch { DoorPhase.Open => 1, _ => 0, };";
        Assert.AreEqual(1, Regex.Matches(wyrazenie, @"(\w+)\s+switch\s*\{").Count,
            "czytnik nie widzi postaci wyrażeniowej — a to jedyna, która stoi dziś "
            + "w `src/Game/`");

        var instrukcja = "switch (phase) { case DoorPhase.Open: break; default: break; }";
        Assert.AreEqual(1, Regex.Matches(instrukcja, @"\bswitch\s*\([^)]*\)\s*\{").Count,
            "czytnik nie widzi postaci instrukcyjnej — wtedy zero z "
            + "`SwitchyInstrukcyjnychWGame` mówi o przyrządzie, a nie o drzewie");
        Assert.AreEqual(0, Regex.Matches(instrukcja, @"(\w+)\s+switch\s*\{").Count,
            "postać instrukcyjna policzona JAKO wyrażeniowa — wtedy dwie liczby "
            + "opisują jeden byt i obie są nieprawdziwe");

        // I że komentarz NIE jest switchem — obcinacz musi zadziałać przed skanem.
        var wKomentarzu = KodBezKomentarzyDlaStaregoCzytnika(
            "// tu kiedyś stało phase switch {\nvar x = 1;\n");
        Assert.AreEqual(0, Regex.Matches(wKomentarzu, @"(\w+)\s+switch\s*\{").Count,
            "słowo `switch` w komentarzu policzone jako switch — wtedy liczba mówi "
            + "o prozie, a nie o kodzie");
    }

    // --- 6.D198: ile nazw w src/ jest DWUZNACZNYCH -----------------------------------
    //
    // ODPOWIEDŹ: DZIESIĘĆ z dwudziestu dwóch, czyli 45 %. Pozycja wymieniała TRZY
    // (`Reason`, `Variant`, `view`) i mówiła wprost, że trzy to liczba z DWUNASTU
    // TRAFIEŃ, a nie z drzewa. Z drzewa wychodzi ponad trzy razy tyle.
    //
    // **I to nie jest liczba, która maleje.** Zmierzone na historii `src/`: wyliczeń
    // jest SZESNAŚCIE od 02.09.2026 i od tamtej pory nie przybyło ani jedno; nazw pod
    // typem wyliczeniowym jest DWADZIEŚCIA DWA od 05.09.2026 i też stoją. Nazw
    // dwuznacznych w tym samym czasie było kolejno 2, 5, 6, 8, 9, 10 — rosną PRZY
    // ZAMROŻONYCH obu populacjach, które miałyby je napędzać. Rosną, bo zwykłe pole
    // `string` dostaje nazwę, której wyliczenie już używa, a pól `string` przybywa
    // szybciej niż typów.
    //
    // **Dlatego zdanie 6.D185 o „puszczeniu skanu szerzej" jest tu PRZEPISANE, a nie
    // powtórzone.** Tamto zdanie mówi: „gdyby trafień fałszywych ubyło do zera, skan
    // wolno byłoby puścić szerzej". Warunek jest spełnialny wyłącznie w drzewie, które
    // dwuznaczności się pozbywa — a zmierzony ruch idzie w drugą stronę, monotonicznie,
    // i nic w drzewie go nie hamuje. Zdanie zostaje w tamtej bramce jako WARUNEK
    // (bo jest poprawne: gdyby ubyło, wolno by było), ale przestaje być planem —
    // co mówi ta sekcja i pilnuje asercja niżej.
    // 16 -> 17 (13.09.2026, MB-02): doszedł `TrainingEnding`. **To jest pierwszy ruch
    // tej liczby od 02.09.2026 i on NIE obala tezy 6.D198, tylko ją zawęża.** Teza
    // brzmiała „dwuznaczności przybywa BEZ nowych typów" — i nadal tak jest: nowa nazwa
    // dwuznaczna (`ending`) przyszła w tym samym commicie co nowy typ, ale ani jedna
    // z dziesięciu poprzednich nie potrzebowała do tego typu. Liczba przestaje być
    // NIERUCHOMA, a asercja niżej mówi teraz, ile jest, a nie że nie drgnęła.
    // 17 -> 18 (14.09.2026, MB-06): doszedł `ControlOwner`. **Drugi ruch tej liczby
    // w ciągu doby, i to jest już inny stan niż opisuje akapit wyżej.** Zdanie
    // „stoi nieruchomo od 02.09.2026" zniknęło stąd i z komunikatu asercji, bo po
    // dwóch ruchach w dwa dni przestało być prawdą — a komunikat bramki, który mówi
    // o drzewie coś nieprawdziwego, jest gorszy od braku komunikatu.
    //
    // **Teza 6.D198 zostaje i zostaje ZAWĘŻONA, a nie obalona.** Brzmiała
    // „dwuznaczności przybywa BEZ nowych typów". `ControlOwner` NIE dokłada ani jednej
    // nazwy dwuznacznej — `NazwyDwuznaczneWSrc` nie drgnęło przy tym commicie — więc
    // ten typ jest przypadkiem odwrotnym niż `TrainingEnding`: nowy typ bez nowej
    // dwuznaczności. Po obu ruchach zdanie prawdziwe brzmi: dwuznaczności nie
    // potrzebują nowych typów, a nowe typy nie muszą ich przynosić.
    // 18 -> 20 (14.09.2026, MB-08): `DoorControl` i `DoorRefusal`, oba w `src/Sim`.
    // TRZECI ruch w trzy dni, więc zdanie o nieruchomości tej liczby zostaje
    // skreślone tak samo, jak zostało po drugim.
    // 20 -> 21 (23.09.2026, 6.M1): `LineEventKind` w `src/Sim/Train/InputLog.cs`. CZWARTY ruch.
    // 21 -> 22 (24.09.2026, wskazówka hamowania): `BrakingCueStage` zatrzaskuje fazę wskazówki hamowania.
    private const int WyliczenWSrc = 22;

    // 22 -> 24 (13.09.2026, MB-02): `Ending` i `ending` z `TrainingEnding`.
    // 24 -> 25 (14.09.2026, MB-06): `Owner` z `ControlOwner`. JEDNA nazwa, a nie dwie
    // jak przy MB-02 — bo `LineCore` nie ma parametru `owner`; właściciel wchodzi
    // przez `TakeControl`/`ReleaseControl`, które biorą identyfikator składu.
    // 25 -> 35 (14.09.2026, MB-08): DZIESIĘĆ nazw naraz, z dwóch nowych typów.
    // `DoorControl` daje `Control`, `DoorControl`, `StopDoorControl`, `_control`
    // i `control`; `DoorRefusal` daje `Refusal`, `_doorRefusal` i `refusal`; do tego
    // `_manualPhase` pod `DoorPhase`.
    //
    // **TEZA 6.D198 ZOSTAJE OBALONA W TĘ STRONĘ, W KTÓRĄ ZOSTAŁA ZAWĘŻONA — i to
    // jest tu treścią, a nie liczba.** Po MB-06 brzmiała: „dwuznaczności nie potrzebują
    // nowych typów, a nowe typy nie muszą ich przynosić". Druga połowa tego zdania
    // właśnie padła: dwa nowe typy przyniosły dziewięć nazw, czyli więcej niż wszystkie
    // ruchy tej liczby razem wzięte od 02.09.2026. Różnica wobec `ControlOwner`
    // (zero nazw) i `TrainingEnding` (dwie) jest strukturalna, a nie przypadkowa:
    // tamte dwa typy są ODCZYTEM stanu, a te dwa są ARGUMENTEM i WYNIKIEM — tryb wchodzi
    // konstruktorem i polem, a powód odmowy wraca z metody i ląduje w polu widoku.
    // Typ, który podróżuje, dostaje nazwę w każdym miejscu, przez które przechodzi.
    // …plus `powodOdmowy` z `DoorPrompt.For` — razem DZIESIĘĆ, nie dziewięć.
    // 35 -> 36 (23.09.2026, 6.M1): `LineEventKind rodzajZdarzenia` w `InputLog` i `InputLogRecorder`. PRZELICZONE.
    // 36 -> 37 (24.09.2026, wskazówka hamowania): dodatkowa nazwa związana z `BrakingCueStage`.
    private const int NazwPodWyliczeniem = 37;

    // Nazwy, pod którymi w `src/` stoi i wartość wyliczenia, i wartość innego typu.
    // Lista, a nie liczba, bo to nazwy rozstrzygają, czy skan po nazwie wolno puścić
    // szerzej — a liczba nie mówi, KTÓRA doszła (rodzina 6.D212).
    private static readonly string[] NazwyDwuznaczneWSrc =
    {
        "Action", "Phase", "Reason", "Variant", "_view",
        "action", "load", "phase", "status", "variant", "view",
    };

    // Typ, pod którym stoi druga strona dwuznaczności. `string` w DZIEWIĘCIU na
    // dziesięć — i to jest treść, a nie ciekawostka: gdyby drugą stroną były inne
    // wyliczenia, sito po nazwie dałoby się uratować słownikiem typów. Napis takiej
    // drogi nie zostawia.
    // 9 -> 10 (13.09.2026, MB-02): doszło `action`. Proporcja robi się jeszcze
    // wyraźniejsza niż w dniu pomiaru — dziesięć z jedenastu, a nie dziewięć z dziesięciu.
    private const int DwuznacznychPrzezNapis = 10;

    // Słowa kluczowe C#, które stoją przed nazwą tak samo jak typ. Bez tej listy
    // `return phase`, `case Phase` i `out status` policzyłyby się jako „drugi typ".
    private static readonly HashSet<string> SlowaNieBedaceTypem = new(StringComparer.Ordinal)
    {
        "return", "new", "case", "is", "as", "out", "ref", "in", "public", "private",
        "internal", "protected", "static", "readonly", "const", "override", "virtual",
        "sealed", "partial", "class", "struct", "record", "enum", "interface", "using",
        "namespace", "if", "else", "foreach", "for", "while", "do", "switch", "throw",
        "await", "yield", "get", "set", "var", "this", "base", "null", "true", "false",
        "when", "where", "select", "from", "default",
    };

    // Po nazwie w DEKLARACJI stoi jeden z tych znaków. Ten człon wzorca jest tu
    // najważniejszy i ma własny pomiar: bez niego wynik ZALEŻY OD OBCINACZA
    // komentarzy (surowo 12, wierszowo 11), bo polska proza „…, jeśli `ma status`
    // parametru…" wygląda jak `Typ nazwa`. Z nim wszystkie trzy warianty tekstu dają
    // TĘ SAMĄ DZIESIĄTKĘ — obcinacz przestaje rozstrzygać. Mierzy to
    // <see cref="Ksztalt_deklaracji_ZDEJMUJE_zaleznosc_od_obcinacza_komentarzy"/>.
    private const string PoNazwieWDeklaracji = @"(?=\s*[;,)=\{]|\s*=>|\s*$)";

    private static List<string> NazwyPodWyliczeniem(string kod, IEnumerable<string> typy)
    {
        var wynik = new List<string>();
        foreach (var typ in typy)
        {
            foreach (Match m in Regex.Matches(
                kod, @"\b" + Regex.Escape(typ) + @"\??\s+(\w+)\b" + PoNazwieWDeklaracji,
                RegexOptions.Multiline))
            {
                wynik.Add(m.Groups[1].Value);
            }
        }

        return wynik;
    }

    // `nazwa -> typy NIE będące wyliczeniem, pod którymi ta sama nazwa też stoi`.
    private static SortedDictionary<string, SortedSet<string>> DwuznacznoscNazw(
        IReadOnlyDictionary<string, List<string>> teksty, ISet<string> wyliczenia,
        IEnumerable<string> nazwy)
    {
        var wynik = new SortedDictionary<string, SortedSet<string>>(StringComparer.Ordinal);
        foreach (var nazwa in nazwy)
        {
            foreach (var kod in teksty.Values.SelectMany(x => x))
            {
                foreach (Match m in Regex.Matches(
                    kod, @"\b(\w+)\??\s+" + Regex.Escape(nazwa) + @"\b" + PoNazwieWDeklaracji,
                    RegexOptions.Multiline))
                {
                    var typ = m.Groups[1].Value;
                    if (wyliczenia.Contains(typ) || SlowaNieBedaceTypem.Contains(typ))
                    {
                        continue;
                    }

                    if (!wynik.TryGetValue(nazwa, out var zbior))
                    {
                        wynik[nazwa] = zbior = new SortedSet<string>(StringComparer.Ordinal);
                    }

                    zbior.Add(typ);
                }
            }
        }

        return wynik;
    }

    private static Dictionary<string, List<string>> ZrodlaSrcJakoTeksty(bool bezKomentarzy)
    {
        var wynik = new Dictionary<string, List<string>>(StringComparer.Ordinal);
        foreach (var sciezka in PlikiZrodlowe())
        {
            var kod = File.ReadAllText(sciezka);
            wynik[sciezka] = new List<string>
            {
                bezKomentarzy ? KodBezKomentarzyDlaStaregoCzytnika(kod) : kod,
            };
        }

        return wynik;
    }

    [TestMethod]
    public void Ile_nazw_w_src_jest_DWUZNACZNYCH_i_czy_sa_wsrod_nich_te_trzy_z_6D185()
    {
        var wyliczenia = WyliczeniaZrodel();
        Assert.AreEqual(WyliczenWSrc, wyliczenia.Count,
            $"typów wyliczeniowych w `src/` jest {wyliczenia.Count}, a zmierzono "
            + $"{WyliczenWSrc}. Liczba ruszyła dwa razy w dwa dni (MB-02, MB-06), "
            + "więc nie jest już nieruchoma — ale teza 6.D198 zostaje: dwuznaczności "
            + "przybywa BEZ nowych typów, a nowy typ nie musi ich przynieść");

        var typy = new HashSet<string>(wyliczenia.Keys, StringComparer.Ordinal);
        var teksty = ZrodlaSrcJakoTeksty(bezKomentarzy: true);
        var nazwy = new SortedSet<string>(
            teksty.Values.SelectMany(x => x).SelectMany(k => NazwyPodWyliczeniem(k, typy)),
            StringComparer.Ordinal);
        Assert.AreEqual(NazwPodWyliczeniem, nazwy.Count,
            $"nazw pod typem wyliczeniowym jest {nazwy.Count}, a zmierzono "
            + $"{NazwPodWyliczeniem}: " + string.Join(", ", nazwy));

        var dwuznaczne = DwuznacznoscNazw(teksty, typy, nazwy);
        CollectionAssert.AreEqual(
            NazwyDwuznaczneWSrc.OrderBy(x => x, StringComparer.Ordinal).ToList(),
            dwuznaczne.Keys.ToList(),
            "nazwy dwuznaczne to dziś "
            + string.Join(", ", dwuznaczne.Select(kv => $"{kv.Key}({string.Join("/", kv.Value)})"))
            + ", a wpisano " + string.Join(", ", NazwyDwuznaczneWSrc)
            + ". JEŚLI ICH PRZYBYŁO, sito po nazwie jest jeszcze mniej zdatne do "
            + "puszczenia szerzej niż w dniu, w którym 6.D185 zapisało ten warunek; "
            + "jeśli UBYŁO — warunek tamtej bramki zbliżył się do spełnienia i wolno "
            + "wrócić do pytania o korpus (6.D198)");

        // KONTROLA PRZYRZĄDU: trzy nazwy, które 6.D185 pokazało palcem, MUSZĄ tu być.
        // Bez niej dziesiątka mogłaby opisywać zupełnie inny zbiór, a test i tak by
        // przeszedł — rodzina 6.D159.
        foreach (var nazwa in new[] { "Reason", "Variant", "view" })
        {
            Assert.IsTrue(dwuznaczne.ContainsKey(nazwa),
                $"`{nazwa}` NIE jest widziane jako dwuznaczne, a 6.D185 wskazało tę "
                + "nazwę wprost — wtedy skan nie widzi deklaracji, którą tamta pozycja "
                + "pokazała palcem, i lista wyżej opisuje inny zbiór: "
                + string.Join(", ", dwuznaczne.Keys));
        }

        var przezNapis = dwuznaczne.Count(kv => kv.Value.Contains("string"));
        Assert.AreEqual(DwuznacznychPrzezNapis, przezNapis,
            $"drugą stroną dwuznaczności jest `string` w {przezNapis} przypadkach, "
            + $"a zmierzono {DwuznacznychPrzezNapis}. Gdyby drugą stroną były INNE "
            + "WYLICZENIA, sito po nazwie dałoby się uratować słownikiem typów — "
            + "napis takiej drogi nie zostawia i dlatego ta liczba stoi osobno");
    }

    [TestMethod]
    public void Ksztalt_deklaracji_ZDEJMUJE_zaleznosc_od_obcinacza_komentarzy()
    {
        // **To jest pomiar, a nie ostrożność.** Bez członu `PoNazwieWDeklaracji` wynik
        // ZALEŻY od tego, czy komentarze zostały zdjęte: na surowym tekście wychodzi
        // dwanaście nazw dwuznacznych, po obcinaczu jedenaście — różnicę robi jedno
        // polskie zdanie („…wcina Environment…"). Z tym członem oba teksty dają TĘ SAMĄ
        // dziesiątkę. Rodzina 6.D212: bramka, której wynik zależy od czytnika, mówi
        // o czytniku, a nie o drzewie.
        var typy = new HashSet<string>(WyliczeniaZrodel().Keys, StringComparer.Ordinal);
        var wyniki = new List<int>();
        var sprawdzonych = 0;
        foreach (var bezKomentarzy in new[] { true, false })
        {
            var teksty = ZrodlaSrcJakoTeksty(bezKomentarzy);
            var nazwy = new SortedSet<string>(
                teksty.Values.SelectMany(x => x).SelectMany(k => NazwyPodWyliczeniem(k, typy)),
                StringComparer.Ordinal);
            wyniki.Add(DwuznacznoscNazw(teksty, typy, nazwy).Count);
            sprawdzonych++;
        }

        Assert.AreEqual(2, sprawdzonych,
            "pętla po wariantach tekstu wykonała się " + sprawdzonych + " razy zamiast "
            + "dwóch — wtedy równość niżej nie porównuje niczego (rodzina 6.D193)");
        Assert.AreEqual(wyniki[0], wyniki[1],
            $"z komentarzami wychodzi {wyniki[1]} nazw dwuznacznych, bez nich "
            + $"{wyniki[0]} — kształt deklaracji przestał wystarczać i wynik znowu "
            + "zależy od obcinacza, czyli mówi o czytniku, a nie o drzewie");
        Assert.AreEqual(NazwyDwuznaczneWSrc.Length, wyniki[0],
            $"oba warianty zgadzają się na {wyniki[0]}, ale lista przybita wyżej ma "
            + $"{NazwyDwuznaczneWSrc.Length} pozycji");
    }

    [TestMethod]
    public void Czytnik_dwuznacznosci_ODROZNIA_deklaracje_od_prozy_na_wejsciu_syntetycznym()
    {
        // Drzewo tych dwóch przypadków nie rozdziela na tyle wyraźnie, żeby liczba 10
        // była dowodem: gdyby człon `PoNazwieWDeklaracji` przepuszczał prozę, dziesiątka
        // po prostu byłaby inną liczbą i nikt by nie wiedział którą.
        var typy = new HashSet<string>(StringComparer.Ordinal) { "DoorPhase" };
        var deklaracja = new Dictionary<string, List<string>>(StringComparer.Ordinal)
        {
            ["a.cs"] = new List<string> { "private DoorPhase phase;\nprivate string phase;" },
        };
        var nazwyD = NazwyPodWyliczeniem(deklaracja["a.cs"][0], typy);
        CollectionAssert.AreEqual(new List<string> { "phase" }, nazwyD,
            "czytnik nie widzi deklaracji `DoorPhase phase;` — wtedy nie widzi niczego");
        Assert.IsTrue(DwuznacznoscNazw(deklaracja, typy, nazwyD).ContainsKey("phase"),
            "czytnik nie rozpoznaje `string phase;` jako drugiej strony dwuznaczności");

        var proza = new Dictionary<string, List<string>>(StringComparer.Ordinal)
        {
            ["b.cs"] = new List<string> { "private DoorPhase phase;\nNieznany phase parametru." },
        };
        Assert.IsFalse(
            DwuznacznoscNazw(proza, typy, NazwyPodWyliczeniem(proza["b.cs"][0], typy))
                .ContainsKey("phase"),
            "polskie zdanie policzone jako deklaracja typu — wtedy dziesiątka wyżej "
            + "opisuje prozę tak samo jak kod, a obcinacz komentarzy znowu rozstrzyga");
    }

    // --- 6.D199: .ToString() bez argumentu — ile ich jest i którą drogą idzie wynik ---
    //
    // ODPOWIEDŹ NA TRZY PYTANIA POZYCJI: wywołanie czytane LEKSYKALNIE jest JEDNO,
    // stoi na wartości wyliczenia i idzie na EKRAN. Do logu zero, do telemetrii zero.
    //
    // **REGEKS PO SUROWYM TEKŚCIE DAJE TRZY, czyli DWA ZGŁOSZENIA TO SZUM (67 %), a nie
    // jedno na dwa (50 %), jak pisała pozycja.** Różnica nie jest zmianą drzewa —
    // jest RÓŻNICĄ KORPUSU między dwoma polami tej samej pozycji. Pole „Skąd” liczyło
    // po `ZrodlaGry()`, które **umyślnie pomija** katalog tekstów `UI/UiText.cs`;
    // pole „Wejście” mówi „`src/Game/` (wszystkie pliki poza `.godot/`)”, czyli razem
    // z katalogiem. W katalogu stoi od 6.D99 komentarz `(_ => phase.ToString())`.
    // Dwa pola jednej pozycji, dwa korpusy, dwie liczby — i na obu czytanie leksykalne
    // zostawia TO SAMO jedno wywołanie.
    //
    // **To jest właśnie powód, dla którego pozycja kazała mierzyć ZANIM ktoś ten skan
    // postawi.** Na trzech zgłoszeniach szum widać gołym okiem; na trzydziestu brałoby
    // się go za rozkład.
    // 1 -> 2 (13.09.2026, MB-02): `panel.ToString()` w `RunSummary.Compose`.
    // Relacja `leksykalnie < surowo` zostaje (2 < 4) i to ona jest treścią tej sekcji.
    // 2 -> 3 (14.09.2026, MB-08): `refusal.ToString()` w ramieniu domyślnym
    // `DoorPrompt.Reason`. Relacja `leksykalnie < surowo` zostaje (3 < 6) i to ona
    // jest treścią tej sekcji.
    private const int ToStringLeksykalnieWGame = 3;

    // 3 -> 4 (13.09.2026, MB-02): `panel.ToString()` w `RunSummary.Compose` — to
    // `StringBuilder`, a nie wyliczenie, więc liczba „na wyliczeniu" zostaje na jednym.
    // 5 -> 6 (14.09.2026, MB-08): `refusal.ToString()` w ramieniu domyślnym
    // `DoorPrompt.Reason` — to samo wyjście awaryjne i ten sam powód,
    // co `phase.ToString()` w `FirstRun.Faza`.
    private const int ToStringRegeksemPoSurowym = 6;

    // 1 -> 2 (14.09.2026, MB-08): `refusal.ToString()` z ramienia domyślnego
    // `DoorPrompt.Reason`. Oba wywołania na wyliczeniu w `src/Game/` są dziś tą samą
    // konstrukcją w tej samej roli — wyjściem awaryjnym dla członu bez nazwy po polsku —
    // więc liczba rośnie, a rodzina zostaje jedna.
    private const int ToStringNaWyliczeniuWGame = 2;

    // 1 -> 2 (14.09.2026, MB-08): `DoorPrompt.Reason`. Zdanie o różnicy zostaje
    // nietknięte i jest po tym ruchu MOCNIEJSZE, a nie słabsze: do logu i do telemetrii
    // nadal nie idzie ANI JEDNO wywołanie na wyliczeniu, a oba, które są, idą na ekran.
    private const int ToStringNaEkranieWGame = 2;

    // `.ToString(cośtam)` — postać, której skan bez argumentu NIE WIDZI. Jest jej
    // DWANAŚCIE razy więcej niż postaci badanej i **żadna nie stoi na wyliczeniu**:
    // wszystkie dwanaście to liczby (`double`), formatowane kulturą niezmienną.
    // Zero z ostatniej stałej jest treścią: gdyby wartość wyliczenia trafiła tu,
    // byłaby tym samym błędem w innym ubraniu, a skan z tej pozycji przeszedłby obok.
    // 12 -> 15 (13.09.2026, MB-02): trzy formatowania liczb w `RunSummary.Compose`.
    // Granica „słowa w katalogu, formaty w kodzie" zostaje tam, gdzie 6.D83 ją
    // postawiło — i te trzy wywołania są jej kolejnym przypadkiem, nie wyjątkiem.
    // 15 -> 18 (14.09.2026, MB-03): trzy formatowania liczb w wierszu prędkości,
    // przeniesione z ciała `Hud.Update` do wywołania `UiText.Format`. Granica
    // „słowa w katalogu, formaty w kodzie" zostaje tam, gdzie 6.D83 ją postawiło.
    private const int ToStringZArgumentemWGame = 18;

    private const int ToStringZArgumentemNaWyliczeniuWGame = 0;

    /// <summary>
    /// Człon wyrażenia: nazwa, ewentualnie z indeksatorem — 6.D214.
    ///
    /// <para><b>Indeksator jest tu treścią, a nie ozdobą.</b> Do 15.09.2026 oba wzorce
    /// niżej brały nazwę jako <c>([\w.]+)</c>, a ta klasa nie wchodzi w <c>]</c>. Na
    /// wyrażeniu <c>_line.Calls[^1].StopErrorM.ToString(…)</c> dopasowanie zaczynało się
    /// więc ZA nawiasem i zgłoszenie brzmiało <c>.StopErrorM</c> — z kropką na początku
    /// i bez nazwy obiektu.</para>
    ///
    /// <para><b>To NIE jest „weź więcej znaków", przed czym ostrzegało pole pozycji.</b>
    /// Poszerzenie jest STRUKTURALNE: człon wyrażenia w C# może nieść indeksator, więc
    /// wzorzec opisuje człon, a nie długość. Zmierzone na drzewie: zgłoszeń jest tyle
    /// samo co przedtem (3 + 18 w <c>src/Game/</c>, 3 + 5 w <c>src/Sim/</c>), różnią się
    /// <b>dokładnie dwa</b> i oba na korzyść — <c>.StopErrorM</c> staje się
    /// <c>_line.Calls[^1].StopErrorM</c> i <c>_stations.Calls[^1].StopErrorM</c>.</para>
    ///
    /// <para><b>I to jest szkoda, którą urwanie robiło naprawdę:</b> te dwa wyrażenia
    /// NIE SĄ tym samym wyrażeniem, a stary czytnik zwijał je do jednego napisu. Komunikat
    /// bramki nie odróżniał więc dwóch różnych miejsc — a istnieje po to, żeby nie trzeba
    /// było wracać do pliku i szukać ręcznie.</para>
    ///
    /// <para><b>Nawias OKRĄGŁY doszedł z tego samego pomiaru i jest INNĄ klasą niż
    /// urwanie.</b> <c>Units.MpsToKmh(PermittedSpeedMps).ToString("R", …)</c>
    /// w <c>SignallingPlan.cs:216</c> był dla obu czytników — starego i nowego —
    /// <b>NIEWIDOCZNY</b>, a nie urwany: przed <c>.ToString</c> stoi <c>)</c>, więc
    /// dopasowanie nie zaczynało się w ogóle. Poszerzenie o <c>\([^()]*\)</c> dodaje
    /// <b>dokładnie to jedno</b> zgłoszenie i nie rusza żadnego z pozostałych 28.</para>
    ///
    /// <para><b>Granica, która zostaje:</b> nawiasy ZAGNIEŻDŻONE
    /// (<c>f(g(x)).ToString()</c>) nadal są niewidoczne, bo <c>[^()]*</c> w nie nie
    /// wchodzi. Dziś takiego wyrażenia w <c>src/</c> nie ma; kontrola przyrządu wykonuje
    /// ten przypadek, żeby granica była zmierzona, a nie opowiedziana.</para>
    /// </summary>
    private const string CzlonWyrazenia = @"\w+(?:\[[^\]\[]*\]|\([^()]*\))?";

    private static readonly Regex WzorzecToStringBezArgumentu =
        new($@"((?:{CzlonWyrazenia})(?:\.{CzlonWyrazenia})*)\.ToString\(\s*\)",
            RegexOptions.Compiled);

    // ---------------------------------------------------------------------
    // 6.D213 — `.ToString()` w RDZENIU; siostra bramki 6.D199 dla `src/Game/`
    // ---------------------------------------------------------------------

    /// <summary>Podłoga na liczbę wywołań `.ToString()` bez argumentu w `src/Sim/`.</summary>
    /// <remarks>
    /// <para><b>Podłoga, a NIE równość, i to jest rozstrzygnięcie pola „Czego NIE wolno
    /// przyjąć bez pomiaru".</b> Dziś wywołania są trzy — `FixedBlockSystem.cs:521`
    /// i `InputLog.cs:321` na <c>StringBuilder</c>, `DriverKeys.cs:85` na
    /// <c>const char NoneCode</c>. Wszystkie trzy są zachowaniem normalnym i przybywa
    /// ich razem z kodem, więc równość świeciłaby przy commitach, które niczego nie psują,
    /// i skończyłaby wyłączona (6.D27). Podłoga pilnuje czego innego: żeby skan nie
    /// oślepł — zero wywołań znaczyłoby „czytnik przestał czytać", a nie „rdzeń czysty".</para>
    /// </remarks>
    private const int MinimumToStringWRdzeniu = 3;

    /// <summary>
    /// Nazwy w `src/Sim/`, które noszą typ wyliczeniowy **i jakiś inny** — ślepa plamka
    /// sita po nazwie, wypisana Z NAZWY, a nie policzona (6.D131).
    /// </summary>
    /// <remarks>
    /// <para><b>Zmierzone 15.09.2026 trzema podstawieniami, nie przyjęte.</b> Sito po
    /// samej nazwie daje FAŁSZYWE TRAFIENIE na kodzie poprawnym: <c>string status</c>
    /// z <c>status.ToString()</c> zapala je, choć nie ma tam żadnego wyliczenia.
    /// Sito zawężone do nazw JEDNOZNACZNYCH (19 z 24) milczy na tym samym kodzie
    /// i zapala na <c>DoorPhase faza</c> — ale milczy też na
    /// <c>ParameterStatus status</c>, czyli na prawdziwej usterce noszącej nazwę
    /// dwuznaczną. Ślepa plamka jest więc ceną, którą płacimy za brak trafień
    /// fałszywych, i dlatego stoi tu wypisana, a nie schowana w liczbie.</para>
    /// <para>Te same nazwy, które 6.D197 wskazało dla <c>src/Game/</c>
    /// (<c>ProtectionMode.cs:33</c> i <c>ParameterStatus.cs:32</c> biorą
    /// <c>string status</c>) — w rdzeniu zjawisko powtarza się co do nazwy.</para>
    /// </remarks>
    private static readonly string[] NazwyDwuznaczneWRdzeniu =
        { "Reason", "expected", "phase", "status", "variant" };

    private static readonly Regex DeklaracjaZmiennej =
        new(@"\b([A-Za-z_]\w*)\??\s+([a-zA-Z_]\w*)\s*(?=[;,=)])", RegexOptions.Compiled);

    /// <summary>Słowa, po których `Typ nazwa` nie jest deklaracją.</summary>
    private static readonly HashSet<string> NieTyp = new(StringComparer.Ordinal)
        { "return", "new", "case", "is", "as", "out", "ref", "in", "typeof", "await", "throw" };

    /// <summary>Pliki rdzenia — `src/Sim/`, bez wygenerowanych.</summary>
    private static List<string> PlikiRdzenia() =>
        PlikiZrodlowe()
            .Where(p => p.Contains(Path.Combine("src", "Sim") + Path.DirectorySeparatorChar,
                                   StringComparison.Ordinal))
            .ToList();

    /// <summary>
    /// `(jednoznaczne, dwuznaczne)` — nazwy zadeklarowane w rdzeniu z typem
    /// wyliczeniowym, rozdzielone po tym, czy ta sama nazwa nosi gdzieś inny typ.
    /// </summary>
    private static (HashSet<string> Jednoznaczne, SortedSet<string> Dwuznaczne)
        NazwyWyliczeniowychWRdzeniu(IEnumerable<string> zrodla)
    {
        var typy = new HashSet<string>(WyliczeniaZrodel().Keys, StringComparer.Ordinal);
        var wyliczeniowe = new SortedSet<string>(StringComparer.Ordinal);
        var inne = new HashSet<string>(StringComparer.Ordinal);
        foreach (var kod in zrodla)
        {
            foreach (Match m in DeklaracjaZmiennej.Matches(KodLeksykalnie(kod)))
            {
                var typ = m.Groups[1].Value;
                var nazwa = m.Groups[2].Value;
                if (typy.Contains(typ))
                {
                    wyliczeniowe.Add(nazwa);
                }
                else if (!NieTyp.Contains(typ))
                {
                    inne.Add(nazwa);
                }
            }
        }

        var dwuznaczne = new SortedSet<string>(wyliczeniowe.Where(inne.Contains), StringComparer.Ordinal);
        return (new HashSet<string>(wyliczeniowe.Where(n => !inne.Contains(n)), StringComparer.Ordinal),
                dwuznaczne);
    }

    /// <summary>Cele wywołań `.ToString()` bez argumentu, czytane leksykalnie.</summary>
    private static List<string> CeleToStringBezArgumentu(IEnumerable<string> zrodla) =>
        zrodla
            .SelectMany(kod => WzorzecToStringBezArgumentu.Matches(KodLeksykalnie(kod))
                .Select(m => m.Groups[1].Value))
            .ToList();

    [TestMethod]
    public void W_rdzeniu_zadne_ToString_nie_stoi_na_wartosci_wyliczenia()
    {
        var zrodla = PlikiRdzenia().Select(File.ReadAllText).ToList();
        Assert.IsTrue(zrodla.Count > 10, $"plików rdzenia znaleziono {zrodla.Count} — skan oślepł");

        var cele = CeleToStringBezArgumentu(zrodla);
        Assert.IsTrue(cele.Count >= MinimumToStringWRdzeniu,
            $"wywołań `.ToString()` bez argumentu w rdzeniu znaleziono {cele.Count} przy "
            + $"podłodze {MinimumToStringWRdzeniu} — zero znaczy „czytnik przestał czytać”, "
            + "a nie „rdzeń czysty”");

        var (jednoznaczne, dwuznaczne) = NazwyWyliczeniowychWRdzeniu(zrodla);
        CollectionAssert.AreEqual(NazwyDwuznaczneWRdzeniu, dwuznaczne.ToArray(),
            "zbiór nazw dwuznacznych w rdzeniu się zmienił — to ŚLEPA PLAMKA tej bramki "
            + "i rośnie razem z nią; nowa nazwa wymaga wpisania tutaj razem z powodem, "
            + $"dziś: [{string.Join(", ", dwuznaczne)}]");

        var naWyliczeniu = cele
            .Where(c => jednoznaczne.Contains(c[(c.LastIndexOf('.') + 1)..]))
            .Distinct(StringComparer.Ordinal)
            .OrderBy(c => c, StringComparer.Ordinal)
            .ToList();
        Assert.AreEqual(0, naWyliczeniu.Count,
            "`.ToString()` na wartości typu wyliczeniowego w `src/Sim/`: "
            + string.Join(", ", naWyliczeniu)
            + " — rdzeń nie ma ekranu (`CLAUDE.md` §4.9), więc angielski identyfikator "
            + "idzie do DZIENNIKA albo do TELEMETRII i wygląda tam poprawnie, dopóki ktoś "
            + "nie weźmie tego pliku za źródło nazw. Nazwij drogę wyniku i dopisz ją "
            + "do raportu 6.D213, albo zamień wywołanie na jawne odwzorowanie");
    }

    [TestMethod]
    public void Sito_rdzenia_milczy_na_kodzie_poprawnym_i_ma_NAZWANA_slepa_plamke()
    {
        // Nazwy próbek są CELOWO takie, jakich w drzewie nie ma (`probaFaza`,
        // `probaNapis`, `probaStatus`). Pierwsza wersja użyła `faza` i `status`
        // — wtedy KN-1, która dokłada do rdzenia `DoorPhase faza`, zapalała
        // DWA testy zamiast jednego: kontrola przyrządu liczyła trafienie
        // z drzewa razem ze swoim. Kontrola przyrządu ma nie zależeć od drzewa.
        // Kontrola PRZYRZĄDU: bramka wyżej stoi dziś na ZERZE, więc sito, które
        // przestałoby cokolwiek rozpoznawać, dałoby tę samą zieleń. Trzy próbki
        // syntetyczne wykonują trzy przypadki, w tym ten, w którym sito jest ŚLEPE.
        var baza = PlikiRdzenia().Select(File.ReadAllText).ToList();

        // PRZYROST, a nie suma — powód stoi przy <see cref="PrzyrostSitaRdzenia"/>,
        // dokąd oba czytniki przeniosły się przy 6.D224, bo woła je teraz także
        // druga kontrola przyrządu. Druga kopia rozjechałaby się przy pierwszej
        // poprawce (6.D213).
        List<string> traf(string dopisek) => PrzyrostSitaRdzenia(baza, dopisek);

        CollectionAssert.AreEqual(new string[0],
            traf("class A { void M() { string probaNapis = \"x\"; var s = probaNapis.ToString(); } }"),
            "sito zapaliło się na napisie — to KOD POPRAWNY, a bramka świecąca "
            + "na poprawnym tekście zostaje wyłączona, nie poprawiona (6.D27)");

        CollectionAssert.AreEqual(new[] { "probaFaza" },
            traf("class B { void M(DoorPhase probaFaza) { var s = probaFaza.ToString(); } }"),
            "sito NIE zobaczyło `.ToString()` na wartości `DoorPhase` — czyli nie widzi "
            + "tego, po co istnieje");

        // Ta JEDNA próbka bierze nazwę Z DRZEWA i to jest konieczne, a nie
        // niedopatrzenie: ślepa plamka jest własnością zbioru nazw dwuznacznych
        // w `src/Sim/`, więc nazwa wymyślona na miejscu nie byłaby dwuznaczna
        // i sito by ją ZOBACZYŁO — czyli próbka mierzyłaby co innego.
        CollectionAssert.AreEqual(new string[0],
            traf($"class C {{ void M(ParameterStatus {NazwyDwuznaczneWRdzeniu[3]}) {{ var s = {NazwyDwuznaczneWRdzeniu[3]}.ToString(); }} }}"),
            "sito zobaczyło wywołanie na nazwie DWUZNACZNEJ (`" + NazwyDwuznaczneWRdzeniu[3]
            + "`) — a zmierzone jest, że nie "
            + "widzi; jeżeli zaczęło widzieć, ślepa plamka zniknęła i `NazwyDwuznaczneWRdzeniu` "
            + "opisuje stan, którego już nie ma");
    }

    /// <summary>
    /// Trafienia sita rdzenia: cele `.ToString()`, których ostatni człon jest nazwą
    /// zadeklarowaną w `src/Sim/` z typem wyliczeniowym JEDNOZNACZNIE.
    /// </summary>
    /// <remarks>
    /// <para>Wyjęte z ciała <see cref="Sito_rdzenia_milczy_na_kodzie_poprawnym_i_ma_NAZWANA_slepa_plamke"/>
    /// przy 6.D224, bo od tej pozycji woła je DRUGA kontrola przyrządu. Druga kopia
    /// rozjechałaby się przy pierwszej poprawce, a 6.D213 usunęło już jedną taką
    /// z tego pliku.</para>
    /// </remarks>
    private static List<string> TrafieniaSitaRdzenia(IEnumerable<string> zrodla)
    {
        var (jednoznaczne, _) = NazwyWyliczeniowychWRdzeniu(zrodla);
        return CeleToStringBezArgumentu(zrodla)
            .Where(c => jednoznaczne.Contains(c[(c.LastIndexOf('.') + 1)..]))
            .ToList();
    }

    /// <summary>PRZYROST trafień sita po dołożeniu JEDNEJ próbki do rdzenia.</summary>
    /// <remarks>
    /// <para><b>Przyrost, a nie suma.</b> Pierwsza wersja zwracała wszystkie trafienia
    /// zbioru `baza + próbka` i przez to kontrola negatywna dokładająca wywołanie do
    /// RDZENIA zapalała kontrolę przyrządu razem z bramką drzewa. Kontrola przyrządu
    /// ma mówić o próbce, a nie o tym, co akurat leży w drzewie.</para>
    /// </remarks>
    private static List<string> PrzyrostSitaRdzenia(List<string> baza, string dopisek)
    {
        var przyrost = new List<string>(TrafieniaSitaRdzenia(baza.Append(dopisek).ToList()));
        foreach (var juz in TrafieniaSitaRdzenia(baza))
        {
            przyrost.Remove(juz);
        }

        return przyrost;
    }

    // ---------------------------------------------------------------------
    // 6.D224 — DRUGA ślepa plamka tego samego sita: typ WNIOSKOWANY (`var`)
    // ---------------------------------------------------------------------

    // Ile jest `var`-ów w rdzeniu — zmierzone 15.09.2026, ale NIE przybite, i to jest
    // rozstrzygnięcie, a nie przeoczenie. Słowo `var` stoi w 57 plikach `src/Sim/`
    // 536 razy, tyle samo surowo i po masce `KodLeksykalnie`; 535 z nich wiąże jedną
    // nazwę, a jedno (`ServiceDay.cs`, `foreach (var (moment, delta) in events)`)
    // rozkłada krotkę i żadnej nazwy pojedynczej nie deklaruje.
    //
    // Podłogi na 536 tu NIE MA, bo została ZMIERZONA jako bramka świecąca na kodzie
    // poprawnym (6.D27). Kontrola negatywna: zamiana `var phase = _stop.Phase;`
    // w `LineDrive.cs` na `DoorPhase phase = _stop.Phase;` — czyli dokładnie ta
    // poprawka, na którą ta pozycja wskazuje — daje 535 i zapala podłogę
    // komunikatem „czytnik przestał czytać”, który w tym przypadku jest nieprawdą.
    // Podłoga `MinimumToStringWRdzeniu` tej wady nie ma, bo tamtych wywołań przybywa
    // razem z kodem i nikt ich celowo nie usuwa; `var`-y usuwa się celowo.
    //
    // Zamiast podłogi stoją dwa sprawdzenia, które oślepłego czytnika łapią mocniej:
    // równość „surowo == po masce" oraz dziesięć wzorców z wykazu, z których KAŻDY
    // musi trafić w zamaskowane źródło dokładnie raz.

    /// <summary>
    /// Ile z <see cref="VarOTypieWyliczeniowymWRdzeniu"/> wpada RÓWNIEŻ w pierwszą
    /// ślepą plamkę, czyli nosi nazwę z <see cref="NazwyDwuznaczneWRdzeniu"/>.
    /// </summary>
    /// <remarks>
    /// <para><b>To jest najważniejsza liczba tej pozycji i dlatego stoi w kodzie,
    /// a nie w raporcie: 8 z 10.</b> Obie plamki się NAKŁADAJĄ. Nawet doskonałe
    /// wnioskowanie typu dla `var` — Roslyn, metadane, cokolwiek — pokazałoby situ
    /// tylko <b>2 z 10</b> tych deklaracji, bo zawężenie do nazw JEDNOZNACZNYCH
    /// odrzuciłoby pozostałe osiem (`phase` ×3, `status` ×4, `variant` ×1) niezależnie
    /// od tego, jak dobrze rozpoznany jest ich typ. Cena domknięcia drugiej plamki
    /// wynosi więc <b>2 pozycje z 10 i 0 usterek</b> — zmierzone, nie oszacowane:
    /// wywołań `.ToString()` na którejkolwiek z tych dziesięciu nazw jest dziś ZERO.</para>
    /// <para><b>Zależność idzie też w drugą stronę i to jest pomiar, nie domysł.</b>
    /// Druga plamka nie tylko nakłada się na pierwszą — częściowo ją WYTWARZA.
    /// <see cref="DeklaracjaZmiennej"/> bierze `var` za nazwę typu, a `var` nie stoi
    /// w <see cref="NieTyp"/>, więc każda nazwa zadeklarowana przez `var` ląduje
    /// w koszyku „inne typy" i tym samym może uczynić DWUZNACZNĄ tę samą nazwę użytą
    /// gdzie indziej z wyliczeniem. Zmierzone podstawieniem 15.09.2026: gdyby `var`
    /// dopisać do <see cref="NieTyp"/>, nazw dwuznacznych byłoby <b>4, nie 5</b>
    /// (odpadłaby `expected`, dwuznaczna WYŁĄCZNIE przez
    /// `ProtectionMode.cs` `var expected = ForHistoricalDate(date)`, gdzie typem jest
    /// klasa `ProtectionMode`), a jednoznacznych <b>20 zamiast 19</b>. Podstawienia
    /// nie wykonuję — `NazwyDwuznaczneWRdzeniu` jest przybite przy 6.D213 i jego
    /// zmiana jest osobną decyzją, nie skutkiem ubocznym tej pozycji.</para>
    /// </remarks>
    private const int NakladaniePlamek = 8;

    /// <summary>
    /// `var`-y w `src/Sim/`, pod którymi kryje się wartość typu wyliczeniowego —
    /// DRUGA ślepa plamka sita, wypisana Z NAZWY, a nie policzona (6.D131).
    /// </summary>
    /// <remarks>
    /// <para><b>Pole: `ścieżka | nazwa | typ | wzorzec deklaracji`.</b> Czwarte pole
    /// musi trafiać w zamaskowane źródło DOKŁADNIE RAZ — bez niego dwie deklaracje
    /// `var status` w `SignallingPlan.cs` byłyby jednym wpisem i wykaz miałby 9 pozycji
    /// zamiast 10, a liczba <see cref="NakladaniePlamek"/> nie miałaby z czego wyjść.
    /// Numeru wiersza w kluczu NIE MA świadomie: zapalałby się przy każdym przesunięciu
    /// linii, czyli na kodzie poprawnym (6.D27).</para>
    /// <para><b>Dlaczego wykaz, a nie liczba (6.D131).</b> Liczba 10 przechodzi
    /// po podbiciu cyfry; wykaz każe powiedzieć, KTÓRA deklaracja doszła i jakiego
    /// jest typu — a tego wzorzec odczytać nie umie, więc musi to zrobić autor.</para>
    /// <para><b>Dlaczego wszystkie dziesięć, a nie tylko te dwie, które pierwsza plamka
    /// przepuszcza.</b> Wykaz opisuje, czego nie widzi TEN czytnik — deklarację
    /// z typem wnioskowanym. To, co z tą samą nazwą robi sito nazw, jest własnością
    /// DRUGIEGO przyrządu i zmienia się razem z nim: <see cref="NazwyDwuznaczneWRdzeniu"/>
    /// jest przybite ręcznie i może się skurczyć, a wtedy pozycje dziś „zasłonięte
    /// podwójnie" przechodzą pod wyłączną odpowiedzialność tego wykazu. Wykaz obcięty
    /// do dwóch nie zauważyłby tego przejścia i — co ważniejsze — nie dałoby się z niego
    /// policzyć <see cref="NakladaniePlamek"/>, czyli jedynego zdania, dla którego
    /// ta pozycja powstała. Wybór jest więc z zakresu pomiaru, nie z wygody: wykaz
    /// dwuelementowy byłby krótszy, ale mierzyłby cudzy przyrząd.</para>
    /// <para><b>GRANICA tego wykazu, zmierzona, a nie opowiedziana.</b> Dziewięciu
    /// z dziesięciu wpisów nie da się z drzewa WYPROWADZIĆ — można tylko sprawdzić,
    /// że nadal tam stoją. Skutek jest taki, że skreślenie jednego z tych dziewięciu
    /// RAZEM z obniżeniem <see cref="NakladaniePlamek"/> o jeden przechodzi
    /// na zielono; zmierzone 15.09.2026 na wpisie `Train/StationStop.cs` (8→7).
    /// Nie jest to wada do naprawienia wzorcem — jest to dokładnie ta plamka, którą
    /// wykaz opisuje: gdyby dało się ją policzyć, nie byłaby ślepa. Domknięcie wymaga
    /// rozbioru składni, czyli zależności, czyli decyzji właściciela (§8), a ta zapadła
    /// tak, że bramka ZOSTAJE NA ŹRÓDLE. Jedyny wpis, który drzewo potwierdza samo,
    /// to `FixedBlockSystem.cs|reason|AuthorityLimit` — sprawdzenie 2 w bramce niżej.</para>
    /// <para><b>Czego wzorzec NIE odczyta i dlaczego wykaz musi być ręczny.</b>
    /// Typ dziewięciu z dziesięciu tych deklaracji jest typem ZWRACANYM: przez
    /// `ParameterStatusParser.Parse` (×4), przez wyrażenie `switch` (×1), przez odczyt
    /// właściwości z innego pliku (×1), przez argument generyczny słownika w `out var`
    /// (×1) i przez element kolekcji w `foreach` (×2). Jedyny kształt czytelny wzorcem
    /// to `var nazwa = Wyliczenie.Człon` i w całym rdzeniu stoi on RAZ —
    /// `FixedBlockSystem.cs`, `var reason = AuthorityLimit.EndOfLine`. Tę jedną pozycję
    /// bramka niżej wylicza i porównuje ze zbiorem; pozostałe dziewięć umie tylko
    /// sprawdzić, że nadal tam stoją.</para>
    /// </remarks>
    private static readonly string[] VarOTypieWyliczeniowymWRdzeniu =
    {
        @"Physics/VehicleRegistry.cs|status|ParameterStatus|var status = ParameterStatusParser\.Parse\(",
        @"Signalling/CbtcTestArea.cs|status|ParameterStatus|var status = ParameterStatusParser\.Parse\(root\.RequiredField\(",
        @"Signalling/FixedBlockSystem.cs|reason|AuthorityLimit|var reason = AuthorityLimit\.EndOfLine;",
        @"Signalling/SignallingPlan.cs|status|ParameterStatus|var status = ParameterStatusParser\.Parse\(Required\(root,",
        @"Signalling/SignallingPlan.cs|status|ParameterStatus|var status = ParameterStatusParser\.Parse\(element\.RequiredField\(",
        @"Signalling/SignallingPlan.cs|variant|ProtectionVariant|var variant = \(Required\(root,[^\n]*\) switch",
        @"Signalling/TrainProtection.cs|previous|ProtectionAction|_lastAction\.TryGetValue\(trainId, out var previous\)",
        @"Train/DoorCycle.cs|phase|DoorPhase|foreach \(var phase in Sequence\)",
        @"Train/LineDrive.cs|phase|DoorPhase|var phase = _stop\.Phase;",
        @"Train/StationStop.cs|phase|DoorPhase|foreach \(var phase in DoorCycle\.Sequence\)",
    };

    /// <summary>
    /// Wpisy z <see cref="VarOTypieWyliczeniowymWRdzeniu"/>, których pierwsza ślepa
    /// plamka NIE zasłania — czyli cały zysk z domknięcia drugiej.
    /// </summary>
    private static readonly string[] VarPozaPierwszaPlamka =
    {
        "Signalling/FixedBlockSystem.cs|reason|AuthorityLimit",
        "Signalling/TrainProtection.cs|previous|ProtectionAction",
    };

    /// <summary>
    /// `var nazwa = Wyliczenie.Człon` — JEDYNY kształt, w którym wzorzec odczyta typ
    /// wnioskowany bez rozbioru składni.
    /// </summary>
    private static readonly Regex VarZCzlonemWyliczenia =
        new(@"\bvar\s+([A-Za-z_]\w*)\s*=\s*([A-Za-z_]\w*)\s*\.\s*[A-Za-z_]\w*", RegexOptions.Compiled);

    /// <summary>
    /// `etykieta|nazwa|Typ` dla tych `var`-ów, których typ wyliczeniowy wzorzec
    /// UMIE odczytać. Wołana i przez bramkę drzewa, i przez kontrolę przyrządu.
    /// </summary>
    private static SortedSet<string> VarWyliczenioweCzytelneWzorcem(
        IEnumerable<(string Etykieta, string Kod)> zrodla, ISet<string> typy)
    {
        var wynik = new SortedSet<string>(StringComparer.Ordinal);
        foreach (var (etykieta, kod) in zrodla)
        {
            foreach (Match m in VarZCzlonemWyliczenia.Matches(KodLeksykalnie(kod)))
            {
                if (typy.Contains(m.Groups[2].Value))
                {
                    wynik.Add($"{etykieta}|{m.Groups[1].Value}|{m.Groups[2].Value}");
                }
            }
        }

        return wynik;
    }

    private static string KluczWpisu(string wpis) =>
        string.Join("|", wpis.Split('|').Take(3));

    [TestMethod]
    public void Var_o_typie_wyliczeniowym_to_DRUGA_slepa_plamka_sita_rdzenia()
    {
        var pliki = PlikiRdzenia();
        Assert.IsTrue(pliki.Count > 10, $"plików rdzenia znaleziono {pliki.Count} — skan oślepł");

        var typy = new HashSet<string>(WyliczeniaZrodel().Keys, StringComparer.Ordinal);
        var slowoVar = new Regex(@"\bvar\b", RegexOptions.Compiled);
        var maski = new Dictionary<string, string>(StringComparer.Ordinal);
        var surowo = 0;
        var poMasce = 0;
        foreach (var sciezka in pliki)
        {
            var kod = File.ReadAllText(sciezka);
            var maska = KodLeksykalnie(kod);
            maski[sciezka] = maska;
            surowo += slowoVar.Matches(kod).Count;
            poMasce += slowoVar.Matches(maska).Count;
        }

        // Relacja, nie liczba: gdyby słowo `var` weszło w rdzeniu do komentarza albo
        // do literału, wykaz niżej mógłby opisywać tekst, którego kompilator nie widzi.
        Assert.AreEqual(surowo, poMasce,
            $"słowo `var` czyta się w rdzeniu inaczej surowo ({surowo}) niż po masce "
            + $"({poMasce}) — weszło do komentarza albo do literału, a wtedy wykaz "
            + "`VarOTypieWyliczeniowymWRdzeniu` może opisywać tekst, którego nie ma w kodzie");
        Assert.IsTrue(poMasce > 0, $"słów `var` w rdzeniu znaleziono {poMasce} — czytnik oślepł");

        // 1. Każdy wpis wykazu nadal stoi w drzewie — i stoi DOKŁADNIE RAZ.
        var czytelneZWykazu = new SortedSet<string>(StringComparer.Ordinal);
        foreach (var wpis in VarOTypieWyliczeniowymWRdzeniu)
        {
            var pola = wpis.Split('|');
            Assert.AreEqual(4, pola.Length, $"wpis `{wpis}` nie ma czterech pól");
            var ogon = pola[0].Replace('/', Path.DirectorySeparatorChar);
            var sciezka = pliki.SingleOrDefault(p => p.EndsWith(
                Path.DirectorySeparatorChar + ogon, StringComparison.Ordinal));
            Assert.IsNotNull(sciezka,
                $"wpis `{wpis}`: pliku `{pola[0]}` nie ma w `src/Sim/` — wykaz drugiej "
                + "ślepej plamki opisuje drzewo, którego już nie ma");
            Assert.IsTrue(typy.Contains(pola[2]),
                $"wpis `{wpis}`: `{pola[2]}` nie jest dziś wyliczeniem zadeklarowanym "
                + "w `src/` — albo typ zmienił postać, albo wykaz kłamie");

            var trafienia = Regex.Matches(maski[sciezka], pola[3]);
            Assert.AreEqual(1, trafienia.Count,
                $"wpis `{wpis}`: wzorzec deklaracji trafia w `{pola[0]}` {trafienia.Count} razy "
                + "zamiast raz. Deklaracja zniknęła, zmieniła kształt albo pojawiła się druga "
                + "taka sama — a każdy z tych trzech przypadków wymaga ODPOWIEDZI, jakiego "
                + "typu jest dziś ta zmienna; wzorzec sam tego nie odczyta");

            var czytelny = VarZCzlonemWyliczenia.Match(trafienia[0].Value);
            if (czytelny.Success && typy.Contains(czytelny.Groups[2].Value))
            {
                czytelneZWykazu.Add($"{Path.GetFileName(sciezka)}|{czytelny.Groups[1].Value}|"
                    + czytelny.Groups[2].Value);
            }
        }

        // 2. Część MIERZALNA: `var nazwa = Wyliczenie.Człon` liczy się wzorcem, więc
        //    zbiór policzony z drzewa musi się zgadzać ze zbiorem wyprowadzonym z wykazu.
        //    Dołożenie takiego `var`-a do `src/Sim/` zapala tę właśnie równość.
        var czytelneZDrzewa = VarWyliczenioweCzytelneWzorcem(
            pliki.Select(p => (Path.GetFileName(p), File.ReadAllText(p))), typy);
        CollectionAssert.AreEqual(czytelneZWykazu.ToArray(), czytelneZDrzewa.ToArray(),
            "zbiór `var`-ów o typie wyliczeniowym CZYTELNYM wzorcem rozjechał się z wykazem: "
            + $"z wykazu [{string.Join(", ", czytelneZWykazu)}], z drzewa "
            + $"[{string.Join(", ", czytelneZDrzewa)}]. To jedyna część drugiej ślepej "
            + "plamki, którą wzorzec umie policzyć — reszta wykazu jest ręczna i tak "
            + "ma zostać do decyzji właściciela (§8)");

        // 3. NAKŁADANIE SIĘ obu plamek, policzone, a nie opowiedziane.
        var dwuznaczne = new HashSet<string>(NazwyDwuznaczneWRdzeniu, StringComparer.Ordinal);
        var wObu = VarOTypieWyliczeniowymWRdzeniu
            .Where(w => dwuznaczne.Contains(w.Split('|')[1])).ToList();
        Assert.AreEqual(NakladaniePlamek, wObu.Count,
            $"nakładanie się obu ślepych plamek wynosi dziś {wObu.Count} z "
            + $"{VarOTypieWyliczeniowymWRdzeniu.Length}, a przybite jest {NakladaniePlamek}. "
            + "Ta liczba mówi, ile kosztowałoby domknięcie DRUGIEJ plamki: pozycje "
            + "zasłonięte także przez PIERWSZĄ nie stałyby się widoczne nawet przy "
            + "doskonałym wnioskowaniu typu. Zmieniła się, bo doszedł/odszedł `var` "
            + "albo bo `NazwyDwuznaczneWRdzeniu` się skurczyło — w obu razach trzeba "
            + "przeliczyć, czy zysk z domknięcia nadal jest wart pracy");
        CollectionAssert.AreEqual(VarPozaPierwszaPlamka,
            VarOTypieWyliczeniowymWRdzeniu
                .Where(w => !dwuznaczne.Contains(w.Split('|')[1]))
                .Select(KluczWpisu)
                .ToArray(),
            "zmienił się zbiór pozycji, które przepuszcza PIERWSZA plamka, a zatrzymuje "
            + "DRUGA — czyli cały zysk z jej domknięcia. Dziś są to dwie pozycje "
            + "i zero usterek");

        // 4. Bramka stoi na ZERZE — i to jest stan drzewa, nie własność przyrządu.
        //    Sprawdzenie jest zawężone do PLIKU wpisu, a nie do całego rdzenia: sito
        //    po samej nazwie dawało w 6.D213 fałszywe trafienie na `string status`.
        //    GRANICA, zmierzona: `TrainProtection.cs` ma DWA `var previous` — ten
        //    z wykazu (`ProtectionAction`) i drugi, `bool`, z `_lastDoorRelease`.
        //    Wywołanie na tym drugim zapaliłoby ten warunek niesłusznie; wtedy wpis
        //    dostaje nazwany wyjątek, a bramka NIE jest wyłączana.
        var wywolania = new List<string>();
        foreach (var wpis in VarOTypieWyliczeniowymWRdzeniu)
        {
            var pola = wpis.Split('|');
            var ogon = pola[0].Replace('/', Path.DirectorySeparatorChar);
            var sciezka = pliki.Single(p => p.EndsWith(
                Path.DirectorySeparatorChar + ogon, StringComparison.Ordinal));
            if (Regex.IsMatch(maski[sciezka], $@"\b{Regex.Escape(pola[1])}\.ToString\(\s*\)"))
            {
                wywolania.Add(KluczWpisu(wpis));
            }
        }

        Assert.AreEqual(0, wywolania.Count,
            "`.ToString()` na `var`-ze o typie wyliczeniowym w `src/Sim/`: "
            + string.Join(", ", wywolania.Distinct())
            + " — sito z 6.D213 tego NIE widzi, bo czyta deklaracje wzorcem `Typ nazwa`. "
            + "Rdzeń nie ma ekranu (`CLAUDE.md` §4.9), więc angielski identyfikator idzie "
            + "do dziennika albo do telemetrii. Zamień na jawne odwzorowanie — albo, jeśli "
            + "wywołanie stoi na innej zmiennej o tej samej nazwie w tym pliku, dopisz "
            + "nazwany wyjątek zamiast wyłączać bramkę");
    }

    /// <summary>
    /// Kontrola PRZYRZĄDU dla 6.D224 — obie gałęzie wykonane, bo bramka stoi na zerze.
    /// </summary>
    /// <remarks>
    /// <para>Bramka wyżej kończy się na <c>Assert.AreEqual(0, …)</c>, więc sito, które
    /// przestałoby cokolwiek rozpoznawać, dałoby tę samą zieleń. Trzy próbki syntetyczne
    /// rozstrzygają to, czego zielony przebieg nie rozstrzyga: że plamka jest PRAWDZIWA
    /// (gałąź A), że przyrząd na tym samym kodzie z typem JAWNYM działa (gałąź B),
    /// i że mierzalna część wykazu naprawdę reaguje na dołożonego `var`-a (gałąź C).</para>
    /// <para>Nazwy próbek są celowo takie, jakich w drzewie nie ma — tak samo jak
    /// w <see cref="Sito_rdzenia_milczy_na_kodzie_poprawnym_i_ma_NAZWANA_slepa_plamke"/>,
    /// i z tego samego powodu: kontrola przyrządu ma nie zależeć od drzewa.</para>
    /// </remarks>
    [TestMethod]
    public void Kontrola_przyrzadu_6D224_sito_jest_SLEPE_na_var_i_widzi_typ_JAWNY()
    {
        var baza = PlikiRdzenia().Select(File.ReadAllText).ToList();

        // GAŁĄŹ A — plamka jest PRAWDZIWA: typ wnioskowany, nazwa jednoznaczna, sito milczy.
        CollectionAssert.AreEqual(new string[0],
            PrzyrostSitaRdzenia(baza,
                "class Sz1 { void M() { var probaFazaVar = DoorPhase.Open; "
                + "var s = probaFazaVar.ToString(); } }"),
            "sito ZOBACZYŁO `.ToString()` na zmiennej z typem WNIOSKOWANYM — a zmierzone "
            + "jest, że nie widzi. Jeżeli zaczęło widzieć, druga ślepa plamka zniknęła "
            + "i `VarOTypieWyliczeniowymWRdzeniu` opisuje stan, którego już nie ma");

        // GAŁĄŹ B — przyrząd DZIAŁA: ten sam kod z typem JAWNYM i tak samo jednoznaczną
        // nazwą zapala. Bez tej gałęzi gałąź A mierzyłaby zepsute sito, a nie plamkę.
        CollectionAssert.AreEqual(new[] { "probaFazaJawna" },
            PrzyrostSitaRdzenia(baza,
                "class Sz2 { void M() { DoorPhase probaFazaJawna = DoorPhase.Open; "
                + "var s = probaFazaJawna.ToString(); } }"),
            "sito NIE zobaczyło `.ToString()` na zmiennej o typie JAWNYM i nazwie "
            + "jednoznacznej — czyli nie widzi tego, po co istnieje, a gałąź A nie mówi "
            + "wtedy nic o `var`");

        // GAŁĄŹ C — mierzalna część wykazu reaguje na dołożonego `var`-a. Bez niej
        // kontrola negatywna „dołóż `var` do `src/Sim/`" nie miałaby czego zapalić.
        var typy = new HashSet<string>(WyliczeniaZrodel().Keys, StringComparer.Ordinal);
        CollectionAssert.AreEqual(new[] { "próbka|probaFazaVar|DoorPhase" },
            VarWyliczenioweCzytelneWzorcem(
                new[] { ("próbka", "class Sz3 { void M() { var probaFazaVar = DoorPhase.Open; } }") },
                typy).ToArray(),
            "czytnik nie rozpoznał kształtu `var nazwa = Wyliczenie.Człon` — jedynego, "
            + "który umie odczytać; równość zbiorów w bramce wyżej przestałaby wtedy "
            + "reagować na dołożonego `var`-a");

        // GRANICA, wykonana a nie opowiedziana: ten sam czytnik NIE odczyta typu, gdy
        // inicjalizator jest wywołaniem — a tak stoi 9 z 10 pozycji wykazu.
        CollectionAssert.AreEqual(new string[0],
            VarWyliczenioweCzytelneWzorcem(
                new[] { ("próbka", "class Sz4 { void M() { var probaStatusVar = "
                    + "ParameterStatusParser.Parse(tekst); } }") },
                typy).ToArray(),
            "czytnik zaczął odczytywać typ z WYWOŁANIA — granica zapisana przy "
            + "`VarOTypieWyliczeniowymWRdzeniu` opisuje wtedy stan, którego już nie ma");
    }

    /// <summary>Podłoga na liczbę zgłoszeń obu czytników `.ToString()` w całym `src/`.</summary>
    /// <remarks>
    /// <para>Zmierzone 15.09.2026 na CAŁYM <c>src/</c>: <b>53</b> — 3 + 18
    /// w <c>src/Game/</c>, 3 + 6 w <c>src/Sim/</c> (szóste doszło razem z nawiasem
    /// okrągłym) i 1 + 22 w <c>src/Sim.Runner/</c>.</para>
    /// <para><b>Pierwsza wersja tej podłogi stała na 30 i to była moja pomyłka,
    /// zmierzona.</b> Trzydziestka wzięła się z dwóch katalogów, a czytnik chodzi po
    /// wszystkich trzech — podłoga stała więc <b>23 poniżej</b> stanu faktycznego
    /// i nie zapalała się przy COFNIĘCIU wzorca: wariant bez nawiasu okrągłego daje 52,
    /// goły <c>\w+</c> też 52, a 52 &gt;= 30. Na 53 oba cofnięcia zapalają.</para>
    /// <para>Podłoga, nie równość — wywołań przybywa z kodem. Ale podłoga POSTAWIONA
    /// NA ZMIERZONEJ WARTOŚCI, a nie z zapasem: zapas jest tu dokładnie tym, co odbiera
    /// bramce zdolność wykrywania.</para>
    /// </remarks>
    private const int MinimumZgloszenToString = 53;

    /// <summary>Zgłoszenia obu czytników `.ToString()` w całym `src/`, z adresem.</summary>
    private static List<string> ZgloszeniaToString()
    {
        var out_ = new List<string>();
        foreach (var sciezka in PlikiZrodlowe())
        {
            var czysty = KodLeksykalnie(File.ReadAllText(sciezka));
            foreach (var wzorzec in new[] { WzorzecToStringBezArgumentu, WzorzecToStringZArgumentem })
            {
                foreach (Match m in wzorzec.Matches(czysty))
                {
                    out_.Add($"{Path.GetFileName(sciezka)}:{m.Groups[1].Value}");
                }
            }
        }

        return out_;
    }

    [TestMethod]
    public void Zadne_zgloszenie_ToString_nie_jest_URWANE_na_indeksatorze()
    {
        var zgloszenia = ZgloszeniaToString();
        Assert.IsTrue(zgloszenia.Count >= MinimumZgloszenToString,
            $"zgłoszeń `.ToString()` w `src/` znaleziono {zgloszenia.Count} przy podłodze "
            + $"{MinimumZgloszenToString} — zero znaczy „czytnik przestał czytać”");

        var urwane = zgloszenia
            .Where(z => z[(z.IndexOf(':') + 1)..] is var cel
                        && (cel.StartsWith('.') || cel.EndsWith('.')))
            .OrderBy(z => z, StringComparer.Ordinal)
            .ToList();
        Assert.AreEqual(0, urwane.Count,
            "zgłoszenie z kropką na brzegu, czyli nazwa URWANA: "
            + string.Join(", ", urwane)
            + " — komunikat bramki istnieje po to, żeby nie trzeba było wracać do pliku "
            + "i szukać ręcznie; nazwa bez obiektu tego nie daje (6.D214)");
    }

    [TestMethod]
    public void Czytnik_ToString_czyta_CZLON_Z_INDEKSATOREM_a_stary_go_gubil()
    {
        // Kontrola PRZYRZĄDU: bramka wyżej stoi po poprawce na ZERZE, więc czytnik,
        // który przestałby cokolwiek znajdować, dałby tę samą zieleń. Próbka wykonuje
        // OBA czytniki — dzisiejszy i ten sprzed 6.D214 — na tym samym tekście.
        const string probka = "var x = _line.Calls[^1].StopErrorM.ToString(\"0.0\");\n"
                              + "var y = _plain.Field.ToString();\n";
        var stary = new Regex(@"([\w.]+)\.ToString\(\s*[^)\s]");
        var staryBez = new Regex(@"([\w.]+)\.ToString\(\s*\)");

        Assert.AreEqual("_line.Calls[^1].StopErrorM",
            WzorzecToStringZArgumentem.Match(probka).Groups[1].Value,
            "dzisiejszy czytnik nie wziął członu z indeksatorem — po to ta pozycja istnieje");
        Assert.AreEqual(".StopErrorM", stary.Match(probka).Groups[1].Value,
            "czytnik SPRZED 6.D214 przestał gubić nazwę — próbka nie rozdziela już obu "
            + "czytników i nie mówi o poprawce niczego");

        // I druga strona: na wyrażeniu BEZ indeksatora oba czytniki mają dać to samo.
        Assert.AreEqual(WzorzecToStringBezArgumentu.Match(probka).Groups[1].Value,
            staryBez.Match(probka).Groups[1].Value,
            "poszerzenie zmieniło odczyt wyrażenia bez indeksatora — miało zmienić "
            + "DOKŁADNIE te przypadki, w których stary czytnik się mylił");

        // NAWIAS OKRĄGŁY: wywołanie na wyniku metody było NIEWIDOCZNE, nie urwane.
        const string poMetodzie = "var z = Units.MpsToKmh(v).ToString(kultura);\n";
        Assert.AreEqual("Units.MpsToKmh(v)",
            WzorzecToStringZArgumentem.Match(poMetodzie).Groups[1].Value,
            "dzisiejszy czytnik nie widzi wywołania na wyniku metody — a `SignallingPlan.cs:216` "
            + "jest dokładnie tym przypadkiem");
        Assert.IsFalse(stary.IsMatch(poMetodzie),
            "czytnik SPRZED 6.D214 zaczął widzieć wywołanie na wyniku metody — próbka "
            + "przestała rozdzielać oba czytniki");

        // GRANICA, wykonana a nie opowiedziana: nawiasy ZAGNIEŻDŻONE zostają niewidoczne.
        const string zagniezdzone = "var q = f(g(x)).ToString(kultura);\n";
        Assert.IsFalse(WzorzecToStringZArgumentem.IsMatch(zagniezdzone),
            "czytnik zaczął czytać nawiasy ZAGNIEŻDŻONE — granica zapisana przy "
            + "`CzlonWyrazenia` opisuje wtedy stan, którego już nie ma, i trzeba ją przepisać");
    }

    private static readonly Regex WzorzecToStringZArgumentem =
        new($@"((?:{CzlonWyrazenia})(?:\.{CzlonWyrazenia})*)\.ToString\(\s*[^)\s]",
            RegexOptions.Compiled);

    /// <summary>
    /// Kod z komentarzami i literałami zamienionymi na spacje — ZACHOWUJE DŁUGOŚĆ,
    /// więc numery wierszy zostają te same.
    ///
    /// <para>Stoi na tych samych prymitywach, co czytnik literałów z 6.D182
    /// (<see cref="PominNieNapis"/>, <see cref="PrefiksLiteralu"/>,
    /// <see cref="CzytajLiteral"/>), bo inny czytnik znaczyłby inny pomiar.</para>
    /// </summary>
    private static string KodLeksykalnie(string source)
    {
        var wynik = new StringBuilder(source);
        var i = 0;
        while (i < source.Length)
        {
            var po = PominNieNapis(source, i, source.Length);
            if (po != i)
            {
                for (var k = i; k < po; k++)
                {
                    if (wynik[k] != '\n')
                    {
                        wynik[k] = ' ';
                    }
                }

                i = po;
                continue;
            }

            if (PrefiksLiteralu(source, i, source.Length) >= 0)
            {
                var koniec = CzytajLiteral(source, i, source.Length, new List<string>());
                for (var k = i; k < koniec; k++)
                {
                    if (wynik[k] != '\n')
                    {
                        wynik[k] = ' ';
                    }
                }

                i = koniec;
                continue;
            }

            i++;
        }

        return wynik.ToString();
    }

    private static List<string> PlikiGryZKatalogiem() =>
        Directory.GetFiles(Path.Combine(MetroBxl.Tests.Shared.KorzenRepozytorium.Sciezka, "src", "Game"), "*.cs",
                SearchOption.AllDirectories)
            .Where(p => !p.Split(Path.DirectorySeparatorChar).Contains(".godot"))
            .Where(p => !p.Split(Path.DirectorySeparatorChar).Contains("obj"))
            .Where(p => !p.Split(Path.DirectorySeparatorChar).Contains("bin"))
            .OrderBy(p => p, StringComparer.Ordinal)
            .ToList();

    [TestMethod]
    public void Ile_wywolan_ToString_bez_argumentu_ma_src_Game_i_ktora_droga_idzie_wynik()
    {
        var leksykalnie = new List<string>();
        var surowo = 0;
        var zArgumentem = new List<string>();
        foreach (var sciezka in PlikiGryZKatalogiem())
        {
            var kod = File.ReadAllText(sciezka);
            surowo += WzorzecToStringBezArgumentu.Matches(kod).Count;
            var czysty = KodLeksykalnie(kod);
            var plik = Path.GetFileName(sciezka);
            foreach (Match m in WzorzecToStringBezArgumentu.Matches(czysty))
            {
                leksykalnie.Add($"{plik}:{m.Groups[1].Value}");
            }

            foreach (Match m in WzorzecToStringZArgumentem.Matches(czysty))
            {
                zArgumentem.Add($"{plik}:{m.Groups[1].Value}");
            }
        }

        Assert.AreEqual(ToStringRegeksemPoSurowym, surowo,
            $"regeks po surowym tekście daje {surowo} zgłoszeń, a zmierzono "
            + $"{ToStringRegeksemPoSurowym}");
        Assert.AreEqual(ToStringLeksykalnieWGame, leksykalnie.Count,
            $"czytanie leksykalne daje {leksykalnie.Count} wywołań, a zmierzono "
            + $"{ToStringLeksykalnieWGame}: " + string.Join(", ", leksykalnie));

        // TO JEST WERYFIKACJA, KTÓREJ ŻĄDAŁO POLE „Weryfikacja" 6.D199, i nie jest
        // tautologią wobec dwóch równości wyżej: te przybijają liczby, ta przybija
        // RELACJĘ — a relacja jest tym, po co ta pozycja istnieje. Gdyby obie liczby
        // podniesiono kiedyś do tej samej wartości, równości przeszłyby, a ta nie.
        Assert.IsTrue(leksykalnie.Count < surowo,
            $"czytanie leksykalne daje {leksykalnie.Count}, a regeks po surowym "
            + $"{surowo} — równość znaczy, że czytnik NIE POMIJA komentarzy i różnica, "
            + "dla której ta pozycja istnieje, nie została zmierzona (6.D199)");

        // DROGA WYNIKU, nazwana wprost dla każdego wywołania na wyliczeniu.
        // `FirstRun.Faza` — ramię domyślne, wynik idzie na HUD, czyli NA EKRAN.
        // `DoorPrompt.Reason` (MB-08) — ramię domyślne, wynik wchodzi dziurą do
        // `hud.doors.refused` i idzie tą samą drogą, czyli też NA EKRAN. Nazwanie drogi
        // jest tym, czego żąda 6.D199, i odpowiedź brzmi: ta sama co przy `Faza`.
        var typy = new HashSet<string>(WyliczeniaZrodel().Keys, StringComparer.Ordinal);
        var nazwyWyliczen = new HashSet<string>(
            NazwyOTypieWyliczeniowym().Keys, StringComparer.Ordinal);
        var naWyliczeniu = leksykalnie
            .Where(w => nazwyWyliczen.Contains(w.Substring(w.IndexOf(':') + 1)))
            .ToList();
        Assert.AreEqual(ToStringNaWyliczeniuWGame, naWyliczeniu.Count,
            $"wywołań na wartości typu wyliczeniowego jest {naWyliczeniu.Count}, "
            + $"a zmierzono {ToStringNaWyliczeniuWGame}: "
            + string.Join(", ", naWyliczeniu));
        CollectionAssert.AreEqual(
            new List<string> { "FirstRun.cs:phase", "DoorPrompt.cs:refusal" }, naWyliczeniu,
            "wywołanie na wyliczeniu stoi gdzie indziej niż `FirstRun.Faza` "
            + "i `DoorPrompt.Reason` — a to jedyne dwa miejsca, o których wiadomo, "
            + "że idą NA EKRAN. Nowe wymaga nazwania drogi: ekran, log czy "
            + "telemetria (6.D199)");

        // NA EKRAN idzie to, co wraca z `Faza` do katalogu tekstów HUD-u. Sprawdzane
        // przez obecność w pliku, o którym 6.D185 wie, że jego wynik ląduje na HUD-zie.
        // DWA pliki, a nie jeden — MB-08. `DoorPrompt.cs` stoi na mapie `ZrodlaHud`
        // pod tym samym argumentem `station`, co `FirstRun.Faza`, więc jego wynik idzie
        // na HUD tą samą drogą. Warunek na jeden plik odpowiedziałby dziś „jedno"
        // i zdanie o różnicy między ekranem a telemetrią przestałoby być pomiarem.
        var plikiNaEkran = new[] { "FirstRun.cs:", "DoorPrompt.cs:" };
        var naEkranie = naWyliczeniu.Count(
            w => plikiNaEkran.Any(p => w.StartsWith(p, StringComparison.Ordinal)));
        Assert.AreEqual(ToStringNaEkranieWGame, naEkranie,
            $"na drodze NA EKRAN stoi {naEkranie} wywołań, a zmierzono "
            + $"{ToStringNaEkranieWGame}. Do logu i do telemetrii nie idzie ANI JEDNO "
            + "i ta różnica jest treścią: angielski identyfikator w telemetrii jest "
            + "danymi dla maszyny, a na HUD-zie tekstem dla gracza");

        // POSTAĆ Z ARGUMENTEM — ta, której skan tej pozycji NIE WIDZI.
        Assert.AreEqual(ToStringZArgumentemWGame, zArgumentem.Count,
            $"wywołań `.ToString(arg)` jest {zArgumentem.Count}, a zmierzono "
            + $"{ToStringZArgumentemWGame}: " + string.Join(", ", zArgumentem));
        var zArgumentemNaWyliczeniu = zArgumentem
            .Where(w => nazwyWyliczen.Contains(w.Substring(w.IndexOf(':') + 1)))
            .ToList();
        Assert.AreEqual(ToStringZArgumentemNaWyliczeniuWGame, zArgumentemNaWyliczeniu.Count,
            "wartość typu wyliczeniowego trafiła do `.ToString(arg)`: "
            + string.Join(", ", zArgumentemNaWyliczeniu)
            + ". Jest to ten sam błąd w innym ubraniu, a skan bez argumentu przechodzi "
            + "obok niego — dlatego to zero stoi tu osobno (6.D199)");
    }

    [TestMethod]
    public void Czytnik_leksykalny_ZDEJMUJE_komentarz_i_literal_a_kodu_NIE_RUSZA()
    {
        // Bez tego wejścia liczba 1 nie odróżniałaby „jedno wywołanie w kodzie" od
        // „czytnik zjada wszystko" — rodzina 6.D159.
        var kod = "var a = x.ToString();\n"
            + "// komentarz z x.ToString() w środku\n"
            + "var b = \"napis z x.ToString() w środku\";\n"
            + "/* blok z x.ToString() */\n";
        Assert.AreEqual(4, WzorzecToStringBezArgumentu.Matches(kod).Count,
            "wejście syntetyczne nie niesie czterech zgłoszeń — kontrola mierzy nie to");

        var czysty = KodLeksykalnie(kod);
        Assert.AreEqual(1, WzorzecToStringBezArgumentu.Matches(czysty).Count,
            "czytnik leksykalny zostawił " + WzorzecToStringBezArgumentu.Matches(czysty).Count
            + " zgłoszeń zamiast jednego — nie pomija komentarza wierszowego, "
            + "blokowego albo literału");
        Assert.AreEqual(kod.Length, czysty.Length,
            "czytnik zmienił DŁUGOŚĆ tekstu — wtedy numery wierszy w komunikatach "
            + "wskazują nie te miejsca");
        StringAssert.Contains(czysty, "var a = x.ToString();",
            "czytnik ruszył KOD, a nie tylko komentarz i literał");
    }

    // --- 6.D202: w jakim języku jest log przejazdu -----------------------------------
    //
    // ODPOWIEDŹ: wierszy ANGIELSKICH jest ZERO. Przesłanka pozycji („szablon
    // z `DesignAssumptions` jest po angielsku") padła, i to na dwa sposoby naraz:
    // szablon `ViewAssumption.ToString()` NIE MA ANI JEDNEGO SŁOWA — jest nim
    // `{Name} = {Value:R} {Unit} — {Reason}`, czyli same dziury, znak równości i myślnik
    // — a jedyne, co przychodzi do niego po angielsku, to `Name`, i to jest
    // IDENTYFIKATOR z `nameof(...)`, nie proza. Wszystkie 20 pól `Reason`
    // w `DesignAssumptions.All` są po polsku.
    //
    // Jest to dokładnie ten sam kształt, co przy 6.D185: na wyjście dociera ANGIELSKI
    // IDENTYFIKATOR, nie angielskie zdanie. Tamto było o nazwach członów wyliczeń
    // na HUD-zie, to jest o nazwach stałych w logu — i dlatego pytanie do właściciela
    // brzmi inaczej, niż pozycja zakładała (patrz raport §5).
    // 25 -> 27 (13.09.2026, MB-02): dwa wiersze `[SESJA]` — jednorazowy z gałęzi
    // panelu wyniku i podsumowanie na końcu odtworzenia.
    // 27 -> 28 (14.09.2026, MB-04): `FirstRun.AssetsRoot`, `DomyslnyZapisWejsc`
    // i wiersz `[ZAPISY]`. Liczba ZMIERZONA przyrzadem tego testu, a nie
    // przepisana z jego komunikatu o bledzie.
    // 28 -> 29 (14.09.2026, MB-05): `CabView.cs`, wiersz `[KABINA]`, stała
    // `ExitCabMissing` i wpięcie kabiny w `FirstRun`. Liczba ZMIERZONA
    // przyrzadem tego testu.
    // 29 -> 30 (14.09.2026, MB-07): trzy klawisze obsługi linii (N/T/O), wiersz
    // `[TUNEL koniec]` i komunikaty zakresu `--trains`. Liczba PRZELICZONA przebiegiem.
    private const int WierszyLoguWGame = 30;

    // 21 -> 23 (13.09.2026, MB-02): dwa wiersze `[SESJA]`. `WierszyLoguPoAngielsku`
    // zostaje ZEREM i to ono jest tu zdaniem.
    // 23 -> 24 (14.09.2026, MB-04): `FirstRun.AssetsRoot`, `DomyslnyZapisWejsc`
    // i wiersz `[ZAPISY]`. Liczba ZMIERZONA przyrzadem tego testu.
    // 24 -> 25 (14.09.2026, MB-07): wiersz `[TUNEL koniec]` — własne słowa, polskie.
    private const int WierszyLoguPoPolsku = 25;

    // Wiersze, których szablon NIE MA WŁASNYCH SŁÓW — cała treść przychodzi z wywołania.
    // Wszystkie w `FirstRun.cs`, i każdy z nich prowadzi do wytwórcy, który własne
    // słowa MA i ma je po polsku. Sprawdza to asercja niżej, żeby „bez słów" nie
    // czytało się jako „nieznanego języka".
    //
    // CZTERY -> PIĘĆ (14.09.2026, MB-05): doszedł `CabView.cs:[KABINA]`. Lista jest
    // WYPISANA, a nie liczona, i dlatego rośnie ręcznie: jej treścią jest odpowiedź
    // „kto te słowa naprawdę pisze", a tej nie da się wyprowadzić z samego `FirstRun`.
    private static readonly string[] WytworcyWierszaBezSlow =
    {
        "CabView.cs:[KABINA]",
        "RunHeader.cs:[PRZEJAZD]",
        "StationView.cs:[PERON]",
        "TrainView.cs:[SKŁAD]",
        "TunnelView.cs:[TUNEL]",
    };

    private const int WierszyLoguPoAngielsku = 0;

    // Identyfikatory angielskie docierające do logu — WSZYSTKIE przez `nameof(...)`
    // w założeniach. To jest jedyna angielszczyzna w całym logu przejazdu i jedyna
    // rzecz, o której jest sens pytać właściciela.
    private const int IdentyfikatorowNameofWZalozeniach = 25;

    // **DWA założenia podają nazwę LITERAŁEM, a nie `nameof(...)`** —
    // `"StartChainageM"` i `"BrakeChainageM"` w `src/Sim/Train/DriveScenario.cs`.
    // Do logu trafia z nich ten sam angielski identyfikator, ale drogą, która
    // **nie idzie za zmianą nazwy**: przemianowanie pola zostawi w logu nazwę starą,
    // i to po cichu. Liczba stoi osobno, bo to inne ryzyko niż `nameof`, a nie inna
    // ilość tego samego.
    private const int IdentyfikatorowLiteralemWZalozeniach = 2;

    private static readonly char[] LiteryPolskie =
        "ąćęłńóśźżĄĆĘŁŃÓŚŹŻ".ToCharArray();

    // **Sito po znaku diakrytycznym MYLI SIĘ NA TRZECH z dwudziestu pięciu wierszy**
    // i to jest zmierzone, nie przewidziane: `[STACJA]`, `[ZRZUT] metadane`
    // (`FirstRun.cs`) oraz CAŁY wiersz `[PRZEJAZD]` z `RunHeader.cs` — którego słowa
    // to `tryb`, `widok`, `krok`, `scenariusz`, `masa` — nie mają ani jednego ogonka,
    // a są po polsku. Sam znak diakrytyczny jest więc PIERWSZYM sitem, nigdy jedynym;
    // bez tej listy bramka meldowałaby trzy wiersze angielskie i pytanie do właściciela
    // stałoby na liczbie nieprawdziwej.
    private static readonly string[] SlowaPolskieBezZnakow =
    {
        "STACJA", "ZRZUT", "metadane", "tryb", "widok", "krok", "scenariusz", "masa",

        // MB-02. „SESJA" i „trwa" są polskie i pozbawione znaków diakrytycznych —
        // dokładnie ta rodzina, dla której ta lista powstała w 6.D202: sito po samych
        // znakach uznałoby oba wiersze `[SESJA]` za angielskie, a `WierszyLoguPoAngielsku`
        // wyszłoby z zera i przestałoby być zdaniem o drzewie.
        "SESJA", "trwa",

        // **6.D217: dziewięć z dwudziestu dziewięciu komunikatów DROGI BŁĘDU nie ma
        // ani jednego ogonka**, czyli 31 % wobec 12 % w logu przejazdu (3 z 25). Nie
        // jest to przypadek: droga błędu nazywa ARGUMENTY i PLIKI (`--limit-kmh`,
        // `.glb`, `[ASSETS]`), więc jej zdania są krótkie i techniczne, a krótkie
        // polskie zdanie techniczne często ogonka nie ma. Dwanaście słów niżej pokrywa
        // wszystkie dziewięć; każde dobrane tak, żeby nie było podciągiem zwykłego
        // słowa angielskiego — dlatego stoi „nieznan", a nie „nie" (to drugie siedzi
        // w „denied" i uznałoby komunikat ANGIELSKI za polski).
        //
        // **Cena, wypisana z nazwy, nie przemilczana:** komunikat angielski zawierający
        // którykolwiek z tych podciągów przejdzie jako polski. Dziś takiego nie ma —
        // literałów angielskich w drodze błędu jest ZERO — a gdy powstanie, złapie go
        // `Zrodla_tekstu_OBCEGO_i_WLASNEGO_sa_wymienione_Z_NAZWY_i_rozdzielone`,
        // bo tekst obcy wchodzi tu wyłącznie dziurą.
        "brak", "plik", "albo", "wymaga", "Wygeneruj", "uruchom",
        "nieznan", "Znane", "zakresem", "ujemny", "pasuje", "planem",
    };

    private static bool WygladaPoPolsku(string tekst) =>
        MaPolskieLitery(tekst)
        || SlowaPolskieBezZnakow.Any(s => tekst.Contains(s, StringComparison.Ordinal));

    private static bool MaPolskieLitery(string tekst) =>
        tekst.IndexOfAny(LiteryPolskie) >= 0;

    // `(plik, wiersz, tekst szablonu bez dziur)` dla każdego wywołania `GD.Print`
    // w `src/Game/`. Czyta po źródle BEZ komentarzy i bez literałów innych niż
    // argument — `GD.Print` w komentarzu nie jest wypisem.

    // --- 6.D217: droga błędu — ilu wołających `Abort` i w jakim języku piszą ---------
    //
    // **Skąd ten blok.** 6.D202 policzyło język LOGU PRZEJAZDU (`GD.Print`) i drogi błędu
    // nie objęło ani razu — to własność jego pytania, nie przeoczenie. Ta pozycja liczy
    // drugą drogę: tę, którą gracz zobaczy, gdy gra się nie uruchomi.
    //
    // **Tekst obcy wchodzi tu WYŁĄCZNIE interpolacją, nigdy literałem** — zmierzone,
    // nie założone. Literałów angielskich w drodze błędu jest ZERO; angielszczyzna
    // przychodzi z dziur, a wszystkie dziury z tekstem obcym niosą **jeden typ**:
    // `Error` Godota (`FileAccess.GetOpenError()`, wynik `DirAccess.MakeDir`, wynik
    // `GltfDocument.AppendFromFile`). Przetłumaczyć się ich nie da bez mapy nazw,
    // czyli bez decyzji, której w `docs/` nie ma (§8).

    /// <summary>Wołający <c>Abort</c> w <c>src/Game/</c> — bez samej deklaracji.</summary>
    /// <remarks>
    /// Deklaracja odsiewana jest po <b>modyfikatorze dostępu</b>, tak samo jak w 6.D211
    /// i z tego samego powodu: sito po samej nazwie bierze wywołanie za deklarację
    /// i odwrotnie. `Abort` ma dziś deklarację w `FirstRun.cs:568` i 21 wywołań.
    /// <para><b>Odsiew jest JEDEN, i to jest poprawka z kontroli negatywnej.</b> Pierwsza
    /// wersja miała dwa naraz — wyprzedzenie ujemne <c>(?&lt;!private\svoid\s)</c> we
    /// wzorcu ORAZ ten warunek — więc KN-1 (zdjęcie warunku) wyszła ZIELONA i czytała się
    /// jako „bramka tego nie łapie". Łapała, tylko drugim mechanizmem. Wyprzedzenie
    /// poszło, bo było węższe: wypisywało <c>private void</c> z nazwy i przepuściłoby
    /// deklarację <c>private static void</c> albo <c>internal</c>.</para>
    /// </remarks>
    private static List<(string Plik, int Wiersz, string Szablon, List<string> Dziury)>
        WolajacyAbort() =>
        Wywolania(@"(?<!\w)Abort\s*\(")
            .Where(w => !DeklaracjaAbort(w.Plik, w.Wiersz))
            .ToList();

    private static bool DeklaracjaAbort(string plik, int wiersz)
    {
        var sciezka = PlikiGryZKatalogiem().Single(p => Path.GetFileName(p) == plik);
        var wiersze = File.ReadAllLines(sciezka);
        return Regex.IsMatch(wiersze[wiersz - 1],
            @"^\s*(?:public|private|protected|internal)\b[^(]*\bAbort\s*\(");
    }

    /// <summary>Cała droga błędu: <c>Abort</c> oraz oba wypisy błędu poza nim.</summary>
    private static List<(string Skad, string Plik, int Wiersz, string Szablon, List<string> Dziury)>
        DrogaBledu()
    {
        var wynik = WolajacyAbort()
            .Select(w => ("Abort", w.Plik, w.Wiersz, w.Szablon, w.Dziury))
            .ToList();
        foreach (var nazwa in new[] { "GD.PrintErr", "GD.PushError" })
        {
            wynik.AddRange(Wywolania(Regex.Escape(nazwa) + @"\s*\(")
                // Dwa wypisy stoją W ŚRODKU `Abort` i niosą jego argument, nie własny
                // literał — liczenie ich osobno podwoiłoby każdy komunikat drogi.
                .Where(w => w.Szablon.Trim().Length > 0 || w.Dziury.Count > 0)
                .Select(w => (nazwa, w.Plik, w.Wiersz, w.Szablon, w.Dziury)));
        }

        return wynik;
    }

    //: Ilu wołających ma `Abort` (bez deklaracji) i ile wypisów błędu stoi poza nim.
    //: Zmierzone 15.09.2026: 21 i 5 (`GD.PrintErr` 2, `GD.PushError` 3). Pole „Skąd"
    //: pozycji mówiło `GD.PrintErr` 3 i `GD.PushError` 4 — te liczby są z WYWOŁANIAMI
    //: WEWNĄTRZ `Abort`, które niosą jego argument, a nie własny literał.
    //: 21 -> 26 (22.09.2026, 6.D235): pięciu wołających — osłony pliku ZŁEGO, po dwie
    //: klauzule przy osi i przy manifeście chunków, jedna nowa przy planie sygnalizacji.
    // 26 -> 27 (24.09.2026): brak generowanej tablicy zatrzymuje uruchomienie.
    private const int WolajacychAbort = 27;
    // 5 -> 6 (24.09.2026, interaktywne R): błąd przeładowania poza Abort.
    private const int WypisowBleduPozaAbort = 6;

    /// <summary>
    /// Dziury drogi błędu niosące tekst <b>obcy</b>, każda z wytwórcą. Zbiór, nie liczba
    /// — 6.D131: liczba przechodzi po podbiciu cyfry, zbiór mówi, KTÓRE.
    /// </summary>
    /// <remarks>
    /// <b>Kluczem jest PARA (plik, wyrażenie), a nie samo wyrażenie — i to jest poprawka
    /// z pomiaru, nie ostrożność.</b> Dziura `{error}` stoi w drodze błędu DWA RAZY
    /// i za każdym razem znaczy co innego: w `GlbLoader.cs:39` jest to `Error` Godota
    /// z `AppendFromFile` (tekst OBCY), a w `FirstRun.cs:1089` out-param
    /// `TelemetryTrack.TryParse` (tekst WŁASNY). Pierwsza wersja tej bramki kluczowała
    /// po samej nazwie i policzyła dziewięć dziur obcych jako dziesięć — dokładnie ta
    /// sama pomyłka, którą 6.D213 zmierzyło na `string status`.
    /// </remarks>
    private static readonly (string Plik, string Wyrazenie, string Wytworca)[] ZrodlaTekstuObcego =
    {
        ("FirstRun.cs", "FileAccess.GetOpenError()", "Error Godota — wynik otwarcia pliku"),
        ("FirstRun.cs", "blad", "Error Godota — wynik DirAccess.MakeDir"),
        ("GlbLoader.cs", "error", "Error Godota — wynik GltfDocument.AppendFromFile"),
    };

    /// <summary>
    /// Dziury drogi błędu niosące tekst <b>własny</b>, każda z wytwórcą. Rozdzielenie
    /// tych dwóch zbiorów jest całym pytaniem pozycji: tylko o drugi da się cokolwiek
    /// rozstrzygnąć, bo pierwszy pisze silnik.
    /// </summary>
    private static readonly (string Plik, string Wyrazenie, string Wytworca)[] ZrodlaTekstuWlasnego =
    {
        ("FirstRun.cs", "error.Message", "wyjątek z `src/Sim/` — filtr `when (error is "
            + "ArgumentException or FormatException)` wpuszcza WYŁĄCZNIE nasze typy, "
            + "a nasze rzuty są polskie"),
        ("FirstRun.cs", "error", "out-param `TelemetryTrack.TryParse` (FirstRun.cs:1089)"),
        ("FirstRun.cs", "availability.Reason",
            "`ViewAssumption.Reason` z `src/Game/DesignAssumptions.cs`"),
    };

    /// <summary>
    /// Miejsca drogi błędu <b>bez własnych słów</b>, każde z wytwórcą do sprawdzenia.
    /// Dwa, i są DWÓCH RÓŻNYCH RODZAJÓW — dlatego stoją z powodem, a nie jako liczba.
    /// </summary>
    private static readonly (string Plik, string Znacznik, string Powod)[] DrogaBezWlasnychSlow =
    {
        ("FirstRun.cs", "[ARGUMENT]",
            "`Abort(plan.ExitCode, plan.Error!)` — nie ma ŻADNEGO literału; treść "
            + "przychodzi z `RunPlan.Refusal`, którego wołających jest 26"),
        ("GlbLoader.cs", "AppendFromFile",
            "literał JEST, ale jego jedyne słowo to nazwa metody Godota — po polsku "
            + "ani po angielsku nie jest, bo nie jest zdaniem"),
    };

    [TestMethod]
    public void Droga_bledu_ZAWIERA_Abort_a_kazdy_jej_komunikat_ze_slowami_jest_po_polsku()
    {
        var droga = DrogaBledu();

        // KONTROLA PRZYRZĄDU, o którą prosiło pole „Weryfikacja" pozycji wprost:
        // „lista zawiera `Abort` — jeśli nie zawiera, skan nie widzi drogi, którą
        // 6.D202 wskazało palcem". Bez niej wszystkie liczby niżej mogłyby opisywać
        // zbiór, w którym drogi błędu nie ma w ogóle (rodzina 6.D159).
        Assert.IsTrue(droga.Any(w => w.Skad == "Abort"),
            "skan NIE ZNAJDUJE ani jednego wołającego `Abort` — to ta droga, o którą "
            + "pyta 6.D217, i bez niej pozostałe asercje są o czym innym");

        var abort = droga.Where(w => w.Skad == "Abort").ToList();
        Assert.AreEqual(WolajacychAbort, abort.Count,
            $"wołających `Abort` jest {abort.Count}, a zmierzono {WolajacychAbort} — "
            + "jeżeli doszła deklaracja, sito po modyfikatorze dostępu przestało "
            + "działać (6.D211): " + string.Join(", ", abort.Select(w => $"{w.Plik}:{w.Wiersz}")));
        Assert.AreEqual(WypisowBleduPozaAbort, droga.Count - abort.Count,
            $"wypisów błędu poza `Abort` jest {droga.Count - abort.Count}, "
            + $"a zmierzono {WypisowBleduPozaAbort}");

        var zeSlowami = droga
            .Where(w => Regex.IsMatch(w.Szablon, @"\p{L}{2,}"))
            .Where(w => !DrogaBezWlasnychSlow.Any(b => b.Plik == w.Plik
                && w.Szablon.Contains(b.Znacznik, StringComparison.Ordinal)))
            .ToList();
        foreach (var w in zeSlowami)
        {
            Assert.IsTrue(WygladaPoPolsku(w.Szablon),
                $"`{w.Plik}:{w.Wiersz}` nie ma ani polskich liter, ani znanego słowa "
                + $"polskiego bez znaków: „{w.Szablon.Trim()}”. Droga błędu jest tą, "
                + "którą czyta ten, komu gra się NIE uruchomiła — nierozpoznany język "
                + "jest tam droższy, nie tańszy (6.D217)");
        }

        // **Literałów angielskich w drodze błędu jest ZERO i to jest zdanie o drzewie,
        // nie życzenie.** Angielszczyzna wchodzi tu wyłącznie interpolacją — pilnują
        // tego dwa testy niżej, każdy o innym zbiorze dziur.
        Assert.IsTrue(zeSlowami.Count >= 18,
            $"komunikatów z własnymi słowami jest {zeSlowami.Count} — poniżej osiemnastu "
            + "znaczy, że czytnik przestał czytać, a nie że droga błędu zmalała");
    }

    [TestMethod]
    public void Zrodla_tekstu_OBCEGO_i_WLASNEGO_sa_wymienione_Z_NAZWY_i_rozdzielone()
    {
        var dziury = DrogaBledu()
            .SelectMany(w => w.Dziury.Select(d => (w.Plik, w.Wiersz, Dziura: d.Split(':')[0].Trim())))
            .ToList();

        // Dziura, która NIE jest ani ścieżką, ani liczbą, ani własnym identyfikatorem
        // drzewa, musi stać na jednej z dwóch list — z wytwórcą. Rozdzielenie jest całym
        // pytaniem pozycji: o tekst z silnika nie da się rozstrzygnąć nic.
        var nazwane = ZrodlaTekstuObcego.Select(z => z.Plik + "|" + z.Wyrazenie)
            .Concat(ZrodlaTekstuWlasnego.Select(z => z.Plik + "|" + z.Wyrazenie))
            .ToHashSet(StringComparer.Ordinal);

        var obce = dziury
            .Where(d => ZrodlaTekstuObcego.Any(z => z.Plik == d.Plik && z.Wyrazenie == d.Dziura))
            .ToList();
        Assert.AreEqual(9, obce.Count,
            $"dziur z tekstem OBCYM jest {obce.Count}, a zmierzono 9 (siedem "
            + "`FileAccess.GetOpenError()`, jedna z `MakeDir`, jedna z `AppendFromFile`): "
            + string.Join(", ", obce.Select(d => $"{d.Plik}:{d.Wiersz} {d.Dziura}")));

        // ZBIÓR, nie liczba (6.D131): gdyby doszedł czwarty wytwórca tekstu obcego,
        // liczba 9 podniesiona o jeden nie powiedziałaby, KTÓRY.
        CollectionAssert.AreEqual(
            new[] { "Error Godota — wynik DirAccess.MakeDir",
                    "Error Godota — wynik GltfDocument.AppendFromFile",
                    "Error Godota — wynik otwarcia pliku" },
            ZrodlaTekstuObcego.Select(z => z.Wytworca).OrderBy(x => x, StringComparer.Ordinal).ToArray(),
            "zbiór wytwórców tekstu obcego się zmienił — dziś wszystkie trzy to JEDEN typ "
            + "(`Error` Godota) i to jest treść tej pozycji: tekstu z silnika nie da się "
            + "przetłumaczyć bez mapy nazw, czyli bez decyzji, której w `docs/` nie ma");

        foreach (var (plik, wyrazenie, wytworca) in ZrodlaTekstuWlasnego)
        {
            Assert.IsTrue(dziury.Any(d => d.Plik == plik && d.Dziura == wyrazenie),
                $"dziury `{wyrazenie}` nie ma już w drodze błędu, a lista mówi o drzewie "
                + $"sprzed zmiany ({wytworca})");
        }

        Assert.IsTrue(nazwane.Count == 6,
            $"list jest razem {nazwane.Count} pozycji zamiast sześciu — dopisanie wytwórcy "
            + "do jednej listy bez drugiej rozdziela zbiory po cichu");
    }

    [TestMethod]
    public void Komunikat_BEZ_WLASNYCH_SLOW_prowadzi_do_wytworcy_ktory_pisze_po_polsku()
    {
        // Bez tego „dwa bez słów" czytałoby się jako „dwa nieznanego języka" — ta sama
        // różnica, którą 6.D202 nazwało dla czterech wierszy logu.
        var refusal = File.ReadAllText(Path.Combine(
            MetroBxl.Tests.Shared.KorzenRepozytorium.Sciezka, "src", "Game", "RunPlan.cs"));
        var czysty = KodLeksykalnie(refusal);
        var wolan = Regex.Matches(czysty, @"return Refusal\s*\(").Count;
        Assert.AreEqual(26, wolan,
            $"wołających `RunPlan.Refusal` jest {wolan}, a zmierzono 26 — to ONE są "
            + "treścią jedynego wywołania `Abort` bez własnego literału "
            + "(`FirstRun.cs:533`), więc ich liczba jest zdaniem o drodze błędu");

        var literaly = Literaly(refusal)
            .Where(l => l.Contains("[ARGUMENT]", StringComparison.Ordinal))
            .ToList();
        Assert.IsTrue(literaly.Count >= 19,
            $"literałów `[ARGUMENT]` w `RunPlan.cs` jest {literaly.Count} — poniżej "
            + "dziewiętnastu znaczy, że czytnik przestał czytać");
        foreach (var l in literaly)
        {
            Assert.IsTrue(WygladaPoPolsku(l),
                "literał `[ARGUMENT]` w `RunPlan.cs` nie wygląda po polsku, więc "
                + "komunikat, który gracz zobaczy zamiast uruchomionej gry, przestał "
                + $"być polski: „{l}”");
        }
    }

    private static List<(string Plik, int Wiersz, string Szablon)> WierszeLogu() =>
        Wywolania(@"GD\.Print\s*\(")
            .Select(w => (w.Plik, w.Wiersz, w.Szablon))
            .ToList();

    /// <summary>
    /// <c>(plik, wiersz, szablon bez dziur, treść dziur)</c> dla każdego wywołania
    /// pasującego do <paramref name="wzorzecWywolania"/> w <c>src/Game/</c>.
    /// </summary>
    /// <remarks>
    /// <para><b>Wydzielone z <c>WierszeLogu</c> przy 6.D217, a nie napisane obok.</b>
    /// Droga błędu potrzebuje dokładnie tego samego czytania — po źródle bez komentarzy
    /// i bez literałów innych niż argument — i różni się WYŁĄCZNIE nazwą wywołania.
    /// Druga kopia rozjechałaby się przy pierwszej poprawce, a 6.D213 usunęło już jedną
    /// taką kopię w tym pliku.</para>
    /// <para><b>Dziury są zwracane osobno i to jest treść, nie wygoda:</b> tekst obcy
    /// wchodzi do tej drogi WYŁĄCZNIE interpolacją, nigdy literałem, więc pytanie „skąd
    /// ten angielski" nie ma odpowiedzi w szablonie — tylko w dziurze.</para>
    /// </remarks>
    private static List<(string Plik, int Wiersz, string Szablon, List<string> Dziury)>
        Wywolania(string wzorzecWywolania)
    {
        var wynik = new List<(string, int, string, List<string>)>();
        foreach (var sciezka in PlikiGryZKatalogiem())
        {
            var kod = File.ReadAllText(sciezka);
            var czysty = KodLeksykalnie(kod);
            foreach (Match m in Regex.Matches(czysty, wzorzecWywolania))
            {
                var otwarcie = czysty.IndexOf('(', m.Index + m.Length - 1);
                var glebia = 0;
                var koniec = otwarcie;
                while (koniec < czysty.Length)
                {
                    if (czysty[koniec] == '(')
                    {
                        glebia++;
                    }
                    else if (czysty[koniec] == ')')
                    {
                        glebia--;
                        if (glebia == 0)
                        {
                            break;
                        }
                    }

                    koniec++;
                }

                var argument = kod.Substring(otwarcie + 1, koniec - otwarcie - 1);
                var literaly = Literaly(argument);
                var szablon = string.Join(" ", literaly
                    .Select(l => Regex.Replace(l, @"\{[^{}]*\}", " ")));
                var dziury = literaly
                    .SelectMany(l => Regex.Matches(l, @"\{([^{}]*)\}")
                        .Select(d => d.Groups[1].Value))
                    .ToList();
                var wiersz = kod.Substring(0, m.Index).Count(z => z == '\n') + 1;
                wynik.Add((Path.GetFileName(sciezka), wiersz, szablon, dziury));
            }
        }

        return wynik;
    }

    [TestMethod]
    public void W_jakim_jezyku_jest_log_przejazdu_i_ile_wierszy_nie_ma_wlasnych_slow()
    {
        var wiersze = WierszeLogu();
        Assert.AreEqual(WierszyLoguWGame, wiersze.Count,
            $"wywołań `GD.Print` w `src/Game/` jest {wiersze.Count}, a zmierzono "
            + $"{WierszyLoguWGame}");

        var bezSlow = wiersze
            .Where(w => !Regex.IsMatch(w.Szablon, @"\p{L}{2,}"))
            .ToList();
        Assert.AreEqual(WytworcyWierszaBezSlow.Length, bezSlow.Count,
            $"wierszy bez własnych słów jest {bezSlow.Count}, a wytwórców wpisano "
            + $"{WytworcyWierszaBezSlow.Length}: "
            + string.Join(", ", bezSlow.Select(w => $"{w.Plik}:{w.Wiersz}")));

        var zeSlowami = wiersze.Except(bezSlow).ToList();
        var poPolsku = zeSlowami.Where(w => MaPolskieLitery(w.Szablon)).ToList();
        var reszta = zeSlowami.Except(poPolsku).ToList();

        // DWA WIERSZE NIE MAJĄ POLSKICH LITER, A POLSKIE SĄ — `[STACJA]` i `[ZRZUT]
        // metadane`. Dlatego sam znak diakrytyczny NIE jest tu kryterium języka,
        // tylko pierwszym sitem; drugim jest lista słów, które po angielsku nie
        // istnieją. Bez tego rozróżnienia bramka meldowałaby dwa wiersze angielskie
        // i pytanie do właściciela stałoby na liczbie nieprawdziwej.
        foreach (var w in reszta)
        {
            Assert.IsTrue(WygladaPoPolsku(w.Szablon),
                $"`{w.Plik}:{w.Wiersz}` nie ma ani polskich liter, ani znanego słowa "
                + $"polskiego bez znaków: „{w.Szablon.Trim()}”. Jeśli to wiersz "
                + "ANGIELSKI, `WierszyLoguPoAngielsku` przestało być zerem i pytanie "
                + "do właściciela stoi na innej liczbie niż w dniu pomiaru (6.D202)");
        }

        Assert.AreEqual(WierszyLoguPoPolsku, zeSlowami.Count,
            $"wierszy z własnymi słowami jest {zeSlowami.Count}, a zmierzono "
            + $"{WierszyLoguPoPolsku} — i WSZYSTKIE są polskie");
        Assert.AreEqual(WierszyLoguPoAngielsku, 0,
            "ta stała ma być zerem, dopóki asercja wyżej nie zapali się na wierszu, "
            + "którego nie da się uznać za polski");

        // CZYTNIK LEKSYKALNY JEST DZIŚ BEZCZYNNY I TO JEST TU SPRAWDZANE, NIE
        // PRZEMILCZANE. Zmierzone: w `src/Game/` `GD.Print` stoi 25 razy w źródle
        // surowym i 25 razy po zdjęciu komentarzy i literałów — ani jednego w prozie.
        // Kontrola negatywna czytająca źródło surowe wychodzi przez to ZIELONA i tak
        // ma być, bo nie ma czego zdjąć. **Mechanizm nie jest przy tym teoretyczny:**
        // w `src/Sim.Runner/Program.cs` `GD.Print` W PROZIE stoi — tylko że tamten plik
        // jest poza korpusem tej pozycji. Ta asercja powie, kiedy przyjdzie tutaj.
        var surowo = PlikiGryZKatalogiem()
            .Sum(s => Regex.Matches(File.ReadAllText(s), @"GD\.Print\s*\(").Count);
        Assert.AreEqual(wiersze.Count, surowo,
            $"skan po źródle surowym daje {surowo} wywołań `GD.Print`, a po zdjęciu "
            + $"komentarzy i literałów — {wiersze.Count}. Znaczy to, że w `src/Game/` "
            + "pojawiło się `GD.Print` w prozie: czytnik leksykalny przestał być "
            + "bezczynny i od teraz jego zdjęcie ZMIENIA wynik (6.D202)");

        // KONTROLA PRZYRZĄDU: skan MA znaleźć wiersz, który 6.D188 pokazało palcem —
        // ten z założeniem widoku. Bez niej wszystkie liczby wyżej mogłyby opisywać
        // zbiór, w którym tego wiersza nie ma (rodzina 6.D159).
        Assert.IsTrue(wiersze.Any(w => w.Szablon.Contains("ZAŁOŻENIE widok",
                StringComparison.Ordinal)),
            "skan NIE ZNAJDUJE wiersza `[ZAŁOŻENIE widok]`, czyli tego, o który ta "
            + "pozycja pyta: " + string.Join(", ", wiersze.Select(w => w.Plik + ":" + w.Wiersz)));
    }

    [TestMethod]
    public void Kazdy_wiersz_BEZ_WLASNYCH_SLOW_prowadzi_do_wytworcy_ktory_pisze_po_polsku()
    {
        // Bez tego „cztery bez słów" czytałoby się jako „cztery nieznanego języka",
        // a to jest różnica między zerem wierszy angielskich a czterema niewiadomymi.
        var sprawdzonych = 0;
        foreach (var wpis in WytworcyWierszaBezSlow)
        {
            var czesci = wpis.Split(':');
            var plik = czesci[0];
            var znacznik = czesci[1];
            var sciezka = PlikiGryZKatalogiem()
                .SingleOrDefault(p => Path.GetFileName(p) == plik);
            Assert.IsNotNull(sciezka, $"nie ma pliku `{plik}` — wytwórca zniknął albo "
                + "przeniósł się, a lista mówi o drzewie sprzed zmiany");

            var kod = KodLeksykalnie(File.ReadAllText(sciezka!));
            var literaly = Literaly(File.ReadAllText(sciezka!));
            var zZnacznikiem = literaly
                .Where(l => l.Contains(znacznik, StringComparison.Ordinal))
                .ToList();
            Assert.IsTrue(zZnacznikiem.Count > 0,
                $"w `{plik}` nie ma literału ze znacznikiem `{znacznik}` — wiersz logu "
                + "zmienił znacznik albo wytwórcę");
            Assert.IsTrue(zZnacznikiem.Any(WygladaPoPolsku),
                $"literał `{znacznik}` w `{plik}` NIE MA polskich liter — wytwórca "
                + "wiersza bez własnych słów przestał pisać po polsku, a to znaczy, "
                + $"że `WierszyLoguPoAngielsku = {WierszyLoguPoAngielsku}` jest "
                + "nieprawdą: " + string.Join(" | ", zZnacznikiem));
            sprawdzonych++;
        }

        Assert.AreEqual(WytworcyWierszaBezSlow.Length, sprawdzonych,
            $"pętla po wytwórcach wykonała się {sprawdzonych} razy zamiast "
            + $"{WytworcyWierszaBezSlow.Length} — wtedy asercje wyżej nie sprawdzają "
            + "wszystkich (rodzina 6.D193)");
    }

    [TestMethod]
    public void Ile_angielskich_IDENTYFIKATOROW_dociera_do_logu_i_skad()
    {
        // **To jest jedyna angielszczyzna w całym logu przejazdu** i jedyna rzecz,
        // o której jest sens pytać właściciela. Wszystkie przychodzą przez `nameof(...)`
        // w polu `Name` założenia — czyli są IDENTYFIKATORAMI, nie prozą. Ten sam
        // kształt, co przy 6.D185 (nazwa członu wyliczenia na HUD-zie).
        var nameof_ow = 0;
        foreach (var sciezka in PlikiZrodlowe())
        {
            var kod = KodLeksykalnie(File.ReadAllText(sciezka));
            nameof_ow += Regex.Matches(kod,
                @"new\s+(?:View|Scenario)Assumption\s*\(\s*nameof\s*\(").Count;
        }

        Assert.AreEqual(IdentyfikatorowNameofWZalozeniach, nameof_ow,
            $"założeń z nazwą z `nameof(...)` jest {nameof_ow}, a zmierzono "
            + $"{IdentyfikatorowNameofWZalozeniach}. Każde z nich wypisuje do logu "
            + "ANGIELSKI IDENTYFIKATOR w polskim wierszu (6.D202)");

        // RÓŻNICĄ, a nie osobnym wzorcem z zaprzeczeniem: `\s*(?!nameof)` przechodzi
        // przez nawrót — `\s*` oddaje jeden znak białej spacji i zaprzeczenie patrzy
        // na spację zamiast na słowo. Pierwsza wersja tej asercji dała przez to 7
        // zamiast 2, czyli WSZYSTKIE założenia. Różnica dwóch liczonych osobno nie
        // ma tej pułapki.
        var wszystkich = 0;
        foreach (var sciezka in PlikiZrodlowe())
        {
            var kod = KodLeksykalnie(File.ReadAllText(sciezka));
            wszystkich += Regex.Matches(kod,
                @"new\s+(?:View|Scenario)Assumption\s*\(").Count;
        }

        var literalem = wszystkich - nameof_ow;
        Assert.AreEqual(IdentyfikatorowLiteralemWZalozeniach, literalem,
            $"założeń z nazwą podaną LITERAŁEM jest {literalem}, a zmierzono "
            + $"{IdentyfikatorowLiteralemWZalozeniach}. Ta droga NIE IDZIE za zmianą "
            + "nazwy pola — przemianowanie stałej zostawi w logu nazwę starą, cicho "
            + "(6.D202)");

        // I DRUGA STRONA, bez której liczba wyżej nie mówi, co jest po polsku:
        // szablon `ViewAssumption.ToString()` NIE MA ANI JEDNEGO SŁOWA. Angielszczyzna
        // jest w DANYCH, a nie w szablonie — i na tym polega poprawka przesłanki.
        var szablon = PlikiZrodlowe()
            .Where(p => Path.GetFileName(p) == "DesignAssumptions.cs")
            .SelectMany(p => Literaly(File.ReadAllText(p)))
            .Where(l => l.Contains("{Name}", StringComparison.Ordinal))
            .ToList();
        Assert.AreEqual(1, szablon.Count,
            "szablonu `{Name} …` w `DesignAssumptions.cs` jest " + szablon.Count
            + " zamiast jednego — wtedy zdanie o „braku słów” opisuje inny szablon");
        Assert.IsFalse(Regex.IsMatch(Regex.Replace(szablon[0], @"\{[^{}]*\}", " "),
                @"\p{L}{2,}"),
            $"szablon założenia MA teraz własne słowa: „{szablon[0]}”. Przesłanka "
            + "6.D202 mówiła, że jest po angielsku, a pomiar 13.09.2026 dał ZERO słów "
            + "— jeśli słowa doszły, trzeba na nowo rozstrzygnąć, w jakim są języku");
    }
}
