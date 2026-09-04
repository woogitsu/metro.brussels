using System;
using System.Collections.Generic;
using System.Globalization;
using MetroBxl.Sim.Physics;
using MetroBxl.Sim.Signalling;
using MetroBxl.Sim.Train;

namespace MetroBxl.Sim.Line;

/// <summary>
/// Skład widziany przez linię: prowadzenie z <see cref="LineDrive"/> plus to, czego
/// prowadzenie o sobie nie wie — kiedy miał wyjechać, kiedy faktycznie wjechał na plan
/// i jaki autorytet dostał w ostatnim kroku.
/// </summary>
public sealed class LineTrain
{
    internal LineTrain(string id, long releaseStep)
    {
        Id = id;
        ReleaseStep = releaseStep;
    }

    /// <summary>Identyfikator składu; ten sam w sygnalizacji i w raporcie.</summary>
    public string Id { get; }

    /// <summary>Krok zegara linii, na którym skład ma wyjechać z pierwszej stacji.</summary>
    public long ReleaseStep { get; }

    /// <summary>
    /// Krok zegara linii, na którym skład faktycznie wszedł na plan; <c>null</c>, dopóki
    /// czeka. Różnica wobec <see cref="ReleaseStep"/> to czas, o który peron początkowy
    /// był zajęty — nie jest to regulacja ruchu, tylko brak miejsca.
    /// </summary>
    public long? EnteredAtStep { get; internal set; }

    /// <summary>Prowadzenie; <c>null</c>, dopóki skład nie wszedł na plan.</summary>
    public LineDrive? Drive { get; internal set; }

    /// <summary>Autorytet z ostatniego kroku; <c>null</c>, dopóki skład nie wszedł na plan.</summary>
    public MovementAuthority? Authority { get; internal set; }

    /// <summary>
    /// Zakończone przejazdy tego pojazdu, w kolejności. Bez turnbacku ma zawsze zero
    /// albo jeden wpis; z turnbackiem rośnie z każdym obiegiem.
    /// </summary>
    public IReadOnlyList<LineRunResult> CompletedRuns => _completed;

    internal readonly List<LineRunResult> _completed = new();

    /// <summary>
    /// Krok, na którym prowadzenie zgłosiło koniec przejazdu; <c>null</c>, gdy jeszcze
    /// jedzie. Od niego liczy się czas nawrotu.
    /// </summary>
    internal long? FinishedAtStep { get; set; }

    /// <summary>Prawda, gdy skład jest na planie.</summary>
    public bool OnLine => Drive is not null;

    /// <summary>Prawda, gdy skład dojechał do ostatniej stacji osi.</summary>
    public bool Finished => Drive is { Finished: true };

    /// <inheritdoc/>
    public override string ToString() => Drive is null
        ? string.Create(CultureInfo.InvariantCulture, $"{Id}: czeka na wyjazd od kroku {ReleaseStep}")
        : string.Create(
            CultureInfo.InvariantCulture,
            $"{Id}: {Drive.ChainageM:F2} m, {Drive.State.SpeedMps:F2} m/s, " +
            $"authority {Authority?.EndChainageM ?? double.NaN:F2} m ({Authority?.Reason})");
}

