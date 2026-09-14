using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.RegularExpressions;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace MetroBxl.Sim.Tests;

/// <summary>
/// Ramiona domyślne switchy po wartości wyliczeniowej w <c>src/Sim/</c> — 6.D210.
///
/// <para><b>Co ta pozycja zmierzyła i dlaczego NIE przybiła podziału postaci.</b>
/// 6.D197 zmierzyło 13.09.2026 dwanaście switchy i zgodność co do jednego wystąpienia:
/// osiem wyrażeniowych, wszystkie z ramieniem <b>rzucającym</b> i wszystkie
/// <b>martwe</b>; cztery instrukcyjne, wszystkie z <c>default: break;</c> i wszystkie
/// <b>żywe</b>. Wyglądało to na regułę projektu.</para>
///
/// <para><b>Dzień później para „postać ↔ martwota" już się rozeszła.</b> MB-08 dołożyło
/// dwa switche wyrażeniowe, a jeden z nich — <c>StationStop.NextManualPhase</c> —
/// pokrywa <b>5 z 7</b> członów <c>DoorPhase</c> i rzuca dla pozostałych dwóch
/// świadomie („Ta faza nie kończy się z upływem czasu"). Jest więc wyrażeniowy,
/// rzucający i <b>ŻYWY</b> — kombinacja, której 13.09.2026 w drzewie nie było.
/// Zapadka na tamtym podziale kazałaby dziś albo ją podnieść, albo przepisać regułę,
/// a chroniłaby przed niczym nazwanym. Podział zostaje więc <b>zapisany</b>, nie
/// przybity — tak jak przy 6.D197.</para>
///
/// <para><b>Przybita jest jedna rzecz, i to taka, którą da się nazwać:</b> ramię
/// domyślne, które jest <b>jednocześnie CICHE i MARTWE</b>. Cichy filtr przy pełnym
/// pokryciu nie filtruje niczego — a gdy ktoś dopisze człon do wyliczenia, ten sam
/// filtr połknie go bez słowa. Dziś takich ramion jest <b>zero</b>, więc bramka stoi
/// na zbiorze pustym i sama z siebie nic nie znaczy (6.D27); dlatego obok niej stoi
/// kontrola przyrządu na wejściu syntetycznym, która żąda, żeby klasyfikator trafił
/// we wszystkie cztery kombinacje (cisza × martwota).</para>
///
/// <para>Rozkład zmierzony 14.09.2026: 14 switchy, 10 wyrażeniowych (10 rzucających)
/// i 4 instrukcyjne (4 ciche); 9 martwych i 5 żywych.</para>
/// </summary>
[TestClass]
public sealed class DefaultArmAuditTests
{
    /// <summary>Podłoga na liczbę znalezionych switchy — zero znaczy zepsuty skan.</summary>
    private const int MinimumSwitches = 10;

    private sealed record Ramie(string Plik, string Wyliczenie, int Pokrytych, int Czlonow,
                                bool Ciche, bool Wyrazeniowy)
    {
        public bool Martwe => Pokrytych == Czlonow && Czlonow > 0;
    }

    private static readonly Regex Wyliczenie = new(
        @"enum\s+(\w+)\s*\{(.*?)\n\}", RegexOptions.Singleline);

    private static readonly Regex Czlon = new(
        @"^\s{4}([A-Z]\w*)\s*(?:=[^,]+)?,\s*$", RegexOptions.Multiline);

    /// <summary>Etykieta ramienia wyrażeniowego: <c>Typ.Czlon =></c> na początku wiersza.</summary>
    private static readonly Regex EtykietaWyrazeniowa = new(
        @"^\s*([A-Z]\w+)\.([A-Z]\w+)\s*(?:when\b[^=]*)?=>", RegexOptions.Multiline);

