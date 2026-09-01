"""Geometria zamiatania profilu wzdłuż osi trasy — czysty Python, bez bpy.

Cała matematyka T-210 (ramki, chunki, siatka, UV, kontrole) siedzi tutaj, żeby dała
się przetestować bez Blendera: CI odpala goły `python3`, a job z Blenderem jest
wolniejszy i cięższy. `tunnel_sweep.py` jest już tylko adapterem na bpy.

Układ: 1 jednostka = 1 metr, oś w płaszczyźnie XY, Z w górę (docs/04-conventions.md).
Profil jest opisany w płaszczyźnie (poprzecznie, pionowo) i przenoszony na ramkę
(prawo, góra) wyznaczoną wzdłuż osi.
"""
import math

UP_WORLD = (0.0, 0.0, 1.0)
DEFAULT_RING_STEP_M = 5.0
DEFAULT_MAX_CHUNK_M = 800.0
DEFAULT_MIN_CHUNK_M = 120.0
# Połowa peronu 60 m plus zapas na rozjazd wjazdowy: w tym promieniu wokół chainage
# stacji nie wolno postawić granicy chunka, bo Godot streamowałby stację na raty.
DEFAULT_STATION_HALO_M = 90.0
UV_METRES_PER_UNIT = 4.0
DEGENERATE_AREA_M2 = 1e-6


# --- wektory ------------------------------------------------------------------

def sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def scale(a, k):
    return (a[0] * k, a[1] * k, a[2] * k)


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def norm(a):
    return math.sqrt(dot(a, a))


def unit(a):
    length = norm(a)
    if length <= 0.0:
        raise ValueError("wektor zerowy nie ma kierunku")
    return (a[0] / length, a[1] / length, a[2] / length)


# --- oś: czyszczenie i zagęszczanie ------------------------------------------

def dedupe(points, eps=1e-6):
    """Usuwa powtórzone punkty — zerowy segment wywraca każdą normalizację stycznej."""
    out = []
    for point in points:
        if not out or norm(sub(point, out[-1])) > eps:
            out.append(tuple(float(c) for c in point))
    return out


def polyline_length(points):
    return sum(norm(sub(b, a)) for a, b in zip(points, points[1:]))


def chainages(points):
    out = [0.0]
    for a, b in zip(points, points[1:]):
        out.append(out[-1] + norm(sub(b, a)))
    return out


def catmull_rom(points, step):
    """Zagęszcza oś krzywą centripetal Catmull-Rom przechodzącą przez WSZYSTKIE punkty.

    ZAŁOŻENIE PROJEKTOWE, nie dana: skomitowana oś to łamana o kroku 15 m, czyli
    cięciwy prawdziwego łuku. Przy minimalnym promieniu 97 m cięciwa 15 m zostawia
    strzałkę ~0,29 m — na renderze widać kanciasty tunel. Interpolacja przechodzi
    przez punkty źródłowe i wybrzusza się na zewnątrz cięciwy, więc przybliża łuk
    lepiej niż łamana; nie wnosi nowej informacji o przebiegu i nie przesuwa
    żadnego punktu STIB. Wariant wierny (`step <= 0`) zwraca łamaną bez zmian.
    """
    points = dedupe(points)
    if step <= 0.0 or len(points) < 3:
        return list(points)
    extended = [add(points[0], sub(points[0], points[1]))] + list(points)
    extended.append(add(points[-1], sub(points[-1], points[-2])))
    out = [points[0]]
    for i in range(1, len(extended) - 2):
        p0, p1, p2, p3 = extended[i - 1], extended[i], extended[i + 1], extended[i + 2]
        span = norm(sub(p2, p1))
        count = max(1, int(math.ceil(span / step)))
        t0 = 0.0
        t1 = t0 + math.sqrt(norm(sub(p1, p0))) or t0 + 1e-6
        t2 = t1 + math.sqrt(span) or t1 + 1e-6
        t3 = t2 + math.sqrt(norm(sub(p3, p2))) or t2 + 1e-6
        for k in range(1, count + 1):
            t = t1 + (t2 - t1) * k / count
            a1 = add(scale(p0, (t1 - t) / (t1 - t0)), scale(p1, (t - t0) / (t1 - t0)))
            a2 = add(scale(p1, (t2 - t) / (t2 - t1)), scale(p2, (t - t1) / (t2 - t1)))
            a3 = add(scale(p2, (t3 - t) / (t3 - t2)), scale(p3, (t - t2) / (t3 - t2)))
            b1 = add(scale(a1, (t2 - t) / (t2 - t0)), scale(a2, (t - t0) / (t2 - t0)))
            b2 = add(scale(a2, (t3 - t) / (t3 - t1)), scale(a3, (t - t1) / (t3 - t1)))
            out.append(add(scale(b1, (t2 - t) / (t2 - t1)), scale(b2, (t - t1) / (t2 - t1))))
    return dedupe(out)


