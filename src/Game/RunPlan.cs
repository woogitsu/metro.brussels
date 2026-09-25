using System;
using System.Collections.Generic;
using System.Globalization;

namespace MetroBxl.Game;

/// <summary>
/// Decyzje, jakie scena podejmuje z wiersza poleceń, ZANIM dotknie Godota.
///
/// <para><b>Dlaczego osobny plik.</b> <see cref="FirstRun"/> ma 847 linii i do
/// 03.09.2026 nie miał ani jednego testu jednostkowego — <c>grep -rn "FirstRun" tests/</c>
/// nie dawał ani jednego trafienia. Jedyne, co go pilnowało, to asercje na NAPISACH
/// w kodzie źródłowym, w Pythonie, w <c>tools/tests/test_ci_workflows.py</c>:
/// <c>assert "_line!.Step(" in text</c>. Taki test nie odróżnia kodu wykonywanego od
/// zakomentowanego i nie dotyka ani jednej gałęzi.</para>
///
/// <para>Ten plik NIE importuje Godota, więc <c>tests/Game.Tests</c> może go wołać
/// wprost. Ta sama konwencja, którą projekt zastosował w <c>tools/blender/</c>: czysta
/// logika wychodzi spod <c>bpy</c>, a w oryginale zostaje budowa siatek i eksport.</para>
///
/// <para><b>Co dokładnie tędy przeszło.</b> Trzy usterki, wszystkie zmierzone, wszystkie
/// opisane w komentarzach przy odpowiednich warunkach niżej: literówka
/// <c>--at-chainag=2000</c> kończąca się kodem 0 i zrzutem stojącego składu,
/// <c>--view=zmyslony</c> cicho spadające do kabiny, oraz <c>--at-chainage=abc</c>
/// wywalające wyjątek w środku <c>_Ready</c> i zostawiające pętlę klatek kręcącą się
/// w nieskończoność aż do wypalenia <c>timeout-minutes</c> w CI.</para>
/// </summary>
public sealed class RunPlan
{
    /// <summary>Argumenty, które scena rozumie. Lista jest jawna, bo argument spoza niej
    /// ma ZATRZYMAĆ przebieg, a nie zostać po cichu zignorowany.</summary>
    public static readonly string[] KnownArguments =
    {
        "telemetry", "shot", "sample-every", "steps-per-frame", "jitter",
        "at-chainage", "view", "axis", "no-geometry", "assets", "manifest", "shell",
        // `cab` stoi przy `shell` i `platforms`, bo jest tym samym: ścieżką do bryły
        // wczytywanej przez scenę. Bez tego wpisu `FirstRun` CZYTAŁO `--cab`, a plan
        // odrzucał je jako „nieznany argument" — czyli nadpisanie było nieosiągalne,
        // a jedyną drogą do innej kabiny było przeniesienie pliku.
        "platforms", "cab", "visual-continuation",
        "line", "calls", "limit-kmh", "signalling", "scheduled-entries",
        "input-log", "replay", "from-telemetry",
        // MB-07. Oba wpisy są KONIECZNE, a nie wygodne: lista jest JAWNA i argument
        // spoza niej zatrzymuje przebieg, więc bez nich `--trains=2` byłoby odrzucone
        // jako nieznane — dokładnie tak, jak `--cab` było odrzucane do MB-05.
        "trains", "headway-steps",
    };

    /// <summary>Widoki, jakie scena potrafi ustawić. Inna wartość jest BŁĘDEM, nie domyślną.</summary>
    public static readonly string[] KnownViews = { "cab", "chase", "outside", "inspect", "side", "platform" };

    /// <summary>
    /// Argumenty, których wartością jest ŚCIEŻKA. Pusta wartość jest dla nich błędem.
    /// </summary>
    /// <remarks>
    /// <para><b>6.A28.</b> Do 07.09.2026 <c>--telemetry=</c> z pustą wartością
    /// przechodziło jako plan POPRAWNY: kod 0, <c>IsValid</c> prawdziwe,
    /// <c>TelemetryPath</c> równe napisowi pustemu — a nie <c>null</c>, więc scena
    /// zbierała wiersze telemetrii i na koniec próbowała zapisać je pod pustą nazwą.
    /// Wartość tej opcji jest napisem, więc pustka nie wywracała żadnego rozbioru.</para>
    ///
    /// <para><b>Jedna lista, nie dziesięć osobnych sprawdzeń — i to jest ZMIERZONE.</b>
    /// Pole „Wyjście" pozycji 6.A28 żądało rozstrzygnięcia pomiarem, ile opcji
    /// ścieżkowych przyjmuje dziś pustkę, bo od tego zależało, czy poprawka jest jedna
    /// i wspólna. Pomiar: <b>dziewięć z dziesięciu</b> przyjmowało (kod 0), a dziesiąta
    /// (<c>--calls</c>) była odrzucana z powodu NIEZWIĄZANEGO z pustką — wymaga
    /// <c>--line</c>. Poprawka jest więc jedna.</para>
    ///
    /// <para><b>Dlaczego dziesięć, a nie dziewięć.</b> Wpis wymieniał
    /// <c>--telemetry</c>, <c>--shot</c>, <c>--replay</c>, <c>--from-telemetry</c>,
    /// <c>--axis</c>, <c>--manifest</c>, <c>--calls</c>, <c>--signalling</c>
    /// i <c>--input-log</c>. Dziesiąta to <c>--assets</c>, której wartość jest ścieżką
    /// katalogu (<c>Argument("assets") ?? RepoPath("build/t400")</c> w
    /// <c>FirstRun</c>) — wpis o niej nie wiedział.</para>
    ///
    /// <para>Lista jest osobna od <c>KnownArguments</c> celowo: tamta mówi, CZY
    /// argument jest znany, ta — jakiego KSZTAŁTU jest jego wartość. Zlanie ich
    /// w jedno zmusiłoby do wpisania kształtu przy każdym argumencie liczbowym
    /// i przy każdej fladze. Że każda pozycja tej listy stoi też w
    /// <c>KnownArguments</c> — i że jest ich dziesięć — pilnuje
    /// <c>RunPlanTests.Lista_opcji_sciezkowych_jest_podzbiorem_znanych_i_ma_dziesiec_pozycji</c>.
    /// Drugiego czytnika po stronie Pythona tu NIE MA i jest to świadome: dwa czytniki
    /// jednej listy rozjeżdżają się po cichu, a przy jednej liście w jednym pliku
    /// bramka C# widzi dokładnie to samo, co widziałby tekstowy czytnik (6.B28).</para>
    /// </remarks>
    public static readonly string[] PathArguments =
    {
        "telemetry", "shot", "replay", "from-telemetry", "axis",
        "manifest", "calls", "signalling", "input-log", "assets", "scheduled-entries",
    };

