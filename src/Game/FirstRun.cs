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

    /// <summary>
    /// Kamera inspekcyjna: stoi na osi tunelu przy zadanym kilometrażu i patrzy
    /// wzdłuż niego, <b>nie czekając na skład</b>. Trzy pozostałe widoki są widokami
    /// JAZDY i wymagają, żeby pojazd do oglądanego miejsca dojechał — przy 6.C4
    /// zmierzone: zrzut z kilometrażu 2521,1 m kosztuje <b>14 686 kroków</b>
    /// symulacji. Ten widok kosztuje ich zero, bo geometrię bierze z osi, a nie
    /// z pozycji pojazdu.
    /// </summary>
    Inspect,
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
/// <b>Pięć trybów.</b> (Wykaz jest PRZEPISANY, a nie dopisany obok: mówił „trzy tryby"
/// przy trzech wymienionych i nie znał ani <c>--replay</c>, ani <c>--from-telemetry</c>.
/// Szósty tryb — <c>--line</c> — jest osobno, w <see cref="RunPlan.LineMode"/>.)
/// <list type="bullet">
/// <item>bez argumentów — prowadzenie z klawiatury;</item>
/// <item><c>--telemetry=PLIK</c> — przejazd po zapisanym scenariuszu, bez interakcji,
/// z telemetrią w formacie rdzenia. To jest odpowiednik testu: te same liczby przy
/// każdym powtórzeniu i te same, co z <c>src/Sim.Runner</c>;</item>
/// <item><c>--replay=PLIK</c> — odtworzenie ZAPISU WEJŚĆ maszynisty, tą samą drogą
/// przez fizykę, co człowiek przy klawiaturze;</item>
/// <item><c>--from-telemetry=PLIK</c> — odtworzenie ZAPISANEGO WYNIKU jako ruchu
/// zadanego: fizyka nie liczy się ani razu, scena jest czystym widokiem przejazdu,
/// który już się odbył;</item>
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
    private SceneAxis? _visualTailAxis;
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
    private readonly BrakingCueMemory _brakingCueMemory = new();

    private FixedStep _step;

    private ScenarioDrive? _scripted;
    private StationService? _stations;

    /// <summary>
    /// Sesja treningowa albo <c>null</c> poza trybem ręcznym — warunek końca przejazdu
    /// gracza (MB-02). <b>Nie ustawia <c>_done</c></b> i to jest cała treść tego pola:
    /// <c>_done</c> powoduje <c>return</c> w <see cref="_Process"/> PRZED odczytem
    /// klawiatury, więc odciąłby <c>R</c>, <c>Esc</c> i <c>C</c> — czyli dokładnie te
    /// trzy klawisze, których panel wyniku potrzebuje (punkty 4 i 5 odbioru M1).
    /// Koniec SESJI i koniec PROCESU są tu dwiema różnymi rzeczami.
    /// </summary>
    private TrainingSession? _training;

    /// <summary>
    /// Czy wiersz <c>[SESJA]</c> już poszedł do logu. Jedno pole, bo wypis ma być
    /// JEDNORAZOWY, a gałąź, która go robi, wykonuje się w KAŻDEJ klatce panelu wyniku
    /// — bez tego log dostałby ten sam wiersz sześćdziesiąt razy na sekundę.
    ///
    /// <para>Reset zdejmuje ten znacznik razem z wynikiem, bo ponowiona sesja skończy
    /// się własnym wynikiem i on też ma być widoczny.</para>
    /// </summary>
    private bool _summaryPrinted;
    private LineDrive? _line;
    private LineCore? _lineCore;
    private LineEntryDispatcher? _lineDispatcher;

    /// <summary>
    /// Sesja linii z maszynistą — 6.M1. Jedna droga kroku i poleceń dla klawiatury,
    /// odtworzenia z zapisu i <c>Sim.Runner replay --line</c>; powód przy
    /// <see cref="LineSession"/>.
    /// </summary>
    private LineSession? _lineSession;

    /// <summary>
    /// Plan sygnalizacji, z którego tryb ręczny bierze prędkość dopuszczalną;
    /// <c>null</c> w trybie linii i w przebiegu skryptowym. Plan jest tu CZYTANY,
    /// a nie prowadzi — patrz <see cref="RunPlan.ManualSpeedLimitPlanPath"/>.
    /// </summary>
    private SignallingPlan? _manualPlan;

    /// <summary>
    /// Ochrona pociągu dla KABINY: bloki, nastawnia, autorytet jazdy i ingerencja
    /// w polecenie człowieka. <c>null</c> poza trybem ręcznym pod <c>--signalling</c>
    /// — i wtedy przejazd jest bit w bit taki, jak przed wprowadzeniem G-5.
    ///
    /// <para>Nie jest to drugi <see cref="LineCore"/>. <see cref="LineDrive"/> uznaje
    /// zatrzymanie za wywołanie stacji przy <c>chainage &gt;= cel − okno</c>, bez
    /// ograniczenia z góry — dla człowieka znaczyłoby to drzwi otwarte 200 m za peronem
    /// (<c>reports/droga-do-grywalnosci.md</c> §5.3). Regułę stacji ma tu
    /// <see cref="StationService"/> i to ona zostaje; <see cref="CabProtection"/> nie wie
    /// o stacjach nic.</para>
    /// </summary>
    private CabProtection? _cabProtection;

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
    private bool _terminalBrakeEngaged;

    private double _acceleration;

    private TunnelView _tunnel = null!;
    // Manifest zostaje w polu, bo metadane zrzutu opisują TO, co scena naprawdę wczytała.
    private ChunkManifest? _manifest;
    private string _assetDirectory = string.Empty;
    private StandardMaterial3D? _tunnelMaterial;
    private bool _hasTrackDetail;
    private readonly List<OmniLight3D> _trackLights = new();
    private int _lightAnchor = int.MinValue;
    private TrainView _train = null!;

    /// <summary>
    /// Widoki składów po NAZWIE — MB-07. Skład zerowy jest tu pod
    /// <see cref="SignalledTrainId"/> i jest TYM SAMYM obiektem co <see cref="_train"/>.
    /// </summary>
    /// <remarks>
    /// <para><b>Dlaczego mapa, a nie lista równoległa do <c>LineCore.Trains</c>.</b>
    /// Bo równoległość dwóch list jest niesprawdzalna: rozjeżdżają się po cichu przy
    /// pierwszym składzie, który wejdzie albo zejdzie w innej kolejności, a skutkiem
    /// jest widok jadący po cudzym kilometrażu — czyli obraz, który wygląda poprawnie
    /// i nie zgadza się z niczym. Klucz po nazwie rozjechać się nie może: albo widok
    /// dla tej nazwy jest, albo go nie ma.</para>
    /// </remarks>
    private readonly Dictionary<string, TrainView> _trainViews = new(StringComparer.Ordinal);

    /// <summary>Indeks składu OBSERWOWANEGO w <c>LineCore.Trains</c> — MB-07.</summary>
    private int _observed;

    private bool _trainNextKeyHeld;
    private bool _trainTakeKeyHeld;
    private bool _trainReleaseKeyHeld;
    private bool _doorOpenKeyHeld;
    private bool _doorCloseKeyHeld;

    /// <summary>
    /// Ostatnia ODMOWA polecenia drzwi; <c>null</c>, gdy ostatnie polecenie przeszło
    /// albo gdy nie było żadnego (MB-08).
    ///
    /// <para><b>Trzyma się jej do NASTĘPNEGO polecenia, a nie przez N klatek.</b>
    /// Komunikat gasnący po czasie ściennym byłby jedyną rzeczą w tej scenie, która
    /// zależy od tego, ile klatek zdążyło się narysować — a determinizm tego przejazdu
    /// jest przybity bramką porównującą telemetrię co do bitu. Odmowa gaśnie, gdy
    /// gracz zrobi coś, co się udaje, albo gdy postój się kończy; do tego czasu stoi
    /// na ekranie, bo dokładnie tak długo jest prawdziwa.</para>
    /// </summary>
    private DoorRefusal? _doorRefusal;

    /// <summary>Widok składu obserwowanego, albo <see cref="_train"/> poza trybem linii.</summary>
    private TrainView ObservedTrainView()
    {
        if (_lineCore is null || _lineCore.Trains.Count == 0)
        {
            return _train;
        }

        var id = _lineCore.Trains[Math.Clamp(_observed, 0, _lineCore.Trains.Count - 1)].Id;
        return _trainViews.TryGetValue(id, out var widok) ? widok : _train;
    }

    private CabView _cabView = null!;
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
    /// Identyfikator składu w sygnalizacji. Jeden na całą scenę, bo sygnalizacja linii
    /// (<c>LineCore</c>) i sygnalizacja kabiny (<c>CabProtection</c>) nigdy nie działają
    /// naraz, a zdarzenia obu stron mają dać się porównać z rdzeniem po NAZWIE, a nie po
    /// domysłach — <c>Sim.Runner</c> używa tego samego napisu.
    /// </summary>
    private const string SignalledTrainId = LineSession.CabTrainId;

    /// <summary>
    /// Nazwa składu o indeksie <paramref name="index"/> — MB-07.
    /// </summary>
    /// <remarks>
    /// <para><b>Skład zerowy zachowuje nazwę <c>KABINA</c> i to nie jest sentyment.</b>
    /// Ta nazwa stoi w wierszach telemetrii, w pliku zatrzymań i w <c>Sim.Runner</c>,
    /// a bramka CI porównuje obie strony PO NAZWIE. Przemianowanie go na „SKLAD-01"
    /// rozjechałoby scenę z rdzeniem w każdym przebiegu, w którym składów jest jeden —
    /// czyli w każdym dzisiejszym.</para>
    /// </remarks>
    private static string TrainIdAt(int index) => LineSession.TrainIdAt(index);

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

    /// <summary>
    /// Kabina się nie wczytała. Odmowa tą samą drogą co przy skorupie i peronach —
    /// i z tego samego powodu, który Issue #107 zmierzyło dwa razy.
    ///
    /// <para><b>Scena bez kabiny wygląda dziś DOKŁADNIE tak, jak wyglądała poprawnie
    /// przed MB-05</b>, i to jest cała treść tej stałej. Kamera kabinowa stoi wewnątrz
    /// skorupy, a skorupa jest w tym widoku ukryta, więc brak wnętrza daje kadr z samym
    /// tunelem — czyli obraz, który <c>godot-first-run.yml</c> sprawdzał i uznawał za
    /// dobry przez cały czas, kiedy kabiny nie było. Bramka oglądająca metryki klatki
    /// nie ma tu czego zauważyć: klatka jest poprawna, tylko pokazuje o jeden przedmiot
    /// mniej, niż powinna.</para>
    /// </summary>
    private const int ExitCabMissing = 14;

    private bool _scriptedMode;
    private bool _lineMode;

    /// <summary>Przejazd odtwarzany z zapisu wejść (<c>--replay</c>).</summary>
    private bool _replayMode;

    /// <summary>
    /// Czy przy sterowaniu siedzi człowiek — rozstrzyga to
    /// <see cref="RunPlan.ReadsKeyboard"/>, a nie osobny warunek tutaj.
    ///
    /// <para>Pole odpowiada na to samo pytanie w dwóch miejscach pętli: czy wołać
    /// <see cref="DriverInput.Read"/> i czy HUD ma pokazać wiersz pomocy. Wcześniej
    /// pierwsze z nich miało własny warunek <c>!_scriptedMode &amp;&amp; !_replayMode</c>,
    /// a drugiego nie było wcale, bo wiersza pomocy nie było.</para>
    /// </summary>
    private bool _readsKeyboard;

    /// <summary>Zapis wejść do odtworzenia; <c>null</c> poza <c>--replay</c>.</summary>
    private InputLog? _replay;

    /// <summary>Zbieranie wejść do zapisu; <c>null</c> bez <c>--input-log</c>.</summary>
    private InputLogRecorder? _recorder;

    /// <summary>Przejazd odtwarzany z pliku telemetrii jako ruch zadany (<c>--from-telemetry</c>).</summary>
    private bool _fromTelemetryMode;

    /// <summary>Wczytany zapis telemetrii; <c>null</c> poza <c>--from-telemetry</c>.</summary>
    private TelemetryTrack? _track;

    /// <summary>Numer próbki, którą scena właśnie pokazuje.</summary>
    private int _trackIndex;

    /// <summary>
    /// Głowica odtwarzania: numer kroku, do którego doszło odtwarzanie.
    ///
    /// <para>Osobna od <c>_state.Steps</c>, i to nie jest duplikat. <c>_state</c>
    /// przeskakuje w tym trybie z próbki na próbkę — o 120 kroków przy domyślnej
    /// gęstości — a głowica idzie po JEDNYM kroku, bo to ona decyduje, kiedy wypada
    /// następna próbka. Gdyby zegar odtwarzania był tym samym polem, co stan, przejazd
    /// przyjmowałby każdą próbkę natychmiast i cały plik wyszedłby w jednej klatce:
    /// telemetria zgadzałaby się co do bajtu, a ruchu nie byłoby żadnego.</para>
    /// </summary>
    private long _playbackStep;

    private string? _inputLogPath;
    private string? _replayPath;
    private string? _fromTelemetryPath;

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

    /// <summary>
    /// Numer kroku w SESJI — rośnie zawsze i nie wraca po resecie. Zapis wejść jest po
    /// nim indeksowany, bo <c>_state.Steps</c> po resecie zaczyna od zera i dwa różne
    /// momenty dostałyby ten sam numer.
    /// </summary>
    private long _logStep;

    /// <summary>
    /// Reset zamówiony klawiszem w tej klatce, czekający na granicę kroku.
    ///
    /// <para>Reset musi paść MIĘDZY krokami, a nie w środku klatki, i to jest ten sam
    /// powód, dla którego przesuw nastawnika przeniósł się do <c>StepOnce</c> (#239):
    /// zdarzenie wykonane w rytmie klatek trafia w inny krok przy 60 i przy 120 kl./s,
    /// więc zapis wejść opisywałby przejazd, którego nie da się odtworzyć.</para>
    /// </summary>
    private bool _resetPending;
    private bool _lineCompletionReported;

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
        _cabView = GetNode<CabView>("Cab");
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
            //
            // W RUCHU ZADANYM wiersz zerowy jest PIERWSZĄ PRÓBKĄ PLIKU, przepisaną
            // z jej własną fazą. `ManualTelemetryRow` wpisałby tu `manual` i echo
            // rozjechałoby się z oryginałem w dziesiątej kolumnie już w pierwszym
            // wierszu — a `compare` odrzuca różnicę fazy przed policzeniem czegokolwiek.
            //
            // W ODTWORZENIU LINII (6.M1) wiersza zerowego nie ma: skład wchodzi na plan
            // dopiero w pierwszym kroku linii, więc stanu „przed pierwszym krokiem" nie
            // ma czym opisać — i tak samo nie wypisuje go `Sim.Runner replay --line`.
            if (!_lineMode)
            {
                _telemetry.Add(_scripted is not null
                    ? DriveTelemetry.Row(_scripted)
                    : _track is not null
                        ? FromTelemetryRow()
                        : ManualTelemetryRow());
            }
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
        _readsKeyboard = plan.ReadsKeyboard;
        _fromTelemetryMode = plan.FromTelemetryMode;
        _inputLogPath = plan.InputLogPath ?? DomyslnyZapisWejsc(plan);
        _replayPath = plan.ReplayPath;
        _fromTelemetryPath = plan.FromTelemetryPath;
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

    /// <summary>
    /// Domyślna ścieżka do zasobu — z KATALOGU REPOZYTORIUM w checkoucie, a z katalogu
    /// obok BINARKI w paczce dla gracza (MB-04).
    ///
    /// <para><b>Dlaczego to nie może zostać przy samym <c>res://</c>.</b> Zmierzone
    /// 14.09.2026 własną sondą, na wyeksportowanej paczce uruchomionej z dwóch różnych
    /// katalogów bieżących: <c>ProjectSettings.GlobalizePath("res://")</c> zwraca
    /// wtedy <b>NAPIS PUSTY</b>. Poprzednia wersja tej metody sklejała z niego
    /// <c>"../../" + relative</c>, więc w paczce dawała ścieżkę WZGLĘDNĄ do katalogu
    /// bieżącego PROCESU — bez żadnego związku z tym, gdzie leży gra. Gracz, który
    /// kliknie ikonę, dostawał dwa poziomy nad przypadkowym katalogiem i pustą scenę
    /// albo <c>[ZASOBY] brak manifestu</c>, zależnie od tego, skąd akurat uruchomił.</para>
    ///
    /// <para><b>Rozstrzygnięcie: pytamy o BINARKĘ, nie o <c>res://</c>.</b>
    /// <c>OS.GetExecutablePath()</c> jest bezwzględna i poprawna w OBU układach —
    /// to też jest zmierzone tą samą sondą, a nie przyjęte. W checkoucie binarką jest
    /// silnik leżący poza drzewem, więc tam nadal rozstrzyga <c>res://</c>; w paczce
    /// binarką jest sama gra i zasoby leżą obok niej.</para>
    ///
    /// <para><b>Jak odróżniamy jeden układ od drugiego.</b> Po tym samym, co się różni:
    /// pusty wynik <c>GlobalizePath</c> znaczy „zasoby są w paczce", bo katalog
    /// projektu nie istnieje na dysku. Warunek nie zgaduje po nazwie pliku ani po
    /// zmiennej środowiskowej — pyta o tę jedną rzecz, która naprawdę się zmienia.</para>
    /// </summary>
    /// <param name="relative">Ścieżka względna, np. <c>data/track/L1_A.json</c>.</param>
    private static string RepoPath(string relative)
    {
        var projectDirectory = ProjectSettings.GlobalizePath("res://");
        if (projectDirectory.Length > 0)
        {
            return Path.GetFullPath(Path.Combine(projectDirectory, "..", "..", relative));
        }

        // PACZKA. Zasoby leżą w podkatalogu `zasoby/` obok binarki — jeden katalog,
        // a nie dwa poziomy w górę, bo w paczce nie ma nad czym iść w górę.
        var exeDirectory = OS.GetExecutablePath().GetBaseDir();
        return Path.GetFullPath(Path.Combine(exeDirectory, PackageAssetsDirectory, relative));
    }

    /// <summary>
    /// Nazwa katalogu z zasobami runtime w paczce dla gracza. Stoi w JEDNYM miejscu,
    /// bo czyta ją i scena, i <c>tools/release/package-playable.sh</c>, a dwie kopie
    /// rozjechałyby się przy pierwszej zmianie układu paczki — wtedy gra szukałaby
    /// zasobów tam, gdzie skrypt ich nie położył, i nie powiedziałaby dlaczego.
    /// </summary>
    public const string PackageAssetsDirectory = "zasoby";

    /// <summary>
    /// Katalog z wygenerowaną geometrią: <c>build/t400</c> w checkoucie, a SAM
    /// <c>zasoby/</c> w paczce dla gracza.
    ///
    /// <para><b>Dlaczego to nie może być <c>RepoPath("build/t400")</c>, choć tak było
    /// do 14.09.2026.</b> Zmierzone na wyeksportowanej paczce uruchomionej spoza
    /// checkoutu, ze ścieżki ze spacjami: scena szukała wtedy manifestu pod
    /// <c>…/MetroBXL/zasoby/build/t400/chunks/L1_A-chunks.json</c> i kończyła się
    /// <c>[ASSETS] brak manifestu</c> z kodem 4. Ścieżka składała się poprawnie —
    /// niepoprawna była jej TREŚĆ: <c>build/t400</c> to nazwa katalogu WYJŚCIOWEGO
    /// generatorów w drzewie źródeł, a w paczce nie ma ani generatorów, ani drzewa.</para>
    ///
    /// <para><b>Dlaczego nie odwrotnie — dołożeniem <c>build/t400/</c> w skrypcie
    /// pakującym.</b> Bo wtedy gracz dostaje w swojej paczce katalog o nazwie
    /// „build", czyli nazwę cudzego procesu budowania, i pierwsza zmiana katalogu
    /// wyjściowego generatorów (dziś <c>t400</c>, jutro inny) cicho rozjeżdża paczkę
    /// z grą. Układ paczki ma zależeć od paczki, a nie od tego, jak nazywa się
    /// katalog roboczy w repozytorium.</para>
    ///
    /// <para>Rozróżnienie idzie po tym samym warunku co w <see cref="RepoPath"/> —
    /// pustym wyniku <c>GlobalizePath("res://")</c> — żeby nie było dwóch niezależnych
    /// odpowiedzi na jedno pytanie „czy to paczka".</para>
    /// </summary>
    private static string AssetsRoot()
    {
        var projectDirectory = ProjectSettings.GlobalizePath("res://");
        if (projectDirectory.Length > 0)
        {
            return Path.GetFullPath(Path.Combine(projectDirectory, "..", "..", "build", "t400"));
        }

        return Path.GetFullPath(
            Path.Combine(OS.GetExecutablePath().GetBaseDir(), PackageAssetsDirectory));
    }

    /// <summary>
    /// Domyślne miejsce zapisu wejść maszynisty, gdy nie podano <c>--input-log</c>:
    /// <c>user://zapisy/ostatni-przejazd.log</c> — albo <c>null</c>, gdy przejazdem
    /// nie kieruje człowiek.
    ///
    /// <para><b>Dlaczego to w ogóle powstało (MB-04, 14.09.2026).</b> Bez tej metody
    /// <c>_recorder</c> tworzył się WYŁĄCZNIE przy jawnym <c>--input-log</c>, więc
    /// gracz uruchamiający paczkę dwukliknięciem nie zapisywał niczego. Pole
    /// „Skończone, gdy" pozycji MB-04 wymaga wprost, żeby „logi trafiały do katalogu
    /// użytkownika", a napisany wcześniej `CZYTAJ-TO-NAJPIERW.txt` już to GŁOSIŁ —
    /// czyli paczka obiecywała rzecz, której nie robiła. Zapis jest tu dokładany,
    /// a nie obietnica usuwana, bo to zapis jest treścią pozycji.</para>
    ///
    /// <para><b>Tylko przejazd prowadzony z klawiatury.</b> <c>--replay</c>,
    /// <c>--line</c>, <c>--shot</c> i przebieg skryptowy dostają <c>null</c>: zapis
    /// WEJŚĆ MASZYNISTY z przejazdu, którego maszynista nie prowadził, byłby zapisem
    /// wejść, których nikt nie wcisnął. Warunek pyta <c>plan.ReadsKeyboard</c>, czyli
    /// tę jedną rzecz, która to rozstrzyga, a nie o tryb z nazwy.</para>
    ///
    /// <para><b><c>user://</c>, a nie katalog obok binarki.</b> Paczka bywa rozpakowana
    /// tam, gdzie gracz nie ma prawa zapisu, a <c>user://</c> jest jedyną ścieżką,
    /// którą Godot gwarantuje jako zapisywalną na każdej z platform. Na Linuksie
    /// wychodzi z tego <c>~/.local/share/godot/app_userdata/&lt;projekt&gt;/</c>.</para>
    ///
    /// <para><b>Jedna nazwa, nadpisywana.</b> Znacznik czasu w nazwie dawałby katalog
    /// rosnący bez granicy, którego nikt nigdy nie sprząta. Nadpisywanie jest wyborem
    /// i dlatego stoi wypisane w <c>CZYTAJ-TO-NAJPIERW.txt</c>, a nie tylko tutaj.</para>
    /// </summary>
    private static string? DomyslnyZapisWejsc(RunPlan plan)
    {
        if (!plan.ReadsKeyboard)
        {
            return null;
        }

        const string katalog = "user://zapisy";
        using var dostep = DirAccess.Open("user://");
        if (dostep is not null && !dostep.DirExists("zapisy"))
        {
            var blad = dostep.MakeDir("zapisy");
            if (blad != Error.Ok)
            {
                GD.PrintErr($"[WEJŚCIE] nie da się założyć {katalog}: {blad}");
                return null;
            }
        }

        return $"{katalog}/ostatni-przejazd.log";
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

        // Plik ZŁY, a nie tylko brakujący, kończy się odmową — 6.D235. Ten sam filtr co
        // w `ReadSignallingPlan` i `ReadInputLog`, i z tego samego powodu: wpuszcza
        // WYŁĄCZNIE typy, które rzuca `src/Sim/`, a te rzuty są po polsku. Oś powstaje
        // przed wszystkim innym, więc bez tej osłony uszkodzony plik osi był pierwszym,
        // na czym gracz się potykał — zrzutem środowiska zamiast wierszem odmowy.
        // Klauzula druga łapie dokument poprawny składniowo, ale innego kształtu
        // (`BadFile`): na osi `[]` scena bez niej nie kończyła się, tylko wisiała.
        try
        {
            _axis = TrackAxis.FromJson(file.GetAsText());
        }
        catch (Exception error) when (error is ArgumentException or FormatException)
        {
            Abort(ExitBadArgumentValue, $"[OŚ] {axisPath} nie jest osią trasy: {error.Message}");
            return;
        }
        catch (Exception error) when (BadFile.IsWrongJsonShape(error))
        {
            Abort(ExitBadArgumentValue,
                $"[OŚ] {axisPath} nie ma kształtu osi trasy: brak wymaganego pola albo pole złego typu");
            return;
        }

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

        if (_fromTelemetryPath is not null)
        {
            _track = ReadTelemetryTrack(_fromTelemetryPath);
            if (_track is null)
            {
                return;
            }

            // Pierwsza próbka JEST stanem początkowym, a nie stanem po pierwszym
            // kroku. Bez tego wiersz zerowy telemetrii wyjścia opisywałby skład
            // stojący na 94 m z zerową prędkością — czyli `DriveState.AtRest`
            // z konstruktora — zamiast tego, od czego zaczyna się odtwarzany plik.
            _playbackStep = _track.FirstStep;
            AdoptTelemetrySample();

            GD.Print(string.Create(
                CultureInfo.InvariantCulture,
                $"[RUCH ZADANY] {_fromTelemetryPath}: {_track.Samples.Count} próbek, "
                + $"kroki {_track.FirstStep}..{_track.LastStep}"));
        }

        if (_inputLogPath is not null)
        {
            _recorder = new InputLogRecorder();

            // ŚCIEŻKA BEZWZGLĘDNA NA STARCIE, a nie dopiero przy zapisie, i nie
            // wyliczona przez czytającego z nazwy projektu. Gracz ma się dowiedzieć,
            // GDZIE leżą jego przejazdy, zanim pierwszy z nich powstanie; dla mnie
            // i dla CI jest to jedyny sposób ZMIERZENIA tej ścieżki zamiast
            // wyprowadzenia jej z `config/name` — a wyprowadzenie było przy MB-04
            // po prostu błędne (`MetroBXL/` zamiast rzeczywistej nazwy projektu).
            GD.Print(string.Create(
                CultureInfo.InvariantCulture,
                $"[ZAPISY] wejścia maszynisty -> {ProjectSettings.GlobalizePath(_inputLogPath)}"));
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

                // MB-07: N składów, każdy o własnym kroku wyjazdu. Przy `--trains=1`
                // (domyślnie) pętla wykonuje się RAZ i robi dokładnie to, co robił
                // pojedynczy `Add` przed tą pozycją — łącznie z nazwą i krokiem zero.
                if (_plan!.ScheduledEntriesPath is { } scheduledPath)
                {
                    using var scheduleFile = FileAccess.Open(scheduledPath, FileAccess.ModeFlags.Read);
                    if (scheduleFile is null)
                    {
                        Abort(ExitMissingInput,
                            $"[ROZKŁAD] nie da się otworzyć {scheduledPath}: {FileAccess.GetOpenError()}");
                        return;
                    }
                    try
                    {
                        var schedule = LineEntrySchedule.FromJson(scheduleFile.GetAsText(), _axis, _step);
                        if (_axis.Id != "L1_A" || schedule.Entries.Count != 2)
                            throw new ArgumentException(
                                "Scenariusz wymaga dokładnie dwóch wjazdów L1_A.");
                        _lineDispatcher = new LineEntryDispatcher(
                            _lineCore, schedule, schedule.ServiceDay);
                        GD.Print($"[ROZKŁAD] {schedule.Date}: dwa wejścia z {scheduledPath}");
                    }
                    catch (Exception error) when (error is ArgumentException or InvalidOperationException
                                                  or FormatException or OverflowException)
                    {
                        Abort(ExitBadArgumentValue,
                            $"[ROZKŁAD] niepoprawny plan wejść {scheduledPath}: {error.Message}");
                        return;
                    }
                    catch (Exception error) when (BadFile.IsWrongJsonShape(error))
                    {
                        Abort(ExitBadArgumentValue,
                            $"[ROZKŁAD] {scheduledPath} nie ma kształtu planu wejść: brak pola albo pole złego typu");
                        return;
                    }
                }
                else
                {
                    for (var i = 0; i < _plan.Trains; i++)
                        _lineCore.Add(TrainIdAt(i), i * _plan.HeadwaySteps);
                }

                _lineSession = new LineSession(_lineCore, _notch, _step, _lineDispatcher);
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
        else if (_fromTelemetryMode)
        {
            // NIC TU NIE POWSTAJE, i to jest treść tej gałęzi, a nie jej brak.
            // W ruchu zadanym nie ma sterownika, bo nie ma czego sterować: stan
            // przychodzi z pliku gotowy. Gałąź istnieje po to, żeby przebieg NIE
            // wpadł do trybu ręcznego niżej — tamten wczytałby plan sygnalizacji,
            // zbudował obsługę stacji z cyklem drzwi i filtrowałby nim polecenie,
            // którego w tym trybie nie ma. Odtwarzanie wyszłoby wtedy takie samo
            // (filtr niczego nie dotyka), ale przebieg odmawiałby startu, gdy planu
            // nie ma na dysku — czyli z powodu, który tego trybu nie dotyczy.
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
            //
            // OD 05.09.2026 (G-5) TO NIE JEST JUŻ CAŁA PRAWDA i akapit wyżej zostaje
            // jako opis trybu BEZ `--signalling`. Z `--signalling` plan nie tylko daje
            // liczbę, ale PILNUJE: skład wchodzi na bloki, nastawnia rygluje mu trasy,
            // dostaje autorytet jazdy, a ochrona ingeruje w polecenie człowieka. Plan
            // podany argumentem zastępuje wtedy stałą w CAŁOŚCI — dwa plany w jednym
            // przejeździe, jeden od limitu i drugi od bloków, byłyby dwiema prawdami
            // o tej samej osi.
            var planPath = _signallingPath ?? RepoPath(RunPlan.ManualSpeedLimitPlanPath);
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

            // Wiersz `[LIMIT]` do ścieżki planu włącznie jest STAŁY, bo tyle wycina
            // `grep -o` w bramce „Manual mode — both sides must hold the same speed
            // ceiling"; obie strony porównania mają wypowiedzieć tę samą liczbę i ten
            // sam plan. Zmienia się ogon, i ma się zmieniać: przejazd pod ochroną
            // a przejazd czytający z planu jedną liczbę to dwie różne rzeczy.
            var planNameForLog = _signallingPath ?? RunPlan.ManualSpeedLimitPlanPath;
            var limitTail = _plan!.ManualSignalling
                ? string.Create(
                    CultureInfo.InvariantCulture,
                    $"plan PILNUJE — bloki, autorytet jazdy i ATP; " +
                    $"sufit maszynisty {Units.MpsToKmh(SpeedLimitMps):F2} km/h")
                : "plan jest czytany, nie prowadzi — bez blokad i bez ochrony pociągu";
            GD.Print(string.Create(
                CultureInfo.InvariantCulture,
                $"[LIMIT] tryb ręczny: {Units.MpsToKmh(_manualPlan.PermittedSpeedMps):F2} km/h " +
                $"z planu {_manualPlan.PlanId} ({planNameForLog}); {limitTail}"));

            if (_plan!.ManualSignalling)
            {
                // Skład wchodzi na plan z czołem tam, gdzie NAPRAWDĘ startuje przejazd
                // ręczny — 94,000 m, czyli z ogonem dokładnie na początku osi. Nie jest
                // to kilometraż pierwszej stacji, którym wchodzi `LineCore`, i to jest
                // różnica z konsekwencjami: na pakiecie A czoło stoi wtedy już w bloku
                // SZLAKOWYM S01, a ogon w peronowym P01. Trasę rygluje się z bloku,
                // który skład ZAJMUJE (`FixedBlockSystem.NextRouteForTrain`), więc R01
                // wychodzi z P01 i przejazd rusza.
                _cabProtection = CabProtection.M7(
                    _manualPlan, SignalledTrainId, _scenario.StartChainageM);
                GD.Print(string.Create(
                    CultureInfo.InvariantCulture,
                    $"[SYGNALIZACJA] {_manualPlan.Blocks.Count} bloków, {_manualPlan.Routes.Count} tras, "
                    + $"wymaga tras: {_manualPlan.RequireRoute}, "
                    + $"limit planu {Units.MpsToKmh(_manualPlan.PermittedSpeedMps):F2} km/h, "
                    + $"margines autorytetu {_manualPlan.AuthorityMarginM:F2} m, "
                    + $"hamulec {_cabProtection.Protection.ServiceBrakeMps2:F2}"
                    + $"/{_cabProtection.Protection.EmergencyBrakeMps2:F2} m/s²"));
            }

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

            // CELE WYCHODZĄ Z OSI, a nie są tu wpisane — `docs/PLAYABILITY.md` §3
            // żąda tego wprost: „cele wyszukiwane po identyfikatorach z osi;
            // kilometraży nie kopiuje się do logiki". Decyzją projektową jest LICZBA
            // celów i to, że są to pierwsze stacje za punktem startowym; które to
            // stacje, mówi plik osi. Wpisanie tu `8742` i `8292` byłoby drugą kopią
            // danych, które stoją w `data/track/L1_A.json`, i milczałoby po zmianie osi.
            //
            // Indeks 0 jest POMIJANY, bo `StationService` traktuje go jako miejsce,
            // na którym skład stoi na starcie — cel z tego miejsca nie trafiłby ani
            // do wywołań, ani do miniętych, a sesja czekałaby na niego bez końca.
            var cele = new List<string>();
            for (var i = 1;
                 i < _axis.Stations.Count && cele.Count < DesignAssumptions.TrainingTargets;
                 i++)
            {
                cele.Add(_axis.Stations[i].StopId);
            }

            if (cele.Count == DesignAssumptions.TrainingTargets)
            {
                _training = new TrainingSession(_axis.Stations, cele, _step);
            }
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
        catch (Exception error) when (BadFile.IsWrongJsonShape(error))
        {
            Abort(ExitBadArgumentValue,
                $"[SYGNALIZACJA] {path} nie ma kształtu planu: brak wymaganego pola albo pole złego typu");
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

    /// <summary>
    /// Zapis telemetrii z pliku. Ta sama droga i ten sam powód, co przy
    /// <see cref="ReadInputLog"/>: czyta <c>FileAccess</c>, więc ścieżka spod
    /// <c>res://</c> też działa, a odmowa jest KODEM WYJŚCIA, nie wyjątkiem
    /// w środku <c>_Ready</c> — wyjątek zostawiłby pętlę klatek kręcącą się
    /// na niezbudowanym stanie do wypalenia limitu czasu w CI.
    /// </summary>
    /// <param name="path">Ścieżka pliku telemetrii.</param>
    /// <returns>Wczytany zapis albo <c>null</c>, gdy przebieg został przerwany.</returns>
    private TelemetryTrack? ReadTelemetryTrack(string path)
    {
        using var file = FileAccess.Open(path, FileAccess.ModeFlags.Read);
        if (file is null)
        {
            Abort(ExitMissingInput,
                $"[TELEMETRIA] nie da się otworzyć {path}: {FileAccess.GetOpenError()}");
            return null;
        }

        if (!TelemetryTrack.TryParse(file.GetAsText(), _step, out var track, out var error))
        {
            Abort(ExitBadArgumentValue, $"{error} (plik {path})");
            return null;
        }

        return track;
    }

    /// <summary>
    /// Przenosi próbkę <see cref="_trackIndex"/> do stanu sceny.
    ///
    /// <para>To jest CAŁA „fizyka" ruchu zadanego: przypisanie. Nie ma tu ani jednego
    /// mnożenia, bo każda liczba, którą scena pokazuje, została policzona wcześniej
    /// i leży w pliku. Polecenie idzie do obu pól — <see cref="_command"/> czyta HUD,
    /// <see cref="_effectiveCommand"/> telemetria — i w tym trybie są tym samym:
    /// filtru stacji ani ochrony pociągu nie ma czego filtrować.</para>
    /// </summary>
    private void AdoptTelemetrySample()
    {
        var sample = _track!.Samples[_trackIndex];
        _state = sample.State;
        _acceleration = sample.AccelerationMps2;
        _command = sample.Command;
        _effectiveCommand = sample.Command;
    }

    /// <summary>Wiersz telemetrii wyjścia dla próbki, którą scena właśnie pokazuje.</summary>
    /// <returns>Wiersz zgodny z <see cref="DriveTelemetry.Header"/>.</returns>
    private string FromTelemetryRow() => _track!.Samples[_trackIndex].Row(_step);

    private void BuildEnvironment()
    {
        // Środowisko powstaje w kodzie, a nie w .tscn, bo jego jedynym zadaniem jest
        // oświetlić wnętrze zamkniętej rury o normalnych skierowanych do środka.
        // Światło kierunkowe do takiego tunelu nie wejdzie; zostaje ambient plus
        // reflektor czołowy podwieszony pod kamerą kabiny.
        using var environment = new Environment
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

        var assetsOverride = Argument("assets");
        var assets = assetsOverride ?? AssetsRoot();
        var manifestPath = Argument("manifest") ?? Path.Combine(assets, "chunks", "L1_A-chunks.json");
        var shellOverride = Argument("shell");
        var shellPath = shellOverride ?? Path.Combine(assets, "M7_shell.glb");
        var platformsPath = Argument("platforms") ?? Path.Combine(assets, "L1_A-platforms.glb");
        var cabPath = Argument("cab") ?? Path.Combine(assets, "M7_cab.glb");

        using var manifestFile = FileAccess.Open(manifestPath, FileAccess.ModeFlags.Read);
        if (manifestFile is null)
        {
            Abort(ExitMissingAssets,
                $"[ASSETS] brak manifestu {manifestPath}. Wygeneruj chunki " +
                "(tools/blender/tunnel_sweep.py --chunk-dir ...) albo uruchom z --no-geometry.");
            return;
        }

        // Ta sama osłona co przy osi (6.D235), z tymi samymi DWIEMA klauzulami.
        // `ChunkManifest.FromJson` na poprawnym JSON-ie bez wymaganego pola rzuca
        // `KeyNotFoundException` z komunikatem .NET-a po angielsku — dlatego ta rodzina
        // ma osobną klauzulę z własnymi słowami, a nie miejsce w filtrze pierwszym.
        ChunkManifest manifest;
        try
        {
            manifest = ChunkManifest.FromJson(manifestFile.GetAsText());
        }
        catch (Exception error) when (error is ArgumentException or FormatException)
        {
            Abort(ExitBadArgumentValue, $"[ASSETS] {manifestPath} nie jest manifestem chunków: {error.Message}");
            return;
        }
        catch (Exception error) when (BadFile.IsWrongJsonShape(error))
        {
            Abort(ExitBadArgumentValue,
                $"[ASSETS] {manifestPath} nie ma kształtu manifestu chunków: brak wymaganego pola albo pole złego typu");
            return;
        }

        _manifest = manifest;
        var tunnelMaterial = GlbLoader.TunnelConcreteMaterial();
        using var trainMaterial = GlbLoader.NeutralMaterial(new Color(0.80f, 0.81f, 0.83f), 0.45f);
        using var cabMaterial = GlbLoader.NeutralMaterial(new Color(0.13f, 0.17f, 0.20f), 0.80f);

        // Peron dostaje WŁASNY, ciemniejszy odcień szarości i to nie jest wybór
        // estetyczny, tylko warunek widzialności: płyta stoi 1,4 m od ściany komory
        // i przy tej samej wartości albedo obie powierzchnie zlewają się w kadrze
        // z kabiny w jedną plamę. Odcień zostaje neutralny — `docs/03-legal.md`
        // zabrania wystroju, piktogramów i barw STIB, a wygląd docelowy jest
        // przedmiotem osobnego zadania, nie tego.
        using var platformMaterial = GlbLoader.NeutralMaterial(new Color(0.34f, 0.34f, 0.36f), 0.90f);

        // Katalog i materiał zapamiętane, bo streamowanie dokłada chunki w KAŻDEJ
        // klatce, a nie raz przy starcie.
        _assetDirectory = Path.GetDirectoryName(manifestPath) ?? assets;
        _hasTrackDetail = manifest.Chunks.Count > 0 && FileAccess.FileExists(
            Path.Combine(_assetDirectory, manifest.Chunks[0].Id + "_detail.glb"));
        _tunnelMaterial = tunnelMaterial;
        _tunnel.Stream(manifest, _assetDirectory, tunnelMaterial, _scenario.StartChainageM);
        var tailMeshes = _tunnel.LoadVisualContinuation(
            Path.Combine(assets, "L1_A-visual-tail.glb"),
            Path.Combine(assets, "L1_A-visual-tail-detail.glb"), tunnelMaterial);
        if (tailMeshes < 0)
        {
            Abort(ExitMissingAssets, "[ASSETS] niekompletna wizualna kontynuacja za Merode; sprawdź pliki toru");
            return;
        }
        var tailAxisPath = Path.Combine(assets, "L1_A-visual-tail-axis.json");
        if (tailMeshes > 0)
        {
            using var tailAxisFile = FileAccess.Open(tailAxisPath, FileAccess.ModeFlags.Read);
            if (tailAxisFile is null)
            {
                Abort(ExitMissingAssets, $"[ASSETS] nie da się odczytać {tailAxisPath}");
                return;
            }
            try
            {
                var tailAxis = new SceneAxis(
                    TrackAxis.FromJson(tailAxisFile.GetAsText()), DesignAssumptions.TrackOffsetM);
                if (tailAxis.CentreLinePoint(0.0).DistanceTo(
                    _sceneAxis.CentreLinePoint(_axis.LengthM)) > 0.02f)
                    throw new ArgumentException("oś scenerii nie łączy się z końcem toru jazdy");
                _visualTailAxis = tailAxis;
            }
            catch (Exception error) when (error is ArgumentException or FormatException)
            {
                Abort(ExitBadArgumentValue, $"[ASSETS] {tailAxisPath} nie jest osią scenerii: {error.Message}");
                return;
            }
            catch (Exception error) when (BadFile.IsWrongJsonShape(error))
            {
                Abort(ExitBadArgumentValue, $"[ASSETS] {tailAxisPath} ma nieprawidłowy kształt osi scenerii");
                return;
            }
        }

        // Wynik `Load` był ODRZUCANY. `TrainView.Load` zwraca liczbę brył i zero znaczy
        // „nie wczytałem nic" — bez tego sprawdzenia scena szła dalej bez składu, a że
        // metadane opisywały wyłącznie tunel, cały `godot-first-run.yml` zostawał
        // zielony. Zmierzone audytem mutacyjnym (Issue #107): mutacja `TrainView.cs:38`
        // przechodziła bramki, tą samą drogą przeżyły `TrackOffsetM 2.10→0.0`
        // i `CabEyeHeightM 2.20→0.0`.
        // Materiały proceduralnego M7 wolno zachować tylko przy domyślnych zasobach.
        // --shell/--assets mogą wskazywać dowolny GLB i nadal dostają neutralny materiał.
        var preserveGeneratedShellMaterials = shellOverride is null && assetsOverride is null;
        var bodies = _train.Load(shellPath, trainMaterial, preserveGeneratedShellMaterials);
        if (bodies <= 0)
        {
            Abort(ExitTrainMissing,
                $"[SKŁAD] {shellPath} nie dał ani jednej bryły — scena bez składu nie jest przejazdem");
            return;
        }

        // MB-07: widoki składów po nazwie. Skład zerowy to węzeł `Train` z `.tscn`,
        // kolejne powstają obok niego i BIORĄ JEGO SIATKI — patrz `LoadSharedFrom`.
        // Przy `--trains=1` pętla nie wykonuje się ani razu i scena jest ta sama.
        _trainViews[TrainIdAt(0)] = _train;
        for (var i = 1; i < _plan!.Trains; i++)
        {
            var widok = new TrainView { Name = $"Train{i + 1}" };
            AddChild(widok);
            var wspolne = widok.LoadSharedFrom(_train, trainMaterial,
                preserveGeneratedShellMaterials);
            if (wspolne <= 0)
            {
                // Ta sama odmowa co przy składzie zerowym i z tego samego powodu:
                // skład bez brył jest niewidoczny i nieruchomy, a przebieg kończy się
                // kodem 0. Cisza tutaj byłaby usterką z Issue #107, tylko N-tą kopią.
                Abort(ExitTrainMissing,
                    $"[SKŁAD] {TrainIdAt(i)} nie dostał ani jednej bryły ze składu "
                    + "zerowego — scena bez składu nie jest przejazdem");
                return;
            }

            _trainViews[TrainIdAt(i)] = widok;
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
        var namePlatePath = Path.Combine(assets, "L1_A-station-board.glb");
        var nameMarkers = _platforms.AddNameMarkers(_sceneAxis, namePlatePath);
        if (nameMarkers != _sceneAxis.Axis.Stations.Count)
        {
            Abort(5, $"[STACJA] {namePlatePath} nie dał tablic nazw wszystkich stacji.");
            return;
        }

        // KABINA WCHODZI TĄ SAMĄ DROGĄ CO SKORUPA I PERONY, łącznie z odmową przy zerze
        // brył (MB-05). Odrzucenie wyniku `Load` jest tu tą samą usterką co przy składzie
        // z Issue #107: scena szłaby dalej bez wnętrza, a że kamera kabinowa i tak stoi
        // w środku skorupy, kadr wyglądałby jak przed tą pozycją — czyli bramka
        // `godot-first-run.yml` zostawałaby zielona na scenie, która kabiny nie ma.
        var cabBodies = _cabView.Load(cabPath, cabMaterial);
        if (cabBodies <= 0)
        {
            Abort(ExitCabMissing,
                $"[KABINA] {cabPath} nie dał ani jednej bryły. Wygeneruj kabinę "
                + "(tools/blender/m7_cab_build.py --out …/M7_cab.glb) albo uruchom "
                + "z --no-geometry.");
            return;
        }

        GD.Print(_tunnel.Describe(manifest));
        GD.Print(_platforms.Describe());
        GD.Print(_train.Describe());
        GD.Print(_cabView.Describe());
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

        if (_readsKeyboard)
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

        // R w trybie linii odtwarza całą scenę: nową nastawnię, składy, licznik
        // postojów i pamięć wskazówki. Ręczny RunReset dotyczy innego sterownika.
        if (_lineMode && _readsKeyboard && _resetPending && _replay is null)
        {
            _resetPending = false;
            var error = GetTree().ReloadCurrentScene();
            if (error != Error.Ok)
                GD.PushError($"[LINIA] nie udało się rozpocząć przejazdu od nowa: {error}");
            return;
        }

        // SESJA SKOŃCZONA: KLATKI IDĄ DALEJ, TICKI NIE — i nie ma tu `_done`.
        // To jest cała różnica między „koniec sesji" a „koniec procesu": `_done`
        // powoduje `return` przed odczytem klawiatury, więc gracz nie mógłby ani
        // ponowić (`R`), ani wyjść (`Esc`), ani przełączyć widoku (`C`). Panel wyniku
        // bez działających klawiszy jest ekranem, z którego nie ma wyjścia.
        //
        // `_resetPending` przepuszcza klatkę dalej, bo reset WYKONUJE się w `StepOnce` —
        // klatka go tylko zamawia (`HandleViewKeys`). Bez tego wyjątku `R` ustawiałoby
        // zamówienie, którego nikt by nie odebrał.
        //
        // Czasu spędzonego na panelu nikt nie nadrabia: `AdvanceBy` nie jest wołane,
        // więc akumulator kroków nie dostaje ani jednej sekundy tych klatek.
        // **WARUNEK `_readsKeyboard` JEST TU NOSNY I ZOSTAL ZNALEZIONY PRZEBIEGIEM,
        // a nie lektura.** Bez niego koniec SESJI polykal koniec ODTWORZENIA: sesja
        // konczy sie na kroku 18 821, zapis ma 20 000, a ta galaz wychodzila z `_Process`
        // przed `AdvanceBy`, wiec `FinishReplayRun` nie wykonywal sie NIGDY. Skutkiem
        // byl proces, ktory nie konczyl sie sam, nie zapisywal telemetrii ani zapisu
        // wejsc i wygladal na dzialajacy — bo wiersz `[SESJA]` w logu juz stal.
        //
        // Panel wyniku jest polityka EKRANU, a ekran ma tylko przejazd prowadzony
        // przez czlowieka. Odtworzenie, przebieg skryptowy i `--line` maja swoje wlasne
        // warunki konca i to one rozstrzygaja, kiedy proces sie konczy; wynik sesji
        // wychodzi w nich wierszem `[SESJA]` z `FinishReplayRun`, a nie zatrzymaniem
        // tickow. Odtworzenie ma odtwarzac CALY zapis — takze to, co gracz robil po
        // zakonczeniu sesji.
        if (_readsKeyboard && _training is { Finished: true } && !_resetPending)
        {
            // WYPIS JEDNORAZOWY — bo koniec sesji jest w tej scenie NIEWIDOCZNY
            // wszędzie poza HUD-em, a HUD-u nie ma ani przebieg headless, ani CI,
            // ani ja bez ekranu. Ta sama zasada, co przy wierszu `[ATP]`
            // w `FinishReplayRun`: zdarzenie, którego nie widać w telemetrii, musi mieć
            // własny wiersz, inaczej „sesja się skończyła" i „sesja nie ruszyła"
            // wyglądają w logu identycznie.
            //
            // Wiersz idzie przez `TrainingResult.ToString()`, czyli tę samą linię, którą
            // porównuje bramka scena–rdzeń — nie przez `RunSummary`, bo tamten składa
            // panel dla CZŁOWIEKA i łamie się na wiersze.
            if (!_summaryPrinted)
            {
                _summaryPrinted = true;
                GD.Print($"[SESJA] {_training.Result!.Value}");
            }

            UpdateHud();
            return;
        }

        // Przebieg z `--calls` jest WERYFIKACYJNY, więc leci syntetycznym rytmem:
        // 853 s przejazdu w czasie ściennym to 853 s czekania w CI. Bez `--calls`
        // tryb `--line` idzie czasem ściennym, bo wtedy ktoś na to patrzy.
        // Odtworzenie z zapisu wejść leci tak samo i z tego samego powodu — a przy
        // okazji to `--steps-per-frame` jest w nim JEDYNYM sposobem, żeby ten sam
        // zapis puścić przy różnym podziale kroków na klatki.
        var synthetic = _scriptedMode || _replayMode || _fromTelemetryMode
            || (_lineMode && _callsPath is not null);
        // Po ostatnim postoju interaktywna linia czeka na N, C albo R. Nie dopisuj
        // fikcyjnych kroków do akumulatora w klatkach tego ekranu.
        if (!_lineCompletionReported)
            AdvanceBy(synthetic ? SyntheticFrameSeconds() : delta);
        PlaceEverything();
        UpdateHud();

        if (_scriptedMode && (_scripted?.Finished ?? false))
        {
            FinishScriptedRun();
        }
        else if (_lineMode && !_lineCompletionReported
            && (_lineCore?.Finished ?? _line?.Finished ?? false))
        {
            FinishLineRun();
        }
        else if (_replay is not null && _logStep >= _replay.Steps)
        {
            FinishReplayRun();
        }
        else if (_track is not null && _trackIndex >= _track.Samples.Count - 1)
        {
            FinishFromTelemetryRun();
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
            if (_lineSession!.Finished)
            {
                return false;
            }

            // DŹWIGNIA MASZYNISTY I POLECENIA — MB-07, MB-08, od 6.M1 przez `LineSession`.
            //
            // Nastawnik posuwa się DOKŁADNIE RAZ na krok, i tylko na składzie
            // obserwowanym prowadzonym przez maszynistę — powód przy `LineSession.Step`.
            // Od 6.M1 ten krok jest w rdzeniu, a nie tutaj: tę samą kolejność wykonuje
            // `Sim.Runner replay --line`, a porównanie sceny z rdzeniem co do bitu
            // znaczy coś tylko wtedy, gdy obie strony idą JEDNĄ drogą.
            //
            // Klawisze i polecenia biorą się z `_replay` PO NUMERZE KROKU, gdy przejazd
            // jest odtwarzany, a z klawiatury w pozostałych przypadkach. Polecenia
            // z klawiatury wykonały się już w tej klatce, w `HandleTrainKeys`, przed
            // pierwszym krokiem — i pod tym samym numerem kroku trafiły do zapisu.
            var lineStep = _logStep;
            if (_replay is not null)
            {
                foreach (var lineEvent in _replay.EventsAt(lineStep))
                {
                    ExecuteLineEvent(lineEvent);
                }
            }

            var lineKeys = _replay?.KeysAt(lineStep) ?? _keys;
            _recorder?.Record(lineStep, lineKeys);
            _activeKeys = lineKeys;
            _lineSession!.Step(lineKeys);
            _logStep++;
            _command = _lineSession.Command;

            // MB-07: `_line` to prowadzenie składu OBSERWOWANEGO, a nie zerowego.
            // Jednym przypisaniem przechodzą na nowy skład: obie kamery, okno
            // streamingu, wiersz pozycji i wiersz stacji — bo wszystkie wiszą na
            // `ChainageM`, czyli na `_line?.ChainageM`. To jest cała treść wyboru
            // składu; gdyby każda z tych rzeczy czytała skład osobno, przełączenie
            // byłoby czterema poprawkami, z których każda mogłaby zostać w tyle.
            _observed = _lineSession.ObservedIndex;
            _line = _lineCore.Trains[_observed].Drive;

            // ODMOWA GAŚNIE Z KOŃCEM POSTOJU — MB-08. Nie po czasie i nie po klatkach
            // (powód przy `_doorRefusal`): przestaje być prawdziwa dokładnie wtedy, gdy
            // przestaje istnieć postój, którego dotyczyła. Bez tego wiersza odmowa
            // z jednej stacji witałaby gracza na następnej.
            if (_line is not { AtStation: true })
            {
                _doorRefusal = null;
            }

            if (_line is null)
            {
                // Skład jeszcze nie wjechał na plan (wejście zajęte). Krok się odbył,
                // zegar linii idzie, ale prowadzenia jeszcze nie ma. Odtworzenie kończy
                // się jednak na długości ZAPISU także tutaj (6.M1) — inaczej kroki spoza
                // zapisu wykonałyby się „z rozpędu" na reszcie akumulatora.
                return _replay is null || _logStep < _replay.Steps;
            }

            _state = _line.State;
            _acceleration = _lineSession.AccelerationMps2;

            // KONIEC ODTWORZENIA LINII — 6.M1. Ten sam warunek próbki, co w
            // `Sim.Runner replay --line`: stan składu obserwowanego, co `_sampleEvery`
            // kroków JEGO przejazdu, plus ostatni krok zapisu albo linii.
            if (_replay is null)
            {
                return true;
            }

            var lineFinished = _logStep >= _replay.Steps || _lineSession.Finished;
            if (_telemetryPath is not null
                && (DriveTelemetry.IsSample(_state.Steps, _sampleEvery) || lineFinished))
            {
                _telemetry.Add(_lineSession.TelemetryRow()!);
            }

            return !lineFinished;
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

        if (_track is not null)
        {
            // RUCH ZADANY. Krok NIE liczy fizyki — przesuwa głowicę odtwarzania o jeden
            // krok rdzenia i sprawdza, czy właśnie wypadła następna próbka. Ta gałąź
            // stoi PRZED `_scriptedMode` z tego samego powodu, dla którego linia stoi
            // przed nią obiema: warunek na ŹRÓDŁO RUCHU musi być sprawdzany przed
            // warunkiem na SPOSÓB ZAPISU wyniku. Przy `--from-telemetry --telemetry`
            // `_scriptedMode` jest fałszem (pilnuje tego `RunPlan`), ale kolejność ma
            // być czytelna, a nie zależeć od tamtego warunku.
            //
            // MIĘDZY PRÓBKAMI STAN STOI, i to jest decyzja, nie niedoróbka. Przy
            // domyślnej gęstości próbka wypada co 120 kroków, czyli co sekundę, więc
            // skład skacze po sekundzie zamiast płynąć. Wygładzanie stawiałoby go na
            // kilometrażach, których NIE MA W ŻADNYM PLIKU — czyli pokazywałoby ruch
            // wymyślony przez widok. Płynność jest tu właściwością nagrania
            // (`--sample-every=1` daje próbkę na krok), a nie sceny.
            if (_trackIndex >= _track.Samples.Count - 1)
            {
                return false;
            }

            _playbackStep++;
            if (_playbackStep < _track.Samples[_trackIndex + 1].Steps)
            {
                return true;
            }

            _trackIndex++;
            AdoptTelemetrySample();
            if (_telemetryPath is not null)
            {
                // KAŻDA przyjęta próbka wychodzi na wyjście, bez pytania o
                // `IsSample`: gęstość jest właściwością wczytanego pliku, a drugie
                // przerzedzenie zrobiłoby z echa podzbiór oryginału. Porównanie przy
                // progu 0 zgłosiłoby wtedy „różna liczba wierszy", i słusznie.
                _telemetry.Add(FromTelemetryRow());
            }

            // Koniec zgłasza `_Process`, tak samo jak w pozostałych trybach. Tutaj
            // przerywa się tylko pętla kroków tej klatki, żeby kroki spoza pliku nie
            // wykonały się „z rozpędu" na przeniesionej reszcie akumulatora.
            return _trackIndex < _track.Samples.Count - 1;
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
        var stepIndex = _logStep;

        // RESET OBOWIĄZUJE PRZED KROKIEM — jedno miejsce dla obu źródeł. Odtworzenie
        // bierze go z zapisu (`IsResetAt`), przejazd z klawiatury z zamówienia złożonego
        // w tej klatce. Numer kroku sesji NIE cofa się: to on trafia do zapisu i po nim
        // zapis jest czytany, więc cofnięcie dałoby dwa różne momenty pod jednym numerem.
        var resetNow = _replay is not null ? _replay.IsResetAt(stepIndex) : _resetPending;
        if (resetNow)
        {
            _resetPending = false;
            ResetRun();
        }

        // Odtworzenie z zapisu bierze klawisze PO NUMERZE KROKU, a nie z klawiatury.
        // Poza tym ścieżka jest ta sama co dla człowieka: ten sam `DriverNotch`,
        // ten sam `StationService`, ten sam `TrainController`. Osobna ścieżka przez
        // fizykę odbierałaby porównaniu gracza z rdzeniem wszelkie znaczenie.
        var keys = _replay?.KeysAt(stepIndex) ?? _keys;
        _recorder?.Record(stepIndex, keys);
        _activeKeys = keys;

        // NASTAWNIA I NADZÓR PRZED KROKIEM, ze stanu sprzed kroku — fazy 1b i 2 kroku
        // `LineCore`. Decyzja powstaje tutaj, a stosuje się ją niżej, ZA filtrem stacji.
        //
        // Zegarem nastawni jest `_state.Steps`, czyli numer kroku PRZEJAZDU, a NIE
        // `stepIndex` (numer kroku sesji, który po resecie nie wraca). Ochrona powstaje
        // po resecie od nowa razem z całym stanem sygnalizacji, więc jej odstęp żądań
        // tras ma liczyć się od zera razem z nią; sesja dałaby tu zegar, który przeżył
        // przejazd, i pierwsze żądanie trasy po resecie spóźniłoby się o tyle kroków,
        // ile trwał poprzedni przejazd. `Sim.Runner replay` podaje tę samą liczbę.
        _cabProtection?.Supervise(_state.Steps, ChainageM, _state.SpeedMps);

        // JEDEN krok dźwigni na JEDEN krok symulacji. Klatka obejmująca N kroków
        // wykona to N razy z tym samym `keys` — stan klawiszy jest stały w obrębie
        // klatki, położenie nastawnika nie. Dlaczego akurat tak: `DriverNotch`.
        _command = _notch.Advance(keys, _step);

        // `Filter` posuwa licznik cyklu drzwi, więc musi zostać zawołane DOKŁADNIE RAZ
        // na krok symulacji — nie raz na klatkę. `AdvanceBy` woła `StepOnce` tyle razy,
        // ile kroków wypada w klatce, i to jest właściwe miejsce.
        var effective = _stations?.Filter(_state, _command, ChainageM) ?? _command;
        if (_stations is { AtStation: true } && _stations.Calls[^1].StopId == _axis.Stations[^1].StopId)
            _terminalBrakeEngaged = true;
        effective = TrackEndStop.ApproachCommand(
            _state, ChainageM,
            _axis.Stations.Count > 0
                ? Math.Min(_axis.Stations[^1].ChainageM, _axis.LengthM) : _axis.LengthM,
            _conditions, _controller, BrakingPointSolver.M7,
            _controller.ServiceBrakeMps2, effective, terminalSection: true,
            ref _terminalBrakeEngaged);

        // ATP JEST OSTATNIM FILTREM POLECENIA i to jest wprost kryterium z Issue #26:
        // „nie można ominąć ATP przez input gracza". Gdyby ochrona stała przed filtrem
        // stacji, blokada trakcji na czas cyklu drzwi nadpisywałaby jej hamulec; gdyby
        // stała przed nastawnikiem — nadpisywałby ją człowiek. Bez `--signalling`
        // `_cabProtection` jest nullem i polecenie idzie do kontrolera dokładnie takie,
        // jak przed wprowadzeniem G-5.
        effective = _cabProtection is null ? effective : _cabProtection.Apply(effective);

        // Telemetria pokazuje polecenie, którym NAPRAWDĘ pojechał kontroler — czyli po
        // filtrze stacji I po ochronie, a nie surowe położenie dźwigni. Ta sama zasada,
        // co w `RunHeader`: kolumna, która nie jest wejściem fizyki, przepuściłaby
        // rozjazd w obsłudze drzwi przy porównaniu z progiem 0 i nikt by nie wiedział,
        // że blokada trakcji zadziałała w innym kroku. Tak samo `LineDrive` wpisuje do
        // śladu polecenie PO ingerencji: inaczej ślad mówiłby, czego maszynista chciał,
        // a nie czym pojechał.
        if (TrackEndStop.Reached(ChainageM, _axis.LengthM))
        {
            effective = DriverCommand.Coast;
        }
        _effectiveCommand = effective;

        var beforeSpeed = _state.SpeedMps;
        _state = _controller.Advance(
            _state, _conditions, effective, SpeedLimitMps, _step, out var forces);
        _state = TrackEndStop.Apply(_state, _scenario.StartChainageM, _axis.LengthM);
        if (TrackEndStop.Reached(ChainageM, _axis.LengthM))
        {
            _effectiveCommand = DriverCommand.Coast;
        }
        _acceleration = TrackEndStop.Reached(ChainageM, _axis.LengthM)
            || (_terminalBrakeEngaged && beforeSpeed <= 0.0 && _state.SpeedMps <= 0.0)
            ? 0.0 : forces.AccelerationMps2;
        _logStep++;

        // MELDUNEK RUCHU PO KROKU — faza 3 kroku `LineCore`. Przed krokiem opisywałby
        // położenie, z którego skład właśnie odjechał.
        _cabProtection?.Move(ChainageM);

        // SESJA PATRZY NA KONIEC KROKU, a nie na jego początek, i to jest treść, nie
        // kolejność wierszy: warunek zaliczenia pyta o prędkość PO kroku i o cykl drzwi
        // PO `StationService.Filter`. Policzony wyżej opisywałby krok poprzedni, czyli
        // kończyłby sesję o jeden krok za wcześnie — a błąd o jeden krok w warunku końca
        // wygląda dokładnie tak samo jak warunek końca, który działa.
        //
        // Decyzja ochrony jest tą z POCZĄTKU tego samego kroku (`Supervise` wyżej), bo
        // to ona filtrowała polecenie, którym skład właśnie pojechał. Wołanie ochrony
        // drugi raz „do policzenia" liczyłoby ją z innego stanu i emitowało zdarzenia
        // sygnalizacji z licznika — ta sama zasada, co przy `CabProtection.Decision`.
        if (_stations is not null)
        {
            _training?.Observe(_stations, _state, _cabProtection?.Decision);
        }

        if (_replay is null)
        {
            return true;
        }

        var finished = _logStep >= _replay.Steps;
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

    /// <summary>
    /// Kilometraż czoła składu — jedno miejsce dla wszystkich trybów.
    ///
    /// <para>RUCH ZADANY idzie pierwszy i bierze liczbę WPROST Z PLIKU, a nie z sumy
    /// „początek scenariusza + droga". Te dwie liczby są równe tylko dla przebiegu,
    /// który zaczyna się tam, gdzie pakiet A: telemetria nagrana przejazdem
    /// <c>--line</c> startuje na kilometrażu pierwszej stacji, więc fallback
    /// przesunąłby cały odtwarzany przejazd i skład jechałby obok własnego zapisu.
    /// Kolumna <c>chainage_m</c> jest w formacie po to, żeby jej użyć.</para>
    /// </summary>
    private double ChainageM => _track is not null
        ? _track.Samples[_trackIndex].ChainageM
        : _line?.ChainageM
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
        // MB-07: chowa się widok składu OBSERWOWANEGO, bo to w nim siedzi kamera.
        // Chowanie `_train` na sztywno ukrywałoby skład zerowy także wtedy, gdy gracz
        // patrzy z kabiny składu drugiego — czyli znikałby skład, na który się NIE
        // patrzy, a ten, w którym siedzi kamera, zasłaniałby jej cały kadr.
        var obserwowany = ObservedTrainView();
        foreach (var widok in _trainViews.Values)
        {
            widok.Visible = widok == obserwowany ? view != ViewKind.Cab : true;
        }

        if (_trainViews.Count == 0)
        {
            _train.Visible = view != ViewKind.Cab;
        }

        // ...a wnętrze DOKŁADNIE ODWROTNIE, tym SAMYM warunkiem (MB-05). Drugi,
        // niezależny przełącznik dałby stan, w którym nie widać ani skorupy, ani
        // kabiny — kadr pusty, wyglądający jak niewczytana geometria.
        _cabView.Visible = view == ViewKind.Cab;
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
        // 6.C4: okno streamowania idzie za TEMATEM KADRU, nie za pojazdem — i to jest
        // poprawka usterki, której nie zobaczyła ani bramka metadanych, ani metryki.
        // Dla trzech widoków jazdy `SubjectChainageM` JEST kilometrażem pojazdu, więc
        // dla nich nie zmienia się nic. Dla widoku inspekcyjnego kamera stoi tam, gdzie
        // pojazd nie dojechał, a chunki wchodziły do pamięci wokół POJAZDU — zmierzone:
        // zrzut z 2521,1 m dawał kadr CZARNY (22 384 B wobec 92 315 B przy 500 m),
        // przy „2/12 chunków rezydentnych" i kodzie 0 z bramki. Kamera była w dobrym
        // miejscu, tylko geometrii tam nie było.
        var streamChainage = Math.Clamp(SubjectChainageM, 0.0, _axis.LengthM);
        if (_manifest is not null && _tunnelMaterial is not null)
        {
            _tunnel.Stream(_manifest, _assetDirectory, _tunnelMaterial, streamChainage);
        }

        // Było tu `_train.LengthM > 0.0 ? _train.LengthM : 94.0` — CICHY ODWRÓT na
        // wartość ze specyfikacji, gdy skorupa się nie wczytała. Podstawiał poprawną
        // liczbę za nieistniejący skład, więc kamery i telemetria wyglądały normalnie.
        // Fallback jest zbędny, odkąd `SetUpScene` odmawia startu bez brył: długość
        // pochodzi teraz zawsze z wczytanej geometrii.
        var trainLength = _train.LengthM;
        _train.PlaceAt(_sceneAxis, chainage);

        // MB-07: POZOSTAŁE składy stoją tam, gdzie stoją W RDZENIU, a nie tam, gdzie
        // patrzy kamera. Pętla jest pusta przy `--trains=1`.
        //
        // Widok składu, który jeszcze nie wjechał na plan (`Drive is null`), jest
        // UKRYWANY, a nie zostawiany w origo. Zostawiony stałby na kilometrażu zero
        // razem z peronem stacji zerowej i wyglądałby jak skład zaparkowany na stacji —
        // czyli jak stan gry, a nie jak jego brak.
        if (_lineCore is not null && _trainViews.Count > 1)
        {
            foreach (var skladRdzenia in _lineCore.Trains)
            {
                if (!_trainViews.TryGetValue(skladRdzenia.Id, out var widok) || widok == _train)
                {
                    continue;
                }

                var prowadzenie = skladRdzenia.Drive;
                widok.Visible = prowadzenie is not null;
                if (prowadzenie is not null)
                {
                    widok.PlaceAt(
                        _sceneAxis,
                        Math.Min(prowadzenie.ChainageM, _axis.LengthM));
                }
            }
        }

        // Kabina jedzie po OGONIE SKORUPY, a nie po własnej rozpiętości, i to jest
        // poprawka usterki znalezionej RACHUNKIEM przy MB-05, nie oglądaniem klatki:
        // bryły kabiny mają wspólny układ współrzędnych ze skorupą, ale własną
        // rozpiętość 93,300 m wobec 94,000 m składu, więc liczenie ogona z nich samych
        // stawiało szybę czołową 0,700 m za daleko — 0,35 m PRZED czołem pudła.
        //
        // ODEJMOWANIA TU NIE MA i to jest poprawka DRUGA, z tej samej rodziny co
        // pierwsza: `chainage - trainLength` było wyrażeniem wpisanym w argument, więc
        // nie widział go żaden test, a dopisanie do niego `+ 0.7` przechodziło 292/292.
        // Arytmetyka ogona stoi teraz w `TrainLayout.RearOfTrain`, przybita liczbowo
        // w `tests/Game.Tests/CabPlacementTests.cs`; tutaj zostaje jedno: CZYJĄ długość
        // jej podajemy. `trainLength` jest długością SKORUPY (wiersz wyżej) i bramka
        // `Scena_bierze_dlugosc_SKLADU_a_nie_kabiny` pyta o ten wiersz osobno — bo
        // podmiana `_train.LengthM` na `_cabView.LengthM` daje dokładnie tę samą
        // usterkę 0,700 m, a tokenu `trainLength` w argumencie nie rusza.
        _cabView.PlaceAt(_sceneAxis, TrainLayout.RearOfTrain(chainage, trainLength));

        // Dostępność widoku goniącego — decyzja właściciela z 05.09.2026, cała
        // arytmetyka w `ChaseCameraAim.Availability`. Długość bierze się STĄD, czyli
        // z wczytanej geometrii, a nie z rejestru: pytanie brzmi „czy kamera siedzi
        // w skorupie", a skorupa jest tym, co naprawdę stoi w scenie. Że ta liczba
        // ma się zgadzać z `parameters.length_m` ze spec M7, pilnuje osobny test —
        // rozjazd między spec a geometrią jest usterką danych, nie powodem, żeby
        // widok liczył się z liczby, której w kadrze nie ma.
        var availability = ChaseCameraAim.Availability(
            chainage, trainLength, DesignAssumptions.ChaseRevealFromM);
        _viewLine = _view == ViewKind.Chase ? availability.HudHint : string.Empty;
        if (availability.Available != _chaseAvailable)
        {
            _chaseAvailable = availability.Available;
            ApplyView();
        }

        var (eye, forward) = _sceneAxis.SmoothCabPoint(
            chainage,
            DesignAssumptions.CabEyeSetbackM,
            DesignAssumptions.CabEyeHeightM,
            DesignAssumptions.CabEyeLateralM);
        _cab.LookAtFromPosition(eye, eye + forward, Vector3.Up);

        if (_view == ViewKind.Inspect)
        {
            // Kamera stoi NA OSI tunelu, odsunięta wzdłuż niej od oglądanego
            // kilometrażu, i patrzy w ten kilometraż. Wszystkie trzy liczby są
            // wyprowadzone z przekroju `box_double`, nie dobrane wzrokiem —
            // uzasadnienie stoi przy stałych w `DesignAssumptions`.
            //
            // Kilometraż bierze się z `_shotChainageM`, a nie z `chainage`: ten
            // drugi jest pozycją POJAZDU, a widok inspekcyjny istnieje właśnie po
            // to, żeby od niej nie zależeć. Przy zrzucie bez `--at-chainage`
            // `_shotChainageM` jest zerem i kamera staje na początku osi, co jest
            // poprawną odpowiedzią na „pokaż mi kilometraż 0".
            var (oko, wzdluz) = _sceneAxis.CabPoint(
                _shotChainageM - DesignAssumptions.InspectStandoffM,
                0.0,
                DesignAssumptions.InspectHeightM,
                DesignAssumptions.InspectLateralM);
            var cel = _sceneAxis.CabPoint(
                _shotChainageM,
                0.0,
                DesignAssumptions.InspectHeightM,
                DesignAssumptions.InspectLateralM).Position;
            _ = wzdluz;
            _chase.LookAtFromPosition(oko, cel, Vector3.Up);
        }
        else if (_view == ViewKind.Outside)
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

        UpdateTrackLights(streamChainage);
    }

    private void UpdateTrackLights(double chainageM)
    {
        if (!_hasTrackDetail)
        {
            return;
        }

        // The Blender fixtures repeat every 16 m. Reposition a small pool only
        // when the camera crosses a fixture interval, so a full route never owns
        // hundreds of live lights. Inspection view uses its own subject chainage.
        const int spacingM = 16;
        const int intervals = 10;
        var anchor = (int)Math.Floor(chainageM / spacingM);
        if (anchor == _lightAnchor)
        {
            return;
        }

        _lightAnchor = anchor;
        while (_trackLights.Count < intervals * 2)
        {
            var light = new OmniLight3D
            {
                LightColor = new Color(1.0f, 0.86f, 0.68f),
                LightEnergy = 1.3f,
                OmniRange = 15.0f,
                ShadowEnabled = false,
            };
            AddChild(light);
            _trackLights.Add(light);
        }

        for (var slot = 0; slot < intervals; slot++)
        {
            var at = (anchor + slot - 2) * spacingM;
            for (var side = 0; side < 2; side++)
            {
                var light = _trackLights[slot * 2 + side];
                var lateral = side == 0 ? -4.48f : 4.48f;
                var position = _sceneAxis.FixturePoint(at, _visualTailAxis, lateral, 3.35);
                light.Visible = position.HasValue;
                if (!position.HasValue)
                {
                    continue;
                }
                light.Position = position.Value;
            }
        }
    }

    private void HandleViewKeys()
    {
        if (Godot.Input.IsActionPressed(DriverActions.Quit))
        {
            GetTree().Quit();
            return;
        }

        var viewKey = Godot.Input.IsActionPressed(DriverActions.ViewToggle);
        if (viewKey && !_viewKeyHeld)
        {
            _view = _view == ViewKind.Cab ? ViewKind.Chase : ViewKind.Cab;
            ApplyView();
        }

        _viewKeyHeld = viewKey;

        var resetKey = Godot.Input.IsActionPressed(DriverActions.Reset);
        if (resetKey && !_resetKeyHeld)
        {
            // Klatka ZAMAWIA reset, krok go WYKONUJE. W odtworzeniu resety bierze
            // wyłącznie zapis: naciśnięcie `R` w trakcie odtwarzania rozjechałoby
            // przejazd z plikiem, który ma go opisywać, i to bez śladu w telemetrii.
            _resetPending = !_replayMode;
        }

        _resetKeyHeld = resetKey;

        HandleTrainKeys();
    }

    /// <summary>
    /// Wykonuje polecenie maszynisty w trybie linii i zapisuje je pod numerem kroku,
    /// PRZED którym się wykonało — 6.M1.
    ///
    /// <para>Jedno wejście dla klawiatury i dla odtworzenia. Zapis idzie tu, a nie przy
    /// klawiszu, bo przy <c>--replay --input-log</c> ma powstać ta sama kopia zapisu,
    /// co przy przejeździe z klawiatury — i wtedy polecenie przychodzi z pliku.</para>
    /// </summary>
    /// <param name="lineEvent">Polecenie; jego numer kroku zapis bierze z siebie.</param>
    private void ExecuteLineEvent(InputLogEvent lineEvent)
    {
        _recorder?.RecordEvent(lineEvent.Kind, lineEvent.TrainId);
        var response = _lineSession!.Execute(lineEvent);
        if (response is DoorRequestResult drzwi)
        {
            ZapamietajOdpowiedzDrzwi(drzwi);
            return;
        }

        if (lineEvent.Kind == LineEventKind.Observe)
        {
            _observed = _lineSession.ObservedIndex;
            // Zmiana obserwacji może przypaść na klatkę bez kroku 120 Hz.
            // HUD i kamera muszą w tej klatce czytać już wybrany skład.
            _line = _lineCore!.Trains[_observed].Drive;
            _state = _line?.State ?? DriveState.AtRest;
            _command = _lineSession.Command;
            _acceleration = _lineSession.AccelerationMps2;
            _activeKeys = _keys;

            // Odmowa dotyczyła składu, którego gracz już nie ogląda — MB-08.
            _doorRefusal = null;
        }

        ApplyView();
    }

    /// <summary>
    /// Wybór obserwowanego składu i przejęcie sterowania — MB-07.
    ///
    /// <para><b>Wszystkie trzy klawisze działają na ZBOCZU, nie przy trzymaniu</b>, tak
    /// samo jak <c>C</c> i <c>R</c>. Przy trzymaniu <c>N</c> przełączałoby skład co
    /// klatkę, czyli kilkadziesiąt razy na sekundę, a <c>T</c> i <c>O</c> wołałyby rdzeń
    /// bez potrzeby. Nastawnik jazdy jest dźwignią i działa inaczej — ale te trzy są
    /// przyciskami i to jest różnica w obsłudze, nie niekonsekwencja.</para>
    ///
    /// <para>Poza trybem <c>--line</c> metoda nie robi NIC i nie jest to zaniechanie:
    /// bez <c>LineCore</c> nie ma ani czego przejmować, ani między czym przełączać,
    /// a ciche przestawianie pola, którego nikt nie czyta, wygląda jak działające
    /// sterowanie.</para>
    /// </summary>
    private void HandleTrainKeys()
    {
        var nextKey = Godot.Input.IsActionPressed(DriverActions.TrainNext);
        var takeKey = Godot.Input.IsActionPressed(DriverActions.TrainTake);
        var releaseKey = Godot.Input.IsActionPressed(DriverActions.TrainRelease);
        var doorOpenKey = Godot.Input.IsActionPressed(DriverActions.DoorOpen);
        var doorCloseKey = Godot.Input.IsActionPressed(DriverActions.DoorClose);

        if (_lineCore is null || _lineCore.Trains.Count == 0)
        {
            _trainNextKeyHeld = nextKey;
            _trainTakeKeyHeld = takeKey;
            _trainReleaseKeyHeld = releaseKey;
            _doorOpenKeyHeld = doorOpenKey;
            _doorCloseKeyHeld = doorCloseKey;
            return;
        }

        // KAŻDE POLECENIE IDZIE PRZEZ `ExecuteLineEvent` — 6.M1. Ta sama metoda wykonuje
        // polecenia odtwarzane z zapisu, więc to, co gracz zrobił klawiszem, i to, co
        // odtworzenie zrobi z pliku, przechodzi jedną drogą: zapis, rdzeń, widok.
        if (nextKey && !_trainNextKeyHeld)
        {
            var next = _lineCore.Trains[(_lineSession!.ObservedIndex + 1) % _lineCore.Trains.Count];
            ExecuteLineEvent(new InputLogEvent(_logStep, LineEventKind.Observe, next.Id));
        }

        var observed = _lineCore.Trains[Math.Clamp(_observed, 0, _lineCore.Trains.Count - 1)];

        // `TakeControl` RZUCA, gdy skład nie wszedł jeszcze na plan (MB-06), i ten
        // wyjątek nie ma prawa wyjść z `_Process`: wywróciłby klatkę, a nie powiedział
        // graczowi, czemu nic się nie stało. Wiersz `hud.owner.not-on-line` mówi to
        // za niego — i mówi to z tego samego odczytu, który tu odmawia. Ten sam warunek
        // stoi w `LineSession.Execute`, więc polecenie z zapisu zachowa się identycznie.
        if (takeKey && !_trainTakeKeyHeld && observed.Owner == ControlOwner.Autopilot
            && observed.OnLine)
        {
            ExecuteLineEvent(new InputLogEvent(_logStep, LineEventKind.Take, observed.Id));
        }

        if (releaseKey && !_trainReleaseKeyHeld && observed.Owner == ControlOwner.Driver)
        {
            ExecuteLineEvent(new InputLogEvent(_logStep, LineEventKind.Release, observed.Id));
        }

        // DRZWI — MB-08. Na ZBOCZU, tak samo jak trzy klawisze wyżej i z tego samego
        // powodu: trzymany klawisz wysyłałby polecenie w każdej klatce, więc drugie
        // i dalsze wracałyby odmową „drzwi są już otwarte" i wiersz HUD-u pokazywałby
        // odmowę zamiast skutku, który właśnie nastąpił.
        //
        // Rdzeń ODMAWIA, a nie rzuca (powód przy `LineCore.RequestDoorOpen`), więc nie
        // ma tu żadnego warunku „czy wolno zapytać" — pytanie wolno zadać zawsze,
        // a rozstrzyga odpowiedź. Warunek postawiony TUTAJ byłby drugim źródłem prawdy
        // o tym, kiedy wolno otworzyć drzwi, i to źródłem po stronie widoku.
        if (doorOpenKey && !_doorOpenKeyHeld)
        {
            ExecuteLineEvent(new InputLogEvent(_logStep, LineEventKind.DoorOpen, observed.Id));
        }

        if (doorCloseKey && !_doorCloseKeyHeld)
        {
            ExecuteLineEvent(new InputLogEvent(_logStep, LineEventKind.DoorClose, observed.Id));
        }

        _trainNextKeyHeld = nextKey;
        _trainTakeKeyHeld = takeKey;
        _trainReleaseKeyHeld = releaseKey;
        _doorOpenKeyHeld = doorOpenKey;
        _doorCloseKeyHeld = doorCloseKey;
    }

    /// <summary>Zapamiętuje odpowiedź rdzenia na polecenie drzwi do wiersza HUD — MB-08.</summary>
    private void ZapamietajOdpowiedzDrzwi(DoorRequestResult odpowiedz) =>
        _doorRefusal = odpowiedz.Ok ? null : odpowiedz.Refusal;

    /// <summary>
    /// Przejazd od nowa. CO reset obejmuje, rozstrzyga <see cref="RunReset.Apply"/> —
    /// tutaj zostaje wyłącznie nadpisanie pól węzła i wiersz zerowy telemetrii.
    ///
    /// <para><b>Dlaczego decyzja wyszła z tej metody.</b> Do 05.09.2026 stała tu lista
    /// sześciu przypisań, której nie wołał żaden test, bo <c>FirstRun</c> jest węzłem
    /// silnika. Brakowało w niej <c>StationService</c>: skład wracał na 94,0 m
    /// z kolejką stacji ustawioną tam, dokąd dojechał, a trwający cykl drzwi przeżywał
    /// reset (<c>reports/droga-do-grywalnosci.md</c> §5.4, zadanie G-4). Lista, której
    /// nie da się wywołać, nie da się też sprawdzić — i dlatego brak w niej trzech
    /// pozycji naraz nie miał czego przewrócić.</para>
    /// </summary>
    private void ResetRun()
    {
        // SYGNALIZACJA KABINY WRACA RAZEM Z RESZTĄ — jako ARGUMENT, a nie jako osobne
        // wołanie obok. Bez tego reset nie byłby resetem, tylko WYJĄTKIEM:
        // `FixedBlockSystem.MoveTrain` odmawia cofnięcia czoła, więc pierwszy meldunek
        // ruchu po resecie próbowałby przesunąć skład z miejsca, do którego dojechał,
        // z powrotem na 94,0 m i wywaliłby pętlę klatek. A że reset jest od #255 wpisem
        // w zapisie wejść, ten sam reset wykonuje `Sim.Runner replay` — więc odpowiedź
        // „co reset zeruje" musi być JEDNA i leżeć w rdzeniu (`RunRestart`), inaczej
        // bramka przy progu 0 porównywałaby dwie różne definicje resetu.
        var start = RunReset.Apply(
            _accumulator, _notch, _input, _stations, _cabProtection, _recorder, _telemetry,
            _training);

        _summaryPrinted = false;
        _state = start.Drive;
        _keys = start.Keys;
        _activeKeys = start.ActiveKeys;
        _brakingCueMemory.Reset();
        _command = start.Command;
        _effectiveCommand = start.EffectiveCommand;
        _terminalBrakeEngaged = false;
        _acceleration = start.AccelerationMps2;

        // Wiersz zerowy — stan PRZED pierwszym krokiem — składa się tak samo jak
        // w `_Ready`, bo po resecie przejazd jest przed pierwszym krokiem. Warunek
        // patrzy na listę, a nie tylko na ścieżkę: przebieg skryptowy ma swój wiersz
        // zerowy z `ScenarioDrive`, a klawiszy w ogóle nie czyta.
        if (_telemetryPath is not null && _telemetry.Count > 0)
        {
            _telemetry.Add(ManualTelemetryRow());
        }
    }

    private void UpdateHud()
    {
        var chainage = ChainageM;
        var name = "koniec pakietu";
        var distance = _axis.LengthM - chainage;
        if (_stations is not null && TrackEndStop.Reached(chainage, _axis.LengthM))
        {
            name = UiText.Get("hud.station.track-end-name");
            distance = 0.0;
        }

        // Wiedza o tym, gdzie jest następna stacja, ma JEDNO miejsce. Poprzednio ta
        // pętla stała tutaj i była drugą kopią tego, co robi `StationService.Approach`;
        // dwie kopie tej samej wiedzy rozjeżdżają się w chwili, gdy jedna z nich dostaje
        // okno zatrzymania, a druga nie.
        if (_line is not null && !TrackEndStop.Reached(chainage, _axis.LengthM))
        {
            var nastepna = _line.NextStation;
            if (nastepna is not null)
            {
                name = nastepna.Value.Name;
                distance = nastepna.Value.ChainageM - chainage;
            }
        }
        else if (_stations is not null && !TrackEndStop.Reached(chainage, _axis.LengthM))
        {
            var approach = _stations.Approach(chainage);
            if (approach.Exists)
            {
                name = approach.DisplayName;
                distance = approach.DistanceM;
            }
        }
        else if (!TrackEndStop.Reached(chainage, _axis.LengthM))
        {
            foreach (var station in _axis.Stations)
            {
                if (station.ChainageM >= chainage)
                {
                    name = station.DisplayName;
                    distance = station.ChainageM - chainage;
                    break;
                }
            }
        }

        _hud.Update(
            _state.SpeedKmh, SufitKmh(), _acceleration,
            chainage, _axis.LengthM,
            name, distance, _command.Throttle, _command.Brake, _mode,
            StationLine(), SignallingLine(), _viewLine,
            EmergencyBrake.Notice(_activeKeys, _command,
                !_lineMode || ObservedOwner() == ControlOwner.Driver),
            HelpLine(),
            SummaryLine(),
            TractionLine());
    }

    /// <summary>
    /// Sufit prędkości do wiersza HUD albo <c>null</c>, gdy przejazd go NIE MA.
    ///
    /// <para><b>Ta metoda istnieje z powodu, który znalazł PRZEBIEG, a nie lektura.</b>
    /// Pierwsza wersja MB-03 podawała tu <c>Units.MpsToKmh(SpeedLimitMps)</c> bez
    /// warunku — a <c>RunHeader.SpeedLimitMps</c> RZUCA przy odtwarzaniu telemetrii,
    /// i rzuca świadomie: ruch jest wtedy zadany plikiem, a nie liczony. Skutkiem był
    /// wyjątek W KAŻDEJ KLATCE (zmierzone: 12 983 w 90 sekundach), przebieg, który
    /// nigdy nie dochodził do swojego warunku końca, i job CI wiszący dziewiętnaście
    /// minut zamiast czterdziestu jeden sekund.</para>
    ///
    /// <para>Warunek pyta o TRYB, a nie łapie wyjątku: wyjątek jest tu informacją, że
    /// pytanie nie ma sensu, więc poprawną odpowiedzią jest go nie zadać. Złapanie go
    /// zamieniłoby świadomą decyzję `RunHeader` w cichy `catch`.</para>
    /// </summary>
    private double? SufitKmh() =>
        _fromTelemetryMode ? null : Units.MpsToKmh(SpeedLimitMps);

    /// <summary>
    /// Wiersz HUD o blokadzie trakcji — MB-03.
    ///
    /// <para><b>Ta metoda niczego nie rozstrzyga.</b> Podaje <see cref="TractionBlock"/>
    /// stan DWÓCH właścicieli blokady, odczytany z tego samego kroku, z którego wyszło
    /// polecenie kontrolera: obsługi stacji (<c>StationService.TractionAllowed</c>)
    /// i ochrony pociągu (<c>CabProtection.Decision</c>). Trzeciego filtru nastawnika
    /// w rdzeniu nie ma — ograniczenie prędkości obcina prędkość PO kroku
    /// (<c>TrainController.Advance</c>), a nastawnika nie rusza.</para>
    ///
    /// <para>Poza postojem <c>TractionAllowed</c> jest prawdą, bo <c>Phase</c> zwraca
    /// wtedy <c>DoorPhase.Closed</c>; przebieg bez obsługi stacji (<c>_stations</c>
    /// jest nullem) blokady drzwiami nie ma z definicji.</para>
    /// </summary>
    private string TractionLine() => TractionBlock.Line(
        _stations?.TractionAllowed ?? true,
        Faza(_stations?.Phase ?? DoorPhase.Closed),
        _cabProtection?.Decision);

    /// <summary>
    /// Panel wyniku; pusty, dopóki sesja trwa — i pusty w przebiegu, który sesji nie ma.
    ///
    /// <para>Treść składa <see cref="RunSummary"/>, czyli kod bez Godota. Tutaj zostaje
    /// jedno pytanie: czy wynik już jest. <c>Result</c> jest <c>null</c> przez cały
    /// przejazd i przestaje nim być dokładnie raz — więc pustka tego wiersza jest tą
    /// samą informacją, co brak wyniku, a nie drugą jej kopią.</para>
    /// </summary>
    private string SummaryLine() => _training?.Result is { } wynik
        ? RunSummary.Compose(wynik)
        : string.Empty;

    /// <summary>
    /// Wiersz HUD z opisem sterowania; pusty w przebiegu, którego nie prowadzi człowiek.
    ///
    /// <para><b>Ten sam warunek, co przy czytaniu klawiatury</b>, i to jest cała treść
    /// tej metody. Wiersz „W ciąg · S hamulec · X wybieg…" nad przejazdem skryptowym
    /// albo odtwarzanym z zapisu wygląda dokładnie tak samo jak nad przejazdem gracza,
    /// a mówi wtedy o klawiszach, których scena w tym przebiegu nie czyta. Milczenie
    /// jest tu informacją: pomoc jest wtedy, kiedy jest komu pomóc.</para>
    ///
    /// <para>Drugi powód jest mierzalny: przebieg z <c>--shot</c> jest skryptowy, więc
    /// zrzuty kontrolne wychodzą z HUD-em IDENTYCZNYM jak przed tą zmianą. Progi bramki
    /// <c>tools/visual/compare.py --set godot</c> są zmierzone na klatce bez geometrii,
    /// czyli na samym HUD-zie, i stały napis w każdej klatce podniósłby dokładnie tę
    /// metrykę, którą ta bramka odrzuca pustą klatkę.</para>
    ///
    /// <para><b>W trybie <c>--line</c> wiersz mówi co innego</b>, bo co innego jest
    /// prawdą: skład prowadzi <c>LineDrive</c>, więc z siedmiu klawiszy działają dwa.
    /// Do 05.09.2026 stał tu ten sam napis, co nad przejazdem gracza — obietnica
    /// siedmiu klawiszy, z których pięć nic nie robiło i nic o tym nie mówiło
    /// (<c>reports/droga-do-grywalnosci.md</c> §5.4). Decyzja właściciela z 05.09.2026:
    /// zachowanie zostaje, HUD ma to powiedzieć.</para>
    /// </summary>
    /// <returns>Opis sterowania albo pusty napis.</returns>
    /// <remarks>
    /// <para><b>Wybór idzie po WŁAŚCICIELU sterowania, a nie po trybie</b> — MB-07,
    /// 14.09.2026. Do tej pozycji `--line` znaczyło „rdzeń prowadzi" i jedno wynikało
    /// z drugiego. Od MB-07 skład da się przejąć, a wtedy pięć klawiszy z listy
    /// <c>DriverActions.TakenOverByTheCore</c> ZACZYNA działać. Wiersz zbudowany z tej
    /// listy mówiłby w tym stanie nieprawdę — i byłaby to dokładnie ta usterka, dla
    /// której ta lista powstała („bezgłośnie bezskuteczne", tylko w drugą stronę:
    /// bezgłośnie SKUTECZNE).</para>
    /// </remarks>
    private string HelpLine()
    {
        if (!_readsKeyboard)
        {
            return string.Empty;
        }

        if (!_lineMode)
        {
            return DriverInput.Help;
        }

        if (_lineCore is null)
        {
            return DriverActions.HelpWhenLegacyLineRuns;
        }

        return ObservedOwner() == ControlOwner.Driver
            ? DriverActions.HelpWhenTheDriverHasTaken
            : DriverActions.HelpWhenTheCoreDrives;
    }

    /// <summary>Właściciel sterowania składem OBSERWOWANYM; autopilot poza trybem linii.</summary>
    private ControlOwner ObservedOwner()
    {
        if (_lineCore is null || _lineCore.Trains.Count == 0)
        {
            return ControlOwner.Autopilot;
        }

        return _lineCore.Trains[Math.Clamp(_observed, 0, _lineCore.Trains.Count - 1)].Owner;
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
        // KABINA POD SYGNALIZACJĄ idzie pierwsza, bo `_lineMode` jest wtedy fałszem,
        // a wiersz ma być. Do 05.09.2026 metoda zaczynała się od `if (!_lineMode) return
        // string.Empty;` i to zdanie jest tu PRZEPISANE, a nie zostawione obok: tryb
        // ręczny z `--signalling` ma dziś bloki, autorytet i ochronę, więc milczenie
        // HUD-u opisywałoby przejazd, którego nie ma.
        if (_cabProtection is not null)
        {
            if (_cabProtection.Authority is not MovementAuthority cabAuthority
                || _cabProtection.Decision is not ProtectionDecision cabDecision)
            {
                return SignallingHud.BeforeFirstStep;
            }

            return SignallingHud.Line(
                cabAuthority,
                cabDecision,
                _cabProtection.Dispatcher.Locked,
                _cabProtection.Dispatcher.Refused);
        }

        if (!_lineMode)
        {
            return string.Empty;
        }

        if (_lineCore is null)
        {
            return SignallingHud.WithoutSignalling;
        }

        if (_lineCore.Trains.Count == 0)
        {
            return SignallingHud.BeforeFirstStep;
        }

        // MB-07: wiersz mówi o składzie OBSERWOWANYM, a nie o zerowym. Gdyby został
        // przy zerowym, po przełączeniu kamery HUD opisywałby bloki i autorytet
        // składu, którego nie widać w kadrze — i wyglądałoby to na poprawny wiersz.
        var train = _lineCore.Trains[Math.Clamp(_observed, 0, _lineCore.Trains.Count - 1)];
        if (train.Drive is null || train.Authority is not MovementAuthority authority)
        {
            return SignallingHud.WithoutAuthority(train);
        }

        if (train.Protection is not ProtectionDecision decision)
        {
            return SignallingHud.WithoutProtection;
        }

        return SignallingHud.Line(
            authority, decision, _lineCore.Dispatcher.Locked, _lineCore.Dispatcher.Refused);
    }

    /// <summary>
    /// Format błędu zatrzymania: znak zawsze, dwa miejsca po przecinku, zero bez znaku.
    ///
    /// <para>Format ZOSTAJE W KODZIE, a nie idzie do katalogu tekstów — ta sama granica,
    /// co przy 6.D83: szablon niesie słowa i kolejność pól, a liczba miejsc po przecinku
    /// nie jest rzeczą, o której ma decydować tłumacz. Stała jest jedna, bo wariantów
    /// wiersza drzwi są dwa i przed 6.D99 ten sam format stał w obu wpisany z ręki.</para>
    /// </summary>
    private const string BladZatrzymaniaFormat = "+0.00;-0.00;0.00";

    /// <summary>
    /// Wiersz HUD o stacji: cykl drzwi albo dojazd, plus rejestr wywołań.
    ///
    /// <para><b>Słowa idą z katalogu (<see cref="UiText"/>), liczby są formatowane
    /// TUTAJ</b> — 6.D99, ta sama granica, co w <see cref="Hud.Update"/> od 6.D83.</para>
    /// </summary>
    private string StationLine()
    {
        if (_line is not null)
        {
            // Na końcu osi nazwa stacji i odległość pozostają dostępne w postoju,
            // ale przed założeniem postoju pokaż faktyczny koniec toru.
            if (TrackEndStop.Reached(ChainageM, _axis.LengthM) && !_line.AtStation)
            {
                return UiText.Get("hud.station.track-end");
            }

            var zaLinie = _line.Calls.Count;
            if (_line.AtStation)
            {
                var blad = _line.Calls[^1].StopErrorM.ToString(
                    BladZatrzymaniaFormat, CultureInfo.InvariantCulture);

                // POSTÓJ RĘCZNY MA WŁASNY SZABLON, a nie ten sam z inną dziurą — MB-08.
                // Pole „jeszcze N s" na postoju ręcznym nie ma czego pokazać: fazę
                // otwartą kończy człowiek, więc `DwellRemainingSeconds` zwraca NaN
                // (powód przy tej właściwości), a `NaN.ToString("F1")` to napis „NaN”.
                // Dwa osobne wywołania `UiText.Format` z literałem klucza, a nie jedno
                // z kluczem za `?:` — z tego samego powodu, co przy wierszu obsługi
                // stacji niżej: skan `UiTextTests` czyta klucz WPROST po nawiasie.
                if (_line.StopDoorControl == DoorControl.Manual)
                {
                    return UiText.Format(
                        "hud.station.doors-manual",
                        Faza(_line.Phase),
                        DoorPrompt.For(_line.Phase, _doorRefusal),
                        blad,
                        zaLinie);
                }

                var automaticStop = UiText.Format(
                    "hud.station.doors",
                    Faza(_line.Phase),
                    _line.DwellRemainingSeconds.ToString("F1", CultureInfo.InvariantCulture),
                    blad,
                    zaLinie);
                // D/F also reach LineCore under autopilot. The core refuses them with
                // AutomaticControl; show that answer while this stop is still active.
                return _doorRefusal is null
                    ? automaticStop
                    : automaticStop + '\n' + DoorPrompt.For(_line.Phase, _doorRefusal);
            }

            var nastepnaNaLinii = _line.NextStation;
            if (nastepnaNaLinii is null)
            {
                return UiText.Format("hud.station.run-over", zaLinie);
            }

            var odleglosc = nastepnaNaLinii.Value.ChainageM - ChainageM;
            // Automatyczny --line korzysta z LineDrive bez LineCore. Podpowiedź
            // hamowania jest tylko dla przejętego składu, więc nie odczytuj tu
            // identyfikatora pociągu, gdy rdzeń sesji nie istnieje.
            var fazaHamowaniaNaLinii = _lineCore is { Trains.Count: > 0 }
                && ObservedOwner() == ControlOwner.Driver
                ? _brakingCueMemory.Update(
                    _lineCore.Trains[Math.Clamp(_observed, 0, _lineCore.Trains.Count - 1)].Id,
                    nastepnaNaLinii.Value.ChainageM, true,
                    _activeKeys, _command, odleglosc, _state.SpeedMps,
                    DesignAssumptions.ControlNotchRatePerSecond,
                    _controller.ServiceBrakeMps2, BrakingPointSolver.M7)
                : BrakingCueStage.None;
            var hamowanieNaLinii = fazaHamowaniaNaLinii == BrakingCueStage.Now
                ? UiText.Get("hud.station.brake-now")
                : fazaHamowaniaNaLinii == BrakingCueStage.Prepare
                    ? UiText.Get("hud.station.brake-prepare")
                    : string.Empty;
            return UiText.Format(
                "hud.station.next",
                nastepnaNaLinii.Value.Name,
                (nastepnaNaLinii.Value.ChainageM - ChainageM).ToString(
                    "F0", CultureInfo.InvariantCulture),
                zaLinie) + hamowanieNaLinii;
        }

        if (_stations is null)
        {
            return string.Empty;
        }

        if (TrackEndStop.Reached(ChainageM, _axis.LengthM))
        {
            return UiText.Get("hud.station.track-end");
        }

        var licznik = UiText.Format(
            "hud.station.counter", _stations.Calls.Count, _stations.Missed.Count);

        if (_stations.AtStation)
        {
            // Dwa wywołania, a nie jedno z kluczem za `?:`, i to jest rozstrzygnięcie:
            // skan `UiTextTests` czyta klucz jako literał WPROST po `UiText.Get(`,
            // więc klucza schowanego za trójargumentowym operatorem nie widzi. Zapala
            // się wtedy GŁOŚNO (oba klucze jako martwe), ale naprawą jest pokazanie
            // wywołania, a nie poszerzanie wzorca skanu o składnię C#.
            var blokada = _stations.TractionAllowed
                ? UiText.Get("hud.traction.free")
                : UiText.Get("hud.traction.locked");
            return UiText.Format(
                "hud.station.doors-traction",
                Faza(_stations.Phase),
                _stations.DwellRemainingSeconds.ToString("F1", CultureInfo.InvariantCulture),
                blokada,
                _stations.Calls[^1].StopErrorM.ToString(
                    BladZatrzymaniaFormat, CultureInfo.InvariantCulture),
                licznik);
        }

        if (_stations.Finished)
        {
            return UiText.Format("hud.station.no-more", licznik);
        }

        var approach = _stations.Approach(ChainageM);
        var okno = approach.WithinWindow ? UiText.Get("hud.station.in-window") : string.Empty;
        var fazaHamowania = _brakingCueMemory.Update(
            SignalledTrainId, approach.ChainageM, !approach.WithinWindow,
            _activeKeys, _command, approach.DistanceM, _state.SpeedMps,
            DesignAssumptions.ControlNotchRatePerSecond, _controller.ServiceBrakeMps2,
            BrakingPointSolver.M7);
        var hamowanie = fazaHamowania == BrakingCueStage.Now
            ? UiText.Get("hud.station.brake-now")
            : fazaHamowania == BrakingCueStage.Prepare
                ? UiText.Get("hud.station.brake-prepare")
                : string.Empty;
        return UiText.Format(
            "hud.station.approach",
            approach.DisplayName,
            approach.DistanceM.ToString("F0", CultureInfo.InvariantCulture),
            _stations.WindowM.ToString("F1", CultureInfo.InvariantCulture),
            okno + hamowanie,
            licznik);
    }

    /// <summary>
    /// Nazwa fazy cyklu drzwi — z katalogu tekstów, klucz na wartość wyliczenia.
    ///
    /// <para>Ramię domyślne zwraca <c>phase.ToString()</c> i tak zostaje:
    /// wartość spoza wyliczenia nie ma nazwy po polsku, więc klucza dla niej nie ma
    /// czego wpisać. Gdyby <c>DoorPhase</c> urosło o ósmą fazę, to ramię pokaże jej
    /// nazwę angielską — widocznie, zamiast rzucić na ekran gracza.</para>
    /// </summary>
    private static string Faza(DoorPhase phase) => phase switch
    {
        DoorPhase.Closed => UiText.Get("hud.door.closed"),
        DoorPhase.Unlocking => UiText.Get("hud.door.unlocking"),
        DoorPhase.Opening => UiText.Get("hud.door.opening"),
        DoorPhase.Open => UiText.Get("hud.door.open"),
        DoorPhase.ClosingWarning => UiText.Get("hud.door.closing-warning"),
        DoorPhase.Closing => UiText.Get("hud.door.closing"),
        DoorPhase.Checking => UiText.Get("hud.door.checking"),
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
            + $"sesja={_logStep} kroków resetów={_replay?.Resets.Count ?? 0} "
            + $"zapis={_replayPath}"));

        // Podsumowanie ochrony LICZBAMI, w tym samym kształcie, co wypisuje
        // `Sim.Runner replay --atp`. Telemetria nie ma kolumny o ingerencji — polecenie
        // po niej wygląda tak samo jak polecenie maszynisty, który sam nacisnął hamulec
        // — więc bez tego wiersza obie strony mogłyby zgodzić się co do bitu, robiąc
        // ochronę w dwóch różnych miejscach. Zero ingerencji jest wynikiem, nie brakiem
        // wyniku, więc wiersz wychodzi zawsze, gdy ochrona była wpięta.
        if (_cabProtection is CabProtection cab)
        {
            GD.Print(string.Create(
                CultureInfo.InvariantCulture,
                $"[ATP] ostrzeżeń={cab.Warnings} ingerencji służbowych={cab.ServiceInterventions} "
                + $"awaryjnych={cab.EmergencyInterventions} "
                + $"max żądanie={cab.MaxBrakeDemandMps2:F3} m/s² "
                + $"(hamulec służbowy {cab.Protection.ServiceBrakeMps2:F3} m/s²) "
                + $"tras zaryglowanych={cab.Dispatcher.Locked} odmów={cab.Dispatcher.Refused}"));
        }

        // STAN SESJI NA KONIEC ZAPISU. Zapis wejść kończy się tam, gdzie się kończy —
        // niekoniecznie na ostatnim celu — więc „sesja nie skończyła się" jest tu
        // WYNIKIEM, a nie brakiem wyniku, i musi mieć wiersz. Bez niego log odtworzenia
        // wygląda identycznie dla zapisu, który dowozi do celu, i dla takiego, który
        // urywa się w tunelu.
        if (_training is TrainingSession sesja)
        {
            GD.Print(sesja.Result is { } wynik
                ? $"[SESJA] {wynik}"
                : $"[SESJA] trwa: cele {string.Join(", ", sesja.TargetStopIds)}, "
                  + $"obsłużonych {ObsluzonychCelow(sesja)}");
        }

        GetTree().Quit();
    }

    /// <summary>
    /// Ile celów sesji ma domknięte wywołanie stacji — liczone z
    /// <see cref="StationService.Calls"/>, a nie z licznika własnego.
    ///
    /// <para>Metoda istnieje wyłącznie dla wiersza logu i dlatego liczy to samo, co
    /// liczy sesja, zamiast trzymać drugi licznik. Drugi licznik rozjechałby się
    /// z pierwszym dokładnie w chwili, w której jeden z nich dostałby reset.</para>
    /// </summary>
    private int ObsluzonychCelow(TrainingSession sesja)
    {
        if (_stations is null)
        {
            return 0;
        }

        var ile = 0;
        foreach (var id in sesja.TargetStopIds)
        {
            foreach (var call in _stations.Calls)
            {
                if (call.StopId == id && double.IsFinite(call.DepartureSeconds))
                {
                    ile++;
                    break;
                }
            }
        }

        return ile;
    }

    /// <summary>
    /// Koniec odtwarzania telemetrii: plik ma skończoną liczbę próbek, więc przebieg
    /// też. Drugi — obok <see cref="FinishReplayRun"/> — tryb, który KOŃCZY SIĘ SAM,
    /// i z tego samego powodu: warunek końca przychodzi z pliku, a nie ze scenariusza.
    ///
    /// <para>Wiersz podsumowania podaje LICZBĘ PRZYJĘTYCH PRÓBEK obok liczby wczytanych.
    /// Kod wyjścia zero tych dwóch liczb nie odróżnia: scena, która przyjęłaby pierwszą
    /// próbkę i uznała przebieg za skończony, wychodzi zerem tak samo jak ta, która
    /// przeszła cały plik — a jej telemetria miałaby jeden wiersz i wywaliła się
    /// dopiero na porównaniu, bez powiedzenia dlaczego.</para>
    /// </summary>
    private void FinishFromTelemetryRun()
    {
        if (_done)
        {
            return;
        }

        _done = true;
        WriteTelemetry();
        GD.Print(string.Create(
            CultureInfo.InvariantCulture,
            $"[RUCH ZADANY] koniec: próbek przyjętych={_trackIndex + 1} "
            + $"z {_track!.Samples.Count} kroków={_state.Steps} "
            + $"t={_state.TimeSeconds(_step):F3} s chainage={ChainageM:F3} m "
            + $"droga={_state.DistanceM:F3} m klatek={_frames} "
            + $"głowica={_playbackStep} zapis={_fromTelemetryPath}"));
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
        // Meshes keep their own native references to the concrete material.
        // Release the C# handle only after streaming has stopped with the scene.
        _tunnelMaterial?.Dispose();
        _tunnelMaterial = null;
        base._ExitTree();
    }

    private void FinishLineRun()
    {
        if (_lineCompletionReported)
        {
            return;
        }

        _lineCompletionReported = true;
        var interactive = _readsKeyboard && _callsPath is null && _replay is null;
        _done = !interactive;

        // Linia skończyła się PRZED końcem zapisu albo przejazdu z klawiatury — 6.M1.
        // Oba pliki mają wtedy powstać tak samo, jak przy końcu odtworzenia.
        WriteTelemetry();
        WriteInputLog();
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

        // DRUGI WYPIS `[TUNEL]`, NA KOŃCU PRZEJAZDU — MB-07, 14.09.2026.
        //
        // Pierwszy stoi w `SetUpScene` i opisuje BUDOWĘ SCENY, a nie przejazd: jest
        // wypisywany raz, zanim padnie pierwszy krok, więc dla całego przejazdu mówi
        // `wczytań 2 zwolnień 0` — czyli stan okna startowego. Zmierzone na tym samym
        // przejeździe sondą w kopii: naprawdę jest **44 wczytania i 43 zwolnienia**,
        // maksimum **1 wczytanie i 1 zwolnienie na klatkę**, a szczyt rezydentnych to
        // **4 z 12** chunków.
        //
        // Bez tego wiersza regresji streamingu NIE MA JAK ZOBACZYĆ, a MB-07 podwaja
        // liczbę rzeczy, za którymi okno może pójść: pole „Czego NIE wolno zrobić bez
        // pomiaru" tej pozycji wymienia przycięcia streamingu wprost. Wiersz różni się
        // od pierwszego znacznikiem `koniec`, żeby dało się je rozróżnić w logu
        // i w bramce — dwa wiersze o tej samej treści byłyby gorsze niż jeden.
        if (_manifest is not null)
        {
            GD.Print(string.Create(
                CultureInfo.InvariantCulture,
                $"[TUNEL koniec] {_manifest.Id}: wczytań {_tunnel.Loaded} zwolnień "
                + $"{_tunnel.Freed} przez cały przejazd, rezydentne na końcu "
                + $"{_tunnel.LoadedChunks}/{_manifest.Chunks.Count} chunków, "
                + $"{_tunnel.MeshNodes} siatek"));
        }

        WriteCalls(result);
        if (!interactive)
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
        // 6.C4: widok inspekcyjny NIE jedzie do celu. Trzy widoki jazdy muszą, bo
        // kamerę wieszają na pojeździe; ten bierze geometrię z osi, więc przejazd
        // byłby kosztem bez skutku widocznego w kadrze. Zmierzone: zrzut z 2521,1 m
        // kosztuje 14 686 kroków symulacji w widoku `outside` i 0 tutaj.
        //
        // Gałąź jest PUSTA, a nie zwraca z metody, i to jest poprawka mojej własnej
        // usterki z tej samej godziny: pierwsza wersja wychodziła stąd przez `return`
        // i pomijała OGON metody, w którym stoi `_shotCountdown = 5` — jedyny wyzwalacz
        // migawki. Scena nie robiła wtedy zrzutu wcale i chodziła do końca świata;
        // `timeout` ubił ją po 300 s, gdy `outside` kończy w 1,2 s. Pusta gałąź zostawia
        // ten wyzwalacz JEDNEMU pisarzowi, zamiast kopiować go do drugiej drogi.
        //
        // Skład zostaje tam, gdzie stał (kilometraż 0), i to jest właściwe: kamera
        // inspekcyjna ma pokazać RURĘ, a nie pojazd w niej. Kadr z pojazdem daje
        // widok `outside`.
        if (_view == ViewKind.Inspect)
        {
        }
        else if (_lineMode)
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
                Math.Min(ChainageM, _axis.LengthM), _train.LengthM,
                DesignAssumptions.ChaseRevealFromM);
            Abort(ExitViewUnavailable, string.Create(
                CultureInfo.InvariantCulture,
                $"[ZRZUT] {availability.Reason}; zrzut na {ChainageM:F1} m nie powstaje — "
                + $"kadr byłby płytą pudła, a plik nazywałby się chase"));
            return;
        }

        // Kilka klatek na dojście świateł i materiałów, zanim zapadnie migawka.
        _shotCountdown = 5;
    }

    /// <summary>
    /// Kilometraż, który kadr NAPRAWDĘ pokazuje — i to nie zawsze jest kilometraż
    /// pojazdu.
    ///
    /// <para>Trzy widoki jazdy wieszają kamerę na składzie, więc tematem kadru jest
    /// pozycja pojazdu (<see cref="ChainageM"/>). Widok <see cref="ViewKind.Inspect"/>
    /// bierze geometrię z osi i pojazdu do niej nie prowadzi, więc pozycja pojazdu
    /// mówi o kadrze tyle, ile o nim mówi pogoda: zmierzone przy 6.C4, zrzut z 2521,1 m
    /// zapisywał <c>chainage_m = 94,0</c>, bo tam stał skład. Metadane opisywały wtedy
    /// INNE miejsce osi niż to, które widać, i bramka
    /// <c>tools/ci/assert_shot_metadata.py</c> słusznie by to odrzuciła.</para>
    ///
    /// <para><b>Pole jest DOPISANE, a nie podmienione:</b> <c>chainage_m</c> zostaje
    /// pozycją pojazdu we wszystkich czterech widokach, bo na nim stoi kontrola peronu
    /// („peron jest przy składzie"), której dla widoku inspekcyjnego nie da się
    /// przenieść — skład jest gdzie indziej i to jest cały sens tego widoku.</para>
    /// </summary>
    private double SubjectChainageM =>
        _view == ViewKind.Inspect ? _shotChainageM : ChainageM;

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
    /// Plik jest JEDEN na prefiks, więc kolejne ujęcia go nadpisują. Pole `scene`
    /// opisuje rezydentne chunki przejezdnej osi, które sprawdza predykat
    /// streamowania. Osobna sceneria za końcem osi nie jest częścią tego manifestu
    /// i nie może rozszerzać jego obwiedni. `last_shot` opisuje tylko ostatnie ujęcie.
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
        var tailBounds = _tunnel.VisualContinuationBounds();
        var tailPresent = tailBounds.HasValue && _visualTailAxis is not null;
        var tailPresentJson = tailPresent ? "true" : "false";
        var tailLow = tailBounds?.Position ?? Vector3.Zero;
        var tailHigh = tailBounds?.End ?? Vector3.Zero;
        var tailMinJson = tailPresent
            ? string.Create(CultureInfo.InvariantCulture,
                $"[{tailLow.X:F4}, {tailLow.Y:F4}, {tailLow.Z:F4}]") : "null";
        var tailMaxJson = tailPresent
            ? string.Create(CultureInfo.InvariantCulture,
                $"[{tailHigh.X:F4}, {tailHigh.Y:F4}, {tailHigh.Z:F4}]") : "null";
        var tailLengthM = tailPresent ? _visualTailAxis!.Axis.LengthM : 0.0;
        var tailSeamGapM = tailPresent
            ? _visualTailAxis!.CentreLinePoint(0.0).DistanceTo(_sceneAxis.CentreLinePoint(_axis.LengthM))
            : 0.0f;
        var json = string.Create(CultureInfo.InvariantCulture, $$"""
        {
         "engine": "godot",
         "engine_version": "{{Engine.GetVersionInfo()["string"]}}",
         "manifest_version": "{{_manifest.Id}}/{{_manifest.Variant}}",
         "resolution": [{{width}}, {{height}}],
         "last_shot": {"view": "{{_view}}", "chainage_m": {{ChainageM:F3}}, "steps": {{_state.Steps}},
                       "subject_chainage_m": {{SubjectChainageM:F3}}},
         "scene": {
          "bbox_min": [{{lo.X:F4}}, {{lo.Y:F4}}, {{lo.Z:F4}}],
          "bbox_max": [{{hi.X:F4}}, {{hi.Y:F4}}, {{hi.Z:F4}}],
          "size_m": [{{bounds.Size.X:F4}}, {{bounds.Size.Y:F4}}, {{bounds.Size.Z:F4}}],
          "mesh_objects": {{_tunnel.ResidentMeshNodes}},
          "vertices": {{faces * 3}},
          "faces": {{faces}},
          "chunks_loaded": {{_tunnel.LoadedChunks}},
          "chunks_declared": {{_manifest.Chunks.Count}},
          "window_low_m": {{_tunnel.WindowLowM:F3}},
          "window_high_m": {{_tunnel.WindowHighM:F3}},
          "axis_length_m": {{_manifest.AxisLengthM:F3}}
         },
         "visual_continuation": {
          "present": {{tailPresentJson}},
          "mesh_objects": {{_tunnel.VisualContinuationMeshNodes}},
          "bbox_min": {{tailMinJson}},
          "bbox_max": {{tailMaxJson}},
          "axis_length_m": {{tailLengthM:F3}},
          "seam_gap_m": {{tailSeamGapM:F4}}
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
