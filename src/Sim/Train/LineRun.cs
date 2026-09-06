using System;
using System.Collections.Generic;
using System.Globalization;
using MetroBxl.Sim.Line;
using MetroBxl.Sim.Physics;

namespace MetroBxl.Sim.Train;

/// <summary>Jedno zatrzymanie: kiedy skład stanął, gdzie i jak długo jechał od poprzedniego.</summary>
/// <param name="Name">Nazwa stacji z osi.</param>
/// <param name="StopId">Identyfikator peronu z GTFS — klucz do zestawienia z rozkładem.</param>
/// <param name="ChainageM">Chainage stacji z <c>data/track/*.json</c>.</param>
/// <param name="StoppedAtChainageM">Chainage, na którym skład faktycznie stanął.</param>
/// <param name="StopErrorM">Błąd zatrzymania; dodatni = przejechał stację.</param>
/// <param name="ArrivalSeconds">Czas zatrzymania od początku przejazdu.</param>
/// <param name="DepartureSeconds">Czas ruszenia; różnica to pełny cykl drzwi.</param>
/// <param name="RunSecondsFromPrevious">Czas jazdy od ruszenia z poprzedniej stacji.</param>
/// <param name="DistanceFromPreviousM">Droga od poprzedniej stacji.</param>
/// <param name="TopSpeedMps">Najwyższa prędkość osiągnięta na tym odcinku.</param>
public readonly record struct StationCall(
    string Name,
    string StopId,
    double ChainageM,
    double StoppedAtChainageM,
    double StopErrorM,
    double ArrivalSeconds,
    double DepartureSeconds,
    double RunSecondsFromPrevious,
    double DistanceFromPreviousM,
    double TopSpeedMps)
{
    /// <summary>Jedna linia raportu; kultura niezmienna, żeby wyjście nie zależało od maszyny.</summary>
    public override string ToString() => string.Create(
        CultureInfo.InvariantCulture,
        $"{Name}: przyjazd {ArrivalSeconds:F2} s na {StoppedAtChainageM:F2} m " +
        $"(błąd {StopErrorM:+0.000;-0.000;0.000} m), jazda {RunSecondsFromPrevious:F2} s " +
        $"na {DistanceFromPreviousM:F2} m, szczyt {Units.MpsToKmh(TopSpeedMps):F2} km/h");
}

/// <summary>Wynik przejazdu z zatrzymaniami.</summary>
/// <param name="AxisId">Identyfikator osi.</param>
/// <param name="Calls">Zatrzymania w kolejności chainage.</param>
/// <param name="TotalSeconds">Czas od ruszenia z pierwszej stacji do zatrzymania na ostatniej.</param>
/// <param name="TotalDistanceM">Droga przebyta między pierwszą a ostatnią stacją.</param>
/// <param name="DwellSeconds">Suma postojów na stacjach pośrednich.</param>
/// <param name="Steps">Liczba kroków symulacji.</param>
/// <param name="FinishReason">Dlaczego pętla się skończyła.</param>
/// <param name="Energy">Bilans energii CAŁEGO przejazdu — patrz <see cref="TripEnergyAccount"/>.</param>
public readonly record struct LineRunResult(
    string AxisId,
    IReadOnlyList<StationCall> Calls,
    double TotalSeconds,
    double TotalDistanceM,
    double DwellSeconds,
    long Steps,
    string FinishReason,
    TripEnergyAccount Energy);