    /// <summary>Etykieta ramienia instrukcyjnego: <c>case Typ.Czlon:</c>.</summary>
    private static readonly Regex EtykietaInstrukcyjna = new(
        @"^\s*case\s+([A-Z]\w+)\.([A-Z]\w+)\s*:", RegexOptions.Multiline);

    private static readonly Regex RamieDomyslne = new(
        @"^\s*(?:_|default)\s*(?:=>|:)\s*(.*)$", RegexOptions.Multiline);

    [TestMethod]
    public void Zadne_ramie_domyslne_w_rdzeniu_nie_jest_jednoczesnie_ciche_i_martwe()
    {
        var znalezione = Zebrane();
        Assert.IsTrue(znalezione.Count >= MinimumSwitches,
            $"switchy po wyliczeniu znaleziono {znalezione.Count} przy podłodze " +
            $"{MinimumSwitches} — skan oślepł albo rdzeń się skurczył, a zero odpowiada " +
            "tak samo jak skan widzący");

        var cicheIMartwe = znalezione.Where(r => r.Ciche && r.Martwe).ToList();
        Assert.AreEqual(0, cicheIMartwe.Count,
            "ramię domyślne CICHE przy PEŁNYM pokryciu członów: " +
            string.Join(" | ", cicheIMartwe.Select(r => $"{r.Plik} ({r.Wyliczenie})")) +
            " — filtr, który nic nie odsiewa, a po dopisaniu członu połknie go bez słowa");
    }

    [TestMethod]
    public void Klasyfikator_trafia_we_wszystkie_cztery_kombinacje_ciszy_i_martwoty()
    {
        // Bez tej kontroli zero wyżej znaczyłoby tyle, co przyrząd, który je wypisał:
        // klasyfikator niewidzący ciszy odpowiedziałby „zero" tak samo, jak widzący.
        // Wejście jest syntetyczne, bo kombinacji „ciche i martwe" w drzewie NIE MA.
        const string wyliczenie = "public enum Proba\n{\n    Jeden,\n    Dwa,\n}\n";

        var przypadki = new (string Kod, bool Ciche, bool Martwe)[]
        {
            ("switch (x)\n{\n    case Proba.Jeden:\n    case Proba.Dwa:\n        break;\n    default:\n        break;\n}\n", true, true),
            ("switch (x)\n{\n    case Proba.Jeden:\n        break;\n    default:\n        break;\n}\n", true, false),
            ("x switch\n{\n    Proba.Jeden => 1,\n    Proba.Dwa => 2,\n    _ => throw new ArgumentOutOfRangeException(),\n}\n", false, true),
            ("x switch\n{\n    Proba.Jeden => 1,\n    _ => throw new ArgumentOutOfRangeException(),\n}\n", false, false),
        };

        foreach (var (kod, ciche, martwe) in przypadki)
        {
            var czlonow = Czlony(wyliczenie);
            var ramie = Sklasyfikuj("proba.cs", kod, czlonow);
            Assert.IsNotNull(ramie, $"klasyfikator nie zobaczył switcha w próbce:\n{kod}");
            Assert.AreEqual(ciche, ramie!.Ciche, $"cisza źle rozpoznana w próbce:\n{kod}");
            Assert.AreEqual(martwe, ramie.Martwe, $"martwota źle rozpoznana w próbce:\n{kod}");
        }
    }

    private static Dictionary<string, int> Czlony(string zrodlo)
    {
        var mapa = new Dictionary<string, int>(StringComparer.Ordinal);
        foreach (Match m in Wyliczenie.Matches(zrodlo))
        {
            mapa[m.Groups[1].Value] = Czlon.Matches(m.Groups[2].Value).Count;
        }

        return mapa;
    }

