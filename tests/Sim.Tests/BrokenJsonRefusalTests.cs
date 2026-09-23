using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Text.RegularExpressions;
using MetroBxl.Sim.Line;
using MetroBxl.Sim.Runner;
using MetroBxl.Sim.Signalling;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace MetroBxl.Sim.Tests;

/// <summary>
/// Plik o ZEPSUTEJ SKŁADNI ma kończyć się odmową, a nie stosem wywołań (6.D229).
///
/// <para><b>Czego te testy pilnują.</b> Nie tego, że loader „coś rzuca" — tego, że
/// rzuca typ, który filtry <c>catch</c> tego repozytorium <b>wymieniają z nazwy</b>:
/// wspólny handler <c>Sim.Runner.Program.Main</c> (<c>IOException</c>,
/// <c>ArgumentException</c>, <c>FormatException</c>, <c>InvalidOperationException</c>)
/// i filtry <c>FirstRun.ReadSignallingPlan</c>/<c>ReadInputLog</c>
/// (<c>ArgumentException</c>, <c>FormatException</c>). Przed 6.D229
/// <c>JsonDocument.Parse</c> rzucał <c>JsonReaderException</c>, którego nie wymienia
/// ŻADEN z nich — i `--signalling` na pliku z `{{{` kończyło się kodem 134,
/// angielskim komunikatem .NET-a i stosem, zamiast wierszem odmowy.</para>
///
/// <para><b>Dlaczego filtry stoją w teście jako kopia, a nie jako odwołanie.</b>
/// Filtr jest wyrażeniem <c>when</c> w kodzie, którego nie da się z niego odczytać.
/// Kopia listy typów zestarzeje się, gdy ktoś filtr rozszerzy — ale zestarzeje się
/// w stronę BEZPIECZNĄ: test dalej wymaga typu, który stary filtr łapał.</para>
/// </summary>
[TestClass]
public sealed class BrokenJsonRefusalTests
{
    /// <summary>Filtr wspólnego handlera z <c>src/Sim.Runner/Program.cs:247</c>.</summary>
    private static bool ZlapieHandlerRunnera(Exception error)
        => error is IOException or ArgumentException or FormatException or InvalidOperationException;

    /// <summary>Filtr z <c>src/Game/FirstRun.cs:1034</c> i <c>:1061</c>.</summary>
    private static bool ZlapieFiltrFirstRun(Exception error)
        => error is ArgumentException or FormatException;

    /// <summary>Kształty, na których 6.D229 zmierzyło szczelinę.</summary>
    private static IEnumerable<(string Nazwa, string Json)> ZepsutaSkladnia()
    {
        yield return ("{{{", "{{{");
        yield return ("napis pusty", "");
    }

    private static IEnumerable<(string Nazwa, Action<string> Wywolaj)> Loadery()
    {
        yield return ("SignallingPlan.FromJson", json => SignallingPlan.FromJson(json));
        yield return ("TrackAxis.FromJson", json => TrackAxis.FromJson(json));
        yield return ("ServiceDay.FromJson", json => ServiceDay.FromJson(json));
        yield return ("CbtcTestArea.FromJson", json => CbtcTestArea.FromJson(json));
        yield return ("JsonText.Parse", json => JsonText.Parse(json, "plik").Dispose());
    }

    [TestMethod]
    public void Zepsuta_skladnia_konczy_sie_typem_ktory_filtry_lapia()
    {
        var sprawdzonych = 0;
        foreach (var (loader, wywolaj) in Loadery())
        {
            foreach (var (ksztalt, json) in ZepsutaSkladnia())
            {
                var error = Assert.ThrowsException<FormatException>(
                    () => wywolaj(json),
                    $"{loader} na `{ksztalt}`: oczekiwano FormatException");

                Assert.IsTrue(ZlapieHandlerRunnera(error),
                    $"{loader} na `{ksztalt}`: {error.GetType().Name} omija handler Sim.Runner");
                Assert.IsTrue(ZlapieFiltrFirstRun(error),
                    $"{loader} na `{ksztalt}`: {error.GetType().Name} omija filtr FirstRun");
                sprawdzonych++;
            }
        }

        Assert.AreEqual(10, sprawdzonych,
            "test nie przeszedł po wszystkich parach loader × kształt");
    }

