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
    private readonly Dictionary<string, string> _args = new(StringComparer.Ordinal);
    private readonly List<string> _telemetry = new();

    private TrackAxis _axis = null!;
    private SceneAxis _sceneAxis = null!;
    private VehicleModel _model = null!;
    private DriveScenario _scenario = null!;
    private RunConditions _conditions = null!;
    private TrainController _controller = null!;
    private DriverInput _input = null!;
    private FixedStep _step;

    private ScenarioDrive? _scripted;
    private DriveState _state;
    private DriverCommand _command = DriverCommand.Coast;
    private double _acceleration;

    private TunnelView _tunnel = null!;
    // Manifest zostaje w polu, bo metadane zrzutu opisują TO, co scena naprawdę wczytała.
    private ChunkManifest? _manifest;
    private TrainView _train = null!;
    private Camera3D _cab = null!;
    private Camera3D _chase = null!;
    private OmniLight3D _headlight = null!;
    private Hud _hud = null!;

    private double _accumulator;
    private long _frames;
    private long _sampleEvery = DriveTelemetry.DefaultSampleEverySteps;
    private long _stepsPerFrame = 120;
    private double _jitter;
    /// <summary>
    /// Kody wyjścia. Były rozsypane po pliku jako literały 3–7; teraz mają nazwy,
    /// bo CI i człowiek czytający log muszą wiedzieć, co je odróżnia.
    /// </summary>
    /// <summary>
    /// Ile wolno się różnić długości osi z manifestu chunków i z rdzenia.
    ///
    /// <para>Nie jest to zapas bezpieczeństwa, tylko rozdzielczość zapisu: manifest
    /// trzyma długość zaokrągloną, a rdzeń liczy ją z zagęszczonej łamanej. Zmierzone
    /// na pakiecie A: |Δ| = 1,335E-005 m. Milimetr jest o dwa rzędy wielkości powyżej
    /// tego rozrzutu i o sześć rzędów poniżej rozjazdu, który ma łapać.</para>
    /// </summary>
    private const double AxisManifestToleranceM = 1e-3;

    private const int ExitMissingInput = 3;

    private const int ExitMissingAssets = 4;

    private const int ExitTelemetryWriteFailed = 5;

    private const int ExitHeadlessCannotRender = 6;

    private const int ExitShotWriteFailed = 7;

    private const int ExitUnknownArgument = 8;

    private const int ExitBadArgumentValue = 9;

    private const int ExitAxisManifestMismatch = 10;

    private bool _scriptedMode;

    /// <summary>Scena zgłosiła błąd i nie ma prawa dalej liczyć klatek.</summary>
    private bool _aborted;

    private string _mode = "manual";
    private string? _telemetryPath;
    private string? _shotPath;
    private double _shotChainageM;
    private int _shotCountdown = int.MaxValue;
    private ViewKind _view = ViewKind.Cab;
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
            _telemetry.Add(DriveTelemetry.Row(_scripted!));
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
    /// Wszystkie argumenty, które scena rozumie. Lista jest jawna, bo argument spoza
    /// niej ma zatrzymać przebieg, a nie zostać po cichu zignorowany.
    ///
    /// <para><b>Zmierzone 02.09.2026 audytem mutacyjnym.</b> Przed tą zmianą
    /// <c>--at-chainag=2000</c> — literówka na jednym znaku — kończyło się kodem 0
    /// i zrzutem o nazwie <c>GODOT_cab_2000m.png</c> przedstawiającym stojący skład
    /// na 94 m. <c>--view=zmyslony</c> cicho spadało do widoku z kabiny. Pięć „ujęć
    /// kontrolnych" mogło więc być pięcioma kopiami tego samego kadru, a wszystkie
    /// opisy kamer z <c>cameras.json</c> („najciaśniejszy łuk R = 91,5 m", „szew
    /// chunków c01/c02") były niesprawdzalnymi deklaracjami.</para>
    /// </summary>
    private static readonly string[] KnownArguments =
    {
        "telemetry", "shot", "sample-every", "steps-per-frame", "jitter",
        "at-chainage", "view", "axis", "no-geometry", "assets", "manifest", "shell",
    };

    /// <summary>Widoki, jakie scena potrafi ustawić. Inna wartość jest błędem, nie domyślną.</summary>
    private static readonly string[] KnownViews = { "cab", "chase", "outside" };

    private void ParseArguments()
    {
        foreach (var argument in OS.GetCmdlineUserArgs())
        {
            var text = argument.TrimStart('-');
            var split = text.IndexOf('=');
            if (split < 0)
            {
                _args[text] = "1";
            }
            else
            {
                _args[text[..split]] = text[(split + 1)..];
            }
        }

        foreach (var name in _args.Keys)
        {
            if (Array.IndexOf(KnownArguments, name) < 0)
            {
                Abort(ExitUnknownArgument,
                    $"[ARGUMENT] nieznany argument '--{name}'. Znane: --{string.Join(" --", KnownArguments)}");
                return;
            }
        }

        _telemetryPath = Argument("telemetry");
        _shotPath = Argument("shot");
        _scriptedMode = _telemetryPath is not null || _shotPath is not null;
        _mode = _telemetryPath is not null ? "telemetry" : _shotPath is not null ? "shot" : "manual";

        if (!TryLong("sample-every", 120L, out _sampleEvery)
            || !TryLong("steps-per-frame", 120L, out _stepsPerFrame)
            || !TryDouble("jitter", 0.0, out _jitter)
            || !TryDouble("at-chainage", 0.0, out _shotChainageM))
        {
            return;
        }

        var view = Argument("view") ?? "cab";
        if (Array.IndexOf(KnownViews, view) < 0)
        {
            Abort(ExitBadArgumentValue,
                $"[ARGUMENT] nieznany widok '--view={view}'. Znane: {string.Join(", ", KnownViews)}");
            return;
        }

        _view = view switch
        {
            "chase" => ViewKind.Chase,
            "outside" => ViewKind.Outside,
            _ => ViewKind.Cab,
        };
    }

    private bool TryLong(string name, long fallback, out long value)
    {
        var text = Argument(name);
        if (text is null)
        {
            value = fallback;
            return true;
        }

        if (long.TryParse(text, NumberStyles.Integer, CultureInfo.InvariantCulture, out value))
        {
            return true;
        }

        Abort(ExitBadArgumentValue, $"[ARGUMENT] '--{name}={text}' nie jest liczbą całkowitą");
        return false;
    }

    private bool TryDouble(string name, double fallback, out double value)
    {
        var text = Argument(name);
        if (text is null)
        {
            value = fallback;
            return true;
        }

        if (double.TryParse(text, NumberStyles.Float, CultureInfo.InvariantCulture, out value)
            && double.IsFinite(value))
        {
            return true;
        }

        // Bez tego `double.Parse` rzucał wyjątkiem w środku `_Ready`, `_shotPath` było
        // już ustawione, a `_Process` wchodziło w odliczanie od int.MaxValue i kręciło
        // się w nieskończoność. Zmierzone: `--at-chainage=abc` nie dawało ani PNG-a,
        // ani kodu błędu — w CI to wypalony `timeout-minutes: 45` bez informacji.
        Abort(ExitBadArgumentValue, $"[ARGUMENT] '--{name}={text}' nie jest skończoną liczbą");
        value = fallback;
        return false;
    }

    private string? Argument(string name) => _args.TryGetValue(name, out var value) ? value : null;

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

        // Pochylenie 0 nie jest wyborem: profil pionowy pakietu A ma status
        // not_modelled, a docs/21-measured-vs-assumed.md §3 zabrania wyprowadzania
        // z niego rzędnych. Otoczenie Tunnel wynika z geometrii pakietu A.
        _conditions = new RunConditions(
            _model.MassKg(TrainLoad.Aw2),
            0.0,
            _model.Adhesion(RailCondition.Dry),
            TrackEnvironment.Tunnel);

        _controller = new TrainController(_model);
        _input = new DriverInput(DesignAssumptions.ControlNotchRatePerSecond);
        _state = DriveState.AtRest;

        if (_scriptedMode)
        {
            _scripted = new ScenarioDrive(_controller, _scenario, _conditions, _step);
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

        _tunnel.LoadAll(manifest, Path.GetDirectoryName(manifestPath) ?? assets, tunnelMaterial);
        _train.Load(shellPath, trainMaterial);

        GD.Print(_tunnel.Describe(manifest));
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
        GD.Print(string.Create(
            CultureInfo.InvariantCulture,
            $"[PRZEJAZD] tryb={_mode} widok={_view} scenariusz={_scenario.Id} " +
            $"krok=1/{FixedStep.SimulationHertz} s masa={_conditions.MassKg:F0} kg " +
            $"limit={Units.MpsToKmh(_scenario.SpeedLimitMps):F1} km/h"));
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

        if (!_scriptedMode)
        {
            _command = _input.Poll(delta);
            HandleViewKeys();
        }

        AdvanceBy(_scriptedMode ? SyntheticFrameSeconds() : delta);
        PlaceEverything();
        UpdateHud();

        if (_scriptedMode && (_scripted?.Finished ?? false))
        {
            FinishScriptedRun();
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
    {
        var baseSeconds = _stepsPerFrame * _step.Seconds;
        return _jitter <= 0.0
            ? baseSeconds
            : baseSeconds * (1.0 + (_jitter * Math.Sin(_frames * 1.7)));
    }

    private long AdvanceBy(double seconds)
    {
        if (seconds <= 0.0)
        {
            return 0;
        }

        _accumulator += seconds;
        var executed = 0L;
        while (_accumulator >= _step.Seconds)
        {
            _accumulator -= _step.Seconds;
            if (!StepOnce())
            {
                _accumulator = 0.0;
                break;
            }

            executed++;
        }

        return executed;
    }

    private bool StepOnce()
    {
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

        _state = _controller.Advance(
            _state, _conditions, _command, _scenario.SpeedLimitMps, _step, out var forces);
        _acceleration = forces.AccelerationMps2;
        return true;
    }

    private double ChainageM => _scenario.StartChainageM + _state.DistanceM;

    // --- widok -------------------------------------------------------------------

    private void ApplyView()
    {
        _cab.Current = _view == ViewKind.Cab;
        _chase.Current = _view != ViewKind.Cab;

        // Z kabiny nie widać własnego pudła: kamera stoi wewnątrz skorupy M7, a ta ma
        // po solidify obie powierzchnie, więc bez ukrycia składu widać z bliska jego
        // wnętrze i nic poza tym. Kabina jako model wnętrza nie istnieje (T-220 jej
        // świadomie nie robi), więc jedyne uczciwe rozwiązanie to schować bryłę.
        _train.Visible = _view != ViewKind.Cab;
    }

    private void PlaceEverything()
    {
        var chainage = Math.Min(ChainageM, _axis.LengthM);
        var trainLength = _train.LengthM > 0.0 ? _train.LengthM : 94.0;

        if (_train.BodyCount > 0)
        {
            _train.PlaceAt(_sceneAxis, chainage);
        }

        var (eye, forward) = _sceneAxis.CabPoint(
            chainage,
            DesignAssumptions.CabEyeSetbackM,
            DesignAssumptions.CabEyeHeightM,
            DesignAssumptions.CabEyeLateralM);
        _cab.LookAtFromPosition(eye, eye + forward, Vector3.Up);

        var middle = _sceneAxis.CabPoint(chainage - (trainLength * 0.5), 0.0, 1.8, 0.0).Position;

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
            var behind = Math.Max(0.0, chainage - trainLength - DesignAssumptions.ChaseBehindM);
            var (position, _) = _sceneAxis.CabPoint(
                behind, 0.0, DesignAssumptions.ChaseHeightM, DesignAssumptions.CabEyeLateralM);
            _chase.LookAtFromPosition(position, middle, Vector3.Up);
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
            _accumulator = 0.0;
            _input.Set(DriverCommand.Coast);
            _command = DriverCommand.Coast;
        }

        _resetKeyHeld = resetKey;
    }

    private void UpdateHud()
    {
        var chainage = ChainageM;
        var name = "koniec pakietu";
        var distance = _axis.LengthM - chainage;
        foreach (var station in _axis.Stations)
        {
            if (station.ChainageM >= chainage)
            {
                name = station.Name;
                distance = station.ChainageM - chainage;
                break;
            }
        }

        _hud.Update(
            _state.SpeedKmh, _acceleration, chainage, _axis.LengthM,
            name, distance, _command.Throttle, _command.Brake, _mode);
    }

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

        PlaceEverything();
        UpdateHud();

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
    /// Metadane zrzutu obok obrazu — `<prefiks>_metadata.json` w tym samym katalogu.
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
          "vertices": {{_manifest.Triangles * 3}},
          "faces": {{_manifest.Triangles}},
          "chunks_loaded": {{_tunnel.LoadedChunks}},
          "chunks_declared": {{_manifest.Chunks.Count}},
          "axis_length_m": {{_manifest.AxisLengthM:F3}}
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
