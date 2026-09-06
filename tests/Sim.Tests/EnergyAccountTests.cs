using System;
using System.Globalization;
using System.Linq;
using MetroBxl.Sim.Physics;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace MetroBxl.Sim.Tests;

/// <summary>
/// Trzy typy wartościowe z <c>MetroBxl.Sim.Physics</c>, których do 6.A8 nie nazywał
/// żaden plik pod <c>tests/</c>: <see cref="EnergyAccount"/>,
/// <see cref="BrakingEnergyAccount"/> i <see cref="DesignParameter"/>.
///
/// <para><b>Czym te testy różnią się od <see cref="EnergyAndProfileTests"/>.</b> Tamte
/// pytają, czy bilans <b>przebiegu</b> się domyka — czyli mierzą całkowanie, a konto
/// energii jest w nich tylko naczyniem. Tu odwrotnie: przebiegu nie ma ani jednego,
/// są same konta budowane z liczb wpisanych wprost. Pytanie brzmi, co konto obiecuje
/// wołającemu, gdy dostanie takie liczby — łącznie z tymi, których żaden przebieg
/// nie wyprodukuje (zerowa praca trakcji, zerowy ubytek energii, zerowe opóźnienie).
/// Bilans, który domyka się na przebiegu, a dzieli przez zero na granicy, przechodzi
/// tamten plik i wywraca raport.</para>
///
/// <para><b>Liczby są arbitralne i takie mają być.</b> Konto energii nie zna ani M7,
/// ani sieci — dodaje i odejmuje to, co dostanie. Wstawienie tu masy składu albo
/// pracy z tablicy referencyjnej przypięłoby stałą, a nie zachowanie; wszystkie
/// wartości poniżej są dobrane tak, żeby wychodziły z arytmetyki double
/// <b>dokładnie</b>, więc porównania idą z tolerancją 0,0.</para>
/// </summary>
[TestClass]
public sealed class EnergyAccountTests
{
    /// <summary>Konto rozruchu domknięte do zera: 100 − 10 − 20 − 50 − 15 − 5 = 0.</summary>
    private static EnergyAccount Balanced() => new(
        TractionWorkJ: 100.0,
        ResistanceWorkJ: 10.0,
        GradeWorkJ: 20.0,
        KineticEnergyJ: 50.0,
        DiscretizationWorkJ: 15.0,
        ClampedWorkJ: 5.0);

    /// <summary>Konto hamowania domknięte do zera: 100 − 10 − 60 − 20 − 10 = 0.</summary>
    private static BrakingEnergyAccount BalancedBraking() => new(
        KineticLossJ: 100.0,
        ResistanceWorkJ: 10.0,
        BrakeWorkJ: 60.0,
        GradeWorkJ: 20.0,
        DiscretizationWorkJ: 10.0);

    /// <summary>Kultura z przecinkiem dziesiętnym, zbudowana bez pytania systemu o dane ICU.</summary>
    private static CultureInfo CommaCulture()
    {
        var culture = (CultureInfo)CultureInfo.InvariantCulture.Clone();
        culture.NumberFormat.NumberDecimalSeparator = ",";
        return culture;
    }

    /// <summary>Tekst wartości z wiersza katalogu: to, co stoi między <c>„= "</c> a <c>„  ("</c>.</summary>
    private static string ValueText(string line)
    {
        var from = line.IndexOf("= ", StringComparison.Ordinal) + 2;
        var to = line.IndexOf("  (", StringComparison.Ordinal);
        Assert.IsTrue(from > 1 && to > from, $"wiersz katalogu zmienił kształt: {line}");
        return line[from..to];
    }

    private static void WithCulture(CultureInfo culture, Action body)
    {
        var previous = CultureInfo.CurrentCulture;
        CultureInfo.CurrentCulture = culture;
        try
        {
            body();
        }
        finally
        {
            CultureInfo.CurrentCulture = previous;
        }
    }

    // --- EnergyAccount ----------------------------------------------------------------

    /// <summary>
    /// Reszta jest pracą trakcji pomniejszoną o <b>każdy</b> z pięciu pozostałych członów,
    /// z wagą dokładnie −1. Test podnosi po jednym członie i sprawdza, o ile spadła reszta:
    /// człon pominięty w sumie albo dodany zamiast odjęty daje tu inną liczbę, a nie
    /// „trochę inną".
    /// </summary>
    [TestMethod]
    public void Reszta_bilansu_odejmuje_kazdy_z_pieciu_czlonow_z_waga_minus_jeden()
    {
        var balanced = Balanced();
        Assert.AreEqual(0.0, balanced.ResidualJ, 0.0, "konto wzorcowe ma się domykać");

        Assert.AreEqual(7.0, (balanced with { TractionWorkJ = 107.0 }).ResidualJ, 0.0, "praca trakcji");
        Assert.AreEqual(-7.0, (balanced with { ResistanceWorkJ = 17.0 }).ResidualJ, 0.0, "opory");
        Assert.AreEqual(-7.0, (balanced with { GradeWorkJ = 27.0 }).ResidualJ, 0.0, "pochylenie");
        Assert.AreEqual(-7.0, (balanced with { KineticEnergyJ = 57.0 }).ResidualJ, 0.0, "energia kinetyczna");
        Assert.AreEqual(-7.0, (balanced with { DiscretizationWorkJ = 22.0 }).ResidualJ, 0.0, "dyskretyzacja");
        Assert.AreEqual(-7.0, (balanced with { ClampedWorkJ = 12.0 }).ResidualJ, 0.0, "obcięcie");
    }

