using System;
using System.Collections.Generic;
using System.Globalization;
using Godot;
using MetroBxl.Game.Assets;
using MetroBxl.Game.Input;
using MetroBxl.Game.UI;
using MetroBxl.Game.World;
using MetroBxl.Sim.Line;
using MetroBxl.Sim.Physics;
using MetroBxl.Sim.Signalling;
using MetroBxl.Sim.Train;
using Environment = Godot.Environment;
using Path = System.IO.Path;

namespace MetroBxl.Game;

/// <summary>Który widok jest aktywny.</summary>
public enum ViewKind
{
    /// <summary>Kabina — widok gry.</summary>
    Cab,

    /// <summary>Za składem, wewnątrz tunelu.</summary>
    Chase,

    /// <summary>Z boku i z góry, przez odrzucone tyłem ściany tunelu — tylko kontrola geometrii.</summary>
    Outside,
}

/// <summary>
/// Pierwszy przejazd: jeden skład M7 na pakiecie A, napędzany rdzeniem <c>MetroBxl.Sim</c>.
///
/// <b>Podział ról, z którego wynika reszta.</b> Ten plik nie liczy ani jednej siły.
/// Krok symulacji wykonuje <see cref="TrainController"/> albo <see cref="ScenarioDrive"/>
/// z rdzenia; tutaj zostaje to, co należy do silnika: wczytanie geometrii, ustawienie
/// kamer, odczyt klawiatury, HUD i pętla klatkowa. <c>docs/01-architecture.md</c>:
/// linia jest symulacją, kabina jednym z jej widoków.
///
/// <b>Trzy tryby.</b>
/// <list type="bullet">
/// <item>bez argumentów — prowadzenie z klawiatury;</item>
/// <item><c>--telemetry=PLIK</c> — przejazd po zapisanym scenariuszu, bez interakcji,
/// z telemetrią w formacie rdzenia. To jest odpowiednik testu: te same liczby przy
/// każdym powtórzeniu i te same, co z <c>src/Sim.Runner</c>;</item>
/// <item><c>--shot=PLIK --at-chainage=X</c> — przewinięcie przejazdu i zrzut ekranu.</item>
/// </list>
///
/// <b>Determinizm.</b> Stan po N krokach nie zależy od tego, jak kroki rozłożyły się na
/// klatki: akumulator zamienia czas klatki na całkowitą liczbę kroków 1/120 s, a resztę
/// przenosi dalej. Tryb telemetrii celowo podaje akumulatorowi **nierówne** czasy klatek
/// (<c>--jitter</c>), żeby to sprawdzić, a nie założyć.
/// </summary>
public sealed partial class FirstRun : Node3D
{
    /// <summary>Rozstrzygnięty wiersz poleceń. Ustawiany raz, w `ParseArguments`.</summary>
    private RunPlan? _plan;
    private readonly List<string> _telemetry = new();

    private TrackAxis _axis = null!;
    private SceneAxis _sceneAxis = null!;
    private VehicleModel _model = null!;
    private DriveScenario _scenario = null!;
    private RunConditions _conditions = null!;
    private TrainController _controller = null!;
    private DriverInput _input = null!;

    /// <summary>
    /// Dźwignia nastawnika. Siedzi w rdzeniu, bo przesuwa się o <c>tempo · krok</c>
    /// RAZ NA KROK SYMULACJI, a nie raz na klatkę — patrz <see cref="DriverNotch"/>
    /// i <c>reports/droga-do-grywalnosci.md</c> §5.1.
    /// </summary>
    private DriverNotch _notch = null!;

    /// <summary>
    /// Stan klawiszy tej klatki. Odczytany raz w <see cref="_Process"/>, użyty przez
    /// wszystkie kroki, które w tej klatce wypadną — silnik nie ma historii klawiatury
    /// wewnątrz klatki i model jej nie udaje.
    /// </summary>
    private DriverKeys _keys = DriverKeys.None;

    /// <summary>
    /// Klawisze OSTATNIEGO wykonanego kroku — z klawiatury albo z zapisu wejść. HUD
    /// czyta to, a nie <see cref="_keys"/>: w odtworzeniu klawiatura milczy, a wiersz
    /// o hamulcu awaryjnym ma mówić o przejeździe, który się odbywa, a nie o tym, czy
    /// ktoś akurat trzyma klawisz przy oglądaniu.
    /// </summary>
    private DriverKeys _activeKeys = DriverKeys.None;

    private FixedStep _step;

    private ScenarioDrive? _scripted;
    private StationService? _stations;
    private LineDrive? _line;
    private LineCore? _lineCore;

    /// <summary>
    /// Plan sygnalizacji, z którego tryb ręczny bierze prędkość dopuszczalną;
    /// <c>null</c> w trybie linii i w przebiegu skryptowym. Plan jest tu CZYTANY,
    /// a nie prowadzi — patrz <see cref="RunPlan.ManualSpeedLimitPlanPath"/>.
    /// </summary>
    private SignallingPlan? _manualPlan;
    private DriveState _state;
    private DriverCommand _command = DriverCommand.Coast;

    /// <summary>
    /// Polecenie po filtrze stacji — to, które dostał kontroler. HUD pokazuje
    /// <see cref="_command"/> (dźwignię pod ręką maszynisty), telemetria pokazuje TO
    /// (wejście fizyki). Rozróżnienie ma znaczenie tylko w trybie ręcznym, bo tylko
    /// tam działa <see cref="StationService"/>, i tylko tam blokada trakcji na czas
    /// cyklu drzwi rozjeżdża jedno z drugim.
    /// </summary>
    private DriverCommand _effectiveCommand = DriverCommand.Coast;

    private double _acceleration;

    private TunnelView _tunnel = null!;
    // Manifest zostaje w polu, bo metadane zrzutu opisują TO, co scena naprawdę wczytała.
    private ChunkManifest? _manifest;
    private string _assetDirectory = string.Empty;
    private StandardMaterial3D? _tunnelMaterial;
    private TrainView _train = null!;
    private StationView _platforms = null!;
    private Camera3D _cab = null!;
    private Camera3D _chase = null!;
    private OmniLight3D _headlight = null!;
    private Hud _hud = null!;

    /// <summary>
    /// Zamiana czasu klatki na kroki rdzenia. Logika siedzi w `src/Sim`, bo
    /// `docs/01-architecture.md` mówi, że ta warstwa jest bez logiki — a jako
    /// prywatne pole węzła nie dawała się dotknąć żadnym testem (Issue #106).
    /// </summary>
    private StepAccumulator _accumulator = null!;
    private long _frames;
    private long _sampleEvery = DriveTelemetry.DefaultSampleEverySteps;
    private long _stepsPerFrame = 120;
    private double _jitter;
    /// <summary>
    /// Ile wolno się różnić długości osi z manifestu chunków i z rdzenia.
    ///
    /// <para>Nie jest to zapas bezpieczeństwa, tylko rozdzielczość zapisu: manifest
    /// trzyma długość zaokrągloną, a rdzeń liczy ją z zagęszczonej łamanej. Zmierzone
    /// na pakiecie A: |Δ| = 1,335E-005 m. Milimetr jest o dwa rzędy wielkości powyżej
    /// tego rozrzutu i o sześć rzędów poniżej rozjazdu, który ma łapać.</para>
    /// </summary>
    private const double AxisManifestToleranceM = 1e-3;

    /// <summary>
    /// Promień, w jakim metadane zrzutu szukają peronu wokół punktu osi.
    ///
    /// <para>Nie jest to wymiar czegokolwiek w metrze, tylko parametr pomiaru, i ma
    /// dwa ograniczenia, oba zmierzone. Od dołu: płyta peronu zaczyna się 3,53 m od osi
    /// TRASY (2,10 m odsunięcia toru + 1,35 m połowy szerokości M7 + 0,08 m szczeliny),
    /// więc promień mniejszy nie znalazłby własnego peronu. Od góry: najkrótszy odstęp
    /// stacji pakietu A to 415 m, a peron ma 94 m, więc sąsiedni peron leży nie bliżej
    /// niż 320 m — 20 m nie ma prawa go złapać.</para>
    /// </summary>
    private const double PlatformNearRadiusM = 20.0;

    /// <summary>
    /// Kody wyjścia. Były rozsypane po pliku jako literały 3–7; teraz mają nazwy,
    /// bo CI i człowiek czytający log muszą wiedzieć, co je odróżnia.
    /// </summary>
    private const int ExitMissingInput = 3;

    private const int ExitMissingAssets = 4;

    private const int ExitTelemetryWriteFailed = 5;

    private const int ExitHeadlessCannotRender = 6;

    private const int ExitShotWriteFailed = 7;

    private const int ExitUnknownArgument = 8;

    private const int ExitBadArgumentValue = 9;

    private const int ExitAxisManifestMismatch = 10;

    /// <summary>Skorupa M7 się nie wczytała. Scena bez składu nie jest przejazdem.</summary>
    private const int ExitTrainMissing = 11;

    /// <summary>
    /// Perony się nie wczytały. Odmowa, a nie cichy przejazd bez nich — i to jest
    /// wprost wniosek z Issue #107. Scena bez peronów wygląda dokładnie tak samo jak
    /// scena z peronami wczytanymi 1000 m dalej: pusty tunel. Kadr z kabiny stojącej
    /// na stacji był takim kadrem od T-400 do 04.09.2026 i żadna bramka tego nie
    /// zauważyła, bo żadna nie miała czego porównać.
    /// </summary>
    private const int ExitPlatformsMissing = 12;

