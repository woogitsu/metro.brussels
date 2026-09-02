using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using MetroBxl.Sim.Line;
using MetroBxl.Sim.Physics;
using MetroBxl.Sim.Signalling;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace MetroBxl.Sim.Tests;

/// <summary>
/// T-314: tryby ochrony pociągu i strefa testowa CBTC.
///
/// <para>Kryterium ukończenia brzmi: „tryb CBTC nie jest aktywny w scenariuszu
/// historycznym 31.08.2026 bez potwierdzenia pełnego uruchomienia STIB". Te testy
/// sprawdzają, że odpowiedź na to pytanie jest CZYTANA Z DANYCH, a nie zakodowana:
/// gdyby ktoś przestawił <c>cbtc_lines_1_5_full_service</c> na <c>true</c> albo dopisał
/// <c>historical_default</c> do trybu CBTC, ma się to zatrzymać tutaj.</para>
/// </summary>
[TestClass]
public sealed class ProtectionModeTests
{
    private static readonly DateOnly HistoricalScenario = new(2026, 8, 31);

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

    private static string GroundTruthPath() =>
        Path.Combine(RepositoryRoot(), "data", "signalling", "ground-truth.json");

    private static string AreaPath() =>
        Path.Combine(RepositoryRoot(), "data", "design", "signalling", "cbtc-test-2026.json");

    private static CbtcTestArea Area() => CbtcTestArea.FromJson(File.ReadAllText(AreaPath()));

    // --- tryb historyczny ------------------------------------------------------------

    /// <summary>Główne kryterium T-314, postawione wprost.</summary>
    [TestMethod]
    public void Scenariusz_historyczny_31_08_2026_nie_jest_CBTC()
    {
        var mode = ProtectionModeRegistry.Current.ForHistoricalDate(HistoricalScenario);

        Assert.AreEqual("classic_2026", mode.Id);
        Assert.IsFalse(mode.IsCbtc, "tryb historyczny nie może być trybem CBTC");
        Assert.AreEqual(ProtectionModeStatus.OperationalBaseline, mode.Status);
        Assert.IsTrue(mode.HistoricalDefault);
    }

    /// <summary>
    /// Odpowiedź ma pochodzić z faktu, a nie z nazwy trybu. Fakt
    /// <c>cbtc_lines_1_5_full_service</c> jest tym, który ją niesie, i musi być
    /// wymieniony przy trybie historycznym — inaczej rejestr twierdzi coś, czego
    /// nie umie wskazać w źródle.
    /// </summary>
    [TestMethod]
    public void Tryb_historyczny_powoluje_sie_na_fakt_o_braku_ruchu_pasazerskiego_CBTC()
    {
        var mode = ProtectionModeRegistry.Current.HistoricalDefault;
        CollectionAssert.Contains(mode.SourceFactIds.ToList(), "cbtc_lines_1_5_full_service");

        using var document = JsonDocument.Parse(File.ReadAllText(GroundTruthPath()));
        var fact = document.RootElement.GetProperty("facts").EnumerateArray()
            .Single(f => f.GetProperty("id").GetString() == "cbtc_lines_1_5_full_service");

        Assert.IsFalse(fact.GetProperty("value").GetBoolean(),
            "gdyby STIB uruchomił CBTC na 1 i 5, ten test ma zmusić do zmiany scenariusza, " +
            "a nie przepuścić starą odpowiedź");
        Assert.AreEqual("observed", fact.GetProperty("status").GetString());
    }

