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
/// Linia jako całość: wiele składów na jednym zegarze, jednej osi i jednym planie
/// sygnalizacji (T-320).
///
/// <para>Testy stoją na dwóch nogach i obie są potrzebne. Pierwsza to <b>tożsamość</b>:
/// jeden skład na pustej linii musi jechać dokładnie tak, jak jechał przed
/// wprowadzeniem sygnalizacji — co do bajtu, krok po kroku. Bez tego każda zmiana
/// w tej klasie po cichu przepisywałaby wszystkie dotychczasowe pomiary czasu jazdy.
/// Druga to <b>sprzężenie</b>: drugi skład ma być zatrzymany przez pierwszy, a nie
/// przez własny rozkład — i to musi być widać jako liczba, nie jako wrażenie.</para>
///
/// <para>Oś jest syntetyczna, ta sama co w <see cref="FixedBlockTests"/>: stacje na
/// 0, 600, 1400 i 2000 m dają bloki <c>P01 [0, 47)</c>, <c>S01 [47, 553)</c>,
/// <c>P02 [553, 647)</c>, <c>S02 [647, 1353)</c>, <c>P03 [1353, 1447)</c>,
/// <c>S03 [1447, 1953)</c>, <c>P04 [1953, 2047)</c> i <c>S04 [2047, 2100)</c>.
/// Granice pakietu A są <c>design_model</c> i przypięcie ich tutaj przypięłoby
/// założenie, a nie zachowanie.</para>
/// </summary>
[TestClass]
public sealed class LineCoreTests
{
    private static readonly double[] Stations = { 0.0, 600.0, 1400.0, 2000.0 };

    private static RunConditions Level() => RunConditions.Level(VehicleModel.M7, TrainLoad.Aw0);

    private static LineRunSettings Settings() => new(Units.KmhToMps(60.0), 10.0, 1.0, 5.0);

    private static LineCore Line(params double[] stationChainages)
    {
        var chainages = stationChainages.Length > 0 ? stationChainages : Stations;
        return LineCore.M7(
            SignallingPlanTests.SyntheticPlan(requireRoute: false, chainages),
            SignallingPlanTests.SyntheticAxis(chainages),
            Level(),
            Settings());
    }

    private static List<LineRun.TracePoint> TraceOf(LineCore line, string trainId, long stepBudget)
    {
        var trace = new List<LineRun.TracePoint>();
        line.Run(stepBudget, (id, point) =>
        {
            if (string.Equals(id, trainId, StringComparison.Ordinal))
            {
                trace.Add(point);
            }
        });

        return trace;
    }

    private static List<LineRun.TracePoint> Solo(params double[] stationChainages)
    {
        var trace = new List<LineRun.TracePoint>();
        LineRun.M7.Run(
            SignallingPlanTests.SyntheticAxis(
                stationChainages.Length > 0 ? stationChainages : Stations),
            Level(), Settings(), LineRun.DefaultStepBudget, trace.Add);
        return trace;
    }

    // --- tożsamość: sygnalizacja bez ruchu niczego nie zmienia ---------------

    [TestMethod]
    public void Jeden_sklad_na_pustej_linii_jedzie_tak_samo_jak_bez_sygnalizacji()
    {
        // To jest ten test. Pusta linia znaczy: autorytet zawsze sięga dalej niż
        // następna stacja, więc cel hamowania ani razu się nie zmienia. Ślad co krok,
        // nie podsumowanie — podsumowanie zgodziłoby się także wtedy, gdyby skład
        // dojechał tam samo, ale inną drogą.
        var line = Line();
        line.Add("A", 0L);
        var withSignalling = TraceOf(line, "A", LineRun.DefaultStepBudget);

        var without = Solo();

        Assert.AreEqual(without.Count, withSignalling.Count, "różna liczba kroków");
        for (var i = 0; i < without.Count; i++)
        {
            Assert.AreEqual(without[i], withSignalling[i], $"rozjazd w kroku {i}");
        }
    }