/// <summary>
/// Linia jako całość: N składów na **jednym** zegarze, jednej osi i jednym planie
/// sygnalizacji.
///
/// <para><b>Zasada z <c>CLAUDE.md</c>, dosłownie.</b> „Linia jest symulacją, która działa
/// bez gracza." Ta klasa jest tą symulacją. Nie ma w niej kabiny, nie ma gracza i nie ma
/// Godota; jest zegar i tyle składów, ile wołający zgłosił. <see cref="LineRun"/> jest po
/// tej zmianie szczególnym przypadkiem — jeden skład, brak sygnalizacji — a nie osobnym
/// modelem.</para>
///
/// <para><b>Kolejność w kroku jest częścią modelu, nie szczegółem.</b> Krok idzie w trzech
/// fazach nad **wszystkimi** składami, a nie skład po składzie:</para>
/// <list type="number">
/// <item>wyjazdy: składy, których krok wyjazdu nadszedł, wchodzą na plan, o ile peron
///   początkowy jest wolny;</item>
/// <item>odczyt: każdy skład dostaje autorytet policzony ze stanu **sprzed** kroku;</item>
/// <item>jazda i ruch: każdy skład robi swój krok, po czym melduje nowe czoło.</item>
/// </list>
///
/// <para>Rozdzielenie odczytu od ruchu jest jedynym powodem, dla którego wynik nie zależy
/// od tego, w jakiej kolejności składy zostały zgłoszone. Gdyby skład B pytał o autorytet
/// po tym, jak skład A już się przesunął, ten sam scenariusz dałby dwa różne przejazdy
/// zależnie od kolejności w liście — a to jest dokładnie ten rodzaj niedeterminizmu, przed
/// którym broni się <c>docs/01-architecture.md</c>.</para>
///
/// <para><b>Gdzie „jednocześnie" i tak przecieka.</b> Faza trzecia melduje ruch składami
/// po kolei, bo <see cref="FixedBlockSystem.MoveTrain"/> uzgadnia zajętość od razu. Dopóki
/// składy respektują autorytet, nie ma to znaczenia: żaden nie sięga bloku, który w tym
/// samym kroku zwalnia inny. Dopiero **naruszenie** autorytetu robi wynik zależnym od
/// kolejności — i wtedy zależność jest sygnałem, że coś jest nie tak, a nie usterką
/// tej pętli. Pilnuje tego test odwróconej kolejności.</para>
///
/// <para><b>Czego tu nie ma i dlaczego.</b> Nie ma zawracania na krańcówce, nie ma
/// regulacji ruchu i nie ma zaburzeń — skład, który dojechał do ostatniej stacji, zostaje
/// na peronie i zajmuje go dalej, bo fizycznie tam stoi. To nie jest przeoczenie: turnback,
/// polityka dyspozytora i model zaburzeń są w <c>docs/TASKS.md</c> (T-320, sekcja STOP)
/// wymienione jako decyzje właściciela. Na krótkiej osi i krótkim odstępie linia dojdzie
/// więc do zakleszczenia — drugi skład stanie przed zajętym peronem końcowym i tam
/// zostanie. Jest to poprawne zachowanie modelu, który nie zna zawracania, i tak jest
/// przypięte testem.</para>
/// </summary>
public sealed class LineCore
{
    private readonly FixedBlockSystem _signalling;
    private readonly RouteDispatcher _dispatcher;
    private readonly long _turnbackSteps;
    private readonly TrackAxis _axis;
    private readonly RunConditions _conditions;
    private readonly LineRunSettings _settings;
    private readonly TrainController _controller;
    private readonly BrakingPointSolver _solver;
    private readonly FixedStep _step;
    private readonly double _trainLengthM;
    private readonly double _entryChainageM;
    private readonly List<LineTrain> _trains = new();

    /// <summary>Linia zbudowana ze złożonych osobno składników.</summary>
    /// <param name="plan">Plan bloków dla tej samej osi.</param>
    /// <param name="axis">Oś z kilometrażem stacji.</param>
    /// <param name="conditions">Masa, pochylenie, przyczepność, otoczenie toru.</param>
    /// <param name="settings">Założenia przejazdu — wszystkie bez źródła.</param>
    /// <param name="controller">Kontroler z T-310.</param>
    /// <param name="solver">Solver punktu hamowania z T-311.</param>
    /// <param name="step">Krok stały; ten sam dla całej linii.</param>
    /// <param name="trainLengthM">Długość składu; z rejestru pojazdu, nie z powietrza.</param>
    public LineCore(
        SignallingPlan plan,
        TrackAxis axis,
        RunConditions conditions,
        LineRunSettings settings,
        TrainController controller,
        BrakingPointSolver solver,
        FixedStep step,
        double trainLengthM)
        : this(plan, axis, conditions, settings, controller, solver, step, trainLengthM, 0.0)
    {
    }

