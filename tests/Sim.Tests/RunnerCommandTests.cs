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

    // --- jeden minus też się liczy (6.A15) ---------------------------------------

    /// <summary>
    /// 6.A15. 6.A11 dopisała odmowę nieznanej opcji i <b>sama wypisała tę dziurę</b>:
    /// sprawdzane były wyłącznie człony z DWOMA minusami, więc <c>-zmyslona 7</c>
    /// kończyło się <b>kodem 0</b>, dokładnie tak jak przed tamtą odmową.
    ///
    /// <para>Rozszerzenie było bezpieczne i to jest ZMIERZONE, nie założone
    /// (<c>reports/jeden-minus.md</c>): w całym repozytorium nie ma ani jednej komendy
    /// podającej runnerowi człon z jednym minusem — <c>-c Release</c> stoi PRZED
    /// separatorem <c>--</c>, więc jest flagą <c>dotnet run</c> i nigdy nie dochodzi
    /// do <c>args</c>. Nie ma też ani jednej wartości ujemnej, a jedyne argumenty
    /// pozycyjne to dwie ŚCIEŻKI polecenia <c>compare</c>.</para>
    /// </summary>
    [TestMethod]
    public void Line_z_jednym_minusem_konczy_sie_kodem_jeden()
    {
        var result = Run(
            "line", "--axis", Path.Combine(RepoRoot(), "data", "track", "L1_A.json"),
            "--limit-kmh", "72", "--exchange-s", "20", "-zmyslona", "7");

        Assert.AreEqual(1, result.ExitCode, result.StdOut + result.StdErr);
        StringAssert.Contains(result.StdErr, "-zmyslona");
        StringAssert.Contains(result.StdErr, "nie zna opcji");
    }

    /// <summary>
    /// Druga strona pary, bez której pierwsza mówi tylko „coś odmawia": wartość
    /// UJEMNA znanej opcji nadal przechodzi przez odmowę, bo człon po opcji
    /// z wartością jest pomijany razem z nią.
    ///
    /// <para>Odmowa, która zjadłaby <c>-5</c>, meldowałaby „nie znam opcji -5" i to
    /// byłby najgorszy możliwy wynik tej pozycji: zamiana jednej cichej dziury na
    /// komunikat mówiący nieprawdę. Test żąda więc, żeby <c>-5</c> doszło do
    /// walidacji dziedzinowej i zostało odrzucone Z JEJ powodu — bo okno stacji
    /// musi być dodatnie, a nie bo runner nie zna opcji.</para>
    /// </summary>
    [TestMethod]
    public void Wartosc_ujemna_znanej_opcji_nie_jest_brana_za_opcje()
    {
        var result = Run(
            "line", "--axis", Path.Combine(RepoRoot(), "data", "track", "L1_A.json"),
            "--limit-kmh", "72", "--exchange-s", "20", "--stop-window-m", "-5");

        Assert.AreEqual(1, result.ExitCode, result.StdOut + result.StdErr);
        Assert.IsFalse(
            result.StdErr.Contains("nie zna opcji", StringComparison.Ordinal),
            "wartość ujemna wzięta za nieznaną opcję: " + result.StdErr);
        StringAssert.Contains(result.StdErr, "Okno stacji");
    }

    /// <summary>
    /// Goły minus nie jest literówką — to konwencja standardowego wejścia. To
    /// repozytorium jej nie używa, ale odmawianie jej byłoby odmową czegoś, co nie
    /// jest pomyłką, a odmowa ma łapać pomyłki.
    /// </summary>
    [TestMethod]
    public void Goly_minus_nie_jest_zglaszany_jako_nieznana_opcja()
    {
        var result = Run(
            "line", "--axis", Path.Combine(RepoRoot(), "data", "track", "L1_A.json"),
            "--limit-kmh", "72", "--exchange-s", "20", "-");

        Assert.IsFalse(
            result.StdErr.Contains("nie zna opcji", StringComparison.Ordinal),
            "goły minus zgłoszony jako nieznana opcja: " + result.StdErr);
    }

    // --- nastawy w pliku, nie tylko w wypisie (6.A20) ----------------------------

    /// <summary>
    /// 6.A20. Nagłówek <c>[BUDŻET]</c> mówi od 6.A18, jaki przejazd zmierzono — ale
    /// wypis ginie razem z konsolą, a plik z <c>--out</c> PRZEŻYWA proces i to on
    /// trafia do raportów. Zmierzone przed tą zmianą: dwa przebiegi różniące się
    /// <c>--coast-from-m</c> dawały pliki dwuwierszowe, w których różnił się
    /// <b>wyłącznie wiersz pomiaru</b> — a mediana kroków wyszła w nich odwrotnie
    /// (88 935 vs 77 237 kroków/s), więc czytający wyciągnąłby wniosek przeciwny do
    /// prawdziwego i nie miał czym tego sprawdzić.
    /// </summary>
    [TestMethod]
    public void Budget_zapisuje_nastawy_do_pliku_a_nie_tylko_na_konsole()
    {
        var output = Path.Combine(Path.GetTempPath(), Path.GetRandomFileName() + ".csv");
        try
        {
            var result = Run(
                "budget", "--axis", Path.Combine(RepoRoot(), "data", "track", "L1_A.json"),
                "--signalling", Path.Combine(
                    RepoRoot(), "data", "design", "signalling", "classic-2026.json"),
                "--limit-kmh", "72", "--exchange-s", "20", "--headway-s", "90",
                "--steps", "200", "--repeats", "1", "--warmup", "0", "--trains", "1",
                "--coast-from-m", "250", "--out", output);

            Assert.AreEqual(0, result.ExitCode, result.StdErr);
            var lines = File.ReadAllLines(output);
            CollectionAssert.Contains(lines, "# coast: wybieg 250.0 m odcinka");
            foreach (var nastawa in new[] { "# axis:", "# signalling_plan:", "# limit_kmh:",
                                            "# exchange_s:", "# headway_s:", "# turnback_s:",
                                            "# load:", "# atp:", "# steps:", "# repeats:" })
            {
                Assert.IsTrue(Array.Exists(lines, l => l.StartsWith(nastawa, StringComparison.Ordinal)),
                    nastawa + " nie ma w pliku: " + string.Join(" | ", lines));
            }
        }
        finally
        {
            File.Delete(output);
        }
    }

    /// <summary>
    /// Druga strona tej samej pary — a bez niej pierwsza nie dowodzi tego, co trzeba.
    /// Kryterium 6.A20 nie brzmi „w pliku stoją nastawy", tylko „z DWÓCH plików da się
    /// odczytać, którą nastawą się różnią". Test bierze więc dwa przebiegi różniące się
    /// jedną nastawą i sprawdza, że różnica jest widoczna w wierszach <c>#</c>, a nie
    /// tylko w liczbach pomiaru.
    /// </summary>
    [TestMethod]
    public void Dwa_przebiegi_roznia_sie_widocznie_nastawa_a_nie_tylko_liczbami()
    {
        var zWybiegiem = Path.Combine(Path.GetTempPath(), Path.GetRandomFileName() + ".csv");
        var bezWybiegu = Path.Combine(Path.GetTempPath(), Path.GetRandomFileName() + ".csv");
        try
        {
            string[] wspolne =
            {
                "budget", "--axis", Path.Combine(RepoRoot(), "data", "track", "L1_A.json"),
                "--signalling", Path.Combine(
                    RepoRoot(), "data", "design", "signalling", "classic-2026.json"),
                "--limit-kmh", "72", "--exchange-s", "20", "--headway-s", "90",
                "--steps", "200", "--repeats", "1", "--warmup", "0", "--trains", "1",
            };
            var a = Run([.. wspolne, "--coast-from-m", "250", "--out", zWybiegiem]);
            var b = Run([.. wspolne, "--out", bezWybiegu]);
            Assert.AreEqual(0, a.ExitCode, a.StdErr);
            Assert.AreEqual(0, b.ExitCode, b.StdErr);

            var opisA = Array.FindAll(File.ReadAllLines(zWybiegiem), l => l.StartsWith("#", StringComparison.Ordinal));
            var opisB = Array.FindAll(File.ReadAllLines(bezWybiegu), l => l.StartsWith("#", StringComparison.Ordinal));
            Assert.AreEqual(opisA.Length, opisB.Length, "bloki nastaw mają różną długość");
            var rozne = Array.Empty<string>();
            for (var i = 0; i < opisA.Length; i++)
            {
                if (!string.Equals(opisA[i], opisB[i], StringComparison.Ordinal))
                {
                    Array.Resize(ref rozne, rozne.Length + 1);
                    rozne[^1] = opisA[i] + " != " + opisB[i];
                }
            }

            Assert.AreEqual(1, rozne.Length,
                "różnić się ma DOKŁADNIE jedna nastawa, a różni się: " + string.Join(" ; ", rozne));
            StringAssert.Contains(rozne[0], "coast");
        }
        finally
        {
            File.Delete(zWybiegiem);
            File.Delete(bezWybiegu);
        }
    }

    /// <summary>
    /// Blok nastaw ma stać PRZED nagłówkiem CSV i być poprzedzony <c>#</c>, bo inaczej
    /// przestaje być metadanymi i staje się uszkodzonym CSV-em. <c>#</c> pomija
    /// <c>pandas.read_csv(comment="#")</c> i jeden filtr w <c>csv</c>.
    /// </summary>
    [TestMethod]
    public void ServiceDay_zapisuje_nastawy_jako_komentarz_przed_naglowkiem()
    {
        var timetable = NapiszTymczasowyRozklad();
        var output = Path.Combine(Path.GetTempPath(), Path.GetRandomFileName() + ".csv");
        try
        {
            var result = Run("service-day", "--timetable", timetable, "--out", output);

            Assert.AreEqual(0, result.ExitCode, result.StdErr);
            var lines = File.ReadAllLines(output);
            Assert.IsTrue(lines[0].StartsWith("# polecenie: service-day", StringComparison.Ordinal), lines[0]);
            var naglowek = Array.FindIndex(lines, l => !l.StartsWith("#", StringComparison.Ordinal));
            Assert.IsTrue(naglowek > 0, "nie ma ani jednego wiersza nastaw przed nagłówkiem");
            Assert.AreEqual("block_id,first_departure_s,last_arrival_s,span_s,trips", lines[naglowek]);
            Assert.IsTrue(Array.Exists(lines, l => l.StartsWith("# timetable:", StringComparison.Ordinal)),
                string.Join(" | ", lines));
        }
        finally
        {
            File.Delete(output);
            File.Delete(timetable);
        }
    }

    // --- wybieg poza poleceniem `line` (6.A18) -----------------------------------

    /// <summary>
    /// 6.A18. <c>budget</c> i <c>line</c> budują ten sam <c>LineRunSettings</c>, ale do
    /// tej pozycji tylko <c>line</c> umiał podać wybieg — więc pomiar kosztu kroku
    /// przy wybiegu (bramka 6.D2) był NIEWYKONALNY, a nie „pominięty".
    ///
    /// <para>Test sprawdza <b>dwie</b> rzeczy, bo pierwsza bez drugiej niczego nie
    /// dowodzi: że odmowa milczy (nastawa jest w tabeli) ORAZ że nagłówek
    /// <c>[BUDŻET]</c> wypisuje ją z powrotem (nastawa doszła do <c>LineRunSettings</c>).
    /// Sama zielona odmowa przeszłaby przy dopisaniu nazwy do samej tabeli, bez
    /// jednej linijki działającego kodu — czyli dokładnie przy zadaniu niezrobionym.</para>
    /// </summary>
    [TestMethod]
    public void Budget_zna_wybieg_i_wypisuje_go_w_naglowku()
    {
        var result = Run(
            "budget", "--axis", Path.Combine(RepoRoot(), "data", "track", "L1_A.json"),
            "--signalling", Path.Combine(
                RepoRoot(), "data", "design", "signalling", "classic-2026.json"),
            "--limit-kmh", "72", "--exchange-s", "20", "--headway-s", "90",
            "--steps", "200", "--repeats", "1", "--warmup", "0", "--trains", "1",
            "--coast-from-m", "250");

        Assert.AreEqual(0, result.ExitCode, result.StdErr);
        Assert.IsFalse(
            result.StdErr.Contains("nie zna opcji", StringComparison.Ordinal), result.StdErr);
        StringAssert.Contains(result.StdOut, "wybieg 250.0 m odcinka");
    }

    /// <summary>
    /// Druga strona tej samej pary. Bez wybiegu nagłówek ma powiedzieć „wyłączony",
    /// a nie milczeć: pomiar bez tej nastawy i pomiar z nią różnią się przejazdem,
    /// więc wypis, który o niej nie wspomina, pozwala porównać dwa różne przejazdy
    /// jako jeden. To jest ta sama usterka, którą wiersz <c>[LIMIT]</c> naprawił
    /// w <c>replay</c> przy #246 — tam też liczba istniała i nie była wypisywana.
    /// </summary>
    [TestMethod]
    public void Budget_bez_wybiegu_melduje_ze_jest_wylaczony()
    {
        var result = Run(
            "budget", "--axis", Path.Combine(RepoRoot(), "data", "track", "L1_A.json"),
            "--signalling", Path.Combine(
                RepoRoot(), "data", "design", "signalling", "classic-2026.json"),
            "--limit-kmh", "72", "--exchange-s", "20", "--headway-s", "90",
            "--steps", "200", "--repeats", "1", "--warmup", "0", "--trains", "1");

        Assert.AreEqual(0, result.ExitCode, result.StdErr);
        StringAssert.Contains(result.StdOut, "wybieg wyłączony");
    }

    /// <summary>
    /// <c>replay</c> wybiegu NIE dostaje, i to jest wynik pomiaru, nie przeoczenie.
    /// Pozycja 6.A18 mówiła o „trzech poleceniach czytających ten sam
    /// <c>LineRunSettings</c>"; w kodzie buduje go <b>dwa</b> — <c>line</c>
    /// i <c>budget</c>. <c>replay</c> odtwarza ZAPIS WEJŚĆ przez
    /// <c>TrainController</c> i <c>DriverNotch</c>, więc nastawa automatu, która
    /// zdejmuje trakcję od X metra, nadpisywałaby wejścia z <c>--keys</c> — po czym
    /// odtworzenie przestałoby być odtworzeniem, przy zielonym teście.
    ///
    /// <para>Ten test przybija dzisiejszą odmowę, żeby dopisanie tam wybiegu było
    /// decyzją podjętą, a nie skutkiem ubocznym. Pytanie „co ma znaczyć wybieg
    /// w odtworzeniu zapisu wejść" jest w kolejce jako 6.A19.</para>
    /// </summary>
    [TestMethod]
    public void Replay_nie_zna_wybiegu_bo_odtwarza_zapis_wejsc()
    {
        var result = Run(
            "replay", "--keys", "build/nie-istnieje.keys",
            "--signalling", Path.Combine(
                RepoRoot(), "data", "design", "signalling", "classic-2026.json"),
            "--coast-from-m", "250");

        Assert.AreEqual(1, result.ExitCode);
        StringAssert.Contains(result.StdErr, "--coast-from-m");
        StringAssert.Contains(result.StdErr, "nie zna opcji");
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

    // --- nieliczbowa wartosc nazywa siebie (6.A14) -------------------------------

    /// <summary>
    /// Sedno pozycji 6.A14. Do 07.09.2026 wartosc nieliczbowa konczyla sie komunikatem
    /// platformy .NET — <c>The input string 'abc' was not in a correct format.</c> —
    /// ktory nie mowil ANI ktorej opcji dotyczy, ANI ktorego polecenia. 6.D20 poprawila
    /// komunikat o BRAKU opcji; ten o zlej WARTOSCI zostal wtedy nietkniety.
    /// </summary>
    [TestMethod]
    public void Line_z_nieliczbowym_limitem_nazywa_polecenie_opcje_i_wartosc()
    {
        var result = Run(
            "line", "--axis", "data/track/L1_A.json", "--limit-kmh", "abc",
            "--exchange-s", "20", "--trace", "build/x.csv");

        Assert.AreEqual(1, result.ExitCode);
        StringAssert.Contains(result.StdErr, "line");
        StringAssert.Contains(result.StdErr, "--limit-kmh");
        StringAssert.Contains(result.StdErr, "abc");
        Assert.IsFalse(
            result.StdErr.Contains("was not in a correct format", StringComparison.Ordinal),
            "komunikat platformy .NET nadal wychodzi na wierzch: " + result.StdErr);
    }

    /// <summary>
    /// Ta sama opcja w innym poleceniu. Bez tego testu poprawka zaszywajaca nowa,
    /// tak samo sztywna nazwe <c>line</c> przeszlaby test wyzej — to ta sama pulapka,
    /// ktora 6.D20 wyjela z <c>RequiredNumber</c>, i ten sam ksztalt kontroli
    /// (<see cref="Budget_bez_limitu_nazywa_budget_a_nie_line"/>).
    /// </summary>
    [TestMethod]
    public void Budget_z_nieliczbowym_limitem_nazywa_budget_a_nie_line()
    {
        var result = Run(
            "budget", "--axis", "data/track/L1_A.json",
            "--signalling", "data/design/signalling/classic-2026.json",
            "--limit-kmh", "abc", "--exchange-s", "20", "--headway-s", "90",
            "--trains", "2", "--steps", "100");

        Assert.AreEqual(1, result.ExitCode);
        StringAssert.Contains(result.StdErr, "budget");
        StringAssert.Contains(result.StdErr, "--limit-kmh");
        Assert.IsFalse(
            result.StdErr.Contains("line nie rozumie", StringComparison.Ordinal),
            "komunikat nazywa line, choc uruchomiono budget: " + result.StdErr);
    }

    /// <summary>
    /// Druga droga wartosci do liczby: <c>OptionalNumber</c>. Opcja bez wartosci
    /// domyslnej i opcja z wartoscia domyslna to dwa osobne pomocniki, wiec poprawka
    /// jednego nie dowodzi niczego o drugim.
    /// </summary>
    [TestMethod]
    public void Line_z_nieliczbowym_oknem_stacji_nazywa_opcje()
    {
        var result = Run(
            "line", "--axis", "data/track/L1_A.json", "--limit-kmh", "72",
            "--exchange-s", "20", "--stop-window-m", "abc", "--trace", "build/x.csv");

        Assert.AreEqual(1, result.ExitCode);
        StringAssert.Contains(result.StdErr, "--stop-window-m");
        StringAssert.Contains(result.StdErr, "abc");
    }

    /// <summary>
    /// Trzecia droga: <c>LongValue</c>. <c>--steps</c> jest <c>long</c>, nie
    /// <c>double</c>, i szlo osobnym <c>long.Parse</c> — komunikat platformy byl tam
    /// dokladnie ten sam, a poprawka innym pomocnikiem.
    /// </summary>
    [TestMethod]
    public void Budget_z_nieliczbowa_liczba_krokow_nazywa_steps()
    {
        var result = Run(
            "budget", "--axis", "data/track/L1_A.json",
            "--signalling", "data/design/signalling/classic-2026.json",
            "--limit-kmh", "72", "--exchange-s", "20", "--headway-s", "90",
            "--trains", "2", "--steps", "abc");

        Assert.AreEqual(1, result.ExitCode);
        StringAssert.Contains(result.StdErr, "--steps");
        StringAssert.Contains(result.StdErr, "abc");
    }

    /// <summary>
    /// Czwarta droga: <c>IntValue</c>. <c>--repeats</c> jest <c>int</c> i ma wartosc
    /// domyslna, wiec przechodzi przez pomocnika, ktorego nie dotyka zaden test wyzej.
    /// </summary>
    [TestMethod]
    public void Budget_z_nieliczbowa_liczba_powtorzen_nazywa_repeats()
    {
        var result = Run(
            "budget", "--axis", "data/track/L1_A.json",
            "--signalling", "data/design/signalling/classic-2026.json",
            "--limit-kmh", "72", "--exchange-s", "20", "--headway-s", "90",
            "--trains", "2", "--steps", "100", "--repeats", "abc");

        Assert.AreEqual(1, result.ExitCode);
        StringAssert.Contains(result.StdErr, "--repeats");
        StringAssert.Contains(result.StdErr, "abc");
    }

    /// <summary>
    /// <c>--trains</c> jest LISTA, wiec cytowany jest zly CZLON, a nie cala wartosc:
    /// przy <c>1,2,4,abc</c> czytajacy ma zobaczyc, ktory z czterech jest zly. Test
    /// pilnuje obu polowek tej decyzji — czlon jest w komunikacie, cala lista nie.
    /// </summary>
    [TestMethod]
    public void Trains_cytuje_zly_czlon_a_nie_cala_liste()
    {
        var result = Run(
            "budget", "--axis", "data/track/L1_A.json",
            "--signalling", "data/design/signalling/classic-2026.json",
            "--limit-kmh", "72", "--exchange-s", "20", "--headway-s", "90",
            "--trains", "1,2,4,abc", "--steps", "100");

        Assert.AreEqual(1, result.ExitCode);
        StringAssert.Contains(result.StdErr, "--trains");
        StringAssert.Contains(result.StdErr, "abc");
        Assert.IsFalse(
            result.StdErr.Contains("1,2,4,abc", StringComparison.Ordinal),
            "komunikat cytuje cala liste zamiast zlego czlonu: " + result.StdErr);
    }

    /// <summary>
    /// <c>--at</c> jest jedna wartoscia o trzech czlonach, wiec cytowana jest CALA:
    /// <c>xx</c> wyjete z <c>10:xx:00</c> nie powiedzialoby, ktora opcje poprawic.
    /// Odwrotna decyzja niz przy <c>--trains</c> i test pilnuje tej roznicy, zeby nie
    /// zostala przypadkiem — a nie z dwoch osobnych powodow.
    /// </summary>
    [TestMethod]
    public void Zegar_cytuje_cala_wartosc_a_nie_zly_czlon()
    {
        var timetable = NapiszTymczasowyRozklad();
        try
        {
            var result = Run("service-day", "--timetable", timetable, "--at", "10:xx:00");

            Assert.AreEqual(1, result.ExitCode);
            StringAssert.Contains(result.StdErr, "--at");
            StringAssert.Contains(result.StdErr, "10:xx:00");
            Assert.IsFalse(
                result.StdErr.Contains("was not in a correct format", StringComparison.Ordinal),
                result.StdErr);
        }
        finally
        {
            File.Delete(timetable);
        }
    }

    /// <summary>
    /// Kontrola drugiego kierunku, bez ktorej testy wyzej byly by zielone rowniez dla
    /// poprawki ZWEZAJACEJ zbior przyjmowanych postaci. <c>double.Parse(text, Inv)</c>
    /// przyjmowal <see cref="System.Globalization.NumberStyles.Float"/> razem
    /// z <see cref="System.Globalization.NumberStyles.AllowThousands"/>; kropka
    /// dziesietna i wykladnik musza przechodzic dalej.
    /// </summary>
    [TestMethod]
    public void Kropka_dziesietna_i_wykladnik_nadal_przechodza()
    {
        var result = Run(
            "line", "--axis", Path.Combine(RepoRoot(), "data", "track", "L1_A.json"),
            "--limit-kmh", "7.2E1", "--exchange-s", "20", "--stop-window-m", "5.5");

        Assert.AreEqual(0, result.ExitCode, result.StdErr);
        Assert.IsFalse(
            result.StdErr.Contains("nie rozumie", StringComparison.Ordinal), result.StdErr);
        StringAssert.Contains(result.StdOut, "[ODCINEK]");
    }

    // --- postac --opcja=wartosc nazywa POSTAC, nie nieznajomosc opcji (6.A22) -----

    /// <summary>
    /// Sedno 6.A22. Do 07.09.2026 <c>--limit-kmh=72</c> konczylo sie komunikatem
    /// „polecenie line nie zna opcji --limit-kmh=72", ktory jest SPRZECZNY z tabela:
    /// <c>--limit-kmh</c> w niej stoi. Runner nie zna POSTACI, a to jest inna
    /// wiadomosc — i wazna, bo cala wartosc odmowy z 6.A11 lezy w tym, ze czytajacy
    /// jej wierzy.
    /// </summary>
    [TestMethod]
    public void Postac_z_rownosciem_nazywa_postac_a_nie_nieznana_opcje()
    {
        var result = Run(
            "line", "--axis", "data/track/L1_A.json", "--limit-kmh=72",
            "--exchange-s", "20");

        Assert.AreEqual(1, result.ExitCode);
        StringAssert.Contains(result.StdErr, "nie przyjmuje postaci");
        StringAssert.Contains(result.StdErr, "--limit-kmh 72");
        Assert.IsFalse(
            result.StdErr.Contains("nie zna opcji", StringComparison.Ordinal),
            "komunikat nadal twierdzi, ze runner nie zna opcji z tabeli: " + result.StdErr);
    }

    /// <summary>
    /// Flaga dostaje INNA rade i to wyszlo z sondowania tej pozycji, nie z wpisu:
    /// pierwsza wersja komunikatu mowila fladze „podaj jako dwa czlony: --atp 1",
    /// co jest nieprawda — flaga wartosci nie bierze, a <c>1</c> zostaloby czlonem
    /// pozycyjnym, ktorego odmowa nie widzi. Komunikat radzacy rzecz niedzialajaca
    /// jest ta sama usterka, ktora ta pozycja zamyka.
    /// </summary>
    [TestMethod]
    public void Postac_z_rownosciem_na_fladze_nie_radzi_dwoch_czlonow()
    {
        var result = Run(
            "budget", "--axis", "data/track/L1_A.json",
            "--signalling", "data/design/signalling/classic-2026.json",
            "--limit-kmh", "72", "--exchange-s", "20", "--headway-s", "90",
            "--trains", "2", "--steps", "100", "--atp=1");

        Assert.AreEqual(1, result.ExitCode);
        StringAssert.Contains(result.StdErr, "jest flagą i wartości nie bierze");
        StringAssert.Contains(result.StdErr, "podaj samo --atp");
        Assert.IsFalse(
            result.StdErr.Contains("--atp 1", StringComparison.Ordinal),
            "komunikat radzi fladze wartosc: " + result.StdErr);
    }

    /// <summary>
    /// Kontrola drugiego kierunku, wprost z pola „Skonczone, gdy" tej pozycji:
    /// literowka nadal daje komunikat o nieznanej opcji i kod 1, czyli poprawka nie
    /// uciszyla odmowy, ktora 6.A11 wprowadzila. Bez tego testu odmowa zdjeta w calosci
    /// przeszlaby oba testy wyzej.
    /// </summary>
    [TestMethod]
    public void Literowka_nadal_dostaje_komunikat_o_nieznanej_opcji()
    {
        var result = Run(
            "line", "--axis", "data/track/L1_A.json", "--zmyslona", "7",
            "--limit-kmh", "72", "--exchange-s", "20");

        Assert.AreEqual(1, result.ExitCode);
        StringAssert.Contains(result.StdErr, "nie zna opcji --zmyslona");
        Assert.IsFalse(
            result.StdErr.Contains("nie przyjmuje postaci", StringComparison.Ordinal),
            result.StdErr);
    }

    /// <summary>
    /// Przedrostek TEZ nieznany: komunikat zostaje o nieznanej opcji, ale nazywa
    /// <c>--zmyslona</c>, a nie <c>--zmyslona=7</c> — bo opcja, ktorej nie ma
    /// w tabeli, nazywa sie <c>--zmyslona</c>. To druga polowa tego samego rozbioru,
    /// nie osobna funkcja.
    /// </summary>
    [TestMethod]
    public void Nieznany_przedrostek_z_rownosciem_nazywa_sam_przedrostek()
    {
        var result = Run(
            "line", "--axis", "data/track/L1_A.json", "--zmyslona=7",
            "--limit-kmh", "72", "--exchange-s", "20");

        Assert.AreEqual(1, result.ExitCode);
        StringAssert.Contains(result.StdErr, "nie zna opcji --zmyslona.");
        Assert.IsFalse(
            result.StdErr.Contains("--zmyslona=7", StringComparison.Ordinal),
            "komunikat cytuje caly czlon zamiast nazwy opcji: " + result.StdErr);
    }

    /// <summary>
    /// Rownosc w WARTOSCI znanej opcji nie jest postacia `--opcja=wartosc`: sciezka
    /// `build/a=b.csv` stoi po `--trace`, wiec jest pomijana razem z opcja (i++).
    /// Odmowa zbudowana na samym wystapieniu znaku rownosci wywrocilaby ten przejazd.
    /// </summary>
    [TestMethod]
    public void Rownosc_w_wartosci_znanej_opcji_przechodzi()
    {
        var trace = Path.Combine(Path.GetTempPath(), "a=b.csv");
        try
        {
            var result = Run(
                "line", "--axis", Path.Combine(RepoRoot(), "data", "track", "L1_A.json"),
                "--limit-kmh", "72", "--exchange-s", "20", "--trace", trace);

            Assert.AreEqual(0, result.ExitCode, result.StdErr);
            Assert.IsFalse(
                result.StdErr.Contains("postaci", StringComparison.Ordinal), result.StdErr);
        }
        finally
        {
            if (File.Exists(trace))
            {
                File.Delete(trace);
            }
        }
    }

    // --- powtorzona opcja jest odmowa, nie nadpisaniem (6.A23) -------------------

    /// <summary>
    /// Sedno 6.A23. Do 07.09.2026 `--limit-kmh 72 --limit-kmh 50` jechalo **72**,
    /// a odwrotna kolejnosc **50** — oba kodem 0 i bez ani jednego zdania o tym, ze
    /// druga wartosc zniknela. `Option` szuka pierwszego wystapienia i nie patrzy
    /// dalej. Wartosc skuteczna nie byla niewidoczna (`[LINIA]` ja podaje, zasluga
    /// 6.A5/6.A6), ale czytajacy nie mial powodu przypuszczac, ze wiersz polecen
    /// mowil takze 50.
    /// </summary>
    [TestMethod]
    public void Powtorzona_opcja_konczy_sie_odmowa()
    {
        var result = Run(
            "line", "--axis", "data/track/L1_A.json", "--limit-kmh", "72",
            "--limit-kmh", "50", "--exchange-s", "20");

        Assert.AreEqual(1, result.ExitCode);
        StringAssert.Contains(result.StdErr, "--limit-kmh");
        StringAssert.Contains(result.StdErr, "więcej niż raz");
    }

    /// <summary>
    /// Odwrotna kolejnosc, bo do tej pozycji wygrywala PIERWSZA wartosc — czyli obie
    /// kolejnosci dawaly INNY przejazd, oba kodem 0. Test na jednej kolejnosci
    /// przeszedlby rowniez dla poprawki, ktora odmawia tylko przy malejacych
    /// wartosciach albo w innym takim przypadkowym ukladzie.
    /// </summary>
    [TestMethod]
    public void Powtorzona_opcja_odmawia_w_obu_kolejnosciach()
    {
        var result = Run(
            "line", "--axis", "data/track/L1_A.json", "--limit-kmh", "50",
            "--limit-kmh", "72", "--exchange-s", "20");

        Assert.AreEqual(1, result.ExitCode);
        StringAssert.Contains(result.StdErr, "więcej niż raz");
    }

    /// <summary>
    /// Kontrola drugiego kierunku: opcja podana RAZ przechodzi nietknieta. Ta pozycja
    /// nie ma prawa tknac przejazdu, a odmowa zbudowana zbyt szeroko odrzucalaby
    /// kazda komende i testy wyzej nadal bylyby zielone.
    /// </summary>
    [TestMethod]
    public void Opcja_podana_raz_nadal_przechodzi()
    {
        var result = Run(
            "line", "--axis", Path.Combine(RepoRoot(), "data", "track", "L1_A.json"),
            "--limit-kmh", "72", "--exchange-s", "20");

        Assert.AreEqual(0, result.ExitCode, result.StdErr);
        StringAssert.Contains(result.StdOut, "[LINIA]");
    }

    /// <summary>
    /// FLAGA powtorzona przechodzi i to jest pole „Poza zakresem" tej pozycji, nie
    /// przeoczenie: `--atp --atp` znaczy dokladnie to samo, co `--atp`, wiec nie ginie
    /// tam zadna wartosc. Test przybija te granice, zeby jej pozniejsze przesuniecie
    /// bylo widoczne, a nie ciche.
    /// </summary>
    [TestMethod]
    public void Powtorzona_flaga_nie_jest_odmowa()
    {
        var result = Run(
            "budget", "--axis", Path.Combine(RepoRoot(), "data", "track", "L1_A.json"),
            "--signalling", Path.Combine(
                RepoRoot(), "data", "design", "signalling", "classic-2026.json"),
            "--limit-kmh", "72", "--exchange-s", "20", "--headway-s", "90",
            "--trains", "2", "--steps", "100", "--atp", "--atp");

        Assert.AreEqual(0, result.ExitCode, result.StdErr);
        StringAssert.Contains(result.StdOut, "ATP=tak");
    }

    // --- zepsuta komorka CSV nazywa plik, wiersz i kolumne (6.A24) ---------------

    /// <summary>
    /// Telemetria z rdzenia plus jej kopia z JEDNA zepsuta komorka. Pliki powstaja
    /// przez `drive --out`, a nie z atrapy, bo `compare` odmawia naglowka niezgodnego
    /// z `DriveTelemetry.Header` — atrapa dowodzilaby czegos innego niz to, co sie
    /// zdarza na prawdziwym pliku.
    /// </summary>
    private static (string Dobry, string Zepsuty) DwaPlikiTelemetrii(int wiersz, int kolumna, string czym)
    {
        var dobry = Path.Combine(Path.GetTempPath(), Path.GetRandomFileName() + ".csv");
        var zepsuty = Path.Combine(Path.GetTempPath(), Path.GetRandomFileName() + ".csv");
        var wynik = Run("drive", "--out", dobry);
        Assert.AreEqual(0, wynik.ExitCode, wynik.StdErr);

        var wiersze = File.ReadAllLines(dobry);
        var komorki = wiersze[wiersz].Split(',');
        komorki[kolumna] = czym;
        wiersze[wiersz] = string.Join(",", komorki);
        File.WriteAllLines(zepsuty, wiersze);
        return (dobry, zepsuty);
    }

    /// <summary>
    /// Sedno 6.A24. Do 07.09.2026 zepsuta komorka konczyla sie komunikatem platformy
    /// .NET — `The input string 'abc' was not in a correct format.` — bez pliku, bez
    /// wiersza i bez kolumny. 6.A14 przeszla po jedenastu drogach wartosci OPCJI
    /// i te jedna zostawila nietknieta, bo zla komorka nie jest zla opcja; nietknieta
    /// nie znaczylo jednak dobra.
    /// </summary>
    [TestMethod]
    public void Zepsuta_komorka_nazywa_plik_wiersz_i_kolumne()
    {
        var (dobry, zepsuty) = DwaPlikiTelemetrii(3, 0, "abc");
        try
        {
            var result = Run("compare", dobry, zepsuty);

            Assert.AreEqual(1, result.ExitCode);
            StringAssert.Contains(result.StdErr, zepsuty);
            StringAssert.Contains(result.StdErr, "wiersz 3");
            StringAssert.Contains(result.StdErr, "kolumna 1");
            StringAssert.Contains(result.StdErr, "step");
            StringAssert.Contains(result.StdErr, "abc");
            Assert.IsFalse(
                result.StdErr.Contains("was not in a correct format", StringComparison.Ordinal),
                "komunikat platformy .NET nadal wychodzi na wierzch: " + result.StdErr);
        }
        finally
        {
            File.Delete(dobry);
            File.Delete(zepsuty);
        }
    }

    /// <summary>
    /// Komunikat nazywa plik ZEPSUTY, a nie pierwszy z wiersza polecen. Bez tego testu
    /// poprawka wypisujaca zawsze `args[1]` przeszlaby test wyzej, a czytajacy szukalby
    /// usterki w pliku, ktory jest w porzadku.
    /// </summary>
    [TestMethod]
    public void Zepsuta_komorka_nazywa_zepsuty_plik_a_nie_pierwszy()
    {
        var (dobry, zepsuty) = DwaPlikiTelemetrii(5, 2, "nie-liczba");
        try
        {
            var result = Run("compare", zepsuty, dobry);

            Assert.AreEqual(1, result.ExitCode);
            StringAssert.Contains(result.StdErr, zepsuty);
            Assert.IsFalse(
                result.StdErr.Contains(dobry, StringComparison.Ordinal),
                "komunikat nazywa plik, ktory jest w porzadku: " + result.StdErr);
        }
        finally
        {
            File.Delete(dobry);
            File.Delete(zepsuty);
        }
    }

    /// <summary>
    /// Numer kolumny idzie z pozycji w wierszu, nie ze stalej: druga kolumna ma inna
    /// nazwe i inny numer niz pierwsza. Test na jednej kolumnie przeszedlby rowniez
    /// dla poprawki wypisujacej zawsze `kolumna 1 step`.
    /// </summary>
    [TestMethod]
    public void Numer_i_nazwa_kolumny_ida_z_pozycji_w_wierszu()
    {
        var (dobry, zepsuty) = DwaPlikiTelemetrii(7, 4, "abc");
        try
        {
            var result = Run("compare", dobry, zepsuty);

            Assert.AreEqual(1, result.ExitCode);
            StringAssert.Contains(result.StdErr, "kolumna 5");
            StringAssert.Contains(result.StdErr, "speed_mps");
            StringAssert.Contains(result.StdErr, "wiersz 7");
        }
        finally
        {
            File.Delete(dobry);
            File.Delete(zepsuty);
        }
    }

    /// <summary>
    /// Kontrola drugiego kierunku: dwa POPRAWNE pliki nadal przechodza kodem 0.
    /// Odmowa zbudowana zbyt szeroko odrzucalaby kazde porownanie, a testy wyzej
    /// nadal bylyby zielone.
    /// </summary>
    [TestMethod]
    public void Dwa_poprawne_pliki_nadal_przechodza()
    {
        var (dobry, _) = DwaPlikiTelemetrii(3, 0, "abc");
        try
        {
            var result = Run("compare", dobry, dobry);

            Assert.AreEqual(0, result.ExitCode, result.StdErr);
            StringAssert.Contains(result.StdOut, "[PORÓWNANIE]");
        }
        finally
        {
            File.Delete(dobry);
        }
    }
    // --- czlon pozycyjny ponad liczbe, jaka polecenie czyta (6.A25) --------------

    /// <summary>
    /// Wartosc podana po FLADZE jest czlonem pozycyjnym i do 07.09.2026 przechodzila
    /// bez slowa.
    /// </summary>
    /// <remarks>
    /// Zmierzone przy 6.A22, ktore swiadomie tego nie tknelo: `--atp 1` i samo `--atp`
    /// dawaly wypis NIEODROZNIALNY, oba kodem 0. Komunikat 6.A22 radzi fladze „podaj
    /// samo --atp" wlasnie dlatego, ze `--atp 1` przechodzi — rada jest poprawna, ale
    /// jej powodem byla ta dziura, a dopoki dziura jest, literowka w wartosci flagi
    /// wyglada dokladnie jak przebieg poprawny.
    /// </remarks>
    [TestMethod]
    public void Wartosc_po_fladze_jest_czlonem_pozycyjnym_i_konczy_sie_odmowa()
    {
        var result = Run(
            "budget", "--axis", Path.Combine(RepoRoot(), "data", "track", "L1_A.json"),
            "--signalling", Path.Combine(
                RepoRoot(), "data", "design", "signalling", "classic-2026.json"),
            "--limit-kmh", "72", "--exchange-s", "20", "--headway-s", "90",
            "--trains", "2", "--steps", "100", "--atp", "1");

        Assert.AreEqual(1, result.ExitCode, result.StdOut);
        StringAssert.Contains(result.StdErr, "człon pozycyjny 1");
        StringAssert.Contains(result.StdErr, "nie bierze ani jednego");
    }

    /// <summary>
    /// Czlon bez minusa, ktory nie jest wartoscia zadnej opcji — druga polowa tej samej
    /// dziury. `budget ... zmyslony_czlon` konczylo sie kodem 0 i wypisem `ATP=nie`.
    /// </summary>
    [TestMethod]
    public void Czlon_pozycyjny_nieznany_poleceniu_konczy_sie_odmowa()
    {
        var result = Run(
            "budget", "--axis", Path.Combine(RepoRoot(), "data", "track", "L1_A.json"),
            "--signalling", Path.Combine(
                RepoRoot(), "data", "design", "signalling", "classic-2026.json"),
            "--limit-kmh", "72", "--exchange-s", "20", "--headway-s", "90",
            "--trains", "2", "--steps", "100", "zmyslony_czlon");

        Assert.AreEqual(1, result.ExitCode, result.StdOut);
        StringAssert.Contains(result.StdErr, "człon pozycyjny zmyslony_czlon");
    }

    /// <summary>
    /// Kontrola drugiego kierunku, i to ONA jest tu wazniejsza od odmow wyzej.
    /// </summary>
    /// <remarks>
    /// Odmowa 6.A11 i 6.A15 odsiewa czlony bez minusa CELOWO, bo `compare` bierze dwie
    /// sciezki pozycyjnie. Odmowa zbudowana na „wszystko, czego nie znam" wywrocilaby
    /// to polecenie w calosci — a testy odmowy wyzej bylyby wtedy nadal zielone. To
    /// jest dokladnie ta kontrola negatywna, ktorej pozycja 6.A25 zazadala: zdjecie
    /// liczby czlonow pozycyjnych z tabeli wywraca TEN test, nie tamte.
    /// </remarks>
    [TestMethod]
    public void Compare_z_dwiema_sciezkami_nadal_przechodzi()
    {
        var (dobry, _) = DwaPlikiTelemetrii(3, 0, "abc");
        try
        {
            var result = Run("compare", dobry, dobry);

            Assert.AreEqual(0, result.ExitCode, result.StdErr);
            StringAssert.Contains(result.StdOut, "[PORÓWNANIE]");
        }
        finally
        {
            File.Delete(dobry);
        }
    }

    /// <summary>
    /// Trzecia sciezka jest odmowa, i komunikat podaje LICZBE, ktora polecenie bierze,
    /// zamiast mowic „nie bierze zadnego" — inaczej odmowa dla `compare` czytalaby sie
    /// jak sprzecznosc z faktem, ze dwie sciezki wlasnie przeszly.
    /// </summary>
    [TestMethod]
    public void Compare_z_trzecia_sciezka_nazywa_liczbe_ktora_bierze()
    {
        var (dobry, _) = DwaPlikiTelemetrii(3, 0, "abc");
        try
        {
            var result = Run("compare", dobry, dobry, dobry);

            Assert.AreEqual(1, result.ExitCode, result.StdOut);
            StringAssert.Contains(result.StdErr, "bierze ich 2");
            StringAssert.Contains(result.StdErr, "3 w kolejności");
        }
        finally
        {
            File.Delete(dobry);
        }
    }

    /// <summary>
    /// Wartosc znanej opcji NIE liczy sie jako czlon pozycyjny, bo jest pomijana razem
    /// z opcja. Bez tego testu odmowa liczaca kazdy czlon bez minusa wywrocilaby
    /// KAZDA komende z jakakolwiek opcja wartosciowa — a to widac tylko wtedy, gdy
    /// ktos tego zada wprost.
    /// </summary>
    [TestMethod]
    public void Wartosci_znanych_opcji_nie_licza_sie_jako_czlony_pozycyjne()
    {
        var result = Run(
            "line", "--axis", Path.Combine(RepoRoot(), "data", "track", "L1_A.json"),
            "--limit-kmh", "72", "--exchange-s", "20", "--stop-window-m", "1.5",
            "--brake-usage", "0.8");

        Assert.AreEqual(0, result.ExitCode, result.StdErr);
        StringAssert.Contains(result.StdOut, "[LINIA]");
    }

    /// <summary>
    /// Wartosc UJEMNA po znanej opcji nie jest ani nieznana opcja, ani czlonem
    /// pozycyjnym — pomijanie dziala na czlonie NASTEPUJACYM po opcji, nie na jego
    /// kształcie.
    /// </summary>
    /// <remarks>
    /// Test sprawdza TRESC odmowy, a nie kod wyjscia, i jest to pomiar, nie wygoda:
    /// pierwsza wersja zadala kodu 0 i padla — `--coast-from-m -1` konczy sie kodem 1
    /// z komunikatem „Poczatek wybiegu musi byc skonczone i nieujemne", czyli odmowa
    /// DZIEDZINY, ktora do rozbioru argumentow nie ma nic. Zadanie kodu 0 mierzylo
    /// wiec zakres wartosci opcji, a nie to, co ta pozycja zmienia. Wlasciwym pomiarem
    /// jest: wartosc ujemna dochodzi do dziedziny, czyli rozbior jej nie przechwycil.
    /// </remarks>
    [TestMethod]
    public void Wartosc_ujemna_po_znanej_opcji_nie_jest_czlonem_pozycyjnym()
    {
        var result = Run(
            "line", "--axis", Path.Combine(RepoRoot(), "data", "track", "L1_A.json"),
            "--limit-kmh", "72", "--exchange-s", "20", "--coast-from-m", "-1");

        Assert.IsFalse(result.StdErr.Contains("człon pozycyjny"), result.StdErr);
        Assert.IsFalse(result.StdErr.Contains("nie zna opcji"), result.StdErr);
        StringAssert.Contains(result.StdErr, "Początek wybiegu");
    }
    // --- ksztalt wyjscia kazdej odmowy `compare` (6.A27) ------------------------

    /// <summary>
    /// Telemetria z rdzenia plus jej kopia zmieniona jednym przekształceniem wierszy.
    /// Pliki powstaja przez `drive --out`, nie z atrapy — `compare` odmawia naglowka
    /// niezgodnego z `DriveTelemetry.Header`, wiec atrapa dowodzilaby czegos innego.
    /// </summary>
    private static (string Dobry, string Inny) DwaPlikiPrzez(Func<string[], string[]> zmiana)
    {
        var dobry = Path.Combine(Path.GetTempPath(), Path.GetRandomFileName() + ".csv");
        var inny = Path.Combine(Path.GetTempPath(), Path.GetRandomFileName() + ".csv");
        var wynik = Run("drive", "--out", dobry);
        Assert.AreEqual(0, wynik.ExitCode, wynik.StdErr);
        File.WriteAllLines(inny, zmiana(File.ReadAllLines(dobry)));
        return (dobry, inny);
    }

    /// <summary>
    /// Wspolny ksztalt wszystkich czterech odmow: przedrostek `BŁĄD:` i kod 1.
    /// </summary>
    /// <remarks>
    /// 6.A16 ujednolicila KOD wyjscia kazdej odmowy argumentowej. Ksztalt zostal
    /// nieujednolicony w czterech miejscach `Compare`, ktore pisaly na stderr wprost
    /// i wracaly `return 1`, omijajac wspolny handler w `Main` — a on jest jedynym
    /// miejscem dodajacym przedrostek. Ksztalt wyjscia jest wyrocznia dla czytajacego
    /// log CI i dla `grep`; wyjatek od wzorca psuje go tak samo, jak komunikat
    /// mowiacy nieprawde psul odmowe przy 6.A22.
    /// </remarks>
    /// <remarks>
    /// Pomocnik sprawdza WYLACZNIE to, co wspolne — kod 1 i przedrostek na poczatku.
    /// Tresc kazdej z czterech odmow asercjonuje jej wlasny test, w swoim ciele,
    /// i nie jest to podzial estetyczny: bramka 6.D28 zapalila sie na pierwszej
    /// wersji tych testow, bo dwie z nich delegowaly do pomocnika WSZYSTKIE asercje
    /// i mialy ciala bez ani jednej. Test bez asercji w ciele przechodzi takze wtedy,
    /// gdy pomocnik przestanie cokolwiek sprawdzac.
    /// </remarks>
    private static void OdmowaMaWspolnyKsztalt(
        (int ExitCode, string StdOut, string StdErr) wynik)
    {
        Assert.AreEqual(1, wynik.ExitCode, wynik.StdOut);
        Assert.IsTrue(
            wynik.StdErr.TrimStart().StartsWith("BŁĄD: ", StringComparison.Ordinal),
            "przedrostek ma stac na POCZATKU odmowy, nie gdziekolwiek w tresci: "
            + wynik.StdErr);
    }

    [TestMethod]
    public void Rozna_liczba_wierszy_ma_przedrostek_bledu()
    {
        var (dobry, krotszy) = DwaPlikiPrzez(w => w[..^3]);
        try
        {
            var wynik = Run("compare", dobry, krotszy);
            OdmowaMaWspolnyKsztalt(wynik);
            StringAssert.Contains(wynik.StdErr, "różna liczba wierszy:");
        }
        finally
        {
            File.Delete(dobry);
            File.Delete(krotszy);
        }
    }

    [TestMethod]
    public void Zly_naglowek_telemetrii_ma_przedrostek_bledu()
    {
        var (dobry, zly) = DwaPlikiPrzez(w =>
        {
            var kopia = (string[])w.Clone();
            kopia[0] = "zly,naglowek";
            return kopia;
        });
        try
        {
            var wynik = Run("compare", zly, zly);
            OdmowaMaWspolnyKsztalt(wynik);
            StringAssert.Contains(
                wynik.StdErr, "nagłówki telemetrii nie zgadzają się z formatem rdzenia");
        }
        finally
        {
            File.Delete(dobry);
            File.Delete(zly);
        }
    }

    /// <summary>
    /// Trzecia odmowa. Pole „Poza zakresem" 6.A27 wylaczalo ja WARUNKOWO — „jezeli
    /// pomiar pokaze, ze ona juz przedrostek ma". Pomiar pokazal, ze NIE mial:
    /// `Console.Error` + `return 1`, tak samo jak dwie wyzej.
    /// </summary>
    [TestMethod]
    public void Zla_liczba_kolumn_ma_przedrostek_bledu()
    {
        var (dobry, zly) = DwaPlikiPrzez(w =>
        {
            var kopia = (string[])w.Clone();
            kopia[5] = "1,2,3";
            return kopia;
        });
        try
        {
            var wynik = Run("compare", zly, dobry);
            OdmowaMaWspolnyKsztalt(wynik);
            StringAssert.Contains(wynik.StdErr, "zła liczba kolumn");
            StringAssert.Contains(wynik.StdErr, "wiersz 5");
        }
        finally
        {
            File.Delete(dobry);
            File.Delete(zly);
        }
    }

    /// <summary>
    /// Czwarta odmowa — ta, o ktorej wpis 6.A27 nie wiedzial wcale. Pozycja mowila
    /// o DWOCH; pomiar w ciele `Compare` znalazl cztery `Console.Error` + `return 1`.
    /// </summary>
    [TestMethod]
    public void Rozna_faza_scenariusza_ma_przedrostek_bledu()
    {
        var (dobry, zly) = DwaPlikiPrzez(w =>
        {
            var kopia = (string[])w.Clone();
            var komorki = kopia[5].Split(',');
            komorki[^1] = "INNA-FAZA";
            kopia[5] = string.Join(",", komorki);
            return kopia;
        });
        try
        {
            var wynik = Run("compare", zly, dobry);
            OdmowaMaWspolnyKsztalt(wynik);
            StringAssert.Contains(wynik.StdErr, "różna faza scenariusza");
            StringAssert.Contains(wynik.StdErr, "INNA-FAZA");
        }
        finally
        {
            File.Delete(dobry);
            File.Delete(zly);
        }
    }

    /// <summary>
    /// Kontrola drugiego kierunku: dwa poprawne pliki nadal koncza sie kodem 0
    /// i wypisem na STDOUT. Odmowa zbudowana zbyt szeroko odrzucalaby kazde
    /// porownanie, a cztery testy wyzej nadal bylyby zielone.
    /// </summary>
    [TestMethod]
    public void Dwa_identyczne_pliki_nadal_koncza_sie_kodem_zero()
    {
        var (dobry, kopia) = DwaPlikiPrzez(w => w);
        try
        {
            var wynik = Run("compare", dobry, kopia);

            Assert.AreEqual(0, wynik.ExitCode, wynik.StdErr);
            StringAssert.Contains(wynik.StdOut, "[PORÓWNANIE]");
            Assert.IsFalse(wynik.StdErr.Contains("BŁĄD", StringComparison.Ordinal),
                "porownanie dwoch poprawnych plikow wypisalo odmowe: " + wynik.StdErr);
        }
        finally
        {
            File.Delete(dobry);
            File.Delete(kopia);
        }
    }
}
