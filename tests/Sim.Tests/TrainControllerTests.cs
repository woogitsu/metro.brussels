using System;
using System.Globalization;
using MetroBxl.Sim.Physics;
using MetroBxl.Sim.Train;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace MetroBxl.Sim.Tests;

/// <summary>
/// Testy tego, co <see cref="TrainController"/> **dokłada** ponad rdzeń z T-310.
///
/// Reszta — siła pociągowa, opory Davisa, składowa pochylenia, masa efektywna —
/// jest już pokryta testami parytetu z <c>tools/physics/reference.py</c> i nie ma
/// sensu sprawdzać jej drugi raz. Nowe są dokładnie trzy rzeczy i to one mają tu
/// swoje testy:
///
/// <list type="number">
/// <item>trakcja częściowa (nastawnik jako mnożnik siły),</item>
/// <item>hamulec jako polecenie, z ograniczeniem zrywu w obie strony,</item>
/// <item>brak obcięcia przyspieszenia od dołu — kontroler musi umieć zwalniać.</item>
/// </list>
///
/// Do tego obcięcia brzegowe (limit prędkości, zero) i walidacja argumentów, czyli
/// wyjątki, których bez testu nikt nigdy nie wywoła.
/// </summary>
[TestClass]
public sealed class TrainControllerTests
{
    private static readonly VehicleModel Model = VehicleModel.M7;
    private static readonly FixedStep Step = FixedStep.Simulation;
    private static readonly double TargetMps = Units.KmhToMps(Model.DesignMaxSpeedKmh);

    private static RunConditions Level(TrainLoad load) => RunConditions.Level(Model, load);

    private static TrainController NewController() => new(Model);

    // --- 1. parytet z T-310 przy pełnym nastawniku --------------------------------

    /// <summary>
    /// Przy pełnym nastawniku i odpuszczonym hamulcu kontroler musi być rdzeniem
    /// z T-310, a nie jego przybliżeniem: ta sama liczba kroków i droga zgodna
    /// **co do bitu**. Mnożenie przez 1,0 i odejmowanie 0,0 są dokładne, więc każdy
    /// inny wynik oznacza, że kolejność działań się rozjechała.
    /// </summary>
    [DataTestMethod]
    [DataRow(TrainLoad.Aw0)]
    [DataRow(TrainLoad.Aw2)]
    public void Pelny_nastawnik_odtwarza_rozruch_z_T310_co_do_bitu(TrainLoad load)
    {
        var conditions = Level(load);
        var reference = new AccelerationRun(Model).ToSpeed(conditions, Model.DesignMaxSpeedKmh, Step);

        var state = RunToTarget(NewController(), conditions, DriverCommand.FullPower);

        Assert.AreEqual(reference.Steps, state.Steps, "liczba kroków");
        Assert.AreEqual(
            BitConverter.DoubleToInt64Bits(reference.DistanceM),
            BitConverter.DoubleToInt64Bits(state.DistanceM),
            "droga musi się zgadzać co do bitu");
    }

    // --- 2. trakcja częściowa ------------------------------------------------------

    /// <summary>
    /// Połowa nastawnika to dokładnie połowa siły pociągowej. Mnożenie przez 0,5 jest
    /// w arytmetyce binarnej dokładne, więc porównanie jest ścisłe, a nie z tolerancją.
    /// </summary>
    [TestMethod]
    public void Polowa_nastawnika_daje_dokladnie_polowe_sily_pociagowej()
    {
        var conditions = Level(TrainLoad.Aw2);
        var controller = NewController();
        var start = new DriveState(0, 10.0, 0.0, 0.0);

        controller.Advance(start, conditions, DriverCommand.FullPower, TargetMps, Step, out var full);
        controller.Advance(start, conditions, new DriverCommand(0.5, 0.0), TargetMps, Step, out var half);

        Assert.AreEqual(
            BitConverter.DoubleToInt64Bits(0.5 * full.TractionN),
            BitConverter.DoubleToInt64Bits(half.TractionN));
        Assert.IsTrue(full.TractionN > 0.0, "przy 10 m/s siła pociągowa musi być dodatnia");
    }

