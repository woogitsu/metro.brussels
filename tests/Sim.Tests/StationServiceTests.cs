using System;
using System.Collections.Generic;
using System.Linq;
using MetroBxl.Sim.Line;
using MetroBxl.Sim.Physics;
using MetroBxl.Sim.Train;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace MetroBxl.Sim.Tests;

/// <summary>
/// Obsługa stacji dla składu prowadzonego RĘCZNIE — to, czego scenie Godota brakowało,
/// żeby przejazd w ogóle zatrzymywał się na stacjach (T-400, „scena go jeszcze nie woła").
///
/// <para>Testy pilnują trzech rzeczy, których autopilot <see cref="LineDrive"/> nie
/// musiał pilnować, bo staje z błędem 0,31 m i nigdy nie wychodzi poza peron:
/// <b>dwustronności okna</b>, <b>nieodwracalności minięcia</b> i <b>blokady trakcji</b>
/// niezależnej od tego, co naciska gracz.</para>
///
/// <para>Czego tu NIE ma: fizyki. Ta klasa nie liczy ani jednej siły — testy podają
/// stan wprost, żeby wynik nie zależał od hamowania. Zgodność z fizyką sprawdza
/// <see cref="LineDriveTests"/> na autopilocie.</para>
/// </summary>
[TestClass]
public sealed class StationServiceTests
{
    private static readonly FixedStep Step = FixedStep.Simulation;

    private static List<AxisStation> Stations() => new()
    {
        new AxisStation("Start", 0.0, "s0"),
        new AxisStation("Pierwsza", 500.0, "s1"),
        new AxisStation("Druga", 1200.0, "s2"),
    };

    private static StationService Service(double windowM = 5.0, double exchangeSeconds = 0.0)
        => new(Stations(), new DoorCycle(exchangeSeconds), Step, windowM);

    private static DriveState Stopped(double distanceM, long steps = 0)
        => new(steps, 0.0, distanceM, 0.0);

    private static DriveState Moving(double distanceM, double speedMps, long steps = 0)
        => new(steps, speedMps, distanceM, 0.0);

    [TestMethod]
    public void FirstStationIsTheStartingPointAndNotACall()
    {
        // Skład stoi na pierwszej stacji na początku przebiegu. Gdyby to liczyło się
        // jako wywołanie, każdy przejazd zaczynałby się od cyklu drzwi w miejscu,
        // z którego gracz właśnie chce odjechać. `LineDrive` zaczyna od `_next = 1`
        // z tego samego powodu i ta klasa musi być z nim zgodna.
        var service = Service();
        var held = service.Filter(Stopped(0.0), DriverCommand.FullPower, 0.0);

        Assert.IsFalse(service.AtStation);
        Assert.AreEqual(0, service.Calls.Count);
        Assert.AreEqual(1.0, held.Throttle, 1e-12, "nastawnik został zablokowany na starcie");
        Assert.AreEqual("Pierwsza", service.Approach(0.0).Name);
    }

    [TestMethod]
    public void StoppingInsideTheWindowOpensTheDoorsAndBlocksTraction()
    {
        var service = Service(windowM: 5.0);
        var held = service.Filter(Stopped(498.0), DriverCommand.FullPower, 498.0);

        Assert.IsTrue(service.AtStation);
        Assert.AreEqual(1, service.Calls.Count);
        Assert.AreEqual("Pierwsza", service.Calls[0].Name);
        Assert.AreEqual(-2.0, service.Calls[0].StopErrorM, 1e-9, "błąd zatrzymania jest MIERZONY");
        Assert.AreEqual(DoorPhase.Unlocking, service.Phase);
        Assert.IsFalse(service.TractionAllowed);
        Assert.AreEqual(0.0, held.Throttle, 1e-12, "trakcja nie została zablokowana");
    }

    [TestMethod]
    public void BrakeIsNeverTouchedByTheFilter()
    {
        // Ta sama umowa co `StationStop.Filter`: hamulec należy do wołającego, bo
        // skład ma STAĆ przy otwartych drzwiach, a nie toczyć się.
        var service = Service();
        var held = service.Filter(
            Stopped(500.0), new DriverCommand(0.7, 0.4), 500.0);

        Assert.AreEqual(0.0, held.Throttle, 1e-12);
        Assert.AreEqual(0.4, held.Brake, 1e-12, "filtr ruszył hamulec");
    }

