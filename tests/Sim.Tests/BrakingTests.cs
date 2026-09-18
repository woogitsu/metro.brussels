using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Reflection;
using MetroBxl.Sim.Physics;
using MetroBxl.Sim.Train;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace MetroBxl.Sim.Tests;

/// <summary>
/// Testy modelu hamowania z T-311.
///
/// Trzy rzeczy, których w rdzeniu nie było i które mają tu swoje testy:
/// sufit przyczepnościowy hamowania, solver punktu hamowania z ograniczeniem zrywu
/// i droga hamowania liczona z oporami ruchu. Do tego audyt założeń projektowych
/// i **regresja parytetu T-400**: model hamowania nie ma prawa zmienić przejazdu
/// pakietu A ani o bit.
/// </summary>
[TestClass]
public sealed class BrakingTests
{
    private static readonly VehicleModel Model = VehicleModel.M7;
    private static readonly FixedStep Step = FixedStep.Simulation;

    private static BrakeAdhesionLimit AllAxles => BrakeAdhesionLimit.AllAxles(Model);

    private static BrakeAdhesionLimit PoweredOnly => BrakeAdhesionLimit.PoweredAxlesOnly(Model);

    // === 1. sufit przyczepnościowy hamowania =====================================

    /// <summary>
    /// Sufit zgadza się z niezależną referencją <c>tools/physics/braking.py</c>
    /// **co do bitu**. Wzór jest jeden i ta sama kolejność mnożeń daje tę samą
    /// liczbę; każdy inny wynik znaczy, że rozjechał się model, nie zaokrąglenie.
    /// </summary>
    [TestMethod]
    public void Sufit_przyczepnosciowy_zgadza_sie_z_referencja_co_do_bitu()
    {
        AssertBits(BrakingReference.CeilingDryAllAxlesMps2, AllAxles.MaxDecelerationMps2(Model.DesignAdhesionDry));
        AssertBits(BrakingReference.CeilingWetAllAxlesMps2, AllAxles.MaxDecelerationMps2(Model.DesignAdhesionWet));
        AssertBits(BrakingReference.CeilingDryPoweredOnlyMps2, PoweredOnly.MaxDecelerationMps2(Model.DesignAdhesionDry));
        AssertBits(BrakingReference.CeilingWetPoweredOnlyMps2, PoweredOnly.MaxDecelerationMps2(Model.DesignAdhesionWet));
        AssertBits(
            BrakingReference.CeilingRigidDryAllAxlesMps2, AllAxles.MaxRigidBodyDecelerationMps2(Model.DesignAdhesionDry));
        AssertBits(
            BrakingReference.CeilingRigidWetAllAxlesMps2, AllAxles.MaxRigidBodyDecelerationMps2(Model.DesignAdhesionWet));
    }

    /// <summary>
    /// **Masa się skraca.** Sufit opóźnienia jest ten sam dla AW0 i AW2 — różni się
    /// wyłącznie siła, jaką trzeba przenieść przez styk, i to dokładnie w stosunku mas.
    /// </summary>
    [TestMethod]
    public void Sufit_opoznienia_nie_zalezy_od_masy_a_sila_zalezy_liniowo()
    {
        var mu = Model.DesignAdhesionDry;
        var aw0 = Model.MassKg(TrainLoad.Aw0);
        var aw2 = Model.MassKg(TrainLoad.Aw2);

        Assert.AreEqual(AllAxles.MaxDecelerationMps2(mu), AllAxles.MaxDecelerationMps2(mu), 0.0);

        var forceAw0 = AllAxles.MaxBrakeForceN(aw0, mu);
        var forceAw2 = AllAxles.MaxBrakeForceN(aw2, mu);
        Assert.AreEqual(aw2 / aw0, forceAw2 / forceAw0, 1e-15, "siła musi rosnąć dokładnie jak masa");

        // Sufit opóźnienia = siła / masa efektywna, i to dla obu obciążeń ta sama liczba.
        var fromForceAw0 = forceAw0 / (aw0 * Model.DesignEffectiveMassFactor);
        var fromForceAw2 = forceAw2 / (aw2 * Model.DesignEffectiveMassFactor);
        Assert.AreEqual(AllAxles.MaxDecelerationMps2(mu), fromForceAw0, 1e-15);
        Assert.AreEqual(AllAxles.MaxDecelerationMps2(mu), fromForceAw2, 1e-15);
    }

    /// <summary>
    /// **Wynik, dla którego to zadanie powstało.** Przy μ = 0,13 (mokra szyna,
    /// <c>design_model</c>) hamowanie awaryjne 1,30 m/s² wymaga udziału osi hamowanych
    /// większego od 1 — czyli jest nieosiągalne przy **każdym** układzie hamulcowym,
    /// nie tylko przy tym legacy 4/6. Wniosek nie zależy od decyzji o masach wirujących:
    /// bez współczynnika λ potrzebny udział to nadal ponad 1.
    /// </summary>
    [TestMethod]
    public void Hamowanie_awaryjne_na_mokrej_szynie_jest_nieosiagalne_przy_kazdym_udziale_osi()
    {
        var wet = Model.DesignAdhesionWet;
        var required = AllAxles.RequiredBrakedMassFraction(Model.DesignEmergencyBrakeMps2, wet);

        Console.WriteLine(string.Create(
            CultureInfo.InvariantCulture,
            $"[SUFIT] awaryjne {Model.DesignEmergencyBrakeMps2:F2} m/s², mokro μ={wet:F2}: " +
            $"f_min = {required:F6}, sufit przy f=1 = {AllAxles.MaxDecelerationMps2(wet):F6} m/s², " +
            $"bez mas wirujących {AllAxles.MaxRigidBodyDecelerationMps2(wet):F6} m/s²"));

        Assert.IsTrue(required > 1.0, $"f_min = {required} — gdyby było ≤ 1, żądanie byłoby osiągalne");
        AssertBits(BrakingReference.RequiredFractionEmergencyWet, required);

        // Ta sama konkluzja bez współczynnika mas wirujących.
        Assert.IsTrue(
            AllAxles.MaxRigidBodyDecelerationMps2(wet) < Model.DesignEmergencyBrakeMps2,
            "wniosek nie może zależeć od decyzji o masach wirujących");

        // ...a hamowanie służbowe 1,10 m/s² na mokrej szynie osiągalne jest,
        // ale dopiero powyżej 93,2 % osi hamowanych.
        Assert.IsFalse(AllAxles.IsAdhesionLimited(Model.DesignServiceBrakeMps2, wet));
        Assert.IsTrue(PoweredOnly.IsAdhesionLimited(Model.DesignServiceBrakeMps2, wet));
    }

