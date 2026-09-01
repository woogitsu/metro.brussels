using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using MetroBxl.Sim.Physics;
using MetroBxl.Sim.Train;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace MetroBxl.Sim.Tests;

/// <summary>
/// Testy przejazdu po zapisanym scenariuszu.
///
/// Porównanie Godota z rdzeniem w CI pokazuje, że **ten sam kod w dwóch gospodarzach**
/// daje ten sam wynik. Tutaj jest to, co trzeba wiedzieć, żeby tamto porównanie w ogóle
/// coś znaczyło: że stan po N krokach nie zależy od tego, jak kroki rozłożyły się na
/// partie, i że dwa przebiegi tego samego scenariusza są identyczne co do bitu.
/// </summary>
[TestClass]
public sealed class ScenarioDriveTests
{
    private static readonly VehicleModel Model = VehicleModel.M7;
    private static readonly FixedStep Step = FixedStep.Simulation;

    private static RunConditions Conditions => new(
        Model.MassKg(TrainLoad.Aw2), 0.0, Model.Adhesion(RailCondition.Dry), TrackEnvironment.Tunnel);

    private static ScenarioDrive NewDrive() =>
        new(Model, DriveScenario.PackageAFirstRun(Model), Conditions, Step);

    /// <summary>Dwa przebiegi tego samego scenariusza są identyczne co do bitu.</summary>
    [TestMethod]
    public void Przejazd_jest_powtarzalny_co_do_bitu()
    {
        var first = NewDrive();
        var second = NewDrive();
        first.RunToEnd();
        second.RunToEnd();

        Assert.AreEqual(first.State.Steps, second.State.Steps);
        Assert.AreEqual(
            BitConverter.DoubleToInt64Bits(first.State.DistanceM),
            BitConverter.DoubleToInt64Bits(second.State.DistanceM));
        Assert.AreEqual(
            BitConverter.DoubleToInt64Bits(first.State.SpeedMps),
            BitConverter.DoubleToInt64Bits(second.State.SpeedMps));
        Assert.AreEqual(first.FinishReason, second.FinishReason);
    }

    /// <summary>
    /// **Sedno determinizmu krokowego.** Ten sam przejazd wykonany w jednej pętli i
    /// w nierównych partiach (37, 1, 500, 13 kroków...) musi dać identyczny stan po
    /// każdej liczbie kroków. To jest ta sama własność, którą w Godocie sprawdza
    /// przebieg z nierównym czasem klatki — tyle że tutaj bez silnika.
    /// </summary>
    [TestMethod]
    public void Podzial_krokow_na_nierowne_partie_nie_zmienia_stanu()
    {
        var straight = NewDrive();
        var batched = NewDrive();

        var batches = new[] { 37, 1, 500, 13, 2, 977, 120 };
        var index = 0;
        var checkpoints = 0;

        while (!straight.Finished)
        {
            var batch = batches[index++ % batches.Length];
            for (var i = 0; i < batch && !straight.Finished; i++)
            {
                straight.Step();
            }

            while (batched.State.Steps < straight.State.Steps && batched.Step())
            {
                // dogonienie w partiach o innym podziale
            }

            Assert.AreEqual(straight.State.Steps, batched.State.Steps);
            Assert.AreEqual(
                BitConverter.DoubleToInt64Bits(straight.State.DistanceM),
                BitConverter.DoubleToInt64Bits(batched.State.DistanceM),
                $"rozjazd drogi po {straight.State.Steps} krokach");
            Assert.AreEqual(
                BitConverter.DoubleToInt64Bits(straight.State.BrakeRateMps2),
                BitConverter.DoubleToInt64Bits(batched.State.BrakeRateMps2),
                $"rozjazd hamulca po {straight.State.Steps} krokach");
            checkpoints++;
        }

        Assert.IsTrue(checkpoints > 100, $"za mało punktów porównania: {checkpoints}");
    }

    /// <summary>Przejazd pakietu A kończy się zatrzymaniem przed końcem osi, a nie limitem pętli.</summary>
    [TestMethod]
    public void Przejazd_pakietu_A_konczy_sie_zatrzymaniem_przed_koncem_osi()
    {
        var drive = NewDrive();
        drive.RunToEnd();

        Console.WriteLine(string.Create(
            CultureInfo.InvariantCulture,
            $"[PRZEJAZD] kroków {drive.State.Steps}, t {drive.State.TimeSeconds(Step):F3} s, " +
            $"chainage {drive.ChainageM:F3} m, powód {drive.FinishReason}"));

        Assert.AreEqual("stopped", drive.FinishReason);
        Assert.AreEqual(0.0, drive.State.SpeedMps, 0.0);
        Assert.AreEqual("brake", drive.Phase);
        Assert.IsTrue(drive.ChainageM < 6686.739,
            $"czoło stanęło za końcem osi: {drive.ChainageM}");
        Assert.IsTrue(drive.ChainageM > 6600.0,
            $"czoło stanęło zbyt wcześnie: {drive.ChainageM}");
    }

    /// <summary>Po zakończeniu przejazdu kolejne kroki nic nie zmieniają — wołanie w pętli klatkowej jest bezpieczne.</summary>
    [TestMethod]
    public void Po_zakonczeniu_kolejne_kroki_nic_nie_zmieniaja()
    {
        var drive = NewDrive();
        drive.RunToEnd();
        var final = drive.State;

        Assert.IsFalse(drive.Step());
        Assert.AreEqual(final, drive.State);
    }

