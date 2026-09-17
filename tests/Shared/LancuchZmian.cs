using System;
using System.Collections.Generic;
using System.Globalization;
using System.Text.RegularExpressions;

namespace MetroBxl.Tests.Shared;

/// <summary>
/// Łańcuch dawnych wartości stałej, czytany z jej komentarza (6.D260).
///
/// <para><b>Skąd to jest.</b> 6.D256 spędziło trzy doby nad liczbą <b>108</b>, którą
/// odtworzenie dało przy stałej stojącej na 116. Odpowiedź leżała kilkanaście wierszy
/// wyżej, w komentarzu tej samej stałej: <c>108 -&gt; 112 -&gt; 113 -&gt; 114 -&gt; 116</c>.
/// Sto osiem było OSTATNIM OGNIWEM PRZED łańcuchem, a nie liczbą znikąd — tylko
/// komunikat odmowy o tym nie mówił, więc wyglądała tak samo jak dowolna inna.</para>
///
/// <para><b>Łańcuch czytany jest Z PLIKU ŹRÓDŁOWEGO, a nie przepisany do tablicy.</b>
/// Przepisana kopia rozjeżdża się z komentarzem po pierwszej zmianie i mówi wtedy
/// nieprawdę o swojej własnej historii — a to jest dokładnie ta klasa usterki, którą
/// ta klasa ma wykrywać.</para>
///
/// <para><b>Czytniki są DWA i to jest wybór, nie przeoczenie (6.D257 kazało szukać
/// jednego).</b> Ten czyta pliki <c>.cs</c>, a <c>tools/tests/test_value_chains.py</c>
/// czyta oba drzewa i pilnuje ciągłości wszystkich 41 łańcuchów. Wspólnego czytnika
/// nie da się tu mieć bez wołania Pythona z testu C# albo odwrotnie; wspólny jest
/// natomiast KSZTAŁT, a bramka pythonowa sprawdza go po obu stronach. Gdyby te dwa
/// wzorce się rozjechały, tamta bramka przestałaby widzieć łańcuchy C# i zapaliłaby
/// się na podłodze liczby stałych.</para>
/// </summary>
public static class LancuchZmian
{
    private static readonly Regex Ogniwo = new(
        @"//[/ ]*\s*(?:<para><b>)?\s*(\d+)\s*->\s*(\d+)\s*\((\d{2}\.\d{2}\.\d{4}),\s*([^)]+)\)",
        RegexOptions.Compiled);

    private static readonly Regex Przypisanie = new(
        @"\b(?:const|static readonly)\s+\w+\s+(\w+)\s*=",
        RegexOptions.Compiled);

    /// <summary>
    /// Zdanie „N stała tu do DATA, pozycja POZYCJA" — albo <c>null</c>, gdy ta liczba
    /// w łańcuchu tej stałej nigdy nie stała.
    /// </summary>
    /// <param name="nazwaStalej">Nazwa stałej; przekazuj przez <c>nameof</c>.</param>
    /// <param name="liczba">Liczba, o którą pytamy.</param>
    /// <param name="czlonySciezki">Ścieżka pliku względem korzenia repozytorium.</param>
    public static string? SkadTaLiczba(string nazwaStalej, int liczba,
                                       params string[] czlonySciezki)
    {
        var zrodlo = KorzenRepozytorium.Tresc(czlonySciezki);
        var szukana = liczba.ToString(CultureInfo.InvariantCulture);
        var biezace = new List<(string Od, string Data, string Pozycja)>();

        foreach (var linia in zrodlo.Split('\n'))
        {
            var ogniwo = Ogniwo.Match(linia);
            if (ogniwo.Success)
            {
                biezace.Add((ogniwo.Groups[1].Value, ogniwo.Groups[3].Value,
                             ogniwo.Groups[4].Value.Trim()));
                continue;
            }

            var przypisanie = Przypisanie.Match(linia);
            if (przypisanie.Success && biezace.Count > 0)
            {
                if (przypisanie.Groups[1].Value == nazwaStalej)
                {
                    foreach (var (od, data, pozycja) in biezace)
                    {
                        if (od == szukana)
                        {
                            return $"{liczba} stała tu do {data}, pozycja {pozycja}";
                        }
                    }

                    return null;
                }

                biezace.Clear();
            }
            else if (linia.Trim().Length > 0
                     && !linia.TrimStart().StartsWith("//", StringComparison.Ordinal)
                     && biezace.Count > 0)
            {
                biezace.Clear();
            }
        }

        return null;
    }
}