def max_deviation(sampled, source):
    """Największa odległość punktu zagęszczonej osi od łamanej źródłowej."""
    return max(point_to_polyline(p, source) for p in sampled) if sampled else 0.0


def point_to_polyline(point, polyline):
    best = float("inf")
    for a, b in zip(polyline, polyline[1:]):
        d = sub(b, a)
        seg = dot(d, d)
        if seg <= 0.0:
            best = min(best, norm(sub(point, a)))
            continue
        t = dot(sub(point, a), d) / seg
        t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
        best = min(best, norm(sub(point, add(a, scale(d, t)))))
    return best


# --- ramki --------------------------------------------------------------------

def tangents(points):
    """Styczne uśrednione na wierzchołkach — bez skoku kierunku na każdym punkcie."""
    segs = [unit(sub(b, a)) for a, b in zip(points, points[1:])]
    out = [segs[0]]
    for a, b in zip(segs, segs[1:]):
        s = add(a, b)
        out.append(unit(s) if norm(s) > 1e-9 else a)
    out.append(segs[-1])
    return out


def rmf_frames(points, up=UP_WORLD):
    """Ramki minimalizujące skręt (Wang i in., podwójne odbicie).

    Naiwna ramka Freneta wywraca binormalę w każdym punkcie przegięcia — na osi
    metra, która jest ciągiem łuków przeciwnego znaku, dałoby to skręcony tunel.
    RMF przenosi ramkę wzdłuż krzywej bez skrętu wokół stycznej, więc profil nie
    obraca się nawet na przegięciu.
    """
    points = dedupe(points)
    if len(points) < 2:
        raise ValueError("oś musi mieć co najmniej 2 różne punkty")
    tans = tangents(points)
    right = cross(tans[0], up)
    if norm(right) < 1e-9:  # oś pionowa: dowolna prostopadła jest równie dobra
        right = cross(tans[0], (1.0, 0.0, 0.0))
    right = unit(right)
    frames = [(points[0], tans[0], right, unit(cross(right, tans[0])))]
    for i in range(len(points) - 1):
        _p, t_i, r_i, _s = frames[-1]
        v1 = sub(points[i + 1], points[i])
        c1 = dot(v1, v1)
        r_l = sub(r_i, scale(v1, 2.0 * dot(v1, r_i) / c1))
        t_l = sub(t_i, scale(v1, 2.0 * dot(v1, t_i) / c1))
        t_next = tans[i + 1]
        v2 = sub(t_next, t_l)
        c2 = dot(v2, v2)
        r_next = r_l if c2 < 1e-18 else sub(r_l, scale(v2, 2.0 * dot(v2, r_l) / c2))
        r_next = unit(r_next)
        frames.append((points[i + 1], t_next, r_next, unit(cross(r_next, t_next))))
    return frames


def frame_twist_deg(frames, up=UP_WORLD):
    """Największy kąt między osią „góra" ramki a pionem świata — detektor skrętu."""
    worst = 0.0
    for _p, _t, _r, s in frames:
        worst = max(worst, math.degrees(math.acos(max(-1.0, min(1.0, dot(s, up))))))
    return worst


# --- podział na chunki --------------------------------------------------------

