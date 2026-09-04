"""Profil luzu wzdłuż CAŁEJ osi i zamiatana obwiednia składu — czysty Python, bez bpy.

`placement.py` mierzy luz dla **jednej** pozycji składu. Tu ta sama miara jest liczona
wzdłuż całej trasy: skład przesuwa się krokiem `DEFAULT_STEP_M`, a dla każdej pozycji
zapisywany jest minimalny luz, bryła i punkt, w którym wypadł, oraz to, czy wiąże
ściana, strop, podłoga czy ścięcie naroża.

Dlaczego osobny moduł, a nie pętla wokół `place_vehicle.py`: naiwny pomiar to
~5400 wierzchołków x ~1350 ramek osi na każdą pozycję. Przy tysiącach pozycji to się
nie policzy w czasie CI. Trzy redukcje, każda z dowodem:

1. **Pasma i otoczka wypukła.** Wierzchołki o tym samym X pojazdu leżą w jednym
   przekroju prostopadłym do bryły, więc do luzu liczy się wyłącznie otoczka wypukła
   ich rzutu na (Y, Z). Wierzchołek w środku otoczki nie może być ekstremalny w żadnym
   kierunku. Redukcja 5408 -> ~800 kandydatów; `--verify-full` w `profile_vehicle.py`
   porównuje to z pełnym przebiegiem po wszystkich wierzchołkach.
2. **Współczynniki na pasmo, nie na wierzchołek.** Offsety liczy się z rozwinięcia
   afinicznego transformacji sztywnej, a iloczyny skalarne ramki liczy się raz na
   pasmo. Ramka jest jednak wybierana **dla każdego wierzchołka osobno**, spośród
   `FRAME_CANDIDATES` ramek wokół pasma — jedna ramka na całe pasmo wystarczała do
   0,1 mm na prostej, ale na łuku pakietu A gubiła 3,7 mm, bo sąsiednie pierścienie
   są 5 m od siebie i widzą inny fragment krzywej. Wynik jest identyczny z
   `placement.local_offsets`, co utrwala test
   `test_clearance_profile_offsets_match_placement`.
3. **Luz jako minimum półpłaszczyzn.** Profil tunelu jest wypukły, a wielokąt wypukły
   to przekrój półpłaszczyzn. Dla punktu WEWNĄTRZ odległość od brzegu = minimum
   odległości od prostych podpierających, więc zamiast liczyć odległość od sześciu
   odcinków wystarczy sześć iloczynów skalarnych. Dla punktu na zewnątrz wzór nie
   obowiązuje i moduł wraca do `placement.distance_to_boundary`. Zgodność obu dróg
   utrwala `test_clearance_profile_halfplane_clearance_matches_distance_to_boundary`.

Zamiatana obwiednia (`SweptEnvelope`) to **inna bryła niż `--envelope-out`
z `m7_shell.py`**: tamta jest statyczną skrajnią prostego składu na prostej, ta jest
objętością, którą skład rzeczywiście zajmuje przejeżdżając łuk.
"""
import bisect
import math

import placement as PL
import profiles
import sweep as SW

# --- design_assumption: parametry pomiaru, nie dane o sieci -------------------
# Krok przesuwania składu. Oś źródłowa STIB to łamana o kroku ~15 m, zagęszczana
# Catmull-Romem do pierścieni co 5 m, więc geometria nie zawiera informacji o skali
# drobniejszej niż 5 m i siatka równomierna 5 m jest najgęstszą, która jeszcze coś
# mierzy, a nie interpoluje. Sam krok 5 m nie wystarcza do znalezienia dołka —
# dlatego po skanie zgrubnym idzie doszlifowanie krokiem DEFAULT_REFINE_STEP_M
# wokół każdego dołka. Zmierzone na pakiecie A: siatka 5 m + doszlifowanie i siatka
# 2 m + doszlifowanie dają IDENTYCZNE minimum 0,899948 m, a samo doszlifowanie
# obniża minimum o 3,194 mm wobec siatki zgrubnej. Krok 5 m zamiast 2 m to 2,5x
# krótszy czas CI przy tym samym wyniku.
DEFAULT_STEP_M = 5.0
# Doszlifowanie wokół dołków: krok, pasmo wyboru dołków i połowa szerokości okna.
DEFAULT_REFINE_STEP_M = 0.25
DEFAULT_REFINE_BAND_M = 0.050
DEFAULT_REFINE_HALF_WINDOW_M = 4.0
# Szerokość pasma X przy budowie kandydatów. 0 = pasma dokładne (grupowanie po
# identycznym X), i tylko one są BEZSTRATNE: wierzchołki o tym samym X mają tę samą
# ramkę, więc luz jest funkcją afiniczną (Y, Z) i minimum leży na otoczce wypukłej.
# Kubełkowanie po 0,5 m daje 794 kandydatów zamiast 1306 i jest o 40 % szybsze, ale
# na torze 0 pakietu A gubi 0,78 mm, a po 1,0 m — 3,4 mm. Domyślnie liczymy dokładnie.
CANDIDATE_BUCKET_M = 0.0
# Okno przeszukiwania ramek wokół szacowanego chainage pasma.
FRAME_WINDOW_M = 12.0
# Ile ramek wokół pasma bierze pod uwagę wybór ramki dla pojedynczego wierzchołka.
# 1 (ramka wspólna dla pasma) gubi na łuku 3,7 mm; 3 zgadza się z `local_offsets`
# co do bitu na wszystkich sprawdzonych pozycjach.
FRAME_CANDIDATES = 3
# Odstęp chainage, powyżej którego dwa punkty pod progiem to dwa różne miejsca.
# Nieco więcej niż cięciwa najdłuższej bryły M7 (15,12 m), żeby jeden ciasny łuk
# nie rozpadł się na kilkanaście wpisów w raporcie.
CRITICAL_CLUSTER_GAP_M = 25.0
# Progi raportowania luzu. 0,30 m NIE jest nowym założeniem — to `profiles.CLEARANCE_M`,
# czyli projektowy luz skrajni pojazdu, który już jest w repozytorium. Pozostałe progi
# są okrągłymi pasmami do czytania profilu i nie mają statusu wymiaru projektowego.
DEFAULT_THRESHOLDS_M = (1.000, 0.950, 0.900, 0.500, profiles.CLEARANCE_M, 0.0)
# Liczba kierunków podparcia przy budowie przekroju zamiatanej obwiedni.
SWEPT_DIRECTIONS = 32
# Domyślny zakres zamiatanej obwiedni: +/- 150 m wokół najgorszej pozycji.
DEFAULT_SWEPT_HALF_RANGE_M = 150.0

