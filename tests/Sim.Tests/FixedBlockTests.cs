using System;
using System.Collections.Generic;
using System.Linq;
using MetroBxl.Sim.Physics;
using MetroBxl.Sim.Signalling;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace MetroBxl.Sim.Tests;

/// <summary>
/// Zajętość bloków, ryglowanie tras i movement authority.
///
/// <para>Plan syntetyczny, a nie pakiet A: te testy sprawdzają **własności modelu**,
/// a granice bloków pakietu A są <c>design_model</c>. Przypięcie ich tutaj przypięłoby
/// założenie, a nie zachowanie.</para>
///
/// <para>Oś syntetyczna ma stacje na 0, 600, 1400 i 2000 m, więc reguła z T-313 daje
/// bloki: <c>P01 [0, 47)</c>, <c>S01 [47, 553)</c>, <c>P02 [553, 647)</c>,
/// <c>S02 [647, 1353)</c>, <c>P03 [1353, 1447)</c>, <c>S03 [1447, 1953)</c>,
/// <c>P04 [1953, 2047)</c> i końcówkę <c>S04 [2047, 2100)</c>.</para>
/// </summary>
[TestClass]
public sealed class FixedBlockTests
{
    private const double TrainLengthM = 94.0;

    private static SignallingPlan Plan(bool requireRoute = false) =>
        SignallingPlanTests.SyntheticPlan(requireRoute, 0.0, 600.0, 1400.0, 2000.0);

    private static FixedBlockSystem System(bool requireRoute = false) => new(Plan(requireRoute));

    private static IReadOnlyList<SignallingEvent> Since(FixedBlockSystem system, int from) =>
        system.Events.Skip(from).ToList();

    // --- zajętość -------------------------------------------------------------------

    [TestMethod]
    public void Blok_pod_skladem_jest_zajety_a_reszta_wolna()
    {
        var system = System();
        system.RegisterTrain("A", 800.0, TrainLengthM);

        Assert.AreEqual(BlockState.Occupied, system.StateOf("S02"));
        Assert.AreEqual("A", system.OccupantOf("S02"));
        Assert.AreEqual(BlockState.Clear, system.StateOf("P02"));
        CollectionAssert.AreEqual(new[] { "S02" }, system.BlocksOccupiedBy("A").ToArray());
    }

    [TestMethod]
    public void Sklad_na_granicy_zajmuje_oba_bloki()
    {
        var system = System();
        system.RegisterTrain("A", 600.0, TrainLengthM); // czoło w P02, tył 506 m w S01

        CollectionAssert.AreEqual(new[] { "S01", "P02" }, system.BlocksOccupiedBy("A").ToArray());
    }

    [TestMethod]
    public void Nie_da_sie_wstawic_skladu_w_blok_zajety()
    {
        var system = System();
        system.RegisterTrain("A", 800.0, TrainLengthM);

        var error = Assert.ThrowsException<InvalidOperationException>(
            () => system.RegisterTrain("B", 850.0, TrainLengthM));
        StringAssert.Contains(error.Message, "S02");
    }

    /// <summary>Zwolnienie bloku ma nastąpić dopiero wtedy, gdy blok opuści **tył** składu.</summary>
    [TestMethod]
    public void Blok_zwalnia_sie_dopiero_gdy_wyjedzie_z_niego_tyl_skladu()
    {
        var system = System();
        system.RegisterTrain("A", 660.0, TrainLengthM); // tył 566 m, czyli w P02

        Assert.AreEqual(BlockState.Occupied, system.StateOf("P02"));

        system.MoveTrain("A", 740.0); // tył 646 m — wciąż w P02
        Assert.AreEqual(BlockState.Occupied, system.StateOf("P02"), "tył jeszcze nie wyjechał");

        var before = system.Events.Count;
        system.MoveTrain("A", 741.5); // tył 647,5 m — już w S02
        Assert.AreEqual(BlockState.Clear, system.StateOf("P02"));
        Assert.IsTrue(
            Since(system, before).Any(e => e.Kind == SignallingEventKind.BlockReleased && e.SubjectId == "P02"),
            "zwolnienie bloku musi wyjść jako zdarzenie, a nie tylko zmienić pole");
    }

