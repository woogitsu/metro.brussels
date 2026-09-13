using System;
using System.Collections.Generic;
using MetroBxl.Sim.Line;
using MetroBxl.Sim.Physics;
using MetroBxl.Sim.Signalling;

namespace MetroBxl.Sim.Train;

/// <summary>
/// Sesja treningowa: kiedy przejazd gracza się KOŃCZY i z jakim wynikiem.
///
/// <para><b>Czego brakowało.</b> Do 13.09.2026 przejazd z klawiatury nie miał warunku
/// końca — jedynym trybem, który kończył się sam, było odtworzenie z zapisu wejść, bo
/// zapis ma skończoną liczbę kroków (<c>FirstRun.FinishReplayRun</c>). Po ostatniej
/// stacji HUD mówił „koniec pakietu", a proces trwał do <c>Esc</c>. Pętli gry
/// <b>start → cel → wynik → ponów</b> nie było gdzie zamknąć.</para>
///
/// <para><b>Dlaczego to mieszka w rdzeniu, a nie w scenie.</b> Ta sama decyzja, co przy
/// <see cref="RunRestart"/>, <c>Game.RunReset</c> i <c>Game.RunHeader</c>: scena jest
/// węzłem Godota i żaden test jednostkowy jej nie wywoła. Gdyby warunek końca stał
/// w <c>FirstRun._Process</c>, pilnowałby go wyłącznie ludzki wzrok czytający log —
/// a warunek końca jest tym jednym miejscem, w którym pomyłka kosztuje CAŁĄ pętlę gry.
/// Tu zostaje STAN sesji; prezentacja i polityka ekranu zostają w <c>Game</c>.</para>
///
/// <para><b>Cele idą po IDENTYFIKATORACH, nie po liczbie ani po kilometrażu.</b>
/// <c>docs/PLAYABILITY.md</c> §3 żąda tego wprost: „cele wyszukiwane po identyfikatorach
/// z osi; kilometraży nie kopiuje się do logiki". Sesja „dwie pierwsze stacje" byłaby
/// niema na zmianę kolejności stacji w danych, a sesja z wpisanym kilometrażem —
/// drugą kopią liczby, która stoi już w <c>data/track/</c>.</para>
///
/// <para><b><see cref="Observe"/> jest IDEMPOTENTNE co do WYNIKU i to jest wybór.</b>
/// <see cref="StationService.Filter"/> trzeba wołać dokładnie raz na krok, bo posuwa
/// licznik cyklu drzwi: dwa wywołania skracają postój o połowę, zero zawiesza go na
/// zawsze, a jedno i drugie wygląda jak działający cykl. Tutaj zakończenie jest
/// ZATRZASKIEM, więc drugie wywołanie w kroku nie zmieni wyniku ani o bit. <b>Liczniki
/// ATP idą po zboczu, więc też nie</b> — powtórzone wywołanie widzi ten sam stan
/// predykatu i zbocza nie ma. Wynik powstaje dokładnie raz dlatego, że jest zatrzask,
/// a nie dlatego, że ktoś policzył wywołania.</para>
///
/// <para><b>Zdarzenie ATP to ZBOCZE PREDYKATU i nic więcej.</b> Decyzja właściciela
/// z 13.09.2026 brzmiała „policz osobne zdarzenia", a <c>CabProtection</c> liczy KROKI
/// (<c>CabProtection.cs:170</c>: dziesięć sekund nad limitem to jedno zdarzenie i 1200
/// kroków). Trzy predykaty, trzy liczniki, jedna reguła: licznik rośnie w kroku,
/// w którym predykat przeszedł z fałszu na prawdę. Konsekwencja wypisana, żeby nie była
/// niespodzianką: <b>eskalacja służbowa → awaryjna daje JEDNO zdarzenie ingerencji
/// (predykat nie zgasł) i JEDNO awaryjne</b> — ochrona nie sięgnęła po hamulec drugi
/// raz, tylko po mocniejszy. Reguła jest mechaniczna, więc nie wymaga rozstrzygnięcia
/// semantycznego przy każdym nowym rodzaju ingerencji.</para>
///
/// <para><b>Liczników kroków w <see cref="CabProtection"/> ta klasa NIE dubluje</b>
/// i nie rusza. Odpowiadają na inne pytanie („ile przejazdu spędzono nad limitem")
/// i tylko one na nie odpowiadają.</para>
///
/// <para><b>Czego ta klasa NIE robi.</b> Nie liczy ani jednej siły, nie podaje ani
/// jednego nastawnika i nie filtruje poleceń — od tego jest <see cref="StationService"/>
/// i <see cref="TrainController"/>. Nie zna też pauzy: pauza jest polityką ekranu
/// (ticki po prostu nie idą), a sesja, której nikt nie obserwuje, stoi w miejscu sama
/// z siebie.</para>
/// </summary>
public sealed class TrainingSession
{
    private readonly List<string> _targets;
    private readonly Dictionary<string, string> _displayNames;
    private readonly FixedStep _step;

