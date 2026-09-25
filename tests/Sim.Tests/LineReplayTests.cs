using System;
using System.Collections.Generic;
using System.IO;
using MetroBxl.Sim.Line;
using MetroBxl.Sim.Physics;
using MetroBxl.Sim.Train;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace MetroBxl.Sim.Tests;

/// <summary>
/// Odtworzenie przejazdu LINII z zapisu wejść — 6.M1: zdarzenia linii w formacie
/// (wersja 3) i <see cref="LineSession"/>, wspólna droga sceny i <c>Sim.Runner</c>.
///
/// <para><b>Wzorzec jest w repozytorium</b> (<c>tests/data/m1-linia-drzwi.log</c>),
/// a nie budowany w teście, z tego samego powodu co <c>manual-keys.log</c>: plik
/// nagrany i sprawdzony tym samym kodem zgadzałby się sam ze sobą także wtedy, gdyby
/// zapis był zepsuty. Wzorzec zapisała scena (<c>--line --replay --input-log</c>),
/// więc jest w postaci kanonicznej — tej, którą pisze <see cref="InputLog.ToText"/>.</para>
/// </summary>
[TestClass]
public sealed class LineReplayTests
{
    [TestMethod]
    public void Zmiana_obserwowanego_skladu_odswieza_polecenie_bez_kroku_fizyki()
    {
        var session = Sesja();
        var second = LineSession.TrainIdAt(1);
        session.Core.Add(second, 5000L);
        for (var i = 0; i < 60; i++)
            Assert.IsTrue(session.Step(DriverKeys.None),
                "przebieg przed zmianą obserwowanego składu nie powinien się kończyć");

        var firstCommand = session.Command;
        Assert.AreNotEqual(DriverCommand.Coast, firstCommand,
            "pierwszy skład powinien już jechać, aby test wykrył stare polecenie");
        session.Execute(new InputLogEvent(60L, LineEventKind.Observe, second));
        Assert.AreEqual(second, session.Observed.Id,
            "zdarzenie obserwacji ma wybrać drugi skład");
        Assert.IsNull(session.Observed.Drive,
            "drugi skład nie powinien jeszcze być na osi");
        Assert.AreEqual(DriverCommand.Coast, session.Command,
            "skład jeszcze poza osią nie może odziedziczyć nastawnika pierwszego");
        session.Execute(new InputLogEvent(60L, LineEventKind.Observe, LineSession.CabTrainId));
        Assert.AreEqual(firstCommand, session.Command,
            "powrót ma przywrócić polecenie tego samego składu bez kroku fizyki");
    }

    [TestMethod]
    public void Przejecie_drugiego_skladu_nie_dziedziczy_nastawnika_pierwszego()
    {
        var session = Sesja();
        var secondId = LineSession.TrainIdAt(1);
        session.Core.Add(secondId, 1500L);
        for (var i = 0; i < 60; i++)
            Assert.IsTrue(session.Step(DriverKeys.None),
                "przebieg przed przejęciem nie powinien się kończyć");
        session.Execute(new InputLogEvent(60L, LineEventKind.Take, LineSession.CabTrainId));
        for (var i = 0; i < 6500; i++)
            Assert.IsTrue(session.Step(DriverKeys.Powering),
                "przebieg do drugiego składu nie powinien się kończyć");

        var second = session.Core.Trains[1];
        Assert.IsTrue(second.OnLine,
            "drugi skład musi być na osi, by porównać nastawnik");
        var before = second.Drive!.LastCommand;
        Assert.AreEqual(DriverCommand.FullServiceBrake, before,
            "drugi skład musi naprawdę hamować, gdy pierwszy ma pełen ciąg");

        session.Execute(new InputLogEvent(6560L, LineEventKind.Observe, secondId));
        session.Execute(new InputLogEvent(6560L, LineEventKind.Take, secondId));
        Assert.AreEqual(before, second.DriverCommand!.Value,
            "przejęcie nie zmienia polecenia przed kolejnym krokiem");
        Assert.IsTrue(session.Step(DriverKeys.Powering),
            "pierwszy krok po przejęciu nie powinien kończyć przebiegu");
        var after = second.DriverCommand!.Value;
        Assert.IsTrue(Math.Abs(after.Throttle - before.Throttle) <= 0.02
            && Math.Abs(after.Brake - before.Brake) <= 0.02,
            $"nastawnik skoczył z {before} do {after} w jednym kroku 120 Hz");

        session.Execute(new InputLogEvent(6561L, LineEventKind.Observe, LineSession.CabTrainId));
        var firstBefore = session.Core.Trains[0].DriverCommand!.Value;
        Assert.IsTrue(session.Step(DriverKeys.Braking),
            "krok po powrocie do pierwszego składu nie powinien kończyć przebiegu");
        var firstAfter = session.Core.Trains[0].DriverCommand!.Value;
        Assert.IsTrue(firstBefore.Throttle - firstAfter.Throttle < 0.02,
            "powrót do pierwszego składu też ma zacząć od jego własnego nastawnika");
    }

