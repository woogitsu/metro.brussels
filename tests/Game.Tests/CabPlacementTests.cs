using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;
using MetroBxl.Game.World;
using MetroBxl.Sim.Line;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace MetroBxl.Game.Tests;

/// <summary>
/// Kabina stoi w układzie SKŁADU, a nie we własnym — MB-05, 14.09.2026.
///
/// <para><b>Skąd ten plik.</b> Pierwsza wersja <c>CabView.PlaceAt</c> wołała
/// <c>TrainLayout.Place</c>, czyli tę samą metodę co skorupa, i wyglądało to na
/// najostrożniejszy możliwy wybór — jedna arytmetyka, zero kopii. Był to jednak wybór
/// BŁĘDNY i nie pokazała tego żadna liczba w logu: <c>Place</c> liczy ogon jako
/// <c>czoło − rozpiętość PRZEKAZANYCH BRYŁ</c>, a bryły kabiny mają rozpiętość
/// <b>93,300 m</b> przy składzie <b>94,000 m</b>, bo kabina zaczyna się 0,35 m za czołem
/// i kończy 0,35 m przed ogonem.</para>
///
/// <para><b>Skutek był ZERO-liczbowy i dlatego groźny.</b> Wiersz <c>[KABINA]</c>
/// podawał poprawną rozpiętość, wiersz <c>[SKŁAD]</c> poprawną długość, porównanie
/// telemetrii z rdzeniem przy progu 0 wychodziło „identyczne co do bajtu" — bo kabina
/// nie dotyka fizyki. Jedyną rzeczą, którą to psuło, było POŁOŻENIE: szyba czołowa
/// lądowała 0,35 m PRZED czołem pudła zamiast 0,35 m za nim, czyli 0,700 m za daleko,
/// a oko maszynisty — stojące na 1998,200 m NIEZALEŻNIE od kabiny — wypadało za
/// oparciem fotela zamiast nad siedziskiem.</para>
///
/// <para><b>Dwa zdania tego akapitu są PRZEPISANE, a nie dopisane obok</b> (audyt
/// 14.09.2026). Stało tu, że oko „zostawało za nią zamiast przed" i że „w kadrze
/// wyglądało to na kabinę bez okna". Pierwsze jest nieprawdą: usterka przesuwa bryły,
/// a nie kamerę, więc oko jest po TEJ SAMEJ stronie płaszczyzny szyby w obu
/// przypadkach — odległość wynosi −1,450 m poprawnie i −2,150 m z usterką. Drugie było
/// nieprawdziwym związkiem przyczynowym: ramy szyby nie ma w kadrze ani przed poprawką,
/// ani po niej, bo kabina jej nie niesie. Liczby, na których usterkę WIDAĆ, są liczbami
/// fotela i pulpitu: siedzisko 1998,100–1998,550 m obejmuje oko poprawnie i przesuwa
/// się na 1998,800–1999,250 m z usterką (oparcie 1998,700–1998,800 m), a pulpit odsuwa
/// się z 0,70 m na 1,40 m przed okiem.</para>
///
/// <para><b>Ta klasa jest PRZEPISANA 14.09.2026, a nie dopisana obok, i powodem jest
/// POMIAR, nie porządki.</b> Poprzednia wersja jej bramki leksykalnej obiecywała
/// w komentarzu, że pilnuje, „czy SCENA UŻYWA" poprawnej arytmetyki, a jej komunikat
/// mówił wprost o 0,700 m. Audyt zmierzył, że pytała o PISOWNIĘ wyrażenia, nie o jego
/// wartość: <b>cztery mutacje odtwarzające dokładnie tę samą szkodę 0,700 m przeszły
/// 292/292</b> —
/// <b>W</b> (<c>var trainLength = _train.LengthM</c> → <c>_cabView.LengthM</c>: token
/// <c>trainLength</c> zostaje w argumencie, więc asercja milczy),
/// <b>X</b> (<c>PlaceWithRear(axis, _bodies, rearChainageM + 0.7)</c> w <c>CabView</c>),
/// <b>Y</b> (<c>chainage - trainLength + 0.7</c> w argumencie),
/// <b>Z</b> (całe wywołanie owinięte w <c>if (trainLength &lt; 0.0)</c>, czyli kabina
/// NIE ustawiana nigdy, a <c>Assert.AreEqual(1, wywolania.Count)</c> nadal liczy
/// wystąpienia TEKSTU).
/// Do tego metoda <c>Ta_sama_wspolrzedna_X…</c> była TAUTOLOGIĄ: obie strony porównania
/// liczyły <c>RearChainageM(Skorupa(), czolo)</c>, a <c>Kabiny()</c> nie było w niej
/// wołane ani razu — podmiana brył kabiny na <c>(−999, −998)</c> nadal dawała
/// <c>Passed: 1</c>.</para>
///
/// <para><b>Czym ta wersja się różni — trzy rzeczy, w tej kolejności.</b>
/// (1) Arytmetyka ogona wyszła z argumentu wywołania do <see cref="TrainLayout.RearOfTrain"/>
/// i jest przybita LICZBOWO; mutacja X i Y nie mają się już gdzie schować jako „wyrażenie,
/// którego nikt nie czyta". (2) Bramka leksykalna czyta źródło <b>rozbiorem</b>, a nie
/// wyszukiwaniem tokenu: pyta o CAŁĄ listę argumentów znak w znak, o GŁĘBOKOŚĆ KLAMER
/// wywołania i o znak, który je poprzedza — więc łapie i podmianę wyrażenia, i owinięcie
/// w warunek. (3) Czytnik źródła ma własną kontrolę negatywną, bo bramka, która myli się
/// w liczeniu klamer, kłamie ciszej niż ta, której w ogóle nie ma.</para>
///
/// <para><b>Czego ta klasa nadal NIE umie i to jest granica, nie przeoczenie.</b>
/// <c>FirstRun</c> i <c>CabView</c> są węzłami Godota, których <c>dotnet test</c> nie
/// powoła — więc o tym, że scena woła właśnie <see cref="TrainLayout.RearOfTrain"/>
/// i podaje jej długość SKORUPY, bramka mówi z ŹRÓDŁA, a nie z przebiegu. Świadomą
/// zmianę tych wywołań trzeba w tym samym commicie przepisać tutaj. Dowodem
/// zachowania jest <c>godot-first-run.yml</c>; to jest dowód, że kod mówi to, co ma
/// mówić.</para>
/// </summary>
[TestClass]
public class CabPlacementTests
{
    /// <summary>Rozpiętość skorupy M7, zmierzona przez scenę z wczytanej geometrii.</summary>
    private const double DlugoscSkladuM = 94.0;

