using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.RegularExpressions;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace MetroBxl.Sim.Tests;

/// <summary>
/// Ramiona domyślne switchy po wartości wyliczeniowej w <c>src/Sim/</c> — 6.D210.
///
/// <para><b>Co ta pozycja zmierzyła i dlaczego NIE przybiła podziału postaci.</b>
/// 6.D197 zmierzyło 13.09.2026 dwanaście switchy i zgodność co do jednego wystąpienia:
/// osiem wyrażeniowych, wszystkie z ramieniem <b>rzucającym</b> i wszystkie
/// <b>martwe</b>; cztery instrukcyjne, wszystkie z <c>default: break;</c> i wszystkie
/// <b>żywe</b>. Wyglądało to na regułę projektu.</para>
///
/// <para><b>Dzień później para „postać ↔ martwota" już się rozeszła.</b> MB-08 dołożyło
/// dwa switche wyrażeniowe, a jeden z nich — <c>StationStop.NextManualPhase</c> —
/// pokrywa <b>5 z 7</b> członów <c>DoorPhase</c> i rzuca dla pozostałych dwóch
/// świadomie („Ta faza nie kończy się z upływem czasu"). Jest więc wyrażeniowy,
/// rzucający i <b>ŻYWY</b> — kombinacja, której 13.09.2026 w drzewie nie było.
/// Zapadka na tamtym podziale kazałaby dziś albo ją podnieść, albo przepisać regułę,
/// a chroniłaby przed niczym nazwanym. Podział zostaje więc <b>zapisany</b>, nie
/// przybity — tak jak przy 6.D197.</para>
///
/// <para><b>Przybita jest jedna rzecz, i to taka, którą da się nazwać:</b> ramię
/// domyślne, które jest <b>jednocześnie CICHE i MARTWE</b>. Cichy filtr przy pełnym
/// pokryciu nie filtruje niczego — a gdy ktoś dopisze człon do wyliczenia, ten sam
/// filtr połknie go bez słowa. Dziś takich ramion jest <b>zero</b>, więc bramka stoi
/// na zbiorze pustym i sama z siebie nic nie znaczy (6.D27); dlatego obok niej stoi
/// kontrola przyrządu na wejściu syntetycznym, która żąda, żeby klasyfikator trafił
/// we wszystkie cztery kombinacje (cisza × martwota).</para>
///
/// <para>Rozkład zmierzony 14.09.2026: 14 switchy, 10 wyrażeniowych (10 rzucających)
/// i 4 instrukcyjne (4 ciche); 9 martwych i 5 żywych.</para>
/// </summary>
[TestClass]
public sealed class DefaultArmAuditTests
{
    /// <summary>Podłoga na liczbę znalezionych switchy — zero znaczy zepsuty skan.</summary>
    private const int MinimumSwitches = 10;

    private sealed record Ramie(string Plik, string Wyliczenie, int Pokrytych, int Czlonow,
                                bool Ciche, bool Wyrazeniowy)
    {
        public bool Martwe => Pokrytych == Czlonow && Czlonow > 0;
    }

    private static readonly Regex Wyliczenie = new(
        @"enum\s+(\w+)\s*\{(.*?)\n\}", RegexOptions.Singleline);

    private static readonly Regex Czlon = new(
        @"^\s{4}([A-Z]\w*)\s*(?:=[^,]+)?,\s*$", RegexOptions.Multiline);

    /// <summary>Etykieta ramienia wyrażeniowego: <c>Typ.Czlon =></c> na początku wiersza.</summary>
    private static readonly Regex EtykietaWyrazeniowa = new(
        @"^\s*([A-Z]\w+)\.([A-Z]\w+)\s*(?:when\b[^=]*)?=>", RegexOptions.Multiline);

    /// <summary>Etykieta ramienia instrukcyjnego: <c>case Typ.Czlon:</c>.</summary>
    private static readonly Regex EtykietaInstrukcyjna = new(
        @"^\s*case\s+([A-Z]\w+)\.([A-Z]\w+)\s*:", RegexOptions.Multiline);

    private static readonly Regex RamieDomyslne = new(
        @"^\s*(?:_|default)\s*(?:=>|:)\s*(.*)$", RegexOptions.Multiline);