    [TestMethod]
    public void Skladowi_na_pustej_linii_autorytet_konczy_sie_dopiero_na_koncu_planu()
    {
        // Kontrola do testu wyżej. Gdyby autorytet z jakiegokolwiek powodu skracał się
        // w trakcie samotnego przejazdu, tożsamość mogłaby zachodzić przypadkiem —
        // na przykład dlatego, że skrócenie wypadało zawsze za punktem hamowania.
        var line = Line();
        line.Add("A", 0L);
        var end = line.Signalling.Plan.EndM;

        while (!line.Finished && line.Steps < LineRun.DefaultStepBudget)
        {
            line.Step();
            var authority = line.Trains[0].Authority!.Value;
            Assert.AreEqual(AuthorityLimit.EndOfLine, authority.Reason,
                $"w kroku {line.Steps} autorytet skrócił się z powodu {authority.Reason}");
            Assert.AreEqual(end, authority.EndChainageM, 0.0);
        }

        Assert.IsTrue(line.Finished);
    }

    // --- sprzężenie: drugi skład widzi pierwszy ------------------------------

    [TestMethod]
    public void Drugi_sklad_zatrzymuje_sie_przed_blokiem_zajetym_przez_pierwszy()
    {
        // Sprzężenie, dla którego cała ta klasa istnieje. Pierwszy skład dojeżdża do
        // ostatniej stacji i tam zostaje — model nie zna zawracania. Drugi ma stanąć
        // przed jego blokiem i tam zostać, a powodem ma być zajętość, nie koniec planu.
        var line = Line();
        line.Add("A", 0L);
        line.Add("B", 30L * FixedStep.SimulationHertz);

        var reason = line.Run(20L * 60L * FixedStep.SimulationHertz);

        Assert.AreEqual("step-budget", reason,
            "linia bez zawracania nie ma prawa zameldować, że wszystkie składy dojechały");
        var leader = line.Trains[0];
        var follower = line.Trains[1];

        Assert.IsTrue(leader.Finished, "pierwszy skład nie dojechał");
        Assert.IsFalse(follower.Finished, "drugi skład dojechał przez zajęty peron końcowy");

        var authority = follower.Authority!.Value;
        Assert.AreEqual(AuthorityLimit.OccupiedBlock, authority.Reason,
            $"drugi skład stoi z powodu {authority.Reason}, a nie przez skład przed sobą");
        Assert.AreEqual("A", line.Signalling.OccupantOf(authority.LimitBlockId),
            "blok, który zatrzymał drugi skład, nie jest blokiem pierwszego");
        Assert.IsTrue(follower.Drive!.ChainageM <= authority.EndChainageM,
            $"czoło drugiego składu jest na {follower.Drive!.ChainageM:F3} m, " +
            $"a autorytet kończy się na {authority.EndChainageM:F3} m");
        Assert.AreEqual(0.0, follower.Drive!.State.SpeedMps, 0.0,
            "drugi skład przed zajętym blokiem nadal jedzie");
    }

    [TestMethod]
    public void Zaden_sklad_nie_wjezdza_w_blok_zajety_przez_inny()
    {
        // Kontrola do testu wyżej, mocniejsza od niego: przez cały przejazd w strumieniu
        // zdarzeń nie ma ani jednego naruszenia autorytetu. Test wyżej pilnuje stanu
        // końcowego, ten — całej drogi do niego.
        var line = Line();
        line.Add("A", 0L);
        line.Add("B", 30L * FixedStep.SimulationHertz);
        line.Run(20L * 60L * FixedStep.SimulationHertz);

        var violations = line.Signalling.Events
            .Where(e => e.Kind == SignallingEventKind.AuthorityViolation)
            .ToList();

        Assert.AreEqual(0, violations.Count,
            "naruszenia autorytetu: " + string.Join("; ", violations.Select(v => v.ToString())));
    }

