using System;
using System.IO;
using MetroBxl.Sim.Runner;
using MetroBxl.Sim.Train;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace MetroBxl.Sim.Tests;

[TestClass]
public sealed class ScheduledReplayRunnerTests
{
    private static (int ExitCode, string StdOut, string StdErr) Run(params string[] args)
    {
        var originalOut = Console.Out;
        var originalError = Console.Error;
        using var stdout = new StringWriter();
        using var stderr = new StringWriter();
        Console.SetOut(stdout);
        Console.SetError(stderr);
        try
        {
            var exitCode = Program.Main(args);
            return (exitCode, stdout.ToString(), stderr.ToString());
        }
        finally
        {
            Console.SetOut(originalOut);
            Console.SetError(originalError);
        }
    }

    private static string[] ReplayArgs(string keys, string schedule, string output) =>
    [
        "replay", "--line", "--atp", "--keys", keys,
        "--axis", Path.Combine(MetroBxl.Tests.Shared.KorzenRepozytorium.Sciezka,
            "data", "track", "L1_A.json"),
        "--signalling", Path.Combine(MetroBxl.Tests.Shared.KorzenRepozytorium.Sciezka,
            "data", "design", "signalling", "classic-2026.json"),
        "--limit-kmh", "70", "--scheduled-entries", schedule, "--out", output,
    ];

    private static void WriteInputs(string directory, long steps, long firstSecond,
        long secondSecond, out string keys, out string schedule, out string output)
    {
        Directory.CreateDirectory(directory);
        keys = Path.Combine(directory, "keys.log");
        schedule = Path.Combine(directory, "entries.json");
        output = Path.Combine(directory, "telemetry.csv");
        File.WriteAllText(keys, new InputLog(steps, Array.Empty<InputLogEntry>()).ToText());
        File.WriteAllText(schedule,
            "{\"axis_id\":\"L1_A\",\"date\":\"20260902\",\"source_gtfs_sha256\":\"test\",\"runs\":["
            + $"{{\"trip_id\":\"west\",\"block_id\":\"block-west\",\"first_stop_id\":\"8733\",\"release_s\":{firstSecond}}},"
            + $"{{\"trip_id\":\"beek\",\"block_id\":\"block-beek\",\"first_stop_id\":\"8742\",\"release_s\":{secondSecond}}}"
            + "]}");
    }

    [TestMethod]
    public void Delayed_first_entry_keeps_the_clock_alive_without_an_observed_train()
    {
        var directory = Path.Combine(Path.GetTempPath(), "metro-scheduled-replay-" + Guid.NewGuid().ToString("N"));
        try
        {
            WriteInputs(directory, 240, 10, 20, out var keys, out var schedule, out var output);
            var result = Run(ReplayArgs(keys, schedule, output));
            Assert.AreEqual(0, result.ExitCode, "czekanie na pierwszy kurs ma kończyć się bez błędu");
            StringAssert.Contains(result.StdOut, "sesja=240 kroków", "zegar musi czekać na pierwszy kurs");
            StringAssert.Contains(result.StdOut, "obserwowany=brak", "przed wjazdem nie ma składu");
            StringAssert.Contains(result.StdOut, "zarejestrowane wjazdy: 0", "kurs nie może wejść przed terminem");
            CollectionAssert.AreEqual(new[] { DriveTelemetry.Header }, File.ReadAllLines(output),
                "bez składu nie ma próbek telemetrii");
            StringAssert.Contains(File.ReadAllText(output + ".provenance.txt"),
                "# scheduled_entries_sha256: ", "plik nastaw musi identyfikować plan");
        }
        finally
        {
            if (Directory.Exists(directory)) Directory.Delete(directory, recursive: true);
        }
    }

    [TestMethod]
    public void Future_entry_is_registered_at_its_step_after_the_first_train()
    {
        var directory = Path.Combine(Path.GetTempPath(), "metro-scheduled-replay-" + Guid.NewGuid().ToString("N"));
        try
        {
            WriteInputs(directory, 125, 0, 1, out var keys, out var schedule, out var output);
            var result = Run(ReplayArgs(keys, schedule, output));
            Assert.AreEqual(0, result.ExitCode, "dwa kursy mają wejść bez błędu");
            StringAssert.Contains(result.StdOut, "zarejestrowane wjazdy: 2",
                "drugi kurs ma wejść dopiero po swoim terminie");
            Assert.IsTrue(File.ReadAllLines(output).Length > 1,
                "pierwszy kurs powinien dać próbkę telemetrii");
        }
        finally
        {
            if (Directory.Exists(directory)) Directory.Delete(directory, recursive: true);
        }
    }

    [TestMethod]
    public void Scheduled_entries_reject_non_line_and_automatic_train_count()
    {
        var directory = Path.Combine(Path.GetTempPath(), "metro-scheduled-replay-" + Guid.NewGuid().ToString("N"));
        try
        {
            WriteInputs(directory, 1, 0, 1, out var keys, out var schedule, out var output);
            var args = ReplayArgs(keys, schedule, output);
            var withoutLine = Array.FindAll(args, item => item != "--line");
            var refused = Run(withoutLine);
            Assert.AreEqual(1, refused.ExitCode, "plan bez trybu linii musi być odmową");
            StringAssert.Contains(refused.StdErr, "wymaga --line", "odmowa ma podać brakujący tryb");

            var withCount = new string[args.Length + 2];
            Array.Copy(args, withCount, args.Length);
            withCount[^2] = "--trains";
            withCount[^1] = "2";
            refused = Run(withCount);
            Assert.AreEqual(1, refused.ExitCode, "plan i automatyczna liczba składów są sprzeczne");
            StringAssert.Contains(refused.StdErr, "nie łączy się z --trains",
                "odmowa ma nazwać sprzeczną opcję");

            withCount[^2] = "--headway-steps";
            withCount[^1] = "120";
            refused = Run(withCount);
            Assert.AreEqual(1, refused.ExitCode, "plan i automatyczny odstęp składów są sprzeczne");
            StringAssert.Contains(refused.StdErr, "--headway-steps",
                "odmowa ma nazwać odstęp niezależny od rozkładu");
        }
        finally
        {
            if (Directory.Exists(directory)) Directory.Delete(directory, recursive: true);
        }
    }
}
