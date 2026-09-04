using System;
using System.Collections.Generic;
using System.Globalization;
using MetroBxl.Sim.Physics;
using MetroBxl.Sim.Train;

namespace MetroBxl.Sim.Signalling;

/// <summary>Co ochrona pociągu robi w tym kroku.</summary>
public enum ProtectionAction
{
    /// <summary>Nic — prędkość mieści się pod krzywą.</summary>
    None,

    /// <summary>Ingerencja hamulcem służbowym: prędkość ponad dopuszczalną, ale krzywa jeszcze wyrabia.</summary>
    ServiceIntervention,

    /// <summary>
    /// Ingerencja awaryjna: hamulec służbowy już nie zatrzyma składu przed końcem
    /// authority, albo authority jest wyczerpane, a skład wciąż jedzie.
    /// </summary>
    EmergencyIntervention,
}

/// <summary>
/// Wynik nadzoru w jednym kroku.
/// </summary>
/// <param name="PermittedSpeedMps">Prędkość dopuszczalna: mniejsza z limitu planu i krzywej do końca authority.</param>
/// <param name="AuthorityDistanceM">Odległość do końca authority.</param>
/// <param name="Action">Reakcja ochrony.</param>
/// <param name="BrakeDemandMps2">Opóźnienie, którego żąda ochrona; 0, gdy nie ingeruje.</param>
/// <param name="Overspeed">Czy prędkość przekracza dopuszczalną — to jest warunek ostrzeżenia.</param>
/// <param name="Reason">Powód reakcji, do zdarzenia i do raportu.</param>
public readonly record struct ProtectionDecision(
    double PermittedSpeedMps,
    double AuthorityDistanceM,
    ProtectionAction Action,
    double BrakeDemandMps2,
    bool Overspeed,
    string Reason)
{
    /// <summary>
    /// Żądanie ochrony przeliczone na położenie hamulca <see cref="MetroBxl.Sim.Train.DriverCommand"/>.
    ///
    /// <para>Ułamki powyżej 1,0 są obcinane, bo polecenie maszynisty kończy się na pełnym
    /// hamulcu służbowym. Hamowanie awaryjne jako **polecenie** nie istnieje w T-310/T-400
    /// i T-313 go nie dokłada — decyzja niesie żądane opóźnienie liczbą
    /// (<see cref="BrakeDemandMps2"/>), a to, że układ nie umie go podać, jest widoczne,
    /// a nie zamiecione.</para>
    /// </summary>
    public double BrakeCommandFraction(double serviceBrakeMps2)
    {
        if (!double.IsFinite(serviceBrakeMps2) || serviceBrakeMps2 <= 0.0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(serviceBrakeMps2), serviceBrakeMps2, "Opóźnienie hamulca służbowego musi być dodatnie.");
        }

        return Math.Clamp(BrakeDemandMps2 / serviceBrakeMps2, 0.0, 1.0);
    }

    /// <summary>
    /// Czy żądane opóźnienie PRZEKRACZA to, co hamulec służbowy potrafi podać.
    ///
    /// <para><b>Po co osobna własność.</b> <see cref="BrakeCommandFraction"/> obcina
    /// ułamek do 1,0, więc żądanie 2,0 m/s² i żądanie 1,1 m/s² dają ten sam nastawnik.
    /// Obcięcie samo w sobie jest poprawne — polecenie maszynisty kończy się na pełnym
    /// hamulcu służbowym — ale gdyby to była jedyna informacja, przekroczenie stałoby
    /// się niewidoczne. Ta własność je pokazuje, zamiast zamiatać.</para>
    /// </summary>
    /// <param name="serviceBrakeMps2">Opóźnienie pełnego hamulca służbowego.</param>
    public bool DemandExceedsServiceBrake(double serviceBrakeMps2)
    {
        if (!double.IsFinite(serviceBrakeMps2) || serviceBrakeMps2 <= 0.0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(serviceBrakeMps2), serviceBrakeMps2, "Opóźnienie hamulca służbowego musi być dodatnie.");
        }

        return BrakeDemandMps2 > serviceBrakeMps2;
    }

    /// <summary>
    /// Polecenie po INGERENCJI ochrony — decyzja właściciela z 04.09.2026:
    /// „ostrzeżenie, potem hamulec służbowy".
    ///
    /// <para><b>Trzy poziomy, dokładnie jak w <see cref="ProtectionAction"/>:</b></para>
    /// <list type="bullet">
    /// <item><see cref="ProtectionAction.None"/> — polecenie maszynisty przechodzi
    ///   BEZ ZMIANY. Samo przekroczenie prędkości bez ingerencji jest ostrzeżeniem
    ///   (<see cref="Overspeed"/>), nie hamowaniem: krzywa jeszcze wyrabia.</item>
    /// <item><see cref="ProtectionAction.ServiceIntervention"/> — nastawnik jazdy
    ///   zerowany, hamulec podniesiony do WIĘKSZEGO z dwóch: tego, co dał maszynista,
    ///   i tego, czego żąda ochrona. Ochrona nie ODPUSZCZA hamulca, który maszynista
    ///   już podał — to byłaby ingerencja w drugą stronę.</item>
    /// <item><see cref="ProtectionAction.EmergencyIntervention"/> — pełny hamulec.
    ///   <b>Hamowanie awaryjne jako POLECENIE nie istnieje</b> w T-310/T-400 i T-313
    ///   go nie dokłada, więc „awaryjne" znaczy tu pełny służbowy; czy to wystarczy,
    ///   mówi <see cref="DemandExceedsServiceBrake"/>, a nie milczenie.</item>
    /// </list>
    ///
    /// <para><b>Czego to NIE robi.</b> Nie liczy fizyki i nie zna prędkości — bierze
    /// gotową decyzję i przekłada ją na nastawniki. Druga formuła hamowania obok tej
    /// z T-311 dałaby dwa modele, które się rozjadą (zasada 4 z T-313).</para>
    /// </summary>
    /// <param name="requested">Polecenie maszynisty albo autopilota.</param>
    /// <param name="serviceBrakeMps2">Opóźnienie pełnego hamulca służbowego.</param>
    public DriverCommand Apply(DriverCommand requested, double serviceBrakeMps2) => Action switch
    {
        ProtectionAction.None => requested,
        ProtectionAction.ServiceIntervention => new DriverCommand(
            0.0, Math.Max(requested.Brake, BrakeCommandFraction(serviceBrakeMps2))),
        ProtectionAction.EmergencyIntervention => new DriverCommand(0.0, 1.0),
        _ => throw new ArgumentOutOfRangeException(nameof(Action), Action, "Nieznana reakcja ochrony."),
    };

    /// <inheritdoc/>
    public override string ToString() => string.Create(
        CultureInfo.InvariantCulture,
        $"v_dop = {Units.MpsToKmh(PermittedSpeedMps):F2} km/h na {AuthorityDistanceM:F2} m, " +
        $"{Action}{(Reason.Length == 0 ? string.Empty : $" ({Reason})")}");
}

