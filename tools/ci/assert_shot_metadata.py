#!/usr/bin/env python3
"""Sprawdza, czy metadane zrzutu z Godota opisują to, co scena naprawdę wczytała.

**Dlaczego to istnieje.** Krok „Screenshots must not be empty frames" woła
`tools/visual/compare.py` **bez `--baseline`**, a `check_geometry` przy braku
baseline zwraca `new-baseline` i wychodzi ZANIM porówna choć jedną liczbę.
`--allow-new-baseline` zamienia to w `pass`. Wyjście bazowe mówi to wprost:

    new-baseline geometria    <- brak metadanych baseline
    [WYNIK] pass — {'total': 6, 'pass': 0, 'fail': 0, 'new_baseline': 6}

Zero `pass`, sześć `new_baseline`. Zmierzone 02.09.2026 audytem mutacyjnym:
przy zielonym CI przechodziły wszystkie z poniższych — przesunięcie bboxa o 1000 m,
`mesh_objects: 0`, `vertices`/`faces` na zerach, `chunks_loaded` o 7 za dużo,
podmieniona rozdzielczość, wyzerowane `axis_length_m` i `last_shot`.

Docstring `FirstRun.WriteShotMetadata` mówi, że te metadane istnieją, bo
„compare.py porównuje je liczbowo, bo obraz tego nie wykryje". W tym workflow
nie porównywał ich z niczym — czyli jedyna obrona przed przesunięciem sceny,
którego kamera nie pokaże, nie działała.

**Dlaczego nie baseline.** Wyjście Godota nie jest stabilne między wersjami
silnika, więc przypięcie pliku baseline dawałoby czerwone CI po każdym
podniesieniu wersji. Zamiast tego sprawdzana jest **spójność wewnętrzna**
metadanych i **zgodność z prawdą policzoną niezależnie**: długość osi liczy
tu Python przez `tools/blender/sweep.py`, a nie parser sceny.
"""
import argparse
import json
import math
import os
import struct
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "blender"))

import profiles  # noqa: E402
import lod as LD  # noqa: E402
import sweep as SW  # noqa: E402

#: Tolerancja porównania długości osi. Ta sama liczba i to samo uzasadnienie,
#: co `FirstRun.AxisManifestToleranceM`: rozdzielczość zapisu, nie zapas.
AXIS_TOLERANCE_M = 1e-3

#: Krok zagęszczania z `TrackAxis.DefaultRingStepM` i `sweep.DEFAULT_RING_STEP_M`.
RING_STEP_M = 5.0

#: Zapas nad wysokością podłogi M7, w którym musi się zmieścić góra brył peronu.
#:
#: Płyta kończy się dokładnie na wysokości podłogi (STIB: podłoga M7 „à hauteur du
#: quai", R-007), a pas ostrzegawczy z `station_kit.py` leży 1 mm nad płytą, żeby dał
#: się pomalować niezależnie. Centymetr to o rząd wielkości więcej niż ten milimetr
#: i o dwa rzędy mniej niż jakikolwiek błąd wysokości, który miałby tu przejść: peron
#: postawiony na poziomie główki szyny albo pod stropem komory wypada z tego
#: przedziału natychmiast.
PLATFORM_TOP_SLACK_M = 0.01


def axis_points(axis_path):
    with open(axis_path, encoding="utf-8") as handle:
        document = json.load(handle)
    return SW.catmull_rom([tuple(float(c) for c in p) for p in document["points"]], RING_STEP_M)


def axis_length_m(axis_path):
    """Długość osi po zagęszczeniu — policzona TU, nie przeczytana z metadanych."""
    return SW.chainages(axis_points(axis_path))[-1]


def axis_scene_bbox(axis_path, low_m=None, high_m=None):
    """Bbox osi w układzie SCENY — kotwica bezwzględna dla bryły tunelu.

    `SceneAxis.ToScene` zamienia punkt danych (X wschód, Y północ, Z w górę) na
    punkt Godota `(X, Z, -Y)`. Zamiana jest tylko przestawieniem osi, bez
    przesuwania układu, więc bbox osi w scenie da się policzyć tutaj — i to jest
    jedyna rzecz, względem której bryła tunelu ma bezwzględne położenie.

    Bez tego przesunięcie CAŁEJ sceny przechodzi: `size_m` zostaje spójne z bboxem,
    bo min i max jadą razem. Zmierzone: bbox przesunięty o 1000 m na każdej osi
    przechodził wszystkie pozostałe kontrole tego pliku.

    `low_m` i `high_m` zawężają oś do OKNA STREAMOWANIA. Odkąd scena streamuje,
    bryła tunelu nie obejmuje całej osi i nie ma prawa obejmować — obejmuje ten jej
    kawałek, który predykat kazał trzymać w pamięci. Kotwica jest przez to CIAŚNIEJSZA
    niż przed streamowaniem, a nie luźniejsza: przed zmianą wystarczyło zawrzeć oś
    długą na 6,7 km, teraz trzeba trafić w odcinek 900-metrowy we właściwym miejscu.
    """
    points = axis_points(axis_path)
    if low_m is not None or high_m is not None:
        chainages = SW.chainages(points)
        lo = -float("inf") if low_m is None else float(low_m)
        hi = float("inf") if high_m is None else float(high_m)
        # Przedział domknięty, tak samo jak w `sweep.chunks_in_range`: punkt dokładnie
        # na granicy okna należy do okna.
        points = [p for p, c in zip(points, chainages) if lo <= c <= hi]
        if not points:
            raise ValueError(f"okno [{low_m}, {high_m}] m nie zawiera ani jednego punktu osi")
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    zs = [p[2] for p in points]
    return ([min(xs), min(zs), -max(ys)], [max(xs), max(zs), -min(ys)])