    [TestMethod]
    public void WindowIsTwoSidedUnlikeTheAutopilot()
    {
        // `LineDrive` wymaga tylko `chainage >= cel - okno`, bez ograniczenia z góry.
        // Dla gracza ten warunek otworzyłby drzwi w tunelu 200 m za peronem.
        var service = Service(windowM: 5.0);
        var held = service.Filter(Stopped(700.0), DriverCommand.FullPower, 700.0);

        Assert.IsFalse(service.AtStation, "drzwi otwarły się 200 m za stacją");
        Assert.AreEqual(0, service.Calls.Count);
        Assert.AreEqual(1.0, held.Throttle, 1e-12);

        // Kontrola po drugiej stronie: 200 m PRZED stacją też nie jest stacją.
        var przed = Service(windowM: 5.0);
        przed.Filter(Stopped(300.0), DriverCommand.Coast, 300.0);
        Assert.IsFalse(przed.AtStation, "drzwi otwarły się 200 m przed stacją");
        Assert.AreEqual(0, przed.Missed.Count, "stacja przed składem została uznana za miniętą");
    }

    [TestMethod]
    public void DoorsOpenOnSTOPPING_NotOnARRIVING()
    {
        // Znalezione KONTROLĄ NEGATYWNĄ, nie lekturą: mutacja `SpeedMps <= 0.0`
        // -> `<= 1.0` przeżyła pierwszą wersję tego zestawu, bo żaden test nie podawał
        // składu W RUCHU w oknie stacji. Testy sprawdzały „drzwi otwierają się, gdy
        // stoję na peronie" i „nie otwierają się 200 m dalej", a nie sprawdzały wcale
        // rzeczy, która jest treścią reguły z `StationStop`: „zatrzymanie liczy się od
        // PRĘDKOŚCI ZERO, nie od kilometrażu peronu".
        //
        // Skład toczący się przez peron z 1 m/s ma drzwi ZAMKNIĘTE.
        var wRuchu = Service(windowM: 5.0);
        var held = wRuchu.Filter(Moving(500.0, 1.0), DriverCommand.FullPower, 500.0);

        Assert.IsFalse(wRuchu.AtStation, "drzwi otwarły się przy 1,0 m/s");
        Assert.AreEqual(0, wRuchu.Calls.Count);
        Assert.AreEqual(0, wRuchu.Missed.Count, "stacja w oknie została uznana za miniętą");
        Assert.AreEqual(1.0, held.Throttle, 1e-12, "trakcja zablokowana bez postoju");

        // Granica jest przy ZERZE i jest przybita z obu stron. Najmniejsza dodatnia
        // prędkość, jaką da się zapisać, już nie otwiera drzwi.
        var ledwoJedzie = Service(windowM: 5.0);
        ledwoJedzie.Filter(Moving(500.0, double.Epsilon), DriverCommand.Coast, 500.0);
        Assert.IsFalse(ledwoJedzie.AtStation, $"drzwi otwarły się przy {double.Epsilon} m/s");

        var stoi = Service(windowM: 5.0);
        stoi.Filter(Moving(500.0, 0.0), DriverCommand.Coast, 500.0);
        Assert.IsTrue(stoi.AtStation, "drzwi nie otwarły się przy zerowej prędkości");
    }

    [TestMethod]
    public void WindowEdgeBelongsToTheStation()
    {
        // Granica należy do stacji — decyzja jawna, obie strony osobno.
        var naGranicy = Service(windowM: 5.0);
        naGranicy.Filter(Stopped(505.0), DriverCommand.Coast, 505.0);
        Assert.IsTrue(naGranicy.AtStation, "zatrzymanie DOKŁADNIE na cel+okno nie weszło");
        Assert.AreEqual(5.0, naGranicy.Calls[0].StopErrorM, 1e-9);

        var milimetrDalej = Service(windowM: 5.0);
        milimetrDalej.Filter(Stopped(505.001), DriverCommand.Coast, 505.001);
        Assert.IsFalse(milimetrDalej.AtStation, "milimetr za oknem nadal otworzył drzwi");
        Assert.AreEqual(1, milimetrDalej.Missed.Count);

        // I ta sama granica po stronie dojazdu.
        var przedGranica = Service(windowM: 5.0);
        przedGranica.Filter(Stopped(495.0), DriverCommand.Coast, 495.0);
        Assert.IsTrue(przedGranica.AtStation, "zatrzymanie DOKŁADNIE na cel-okno nie weszło");
    }