    /// <summary>
    /// Reszta względna jest wartością bezwzględną odniesioną do wartości bezwzględnej
    /// pracy trakcji — nigdy liczbą ujemną, także gdy bilans nie domyka się „w drugą stronę".
    /// </summary>
    [TestMethod]
    public void Reszta_wzgledna_jest_nieujemna_takze_przy_ujemnym_niedomknieciu()
    {
        var over = Balanced() with { TractionWorkJ = 200.0 };   // reszta +100
        var under = Balanced() with { ClampedWorkJ = 9.0 };     // reszta −4 przy trakcji 100

        Assert.AreEqual(100.0, over.ResidualJ, 0.0);
        Assert.AreEqual(0.5, over.RelativeResidual, 0.0);

        Assert.AreEqual(-4.0, under.ResidualJ, 0.0);
        Assert.AreEqual(0.04, under.RelativeResidual, 1e-15, "znak niedomknięcia nie może przeciekać do miary");
    }

    /// <summary>
    /// Granica, której żaden przebieg nie wyprodukuje, a raport tak: przy zerowej pracy
    /// trakcji miara względna nie ma mianownika. Kontrakt mówi <b>zero</b>, a nie
    /// nieskończoność i nie NaN — bo miarę wypisuje się w tabeli obok liczb, a nie
    /// porównuje z progiem w milczeniu. Reszta bezwzględna w tym samym koncie zostaje
    /// niezerowa i to ona niesie informację.
    /// </summary>
    [TestMethod]
    public void Reszta_wzgledna_przy_zerowej_pracy_trakcji_jest_zerem_a_nie_nieskonczonoscia()
    {
        var idle = new EnergyAccount(0.0, 3.0, 0.0, 0.0, 0.0, 0.0);

        Assert.AreEqual(-3.0, idle.ResidualJ, 0.0, "niedomknięcie nie znika, znika tylko jego miara");
        Assert.AreEqual(0.0, idle.RelativeResidual, 0.0);
        Assert.IsFalse(double.IsNaN(idle.RelativeResidual));
        Assert.IsFalse(double.IsInfinity(idle.RelativeResidual));
    }

    /// <summary>Kilowatogodzina to 3,6 MJ; przeliczenie idzie w tę stronę, a nie w odwrotną.</summary>
    [TestMethod]
    public void Praca_trakcji_w_kilowatogodzinach_dzieli_dzule_przez_trzy_i_szesc_miliona()
    {
        var account = Balanced() with { TractionWorkJ = 7_200_000.0 };

        Assert.AreEqual(2.0, account.TractionWorkKwh, 0.0);
        Assert.AreEqual(0.0, (Balanced() with { TractionWorkJ = 0.0 }).TractionWorkKwh, 0.0);
    }

    /// <summary>
    /// Wiersz konta trafia do raportu, więc nie wolno mu zależeć od ustawień maszyny,
    /// która go wypisała. Test podstawia kulturę z przecinkiem dziesiętnym i sprawdza,
    /// że w wyjściu nadal stoi kropka.
    /// </summary>
    [TestMethod]
    public void Wiersz_konta_rozruchu_nie_zalezy_od_kultury_maszyny()
    {
        WithCulture(CommaCulture(), () =>
        {
            var line = (Balanced() with { TractionWorkJ = 7_200_000.0 }).ToString();

            Console.WriteLine(line);
            StringAssert.Contains(line, "2.0000 kWh");
            Assert.IsFalse(line.Contains("2,0000", StringComparison.Ordinal), $"przecinek dziesiętny: {line}");
        });
    }

    // --- BrakingEnergyAccount ---------------------------------------------------------