def glb_mesh_nodes(path):
    """Read the exported GLB's node table, independently of Godot's scene tree."""
    with open(path, "rb") as handle:
        header = handle.read(20)
        if len(header) != 20 or header[:4] != b"glTF":
            raise ValueError(f"{path}: brak nagłówka GLB")
        version, length = struct.unpack_from("<II", header, 4)
        json_size, chunk_type = struct.unpack_from("<II", header, 12)
        if version != 2 or length != os.path.getsize(path) or chunk_type != 0x4E4F534A \
                or json_size == 0 or json_size > length - 20:
            raise ValueError(f"{path}: niepoprawna struktura GLB")
        document = json.loads(handle.read(json_size).rstrip(b" \x00"))
    count = sum("mesh" in node for node in document.get("nodes", []))
    if count <= 0:
        raise ValueError(f"{path}: GLB bez węzłów siatki")
    return count


def check_visual_continuation(metadata, playable_axis_path, tail_axis_path, assets_dir=None,
                              require_visual_tail=False):
    """Check the visible 300 m tail separately from streamed playable chunks."""
    visual = metadata.get("visual_continuation")
    if visual is None and assets_dir is None and not require_visual_tail:
        return []  # Historical screenshot metadata did not have this section.
    if not isinstance(visual, dict) or type(visual.get("present")) is not bool:
        return ["visual_continuation.present: brak wartości logicznej"]

    problems = []
    if require_visual_tail and not visual["present"]:
        problems.append("visual_continuation: wymagany pakiet scenerii jest nieobecny")
    glb_files = ("L1_A-visual-tail.glb", "L1_A-visual-tail-detail.glb")
    if assets_dir is not None:
        paths = [os.path.join(assets_dir, name) for name in glb_files]
        existing = [os.path.isfile(path) for path in paths]
        if any(existing) != all(existing):
            problems.append("visual_continuation: niekompletna para GLB")
        if visual["present"] != all(existing):
            problems.append("visual_continuation.present nie odpowiada parze GLB")
        packaged_axis = os.path.join(assets_dir, "L1_A-visual-tail-axis.json")
        if not any(existing) and os.path.exists(packaged_axis):
            problems.append("visual_continuation: oś bez pary GLB")
        if all(existing):
            try:
                with open(packaged_axis, encoding="utf-8") as handle:
                    packaged = json.load(handle)
                with open(tail_axis_path, encoding="utf-8") as handle:
                    canonical = json.load(handle)
                if packaged != canonical:
                    problems.append("visual_continuation: zapakowana oś różni się od osi scenerii")
            except (OSError, ValueError) as error:
                problems.append(f"visual_continuation: brak poprawnej osi w pakiecie: {error}")
    else:
        paths = []

    if not visual["present"]:
        if visual.get("mesh_objects") != 0 or visual.get("axis_length_m") != 0 \
                or visual.get("seam_gap_m") != 0 \
                or visual.get("bbox_min") is not None or visual.get("bbox_max") is not None:
            problems.append("visual_continuation: brak zasobów wymaga zerowych metryk")
        return problems

    meshes = visual.get("mesh_objects")
    if not isinstance(meshes, int) or isinstance(meshes, bool) or meshes <= 0:
        problems.append("visual_continuation.mesh_objects musi być dodatnią liczbą")
    if paths and all(os.path.isfile(path) for path in paths):
        try:
            actual_meshes = sum(glb_mesh_nodes(path) for path in paths)
            if meshes != actual_meshes:
                problems.append(f"visual_continuation.mesh_objects = {meshes}, GLB ma {actual_meshes}")
        except (OSError, ValueError, json.JSONDecodeError) as error:
            problems.append(f"visual_continuation: niepoprawny GLB: {error}")

    axis_length = axis_length_m(tail_axis_path)
    reported_length = visual.get("axis_length_m")
    if not isinstance(reported_length, (int, float)) or not math.isfinite(reported_length) or \
            abs(reported_length - axis_length) > AXIS_TOLERANCE_M:
        problems.append(f"visual_continuation.axis_length_m = {reported_length}, oś daje {axis_length:.3f}")
    playable_end = axis_points(playable_axis_path)[-1]
    tail_start = axis_points(tail_axis_path)[0]
    seam_gap = sum((a - b) ** 2 for a, b in zip(playable_end, tail_start)) ** 0.5
    reported_gap = visual.get("seam_gap_m")
    if not isinstance(reported_gap, (int, float)) or not math.isfinite(reported_gap) or \
            abs(reported_gap - seam_gap) > 1e-3 \
            or seam_gap > 0.02:
        problems.append(f"visual_continuation.seam_gap_m = {reported_gap}, osie dają {seam_gap:.4f}")

    lo, hi = visual.get("bbox_min"), visual.get("bbox_max")
    if not all(isinstance(value, list) and len(value) == 3 and
               all(isinstance(number, (int, float)) and math.isfinite(number)
                   for number in value)
               for value in (lo, hi)):
        problems.append("visual_continuation: niekompletna obwiednia")
    else:
        axis_lo, axis_hi = axis_scene_bbox(tail_axis_path)
        profile_width = max(profiles.dimensions("box_double"))
        for coordinate, name in enumerate("XYZ"):
            if lo[coordinate] > axis_lo[coordinate] + 1e-3 or \
                    hi[coordinate] < axis_hi[coordinate] - 1e-3:
                problems.append(f"visual_continuation: obwiednia nie zawiera osi {name}")
            if max(axis_lo[coordinate] - lo[coordinate],
                   hi[coordinate] - axis_hi[coordinate]) > profile_width:
                problems.append(f"visual_continuation: obwiednia za daleko od osi {name}")
    return problems


