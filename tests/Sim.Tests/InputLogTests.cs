using System;
using System.Collections.Generic;
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
        var both = new DriverKeys(Power: true, Brake: true, Coast: false);
        var log = new InputLog(5, new[] { new InputLogEntry(0, both) });

        var again = InputLog.Parse(log.ToText());

        Assert.AreEqual("WS", both.Code());
        Assert.AreEqual(both, again.KeysAt(0));
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

    [TestMethod]
    public void UnknownFormatVersionIsRefused()
    {
        try
        {
            InputLog.Parse("wersja=2\nkroki=5\nkrok;klawisze\n0;W\n");
        }
        catch (FormatException error)
        {
            StringAssert.Contains(error.Message, "wersji 2");
            return;
        }

        Assert.Fail("zapis w nieznanej wersji formatu został przyjęty");
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

    [TestMethod]
    public void ClearStartsTheRecordingOver()
    {
        var recorder = new InputLogRecorder();
        recorder.Record(0, DriverKeys.Powering);
        recorder.Record(1, DriverKeys.Braking);

        recorder.Clear();
        recorder.Record(0, DriverKeys.Coasting);

        var log = recorder.Build();
        Assert.AreEqual(1L, log.Steps);
        Assert.AreEqual(1, log.Entries.Count);
        Assert.AreEqual(DriverKeys.Coasting, log.KeysAt(0));
    }
}
