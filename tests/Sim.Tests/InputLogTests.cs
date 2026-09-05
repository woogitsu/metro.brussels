using System;
using System.Collections.Generic;
using System.Linq;
using MetroBxl.Sim.Train;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace MetroBxl.Sim.Tests;

/// <summary>
/// Zapis wejść maszynisty po numerze kroku (<see cref="InputLog"/>,
/// <see cref="InputLogRecorder"/>, <see cref="DriverKeys"/>).
///
/// <para><c>docs/01-architecture.md</c> §Determinizm: „z ziarna + zapisu wejść da się
/// odtworzyć przejazd". Zapisu nie było w ogóle
/// (<c>reports/droga-do-grywalnosci.md</c> §1.6), więc nie było też czego porównywać
/// z rdzeniem — a bramki tego repozytorium porównują przy progu 0.</para>
///
/// <para>Testy niżej pilnują trzech rzeczy: że plik jest bezstratny w obie strony
/// (<c>ToText</c> → <c>Parse</c> → <c>ToText</c>), że <see cref="InputLog.KeysAt"/>
/// odpowiada stanem obowiązującym w KROKU, a nie najbliższym wpisem, i że uszkodzony
/// plik jest odrzucany, a nie cicho poprawiany.</para>
/// </summary>
[TestClass]
public sealed class InputLogTests
{
    private static InputLog Sample() => new(7200, new[]
    {
        new InputLogEntry(0, DriverKeys.Powering),
        new InputLogEntry(3600, DriverKeys.Braking),
        new InputLogEntry(7000, DriverKeys.None),
    });

    // --- odczyt stanu w kroku -----------------------------------------------------

    [TestMethod]
    public void KeysAtGivesTheEntryInForceNotTheNearestOne()
    {
        var log = Sample();

        Assert.AreEqual(DriverKeys.Powering, log.KeysAt(0));
        Assert.AreEqual(DriverKeys.Powering, log.KeysAt(3599));
        Assert.AreEqual(DriverKeys.Braking, log.KeysAt(3600));
        Assert.AreEqual(DriverKeys.Braking, log.KeysAt(6999));
        Assert.AreEqual(DriverKeys.None, log.KeysAt(7000));
        Assert.AreEqual(DriverKeys.None, log.KeysAt(7199));
    }

    [TestMethod]
    public void KeysBeforeTheFirstEntryAreNone()
    {
        var log = new InputLog(100, new[] { new InputLogEntry(10, DriverKeys.Powering) });

        Assert.AreEqual(DriverKeys.None, log.KeysAt(0));
        Assert.AreEqual(DriverKeys.None, log.KeysAt(9));
        Assert.AreEqual(DriverKeys.Powering, log.KeysAt(10));
    }

    [TestMethod]
    public void EmptyLogGivesNoKeysAtEveryStep()
    {
        var log = new InputLog(50, Array.Empty<InputLogEntry>());

        Assert.AreEqual(DriverKeys.None, log.KeysAt(0));
        Assert.AreEqual(DriverKeys.None, log.KeysAt(49));
    }

    // --- format -------------------------------------------------------------------

    [TestMethod]
    public void TextRoundTripsWithoutLoss()
    {
        var log = Sample();

        var again = InputLog.Parse(log.ToText());

        Assert.AreEqual(log.Steps, again.Steps);
        CollectionAssert.AreEqual(new List<InputLogEntry>(log.Entries), new List<InputLogEntry>(again.Entries));
        Assert.AreEqual(log.ToText(), again.ToText());
    }

    [TestMethod]
    public void TextIsReadableAndStepIndexed()
    {
        // Format ma być czytelny dla człowieka, jak reszta wyjść tego repo, i ma
        // trzymać NUMER KROKU, a nie czas. Ten test jest po to, żeby zmiana formatu
        // była decyzją, a nie skutkiem ubocznym.
        var text = Sample().ToText();

        StringAssert.Contains(text, "wersja=1");
        StringAssert.Contains(text, "kroki=7200");
        StringAssert.Contains(text, "krok;klawisze");
        StringAssert.Contains(text, "\n0;W\n");
        StringAssert.Contains(text, "\n3600;S\n");
        StringAssert.Contains(text, "\n7000;-\n");
    }

    [TestMethod]
    public void CommentsAndBlankLinesAreIgnored()
    {
        var log = InputLog.Parse(
            "# cokolwiek\n\nwersja=1\n# jeszcze coś\nkroki=10\nkrok;klawisze\n\n0;X\n");

        Assert.AreEqual(10L, log.Steps);
        Assert.AreEqual(1, log.Entries.Count);
        Assert.AreEqual(DriverKeys.Coasting, log.KeysAt(0));
    }