    /// <summary>Rozpiętość WŁASNA brył kabiny — 0,35 m krócej z każdej strony.</summary>
    private const double RozpietoscKabinyM = 93.30;

    /// <summary>Zakres X skrajnej bryły kabiny czołowej — z raportu `m7_cab_build.py`.</summary>
    private const double SzybaCzolowaX = 93.65;

    /// <summary>Zakres X skrajnej bryły kabiny ogonowej — z tego samego raportu.</summary>
    private const double KabinaOgonowaOdX = 90.40;

    /// <summary>Odsunięcie kabiny od obu końców pudła, z tego samego raportu.</summary>
    private const double OdsunieciaKabinyM = 0.35;

    private sealed class Bryla : ITrainBody
    {
        public Bryla(double from, double to) => Span = new BodySpan(from, to);

        public BodySpan Span { get; }

        public bool Visible { get; set; }

        public Godot.Transform3D Transform { get; set; }
    }

    private static IReadOnlyList<ITrainBody> Skorupa() => new ITrainBody[]
    {
        new Bryla(0.0, 47.0),
        new Bryla(47.0, DlugoscSkladuM),
    };

    private static IReadOnlyList<ITrainBody> Kabiny() => new ITrainBody[]
    {
        new Bryla(OdsunieciaKabinyM, 3.60),
        new Bryla(KabinaOgonowaOdX, SzybaCzolowaX),
    };

    /// <summary>Oś prosta 0…3000 m — jedna dla wszystkich testów planu w tej klasie.</summary>
    private static TrackAxis Os() => TrackAxis.FromJson("""
        {"id":"TEST","crs":"EPSG:31370",
         "points":[[0,0,0],[1000,0,0],[2000,0,0],[3000,0,0]],
         "stations":[]}
        """);

    [TestMethod]
    public void Kabina_liczona_WLASNA_rozpietoscia_lezy_0_700_m_za_daleko()
    {
        const double czolo = 2000.0;

        var ogonSkladu = TrainLayout.RearChainageM(Skorupa(), czolo);
        var ogonKabiny = TrainLayout.RearChainageM(Kabiny(), czolo);

        var poprawnie = ogonSkladu + SzybaCzolowaX;
        var zleAleKuszace = ogonKabiny + SzybaCzolowaX;

        Assert.AreEqual(czolo - 0.35, poprawnie, 1e-9,
            "szyba czołowa ma stać 0,35 m ZA czołem składu");
        Assert.AreEqual(czolo + 0.35, zleAleKuszace, 1e-9,
            "liczenie ogona z rozpiętości kabiny stawia szybę PRZED czołem");
        Assert.AreEqual(0.700, zleAleKuszace - poprawnie, 1e-9,
            "różnica między jednym a drugim wynosi 0,700 m — i tyle właśnie wynosiła usterka");
    }