    [TestMethod]
    public void Zadne_ramie_domyslne_w_rdzeniu_nie_jest_jednoczesnie_ciche_i_martwe()
    {
        var znalezione = Zebrane();
        Assert.IsTrue(znalezione.Count >= MinimumSwitches,
            $"switchy po wyliczeniu znaleziono {znalezione.Count} przy podłodze " +
            $"{MinimumSwitches} — skan oślepł albo rdzeń się skurczył, a zero odpowiada " +
            "tak samo jak skan widzący");

        var cicheIMartwe = znalezione.Where(r => r.Ciche && r.Martwe).ToList();
        Assert.AreEqual(0, cicheIMartwe.Count,
            "ramię domyślne CICHE przy PEŁNYM pokryciu członów: " +
            string.Join(" | ", cicheIMartwe.Select(r => $"{r.Plik} ({r.Wyliczenie})")) +
            " — filtr, który nic nie odsiewa, a po dopisaniu członu połknie go bez słowa");
    }

    [TestMethod]
    public void Klasyfikator_trafia_we_wszystkie_cztery_kombinacje_ciszy_i_martwoty()
    {
        // Bez tej kontroli zero wyżej znaczyłoby tyle, co przyrząd, który je wypisał:
        // klasyfikator niewidzący ciszy odpowiedziałby „zero" tak samo, jak widzący.
        // Wejście jest syntetyczne, bo kombinacji „ciche i martwe" w drzewie NIE MA.
        const string wyliczenie = "public enum Proba\n{\n    Jeden,\n    Dwa,\n}\n";

        var przypadki = new (string Kod, bool Ciche, bool Martwe)[]
        {
            ("switch (x)\n{\n    case Proba.Jeden:\n    case Proba.Dwa:\n        break;\n    default:\n        break;\n}\n", true, true),
            ("switch (x)\n{\n    case Proba.Jeden:\n        break;\n    default:\n        break;\n}\n", true, false),
            ("x switch\n{\n    Proba.Jeden => 1,\n    Proba.Dwa => 2,\n    _ => throw new ArgumentOutOfRangeException(),\n}\n", false, true),
            ("x switch\n{\n    Proba.Jeden => 1,\n    _ => throw new ArgumentOutOfRangeException(),\n}\n", false, false),
        };

        foreach (var (kod, ciche, martwe) in przypadki)
        {
            var czlonow = Czlony(wyliczenie);
            var ramie = Sklasyfikuj("proba.cs", kod, czlonow);
            Assert.IsNotNull(ramie, $"klasyfikator nie zobaczył switcha w próbce:\n{kod}");
            Assert.AreEqual(ciche, ramie!.Ciche, $"cisza źle rozpoznana w próbce:\n{kod}");
            Assert.AreEqual(martwe, ramie.Martwe, $"martwota źle rozpoznana w próbce:\n{kod}");
        }
    }