    [TestMethod]
    public void BothKeysHeldAtOnceSurviveTheRoundTrip()
    {
        // Bezstratność: pierwszeństwo W nad S jest regułą DriverNotch, nie własnością
        // zapisu. Gdyby zapis trzymał już rozstrzygnięty klawisz, zmiana tej reguły
        // cicho zmieniłaby znaczenie starych plików.
        var both = new DriverKeys(Power: true, Brake: true, Coast: false, Emergency: false);
        var log = new InputLog(5, new[] { new InputLogEntry(0, both) });

        var again = InputLog.Parse(log.ToText());

        Assert.AreEqual("WS", both.Code());
        Assert.AreEqual(both, again.KeysAt(0));
    }

    /// <summary>
    /// Hamulec awaryjny przechodzi przez zapis. Bez tego przejazd, w którym maszynista
    /// go użył, odtworzyłby się BEZ hamowania — a odtworzenie, które gubi jeden
    /// klawisz, wygląda dokładnie tak samo jak odtworzenie poprawne, tyle że kończy się
    /// gdzie indziej.
    /// </summary>
    [TestMethod]
    public void EmergencyBrakeSurvivesTheRoundTrip()
    {
        var log = new InputLog(20, new[]
        {
            new InputLogEntry(0, DriverKeys.Powering),
            new InputLogEntry(10, DriverKeys.EmergencyBraking),
        });

        var again = InputLog.Parse(log.ToText());

        Assert.AreEqual("E", DriverKeys.EmergencyBraking.Code());
        Assert.AreEqual(DriverKeys.Powering, again.KeysAt(9));
        Assert.AreEqual(DriverKeys.EmergencyBraking, again.KeysAt(10));
        Assert.IsTrue(again.KeysAt(10).Emergency);
    }

    /// <summary>
    /// Dopisanie znaku <c>E</c> do zestawu NIE zmieniło zapisu przejazdów, w których
    /// go nie użyto: wiersze wpisów wychodzą bajt w bajt takie same jak przed
    /// 05.09.2026. Zmieniła się wyłącznie linia komentarza z legendą, której
    /// <see cref="InputLog.Parse"/> nie czyta — i dlatego stary plik odtwarza się bez
    /// zmian, a bramka porównująca zapis z fixture'em nie ma się o co potknąć.
    /// </summary>
    [TestMethod]
    public void AddingTheEmergencyKeyDidNotMoveASingleByteOfOlderRuns()
    {
        var log = new InputLog(7200, new[]
        {
            new InputLogEntry(0, DriverKeys.Powering),
            new InputLogEntry(1800, DriverKeys.Coasting),
            new InputLogEntry(3600, DriverKeys.Braking),
        });

        var rows = log.ToText().Split('\n');
        CollectionAssert.AreEqual(
            new[] { "0;W", "1800;X", "3600;S" },
            rows.Where(row => row.Length > 0 && char.IsAsciiDigit(row[0])).ToArray());
        Assert.IsFalse(
            rows.Any(row => row.StartsWith("wersja=", StringComparison.Ordinal)
                && row != "wersja=1"),
            "wersja formatu nie miała się zmienić: zestaw znaków tylko urósł");
    }

    // --- odmowy -------------------------------------------------------------------

    [TestMethod]
    public void MissingStepCountIsRefused()
    {
        try
        {
            InputLog.Parse("wersja=1\nkrok;klawisze\n0;W\n");
        }
        catch (FormatException error)
        {
            StringAssert.Contains(error.Message, "kroki");
            return;
        }

        Assert.Fail("zapis bez liczby kroków został przyjęty — odtworzenie nie wiedziałoby, kiedy skończyć");
    }

    /// <summary>
    /// Do 05.09.2026 ten test sprawdzał, że `wersja=2` jest ODRZUCANA — bo wtedy druga
    /// wersja formatu nie istniała. Przepisany, a nie dopisany obok: wersja 2 jest dziś
    /// czytana, a odrzucana jest wersja, której program nie zna.
    /// </summary>
    [TestMethod]
    public void UnknownFormatVersionIsRefused()
    {
        try
        {
            InputLog.Parse("wersja=3\nkroki=5\nkrok;klawisze\n0;W\n");
        }
        catch (FormatException error)
        {
            StringAssert.Contains(error.Message, "wersji 3");
            return;
        }

        Assert.Fail("zapis w nieznanej wersji formatu został przyjęty");
    }

    /// <summary>
    /// Wersja ma zgadzać się z treścią W OBIE STRONY. Plik, który mówi o sobie co innego,
    /// niż zawiera, jest gorszy niż odrzucony, bo wygląda dokładnie tak samo jak poprawny.
    /// </summary>
    [TestMethod]
    public void VersionOneWithAResetRowIsRefused()
    {
        try
        {
            InputLog.Parse("wersja=1\nkroki=5\nkrok;klawisze\n0;W\n3;reset\n");
        }
        catch (FormatException error)
        {
            StringAssert.Contains(error.Message, "wersji 2");
            return;
        }

        Assert.Fail("zapis mówiący 'wersja=1' i zawierający reset został przyjęty");
    }

