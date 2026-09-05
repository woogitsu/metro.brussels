using System;
using System.Collections.Generic;
using MetroBxl.Sim.Physics;
using MetroBxl.Sim.Runner;
using MetroBxl.Sim.Signalling;
using MetroBxl.Sim.Train;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace MetroBxl.Sim.Tests;

/// <summary>
/// Pomiar kosztu kroku linii (pozycja 5.7). Testy tutaj <b>nie sprawdzają czasu</b> —
/// czas na maszynie dzielonej z innymi procesami nie jest wielkością, którą wolno
/// przypiąć progiem. Sprawdzają to, bez czego zmierzony czas nic nie znaczy:
///
/// <list type="number">
/// <item>że okno wykonało dokładnie tyle kroków, ile deklaruje wynik;</item>
/// <item>że wszystkie okna policzyły <b>tę samą pracę</b> — inaczej mediana z ich
/// czasów jest medianą z dwóch różnych rzeczy;</item>
/// <item>że N w wyniku to liczba składów, które naprawdę weszły na plan, a nie liczba
/// zgłoszonych — bo oś mieści tylko tyle, ile pozwolą bloki;</item>
/// <item>że kolejność scenariuszy w pomiarze nie zmienia obsady linii.</item>
/// </list>
/// </summary>
[TestClass]
public sealed class LineBudgetTests
{
    private static readonly double[] Stations = { 0.0, 600.0, 1400.0, 2000.0 };

    /// <summary>
    /// Okno testowe: 24 000 kroków, czyli 200 s zegara linii. Tyle wystarczy, żeby przy
    /// odstępie 20 s wyjechał każdy z czterech składów — okno krótsze mierzyłoby linię,
    /// na którą część zgłoszonych składów jeszcze nie miała prawa wjechać, i test
    /// „N na planie" przechodziłby na złej przyczynie.
    /// </summary>
    private const long Window = 24_000L;

    private static LineBudgetScenario Scenario(
        int trains, double headwaySeconds, bool requireRoute = false, double turnbackSeconds = 0.0) =>
        new(
            SignallingPlanTests.SyntheticPlan(requireRoute, Stations),
            SignallingPlanTests.SyntheticAxis(Stations),
            RunConditions.Level(VehicleModel.M7, TrainLoad.Aw0),
            new LineRunSettings(Units.KmhToMps(60.0), 10.0, 1.0, 5.0),
            trains,
            headwaySeconds,
            turnbackSeconds,
            atp: false);

    // --- okno mierzy to, co deklaruje ----------------------------------------

    /// <summary>
    /// Wynik podaje tę liczbę kroków, którą zamówiono. Kontrola negatywna: pętla
    /// skrócona o jeden krok wywraca się na własnym sprawdzeniu w
    /// <see cref="LineBudget.Measure"/>, zamiast policzyć kroki na sekundę z liczby
    /// kroków, której nie wykonała.
    /// </summary>
    [TestMethod]
    public void Okno_wykonuje_dokladnie_tyle_krokow_ile_zamowiono()
    {
        var run = LineBudget.Measure(Scenario(2, 20.0), 500L);

        Assert.AreEqual(500L, run.Steps);
        Assert.IsTrue(run.WallSeconds > 0.0, "okno bez zmierzonego czasu nie jest pomiarem");
        Assert.AreEqual(run.Steps / run.WallSeconds, run.StepsPerSecond, 1e-9);
        Assert.AreEqual(run.WallSeconds * 1e6 / run.Steps, run.MicrosecondsPerStep, 1e-9);
    }

    /// <summary>Okno krótsze niż jeden krok nie istnieje.</summary>
    [TestMethod]
    public void Okno_bez_ani_jednego_kroku_jest_odmowa()
    {
        Assert.ThrowsException<ArgumentOutOfRangeException>(
            () => LineBudget.Measure(Scenario(1, 0.0), 0L));
        Assert.ThrowsException<ArgumentOutOfRangeException>(
            () => LineBudget.Census(Scenario(1, 0.0), -1L));
    }

    // --- wszystkie okna liczą tę samą pracę ----------------------------------

