using System;
using System.Collections.Generic;
using System.Globalization;
using System.Text;
using MetroBxl.Sim.Line;

namespace MetroBxl.Sim.Signalling;

/// <summary>
/// Klasyczna sygnalizacja blokowa: zajętość, ryglowanie tras i movement authority.
///
/// <para><b>Co ta klasa robi.</b> Trzyma stan ryglowania — który blok jest zajęty, przez
/// kogo, pod którą trasę zarezerwowany — i odpowiada na jedno pytanie: dokąd wolno
/// jechać temu składowi. Każda zmiana stanu wychodzi jako
/// <see cref="SignallingEvent"/>. To jest cały jej kontrakt.</para>
///
/// <para><b>Czego ta klasa nie robi</b> (zasada 6 z T-313 i reguła 9 z <c>CLAUDE.md</c>):
/// nie prowadzi składu, nie liczy fizyki, nie wie o Godocie, nie ma zegara i nie ma
/// pojęcia „krok symulacji". Ruch dostaje z zewnątrz jako nowy chainage czoła.</para>
///
/// <para><b>Dlaczego ruch wchodzi jako pozycja, a nie jako <c>dt</c>.</b> Bo tylko wtedy
/// da się obronić przed przeskoczeniem bloku. <see cref="MoveTrain"/> nie patrzy na to,
/// gdzie skład jest **teraz** — patrzy na cały odcinek, który zamiótł od poprzedniego
/// wywołania: od dawnego tyłu do nowego czoła. Skok o 400 m w jednym wywołaniu zajmuje
/// i zwalnia po drodze każdy blok, a wjazd w blok cudzy zostaje zgłoszony, nawet jeżeli
/// na końcu skoku skład jest już z tego bloku wyjechany. Krok czasowy może więc być
/// dowolnie długi i model dalej nie przepuści składu przez zajęty blok po cichu.</para>
///
/// <para><b>Determinizm.</b> Bloki i składy są przeglądane po indeksie tablicy, nigdy po
/// iteracji słownika; porównania łańcuchów są <see cref="StringComparison.Ordinal"/>;
/// zdarzenia numeruje licznik całkowity. Ten sam ciąg wywołań daje ten sam strumień
/// zdarzeń i ten sam <see cref="StateDigest"/>, a <see cref="Replay"/> odtwarza z tego
/// strumienia identyczny stan ryglowania.</para>
/// </summary>
public sealed class FixedBlockSystem
{
    private sealed class TrainRecord
    {
        public TrainRecord(string id, double lengthM, double frontM)
        {
            Id = id;
            LengthM = lengthM;
            FrontM = frontM;
        }

        public string Id { get; }

        public double LengthM { get; }

        public double FrontM { get; set; }

        public string? RouteId { get; set; }

        public MovementAuthority? LastAuthority { get; set; }
    }

    private readonly SignallingPlan _plan;
    private readonly string?[] _occupant;
    private readonly string?[] _reservedBy;
    private readonly List<TrainRecord> _trains = new();
    private readonly List<string> _lockedRoutes = new();
    private readonly List<SignallingEvent> _events = new();
    private long _sequence;

    /// <summary>Pusty system dla zadanego planu: wszystkie bloki wolne, żadnego składu.</summary>
    public FixedBlockSystem(SignallingPlan plan)
    {
        ArgumentNullException.ThrowIfNull(plan);
        _plan = plan;
        _occupant = new string?[plan.Blocks.Count];
        _reservedBy = new string?[plan.Blocks.Count];
    }

    /// <summary>Plan, na którym stoi ten system.</summary>
    public SignallingPlan Plan => _plan;

    /// <summary>Strumień zdarzeń od utworzenia systemu, w kolejności emisji.</summary>
    public IReadOnlyList<SignallingEvent> Events => _events;

    /// <summary>Identyfikatory składów w kolejności wprowadzenia.</summary>
    public IReadOnlyList<string> TrainIds
    {
        get
        {
            var ids = new string[_trains.Count];
            for (var i = 0; i < _trains.Count; i++)
            {
                ids[i] = _trains[i].Id;
            }

            return ids;
        }
    }

    /// <summary>Identyfikatory zaryglowanych tras w kolejności ryglowania.</summary>
    public IReadOnlyList<string> LockedRoutes => _lockedRoutes;

    // --- odczyt stanu --------------------------------------------------------------

    /// <summary>Stan bloku o zadanym identyfikatorze.</summary>
    public BlockState StateOf(string blockId)
    {
        var index = _plan.IndexOf(blockId);
        if (_occupant[index] is not null)
        {
            return BlockState.Occupied;
        }

        return _reservedBy[index] is not null ? BlockState.Reserved : BlockState.Clear;
    }