    [TestMethod]
    public void Odstep_wydluza_przejazd_drugiego_skladu_wobec_pustej_linii()
    {
        // Liczba zamiast wrażenia. Drugi skład jedzie tą samą osią z tymi samymi
        // założeniami, więc każda różnica w czasie jazdy między stacjami bierze się
        // wyłącznie z pierwszego składu przed nim.
        var line = Line();
        line.Add("A", 0L);
        line.Add("B", 30L * FixedStep.SimulationHertz);
        line.Run(20L * 60L * FixedStep.SimulationHertz);

        var alone = LineRun.M7.Run(SignallingPlanTests.SyntheticAxis(Stations), Level(), Settings());
        var follower = line.ResultOf("B", "step-budget");

        Assert.IsTrue(follower.Calls.Count >= 2,
            $"drugi skład zaliczył tylko {follower.Calls.Count} zatrzymań");
        var heldRun = follower.Calls[1].RunSecondsFromPrevious;
        var freeRun = alone.Calls[1].RunSecondsFromPrevious;
        Assert.IsTrue(heldRun > freeRun,
            $"drugi skład przejechał odcinek w {heldRun:F2} s, a samotny w {freeRun:F2} s — " +
            "odstęp nie zrobił żadnej różnicy");
    }

    // --- wyjazdy -------------------------------------------------------------

    [TestMethod]
    public void Sklad_nie_wjezdza_na_zajety_peron_poczatkowy_tylko_czeka()
    {
        // Dwa wyjazdy na ten sam krok. Peron początkowy mieści jeden skład, więc drugi
        // wchodzi na plan dopiero wtedy, gdy pierwszy zwolni blok — i to jest brak
        // miejsca, a nie regulacja ruchu.
        var line = Line();
        line.Add("A", 0L);
        line.Add("B", 0L);
        line.Step();

        Assert.IsTrue(line.Trains[0].OnLine, "pierwszy skład nie wszedł na plan");
        Assert.IsFalse(line.Trains[1].OnLine, "dwa składy weszły na ten sam peron");

        line.Run(20L * 60L * FixedStep.SimulationHertz);

        Assert.IsTrue(line.Trains[1].OnLine, "drugi skład nigdy nie wyjechał");
        Assert.IsTrue(line.Trains[1].EnteredAtStep > 0L,
            $"drugi skład wszedł na kroku {line.Trains[1].EnteredAtStep}, czyli od razu");
    }

    [TestMethod]
    public void Sklad_ktory_nie_wyjechal_nie_ma_wyniku_przejazdu()
    {
        // Wynik zerowy dla składu, którego nie było, byłby nie do odróżnienia od
        // przejazdu, który się nie udał.
        var line = Line();
        line.Add("A", 10L * FixedStep.SimulationHertz);

        Assert.ThrowsException<InvalidOperationException>(() => line.ResultOf("A", "arrived"));
    }

    // --- niezależność od kolejności -----------------------------------------

    [TestMethod]
    public void Wynik_nie_zalezy_od_kolejnosci_zgloszenia_skladow()
    {
        // Kanarek na fazowanie kroku. Autorytety są czytane ze stanu SPRZED kroku, więc
        // dopóki składy respektują autorytet, kolejność meldowania ruchu jest bez znaczenia
        // i oba przejazdy muszą wyjść identyczne. Gdyby odczyt przesunął się za ruch — albo
        // gdyby któryś skład przekroczył autorytet — ten test zaczyna padać.
        const long Budget = 20L * 60L * FixedStep.SimulationHertz;
        var forward = Line();
        forward.Add("A", 0L);
        forward.Add("B", 30L * FixedStep.SimulationHertz);
        var forwardA = new List<LineRun.TracePoint>();
        var forwardB = new List<LineRun.TracePoint>();
        forward.Run(Budget, (id, p) => (id == "A" ? forwardA : forwardB).Add(p));

        var reversed = Line();
        reversed.Add("B", 30L * FixedStep.SimulationHertz);
        reversed.Add("A", 0L);
        var reversedA = new List<LineRun.TracePoint>();
        var reversedB = new List<LineRun.TracePoint>();
        reversed.Run(Budget, (id, p) => (id == "A" ? reversedA : reversedB).Add(p));

        CollectionAssert.AreEqual(forwardA, reversedA, "skład A pojechał inaczej po zamianie kolejności");
        CollectionAssert.AreEqual(forwardB, reversedB, "skład B pojechał inaczej po zamianie kolejności");
    }

