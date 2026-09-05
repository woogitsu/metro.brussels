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
        "platforms",
        "line", "calls", "limit-kmh", "signalling",
        "input-log", "replay",
    };

    /// <summary>Widoki, jakie scena potrafi ustawić. Inna wartość jest BŁĘDEM, nie domyślną.</summary>
    public static readonly string[] KnownViews = { "cab", "chase", "outside" };

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
    /// <para><b>Dlaczego domyślna ścieżka, a nie argument.</b> <c>--signalling</c>
    /// znaczy „prowadź linię przez nastawnię i ochronę pociągu" i dlatego łączy się
    /// wyłącznie z <c>--line</c>; tryb ręczny nie rejestruje składu w sygnalizacji
    /// i nie dostaje autorytetu jazdy. Czyta z planu JEDNĄ liczbę — prędkość
    /// dopuszczalną — i mówi o tym wprost wierszem <c>[LIMIT]</c>. Gdy pliku nie ma,
    /// scena ODMAWIA startu; cichy odwrót na 80 km/h byłby powrotem do usterki.</para>
    /// </summary>
    public const string ManualSpeedLimitPlanPath = "data/design/signalling/classic-2026.json";

    /// <summary>Domyślna liczba kroków między próbkami telemetrii.</summary>
    public const long DefaultSampleEvery = 120L;

    /// <summary>Domyślna liczba kroków symulacji na klatkę.</summary>
    public const long DefaultStepsPerFrame = 120L;

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
    /// </summary>
    public bool ScriptedMode => (TelemetryPath is not null && ReplayPath is null) || ShotPath is not null;

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
    /// pochodzi od maszynisty. Warunek musi więc wymienić oba tryby, a nie zaprzeczyć
    /// jednemu.</para>
    ///
    /// <para>Skutek uboczny jest tu skutkiem głównym: w przebiegu skryptowym wiersz
    /// pomocy NIE WYCHODZI na zrzut. Bramka wizualna <c>tools/visual/compare.py</c>
    /// mierzy zawartość klatki z progami zmierzonymi na klatce bez geometrii, czyli na
    /// samym HUD-zie; dopisanie do niej stałego napisu podniosłoby „ink" w klatce,
    /// którą ta bramka ma ODRZUCAĆ.</para>
    /// </summary>
    public bool ReadsKeyboard => !ScriptedMode && !ReplayMode;

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
    /// Przejazd całą linią z zatrzymaniami na stacjach, prowadzony rdzeniem
    /// (<c>LineDrive</c>) — scena jest wtedy WIDOKIEM linii, która jedzie sama.
    ///
    /// To zdanie przewodnie z <c>docs/01-architecture.md</c> wzięte dosłownie:
    /// „Linia jest symulacją, która działa bez gracza. Kabina jest jednym z jej
    /// widoków." Tryb ręczny jest drugim widokiem tej samej linii, z człowiekiem
    /// w miejscu autopilota.
    /// </summary>
    public bool LineMode => HasFlag("line") && TelemetryPath is null;

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
    /// </summary>
    public double LimitKmh { get; private init; }

    /// <summary>
    /// Plan sygnalizacji dla przejazdu linią; <c>null</c> znaczy „bez sygnalizacji".
    ///
    /// <para><b>Jawny argument, a nie ciche wykrywanie.</b> Scena mogłaby próbować
    /// znaleźć plan dla osi sama i po cichu jechać bez sygnalizacji, gdy go nie ma —
    /// i to jest dokładnie ta rodzina usterek, którą to repozytorium zbierało: przebieg
    /// kończy się kodem zero, a nikt nie wie, czy sygnalizacja w nim była. Bez tego
    /// argumentu przejazd jedzie bez blokad i HUD mówi to wprost; z nim prowadzi
    /// <c>LineCore</c>, czyli linia z nastawnią i autorytetem jazdy.</para>
    ///
    /// <para>Plan musi pochodzić z TEJ SAMEJ osi — <c>LineCore</c> odrzuca niezgodną
    /// parę, bo autorytet i cel hamowania liczyłyby się wtedy w dwóch układach.</para>
    /// </summary>
    public string? SignallingPath { get; private init; }

    /// <summary>Nazwa trybu do nagłówka logu i do HUD-a.</summary>
    public string Mode => ReplayPath is not null ? "replay"
        : TelemetryPath is not null ? "telemetry"
        : ShotPath is not null ? "shot"
        : LineMode ? "line" : "manual";

    /// <summary>Co ile kroków zapisać wiersz telemetrii.</summary>
    public long SampleEvery { get; private init; } = DefaultSampleEvery;

    /// <summary>Ile kroków symulacji na jedną klatkę.</summary>
    public long StepsPerFrame { get; private init; } = DefaultStepsPerFrame;

    /// <summary>Nierówność czasów klatek, którą tryb telemetrii wstrzykuje celowo.</summary>
    public double Jitter { get; private init; }

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
        if (arguments.ContainsKey("line") && arguments.ContainsKey("telemetry"))
        {
            return Refusal(arguments, exitBadArgumentValue,
                "[ARGUMENT] --line nie łączy się z --telemetry: to dwa różne źródła "
                + "polecenia dla tego samego składu, a telemetria jest porównywana "
                + "z rdzeniem CO DO BITU, więc pomyłka tutaj wyglądałaby jak rozjazd fizyki");
        }

        // `--replay` jest TRZECIM źródłem polecenia dla tego samego składu, obok
        // klawiatury i autopilota. Ta sama zasada, co przy `--line` z `--telemetry`:
        // dwa źródła naraz nie dają się rozróżnić po wyniku, więc pomyłka wyglądałaby
        // jak rozjazd fizyki. `--shot` nie jest sterownikiem, ale odtworzenie kończy się
        // na ostatnim kroku ZAPISU, a zrzut na zadanym kilometrażu — dwa różne warunki
        // końca tego samego przebiegu, więc też odmowa.
        if (arguments.ContainsKey("replay") && arguments.ContainsKey("line"))
        {
            return Refusal(arguments, exitBadArgumentValue,
                "[ARGUMENT] --replay nie łączy się z --line: zapis wejść i autopilot to dwa "
                + "różne źródła polecenia dla tego samego składu");
        }

        if (arguments.ContainsKey("replay") && arguments.ContainsKey("shot"))
        {
            return Refusal(arguments, exitBadArgumentValue,
                "[ARGUMENT] --replay nie łączy się z --shot: odtworzenie kończy się na ostatnim "
                + "kroku zapisu, a zrzut na zadanym kilometrażu — to dwa warunki końca naraz");
        }

        // Zapisywać można TYLKO to, co naprawdę przyszło od maszynisty. W przebiegu
        // skryptowym i w `--line` polecenie liczy rdzeń, więc plik nazwany „zapisem
        // wejść" opisywałby przejazd, którego nikt nie prowadził — i odtworzony
        // wyglądałby jak dowód determinizmu wejścia gracza, którym by nie był.
        if (arguments.ContainsKey("input-log") && !arguments.ContainsKey("replay")
            && (arguments.ContainsKey("line") || arguments.ContainsKey("shot")
                || arguments.ContainsKey("telemetry")))
        {
            return Refusal(arguments, exitBadArgumentValue,
                "[ARGUMENT] --input-log ma sens tylko w przejeździe prowadzonym z klawiatury "
                + "albo odtwarzanym z --replay: w --line, --shot i --telemetry polecenie "
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

        if (arguments.ContainsKey("signalling") && !arguments.ContainsKey("line"))
        {
            return Refusal(arguments, exitBadArgumentValue,
                "[ARGUMENT] --signalling ma sens tylko z --line: przebieg skryptowy i ręczny "
                + "nie mają składu zarejestrowanego w sygnalizacji");
        }

        if (arguments.ContainsKey("limit-kmh") && !arguments.ContainsKey("line"))
        {
            return Refusal(arguments, exitBadArgumentValue,
                "[ARGUMENT] --limit-kmh ma sens tylko z --line: przebieg skryptowy bierze "
                + "limit ze scenariusza, a ręczny z planu sygnalizacji "
                + ManualSpeedLimitPlanPath);
        }

        if (arguments.ContainsKey("calls") && !arguments.ContainsKey("line"))
        {
            return Refusal(arguments, exitBadArgumentValue,
                "[ARGUMENT] --calls ma sens tylko z --line: bez przejazdu linią nie ma "
                + "zatrzymań do wypisania");
        }

        return new RunPlan(arguments)
        {
            TelemetryPath = Argument(arguments, "telemetry"),
            ShotPath = Argument(arguments, "shot"),
            CallsPath = Argument(arguments, "calls"),
            InputLogPath = Argument(arguments, "input-log"),
            ReplayPath = Argument(arguments, "replay"),
            LimitKmh = limitKmh,
            SignallingPath = Argument(arguments, "signalling"),
            SampleEvery = sampleEvery,
            StepsPerFrame = stepsPerFrame,
            Jitter = jitter,
            ShotChainageM = chainage,
            View = view switch
            {
                "chase" => ViewKind.Chase,
                "outside" => ViewKind.Outside,
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
