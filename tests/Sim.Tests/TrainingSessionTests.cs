using System;
using System.Collections.Generic;
using System.Linq;
using MetroBxl.Sim.Line;
using MetroBxl.Sim.Physics;
using MetroBxl.Sim.Signalling;
using MetroBxl.Sim.Train;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace MetroBxl.Sim.Tests;

/// <summary>
/// Warunek końca przejazdu gracza — to, czego brakowało, żeby pętla gry
/// <b>start → cel → wynik → ponów</b> miała gdzie się zamknąć (MB-02).
///
/// <para>Testy pilnują pięciu rzeczy, z których każda potrafi wyglądać jak działająca
/// i nią nie być: <b>że wynik powstaje DOKŁADNIE RAZ</b>, <b>że nie powstaje przy
/// otwartych drzwiach</b> (pułapka <c>NaN</c>), <b>że minięcie celu kończy sesję,
/// a minięcie nie-celu nie</b>, <b>że zdarzenie ATP to zbocze, a nie krok</b>,
/// i <b>że reset czyści także pamięć zboczy</b>.</para>
///
/// <para>Czego tu NIE ma: fizyki. Ta klasa nie liczy ani jednej siły — testy podają
/// stan wprost przez <see cref="StationService.Filter"/>, żeby wynik nie zależał od
/// hamowania. Ta sama granica, co w <see cref="StationServiceTests"/>.</para>
/// </summary>
[TestClass]
public sealed class TrainingSessionTests
{
    private static readonly FixedStep Step = FixedStep.Simulation;

    private static List<AxisStation> Stations() => new()
    {
        new AxisStation("Start", 0.0, "s0"),
        new AxisStation("Pierwsza", 500.0, "s1"),
        new AxisStation("Druga", 1200.0, "s2"),
        new AxisStation("Trzecia", 1900.0, "s3"),
    };

    private static StationService Service(double windowM = 5.0, double exchangeSeconds = 0.0)
        => new(Stations(), new DoorCycle(exchangeSeconds), Step, windowM);

    private static TrainingSession Session(params string[] targets)
        => new(Stations(), targets, Step);

    private static DriveState Stopped(double distanceM, long steps = 0)
        => new(steps, 0.0, distanceM, 0.0);

    private static DriveState Moving(double distanceM, double speedMps, long steps = 0)
        => new(steps, speedMps, distanceM, 0.0);

    /// <summary>
    /// Postój do końca cyklu drzwi, krok po kroku — tak, jak robi to scena: JEDEN
    /// <see cref="StationService.Filter"/> i JEDEN <see cref="TrainingSession.Observe"/>
    /// na krok.
    /// </summary>
    private static long ObsluzPostoj(
        StationService service, TrainingSession session, double chainageM, long steps)
    {
        // Z zapasem: pełny cykl przy zerowej wymianie to 8,5 s, czyli 1020 kroków.
        for (var i = 0; i < 4000; i++)
        {
            var state = Stopped(chainageM, steps);
            service.Filter(state, DriverCommand.Coast, chainageM);
            session.Observe(service, state, null);
            steps++;
            if (!service.AtStation)
            {
                return steps;
            }
        }

        Assert.Fail("cykl drzwi nie domknął się w 4000 krokach");
        return steps;
    }