CONVEXITY_EPS = 1e-9


# --- kandydaci: pasma X i otoczka wypukła przekroju --------------------------

def hull_2d(points):
    """Otoczka wypukła zbioru punktów 2D (monotone chain), przeciwnie do zegara."""
    pts = sorted(set(points))
    if len(pts) <= 2:
        return list(pts)

    def turn(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower = []
    for point in pts:
        while len(lower) >= 2 and turn(lower[-2], lower[-1], point) <= 0.0:
            lower.pop()
        lower.append(point)
    upper = []
    for point in reversed(pts):
        while len(upper) >= 2 and turn(upper[-2], upper[-1], point) <= 0.0:
            upper.pop()
        upper.append(point)
    return lower[:-1] + upper[:-1]


def candidate_bands(vertices, bucket_m=CANDIDATE_BUCKET_M):
    """Wierzchołki bryły pogrupowane w pasma X, z otoczką wypukłą rzutu na (Y, Z).

    Zwraca listę `{"x": środek pasma, "points": [(x, y, z), ...]}` posortowaną po X.
    Punkt wewnątrz otoczki swojego pasma nie jest ekstremalny w żadnym kierunku
    poprzecznym, więc nie może wyznaczyć ani minimalnego luzu, ani obrysu obwiedni.
    """
    groups = {}
    for vertex in vertices:
        key = vertex[0] if bucket_m <= 0.0 else int(math.floor(vertex[0] / bucket_m))
        groups.setdefault(key, []).append(tuple(vertex))
    bands = []
    for key in sorted(groups):
        group = groups[key]
        keep = set(hull_2d([(v[1], v[2]) for v in group]))
        seen = set()
        points = []
        for vertex in group:
            flat = (vertex[1], vertex[2])
            if flat in keep and flat not in seen:
                seen.add(flat)
                points.append(vertex)
        bands.append({"x": sum(v[0] for v in points) / len(points), "points": points})
    return bands


def reduce_bodies(bodies, bucket_m=CANDIDATE_BUCKET_M):
    """`[{"name", "span", "vertices"}]` -> to samo z `bands` zamiast wszystkich wierzchołków."""
    out = []
    for body in bodies:
        vertices = body["vertices"]
        span = body.get("span") or (min(v[0] for v in vertices), max(v[0] for v in vertices))
        out.append({"name": body["name"], "span": (float(span[0]), float(span[1])),
                    "bands": candidate_bands(vertices, bucket_m),
                    "vertex_count": len(vertices)})
    out.sort(key=lambda b: b["span"][0])
    return out


def candidate_count(reduced):
    return sum(len(band["points"]) for body in reduced for band in body["bands"])


# --- profil tunelu jako przekrój półpłaszczyzn -------------------------------

WALL = "ściana"
ROOF = "strop"
FLOOR = "podłoga"
CHAMFER = "ścięcie naroża stropu"


def halfplanes(ring):
    """Półpłaszczyzny wypukłego obrysu: `(nx, ny, c, etykieta)` z normalną DO WNĘTRZA.

    Luz punktu wewnątrz = `min(nx*x + ny*y - c)`. Rzuca `ValueError`, gdy obrys nie
    jest wypukły — wtedy tożsamość „odległość od brzegu = minimum po prostych"
    nie obowiązuje i trzeba użyć `placement.distance_to_boundary`.
    """
    count = len(ring)
    if count < 3:
        raise ValueError("obrys profilu musi mieć co najmniej 3 punkty")
    area2 = 0.0
    for a, b in zip(ring, ring[1:] + ring[:1]):
        area2 += a[0] * b[1] - b[0] * a[1]
    # Pierścień o zerowym polu NIE JEST obrysem — jest odcinkiem albo punktem.
    # Odmowa, tak samo jak dla zerowej krawędzi niżej, bo dalej cała tożsamość
    # „luz = minimum po półpłaszczyznach" traci sens: wnętrza nie ma, więc luz
    # każdego punktu wychodzi niedodatni, a etykieta wiążącej krawędzi jest losowa.
    # Decyzja właściciela, pozycja 12 w `docs/24-clearance-profile-decisions.md`.
    #
    # PRÓG TO ISTNIEJĄCY `CONVEXITY_EPS`, nie nowa stała, i nie jest to wygoda.
    # `area2 == 0.0` byłoby DEKORACJĄ: zmierzone 04.09.2026 na 200 000 losowych
    # trójkach współliniowych — 63,46 % z nich daje `area2` różne od zera przez
    # zaokrąglenie (największe |area2| 2,183e-11), więc dokładne porównanie
    # przepuszczałoby prawie dwie trzecie prawdziwie zdegenerowanych wejść.
    # Rozdzielenie zmierzone z OBU stron: wejścia współliniowe siedzą 1,7 rzędu
    # PONIŻEJ progu, najmniejszy obrys, który ten zestaw każe przyjąć (trójkąt
    # 0,5 mm), 2,4 rzędu POWYŻEJ, a prawdziwe profile 10,8-11,3 rzędu powyżej.
    if abs(area2) <= CONVEXITY_EPS:
        raise ValueError("obrys profilu ma zerowe pole")
    # ZNAK pola, wyrażony bez porównania — i to jest celowe.
    #
    # Ta linia była `1.0 if area2 > 0.0 else -1.0`, a mutacja `>` -> `>=` PRZEŻYWAŁA
    # przegląd (to ona była pytaniem, na które odpowiada pozycja 12 w `docs/24`).
    # Strażnik wyżej nie zabija jej, tylko czyni NIEOSIĄGALNĄ: różnica między `>`
    # i `>=` widać wyłącznie przy `area2 == 0.0`, a takie wejście zostało już
    # odrzucone. Zmierzone: po dodaniu strażnika mutacja nadal ocalała (przegląd
    # na `f6058f9`: 78 mutacji, 29 zabitych, 49 ocalałych — ta wśród ocalałych).
    #
    # Zostawienie jej byłoby więc zostawieniem progu, który niczego nie rozstrzyga,
    # w module, którego progi są tematem całego `docs/24`. `copysign` nie ma progu
    # do zmutowania. Zmierzone na 200 000 wejściach z `area2 != 0`: 0 różnic wobec
    # starego wyrażenia; dla dokładnego zera wyniki się różnią (+1,0 kontra -1,0),
    # ale tam nie dochodzi już wykonanie.
    orientation = math.copysign(1.0, area2)
    planes = []
    for index in range(count):
        a = ring[index]
        b = ring[(index + 1) % count]
        c = ring[(index + 2) % count]
        turn = ((b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])) * orientation
        if turn < -CONVEXITY_EPS:
            raise ValueError("obrys profilu nie jest wypukły")
        edge = (b[0] - a[0], b[1] - a[1])
        length = math.hypot(*edge)
        if length <= 0.0:
            raise ValueError("obrys profilu ma zerową krawędź")
        # normalna w lewo od krawędzi razy orientacja = normalna do wnętrza
        normal = (-edge[1] / length * orientation, edge[0] / length * orientation)
        planes.append((normal[0], normal[1], normal[0] * a[0] + normal[1] * a[1],
                       _edge_label(normal)))
    return planes


