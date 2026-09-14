using System;
using System.Collections.Generic;
using MetroBxl.Sim.Line;
using MetroBxl.Sim.Physics;
using MetroBxl.Sim.Signalling;
using MetroBxl.Sim.Train;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace MetroBxl.Sim.Tests;

/// <summary>
/// Jeden skład, dwa źródła komend — MB-06, 14.09.2026.
///
/// <para><b>Pytanie tej klasy nie brzmi „czy da się wstrzyknąć komendę".</b> Brzmi: czy
/// wstrzyknięta komenda idzie TĄ SAMĄ drogą co komenda autopilota — przez filtr drzwi
/// i przez ochronę pociągu — i czy samo przełączenie właściciela nie rusza składu.
/// Pole „Pułapka wypisana w audycie" pozycji MB-06 nazywa to wprost: supervisor zostaje
/// OCHRONĄ, nie zastępczym wejściem gracza.</para>
///
/// <para>Oś syntetyczna jest ta sama co w <see cref="LineCoreTests"/> — 0, 600, 1400
/// i 2000 m — żeby liczby dało się czytać obok siebie.</para>
/// </summary>
[TestClass]
public sealed class ControlOwnerTests
{
    private static readonly double[] Stations = { 0.0, 600.0, 1400.0, 2000.0 };

    private static RunConditions Level() => RunConditions.Level(VehicleModel.M7, TrainLoad.Aw0);

    private static LineRunSettings Settings() => new(Units.KmhToMps(60.0), 10.0, 1.0, 5.0);

    private static LineCore Line() => LineCore.M7(
        SignallingPlanTests.SyntheticPlan(requireRoute: false, Stations),
        SignallingPlanTests.SyntheticAxis(Stations),
        Level(),
        Settings());

    /// <summary>Linia z jednym składem, przekrokowana do zadanego kroku.</summary>
    private static LineCore Do(long krok, string trainId = "A")
    {
        var line = Line();
        line.Add(trainId, 0L);
        while (line.Steps < krok)
        {
            line.Step();
        }

        return line;
    }

    // --- 1. przełączenie nie rusza składu ----------------------------------------

    [TestMethod]
    public void Przejecie_przy_NIEZEROWEJ_predkosci_nie_zmienia_polozenia_ani_predkosci()
    {
        var line = Do(1200L);
        var drive = line.Trains[0].Drive!;
        Assert.IsTrue(drive.State.SpeedMps > 1.0,
            $"wzorzec ma przejmowac skład W RUCHU, a jedzie {drive.State.SpeedMps:F3} m/s");

        var chainagePrzed = drive.ChainageM;
        var predkoscPrzed = drive.State.SpeedMps;

        line.TakeControl("A");

        Assert.AreEqual(ControlOwner.Driver, line.Trains[0].Owner,
            "TakeControl nie zmieniło właściciela sterowania");
        Assert.AreEqual(chainagePrzed, drive.ChainageM, 0.0,
            "samo przejęcie przesunęło skład — a jest przełączeniem, nie krokiem");
        Assert.AreEqual(predkoscPrzed, drive.State.SpeedMps, 0.0,
            "samo przejęcie zmieniło prędkość");
    }

    [TestMethod]
    public void Przejecie_ustawia_dzwignie_na_to_co_sklad_WLASNIE_robi()
    {
        // To jest powód, dla którego `LineDrive.LastCommand` w ogóle istnieje.
        // Przejęcie zaczynające się od zera nastawnika zmieniłoby prowadzenie
        // w następnym kroku, a wyglądałoby na „samo przełączenie".
        var line = Do(1200L);
        var autopilota = line.Trains[0].Drive!.LastCommand;

        line.TakeControl("A");

        Assert.AreEqual(autopilota, line.Trains[0].DriverCommand,
            "dźwignia po przejęciu nie stoi tam, gdzie stała komenda autopilota");

        // STRAŻNIK ODRÓŻNIAJĄCY, dopisany po audycie. Sama asercja wyżej porównuje
        // `Drive.LastCommand` z tym, co `TakeControl` z niego przepisało — czyli
        // wyrażenie z samym sobą. Rozróżnia mutację „przejęcie zeruje nastawnik"
        // WYŁĄCZNIE dlatego, że akurat na kroku 1200 autopilot trzyma pełną trakcję.
        // Gdyby trzymał wybieg, mutacja przeszłaby. Ten wiersz przybija tę przesłankę,
        // więc dzień, w którym przestanie być prawdziwa, jest widoczny.
        Assert.AreNotEqual(DriverCommand.Coast, line.Trains[0].DriverCommand!.Value,
            "wzorzec ma przejmować skład w chwili, gdy autopilot NIE jest na wybiegu — "
            + "inaczej asercja wyżej nie odróżnia przejęcia od wyzerowania nastawnika");
    }

