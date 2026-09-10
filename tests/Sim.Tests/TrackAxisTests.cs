using System;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Reflection;
using MetroBxl.Sim.Line;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace MetroBxl.Sim.Tests;

/// <summary>
/// Testy osi trasy. Kontrola z <c>src/Sim.Runner axis</c> jest **integracyjna** —
/// porównuje całą oś pakietu A z manifestem generatora i z Pythonem. Tutaj są
/// przypadki, których takie porównanie nie pokrywa: pojedynczy odcinek, kilometraż
/// dokładnie na wierzchołku, oba końce osi i wartości poza zakresem.
/// </summary>
[TestClass]
public sealed class TrackAxisTests
{
    /// <summary>Oś z dwóch punktów: nie ma czego zagęszczać, więc łamana zostaje bez zmian.</summary>
    [TestMethod]
    public void Pojedynczy_odcinek_nie_jest_zageszczany()
    {
        var axis = TrackAxis.FromJson(Json((0.0, 0.0), (100.0, 0.0)));

        Assert.AreEqual(2, axis.Points.Count);
        Assert.AreEqual(100.0, axis.LengthM, 0.0);
        Assert.AreEqual(0.0, axis.ChainagesM[0], 0.0);
        Assert.AreEqual(100.0, axis.ChainagesM[1], 0.0);
    }

    /// <summary>Krok zagęszczania ≤ 0 to tryb wierny: wychodzi surowa łamana STIB.</summary>
    [TestMethod]
    public void Krok_niedodatni_zostawia_lamana_bez_zmian()
    {
        var json = Json((0.0, 0.0), (50.0, 0.0), (100.0, 40.0), (200.0, 40.0));

        var faithful = TrackAxis.FromJson(json, 0.0);
        var densified = TrackAxis.FromJson(json);

        Assert.AreEqual(4, faithful.Points.Count);
        Assert.AreEqual(0.0, faithful.MaxDeviationFromSourceM(), 0.0,
            "tryb wierny nie może odchylić się od źródła ani o metr, ani o bit");
        Assert.IsTrue(densified.Points.Count > faithful.Points.Count,
            "zagęszczanie ma dołożyć punkty, a nie tylko przepisać łamaną");
    }

    /// <summary>Powtórzony punkt jest usuwany — zerowy segment wywraca każdą normalizację.</summary>
    [TestMethod]
    public void Powtorzone_punkty_sa_usuwane()
    {
        var axis = TrackAxis.FromJson(Json((0.0, 0.0), (0.0, 0.0), (100.0, 0.0)), 0.0);

        Assert.AreEqual(2, axis.SourcePoints.Count);
        Assert.AreEqual(100.0, axis.LengthM, 0.0);
    }

    /// <summary>Oś, z której po odsianiu duplikatów zostaje jeden punkt, nie jest osią.</summary>
    [TestMethod]
    public void Os_z_jednego_punktu_jest_odrzucana()
    {
        Assert.ThrowsException<ArgumentException>(
            () => TrackAxis.FromJson(Json((5.0, 5.0), (5.0, 5.0))));
        Assert.ThrowsException<ArgumentNullException>(() => TrackAxis.FromJson(null!));
    }

    /// <summary>Kilometraż dokładnie na wierzchołku daje ten wierzchołek, a nie sąsiada.</summary>
    [TestMethod]
    public void Chainage_na_wierzcholku_daje_ten_wierzcholek()
    {
        var axis = TrackAxis.FromJson(Json((0.0, 0.0), (30.0, 0.0), (30.0, 40.0)), 0.0);

        var atVertex = axis.PointAt(30.0);

        Assert.AreEqual(30.0, atVertex.X, 1e-12);
        Assert.AreEqual(0.0, atVertex.Y, 1e-12);
        Assert.AreEqual(70.0, axis.LengthM, 1e-12);
    }