    [TestMethod]
    public void Dwa_przebiegi_tego_samego_scenariusza_daja_ten_sam_odcisk_stanu()
    {
        const long Budget = 20L * 60L * FixedStep.SimulationHertz;

        string Digest()
        {
            var line = Line();
            line.Add("A", 0L);
            line.Add("B", 30L * FixedStep.SimulationHertz);
            line.Run(Budget);
            return line.Signalling.StateDigest();
        }

        Assert.AreEqual(Digest(), Digest(),
            "dwa przebiegi tego samego scenariusza rozeszły się w stanie ryglowania");
    }

    // --- zegar ---------------------------------------------------------------

    [TestMethod]
    public void Czas_linii_jest_funkcja_liczby_krokow()
    {
        var line = Line();
        line.Add("A", 0L);
        for (var i = 0; i < 1000; i++)
        {
            line.Step();
        }

        Assert.AreEqual(1000L, line.Steps);
        Assert.AreEqual(1000.0 / FixedStep.SimulationHertz, line.TimeSeconds, 0.0);
    }

    [TestMethod]
    public void Linia_bez_skladow_nigdy_nie_jest_skonczona()
    {
        // Inaczej „wszystkie składy dojechały" byłoby prawdą dla pustej linii i pętla
        // wołającego kończyłaby się natychmiast, nie zrobiwszy nic.
        var line = Line();
        Assert.IsFalse(line.Finished);
        Assert.AreEqual("step-budget", line.Run(10L));
        Assert.AreEqual(10L, line.Steps);
    }

    // --- PRAWDZIWY plan: RequireRoute = true ---------------------------------
    //
    // Do 04.09.2026 KAŻDY test tej klasy budował plan przez
    // `SyntheticPlan(requireRoute: false, ...)`. Cały rdzeń wielu składów był więc
    // sprawdzony na konfiguracji, której prawdziwy plan projektu NIE UŻYWA:
    // `data/design/signalling/classic-2026.json` ma `RequireRoute = true`. Zmierzone
    // na tym planie przed wprowadzeniem nastawni: skład dojeżdżał do 46,7 m i stawał,
    // autorytet 47,00 m, powód `BlockNotReserved`. Zielony zestaw testów nie zauważał,
    // że linia nie rusza — bo pytał o inny plan.

    private static LineCore RealLine() => LineCore.M7(
        SignallingPlanTests.PackageAPlan(),
        SignallingPlanTests.PackageAAxis(),
        new RunConditions(
            VehicleModel.M7.MassKg(TrainLoad.Aw2), 0.0,
            VehicleModel.M7.Adhesion(RailCondition.Dry), TrackEnvironment.Tunnel),
        RealSettings());

    private static LineRunSettings RealSettings() =>
        new(Units.KmhToMps(70.0), 8.0, 1.0, 5.0);

    [TestMethod]
    public void Na_prawdziwym_planie_wymagajacym_tras_linia_przejezdza_cala_os()
    {
        var line = RealLine();
        line.Add("A", 0L);
        while (!line.Finished && line.Steps < LineRun.DefaultStepBudget)
        {
            line.Step();
        }

        var result = line.Trains[0].Drive!.Result(line.Finished ? "arrived" : "step-budget");

        Assert.AreEqual("arrived", result.FinishReason,
            $"linia nie dojechała: {line.Dispatcher}, chainage {line.Trains[0].Drive!.ChainageM:F2} m");
        Assert.AreEqual(11, result.Calls.Count, "pakiet A ma 12 stacji, czyli 11 wywołań");
        Assert.AreEqual(11, line.Dispatcher.Locked, "jedna trasa na odcinek międzystacyjny");
        Assert.AreEqual(0, line.Dispatcher.Refused,
            "samotny skład na pustej linii nie ma prawa dostać ani jednej odmowy");
    }

