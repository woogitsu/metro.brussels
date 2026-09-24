using System;
using System.Collections.Generic;
using MetroBxl.Sim.Line;
using MetroBxl.Sim.Physics;

namespace MetroBxl.Sim.Train;

/// <summary>
/// Jeden prowadzony skład, krokowany **z zewnątrz**.
///
/// <para><b>Po co to istnieje.</b> <see cref="LineRun"/> trzyma pętlę wewnątrz siebie:
/// woła się raz i wraca dopiero po całym przejeździe. Dla jednego składu to wystarcza,
/// ale T-320 potrzebuje **wielu składów na jednym zegarze** — a dwóch pętli, z których
/// każda wie tylko o sobie, nie da się zsynchronizować co krok. Żeby skład mógł zobaczyć
/// inny skład przed sobą, ktoś musi mieć prawo powiedzieć „wszyscy o jeden krok".</para>
///
/// <para><b>Czym to NIE jest.</b> To nie jest nowy model jazdy. Ciało kroku jest
/// przeniesione z <see cref="LineRun"/> bez zmiany kolejności działań — dowodem jest
/// ślad co krok, identyczny co do bajtu na sześciu osiach przed refaktorem i po nim.
/// Sam <see cref="LineRun"/> po tej zmianie jest pętlą <c>while</c> nad tą klasą
/// i niczym więcej.</para>
///
/// <para><b>Czego tu nadal nie ma.</b> Ani jeden skład nie wie o żadnym innym. Ta klasa
/// tylko **umożliwia** wspólny zegar; sprzężenie między składami — autorytet jazdy
/// z T-313, takt, turnback — jest osobnym krokiem i częściowo czeka na decyzje,
/// których nie ma w żadnym dokumencie (`docs/TASKS.md`, T-320, sekcja STOP).</para>
///
/// <para><b>Okno zatrzymania jest JEDNOSTRONNE, i to jest różnica wobec
/// <see cref="StationService"/> — wybrana świadomie (6.M2), a nie przeoczona.</b>
/// Postój zakłada się przy <c>chainage &gt;= cel − okno</c>, bez ograniczenia z góry;
/// <c>StationService</c> wymaga <c>|chainage − cel| &lt;= okno</c>. Skład ręczny
/// zatrzymany 50 m za peronem dostaje tu więc postój z błędem zatrzymania +50 m,
/// a tam — stację miniętą; drzwi na takim postoju są jednak odmówione (6.M3), więc
/// różnica dotyczy WYŁĄCZNIE zapisu wywołania, nie obsługi. Powód, dla którego zostaje tak: dwustronne okno wymagałoby
/// reguły dla składu stojącego ZA oknem, której żaden dokument nie podaje, bo ta klasa
/// nie ma rejestru stacji miniętych, a odjazd bez obsługi (MB-08) jest gałęzią TRWAJĄCEGO
/// postoju. Dla autopilota różnica nie ma skutku — staje z błędem rzędu 0,3 m — więc
/// ślad sześciu osi jest przy tej odpowiedzi ten sam co do bajtu. Obie strony przybija
/// <c>StopWindowParityTests</c> na jednym i tym samym stanie składu.</para>
/// </summary>
public sealed class LineDrive
{
    private readonly TrainController _controller;
    private readonly BrakingPointSolver _solver;
    private readonly FixedStep _step;
    private readonly IReadOnlyList<AxisStation> _stations;
    private readonly RunConditions _conditions;
    private readonly LineRunSettings _settings;
    private readonly DoorCycle _cycle;
    private readonly double _start;
    private readonly double _axisEndM;
    private readonly double _trigger;
    private readonly double _effectiveMassKg;
    private readonly List<StationCall> _calls;

    private DriveState _state = DriveState.AtRest;
    private int _next = 1;
    private double _topSpeed;
    private double _departedAtSeconds;
    private double _departedFromM;
    private bool _braking;
    private double _brakingToM = double.NaN;
    private StationStop? _stop;

    // Bilans energii CAŁEGO przejazdu — patrz TripEnergyAccount. Akumulowane po KAŻDYM
    // kroku kontrolera, na postoju i między stacjami jednakowo, żeby suma objęła cały
    // przejazd, a nie tylko jazdę między peronami.
    private double _tractionWorkJ;
    private double _resistanceWorkJ;
    private double _gradeWorkJ;
    private double _brakeWorkJ;
    private double _discretizationWorkJ;
    private double _clampedWorkJ;

    // Praca trakcji odczytana w chwili ODJAZDU z poprzedniej stacji. Różnica wobec
    // bieżącej daje pracę trakcji NA ODCINKU — jedyną postać, w której da się
    // odpowiedzieć na pytanie 6.A6 („ile wybieg oszczędza") inaczej niż jedną liczbą
    // na całą oś. Migawka, a nie drugi akumulator: dwa liczniki tej samej wielkości
    // rozjechałyby się przy pierwszej zmianie w AccumulateEnergy.
    private double _tractionWorkAtDepartureJ;