/// <summary>
/// Bilans energii CAŁEGO przejazdu z zatrzymaniami — druga, niezależna droga do tej
/// samej liczby, na wzór <see cref="Physics.EnergyAccount"/> (T-310) i
/// <see cref="Physics.BrakingEnergyAccount"/> (T-311), ale scalona na jeden przejazd,
/// który miesza rozruch, wybieg, hamowanie **i** postój na każdej stacji pośredniej.
///
/// <para><b>Dlaczego to osobny typ, a nie jeden z tamtych dwóch.</b>
/// <see cref="Physics.EnergyAccount"/> zna tylko trakcję (T-310: sam rozruch),
/// a <see cref="Physics.BrakingEnergyAccount"/> zna tylko hamulec (T-311: samo
/// hamowanie). Przejazd liniowy robi oba na przemian w jednej pętli — dopisanie pracy
/// hamulca do <see cref="Physics.EnergyAccount"/> zmieniłoby znaczenie pola, które
/// T-310 już opisał i przypiął testem, a rozdzielenie na dwa osobne bilanse dla jednego
/// przejazdu policzyłoby energię kinetyczną między stacjami dwa razy.</para>
///
/// <para><b>Wyprowadzenie równania kroku</b> jest tym samym rachunkiem co w obu
/// tamtych typach, tylko z dodatkowym członem hamulca w sile wypadkowej:
/// <c>a = (F_trakcji − F_oporu − F_pochylenia)/m_ef − b_hamulca</c>. Per krok:</para>
///
/// <code>
/// F_netto_wszystko · przebyta = ΔE_kin + dyskretyzacja + obcięcie
/// </code>
///
/// <para>gdzie <c>F_netto_wszystko = (trakcja − opory − pochylenie) − m_ef·b_hamulca</c>
/// i <c>ΔE_kin</c> jest zmianą energii kinetycznej W TYM kroku — dokładnie ta sama
/// tożsamość, którą <see cref="Physics.AccelerationRun"/> wyprowadza dla samej trakcji.
/// Zsumowana po WSZYSTKICH krokach przejazdu (rozruch, wybieg, hamowanie, postój)
/// teleskopuje do <see cref="ResidualJ"/> poniżej.</para>
/// </summary>
/// <param name="TractionWorkJ">Praca siły pociągowej, sumowana po całym przejeździe.</param>
/// <param name="ResistanceWorkJ">Praca oporów ruchu; zawsze dodatnia.</param>
/// <param name="GradeWorkJ">Praca przeciw ciężarowi; ujemna przy jeździe z góry.</param>
/// <param name="BrakeWorkJ">
/// Praca hamulca — mechaniczna, na obwodzie kół. Tak jak w
/// <see cref="Physics.BrakingEnergyAccount"/>: **cała** praca hamulca, bez podziału na
/// odzysk i straty, bo karta M7 potwierdza sam fakt hamowania odzyskowego i nic więcej.
/// </param>
/// <param name="KineticEnergyDeltaJ">
/// Zmiana energii kinetycznej masy efektywnej: koniec minus początek przejazdu. Skład
/// zaczyna i kończy przejazd w spoczynku, więc przy przejeździe zakończonym „arrived"
/// ta wartość jest zerem — a nie zerem z definicji typu, tylko zmierzonym zerem.
/// </param>
/// <param name="DiscretizationWorkJ">Człon schematu <c>½·m_ef·Σ(Δv)²</c>, sumowany po całym przejeździe.</param>
/// <param name="ClampedWorkJ">
/// Praca odrzucona przez obcięcia modelu: obcięcie prędkości do zera i do limitu.
/// Artefakt schematu całkowania, nie fizyka — patrz <see cref="Physics.EnergyAccount"/>.
/// </param>
public readonly record struct TripEnergyAccount(
    double TractionWorkJ,
    double ResistanceWorkJ,
    double GradeWorkJ,
    double BrakeWorkJ,
    double KineticEnergyDeltaJ,
    double DiscretizationWorkJ,
    double ClampedWorkJ)
{
    /// <summary>Domknięcie bilansu. Zero oznacza, że rachunek sił i całkowanie mówią to samo.</summary>
    public double ResidualJ =>
        TractionWorkJ - ResistanceWorkJ - GradeWorkJ - BrakeWorkJ
        - KineticEnergyDeltaJ - DiscretizationWorkJ - ClampedWorkJ;

    /// <summary>
    /// Domknięcie odniesione do przepływu energii w obie strony — trakcji I hamulca
    /// razem, a nie do samej trakcji. Przejazd złożony wyłącznie z hamowania (autorytet
    /// ucięty tuż za startem) miałby TractionWorkJ bliskie zeru i odniesienie do niego
    /// dzieliłoby przez prawie zero; suma obu prac nie ma tej wady.
    /// </summary>
    public double RelativeResidual
    {
        get
        {
            var scale = Math.Abs(TractionWorkJ) + Math.Abs(BrakeWorkJ);
            return scale == 0.0 ? 0.0 : Math.Abs(ResidualJ) / scale;
        }
    }

    /// <summary>Praca trakcji w kWh — energia pobrana z sieci, licząc na obwodzie kół i bez sprawności.</summary>
    public double TractionWorkKwh => TractionWorkJ / 3_600_000.0;

    /// <summary>Praca hamulca w kWh — mechaniczna, przed jakimkolwiek podziałem na odzysk.</summary>
    public double BrakeWorkKwh => BrakeWorkJ / 3_600_000.0;

    /// <summary>
    /// Energia netto pobrana z sieci przy zadanym WARIANCIE SKRAJNYM odzysku hamowania:
    /// <c>false</c> = 0 % (cały hamulec grzeje opory, nic nie wraca do sieci),
    /// <c>true</c> = 100 % (cała praca mechaniczna hamulca wraca do sieci). Żadna wartość
    /// pośrednia nie jest tu dostępna świadomie — karta M7 nie podaje sprawności odzysku,
    /// więc liczba między 0 a 100 % byłaby zmyśloną liczbą o taborze (`CLAUDE.md` §1 i §8).
    /// </summary>
    public double NetGridWorkKwh(bool fullRecovery) =>
        fullRecovery ? TractionWorkKwh - BrakeWorkKwh : TractionWorkKwh;

    /// <inheritdoc/>
    public override string ToString() => string.Create(
        CultureInfo.InvariantCulture,
        $"E_trakcji = {TractionWorkKwh:F4} kWh, E_hamulca = {BrakeWorkKwh:F4} kWh, " +
        $"opory = {ResistanceWorkJ / 1e6:F3} MJ, pochylenie = {GradeWorkJ / 1e6:F3} MJ, " +
        $"ΔE_kin = {KineticEnergyDeltaJ / 1e6:F3} MJ, dyskretyzacja = {DiscretizationWorkJ:F1} J, " +
        $"obcięcie = {ClampedWorkJ:F1} J, reszta = {ResidualJ:E3} J, względnie = {RelativeResidual:E3}");
}