    /// <summary>
    /// Bilans hamowania: ubytek energii kinetycznej minus cztery człony, każdy z wagą −1.
    /// Ta sama metoda co przy rozruchu i z tego samego powodu — konto, w którym jeden człon
    /// wchodzi ze złym znakiem, domyka się na przebiegu symetrycznym i rozjeżdża na innym.
    /// </summary>
    [TestMethod]
    public void Reszta_bilansu_hamowania_odejmuje_kazdy_z_czterech_czlonow_z_waga_minus_jeden()
    {
        var balanced = BalancedBraking();
        Assert.AreEqual(0.0, balanced.ResidualJ, 0.0, "konto wzorcowe ma się domykać");

        Assert.AreEqual(7.0, (balanced with { KineticLossJ = 107.0 }).ResidualJ, 0.0, "ubytek energii");
        Assert.AreEqual(-7.0, (balanced with { ResistanceWorkJ = 17.0 }).ResidualJ, 0.0, "opory");
        Assert.AreEqual(-7.0, (balanced with { BrakeWorkJ = 67.0 }).ResidualJ, 0.0, "hamulec");
        Assert.AreEqual(-7.0, (balanced with { GradeWorkJ = 27.0 }).ResidualJ, 0.0, "pochylenie");
        Assert.AreEqual(-7.0, (balanced with { DiscretizationWorkJ = 17.0 }).ResidualJ, 0.0, "dyskretyzacja");
    }

    /// <summary>
    /// Granica bliźniacza do rozruchowej, ale mianownik jest inny: przy zerowym ubytku
    /// energii kinetycznej — czyli hamowaniu, które niczego nie wyhamowało — miara
    /// względna ma być zerem.
    /// </summary>
    [TestMethod]
    public void Reszta_wzgledna_hamowania_przy_zerowym_ubytku_energii_jest_zerem()
    {
        var nothing = new BrakingEnergyAccount(0.0, 2.0, 0.0, 0.0, 0.0);

        Assert.AreEqual(-2.0, nothing.ResidualJ, 0.0);
        Assert.AreEqual(0.0, nothing.RelativeResidual, 0.0);
        Assert.IsFalse(double.IsNaN(nothing.RelativeResidual));
        Assert.IsFalse(double.IsInfinity(nothing.RelativeResidual));

        var real = BalancedBraking() with { BrakeWorkJ = 56.0 };  // reszta +4 przy ubytku 100
        Assert.AreEqual(0.04, real.RelativeResidual, 1e-15);
    }

    /// <summary>
    /// Zamiana bilansu na metry: praca oporów podzielona przez siłę hamowania
    /// <c>m_ef · b</c>. 1000 J na 100 kg przy 2 m/s² to 5 m i nic ponadto — metoda
    /// nie zna ani prędkości, ani reszty konta.
    /// </summary>
    [TestMethod]
    public void Skrocenie_drogi_przez_opory_to_praca_oporow_przez_sile_hamowania()
    {
        var account = new BrakingEnergyAccount(0.0, 1000.0, 0.0, 0.0, 0.0);

        Assert.AreEqual(5.0, account.ResistanceShorteningM(100.0, 2.0), 0.0);
        Assert.AreEqual(2.5, account.ResistanceShorteningM(200.0, 2.0), 0.0, "dwa razy cięższy skład — połowa metrów");
        Assert.AreEqual(2.5, account.ResistanceShorteningM(100.0, 4.0), 0.0, "dwa razy mocniejszy hamulec — połowa metrów");
        Assert.AreEqual(
            0.0,
            (account with { ResistanceWorkJ = 0.0 }).ResistanceShorteningM(100.0, 2.0),
            0.0,
            "bez oporów nie ma czego zamieniać na metry");
    }

    /// <summary>
    /// Zerowe opóźnienie to dzielenie przez zero, a wynikiem byłaby nieskończoność
    /// metrów wpisana do raportu jako skrócenie drogi hamowania. Metoda ma odmówić,
    /// i to na granicy — zero jest odrzucone, a nie „prawie zero".
    /// </summary>
    [TestMethod]
    public void Skrocenie_drogi_odrzuca_opoznienie_niedodatnie_i_nieskonczone()
    {
        var account = new BrakingEnergyAccount(0.0, 1000.0, 0.0, 0.0, 0.0);

        foreach (var deceleration in new[] { 0.0, -1.0, double.NaN, double.PositiveInfinity })
        {
            var error = Assert.ThrowsException<ArgumentOutOfRangeException>(
                () => account.ResistanceShorteningM(100.0, deceleration),
                $"opóźnienie {deceleration} zostało przyjęte");
            Assert.AreEqual("decelerationMps2", error.ParamName);
        }

        // Granica po drugiej stronie: najmniejsze dodatnie opóźnienie jest jeszcze
        // przyjmowane — próg ma odcinać zero, a nie wszystko, co małe.
        Assert.IsTrue(account.ResistanceShorteningM(100.0, double.Epsilon) > 0.0);
    }

