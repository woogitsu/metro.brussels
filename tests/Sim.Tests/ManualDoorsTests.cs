using System;
using MetroBxl.Sim.Physics;
using MetroBxl.Sim.Train;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace MetroBxl.Sim.Tests;

/// <summary>
/// Drzwi prowadzone przez maszynistę (MB-08, krok 1 — rdzeń, bez Godota).
///
/// <para><b>Pytanie, na które te testy odpowiadają, brzmi „czy gracz dostał tę samą
/// regułę, co AI", a nie „czy da się otworzyć drzwi".</b> Blokada trakcji jest
/// własnością bezpieczeństwa i ma jedno źródło — <see cref="DoorCycle.TractionAllowed"/>.
/// Tryb ręczny zmienia wyłącznie to, SKĄD bierze się czas trwania fazy otwartej;
/// nie zmienia ani jednej reguły o tym, kiedy wolno ciągnąć. Dlatego kluczowy test
/// tego pliku porównuje LICZBĘ zablokowanych kroków cyklu ręcznego z liczbą kroków
/// cyklu automatycznego o zerowej wymianie pasażerów i żąda równości.</para>
/// </summary>
[TestClass]
public sealed class ManualDoorsTests
{
    private static readonly FixedStep Step = FixedStep.Simulation;

    private static readonly DriverCommand Full = new(1.0, 0.0);

    private static StationStop Manual(double exchange = 20.0) =>
        new(new DoorCycle(exchange), Step, DoorControl.Manual);

    private static int StepsFor(double seconds) => (int)Math.Round(seconds / Step.Seconds);

    // --- tryb automatyczny nie przyjmuje poleceń ręcznych ---------------------

    [TestMethod]
    public void Cykl_automatyczny_odmawia_obu_polecen_recznych()
    {
        var stop = new StationStop(new DoorCycle(20.0), Step);
        Assert.AreEqual(DoorControl.Automatic, stop.Control, "konstruktor dwuargumentowy ma zostać automatem");

        var open = stop.RequestOpen(DriveState.AtRest);
        var close = stop.RequestClose();
        Assert.IsFalse(open.Ok, "automat nie przyjmuje ręcznego otwarcia");
        Assert.IsFalse(close.Ok, "automat nie przyjmuje ręcznego zamknięcia");
        Assert.AreEqual(DoorRefusal.AutomaticControl, open.Refusal,
            "powód odmowy ma nazwać AUTOMAT, a nie stan drzwi");
        Assert.AreEqual(DoorRefusal.AutomaticControl, close.Refusal,
            "ten sam powód w obie strony — cykl prowadzi automat");
    }

    // --- cykl ręczny nie rusza sam -------------------------------------------

    [TestMethod]
    public void Cykl_reczny_nie_rusza_sam_przez_caly_czas_pelnego_postoju_automatycznego()
    {
        // Gdyby tryb ręczny startował sam, ten test byłby zielony tylko przez chwilę:
        // liczba kroków jest DŁUŻSZA niż cały cykl automatyczny z tą samą wymianą.
        var stop = Manual(20.0);
        var steps = StepsFor(stop.Cycle.DwellSeconds) + 240;
        for (var i = 0; i < steps; i++)
        {
            var filtered = stop.Filter(DriveState.AtRest, Full);
            Assert.AreEqual(DoorPhase.Closed, stop.Phase, $"krok {i}: drzwi ruszyły bez polecenia");
            Assert.AreEqual(1.0, filtered.Throttle, 0.0, $"krok {i}: trakcja zablokowana bez otwartych drzwi");
        }

        Assert.IsTrue(stop.Started, "licznik zatrzymania idzie w obu trybach");
        Assert.IsFalse(stop.Finished, "postój bez obsługi drzwi nie jest domknięty");
    }

    // --- odmowy ---------------------------------------------------------------

