"""Deterministyczny render kontrolny wg canonical manifestu kamer (T-012).

Uruchamianie:

    blender --background --python-exit-code 7 --python tools/visual/capture_blender.py -- \
        --in build/M7_shell.glb --set vehicle --prefix M7_shell --out renders

Świadomie korzysta z `tools/blender/render_check.py` (świat, materiał kontrolny,
overlay siatki, odczyt osi trasy), żeby nie mieć dwóch różnych definicji sceny
kontrolnej. Kadrowanie liczy `tools/visual/framing.py` — bez bpy, więc testowalne.
"""
import argparse
import hashlib
import json
import os
import sys

import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "tools", "blender"))

import capture_plan as CPL  # noqa: E402
import framing  # noqa: E402
import placement as PL  # noqa: E402
import render_check as rc  # noqa: E402
import sweep as SW  # noqa: E402


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser(description="Render kontrolny wg manifestu kamer")
    parser.add_argument("--in", dest="inp", required=True, help="wejściowy GLB")
    parser.add_argument("--set", dest="scene_set", required=True, help="zestaw kamer z manifestu")
    parser.add_argument("--prefix", required=True, help="przedrostek nazw plików wyjściowych")
    parser.add_argument("--out", default="renders", help="katalog wyjściowy")
    parser.add_argument("--manifest", default=os.path.join(HERE, "cameras.json"))
    parser.add_argument("--centerline", help="oś trasy — źródło kotwic inside_eye/inside_target")
    parser.add_argument("--axis-fractions", default="0.05,0.25,0.5,0.75",
                        help="ułamki chainage, dla których powstają kotwice axisNN_eye/_target")
    parser.add_argument("--anchor", action="append", default=[],
                        help="jawna kotwica, np. --anchor door=12.5,0,1.8")
    parser.add_argument("--commit", default=os.environ.get("GITHUB_SHA", "local"))
    parser.add_argument("--wire-cameras", default="inside,section",
                        help="kamery z overlayem siatki (kontrola normalnych)")
    parser.add_argument("--test-shift", help="TYLKO test pipeline'u: przesuń geometrię o X,Y,Z metrów")
    return parser.parse_args(argv)


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


# `idat_sha256` jest WOŁANE z tools/ci, a nie przepisane tutaj. Kopia dawałaby dwie
# implementacje jednej wyroczni i jedną z nich niesprawdzoną przez testy tamtej.
_CI_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ci")
if _CI_DIR not in sys.path:
    sys.path.insert(0, _CI_DIR)
import png_pixels_sha256 as PNGSUM  # noqa: E402


def idat_sha256(path):
    """Suma SHA-256 SAMYCH pikseli — chunków `IDAT`, bez metadanych PNG.

    **Po co obok sumy całego pliku, a nie zamiast niej.** Obie liczby mówią co innego
    i obie są potrzebne. Suma pliku identyfikuje **plik** — po niej poznaje się, że to
    dokładnie ten artefakt, który wyszedł z tamtego przebiegu. Suma `IDAT` identyfikuje
    **obraz** — i tylko ona nadaje się na wyrocznię determinizmu renderu.

    **Zmierzone 06.09.2026** na dwóch przebiegach tej samej scenyodpowiednio (ten sam GLB,
    te same kamery, ten sam Blender 5.2.1): z 18 chunków PNG różnią się **dwa**, oba
    `tEXt` — `Date` (`2026/09/06 09:52:07` wobec `09:52:50`) i `RenderTime` (`00:29.17`
    wobec `00:14.73`). Wszystkie trzy chunki `IDAT` są identyczne co do bajtu. Suma
    całego pliku różni się więc na każdej z trzech klatek, a suma `IDAT` na żadnej —
    i to jest cała przyczyna, dla której ta druga tu jest.
    """
    return PNGSUM.idat_sha256(path)


