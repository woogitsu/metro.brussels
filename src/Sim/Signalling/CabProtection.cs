using System;
using MetroBxl.Sim.Physics;
using MetroBxl.Sim.Train;

namespace MetroBxl.Sim.Signalling;

/// <summary>
/// Jeden skład prowadzony PRZEZ CZŁOWIEKA, postawiony pod planem sygnalizacji:
/// bloki, nastawnia, autorytet jazdy i ochrona pociągu, która naprawdę ingeruje.
///
/// <para><b>Po co to istnieje, skoro jest <see cref="Line.LineCore"/>.</b> Bo do
/// 05.09.2026 tryb ręczny i tryb z sygnalizacją były w tej grze ROZŁĄCZNE: jedyny
/// tryb, w którym prowadzi człowiek, był jedynym, w którym nie ma ani blokad, ani
/// ochrony pociągu (<c>reports/droga-do-grywalnosci.md</c> §1.3). Rdzeń miał wszystko
/// — <see cref="TrainProtection.Supervise"/>, <see cref="ProtectionDecision.Apply"/>
/// i hak <see cref="Train.LineDrive.Supervisor"/> — brakowało wyłącznie miejsca, w
/// którym te trzy rzeczy spotykają się z poleceniem od klawiatury.</para>
///
/// <para><b>Dlaczego to NIE jest <see cref="Line.LineCore"/> z podstawionym
/// człowiekiem.</b> Bo <see cref="Train.LineDrive"/> uznaje zatrzymanie za wywołanie
/// stacji przy <c>chainage &gt;= cel − okno</c>, BEZ ograniczenia z góry. Dla
/// autopilota, który staje z błędem 0,31 m, ten warunek nigdy nie wychodzi poza peron;
/// dla człowieka wychodzi natychmiast — skład zatrzymany 200 m za stacją spełniałby go
/// tak samo dobrze i otworzyłby drzwi w tunelu
/// (<c>reports/droga-do-grywalnosci.md</c> §5.3). Regułę stacji dla kabiny ma
/// <see cref="Train.StationService"/> i to ona zostaje; ta klasa nie wie o stacjach
/// NIC i celowo nie ma jak się z tamtą rozjechać.</para>
///
/// <para><b>Czego ta klasa nie robi.</b> Nie liczy ani jednej siły, nie zna kroku
/// symulacji i nie podaje ani jednego nastawnika z siebie. Bierze gotową decyzję
/// z <see cref="TrainProtection"/> i przekłada ją na polecenie przez
/// <see cref="ProtectionDecision.Apply"/> — druga formuła hamowania obok tej z T-311
/// dałaby dwa modele, które się rozjadą (zasada 4 z T-313). Nie podaje też składowi
/// końca autorytetu jako celu hamowania, tak jak robi to <see cref="Line.LineCore"/>
/// przez <see cref="Train.LineDrive.AuthorityEndM"/>: w kabinie punkt hamowania wybiera
/// CZŁOWIEK, a ochrona jest od tego, żeby jego wybór pilnować, a nie zastępować.</para>
///
/// <para><b>Kolejność w kroku jest ta sama, co w <see cref="Line.LineCore.Step"/>,
/// i to jest warunek, a nie kosmetyka:</b> nastawnia (<see cref="Supervise"/>, faza 1b),
/// odczyt autorytetu i nadzór ze stanu SPRZED kroku (<see cref="Supervise"/>, faza 2),
/// filtr polecenia (<see cref="Apply"/>, faza 3), meldunek ruchu po kroku
/// (<see cref="Move"/>). Wołający wykonuje je w tej kolejności i nic tego za niego nie
/// zrobi — ale dwie pierwsze fazy siedzą w jednym wywołaniu właśnie po to, żeby nie dało
/// się ich rozdzielić ani zamienić miejscami.</para>
///
/// <para><b><see cref="Apply"/> jest OSTATNIM filtrem polecenia.</b> Issue #26:
/// „nie można ominąć ATP przez input gracza". Polecenie idzie
/// <c>DriverNotch → StationService.Filter → CabProtection.Apply → TrainController</c>;
/// gdyby ochrona stała przed filtrem stacji, blokada trakcji na czas cyklu drzwi
/// nadpisywałaby jej hamulec, a gdyby stała przed nastawnikiem — nadpisywałby ją
/// człowiek. Ostatni filtr jest jedynym, którego nie da się obejść z żadnej strony.</para>
/// </summary>
public sealed class CabProtection
{
    private readonly SignallingPlan _plan;
    private readonly VehicleModel _model;
    private readonly string _trainId;
    private readonly double _startChainageM;
    private readonly double _trainLengthM;
    private readonly long _requestIntervalSteps;