    /// <summary>Skład zajmujący blok albo <c>null</c>.</summary>
    public string? OccupantOf(string blockId) => _occupant[_plan.IndexOf(blockId)];

    /// <summary>Trasa, pod którą blok jest zarezerwowany, albo <c>null</c>.</summary>
    public string? ReservationOf(string blockId) => _reservedBy[_plan.IndexOf(blockId)];

    /// <summary>Trasa prowadząca skład albo <c>null</c>.</summary>
    public string? RouteOf(string trainId) => Require(trainId).RouteId;

    /// <summary>Chainage czoła składu.</summary>
    public double FrontOf(string trainId) => Require(trainId).FrontM;

    /// <summary>
    /// Mutable runtime fields omitted by StateDigest, whose narrower contract is
    /// replayable block/route state. LastAuthority controls future event emission.
    /// </summary>
    internal void AppendRuntimeState(StateHashWriter hash)
    {
        hash.Add(_sequence);
        hash.Add(_trains.Count);
        foreach (var train in _trains)
        {
            hash.Add(train.Id);
            hash.Add(train.LengthM);
            hash.Add(train.FrontM);
            hash.Add(train.RouteId);
            hash.Add(train.LastAuthority.HasValue);
            if (train.LastAuthority is { } authority)
            {
                hash.Add(authority.TrainId);
                hash.Add(authority.FrontChainageM);
                hash.Add(authority.EndChainageM);
                hash.Add(authority.LimitBlockId);
                hash.Add((long)authority.Reason);
            }
        }
    }

    /// <summary>Chainage tyłu składu, przycięty do planu.</summary>
    public double RearOf(string trainId)
    {
        var train = Require(trainId);
        return Clamp(train.FrontM - train.LengthM);
    }

    /// <summary>Bloki zajęte przez zadany skład, w kolejności chainage.</summary>
    public IReadOnlyList<string> BlocksOccupiedBy(string trainId)
    {
        var train = Require(trainId);
        var occupied = new List<string>(2);
        for (var i = 0; i < _occupant.Length; i++)
        {
            if (string.Equals(_occupant[i], train.Id, StringComparison.Ordinal))
            {
                occupied.Add(_plan.Blocks[i].Id);
            }
        }

        return occupied;
    }

    /// <summary>
    /// Trasa, o którą ten skład ma prawo poprosić: pierwsza wychodząca z bloku, który
    /// skład ZAJMUJE, licząc od ogona w stronę czoła. <c>null</c>, gdy z żadnego
    /// zajętego bloku trasa nie wychodzi.
    ///
    /// <para><b>Po co „z bloku, który zajmuje", a nie „z bloku, w którym jest czoło".</b>
    /// Bo skład M7 ma 94 m i blok peronowy ma dokładnie tyle samo — więc skład stojący
    /// przy peronie NIGDY nie mieści się w jednym bloku. Do 05.09.2026 nie miało to
    /// znaczenia, bo jedyny wołający (<see cref="Line.LineCore"/>) wstawia skład na plan
    /// z czołem dokładnie na kilometrażu pierwszej stacji, czyli w bloku peronowym.
    /// Kabina prowadzona ręcznie zaczyna przejazd z czołem na 94,000 m — bo cały skład
    /// ma stać na osi (<c>DriveScenario.PackageAFirstRun</c>) — a to na pakiecie A jest
    /// już blok SZLAKOWY <c>S01</c>. Zmierzone: nastawnia nie zamawiała wtedy ANI JEDNEJ
    /// trasy, autorytet kończył się na 462,730 m z powodem <c>BlockNotReserved</c>,
    /// a ochrona hamowała skład awaryjnie przez 1998 kroków, zanim ten dojechał do
    /// pierwszej stacji. Skład stał wtedy ogonem w <c>P01</c> — czyli w bloku
    /// początkowym trasy <c>R01</c> — i to jest dokładnie ten sam blok, który
    /// <c>docs/15-classic-signalling.md</c> §6 nazywa blokiem, w którym skład
    /// „stoi".</para>
    ///
    /// <para><b>Ta metoda niczego nie rozluźnia.</b> Warunek dalej brzmi „skład jest
    /// fizycznie w bloku początkowym trasy" — zmienia się wyłącznie to, że zajętość
    /// liczy się po CAŁYM składzie, a nie po jednym punkcie. Zaryglowanie przebiegu
    /// „po drugiej stronie linii" jest tak samo niemożliwe jak przedtem, bo blok
    /// niezajęty przez ten skład nie wejdzie do tej pętli.</para>
    ///
    /// <para>Kolejność od ogona jest treścią: trasa wychodząca z bloku bliżej ogona
    /// obejmuje CAŁY skład, a trasa z bloku bliżej czoła zostawiłaby ogon poza
    /// rezerwacją.</para>
    /// </summary>
    /// <param name="trainId">Skład zarejestrowany na planie.</param>
    /// <returns>Trasa do zamówienia albo <c>null</c>.</returns>
    public Route? NextRouteForTrain(string trainId)
    {
        var train = Require(trainId);
        for (var i = 0; i < _occupant.Length; i++)
        {
            if (!string.Equals(_occupant[i], train.Id, StringComparison.Ordinal))
            {
                continue;
            }

            if (_plan.RouteOutOf(_plan.Blocks[i].Id) is Route route)
            {
                return route;
            }
        }

        return null;
    }