# Progi i decyzje wokół renderu siedzą w `capture_plan.py`, bo tamten moduł da się
# zaimportować bez Blendera, a ten nie. Nazwy zostają dostępne pod starym adresem,
# bo `EEVEE_NEXT_SINCE` jest cytowane w komunikacie odmowy i w docstringach.
EEVEE_NEXT_SINCE = CPL.EEVEE_NEXT_SINCE


def eevee_generation():
    """'next' albo 'legacy' — który EEVEE naprawdę stoi za nazwą `BLENDER_EEVEE`."""
    return CPL.eevee_generation(bpy.app.version)


def apply_render_settings(scene, render_cfg, resolution):
    # Bramka na renderer, nie na napis. ZMIERZONE 02.09.2026: `enum_items` dla
    # `engine` zwraca DOKŁADNIE `['BLENDER_EEVEE']` i na 4.0.2, i na 5.0.1 — a to
    # dwa różne silniki. Bez tej bramki CI liczyło ujęcia legacy EEVEE, uznawało je
    # za baseline i nikt by się nie dowiedział, że renderer się zmienił: w logu stał
    # ten sam `engine=BLENDER_EEVEE`. Kosztowało to dwie czerwone bramki
    # (`tunnel-alignment` L1_B i L2_E) przy przejściu CI na maszynę właściciela.
    conflict = CPL.eevee_conflict(render_cfg.get("eevee_generation"),
                                  eevee_generation(), bpy.app.version_string)
    if conflict:
        raise SystemExit(conflict)

    engine = render_cfg.get("engine", "BLENDER_EEVEE_NEXT")
    try:
        scene.render.engine = engine
    except Exception:
        engine = render_cfg.get("engine_fallback", "BLENDER_EEVEE")
        scene.render.engine = engine
    scene.render.resolution_x, scene.render.resolution_y = resolution
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = bool(render_cfg.get("film_transparent", False))
    scene.render.dither_intensity = 0.0
    scene.render.use_motion_blur = bool(render_cfg.get("use_motion_blur", False))
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = render_cfg.get("color_mode", "RGB")
    scene.render.image_settings.color_depth = "8"
    scene.render.image_settings.compression = 15
    try:
        scene.view_settings.view_transform = render_cfg.get("view_transform", "Standard")
        scene.view_settings.look = render_cfg.get("look", "None")
    except Exception as exc:
        print(f"[WARN] color management nieustawione: {exc}")
    samples = int(render_cfg.get("samples", 32))
    if hasattr(scene, "eevee"):
        for attr in ("taa_render_samples", "taa_samples"):
            if hasattr(scene.eevee, attr):
                setattr(scene.eevee, attr, samples)
    if hasattr(scene, "cycles"):
        scene.cycles.samples = samples
        scene.cycles.seed = 0
        scene.cycles.use_denoising = False
    print(f"[RENDER] engine={engine} eevee={eevee_generation()} blender={bpy.app.version_string} "
          f"samples={samples} res={resolution[0]}x{resolution[1]} dither=0.0")
    return engine


def build_camera(solved, name):
    data = bpy.data.cameras.new(name)
    data.clip_start = solved["clip_start"]
    data.clip_end = solved["clip_end"]
    if CPL.is_orthographic(solved):
        data.type = "ORTHO"
        data.ortho_scale = solved["ortho_scale"]
    else:
        data.type = "PERSP"
        data.lens = solved["lens"]
        data.sensor_fit = "AUTO"
        data.sensor_width = framing.SENSOR_MM
    cam = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(cam)
    cam.location = Vector(solved["location"])
    right = Vector(solved["right"])
    up = Vector(solved["up"])
    back = -Vector(solved["direction"])
    cam.rotation_mode = "QUATERNION"
    cam.rotation_quaternion = Matrix((right, up, back)).transposed().to_quaternion()
    return cam