    /// <summary>
    /// Człony, które ramię domyślne POŁYKA — po NAZWIE, nie po liczbie (6.D211).
    ///
    /// <para><b>Dlaczego nazwy, a nie liczba.</b> Pole „Czego NIE wolno przyjąć bez
    /// pomiaru" pozycji 6.D211 pyta wprost, czy zapadka równościowa na LICZBIE
    /// obsłużonych członów jest tu właściwą formą. Nie jest, i powód jest ten sam, który
    /// 6.D131 zapisało dla zapadek: liczba rośnie razem z wyliczeniem, więc jej
    /// podniesienie jest <b>cichym sposobem na połknięcie członu zmieniającego stan</b>.
    /// Nazwa tego nie pozwala — kto dopisuje człon, musi albo wpisać go tutaj razem
    /// z powodem, albo dołożyć ramię; jedno i drugie jest decyzją zapisaną.</para>
    ///
    /// <para><b>Wszystkie cztery filtry są ŚWIADOME i zadaniem NIE było ich naprawianie.</b>
    /// <c>Replay</c> odtwarza stan z dziennika, a zdarzenia czysto sprawozdawcze stanu
    /// nie zmieniają. Trzy filtry na <c>ProtectionAction</c> połykają <c>None</c>, czyli
    /// „nic nie rób" — ramię byłoby puste i tylko powtarzałoby domyślne.</para>
    ///
    /// <para>Zbiór porównywany jest W OBIE STRONY: człon dopisany do wyliczenia wchodzi
    /// do połykanych i zapala bramkę, a ramię dołożone do filtra wyjmuje go z połykanych
    /// i zapala ją tak samo. Stan zmierzony 14.09.2026: 7 z 17 członów
    /// <c>SignallingEventKind</c> w <c>Replay</c> i trzy razy 2 z 3 członów
    /// <c>ProtectionAction</c>.</para>
    /// </summary>
    private static readonly (string Plik, string Metoda, string Wyliczenie, string[] Polykane, string Powod)[]
        PolykaneCzlony =
    {
        ("src/Sim/Signalling/FixedBlockSystem.cs", "Replay", "SignallingEventKind",
            new[]
            {
                "AuthorityIssued", "AuthorityViolation", "DoorInhibit", "DoorRelease",
                "EmergencyIntervention", "OverspeedIntervention", "OverspeedWarning",
                "RouteRejected", "RouteRequested", "TrainDeregistered",
            },
            "zdarzenia sprawozdawcze — nie zmieniają stanu, który Replay odtwarza z dziennika"),
        ("src/Sim/Signalling/TrainProtection.cs", "Supervise", "ProtectionAction",
            new[] { "None" },
            "None znaczy „nic nie rób\" — ramię byłoby puste i tylko powtarzałoby domyślne"),
        ("src/Sim/Signalling/CabProtection.cs", "Supervise", "ProtectionAction",
            new[] { "None" },
            "None znaczy „nic nie rób\" — ramię byłoby puste i tylko powtarzałoby domyślne"),
        ("src/Sim/Line/LineCore.cs", "Step", "ProtectionAction",
            new[] { "None" },
            "None znaczy „nic nie rób\" — ramię byłoby puste i tylko powtarzałoby domyślne"),
    };

    [TestMethod]
    public void Kazdy_swiadomy_filtr_ma_polykane_czlony_wypisane_Z_NAZWY()
    {
        var root = FindRepositoryRoot();
        Assert.IsNotNull(root, "nie znaleziono korzenia repozytorium");

        var czlony = WszystkieCzlonyRdzenia(root!);
        var sprawdzonych = 0;

        foreach (var (plik, metoda, wyliczenie, polykane, powod) in PolykaneCzlony)
        {
            var sciezka = Path.Combine(root!, plik.Replace('/', Path.DirectorySeparatorChar));
            Assert.IsTrue(File.Exists(sciezka),
                $"{plik} nie istnieje — wpis opisuje plik, którego nie ma");
            Assert.IsTrue(czlony.ContainsKey(wyliczenie),
                $"wyliczenia {wyliczenie} nie ma już w rdzeniu — wpis o filtrze " +
                $"{plik}:{metoda} opisuje typ, którego nie ma");
            Assert.IsTrue(powod.Length > 20, $"{plik}:{metoda} — powód bez treści");

            var zrodlo = File.ReadAllText(sciezka);
            var korpusMetody =
                KorpusMetody(zrodlo, metoda, out var deklaracji, out var powodCzytnika);
            Assert.AreEqual(1, deklaracji,
                $"{plik}: deklaracji metody {metoda} znaleziono {deklaracji}, a wpis niżej " +
                "opisuje jedną — metoda zniknęła albo doszło przeciążenie");
            Assert.IsNotNull(korpusMetody,
                $"{plik}:{metoda} — czytnik korpusu ODMÓWIŁ: {powodCzytnika}");

            var obsluzone = ObsluzoneCzlony(korpusMetody!, wyliczenie);
            Assert.AreEqual(1, obsluzone.Count,
                $"{plik}:{metoda} — switchy instrukcyjnych po {wyliczenie} znaleziono " +
                $"{obsluzone.Count}, a wpis niżej opisuje jeden; zero znaczy oślepły " +
                "czytnik etykiet, a wtedy „połykane\" niżej nic nie znaczy");

            var faktycznie = czlony[wyliczenie]
                .Where(c => !obsluzone[0].Contains(c))
                .OrderBy(c => c, StringComparer.Ordinal)
                .ToList();
            var wypisane = polykane.OrderBy(c => c, StringComparer.Ordinal).ToList();

            CollectionAssert.AreEqual(wypisane, faktycznie,
                $"{plik}:{metoda} połyka dziś [{string.Join(", ", faktycznie)}], a wypisane " +
                $"są [{string.Join(", ", wypisane)}] — jeśli doszedł człon, wpisz go tutaj " +
                "razem z powodem ALBO dołóż ramię; podniesienie samej liczby byłoby cichym " +
                "połknięciem (6.D211)");
            sprawdzonych++;
        }

        Assert.AreEqual(PolykaneCzlony.Length, sprawdzonych,
            $"pętla po filtrach wykonała się {sprawdzonych} razy zamiast " +
            $"{PolykaneCzlony.Length} — pusta pętla przechodzi każdą regułę w środku");
    }