    [TestMethod]
    public void Otwarcie_w_ruchu_jest_odmowione_a_drzwi_zostaja_zamkniete()
    {
        var stop = Manual();
        var moving = DriveState.AtRest with { SpeedMps = 0.05 };

        var result = stop.RequestOpen(moving);

        Assert.IsFalse(result.Ok, "drzwi otwiera się na stojącym, nie na toczącym się");
        Assert.AreEqual(DoorRefusal.TrainMoving, result.Refusal, "powód ma nazwać RUCH");
        Assert.AreEqual(DoorPhase.Closed, stop.Phase, "odmowa nie ma prawa ruszyć cyklu");
        Assert.AreEqual(1.0, stop.Filter(moving, Full).Throttle, 0.0, "odmowa nie ma prawa zablokować trakcji");
    }

    [TestMethod]
    public void Zamkniecie_przy_drzwiach_zamknietych_jest_odmowione()
    {
        var stop = Manual();
        var result = stop.RequestClose();
        Assert.IsFalse(result.Ok, "nie ma czego zamykać przy drzwiach zamkniętych");
        Assert.AreEqual(DoorRefusal.DoorsNotOpen, result.Refusal, "powód ma nazwać STAN drzwi");
    }

    [TestMethod]
    public void Zamkniecie_w_trakcie_otwierania_jest_odmowione_bo_skrzydla_ida_do_konca()
    {
        var stop = Manual();
        Assert.IsTrue(stop.RequestOpen(DriveState.AtRest).Ok, "otwarcie na stojącym składzie");

        // Faza Unlocking i faza Opening — w obu skrzydła albo się ryglują, albo jadą.
        for (var i = 0; i < StepsFor(DoorCycle.UnlockSeconds + DoorCycle.OpenSeconds) - 1; i++)
        {
            stop.Filter(DriveState.AtRest, Full);
            Assert.AreNotEqual(DoorPhase.Open, stop.Phase, $"krok {i}: faza otwarta przyszła za wcześnie");
            Assert.AreEqual(DoorRefusal.DoorsNotOpen, stop.RequestClose().Refusal, $"krok {i}");
        }
    }

    [TestMethod]
    public void Drugie_otwarcie_przy_otwartych_drzwiach_jest_odmowione()
    {
        var stop = Manual();
        Assert.IsTrue(stop.RequestOpen(DriveState.AtRest).Ok, "otwarcie na stojącym składzie");
        var again = stop.RequestOpen(DriveState.AtRest);
        Assert.IsFalse(again.Ok, "drugie otwarcie w trwającym cyklu jest odmową");
        Assert.AreEqual(DoorRefusal.DoorsAlreadyOpen, again.Refusal, "powód ma nazwać trwający cykl");
    }

    // --- pełny cykl ręczny ----------------------------------------------------

    [TestMethod]
    public void Najkrotszy_cykl_reczny_blokuje_trakcje_DOKLADNIE_tyle_krokow_co_automat_bez_wymiany()
    {
        // TO JEST GŁÓWNY TEST TEGO PLIKU. Liczba po lewej stronie porównania pochodzi
        // z przebiegu trybu RĘCZNEGO, po prawej — ze stałych cyklu. Równość znaczy,
        // że gracz nie dostał łagodniejszej reguły niż AI, tylko inne źródło czasu
        // fazy otwartej.
        var stop = Manual(20.0);
        Assert.IsTrue(stop.RequestOpen(DriveState.AtRest).Ok, "otwarcie na stojącym składzie");

        var blocked = 0;
        var calls = 0;
        var closeSent = false;
        while (!stop.Finished)
        {
            if (calls > 4000)
            {
                Assert.Fail($"cykl ręczny nie domknął się w {calls} krokach, faza {stop.Phase}");
            }

            if (stop.Filter(DriveState.AtRest, Full).Throttle == 0.0)
            {
                blocked++;
            }

            calls++;

            if (!closeSent && stop.Phase == DoorPhase.Open)
            {
                Assert.IsTrue(stop.RequestClose().Ok, "zamknięcie przy drzwiach otwartych");
                closeSent = true;
            }
        }

        Assert.IsTrue(closeSent, "cykl domknął się bez polecenia zamknięcia — drzwi zamknęły się same");
        Assert.AreEqual(1021, calls, "najkrótszy cykl ręczny: 1020 kroków faz stałych + 1 krok w fazie otwartej");
        Assert.AreEqual(StepsFor(DoorCycle.MinimumDwellSeconds), blocked,
            "blokada trakcji ma trwać tyle samo, co w cyklu automatycznym bez wymiany pasażerów");
        Assert.AreEqual(1020, blocked, "liczba przybita wprost, obok wyprowadzonej wyżej");
        Assert.AreEqual(DoorPhase.Closed, stop.Phase, "po kontroli zamknięcia cykl wraca do fazy zamkniętej");
        Assert.AreEqual(1.0, stop.Filter(DriveState.AtRest, Full).Throttle, 0.0, "po kontroli zamknięcia wolno jechać");
    }