    /// <summary>Skład postawiony na początku osi, gotowy do pierwszego kroku.</summary>
    /// <param name="axis">Oś z kilometrażem stacji.</param>
    /// <param name="conditions">Masa, pochylenie, przyczepność, otoczenie toru.</param>
    /// <param name="settings">Założenia przejazdu — wszystkie bez źródła.</param>
    /// <param name="controller">Kontroler z T-310.</param>
    /// <param name="solver">Solver punktu hamowania z T-311.</param>
    /// <param name="step">Krok stały.</param>
    /// <param name="startStationIndex">Peron wejścia; domyślnie pierwszy na osi.</param>
    public LineDrive(
        TrackAxis axis,
        RunConditions conditions,
        LineRunSettings settings,
        TrainController controller,
        BrakingPointSolver solver,
        FixedStep step,
        int startStationIndex = 0)
    {
        ArgumentNullException.ThrowIfNull(axis);
        ArgumentNullException.ThrowIfNull(conditions);
        ArgumentNullException.ThrowIfNull(settings);
        ArgumentNullException.ThrowIfNull(controller);
        ArgumentNullException.ThrowIfNull(solver);
        step.RequireValid();

        if (axis.Stations.Count < 2)
        {
            throw new ArgumentOutOfRangeException(
                nameof(axis), axis.Stations.Count,
                "Przejazd z zatrzymaniami wymaga co najmniej dwóch stacji na osi.");
        }
        if (startStationIndex < 0 || startStationIndex >= axis.Stations.Count - 1)
        {
            throw new ArgumentOutOfRangeException(nameof(startStationIndex), startStationIndex,
                "Stacja wejścia musi mieć następną stację na osi.");
        }

        AxisId = axis.Id;
        _stations = axis.Stations;
        _conditions = conditions;
        _settings = settings;
        _controller = controller;
        _solver = solver;
        _step = step;

        _start = _stations[startStationIndex].ChainageM;
        _axisEndM = axis.LengthM;
        _next = startStationIndex + 1;
        _cycle = new DoorCycle(settings.PassengerExchangeSeconds);
        _trigger = settings.BrakeUsageFraction * controller.ServiceBrakeMps2;
        _effectiveMassKg = controller.Dynamics.EffectiveMassKg(conditions.MassKg);
        _calls = new List<StationCall>(_stations.Count);
        _departedFromM = _start;
    }

    /// <summary>Identyfikator osi, po której jedzie ten skład.</summary>
    public string AxisId { get; }

    /// <summary>Stan dynamiczny po ostatnim kroku.</summary>
    public DriveState State => _state;

    /// <summary>Chainage czoła składu na osi.</summary>
    public double ChainageM => _start + _state.DistanceM;

    /// <summary>Liczba wykonanych kroków — czas jest funkcją tej liczby, nigdy sumą.</summary>
    public long Steps => _state.Steps;

    /// <summary>Zatrzymania odnotowane do tej pory.</summary>
    public IReadOnlyList<StationCall> Calls => _calls;

    /// <summary>Prawda, gdy skład zatrzymał się na ostatniej stacji osi.</summary>
    public bool Finished => _next >= _stations.Count;

    /// <summary>Prawda, gdy trwa postój na stacji.</summary>
    public bool AtStation => _stop is not null;

    /// <summary>
    /// Faza drzwi w tym kroku; <see cref="DoorPhase.Closed"/> poza postojem.
    ///
    /// Dopisane, żeby KABINA mogła być widokiem tego przejazdu, a nie tylko jego
    /// wynikiem: HUD ma pokazać, co dzieje się z drzwiami, a nie odgadywać tego
    /// z prędkości zero. Sam przebieg jest niezmieniony — trzy własności tylko
    /// czytają stan, który ta klasa i tak trzymała.
    /// </summary>
    public DoorPhase Phase => _stop?.Phase ?? DoorPhase.Closed;

    /// <summary>
    /// Ile sekund postoju zostało; zero poza postojem, <b>NaN na postoju ręcznym</b>.
    ///
    /// <para>NaN, a nie zero i nie jakakolwiek liczba — bo na postoju ręcznym długość
    /// fazy otwartej podaje CZŁOWIEK i nikt jej z góry nie zna (MB-08). Zero znaczyłoby
    /// „już koniec", a liczba z <see cref="DoorCycle.PassengerExchangeSeconds"/> byłaby
    /// założeniem scenariusza podanym jako pomiar. Widok ma na to gałąź, a nie
    /// formatowanie.</para>
    /// </summary>
    public double DwellRemainingSeconds => _stop is null
        ? 0.0
        : _stop.Control == DoorControl.Manual
            ? double.NaN
            : Math.Max(0.0, _cycle.DwellSeconds - _stop.SecondsSinceStopped);

    /// <summary>
    /// Tryb sterowania drzwiami, który dostanie <b>NASTĘPNY</b> postój tego składu.
    ///
    /// <para><b>Czytany przy zakładaniu postoju, nie w każdym kroku</b> — i to jest
    /// treść, nie szczegół. Pole „Weryfikacja" MB-08 żąda, żeby przejęcie i oddanie
    /// sterowania <b>w czasie cyklu</b> nie resetowało drzwi; tryb zamrożony na czas
    /// postoju spełnia to z definicji, bo nie ma czego resetować. Zmiana trybu w środku
    /// cyklu wymagałaby przeniesienia stanu między dwiema różnymi maszynami faz i każde
    /// takie przeniesienie byłoby wymyśloną regułą.</para>
    ///
    /// <para><b>Skutek dla przejazdu autopilota: żaden.</b> Domyślną wartością jest
    /// <see cref="DoorControl.Automatic"/>, a <see cref="LineCore"/> ustawia
    /// <see cref="DoorControl.Manual"/> wyłącznie składom, które w tej chwili prowadzi
    /// człowiek. Przejazd bez ani jednego przejęcia idzie więc tą samą maszyną,
    /// co przed MB-08 — zmierzone na sześciu osiach co do bajtu.</para>
    /// </summary>
    public DoorControl DoorControl { get; set; } = DoorControl.Automatic;

    /// <summary>Tryb sterowania drzwiami TRWAJĄCEGO postoju; <c>null</c> poza postojem.</summary>
    public DoorControl? StopDoorControl => _stop?.Control;