    [TestMethod]
    public void Czytnik_polykanych_reaguje_i_na_dolozony_czlon_i_na_dolozone_ramie()
    {
        // Kontrola przyrządu, nie drzewa: bez niej zieleń wyżej znaczyłaby tyle, co
        // czytnik, który ją wypisał. Czytnik ślepy na etykiety zgłosiłby jako „połykane"
        // CAŁE wyliczenie, a czytnik ślepy na nowy człon nie zgłosiłby go nigdy —
        // obie ślepoty zapala ta próbka, bo obie zmiany są tu wykonane naprawdę.
        const string trzyCzlony = "public enum Proba\n{\n    Alfa,\n    Beta,\n    Gamma,\n}\n";
        const string czteryCzlony =
            "public enum Proba\n{\n    Alfa,\n    Beta,\n    Gamma,\n    Delta,\n}\n";
        const string jednoRamie =
            "public void Filtr(Proba p)\n{\n    switch (p)\n    {\n        case Proba.Alfa:\n" +
            "            break;\n        default:\n            break;\n    }\n}\n";
        const string dwaRamiona =
            "public void Filtr(Proba p)\n{\n    switch (p)\n    {\n        case Proba.Alfa:\n" +
            "        case Proba.Beta:\n            break;\n        default:\n" +
            "            break;\n    }\n}\n";

        var nazwy = CzlonyNazwy(trzyCzlony);
        CollectionAssert.AreEqual(new[] { "Alfa", "Beta", "Gamma" }, nazwy["Proba"],
            "czytnik członów nie odtworzył wyliczenia syntetycznego");

        CollectionAssert.AreEqual(new[] { "Beta", "Gamma" }, Polykane(jednoRamie, "Filtr", nazwy),
            "przy jednym ramieniu czytnik ma zgłosić DWA połykane człony");
        CollectionAssert.AreEqual(new[] { "Gamma" }, Polykane(dwaRamiona, "Filtr", nazwy),
            "ramię dołożone do filtra ma WYJĄĆ człon z połykanych — czytnik tego nie zobaczył");
        CollectionAssert.AreEqual(new[] { "Beta", "Delta", "Gamma" },
            Polykane(jednoRamie, "Filtr", CzlonyNazwy(czteryCzlony)),
            "człon dopisany do wyliczenia ma WEJŚĆ do połykanych — czytnik tego nie zobaczył");
    }

    [TestMethod]
    public void Czytnik_korpusu_ODMAWIA_metodzie_wyrazeniowej_zamiast_czytac_cudza()
    {
        // 6.D231. Próbka jest złożona z dwóch składowych w tej samej kolejności, co
        // w rdzeniu: WYRAŻENIOWA przed KLAMROWĄ. Bez sąsiadki poniżej `Korpus` nie
        // znalazłby żadnej klamry i zwróciłby null Z INNEGO POWODU — a wtedy zieleń tej
        // kontroli nie mówiłaby nic o usterce, którą 6.D231 zmierzyło na drzewie.
        const string probka =
            "public static double Hamowanie(double v) => v * v / 2.0;\n"
            + "\n"
            + "public static void Nadzoruj(object system)\n"
            + "{\n"
            + "    ArgumentNullException.ThrowIfNull(system);\n"
            + "}\n";

        var wyrazeniowa = KorpusMetody(probka, "Hamowanie", out var deklaracjiW, out var powodW);
        Assert.AreEqual(1, deklaracjiW,
            "straż liczby deklaracji ma być SPEŁNIONA — usterka 6.D231 polegała właśnie " +
            "na tym, że przy spełnionej straży czytnik oddawał cudzy korpus");
        Assert.IsNull(wyrazeniowa,
            $"metoda wyrażeniowa ma dostać ODMOWĘ, a czytnik zwrócił: {wyrazeniowa}");
        Assert.IsNotNull(powodW,
            "odmowa bez powodu jest nieodróżnialna od niedomkniętej klamry");
        StringAssert.Contains(powodW!, "WYRAŻENIOWA",
            $"powód odmowy ma NAZYWAĆ kształt ciała, a mówi: {powodW}");
        Assert.IsFalse(powodW!.Contains("ThrowIfNull", StringComparison.Ordinal),
            "powód ma być powodem, a nie cudzą treścią podaną inną drogą");

        // Kontrola DODATNIA: sąsiadka KLAMROWA — czyli dokładnie ten korpus, który
        // czytnik podstawiał pod pytanie wyżej — ma się nadal czytać BEZ ZMIANY.
        // Bramka zapalająca się na pracy poprawnej zostaje wyłączona, nie poprawiona (6.D27).
        var klamrowa = KorpusMetody(probka, "Nadzoruj", out var deklaracjiK, out var powodK);
        Assert.AreEqual(1, deklaracjiK, "sąsiadka klamrowa ma dokładnie jedną deklarację");
        Assert.IsNull(powodK,
            $"metoda klamrowa NIE ma być odrzucana, a powód brzmi: {powodK}");
        Assert.IsNotNull(klamrowa, "metoda klamrowa ma nadal oddać swój korpus");
        StringAssert.Contains(klamrowa!, "ThrowIfNull(system)",
            "korpus metody klamrowej ma być JEJ WŁASNY");
    }

