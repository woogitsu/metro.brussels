using System;
using System.Globalization;
using System.Linq;
using MetroBxl.Sim.Line;
using MetroBxl.Sim.Physics;
using MetroBxl.Sim.Signalling;
using MetroBxl.Sim.Train;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace MetroBxl.Sim.Tests;

/// <summary>
/// Ochrona pociągu jako KLASA: krzywa dopuszczalna, granica przekroczenia, strażniki
/// argumentów, blokada drzwi i KCV, oraz przekład decyzji na nastawniki
/// (<c>ProtectionDecision.Apply</c>).
///
/// <para><b>Po co osobny plik.</b> Do 05.09.2026 <c>TrainProtection</c> nie miało
/// własnego pliku testów — sprawdzały je scenariusze w
/// <c>ClassicSignallingScenarioTests</c>. Przegląd mutacyjny pokazał, co z tego wyszło:
/// klasa miała najgorsze pokrycie mutacyjne z całej piątki rdzenia, a trzy z czterech
/// ocalałych mutacji łapie test jednostkowy w trzech wierszach. Scenariusz jedzie po
/// środku dziedziny i nie zagląda w jej brzegi; tym zajmuje się ten plik.</para>
///
/// <para>Scenariusze jazdy (dwa składy na pakiecie A, hamowanie na żądanie ATP) zostają
/// tam, gdzie były — one sprawdzają, że warstwy się składają, a nie tę jedną klasę.</para>
/// </summary>
[TestClass]
public sealed class TrainProtectionTests
{
    private static readonly VehicleModel Model = VehicleModel.M7;

    private static readonly double TrainLengthM =
        VehicleRegistry.M7.RequireValue("parameters.length_m", ParameterStatus.Spec);

    private static SignallingPlan Plan(bool requireRoute = false) =>
        SignallingPlanTests.SyntheticPlan(requireRoute, 0.0, 600.0, 1400.0, 2000.0);

    private static TrainProtection Protection(SignallingPlan plan) => new(plan, Model);

    /// <summary>
    /// Skład sam na planie, daleko od końca autorytetu — czyli sytuacja, w której
    /// prędkość dopuszczalna jest DOKŁADNIE limitem planu, bit w bit.
    /// </summary>
    private static (FixedBlockSystem System, TrainProtection Atp, double Permitted) NaLimicie()
    {
        var plan = Plan();
        var system = new FixedBlockSystem(plan);
        var protection = Protection(plan);
        system.RegisterTrain("B", 200.0, TrainLengthM);

        var permitted = protection.PermittedSpeedMps(system.Authority("B").DistanceM);
        Assert.AreEqual(plan.PermittedSpeedMps, permitted, 0.0,
            "scenariusz graniczny wymaga, żeby dopuszczalna była DOKŁADNIE limitem planu, "
            + "a nie w przybliżeniu — inaczej testy niżej nie stoją na granicy");
        return (system, protection, permitted);
    }

    // --- GRANICA: prędkość dokładnie równa dopuszczalnej -------------------------------
    //
    // Mutacja TP-08 (`speedMps > permitted` → `speedMps >= permitted`) PRZEŻYŁA przegląd
    // mutacyjny na `main`: cały zestaw 376 testów przechodził po jej zastosowaniu, bo
    // żaden test nie jechał po granicy 72,00 km/h (były 70 oraz 74/76/80).
    //
    // Zmierzone 05.09.2026 sondą na pakiecie A, limit scenariusza = limit planu = 72,00 km/h:
    //
    //                         czysty kod   z mutacją TP-08
    //   kroki przejazdu       89 667       89 672
    //   kroki v == v_dop      4492         4492
    //   ostrzeżenia           0            0
    //   ingerencje służbowe   0            4492
    //
    // Czyli: ochrona hamowałaby przez 4492 kroki = 37,43 s skład, który niczego nie łamie,
    // i nie zapisałaby przy tym ANI JEDNEGO ostrzeżenia.
    //
    // Równość bitowa nie jest tu przypadkiem: `TrainController.Advance` PRZYPISUJE
    // prędkość limitowi (`speed = speedLimitMps`), a `PermittedSpeedMps` przy długim
    // autorytecie zwraca dokładnie limit planu. Skład jadący „po limicie" siedzi więc
    // na dokładnej równości przez czterdzieści sekund przejazdu, a nie mija ją raz.
    //
    // ROZSTRZYGNIĘCIE, że `>` jest poprawne, jest ze ŹRÓDEŁ, nie z tego, że tak jest dziś:
    //
    //   1. `docs/15-classic-signalling.md`, tabela „Co z tego wychodzi na pakiecie A":
    //      wiersz `72,0 km/h | 89 667 | 89 667 | 0 / 0`. Limit scenariusza równy limitowi
    //      planu daje ZERO ostrzeżeń, ZERO ingerencji i ślad identyczny co do bitu.
    //      To jest pomiar, który już stoi w dokumencie — `>=` go wywraca.
    //   2. Ten sam dokument: „ochrona ingeruje PO przekroczeniu". Prędkość równa
    //      dopuszczalnej nie jest przekroczeniem.
    //   3. `data/signalling/ground-truth.json`, `legacy_automatic_speed_protection`:
    //      „may automatically slow/intervene when the protected separation is NOT
    //      RESPECTED". Jazda po limicie limit respektuje.
    //   4. Konsekwencja w samej klasie: `DemandExceedsServiceBrake` też używa `>`,
    //      i jest to przybite testem „żądanie równe pełnemu hamulcowi jeszcze go
    //      nie przekracza". Dwie różne konwencje równości w jednym pliku byłyby usterką.
    //   5. Skutek konstrukcyjny: przy `>=` limit planu przestałby być OSIĄGALNY.
    //      Sterownik dociąga prędkość dokładnie do limitu, więc ochrona hamowałaby
    //      każdy skład, który dojechał do własnego pułapu.