    /// <summary>
    /// Zrzut zamówiony w widoku, którego na tym kilometrażu nie ma.
    ///
    /// <para>Odmowa, a nie podstawienie innego kadru — i to jest ta sama decyzja, co
    /// przy <see cref="ExitPlatformsMissing"/>. Zrzut jest artefaktem WERYFIKACJI:
    /// plik nazwany <c>..._chase.png</c>, w którym po cichu siedzi kadr z kabiny,
    /// przeszedłby każdą bramkę oglądającą metryki klatki, bo klatka jest poprawna —
    /// tylko nie ta. Wołający zrzut umie odczytać kod wyjścia; gracz w kabinie nie ma
    /// gdzie go zobaczyć, więc tam odpowiedzią jest wiersz HUD-u, nie odmowa.</para>
    /// </summary>
    private const int ExitViewUnavailable = 13;

    private bool _scriptedMode;
    private bool _lineMode;

    /// <summary>Przejazd odtwarzany z zapisu wejść (<c>--replay</c>).</summary>
    private bool _replayMode;

    /// <summary>Zapis wejść do odtworzenia; <c>null</c> poza <c>--replay</c>.</summary>
    private InputLog? _replay;

    /// <summary>Zbieranie wejść do zapisu; <c>null</c> bez <c>--input-log</c>.</summary>
    private InputLogRecorder? _recorder;

    private string? _inputLogPath;
    private string? _replayPath;

    /// <summary>Zapis wejść już poszedł na dysk. Bez tego wyszedłby dwa razy: z końca przebiegu i z <c>_ExitTree</c>.</summary>
    private bool _inputLogWritten;

    private string? _callsPath;
    private double _limitKmh;
    private string? _signallingPath;

    /// <summary>Scena zgłosiła błąd i nie ma prawa dalej liczyć klatek.</summary>
    private bool _aborted;

    private string _mode = "manual";
    private string? _telemetryPath;
    private string? _shotPath;
    private double _shotChainageM;
    private int _shotCountdown = int.MaxValue;
    private ViewKind _view = ViewKind.Cab;

    /// <summary>
    /// Czy widok goniący da się w tej chwili pokazać. Liczy to
    /// <see cref="ChaseCameraAim.Availability"/> z kilometrażu i długości składu;
    /// tutaj jest tylko zapamiętane, żeby <see cref="ApplyView"/> i
    /// <see cref="UpdateHud"/> mówiły to samo w tej samej klatce.
    ///
    /// <para>Startuje na <c>true</c>, bo <see cref="ApplyView"/> leci w
    /// <c>_Ready</c> PRZED pierwszym <see cref="PlaceEverything"/>, a długość składu
    /// jest znana dopiero po wczytaniu skorupy. Godot rysuje po powrocie z
    /// <c>_Ready</c>, więc ta jedna klatka i tak nie ma jak trafić na ekran.</para>
    /// </summary>
    private bool _chaseAvailable = true;

    /// <summary>
    /// Wiersz HUD-u o niedostępnym widoku; pusty, gdy widok jest dostępny albo
    /// nieproszony. Składa go <see cref="PlaceEverything"/>, czyta
    /// <see cref="UpdateHud"/> — te dwie metody chodzą zawsze parą.
    /// </summary>
    private string _viewLine = string.Empty;

    private bool _viewKeyHeld;
    private bool _resetKeyHeld;
    private bool _done;

    /// <inheritdoc/>
    public override void _Ready()
    {
        ParseArguments();
        if (_aborted)
        {
            return;
        }

        _tunnel = GetNode<TunnelView>("Tunnel");
        _train = GetNode<TrainView>("Train");
        _platforms = GetNode<StationView>("Platforms");
        _cab = GetNode<Camera3D>("CabCamera");
        _chase = GetNode<Camera3D>("ChaseCamera");
        _headlight = GetNode<OmniLight3D>("CabCamera/Headlight");
        _hud = GetNode<Hud>("Hud");

        _cab.Fov = (float)DesignAssumptions.CabFovDeg;
        _headlight.OmniRange = (float)DesignAssumptions.HeadlightRangeM;
        _headlight.LightEnergy = (float)DesignAssumptions.HeadlightEnergy;

        BuildEnvironment();
        BuildSimulation();
        if (_aborted)
        {
            return;
        }

        BuildWorld();
        if (_aborted)
        {
            return;
        }

        ApplyView();
        LogHeader();

        if (_telemetryPath is not null)
        {
            _telemetry.Add(DriveTelemetry.Header);

            // Wiersz zerowy: stan PRZED pierwszym krokiem. W przebiegu skryptowym
            // podaje go `ScenarioDrive`; w odtworzeniu takiego obiektu nie ma, więc
            // wiersz składa się z tych samych składników, co każdy następny.
            _telemetry.Add(_scripted is not null
                ? DriveTelemetry.Row(_scripted)
                : ManualTelemetryRow());
        }

        PlaceEverything();
        UpdateHud();

        if (_shotPath is not null)
        {
            FastForwardToShot();
        }
    }

    // --- argumenty i ścieżki ------------------------------------------------------

    /// <summary>
    /// Czyta wiersz poleceń przez <see cref="RunPlan"/> i przenosi wynik do pól sceny.
    ///
    /// <para>Samo rozstrzyganie — lista znanych argumentów, znane widoki, parsowanie
    /// liczb i kontrola skończoności — siedzi w <see cref="RunPlan"/>, bo tamten plik
    /// NIE importuje Godota i daje się zawołać wprost z <c>tests/Game.Tests</c>.
    /// Tutaj zostaje wyłącznie to, co bez silnika nie ma sensu: odczyt argumentów
    /// procesu i <see cref="Abort"/>, który zatrzymuje pętlę klatek.</para>
    /// </summary>
    private void ParseArguments()
    {
        var plan = RunPlan.Parse(OS.GetCmdlineUserArgs(), ExitUnknownArgument, ExitBadArgumentValue);
        _plan = plan;
        if (!plan.IsValid)
        {
            Abort(plan.ExitCode, plan.Error!);
            return;
        }

        _telemetryPath = plan.TelemetryPath;
        _shotPath = plan.ShotPath;
        _scriptedMode = plan.ScriptedMode;
        _lineMode = plan.LineMode;
        _replayMode = plan.ReplayMode;
        _inputLogPath = plan.InputLogPath;
        _replayPath = plan.ReplayPath;
        _callsPath = plan.CallsPath;
        _limitKmh = plan.LimitKmh;
        _signallingPath = plan.SignallingPath;
        _mode = plan.Mode;
        _sampleEvery = plan.SampleEvery;
        _stepsPerFrame = plan.StepsPerFrame;
        _jitter = plan.Jitter;
        _shotChainageM = plan.ShotChainageM;
        _view = plan.View;
    }

    private string? Argument(string name) => _plan?.Argument(name);

    /// <summary>
    /// Przerywa przebieg z kodem błędu i **zatrzymuje pętlę klatek**.
    ///
    /// <para>Sam <c>GetTree().Quit()</c> nie wystarcza: Godot kończy dopiero na końcu
    /// klatki, a <c>_Ready</c> i <c>_Process</c> lecą dalej po niezbudowanym stanie.
    /// Flaga <see cref="_aborted"/> jest tym, co odróżnia „scena zgłosiła błąd"
    /// od „scena zawisła".</para>
    /// </summary>
    private void Abort(int code, string message)
    {
        _aborted = true;
        GD.PushError(message);
        GD.PrintErr(message);
        GetTree().Quit(code);
    }

    private static string RepoPath(string relative)
    {
        var projectDirectory = ProjectSettings.GlobalizePath("res://");
        return Path.GetFullPath(Path.Combine(projectDirectory, "..", "..", relative));
    }

    // --- budowa ------------------------------------------------------------------