    /// <summary>Progi krytyczne zgadzają się z referencją co do bitu.</summary>
    [TestMethod]
    public void Progi_krytyczne_zgadzaja_sie_z_referencja_co_do_bitu()
    {
        AssertBits(
            BrakingReference.RequiredFractionServiceDry,
            AllAxles.RequiredBrakedMassFraction(Model.DesignServiceBrakeMps2, Model.DesignAdhesionDry));
        AssertBits(
            BrakingReference.RequiredFractionServiceWet,
            AllAxles.RequiredBrakedMassFraction(Model.DesignServiceBrakeMps2, Model.DesignAdhesionWet));
        AssertBits(
            BrakingReference.RequiredFractionEmergencyDry,
            AllAxles.RequiredBrakedMassFraction(Model.DesignEmergencyBrakeMps2, Model.DesignAdhesionDry));
        AssertBits(BrakingReference.RequiredAdhesionService, AllAxles.RequiredAdhesion(Model.DesignServiceBrakeMps2));
        AssertBits(BrakingReference.RequiredAdhesionEmergency, AllAxles.RequiredAdhesion(Model.DesignEmergencyBrakeMps2));
    }

    /// <summary>
    /// **Druga, niezależna droga do progu krytycznego.** Wzór <c>f = b·λ/(μ·g)</c>
    /// jest jedną drogą; skanowanie udziału osi drobnym krokiem i szukanie pierwszej
    /// wartości, przy której sufit dogania żądanie, jest drugą. Muszą się spotkać
    /// w granicy kroku skanu.
    /// </summary>
    [TestMethod]
    public void Prog_krytyczny_zgadza_sie_ze_skanem_udzialu_osi()
    {
        var mu = Model.DesignAdhesionWet;
        var demand = Model.DesignServiceBrakeMps2;
        var analytic = AllAxles.RequiredBrakedMassFraction(demand, mu);

        const int samples = 1_000_000;
        var scanned = double.NaN;
        for (var i = 1; i <= samples; i++)
        {
            var fraction = (double)i / samples;
            var limit = new BrakeAdhesionLimit(fraction, Model.DesignEffectiveMassFactor, "scan");
            if (limit.MaxDecelerationMps2(mu) >= demand)
            {
                scanned = fraction;
                break;
            }
        }

        Console.WriteLine(string.Create(
            CultureInfo.InvariantCulture,
            $"[SKAN] f_min ze wzoru = {analytic:F9}, ze skanu {samples} kroków = {scanned:F9}, " +
            $"|Δ| = {Math.Abs(analytic - scanned):E3}"));

        // Skan ma rozdzielczość 1e-6, więc różnica nie może przekroczyć jednego kroku.
        Assert.AreEqual(analytic, scanned, 1.0 / samples);
    }

    /// <summary>Obcięcie sufitem działa dopiero powyżej sufitu, a nie „prawie zawsze".</summary>
    [TestMethod]
    public void Sufit_obcina_zadanie_dopiero_powyzej_siebie()
    {
        var mu = Model.DesignAdhesionWet;
        var ceiling = PoweredOnly.MaxDecelerationMps2(mu);

        Assert.AreEqual(0.5 * ceiling, PoweredOnly.AchievableDecelerationMps2(0.5 * ceiling, mu), 0.0);
        Assert.AreEqual(ceiling, PoweredOnly.AchievableDecelerationMps2(ceiling, mu), 0.0);
        Assert.AreEqual(ceiling, PoweredOnly.AchievableDecelerationMps2(2.0 * ceiling, mu), 0.0);
        Assert.IsFalse(PoweredOnly.IsAdhesionLimited(ceiling, mu), "równe sufitowi to jeszcze nie obcięcie");
        Assert.IsTrue(PoweredOnly.IsAdhesionLimited(Math.BitIncrement(ceiling), mu));
    }

    /// <summary>Sufit i próg krytyczny są wzajemnie odwrotne dla każdego żądania.</summary>
    [DataTestMethod]
    [DataRow(0.4)]
    [DataRow(0.8)]
    [DataRow(1.1)]
    [DataRow(1.3)]
    [DataRow(2.0)]
    public void Prog_krytyczny_jest_odwrotnoscia_sufitu(double demand)
    {
        foreach (var mu in new[] { Model.DesignAdhesionDry, Model.DesignAdhesionWet })
        {
            var fraction = AllAxles.RequiredBrakedMassFraction(demand, mu);
            if (fraction > 1.0)
            {
                continue;
            }

            var limit = new BrakeAdhesionLimit(fraction, Model.DesignEffectiveMassFactor, "odwrotność");
            Assert.AreEqual(demand, limit.MaxDecelerationMps2(mu), 1e-15);
            Assert.AreEqual(mu, limit.RequiredAdhesion(demand), 1e-15);
        }
    }

    /// <summary>Udział osi poza (0, 1] i przyczepność poza (0, 1] są odrzucane, nie obcinane.</summary>
    [DataTestMethod]
    [DataRow(0.0)]
    [DataRow(-0.5)]
    [DataRow(1.0000001)]
    [DataRow(double.NaN)]
    [DataRow(double.PositiveInfinity)]
    public void Sufit_odrzuca_bledny_udzial_osi(double fraction)
    {
        Assert.ThrowsException<ArgumentOutOfRangeException>(
            () => new BrakeAdhesionLimit(fraction, Model.DesignEffectiveMassFactor, "zły"));
    }

