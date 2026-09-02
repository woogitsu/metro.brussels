"""Ustawienie pojazdu na osi trasy — czysty Python, bez bpy.

Skład M7 jest przegubowy: sześć sztywnych pudeł połączonych przegubami. Na łuku
każde pudło opiera się na **własnej cięciwie**, więc ustawienie całego składu jako
jednej bryły dałoby geometrię, której na torze nie ma. Ten moduł liczy transformację
osobno dla każdego członu.

Układ pojazdu (z `m7_shell.py`): X wzdłuż składu 0..94 m, Y poprzecznie ze środkiem
w 0, Z w górę z **główką szyny na Z = 0**. Profile tuneli w `profiles.py` mają ten
sam poziom odniesienia: `vehicle_gauge` zaczyna się na y = -0.10 względem główki
szyny, a `fits_gauge` porównuje to bezpośrednio z obrysem profilu. Dzięki temu
osadzenie pojazdu nie wprowadza ani jednego nowego założenia o wysokości.
"""
import math

import sweep


def car_spans(total_length_m, cars):
    """Zakresy chainage kolejnych członów wzdłuż składu, licząc od czoła."""
    step = total_length_m / cars
    return [(index * step, (index + 1) * step) for index in range(cars)]


def frame_at(points, stations, chainage):
    """Ramka (pozycja, styczna, prawo, góra) w zadanym chainage osi."""
    total = stations[-1]
    chainage = max(0.0, min(total, chainage))
    for index in range(len(stations) - 1):
        if stations[index] <= chainage <= stations[index + 1]:
            span = stations[index + 1] - stations[index]
            t = 0.0 if span <= 0.0 else (chainage - stations[index]) / span
            a, b = points[index], points[index + 1]
            position = tuple(a[i] + t * (b[i] - a[i]) for i in range(3))
            return position, index, t
    return points[-1], len(points) - 2, 1.0


def axis_window(points, from_m, to_m):
    """Kadr wycinka osi: środek i rozmiar dla kamer kontrolnych.

    Ramuje OŚ, nie scenę — geometria odsunięta od osi dalej niż połowa okna może
    wypaść poza kadr. To jest cena za kadrowanie bez przeglądania wszystkich
    wierzchołków i dlatego pusta klatka musi być błędem, a nie ciszą.

    Powód istnienia: kamera obejmująca cały bbox stawia słupek 0,2 m w kadrze
    5,4 km na 0,03 piksela. Render wychodzi wtedy pusty, a skrypt kończy się zerem.
    """
    stations = sweep.chainages(points)
    total = stations[-1]
    if to_m <= from_m:
        raise ValueError(f"okno kadru musi rosnąć: from_m={from_m:.2f} to_m={to_m:.2f}")
    if from_m < 0.0 or to_m > total + 1e-6:
        raise ValueError(f"okno {from_m:.2f}-{to_m:.2f} m wychodzi poza oś 0.00-{total:.2f} m")
    head, _i, _t = frame_at(points, stations, from_m)
    tail, _j, _u = frame_at(points, stations, to_m)
    window = [head] + [tuple(p) for p, s in zip(points, stations) if from_m < s < to_m] + [tail]
    mins = tuple(min(p[axis] for p in window) for axis in range(3))
    maxs = tuple(max(p[axis] for p in window) for axis in range(3))
    return {
        "from_m": from_m,
        "to_m": to_m,
        "length_m": to_m - from_m,
        "head": head,
        "tail": tail,
        "points": window,
        "min": mins,
        "max": maxs,
        "center": tuple((a + b) / 2.0 for a, b in zip(mins, maxs)),
        "size": max(max(b - a for a, b in zip(mins, maxs)), 1.0),
    }


def place_cars(points, frames, stations, start_m, total_length_m, cars, track_offset_m=0.0):
    """Wygodny wariant dla równego podziału składu na `cars` członów."""
    return place_spans(points, stations, start_m, car_spans(total_length_m, cars), track_offset_m)


def place_spans(points, stations, start_m, spans, track_offset_m=0.0):
    """Transformacja każdej sztywnej bryły: pozycja środka, obrót wokół pionu, bok.

    Bryła jest ustawiana na cięciwie łączącej jej dwa końce na osi — dokładnie tak,
    jak stoi na torze pudło oparte na dwóch końcach. Zwis czopów skrętu nie jest
    modelowany, bo rozstaw czopów M7 nie ma źródła (patrz `reports/M7-curve-clearance.md`).

    `spans` to zakresy X w układzie pojazdu, więc ten sam kod obsługuje pudła członów
    i krótkie mieszki przegubów — każdy dostaje własną cięciwę, zamiast jechać
    na cięciwie sąsiada.
    """
    out = []
    for index, (a, b) in enumerate(spans):
        head, _i, _t = frame_at(points, stations, start_m + a)
        tail, _j, _u = frame_at(points, stations, start_m + b)
        chord = sweep.sub(tail, head)
        length = sweep.norm(chord)
        if length < 1e-9:
            raise ValueError(f"zerowa cięciwa członu {index}")
        forward = sweep.unit(chord)
        right = sweep.cross(forward, (0.0, 0.0, 1.0))
        if sweep.norm(right) < 1e-9:
            right = (0.0, -1.0, 0.0)
        right = sweep.unit(right)
        up = sweep.unit(sweep.cross(right, forward))
        centre = sweep.scale(sweep.add(head, tail), 0.5)
        centre = sweep.add(centre, sweep.scale(right, track_offset_m))
        out.append({
            "car": index,
            "chainage_from_m": start_m + a,
            "chainage_to_m": start_m + b,
            "local_centre_x_m": 0.5 * (a + b),
            "chord_m": length,
            "location": centre,
            "forward": forward,
            "right": right,
            "up": up,
            "yaw_rad": math.atan2(forward[1], forward[0]),
        })
    return out