    /// <summary>Zerowy nastawnik to zerowa siła pociągowa, a nie „prawie zero".</summary>
    [TestMethod]
    public void Zerowy_nastawnik_daje_zerowa_sile_pociagowa()
    {
        var controller = NewController();
        var start = new DriveState(0, 15.0, 0.0, 0.0);

        controller.Advance(start, Level(TrainLoad.Aw2), DriverCommand.Coast, TargetMps, Step, out var forces);

        Assert.AreEqual(0.0, forces.TractionN);
    }

    /// <summary>
    /// Hamulec ma pierwszeństwo nad nastawnikiem. Stanu „ciągnij i hamuj naraz"
    /// maszynista na M7 nie osiąga i model nie ma powodu go dopuszczać.
    /// </summary>
    [TestMethod]
    public void Hamulec_zeruje_trakcje_nawet_przy_pelnym_nastawniku()
    {
        var controller = NewController();
        var start = new DriveState(0, 15.0, 0.0, 0.0);

        controller.Advance(start, Level(TrainLoad.Aw2), new DriverCommand(1.0, 0.2), TargetMps, Step, out var forces);

        Assert.AreEqual(0.0, forces.TractionN);
    }

    // --- 3. brak obcięcia przyspieszenia od dołu ----------------------------------

    /// <summary>
    /// **Kontrola różnicy wobec <see cref="TrainDynamics.Advance"/>.** Tamten krok
    /// obcina przyspieszenie od dołu do zera, bo przebieg rozruchowy z definicji
    /// przyspiesza. Prowadzony skład musi umieć zwalniać na wybiegu — ten test
    /// wywróciłby się, gdyby ktoś kiedyś dołożył <c>Math.Max(0, ...)</c> z powrotem.
    /// </summary>
    [TestMethod]
    public void Wybieg_zwalnia_sklad_oporami_bez_obciecia_przyspieszenia()
    {
        var conditions = Level(TrainLoad.Aw2);
        var controller = NewController();
        var start = new DriveState(0, TargetMps, 0.0, 0.0);

        var after = controller.Advance(start, conditions, DriverCommand.Coast, TargetMps, Step, out var forces);

        Assert.IsTrue(forces.AccelerationMps2 < 0.0,
            $"na wybiegu przyspieszenie musi być ujemne, jest {forces.AccelerationMps2.ToString("R", CultureInfo.InvariantCulture)}");
        Assert.IsTrue(after.SpeedMps < start.SpeedMps, "prędkość na wybiegu musi maleć");

        // Opóźnienie wybiegu to dokładnie opory podzielone przez masę efektywną:
        // nic więcej w tym kroku nie działa (trakcja 0, hamulec 0, pochylenie 0).
        var expected = -forces.ResistanceN / controller.Dynamics.EffectiveMassKg(conditions.MassKg);
        Assert.AreEqual(
            BitConverter.DoubleToInt64Bits(expected),
            BitConverter.DoubleToInt64Bits(forces.AccelerationMps2));
    }

    // --- 4. hamulec i ograniczenie zrywu ------------------------------------------

    /// <summary>
    /// Narastanie hamowania nie może przeskoczyć więcej niż <c>zryw · dt</c> w kroku.
    /// Bez tego model dawałby nieskończony zryw, którego <c>docs/02-simulation.md</c>
    /// jawnie zabrania.
    /// </summary>
    [TestMethod]
    public void Zryw_ogranicza_narastanie_hamowania_w_kazdym_kroku()
    {
        var controller = NewController();
        var conditions = Level(TrainLoad.Aw2);
        var maximumChange = controller.JerkMps3 * Step.Seconds;

        var state = new DriveState(0, TargetMps, 0.0, 0.0);
        for (var i = 0; i < 400; i++)
        {
            var before = state.BrakeRateMps2;
            state = controller.Advance(state, conditions, DriverCommand.FullServiceBrake, TargetMps, Step, out _);
            var change = state.BrakeRateMps2 - before;

            Assert.IsTrue(change >= 0.0, $"krok {i}: hamowanie nie może maleć przy pełnym hamulcu");
            Assert.IsTrue(change <= maximumChange + 1e-15,
                $"krok {i}: skok {change} przekracza zryw·dt = {maximumChange}");
        }
    }