def load_manifest(manifest_path):
    with open(manifest_path, encoding="utf-8") as handle:
        return json.load(handle)


def streaming_expectations(manifest, chainage_m):
    """Czego predykat POWINIEN był zażądać od sceny na tym chainage.

    Liczone implementacją wzorcową w Pythonie (`sweep`, `lod`), a nie odczytane
    z metadanych — czyli tą samą drogą, którą `tests/Game.Tests/StreamingPlanTests.cs`
    przybija stronę C#. Bramka porównuje więc scenę z niezależnym rachunkiem,
    a nie ze sobą samą.

    Kierunek jazdy jest tu na sztywno „do przodu": scena T-400 jedzie w stronę
    rosnącego chainage i nic w niej nie umie zawrócić. Gdyby to się zmieniło,
    ten rachunek trzeba przekazać, a nie zgadywać.
    """
    axis_end = float(manifest["axis_length_m"])
    clamped = min(float(chainage_m), axis_end)
    low, high = SW.stream_window(clamped, heading=1.0)
    resident = SW.chunks_for_train(manifest, clamped, heading=1.0)
    plan = LD.lod_plan(manifest, clamped, heading=1.0)

    # Zakres osi, który bryła sceny ma OBEJMOWAĆ, to nie jest okno streamowania.
    # Chunk wchodzi do pamięci w całości, więc rezydentny chunk wystaje poza krawędź
    # okna o tyle, ile sam ma długości — na pakiecie A do 725 m. Kotwica liczy się
    # więc na sumie zakresów chunków rezydentnych, a nie na oknie. Zmierzone:
    # przy oknie [1700, 2600] m bryła sięgała 709 m dalej wzdłuż X i to było
    # zachowanie POPRAWNE, a nie usterka.
    span = (min(float(c["start_m"]) for c in resident),
            max(float(c["end_m"]) for c in resident)) if resident else (None, None)

    return {
        "chainage_m": clamped,
        "window": (low, high),
        "span": span,
        "resident_ids": [c["id"] for c in resident],
        "faces": LD.lod_triangles(manifest, plan),
    }


#: Skorupa M7 to 6 pudeł i 5 mieszków między nimi. Liczba brył jest więc funkcją
#: liczby członów z rejestru, a nie osobną stałą do przepisania.
def expected_bodies(cars):
    return 2 * cars - 1


def m7_spec(spec_path):
    """Długość, szerokość i liczba członów M7 — wyłącznie wpisy o statusie `spec`.

    To jest DRUGA, niezależna droga do tych samych liczb: pierwszą jest AABB brył
    odczytany przez `TrainView` z wyeksportowanego GLB. Rozjazd między nimi znaczy,
    że skorupa nie odpowiada rejestrowi — i jest informacją, nie szumem.
    """
    with open(spec_path, encoding="utf-8") as handle:
        registry = json.load(handle)
    out = {}
    for key in ("length_m", "width_m", "cars"):
        entry = registry["parameters"][key]
        if entry.get("status") != "spec":
            raise SystemExit(
                f"BŁĄD: {key} w rejestrze M7 ma status {entry.get('status')!r}, nie 'spec' — "
                "bramka nie ma prawa opierać się na wartości bez źródła")
        out[key] = entry["value"]
    return out


def check_train(metadata, spec_path):
    """Czy w scenie JEST skład i czy to ten skład.

    **Issue #107.** Cały blok `scene` opisuje wyłącznie tunel, więc mutacja
    `TrainView.cs:38` — skorupa nie wczytuje się w ogóle — zostawiała cały
    `godot-first-run.yml` zielony. Próg pustej klatki łapie brak tunelu, bo tunel
    wypełnia kadr; składu w widoku `cab` nie widać z definicji, a w `chase`
    i `outside` jego brak wygląda jak zwykły kadr tunelu.
    """
    problems = []
    train = metadata.get("train")
    if not isinstance(train, dict):
        return ["metadane nie mają bloku `train` — nie ma czym udowodnić, że skład jest w scenie"]

    spec = m7_spec(spec_path)
    bodies = train.get("bodies")
    wanted = expected_bodies(int(spec["cars"]))
    if bodies != wanted:
        problems.append(
            f"train.bodies = {bodies}; rejestr daje {spec['cars']} członów, "
            f"czyli {wanted} brył (pudła + mieszki)")

    length = train.get("length_m")
    if not isinstance(length, (int, float)) or length <= 0.0:
        problems.append(f"train.length_m = {length}; skład zwinięty w punkt albo nieobecny")
    else:
        # Skorupa jest zamiatana po cięciwach, więc jej długość mierzona wzdłuż X jest
        # nieco mniejsza niż nominalna. 1 % to zapas na to, nie na pomyłkę w wymiarze.
        nominal = float(spec["length_m"])
        if abs(length - nominal) > nominal * 0.01:
            problems.append(
                f"train.length_m = {length:.4f}, a rejestr M7 mówi {nominal} "
                f"(status spec) — rozjazd {abs(length - nominal):.4f} m")

    width = train.get("width_m")
    nominal_w = float(spec["width_m"])
    if not isinstance(width, (int, float)) or abs(width - nominal_w) > nominal_w * 0.01:
        problems.append(f"train.width_m = {width}, a rejestr M7 mówi {nominal_w} (status spec)")

    roof = train.get("roof_height_m")
    if not isinstance(roof, (int, float)) or roof <= 0.0:
        problems.append(f"train.roof_height_m = {roof}; bryła bez wysokości nie jest składem")
    return problems