    [TestMethod]
    public void Odmowa_jest_po_polsku_i_nazywa_plik()
    {
        var error = Assert.ThrowsException<FormatException>(
            () => SignallingPlan.FromJson("{{{"),
            "plan o zepsutej składni ma kończyć się FormatException");

        StringAssert.Contains(error.Message, "nie jest poprawnym JSON-em",
            "odmowa nie mówi po polsku, czego dotyczy");
        StringAssert.Contains(error.Message, "plan sygnalizacji",
            "odmowa nie nazywa czytanego pliku");

        // Powód parsera zostaje DOŁĄCZONY jako InnerException, a nie wyrzucony — ale
        // od 6.D357 już nie w tekście odmowy: miejsce w pliku podaje sam komunikat,
        // z liczb parsera (test niżej).
        Assert.IsInstanceOfType(error.InnerException, typeof(JsonException),
            "powód parsera ma zostać jako InnerException");
    }

    /// <summary>
    /// Słowa komunikatu: ciągi liter z łącznikami w środku. Łącznik jest w słowie, bo
    /// polska odmiana skrótowca pisze się z nim — „JSON-em” jest JEDNYM słowem
    /// polskim, a nie angielskim „JSON” z doklejką. Bez tego sito uznałoby za tekst
    /// parsera sam polski początek odmowy, który stał tu przed 6.D357.
    /// </summary>
    private static HashSet<string> Slowa(string tekst)
        => Regex.Matches(tekst, @"\p{L}+(?:-\p{L}+)*")
            .Select(m => m.Value.ToLowerInvariant())
            .ToHashSet();

    [TestMethod]
    public void Odmowa_nie_niesie_tekstu_parsera_i_podaje_wiersz_oraz_bajt()
    {
        // 6.D357: do tej pozycji wiersz odmowy kończył się `error.Message` .NET-a,
        // np. „'{' is an invalid start of a property name. Expected a '"'.
        // LineNumber: 0 | BytePositionInLine: 1.” Pozycja stoi w wyjątku jako liczby,
        // więc ma przyjść stamtąd, a nie ze zdania parsera.
        var sprawdzonych = 0;
        foreach (var (loader, wywolaj) in Loadery())
        {
            foreach (var (ksztalt, json) in ZepsutaSkladnia())
            {
                var error = Assert.ThrowsException<FormatException>(
                    () => wywolaj(json),
                    $"{loader} na `{ksztalt}`: oczekiwano FormatException");
                var parser = (JsonException)error.InnerException!;

                var wspolne = Slowa(error.Message).Intersect(Slowa(parser.Message)).ToList();
                Assert.AreEqual(0, wspolne.Count,
                    $"{loader} na `{ksztalt}`: odmowa niesie słowa parsera "
                    + $"[{string.Join(", ", wspolne)}]: {error.Message}");

                var pozycja = Regex.Match(error.Message, @"w wierszu (\d+), bajt (\d+)");
                Assert.IsTrue(pozycja.Success,
                    $"{loader} na `{ksztalt}`: odmowa nie podaje wiersza i bajtu: {error.Message}");
                Assert.AreEqual(parser.LineNumber + 1, long.Parse(pozycja.Groups[1].Value),
                    $"{loader} na `{ksztalt}`: wiersz nie jest `LineNumber` parsera liczonym od 1");
                Assert.AreEqual(parser.BytePositionInLine + 1, long.Parse(pozycja.Groups[2].Value),
                    $"{loader} na `{ksztalt}`: bajt nie jest `BytePositionInLine` parsera liczonym od 1");
                sprawdzonych++;
            }
        }

        Assert.AreEqual(10, sprawdzonych,
            "test nie przeszedł po wszystkich parach loader × kształt");
    }