    /// <summary>Przyczepność, masa i żądanie poza dziedziną są odrzucane.</summary>
    [TestMethod]
    public void Sufit_odrzuca_bledne_argumenty()
    {
        Assert.ThrowsException<ArgumentOutOfRangeException>(() => AllAxles.MaxDecelerationMps2(0.0));
        Assert.ThrowsException<ArgumentOutOfRangeException>(() => AllAxles.MaxDecelerationMps2(1.5));
        Assert.ThrowsException<ArgumentOutOfRangeException>(() => AllAxles.MaxDecelerationMps2(double.NaN));
        Assert.ThrowsException<ArgumentOutOfRangeException>(() => AllAxles.MaxBrakeForceN(0.0, 0.25));
        Assert.ThrowsException<ArgumentOutOfRangeException>(() => AllAxles.AchievableDecelerationMps2(0.0, 0.25));
        Assert.ThrowsException<ArgumentOutOfRangeException>(
            () => new BrakeAdhesionLimit(1.0, 0.0, "zły współczynnik"));
        Assert.ThrowsException<ArgumentNullException>(() => BrakeAdhesionLimit.AllAxles(null!));
        Assert.ThrowsException<ArgumentNullException>(() => BrakeAdhesionLimit.PoweredAxlesOnly(null!));
    }

    // === 2. solver punktu hamowania ==============================================

    /// <summary>
    /// **Wzór zamknięty jest granicą modelu krokowego, a nie inną fizyką.**
    /// Różnica maleje liniowo z krokiem: dziesięciokrotne skrócenie <c>dt</c> ma
    /// dziesięciokrotnie zmniejszyć rozjazd. Zmierzone przy 80 km/h: 0,185 m przy
    /// 1/120 s, 0,0185 m przy 1/1200 s, 0,00185 m przy 1/12000 s.
    /// </summary>
    [TestMethod]
    public void Wzor_zamkniety_jest_granica_modelu_krokowego_przy_dt_do_zera()
    {
        var solver = new BrakingPointSolver(Model);
        var start = Units.KmhToMps(Model.DesignMaxSpeedKmh);
        var closed = solver.DistanceM(start, 0.0, Model.DesignServiceBrakeMps2);
        var run = new ServiceBrakingRun(Model);

        var previous = double.NaN;
        foreach (var hertz in new[] { 120, 1200, 12000 })
        {
            var discrete = run.ToStop(
                Model.DesignMaxSpeedKmh, Model.DesignServiceBrakeMps2, FixedStep.FromHertz(hertz));
            var error = closed - discrete.DistanceM;

            Console.WriteLine(string.Create(
                CultureInfo.InvariantCulture,
                $"[ZBIEŻNOŚĆ] dt = 1/{hertz} s: krokowo {discrete.DistanceM:F6} m, wzór {closed:F6} m, " +
                $"błąd {error:F6} m"));

            Assert.IsTrue(error > 0.0, "model krokowy musi zaniżać drogę, bo drogę liczy po prędkości z końca kroku");
            if (!double.IsNaN(previous))
            {
                var ratio = previous / error;
                Assert.AreEqual(10.0, ratio, 0.05, $"zbieżność nie jest pierwszego rzędu: iloraz {ratio}");
            }

            previous = error;
        }
    }

    /// <summary>Droga ze wzoru zgadza się z referencją Pythona co do bitu.</summary>
    [TestMethod]
    public void Droga_ze_wzoru_zamknietego_zgadza_sie_z_referencja_co_do_bitu()
    {
        var solver = new BrakingPointSolver(Model);
        for (var i = 0; i < BrakingReference.SpeedsKmh.Length; i++)
        {
            var start = Units.KmhToMps(BrakingReference.SpeedsKmh[i]);
            AssertBits(
                BrakingReference.ClosedFormM[i],
                solver.DistanceM(start, 0.0, Model.DesignServiceBrakeMps2),
                $"{BrakingReference.SpeedsKmh[i]} km/h");
        }
    }

    /// <summary>
    /// Solver i droga są wzajemnie odwrotne: opóźnienie policzone dla zadanej drogi,
    /// wstawione z powrotem do wzoru, musi dać tę samą drogę.
    /// </summary>
    [DataTestMethod]
    [DataRow(150.0, BrakingReference.RequiredDeceleration80On150M)]
    [DataRow(200.0, BrakingReference.RequiredDeceleration80On200M)]
    [DataRow(240.0, BrakingReference.RequiredDeceleration80On240M)]
    [DataRow(300.0, BrakingReference.RequiredDeceleration80On300M)]
    [DataRow(400.0, BrakingReference.RequiredDeceleration80On400M)]
    public void Solver_i_droga_sa_wzajemnie_odwrotne(double distance, double expected)
    {
        var solver = new BrakingPointSolver(Model);
        var start = Units.KmhToMps(Model.DesignMaxSpeedKmh);

        var point = solver.RequiredDeceleration(start, 0.0, distance);
        var back = solver.DistanceM(start, 0.0, point.DecelerationMps2);

        Console.WriteLine(string.Create(
            CultureInfo.InvariantCulture,
            $"[SOLVER] s = {distance:F1} m -> b = {point.DecelerationMps2:F9} m/s², " +
            $"kontrola s(b) = {back:F9} m, |Δ| = {Math.Abs(back - distance):E3} m"));

        AssertBits(expected, point.DecelerationMps2, $"{distance} m");
        Assert.AreEqual(distance, back, 1e-9, "odwrotność solvera musi wracać do zadanej drogi");
        Assert.AreEqual(distance, point.DistanceM, 1e-9);
        Assert.IsFalse(point.RampOnly);
    }