    private void BuildSimulation()
    {
        var axisPath = Argument("axis") ?? RepoPath("data/track/L1_A.json");
        using var file = FileAccess.Open(axisPath, FileAccess.ModeFlags.Read);
        if (file is null)
        {
            Abort(ExitMissingInput, $"[OŚ] nie da się otworzyć {axisPath}: {FileAccess.GetOpenError()}");
            return;
        }

        _axis = TrackAxis.FromJson(file.GetAsText());
        _sceneAxis = new SceneAxis(_axis, DesignAssumptions.TrackOffsetM);

        _model = VehicleModel.M7;
        _scenario = DriveScenario.PackageAFirstRun(_model);
        _step = FixedStep.Simulation;
        _accumulator = new StepAccumulator(_step);

        // Pochylenie 0 nie jest wyborem: profil pionowy pakietu A ma status
        // not_modelled, a docs/21-measured-vs-assumed.md §3 zabrania wyprowadzania
        // z niego rzędnych. Otoczenie Tunnel wynika z geometrii pakietu A.
        _conditions = new RunConditions(
            _model.MassKg(TrainLoad.Aw2),
            0.0,
            _model.Adhesion(RailCondition.Dry),
            TrackEnvironment.Tunnel);

        _controller = new TrainController(_model);
        _input = new DriverInput();
        _notch = new DriverNotch(DesignAssumptions.ControlNotchRatePerSecond);
        _state = DriveState.AtRest;

        if (_replayPath is not null)
        {
            _replay = ReadInputLog(_replayPath);
            if (_replay is null)
            {
                return;
            }

            GD.Print(string.Create(
                CultureInfo.InvariantCulture,
                $"[WEJŚCIE] odtworzenie z {_replayPath}: {_replay.Steps} kroków, "
                + $"{_replay.Entries.Count} zmian klawiszy"));
        }

        if (_inputLogPath is not null)
        {
            _recorder = new InputLogRecorder();
        }

        if (_lineMode)
        {
            // TRZECI sterownik tego samego składu, i to jest zdanie przewodnie
            // `docs/01-architecture.md` wzięte dosłownie: „Linia jest symulacją, która
            // działa bez gracza. Kabina jest jednym z jej widoków." Tutaj scena JEST
            // widokiem — prowadzi rdzeń przez `LineDrive`, a kamera tylko patrzy.
            //
            // Autorytet stacji należy w tym trybie do `LineDrive`, nie do
            // `StationService`. Dwie kopie tej samej wiedzy w jednym przebiegu
            // rozjechałyby się, a `LineDrive` ma tu więcej: własny punkt hamowania
            // z T-311, którego kabina nie liczy, bo w kabinie liczy go człowiek.
            if (_axis.Stations.Count < 2)
            {
                Abort(ExitMissingInput,
                    $"[LINIA] oś {_axis.Id} ma {_axis.Stations.Count} stacji, "
                    + "przejazd z zatrzymaniami wymaga co najmniej dwóch");
                return;
            }

            var settings = new LineRunSettings(
                Units.KmhToMps(_limitKmh),
                DesignAssumptions.PassengerExchangeSeconds,
                DesignAssumptions.LineBrakeUsageFraction,
                DesignAssumptions.StationStopWindowM);
            if (_signallingPath is null)
            {
                // Bez sygnalizacji: goły `LineDrive`, tak jak przed wprowadzeniem
                // `--signalling`. Nie ma tu cichego wykrywania planu — brak argumentu
                // znaczy „jedź bez blokad" i HUD mówi to wprost.
                _line = new LineDrive(
                    _axis, _conditions, settings, _controller,
                    new BrakingPointSolver(_model), _step);
            }
            else
            {
                // Z sygnalizacją: prowadzi `LineCore`, czyli linia z nastawnią
                // automatyczną i autorytetem jazdy. `_line` wskazuje potem na
                // prowadzenie TEGO składu, więc reszta sceny nie widzi różnicy.
                var signalling = ReadSignallingPlan(_signallingPath);
                if (signalling is null)
                {
                    return;
                }

                try
                {
                    // ATP jest WŁĄCZONE razem z planem, bez osobnego argumentu, i to jest
                    // treść, nie domyślność. `data/signalling/ground-truth.json` mówi
                    // o obecnym systemie, że „automatycznie spowalnia skład"; plan
                    // w trybie `classic_2026` jest właśnie tym systemem. Osobny
                    // przełącznik znaczyłby, że istnieje sieć z blokadami i bez ochrony,
                    // a takiej sieci w źródłach nie ma.
                    //
                    // Przy limicie planu (72,00 km/h) ochrona nie ingeruje ANI RAZU
                    // i przejazd jest ten sam co przed jej wpięciem — zmierzone, nie
                    // założone. Zmienia przejazd dopiero limit podniesiony ponad plan
                    // (`--limit-kmh=76`), i wtedy ma zmieniać.
                    _lineCore = LineCore.M7(
                        signalling, _axis, _conditions, settings, turnbackSeconds: 0.0, atp: true);
                }
                catch (ArgumentException error)
                {
                    Abort(ExitBadArgumentValue,
                        $"[LINIA] plan sygnalizacji nie pasuje do osi {_axis.Id}: {error.Message}");
                    return;
                }

                _lineCore.Add("KABINA", 0L);
                GD.Print(string.Create(
                    CultureInfo.InvariantCulture,
                    $"[SYGNALIZACJA] {signalling.Blocks.Count} bloków, {signalling.Routes.Count} tras, "
                    + $"wymaga tras: {signalling.RequireRoute}, "
                    + $"limit planu {Units.MpsToKmh(signalling.PermittedSpeedMps):F2} km/h, "
                    + $"margines autorytetu {signalling.AuthorityMarginM:F2} m"));
            }
        }
        else if (_scriptedMode)
        {
            _scripted = new ScenarioDrive(_controller, _scenario, _conditions, _step);
        }
        else
        {
            // TRYB RĘCZNY (i odtworzenie, które jest nim z klawiszami z pliku) bierze
            // prędkość dopuszczalną Z PLANU SYGNALIZACJI — decyzja właściciela
            // z 05.09.2026. Do tego dnia jechał limitem ze scenariusza, czyli 80 km/h,
            // prędkością KONSTRUKCYJNĄ M7: dokładnie tą liczbą, którą `RunHeader`
            // naprawił dla `--line` (#220), tyle że ścieżka ręczna została wtedy
            // pominięta i liczba trafiała nie tylko do napisu, ale i do kontrolera.
            //
            // Plan jest CZYTANY, nie prowadzi: skład nie jest zarejestrowany
            // w sygnalizacji, nie dostaje autorytetu jazdy i nie ma ochrony pociągu.
            // Z pliku bierze się jedna liczba i tylko ta jedna — a wiersz [LIMIT] niżej
            // mówi, która i skąd. Brak pliku jest ODMOWĄ startu: cichy odwrót na
            // scenariusz byłby powrotem do usterki, a wygląda tak samo jak przejazd
            // poprawny.
            var planPath = RepoPath(RunPlan.ManualSpeedLimitPlanPath);
            _manualPlan = ReadSignallingPlan(planPath);
            if (_manualPlan is null)
            {
                return;
            }

            if (!string.Equals(_manualPlan.AxisId, _axis.Id, StringComparison.Ordinal))
            {
                Abort(ExitBadArgumentValue,
                    $"[LIMIT] plan {planPath} opisuje oś {_manualPlan.AxisId}, a przejazd "
                    + $"idzie po {_axis.Id}: prędkość dopuszczalna z cudzej osi nie jest "
                    + "prędkością dopuszczalną tej");
                return;
            }

            GD.Print(string.Create(
                CultureInfo.InvariantCulture,
                $"[LIMIT] tryb ręczny: {Units.MpsToKmh(_manualPlan.PermittedSpeedMps):F2} km/h z planu {_manualPlan.PlanId} ({RunPlan.ManualSpeedLimitPlanPath}); plan jest czytany, nie prowadzi — bez blokad i bez ochrony pociągu"));

            BuildStationService();
        }
    }

    /// <summary>
    /// Obsługa stacji dla przejazdu prowadzonego z klawiatury albo odtwarzanego
    /// z zapisu wejść.
    /// </summary>
    private void BuildStationService()
    {
        if (_axis.Stations.Count >= 2)
        {
            // Obsługa stacji jest WYŁĄCZNIE w trybie ręcznym, i to nie jest oszczędność.
            // Przebieg skryptowy odtwarza `ScenarioDrive` z rdzenia i jego telemetria jest
            // porównywana z rdzeniem CO DO BITU (`reports/T-400-first-run.md`, rozjazd
            // 0,000 m). Wpięcie tu blokady drzwi zmieniłoby przebieg, którego zgodność
            // jest całą treścią tamtej bramki — a scenariusz T-400 nie ma zatrzymań na
            // stacjach, więc nie ma czego blokować.
            _stations = new StationService(
                _axis.Stations,
                new DoorCycle(DesignAssumptions.PassengerExchangeSeconds),
                _step,
                DesignAssumptions.StationStopWindowM);
        }
    }

    /// <summary>
    /// Plan sygnalizacji z pliku. Godot czyta przez <see cref="FileAccess"/>, więc
    /// ścieżka spod `res://` też działa; <c>SignallingPlan.FromFile</c> użyłoby
    /// <c>System.IO</c> i nie widziałoby zasobów silnika.
    /// </summary>
    private SignallingPlan? ReadSignallingPlan(string path)
    {
        using var file = FileAccess.Open(path, FileAccess.ModeFlags.Read);
        if (file is null)
        {
            Abort(ExitMissingInput,
                $"[SYGNALIZACJA] nie da się otworzyć {path}: {FileAccess.GetOpenError()}");
            return null;
        }

        try
        {
            return SignallingPlan.FromJson(file.GetAsText());
        }
        catch (Exception error) when (error is ArgumentException or FormatException)
        {
            Abort(ExitBadArgumentValue, $"[SYGNALIZACJA] {path} nie jest planem: {error.Message}");
            return null;
        }
    }

    /// <summary>
    /// Zapis wejść maszynisty z pliku. Czytany przez <see cref="FileAccess"/> z tego
    /// samego powodu co plan sygnalizacji: ścieżka spod `res://` ma działać.
    /// </summary>
    /// <param name="path">Ścieżka pliku zapisu.</param>
    /// <returns>Odczytany zapis albo <c>null</c>, gdy przebieg został przerwany.</returns>
    private InputLog? ReadInputLog(string path)
    {
        using var file = FileAccess.Open(path, FileAccess.ModeFlags.Read);
        if (file is null)
        {
            Abort(ExitMissingInput,
                $"[WEJŚCIE] nie da się otworzyć {path}: {FileAccess.GetOpenError()}");
            return null;
        }

        try
        {
            return InputLog.Parse(file.GetAsText());
        }
        catch (Exception error) when (error is ArgumentException or FormatException)
        {
            Abort(ExitBadArgumentValue, $"[WEJŚCIE] {path} nie jest zapisem wejść: {error.Message}");
            return null;
        }
    }

    private void BuildEnvironment()
    {
        // Środowisko powstaje w kodzie, a nie w .tscn, bo jego jedynym zadaniem jest
        // oświetlić wnętrze zamkniętej rury o normalnych skierowanych do środka.
        // Światło kierunkowe do takiego tunelu nie wejdzie; zostaje ambient plus
        // reflektor czołowy podwieszony pod kamerą kabiny.
        var environment = new Environment
        {
            BackgroundMode = Environment.BGMode.Color,
            BackgroundColor = new Color(0.02f, 0.02f, 0.03f),
            AmbientLightSource = Environment.AmbientSource.Color,
            AmbientLightColor = new Color(0.62f, 0.63f, 0.66f),
            AmbientLightEnergy = 0.35f,
        };

        GetNode<WorldEnvironment>("WorldEnvironment").Environment = environment;
    }

