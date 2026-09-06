using System;
using System.Linq;
using MetroBxl.Sim.Line;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace MetroBxl.Sim.Tests;

/// <summary>
/// Doba służby odtworzona przez RDZEŃ (pozycja 6.A3).
///
/// <para><b>Dlaczego testy nie czytają prawdziwego rozkładu.</b> Rozkład powstaje
/// z archiwum GTFS, którego nie ma w drzewie — <c>data/gtfs/</c> i katalog wytworów
/// są w <c>.gitignore</c>, a pobranie wymaga sieci. Test wiążący się z tym plikiem
/// przechodziłby na maszynie, która akurat go ma, i padał w czystym checkoucie;
/// dokładnie tak wywrócił się jeden pull request 06.09.2026. Liczby z prawdziwego
/// feedu (71 obiegów, 56 naraz o 07:06:44) są zmierzone i wklejone
/// w <c>reports/service-day.md</c>, a tutaj sprawdzane są WŁASNOŚCI, które te liczby
/// produkują.</para>
/// </summary>
[TestClass]
public sealed class ServiceDayTests
{
    private static string Rozklad(string date, params string[] blocks) =>
        FormattableString.Invariant(
            $"{{\"date\":\"{date}\",\"duties\":{{\"rows\":[{string.Join(",", blocks)}]}}}}");

    private static string Blok(string id, params (int Start, int End)[] windows) =>
        FormattableString.Invariant(
            $"{{\"block_id\":\"{id}\",\"trips\":{windows.Length},\"trip_windows\":[")
        + string.Join(",", windows.Select(w => FormattableString.Invariant($"[{w.Start},{w.End}]")))
        + "]}";

    [TestMethod]
    public void Liczba_obiegow_to_liczba_wierszy_rozkladu()
    {
        var day = ServiceDay.FromJson(Rozklad("20260902",
            Blok("A", (100, 200)), Blok("B", (150, 260)), Blok("C", (400, 500))));

        Assert.AreEqual(3, day.BlockCount);
        Assert.AreEqual("20260902", day.Date);
    }

    [TestMethod]
    public void Szczyt_liczy_obiegi_naraz_i_podaje_chwile_pierwszego_wystapienia()
    {
        // A i B nakładają się w 150..200, C stoi osobno.
        var day = ServiceDay.FromJson(Rozklad("20260902",
            Blok("A", (100, 200)), Blok("B", (150, 260)), Blok("C", (400, 500))));

        var peak = day.Peak;
        Assert.AreEqual(2, peak.Blocks);
        Assert.AreEqual(150.0, peak.AtSeconds, 1e-9);
    }

    [TestMethod]
    public void Wejscie_liczy_sie_przed_wyjsciem_gdy_padaja_w_tej_samej_sekundzie()
    {
        // KLUCZOWA WŁASNOŚĆ, nie szczegół: przedział służby jest domknięty z obu stron,
        // więc w sekundzie 200 oba składy stoją na sieci. Odwrotna kolejność dałaby
        // szczyt 1 i wyglądałaby tak samo poprawnie — dlatego ma własny test.
        var day = ServiceDay.FromJson(Rozklad("20260902",
            Blok("A", (100, 200)), Blok("B", (200, 300))));

        Assert.AreEqual(2, day.Peak.Blocks);
        Assert.AreEqual(200.0, day.Peak.AtSeconds, 1e-9);
        Assert.AreEqual(2, day.ConcurrentAt(200.0));
    }

    [TestMethod]
    public void Przedzial_sluzby_jest_domkniety_z_obu_stron()
    {
        var day = ServiceDay.FromJson(Rozklad("20260902", Blok("A", (100, 200))));

        Assert.AreEqual(0, day.ConcurrentAt(99.0), "sekundę przed wyjazdem skład nie jest w służbie");
        Assert.AreEqual(1, day.ConcurrentAt(100.0), "w sekundzie wyjazdu już jest");
        Assert.AreEqual(1, day.ConcurrentAt(200.0), "w sekundzie przyjazdu jeszcze jest");
        Assert.AreEqual(0, day.ConcurrentAt(201.0), "sekundę po przyjeździe już nie");
    }

    [TestMethod]
    public void Ostatni_przyjazd_to_maksimum_a_nie_koniec_ostatniego_okna()
    {
        // Okna są w kolejności wyjazdów, ale kurs krótszy może skończyć się PÓŹNIEJ
        // niż następny po nim. Branie `Windows[^1].EndS` dałoby tu 250 zamiast 400.
        var day = ServiceDay.FromJson(Rozklad("20260902", Blok("A", (100, 400), (150, 250))));

        Assert.AreEqual(400.0, day.Blocks[0].LastArrivalS, 1e-9);
        Assert.AreEqual(300.0, day.Blocks[0].SpanSeconds, 1e-9);
    }