    [TestMethod]
    public void Fazy_stale_cyklu_recznego_trwaja_dokladnie_tyle_co_ich_stale()
    {
        var stop = Manual(20.0);
        Assert.IsTrue(stop.RequestOpen(DriveState.AtRest).Ok, "otwarcie na stojącym składzie");

        var counted = new System.Collections.Generic.Dictionary<DoorPhase, int>();
        var closeSent = false;
        while (!stop.Finished && counted.Count < 10)
        {
            var phase = stop.Phase;
            counted[phase] = counted.TryGetValue(phase, out var n) ? n + 1 : 1;
            stop.Filter(DriveState.AtRest, Full);
            if (!closeSent && stop.Phase == DoorPhase.Open)
            {
                Assert.IsTrue(stop.RequestClose().Ok, "zamknięcie przy drzwiach otwartych");
                closeSent = true;
            }
        }

        Assert.AreEqual(StepsFor(DoorCycle.UnlockSeconds), counted[DoorPhase.Unlocking],
            "odryglowanie trwa tyle, co jego stała");
        Assert.AreEqual(StepsFor(DoorCycle.OpenSeconds), counted[DoorPhase.Opening],
            "otwieranie trwa tyle, co jego stała");
        Assert.AreEqual(1, counted[DoorPhase.Open], "maszynista zamknął przy pierwszej możliwości");
        Assert.AreEqual(StepsFor(DoorCycle.ClosingWarningSeconds), counted[DoorPhase.ClosingWarning],
            "sygnał zamykania trwa tyle, co jego stała");
        Assert.AreEqual(StepsFor(DoorCycle.CloseSeconds), counted[DoorPhase.Closing],
            "zamykanie trwa tyle, co jego stała");
        Assert.AreEqual(StepsFor(DoorCycle.CheckSeconds), counted[DoorPhase.Checking],
            "kontrola zamknięcia trwa tyle, co jej stała");
        Assert.IsFalse(counted.ContainsKey(DoorPhase.Closed), "faza zamknięta nie należy do trwającego cyklu");
    }

    [TestMethod]
    public void Drzwi_stoja_otwarte_dopoki_maszynista_nie_zamknie_a_trakcja_stoi_z_nimi()
    {
        var stop = Manual(1.0);
        Assert.IsTrue(stop.RequestOpen(DriveState.AtRest).Ok, "otwarcie na stojącym składzie");

        // Dziesięciokrotność PEŁNEGO postoju automatycznego. Gdyby fazą otwartą rządził
        // `PassengerExchangeSeconds`, cykl domknąłby się tu 10 razy.
        var held = StepsFor(stop.Cycle.DwellSeconds) * 10;
        var reachedOpen = 0;
        for (var i = 0; i < held; i++)
        {
            // Faza czytana PRZED krokiem, bo to ona opisuje ten krok. `Filter` najpierw
            // posuwa cykl, a potem odpowiada — odczyt po nim opisywałby krok następny
            // i przesuwał każdą granicę faz o jeden.
            if (stop.Phase == DoorPhase.Open)
            {
                reachedOpen++;
            }

            var filtered = stop.Filter(DriveState.AtRest, Full);
            Assert.AreEqual(0.0, filtered.Throttle, 0.0, $"krok {i}: trakcja wolna przy niedomkniętym cyklu");
            Assert.IsFalse(stop.Finished, $"krok {i}: cykl domknął się bez polecenia zamknięcia");
        }

        Assert.AreEqual(held - StepsFor(DoorCycle.UnlockSeconds + DoorCycle.OpenSeconds), reachedOpen,
            "po fazach stałych otwierania drzwi mają stać otwarte do końca pomiaru");
        Assert.AreEqual(DoorPhase.Open, stop.Phase,
            "po całym pomiarze drzwi mają nadal stać otwarte");
    }