    /// <summary>Bezpiecznik pętli ma zadziałać, gdy przejazd nie potrafi się zatrzymać.</summary>
    [TestMethod]
    public void Bezpiecznik_petli_konczy_przejazd_ktory_utknal()
    {
        // Scenariusz bez fazy hamowania: skład jedzie i nigdy nie stanie.
        var scenario = new DriveScenario(
            "bez-hamowania",
            0.0,
            Units.KmhToMps(Model.DesignMaxSpeedKmh),
            new[] { new DriveSegment(0.0, DriverCommand.FullPower, "traction") },
            Array.Empty<ScenarioAssumption>());

        var drive = new ScenarioDrive(Model, scenario, Conditions, Step, stepBudget: 600);
        drive.RunToEnd();

        Assert.AreEqual("step-budget", drive.FinishReason);
        Assert.AreEqual(600, drive.State.Steps);
    }

    /// <summary>Polecenie obowiązuje od swojego chainage do następnego wpisu.</summary>
    [TestMethod]
    public void SegmentAt_zwraca_ostatni_obowiazujacy_odcinek()
    {
        var scenario = DriveScenario.PackageAFirstRun(Model);

        Assert.AreEqual("traction", scenario.SegmentAt(scenario.StartChainageM).Label);
        Assert.AreEqual("traction", scenario.SegmentAt(6419.999).Label);
        Assert.AreEqual("brake", scenario.SegmentAt(6420.0).Label);
        Assert.AreEqual("brake", scenario.SegmentAt(99999.0).Label);

        // Przed pierwszym odcinkiem obowiązuje pierwszy — skład nie zostaje bez polecenia.
        Assert.AreEqual("traction", scenario.SegmentAt(0.0).Label);
    }

    /// <summary>Scenariusz z odcinkami nie w kolejności jest błędem, nie do posortowania po cichu.</summary>
    [TestMethod]
    public void Scenariusz_odrzuca_odcinki_nierosnace_po_chainage()
    {
        var segments = new List<DriveSegment>
        {
            new(100.0, DriverCommand.FullPower, "a"),
            new(50.0, DriverCommand.FullServiceBrake, "b"),
        };

        Assert.ThrowsException<ArgumentException>(() => new DriveScenario(
            "zły", 0.0, 22.0, segments, Array.Empty<ScenarioAssumption>()));
        Assert.ThrowsException<ArgumentException>(() => new DriveScenario(
            "pusty", 0.0, 22.0, Array.Empty<DriveSegment>(), Array.Empty<ScenarioAssumption>()));
    }

    /// <summary>
    /// Każda liczba scenariusza bez źródła musi być zadeklarowana jako założenie —
    /// ten sam mechanizm, co <c>VehicleModel.DesignAssumptions</c> po stronie pojazdu
    /// i <c>DESIGN_ASSUMPTIONS</c> po stronie generatorów.
    /// </summary>
    [TestMethod]
    public void Scenariusz_pakietu_A_deklaruje_swoje_zalozenia()
    {
        var scenario = DriveScenario.PackageAFirstRun(Model);
        var names = scenario.Assumptions.Select(a => a.Name).ToArray();

        CollectionAssert.Contains(names, "StartChainageM");
        CollectionAssert.Contains(names, "BrakeChainageM");
        CollectionAssert.AllItemsAreUnique(names);

        foreach (var assumption in scenario.Assumptions)
        {
            Assert.IsFalse(string.IsNullOrWhiteSpace(assumption.Reason), assumption.Name);
        }

        Assert.AreEqual(scenario.StartChainageM,
            scenario.Assumptions.Single(a => a.Name == "StartChainageM").Value, 0.0);
        Assert.AreEqual(scenario.Segments[1].FromChainageM,
            scenario.Assumptions.Single(a => a.Name == "BrakeChainageM").Value, 0.0);
        Assert.AreEqual(Units.KmhToMps(Model.DesignMaxSpeedKmh), scenario.SpeedLimitMps, 0.0);
    }

    /// <summary>Telemetria ma tyle kolumn, ile deklaruje nagłówek — inaczej porównanie milczkiem gubi kolumnę.</summary>
    [TestMethod]
    public void Wiersz_telemetrii_ma_tyle_kolumn_co_naglowek()
    {
        var drive = NewDrive();
        drive.Step();

        var header = DriveTelemetry.Header.Split(',');
        var row = DriveTelemetry.Row(drive).Split(',');

        Assert.AreEqual(DriveTelemetry.ColumnCount, header.Length);
        Assert.AreEqual(DriveTelemetry.ColumnCount, row.Length);
        Assert.AreEqual("traction", row[^1]);
        Assert.IsTrue(DriveTelemetry.IsSample(240, 120));
        Assert.IsFalse(DriveTelemetry.IsSample(241, 120));
    }

    /// <summary>Konstruktor przejazdu odrzuca braki zamiast je zgadywać.</summary>
    [TestMethod]
    public void Konstruktor_przejazdu_odrzuca_braki()
    {
        var scenario = DriveScenario.PackageAFirstRun(Model);

        Assert.ThrowsException<ArgumentNullException>(
            () => new ScenarioDrive((TrainController)null!, scenario, Conditions, Step));
        Assert.ThrowsException<ArgumentNullException>(
            () => new ScenarioDrive(Model, null!, Conditions, Step));
        Assert.ThrowsException<ArgumentNullException>(
            () => new ScenarioDrive(Model, scenario, null!, Step));
        Assert.ThrowsException<ArgumentException>(
            () => new ScenarioDrive(Model, scenario, Conditions, default));
        Assert.ThrowsException<ArgumentOutOfRangeException>(
            () => new ScenarioDrive(Model, scenario, Conditions, Step, stepBudget: 0));
    }
}
