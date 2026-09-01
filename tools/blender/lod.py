"""Poziomy szczegółowości i geometria kolizyjna chunków tunelu — czysty Python, bez bpy.

Manifest streamingowy z `sweep.py` mówi, CO wczytać. Ten moduł odpowiada na dwa
pozostałe pytania: **w jakiej rozdzielczości** to rysować i **czym testować kolizje**.

Trzy decyzje, na których stoi cały moduł:

1. **LOD to podzbiór pierścieni LOD0, nie nowe zagęszczenie osi.** Generator jest
   parametryczny, więc rzadszy LOD dałoby się zrobić przez `--ring-step 20`. Nie robi
   się tego, bo `catmull_rom` z innym krokiem daje inną długość osi i inne chainage
   pierścieni, więc granice chunków przestałyby się pokrywać między poziomami —
   przełączenie LOD-a na szwie otwierałoby dziurę. Tutaj wszystkie poziomy siedzą
   na tych samych ramkach, pierwszy i ostatni pierścień chunka jest zawsze zachowany,
   więc szczelina na szwie jest zerowa **z konstrukcji, także między różnymi LOD-ami**.

2. **Krok pierścieni ma dwa parametry, nie jeden.** Stały krok metryczny jest zły na
   osi, która ma i 700-metrowe proste, i łuki o R = 91,5 m: krok 60 m na prostej nie
   kosztuje nic, a na tym łuku odchyla powierzchnię o 2,2 m. Dlatego selekcja bierze
   `max_chord_m` (górny limit długości cięciwy) **i** `max_sagitta_m` (górny limit
   strzałki, czyli odchyłki wyrzuconych pierścieni od cięciwy). Na prostej rządzi
   pierwszy, na łuku drugi.

3. **Kolizja to wnętrze, nie ściany, i nie jest zamykana czapkami na szwach.**
   Szczegóły i uzasadnienie: `collision_solid` i `reports/L1_A-lod.md` §4.

Układ jak wszędzie: 1 jednostka = 1 metr, oś w XY, Z w górę (docs/04-conventions.md).
"""
import math

import sweep as SW

# --- poziomy ------------------------------------------------------------------
#
# ZAŁOŻENIE PROJEKTOWE, nie dana o sieci. Trzy poziomy, każdy opisany parą
# (maksymalna cięciwa, maksymalna strzałka). Poziom 0 zachowuje wszystkie pierścienie,
# więc jest referencją, wobec której mierzy się błąd pozostałych.
LOD_LEVELS = (
    {"level": 0, "max_chord_m": 0.0, "max_sagitta_m": 0.0,
     "purpose": "chunk pod pociągiem i w bliskim planie — pełny zestaw pierścieni"},
    {"level": 1, "max_chord_m": 25.0, "max_sagitta_m": 0.15,
     "purpose": "plan średni — strzałka poniżej 1 px na ok. 150 m"},
    {"level": 2, "max_chord_m": 60.0, "max_sagitta_m": 0.35,
     "purpose": "plan daleki — strzałka poniżej 1 px na ok. 350 m"},
)

# Budżet błędu ekranowego, z którego wyprowadzają się progi odległości. Kamery wnętrza
# zestawu `alignment` mają obiektyw 35 mm na matrycy 36 mm i 960 px szerokości, więc
# jeden piksel to hfov/px radiana. ZAŁOŻENIE PROJEKTOWE: docelowe budżety mają zostać
# zmierzone na rzeczywistym sprzęcie w T-400, tutaj jest tylko jawny wzór.
PIXEL_BUDGET_LENS_MM = 35.0
PIXEL_BUDGET_SENSOR_MM = 36.0
PIXEL_BUDGET_WIDTH_PX = 960
PIXEL_BUDGET_TOLERANCE_PX = 1.0