    /// <summary>Połykane człony jednego filtra — wspólna droga pomiaru i kontroli przyrządu.</summary>
    private static List<string> Polykane(
        string zrodlo, string metoda, Dictionary<string, List<string>> czlony)
    {
        var korpus = KorpusMetody(zrodlo, metoda, out _, out var powodCzytnika);
        Assert.IsNotNull(korpus, $"czytnik korpusu ODMÓWIŁ metodzie {metoda}: {powodCzytnika}");

        var typ = czlony.Keys.Single();
        var obsluzone = ObsluzoneCzlony(korpus!, typ);
        Assert.AreEqual(1, obsluzone.Count, $"switchy po {typ} w {metoda}: {obsluzone.Count}");

        return czlony[typ]
            .Where(c => !obsluzone[0].Contains(c))
            .OrderBy(c => c, StringComparer.Ordinal)
            .ToList();
    }

    /// <summary>Zbiory członów pokrytych etykietami <c>case Typ.Człon:</c> — po jednym na switch.</summary>
    private static List<HashSet<string>> ObsluzoneCzlony(string korpusMetody, string wyliczenie)
    {
        var out_ = new List<HashSet<string>>();
        foreach (var poczatek in PoczatkiSwitchy(korpusMetody))
        {
            var korpus = Korpus(korpusMetody, poczatek);
            if (korpus is null)
            {
                continue;
            }

            var zbior = EtykietaInstrukcyjna.Matches(korpus)
                .Where(m => string.Equals(m.Groups[1].Value, wyliczenie, StringComparison.Ordinal))
                .Select(m => m.Groups[2].Value)
                .ToHashSet(StringComparer.Ordinal);
            if (zbior.Count > 0)
            {
                out_.Add(zbior);
            }
        }

        return out_;
    }