    private FixedBlockSystem _signalling = null!;
    private RouteDispatcher _dispatcher = null!;
    private TrainProtection _protection = null!;

    /// <summary>
    /// Skład zarejestrowany na planie, gotowy na pierwsze wołanie <see cref="Supervise"/>.
    /// </summary>
    /// <param name="plan">Plan bloków i tras; z niego bierze się prędkość dopuszczalna i wariant ochrony.</param>
    /// <param name="model">Model pojazdu — stąd krzywa hamowania i opóźnienia obu hamulców.</param>
    /// <param name="trainId">Identyfikator składu w sygnalizacji; ten sam po stronie sceny i rdzenia.</param>
    /// <param name="startChainageM">Kilometraż czoła na starcie przejazdu.</param>
    /// <param name="trainLengthM">Długość składu; z rejestru pojazdu, nie z powietrza.</param>
    /// <param name="requestIntervalSteps">Odstęp żądań trasy, w krokach; domyślnie jedna sekunda.</param>
    public CabProtection(
        SignallingPlan plan,
        VehicleModel model,
        string trainId,
        double startChainageM,
        double trainLengthM,
        long requestIntervalSteps = RouteDispatcher.DefaultRequestIntervalSteps)
    {
        ArgumentNullException.ThrowIfNull(plan);
        ArgumentNullException.ThrowIfNull(model);
        ArgumentNullException.ThrowIfNull(trainId);
        if (trainId.Length == 0)
        {
            throw new ArgumentException("Identyfikator składu nie może być pusty.", nameof(trainId));
        }

        if (!double.IsFinite(startChainageM))
        {
            throw new ArgumentOutOfRangeException(
                nameof(startChainageM), startChainageM, "Kilometraż startu musi być skończony.");
        }

        if (!double.IsFinite(trainLengthM) || trainLengthM <= 0.0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(trainLengthM), trainLengthM, "Długość składu musi być dodatnia i skończona.");
        }

