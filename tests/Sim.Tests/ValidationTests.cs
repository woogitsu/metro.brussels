using System;
using MetroBxl.Sim.Physics;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace MetroBxl.Sim.Tests;

/// <summary>
/// Testy negatywne. Model, który na bzdurne wejście odpowiada liczbą, jest gorszy od
/// modelu, który się zatrzymuje: ujemna masa albo zerowy krok dają wynik wyglądający
/// zupełnie normalnie, dopóki ktoś nie zapyta, skąd się wziął.
/// </summary>
[TestClass]
public sealed class ValidationTests
{
    private static readonly VehicleModel Model = VehicleModel.M7;

    [DataTestMethod]
    [DataRow(-1.0)]
    [DataRow(-170_000.0)]
    [DataRow(0.0)]
    [DataRow(double.NaN)]
    [DataRow(double.PositiveInfinity)]
    public void Masa_niedodatnia_lub_nieskonczona_jest_odrzucana(double massKg) =>
        Assert.ThrowsException<ArgumentOutOfRangeException>(
            () => new RunConditions(massKg, 0.0, 0.25, TrackEnvironment.Tunnel));

    [TestMethod]
    public void Zerowy_krok_czasowy_jest_odrzucany()
    {
        Assert.ThrowsException<ArgumentOutOfRangeException>(() => FixedStep.FromSeconds(0.0));
        Assert.ThrowsException<ArgumentOutOfRangeException>(() => FixedStep.FromSeconds(-1.0 / 120.0));
        Assert.ThrowsException<ArgumentOutOfRangeException>(() => FixedStep.FromSeconds(double.NaN));
        Assert.ThrowsException<ArgumentOutOfRangeException>(() => FixedStep.FromHertz(0));
        Assert.ThrowsException<ArgumentOutOfRangeException>(() => FixedStep.FromHertz(-120));
    }

    /// <summary>
    /// <c>default(FixedStep)</c> ma krok zerowy i w C# nie da się tego zabronić w typie
    /// wartościowym — więc odrzuca go całkowanie. Domyślny parametr metody przebiegu
    /// jest za to podmieniany na krok rdzenia, bo tak jest czytelniej w wywołaniu.
    /// </summary>
    [TestMethod]
    public void Niezainicjowany_krok_nie_wchodzi_do_calkowania()
    {
        var uninitialised = default(FixedStep);
        Assert.AreEqual(0.0, uninitialised.Seconds, 0.0);
        Assert.ThrowsException<ArgumentException>(() => uninitialised.RequireValid());

        Assert.ThrowsException<ArgumentException>(() => TrainDynamics.M7.Advance(
            TrainState.AtRest,
            RunConditions.Level(Model, TrainLoad.Aw0),
            Units.KmhToMps(80.0),
            uninitialised,
            out _));

        // …ale przebieg wywołany bez podania kroku dostaje krok rdzenia 1/120 s.
        var run = AccelerationRun.M7.ToSpeed(RunConditions.Level(Model, TrainLoad.Aw0), 80.0);
        Assert.AreEqual(FixedStep.Simulation, run.Step);
    }

    [DataTestMethod]
    [DataRow(0.0)]
    [DataRow(-10.0)]
    [DataRow(80.1)]
    [DataRow(120.0)]
    [DataRow(double.NaN)]
    [DataRow(double.PositiveInfinity)]
    public void Predkosc_docelowa_poza_zakresem_jest_odrzucana(double targetKmh) =>
        Assert.ThrowsException<ArgumentOutOfRangeException>(
            () => AccelerationRun.M7.ToSpeed(RunConditions.Level(Model, TrainLoad.Aw0), targetKmh));

    [TestMethod]
    public void Predkosc_dokladnie_rowna_Vmax_modelu_jest_dozwolona()
    {
        var run = AccelerationRun.M7.ToSpeed(RunConditions.Level(Model, TrainLoad.Aw0), Model.DesignMaxSpeedKmh);
        Assert.IsTrue(run.ReachedTarget);
        Assert.AreEqual(80.0, Model.DesignMaxSpeedKmh, 0.0);
    }

    [DataTestMethod]
    [DataRow(0.0)]
    [DataRow(-0.25)]
    [DataRow(1.5)]
    [DataRow(double.NaN)]
    public void Bezsensowna_przyczepnosc_jest_odrzucana(double adhesion) =>
        Assert.ThrowsException<ArgumentOutOfRangeException>(
            () => new RunConditions(170_000.0, 0.0, adhesion, TrackEnvironment.Tunnel));

    [DataTestMethod]
    [DataRow(15.001)]
    [DataRow(-40.0)]
    [DataRow(double.NaN)]
    public void Pochylenie_poza_zakresem_modelu_jest_odrzucane(double gradePercent) =>
        Assert.ThrowsException<ArgumentOutOfRangeException>(
            () => new RunConditions(170_000.0, gradePercent, 0.25, TrackEnvironment.Tunnel));

