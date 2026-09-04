"""Werdykt kontroli round-trip GLB — czysty Python, bez Blendera.

Wydzielone z `glb_roundtrip.py`, który importuje `bpy` i przez to nie daje się
zaimportować w `tools/tests/test_all.py`. Przemiatanie mutacyjne z 03.09.2026
pokazało tam 10 mutacji i 10 ocalałych — 100 %, i **nie z braku testów, tylko
z braku drogi**: żaden test nie mógł tego pliku nawet zaimportować. Czwarta taka
ekstrakcja po `tunnel_manifest.py` (#142), `m7_report.py` (#144)
i `profile_scan.py` (#154).

Podział jest ten sam co w tamtych trzech. Tutaj zostaje wszystko, co ODPOWIADA
NA PYTANIE „czy plik przeżył eksport": składanie bboxa z narożników, kontrola
skończoności i — najważniejsze — **lista zarzutów**, czyli sama bramka.
W `glb_roundtrip.py` zostaje czyszczenie scenu, `bpy.ops.import_scene.gltf`
i chodzenie po obiektach Blendera.

Progi są tu, a nie u wołającego, bo to one są treścią bramki.
"""
import math

TOLERANCE_M = 0.01
COUNT_TOLERANCE = 0.10
# Eksport glTF rozszczepia wierzchołki na szwach UV, więc wierzchołków po imporcie
# jest WIĘCEJ niż zgłosił generator i sufit musi być luźny. Mnożnik stoi tutaj jako
# stała nazwana, a nie jako `* 4` w środku porównania — inaczej nie da się o niego
# zapytać z testu, a właśnie o niego pyta bramka.
VERTEX_CEILING_FACTOR = 4.0


def bbox_from_corners(corner_groups):
    """Wspólny bbox z grup narożników. Zwraca `(lo, hi)`, obie po trzy liczby.

    Wejściem są grupy, nie płaska lista, bo w Blenderze narożniki przychodzą per
    obiekt i przeliczone przez jego macierz świata — ta funkcja nie musi o tym
    wiedzieć, ale kształt wejścia zostaje ten sam, żeby wołający nie spłaszczał.

    Brak narożników to `inf`/`-inf`, dokładnie jak w oryginale: pusta scena ma
    zostać złapana przez `finite_bbox`, a nie przemilczana zerem.
    """
    lo = [math.inf] * 3
    hi = [-math.inf] * 3
    for corners in corner_groups:
        for corner in corners:
            for i in range(3):
                lo[i] = min(lo[i], corner[i])
                hi[i] = max(hi[i], corner[i])
    return lo, hi


def finite_bbox(lo, hi):
    """Czy bbox nadaje się do czegokolwiek. `False` dla NaN, `inf` i pustej sceny.

    Osobna funkcja, a nie `raise` w środku składania, bo to jest pytanie, na które
    bramka odpowiada, a nie awaria składania. Pusta scena trafia tu jako `inf`.
    """
    for value in list(lo) + list(hi):
        if math.isnan(value) or math.isinf(value):
            return False
    return True


def bbox_size(lo, hi):
    """Rozmiar bboxa w metrach, po osi. Nie zaokrągla — zaokrąglenie jest formatem."""
    return [hi[i] - lo[i] for i in range(3)]


def vertex_ceiling(expected_vertices):
    """Sufit liczby wierzchołków po imporcie, powyżej którego to już nie jest ten mesh.

    Wystawione jako funkcja **specjalnie po to, żeby test mógł dotknąć granicy**.
    `expected * (1 + 0.10) * 4.0` nie jest liczbą, którą da się bezpiecznie wpisać
    do testu z ręki: `10 * 1.1` to 11.000000000000002, więc „wartość na granicy"
    napisana odruchowo wypada obok granicy i nie odróżnia `>` od `>=`. Test woła
    tę funkcję i podaje jej wynik jako wejście — wtedy trafia dokładnie.
    """
    allowed = max(1.0, expected_vertices * (1.0 + COUNT_TOLERANCE))
    return allowed * VERTEX_CEILING_FACTOR


def roundtrip_problems(objects, vertices, faces, without_uv, size_m,
                       expect_objects=None, expected=None, allow_missing_uv=False):
    """Lista zarzutów wobec wczytanego pliku. Pusta lista = plik przeszedł.

    To jest cała bramka round-tripu w jednym miejscu. Zwraca listę zdań po polsku,
    w ustalonej kolejności, bo ta lista trafia do komunikatu błędu i kolejność ma
    być powtarzalna między przebiegami.

    `expected` to metryki zgłoszone przez generator (`bbox_size_m`, `vertices`,
    `faces`) albo `None`, gdy nie ma z czym porównywać.
    """
    problems = []
    if vertices == 0 or faces == 0:
        problems.append("geometria pusta po imporcie")
    if without_uv and not allow_missing_uv:
        problems.append(f"obiekty bez UV: {list(without_uv)}")
    if expect_objects is not None and objects != expect_objects:
        problems.append(f"obiektów {objects}, oczekiwano {expect_objects}")
    if expected is not None:
        for i, axis in enumerate("XYZ"):
            delta = abs(size_m[i] - expected["bbox_size_m"][i])
            if delta > TOLERANCE_M:
                problems.append(f"bbox {axis} rozjazd {delta:.4f} m > {TOLERANCE_M} m")
        if vertices < expected["vertices"] or vertices > vertex_ceiling(expected["vertices"]):
            problems.append(f"wierzchołków {vertices}, generator zgłosił {expected['vertices']}")
        if faces < expected["faces"]:
            problems.append(f"ścian {faces} < {expected['faces']} zgłoszonych przez generator")
    return problems
