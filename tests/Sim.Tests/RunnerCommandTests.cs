using System;
using System.IO;
using MetroBxl.Sim.Runner;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace MetroBxl.Sim.Tests;

/// <summary>
/// Kod wyjścia ośmiu poleceń <c>Sim.Runner</c> (<see cref="Program.Main"/>) — pozycja
/// 6.A9, bliźniak 6.A8 po stronie CLI. Zmierzone 06.09.2026: nazwę polecenia wymieniał
/// dotąd tylko jeden plik testowy — i to przypadkiem, w komentarzu
/// <c>CabProtectionTests.cs</c> niezwiązanym z rozbiorem argumentów. Rozbiór i kod
/// wyjścia siedmiu pozostałych poleceń (<c>drive</c>, <c>replay</c>, <c>compare</c>,
/// <c>parity</c>, <c>braking</c>, <c>line</c>, <c>budget</c>) nie miały ani jednego
/// testu: literówka w nazwie przełącznika albo odwrócony warunek przeszłyby cały
/// zestaw, bo istniejące testy wołają metody rdzenia bezpośrednio, z pominięciem
/// <c>Program.Main</c>.
///
/// <para><b>Czego te testy NIE robią.</b> Nie sprawdzają treści telemetrii ani liczb
/// o sieci — to robią <c>LineRunTests</c>, <c>LineBudgetTests</c>, <c>TrackAxisTests</c>
/// i <c>ClassicSignallingScenarioTests</c>, wołając rdzeń bezpośrednio. Tu wchodzi się
/// WYŁĄCZNIE przez <see cref="Program.Main"/> — tą samą drogą, którą idzie CI
/// i człowiek z terminala — i patrzy wyłącznie na kod wyjścia oraz na to, czy komunikat
/// wygląda jak odmowa, a nie na zawartość przejazdu.</para>
///
/// <para><b>Poza zakresem, świadomie (docs/TASKS.md, 6.A9).</b> Zmiana zachowania
/// <c>Program.cs</c> — w tym „poprawienie" kodu wyjścia czy komunikatu. Testy przybijają
/// stan, jaki jest DZIŚ; <c>compare</c> zwraca 2 przy złej liczbie argumentów, a reszta
/// odmów (<c>replay</c>, <c>axis</c>, <c>line</c>, <c>budget</c>) zwraca 1 przez wspólny
/// handler wyjątków — dwie różne liczby dla tej samej kategorii błędu. To jest
/// ZGŁOSZENIE, przybite testami niżej, nie poprawka przy okazji.</para>
/// </summary>
[TestClass]
public sealed class RunnerCommandTests
{
    // --- pomocnicze -------------------------------------------------------------

    /// <summary>
    /// Wołanie <see cref="Program.Main"/> z przechwyceniem obu strumieni — dokładnie
    /// tak, jak widziałby je proces wywołujący <c>dotnet MetroBxl.Sim.Runner.dll</c>.
    /// Strumienie wracają na miejsce w <c>finally</c>, żeby awaria jednego testu nie
    /// zabrała stdout/stderr reszcie zestawu.
    /// </summary>
    private static (int ExitCode, string StdOut, string StdErr) Run(params string[] args)
    {
        var originalOut = Console.Out;
        var originalError = Console.Error;
        using var outWriter = new StringWriter();
        using var errWriter = new StringWriter();
        Console.SetOut(outWriter);
        Console.SetError(errWriter);
        try
        {
            var exitCode = Program.Main(args);
            return (exitCode, outWriter.ToString(), errWriter.ToString());
        }
        finally
        {
            Console.SetOut(originalOut);
            Console.SetError(originalError);
        }
    }

    // --- polecenia bez wymaganych argumentów: kod wyjścia przy poprawnym wywołaniu --

    /// <summary>
    /// <c>drive</c> nie ma ani jednego wymaganego argumentu — scenariusz startowy jest
    /// wpisany w kod (<see cref="Program.NewDrive"/>). Test na kod wyjścia jest tu więc
    /// testem POPRAWNEGO wywołania: 0, a nie odmowy.
    /// </summary>
    [TestMethod]
    public void Drive_bez_argumentow_konczy_sie_kodem_zero()
    {
        var result = Run("drive");

        Assert.AreEqual(0, result.ExitCode);
        StringAssert.Contains(result.StdErr, "[RDZEŃ]");
    }

