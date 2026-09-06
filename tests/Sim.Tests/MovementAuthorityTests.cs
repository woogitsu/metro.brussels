using System;
using System.Globalization;
using MetroBxl.Sim.Signalling;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace MetroBxl.Sim.Tests;

/// <summary>
/// Typy wartościowe warstwy sygnalizacji: <see cref="MovementAuthority"/>,
/// <see cref="Block"/> i <see cref="Route"/>. Pliku <c>Block.cs</c> do 6.A8 nie nazywał
/// żaden test, a <c>MovementAuthority.cs</c> nazywał wyłącznie
/// <c>tests/Game.Tests/SignallingHudTests.cs</c> — czyli warstwa kabiny, przez zaślepkę.
///
/// <para><b>Czym te testy różnią się od <see cref="FixedBlockTests"/>.</b> Tamte pytają
/// <see cref="FixedBlockSystem"/>, czy przy takim rozstawieniu składów wyjdzie takie
/// authority — sprawdzają więc <b>system</b>, a bloki i authority są w nich wynikiem.
/// Tu system nie występuje ani razu: bloki i authority są budowane wprost, z liczbami
/// dobranymi pod granicę. Reguła półotwartości <c>[Start, End)</c> jest w tym modelu
/// warunkiem tego, żeby skład stojący dokładnie na styku nie zajmował dwóch bloków
/// naraz, więc granica jest tu przedmiotem, a nie przypadkiem brzegowym.</para>
///
/// <para><b>Liczby są syntetyczne i takie mają być</b> — dokładnie z powodu podanego
/// w <see cref="FixedBlockTests"/>: granice bloków pakietu A są <c>design_model</c>,
/// więc przypięcie ich tutaj przypięłoby założenie zamiast zachowania.</para>
/// </summary>
[TestClass]
public sealed class MovementAuthorityTests
{
    private static Block Interstation(double startM, double endM) =>
        new("S01", startM, endM, BlockKind.Interstation, string.Empty);

    private static Block Platform(double startM, double endM) =>
        new("P01", startM, endM, BlockKind.Platform, "Gare du Midi|Zuidstation");

    private static Route RouteOf(string id, params string[] blockIds) =>
        new(id, blockIds[0], blockIds[^1], blockIds);

    // --- MovementAuthority ------------------------------------------------------------

    /// <summary>
    /// Odległość jest mierzona od czoła składu do końca authority — w tę stronę, bo
    /// właśnie tyle metrów zostaje do przejechania. Zamiana odjemnej z odjemnikiem daje
    /// liczbę ujemną, którą <c>Math.Max</c> zetnie do zera, więc pomyłka nie objawia się
    /// znakiem, tylko cichym „stój".
    /// </summary>
    [TestMethod]
    public void Odleglosc_authority_liczy_sie_od_czola_skladu_do_jego_konca()
    {
        var authority = new MovementAuthority("A", 200.0, 500.0, "S02", AuthorityLimit.OccupiedBlock);

        Assert.AreEqual(300.0, authority.DistanceM, 0.0);
        Assert.IsTrue(authority.AllowsMovement);
    }

    /// <summary>
    /// Authority kończące się <b>za</b> czołem składu — po cofnięciu granicy albo po
    /// zajęciu bloku pod stojącym już składem — daje zero metrów, a nie metry ujemne.
    /// Liczba ujemna poszłaby do krzywej hamowania i wyszłaby z niej jako prędkość
    /// dozwolona, więc obcięcie jest tu częścią kontraktu, a nie kosmetyką.
    /// </summary>
    [TestMethod]
    public void Odleglosc_authority_nigdy_nie_jest_ujemna()
    {
        var behind = new MovementAuthority("A", 200.0, 100.0, "S01", AuthorityLimit.OccupiedBlock);

        Assert.AreEqual(0.0, behind.DistanceM, 0.0);
        Assert.IsFalse(double.IsNegative(behind.DistanceM), "zero ma być dodatnie, nie „minus zero”");
        Assert.IsFalse(behind.AllowsMovement);
    }