    /// <summary>
    /// Korpus metody o podanej nazwie. Deklaracja rozpoznawana jest po MODYFIKATORZE
    /// DOSTĘPU na początku wiersza, bo wywołań tej samej nazwy jest w rdzeniu więcej
    /// niż deklaracji (<c>Supervise</c> ma w <c>CabProtection.cs</c> jedną deklarację
    /// i jedno wywołanie cztery wiersze niżej). Liczbę trafień zwraca osobno: „zero"
    /// i „dwie" to dwie różne usterki i wołający ma je rozróżnić.
    /// </summary>
    /// <remarks>
    /// <para><b>Metodę WYRAŻENIOWĄ czytnik ODMAWIA, a nie mierzy (6.D231).</b> Korpus
    /// wycinany jest od PIERWSZEJ KLAMRY po deklaracji, a metoda o ciele
    /// <c>=&gt; wyrażenie;</c> własnej klamry nie ma — pierwszą napotkaną jest więc
    /// klamra czegoś INNEGO. Zmierzone 17.09.2026 przebiegiem czytnika po <c>src/Sim/</c>:
    /// deklaracji z modyfikatorem dostępu i nawiasem jest <b>380</b>, z tego
    /// WYRAŻENIOWYCH <b>123</b>; switch niesie <b>10</b> z nich, a switch PO WYLICZENIU
    /// <b>8</b>. Przed tą poprawką <b>81</b> z tych 123 czytnik przepuszczał BEZ ODMOWY:
    /// 41 razy zwracał korpus CUDZY (dla <c>BrakingDistanceM</c>
    /// w <c>src/Sim/Signalling/TrainProtection.cs</c> — 3056 znaków korpusu
    /// <c>Supervise</c>), 40 razy urywek własnego wyrażenia. <c>deklaracji == 1</c> było
    /// przy tym SPEŁNIONE, więc żadna asercja się nie zapalała.</para>
    /// <para>Rozpoznanie jest LEKSYKALNE i takie ma zostać — rozbiór składni C# jest poza
    /// zakresem. Między deklaracją a pierwszą klamrą metody KLAMROWEJ stoi wyłącznie
    /// lista parametrów i ewentualne ograniczenia typów, a w żadnym z nich <c>=&gt;</c>
    /// wystąpić nie może; w metodzie WYRAŻENIOWEJ <c>=&gt;</c> stoi z definicji PRZED
    /// każdą klamrą, jaką jej ciało niesie.</para>
    /// </remarks>
    private static string? KorpusMetody(
        string zrodlo, string metoda, out int deklaracji, out string? powod)
    {
        var wzorzec = new Regex(
            @"^[ \t]*(?:public|private|internal|protected)[^;=\n]*\b" + Regex.Escape(metoda) + @"\s*\(",
            RegexOptions.Multiline);
        var trafienia = wzorzec.Matches(zrodlo);
        deklaracji = trafienia.Count;
        if (deklaracji != 1)
        {
            powod = $"deklaracji metody {metoda} znaleziono {deklaracji}, a czytnik " +
                "obsługuje dokładnie jedną";
            return null;
        }

        var poczatek = trafienia[0].Index;
        var klamra = zrodlo.IndexOf('{', poczatek);
        var glowa = klamra < 0 ? zrodlo[poczatek..] : zrodlo[poczatek..klamra];
        if (glowa.Contains("=>", StringComparison.Ordinal))
        {
            powod = $"metoda {metoda} jest WYRAŻENIOWA (=>) — własnej klamry nie ma, " +
                "więc pierwsza klamra po deklaracji należy już do czegoś innego (6.D231)";
            return null;
        }

        var korpus = Korpus(zrodlo, poczatek);
        powod = korpus is null
            ? $"korpusu metody {metoda} nie udało się domknąć klamrami"
            : null;
        return korpus;
    }

    /// <summary>Człony wszystkich wyliczeń rdzenia, po nazwie.</summary>
    private static Dictionary<string, List<string>> WszystkieCzlonyRdzenia(string root)
    {
        var mapa = new Dictionary<string, List<string>>(StringComparer.Ordinal);
        foreach (var plik in ZrodlaRdzenia(root))
        {
            foreach (var para in CzlonyNazwy(File.ReadAllText(plik)))
            {
                mapa[para.Key] = para.Value;
            }
        }

        return mapa;
    }

    /// <summary>Liczby członów wyliczeń. Czyta je <see cref="CzlonyNazwy"/> — jeden czytnik, nie dwa.</summary>
    private static Dictionary<string, int> Czlony(string zrodlo)
    {
        var mapa = new Dictionary<string, int>(StringComparer.Ordinal);
        foreach (var para in CzlonyNazwy(zrodlo))
        {
            mapa[para.Key] = para.Value.Count;
        }

        return mapa;
    }

    /// <summary>Człony wyliczeń po NAZWIE — 6.D211 potrzebuje nazw, 6.D210 ich liczby.</summary>
    private static Dictionary<string, List<string>> CzlonyNazwy(string zrodlo)
    {
        var mapa = new Dictionary<string, List<string>>(StringComparer.Ordinal);
        foreach (Match m in Wyliczenie.Matches(zrodlo))
        {
            mapa[m.Groups[1].Value] = Czlon.Matches(m.Groups[2].Value)
                .Select(c => c.Groups[1].Value)
                .ToList();
        }

        return mapa;
    }

