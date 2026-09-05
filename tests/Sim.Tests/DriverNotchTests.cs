using System;
using MetroBxl.Sim.Physics;
using MetroBxl.Sim.Train;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace MetroBxl.Sim.Tests;

/// <summary>
/// Nastawnik krokowany numerem kroku, nie czasem klatki.
///
/// <para><b>Co te testy pilnują.</b> Do 05.09.2026 przesuw dźwigni siedział
/// w <c>src/Game/Input/DriverInput.Poll(delta)</c> i był wołany raz na KLATKĘ, z czasem
/// klatki; wszystkie kroki tej klatki dostawały potem to samo polecenie. Zmierzone
/// przeciw <c>src/Sim</c> (30 s trzymanego W, potem 30 s trzymanego S, tempo 0,80 1/s,
/// limit 70 km/h): 566,407284 m przy 120 kl./s wobec 566,641450 m przy 60 kl./s,
/// rozjazd <b>0,234166 m na 60 s</b> — przy bramkach porównujących telemetrię
/// z progiem <b>0</b>. <c>reports/droga-do-grywalnosci.md</c> §5.1.</para>
///
/// <para>Testy niżej są dwustronne: sprawdzają i to, że dźwignia rusza się we
/// właściwym tempie, i to, że wynik NIE ZALEŻY od podziału kroków na klatki.</para>
/// </summary>
[TestClass]
public sealed class DriverNotchTests
{
    /// <summary>Tempo z <c>DesignAssumptions.ControlNotchRatePerSecond</c>; ta stała jest poza zakresem tego zadania.</summary>
    private const double Rate = 0.80;

    private static DriverNotch Notch() => new(Rate);

    [TestMethod]
    public void OneStepOfPowerMovesTheNotchByRateTimesStepSeconds()
    {
        var notch = Notch();
        var step = FixedStep.Simulation;

        var command = notch.Advance(DriverKeys.Powering, step);

        Assert.AreEqual(Rate * step.Seconds, command.Throttle, 0.0);
        Assert.AreEqual(0.0, command.Brake, 0.0);
    }

    [TestMethod]
    public void FrameCoveringManyStepsMovesNotchOncePerStep()
    {
        // DECYZJA MODELOWA, przybita liczbą: klatka 60 kl./s obejmuje 2 kroki rdzenia
        // i dźwignia przesuwa się o DWA kroki, nie o jeden i nie o „czas klatki".
        // Mutacja `krok.Seconds` na `1.0 / 60.0` (czas klatki) daje tu 2 · 0,0133
        // zamiast 2 · 0,00667 i test pada.
        var notch = Notch();
        var step = FixedStep.Simulation;

        notch.Advance(DriverKeys.Powering, step);
        var command = notch.Advance(DriverKeys.Powering, step);

        Assert.AreEqual(2.0 * Rate * step.Seconds, command.Throttle, 1e-15);
    }

    [TestMethod]
    public void GivesTheSameNotchRegardlessOfHowStepsSplitIntoFrames()
    {
        // Sedno naprawy. Ten sam stan klawiszy przez 240 kroków, raz podany jako
        // 240 klatek po jednym kroku, raz jako 2 klatki po 120 kroków. Dźwignia ma
        // wyjść IDENTYCZNA CO DO BITU, bo jej położenie jest funkcją liczby kroków,
        // a nie liczby klatek.
        var step = FixedStep.Simulation;

        var perStep = Notch();
        for (var i = 0; i < 240; i++)
        {
            perStep.Advance(DriverKeys.Powering, step);
        }

        var perBigFrame = Notch();
        for (var frame = 0; frame < 2; frame++)
        {
            for (var i = 0; i < 120; i++)
            {
                perBigFrame.Advance(DriverKeys.Powering, step);
            }
        }

        Assert.AreEqual(perStep.Command.Throttle, perBigFrame.Command.Throttle, 0.0);
        Assert.AreEqual(perStep.Command.Brake, perBigFrame.Command.Brake, 0.0);
    }