    [TestMethod]
    public void VersionTwoWithoutAnyResetRowIsRefused()
    {
        try
        {
            InputLog.Parse("wersja=2\nkroki=5\nkrok;klawisze\n0;W\n");
        }
        catch (FormatException error)
        {
            StringAssert.Contains(error.Message, "wersji 1");
            return;
        }

        Assert.Fail("zapis mówiący 'wersja=2' bez ani jednego resetu został przyjęty");
    }

    /// <summary>
    /// Zapis BEZ resetu wychodzi w wersji 1 — bajt w bajt tak, jak przed dopisaniem
    /// resetów. To nie jest kosmetyka: dwa wzorce bramek CI leżą w repozytorium
    /// w wersji 1 i porównuje się je `cmp`, więc podbicie wersji „na zapas" kazałoby
    /// je zmigrować i unieważniłoby wszystkie liczby, które opisują.
    /// </summary>
    [TestMethod]
    public void ALogWithoutResetsStaysInVersionOne()
    {
        var log = new InputLog(10, new[] { new InputLogEntry(0, DriverKeys.Powering) });

        Assert.AreEqual(InputLog.VersionWithoutResets, log.FormatVersion);
        StringAssert.Contains(log.ToText(), $"{InputLog.VersionField}={InputLog.VersionWithoutResets}\n");
        Assert.AreEqual(0, log.Resets.Count);
    }

    [TestMethod]
    public void ALogWithAResetIsVersionTwoAndSurvivesARoundTrip()
    {
        var log = new InputLog(
            10,
            new[] { new InputLogEntry(0, DriverKeys.Powering), new InputLogEntry(6, DriverKeys.Braking) },
            new[] { 4L, 8L });

        Assert.AreEqual(InputLog.VersionWithResets, log.FormatVersion);

        var again = InputLog.Parse(log.ToText());

        Assert.AreEqual(log.Steps, again.Steps);
        CollectionAssert.AreEqual(new List<long>(log.Resets), new List<long>(again.Resets));
        CollectionAssert.AreEqual(new List<InputLogEntry>(log.Entries), new List<InputLogEntry>(again.Entries));
        Assert.AreEqual(log.ToText(), again.ToText(), "zapis nie przetrwał obiegu tekst → zapis → tekst");
    }

    /// <summary>
    /// Reset jest ZDARZENIEM, nie stanem dźwigni: nie zmienia tego, co maszynista trzyma.
    /// Gdyby domykał stan klawiszy, zapis niósłby zmianę, której nie było.
    /// </summary>
    [TestMethod]
    public void AResetDoesNotChangeWhatTheDriverIsHolding()
    {
        var log = new InputLog(
            10,
            new[] { new InputLogEntry(0, DriverKeys.Powering) },
            new[] { 4L });

        Assert.AreEqual(DriverKeys.Powering, log.KeysAt(3));
        Assert.IsTrue(log.IsResetAt(4));
        Assert.AreEqual(DriverKeys.Powering, log.KeysAt(4));
        Assert.IsFalse(log.IsResetAt(3));
        Assert.IsFalse(log.IsResetAt(5));
    }

    /// <summary>
    /// Reset obowiązuje PRZED swoim krokiem, więc reset w kroku równym długości przejazdu
    /// nigdy by nie zadziałał — a zapis z zdarzeniem niewykonalnym wygląda tak samo jak
    /// zapis poprawny. Ten sam warunek, co dla wpisów klawiszy.
    /// </summary>
    [TestMethod]
    public void AResetPastTheEndOfTheRunIsRefused()
    {
        try
        {
            _ = new InputLog(10, Array.Empty<InputLogEntry>(), new[] { 10L });
        }
        catch (ArgumentException)
        {
            return;
        }

        Assert.Fail("reset za końcem przejazdu został przyjęty");
    }

    [TestMethod]
    public void ResetsMustIncrease()
    {
        try
        {
            _ = new InputLog(10, Array.Empty<InputLogEntry>(), new[] { 5L, 5L });
        }
        catch (ArgumentException)
        {
            return;
        }

        Assert.Fail("dwa resety w tym samym kroku zostały przyjęte");
    }

    [TestMethod]
    public void UnknownKeyCodeIsRefusedWithTheLineNumber()
    {
        try
        {
            InputLog.Parse("wersja=1\nkroki=5\nkrok;klawisze\n0;Q\n");
        }
        catch (FormatException error)
        {
            StringAssert.Contains(error.Message, "Wiersz 4");
            StringAssert.Contains(error.Message, "Q");
            return;
        }

        Assert.Fail("nieznany klawisz 'Q' został przyjęty");
    }

