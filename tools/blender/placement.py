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