def platform_floor_height_m(spec_path):
    """Wysokość podłogi M7 z rejestru — wyłącznie wpis o statusie `spec`.

    To jest DRUGA, niezależna droga do wysokości peronu. Pierwszą jest AABB brył,
    który `StationView` odczytał z wyeksportowanego GLB. Bramka nie porównuje więc
    generatora z samym sobą.
    """
    with open(spec_path, encoding="utf-8") as handle:
        registry = json.load(handle)
    entry = registry["parameters"]["floor_height_m"]
    if entry.get("status") != "spec":
        raise SystemExit(
            f"BŁĄD: floor_height_m w rejestrze M7 ma status {entry.get('status')!r}, "
            "nie 'spec' — bramka nie ma prawa opierać się na wartości bez źródła")
    return float(entry["value"])


def platform_radius_bounds(layout, metrics):
    """Przedział, w którym musi się zmieścić promień szukania peronu.

    **Po co to jest.** Promień przychodzi z metadanych, czyli OD SCENY, a bramka
    liczy nim swoje oczekiwania — więc scena, która poda promień 20 km, sama sobie
    rozszerza bramkę do „gdziekolwiek na pakiecie" i przechodzi. Zmierzone
    04.09.2026: mutacja `PlatformNearRadiusM 20.0 -> 20000.0` dawała
    `near_shot.slabs = 48` i przechodziła kontrolę przedziału, bo przy takim
    promieniu layout „luźno" obejmował wszystkie dwanaście peronów.

    Oba końce przedziału są policzone z danych, nie przyjęte:

    * **od dołu** — odległość krawędzi peronu od osi TRASY, czyli odsunięcie toru
      z profilu plus największe minimalne odsunięcie krawędzi na pakiecie plus
      szczelina. Promień mniejszy nie sięgnąłby własnego peronu na żadnej stacji
      i `near_shot` byłoby zawsze zerem;
    * **od góry** — połowa najmniejszego odstępu między sąsiednimi peronami.
      Promień większy mógłby złapać peron następnej stacji i „peron jest przy
      składzie" przestałoby cokolwiek znaczyć.
    """
    offsets = profiles.PROFILES[metrics["profile"]]["track_offsets"]
    gap_m = float(metrics["platform_gap_m"])
    edge_m = max(float(p["minimum_edge_offset_m"]) for p in layout["platforms"])
    low = max(abs(o) for o in offsets) + edge_m + gap_m

    ordered = sorted(layout["platforms"], key=lambda p: float(p["from_m"]))
    gaps = [float(b["from_m"]) - float(a["to_m"]) for a, b in zip(ordered, ordered[1:])]
    if not gaps:
        raise SystemExit("BŁĄD: layout ma mniej niż dwa perony — nie da się policzyć "
                         "górnej granicy promienia szukania")
    return low, min(gaps) / 2.0


def platforms_around(layout, chainage_m, radius_m):
    """Ile peronów layoutu obejmuje ten kilometraż — ciasno i luźno.

    Zwraca `(ciasno, luzno)`. `ciasno` liczy perony, w których kilometraż leży
    **z zapasem** `radius_m` od obu końców — tam scena MUSI mieć bryły peronu.
    `luzno` liczy perony, których zakres poszerzony o `2 x radius_m` ten kilometraż
    jeszcze zawiera — poza nimi scena NIE MA PRAWA mieć ani jednej bryły.

    Dwa progi zamiast jednego, bo `PlatformFit.Near` mierzy odległość POZIOMĄ od
    prostopadłościanu, a layout zna tylko kilometraż. Na końcach peronu te dwie miary
    się rozjeżdżają i równość byłaby bramką losową; przedział jest bramką ciasną
    z obu stron i nie zależy od tego, po której stronie końca wypadł zrzut.
    """
    tight = 0
    loose = 0
    for platform in layout["platforms"]:
        low = float(platform["from_m"])
        high = float(platform["to_m"])
        if low + radius_m <= chainage_m <= high - radius_m:
            tight += 1
        if low - 2.0 * radius_m <= chainage_m <= high + 2.0 * radius_m:
            loose += 1
    return tight, loose


