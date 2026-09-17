using System;
using System.Text.Json;
using MetroBxl.Sim.Json;
using MetroBxl.Sim.Line;
using MetroBxl.Sim.Signalling;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace MetroBxl.Sim.Tests;

/// <summary>
/// 6.D233. Dokument bez wymaganego pola jest ODMOWĄ czytnika, a nie zrzutem
/// środowiska uruchomieniowego.
/// </summary>
/// <remarks>
/// Zmierzone 17.09.2026 przed zmianą: <c>axis --axis &lt;plik o treści {}&gt;</c>
/// kończyło się <b>kodem 134</b> z wypisem <c>Unhandled exception.
/// KeyNotFoundException</c> i stosem. Miarą NIE jest przejście tych testów na
/// dokumentach poprawnych — te przechodziły i przed zmianą; miarą jest zachowanie
/// na dokumencie niepełnym.
/// </remarks>
[TestClass]
public sealed class RequiredFieldTests
{
    /// <summary>Komunikat ma nazwać POLE — to jedyna informacja, po którą sięga poprawiający plik.</summary>
    [TestMethod]
    public void Brak_pola_nazywa_pole_i_nie_jest_KeyNotFoundException()
    {
        using var document = JsonDocument.Parse("{\"a\": 1}");
        var error = Assert.ThrowsException<FormatException>(
            () => document.RootElement.RequiredField("b", "dokument"),
            "brak pola konczy sie KeyNotFoundException, czyli kodem 134");
        StringAssert.Contains(error.Message, "'b'", "komunikat nie nazywa pola: " + error.Message);
        StringAssert.Contains(error.Message, "dokument", "komunikat nie nazywa wlasciciela: " + error.Message);
    }

    /// <summary>Właściciel, który obiektem nie jest, też jest odmową formatu, a nie <c>InvalidOperationException</c>.</summary>
    [TestMethod]
    public void Wlasciciel_ktory_nie_jest_obiektem_jest_odmowa_formatu()
    {
        using var document = JsonDocument.Parse("[1, 2]");
        var error = Assert.ThrowsException<FormatException>(
            () => document.RootElement.RequiredField("b", "dokument"),
            "wlasciciel nie bedacy obiektem daje InvalidOperationException bez nazwy pola");
        StringAssert.Contains(error.Message, "'b'", "komunikat nie nazywa pola: " + error.Message);
    }

    /// <summary>Pole obecne wraca nietknięte — osłona nie zmienia drogi poprawnej.</summary>
    [TestMethod]
    public void Pole_obecne_wraca_nietkniete()
    {
        using var document = JsonDocument.Parse("{\"a\": 7}");
        Assert.AreEqual(
            7,
            JsonFields.RequiredField(document.RootElement, "a", "dokument").GetInt32(),
            "osłona zmienia drogę poprawną");
    }

    /// <summary>Oś bez <c>points</c>: odmowa z nazwą pola zamiast <c>KeyNotFoundException</c>.</summary>
    [TestMethod]
    public void Os_bez_points_konczy_sie_odmowa_a_nie_zrzutem()
    {
        var error = Assert.ThrowsException<FormatException>(
            () => TrackAxis.FromJson("{}"), "os bez points konczy sie zrzutem, a nie odmowa");
        StringAssert.Contains(error.Message, "'points'", "komunikat nie nazywa pola: " + error.Message);
    }

    /// <summary>Stacja osi bez <c>chainage_m</c> — pole zagnieżdżone, nie wierzchnie.</summary>
    [TestMethod]
    public void Stacja_osi_bez_chainage_konczy_sie_odmowa()
    {
        const string json =
            "{\"points\": [[0,0,0],[10,0,0]], \"stations\": [{\"name\": \"X\"}]}";
        var error = Assert.ThrowsException<FormatException>(
            () => TrackAxis.FromJson(json), "pole ZAGNIEZDZONE zostalo poza oslona");
        StringAssert.Contains(error.Message, "'chainage_m'", "komunikat nie nazywa pola: " + error.Message);
    }

    /// <summary>Strefa testowa bez <c>schema_version</c>: czytnik BEZ osłony przed 6.D233.</summary>
    [TestMethod]
    public void Strefa_testowa_bez_pola_konczy_sie_odmowa()
    {
        var error = Assert.ThrowsException<FormatException>(
            () => CbtcTestArea.FromJson("{}"), "czytnik strefy nie mial osłony przed 6.D233");
        StringAssert.Contains(error.Message, "'schema_version'", "komunikat nie nazywa pola: " + error.Message);
    }

    /// <summary>
    /// Plan bloków: osłona `Required` obejmowała WYŁĄCZNIE pola wierzchnie, więc blok
    /// bez <c>start_m</c> przechodził przez nią i kończył się zrzutem.
    /// </summary>
    [TestMethod]
    public void Blok_planu_bez_pola_konczy_sie_odmowa_a_nie_zrzutem()
    {
        var plan = SignallingPlanFixture.WithBlockMissing("start_m");
        var error = Assert.ThrowsException<FormatException>(
            () => SignallingPlan.FromJson(plan),
            "oslona `Required` obejmowala WYLACZNIE pola wierzchnie");
        StringAssert.Contains(error.Message, "'start_m'", "komunikat nie nazywa pola: " + error.Message);
    }

    private static class SignallingPlanFixture
    {
        internal static string WithBlockMissing(string field)
        {
            var text = System.IO.File.ReadAllText(RepoFile("data/design/signalling/classic-2026.json"));
            using var document = JsonDocument.Parse(text);
            var buffer = new System.IO.MemoryStream();
            using (var writer = new Utf8JsonWriter(buffer))
            {
                writer.WriteStartObject();
                foreach (var property in document.RootElement.EnumerateObject())
                {
                    if (property.Name != "blocks")
                    {
                        property.WriteTo(writer);
                        continue;
                    }

                    writer.WritePropertyName("blocks");
                    writer.WriteStartArray();
                    var first = true;
                    foreach (var block in property.Value.EnumerateArray())
                    {
                        writer.WriteStartObject();
                        foreach (var inner in block.EnumerateObject())
                        {
                            if (first && inner.Name == field)
                            {
                                continue;
                            }

                            inner.WriteTo(writer);
                        }

                        writer.WriteEndObject();
                        first = false;
                    }

                    writer.WriteEndArray();
                }

                writer.WriteEndObject();
            }

            return System.Text.Encoding.UTF8.GetString(buffer.ToArray());
        }

        private static string RepoFile(string relative)
        {
            var directory = AppContext.BaseDirectory;
            while (directory is not null
                   && !System.IO.File.Exists(System.IO.Path.Combine(directory, "MetroBxl.sln")))
            {
                directory = System.IO.Directory.GetParent(directory)?.FullName;
            }

            Assert.IsNotNull(directory, "nie znaleziono korzenia repozytorium");
            return System.IO.Path.Combine(directory!, relative);
        }
    }
}