    // --- składy --------------------------------------------------------------------

    /// <summary>
    /// Wprowadza skład na plan. Odmowa jest wyjątkiem, a nie zdarzeniem: postawienie
    /// składu na zajętym bloku to błąd scenariusza, a nie sytuacja ruchowa.
    /// </summary>
    /// <param name="trainId">Identyfikator składu; musi być nowy.</param>
    /// <param name="frontChainageM">Chainage czoła.</param>
    /// <param name="lengthM">Długość składu.</param>
    public void RegisterTrain(string trainId, double frontChainageM, double lengthM)
    {
        ArgumentNullException.ThrowIfNull(trainId);
        if (!double.IsFinite(frontChainageM))
        {
            throw new ArgumentOutOfRangeException(nameof(frontChainageM), frontChainageM, "Chainage musi być skończony.");
        }

        if (!double.IsFinite(lengthM) || lengthM <= 0.0)
        {
            throw new ArgumentOutOfRangeException(nameof(lengthM), lengthM, "Długość składu musi być dodatnia i skończona.");
        }

        foreach (var existing in _trains)
        {
            if (string.Equals(existing.Id, trainId, StringComparison.Ordinal))
            {
                throw new ArgumentException($"skład {trainId} jest już na planie", nameof(trainId));
            }
        }

        var front = Clamp(frontChainageM);
        var rear = Clamp(frontChainageM - lengthM);
        for (var i = 0; i < _occupant.Length; i++)
        {
            if (_plan.Blocks[i].Overlaps(rear, front) &&
                _occupant[i] is string other &&
                !string.Equals(other, trainId, StringComparison.Ordinal))
            {
                throw new InvalidOperationException(
                    $"blok {_plan.Blocks[i].Id} jest zajęty przez {other} — nie da się tam wstawić {trainId}");
            }
        }

        var train = new TrainRecord(trainId, lengthM, front);
        _trains.Add(train);
        Emit(SignallingEventKind.TrainRegistered, trainId, trainId, front,
            string.Create(CultureInfo.InvariantCulture, $"length_m={lengthM:R}"));

        for (var i = 0; i < _occupant.Length; i++)
        {
            if (_plan.Blocks[i].Overlaps(rear, front) && _occupant[i] is null)
            {
                _occupant[i] = trainId;
                Emit(SignallingEventKind.BlockOccupied, _plan.Blocks[i].Id, trainId, front, string.Empty);
            }
        }

        PublishAuthorities();
    }

    /// <summary>
    /// Wypisuje skład z planu: zwalnia jego trasę i wszystkie zajęte przez niego bloki.
    ///
    /// <para><b>Po co to istnieje.</b> Do 04.09.2026 składu nie dało się z planu zdjąć.
    /// Skład, który dojechał do ostatniego peronu, trzymał go NA ZAWSZE — a dwie kolejne
    /// trasy dzielą blok peronowy, więc następny skład nie miał jak zaryglować ostatniej.
    /// Zmierzone na pakiecie A przed tą zmianą: drugi skład stawał na 5514,04 m, za
    /// Schumanem, i nie dojeżdżał do Merode nigdy.</para>
    ///
    /// <para><b>Co to NIE jest.</b> Nie jest to jazda w przeciwną stronę. Oś pakietu
    /// biegnie w jednym kierunku i <see cref="MoveTrain"/> odmawia cofnięcia czoła;
    /// przeciwny kierunek to OSOBNA oś (pakiet A ma parę w pakiecie B). Wypisanie składu
    /// znaczy dosłownie „ten pojazd zniknął z tego planu" i nic więcej — co z nim dalej,
    /// rozstrzyga wołający.</para>
    ///
    /// <para>Wypisanie składu, którego nie ma, jest wyjątkiem, a nie ciszą: pomyłka
    /// w identyfikatorze wyglądałaby wtedy jak udane wypisanie.</para>
    /// </summary>
    /// <param name="trainId">Skład do wypisania.</param>
    public void ReleaseTrain(string trainId)
    {
        var train = Require(trainId);
        var chainage = train.FrontM;

        if (train.RouteId is string routeId)
        {
            ReleaseRoute(routeId);
        }

        for (var i = 0; i < _occupant.Length; i++)
        {
            if (string.Equals(_occupant[i], trainId, StringComparison.Ordinal))
            {
                _occupant[i] = null;
                Emit(SignallingEventKind.BlockReleased, _plan.Blocks[i].Id, trainId, chainage, string.Empty);
            }
        }

        _trains.Remove(train);
        Emit(SignallingEventKind.TrainDeregistered, trainId, trainId, chainage, string.Empty);
        PublishAuthorities();
    }