    /// <summary>
    /// Prędkość DOKŁADNIE równa dopuszczalnej nie jest przekroczeniem: bez ostrzeżenia,
    /// bez ingerencji, bez żądania hamulca. To jest test, który pada po mutacji TP-08.
    /// </summary>
    [TestMethod]
    public void Predkosc_dokladnie_rowna_dopuszczalnej_nie_jest_przekroczeniem()
    {
        var (system, protection, permitted) = NaLimicie();
        var before = system.Events.Count;

        var decision = protection.Supervise(system, "B", permitted);

        Assert.AreEqual(ProtectionAction.None, decision.Action,
            "jazda dokładnie po limicie planu nie może wywołać ingerencji");
        Assert.IsFalse(decision.Overspeed, "równość nie jest przekroczeniem");
        Assert.AreEqual(0.0, decision.BrakeDemandMps2, 0.0);
        Assert.AreEqual(string.Empty, decision.Reason);
        Assert.AreEqual(before, system.Events.Count,
            "jazda po limicie nie ma prawa zostawić ani jednego zdarzenia w zapisie");
    }

    /// <summary>
    /// Druga strona tej samej granicy: JEDEN ULP powyżej dopuszczalnej to już
    /// przekroczenie. Bez tego testu „nie reaguj na równości" dałoby się spełnić
    /// ochroną, która nie reaguje nigdy.
    /// </summary>
    [TestMethod]
    public void Jeden_ulp_ponad_dopuszczalna_to_juz_przekroczenie()
    {
        var (system, protection, permitted) = NaLimicie();
        var ponad = Math.BitIncrement(permitted);
        Assert.IsTrue(ponad > permitted, "BitIncrement ma dać liczbę większą, inaczej test jest pusty");

        var decision = protection.Supervise(system, "B", ponad);

        Assert.IsTrue(decision.Overspeed, $"{ponad:R} m/s wobec {permitted:R} m/s to przekroczenie");
        Assert.AreNotEqual(ProtectionAction.None, decision.Action);
    }

    /// <summary>
    /// Ostrzeżenie i ingerencja porównują TĘ SAMĄ parę liczb i muszą to robić TYM SAMYM
    /// operatorem.
    ///
    /// <para>Stan „4492 ingerencje, 0 ostrzeżeń" z pomiaru po mutacji TP-08 jest właśnie
    /// rozjazdem tych dwóch porównań: gałąź ingerencji brała <c>&gt;=</c>, a flaga
    /// <c>Overspeed</c> została przy <c>&gt;</c>. Ochrona hamowała wtedy bez powodu
    /// zapisanego w zdarzeniach — czyli najgorszy możliwy wariant: niewidoczny.</para>
    ///
    /// <para>Niezmiennik jest jednostronny i to jest celowe: ingerencja AWARYJNA
    /// z wyczerpanego autorytetu zachodzi bez przekroczenia (skład pełznie za koniec
    /// autorytetu z dowolnie małą prędkością) i to jest poprawne.</para>
    /// </summary>
    [TestMethod]
    public void Ingerencja_sluzbowa_zawsze_jest_tez_ostrzezeniem()
    {
        var (system, protection, permitted) = NaLimicie();

        foreach (var ulamek in new[] { 0.0, 1e-9, 0.25, 0.5, 0.9, 0.99, 0.999, 1.0 })
        {
            var speed = permitted * ulamek;
            var decision = protection.Supervise(system, "B", speed);
            Assert.AreNotEqual(ProtectionAction.ServiceIntervention, decision.Action,
                $"{Units.MpsToKmh(speed):F4} km/h nie przekracza {Units.MpsToKmh(permitted):F4} km/h");
        }

        foreach (var ulamek in new[] { 1.0000001, 1.001, 1.05, 1.2 })
        {
            var speed = permitted * ulamek;
            var decision = protection.Supervise(system, "B", speed);
            Assert.IsTrue(decision.Overspeed,
                $"{Units.MpsToKmh(speed):F4} km/h ponad {Units.MpsToKmh(permitted):F4} km/h musi być ostrzeżeniem");
            Assert.AreEqual(ProtectionAction.ServiceIntervention, decision.Action,
                $"{Units.MpsToKmh(speed):F4} km/h: krzywa jeszcze wyrabia, więc ingerencja jest służbowa");
        }
    }