    [TestMethod]
    public void Nakladajace_sie_kursy_w_jednym_obiegu_sa_zgloszone_a_nie_przemilczane()
    {
        // Jeden pojazd nie jedzie dwoma kursami naraz — nakładka jest błędem w feedzie.
        var czysty = ServiceDay.FromJson(Rozklad("20260902", Blok("A", (100, 200), (200, 300))));
        Assert.AreEqual(0, czysty.OverlappingTripsInABlock, "styk w sekundzie 200 to nie nakładka");

        var zepsuty = ServiceDay.FromJson(Rozklad("20260902", Blok("A", (100, 250), (200, 300))));
        Assert.AreEqual(1, zepsuty.OverlappingTripsInABlock);
    }

    [TestMethod]
    public void Nakladki_licza_sie_po_wszystkich_obiegach()
    {
        var day = ServiceDay.FromJson(Rozklad("20260902",
            Blok("A", (100, 250), (200, 300)),
            Blok("B", (100, 250), (200, 300), (280, 400))));

        Assert.AreEqual(3, day.OverlappingTripsInABlock);
    }

    [TestMethod]
    public void Liczba_kursow_obiegu_to_liczba_okien()
    {
        var day = ServiceDay.FromJson(Rozklad("20260902", Blok("A", (1, 2), (3, 4), (5, 6))));
        Assert.AreEqual(3, day.Blocks[0].Trips);
    }

    [TestMethod]
    public void Godzina_wolno_przekroczyc_24_bo_doba_sluzby_konczy_sie_po_polnocy()
    {
        // 24:36:14 to prawdziwy ostatni przyjazd w feedzie STIB. Zawinięcie go do
        // 00:36:14 przeniosłoby skład o dobę wstecz i zbiłoby szczyt.
        Assert.AreEqual("24:36:14", ServiceDay.Clock((24 * 3600) + (36 * 60) + 14));
        Assert.AreEqual("07:06:44", ServiceDay.Clock((7 * 3600) + (6 * 60) + 44));
        Assert.AreEqual("00:00:00", ServiceDay.Clock(0.0));
    }

    [TestMethod]
    public void Szczyt_po_polnocy_zachowuje_godzine_wieksza_niz_24()
    {
        var day = ServiceDay.FromJson(Rozklad("20260902",
            Blok("A", (86000, 88000)), Blok("B", (87000, 89000))));

        Assert.AreEqual(2, day.Peak.Blocks);
        Assert.AreEqual("24:10:00", day.Peak.AtClock);
    }

    [TestMethod]
    public void Rozklad_bez_sekcji_obiegow_jest_odrzucony()
    {
        var problem = Assert.ThrowsException<ArgumentException>(
            () => ServiceDay.FromJson("{\"date\":\"20260902\"}"));
        StringAssert.Contains(problem.Message, "duties.rows");
    }

    [TestMethod]
    public void Rozklad_bez_okien_kursow_jest_odrzucony_a_nie_przyjety_po_cichu()
    {
        // Bez okien rdzeń mógłby co najwyżej przepisać liczby Pythona. Cicha zgoda
        // dałaby bramkę porównującą liczbę ze sobą samą.
        var problem = Assert.ThrowsException<ArgumentException>(() => ServiceDay.FromJson(
            "{\"date\":\"20260902\",\"duties\":{\"rows\":[{\"block_id\":\"A\",\"trips\":2}]}}"));
        StringAssert.Contains(problem.Message, "trip_windows");
        StringAssert.Contains(problem.Message, "A");
    }

    [TestMethod]
    public void Obieg_bez_ani_jednego_kursu_jest_odrzucony()
    {
        var problem = Assert.ThrowsException<ArgumentException>(() => ServiceDay.FromJson(
            "{\"date\":\"20260902\",\"duties\":{\"rows\":[{\"block_id\":\"A\",\"trip_windows\":[]}]}}"));
        StringAssert.Contains(problem.Message, "bez ani jednego kursu");
    }

    [TestMethod]
    public void Rozklad_bez_ani_jednego_obiegu_jest_odrzucony()
    {
        var problem = Assert.ThrowsException<ArgumentException>(() => ServiceDay.FromJson(
            "{\"date\":\"20260902\",\"duties\":{\"rows\":[]}}"));
        StringAssert.Contains(problem.Message, "bez ani jednego obiegu");
    }

    [TestMethod]
    public void Doba_z_jednym_obiegiem_ma_szczyt_jeden()
    {
        var day = ServiceDay.FromJson(Rozklad("20260902", Blok("A", (100, 200))));
        Assert.AreEqual(1, day.Peak.Blocks);
        Assert.AreEqual(100.0, day.Peak.AtSeconds, 1e-9);
        Assert.AreEqual(0, day.OverlappingTripsInABlock);
    }

    [TestMethod]
    public void Poza_doba_sluzby_nie_ma_w_sluzbie_nikogo()
    {
        var day = ServiceDay.FromJson(Rozklad("20260902",
            Blok("A", (100, 200)), Blok("B", (150, 260))));

        Assert.AreEqual(0, day.ConcurrentAt(0.0));
        Assert.AreEqual(0, day.ConcurrentAt(1_000_000.0));
    }
}