    /// <summary>
    /// <c>parity</c> nie bierze żadnego argumentu z linii poleceń — porównuje kontroler
    /// z <c>AccelerationRun</c> na stałym, wbudowanym scenariuszu. Zgodność bitową
    /// przybijają już <c>ReferenceParityTests</c>; tu chodzi wyłącznie o to, że
    /// wywołanie z linii poleceń kończy się kodem 0.
    /// </summary>
    [TestMethod]
    public void Parity_bez_argumentow_konczy_sie_kodem_zero()
    {
        var result = Run("parity");

        Assert.AreEqual(0, result.ExitCode);
        StringAssert.Contains(result.StdOut, "[PARYTET]");
    }

    /// <summary>
    /// <c>braking</c> nie bierze żadnego argumentu i zawsze kończy się kodem 0 — to jest
    /// wydruk tablic referencyjnych T-311, nie test niczego. Wart osobnego testu
    /// wyłącznie dlatego, że to jedno z ośmiu poleceń bez ani jednego testu kodu
    /// wyjścia (stąd zadanie 6.A9).
    /// </summary>
    [TestMethod]
    public void Braking_bez_argumentow_konczy_sie_kodem_zero()
    {
        var result = Run("braking");

        Assert.AreEqual(0, result.ExitCode);
        StringAssert.Contains(result.StdOut, "DROGA HAMOWANIA");
    }

    // --- polecenia z wymaganymi argumentami: kod wyjścia przy ich braku ----------

    /// <summary>
    /// <c>replay</c> wymaga <c>--keys</c> PRZED odczytem jakiegokolwiek pliku — bez
    /// niego rzuca <see cref="ArgumentException"/>, którą łapie wspólny handler
    /// w <see cref="Program.Main"/> i zwraca 1. Test nie podaje żadnego pliku:
    /// literówka w rozbiorze <c>--keys</c> ujawniłaby się tu przed literówką gdziekolwiek
    /// dalej w tym poleceniu.
    /// </summary>
    [TestMethod]
    public void Replay_bez_wymaganego_argumentu_konczy_sie_kodem_jeden()
    {
        var result = Run("replay");

        Assert.AreEqual(1, result.ExitCode);
        StringAssert.Contains(result.StdErr, "--keys");
    }

    /// <summary>
    /// <c>compare</c> było jedynym z dziewięciu poleceń, które sprawdzało liczbę
    /// argumentów RĘCZNIE (<c>args.Length &lt; 3</c>) i wracało z kodem 2 — zamiast
    /// rzucić wyjątek złapany wspólnym handlerem (kod 1), jak reszta odmów.
    ///
    /// <para><b>Test przepisany, a nie dopisany obok, i to jest cała treść 6.A16.</b>
    /// Poprzednia wersja przybijała kod <b>2</b> i mówiła wprost, że niespójność jest
    /// warta zgłoszenia, ale nie poprawki — bo wybór między 1 a 2 nie należał do
    /// pozycji, która ma opisać zastane zachowanie. Cztery pozycje (6.A10, 6.A11,
    /// 6.A13, 6.D20) zatrzymały się na tej granicy. Właściciel wybrał 06.09.2026:
    /// każda odmowa argumentowa kończy się kodem <b>1</b>, a <b>2</b> zostaje wyłącznie
    /// dla „nie wiem, co uruchomić".</para>
    /// </summary>
    [TestMethod]
    public void Compare_bez_dwoch_plikow_konczy_sie_kodem_jeden()
    {
        var result = Run("compare");

        Assert.AreEqual(1, result.ExitCode);
        StringAssert.Contains(result.StdErr, "dwóch plików");
        StringAssert.Contains(result.StdErr, "BŁĄD:");
    }

    /// <summary>
    /// <c>axis</c> wymaga <c>--axis</c>; brak rzuca <see cref="ArgumentException"/> —
    /// ten sam handler i ten sam kod 1, co <c>replay</c>, <c>line</c> i <c>budget</c>.
    /// </summary>
    [TestMethod]
    public void Axis_bez_wymaganego_argumentu_konczy_sie_kodem_jeden()
    {
        var result = Run("axis");

        Assert.AreEqual(1, result.ExitCode);
        StringAssert.Contains(result.StdErr, "--axis");
    }