    [TestMethod]
    public void Zaden_tryb_CBTC_nie_jest_domyslny_historycznie()
    {
        var cbtc = ProtectionModeRegistry.Current.ModeIds
            .Select(ProtectionModeRegistry.Current.Named)
            .Where(mode => mode.IsCbtc)
            .ToList();

        Assert.IsTrue(cbtc.Count >= 3, "rejestr ma znać tryb testowy i dwa przyszłe");
        foreach (var mode in cbtc)
        {
            Assert.IsFalse(mode.HistoricalDefault, mode.Id);
            Assert.AreNotEqual(ProtectionModeStatus.OperationalBaseline, mode.Status, mode.Id);
        }

        Assert.AreEqual(1, ProtectionModeRegistry.Current.ModeIds
            .Select(ProtectionModeRegistry.Current.Named)
            .Count(mode => mode.HistoricalDefault),
            "dokładnie jeden tryb historyczny");
    }

    /// <summary>
    /// Za <c>as_of</c> rejestr nie odpowiada. Plany wdrożenia — Jacques Brel/Merode do
    /// końca 2026, Herrmann-Debroux na początku 2027 — są w ground truth opisane
    /// wprost jako plany, a <c>limitations</c> mówi: „a plan is not proof of
    /// commissioning". Zwracanie dla nich trybu byłoby zgadywaniem.
    /// </summary>
    [TestMethod]
    public void Poza_data_weryfikacji_rejestr_odmawia_zamiast_zgadywac()
    {
        var registry = ProtectionModeRegistry.Current;
        Assert.AreEqual(new DateOnly(2026, 8, 31), registry.AsOf);

        Assert.IsNotNull(registry.ForHistoricalDate(registry.AsOf));
        Assert.IsNotNull(registry.ForHistoricalDate(registry.AsOf.AddDays(-1)));
        Assert.ThrowsException<ArgumentOutOfRangeException>(
            () => registry.ForHistoricalDate(registry.AsOf.AddDays(1)));
        Assert.ThrowsException<ArgumentOutOfRangeException>(
            () => registry.ForHistoricalDate(new DateOnly(2027, 6, 1)));
    }

    /// <summary>
    /// Dwie drogi do trybu są rozdzielone celowo: <c>Named</c> daje dowolny tryb do
    /// scenariuszy „co by było gdyby", a strażnik jest miejscem, w którym scenariusz
    /// deklaruje, że jest historyczny. Gdyby wybór szedł jedną ścieżką z parametrem,
    /// przypadkowe włączenie CBTC w przejeździe historycznym byłoby odległe
    /// o jedną literówkę.
    /// </summary>
    [TestMethod]
    public void Straznik_scenariusza_historycznego_odrzuca_kazdy_tryb_CBTC()
    {
        var registry = ProtectionModeRegistry.Current;

        registry.RequireHistorical(registry.Named("classic_2026"), HistoricalScenario);

        var refused = 0;
        foreach (var id in registry.ModeIds)
        {
            var mode = registry.Named(id);
            if (!mode.IsCbtc)
            {
                continue;
            }

            var error = Assert.ThrowsException<InvalidOperationException>(
                () => registry.RequireHistorical(mode, HistoricalScenario), id);
            StringAssert.Contains(error.Message, "cbtc_lines_1_5_full_service");
            refused++;
        }

        Assert.IsTrue(refused >= 3, $"odrzucono {refused} trybów CBTC");
    }

    [TestMethod]
    public void Nieznany_tryb_jest_bledem_a_nie_trybem_domyslnym()
    {
        Assert.ThrowsException<KeyNotFoundException>(
            () => ProtectionModeRegistry.Current.Named("cbtc_wczoraj"));
        Assert.ThrowsException<FormatException>(
            () => ProtectionModeStatusParser.Parse("mniej_wiecej"));
    }