    /// <summary>
    /// Polecenie otwarcia drzwi od maszynisty.
    ///
    /// <para>Odmowa <see cref="DoorRefusal.OutsidePlatformWindow"/> pada tutaj, a nie
    /// w <see cref="StationStop"/>, i nie da się jej tam przenieść: postój w ogóle nie
    /// istnieje, dopóki skład nie stanie w oknie peronu, więc obiekt, który miałby
    /// odmówić, jeszcze nie powstał. To jest ta sama granica, co między „czy wolno
    /// ciągnąć" a „gdzie stoi skład".</para>
    ///
    /// <para><b>Odmawia także NA postoju, gdy czoło stoi za oknem peronu</b> — DECYZJA
    /// WŁAŚCICIELA 23.09.2026 (6.M3). Okno zakładania postoju jest tu jednostronne (6.M2),
    /// więc skład ręczny zatrzymany 50 m za peronem ma postój, a do tej zmiany mógł na nim
    /// otworzyć drzwi w tunelu. Okno DRZWI jest od dziś dwustronne, jak w
    /// <see cref="StationService"/>: <c>|chainage − cel| &lt;= okno</c>. Skład za oknem może
    /// już tylko odjechać, a stacja zostaje w <see cref="Calls"/> jako odjazd bez obsługi.</para>
    /// </summary>
    /// <returns>Przyjęcie albo odmowa z powodem.</returns>
    public DoorRequestResult RequestDoorOpen() => _stop is null || OutsideDoorWindow()
        ? DoorRequestResult.Refused(DoorRefusal.OutsidePlatformWindow)
        : _stop.RequestOpen(_state);

    /// <summary>
    /// Czy czoło stoi poza oknem drzwi bieżącej stacji — <c>|chainage − cel| &gt; okno</c>.
    /// Jedno zdanie dla polecenia maszynisty i dla autopilota dopilnowującego postoju
    /// ręcznego (6.M3), żeby obaj dostawali tę samą odmowę.
    /// </summary>
    private bool OutsideDoorWindow() =>
        Math.Abs(ChainageM - _stations[_next].ChainageM) > _settings.StopWindowM;

    /// <summary>Polecenie zamknięcia drzwi od maszynisty.</summary>
    /// <returns>Przyjęcie albo odmowa z powodem.</returns>
    public DoorRequestResult RequestDoorClose() => _stop is null
        ? DoorRequestResult.Refused(DoorRefusal.OutsidePlatformWindow)
        : _stop.RequestClose();

    /// <summary>Stacja, do której skład jedzie; <c>null</c> po ostatniej.</summary>
    public AxisStation? NextStation => Finished ? null : _stations[_next];

    /// <summary>
    /// Ograniczenie prędkości, którym TEN skład naprawdę jedzie — ta sama liczba,
    /// którą <see cref="Step"/> podaje kontrolerowi, a nie jej kopia.
    ///
    /// <para><b>Po co to jest.</b> Żeby widok mógł POKAZAĆ limit przejazdu, nie musząc
    /// go szukać u siebie. Do 04.09.2026 nagłówek sceny brał limit z rejestru pojazdu
    /// (<c>DriveScenario.SpeedLimitMps</c>, 80 km/h — prędkość KONSTRUKCYJNA M7) i przy
    /// <c>--limit-kmh=70</c> wypisywał 80,0 km/h, podczas gdy skład rozpędzał się
    /// dokładnie do 70,00 km/h. Liczba w napisie nie była wynikiem, więc nic jej nie
    /// porównywało.</para>
    /// </summary>
    public double SpeedLimitMps => _settings.SpeedLimitMps;

    /// <summary>
    /// Kilometraż, za który skład nie ma prawa wyjechać w tym kroku — koniec autorytetu
    /// jazdy. `null` znaczy „droga wolna do następnej stacji".
    ///
    /// <para><b>Dlaczego to jest tu, a nie w kontrolerze.</b> Ograniczenie ruchu składu
    /// jest poleceniem maszynisty, a nie własnością pojazdu. Kontroler z T-310 dostaje
    /// nastawę i liczy fizykę; to, skąd ta nastawa się wzięła — z odległości do stacji
    /// czy z zajętego bloku przed nosem — należy do prowadzenia.</para>
    ///
    /// <para><b>Czego to NIE robi.</b> Nie jest drugą fizyką hamowania. Skład hamuje tym
    /// samym serwem co przed stacją, tylko cel jest bliższy z dwóch. Gdyby autorytet miał
    /// własny wzór, dwa modele hamowania rozjechałyby się i nie dałoby się powiedzieć,
    /// który jest prawdziwy.</para>
    /// </summary>
    public double? AuthorityEndM { get; set; }

    /// <summary>
    /// Nadzór ochrony pociągu: filtr polecenia stosowany PRZED kontrolerem.
    /// <c>null</c> znaczy „bez ochrony" i wtedy przejazd jest bit w bit taki, jak przed
    /// dodaniem tego haka.
    ///
    /// <para><b>Dlaczego hak, a nie gałąź w środku.</b> Z tego samego powodu, dla którego
    /// <see cref="AuthorityEndM"/> jest tu, a nie w kontrolerze: ograniczenie ruchu składu
    /// jest poleceniem, a nie własnością pojazdu. Ochrona nie liczy tu ani jednej siły —
    /// bierze gotową decyzję (<c>ProtectionDecision.Apply</c>) i przekłada ją na
    /// nastawniki. Druga formuła hamowania obok tej z T-311 dałaby dwa modele, które się
    /// rozjadą (zasada 4 z T-313).</para>
    ///
    /// <para><b>Filtr widzi polecenie, nie stan.</b> Wołający zna prędkość i sygnalizację
    /// lepiej niż prowadzenie, więc decyzję podejmuje on; tutaj wchodzi wyłącznie jej
    /// skutek. Dzięki temu ten sam hak obsługuje autopilota i kabinę z człowiekiem.</para>
    /// </summary>
    public Func<DriverCommand, DriverCommand>? Supervisor { get; set; }