    [TestMethod]
    public void SameStepIndexedKeysGiveTheSameRunAtEveryFrameRate()
    {
        // To jest pomiar z §5.1 raportu, powtórzony po naprawie. Te same klawisze
        // rozpisane po NUMERACH KROKÓW (3600 kroków W, potem 3600 kroków S) idą przez
        // pętlę klatek o czterech różnych rozmiarach — 1, 2, 4 i 120 kroków na klatkę.
        // Przed naprawą ta sama próba dawała pięć różnych dróg; teraz ma dać jedną,
        // co do bitu.
        var distances = new double[4];
        var sizes = new[] { 1, 2, 4, 120 };
        for (var i = 0; i < sizes.Length; i++)
        {
            distances[i] = RunHoldThenBrake(sizes[i]);
        }

        Assert.AreEqual(distances[0], distances[1], 0.0, "1 vs 2 kroki na klatkę");
        Assert.AreEqual(distances[0], distances[2], 0.0, "1 vs 4 kroki na klatkę");
        Assert.AreEqual(distances[0], distances[3], 0.0, "1 vs 120 kroków na klatkę");
        Assert.IsTrue(distances[0] > 100.0, $"przejazd ma być przejazdem, a nie postojem: {distances[0]} m");
    }

    [TestMethod]
    public void PowerReleasesBrakeBeforeTractionRises()
    {
        // Reguła przeniesiona z DriverInput bez zmiany: na M7 nie ma pozycji
        // „ciągnij i hamuj naraz". Póki hamulec jest podany, ciąg nie rośnie.
        var notch = Notch();
        var step = FixedStep.Simulation;
        notch.Set(new DriverCommand(0.0, 0.5));

        var command = notch.Advance(DriverKeys.Powering, step);

        Assert.AreEqual(0.5 - (Rate * step.Seconds), command.Brake, 1e-15);
        Assert.AreEqual(0.0, command.Throttle, 0.0);
    }

    [TestMethod]
    public void PowerWinsOverBrakeWhenBothKeysAreHeld()
    {
        // Zapis wejść jest bezstratny (W i S naraz da się zapisać), więc reguła
        // pierwszeństwa musi być tutaj i musi być przybita — inaczej zmiana kolejności
        // warunków cicho zmieniłaby znaczenie starych plików zapisu.
        var notch = Notch();
        var step = FixedStep.Simulation;

        var command = notch.Advance(new DriverKeys(Power: true, Brake: true, Coast: false), step);

        Assert.AreEqual(Rate * step.Seconds, command.Throttle, 0.0);
        Assert.AreEqual(0.0, command.Brake, 0.0);
    }

    [TestMethod]
    public void NoKeysLeaveTheNotchWhereItWas()
    {
        // Dźwignia nie wraca sama. Puszczenie klawiszy to nie to samo, co X.
        var notch = Notch();
        var step = FixedStep.Simulation;
        notch.Set(new DriverCommand(0.4, 0.0));

        var command = notch.Advance(DriverKeys.None, step);

        Assert.AreEqual(0.4, command.Throttle, 0.0);
        Assert.AreEqual(0.0, command.Brake, 0.0);
    }

    [TestMethod]
    public void UninitialisedStepIsRefused()
    {
        var notch = Notch();

        try
        {
            notch.Advance(DriverKeys.Powering, default);
        }
        catch (ArgumentException)
        {
            Assert.AreEqual(0.0, notch.Command.Throttle, 0.0);
            return;
        }

        Assert.Fail("krok zerowy przesunął dźwignię o zero i przeszedł bez słowa");
    }

    [TestMethod]
    public void NonPositiveRateIsRefused()
    {
        try
        {
            _ = new DriverNotch(0.0);
        }
        catch (ArgumentOutOfRangeException)
        {
            Assert.AreEqual(0.80, Rate, 0.0);
            return;
        }

        Assert.Fail("tempo zero zostało przyjęte");
    }

    /// <summary>
    /// Przejazd 7200 kroków przy zadanej liczbie kroków na klatkę: 3600 kroków
    /// trzymanego W, potem 3600 kroków trzymanego S. Klawisze są wybierane po NUMERZE
    /// KROKU, więc podział na klatki nie ma prawa niczego zmienić.
    /// </summary>
    private static double RunHoldThenBrake(int stepsPerFrame)
    {
        var model = VehicleModel.M7;
        var conditions = new RunConditions(
            model.MassKg(TrainLoad.Aw2), 0.0, model.Adhesion(RailCondition.Dry), TrackEnvironment.Tunnel);
        var controller = new TrainController(model);
        var step = FixedStep.Simulation;
        var notch = Notch();
        var state = DriveState.AtRest;
        const double limitMps = 70.0 / 3.6;
        const long totalSteps = 7200;

        for (var executed = 0L; executed < totalSteps; executed += stepsPerFrame)
        {
            for (var i = 0; i < stepsPerFrame; i++)
            {
                var index = executed + i;
                var keys = index < totalSteps / 2 ? DriverKeys.Powering : DriverKeys.Braking;
                var command = notch.Advance(keys, step);
                state = controller.Advance(state, conditions, command, limitMps, step, out _);
            }
        }

        return state.DistanceM;
    }
}