    private void BuildWorld()
    {
        if (Argument("no-geometry") is not null)
        {
            GD.Print("[ASSETS] --no-geometry: scena bez tunelu i bez składu; fizyka bez zmian");
            return;
        }

        var assets = Argument("assets") ?? RepoPath("build/t400");
        var manifestPath = Argument("manifest") ?? Path.Combine(assets, "chunks", "L1_A-chunks.json");
        var shellPath = Argument("shell") ?? Path.Combine(assets, "M7_shell.glb");
        var platformsPath = Argument("platforms") ?? Path.Combine(assets, "L1_A-platforms.glb");

        using var manifestFile = FileAccess.Open(manifestPath, FileAccess.ModeFlags.Read);
        if (manifestFile is null)
        {
            Abort(ExitMissingAssets,
                $"[ASSETS] brak manifestu {manifestPath}. Wygeneruj chunki " +
                "(tools/blender/tunnel_sweep.py --chunk-dir ...) albo uruchom z --no-geometry.");
            return;
        }

        var manifest = ChunkManifest.FromJson(manifestFile.GetAsText());
        _manifest = manifest;
        var tunnelMaterial = GlbLoader.NeutralMaterial(new Color(0.52f, 0.52f, 0.53f), 0.95f);
        var trainMaterial = GlbLoader.NeutralMaterial(new Color(0.80f, 0.81f, 0.83f), 0.45f);

        // Peron dostaje WŁASNY, ciemniejszy odcień szarości i to nie jest wybór
        // estetyczny, tylko warunek widzialności: płyta stoi 1,4 m od ściany komory
        // i przy tej samej wartości albedo obie powierzchnie zlewają się w kadrze
        // z kabiny w jedną plamę. Odcień zostaje neutralny — `docs/03-legal.md`
        // zabrania wystroju, piktogramów i barw STIB, a wygląd docelowy jest
        // przedmiotem osobnego zadania, nie tego.
        var platformMaterial = GlbLoader.NeutralMaterial(new Color(0.34f, 0.34f, 0.36f), 0.90f);

        // Katalog i materiał zapamiętane, bo streamowanie dokłada chunki w KAŻDEJ
        // klatce, a nie raz przy starcie.
        _assetDirectory = Path.GetDirectoryName(manifestPath) ?? assets;
        _tunnelMaterial = tunnelMaterial;
        _tunnel.Stream(manifest, _assetDirectory, tunnelMaterial, _scenario.StartChainageM);

        // Wynik `Load` był ODRZUCANY. `TrainView.Load` zwraca liczbę brył i zero znaczy
        // „nie wczytałem nic" — bez tego sprawdzenia scena szła dalej bez składu, a że
        // metadane opisywały wyłącznie tunel, cały `godot-first-run.yml` zostawał
        // zielony. Zmierzone audytem mutacyjnym (Issue #107): mutacja `TrainView.cs:38`
        // przechodziła bramki, tą samą drogą przeżyły `TrackOffsetM 2.10→0.0`
        // i `CabEyeHeightM 2.20→0.0`.
        var bodies = _train.Load(shellPath, trainMaterial);
        if (bodies <= 0)
        {
            Abort(ExitTrainMissing,
                $"[SKŁAD] {shellPath} nie dał ani jednej bryły — scena bez składu nie jest przejazdem");
            return;
        }

        // Perony wchodzą PRZED wypisaniem opisu sceny, żeby log przejazdu mówił
        // o tym, co scena naprawdę trzyma, a nie o połowie tego.
        var slabs = _platforms.Load(platformsPath, platformMaterial);
        if (slabs <= 0)
        {
            Abort(ExitPlatformsMissing,
                $"[PERON] {platformsPath} nie dał ani jednej bryły. Wygeneruj perony "
                + "(tools/track/station_layout.py, potem tools/blender/station_kit.py "
                + "--component platform --component edge) albo uruchom z --no-geometry.");
            return;
        }

        GD.Print(_tunnel.Describe(manifest));
        GD.Print(_platforms.Describe());
        GD.Print(_train.Describe());
        var drift = Math.Abs(manifest.AxisLengthM - _axis!.LengthM);
        GD.Print(string.Create(
            CultureInfo.InvariantCulture,
            $"[OŚ] manifest {manifest.AxisLengthM:F3} m vs oś z rdzenia {_axis.LengthM:F3} m, " +
            $"|Δ| = {drift:E3} m"));

        // Do 02.09.2026 był to sam wydruk. Zmierzone mutacją: wyzerowanie
        // `axis_length_m` w ChunkManifest dawało w logu zielonego przebiegu
        // „|Δ| = 6.687E+003 m" — rozjazd 6,7 km — i job kończył się sukcesem.
        // Osobny krok CI `axis-vs-manifest` tego nie łapie, bo czyta manifest
        // WŁASNYM parserem z Sim.Runner: sprawdza plik na dysku, a nie to, co
        // z tego pliku wyjęła scena.
        if (drift > AxisManifestToleranceM)
        {
            Abort(ExitAxisManifestMismatch, string.Create(
                CultureInfo.InvariantCulture,
                $"[OŚ] manifest chunków ({manifest.AxisLengthM:F3} m) nie opisuje tej osi " +
                $"({_axis.LengthM:F3} m), |Δ| = {drift:E3} m > {AxisManifestToleranceM:E3} m"));
        }
    }

    private void LogHeader()
    {
        // Składanie tego wiersza siedzi w `RunHeader`, czyli w pliku BEZ GODOTA, i to
        // nie jest przenoszenie kodu dla porządku. Do 04.09.2026 pole `limit=` brało
        // liczbę z `_scenario.SpeedLimitMps` — z rejestru pojazdu — więc przy
        // `--limit-kmh=70` nagłówek mówił 80,0 km/h, a rdzeń jechał 70,00 km/h.
        // Nagłówek nie dostaje już ŻADNEJ liczby parametrem: dostaje obiekty, które
        // prowadzą przebieg, i czyta liczby z nich.
        GD.Print(RunHeader.Line(
            _plan!, _view, _scenario, _step, _conditions, _lineCore, _line, _manualPlan));
        GD.Print($"[OŚ] {_axis}");

        foreach (var assumption in _scenario.Assumptions)
        {
            GD.Print($"[ZAŁOŻENIE scenariusz] {assumption}");
        }

        foreach (var assumption in DesignAssumptions.All)
        {
            GD.Print($"[ZAŁOŻENIE widok] {assumption}");
        }
    }

    // --- pętla -------------------------------------------------------------------

    /// <inheritdoc/>
    public override void _Process(double delta)
    {
        if (_aborted)
        {
            // Bez tego przebieg przerwany w `_Ready` kręcił klatki na niezbudowanym
            // stanie aż do `timeout-minutes` w CI.
            return;
        }

        _frames++;

        if (_shotPath is not null)
        {
            if (--_shotCountdown <= 0)
            {
                SaveShot();
            }

            return;
        }

        if (_done)
        {
            return;
        }

        if (!_scriptedMode && !_replayMode)
        {
            // KLATKA CZYTA KLAWISZE, KROK PRZESUWA DŹWIGNIĘ. Do 05.09.2026 stało tu
            // `_command = _input.Poll(delta)`, czyli przesuw nastawnika o
            // `tempo · Δt_klatki`, a wszystkie kroki tej klatki dostawały to samo
            // polecenie. Skutkiem było, że o położeniu dźwigni decydowała LICZBA KLATEK:
            // ta sama sekwencja klawiszy dawała 566,407284 m przy 120 kl./s i
            // 566,641450 m przy 60 kl./s (reports/droga-do-grywalnosci.md §5.1),
            // przy bramkach porównujących telemetrię z progiem 0.
            //
            // Odczyt klawiatury zostaje raz na klatkę, bo silnik nie daje jej częściej
            // i zmyślanie historii wewnątrz klatki byłoby wymyślaniem wejścia gracza.
            // Przesuw dźwigni przeniósł się do `StepOnce`, czyli pod licznik kroków.
            _keys = _input.Read();
            HandleViewKeys();
        }

        // Przebieg z `--calls` jest WERYFIKACYJNY, więc leci syntetycznym rytmem:
        // 853 s przejazdu w czasie ściennym to 853 s czekania w CI. Bez `--calls`
        // tryb `--line` idzie czasem ściennym, bo wtedy ktoś na to patrzy.
        // Odtworzenie z zapisu wejść leci tak samo i z tego samego powodu — a przy
        // okazji to `--steps-per-frame` jest w nim JEDYNYM sposobem, żeby ten sam
        // zapis puścić przy różnym podziale kroków na klatki.
        var synthetic = _scriptedMode || _replayMode || (_lineMode && _callsPath is not null);
        AdvanceBy(synthetic ? SyntheticFrameSeconds() : delta);
        PlaceEverything();
        UpdateHud();

        if (_scriptedMode && (_scripted?.Finished ?? false))
        {
            FinishScriptedRun();
        }
        else if (_lineMode && (_lineCore?.Finished ?? _line?.Finished ?? false))
        {
            FinishLineRun();
        }
        else if (_replay is not null && _state.Steps >= _replay.Steps)
        {
            FinishReplayRun();
        }
    }

    /// <summary>
    /// Czas klatki podawany akumulatorowi w trybie skryptowym.
    ///
    /// Nie jest to czas ścienny: przejazd pakietu A trwa 5,3 minuty symulacji i
    /// odtwarzanie go w czasie rzeczywistym w CI byłoby płaceniem minutami za czekanie.
    /// Z <c>--jitter</c> czas klatki jest **celowo nierówny**, więc akumulator dostaje
    /// niecałkowite liczby kroków i musi przenosić resztę. Jeżeli telemetria mimo to
    /// zgadza się z rdzeniem co do bitu, znaczy to, że krok stały robi to, co obiecuje.
    /// </summary>
    private double SyntheticFrameSeconds()
        => _plan!.SyntheticFrameSeconds(_step.Seconds, _frames);

    private long AdvanceBy(double seconds)
    {
        if (seconds <= 0.0)
        {
            return 0;
        }

        var wanted = _accumulator.StepsForFrame(seconds);
        var executed = 0L;
        for (var i = 0L; i < wanted; i++)
        {
            if (!StepOnce())
            {
                _accumulator.DropCarry();
                break;
            }

            executed++;
        }

        return executed;
    }

