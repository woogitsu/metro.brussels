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
    };

    /// <summary>Widoki, jakie scena potrafi ustawić. Inna wartość jest BŁĘDEM, nie domyślną.</summary>
    public static readonly string[] KnownViews = { "cab", "chase", "outside" };

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

    /// <summary>Przebieg bez interakcji: telemetria albo zrzut.</summary>
    public bool ScriptedMode => TelemetryPath is not null || ShotPath is not null;

    /// <summary>Nazwa trybu do nagłówka logu: <c>telemetry</c>, <c>shot</c> albo <c>manual</c>.</summary>
    public string Mode => TelemetryPath is not null ? "telemetry"
        : ShotPath is not null ? "shot" : "manual";

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

        return new RunPlan(arguments)
        {
            TelemetryPath = Argument(arguments, "telemetry"),
            ShotPath = Argument(arguments, "shot"),
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