    [TestMethod]
    public void TwoStopsPassTheSessionAndTheResultIsBuiltFromMeasuredFacts()
    {
        var service = Service();
        var session = Session("s1", "s2");
        long steps = 0;

        steps = ObsluzPostoj(service, session, 499.5, steps);
        Assert.IsFalse(session.Finished, "sesja skończyła się po PIERWSZYM celu z dwóch");

        steps = ObsluzPostoj(service, session, 1201.25, steps);

        Assert.IsTrue(session.Finished, "sesja nie skończyła się po obsłużeniu obu celów");
        var result = session.Result!.Value;
        Assert.AreEqual(TrainingEnding.AllTargetsServed, result.Ending,
            "dwa poprawne postoje dały inne zakończenie niż „wszystkie cele obsłużone”");
        Assert.IsTrue(result.Passed, "dwa poprawne postoje nie dały zaliczenia");
        Assert.AreEqual(2, result.TargetsServed,
            "wynik nie policzył obu obsłużonych celów");
        Assert.AreEqual(-0.5, result.Targets[0].StopErrorM!.Value, 1e-9,
            "błąd zatrzymania pierwszego celu nie jest MIERZONY");
        Assert.AreEqual(1.25, result.Targets[1].StopErrorM!.Value, 1e-9,
            "błąd zatrzymania drugiego celu nie jest MIERZONY");
        Assert.AreEqual("Pierwsza", result.Targets[0].DisplayName,
            "nazwa celu nie przyszła z osi — panel pokazałby graczowi identyfikator GTFS");
        // `steps` wskazuje krok NASTĘPNY po domknięciu drzwi, a zatrzask pada W kroku
        // domykającym — i to jest zmierzone, nie założone: pierwsza wersja tej asercji
        // różniła się o dokładnie jeden krok (17,016667 s wobec 17,008333 s, czyli
        // 1/120 s). Różnica jest treścią: wynik opisuje stan składu w chwili, w której
        // sesja się skończyła, a nie w chwili, w której ktoś na niego spojrzał.
        var krokZamkniecia = steps - 1;
        Assert.AreEqual(Step.TimeAt(krokZamkniecia), result.TotalSeconds, 1e-9,
            "czas wyniku nie jest czasem symulacji w chwili zakończenia");
    }

    [TestMethod]
    public void TheResultIsNOTBuiltWhileTheDoorsAreStillOpen()
    {
        // NAJWAŻNIEJSZY TEST TEJ KLASY. `StationService` wpisuje wywołanie
        // z `DepartureSeconds = double.NaN` już przy ZATRZYMANIU, a domyka je dopiero
        // przy ruszeniu. Warunek napisany jako `!= double.NaN` jest ZAWSZE prawdziwy —
        // także dla samego NaN — więc wynik powstałby tu, z otwartymi drzwiami,
        // i wyglądałby dokładnie tak samo jak poprawny.
        var service = Service();
        var session = Session("s1");

        var state = Stopped(500.0);
        service.Filter(state, DriverCommand.Coast, 500.0);
        session.Observe(service, state, null);

        Assert.IsTrue(service.AtStation, "cykl drzwi w ogóle się nie zaczął");
        Assert.AreEqual(1, service.Calls.Count,
            "zatrzymanie w oknie nie zostało zapisane jako wywołanie stacji");
        Assert.IsTrue(double.IsNaN(service.Calls[0].DepartureSeconds),
            "wywołanie domknęło się w kroku zatrzymania — ten test przestał mierzyć pułapkę");
        Assert.IsFalse(session.Finished, "wynik powstał przy OTWARTYCH drzwiach");

        var steps = ObsluzPostoj(service, session, 500.0, 0);
        Assert.IsTrue(session.Finished, "wynik nie powstał po domknięciu drzwi");
        Assert.IsTrue(steps > 1, "postój trwał jeden krok");
    }

    [TestMethod]
    public void TheResultIsNOTBuiltWhileTheTrainIsStillRolling()
    {
        // Druga połowa warunku z `docs/PLAYABILITY.md` §3: „drzwi są zamknięte
        // I SKŁAD STOI". Bez niej sesja kończyłaby się na składzie toczącym się
        // z peronu — cykl drzwi już domknięty, a pociąg w ruchu.
        var service = Service();
        var session = Session("s1");
        ObsluzPostoj(service, session, 500.0, 0);
        Assert.IsTrue(session.Finished,
            "kontrola przyrządu: postój OBSERWOWANY co krok kończy sesję — bez tego "
            + "drugi przebieg nie miałby z czym się różnić");

        var wRuchu = Service();
        var sesjaWRuchu = Session("s1");
        var kroki = ObsluzPostojBezObserwacji(wRuchu, 500.0);
        sesjaWRuchu.Observe(wRuchu, Moving(505.0, 2.0, kroki), null);
        Assert.IsFalse(sesjaWRuchu.Finished, "sesja skończyła się na składzie W RUCHU");

        sesjaWRuchu.Observe(wRuchu, Stopped(505.0, kroki), null);
        Assert.IsTrue(sesjaWRuchu.Finished, "sesja nie skończyła się po zatrzymaniu");
    }