    // --- movement authority ----------------------------------------------------------

    [TestMethod]
    public void Bez_innych_skladow_authority_siega_konca_planu()
    {
        var system = System();
        system.RegisterTrain("A", 100.0, TrainLengthM);

        var authority = system.Authority("A");
        Assert.AreEqual(system.Plan.EndM, authority.EndChainageM, 1e-9);
        Assert.AreEqual(AuthorityLimit.EndOfLine, authority.Reason);
    }

    /// <summary>Scenariusz „zajęty blok → authority kończy się wcześniej" z T-313.</summary>
    [TestMethod]
    public void Zajety_blok_skraca_authority_do_jego_poczatku()
    {
        var system = System();
        system.RegisterTrain("A", 100.0, TrainLengthM);
        var free = system.Authority("A").EndChainageM;

        system.RegisterTrain("B", 800.0, TrainLengthM); // B zajmuje wyłącznie S02 [647, 1353)
        var limited = system.Authority("A");

        Assert.IsTrue(limited.EndChainageM < free, $"{limited.EndChainageM:F2} nie jest przed {free:F2}");
        Assert.AreEqual(647.0, limited.EndChainageM, 1e-9, "authority ma kończyć się na granicy zajętego bloku");
        Assert.AreEqual(AuthorityLimit.OccupiedBlock, limited.Reason);
        Assert.AreEqual("S02", limited.LimitBlockId);
    }

    [TestMethod]
    public void Zmiana_authority_wychodzi_jako_zdarzenie()
    {
        var system = System();
        system.RegisterTrain("A", 100.0, TrainLengthM);
        var before = system.Events.Count;

        system.RegisterTrain("B", 800.0, TrainLengthM);

        var issued = Since(system, before)
            .Where(e => e.Kind == SignallingEventKind.AuthorityIssued && e.TrainId == "A")
            .ToList();
        Assert.AreEqual(1, issued.Count, "skrócenie authority składu A ma zostać ogłoszone dokładnie raz");
        StringAssert.Contains(issued[0].Detail, "OccupiedBlock");
    }

    /// <summary>
    /// Dwa składy w kolejnych blokach nie mogą się zejść: authority tylnego kończy się
    /// na granicy bloku zajętego przez przedni, więc między nimi zostaje cały blok.
    /// </summary>
    [TestMethod]
    public void Dwa_sklady_w_kolejnych_blokach_nie_moga_sie_zejsc()
    {
        var system = System();
        system.RegisterTrain("A", 1400.0, TrainLengthM); // czoło w P03, tył 1306 m w S02
        system.RegisterTrain("B", 200.0, TrainLengthM);

        var authority = system.Authority("B");
        Assert.AreEqual(647.0, authority.EndChainageM, 1e-9);

        system.MoveTrain("B", authority.EndChainageM);
        Assert.IsFalse(
            system.Events.Any(e => e.Kind == SignallingEventKind.AuthorityViolation),
            "jazda dokładnie do końca authority nie jest naruszeniem");
        Assert.IsTrue(
            system.RearOf("A") - system.FrontOf("B") > 0.0,
            "między tyłem A a czołem B musi zostać dystans");
    }

    [TestMethod]
    public void Przejechanie_konca_authority_wychodzi_jako_naruszenie()
    {
        var system = System();
        system.RegisterTrain("A", 1400.0, TrainLengthM);
        system.RegisterTrain("B", 200.0, TrainLengthM);

        system.MoveTrain("B", 700.0);

        var violations = system.Events.Where(e => e.Kind == SignallingEventKind.AuthorityViolation).ToList();
        Assert.AreEqual(2, violations.Count, "przejechanie authority i wjazd w cudzy blok to dwa osobne naruszenia");
        Assert.AreEqual("B", violations[0].TrainId);
        StringAssert.Contains(violations[0].Detail, "authority-end=647.000");
        StringAssert.Contains(violations[1].Detail, "occupied-by=A");
    }

    [TestMethod]
    public void Sklad_nie_moze_cofnac_sie_na_planie()
    {
        var system = System();
        system.RegisterTrain("A", 800.0, TrainLengthM);

        Assert.ThrowsException<ArgumentOutOfRangeException>(() => system.MoveTrain("A", 790.0));
    }