    [TestMethod]
    public void Na_prawdziwym_planie_samotny_sklad_jedzie_tak_samo_jak_bez_sygnalizacji()
    {
        // Ta sama zasada, co w teście tożsamości na osi syntetycznej, ale na planie,
        // który tras WYMAGA: nastawnia nie ma prawa zmienić przejazdu samotnego składu.
        // Gdyby zmieniała, znaczyłoby to, że ryglowanie tras dokłada opóźnienie —
        // a wtedy każdy zmierzony czas jazdy w tym repozytorium byłby do przeliczenia.
        var line = RealLine();
        line.Add("A", 0L);
        var withSignalling = new List<LineRun.TracePoint>();
        line.Run(LineRun.DefaultStepBudget, (id, point) =>
        {
            if (string.Equals(id, "A", StringComparison.Ordinal))
            {
                withSignalling.Add(point);
            }
        });

        var without = new List<LineRun.TracePoint>();
        LineRun.M7.Run(
            SignallingPlanTests.PackageAAxis(),
            new RunConditions(
                VehicleModel.M7.MassKg(TrainLoad.Aw2), 0.0,
                VehicleModel.M7.Adhesion(RailCondition.Dry), TrackEnvironment.Tunnel),
            RealSettings(), LineRun.DefaultStepBudget, without.Add);

        Assert.AreEqual(without.Count, withSignalling.Count, "różna liczba kroków");
        for (var i = 0; i < without.Count; i++)
        {
            Assert.AreEqual(without[i], withSignalling[i], $"rozjazd w kroku {i}");
        }
    }

    [TestMethod]
    public void Na_prawdziwym_planie_dwa_sklady_nigdy_nie_stoja_w_jednym_bloku()
    {
        // Sprzężenie na planie, który tras wymaga. Odmowy są tu NORMALNĄ odpowiedzią,
        // nie usterką: drugi skład pyta o trasę, której pierwszy jeszcze nie zwolnił.
        // Zmierzone: pierwsza odmowa w kroku 4399, najmniejszy odstęp czół 462,70 m.
        var line = RealLine();
        line.Add("A", 0L);
        line.Add("B", 30L * FixedStep.SimulationHertz);

        var minSpacing = double.MaxValue;
        var shared = 0;
        for (var i = 0L; i < 60_000L; i++)
        {
            line.Step();
            if (line.Trains[0].Drive is null || line.Trains[1].Drive is null)
            {
                continue;
            }

            var spacing = line.Trains[0].Drive!.ChainageM - line.Trains[1].Drive!.ChainageM;
            if (spacing > 0.0 && spacing < minSpacing)
            {
                minSpacing = spacing;
            }

            var byA = line.Signalling.BlocksOccupiedBy("A");
            foreach (var block in line.Signalling.BlocksOccupiedBy("B"))
            {
                if (byA.Contains(block))
                {
                    shared++;
                }
            }
        }

        Assert.AreEqual(0, shared, "dwa składy zajęły ten sam blok");
        Assert.IsTrue(line.Dispatcher.Refused > 0,
            $"sygnalizacja ani razu nie odmówiła — sprzężenia nie ma: {line.Dispatcher}");
        Assert.IsTrue(minSpacing > 94.0,
            $"odstęp czół {minSpacing:F2} m nie przekracza długości składu");
    }