    /// <summary>
    /// Przesuwa czoło składu do zadanego chainage i uzgadnia zajętość na **całym**
    /// zamiecionym odcinku.
    ///
    /// <para>Kolejność jest istotna i jest taka: kontrola authority sprzed ruchu →
    /// zajęcie bloków po drodze → przesunięcie składu → zwolnienie bloków za tyłem →
    /// zwolnienie trasy, gdy zrobiła swoje → publikacja authority.</para>
    /// </summary>
    /// <param name="trainId">Skład.</param>
    /// <param name="frontChainageM">Nowy chainage czoła; nie może być mniejszy od dotychczasowego.</param>
    public void MoveTrain(string trainId, double frontChainageM)
    {
        var train = Require(trainId);
        if (!double.IsFinite(frontChainageM))
        {
            throw new ArgumentOutOfRangeException(nameof(frontChainageM), frontChainageM, "Chainage musi być skończony.");
        }

        if (frontChainageM < train.FrontM - TrackAxis.PositionEpsilonM)
        {
            throw new ArgumentOutOfRangeException(
                nameof(frontChainageM), frontChainageM, string.Create(
                    CultureInfo.InvariantCulture,
                    $"skład {trainId} miałby cofnąć się z {train.FrontM:F3} m — model nie odtacza składów w tył " +
                    $"(TrainController obcina prędkość do zera), więc ruch wstecz jest błędem wołającego"));
        }

        var authority = ComputeAuthority(train);
        var target = Clamp(frontChainageM);
        if (target > authority.EndChainageM + TrackAxis.PositionEpsilonM)
        {
            Emit(SignallingEventKind.AuthorityViolation, authority.LimitBlockId, trainId, target,
                string.Create(CultureInfo.InvariantCulture,
                    $"authority-end={authority.EndChainageM:F3};reason={authority.Reason}"));
        }

        var sweptFrom = Clamp(train.FrontM - train.LengthM);
        for (var i = 0; i < _occupant.Length; i++)
        {
            if (!_plan.Blocks[i].Overlaps(sweptFrom, target))
            {
                continue;
            }

            if (_occupant[i] is null)
            {
                _occupant[i] = trainId;
                Emit(SignallingEventKind.BlockOccupied, _plan.Blocks[i].Id, trainId, target, string.Empty);
            }
            else if (!string.Equals(_occupant[i], trainId, StringComparison.Ordinal))
            {
                // Wjazd w blok cudzy. Zajętość zostaje przy tamtym składzie — intruz jej
                // nie przejmuje — a zdarzenie zostaje w strumieniu na zawsze.
                Emit(SignallingEventKind.AuthorityViolation, _plan.Blocks[i].Id, trainId, target,
                    "occupied-by=" + _occupant[i]);
            }
        }

        train.FrontM = target;
        var rear = Clamp(target - train.LengthM);
        for (var i = 0; i < _occupant.Length; i++)
        {
            if (string.Equals(_occupant[i], trainId, StringComparison.Ordinal) &&
                !_plan.Blocks[i].Overlaps(rear, target))
            {
                _occupant[i] = null;
                Emit(SignallingEventKind.BlockReleased, _plan.Blocks[i].Id, trainId, target, string.Empty);
            }
        }

        ReleaseCompletedRoute(train);
        PublishAuthorities();
    }

    // --- trasy ---------------------------------------------------------------------