/// <summary>Stan blokady drzwi.</summary>
/// <param name="Released">Czy wolno zwolnić drzwi.</param>
/// <param name="Reason">Dlaczego wolno albo nie wolno.</param>
public readonly record struct DoorInterlock(bool Released, string Reason);

/// <summary>
/// Funkcje KCV **wymienione wprost przez STIB** 02.07.2026 dla linii 2/6
/// (<c>data/signalling/ground-truth.json</c>: <c>kcv_confirmed_functions_lines_2_6</c>).
///
/// <para>To jest cała lista i nie wolno jej rozszerzać bez nowego źródła. Enum istnieje
/// po to, żeby wiadomo było, co jest funkcją potwierdzoną, a nie po to, żeby udawać
/// urządzenie: telegramy, balisy, częstotliwości i protokoły są poza zakresem T-313
/// i poza zakresem tego repozytorium.</para>
/// </summary>
public enum KcvFunction
{
    /// <summary>Zabezpieczenie automatycznego otwierania drzwi na stacji.</summary>
    SecureAutomaticDoorOpening,

    /// <summary>Wyzwalanie zapowiedzi stacyjnych w M7.</summary>
    StationAnnouncements,

    /// <summary>Włączanie smarowania obrzeży kół na części łuków.</summary>
    WheelLubrication,
}