    [TestMethod]
    public void StepNumbersMustIncrease()
    {
        try
        {
            InputLog.Parse("wersja=1\nkroki=100\nkrok;klawisze\n50;W\n20;S\n");
        }
        catch (ArgumentException error)
        {
            StringAssert.Contains(error.Message, "rosnąć");
            return;
        }

        Assert.Fail("zapis z cofniętym numerem kroku został przyjęty");
    }

    [TestMethod]
    public void EntryBeyondTheRunIsRefused()
    {
        try
        {
            _ = new InputLog(100, new[] { new InputLogEntry(100, DriverKeys.Powering) });
        }
        catch (ArgumentException error)
        {
            StringAssert.Contains(error.Message, "nigdy by nie zadziałał");
            return;
        }

        Assert.Fail("wpis poza przejazdem został przyjęty");
    }

    // --- nagrywanie ---------------------------------------------------------------

    [TestMethod]
    public void RecorderKeepsOnlyChanges()
    {
        var recorder = new InputLogRecorder();
        for (var step = 0L; step < 100; step++)
        {
            recorder.Record(step, step < 60 ? DriverKeys.Powering : DriverKeys.Braking);
        }

        var log = recorder.Build();

        Assert.AreEqual(100L, log.Steps);
        Assert.AreEqual(2, log.Entries.Count);
        Assert.AreEqual(new InputLogEntry(0, DriverKeys.Powering), log.Entries[0]);
        Assert.AreEqual(new InputLogEntry(60, DriverKeys.Braking), log.Entries[1]);
    }

    [TestMethod]
    public void RecordedRunReadsBackStepForStep()
    {
        // Właściwość, na której stoi cały `--replay`: co nagrane, to odczytane,
        // dla KAŻDEGO kroku z osobna, a nie tylko dla punktów zmiany.
        var recorder = new InputLogRecorder();
        var expected = new DriverKeys[300];
        for (var step = 0; step < expected.Length; step++)
        {
            expected[step] = ((step / 37) % 3) switch
            {
                0 => DriverKeys.Powering,
                1 => DriverKeys.Braking,
                _ => DriverKeys.Coasting,
            };
            recorder.Record(step, expected[step]);
        }

        var log = InputLog.Parse(recorder.Build().ToText());

        for (var step = 0; step < expected.Length; step++)
        {
            Assert.AreEqual(expected[step], log.KeysAt(step), $"krok {step}");
        }
    }

    [TestMethod]
    public void RecorderRefusesAStepOutOfOrder()
    {
        // Wołanie z pętli KLATEK zamiast z pętli KROKÓW wygląda dokładnie tak.
        var recorder = new InputLogRecorder();
        recorder.Record(0, DriverKeys.Powering);

        try
        {
            recorder.Record(2, DriverKeys.Powering);
        }
        catch (ArgumentOutOfRangeException)
        {
            Assert.AreEqual(1L, recorder.NextStep);
            return;
        }

        Assert.Fail("zapis przyjął krok z luką — opisywałby inny przejazd niż ten, który się odbył");
    }

    /// <summary>
    /// Do 05.09.2026 stał tu <c>ClearStartsTheRecordingOver</c>: reset KASOWAŁ zapis, bo
    /// licznik kroków przejazdu wracał do zera i dalsze nagrywanie nadpisywałoby numery,
    /// które już padły. Test jest przepisany, a nie dopisany obok, bo jego twierdzenie
    /// przestało być prawdziwe: decyzja właściciela (wariant W1) rozdzieliła numer kroku
    /// SESJI od numeru kroku PRZEJAZDU, więc zapis idzie dalej i niesie reset jako wpis.
    /// </summary>
    [TestMethod]
    public void ResetIsRecordedAndTheStepCounterDoesNotGoBack()
    {
        var recorder = new InputLogRecorder();
        recorder.Record(0, DriverKeys.Powering);
        recorder.Record(1, DriverKeys.Powering);

        recorder.RecordReset();

        Assert.AreEqual(2L, recorder.NextStep, "numer kroku sesji cofnął się po resecie");
        Assert.AreEqual(1, recorder.ResetCount);

        recorder.Record(2, DriverKeys.Coasting);

        var log = recorder.Build();
        Assert.AreEqual(3L, log.Steps);
        CollectionAssert.AreEqual(new List<long> { 2L }, new List<long>(log.Resets));
        Assert.AreEqual(DriverKeys.Powering, log.KeysAt(1));
        Assert.IsTrue(log.IsResetAt(2));
        Assert.AreEqual(DriverKeys.Coasting, log.KeysAt(2));
        Assert.AreEqual(InputLog.VersionWithResets, log.FormatVersion);
    }
}