    /// <summary>
    /// Plan sygnalizacji, z którego <b>tryb ręczny</b> bierze prędkość dopuszczalną,
    /// względem katalogu repozytorium.
    ///
    /// <para><b>Ścieżka, a nie liczba — i to jest cała treść tej stałej.</b> Decyzja
    /// właściciela z 05.09.2026 mówi „72 km/h, limit planu <c>classic-2026</c>", czyli
    /// ten sam limit, którym jedzie autopilot pod <c>--signalling</c>. Liczba mieszka
    /// w <c>data/design/signalling/classic-2026.json</c> w polu
    /// <c>default_permitted_speed_kmh</c>, opisanym tam swoim źródłem (R-006: żaden
    /// dokument STIB nie podaje prędkości na torze, 72 km/h wolno używać wyłącznie jako
    /// jawnego parametru scenariusza). Wpisanie 72 do kodu zrobiłoby drugą kopię liczby
    /// bez źródła — a to jest ta sama rodzina usterek, co <c>limit=80.0 km/h</c>
    /// w nagłówku: kopia zgadza się z oryginałem tylko dopóty, dopóki nikt nie zmieni
    /// jednego z nich.</para>
    ///
    /// <para><b>Dlaczego domyślna ścieżka, a nie argument.</b> Bo tryb ręczny BEZ
    /// <c>--signalling</c> czyta z planu jedną jedyną liczbę — prędkość dopuszczalną —
    /// i mówi o tym wprost wierszem <c>[LIMIT]</c>: skład nie jest wtedy zarejestrowany
    /// w sygnalizacji, nie dostaje autorytetu jazdy i nie ma ochrony pociągu. Gdy pliku
    /// nie ma, scena ODMAWIA startu; cichy odwrót na 80 km/h byłby powrotem do usterki.</para>
    ///
    /// <para><b>Ta stała jest domyślną, a nie jedyną — od 05.09.2026.</b> Poprzednia
    /// wersja tego akapitu mówiła, że <c>--signalling</c> „łączy się wyłącznie
    /// z <c>--line</c>", i jest tu PRZEPISANA, a nie zostawiona obok: G-5 dopuszcza
    /// <c>--signalling</c> także w trybie ręcznym i wtedy plan nie tylko DAJE limit,
    /// ale go PILNUJE — skład wchodzi na bloki, dostaje autorytet i ochronę
    /// (<see cref="MetroBxl.Sim.Signalling.CabProtection"/>). Ścieżka z argumentu
    /// zastępuje wtedy tę stałą w całości, bo dwa plany w jednym przejeździe — jeden
    /// od limitu, drugi od bloków — byłyby dwiema prawdami o tej samej osi.</para>
    /// </summary>
    public const string ManualSpeedLimitPlanPath = "data/design/signalling/classic-2026.json";

    /// <summary>Domyślna liczba kroków między próbkami telemetrii.</summary>
    public const long DefaultSampleEvery = 120L;

    /// <summary>Domyślna liczba kroków symulacji na klatkę.</summary>
    public const long DefaultStepsPerFrame = 120L;

    /// <summary>Ile składów bez `--trains`. JEDEN — patrz <see cref="Trains"/>.</summary>
    public const long DefaultTrains = 1L;

    /// <summary>Górne ostrze `--trains`. Patrz uzasadnienie przy sprawdzeniu zakresu.</summary>
    public const long MaxTrains = 16L;

    /// <summary>Odstęp wyjazdu bez `--headway-steps`: 37 200 kroków = 310 s.</summary>
    public const long DefaultHeadwaySteps = 37200L;

    private RunPlan(IReadOnlyDictionary<string, string> arguments)
    {
        Arguments = arguments;
    }

    /// <summary>Surowe pary klucz–wartość, po rozbiciu <c>--klucz=wartość</c>.</summary>
    public IReadOnlyDictionary<string, string> Arguments { get; }

    /// <summary>Kod wyjścia, gdy plan jest odmową. Zero, gdy plan jest poprawny.</summary>
    public int ExitCode { get; private init; }

    /// <summary>Powód odmowy albo <c>null</c>, gdy plan jest poprawny.</summary>
    public string? Error { get; private init; }

    /// <summary>Czy plan da się wykonać.</summary>
    public bool IsValid => Error is null;

    /// <summary>Ścieżka pliku telemetrii albo <c>null</c>.</summary>
    public string? TelemetryPath { get; private init; }

    /// <summary>Ścieżka zrzutu albo <c>null</c>.</summary>
    public string? ShotPath { get; private init; }

    /// <summary>
    /// Przebieg bez interakcji, prowadzony przez <c>ScenarioDrive</c>: telemetria
    /// albo zrzut.
    ///
    /// <para><c>--telemetry</c> RAZEM z <c>--replay</c> nie jest przebiegiem
    /// skryptowym — polecenie pochodzi wtedy z zapisu wejść maszynisty, a telemetria
    /// jest tylko sposobem zapisania wyniku. To rozróżnienie jest tu, a nie w scenie,
    /// bo od niego zależy, który sterownik scena w ogóle zbuduje.</para>
    ///
    /// <para>Tak samo <c>--telemetry</c> RAZEM z <c>--from-telemetry</c>: przebieg
    /// prowadzi wtedy PLIK, a telemetria jest jego echem — i to echo jest całą
    /// weryfikacją tamtego trybu, więc musi się dać zamówić. Gdyby ta para wpadała
    /// w przebieg skryptowy, scena zbudowałaby <c>ScenarioDrive</c> i „odtworzenie"
    /// wypisałoby scenariusz T-400 zamiast wczytanego przejazdu — z kodem wyjścia
    /// zero i telemetrią, która wygląda poprawnie.</para>
    /// </summary>
    public bool ScriptedMode =>
        (TelemetryPath is not null && ReplayPath is null && FromTelemetryPath is null)
        || ShotPath is not null;