    private static long ObsluzPostojBezObserwacji(StationService service, double chainageM)
    {
        long steps = 0;
        for (var i = 0; i < 4000 && (i == 0 || service.AtStation); i++)
        {
            service.Filter(Stopped(chainageM, steps), DriverCommand.Coast, chainageM);
            steps++;
        }

        Assert.IsFalse(service.AtStation, "cykl drzwi nie domknął się");
        return steps;
    }

    [TestMethod]
    public void MissingAREQUIREDTargetEndsTheSessionAsAFailure()
    {
        var service = Service();
        var session = Session("s1", "s2");

        // Skład przejeżdża pierwszy cel bez zatrzymania: 506 m to `cel + okno + 1 m`.
        var state = Moving(506.0, 12.0);
        service.Filter(state, DriverCommand.FullPower, 506.0);
        session.Observe(service, state, null);

        Assert.AreEqual(1, service.Missed.Count, "stacja nie została uznana za miniętą");
        Assert.IsTrue(session.Finished, "minięty CEL nie zakończył sesji");
        var result = session.Result!.Value;
        Assert.AreEqual(TrainingEnding.TargetMissed, result.Ending,
            "minięty cel dał inne zakończenie niż „cel minięty”");
        Assert.IsFalse(result.Passed, "sesja z miniętym celem wyszła zaliczona");
        Assert.AreEqual(0, result.TargetsServed,
            "wynik policzył obsłużony cel, choć skład nie zatrzymał się ani razu");
        Assert.IsNull(result.Targets[0].StopErrorM,
            "cel pominięty dostał błąd zatrzymania — a nie ma czego mierzyć");
    }

    [TestMethod]
    public void MissingASTATIONTHATISNOTATargetDoesNotEndTheSession()
    {
        // Kontrakt M1 mówi o „miniętym WYMAGANYM celu". Oś pakietu A ma dwanaście
        // stacji przy dwóch celach — przejechanie trzeciej bez zatrzymania jest poza
        // zadaniem, a nie porażką w nim.
        var service = Service();
        var session = Session("s2");

        var state = Moving(506.0, 12.0);
        service.Filter(state, DriverCommand.FullPower, 506.0);
        session.Observe(service, state, null);

        Assert.AreEqual(1, service.Missed.Count,
            "stacja spoza celów nie została uznana za miniętą — test mierzy co innego");
        Assert.AreEqual("s1", service.Missed[0].StopId, "minięta jest inna stacja, niż test zakłada");
        Assert.IsFalse(session.Finished, "minięcie stacji spoza celów zakończyło sesję");

        ObsluzPostoj(service, session, 1200.0, 0);
        Assert.IsTrue(session.Finished, "sesja nie skończyła się po obsłużeniu swojego celu");
        Assert.IsTrue(session.Result!.Value.Passed,
            "minięcie stacji spoza celów odebrało zaliczenie");
    }

    [TestMethod]
    public void AnAtpEventIsANEDGEOfThePredicateNotAStep()
    {
        // Decyzja właściciela z 13.09.2026: „policz osobne zdarzenia".
        // `CabProtection` liczy KROKI i zostaje przy tym — odpowiada na inne pytanie.
        var service = Service();
        var session = Session("s1");

        var overspeed = Decyzja(ProtectionAction.None, overspeed: true);
        for (var i = 0; i < 120; i++)
        {
            session.Observe(service, Moving(100.0, 20.0, i), overspeed);
        }

        session.Observe(service, Moving(100.0, 10.0, 120), Decyzja(ProtectionAction.None));
        for (var i = 0; i < 120; i++)
        {
            session.Observe(service, Moving(100.0, 20.0, 121 + i), overspeed);
        }

        var steps = ObsluzPostoj(service, session, 500.0, 241);
        Assert.IsTrue(steps > 241,
            "postój nie ruszył licznika kroków — dwa ciągi ostrzeżeń nie zdążyły się policzyć");
        var result = session.Result!.Value;
        Assert.AreEqual(2L, result.AtpWarningEvents,
            "240 kroków nad limitem w DWÓCH ciągach dało inną liczbę niż 2 zdarzenia");
        Assert.AreEqual(0L, result.AtpInterventionEvents,
            "samo ostrzeżenie policzyło się jako ingerencja");
    }

