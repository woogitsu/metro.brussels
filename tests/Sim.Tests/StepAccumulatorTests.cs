using System;
using MetroBxl.Sim.Physics;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace MetroBxl.Sim.Tests;

/// <summary>
/// Issue #106. Akumulator klatek nie miał ŻADNEGO pokrycia, bo siedział jako prywatne
/// pole węzła Godota. Audyt mutacyjny: podmiana „120 kroków na klatkę" na „1 krok na
/// klatkę" PRZEŻYWAŁA przy zielonym CI — telemetria próbkuje się po liczniku kroków
/// symulacji, więc wolniejszy przebieg produkuje identyczny co do bajtu plik CSV,
/// tylko dłużej. Bramka parytetu nie miała czego wykryć.
/// </summary>
[TestClass]
public sealed class StepAccumulatorTests
{
    private static StepAccumulator Simulation() => new(FixedStep.Simulation);

    [TestMethod]
    public void ExactlyOneStepWorthOfTimeGivesExactlyOneStep()
    {
        var accumulator = Simulation();
        Assert.AreEqual(1L, accumulator.StepsForFrame(1.0 / 120.0));
    }

    [TestMethod]
    public void SixtyHertzFrameGivesTwoStepsAtOneTwentiethHertzCore()
    {
        // To jest dokładnie ta liczba, którą psuła przeżywająca mutacja.
        var accumulator = Simulation();
        Assert.AreEqual(2L, accumulator.StepsForFrame(1.0 / 60.0));
    }

    [TestMethod]
    public void OneSecondFrameGivesOneHundredTwentySteps()
    {
        var accumulator = Simulation();
        Assert.AreEqual(120L, accumulator.StepsForFrame(1.0));
    }

    [TestMethod]
    public void RemainderIsCarriedNotDropped()
    {
        // Klatka krótsza od kroku nie daje kroku, ale jej czas nie znika: trzy takie
        // klatki po 1/360 s składają się na dokładnie jeden krok.
        var accumulator = Simulation();
        Assert.AreEqual(0L, accumulator.StepsForFrame(1.0 / 360.0));
        Assert.AreEqual(0L, accumulator.StepsForFrame(1.0 / 360.0));
        Assert.AreEqual(1L, accumulator.StepsForFrame(1.0 / 360.0));
        Assert.AreEqual(1L, accumulator.TotalSteps);
    }

    [TestMethod]
    public void UnevenFramesGiveTheSameTotalAsEvenFramesOverTheSameTime()
    {
        // To jest własność, na której stoi tryb --jitter: nierówny podział klatek
        // NIE MOŻE zmienić liczby kroków, bo inaczej odcisk telemetrii by się rozjechał.
        var even = Simulation();
        for (var i = 0; i < 600; i++)
        {
            even.StepsForFrame(1.0 / 60.0);
        }

        var uneven = Simulation();
        var elapsed = 0.0;
        var frame = 0;
        while (elapsed < 10.0)
        {
            var delta = (1.0 / 60.0) * (1.0 + (0.4 * Math.Sin(frame * 1.7)));
            if (elapsed + delta > 10.0)
            {
                delta = 10.0 - elapsed;
            }

            uneven.StepsForFrame(delta);
            elapsed += delta;
            frame++;
        }

        Assert.AreEqual(even.TotalSteps, uneven.TotalSteps);
        Assert.AreEqual(1200L, even.TotalSteps);
    }

    [TestMethod]
    public void NoDriftOverALongRun()
    {
        // Suma `t += dt` dryfuje, licznik kroków nie. Dziesięć minut przy 59,94 kl./s.
        var accumulator = Simulation();
        var frames = (int)Math.Round(600.0 * 59.94);
        for (var i = 0; i < frames; i++)
        {
            accumulator.StepsForFrame(1.0 / 59.94);
        }

        Assert.AreEqual(600L * 120L, accumulator.TotalSteps);
    }

    [TestMethod]
    public void NonPositiveAndNonFiniteFramesGiveNoStepsAndKeepTheCarry()
    {
        // Godot potrafi podać `delta` równą zeru w pierwszej klatce.
        var accumulator = Simulation();
        accumulator.StepsForFrame(1.0 / 360.0);
        var carry = accumulator.CarrySeconds;

        foreach (var bad in new[] { 0.0, -1.0, double.NaN, double.PositiveInfinity })
        {
            Assert.AreEqual(0L, accumulator.StepsForFrame(bad), $"delta={bad}");
        }

        Assert.AreEqual(carry, accumulator.CarrySeconds);
        Assert.AreEqual(0L, accumulator.TotalSteps);
    }

    [TestMethod]
    public void CarryStaysBelowOneStepAndNeverGoesNegative()
    {
        var accumulator = Simulation();
        var frame = 0;
        while (frame < 5000)
        {
            accumulator.StepsForFrame((1.0 / 60.0) * (1.0 + (0.9 * Math.Sin(frame * 0.37))));
            Assert.IsTrue(accumulator.CarrySeconds >= 0.0, "reszta zeszła poniżej zera");
            Assert.IsTrue(accumulator.CarrySeconds < FixedStep.Simulation.Seconds,
                "reszta urosła ponad jeden krok — kroki są gubione");
            frame++;
        }
    }

    [TestMethod]
    public void TheCarryClampIsNotDeadCode()
    {
        // ZMIERZONE, nie wymyślone. Szukanie po granicach wielokrotności kroku
        // znalazło klatki, dla których `carry - steps * Seconds` wychodzi UJEMNE:
        //
        //   0.024999999999999998 s -> 3 kroki, reszta -3.469446951953614e-18
        //   0.049999999999999996 s -> 6 kroków, reszta -6.938893903907228e-18
        //   0.09999999999999999  s -> 12 kroków, reszta -1.3877787807814457e-17
        //
        // To nie są wartości egzotyczne: pierwsza z nich to 25 ms, czyli zwykła
        // klatka przy 40 kl./s. Dzielenie zaokrągla w górę przez granicę całkowitą,
        // więc `steps` wychodzi o jeden za dużo względem prawdziwej podłogi.
        // Bez przycięcia ujemna reszta opóźniłaby następny krok o cały krok.
        //
        // Trzy miliony losowych klatek NIE trafiły w ten przypadek — losowanie nie
        // jest tu dowodem, konstrukcja jest.
        foreach (var delta in new[] { 0.024999999999999998, 0.049999999999999996, 0.09999999999999999 })
        {
            var accumulator = Simulation();
            accumulator.StepsForFrame(delta);
            Assert.IsTrue(accumulator.CarrySeconds >= 0.0,
                $"delta={delta:R} dała ujemną resztę {accumulator.CarrySeconds:R}");
        }
    }

    [TestMethod]
    public void DropCarryClearsTheRemainderButKeepsTheCounter()
    {
        var accumulator = Simulation();
        accumulator.StepsForFrame(1.0 / 80.0);
        Assert.IsTrue(accumulator.CarrySeconds > 0.0);
        accumulator.DropCarry();
        Assert.AreEqual(0.0, accumulator.CarrySeconds);
        Assert.AreEqual(1L, accumulator.TotalSteps);
    }

    [TestMethod]
    public void AnUninitialisedStepIsRefusedInsteadOfLoopingForever()
    {
        Assert.ThrowsException<ArgumentException>(() => new StepAccumulator(default));
    }

    [TestMethod]
    public void TheCoreFrequencyIsTheOneTheArchitectureDeclares()
    {
        // Kontrola, że test wyżej mierzy 120 Hz, a nie cokolwiek, co akurat jest w kodzie.
        Assert.AreEqual(120, FixedStep.SimulationHertz);
    }
}