    /// <summary>
    /// Czy scena w tym przebiegu CZYTA KLAWIATURĘ — czyli czy przy sterowaniu siedzi
    /// człowiek.
    ///
    /// <para>Jedno miejsce na tę decyzję, bo odpowiedź jest potrzebna w dwóch: pętla
    /// klatek pyta o nią, zanim zawoła <c>DriverInput.Read</c>, a HUD, zanim pokaże
    /// wiersz pomocy. Dwie kopie warunku rozjechałyby się w stronę, której nikt by nie
    /// zauważył od razu: wiersz „W ciąg · S hamulec" nad przejazdem, w którym W i S nic
    /// nie robią, wygląda dokładnie tak samo jak wiersz prawdziwy.</para>
    ///
    /// <para><b>Dlaczego to nie jest po prostu „nie skryptowy".</b> Odtworzenie
    /// z <c>--replay</c> też nie czyta klawiatury — polecenie przychodzi z zapisu po
    /// numerze kroku — a <see cref="ScriptedMode"/> jest w nim FAŁSZYWE, bo zapis wejść
    /// pochodzi od maszynisty. Tak samo <c>--from-telemetry</c>, gdzie polecenia nie ma
    /// w ogóle: jest gotowy ruch. Warunek musi więc wymienić WSZYSTKIE trzy tryby,
    /// a nie zaprzeczyć jednemu.</para>
    ///
    /// <para>Skutek uboczny jest tu skutkiem głównym: w przebiegu skryptowym wiersz
    /// pomocy NIE WYCHODZI na zrzut. Bramka wizualna <c>tools/visual/compare.py</c>
    /// mierzy zawartość klatki z progami zmierzonymi na klatce bez geometrii, czyli na
    /// samym HUD-zie; dopisanie do niej stałego napisu podniosłoby „ink" w klatce,
    /// którą ta bramka ma ODRZUCAĆ.</para>
    /// </summary>
    public bool ReadsKeyboard => !ScriptedMode && !ReplayMode && !FromTelemetryMode;

    /// <summary>A manual GUI run needs a visible startup error; automation keeps its exit code.</summary>
    public bool ShouldShowStartupErrorDialog(bool headless) => ReadsKeyboard && !headless;

    /// <summary>
    /// Plik, do którego zapisuje się wejścia maszynisty (numer kroku + klawisze),
    /// albo <c>null</c>. Format czyta i pisze <c>MetroBxl.Sim.Train.InputLog</c>.
    /// </summary>
    public string? InputLogPath { get; private init; }

    /// <summary>
    /// Plik zapisu wejść, z którego przejazd ma być odtworzony, albo <c>null</c>.
    ///
    /// <para>Odtworzenie prowadzi ten sam <c>DriverNotch</c> i ten sam
    /// <c>TrainController</c>, co człowiek przy klawiaturze — różni się WYŁĄCZNIE
    /// źródłem stanu klawiszy. Gdyby odtwarzanie miało własną ścieżkę przez fizykę,
    /// porównanie z przejazdem gracza nie znaczyłoby nic.</para>
    /// </summary>
    public string? ReplayPath { get; private init; }

    /// <summary>Przejazd odtwarzany z zapisu wejść.</summary>
    public bool ReplayMode => ReplayPath is not null;

    /// <summary>
    /// Plik telemetrii, z którego przejazd ma być odtworzony jako RUCH ZADANY,
    /// albo <c>null</c>. Format czyta <see cref="TelemetryTrack"/>.
    ///
    /// <para><b>Czwarte źródło polecenia — i jedyne, w którym polecenia nie ma.</b>
    /// Autopilot, klawiatura i zapis wejść podają polecenie, które przechodzi przez
    /// fizykę; telemetria podaje WYNIK i fizyka nie liczy się drugi raz. Stąd nazwa
    /// argumentu jest inna niż <c>--telemetry</c>, choć plik ten sam: tamten to
    /// wyjście, ten to wejście, a jeden argument w dwóch rolach byłby dokładnie tą
    /// dwuznacznością, którą reszta tego pliku wycina.</para>
    ///
    /// <para>Scena jest tu WIDOKIEM w najczystszej postaci, jaką to repozytorium ma —
    /// <c>docs/01-architecture.md</c>: „Linia jest symulacją, która działa bez gracza.
    /// Kabina jest jednym z jej widoków." W tym trybie symulacja już się odbyła
    /// i leży w pliku; kabina tylko na nią patrzy.</para>
    /// </summary>
    public string? FromTelemetryPath { get; private init; }

    /// <summary>Przejazd odtwarzany z pliku telemetrii jako ruch zadany.</summary>
    public bool FromTelemetryMode => FromTelemetryPath is not null;

    /// <summary>
    /// Przejazd całą linią z zatrzymaniami na stacjach, prowadzony rdzeniem
    /// (<c>LineDrive</c>) — scena jest wtedy WIDOKIEM linii, która jedzie sama.
    ///
    /// To zdanie przewodnie z <c>docs/01-architecture.md</c> wzięte dosłownie:
    /// „Linia jest symulacją, która działa bez gracza. Kabina jest jednym z jej
    /// widoków." Tryb ręczny jest drugim widokiem tej samej linii, z człowiekiem
    /// w miejscu autopilota.
    /// </summary>
    ///
    /// <para><b>Z <c>--replay</c> telemetria nie wyłącza trybu linii</b> (6.M1): jest
    /// wtedy WYJŚCIEM odtworzenia, jak w odtworzeniu ręcznym, a nie drugim źródłem
    /// polecenia.</para>
    public bool LineMode => HasFlag("line") && (TelemetryPath is null || ReplayPath is not null);

    /// <summary>
    /// Plik, do którego przejazd linią wypisuje ZATRZYMANIA (CSV). Podanie go znaczy
    /// też „to jest przebieg weryfikacyjny", więc klatki lecą tak szybko, jak procesor
    /// zdąży — a nie w czasie ściennym, w którym 853 s przejazdu to 853 s czekania.
    /// </summary>
    public string? CallsPath { get; private init; }

    /// <summary>
    /// Prędkość dopuszczalna na torze dla przejazdu linią, km/h. <b>Bez wartości
    /// domyślnej</b> i to jest cała treść tego pola.
    ///
    /// <para>Pierwsza wersja trybu <c>--line</c> brała limit z
    /// <c>DriveScenario.PackageAFirstRun</c>, a ten woła
    /// <c>Units.KmhToMps(model.DesignMaxSpeedKmh)</c> — czyli <b>80 km/h, prędkość
    /// KONSTRUKCYJNĄ pojazdu</b>. Zmierzone: scena rozpędzała skład do 80,00 km/h
    /// i przejeżdżała linię w 724,94 s wobec 733,14 s rdzenia. Prędkość konstrukcyjna
    /// nie jest prędkością dopuszczalną na torze i <c>LineRunSettings</c> ostrzega
    /// o tym wprost.</para>
    ///
    /// <para>Źródła nie ma (R-006, #85: 72/50 km/h pochodzi z notatki DH z 2008 o sieci
    /// sprzed układu z 2009, klasa <c>manufacturer_or_trade_press</c>). Znane są tylko
    /// ograniczenia: <b>od dołu 58,68 km/h</b> z rozkładu T-401, <b>od góry 80 km/h</b>
    /// z rejestru pojazdu. Dlatego liczba musi przyjść od wołającego, tak samo jak
    /// w <c>LineRunSettings</c>, gdzie konstruktor celowo nie ma domyślnych.</para>
    ///
    /// <para><b>W trybie ręcznym ta liczba znaczy co innego niż w <c>--line</c>.</b>
    /// Tam jest prędkością dopuszczalną, którą jedzie autopilot; tu jest SUFITEM
    /// MASZYNISTY — tym, o co człowiek może poprosić — a prędkością dopuszczalną
    /// zostaje limit planu, którego pilnuje ochrona. Dwie różne liczby, i dopiero
    /// ich rozdzielenie czyni ingerencję ATP obserwowalną: przy suficie równym limitowi
    /// planu sterownik i tak nie przekroczy 72,00 km/h, więc ochrona nie ma czego łapać.
    /// Zero znaczy „nie podano" i wtedy sufitem jest limit planu.</para>
    /// </summary>
    public double LimitKmh { get; private init; }

