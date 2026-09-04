using System;
using MetroBxl.Sim.Physics;
using MetroBxl.Sim.Signalling;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace MetroBxl.Sim.Tests;

/// <summary>
/// Nastawnia automatyczna: kto rygluje trasy i jak często pyta.
///
/// <para><b>Skąd ta klasa się wzięła.</b> Reguła istniała w tym repozytorium od T-313,
/// ale wyłącznie w PRYWATNEJ KLASIE TESTU (<c>ClassicSignallingScenarioTests.Runner</c>).
/// Produkcyjnie nie ryglował tras nikt, a <see cref="MetroBxl.Sim.Line.LineCore"/> na
/// planie, który ich wymaga, w ogóle nie ruszał — 47,00 m i <c>BlockNotReserved</c>.
/// Testy tej klasy pilnują reguły, nie przypadku: każdy z warunków, które powodują
/// bezczynność, ma tu własny test.</para>
/// </summary>
[TestClass]
public sealed class RouteDispatcherTests
{
    private static readonly double[] Stations = { 0.0, 600.0, 1400.0, 2000.0 };
    private const double TrainLengthM = 94.0;

    private static SignallingPlan Plan(bool requireRoute) =>
        SignallingPlanTests.SyntheticPlan(requireRoute, Stations);

    private static (FixedBlockSystem System, RouteDispatcher Dispatcher) Setup(
        bool requireRoute = true, long interval = RouteDispatcher.DefaultRequestIntervalSteps)
    {
        var plan = Plan(requireRoute);
        var system = new FixedBlockSystem(plan);
        system.RegisterTrain("A", 0.0, TrainLengthM);
        return (system, new RouteDispatcher(plan, interval));
    }

    [TestMethod]
    public void LocksTheRouteLeavingTheBlockTheTrainStandsIn()
    {
        var (system, dispatcher) = Setup();
        Assert.IsNull(system.RouteOf("A"), "skład nie ma prawa startować z zaryglowaną trasą");

        Assert.IsTrue(dispatcher.Dispatch(system, "A", 0.0, 0L), "trasa nie została zaryglowana");
        Assert.AreEqual(1, dispatcher.Locked);
        Assert.AreEqual(0, dispatcher.Refused);
        Assert.IsNotNull(system.RouteOf("A"));

        // Autorytet MUSI się wydłużyć — inaczej ryglowanie byłoby zapisem bez skutku.
        Assert.IsTrue(system.Authority("A").DistanceM > 500.0,
            $"autorytet {system.Authority("A")} nie wyszedł za blok peronowy");
    }

    [TestMethod]
    public void DoesNothingWhenThePlanDoesNotRequireRoutes()
    {
        // Nie optymalizacja, a poprawność: bez wymogu tras autorytet nie zależy od
        // rezerwacji, więc zaryglowanie niczego nie odblokuje, a ODEJMIE pojemność —
        // rezerwacja odrzuca cudze żądania i skraca cudzy autorytet.
        var (system, dispatcher) = Setup(requireRoute: false);
        var before = system.Authority("A").DistanceM;

        Assert.IsFalse(dispatcher.Dispatch(system, "A", 0.0, 0L));
        Assert.AreEqual(0, dispatcher.Locked);
        Assert.AreEqual(0, dispatcher.Refused);
        Assert.IsNull(system.RouteOf("A"), "zaryglowano trasę, której plan nie wymaga");
        Assert.AreEqual(before, system.Authority("A").DistanceM, 0.0,
            "autorytet się zmienił, choć nastawnia miała nic nie robić");
    }

    [TestMethod]
    public void DoesNotAskAgainWhileTheTrainAlreadyHoldsARoute()
    {
        var (system, dispatcher) = Setup();
        Assert.IsTrue(dispatcher.Dispatch(system, "A", 0.0, 0L));

        // Sto kroków później, długo po odstępie: skład ma trasę, więc pytania nie ma.
        // `RequestRoute` odrzuciłoby to jako `train-already-routed`, czyli odmowa
        // trafiłaby do strumienia zdarzeń jako zdarzenie, którego nikt nie potrzebuje.
        for (var step = 200L; step < 2000L; step += 200L)
        {
            Assert.IsFalse(dispatcher.Dispatch(system, "A", 0.0, step));
        }

        Assert.AreEqual(1, dispatcher.Locked);
        Assert.AreEqual(0, dispatcher.Refused, "policzono odmowę, choć nastawnia nie pytała");
    }

