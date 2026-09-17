using System;
using System.Collections.Generic;
using System.IO;
using MetroBxl.Tests.Shared;
using System.Linq;
using System.Text.RegularExpressions;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace MetroBxl.Game.Tests;

/// <summary>
/// Bramka LEKSYKALNA na odczyt klawiszy obsługi linii w <c>FirstRun.HandleTrainKeys</c>
/// — MB-08.
///
/// <para><b>Ta bramka istnieje, bo kontrola negatywna wyszła ZIELONA, i jest to
/// wyjaśnienie pomiarem, a nie łatka na wyczucie.</b> KN-9 przy MB-08: warunek
/// <c>if (doorOpenKey &amp;&amp; !_doorOpenKeyHeld)</c> zamieniony na
/// <c>if (doorOpenKey)</c> — czyli klawisz wysyłający polecenie w KAŻDEJ klatce,
/// a nie na zboczu — dał <b>303/303, kod 0</b>. Powód jest dokładnie ten sam, co przy
/// KN-4 pozycji MB-03: cały ten kod stoi w klasie dziedziczącej po węźle Godota,
/// której żaden test jednostkowy nie zbuduje. Naprawą jest bramka czytająca ŹRÓDŁO,
/// tak samo jak tam.</para>
///
/// <para><b>Dlaczego to jest usterka, a nie kosmetyka.</b> Przy trzymanym <c>D</c>
/// pierwsze polecenie przechodzi, a każde następne w tej samej sekundzie wraca odmową
/// „drzwi są już otwarte" — i to ODMOWA ląduje w wierszu HUD-u, bo ma pierwszeństwo
/// przed podpowiedzią. Gracz widzi więc komunikat o błędzie po czynności, która się
/// UDAŁA. Ta sama arytmetyka dotyczy <c>N</c>: klawisz bez zbocza przewijałby składy
/// z prędkością klatek.</para>
///
/// <para><b>Czego ta bramka NIE robi.</b> Nie uruchamia sceny i nie wie, czy
/// <c>HandleTrainKeys</c> jest w ogóle wołane. Jest sitem na KSZTAŁT kodu, nie na
/// zachowanie — i dlatego stoi obok testów <c>DoorPrompt</c>, a nie zamiast nich.</para>
/// </summary>
[TestClass]
public sealed class HandleTrainKeysGateTests
{
    private const string Metoda = "private void HandleTrainKeys()";

    /// <summary>Ile klawiszy czyta ta metoda — <c>N</c>, <c>T</c>, <c>O</c>, <c>D</c>, <c>F</c>.</summary>
    private const int CzytanychKlawiszy = 5;

    private static string Zrodlo()
    {
        var sciezka = KorzenRepozytorium.Plik("src", "Game", "FirstRun.cs");
        Assert.IsTrue(File.Exists(sciezka), $"nie ma pliku {sciezka}");
        return File.ReadAllText(sciezka);
    }

    /// <summary>Ciało metody: od pierwszej klamry po nagłówku do jej pary.</summary>
    private static string Cialo(string kod, string naglowek)
    {
        var start = kod.IndexOf(naglowek, StringComparison.Ordinal);
        Assert.IsTrue(start >= 0, $"nie ma w źródle nagłówka `{naglowek}`");
        var otwarcie = kod.IndexOf('{', start);
        Assert.IsTrue(otwarcie >= 0, "nagłówek bez ciała");

        var glebokosc = 0;
        for (var i = otwarcie; i < kod.Length; i++)
        {
            if (kod[i] == '{')
            {
                glebokosc++;
            }
            else if (kod[i] == '}')
            {
                glebokosc--;
                if (glebokosc == 0)
                {
                    return kod.Substring(otwarcie, i - otwarcie + 1);
                }
            }
        }

        Assert.Fail("ciało metody się nie domyka");
        return string.Empty;
    }

    /// <summary>Nazwy zmiennych lokalnych wziętych wprost z odczytu akcji.</summary>
    private static List<string> OdczytaneKlawisze(string cialo) => Regex
        .Matches(cialo, @"var\s+(\w+)\s*=\s*Godot\.Input\.IsActionPressed\(")
        .Select(m => m.Groups[1].Value)
        .ToList();

    [TestMethod]
    public void Skan_widzi_wszystkie_odczyty_klawiszy_tej_metody()
    {
        // KONTROLA PRZYRZĄDU, bez której wynik testu niżej nie znaczyłby nic: bramka,
        // która nie widzi ANI JEDNEGO odczytu, przechodzi pętlę zero razy i melduje
        // zieleń tak samo, jak bramka widząca wszystkie (rodzina 6.D159).
        var odczyty = OdczytaneKlawisze(Cialo(Zrodlo(), Metoda));

        Assert.AreEqual(CzytanychKlawiszy, odczyty.Count,
            $"`HandleTrainKeys` czyta dziś {odczyty.Count} klawiszy wobec zmierzonych "
            + $"{CzytanychKlawiszy}: " + string.Join(", ", odczyty));
        Assert.AreEqual(odczyty.Count, odczyty.Distinct(StringComparer.Ordinal).Count(),
            "dwa odczyty pod tą samą nazwą: " + string.Join(", ", odczyty));
    }

    [TestMethod]
    public void Kazdy_czytany_klawisz_dziala_NA_ZBOCZU_i_zapamietuje_swoj_stan()
    {
        var cialo = Cialo(Zrodlo(), Metoda);
        var odczyty = OdczytaneKlawisze(cialo);
        Assert.AreEqual(CzytanychKlawiszy, odczyty.Count, "skan zawęził się — patrz test wyżej");

        foreach (var klawisz in odczyty)
        {
            Assert.IsTrue(
                Regex.IsMatch(cialo, $@"\b{Regex.Escape(klawisz)}\s*&&\s*!_\w+Held\b"),
                $"`{klawisz}` jest użyty bez zbocza: nie ma ani jednego warunku "
                + $"`{klawisz} && !_…Held`, więc polecenie poszłoby w KAŻDEJ klatce, "
                + "w której klawisz jest trzymany");

            Assert.IsTrue(
                Regex.IsMatch(cialo, $@"_\w+Held\s*=\s*{Regex.Escape(klawisz)}\s*;"),
                $"`{klawisz}` nie zapisuje swojego stanu do pola `_…Held`, więc zbocze "
                + "nigdy nie wygaśnie i warunek zadziała raz na zawsze albo nigdy");
        }
    }

    [TestMethod]
    public void Wczesny_powrot_tez_zapamietuje_stan_wszystkich_klawiszy()
    {
        // Gałąź „nie ma linii" wraca przed obsługą, ale MUSI zapisać stany — inaczej
        // klawisz trzymany przez czas, w którym linii nie było, zadziałałby na zboczu
        // w chwili, gdy linia się pojawi, choć gracz go wtedy tylko TRZYMAŁ.
        var cialo = Cialo(Zrodlo(), Metoda);
        var odczyty = OdczytaneKlawisze(cialo);
        var przedPowrotem = cialo.Substring(0, cialo.IndexOf("return;", StringComparison.Ordinal));

        foreach (var klawisz in odczyty)
        {
            Assert.IsTrue(
                Regex.IsMatch(przedPowrotem, $@"_\w+Held\s*=\s*{Regex.Escape(klawisz)}\s*;"),
                $"`{klawisz}` nie jest zapamiętany przed wczesnym powrotem");
        }
    }
}