def build_headlight(cam_solved, cfg):
    """Punktowe światło W MIEJSCU kamery. Zwraca obiekt albo None.

    **Po co.** Tunel jest zamkniętą rurą pokrytą jednym materiałem emisyjnym o stałej
    jasności, a słońce ze `setup_world` do wnętrza nie dociera. Kamera perspektywiczna
    patrząca wzdłuż osi trafia więc w każdym kierunku w powierzchnię o TEJ SAMEJ
    jasności i klatka wychodzi płaska — nie z powodu awarii, tylko z konstrukcji.
    Komentarz przy kamerze `flank` mówi to samo o zamkniętej rurze; tam rozwiązano to
    cięciem płaszczyzną, a `approach` nie dostała ani cięcia, ani światła.

    ZMIERZONE na L1_B: bez światła `approach` daje ink=0.0104 na legacy EEVEE
    (próg 0.0002, ale `min_distinct_levels` 16 wobec zmierzonych 56) i ink=0.0002
    przy 13 poziomach na EEVEE Next — czyli klatkę odrzuca bramka pustki. Ujęcie
    przechodziło latami resztką refleksów przy kącie muskającym, a nie treścią.

    Spadek jasności z odległością daje głębię: bliższy przekrój tunelu jest jaśniejszy
    od dalszego, więc widać rurę, sylwetkę składu i szczelinę.
    """
    if not cfg:
        return None
    data = bpy.data.lights.new(f"headlight_{cam_solved['id']}", type="POINT")
    data.energy = float(cfg["energy_w"])
    data.shadow_soft_size = float(cfg.get("radius_m", 0.1))
    # Zasięg obcina wpływ światła, żeby ujęcie nie rozjaśniało całej sceny 9 km osi.
    if hasattr(data, "use_custom_distance"):
        data.use_custom_distance = True
        data.cutoff_distance = float(cfg["range_m"])
    light = bpy.data.objects.new(f"headlight_{cam_solved['id']}", data)
    bpy.context.collection.objects.link(light)
    light.location = Vector(cam_solved["location"])
    return light


def named_anchors_from_args(args, vertices, scene_size, fractions="0.05,0.25,0.5,0.75"):
    try:
        anchors = CPL.parse_anchors(args.anchor)
    except ValueError as err:
        raise SystemExit(f"BŁĄD: {err}")
    if args.centerline:
        raw = rc.load_centerline(args.centerline)
        axis = [(p.x, p.y, p.z) for p in raw]
        frames = SW.rmf_frames(axis)
        stations = SW.chainages(axis)
        # Ułamki liczone są w zakresie, który POKRYWA wczytana geometria, nie w całej osi.
        # Dla pełnej osi to jedno i to samo; dla chunka 2923..3433 m ułamek 0,05 wskazywałby
        # 86 m, czyli 2,8 km przed jego początkiem, i kamera trafiałaby w pustkę.
        low, high = PL.covered_chainage_range([(v.x, v.y, v.z) for v in vertices],
                                              frames, stations)
        span = high - low
        print(f"[POKRYCIE] geometria zajmuje chainage {low:.1f}..{high:.1f} m "
              f"z osi {stations[0]:.1f}..{stations[-1]:.1f} m")

        def anchor_pair(fraction, ahead_m):
            eye = _point_at_chainage(axis, stations, PL.fraction_to_chainage(fraction, low, high))
            look = _point_at_chainage(axis, stations,
                                      PL.fraction_to_chainage(fraction, low, high) + ahead_m)
            eye.z = look.z = rc.vertical_mid_on_axis(vertices, eye, look - eye, scene_size)
            return eye, look

        eye, target = anchor_pair(0.05, max(5.0, span * 0.005))
        anchors.setdefault("inside_eye", [eye.x, eye.y, eye.z])
        anchors.setdefault("inside_target", [target.x, target.y, target.z])
        cut, ahead = anchor_pair(0.5, max(5.0, span * 0.005))
        anchors.setdefault("section_eye", [cut.x, cut.y, cut.z])
        anchors.setdefault("section_target", [ahead.x, ahead.y, ahead.z])
        # Zbiór kotwic wzdłuż osi: pojedynczy render całego, 6,7-kilometrowego tunelu
        # daje kreskę grubości 2 px i nie odpowiada na pytanie „czy gdzieś znika przekrój".
        # Zbliżenia w kilku chainage'ach odpowiadają.
        for fraction in [float(v) for v in fractions.split(",") if v.strip()]:
            eye, look = anchor_pair(fraction, max(5.0, span * 0.005))
            tag = f"axis{int(round(fraction * 100)):02d}"
            anchors.setdefault(f"{tag}_eye", [eye.x, eye.y, eye.z])
            anchors.setdefault(f"{tag}_target", [look.x, look.y, look.z])
    return anchors