    private const double BeekkantM = 509.7;
    private const double WindowM = 5.0;

    private static string WzorzecPath => Path.Combine(
        MetroBxl.Tests.Shared.KorzenRepozytorium.Sciezka, "tests", "data", "m1-linia-drzwi.log");

    private static LineSession Sesja()
    {
        var core = LineCore.M7(
            SignallingPlanTests.PackageAPlan(),
            SignallingPlanTests.PackageAAxis(),
            new RunConditions(
                VehicleModel.M7.MassKg(TrainLoad.Aw2), 0.0,
                VehicleModel.M7.Adhesion(RailCondition.Dry), TrackEnvironment.Tunnel),
            new LineRunSettings(Units.KmhToMps(70.0), 8.0, 1.0, WindowM),
            turnbackSeconds: 0.0,
            atp: true);
        core.Add(LineSession.TrainIdAt(0), 0L);
        return new LineSession(core, new DriverNotch(0.80), FixedStep.Simulation);
    }

    /// <summary>Odtwarza zapis tak, jak robi to <c>Sim.Runner replay --line</c>.</summary>
    private static (LineSession Sesja, List<string> Telemetria, List<DoorRequestResult> Drzwi) Odtworz(
        InputLog log, Action<long, LineSession>? poKroku = null)
    {
        var sesja = Sesja();
        var telemetria = new List<string>();
        var drzwi = new List<DoorRequestResult>();
        for (var krok = 0L; krok < log.Steps; krok++)
        {
            foreach (var zdarzenie in log.EventsAt(krok))
            {
                if (sesja.Execute(zdarzenie) is DoorRequestResult odpowiedz)
                {
                    drzwi.Add(odpowiedz);
                }
            }

            Assert.IsTrue(sesja.Step(log.KeysAt(krok)), $"linia skończyła się przed krokiem {krok}");
            poKroku?.Invoke(krok, sesja);
            if (sesja.Observed.Drive is { } prowadzenie
                && (DriveTelemetry.IsSample(prowadzenie.State.Steps, DriveTelemetry.DefaultSampleEverySteps)
                    || krok + 1 == log.Steps))
            {
                telemetria.Add(sesja.TelemetryRow()!);
            }
        }

        return (sesja, telemetria, drzwi);
    }

    [TestMethod]
    public void Wzorzec_z_repozytorium_jest_w_postaci_kanonicznej_co_do_bajtu()
    {
        var tekst = File.ReadAllText(WzorzecPath);
        var log = InputLog.Parse(tekst);

        Assert.AreEqual(InputLog.VersionWithLineEvents, log.FormatVersion, "wzorzec nie jest w wersji 3");
        Assert.AreEqual(tekst, log.ToText(),
            "zapis po odczycie i ponownym zapisie różni się od wzorca — plik nie jest tym, co pisze scena");
        Assert.AreEqual(4, log.Events.Count, "wzorzec miał nieść cztery zdarzenia linii");
        CollectionAssert.AreEqual(
            new[] { LineEventKind.Take, LineEventKind.DoorOpen, LineEventKind.DoorClose, LineEventKind.Release },
            new[] { log.Events[0].Kind, log.Events[1].Kind, log.Events[2].Kind, log.Events[3].Kind },
            "kolejność zdarzeń wzorca się zmieniła");
    }