/// <summary>
/// Ochrona pociągu (ATP) i interfejs KCV dla trybu <c>classic_2026</c>.
///
/// <para><b>Jedna krzywa hamowania, nie druga.</b> Zasada 4 z T-313: prędkość
/// dopuszczalną wyznacza <see cref="BrakingPointSolver"/> z T-311 — ten sam obiekt,
/// którym prowadzi się skład w <c>LineRun</c>. Ochrona nie ma własnego wzoru na drogę
/// hamowania i nie da się jej dać innego: solver wchodzi konstruktorem.</para>
///
/// <para><b>Dlaczego nie ma progów ostrzegania.</b> Bo nie ma dla nich źródła.
/// <c>unknown_parameters</c> wymienia „ATP/ATO braking curves and safety margins"
/// i „device reaction times". Zamiast wpisać wymyślony margines, model bierze dwa progi,
/// które **wynikają** z krzywej:</para>
/// <list type="number">
/// <item>prędkość przekracza dopuszczalną → ostrzeżenie i ingerencja hamulcem służbowym
///   (ground truth: obecny system „automatycznie spowalnia skład");</item>
/// <item>hamulec służbowy nie zatrzyma już składu przed końcem authority → ingerencja
///   awaryjna.</item>
/// </list>
/// <para>Oba progi są policzone, a nie przyjęte. Czas reakcji urządzenia wynosi zero
/// i to też jest świadome: zerowa zwłoka jest widoczna w kodzie, a zmyślone 0,4 s
/// wyglądałoby jak zmierzone.</para>
/// </summary>
public sealed class TrainProtection
{
    /// <summary>
    /// Liczba kroków bisekcji przy szukaniu prędkości dopuszczalnej. Stała z tego samego
    /// powodu co <see cref="BrakingPointSolver.BisectionSteps"/>: pętla „aż się zbiegnie"
    /// nie jest deterministyczna. 64 kroki wyczerpują mantysę <c>double</c> na przedziale
    /// prędkości rzędu 30 m/s.
    /// </summary>
    public const int PermittedSpeedBisectionSteps = 64;

    /// <summary>Poniżej tej prędkości skład jest uznany za stojący.</summary>
    public const double StandstillSpeedMps = 1e-6;

    private readonly SignallingPlan _plan;
    private readonly BrakingPointSolver _solver;
    private readonly double _serviceBrakeMps2;
    private readonly double _emergencyBrakeMps2;
    private readonly Dictionary<string, ProtectionAction> _lastAction = new(StringComparer.Ordinal);
    private readonly Dictionary<string, bool> _lastDoorRelease = new(StringComparer.Ordinal);

    /// <summary>Ochrona zbudowana z planu i modelu pojazdu.</summary>
    public TrainProtection(SignallingPlan plan, VehicleModel model)
        : this(
            plan,
            new BrakingPointSolver(model ?? throw new ArgumentNullException(nameof(model))),
            model.DesignServiceBrakeMps2,
            model.DesignEmergencyBrakeMps2)
    {
    }

    /// <summary>Ochrona ze złożonych osobno składników.</summary>
    /// <param name="plan">Plan bloków — daje limit prędkości i wariant ochrony.</param>
    /// <param name="solver">Solver hamowania z T-311. Ten sam, którym jedzie skład.</param>
    /// <param name="serviceBrakeMps2">Opóźnienie hamulca służbowego.</param>
    /// <param name="emergencyBrakeMps2">Opóźnienie hamulca awaryjnego.</param>
    public TrainProtection(
        SignallingPlan plan, BrakingPointSolver solver, double serviceBrakeMps2, double emergencyBrakeMps2)
    {
        ArgumentNullException.ThrowIfNull(plan);
        ArgumentNullException.ThrowIfNull(solver);
        if (!double.IsFinite(serviceBrakeMps2) || serviceBrakeMps2 <= 0.0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(serviceBrakeMps2), serviceBrakeMps2, "Opóźnienie hamulca służbowego musi być dodatnie.");
        }

        if (!double.IsFinite(emergencyBrakeMps2) || emergencyBrakeMps2 < serviceBrakeMps2)
        {
            throw new ArgumentOutOfRangeException(
                nameof(emergencyBrakeMps2), emergencyBrakeMps2,
                "Hamulec awaryjny nie może być słabszy od służbowego.");
        }