    [TestMethod]
    public void PassingTheWindowMissesTheStationForGood()
    {
        // Nie ma biegu wstecznego: `DriverCommand` to nastawnik i hamulec, bez kierunku.
        // Więc minięcie musi być monotoniczne, inaczej wynik zależałby od tego, co
        // gracz zrobi potem.
        var service = Service(windowM: 5.0);
        service.Filter(Moving(520.0, 10.0), DriverCommand.Coast, 520.0);

        Assert.AreEqual(1, service.Missed.Count);
        Assert.AreEqual("Pierwsza", service.Missed[0].Name);
        Assert.AreEqual("Druga", service.Approach(520.0).Name, "kolejka nie przeszła dalej");

        // Zatrzymanie się POTEM w oknie minionej stacji już jej nie przywraca.
        service.Filter(Stopped(500.0), DriverCommand.Coast, 500.0);
        Assert.IsFalse(service.AtStation);
        Assert.AreEqual(0, service.Calls.Count);
    }

    /// <summary>
    /// DECYZJA 2 (05.09.2026): minięta stacja to <b>licznik miniętych</b>, a jazda
    /// trwa dalej.
    ///
    /// <para>Nieodwracalność pilnuje <see cref="PassingTheWindowMissesTheStationForGood"/>.
    /// Tu przybite jest to, czego tamten test nie sprawdza, a co jest drugą połową tej
    /// decyzji: <b>polecenie maszynisty wychodzi z filtra NIETKNIĘTE</b>. Gdyby minięcie
    /// dokładało hamulec albo zdejmowało trakcję „za karę", byłaby to inna decyzja niż
    /// ta, którą podjął właściciel — i wyglądałaby w kabinie dokładnie tak samo jak
    /// zadziałanie ochrony pociągu, której w trybie ręcznym nie ma.</para>
    /// </summary>
    [TestMethod]
    public void MissingAStationOnlyCountsItAndLetsTheDriveGoOn()
    {
        var service = Service(windowM: 5.0);
        var pelnyCiag = DriverCommand.FullPower;

        // Krok TUŻ przed granicą okna: stacja jeszcze nie jest minięta.
        var przed = service.Filter(Moving(504.99, 15.0), pelnyCiag, 504.99);
        Assert.AreEqual(pelnyCiag, przed);
        Assert.AreEqual(0, service.Missed.Count);

        // Krok za granicą: minięta, licznik rośnie, polecenie wychodzi to samo.
        var minieta = service.Filter(Moving(505.01, 15.0), pelnyCiag, 505.01);

        Assert.AreEqual(pelnyCiag, minieta, "filtr dołożył coś do polecenia maszynisty");
        Assert.AreEqual(1, service.Missed.Count);
        Assert.AreEqual("Pierwsza", service.Missed[0].Name);
        Assert.AreEqual(0, service.Calls.Count, "minięta stacja nie jest obsłużona");
        Assert.IsFalse(service.AtStation);
        Assert.IsFalse(service.Finished, "jazda trwa dalej — jest jeszcze Druga");
        Assert.IsTrue(service.TractionAllowed, "minięcie nie blokuje trakcji");

        // I dalej: następna stacja obsługuje się normalnie, czyli przejazd nie jest
        // „zepsuty" minięciem — licznik miniętych zostaje, licznik obsłużonych rośnie.
        Assert.AreEqual("Druga", service.Approach(505.01).Name);
        service.Filter(Stopped(1200.0), DriverCommand.Coast, 1200.0);
        Assert.IsTrue(service.AtStation);
        Assert.AreEqual(1, service.Calls.Count);
        Assert.AreEqual(1, service.Missed.Count);
    }