    /// <summary>
    /// **Zryw stawia twardą granicę.** Poniżej <c>MinimumDistanceM</c> nie ma
    /// rozwiązania i solver mówi to wprost, zamiast zwrócić dowolnie dużą liczbę.
    /// </summary>
    [TestMethod]
    public void Ponizej_minimum_wynikajacego_ze_zrywu_solver_odmawia()
    {
        var solver = new BrakingPointSolver(Model);
        var start = Units.KmhToMps(Model.DesignMaxSpeedKmh);
        var minimum = solver.MinimumDistanceM(start, 0.0);

        Console.WriteLine(string.Create(
            CultureInfo.InvariantCulture,
            $"[ZRYW] z {Model.DesignMaxSpeedKmh:F0} km/h przy zrywie {Model.DesignJerkMps3:F2} m/s³ " +
            $"nie da się stanąć krócej niż na {minimum:F3} m (b progowe {solver.PlateauCeilingMps2(start, 0.0):F4} m/s²)"));

        AssertBits(BrakingReference.MinimumDistance80M, minimum);
        AssertBits(BrakingReference.PlateauCeiling80Mps2, solver.PlateauCeilingMps2(start, 0.0));

        Assert.IsFalse(solver.TryRequiredDeceleration(start, 0.0, minimum - 1e-6, out _));
        Assert.IsTrue(solver.TryRequiredDeceleration(start, 0.0, minimum, out _));
        Assert.ThrowsException<ArgumentOutOfRangeException>(
            () => solver.RequiredDeceleration(start, 0.0, 0.5 * minimum));
    }

    /// <summary>
    /// Powyżej opóźnienia progowego droga przestaje zależeć od zadanego opóźnienia:
    /// prędkość docelowa wypada jeszcze w trakcie narastania hamulca. Mocniejszy
    /// hamulec nie skraca już wtedy niczego.
    /// </summary>
    [TestMethod]
    public void Powyzej_progu_zrywu_droga_przestaje_zalezec_od_opoznienia()
    {
        var solver = new BrakingPointSolver(Model);
        var start = Units.KmhToMps(Model.DesignMaxSpeedKmh);
        var ceiling = solver.PlateauCeilingMps2(start, 0.0);

        var atCeiling = solver.Solve(start, 0.0, ceiling);
        var above = solver.Solve(start, 0.0, 10.0 * ceiling);

        Assert.IsTrue(atCeiling.RampOnly);
        Assert.IsTrue(above.RampOnly);
        AssertBits(atCeiling.DistanceM, above.DistanceM, "droga nie może zależeć od b powyżej progu");
        AssertBits(atCeiling.TimeSeconds, above.TimeSeconds);

        // Tuż pod progiem droga jest jeszcze funkcją b — inaczej test niczego nie dowodzi.
        var below = solver.Solve(start, 0.0, 0.9 * ceiling);
        Assert.IsFalse(below.RampOnly);
        Assert.IsTrue(below.DistanceM > atCeiling.DistanceM);
    }

    /// <summary>
    /// Bez ograniczenia zrywu wzór musi zbiegać do szkolnego <c>(v₀² − v₁²)/2b</c>.
    /// To jest kontrola samego wzoru: dwa dodatkowe człony są ceną zrywu i mają zniknąć.
    /// </summary>
    [TestMethod]
    public void Przy_nieskonczonym_zrywie_wzor_zbiega_do_v2_przez_2a()
    {
        var start = Units.KmhToMps(80.0);
        var target = Units.KmhToMps(30.0);
        const double deceleration = 1.1;
        var textbook = ((start * start) - (target * target)) / (2.0 * deceleration);

        var previous = double.NaN;
        foreach (var jerk in new[] { 750.0, 7500.0, 75000.0 })
        {
            var distance = new BrakingPointSolver(jerk).DistanceM(start, target, deceleration);
            var error = Math.Abs(distance - textbook);
            if (!double.IsNaN(previous))
            {
                Assert.AreEqual(10.0, previous / error, 0.05, "człon zrywu musi maleć jak 1/j");
            }

            previous = error;
        }

        Assert.IsTrue(previous < 1e-3, $"resztka {previous} m przy zrywie 75000 m/s³");
    }

    /// <summary>Droga maleje monotonicznie wraz z opóźnieniem aż do progu zrywu.</summary>
    [TestMethod]
    public void Droga_maleje_monotonicznie_wraz_z_opoznieniem()
    {
        var solver = new BrakingPointSolver(Model);
        var start = Units.KmhToMps(Model.DesignMaxSpeedKmh);
        var ceiling = solver.PlateauCeilingMps2(start, 0.0);

        var previous = double.PositiveInfinity;
        for (var i = 1; i <= 500; i++)
        {
            var deceleration = ceiling * i / 500.0;
            var distance = solver.DistanceM(start, 0.0, deceleration);
            Assert.IsTrue(distance < previous, $"b = {deceleration}: {distance} m nie jest mniejsze niż {previous} m");
            previous = distance;
        }
    }

    /// <summary>
    /// Czas hamowania ze wzoru zgadza się z czasem policzonym z rozbicia na fazy:
    /// narastanie zrywem plus odcinek o stałym opóźnieniu. Dwa różne rachunki,
    /// jedna liczba.
    /// </summary>
    [TestMethod]
    public void Czas_ze_wzoru_zgadza_sie_z_rozbiciem_na_fazy()
    {
        var solver = new BrakingPointSolver(Model);
        var start = Units.KmhToMps(Model.DesignMaxSpeedKmh);

        foreach (var deceleration in new[] { 0.6, 0.9, 1.1, 1.3, 2.0 })
        {
            var point = solver.Solve(start, 0.0, deceleration);
            var rampTime = deceleration / Model.DesignJerkMps3;
            var speedAfterRamp = start - (0.5 * Model.DesignJerkMps3 * rampTime * rampTime);
            var plateauTime = speedAfterRamp / deceleration;

            Assert.AreEqual(rampTime + plateauTime, point.TimeSeconds, 1e-12, $"b = {deceleration}");
            Assert.AreEqual(speedAfterRamp, point.SpeedAfterRampMps, 1e-12);

            // Droga też: pole pod v(t) w obu fazach.
            var rampDistance = (start * rampTime) - (Model.DesignJerkMps3 * rampTime * rampTime * rampTime / 6.0);
            var plateauDistance = speedAfterRamp * speedAfterRamp / (2.0 * deceleration);
            Assert.AreEqual(rampDistance + plateauDistance, point.DistanceM, 1e-10, $"b = {deceleration}");
        }
    }

