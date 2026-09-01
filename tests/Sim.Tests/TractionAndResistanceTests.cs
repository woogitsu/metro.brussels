using MetroBxl.Sim.Physics;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace MetroBxl.Sim.Tests;

/// <summary>
/// Charakterystyka trakcyjna i opory ruchu osobno, bez całkowania. Przebieg 0 → 80
/// przechodzi przez oba modele naraz, więc sam w sobie nie pokazuje, który z nich się myli.
/// </summary>
[TestClass]
public sealed class TractionAndResistanceTests
{
    private const double ForceToleranceN = 1e-6;

    private static readonly VehicleModel Model = VehicleModel.M7;
    private static readonly TractionModel Traction = TractionModel.M7;
    private static readonly DavisResistance Resistance = DavisResistance.M7;

    [TestMethod]
    public void Ponizej_punktu_przejscia_sila_jest_stala_i_rowna_F0()
    {
        Assert.AreEqual(248_900.0, Traction.CharacteristicForceN(0.0), ForceToleranceN);
        Assert.AreEqual(248_900.0, Traction.CharacteristicForceN(Traction.TransitionSpeedMps), ForceToleranceN);
        Assert.AreEqual(Model.DesignStartupForceN, Traction.CharacteristicForceN(1.0), ForceToleranceN);
    }

    [TestMethod]
    public void Powyzej_punktu_przejscia_obowiazuje_stala_moc_zainstalowana()
    {
        var speed = Units.KmhToMps(80.0);
        Assert.AreEqual(Model.InstalledPowerW / speed, Traction.CharacteristicForceN(speed), ForceToleranceN);

        // Iloczyn siły i prędkości nie może przekroczyć 2160 kW — to jest wartość `spec`.
        Assert.AreEqual(Model.InstalledPowerW, Traction.CharacteristicForceN(speed) * speed, 1e-6);
    }

    [TestMethod]
    public void Sucha_szyna_przenosi_F0_a_mokra_juz_nie()
    {
        var aw0 = Model.MassKg(TrainLoad.Aw0);
        var dry = Model.Adhesion(RailCondition.Dry);
        var wet = Model.Adhesion(RailCondition.Wet);

        Assert.AreEqual(0.25, dry, 0.0);
        Assert.AreEqual(0.13, wet, 0.0);

        Assert.AreEqual(PythonReference.AdhesionLimitAw0DryN, Traction.AdhesionLimitN(aw0, dry), ForceToleranceN);
        Assert.AreEqual(
            PythonReference.AdhesionLimitAw2WetN,
            Traction.AdhesionLimitN(Model.MassKg(TrainLoad.Aw2), wet),
            ForceToleranceN);

        Assert.IsFalse(Traction.IsAdhesionLimited(0.0, aw0, dry), "sucho F0 mieści się w przyczepności");
        Assert.IsTrue(Traction.IsAdhesionLimited(0.0, aw0, wet), "mokro przyczepność obcina F0");

        Assert.AreEqual(Model.DesignStartupForceN, Traction.ForceN(0.0, aw0, dry), ForceToleranceN);
        Assert.AreEqual(Traction.AdhesionLimitN(aw0, wet), Traction.ForceN(0.0, aw0, wet), ForceToleranceN);
    }

    [TestMethod]
    public void Limit_przyczepnosci_rosnie_liniowo_z_masa()
    {
        var dry = Model.Adhesion(RailCondition.Dry);
        var single = Traction.AdhesionLimitN(100_000.0, dry);
        var doubled = Traction.AdhesionLimitN(200_000.0, dry);

        Assert.AreEqual(2.0 * single, doubled, 1e-9);
    }

    [TestMethod]
    public void Opory_w_tunelu_i_na_powierzchni_zgadzaja_sie_z_referencja()
    {
        var mass = Model.MassKg(TrainLoad.Aw0);
        var speed = Units.KmhToMps(80.0);

        Assert.AreEqual(1.40, Resistance.Multiplier(TrackEnvironment.Tunnel), 0.0);
        Assert.AreEqual(1.00, Resistance.Multiplier(TrackEnvironment.Surface), 0.0);

        Assert.AreEqual(
            PythonReference.DavisTunnelAw080KmhN,
            Resistance.ForceN(mass, speed, TrackEnvironment.Tunnel),
            ForceToleranceN);
        Assert.AreEqual(
            PythonReference.DavisSurfaceAw080KmhN,
            Resistance.ForceN(mass, speed, TrackEnvironment.Surface),
            ForceToleranceN);
    }

