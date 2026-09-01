using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Reflection;
using System.Threading;
using MetroBxl.Sim.Physics;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace MetroBxl.Sim.Tests;

/// <summary>
/// Determinizm z <c>docs/01-architecture.md</c>: ten sam scenariusz ma dać ten sam
/// wynik, bit w bit, niezależnie od maszyny i od kolejności wywołań. „Prawie ten sam"
/// wynik znaczy, że zapisu przejazdu nie da się odtworzyć, a to wywraca cały pomysł
/// na powtórki i testy regresji.
/// </summary>
[TestClass]
public sealed class DeterminismTests
{
    private static readonly VehicleModel Model = VehicleModel.M7;

    [TestMethod]
    public void Dwa_przebiegi_tego_samego_scenariusza_sa_identyczne_co_do_bitu()
    {
        var conditions = RunConditions.Level(Model, TrainLoad.Aw2).WithGrade(1.5);

        var first = AccelerationRun.M7.ToSpeed(conditions, 72.0, FixedStep.Simulation, sampleEverySteps: 60);
        var second = AccelerationRun.M7.ToSpeed(conditions, 72.0, FixedStep.Simulation, sampleEverySteps: 60);

        AssertSameBits(first.DistanceM, second.DistanceM, "droga");
        AssertSameBits(first.FinalSpeedMps, second.FinalSpeedMps, "prędkość końcowa");
        AssertSameBits(first.TimeSeconds, second.TimeSeconds, "czas");
        Assert.AreEqual(first.Steps, second.Steps, "liczba kroków");

        Assert.AreEqual(first.Profile.Samples.Count, second.Profile.Samples.Count);
        for (var i = 0; i < first.Profile.Samples.Count; i++)
        {
            AssertSameBits(first.Profile.Samples[i].SpeedMps, second.Profile.Samples[i].SpeedMps, $"v[{i}]");
            AssertSameBits(first.Profile.Samples[i].DistanceM, second.Profile.Samples[i].DistanceM, $"s[{i}]");
        }

        var firstEnergy = first.Energy!.Value;
        var secondEnergy = second.Energy!.Value;
        AssertSameBits(firstEnergy.TractionWorkJ, secondEnergy.TractionWorkJ, "praca trakcji");
    }

    /// <summary>
    /// Kolejność wykonania innych przebiegów nie może wpłynąć na wynik. Gdyby rdzeń
    /// trzymał gdzieś stan między wywołaniami, ten test by to pokazał.
    /// </summary>
    [TestMethod]
    public void Wynik_nie_zalezy_od_tego_co_liczono_wczesniej()
    {
        var conditions = RunConditions.Level(Model, TrainLoad.Aw0);
        var clean = AccelerationRun.M7.ToSpeed(conditions, 80.0);

        _ = AccelerationRun.M7.ToSpeed(conditions.WithGrade(-2.0), 40.0, sampleEverySteps: 7);
        _ = ServiceBrakingRun.M7.ToStop(55.0, sampleEverySteps: 3);
        _ = AccelerationRun.M7.ToSpeed(conditions.WithAdhesion(0.13), 30.0);

        var afterwards = AccelerationRun.M7.ToSpeed(conditions, 80.0);

        AssertSameBits(clean.DistanceM, afterwards.DistanceM, "droga");
        Assert.AreEqual(clean.Steps, afterwards.Steps);
    }

    /// <summary>Ten sam przebieg policzony równolegle w kilku wątkach musi dać tę samą liczbę.</summary>
    [TestMethod]
    public void Przebieg_liczony_rownolegle_daje_te_same_bity()
    {
        var conditions = RunConditions.Level(Model, TrainLoad.Aw2);
        var expected = AccelerationRun.M7.ToSpeed(conditions, 80.0).DistanceM;
        var results = new double[8];

        var threads = new List<Thread>();
        for (var i = 0; i < results.Length; i++)
        {
            var index = i;
            var thread = new Thread(() => results[index] = AccelerationRun.M7.ToSpeed(conditions, 80.0).DistanceM);
            threads.Add(thread);
            thread.Start();
        }

        foreach (var thread in threads)
        {
            thread.Join();
        }

        foreach (var value in results)
        {
            AssertSameBits(expected, value, "droga z wątku");
        }
    }

    /// <summary>
    /// Rejestr wystawia ścieżki w ustalonym porządku, nie w kolejności iteracji po
    /// słowniku. Bez tego raport parametrów potrafiłby wyglądać inaczej po każdym
    /// uruchomieniu, a diff przestałby cokolwiek znaczyć.
    /// </summary>
    [TestMethod]
    public void Kolejnosc_parametrow_rejestru_jest_ustalona()
    {
        var paths = VehicleRegistry.M7.Paths;
        var sorted = paths.OrderBy(p => p, StringComparer.Ordinal).ToList();

        CollectionAssert.AreEqual(sorted, paths.ToList());
        CollectionAssert.AreEqual(
            VehicleRegistry.M7.Paths.ToList(),
            VehicleRegistry.M7.Paths.ToList());
    }

    /// <summary>
    /// <c>CLAUDE.md</c> reguła 9: nic w <c>src/Sim/</c> nie importuje Godota. Reflektowana
    /// lista referencji assembly jest mocniejszym dowodem niż grep po źródłach, bo
    /// wykryje też zależność wciągniętą pośrednio.
    /// </summary>
    [TestMethod]
    public void Rdzen_nie_ma_zadnej_referencji_do_silnika()
    {
        var core = typeof(VehicleModel).Assembly;
        var referenced = core.GetReferencedAssemblies().Select(a => a.Name ?? string.Empty).ToList();

        foreach (var name in referenced)
        {
            Assert.IsFalse(
                name.Contains("Godot", StringComparison.OrdinalIgnoreCase),
                $"rdzeń odwołuje się do {name}");
        }

        // Poza silnikiem: rdzeń nie ma też żadnego pakietu NuGet — same biblioteki platformy.
        var allowedPrefixes = new[] { "System", "netstandard", "Microsoft.CSharp", "mscorlib" };
        foreach (var name in referenced)
        {
            Assert.IsTrue(
                allowedPrefixes.Any(prefix => name.StartsWith(prefix, StringComparison.Ordinal)),
                $"nieoczekiwana zależność rdzenia: {name}");
        }
    }

    private static void AssertSameBits(double expected, double actual, string label) =>
        Assert.AreEqual(
            BitConverter.DoubleToInt64Bits(expected),
            BitConverter.DoubleToInt64Bits(actual),
            string.Create(CultureInfo.InvariantCulture, $"{label}: {expected:R} vs {actual:R}"));
}