    [TestMethod]
    public void Przejecie_i_natychmiastowe_oddanie_daje_przejazd_CO_DO_BITU_ten_sam()
    {
        // Najostrzejsza postać zdania „przełączenie nie zmienia kursu": bierzemy
        // sterowanie i oddajemy je, nie dotykając dźwigni, a potem porównujemy CAŁY
        // dalszy ślad z przejazdem, w którym nikt niczego nie brał.
        var bezPrzejecia = SladOd(1200L, _ => { });
        var zPrzejeciem = SladOd(1200L, line =>
        {
            line.TakeControl("A");
            line.ReleaseControl("A");
        });

        Assert.AreEqual(bezPrzejecia.Count, zPrzejeciem.Count,
            "ślady mają różną długość, więc porównanie punkt po punkcie nic nie znaczy");
        Assert.IsTrue(bezPrzejecia.Count > 0,
            "przejazd nie dał ani jednego punktu śladu — pętla niżej obiega zero razy "
            + "i test przechodzi, nie sprawdziwszy niczego");
        for (var i = 0; i < bezPrzejecia.Count; i++)
        {
            Assert.AreEqual(bezPrzejecia[i].ChainageM, zPrzejeciem[i].ChainageM, 0.0,
                $"ślady rozjeżdżają się na punkcie {i}");
            Assert.AreEqual(bezPrzejecia[i].SpeedMps, zPrzejeciem[i].SpeedMps, 0.0,
                $"prędkości rozjeżdżają się na punkcie {i}");
        }
    }

    private static List<LineRun.TracePoint> SladOd(long krok, Action<LineCore> co)
    {
        var line = Do(krok);
        co(line);
        var slad = new List<LineRun.TracePoint>();
        while (!line.Finished && line.Steps < LineRun.DefaultStepBudget)
        {
            line.Step((_, point) => slad.Add(point));
        }

        return slad;
    }

    // --- 2. droga komendy jest JEDNA ---------------------------------------------

    [TestMethod]
    public void Komenda_maszynisty_przechodzi_przez_OCHRONE_tak_samo_jak_autopilota()
    {
        // Pytanie pola „Weryfikacja": agresywny input nie omija ATP. Zamiast budować
        // plan z ingerencją, pytamy o rzecz ogólniejszą i mocniejszą: czy filtr
        // `Supervisor` w ogóle DOSTAJE komendę człowieka. Filtr zapamiętuje wszystko,
        // co przez niego przeszło.
        var widziane = new List<DriverCommand>();
        var line = Do(1200L);
        var drive = line.Trains[0].Drive!;
        drive.Supervisor = command =>
        {
            widziane.Add(command);
            return command;
        };

        line.TakeControl("A");
        line.Drive("A", DriverCommand.FullPower);
        line.Step();

        Assert.AreEqual(1, widziane.Count,
            "ochrona nie zobaczyła ani jednej komendy w kroku, w którym prowadził człowiek");
        Assert.AreEqual(DriverCommand.FullPower, widziane[0],
            "ochrona zobaczyła co innego niż to, co postawił maszynista — "
            + "czyli komenda człowieka idzie inną drogą niż komenda autopilota");
    }

    [TestMethod]
    public void Ochrona_moze_PRZYCIAC_komende_czlowieka_i_to_jej_wersja_jedzie()
    {
        // Druga połowa tego samego zdania: filtr nie tylko widzi, ale i rozstrzyga.
        var line = Do(1200L);
        var drive = line.Trains[0].Drive!;
        drive.Supervisor = _ => DriverCommand.FullServiceBrake;

        line.TakeControl("A");
        line.Drive("A", DriverCommand.FullPower);

        var predkoscPrzed = drive.State.SpeedMps;
        line.Step();

        Assert.IsTrue(drive.State.SpeedMps < predkoscPrzed,
            $"maszynista zamówił pełną trakcję, ochrona pełny hamulec, a skład "
            + $"przyspieszył z {predkoscPrzed:F3} do {drive.State.SpeedMps:F3} m/s — "
            + "czyli ochrona nie rozstrzyga o komendzie człowieka");
    }