    private bool StepOnce()
    {
        // LINIA IDZIE PIERWSZA, i to nie jest kosmetyka kolejności. Przy `--line --shot`
        // `_scriptedMode` jest PRAWDZIWE (bo jest `--shot`), a `_scripted` jest NULLEM,
        // bo sterownikiem jest `LineDrive`. Ta gałąź stała wcześniej pod spodem i pierwszy
        // krok wchodził w `_scripted!.Step()` na nullu: zrzut wisiał do timeoutu 400 s
        // i nie powstawał żaden plik. Warunek na sterownik musi być sprawdzany przed
        // warunkiem na SPOSÓB ZAPISU wyniku.
        if (_lineCore is not null)
        {
            // Linia z sygnalizacją. `LineCore.Step` robi w jednym kroku wszystko:
            // wyjazdy, żądania tras nastawni, odczyt autorytetów, jazdę i meldunek
            // ruchu. Scena nie powtarza ani jednej z tych faz — tylko patrzy.
            if (_lineCore.Finished)
            {
                return false;
            }

            var przed = _state.SpeedMps;
            _lineCore.Step((id, point) => _command = point.Command);
            _line = _lineCore.Trains[0].Drive;
            if (_line is null)
            {
                // Skład jeszcze nie wjechał na plan (wejście zajęte). Krok się odbył,
                // zegar linii idzie, ale prowadzenia jeszcze nie ma.
                return true;
            }

            _state = _line.State;
            _acceleration = (_state.SpeedMps - przed) / _step.Seconds;
            return true;
        }

        if (_line is not null)
        {
            // Polecenie bierze się ZE ŚLADU, nie z domysłu: `LineDrive` liczy je sam
            // (punkt hamowania z T-311) i podaje w `TracePoint`. Wpisanie tu `Coast`
            // dałoby HUD pokazujący wyluzowane nastawniki w trakcie hamowania do peronu.
            var before = _state.SpeedMps;
            if (!_line.Step(point => _command = point.Command))
            {
                return false;
            }

            _state = _line.State;

            // Przyspieszenie to RÓŻNICA prędkości na tym kroku, nie osobny model:
            // `LineDrive` nie wystawia sił, a druga formuła obok pierwszej rozjechałaby
            // się z nią. Krok jest stały, więc iloraz jest dokładny, nie przybliżony.
            _acceleration = (_state.SpeedMps - before) / _step.Seconds;
            return true;
        }

        if (_scriptedMode)
        {
            if (!_scripted!.Step())
            {
                return false;
            }

            _state = _scripted.State;
            _command = _scripted.Command;
            _acceleration = _scripted.AccelerationMps2;

            if (_telemetryPath is not null &&
                (DriveTelemetry.IsSample(_state.Steps, _sampleEvery) || _scripted.Finished))
            {
                _telemetry.Add(DriveTelemetry.Row(_scripted));
            }

            return true;
        }

        // Numer kroku, który zaraz się wykona. `_state.Steps` rośnie dopiero w
        // `Advance`, więc TU jest jeszcze indeks tego kroku — i to jest ten sam numer,
        // pod którym wejście trafia do zapisu i z którego jest odczytywane. Gdyby
        // zapis i odtworzenie brały go z dwóch różnych miejsc pętli, przejazdy
        // przesunęłyby się o jeden krok i nikt by nie wiedział który jest prawdziwy.
        var stepIndex = _state.Steps;

        // Odtworzenie z zapisu bierze klawisze PO NUMERZE KROKU, a nie z klawiatury.
        // Poza tym ścieżka jest ta sama co dla człowieka: ten sam `DriverNotch`,
        // ten sam `StationService`, ten sam `TrainController`. Osobna ścieżka przez
        // fizykę odbierałaby porównaniu gracza z rdzeniem wszelkie znaczenie.
        var keys = _replay?.KeysAt(stepIndex) ?? _keys;
        _recorder?.Record(stepIndex, keys);
        _activeKeys = keys;

        // JEDEN krok dźwigni na JEDEN krok symulacji. Klatka obejmująca N kroków
        // wykona to N razy z tym samym `keys` — stan klawiszy jest stały w obrębie
        // klatki, położenie nastawnika nie. Dlaczego akurat tak: `DriverNotch`.
        _command = _notch.Advance(keys, _step);

        // `Filter` posuwa licznik cyklu drzwi, więc musi zostać zawołane DOKŁADNIE RAZ
        // na krok symulacji — nie raz na klatkę. `AdvanceBy` woła `StepOnce` tyle razy,
        // ile kroków wypada w klatce, i to jest właściwe miejsce.
        var effective = _stations?.Filter(_state, _command, ChainageM) ?? _command;

        // Telemetria pokazuje polecenie, którym NAPRAWDĘ pojechał kontroler, czyli po
        // filtrze stacji — a nie surowe położenie dźwigni. Ta sama zasada, co
        // w `RunHeader`: kolumna, która nie jest wejściem fizyki, przepuściłaby
        // rozjazd w obsłudze drzwi przy porównaniu z progiem 0 i nikt by nie wiedział,
        // że blokada trakcji zadziałała w innym kroku.
        _effectiveCommand = effective;

        _state = _controller.Advance(
            _state, _conditions, effective, SpeedLimitMps, _step, out var forces);
        _acceleration = forces.AccelerationMps2;

        if (_replay is null)
        {
            return true;
        }

        var finished = _state.Steps >= _replay.Steps;
        if (_telemetryPath is not null
            && (DriveTelemetry.IsSample(_state.Steps, _sampleEvery) || finished))
        {
            _telemetry.Add(ManualTelemetryRow());
        }

        // Koniec przebiegu zgłasza `_Process`, tak samo jak dla scenariusza i dla linii.
        // Tutaj tylko przerywa się pętla kroków tej klatki, żeby kroki spoza zapisu
        // nie wykonały się „z rozpędu" na przeniesionej reszcie akumulatora.
        return !finished;
    }

    /// <summary>
    /// Wiersz telemetrii przejazdu bez scenariusza — prowadzonego z klawiatury albo
    /// odtwarzanego z zapisu wejść. Format składa <see cref="DriveTelemetry"/>, żeby
    /// wiersz wyszedł identyczny co do bajtu z wierszem rdzenia.
    /// </summary>
    /// <returns>Wiersz CSV zgodny z <see cref="DriveTelemetry.Header"/>.</returns>
    private string ManualTelemetryRow() => DriveTelemetry.Row(
        _state, _step, ChainageM, _acceleration, _effectiveCommand, DriveTelemetry.ManualPhase);

    private double ChainageM => _line?.ChainageM
        ?? (_lineCore is not null
            ? _axis.Stations[0].ChainageM
            : _scenario.StartChainageM + _state.DistanceM);

    /// <summary>
    /// Ograniczenie prędkości tego przebiegu — JEDNA liczba dla fizyki i dla nagłówka.
    ///
    /// <para>Nie jest to skrót zapisu. Nagłówek kłamał o limicie właśnie dlatego, że
    /// wypisywał SWOJĄ liczbę obok tej, którą jechał rdzeń; dopóki obie liczby są tym
    /// samym wyrażeniem, rozjazd między nimi nie ma się gdzie wziąć. W trybie RĘCZNYM
    /// to jest limit z planu sygnalizacji (72,00 km/h z `classic-2026`), w SKRYPTOWYM —
    /// limit ze scenariusza, czyli liczba, którą rdzeń podaje `ScenarioDrive`; tamten
    /// przebieg jest z rdzeniem porównywany CO DO BITU i musi zostać bez zmian.</para>
    /// </summary>
    private double SpeedLimitMps
        => RunHeader.SpeedLimitMps(_plan!, _scenario, _lineCore, _line, _manualPlan);

    // --- widok -------------------------------------------------------------------

    /// <summary>
    /// Widok, który scena naprawdę stawia — <see cref="_view"/> albo kabina, gdy
    /// zamówiony <c>chase</c> jest w tej chwili niedostępny.
    ///
    /// <para>Zejście do kabiny, a nie zostawienie kamery goniącej w skorupie: gracz
    /// dostaje kadr, który coś pokazuje, i wiersz HUD-u mówiący, czego nie dostał
    /// i od kiedy dostanie. Sam <c>chase</c> zostaje w <see cref="_view"/>, więc gdy
    /// skład wjedzie na oś, widok wraca sam — bez drugiego naciśnięcia klawisza.</para>
    /// </summary>
    private ViewKind EffectiveView =>
        _view == ViewKind.Chase && !_chaseAvailable ? ViewKind.Cab : _view;

    private void ApplyView()
    {
        var view = EffectiveView;
        _cab.Current = view == ViewKind.Cab;
        _chase.Current = view != ViewKind.Cab;

        // Z kabiny nie widać własnego pudła: kamera stoi wewnątrz skorupy M7, a ta ma
        // po solidify obie powierzchnie, więc bez ukrycia składu widać z bliska jego
        // wnętrze i nic poza tym. Kabina jako model wnętrza nie istnieje (T-220 jej
        // świadomie nie robi), więc jedyne uczciwe rozwiązanie to schować bryłę.
        _train.Visible = view != ViewKind.Cab;
    }