    [TestMethod]
    public void Wzorzec_przejmuje_sklad_staje_w_oknie_otwiera_i_zamyka_drzwi_i_oddaje_sterowanie()
    {
        var log = InputLog.Parse(File.ReadAllText(WzorzecPath));
        var wlascicielPoPrzejeciu = ControlOwner.Autopilot;
        var stanalW = double.NaN;
        var (sesja, _, drzwi) = Odtworz(log, (krok, s) =>
        {
            if (krok == 2880)
            {
                wlascicielPoPrzejeciu = s.Observed.Owner;
            }

            if (krok == 5639)
            {
                stanalW = s.Observed.Drive!.ChainageM;
                Assert.AreEqual(0.0, s.Observed.Drive.State.SpeedMps, 0.0,
                    "skład nie stoi przed otwarciem drzwi");
            }
        });

        Assert.AreEqual(ControlOwner.Driver, wlascicielPoPrzejeciu, "przejęcie z zapisu się nie wykonało");
        Assert.IsTrue(Math.Abs(stanalW - BeekkantM) <= WindowM,
            $"skład stanął na {stanalW:F3} m, poza oknem ±{WindowM} m od Beekkant");
        Assert.AreEqual(2, drzwi.Count, "wzorzec miał wydać dwa polecenia drzwi");
        Assert.IsTrue(drzwi[0].Ok, $"otwarcie drzwi odmówione: {drzwi[0].Reason}");
        Assert.IsTrue(drzwi[1].Ok, $"zamknięcie drzwi odmówione: {drzwi[1].Reason}");
        Assert.AreEqual(ControlOwner.Autopilot, sesja.Observed.Owner, "oddanie sterowania z zapisu się nie wykonało");
        Assert.IsTrue(sesja.Observed.Drive!.ChainageM > BeekkantM + 500.0,
            $"autopilot nie odjechał po oddaniu: {sesja.Observed.Drive.ChainageM:F3} m");
    }

    [TestMethod]
    public void Dwa_odtworzenia_tego_samego_zapisu_daja_telemetrie_identyczna_co_do_bajtu()
    {
        var log = InputLog.Parse(File.ReadAllText(WzorzecPath));
        var first = Odtworz(log);
        var second = Odtworz(log);
        var pierwsze = first.Telemetria;
        var drugie = second.Telemetria;

        Assert.IsTrue(pierwsze.Count > 100, $"telemetria ma tylko {pierwsze.Count} wierszy");
        CollectionAssert.AreEqual(pierwsze, drugie, "to samo odtworzenie dało dwa różne przejazdy");
        Assert.AreEqual(first.Sesja.StateSha256(), second.Sesja.StateSha256(),
            "pełny stan sesji po tym samym zapisie musi mieć ten sam odcisk");
    }

    [TestMethod]
    public void Odcisk_widzi_drugi_sklad_mimo_identycznej_telemetrii_kabiny()
    {
        var first = Sesja();
        var second = Sesja();
        first.Core.Add(LineSession.TrainIdAt(1), 120L);
        second.Core.Add(LineSession.TrainIdAt(1), 120L);
        for (var i = 0; i < 16000 && !second.Core.Trains[1].OnLine; i++)
        {
            Assert.IsTrue(first.Step(DriverKeys.None), "pierwsza sesja nie powinna kończyć się przed drugim wjazdem");
            Assert.IsTrue(second.Step(DriverKeys.None), "druga sesja nie powinna kończyć się przed drugim wjazdem");
        }
        Assert.IsTrue(second.Core.Trains[1].OnLine, "drugi skład musi naprawdę jechać");
        Assert.AreEqual(first.StateSha256(), second.StateSha256(),
            "ten sam początek i te same kroki muszą dać identyczny odcisk");
        second.Core.Trains[1].Drive!.DoorControl = DoorControl.Manual;
        Assert.AreEqual(first.TelemetryRow(), second.TelemetryRow(),
            "własny wiersz kabiny nie powinien widzieć trybu drzwi innego składu");
        Assert.AreNotEqual(first.StateSha256(), second.StateSha256(),
            "odcisk linii ma widzieć stan drugiego składu");
    }