/// <summary>
/// Przejazd całej osi z zatrzymaniem na **każdej** stacji: rozpęd, hamowanie liczone
/// solverem z T-311 i pełny cykl drzwi z T-312.
///
/// <para><b>Czym to się różni od <see cref="ScenarioDrive"/>.</b> Tamten wykonuje
/// **zapisany** scenariusz: polecenie jest funkcją chainage, wpisaną z góry. Tutaj
/// polecenia nie ma z góry — maszynista jest zamknięty w pętli sprzężenia zwrotnego:
/// w każdym kroku pyta solvera, jakiego opóźnienia wymaga odległość do najbliższej
/// stacji, i hamuje wtedy, gdy odpowiedź przekroczy próg. Punkt hamowania nie jest
/// więc parametrem — jest **wynikiem**, i to takim, który zmienia się z prędkością,
/// masą i pochyleniem, bo zmienia się razem z nimi wymagane opóźnienie.</para>
///
/// <para><b>Co to daje.</b> Czas jazdy między stacjami przestaje być liczbą wpisaną
/// do scenariusza i staje się przewidywaniem modelu — porównywalnym z rozkładem STIB
/// zmierzonym w T-113 (`build/timetable.json`, pole `segments`). Błąd zatrzymania jest
/// mierzony, a nie zakładany: skład staje tam, gdzie fizyka go zatrzyma.</para>
///
/// <para><b>Czego tu świadomie nie ma.</b> Ograniczeń prędkości wzdłuż osi — w
/// `data/track/*.json` pole `speed_limits` jest **pustą listą we wszystkich sześciu
/// pakietach** i nie ma dla nich źródła. Przejazd dostaje więc jedno ograniczenie na
/// całą oś, jako jawne założenie wołającego. Nie ma też sygnalizacji (T-313) ani
/// innych składów (T-320): ten przejazd jest sam na linii.</para>
/// </summary>
public sealed class LineRun
{
    /// <summary>
    /// Bezpiecznik pętli: godzina symulacji. Przejazd pakietu A z zatrzymaniami trwa
    /// ok. 11 minut, więc limit łapie tylko przebieg, który utknął.
    /// </summary>
    public const long DefaultStepBudget = 60 * 60 * FixedStep.SimulationHertz;

    private readonly TrainController _controller;
    private readonly BrakingPointSolver _solver;
    private readonly FixedStep _step;