    [TestMethod]
    public void Kazdy_stan_trybu_parsuje_sie_na_siebie()
    {
        foreach (ProtectionModeStatus status in Enum.GetValues<ProtectionModeStatus>())
        {
            var text = ProtectionModeStatusParser.ToGroundTruthString(status);
            Assert.AreEqual(status, ProtectionModeStatusParser.Parse(text), text);
        }

        Assert.AreEqual(ProtectionModeStatus.OperationalBaseline,
            ProtectionModeStatusParser.Parse("operational_baseline"));
        Assert.AreEqual(ProtectionModeStatus.InstallationAndValidation,
            ProtectionModeStatusParser.Parse("installation_and_validation"));
        Assert.AreEqual(ProtectionModeStatus.FutureScenario,
            ProtectionModeStatusParser.Parse("future_scenario"));
        Assert.AreEqual(3, Enum.GetValues<ProtectionModeStatus>().Length,
            "doszedł stan wdrożenia — rozstrzygnij, czy wolno mu być historycznym");
    }

    // --- rejestr kontra plik ---------------------------------------------------------

    /// <summary>Zasób osadzony i plik w <c>data/</c> to ma być jedna kopia, nie dwie.</summary>
    [TestMethod]
    public void Osadzony_ground_truth_jest_tym_samym_plikiem_co_w_data()
    {
        Assert.AreEqual(
            File.ReadAllText(GroundTruthPath()).Replace("\r\n", "\n", StringComparison.Ordinal),
            ProtectionModeRegistry.ReadEmbeddedJson().Replace("\r\n", "\n", StringComparison.Ordinal));
    }

    /// <summary>Tryb nie może powoływać się na fakt, którego w rejestrze nie ma.</summary>
    [TestMethod]
    public void Kazdy_fakt_wskazany_przez_tryb_istnieje_w_ground_truth()
    {
        using var document = JsonDocument.Parse(ProtectionModeRegistry.ReadEmbeddedJson());
        var known = document.RootElement.GetProperty("facts").EnumerateArray()
            .Select(f => f.GetProperty("id").GetString() ?? string.Empty)
            .ToHashSet(StringComparer.Ordinal);

        var missing = new List<string>();
        foreach (var id in ProtectionModeRegistry.Current.ModeIds)
        {
            var mode = ProtectionModeRegistry.Current.Named(id);
            Assert.IsTrue(mode.SourceFactIds.Count > 0, $"{id}: tryb bez ani jednego faktu");
            missing.AddRange(mode.SourceFactIds.Where(fact => !known.Contains(fact))
                .Select(fact => $"{id} -> {fact}"));
        }

        CollectionAssert.AreEqual(new List<string>(), missing);
    }

    /// <summary>
    /// Tryby CBTC muszą nadal wypisywać, czego symulator NIE ma.
    ///
    /// <para>To nie jest ozdoba: ten PR dodaje warstwę trybów i zasięg strefy testowej,
    /// a nie model CBTC. Algorytm movement authority, bufor ochronny i krzywe ATO
    /// zostają niezaimplementowane, bo nie ma ich w żadnym źródle. Lista
    /// <c>design_model_required</c> jest jedynym miejscem, w którym ta dziura jest
    /// widoczna — wyczyszczenie jej wyglądałoby jak ukończenie pracy.</para>
    /// </summary>
    [TestMethod]
    public void Tryby_CBTC_nadal_wypisuja_czego_symulator_nie_ma()
    {
        var future = ProtectionModeRegistry.Current.Named("cbtc_future");
        CollectionAssert.IsSubsetOf(
            new[] { "movement_authority_algorithm", "protective_buffer", "ato_curves", "degraded_modes" },
            future.DesignModelRequired.ToList());

        var test = ProtectionModeRegistry.Current.Named("cbtc_test");
        CollectionAssert.IsSubsetOf(
            new[] { "test_area_boundaries_in_sim", "radio_protocol", "positioning_accuracy", "safety_buffers" },
            test.DesignModelRequired.ToList());
        Assert.IsFalse(test.PassengerServiceNetworkWide,
            "tryb testowy nie jest ruchem pasażerskim w skali sieci");
    }

