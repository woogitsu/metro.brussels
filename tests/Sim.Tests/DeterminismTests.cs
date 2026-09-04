using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Text.Json;
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
    ///
    /// <para>Ten test jest PRZEPISANY, nie dopisany obok, i warto powiedzieć dlaczego.
    /// Kończył się porównaniem <c>CollectionAssert.AreEqual(VehicleRegistry.M7.Paths
    /// .ToList(), VehicleRegistry.M7.Paths.ToList())</c> — czyli tej samej, raz
    /// posortowanej i zapamiętanej w konstruktorze listy z SOBĄ SAMĄ. Takie
    /// porównanie nie może się nie udać i nie mierzy niczego.</para>
    ///
    /// <para>Zmierzone 04.09.2026, dwie mutacje w <c>VehicleRegistry</c>, każda
    /// przechodziła cały zestaw 331/331:</para>
    /// <list type="bullet">
    /// <item><c>PathsWithStatus</c> iterujące po <c>_entries.Keys</c>, czyli po
    /// kolejności SŁOWNIKA — dokładnie po tym, czego nazwa tego testu zabrania.</item>
    /// <item><c>sourceIds.Sort(StringComparer.Ordinal)</c> zamienione na
    /// <c>Reverse()</c>, wbrew temu, co obiecuje dokumentacja <c>SourceIds</c>.</item>
    /// </list>
    ///
    /// <para>Dlatego każda deklarowana kolejność ma teraz NIEZALEŻNY punkt
    /// odniesienia, a nie samą siebie.</para>
    /// </summary>
    [TestMethod]
    public void Kolejnosc_parametrow_rejestru_jest_ustalona()
    {
        var registry = VehicleRegistry.M7;
        var paths = registry.Paths.ToList();

        // 1. Porządek jest ordinalny, a nie „jakiś stały".
        CollectionAssert.AreEqual(
            paths.OrderBy(p => p, StringComparer.Ordinal).ToList(),
            paths,
            "Paths nie jest w porządku ordinalnym");

        // 2. Odniesienie z DRUGIEJ STRONY: ten sam osadzony JSON, czytany tu jeszcze
        //    raz. Porównanie z sobą samą nie odróżniało listy pełnej od takiej, która
        //    zgubiła wpis — ta asercja odróżnia.
        using var document = JsonDocument.Parse(VehicleRegistry.ReadEmbeddedJson());
        var fromJson = new List<string>();
        foreach (var section in new[] { "parameters", "reference_model" })
        {
            foreach (var property in document.RootElement.GetProperty(section).EnumerateObject())
            {
                fromJson.Add(section + "." + property.Name);
            }
        }

        CollectionAssert.AreEqual(
            fromJson.OrderBy(p => p, StringComparer.Ordinal).ToList(),
            paths,
            "Paths nie zgadza się ze zbiorem kluczy osadzonego rejestru");

        // Pułapka na samą tę bramkę. Gdyby klucze w `m7-spec.json` stały JUŻ w porządku
        // ordinalnym, warunek 1 przechodziłby także z wyrzuconym `paths.Sort(...)`
        // i przestałby cokolwiek mierzyć — utajona luka, ta sama rodzina co
        // `next(iter(document["jobs"]))` w bramkach CI. Ta asercja mówi to wprost,
        // zamiast pozwolić bramce ucichnąć.
        CollectionAssert.AreNotEqual(
            fromJson,
            paths,
            "kolejność kluczy w m7-spec.json zrównała się z porządkiem ordinalnym — "
            + "sortowanie w VehicleRegistry przestało być tym testem mierzalne");

        // 3. Widok pochodny trzyma TĘ SAMĄ kolejność. `PathsWithStatus` obiecuje ją
        //    w dokumentacji, jest jedynym wyjściem, którego używa `DesignModelAuditTests`,
        //    i jedynym, które mutacja mogła cofnąć do kolejności słownika.
        var covered = 0;
        foreach (var status in Enum.GetValues<ParameterStatus>())
        {
            var subset = registry.PathsWithStatus(status).ToList();
            CollectionAssert.AreEqual(
                subset.OrderBy(p => p, StringComparer.Ordinal).ToList(),
                subset,
                $"PathsWithStatus({status}) nie jest w porządku ordinalnym");
            // Podciąg, nie tylko posortowany zbiór: kolejność ma być kolejnością `Paths`.
            CollectionAssert.AreEqual(
                paths.Where(subset.Contains).ToList(),
                subset,
                $"PathsWithStatus({status}) nie jest podciągiem Paths");
            covered += subset.Count;
        }

        // Licznik, żeby pętla po statusach nie przeszła pusta i zielona.
        Assert.AreEqual(paths.Count, covered, "statusy nie pokrywają wszystkich wpisów");

        // 4. `SourceIds` deklaruje porządek ordinalny w tym samym pliku i nie miał
        //    dotąd ani jednej bramki — mutacja `Reverse()` przechodziła cały zestaw.
        var sources = registry.SourceIds.ToList();
        CollectionAssert.AreEqual(
            sources.OrderBy(s => s, StringComparer.Ordinal).ToList(),
            sources,
            "SourceIds nie jest w porządku ordinalnym");
        Assert.IsTrue(sources.Count >= 2, $"rejestr podaje tylko {sources.Count} źródeł");
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

    /// <summary>
    /// Reguła 9 dotyczy ZALEŻNOŚCI, nie samego użycia typu.
    ///
    /// <see cref="Assembly.GetReferencedAssemblies"/> wypisuje wyłącznie assembly,
    /// z których rdzeń faktycznie używa typów — kompilator wycina z manifestu
    /// referencję, po której nikt nic nie woła. Dodanie do <c>Sim.csproj</c>
    /// <c>ProjectReference</c> do projektu Godota (bez ani jednego <c>using</c>)
    /// przechodziłoby więc przez test wyżej, a <c>Godot.dll</c> i tak lądowałoby
    /// obok rdzenia w katalogu wyjściowym i w grafie zależności. Zmierzone
    /// 02.09.2026 na osobnej bibliotece podpiętej do rdzenia: test wyżej zielony,
    /// plik w katalogu wyjściowym.
    ///
    /// Ten test patrzy więc na to, co realnie leży obok rdzenia i co deklaruje
    /// graf zależności, a nie na to, czego kod używa.
    /// </summary>
    [TestMethod]
    public void Rdzen_nie_wciaga_zadnego_pliku_silnika_do_katalogu_wyjsciowego()
    {
        var core = typeof(VehicleModel).Assembly;
        var directory = Path.GetDirectoryName(core.Location)
            ?? throw new InvalidOperationException("rdzeń nie ma ścieżki na dysku");

        foreach (var file in Directory.GetFiles(directory, "*Godot*", SearchOption.AllDirectories))
        {
            Assert.Fail($"obok rdzenia leży plik silnika: {Path.GetFileName(file)}");
        }

        // Graf zależności z deps.json: pozycja rdzenia nie może zależeć od niczego
        // spoza platformy. To łapie ProjectReference bez użycia typu.
        var depsPath = Path.Combine(directory, "MetroBxl.Sim.Tests.deps.json");
        Assert.IsTrue(File.Exists(depsPath), $"brak {depsPath} — test nie ma czego sprawdzić");
        using var deps = JsonDocument.Parse(File.ReadAllText(depsPath));
        var allowed = new[] { "System", "netstandard", "Microsoft.CSharp", "mscorlib" };
        var found = 0;
        foreach (var target in deps.RootElement.GetProperty("targets").EnumerateObject())
        {
            foreach (var library in target.Value.EnumerateObject())
            {
                if (!library.Name.StartsWith("MetroBxl.Sim/", StringComparison.Ordinal))
                {
                    continue;
                }

                found++;
                if (!library.Value.TryGetProperty("dependencies", out var dependencies))
                {
                    continue;
                }

                foreach (var dependency in dependencies.EnumerateObject())
                {
                    Assert.IsTrue(
                        allowed.Any(prefix => dependency.Name.StartsWith(prefix, StringComparison.Ordinal)),
                        $"rdzeń wciąga zależność {dependency.Name} — CLAUDE.md reguła 9");
                }
            }
        }

        Assert.IsTrue(found > 0, "w deps.json nie ma pozycji MetroBxl.Sim — wzorzec przestał pasować");
    }

    private static void AssertSameBits(double expected, double actual, string label) =>
        Assert.AreEqual(
            BitConverter.DoubleToInt64Bits(expected),
            BitConverter.DoubleToInt64Bits(actual),
            string.Create(CultureInfo.InvariantCulture, $"{label}: {expected:R} vs {actual:R}"));
}