    /// <summary>
    /// Plan sygnalizacji przejazdu; <c>null</c> znaczy „bez sygnalizacji".
    ///
    /// <para><b>Jawny argument, a nie ciche wykrywanie.</b> Scena mogłaby próbować
    /// znaleźć plan dla osi sama i po cichu jechać bez sygnalizacji, gdy go nie ma —
    /// i to jest dokładnie ta rodzina usterek, którą to repozytorium zbierało: przebieg
    /// kończy się kodem zero, a nikt nie wie, czy sygnalizacja w nim była. Bez tego
    /// argumentu przejazd jedzie bez blokad i HUD mówi to wprost; z nim prowadzi
    /// <c>LineCore</c>, czyli linia z nastawnią i autorytetem jazdy.</para>
    ///
    /// <para><b>Od 05.09.2026 argument działa też BEZ <c>--line</c></b> i wtedy znaczy
    /// „kabina jedzie pod tym planem": skład wchodzi na bloki, dostaje autorytet jazdy
    /// i ochronę, która ingeruje w polecenie człowieka
    /// (<see cref="MetroBxl.Sim.Signalling.CabProtection"/>, <see cref="ManualSignalling"/>).
    /// Podany plan zastępuje wtedy <see cref="ManualSpeedLimitPlanPath"/> także jako
    /// źródło prędkości dopuszczalnej — dwa plany w jednym przejeździe byłyby dwiema
    /// prawdami o tej samej osi.</para>
    ///
    /// <para>Plan musi pochodzić z TEJ SAMEJ osi — <c>LineCore</c> odrzuca niezgodną
    /// parę, bo autorytet i cel hamowania liczyłyby się wtedy w dwóch układach;
    /// w trybie ręcznym tę samą parę sprawdza scena, zanim zbuduje ochronę.</para>
    /// </summary>
    public string? SignallingPath { get; private init; }

    /// <summary>Explicit two-entry dated L1_A plan; absent in the normal line scenario.</summary>
    public string? ScheduledEntriesPath { get; private init; }

    /// <summary>
    /// Czy KABINA jedzie pod sygnalizacją: przejazd prowadzony poleceniem maszynisty
    /// (z klawiatury albo z zapisu wejść) i mający plan podany argumentem.
    ///
    /// <para>Jedno miejsce na tę decyzję, bo odpowiedź jest potrzebna w trzech: scena
    /// pyta o nią, zanim zbuduje <see cref="MetroBxl.Sim.Signalling.CabProtection"/>,
    /// nagłówek — zanim wybierze źródło limitu, a HUD — zanim pokaże wiersz
    /// sygnalizacji. Trzy kopie warunku rozjechałyby się dokładnie tak, jak rozjechał
    /// się kiedyś limit w nagłówku: HUD mówiący „ATP pilnuje" nad przejazdem bez ATP
    /// wygląda tak samo jak wiersz prawdziwy.</para>
    /// </summary>
    public bool ManualSignalling => SignallingPath is not null && !LineMode && !ScriptedMode;

    /// <summary>
    /// Nazwa trybu do nagłówka logu i do HUD-a.
    ///
    /// <para>Kolejność nie jest dowolna i to jest ta sama reguła, co przy
    /// <c>--replay</c>: tryb, który <c>--telemetry</c> tylko ZAPISUJE, musi stać PRZED
    /// nim, inaczej odtwarzanie z pliku nazwałoby się „telemetry" i log przestałby
    /// odróżniać przebieg policzony od odtworzonego. Bramka CI czyta ten napis
    /// grepem, więc pomyłka tutaj byłaby zieloną bramką nad złym trybem.</para>
    /// </summary>
    public string Mode => FromTelemetryPath is not null ? "from-telemetry"
        : ReplayPath is not null ? "replay"
        : TelemetryPath is not null ? "telemetry"
        : ShotPath is not null ? "shot"
        : LineMode ? "line" : "manual";

    /// <summary>Co ile kroków zapisać wiersz telemetrii.</summary>
    public long SampleEvery { get; private init; } = DefaultSampleEvery;

    /// <summary>Ile kroków symulacji na jedną klatkę.</summary>
    public long StepsPerFrame { get; private init; } = DefaultStepsPerFrame;

    /// <summary>Nierówność czasów klatek, którą tryb telemetrii wstrzykuje celowo.</summary>
    public double Jitter { get; private init; }

    /// <summary>Ile składów wpuścić na plan. Domyślnie JEDEN.</summary>
    /// <remarks>
    /// <para><b>Domyślna jedynka jest treścią, a nie wygodą.</b> Pole „Czego NIE wolno
    /// zrobić bez pomiaru" pozycji MB-07 mówi wprost: liczbę składów zwiększa się
    /// dopiero po zmierzeniu renderu, ticków, pamięci i przycięć streamingu. Domyślna
    /// dwójka zwiększyłaby ją WSZYSTKIM przebiegom naraz — w tym bramkom CI, których
    /// wzorce są przybite do przejazdu jednego składu — i zrobiłaby to po cichu.</para>
    /// </remarks>
    public long Trains { get; private init; } = DefaultTrains;

    /// <summary>Odstęp wyjazdu kolejnych składów, w krokach symulacji.</summary>
    /// <remarks>
    /// <para><b>Domyślne 37 200 kroków to 310 s przy kroku 1/120 s</b>, czyli zmierzony
    /// takt L1/L5 z GTFS (`docs/21-measured-vs-assumed.md` §4d, T-113). Jest to
    /// <b>9,1× powyżej zmierzonego minimum</b>: pierwszy krok, w którym blok wjazdowy
    /// jest wolny, to <b>4073</b> przy limicie planu 72 km/h.</para>
    ///
    /// <para><b>Czego ta liczba NIE jest: rozkładem STIB.</b> Pole „Czego NIE wolno
    /// przedstawiać jako rozkładu" zabrania tego wprost, i słusznie — pakiet A to
    /// fragment L1_A, a nie linia. 310 s jest tu ODSTĘPEM SCENARIUSZA, którego wartość
    /// wzięto ze zmierzonego taktu, żeby nie była zmyślona; kursem rozkładowym nie jest
    /// ani jeden z tych składów.</para>
    /// </remarks>
    public long HeadwaySteps { get; private init; } = DefaultHeadwaySteps;