    /// <summary>
    /// Dwa okna tego samego scenariusza kończą się w <b>identycznym</b> stanie
    /// sygnalizacji, i taki sam ma spis. Bez tego mediana z powtórzeń byłaby medianą
    /// z różnych przebiegów: gdyby scenariusz był budowany raz i krokowany dalej,
    /// drugie okno zastałoby składy już na trasie.
    /// </summary>
    [TestMethod]
    public void Powtorzenia_koncza_sie_w_tym_samym_stanie_co_spis()
    {
        var scenario = Scenario(3, 20.0);

        var first = LineBudget.Measure(scenario, Window);
        var second = LineBudget.Measure(scenario, Window);
        var census = LineBudget.Census(scenario, Window);

        Assert.AreEqual(first.Digest, second.Digest);
        Assert.AreEqual(first.Digest, census.Digest);
        Assert.AreNotEqual(string.Empty, first.Digest);
    }

    /// <summary>
    /// Kontrola pozytywna do poprzedniego testu: odcisk stanu <b>umie</b> się różnić.
    /// Porównanie, które nigdy nie zawodzi, nie jest bramką — trzy składy zostawiają
    /// oś w innym stanie niż jeden i to musi być widać.
    /// </summary>
    [TestMethod]
    public void Odcisk_stanu_rozni_sie_miedzy_scenariuszami()
    {
        var one = LineBudget.Census(Scenario(1, 20.0), Window);
        var three = LineBudget.Census(Scenario(3, 20.0), Window);

        Assert.AreNotEqual(one.Digest, three.Digest);
    }

    // --- N w wyniku to składy na planie, nie zgłoszone ------------------------

    /// <summary>
    /// Spis liczy składy, które naprawdę weszły na plan. Kontrola negatywna: pomiar,
    /// który ignorowałby <c>--trains</c> i zgłaszał jeden skład, dałby tu
    /// <c>MaxOnLine == 1</c> przy każdym N — a daje cztery.
    /// </summary>
    [TestMethod]
    public void Spis_liczy_sklady_ktore_weszly_na_plan()
    {
        var census = LineBudget.Census(Scenario(4, 20.0), Window);

        Assert.AreEqual(4, census.Declared);
        Assert.AreEqual(4, census.MaxOnLine);
        Assert.IsTrue(
            census.MeanOnLine > 1.0 && census.MeanOnLine <= census.MaxOnLine,
            $"średnia obsada {census.MeanOnLine:F2} poza przedziałem (1, {census.MaxOnLine}]");
    }

    /// <summary>
    /// Zgłoszenie N składów nie znaczy N składów na osi. Przy odstępie zero wszystkie
    /// są wymagalne od kroku 0, ale peron początkowy mieści jeden — reszta czeka i to
    /// czekanie ma być widoczne w spisie, a nie ukryte w liczbie zgłoszonych.
    ///
    /// <para>Jest to jedyny powód, dla którego raport 5.7 podaje dwie kolumny N:
    /// bez tego rozróżnienia „koszt przy 32 składach" znaczyłoby koszt przy trzech.</para>
    /// </summary>
    [TestMethod]
    public void Sklady_ktore_nie_zmiescily_sie_na_osi_sa_policzone_osobno()
    {
        var census = LineBudget.Census(Scenario(8, 0.0), Window);

        Assert.AreEqual(8, census.Declared);
        Assert.IsTrue(census.MaxOnLine < 8, $"na oś weszło {census.MaxOnLine} z 8 — spis nie odróżnia obsady od zgłoszeń");
        Assert.IsTrue(census.MaxWaiting > 0, "przy odstępie zero ktoś musi czekać");
        Assert.IsTrue(census.MeanWaiting > 0.0, "średnia kolejka nie może być zerem, skoro maksimum nie jest");
    }

    // --- przeplot i mediana ---------------------------------------------------

