using System;
using System.Collections.Generic;
using System.Globalization;
using MetroBxl.Sim.Physics;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace MetroBxl.Sim.Tests;

/// <summary>
/// Parytet z <c>tools/physics/reference.py</c>. Referencja jest źródłem prawdy dla
/// modelu projektowego; rdzeń C# ma dawać te same liczby, a nie liczby podobne.
///
/// Tolerancje:
/// • <b>liczba kroków — dokładnie</b>. To jest właściwe kryterium parytetu: identyczna
///   liczba kroków oznacza, że obie implementacje przeszły tę samą trajektorię, krok po kroku.
/// • <b>droga — 1 nm</b>. Ta sama kolejność działań zmiennoprzecinkowych daje ten sam
///   wynik co do bitu; tolerancja jest tylko zabezpieczeniem przed inną biblioteką
///   matematyczną, nie miejscem na rozjazd modelu.
/// • <b>czas — 1 ns</b>. Referencja sumuje <c>t += dt</c>, rdzeń liczy <c>kroki · dt</c>.
///   Zmierzona różnica po 3023 krokach to 7,9·10⁻¹³ s, czyli tysięczna część tolerancji.
///   Rdzeń nie sumuje przyrostów świadomie: suma dryfuje z długością przebiegu,
///   iloczyn nie dryfuje nigdy (<c>docs/01-architecture.md</c>, determinizm).
/// </summary>
[TestClass]
public sealed class ReferenceParityTests
{
    /// <summary>Tolerancja drogi: nanometr.</summary>
    public const double DistanceToleranceM = 1e-9;

    /// <summary>Tolerancja czasu: nanosekunda.</summary>
    public const double TimeToleranceS = 1e-9;

    /// <summary>Tolerancja siły: mikroniuton.</summary>
    public const double ForceToleranceN = 1e-6;

    private static readonly VehicleModel Model = VehicleModel.M7;

    [TestMethod]
    public void Rozruch_0_80_AW0_zgadza_sie_z_referencja()
    {
        var run = AccelerationRun.M7.ToSpeed(RunConditions.Level(Model, TrainLoad.Aw0), 80.0);

        Assert.AreEqual(PythonReference.Accel80Aw0Steps, run.Steps, "liczba kroków");
        Assert.AreEqual(PythonReference.Accel80Aw0TimeS, run.TimeSeconds, TimeToleranceS, "czas");
        Assert.AreEqual(PythonReference.Accel80Aw0DistanceM, run.DistanceM, DistanceToleranceM, "droga");
        Assert.IsTrue(run.ReachedTarget);
    }

    [TestMethod]
    public void Rozruch_0_80_AW2_zgadza_sie_z_referencja()
    {
        var run = AccelerationRun.M7.ToSpeed(RunConditions.Level(Model, TrainLoad.Aw2), 80.0);

        Assert.AreEqual(PythonReference.Accel80Aw2Steps, run.Steps, "liczba kroków");
        Assert.AreEqual(PythonReference.Accel80Aw2TimeS, run.TimeSeconds, TimeToleranceS, "czas");
        Assert.AreEqual(PythonReference.Accel80Aw2DistanceM, run.DistanceM, DistanceToleranceM, "droga");
    }

    /// <summary>
    /// Referencja liczy hamowanie służbowe osobno dla AW0 i AW2 i dostaje dwa razy tę
    /// samą liczbę, bo model jest kinematyczny. Rdzeń nie przyjmuje masy w tej ścieżce
    /// w ogóle, więc oba wiersze tabeli parytetu wychodzą z jednego wywołania.
    /// </summary>
    [TestMethod]
    public void Hamowanie_sluzbowe_80_0_zgadza_sie_z_referencja_i_nie_zalezy_od_masy()
    {
        var run = ServiceBrakingRun.M7.ToStop(80.0);

        Assert.AreEqual(PythonReference.ServiceBrake80Steps, run.Steps, "liczba kroków");
        Assert.AreEqual(PythonReference.ServiceBrake80TimeS, run.TimeSeconds, TimeToleranceS, "czas");
        Assert.AreEqual(PythonReference.ServiceBrake80DistanceM, run.DistanceM, DistanceToleranceM, "droga");
        Assert.AreEqual(0.0, run.FinalSpeedMps, "skład ma stanąć");
        Assert.IsNull(run.Energy, "model kinematyczny nie ma bilansu energii");
    }

