using System;
using System.Globalization;
using System.Text.RegularExpressions;
using MetroBxl.Game;
using MetroBxl.Sim.Line;
using MetroBxl.Sim.Physics;
using MetroBxl.Sim.Signalling;
using MetroBxl.Sim.Train;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace MetroBxl.Game.Tests;

/// <summary>
/// Nagłówek <c>[PRZEJAZD]</c> — liczby w napisie mają być liczbami przebiegu.
///
/// <para><b>Usterka, którą ten plik przybija.</b> Zmierzone 04.09.2026:
/// <c>--line --limit-kmh=70</c> dawało nagłówek
/// <c>[PRZEJAZD] tryb=line ... limit=80.0 km/h</c>, a ten sam przebieg meldował
/// <c>[STACJA] Beekkant: ... szczyt 70.00 km/h</c> na dziewięciu z jedenastu odcinków.
/// Nagłówek brał limit z <see cref="DriveScenario"/>, czyli z rejestru pojazdu — 80 km/h
/// jest prędkością KONSTRUKCYJNĄ M7 (<c>design_model</c>), nie ograniczeniem na torze
/// i nie argumentem, którym jedzie rdzeń.</para>
///
/// <para><b>Czego te testy pilnują.</b> Nie tego, że pole <c>limit=</c> istnieje —
/// tego, że liczba w nim <b>równa się limitowi z argumentu</b>, którym prowadzi rdzeń.
/// Każdy z nich pada, gdy źródło liczby wróci do scenariusza: 80,0 ≠ 70,0. Limit
/// wyciągany jest z gotowego napisu wyrażeniem regularnym, bo to jest dokładnie to,
/// co czyta człowiek i bramka CI — asercja na osobno policzonej wartości sprawdzałaby
/// drugą kopię, czyli tę samą usterkę.</para>
/// </summary>
[TestClass]
public sealed class RunHeaderTests
{
    private const int UnknownArgument = 8;
    private const int BadArgumentValue = 9;

    /// <summary>Limit planu sygnalizacji pakietu A — trzecia, ODRÓŻNIALNA liczba.</summary>
    private const double PlanLimitKmh = 72.0;

    /// <summary>Stacje osi syntetycznej; te same co w <c>LineCoreTests</c> rdzenia.</summary>
    private static readonly double[] StationChainagesM = { 0.0, 600.0, 1400.0, 2000.0 };

    private static RunPlan Parse(params string[] arguments)
        => RunPlan.Parse(arguments, UnknownArgument, BadArgumentValue);

    private static DriveScenario Scenario() => DriveScenario.PackageAFirstRun(VehicleModel.M7);

    /// <summary>Warunki przebiegu — te same, które scena podaje rdzeniowi.</summary>
    private static RunConditions Conditions() => new(
        VehicleModel.M7.MassKg(TrainLoad.Aw2),
        0.0,
        VehicleModel.M7.Adhesion(RailCondition.Dry),
        TrackEnvironment.Tunnel);

    /// <summary>Prosta oś z czterema stacjami. Z zawsze 0 — profil pionowy jest not_modelled.</summary>
    private static TrackAxis Axis() => TrackAxis.FromJson("""
        {"id":"TEST","crs":"EPSG:31370",
         "points":[[0,0,0],[700,0,0],[1500,0,0],[2100,0,0]],
         "stations":[{"name":"S0","chainage_m":0.0,"stop_id":"P0"},
                     {"name":"S1","chainage_m":600.0,"stop_id":"P1"},
                     {"name":"S2","chainage_m":1400.0,"stop_id":"P2"},
                     {"name":"S3","chainage_m":2000.0,"stop_id":"P3"}]}
        """);

    /// <summary>
    /// Nastawy przejazdu z limitem <b>z argumentu</b>. Ta droga — argument, potem
    /// <see cref="LineRunSettings"/>, potem prowadzenie — jest tą, którą naprawdę idzie
    /// scena w <c>BuildSimulation</c>.
    /// </summary>
    private static LineRunSettings Settings(double limitKmh) => new(
        Units.KmhToMps(limitKmh),
        DesignAssumptions.PassengerExchangeSeconds,
        DesignAssumptions.LineBrakeUsageFraction,
        DesignAssumptions.StationStopWindowM);

    private static LineDrive Drive(double limitKmh, TrackAxis axis) => new(
        axis,
        Conditions(),
        Settings(limitKmh),
        new TrainController(VehicleModel.M7),
        new BrakingPointSolver(VehicleModel.M7),
        FixedStep.Simulation);

    private static LineCore Core(double limitKmh, TrackAxis axis) => LineCore.M7(
        SignallingPlan.FromAxis(
            axis,
            VehicleRegistry.M7.RequireValue("parameters.length_m", ParameterStatus.Spec),
            Units.KmhToMps(PlanLimitKmh),
            0.0,
            ProtectionVariant.LegacyFixedBlock,
            requireRoute: false),
        axis,
        Conditions(),
        Settings(limitKmh));