    private TrainingResult? _result;
    private bool _overspeedHeld;
    private bool _interveningHeld;
    private bool _emergencyHeld;
    private long _warningEvents;
    private long _interventionEvents;
    private long _emergencyEvents;

    /// <summary>Sesja z celami wskazanymi identyfikatorami przystanków.</summary>
    /// <param name="stations">
    /// Stacje osi w kolejności kilometrażu — ta sama lista, którą dostaje
    /// <see cref="StationService"/>. Sesja czyta z niej nazwy do pokazania i sprawdza,
    /// czy zadane cele w ogóle na tej osi są.
    /// </param>
    /// <param name="targetStopIds">
    /// Identyfikatory celów, w kolejności, w jakiej mają zostać obsłużone.
    /// <b>Bez wartości domyślnej</b> — ta sama decyzja, co przy oknie zatrzymania
    /// w <see cref="StationService"/>: zestaw celów jest treścią zadania, a nie
    /// własnością klasy. M1 podaje dwa (<c>docs/PLAYABILITY.md</c> §3), ale ta klasa
    /// o M1 nic nie wie.
    /// </param>
    /// <param name="step">Krok symulacji — z niego bierze się czas wyniku.</param>
    /// <exception cref="ArgumentNullException">Którykolwiek argument jest <c>null</c>.</exception>
    /// <exception cref="ArgumentException">
    /// Lista celów jest pusta, niesie powtórzenie, cel spoza osi albo <b>cel będący
    /// punktem startowym</b>. Ten ostatni jest najważniejszy i dlatego jest sprawdzany:
    /// <see cref="StationService"/> pomija stację o indeksie 0 jako miejsce, na którym
    /// skład stoi na starcie, więc taki cel nie trafiłby ANI do
    /// <see cref="StationService.Calls"/>, ANI do <see cref="StationService.Missed"/> —
    /// sesja czekałaby na niego bez końca i wyglądałoby to na zawieszoną grę, a nie na
    /// błędne zadanie.
    /// </exception>
    public TrainingSession(
        IReadOnlyList<AxisStation> stations,
        IReadOnlyList<string> targetStopIds,
        FixedStep step)
    {
        ArgumentNullException.ThrowIfNull(stations);
        ArgumentNullException.ThrowIfNull(targetStopIds);
        step.RequireValid();

        if (targetStopIds.Count == 0)
        {
            throw new ArgumentException(
                "Sesja treningowa bez ani jednego celu nie ma jak się skończyć.",
                nameof(targetStopIds));
        }

        _displayNames = new Dictionary<string, string>(StringComparer.Ordinal);
        for (var i = 0; i < stations.Count; i++)
        {
            _displayNames[stations[i].StopId] = stations[i].DisplayName;
        }

        var startId = stations.Count > 0 ? stations[0].StopId : null;
        var widziane = new HashSet<string>(StringComparer.Ordinal);
        foreach (var id in targetStopIds)
        {
            if (!_displayNames.ContainsKey(id))
            {
                throw new ArgumentException(
                    $"Cel „{id}” nie występuje na tej osi — sesja czekałaby na niego bez końca.",
                    nameof(targetStopIds));
            }

            if (string.Equals(id, startId, StringComparison.Ordinal))
            {
                throw new ArgumentException(
                    $"Cel „{id}” jest punktem startowym osi, a obsługa stacji pomija go " +
                    "jako miejsce, na którym skład stoi na starcie — nie trafi ani do " +
                    "wywołań, ani do miniętych.",
                    nameof(targetStopIds));
            }

            if (!widziane.Add(id))
            {
                throw new ArgumentException(
                    $"Cel „{id}” podany dwa razy, a stacji nie da się obsłużyć dwukrotnie " +
                    "— skład nie ma biegu wstecznego.",
                    nameof(targetStopIds));
            }
        }

        _targets = new List<string>(targetStopIds);
        _step = step;
    }

