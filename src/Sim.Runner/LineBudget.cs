using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Globalization;
using MetroBxl.Sim.Line;
using MetroBxl.Sim.Physics;
using MetroBxl.Sim.Signalling;
using MetroBxl.Sim.Train;

namespace MetroBxl.Sim.Runner;

/// <summary>
/// Spis tego, co w oknie pomiarowym naprawdę jeździło. Powstaje w przebiegu
/// <b>osobnym od mierzonego</b> i to jest jego cały sens: liczenie składów na planie
/// w każdym kroku samo kosztuje O(N) na krok, więc doliczyłoby się do wyniku, który ma
/// mierzyć koszt rdzenia, a nie koszt licznika.
/// </summary>
public sealed class LineBudgetCensus
{
    internal LineBudgetCensus(
        int declared, int maxOnLine, double meanOnLine, int onLineAtEnd,
        int maxWaiting, double meanWaiting, string digest)
    {
        Declared = declared;
        MaxOnLine = maxOnLine;
        MeanOnLine = meanOnLine;
        OnLineAtEnd = onLineAtEnd;
        MaxWaiting = maxWaiting;
        MeanWaiting = meanWaiting;
        Digest = digest;
    }

    /// <summary>Ile składów zgłoszono do linii.</summary>
    public int Declared { get; }

    /// <summary>
    /// Najwięcej składów naraz na planie w oknie. Jest to liczba <b>fizyczna</b>:
    /// oś mieści tyle składów, ile pozwolą bloki i ryglowanie tras, a nie tyle,
    /// ile ich zgłoszono.
    /// </summary>
    public int MaxOnLine { get; }

    /// <summary>
    /// Średnia liczba składów na planie na krok okna. To ona, a nie
    /// <see cref="MaxOnLine"/>, odpowiada kosztowi kroku: przez większość okna na osi
    /// jest tylu składów, ilu tu stoi, a szczyt trwa tyle, ile trwa.
    /// </summary>
    public double MeanOnLine { get; }

    /// <summary>Składy na planie w ostatnim kroku okna.</summary>
    public int OnLineAtEnd { get; }

    /// <summary>
    /// Najwięcej składów naraz czekających na wjazd (zgłoszonych, po kroku wyjazdu,
    /// a wciąż poza planem). Czekający skład też kosztuje: faza wyjazdów sprawdza dla
    /// niego zajętość peronu początkowego.
    /// </summary>
    public int MaxWaiting { get; }

    /// <summary>Średnia liczba składów czekających na wjazd na krok okna.</summary>
    public double MeanWaiting { get; }

    /// <summary>Odcisk stanu sygnalizacji po ostatnim kroku okna.</summary>
    public string Digest { get; }
}

/// <summary>Jedno powtórzenie pomiaru: ile kroków, w jakim czasie, z jakim odciskiem.</summary>
public sealed class LineBudgetRun
{
    /// <summary>
    /// Wynik jednego okna. Konstruktor jest publiczny, bo mediana i rozstęp liczą się
    /// z listy takich wyników i muszą dać się sprawdzić na liczbach podanych z ręki —
    /// test, który sam mierzy czas, żeby sprawdzić liczenie mediany, mierzyłby maszynę.
    /// </summary>
    /// <param name="steps">Liczba wykonanych kroków; musi być dodatnia.</param>
    /// <param name="wallSeconds">Czas ścienny okna; musi być dodatni, bo dzieli.</param>
    /// <param name="cpuSeconds">Czas procesora zużyty w oknie; nieujemny.</param>
    /// <param name="digest">Odcisk stanu sygnalizacji po oknie.</param>
    public LineBudgetRun(long steps, double wallSeconds, double cpuSeconds, string digest)
    {
        ArgumentNullException.ThrowIfNull(digest);
        if (steps < 1L)
        {
            throw new ArgumentOutOfRangeException(nameof(steps), steps, "Okno bez kroków nie jest pomiarem.");
        }

        if (!double.IsFinite(wallSeconds) || wallSeconds <= 0.0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(wallSeconds), wallSeconds,
                "Czas okna musi być dodatni i skończony; z zera wyszłyby nieskończone kroki na sekundę.");
        }