    [TestMethod]
    public void Pozycja_jest_ta_sama_co_w_edytorze()
    {
        // Kontrola znaczenia, nie wzoru: test wyżej sprawdza, że liczby są liczbami
        // parsera plus jeden, a ten — że plus jeden jest DOBRĄ poprawką. `x` stoi
        // w trzecim wierszu, na trzeciej pozycji, tak jak pokaże go edytor.
        var error = Assert.ThrowsException<FormatException>(
            () => JsonText.Parse("{\n  \"a\": 1,\n  x\n}", "plik").Dispose(),
            "plik z `x` zamiast klucza ma kończyć się FormatException");

        StringAssert.Contains(error.Message, "w wierszu 3, bajt 3",
            "pozycja błędu nie zgadza się z tym, co gracz zobaczy w edytorze");
    }

    [TestMethod]
    public void Poprawny_plik_przechodzi_nietkniety()
    {
        // Kontrola dodatnia w samym teście: owinięcie ma odmawiać TYLKO zepsutej
        // składni. Plan pakietu A ma się wczytać tak samo jak przed 6.D229.
        var plan = SignallingPlanTests.PackageAPlan();
        Assert.IsTrue(plan.Blocks.Count > 0, "poprawny plan wczytał się pusty");
    }
    // --- 6.D356: dokument poprawny składniowo, ale innego KSZTAŁTU ---------------

    /// <summary>Trzy kształty, na których 6.D235 zmierzyło angielski wiersz CLI.</summary>
    private static IEnumerable<(string Nazwa, string Json)> InnyKsztalt()
    {
        yield return ("[]", "[]");
        yield return ("5", "5");
        yield return ("{\"points\": 5}", "{\"points\": 5}");
    }

    /// <summary>
    /// <see cref="Program.Main"/> z przechwyconym stderr — ta sama droga, którą idzie
    /// człowiek z terminala (kopia pomocnika z <c>RunnerCommandTests</c>).
    /// </summary>
    private static (int ExitCode, string StdErr) Uruchom(params string[] args)
    {
        var originalOut = Console.Out;
        var originalError = Console.Error;
        using var outWriter = new StringWriter();
        using var errWriter = new StringWriter();
        Console.SetOut(outWriter);
        Console.SetError(errWriter);
        try
        {
            return (Program.Main(args), errWriter.ToString());
        }
        finally
        {
            Console.SetOut(originalOut);
            Console.SetError(originalError);
        }
    }

    /// <summary>
    /// Wiersz odmowy <c>line --axis</c> na dokumencie innego kształtu: kod 1 jak przed
    /// 6.D356, ale bez ani jednego słowa z komunikatu <c>System.Text.Json</c>.
    /// </summary>
    /// <remarks>
    /// Słowa zakazane nie są wpisane w test, tylko wzięte z PRAWDZIWEGO wyjątku tego
    /// samego czytnika na tym samym kształcie — test nie zestarzeje się, gdy .NET zmieni
    /// brzmienie komunikatu. Ścieżka pliku jest z wiersza usuwana przed porównaniem,
    /// żeby katalog tymczasowy nie mógł ani zapalić, ani zgasić testu.
    /// </remarks>
    [TestMethod]
    public void Inny_ksztalt_w_Sim_Runner_konczy_sie_kodem_1_i_wierszem_po_polsku()
    {
        var sprawdzonych = 0;
        foreach (var (ksztalt, json) in InnyKsztalt())
        {
            var zrodlowy = Assert.ThrowsException<InvalidOperationException>(
                () => TrackAxis.FromJson(json),
                $"TrackAxis.FromJson na `{ksztalt}`: oczekiwano wyjątku System.Text.Json");
            Assert.IsTrue(Program.IsWrongJsonShape(zrodlowy),
                $"`{ksztalt}`: wyjątek nie został rozpoznany jako kształt: {zrodlowy.Message}");

            var sciezka = Path.Combine(Path.GetTempPath(), $"6d356-{Guid.NewGuid():N}.json");
            File.WriteAllText(sciezka, json);
            try
            {
                var (kod, stderr) = Uruchom(
                    "line", "--axis", sciezka, "--limit-kmh", "72", "--exchange-s", "20");

                Assert.AreEqual(1, kod, $"`{ksztalt}`: kod wyjścia zmienił się");
                StringAssert.StartsWith(stderr, "BŁĄD: " + sciezka + ": ",
                    $"`{ksztalt}`: wiersz odmowy nie nazywa pliku: {stderr}");
                StringAssert.Contains(stderr, Program.WrongJsonShapeText,
                    $"`{ksztalt}`: wiersz odmowy nie mówi własnymi słowami: {stderr}");

                var bezSciezki = stderr.Replace(sciezka, string.Empty, StringComparison.Ordinal);
                var slowa = Regex.Matches(zrodlowy.Message, @"[A-Za-z]{3,}")
                    .Select(m => m.Value)
                    .Distinct(StringComparer.Ordinal)
                    .ToArray();
                Assert.IsTrue(slowa.Length >= 5,
                    $"`{ksztalt}`: z komunikatu parsera wyszło za mało słów do porównania");
                foreach (var slowo in slowa)
                {
                    Assert.IsFalse(
                        Regex.IsMatch(bezSciezki, $@"\b{slowo}\b", RegexOptions.IgnoreCase),
                        $"`{ksztalt}`: wiersz odmowy niesie słowo `{slowo}` z System.Text.Json: {stderr}");
                }
            }
            finally
            {
                File.Delete(sciezka);
            }

            sprawdzonych++;
        }

        Assert.AreEqual(3, sprawdzonych, "test nie przeszedł po wszystkich trzech kształtach");
    }

