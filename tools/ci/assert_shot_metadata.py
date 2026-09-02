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
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "blender"))

import profiles  # noqa: E402
import sweep as SW  # noqa: E402

#: Tolerancja porównania długości osi. Ta sama liczba i to samo uzasadnienie,
#: co `FirstRun.AxisManifestToleranceM`: rozdzielczość zapisu, nie zapas.
AXIS_TOLERANCE_M = 1e-3

#: Krok zagęszczania z `TrackAxis.DefaultRingStepM` i `sweep.DEFAULT_RING_STEP_M`.
RING_STEP_M = 5.0


def axis_points(axis_path):
    with open(axis_path, encoding="utf-8") as handle:
        document = json.load(handle)
    return SW.catmull_rom([tuple(float(c) for c in p) for p in document["points"]], RING_STEP_M)


def axis_length_m(axis_path):
    """Długość osi po zagęszczeniu — policzona TU, nie przeczytana z metadanych."""
    return SW.chainages(axis_points(axis_path))[-1]


def axis_scene_bbox(axis_path):
    """Bbox osi w układzie SCENY — kotwica bezwzględna dla bryły tunelu.

    `SceneAxis.ToScene` zamienia punkt danych (X wschód, Y północ, Z w górę) na
    punkt Godota `(X, Z, -Y)`. Zamiana jest tylko przestawieniem osi, bez
    przesuwania układu, więc bbox osi w scenie da się policzyć tutaj — i to jest
    jedyna rzecz, względem której bryła tunelu ma bezwzględne położenie.

    Bez tego przesunięcie CAŁEJ sceny przechodzi: `size_m` zostaje spójne z bboxem,
    bo min i max jadą razem. Zmierzone: bbox przesunięty o 1000 m na każdej osi
    przechodził wszystkie pozostałe kontrole tego pliku.
    """
    points = axis_points(axis_path)
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    zs = [p[2] for p in points]
    return ([min(xs), min(zs), -max(ys)], [max(xs), max(zs), -min(ys)])


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


def check(metadata, axis_path, resolution, view, chainage_m):
    problems = []
    scene = metadata.get("scene") or {}

    if not scene:
        return ["metadane nie mają sekcji `scene` — scena nic nie opisała"]

    declared = scene.get("chunks_declared")
    loaded = scene.get("chunks_loaded")
    if loaded != declared:
        problems.append(
            f"manifest deklaruje {declared} chunków, a scena wczytała {loaded} — "
            "metadane są wewnętrznie sprzeczne")
    if not declared:
        problems.append(f"chunks_declared = {declared}; manifest bez chunków nie jest sceną")

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
        axis_lo, axis_hi = axis_scene_bbox(axis_path)
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
        got = last.get("chainage_m")
        if not isinstance(got, (int, float)) or abs(got - chainage_m) > 1.0:
            problems.append(
                f"last_shot.chainage_m = {got}, żądano {chainage_m} "
                "(literówka w --at-chainage dawała kadr z innego miejsca osi)")

    return problems


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata", required=True)
    parser.add_argument("--axis", required=True, help="oś, z której liczona jest prawda niezależna")
    parser.add_argument("--resolution", help="np. 1280x720")
    parser.add_argument("--view", help="widok ostatniego zrzutu")
    parser.add_argument("--at-chainage", type=float, help="chainage ostatniego zrzutu")
    parser.add_argument("--m7-spec", default=os.path.join(ROOT, "data", "vehicle", "m7-spec.json"),
                        help="rejestr M7 — niezależna prawda o składzie")
    args = parser.parse_args()

    with open(args.metadata, encoding="utf-8") as handle:
        metadata = json.load(handle)

    resolution = None
    if args.resolution:
        resolution = [int(part) for part in args.resolution.lower().split("x")]

    expected = axis_length_m(args.axis)
    problems = check(metadata, args.axis, resolution, args.view, args.at_chainage)
    problems += check_train(metadata, args.m7_spec)
    if problems:
        print(f"BŁĄD: metadane zrzutu nie opisują tej sceny ({args.metadata}):", file=sys.stderr)
        for problem in problems:
            print(f"  {problem}", file=sys.stderr)
        return 1

    scene = metadata["scene"]
    print(f"[METADANE] {scene['chunks_loaded']}/{scene['chunks_declared']} chunków, "
          f"{scene['mesh_objects']} obiektów, {scene['vertices']} wierzchołków, "
          f"oś {scene['axis_length_m']:.3f} m == {expected:.3f} m policzone niezależnie")
    train = metadata["train"]
    print(f"[SKŁAD] {train['bodies']} brył, {train['length_m']:.3f} m x {train['width_m']:.3f} m, "
          f"dach {train['roof_height_m']:.3f} m — zgodne z rejestrem M7 (status spec)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