    [TestMethod]
    public void W_tunelu_opor_jest_wiekszy_niz_na_powierzchni_i_tylko_przez_czlon_kwadratowy()
    {
        var mass = Model.MassKg(TrainLoad.Aw0);

        // Na postoju człon kwadratowy znika, więc mnożnik tunelowy nie ma na czym działać.
        Assert.AreEqual(
            Resistance.ForceN(mass, 0.0, TrackEnvironment.Tunnel),
            Resistance.ForceN(mass, 0.0, TrackEnvironment.Surface),
            ForceToleranceN);

        var speed = Units.KmhToMps(80.0);
        Assert.IsTrue(
            Resistance.ForceN(mass, speed, TrackEnvironment.Tunnel)
            > Resistance.ForceN(mass, speed, TrackEnvironment.Surface));
    }

    [TestMethod]
    public void Opor_rosnie_monotonicznie_z_predkoscia()
    {
        var mass = Model.MassKg(TrainLoad.Aw2);
        var previous = double.NegativeInfinity;

        for (var kmh = 0.0; kmh <= 80.0; kmh += 5.0)
        {
            var force = Resistance.ForceN(mass, Units.KmhToMps(kmh), TrackEnvironment.Tunnel);
            Assert.IsTrue(force > previous, "opór ruchu musi rosnąć z prędkością");
            previous = force;
        }
    }

    [TestMethod]
    public void Sila_na_pochyleniu_liczy_sie_od_masy_rzeczywistej_a_nie_efektywnej()
    {
        var mass = Model.MassKg(TrainLoad.Aw2);
        var expected = mass * Units.StandardGravityMps2 * 3.0 / 100.0;

        Assert.AreEqual(expected, TrainDynamics.GradeForceN(mass, 3.0), 1e-6);
        Assert.AreEqual(-expected, TrainDynamics.GradeForceN(mass, -3.0), 1e-6);
        Assert.AreEqual(0.0, TrainDynamics.GradeForceN(mass, 0.0), 0.0);
    }

    /// <summary>
    /// Masa wirująca zwiększa bezwładność, ale nie ciężar. Referencja robi to samo i
    /// wygląda to jak niekonsekwencja, dopóki nie zapyta się, co ten współczynnik opisuje.
    /// </summary>
    [TestMethod]
    public void Masa_efektywna_wchodzi_tylko_do_przyspieszenia()
    {
        var conditions = RunConditions.Level(Model, TrainLoad.Aw0);
        var dynamics = TrainDynamics.M7;
        var forces = dynamics.Forces(0.0, conditions);

        Assert.AreEqual(1.08, dynamics.EffectiveMassFactor, 0.0);
        Assert.AreEqual(
            conditions.MassKg * 1.08,
            dynamics.EffectiveMassKg(conditions.MassKg),
            1e-9);

        // Opór policzony od masy rzeczywistej, przyspieszenie od efektywnej.
        Assert.AreEqual(
            Resistance.ForceN(conditions.MassKg, 0.0, TrackEnvironment.Tunnel),
            forces.ResistanceN,
            ForceToleranceN);
        Assert.AreEqual(
            forces.NetN / (conditions.MassKg * 1.08),
            forces.AccelerationMps2,
            1e-12);
    }

    /// <summary>
    /// Model nie odtacza się w tył: przy pochyleniu, którego trakcja nie pokonuje,
    /// przyspieszenie jest obcinane do zera, a przebieg kończy limit czasu.
    /// Ruch wsteczny wymagałby modelu hamulca postojowego — to nie jest T-310.
    /// </summary>
    [TestMethod]
    public void Zbyt_strome_pochylenie_zatrzymuje_sklad_zamiast_cofac()
    {
        var conditions = RunConditions.Level(Model, TrainLoad.Aw2).WithGrade(15.0);
        var forces = TrainDynamics.M7.Forces(0.0, conditions);

        Assert.IsTrue(forces.NetN < 0.0, "przy 15% siła wypadkowa musi być ujemna");
        Assert.AreEqual(0.0, forces.AccelerationMps2, 0.0);

        var run = AccelerationRun.M7.ToSpeed(conditions, 80.0);
        Assert.AreEqual(RunOutcome.TimeLimit, run.Outcome);
        Assert.AreEqual(0.0, run.DistanceM, 0.0);
    }
}