    /// <summary>
    /// Żądanie trasy. Odmowa **nie jest wyjątkiem** — jest normalną sytuacją ruchową
    /// i wychodzi jako <see cref="SignallingEventKind.RouteRejected"/> z powodem.
    /// </summary>
    /// <returns><c>true</c>, gdy trasa została zaryglowana.</returns>
    public bool RequestRoute(string routeId, string trainId)
    {
        var train = Require(trainId);
        var route = _plan.RouteById(routeId);
        Emit(SignallingEventKind.RouteRequested, route.Id, trainId, train.FrontM, string.Empty);

        var reject = RejectionReason(route, train);
        if (reject is not null)
        {
            Emit(SignallingEventKind.RouteRejected, route.Id, trainId, train.FrontM, reject);
            return false;
        }

        foreach (var blockId in route.BlockIds)
        {
            var index = _plan.IndexOf(blockId);
            if (_reservedBy[index] is null)
            {
                _reservedBy[index] = route.Id;
                Emit(SignallingEventKind.BlockReserved, blockId, trainId, train.FrontM, route.Id);
            }
        }

        _lockedRoutes.Add(route.Id);
        train.RouteId = route.Id;
        Emit(SignallingEventKind.RouteLocked, route.Id, trainId, train.FrontM, string.Empty);
        PublishAuthorities();
        return true;
    }

    /// <summary>Zwalnia trasę i zdejmuje jej rezerwacje. Zwolnienie trasy niezaryglowanej nic nie robi.</summary>
    public void ReleaseRoute(string routeId)
    {
        var route = _plan.RouteById(routeId);
        if (!_lockedRoutes.Remove(route.Id))
        {
            return;
        }

        string trainId = string.Empty;
        double chainage = 0.0;
        foreach (var train in _trains)
        {
            if (string.Equals(train.RouteId, route.Id, StringComparison.Ordinal))
            {
                train.RouteId = null;
                trainId = train.Id;
                chainage = train.FrontM;
            }
        }

        foreach (var blockId in route.BlockIds)
        {
            var index = _plan.IndexOf(blockId);
            if (string.Equals(_reservedBy[index], route.Id, StringComparison.Ordinal))
            {
                _reservedBy[index] = null;
                Emit(SignallingEventKind.BlockReservationReleased, blockId, trainId, chainage, route.Id);
            }
        }

        Emit(SignallingEventKind.RouteReleased, route.Id, trainId, chainage, string.Empty);
        PublishAuthorities();
    }

    // --- movement authority ---------------------------------------------------------

    /// <summary>
    /// Movement authority dla składu. Funkcja czysta: nie zmienia stanu i nie emituje
    /// zdarzeń. Zdarzenie <see cref="SignallingEventKind.AuthorityIssued"/> powstaje
    /// wtedy, gdy authority faktycznie się zmieni — czyli po zmianie stanu, a nie po
    /// zapytaniu o niego.
    /// </summary>
    public MovementAuthority Authority(string trainId) => ComputeAuthority(Require(trainId));

    /// <summary>
    /// Dopisuje do strumienia zdarzenie, które jest **wynikiem**, a nie zmianą stanu
    /// ryglowania: ostrzeżenie o prędkości, ingerencję, zwolnienie albo blokadę drzwi.
    ///
    /// <para>Istnieje po to, żeby <see cref="TrainProtection"/> pisało do tego samego
    /// zapisu, co system blokowy — kabina i dispatcher mają widzieć jeden strumień, a nie
    /// dwa, które trzeba scalać po czasie, którego sygnalizacja nie ma.
    /// <see cref="Replay"/> te zdarzenia pomija, bo stanu nie zmieniają.</para>
    /// </summary>
    public void Report(SignallingEventKind kind, string subjectId, string trainId, double chainageM, string detail)
    {
        ArgumentNullException.ThrowIfNull(subjectId);
        ArgumentNullException.ThrowIfNull(trainId);
        ArgumentNullException.ThrowIfNull(detail);
        if (kind is SignallingEventKind.TrainRegistered
            or SignallingEventKind.BlockOccupied
            or SignallingEventKind.BlockReleased
            or SignallingEventKind.BlockReserved
            or SignallingEventKind.BlockReservationReleased
            or SignallingEventKind.RouteLocked
            or SignallingEventKind.RouteReleased)
        {
            throw new ArgumentOutOfRangeException(
                nameof(kind), kind,
                "Zdarzenia zmieniające stan ryglowania emituje sam system blokowy — " +
                "wpuszczenie ich z zewnątrz rozjechałoby stan z zapisem.");
        }

        Emit(kind, subjectId, trainId, chainageM, detail);
    }

    // --- odcisk stanu i odtworzenie --------------------------------------------------