    // --- 2b. GAŁĄŹ POSTOJU — dziura w ochronie, znaleziona AUDYTEM ---------------
    //
    // **Te cztery testy istnieją, bo pierwsze podejście do MB-06 wpuściło dziurę
    // w ochronie i ANI JEDEN z pozostałych testów tej klasy jej nie widział.**
    // Wszystkie wołały `TakeControl` w JEŹDZIE (kroki 60/600/1200/5400), a dziura
    // siedziała w gałęzi postoju — tam, gdzie `LineDrive.Step` wychodzi własnym
    // `return true` osiemdziesiąt wierszy przed wywołaniem `Supervisor`. Kontrola
    // negatywna KN-1 też jej nie widziała, bo mutowała gałąź, która ochronę MA.
    //
    // Na prawdziwym przejeździe L1_A ta gałąź to **25,32 % wszystkich kroków**
    // (21 780 z 86 032), a zmierzony skutek to **38,27 m staczania na −3 % przy
    // OTWARTYCH drzwiach**, do 4,44 m/s, przez 2220 kroków bez ani jednego wywołania
    // ochrony.

    /// <summary>Linia przekrokowana do pierwszego kroku, w którym trwa cykl drzwi.</summary>
    private static LineCore DoPostoju()
    {
        var line = Line();
        line.Add("A", 0L);
        while (line.Steps < 20000L)
        {
            DoorPhase? ostatnia = null;
            line.Step((_, point) => ostatnia = point.Phase);
            if (ostatnia is DoorPhase faza && faza != DoorPhase.Closed)
            {
                return line;
            }
        }

        Assert.Fail("w 20 000 krokach skład nie doszedł do ani jednego postoju");
        throw new InvalidOperationException();
    }

    [TestMethod]
    public void NA_POSTOJU_komenda_maszynisty_TEZ_przechodzi_przez_ochrone()
    {
        var line = DoPostoju();
        var widziane = new List<DriverCommand>();
        var drive = line.Trains[0].Drive!;
        drive.Supervisor = command =>
        {
            widziane.Add(command);
            return command;
        };

        line.TakeControl("A");
        line.Drive("A", DriverCommand.Coast);
        line.Step();

        Assert.AreEqual(1, widziane.Count,
            "ochrona NIE ZOBACZYŁA komendy maszynisty w kroku postoju — to jest dokładnie "
            + "ta dziura, którą zmierzył audyt: 2220 kolejnych kroków bez ani jednego "
            + "wywołania ochrony i 38,27 m staczania przy otwartych drzwiach");
    }

    [TestMethod]
    public void NA_POSTOJU_ochrona_dostaje_komende_JUZ_po_drzwiach()
    {
        // Kolejność, nie samo wywołanie: drzwi mówią, czy wolno ciągnąć, ochrona —
        // czy wolno jechać. Odwrócenie tej pary przepuściłoby nastawnik przy otwartych
        // drzwiach wszędzie tam, gdzie ochrona nie ingeruje.
        var line = DoPostoju();
        var drive = line.Trains[0].Drive!;
        DriverCommand? doOchrony = null;
        drive.Supervisor = command =>
        {
            doOchrony = command;
            return command;
        };

        line.TakeControl("A");
        line.Drive("A", DriverCommand.FullPower);
        line.Step();

        Assert.IsTrue(doOchrony.HasValue, "ochrona nie została zawołana w gałęzi postoju");
        Assert.AreEqual(0.0, doOchrony!.Value.Throttle, 1e-9,
            "ochrona zobaczyła nastawnik NIEZEROWY na postoju — dostała więc komendę "
            + "PRZED filtrem drzwi, a nie po nim");
    }

    [TestMethod]
    public void NA_POSTOJU_ochrona_ma_OSTATNIE_slowo_nad_dzwignia()
    {
        // Pytanie postawione na SKUTKU, nie na wywołaniu. `StationStop.Filter` zeruje
        // wyłącznie `Throttle` i tylko poza fazą `Closed`; `Brake` nie rusza NIGDY —
        // więc maszynista puszczający hamulec omijał ochronę zupełnie.
        var line = DoPostoju();
        var drive = line.Trains[0].Drive!;
        drive.Supervisor = _ => DriverCommand.FullServiceBrake;

        line.TakeControl("A");
        line.Drive("A", DriverCommand.Coast);

        var przed = drive.ChainageM;
        for (var i = 0; i < 600; i++)
        {
            line.Step();
        }

        Assert.AreEqual(przed, drive.ChainageM, 1e-9,
            "skład ruszył z miejsca na postoju mimo ochrony żądającej pełnego hamulca — "
            + "komenda maszynisty omija `Supervisor` w gałęzi postoju");
    }