        if (!double.IsFinite(cpuSeconds) || cpuSeconds < 0.0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(cpuSeconds), cpuSeconds, "Czas procesora musi być nieujemny i skończony.");
        }

        Steps = steps;
        WallSeconds = wallSeconds;
        CpuSeconds = cpuSeconds;
        Digest = digest;
    }

    /// <summary>Liczba wykonanych kroków zegara linii.</summary>
    public long Steps { get; }

    /// <summary>Czas ścienny okna, w sekundach.</summary>
    public double WallSeconds { get; }

    /// <summary>Czas procesora zużyty przez proces w oknie, w sekundach.</summary>
    public double CpuSeconds { get; }

    /// <summary>Odcisk stanu sygnalizacji po ostatnim kroku okna.</summary>
    public string Digest { get; }

    /// <summary>Kroki na sekundę czasu ściennego.</summary>
    public double StepsPerSecond => Steps / WallSeconds;

    /// <summary>Średni czas jednego kroku w mikrosekundach.</summary>
    public double MicrosecondsPerStep => WallSeconds * 1e6 / Steps;
}

/// <summary>
/// Pomiar kosztu kroku <see cref="LineCore"/> przy N składach na osi.
///
/// <para><b>Dlaczego to nie jest jedno wywołanie ze stoperem.</b> Rdzeń liczy się
/// z JIT-em: pierwsze przejście przez <c>LineCore.Step</c> obejmuje kompilację metod
/// i jest wolniejsze o rzędy wielkości od ustalonego. Dlatego pomiar składa się
/// z rozgrzewki, którą się odrzuca, i z powtórzeń, z których bierze się <b>medianę
/// i rozstęp</b> — na maszynie dzielonej z innymi procesami pojedynczy przebieg mierzy
/// tyle samo cudzego obciążenia, co własnego kodu.</para>
///
/// <para><b>Każde powtórzenie buduje linię od nowa.</b> Inaczej drugie powtórzenie
/// mierzyłoby inną pracę niż pierwsze: składy zdążyłyby dojechać, a pusty plan liczy się
/// szybciej niż pełny. Że praca jest ta sama, nie jest tu założeniem — sprawdza to
/// porównanie <see cref="LineBudgetRun.Digest"/> między powtórzeniami.</para>
/// </summary>
public static class LineBudget
{
    /// <summary>
    /// Buduje linię z zadanymi składami i krokuje ją zadaną liczbę kroków, licząc po
    /// drodze, ile składów było na planie. Przebieg <b>nie jest mierzony</b>.
    /// </summary>
    /// <param name="scenario">Opis linii i rozkładu wyjazdów.</param>
    /// <param name="steps">Długość okna w krokach zegara linii.</param>
    /// <returns>Spis obsady linii w oknie.</returns>
    public static LineBudgetCensus Census(LineBudgetScenario scenario, long steps)
    {
        ArgumentNullException.ThrowIfNull(scenario);
        RequireSteps(steps);

        var core = scenario.Build();
        var maxOnLine = 0;
        var maxWaiting = 0;
        var onLineAtEnd = 0;
        var onLineTotal = 0L;
        var waitingTotal = 0L;
        for (var i = 0L; i < steps; i++)
        {
            core.Step();
            var onLine = 0;
            var waiting = 0;
            foreach (var train in core.Trains)
            {
                if (train.OnLine)
                {
                    onLine++;
                }
                else if (train.ReleaseStep < core.Steps)
                {
                    waiting++;
                }
            }

            onLineAtEnd = onLine;
            onLineTotal += onLine;
            waitingTotal += waiting;
            maxOnLine = Math.Max(maxOnLine, onLine);
            maxWaiting = Math.Max(maxWaiting, waiting);
        }

        return new LineBudgetCensus(
            scenario.Trains,
            maxOnLine,
            (double)onLineTotal / steps,
            onLineAtEnd,
            maxWaiting,
            (double)waitingTotal / steps,
            core.Signalling.StateDigest());
    }