    /// <summary>Oba końce osi trafiają dokładnie w punkty skrajne.</summary>
    [TestMethod]
    public void Konce_osi_trafiaja_w_punkty_skrajne()
    {
        var axis = TrackAxis.FromJson(Json((0.0, 0.0), (30.0, 0.0), (30.0, 40.0)), 0.0);

        var start = axis.PointAt(0.0);
        var end = axis.PointAt(axis.LengthM);

        Assert.AreEqual(0.0, start.X, 0.0);
        Assert.AreEqual(0.0, start.Y, 0.0);
        Assert.AreEqual(30.0, end.X, 1e-12);
        Assert.AreEqual(40.0, end.Y, 1e-12);
    }

    /// <summary>
    /// Kilometraż poza osią jest przycinany do jej końców — tak samo jak w
    /// <c>tools/blender/placement.py: frame_at</c>. Skład dłuższy niż resztka osi ma
    /// stanąć na jej końcu, a nie zniknąć albo wylecieć w nieskończoność.
    /// </summary>
    [TestMethod]
    public void Chainage_poza_osia_jest_przycinany_do_konca()
    {
        var axis = TrackAxis.FromJson(Json((0.0, 0.0), (100.0, 0.0)), 0.0);

        Assert.AreEqual(0.0, axis.PointAt(-500.0).X, 0.0);
        Assert.AreEqual(100.0, axis.PointAt(9999.0).X, 1e-12);
        Assert.ThrowsException<ArgumentOutOfRangeException>(() => axis.PointAt(double.NaN));
    }

    /// <summary>Punkt w połowie odcinka leży w jego połowie — interpolacja liniowa, bez niespodzianek.</summary>
    [TestMethod]
    public void Punkt_w_polowie_odcinka_lezy_w_jego_polowie()
    {
        var axis = TrackAxis.FromJson(Json((0.0, 0.0), (100.0, 0.0)), 0.0);

        var middle = axis.PointAt(25.0);

        Assert.AreEqual(25.0, middle.X, 1e-12);
        Assert.AreEqual(0.0, middle.Y, 0.0);
        Assert.AreEqual(0.0, middle.Z, 0.0);
    }

    /// <summary>Zagęszczona oś przechodzi przez punkty źródłowe i jest od nich dłuższa na łuku.</summary>
    [TestMethod]
    public void Zageszczenie_wybrzusza_luk_na_zewnatrz_ciagliwy_i_dluzszy()
    {
        var json = Json((0.0, 0.0), (50.0, 0.0), (100.0, 50.0), (100.0, 150.0));

        var faithful = TrackAxis.FromJson(json, 0.0);
        var densified = TrackAxis.FromJson(json);

        Assert.IsTrue(densified.LengthM > faithful.LengthM,
            "krzywa przez te same punkty nie może być krótsza od łamanej");
        Assert.IsTrue(densified.MaxDeviationFromSourceM() > 0.0,
            "gdyby odchyłka wyszła zerowa, znaczyłoby to, że interpolacja nic nie robi");

        // Krok zagęszczania dzieli **cięciwę** źródłowego odcinka na równe części,
        // a krzywa przez te punkty jest od cięciwy dłuższa — więc odstęp mierzony po
        // łuku bywa nieco większy niż nominalny krok. Zmierzone na tym łuku maksimum
        // to 5,036 m przy kroku 5,0 m, czyli 0,7 %. Granica 10 % łapie rozjazd
        // rzędu wielkości, a nie karze za geometrię krzywej.
        var worstGap = 0.0;
        for (var i = 1; i < densified.Points.Count; i++)
        {
            worstGap = Math.Max(worstGap, densified.ChainagesM[i] - densified.ChainagesM[i - 1]);
        }

        Assert.IsTrue(worstGap <= 1.10 * TrackAxis.DefaultRingStepM,
            $"największy odstęp {worstGap} m przy kroku {TrackAxis.DefaultRingStepM} m");
        Assert.IsTrue(worstGap > 0.5 * TrackAxis.DefaultRingStepM,
            "odstępy dużo mniejsze od kroku znaczyłyby, że zagęszczanie liczy coś innego niż cięciwę");
    }