    /// <summary>
    /// Ta sama granica, ale PRZEJECHANA, a nie policzona w jednym wywołaniu: pakiet A,
    /// limit scenariusza równy limitowi planu (72,00 km/h).
    ///
    /// <para>Test jednostkowy wyżej pyta ochronę raz. Ten jedzie 89 667 kroków i liczy,
    /// ile z nich siedzi na DOKŁADNEJ równości — bo gdyby ich było zero, „0 ingerencji"
    /// nic by nie znaczyło. Zmierzone: 4492 kroki, czyli 37,43 s przejazdu.</para>
    ///
    /// <para>To jest wiersz `72,0 km/h` z tabeli w `docs/15-classic-signalling.md`,
    /// dotąd zapisany i niesprawdzony: istniejący test „pod limitem planu" jedzie
    /// 70,0 km/h, czyli obok granicy.</para>
    /// </summary>
    [TestMethod]
    public void Na_pakiecie_A_jazda_dokladnie_po_limicie_planu_nie_budzi_ochrony()
    {
        var line = LineCore.M7(
            SignallingPlanTests.PackageAPlan(),
            SignallingPlanTests.PackageAAxis(),
            new RunConditions(
                Model.MassKg(TrainLoad.Aw2), 0.0,
                Model.Adhesion(RailCondition.Dry), TrackEnvironment.Tunnel),
            new LineRunSettings(Units.KmhToMps(72.0), 8.0, 1.0, 5.0),
            turnbackSeconds: 0.0,
            atp: true);

        Assert.AreEqual(Units.KmhToMps(72.0), line.Signalling.Plan.PermittedSpeedMps, 0.0,
            "ten test ma sens tylko wtedy, gdy limit scenariusza jest DOKŁADNIE limitem planu");

        line.Add("A", 0L);
        var naGranicy = 0L;
        var ponadGranica = 0L;
        while (!line.Finished && line.Steps < LineRun.DefaultStepBudget)
        {
            var przed = line.Trains[0].Drive?.State.SpeedMps;
            line.Step();
            if (przed is double speed && line.Trains[0].Protection is ProtectionDecision decision)
            {
                if (speed == decision.PermittedSpeedMps)
                {
                    naGranicy++;
                }
                else if (speed > decision.PermittedSpeedMps)
                {
                    ponadGranica++;
                }
            }
        }

        Assert.IsTrue(line.Finished, "przejazd po limicie planu nie dojechał");
        Assert.AreEqual(4492L, naGranicy, string.Create(CultureInfo.InvariantCulture,
            $"zmierzone 4492 kroki z prędkością DOKŁADNIE równą dopuszczalnej; "
            + $"gdyby ich było zero, zera niżej nic by nie znaczyły"));
        Assert.AreEqual(0L, ponadGranica, "przy limicie scenariusza równym limitowi planu nic go nie przekracza");
        Assert.AreEqual(0L, line.ProtectionWarnings, "ani jednego ostrzeżenia");
        Assert.AreEqual(0L, line.ServiceInterventions, "ani jednej ingerencji służbowej");
        Assert.AreEqual(0L, line.EmergencyInterventions, "ani jednej ingerencji awaryjnej");
        Assert.AreEqual(0.0, line.MaxBrakeDemandMps2, 0.0, "ochrona nie zażądała ani grama hamulca");
        Assert.AreEqual(89667L, line.Steps, "zmierzony przejazd z tabeli w docs/15: 89 667 kroków");
    }

    // --- krzywa dopuszczalna ----------------------------------------------------------