    [DataTestMethod]
    [DataRow(0.0)]
    [DataRow(-1.0)]
    [DataRow(85.0)]
    public void Predkosc_poczatkowa_hamowania_poza_zakresem_jest_odrzucana(double startKmh) =>
        Assert.ThrowsException<ArgumentOutOfRangeException>(() => ServiceBrakingRun.M7.ToStop(startKmh));

    [TestMethod]
    public void Niedodatnie_opoznienie_hamowania_jest_odrzucane()
    {
        Assert.ThrowsException<ArgumentOutOfRangeException>(() => ServiceBrakingRun.M7.ToStop(80.0, 0.0));
        Assert.ThrowsException<ArgumentOutOfRangeException>(() => ServiceBrakingRun.M7.ToStop(80.0, -1.1));
    }

    [TestMethod]
    public void Ujemny_odstep_probkowania_jest_odrzucany() =>
        Assert.ThrowsException<ArgumentOutOfRangeException>(
            () => AccelerationRun.M7.ToSpeed(RunConditions.Level(Model, TrainLoad.Aw0), 80.0, sampleEverySteps: -1));

    [TestMethod]
    public void Brak_warunkow_przebiegu_jest_bledem_a_nie_wartoscia_domyslna() =>
        Assert.ThrowsException<ArgumentNullException>(
            () => AccelerationRun.M7.ToSpeed(null!, 80.0));

    [TestMethod]
    public void Nieznany_status_parametru_w_rejestrze_jest_bledem() =>
        Assert.ThrowsException<FormatException>(() => ParameterStatusParser.Parse("mniej_wiecej"));

    /// <summary>
    /// Każdy napis z rejestru ma trafiać w SWÓJ status, a nie w jakikolwiek.
    ///
    /// Zmierzone 02.09.2026 mutacją: podmiana <c>"observed"</c> i <c>"est"</c> na
    /// <see cref="ParameterStatus.Spec"/> w parserze przechodziła przez cały zestaw
    /// (Passed: 252). Rejestr M7 nie ma dziś ani jednego wpisu <c>est</c>/<c>observed</c>,
    /// więc te dwie gałęzie nie były wykonywane przez nic. Dopisanie takiego wpisu
    /// oznaczałoby wtedy, że oszacowanie historyczne wchodzi do fizyki jako wartość
    /// z oficjalnego źródła — czyli dokładnie to, przed czym broni reguła 1 z CLAUDE.md.
    /// </summary>
    [TestMethod]
    public void Kazdy_status_z_rejestru_parsuje_sie_na_siebie()
    {
        Assert.AreEqual(ParameterStatus.Spec, ParameterStatusParser.Parse("spec"));
        Assert.AreEqual(ParameterStatus.Observed, ParameterStatusParser.Parse("observed"));
        Assert.AreEqual(ParameterStatus.Est, ParameterStatusParser.Parse("est"));
        Assert.AreEqual(ParameterStatus.DesignModel, ParameterStatusParser.Parse("design_model"));

        // Obie strony zamiany, dla każdego statusu z enuma — nowy status nie może
        // przejść bez napisu, a napis nie może wracać na inny status.
        foreach (ParameterStatus status in Enum.GetValues<ParameterStatus>())
        {
            var text = ParameterStatusParser.ToRegistryString(status);
            Assert.AreEqual(status, ParameterStatusParser.Parse(text), text);
        }

        Assert.AreEqual(4, Enum.GetValues<ParameterStatus>().Length,
            "doszedł status pochodzenia — dopisz go do tego testu, zanim wejdzie do fizyki");
    }

    /// <summary>
    /// Rdzeń nie wydaje liczby bez deklaracji jej pochodzenia: prośba o <c>spec</c>
    /// tam, gdzie rejestr ma <c>design_model</c>, kończy się wyjątkiem, a nie wynikiem.
    /// </summary>
    [TestMethod]
    public void Zla_deklaracja_statusu_parametru_konczy_sie_wyjatkiem()
    {
        Assert.ThrowsException<System.IO.InvalidDataException>(
            () => VehicleRegistry.M7.RequireValue("parameters.max_speed_kmh", ParameterStatus.Spec));
        Assert.ThrowsException<System.IO.InvalidDataException>(
            () => VehicleRegistry.M7.RequireValue("parameters.empty_mass_kg", ParameterStatus.DesignModel));
        Assert.ThrowsException<System.Collections.Generic.KeyNotFoundException>(
            () => VehicleRegistry.M7.Get("reference_model.wymyslony_parametr"));
    }
}