    /// <summary>
    /// Granica prawa jazdy: zero metrów to zakaz, a najmniejsza dodatnia odległość to
    /// już pozwolenie. Przesunięcie progu na <c>&gt;=</c> puszcza skład przy authority
    /// kończącym się dokładnie na jego czole.
    /// </summary>
    [TestMethod]
    public void Prawo_jazdy_gasnie_dokladnie_przy_zerowej_odleglosci()
    {
        var touching = new MovementAuthority("A", 200.0, 200.0, "S01", AuthorityLimit.OccupiedBlock);
        var barely = new MovementAuthority("A", 200.0, Math.BitIncrement(200.0), "S01", AuthorityLimit.OccupiedBlock);

        Assert.AreEqual(0.0, touching.DistanceM, 0.0);
        Assert.IsFalse(touching.AllowsMovement, "authority na czole składu nie pozwala ruszyć");
        Assert.IsTrue(barely.AllowsMovement, "najmniejsza dodatnia odległość to już pozwolenie");
    }

    /// <summary>
    /// Powód skrócenia authority jest jego częścią, a nie komentarzem, więc idzie do
    /// wiersza razem z blokiem ograniczającym. Wiersz trafia do logu przebiegu, więc
    /// nie zależy od kultury maszyny — sprawdzone kulturą z przecinkiem dziesiętnym.
    /// </summary>
    [TestMethod]
    public void Wiersz_authority_niesie_powod_i_blok_ograniczajacy_niezaleznie_od_kultury()
    {
        var previous = CultureInfo.CurrentCulture;
        var comma = (CultureInfo)CultureInfo.InvariantCulture.Clone();
        comma.NumberFormat.NumberDecimalSeparator = ",";
        CultureInfo.CurrentCulture = comma;
        try
        {
            var line = new MovementAuthority("A", 200.0, 500.0, "S02", AuthorityLimit.ReservedByOtherRoute).ToString();

            Console.WriteLine(line);
            StringAssert.Contains(line, "ReservedByOtherRoute");
            StringAssert.Contains(line, "S02");
            StringAssert.Contains(line, "500.00 m");
            StringAssert.Contains(line, "300.00 m");
        }
        finally
        {
            CultureInfo.CurrentCulture = previous;
        }
    }

    // --- Block ------------------------------------------------------------------------

    /// <summary>
    /// Półotwartość <c>[Start, End)</c>: początek należy do bloku, koniec już nie.
    /// To jest ta reguła, bez której skład stojący na granicy zajmowałby dwa bloki
    /// naraz — więc obie strony granicy są sprawdzone co do bitu, a nie „z zapasem".
    /// </summary>
    [TestMethod]
    public void Blok_jest_polotwarty_poczatek_nalezy_koniec_juz_nie()
    {
        var block = Interstation(47.0, 553.0);

        Assert.IsTrue(block.Contains(47.0), "początek należy do bloku");
        Assert.IsTrue(block.Contains(Math.BitDecrement(553.0)), "tuż przed końcem jeszcze w bloku");
        Assert.IsFalse(block.Contains(553.0), "koniec należy już do bloku następnego");
        Assert.IsFalse(block.Contains(Math.BitDecrement(47.0)), "tuż przed początkiem jeszcze poza blokiem");
    }

    /// <summary>Długość i rola: dwie liczby, które czyta plan i raport kilometrażu.</summary>
    [TestMethod]
    public void Blok_podaje_swoja_dlugosc_i_role()
    {
        var interstation = Interstation(47.0, 553.0);
        var platform = Platform(0.0, 47.0);

        Assert.AreEqual(506.0, interstation.LengthM, 0.0);
        Assert.AreEqual(47.0, platform.LengthM, 0.0);
        Assert.IsFalse(interstation.IsPlatform);
        Assert.IsTrue(platform.IsPlatform);
    }