    [TestMethod]
    public void Na_prawdziwym_planie_drugi_sklad_nie_dojedzie_do_konca_bez_turnbacku()
    {
        // To NIE jest test naprawy, to test PRZYPINAJĄCY znaną dziurę. Pierwszy skład
        // kończy przejazd na ostatnim peronie i **nigdy z niego nie odjeżdża**, bo
        // turnbacku w modelu nie ma (T-320, punkt „Zostaje": „bez turnbacku nie da się
        // ..."). Ostatni blok peronowy zostaje więc zajęty na zawsze i drugi skład nie
        // ma jak zaryglować ostatniej trasy.
        //
        // Zmierzone przy budżecie 200 000 kroków: A robi 11 zatrzymań i staje na
        // 6686,05 m, B robi 10 i staje na 5514,04 m, czyli za Schumanem. Dzień, w którym
        // turnback wejdzie, ten test ZAUWAŻY — i wtedy trzeba go przepisać, a nie usunąć.
        var line = RealLine();
        line.Add("A", 0L);
        line.Add("B", 30L * FixedStep.SimulationHertz);
        for (var i = 0L; i < 200_000L; i++)
        {
            line.Step();
        }

        var a = line.Trains[0].Drive!.Result("x");
        var b = line.Trains[1].Drive!.Result("x");

        Assert.AreEqual(11, a.Calls.Count, "pierwszy skład ma przejechać całą oś");
        Assert.AreEqual(10, b.Calls.Count,
            $"drugi skład zrobił {b.Calls.Count} zatrzymań — jeżeli 11, turnback wszedł "
            + "i ten test trzeba przepisać");
        Assert.IsFalse(line.Finished, "linia nie ma prawa być skończona, dopóki B stoi");

        var terminus = line.Signalling.Plan.Blocks[^1];
        var lastPlatform = line.Signalling.Plan.Blocks
            .Where(block => block.IsPlatform).Last();
        Assert.AreEqual("A", line.Signalling.OccupantOf(lastPlatform.Id),
            $"ostatni peron {lastPlatform.Id} nie jest zajęty przez A, więc blokada ma inny powód");
        Assert.IsTrue(terminus.EndM > 0.0);
    }

    // --- turnback ------------------------------------------------------------
    //
    // Decyzja właściciela z 04.09.2026: nawrót na oba końce osi. Czas nawrotu ma
    // ŹRÓDŁO — zmierzony z feedu GTFS STIB przez połączenie kursów po `block_id` na
    // liniach 1 i 5: 194 obiegi, 4289 nawrotów, minimum 240 s, mediana 445 s, maksimum
    // 1005 s, ani jednego poniżej 240 s. Szczegóły i zastrzeżenia: `docs/21`.

    private static LineCore RealLineWithTurnback(double seconds) => LineCore.M7(
        SignallingPlanTests.PackageAPlan(),
        SignallingPlanTests.PackageAAxis(),
        new RunConditions(
            VehicleModel.M7.MassKg(TrainLoad.Aw2), 0.0,
            VehicleModel.M7.Adhesion(RailCondition.Dry), TrackEnvironment.Tunnel),
        RealSettings(),
        seconds);

    [TestMethod]
    public void Turnback_jest_domyslnie_wylaczony_i_linia_zachowuje_sie_jak_dotad()
    {
        // Turnback musi być opt-in, bo z nim linia NIGDY nie jest skończona — pojazdy
        // krążą. Gdyby był domyślny, każdy dotychczasowy test kończący się na
        // `Finished` przestałby się kończyć, a to nie jest zmiana, którą wolno wprowadzić
        // po cichu.
        var bez = RealLine();
        Assert.IsFalse(bez.TurnbackEnabled);
        Assert.AreEqual(0L, bez.TurnbackSteps);

        bez.Add("A", 0L);
        while (!bez.Finished && bez.Steps < LineRun.DefaultStepBudget)
        {
            bez.Step();
        }

        Assert.IsTrue(bez.Finished, "bez turnbacku linia ma się kończyć");
        Assert.AreEqual(0, bez.Trains[0].CompletedRuns.Count,
            "bez turnbacku nie ma obiegów zakończonych — pojazd stoi na ostatnim peronie");
    }