    /// <summary>
    /// Komenda maszynisty na ten krok — <c>null</c> znaczy „prowadzi autopilot".
    ///
    /// <para><b>Ten hak jest ODDZIELNY od <see cref="Supervisor"/> i to jest cała
    /// treść MB-06.</b> Supervisor jest OCHRONĄ: stoi ZA poleceniem i może je tylko
    /// przyciąć. Ten hak jest ŹRÓDŁEM polecenia: staje w miejsce autopilota. Wepchnięcie
    /// klawiszy gracza w <c>Supervisor</c> byłoby wygodne i byłoby błędem — ochrona
    /// przestałaby być ochroną, a stałaby się drugim wejściem, przez które da się ją
    /// wyłączyć.</para>
    ///
    /// <para><b>Droga polecenia jest JEDNA, niezależnie od właściciela.</b> Komenda
    /// maszynisty przechodzi przez ten sam filtr postoju (<c>StationStop.Filter</c>,
    /// czyli drzwi) i przez tego samego <see cref="Supervisor"/> co komenda autopilota.
    /// Człowiek nie ma więc ani jednej drogi, której autopilot nie ma — ma tylko inne
    /// źródło.</para>
    ///
    /// <para><b>Autopilot liczy swoje polecenie NAWET wtedy, gdy prowadzi człowiek,
    /// i to jest decyzja, nie przeoczenie.</b> Zatrzask hamowania
    /// (<c>_braking</c>/<c>_brakingToM</c>) jest stanem autopilota rozpiętym na wiele
    /// kroków; gdyby przestał się posuwać na czas przejęcia, oddanie sterowania
    /// wznawiałoby autopilota ze stanem sprzed przejęcia — a najgorszy przypadek jest
    /// zmierzony i nazwany w T-320: autopilot z wyzerowanym zatrzaskiem, stojący przed
    /// autorytetem, PEŁZNIE (0,30 m w 58 s). Autopilot patrzy więc na trasę przez cały
    /// czas; zmienia się wyłącznie to, czyja komenda dociera do kontrolera.</para>
    /// </summary>
    public DriverCommand? DriverInput { get; set; }

    /// <summary>
    /// Ostatnia komenda PRZED ochroną — czyli położenie dźwigni, a nie skutek jazdy.
    ///
    /// <para>Istnieje po to, żeby przejęcie sterowania mogło zacząć się od tego, co skład
    /// robi w tej chwili. Pole „Weryfikacja" MB-06 żąda, żeby przejęcie przy niezerowej
    /// prędkości nie zmieniło ani pozycji, ani prędkości, ani kursu — a przejęcie
    /// zaczynające się od zera nastawnika zmieniłoby wszystkie trzy w następnym kroku.</para>
    /// </summary>
    public DriverCommand LastCommand { get; private set; } = DriverCommand.Coast;

