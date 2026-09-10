using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.RegularExpressions;
using MetroBxl.Game.Input;
using MetroBxl.Game.UI;
using MetroBxl.Sim.Train;
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
    /// </summary>
    private static readonly string[] NazwyKlawiszy = { "Esc" };

    /// <summary>Metody <c>FirstRun.cs</c>, które 6.D99 wyczyściło ze słów.</summary>
    private static readonly string[] MetodyFirstRun =
    {
        "private string StationLine()",
        "private static string Faza(DoorPhase phase)",
        "private string HelpLine()",
    };

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

    private static List<string> SlowaWKodzie(string kod)
    {
        var zle = new List<string>();
        foreach (var literal in Literaly(kod))
        {
            if (literal.Contains('/', StringComparison.Ordinal))
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

            if (Regex.IsMatch(BezDziur(literal), @"\p{L}{2,}"))
            {
                zle.Add(literal);
            }
        }

        return zle;
    }

    [TestMethod]
    public void W_metodach_HUD_nie_ma_ani_jednego_literalu_jezykowego()
    {
        var zle = SlowaWKodzie(KodBezKomentarzy(HudSource()));

        Assert.AreEqual(0, zle.Count,
            "w `Hud.cs` stoi literał językowy zamiast klucza katalogu: "
            + string.Join(" | ", zle.Select(z => $"\"{z}\"")));
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
                $"w `{naglowek}` stoi literał językowy zamiast klucza katalogu: "
                + string.Join(" | ", zle.Select(z => $"\"{z}\"")));
        }
    }

    [TestMethod]
    public void W_plikach_sterowania_nie_ma_ani_jednego_slowa()
    {
        foreach (var plik in new[] { "DriverActions.cs", "EmergencyBrake.cs" })
        {
            var zle = SlowaWKodzie(
                KodBezKomentarzy(Zrodlo("src", "Game", "Input", plik)));
            Assert.AreEqual(0, zle.Count,
                $"w `{plik}` stoi literał językowy zamiast klucza katalogu: "
                + string.Join(" | ", zle.Select(z => $"\"{z}\"")));
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
}