    /// <summary>
    /// <c>line</c> ma trzy argumenty obowiązkowe bez wartości domyślnej (<c>--axis</c>,
    /// <c>--limit-kmh</c>, <c>--exchange-s</c>) — patrz komentarz przy
    /// <see cref="Program"/> o czterech obowiązkowych liczbach wejściowych. Bez żadnego
    /// z nich pierwszy w kolejności rozbioru jest <c>--axis</c>.
    /// </summary>
    [TestMethod]
    public void Line_bez_wymaganego_argumentu_konczy_sie_kodem_jeden()
    {
        var result = Run("line");

        Assert.AreEqual(1, result.ExitCode);
        StringAssert.Contains(result.StdErr, "line wymaga --axis");
    }

    /// <summary>
    /// <c>budget</c> ma siedem argumentów obowiązkowych (<c>--axis</c>,
    /// <c>--signalling</c>, <c>--limit-kmh</c>, <c>--exchange-s</c>, <c>--headway-s</c>,
    /// <c>--trains</c>, <c>--steps</c>) — więcej niż jakiekolwiek inne polecenie. Bez
    /// żadnego z nich pierwszy w kolejności rozbioru jest <c>--axis</c>, tak jak
    /// w <c>line</c>.
    /// </summary>
    [TestMethod]
    public void Budget_bez_wymaganego_argumentu_konczy_sie_kodem_jeden()
    {
        var result = Run("budget");

        Assert.AreEqual(1, result.ExitCode);
        StringAssert.Contains(result.StdErr, "budget wymaga --axis");
    }

    // --- service-day: dziewiąte polecenie, dopisane w 6.A10 ----------------------

    /// <summary>
    /// Minimalny, poprawny rozkład na potrzeby testów <c>service-day</c> — jeden obieg,
    /// jeden kurs. Zapisywany do pliku tymczasowego, bo <c>--timetable</c> czyta
    /// z dysku (<see cref="File.ReadAllText"/>), nie z argumentu wprost.
    /// </summary>
    private static string NapiszTymczasowyRozklad()
    {
        var path = Path.GetTempFileName();
        File.WriteAllText(path,
            "{\"date\":\"20260906\",\"duties\":{\"rows\":["
            + "{\"block_id\":\"A\",\"trips\":1,\"trip_windows\":[[100,200]]}"
            + "]}}");
        return path;
    }

    /// <summary>
    /// <c>service-day</c> wymaga <c>--timetable</c> PRZED odczytem czegokolwiek innego
    /// (patrz komentarz przy <see cref="Program.ServiceDayCommand"/>: „bez pliku nie ma
    /// czego odtwarzać") — rzuca <see cref="ArgumentException"/>, którą łapie wspólny
    /// handler w <see cref="Program.Main"/> i zwraca 1, tak samo jak <c>replay</c>,
    /// <c>axis</c>, <c>line</c> i <c>budget</c>.
    /// </summary>
    [TestMethod]
    public void ServiceDay_bez_wymaganego_argumentu_konczy_sie_kodem_jeden()
    {
        var result = Run("service-day");

        Assert.AreEqual(1, result.ExitCode);
        StringAssert.Contains(result.StdErr, "--timetable");
    }

    /// <summary>
    /// <c>--at</c> w niepoprawnym formacie (nie <c>HH:MM:SS</c>) trafia w
    /// <see cref="Program.ParseClock"/>, która rzuca <see cref="ArgumentException"/> —
    /// złapaną tym samym wspólnym handlerem, kod 1. Test podaje POPRAWNY
    /// <c>--timetable</c>, żeby błąd, który testujemy, był naprawdę w rozbiorze
    /// <c>--at</c>, a nie w braku pliku sprzed niego.
    /// </summary>
    [TestMethod]
    public void ServiceDay_z_niepoprawnym_formatem_at_konczy_sie_kodem_jeden()
    {
        var timetable = NapiszTymczasowyRozklad();
        try
        {
            var result = Run("service-day", "--timetable", timetable, "--at", "nie-jest-zegarem");

            Assert.AreEqual(1, result.ExitCode);
            StringAssert.Contains(result.StdErr, "HH:MM:SS");
        }
        finally
        {
            File.Delete(timetable);
        }
    }

    // --- nazwa polecenia, którego nie ma -----------------------------------------