    /// <summary>
    /// Jedno mierzone okno: świeża linia, zadana liczba kroków, stoper wokół samej
    /// pętli. W pętli nie ma ani śladu, ani licznika, ani wypisywania — wszystko, co
    /// mierzalne, jest w niej kosztem rdzenia.
    /// </summary>
    /// <param name="scenario">Opis linii i rozkładu wyjazdów.</param>
    /// <param name="steps">Długość okna w krokach zegara linii.</param>
    /// <returns>Czas ścienny, czas procesora i odcisk stanu po oknie.</returns>
    public static LineBudgetRun Measure(LineBudgetScenario scenario, long steps)
    {
        ArgumentNullException.ThrowIfNull(scenario);
        RequireSteps(steps);

        var core = scenario.Build();
        var process = Process.GetCurrentProcess();
        var cpuBefore = process.TotalProcessorTime;
        var stopwatch = Stopwatch.StartNew();
        for (var i = 0L; i < steps; i++)
        {
            core.Step();
        }

        stopwatch.Stop();
        var cpuAfter = Process.GetCurrentProcess().TotalProcessorTime;

        if (core.Steps != steps)
        {
            throw new InvalidOperationException(
                $"okno miało {steps} kroków, a zegar linii stanął na {core.Steps} — "
                + "pomiar podałby kroki na sekundę z innej liczby kroków, niż zmierzono");
        }

        return new LineBudgetRun(
            steps,
            stopwatch.Elapsed.TotalSeconds,
            (cpuAfter - cpuBefore).TotalSeconds,
            core.Signalling.StateDigest());
    }

    /// <summary>
    /// Pełny pomiar dla listy scenariuszy, <b>na przemian</b>: najpierw okna
    /// rozgrzewkowe, potem rundy, a w każdej rundzie po jednym oknie na scenariusz.
    ///
    /// <para><b>Przeplot jest tu treścią, nie porządkiem wykonania.</b> Zmierzone
    /// 05.09.2026 na tej maszynie: przy pomiarze „wszystkie powtórzenia dla N=1, potem
    /// wszystkie dla N=2..." pierwsze N w kolejności wychodziło <b>pięć razy wolniejsze</b>
    /// od ostatniego, i odwracało się razem z kolejnością argumentów — 229 tys. kroków/s
    /// dla N=1 przy <c>--trains 1,2,4</c> wobec 1064 tys. kroków/s dla tego samego N=1
    /// przy <c>--trains 4,2,1</c>. To nie był koszt składów, tylko kompilacja warstwowa
    /// i cudze procesy na wspólnych rdzeniach. Przeplot rozkłada jedno i drugie na
    /// wszystkie N po równo, zamiast wpisywać je w pierwszą zmierzoną pozycję.</para>
    ///
    /// <para>Powtórzenie, którego odcisk stanu nie zgadza się ze spisem, jest
    /// <b>odmową</b>, a nie ostrzeżeniem: znaczyłoby, że dwa przebiegi tego samego
    /// scenariusza policzyły dwie różne rzeczy i mediana z ich czasów nie mierzy
    /// niczego.</para>
    /// </summary>
    /// <param name="scenarios">Scenariusze, po jednym na N; kolejność jest kolejnością w rundzie.</param>
    /// <param name="steps">Długość okna w krokach zegara linii.</param>
    /// <param name="warmup">Ile rund odrzucić na rozgrzewkę; zero jest dozwolone.</param>
    /// <param name="repeats">Ile rund policzyć do mediany; musi być dodatnie.</param>
    /// <returns>Spis i powtórzenia dla każdego scenariusza, w kolejności wejściowej.</returns>
    public static IReadOnlyList<(LineBudgetCensus Census, IReadOnlyList<LineBudgetRun> Runs)> Sweep(
        IReadOnlyList<LineBudgetScenario> scenarios, long steps, int warmup, int repeats)
    {
        ArgumentNullException.ThrowIfNull(scenarios);
        RequireSteps(steps);
        if (scenarios.Count == 0)
        {
            throw new ArgumentException("Pomiar bez ani jednego scenariusza nic nie mierzy.", nameof(scenarios));
        }

        if (warmup < 0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(warmup), warmup, "Liczba rund rozgrzewkowych nie może być ujemna.");
        }