    /// <summary>
    /// Odcisk stanu ryglowania: bloki, rezerwacje, zaryglowane trasy i przypisanie tras
    /// do składów.
    ///
    /// <para><b>Czego w odcisku celowo nie ma:</b> położenia i prędkości składów. To nie
    /// jest stan sygnalizacji — to stan rdzenia fizyki, który ma własny test determinizmu
    /// (<c>DeterminismTests</c>). Sygnalizacja odpowiada za to, co sama trzyma, i tyle
    /// odtwarza <see cref="Replay"/>.</para>
    /// </summary>
    public string StateDigest()
    {
        var text = new StringBuilder();
        text.Append("plan=").Append(_plan.PlanId);
        for (var i = 0; i < _occupant.Length; i++)
        {
            text.Append(";b:").Append(_plan.Blocks[i].Id).Append('=')
                .Append(StateOf(_plan.Blocks[i].Id))
                .Append('/').Append(_occupant[i] ?? "-")
                .Append('/').Append(_reservedBy[i] ?? "-");
        }

        foreach (var route in _lockedRoutes)
        {
            text.Append(";r:").Append(route);
        }

        foreach (var train in _trains)
        {
            text.Append(";t:").Append(train.Id).Append('=').Append(train.RouteId ?? "-");
        }

        return text.ToString();
    }

    /// <summary>
    /// Odtwarza stan ryglowania z zapisanego strumienia zdarzeń.
    ///
    /// <para>Zdarzenia nadzoru prędkości i drzwi są **wynikami**, nie stanem, więc
    /// odtworzenie ich pomija. Stan zmieniają wyłącznie zdarzenia zajętości, rezerwacji
    /// i cyklu życia trasy — i to one muszą wystarczyć, żeby po restarcie
    /// <see cref="StateDigest"/> wyszedł identyczny.</para>
    /// </summary>
    public static FixedBlockSystem Replay(SignallingPlan plan, IEnumerable<SignallingEvent> events)
    {
        ArgumentNullException.ThrowIfNull(plan);
        ArgumentNullException.ThrowIfNull(events);

        var system = new FixedBlockSystem(plan);
        var stream = new List<SignallingEvent>(events);
        foreach (var entry in stream)
        {
            switch (entry.Kind)
            {
                case SignallingEventKind.TrainRegistered:
                    system._trains.Add(new TrainRecord(entry.TrainId, LengthFrom(entry.Detail), entry.ChainageM));
                    break;
                case SignallingEventKind.BlockOccupied:
                    system._occupant[plan.IndexOf(entry.SubjectId)] = entry.TrainId;
                    break;
                case SignallingEventKind.BlockReleased:
                    system._occupant[plan.IndexOf(entry.SubjectId)] = null;
                    break;
                case SignallingEventKind.BlockReserved:
                    system._reservedBy[plan.IndexOf(entry.SubjectId)] = entry.Detail;
                    break;
                case SignallingEventKind.BlockReservationReleased:
                    system._reservedBy[plan.IndexOf(entry.SubjectId)] = null;
                    break;
                case SignallingEventKind.RouteLocked:
                    system._lockedRoutes.Add(entry.SubjectId);
                    var routed = system.FindOrNull(entry.TrainId);
                    if (routed is not null)
                    {
                        routed.RouteId = entry.SubjectId;
                    }

                    break;
                case SignallingEventKind.RouteReleased:
                    system._lockedRoutes.Remove(entry.SubjectId);
                    foreach (var train in system._trains)
                    {
                        if (string.Equals(train.RouteId, entry.SubjectId, StringComparison.Ordinal))
                        {
                            train.RouteId = null;
                        }
                    }

                    break;
                default:
                    break;
            }

            system._events.Add(entry);
            system._sequence = entry.Sequence + 1;
        }

        // Czoła składów odtwarzamy z tych zdarzeń, które niosą **położenie składu**:
        // wprowadzenia na plan oraz zajęcia i zwolnienia bloku. AuthorityIssued niesie
        // koniec authority, a nie czoło, więc wzięcie go tutaj przesunęłoby skład do
        // przodu o całą wolną drogę. Między zdarzeniami zajętości czoło nie jest częścią
        // stanu sygnalizacji i odtworzenie zna je z dokładnością do ostatniej zmiany
        // zajętości — dlatego nie wchodzi do StateDigest.
        foreach (var entry in stream)
        {
            if (entry.Kind is not (SignallingEventKind.TrainRegistered
                or SignallingEventKind.BlockOccupied
                or SignallingEventKind.BlockReleased))
            {
                continue;
            }

            var train = system.FindOrNull(entry.TrainId);
            if (train is not null && entry.ChainageM > train.FrontM)
            {
                train.FrontM = entry.ChainageM;
            }
        }

        return system;
    }