def _edge_label(normal):
    nx, ny = normal
    if ny <= -0.9:
        return ROOF
    if ny >= 0.9:
        return FLOOR
    if abs(nx) >= 0.9:
        return WALL
    return CHAMFER


def clearance_in_planes(planes, lateral, vertical):
    """Luz punktu wobec wypukłego obrysu: `(luz, etykieta wiążącej krawędzi)`.

    Dla punktu wewnątrz wynik jest identyczny z `placement.distance_to_boundary`
    (przekrój półpłaszczyzn), dla punktu na zewnątrz jest ujemny, ale nie jest
    odległością — wtedy pomiar i tak jest już wynikiem do zaraportowania, a nie
    liczbą do dalszej optymalizacji.
    """
    best = float("inf")
    label = ""
    for nx, ny, c, name in planes:
        value = nx * lateral + ny * vertical - c
        if value < best:
            best = value
            label = name
    return best, label


# --- ramki: jedna na pasmo, nie jedna na wierzchołek -------------------------

def nearest_frame(frames, stations, point, window_m=FRAME_WINDOW_M, hint_m=None):
    """Indeks ramki minimalizującej |odległość wzdłuż stycznej| — reguła z `local_offsets`.

    `hint_m` zawęża przeszukiwanie do otoczenia szacowanego chainage; bez tego każde
    pasmo przeglądałoby wszystkie ramki osi. Okno rozszerza się, dopóki nie obejmie
    choć jednej ramki, więc wynik nie zależy od trafności podpowiedzi.
    """
    centre = stations[len(stations) // 2] if hint_m is None else float(hint_m)
    span = float(window_m)
    while True:
        low = bisect.bisect_left(stations, centre - span)
        high = bisect.bisect_right(stations, centre + span)
        if high > low:
            break
        span *= 2.0
        if span > 4.0 * (stations[-1] - stations[0] + 1.0):
            raise ValueError("oś nie ma ani jednej ramki")
    best_index = low
    best_along = float("inf")
    for index in range(low, min(high, len(frames))):
        frame = frames[index]
        delta = SW.sub(point, frame[0])
        along = abs(SW.dot(delta, frame[1]))
        if along < best_along:
            best_along = along
            best_index = index
    return best_index


def offsets_in_frame(frame, station, point):
    """`(chainage, w prawo, w górę)` punktu w zadanej ramce — wzór z `local_offsets`."""
    delta = SW.sub(point, frame[0])
    return (station + SW.dot(delta, frame[1]),
            SW.dot(delta, frame[2]),
            SW.dot(delta, frame[3]))


def band_coefficients(place, frame, station):
    """Rozwinięcie afiniczne transformacji bryły w ramce osi.

    Dla wierzchołka lokalnego `(x, y, z)` bryły:
        chainage = c0 + cx*x + cy*y + cz*z
        w prawo   = l0 + lx*x + ly*y + lz*z
        w górę    = v0 + vx*x + vy*y + vz*z
    To jest to samo, co `offsets_in_frame(transform_point(...))`, tylko z iloczynami
    skalarnymi policzonymi RAZ na pasmo, a nie raz na wierzchołek.
    """
    origin, tangent, right, up = frame
    delta = SW.sub(place["location"], origin)
    forward = place["forward"]
    body_right = place["right"]
    body_up = place["up"]
    shift = place["local_centre_x_m"]
    out = []
    for axis, base in ((tangent, station), (right, 0.0), (up, 0.0)):
        d_forward = SW.dot(forward, axis)
        d_right = SW.dot(body_right, axis)
        d_up = SW.dot(body_up, axis)
        out.append((base + SW.dot(delta, axis) - shift * d_forward,
                    d_forward, -d_right, d_up))
    return out


# --- pomiar jednej pozycji ----------------------------------------------------

def place_bodies(points, stations, start_m, reduced, track_offset_m):
    return PL.place_spans(points, stations, start_m,
                          [body["span"] for body in reduced], track_offset_m)


def measure_position(points, frames, stations, planes, reduced, start_m, track_offset_m,
                     window_m=FRAME_WINDOW_M, collector=None):
    """Minimalny luz składu, którego czoło stoi na chainage `start_m`.

    `collector` (jeśli podany) dostaje każdy kandydat jako `(chainage, lateral, vertical)`
    — tak zamiatana obwiednia powstaje bez drugiego przebiegu po geometrii.
    """
    places = place_bodies(points, stations, start_m, reduced, track_offset_m)
    best = {"clearance_m": float("inf"), "object": "", "chainage_m": 0.0,
            "lateral_m": 0.0, "vertical_m": 0.0, "bound_by": "", "chord_m": 0.0,
            "body_from_m": 0.0, "body_to_m": 0.0}
    half = FRAME_CANDIDATES // 2
    for body, place in zip(reduced, places):
        for band in body["bands"]:
            hint = start_m + band["x"]
            index = nearest_frame(frames, stations,
                                  PL.transform_point(place, (band["x"], 0.0, 0.0)),
                                  window_m, hint)
            candidates = [(stations[k], band_coefficients(place, frames[k], stations[k]))
                          for k in range(max(0, index - half),
                                         min(len(frames), index + half + 1))]
            for x, y, z in band["points"]:
                chosen = None
                chosen_chainage = 0.0
                closest = float("inf")
                for station, coefficients in candidates:
                    c0, cx, cy, cz = coefficients[0]
                    chainage = c0 + cx * x + cy * y + cz * z
                    along = chainage - station
                    if along < 0.0:
                        along = -along
                    if along < closest:
                        closest = along
                        chosen = coefficients
                        chosen_chainage = chainage
                l0, lx, ly, lz = chosen[1]
                v0, vx, vy, vz = chosen[2]
                lateral = l0 + lx * x + ly * y + lz * z
                vertical = v0 + vx * x + vy * y + vz * z
                clearance, label = clearance_in_planes(planes, lateral, vertical)
                if collector is not None:
                    collector(chosen_chainage, lateral, vertical)
                if clearance < best["clearance_m"]:
                    best = {"clearance_m": clearance, "object": body["name"],
                            "chainage_m": chosen_chainage,
                            "lateral_m": lateral, "vertical_m": vertical,
                            "bound_by": label, "chord_m": place["chord_m"],
                            "body_from_m": place["chainage_from_m"],
                            "body_to_m": place["chainage_to_m"]}
    best["start_m"] = start_m
    return best


def measure_position_naive(points, frames, stations, ring, bodies, start_m, track_offset_m):
    """Ten sam pomiar bez ani jednej redukcji: wszystkie wierzchołki, `placement` wprost.

    Wolne z założenia. Istnieje po to, żeby udowodnić, że redukcje nie gubią minimum.
    """
    ordered = sorted(bodies, key=lambda b: min(v[0] for v in b["vertices"]))
    spans = [(min(v[0] for v in b["vertices"]), max(v[0] for v in b["vertices"]))
             for b in ordered]
    places = PL.place_spans(points, stations, start_m, spans, track_offset_m)
    train_length = max(s[1] for s in spans) - min(s[0] for s in spans)
    window = (start_m - 40.0, start_m + train_length + 40.0)
    best = {"clearance_m": float("inf"), "object": "", "chainage_m": 0.0,
            "lateral_m": 0.0, "vertical_m": 0.0}
    for body, place in zip(ordered, places):
        for vertex in body["vertices"]:
            world = PL.transform_point(place, vertex)
            chainage, lateral, vertical = PL.local_offsets(world, frames, stations, window)
            clearance = PL.distance_to_boundary(ring, lateral, vertical)
            if clearance < best["clearance_m"]:
                best = {"clearance_m": clearance, "object": body["name"],
                        "chainage_m": chainage, "lateral_m": lateral, "vertical_m": vertical}
    best["start_m"] = start_m
    return best


# --- skan całej osi -----------------------------------------------------------

def scan_positions(axis_length_m, train_length_m, step_m=DEFAULT_STEP_M):
    """Chainage czoła składu: od 0 do końca osi minus długość składu, krokiem `step_m`.

    Suma pozycji pokrywa całą oś: przy czole w 0 skład zajmuje [0, L], przy ostatniej
    pozycji [axis - L, axis]. Krok nie musi dzielić zakresu — ostatnia pozycja jest
    dokładnie na końcu, więc nie zostaje niepokryty ogon.
    """
    if step_m <= 0.0:
        raise ValueError("krok musi być dodatni")
    last = axis_length_m - train_length_m
    if last <= 0.0:
        raise ValueError(f"skład {train_length_m} m nie mieści się na osi {axis_length_m} m")
    count = int(math.floor(last / step_m))
    out = [round(index * step_m, 6) for index in range(count + 1)]
    if abs(out[-1] - last) > 1e-9:
        out.append(round(last, 6))
    return out


def coverage_gaps(records, train_length_m, axis_length_m, step_m):
    """Dziury w pokryciu osi: pozycje odległe o więcej niż krok, albo brak końców."""
    problems = []
    if not records:
        return ["profil nie ma ani jednej pozycji"]
    starts = [r["start_m"] for r in records]
    if abs(starts[0]) > 1e-6:
        problems.append(f"pierwsza pozycja czoła w {starts[0]} m, nie w 0")
    expected_last = axis_length_m - train_length_m
    if abs(starts[-1] - expected_last) > 1e-6:
        problems.append(f"ostatnia pozycja czoła w {starts[-1]} m, oczekiwano {expected_last:.3f} m")
    for a, b in zip(starts, starts[1:]):
        if b - a > step_m + 1e-6:
            problems.append(f"dziura {b - a:.3f} m między pozycjami {a} m i {b} m")
    return problems


def refine_windows(records, step_m, band_m=DEFAULT_REFINE_BAND_M, half_window_m=None):
    """Okna do doszlifowania: otoczenia pozycji nie gorszych niż `min + band_m`.

    Odpowiada na zarzut „krok zgrubny mógł przeoczyć dołek": doszlifowanie liczy te
    same okna gęściej i pokazuje, o ile faktycznie schodzi minimum. Okno jest nie
    węższe niż krok zgrubny, więc przedział między sąsiednimi pozycjami siatki jest
    pokryty w całości, a nie tylko wokół jej węzłów.
    """
    if half_window_m is None:
        half_window_m = max(step_m, DEFAULT_REFINE_HALF_WINDOW_M)
    if not records:
        return []
    floor_value = min(r["clearance_m"] for r in records) + band_m
    picked = sorted(r["start_m"] for r in records if r["clearance_m"] <= floor_value)
    windows = []
    for start in picked:
        low, high = start - half_window_m, start + half_window_m
        if windows and low <= windows[-1][1]:
            windows[-1] = (windows[-1][0], max(windows[-1][1], high))
        else:
            windows.append((low, high))
    return windows


def percentile(values, fraction):
    """Percentyl metodą najbliższego rzędu — ta sama konwencja co w `clearance.py`."""
    if not values:
        return None
    ordered = sorted(values)
    return ordered[int(fraction * (len(ordered) - 1))]


def statistics(records, thresholds=DEFAULT_THRESHOLDS_M):
    """Minimum, percentyle, rozkład po wiążącej krawędzi i liczby pozycji pod progami."""
    values = [r["clearance_m"] for r in records]
    worst = min(records, key=lambda r: r["clearance_m"])
    bound = {}
    for record in records:
        bound[record["bound_by"]] = bound.get(record["bound_by"], 0) + 1
    return {
        "positions": len(records),
        "min_clearance_m": round(worst["clearance_m"], 6),
        "min_at": {"start_m": round(worst["start_m"], 3),
                   "object": worst["object"],
                   "chainage_m": round(worst["chainage_m"], 3),
                   "lateral_m": round(worst["lateral_m"], 4),
                   "vertical_m": round(worst["vertical_m"], 4),
                   "bound_by": worst["bound_by"],
                   "chord_m": round(worst["chord_m"], 4)},
        "p05_clearance_m": round(percentile(values, 0.05), 6),
        "median_clearance_m": round(percentile(values, 0.50), 6),
        "p95_clearance_m": round(percentile(values, 0.95), 6),
        "max_clearance_m": round(max(values), 6),
        "bound_by_counts": dict(sorted(bound.items())),
        "below_threshold": {f"{t:.3f}": sum(1 for v in values if v < t) for t in thresholds},
        "negative_positions": sum(1 for v in values if v < 0.0),
    }


def nearest_station(stations_doc, chainage_m):
    """Najbliższa stacja i odległość do niej — profil ma się czytać bez tablicy chainage."""
    best = None
    for station in stations_doc:
        distance = abs(float(station["chainage_m"]) - float(chainage_m))
        if best is None or distance < best[1]:
            best = (station, distance)
    if best is None:
        return {"name": "", "chainage_m": None, "distance_m": None}
    station, distance = best
    return {"name": station.get("name", ""),
            "chainage_m": round(float(station["chainage_m"]), 2),
            "distance_m": round(distance, 1)}


def between_stations(stations_doc, chainage_m):
    """Para stacji, między którymi wypada chainage — czytelniejsza niż sama najbliższa."""
    ordered = sorted(stations_doc, key=lambda s: float(s["chainage_m"]))
    before = None
    after = None
    for station in ordered:
        value = float(station["chainage_m"])
        if value <= chainage_m:
            before = station
        elif after is None:
            after = station
    return {"after": (before or {}).get("name", ""), "before": (after or {}).get("name", "")}


def critical_places(records, threshold_m, stations_doc, gap_m=CRITICAL_CLUSTER_GAP_M):
    """Miejsca na TRASIE, w których luz spada poniżej progu — jeden wpis na miejsce.

    Grupowanie idzie po chainage punktu styku, nie po pozycji składu: jeden ciasny łuk
    widziany z kilkuset pozycji składu to jedno miejsce w tunelu, a nie kilkaset wpisów.
    """
    below = [r for r in records if r["clearance_m"] < threshold_m]
    if not below:
        return []
    below.sort(key=lambda r: r["chainage_m"])
    runs = [[below[0]]]
    for record in below[1:]:
        if record["chainage_m"] - runs[-1][-1]["chainage_m"] <= gap_m:
            runs[-1].append(record)
        else:
            runs.append([record])
    out = []
    for run in runs:
        worst = min(run, key=lambda r: r["clearance_m"])
        out.append({
            "threshold_m": round(threshold_m, 3),
            "from_chainage_m": round(run[0]["chainage_m"], 2),
            "to_chainage_m": round(run[-1]["chainage_m"], 2),
            "positions": len(run),
            "min_clearance_m": round(worst["clearance_m"], 6),
            "worst_start_m": round(worst["start_m"], 2),
            "object": worst["object"],
            "bound_by": worst["bound_by"],
            "chainage_m": round(worst["chainage_m"], 2),
            "nearest_station": nearest_station(stations_doc, worst["chainage_m"]),
            "between": between_stations(stations_doc, worst["chainage_m"]),
        })
    return out


def point_at(points, stations, chainage_m):
    """Punkt osi w zadanym chainage — jak `placement.frame_at`, ale przez bisect.

    `frame_at` przegląda całą oś liniowo, więc szukanie minimalnego promienia wzdłuż
    6,7 km kosztuje kwadrat liczby pierścieni. Wynik jest identyczny.
    """
    total = stations[-1]
    value = max(stations[0], min(total, float(chainage_m)))
    index = min(max(0, bisect.bisect_right(stations, value) - 1), len(points) - 2)
    span = stations[index + 1] - stations[index]
    t = 0.0 if span <= 0.0 else (value - stations[index]) / span
    a, b = points[index], points[index + 1]
    return tuple(a[i] + t * (b[i] - a[i]) for i in range(3))


def min_radius_on_chord(points, stations, chord_m, guard_m=0.0):
    """Najmniejszy promień osi mierzony na cięciwie długości `chord_m`.

    Ta sama definicja co `clearance.radii_along`: promień na cięciwie pudła, a nie
    na trójce sąsiednich wierzchołków, bo trójka daje promień szumu digitalizacji.
    """
    half = chord_m / 2.0
    total = stations[-1]
    best = (None, float("inf"))
    for index, station in enumerate(stations):
        if station < max(half, guard_m) or station > total - max(half, guard_m):
            continue
        before = point_at(points, stations, station - half)
        after = point_at(points, stations, station + half)
        radius = PL._circumradius(before[:2], points[index][:2], after[:2])
        if radius is not None and radius < best[1]:
            best = (station, radius)
    return best


def chord_deviation_m(points, stations, from_m, to_m, samples=200):
    """Największe odchylenie osi od cięciwy bryły — strzałka ZMIERZONA, nie ze wzoru.

    Wzór `R - sqrt(R^2 - (l/2)^2)` zakłada, że oś między końcami bryły jest łukiem
    okręgu. Oś pakietu A nim nie jest: to łamana STIB zagęszczona Catmull-Romem,
    o zmiennej krzywiźnie. Ta funkcja mierzy to samo bez tego założenia, żeby dało się
    powiedzieć, ile z rozjazdu wzoru i siatki bierze się właśnie stąd.
    """
    head, _i, _t = PL.frame_at(points, stations, from_m)
    tail, _j, _u = PL.frame_at(points, stations, to_m)
    chord = SW.sub(tail, head)
    if SW.norm(chord) < 1e-9:
        return 0.0
    normal = SW.cross(SW.unit(chord), (0.0, 0.0, 1.0))
    worst = 0.0
    for index in range(samples + 1):
        chainage = from_m + (to_m - from_m) * index / samples
        point, _k, _v = PL.frame_at(points, stations, chainage)
        deviation = abs(SW.dot(SW.sub(point, head), normal))
        worst = max(worst, deviation)
    return worst


def body_radius_m(points, stations, chord_m, centre_chainage_m):
    """Promień na cięciwie bryły w danym punkcie — wielkość, której używa wzór na strzałkę."""
    half = chord_m / 2.0
    before, _i, _t = PL.frame_at(points, stations, centre_chainage_m - half)
    here, _j, _u = PL.frame_at(points, stations, centre_chainage_m)
    after, _k, _v = PL.frame_at(points, stations, centre_chainage_m + half)
    return PL._circumradius(before[:2], here[:2], after[:2])


# --- zamiatana obwiednia ------------------------------------------------------

def support_directions(count=SWEPT_DIRECTIONS):
    """Równomierne kierunki podparcia w płaszczyźnie (w prawo, w górę)."""
    if count < 3:
        raise ValueError("obwiednia potrzebuje co najmniej 3 kierunków podparcia")
    return [(math.cos(2.0 * math.pi * i / count), math.sin(2.0 * math.pi * i / count))
            for i in range(count)]


class SweptEnvelope:
    """Objętość zamiatana przez skład: obrys podparcia w każdym pierścieniu osi.

    To NIE jest `--envelope-out` z `m7_shell.py`. Tamto jest skrajnią prostego składu
    stojącego na prostej; tu każdy wierzchołek pojazdu wnosi swoje offsety w tym
    pierścieniu osi, w którym faktycznie wypadł, i to dla każdej pozycji składu.

    Przekrój jest przekrojem półpłaszczyzn podparcia, więc jest OTOCZKĄ WYPUKŁĄ z
    nadmiarem: obwiednia jest nadzbiorem rzeczywiście zajętej objętości. Do pytania
    „czy coś wstawionego do tunelu wchodzi w drogę składu" nadmiar jest bezpieczny,
    niedomiar nie byłby.

    Wierzchołek trafia do dwóch pierścieni otaczających jego chainage, nie do
    najbliższego: odcinek między dwiema próbkami pozycji musi być pokryty z obu stron,
    inaczej obwiednia miałaby prążki niedomiaru na szwach.
    """

    def __init__(self, stations, low_m, high_m, directions=None):
        self.stations = stations
        self.directions = directions or support_directions()
        self.low_m = float(low_m)
        self.high_m = float(high_m)
        self.first = max(0, bisect.bisect_left(stations, self.low_m) - 1)
        self.last = min(len(stations) - 1, bisect.bisect_right(stations, self.high_m))
        self.heights = {}
        self.samples = 0

    def rings_for(self, chainage_m):
        """Pierścienie, do których wnosi się wierzchołek o tym chainage."""
        if chainage_m < self.low_m or chainage_m > self.high_m:
            return ()
        index = bisect.bisect_left(self.stations, chainage_m)
        return tuple(r for r in (index - 1, index) if self.first <= r <= self.last)

    def add(self, chainage_m, lateral_m, vertical_m):
        for ring in self.rings_for(chainage_m):
            row = self.heights.get(ring)
            if row is None:
                row = [-float("inf")] * len(self.directions)
                self.heights[ring] = row
            for slot, (dx, dy) in enumerate(self.directions):
                value = dx * lateral_m + dy * vertical_m
                if value > row[slot]:
                    row[slot] = value
        self.samples += 1

    def collector(self):
        return self.add

    def rings(self):
        """`[(indeks pierścienia, [(w prawo, w górę), ...])]` — obrys w każdym pierścieniu."""
        out = []
        for ring in sorted(self.heights):
            row = self.heights[ring]
            if any(h == -float("inf") for h in row):
                continue
            out.append((ring, support_polygon(self.directions, row)))
        return out


def support_polygon(directions, heights):
    """Wielokąt jako przekrój półpłaszczyzn `d . p <= h`, wierzchołki z sąsiednich prostych."""
    count = len(directions)
    out = []
    for index in range(count):
        a, ha = directions[index], heights[index]
        b, hb = directions[(index + 1) % count], heights[(index + 1) % count]
        det = a[0] * b[1] - a[1] * b[0]
        if abs(det) < 1e-12:
            continue
        out.append(((ha * b[1] - hb * a[1]) / det, (a[0] * hb - b[0] * ha) / det))
    if len(out) < 3:
        raise ValueError("obrys podparcia zdegenerował się do mniej niż 3 wierzchołków")
    return out


def swept_mesh(frames, rings):
    """Siatka rury zamiatanej obwiedni: pierścienie na ramkach osi plus dwie zaślepki.

    Bez bpy — zwraca `{"vertices", "faces"}`, żeby dało się to sprawdzić gołym Pythonem.
    """
    if len(rings) < 2:
        raise ValueError("zamiatana obwiednia potrzebuje co najmniej 2 pierścieni")
    columns = len(rings[0][1])
    vertices = []
    for index, polygon in rings:
        if len(polygon) != columns:
            raise ValueError("pierścienie obwiedni mają różną liczbę kolumn")
        origin, _tangent, right, up = frames[index]
        for lateral, vertical in polygon:
            vertices.append(SW.add(origin, SW.add(SW.scale(right, lateral),
                                                  SW.scale(up, vertical))))
    faces = []
    for row in range(len(rings) - 1):
        base = row * columns
        for column in range(columns):
            nxt = (column + 1) % columns
            faces.append((base + column, base + nxt,
                          base + columns + nxt, base + columns + column))
    faces.append(tuple(range(columns - 1, -1, -1)))
    tail = (len(rings) - 1) * columns
    faces.append(tuple(range(tail, tail + columns)))
    return {"vertices": vertices, "faces": faces, "columns": columns, "rings": len(rings)}


def mesh_bbox(mesh):
    lo = [float("inf")] * 3
    hi = [-float("inf")] * 3
    for vertex in mesh["vertices"]:
        for axis in range(3):
            lo[axis] = min(lo[axis], vertex[axis])
            hi[axis] = max(hi[axis], vertex[axis])
    return tuple(lo), tuple(hi)


def envelope_clearance(rings, planes):
    """Najmniejszy luz obrysu zamiatanej obwiedni wobec profilu tunelu."""
    best = float("inf")
    where = None
    for index, polygon in rings:
        for lateral, vertical in polygon:
            value, label = clearance_in_planes(planes, lateral, vertical)
            if value < best:
                best = value
                where = {"ring": index, "lateral_m": round(lateral, 4),
                         "vertical_m": round(vertical, 4), "bound_by": label}
    return best, where


def envelope_contains(envelope, rings, samples, tolerance_m=1e-6):
    """Ile próbek `(chainage, lateral, vertical)` wypada poza swoim pierścieniem obwiedni.

    Niezmiennik: obwiednia ma zawierać skład w każdej zmierzonej pozycji. Wartość > 0
    znaczy, że obwiednia jest za mała i nie wolno jej użyć do testów kolizji.
    """
    by_ring = dict(rings)
    outside = 0
    checked = 0
    for chainage, lateral, vertical in samples:
        for ring in envelope.rings_for(chainage):
            polygon = by_ring.get(ring)
            if polygon is None:
                continue
            checked += 1
            if PL.distance_to_boundary(polygon, lateral, vertical) < -tolerance_m:
                outside += 1
    return outside, checked