    /// <summary>Kilometraż, na którym ma powstać zrzut.</summary>
    public double ShotChainageM { get; private init; }

    /// <summary>Widok, który scena ma ustawić.</summary>
    public ViewKind View { get; private init; } = ViewKind.Cab;

    /// <summary>
    /// Rozbija argumenty i rozstrzyga, czy da się z nich zbudować przebieg.
    /// Nie rzuca wyjątków: odmowa jest wartością zwracaną, z kodem i powodem.
    /// </summary>
    /// <param name="commandLine">Argumenty w postaci, w jakiej daje je
    /// <c>OS.GetCmdlineUserArgs()</c> — z wiodącymi myślnikami albo bez.</param>
    /// <param name="exitUnknownArgument">Kod dla argumentu spoza listy.</param>
    /// <param name="exitBadArgumentValue">Kod dla wartości, której nie da się odczytać.</param>
    public static RunPlan Parse(IEnumerable<string> commandLine,
        int exitUnknownArgument, int exitBadArgumentValue)
    {
        var arguments = new Dictionary<string, string>(StringComparer.Ordinal);
        foreach (var argument in commandLine ?? Array.Empty<string>())
        {
            var text = argument.TrimStart('-');
            var split = text.IndexOf('=');
            if (split < 0)
            {
                // Argument bez `=` jest flagą. Wartość „1" jest tu umowna i czyta ją
                // wyłącznie `HasFlag`; liczbą nigdy nie będzie.
                arguments[text] = "1";
            }
            else
            {
                arguments[text[..split]] = text[(split + 1)..];
            }
        }

        // Nieznany argument ZATRZYMUJE przebieg. Zmierzone 02.09.2026 audytem
        // mutacyjnym: przed tym warunkiem `--at-chainag=2000` — literówka na jednym
        // znaku — kończyło się kodem 0 i zrzutem o nazwie `GODOT_cab_2000m.png`
        // przedstawiającym stojący skład na 94 m. Pięć „ujęć kontrolnych" mogło więc
        // być pięcioma kopiami tego samego kadru.
        foreach (var name in arguments.Keys)
        {
            if (Array.IndexOf(KnownArguments, name) < 0)
            {
                return Refusal(arguments, exitUnknownArgument,
                    $"[ARGUMENT] nieznany argument '--{name}'. Znane: --{string.Join(" --", KnownArguments)}");
            }
        }

        // Pusta wartosc opcji SCIEZKOWEJ (6.A28). Sprawdzane TUTAJ, a nie przy kazdym
        // uzyciu: uzyc jest wiecej niz opcji, a odmowa ma padac PRZED przejazdem, nie
        // przy zapisie wyniku — inaczej scena przejezdza cala linie i wywala sie na
        // koncu, a zebrane wiersze telemetrii ida do kosza.
        //
        // `IsNullOrWhiteSpace`, nie `Length == 0`: `--telemetry=" "` jest tym samym
        // rodzajem wejscia i tym samym rodzajem usterki, tylko trudniejszym do
        // zauwazenia w wierszu polecen.
        foreach (var name in PathArguments)
        {
            if (arguments.TryGetValue(name, out var path) && string.IsNullOrWhiteSpace(path))
            {
                return Refusal(arguments, exitBadArgumentValue,
                    $"[ARGUMENT] --{name} wymaga ścieżki, a dostało wartość pustą. "
                    + "Pusta ścieżka nie jest sposobem na pominięcie zapisu: scena przyjęłaby plan "
                    + "jako poprawny i przejechała cały odcinek, żeby wywrócić się "
                    + "dopiero przy zapisie wyniku. Podaj ścieżkę albo pomiń argument");
            }
        }

        if (arguments.TryGetValue("visual-continuation", out var continuation) &&
            continuation is not ("tail" or "connector-preview"))
        {
            return Refusal(arguments, exitBadArgumentValue,
                "[ARGUMENT] --visual-continuation przyjmuje tail albo connector-preview.");
        }
        if (continuation == "connector-preview" && arguments.ContainsKey("no-geometry"))
        {
            return Refusal(arguments, exitBadArgumentValue,
                "[ARGUMENT] --visual-continuation=connector-preview wymaga geometrii.");
        }

        if (!TryLong(arguments, "sample-every", DefaultSampleEvery, out var sampleEvery, out var error))
        {
            return Refusal(arguments, exitBadArgumentValue, error!);
        }

        if (!TryLong(arguments, "steps-per-frame", DefaultStepsPerFrame, out var stepsPerFrame, out error))
        {
            return Refusal(arguments, exitBadArgumentValue, error!);
        }

        if (!TryDouble(arguments, "jitter", 0.0, out var jitter, out error))
        {
            return Refusal(arguments, exitBadArgumentValue, error!);
        }

        if (!TryLong(arguments, "trains", DefaultTrains, out var trains, out error))
        {
            return Refusal(arguments, exitBadArgumentValue, error!);
        }

        // Zakres jest tu SPRAWDZANY, inaczej niż przy `--steps-per-frame`, i to nie
        // jest niekonsekwencja. `--trains=0` dałoby przejazd bez ani jednego składu,
        // czyli PUSTĄ SCENĘ kończącą się kodem 0 — a to jest dokładnie ten wynik,
        // przed którym ostrzega §5 CLAUDE.md („skrypt bez błędu potrafi wyprodukować
        // pustą scenę"). Górne ostrze stoi na SZESNASTU i jest arbitralne w wartości,
        // ale nie w istnieniu: koszt drugiego składu jest zmierzony (35 752 B
        // geometrii), kosztu szesnastu nikt nie mierzył, a liczba bez ostrza zamienia
        // literówkę w minutę czekania na scenę, której nie da się narysować.
        if (trains is < 1 or > MaxTrains)
        {
            return Refusal(arguments, exitBadArgumentValue,
                $"[ARGUMENT] '--trains={trains}' jest poza zakresem 1..{MaxTrains}. "
                + "Zero składów daje pustą scenę kończącą się powodzeniem, a górne "
                + "ostrze stoi tam, dokąd sięga pomiar (MB-07).");
        }

        if (!TryLong(arguments, "headway-steps", DefaultHeadwaySteps, out var headwaySteps, out error))
        {
            return Refusal(arguments, exitBadArgumentValue, error!);
        }

        // Zmierzone na `data/track/L1_A.json` + `classic-2026.json` przy limicie planu:
        // pierwszy krok, w którym blok wjazdowy jest CLEAR, to 4073 — i wiąże tam
        // RYGLOWANIE TRASY, a nie zajętość pudła (sama długość składu dałaby 1817).
        // Odstęp mniejszy nie jest błędem argumentu: skład po prostu czeka, a `LineCore`
        // rozstrzyga to poprawnie. Odstęp UJEMNY jest błędem, bo `LineCore.Add` odmawia
        // wyjazdu w przeszłości i robi to wyjątkiem w środku `_Ready`.
        if (headwaySteps < 0L)
        {
            return Refusal(arguments, exitBadArgumentValue,
                $"[ARGUMENT] '--headway-steps={headwaySteps}' jest ujemny — wyjazd "
                + "w przeszłości jest cichym przesunięciem rozkładu, nie wyjazdem.");
        }

        if (!TryDouble(arguments, "at-chainage", 0.0, out var chainage, out error))
        {
            return Refusal(arguments, exitBadArgumentValue, error!);
        }

        // Nieznany widok jest BŁĘDEM, nie domyślną kabiną. Zmierzone: `--view=zmyslony`
        // cicho spadało do widoku z kabiny, więc zrzut „z zewnątrz" mógł być kolejnym
        // kadrem z kabiny i nikt by tego nie zauważył po nazwie pliku.
        var view = Argument(arguments, "view") ?? "cab";
        if (Array.IndexOf(KnownViews, view) < 0)
        {
            return Refusal(arguments, exitBadArgumentValue,
                $"[ARGUMENT] nieznany widok '--view={view}'. Znane: {string.Join(", ", KnownViews)}");
        }

        // `--line` i `--telemetry` to DWA RÓŻNE źródła polecenia dla tego samego składu.
        // `--shot` nie jest sterownikiem, tylko migawką, więc z `--line` się łączy —
        // i właśnie po to, żeby dało się OBEJRZEĆ skład stojący przy peronie
        // z otwartymi drzwiami, a nie tylko przeczytać, że się zatrzymał.
        if (arguments.ContainsKey("line") && arguments.ContainsKey("telemetry")
            && !arguments.ContainsKey("replay"))
        {
            return Refusal(arguments, exitBadArgumentValue,
                "[ARGUMENT] --line nie łączy się z --telemetry: to dwa różne źródła "
                + "polecenia dla tego samego składu, a telemetria jest porównywana "
                + "z rdzeniem CO DO BITU, więc pomyłka tutaj wyglądałaby jak rozjazd fizyki");
        }

        // `--replay` RAZEM z `--line` jest od 6.M1 POPRAWNE, i ten akapit jest
        // przepisany, a nie dopisany obok. Do 6.M1 stała tu odmowa „zapis wejść
        // i autopilot to dwa różne źródła polecenia dla tego samego składu". Od MB-06
        // linia ma jednak MASZYNISTĘ przy jednym ze składów, a zapis wejść niesie jego
        // polecenia — przejęcie, oddanie, drzwi, obserwację — obok klawiszy. Autopilot
        // prowadzi resztę linii i skład nieprzejęty, więc źródła się nie dublują: każdy
        // skład ma w każdym kroku DOKŁADNIE jednego właściciela, a rozstrzyga go zapis.
        //
        // Jedna odmowa zostaje, i jest nowa: bez `--signalling` linię prowadzi sam
        // `LineDrive`, bez `LineCore`, więc nie ma w niej maszynisty ani przejęcia —
        // zapis wejść nie miałby do kogo trafić, a odtworzenie wyglądałoby jak przejazd
        // autopilota podpisany cudzym zapisem.
        if (arguments.ContainsKey("replay") && arguments.ContainsKey("line")
            && !arguments.ContainsKey("signalling"))
        {
            return Refusal(arguments, exitBadArgumentValue,
                "[ARGUMENT] --replay z --line wymaga --signalling: bez planu sygnalizacji "
                + "linia nie ma maszynisty, więc zapis wejść nie ma do kogo trafić");
        }

        // `--shot` nie jest sterownikiem, ale odtworzenie kończy się
        // na ostatnim kroku ZAPISU, a zrzut na zadanym kilometrażu — dwa różne warunki
        // końca tego samego przebiegu, więc odmowa.
        if (arguments.ContainsKey("replay") && arguments.ContainsKey("shot"))
        {
            return Refusal(arguments, exitBadArgumentValue,
                "[ARGUMENT] --replay nie łączy się z --shot: odtworzenie kończy się na ostatnim "
                + "kroku zapisu, a zrzut na zadanym kilometrażu — to dwa warunki końca naraz");
        }

        // `--from-telemetry` jest CZWARTYM źródłem ruchu tego samego składu, obok
        // autopilota, klawiatury i zapisu wejść — i jedynym, w którym fizyka nie liczy
        // się wcale: ruch jest ZADANY plikiem. Odmowy są tu z tego samego powodu, co
        // trzy wyżej, i wymieniają OBA tryby z nazwy, bo cichy wybór jednego z dwóch
        // źródeł daje przejazd, którego po wyniku nie da się odróżnić od zamówionego.
        //
        // Powód dodatkowy, którego tamte trzy nie mają: te dwa źródła nawet nie
        // rozjeżdżałyby się „trochę". Ruch zadany bierze kilometraż WPROST z pliku,
        // więc skład stałby w miejscu z pliku, a nie tam, dokąd doprowadziłby go
        // sterownik — i telemetria wyszłaby echem pliku bez względu na to, co robił
        // rdzeń. Bramka porównująca ją z rdzeniem byłaby wtedy zielona zawsze.
        if (arguments.ContainsKey("from-telemetry") && arguments.ContainsKey("line"))
        {
            return Refusal(arguments, exitBadArgumentValue,
                "[ARGUMENT] --from-telemetry nie łączy się z --line: odtwarzany ruch zadany "
                + "i autopilot to dwa różne źródła ruchu dla tego samego składu");
        }

        if (arguments.ContainsKey("from-telemetry") && arguments.ContainsKey("replay"))
        {
            return Refusal(arguments, exitBadArgumentValue,
                "[ARGUMENT] --from-telemetry nie łączy się z --replay: telemetria jest WYNIKIEM "
                + "odtwarzanym bez fizyki, a zapis wejść POLECENIEM przechodzącym przez fizykę");
        }

        if (arguments.ContainsKey("from-telemetry") && arguments.ContainsKey("input-log"))
        {
            return Refusal(arguments, exitBadArgumentValue,
                "[ARGUMENT] --from-telemetry nie łączy się z --input-log: w ruchu zadanym scena "
                + "nie czyta klawiatury, więc plik nazwany zapisem wejść byłby pusty albo "
                + "opisywałby przejazd, którego nikt nie prowadził");
        }

        if (arguments.ContainsKey("from-telemetry") && arguments.ContainsKey("shot"))
        {
            return Refusal(arguments, exitBadArgumentValue,
                "[ARGUMENT] --from-telemetry nie łączy się z --shot: odtwarzanie kończy się na "
                + "ostatniej próbce pliku, a zrzut na zadanym kilometrażu — to dwa warunki "
                + "końca naraz");
        }

        if (arguments.ContainsKey("from-telemetry") && arguments.ContainsKey("signalling"))
        {
            return Refusal(arguments, exitBadArgumentValue,
                "[ARGUMENT] --from-telemetry nie łączy się z --signalling: ochrona pociągu "
                + "ingeruje w POLECENIE, a w ruchu zadanym polecenia nie ma — hamulec ATP "
                + "nie zmieniłby ani jednego metra i wyszedłby przejazd z ochroną, "
                + "która niczego nie chroni");
        }

        // `--sample-every` w ruchu zadanym byłby argumentem BEZCZYNNYM, a taki jest
        // gorszy od nieznanego: nieznany zatrzymuje przebieg, bezczynny wygląda jak
        // działający. Gęstość próbek jest właściwością PLIKU — odtwarzanie wypisuje
        // dokładnie te próbki, które wczytało, i żadnej innej.
        if (arguments.ContainsKey("from-telemetry") && arguments.ContainsKey("sample-every"))
        {
            return Refusal(arguments, exitBadArgumentValue,
                "[ARGUMENT] --from-telemetry nie łączy się z --sample-every: gęstość próbek "
                + "przychodzi z odtwarzanego pliku, a nie z argumentu");
        }

        // Zapisywać można TYLKO to, co naprawdę przyszło od maszynisty. W przebiegu
        // skryptowym i w `--line` polecenie liczy rdzeń, więc plik nazwany „zapisem
        // wejść" opisywałby przejazd, którego nikt nie prowadził — i odtworzony
        // wyglądałby jak dowód determinizmu wejścia gracza, którym by nie był.
        //
        // `--line` jest od 6.M1 poza tą listą: przejazd linii ma maszynistę przy
        // jednym ze składów (MB-06), a jego polecenia i klawisze trafiają do zapisu.
        if (arguments.ContainsKey("input-log") && !arguments.ContainsKey("replay")
            && (arguments.ContainsKey("shot") || arguments.ContainsKey("telemetry")))
        {
            return Refusal(arguments, exitBadArgumentValue,
                "[ARGUMENT] --input-log ma sens tylko w przejeździe prowadzonym z klawiatury "
                + "albo odtwarzanym z --replay: w --shot i --telemetry polecenie "
                + "pochodzi z rdzenia, a nie od maszynisty");
        }

        if (!TryDouble(arguments, "limit-kmh", 0.0, out var limitKmh, out error))
        {
            return Refusal(arguments, exitBadArgumentValue, error!);
        }

        if (arguments.ContainsKey("line") && limitKmh <= 0.0)
        {
            return Refusal(arguments, exitBadArgumentValue,
                "[ARGUMENT] --line wymaga --limit-kmh: prędkość dopuszczalna na torze NIE MA "
                + "źródła (R-006), a scenariusz T-400 podaje 80 km/h, czyli prędkość "
                + "KONSTRUKCYJNĄ M7. Znane ograniczenia: od dołu 58,68 km/h z rozkładu "
                + "T-401, od góry 80 km/h z rejestru pojazdu");
        }

        // `--signalling` BEZ `--line` jest od 05.09.2026 POPRAWNE i to jest cała treść
        // G-5. Poprzednia wersja tego warunku odmawiała — „przebieg skryptowy i ręczny
        // nie mają składu zarejestrowanego w sygnalizacji" — i jest tu PRZEPISANA,
        // a nie zostawiona obok: tryb ręczny taki skład teraz rejestruje
        // (`CabProtection`), więc tamto zdanie jest nieprawdą o dzisiejszym kodzie.
        // Dopóki obowiązywało, jedyny tryb, w którym prowadzi człowiek, był jedynym,
        // w którym nie ma ani blokad, ani ochrony pociągu
        // (`reports/droga-do-grywalnosci.md` §1.3).
        //
        // Odmowa ZOSTAJE dla przebiegu skryptowego i z niezmienionego powodu:
        // polecenie podaje w nim `ScenarioDrive`, a jego telemetria jest porównywana
        // z rdzeniem CO DO BITU — ochrona zmieniłaby przejazd, którego zgodność jest
        // całą treścią tamtej bramki. `--line --shot` przechodzi, bo `--shot` nie jest
        // sterownikiem, tylko migawką.
        var scriptedWithoutLine = !arguments.ContainsKey("line")
            && (arguments.ContainsKey("shot")
                || (arguments.ContainsKey("telemetry") && !arguments.ContainsKey("replay")));
        if (arguments.ContainsKey("signalling") && scriptedWithoutLine)
        {
            return Refusal(arguments, exitBadArgumentValue,
                "[ARGUMENT] --signalling nie łączy się z przebiegiem skryptowym: polecenie "
                + "podaje w nim scenariusz, a jego telemetria jest porównywana z rdzeniem "
                + "co do bitu, więc ochrona pociągu zmieniłaby przejazd, którego zgodność "
                + "jest całą treścią tamtej bramki");
        }

        // `--limit-kmh` w trybie ręcznym jest SUFITEM MASZYNISTY, a prędkość dopuszczalna
        // przychodzi z planu — to dwie różne liczby i dopiero ich rozdzielenie czyni
        // ochronę widoczną. Bez `--signalling` sufitu nie miałby kto pilnować, więc
        // byłby przejazdem ręcznym z wymyśloną prędkością: dokładnie tą usterką, którą
        // naprawiło #246 (nagłówek mówił `limit=80.0 km/h`, czyli prędkość
        // KONSTRUKCYJNĄ M7, i ta liczba szła do kontrolera).
        if (arguments.ContainsKey("limit-kmh")
            && !arguments.ContainsKey("line") && !arguments.ContainsKey("signalling"))
        {
            return Refusal(arguments, exitBadArgumentValue,
                "[ARGUMENT] --limit-kmh wymaga --line albo --signalling: przebieg skryptowy "
                + "bierze limit ze scenariusza, a ręczny bez ochrony pociągu — z planu "
                + ManualSpeedLimitPlanPath
                + "; sufit ponad limit planu ma sens tylko wtedy, gdy ktoś go pilnuje");
        }

        if (arguments.ContainsKey("calls") && !arguments.ContainsKey("line"))
        {
            return Refusal(arguments, exitBadArgumentValue,
                "[ARGUMENT] --calls ma sens tylko z --line: bez przejazdu linią nie ma "
                + "zatrzymań do wypisania");
        }

        if (arguments.ContainsKey("scheduled-entries") &&
            (!arguments.ContainsKey("line") || !arguments.ContainsKey("signalling")))
        {
            return Refusal(arguments, exitBadArgumentValue,
                "[ARGUMENT] --scheduled-entries wymaga --line i --signalling.");
        }
        if (arguments.ContainsKey("scheduled-entries") &&
            (arguments.ContainsKey("trains") || arguments.ContainsKey("headway-steps")))
        {
            return Refusal(arguments, exitBadArgumentValue,
                "[ARGUMENT] --scheduled-entries wyznacza wjazdy; nie łączy się z --trains ani --headway-steps.");
        }
        return new RunPlan(arguments)
        {
            TelemetryPath = Argument(arguments, "telemetry"),
            ShotPath = Argument(arguments, "shot"),
            CallsPath = Argument(arguments, "calls"),
            InputLogPath = Argument(arguments, "input-log"),
            ReplayPath = Argument(arguments, "replay"),
            FromTelemetryPath = Argument(arguments, "from-telemetry"),
            LimitKmh = limitKmh,
            SignallingPath = Argument(arguments, "signalling"),
            ScheduledEntriesPath = Argument(arguments, "scheduled-entries"),
            SampleEvery = sampleEvery,
            StepsPerFrame = stepsPerFrame,
            Trains = trains,
            HeadwaySteps = headwaySteps,
            Jitter = jitter,
            ShotChainageM = chainage,
            View = view switch
            {
                "chase" => ViewKind.Chase,
                "outside" => ViewKind.Outside,
                "inspect" => ViewKind.Inspect,
                "side" => ViewKind.Side,
                "platform" => ViewKind.Platform,
                _ => ViewKind.Cab,
            },
        };
    }