    /// <summary>
    /// Po dojściu do zadanego opóźnienia narastanie się zatrzymuje **dokładnie** na
    /// zadanej wartości — to jest gałąź <c>return target</c> w rampie. Bez niej
    /// opóźnienie przeskakiwałoby wartość zadaną i oscylowało wokół niej.
    /// </summary>
    [TestMethod]
    public void Po_dojsciu_do_zadanego_opoznienia_hamowanie_stoi_na_tej_wartosci()
    {
        var controller = NewController();
        var conditions = Level(TrainLoad.Aw2);

        // Czas dojścia to zryw -> opóźnienie: 1,10 / 0,75 = 1,467 s, czyli 177 kroków.
        var state = new DriveState(0, TargetMps, 0.0, 0.0);
        for (var i = 0; i < 300; i++)
        {
            state = controller.Advance(state, conditions, DriverCommand.FullServiceBrake, TargetMps, Step, out _);
        }

        Assert.AreEqual(controller.ServiceBrakeMps2, state.BrakeRateMps2, 0.0);

        var next = controller.Advance(state, conditions, DriverCommand.FullServiceBrake, TargetMps, Step, out _);
        Assert.AreEqual(controller.ServiceBrakeMps2, next.BrakeRateMps2, 0.0);
    }

    /// <summary>
    /// Zdejmowanie hamulca jest ograniczone zrywem tak samo jak narastanie.
    /// Hamulec, który znika w jednym kroku, jest tym samym błędem co hamulec,
    /// który w jednym kroku pojawia się na maksimum.
    /// </summary>
    [TestMethod]
    public void Zryw_ogranicza_takze_zdejmowanie_hamulca()
    {
        var controller = NewController();
        var conditions = Level(TrainLoad.Aw2);
        var maximumChange = controller.JerkMps3 * Step.Seconds;

        var state = new DriveState(0, TargetMps, 0.0, controller.ServiceBrakeMps2);
        var released = controller.Advance(state, conditions, DriverCommand.Coast, TargetMps, Step, out _);

        Assert.AreEqual(controller.ServiceBrakeMps2 - maximumChange, released.BrakeRateMps2, 1e-15);
        Assert.IsTrue(released.BrakeRateMps2 > 0.0, "hamulec nie znika w jednym kroku");

        // ...a po dojściu do zera zostaje na zerze, a nie schodzi poniżej.
        for (var i = 0; i < 300; i++)
        {
            released = controller.Advance(released, conditions, DriverCommand.Coast, TargetMps, Step, out _);
        }

        Assert.AreEqual(0.0, released.BrakeRateMps2, 0.0);
    }

    /// <summary>Połowa hamulca to połowa zadanego opóźnienia, nie połowa czegoś innego.</summary>
    [TestMethod]
    public void Polowa_hamulca_zmierza_do_polowy_opoznienia_sluzbowego()
    {
        var controller = NewController();
        var conditions = Level(TrainLoad.Aw2);

        var state = new DriveState(0, TargetMps, 0.0, 0.0);
        for (var i = 0; i < 300; i++)
        {
            state = controller.Advance(state, conditions, new DriverCommand(0.0, 0.5), TargetMps, Step, out _);
        }

        Assert.AreEqual(0.5 * controller.ServiceBrakeMps2, state.BrakeRateMps2, 0.0);
    }

    // --- 5. obcięcia brzegowe -----------------------------------------------------