def chunk_boundaries(total_m, station_chainages, max_chunk_m=DEFAULT_MAX_CHUNK_M,
                     min_chunk_m=DEFAULT_MIN_CHUNK_M, halo_m=DEFAULT_STATION_HALO_M):
    """Granice chunków w chainage: nigdy w obrębie stacji, długość <= max_chunk_m.

    Bazowe cięcia idą w połowie odległości między sąsiednimi stacjami — wtedy każda
    stacja z definicji leży wewnątrz chunka, a nie na jego szwie. Zbyt długie chunki
    są dzielone dalej, ale kandydat wpadający w halo stacji jest odsuwany poza nie.
    """
    stops = sorted(float(c) for c in station_chainages)
    cuts = []
    for a, b in zip(stops, stops[1:]):
        # Dwie stacje bliżej niż 2 x halo nie dają się rozdzielić żadnym cięciem —
        # wtedy obie zostają w jednym chunku, zamiast dostać szew na peronie.
        cut = _push_out_of_stations(0.5 * (a + b), stops, halo_m, 0.0, total_m)
        if cut is not None and 0.0 < cut < total_m:
            cuts.append(cut)
    cuts = _split_long(sorted(set(cuts)), total_m, max_chunk_m, stops, halo_m)
    cuts = _drop_short(cuts, total_m, min_chunk_m)
    bounds = [0.0] + cuts + [total_m]
    return [(a, b) for a, b in zip(bounds, bounds[1:])]


def _split_long(cuts, total_m, max_chunk_m, stops, halo_m):
    out = sorted(cuts)
    changed = True
    while changed:
        changed = False
        edges = [0.0] + out + [total_m]
        for a, b in zip(edges, edges[1:]):
            if b - a <= max_chunk_m:
                continue
            pieces = int(math.ceil((b - a) / max_chunk_m))
            for k in range(1, pieces):
                candidate = _push_out_of_stations(a + (b - a) * k / pieces, stops, halo_m, a, b)
                if candidate is not None and all(abs(candidate - c) > 1e-6 for c in out):
                    out.append(candidate)
                    changed = True
            out.sort()
            break
    return out


def _push_out_of_stations(value, stops, halo_m, low, high):
    for stop in stops:
        if abs(value - stop) >= halo_m:
            continue
        for shifted in (stop - halo_m, stop + halo_m):
            if low + 1e-6 < shifted < high - 1e-6 and all(abs(shifted - s) >= halo_m for s in stops):
                return shifted
        return None
    return value


def _drop_short(cuts, total_m, min_chunk_m):
    out = []
    previous = 0.0
    for cut in sorted(cuts):
        if cut - previous >= min_chunk_m:
            out.append(cut)
            previous = cut
    if out and total_m - out[-1] < min_chunk_m:
        out.pop()
    return out


def splits_station(bounds, station_chainages, halo_m=DEFAULT_STATION_HALO_M):
    """Zwraca granice, które przecinają halo którejkolwiek stacji."""
    inner = [b for _a, b in bounds[:-1]]
    return [(cut, stop) for cut in inner for stop in station_chainages if abs(cut - stop) < halo_m]


# --- siatka -------------------------------------------------------------------

def profile_arc(profile):
    """Skumulowana długość obwodu profilu; ostatnia wartość zamyka pętlę."""
    out = [0.0]
    for a, b in zip(profile, profile[1:] + profile[:1]):
        out.append(out[-1] + math.dist(a, b))
    return out


def ring_positions(frame, profile):
    _p, _t, right, up = frame
    origin = frame[0]
    return [add(origin, add(scale(right, px), scale(up, py))) for px, py in profile]