        _plan = plan;
        _model = model;
        _trainId = trainId;
        _startChainageM = startChainageM;
        _trainLengthM = trainLengthM;
        _requestIntervalSteps = requestIntervalSteps;
        StartFromScratch();
    }

    /// <summary>
    /// Kabina M7 pod zadanym planem. Długość składu pochodzi z rejestru pojazdu
    /// (<c>parameters.length_m</c>, status <c>spec</c>) — tak samo jak w
    /// <see cref="Line.LineCore"/>, żeby liczba miała jedno źródło, a nie dwa zgodne
    /// przez przypadek.
    /// </summary>
    /// <param name="plan">Plan bloków i tras dla osi, po której idzie przejazd.</param>
    /// <param name="trainId">Identyfikator składu w sygnalizacji.</param>
    /// <param name="startChainageM">Kilometraż czoła na starcie przejazdu.</param>
    /// <returns>Kabina gotowa na pierwszy krok.</returns>
    public static CabProtection M7(SignallingPlan plan, string trainId, double startChainageM) =>
        new(plan, VehicleModel.M7, trainId, startChainageM,
            VehicleRegistry.M7.RequireValue("parameters.length_m", ParameterStatus.Spec));

    /// <summary>Plan, pod którym jedzie ta kabina.</summary>
    public SignallingPlan Plan => _plan;

    /// <summary>Sygnalizacja tego przejazdu — do odczytu zajętości, zdarzeń i odcisku stanu.</summary>
    public FixedBlockSystem Signalling => _signalling;

    /// <summary>Nastawnia automatyczna — do odczytu licznika zaryglowanych tras i odmów.</summary>
    public RouteDispatcher Dispatcher => _dispatcher;

    /// <summary>Ochrona pociągu — do odczytu opóźnień hamulców, którymi naprawdę liczy.</summary>
    public TrainProtection Protection => _protection;

    /// <summary>Identyfikator składu w sygnalizacji.</summary>
    public string TrainId => _trainId;

    /// <summary>Kilometraż czoła na starcie przejazdu; tu wraca skład po <see cref="Reset"/>.</summary>
    public double StartChainageM => _startChainageM;

    /// <summary>Długość składu użyta do zajmowania bloków.</summary>
    public double TrainLengthM => _trainLengthM;

    /// <summary>
    /// Autorytet jazdy odczytany w ostatnim <see cref="Supervise"/>; <c>null</c> przed
    /// pierwszym krokiem.
    /// </summary>
    public MovementAuthority? Authority { get; private set; }

    /// <summary>
    /// Decyzja ochrony z ostatniego <see cref="Supervise"/>; <c>null</c> przed pierwszym
    /// krokiem.
    ///
    /// <para>HUD ma czytać TĘ decyzję, a nie wołać <see cref="TrainProtection.Supervise"/>
    /// drugi raz „do pokazania". Drugie wołanie liczyłoby ją z innego stanu — widok chodzi
    /// w klatkach, rdzeń w krokach — i emitowałoby zdarzenia sygnalizacji z widoku.</para>
    /// </summary>
    public ProtectionDecision? Decision { get; private set; }

    /// <summary>
    /// Kroki, w których prędkość przekraczała dopuszczalną — czyli OSTRZEŻENIA.
    ///
    /// Licznik jest po krokach, nie po zdarzeniach: zdarzenia powstają na przejściu,
    /// więc jedno przekroczenie trwające dziesięć sekund daje jedno zdarzenie i 1200
    /// kroków. Do pomiaru „ile przejazdu spędzono nad limitem" potrzebna jest ta druga
    /// liczba.
    /// </summary>
    public long Warnings { get; private set; }

    /// <summary>Kroki z ingerencją hamulcem służbowym.</summary>
    public long ServiceInterventions { get; private set; }

    /// <summary>Kroki z ingerencją awaryjną.</summary>
    public long EmergencyInterventions { get; private set; }

    /// <summary>Największe opóźnienie, jakiego ochrona zażądała w tym przejeździe.</summary>
    public double MaxBrakeDemandMps2 { get; private set; }

    /// <summary>
    /// Nastawnia i nadzór PRZED krokiem: żądanie trasy, odczyt autorytetu i decyzja
    /// ochrony policzona ze stanu sprzed kroku.
    ///
    /// <para>Kolejność „żądanie trasy przed odczytem autorytetu" jest treścią, nie
    /// kosmetyką — ta sama, co w fazach 1b i 2 <see cref="Line.LineCore.Step"/>:
    /// <see cref="FixedBlockSystem.RequestRoute"/> publikuje autorytety w środku, więc
    /// trasa zaryglowana teraz jest widoczna w autorytecie odczytanym za chwilę i skład
    /// może ruszyć w TYM kroku, a nie w następnym.</para>
    /// </summary>
    /// <param name="steps">Numer kroku, który zaraz się wykona; z niego liczy się odstęp żądań trasy.</param>
    /// <param name="chainageM">Kilometraż czoła przed krokiem.</param>
    /// <param name="speedMps">Prędkość składu przed krokiem.</param>
    /// <returns>Decyzja ochrony dla tego kroku.</returns>
    public ProtectionDecision Supervise(long steps, double chainageM, double speedMps)
    {
        _dispatcher.Dispatch(_signalling, _trainId, chainageM, steps);

        var authority = _signalling.Authority(_trainId);
        Authority = authority;

        var decision = _protection.Supervise(_signalling, _trainId, speedMps);
        Decision = decision;

        if (decision.Overspeed)
        {
            Warnings++;
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

        return decision;
    }

    /// <summary>
    /// Polecenie po ingerencji ochrony. Przed pierwszym <see cref="Supervise"/> — czyli
    /// gdy decyzji jeszcze nie ma — polecenie przechodzi BEZ ZMIANY: ochrona bez odczytu
    /// autorytetu nie ma czego pilnować, a zgadywanie hamulca byłoby wymyśleniem stanu
    /// sygnalizacji.
    /// </summary>
    /// <param name="requested">Polecenie maszynisty po filtrze stacji.</param>
    /// <returns>Polecenie, które wolno podać kontrolerowi.</returns>
    public DriverCommand Apply(DriverCommand requested) =>
        Decision is ProtectionDecision decision
            ? decision.Apply(requested, _protection.ServiceBrakeMps2)
            : requested;

    /// <summary>
    /// Meldunek ruchu PO kroku: nowy kilometraż czoła idzie do sygnalizacji, która zajmuje
    /// bloki po drodze, zwalnia te za tyłem i zwalnia trasę, gdy zrobiła swoje.
    ///
    /// <para>Wołane po kroku, a nie przed — tak samo jak faza 3
    /// <see cref="Line.LineCore.Step"/>. Meldunek przed krokiem opisywałby położenie,
    /// z którego skład właśnie odjechał.</para>
    /// </summary>
    /// <param name="chainageM">Kilometraż czoła po kroku.</param>
    public void Move(double chainageM) => _signalling.MoveTrain(_trainId, chainageM);

    /// <summary>
    /// Zeruje sygnalizację tego przejazdu do stanu z chwili utworzenia: skład wraca na
    /// <see cref="StartChainageM"/>, bloki, trasy i liczniki są puste, a strumień zdarzeń
    /// zaczyna się od nowa.
    ///
    /// <para><b>Bez tego reset przejazdu (klawisz <c>R</c>) byłby WYJĄTKIEM, a nie
    /// resetem.</b> <see cref="FixedBlockSystem.MoveTrain"/> odmawia cofnięcia czoła —
    /// model nie odtacza składów w tył — więc pierwszy meldunek ruchu po resecie
    /// próbowałby przesunąć skład z miejsca, do którego dojechał, na 94,0 m i skończyłby
    /// się <see cref="ArgumentOutOfRangeException"/> w środku pętli klatek.</para>
    ///
    /// <para><b>Dlaczego cała trójka powstaje od nowa, a nie tylko skład.</b> Bo stan po
    /// resecie nie ma jak różnić się od stanu po utworzeniu tylko wtedy, gdy powstaje tą
    /// samą drogą — ta sama zasada i ten sam prywatny <c>StartFromScratch</c>, co
    /// w <see cref="Train.StationService.Reset"/>. <see cref="TrainProtection"/> trzyma
    /// u siebie ostatnią reakcję i ostatnią blokadę drzwi po to, żeby zdarzenia powstawały
    /// NA PRZEJŚCIU; zostawiona po resecie pamięć zjadłaby pierwsze zdarzenie nowego
    /// przejazdu i nie byłoby po niej śladu.</para>
    /// </summary>
    public void Reset() => StartFromScratch();

    /// <summary>
    /// Stan początkowy sygnalizacji kabiny. JEDNO miejsce dla konstruktora i dla
    /// <see cref="Reset"/> — uzasadnienie przy <see cref="Reset"/>.
    /// </summary>
    private void StartFromScratch()
    {
        _signalling = new FixedBlockSystem(_plan);
        _dispatcher = new RouteDispatcher(_plan, _requestIntervalSteps);
        _protection = new TrainProtection(_plan, _model);
        _signalling.RegisterTrain(_trainId, _startChainageM, _trainLengthM);

        Authority = null;
        Decision = null;
        Warnings = 0L;
        ServiceInterventions = 0L;
        EmergencyInterventions = 0L;
        MaxBrakeDemandMps2 = 0.0;
    }

    /// <inheritdoc/>
    public override string ToString() => string.Create(
        System.Globalization.CultureInfo.InvariantCulture,
        $"kabina {_trainId} pod {_plan.PlanId}: limit {Units.MpsToKmh(_plan.PermittedSpeedMps):F2} km/h, "
        + $"ostrzeżeń {Warnings}, ingerencji {ServiceInterventions}+{EmergencyInterventions}, "
        + $"max żądanie {MaxBrakeDemandMps2:F3} m/s²");
}