    /// <summary>Prędkość nigdy nie przekracza ograniczenia, także przy pełnej trakcji.</summary>
    [TestMethod]
    public void Predkosc_jest_obcinana_do_ograniczenia()
    {
        var controller = NewController();
        var conditions = Level(TrainLoad.Aw0);
        var limit = Units.KmhToMps(40.0);

        var state = DriveState.AtRest;
        for (var i = 0; i < 30 * FixedStep.SimulationHertz; i++)
        {
            state = controller.Advance(state, conditions, DriverCommand.FullPower, limit, Step, out _);
            Assert.IsTrue(state.SpeedMps <= limit, $"krok {i}: {state.SpeedMps} > {limit}");
        }

        Assert.AreEqual(limit, state.SpeedMps, 0.0,
            "po 30 s pełnej trakcji skład ma siedzieć dokładnie na ograniczeniu, a nie obok niego");
    }

    /// <summary>
    /// Skład stojący pod hamulcem i na wybiegu nie odtacza się w tył. Model nie ma
    /// hamulca postojowego (to T-311), więc jedyne, co go trzyma, to obcięcie
    /// prędkości do zera — i musi być pewne.
    /// </summary>
    [TestMethod]
    public void Sklad_nie_odtacza_sie_w_tyl()
    {
        var controller = NewController();
        var conditions = Level(TrainLoad.Aw2);

        foreach (var command in new[] { DriverCommand.Coast, DriverCommand.FullServiceBrake })
        {
            var state = DriveState.AtRest;
            for (var i = 0; i < 600; i++)
            {
                state = controller.Advance(state, conditions, command, TargetMps, Step, out _);
                Assert.AreEqual(0.0, state.SpeedMps, 0.0, $"{command}: krok {i}");
                Assert.AreEqual(0.0, state.DistanceM, 0.0, $"{command}: krok {i}");
            }
        }
    }

    /// <summary>To samo pod górę: brak trakcji na pochyleniu nie cofa składu.</summary>
    [TestMethod]
    public void Wybieg_pod_gore_nie_cofa_stojacego_skladu()
    {
        var controller = NewController();
        var conditions = Level(TrainLoad.Aw2).WithGrade(4.0);

        var state = DriveState.AtRest;
        for (var i = 0; i < 600; i++)
        {
            state = controller.Advance(state, conditions, DriverCommand.Coast, TargetMps, Step, out _);
        }

        Assert.AreEqual(0.0, state.SpeedMps, 0.0);
        Assert.AreEqual(0.0, state.DistanceM, 0.0);
    }

    // --- 6. bilans energii hamowania ----------------------------------------------

    /// <summary>
    /// Druga, niezależna droga do tej samej liczby (<c>docs/06-worked-example.md</c>).
    ///
    /// Dla hamowania na poziomie, bez trakcji, równanie kroku brzmi
    /// <c>m_ef · a = −F_oporu − m_ef · b</c>. Po przemnożeniu przez drogę i zsumowaniu
    /// po całym przebiegu musi się domknąć bilans:
    ///
    /// <c>½ · m_ef · v₀² = ∫F_oporu ds + m_ef · ∫b ds</c>
    ///
    /// Reszta niedomknięcia to człon dyskretyzacji: krok liczy siły od prędkości
    /// z **początku** kroku, a drogę od prędkości z **końca**, więc różnica jest
    /// rzędu <c>½ · m_ef · Σ(Δv)²</c> i ten człon jest w bilansie wypisany osobno,
    /// zamiast być rozmazany w tolerancji.
    /// </summary>
    [TestMethod]
    public void Bilans_energii_hamowania_domyka_sie_do_precyzji_double()
    {
        var controller = NewController();
        var conditions = Level(TrainLoad.Aw2);
        var effectiveMass = controller.Dynamics.EffectiveMassKg(conditions.MassKg);

        var state = new DriveState(0, TargetMps, 0.0, 0.0);
        var resistanceWork = 0.0;
        var brakeWork = 0.0;
        var discretization = 0.0;

        while (state.SpeedMps > 0.0 && state.Steps < 120 * FixedStep.SimulationHertz)
        {
            var before = state;
            state = controller.Advance(before, conditions, DriverCommand.FullServiceBrake, TargetMps, Step, out var forces);
            var distance = state.DistanceM - before.DistanceM;

            resistanceWork += forces.ResistanceN * distance;
            brakeWork += effectiveMass * state.BrakeRateMps2 * distance;

            var deltaSpeed = before.SpeedMps - state.SpeedMps;
            discretization += 0.5 * effectiveMass * deltaSpeed * deltaSpeed;
        }

        var kinetic = 0.5 * effectiveMass * TargetMps * TargetMps;
        var residual = kinetic - resistanceWork - brakeWork - discretization;

        Console.WriteLine(string.Create(
            CultureInfo.InvariantCulture,
            $"[BILANS HAMOWANIA] E_kin = {kinetic:F3} J, opory = {resistanceWork:F3} J, " +
            $"hamulec = {brakeWork:F3} J, dyskretyzacja = {discretization:F3} J, " +
            $"reszta = {residual:E3} J, względnie = {Math.Abs(residual) / kinetic:E3}"));

        // Zmierzone: reszta względna 7,155·10⁻¹⁶, czyli precyzja double.
        // Próg 1e-12 zostawia cztery rzędy zapasu i nadal łapie każdy realny rozjazd.
        Assert.IsTrue(Math.Abs(residual) / kinetic < 1e-12,
            $"bilans nie domyka się: reszta względna {Math.Abs(residual) / kinetic}");
        Assert.IsTrue(resistanceWork > 0.0, "praca oporów musi być dodatnia");
    }