    [TestMethod]
    public void AsksAtMostOncePerIntervalAndTheIntervalIsMeasuredInSteps()
    {
        // Odstęp jest treścią, nie ozdobą: odmowa jest normalną odpowiedzią i trafia
        // do strumienia zdarzeń, więc pytanie co krok zalałoby go niczym. Zmierzone
        // na pakiecie A: dwa składy dają 1118 odmów przy odstępie sekundy w 60 000
        // krokach; przy pytaniu co krok byłoby ich dwa rzędy wielkości więcej.
        var plan = Plan(requireRoute: true);
        var system = new FixedBlockSystem(plan);
        system.RegisterTrain("A", 0.0, TrainLengthM);
        system.RegisterTrain("B", 600.0, TrainLengthM);
        var dispatcher = new RouteDispatcher(plan, requestIntervalSteps: 120L);

        // B stoi na P02, czyli w bloku docelowym trasy A — żądanie A musi zostać odrzucone.
        Assert.IsFalse(dispatcher.Dispatch(system, "A", 0.0, 0L));
        Assert.AreEqual(1, dispatcher.Refused, "pierwsza odmowa nie została policzona");

        // W obrębie odstępu nastawnia MILCZY, więc licznik odmów nie rośnie.
        for (var step = 1L; step < 120L; step++)
        {
            Assert.IsFalse(dispatcher.Dispatch(system, "A", 0.0, step));
        }

        Assert.AreEqual(1, dispatcher.Refused, "nastawnia pytała częściej niż raz na odstęp");

        // Dokładnie na odstępie pyta znowu. Granica należy do pytania: `>=`, nie `>`.
        Assert.IsFalse(dispatcher.Dispatch(system, "A", 0.0, 120L));
        Assert.AreEqual(2, dispatcher.Refused, "nastawnia nie zapytała po upływie odstępu");
    }

    [TestMethod]
    public void DoesNothingPastTheLastPlatform()
    {
        // Za ostatnim peronem nie ma dokąd ryglować i to nie jest usterka: autorytet
        // kończy się wtedy na `EndOfLine`. Bez tego warunku nastawnia pytałaby o trasę
        // co sekundę do końca przebiegu i produkowała odmowy bez treści.
        var plan = Plan(requireRoute: true);
        var system = new FixedBlockSystem(plan);
        system.RegisterTrain("A", 2000.0, TrainLengthM);
        var dispatcher = new RouteDispatcher(plan, RouteDispatcher.DefaultRequestIntervalSteps);

        Assert.IsNull(plan.NextRouteFrom(2000.0), "oś testowa ma jednak trasę za ostatnim peronem");
        Assert.IsFalse(dispatcher.Dispatch(system, "A", 2000.0, 0L));
        Assert.AreEqual(0, dispatcher.Locked);
        Assert.AreEqual(0, dispatcher.Refused, "policzono odmowę, choć nie było o co pytać");
    }

    [TestMethod]
    public void RefusesANonPositiveInterval()
    {
        // Odstęp zerowy to nie „pytaj zawsze", tylko utrata jedynego zapisu tego, co
        // robiła sygnalizacja. Dlatego jest odmową w konstruktorze, a nie wartością.
        foreach (var bad in new[] { 0L, -1L, -120L })
        {
            Assert.ThrowsException<ArgumentOutOfRangeException>(
                () => new RouteDispatcher(Plan(requireRoute: true), bad), $"odstęp {bad} przeszedł");
        }
    }

    [TestMethod]
    public void RefusesAMissingPlanOrSystemOrTrain()
    {
        var (system, dispatcher) = Setup();
        Assert.ThrowsException<ArgumentNullException>(() => new RouteDispatcher(null!));
        Assert.ThrowsException<ArgumentNullException>(() => dispatcher.Dispatch(null!, "A", 0.0, 0L));
        Assert.ThrowsException<ArgumentNullException>(() => dispatcher.Dispatch(system, null!, 0.0, 0L));
    }
}