    [TestMethod]
    public void FullCycleReleasesTractionOnlyAfterTheCheck()
    {
        // Cały cykl krok po kroku. To jest test, który odróżnia „drzwi się otwierają"
        // od „blokada jazdy działa": trakcja musi być zwolniona DOPIERO po kontroli
        // zamknięcia, nie w chwili, gdy skrzydła się zetknęły (docs/02-simulation.md).
        var service = Service(windowM: 5.0, exchangeSeconds: 4.0);
        var cycle = service.Cycle;
        Assert.AreEqual(12.5, cycle.DwellSeconds, 1e-12, "8,5 s faz stałych + 4 s wymiany");

        var fazy = new List<DoorPhase>();
        var steps = (long)Math.Round(cycle.DwellSeconds / Step.Seconds) + 2;
        DriverCommand held = DriverCommand.Coast;
        for (var i = 0L; i < steps; i++)
        {
            held = service.Filter(Stopped(500.0, i), DriverCommand.FullPower, 500.0);
            if (fazy.Count == 0 || fazy[^1] != service.Phase)
            {
                fazy.Add(service.Phase);
            }

            if (service.AtStation)
            {
                Assert.AreEqual(0.0, held.Throttle, 1e-12, $"trakcja wolna w fazie {service.Phase}");
            }
        }

        CollectionAssert.AreEqual(
            new[]
            {
                DoorPhase.Unlocking, DoorPhase.Opening, DoorPhase.Open,
                DoorPhase.ClosingWarning, DoorPhase.Closing, DoorPhase.Checking,
                DoorPhase.Closed,
            },
            fazy,
            "kolejność faz cyklu drzwi: " + string.Join(" -> ", fazy));

        Assert.IsFalse(service.AtStation, "postój się nie domknął");
        Assert.AreEqual(1.0, held.Throttle, 1e-12, "trakcja nie została zwolniona po kontroli");
        Assert.IsFalse(double.IsNaN(service.Calls[0].DepartureSeconds), "brak czasu odjazdu");
        Assert.AreEqual("Druga", service.Approach(500.0).Name);
    }

    [TestMethod]
    public void ZeroExchangeStillHoldsTheTrainForTheFixedPhases()
    {
        // Zerowa wymiana pasażerów znaczy „nikt nie wysiada", a nie „drzwi się nie
        // otwierają": 8,5 s cyklu zostaje. To jest własność `DoorCycle`, ale przez
        // tę klasę musi przejść — inaczej scena mogłaby ruszyć natychmiast.
        var service = Service(exchangeSeconds: 0.0);
        Assert.AreEqual(DoorCycle.MinimumDwellSeconds, service.Cycle.DwellSeconds, 1e-12);

        service.Filter(Stopped(500.0, 0), DriverCommand.FullPower, 500.0);
        var polowa = (long)Math.Round(0.5 * DoorCycle.MinimumDwellSeconds / Step.Seconds);
        var held = service.Filter(Stopped(500.0, polowa), DriverCommand.FullPower, 500.0);

        Assert.IsTrue(service.AtStation, "postój zerowej wymiany domknął się natychmiast");
        Assert.AreEqual(0.0, held.Throttle, 1e-12);
    }

    [TestMethod]
    public void ApproachIsTheOnlyPlaceThatKnowsWhereTheNextStationIs()
    {
        // Scena szukała najbliższej stacji własną pętlą w `UpdateHud` — druga kopia
        // tej samej wiedzy. Ten test przypina umowę, którą scena teraz woła.
        var service = Service(windowM: 5.0);

        var daleko = service.Approach(100.0);
        Assert.AreEqual("Pierwsza", daleko.Name);
        Assert.AreEqual(400.0, daleko.DistanceM, 1e-9);
        Assert.IsFalse(daleko.WithinWindow);
        Assert.IsTrue(daleko.Exists);

        var wOknie = service.Approach(497.0);
        Assert.IsTrue(wOknie.WithinWindow);

        // Odległość jest ZE ZNAKIEM: ujemna, gdy punkt zatrzymania jest już za czołem.
        Assert.AreEqual(-3.0, service.Approach(503.0).DistanceM, 1e-9);
    }

    [TestMethod]
    public void RunOutOfStationsStopsFilteringAltogether()
    {
        var service = Service(windowM: 5.0);
        service.Filter(Moving(2000.0, 10.0), DriverCommand.Coast, 2000.0);
        service.Filter(Moving(2001.0, 10.0), DriverCommand.Coast, 2001.0);

        Assert.IsTrue(service.Finished);
        Assert.AreEqual(2, service.Missed.Count);
        Assert.IsFalse(service.Approach(2001.0).Exists);

        var held = service.Filter(Stopped(2001.0), DriverCommand.FullPower, 2001.0);
        Assert.AreEqual(1.0, held.Throttle, 1e-12);
    }

    // --- reset przejazdu (G-4) ----------------------------------------------------