    /// <summary>Stacje wychodzą posortowane po chainage bez względu na kolejność w pliku.</summary>
    [TestMethod]
    public void Stacje_sa_posortowane_po_chainage()
    {
        const string json = """
            {"id":"T","length_m":100.0,"vertical":{"status":"not_modelled"},
             "points":[[0,0,0],[100,0,0]],
             "stations":[{"name":"B","chainage_m":80.0},{"name":"A","chainage_m":10.0}]}
            """;

        var axis = TrackAxis.FromJson(json, 0.0);

        CollectionAssert.AreEqual(
            new[] { "A", "B" }, axis.Stations.Select(s => s.Name).ToArray());
        Assert.AreEqual(10.0, axis.Stations[0].ChainageM, 0.0);
    }

    /// <summary>
    /// Profil pionowy jest raportowany, a nie zgadywany. Dopóki oś ma status
    /// <c>not_modelled</c>, nie wolno wyprowadzać z niej pochylenia
    /// (<c>docs/21-measured-vs-assumed.md</c> §3).
    /// </summary>
    [TestMethod]
    public void Status_profilu_pionowego_jest_przenoszony_z_pliku()
    {
        var axis = TrackAxis.FromJson(Json((0.0, 0.0), (100.0, 0.0)), 0.0);

        Assert.AreEqual("not_modelled", axis.VerticalStatus);
        Assert.IsFalse(axis.IsVerticalModelled);
    }

    /// <summary>
    /// Kontrola na prawdziwej osi pakietu A: liczby muszą zgadzać się z manifestem
    /// generatora (<c>reports/L1_A-chunks.md</c>: 447 punktów źródłowych, oś
    /// zagęszczona 6686,739 m, 12 stacji). Test jest pomijany, gdy testy zostały
    /// uruchomione poza repozytorium.
    /// </summary>
    [TestMethod]
    public void Os_pakietu_A_zgadza_sie_z_geometria_generatora()
    {
        var root = FindRepositoryRoot();
        if (root is null)
        {
            Assert.Inconclusive("brak repozytorium na dysku — kontrola osi pakietu A pominięta");
            return;
        }

        var axis = TrackAxis.FromJson(File.ReadAllText(Path.Combine(root, "data", "track", "L1_A.json")));

        Console.WriteLine(string.Create(
            CultureInfo.InvariantCulture,
            $"[OŚ L1_A] źródłowych {axis.SourcePoints.Count}, zagęszczonych {axis.Points.Count}, " +
            $"długość {axis.LengthM:F3} m, odchyłka {axis.MaxDeviationFromSourceM():F4} m"));

        Assert.AreEqual("L1_A", axis.Id);
        Assert.AreEqual(447, axis.SourcePoints.Count);
        Assert.AreEqual(1349, axis.Points.Count);
        Assert.AreEqual(6686.739, axis.LengthM, 1e-3, "długość osi z manifestu chunków T-210");
        Assert.AreEqual(6686.35, axis.DeclaredLengthM, 1e-9);
        Assert.AreEqual(12, axis.Stations.Count);
        Assert.IsFalse(axis.IsVerticalModelled);
    }

    /// <summary>
    /// Trzy sposoby, na jakie plik osi może POWIEDZIEĆ NIC, i wszystkie trzy dają
    /// fałsz — 6.D80. Zmierzone 09.09.2026 sondą wołającą ten sam typ: przed
    /// poprawką każdy z tych trzech wierszy dawał <c>True</c>, bo predykat był
    /// negacją JEDNEGO napisu, a nie białą listą.
    /// </summary>
    [TestMethod]
    public void Os_bez_klucza_profilu_pionowego_nie_jest_zamodelowana()
    {
        var axis = TrackAxis.FromJson(JsonBezProfilu((0.0, 0.0), (100.0, 0.0)));

        Assert.AreEqual("unknown", axis.VerticalStatus,
            "brak klucza `vertical` ma dawać status `unknown`, a nie pusty napis");
        Assert.IsFalse(axis.IsVerticalModelled,
            "oś bez klucza profilu nie mówi NIC o pochyleniu — a nie „jest zamodelowana\u201d");
    }