    [TestMethod]
    public void RearOfTrain_jest_JEDYNA_arytmetyka_ogona_i_stoi_na_dlugosci_SKLADU()
    {
        // Seam, dla którego ta pozycja powstała. Do 14.09.2026 odejmowanie ogona stało
        // W ARGUMENCIE wywołania w `FirstRun` (`chainage - trainLength`), czyli w jedynym
        // miejscu tej ścieżki, którego żaden test nie umiał wykonać — i dopisanie do
        // niego `+ 0.7` przechodziło 292/292. Tu jest ta sama arytmetyka, wykonywana
        // naprawdę, z liczbami z raportu generatora.
        const double czolo = 2000.0;

        Assert.AreEqual(RozpietoscKabinyM, TrainLayout.LengthM(Kabiny()), 1e-9,
            "stała 93,30 m ma być rozpiętością brył z `Kabiny()`, a nie liczbą wpisaną obok nich");

        var ogonSkladu = TrainLayout.RearOfTrain(czolo, DlugoscSkladuM);
        var ogonZKabiny = TrainLayout.RearOfTrain(czolo, RozpietoscKabinyM);

        Assert.AreEqual(1906.0, ogonSkladu, 1e-9,
            "ogon składu 94,000 m przy czole na 2000,000 m leży na 1906,000 m");
        Assert.AreEqual(czolo - OdsunieciaKabinyM, ogonSkladu + SzybaCzolowaX, 1e-9,
            "szyba czołowa ustawiona na ogonie SKŁADU stoi 0,35 m ZA czołem pudła");
        Assert.AreEqual(czolo + OdsunieciaKabinyM, ogonZKabiny + SzybaCzolowaX, 1e-9,
            "nakarmienie tej samej metody rozpiętością KABINY stawia szybę PRZED czołem");
        Assert.AreEqual(0.700, ogonZKabiny - ogonSkladu, 1e-9,
            "różnica między jedną a drugą długością wynosi 0,700 m — i tyle wynosiła usterka");
        Assert.AreEqual(
            TrainLayout.RearChainageM(Skorupa(), czolo),
            TrainLayout.RearOfTrain(czolo, TrainLayout.LengthM(Skorupa())),
            1e-9,
            "dla SKORUPY obie drogi mają dawać to samo — inaczej seam jest drugą arytmetyką, "
            + "a nie tą samą wyciągniętą w jedno miejsce");
        Assert.AreEqual(0.0, TrainLayout.RearOfTrain(0.0, 0.0), 1e-9,
            "zera nie odrzucamy i to jest decyzja: `--no-geometry` woła `PlaceEverything` "
            + "przy nie wczytanej skorupie, więc `LengthM` jest wtedy zerem");
    }

    [TestMethod]
    public void Ta_sama_wspolrzedna_X_daje_ten_sam_kilometraz_w_obu_zbiorach()
    {
        // **Metoda jest PRZEPISANA, bo poprzednia była tautologią.** Stało w niej
        // `wSkorupie = ogon + x` obok `wKabinie = RearChainageM(Skorupa(), czolo) + x`,
        // czyli obie strony liczyły to samo z tych samych brył, a `Kabiny()` nie było
        // wołane ani razu; podmiana brył kabiny na `(−999, −998)` nadal dawała
        // `Passed: 1`. Tutaj porównywane są DWA RÓŻNE PLANY: plan skorupy i plan kabiny,
        // każdy zbudowany ze swoich brył.
        const double czolo = 1234.567;
        var axis = Os();
        var skorupa = Skorupa();
        var kabiny = Kabiny();

        var planSkorupy = TrainLayout.Plan(axis, skorupa, czolo);

        // Tak robi to scena: ogon bierze się z długości SKŁADU, nie z rozpiętości kabiny.
        var ogonSkladu = TrainLayout.RearOfTrain(czolo, TrainLayout.LengthM(skorupa));
        var planKabiny = new List<BodyPlacement>();
        for (var index = 0; index < kabiny.Count; index++)
        {
            planKabiny.Add(TrainLayout.PlacementFor(axis, kabiny[index].Span, ogonSkladu, index));
        }

        // A tak wyglądała usterka: ogon liczony z rozpiętości własnej kabiny.
        var ogonKabiny = TrainLayout.RearChainageM(kabiny, czolo);
        var planZly = new List<BodyPlacement>();
        for (var index = 0; index < kabiny.Count; index++)
        {
            planZly.Add(TrainLayout.PlacementFor(axis, kabiny[index].Span, ogonKabiny, index));
        }

        Assert.AreEqual(planSkorupy[^1].ToChainageM - OdsunieciaKabinyM,
            planKabiny[^1].ToChainageM, 1e-9,
            "szyba czołowa kabiny ma leżeć 0,35 m za CZOŁEM SKORUPY — liczbą z planu "
            + "skorupy, a nie z drugiego rachunku na tych samych bryłach");
        Assert.AreEqual(planSkorupy[0].FromChainageM + OdsunieciaKabinyM,
            planKabiny[0].FromChainageM, 1e-9,
            "koniec ogonowy kabiny ma leżeć 0,35 m za OGONEM SKORUPY");
        Assert.AreEqual(TrainLayout.LengthM(kabiny),
            planKabiny[^1].ToChainageM - planKabiny[0].FromChainageM, 1e-9,
            "kabina ma zachować własną rozpiętość — plan ją PRZESUWA, a nie rozciąga");
        Assert.AreEqual(0.700, planZly[^1].ToChainageM - planKabiny[^1].ToChainageM, 1e-9,
            "plan zbudowany na własnym ogonie kabiny leży 0,700 m dalej");
        Assert.IsTrue(planZly[^1].ToChainageM > planSkorupy[^1].ToChainageM,
            "a szyba czołowa wystaje wtedy PRZED czoło pudła — to jest ta usterka "
            + "widziana z zewnątrz, a nie liczbowa ciekawostka");
    }