def check_platforms(metadata, layout, metrics, spec_path):
    """Czy w scenie JEST peron i czy stoi tam, gdzie stanął skład.

    **Po co dwie kontrole zamiast jednej.** `slabs` mówi, że plik peronów się wczytał
    — i tylko to. Bryła peronów pakietu A ma 5,4 km rozpiętości, więc jej obwiednia
    zawiera każdy punkt, o który dałoby się zapytać: peron odsunięty od osi albo
    wczytany z innej linii przeszedłby taką kontrolę bez mrugnięcia. `near_shot` liczy
    bryły w promieniu wokół punktu osi, na którym stanął skład, i porównuje to z tym,
    co o tym kilometrażu mówi layout policzony osobno.

    Kadr z kabiny stojącej na peronie Beekkant był do 04.09.2026 kadrem PUSTEGO
    tunelu i żadna bramka tego nie widziała: `scene` opisuje wyłącznie tunel, `train`
    wyłącznie skład, a próg pustej klatki mierzy jasność — którą ściany tunelu
    wypełniają tak samo dobrze bez peronu, jak z nim.
    """
    problems = []
    platforms = metadata.get("platforms")
    if not isinstance(platforms, dict):
        return ["metadane nie mają bloku `platforms` — nie ma czym udowodnić, "
                "że peron jest w scenie"]

    declared = int(metrics["objects"])
    slabs = platforms.get("slabs")
    if slabs != declared:
        problems.append(
            f"platforms.slabs = {slabs}, a generator zbudował {declared} brył "
            f"({metrics.get('objects_per_component')}) — scena trzyma inny peron")

    floor_m = platform_floor_height_m(spec_path)
    top = platforms.get("top_m")
    if not isinstance(top, (int, float)):
        problems.append(f"platforms.top_m = {top}; peron bez wysokości nie jest peronem")
    elif not floor_m <= top <= floor_m + PLATFORM_TOP_SLACK_M:
        problems.append(
            f"platforms.top_m = {top} m, a podłoga M7 jest na {floor_m} m (status spec) "
            f"z zapasem {PLATFORM_TOP_SLACK_M} m na pas ostrzegawczy — peron na innej "
            "wysokości niż podłoga nie jest peronem M7")

    lo = platforms.get("bbox_min") or []
    hi = platforms.get("bbox_max") or []
    if len(lo) != 3 or len(hi) != 3:
        problems.append(f"obwiednia peronu niekompletna: min={lo} max={hi}")
    else:
        # Peron ciągnie się wzdłuż osi, czyli w płaszczyźnie (X, Z) sceny. Obwiednia
        # zwinięta wzdłuż którejkolwiek z nich znaczy, że zamiatanie nie ruszyło.
        for axis, name in ((0, "X"), (2, "Z")):
            if hi[axis] - lo[axis] <= 0.0:
                problems.append(
                    f"obwiednia peronu zwinięta wzdłuż {name}: [{lo[axis]}, {hi[axis]}]")
        if isinstance(top, (int, float)) and abs(hi[1] - top) > 1e-3:
            problems.append(
                f"platforms.top_m = {top}, a bbox_max[Y] = {hi[1]} — dwie liczby o tej "
                "samej rzeczy, więc rozjazd znaczy, że jedna z nich jest przepisana")

    near = platforms.get("near_shot") or {}
    radius = near.get("radius_m")
    last_chainage = (metadata.get("last_shot") or {}).get("chainage_m")
    radius_low, radius_high = platform_radius_bounds(layout, metrics)
    if not isinstance(radius, (int, float)) or radius <= 0.0:
        problems.append(f"near_shot.radius_m = {radius}; promień szukania musi być dodatni")
    elif not radius_low <= radius <= radius_high:
        problems.append(
            f"near_shot.radius_m = {radius} m poza przedziałem "
            f"[{radius_low:.3f}, {radius_high:.3f}] m: poniżej dolnej granicy scena nie "
            "sięgnie własnego peronu, powyżej górnej złapie peron sąsiedniej stacji "
            "— w obie strony `near_shot` przestaje znaczyć „peron jest przy składzie\"")
    elif not isinstance(last_chainage, (int, float)):
        problems.append("brak last_shot.chainage_m — nie da się sprawdzić, czy peron "
                        "jest tam, gdzie stanął skład")
    else:
        per_platform = declared / len(layout["platforms"])
        tight, loose = platforms_around(layout, last_chainage, radius)
        found = near.get("slabs")
        low = int(round(per_platform * tight))
        high = int(round(per_platform * loose))
        if not isinstance(found, int) or not low <= found <= high:
            problems.append(
                f"near_shot.slabs = {found} w promieniu {radius} m od kilometrażu "
                f"{last_chainage:.3f} m, a layout daje tam {tight} peronów ciasno "
                f"i {loose} luźno, czyli {low}..{high} brył")
        if low > 0:
            near_top = near.get("top_m")
            if not isinstance(near_top, (int, float)) or \
                    not floor_m <= near_top <= floor_m + PLATFORM_TOP_SLACK_M:
                problems.append(
                    f"near_shot.top_m = {near_top} m przy podłodze M7 {floor_m} m — "
                    "peron pod drzwiami składu jest na innej wysokości niż jego podłoga")
    return problems