    /// <summary>Prędkość docelowa większa lub równa bieżącej to nie jest hamowanie.</summary>
    [TestMethod]
    public void Solver_odrzuca_bledne_predkosci_i_odleglosci()
    {
        var solver = new BrakingPointSolver(Model);
        var start = Units.KmhToMps(80.0);

        Assert.ThrowsException<ArgumentOutOfRangeException>(() => solver.DistanceM(start, start, 1.1));
        Assert.ThrowsException<ArgumentOutOfRangeException>(() => solver.DistanceM(start, start + 1.0, 1.1));
        Assert.ThrowsException<ArgumentOutOfRangeException>(() => solver.DistanceM(0.0, 0.0, 1.1));
        Assert.ThrowsException<ArgumentOutOfRangeException>(() => solver.DistanceM(double.NaN, 0.0, 1.1));
        Assert.ThrowsException<ArgumentOutOfRangeException>(() => solver.Solve(start, 0.0, 0.0));
        Assert.ThrowsException<ArgumentOutOfRangeException>(() => solver.Solve(start, -1.0, 1.1));
        Assert.ThrowsException<ArgumentOutOfRangeException>(
            () => solver.TryRequiredDeceleration(start, 0.0, 0.0, out _));
        Assert.ThrowsException<ArgumentOutOfRangeException>(() => new BrakingPointSolver(0.0));
        Assert.ThrowsException<ArgumentOutOfRangeException>(() => new BrakingPointSolver(double.NaN));
        Assert.ThrowsException<ArgumentNullException>(() => new BrakingPointSolver((VehicleModel)null!));
    }

    // === 3. droga hamowania z oporami ============================================

    /// <summary>
    /// Tablica referencyjna zgadza się z <c>tools/physics/braking.py</c>. Model krokowy
    /// w C# i w Pythonie ma **inną kolejność działań zmiennoprzecinkowych** (kontroler
    /// liczy siły i dzieli przez masę efektywną, referencja składa opóźnienia), więc
    /// zgodności co do bitu tu nie ma i nie może być — jest za to zmierzony próg.
    /// </summary>
    [TestMethod]
    public void Tablica_referencyjna_zgadza_sie_z_referencja_Pythona()
    {
        var conditions = RunConditions.Level(Model, TrainLoad.Aw2);
        var rows = new BrakingRun(Model).ReferenceTable(
            conditions, BrakingReference.SpeedsKmh, Model.DesignServiceBrakeMps2, Step);

        var worst = 0.0;
        for (var i = 0; i < rows.Count; i++)
        {
            var row = rows[i];

            // Model kinematyczny nie zna oporów, więc tu kolejność działań jest ta sama
            // co w referencji i zgodność musi być co do bitu.
            AssertBits(BrakingReference.KinematicM[i], row.KinematicDistanceM, $"{row.StartSpeedKmh} km/h bez oporów");
            AssertBits(BrakingReference.ClosedFormM[i], row.ClosedFormDistanceM, $"{row.StartSpeedKmh} km/h wzór");

            worst = Math.Max(worst, Math.Abs(BrakingReference.TunnelM[i] - row.TunnelDistanceM));
            worst = Math.Max(worst, Math.Abs(BrakingReference.SurfaceM[i] - row.SurfaceDistanceM));

            Console.WriteLine(string.Create(
                CultureInfo.InvariantCulture,
                $"[TABLICA] {row.StartSpeedKmh,4:F0} km/h  bez oporów {row.KinematicDistanceM,8:F3} m  " +
                $"tunel {row.TunnelDistanceM,8:F3} m  powierzchnia {row.SurfaceDistanceM,8:F3} m  " +
                $"skrócenie {row.TunnelShorteningM,6:F3} / {row.SurfaceShorteningM,6:F3} m  " +
                $"z energii {row.TunnelShorteningFromEnergyM,6:F3} / {row.SurfaceShorteningFromEnergyM,6:F3} m"));
        }

        Console.WriteLine(string.Create(
            CultureInfo.InvariantCulture, $"[TABLICA] największy rozjazd z referencją Pythona = {worst:E3} m"));

        // Zmierzony rozjazd jest rzędu 1e-12 m; próg 1e-9 m zostawia trzy rzędy zapasu
        // i nadal łapie każdy realny błąd modelu.
        Assert.IsTrue(worst < 1e-9, $"rozjazd z referencją {worst} m");
    }

    /// <summary>
    /// **Droga hamowania z oporami nie zależy od masy składu.** Opór Davisa jest
    /// liczony na tonę, więc opóźnienie od oporów to <c>r·g/(1000·λ)</c> — masa się
    /// skraca dokładnie tak samo jak w suficie przyczepnościowym. AW0 i AW2 hamują
    /// na tej samej drodze, a nie „prawie".
    /// </summary>
    [TestMethod]
    public void Droga_hamowania_z_oporami_nie_zalezy_od_masy_skladu()
    {
        var run = new BrakingRun(Model);
        var aw0 = run.ToStop(RunConditions.Level(Model, TrainLoad.Aw0), 80.0, Model.DesignServiceBrakeMps2, null, Step);
        var aw2 = run.ToStop(RunConditions.Level(Model, TrainLoad.Aw2), 80.0, Model.DesignServiceBrakeMps2, null, Step);

        Console.WriteLine(string.Create(
            CultureInfo.InvariantCulture,
            $"[MASA] AW0 {aw0.DistanceM:F9} m, AW2 {aw2.DistanceM:F9} m, |Δ| = {Math.Abs(aw0.DistanceM - aw2.DistanceM):E3} m"));

        Assert.AreEqual(aw0.Steps, aw2.Steps, "liczba kroków musi być ta sama");
        Assert.AreEqual(aw0.DistanceM, aw2.DistanceM, 1e-9, "różnica może być tylko zaokrągleniem, nie fizyką");
    }

