using System;
using System.Collections.Generic;
using System.Linq;
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

    /// <summary>
    /// Nastawnia z zajętym blokiem docelowym: KAŻDE żądanie, które przejdzie przez dławik,
    /// kończy się odmową, więc <see cref="RouteDispatcher.Refused"/> liczy dokładnie tyle,
    /// ile razy nastawnia zapytała. To jest jedyny sposób, żeby zmierzyć LICZBĘ żądań
    /// w oknie czasu, a nie sam fakt, że coś się wydarzyło.
    /// </summary>
    private static (FixedBlockSystem System, RouteDispatcher Dispatcher) SetupWithBlockedTarget(long interval)
    {
        var plan = Plan(requireRoute: true);
        var system = new FixedBlockSystem(plan);
        system.RegisterTrain("A", 0.0, TrainLengthM);
        system.RegisterTrain("B", 600.0, TrainLengthM);
        return (system, new RouteDispatcher(plan, interval));
    }

    /// <summary>
    /// Woła nastawnię w KAŻDYM kroku z podanego zakresu i zwraca numery kroków, w których
    /// naprawdę zapytała. Bez tej listy test widziałby tylko „coś się wydarzyło"; z nią
    /// widzi rozstaw pytań, czyli treść dławika.
    /// </summary>
    private static List<long> StepsOnWhichItAsked(
        FixedBlockSystem system, RouteDispatcher dispatcher, long fromStep, long toStepExclusive)
    {
        var asked = new List<long>();
        var refusedBefore = dispatcher.Refused;
        for (var step = fromStep; step < toStepExclusive; step++)
        {
            dispatcher.Dispatch(system, "A", 0.0, step);
            if (dispatcher.Refused != refusedBefore)
            {
                asked.Add(step);
                refusedBefore = dispatcher.Refused;
            }
        }

        return asked;
    }

    [TestMethod]
    public void MeasuresEachIntervalFromTheLastRequestAndNotFromStepZero()
    {
        // DZIURA, KTÓRĄ TEN TEST ZAMYKA. Do 05.09.2026 jedyny test odstępu
        // (`AsksAtMostOncePerIntervalAndTheIntervalIsMeasuredInSteps`) zaczynał od kroku 0,
        // czyli od jedynej wartości, przy której `steps - last` i `steps + last` są TYM
        // SAMYM wyrażeniem — bo `last == 0`. Mutacja `steps - last` → `steps + last`
        // przeżyła przez to dwie niezależne przeglądy mutacyjne, 376/376 bez mrugnięcia,
        // choć na pakiecie A podnosiła liczbę odmów ze 158 do 18 748 (119×), a strumień
        // zdarzeń sygnalizacji z 513 do 37 693. Po pierwszym żądaniu `last` przestaje być
        // zerem i suma natychmiast przekracza odstęp, więc dławik milknie na zawsze.
        //
        // Dlatego tu: pierwsze żądanie pada na kroku NIEZEROWYM, a odstęp jest sprawdzany
        // po DRUGIM i po TRZECIM żądaniu — czyli dokładnie tam, gdzie `last > 0`.
        const long Interval = 120L;
        var (system, dispatcher) = SetupWithBlockedTarget(Interval);

        // Zegar linii nie startuje od zera dla każdego składu: `LineCore` wpuszcza kolejne
        // obiegi w środku przebiegu, więc pierwsze żądanie tego składu pada na kroku 1000.
        var asked = StepsOnWhichItAsked(system, dispatcher, fromStep: 1000L, toStepExclusive: 1361L);

        CollectionAssert.AreEqual(
            new List<long> { 1000L, 1120L, 1240L, 1360L },
            asked,
            "nastawnia pytała na krokach " + string.Join(", ", asked) +
            " — odstęp nie jest liczony od OSTATNIEGO żądania");

        // Ta sama własność wyrażona odstępami, żeby komunikat błędu mówił, o co chodzi.
        var gaps = asked.Zip(asked.Skip(1), (a, b) => b - a).ToArray();
        foreach (var gap in gaps)
        {
            Assert.AreEqual(Interval, gap,
                $"przerwa {gap} kroków zamiast {Interval}; przerwy: {string.Join(", ", gaps)}");
        }

        Assert.AreEqual(4, dispatcher.Refused, "licznik odmów nie zgadza się z liczbą pytań");
        Assert.AreEqual(0, dispatcher.Locked, "blok docelowy jest zajęty, nic nie mogło się zaryglować");
    }

    [TestMethod]
    public void AsksTenTimesInTenSecondsWhenCalledOnEveryStep()
    {
        // Odstęp to LICZBA żądań w oknie czasu, nie sam fakt, że nastawnia kiedyś milczy.
        // Dziesięć sekund symulacji przy 120 Hz to 1200 wywołań `Dispatch`; przy odstępie
        // sekundy ma z nich wyjść DZIESIĘĆ żądań. Bez dławika byłoby ich 1200, a z dławikiem
        // zepsutym po pierwszym żądaniu (`steps + last`) — 1081, i to jest ta liczba, której
        // żaden wcześniejszy test nie umiał odróżnić od dziesięciu.
        const long Interval = RouteDispatcher.DefaultRequestIntervalSteps; // 120 kroków = 1 s
        const long Window = 10L * Interval;
        var (system, dispatcher) = SetupWithBlockedTarget(Interval);

        var asked = StepsOnWhichItAsked(system, dispatcher, fromStep: 0L, toStepExclusive: Window);

        Assert.AreEqual(10, asked.Count,
            $"w oknie {Window} kroków padło {asked.Count} żądań zamiast 10");
        Assert.AreEqual(10, dispatcher.Refused, "każde żądanie w tym oknie musi być odmową");
        CollectionAssert.AreEqual(
            Enumerable.Range(0, 10).Select(i => i * Interval).ToList(),
            asked,
            "żądania nie leżą co sekundę: " + string.Join(", ", asked));
    }

    [TestMethod]
    public void KeepsTheIntervalPerTrainAndNotGlobally()
    {
        // Dławik jest słownikiem po składzie i to jest treść, nie szczegół implementacji:
        // gdyby był jedną liczbą, żądanie składu B kasowałoby odstęp składu A i pierwszy
        // z brzegu skład zagłodziłby resztę linii. Sprawdzane po drugim żądaniu każdego
        // z nich, czyli przy `last > 0` dla obu.
        const long Interval = 120L;
        var plan = Plan(requireRoute: true);
        var system = new FixedBlockSystem(plan);
        system.RegisterTrain("A", 0.0, TrainLengthM);
        system.RegisterTrain("B", 600.0, TrainLengthM);
        system.RegisterTrain("C", 1400.0, TrainLengthM);
        var dispatcher = new RouteDispatcher(plan, Interval);

        // A pyta o trasę do bloku B, B o trasę do bloku C — obie odmowy, obie policzone.
        Assert.IsFalse(dispatcher.Dispatch(system, "A", 0.0, 500L));
        Assert.IsFalse(dispatcher.Dispatch(system, "B", 600.0, 560L));
        Assert.AreEqual(2, dispatcher.Refused);

        // Krok 620: dla A minęło 120, dla B dopiero 60. Pyta więc TYLKO A.
        Assert.IsFalse(dispatcher.Dispatch(system, "B", 600.0, 620L));
        Assert.AreEqual(2, dispatcher.Refused, "B zapytał po 60 krokach, choć odstęp to 120");
        Assert.IsFalse(dispatcher.Dispatch(system, "A", 0.0, 620L));
        Assert.AreEqual(3, dispatcher.Refused, "A nie zapytał, choć minął mu pełny odstęp");

        // Krok 680: teraz odwrotnie — B ma pełne 120 od 560, A dopiero 60 od 620.
        Assert.IsFalse(dispatcher.Dispatch(system, "A", 0.0, 680L));
        Assert.AreEqual(3, dispatcher.Refused, "A zapytał po 60 krokach, choć odstęp to 120");
        Assert.IsFalse(dispatcher.Dispatch(system, "B", 600.0, 680L));
        Assert.AreEqual(4, dispatcher.Refused, "B nie zapytał, choć minął mu pełny odstęp");
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