    /// <summary>
    /// Jeden krok stały. Ciało przeniesione z <see cref="LineRun"/> bez zmiany kolejności.
    /// </summary>
    /// <param name="trace">Ślad wołany po kroku, gdy podany.</param>
    /// <returns>Fałsz, gdy skład był już na końcu i krok się nie odbył.</returns>
    public bool Step(Action<LineRun.TracePoint>? trace = null)
    {
        if (Finished)
        {
            return false;
        }

        var chainage = _start + _state.DistanceM;
        var target = _stations[_next].ChainageM;

        if (_stop is null
            && _state.SpeedMps <= 0.0
            && chainage >= target - _settings.StopWindowM
            && chainage - _departedFromM >= _settings.StopWindowM)
        {
            _stop = new StationStop(_cycle, _step, DoorControl);
            _calls.Add(new StationCall(
                _stations[_next].Name,
                _stations[_next].StopId,
                target,
                chainage,
                chainage - target,
                _state.TimeSeconds(_step),
                double.NaN,
                _state.TimeSeconds(_step) - _departedAtSeconds,
                chainage - _departedFromM,
                _topSpeed,
                _tractionWorkJ - _tractionWorkAtDepartureJ));
        }

        if (_stop is not null)
        {
            // AUTOPILOT DOPILNOWUJE RĘCZNIE OTWARTEGO POSTOJU. To jest odpowiedź na pole
            // „Wyjście" MB-08: „obsługa TYCH SAMYCH reguł przez AI" — nie druga maszyna
            // drzwi dla AI, tylko ta sama maszyna z drugim palcem na przycisku.
            //
            // Sytuacja, dla której to istnieje, jest jedna i konkretna: maszynista
            // przejął skład, stanął, otworzył drzwi i ODDAŁ sterowanie. Bez tych paru
            // wierszy skład stałby z otwartymi drzwiami do końca przejazdu, bo jedyne
            // polecenie zamknięcia w trybie ręcznym pochodzi od człowieka, a człowieka
            // już nie ma; blokada trakcji trzymałaby przy tym nastawnik na zerze, więc
            // nie byłoby to nawet widoczne jako ruch — linia po prostu by stanęła.
            //
            // Autopilot nie dostaje tu ani jednej reguły, której nie ma gracz: wciska
            // te same dwa polecenia i dostaje te same odmowy. Czas, po którym zamyka,
            // to `PassengerExchangeSeconds` — czyli **założenie scenariusza**, dokładnie
            // to samo, którym rządzi się jego własny cykl automatyczny.
            //
            // Warunek `DriverInput is null` znaczy „nikogo nie ma przy nastawniku".
            // Przy człowieku u steru te wiersze milczą i drzwi należą wyłącznie do niego.
            //
            // POSTÓJ RĘCZNY ZA OKNEM DRZWI (6.M3): autopilot nie otwiera tu drzwi, bo nie
            // wolno tego także maszyniście, tylko kończy postój odjazdem bez obsługi —
            // tym samym, który maszynista dostaje, ruszając za peronem. Bez tego skład
            // oddany autopilotowi stałby za peronem do końca przejazdu: drzwi nie da się
            // otworzyć, więc cykl nigdy się nie skończy.
            var abandoned = false;
            if (_stop.Control == DoorControl.Manual && DriverInput is null)
            {
                if (_stop.Phase == DoorPhase.Closed && !_stop.Finished && OutsideDoorWindow())
                {
                    abandoned = true;
                }
                else if (_stop.Phase == DoorPhase.Closed && !_stop.Finished)
                {
                    _stop.RequestOpen(_state);
                }
                else if (_stop.Phase == DoorPhase.Open
                         && _stop.SecondsInPhase >= _cycle.PassengerExchangeSeconds)
                {
                    _stop.RequestClose();
                }
            }

            // NA POSTOJU DŹWIGNIA TEŻ NALEŻY DO WŁAŚCICIELA, ale drzwi rozstrzygają.
            // `Filter` jest jedynym miejscem posuwającym licznik cyklu drzwi i musi
            // zostać zawołane dokładnie raz na krok — dlatego komenda maszynisty wchodzi
            // JAKO ARGUMENT tego samego wywołania, a nie obok niego. Autopilot trzyma
            // pełny hamulec służbowy i to zachowanie nie zmienia się o bit.
            var wanted = DriverInput ?? DriverCommand.FullServiceBrake;
            LastCommand = wanted;
            var held = _stop.Filter(_state, wanted);

            // OCHRONA STOI ZA DRZWIAMI I ZA OBOMA WŁAŚCICIELAMI — także tutaj.
            //
            // **Ten wiersz jest poprawką DZIURY W OCHRONIE, którą wpuściło pierwsze
            // podejście do MB-06, i był to najgorszy możliwy rodzaj dziury: cichy.**
            // Do chwili jego dopisania gałąź postoju szła z `held` prosto do
            // `_controller.Advance`, z pominięciem `Supervisor`. Dla autopilota nie
            // znaczyło to nic, bo autopilot trzyma tu pełny hamulec służbowy — ale od
            // MB-06 `wanted` bywa komendą CZŁOWIEKA, a `StationStop.Filter` zeruje
            // wyłącznie `Throttle`, i to tylko wtedy, gdy cykl drzwi już ruszył
            // (`Started`); `Brake` nie rusza NIGDY — zmierzone na całym cyklu:
            // 1980 kroków z wyzerowanym nastawnikiem, ZERO kroków ze zmienionym
            // hamulcem.
            // Maszynista puszczający hamulec na postoju omijał więc ochronę zupełnie.
            //
            // ZMIERZONE dwoma niezależnymi przebiegami, zanim ten wiersz powstał.
            // Miara nieczuła na pochylenie — ile kroków postoju w ogóle woła ochronę,
            // na przejeździe L1_A przy limicie 72 km/h i wymianie 8 s:
            //
            //     bez tego wiersza   OCHRONA w krokach postoju:      0 / 21 780
            //     z tym wierszem     OCHRONA w krokach postoju: 21 780 / 21 780
            //     najdłuższa cisza ochrony: 1981 kroków (16,51 s) -> 0
            //
            // Gałąź postoju to **25,32 % wszystkich kroków** przejazdu (21 780
            // z 86 032), więc nie było to okno brzegowe.
            //
            // **LICZBA W TYM AKAPICIE JEST POPRAWIONA, a nie dopisana obok**
            // (audyt 14.09.2026). Stało tu **21 791** i **25,33 %**, i było to
            // nieprawdą — a co gorsza, nieprawdą SPRZECZNĄ Z DWOMA INNYMI MIEJSCAMI
            // TEGO SAMEGO COMMITA: `reports/mb06-wspolne-komendy.md` i
            // `ControlOwnerTests.cs` podawały od początku 21 780 i 25,32 %. Trzy
            // artefakty, dwie liczby, żadnego porównania między nimi. Przeliczone
            // ponownie na `data/track/L1_A.json` przy limicie 72 km/h i wymianie 8 s:
            // kroków postoju jest **21 780**, tak samo z planem sygnalizacji i bez
            // niego. Wniosek dla następnego, kto będzie tu pisał liczbę: liczba
            // powtórzona w trzech miejscach musi być w trzech miejscach ZMIERZONA
            // albo w jednym, a w pozostałych dwóch zacytowana — nie przepisana.
            //
            // Skutek ruchowy zależy od
            // pochylenia: na −3 % skład staczał się przy OTWARTYCH drzwiach, meldując
            // ten ruch sygnalizacji przez `MoveTrain`. Liczba metrów zależy od tego,
            // w której fazie drzwi maszynista przejmie — 5,83 m do 1,73 m/s przy
            // przejęciu w fazie `Open`, 38,27 m do 4,44 m/s przy przejęciu na początku
            // cyklu; **dlatego miarą tego komentarza są wywołania ochrony, a nie metry.**
            // Widać to nawet na PŁASKIM: bez tego wiersza cały przejazd trwa 85 962
            // kroki zamiast 86 032, bo puszczony hamulec nie musi się przed odjazdem
            // odpuszczać.
            //
            // Kolejność jest treścią: najpierw DRZWI (czy wolno ciągnąć), potem
            // OCHRONA (czy wolno jechać tak szybko). Ochrona ma ostatnie słowo w obu
            // gałęziach tej metody i dopiero to czyni prawdziwym zdanie, że komenda
            // człowieka nie ma ani jednej drogi, której nie ma komenda autopilota.
            held = Supervisor is null ? held : Supervisor(held);

            var phase = _stop.Phase;
            var beforeStop = _state;
            var advancedStop = _controller.Advance(
                _state, _conditions, held, _settings.SpeedLimitMps, _step, out var stopForces);
            _state = TrackEndStop.Apply(advancedStop, _start, _axisEndM);
            AccumulateEnergy(beforeStop, _state, stopForces, advancedStop != _state);
            trace?.Invoke(new LineRun.TracePoint(
                _state.TimeSeconds(_step), _start + _state.DistanceM, _state.SpeedMps,
                _state.BrakeRateMps2,
                TrackEndStop.Reached(ChainageM, _axisEndM) ? DriverCommand.Coast : held,
                phase));

            // ODJAZD BEZ OBSŁUGI DRZWI — możliwy WYŁĄCZNIE w trybie ręcznym i wyłącznie
            // do przodu. W trybie automatycznym nie ma jak: cykl rusza sam w pierwszym
            // kroku o zerowej prędkości, a blokada trakcji trzyma skład do końca kontroli
            // zamknięcia. W ręcznym maszynista ma drzwi zamknięte i wolną trakcję od
            // pierwszego kroku postoju, więc wolno mu po prostu odjechać.
            //
            // Bez tego warunku skład jechałby dalej GAŁĘZIĄ POSTOJU przez resztę osi:
            // `_next` nigdy by się nie posunął, hamowanie do następnej stacji nigdy nie
            // zostałoby policzone, a gałąź postoju nie zna ani autorytetu, ani zatrzasku.
            // Byłaby to usterka cicha — skład jedzie, HUD pokazuje drzwi zamknięte,
            // a przejazd nie kończy się nigdy.
            //
            // Stacja mijana w ten sposób zostaje w `Calls` z czasem odjazdu, bo skład
            // NAPRAWDĘ tam był i NAPRAWDĘ odjechał. Czego ten zapis nie mówi, to czy
            // ktokolwiek wsiadł; osobnej kolumny nie ma świadomie — plik `--calls` jest
            // porównywany ze sceną co do bajtu (`godot-first-run.yml`), więc nowa kolumna
            // zerwałaby cudzą bramkę. Brak jest nazwany w odbiorze #26.
            // WARUNEK „SKŁAD JEDZIE" JEST TU KONIECZNY, a nie ostrożnościowy. Okno
            // zatrzymania jest w tej klasie JEDNOSTRONNE — postój zakłada się przy
            // `chainage >= target - StopWindowM`, bez ograniczenia od góry — więc skład,
            // który przestrzelił peron o sześć metrów, staje i dostaje normalny postój.
            // Bez pytania o prędkość taki postój byłby uznany za „odjazd bez obsługi"
            // w tym samym kroku, w którym powstał: zmierzone na ręcznym przejeździe osi
            // syntetycznej — trzy stacje, trzy postoje, WSZYSTKIE zamknięte natychmiast
            // (zatrzymania na 2005,72 m przy stacji 2000,00 m i oknie 5,00 m).
            //
            // „Odjazd bez obsługi" ma znaczyć ODJAZD. Skład stojący za peronem stoi,
            // a nie odjeżdża. **Zdanie przepisane 23.09.2026, a nie dopisane obok
            // (DECYZJA WŁAŚCICIELA, 6.M3):** stało tu „i wolno mu jeszcze otworzyć
            // drzwi" — i to już nieprawda. Za oknem drzwi odmawia `RequestDoorOpen`,
            // więc stojący tam skład może już tylko odjechać.
            var behindPlatform = _start + _state.DistanceM > target + _settings.StopWindowM;
            var leftWithoutService = _stop.Control == DoorControl.Manual
                && !_stop.Finished
                && _stop.Phase == DoorPhase.Closed
                && behindPlatform
                && _state.SpeedMps > 0.0;

            if (_stop.Finished || leftWithoutService || abandoned)
            {
                _calls[^1] = _calls[^1] with { DepartureSeconds = _state.TimeSeconds(_step) };
                _departedAtSeconds = _state.TimeSeconds(_step);
                _departedFromM = _start + _state.DistanceM;
                _tractionWorkAtDepartureJ = _tractionWorkJ;
                _topSpeed = 0.0;
                _braking = false;
                _brakingToM = double.NaN;
                _stop = null;
                _next++;
            }

            return true;
        }

        // Cel hamowania to BLIŻSZY z dwóch: następna stacja albo koniec autorytetu.
        // Gdy autorytet sięga dalej niż stacja, nie zmienia się nic — i ta tożsamość
        // jest przypięta testem, bo inaczej wprowadzenie sygnalizacji po cichu zmieniłoby
        // każdy dotychczasowy przejazd.
        var stopAt = AuthorityEndM is double limit && limit < target ? limit : target;

        // Zatrzask hamowania jest zatrzaskiem **na konkretny cel**, a nie na cały odcinek.
        // Przed autorytetem cel się cofa i wraca: skład wyhamowuje przed zajętym blokiem,
        // a gdy poprzedzający zwolni blok, autorytet skacze do przodu. Zatrzask bez tego
        // zwolnienia trzymałby skład na zawsze — `Command` przy zatrzasku nigdy nie wraca
        // do trakcji, więc skład, raz zatrzymany przed sygnałem, dojechałby do stacji
        // wybiegiem albo wcale. Przy jeździe do stacji cel się nie rusza, więc warunek
        // nigdy nie zachodzi i ślad przejazdu solo jest ten sam co przed tą zmianą.
        if (_braking && stopAt > _brakingToM + TrackAxis.PositionEpsilonM)
        {
            _braking = false;
        }

        // Skład, który stanął PRZED AUTORYTETEM, stoi — dopóki autorytet się nie ruszy.
        //
        // Bez tego warunku pełznie. `Command` przy prędkości zero daje pełną trakcję,
        // bo tak się rusza z peronu; przed sygnałem daje to skok o 9 mm/s, zaraz potem
        // wyhamowanie do zera i tak w kółko. Zmierzone: 0,30 m w 58 s, czyli minuta
        // doliczona do każdego postoju przed zajętym blokiem, a więc do każdego pomiaru
        // odstępu. Do STACJI podpełznąć wolno i jest to potrzebne — okno zatrzymania
        // (`StopWindowM`) łapie skład, który stanął za wcześnie — dlatego warunek pyta
        // o autorytet, a nie o samo zatrzymanie.
        //
        // Zatrzymanie przed autorytetem jest ostateczne, bo zezwolenie na jazdę albo jest,
        // albo go nie ma; nie ma stanu pośredniego, w którym skład dosuwa się do sygnału
        // centymetrami. Warunek nie zawiera ani jednej liczby — pyta o zatrzask hamowania
        // i o to, czy cel jest bliższy niż stacja.
        //
        // Skład, który dopiero rusza z peronu przy krótkim autorytecie, ma zatrzask
        // wyzerowany przy odjeździe, więc ten warunek go nie dotyczy i odjazd się odbywa.
        var command = _braking && stopAt < target && _state.SpeedMps <= 0.0
            ? DriverCommand.FullServiceBrake
            : Command(stopAt - chainage);
        if (command.Brake > 0.0)
        {
            if (!_braking)
            {
                _brakingToM = stopAt;
            }

            _braking = true;
        }
        // Ochrona wchodzi TUTAJ, między poleceniem i kontrolerem, i widzi ślad: to, co
        // trafia do `TracePoint`, jest poleceniem PO ingerencji, a nie przed nią. Inaczej
        // ślad pokazywałby, co maszynista chciał, a nie co pojechało — i telemetria
        // porównywana co do bitu przestałaby opisywać przejazd.
        // ŹRÓDŁO POLECENIA — tutaj i tylko tutaj. Autopilot policzył swoje `command`
        // wyżej i posunął swój zatrzask hamowania; gdy prowadzi człowiek, jego komenda
        // staje w miejsce tamtej, a zatrzask autopilota zostaje policzony i nietknięty
        // (powód przy `DriverInput`). Bez `DriverInput` nie zmienia się ani jeden bit.
        command = DriverInput ?? command;
        LastCommand = command;

        // OCHRONA STOI ZA OBOMA. To jest zdanie pola „Pułapka wypisana w audycie"
        // pozycji MB-06 wzięte dosłownie: nie ma gałęzi, w której komenda człowieka
        // omija `Supervisor`, i nie ma jej dlatego, że podmiana źródła stoi WYŻEJ
        // od ochrony, a nie obok niej.
        command = Supervisor is null ? command : Supervisor(command);
        var beforeRun = _state;
        var advancedRun = _controller.Advance(
            _state, _conditions, command, _settings.SpeedLimitMps, _step, out var runForces);
        _state = TrackEndStop.Apply(advancedRun, _start, _axisEndM);
        AccumulateEnergy(beforeRun, _state, runForces, advancedRun != _state);
        trace?.Invoke(new LineRun.TracePoint(
            _state.TimeSeconds(_step), _start + _state.DistanceM, _state.SpeedMps,
            _state.BrakeRateMps2,
            TrackEndStop.Reached(ChainageM, _axisEndM) ? DriverCommand.Coast : command,
            DoorPhase.Closed));
        if (_state.SpeedMps > _topSpeed)
        {
            _topSpeed = _state.SpeedMps;
        }

        return true;
    }

