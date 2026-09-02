using System;
using System.Globalization;
using System.IO;
using System.Linq;
using MetroBxl.Sim.Line;
using MetroBxl.Sim.Physics;
using MetroBxl.Sim.Signalling;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace MetroBxl.Sim.Tests;

/// <summary>
/// Plan bloków pakietu A: co jest w pliku, skąd się wzięło i czego w nim nie ma.
///
/// <para>Te testy pilnują **pochodzenia**, a nie liczb. Granice bloków to
/// <c>design_model</c>; przypięcie ich tutaj na sztywno przypięłoby zgadywanie.
/// Przypięta jest za to reguła, z której powstały, i to, że plik nie udaje danych STIB.</para>
/// </summary>
[TestClass]
public sealed class SignallingPlanTests
{
    private const string AxisId = "L1_A";

    private static string RepositoryRoot()
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

        Assert.Inconclusive("Test uruchomiony poza drzewem repozytorium.");
        throw new InvalidOperationException();
    }

    private static string PlanPath() =>
        Path.Combine(RepositoryRoot(), "data", "design", "signalling", "classic-2026.json");

    internal static SignallingPlan PackageAPlan() => SignallingPlan.FromFile(PlanPath());

    internal static TrackAxis PackageAAxis() =>
        TrackAxis.FromJson(File.ReadAllText(
            Path.Combine(RepositoryRoot(), "data", "track", AxisId + ".json")));

    /// <summary>Oś syntetyczna o zadanych kilometrażach stacji — wzorowana na LineRunTests.</summary>
    internal static TrackAxis SyntheticAxis(params double[] stationChainages)
    {
        var length = stationChainages[^1] + 100.0;
        var stations = string.Join(",", stationChainages.Select((c, i) => string.Create(
            CultureInfo.InvariantCulture,
            $$"""{"name":"S{{i}}","chainage_m":{{c.ToString("R", CultureInfo.InvariantCulture)}},"stop_id":"P{{i}}"}""")));
        return TrackAxis.FromJson(string.Create(
            CultureInfo.InvariantCulture,
            $$"""
            {"id":"T","length_m":0.0,"vertical":{"status":"not_modelled"},
             "points":[[0.0,0.0,0.0],[{{length.ToString("R", CultureInfo.InvariantCulture)}},0.0,0.0]],
             "stations":[{{stations}}]}
            """), 0.0);
    }

    /// <summary>Plan syntetyczny: ta sama reguła, krótsza oś, sterowalny wymóg trasy.</summary>
    internal static SignallingPlan SyntheticPlan(bool requireRoute, params double[] stationChainages) =>
        SignallingPlan.FromAxis(
            SyntheticAxis(stationChainages),
            VehicleRegistry.M7.RequireValue("parameters.length_m", ParameterStatus.Spec),
            Units.KmhToMps(72.0),
            0.0,
            ProtectionVariant.LegacyFixedBlock,
            requireRoute);

    /// <summary>Ten sam plan z NIEZEROWYM zapasem za końcem authority.</summary>
    internal static SignallingPlan SyntheticPlanWithMargin(
        double authorityMarginM, params double[] stationChainages) =>
        SignallingPlan.FromAxis(
            SyntheticAxis(stationChainages),
            VehicleRegistry.M7.RequireValue("parameters.length_m", ParameterStatus.Spec),
            Units.KmhToMps(72.0),
            authorityMarginM,
            ProtectionVariant.LegacyFixedBlock,
            false);

    // --- pochodzenie ---------------------------------------------------------------

    [TestMethod]
    public void Plan_pakietu_A_jest_design_model_w_calosci()
    {
        var plan = PackageAPlan();

        Assert.AreEqual(ParameterStatus.DesignModel, plan.Status, "plan bez źródła nie może mieć innego statusu");
        Assert.AreEqual("classic_2026", plan.Mode);
        Assert.AreEqual(AxisId, plan.AxisId);
        CollectionAssert.Contains(
            plan.UnknownParameters.ToList(),
            "exact fixed-block boundaries and lengths",
            "plik musi sam mówić, czego nie wie");
    }

    /// <summary>
    /// Pakiet A leży na linii 1. KCV jest potwierdzony przez STIB **wyłącznie** dla
    /// linii 2 i 6 (<c>kcv_lines_2_6</c>), więc plan pakietu A nie ma prawa go deklarować.
    /// </summary>
    [TestMethod]
    public void Plan_pakietu_A_nie_deklaruje_KCV()
    {
        var plan = PackageAPlan();
        Assert.AreEqual(ProtectionVariant.LegacyFixedBlock, plan.Variant);

        var protection = new TrainProtection(plan, VehicleModel.M7);
        Assert.ThrowsException<InvalidOperationException>(protection.RequireKcv);
    }

    [TestMethod]
    public void Loader_odrzuca_plan_awansowany_do_spec_bez_zrodla()
    {
        var json = File.ReadAllText(PlanPath()).Replace(
            "\"status\": \"design_model\"", "\"status\": \"spec\"", StringComparison.Ordinal);
        Assert.AreNotEqual(File.ReadAllText(PlanPath()), json, "podmiana statusu w teście nie zadziałała");

        var error = Assert.ThrowsException<FormatException>(() => SignallingPlan.FromJson(json));
        StringAssert.Contains(error.Message, "source_id");
    }

    [TestMethod]
    public void Loader_odrzuca_gola_liczbe_bez_deklaracji_pochodzenia()
    {
        var json = File.ReadAllText(PlanPath())
            .Replace("\"authority_margin_m\": {", "\"authority_margin_m_disabled\": {", StringComparison.Ordinal)
            .Replace(
                "\"require_route\": true,",
                "\"require_route\": true, \"authority_margin_m\": 0.0,",
                StringComparison.Ordinal);

        var error = Assert.ThrowsException<FormatException>(() => SignallingPlan.FromJson(json));
        StringAssert.Contains(error.Message, "skąd pochodzi");
    }

    // --- spójność planu -------------------------------------------------------------

    [TestMethod]
    public void Bloki_sa_ciagle_rozlaczne_i_pokrywaja_cala_os()
    {
        var plan = PackageAPlan();
        var axis = PackageAAxis();

        Assert.AreEqual(0.0, plan.StartM, 0.0, "plan musi zaczynać się na początku osi");
        Assert.IsTrue(plan.EndM >= axis.LengthM, $"plan kończy się na {plan.EndM:F3} m, oś na {axis.LengthM:F3} m");

        for (var i = 1; i < plan.Blocks.Count; i++)
        {
            Assert.AreEqual(plan.Blocks[i - 1].EndM, plan.Blocks[i].StartM, 1e-9,
                $"dziura albo zakładka między {plan.Blocks[i - 1].Id} a {plan.Blocks[i].Id}");
        }

        foreach (var block in plan.Blocks)
        {
            Assert.IsTrue(block.LengthM > 0.0, $"{block.Id} ma niedodatnią długość");
        }

        CollectionAssert.AllItemsAreUnique(plan.Blocks.Select(b => b.Id).ToArray());
    }

    [TestMethod]
    public void Kazda_stacja_osi_ma_swoj_blok_peronowy()
    {
        var plan = PackageAPlan();
        var axis = PackageAAxis();

        Assert.AreEqual(axis.Stations.Count, plan.Blocks.Count(b => b.IsPlatform));
        foreach (var station in axis.Stations)
        {
            var block = plan.BlockAt(station.ChainageM);
            Assert.IsTrue(block.IsPlatform, $"{station.Name} na {station.ChainageM:F2} m wypada w bloku {block.Id}");
            Assert.AreEqual(station.Name, block.StationName);
        }
    }

    [TestMethod]
    public void Trasy_wskazuja_istniejace_bloki_i_sasiednie_trasy_sa_w_konflikcie()
    {
        var plan = PackageAPlan();
        Assert.AreEqual(plan.Blocks.Count(b => b.IsPlatform) - 1, plan.Routes.Count);

        foreach (var route in plan.Routes)
        {
            Assert.IsTrue(plan.HasBlock(route.FromBlockId), route.Id);
            Assert.IsTrue(plan.HasBlock(route.ToBlockId), route.Id);
            Assert.AreEqual(route.FromBlockId, route.BlockIds[0], route.Id);
            Assert.AreEqual(route.ToBlockId, route.BlockIds[^1], route.Id);
        }

        for (var i = 1; i < plan.Routes.Count; i++)
        {
            Assert.IsTrue(
                plan.Routes[i - 1].ConflictsWith(plan.Routes[i]),
                $"{plan.Routes[i - 1].Id} i {plan.Routes[i].Id} powinny dzielić blok peronowy");
        }

        Assert.IsFalse(
            plan.Routes[0].ConflictsWith(plan.Routes[2]),
            "trasy oddalone o dwa perony nie mają wspólnego bloku");
    }

    // --- reguła generowania ----------------------------------------------------------

    /// <summary>
    /// Plik w <c>data/design/signalling/</c> ma być **wynikiem reguły**, a nie ręczną
    /// tabelką. Ten test jest jedynym miejscem, w którym reguła jest przypięta do
    /// bieżącego planu — gdy pojawi się plan ze źródłem, ten test się kasuje razem
    /// z podmianą pliku, a reszta kodu zostaje bez zmian.
    /// </summary>
    [TestMethod]
    public void Plik_planu_jest_dokladnie_tym_co_daje_regula_generowania()
    {
        var expected = SignallingPlan.FromAxis(
            PackageAAxis(),
            VehicleRegistry.M7.RequireValue("parameters.length_m", ParameterStatus.Spec),
            Units.KmhToMps(72.0),
            0.0,
            ProtectionVariant.LegacyFixedBlock,
            requireRoute: true);

        Assert.AreEqual(expected.ToJson(), File.ReadAllText(PlanPath()));
    }

    /// <summary>Wczytanie i zapis muszą dać ten sam plik — inaczej loader coś z niego gubi.</summary>
    [TestMethod]
    public void Wczytanie_i_zapis_planu_daja_ten_sam_plik()
    {
        var onDisk = File.ReadAllText(PlanPath());
        Assert.AreEqual(onDisk, SignallingPlan.FromJson(onDisk).ToJson());
    }

    [TestMethod]
    public void Dlugosc_bloku_peronowego_pochodzi_z_rejestru_M7_a_nie_z_kodu()
    {
        var plan = PackageAPlan();
        Assert.AreEqual(
            VehicleRegistry.M7.RequireValue("parameters.length_m", ParameterStatus.Spec),
            plan.PlatformBlockLengthM,
            0.0);

        foreach (var block in plan.Blocks.Where(b => b.IsPlatform && b.StartM > 0.0))
        {
            Assert.AreEqual(plan.PlatformBlockLengthM, block.LengthM, 1e-9, block.Id);
        }
    }

    /// <summary>
    /// Reguła musi odmówić, gdy międzystacja jest krótsza niż blok peronowy — inaczej
    /// dwa perony zachodziłyby na siebie i plan przestałby być ciągły.
    /// </summary>
    [TestMethod]
    public void Regula_odmawia_gdy_stacje_sa_blizej_niz_dlugosc_skladu()
    {
        var error = Assert.ThrowsException<ArgumentOutOfRangeException>(
            () => SyntheticPlan(requireRoute: false, 0.0, 80.0, 500.0));
        StringAssert.Contains(error.Message, "zachodzą na siebie");
    }

    [TestMethod]
    public void Katalog_zalozen_planu_wymienia_kazdy_parametr_bez_zrodla()
    {
        var plan = PackageAPlan();
        var names = plan.Assumptions.Select(a => a.Name).ToList();

        CollectionAssert.AllItemsAreUnique(names);
        CollectionAssert.Contains(names, "block_boundaries");
        CollectionAssert.Contains(names, "PermittedSpeedMps");
        CollectionAssert.Contains(names, "AuthorityMarginM");
        CollectionAssert.Contains(names, "route_conflict_rule");

        foreach (var assumption in plan.Assumptions)
        {
            Assert.IsFalse(string.IsNullOrWhiteSpace(assumption.Reason), assumption.Name);
        }
    }

    /// <summary>
    /// Kontrola sensowności planu, której nie da się zrobić przez zapatrzenie się
    /// w liczby: **najkrótszy blok szlakowy musi być dłuższy niż droga hamowania
    /// z prędkości planu**. Inaczej skład, który wjechał do bloku poprzedzającego zajęty,
    /// nie miałby jak się przed nim zatrzymać, a plan bloków byłby wewnętrznie sprzeczny
    /// z krzywą z T-311.
    ///
    /// <para>Bloki peronowe świadomie **nie** są tym objęte: mają długość jednego składu
    /// i skład nigdy nie wjeżdża do nich z prędkością liniową — prędkość dopuszczalna na
    /// authority równym blokowi peronowemu wychodzi z krzywej i jest od niej dużo niższa.</para>
    /// </summary>
    [TestMethod]
    public void Najkrotszy_blok_szlakowy_miesci_droge_hamowania_z_predkosci_planu()
    {
        var plan = PackageAPlan();
        var protection = new TrainProtection(plan, VehicleModel.M7);
        var braking = protection.BrakingDistanceM(plan.PermittedSpeedMps);
        var shortest = plan.Blocks.Where(b => !b.IsPlatform).OrderBy(b => b.LengthM).First();

        Assert.IsTrue(
            shortest.LengthM > braking,
            $"{shortest.Id} ma {shortest.LengthM:F2} m, a droga hamowania z " +
            $"{Units.MpsToKmh(plan.PermittedSpeedMps):F1} km/h to {braking:F2} m");
    }

    /// <summary>
    /// Zapas za końcem authority jest zerem i ma nim zostać, dopóki nie ma źródła.
    /// Test istnieje po to, żeby wpisanie tam „bezpiecznych 20 m" nie przeszło po cichu.
    /// </summary>
    [TestMethod]
    public void Zapas_za_koncem_authority_jest_zerem_bo_nie_ma_dla_niego_zrodla() =>
        Assert.AreEqual(0.0, PackageAPlan().AuthorityMarginM, 0.0);

    [TestMethod]
    public void Predkosc_planu_lezy_powyzej_zmierzonego_dolnego_ograniczenia_z_T_401()
    {
        // reports/R-006-line-speed.md §7: 58,75 km/h to jedyna liczba o prędkości
        // liniowej, która ma w tym repo wyprowadzenie — dolne ograniczenie z rozkładu.
        var kmh = Units.MpsToKmh(PackageAPlan().PermittedSpeedMps);
        Assert.IsTrue(kmh >= 58.75, $"{kmh:F2} km/h nie wystarcza na rozkład zmierzony w T-113");
        Assert.IsTrue(kmh <= VehicleModel.M7.DesignMaxSpeedKmh, $"{kmh:F2} km/h powyżej prędkości konstrukcyjnej M7");
    }
}
