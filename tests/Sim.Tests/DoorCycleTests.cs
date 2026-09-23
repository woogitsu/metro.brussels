using System.Globalization;
using System.Text.RegularExpressions;
using MetroBxl.Sim.Physics;
using MetroBxl.Sim.Train;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace MetroBxl.Sim.Tests;

/// <summary>
/// Cykl drzwi i blokada jazdy (T-312).
///
/// Testy pilnują dwóch rzeczy o różnym ciężarze. Czasy faz są <c>design_model</c>
/// z <c>docs/02-simulation.md</c> i mogą się zmienić, gdy pojawi się źródło — te testy
/// przypinają je, żeby zmiana była świadoma, nie przypadkowa. Blokada trakcji jest
/// własnością BEZPIECZEŃSTWA i nie ma prawa się zmienić bez zmiany dokumentu.
/// </summary>
[TestClass]
public sealed class DoorCycleTests
{
    private static readonly FixedStep Step = FixedStep.Simulation;

    private static DoorCycle Cycle(double exchange = 20.0) => new(exchange);

    // --- czasy faz -----------------------------------------------------------

    [TestMethod]
    public void Fazy_maja_czasy_z_dokumentu()
    {
        var cycle = Cycle();
        Assert.AreEqual(0.5, cycle.PhaseSeconds(DoorPhase.Unlocking), 0.0);
        Assert.AreEqual(2.0, cycle.PhaseSeconds(DoorPhase.Opening), 0.0);
        Assert.AreEqual(3.0, cycle.PhaseSeconds(DoorPhase.ClosingWarning), 0.0);
        Assert.AreEqual(2.5, cycle.PhaseSeconds(DoorPhase.Closing), 0.0);
        Assert.AreEqual(0.5, cycle.PhaseSeconds(DoorPhase.Checking), 0.0);
    }

    [TestMethod]
    public void Minimalny_postoj_jest_suma_faz_stalych_a_nie_osobna_liczba()
    {
        var sum = DoorCycle.UnlockSeconds + DoorCycle.OpenSeconds + DoorCycle.ClosingWarningSeconds
                  + DoorCycle.CloseSeconds + DoorCycle.CheckSeconds;
        Assert.AreEqual(sum, DoorCycle.MinimumDwellSeconds, 0.0);
        Assert.AreEqual(8.5, DoorCycle.MinimumDwellSeconds, 1e-12);
    }

    [TestMethod]
    public void Wymiana_pasazerow_wydluza_postoj_o_dokladnie_swoj_czas()
    {
        Assert.AreEqual(DoorCycle.MinimumDwellSeconds, Cycle(0.0).DwellSeconds, 1e-12);
        Assert.AreEqual(DoorCycle.MinimumDwellSeconds + 42.0, Cycle(42.0).DwellSeconds, 1e-12);
    }

    [TestMethod]
    public void Ujemna_wymiana_pasazerow_jest_odrzucana()
    {
        Assert.ThrowsException<System.ArgumentOutOfRangeException>(() => new DoorCycle(-0.001));
        Assert.ThrowsException<System.ArgumentOutOfRangeException>(() => new DoorCycle(double.NaN));
    }

    // --- przebieg cyklu ------------------------------------------------------

    [TestMethod]
    public void Cykl_przechodzi_fazy_w_kolejnosci_z_dokumentu()
    {
        var cycle = Cycle(10.0);
        Assert.AreEqual(DoorPhase.Unlocking, cycle.At(0.0).Phase);
        Assert.AreEqual(DoorPhase.Unlocking, cycle.At(0.49).Phase);
        Assert.AreEqual(DoorPhase.Opening, cycle.At(0.51).Phase);
        Assert.AreEqual(DoorPhase.Open, cycle.At(2.51).Phase);
        Assert.AreEqual(DoorPhase.ClosingWarning, cycle.At(12.51).Phase);
        Assert.AreEqual(DoorPhase.Closing, cycle.At(15.51).Phase);
        Assert.AreEqual(DoorPhase.Checking, cycle.At(18.01).Phase);
        Assert.AreEqual(DoorPhase.Closed, cycle.At(18.51).Phase);
    }

    [TestMethod]
    public void Zerowa_wymiana_nie_kasuje_fazy_otwartych_drzwi_z_cyklu()
    {
        var cycle = Cycle(0.0);
        Assert.AreEqual(0.0, cycle.PhaseSeconds(DoorPhase.Open), 0.0);
        // po otwieraniu wchodzimy od razu w sygnał zamykania, ale cykl nadal trwa
        Assert.AreEqual(DoorPhase.ClosingWarning, cycle.At(2.6).Phase);
        Assert.AreEqual(DoorPhase.Closed, cycle.At(DoorCycle.MinimumDwellSeconds + 1e-9).Phase);
    }

    [TestMethod]
    public void Czas_w_fazie_liczy_sie_od_jej_poczatku_a_nie_od_zatrzymania()
    {
        var (phase, elapsed) = Cycle(10.0).At(1.25);
        Assert.AreEqual(DoorPhase.Opening, phase);
        Assert.AreEqual(0.75, elapsed, 1e-12);
    }

    // --- blokada jazdy: własność bezpieczeństwa ------------------------------