    /// <summary>
    /// Zasada 4 z T-313: ATP nie ma własnej fizyki. Prędkość dopuszczalna wyznaczona
    /// przez ochronę musi zgadzać się z drogą hamowania solvera z T-311 co do metra,
    /// a nie „mniej więcej".
    /// </summary>
    [TestMethod]
    public void Predkosc_dopuszczalna_jest_odwrotnoscia_krzywej_z_T_311()
    {
        var plan = Plan();
        var protection = Protection(plan);
        var solver = new BrakingPointSolver(Model);

        foreach (var distance in new[] { 10.0, 50.0, 120.0, 300.0, 700.0 })
        {
            var permitted = protection.PermittedSpeedMps(distance);
            if (permitted >= plan.PermittedSpeedMps)
            {
                Assert.IsTrue(
                    solver.Solve(plan.PermittedSpeedMps, 0.0, Model.DesignServiceBrakeMps2).DistanceM <= distance,
                    $"{distance:F0} m: limit planu ma się zmieścić w authority");
                continue;
            }

            var need = solver.Solve(permitted, 0.0, Model.DesignServiceBrakeMps2).DistanceM;
            Assert.IsTrue(need <= distance + 1e-6, $"{distance:F0} m: droga {need:F6} m nie mieści się w authority");

            var faster = solver.Solve(permitted + 0.01, 0.0, Model.DesignServiceBrakeMps2).DistanceM;
            Assert.IsTrue(faster > distance, $"{distance:F0} m: o 0,01 m/s szybciej wciąż by się mieściło");
        }
    }

    [TestMethod]
    public void Predkosc_dopuszczalna_spada_do_zera_na_koncu_authority()
    {
        var protection = Protection(Plan());

        Assert.AreEqual(0.0, protection.PermittedSpeedMps(0.0), 0.0);
        Assert.IsTrue(protection.PermittedSpeedMps(1.0) > 0.0);
        Assert.IsTrue(protection.PermittedSpeedMps(1.0) < protection.PermittedSpeedMps(100.0));
    }

    /// <summary>
    /// Strażnik <c>speedMps &lt;= 0.0</c> w <c>BrakingDistanceM</c> nie jest ozdobą:
    /// solver z T-311 ODMAWIA zerowej prędkości początkowej („to nie jest hamowanie").
    ///
    /// <para>Zmierzone przeglądem mutacyjnym: zdjęcie strażnika sprawia, że publiczna
    /// metoda <c>BrakingDistanceM(0.0)</c> RZUCA zamiast zwrócić zero — i cały zestaw
    /// tego nie widział, bo nikt jej nie wołał zerem. Negatywna kontrola stoi w tym
    /// samym teście: gdyby solver zero przyjmował, strażnik byłby martwy naprawdę.</para>
    /// </summary>
    [TestMethod]
    public void Droga_hamowania_z_postoju_jest_zerem_a_nie_wyjatkiem()
    {
        var protection = Protection(Plan());

        Assert.AreEqual(0.0, protection.BrakingDistanceM(0.0), 0.0,
            "skład stojący ma zerową drogę hamowania");

        Assert.ThrowsException<ArgumentOutOfRangeException>(
            () => new BrakingPointSolver(Model).Solve(0.0, 0.0, Model.DesignServiceBrakeMps2),
            "kontrola negatywna: solver zera NIE przyjmuje, więc strażnik w BrakingDistanceM "
            + "jest jedynym powodem, dla którego asercja wyżej przechodzi");

        Assert.IsTrue(protection.BrakingDistanceM(1e-9) >= 0.0, "dodatnia prędkość idzie do solvera");
    }

    [TestMethod]
    public void Predkosc_dopuszczalna_odmawia_odleglosci_ujemnej_i_nieskonczonej()
    {
        var protection = Protection(Plan());
        foreach (var bad in new[] { -1.0, double.NaN, double.PositiveInfinity, double.NegativeInfinity })
        {
            Assert.ThrowsException<ArgumentOutOfRangeException>(
                () => protection.PermittedSpeedMps(bad), $"{bad}");
        }
    }

    [TestMethod]
    public void Nadzor_odmawia_predkosci_ujemnej_i_nieskonczonej()
    {
        var plan = Plan();
        var system = new FixedBlockSystem(plan);
        var protection = Protection(plan);
        system.RegisterTrain("B", 200.0, TrainLengthM);

        foreach (var bad in new[] { -1e-9, -5.0, double.NaN, double.PositiveInfinity, double.NegativeInfinity })
        {
            Assert.ThrowsException<ArgumentOutOfRangeException>(
                () => protection.Supervise(system, "B", bad), $"{bad}");
        }
    }

    // --- strażnicy konstruktora -------------------------------------------------------