# Kolizja: własny, ostrzejszy limit strzałki niż LOD2, bo błąd kolizji nie jest
# kosmetyczny — patrz `collision_solid`.
COLLISION_MAX_CHORD_M = 25.0
COLLISION_MAX_SAGITTA_M = 0.10
# Wcięcie obrysu do środka. Cięciwa po wewnętrznej stronie łuku wypycha powierzchnię
# NA ZEWNĄTRZ prawdziwego światła tunelu o co najwyżej strzałkę, czyli o 0,10 m.
# Bryła kolizyjna, która wystaje w ścianę, przepuszcza pociąg przez mur, więc obrys
# jest wcięty o strzałkę plus zapas — wtedy bryła jest gwarantowanie WEWNĄTRZ tunelu.
COLLISION_INSET_MARGIN_M = 0.05
COLLISION_INSET_M = round(COLLISION_MAX_SAGITTA_M + COLLISION_INSET_MARGIN_M, 6)
# ZAŁOŻENIE PROJEKTOWE: promień, w którym bryła kolizyjna musi być rezydentna —
# długość składu M7 (94,0 m) z zapasem po obu stronach.
COLLISION_RADIUS_M = 150.0


def level_params(level):
    for entry in LOD_LEVELS:
        if entry["level"] == int(level):
            return entry
    raise ValueError(f"nie ma poziomu LOD {level}")


def pixel_angle_rad(lens_mm=PIXEL_BUDGET_LENS_MM, sensor_mm=PIXEL_BUDGET_SENSOR_MM,
                    width_px=PIXEL_BUDGET_WIDTH_PX):
    """Kąt widzenia jednego piksela — podstawa progów odległości."""
    hfov = 2.0 * math.atan(0.5 * sensor_mm / lens_mm)
    return hfov / float(width_px)


def switch_distance_m(deviation_m, tolerance_px=PIXEL_BUDGET_TOLERANCE_PX, **kwargs):
    """Odległość, od której zmierzone odchylenie schodzi poniżej `tolerance_px` piksela.

    To NIE jest zmierzony budżet klatki, tylko przeliczenie zmierzonego błędu
    geometrycznego na błąd ekranowy. Prawdziwe progi wychodzą z pomiaru wydajności
    w T-400; ten wzór daje im punkt startowy, który da się obronić liczbą.
    """
    if deviation_m <= 0.0:
        return 0.0
    return deviation_m / (tolerance_px * pixel_angle_rad(**kwargs))


# --- wybór pierścieni ---------------------------------------------------------

def sagitta_m(points, first, last):
    """Największa odległość punktów (first, last) od cięciwy first–last."""
    a, b = points[first], points[last]
    worst = 0.0
    for index in range(first + 1, last):
        worst = max(worst, _point_to_segment(points[index], a, b))
    return worst


def _point_to_segment(point, a, b):
    d = SW.sub(b, a)
    length2 = SW.dot(d, d)
    if length2 <= 0.0:
        return SW.norm(SW.sub(point, a))
    t = SW.dot(SW.sub(point, a), d) / length2
    t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
    return SW.norm(SW.sub(point, SW.add(a, SW.scale(d, t))))


def select_rings(positions, station_m, first, last, max_chord_m, max_sagitta_m):
    """Podzbiór pierścieni [first..last] spełniający oba limity; zawsze z końcami.

    Zachłanne dopasowanie cięciwy: od bieżącego pierścienia idziemy tak daleko, jak
    pozwalają oba limity, i tam stawiamy następny pierścień. Końce chunka są w wyniku
    zawsze, bo na nich stoi szew — dzięki temu szczelina między chunkami jest zerowa
    w każdym poziomie i między poziomami.
    """
    if last <= first:
        raise ValueError("chunk potrzebuje co najmniej dwóch pierścieni")
    if max_chord_m <= 0.0 and max_sagitta_m <= 0.0:
        return list(range(first, last + 1))
    keep = [first]
    current = first
    while current < last:
        best = current + 1
        candidate = current + 1
        while candidate <= last:
            if max_chord_m > 0.0 and station_m[candidate] - station_m[current] > max_chord_m:
                break
            if max_sagitta_m > 0.0 and sagitta_m(positions, current, candidate) > max_sagitta_m:
                break
            best = candidate
            candidate += 1
        keep.append(best)
        current = best
    if keep[-1] != last:
        keep.append(last)
    return keep