def build_chunk(frames, station_m, profile, first, last, uv_scale=UV_METRES_PER_UNIT):
    """Buduje jeden chunk jako rurę na ramkach [first, last] włącznie.

    Kolumna szwu jest zdublowana (n+1 kolumn na pierścień), żeby UV szło 0..obwód
    bez zawijania — inaczej ostatni czworokąt dostaje u od obwodu do 0 i rozciąga
    teksturę na całą szerokość.
    """
    arc = profile_arc(profile)
    columns = len(profile) + 1
    vertices, uvs = [], []
    for index in range(first, last + 1):
        ring = ring_positions(frames[index], profile)
        v = station_m[index] / uv_scale
        for column in range(columns):
            vertices.append(ring[column % len(profile)])
            uvs.append((arc[column] / uv_scale, v))
    flip = _needs_flip(frames[first], profile)
    faces = []
    for row in range(last - first):
        base = row * columns
        for column in range(columns - 1):
            a = base + column
            quad = (a, a + 1, a + columns + 1, a + columns)
            faces.append(quad[::-1] if flip else quad)
    return {
        "vertices": vertices,
        "faces": faces,
        "uvs": uvs,
        "first_ring": first,
        "last_ring": last,
        "start_m": station_m[first],
        "end_m": station_m[last],
        "length_m": station_m[last] - station_m[first],
    }


def _needs_flip(frame, profile):
    """Czy domyślne nawinięcie daje normalne na zewnątrz rury.

    Wynik zależy tylko od kolejności punktów profilu i skrętności ramki, więc jest
    deterministyczny; liczymy go raz, na pierwszym pierścieniu, i stosujemy do
    całego chunka, żeby nie mieszać orientacji wewnątrz jednej siatki.
    """
    _p, tangent, right, up = frame
    (x1, y1), (x2, y2) = profile[0], profile[1]
    edge = add(scale(right, x2 - x1), scale(up, y2 - y1))
    normal = cross(edge, tangent)
    midpoint = add(scale(right, 0.5 * (x1 + x2)), scale(up, 0.5 * (y1 + y2)))
    return dot(normal, midpoint) > 0.0


def face_normal(vertices, face):
    """Normalna Newella — odporna na czworokąty lekko niepłaskie."""
    nx = ny = nz = 0.0
    for i in range(len(face)):
        a = vertices[face[i]]
        b = vertices[face[(i + 1) % len(face)]]
        nx += (a[1] - b[1]) * (a[2] + b[2])
        ny += (a[2] - b[2]) * (a[0] + b[0])
        nz += (a[0] - b[0]) * (a[1] + b[1])
    return (nx, ny, nz)


def face_area(vertices, face):
    return 0.5 * norm(face_normal(vertices, face))


def outward_faces(chunk, frames, columns):
    """Liczba ścian, których normalna wskazuje NA ZEWNĄTRZ rury.

    Powierzchnia tunelu jest oglądana od środka (docs 01), więc poprawny wynik to 0.
    """
    count = 0
    for face in chunk["faces"]:
        normal = face_normal(chunk["vertices"], face)
        centre = [0.0, 0.0, 0.0]
        for index in face:
            vertex = chunk["vertices"][index]
            centre = [centre[i] + vertex[i] / len(face) for i in range(3)]
        row = face[0] // columns
        axis = frames[chunk["first_ring"] + row][0]
        if dot(normal, sub(tuple(centre), axis)) > 0.0:
            count += 1
    return count


def degenerate_faces(chunk, min_area=DEGENERATE_AREA_M2):
    return [f for f in chunk["faces"] if face_area(chunk["vertices"], f) < min_area]


def chunk_gap_m(previous, current, columns):
    """Największy rozjazd między ostatnim pierścieniem chunka a pierwszym następnego."""
    tail = previous["vertices"][-columns:]
    head = current["vertices"][:columns]
    return max(norm(sub(a, b)) for a, b in zip(tail, head))


def uv_stretch(chunk, columns):
    """Stosunek długości krawędzi w metrach do długości w UV — im równiej, tym lepiej.

    Zwraca (min, max) dla krawędzi wzdłuż osi; skok na szwie chunka oznaczałby, że
    tekstura zmienia gęstość w widocznym miejscu.
    """
    ratios = []
    rows = len(chunk["vertices"]) // columns
    for row in range(rows - 1):
        for column in range(columns):
            i = row * columns + column
            j = i + columns
            metres = norm(sub(chunk["vertices"][j], chunk["vertices"][i]))
            duv = math.dist(chunk["uvs"][i], chunk["uvs"][j])
            if duv > 1e-9:
                ratios.append(metres / duv)
    return (min(ratios), max(ratios)) if ratios else (0.0, 0.0)