    /// <summary>
    /// Linia z TURNBACKIEM: pojazd, który dojechał do ostatniego peronu, po zadanym
    /// czasie wypisuje się z planu i wjeżdża znowu na pierwszym.
    ///
    /// <para><b>Czas nawrotu ma źródło i to jest jego cała treść.</b> Zmierzony
    /// 04.09.2026 z feedu GTFS STIB (`data/network/gtfs-manifest.json`, suma
    /// <c>content_sha256</c> zgodna), przez połączenie kursów po <c>block_id</c> na
    /// liniach 1 i 5: <b>194 obiegi, 4289 nawrotów, minimum 240 s</b>, p05 259 s,
    /// mediana 445 s, p95 841 s, maksimum 1005 s, <b>ani jednego poniżej 240 s</b>.
    /// Luka między kursami zawiera też postój wyrównawczy, więc 240 s jest
    /// ograniczeniem NA ROZKŁAD, nie technicznym minimum nawrotu — i tak trzeba o niej
    /// mówić.</para>
    ///
    /// <para><b>Czego ten model NIE robi.</b> Nie zawraca składu na osi. Oś pakietu
    /// biegnie w jednym kierunku, a przeciwny to osobna oś (pakiet A ma parę w B), więc
    /// „nawrót" znaczy tu: pojazd znika z tego planu i wraca na jego początek jako
    /// następny obieg. Nawrót na MERODE jest przy tym <c>design_assumption</c>, a nie
    /// faktem o ruchu STIB: w GTFS krańcówkami linii 1 są Gare de l'Ouest i Stockel,
    /// a Merode to granica pakietu. Nawrót na Gare de l'Ouest ma pokrycie w danych
    /// (1126 nawrotów, minimum 377 s); nawrót na Merode wynika z cięcia sieci na
    /// pakiety i z decyzji właściciela z 04.09.2026.</para>
    /// </summary>
    /// <param name="turnbackSeconds">
    /// Czas nawrotu w sekundach. <b>Zero wyłącza turnback</b> i wtedy linia zachowuje
    /// się dokładnie tak, jak przed tą zmianą: pojazd kończy na ostatnim peronie i tam
    /// zostaje. Wartość ujemna jest odmową, nie wyłączeniem.
    /// </param>
    public LineCore(
        SignallingPlan plan,
        TrackAxis axis,
        RunConditions conditions,
        LineRunSettings settings,
        TrainController controller,
        BrakingPointSolver solver,
        FixedStep step,
        double trainLengthM,
        double turnbackSeconds)
    {
        ArgumentNullException.ThrowIfNull(plan);
        ArgumentNullException.ThrowIfNull(axis);
        ArgumentNullException.ThrowIfNull(conditions);
        ArgumentNullException.ThrowIfNull(settings);
        ArgumentNullException.ThrowIfNull(controller);
        ArgumentNullException.ThrowIfNull(solver);
        step.RequireValid();

        if (!string.Equals(plan.AxisId, axis.Id, StringComparison.Ordinal))
        {
            throw new ArgumentException(
                $"plan jest dla osi {plan.AxisId}, a linia jedzie po {axis.Id} — " +
                "kilometraż bloków i kilometraż stacji muszą pochodzić z tej samej osi",
                nameof(plan));
        }

        if (axis.Stations.Count < 2)
        {
            throw new ArgumentOutOfRangeException(
                nameof(axis), axis.Stations.Count, "Linia wymaga co najmniej dwóch stacji na osi.");
        }

        if (!double.IsFinite(trainLengthM) || trainLengthM <= 0.0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(trainLengthM), trainLengthM, "Długość składu musi być dodatnia i skończona.");
        }

        _signalling = new FixedBlockSystem(plan);
        _dispatcher = new RouteDispatcher(plan);
        _axis = axis;
        _conditions = conditions;
        _settings = settings;
        _controller = controller;
        _solver = solver;
        _step = step;
        _trainLengthM = trainLengthM;
        _entryChainageM = axis.Stations[0].ChainageM;