    /// <summary>
    /// ATS jest osobną warstwą nadzoru i **nie wolno mu omijać ochrony pociągu** —
    /// to zdanie stoi wprost w <c>ats_transition.simulation_abstraction</c>. Warstwa
    /// trybów nie może więc wystawiać niczego, czym dałoby się prowadzić skład.
    /// </summary>
    [TestMethod]
    public void Warstwa_trybow_nie_wystawia_zadnej_drogi_omijajacej_ochrone()
    {
        var members = typeof(ProtectionMode).GetMembers()
            .Concat(typeof(ProtectionModeRegistry).GetMembers())
            .Concat(typeof(CbtcTestArea).GetMembers())
            .Select(member => member.Name)
            .ToList();

        foreach (var forbidden in new[] { "Authority", "PermittedSpeed", "BrakeDemand", "Supervise" })
        {
            Assert.IsFalse(members.Any(name => name.Contains(forbidden, StringComparison.Ordinal)),
                $"warstwa trybów wystawia '{forbidden}' — ATS nie ma prawa omijać ochrony pociągu " +
                "(data/signalling/ground-truth.json: ats_transition)");
        }
    }

    // --- strefa testowa --------------------------------------------------------------

    [TestMethod]
    public void Strefa_testowa_jest_design_model_i_nalezy_do_znanego_trybu()
    {
        var area = Area();

        Assert.AreEqual(ParameterStatus.DesignModel, area.Status,
            "granice strefy nie mają źródła — awans na spec jest zabroniony");
        Assert.AreEqual("cbtc_test", area.ModeId);
        Assert.IsNotNull(ProtectionModeRegistry.Current.Named(area.ModeId));
        Assert.AreEqual(ProtectionModeRegistry.Current.AsOf, area.AsOf);
        CollectionAssert.Contains(area.SourceFactIds.ToList(), "cbtc_test_erasme_stockel");
    }

    [TestMethod]
    public void Loader_strefy_odrzuca_awans_do_spec_bez_zrodla()
    {
        var json = File.ReadAllText(AreaPath()).Replace(
            "\"status\": \"design_model\"", "\"status\": \"spec\"", StringComparison.Ordinal);
        Assert.AreNotEqual(File.ReadAllText(AreaPath()), json, "podmiana statusu w teście nie zadziałała");
        Assert.ThrowsException<FormatException>(() => CbtcTestArea.FromJson(json));
    }

    [TestMethod]
    public void Etapy_testow_ida_w_kolejnosci_ze_zrodla()
    {
        CollectionAssert.AreEqual(
            new[] { CbtcTestStage.StaticCommunications, CbtcTestStage.DynamicTrainRunning },
            Area().Stages.ToArray(),
            "najpierw łączność statyczna, potem jazda — cbtc_test_method_and_beekkant.test_sequence");
    }

    /// <summary>
    /// Rozpoczęcie testów dynamicznych zostaje ETYKIETĄ, a nie datą.
    ///
    /// <para>Źródło mówi „koniec maja 2026" i „lato 2026". Zamiana tego na
    /// <c>DateOnly</c> wymagałaby wybrania dnia, którego nikt nie opublikował.</para>
    /// </summary>
    [TestMethod]
    public void Rozpoczecie_testow_dynamicznych_nie_udaje_daty()
    {
        var area = Area();
        Assert.IsTrue(area.IsDynamicTestSite("Beekkant"));
        Assert.IsFalse(area.IsDynamicTestSite("Merode"));

        var beekkant = area.DynamicTestSites.Single(site => site.StationName == "Beekkant");
        Assert.AreEqual("started_late_may_2026", beekkant.StartedLabel);
        StringAssert.StartsWith(beekkant.StartedDateStatus, "unknown");

        foreach (var site in area.DynamicTestSites)
        {
            Assert.IsFalse(DateOnly.TryParse(site.StartedLabel, out _),
                $"{site} — etykieta nie może dać się przeczytać jako data");
            StringAssert.StartsWith(site.StartedDateStatus, "unknown", site.ToString());
        }
    }