    /// <summary>
    /// Literówka w statusie daje fałsz. To jest ten wiersz, który przed 6.D80
    /// przechodził: <c>nod_modelled</c> nie równa się <c>not_modelled</c>, więc
    /// negacja dawała <c>True</c> — czyli literówka w danych ogłaszała profil
    /// zamodelowanym.
    /// </summary>
    [TestMethod]
    public void Literowka_w_statusie_profilu_nie_ogłasza_profilu_zamodelowanym()
    {
        foreach (var status in new[] { "nod_modelled", "unknown", "", "modelled",
                                       "NOT_MODELLED", "not modelled" })
        {
            var axis = TrackAxis.FromJson(JsonZeStatusem(status, (0.0, 0.0), (100.0, 0.0)));

            Assert.AreEqual(status, axis.VerticalStatus);
            Assert.IsFalse(axis.IsVerticalModelled,
                $"status `{status}` ogłosił profil zamodelowanym");
        }
    }

    /// <summary>
    /// Biała lista jest ZAMKNIĘTA i dziś pusta — a ten test jest miejscem, w którym
    /// to zdanie stoi, żeby jego zmiana była widoczna w diffie, a nie ukryta
    /// w jednej linijce pola.
    ///
    /// <para>Predykat CZYTA tę listę i to jest sprawdzone w obie strony: pusta lista
    /// odrzuca każdy napis, a wpis dopisany do niej byłby jedynym, który przechodzi.
    /// Kontrola negatywna WYKONANA 10.09.2026: dopisanie <c>"not_modelled"</c> do
    /// listy wywraca oba testy wyżej — czyli lista nie jest ozdobą.</para>
    /// </summary>
    [TestMethod]
    public void Biala_lista_statusow_profilu_jest_dzis_pusta_i_predykat_z_niej_czyta()
    {
        Assert.AreEqual(0, TrackAxis.ModelledVerticalStatuses.Count,
            "biała lista przestała być pusta — dopisanie do niej wartości jest "
            + "oświadczeniem, że dla tego statusu profil NAPRAWDĘ jest w danych, "
            + "i ma iść razem z rzędnymi w plikach osi");

        // Predykat idzie przez listę, a nie przez własną kopię reguły: dla każdego
        // napisu wynik ma być RÓWNY przynależności do listy. Przy pustej liście
        // znaczy to „fałsz dla wszystkiego", a po dopisaniu wpisu ta sama asercja
        // wymusi prawdę dokładnie dla niego.
        foreach (var status in new[] { "not_modelled", "unknown", "modelled",
                                       "nod_modelled", "surveyed", "" })
        {
            Assert.AreEqual(TrackAxis.ModelledVerticalStatuses.Contains(status),
                TrackAxis.IsModelledStatus(status),
                $"predykat rozjechał się z białą listą dla `{status}`");
        }

        Assert.IsFalse(TrackAxis.IsModelledStatus(null),
            "brak statusu nie jest statusem zamodelowanym");

        // REGUŁA SPRAWDZONA NA LIŚCIE NIEPUSTEJ, i to jest tu konieczne, nie ozdobne.
        // Zmierzone 10.09.2026: przy liście pustej predykat czytający listę i predykat
        // zwracający twarde `false` są dla testów NIEODRÓŻNIALNE — kontrola negatywna
        // zastępująca całą pętlę przez `return false` przeszła 597/597, ZIELONO.
        // Poniższe trzy asercje są jedynym miejscem, które tę mutację wywraca.
        var lista = new[] { "surveyed", "modelled" };
        Assert.IsTrue(TrackAxis.IsModelledStatus("surveyed", lista),
            "status z listy ma dawać prawdę — inaczej lista nie jest czytana");
        Assert.IsTrue(TrackAxis.IsModelledStatus("modelled", lista));
        Assert.IsFalse(TrackAxis.IsModelledStatus("not_modelled", lista),
            "status spoza listy ma dawać fałsz");
        Assert.IsFalse(TrackAxis.IsModelledStatus("SURVEYED", lista),
            "porównanie jest Ordinal: status pochodzi z pliku, nie od człowieka");
    }