        if (!double.IsFinite(turnbackSeconds) || turnbackSeconds < 0.0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(turnbackSeconds), turnbackSeconds,
                "Czas nawrotu musi być nieujemny i skończony; zero wyłącza turnback.");
        }

        _turnbackSteps = turnbackSeconds > 0.0
            ? (long)Math.Round(turnbackSeconds / step.Seconds)
            : 0L;
        if (turnbackSeconds > 0.0 && _turnbackSteps <= 0L)
        {
            throw new ArgumentOutOfRangeException(
                nameof(turnbackSeconds), turnbackSeconds,
                "Czas nawrotu krótszy niż jeden krok symulacji zaokrągliłby się do zera, "
                + "czyli po cichu wyłączyłby turnback.");
        }
    }

    /// <summary>Linia M7 z planem dla podanej osi.</summary>
    /// <param name="plan">Plan bloków.</param>
    /// <param name="axis">Oś.</param>
    /// <param name="conditions">Warunki przejazdu.</param>
    /// <param name="settings">Założenia przejazdu.</param>
    public static LineCore M7(
        SignallingPlan plan, TrackAxis axis, RunConditions conditions, LineRunSettings settings) =>
        M7(plan, axis, conditions, settings, turnbackSeconds: 0.0);

    /// <summary>Linia M7 z turnbackiem; zero sekund wyłącza nawrót.</summary>
    public static LineCore M7(
        SignallingPlan plan, TrackAxis axis, RunConditions conditions,
        LineRunSettings settings, double turnbackSeconds) =>
        new(plan, axis, conditions, settings,
            new TrainController(VehicleModel.M7),
            new BrakingPointSolver(VehicleModel.M7),
            FixedStep.Simulation,
            VehicleRegistry.M7.RequireValue("parameters.length_m", ParameterStatus.Spec),
            turnbackSeconds);

    /// <summary>Sygnalizacja linii — do odczytu zajętości, zdarzeń i odcisku stanu.</summary>
    public FixedBlockSystem Signalling => _signalling;

    /// <summary>
    /// Nastawnia automatyczna tej linii — do odczytu licznika zaryglowanych tras i odmów.
    ///
    /// Odmowa NIE jest usterką: blok przed nosem bywa zajęty i wtedy sygnał ma stać na
    /// stój. Licznik jest tu, żeby dało się to zmierzyć, a nie żeby świecił na zielono.
    /// </summary>
    public RouteDispatcher Dispatcher => _dispatcher;

    /// <summary>Liczba wykonanych kroków zegara linii.</summary>
    public long Steps { get; private set; }

    /// <summary>Czas linii; funkcja liczby kroków, nigdy suma.</summary>
    public double TimeSeconds => _step.TimeAt(Steps);

    /// <summary>Składy w kolejności zgłoszenia.</summary>
    public IReadOnlyList<LineTrain> Trains => _trains;

    /// <summary>
    /// Prawda, gdy każdy zgłoszony skład wszedł na plan i dojechał do ostatniej stacji.
    /// Na krótkiej osi z krótkim odstępem nie nastąpi to nigdy — patrz akapit o turnbacku
    /// w opisie klasy.
    /// </summary>
    /// <summary>Czy ta linia ma włączony turnback (pojazdy krążą i nigdy nie kończą).</summary>
    public bool TurnbackEnabled => _turnbackSteps > 0L;

    /// <summary>Czas nawrotu w krokach; zero, gdy turnback wyłączony.</summary>
    public long TurnbackSteps => _turnbackSteps;

    public bool Finished
    {
        get
        {
            foreach (var train in _trains)
            {
                if (!train.Finished)
                {
                    return false;
                }
            }

            return _trains.Count > 0;
        }
    }

    /// <summary>
    /// Zgłasza skład do wyjazdu z pierwszej stacji osi na zadanym kroku zegara linii.
    /// </summary>
    /// <param name="trainId">Identyfikator; musi być nowy.</param>
    /// <param name="releaseStep">Krok wyjazdu; nie może leżeć w przeszłości linii.</param>
    /// <returns>Zgłoszony skład.</returns>
    public LineTrain Add(string trainId, long releaseStep)
    {
        ArgumentNullException.ThrowIfNull(trainId);
        if (releaseStep < Steps)
        {
            throw new ArgumentOutOfRangeException(
                nameof(releaseStep), releaseStep,
                $"zegar linii jest już na kroku {Steps} — wyjazd w przeszłości byłby " +
                "cichym przesunięciem rozkładu, a nie wyjazdem");
        }

        foreach (var existing in _trains)
        {
            if (string.Equals(existing.Id, trainId, StringComparison.Ordinal))
            {
                throw new ArgumentException($"skład {trainId} jest już na linii", nameof(trainId));
            }
        }

        var train = new LineTrain(trainId, releaseStep);
        _trains.Add(train);
        return train;
    }

    /// <summary>
    /// Jeden krok zegara linii nad wszystkimi składami. Fazy w kolejności opisanej
    /// przy klasie: wyjazdy, odczyt autorytetów, jazda i meldunek ruchu.
    /// </summary>
    /// <param name="trace">Ślad wołany po kroku każdego składu, gdy podany.</param>
    public void Step(Action<string, LineRun.TracePoint>? trace = null)
    {
        // 1. wyjazdy
        foreach (var train in _trains)
        {
            if (train.Drive is not null || train.ReleaseStep > Steps || !EntryIsClear())
            {
                continue;
            }

            train.Drive = new LineDrive(_axis, _conditions, _settings, _controller, _solver, _step);
            train.EnteredAtStep = Steps;
            _signalling.RegisterTrain(train.Id, _entryChainageM, _trainLengthM);
        }

        // 1b. nastawnia — żądania tras PRZED odczytem autorytetów.
        //
        // Kolejność jest tu treścią, nie kosmetyką: `RequestRoute` woła w środku
        // `PublishAuthorities`, więc trasa zaryglowana teraz jest widoczna w autorytecie
        // odczytanym w fazie 2 i skład może ruszyć w TYM kroku, a nie w następnym.
        // Po fazie 2 byłoby o krok późno przy każdym odjeździe z peronu — 1/120 s na
        // zatrzymanie, czyli niewidocznie mało, ale mierzalnie nieprawdziwie.
        //
        // Przed 04.09.2026 tej fazy nie było i NIKT tras nie ryglował. Na planie, który
        // ich wymaga (`data/design/signalling/classic-2026.json`, `RequireRoute = true`),
        // linia wtedy nie ruszała: autorytet 47,00 m, powód `BlockNotReserved`.
        foreach (var train in _trains)
        {
            if (train.Drive is null)
            {
                continue;
            }

            _dispatcher.Dispatch(_signalling, train.Id, train.Drive.ChainageM, Steps);
        }

        // 2. odczyt — wszystkie autorytety ze stanu SPRZED kroku
        foreach (var train in _trains)
        {
            if (train.Drive is null)
            {
                continue;
            }

            var authority = _signalling.Authority(train.Id);
            train.Authority = authority;
            train.Drive.AuthorityEndM = authority.EndChainageM;
        }

        // 3. jazda i meldunek ruchu
        foreach (var train in _trains)
        {
            if (train.Drive is null)
            {
                continue;
            }

            var id = train.Id;
            train.Drive.Step(trace is null ? null : point => trace(id, point));
            _signalling.MoveTrain(id, train.Drive.ChainageM);
        }

        // 4. TURNBACK. Pojazd, który dojechał do ostatniego peronu, po zmierzonym czasie
        // nawrotu wypisuje się z planu i wraca na jego początek jako następny obieg.
        //
        // Bez tej fazy ostatni peron zostawał zajęty NA ZAWSZE, a dwie kolejne trasy
        // dzielą blok peronowy — więc następny skład nie miał jak zaryglować ostatniej
        // trasy. Zmierzone na pakiecie A: drugi skład stawał na 5514,04 m, za Schumanem.
        //
        // Faza jest OSTATNIA i to jest istotne: pojazd, który właśnie dojechał, ma
        // w tym kroku jeszcze pełny stan (`Drive.Result`), a zwolnienie peronu wchodzi
        // do autorytetów dopiero w następnym kroku — tak samo jak każda inna zmiana
        // zajętości. Wypisanie w fazie 1 dałoby skład, który znika, zanim ktokolwiek
        // zobaczył jego przyjazd.
        if (_turnbackSteps > 0L)
        {
            foreach (var train in _trains)
            {
                if (train.Drive is not { Finished: true })
                {
                    continue;
                }

                if (train.FinishedAtStep is null)
                {
                    train.FinishedAtStep = Steps;
                    continue;
                }

                if (Steps - train.FinishedAtStep.Value < _turnbackSteps)
                {
                    continue;
                }

                train._completed.Add(train.Drive.Result("turnback"));
                _signalling.ReleaseTrain(train.Id);
                train.Drive = null;
                train.Authority = null;
                train.FinishedAtStep = null;
                train.EnteredAtStep = null;

                // Nie ma tu żadnego przesuwania kroku wyjazdu i to jest ŚWIADOME.
                // Pierwsza wersja ustawiała `NextReleaseStep = Steps + 1`, a kontrola
                // negatywna pokazała, że to pole nic nie robi: faza wyjazdów idzie
                // PRZED tą fazą, więc pojazd wypisany w kroku N jest rozważany do
                // wjazdu najwcześniej w kroku N+1 i tak. Mutacja przywracająca stare
                // `ReleaseStep` przeszła 363/363, więc pole zostało usunięte, a nie
                // obronione. Czas nawrotu pilnuje wyłącznie `FinishedAtStep`.
            }
        }

        Steps++;
    }

    /// <summary>
    /// Krokuje linię aż do <see cref="Finished"/> albo do wyczerpania bezpiecznika.
    /// </summary>
    /// <param name="stepBudget">Bezpiecznik pętli.</param>
    /// <param name="trace">Ślad co krok, gdy podany.</param>
    /// <returns>Dlaczego pętla się skończyła.</returns>
    public string Run(
        long stepBudget = LineRun.DefaultStepBudget,
        Action<string, LineRun.TracePoint>? trace = null)
    {
        while (Steps < stepBudget && !Finished)
        {
            Step(trace);
        }

        return Finished ? "arrived" : "step-budget";
    }

    /// <summary>Wynik przejazdu jednego składu; odmawia dla składu, który nie wyjechał.</summary>
    /// <param name="trainId">Identyfikator składu.</param>
    /// <param name="reason">Dlaczego pętla wołającego się skończyła.</param>
    public LineRunResult ResultOf(string trainId, string reason)
    {
        foreach (var train in _trains)
        {
            if (string.Equals(train.Id, trainId, StringComparison.Ordinal))
            {
                return train.Drive is null
                    ? throw new InvalidOperationException(
                        $"skład {trainId} nie wyjechał — wynik przejazdu, którego nie było, " +
                        "byłby zerami nie do odróżnienia od przejazdu nieudanego")
                    : train.Drive.Result(reason);
            }
        }

        throw new ArgumentException($"nie ma składu {trainId} na linii", nameof(trainId));
    }

    /// <summary>
    /// Czy peron początkowy jest wolny na całej długości składu. Zajęty peron odkłada
    /// wyjazd na później — nie jest to regulacja ruchu, tylko to, że dwa składy nie mieszczą
    /// się w jednym miejscu.
    /// </summary>
    private bool EntryIsClear()
    {
        var plan = _signalling.Plan;
        var front = Math.Clamp(_entryChainageM, plan.StartM, plan.EndM);
        var rear = Math.Clamp(_entryChainageM - _trainLengthM, plan.StartM, plan.EndM);
        foreach (var block in plan.Blocks)
        {
            if (block.Overlaps(rear, front) && _signalling.StateOf(block.Id) != BlockState.Clear)
            {
                return false;
            }
        }

        return true;
    }
}