    /// <summary>
    /// Hamulec awaryjny SŁABSZY od służbowego, <c>NaN</c> i nieskończoność są odmową
    /// przy budowie, a nie zagadką w raporcie.
    ///
    /// <para>Zmierzone przeglądem mutacyjnym: zdjęcie tych strażników przechodziło
    /// przez cały zestaw. Ochrona z awaryjnym słabszym od służbowego eskalowałaby
    /// „w dół" — sięgałaby po hamulec, który hamuje SŁABIEJ od tego, który właśnie
    /// uznała za niewystarczający.</para>
    /// </summary>
    [TestMethod]
    public void Konstruktor_odmawia_hamulcow_bez_sensu()
    {
        var plan = Plan();
        var solver = new BrakingPointSolver(Model);

        foreach (var bad in new[] { 0.0, -1.1, double.NaN, double.PositiveInfinity })
        {
            Assert.ThrowsException<ArgumentOutOfRangeException>(
                () => new TrainProtection(plan, solver, bad, 1.3), $"hamulec służbowy {bad}");
        }

        foreach (var bad in new[] { 1.099, 0.0, -1.3, double.NaN, double.PositiveInfinity })
        {
            Assert.ThrowsException<ArgumentOutOfRangeException>(
                () => new TrainProtection(plan, solver, 1.1, bad), $"hamulec awaryjny {bad}");
        }

        Assert.ThrowsException<ArgumentNullException>(() => new TrainProtection(null!, solver, 1.1, 1.3));
        Assert.ThrowsException<ArgumentNullException>(() => new TrainProtection(plan, null!, 1.1, 1.3));
        Assert.ThrowsException<ArgumentNullException>(() => new TrainProtection(plan, (VehicleModel)null!));
    }

    /// <summary>
    /// Awaryjny RÓWNY służbowemu przechodzi — warunek jest <c>&lt;</c>, nie
    /// <c>&lt;=</c>, i to jest ta sama konwencja równości, co przy przekroczeniu
    /// prędkości: równość nie jest przekroczeniem. Bez tej asercji test wyżej
    /// przechodziłby też dla ochrony, która odmawia wszystkiego.
    /// </summary>
    [TestMethod]
    public void Hamulec_awaryjny_rowny_sluzbowemu_jest_dopuszczalny()
    {
        var protection = new TrainProtection(Plan(), new BrakingPointSolver(Model), 1.1, 1.1);

        Assert.AreEqual(1.1, protection.ServiceBrakeMps2, 0.0);
        Assert.AreEqual(1.1, protection.EmergencyBrakeMps2, 0.0);
    }

    // --- ingerencja -------------------------------------------------------------------

    /// <summary>Scenariusz „overspeed ponad curve → intervention".</summary>
    [TestMethod]
    public void Predkosc_ponad_krzywa_wywoluje_ostrzezenie_i_ingerencje()
    {
        var plan = Plan();
        var system = new FixedBlockSystem(plan);
        var protection = Protection(plan);
        system.RegisterTrain("A", 1400.0, TrainLengthM);
        system.RegisterTrain("B", 200.0, TrainLengthM);

        var authority = system.Authority("B");
        var permitted = protection.PermittedSpeedMps(authority.DistanceM);
        var before = system.Events.Count;

        var calm = protection.Supervise(system, "B", permitted * 0.5);
        Assert.AreEqual(ProtectionAction.None, calm.Action);
        Assert.IsFalse(calm.Overspeed);

        var decision = protection.Supervise(system, "B", permitted * 1.05);
        Assert.IsTrue(decision.Overspeed);
        Assert.AreEqual(ProtectionAction.ServiceIntervention, decision.Action);
        Assert.IsTrue(decision.BrakeDemandMps2 > 0.0);
        Assert.IsTrue(decision.BrakeDemandMps2 <= Model.DesignServiceBrakeMps2);

        var kinds = system.Events.Skip(before).Select(e => e.Kind).ToList();
        CollectionAssert.Contains(kinds, SignallingEventKind.OverspeedWarning);
        CollectionAssert.Contains(kinds, SignallingEventKind.OverspeedIntervention);
    }

    /// <summary>
    /// Próg ingerencji awaryjnej nie jest przyjętym marginesem — jest policzony:
    /// wypada tam, gdzie hamulec służbowy przestaje wystarczać na pozostałą drogę.
    /// </summary>
    [TestMethod]
    public void Gdy_hamulec_sluzbowy_nie_wystarcza_ingerencja_jest_awaryjna()
    {
        var plan = Plan();
        var system = new FixedBlockSystem(plan);
        var protection = Protection(plan);
        system.RegisterTrain("A", 1400.0, TrainLengthM);
        system.RegisterTrain("B", 600.0, TrainLengthM);

        var authority = system.Authority("B");
        Assert.IsTrue(authority.DistanceM < 50.0, $"do końca authority zostało {authority.DistanceM:F2} m");

        var decision = protection.Supervise(system, "B", Units.KmhToMps(60.0));
        Assert.AreEqual(ProtectionAction.EmergencyIntervention, decision.Action);
        Assert.AreEqual(Model.DesignEmergencyBrakeMps2, decision.BrakeDemandMps2, 0.0);
        Assert.IsTrue(
            system.Events.Any(e => e.Kind == SignallingEventKind.EmergencyIntervention),
            "ingerencja awaryjna musi zostawić ślad w zapisie");
    }