    [TestMethod]
    public void Zdarzenia_linii_zmieniaja_przejazd_a_nie_tylko_plik()
    {
        // Kontrola przyrządu: bez niej zdarzenia mogłyby być czytane i ignorowane,
        // a test wyżej przeszedłby dalej, bo autopilot też dojeżdża do Beekkant.
        var log = InputLog.Parse(File.ReadAllText(WzorzecPath));
        var bezZdarzen = new InputLog(log.Steps, log.Entries, log.Resets);
        CollectionAssert.AreNotEqual(Odtworz(log).Telemetria, Odtworz(bezZdarzen).Telemetria,
            "przejazd ze zdarzeniami i bez nich jest ten sam — zdarzenia nic nie robią");
    }

    [TestMethod]
    public void Wersja_3_istnieje_tylko_dla_zapisow_ze_zdarzeniami_linii()
    {
        var zResetem = new InputLog(10, new[] { new InputLogEntry(0, DriverKeys.None) }, new[] { 5L });
        Assert.AreEqual(InputLog.VersionWithResets, zResetem.FormatVersion,
            "zapis z resetem bez zdarzeń przestał być wersją 2");
        StringAssert.Contains(zResetem.ToText(), "wersja=2\n", "zapis z resetem nie wyszedł jako wersja 2");

        var zeZdarzeniem = new InputLog(
            10, new[] { new InputLogEntry(0, DriverKeys.None) }, Array.Empty<long>(),
            new[] { new InputLogEvent(3, LineEventKind.Take, "KABINA") });
        StringAssert.Contains(zeZdarzeniem.ToText(), "\nwersja=3\n", "zapis ze zdarzeniem nie wyszedł jako wersja 3");
        StringAssert.Contains(zeZdarzeniem.ToText(), "\n3;przejmij:KABINA\n", "zapis zgubił wiersz zdarzenia");

        foreach (var (tekst, powod) in new[]
        {
            ("wersja=1\nkroki=5\nkrok;klawisze\n0;-\n2;przejmij:KABINA\n", "wersja 1 ze zdarzeniem"),
            ("wersja=2\nkroki=5\nkrok;klawisze\n0;-\n1;reset\n2;oddaj:KABINA\n", "wersja 2 ze zdarzeniem"),
            ("wersja=3\nkroki=5\nkrok;klawisze\n0;-\n", "wersja 3 bez zdarzenia"),
            ("wersja=3\nkroki=5\nkrok;klawisze\n0;-\n2;skocz:KABINA\n", "nieznany kod zdarzenia"),
        })
        {
            Assert.ThrowsException<FormatException>(() => InputLog.Parse(tekst), $"przyjęty zapis: {powod}");
        }
    }

    [TestMethod]
    public void Zdarzenia_jednego_kroku_wykonuja_sie_w_kolejnosci_zapisu_a_kroki_nie_maleja()
    {
        var log = InputLog.Parse(
            "wersja=3\nkroki=10\nkrok;klawisze\n0;-\n4;przejmij:KABINA\n4;drzwi-otworz:KABINA\n7;oddaj:KABINA\n");
        var wKroku4 = log.EventsAt(4);
        Assert.AreEqual(2, wKroku4.Count, "EventsAt zgubił zdarzenie tego samego kroku");
        Assert.AreEqual(LineEventKind.Take, wKroku4[0].Kind, "kolejność zdarzeń jednego kroku się odwróciła");
        Assert.AreEqual(LineEventKind.DoorOpen, wKroku4[1].Kind, "kolejność zdarzeń jednego kroku się odwróciła");
        Assert.AreEqual(0, log.EventsAt(5).Count, "EventsAt zwrócił zdarzenie z innego kroku");

        Assert.ThrowsException<ArgumentException>(() => new InputLog(
            10, Array.Empty<InputLogEntry>(), Array.Empty<long>(),
            new[]
            {
                new InputLogEvent(5, LineEventKind.Take, "KABINA"),
                new InputLogEvent(4, LineEventKind.Release, "KABINA"),
            }), "przyjęte zdarzenia z malejącym numerem kroku");
    }
}
