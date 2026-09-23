using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text.RegularExpressions;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace MetroBxl.Game.Tests;

/// <summary>
/// Panel interfejsu mieści się w widoku przy KAŻDEJ rozdzielczości — 6.D82.
///
/// <para><b>Skąd.</b> Do 10.09.2026 panel miał kotwicę w lewym dolnym rogu
/// i <c>offset_right = 900.0</c>, czyli szerokość STAŁĄ 876 px niezależnie od widoku.
/// Zmierzone zrzutami z silnika przy kilometrażu 2054 m, gdzie stoi
/// <c>Comte de Flandre|Graaf van Vlaanderen</c> — najdłuższa nazwa stacji w danych
/// osi (37 znaków):</para>
/// <code>
/// 1280 x 720   „… Comte de Flandre|Graaf van Vlaanderen za 1 m"   (całe)
///  800 x 600   „… Comte de Flandre|Graaf van Vlaanderen za 1"     (UCIĘTE)
/// </code>
/// <para>Ucięta jest jednostka, a przy dłuższej odległości ucięte byłyby cyfry.
/// Gracz przy węższym widoku nie odczyta, ile zostało do peronu — to utrata
/// informacji sterującej, nie wygląd.</para>
///
/// <para><b>Czego te testy NIE mierzą i dlaczego.</b> Prostokątów ETYKIET nie da się
/// tu policzyć: ich szerokość zależy od metryk czcionki, a te zna wyłącznie silnik,
/// którego <c>dotnet test</c> nie uruchamia. Mierzalne jest to, co rozstrzyga:
/// prostokąt panelu wyliczony z kotwic tak, jak liczy go Godot, oraz to, że wiersz
/// pozycji ZAWIJA — bo etykieta zawijająca wewnątrz kontenera nie może być szersza
/// od niego, więc jej zmieszczenie wynika ze zmieszczenia panelu. Sam kadr został
/// obejrzany i opisany w <c>reports/6d82-panel-w-weszym-widoku.md</c>; test pilnuje,
/// żeby arytmetyka pod nim nie wróciła do stałej szerokości.</para>
/// </summary>
[TestClass]
public sealed class HudLayoutTests
{
    /// <summary>Rozdzielczości z pola „Skończone, gdy" pozycji 6.D82.</summary>
    private static readonly (int W, int H)[] Widoki =
    {
        (800, 600), (1280, 720), (1920, 1080),
    };

    /// <summary>
    /// Prostokąt węzła <c>Control</c> liczony tak, jak liczy go Godot:
    /// <c>lewa = anchor_left * szerokość + offset_left</c>, i tak dla każdej krawędzi.
    /// </summary>
    private static (double L, double T, double R, double B) Rect(
        IReadOnlyDictionary<string, double> node, int width, int height)
    {
        double A(string name, double fallback) => node.TryGetValue(name, out var v) ? v : fallback;
        return (A("anchor_left", 0.0) * width + A("offset_left", 0.0),
                A("anchor_top", 0.0) * height + A("offset_top", 0.0),
                A("anchor_right", 0.0) * width + A("offset_right", 0.0),
                A("anchor_bottom", 0.0) * height + A("offset_bottom", 0.0));
    }

    /// <summary>Właściwości liczbowe węzła sceny o podanej nazwie.</summary>
    private static Dictionary<string, double> NodeProperties(string scene, string nodeName)
    {
        var start = scene.IndexOf($"[node name=\"{nodeName}\"", StringComparison.Ordinal);
        Assert.IsTrue(start >= 0, $"nie znalazłem węzła `{nodeName}` w scenie");
        var next = scene.IndexOf("\n[node ", start + 1, StringComparison.Ordinal);
        var block = next < 0 ? scene[start..] : scene[start..next];

        var found = new Dictionary<string, double>(StringComparer.Ordinal);
        foreach (Match m in Regex.Matches(block, @"(?m)^([a-z_]+) = (-?[0-9.]+)$"))
        {
            found[m.Groups[1].Value] = double.Parse(m.Groups[2].Value, CultureInfo.InvariantCulture);
        }

        return found;
    }

    private static string Scene() =>
        File.ReadAllText(Path.Combine(MetroBxl.Tests.Shared.KorzenRepozytorium.Sciezka, "src", "Game", "Scenes", "FirstRun.tscn"));

    [TestMethod]
    public void Panel_miesci_sie_w_widoku_dla_kazdej_z_trzech_rozdzielczosci()
    {
        var panel = NodeProperties(Scene(), "Panel");

        foreach (var (w, h) in Widoki)
        {
            var (l, t, r, b) = Rect(panel, w, h);
            Assert.IsTrue(l >= 0.0, $"{w}x{h}: panel wychodzi poza lewą krawędź ({l})");
            Assert.IsTrue(t >= 0.0, $"{w}x{h}: panel wychodzi poza górną krawędź ({t})");
            Assert.IsTrue(r <= w, $"{w}x{h}: panel sięga do x={r}, czyli POZA widok — "
                                  + "to jest dokładnie usterka 6.D82");
            Assert.IsTrue(b <= h, $"{w}x{h}: panel sięga do y={b}, czyli poza widok");
            Assert.IsTrue(r > l, $"{w}x{h}: panel ma niedodatnią szerokość ({l}..{r})");
        }
    }