    /// <summary>Wynik przejazdu w postaci, jakiej oczekuje <see cref="LineRun"/>.</summary>
    /// <param name="reason">Dlaczego pętla wołającego się skończyła.</param>
    public LineRunResult Result(string reason)
    {
        var last = _calls.Count > 0 ? _calls[^1] : default;
        return new LineRunResult(
            AxisId,
            _calls,
            last.ArrivalSeconds,
            last.StoppedAtChainageM - _start,
            SumDwell(_calls),
            _state.Steps,
            reason,
            new TripEnergyAccount(
                _tractionWorkJ,
                _resistanceWorkJ,
                _gradeWorkJ,
                _brakeWorkJ,
                0.5 * _effectiveMassKg * _state.SpeedMps * _state.SpeedMps,
                _discretizationWorkJ,
                _clampedWorkJ));
    }

    /// <summary>
    /// Akumulacja bilansu energii po jednym kroku kontrolera — wołana identycznie na
    /// postoju i między stacjami, bo `TripEnergyAccount` opisuje CAŁY przejazd, a nie
    /// tylko jazdę.
    ///
    /// <para><b>Wyprowadzenie <c>ClampedWorkJ</c>.</b> Kontroler liczy przyspieszenie
    /// jako <c>(trakcja − opory − pochylenie)/m_ef − b_hamulca</c>, więc siła wypadkowa
    /// WSZYSTKIEGO (łącznie z hamulcem) to <c>forces.NetN − m_ef·b_hamulca</c>. Reszta
    /// jest tym samym rachunkiem, który <see cref="Physics.AccelerationRun"/> robi dla
    /// samej trakcji: iloczyn tej siły i przebytej drogi rozkłada się dokładnie na zmianę
    /// energii kinetycznej, człon dyskretyzacji i to, co zostaje — obcięcie prędkości do
    /// zera i do limitu. Tożsamość jest algebraiczna, więc działa bez względu na to, czy
    /// w danym kroku obcięcie faktycznie zaszło.</para>
    /// </summary>
    private void AccumulateEnergy(DriveState before, DriveState after, StepForces forces,
        bool axisEndClamped = false)
    {
        var travelled = after.DistanceM - before.DistanceM;
        var deltaSpeed = after.SpeedMps - before.SpeedMps;
        var netAll = forces.NetN - (_effectiveMassKg * after.BrakeRateMps2);

        _tractionWorkJ += forces.TractionN * travelled;
        _resistanceWorkJ += forces.ResistanceN * travelled;
        _gradeWorkJ += forces.GradeN * travelled;
        _brakeWorkJ += _effectiveMassKg * after.BrakeRateMps2 * travelled;
        _discretizationWorkJ += 0.5 * _effectiveMassKg * deltaSpeed * deltaSpeed;
        // Zwykły krok ma travelled = v_po·dt i zachowuje historyczny rachunek bitowo.
        // Na końcu osi odrzucamy też część DROGI kroku, więc tej równości już nie ma.
        // Bilans liczony wtedy z rzeczywistego ΔE i rzeczywistej drogi opisuje dokładnie
        // stan po ograniczeniu, który trafia do śladu i HUD.
        _clampedWorkJ += axisEndClamped
            ? netAll * travelled
              - 0.5 * _effectiveMassKg *
                (after.SpeedMps * after.SpeedMps - before.SpeedMps * before.SpeedMps)
              - 0.5 * _effectiveMassKg * deltaSpeed * deltaSpeed
            : (netAll - (_effectiveMassKg * deltaSpeed / _step.Seconds)) * travelled;
    }