    /// <summary>
    /// Nazwa spoza ósemki (<c>drive</c>, <c>replay</c>, <c>compare</c>, <c>axis</c>,
    /// <c>parity</c>, <c>braking</c>, <c>line</c>, <c>budget</c>) trafia w
    /// <see cref="Program.Unknown"/> — kod 2, tą samą liczbą co brak argumentów
    /// w ogóle (<see cref="Brak_argumentow_w_ogole_konczy_sie_kodem_dwa"/>), ale przez
    /// ODDZIELNĄ ścieżkę kodu: gałąź <c>_ =&gt; Unknown(args[0])</c> wewnątrz
    /// <c>switch</c> w <c>try</c>, a nie sprawdzenie <c>args.Length == 0</c> przed nim.
    /// </summary>
    [TestMethod]
    public void Nieznane_polecenie_konczy_sie_kodem_dwa()
    {
        var result = Run("nie-ma-takiego-polecenia");

        Assert.AreEqual(2, result.ExitCode);
        StringAssert.Contains(result.StdErr, "nieznane polecenie: nie-ma-takiego-polecenia");
    }

    /// <summary>
    /// Wywołanie bez ŻADNEGO argumentu to inna ścieżka kodu niż nieznana nazwa —
    /// sprawdzana PRZED wejściem w <c>try</c>/<c>switch</c>, na samym początku
    /// <c>Program.Main</c>. Ten sam kod wyjścia (2), inny powód; test dodatkowy, poza
    /// minimalnym wymogiem zadania 6.A9 (ono mówi o NAZWIE polecenia, którego nie ma —
    /// nie o jej braku), ale ta sama rodzina odmowy i ta sama metoda pomocnicza, więc
    /// tani do dodania obok.
    /// </summary>
    [TestMethod]
    public void Brak_argumentow_w_ogole_konczy_sie_kodem_dwa()
    {
        var result = Run();

        Assert.AreEqual(2, result.ExitCode);
    }

    // --- nieznana opcja (6.A11) --------------------------------------------------

    /// <summary>
    /// Sedno pozycji 6.A11. Przed nią nieznana opcja polecenia <c>line</c> kończyła się
    /// <b>kodem 0</b>: była przemilczana, a jej wartość — nawet nieliczbowa — nigdy
    /// nie czytana. Zmierzone przy 6.D15 (#301): dwa przejazdy, z taką opcją i bez niej,
    /// dały pliki identyczne co do bajtu, więc weryfikacja oparta na takiej komendzie
    /// spełniała się przez NIEZROBIENIE zadania.
    ///
    /// <para><b>Opcja w tym teście jest przepisana, a nie dopisana obok.</b> Do 6.A6
    /// stało tu <c>--coast-from-m X</c> — dokładnie ta nazwa, na której 6.D15 złapało
    /// milczenie. 6.A6 dopisała <c>--coast-from-m</c> do polecenia <c>line</c>, więc
    /// nazwa przestała być nieznana: test padał teraz na rozbiorze <c>X</c> jako liczby,
    /// czyli sprawdzałby coś innego, niż mówi jego nazwa. Rolę przejmuje
    /// <c>--headway-s</c> — opcja, która NAPRAWDĘ istnieje, tyle że w <c>budget</c>,
    /// a nie w <c>line</c>. Jest to mocniejsza kontrola niż wymyślona nazwa: literówka
    /// w wierszu poleceń rzadko jest ciągiem znaków, którego nikt nigdy nie napisał,
    /// a znacznie częściej opcją wziętą z innego polecenia.</para>
    /// </summary>
    [TestMethod]
    public void Line_z_nieznana_opcja_konczy_sie_kodem_jeden()
    {
        var result = Run(
            "line", "--axis", "data/track/L1_A.json", "--limit-kmh", "72",
            "--exchange-s", "20", "--headway-s", "X", "--trace", "build/x.csv");

        Assert.AreEqual(1, result.ExitCode);
        StringAssert.Contains(result.StdErr, "--headway-s");
        StringAssert.Contains(result.StdErr, "nie zna opcji");
    }

    /// <summary>
    /// Druga strona tej samej pary: <c>--coast-from-m</c> jest od 6.A6 opcją ZNANĄ
    /// poleceniu <c>line</c>, więc odmowa ma o niej milczeć, a przejazd ma się odbyć.
    /// Bez tego testu dopisanie opcji do samej tabeli <c>KnownOptions</c>, bez wpięcia
    /// jej w kod, wyglądałoby tu tak samo jak zrobione zadanie.
    /// </summary>
    [TestMethod]
    public void Line_zna_wybieg_i_nie_odmawia_go()
    {
        var result = Run(
            "line", "--axis", Path.Combine(RepoRoot(), "data", "track", "L1_A.json"),
            "--limit-kmh", "72", "--exchange-s", "20", "--coast-from-m", "250");

        Assert.AreEqual(0, result.ExitCode, result.StdErr);
        Assert.IsFalse(
            result.StdErr.Contains("nie zna opcji", StringComparison.Ordinal), result.StdErr);
        StringAssert.Contains(result.StdOut, "CoastFromM = 250");
        StringAssert.Contains(result.StdOut, "[ODCINEK]");
    }