    [TestMethod]
    public void Trakcja_jest_wolna_wylacznie_przy_drzwiach_zamknietych()
    {
        foreach (DoorPhase phase in System.Enum.GetValues(typeof(DoorPhase)))
        {
            Assert.AreEqual(phase == DoorPhase.Closed, DoorCycle.TractionAllowed(phase), phase.ToString());
        }
    }

    [TestMethod]
    public void Kontrola_zamkniecia_nadal_blokuje_mimo_ze_skrzydla_juz_stoja()
    {
        // To jest sens zdania „jazda zablokowana do POTWIERDZENIA zamknięcia":
        // skrzydła zetknęły się na końcu fazy Closing, a jechać wolno dopiero 0,5 s później.
        Assert.IsFalse(DoorCycle.LeavesMoving(DoorPhase.Checking));
        Assert.IsFalse(DoorCycle.TractionAllowed(DoorPhase.Checking));
    }

    [TestMethod]
    public void Postoj_zeruje_nastawnik_przez_caly_cykl_i_zwalnia_dopiero_na_koncu()
    {
        var stop = new StationStop(Cycle(5.0), Step);
        var state = DriveState.AtRest;
        var full = new DriverCommand(1.0, 0.0);
        var blocked = 0;
        var steps = (int)System.Math.Round(stop.Cycle.DwellSeconds / Step.Seconds) + 2;
        for (var i = 0; i < steps; i++)
        {
            var filtered = stop.Filter(state, full);
            if (filtered.Throttle == 0.0)
            {
                blocked++;
            }
        }

        Assert.IsTrue(stop.Finished, "cykl miał się domknąć");
        Assert.AreEqual((int)System.Math.Round(stop.Cycle.DwellSeconds / Step.Seconds), blocked,
            "blokada ma trwać dokładnie tyle, co cykl");
    }

    [TestMethod]
    public void Postoj_nie_zaczyna_sie_dopoki_sklad_jedzie()
    {
        var stop = new StationStop(Cycle(5.0), Step);
        var moving = DriveState.AtRest with { SpeedMps = 0.5 };
        var full = new DriverCommand(1.0, 0.0);
        for (var i = 0; i < 100; i++)
        {
            Assert.AreEqual(1.0, stop.Filter(moving, full).Throttle, 0.0);
        }

        Assert.IsFalse(stop.Started, "toczący się skład nie otwiera drzwi");
    }

    [TestMethod]
    public void Postoj_nie_zeruje_hamulca()
    {
        var stop = new StationStop(Cycle(1.0), Step);
        var filtered = stop.Filter(DriveState.AtRest, new DriverCommand(1.0, 0.7));
        Assert.AreEqual(0.0, filtered.Throttle, 0.0);
        Assert.AreEqual(0.7, filtered.Brake, 0.0, "skład ma stać, a nie toczyć się przy otwartych drzwiach");
    }

    /// <summary>
    /// Wiersz postoju idzie do logu przebiegu, więc nie zależy od kultury maszyny —
    /// także w części zagnieżdżonej, czasie od zatrzymania (23.09.2026, 6.D365).
    /// Zagnieżdżony literał interpolowany formatuje się w kulturze BIEŻĄCEJ, zanim
    /// zewnętrzny <c>string.Create(InvariantCulture, …)</c> go zobaczy — dlatego
    /// kultura z przecinkiem jest tu ustawiana jawnie, a nie zostawiana maszynie.
    /// </summary>
    [TestMethod]
    public void Wiersz_postoju_nie_zalezy_od_kultury_maszyny()
    {
        var stop = new StationStop(Cycle(5.0), Step);
        for (var i = 0; i < 30; i++)
        {
            stop.Filter(DriveState.AtRest, new DriverCommand(0.0, 1.0));
        }

        Assert.IsTrue(stop.Started, "postój miał się rozpocząć — wiersz nie niesie czasu");
        var previous = CultureInfo.CurrentCulture;
        string line;
        CultureInfo.CurrentCulture = CultureInfo.GetCultureInfo("pl-PL");
        try
        {
            Assert.AreEqual(",", CultureInfo.CurrentCulture.NumberFormat.NumberDecimalSeparator,
                "kultura pl-PL nie ma przecinka dziesiętnego — test nie sprawdza tego, co obiecuje");
            line = stop.ToString();
        }
        finally
        {
            CultureInfo.CurrentCulture = previous;
        }

        System.Console.WriteLine(line);
        StringAssert.Matches(line, new Regex(@": \d+\.\d{2} s, faza "),
            "czas od zatrzymania nie jest zapisany z kropką dziesiętną");
        StringAssert.Contains(line, "pełny cykl 13.5 s", "pełny cykl nie jest zapisany z kropką dziesiętną");
    }

    // --- oś czasu ------------------------------------------------------------

    [TestMethod]
    public void Os_czasu_konczy_sie_na_pelnym_postoju()
    {
        var cycle = Cycle(12.0);
        var timeline = StationStop.Timeline(cycle, Step);
        Assert.AreEqual(DoorCycle.Sequence.Count, timeline.Count);
        Assert.AreEqual(cycle.DwellSeconds, timeline[^1].EndsAtSeconds, 1e-12);
        for (var i = 1; i < timeline.Count; i++)
        {
            Assert.IsTrue(timeline[i].EndsAtSeconds >= timeline[i - 1].EndsAtSeconds);
        }
    }
}