    [TestMethod]
    public void EscalationFromServiceToEmergencyIsONEInterventionAndONEEmergency()
    {
        // Konsekwencja reguły „zbocze predykatu", wypisana wprost, żeby nie była
        // niespodzianką: ochrona nie sięgnęła po hamulec drugi raz, tylko po mocniejszy.
        var service = Service();
        var session = Session("s1");

        session.Observe(service, Moving(100.0, 20.0, 0),
            Decyzja(ProtectionAction.ServiceIntervention, overspeed: true));
        session.Observe(service, Moving(100.0, 20.0, 1),
            Decyzja(ProtectionAction.EmergencyIntervention, overspeed: true));
        session.Observe(service, Moving(100.0, 20.0, 2),
            Decyzja(ProtectionAction.EmergencyIntervention, overspeed: true));

        ObsluzPostoj(service, session, 500.0, 3);
        var result = session.Result!.Value;
        Assert.AreEqual(1L, result.AtpInterventionEvents,
            "eskalacja policzyła się jako druga ingerencja");
        Assert.AreEqual(1L, result.AtpEmergencyEvents,
            "zbocze ingerencji awaryjnej policzyło się inaczej niż raz");
        Assert.AreEqual(1L, result.AtpWarningEvents,
            "jeden ciąg przekroczenia dał inną liczbę ostrzeżeń niż jedno");
    }

    [TestMethod]
    public void ObserveIsIdempotentWithinAStep()
    {
        // `StationService.Filter` trzeba wołać DOKŁADNIE RAZ na krok, bo posuwa licznik
        // drzwi. Ta klasa nie posuwa niczego, więc drugie wołanie w kroku nie może
        // zmienić ani wyniku, ani liczników — inaczej zapis wejść odtworzony przy innym
        // podziale kroków na klatki dałby inny wynik.
        var jedno = Service();
        var sesjaJedno = Session("s1");
        var dwa = Service();
        var sesjaDwa = Session("s1");

        var decyzja = Decyzja(ProtectionAction.ServiceIntervention, overspeed: true);
        for (long i = 0; i < 60; i++)
        {
            sesjaJedno.Observe(jedno, Moving(100.0, 20.0, i), decyzja);
            sesjaDwa.Observe(dwa, Moving(100.0, 20.0, i), decyzja);
            sesjaDwa.Observe(dwa, Moving(100.0, 20.0, i), decyzja);
        }

        ObsluzPostoj(jedno, sesjaJedno, 500.0, 60);
        ObsluzPostojZPodwojnaObserwacja(dwa, sesjaDwa, 500.0, 60);

        Assert.AreEqual(
            sesjaJedno.Result!.Value.ToString(),
            sesjaDwa.Result!.Value.ToString(),
            "drugie wołanie `Observe` w kroku zmieniło wynik");
    }

    private static void ObsluzPostojZPodwojnaObserwacja(
        StationService service, TrainingSession session, double chainageM, long steps)
    {
        for (var i = 0; i < 4000; i++)
        {
            var state = Stopped(chainageM, steps);
            service.Filter(state, DriverCommand.Coast, chainageM);
            session.Observe(service, state, null);
            session.Observe(service, state, null);
            steps++;
            if (!service.AtStation)
            {
                return;
            }
        }

        Assert.Fail("cykl drzwi nie domknął się w 4000 krokach");
    }

    [TestMethod]
    public void TheResultIsBuiltEXACTLYONCE()
    {
        var service = Service();
        var session = Session("s1");
        var steps = ObsluzPostoj(service, session, 500.0, 0);
        Assert.IsTrue(session.Finished,
            "sesja nie skończyła się — nie ma czego liczyć dwa razy");
        var pierwszy = session.Result!.Value.ToString();

        // Sto kroków po zakończeniu — tyle, ile scena zdąży przerobić, zanim gracz
        // spojrzy na panel wyniku. Ani czas, ani liczniki ATP nie mają drgnąć.
        for (var i = 0; i < 100; i++)
        {
            session.Observe(service, Moving(600.0, 5.0, steps + i),
                Decyzja(ProtectionAction.EmergencyIntervention, overspeed: true));
        }

        Assert.AreEqual(pierwszy, session.Result!.Value.ToString(),
            "wynik przeliczył się po zakończeniu sesji — rósł o czas spędzony na ekranie wyniku");
    }

