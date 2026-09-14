using System;
using System.Collections.Generic;
using MetroBxl.Sim.Line;
using MetroBxl.Sim.Physics;
using MetroBxl.Sim.Train;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace MetroBxl.Sim.Tests;

/// <summary>
/// Pełne flow z Issue #26 na poziomie linii: obserwacja → przejęcie → stop → drzwi →
/// odjazd → oddanie (MB-08).
///
/// <para><b>Dlaczego te testy naprawdę PROWADZĄ skład, zamiast ustawić stan wprost.</b>
/// Tryb drzwi zależy od tego, kto był właścicielem sterowania W CHWILI, gdy skład stanął
/// w oknie peronu — a tej chwili nie da się udać. Test, który podstawia
/// <c>StationStop</c> z trybem ręcznym, sprawdziłby <see cref="StationStop"/> jeszcze raz,
/// a nie to, czy linia ten tryb w ogóle komuś nadaje. Dlatego jest tu pętla z prostym
/// maszynistą: ciąg, dopóki droga hamowania mieści się w pozostałym dystansie, potem
/// pełny hamulec służbowy.</para>
/// </summary>
[TestClass]
public sealed class ManualDoorsOnLineTests
{
    private const string TrainId = "A";

    private static readonly double[] Stations = { 0.0, 600.0, 1400.0, 2000.0 };

    private static RunConditions Level() => RunConditions.Level(VehicleModel.M7, TrainLoad.Aw0);

    private static LineRunSettings Settings() => new(Units.KmhToMps(60.0), 10.0, 1.0, 5.0);

    private static LineCore Line() => LineCore.M7(
        SignallingPlanTests.SyntheticPlan(requireRoute: false, Stations),
        SignallingPlanTests.SyntheticAxis(Stations),
        Level(),
        Settings());

    /// <summary>Linia z jednym składem, który już wjechał na plan i ma właściciela.</summary>
    private static (LineCore Line, LineTrain Train) Taken()
    {
        var line = Line();
        line.Add(TrainId, 0L);
        line.Step();
        var train = line.TakeControl(TrainId);
        Assert.AreEqual(ControlOwner.Driver, train.Owner,
            "bez przejęcia reszta tego pliku nie mierzy tego, o co pyta");
        return (line, train);
    }

    /// <summary>
    /// Prosty maszynista: ciąg, dopóki droga hamowania mieści się w pozostałym dystansie.
    ///
    /// <para>Nie jest to kopia autopilota i nie ma nią być — autopilot ma zatrzask,
    /// autorytet i wybieg. To jest tyle sterowania, ile trzeba, żeby skład zatrzymał się
    /// w oknie peronu <b>z ręki człowieka</b>, bo tylko wtedy postój dostanie tryb ręczny.</para>
    /// </summary>
    private static DriverCommand DriverAiming(LineDrive drive)
    {
        var target = drive.NextStation!.Value.ChainageM;
        var remaining = target - drive.ChainageM;
        if (remaining <= 0.0)
        {
            return DriverCommand.FullServiceBrake;
        }

        // Opóźnienie przyjęte OSTROŻNIE (1,1 m/s² — sam hamulec, bez oporów), więc skład
        // hamuje za wcześnie i staje PRZED punktem zatrzymania. Ta sama reguła dociąga go
        // potem do peronu: przy zerowej prędkości droga hamowania jest zerowa, więc
        // warunek znowu daje ciąg. Zapas 0,20 m sprawia, że dociąganie idzie centymetrami,
        // a nie skokiem przez okno peronu — skład zatrzymany ZA oknem byłby w tym teście
        // stacją MINIĘTĄ, czyli mierzyłby coś innego, niż mierzy.
        // SUFIT PRĘDKOŚCI MALEJĄCY Z ODLEGŁOŚCIĄ, a nie samo „hamuj, gdy blisko".
        // Wersja bez sufitu przejeżdżała peron POWOLI i stawała 8,82 m za punktem
        // zatrzymania (zmierzone) — bo przy prędkości rzędu metra na sekundę droga
        // hamowania jest krótsza niż krok decyzji, więc warunek „droga hamowania mieści
        // się w pozostałym dystansie" pozwalał ciągnąć aż do samego peronu i dalej.
        var speed = drive.State.SpeedMps;
        var stopping = speed * speed / (2.0 * 1.1);
        var cap = remaining > 60.0 ? 12.0 : remaining > 10.0 ? 3.0 : 0.6;
        return speed > cap || remaining <= stopping + 0.10
            ? DriverCommand.FullServiceBrake
            : new DriverCommand(0.5, 0.0);
    }