    private void PlaceEverything()
    {
        var chainage = Math.Min(ChainageM, _axis.LengthM);

        // Streamowanie stoi na początku, ale to jest porządek czytania, nie warunek
        // poprawności — i tak jest tu napisane, bo pierwsza wersja tego komentarza
        // twierdziła inaczej. Stało: „gdyby geometria dochodziła po ustawieniu kamery,
        // zrzut pokazywałby dziurę przed czołem". SPRAWDZONE 03.09.2026 i to nieprawda:
        // po przeniesieniu tego wywołania na koniec metody zrzut z 2000 m wyszedł
        // IDENTYCZNY CO DO BAJTU, a bramka metadanych przeszła. Powód jest prosty —
        // jedno i drugie dzieje się w tym samym `_Process`, a Godot rysuje dopiero
        // po jego powrocie, więc w obrębie klatki kolejność jest niewidoczna.
        //
        // Kolejność zaczęłaby mieć znaczenie dopiero wtedy, gdyby streamowanie
        // spóźniało się o CAŁĄ klatkę (osobny wątek, wczytywanie asynchroniczne).
        // Tego tu nie ma i dopóki nie ma, żaden test tej kolejności nie pilnuje.
        if (_manifest is not null && _tunnelMaterial is not null)
        {
            _tunnel.Stream(_manifest, _assetDirectory, _tunnelMaterial, chainage);
        }

        // Było tu `_train.LengthM > 0.0 ? _train.LengthM : 94.0` — CICHY ODWRÓT na
        // wartość ze specyfikacji, gdy skorupa się nie wczytała. Podstawiał poprawną
        // liczbę za nieistniejący skład, więc kamery i telemetria wyglądały normalnie.
        // Fallback jest zbędny, odkąd `SetUpScene` odmawia startu bez brył: długość
        // pochodzi teraz zawsze z wczytanej geometrii.
        var trainLength = _train.LengthM;
        _train.PlaceAt(_sceneAxis, chainage);

        // Dostępność widoku goniącego — decyzja właściciela z 05.09.2026, cała
        // arytmetyka w `ChaseCameraAim.Availability`. Długość bierze się STĄD, czyli
        // z wczytanej geometrii, a nie z rejestru: pytanie brzmi „czy kamera siedzi
        // w skorupie", a skorupa jest tym, co naprawdę stoi w scenie. Że ta liczba
        // ma się zgadzać z `parameters.length_m` ze spec M7, pilnuje osobny test —
        // rozjazd między spec a geometrią jest usterką danych, nie powodem, żeby
        // widok liczył się z liczby, której w kadrze nie ma.
        var availability = ChaseCameraAim.Availability(chainage, trainLength);
        _viewLine = _view == ViewKind.Chase ? availability.Reason : string.Empty;
        if (availability.Available != _chaseAvailable)
        {
            _chaseAvailable = availability.Available;
            ApplyView();
        }

        var (eye, forward) = _sceneAxis.CabPoint(
            chainage,
            DesignAssumptions.CabEyeSetbackM,
            DesignAssumptions.CabEyeHeightM,
            DesignAssumptions.CabEyeLateralM);
        _cab.LookAtFromPosition(eye, eye + forward, Vector3.Up);

        if (_view == ViewKind.Outside)
        {
            // Kamera stoi na sąsiednim torze, przed czołem składu, i patrzy wzdłuż
            // niego. Widać wtedy naraz trzy rzeczy, o które chodzi w kontroli: czy
            // skład stoi na torze, jaki ma luz do ściany i jaka jest skala wobec
            // przekroju 9,40 × 5,90 m.
            var (position, _) = _sceneAxis.CabPoint(
                chainage + DesignAssumptions.OutsideAheadM,
                0.0,
                DesignAssumptions.OutsideHeightM,
                DesignAssumptions.OutsideLateralM);
            var nose = _sceneAxis.CabPoint(chainage - (trainLength * 0.25), 0.0, 1.8, 0.0).Position;
            _chase.LookAtFromPosition(position, nose, Vector3.Up);
        }
        else
        {
            // Kilometraże kamery i celu liczy `ChaseCameraAim`, a nie ten plik, bo była
            // to jedyna arytmetyka kadru bez ani jednego testu — i przechodziło przez nią
            // 10 ostrzeżeń `Target and up vectors are colinear` na przebieg `--line`.
            // Przy czole ≤ 47 m oba kilometraże przycinają się do zera, kamera stoi
            // 2,60 m nad główką szyny, cel 1,80 m, a odcinek między nimi jest wtedy
            // PIONOWY. `LookTarget` podstawia w takim razie kierunek osi — dokładnie ten,
            // który dostaje kamera kabinowa w tym samym miejscu.
            var framing = ChaseCameraAim.Frame(
                chainage, trainLength, _axis.LengthM, DesignAssumptions.ChaseBehindM);
            var (position, forwardAtCamera) = _sceneAxis.CabPoint(
                framing.CameraChainageM,
                0.0,
                DesignAssumptions.ChaseHeightM,
                DesignAssumptions.CabEyeLateralM);
            var middle = _sceneAxis.CabPoint(framing.TargetChainageM, 0.0, 1.8, 0.0).Position;
            _chase.LookAtFromPosition(
                position,
                ChaseCameraAim.LookTarget(position, middle, forwardAtCamera, Vector3.Up),
                Vector3.Up);
        }
    }

    private void HandleViewKeys()
    {
        if (Godot.Input.IsPhysicalKeyPressed(Key.Escape))
        {
            GetTree().Quit();
            return;
        }

        var viewKey = Godot.Input.IsPhysicalKeyPressed(Key.C);
        if (viewKey && !_viewKeyHeld)
        {
            _view = _view == ViewKind.Cab ? ViewKind.Chase : ViewKind.Cab;
            ApplyView();
        }

        _viewKeyHeld = viewKey;

        var resetKey = Godot.Input.IsPhysicalKeyPressed(Key.R);
        if (resetKey && !_resetKeyHeld)
        {
            _state = DriveState.AtRest;
            _accumulator.DropCarry();
            _input.Clear();
            _notch.Set(DriverCommand.Coast);
            _keys = DriverKeys.None;
            _command = DriverCommand.Coast;

            // Zapis wejść idzie po NUMERZE KROKU, a reset cofa licznik kroków do zera —
            // dalsze nagrywanie nadpisywałoby numery, które już padły. Zapis zaczyna się
            // więc od nowa, razem z przejazdem. To, czego reset NIE obejmuje, to
            // `StationService` (kolejka stacji zostaje tam, gdzie dojechał skład) —
            // usterka opisana w reports/droga-do-grywalnosci.md §5.4 i zadanie G-4,
            // świadomie nietknięte tutaj, żeby zapis wejść nie udawał, że ją naprawia.
            _recorder?.Clear();
        }

        _resetKeyHeld = resetKey;
    }

    private void UpdateHud()
    {
        var chainage = ChainageM;
        var name = "koniec pakietu";
        var distance = _axis.LengthM - chainage;

        // Wiedza o tym, gdzie jest następna stacja, ma JEDNO miejsce. Poprzednio ta
        // pętla stała tutaj i była drugą kopią tego, co robi `StationService.Approach`;
        // dwie kopie tej samej wiedzy rozjeżdżają się w chwili, gdy jedna z nich dostaje
        // okno zatrzymania, a druga nie.
        if (_line is not null)
        {
            var nastepna = _line.NextStation;
            if (nastepna is not null)
            {
                name = nastepna.Value.Name;
                distance = nastepna.Value.ChainageM - chainage;
            }
        }
        else if (_stations is not null)
        {
            var approach = _stations.Approach(chainage);
            if (approach.Exists)
            {
                name = approach.Name;
                distance = approach.DistanceM;
            }
        }
        else
        {
            foreach (var station in _axis.Stations)
            {
                if (station.ChainageM >= chainage)
                {
                    name = station.Name;
                    distance = station.ChainageM - chainage;
                    break;
                }
            }
        }

        _hud.Update(
            _state.SpeedKmh, _acceleration, chainage, _axis.LengthM,
            name, distance, _command.Throttle, _command.Brake, _mode,
            StationLine(), SignallingLine(), _viewLine,
            EmergencyBrake.Notice(_activeKeys, _command));
    }

    /// <summary>
    /// Wiersz HUD o sygnalizacji: prędkość dopuszczalna, autorytet jazdy, powód jego
    /// końca i to, czy ochrona pociągu właśnie hamuje za maszynistę.
    ///
    /// <para><b>Wiersz POKAZUJE decyzję, a nie liczy drugiej.</b> Do 04.09.2026 stało tu
    /// własne wołanie <c>Supervise</c> „tylko do pokazania" — ochrona nie ingerowała,
    /// bo to była decyzja o rozgrywce, a nie usterka. Decyzja właściciela zapadła
    /// („ostrzeżenie, potem hamulec służbowy"), ochrona jest w rdzeniu, więc HUD czyta
    /// <c>LineTrain.Protection</c>: dokładnie tę decyzję, która w tym kroku zadziałała.
    /// Drugie wołanie liczyłoby ją z innego stanu (HUD chodzi w klatkach, rdzeń
    /// w krokach) i nie dałoby się powiedzieć, która liczba jest prawdziwa — a przy
    /// okazji emitowałoby zdarzenia sygnalizacji z widoku.</para>
    ///
    /// <para>Bez <c>--signalling</c> wiersz mówi WPROST, że blokad nie ma. Milczenie
    /// wyglądałoby dokładnie tak samo jak „droga wolna", a to dwie różne rzeczy.</para>
    /// </summary>
    private string SignallingLine()
    {
        if (!_lineMode)
        {
            return string.Empty;
        }

        if (_lineCore is null)
        {
            return "bez sygnalizacji — przejazd bez blokad (podaj --signalling)";
        }

        var train = _lineCore.Trains[0];
        if (train.Drive is null || train.Authority is not MovementAuthority authority)
        {
            return "sygnalizacja: skład jeszcze nie wjechał na plan";
        }

        if (train.Protection is not ProtectionDecision decision)
        {
            return "sygnalizacja: linia bez ochrony pociągu";
        }

        var ostrzezenie = decision.Overspeed ? "  PRZEKROCZENIE" : string.Empty;
        var ingerencja = decision.Action == ProtectionAction.None
            ? string.Empty
            : $"  ATP HAMUJE: {decision.Action} {decision.BrakeDemandMps2:F2} m/s²";
        return string.Create(
            CultureInfo.InvariantCulture,
            $"v_dop {Units.MpsToKmh(decision.PermittedSpeedMps),5:F1} km/h   "
            + $"autorytet {authority.DistanceM,7:F0} m ({authority.Reason}, blok {authority.LimitBlockId})   "
            + $"tras {_lineCore.Dispatcher.Locked}/odmów {_lineCore.Dispatcher.Refused}"
            + $"{ostrzezenie}{ingerencja}");
    }

