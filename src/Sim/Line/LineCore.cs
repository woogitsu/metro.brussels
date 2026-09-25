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
    internal LineTrain(string id, long releaseStep, int entryStationIndex)
    {
        Id = id;
        ReleaseStep = releaseStep;
        EntryStationIndex = entryStationIndex;
    }

    /// <summary>Identyfikator składu; ten sam w sygnalizacji i w raporcie.</summary>
    public string Id { get; }

    /// <summary>Krok zegara linii, na którym skład ma wyjechać z pierwszej stacji.</summary>
    public long ReleaseStep { get; }

    /// <summary>Indeks peronu, na którym ten skład wchodzi na oś.</summary>
    public int EntryStationIndex { get; }

    /// <summary>
    /// Krok zegara linii, na którym skład faktycznie wszedł na plan; <c>null</c>, dopóki
    /// czeka — i znowu <c>null</c> od nawrotu do ponownego wjazdu.
    ///
    /// <para><b>Po co to pole istnieje.</b> Jest jedyną rzeczą, która odróżnia skład,
    /// który wyjechał o czasie, od składu, który stał, bo peron początkowy był zajęty:
    /// <see cref="OnLine"/> mówi tylko „jest na planie teraz", a <see cref="ReleaseStep"/>
    /// tylko „miał wyjechać wtedy". Bez tego pola różnica między rozkładem a wykonaniem
    /// wyjazdu nie jest w tym modelu obserwowalna z zewnątrz w ogóle.</para>
    ///
    /// <para><b>Dlaczego nie podzieliło losu <c>NextReleaseStep</c>.</b> Tamto pole
    /// zostało usunięte (komentarz przy nawrocie w <see cref="LineCore.Step"/>), bo
    /// <b>wyglądało, jakby coś robiło</b> — miało przesuwać wyjazd i nie przesuwało go,
    /// a mutacja przywracająca stary <see cref="ReleaseStep"/> przechodziła przez całą
    /// suitę. To pole nie udaje, że działa: jest pomiarem, nie sterowaniem, i żaden krok
    /// symulacji nie ma prawa go czytać. Nie zwalnia to go z obowiązku posiadania
    /// desygnatu — mówi go <c>Krok_wjazdu_na_plan_jest_krokiem_wjazdu_a_nie_krokiem_wyjazdu</c>
    /// w <c>tests/Sim.Tests/LineCoreTests.cs</c> i to ten test, a nie ten akapit, pada
    /// przy podmianie <c>Steps</c> na <c>ReleaseStep</c> albo na <c>Steps + 1</c>.</para>
    ///
    /// <para><b>Zastrzeżenie do różnicy wobec <see cref="ReleaseStep"/>.</b> Na PIERWSZYM
    /// wjeździe różnica <c>EnteredAtStep - ReleaseStep</c> jest czasem, o który peron
    /// początkowy był zajęty — nie regulacją ruchu, tylko brakiem miejsca. Po nawrocie
    /// przestaje nim być: <see cref="ReleaseStep"/> się nie rusza (nawrót pilnuje
    /// wyłącznie <c>FinishedAtStep</c>), więc różnica obejmowałaby cały poprzedni obieg.
    /// Dla obiegu drugiego i dalszych to pole znaczy tyle, ile mówi jego nazwa: krok
    /// wjazdu na plan, i nic ponadto.</para>
    /// </summary>
    public long? EnteredAtStep { get; internal set; }

    /// <summary>Prowadzenie; <c>null</c>, dopóki skład nie wszedł na plan.</summary>
    public LineDrive? Drive { get; internal set; }

    /// <summary>Autorytet z ostatniego kroku; <c>null</c>, dopóki skład nie wszedł na plan.</summary>
    public MovementAuthority? Authority { get; internal set; }

    /// <summary>
    /// Decyzja ochrony pociągu z ostatniego kroku; <c>null</c>, gdy linia jedzie
    /// bez ATP albo skład jeszcze nie wszedł na plan.
    ///
    /// <para><b>To jest ta sama decyzja, która działała.</b> Nie jest przeliczana na
    /// potrzeby raportu ani HUD-u — wołający czyta dokładnie to, co filtr polecenia
    /// zastosował w fazie 3. Drugie wołanie <c>Supervise</c> „do pokazania" dałoby
    /// liczbę policzoną z innego stanu i nie dałoby się powiedzieć, która jest
    /// prawdziwa.</para>
    /// </summary>
    public ProtectionDecision? Protection { get; internal set; }

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

    /// <summary>
    /// Kto prowadzi ten skład — MB-06. Domyślnie <see cref="ControlOwner.Autopilot"/>.
    ///
    /// <para>Pole jest tu, a nie w <see cref="LineDrive"/>, bo właściciel sterowania jest
    /// własnością POJAZDU NA LINII, a nie jego bieżącego przejazdu: <c>Drive</c> znika
    /// i powstaje od nowa przy każdym nawrocie (faza 4 <c>Step</c>), a przejęcie ma
    /// przetrwać obieg. Trzymanie go w <c>Drive</c> oddawałoby sterowanie autopilotowi
    /// po cichu, w środku nawrotu, i nikt by tego nie zauważył — bo skład i tak wtedy
    /// stoi.</para>
    /// </summary>
    public ControlOwner Owner { get; internal set; } = ControlOwner.Autopilot;

    /// <summary>
    /// Położenie dźwigni maszynisty — trwa DO ZMIANY, a nie do końca kroku.
    ///
    /// <para><b>Dlaczego trwa.</b> Nastawnik jest dźwignią, a nie przyciskiem: człowiek
    /// stawia go raz i zostaje, gdzie go postawiono. Komenda wygasająca po kroku dawałaby
    /// skład, który przy każdej zgubionej klatce przechodzi na wybieg — czyli sterowanie
    /// zależne od tego, jak szybko rysuje się obraz. Ta sama zasada, co w kabinie
    /// (<c>FirstRun</c> trzyma położenie nastawnika między klatkami).</para>
    ///
    /// <para><c>null</c> dopóki nikt nie przejął sterowania; ustawiane na komendę
    /// wykonywaną w chwili przejęcia, żeby przejęcie nie zmieniło ani prędkości,
    /// ani kursu.</para>
    /// </summary>
    public DriverCommand? DriverCommand { get; internal set; }

    /// <summary>Prawda, gdy skład jest na planie.</summary>
    public bool OnLine => Drive is not null && !LeftPlan;

    /// <summary>
    /// Skład ZJECHAŁ Z PLANU po dojechaniu do ostatniej stacji — MB-07, 14.09.2026.
    ///
    /// <para><b>Czym to się różni od nawrotu.</b> Nawrót zwalnia bloki i wpuszcza
    /// skład z powrotem na początek osi jako następny obieg; zjazd zwalnia bloki
    /// i NIE wpuszcza go z powrotem. Jedno i drugie jest wypisaniem z planu; różni
    /// je to, czy pojazd wraca.</para>
    ///
    /// <para><b>Dlaczego <c>Drive</c> ZOSTAJE, choć skład zjechał.</b> Bo
    /// <see cref="Finished"/> czyta <c>Drive.Finished</c>, a
    /// <see cref="LineCore.Finished"/> jest koniunkcją po składach. Wyzerowanie
    /// <c>Drive</c> przy zjeździe cofnęłoby skład do stanu „czeka na wyjazd",
    /// przez co linia NIGDY nie byłaby skończona, a pętla przebiegu kręciłaby się
    /// bez końca — zmierzone na tej samej usterce od drugiej strony. Wynik przejazdu
    /// też stoi w <c>Drive</c> i jest po zjeździe nadal potrzebny.</para>
    /// </summary>
    public bool LeftPlan { get; internal set; }

    /// <summary>
    /// Prawda, gdy skład dojechał do ostatniej stacji osi.
    /// <para><b>Także w czasie nawrotu</b> — i to nie jest szczegół (6.D70). Faza
    /// nawrotu ZOSTAWIA <c>Drive</c> na miejscu przez cały <c>TurnbackSteps</c>
    /// i czyści je dopiero po odczekaniu, więc przez to okno skład jest
    /// <c>Finished</c>, choć zaraz ruszy w kolejny obieg.</para>
    /// </summary>
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
/// <para><b>Kolejność w kroku jest częścią modelu, nie szczegółem.</b> Krok idzie fazami
/// nad **wszystkimi** składami, a nie skład po składzie:</para>
/// <list type="number">
/// <item>wyjazdy: składy, których krok wyjazdu nadszedł, wchodzą na plan, o ile peron
///   początkowy jest wolny;</item>
/// <item>nastawnia: każdy skład bez trasy żąda tej, która wyprowadza z jego bloku —
///   PRZED odczytem, żeby zaryglowana trasa była widoczna w tym samym kroku;</item>
/// <item>odczyt: każdy skład dostaje autorytet policzony ze stanu **sprzed** kroku,
///   a przy włączonym ATP także decyzję ochrony z tego samego stanu;</item>
/// <item>jazda i ruch: każdy skład robi swój krok, po czym melduje nowe czoło;</item>
/// <item>nawrót: skład, który dojechał i odstał czas nawrotu, wypisuje się z planu
///   i wraca na jego początek — faza jest ostatnia, żeby przyjazd był widoczny.</item>
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
    private readonly TrainProtection? _protection;
    private readonly long _turnbackSteps;
    private readonly TrackAxis _axis;
    private readonly RunConditions _conditions;
    private readonly LineRunSettings _settings;
    private readonly TrainController _controller;
    private readonly BrakingPointSolver _solver;
    private readonly FixedStep _step;
    private readonly double _trainLengthM;
    private readonly List<LineTrain> _trains = new();

    /// <summary>Identity of the physical axis used by this line clock.</summary>
    public string AxisId => _axis.Id;

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
    /// <param name="plan">
    /// Plan bloków. Musi być zbudowany dla tej samej osi co <paramref name="axis"/> —
    /// niezgodne <c>AxisId</c> jest odmową, bo kilometraż bloków i kilometraż stacji
    /// muszą pochodzić z jednego przebiegu.
    /// </param>
    /// <param name="axis">Oś z kilometrażem stacji; po niej jedzie każdy skład tej linii.</param>
    /// <param name="conditions">Masa, pochylenie, przyczepność i otoczenie toru, wspólne dla linii.</param>
    /// <param name="settings">
    /// Założenia przejazdu — ten sam obiekt dostaje każde prowadzenie, więc
    /// <see cref="SpeedLimitMps"/> jest liczbą prowadzenia, a nie jej kopią.
    /// </param>
    /// <param name="controller">Kontroler ruchu z T-310; jeden na linię, bo jest bezstanowy.</param>
    /// <param name="solver">Solver punktu hamowania z T-311, wołany przy każdym podejściu do stacji.</param>
    /// <param name="step">Krok stały zegara linii; ten sam dla wszystkich składów, inaczej nie ma determinizmu.</param>
    /// <param name="trainLengthM">
    /// Długość składu w metrach; z rejestru pojazdu, nie z powietrza. Linia zajmuje nią
    /// bloki: ogon leży o tyle za czołem i to on zwalnia blok za sobą.
    /// </param>
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
        : this(plan, axis, conditions, settings, controller, solver, step, trainLengthM,
            turnbackSeconds, protection: null)
    {
    }

    /// <summary>
    /// Linia z OCHRONĄ POCIĄGU, która naprawdę ingeruje w polecenie — decyzja
    /// właściciela z 04.09.2026: „ostrzeżenie, potem hamulec służbowy".
    ///
    /// <para><b>Ochrona jest opcją, bo jej brak też jest stanem sieci.</b> `null` znaczy
    /// „linia bez ATP" i wtedy przejazd jest bit w bit taki, jak przed tą zmianą —
    /// ani jedno wołanie <c>Supervise</c> się nie odbywa, więc nie powstaje ani jedno
    /// zdarzenie sygnalizacji. Nie jest to wyłącznik na wszelki wypadek: tryb
    /// <c>classic_2026</c> na pakiecie A ma ochronę, a przejazd bez planu sygnalizacji
    /// nie ma czego nadzorować, bo nie ma autorytetu jazdy.</para>
    ///
    /// <para><b>Gdzie ochrona wchodzi w krok.</b> Nadzór jest w fazie 2, razem
    /// z odczytem autorytetów: liczy się ze stanu SPRZED kroku. Zastosowanie decyzji jest
    /// w fazie 3, przez <see cref="LineDrive.Supervisor"/>. Że akurat ta faza jest
    /// NIEODRÓŻNIALNA od trzeciej — zmierzone, osiem odstępów, zero różnicy — opisuje
    /// komentarz przy samej fazie; niezmiennik zostaje, ale nie udaje, że coś ratuje.</para>
    ///
    /// <para><b>Czego ochrona NIE rusza.</b> Zatrzasku hamowania w prowadzeniu
    /// (<c>_braking</c>). Filtr stoi ZA zatrzaskiem, więc hamulec podany przez ATP nie
    /// zatrzaskuje jazdy na cel — ingerencja trwa dokładnie tyle, ile trwa przekroczenie,
    /// i puszcza. Gdyby zatrzaskiwała, skład raz zwolniony przez ATP dojeżdżałby do
    /// stacji wybiegiem, bo zatrzask nie wraca do trakcji.</para>
    /// </summary>
    /// <param name="plan">Plan bloków dla tej samej osi.</param>
    /// <param name="axis">Oś z kilometrażem stacji.</param>
    /// <param name="conditions">Masa, pochylenie, przyczepność, otoczenie toru.</param>
    /// <param name="settings">Założenia przejazdu — wszystkie bez źródła.</param>
    /// <param name="controller">Kontroler z T-310.</param>
    /// <param name="solver">Solver punktu hamowania z T-311.</param>
    /// <param name="step">Krok stały; ten sam dla całej linii.</param>
    /// <param name="trainLengthM">Długość składu; z rejestru pojazdu, nie z powietrza.</param>
    /// <param name="turnbackSeconds">
    /// Czas nawrotu w sekundach. <b>Zero wyłącza turnback</b> i wtedy linia zachowuje
    /// się tak, jak przed jego wprowadzeniem: pojazd kończy na ostatnim peronie i tam
    /// zostaje. Wartość ujemna jest odmową, nie wyłączeniem; czas krótszy niż jeden
    /// krok symulacji też, bo zaokrągliłby się do zera i wyłączył nawrót po cichu.
    /// </param>
    /// <param name="protection">
    /// Ochrona pociągu. Musi być zbudowana na TYM SAMYM obiekcie planu — inaczej
    /// nadzorowałaby limit i bloki innego planu niż ten, po którym linia jedzie,
    /// a rozjazd byłby widoczny tylko jako dziwne liczby w raporcie.
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
        double turnbackSeconds,
        TrainProtection? protection)
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

        if (protection is not null && !ReferenceEquals(protection.Plan, plan))
        {
            throw new ArgumentException(
                "ochrona pociągu jest zbudowana na innym obiekcie planu niż linia — "
                + "nadzorowałaby limit prędkości i bloki planu, po którym nikt nie jedzie",
                nameof(protection));
        }

        _signalling = new FixedBlockSystem(plan);
        _dispatcher = new RouteDispatcher(plan);
        _protection = protection;
        _axis = axis;
        _conditions = conditions;
        _settings = settings;
        _controller = controller;
        _solver = solver;
        _step = step;
        _trainLengthM = trainLengthM;

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
        M7(plan, axis, conditions, settings, turnbackSeconds, atp: false);

    /// <summary>
    /// Linia M7 z turnbackiem i z OCHRONĄ POCIĄGU, która ingeruje w polecenie.
    ///
    /// <para>Ochrona jest zbudowana z TEGO SAMEGO planu i z modelu M7, więc opóźnienia
    /// hamulców pochodzą z rejestru pojazdu, a nie z argumentu — dokładnie tak samo jak
    /// kontroler i solver linii. Solvera ochrona ma własnego, ale z tego samego modelu,
    /// więc krzywa hamowania jest ta z T-311, a nie druga obok niej.</para>
    /// </summary>
    /// <param name="plan">Plan bloków; ten sam obiekt dostaje ochrona, więc nadzoruje tę linię.</param>
    /// <param name="axis">Oś z kilometrażem stacji; musi być tą, dla której powstał plan.</param>
    /// <param name="conditions">Masa, pochylenie, przyczepność, otoczenie toru.</param>
    /// <param name="settings">Założenia przejazdu — wszystkie bez źródła.</param>
    /// <param name="turnbackSeconds">Czas nawrotu; zero wyłącza turnback, ujemny jest odmową.</param>
    /// <param name="atp">
    /// <c>false</c> daje linię bez ochrony i przejazd bit w bit taki jak przed
    /// wprowadzeniem ATP; <c>true</c> włącza nadzór i ingerencję.
    /// </param>
    /// <returns>Linia gotowa na pierwszy krok; składy dokłada <see cref="Add"/>.</returns>
    public static LineCore M7(
        SignallingPlan plan, TrackAxis axis, RunConditions conditions,
        LineRunSettings settings, double turnbackSeconds, bool atp) =>
        new(plan, axis, conditions, settings,
            new TrainController(VehicleModel.M7),
            new BrakingPointSolver(VehicleModel.M7),
            FixedStep.Simulation,
            VehicleRegistry.M7.RequireValue("parameters.length_m", ParameterStatus.Spec),
            turnbackSeconds,
            atp ? new TrainProtection(plan, VehicleModel.M7) : null);

    /// <summary>Sygnalizacja linii — do odczytu zajętości, zdarzeń i odcisku stanu.</summary>
    public FixedBlockSystem Signalling => _signalling;

    /// <summary>
    /// Nastawnia automatyczna tej linii — do odczytu licznika zaryglowanych tras i odmów.
    ///
    /// Odmowa NIE jest usterką: blok przed nosem bywa zajęty i wtedy sygnał ma stać na
    /// stój. Licznik jest tu, żeby dało się to zmierzyć, a nie żeby świecił na zielono.
    /// </summary>
    public RouteDispatcher Dispatcher => _dispatcher;

    /// <summary>
    /// Ochrona pociągu tej linii; <c>null</c>, gdy linia jedzie bez ATP.
    ///
    /// Jest do ODCZYTU — po to, żeby raport i HUD pokazały opóźnienia hamulców, którymi
    /// ochrona naprawdę liczy, a nie kopię tych liczb wpisaną obok.
    /// </summary>
    public TrainProtection? Protection => _protection;

    /// <summary>Czy ta linia ma ochronę, która ingeruje w polecenie.</summary>
    public bool ProtectionEnabled => _protection is not null;

    /// <summary>
    /// Kroki składów, w których prędkość przekraczała dopuszczalną — czyli OSTRZEŻENIA.
    ///
    /// Licznik jest po kroku-składzie, nie po zdarzeniu: zdarzenia powstają na przejściu
    /// i jedno przekroczenie trwające dziesięć sekund daje jedno zdarzenie, ale 1200
    /// kroków. Do pomiaru „ile przejazdu spędzono nad limitem" potrzebna jest ta druga
    /// liczba, a nie pierwsza.
    /// </summary>
    public long ProtectionWarnings { get; private set; }

    /// <summary>Kroki składów z ingerencją hamulcem służbowym.</summary>
    public long ServiceInterventions { get; private set; }

    /// <summary>Kroki składów z ingerencją awaryjną.</summary>
    public long EmergencyInterventions { get; private set; }

    /// <summary>
    /// Największe opóźnienie, jakiego ochrona zażądała w tym przejeździe; zero, gdy nie
    /// ingerowała ani razu. Do porównania z opóźnieniem hamulca służbowego: żądanie
    /// większe znaczy, że nastawnik został obcięty i pełny hamulec nie wystarczył.
    /// </summary>
    public double MaxBrakeDemandMps2 { get; private set; }

    /// <summary>Liczba wykonanych kroków zegara linii.</summary>
    public long Steps { get; private set; }

    /// <summary>Czas linii; funkcja liczby kroków, nigdy suma.</summary>
    public double TimeSeconds => _step.TimeAt(Steps);

    /// <summary>Składy w kolejności zgłoszenia.</summary>
    public IReadOnlyList<LineTrain> Trains => _trains;

    /// <summary>
    /// Ograniczenie prędkości, którym linia prowadzi każdy swój skład — ten sam obiekt
    /// <see cref="LineRunSettings"/> dostaje w <see cref="Step"/> każde nowe
    /// <see cref="LineDrive"/>, więc jest to liczba prowadzenia, nie jej kopia.
    ///
    /// <para>Widok musi mieć skąd ją wziąć PRZED pierwszym krokiem: prowadzenie powstaje
    /// leniwie, w fazie wyjazdów, więc w chwili wypisywania nagłówka
    /// <see cref="LineTrain.Drive"/> jest jeszcze nullem. Tą dziurą nagłówek wracał do
    /// limitu ze scenariusza — 80 km/h prędkości konstrukcyjnej M7 — przy przejeździe
    /// jadącym 70 km/h.</para>
    /// </summary>
    public double SpeedLimitMps => _settings.SpeedLimitMps;

    /// <summary>
    /// Czy ta linia ma włączony turnback.
    /// <para><b>Opis „pojazdy krążą i nigdy nie kończą" jest tu PRZEPISANY, bo był
    /// nieprawdziwy dla jednego składu</b> (6.D70). Zmierzone 09.09.2026 na pakiecie A
    /// z nawrotem 240 s i JEDNYM składem: <c>Run()</c> zwraca <c>arrived</c> po
    /// 89 958 krokach, z <b>zerem</b> zamkniętych obiegów. Powód jest w zdaniu wyżej:
    /// <see cref="LineTrain.Finished"/> jest prawdą przez całe okno nawrotu, więc
    /// przy jednym składzie <see cref="Finished"/> całej linii też — i pętla
    /// <c>Run()</c> wychodzi, zanim nawrót zdąży cokolwiek zrobić.</para>
    /// <para>Nawrót przy tym DZIAŁA: ta sama linia dokrokowana <c>Step()</c> zamyka
    /// obieg z powodem <c>turnback</c>. „Nigdy nie kończą" jest prawdą od DWÓCH
    /// składów wzwyż, bo wtedy któryś zawsze jedzie i koniunkcja w
    /// <see cref="Finished"/> nie zachodzi. Oba zachowania są przybite testami
    /// w <c>LineCoreTests</c>.</para>
    /// </summary>
    public bool TurnbackEnabled => _turnbackSteps > 0L;

    /// <summary>Czas nawrotu w krokach; zero, gdy turnback wyłączony.</summary>
    public long TurnbackSteps => _turnbackSteps;

    /// <summary>
    /// Prawda, gdy każdy zgłoszony skład wszedł na plan i dojechał do ostatniej stacji.
    /// Na krótkiej osi z krótkim odstępem nie nastąpi to nigdy — patrz akapit o turnbacku
    /// w opisie klasy. Linia bez ani jednego zgłoszonego składu nie jest skończona.
    /// <para>Z nawrotem i JEDNYM składem ta koniunkcja ZACHODZI w chwili przyjazdu —
    /// zmierzone, patrz <see cref="TurnbackEnabled"/>. Dopiero od dwóch składów
    /// wzwyż któryś zawsze jedzie i linia nie kończy się nigdy (6.D70).</para>
    /// </summary>
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
        => AddAtStation(trainId, releaseStep, 0);

    /// <summary>Planuje pierwszy wjazd od wskazanej stacji osi, bez planowania kolejnego kursu.</summary>
    public LineTrain AddAtStation(string trainId, long releaseStep, int stationIndex)
    {
        ArgumentNullException.ThrowIfNull(trainId);
        if (stationIndex < 0 || stationIndex >= _axis.Stations.Count - 1)
        {
            throw new ArgumentOutOfRangeException(nameof(stationIndex), stationIndex,
                "Stacja wejścia musi mieć następną stację na osi.");
        }
        if (stationIndex > 0 && TurnbackEnabled)
        {
            throw new InvalidOperationException(
                "Nawrót składu ze środka osi wymaga osobnego rozkładu kolejnego kursu.");
        }
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

        var train = new LineTrain(trainId, releaseStep, stationIndex);
        _trains.Add(train);
        return train;
    }

    /// <summary>
    /// Oddaje sterowanie składem człowiekowi, zaczynając od komendy, którą skład
    /// wykonuje w tej chwili.
    ///
    /// <para><b>Przejęcie nie zmienia ani pozycji, ani prędkości, ani kursu</b> — pole
    /// „Weryfikacja" MB-06 żąda tego wprost. Bierze się to stąd, że dźwignia startuje
    /// z <c>LineDrive.LastCommand</c>, czyli z polecenia PRZED ochroną, które autopilot
    /// wydał w poprzednim kroku. Przejęcie zaczynające się od zera nastawnika zmieniłoby
    /// wszystkie trzy rzeczy już w następnym kroku, a wyglądałoby na „samo przełączenie".</para>
    ///
    /// <para><b>Skład, który nie wszedł jeszcze na plan, przejąć się NIE DA — i to jest
    /// poprawka twierdzenia, które stało tu wcześniej.</b> Poprzednia wersja obiecywała,
    /// że „dźwignia dostanie wtedy pozycję przy wjeździe", i było to nieprawdą
    /// o mierzalnych skutkach. `Drive` powstaje w fazie 1 tego samego kroku, a jego
    /// `LastCommand` jest wtedy jeszcze inicjalizatorem pola (<c>Coast</c>, czyli
    /// <c>default(DriverCommand)</c>) — bo `Step` jeszcze nie biegł. Przejęty przed
    /// wjazdem skład dostawał więc wybieg z zerową prędkością, **stał na kilometrażu
    /// wjazdowym w nieskończoność** i blokował blok wjazdowy: zmierzone — po 100 s
    /// przejęty skład miał 0,000 m i 0,000 m/s wobec 997,498 m i 16,667 m/s pod
    /// autopilotem, a drugi skład po 250 s wciąż nie był na planie.</para>
    ///
    /// <para>Odmowa, a nie podstawienie jakiejkolwiek komendy — bo nie ma komendy,
    /// którą skład „właśnie wykonuje", dopóki nie wykonuje żadnej. To ta sama zasada,
    /// co przy <see cref="Drive(string, DriverCommand)"/>: cichy brak skutku wygląda
    /// w logu tak samo jak sterowanie, które nic nie daje. Po wjeździe składu na plan
    /// przejęcie działa normalnie.</para>
    /// </summary>
    /// <param name="trainId">Identyfikator składu.</param>
    /// <returns>Pojazd, którego sterowanie przejęto.</returns>
    /// <exception cref="ArgumentException">Nie ma składu o tym identyfikatorze.</exception>
    /// <exception cref="InvalidOperationException">Skład nie wszedł jeszcze na plan.</exception>
    public LineTrain TakeControl(string trainId)
    {
        var train = Find(trainId);
        if (train.Drive is null)
        {
            throw new InvalidOperationException(
                $"Skład {trainId} nie wszedł jeszcze na plan — nie ma czego przejąć. "
                + "Przejęcie jest możliwe dopiero po wyjeździe.");
        }

        train.Owner = ControlOwner.Driver;
        train.DriverCommand ??= train.Drive.LastCommand;
        return train;
    }

    /// <summary>
    /// Oddaje sterowanie autopilotowi.
    ///
    /// <para><b>Oddanie też nie zmienia stanu składu</b>, i to nie dlatego, że o to
    /// zadbano osobno: autopilot liczy swoje polecenie i posuwa swój zatrzask hamowania
    /// przez CAŁY czas przejęcia (powód przy <c>LineDrive.DriverInput</c>), więc
    /// w kroku po oddaniu jest dokładnie tam, gdzie byłby, gdyby prowadził sam.</para>
    ///
    /// <para>Dźwignia jest przy oddaniu ZAPOMINANA. Zostawiona pamiętałaby położenie
    /// sprzed oddania i następne przejęcie zaczynałoby się od komendy, której skład
    /// w tej chwili nie wykonuje — czyli dokładnie od tego skoku, którego
    /// <see cref="TakeControl"/> unika.</para>
    /// </summary>
    /// <param name="trainId">Identyfikator składu.</param>
    /// <returns>Pojazd, którego sterowanie oddano.</returns>
    /// <exception cref="ArgumentException">Nie ma składu o tym identyfikatorze.</exception>
    public LineTrain ReleaseControl(string trainId)
    {
        var train = Find(trainId);
        train.Owner = ControlOwner.Autopilot;
        train.DriverCommand = null;
        return train;
    }

    /// <summary>
    /// Stawia dźwignię maszynisty składu <paramref name="trainId"/>.
    ///
    /// <para>Odmawia, gdy sterowania nie przejęto — i jest to ODMOWA, a nie ciche
    /// przejęcie. Komenda podana składowi prowadzonemu przez autopilota nie miałaby
    /// gdzie zadziałać, więc wołający, który jej nie widzi, wierzyłby, że prowadzi,
    /// a prowadziłby autopilot. Cichy brak skutku wygląda w logu tak samo jak
    /// sterowanie, które nic nie daje.</para>
    /// </summary>
    /// <param name="trainId">Identyfikator składu.</param>
    /// <param name="command">Nowe położenie dźwigni.</param>
    /// <exception cref="ArgumentException">Nie ma składu o tym identyfikatorze.</exception>
    /// <exception cref="InvalidOperationException">Sterowania tego składu nie przejęto.</exception>
    public void Drive(string trainId, DriverCommand command)
    {
        var train = Find(trainId);
        if (train.Owner != ControlOwner.Driver)
        {
            throw new InvalidOperationException(
                $"Sterowania składu {trainId} nie przejęto — zawołaj najpierw TakeControl.");
        }

        train.DriverCommand = command;
    }

    /// <summary>
    /// Polecenie otwarcia drzwi składu <paramref name="trainId"/> (MB-08).
    ///
    /// <para><b>Odmowa, nie wyjątek — i to jest różnica wobec
    /// <see cref="Drive(string, DriverCommand)"/>, a nie niekonsekwencja.</b> Dźwignia
    /// podana nieprzejętemu składowi nie ma gdzie zadziałać i nie ma czym o tym
    /// powiedzieć, więc musi rzucić. Polecenie drzwi ma własny kanał odpowiedzi:
    /// <see cref="DoorRequestResult"/> niesie powód, który gracz zobaczy na ekranie.
    /// Naciśnięcie klawisza w złej chwili jest zwykłym zdarzeniem w grze, a nie błędem
    /// programu.</para>
    /// </summary>
    /// <param name="trainId">Identyfikator składu.</param>
    /// <returns>Przyjęcie albo odmowa z powodem.</returns>
    /// <exception cref="ArgumentException">Nie ma składu o tym identyfikatorze.</exception>
    public DoorRequestResult RequestDoorOpen(string trainId) =>
        DoorRequest(trainId, drive => drive.RequestDoorOpen());

    /// <summary>Polecenie zamknięcia drzwi składu <paramref name="trainId"/> (MB-08).</summary>
    /// <param name="trainId">Identyfikator składu.</param>
    /// <returns>Przyjęcie albo odmowa z powodem.</returns>
    /// <exception cref="ArgumentException">Nie ma składu o tym identyfikatorze.</exception>
    public DoorRequestResult RequestDoorClose(string trainId) =>
        DoorRequest(trainId, drive => drive.RequestDoorClose());

    /// <summary>
    /// Wspólna droga obu poleceń drzwi: te same dwie odmowy przed przekazaniem dalej.
    ///
    /// <para>Jedna metoda, bo dwie kopie tych samych warunków rozjechałyby się przy
    /// pierwszym nowym powodzie odmowy — ta sama zasada, co przy nastawach `line`
    /// w <c>Sim.Runner</c> (6.D44).</para>
    /// </summary>
    private DoorRequestResult DoorRequest(string trainId, Func<LineDrive, DoorRequestResult> request)
    {
        var train = Find(trainId);
        if (train.Drive is null || train.LeftPlan)
        {
            return DoorRequestResult.Refused(DoorRefusal.OutsidePlatformWindow);
        }

        return train.Owner != ControlOwner.Driver
            ? DoorRequestResult.Refused(DoorRefusal.AutomaticControl)
            : request(train.Drive);
    }

    /// <summary>Pojazd o zadanym identyfikatorze albo wyjątek z jego nazwą.</summary>
    private LineTrain Find(string trainId)
    {
        ArgumentNullException.ThrowIfNull(trainId);
        foreach (var train in _trains)
        {
            if (string.Equals(train.Id, trainId, StringComparison.Ordinal))
            {
                return train;
            }
        }

        throw new ArgumentException($"Nie ma składu o identyfikatorze {trainId}.", nameof(trainId));
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
            var entry = _axis.Stations[train.EntryStationIndex].ChainageM;
            if (train.Drive is not null || train.ReleaseStep > Steps || !EntryIsClear(entry))
            {
                continue;
            }

            train.Drive = new LineDrive(_axis, _conditions, _settings, _controller, _solver, _step,
                train.EntryStationIndex);
            train.EnteredAtStep = Steps;

            // Filtr ochrony zakładany RAZ, przy wjeździe na plan, i czytający decyzję
            // z fazy 2 tego samego kroku. Domknięcie bierze `train`, a nie kopię
            // decyzji, bo decyzja zmienia się co krok, a filtr ma zostać ten sam.
            if (_protection is not null)
            {
                var supervised = train;
                var protection = _protection;
                train.Drive.Supervisor = command => supervised.Protection is ProtectionDecision decision
                    ? decision.Apply(command, protection.ServiceBrakeMps2)
                    : command;
            }

            _signalling.RegisterTrain(train.Id, entry, _trainLengthM);
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

            if (train.LeftPlan)
            {
                // Skład zjechał z planu — nie ma dla kogo ryglować trasy, a nastawnia
                // nie zna już tego identyfikatora.
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

            if (train.LeftPlan)
            {
                // Jak wyżej: `Authority` woła `Require(trainId)`, a zjechanego składu
                // w systemie blokowym już nie ma. Autorytet i decyzja ochrony zostają
                // wyzerowane w chwili zjazdu i nie są liczone od nowa.
                continue;
            }

            var authority = _signalling.Authority(train.Id);
            train.Authority = authority;
            train.Drive.AuthorityEndM = authority.EndChainageM;

            // Nadzór ochrony stoi TUTAJ, ze stanem sprzed kroku, razem z odczytem
            // autorytetów — ale uczciwie trzeba powiedzieć, ILE z tego wynika.
            //
            // Zasada jest ta sama, co przy autorytetach: prędkość dopuszczalna liczy się
            // z zajętości bloków, a w fazie 3 zajętość zmienia się w trakcie, skład po
            // składzie. Nadzór po ruchu byłby więc odczytem ze stanu, który inny skład
            // zdążył już zmienić w tym samym kroku.
            //
            // ZMIERZONE 04.09.2026, i wynik jest inny, niż zakładała pierwsza wersja tego
            // komentarza: przeniesienie nadzoru do fazy 3 NIE ZMIENIA ani jednej liczby.
            // Kontrola negatywna na pakiecie A, dwa składy przy limicie 76 km/h, osiem
            // odstępów od 5 s do 150 s (przy 5 s nastawnia odmawia 603 razy, czyli składy
            // są tak blisko, jak ryglowanie pozwala): sumy kilometraży obu składów,
            // liczba ingerencji i liczba odmów wychodzą IDENTYCZNE. Cały zestaw 376
            // testów też przechodzi po mutacji.
            //
            // Powód jest strukturalny, nie przypadkowy: `MoveTrain` innego składu może
            // autorytet tego składu tylko WYDŁUŻYĆ (zwolniony blok), nigdy skrócić.
            // Żeby wydłużenie zmieniło decyzję, skład musiałby być nad prędkością
            // dopuszczalną dokładnie w tym kroku, w którym poprzedzający zwalnia blok —
            // a skład, który jedzie za sygnałem, jest wtedy zatrzymany albo pełznie.
            //
            // Faza 2 zostaje mimo to, bo niezmiennik „odczyt przed ruchem" ma trzymać
            // z zasady, a nie dlatego, że akurat udało się go złamać niewidocznie.
            // Ale nie wolno pisać, że to ta faza broni niezależności od kolejności:
            // broni jej to, że składy respektują autorytet, i to jest przypięte testem
            // `Z_ochrona_wynik_nadal_nie_zalezy_od_kolejnosci_zgloszenia_skladow`.
            if (_protection is null)
            {
                continue;
            }

            var decision = _protection.Supervise(_signalling, train.Id, train.Drive.State.SpeedMps);
            train.Protection = decision;
            if (decision.Overspeed)
            {
                ProtectionWarnings++;
            }

            switch (decision.Action)
            {
                case ProtectionAction.ServiceIntervention:
                    ServiceInterventions++;
                    break;
                case ProtectionAction.EmergencyIntervention:
                    EmergencyInterventions++;
                    break;
                default:
                    break;
            }

            if (decision.BrakeDemandMps2 > MaxBrakeDemandMps2)
            {
                MaxBrakeDemandMps2 = decision.BrakeDemandMps2;
            }
        }

        // 3. jazda i meldunek ruchu
        foreach (var train in _trains)
        {
            if (train.Drive is null || train.LeftPlan)
            {
                // Skład zjechany z planu NIE jest krokowany i NIE melduje ruchu.
                // `MoveTrain` woła `Require(trainId)`, więc meldunek po zjeździe
                // byłby wyjątkiem w środku kroku linii, a nie cichym pominięciem.
                continue;
            }

            var id = train.Id;

            // WŁAŚCICIEL STEROWANIA WCHODZI TUTAJ, w fazie 3, tuż przed krokiem — bo
            // tutaj i tylko tutaj polecenie dociera do kontrolera. Autopilot dostaje
            // `null`, czyli prowadzi tak jak przed MB-06, co do bitu.
            //
            // Dźwignia przejętego składu bez ani jednej komendy dostaje pozycję
            // z poprzedniego kroku (`LastCommand`) — nie wybieg. Wybieg byłby cichą
            // zmianą prowadzenia w chwili przejęcia, czyli dokładnie tym, czego pole
            // „Weryfikacja" MB-06 zabrania.
            if (train.Owner == ControlOwner.Driver)
            {
                train.DriverCommand ??= train.Drive.LastCommand;
                train.Drive.DriverInput = train.DriverCommand;
            }
            else
            {
                train.Drive.DriverInput = null;
            }

            // TRYB DRZWI IDZIE ZA WŁAŚCICIELEM, ale wchodzi w życie dopiero przy
            // ZAKŁADANIU postoju (MB-08). Człowiek u steru dostaje drzwi ręczne, autopilot
            // automatyczne, i ta linijka jest jedynym miejscem, w którym tryb się zmienia.
            //
            // Stąd bierze się zdanie z pola „Weryfikacja" MB-08 — „take/release w czasie
            // cyklu NIE RESETUJE drzwi": trwający postój trzyma swój tryb, bo
            // `LineDrive.DoorControl` opisuje postój NASTĘPNY, nie bieżący.
            //
            // Przejazd bez ani jednego przejęcia ustawia tu zawsze `Automatic`, czyli
            // dokładnie wartość domyślną — i dlatego ślad autopilota nie rusza się o bit.
            train.Drive.DoorControl = train.Owner == ControlOwner.Driver
                ? DoorControl.Manual
                : DoorControl.Automatic;

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
        //
        // **BEZ NAWROTU FAZA TEŻ DZIAŁA i to jest poprawka z MB-07 (14.09.2026).**
        // Ten akapit jest DOPISANY obok akapitu wyżej, a nie zamiast niego: opis
        // nawrotu zostaje w całości i nic z niego nie znika.
        //
        // Do 14.09.2026 cała faza stała pod `if (_turnbackSteps > 0L)`, więc przy
        // `turnbackSeconds: 0` — czyli tak, jak woła ją SCENA — skład, który dojechał,
        // zostawał na ostatnim peronie NA ZAWSZE. Akapit wyżej opisuje dokładnie ten
        // skutek („ostatni peron zostawał zajęty NA ZAWSZE… drugi skład stawał na
        // 5514,04 m") i został napisany, gdy naprawiano to DLA NAWROTU. Przy zerowym
        // nawrocie usterka została nietknięta i jest zmierzona ponownie, tą samą
        // liczbą: KABINA kończy na 6686,05 m trzymając `S11` i `P12`, a SKLAD-02
        // staje na **5514,01 m** z autorytetem 5514,35 m i powodem `OccupiedBlock`,
        // i stoi tam przez 400 000 kroków, czyli 55 minut symulacji. Odstęp nie ma
        // z tym nic wspólnego: 4200 i 37 200 kroków dają wynik CO DO CENTYMETRA ten sam.
        //
        // Decyzja właściciela z 14.09.2026: skład, który dojechał, SCHODZI Z PLANU.
        // Bez nawrotu znaczy to „zjazd do zajezdni" — bloki wolne, pojazd nie wraca.
        // `Drive` przy tym ZOSTAJE; dlaczego, stoi przy `LineTrain.LeftPlan`.
        foreach (var train in _trains)
        {
            if (train.Drive is not { Finished: true } || train.LeftPlan)
            {
                continue;
            }

            if (train.FinishedAtStep is null)
            {
                train.FinishedAtStep = Steps;
                continue;
            }

            if (_turnbackSteps > 0L)
            {
                continue;
            }

            _signalling.ReleaseTrain(train.Id);
            train.LeftPlan = true;
            train.Authority = null;
            train.Protection = null;
        }

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
                train.Protection = null;
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
    private bool EntryIsClear(double chainageM)
    {
        var plan = _signalling.Plan;
        var front = Math.Clamp(chainageM, plan.StartM, plan.EndM);
        var rear = Math.Clamp(chainageM - _trainLengthM, plan.StartM, plan.EndM);
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
