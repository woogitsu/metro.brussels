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