    /// <summary>
    /// Rzut strefy na pakiet A musi być PRZYCIĘTY i musi to powiedzieć.
    ///
    /// <para>Odcinek testowy jest opisany stacjami końcowymi linii 1 i 5 — Erasme
    /// i Stockel. Pakiet A biegnie z Gare de l'Ouest do Merode, więc żadnej z tych
    /// dwóch stacji na nim nie ma. „Strefa pokrywa całą oś" i „oś kończy się przed
    /// granicą strefy" to dwie różne rzeczy i nie wolno ich zapisać tą samą liczbą.</para>
    /// </summary>
    [TestMethod]
    public void Zasieg_strefy_na_pakiecie_A_jest_przyciety_i_mowi_to_wprost()
    {
        var axis = SignallingPlanTests.PackageAAxis();
        var names = axis.Stations.Select(station => station.Name).ToList();
        CollectionAssert.DoesNotContain(names, "Erasme|Erasmus");
        CollectionAssert.DoesNotContain(names, "Stockel|Stokkel");
        CollectionAssert.Contains(names, "Beekkant");

        var span = Area().OnAxis(axis);

        Assert.IsTrue(span.ClippedAtStart, "Erasme leży poza pakietem A");
        Assert.IsTrue(span.ClippedAtEnd, "Stockel leży poza pakietem A");
        Assert.IsTrue(span.IsClipped);
        Assert.AreEqual(0.0, span.StartM, 0.0);
        Assert.AreEqual(axis.LengthM, span.EndM, 1e-9);
        Assert.AreEqual(axis.Id, span.AxisId);
    }

    /// <summary>
    /// Gdy obie stacje SĄ na osi, przycięcia nie ma i granice są ich kilometrażem.
    /// Bez tego testu flagi przycięcia mogłyby być zawsze prawdziwe i nikt by nie
    /// zauważył.
    /// </summary>
    [TestMethod]
    public void Zasieg_na_osi_zawierajacej_obie_stacje_nie_jest_przyciety()
    {
        var axis = SignallingPlanTests.PackageAAxis();
        var first = axis.Stations[0];
        var last = axis.Stations[^1];

        var json = File.ReadAllText(AreaPath())
            .Replace("\"from_station\": \"Erasme|Erasmus\"",
                     $"\"from_station\": {JsonSerializer.Serialize(first.Name)}", StringComparison.Ordinal)
            .Replace("\"to_station\": \"Stockel|Stokkel\"",
                     $"\"to_station\": {JsonSerializer.Serialize(last.Name)}", StringComparison.Ordinal);
        Assert.AreNotEqual(File.ReadAllText(AreaPath()), json, "podmiana stacji w teście nie zadziałała");

        var span = CbtcTestArea.FromJson(json).OnAxis(axis);

        Assert.IsFalse(span.ClippedAtStart);
        Assert.IsFalse(span.ClippedAtEnd);
        Assert.IsFalse(span.IsClipped);
        Assert.AreEqual(first.ChainageM, span.StartM, 1e-9);
        Assert.AreEqual(last.ChainageM, span.EndM, 1e-9);
    }

    /// <summary>
    /// Strefa musi wypisywać dokładnie te niewiadome, które ground truth przypisuje
    /// trybowi <c>cbtc_test</c>. Skrócenie tej listy wyglądałoby jak zdobycie danych.
    /// </summary>
    [TestMethod]
    public void Strefa_wypisuje_niewiadome_swojego_trybu()
    {
        var area = Area();
        var mode = ProtectionModeRegistry.Current.Named(area.ModeId);

        CollectionAssert.IsSubsetOf(mode.DesignModelRequired.ToList(), area.UnknownParameters.ToList());
        CollectionAssert.IsSubsetOf(
            new[]
            {
                "CBTC/KCV radio or telegram formats, frequencies and network topology",
                "exact balise/localiser parameters and positioning algorithm",
            },
            area.UnknownParameters.ToList());
    }
}