    [TestMethod]
    public void Hamowanie_awaryjne_80_0_zgadza_sie_z_referencja()
    {
        var run = ServiceBrakingRun.M7.ToStop(80.0, Model.DesignEmergencyBrakeMps2);

        Assert.AreEqual(PythonReference.EmergencyBrake80TimeS, run.TimeSeconds, TimeToleranceS);
        Assert.AreEqual(PythonReference.EmergencyBrake80DistanceM, run.DistanceM, DistanceToleranceM);
    }

    [TestMethod]
    public void Punkt_przejscia_F0_P_to_31_24_km_h_i_jest_pochodna_mocy_i_F0()
    {
        var transition = Model.DesignForcePowerTransitionSpeedMps;

        Assert.AreEqual(
            Model.InstalledPowerW / Model.DesignStartupForceN, transition, 0.0,
            "punkt przejścia musi być pochodną, a nie liczbą wpisaną z ręki");
        Assert.AreEqual(PythonReference.TransitionSpeedMps, transition, 1e-12);
        Assert.AreEqual(PythonReference.TransitionSpeedKmh, Units.MpsToKmh(transition), 1e-12);
        Assert.IsTrue(Units.MpsToKmh(transition) is > 31.2 and < 31.3);
    }

    [TestMethod]
    public void Pochylenie_pod_gore_i_z_gory_zgadza_sie_z_referencja()
    {
        var level = RunConditions.Level(Model, TrainLoad.Aw2);

        var uphill = AccelerationRun.M7.ToSpeed(level.WithGrade(3.0), 80.0);
        var downhill = AccelerationRun.M7.ToSpeed(level.WithGrade(-3.0), 80.0);

        Assert.AreEqual(PythonReference.Accel80Aw2UphillTimeS, uphill.TimeSeconds, TimeToleranceS);
        Assert.AreEqual(PythonReference.Accel80Aw2UphillDistanceM, uphill.DistanceM, DistanceToleranceM);
        Assert.AreEqual(PythonReference.Accel80Aw2DownhillTimeS, downhill.TimeSeconds, TimeToleranceS);
        Assert.AreEqual(PythonReference.Accel80Aw2DownhillDistanceM, downhill.DistanceM, DistanceToleranceM);

        Assert.IsTrue(uphill.TimeSeconds > downhill.TimeSeconds, "pod górę musi być wolniej");
        Assert.IsTrue(uphill.DistanceM > downhill.DistanceM, "pod górę droga rozruchu musi być dłuższa");
    }

    [TestMethod]
    public void Mokra_szyna_wydluza_rozruch_zgodnie_z_referencja()
    {
        var dry = RunConditions.Level(Model, TrainLoad.Aw0);
        var wet = dry.WithAdhesion(Model.Adhesion(RailCondition.Wet));

        var dryRun = AccelerationRun.M7.ToSpeed(dry, 80.0);
        var wetRun = AccelerationRun.M7.ToSpeed(wet, 80.0);

        Assert.AreEqual(PythonReference.Accel80Aw0WetTimeS, wetRun.TimeSeconds, TimeToleranceS);
        Assert.AreEqual(PythonReference.Accel80Aw0WetDistanceM, wetRun.DistanceM, DistanceToleranceM);
        Assert.IsTrue(wetRun.TimeSeconds > dryRun.TimeSeconds, "na mokrej szynie rozruch musi trwać dłużej");
    }

    [TestMethod]
    public void Zaladowany_sklad_rozpedza_sie_wolniej_i_na_dluzszej_drodze()
    {
        var aw0 = AccelerationRun.M7.ToSpeed(RunConditions.Level(Model, TrainLoad.Aw0), 80.0);
        var aw2 = AccelerationRun.M7.ToSpeed(RunConditions.Level(Model, TrainLoad.Aw2), 80.0);

        Assert.IsTrue(aw2.TimeSeconds > aw0.TimeSeconds);
        Assert.IsTrue(aw2.DistanceM > aw0.DistanceM);
    }

    [TestMethod]
    public void Moc_zainstalowana_to_2160_kW_ze_zrodla_pierwotnego()
    {
        Assert.AreEqual(2_160_000.0, Model.InstalledPowerW, 0.0);
        Assert.AreEqual(170_000.0, Model.EmptyMassKg, 0.0);
    }