    [TestMethod]
    public void ResetClearsTheResultTheCountersANDTheEdgeMemory()
    {
        var service = Service();
        var session = Session("s1");
        session.Observe(service, Moving(100.0, 20.0, 0),
            Decyzja(ProtectionAction.ServiceIntervention, overspeed: true));
        ObsluzPostoj(service, session, 500.0, 1);
        Assert.IsTrue(session.Finished,
            "sesja nie skończyła się przed resetem — test mierzy co innego");

        service.Reset();
        session.Reset();

        Assert.IsFalse(session.Finished, "reset nie zdjął wyniku");
        Assert.AreEqual(TrainingEnding.Running, session.Ending,
            "po resecie zakończenie nie wróciło do „sesja trwa”");
        CollectionAssert.AreEqual(
            new[] { "s1" }, session.TargetStopIds.ToArray(),
            "reset ruszył CELE — a to jest inne zadanie, nie ta sama sesja od nowa");

        // PAMIĘĆ ZBOCZA też wraca do fałszu. Gdyby została, ta ingerencja nie
        // policzyłaby się, bo predykat byłby „nadal prawdziwy" z poprzedniej sesji.
        session.Observe(service, Moving(100.0, 20.0, 0),
            Decyzja(ProtectionAction.ServiceIntervention, overspeed: true));
        ObsluzPostoj(service, session, 500.0, 1);
        Assert.AreEqual(1L, session.Result!.Value.AtpInterventionEvents,
            "pierwsza ingerencja po resecie nie policzyła się — pamięć zbocza przeżyła reset");
    }

    [TestMethod]
    public void ATargetThatIsTheAXISSTARTINGPOINTIsRefusedAtConstruction()
    {
        // Najważniejsza z czterech kontroli konstruktora. `StationService` pomija stację
        // o indeksie 0 jako miejsce, na którym skład stoi na starcie, więc taki cel nie
        // trafiłby ANI do `Calls`, ANI do `Missed` — sesja czekałaby bez końca
        // i wyglądałoby to na zawieszoną grę, a nie na błędne zadanie.
        var wyjatek = Assert.ThrowsException<ArgumentException>(() => Session("s0"),
            "cel będący punktem startowym osi został przyjęty — sesja czekałaby na niego bez końca");
        StringAssert.Contains(wyjatek.Message, "punktem startowym",
            "wyjątek nie mówi, CZYM ten cel jest — komunikat bez powodu każe czytać kod");

        StringAssert.Contains(
            Assert.ThrowsException<ArgumentException>(() => Session("s9"),
                "cel spoza osi został przyjęty").Message,
            "nie występuje na tej osi",
            "wyjątek o celu spoza osi nie mówi, na czym polega błąd");
        StringAssert.Contains(
            Assert.ThrowsException<ArgumentException>(() => Session("s1", "s1"),
                "ten sam cel podany dwa razy został przyjęty").Message,
            "dwa razy",
            "wyjątek o powtórzonym celu nie mówi, na czym polega błąd");
        StringAssert.Contains(
            Assert.ThrowsException<ArgumentException>(() => Session(),
                "sesja bez ani jednego celu została zbudowana — nie ma jak się skończyć").Message,
            "bez ani jednego celu",
            "wyjątek o pustej liście celów nie mówi, na czym polega błąd");
    }

    [TestMethod]
    public void TheResultLineIsCompleteAndCultureInvariant()
    {
        // Ta linia jest wspólnym językiem bramki scena–rdzeń: porównanie przez `==`
        // rekordu poszłoby po REFERENCJI listy celów i powiedziałoby „różne" o wynikach
        // identycznych.
        var service = Service();
        var session = Session("s1");
        ObsluzPostoj(service, session, 499.0, 0);

        var linia = session.Result!.Value.ToString();
        StringAssert.Contains(linia, "zaliczone",
            "linia wyniku nie mówi, czy sesja jest zaliczona");
        StringAssert.Contains(linia, "1/1 celów",
            "linia wyniku nie niesie liczby obsłużonych celów");
        StringAssert.Contains(linia, "s1 obsłużony",
            "linia wyniku nie wymienia celu po identyfikatorze");
        StringAssert.Contains(linia, "-1.000 m", "błąd zatrzymania nie wszedł do linii wyniku");
        StringAssert.Contains(linia, "ATP 0/0/0",
            "linia wyniku nie niesie liczników ochrony — przejazd bez ochrony wygląda tak samo jak z nią");
    }