    /// <summary>Wiersz HUD o stacji: cykl drzwi albo dojazd, plus rejestr wywołań.</summary>
    private string StationLine()
    {
        if (_line is not null)
        {
            var zaLinie = _line.Calls.Count;
            if (_line.AtStation)
            {
                var blad = _line.Calls[^1].StopErrorM;
                return string.Create(
                    CultureInfo.InvariantCulture,
                    $"DRZWI {Faza(_line.Phase)}  jeszcze {_line.DwellRemainingSeconds:F1} s  "
                    + $"błąd zatrzymania {blad:+0.00;-0.00;0.00} m   obsłużone {zaLinie}");
            }

            var nastepnaNaLinii = _line.NextStation;
            if (nastepnaNaLinii is null)
            {
                return string.Create(
                    CultureInfo.InvariantCulture, $"koniec przejazdu   obsłużone {zaLinie}");
            }

            return string.Create(
                CultureInfo.InvariantCulture,
                $"{nastepnaNaLinii.Value.Name} za {nastepnaNaLinii.Value.ChainageM - ChainageM:F0} m"
                + $"   obsłużone {zaLinie}");
        }

        if (_stations is null)
        {
            return string.Empty;
        }

        var obsluzone = _stations.Calls.Count;
        var minione = _stations.Missed.Count;
        var licznik = string.Create(
            CultureInfo.InvariantCulture, $"obsłużone {obsluzone}  minięte {minione}");

        if (_stations.AtStation)
        {
            var blokada = _stations.TractionAllowed ? "trakcja WOLNA" : "trakcja ZABLOKOWANA";
            var blad = _stations.Calls[^1].StopErrorM;
            return string.Create(
                CultureInfo.InvariantCulture,
                $"DRZWI {Faza(_stations.Phase)}  jeszcze {_stations.DwellRemainingSeconds:F1} s  " +
                $"({blokada})  błąd zatrzymania {blad:+0.00;-0.00;0.00} m   {licznik}");
        }

        if (_stations.Finished)
        {
            return string.Create(CultureInfo.InvariantCulture, $"brak dalszych stacji   {licznik}");
        }

        var approach = _stations.Approach(ChainageM);
        var okno = approach.WithinWindow ? "  W OKNIE — zatrzymaj się" : string.Empty;
        return string.Create(
            CultureInfo.InvariantCulture,
            $"{approach.Name} za {approach.DistanceM:F0} m (okno ±{_stations.WindowM:F1} m)" +
            $"{okno}   {licznik}");
    }

    private static string Faza(DoorPhase phase) => phase switch
    {
        DoorPhase.Closed => "zamknięte",
        DoorPhase.Unlocking => "odryglowanie",
        DoorPhase.Opening => "otwieranie",
        DoorPhase.Open => "otwarte",
        DoorPhase.ClosingWarning => "sygnał zamykania",
        DoorPhase.Closing => "zamykanie",
        DoorPhase.Checking => "kontrola zamknięcia",
        _ => phase.ToString(),
    };

    // --- zakończenie -------------------------------------------------------------

    private void FinishScriptedRun()
    {
        if (_done)
        {
            return;
        }

        _done = true;
        WriteTelemetry();
        GD.Print(string.Create(
            CultureInfo.InvariantCulture,
            $"[PRZEJAZD] koniec: kroków={_state.Steps} t={_state.TimeSeconds(_step):F3} s " +
            $"chainage={ChainageM:F3} m droga={_state.DistanceM:F3} m klatek={_frames} " +
            $"powód={_scripted!.FinishReason}"));
        GetTree().Quit();
    }

    /// <summary>
    /// Koniec odtworzenia z zapisu wejść: zapis ma skończoną liczbę kroków, więc
    /// przebieg też. To jest jedyny tryb prowadzony poleceniem maszynisty, który
    /// KOŃCZY SIĘ SAM — przejazd z klawiatury nie ma dziś warunku końca
    /// (<c>reports/droga-do-grywalnosci.md</c> §1.4) i to jest osobne zadanie.
    /// </summary>
    private void FinishReplayRun()
    {
        if (_done)
        {
            return;
        }

        _done = true;
        WriteTelemetry();
        WriteInputLog();
        GD.Print(string.Create(
            CultureInfo.InvariantCulture,
            $"[ODTWORZENIE] koniec: kroków={_state.Steps} t={_state.TimeSeconds(_step):F3} s "
            + $"chainage={ChainageM:F3} m droga={_state.DistanceM:F3} m klatek={_frames} "
            + $"zapis={_replayPath}"));
        GetTree().Quit();
    }

    /// <summary>
    /// Zapis wejść na dysk. Idempotentny, bo woła go i koniec przebiegu, i
    /// <see cref="_ExitTree"/> — przejazd z klawiatury nie ma warunku końca, więc
    /// jedynym momentem, w którym plik może powstać, jest wyjście z gry.
    /// </summary>
    private void WriteInputLog()
    {
        if (_inputLogPath is null || _recorder is null || _inputLogWritten)
        {
            return;
        }

        _inputLogWritten = true;
        using var file = FileAccess.Open(_inputLogPath, FileAccess.ModeFlags.Write);
        if (file is null)
        {
            GD.PrintErr($"[WEJŚCIE] nie da się zapisać {_inputLogPath}: {FileAccess.GetOpenError()}");
            return;
        }

        var log = _recorder.Build();

        // `StoreString`, nie `StoreLine`: `InputLog.ToText` kończy każdy wiersz sam,
        // znakiem `\n`. Plik ma wyjść identyczny co do bajtu na każdej maszynie, więc
        // o końcach wierszy decyduje format, a nie silnik.
        file.StoreString(log.ToText());
        GD.Print(string.Create(
            CultureInfo.InvariantCulture,
            $"[WEJŚCIE] {log.Steps} kroków, {log.Entries.Count} zmian klawiszy -> {_inputLogPath}"));
    }

    /// <inheritdoc/>
    public override void _ExitTree()
    {
        // Jedyne miejsce, w którym zapis wejść z przejazdu KLAWIATUROWEGO może powstać:
        // taki przejazd nie kończy się sam, kończy go Esc albo zamknięcie okna.
        WriteInputLog();
        base._ExitTree();
    }

    private void FinishLineRun()
    {
        if (_done)
        {
            return;
        }

        _done = true;
        var result = _line!.Result("arrived");
        GD.Print(string.Create(
            CultureInfo.InvariantCulture,
            $"[LINIA] {result.AxisId}: {result.Calls.Count} zatrzymań, "
            + $"{result.TotalDistanceM:F2} m, {result.TotalSeconds:F2} s, "
            + $"postoje {result.DwellSeconds:F2} s, kroków {result.Steps}, "
            + $"koniec={result.FinishReason}"));
        foreach (var call in result.Calls)
        {
            GD.Print($"[STACJA] {call}");
        }

        WriteCalls(result);
        GetTree().Quit();
    }

    /// <summary>
    /// Zatrzymania do CSV. Format jest ten sam, co wypisuje `Sim.Runner line`, żeby
    /// bramka CI mogła porównać przejazd SCENY z przejazdem RDZENIA — a nie tylko
    /// sprawdzić, że scena czegoś nie wywróciła.
    /// </summary>
    private void WriteCalls(LineRunResult result)
    {
        if (_callsPath is null)
        {
            return;
        }

        using var file = FileAccess.Open(_callsPath, FileAccess.ModeFlags.Write);
        if (file is null)
        {
            Abort(ExitTelemetryWriteFailed,
                $"[STACJE] nie da się zapisać {_callsPath}: {FileAccess.GetOpenError()}");
            return;
        }

        file.StoreLine("name,stop_id,chainage_m,stopped_at_m,stop_error_m,arrival_s,departure_s");
        foreach (var call in result.Calls)
        {
            file.StoreLine(string.Create(
                CultureInfo.InvariantCulture,
                $"{call.Name},{call.StopId},{call.ChainageM:R},{call.StoppedAtChainageM:R},"
                + $"{call.StopErrorM:R},{call.ArrivalSeconds:R},{call.DepartureSeconds:R}"));
        }

        GD.Print($"[STACJE] {result.Calls.Count} zatrzymań -> {_callsPath}");
    }

    private void WriteTelemetry()
    {
        if (_telemetryPath is null)
        {
            return;
        }

        using var file = FileAccess.Open(_telemetryPath, FileAccess.ModeFlags.Write);
        if (file is null)
        {
            Abort(ExitTelemetryWriteFailed,
                $"[TELEMETRIA] nie da się zapisać {_telemetryPath}: {FileAccess.GetOpenError()}");
            return;
        }

        foreach (var line in _telemetry)
        {
            file.StoreLine(line);
        }

        GD.Print($"[TELEMETRIA] {_telemetry.Count - 1} próbek -> {_telemetryPath}");
    }