    [TestMethod]
    public void Przejecie_skladu_PRZED_wjazdem_na_plan_jest_ODMOWA()
    {
        // Audyt zmierzył, co dawało ciche przejęcie: dźwignia dostawała
        // `default(DriverCommand)` (bo `LastCommand` to wtedy jeszcze inicjalizator
        // pola), skład stał na kilometrażu wjazdowym w nieskończoność — 0,000 m po
        // 100 s wobec 997,498 m pod autopilotem — i BLOKOWAŁ BLOK WJAZDOWY, więc
        // następny skład nie wjeżdżał wcale.
        var line = Line();
        line.Add("Z", 100_000L);
        Assert.IsNull(line.Trains[0].Drive, "wzorzec wymaga składu jeszcze POZA planem");

        var blad = Assert.ThrowsException<InvalidOperationException>(
            () => line.TakeControl("Z"),
            "przejęcie składu spoza planu przeszło po cichu");

        StringAssert.Contains(blad.Message, "nie wszedł jeszcze na plan",
            "komunikat nie mówi, dlaczego odmowa: " + blad.Message);
        Assert.AreEqual(ControlOwner.Autopilot, line.Trains[0].Owner,
            "odmowa zostawiła składowi zmienionego właściciela");
    }

    // --- 3. odmowa zamiast cichego braku skutku ----------------------------------

    [TestMethod]
    public void Komenda_dla_skladu_prowadzonego_przez_autopilota_jest_ODMOWA()
    {
        var line = Do(600L);

        var blad = Assert.ThrowsException<InvalidOperationException>(
            () => line.Drive("A", DriverCommand.FullPower),
            "komenda podana składowi prowadzonemu przez autopilota przeszła po cichu — "
            + "wołający wierzyłby, że prowadzi, a prowadziłby autopilot");

        StringAssert.Contains(blad.Message, "TakeControl",
            "komunikat nie mówi, czego brakuje: " + blad.Message);
    }

    [TestMethod]
    public void Nieznany_sklad_jest_ODMOWA_z_jego_identyfikatorem_w_tresci()
    {
        var line = Do(60L);

        foreach (var wolanie in new Action[]
        {
            () => line.TakeControl("NIE-MA"),
            () => line.ReleaseControl("NIE-MA"),
            () => line.Drive("NIE-MA", DriverCommand.Coast),
        })
        {
            var blad = Assert.ThrowsException<ArgumentException>(wolanie,
                "wołanie o nieistniejący skład nie skończyło się odmową");
            StringAssert.Contains(blad.Message, "NIE-MA",
                "komunikat nie podaje identyfikatora, o który pytano: " + blad.Message);
        }
    }

    // --- 4. drugi skład jedzie dalej ---------------------------------------------

    [TestMethod]
    public void Przejecie_JEDNEGO_skladu_nie_dotyka_drugiego()
    {
        var line = Line();
        line.Add("A", 0L);
        line.Add("B", 3600L);
        while (line.Steps < 5400L)
        {
            line.Step();
        }

        var b = line.Trains[1];
        Assert.IsNotNull(b.Drive, "wzorzec wymaga, żeby drugi skład był już na planie");
        var bPrzed = b.Drive!.ChainageM;

        // MASZYNISTA SKŁADU A JEDZIE DALEJ, a nie hamuje, i to jest poprawka mojego
        // własnego wzorca, nie kodu. Pierwsza wersja zatrzymywała A pełnym hamulcem
        // i test padał na „skład B zamarł: 46.69 m -> 46.69 m" — bo B stał wtedy
        // SŁUSZNIE: 46,69 m to granica bloku wjazdowego `P01 [0, 47)`, a przed nim
        // stał zatrzymany skład A. Zmierzone zachowanie było poprawne; pytanie było
        // źle postawione. Żeby zapytać o to, o co chodzi — czy przejęcie JEDNEGO składu
        // dotyka drugiego — maszynista musi prowadzić tak, żeby nie blokować linii.
        // 3600 kroków to TRZYDZIEŚCI sekund i ta liczba też jest policzona, nie dobrana.
        // Druga wersja tego wzorca stepowała 5 s i nadal padała — a komunikat, który
        // sobie dopisałem, powiedział dlaczego: „A na 626.54 m, autorytet B do 47.00 m
        // (OccupiedBlock)". Skład ma 94 m, więc ogon A stał wtedy na 532,54 m, czyli
        // WCIĄŻ w bloku `S01 [47, 553)`. B stał słusznie i sygnalizacja miała rację;
        // za krótka była moja pętla. B rusza, gdy czoło A minie 647 m.
        line.TakeControl("A");
        line.Drive("A", DriverCommand.FullPower);
        for (var i = 0; i < 3600; i++)
        {
            line.Step();
        }

        Assert.AreEqual(ControlOwner.Autopilot, b.Owner,
            "przejęcie składu A zmieniło właściciela składu B");
        Assert.IsNull(b.DriverCommand, "skład B dostał dźwignię, o którą nikt nie prosił");
        Assert.IsTrue(b.Drive!.ChainageM > bPrzed,
            $"skład B zamarł: {bPrzed:F2} m -> {b.Drive.ChainageM:F2} m; "
            + $"A na {line.Trains[0].Drive?.ChainageM:F2} m, "
            + $"autorytet B do {b.Authority?.EndChainageM:F2} m ({b.Authority?.Reason})");
    }