    /// <summary>
    /// Sam próg służbowy → awaryjny, a nie tylko jego okolice.
    ///
    /// <para>Zmierzone 02.09.2026 mutacją: podmiana warunku
    /// <c>need &lt;= _serviceBrakeMps2</c> na <c>need &lt;= _emergencyBrakeMps2</c> —
    /// czyli zgoda na ingerencję służbową tam, gdzie służbowy nie wystarcza —
    /// przechodziła przez cały zestaw (Passed: 255). Istniejące testy używają
    /// prędkości tak wysokich, że potrzebne opóźnienie przekracza także hamulec
    /// awaryjny; obie strony podmienionego warunku dają wtedy ten sam wynik.</para>
    ///
    /// <para>Ten test kalibruje się na rzeczywistej odległości authority: liczy
    /// potrzebne opóźnienie solverem z T-311, a potem buduje ochronę tak, żeby ta
    /// liczba wypadła DOKŁADNIE między hamulcem służbowym a awaryjnym. To jedyne
    /// miejsce, w którym oba warunki się rozchodzą.</para>
    /// </summary>
    [TestMethod]
    public void Prog_miedzy_sluzbowym_a_awaryjnym_wypada_tam_gdzie_sluzbowy_przestaje_wystarczac()
    {
        var plan = Plan();
        var system = new FixedBlockSystem(plan);
        system.RegisterTrain("A", 1400.0, TrainLengthM);
        system.RegisterTrain("B", 200.0, TrainLengthM);

        var solver = new BrakingPointSolver(Model);
        var distance = system.Authority("B").DistanceM;
        var speed = Units.KmhToMps(40.0);
        var need = solver.RequiredDeceleration(speed, 0.0, distance).DecelerationMps2;
        Assert.IsTrue(need > 0.0, $"potrzebne opóźnienie {need:F4} m/s² nie nadaje się na próg");

        // Hamulec służbowy poniżej potrzeby, awaryjny powyżej — czyli dokładnie
        // sytuacja „służbowy nie wystarcza, ale awaryjny tak".
        var tooWeak = new TrainProtection(plan, solver, need * 0.5, need * 2.0);
        var escalated = tooWeak.Supervise(system, "B", speed);
        Assert.AreEqual(ProtectionAction.EmergencyIntervention, escalated.Action,
            $"potrzeba {need:F4} m/s², służbowy {need * 0.5:F4} m/s²");
        StringAssert.Contains(escalated.Reason, "service-brake-insufficient");
        Assert.AreEqual(need * 2.0, escalated.BrakeDemandMps2, 0.0);

        // Ta sama sytuacja z hamulcem służbowym mocniejszym od potrzeby: bez eskalacji.
        // Nie żądam tu ingerencji służbowej, bo mocniejszy hamulec podnosi też samą
        // krzywą — skład może się zmieścić pod nią i nie być w ogóle w nadmiernej
        // prędkości. Istotne jest, że hamulec awaryjny NIE wchodzi.
        var strongEnough = new TrainProtection(plan, solver, need * 2.0, need * 4.0);
        var served = strongEnough.Supervise(system, "B", speed);
        Assert.AreNotEqual(ProtectionAction.EmergencyIntervention, served.Action,
            $"potrzeba {need:F4} m/s², służbowy {need * 2.0:F4} m/s²");
    }

    [TestMethod]
    public void Wyczerpane_authority_przy_ruchu_to_zawsze_ingerencja_awaryjna()
    {
        var plan = Plan();
        var system = new FixedBlockSystem(plan);
        var protection = Protection(plan);
        system.RegisterTrain("A", 1400.0, TrainLengthM);
        system.RegisterTrain("B", 200.0, TrainLengthM);
        system.MoveTrain("B", system.Authority("B").EndChainageM);

        Assert.AreEqual(0.0, system.Authority("B").DistanceM, 0.0);
        var decision = protection.Supervise(system, "B", 1.0);

        Assert.AreEqual(ProtectionAction.EmergencyIntervention, decision.Action);
        StringAssert.Contains(decision.Reason, "authority-exhausted");
    }