    /// <summary>
    /// Odmowa ma być per polecenie, a nie wspólną listą wszystkich opcji runnera:
    /// <c>--trains</c> istnieje w <c>budget</c> i nie istnieje w <c>service-day</c>.
    /// Test pilnuje, że komunikat wymienia opcje TEGO polecenia — bez tego lista
    /// znanych nazw byłaby sumą i odmowa przestałaby cokolwiek znaczyć.
    /// </summary>
    [TestMethod]
    public void Odmowa_wymienia_opcje_tego_polecenia_a_nie_wszystkich()
    {
        var result = Run("service-day", "--timetable", "build/nie-ma.json", "--trains", "8");

        Assert.AreEqual(1, result.ExitCode);
        StringAssert.Contains(result.StdErr, "--trains");
        StringAssert.Contains(result.StdErr, "--at");
        Assert.IsFalse(
            result.StdErr.Contains("--headway-s", StringComparison.Ordinal),
            "komunikat wymienia opcje innego polecenia: " + result.StdErr);
    }

    /// <summary>
    /// Kontrola drugiego kierunku: argument POZYCYJNY nie zaczyna się od <c>--</c>
    /// i ma przejść nietknięty. <c>compare</c> bierze dwie ścieżki pozycyjnie, więc
    /// odmowa zbudowana na „wszystko, czego nie znam" wywróciłaby to polecenie
    /// w całości. Kod 1 pochodzi tu z czytania pliku, nie z rozbioru argumentów —
    /// i to jest cała treść tego testu.
    /// </summary>
    [TestMethod]
    public void Argument_pozycyjny_nie_jest_brany_za_nieznana_opcje()
    {
        var result = Run("compare", "build/nie-ma-a.csv", "build/nie-ma-b.csv", "--tolerance", "0");

        Assert.IsFalse(
            result.StdErr.Contains("nie zna opcji", StringComparison.Ordinal),
            "argument pozycyjny wzięty za opcję: " + result.StdErr);
    }

    /// <summary>
    /// Flaga bez wartości (<c>--atp</c>) nie może zjadać następnego członu. Gdyby
    /// pomijanie wartości objęło także flagi, <c>--atp --axis …</c> zjadłoby
    /// <c>--axis</c> i polecenie odmówiłoby z powodu BRAKU osi zamiast z powodu
    /// nieczytelnego pliku. Test nie ogląda kodu wyjścia (oba warianty dają 1) tylko
    /// POWÓD odmowy — bo to on odróżnia zjedzony człon od przeczytanego. Ścieżka
    /// celowo wskazuje plik, którego nie ma: test ma nie zależeć od katalogu
    /// roboczego, w którym uruchomiono zestaw.
    /// </summary>
    [TestMethod]
    public void Flaga_bez_wartosci_nie_zjada_nastepnego_czlonu()
    {
        var result = Run(
            "budget", "--atp", "--axis", "data/track/nie-ma-takiej-osi.json",
            "--signalling", "data/design/signalling/classic-2026.json",
            "--limit-kmh", "72", "--exchange-s", "20", "--headway-s", "120",
            "--steps", "200", "--trains", "1");

        Assert.IsFalse(
            result.StdErr.Contains("budget wymaga --axis", StringComparison.Ordinal),
            "flaga --atp zjadła następny człon: " + result.StdErr);
        Assert.IsFalse(
            result.StdErr.Contains("nie zna opcji", StringComparison.Ordinal),
            "flaga --atp została odrzucona: " + result.StdErr);
    }

    // --- plik, ktory planem nie jest (6.A13) --------------------------------------

    /// <summary>Katalog repozytorium — po pliku <c>CLAUDE.md</c>, tak jak w innych testach.</summary>
    private static string RepoRoot()
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

