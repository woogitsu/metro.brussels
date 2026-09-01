using System;
using System.Globalization;
using MetroBxl.Sim.Physics;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace MetroBxl.Sim.Tests;

/// <summary>
/// Energia i profil prędkości. Bilans energii jest tu drugą, niezależną drogą do
/// wyniku przebiegu — <c>docs/06-worked-example.md</c>: dobre zadanie kończy się
/// dwiema drogami do tej samej liczby, a rozjazd między nimi jest informacją.
/// </summary>
[TestClass]
public sealed class EnergyAndProfileTests
{
    /// <summary>
    /// Dopuszczalne niedomknięcie bilansu, odniesione do pracy trakcji. Praca, energia
    /// kinetyczna i człon dyskretyzacji sumują się do zera w arytmetyce dokładnej, więc
    /// zostaje wyłącznie kumulacja błędu zaokrągleń po kilku tysiącach kroków —
    /// zmierzone niedomknięcie jest o kilka rzędów mniejsze od tego progu.
    /// </summary>
    private const double EnergyClosureTolerance = 1e-12;

    private static readonly VehicleModel Model = VehicleModel.M7;

    [TestMethod]
    public void Bilans_energii_rozruchu_domyka_sie_na_poziomie()
    {
        var run = AccelerationRun.M7.ToSpeed(RunConditions.Level(Model, TrainLoad.Aw2), 80.0);
        var energy = run.Energy!.Value;

        Console.WriteLine(string.Create(CultureInfo.InvariantCulture, $"AW2 0→80 poziom: {energy}"));
        Console.WriteLine(string.Create(
            CultureInfo.InvariantCulture,
            $"niedomknięcie względne = {energy.RelativeResidual:E3}"));

        Assert.IsTrue(energy.TractionWorkJ > 0.0);
        Assert.IsTrue(energy.ResistanceWorkJ > 0.0);
        Assert.AreEqual(0.0, energy.GradeWorkJ, 0.0, "na poziomie praca na pochyleniu jest zerowa");
        Assert.IsTrue(
            energy.RelativeResidual < EnergyClosureTolerance,
            string.Create(CultureInfo.InvariantCulture, $"bilans nie domyka się: {energy.RelativeResidual:E3}"));
    }

    [TestMethod]
    public void Bilans_energii_domyka_sie_takze_pod_gore_i_z_gory()
    {
        var level = RunConditions.Level(Model, TrainLoad.Aw2);

        var uphill = AccelerationRun.M7.ToSpeed(level.WithGrade(2.0), 60.0).Energy!.Value;
        var downhill = AccelerationRun.M7.ToSpeed(level.WithGrade(-2.0), 60.0).Energy!.Value;

        Assert.IsTrue(uphill.RelativeResidual < EnergyClosureTolerance);
        Assert.IsTrue(downhill.RelativeResidual < EnergyClosureTolerance);

        Assert.IsTrue(uphill.GradeWorkJ > 0.0, "pod górę praca przeciw ciężarowi jest dodatnia");
        Assert.IsTrue(downhill.GradeWorkJ < 0.0, "z góry ciężar pracuje na rzecz pociągu");
        Assert.IsTrue(
            uphill.TractionWorkJ > downhill.TractionWorkJ,
            "pod górę trzeba włożyć więcej pracy na tę samą prędkość końcową");
    }

    [TestMethod]
    public void Energia_kinetyczna_liczy_sie_od_masy_efektywnej()
    {
        var conditions = RunConditions.Level(Model, TrainLoad.Aw0);
        var run = AccelerationRun.M7.ToSpeed(conditions, 80.0);
        var energy = run.Energy!.Value;

        var effectiveMass = conditions.MassKg * Model.DesignEffectiveMassFactor;
        Assert.AreEqual(
            0.5 * effectiveMass * run.FinalSpeedMps * run.FinalSpeedMps,
            energy.KineticEnergyJ,
            1e-6);
    }

    [TestMethod]
    public void Praca_trakcji_w_kWh_ma_wlasciwy_rzad_wielkosci()
    {
        var energy = AccelerationRun.M7.ToSpeed(RunConditions.Level(Model, TrainLoad.Aw2), 80.0).Energy!.Value;

        Console.WriteLine(string.Create(
            CultureInfo.InvariantCulture,
            $"praca trakcji 0→80 AW2 = {energy.TractionWorkKwh:F4} kWh"));

        // Energia kinetyczna masy efektywnej AW2 przy 80 km/h to ~59 MJ, czyli ~16 kWh;
        // opory dokładają kilka procent. Wynik poza przedziałem 10–25 kWh oznaczałby
        // pomylone jednostki, a nie inny model.
        Assert.IsTrue(energy.TractionWorkKwh is > 10.0 and < 25.0, $"{energy.TractionWorkKwh} kWh");
    }