    /// <summary>Liczba z pola <c>limit=</c> gotowego nagłówka, w km/h.</summary>
    private static double LimitFromHeader(string header)
    {
        var match = Regex.Match(header, @"limit=(-?[0-9]+(?:\.[0-9]+)?) km/h");
        Assert.IsTrue(match.Success, $"nagłówek nie ma pola limit=: {header}");
        return double.Parse(match.Groups[1].Value, CultureInfo.InvariantCulture);
    }

    private static double NumberFromHeader(string header, string field, string unit)
    {
        var match = Regex.Match(header, $@"{field}=(-?[0-9]+(?:\.[0-9]+)?) {unit}");
        Assert.IsTrue(match.Success, $"nagłówek nie ma pola {field}=: {header}");
        return double.Parse(match.Groups[1].Value, CultureInfo.InvariantCulture);
    }

    // --- USTERKA: nagłówek kłamał o limicie ---------------------------------------

    /// <summary>
    /// Przejazd bez sygnalizacji: nagłówek pokazuje limit, którym jedzie
    /// <see cref="LineDrive"/> — czyli ten z <c>--limit-kmh</c>, nie ten ze scenariusza.
    /// </summary>
    [TestMethod]
    public void LimitWNaglowkuJestLimitemZArgumentu()
    {
        var plan = Parse("--line", "--limit-kmh=70");
        Assert.IsTrue(plan.IsValid, plan.Error);
        Assert.AreEqual(70.0, plan.LimitKmh, 1e-12);

        var scenario = Scenario();
        Assert.AreEqual(
            VehicleModel.M7.DesignMaxSpeedKmh, Units.MpsToKmh(scenario.SpeedLimitMps), 1e-9,
            "scenariusz podaje prędkość konstrukcyjną M7; gdyby podawał 70, ten test "
            + "przestałby odróżniać źródła i przechodziłby także z usterką");

        var header = RunHeader.Line(
            plan, ViewKind.Cab, scenario, FixedStep.Simulation, Conditions(),
            core: null, line: Drive(plan.LimitKmh, Axis()));

        // 0,05 km/h to połowa ostatniej wypisywanej cyfry (format F1), a nie zapas
        // na rozjazd: nagłówek pokazuje jedno miejsce po przecinku.
        Assert.AreEqual(plan.LimitKmh, LimitFromHeader(header), 0.05, header);
    }

    /// <summary>
    /// Przejazd z sygnalizacją. Nagłówek leci PRZED pierwszym krokiem, a prowadzenie
    /// (<see cref="LineTrain.Drive"/>) powstaje leniwie — w chwili wypisania jest jeszcze
    /// nullem. Tą dziurą limit wracał do scenariusza; liczba musi wyjść z
    /// <see cref="LineCore"/>, i to ani ze scenariusza (80), ani z planu (72).
    /// </summary>
    [TestMethod]
    public void LimitWNaglowkuIdzieZLiniiTakzePrzedPierwszymKrokiem()
    {
        var plan = Parse("--line", "--limit-kmh=70", "--signalling=nieistotna-sciezka.json");
        Assert.IsTrue(plan.IsValid, plan.Error);

        var axis = Axis();
        var core = Core(plan.LimitKmh, axis);
        var train = core.Add("KABINA", 0L);
        Assert.IsNull(train.Drive, "prowadzenie ma powstać dopiero w pierwszym kroku");

        var header = RunHeader.Line(
            plan, ViewKind.Cab, Scenario(), FixedStep.Simulation, Conditions(),
            core, line: null);
        var limit = LimitFromHeader(header);

        Assert.AreEqual(plan.LimitKmh, limit, 0.05, header);
        Assert.AreNotEqual(PlanLimitKmh, limit, 0.05,
            "limit planu sygnalizacji jest osobną liczbą i ma swój własny wiersz");
    }

    /// <summary>
    /// Kilka wartości, bo jedna przechodzi także przy zaszytej liczbie. 58,68 km/h to
    /// dolne ograniczenie z rozkładu T-401, 45,5 — wartość spoza wszystkich progów.
    /// </summary>
    [TestMethod]
    public void KazdyLimitZArgumentuWychodziWNaglowku()
    {
        foreach (var limitKmh in new[] { 70.0, 58.68, 45.5, 80.0 })
        {
            var plan = Parse(
                "--line",
                string.Create(CultureInfo.InvariantCulture, $"--limit-kmh={limitKmh}"));
            Assert.IsTrue(plan.IsValid, plan.Error);

            var header = RunHeader.Line(
                plan, ViewKind.Cab, Scenario(), FixedStep.Simulation, Conditions(),
                core: null, line: Drive(plan.LimitKmh, Axis()));

            Assert.AreEqual(limitKmh, LimitFromHeader(header), 0.05, header);
        }
    }