    /// <summary>
    /// Przecięcie z odcinkiem <c>[from, to]</c> — czyli ze składem o niezerowej długości
    /// — dziedziczy półotwartość bloku. Skład kończący się dokładnie na początku bloku
    /// jeszcze go nie zajmuje, a zaczynający się dokładnie na jego końcu już go opuścił.
    /// </summary>
    [TestMethod]
    public void Przeciecie_ze_skladem_dziedziczy_polotwartosc_granic()
    {
        var block = Interstation(47.0, 553.0);

        Assert.IsTrue(block.Overlaps(0.0, 100.0), "skład wjeżdżający zajmuje blok");
        Assert.IsTrue(block.Overlaps(500.0, 600.0), "skład wyjeżdżający jeszcze go zajmuje");
        Assert.IsTrue(block.Overlaps(0.0, 600.0), "skład dłuższy od bloku zajmuje go w całości");

        Assert.IsFalse(block.Overlaps(553.0, 600.0), "odcinek zaczynający się na końcu bloku już go nie dotyka");
        Assert.IsFalse(block.Overlaps(0.0, 47.0), "odcinek kończący się na początku bloku jeszcze go nie dotyka");
    }

    /// <summary>
    /// Odcinek zdegenerowany do punktu — skład o zerowej długości, czyli sam punkt
    /// zatrzymania — musi zachowywać się jak <see cref="Block.Contains"/>. Gdyby szedł
    /// tą samą gałęzią co odcinek niezdegenerowany, warunek <c>to &gt; Start &amp;&amp; from &lt; End</c>
    /// dawałby dla punktu wewnątrz bloku prawdę tylko przypadkiem, a na granicy nigdy.
    /// </summary>
    [TestMethod]
    public void Odcinek_zdegenerowany_do_punktu_dziala_jak_zawieranie()
    {
        var block = Interstation(47.0, 553.0);

        Assert.IsTrue(block.Overlaps(47.0, 47.0), "punkt na początku bloku leży w bloku");
        Assert.IsTrue(block.Overlaps(300.0, 300.0));
        Assert.IsFalse(block.Overlaps(553.0, 553.0), "punkt na końcu bloku leży już w następnym");
        Assert.IsFalse(block.Overlaps(600.0, 600.0));

        foreach (var chainage in new[] { 46.0, 47.0, 300.0, 553.0, 600.0 })
        {
            Assert.AreEqual(
                block.Contains(chainage),
                block.Overlaps(chainage, chainage),
                string.Create(CultureInfo.InvariantCulture, $"rozjazd na chainage {chainage}"));
        }
    }

    /// <summary>
    /// Odcinek odwrócony jest błędem wołającego, a nie odcinkiem pustym: przy cichym
    /// przyjęciu skład z pomylonymi końcami nie zajmowałby żadnego bloku i zniknąłby
    /// z widoku sygnalizacji zamiast wywalić przebieg.
    /// </summary>
    [TestMethod]
    public void Odcinek_odwrocony_jest_odrzucony_a_nie_uznany_za_pusty()
    {
        var block = Interstation(47.0, 553.0);

        var error = Assert.ThrowsException<ArgumentOutOfRangeException>(() => block.Overlaps(300.0, 200.0));
        Assert.AreEqual("toM", error.ParamName);

        // Granica: odcinek zdegenerowany jest jeszcze poprawny, dopiero krótszy o jeden ULP już nie.
        Assert.IsTrue(block.Overlaps(300.0, 300.0));
        Assert.ThrowsException<ArgumentOutOfRangeException>(() => block.Overlaps(300.0, Math.BitDecrement(300.0)));
    }