        throw new FileNotFoundException("nie znalazłem katalogu repozytorium (brak CLAUDE.md w górę drzewa)");
    }

    /// <summary>
    /// Sedno pozycji 6.A13. Plik <c>cbtc-test-2026.json</c> LEŻY w <c>data/</c> i nie jest
    /// atrapą — to on wywrócił proces: <c>JsonElement.GetProperty</c> rzucało
    /// <c>KeyNotFoundException</c>, którego wspólny handler nie łapie, więc proces kończył
    /// się kodem <b>134</b> i stosem wywołań. Test używa prawdziwego pliku właśnie dlatego;
    /// atrapa dowodziłaby czegoś innego niż to, co się zdarzyło.
    /// </summary>
    [TestMethod]
    public void Plik_ktory_nie_jest_planem_konczy_sie_odmowa_a_nie_sygnalem()
    {
        var plan = Path.Combine(RepoRoot(), "data", "design", "signalling", "cbtc-test-2026.json");
        Assert.IsTrue(File.Exists(plan), "plik z data/ zniknął — test straciłby swój przedmiot: " + plan);

        var result = Run(
            "budget", "--axis", Path.Combine(RepoRoot(), "data", "track", "L1_A.json"),
            "--signalling", plan,
            "--limit-kmh", "72", "--exchange-s", "20", "--headway-s", "10",
            "--steps", "2000", "--trains", "2");

        Assert.AreEqual(1, result.ExitCode);
        StringAssert.Contains(result.StdErr, "protection_variant");
        StringAssert.Contains(result.StdErr, "nie wyglada na plan sygnalizacji");
    }

    /// <summary>
    /// Kontrola drugiego kierunku: plan, który planem JEST, ma nadal przechodzić.
    /// Odmowa zbudowana zbyt szeroko odrzuciłaby oba pliki i test wyżej nadal byłby
    /// zielony — dlatego ten stoi obok niego, a nie zamiast niego.
    /// </summary>
    [TestMethod]
    public void Prawdziwy_plan_nadal_przechodzi()
    {
        var result = Run(
            "budget", "--axis", Path.Combine(RepoRoot(), "data", "track", "L1_A.json"),
            "--signalling", Path.Combine(RepoRoot(), "data", "design", "signalling", "classic-2026.json"),
            "--limit-kmh", "72", "--exchange-s", "20", "--headway-s", "10",
            "--steps", "2000", "--trains", "2");

        Assert.AreEqual(0, result.ExitCode, result.StdErr);
        StringAssert.Contains(result.StdOut, "[BUDŻET]");
    }

    // --- komunikat odmowy nazywa wolane polecenie (6.D20) -------------------------

    /// <summary>
    /// Sedno pozycji 6.D20. <c>RequiredNumber</c> jest wspolny dla <c>line</c>,
    /// <c>budget</c> i <c>replay</c>, a nazwe polecenia mial zaszyta jako
    /// <c>line</c> — wiec <c>budget</c> bez <c>--limit-kmh</c> odsylal czytajacego
    /// do polecenia, ktorego nie uruchamial.
    /// </summary>
    [TestMethod]
    public void Budget_bez_limitu_nazywa_budget_a_nie_line()
    {
        var result = Run(
            "budget", "--axis", "data/track/L1_A.json",
            "--signalling", "data/design/signalling/classic-2026.json",
            "--headway-s", "120", "--steps", "1000", "--trains", "1");

        Assert.AreEqual(1, result.ExitCode);
        StringAssert.Contains(result.StdErr, "budget wymaga --limit-kmh");
        Assert.IsFalse(
            result.StdErr.Contains("line wymaga", StringComparison.Ordinal),
            "komunikat nadal nazywa line: " + result.StdErr);
    }

    /// <summary>
    /// Drugie polecenie, bo poprawka biorąca nazwę z <c>args[0]</c> musi dawać
    /// poprawny wynik takze tam, gdzie stara stala byla przypadkiem trafna —
    /// inaczej test na samym <c>budget</c> przeszedlby rowniez dla poprawki,
    /// ktora zaszywa nowa, tak samo sztywna nazwe.
    /// </summary>
    [TestMethod]
    public void Line_bez_limitu_nadal_nazywa_line()
    {
        var result = Run(
            "line", "--axis", "data/track/L1_A.json", "--exchange-s", "20",
            "--trace", "build/x.csv");

        Assert.AreEqual(1, result.ExitCode);
        StringAssert.Contains(result.StdErr, "line wymaga --limit-kmh");
    }
}