    /// <summary>
    /// Przewija przejazd do chainage zrzutu. Kroki idą przez tę samą pętlę
    /// <see cref="ScenarioDrive.Step"/>, więc obraz pokazuje stan, który da się
    /// odtworzyć liczbą kroków, a nie „gdzieś tam po drodze".
    /// </summary>
    private void FastForwardToShot()
    {
        if (_lineMode)
        {
            // Warunek jest na TRYB, nie na `_line`, i to jest naprawa trzeciego
            // wystąpienia tej samej usterki w tym pliku. `LineCore` tworzy prowadzenie
            // LENIWIE — dopiero w pierwszym `Step`, w fazie wyjazdów — więc w chwili
            // wejścia tutaj `_line` jest jeszcze NULLEM. Gałąź na `_line is not null`
            // spadała wtedy do przebiegu skryptowego i wchodziła w `_scripted!` na
            // nullu: zrzut wisiał do timeoutu 400 s i nie powstawał żaden plik.
            // Dokładnie tak jak przy `StepOnce` przed #212.
            //
            // Dwa różne cele wymagają dwóch różnych warunków
            // końca i to jest cała treść tego rozgałęzienia.
            //
            // CEL W TUNELU: jedziemy, aż czoło minie zadany kilometraż. Prosto.
            //
            // CEL NA PERONIE: warunek na kilometraż tu NIE WYSTARCZA i to jest zmierzone.
            // Skład staje z błędem −0,3027 m, więc przy celu 509,73 m zatrzymuje się na
            // 509,4267 m — czyli PRZED celem. Pętla na kilometraż przekręcała wtedy cały
            // postój (16,5 s, 1980 kroków) i łapała skład odjeżdżający; wiersz HUD mówił
            // „obsłużone 1", a nie „DRZWI otwarte", więc zrzut wyglądał jak dowód postoju,
            // a był dowodem odjazdu. Druga próba, z czekaniem na otwarte drzwi bez
            // przypisania do stacji, przeskakiwała o jedną stację dalej i kończyła na
            // 1451,6 m. Warunek musi więc mówić trzy rzeczy naraz: skład stoi na stacji,
            // drzwi są otwarte, i to jest TA stacja, w którą celowano.
            var okno = DesignAssumptions.StationStopWindowM;
            var celowaneWPeron = false;
            foreach (var station in _axis.Stations)
            {
                if (Math.Abs(station.ChainageM - _shotChainageM) <= okno)
                {
                    celowaneWPeron = true;
                    break;
                }
            }

            if (celowaneWPeron)
            {
                while (!(_line is not null && _line.Finished)
                       && !(_line is not null
                            && _line.AtStation
                            && _line.Phase == DoorPhase.Open
                            && Math.Abs(ChainageM - _shotChainageM) <= okno)
                       && StepOnce())
                {
                }
            }
            else
            {
                while (!(_line is not null && _line.Finished)
                       && ChainageM < _shotChainageM
                       && StepOnce())
                {
                }
            }
        }
        else
        {
            while (!_scripted!.Finished && ChainageM < _shotChainageM)
            {
                if (!_scripted.Step())
                {
                    break;
                }

                _state = _scripted.State;
                _command = _scripted.Command;
                _acceleration = _scripted.AccelerationMps2;
            }
        }

        PlaceEverything();
        UpdateHud();

        // Widok zamówiony, ale na TYM kilometrażu go nie ma — odmowa, nie podmiana.
        // Warunek stoi tutaj, a nie w `RunPlan`, bo do rozstrzygnięcia potrzeba
        // długości wczytanej skorupy i kilometraża, na którym przewijanie naprawdę
        // stanęło; jedno i drugie jest znane dopiero teraz. `--at-chainage` jest CELEM,
        // a nie wynikiem: w trybie skryptowym przejazd zaczyna się na 94,0 m, więc
        // każdy cel poniżej tej liczby zatrzymuje się na niej.
        if (_view == ViewKind.Chase && !_chaseAvailable)
        {
            var availability = ChaseCameraAim.Availability(
                Math.Min(ChainageM, _axis.LengthM), _train.LengthM);
            Abort(ExitViewUnavailable, string.Create(
                CultureInfo.InvariantCulture,
                $"[ZRZUT] {availability.Reason}; zrzut na {ChainageM:F1} m nie powstaje — "
                + $"kadr byłby płytą pudła, a plik nazywałby się chase"));
            return;
        }

        // Kilka klatek na dojście świateł i materiałów, zanim zapadnie migawka.
        _shotCountdown = 5;
    }

    private void SaveShot()
    {
        if (DisplayServer.GetName() == "headless")
        {
            Abort(ExitHeadlessCannotRender,
                "[ZRZUT] --headless wyłącza renderer; użyj xvfb-run i --rendering-driver opengl3");
            return;
        }

        var image = GetViewport().GetTexture().GetImage();
        var error = image.SavePng(_shotPath!);
        WriteShotMetadata(image.GetWidth(), image.GetHeight());
        GD.Print(string.Create(
            CultureInfo.InvariantCulture,
            $"[ZRZUT] {_shotPath} {image.GetWidth()}x{image.GetHeight()} err={error} widok={_view} " +
            $"kroków={_state.Steps} chainage={ChainageM:F1} m v={_state.SpeedKmh:F1} km/h"));
        GetTree().Quit(error == Error.Ok ? 0 : ExitShotWriteFailed);
    }

    /// <summary>
    /// Metadane zrzutu obok obrazu — <c>&lt;prefiks&gt;_metadata.json</c> w tym samym katalogu.
    ///
    /// `tools/visual/compare.py` porównuje je liczbowo, bo obraz tego nie wykryje:
    /// przesunięcie całej sceny nie zmienia kadru, skoro kamera jedzie razem z nią.
    /// Kształt pola `scene` jest ten sam, co w metadanych Blenderowych, żeby
    /// `check_geometry` nie potrzebowało dwóch ścieżek na dwa silniki.
    ///
    /// Plik jest JEDEN na prefiks, więc kolejne ujęcia go nadpisują. Pole `scene` jest
    /// dla wszystkich pięciu identyczne (ta sama wczytana geometria) i to ono jest tu
    /// treścią; `last_shot` opisuje wyłącznie ostatnie ujęcie i tak się nazywa, żeby
    /// nikt nie odczytał go jako opisu całego zestawu.
    /// </summary>
    private void WriteShotMetadata(int width, int height)
    {
        if (_tunnel is null || _manifest is null || _shotPath is null)
        {
            return;
        }

        var bounds = _tunnel.LoadedBounds();
        var lo = bounds.Position;
        var hi = bounds.End;

        // `vertices` i `faces` szły dotąd z `_manifest.Triangles`, czyli z SUMY CAŁEGO
        // pakietu, niezależnie od tego, co scena naprawdę trzymała. Przy wczytywaniu
        // wszystkiego naraz liczby przypadkiem się zgadzały; przy streamowaniu byłoby
        // to wprost nieprawdą — 3 chunki w pamięci, a w metadanych 16176 ścian.
        // Teraz suma idzie po chunkach REZYDENTNYCH i po tym poziomie, w którym każdy
        // z nich faktycznie wisi, więc bramka porównuje to, co jest na scenie.
        var faces = StreamingPlan.TrianglesFor(_manifest, _tunnel.ResidentLevels);

        // Peron opisany DWA RAZY i to nie jest powtórzenie. Obwiednia wszystkich brył
        // mówi, że coś się wczytało; obwiednia brył PRZY ZRZUCIE mówi, że peron jest
        // TAM, gdzie stanął skład. Pierwsza sama w sobie przepuściłaby peron pakietu
        // wczytany w całości, ale odsunięty od osi — bo bryła długa na 6,7 km zawiera
        // każdy punkt, o który bramka mogłaby zapytać.
        var peronBox = PlatformFit.Merge(_platforms.Slabs) ?? new Aabb();
        var plo = peronBox.Position;
        var phi = peronBox.End;
        var punktOsi = _sceneAxis.CentreLinePoint(Math.Min(ChainageM, _axis.LengthM));
        var przyZrzucie = PlatformFit.Near(_platforms.Slabs, punktOsi, PlatformNearRadiusM);
        var przyZrzucieGora = PlatformFit.TopM(_platforms.Slabs, przyZrzucie) ?? 0.0;
        var directory = _shotPath.Contains('/') ? _shotPath[.._shotPath.LastIndexOf('/')] : ".";
        var name = _shotPath[(_shotPath.LastIndexOf('/') + 1)..];
        var prefix = name.Contains('_') ? name[..name.IndexOf('_')] : "GODOT";
        var path = $"{directory}/{prefix}_metadata.json";
        var json = string.Create(CultureInfo.InvariantCulture, $$"""
        {
         "engine": "godot",
         "engine_version": "{{Engine.GetVersionInfo()["string"]}}",
         "manifest_version": "{{_manifest.Id}}/{{_manifest.Variant}}",
         "resolution": [{{width}}, {{height}}],
         "last_shot": {"view": "{{_view}}", "chainage_m": {{ChainageM:F3}}, "steps": {{_state.Steps}}},
         "scene": {
          "bbox_min": [{{lo.X:F4}}, {{lo.Y:F4}}, {{lo.Z:F4}}],
          "bbox_max": [{{hi.X:F4}}, {{hi.Y:F4}}, {{hi.Z:F4}}],
          "size_m": [{{bounds.Size.X:F4}}, {{bounds.Size.Y:F4}}, {{bounds.Size.Z:F4}}],
          "mesh_objects": {{_tunnel.MeshNodes}},
          "vertices": {{faces * 3}},
          "faces": {{faces}},
          "chunks_loaded": {{_tunnel.LoadedChunks}},
          "chunks_declared": {{_manifest.Chunks.Count}},
          "window_low_m": {{_tunnel.WindowLowM:F3}},
          "window_high_m": {{_tunnel.WindowHighM:F3}},
          "axis_length_m": {{_manifest.AxisLengthM:F3}}
         },
         "platforms": {
          "slabs": {{_platforms.SlabCount}},
          "bbox_min": [{{plo.X:F4}}, {{plo.Y:F4}}, {{plo.Z:F4}}],
          "bbox_max": [{{phi.X:F4}}, {{phi.Y:F4}}, {{phi.Z:F4}}],
          "top_m": {{peronBox.End.Y:F4}},
          "near_shot": {
           "radius_m": {{PlatformNearRadiusM:F3}},
           "slabs": {{przyZrzucie.Count}},
           "top_m": {{przyZrzucieGora:F4}}
          }
         },
         "train": {
          "bodies": {{_train.BodyCount}},
          "length_m": {{_train.LengthM:F4}},
          "width_m": {{_train.WidthM:F4}},
          "roof_height_m": {{_train.RoofHeightM:F4}}
         }
        }
        """);
        using var file = FileAccess.Open(path, FileAccess.ModeFlags.Write);
        if (file is null)
        {
            GD.PushError($"[ZRZUT] nie udało się zapisać metadanych {path}");
            return;
        }

        file.StoreString(json);
        GD.Print($"[ZRZUT] metadane {path}");
    }
}