    [TestMethod]
    public void PlaceWithRear_NIE_liczy_ogona_sam_i_to_jest_cala_jego_treść()
    {
        // Kontrola przyrządu, nie powtórzenie testu wyżej: gdyby `PlaceWithRear`
        // mimo nazwy liczyło ogon z przekazanych brył, obie liczby znów by się zrównały
        // i poprawka byłaby pozorna. Pytamy o PLAN, bo on jest tym, co `PlaceWithRear`
        // buduje, zanim dotknie silnika.
        var axis = Os();
        var kabiny = Kabiny();
        const double czolo = 2000.0;
        var ogonSkladu = TrainLayout.RearChainageM(Skorupa(), czolo);

        var planZeSkladu = new List<double>();
        foreach (var bryla in kabiny)
        {
            planZeSkladu.Add(
                TrainLayout.PlacementFor(axis, bryla.Span, ogonSkladu, 0).ToChainageM);
        }

        Assert.AreEqual(czolo - 0.35, planZeSkladu[^1], 1e-9,
            "plan zbudowany na ogonie SKŁADU stawia szybę 0,35 m za czołem");
        Assert.AreEqual(czolo - DlugoscSkladuM + 3.60, planZeSkladu[0], 1e-9,
            "kabina ogonowa ma stać przy ogonie składu, nie przy własnym");
    }

    // --- CZYTNIK ŹRÓDŁA ----------------------------------------------------------
    //
    // **Dlaczego bramki niżej czytają ŹRÓDŁO, i to nie jest lenistwo — zostało
    // WYMIERZONE.** Mutacje siedzą w `FirstRun.cs` i w `CabView.cs`, czyli w węzłach
    // Godota, których `dotnet test` nie powoła; testy arytmetyczne wyżej sprawdzają
    // RACHUNEK na atrapach i robią to poprawnie, ale miejsce wywołania jest poza ich
    // zasięgiem. „Arytmetyka się zgadza" i „scena jej używa" to dwa różne zdania.
    //
    // **Co się zmieniło 14.09.2026.** Poprzednia wersja pytała o TOKEN (`argumenty
    // .Contains("trainLength")`), a token przeżywa każdą z czterech zmierzonych mutacji.
    // Ta pyta o rozbiór: całą listę argumentów znak w znak, głębokość klamer wywołania
    // i znak, który je poprzedza. Żeby to miało sens, czytnik musi rozumieć, że klamra
    // w napisie i klamra w komentarzu nie są klamrą kodu — `FirstRun.cs` ma w sobie
    // literał surowy z JSON-em pełnym klamer. Stąd `TylkoKod` i jego własna kontrola
    // negatywna niżej: bramka, która myli się w liczeniu klamer, kłamie ciszej niż ta,
    // której nie ma wcale.
    private static string Zrodlo(params string[] czesci) =>
        File.ReadAllText(Path.Combine(MetroBxl.Tests.Shared.KorzenRepozytorium.Sciezka, Path.Combine(czesci)));