        _plan = plan;
        _solver = solver;
        _serviceBrakeMps2 = serviceBrakeMps2;
        _emergencyBrakeMps2 = emergencyBrakeMps2;
    }

    /// <summary>Plan, z którego ochrona bierze limit prędkości i wariant.</summary>
    public SignallingPlan Plan => _plan;

    /// <summary>Solver hamowania — ten sam obiekt, którym prowadzi się skład.</summary>
    public BrakingPointSolver Solver => _solver;

    /// <summary>Opóźnienie hamulca służbowego użyte przez krzywą.</summary>
    public double ServiceBrakeMps2 => _serviceBrakeMps2;

    /// <summary>Opóźnienie hamulca awaryjnego.</summary>
    public double EmergencyBrakeMps2 => _emergencyBrakeMps2;

    /// <summary>
    /// Największa prędkość, z której da się jeszcze zatrzymać na zadanej odległości
    /// hamulcem służbowym, przy krzywej z T-311 (czyli z ograniczeniem zrywu).
    ///
    /// <para>Bisekcja, a nie wzór zamknięty, bo <c>s(v)</c> z T-311 składa się z dwóch
    /// gałęzi — z narastaniem hamulca i samym narastaniem — i odwrócenie go analitycznie
    /// dałoby wzór, którego nie da się sprawdzić ręcznie. Obie gałęzie są rosnące
    /// względem <c>v</c>, więc bisekcja jest jednoznaczna.</para>
    /// </summary>
    public double PermittedSpeedMps(double authorityDistanceM)
    {
        if (!double.IsFinite(authorityDistanceM) || authorityDistanceM < 0.0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(authorityDistanceM), authorityDistanceM, "Odległość do końca authority musi być nieujemna.");
        }

        if (authorityDistanceM <= 0.0)
        {
            return 0.0;
        }

        var ceiling = _plan.PermittedSpeedMps;
        if (BrakingDistanceM(ceiling) <= authorityDistanceM)
        {
            return ceiling;
        }

        var low = 0.0;
        var high = ceiling;
        for (var i = 0; i < PermittedSpeedBisectionSteps; i++)
        {
            var mid = 0.5 * (low + high);
            if (mid <= low || mid >= high)
            {
                break;
            }

            if (BrakingDistanceM(mid) > authorityDistanceM)
            {
                high = mid;
            }
            else
            {
                low = mid;
            }
        }

        return low;
    }

    /// <summary>Droga hamowania do zatrzymania z zadanej prędkości, hamulcem służbowym.</summary>
    public double BrakingDistanceM(double speedMps) =>
        speedMps <= 0.0 ? 0.0 : _solver.Solve(speedMps, 0.0, _serviceBrakeMps2).DistanceM;

    /// <summary>
    /// Nadzór w jednym kroku. Zdarzenia trafiają do strumienia
    /// <paramref name="system"/> i powstają **na przejściu**, a nie w każdym kroku:
    /// przy 120 Hz ostrzeżenie emitowane co krok zalałoby zapis i przestałoby cokolwiek
    /// znaczyć.
    /// </summary>
    /// <param name="system">System blokowy — źródło movement authority.</param>
    /// <param name="trainId">Skład.</param>
    /// <param name="speedMps">Prędkość składu w tym kroku.</param>
    public ProtectionDecision Supervise(FixedBlockSystem system, string trainId, double speedMps)
    {
        ArgumentNullException.ThrowIfNull(system);
        if (!double.IsFinite(speedMps) || speedMps < 0.0)
        {
            throw new ArgumentOutOfRangeException(nameof(speedMps), speedMps, "Prędkość musi być nieujemna i skończona.");
        }

        var authority = system.Authority(trainId);
        var distance = authority.DistanceM;
        var permitted = PermittedSpeedMps(distance);

        ProtectionAction action;
        double demand;
        string reason;

        if (speedMps <= StandstillSpeedMps)
        {
            action = ProtectionAction.None;
            demand = 0.0;
            reason = string.Empty;
        }
        else if (distance <= 0.0)
        {
            action = ProtectionAction.EmergencyIntervention;
            demand = _emergencyBrakeMps2;
            reason = "authority-exhausted:" + authority.Reason;
        }
        else if (speedMps > permitted)
        {
            if (_solver.TryRequiredDeceleration(speedMps, 0.0, distance, out var need) &&
                need.DecelerationMps2 <= _serviceBrakeMps2)
            {
                action = ProtectionAction.ServiceIntervention;
                demand = need.DecelerationMps2;
                reason = "overspeed:" + authority.Reason;
            }
            else
            {
                action = ProtectionAction.EmergencyIntervention;
                demand = _emergencyBrakeMps2;
                reason = "service-brake-insufficient:" + authority.Reason;
            }
        }
        else
        {
            action = ProtectionAction.None;
            demand = 0.0;
            reason = string.Empty;
        }

        var overspeed = speedMps > permitted && speedMps > StandstillSpeedMps;
        if (!_lastAction.TryGetValue(trainId, out var previous) || previous != action)
        {
            _lastAction[trainId] = action;
            switch (action)
            {
                case ProtectionAction.ServiceIntervention:
                    system.Report(SignallingEventKind.OverspeedWarning, authority.LimitBlockId, trainId,
                        authority.FrontChainageM, Detail(speedMps, permitted));
                    system.Report(SignallingEventKind.OverspeedIntervention, authority.LimitBlockId, trainId,
                        authority.FrontChainageM, reason);
                    break;
                case ProtectionAction.EmergencyIntervention:
                    if (overspeed)
                    {
                        system.Report(SignallingEventKind.OverspeedWarning, authority.LimitBlockId, trainId,
                            authority.FrontChainageM, Detail(speedMps, permitted));
                    }

                    system.Report(SignallingEventKind.EmergencyIntervention, authority.LimitBlockId, trainId,
                        authority.FrontChainageM, reason);
                    break;
                default:
                    break;
            }
        }

        return new ProtectionDecision(permitted, distance, action, demand, overspeed, reason);
    }

    /// <summary>
    /// Blokada drzwi jako **interfejs**, nie jako urządzenie.
    ///
    /// <para>Warunki są trzy i wszystkie wynikają z rzeczy, które repo już ma: skład stoi
    /// (T-312: drzwi otwierają się po zatrzymaniu, nie po dojechaniu), czoło jest w bloku
    /// peronowym, a w wariancie linii 2/6 dochodzi potwierdzenie z KCV — bo dokładnie tę
    /// funkcję STIB wymienia jako KCV-ową: „zabezpieczenie automatycznego otwierania
    /// drzwi na stacji".</para>
    ///
    /// <para>Na planie z wariantem <see cref="ProtectionVariant.LegacyFixedBlock"/>
    /// argument <paramref name="kcvAvailable"/> jest **ignorowany**, i to jest celowe:
    /// KCV jest potwierdzony przez STIB dla linii 2/6, a pakiet A jest na linii 1.
    /// Dopisanie mu KCV byłoby wymyśleniem faktu o sieci.</para>
    /// </summary>
    public DoorInterlock DoorRelease(FixedBlockSystem system, string trainId, double speedMps, bool kcvAvailable)
    {
        ArgumentNullException.ThrowIfNull(system);
        var front = system.FrontOf(trainId);
        var block = _plan.BlockAt(front);

        DoorInterlock interlock;
        if (speedMps > StandstillSpeedMps)
        {
            interlock = new DoorInterlock(false, "moving");
        }
        else if (!block.IsPlatform)
        {
            interlock = new DoorInterlock(false, "not-at-platform:" + block.Id);
        }
        else if (_plan.Variant == ProtectionVariant.LegacyWithKcv && !kcvAvailable)
        {
            interlock = new DoorInterlock(false, "kcv-unavailable");
        }
        else
        {
            interlock = new DoorInterlock(true, block.Id);
        }

        if (!_lastDoorRelease.TryGetValue(trainId, out var previous) || previous != interlock.Released)
        {
            _lastDoorRelease[trainId] = interlock.Released;
            system.Report(
                interlock.Released ? SignallingEventKind.DoorRelease : SignallingEventKind.DoorInhibit,
                block.Id, trainId, front, interlock.Reason);
        }

        return interlock;
    }

    /// <summary>
    /// Funkcje KCV potwierdzone źródłem, w kolejności, w jakiej wymienia je STIB.
    /// Lista jest zamknięta.
    /// </summary>
    public static IReadOnlyList<KcvFunction> SourceBackedKcvFunctions { get; } = new[]
    {
        KcvFunction.SecureAutomaticDoorOpening,
        KcvFunction.StationAnnouncements,
        KcvFunction.WheelLubrication,
    };

    /// <summary>
    /// Czy plan w ogóle ma prawo korzystać z KCV. Odmowa jest wyjątkiem, bo zapytanie
    /// o KCV na linii 1 nie jest sytuacją ruchową — jest błędem w danych scenariusza.
    /// </summary>
    public void RequireKcv()
    {
        if (_plan.Variant != ProtectionVariant.LegacyWithKcv)
        {
            throw new InvalidOperationException(
                $"plan {_plan.PlanId} ma wariant {_plan.Variant}; KCV jest potwierdzony przez STIB " +
                "wyłącznie dla linii 2/6 (kcv_lines_2_6) i nie wolno go przypisywać innym liniom");
        }
    }

    /// <inheritdoc/>
    public override string ToString() => string.Create(
        CultureInfo.InvariantCulture,
        $"ATP {_plan.PlanId}: limit {Units.MpsToKmh(_plan.PermittedSpeedMps):F1} km/h, " +
        $"hamulec {_serviceBrakeMps2:F2}/{_emergencyBrakeMps2:F2} m/s², {_plan.Variant}");

    private static string Detail(double speedMps, double permittedMps) => string.Create(
        CultureInfo.InvariantCulture,
        $"v={Units.MpsToKmh(speedMps):F2};v_dop={Units.MpsToKmh(permittedMps):F2}");
}