    /// <inheritdoc/>
    public override string ToString() => string.Create(
        CultureInfo.InvariantCulture,
        $"{_plan.PlanId}: {_trains.Count} składów, {_lockedRoutes.Count} tras zaryglowanych, " +
        $"{_events.Count} zdarzeń");

    // --- wnętrze ---------------------------------------------------------------------

    private MovementAuthority ComputeAuthority(TrainRecord train)
    {
        // Blok, w którym stoi czoło — ale liczony po **zajętości**, nie po samym punkcie.
        // Przy półotwartej konwencji chainage dokładnie na granicy należy już do bloku
        // następnego, którego skład jeszcze nie zajmuje; wyjście z niego dawałoby
        // authority przez blok, do którego skład dopiero ma prawo wjechać — a w skrajnym
        // przypadku przez blok zajęty przez kogoś innego.
        var rear = Clamp(train.FrontM - train.LengthM);
        var front = Clamp(train.FrontM);
        var index = _plan.BlockIndexAt(front);
        while (index > 0 && !_plan.Blocks[index].Overlaps(rear, front))
        {
            index--;
        }

        var end = _plan.Blocks[index].EndM;
        var limitBlockId = _plan.Blocks[index].Id;
        var reason = AuthorityLimit.EndOfLine;

        for (var j = index + 1; j < _plan.Blocks.Count; j++)
        {
            if (_occupant[j] is string occupant && !string.Equals(occupant, train.Id, StringComparison.Ordinal))
            {
                limitBlockId = _plan.Blocks[j].Id;
                reason = AuthorityLimit.OccupiedBlock;
                break;
            }

            if (_reservedBy[j] is string reservation &&
                !string.Equals(reservation, train.RouteId, StringComparison.Ordinal))
            {
                limitBlockId = _plan.Blocks[j].Id;
                reason = AuthorityLimit.ReservedByOtherRoute;
                break;
            }

            if (_plan.RequireRoute &&
                (train.RouteId is null || !string.Equals(_reservedBy[j], train.RouteId, StringComparison.Ordinal)))
            {
                limitBlockId = _plan.Blocks[j].Id;
                reason = AuthorityLimit.BlockNotReserved;
                break;
            }

            end = _plan.Blocks[j].EndM;
            limitBlockId = _plan.Blocks[j].Id;
            reason = AuthorityLimit.EndOfLine;
        }

        var endpoint = Math.Max(train.FrontM, end - _plan.AuthorityMarginM);
        return new MovementAuthority(train.Id, train.FrontM, endpoint, limitBlockId, reason);
    }

    private void PublishAuthorities()
    {
        foreach (var train in _trains)
        {
            var authority = ComputeAuthority(train);
            if (train.LastAuthority is MovementAuthority previous &&
                previous.EndChainageM.Equals(authority.EndChainageM) &&
                previous.Reason == authority.Reason &&
                string.Equals(previous.LimitBlockId, authority.LimitBlockId, StringComparison.Ordinal))
            {
                continue;
            }

            train.LastAuthority = authority;
            Emit(SignallingEventKind.AuthorityIssued, authority.LimitBlockId, train.Id, authority.EndChainageM,
                string.Create(CultureInfo.InvariantCulture,
                    $"reason={authority.Reason};distance_m={authority.DistanceM:F3}"));
        }
    }