        if (repeats < 1)
        {
            throw new ArgumentOutOfRangeException(
                nameof(repeats), repeats, "Mediana z zera powtórzeń nie istnieje.");
        }

        var census = new LineBudgetCensus[scenarios.Count];
        var runs = new List<LineBudgetRun>[scenarios.Count];
        for (var i = 0; i < scenarios.Count; i++)
        {
            census[i] = Census(scenarios[i], steps);
            runs[i] = new List<LineBudgetRun>(repeats);
        }

        for (var round = 0; round < warmup; round++)
        {
            for (var i = 0; i < scenarios.Count; i++)
            {
                _ = Measure(scenarios[i], steps);
            }
        }

        for (var round = 0; round < repeats; round++)
        {
            for (var i = 0; i < scenarios.Count; i++)
            {
                var run = Measure(scenarios[i], steps);
                if (!string.Equals(run.Digest, census[i].Digest, StringComparison.Ordinal))
                {
                    throw new InvalidOperationException(
                        $"runda {round + 1}, N={scenarios[i].Trains}: przebieg skończył się w innym "
                        + "stanie sygnalizacji niż spis — przebiegi nie policzyły tej samej pracy, "
                        + "więc mediana z ich czasów nie jest kosztem kroku");
                }

                runs[i].Add(run);
            }
        }

        var result = new (LineBudgetCensus Census, IReadOnlyList<LineBudgetRun> Runs)[scenarios.Count];
        for (var i = 0; i < scenarios.Count; i++)
        {
            result[i] = (census[i], runs[i]);
        }

        return result;
    }

    /// <summary>Mediana kroków na sekundę z powtórzeń; dla parzystej liczby — średnia dwóch środkowych.</summary>
    /// <param name="runs">Powtórzenia pomiaru.</param>
    /// <returns>Mediana kroków na sekundę.</returns>
    public static double MedianStepsPerSecond(IReadOnlyList<LineBudgetRun> runs)
    {
        ArgumentNullException.ThrowIfNull(runs);
        if (runs.Count == 0)
        {
            throw new ArgumentException("Mediana z pustej listy nie istnieje.", nameof(runs));
        }

        var values = new double[runs.Count];
        for (var i = 0; i < runs.Count; i++)
        {
            values[i] = runs[i].StepsPerSecond;
        }

        Array.Sort(values);
        var middle = values.Length / 2;
        return values.Length % 2 == 1
            ? values[middle]
            : 0.5 * (values[middle - 1] + values[middle]);
    }

    private static void RequireSteps(long steps)
    {
        if (steps < 1L)
        {
            throw new ArgumentOutOfRangeException(
                nameof(steps), steps, "Okno pomiarowe musi mieć co najmniej jeden krok.");
        }
    }
}

/// <summary>
/// Scenariusz pomiaru: linia i rozkład wyjazdów. Istnieje jako osobny obiekt, bo
/// pomiar buduje linię <b>wielokrotnie</b> — raz na każde okno — i każde zbudowanie musi
/// dać dokładnie tę samą linię.
/// </summary>
public sealed class LineBudgetScenario
{
    private readonly SignallingPlan _plan;
    private readonly TrackAxis _axis;
    private readonly RunConditions _conditions;
    private readonly LineRunSettings _settings;
    private readonly double _turnbackSeconds;
    private readonly bool _atp;
    private readonly long _headwaySteps;