    // --- duże dt ---------------------------------------------------------------------

    /// <summary>
    /// Scenariusz „duże <c>dt</c> nie pozwala przeskoczyć occupancy bez aktualizacji".
    ///
    /// <para>Skok o 1560 m w jednym wywołaniu przechodzi przez pięć bloków. Model, który
    /// patrzyłby tylko na punkt końcowy, zameldowałby zajęcie jednego bloku i zgubiłby
    /// cztery. Tutaj każdy blok po drodze ma swoje zajęcie i swoje zwolnienie.</para>
    /// </summary>
    [TestMethod]
    public void Duzy_skok_zajmuje_i_zwalnia_kazdy_blok_po_drodze()
    {
        var system = System();
        system.RegisterTrain("A", 100.0, TrainLengthM);
        var before = system.Events.Count;

        system.MoveTrain("A", 1660.0);

        var occupied = Since(system, before)
            .Where(e => e.Kind == SignallingEventKind.BlockOccupied)
            .Select(e => e.SubjectId)
            .ToArray();
        CollectionAssert.AreEqual(new[] { "P02", "S02", "P03", "S03" }, occupied,
            "każdy blok na zamiecionym odcinku musi zostać zameldowany");

        var released = Since(system, before)
            .Where(e => e.Kind == SignallingEventKind.BlockReleased)
            .Select(e => e.SubjectId)
            .ToArray();
        CollectionAssert.AreEqual(new[] { "P01", "S01", "P02", "S02", "P03" }, released);
        CollectionAssert.AreEqual(new[] { "S03" }, system.BlocksOccupiedBy("A").ToArray());
    }

    /// <summary>
    /// Ten sam skok, ale przez blok zajęty przez inny skład. Zajętość nie zostaje
    /// przejęta, a naruszenie zostaje zgłoszone — mimo że na końcu skoku składy
    /// są już w różnych blokach i „na zdjęciu" nic się nie stało.
    /// </summary>
    [TestMethod]
    public void Duzy_skok_przez_zajety_blok_nie_przechodzi_po_cichu()
    {
        var system = System();
        system.RegisterTrain("A", 800.0, TrainLengthM); // A wyłącznie w S02
        system.RegisterTrain("B", 200.0, TrainLengthM);
        var before = system.Events.Count;

        system.MoveTrain("B", 1900.0); // przeskok przez cały blok A

        var conflicts = Since(system, before)
            .Where(e => e.Kind == SignallingEventKind.AuthorityViolation &&
                        e.Detail.StartsWith("occupied-by", StringComparison.Ordinal))
            .ToList();
        Assert.AreEqual("S02", conflicts[0].SubjectId);
        Assert.AreEqual(1, conflicts.Count, "wjazd w blok zajęty musi zostać zgłoszony");
        StringAssert.Contains(conflicts[0].Detail, "occupied-by=A");
        Assert.AreEqual("A", system.OccupantOf("S02"), "intruz nie przejmuje cudzej zajętości");
    }

    // --- trasy -----------------------------------------------------------------------

    [TestMethod]
    public void Trasa_rezerwuje_swoje_bloki_i_wydluza_authority()
    {
        var system = System(requireRoute: true);
        system.RegisterTrain("A", 600.0, TrainLengthM);

        var beforeRoute = system.Authority("A");
        Assert.AreEqual(AuthorityLimit.BlockNotReserved, beforeRoute.Reason, "bez trasy nie ma jazdy dalej niż blok");
        Assert.AreEqual(647.0, beforeRoute.EndChainageM, 1e-9);

        Assert.IsTrue(system.RequestRoute("R02", "A"));
        Assert.AreEqual(BlockState.Reserved, system.StateOf("P03"));
        Assert.AreEqual("R02", system.ReservationOf("S02"));

        var afterRoute = system.Authority("A");
        Assert.AreEqual(1447.0, afterRoute.EndChainageM, 1e-9, "authority sięga końca bloku docelowego trasy");
    }

