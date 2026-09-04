"""Decyzje osadzenia składu w tunelu — czysty Python, bez Blendera.

Wydzielone z `place_vehicle.py`, który robi `import bpy` na poziomie modułu.
Przemiatanie mutacyjne z 03.09.2026 dało tam 7 mutacji i 7 ocalałych. Droga do
modułu istniała — `tools/tests/test_blender_cli.py` od 02.09.2026 podstawia
atrapę `bpy` i importuje `place_vehicle` bez przeszkód — ale sześć z siedmiu
mutacji siedziało wewnątrz `main()`, za `bpy.ops.object.select_all`
i `bpy.ops.import_scene.gltf`. Nieosiągalna była nie ścieżka importu, a same
bramki. Siódma (`o.type == "MESH"`) wymaga prawdziwej sceny i zostaje
w `place_vehicle.py`, gdzie ją weryfikuje CI z Blenderem.

To ta sama ekstrakcja co `tunnel_manifest.py` (#142), `m7_report.py` (#144),
`profile_scan.py` (#154), `glb_report.py` (#160), `capture_plan.py` (#161)
i `camera_aim.py` (#162), na siódmym module.

Cztery pytania, na które odpowiada się liczbami, i wszystkie cztery są bramkami:

    track_offset        który tor, z odmową zamiast cudzego toru albo IndexError
    resolve_chainage    gdzie postawić czoło składu — wprost albo na najgorszym łuku
    clearance_tally     najgorszy luz w składzie i minimum każdego pudła
    clearance_problem   czy zmierzony luz wolno wypuścić

W `place_vehicle.py` zostaje import GLB, ustawianie macierzy pudeł, chodzenie
po wierzchołkach siatki i eksport.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import placement as PL  # noqa: E402

# Skład M7 to sześć sztywnych pudeł. Cięciwa do szukania najgorszego łuku jest
# długością JEDNEGO pudła, bo na łuku każde pudło opiera się na własnej cięciwie
# i to ona, a nie całe 94 m, decyduje o luzie.
M7_BODIES = 6.0


def track_offset(offsets, index):
    """Przesunięcie żądanego toru, albo odmowa z liczbami.

    Numer toru jest indeksem do listy z profilu. Poza zakresem oznacza cichy wybór
    cudzego toru (dla indeksu ujemnego, bo Python liczy od końca) albo `IndexError`
    w środku pomiaru — jedno i drugie gorsze niż odmowa.
    """
    if not 0 <= index < len(offsets):
        raise ValueError(f"ma {len(offsets)} torów, żądano {index}")
    return offsets[index]


def resolve_chainage(chainage, points, length_m):
    """Chainage czoła i środka składu oraz promień w środku.

    `worst` znaczy „policz sam": narzędzie szuka najciaśniejszego łuku na osi,
    bo pomiar luzu ma sens tam, a nie tam, gdzie ktoś akurat postawił skład.
    Każda inna wartość jest metrami czoła i wtedy promienia nie liczymy —
    `None` w raporcie jest uczciwsze niż promień policzony gdzie indziej.
    """
    if chainage == "worst":
        station, radius = PL.worst_chainage(points, length_m / M7_BODIES, length_m)
        return station - length_m / 2.0, station, radius
    start = float(chainage)
    return start, start + length_m / 2.0, None


def clearance_tally(bodies):
    """Najgorszy luz w całym składzie i minimum osobno dla każdego pudła.

    `bodies` to pary `(nazwa, próbki)`, a próbka to
    `(luz, chainage, bok, wysokość)` jednego wierzchołka. Pudło bez ani jednego
    wierzchołka zostaje z nieskończonością i tak trafia do raportu — pusta bryła
    ma być widoczna, a nie podszywać się pod zerowy luz.

    Przy remisie wygrywa PIERWSZE napotkane pudło. To nie jest obojętne: obok
    samej liczby zapisujemy nazwę bryły i chainage, więc „ten sam luz" w dwóch
    miejscach daje dwa różne wiersze raportu.
    """
    worst = {"clearance_m": float("inf"), "object": "", "chainage_m": 0.0,
             "lateral_m": 0.0, "vertical_m": 0.0}
    per_object = {}
    for name, samples in bodies:
        local_worst = float("inf")
        for clearance, chainage, lateral, vertical in samples:
            local_worst = min(local_worst, clearance)
            if clearance < worst["clearance_m"]:
                worst = {"clearance_m": clearance, "object": name,
                         "chainage_m": chainage, "lateral_m": lateral,
                         "vertical_m": vertical}
        per_object[name] = round(local_worst, 4)
    return worst, per_object


def clearance_problem(clearance_m, minimum_m):
    """Gotowy komunikat odmowy albo `None`, gdy luz wolno wypuścić.

    Równość przechodzi i jest to zachowanie przeniesione wiernie: próg jest dolną
    granicą DOPUSZCZALNEGO luzu, więc „nie mniej niż" nie znaczy „więcej niż".
    Przy domyślnym progu 0,0 m rozstrzyga się to na styku pojazdu ze ścianą —
    luz dokładnie zerowy jeszcze przechodzi, ujemny już nie.
    """
    if clearance_m < minimum_m:
        return (f"zmierzony luz {clearance_m:.4f} m poniżej progu "
                f"{minimum_m:.4f} m — pojazd wchodzi w ścianę tunelu")
    return None