    /// <summary>Przejazd zbudowany z modelu pojazdu.</summary>
    public LineRun(VehicleModel model)
        : this(new TrainController(model), new BrakingPointSolver(model), FixedStep.Simulation)
    {
    }

    /// <summary>Przejazd ze złożonych osobno składników.</summary>
    public LineRun(TrainController controller, BrakingPointSolver solver, FixedStep step)
    {
        ArgumentNullException.ThrowIfNull(controller);
        ArgumentNullException.ThrowIfNull(solver);
        step.RequireValid();

        _controller = controller;
        _solver = solver;
        _step = step;
    }

    /// <summary>Przejazd M7.</summary>
    public static LineRun M7 { get; } = new(VehicleModel.M7);

    /// <summary>Kontroler prowadzący ten przejazd.</summary>
    public TrainController Controller => _controller;

    /// <summary>Krok stały użyty przez przejazd.</summary>
    public FixedStep TimeStep => _step;

    /// <summary>
    /// Ślad przejazdu: wołany po każdym kroku, gdy podany. Istnieje po to, żeby różnicę
    /// wobec profilu idealnego dało się **zobaczyć**, a nie tylko zmierzyć na końcu.
    /// </summary>
    /// <param name="TimeSeconds">Czas od początku przejazdu.</param>
    /// <param name="ChainageM">Chainage czoła składu.</param>
    /// <param name="SpeedMps">Prędkość po kroku.</param>
    /// <param name="BrakeRateMps2">Opóźnienie hamulca, jakie faktycznie działa.</param>
    /// <param name="Command">Polecenie użyte w tym kroku.</param>
    /// <param name="Phase">Faza drzwi, gdy trwa postój.</param>
    public readonly record struct TracePoint(
        double TimeSeconds, double ChainageM, double SpeedMps,
        double BrakeRateMps2, DriverCommand Command, DoorPhase Phase);

    /// <summary>
    /// Przejazd osi od pierwszej do ostatniej stacji.
    /// </summary>
    /// <param name="axis">Oś z chainage stacji.</param>
    /// <param name="conditions">Masa, pochylenie, przyczepność, otoczenie toru.</param>
    /// <param name="settings">Założenia przejazdu — wszystkie bez źródła, patrz <see cref="LineRunSettings"/>.</param>
    /// <param name="stepBudget">
    /// Bezpiecznik pętli. Po tylu krokach przejazd kończy się BEZ dojazdu do ostatniej
    /// stacji i mówi o tym wprost: <c>FinishReason</c> ma wtedy wartość
    /// <c>"step-budget"</c>, a nie <c>"arrived"</c>. Nie jest to wyjątek — wynik jest
    /// pełny i daje się obejrzeć.
    /// </param>
    /// <param name="trace">
    /// Ślad przejazdu; wołany po KAŻDYM kroku, gdy podany, i pomijany, gdy null.
    /// Nie wpływa na wynik — przejazd bez śladu i ze śladem daje ten sam
    /// <see cref="LineRunResult"/> co do bitu.
    /// </param>
    /// <returns>
    /// Czas, droga, suma postojów, liczba kroków, lista zatrzymań i powód zakończenia
    /// pętli. Powodu trzeba zawsze przeczytać — patrz <paramref name="stepBudget"/>.
    /// </returns>
    public LineRunResult Run(
        TrackAxis axis,
        RunConditions conditions,
        LineRunSettings settings,
        long stepBudget = DefaultStepBudget,
        Action<TracePoint>? trace = null)
    {
        ArgumentNullException.ThrowIfNull(axis);
        ArgumentNullException.ThrowIfNull(conditions);
        ArgumentNullException.ThrowIfNull(settings);
        if (axis.Stations.Count < 2)
        {
            throw new ArgumentOutOfRangeException(
                nameof(axis), axis.Stations.Count,
                "Przejazd z zatrzymaniami wymaga co najmniej dwóch stacji na osi.");
        }

        var drive = new LineDrive(axis, conditions, settings, _controller, _solver, _step);
        while (drive.Steps < stepBudget && !drive.Finished)
        {
            drive.Step(trace);
        }

        return drive.Result(drive.Finished ? "arrived" : "step-budget");
    }

}