    /// <summary>
    /// Czas jednej „klatki" w trybie skryptowym, w sekundach.
    ///
    /// <para>Bez <c>--jitter</c> to po prostu <see cref="StepsPerFrame"/> kroków.
    /// Z <c>--jitter</c> czas klatki jest CELOWO NIERÓWNY — i to jest sedno testu
    /// determinizmu, a nie ozdoba. Akumulator zamienia czas klatki na całkowitą
    /// liczbę kroków 1/120 s i przenosi resztę dalej; jeśli stan po N krokach
    /// zależałby od tego, jak kroki rozłożyły się na klatki, nierówne klatki by to
    /// pokazały. Równe klatki nie pokazałyby niczego, bo przy nich reszta jest
    /// zawsze taka sama.</para>
    ///
    /// <para>Sinus, nie liczba losowa: przebieg ma być powtarzalny co do bajtu.
    /// Mnożnik 1,7 jest niewymierny względem 2π, więc kolejne klatki nie wpadają
    /// w krótki cykl.</para>
    /// </summary>
    /// <param name="stepSeconds">Długość jednego kroku symulacji (1/120 s).</param>
    /// <param name="frameIndex">Numer klatki, od zera.</param>
    public double SyntheticFrameSeconds(double stepSeconds, long frameIndex)
    {
        var baseSeconds = StepsPerFrame * stepSeconds;

        // Granica należy do „bez jittera": zero i wartości ujemne znaczą „nie
        // wstrzykuj". To zapis intencji, nie zabezpieczenie liczbowe — wcześniejsza
        // wersja tego komentarza mówiła, że przejście przez sinus dokładałoby błąd
        // zaokrąglenia, i to jest nieprawda. Zmierzone 03.09.2026 na 483 120
        // wejściach, z czego 480 trafiło dokładnie w `Jitter == 0.0`: `<= 0.0`
        // i `< 0.0` dają wynik identyczny co do bitu, bo `0.0 * sin(x)` to dokładnie
        // zero, a mnożenie przez `1.0` jest tożsamością. Mutant tej granicy przechodzi
        // cały zestaw testów i jest równoważny — świadomie, nie z przeoczenia.
        return Jitter <= 0.0
            ? baseSeconds
            : baseSeconds * (1.0 + (Jitter * Math.Sin(frameIndex * JitterFrequency)));
    }