    private static Ramie? Sklasyfikuj(string plik, string korpus, Dictionary<string, int> czlony)
    {
        var wyrazeniowy = EtykietaWyrazeniowa.Matches(korpus).Count > 0;
        var etykiety = wyrazeniowy
            ? EtykietaWyrazeniowa.Matches(korpus)
            : EtykietaInstrukcyjna.Matches(korpus);
        if (etykiety.Count == 0)
        {
            return null;
        }

        var typ = etykiety.Select(m => m.Groups[1].Value)
            .Where(czlony.ContainsKey)
            .GroupBy(t => t, StringComparer.Ordinal)
            .OrderByDescending(g => g.Count())
            .Select(g => g.Key)
            .FirstOrDefault();
        if (typ is null)
        {
            return null;
        }

        var pokryte = etykiety
            .Where(m => string.Equals(m.Groups[1].Value, typ, StringComparison.Ordinal))
            .Select(m => m.Groups[2].Value)
            .Distinct(StringComparer.Ordinal)
            .Count();

        var domyslne = RamieDomyslne.Match(korpus);
        if (!domyslne.Success)
        {
            return null;
        }

        var tresc = domyslne.Groups[1].Value.Trim();
        if (tresc.Length == 0)
        {
            // `default:` z treścią w następnym wierszu — postać instrukcyjna.
            var po = korpus[(domyslne.Index + domyslne.Length)..].TrimStart('\r', '\n');
            tresc = po.Split('\n').FirstOrDefault()?.Trim() ?? string.Empty;
        }

        var ciche = !tresc.StartsWith("throw", StringComparison.Ordinal);
        return new Ramie(plik, typ, pokryte, czlony[typ], ciche, wyrazeniowy);
    }

    private static List<Ramie> Zebrane()
    {
        var root = FindRepositoryRoot();
        Assert.IsNotNull(root, "nie znaleziono korzenia repozytorium");

        var pliki = ZrodlaRdzenia(root!);

        var czlony = new Dictionary<string, int>(StringComparer.Ordinal);
        var zrodla = new List<(string Plik, string Tresc)>();
        foreach (var plik in pliki)
        {
            var tresc = File.ReadAllText(plik);
            zrodla.Add((Path.GetRelativePath(root!, plik), tresc));
            foreach (var para in Czlony(tresc))
            {
                czlony[para.Key] = para.Value;
            }
        }

        var out_ = new List<Ramie>();
        foreach (var (plik, tresc) in zrodla)
        {
            foreach (var poczatek in PoczatkiSwitchy(tresc))
            {
                var korpus = Korpus(tresc, poczatek);
                if (korpus is null)
                {
                    continue;
                }

                var ramie = Sklasyfikuj(plik, korpus, czlony);
                if (ramie is not null)
                {
                    out_.Add(ramie);
                }
            }
        }

        return out_;
    }

    private static IEnumerable<int> PoczatkiSwitchy(string zrodlo)
    {
        foreach (Match m in Regex.Matches(zrodlo, @"\bswitch\b"))
        {
            yield return m.Index;
        }
    }

    private static string? Korpus(string zrodlo, int poczatek)
    {
        var i = zrodlo.IndexOf('{', poczatek);
        if (i < 0)
        {
            return null;
        }

        var glebokosc = 0;
        for (var j = i; j < zrodlo.Length; j++)
        {
            if (zrodlo[j] == '{')
            {
                glebokosc++;
            }
            else if (zrodlo[j] == '}')
            {
                glebokosc--;
                if (glebokosc == 0)
                {
                    return zrodlo[(i + 1)..j];
                }
            }
        }

        return null;
    }

    /// <summary>Pliki źródłowe rdzenia — bez <c>bin/</c> i <c>obj/</c>, w porządku stałym.</summary>
    private static List<string> ZrodlaRdzenia(string root)
    {
        return Directory
            .EnumerateFiles(Path.Combine(root, "src", "Sim"), "*.cs", SearchOption.AllDirectories)
            .Where(p => !p.Contains($"{Path.DirectorySeparatorChar}bin{Path.DirectorySeparatorChar}",
                                    StringComparison.Ordinal))
            .Where(p => !p.Contains($"{Path.DirectorySeparatorChar}obj{Path.DirectorySeparatorChar}",
                                    StringComparison.Ordinal))
            .OrderBy(p => p, StringComparer.Ordinal)
            .ToList();
    }

    private static string? FindRepositoryRoot()
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

        return null;
    }
}