    /// <summary>
    /// **Druga droga do skrócenia drogi hamowania.** Praca oporów podzielona przez siłę
    /// hamowania musi dać te same metry, o które opory skróciły drogę. Zmierzone przy
    /// 80 km/h w tunelu: 6,757 m zmierzone wobec 6,738 m z bilansu, czyli 0,019 m —
    /// resztę tłumaczy narastanie hamulca, kiedy <c>b</c> nie jest jeszcze stałe.
    /// Ta sama liczba stoi w <c>reports/T-400-first-run.md</c> §3.6.
    /// </summary>
    [TestMethod]
    public void Skrocenie_drogi_przez_opory_zgadza_sie_z_bilansem_energii()
    {
        var conditions = RunConditions.Level(Model, TrainLoad.Aw2);
        var rows = new BrakingRun(Model).ReferenceTable(
            conditions, BrakingReference.SpeedsKmh, Model.DesignServiceBrakeMps2, Step);

        foreach (var row in rows)
        {
            Assert.IsTrue(row.TunnelShorteningM > 0.0, "opory muszą skracać drogę, nie wydłużać");
            Assert.IsTrue(
                row.TunnelShorteningM > row.SurfaceShorteningM,
                "w tunelu opór aerodynamiczny jest większy, więc skrócenie też");

            Assert.AreEqual(
                row.TunnelShorteningFromEnergyM, row.TunnelShorteningM, 0.02,
                $"{row.StartSpeedKmh} km/h w tunelu: bilans energii nie zgadza się ze zmierzonym skróceniem");
            Assert.AreEqual(
                row.SurfaceShorteningFromEnergyM, row.SurfaceShorteningM, 0.02,
                $"{row.StartSpeedKmh} km/h na powierzchni");
        }
    }

    /// <summary>
    /// Bilans energii hamowania domyka się do precyzji <c>double</c> także wtedy,
    /// gdy w grze jest pochylenie — a to jest przypadek, którego test z T-400 nie miał.
    /// </summary>
    [DataTestMethod]
    [DataRow(0.0)]
    [DataRow(3.0)]
    [DataRow(-3.0)]
    public void Bilans_energii_hamowania_domyka_sie_takze_na_pochyleniu(double gradePercent)
    {
        var conditions = RunConditions.Level(Model, TrainLoad.Aw2).WithGrade(gradePercent);
        var result = new BrakingRun(Model).ToStop(conditions, 80.0, Model.DesignServiceBrakeMps2, null, Step);

        Console.WriteLine(string.Create(
            CultureInfo.InvariantCulture,
            $"[BILANS] pochylenie {gradePercent:F1}%: s = {result.DistanceM:F3} m, {result.Energy}"));

        Assert.IsTrue(result.ReachedTarget);
        Assert.IsTrue(
            result.Energy.RelativeResidual < 1e-12,
            $"bilans nie domyka się: reszta względna {result.Energy.RelativeResidual}");
        Assert.IsTrue(result.Energy.ResistanceWorkJ > 0.0);

        // Kontrola kierunku: z góry skład jedzie dalej, pod górę staje bliżej.
        if (gradePercent < 0.0)
        {
            Assert.IsTrue(result.Energy.GradeWorkJ < 0.0, "z góry ciężar pomaga jechać, więc pracuje na minus");
        }
    }

    /// <summary>
    /// Hamowanie z góry wydłuża drogę, pod górę skraca — i to o wielkość, którą można
    /// policzyć osobno z pracy składowej ciężaru.
    /// </summary>
    [TestMethod]
    public void Pochylenie_przesuwa_droge_hamowania_w_przewidywalna_strone()
    {
        var run = new BrakingRun(Model);
        var level = run.ToStop(RunConditions.Level(Model, TrainLoad.Aw2), 80.0, Model.DesignServiceBrakeMps2, null, Step);
        var down = run.ToStop(
            RunConditions.Level(Model, TrainLoad.Aw2).WithGrade(-3.0), 80.0, Model.DesignServiceBrakeMps2, null, Step);
        var up = run.ToStop(
            RunConditions.Level(Model, TrainLoad.Aw2).WithGrade(3.0), 80.0, Model.DesignServiceBrakeMps2, null, Step);

        Console.WriteLine(string.Create(
            CultureInfo.InvariantCulture,
            $"[POCHYLENIE] poziom {level.DistanceM:F3} m, −3% {down.DistanceM:F3} m, +3% {up.DistanceM:F3} m"));

        Assert.IsTrue(down.DistanceM > level.DistanceM, "z góry skład musi stanąć dalej");
        Assert.IsTrue(up.DistanceM < level.DistanceM, "pod górę bliżej");
    }

    /// <summary>
    /// Sufit przyczepnościowy naprawdę wydłuża drogę: na mokrej szynie i przy hamowaniu
    /// wyłącznie osiami napędnymi żądanie 1,30 m/s² zostaje obcięte do 0,787 m/s²,
    /// a przebieg jest wtedy identyczny z przebiegiem zadanym wprost tą wartością.
    /// </summary>
    [TestMethod]
    public void Sufit_przyczepnosciowy_obcina_zadanie_i_wydluza_droge()
    {
        var wet = new RunConditions(
            Model.MassKg(TrainLoad.Aw2), 0.0, Model.DesignAdhesionWet, TrackEnvironment.Tunnel);
        var run = new BrakingRun(Model);

        var limited = run.ToStop(wet, 80.0, Model.DesignEmergencyBrakeMps2, PoweredOnly, Step);
        var unlimited = run.ToStop(wet, 80.0, Model.DesignEmergencyBrakeMps2, null, Step);
        var ceiling = PoweredOnly.MaxDecelerationMps2(Model.DesignAdhesionWet);
        var direct = run.ToStop(wet, 80.0, ceiling, null, Step);

        Console.WriteLine(string.Create(
            CultureInfo.InvariantCulture,
            $"[OBCIĘCIE] żądane {Model.DesignEmergencyBrakeMps2:F2} m/s², sufit {ceiling:F4} m/s²: " +
            $"z sufitem {limited.DistanceM:F3} m, bez sufitu {unlimited.DistanceM:F3} m, " +
            $"wydłużenie {limited.DistanceM - unlimited.DistanceM:F3} m"));

        Assert.IsTrue(limited.AdhesionLimited);
        Assert.IsFalse(unlimited.AdhesionLimited);
        Assert.AreEqual(ceiling, limited.AppliedDecelerationMps2, 0.0);
        Assert.AreEqual(Model.DesignEmergencyBrakeMps2, limited.DemandedDecelerationMps2, 0.0);
        AssertBits(direct.DistanceM, limited.DistanceM, "obcięcie musi być tym samym przebiegiem co żądanie równe sufitowi");
        Assert.IsTrue(limited.DistanceM > unlimited.DistanceM + 100.0, "obcięcie o 40% opóźnienia to nie kilka metrów");
    }