def transform_point(placement, local):
    """Punkt lokalny pojazdu -> świat, dla jednego członu."""
    x = local[0] - placement["local_centre_x_m"]
    return sweep.add(placement["location"],
                     sweep.add(sweep.scale(placement["forward"], x),
                               sweep.add(sweep.scale(placement["right"], -local[1]),
                                         sweep.scale(placement["up"], local[2]))))


def worst_chainage(points, chord_m, guard_m):
    """Chainage o najmniejszym promieniu mierzonym na cięciwie pudła — najgorszy przypadek.

    `guard_m` odsuwa wynik od końców osi, żeby cały skład mieścił się na trasie.
    """
    stations = sweep.chainages(points)
    total = stations[-1]
    best = (None, float("inf"))
    half = chord_m / 2.0
    for station in stations:
        if station < guard_m or station > total - guard_m:
            continue
        before, _i, _t = frame_at(points, stations, station - half)
        after, _j, _u = frame_at(points, stations, station + half)
        here, _k, _v = frame_at(points, stations, station)
        radius = _circumradius(before[:2], here[:2], after[:2])
        if radius is not None and radius < best[1]:
            best = (station, radius)
    return best


def _circumradius(a, b, c):
    ab = math.dist(a, b)
    bc = math.dist(b, c)
    ca = math.dist(c, a)
    area2 = abs((b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]))
    if area2 < 1e-12 or ab * bc * ca == 0.0:
        return None
    return ab * bc * ca / (2.0 * area2)


def local_offsets(world_point, frames, stations, window=None):
    """Offsety punktu świata względem najbliższego punktu osi: (chainage, prawo, góra).

    `window` ogranicza przeszukiwanie do zakresu chainage — bez tego każdy wierzchołek
    pojazdu przeglądałby wszystkie 1349 pierścieni osi pakietu A.
    """
    best = (0.0, 0.0, 0.0, float("inf"))
    for station, frame in zip(stations, frames):
        if window and not (window[0] <= station <= window[1]):
            continue
        delta = sweep.sub(world_point, frame[0])
        along = sweep.dot(delta, frame[1])
        if abs(along) < best[3]:
            best = (station + along, sweep.dot(delta, frame[2]),
                    sweep.dot(delta, frame[3]), abs(along))
    return best[0], best[1], best[2]


def distance_to_boundary(profile_points, x, y):
    """Odległość punktu od obrysu profilu; dodatnia wewnątrz, ujemna na zewnątrz.

    To jest zmierzony luz do ściany, a nie wynik wzoru na strzałkę cięciwy — obie
    liczby mają się zgadzać, i właśnie po to jedna sprawdza drugą.
    """
    best = float("inf")
    for a, b in zip(profile_points, profile_points[1:] + profile_points[:1]):
        best = min(best, _point_segment(x, y, a, b))
    return best if _inside_polygon(profile_points, x, y) else -best


def _point_segment(x, y, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    span = dx * dx + dy * dy
    if span <= 0.0:
        return math.dist((x, y), a)
    t = ((x - a[0]) * dx + (y - a[1]) * dy) / span
    t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
    return math.dist((x, y), (a[0] + t * dx, a[1] + t * dy))


def _inside_polygon(ring, x, y):
    inside = False
    for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1]):
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            inside = not inside
    return inside


MIN_SECTION_HEIGHT_M = 0.5


def section_vertical(points, origin, normal, tolerance):
    """Zakres pionowy przekroju prostopadłego do `normal` w punkcie `origin`.

    Zwraca (zmin, zmax, liczba wierzchołków). Wybór płata po **stałym X** jest
    przekrojem tunelu tylko wtedy, gdy tunel biegnie wzdłuż X; na odcinku pod innym
    kątem taki płat łapie sam strop i daje zakres bliski zeru. Płaszczyzna
    prostopadła do lokalnej stycznej działa niezależnie od orientacji odcinka.
    """
    length = sweep.norm(normal)
    if length < 1e-9:
        raise ValueError("normalna przekroju nie może być wektorem zerowym")
    unit = sweep.scale(normal, 1.0 / length)
    depth = [abs(sweep.dot(sweep.sub(p, origin), unit)) for p in points]
    section = [p for p, d in zip(points, depth) if d <= tolerance]
    if not section:
        nearest = min(depth)
        section = [p for p, d in zip(points, depth) if abs(d - nearest) <= 1e-4]
    zs = [p[2] for p in section]
    return min(zs), max(zs), len(section)