    /// <summary>
    /// Nazwa do pokazania jest brana z GOTOWEGO pola danych, a nie parsowana
    /// z separatora — 6.D83.
    /// </summary>
    [TestMethod]
    public void Nazwa_do_pokazania_pochodzi_z_pola_jednojezycznego()
    {
        var axis = TrackAxis.FromJson(JsonZeStacja(
            "Comte de Flandre|Graaf van Vlaanderen", "Comte De Flandre", "Graaf Van Vlaand."));
        var station = axis.Stations[0];

        Assert.AreEqual("Comte de Flandre|Graaf van Vlaanderen", station.Name,
            "nazwa dwujęzyczna zostaje NIETKNIĘTA — po niej idą ślady przejazdu "
            + "i porównanie wywołań scena-rdzeń, przybite sumą SHA-256");
        Assert.AreEqual("Comte De Flandre", station.NameFr);
        Assert.AreEqual("Graaf Van Vlaand.", station.NameNl);
        Assert.AreEqual("Comte De Flandre", station.DisplayName);
        Assert.IsFalse(station.DisplayName.Contains('|'),
            "nazwa do pokazania niesie separator, czyli jest złączona, a nie wybrana");
    }

    /// <summary>
    /// Brak pola jednojęzycznego daje CAŁĄ nazwę, a nie jej kawałek. Separatora
    /// nie parsujemy — pole „Wyjście" pozycji 6.D83 mówi o tym wprost.
    /// </summary>
    [TestMethod]
    public void Bez_pola_jednojezycznego_nazwa_do_pokazania_nie_jest_ciachana()
    {
        var station = TrackAxis.FromJson(JsonZeStacja("Alfa|Beta", null, null)).Stations[0];

        Assert.AreEqual(string.Empty, station.NameFr);
        Assert.AreEqual("Alfa|Beta", station.DisplayName,
            "przy braku pola jednojęzycznego nazwa ma zostać CAŁA — ucięcie jej "
            + "na separatorze byłoby parsowaniem, którego ta pozycja zabrania");
    }

    /// <summary>
    /// Kontrola na PRAWDZIWYCH danych: pola jednojęzyczne są kompletne, a separator
    /// niesie mniejszość nazw. Liczby są zmierzone 10.09.2026 i stoją tu po to, żeby
    /// zmiana w danych była widoczna, a nie cicha.
    /// </summary>
    [TestMethod]
    public void Wszystkie_stacje_w_danych_maja_nazwe_jednojezyczna()
    {
        var root = FindRepositoryRoot();
        if (root is null)
        {
            Assert.Inconclusive("brak repozytorium na dysku — kontrola danych pominięta");
            return;
        }

        var stacji = 0;
        var bezFr = 0;
        var zSeparatorem = 0;
        var zSeparatoremWPokazywanej = 0;
        // Wzorzec `L*_?.json`, a nie `*.json`: obok osi leżą pliki `*.provenance.json`,
        // które osiami nie są i wywracają rozbiór na pierwszym `points`. Zmierzone
        // przy pisaniu tego testu — `*.json` daje dwanaście plików, a osi jest sześć.
        foreach (var plik in Directory.GetFiles(Path.Combine(root, "data", "track"), "*.json")
                     .Where(f => !f.EndsWith(".provenance.json", StringComparison.Ordinal))
                     .OrderBy(f => f, StringComparer.Ordinal))
        {
            foreach (var station in TrackAxis.FromJson(File.ReadAllText(plik)).Stations)
            {
                stacji++;
                if (station.NameFr.Length == 0)
                {
                    bezFr++;
                }

                if (station.Name.Contains('|'))
                {
                    zSeparatorem++;
                }

                if (station.DisplayName.Contains('|'))
                {
                    zSeparatoremWPokazywanej++;
                }
            }
        }

        Assert.AreEqual(61, stacji, "liczba stacji w danych osi zmieniła się");
        Assert.AreEqual(0, bezFr, "stacja bez `name_fr` — nazwa do pokazania spadnie "
                                  + "na dwujęzyczną, czyli na ten napis, który ucinał wiersz");
        Assert.AreEqual(27, zSeparatorem,
            "liczba nazw z separatorem zmieniła się — pomiar 6.D83 dotyczył 27 z 61");
        Assert.AreEqual(0, zSeparatoremWPokazywanej,
            "nazwa do pokazania nadal niesie separator w " + zSeparatoremWPokazywanej + " stacjach");
    }