    /// <summary>
    /// Droga zgadza się z referencją <b>co do bitu</b>, nie w granicach tolerancji.
    /// To jest właściwy dowód, że obie implementacje wykonują te same działania w tej
    /// samej kolejności: przy liczbach zmiennoprzecinkowych przestawienie mnożenia i
    /// dzielenia widać w ostatnim bicie mantysy, a tego testu nie da się przejść przypadkiem.
    /// </summary>
    [TestMethod]
    public void Droga_zgadza_sie_z_referencja_co_do_bitu()
    {
        AssertSameBits(
            PythonReference.Accel80Aw0DistanceM,
            AccelerationRun.M7.ToSpeed(RunConditions.Level(Model, TrainLoad.Aw0), 80.0).DistanceM,
            "accel_0_80 AW0");

        AssertSameBits(
            PythonReference.Accel80Aw2DistanceM,
            AccelerationRun.M7.ToSpeed(RunConditions.Level(Model, TrainLoad.Aw2), 80.0).DistanceM,
            "accel_0_80 AW2");

        AssertSameBits(
            PythonReference.ServiceBrake80DistanceM,
            ServiceBrakingRun.M7.ToStop(80.0).DistanceM,
            "brake_service_80_0");

        AssertSameBits(
            PythonReference.Accel80Aw2UphillDistanceM,
            AccelerationRun.M7.ToSpeed(RunConditions.Level(Model, TrainLoad.Aw2).WithGrade(3.0), 80.0).DistanceM,
            "accel_0_80 AW2 +3%");

        static void AssertSameBits(double expected, double actual, string label) =>
            Assert.AreEqual(
                BitConverter.DoubleToInt64Bits(expected),
                BitConverter.DoubleToInt64Bits(actual),
                string.Create(CultureInfo.InvariantCulture, $"{label}: {expected:R} vs {actual:R}"));
    }

    /// <summary>
    /// Tabela parytetu wypisana na wyjście testu — te same cztery przypadki, które
    /// drukuje referencja, w tej samej postaci. Do wklejenia w raport, żeby nikt nie
    /// musiał wierzyć na słowo, że liczby się zgadzają.
    /// </summary>
    [TestMethod]
    public void Tabela_parytetu_do_raportu()
    {
        // Wiersze idą najpierw do listy, a na konsolę dopiero po policzeniu. Powód jest
        // zmierzony, nie estetyczny: audyt asercji z 05.09.2026 pokazał, że ten test
        // przechodził, wykonując ZERO asercji — drukował cztery wiersze i podnosił
        // licznik `Passed` tak samo, jak podniósłby go, nie drukując ani jednego.
        // Tabela, która wyszła pusta, jest awarią raportu, a nie pustym raportem.
        var rows = new List<string>();

        Row("accel_0_80", "AW0",
            PythonReference.Accel80Aw0TimeS, PythonReference.Accel80Aw0DistanceM,
            AccelerationRun.M7.ToSpeed(RunConditions.Level(Model, TrainLoad.Aw0), 80.0));

        Row("accel_0_80", "AW2",
            PythonReference.Accel80Aw2TimeS, PythonReference.Accel80Aw2DistanceM,
            AccelerationRun.M7.ToSpeed(RunConditions.Level(Model, TrainLoad.Aw2), 80.0));

        var brake = ServiceBrakingRun.M7.ToStop(80.0);
        Row("brake_service_80_0", "AW0", PythonReference.ServiceBrake80TimeS, PythonReference.ServiceBrake80DistanceM, brake);
        Row("brake_service_80_0", "AW2", PythonReference.ServiceBrake80TimeS, PythonReference.ServiceBrake80DistanceM, brake);

        Assert.AreEqual(4, rows.Count, "tabela parytetu wyszła niepełna");
        foreach (string row in rows)
        {
            Assert.IsTrue(row.EndsWith(" |", StringComparison.Ordinal), row);
            Console.WriteLine(row);
        }

        void Row(string name, string load, double refTime, double refDistance, RunResult run)
        {
            rows.Add(string.Create(
                CultureInfo.InvariantCulture,
                $"| {name} | {load} | {refTime:F1} | {run.TimeSeconds:F1} | {refDistance:F1} | {run.DistanceM:F1} | " +
                $"{run.Steps} | dt={run.TimeSeconds - refTime:E3} s | ds={run.DistanceM - refDistance:E3} m |"));
        }
    }
}