def _point_at_chainage(axis, stations, chainage):
    """Punkt na osi w zadanym chainage, jako Vector.

    Samo szukanie jest w `capture_plan.point_at_chainage` i zwraca krotkę; tutaj
    zostaje wyłącznie owinięcie w `Vector`, bo `mathutils` istnieje tylko w Blenderze.
    """
    return Vector(CPL.point_at_chainage(axis, stations, chainage))


def main():
    args = parse_args()
    with open(args.manifest, encoding="utf-8") as handle:
        manifest = json.load(handle)
    if args.scene_set not in manifest["scene_sets"]:
        raise SystemExit(f"BŁĄD: zestaw {args.scene_set} nie istnieje w manifeście")
    scene_set = manifest["scene_sets"][args.scene_set]
    # Zestaw `godot` opisuje ujęcia z SILNIKA: kamery są w scenie Godota, a tutaj są
    # tylko identyfikatory i progi dla `compare.py`. Bez tej odmowy Blender wygenerowałby
    # z niego klatki z domyślną kamerą i nikt by nie zauważył, że to nie są te ujęcia.
    conflict = CPL.renderer_conflict(args.scene_set, scene_set.get("renderer", "blender"))
    if conflict:
        raise SystemExit(conflict)
    if not os.path.isfile(args.inp):
        raise SystemExit(f"BŁĄD: brak pliku wejściowego {args.inp}")

    rc.clear_scene()
    bpy.ops.import_scene.gltf(filepath=args.inp)
    rc.setup_world()
    rc.setup_verification_material()
    scene = bpy.context.scene
    engine = apply_render_settings(scene, manifest["render"], scene_set["resolution"])

    vertices = rc.mesh_world_vertices()
    mins, maxs = rc.scene_bounds(vertices)
    bmin = (mins.x, mins.y, mins.z)
    bmax = (maxs.x, maxs.y, maxs.z)
    scene_size = max(maxs.x - mins.x, maxs.y - mins.y, maxs.z - mins.z, 1.0)
    points = [(v.x, v.y, v.z) for v in vertices]
    anchors = named_anchors_from_args(args, vertices, scene_size, args.axis_fractions)
    solved, skipped = framing.solve_set(manifest, args.scene_set, bmin, bmax, anchors, points)
    for entry in skipped:
        print(f"[SKIP] kamera {entry['id']}: {entry['reason']}")

    shifted_bbox = None
    if args.test_shift:
        # Kamery są już policzone. Przesunięcie PO kadrowaniu symuluje realną regresję
        # geometrii przy niezmienionym baseline; przesunięcie przed kadrowaniem byłoby
        # niewidoczne, bo kamera kadruje się względem bboxa i pojechałaby razem z modelem.
        offset = Vector([float(v) for v in args.test_shift.split(",")])
        for obj in rc.mesh_objects():
            obj.location = obj.location + offset
        bpy.context.view_layer.update()
        shifted = rc.mesh_world_vertices()
        smins, smaxs = rc.scene_bounds(shifted)
        shifted_bbox = [[round(c, 6) for c in (smins.x, smins.y, smins.z)],
                        [round(c, 6) for c in (smaxs.x, smaxs.y, smaxs.z)]]
        print(f"[TEST-SHIFT] geometria przesunięta o {tuple(offset)} po ustaleniu kamer — test pipeline'u")

    wire_ids = {c.strip() for c in args.wire_cameras.split(",") if c.strip()}
    # Manifest też może zażądać siatki. To wiedza o kamerze, nie o wywołaniu: bez siatki
    # scena złożona z pojazdu i tunelu jest jednolicie szara i nie da się odróżnić, gdzie
    # kończy się pudło, a zaczyna ściana. Flaga CLI tylko dodaje kamery do tego zbioru.
    wire_ids |= {c["id"] for c in scene_set["cameras"] if c.get("wire")}
    if wire_ids & {c["id"] for c in solved}:
        rc.add_inside_wire_overlay()
        wire_objects = [o for o in rc.mesh_objects() if o.name.endswith("_verification_wire")]
    else:
        wire_objects = []

    os.makedirs(args.out, exist_ok=True)
    meshes = [o for o in rc.mesh_objects() if not o.name.endswith("_verification_wire")]
    records = []
    for cam_solved in solved:
        camera_id = cam_solved["id"]
        for obj in wire_objects:
            obj.hide_render = camera_id not in wire_ids
        cam = build_camera(cam_solved, f"cam_{camera_id}")
        headlight_cfg = cam_solved.get("headlight")
        headlight = build_headlight(cam_solved, headlight_cfg)
        if headlight is not None:
            print(f"[ZAŁOŻENIE] {camera_id}: reflektor przy kamerze "
                  f"{headlight_cfg['energy_w']:.1f} W, zasięg {headlight_cfg['range_m']:.0f} m "
                  "— parametr obrazu, nie dana o taborze")
        path = os.path.join(args.out, f"{args.prefix}_{camera_id}.png")
        scene.camera = cam
        scene.render.filepath = path
        bpy.ops.render.render(write_still=True)
        if headlight is not None:
            # Zdejmowane od razu: światło jednego ujęcia nie ma rozjaśniać następnych.
            bpy.data.objects.remove(headlight, do_unlink=True)
        record = dict(cam_solved)
        record["file"] = path
        record["bytes"] = os.path.getsize(path)
        record["sha256"] = sha256(path)
        record["idat_sha256"] = idat_sha256(path)
        record["wire_overlay"] = camera_id in wire_ids
        record["corner_visibility"] = round(framing.corner_visibility(cam_solved, bmin, bmax), 4)
        records.append(record)
        print(f"[RENDER] {path} bytes={record['bytes']} corner_visibility={record['corner_visibility']}")

    metadata = {
        "tool": "tools/visual/capture_blender.py",
        "manifest_version": manifest.get("manifest_version"),
        "scene_set": args.scene_set,
        "prefix": args.prefix,
        "commit": args.commit,
        "blender_version": bpy.app.version_string,
        "engine": engine,
        "resolution": scene_set["resolution"],
        "source_glb": {"path": args.inp, "sha256": sha256(args.inp), "bytes": os.path.getsize(args.inp)},
        "scene": {
            "bbox_min": [round(c, 6) for c in bmin],
            "bbox_max": [round(c, 6) for c in bmax],
            "size_m": [round(bmax[i] - bmin[i], 6) for i in range(3)],
            "mesh_objects": len(meshes),
            "vertices": sum(len(o.data.vertices) for o in meshes),
            "faces": sum(len(o.data.polygons) for o in meshes),
        },
        "anchors": anchors,
        "test_shift": args.test_shift,
        "test_shift_bbox": shifted_bbox,
        "cameras": records,
        "skipped": skipped,
    }
    meta_path = os.path.join(args.out, f"{args.prefix}_metadata.json")
    with open(meta_path, "w", encoding="utf-8") as handle:
        json.dump(metadata, handle, ensure_ascii=False, indent=2)
    print(f"[METADATA] {meta_path}")
    print(f"[RAPORT] kamery={len(records)} pominięte={len(skipped)} "
          f"bbox={metadata['scene']['size_m']} wierzchołki={metadata['scene']['vertices']}")
    if not records:
        raise SystemExit("BŁĄD: żadna kamera nie została wyrenderowana")


if __name__ == "__main__":
    main()