    /// <summary>
    /// Kontrola w drugą stronę: własne wyjątki rdzenia TYCH SAMYCH typów niosą polski
    /// komunikat i rozpoznawane jako kształt być nie mogą — inaczej handler przepisałby
    /// komunikat, którego ta pozycja nie dotyczy.
    /// </summary>
    [TestMethod]
    public void Wlasny_wyjatek_rdzenia_tego_samego_typu_nie_jest_ksztaltem()
    {
        var plan = SignallingPlanTests.PackageAPlan();
        var brakBloku = Assert.ThrowsException<KeyNotFoundException>(
            () => plan.IndexOf("nie-ma-takiego-bloku"),
            "plan pakietu A nie odmówił nieistniejącego bloku");
        Assert.IsFalse(Program.IsWrongJsonShape(brakBloku),
            "KeyNotFoundException rdzenia wzięty za dokument innego kształtu");

        var brakPola = Assert.ThrowsException<FormatException>(
            () => TrackAxis.FromJson("{}"),
            "oś `{}` ma kończyć się polską odmową loadera");
        Assert.IsFalse(Program.IsWrongJsonShape(brakPola),
            "odmowa loadera na `{}` wzięta za wyjątek System.Text.Json");

        Assert.IsFalse(Program.IsWrongJsonShape(new InvalidOperationException("x")),
            "wyjątek bez miejsca rzucenia wzięty za wyjątek System.Text.Json");
    }
    /// <summary>
    /// Wspólny handler <see cref="Program.Main"/>: pole złego typu w pliku, który
    /// przeszedł już przez czytnik (<c>--timetable</c> z <c>"segments": 5</c>), rzuca
    /// z <c>System.Text.Json</c> POZA <c>FromFile</c>. Kod 1 jak przed 6.D356, wiersz
    /// bez angielskiego komunikatu.
    /// </summary>
    [TestMethod]
    public void Inny_ksztalt_poza_czytnikiem_trafia_do_handlera_po_polsku()
    {
        var sciezka = Path.Combine(Path.GetTempPath(), $"6d356-{Guid.NewGuid():N}.json");
        File.WriteAllText(sciezka, "{\"segments\": 5}");
        try
        {
            var (kod, stderr) = Uruchom(
                "line", "--axis",
                Path.Combine(MetroBxl.Tests.Shared.KorzenRepozytorium.Sciezka, "data", "track", "L1_A.json"),
                "--limit-kmh", "72", "--exchange-s", "20", "--timetable", sciezka);

            Assert.AreEqual(1, kod, $"kod wyjścia zmienił się: {stderr}");
            Assert.AreEqual("BŁĄD: " + Program.WrongJsonShapeText, stderr.TrimEnd(),
                "wiersz handlera nie jest polskim opisem kształtu");
        }
        finally
        {
            File.Delete(sciezka);
        }
    }
}