def check(metadata, axis_path, resolution, view, chainage_m, manifest=None):
    problems = []
    scene = metadata.get("scene") or {}

    if not scene:
        return ["metadane nie mają sekcji `scene` — scena nic nie opisała"]

    declared = scene.get("chunks_declared")
    loaded = scene.get("chunks_loaded")
    if not declared:
        problems.append(f"chunks_declared = {declared}; manifest bez chunków nie jest sceną")

    # Do 03.09.2026 stało tu `loaded != declared` — „scena ma mieć wczytane wszystko".
    # Warunek jest przepisany, a nie dopisany obok, bo scena STREAMUJE i wczytanie
    # wszystkiego byłoby teraz usterką, nie poprawnością. Zamiast liczby chunków
    # z manifestu porównujemy z tym, czego na tym chainage żąda predykat, policzony
    # tu niezależnie implementacją pythonową. To jest kontrola MOCNIEJSZA od poprzedniej:
    # „12 z 12" spełniała każda scena, która wczytała wszystko, także wtedy gdy okno
    # streamowania było policzone źle albo wcale.
    # Predykat liczy się na chainage, na którym scena NAPRAWDĘ stanęła, a nie na
    # żądanym: skład zatrzymuje się na najbliższym całym kroku, więc żądane 2000 m
    # to w metadanych 2000,068 m, a okno przesunięte o te 68 mm nie jest usterką.
    # Że `last_shot.chainage_m` odpowiada żądaniu, sprawdza osobno kontrola niżej —
    # obie razem są ciaśniejsze niż którakolwiek z osobna.
    #
    # 6.C4: kotwicą GEOMETRII jest `subject_chainage_m`, czyli kilometraż, który kadr
    # pokazuje — bo to on wyznacza okno streamowania. Dla trzech widoków jazdy jest
    # równy `chainage_m` i nic się nie zmienia; dla widoku `inspect` kamera stoi tam,
    # gdzie pojazd nie dojechał, więc kotwica na pojeździe kazałaby scenie trzymać
    # geometrię z DRUGIEGO KOŃCA osi. Zmierzone: przy kotwicy na pojeździe bramka
    # żądała osi [0,000, 385,021] m od scény streamującej [1136,374, 2480,285] m.
    #
    # Sprawdzenie jest po tej zmianie CIAŚNIEJSZE, nie luźniejsze: geometria jest
    # porównywana z miejscem, które kadr NAPRAWDĘ pokazuje, a nie z miejscem, które
    # przy widokach jazdy przypadkiem się z nim pokrywa.
    last = metadata.get("last_shot") or {}
    last_chainage = last.get("subject_chainage_m")
    if not isinstance(last_chainage, (int, float)):
        last_chainage = last.get("chainage_m")
    expected = None
    if manifest is not None and isinstance(last_chainage, (int, float)):
        expected = streaming_expectations(manifest, last_chainage)
        if loaded != len(expected["resident_ids"]):
            problems.append(
                f"scena trzyma {loaded} chunków, a predykat na chainage "
                f"{expected['chainage_m']:.3f} m żąda {len(expected['resident_ids'])} "
                f"({', '.join(expected['resident_ids'])})")

        low, high = expected["window"]
        for key, want in (("window_low_m", low), ("window_high_m", high)):
            got = scene.get(key)
            if not isinstance(got, (int, float)) or abs(got - want) > 1e-3:
                problems.append(
                    f"{key} = {got}, a predykat daje {want:.3f} m — scena streamuje "
                    "z innego okna, niż wynika z manifestu")

        faces = scene.get("faces")
        if faces != expected["faces"]:
            problems.append(
                f"faces = {faces}, a chunki rezydentne w policzonych poziomach LOD "
                f"dają {expected['faces']} — metadane opisują inną geometrię niż scena")
    elif loaded is not None and declared is not None and loaded > declared:
        problems.append(
            f"scena trzyma {loaded} chunków, a manifest deklaruje tylko {declared}")

    for key in ("mesh_objects", "vertices", "faces"):
        value = scene.get(key)
        if not isinstance(value, (int, float)) or value <= 0:
            problems.append(f"{key} = {value}; scena bez geometrii nie jest kontrolą zawartości")

    size = scene.get("size_m") or []
    lo = scene.get("bbox_min") or []
    hi = scene.get("bbox_max") or []
    if len(size) != 3 or len(lo) != 3 or len(hi) != 3:
        problems.append(f"bbox niekompletny: min={lo} max={hi} size={size}")
    else:
        for axis, (a, b, s) in enumerate(zip(lo, hi, size)):
            if abs((b - a) - s) > 1e-3:
                problems.append(f"size_m[{axis}] = {s} nie wynika z bboxa ({a} … {b})")
            if s <= 0.0:
                problems.append(f"size_m[{axis}] = {s}; bryła zwinięta w punkt albo płaszczyznę")

    # Kotwica bezwzględna: bryła tunelu musi ZAWIERAĆ oś i nie może jej przekraczać
    # o więcej niż przekrój tunelu. Profil `box_double` ma 9,40 × 5,90 m, a zmierzone
    # rozszerzenia na pakiecie A to 1,2–4,7 m — czyli mieszczą się w jednej szerokości
    # profilu w każdą stronę.
    profile_width_m = max(profiles.dimensions("box_double"))
    if len(lo) == 3 and len(hi) == 3:
        # Kotwica jest liczona na OKNIE, nie na całej osi: bryła streamowanej sceny
        # obejmuje ten kawałek osi, który predykat kazał trzymać, i tylko ten.
        span = expected["span"] if expected else (None, None)
        axis_lo, axis_hi = axis_scene_bbox(axis_path, span[0], span[1])
        for axis, name in enumerate("XYZ"):
            if lo[axis] > axis_lo[axis] + 1e-6 or hi[axis] < axis_hi[axis] - 1e-6:
                problems.append(
                    f"bryła sceny nie zawiera osi wzdłuż {name}: scena "
                    f"[{lo[axis]:.3f}, {hi[axis]:.3f}], oś [{axis_lo[axis]:.3f}, {axis_hi[axis]:.3f}]")
            slack_lo = axis_lo[axis] - lo[axis]
            slack_hi = hi[axis] - axis_hi[axis]
            if max(slack_lo, slack_hi) > profile_width_m:
                problems.append(
                    f"bryła sceny wystaje poza oś wzdłuż {name} o "
                    f"{max(slack_lo, slack_hi):.3f} m, a przekrój tunelu ma {profile_width_m:.2f} m")

    expected_axis_m = axis_length_m(axis_path)
    reported_axis = scene.get("axis_length_m")
    if not isinstance(reported_axis, (int, float)):
        problems.append(f"axis_length_m = {reported_axis}")
    elif abs(reported_axis - expected_axis_m) > AXIS_TOLERANCE_M:
        problems.append(
            f"axis_length_m = {reported_axis} m, a oś policzona niezależnie ma "
            f"{expected_axis_m:.3f} m (|Δ| = {abs(reported_axis - expected_axis_m):.6f} m)")

    if resolution is not None and list(metadata.get("resolution") or []) != list(resolution):
        problems.append(f"resolution = {metadata.get('resolution')}, żądano {resolution}")

    last = metadata.get("last_shot") or {}
    if view is not None and (last.get("view") or "").lower() != view.lower():
        problems.append(f"last_shot.view = {last.get('view')!r}, żądano {view!r}")
    if chainage_m is not None:
        # Skład zatrzymuje się na najbliższym całym kroku, więc równości nie ma;
        # metr zapasu odróżnia „ten sam kadr" od „kadr z innego miejsca osi".
        #
        # 6.C4: sprawdzany jest `subject_chainage_m`, czyli kilometraż, który kadr
        # NAPRAWDĘ pokazuje. Dla trzech widoków jazdy jest on równy `chainage_m`,
        # bo kamera wisi na składzie. Dla widoku `inspect` nie jest: kamera bierze
        # geometrię z osi, a skład zostaje tam, gdzie stał — zmierzone, zrzut
        # z 2521,1 m zapisywał `chainage_m = 94,0`.
        #
        # Pole jest wymagane TYLKO dla widoku `inspect` i to jest wybór wyprowadzony,
        # nie kompromis. Dla trzech widoków jazdy `subject_chainage_m` jest RÓWNE
        # `chainage_m` z konstrukcji, więc odwrót na drugie pole nie jest cichą zgodą —
        # to ta sama liczba. Dla `inspect` równa nie jest i wtedy brak pola znaczy, że
        # nie ma czym sprawdzić kadru, czyli byłby zielonym zerem.
        #
        # Żądanie pola OD WSZYSTKICH wywracało dziesięć testów bramki, których atrapa
        # jest METADANYMI ZMIERZONYMI na przebiegu Godota 4.3 — a dopisanie do zapisu
        # pomiaru pola, którego tamten przebieg nie wypisał, byłoby jego falsyfikacją.
        # Nazwa pola w komunikacie jest NAZWĄ POLA, KTÓRE NAPRAWDĘ PORÓWNANO —
        # inaczej odmowa mówiłaby o `subject_chainage_m` przy metadanych, które go
        # nie mają, czyli o polu nieistniejącym. Ta sama zasada, co przy 6.A19.
        pole = "subject_chainage_m"
        got = last.get("subject_chainage_m")
        widok = (last.get("view") or "").lower()
        if not isinstance(got, (int, float)):
            pole = "chainage_m"
            if widok == "inspect":
                problems.append(
                    f"brak last_shot.subject_chainage_m (jest {got!r}) przy widoku "
                    "inspect — dla tego widoku kilometraż pojazdu NIE opisuje kadru, "
                    "więc bez tego pola nie ma czego sprawdzić")
            got = last.get("chainage_m")
        if not isinstance(got, (int, float)):
            problems.append(
                f"brak last_shot.chainage_m ani subject_chainage_m (jest {got!r})")
        elif abs(got - chainage_m) > 1.0:
            problems.append(
                f"last_shot.{pole} = {got}, żądano {chainage_m} "
                "(literówka w --at-chainage dawała kadr z innego miejsca osi)")

        # Widok inspekcyjny ma pokazać kilometraż BEZ przejeżdżania do niego, więc
        # `steps` musi być zerem, a kilometraż składu ma się od tematu kadru RÓŻNIĆ,
        # jeżeli tylko cel leży dalej niż start przejazdu. Bez tych dwóch warunków
        # widok „inspekcyjny", który po cichu wrócił do jazdy, przechodziłby bramkę.
        if (last.get("view") or "").lower() == "inspect":
            steps = last.get("steps")
            if steps != 0:
                problems.append(
                    f"last_shot.steps = {steps} przy widoku inspect — ten widok ma nie "
                    "przejeżdżać do celu, a zero kroków jest jedynym dowodem, że nie przejechał")
            train = last.get("chainage_m")
            if isinstance(train, (int, float)) and abs(train - chainage_m) <= 1.0 \
                    and chainage_m > 100.0:
                problems.append(
                    f"last_shot.chainage_m = {train} zbieżny z żądanym {chainage_m} przy "
                    "widoku inspect — skład stoi w kadrze, czyli albo przejazd się odbył, "
                    "albo temat kadru został przepisany z pozycji pojazdu")

    return problems


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata", required=True)
    parser.add_argument("--axis", required=True, help="oś, z której liczona jest prawda niezależna")
    parser.add_argument("--manifest",
                        help="manifest chunków — pozwala policzyć predykat streamowania "
                             "niezależnie i porównać go z tym, co scena wczytała")
    parser.add_argument("--visual-tail-axis",
                        default=os.path.join(ROOT, "data", "scenery", "L1_A_visual_tail.json"),
                        help="kanoniczna oś osobnej scenerii za Merode")
    parser.add_argument("--visual-tail-assets",
                        help="katalog z parą GLB i osią scenerii z bieżącego pakietu")
    parser.add_argument("--require-visual-tail", action="store_true",
                        help="wymagaj scenerii za Merode w bieżącym pakiecie CI")
    parser.add_argument("--resolution", help="np. 1280x720")
    parser.add_argument("--view", help="widok ostatniego zrzutu")
    parser.add_argument("--at-chainage", type=float, help="chainage ostatniego zrzutu")
    parser.add_argument("--m7-spec", default=os.path.join(ROOT, "data", "vehicle", "m7-spec.json"),
                        help="rejestr M7 — niezależna prawda o składzie i o wysokości peronu")
    parser.add_argument("--platform-layout",
                        help="wyjście tools/track/station_layout.py — zakresy peronów, "
                             "czyli niezależna prawda o tym, gdzie peron ma być")
    parser.add_argument("--platform-metrics",
                        help="wyjście --metrics z tools/blender/station_kit.py — ile brył "
                             "generator naprawdę zbudował")
    args = parser.parse_args()

    with open(args.metadata, encoding="utf-8") as handle:
        metadata = json.load(handle)

    resolution = None
    if args.resolution:
        resolution = [int(part) for part in args.resolution.lower().split("x")]

    expected = axis_length_m(args.axis)
    manifest = load_manifest(args.manifest) if args.manifest else None
    problems = check(metadata, args.axis, resolution, args.view, args.at_chainage, manifest)
    if args.require_visual_tail and not args.visual_tail_assets:
        parser.error("--require-visual-tail wymaga --visual-tail-assets")
    problems += check_visual_continuation(metadata, args.axis, args.visual_tail_axis,
                                          args.visual_tail_assets, args.require_visual_tail)
    problems += check_train(metadata, args.m7_spec)
    # Peron sprawdzany TYLKO wtedy, gdy wołający podał, z czym go porównać. Bez tego
    # bramka nie ma niezależnej prawdy, a „przeszło" znaczyłoby wyłącznie „nie było
    # czego sprawdzić" — dokładnie ta forma weryfikacji, którą CLAUDE.md §5 zakazuje.
    layout = None
    if args.platform_layout or args.platform_metrics:
        if not (args.platform_layout and args.platform_metrics):
            raise SystemExit("BŁĄD: --platform-layout i --platform-metrics idą razem; "
                             "jedno bez drugiego nie daje pełnej prawdy o peronie")
        with open(args.platform_layout, encoding="utf-8") as handle:
            layout = json.load(handle)
        with open(args.platform_metrics, encoding="utf-8") as handle:
            metrics = json.load(handle)
        problems += check_platforms(metadata, layout, metrics, args.m7_spec)
    if problems:
        print(f"BŁĄD: metadane zrzutu nie opisują tej sceny ({args.metadata}):", file=sys.stderr)
        for problem in problems:
            print(f"  {problem}", file=sys.stderr)
        return 1

    scene = metadata["scene"]
    print(f"[METADANE] {scene['chunks_loaded']}/{scene['chunks_declared']} chunków rezydentnych, "
          f"{scene['mesh_objects']} obiektów, {scene['vertices']} wierzchołków, "
          f"oś {scene['axis_length_m']:.3f} m == {expected:.3f} m policzone niezależnie")
    visual = metadata.get("visual_continuation")
    if visual is not None:
        print(f"[SCENERIA] za Merode: obecna={visual['present']}, "
              f"siatek={visual['mesh_objects']}, oś={visual['axis_length_m']:.3f} m")
    train = metadata["train"]
    print(f"[SKŁAD] {train['bodies']} brył, {train['length_m']:.3f} m x {train['width_m']:.3f} m, "
          f"dach {train['roof_height_m']:.3f} m — zgodne z rejestrem M7 (status spec)")
    if layout is not None:
        peron = metadata["platforms"]
        near = peron["near_shot"]
        print(f"[PERON] {peron['slabs']} brył, góra {peron['top_m']:.4f} m nad główką "
              f"szyny; w promieniu {near['radius_m']:.1f} m od kilometrażu zrzutu "
              f"{near['slabs']} brył")
    return 0


if __name__ == "__main__":
    sys.exit(main())