def bounding_box(chunks):
    lo = [float("inf")] * 3
    hi = [float("-inf")] * 3
    for chunk in chunks:
        for vertex in chunk["vertices"]:
            for i in range(3):
                lo[i] = min(lo[i], vertex[i])
                hi[i] = max(hi[i], vertex[i])
    return tuple(lo), tuple(hi)


def non_finite(chunks):
    bad = 0
    for chunk in chunks:
        for vertex in chunk["vertices"]:
            for value in vertex:
                if math.isnan(value) or math.isinf(value):
                    bad += 1
    return bad


# --- złożenie -----------------------------------------------------------------

def sweep(points, profile, ring_step=DEFAULT_RING_STEP_M, station_chainages=(),
          max_chunk_m=DEFAULT_MAX_CHUNK_M, halo_m=DEFAULT_STATION_HALO_M,
          uv_scale=UV_METRES_PER_UNIT):
    """Pełny przebieg: oś -> zagęszczenie -> ramki -> chunki -> siatki + metryki."""
    source = dedupe(points)
    dense = catmull_rom(source, ring_step)
    frames = rmf_frames(dense)
    station_m = chainages(dense)
    total = station_m[-1]
    bounds = chunk_boundaries(total, station_chainages or (0.0, total), max_chunk_m,
                              DEFAULT_MIN_CHUNK_M, halo_m)
    edges = [0.0] + [b for _a, b in bounds]
    ring_index = [_nearest_ring(station_m, value) for value in edges]
    ring_index = _strictly_increasing(ring_index, len(station_m) - 1)
    chunks = [build_chunk(frames, station_m, profile, a, b, uv_scale)
              for a, b in zip(ring_index, ring_index[1:])]
    columns = len(profile) + 1
    return {
        "chunks": chunks,
        "frames": frames,
        "columns": columns,
        "source_points": len(source),
        "ring_points": len(dense),
        "axis_length_m": total,
        "source_length_m": polyline_length(source),
        "ring_step_m": ring_step,
        "max_deviation_m": max_deviation(dense, source),
        "twist_deg": frame_twist_deg(frames),
        "chunk_bounds": bounds,
    }


def _nearest_ring(station_m, value):
    best, best_d = 0, float("inf")
    for index, station in enumerate(station_m):
        distance = abs(station - value)
        if distance < best_d:
            best, best_d = index, distance
    return best


def _strictly_increasing(indices, maximum):
    out = [indices[0]]
    for index in indices[1:]:
        out.append(max(index, out[-1] + 1))
    out[-1] = maximum
    while len(out) > 1 and out[-2] >= out[-1]:
        out.pop(-2)
    return out


# --- manifest streamingowy ----------------------------------------------------
#
# Chunki jako osobne obiekty w jednym GLB nie dają streamowania: Godot i tak wczytuje
# cały plik. Streaming potrzebuje osobnych plików i indeksu, po którym da się w czasie
# rzeczywistym odpowiedzieć „co wczytać, a co zwolnić, gdy pociąg jest na chainage X".
# Ta sekcja jest celowo bez bpy — predykat okna ma się dać przetestować gołym python3
# i przepisać 1:1 na GDScript.

CHUNK_MANIFEST_SCHEMA_VERSION = 1
# ZAŁOŻENIE PROJEKTOWE, nie dana o sieci: okno streamowania z docs/01-architecture.md
# („600 m przed składem i 300 m za nim"). Manifest tylko je zapisuje; predykat przyjmuje
# dowolne wartości, bo budżet pamięci jest decyzją silnika, nie faktem o metrze.
DEFAULT_STREAM_AHEAD_M = 600.0
DEFAULT_STREAM_BEHIND_M = 300.0
# Klucze zależne od bajtów pliku GLB. Eksporter glTF nie gwarantuje kolejności bufora,
# więc te wartości NIE są odtwarzalne między przebiegami — reszta manifestu jest.
VOLATILE_CHUNK_KEYS = ("sha256", "bytes")