    [TestMethod]
    public void Probkowanie_profilu_nie_zmienia_wyniku_przebiegu()
    {
        var conditions = RunConditions.Level(Model, TrainLoad.Aw0);

        var plain = AccelerationRun.M7.ToSpeed(conditions, 80.0);
        var sampled = AccelerationRun.M7.ToSpeed(conditions, 80.0, sampleEverySteps: 12);

        Assert.AreEqual(
            BitConverter.DoubleToInt64Bits(plain.DistanceM),
            BitConverter.DoubleToInt64Bits(sampled.DistanceM),
            "obserwacja przebiegu nie może zmienić przebiegu");
        Assert.AreEqual(plain.Steps, sampled.Steps);
        Assert.AreEqual(0, plain.Profile.Samples.Count);
        Assert.IsTrue(sampled.Profile.Samples.Count > 0);
    }

    [TestMethod]
    public void Profil_rozruchu_jest_monotoniczny_i_konczy_sie_na_wyniku_przebiegu()
    {
        var run = AccelerationRun.M7.ToSpeed(RunConditions.Level(Model, TrainLoad.Aw2), 80.0, sampleEverySteps: 60);
        var samples = run.Profile.Samples;

        Assert.AreEqual(0.0, samples[0].SpeedMps, 0.0);
        Assert.AreEqual(0.0, samples[0].DistanceM, 0.0);

        for (var i = 1; i < samples.Count; i++)
        {
            Assert.IsTrue(samples[i].TimeSeconds > samples[i - 1].TimeSeconds, "czas musi rosnąć");
            Assert.IsTrue(samples[i].SpeedMps >= samples[i - 1].SpeedMps, "przy rozruchu prędkość nie spada");
            Assert.IsTrue(samples[i].DistanceM > samples[i - 1].DistanceM, "droga musi rosnąć");
        }

        var last = samples[^1];
        Assert.AreEqual(run.Steps, last.Steps);
        Assert.AreEqual(run.DistanceM, last.DistanceM, 0.0);
        Assert.AreEqual(run.FinalSpeedMps, last.SpeedMps, 0.0);
        Assert.AreEqual(80.0, run.Profile.PeakSpeedMps * 3.6, 1e-9);
    }

    [TestMethod]
    public void Profil_hamowania_maleje_do_zera()
    {
        var run = ServiceBrakingRun.M7.ToStop(80.0, FixedStep.Simulation, sampleEverySteps: 60);
        var samples = run.Profile.Samples;

        Assert.AreEqual(80.0, samples[0].SpeedKmh, 1e-9);
        for (var i = 1; i < samples.Count; i++)
        {
            Assert.IsTrue(samples[i].SpeedMps < samples[i - 1].SpeedMps, "przy hamowaniu prędkość musi maleć");
        }

        Assert.AreEqual(0.0, samples[^1].SpeedMps, 0.0);
    }

    /// <summary>
    /// Ograniczenie zrywu widać w profilu: na starcie hamowania opóźnienie narasta
    /// od zera, więc pierwsza sekunda zabiera mniej prędkości niż kolejna.
    /// </summary>
    [TestMethod]
    public void Ograniczenie_zrywu_widac_na_poczatku_hamowania()
    {
        var run = ServiceBrakingRun.M7.ToStop(80.0, FixedStep.Simulation, sampleEverySteps: 120);
        var samples = run.Profile.Samples;

        var firstSecond = samples[0].SpeedMps - samples[1].SpeedMps;
        var secondSecond = samples[1].SpeedMps - samples[2].SpeedMps;

        Assert.IsTrue(firstSecond < secondSecond, "pierwsza sekunda musi zabrać mniej prędkości");

        // Docelowe opóźnienie służbowe to 1,10 m/s²; przy zrywie 0,75 m/s³ pełną
        // wartość osiąga po ~1,47 s, więc w pierwszej sekundzie średnie opóźnienie
        // musi być wyraźnie mniejsze.
        Assert.IsTrue(firstSecond < Model.DesignServiceBrakeMps2);
        Assert.IsTrue(secondSecond <= Model.DesignServiceBrakeMps2 + 1e-9);
    }

    [TestMethod]
    public void Hamowanie_awaryjne_jest_krotsze_od_sluzbowego()
    {
        var service = ServiceBrakingRun.M7.ToStop(80.0, Model.DesignServiceBrakeMps2);
        var emergency = ServiceBrakingRun.M7.ToStop(80.0, Model.DesignEmergencyBrakeMps2);

        Assert.IsTrue(emergency.DistanceM < service.DistanceM);
        Assert.IsTrue(emergency.TimeSeconds < service.TimeSeconds);
    }
}
