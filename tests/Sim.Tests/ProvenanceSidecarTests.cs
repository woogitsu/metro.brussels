using System;
using System.IO;
using System.Linq;
using MetroBxl.Sim.Train;
using MetroBxl.Sim.Runner;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace MetroBxl.Sim.Tests;

/// <summary>
/// Nastawy przebiegu w pliku OBOK — pozycja 6.A21. Trzy pisarze
/// (<c>drive</c>, <c>replay</c>, <c>line</c>) mają format przybity z zewnątrz, więc
/// nastawy nie mogą wejść DO pliku; wchodzą do pliku obok.
///
/// <para><b>Dlaczego to jest test C#, a nie tylko bramka czytająca <c>Program.cs</c>.</b>
/// Bramka <c>tools/tests/test_csv_provenance.py</c> czyta źródło jako TEKST i pilnuje
/// kształtu: że pomocnik istnieje, że składa treść przez <c>Provenance</c> i że plik
/// nastaw wskazuje tę samą ścieżkę, co plik wyniku. Żadna z tych asercji nie uruchamia
/// runnera, więc żadna nie odpowiada na pytanie, czy plik wyniku po tej zmianie NADAL
/// jest tym, czego żąda <c>Compare</c>. Tu wchodzi się przez
/// <see cref="Program.Main"/> — tą samą drogą, którą idzie CI — i patrzy na bajty
/// na dysku.</para>
///
/// <para><b>Dlaczego nie przez pomocnik z <c>RunnerCommandTests</c>.</b> Tamten
/// zwraca oba strumienie, bo tam PRZEDMIOTEM pomiaru jest wypis. Tutaj przedmiotem są
/// pliki, a strumienie tylko przeszkadzają — kopia harnessu po to, żeby wyrzucić jego
/// wynik, byłaby kopią bez powodu.</para>
/// </summary>
[TestClass]
public sealed class ProvenanceSidecarTests
{
    /// <summary>
    /// Katalog repozytorium — ten sam sposób, co w <c>BrakingTests</c>,
    /// <c>CabProtectionTests</c> i trzech innych plikach: w górę po
    /// <c>CLAUDE.md</c>. Host testów ma katalog roboczy w <c>bin/</c>, więc
    /// ścieżka względna z treści polecenia CI nie rozwiązuje się tutaj.
    /// </summary>
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

    private static string NewDirectory()
    {
        var path = Path.Combine(Path.GetTempPath(), "mbxl-6a21-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(path);
        return path;
    }

    /// <summary>Wołanie runnera z wypisem w kosz — mierzymy pliki, nie strumienie.</summary>
    private static int RunQuiet(params string[] args)
    {
        var originalOut = Console.Out;
        Console.SetOut(TextWriter.Null);
        try
        {
            return Program.Main(args);
        }
        finally
        {
            Console.SetOut(originalOut);
        }
    }

    [TestMethod]
    public void DriveTelemetryKeepsThePinnedHeaderAndGetsSettingsBeside()
    {
        var directory = NewDirectory();
        var csv = Path.Combine(directory, "drive.csv");
        Assert.AreEqual(0, RunQuiet("drive", "--out", csv), "drive --out nie skończyło się zerem");

        var rows = File.ReadAllLines(csv);
        // WARUNEK, KTÓREGO ŻĄDA `Compare`: pierwszy wiersz DOKŁADNIE nagłówek. To jest
        // powód, dla którego nastawy nie mogły wejść do tego pliku (6.A20, 6.A21).
        Assert.AreEqual(DriveTelemetry.Header, rows[0],
            "pierwszy wiersz telemetrii przestał być nagłówkiem — `Compare` odrzuci ten plik, "
            + "a `godot-first-run.yml` porównuje go z plikiem SCENY przy --tolerance 0");
        // DRUGI KIERUNEK: ani jednego wiersza `#` w pliku wyniku. Bez tej asercji test
        // byłby zielony także wtedy, gdyby ktoś wkleił nastawy do środka pliku.
        Assert.IsFalse(rows.Any(r => r.StartsWith("#", StringComparison.Ordinal)),
            "plik telemetrii nosi wiersz komentarza — format przybity z zewnątrz nie ma na to miejsca");

        var beside = Program.ProvenancePathFor(csv);
        Assert.IsTrue(File.Exists(beside), "nie ma pliku nastaw obok telemetrii: " + beside);
        var settings = File.ReadAllLines(beside);
        Assert.AreEqual("# polecenie: drive", settings[0], string.Join("\n", settings));
        Assert.IsTrue(settings.All(r => r.StartsWith("# ", StringComparison.Ordinal)),
            "plik nastaw ma wiersz, który nie jest komentarzem: " + string.Join("\n", settings));
        Assert.IsTrue(settings.Any(r => r.StartsWith("# scenario: ", StringComparison.Ordinal)),
            "nastawy nie nazywają scenariusza, czyli nie mówią, CO zostało zmierzone: "
            + string.Join("\n", settings));
        Directory.Delete(directory, recursive: true);
    }

    [TestMethod]
    public void CompareStillAcceptsATelemetryFileWrittenWithSettingsBeside()
    {
        // Najmocniejszy dowód, że format nie został tknięty: KONSUMENT go przyjmuje.
        // `--tolerance 0` to ten sam próg, którym `godot-first-run.yml` porównuje
        // przejazd rdzenia z przejazdem sceny.
        var directory = NewDirectory();
        var first = Path.Combine(directory, "a.csv");
        var second = Path.Combine(directory, "b.csv");
        Assert.AreEqual(0, RunQuiet("drive", "--out", first));
        Assert.AreEqual(0, RunQuiet("drive", "--out", second));
        Assert.AreEqual(0, RunQuiet("compare", first, second, "--tolerance", "0"),
            "compare przy progu 0 odrzuciło dwa przebiegi tego samego scenariusza");
        Directory.Delete(directory, recursive: true);
    }

    [TestMethod]
    public void LineWritesSettingsBesideBothItsFilesAndNamesTheAxisInEach()
    {
        var directory = NewDirectory();
        var trace = Path.Combine(directory, "trace.csv");
        var calls = Path.Combine(directory, "calls.csv");
        Assert.AreEqual(0, RunQuiet(
            "line", "--axis", Path.Combine(RepoRoot(), "data", "track", "L1_A.json"),
            "--limit-kmh", "72", "--exchange-s", "20",
            "--trace", trace, "--calls", calls));

        foreach (var (path, command) in new[] { (trace, "line --trace"), (calls, "line --calls") })
        {
            var beside = Program.ProvenancePathFor(path);
            Assert.IsTrue(File.Exists(beside), "nie ma pliku nastaw obok " + path);
            var settings = File.ReadAllLines(beside);
            Assert.AreEqual("# polecenie: " + command, settings[0], string.Join("\n", settings));
            Assert.IsTrue(
                settings.Contains("# axis: " + Path.Combine(RepoRoot(), "data", "track", "L1_A.json")),
                "nastawy nie nazywają osi przejazdu: " + string.Join("\n", settings));
            Assert.IsFalse(
                File.ReadAllLines(path).Any(r => r.StartsWith("#", StringComparison.Ordinal)),
                "plik " + path + " nosi wiersz komentarza, a jego format jest przybity");
        }

        // Dwa pliki nastaw, nie jeden na dwa przebiegi — i każdy o SWOIM pliku.
        Assert.AreNotEqual(Program.ProvenancePathFor(trace), Program.ProvenancePathFor(calls));
        Directory.Delete(directory, recursive: true);
    }
}