    [TestMethod]
    public void Zadanie_trasy_przez_blok_zajety_zostaje_odrzucone()
    {
        var system = System(requireRoute: true);
        system.RegisterTrain("A", 600.0, TrainLengthM);
        system.RegisterTrain("B", 1400.0, TrainLengthM); // B stoi w P03, czyli w celu trasy R02

        Assert.IsFalse(system.RequestRoute("R02", "A"));

        var rejection = system.Events.Single(e => e.Kind == SignallingEventKind.RouteRejected);
        StringAssert.Contains(rejection.Detail, "block-occupied:S02:B");
        Assert.IsNull(system.RouteOf("A"));
    }

    /// <summary>
    /// Scenariusz „conflicting routes → jedna zostaje odrzucona".
    ///
    /// <para>R02 (P02→P03) i R03 (P03→P04) dzielą blok P03, więc są w konflikcie.
    /// Skład B rygluje R03 i wyjeżdża z P03 na szlak; P03 nie jest już zajęty, ale
    /// **wciąż jest zarezerwowany** pod R03 — i to wystarcza, żeby żądanie R02
    /// zostało odrzucone.</para>
    /// </summary>
    [TestMethod]
    public void Dwie_trasy_w_konflikcie_nie_zostaja_zaryglowane()
    {
        var plan = Plan(requireRoute: true);
        Assert.IsTrue(plan.RouteById("R02").ConflictsWith(plan.RouteById("R03")), "R02 i R03 dzielą P03");

        var system = new FixedBlockSystem(plan);
        system.RegisterTrain("A", 600.0, TrainLengthM);
        system.RegisterTrain("B", 1400.0, TrainLengthM);

        Assert.IsTrue(system.RequestRoute("R03", "B"));
        system.MoveTrain("B", 1500.0); // czoło B w S03, tył 1406 m — jeszcze w P03
        system.MoveTrain("B", 1600.0); // tył 1506 m — P03 zwolniony, ale zarezerwowany

        Assert.AreEqual(BlockState.Reserved, system.StateOf("P03"));
        Assert.IsFalse(system.RequestRoute("R02", "A"));

        var rejection = system.Events.Last(e => e.Kind == SignallingEventKind.RouteRejected);
        StringAssert.Contains(rejection.Detail, "block-reserved:P03:R03");
    }

    [TestMethod]
    public void Trasa_zwalnia_sie_gdy_sklad_wjedzie_do_bloku_docelowego()
    {
        var system = System(requireRoute: true);
        system.RegisterTrain("A", 600.0, TrainLengthM);
        Assert.IsTrue(system.RequestRoute("R02", "A"));

        system.MoveTrain("A", 1300.0);
        Assert.AreEqual("R02", system.RouteOf("A"), "trasa trzyma, dopóki czoło nie wjedzie do celu");

        var before = system.Events.Count;
        system.MoveTrain("A", 1400.0);

        Assert.IsNull(system.RouteOf("A"));
        CollectionAssert.DoesNotContain(system.LockedRoutes.ToArray(), "R02");
        Assert.IsTrue(Since(system, before).Any(e => e.Kind == SignallingEventKind.RouteReleased && e.SubjectId == "R02"));
        Assert.IsNull(system.ReservationOf("S02"), "rezerwacja zeszła razem z trasą");
        Assert.AreEqual(BlockState.Occupied, system.StateOf("S02"), "ogon składu wciąż stoi w S02 — zajętość zostaje");
    }

    [TestMethod]
    public void Trasa_z_innego_miejsca_niz_stoi_sklad_zostaje_odrzucona()
    {
        var system = System(requireRoute: true);
        system.RegisterTrain("A", 600.0, TrainLengthM);

        Assert.IsFalse(system.RequestRoute("R03", "A"));
        StringAssert.Contains(
            system.Events.Single(e => e.Kind == SignallingEventKind.RouteRejected).Detail,
            "train-not-at-route-entry:P02");
    }

    // --- determinizm i odtworzenie -----------------------------------------------------

    private static FixedBlockSystem RunScript(SignallingPlan plan)
    {
        var system = new FixedBlockSystem(plan);
        system.RegisterTrain("A", 600.0, TrainLengthM);
        system.RegisterTrain("B", 0.0, TrainLengthM);
        system.RequestRoute("R01", "B");   // odrzucone: A zajmuje S01 i P02
        system.RequestRoute("R02", "A");
        system.MoveTrain("A", 900.0);
        system.MoveTrain("A", 1400.0);
        system.RequestRoute("R01", "B");
        system.MoveTrain("B", 300.0);
        system.MoveTrain("B", 600.0);
        return system;
    }