    private static string JsonZeStacja(string name, string? nameFr, string? nameNl)
    {
        var pola = string.Create(CultureInfo.InvariantCulture, $"\"name\":\"{name}\"");
        if (nameFr is not null)
        {
            pola += string.Create(CultureInfo.InvariantCulture, $",\"name_fr\":\"{nameFr}\"");
        }

        if (nameNl is not null)
        {
            pola += string.Create(CultureInfo.InvariantCulture, $",\"name_nl\":\"{nameNl}\"");
        }

        return string.Create(
            CultureInfo.InvariantCulture,
            $$"""{"id":"T","length_m":0.0,"vertical":{"status":"not_modelled"},"points":[[0.0,0.0,0.0],[100.0,0.0,0.0]],"stations":[{{{pola}},"chainage_m":50.0,"stop_id":"s1"}]}""");
    }

    private static string JsonBezProfilu(params (double X, double Y)[] points)
    {
        var coordinates = string.Join(",", points.Select(p => string.Create(
            CultureInfo.InvariantCulture, $"[{p.X:R},{p.Y:R},0.0]")));
        return string.Create(
            CultureInfo.InvariantCulture,
            $$"""{"id":"T","length_m":0.0,"points":[{{coordinates}}],"stations":[]}""");
    }

    private static string JsonZeStatusem(string status, params (double X, double Y)[] points)
    {
        var coordinates = string.Join(",", points.Select(p => string.Create(
            CultureInfo.InvariantCulture, $"[{p.X:R},{p.Y:R},0.0]")));
        return string.Create(
            CultureInfo.InvariantCulture,
            $$"""{"id":"T","length_m":0.0,"vertical":{"status":"{{status}}"},"points":[{{coordinates}}],"stations":[]}""");
    }