    /// <summary>Prowadzi skład ręcznie aż do postoju; zwraca liczbę wykonanych kroków.</summary>
    private static int DriveToPlatform(LineCore line, LineTrain train, int budget = 40_000)
    {
        for (var i = 0; i < budget; i++)
        {
            if (train.Drive!.AtStation)
            {
                var stopped = train.Drive.NextStation!.Value.ChainageM;
                Assert.IsTrue(
                    Math.Abs(train.Drive.ChainageM - stopped) <= 5.0,
                    $"skład stanął {train.Drive.ChainageM - stopped:F2} m od punktu zatrzymania — "
                    + "poza oknem peronu ten test mierzyłby stację MINIĘTĄ, nie postój");
                return i;
            }

            line.Drive(TrainId, DriverAiming(train.Drive));
            line.Step();
        }

        Assert.Fail($"skład nie dojechał do peronu w {budget} krokach, " +
            $"kilometraż {train.Drive!.ChainageM:F2} m");
        return budget;
    }

    // --- tryb postoju idzie za właścicielem ----------------------------------

    [TestMethod]
    public void Postoj_skladu_prowadzonego_przez_autopilota_jest_AUTOMATYCZNY()
    {
        var line = Line();
        line.Add(TrainId, 0L);
        var train = line.Trains[0];
        for (var i = 0; i < 40_000 && !(train.Drive?.AtStation ?? false); i++)
        {
            line.Step();
        }

        Assert.IsTrue(train.Drive!.AtStation, "autopilot miał dojechać do peronu");
        Assert.AreEqual(DoorControl.Automatic, train.Drive.StopDoorControl,
            "postój autopilota ma tryb sprzed MB-08");
    }

    [TestMethod]
    public void Postoj_skladu_prowadzonego_przez_czlowieka_jest_RECZNY_a_drzwi_stoja_zamkniete()
    {
        var (line, train) = Taken();
        DriveToPlatform(line, train);

        Assert.AreEqual(DoorControl.Manual, train.Drive!.StopDoorControl,
            "postój założony pod ręką człowieka ma być ręczny");
        Assert.AreEqual(DoorPhase.Closed, train.Drive.Phase, "drzwi nie otwierają się same");
        Assert.IsTrue(double.IsNaN(train.Drive.DwellRemainingSeconds),
            "na postoju ręcznym nikt nie zna długości fazy otwartej");
    }

    // --- pełne flow #26 -------------------------------------------------------

    [TestMethod]
    public void Pelne_flow_przejecie_stop_drzwi_odjazd_oddanie()
    {
        var (line, train) = Taken();
        DriveToPlatform(line, train);
        var drive = train.Drive!;
        var stationBefore = drive.Calls.Count;

        Assert.IsTrue(line.RequestDoorOpen(TrainId).Ok, "otwarcie na stojącym składzie w oknie peronu");

        // Blokada trakcji: pełny nastawnik człowieka nie rusza składu ani o krok.
        var chainageAtOpen = drive.ChainageM;
        for (var i = 0; i < 2000 && drive.Phase != DoorPhase.Open; i++)
        {
            line.Drive(TrainId, new DriverCommand(1.0, 0.0));
            line.Step();
        }

        Assert.AreEqual(DoorPhase.Open, drive.Phase, "cykl ręczny miał dojść do fazy otwartej");
        Assert.AreEqual(chainageAtOpen, drive.ChainageM, 0.0,
            "pełny nastawnik przy otwierających się drzwiach nie ma prawa ruszyć składu");

        // Drzwi stoją otwarte, dopóki maszynista nie zamknie.
        for (var i = 0; i < 3600; i++)
        {
            line.Drive(TrainId, new DriverCommand(1.0, 0.0));
            line.Step();
            Assert.AreEqual(DoorPhase.Open, drive.Phase, $"krok {i}: drzwi zamknęły się same");
        }

        Assert.IsTrue(line.RequestDoorClose(TrainId).Ok, "zamknięcie przy drzwiach otwartych");
        for (var i = 0; i < 2000 && drive.AtStation; i++)
        {
            line.Drive(TrainId, DriverCommand.FullServiceBrake);
            line.Step();
        }

        Assert.IsFalse(drive.AtStation, "po kontroli zamknięcia postój ma się domknąć");
        Assert.AreEqual(stationBefore, drive.Calls.Count - 0, "postój został odnotowany raz");
        Assert.IsTrue(double.IsFinite(drive.Calls[^1].DepartureSeconds), "odjazd ma czas");

        line.ReleaseControl(TrainId);
        Assert.AreEqual(ControlOwner.Autopilot, train.Owner,
            "oddanie ma wrócić skład autopilotowi");
    }