    /// <summary>Scenariusz z gotowych składników.</summary>
    /// <param name="plan">Plan bloków dla tej samej osi.</param>
    /// <param name="axis">Oś z kilometrażem stacji.</param>
    /// <param name="conditions">Masa, pochylenie, przyczepność, otoczenie toru.</param>
    /// <param name="settings">Założenia przejazdu.</param>
    /// <param name="trains">Liczba zgłoszonych składów; musi być dodatnia.</param>
    /// <param name="headwaySeconds">
    /// Odstęp między kolejnymi wyjazdami. Zero znaczy „wszystkie zgłoszone na krok 0"
    /// i jest dozwolone: wtedy o wjeździe decyduje wyłącznie zajętość peronu.
    /// Odstęp krótszy niż krok symulacji jest odmową, bo zaokrągliłby się do zera
    /// i po cichu zamienił rozkład na zerowy.
    /// </param>
    /// <param name="turnbackSeconds">Czas nawrotu; zero wyłącza nawrót.</param>
    /// <param name="atp">Czy linia ma ochronę pociągu.</param>
    public LineBudgetScenario(
        SignallingPlan plan,
        TrackAxis axis,
        RunConditions conditions,
        LineRunSettings settings,
        int trains,
        double headwaySeconds,
        double turnbackSeconds,
        bool atp)
    {
        ArgumentNullException.ThrowIfNull(plan);
        ArgumentNullException.ThrowIfNull(axis);
        ArgumentNullException.ThrowIfNull(conditions);
        ArgumentNullException.ThrowIfNull(settings);
        if (trains < 1)
        {
            throw new ArgumentOutOfRangeException(
                nameof(trains), trains, "Linia bez ani jednego składu nie mierzy kosztu składu.");
        }

        if (!double.IsFinite(headwaySeconds) || headwaySeconds < 0.0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(headwaySeconds), headwaySeconds, "Odstęp musi być nieujemny i skończony.");
        }

        var step = FixedStep.Simulation;
        _headwaySteps = headwaySeconds > 0.0 ? (long)Math.Round(headwaySeconds / step.Seconds) : 0L;
        if (headwaySeconds > 0.0 && _headwaySteps <= 0L)
        {
            throw new ArgumentOutOfRangeException(
                nameof(headwaySeconds), headwaySeconds,
                "Odstęp krótszy niż jeden krok symulacji zaokrągliłby się do zera, "
                + "czyli po cichu zamieniłby rozkład na wyjazd wszystkich naraz.");
        }

        _plan = plan;
        _axis = axis;
        _conditions = conditions;
        _settings = settings;
        Trains = trains;
        HeadwaySeconds = headwaySeconds;
        _turnbackSeconds = turnbackSeconds;
        _atp = atp;
    }

    /// <summary>Liczba zgłoszonych składów.</summary>
    public int Trains { get; }

    /// <summary>Odstęp między wyjazdami w sekundach.</summary>
    public double HeadwaySeconds { get; }

    /// <summary>Odstęp między wyjazdami w krokach zegara linii.</summary>
    public long HeadwaySteps => _headwaySteps;

    /// <summary>
    /// Buduje linię i zgłasza do niej wszystkie składy. Identyfikatory są numerowane
    /// z wiodącymi zerami, żeby porządek napisowy zgadzał się z porządkiem wyjazdów —
    /// odcisk stanu sygnalizacji sortuje po identyfikatorze.
    /// </summary>
    /// <returns>Linia na kroku zero, z kompletem zgłoszonych składów.</returns>
    public LineCore Build()
    {
        var core = LineCore.M7(_plan, _axis, _conditions, _settings, _turnbackSeconds, _atp);
        for (var i = 0; i < Trains; i++)
        {
            core.Add(
                string.Create(CultureInfo.InvariantCulture, $"T{i:D4}"),
                i * _headwaySteps);
        }

        return core;
    }
}
