#!/usr/bin/env python3
"""Przekroje i wybór peronów stacji — czysty Python, bez `bpy`.

**Dlaczego osobny moduł.** Do 06.09.2026 te funkcje siedziały w `station_kit.py`,
tuż obok `import bpy`. Nie wołały Blendera ani razu, ale mieszkały w module, którego
zestaw testów nie potrafi zaimportować — więc **żaden test nie mógł ich dotknąć**,
a przegląd mutacyjny liczył je jako „nieosiągalne": 12 z 13 mutacji tego pliku.
`reports/mutation-sweep.md` nazywa lekarstwo wprost: „nie testy, tylko dalsze
wyciąganie logiki spod `bpy`".

To ta sama operacja, którą przeszły wcześniej `m7_shell.py` (35 → 2 nieosiągalne),
`tunnel_sweep.py` (35 → 6), `profile_vehicle.py` (26 → 7), `glb_roundtrip.py`
(10 → 1) i `place_vehicle.py` (7 → 1), i ten sam wzorzec: moduł-rodzeństwo bez
`bpy`, z którego skrypt sceny bierze gotowe wierzchołki i ściany.

Osie wg `docs/04-conventions.md`: X wzdłuż osi trasy, Y w poprzek (0 = oś toru),
Z w górę (0 = główka szyny). 1 jednostka = 1 metr.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "tools", "track"))

import placement as PL  # noqa: E402
import profiles  # noqa: E402
import sweep as SW  # noqa: E402

#: ZAŁOŻENIE 2. O tyle peron cofa się od ściany komory, żeby nie wchodzić w nią siatką.
DESIGN_WALL_SETBACK_M = 0.10

#: ZAŁOŻENIE 3. Pas ostrzegawczy przy krawędzi — osobna bryła, żeby dało się go
#: sprawdzić i pomalować niezależnie od płyty.
DESIGN_EDGE_STRIP_M = 0.60

#: ZAŁOŻENIE 4. Peron jest pełny od główki szyny w górę.
DESIGN_SOLID_FROM_RAIL_HEAD = True

DESIGN_ASSUMPTIONS = {
    "DESIGN_WALL_SETBACK_M": DESIGN_WALL_SETBACK_M,
    "DESIGN_EDGE_STRIP_M": DESIGN_EDGE_STRIP_M,
    "DESIGN_SOLID_FROM_RAIL_HEAD": DESIGN_SOLID_FROM_RAIL_HEAD,
}

def straight_prism(points, stations, at_m, length_m, section):
    """Graniastosłup PROSTY w ramce lokalnej — dla brył krótkich i poprzecznych.

    Zamiatanie po łuku (`sweep_section`) ma sens dla peronu i antresoli, które idą
    wzdłuż osi na dziesiątki metrów. Schody, winda, korytarz i portal są krótkie albo
    stoją w poprzek toru; zamiatanie ich po łuku wykręciłoby stopień i szyb windy.
    Błąd prostej wobec łuku na `length_m` to strzałka cięciwy: przy najciaśniejszym
    promieniu pakietu A (97 m) i najdłuższej takiej bryle (4,0 m portalu) wychodzi
    20,6 mm — mniej niż grubość płyty i mniej niż szczelina peron–pudło.
    """
    position, index, _t = PL.frame_at(points, stations, at_m)
    forward = SW.unit(SW.sub(points[min(index + 1, len(points) - 1)], points[index])) \
        if index + 1 < len(points) else (1.0, 0.0, 0.0)
    right = SW.unit(SW.cross(forward, SW.UP_WORLD))
    up = SW.unit(SW.cross(right, forward))

    verts = []
    for distance in (0.0, length_m):
        origin = SW.add(position, SW.scale(forward, distance))
        for y, z in section:
            verts.append(SW.add(origin, SW.add(SW.scale(right, y), SW.scale(up, z))))

    width = len(section)
    faces = []
    for i in range(width):
        j = (i + 1) % width
        faces.append((i, j, width + j, width + i))
    faces.append(tuple(range(width - 1, -1, -1)))
    faces.append(tuple(range(width, 2 * width)))
    return verts, faces

def wall_offset_m(profile_name):
    """Odległość ściany komory od osi trasy, z profilu.

    Przez `profile_points`, a nie przez `PROFILES[...]["points"]`: klucza `points`
    nie mają profile okrągłe (`bore_single` opisuje się promieniem i środkiem),
    a `--profile` przyjmuje KAŻDY profil z rejestru. Pierwsza wersja czytała klucz
    wprost i wywracała się na `bore_single` z gołym `KeyError: 'points'` —
    zamiatanie nie zaczynało się w ogóle, więc żaden render tego nie pokazywał.
    """
    return max(abs(x) for x, _z in profiles.profile_points(profile_name))

def slab_sections(gap_m, minimum_offset_m, wall_m, height_m, track_offset_m, side):
    """Przekrój płyty i pasa ostrzegawczego po jednej stronie, w metrach lokalnych.

    Zwraca dwie listy `(y, z)`: płyta i pas. `side` to +1 albo -1.
    """
    inner = track_offset_m + side * (minimum_offset_m + gap_m)
    outer = side * (wall_m - DESIGN_WALL_SETBACK_M)
    if side > 0:
        assert outer > inner, (inner, outer)
        strip_far = min(outer, inner + DESIGN_EDGE_STRIP_M)
    else:
        assert outer < inner, (inner, outer)
        strip_far = max(outer, inner - DESIGN_EDGE_STRIP_M)

    slab = [(inner, 0.0), (outer, 0.0), (outer, height_m), (inner, height_m)]
    strip = [(inner, height_m), (strip_far, height_m),
             (strip_far, height_m + 0.001), (inner, height_m + 0.001)]
    return slab, strip

def selected_platforms(platforms, only_station):
    """Perony do zbudowania. `only_station` puste albo `None` znaczy WSZYSTKIE.

    Wyjęte z `main()` na poziom modułu, bo tam siedziało za `bpy.ops` i żaden test
    nie mógł tego dotknąć — przemiatanie mutacyjne z 03.09.2026 pokazało tu mutację
    ocalałą. Sam filtr nie potrzebuje Blendera i jest bramką: `--only-station`
    z literówką ma dać PUSTĄ listę, a nie po cichu zbudować wszystko.

    Nazwa musi zgadzać się dokładnie. Dopasowanie po fragmencie byłoby gorsze niż
    brak filtru: „Arts" trafiałoby w „Arts-Loi" i w każdą inną stację z tym słowem.
    """
    if not only_station:
        return list(platforms)
    return [p for p in platforms if p["name"] == only_station]

def side_tag(side):
    """'R' dla strony dodatniej, 'L' dla ujemnej — to trafia do NAZWY bryły.

    Też wyjęte z `main()`. Pomyłka tutaj nie wywraca niczego: bryły powstają
    poprawne, tylko z zamienionymi nazwami, więc wszystkie kontrole geometryczne
    przechodzą, a peron prawy nazywa się lewym. Taki błąd wychodzi dopiero wtedy,
    gdy ktoś w scenie szuka peronu po nazwie.

    Zero nie jest stroną i nie ma tu cichej odpowiedzi: wołający podaje +1 albo -1.
    """
    if side > 0:
        return "R"
    if side < 0:
        return "L"
    raise ValueError("strona peronu musi być dodatnia albo ujemna, nie zero")

def sweep_section(points, stations, from_m, to_m, section, step_m):
    """Zamiata przekrój `(y, z)` wzdłuż odcinka osi. Zwraca (wierzchołki, ściany)."""
    ring_at = []
    cursor = from_m
    while cursor < to_m - 1e-9:
        ring_at.append(cursor)
        cursor += step_m
    ring_at.append(to_m)

    verts = []
    for chainage in ring_at:
        position, index, _t = PL.frame_at(points, stations, chainage)
        forward = SW.unit(SW.sub(points[min(index + 1, len(points) - 1)], points[index])) \
            if index + 1 < len(points) else (1.0, 0.0, 0.0)
        right = SW.unit(SW.cross(forward, SW.UP_WORLD))
        up = SW.unit(SW.cross(right, forward))
        for y, z in section:
            verts.append(SW.add(position,
                                SW.add(SW.scale(right, y), SW.scale(up, z))))

    faces = []
    width = len(section)
    for ring in range(len(ring_at) - 1):
        base = ring * width
        nxt = base + width
        for i in range(width):
            j = (i + 1) % width
            faces.append((base + i, base + j, nxt + j, nxt + i))
    # Denka, żeby bryła była zamknięta — inaczej render `_inside` pokazuje wnętrze.
    faces.append(tuple(range(width - 1, -1, -1)))
    faces.append(tuple(range(len(verts) - width, len(verts))))
    return verts, faces