    [TestMethod]
    public void Turnback_zwalnia_ostatni_peron_i_drugi_sklad_dojezdza_do_konca()
    {
        // TO JEST TEN TEST. Bez turnbacku drugi skład stawał na 5514,04 m, za Schumanem,
        // bo pierwszy trzymał Merode na zawsze — a dwie kolejne trasy dzielą blok
        // peronowy. Test `..._drugi_sklad_nie_dojedzie_do_konca_bez_turnbacku` przypina
        // tamten stan; ten pokazuje, że z nawrotem blokady nie ma.
        var line = RealLineWithTurnback(240.0);
        Assert.IsTrue(line.TurnbackEnabled);
        Assert.AreEqual(240L * FixedStep.SimulationHertz, line.TurnbackSteps);

        line.Add("A", 0L);
        line.Add("B", 30L * FixedStep.SimulationHertz);
        for (var i = 0L; i < 300_000L; i++)
        {
            line.Step();
        }

        Assert.IsFalse(line.Finished, "z turnbackiem linia nie ma prawa się skończyć");
        foreach (var train in line.Trains)
        {
            Assert.IsTrue(train.CompletedRuns.Count >= 2,
                $"{train.Id}: {train.CompletedRuns.Count} obiegów, oczekiwano co najmniej dwóch");
            foreach (var run in train.CompletedRuns)
            {
                Assert.AreEqual(11, run.Calls.Count,
                    $"{train.Id}: obieg z {run.Calls.Count} zatrzymaniami zamiast 11");
                Assert.AreEqual("turnback", run.FinishReason);
            }
        }

        // Sprzężenie widać w LICZBIE, nie we wrażeniu: pierwszy obieg drugiego składu
        // jest dłuższy, bo sygnalizacja go trzyma; kolejne wchodzą w rytm.
        var pierwszyB = line.Trains[1].CompletedRuns[0].TotalSeconds;
        var drugiB = line.Trains[1].CompletedRuns[1].TotalSeconds;
        Assert.IsTrue(pierwszyB > drugiB + 100.0,
            $"pierwszy obieg B {pierwszyB:F2} s nie jest wyraźnie dłuższy od drugiego {drugiB:F2} s "
            + "— sprzężenia przez sygnalizację nie ma");
    }

    [TestMethod]
    public void Turnback_nie_wypuszcza_pojazdu_wczesniej_niz_po_zmierzonym_czasie()
    {
        // Czas nawrotu ma być czasem, nie ozdobą. Bez tego testu turnback mógłby
        // wypisywać pojazd natychmiast po dojechaniu i różnicy nikt by nie zauważył,
        // bo przejazd i tak by się zamykał.
        var line = RealLineWithTurnback(240.0);
        line.Add("A", 0L);

        long dojechalW = -1L, wrocilW = -1L;
        for (var i = 0L; i < 150_000L && wrocilW < 0L; i++)
        {
            line.Step();
            var train = line.Trains[0];
            if (dojechalW < 0L && train.Drive is { Finished: true })
            {
                dojechalW = line.Steps;
            }
            else if (dojechalW > 0L && train.CompletedRuns.Count == 1 && train.OnLine)
            {
                wrocilW = line.Steps;
            }
        }

        Assert.IsTrue(dojechalW > 0L, "pojazd nie dojechał do końca");
        Assert.IsTrue(wrocilW > 0L, "pojazd nie wrócił na plan");
        var przerwa = wrocilW - dojechalW;
        Assert.IsTrue(przerwa >= line.TurnbackSteps,
            $"przerwa {przerwa} kroków jest krótsza niż nawrót {line.TurnbackSteps} kroków");
    }