    /// <summary>
    /// Źródło z wymazaną treścią komentarzy i literałów — bajt w bajt tej samej
    /// długości, żeby indeksy zgadzały się z oryginałem. Obsługuje literał zwykły,
    /// znakowy, werbatim (<c>@"…"</c>) i surowy (<c>"""…"""</c>, także z przedrostkiem
    /// interpolacji), bo `FirstRun.cs` używa ostatniego z nich do metadanych zrzutu
    /// i ma w nim kilkadziesiąt klamer.
    /// </summary>
    private static string TylkoKod(string zrodlo)
    {
        var wynik = new StringBuilder(zrodlo.Length);
        var i = 0;

        void Wymaz(int od, int doWylacznie)
        {
            for (var k = od; k < doWylacznie && k < zrodlo.Length; k++)
            {
                wynik.Append(zrodlo[k] == '\n' ? '\n' : ' ');
            }
        }

        while (i < zrodlo.Length)
        {
            var c = zrodlo[i];

            if (c == '/' && i + 1 < zrodlo.Length && zrodlo[i + 1] == '/')
            {
                var koniec = zrodlo.IndexOf('\n', i);
                koniec = koniec < 0 ? zrodlo.Length : koniec;
                Wymaz(i, koniec);
                i = koniec;
                continue;
            }

            if (c == '/' && i + 1 < zrodlo.Length && zrodlo[i + 1] == '*')
            {
                var koniec = zrodlo.IndexOf("*/", i + 2, StringComparison.Ordinal);
                koniec = koniec < 0 ? zrodlo.Length : koniec + 2;
                Wymaz(i, koniec);
                i = koniec;
                continue;
            }

            if (c == '\'')
            {
                var j = i + 1;
                while (j < zrodlo.Length && zrodlo[j] != '\'')
                {
                    j += zrodlo[j] == '\\' ? 2 : 1;
                }

                Wymaz(i, Math.Min(j + 1, zrodlo.Length));
                i = Math.Min(j + 1, zrodlo.Length);
                continue;
            }

            // Przedrostki literału: `$`, `$$`, `@` w dowolnej kolejności i liczbie.
            var poczatek = i;
            var p = i;
            var werbatim = false;
            while (p < zrodlo.Length && (zrodlo[p] == '$' || zrodlo[p] == '@'))
            {
                werbatim |= zrodlo[p] == '@';
                p++;
            }

            if (p < zrodlo.Length && zrodlo[p] == '"')
            {
                var cudzyslowow = 0;
                while (p + cudzyslowow < zrodlo.Length && zrodlo[p + cudzyslowow] == '"')
                {
                    cudzyslowow++;
                }

                int koniec;
                if (cudzyslowow >= 3)
                {
                    // Literał surowy: kończy go pierwszy ciąg co najmniej tylu cudzysłowów.
                    var j = p + cudzyslowow;
                    while (j < zrodlo.Length)
                    {
                        if (zrodlo[j] == '"')
                        {
                            var ile = 0;
                            while (j + ile < zrodlo.Length && zrodlo[j + ile] == '"')
                            {
                                ile++;
                            }

                            if (ile >= cudzyslowow)
                            {
                                j += ile;
                                break;
                            }

                            j += ile;
                            continue;
                        }

                        j++;
                    }

                    koniec = Math.Min(j, zrodlo.Length);
                }
                else if (cudzyslowow == 2)
                {
                    koniec = p + 2;
                }
                else if (werbatim)
                {
                    var j = p + 1;
                    while (j < zrodlo.Length)
                    {
                        if (zrodlo[j] == '"')
                        {
                            if (j + 1 < zrodlo.Length && zrodlo[j + 1] == '"')
                            {
                                j += 2;
                                continue;
                            }

                            j++;
                            break;
                        }

                        j++;
                    }

                    koniec = Math.Min(j, zrodlo.Length);
                }
                else
                {
                    var j = p + 1;
                    while (j < zrodlo.Length && zrodlo[j] != '"')
                    {
                        j += zrodlo[j] == '\\' ? 2 : 1;
                    }

                    koniec = Math.Min(j + 1, zrodlo.Length);
                }

                Wymaz(poczatek, koniec);
                i = koniec;
                continue;
            }

            wynik.Append(c);
            i++;
        }

        return wynik.ToString();
    }

    /// <summary>Jedno wywołanie znalezione w kodzie: gdzie stoi i co dostało w nawiasach.</summary>
    private readonly record struct Wywolanie(int Indeks, string Argumenty);

    /// <summary>
    /// Wszystkie wywołania <paramref name="wzorzec"/> (np. <c>_cabView.PlaceAt(</c>)
    /// z listą argumentów wyciętą po BILANSIE NAWIASÓW, a nie do pierwszego przecinka
    /// czy średnika — bo argument bywa wywołaniem z własnymi przecinkami.
    /// </summary>
    private static IReadOnlyList<Wywolanie> Wywolania(string kod, string wzorzec)
    {
        var znalezione = new List<Wywolanie>();
        var od = 0;
        while (true)
        {
            var indeks = kod.IndexOf(wzorzec, od, StringComparison.Ordinal);
            if (indeks < 0)
            {
                return znalezione;
            }

            var otwarcie = indeks + wzorzec.Length;
            var glebokosc = 1;
            var j = otwarcie;
            while (j < kod.Length && glebokosc > 0)
            {
                if (kod[j] == '(')
                {
                    glebokosc++;
                }
                else if (kod[j] == ')')
                {
                    glebokosc--;
                }

                j++;
            }

            znalezione.Add(new Wywolanie(indeks, kod[otwarcie..Math.Max(otwarcie, j - 1)]));
            od = otwarcie;
        }
    }