    /// <summary>
    /// Skład STOJĄCY nie dostaje ingerencji, nawet gdy autorytet jest wyczerpany —
    /// prędkość dopuszczalna jest wtedy zerem, więc bez progu postoju każde zero
    /// byłoby „przekroczeniem" o zero.
    /// </summary>
    [TestMethod]
    public void Sklad_stojacy_nie_dostaje_ingerencji_nawet_bez_authority()
    {
        var plan = Plan();
        var system = new FixedBlockSystem(plan);
        var protection = Protection(plan);
        system.RegisterTrain("A", 1400.0, TrainLengthM);
        system.RegisterTrain("B", 200.0, TrainLengthM);
        system.MoveTrain("B", system.Authority("B").EndChainageM);
        Assert.AreEqual(0.0, system.Authority("B").DistanceM, 0.0);

        var decision = protection.Supervise(system, "B", 0.0);

        Assert.AreEqual(ProtectionAction.None, decision.Action);
        Assert.IsFalse(decision.Overspeed);
        Assert.AreEqual(0.0, decision.PermittedSpeedMps, 0.0,
            "przy zerowym autorytecie dopuszczalna jest zerem — i mimo to postój jest w porządku");
    }

    // --- drzwi i KCV ------------------------------------------------------------------

    [TestMethod]
    public void Drzwi_zwalniaja_sie_tylko_na_postoju_w_bloku_peronowym()
    {
        var plan = Plan();
        var system = new FixedBlockSystem(plan);
        var protection = Protection(plan);
        system.RegisterTrain("A", 600.0, TrainLengthM);

        Assert.IsTrue(protection.DoorRelease(system, "A", 0.0, kcvAvailable: false).Released,
            "skład stoi w bloku peronowym P02");

        var moving = protection.DoorRelease(system, "A", 3.0, kcvAvailable: false);
        Assert.IsFalse(moving.Released);
        Assert.AreEqual("moving", moving.Reason);

        system.MoveTrain("A", 800.0);
        var offPlatform = protection.DoorRelease(system, "A", 0.0, kcvAvailable: false);
        Assert.IsFalse(offPlatform.Released);
        StringAssert.Contains(offPlatform.Reason, "not-at-platform");

        var kinds = system.Events.Select(e => e.Kind).ToList();
        CollectionAssert.Contains(kinds, SignallingEventKind.DoorRelease);
        CollectionAssert.Contains(kinds, SignallingEventKind.DoorInhibit);
    }

    /// <summary>
    /// KCV jako interfejs, nie jako urządzenie: w wariancie linii 2/6 brak potwierdzenia
    /// z KCV blokuje zwolnienie drzwi. Telegramów, balis ani protokołu tu nie ma i nie
    /// będzie — <c>ground-truth.json</c> wymienia je jako nieznane.
    /// </summary>
    [TestMethod]
    public void W_wariancie_KCV_brak_potwierdzenia_blokuje_drzwi()
    {
        var axis = SignallingPlanTests.SyntheticAxis(0.0, 600.0, 1400.0);
        var plan = SignallingPlan.FromAxis(
            axis, TrainLengthM, Units.KmhToMps(72.0), 0.0, ProtectionVariant.LegacyWithKcv, requireRoute: false);
        var system = new FixedBlockSystem(plan);
        var protection = new TrainProtection(plan, Model);
        system.RegisterTrain("A", 600.0, TrainLengthM);

        protection.RequireKcv();
        Assert.IsFalse(protection.DoorRelease(system, "A", 0.0, kcvAvailable: false).Released);
        Assert.AreEqual("kcv-unavailable", protection.DoorRelease(system, "A", 0.0, kcvAvailable: false).Reason);
        Assert.IsTrue(protection.DoorRelease(system, "A", 0.0, kcvAvailable: true).Released);
    }

    [TestMethod]
    public void Lista_funkcji_KCV_jest_dokladnie_ta_ktora_podaje_STIB() =>
        CollectionAssert.AreEqual(
            new[]
            {
                KcvFunction.SecureAutomaticDoorOpening,
                KcvFunction.StationAnnouncements,
                KcvFunction.WheelLubrication,
            },
            TrainProtection.SourceBackedKcvFunctions.ToArray());

    // --- decyzja na nastawnikach ------------------------------------------------------
    //
    // Decyzja właściciela z 04.09.2026: „ostrzeżenie, potem hamulec służbowy".
    // Do tego dnia `Supervise` liczyło decyzję, a nikt jej nie stosował — HUD pokazywał
    // liczbę i tyle. Poniżej testy tej jednej rzeczy, która zamienia liczbę
    // w zachowanie: `ProtectionDecision.Apply`.

    private static ProtectionDecision Decision(ProtectionAction action, double demand) =>
        new(0.0, 100.0, action, demand, action != ProtectionAction.None, "test");