    /// <summary>
    /// Jeden przejazd tą samą sekwencją zatrzymań, przez obsługę podaną z zewnątrz.
    /// Sekwencja jest tu po to, żeby dwa przejazdy dało się porównać co do bitu —
    /// dlatego numer kroku startuje od zera przy każdym wywołaniu, tak samo jak
    /// <see cref="DriveState.Steps"/> po resecie przejazdu.
    /// </summary>
    private static List<StationCall> DriveBothStations(StationService service)
    {
        var step = 0L;
        var dwell = (long)Math.Round(service.Cycle.DwellSeconds / Step.Seconds) + 2;
        foreach (var chainage in new[] { 500.0, 1200.0 })
        {
            // Dojazd: 200 m przed peronem, w ruchu — żeby licznik prędkości szczytowej
            // i odległości od poprzedniej stacji też miały co zbierać.
            for (var i = 0; i < 3; i++)
            {
                service.Filter(Moving(chainage - 200.0, 12.0, step++), DriverCommand.Coast,
                               chainage - 200.0);
            }

            for (var i = 0L; i < dwell; i++)
            {
                service.Filter(Stopped(chainage, step++), DriverCommand.FullPower, chainage);
            }
        }

        return new List<StationCall>(service.Calls);
    }

    /// <summary>
    /// USTERKA G-4: trwający cykl drzwi przeżywał reset przejazdu.
    ///
    /// <para>Scena zerowała stan dynamiczny składu i nie dotykała tej klasy
    /// (<c>reports/droga-do-grywalnosci.md</c> §5.4). Skład wracał na początek osi,
    /// a licznik postoju szedł dalej z poprzedniego przejazdu — z blokadą trakcji,
    /// czyli w tunelu i przy zamkniętych drzwiach.</para>
    /// </summary>
    [TestMethod]
    public void ResetEndsARunningDoorCycle()
    {
        var service = Service(windowM: 5.0, exchangeSeconds: 8.0);
        var half = (long)Math.Round(0.5 * service.Cycle.DwellSeconds / Step.Seconds);
        for (var i = 0L; i <= half; i++)
        {
            service.Filter(Stopped(500.0, i), DriverCommand.FullPower, 500.0);
        }

        // Pomiar PRZED resetem — inaczej „po resecie zero" nie znaczyłoby nic.
        Assert.IsTrue(service.AtStation, "cykl drzwi w ogóle się nie zaczął");
        Assert.IsTrue(service.DwellRemainingSeconds > 0.0,
            $"licznik postoju stał na {service.DwellRemainingSeconds:F3} s jeszcze przed resetem");
        Assert.IsFalse(service.TractionAllowed);
        Assert.AreEqual(1, service.Calls.Count);

        service.Reset();

        Assert.IsFalse(service.AtStation, "trwający cykl drzwi przeżył reset");
        Assert.AreEqual(0.0, service.DwellRemainingSeconds, 0.0,
            "licznik cyklu drzwi nie stoi po resecie na zerze");
        Assert.AreEqual(DoorPhase.Closed, service.Phase);
        Assert.IsTrue(service.TractionAllowed, "trakcja została zablokowana przez poprzedni przejazd");
        Assert.AreEqual(0, service.Calls.Count, "wywołania poprzedniego przejazdu zostały w rejestrze");
        Assert.AreEqual(0, service.Missed.Count);
        Assert.IsFalse(service.Finished);
    }

    /// <summary>
    /// „Przejechana stacja jest przejechana na zawsze" — ale <b>w obrębie przejazdu</b>.
    /// Reset kończy przejazd, więc kolejka wraca na pierwszą stację za punktem startowym;
    /// gdyby nie wracała, skład stałby na 94,0 m z kolejką ustawioną tam, dokąd dojechał,
    /// a <c>_next</c> idzie tylko w przód.
    /// </summary>
    [TestMethod]
    public void ResetBringsBackTheStationsThatWereAlreadyPassed()
    {
        var service = Service(windowM: 5.0);
        service.Filter(Moving(520.0, 10.0), DriverCommand.Coast, 520.0);
        service.Filter(Moving(1300.0, 10.0), DriverCommand.Coast, 1300.0);
        Assert.IsTrue(service.Finished, "przejazd nie minął obu stacji");
        Assert.AreEqual(2, service.Missed.Count);

        service.Reset();

        Assert.IsFalse(service.Finished, "kolejka stacji została na końcu osi");
        Assert.AreEqual(0, service.Missed.Count);
        Assert.AreEqual("Pierwsza", service.Approach(0.0).Name, "kolejka nie wróciła na początek");

        // I stacja minięta w poprzednim przejeździe daje się obsłużyć w nowym.
        service.Filter(Stopped(500.0), DriverCommand.Coast, 500.0);
        Assert.IsTrue(service.AtStation);
        Assert.AreEqual(1, service.Calls.Count);
        Assert.AreEqual("Pierwsza", service.Calls[0].Name);
    }