    /// <summary>Bilans klamer przed danym indeksem — głębokość bloku, w którym stoi wyrażenie.</summary>
    private static int Glebokosc(string kod, int indeks)
    {
        var glebokosc = 0;
        for (var i = 0; i < indeks && i < kod.Length; i++)
        {
            if (kod[i] == '{')
            {
                glebokosc++;
            }
            else if (kod[i] == '}')
            {
                glebokosc--;
            }
        }

        return glebokosc;
    }

    /// <summary>Ostatni niebiały znak przed indeksem — mówi, czy wyrażenie jest instrukcją, czy ciałem warunku.</summary>
    private static char ZnakPrzed(string kod, int indeks)
    {
        for (var i = Math.Min(indeks, kod.Length) - 1; i >= 0; i--)
        {
            if (!char.IsWhiteSpace(kod[i]))
            {
                return kod[i];
            }
        }

        return '\0';
    }

    /// <summary>Ciągi białych znaków sprowadzone do jednej spacji — porównujemy treść, nie łamanie wierszy.</summary>
    private static string Splaszcz(string tekst) =>
        Regex.Replace(tekst, @"\s+", " ").Trim();

    [TestMethod]
    public void Czytnik_zrodla_NIE_liczy_klamer_z_napisow_ani_z_komentarzy()
    {
        // Kontrola przyrządu. Bez niej trzy bramki niżej stoją na czymś, czego nikt
        // nie sprawdził — a `FirstRun.cs` ma w sobie literał surowy z JSON-em, czyli
        // kilkadziesiąt klamer, które do bilansu bloków nie należą.
        var zNapisami = string.Join("\n",
            "void M()",
            "{",
            "    // { komentarz }",
            "    /* { blok } */",
            "    var a = \"{ napis }\";",
            "    var b = @\"{ werbatim }\";",
            "    var c = '{';",
            "    var d = $$\"\"\"{ surowy }\"\"\";",
            "    Cel();",
            "}");
        var kod = TylkoKod(zNapisami);

        Assert.AreEqual(zNapisami.Length, kod.Length,
            "wymazywanie ma zachować długość — inaczej indeksy przestają wskazywać "
            + "to samo miejsce w oryginale");
        Assert.AreEqual(1, Glebokosc(kod, zNapisami.IndexOf("Cel(", StringComparison.Ordinal)),
            "klamry z napisów, z komentarza i z literału surowego nie są klamrami bloku");
        foreach (var slowo in new[] { "komentarz", "blok", "napis", "werbatim", "surowy" })
        {
            Assert.IsFalse(kod.Contains(slowo, StringComparison.Ordinal),
                $"treść \u201E{slowo}\u201D przeszła przez czytnik — bramki niżej "
                + "czytałyby wtedy komentarze i literały jako kod");
        }

        // Druga połowa kontroli: czytnik ma klamry KODU liczyć, a nie wycinać wszystkiego.
        var zWarunkiem = string.Join("\n",
            "void M()",
            "{",
            "    if (x)",
            "    {",
            "        Cel();",
            "    }",
            "}");
        var kodWarunku = TylkoKod(zWarunkiem);

        Assert.AreEqual(2, Glebokosc(kodWarunku, zWarunkiem.IndexOf("Cel(", StringComparison.Ordinal)),
            "wywołanie w bloku `if` stoi o jedną klamrę głębiej i czytnik ma to widzieć");
        Assert.AreEqual('{', ZnakPrzed(kodWarunku, zWarunkiem.IndexOf("Cel(", StringComparison.Ordinal)),
            "instrukcja otwierająca blok ma przed sobą klamrę, a nie średnik");
        Assert.AreEqual("_sceneAxis, chainage",
            Splaszcz(Wywolania("f(); g(_sceneAxis,\n    chainage); h();", "g(")[0].Argumenty),
            "argumenty wycina bilans nawiasów, a spłaszczenie zbija łamanie wiersza");
    }