    [TestMethod]
    public void Odstep_od_obu_krawedzi_jest_ten_sam_i_nie_zalezy_od_rozdzielczosci()
    {
        // To odróżnia POPRAWKĘ od jej pozoru: panel przesunięty w lewo też mieściłby
        // się w widoku, ale przy 1920 px zostawiłby 1000 px pustki z prawej. Kotwica
        // musi być OBUSTRONNA, a odstęp — stały.
        var panel = NodeProperties(Scene(), "Panel");
        var odstepy = new List<(int W, double Lewy, double Prawy)>();

        foreach (var (w, h) in Widoki)
        {
            var (l, _t, r, _b) = Rect(panel, w, h);
            odstepy.Add((w, l, w - r));
        }

        foreach (var (w, lewy, prawy) in odstepy)
        {
            Assert.AreEqual(lewy, prawy, 1e-9,
                $"{w} px: odstęp z lewej {lewy} != odstęp z prawej {prawy}");
        }

        Assert.AreEqual(1, odstepy.Select(o => o.Prawy).Distinct().Count(),
            "odstęp od prawej krawędzi zmienia się z rozdzielczością — to znaczy, że "
            + "prawa kotwica nie jest przypięta do krawędzi widoku");
    }

    [TestMethod]
    public void Wiersz_pozycji_zawija_bo_to_on_niesie_nazwe_stacji()
    {
        // Etykieta bez zawijania jest UCINANA przez kontener, a nie zwężana — więc
        // samo zmieszczenie panelu nie wystarcza. Zmierzone: to wiersz pozycji niósł
        // ucięty tekst na zrzucie 800 x 600.
        var scene = Scene();
        var start = scene.IndexOf("[node name=\"Position\" type=\"Label\"", StringComparison.Ordinal);
        Assert.IsTrue(start >= 0, "nie znalazłem wiersza pozycji w scenie");
        var next = scene.IndexOf("\n[node ", start + 1, StringComparison.Ordinal);
        var block = next < 0 ? scene[start..] : scene[start..next];

        var tryb = Regex.Match(block, @"(?m)^autowrap_mode = ([0-9]+)$");
        Assert.IsTrue(tryb.Success,
            "wiersz pozycji nie ma `autowrap_mode` — długa nazwa stacji zostanie UCIĘTA, "
            + "a nie zawinięta");
        var wartosc = int.Parse(tryb.Groups[1].Value, CultureInfo.InvariantCulture);
        Assert.AreNotEqual(0, wartosc, "`autowrap_mode = 0` to zawijanie WYŁĄCZONE");
        Assert.IsTrue(wartosc >= 2,
            $"`autowrap_mode = {wartosc}`: nazwa dwujęzyczna `Comte de Flandre|Graaf van "
            + "Vlaanderen` nie ma spacji przy pionowej kresce, więc potrzebne jest "
            + "zawijanie po słowach (2) albo mądre (3)");
    }

    [TestMethod]
    public void Sygnalizacja_zawija_zamiast_rozszerzac_panel_recznego_postoju()
    {
        Assert.IsTrue(Regex.IsMatch(Scene(),
                @"\[node name=""Signalling"" type=""Label"" parent=""Hud/Panel/Rows""\]\r?\nautowrap_mode = 3\r?\n"),
            "długi autorytet jazdy rozszerza panel i ucina początek wskazówki drzwi przy 800x600");
    }

    [TestMethod]
    public void Najdluzsza_nazwa_stacji_z_danych_jest_ta_ktora_zmierzono()
    {
        // Pole „Skończone, gdy" mówi o NAJDŁUŻSZEJ nazwie z danych osi. Gdyby doszła
        // dłuższa, pomiar ze zrzutów przestałby dotyczyć najgorszego przypadku —
        // i ten test jest miejscem, w którym to widać, zamiast po cichu.
        var root = MetroBxl.Tests.Shared.KorzenRepozytorium.Sciezka;
        var najdluzsza = "";
        var stacji = 0;
        foreach (var plik in Directory.GetFiles(Path.Combine(root, "data", "track"), "*.json"))
        {
            foreach (Match m in Regex.Matches(File.ReadAllText(plik), "\"name\"\\s*:\\s*\"([^\"]*)\""))
            {
                stacji++;
                if (m.Groups[1].Value.Length > najdluzsza.Length)
                {
                    najdluzsza = m.Groups[1].Value;
                }
            }
        }

        Assert.IsTrue(stacji >= 60, $"skan widzi {stacji} nazw stacji — rozjechał się z danymi");
        Assert.AreEqual("Comte de Flandre|Graaf van Vlaanderen", najdluzsza,
            "najdłuższa nazwa stacji w danych osi zmieniła się — pomiar ze zrzutów "
            + "6.D82 dotyczył tej, więc trzeba go powtórzyć dla nowej");
    }
}