    [TestMethod]
    public void Turnback_krotszy_niz_krok_jest_ODMOWA_a_nie_cichym_wylaczeniem()
    {
        // Czas nawrotu krótszy niż 1/120 s zaokrągliłby się do zera kroków, czyli
        // po cichu WYŁĄCZYŁBY turnback — a wołający myślałby, że go ustawił.
        // To jest dokładnie ta rodzina usterek, którą to repozytorium zbierało.
        var maly = 0.5 / FixedStep.SimulationHertz;
        var error = Assert.ThrowsException<ArgumentOutOfRangeException>(
            () => RealLineWithTurnback(maly));
        StringAssert.Contains(error.Message, "wyłączyłby turnback");

        foreach (var zly in new[] { -1.0, -240.0, double.NaN, double.PositiveInfinity })
        {
            Assert.ThrowsException<ArgumentOutOfRangeException>(
                () => RealLineWithTurnback(zly), $"czas nawrotu {zly} został przyjęty");
        }

        // Zero jest DOZWOLONE i znaczy „bez turnbacku" — to nie to samo co 0,004 s.
        var zero = RealLineWithTurnback(0.0);
        Assert.IsFalse(zero.TurnbackEnabled);
    }

    // --- odmowy --------------------------------------------------------------

    [TestMethod]
    public void Plan_dla_innej_osi_jest_odrzucany()
    {
        // Bloki i stacje muszą pochodzić z tego samego kilometrażu; inaczej autorytet
        // i cel hamowania są liczone w dwóch różnych układach i nikt tego nie zauważy.
        var error = Assert.ThrowsException<ArgumentException>(() => LineCore.M7(
            SignallingPlanTests.PackageAPlan(),
            SignallingPlanTests.SyntheticAxis(Stations),
            Level(),
            Settings()));
        StringAssert.Contains(error.Message, "muszą pochodzić z tej samej osi");
    }

    [TestMethod]
    public void Wyjazd_w_przeszlosci_jest_odrzucany()
    {
        var line = Line();
        line.Add("A", 0L);
        line.Step();

        Assert.ThrowsException<ArgumentOutOfRangeException>(() => line.Add("B", 0L));
    }

    [TestMethod]
    public void Powtorzony_identyfikator_skladu_jest_odrzucany()
    {
        var line = Line();
        line.Add("A", 0L);

        Assert.ThrowsException<ArgumentException>(() => line.Add("A", 100L));
    }

    [TestMethod]
    public void Nieznany_sklad_nie_ma_wyniku()
    {
        var line = Line();
        line.Add("A", 0L);

        Assert.ThrowsException<ArgumentException>(() => line.ResultOf("Z", "arrived"));
    }

    [TestMethod]
    public void Brakujace_skladniki_sa_odrzucane()
    {
        var plan = SignallingPlanTests.SyntheticPlan(requireRoute: false, Stations);
        var axis = SignallingPlanTests.SyntheticAxis(Stations);
        var controller = new TrainController(VehicleModel.M7);
        var solver = new BrakingPointSolver(VehicleModel.M7);

        Assert.ThrowsException<ArgumentNullException>(() => new LineCore(
            null!, axis, Level(), Settings(), controller, solver, FixedStep.Simulation, 94.0));
        Assert.ThrowsException<ArgumentNullException>(() => new LineCore(
            plan, null!, Level(), Settings(), controller, solver, FixedStep.Simulation, 94.0));
        Assert.ThrowsException<ArgumentNullException>(() => new LineCore(
            plan, axis, null!, Settings(), controller, solver, FixedStep.Simulation, 94.0));
        Assert.ThrowsException<ArgumentNullException>(() => new LineCore(
            plan, axis, Level(), null!, controller, solver, FixedStep.Simulation, 94.0));
        Assert.ThrowsException<ArgumentNullException>(() => new LineCore(
            plan, axis, Level(), Settings(), null!, solver, FixedStep.Simulation, 94.0));
        Assert.ThrowsException<ArgumentNullException>(() => new LineCore(
            plan, axis, Level(), Settings(), controller, null!, FixedStep.Simulation, 94.0));
        Assert.ThrowsException<ArgumentOutOfRangeException>(() => new LineCore(
            plan, axis, Level(), Settings(), controller, solver, FixedStep.Simulation, 0.0));
    }
}