    /// <summary>
    /// Skąd bierze się krótsza droga hamowania kontrolera niż
    /// <see cref="ServiceBrakingRun"/> — **policzone, nie zadeklarowane**.
    ///
    /// Model kinematyczny z T-310 nie zna oporów ruchu. Kontroler dokłada je do
    /// zadanego opóźnienia, więc na tej samej prędkości początkowej staje bliżej.
    /// Skrócenie musi się równać pracy oporów podzielonej przez siłę hamowania:
    /// <c>Δs ≈ (∫F_oporu ds) / (m_ef · b)</c>, gdzie <c>b</c> to opóźnienie na
    /// płaskiej części profilu. Człon narastania hamulca (pierwsze 1,47 s) psuje
    /// tę równość o ułamek metra: zmierzona różnica to **0,019 m na 6,757 m
    /// skrócenia**, czyli 0,3 %. Tolerancja 0,05 m jest z tego pomiaru, nie z sufitu.
    /// </summary>
    [TestMethod]
    public void Skrocenie_drogi_hamowania_rowna_sie_pracy_oporow()
    {
        var controller = NewController();
        var conditions = Level(TrainLoad.Aw2);
        var effectiveMass = controller.Dynamics.EffectiveMassKg(conditions.MassKg);

        var kinematic = new ServiceBrakingRun(Model).ToStop(Model.DesignMaxSpeedKmh, Step);

        var state = new DriveState(0, TargetMps, 0.0, 0.0);
        var resistanceWork = 0.0;
        while (state.SpeedMps > 0.0 && state.Steps < 120 * FixedStep.SimulationHertz)
        {
            var before = state;
            state = controller.Advance(before, conditions, DriverCommand.FullServiceBrake, TargetMps, Step, out var forces);
            resistanceWork += forces.ResistanceN * (state.DistanceM - before.DistanceM);
        }

        var measured = kinematic.DistanceM - state.DistanceM;
        var predicted = resistanceWork / (effectiveMass * controller.ServiceBrakeMps2);

        Console.WriteLine(string.Create(
            CultureInfo.InvariantCulture,
            $"[SKRÓCENIE] kinematyczne {kinematic.DistanceM:F3} m, kontroler {state.DistanceM:F3} m, " +
            $"zmierzone skrócenie {measured:F3} m, z pracy oporów {predicted:F3} m, " +
            $"różnica {Math.Abs(measured - predicted):F3} m"));

        Assert.IsTrue(measured > 0.0, "z oporami skład musi stanąć bliżej, nie dalej");
        Assert.AreEqual(predicted, measured, 0.05,
            "skrócenie drogi hamowania nie zgadza się z pracą oporów");
    }