    [TestMethod]
    public void Scena_podaje_kabinie_ogon_SKLADU_a_nie_jej_wlasny()
    {
        var kod = TylkoKod(Zrodlo("src", "Game", "FirstRun.cs"));

        var wywolania = Wywolania(kod, "_cabView.PlaceAt(");
        Assert.AreEqual(1, wywolania.Count,
            "`_cabView.PlaceAt` ma być wołane DOKŁADNIE raz — drugie wywołanie znaczy "
            + "drugie miejsce, w którym da się podać zły ogon");

        // **Pin na CAŁĄ listę argumentów, a nie na token w niej.** Poprzednia wersja
        // pytała `argumenty.Contains("trainLength")` i przepuszczała `chainage -
        // trainLength + 0.7` — zmierzone, 292/292. Tu każda zmiana wyrażenia, także
        // dopisanie składnika, zmienia porównywany napis.
        Assert.AreEqual(
            "_sceneAxis, TrainLayout.RearOfTrain(chainage, trainLength)",
            Splaszcz(wywolania[0].Argumenty),
            "kabina ma dostać ogon policzony przez `TrainLayout.RearOfTrain` z długości "
            + "SKŁADU i nic poza tym. Każdy inny kształt tego argumentu — własna "
            + "rozpiętość kabiny, dopisany składnik, inna metoda — przesuwa szybę czołową "
            + "i nie zapala się nigdzie indziej; usterka MB-05 wynosiła 0,700 m. Jeśli "
            + "zmieniasz to wywołanie ŚWIADOMIE, przepisz ten pin w tym samym commicie "
            + "i dopisz, co zmierzyłeś");
    }

    [TestMethod]
    public void Scena_bierze_dlugosc_SKLADU_a_nie_kabiny()
    {
        // Mutacja W z audytu: `var trainLength = _cabView.LengthM;`. Argument wywołania
        // wygląda wtedy IDENTYCZNIE — token `trainLength` stoi w nim dalej — a kabina
        // ląduje 0,700 m za daleko, dokładnie tak samo jak przy usterce pierwotnej.
        // Przy okazji psuje kamerę goniącą, bo ta bierze długość z tego samego wiersza.
        // Pin wyżej tego nie widzi i widzieć nie może: mutacja siedzi wiersz wcześniej.
        var kod = TylkoKod(Zrodlo("src", "Game", "FirstRun.cs"));

        var deklaracje = Regex.Matches(kod, @"\bvar\s+trainLength\s*=\s*([^;]+);");
        Assert.AreEqual(1, deklaracje.Count,
            "`trainLength` ma być deklarowane DOKŁADNIE raz — zero znaczy, że wyrażenie "
            + "wjechało z powrotem w argument wywołania, a dwa, że są dwie długości");
        Assert.AreEqual("_train.LengthM", Splaszcz(deklaracje[0].Groups[1].Value),
            "długość, po której jedzie kabina, ma pochodzić ze SKORUPY. `_cabView.LengthM` "
            + "to 93,300 m wobec 94,000 m składu — kabina ląduje 0,700 m za daleko, "
            + "a szyba czołowa PRZED czołem pudła");
    }

    [TestMethod]
    public void Ustawienie_kabiny_jest_BEZWARUNKOWE_wobec_wyboru_widoku_skorupy()
    {
        // Widok skorupy jest teraz ustawiany według ID składu w linii, lecz kamera
        // kabiny musi pozostać ustawiana bezwarunkowo z długości tej samej skorupy.
        // Mutacja Z z audytu: całe wywołanie owinięte w `if (trainLength < 0.0) { … }`,
        // czyli kabina NIE ustawiana ani razu. Liczenie WYSTĄPIEŃ tekstu daje wtedy
        // dalej jedynkę i bramka milczy — zmierzone, 292/292. Pytanie o głębokość
        // klamer i o znak poprzedzający jest jedynym, które to rozróżnia bez silnika.
        var kod = TylkoKod(Zrodlo("src", "Game", "FirstRun.cs"));

        var skorupa = Wywolania(kod, "_train.PlaceAt(");
        var kabina = Wywolania(kod, "_cabView.PlaceAt(");
        Assert.AreEqual(1, skorupa.Count,
            "`_train.PlaceAt` ma być wołane DOKŁADNIE raz — to ono wyznacza miejsce, "
            + "względem którego mierzymy wywołanie kabiny");
        Assert.AreEqual("_sceneAxis, chainage", Splaszcz(skorupa[0].Argumenty),
            "skorupa ma dostać kilometraż CZOŁA — jeśli i ona pojedzie po czymś innym, "
            + "porównanie kabiny ze skorupą przestaje o czymkolwiek mówić");

        var dlugosc = Regex.Match(kod, @"\bvar\s+trainLength\s*=");
        Assert.IsTrue(dlugosc.Success, "długość składu musi być czytana przed ustawieniem kabiny");
        Assert.AreEqual(Glebokosc(kod, dlugosc.Index), Glebokosc(kod, kabina[0].Indeks),
            "kabina ma być ustawiana na głębokości bezwarunkowego odczytu długości. Głębiej "
            + "znaczy \u201Epod warunkiem\u201D — a wywołanie, które nie wykonuje się "
            + "nigdy, wygląda w wyszukiwaniu tekstu dokładnie tak samo jak wykonywane "
            + "co klatkę");
        // **Dozwolone znaki są DWA, i ten wiersz jest PRZEPISANY, a nie rozluźniony**
        // (MB-07, 14.09.2026). Do tej pozycji stało tu `AreEqual(';', …)`, bo przed
        // wywołaniem kabiny stała jedna instrukcja — `_train.PlaceAt(…);`. MB-07 wstawia
        // między nie pętlę ustawiającą POZOSTAŁE składy, więc znakiem poprzedzającym
        // jest dziś `}`, czyli koniec bloku. Jedno i drugie znaczy to samo, o co ten
        // strażnik pyta: wywołanie stoi NA POZIOMIE INSTRUKCJI, a nie jako ciało
        // bezklamrowego `if`. Rozróżnienie zostaje nietknięte — `)` nadal zapala test,
        // i to jest jedyny znak, który ten strażnik ma odrzucać.
        var znak = ZnakPrzed(kod, kabina[0].Indeks);
        Assert.IsTrue(znak is ';' or '}',
            $"wywołanie ma stać zaraz po innej INSTRUKCJI albo po zamknięciu bloku, "
            + $"a stoi po znaku `{znak}`. Znak `)` przed nim znaczy "
            + "`if (…) _cabView.PlaceAt(…);` bez klamer — ten wariant ma tę samą "
            + "głębokość co poprawny i rozróżnia go dopiero ten znak");
    }

