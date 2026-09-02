using System;
using System.Linq;
using System.Reflection;
using MetroBxl.Game;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace MetroBxl.Game.Tests;

/// <summary>
/// Katalog założeń warstwy silnika. Sprawdzana jest WŁASNOŚĆ, nie lista wartości:
/// każda liczba bez źródła ma być zadeklarowana jako założenie i wypisana w logu
/// przejazdu. Test na same wartości byłby przepisaniem kodu do testu.
/// </summary>
[TestClass]
public sealed class DesignAssumptionsTests
{
    private static FieldInfo[] Constants() => typeof(DesignAssumptions)
        .GetFields(BindingFlags.Public | BindingFlags.Static)
        .Where(f => f.IsLiteral && f.FieldType == typeof(double))
        .ToArray();

    [TestMethod]
    public void EveryConstantIsDeclaredAsAnAssumption()
    {
        // TO JEST TEN TEST, o który chodzi. Dopisanie stałej bez wpisu w `All`
        // robi z liczby bez źródła cichy fakt: nie pojawi się w logu przejazdu
        // ani w raporcie, więc nikt się nie dowie, że coś zgadnięto.
        var declared = DesignAssumptions.All.Select(a => a.Name).ToHashSet(StringComparer.Ordinal);
        var missing = Constants().Select(f => f.Name).Where(n => !declared.Contains(n)).ToArray();
        Assert.AreEqual(0, missing.Length,
            "stałe bez wpisu w DesignAssumptions.All: " + string.Join(", ", missing));
    }

    [TestMethod]
    public void EveryDeclaredAssumptionMatchesTheConstantItNames()
    {
        // Druga strona tego samego: wpis może istnieć, ale nieść inną liczbę niż
        // stała, której nazwę nosi. Log wypisywałby wtedy wartość, której kod nie używa.
        foreach (var assumption in DesignAssumptions.All)
        {
            var field = typeof(DesignAssumptions).GetField(
                assumption.Name, BindingFlags.Public | BindingFlags.Static);
            Assert.IsNotNull(field, $"{assumption.Name} nie odpowiada żadnej stałej");
            Assert.AreEqual((double)field!.GetRawConstantValue()!, assumption.Value, 1e-12,
                $"{assumption.Name}: log wypisałby inną liczbę niż ta, której używa kod");
        }
    }

    /// <summary>Napisy, które wyglądają jak uzasadnienie, a nim nie są.</summary>
    private static readonly string[] Placeholders = { "todo", "tbd", "?", "-", "n/a", "brak" };

    [TestMethod]
    public void EveryAssumptionSaysWhyItIsAnAssumption()
    {
        // Sama liczba z jednostką nie wystarcza. Uzasadnienie jest tym, co odróżnia
        // „przyjęliśmy, bo nie ma źródła" od „zmierzyliśmy".
        //
        // Pierwsza wersja tego testu wymagała uzasadnienia dłuższego niż 30 znaków
        // i PADŁA na prawdziwym wpisie: `HeadlightEnergy` ma „jasność reflektora;
        // jak wyżej", czyli 29 znaków. Próg był arbitralny i mierzył nie to, co
        // trzeba — „jak wyżej" jest poprawnym odwołaniem do poprzedniego wpisu
        // (`HeadlightRangeM`: „parametr oświetlenia sceny, nie dane o taborze")
        // i tak właśnie ten katalog jest pisany. Obniżenie progu do 25 byłoby
        // dopasowaniem testu do wyniku, więc próg znika, a zostaje własność:
        // uzasadnienie ma istnieć i nie może być zaślepką.
        foreach (var assumption in DesignAssumptions.All)
        {
            Assert.IsFalse(string.IsNullOrWhiteSpace(assumption.Unit), assumption.Name);
            Assert.IsFalse(string.IsNullOrWhiteSpace(assumption.Reason), assumption.Name);
            var reason = assumption.Reason.Trim().ToLowerInvariant();
            Assert.IsFalse(Placeholders.Contains(reason),
                $"{assumption.Name}: uzasadnienie '{assumption.Reason}' to zaślepka");
        }
    }

    [TestMethod]
    public void TheCatalogueIsNotEmptyAndHasNoDuplicates()
    {
        // Kontrola negatywna do pierwszego testu: pusty katalog przechodziłby
        // „wszystkie zadeklarowane" trywialnie, gdyby stałych też nie było.
        Assert.IsTrue(Constants().Length >= 10, "katalog stałych nagle zmalał");
        var names = DesignAssumptions.All.Select(a => a.Name).ToArray();
        Assert.AreEqual(names.Length, names.Distinct(StringComparer.Ordinal).Count(),
            "duplikat w katalogu założeń");
    }

    [TestMethod]
    public void TheEyeSitsAboveTheFloorOfAnM7()
    {
        // Podłoga M7 jest na 1,03 m (spec). Oko maszynisty musi być wyżej —
        // inaczej kamera kabinowa patrzy spod podłogi.
        Assert.IsTrue(DesignAssumptions.CabEyeHeightM > 1.03,
            $"oko na {DesignAssumptions.CabEyeHeightM} m jest pod podłogą M7");
    }

    [TestMethod]
    public void TheControlCameraSitsOnTheOtherTrack()
    {
        // −4,20 m to rozstaw torów profilu box_double: kamera kontrolna ma stać
        // na sąsiednim torze, po przeciwnej stronie niż oś toru składu (+2,10 m).
        Assert.IsTrue(DesignAssumptions.OutsideLateralM < 0.0);
        Assert.IsTrue(DesignAssumptions.TrackOffsetM > 0.0);
        Assert.AreEqual(-2.0 * DesignAssumptions.TrackOffsetM, DesignAssumptions.OutsideLateralM, 1e-9,
            "kamera kontrolna nie stoi na sąsiednim torze");
    }
}