    // --- przejęcie i oddanie w czasie cyklu ----------------------------------

    [TestMethod]
    public void Oddanie_sterowania_w_czasie_cyklu_NIE_resetuje_drzwi_a_autopilot_dopilnowuje_reszty()
    {
        var (line, train) = Taken();
        DriveToPlatform(line, train);
        var drive = train.Drive!;
        Assert.IsTrue(line.RequestDoorOpen(TrainId).Ok, "otwarcie na stojącym składzie w oknie peronu");

        for (var i = 0; i < 2000 && drive.Phase != DoorPhase.Open; i++)
        {
            line.Drive(TrainId, DriverCommand.FullServiceBrake);
            line.Step();
        }

        Assert.AreEqual(DoorPhase.Open, drive.Phase, "cykl ręczny miał dojść do fazy otwartej");

        // ODDANIE W ŚRODKU CYKLU. Drzwi mają zostać otwarte — nie wrócić do zamkniętych,
        // nie zacząć cyklu od nowa i nie zmienić trybu trwającego postoju.
        line.ReleaseControl(TrainId);
        line.Step();
        Assert.AreEqual(DoorPhase.Open, drive.Phase, "oddanie sterowania zresetowało drzwi");
        Assert.AreEqual(DoorControl.Manual, drive.StopDoorControl, "trwający postój zmienił tryb");

        // ...a potem autopilot ma ten postój DOMKNĄĆ. Bez tego linia stanęłaby na zawsze.
        for (var i = 0; i < 20_000 && drive.AtStation; i++)
        {
            line.Step();
        }

        Assert.IsFalse(drive.AtStation, "autopilot nie domknął cudzego, ręcznie otwartego postoju");
        Assert.IsTrue(double.IsFinite(drive.Calls[^1].DepartureSeconds),
            "postój domknięty przez autopilota ma czas odjazdu");
    }

    [TestMethod]
    public void Przejecie_w_czasie_cyklu_AUTOMATYCZNEGO_nie_resetuje_drzwi_i_nie_zmienia_trybu()
    {
        var line = Line();
        line.Add(TrainId, 0L);
        var train = line.Trains[0];
        for (var i = 0; i < 40_000 && train.Drive?.Phase != DoorPhase.Open; i++)
        {
            line.Step();
        }

        var drive = train.Drive!;
        Assert.AreEqual(DoorPhase.Open, drive.Phase,
            "bez fazy otwartej test nie mierzy przejęcia W ŚRODKU cyklu");

        line.TakeControl(TrainId);
        line.Drive(TrainId, DriverCommand.FullServiceBrake);
        line.Step();

        Assert.AreEqual(DoorPhase.Open, drive.Phase, "przejęcie zresetowało drzwi");
        Assert.AreEqual(DoorControl.Automatic, drive.StopDoorControl,
            "tryb trwającego postoju idzie za tym, kto go ZAKŁADAŁ, a nie za bieżącym właścicielem");
        Assert.AreEqual(DoorRefusal.AutomaticControl, line.RequestDoorOpen(TrainId).Refusal,
            "cykl automatyczny nie przyjmuje poleceń ręcznych nawet od właściciela");
    }

    // --- odmowy na poziomie linii --------------------------------------------

    [TestMethod]
    public void Polecenie_drzwi_dla_skladu_prowadzonego_przez_autopilota_jest_odmowione()
    {
        var line = Line();
        line.Add(TrainId, 0L);
        line.Step();

        Assert.AreEqual(DoorRefusal.AutomaticControl, line.RequestDoorOpen(TrainId).Refusal,
            "skład pod autopilotem nie przyjmuje otwarcia od gracza");
        Assert.AreEqual(DoorRefusal.AutomaticControl, line.RequestDoorClose(TrainId).Refusal,
            "ten sam powód w obie strony");
    }

