using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.RegularExpressions;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace MetroBxl.Game.Tests;

/// <summary>
/// Każdy czytnik TREŚCI pliku w <c>src/Game/</c> ma domkniętą drogę błędu dla pliku
/// ZŁEGO, a nie tylko dla brakującego (6.D235).
///
/// <para><b>Dlaczego bramka czyta źródło, a nie uruchamia czytników.</b> Przejście
/// testów warstwy gry było zielone z osłoną i bez niej — testy wołają czytniki na
/// plikach poprawnych, a osłona jest w <c>FirstRun</c>, którego bez silnika nie da się
/// uruchomić. Pytanie „czy wywołanie stoi w bloku <c>try</c>" jest za to własnością
/// tekstu i da się je zadać bez Godota.</para>
///
/// <para><b>Co liczy się jako osłona.</b> Blok <c>try</c> obejmujący wywołanie albo
/// odczyt przez <c>TryParse</c>, który błędu nie rzuca, tylko go zwraca. Filtr
/// <c>catch</c> nie jest tu sprawdzany: jego typy pilnuje
/// <c>BrokenJsonRefusalTests.ZlapieFiltrFirstRun</c> po stronie rdzenia.</para>
///
/// <para><b>Rozpoznanie bloku idzie po WCIĘCIU, nie po nawiasach</b> — i to jest wybór
/// z powodu, nie wygoda. Licznik nawiasów musiałby pomijać literały, a literał
/// interpolowany niesie nawiasy klamrowe w dziurach i cudzysłowy wewnątrz nich;
/// czytnik, który się na tym pomyli, zgłosi osłonę tam, gdzie jej nie ma. Kod tego
/// repozytorium jest formatowany jednolicie (cztery spacje, klamra w osobnym wierszu),
/// więc wcięcie jednoznacznie wskazuje nagłówek bloku.</para>
/// </summary>
[TestClass]
public sealed class FileReadGuardTests
{
    /// <summary>Wywołania, które czytają TREŚĆ pliku — nie jego obecność.</summary>
    private const string Czytnik =
        @"\.GetAsText\s*\(|\bFile\.ReadAll(?:Text|Lines|Bytes)\s*\(|\bFileAccess\.GetFileAs(?:String|Bytes)\s*\(";

    /// <summary>
    /// Czytniki zmierzone 24.09.2026, jako wywołanie, które dostaje treść. Zbiór, nie
    /// liczba (6.D131): liczba przeszłaby po zamianie jednego czytnika na inny.
    /// </summary>
    private static readonly string[] CzytnikiZmierzone =
    {
        "ChunkManifest.FromJson",
        "InputLog.Parse",
        "JsonDocument.Parse",
        "SignallingPlan.FromJson",
        "TelemetryTrack.TryParse",
        "TrackAxis.FromJson",
        "tailAxisFile.GetAsText",
    };

    private static List<string> PlikiCsWarstwyGry() =>
        Directory.GetFiles(Path.Combine(MetroBxl.Tests.Shared.KorzenRepozytorium.Sciezka, "src", "Game"), "*.cs",
                SearchOption.AllDirectories)
            .Where(p => !p.Split(Path.DirectorySeparatorChar).Contains(".godot"))
            .Where(p => !p.Split(Path.DirectorySeparatorChar).Contains("obj"))
            .Where(p => !p.Split(Path.DirectorySeparatorChar).Contains("bin"))
            .OrderBy(p => p, StringComparer.Ordinal)
            .ToList();

    private static int Wciecie(string wiersz) => wiersz.Length - wiersz.TrimStart(' ').Length;

    /// <summary>
    /// Czy wiersz <paramref name="indeks"/> leży w bloku <c>try</c>. Idzie w górę po
    /// coraz płytszych klamrach otwierających i pyta o nagłówek każdej; kończy na
    /// poziomie składowej klasy (wcięcie cztery), bo dalej bloków metody już nie ma.
    /// </summary>
    private static bool WBlokuTry(string[] wiersze, int indeks)
    {
        var poziom = Wciecie(wiersze[indeks]);
        for (var k = indeks - 1; k > 0; k--)
        {
            var wiersz = wiersze[k];
            if (wiersz.Trim() != "{" || Wciecie(wiersz) >= poziom)
            {
                continue;
            }

            poziom = Wciecie(wiersz);
            if (wiersze[k - 1].Trim() == "try")
            {
                return true;
            }

            if (poziom <= 4)
            {
                return false;
            }
        }

        return false;
    }

    /// <summary>Każdy czytnik treści pliku: (plik, wiersz, wywołanie, rodzaj osłony).</summary>
    private static List<(string Plik, int Wiersz, string Wywolanie, string Oslona)> Czytniki()
    {
        var wynik = new List<(string, int, string, string)>();
        foreach (var sciezka in PlikiCsWarstwyGry())
        {
            var wiersze = File.ReadAllLines(sciezka);
            for (var i = 0; i < wiersze.Length; i++)
            {
                var wiersz = wiersze[i];
                var tresc = wiersz.TrimStart();
                if (tresc.StartsWith("//", StringComparison.Ordinal) || !Regex.IsMatch(wiersz, Czytnik))
                {
                    continue;
                }

                var wywolanie = Regex.Match(wiersz, @"(\w+\.\w+)\s*\(").Groups[1].Value;
                var oslona = wywolanie.EndsWith(".TryParse", StringComparison.Ordinal) ? "TryParse"
                    : WBlokuTry(wiersze, i) ? "try"
                    : "BRAK";
                wynik.Add((Path.GetFileName(sciezka), i + 1, wywolanie, oslona));
            }
        }

        return wynik;
    }