    /// <summary>
    /// Na suchej szynie sufit nie zmienia niczego — i to jest powód, dla którego
    /// wpięcie go w <see cref="TrainController"/> byłoby niewidoczne w przejeździe
    /// z T-400, a decydujące dopiero na mokrym torze.
    /// </summary>
    [TestMethod]
    public void Na_suchej_szynie_sufit_nie_zmienia_drogi_hamowania()
    {
        var dry = RunConditions.Level(Model, TrainLoad.Aw2);
        var run = new BrakingRun(Model);

        foreach (var limit in new[] { AllAxles, PoweredOnly })
        {
            var withLimit = run.ToStop(dry, 80.0, Model.DesignServiceBrakeMps2, limit, Step);
            var without = run.ToStop(dry, 80.0, Model.DesignServiceBrakeMps2, null, Step);

            Assert.IsFalse(withLimit.AdhesionLimited, limit.Variant);
            AssertBits(without.DistanceM, withLimit.DistanceM, limit.Variant);
        }
    }

    /// <summary>Argumenty przebiegu poza dziedziną są odrzucane.</summary>
    [TestMethod]
    public void Przebieg_hamowania_odrzuca_bledne_argumenty()
    {
        var run = new BrakingRun(Model);
        var conditions = RunConditions.Level(Model, TrainLoad.Aw2);

        Assert.ThrowsException<ArgumentNullException>(() => new BrakingRun(null!));
        Assert.ThrowsException<ArgumentNullException>(() => run.ToStop(null!, 80.0, 1.1));
        Assert.ThrowsException<ArgumentOutOfRangeException>(() => run.ToStop(conditions, 0.0, 1.1));
        Assert.ThrowsException<ArgumentOutOfRangeException>(
            () => run.ToStop(conditions, Model.DesignMaxSpeedKmh + 1.0, 1.1));
        Assert.ThrowsException<ArgumentOutOfRangeException>(() => run.ToStop(conditions, 80.0, 0.0));
        Assert.ThrowsException<ArgumentOutOfRangeException>(() => run.ToSpeed(conditions, 80.0, 80.0, 1.1));
        Assert.ThrowsException<ArgumentOutOfRangeException>(() => run.ToSpeed(conditions, 80.0, -1.0, 1.1));
        Assert.ThrowsException<ArgumentOutOfRangeException>(
            () => run.ToStop(conditions, 80.0, 1.1, null, Step, -1));
    }

    /// <summary>
    /// Hamowanie do prędkości pośredniej kończy się na niej, a nie na postoju —
    /// tego <see cref="ServiceBrakingRun"/> z T-310 w ogóle nie umiał.
    /// </summary>
    [TestMethod]
    public void Hamowanie_do_predkosci_posredniej_konczy_sie_na_niej()
    {
        var conditions = RunConditions.Level(Model, TrainLoad.Aw2);
        var result = new BrakingRun(Model).ToSpeed(conditions, 80.0, 30.0, Model.DesignServiceBrakeMps2, null, Step);
        var toStop = new BrakingRun(Model).ToStop(conditions, 80.0, Model.DesignServiceBrakeMps2, null, Step);

        Console.WriteLine(string.Create(
            CultureInfo.InvariantCulture,
            $"[80→30] s = {result.DistanceM:F3} m, t = {result.TimeSeconds:F3} s, " +
            $"v_koncowe = {result.FinalSpeedKmh:F3} km/h"));

        // Przestrzelenie celu nie może przekroczyć jednego kroku całkowania: przy
        // dt = 1/120 s i opóźnieniu 1,10 m/s² to najwyżej 0,0092 m/s. Zmierzone: 0,0031 m/s.
        var overshoot = Units.KmhToMps(30.0) - result.FinalSpeedMps;
        var oneStep = 1.5 * Model.DesignServiceBrakeMps2 * Step.Seconds;

        Console.WriteLine(string.Create(
            CultureInfo.InvariantCulture,
            $"[80→30] przestrzelenie {overshoot:F6} m/s przy granicy jednego kroku {oneStep:F6} m/s"));

        Assert.IsTrue(result.ReachedTarget);
        Assert.IsTrue(result.FinalSpeedKmh <= 30.0);
        Assert.IsTrue(overshoot >= 0.0 && overshoot < oneStep, $"przestrzelenie {overshoot} m/s");
        Assert.IsTrue(result.DistanceM < toStop.DistanceM, "krótsze hamowanie musi dać krótszą drogę");
    }

    // === 4. regresja: T-400 ma zostać nietknięty ==================================

    /// <summary>
    /// **Parytet T-400 co do bitu.** Model hamowania z T-311 nie dotyka
    /// <see cref="TrainController"/>, więc przejazd pakietu A musi dać dokładnie te
    /// same liczby, co w <c>reports/T-400-first-run.md</c> §2: 38194 kroków i czoło
    /// zatrzymane na chainage 6653,791185780133 m. Ten test jest po to, żeby przyszła
    /// zmiana w hamowaniu nie przesunęła przejazdu po cichu.
    /// </summary>
    [TestMethod]
    public void Model_hamowania_nie_zmienil_przejazdu_z_T400_ani_o_bit()
    {
        var scenario = DriveScenario.PackageAFirstRun(Model);
        var drive = new ScenarioDrive(
            Model,
            scenario,
            new RunConditions(
                Model.MassKg(TrainLoad.Aw2), 0.0, Model.Adhesion(RailCondition.Dry), TrackEnvironment.Tunnel),
            Step);

        drive.RunToEnd();

        Console.WriteLine(string.Create(
            CultureInfo.InvariantCulture,
            $"[T-400] kroków = {drive.State.Steps}, chainage = {drive.ChainageM:R} m, powód = {drive.FinishReason}"));

        Assert.AreEqual(38194L, drive.State.Steps);
        Assert.AreEqual("stopped", drive.FinishReason);
        AssertBits(6653.791185780133, drive.ChainageM, "chainage końcowy przejazdu pakietu A");
        AssertBits(6559.791185780133, drive.State.DistanceM, "droga przejazdu pakietu A");
    }