    /// <summary>
    /// Polecenie maszynisty w jednym kroku jazdy między stacjami.
    ///
    /// Punkt hamowania nie jest tu parametrem. W każdym kroku solver z T-311 odpowiada,
    /// jakiego opóźnienia wymaga pozostała odległość przy bieżącej prędkości; hamowanie
    /// zaczyna się, gdy odpowiedź przekroczy próg, a jego siła jest tą odpowiedzią.
    /// Dlatego punkt hamowania przesuwa się sam wraz z prędkością, masą i pochyleniem.
    /// </summary>
    private DriverCommand Command(double remainingM)
    {
        if (remainingM <= 0.0)
        {
            // Stacja minięta z prędkością. Pełny hamulec; błąd zatrzymania to zmierzy
            // i wyjdzie w raporcie jako dodatni StopErrorM, a nie zniknie.
            return DriverCommand.FullServiceBrake;
        }

        if (_state.SpeedMps <= 0.0)
        {
            return DriverCommand.FullPower;
        }

        if (!_solver.TryRequiredDeceleration(_state.SpeedMps, 0.0, remainingM, out var need))
        {
            // Poniżej minimalnej drogi wynikającej ze zrywu rozwiązania nie ma — wtedy
            // nawet pełny hamulec nie zatrzyma składu na czas i „prawie" nie jest odpowiedzią.
            return DriverCommand.FullServiceBrake;
        }

        if (!_braking && need.DecelerationMps2 < _trigger)
        {
            // WYBIEG (6.A6) wchodzi DOKŁADNIE tutaj i nigdzie indziej: w jedynej gałęzi,
            // w której maszynista sam decyduje, czy ciągnąć. Poniżej próg już zdecydował
            // za niego i tam wybieg nie ma czego zmieniać — dlatego odcinek, na którym
            // hamowanie zaczyna się przed zadanym metrem, jedzie się bit w bit tak samo
            // jak bez wybiegu, a nie „prawie tak samo".
            return _state.SpeedMps < _settings.SpeedLimitMps && !Coasting
                ? DriverCommand.FullPower
                : DriverCommand.Coast;
        }

        // **Próg wyzwala hamowanie, ale nie steruje nim.** Raz zaczęte hamowanie idzie
        // za serwem aż do zatrzymania: siła hamulca jest w każdym kroku tą, której wymaga
        // pozostała odległość. Sprawdzanie progu również w trakcie hamowania było usterką
        // — opory ruchu hamują mocniej, niż zakłada wzór zamknięty z T-311 (ten jest
        // czysto kinematyczny), więc wymagane opóźnienie spadało poniżej progu, pętla
        // wracała do trakcji, odległość malała i hamulec wracał. W śladzie widać było
        // 3,12 s pełzania na 1,08 m: trzy sekundy doliczone do czasu jazdy przez
        // sterowanie, nie przez fizykę.
        // **Wzór zamknięty odpowiada na inne pytanie niż to, które ma serwo.** Droga
        // z T-311 zawiera człon narastania hamulca zrywem od ZERA — jest więc odpowiedzią
        // na „kiedy zacząć hamować". Gdy hamulec już działa, ten człon jest zaliczony
        // dwa razy: solver kredytuje narastanie, które się właśnie odbyło, więc żąda
        // mniejszego opóźnienia, skład jedzie dalej, i tak w kółko. W śladzie wychodziło
        // to jako łagodne dojeżdżanie do peronu i 3 s doliczone do czasu jazdy.
        //
        // Dlatego próg wyzwala hamowanie wzorem z narastaniem, a samo hamowanie prowadzi
        // czysta kinematyka v²/2d — hamulec już narósł, więc nie ma czego doliczać.
        var required = _state.SpeedMps * _state.SpeedMps / (2.0 * remainingM);

        // Polecenie to opóźnienie **hamulca**, a nie całkowite: skład zwalnia też oporami
        // ruchu i składową pochylenia, a te działają niezależnie od nastawy. Żeby sumaryczne
        // opóźnienie wyszło takie, o jakie prosi kinematyka, hamulec dostaje różnicę.
        var resistance = _controller.Dynamics.Resistance.ForceN(
            _conditions.MassKg, _state.SpeedMps, _conditions.Environment);
        var grade = TrainDynamics.GradeForceN(_conditions.MassKg, _conditions.GradePercent);
        var passive = (resistance + grade) / _controller.Dynamics.EffectiveMassKg(_conditions.MassKg);

        return new DriverCommand(
            0.0, Math.Clamp((required - passive) / _controller.ServiceBrakeMps2, 0.0, 1.0));
    }

    /// <summary>
    /// Czy skład minął już metr odcinka, od którego <see cref="LineRunSettings.CoastFromM"/>
    /// każe zdjąć trakcję. Fałsz zawsze, gdy wybieg jest wyłączony.
    ///
    /// <para>Odległość liczy się od ODJAZDU z poprzedniej stacji, a nie od początku osi:
    /// pytanie 6.A6 jest per odcinek, a próg mierzony od początku osi zdjąłby trakcję
    /// raz i na zawsze, czyli mierzyłby zupełnie inną rzecz.</para>
    /// </summary>
    private bool Coasting =>
        _settings.CoastFromM is double from && _start + _state.DistanceM - _departedFromM >= from;

    private static double SumDwell(IReadOnlyList<StationCall> calls)
    {
        var total = 0.0;
        foreach (var call in calls)
        {
            if (double.IsFinite(call.DepartureSeconds))
            {
                total += call.DepartureSeconds - call.ArrivalSeconds;
            }
        }

        return total;
    }
}