    [TestMethod]
    public void DOORS_OPEN_AND_NaN_DEPARTURE_ARE_THE_SAME_FACT_READ_TWICE()
    {
        // **Ta asercja wyszła z ZIELONEJ kontroli negatywnej, a nie z lektury.**
        // KN-1 podstawiła `!= double.NaN` (wyrażenie ZAWSZE prawdziwe) i zestaw został
        // zielony; KN-1b zdjęła warunek `IsFinite` całkiem — też zielony; KN-1c zdjęła
        // strażnik `AtStation` i zostawiła `IsFinite` — również zielony. Zmierzone
        // znaczy: oba warunki opisują TEN SAM fakt, a każdy z osobna wystarcza.
        //
        // Redundancja zostaje — bo kontrakt M1 mówi o „drzwiach zamkniętych i składzie
        // stojącym", a `AtStation` jest dosłownie pierwszą połową tego zdania — ale
        // przestaje być martwa: ten test sprawdza, że te dwa odczyty ZGADZAJĄ SIĘ
        // w każdym kroku postoju. Gdyby `StationService` kiedyś rozdzielił te dwa
        // stany, jeden z warunków stałby się nośny i dowiedziałbym się o tym tutaj,
        // a nie z zachowania gry.
        var service = Service(exchangeSeconds: 4.0);
        long steps = 0;
        var sprawdzonych = 0;

        for (var i = 0; i < 4000; i++)
        {
            var state = Stopped(500.0, steps);
            service.Filter(state, DriverCommand.Coast, 500.0);
            steps++;

            if (service.Calls.Count > 0)
            {
                var domkniete = double.IsFinite(service.Calls[^1].DepartureSeconds);
                Assert.AreEqual(!service.AtStation, domkniete,
                    $"w kroku {steps} `AtStation` mówi {service.AtStation}, a wpis "
                    + "wywołania mówi co innego — dwa warunki `Observe` przestały "
                    + "opisywać ten sam fakt i jeden z nich stał się nośny");
                sprawdzonych++;
            }

            if (!service.AtStation && service.Calls.Count > 0)
            {
                break;
            }
        }

        Assert.IsTrue(sprawdzonych > 1400,
            $"sprawdzono tylko {sprawdzonych} kroków postoju — przy wymianie 4,0 s "
            + "cykl ma ich ponad 1400, więc pętla urwała się za wcześnie i nic nie mierzy");
    }

    [TestMethod]
    public void RESET_W_TRAKCIE_TRWAJACEJ_INGERENCJI_LICZY_NASTEPNA_OD_NOWA()
    {
        // **Ta asercja też wyszła z ZIELONEJ kontroli.** KN-3 zdjęła zerowanie pamięci
        // zboczy w `Reset()` i zestaw został zielony — bo poprzedni test resetował
        // sesję DOPIERO po postoju, a postój obserwowany jest bez decyzji ochrony
        // (`null`), co samo gasi predykat. Pamięć zbocza była więc czyszczona przez
        // przebieg testu, a nie przez `Reset`.
        //
        // Tutaj reset pada, gdy ochrona NADAL hamuje — czyli dokładnie wtedy, kiedy
        // gracz naciska `R` w środku interwencji. Bez zerowania pamięci następna
        // ingerencja nie policzyłaby się wcale.
        var service = Service();
        var session = Session("s1");
        var hamuje = Decyzja(ProtectionAction.ServiceIntervention, overspeed: true);

        session.Observe(service, Moving(100.0, 20.0, 0), hamuje);

        service.Reset();
        session.Reset();

        session.Observe(service, Moving(100.0, 20.0, 0), hamuje);
        ObsluzPostoj(service, session, 500.0, 1);

        Assert.AreEqual(1L, session.Result!.Value.AtpInterventionEvents,
            "pierwsza ingerencja po resecie nie policzyła się — pamięć zbocza "
            + "przeżyła reset, a reset padł w środku trwającej ingerencji");
        Assert.AreEqual(1L, session.Result!.Value.AtpWarningEvents,
            "to samo dla ostrzeżenia: pamięć przekroczenia przeżyła reset");
    }