    /// <summary>
    /// Dowód wprost z kryterium G-4: przejazd po resecie ma tę samą sekwencję wywołań
    /// stacji, co ten sam przejazd na świeżo zbudowanej obsłudze, przy progu <b>0</b>.
    ///
    /// <para>Próg zero jest tu dosłowny: <see cref="StationCall"/> jest rekordem, więc
    /// porównanie idzie po WSZYSTKICH polach — kilometrażu, błędzie zatrzymania, czasach
    /// przyjazdu i odjazdu, drodze od poprzedniej stacji i prędkości szczytowej. Gdyby
    /// reset zostawiał którykolwiek z liczników wewnętrznych (<c>_departedAtSeconds</c>,
    /// <c>_departedFromM</c>, <c>_topSpeedMps</c>), rozjazd wyszedłby właśnie tutaj,
    /// a nie na licznikach, które widać z HUD-u.</para>
    /// </summary>
    [TestMethod]
    public void RunAfterResetIsBitIdenticalWithARunOnAFreshService()
    {
        var wzorzec = DriveBothStations(Service(windowM: 5.0, exchangeSeconds: 8.0));

        var uzywana = Service(windowM: 5.0, exchangeSeconds: 8.0);
        DriveBothStations(uzywana);
        uzywana.Reset();
        var poResecie = DriveBothStations(uzywana);

        Assert.AreEqual(2, wzorzec.Count, "przejazd wzorcowy nie obsłużył obu stacji");
        CollectionAssert.AreEqual(
            wzorzec, poResecie,
            "wywołania po resecie: " + string.Join(" | ", poResecie));
    }

    [TestMethod]
    public void WindowMustBePositiveAndFinite()
    {
        // Okno zero scaliłoby rozpoznanie do jednego punktu zmiennoprzecinkowego,
        // w który zatrzymanie nie trafi nigdy — czyli cicho wyłączyłoby stacje.
        foreach (var zle in new[] { 0.0, -5.0, double.NaN, double.PositiveInfinity })
        {
            Assert.ThrowsException<ArgumentOutOfRangeException>(
                () => new StationService(Stations(), new DoorCycle(0.0), Step, zle),
                $"okno {zle} zostało przyjęte");
        }
    }

    [TestMethod]
    public void RealPackageAxisGivesElevenCallsWhenEveryStopIsMade()
    {
        // Zgodność z rdzeniem na PRAWDZIWEJ osi: `LineRun` na pakiecie A daje
        // 11 zatrzymań (12 stacji minus punkt startowy). Ta klasa musi dawać tyle samo,
        // gdy gracz zatrzyma się na każdej — inaczej kabina liczyłaby stacje inaczej
        // niż linia, której jest widokiem.
        var axis = SignallingPlanTests.PackageAAxis();
        var service = new StationService(axis.Stations, new DoorCycle(0.0), Step, 5.0);
        Assert.AreEqual(12, axis.Stations.Count);

        var step = 0L;
        foreach (var station in axis.Stations.Skip(1))
        {
            // Zatrzymanie w punkcie stacji, potem tyle kroków, ile trwa cykl.
            var dwell = (long)Math.Round(service.Cycle.DwellSeconds / Step.Seconds) + 2;
            for (var i = 0L; i < dwell; i++)
            {
                service.Filter(Stopped(station.ChainageM, step++), DriverCommand.Coast,
                               station.ChainageM);
            }
        }

        Assert.AreEqual(11, service.Calls.Count,
            "wywołania: " + string.Join(", ", service.Calls.Select(c => c.Name)));
        Assert.AreEqual(0, service.Missed.Count);
        Assert.IsTrue(service.Finished);
        foreach (var call in service.Calls)
        {
            Assert.AreEqual(0.0, call.StopErrorM, 1e-9, call.Name);
        }
    }
}