    // --- 7. walidacja argumentów --------------------------------------------------

    /// <summary>Konstruktor odrzuca opóźnienie i zryw, które nie są dodatnie i skończone.</summary>
    [DataTestMethod]
    [DataRow(0.0, 0.75)]
    [DataRow(-1.0, 0.75)]
    [DataRow(double.NaN, 0.75)]
    [DataRow(double.PositiveInfinity, 0.75)]
    [DataRow(1.1, 0.0)]
    [DataRow(1.1, -0.75)]
    [DataRow(1.1, double.NaN)]
    public void Konstruktor_odrzuca_niedodatnie_parametry_hamulca(double brake, double jerk)
    {
        Assert.ThrowsException<ArgumentOutOfRangeException>(
            () => new TrainController(TrainDynamics.M7, brake, jerk));
    }

    /// <summary>Brak dynamiki to nie jest „domyślna dynamika".</summary>
    [TestMethod]
    public void Konstruktor_odrzuca_brak_dynamiki_i_brak_modelu()
    {
        Assert.ThrowsException<ArgumentNullException>(() => new TrainController((TrainDynamics)null!, 1.1, 0.75));
        Assert.ThrowsException<ArgumentNullException>(() => new TrainController((VehicleModel)null!));
    }

    /// <summary>Ograniczenie prędkości musi być nieujemne i skończone.</summary>
    [DataTestMethod]
    [DataRow(-1.0)]
    [DataRow(double.NaN)]
    [DataRow(double.PositiveInfinity)]
    public void Advance_odrzuca_bledne_ograniczenie_predkosci(double limit)
    {
        var controller = NewController();
        Assert.ThrowsException<ArgumentOutOfRangeException>(
            () => controller.Advance(DriveState.AtRest, Level(TrainLoad.Aw2), DriverCommand.Coast, limit, Step, out _));
    }

    /// <summary>Brak warunków przebiegu i niezainicjowany krok są odrzucane, nie zgadywane.</summary>
    [TestMethod]
    public void Advance_odrzuca_brak_warunkow_i_zerowy_krok()
    {
        var controller = NewController();

        Assert.ThrowsException<ArgumentNullException>(
            () => controller.Advance(DriveState.AtRest, null!, DriverCommand.Coast, TargetMps, Step, out _));
        Assert.ThrowsException<ArgumentException>(
            () => controller.Advance(DriveState.AtRest, Level(TrainLoad.Aw2), DriverCommand.Coast, TargetMps, default, out _));
    }

    /// <summary>Nastawnik poza zakresem jest obcinany, a NaN odrzucany.</summary>
    [TestMethod]
    public void Polecenie_maszynisty_jest_obcinane_a_NaN_odrzucany()
    {
        var clamped = new DriverCommand(3.0, -2.0).Clamped();
        Assert.AreEqual(1.0, clamped.Throttle, 0.0);
        Assert.AreEqual(0.0, clamped.Brake, 0.0);

        Assert.ThrowsException<ArgumentOutOfRangeException>(() => new DriverCommand(double.NaN, 0.0).Clamped());
        Assert.ThrowsException<ArgumentOutOfRangeException>(() => new DriverCommand(0.0, double.NaN).Clamped());

        Assert.AreEqual(0.0, new DriverCommand(1.0, 0.3).EffectiveThrottle, 0.0);
        Assert.AreEqual(1.0, new DriverCommand(1.0, 0.0).EffectiveThrottle, 0.0);
    }

    private static DriveState RunToTarget(TrainController controller, RunConditions conditions, DriverCommand command)
    {
        var state = DriveState.AtRest;
        while (state.SpeedMps < TargetMps && state.Steps < 300 * FixedStep.SimulationHertz)
        {
            state = controller.Advance(state, conditions, command, TargetMps, Step, out _);
        }

        return state;
    }
}