    /// <summary>Wiersz bloku niesie granice, długość i rolę, kulturą niezmienną.</summary>
    [TestMethod]
    public void Wiersz_bloku_niesie_granice_dlugosc_i_role()
    {
        var previous = CultureInfo.CurrentCulture;
        var comma = (CultureInfo)CultureInfo.InvariantCulture.Clone();
        comma.NumberFormat.NumberDecimalSeparator = ",";
        CultureInfo.CurrentCulture = comma;
        try
        {
            var platform = Platform(0.0, 47.0).ToString();
            var interstation = Interstation(47.0, 553.0).ToString();

            Console.WriteLine(platform);
            Console.WriteLine(interstation);

            StringAssert.Contains(platform, "[0.00, 47.00)");
            StringAssert.Contains(platform, "47.00 m");
            StringAssert.Contains(platform, "Gare du Midi|Zuidstation");
            StringAssert.Contains(interstation, "506.00 m");
            Assert.IsFalse(
                interstation.Contains('—', StringComparison.Ordinal),
                $"blok szlakowy nie ma stacji, więc nie ma jej dopisywać: {interstation}");
        }
        finally
        {
            CultureInfo.CurrentCulture = previous;
        }
    }

    // --- Route ------------------------------------------------------------------------

    /// <summary>
    /// Jedyne kryterium konfliktu w tym modelu: wspólny blok. Trasy rozłączne nie są
    /// w konflikcie nawet wtedy, gdy stykają się końcami, a relacja jest symetryczna —
    /// odrzucenie żądania nie może zależeć od tego, którą trasę spytano pierwszą.
    /// </summary>
    [TestMethod]
    public void Trasy_sa_w_konflikcie_dokladnie_wtedy_gdy_dziela_blok()
    {
        var west = RouteOf("R1", "P01", "S01", "P02");
        var east = RouteOf("R2", "P03", "S03", "P04");
        var crossing = RouteOf("R3", "P02", "S02", "P03");

        Assert.IsFalse(west.ConflictsWith(east));
        Assert.IsFalse(east.ConflictsWith(west));

        Assert.IsTrue(west.ConflictsWith(crossing), "P02 należy do obu tras");
        Assert.IsTrue(crossing.ConflictsWith(west));
        Assert.IsTrue(west.ConflictsWith(west), "trasa jest w konflikcie sama ze sobą");
    }

    /// <summary>
    /// Identyfikatory bloków porównują się dokładnie. Porównanie bez względu na wielkość
    /// liter albo z regułami kultury zamieniłoby dwa różne bloki w jeden i odrzuciło
    /// trasę, która konfliktu nie ma — a przy tureckim <c>i</c> zrobiłoby to zależnie
    /// od ustawień maszyny.
    /// </summary>
    [TestMethod]
    public void Identyfikatory_blokow_porownuja_sie_dokladnie()
    {
        var upper = RouteOf("R1", "P01", "S01");
        var lower = RouteOf("R2", "p01", "s01");

        Assert.IsFalse(upper.ConflictsWith(lower), "P01 i p01 to dwa różne bloki");
        Assert.IsTrue(upper.ConflictsWith(RouteOf("R3", "S01", "P02")));
    }

    /// <summary>
    /// <c>default(Route)</c> ma listę bloków równą <c>null</c> — struktury w C# zawsze da
    /// się utworzyć z pominięciem konstruktora. Pytanie o konflikt z taką trasą jest
    /// błędem wołającego i ma paść nazwanym wyjątkiem, a nie <c>NullReferenceException</c>
    /// z wnętrza pętli.
    /// </summary>
    [TestMethod]
    public void Konflikt_z_trasa_bez_listy_blokow_jest_odrzucony_nazwanym_wyjatkiem()
    {
        var route = RouteOf("R1", "P01", "S01");

        Assert.ThrowsException<ArgumentNullException>(() => route.ConflictsWith(default));
    }

    /// <summary>Wiersz trasy niesie oba końce i pełną listę bloków, w kolejności chainage.</summary>
    [TestMethod]
    public void Wiersz_trasy_niesie_konce_i_pelna_liste_blokow()
    {
        var line = RouteOf("R1", "P01", "S01", "P02").ToString();

        Console.WriteLine(line);
        StringAssert.Contains(line, "R1: P01 → P02");
        StringAssert.Contains(line, "P01, S01, P02");
    }
}