    private static Ramie? Sklasyfikuj(string plik, string korpus, Dictionary<string, int> czlony)
    {
        var wyrazeniowy = EtykietaWyrazeniowa.Matches(korpus).Count > 0;
        var etykiety = wyrazeniowy
            ? EtykietaWyrazeniowa.Matches(korpus)
            : EtykietaInstrukcyjna.Matches(korpus);
        if (etykiety.Count == 0)
        {
            return null;
        }

        var typ = etykiety.Select(m => m.Groups[1].Value)
            .Where(czlony.ContainsKey)
            .GroupBy(t => t, StringComparer.Ordinal)
            .OrderByDescending(g => g.Count())
            .Select(g => g.Key)
            .FirstOrDefault();
        if (typ is null)
        {
            return null;
        }

        var pokryte = etykiety
            .Where(m => string.Equals(m.Groups[1].Value, typ, StringComparison.Ordinal))
            .Select(m => m.Groups[2].Value)
            .Distinct(StringComparer.Ordinal)
            .Count();

        var domyslne = RamieDomyslne.Match(korpus);
        if (!domyslne.Success)
        {
            return null;
        }

        var tresc = domyslne.Groups[1].Value.Trim();
        if (tresc.Length == 0)
        {
            // `default:` z treścią w następnym wierszu — postać instrukcyjna.
            var po = korpus[(domyslne.Index + domyslne.Length)..].TrimStart('\r', '\n');
            tresc = po.Split('\n').FirstOrDefault()?.Trim() ?? string.Empty;
        }

        var ciche = !tresc.StartsWith("throw", StringComparison.Ordinal);
        return new Ramie(plik, typ, pokryte, czlony[typ], ciche, wyrazeniowy);
    }

    private static List<Ramie> Zebrane()
    {
        var root = FindRepositoryRoot();
        Assert.IsNotNull(root, "nie znaleziono korzenia repozytorium");

        var pliki = Directory
            .EnumerateFiles(Path.Combine(root!, "src", "Sim"), "*.cs", SearchOption.AllDirectories)
            .Where(p => !p.Contains($"{Path.DirectorySeparatorChar}bin{Path.DirectorySeparatorChar}",
                                    StringComparison.Ordinal))
            .Where(p => !p.Contains($"{Path.DirectorySeparatorChar}obj{Path.DirectorySeparatorChar}",
                                    StringComparison.Ordinal))
            .OrderBy(p => p, StringComparer.Ordinal)
            .ToList();

        var czlony = new Dictionary<string, int>(StringComparer.Ordinal);
        var zrodla = new List<(string Plik, string Tresc)>();
        foreach (var plik in pliki)
        {
            var tresc = File.ReadAllText(plik);
            zrodla.Add((Path.GetRelativePath(root!, plik), tresc));
            foreach (var para in Czlony(tresc))
            {
                czlony[para.Key] = para.Value;
            }
        }

        var out_ = new List<Ramie>();
        foreach (var (plik, tresc) in zrodla)
        {
            foreach (var poczatek in PoczatkiSwitchy(tresc))
            {
                var korpus = Korpus(tresc, poczatek);
                if (korpus is null)
                {
                    continue;
                }

                var ramie = Sklasyfikuj(plik, korpus, czlony);
                if (ramie is not null)
                {
                    out_.Add(ramie);
                }
            }
        }

        return out_;
    }

    private static IEnumerable<int> PoczatkiSwitchy(string zrodlo)
    {
        foreach (Match m in Regex.Matches(zrodlo, @"\bswitch\b"))
        {
            yield return m.Index;
        }
    }

    private static string? Korpus(string zrodlo, int poczatek)
    {
        var i = zrodlo.IndexOf('{', poczatek);
        if (i < 0)
        {
            return null;
        }

        var glebokosc = 0;
        for (var j = i; j < zrodlo.Length; j++)
        {
            if (zrodlo[j] == '{')
            {
                glebokosc++;
            }
            else if (zrodlo[j] == '}')
            {
                glebokosc--;
                if (glebokosc == 0)
                {
                    return zrodlo[(i + 1)..j];
                }
            }
        }

        return null;
    }

    private static string? FindRepositoryRoot()
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

        return null;
    }
}