    [TestMethod]
    public void Kazdy_czytnik_tresci_pliku_w_src_Game_ma_oslone_dla_pliku_ZLEGO()
    {
        var czytniki = Czytniki();

        // KONTROLA PRZYRZĄDU: bez niej zero czytników dawałoby zero braków i zieleń
        // o niczym (6.D27). Zbiór jest przybity, bo liczba nie mówi, KTÓRY odpadł.
        CollectionAssert.AreEqual(
            CzytnikiZmierzone,
            czytniki.Select(c => c.Wywolanie).OrderBy(x => x, StringComparer.Ordinal).ToArray(),
            "zbiór czytników treści pliku w src/Game/ się zmienił: "
            + string.Join(", ", czytniki.Select(c => $"{c.Plik}:{c.Wiersz} {c.Wywolanie}"))
            + " — nowy czytnik ma wejść tu RAZEM ze swoją osłoną");

        var bezOslony = czytniki.Where(c => c.Oslona == "BRAK").ToList();
        Assert.AreEqual(0, bezOslony.Count,
            "czytniki treści pliku BEZ osłony dla pliku złego: "
            + string.Join(", ", bezOslony.Select(c => $"{c.Plik}:{c.Wiersz} {c.Wywolanie}"))
            + " — uszkodzony plik kończy się tam zrzutem środowiska, a nie wierszem `Abort`");

        Assert.AreEqual(6, czytniki.Count(c => c.Oslona == "try"),
            "osłoniętych blokiem try ma być sześć, a jest: "
            + string.Join(", ", czytniki.Select(c => $"{c.Wywolanie}={c.Oslona}")));
        Assert.AreEqual(1, czytniki.Count(c => c.Oslona == "TryParse"),
            "osłonięty przez TryParse ma być jeden (telemetria), a jest: "
            + string.Join(", ", czytniki.Select(c => $"{c.Wywolanie}={c.Oslona}")));
    }

    [TestMethod]
    public void Kazdy_czytnik_JSON_ma_klauzule_na_ZLY_KSZTALT_dokumentu()
    {
        // Sam blok try nie wystarcza: filtr pierwszej klauzuli przepuszcza wyjątki
        // `System.Text.Json` dla dokumentu poprawnego składniowo, ale innego kształtu
        // (zmierzone: oś `[]` — scena wisiała). Klauzul drugiej rodziny ma być tyle,
        // ile czytników JSON, bo każdy z nich ma własny wiersz odmowy.
        var zrodlo = File.ReadAllText(Path.Combine(
            MetroBxl.Tests.Shared.KorzenRepozytorium.Sciezka, "src", "Game", "FirstRun.cs"));
        var czytnikiJson = Czytniki().Count(c => c.Wywolanie.EndsWith(".FromJson", StringComparison.Ordinal)
            || c.Wywolanie == "JsonDocument.Parse");
        var klauzule = Regex.Matches(zrodlo, @"catch \(Exception error\) when \(BadFile\.IsWrongJsonShape\(error\)\)").Count;

        Assert.AreEqual(4, czytnikiJson, $"czytników JSON w src/Game/ jest {czytnikiJson}, a zmierzono cztery");
        Assert.AreEqual(czytnikiJson, klauzule,
            $"klauzul na zły kształt dokumentu jest {klauzule} przy {czytnikiJson} czytnikach JSON");
    }

    [TestMethod]
    public void Rozpoznanie_bloku_try_widzi_oslone_i_jej_BRAK_na_tekscie_wzorcowym()
    {
        // Przyrząd sprawdzony na własnym przedmiocie, w obie strony: ten sam czytnik
        // raz w bloku try, raz za nim. Bez drugiej połowy przyrząd zwracający zawsze
        // „try" przeszedłby bramkę wyżej tak samo dobrze jak prawdziwy.
        var wiersze = new[]
        {
            "    private void Czytaj()",
            "    {",
            "        try",
            "        {",
            "            _axis = TrackAxis.FromJson(file.GetAsText());",
            "        }",
            "        catch (Exception error) when (error is FormatException)",
            "        {",
            "            return;",
            "        }",
            "",
            "        var manifest = ChunkManifest.FromJson(file.GetAsText());",
            "    }",
        };

        Assert.IsTrue(WBlokuTry(wiersze, 4), "czytnik w bloku try nie został rozpoznany jako osłonięty");
        Assert.IsFalse(WBlokuTry(wiersze, 11), "czytnik ZA blokiem try został uznany za osłonięty");
        Assert.IsFalse(WBlokuTry(wiersze, 8), "wiersz w bloku catch został uznany za osłonięty przez try");
    }
}