    /// <summary>Mnożnik fazy jittera. Niewymierny względem 2π, więc klatki nie cyklują.</summary>
    public const double JitterFrequency = 1.7;

    /// <summary>Wartość argumentu albo <c>null</c>, gdy go nie podano.</summary>
    public string? Argument(string name) => Argument(Arguments, name);

    /// <summary>Czy flagę podano — bez względu na jej wartość.</summary>
    public bool HasFlag(string name) => Arguments.ContainsKey(name);

    private static string? Argument(IReadOnlyDictionary<string, string> arguments, string name)
        => arguments.TryGetValue(name, out var value) ? value : null;

    private static RunPlan Refusal(IReadOnlyDictionary<string, string> arguments,
        int code, string message)
        => new(arguments) { ExitCode = code, Error = message };

    private static bool TryLong(IReadOnlyDictionary<string, string> arguments, string name,
        long fallback, out long value, out string? error)
    {
        error = null;
        var text = Argument(arguments, name);
        if (text is null)
        {
            value = fallback;
            return true;
        }

        if (long.TryParse(text, NumberStyles.Integer, CultureInfo.InvariantCulture, out value))
        {
            return true;
        }

        error = $"[ARGUMENT] '--{name}={text}' nie jest liczbą całkowitą";
        return false;
    }

    private static bool TryDouble(IReadOnlyDictionary<string, string> arguments, string name,
        double fallback, out double value, out string? error)
    {
        error = null;
        var text = Argument(arguments, name);
        if (text is null)
        {
            value = fallback;
            return true;
        }

        // `IsFinite` jest tu równie ważne jak `TryParse`. Bez niego `double.Parse`
        // rzucał wyjątkiem w środku `_Ready`, `_shotPath` było już ustawione,
        // a `_Process` wchodziło w odliczanie od int.MaxValue i kręciło się
        // w nieskończoność. Zmierzone: `--at-chainage=abc` nie dawało ani PNG-a,
        // ani kodu błędu — w CI to wypalony `timeout-minutes: 45` bez informacji.
        // `TryParse` przyjmuje też "Infinity" i "NaN", więc sam nie wystarcza.
        if (double.TryParse(text, NumberStyles.Float, CultureInfo.InvariantCulture, out value)
            && double.IsFinite(value))
        {
            return true;
        }

        value = fallback;
        error = $"[ARGUMENT] '--{name}={text}' nie jest skończoną liczbą";
        return false;
    }
}