    [TestMethod]
    public void WYNIK_NIE_ROSNIE_O_CZAS_SPEDZONY_NA_PANELU_WYNIKU()
    {
        // **Trzecia asercja z zielonej kontroli.** KN-4 zdjęła zatrzask i zestaw został
        // zielony, bo poprzedni test obserwował po zakończeniu skład W RUCHU — a wtedy
        // `Observe` wychodzi na strażniku prędkości, zanim dojdzie do przeliczenia.
        // Zmierzone znaczy: tamten test nie ćwiczył zatrzasku ani razu.
        //
        // Tutaj skład STOI na peronie ostatniego celu, czyli jest dokładnie tam, gdzie
        // zostawia go koniec sesji, a gracz czyta panel. Bez zatrzasku `TotalSeconds`
        // rosłoby o każdą klatkę patrzenia na wynik.
        var service = Service();
        var session = Session("s1");
        var steps = ObsluzPostoj(service, session, 500.0, 0);
        var pierwszy = session.Result!.Value.ToString();
        var czasPierwszy = session.Result!.Value.TotalSeconds;

        for (var i = 0; i < 600; i++)
        {
            session.Observe(service, Stopped(500.0, steps + i),
                Decyzja(ProtectionAction.EmergencyIntervention, overspeed: true));
        }

        Assert.AreEqual(pierwszy, session.Result!.Value.ToString(),
            "wynik przeliczył się przy składzie STOJĄCYM po końcu sesji — czas "
            + "i liczniki rosłyby o czas spędzony na ekranie wyniku");
        Assert.AreEqual(czasPierwszy, session.Result!.Value.TotalSeconds, 1e-12,
            "czas wyniku urósł po zakończeniu sesji");
    }

    [TestMethod]
    public void RunRestartCLEARSTheSessionSoBothSidesOfTheGateResetTheSameThing()
    {
        // Reset jest wpisem w zapisie wejść (decyzja W1), a zapis odtwarzają DWIE
        // strony bramki: scena i `Sim.Runner replay`. Gdyby sesję zerowała tylko scena,
        // runner odtwarzałby ten sam zapis z wynikiem z poprzedniego przejazdu — i obie
        // strony zgodziłyby się co do bitu na telemetrii, różniąc się wynikiem sesji.
        // Dlatego `session?.Reset()` stoi w `RunRestart`, obok `stations?.Reset()`.
        var service = Service();
        var session = Session("s1");
        ObsluzPostoj(service, session, 500.0, 0);
        Assert.IsTrue(session.Finished,
            "sesja nie skończyła się przed resetem — test mierzy co innego");

        var notch = new DriverNotch(1.0);
        RunRestart.Apply(notch, service, cab: null, telemetry: null, session: session);

        Assert.IsFalse(session.Finished,
            "`RunRestart.Apply` nie zresetował sesji — scena i `Sim.Runner replay` "
            + "zerują wtedy RÓŻNE rzeczy, a bramka przy progu 0 tego nie zobaczy");
        Assert.AreEqual(0, service.Calls.Count,
            "kontrola przyrządu: ten sam reset ma zerować też obsługę stacji");
    }

    [TestMethod]
    public void RunRestartWITHOUTASessionStillWorksBecauseNotEveryRunHasOne()
    {
        // Brak sesji jest poprawnym stanem, a nie błędem — tak samo jak brak obsługi
        // stacji i brak ochrony kabiny. Przebieg skryptowy, liniowy i z telemetrii
        // sesji nie mają.
        var notch = new DriverNotch(1.0);
        var start = RunRestart.Apply(notch, stations: null, cab: null, telemetry: null);

        Assert.AreEqual(0L, start.Drive.Steps,
            "reset bez sesji nie zwrócił stanu początkowego");
    }

    private static ProtectionDecision Decyzja(
        ProtectionAction action, bool overspeed = false) => new(
            20.0, 500.0, action, action == ProtectionAction.None ? 0.0 : 1.0,
            overspeed, "test");
}