def stations_by_chunk(bounds, station_chainages):
    """Indeksy stacji przypisane do chunków — każda stacja trafia do dokładnie jednego.

    Chainage stacji pochodzi z łamanej źródłowej, a granice chunków z osi zagęszczonej,
    więc skrajna stacja potrafi wypaść o ułamek metra za końcem osi (Merode: 6686,99 m
    przy osi 6686,74 m). Zamiast gubić taką stację, chainage jest przycinany do osi.
    """
    total = bounds[-1][1]
    out = [[] for _ in bounds]
    last = len(bounds) - 1
    for position, raw in enumerate(station_chainages):
        value = min(max(float(raw), 0.0), total)
        target = last
        for index, (_a, b) in enumerate(bounds):
            if value < b or index == last:
                target = index
                break
        out[target].append(position)
    return out


def chunk_geometry_sha256(chunk, digits=6):
    """Odcisk samej geometrii chunka — niezależny od bajtów GLB.

    Potrzebny, bo eksporter glTF nie daje powtarzalnych bajtów: `sha256` pliku zmienia
    się między przebiegami, choć siatka jest ta sama. Ten hash liczy się z wierzchołków,
    UV i ścian, więc odpowiada na pytanie „czy geometria się zmieniła" i nadaje się na
    klucz cache'u po stronie Godota.
    """
    import hashlib
    digest = hashlib.sha256()
    for vertex in chunk["vertices"]:
        digest.update((",".join(f"{c:.{digits}f}" for c in vertex) + ";").encode("ascii"))
    digest.update(b"|uv|")
    for uv in chunk["uvs"]:
        digest.update((",".join(f"{c:.{digits}f}" for c in uv) + ";").encode("ascii"))
    digest.update(b"|f|")
    for face in chunk["faces"]:
        digest.update((",".join(str(i) for i in face) + ";").encode("ascii"))
    return digest.hexdigest()


def stream_window(chainage_m, radius_m=None, ahead_m=None, behind_m=None, heading=1.0):
    """Zakres chainage, który musi być wczytany dla pociągu w punkcie `chainage_m`.

    `radius_m` daje okno symetryczne; `ahead_m`/`behind_m` okno asymetryczne w kierunku
    jazdy. `heading` < 0 znaczy jazdę w stronę malejącego chainage, więc „przed składem"
    leży po stronie mniejszych wartości.
    """
    if ahead_m is None:
        ahead_m = DEFAULT_STREAM_AHEAD_M if radius_m is None else radius_m
    if behind_m is None:
        behind_m = DEFAULT_STREAM_BEHIND_M if radius_m is None else radius_m
    ahead_m, behind_m = float(ahead_m), float(behind_m)
    if ahead_m < 0.0 or behind_m < 0.0:
        raise ValueError("zasięg streamowania nie może być ujemny")
    x = float(chainage_m)
    if heading >= 0.0:
        return (x - behind_m, x + ahead_m)
    return (x - ahead_m, x + behind_m)


def chunks_in_range(manifest, low_m, high_m):
    """Chunki przecinające zakres [low_m, high_m], w kolejności chainage.

    Przedział domknięty z obu stron: pociąg dokładnie na szwie potrzebuje obu chunków,
    a nadmiarowy chunk kosztuje pamięć, brakujący — dziurę w tunelu.
    """
    if high_m < low_m:
        low_m, high_m = high_m, low_m
    out = [c for c in manifest["chunks"]
           if float(c["start_m"]) <= high_m and float(c["end_m"]) >= low_m]
    return sorted(out, key=lambda c: float(c["start_m"]))


def chunks_for_train(manifest, chainage_m, radius_m=None, ahead_m=None, behind_m=None,
                     heading=1.0):
    """Predykat streamowania: co musi być w pamięci dla składu na `chainage_m`."""
    low, high = stream_window(chainage_m, radius_m, ahead_m, behind_m, heading)
    return chunks_in_range(manifest, low, high)