    // --- 5. dźwignia trwa do zmiany ----------------------------------------------

    [TestMethod]
    public void Dzwignia_TRWA_miedzy_krokami_i_nie_wraca_na_wybieg()
    {
        // Nastawnik jest dźwignią, nie przyciskiem. Komenda wygasająca po kroku dawałaby
        // sterowanie zależne od tego, jak często wołający zdąży ją podać.
        var line = Do(1200L);
        line.TakeControl("A");
        line.Drive("A", DriverCommand.FullServiceBrake);

        // 2400 kroków to DWADZIEŚCIA sekund, a nie dwie, i ta liczba jest policzona,
        // a nie dobrana: krok wynosi 1/120 s, prędkość w chwili przejęcia ~13 m/s,
        // a pełny hamulec służbowy to 1,1 m/s² — czyli droga do zera zajmuje niecałe
        // 12 s. Pierwsza wersja tego wzorca stepowała 240 kroków i padała na prędkości
        // 11,06 m/s; nie mówiło to nic o dźwigni, tylko o mojej arytmetyce.
        for (var i = 0; i < 2400; i++)
        {
            line.Step();
        }

        Assert.AreEqual(DriverCommand.FullServiceBrake, line.Trains[0].DriverCommand,
            "dźwignia zmieniła się sama między krokami");
        Assert.AreEqual(0.0, line.Trains[0].Drive!.State.SpeedMps, 1e-9,
            "dwadzieścia sekund pełnego hamulca służbowego nie zatrzymało składu — "
            + "dźwignia przestała obowiązywać w którymś z kroków");
    }

    [TestMethod]
    public void Oddanie_ZAPOMINA_dzwignie_zeby_nastepne_przejecie_nie_skakalo()
    {
        var line = Do(1200L);
        line.TakeControl("A");
        line.Drive("A", DriverCommand.FullServiceBrake);
        line.Step();

        line.ReleaseControl("A");

        Assert.AreEqual(ControlOwner.Autopilot, line.Trains[0].Owner,
            "ReleaseControl nie oddało sterowania autopilotowi");
        Assert.IsNull(line.Trains[0].DriverCommand,
            "dźwignia przeżyła oddanie sterowania — następne przejęcie zaczęłoby się "
            + "od komendy, której skład w tej chwili nie wykonuje");
    }

    // --- 6. identyczne komendy dają identyczny stan ------------------------------

    [TestMethod]
    public void Te_same_komendy_daja_ten_sam_stan_CO_DO_BITU()
    {
        static List<LineRun.TracePoint> Przejazd()
        {
            var line = Do(1200L);
            line.TakeControl("A");
            var slad = new List<LineRun.TracePoint>();
            for (var i = 0; i < 1800; i++)
            {
                line.Drive("A", i < 600
                    ? DriverCommand.FullPower
                    : i < 1200 ? DriverCommand.Coast : DriverCommand.FullServiceBrake);
                line.Step((_, point) => slad.Add(point));
            }

            return slad;
        }

        var pierwszy = Przejazd();
        var drugi = Przejazd();

        Assert.AreEqual(pierwszy.Count, drugi.Count,
            "dwa identycznie prowadzone przejazdy dały ślady różnej długości");
        Assert.IsTrue(pierwszy.Count > 0, "przejazd nie dał ani jednego punktu śladu");
        for (var i = 0; i < pierwszy.Count; i++)
        {
            Assert.AreEqual(pierwszy[i].ChainageM, drugi[i].ChainageM, 0.0,
                $"droga rozjechała się na punkcie {i}");
            Assert.AreEqual(pierwszy[i].SpeedMps, drugi[i].SpeedMps, 0.0,
                $"prędkość rozjechała się na punkcie {i}");
        }
    }
}