    /// <summary>
    /// Cichy odwrót na scenariusz w trybie linii jest ZABRONIONY. Gdyby scena przestała
    /// podawać prowadzenie, nagłówek ma się wywrócić, a nie wypisać 80 km/h — bo napis
    /// 80,0 przy przejeździe 70 km/h przeszedł wszystkie bramki tego repozytorium.
    /// </summary>
    [TestMethod]
    public void PrzejazdLiniaBezProwadzeniaNieDostajeLimituZeScenariusza()
    {
        var plan = Parse("--line", "--limit-kmh=70");
        Assert.IsTrue(plan.IsValid, plan.Error);

        Assert.ThrowsException<ArgumentException>(() => RunHeader.Line(
            plan, ViewKind.Cab, Scenario(), FixedStep.Simulation, Conditions(),
            core: null, line: null));
    }

    // --- tryb ręczny i skryptowy: limit ze scenariusza JEST tym, którym się jedzie ---

    /// <summary>
    /// Bez <c>--line</c> limit ze scenariusza jest limitem prowadzenia — <c>--limit-kmh</c>
    /// się z tymi trybami nie łączy (<see cref="RunPlan"/> odmawia), a <c>StepOnce</c>
    /// podaje kontrolerowi to samo wyrażenie, które czyta nagłówek.
    /// </summary>
    [TestMethod]
    public void BezLiniiNaglowekPokazujeLimitScenariusza()
    {
        var plan = Parse();
        Assert.IsTrue(plan.IsValid, plan.Error);
        Assert.IsFalse(plan.LineMode);

        var scenario = Scenario();
        var conditions = Conditions();
        var header = RunHeader.Line(
            plan, ViewKind.Cab, scenario, FixedStep.Simulation, conditions,
            core: null, line: null);

        Assert.AreEqual(Units.MpsToKmh(scenario.SpeedLimitMps), LimitFromHeader(header), 0.05, header);
        Assert.AreEqual(
            RunHeader.SpeedLimitMps(plan.LineMode, scenario, null, null),
            scenario.SpeedLimitMps,
            1e-12,
            "fizyka trybu ręcznego i nagłówek mają czytać JEDNO wyrażenie");
    }

    // --- pozostałe liczby nagłówka ------------------------------------------------

    /// <summary>
    /// Krok wypisywany jest z <see cref="FixedStep"/> PODANEGO rdzeniowi, a nie ze stałej
    /// <c>FixedStep.SimulationHertz</c>. Ta sama rodzina co limit: stała w napisie zgadza
    /// się z przebiegiem tylko dopóty, dopóki nikt nie zmieni kroku.
    /// </summary>
    [TestMethod]
    public void KrokWNaglowkuJestKrokiemPodanymRdzeniowi()
    {
        var plan = Parse();
        var pinned = RunHeader.Line(
            plan, ViewKind.Cab, Scenario(), FixedStep.Simulation, Conditions(), null, null);
        StringAssert.Contains(pinned, "krok=1/120 s", pinned);

        var slower = RunHeader.Line(
            plan, ViewKind.Cab, Scenario(), FixedStep.FromHertz(60), Conditions(), null, null);
        StringAssert.Contains(slower, "krok=1/60 s", slower);
    }

    /// <summary>Masa idzie z warunków podanych rdzeniowi, nie z rejestru obok nich.</summary>
    [TestMethod]
    public void MasaWNaglowkuJestMasaPodanaRdzeniowi()
    {
        var plan = Parse();
        var conditions = new RunConditions(
            123456.0, 0.0, VehicleModel.M7.Adhesion(RailCondition.Dry), TrackEnvironment.Tunnel);

        var header = RunHeader.Line(
            plan, ViewKind.Cab, Scenario(), FixedStep.Simulation, conditions, null, null);

        Assert.AreEqual(123456.0, NumberFromHeader(header, "masa", "kg"), 0.5, header);
    }

    /// <summary>Tryb i widok są tymi, z którymi przebieg wystartował.</summary>
    [TestMethod]
    public void TrybIWidokSaTymiZWierszaPolecen()
    {
        var plan = Parse("--line", "--limit-kmh=70", "--view=outside");
        Assert.IsTrue(plan.IsValid, plan.Error);

        var header = RunHeader.Line(
            plan, plan.View, Scenario(), FixedStep.Simulation, Conditions(),
            core: null, line: Drive(plan.LimitKmh, Axis()));

        StringAssert.StartsWith(header, "[PRZEJAZD] tryb=line widok=Outside", header);
    }
}
