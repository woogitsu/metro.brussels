using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using MetroBxl.Sim.Physics;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace MetroBxl.Sim.Tests;

/// <summary>
/// Audyt pochodzenia parametrów — odpowiednik <c>tools/tests/test_dimension_audit.py</c>
/// po stronie rdzenia.
///
/// Reguła 1 z <c>CLAUDE.md</c> nie działa na dobre chęci: zmyślona liczba wygląda
/// dokładnie tak samo jak prawdziwa. Dlatego każda wartość <c>design_model</c> musi
/// mieć w kodzie właściwość z przedrostkiem <c>Design</c>, wpis w
/// <see cref="VehicleModel.DesignAssumptions"/> z powodem i wpis w rejestrze.
/// Dopisanie parametru bez tego kompletu wywraca testy.
/// </summary>
[TestClass]
public sealed class DesignModelAuditTests
{
    private static readonly VehicleModel Model = VehicleModel.M7;

    private static IReadOnlyList<PropertyInfo> DesignProperties() =>
        typeof(VehicleModel)
            .GetProperties(BindingFlags.Public | BindingFlags.Instance)
            .Where(p => p.Name.StartsWith("Design", StringComparison.Ordinal))
            .Where(p => p.PropertyType == typeof(double))
            .OrderBy(p => p.Name, StringComparer.Ordinal)
            .ToList();

    [TestMethod]
    public void Kazda_wlasciwosc_Design_ma_wpis_w_katalogu_zalozen()
    {
        var properties = DesignProperties();
        Assert.IsTrue(properties.Count >= 16, $"za mało parametrów projektowych: {properties.Count}");

        foreach (var property in properties)
        {
            var entry = Model.DesignAssumptions.SingleOrDefault(a => a.Name == property.Name);
            Assert.AreNotEqual(default, entry, $"{property.Name} nie ma wpisu w DesignAssumptions");
            Assert.AreEqual((double)property.GetValue(Model)!, entry.Value, 0.0, property.Name);
            Assert.IsFalse(string.IsNullOrWhiteSpace(entry.Reason), $"{property.Name} nie ma uzasadnienia");
        }
    }

    [TestMethod]
    public void Katalog_zalozen_nie_zawiera_nic_ponad_wlasciwosci_Design()
    {
        var propertyNames = DesignProperties().Select(p => p.Name).ToHashSet(StringComparer.Ordinal);
        var catalogueNames = Model.DesignAssumptions.Select(a => a.Name).ToList();

        CollectionAssert.AllItemsAreUnique(catalogueNames);
        foreach (var name in catalogueNames)
        {
            Assert.IsTrue(propertyNames.Contains(name), $"katalog wymienia nieistniejącą właściwość {name}");
        }
    }

    /// <summary>
    /// Każdy wpis katalogu wskazuje na wpis rejestru o statusie <c>design_model</c>.
    /// Awans wartości na <c>spec</c> bez źródła nie przejdzie po cichu.
    /// </summary>
    [TestMethod]
    public void Kazdy_wpis_katalogu_wskazuje_parametr_design_model_w_rejestrze()
    {
        foreach (var assumption in Model.DesignAssumptions)
        {
            var entry = VehicleRegistry.M7.Get(assumption.RegistryPath);
            Assert.AreEqual(ParameterStatus.DesignModel, entry.Status, assumption.RegistryPath);
        }
    }

    /// <summary>
    /// I w drugą stronę: żaden parametr <c>design_model</c> z rejestru nie może zostać
    /// pominięty. Dopisanie nowego założenia do <c>data/vehicle/m7-spec.json</c> bez
    /// zadeklarowania go w modelu wywraca ten test.
    /// </summary>
    [TestMethod]
    public void Kazdy_parametr_design_model_z_rejestru_jest_zadeklarowany_w_modelu()
    {
        var declared = Model.DesignAssumptions.Select(a => a.RegistryPath).ToHashSet(StringComparer.Ordinal);
        var inRegistry = VehicleRegistry.M7.PathsWithStatus(ParameterStatus.DesignModel);

        var missing = inRegistry.Where(path => !declared.Contains(path)).ToList();
        Assert.AreEqual(0, missing.Count, "parametry design_model bez deklaracji w modelu: " + string.Join(", ", missing));
        Assert.AreEqual(18, inRegistry.Count, "zmieniła się liczba założeń projektowych w rejestrze");
    }