    /// <summary>Identyfikatory celów, w zadanej kolejności.</summary>
    public IReadOnlyList<string> TargetStopIds => _targets;

    /// <summary>Czy wynik już powstał.</summary>
    public bool Finished => _result is not null;

    /// <summary>
    /// Wynik albo <c>null</c>, gdy sesja trwa. <c>null</c>, a nie wynik
    /// z <see cref="TrainingEnding.Running"/>: wynik trwającej sesji jest wynikiem,
    /// którego nie ma, a nie wynikiem o treści „trwa".
    /// </summary>
    public TrainingResult? Result => _result;

    /// <summary>Jak sesja się skończyła; <see cref="TrainingEnding.Running"/>, gdy trwa.</summary>
    public TrainingEnding Ending => _result?.Ending ?? TrainingEnding.Running;

    /// <summary>
    /// Patrzy na stan przejazdu i zatrzaskuje wynik, gdy sesja się skończyła.
    ///
    /// <para><b>Wołać RAZ NA KROK, na KOŃCU kroku</b> — za ruchem składu i za
    /// <see cref="StationService.Filter"/>. Warunek zaliczenia pyta o prędkość PO kroku
    /// i o cykl drzwi PO filtrze; policzony przed nimi opisywałby krok poprzedni.
    /// Wywołanie nadmiarowe niczego nie psuje (zatrzask i zbocza), ale wywołanie
    /// ZA WCZEŚNIE — owszem.</para>
    /// </summary>
    /// <param name="stations">Obsługa stacji tego przejazdu.</param>
    /// <param name="state">Stan składu po ostatnim kroku.</param>
    /// <param name="protection">
    /// Decyzja ochrony z tego kroku albo <c>null</c> w przejeździe bez sygnalizacji.
    /// Brak jest tu poprawnym stanem, a nie błędem — tak samo jak w
    /// <see cref="RunRestart.Apply"/>.
    /// </param>
    /// <exception cref="ArgumentNullException">Obsługa stacji jest <c>null</c>.</exception>
    public void Observe(
        StationService stations, DriveState state, ProtectionDecision? protection)
    {
        ArgumentNullException.ThrowIfNull(stations);

        if (_result is not null)
        {
            // ZATRZASK. Bez niego wynik przeliczałby się co krok i rósł o czas spędzony
            // na ekranie wyniku, a liczniki ATP — o zdarzenia po zakończeniu sesji.
            return;
        }

        LiczZbocza(protection);

        // Minięcie WYMAGANEGO celu kończy sesję natychmiast: skład nie ma biegu
        // wstecznego, więc żadne późniejsze polecenie tego nie odwróci. Minięcie stacji,
        // która celem nie jest, jest poza zadaniem — patrz `TrainingEnding.TargetMissed`.
        foreach (var minieta in stations.Missed)
        {
            if (_targets.Contains(minieta.StopId))
            {
                Zatrzasnij(TrainingEnding.TargetMissed, stations, state);
                return;
            }
        }

        if (state.SpeedMps > 0.0 || stations.AtStation)
        {
            // „Drzwi zamknięte i skład stoi" (`docs/PLAYABILITY.md` §3). `AtStation`
            // gaśnie dopiero, gdy `StationStop` domknie cykl — czyli to jest ten sam
            // warunek co domknięty wpis wywołania, tylko czytany u źródła.
            return;
        }

        foreach (var id in _targets)
        {
            if (Wywolanie(stations, id) is null)
            {
                return;
            }
        }

        Zatrzasnij(TrainingEnding.AllTargetsServed, stations, state);
    }

