using System.Globalization;
using MetroBxl.Game;
using MetroBxl.Sim.Physics;
using MetroBxl.Sim.Signalling;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace MetroBxl.Game.Tests;

/// <summary>
/// Wiersz HUD-u o sygnalizacji — jeden skład dla linii i dla kabiny.
///
/// <para><b>Po co testy na NAPIS.</b> Bo do 05.09.2026 ten napis powstawał w metodzie
/// węzła <c>Node3D</c> i pilnował go wyłącznie ludzki wzrok czytający zrzut. Od G-5
/// czytają go dwa różne przebiegi — <c>--line --signalling</c> i kabina pod
/// <c>--signalling</c> — więc rozjazd między nimi byłby cichy: wiersz z inną jednostką
/// albo innym zaokrągleniem wygląda dokładnie tak samo jak wiersz prawdziwy.</para>
///
/// <para>Format dla trybu <c>--line</c> ma zostać CO DO ZNAKU taki, jaki był, bo zrzuty
/// kontrolne z <c>--line --shot</c> ogląda bramka wizualna, a jej progi są zmierzone na
/// klatce bez geometrii — czyli na samym HUD-zie.</para>
/// </summary>
[TestClass]
public sealed class SignallingHudTests
{
    private static MovementAuthority Authority(double frontM, double endM, string blockId) =>
        new("KABINA", frontM, endM, blockId, AuthorityLimit.BlockNotReserved);

    [TestMethod]
    public void WierszBezIngerencjiNieObiecujeHamowania()
    {
        var decision = new ProtectionDecision(
            Units.KmhToMps(72.0), 462.73, ProtectionAction.None, 0.0, false, string.Empty);

        var line = SignallingHud.Line(Authority(94.0, 556.73, "S02"), decision, 1, 0);

        System.Console.WriteLine(line);
        Assert.AreEqual(
            "v_dop  72.0 km/h   autorytet     463 m (BlockNotReserved, blok S02)   tras 1/odmów 0",
            line);
        StringAssert.DoesNotMatch(line, new System.Text.RegularExpressions.Regex("ATP HAMUJE"));
        StringAssert.DoesNotMatch(line, new System.Text.RegularExpressions.Regex("PRZEKROCZENIE"));
    }

    [TestMethod]
    public void PrzekroczenieBezIngerencjiJestOSTRZEZENIEMANieHamowaniem()
    {
        // Trzy poziomy `ProtectionAction` mają się w tym wierszu ROZRÓŻNIAĆ. Samo
        // przekroczenie przy krzywej, która jeszcze wyrabia, jest ostrzeżeniem —
        // i gdyby HUD pisał wtedy „ATP HAMUJE", mówiłby o hamowaniu, którego nie ma.
        var decision = new ProtectionDecision(
            Units.KmhToMps(72.0), 900.0, ProtectionAction.None, 0.0, true, "overspeed:EndOfLine");

        var line = SignallingHud.Line(Authority(94.0, 994.0, "S03"), decision, 2, 1);

        System.Console.WriteLine(line);
        StringAssert.Contains(line, "PRZEKROCZENIE");
        StringAssert.DoesNotMatch(line, new System.Text.RegularExpressions.Regex("ATP HAMUJE"));
        StringAssert.Contains(line, "tras 2/odmów 1");
    }

    [TestMethod]
    public void IngerencjaNiesieRODZAJIZADANIEWMetrachNaSekundeKwadrat()
    {
        var decision = new ProtectionDecision(
            Units.KmhToMps(58.4), 210.5, ProtectionAction.ServiceIntervention, 0.863, true,
            "overspeed:BlockNotReserved");

        var line = SignallingHud.Line(Authority(300.0, 510.5, "P02"), decision, 3, 0);

        System.Console.WriteLine(line);
        StringAssert.Contains(line, "PRZEKROCZENIE");
        StringAssert.Contains(line, "ATP HAMUJE: ServiceIntervention 0.86 m/s²");
        StringAssert.Contains(line, string.Create(CultureInfo.InvariantCulture, $"v_dop  58.4 km/h"));
    }

    [TestMethod]
    public void IngerencjaAwaryjnaNazywaSieAwaryjna()
    {
        // Rodzaj ingerencji jest w tym wierszu treścią, nie ozdobą: hamulec służbowy
        // i „awaryjny" dają dziś ten sam nastawnik (pełny służbowy), więc po samym
        // zachowaniu składu gracz ich nie odróżni. Napis jest jedynym miejscem, gdzie
        // ta różnica jest widoczna.
        var decision = new ProtectionDecision(
            Units.KmhToMps(16.9), 41.0, ProtectionAction.EmergencyIntervention, 1.3, true,
            "service-brake-insufficient:BlockNotReserved");

        var line = SignallingHud.Line(Authority(450.0, 491.0, "S02"), decision, 1, 0);

        System.Console.WriteLine(line);
        StringAssert.Contains(line, "ATP HAMUJE: EmergencyIntervention 1.30 m/s²");
    }

    [TestMethod]
    public void MilczenieINIEMASYGNALIZACJIToDwaROZNENapisy()
    {
        // Milczenie wygląda dokładnie tak samo jak „droga wolna", a to dwie różne
        // rzeczy — i dlatego przebieg bez planu ma własny wiersz, a nie pusty.
        Assert.AreNotEqual(string.Empty, SignallingHud.WithoutSignalling);
        Assert.AreNotEqual(string.Empty, SignallingHud.NotOnPlanYet);
        Assert.AreNotEqual(string.Empty, SignallingHud.WithoutProtection);
        Assert.AreNotEqual(string.Empty, SignallingHud.BeforeFirstStep);
        StringAssert.Contains(SignallingHud.WithoutSignalling, "--signalling");
    }
}