def streaming_plan(manifest, chainage_m, loaded_ids=(), radius_m=None, ahead_m=None,
                   behind_m=None, heading=1.0):
    """Różnica między tym, co jest wczytane, a tym, co być powinno.

    Zwraca `load` / `keep` / `free` — dokładnie trzy listy, których potrzebuje pętla
    streamowania w Godocie, żeby nie przeliczać zbiorów przy każdej klatce.
    """
    needed = [c["id"] for c in chunks_for_train(manifest, chainage_m, radius_m, ahead_m,
                                                behind_m, heading)]
    have = set(loaded_ids)
    return {
        "load": [i for i in needed if i not in have],
        "keep": [i for i in needed if i in have],
        "free": sorted(have - set(needed)),
    }


def deterministic_view(manifest):
    """Kopia manifestu bez pól zależnych od bajtów GLB — do porównania dwóch przebiegów."""
    import copy
    out = copy.deepcopy(manifest)
    out.pop("glb_bytes", None)
    for chunk in out.get("chunks", []):
        for key in VOLATILE_CHUNK_KEYS:
            chunk.pop(key, None)
    return out


def manifest_problems(manifest, length_tolerance_m=0.01, seam_tolerance_m=1e-6):
    """Kontrola spójności manifestu — lista problemów, pusta znaczy OK.

    Sprawdza dokładnie te niezmienniki, na których opiera się streaming: chunki mają
    pokryć oś raz, bez dziur i bez zakładek, a deklarowane liczniki mają się sumować
    do metryk generatora.
    """
    problems = []
    chunks = manifest.get("chunks") or []
    if not chunks:
        return ["manifest nie ma ani jednego chunka"]

    ids = [c["id"] for c in chunks]
    if len(set(ids)) != len(ids):
        problems.append("powtórzone id chunków")
    files = [c["file"] for c in chunks]
    if len(set(files)) != len(files):
        problems.append("powtórzone nazwy plików chunków")

    ordered = sorted(chunks, key=lambda c: float(c["start_m"]))
    if [c["id"] for c in ordered] != ids:
        problems.append("chunki w manifeście nie są posortowane po chainage")

    axis = float(manifest["axis_length_m"])
    if abs(float(ordered[0]["start_m"])) > seam_tolerance_m:
        problems.append(f"pierwszy chunk zaczyna się w {ordered[0]['start_m']} m, nie w 0")
    if abs(float(ordered[-1]["end_m"]) - axis) > length_tolerance_m:
        problems.append(f"ostatni chunk kończy się w {ordered[-1]['end_m']} m, oś ma {axis} m")

    for chunk in ordered:
        span = float(chunk["end_m"]) - float(chunk["start_m"])
        if span <= 0.0:
            problems.append(f"{chunk['id']}: zakres chainage nie rośnie")
        if abs(span - float(chunk["length_m"])) > seam_tolerance_m:
            problems.append(f"{chunk['id']}: length_m {chunk['length_m']} != {span}")
        if int(chunk["vertices"]) <= 0 or int(chunk["triangles"]) <= 0:
            problems.append(f"{chunk['id']}: pusta geometria")
        size = [float(chunk["bbox_max_m"][i]) - float(chunk["bbox_min_m"][i]) for i in range(3)]
        if max(size) <= 0.0:
            problems.append(f"{chunk['id']}: bbox zwinięty do punktu")

    for previous, current in zip(ordered, ordered[1:]):
        seam = float(current["start_m"]) - float(previous["end_m"])
        if abs(seam) > seam_tolerance_m:
            kind = "dziura" if seam > 0 else "zakładka"
            problems.append(f"{kind} {abs(seam):.6f} m między {previous['id']} a {current['id']}")

    total = sum(float(c["length_m"]) for c in chunks)
    if abs(total - axis) > length_tolerance_m:
        problems.append(f"suma długości chunków {total:.3f} m != długość osi {axis} m")

    totals = manifest.get("totals") or {}
    for key in ("vertices", "faces", "triangles"):
        if key in totals and sum(int(c[key]) for c in chunks) != int(totals[key]):
            problems.append(f"suma {key} po chunkach != totals.{key}")

    covered = [s for c in chunks for s in c.get("stations", [])]
    declared = manifest.get("station_count")
    if declared is not None and len(covered) != int(declared):
        problems.append(f"stacje w chunkach: {len(covered)}, deklarowane: {declared}")
    return problems