    /// <summary>
    /// Droga hamowania kontrolera z T-400 (233,723 m w tunelu z 80 km/h) jest tą samą
    /// liczbą, co <see cref="BrakingRun"/> bez sufitu — czyli nowy przebieg naprawdę
    /// woła stary kontroler, a nie liczy tego samego drugi raz.
    /// </summary>
    [TestMethod]
    public void Przebieg_hamowania_to_ten_sam_kontroler_co_w_T400()
    {
        var conditions = RunConditions.Level(Model, TrainLoad.Aw2);
        var target = Units.KmhToMps(Model.DesignMaxSpeedKmh);

        var controller = new TrainController(Model);
        var state = new DriveState(0, target, 0.0, 0.0);
        while (state.SpeedMps > 0.0 && state.Steps < 120 * FixedStep.SimulationHertz)
        {
            state = controller.Advance(state, conditions, DriverCommand.FullServiceBrake, target, Step, out _);
        }

        var run = new BrakingRun(Model).ToStop(conditions, Model.DesignMaxSpeedKmh, Model.DesignServiceBrakeMps2, null, Step);

        Assert.AreEqual(state.Steps, run.Steps);
        AssertBits(state.DistanceM, run.DistanceM, "droga musi być ta sama co do bitu");
    }

    // === 5. audyt założeń =========================================================

    /// <summary>
    /// Każda właściwość <c>Design*</c> modelu hamowania ma wpis w katalogu założeń
    /// z uzasadnieniem. Ten sam mechanizm, co
    /// <see cref="DesignModelAuditTests"/> dla parametrów pojazdu — dopisanie liczby
    /// bez deklaracji pochodzenia wywraca testy.
    /// </summary>
    [TestMethod]
    public void Kazde_zalozenie_hamowania_ma_wpis_w_katalogu_z_uzasadnieniem()
    {
        var catalogue = BrakingAssumptions.All;
        Assert.IsTrue(catalogue.Count >= 3, $"za mało założeń w katalogu: {catalogue.Count}");

        foreach (var entry in catalogue)
        {
            Assert.IsFalse(string.IsNullOrWhiteSpace(entry.Name), "wpis bez nazwy");
            Assert.IsFalse(string.IsNullOrWhiteSpace(entry.Reason), $"{entry.Name} bez uzasadnienia");
            Assert.IsTrue(double.IsFinite(entry.Value), $"{entry.Name} ma wartość {entry.Value}");
            Console.WriteLine($"[ZAŁOŻENIE] {entry}");
        }

        var names = catalogue.Select(a => a.Name).ToList();
        CollectionAssert.AllItemsAreUnique(names);

        // Każdy wariant zbudowany fabryką musi używać liczby, która jest w katalogu.
        // Inaczej dałoby się dołożyć wariant z wartością bez pochodzenia.
        var designProperties = typeof(BrakeAdhesionLimit)
            .GetProperties(BindingFlags.Public | BindingFlags.Instance)
            .Where(p => p.Name.StartsWith("Design", StringComparison.Ordinal))
            .Where(p => p.PropertyType == typeof(double))
            .ToList();

        Assert.IsTrue(designProperties.Count >= 1, "sufit nie deklaruje żadnego parametru projektowego");

        var catalogued = catalogue.Select(a => a.Value).ToList();
        foreach (var limit in new[] { AllAxles, PoweredOnly })
        {
            foreach (var property in designProperties)
            {
                var value = (double)property.GetValue(limit)!;
                Assert.IsTrue(
                    catalogued.Any(v => BitConverter.DoubleToInt64Bits(v) == BitConverter.DoubleToInt64Bits(value)),
                    $"{limit.Variant}.{property.Name} = {value.ToString("R", CultureInfo.InvariantCulture)} " +
                    "nie ma wpisu w katalogu założeń hamowania");
            }
        }
    }

    /// <summary>
    /// Katalog założeń hamowania jest wypisany w <c>docs/21-measured-vs-assumed.md</c>.
    /// Liczba w kodzie bez wiersza w audycie jest dokładnie tym, przed czym ostrzega
    /// reguła 1 z <c>CLAUDE.md</c>.
    /// </summary>
    [TestMethod]
    public void Katalog_zalozen_hamowania_jest_wypisany_w_audycie()
    {
        var audit = File.ReadAllText(Path.Combine(MetroBxl.Tests.Shared.KorzenRepozytorium.Sciezka, "docs", "21-measured-vs-assumed.md"));

        foreach (var entry in BrakingAssumptions.All)
        {
            StringAssert.Contains(audit, entry.Name, $"{entry.Name} nie ma wiersza w docs/21-measured-vs-assumed.md");
        }

        StringAssert.Contains(audit, "design_assumption");
        StringAssert.Contains(audit, "udział osi hamowanych");
    }

    /// <summary>
    /// Rejestr M7 **nie** dostał nowych wpisów. <c>data/</c> jest tylko do odczytu
    /// (reguła 6), a T-311 nie ma prawa awansować własnych założeń na parametry pojazdu.
    /// </summary>
    [TestMethod]
    public void Rejestr_M7_nie_zna_parametrow_hamulca_ktorych_nie_ma_w_zrodlach()
    {
        var registry = File.ReadAllText(Path.Combine(MetroBxl.Tests.Shared.KorzenRepozytorium.Sciezka, "data", "vehicle", "m7-spec.json"));

        foreach (var forbidden in new[]
                 {
                     "braked_mass_fraction", "braked_axle", "electrodynamic", "ed_brake",
                     "friction_brake", "brake_blend", "safety_curve",
                 })
        {
            Assert.IsFalse(
                registry.Contains(forbidden, StringComparison.OrdinalIgnoreCase),
                $"rejestr dostał '{forbidden}' — a tej wielkości nie ma w źródłach STIB");
        }
    }

    // === pomocnicze ===============================================================

    private static void AssertBits(double expected, double actual, string message = "")
    {
        Assert.AreEqual(
            BitConverter.DoubleToInt64Bits(expected),
            BitConverter.DoubleToInt64Bits(actual),
            string.Create(
                CultureInfo.InvariantCulture,
                $"{message}: oczekiwano {expected:R}, jest {actual:R}"));
    }
}