    /// <summary>
    /// 6.D124: rejestr niesie flagę <c>approximate</c> i rdzeń ją CZYTA — bo wypis
    /// <c>Sim.Runner braking</c> jest porównywany <c>diff</c>em co do bitu
    /// z niezależną referencją <c>tools/physics/braking.py</c>, a tamta ją wypisuje.
    /// Wpis jest dziś dokładnie jeden i wchodzi do modelu jako masa AW0.
    /// </summary>
    [TestMethod]
    public void Rejestr_mowi_ktora_wartosc_jest_przyblizona_i_rdzen_to_czyta()
    {
        var approximate = VehicleRegistry.M7.ApproximateEntries();

        Assert.AreEqual(1, approximate.Count,
            "zmieniła się liczba wartości oznaczonych w rejestrze jako przybliżone");
        Assert.AreEqual("parameters.empty_mass_kg", approximate[0].Path);
        Assert.AreEqual(Model.EmptyMassKg, approximate[0].RequireNumber(),
            "przybliżony wpis rejestru to nie jest ta masa, którą model naprawdę bierze");
        StringAssert.Contains(approximate[0].Notes, "approximately",
            "wpis stracił notatkę, a to ona mówi, CO jest przybliżone i z czyjej ręki");

        // Kontrola przyrządu: flaga jest CZYTANA, a nie zwracana dla wszystkiego.
        // Bez tego lista „wszystkich wpisów" wyglądałaby tak samo przy jednym wpisie
        // w rejestrze — a wpisów jest kilkadziesiąt.
        Assert.IsTrue(VehicleRegistry.M7.Paths.Count > approximate.Count,
            "lista przybliżonych obejmuje wszystkie wpisy — flaga nie jest czytana");
        Assert.IsFalse(VehicleRegistry.M7.Get("reference_model.jerk_mps3").IsApproximate,
            "założenie projektowe bez flagi zostało policzone jako przybliżone");
    }

    [TestMethod]
    public void Wartosci_spec_maja_zrodlo_pierwotne_z_adresem()
    {
        foreach (var path in VehicleRegistry.M7.PathsWithStatus(ParameterStatus.Spec))
        {
            var entry = VehicleRegistry.M7.Get(path);
            Assert.IsNotNull(entry.SourceId, path);
            CollectionAssert.Contains(VehicleRegistry.M7.SourceIds.ToList(), entry.SourceId, path);
        }
    }

    /// <summary>
    /// Parametry, których audyt T-904 nie potwierdził źródłem pierwotnym, mają
    /// zostać <c>design_model</c>. To ten sam warunek, którego po stronie Pythona
    /// pilnuje <c>test_unverified_m7_values_are_not_spec</c>.
    /// </summary>
    [DataTestMethod]
    [DataRow("parameters.max_speed_kmh")]
    [DataRow("parameters.powered_mass_fraction")]
    [DataRow("reference_model.aw2_model_mass_kg")]
    [DataRow("reference_model.startup_force_n")]
    [DataRow("reference_model.force_power_transition_speed_kmh")]
    public void Niepotwierdzone_wartosci_nie_awansuja_do_spec(string path) =>
        Assert.AreEqual(ParameterStatus.DesignModel, VehicleRegistry.M7.Get(path).Status, path);

    [TestMethod]
    public void Masa_modelowa_AW2_to_masa_pusta_plus_pasazerowie()
    {
        Assert.AreEqual(
            Model.EmptyMassKg + (Model.DesignAw2Passengers * Model.DesignPassengerMassKg),
            Model.DesignAw2MassKg,
            1e-6);
        Assert.AreEqual(221_940.0, Model.MassKg(TrainLoad.Aw2), 1e-6);
        Assert.AreEqual(170_000.0, Model.MassKg(TrainLoad.Aw0), 0.0);
    }

    /// <summary>
    /// Zasób osadzony w assembly musi być tym samym plikiem co canonical registry w
    /// <c>data/</c>. Inaczej rdzeń liczyłby po cichu z kopii sprzed zmiany danych.
    /// </summary>
    [TestMethod]
    public void Osadzony_rejestr_jest_identyczny_z_plikiem_w_data()
    {
        var repoRoot = MetroBxl.Tests.Shared.KorzenRepozytorium.SciezkaAlboNull;
        if (repoRoot is null)
        {
            Assert.Inconclusive("Test uruchomiony poza drzewem repozytorium — nie ma z czym porównać.");
            return;
        }

        var onDisk = File.ReadAllText(Path.Combine(repoRoot, "data", "vehicle", "m7-spec.json"));
        Assert.AreEqual(onDisk, VehicleRegistry.ReadEmbeddedJson());
    }

    [TestMethod]
    public void Rejestr_opisuje_M7_i_ma_date_audytu()
    {
        Assert.AreEqual("M7", VehicleRegistry.M7.VehicleId);
        Assert.AreEqual(1, VehicleRegistry.M7.SchemaVersion);
        Assert.IsFalse(string.IsNullOrWhiteSpace(VehicleRegistry.M7.AsOf));
    }
}