    [TestMethod]
    public void Cykl_reczny_nie_zeruje_hamulca_tak_samo_jak_automatyczny()
    {
        var stop = Manual();
        Assert.IsTrue(stop.RequestOpen(DriveState.AtRest).Ok, "otwarcie na stojącym składzie");
        var filtered = stop.Filter(DriveState.AtRest, new DriverCommand(1.0, 0.7));
        Assert.AreEqual(0.0, filtered.Throttle, 0.0, "nastawnik zerowany przy niezamkniętych drzwiach");
        Assert.AreEqual(0.7, filtered.Brake, 0.0, "hamulec należy do wołającego w obu trybach");
    }

    [TestMethod]
    public void Cykl_reczny_idzie_dalej_gdy_sklad_sie_stoczyl()
    {
        // Skrót „wróć wprost, gdy skład jeszcze jedzie" był poprawny dla automatu
        // i byłby usterką tutaj: drzwi otwarte zamarłyby w fazie otwartej i nigdy
        // nie doszły do kontroli zamknięcia.
        var stop = Manual(1.0);
        Assert.IsTrue(stop.RequestOpen(DriveState.AtRest).Ok, "otwarcie na stojącym składzie");
        var rolling = DriveState.AtRest with { SpeedMps = 0.4 };

        for (var i = 0; i < StepsFor(DoorCycle.UnlockSeconds + DoorCycle.OpenSeconds); i++)
        {
            stop.Filter(rolling, Full);
        }

        Assert.AreEqual(DoorPhase.Open, stop.Phase, "cykl ma iść mimo ruchu składu");
        Assert.IsTrue(stop.RequestClose().Ok, "zamknięcie przy drzwiach otwartych");
        for (var i = 0; i < StepsFor(DoorCycle.ClosingWarningSeconds + DoorCycle.CloseSeconds + DoorCycle.CheckSeconds) + 1; i++)
        {
            stop.Filter(rolling, Full);
        }

        Assert.IsTrue(stop.Finished, "cykl ręczny domyka się także na składzie w ruchu");
    }

    // --- odpowiedź jako wynik -------------------------------------------------

    [TestMethod]
    public void Odmowa_bez_powodu_jest_bledem_wolajacego()
    {
        Assert.ThrowsException<ArgumentOutOfRangeException>(
            () => DoorRequestResult.Refused(DoorRefusal.None),
            "odmowa bez powodu jest błędem wołającego, nie cichą odmową");
        Assert.IsTrue(DoorRequestResult.Accepted.Ok, "przyjęcie jest przyjęciem");
        Assert.AreEqual(DoorRefusal.None, DoorRequestResult.Accepted.Refusal,
            "przyjęcie nie niesie powodu odmowy");
    }

    [TestMethod]
    public void Kazdy_powod_odmowy_ma_wlasne_zdanie_dla_gracza()
    {
        var seen = new System.Collections.Generic.HashSet<string>();
        foreach (DoorRefusal refusal in Enum.GetValues<DoorRefusal>())
        {
            var reason = new DoorRequestResult(refusal).Reason;
            Assert.IsFalse(string.IsNullOrWhiteSpace(reason), $"{refusal} bez zdania");
            Assert.IsTrue(seen.Add(reason), $"{refusal} powtarza cudze zdanie: {reason}");
        }

        Assert.AreEqual(Enum.GetValues<DoorRefusal>().Length, seen.Count,
            "każdy człon wyliczenia ma własne zdanie — także None");
    }

    [TestMethod]
    public void Nieznany_tryb_sterowania_jest_odrzucany_w_konstruktorze()
    {
        Assert.ThrowsException<ArgumentOutOfRangeException>(
            () => new StationStop(new DoorCycle(1.0), Step, (DoorControl)7),
            "tryb spoza wyliczenia ma paść przy konstruktorze, a nie w środku kroku");
    }
}
