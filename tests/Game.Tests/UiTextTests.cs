using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.RegularExpressions;
using MetroBxl.Game.UI;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace MetroBxl.Game.Tests;

/// <summary>
/// Katalog tekstów interfejsu jest kompletny, a w metodach HUD-u nie ma słów — 6.D83.
///
/// <para><b>Skąd.</b> Zmierzone 09.09.2026 i przeliczone 10.09.2026: trzy napisy
/// interfejsu niosły cztery słowa językowe wpisane wprost w ciało <c>Hud.Update</c>,
/// a przeszukanie warstwy gry pod wywołania funkcji tłumaczącej, pliki katalogu
/// tekstów i sekcję <c>[internationalization]</c> dało <b>zero</b> trafień.</para>
/// </summary>
[TestClass]
public sealed class UiTextTests
{
    /// <summary>Napisy w <c>Hud.cs</c>, które NIE są tekstem dla człowieka.</summary>
    private static readonly string[] NieJestTekstem =
    {
        // Nazwy właściwości motywu Godota — API silnika, nie słowa interfejsu.
        "font_size", "font_color",
    };

    private static string HudSource() =>
        File.ReadAllText(Path.Combine(RepositoryRoot(), "src", "Game", "UI", "Hud.cs"));

    /// <summary>Kod pliku bez komentarzy — komentarze WOLNO pisać po polsku.</summary>
    private static string KodBezKomentarzy(string source) =>
        string.Join("\n", source.Split('\n')
            .Where(l => !l.TrimStart().StartsWith("//", StringComparison.Ordinal)));

    private static List<string> Literaly(string kod) =>
        Regex.Matches(kod, "\"((?:[^\"\\\\]|\\\\.)*)\"")
             .Select(m => m.Groups[1].Value).ToList();

    [TestMethod]
    public void Kazdy_klucz_wolany_przez_HUD_jest_w_katalogu_domyslnym()
    {
        var wolane = Regex.Matches(HudSource(), "UiText\\.(?:Format|Get)\\(\\s*\"([^\"]+)\"")
                          .Select(m => m.Groups[1].Value).Distinct().ToList();

        Assert.IsTrue(wolane.Count >= 2,
            $"skan widzi {wolane.Count} wywołań katalogu w `Hud.cs` — wzorzec rozjechał "
            + "się z kodem, więc pętla niżej sprawdzałaby nic");

        foreach (var klucz in wolane)
        {
            Assert.IsTrue(UiText.Keys.Contains(klucz),
                $"HUD woła klucz `{klucz}`, którego katalog ({UiText.DefaultLanguage}) nie zna");
        }
    }

    [TestMethod]
    public void Katalog_nie_ma_wpisow_martwych()
    {
        // Wpis, którego nikt nie woła, jest zdaniem o interfejsie, które przestało być
        // prawdziwe — ta sama choroba, co martwa stała z 6.B29.
        var wolane = Regex.Matches(HudSource(), "UiText\\.(?:Format|Get)\\(\\s*\"([^\"]+)\"")
                          .Select(m => m.Groups[1].Value).ToHashSet(StringComparer.Ordinal);

        foreach (var klucz in UiText.Keys)
        {
            Assert.IsTrue(wolane.Contains(klucz),
                $"katalog ma klucz `{klucz}`, którego nikt nie woła — zdejmij go albo użyj");
        }
    }

    [TestMethod]
    public void Brak_klucza_jest_bledem_a_nie_napisem_z_nazwa_klucza()
    {
        // Tego wprost żąda pole „Skończone, gdy": usunięcie używanego klucza ma
        // WYWRÓCIĆ test, a nie wyświetlić cicho nazwę klucza. Katalog zwracający
        // `hud.position` wygląda na ekranie jak usterka tekstu i tak też zostaje
        // zgłoszony — po dwóch dniach i przez kogoś innego.
        var wyjatek = Assert.ThrowsException<KeyNotFoundException>(
            () => UiText.Get("hud.nie-ma-takiego"));
        StringAssert.Contains(wyjatek.Message, "hud.nie-ma-takiego");
        StringAssert.Contains(wyjatek.Message, UiText.DefaultLanguage);
    }

    [TestMethod]
    public void W_metodach_HUD_nie_ma_ani_jednego_literalu_jezykowego()
    {
        var kod = KodBezKomentarzy(HudSource());
        var zle = new List<string>();

        foreach (var literal in Literaly(kod))
        {
            if (literal.Contains('/', StringComparison.Ordinal))
            {
                continue;                       // ścieżka węzła sceny
            }

            if (NieJestTekstem.Contains(literal, StringComparer.Ordinal))
            {
                continue;                       // nazwa właściwości motywu
            }

            if (UiText.Keys.Contains(literal))
            {
                continue;                       // klucz katalogu, nie słowo
            }

            // Słowo to co najmniej dwie litery pod rząd. Jednostki i separatory
            // (`   `, `[`, `]`) zostają — pole „Skończone, gdy" mówi wprost, że
            // jednostki i formaty liczb zostają.
            if (Regex.IsMatch(literal, @"\p{L}{2,}"))
            {
                zle.Add(literal);
            }
        }

        Assert.AreEqual(0, zle.Count,
            "w `Hud.cs` stoi literał językowy zamiast klucza katalogu: "
            + string.Join(" | ", zle.Select(z => $"\"{z}\"")));
    }

    [TestMethod]
    public void Skan_literalow_widzi_te_ktore_sa_i_nie_bierze_sciezki_wezla_za_slowo()
    {
        // Kontrola przyrządu: pusta lista wyżej byłaby zielona także wtedy, gdyby
        // wzorzec przestał cokolwiek łapać albo gdyby odsianie odsiewało wszystko.
        var kod = KodBezKomentarzy(HudSource());
        var literaly = Literaly(kod);
        Assert.IsTrue(literaly.Count >= 10,
            $"skan widzi {literaly.Count} literałów w `Hud.cs` — wzorzec się rozjechał");
        Assert.IsTrue(literaly.Any(l => l.Contains("Panel/Rows", StringComparison.Ordinal)),
            "skan nie widzi ścieżek węzłów, więc nie ma czego odsiewać");
        Assert.IsTrue(literaly.Contains("font_size"),
            "skan nie widzi nazw właściwości motywu");

        // I że wzorzec „słowa" NAPRAWDĘ łapie słowo: to on rozstrzyga cały test wyżej.
        Assert.IsTrue(Regex.IsMatch("chainage {0} m", @"\p{L}{2,}"));
        Assert.IsTrue(Regex.IsMatch("ciąg {0}", @"\p{L}{2,}"));
        Assert.IsFalse(Regex.IsMatch("   ", @"\p{L}{2,}"));
        Assert.IsFalse(Regex.IsMatch("{0} m / {1} m", @"\p{L}{2,}"),
            "sama jednostka `m` nie jest słowem — jednostki mają zostać");
    }

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
}