    [TestMethod]
    public void Widocznosc_kabiny_jest_ZWIAZANA_z_widokiem_a_nie_ustawiana_osobno()
    {
        var kod = TylkoKod(Zrodlo("src", "Game", "FirstRun.cs"));

        var przypisania = Regex.Matches(kod, @"_cabView\.Visible\s*=\s*([^;]+);");
        Assert.AreEqual(1, przypisania.Count,
            "`_cabView.Visible` ma być przypisywane DOKŁADNIE raz — drugi przełącznik "
            + "daje stan, w którym nie widać ani skorupy, ani kabiny");

        var wyrazenie = Splaszcz(przypisania[0].Groups[1].Value);
        Assert.AreEqual("view == ViewKind.Cab", wyrazenie,
            "widoczność kabiny ma być ODWROTNOŚCIĄ widoczności skorupy, wyrażoną tym "
            + "samym warunkiem. Stałe `true`/`false` albo własne pole dają kabinę, która "
            + "nie znika przy przejściu do widoku goniącego — a tam kamera patrzy na "
            + "skład Z ZEWNĄTRZ i wnętrze wisiałoby w powietrzu obok pudła");
    }

    [TestMethod]
    public void CabView_PlaceAt_przekazuje_ogon_BEZ_WLASNEJ_arytmetyki()
    {
        // Mutacja X z audytu: `PlaceWithRear(axis, _bodies, rearChainageM + 0.7)`.
        // Poprzednia wersja pytała, czy w pliku STOI `TrainLayout.PlaceWithRear(` —
        // a stoi, razem z dopiskiem. Ta pyta o całe ciało metody znak w znak.
        var kod = TylkoKod(Zrodlo("src", "Game", "World", "CabView.cs"));

        var metoda = Regex.Match(
            kod, @"public void PlaceAt\(SceneAxis axis, double rearChainageM\)\s*=>([^;]+);");
        Assert.IsTrue(metoda.Success,
            "`CabView.PlaceAt` ma brać OGON, nie czoło, i ma być jednym wyrażeniem. Nazwa "
            + "parametru jest tu jedynym miejscem, w którym wołający dowiaduje się, co ma "
            + "podać; ciało z klamrami znaczy, że coś się po drodze liczy");
        Assert.AreEqual("TrainLayout.PlaceWithRear(axis, _bodies, rearChainageM)",
            Splaszcz(metoda.Groups[1].Value),
            "kabina ma przekazać ogon DALEJ bez tknięcia go. Własna arytmetyka tutaj "
            + "przesuwa całe wnętrze i nie widać jej w żadnej liczbie logu — wiersz "
            + "`[KABINA]` podaje rozpiętość, a nie położenie");
        Assert.IsFalse(Regex.IsMatch(kod, @"TrainLayout\.Place\("),
            "`CabView` woła `TrainLayout.Place`, które liczy ogon z przekazanych brył — "
            + "dla kabiny jest to 93,300 m zamiast 94,000 m składu");
    }
}
