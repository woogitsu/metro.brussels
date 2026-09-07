using System;
using System.Globalization;
using System.IO;
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

    /// <summary>Plan sygnalizacji osi testowej, z limitem <see cref="PlanLimitKmh"/>.</summary>
    private static SignallingPlan Plan(TrackAxis axis) => SignallingPlan.FromAxis(
        axis,
        VehicleRegistry.M7.RequireValue("parameters.length_m", ParameterStatus.Spec),
        Units.KmhToMps(PlanLimitKmh),
        0.0,
        ProtectionVariant.LegacyFixedBlock,
        requireRoute: false);

    private static LineCore Core(double limitKmh, TrackAxis axis) => LineCore.M7(
        Plan(axis),
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
            core: null, line: Drive(plan.LimitKmh, Axis()), manualPlan: null);

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
            core, line: null, manualPlan: null);
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
                core: null, line: Drive(plan.LimitKmh, Axis()), manualPlan: null);

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
            core: null, line: null, manualPlan: null));
    }

    // --- tryb skryptowy: limit ze scenariusza JEST tym, którym się jedzie ------------

    /// <summary>
    /// Przebieg SKRYPTOWY (<c>--telemetry</c>, <c>--shot</c>) jedzie limitem ze
    /// scenariusza, bo tym limitem jedzie <c>ScenarioDrive</c> w rdzeniu, a telemetria
    /// sceny jest z rdzeniem porównywana CO DO BITU. Zmiana z 05.09.2026 dotyczy
    /// wyłącznie trybu ręcznego i ten test jest tym, co trzyma ją po swojej stronie.
    /// </summary>
    [TestMethod]
    public void PrzebiegSkryptowyNadalPokazujeLimitScenariusza()
    {
        var plan = Parse("--telemetry=przebieg.csv");
        Assert.IsTrue(plan.IsValid, plan.Error);
        Assert.IsTrue(plan.ScriptedMode);
        Assert.IsFalse(plan.LineMode);

        var scenario = Scenario();
        var header = RunHeader.Line(
            plan, ViewKind.Cab, scenario, FixedStep.Simulation, Conditions(),
            core: null, line: null, manualPlan: null);

        Assert.AreEqual(Units.MpsToKmh(scenario.SpeedLimitMps), LimitFromHeader(header), 0.05, header);
        Assert.AreEqual(
            RunHeader.SpeedLimitMps(plan, scenario, null, null, null),
            scenario.SpeedLimitMps,
            1e-12,
            "fizyka przebiegu skryptowego i nagłówek mają czytać JEDNO wyrażenie");
    }

    // --- DECYZJA 1 (05.09.2026): tryb ręczny jedzie limitem PLANU -------------------

    /// <summary>
    /// Tryb ręczny bierze limit z planu sygnalizacji, a nie ze scenariusza. To jest ta
    /// sama usterka, którą <see cref="RunHeader"/> naprawił dla <c>--line</c>: ścieżka
    /// ręczna jechała 80 km/h, czyli prędkością KONSTRUKCYJNĄ M7, i ta liczba trafiała
    /// nie tylko do napisu, ale i do kontrolera.
    /// </summary>
    [TestMethod]
    public void TrybRecznyJedzieLimitemPlanuANieScenariusza()
    {
        var plan = Parse();
        Assert.IsTrue(plan.IsValid, plan.Error);
        Assert.IsFalse(plan.LineMode);
        Assert.IsFalse(plan.ScriptedMode, "brak argumentów znaczy tryb ręczny");

        var scenario = Scenario();
        var signalling = Plan(Axis());

        var limitMps = RunHeader.SpeedLimitMps(plan, scenario, null, null, signalling);

        Assert.AreEqual(signalling.PermittedSpeedMps, limitMps, 0.0,
            "limit trybu ręcznego ma być TĄ SAMĄ liczbą, co limit planu — nie równą jej");
        Assert.AreEqual(PlanLimitKmh, Units.MpsToKmh(limitMps), 1e-9);
        Assert.AreNotEqual(
            VehicleModel.M7.DesignMaxSpeedKmh, Units.MpsToKmh(limitMps), 1e-9,
            "80 km/h to prędkość konstrukcyjna M7, a nie ograniczenie na torze");

        var header = RunHeader.Line(
            plan, ViewKind.Cab, scenario, FixedStep.Simulation, Conditions(),
            core: null, line: null, manualPlan: signalling);
        Assert.AreEqual(PlanLimitKmh, LimitFromHeader(header), 0.05, header);
    }

    [TestMethod]
    public void KabinaPodOchronaJedzieSUFITEMMaszynistyANieLimitemPlanu()
    {
        // To są DWIE RÓŻNE LICZBY i dopiero ich rozdzielenie czyni ingerencję ATP
        // możliwą. Sufit dostaje kontroler, bo tyle wolno maszyniście poprosić;
        // limitu planu pilnuje ochrona i on wychodzi osobno, jako `v_dop` w HUD-zie.
        // Przy suficie równym limitowi planu sterownik nie przekroczy 72,00 km/h,
        // więc ochrona nie miałaby czego łapać.
        var plan = Parse("--signalling=/tmp/plan.json", "--limit-kmh=76");
        Assert.IsTrue(plan.IsValid, plan.Error);
        Assert.IsTrue(plan.ManualSignalling);

        var scenario = Scenario();
        var signalling = Plan(Axis());
        var limitMps = RunHeader.SpeedLimitMps(plan, scenario, null, null, signalling);

        Assert.AreEqual(76.0, Units.MpsToKmh(limitMps), 1e-9,
            "kontroler dostał limit planu zamiast sufitu maszynisty");
        Assert.AreNotEqual(
            PlanLimitKmh, Units.MpsToKmh(limitMps), 1e-9,
            "sufit ponad limit planu zniknął — ochrona nie miałaby czego łapać");

        var header = RunHeader.Line(
            plan, ViewKind.Cab, scenario, FixedStep.Simulation, Conditions(),
            core: null, line: null, manualPlan: signalling);
        Assert.AreEqual(76.0, LimitFromHeader(header), 0.05, header);
    }

    [TestMethod]
    public void KabinaPodOchronaBezSufituJedzieLimitemPlanu()
    {
        // Sufit jest OPCJĄ. Bez niego wpięcie ochrony nie zmienia ani jednej liczby
        // w nagłówku — a to jest warunek tożsamości: przejazd pod ATP przy limicie
        // planu ma być tym samym przejazdem, co bez ATP.
        var plan = Parse("--signalling=/tmp/plan.json");
        Assert.IsTrue(plan.IsValid, plan.Error);
        Assert.IsTrue(plan.ManualSignalling);

        var signalling = Plan(Axis());
        var limitMps = RunHeader.SpeedLimitMps(plan, Scenario(), null, null, signalling);

        Assert.AreEqual(signalling.PermittedSpeedMps, limitMps, 0.0,
            "limit kabiny bez sufitu ma być TĄ SAMĄ liczbą, co limit planu — nie równą jej");
    }

    /// <summary>
    /// Odtworzenie z zapisu wejść jest trybem ręcznym z klawiszami z pliku, więc jedzie
    /// tym samym limitem. Gdyby brało inny, przejazd gracza i jego odtworzenie
    /// rozjechałyby się na fizyce, a nie na wejściu — czyli porównanie, po które ten
    /// zapis w ogóle istnieje, przestałoby cokolwiek znaczyć.
    /// </summary>
    [TestMethod]
    public void OdtworzenieJedzieTymSamymLimitemCoTrybReczny()
    {
        var reczny = Parse();
        var odtworzenie = Parse("--replay=zapis.log");
        Assert.IsTrue(odtworzenie.IsValid, odtworzenie.Error);
        Assert.IsFalse(odtworzenie.ScriptedMode);

        var signalling = Plan(Axis());
        Assert.AreEqual(
            RunHeader.SpeedLimitMps(reczny, Scenario(), null, null, signalling),
            RunHeader.SpeedLimitMps(odtworzenie, Scenario(), null, null, signalling),
            0.0);
    }

    /// <summary>
    /// Tryb ręczny bez planu wywraca się, a nie wraca po cichu na 80 km/h. Ta sama
    /// decyzja i ten sam powód, co przy przejeździe linią bez prowadzenia: cichy odwrót
    /// na prędkość konstrukcyjną przeszedł wszystkie bramki tego repozytorium przez
    /// pięć miesięcy.
    /// </summary>
    [TestMethod]
    public void TrybRecznyBezPlanuNieDostajeLimituZeScenariusza()
    {
        var plan = Parse();

        var error = Assert.ThrowsException<ArgumentException>(() => RunHeader.SpeedLimitMps(
            plan, Scenario(), null, null, null));
        StringAssert.Contains(error.Message, "Przejazd ręczny bez planu sygnalizacji", error.Message);
    }

    /// <summary>
    /// Liczba 72 nie jest wpisana w kodzie: pochodzi z pliku planu, tego samego, który
    /// scena podaje autopilotowi pod <c>--signalling</c>. Ten test jest jedynym
    /// miejscem, w którym ścieżka z <see cref="RunPlan.ManualSpeedLimitPlanPath"/> jest
    /// przypięta do pliku na dysku — gdyby plik zniknął albo zmienił limit, tryb ręczny
    /// zmieniłby prędkość, a nie „nic by się nie stało".
    /// </summary>
    [TestMethod]
    public void LimitTrybuRecznegoPochodziZPlikuPlanuANieZKodu()
    {
        var path = Path.Combine(RepositoryRoot(), RunPlan.ManualSpeedLimitPlanPath);
        Assert.IsTrue(File.Exists(path), path);

        var signalling = SignallingPlan.FromJson(File.ReadAllText(path));
        var limitMps = RunHeader.SpeedLimitMps(Parse(), Scenario(), null, null, signalling);

        Assert.AreEqual(PlanLimitKmh, Units.MpsToKmh(limitMps), 1e-9, path);
        Assert.AreEqual("classic_2026", signalling.Mode, path);
    }

    private static string RepositoryRoot()
    {
        var directory = new DirectoryInfo(AppContext.BaseDirectory);
        while (directory is not null)
        {
            if (File.Exists(Path.Combine(directory.FullName, "CLAUDE.md")))
            {
                return directory.FullName;
            }

            directory = directory.Parent;
        }

        Assert.Inconclusive("Test uruchomiony poza drzewem repozytorium.");
        throw new InvalidOperationException();
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
            plan, ViewKind.Cab, Scenario(), FixedStep.Simulation, Conditions(),
            null, null, Plan(Axis()));
        StringAssert.Contains(pinned, "krok=1/120 s", pinned);

        var slower = RunHeader.Line(
            plan, ViewKind.Cab, Scenario(), FixedStep.FromHertz(60), Conditions(),
            null, null, Plan(Axis()));
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
            plan, ViewKind.Cab, Scenario(), FixedStep.Simulation, conditions,
            null, null, Plan(Axis()));

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
            core: null, line: Drive(plan.LimitKmh, Axis()), manualPlan: null);

        StringAssert.StartsWith(header, "[PRZEJAZD] tryb=line widok=Outside", header);
    }
}