    private string? RejectionReason(Route route, TrainRecord train)
    {
        if (_lockedRoutes.Contains(route.Id))
        {
            return "route-already-locked";
        }

        if (train.RouteId is string held)
        {
            return "train-already-routed:" + held;
        }

        // Trasa zaczyna się tam, gdzie stoi skład. Bez tego dałoby się zaryglować
        // przebieg po drugiej stronie linii i pojechać po nim „z niczego".
        //
        // „STOI W BLOKU" ZNACZY „ZAJMUJE BLOK", a nie „ma w nim czoło" — i to jest ta
        // sama konwencja, którą stosuje `ComputeAuthority` kilkadziesiąt linii wyżej
        // („liczony po zajętości, nie po samym punkcie"). Powód jest wymiarowy: skład
        // M7 ma 94 m, blok peronowy ma dokładnie tyle samo, więc skład przy peronie
        // nigdy nie mieści się w jednym bloku. Do 05.09.2026 warunek patrzył wyłącznie
        // na czoło i wystarczał, bo jedyny wołający — `LineCore` — wstawia skład
        // z czołem dokładnie na kilometrażu pierwszej stacji. Kabina prowadzona ręcznie
        // zaczyna z czołem na 94,000 m, czyli w bloku SZLAKOWYM S01, mając ogon w P01:
        // nastawnia nie zamawiała wtedy ani jednej trasy, a ochrona hamowała skład
        // awaryjnie przez 1998 kroków, bo autorytet kończył się na 462,730 m.
        // `docs/15-classic-signalling.md` §6 mówi „skład nie stoi w bloku początkowym
        // trasy" — i skład, którego ogon jest w tym bloku, w nim stoi.
        //
        // Warunek jest SUMĄ dwóch, a nie zamianą jednego na drugi, i to jest celowe:
        // stary człon (blok czoła) zostaje nietknięty, więc każde żądanie, które
        // przechodziło przedtem, przechodzi tak samo teraz. Nowy człon może wyłącznie
        // ZAMIENIĆ ODMOWĘ NA ZGODĘ i nigdy odwrotnie — dzięki temu tożsamość przejazdu
        // `--line` nie zależy od tego, w którym dokładnie kroku blok peronowy przechodzi
        // z „czoło w nim jest" na „skład go zajmuje" (`Block.Overlaps` przy czole
        // dokładnie na granicy daje jeszcze fałsz).
        var frontBlockId = _plan.Blocks[_plan.BlockIndexAt(train.FrontM)].Id;
        var entryIndex = _plan.IndexOf(route.FromBlockId);
        var standsAtEntry =
            string.Equals(frontBlockId, route.FromBlockId, StringComparison.Ordinal) ||
            string.Equals(_occupant[entryIndex], train.Id, StringComparison.Ordinal);
        if (!standsAtEntry)
        {
            return "train-not-at-route-entry:" + frontBlockId;
        }

        foreach (var blockId in route.BlockIds)
        {
            var index = _plan.IndexOf(blockId);
            if (_occupant[index] is string occupant && !string.Equals(occupant, train.Id, StringComparison.Ordinal))
            {
                return "block-occupied:" + blockId + ":" + occupant;
            }

            if (_reservedBy[index] is string reservation)
            {
                return "block-reserved:" + blockId + ":" + reservation;
            }
        }

        return null;
    }

    /// <summary>
    /// Trasa zrobiła swoje w chwili, gdy **czoło** składu weszło do jej bloku docelowego.
    ///
    /// <para><b>Dlaczego czoło, a nie cały skład.</b> Bo rezerwacja i zajętość to dwie
    /// różne rzeczy i chronią co innego. Ogon składu wciąż stoi w blokach poprzedzających
    /// i wciąż je **zajmuje** — a zajętość sama z siebie skraca cudze authority i sama
    /// z siebie odrzuca cudze żądanie trasy. Trzymanie rezerwacji do wyjazdu ogona nic
    /// by nie dodało do bezpieczeństwa, a zablokowałoby tor na dłużej, niż wynika
    /// z modelu. Czekanie na cały skład byłoby zresztą nieosiągalne dla bloku peronowego
    /// długości dokładnie jednego składu: skład zatrzymany na środku peronu ma ogon
    /// w bloku poprzednim.</para>
    /// </summary>
    private void ReleaseCompletedRoute(TrainRecord train)
    {
        if (train.RouteId is not string routeId)
        {
            return;
        }

        var last = _plan.BlockById(_plan.RouteById(routeId).ToBlockId);
        if (train.FrontM >= last.StartM - TrackAxis.PositionEpsilonM)
        {
            ReleaseRoute(routeId);
        }
    }

    private void Emit(SignallingEventKind kind, string subjectId, string trainId, double chainageM, string detail) =>
        _events.Add(new SignallingEvent(_sequence++, kind, subjectId, trainId, chainageM, detail));

    private double Clamp(double chainageM) => Math.Clamp(chainageM, _plan.StartM, _plan.EndM);

    private TrainRecord Require(string trainId)
    {
        ArgumentNullException.ThrowIfNull(trainId);
        foreach (var train in _trains)
        {
            if (string.Equals(train.Id, trainId, StringComparison.Ordinal))
            {
                return train;
            }
        }

        throw new KeyNotFoundException($"skład {trainId} nie jest na planie {_plan.PlanId}");
    }

    private TrainRecord? FindOrNull(string trainId)
    {
        foreach (var train in _trains)
        {
            if (string.Equals(train.Id, trainId, StringComparison.Ordinal))
            {
                return train;
            }
        }

        return null;
    }

    private static double LengthFrom(string detail)
    {
        const string prefix = "length_m=";
        if (!detail.StartsWith(prefix, StringComparison.Ordinal))
        {
            throw new FormatException($"zdarzenie TrainRegistered bez długości składu: '{detail}'");
        }

        return double.Parse(detail.AsSpan(prefix.Length), NumberStyles.Float, CultureInfo.InvariantCulture);
    }
}