    /// <summary>
    /// Pomiar wielu N naraz nie zależy od kolejności: ten sam scenariusz podany jako
    /// pierwszy i jako ostatni daje tę samą obsadę i ten sam odcisk stanu. Czasu ten
    /// test nie porównuje — porównuje go raport, i to jest jego rola.
    /// </summary>
    [TestMethod]
    public void Kolejnosc_scenariuszy_nie_zmienia_obsady()
    {
        var forward = LineBudget.Sweep(
            new List<LineBudgetScenario> { Scenario(1, 20.0), Scenario(4, 20.0) }, Window, 0, 2);
        var backward = LineBudget.Sweep(
            new List<LineBudgetScenario> { Scenario(4, 20.0), Scenario(1, 20.0) }, Window, 0, 2);

        Assert.AreEqual(forward[0].Census.MaxOnLine, backward[1].Census.MaxOnLine);
        Assert.AreEqual(forward[1].Census.MaxOnLine, backward[0].Census.MaxOnLine);
        Assert.AreEqual(forward[0].Census.Digest, backward[1].Census.Digest);
        Assert.AreEqual(forward[1].Census.Digest, backward[0].Census.Digest);
        Assert.AreEqual(2, forward[0].Runs.Count);
        Assert.AreEqual(2, forward[1].Runs.Count);
    }

    /// <summary>Mediana z nieparzystej liczby powtórzeń to środkowa, z parzystej — średnia dwóch środkowych.</summary>
    [TestMethod]
    public void Mediana_bierze_srodek_a_nie_srednia_wszystkiego()
    {
        var three = new List<LineBudgetRun>
        {
            Run(steps: 100L, wallSeconds: 1.0),      // 100 kroków/s
            Run(steps: 100L, wallSeconds: 0.5),      // 200 kroków/s
            Run(steps: 100L, wallSeconds: 0.01),     // 10000 kroków/s
        };
        Assert.AreEqual(200.0, LineBudget.MedianStepsPerSecond(three), 1e-9);

        var four = new List<LineBudgetRun>(three) { Run(steps: 100L, wallSeconds: 0.25) };
        Assert.AreEqual(300.0, LineBudget.MedianStepsPerSecond(four), 1e-9);

        Assert.ThrowsException<ArgumentException>(
            () => LineBudget.MedianStepsPerSecond(new List<LineBudgetRun>()));

        // Okno z zerowym czasem dałoby nieskończone kroki na sekundę i medianę,
        // która wygląda jak pomiar. Odmowa jest w konstruktorze, nie w medianie.
        Assert.ThrowsException<ArgumentOutOfRangeException>(() => Run(steps: 100L, wallSeconds: 0.0));
        Assert.ThrowsException<ArgumentOutOfRangeException>(() => Run(steps: 0L, wallSeconds: 1.0));
    }

    // --- odmowy scenariusza ---------------------------------------------------

    /// <summary>
    /// Odstęp krótszy niż krok symulacji zaokrągliłby się do zera i po cichu zamienił
    /// rozkład na „wszyscy naraz". Odmowa, nie zaokrąglenie.
    /// </summary>
    [TestMethod]
    public void Odstep_krotszy_niz_krok_symulacji_jest_odmowa()
    {
        Assert.ThrowsException<ArgumentOutOfRangeException>(
            () => Scenario(2, 0.001));
        Assert.ThrowsException<ArgumentOutOfRangeException>(
            () => Scenario(2, -1.0));
        Assert.ThrowsException<ArgumentOutOfRangeException>(
            () => Scenario(0, 10.0));

        // Zero jest dozwolone i znaczy „wszyscy zgłoszeni na krok 0".
        Assert.AreEqual(0L, Scenario(2, 0.0).HeadwaySteps);
        Assert.AreEqual(FixedStep.SimulationHertz, (int)Scenario(2, 1.0).HeadwaySteps);
    }

    /// <summary>Pomiar bez powtórzeń i bez scenariuszy jest odmową, a nie pustym wynikiem.</summary>
    [TestMethod]
    public void Pomiar_bez_powtorzen_albo_bez_scenariuszy_jest_odmowa()
    {
        var one = new List<LineBudgetScenario> { Scenario(1, 20.0) };

        Assert.ThrowsException<ArgumentOutOfRangeException>(() => LineBudget.Sweep(one, 100L, 0, 0));
        Assert.ThrowsException<ArgumentOutOfRangeException>(() => LineBudget.Sweep(one, 100L, -1, 1));
        Assert.ThrowsException<ArgumentException>(
            () => LineBudget.Sweep(new List<LineBudgetScenario>(), 100L, 0, 1));
    }

    private static LineBudgetRun Run(long steps, double wallSeconds) =>
        new(steps, wallSeconds, wallSeconds, "odcisk-z-reki");
}