    [TestMethod]
    public void Polecenie_drzwi_POZA_peronem_jest_odmowione_z_wlasnym_powodem()
    {
        var (line, train) = Taken();

        // Skład rusza z peronu zerowego i jedzie; do następnego peronu jeszcze daleko.
        for (var i = 0; i < 600; i++)
        {
            line.Drive(TrainId, new DriverCommand(0.35, 0.0));
            line.Step();
        }

        Assert.IsFalse(train.Drive!.AtStation, "test ma mierzyć skład MIĘDZY peronami");
        Assert.AreEqual(DoorRefusal.OutsidePlatformWindow, line.RequestDoorOpen(TrainId).Refusal,
            "między peronami nie ma postoju, do którego to polecenie by należało");
        Assert.AreEqual(DoorRefusal.OutsidePlatformWindow, line.RequestDoorClose(TrainId).Refusal,
            "ten sam powód w obie strony");
    }

    [TestMethod]
    public void Otwarcie_w_ruchu_jest_odmowione_takze_przez_linie()
    {
        var (line, train) = Taken();
        DriveToPlatform(line, train);

        // Skład stoi w oknie peronu, ale maszynista dał ciąg i skład się toczy.
        var drive = train.Drive!;
        for (var i = 0; i < 2000 && drive.AtStation && drive.State.SpeedMps <= 0.0; i++)
        {
            line.Drive(TrainId, new DriverCommand(1.0, 0.0));
            line.Step();
        }

        Assert.IsTrue(drive.State.SpeedMps > 0.0, "skład miał ruszyć — bez tego test nic nie mierzy");
        Assert.IsTrue(drive.AtStation, "skład miał jeszcze stać w oknie peronu, a już je opuścił");
        Assert.AreEqual(DoorRefusal.TrainMoving, line.RequestDoorOpen(TrainId).Refusal,
            "odmowa w ruchu ma dojść także drogą przez linię, nie tylko w rdzeniu");
    }

    // --- odjazd bez obsługi ---------------------------------------------------

    [TestMethod]
    public void Maszynista_moze_odjechac_BEZ_obslugi_drzwi_a_stacja_zostaje_minieta()
    {
        var (line, train) = Taken();
        DriveToPlatform(line, train);
        var drive = train.Drive!;
        var station = drive.NextStation!.Value.ChainageM;

        for (var i = 0; i < 20_000 && drive.AtStation; i++)
        {
            line.Drive(TrainId, new DriverCommand(1.0, 0.0));
            line.Step();
        }

        Assert.IsFalse(drive.AtStation,
            "bez tego warunku skład jechałby dalej GAŁĘZIĄ POSTOJU przez resztę osi");
        Assert.IsTrue(drive.ChainageM > station + 5.0, "skład ma być za oknem peronu");
        Assert.AreEqual(DoorPhase.Closed, drive.Phase, "drzwi nie zostały ani razu otwarte");
        Assert.IsTrue(double.IsFinite(drive.Calls[^1].DepartureSeconds),
            "skład tam był i odjechał — zapis ma to odnotować");

        // ...a przejazd ma iść dalej: następna stacja jest policzona normalnie.
        var next = drive.NextStation;
        Assert.IsNotNull(next, "po minięciu stacji przejazd ma iść dalej, a nie skończyć się");
        Assert.IsTrue(next!.Value.ChainageM > station, "cel przesunął się na następną stację");
    }

    // --- ślad autopilota ------------------------------------------------------

    [TestMethod]
    public void Przejazd_bez_ani_jednego_przejecia_nie_dotyka_maszyny_recznej()
    {
        // Miara nieczuła na pochylenie i na liczby: ile postojów w tym przejeździe
        // dostało tryb inny niż automatyczny. Zero, i to jest cała teza.
        var line = Line();
        line.Add(TrainId, 0L);
        var train = line.Trains[0];
        var manual = 0;
        var stops = new HashSet<int>();
        for (var i = 0; i < 200_000 && !line.Finished; i++)
        {
            line.Step();
            if (train.Drive is { AtStation: true } drive)
            {
                stops.Add(drive.Calls.Count);
                if (drive.StopDoorControl != DoorControl.Automatic)
                {
                    manual++;
                }
            }
        }

        Assert.AreEqual(0, manual, "autopilot ani razu nie dostał drzwi ręcznych");
        Assert.AreEqual(Stations.Length - 1, stops.Count,
            "trzy postoje na czterostacyjnej osi — bez tego licznik wyżej liczyłby pustkę");
    }
}