    [TestMethod]
    public void Bez_ingerencji_polecenie_maszynisty_przechodzi_bez_zmiany()
    {
        // Samo przekroczenie prędkości jest OSTRZEŻENIEM, nie hamowaniem: dopóki krzywa
        // wyrabia, ochrona nie ma prawa odebrać jazdy. Gdyby `None` też hamowało,
        // przejazd z limitem planu przestałby być tym zweryfikowanym przejazdem.
        var wanted = new DriverCommand(0.65, 0.0);
        var passed = Decision(ProtectionAction.None, 0.0).Apply(wanted, 1.1);

        Assert.AreEqual(wanted.Throttle, passed.Throttle, 0.0, "trakcja ma przejść nietknięta");
        Assert.AreEqual(wanted.Brake, passed.Brake, 0.0, "hamulec ma przejść nietknięty");
    }

    [TestMethod]
    public void Ingerencja_sluzbowa_zeruje_trakcje_i_podaje_zadany_hamulec()
    {
        // 0,55 m/s² przy hamulcu służbowym 1,10 m/s² to dokładnie połowa nastawnika.
        // Liczba jest wybrana tak, żeby dała się sprawdzić w głowie, a nie żeby zgodzić
        // się z implementacją.
        var passed = Decision(ProtectionAction.ServiceIntervention, 0.55)
            .Apply(new DriverCommand(1.0, 0.0), 1.1);

        Assert.AreEqual(0.0, passed.Throttle, 0.0, "trakcja przy ingerencji musi zniknąć");
        Assert.AreEqual(0.5, passed.Brake, 1e-12, "0,55 / 1,10 = połowa nastawnika hamulca");
    }

    [TestMethod]
    public void Ochrona_nie_odpuszcza_hamulca_ktory_maszynista_juz_podal()
    {
        // Ingerencja idzie TYLKO w stronę mocniejszego hamowania. Gdyby ochrona
        // wstawiała swój ułamek zamiast brać większy z dwóch, maszynista hamujący
        // pełnym hamulcem dostałby przy ostrzeżeniu hamulec SŁABSZY — czyli ochrona
        // przyspieszałaby skład, którego ma pilnować.
        var passed = Decision(ProtectionAction.ServiceIntervention, 0.55)
            .Apply(new DriverCommand(0.0, 1.0), 1.1);

        Assert.AreEqual(1.0, passed.Brake, 0.0,
            "pełny hamulec maszynisty ma zostać pełnym, a nie spaść do połowy");
    }

    [TestMethod]
    public void Ingerencja_awaryjna_daje_pelny_hamulec_niezaleznie_od_zadania()
    {
        foreach (var demand in new[] { 0.0, 0.4, 1.3, 9.9 })
        {
            var passed = Decision(ProtectionAction.EmergencyIntervention, demand)
                .Apply(new DriverCommand(1.0, 0.0), 1.1);
            Assert.AreEqual(0.0, passed.Throttle, 0.0, $"żądanie {demand:F1} m/s²");
            Assert.AreEqual(1.0, passed.Brake, 0.0, $"żądanie {demand:F1} m/s²");
        }
    }

    [TestMethod]
    public void Zadanie_ponad_hamulec_sluzbowy_jest_widoczne_a_nie_zamiecione()
    {
        // `BrakeCommandFraction` obcina ułamek do 1,0, więc żądanie 2,00 m/s² i żądanie
        // 1,10 m/s² dają ten sam nastawnik. Obcięcie jest poprawne — polecenie kończy
        // się na pełnym hamulcu — ale gdyby to była jedyna informacja, przekroczenie
        // stałoby się niewidoczne.
        var ledwo = Decision(ProtectionAction.ServiceIntervention, 1.1);
        var ponad = Decision(ProtectionAction.ServiceIntervention, 2.0);

        Assert.AreEqual(1.0, ledwo.BrakeCommandFraction(1.1), 1e-12);
        Assert.AreEqual(1.0, ponad.BrakeCommandFraction(1.1), 1e-12);
        Assert.IsFalse(ledwo.DemandExceedsServiceBrake(1.1),
            "żądanie równe pełnemu hamulcowi jeszcze go nie przekracza");
        Assert.IsTrue(ponad.DemandExceedsServiceBrake(1.1),
            "żądanie 2,00 m/s² przy hamulcu 1,10 m/s² przekracza go i musi to powiedzieć");
    }

    [TestMethod]
    public void Apply_i_DemandExceeds_odmawiaja_niedodatniego_hamulca()
    {
        var decision = Decision(ProtectionAction.ServiceIntervention, 0.55);
        foreach (var bad in new[] { 0.0, -1.1, double.NaN, double.PositiveInfinity })
        {
            Assert.ThrowsException<ArgumentOutOfRangeException>(
                () => decision.DemandExceedsServiceBrake(bad), $"{bad}");
            Assert.ThrowsException<ArgumentOutOfRangeException>(
                () => decision.Apply(new DriverCommand(1.0, 0.0), bad), $"{bad}");
        }
    }
}