    /// <summary>Ten sam ciąg wywołań ma dać ten sam strumień zdarzeń, co do bitu.</summary>
    [TestMethod]
    public void Ten_sam_scenariusz_daje_identyczny_strumien_zdarzen()
    {
        var first = RunScript(Plan(requireRoute: true));
        var second = RunScript(Plan(requireRoute: true));

        Assert.AreEqual(first.Events.Count, second.Events.Count);
        for (var i = 0; i < first.Events.Count; i++)
        {
            Assert.AreEqual(first.Events[i].Kind, second.Events[i].Kind, $"zdarzenie {i}");
            Assert.AreEqual(first.Events[i].SubjectId, second.Events[i].SubjectId, $"zdarzenie {i}");
            Assert.AreEqual(first.Events[i].TrainId, second.Events[i].TrainId, $"zdarzenie {i}");
            Assert.AreEqual(first.Events[i].Detail, second.Events[i].Detail, $"zdarzenie {i}");
            Assert.AreEqual(
                BitConverter.DoubleToInt64Bits(first.Events[i].ChainageM),
                BitConverter.DoubleToInt64Bits(second.Events[i].ChainageM),
                $"chainage zdarzenia {i}");
        }

        Assert.AreEqual(first.StateDigest(), second.StateDigest());
    }

    /// <summary>Scenariusz „restart/replay tego samego event stream → identyczny stan".</summary>
    [TestMethod]
    public void Odtworzenie_ze_strumienia_zdarzen_daje_identyczny_stan()
    {
        var plan = Plan(requireRoute: true);
        var live = RunScript(plan);

        var replayed = FixedBlockSystem.Replay(plan, live.Events);

        Assert.AreEqual(live.StateDigest(), replayed.StateDigest());
        CollectionAssert.AreEqual(live.TrainIds.ToArray(), replayed.TrainIds.ToArray());
        CollectionAssert.AreEqual(live.LockedRoutes.ToArray(), replayed.LockedRoutes.ToArray());
        foreach (var trainId in live.TrainIds)
        {
            Assert.AreEqual(live.Authority(trainId), replayed.Authority(trainId), trainId);
        }
    }

    [TestMethod]
    public void Odcisk_stanu_zmienia_sie_przy_kazdej_zmianie_ryglowania()
    {
        var system = System(requireRoute: true);
        var empty = system.StateDigest();

        system.RegisterTrain("A", 600.0, TrainLengthM);
        var withTrain = system.StateDigest();
        Assert.AreNotEqual(empty, withTrain);

        system.RequestRoute("R02", "A");
        Assert.AreNotEqual(withTrain, system.StateDigest());
    }

    /// <summary>
    /// Zdarzenia zmieniające stan ryglowania mogą pochodzić tylko z samego systemu.
    /// Gdyby warstwa ochrony mogła je wstrzyknąć, zapis rozjechałby się ze stanem
    /// i odtworzenie przestałoby cokolwiek dowodzić.
    /// </summary>
    [TestMethod]
    public void Warstwa_ochrony_nie_moze_wstrzyknac_zdarzenia_stanu()
    {
        var system = System();
        system.RegisterTrain("A", 600.0, TrainLengthM);

        Assert.ThrowsException<ArgumentOutOfRangeException>(
            () => system.Report(SignallingEventKind.BlockOccupied, "P03", "A", 600.0, string.Empty));
    }

    /// <summary>
    /// <c>CLAUDE.md</c> reguła 9 i zasada 6 z T-313: sygnalizacja jest w tym samym
    /// rdzeniu co fizyka i tak samo nie zna silnika.
    /// </summary>
    [TestMethod]
    public void Sygnalizacja_siedzi_w_rdzeniu_bez_silnika()
    {
        Assert.AreSame(typeof(VehicleModel).Assembly, typeof(FixedBlockSystem).Assembly);
        Assert.IsFalse(
            typeof(FixedBlockSystem).Assembly.GetReferencedAssemblies()
                .Any(a => (a.Name ?? string.Empty).Contains("Godot", StringComparison.OrdinalIgnoreCase)));
    }
}