def section_vertical_stable(points, origin, normal, tolerance, rounds=4):
    """Poszerza płat kilka razy i bierze NAJWYŻSZY znaleziony przekrój.

    Ramki liczone z surowej łamanej mają nieco inne styczne niż pierścienie wygenerowane
    z osi zagęszczonej, więc płaszczyzna potrafi ciąć pierścień ukośnie i złapać tylko
    część jego wierzchołków — objawia się to stropem 4,30 m zamiast 4,70 m, czyli
    początkiem ścięcia naroża zamiast płyty stropowej.

    Przerwanie na pierwszym braku przyrostu **nie działa**: zmierzone na chunku pakietu A
    tolerancje 1 m i 2 m dają identyczne 5,50 m, a dopiero 4 m daje pełne 5,90 m.
    Dlatego przechodzimy wszystkie rundy i bierzemy maksimum. Wysokość i tak nasyca się
    na wysokości profilu, więc poszerzanie nie zamienia przekroju w pomiar całej sceny.
    """
    best = section_vertical(points, origin, normal, tolerance)
    for _ in range(rounds):
        tolerance *= 2.0
        candidate = section_vertical(points, origin, normal, tolerance)
        if candidate[1] - candidate[0] > best[1] - best[0]:
            best = candidate
    return best


def is_degenerate_section(zmin, zmax, minimum=MIN_SECTION_HEIGHT_M):
    """Czy przekrój jest zbyt płaski, żeby uznać go za przekrój tunelu.

    Zdegenerowany przekrój nie jest wynikiem do cichego użycia: oko kamery trafia
    wtedy w ścianę albo strop, a klatka wychodzi jednolita — i **przechodzi**
    kontrolę „nie jest pusta", bo jednolita szarość ma i ink, i odchylenie
    standardowe powyżej progów.
    """
    return (zmax - zmin) < minimum


COVERAGE_SAMPLES = 2000


def covered_chainage_range(points, frames, stations, samples=COVERAGE_SAMPLES):
    """Zakres chainage osi, który rzeczywiście pokrywa wczytana geometria.

    Kotwice kamer liczone jako ułamki **całej** osi wypadają poza chunkiem: dla
    chunka 2923..3433 m ułamek 0,05 wskazuje 86 m, czyli 2,8 km przed jego początkiem.
    Kamera trafia wtedy w pustkę, a przekrój zjeżdża na najbliższy pierścień skraju.
    Ułamki liczone w tym zakresie trafiają w geometrię niezależnie od tego, czy
    wczytano całą oś, czy jeden chunk.
    """
    if not points:
        raise ValueError("brak wierzchołków do wyznaczenia zakresu")
    step = max(1, len(points) // max(1, samples))
    low, high = float("inf"), float("-inf")
    for point in points[::step]:
        chainage, _lateral, _vertical = local_offsets(point, frames, stations)
        low = min(low, chainage)
        high = max(high, chainage)
    return max(stations[0], low), min(stations[-1], high)


def fraction_to_chainage(fraction, low, high):
    """Ułamek w zakresie pokrycia, przycięty do niego."""
    value = low + (high - low) * float(fraction)
    return max(low, min(high, value))


# --- detale przy torze (T-011) ---------------------------------------------------


def gauge_half_width_m(gauge, height_m):
    """Najszersze pół-rozstawienie skrajni pojazdu **do** zadanej wysokości.

    Skrajnia zwęża się ku górze (ścięcia naroży), więc niski słupek może stać bliżej
    osi niż wysoki. Branie zawsze najszerszego miejsca skrajni odsuwałoby hektometry
    dalej, niż muszą stać.
    """
    below = [abs(x) for x, z in gauge if z <= height_m + 1e-9]
    if not below:
        raise ValueError(f"skrajnia nie ma ani jednego punktu poniżej {height_m} m")
    return max(below)


def marker_clearances(profile, gauge, offset_m, width_m, foot_m, height_m):
    """Dwa luzy słupka przy torze: do skrajni pojazdu i do ściany tunelu.

    Liczone w NAJGORSZYM punkcie bryły, nie w jej środku: o luz do skrajni decyduje
    krawędź bliższa osi, o luz do ściany — dalsza i najwyższa. Wynik ujemny znaczy
    kolizję i wołający ma odmówić zapisu, a nie zaokrąglić.
    """
    near = offset_m - width_m / 2.0
    far = offset_m + width_m / 2.0
    top = foot_m + height_m
    to_gauge = near - gauge_half_width_m(gauge, top)
    to_wall = min(distance_to_boundary(profile, far, top),
                  distance_to_boundary(profile, far, foot_m),
                  distance_to_boundary(profile, near, top))
    return to_gauge, to_wall