    private static string Json(params (double X, double Y)[] points)
    {
        var coordinates = string.Join(",", points.Select(p => string.Create(
            CultureInfo.InvariantCulture, $"[{p.X:R},{p.Y:R},0.0]")));
        return string.Create(
            CultureInfo.InvariantCulture,
            $$"""{"id":"T","length_m":0.0,"vertical":{"status":"not_modelled"},"points":[{{coordinates}}],"stations":[]}""");
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

    [TestMethod]
    public void CoversChordSaysWhenAChordHasNoLengthOnThisAxis()
    {
        // `PointAt` PRZYCINA kilometraż, więc dwa różne kilometraże leżące oba przed
        // początkiem dają ten sam punkt — i cięciwę zerowej długości, z której nie da
        // się zbudować ramki. Widok składu pytał o takie cięciwy przy przejeździe
        // rozpoczętym na kilometrażu 0: ogon leżał wtedy 94 m przed osią.
        var axis = TrackAxis.FromJson(Json((0.0, 0.0), (100.0, 0.0), (200.0, 0.0)));
        var length = axis.LengthM;

        Assert.IsTrue(axis.CoversChord(0.0, 15.0), "cięciwa w środku osi");
        Assert.IsTrue(axis.CoversChord(-10.0, 15.0), "cięciwa wchodząca na oś z lewej");
        Assert.IsTrue(axis.CoversChord(length - 5.0, length + 50.0), "wychodząca za koniec");

        Assert.IsFalse(axis.CoversChord(-95.0, -80.0), "cięciwa CAŁA przed osią");
        Assert.IsFalse(axis.CoversChord(length + 1.0, length + 20.0), "cięciwa CAŁA za osią");
        Assert.IsFalse(axis.CoversChord(50.0, 50.0), "cięciwa zdegenerowana do punktu");

        // Granica: koniec dokładnie w zerze to jeszcze nie cięciwa, bo drugi koniec
        // też przycina się do zera.
        Assert.IsFalse(axis.CoversChord(-15.0, 0.0), "oba końce przycięte do zera");
        Assert.IsTrue(axis.CoversChord(-15.0, 1e-9), "koniec o nanometr na osi już wystarcza");

        // Wartości niepoliczalne są ODMOWĄ, nie wyjątkiem: widok pyta o to raz na
        // bryłę na klatkę i nie ma sensownej reakcji na NaN poza „nie rysuj".
        Assert.IsFalse(axis.CoversChord(double.NaN, 10.0));
        Assert.IsFalse(axis.CoversChord(0.0, double.PositiveInfinity));
    }

    /// <summary>
    /// Tolerancja kilometrażu jest JEDNĄ liczbą w jednym miejscu — i to jest cały ten test.
    /// </summary>
    [TestMethod]
    public void Tolerancja_kilometrazu_jest_jedna_liczba_w_calym_rdzeniu()
    {
        // Do 05.09.2026 `PositionEpsilonM` stała w dwóch egzemplarzach: w
        // `Signalling.FixedBlockSystem` i w `Train.LineDrive`. Komentarz przy drugiej
        // mówił „ta sama co w FixedBlockSystem", ale komentarz nie jest bramką: rozjazd
        // wartości nie dałby ani błędu kompilacji, ani czerwonego testu — dałby dwa różne
        // progi „to jest to samo miejsce" w dwóch warstwach jednego modelu
        // (reports/mutacje-rdzen-sygnalizacji.md §9.2, pozycja 8 z sekcji 8).
        //
        // Test czyta metadane zestawu, a nie źródła, bo interesuje go DEKLARACJA, a nie
        // to, jak wygląda: `const` jest wstawiany w miejscu użycia, więc drugi egzemplarz
        // o innej wartości byłby niewidoczny w zachowaniu jednej warstwy z punktu widzenia
        // testów drugiej. Ponowne dopisanie stałej gdziekolwiek w `src/Sim` wywraca ten
        // test na pierwszej asercji.
        var declarations = typeof(TrackAxis).Assembly.GetTypes()
            .SelectMany(type => type.GetFields(
                BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Static | BindingFlags.DeclaredOnly))
            .Where(field => field.IsLiteral
                && !field.IsInitOnly
                && string.Equals(field.Name, nameof(TrackAxis.PositionEpsilonM), StringComparison.Ordinal))
            .OrderBy(field => field.DeclaringType!.FullName, StringComparer.Ordinal)
            .ToList();

        Assert.AreEqual(
            1,
            declarations.Count,
            "tolerancja kilometrażu jest zadeklarowana w: "
                + string.Join("; ", declarations.Select(f => f.DeclaringType!.FullName)));

        Assert.AreEqual(
            typeof(TrackAxis).FullName,
            declarations[0].DeclaringType!.FullName,
            "kilometraż jest współrzędną osi, więc granica jego rozdzielczości należy do osi");

        // Wartość przypięta liczbą, nie wyprowadzeniem, bo wyprowadzenia nie ma: 1e-9 m
        // to granica rozdzielczości `double` na kilometrażu rzędu 10 km, a nie odległość
        // dobrana z modelu. Przybicie progu ZACHOWANIEM (cofnięcie o 1e-8 m jest odmową,
        // o 1e-10 m przechodzi) jest osobną pozycją kolejki — sekcja 8, pozycja 7 tego
        // samego raportu — i nie należy do tej zmiany.
        Assert.AreEqual(1e-9, (double)declarations[0].GetRawConstantValue()!, 0.0);
    }
}