    /// <summary>
    /// Sesja od nowa: wynik znika, a razem z nim liczniki zdarzeń i pamięć zboczy.
    ///
    /// <para>Celów ta metoda NIE rusza i to jest wybór: reset znaczy „ta sama sesja od
    /// nowa", a nie „inne zadanie" — dokładnie ta sama granica, co w
    /// <see cref="RunRestart"/> („osi, składu i warunków przejazdu reset nie obejmuje").</para>
    ///
    /// <para><b>Pamięć zboczy wraca do fałszu, a nie zostaje.</b> Gdyby została, pierwsza
    /// ingerencja po resecie nie policzyłaby się — predykat byłby „nadal prawdziwy" od
    /// poprzedniej sesji. Reset obejmuje więc i liczniki, i stan, z którego liczą.</para>
    /// </summary>
    public void Reset()
    {
        _result = null;
        _overspeedHeld = false;
        _interveningHeld = false;
        _emergencyHeld = false;
        _warningEvents = 0;
        _interventionEvents = 0;
        _emergencyEvents = 0;
    }

    private void LiczZbocza(ProtectionDecision? protection)
    {
        // Brak decyzji znaczy „ochrona nic nie mówi", więc wszystkie trzy predykaty są
        // fałszem — a nie „stan z poprzedniego kroku". Inaczej wyłączenie sygnalizacji
        // w połowie przejazdu zamrażałoby zbocze i następna ingerencja nie policzyłaby się.
        var overspeed = protection?.Overspeed ?? false;
        var intervening = protection is { } d && d.Action != ProtectionAction.None;
        var emergency = protection is { } e && e.Action == ProtectionAction.EmergencyIntervention;

        if (overspeed && !_overspeedHeld)
        {
            _warningEvents++;
        }

        if (intervening && !_interveningHeld)
        {
            _interventionEvents++;
        }

        if (emergency && !_emergencyHeld)
        {
            _emergencyEvents++;
        }

        _overspeedHeld = overspeed;
        _interveningHeld = intervening;
        _emergencyHeld = emergency;
    }

    private static StationCall? Wywolanie(StationService stations, string stopId)
    {
        foreach (var call in stations.Calls)
        {
            // `IsFinite`, a NIE `!= double.NaN`. `StationService` wpisuje wywołanie
            // z `DepartureSeconds = double.NaN` już przy ZATRZYMANIU i domyka je dopiero
            // przy ruszeniu. Porównanie `!= double.NaN` jest ZAWSZE prawdziwe, także dla
            // samego NaN, więc cel z otwartymi drzwiami liczyłby się jako obsłużony
            // i wyglądałoby to dokładnie tak samo jak obsłużony naprawdę.
            if (string.Equals(call.StopId, stopId, StringComparison.Ordinal)
                && double.IsFinite(call.DepartureSeconds))
            {
                return call;
            }
        }

        return null;
    }

    private void Zatrzasnij(TrainingEnding ending, StationService stations, DriveState state)
    {
        var targets = new List<TrainingTarget>(_targets.Count);
        foreach (var id in _targets)
        {
            var call = Wywolanie(stations, id);
            targets.Add(new TrainingTarget(
                id,
                _displayNames.TryGetValue(id, out var nazwa) ? nazwa : id,
                call is not null,
                call?.StopErrorM,
                call?.ArrivalSeconds,
                call?.DepartureSeconds));
        }

        _result = new TrainingResult(
            ending,
            targets,
            state.TimeSeconds(_step),
            state.DistanceM,
            _warningEvents,
            _interventionEvents,
            _emergencyEvents);
    }
}
