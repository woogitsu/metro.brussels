using MetroBxl.Game.UI;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace MetroBxl.Game.Tests;

[TestClass]
public sealed class HudPositionTests
{
    [TestMethod]
    public void Widoczny_wiersz_stacji_nie_powtarza_dlugiiej_nazwy_w_pozycji()
    {
        var name = "Comte de Flandre|Graaf van Vlaanderen";

        var line = Hud.PositionLine(2042.7, 6686.7, name, 12, true);

        Assert.AreEqual("chainage    2042.7 m / 6686.7 m", line,
            "Pozycja ma zostać jednoliniowa, gdy wiersz stacji pokazuje już nazwę i odległość.");
    }

    [TestMethod]
    public void Bez_wiersza_stacji_pozycja_zachowuje_cel_i_odleglosc()
    {
        var name = "Comte de Flandre|Graaf van Vlaanderen";

        var line = Hud.PositionLine(2042.7, 6686.7, name, 12, false);

        Assert.AreEqual("chainage    2042.7 m / 6686.7 m     " + name + " za 12 m", line,
            "Bez osobnego wiersza stacji pełny cel i odległość muszą pozostać widoczne.");
    }
}