# --- wielobok profilu ---------------------------------------------------------

def polygon_area_m2(points):
    """Pole wieloboku (dodatnie, bez znaku) — pole przekroju tunelu."""
    total = 0.0
    for (x1, y1), (x2, y2) in zip(points, points[1:] + points[:1]):
        total += x1 * y2 - x2 * y1
    return abs(0.5 * total)


def polygon_perimeter_m(points):
    return sum(math.dist(a, b) for a, b in zip(points, points[1:] + points[:1]))


def point_in_polygon(points, x, y):
    inside = False
    for (x1, y1), (x2, y2) in zip(points, points[1:] + points[:1]):
        if (y1 > y) != (y2 > y):
            cut = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if x < cut:
                inside = not inside
    return inside


def polygon_signed_distance_m(points, x, y):
    """Odległość punktu od brzegu wieloboku; dodatnia wewnątrz, ujemna na zewnątrz."""
    best = float("inf")
    for a, b in zip(points, points[1:] + points[:1]):
        best = min(best, _point_to_segment_2d((x, y), a, b))
    return best if point_in_polygon(points, x, y) else -best


def _point_to_segment_2d(point, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    length2 = dx * dx + dy * dy
    if length2 <= 0.0:
        return math.dist(point, a)
    t = ((point[0] - a[0]) * dx + (point[1] - a[1]) * dy) / length2
    t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
    return math.dist(point, (a[0] + t * dx, a[1] + t * dy))


def inset_polygon(points, distance):
    """Obrys wcięty do środka o `distance` — każda krawędź przesunięta po normalnej.

    Nie zmienia `profiles.py`: obrys wejściowy jest odczytany, wynik jest nowym
    wielobokiem tego modułu. Wymiary profilu pozostają decyzją właściciela (R-005).
    """
    if distance <= 0.0:
        return list(points)
    count = len(points)
    if count < 3:
        raise ValueError("wielobok potrzebuje co najmniej trzech punktów")
    sign = 1.0 if _signed_area(points) > 0.0 else -1.0
    lines = []
    for a, b in zip(points, points[1:] + points[:1]):
        dx, dy = b[0] - a[0], b[1] - a[1]
        length = math.hypot(dx, dy)
        if length <= 0.0:
            raise ValueError("krawędź zerowej długości")
        # normalna do wnętrza dla obiegu przeciwnie do ruchu wskazówek: (-dy, dx)
        nx, ny = -dy / length * sign, dx / length * sign
        lines.append((a[0] + nx * distance, a[1] + ny * distance, dx, dy))
    out = []
    for index in range(count):
        x1, y1, dx1, dy1 = lines[index - 1]
        x2, y2, dx2, dy2 = lines[index]
        cross = dx1 * dy2 - dy1 * dx2
        if abs(cross) < 1e-12:
            out.append((x2, y2))
            continue
        t = ((x2 - x1) * dy2 - (y2 - y1) * dx2) / cross
        out.append((x1 + dx1 * t, y1 + dy1 * t))
    return [(round(x, 6), round(y, 6)) for x, y in out]


def _signed_area(points):
    total = 0.0
    for (x1, y1), (x2, y2) in zip(points, points[1:] + points[:1]):
        total += x1 * y2 - x2 * y1
    return 0.5 * total


def gauge_margin_m(polygon, gauge, track_offsets, samples=40):
    """Najmniejszy zapas między skrajnią pojazdu a brzegiem wieloboku, w metrach.

    Skrajnia pojazdu (`profiles.vehicle_gauge`) NIE jest światłem tunelu i nie jest
    tu geometrią kolizyjną — służy wyłącznie jako kontrola, że wcięcie obrysu nie
    zjadło miejsca, w którym musi się zmieścić M7. Wynik ujemny = bryła kolizyjna
    jest węższa od skrajni i pociąg zderzałby się z powietrzem.
    """
    worst = float("inf")
    for offset in track_offsets:
        for a, b in zip(gauge, gauge[1:] + gauge[:1]):
            for step in range(samples + 1):
                t = step / samples
                x = offset + a[0] + t * (b[0] - a[0])
                y = a[1] + t * (b[1] - a[1])
                worst = min(worst, polygon_signed_distance_m(polygon, x, y))
    return worst


# --- siatka: objętość, zamknięcie, odchyłka -----------------------------------

def rings_of(frames, profile, ring_indices):
    """Pierścienie jako listy punktów 3D, bez zdublowanej kolumny szwu."""
    return [SW.ring_positions(frames[index], profile) for index in ring_indices]


def tube_volume_m3(rings):
    """Objętość zamknięta rurą, po dołożeniu czapek na obu końcach.

    Czapki są liczone tylko do tej metryki i NIE trafiają do eksportu — patrz
    `collision_solid`. Twierdzenie o dywergencji na trójkątach o stałym nawinięciu,
    więc znak zależy od skrętności obrysu; bierzemy wartość bezwzględną, a poprawność
    pilnuje test na prostej rurze o znanej objętości.
    """
    if len(rings) < 2:
        return 0.0
    count = len(rings[0])
    total = 0.0
    for lower, upper in zip(rings, rings[1:]):
        for column in range(count):
            nxt = (column + 1) % count
            total += _tetra(lower[column], lower[nxt], upper[nxt])
            total += _tetra(lower[column], upper[nxt], upper[column])
    for column in range(1, count - 1):
        total += _tetra(rings[0][0], rings[0][column + 1], rings[0][column])
        total += _tetra(rings[-1][0], rings[-1][column], rings[-1][column + 1])
    return abs(total)


def _tetra(a, b, c):
    return SW.dot(a, SW.cross(b, c)) / 6.0


def weld(vertices, faces, digits=6):
    """Skleja wierzchołki leżące w tym samym punkcie i przepisuje ściany.

    Rura ma ZDUBLOWANĄ kolumnę szwu UV (`sweep.build_chunk_from_rings`), więc
    topologicznie jest arkuszem, nie rurą, i test rozmaitości na surowych indeksach
    zawsze pokaże dwie krawędzie brzegowe za dużo. Sklejenie po współrzędnych pyta
    o kształt, a nie o numerację, i to jest pytanie, które ma sens dla kolizji.
    """
    canonical = {}
    remap = []
    for vertex in vertices:
        key = tuple(round(c, digits) for c in vertex)
        remap.append(canonical.setdefault(key, len(canonical)))
    out = []
    for face in faces:
        indices = [remap[i] for i in face]
        collapsed = [a for a, b in zip(indices, indices[1:] + indices[:1]) if a != b]
        if len(collapsed) >= 3:
            out.append(tuple(collapsed))
    return len(canonical), out


def open_edges(faces):
    """Krawędzie należące do innej liczby ścian niż dwie — brzeg siatki."""
    seen = {}
    for face in faces:
        for a, b in zip(face, face[1:] + face[:1]):
            key = (a, b) if a < b else (b, a)
            seen[key] = seen.get(key, 0) + 1
    return [edge for edge, count in seen.items() if count != 2]


def transversally_closed(chunk, columns):
    """Czy bryła jest zamknięta poprzecznie: brzeg to WYŁĄCZNIE dwa końcowe pierścienie.

    Rura tunelu ma być otwarta wzdłuż osi — chunk sąsiedni jest jej dosłowną
    kontynuacją, a czapka na szwie byłaby niewidzialną ścianą w poprzek toru —
    i zamknięta w każdym przekroju, żeby nie dało się wyjść bokiem. Kryterium po
    sklejeniu wierzchołków: krawędzi brzegowych jest dokładnie tyle, ile liczy obwód
    dwóch pierścieni końcowych, i wszystkie leżą na tych pierścieniach.
    """
    count, faces = weld(chunk["vertices"], [tuple(f) for f in chunk["faces"]])
    rings = len(chunk["vertices"]) // columns
    perimeter = columns - 1
    expected = 2 * perimeter
    ends = set(range(perimeter)) | set(range(count - perimeter, count))
    boundary = open_edges(faces)
    on_ends = all(a in ends and b in ends for a, b in boundary)
    return (len(boundary) == expected and on_ends), len(boundary), expected


def deviation_stats(frames, profile, station_m, first, last, ring_indices):
    """Odchylenie powierzchni LOD0 od powierzchni rzadszego LOD-a, w metrach.

    Mierzy się w jedynym kierunku, który coś znaczy: wierzchołki LOD-a są PODZBIOREM
    wierzchołków LOD0, więc odległość LOD -> LOD0 jest tożsamościowo zerowa i nie
    dowodzi niczego. Liczymy odległość każdego wierzchołka LOD0 od powierzchni LOD-a,
    a ta powierzchnia między zachowanymi pierścieniami jest linią prostą w każdej
    kolumnie — więc punkt porównania to interpolacja po chainage w tej samej kolumnie.

    Zwraca max / medianę / p95 / średnią po WSZYSTKICH wierzchołkach LOD0 chunka,
    razem z zachowanymi pierścieniami (te dają zero, bo leżą na powierzchni LOD-a).
    """
    kept = list(ring_indices)
    samples = []
    slot = 0
    for index in range(first, last + 1):
        while slot + 1 < len(kept) and kept[slot + 1] < index:
            slot += 1
        low, high = kept[slot], kept[min(slot + 1, len(kept) - 1)]
        exact = SW.ring_positions(frames[index], profile)
        if index == low or index == high or high == low:
            samples.extend([0.0] * len(exact))
            continue
        span = station_m[high] - station_m[low]
        t = 0.0 if span <= 0.0 else (station_m[index] - station_m[low]) / span
        a = SW.ring_positions(frames[low], profile)
        b = SW.ring_positions(frames[high], profile)
        for column in range(len(exact)):
            lerp = SW.add(a[column], SW.scale(SW.sub(b[column], a[column]), t))
            samples.append(SW.norm(SW.sub(exact[column], lerp)))
    samples.sort()
    count = len(samples)
    return {
        "samples": count,
        "max_m": samples[-1] if count else 0.0,
        "p95_m": samples[min(count - 1, int(0.95 * count))] if count else 0.0,
        "median_m": samples[count // 2] if count else 0.0,
        "mean_m": sum(samples) / count if count else 0.0,
    }


def wall_margin_m(frames, profile_true, profile_used, station_m, first, last, ring_indices):
    """Najmniejszy zapas między powierzchnią rzadkiej rury a prawdziwym światłem tunelu.

    Dla każdego wyrzuconego pierścienia bierzemy punkt powierzchni rzadkiej rury
    (interpolacja między zachowanymi pierścieniami), rzutujemy go na ramkę tego
    pierścienia i pytamy, jak głęboko leży wewnątrz prawdziwego obrysu. Wartość
    dodatnia = bryła jest wewnątrz tunelu; ujemna = wystaje w ścianę.
    """
    kept = list(ring_indices)
    worst = float("inf")
    slot = 0
    for index in range(first, last + 1):
        while slot + 1 < len(kept) and kept[slot + 1] < index:
            slot += 1
        low, high = kept[slot], kept[min(slot + 1, len(kept) - 1)]
        origin, _t, right, up = frames[index]
        a = SW.ring_positions(frames[low], profile_used)
        b = SW.ring_positions(frames[high], profile_used)
        span = station_m[high] - station_m[low]
        t = 0.0 if span <= 0.0 else (station_m[index] - station_m[low]) / span
        for column in range(len(profile_used)):
            point = SW.add(a[column], SW.scale(SW.sub(b[column], a[column]), t))
            local = SW.sub(point, origin)
            worst = min(worst, polygon_signed_distance_m(profile_true,
                                                         SW.dot(local, right),
                                                         SW.dot(local, up)))
    return worst


# --- geometria kolizyjna ------------------------------------------------------

def collision_solid(frames, station_m, profile, first, last,
                    max_chord_m=COLLISION_MAX_CHORD_M,
                    max_sagitta_m=COLLISION_MAX_SAGITTA_M,
                    inset_m=COLLISION_INSET_M, uv_scale=SW.UV_METRES_PER_UNIT):
    """Bryła kolizyjna chunka: WNĘTRZE tunelu, obrys zamiatany rzadziej i wcięty.

    Trzy decyzje i ich uzasadnienie:

    * **obrys zamiatany rzadziej, nie uproszczony wielobok.** `box_double` ma sześć
      punktów; sprowadzenie go do prostokąta oszczędza 2 z 6 kolumn (33 %), ale albo
      podnosi strop o 0,40 m nad prawdziwe światło na całej szerokości (bryła wystaje
      w ścianę), albo obcina 0,32 m w narożach (pociąg zderza się z powietrzem).
      Rzadszy krok pierścieni oszczędza ponad 80 % przy błędzie 0,10 m, więc cała
      oszczędność siedzi w kroku, nie w obrysie.
    * **obrys wcięty o `inset_m`.** Cięciwa po wewnętrznej stronie łuku wypycha
      powierzchnię na zewnątrz prawdziwego światła o co najwyżej strzałkę; wcięcie
      o strzałkę plus zapas gwarantuje, że bryła kolizyjna jest w całości wewnątrz
      tunelu. Kontrola: `wall_margin_m` >= 0 i `gauge_margin_m` > 0.
    * **bez czapek na końcach chunka.** Zamknięcie każdego chunka czapką postawiłoby
      niewidzialną ścianę na każdym z 11 szwów — dokładnie tam, gdzie pociąg jedzie.
      Bryła jest zamknięta POPRZECZNIE (każdy przekrój to domknięta pętla) i styka się
      z sąsiadem na wspólnym pierścieniu, więc suma po chunkach jest szczelna. Czapki
      liczą się wyłącznie do objętości (`tube_volume_m3`) i nie są eksportowane.

    Normalne idą DO WNĘTRZA, tak jak w siatce wizualnej: kolizja typu trimesh
    z wyłączonymi tylnymi ścianami blokuje tylko od strony lica, a pociąg jest w środku.
    (Założenie implementacyjne o Godocie, do potwierdzenia w T-4xx.)
    """
    positions = [f[0] for f in frames]
    kept = select_rings(positions, station_m, first, last, max_chord_m, max_sagitta_m)
    hull = inset_polygon(profile, inset_m)
    chunk = SW.build_chunk_from_rings(frames, station_m, hull, kept, uv_scale)
    chunk["profile"] = hull
    chunk["inset_m"] = inset_m
    chunk["max_chord_m"] = max_chord_m
    chunk["max_sagitta_m"] = max_sagitta_m
    return chunk


def lod_chunk(frames, station_m, profile, first, last, level, uv_scale=SW.UV_METRES_PER_UNIT):
    """Siatka wizualna chunka w podanym poziomie szczegółowości."""
    params = level_params(level)
    positions = [f[0] for f in frames]
    kept = select_rings(positions, station_m, first, last,
                        params["max_chord_m"], params["max_sagitta_m"])
    chunk = SW.build_chunk_from_rings(frames, station_m, profile, kept, uv_scale)
    chunk["level"] = int(level)
    return chunk


# --- predykat wyboru poziomu --------------------------------------------------
#
# ŚWIADOMIE ODDZIELNY od `sweep.chunks_for_train`. Rezydencja i rozdzielczość są
# dwoma różnymi pytaniami: rezydencja („czy plik jest w pamięci") zależy od chainage
# i zmienia się skokowo na granicach chunków, rozdzielczość („którą siatkę pokazać")
# zależy od odległości do kamery i zmienia się w sposób ciągły. Wsadzenie LOD-a do
# predykatu okna zmusiłoby do przeładowania chunka, który JEST już rezydentny, tylko
# dlatego że zmienił się dystans — a to jest dokładnie ta operacja, której streaming
# ma unikać. Dlatego `chunks_for_train` zostaje bez zmiany, a poziom liczy `lod_plan`.

def chunk_distance_m(chunk, chainage_m):
    """Odległość po chainage od pociągu do chunka; 0, gdy pociąg jest w środku."""
    value = float(chainage_m)
    start, end = float(chunk["start_m"]), float(chunk["end_m"])
    if start <= value <= end:
        return 0.0
    return start - value if value < start else value - end


def lod_for_distance(distance_m, thresholds):
    """Poziom dla podanej odległości; `thresholds[k]` to dystans, od którego wolno LOD k+1."""
    level = 0
    for index, limit in enumerate(thresholds):
        if distance_m >= float(limit):
            level = index + 1
    return level


def manifest_thresholds(manifest):
    levels = sorted(manifest.get("lod_levels") or [], key=lambda e: e["level"])
    return [e["switch_distance_m"] for e in levels if e["level"] > 0]


def lod_plan(manifest, chainage_m, radius_m=None, ahead_m=None, behind_m=None,
             heading=1.0, thresholds=None):
    """Poziom szczegółowości dla każdego rezydentnego chunka: {id: level}.

    Rezydencja bierze się z niezmienionego `sweep.chunks_for_train`, więc predykat
    okna nadal jest jedynym źródłem prawdy o tym, co jest w pamięci. Chunk, w którym
    stoi pociąg, ma odległość 0, więc zawsze wypada na poziom 0 — to jest niezmiennik,
    a nie efekt uboczny: właśnie ten chunk jest oglądany z bliska i właśnie dla niego
    wczytana jest bryła kolizyjna.
    """
    if thresholds is None:
        thresholds = manifest_thresholds(manifest)
    resident = SW.chunks_for_train(manifest, chainage_m, radius_m, ahead_m, behind_m, heading)
    return {c["id"]: lod_for_distance(chunk_distance_m(c, chainage_m), thresholds)
            for c in resident}


def collision_plan(manifest, chainage_m, radius_m=None, **window):
    """Chunki, dla których trzeba mieć wczytaną bryłę kolizyjną.

    Kolizja jest osobnym plikiem, więc jej rezydencja jest osobną decyzją i nie
    zależy od tego, w jakim LOD-zie chunk akurat jest rysowany. Domyślny promień to
    ZAŁOŻENIE PROJEKTOWE: 150 m, czyli skład M7 (94,0 m, `data/vehicle/m7-spec.json`)
    z zapasem po obu stronach. Chunk pod pociągiem ma odległość 0, więc jest w wyniku
    zawsze — to jest niezmiennik, na którym stoi cały sens tej listy.
    """
    if radius_m is None:
        radius_m = COLLISION_RADIUS_M
    resident = SW.chunks_for_train(manifest, chainage_m, **window)
    return [c["id"] for c in resident if chunk_distance_m(c, chainage_m) <= float(radius_m)]


def lod_triangles(manifest, plan):
    """Trójkąty, które trafiłyby na kartę graficzną dla danego planu poziomów."""
    by_id = {c["id"]: c for c in manifest["chunks"]}
    total = 0
    for chunk_id, level in plan.items():
        chunk = by_id[chunk_id]
        entry = next(l for l in chunk["lods"] if l["level"] == level)
        total += int(entry["triangles"])
    return total


# --- kontrola manifestu -------------------------------------------------------

def lod_problems(manifest, seam_tolerance_m=1e-6):
    """Kontrola części LOD/kolizja manifestu — lista problemów, pusta znaczy OK.

    Osobna funkcja obok `sweep.manifest_problems`, żeby stare manifesty schematu 1
    nadal dawały się sprawdzić tamtą; ta wymaga schematu >= 2.
    """
    problems = []
    if int(manifest.get("schema_version", 0)) < 2:
        return ["manifest jest w schemacie < 2, nie ma LOD-ów"]
    header = sorted(manifest.get("lod_levels") or [], key=lambda e: e["level"])
    if not header:
        return ["manifest nie deklaruje ani jednego poziomu LOD"]
    if [e["level"] for e in header] != list(range(len(header))):
        problems.append("poziomy LOD w nagłówku nie są ciągłe od zera")
    if len(header) < 3:
        problems.append(f"tylko {len(header)} poziomy LOD, wymagane co najmniej 3")
    for previous, current in zip(header, header[1:]):
        if current["switch_distance_m"] <= previous["switch_distance_m"]:
            problems.append(f"próg LOD {current['level']} nie jest dalszy od poprzedniego")
        if current["max_chord_m"] <= previous["max_chord_m"] and previous["level"] > 0:
            problems.append(f"LOD {current['level']} nie jest rzadszy od poprzedniego")
    for entry in header:
        if entry.get("status") != "design_assumption":
            problems.append(f"próg LOD {entry['level']} nie jest oznaczony jako założenie")

    wanted = [e["level"] for e in header]
    for chunk in manifest.get("chunks") or []:
        lods = chunk.get("lods")
        if not lods:
            problems.append(f"{chunk['id']}: brak listy lods")
            continue
        if [l["level"] for l in sorted(lods, key=lambda l: l["level"])] != wanted:
            problems.append(f"{chunk['id']}: poziomy nie zgadzają się z nagłówkiem")
            continue
        base = next(l for l in lods if l["level"] == 0)
        if base["file"] != chunk["file"] or int(base["triangles"]) != int(chunk["triangles"]):
            problems.append(f"{chunk['id']}: LOD 0 nie jest tym samym co siatka bazowa")
        if float(base["max_deviation_m"]) != 0.0:
            problems.append(f"{chunk['id']}: LOD 0 ma niezerowy błąd wobec siebie")
        for previous, current in zip(sorted(lods, key=lambda l: l["level"])[:-1],
                                     sorted(lods, key=lambda l: l["level"])[1:]):
            if int(current["triangles"]) > int(previous["triangles"]):
                problems.append(f"{chunk['id']}: LOD {current['level']} nie jest tańszy "
                                f"od LOD {previous['level']}")
            if float(current["max_deviation_m"]) < float(previous["max_deviation_m"]):
                problems.append(f"{chunk['id']}: LOD {current['level']} ma mniejszy błąd "
                                f"niż LOD {previous['level']}")
        for entry in lods:
            if int(entry["triangles"]) <= 0 or int(entry["vertices"]) <= 0:
                problems.append(f"{chunk['id']}: LOD {entry['level']} ma pustą geometrię")
            if abs(float(entry["start_m"]) - float(chunk["start_m"])) > seam_tolerance_m or \
               abs(float(entry["end_m"]) - float(chunk["end_m"])) > seam_tolerance_m:
                problems.append(f"{chunk['id']}: LOD {entry['level']} ma inny zakres chainage "
                                f"niż chunk — szew rozjechałby się przy przełączeniu")

        collision = chunk.get("collision")
        if not collision:
            problems.append(f"{chunk['id']}: brak geometrii kolizyjnej")
            continue
        if int(collision["triangles"]) >= int(base["triangles"]):
            problems.append(f"{chunk['id']}: kolizja nie jest tańsza od siatki wizualnej")
        if not collision.get("transversally_closed"):
            problems.append(f"{chunk['id']}: bryła kolizyjna nie jest zamknięta poprzecznie")
        if float(collision["wall_margin_m"]) < 0.0:
            problems.append(f"{chunk['id']}: bryła kolizyjna wystaje poza światło tunelu "
                            f"({collision['wall_margin_m']} m)")
        if float(collision["gauge_margin_m"]) <= 0.0:
            problems.append(f"{chunk['id']}: bryła kolizyjna nie mieści skrajni M7")
        if float(collision["volume_m3"]) <= 0.0:
            problems.append(f"{chunk['id']}: objętość bryły kolizyjnej nie jest dodatnia")
        if abs(float(collision["start_m"]) - float(chunk["start_m"])) > seam_tolerance_m or \
           abs(float(collision["end_m"]) - float(chunk["end_m"])) > seam_tolerance_m:
            problems.append(f"{chunk['id']}: kolizja ma inny zakres chainage niż chunk")
    return problems