    /// <summary>Masa niedodatnia albo nieskończona daje metry bez sensu — też odmowa.</summary>
    [TestMethod]
    public void Skrocenie_drogi_odrzuca_mase_niedodatnia_i_nieskonczona()
    {
        var account = new BrakingEnergyAccount(0.0, 1000.0, 0.0, 0.0, 0.0);

        foreach (var mass in new[] { 0.0, -1.0, double.NaN, double.PositiveInfinity })
        {
            var error = Assert.ThrowsException<ArgumentOutOfRangeException>(
                () => account.ResistanceShorteningM(mass, 2.0),
                $"masa {mass} została przyjęta");
            Assert.AreEqual("effectiveMassKg", error.ParamName);
        }
    }

    /// <summary>Wiersz konta hamowania też idzie do raportu i też nie zależy od maszyny.</summary>
    [TestMethod]
    public void Wiersz_konta_hamowania_nie_zalezy_od_kultury_maszyny()
    {
        WithCulture(CommaCulture(), () =>
        {
            var line = BalancedBraking().ToString();

            Console.WriteLine(line);
            StringAssert.Contains(line, "hamulec = 60.000 J");
            Assert.IsFalse(line.Contains("60,000", StringComparison.Ordinal), $"przecinek dziesiętny: {line}");
        });
    }

    // --- DesignParameter --------------------------------------------------------------

    /// <summary>
    /// Wiersz katalogu założeń wypisuje wszystkie cztery pola: nazwę właściwości,
    /// wartość, ścieżkę w rejestrze i powód. Ten wiersz jest jedynym miejscem, w którym
    /// widać, że liczba jest <c>design_model</c>, a nie pomiarem — gubienie któregokolwiek
    /// pola zamienia audyt w listę liczb bez pochodzenia.
    /// </summary>
    [TestMethod]
    public void Wiersz_zalozenia_projektowego_niesie_nazwe_wartosc_sciezke_i_powod()
    {
        var parameter = new DesignParameter(
            "DesignJerkMps3", "reference_model.jerk_mps3", 0.75, "brak publikowanego zrywu STIB");

        var line = parameter.ToString();
        Console.WriteLine(line);

        StringAssert.Contains(line, "DesignJerkMps3");
        StringAssert.Contains(line, "0.75");
        StringAssert.Contains(line, "reference_model.jerk_mps3");
        StringAssert.Contains(line, "brak publikowanego zrywu STIB");
    }

    /// <summary>
    /// Wartość idzie formatem <c>R</c>, czyli w obie strony bez straty. To nie jest
    /// ozdoba: katalog założeń czyta się po to, żeby porównać liczbę w kodzie z liczbą
    /// w <c>data/vehicle/m7-spec.json</c>, a format skracający do kilku miejsc pokazuje
    /// zgodność tam, gdzie jej nie ma. Test bierze wartość, której nie da się zapisać
    /// skończenie dziesiętnie, i parsuje wypisany tekst z powrotem.
    /// </summary>
    [TestMethod]
    public void Wartosc_zalozenia_wypisuje_sie_bez_straty_precyzji()
    {
        var awkward = 1.0 / 3.0;
        var parameter = new DesignParameter("DesignX", "reference_model.x", awkward, "powód");

        var number = ValueText(parameter.ToString());
        Console.WriteLine($"{awkward:R} -> {number}");

        Assert.AreEqual(
            BitConverter.DoubleToInt64Bits(awkward),
            BitConverter.DoubleToInt64Bits(double.Parse(number, CultureInfo.InvariantCulture)),
            "wartość wypisana i odczytana z powrotem musi być tym samym double");
    }

    /// <summary>
    /// Katalog założeń wypisuje się do raportu, więc kultura maszyny nie może zmienić
    /// ani jednego wiersza. Sprawdzone na prawdziwym katalogu M7, a nie na wpisie
    /// zmyślonym na tę okazję — tam liczby są ułamkowe wszystkie.
    /// </summary>
    [TestMethod]
    public void Caly_katalog_zalozen_M7_wypisuje_sie_w_kulturze_niezmiennej()
    {
        WithCulture(CommaCulture(), () =>
        {
            var lines = VehicleModel.M7.DesignAssumptions.Select(a => a.ToString()).ToList();

            Assert.IsTrue(lines.Count >= 16, $"katalog M7 zmalał do {lines.Count} wpisów");
            Console.WriteLine(lines[0]);

            var values = lines.Select(ValueText).ToList();
            foreach (var value in values)
            {
                Assert.IsFalse(value.Contains(',', StringComparison.Ordinal), $"przecinek dziesiętny w wartości: {value}");
                Assert.IsTrue(
                    double.TryParse(value, NumberStyles.Float, CultureInfo.InvariantCulture, out _),
                    $"wartość nie odczytuje się kulturą niezmienną: {value}");
            }

            Assert.IsTrue(
                values.Any(v => v.Contains('.', StringComparison.Ordinal)),
                "żaden wpis katalogu nie ma wartości ułamkowej — test przestał cokolwiek sprawdzać");
        });
    }
}
