#!/usr/bin/env python3
"""Testy pipeline'u kontroli wizualnej (T-012). Bez Blendera i bez pytest.

Dowodzą tego, czego wymaga #27: identyczny render przechodzi, czarny obraz i zły
rozmiar są odrzucane, przesunięty obiekt przekracza próg, drobny szum nie, a brak
baseline nigdy nie prowadzi do automatycznego nadpisania.
"""
import json
import os
import shutil
import struct
import sys
import tempfile
import zlib

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "visual"))

import compare  # noqa: E402
import framing  # noqa: E402
import pngio  # noqa: E402

MANIFEST = compare.load_manifest(os.path.join(ROOT, "tools", "visual", "cameras.json"))
W, H = 160, 96
M7_BMIN = (0.0, -1.35, 0.0)
M7_BMAX = (94.0, 1.35, 3.6)


def _scene(shift=0, noise=0.0, blank=False):
    """Syntetyczny 'render': tło + jasny prostokąt, opcjonalnie przesunięty."""
    pixels = []
    for y in range(H):
        for x in range(W):
            if blank:
                pixels.append((0.0, 0.0, 0.0))
                continue
            inside = (30 + shift) <= x < (70 + shift) and 30 <= y < 66
            # delikatny gradient tła: prawdziwy render nigdy nie ma dwóch poziomów
            value = (0.85 if inside else 0.30) + 0.12 * y / H
            if noise:
                value += noise * (((x * 7 + y * 13) % 5) - 2) / 2.0
            pixels.append((value, value, value))
    return pixels


def _write(path, pixels, width=W, height=H):
    pngio.write_rgb(path, width, height, pixels)


def _thresholds():
    return MANIFEST["scene_sets"]["vehicle"]["thresholds"]


def _small_manifest():
    """Kopia manifestu w rozdzielczości obrazów testowych — reszta bez zmian."""
    manifest = json.loads(json.dumps(MANIFEST))
    manifest["scene_sets"]["vehicle"]["resolution"] = [W, H]
    return manifest


def _check(current_pixels, baseline_pixels, size=(W, H), base_size=None, diff_dir=None):
    tmp = tempfile.mkdtemp()
    try:
        cur = os.path.join(tmp, "a.png")
        _write(cur, current_pixels, size[0], size[1])
        base = None
        if baseline_pixels is not None:
            base = os.path.join(tmp, "b.png")
            bw, bh = base_size or size
            _write(base, baseline_pixels, bw, bh)
        diff_path = os.path.join(diff_dir, "x_diff.png") if diff_dir else None
        return compare.check_image(cur, list(size), _thresholds(), base, diff_path)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# --- manifest kamer -----------------------------------------------------------

def test_visual_manifest_covers_required_vehicle_cameras():
    ids = {c["id"] for c in MANIFEST["scene_sets"]["vehicle"]["cameras"]}
    assert {"side", "front", "iso", "roof", "door"} <= ids, ids


def test_visual_manifest_covers_required_infrastructure_cameras():
    ids = {c["id"] for c in MANIFEST["scene_sets"]["infrastructure"]["cameras"]}
    assert {"iso", "side", "top", "inside", "section"} <= ids, ids


def test_visual_manifest_render_settings_are_deterministic():
    render = MANIFEST["render"]
    assert render["samples"] >= 1 and render["use_motion_blur"] is False
    assert render["view_transform"] == "Standard"
    for scene_set in MANIFEST["scene_sets"].values():
        assert len(scene_set["resolution"]) == 2 and all(v > 0 for v in scene_set["resolution"])
        assert set(scene_set["thresholds"]) == {"mean_abs_diff", "p95_abs_diff", "ssim_min",
                                                "min_ink_fraction", "min_luma_std",
                                                "min_distinct_levels"}


# --- kadrowanie ---------------------------------------------------------------

def test_visual_framing_is_deterministic():
    anchors = {"door": [12.0, 0.0, 1.8]}
    first, _ = framing.solve_set(MANIFEST, "vehicle", M7_BMIN, M7_BMAX, anchors)
    second, _ = framing.solve_set(MANIFEST, "vehicle", M7_BMIN, M7_BMAX, anchors)
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


def test_visual_framing_covers_whole_bbox():
    solved, skipped = framing.solve_set(MANIFEST, "vehicle", M7_BMIN, M7_BMAX, {"door": [12.0, 0.0, 1.8]})
    assert not skipped
    for cam in solved:
        if cam["id"] == "door":
            continue  # zbliżenie ma z definicji nie łapać całej bryły
        assert framing.corner_visibility(cam, M7_BMIN, M7_BMAX) == 1.0, cam["id"]


def test_visual_side_camera_frame_matches_vehicle_length():
    solved, _ = framing.solve_set(MANIFEST, "vehicle", M7_BMIN, M7_BMAX, {"door": [12.0, 0.0, 1.8]})
    side = next(c for c in solved if c["id"] == "side")
    assert side["projection"] == "ORTHO"
    length = M7_BMAX[0] - M7_BMIN[0]
    assert length <= side["frame_w_m"] <= length * 1.2, side["frame_w_m"]


def test_visual_door_camera_uses_declared_frame_width():
    spec = next(c for c in MANIFEST["scene_sets"]["vehicle"]["cameras"] if c["id"] == "door")
    solved = framing.solve_camera(spec, M7_BMIN, M7_BMAX, 1280, 720, {"door": [12.0, 0.0, 1.8]})
    half_width = solved["distance_m"] * __import__("math").tan(__import__("math").radians(solved["fov_x_deg"]) / 2)
    assert abs(2 * half_width - spec["frame_width_m"]) < 1e-6


def test_visual_missing_anchor_skips_camera_explicitly():
    solved, skipped = framing.solve_set(MANIFEST, "vehicle", M7_BMIN, M7_BMAX, {})
    assert [s["id"] for s in skipped] == ["door"]
    assert "door" not in {c["id"] for c in solved}


def test_visual_section_camera_ignores_the_far_side_of_a_returning_route():
    """Regresja: oś pakietu E to pierścień i płaszczyzna cięcia trafia w niego dwa razy.

    Bez ograniczenia promienia ortho rośnie z 16,5 m do 4777,7 m — kadr formalnie
    „znalazł geometrię", a pokazuje pustkę, bo przekrój pod kotwicą ma wtedy kilka
    pikseli.
    """
    spec = {"id": "section", "projection": "ORTHO", "fit": "slab",
            "slab_thickness_m": 12.0, "slab_radius_m": 40.0,
            "direction": [1.0, 0.0, 0.0], "margin": 1.0,
            "anchor": {"mode": "named", "name": "cut"}}
    anchors = {"cut": [0.0, 0.0, 1.75]}
    here = [(0.0, -4.7, -1.2), (0.0, 4.7, -1.2), (0.0, 4.7, 4.7), (0.0, -4.7, 4.7)]
    far_side = [(0.0, 2400.0, -1.2), (0.0, 2409.4, 4.7)]
    solved = framing.solve_camera(spec, (-500.0, -10.0, -1.2), (500.0, 2410.0, 4.7),
                                  960, 576, named_anchors=anchors, points=here + far_side)
    assert solved["fit_fallback"] is False
    assert solved["ortho_scale"] < 30.0, solved
    without = dict(spec)
    without.pop("slab_radius_m")
    loose = framing.solve_camera(without, (-500.0, -10.0, -1.2), (500.0, 2410.0, 4.7),
                                 960, 576, named_anchors=anchors, points=here + far_side)
    assert loose["ortho_scale"] > 1000.0, "przypadek brzegowy przestał być brzegowy"


def test_visual_section_camera_grows_the_slab_until_it_finds_a_ring():
    """Regresja: na LOD 2 pierścienie stoją co kilkadziesiąt metrów.

    Płat +-12 m wokół kotwicy bywa wtedy pusty, kadr cicho spada na bbox całego
    chunka i przekrój 9,4 x 5,9 m ląduje jako plamka na 570-metrowej klatce.
    Zmierzone na chunku pakietu E: LOD 0 przechodzi, LOD 2 daje ink=0.0000.
    """
    spec = {"id": "section", "projection": "ORTHO", "fit": "slab",
            "slab_thickness_m": 12.0, "direction": [1.0, 0.0, 0.0], "margin": 1.0,
            "anchor": {"mode": "named", "name": "cut"}}
    # jedyny pierścień leży 40 m przed kotwicą — dokładnie tak, jak na LOD 2
    ring = [(40.0, -4.7, -1.2), (40.0, 4.7, -1.2), (40.0, 4.7, 4.7), (40.0, -4.7, 4.7)]
    solved = framing.solve_camera(spec, (0.0, -4.7, -1.2), (570.0, 4.7, 4.7), 960, 576,
                                  named_anchors={"cut": [0.0, 0.0, 1.75]}, points=ring)
    assert solved["fit_fallback"] is False, solved
    assert solved["slab_thickness_used_m"] >= 40.0, solved
    # kadr ma obejmować przekrój, a nie 570 m chunka
    assert solved["ortho_scale"] < 30.0, solved


def test_visual_section_camera_reports_fallback_when_there_is_no_geometry():
    """Sześć podwojeń to 768 m. Jeśli i to nie łapie nic, kadr JEST zastępczy."""
    spec = {"id": "section", "projection": "ORTHO", "fit": "slab",
            "slab_thickness_m": 12.0, "direction": [1.0, 0.0, 0.0], "margin": 1.0,
            "anchor": {"mode": "named", "name": "cut"}}
    solved = framing.solve_camera(spec, (0.0, -4.7, -1.2), (570.0, 4.7, 4.7), 960, 576,
                                  named_anchors={"cut": [0.0, 0.0, 1.75]},
                                  points=[(5000.0, 0.0, 0.0)])
    assert solved["fit_fallback"] is True, solved


def test_visual_section_camera_uses_slab_not_whole_bbox():
    spec = next(c for c in MANIFEST["scene_sets"]["infrastructure"]["cameras"] if c["id"] == "section")
    bmin, bmax = (0.0, -120.0, -15.0), (2000.0, 0.0, -9.0)
    points = [(1000.0, -60.0, -15.0), (1000.0, -55.0, -9.0), (0.0, -120.0, -15.0), (2000.0, 0.0, -9.0)]
    anchors = {"section_eye": [1000.0, -57.5, -12.0], "section_target": [1010.0, -57.4, -12.0]}
    solved = framing.solve_camera(spec, bmin, bmax, 960, 576, anchors, points)
    assert solved["fit"] == "slab" and solved["fit_fallback"] is False
    assert solved["frame_w_m"] < 20.0, solved["frame_w_m"]
    assert solved["clip_start"] == solved["distance_m"]


# --- PNG i metryki ------------------------------------------------------------

def test_visual_png_roundtrip_keeps_values():
    tmp = tempfile.mkdtemp()
    try:
        path = os.path.join(tmp, "r.png")
        _write(path, _scene())
        img = pngio.read_gray(path)
        assert img.size == (W, H)
        assert abs(img.at(50, 50) - (0.85 + 0.12 * 50 / H)) < 0.01
        assert abs(img.at(5, 5) - (0.30 + 0.12 * 5 / H)) < 0.01
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_visual_identical_render_passes():
    result = _check(_scene(), _scene())
    assert result["status"] == "pass", result
    assert result["metrics"]["mean_abs_diff"] == 0.0 and result["metrics"]["ssim"] > 0.999


def test_visual_black_image_fails():
    result = _check(_scene(blank=True), _scene())
    assert result["status"] == "fail" and result["checks"]["not_empty"] is False


def test_visual_changed_resolution_fails():
    result = _check(_scene(), _scene(), size=(W, H), base_size=(W, H))
    assert result["status"] == "pass"
    tmp = tempfile.mkdtemp()
    try:
        path = os.path.join(tmp, "small.png")
        pngio.write_rgb(path, 80, 48, [(0.3, 0.3, 0.3)] * (80 * 48))
        result = compare.check_image(path, [W, H], _thresholds())
        assert result["status"] == "fail" and result["checks"]["dimension"] is False
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_visual_shifted_object_exceeds_threshold():
    result = _check(_scene(shift=6), _scene())
    assert result["status"] == "fail", result
    assert result["metrics"]["mean_abs_diff"] > _thresholds()["mean_abs_diff"]
    assert result["metrics"]["ssim"] < _thresholds()["ssim_min"]


def _only(criterion):
    """Progi, w których działa DOKŁADNIE jedno kryterium regresji; reszta wyłączona."""
    disabled = {"mean_abs_diff": 2.0, "p95_abs_diff": 2.0, "ssim_min": -1.0}
    thresholds = dict(_thresholds())
    thresholds.update(disabled)
    thresholds[criterion] = _thresholds()[criterion]
    return thresholds


def _check_with(thresholds, current_pixels, baseline_pixels):
    tmp = tempfile.mkdtemp()
    try:
        cur = os.path.join(tmp, "a.png")
        base = os.path.join(tmp, "b.png")
        _write(cur, current_pixels)
        _write(base, baseline_pixels)
        return compare.check_image(cur, [W, H], thresholds, base, None)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_visual_each_regression_criterion_can_fail_on_its_own():
    """Każde z trzech kryteriów regresji musi umieć wywrócić render SAMO.

    Zmierzone 02.09.2026 audytem mutacyjnym: usunięcie z alternatywy dowolnego
    JEDNEGO z trzech członów (`mean_abs_diff`, `p95_abs_diff`, `ssim`) przechodziło
    przez całą suitę, bo jedna klatka testowa przekraczała wszystkie trzy progi
    naraz. Kryteria były w testach wzajemnie redundantne — a p95 jest właśnie po to,
    żeby łapać regresję **lokalną**, którą MAE i SSIM rozmydlają.

    Klatki dobrane tak, żeby każda przekraczała inne kryterium, nie wystarczą:
    ta implementacja SSIM reaguje na wszystko, co porusza p95. Izolacja idzie więc
    przez progi — dla każdego kryterium pozostałe dwa są wyłączone.
    """
    baseline = _scene()

    band = list(baseline)
    for y in range(6):                       # 6,25 % obrazu, czyli ponad 5 % dla p95
        for x in range(W):
            index = y * W + x
            value = band[index][0] + 0.062   # ponad próg p95 (0,06), poniżej progu MAE
            band[index] = (value, value, value)

    by_p95 = _check_with(_only("p95_abs_diff"), band, baseline)
    assert by_p95["status"] == "fail", by_p95
    assert by_p95["metrics"]["p95_abs_diff"] > _thresholds()["p95_abs_diff"]
    assert by_p95["metrics"]["mean_abs_diff"] <= _thresholds()["mean_abs_diff"], \
        "ta klatka ma przekraczać WYŁĄCZNIE p95 — inaczej nie izoluje kryterium"

    by_mae = _check_with(_only("mean_abs_diff"), _scene(shift=6), baseline)
    assert by_mae["status"] == "fail", by_mae
    assert by_mae["metrics"]["mean_abs_diff"] > _thresholds()["mean_abs_diff"]

    by_ssim = _check_with(_only("ssim_min"), _scene(shift=6), baseline)
    assert by_ssim["status"] == "fail", by_ssim
    assert by_ssim["metrics"]["ssim"] < _thresholds()["ssim_min"]

    # Kontrola w drugą stronę: przy wszystkich trzech kryteriach wyłączonych ta sama
    # klatka przechodzi, więc powyższe „fail" biorą się z kryteriów, a nie z czegoś obok.
    nothing = dict(_thresholds())
    nothing.update({"mean_abs_diff": 2.0, "p95_abs_diff": 2.0, "ssim_min": -1.0})
    assert _check_with(nothing, _scene(shift=6), baseline)["status"] == "pass"


def test_visual_regression_thresholds_are_pinned():
    """Same wartości progów, nie tylko to, że są używane.

    Test wyżej bierze progi z manifestu, więc podniesienie `p95_abs_diff` z 0,06
    do 0,99 podniosłoby razem z nim poprzeczkę i mutacja by przeszła.
    """
    for name, expected in (("vehicle", {"mean_abs_diff": 0.004, "p95_abs_diff": 0.06, "ssim_min": 0.98}),
                           ("tunnel", None), ("godot", None)):
        scene_set = MANIFEST["scene_sets"].get(name)
        if scene_set is None or expected is None:
            continue
        for key, value in expected.items():
            assert scene_set["thresholds"][key] == value, (name, key, scene_set["thresholds"][key])


def test_visual_small_noise_stays_below_threshold():
    result = _check(_scene(noise=0.002), _scene())
    assert result["status"] == "pass", result
    assert 0.0 < result["metrics"]["mean_abs_diff"] <= _thresholds()["mean_abs_diff"]


def test_visual_regression_writes_before_current_diff():
    tmp = tempfile.mkdtemp()
    try:
        result = _check(_scene(shift=6), _scene(), diff_dir=tmp)
        assert result["status"] == "fail"
        for key in ("diff", "current", "before"):
            assert os.path.getsize(result["artifacts"][key]) > 0, key
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# --- polityka baseline --------------------------------------------------------

def test_visual_missing_baseline_is_new_baseline_not_pass():
    result = _check(_scene(), None)
    assert result["status"] == "new-baseline"


def test_visual_baseline_is_never_written_automatically():
    tmp = tempfile.mkdtemp()
    try:
        current = os.path.join(tmp, "cur")
        baseline = os.path.join(tmp, "base")
        os.makedirs(current)
        os.makedirs(baseline)
        _write(os.path.join(current, "t_side.png"), _scene())
        report = compare.run(_small_manifest(), "vehicle", current, "t", baseline, None, ["side"])
        assert report["images"][0]["status"] == "new-baseline"
        assert os.listdir(baseline) == [], "baseline nie może powstać bez jawnego zatwierdzenia"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_visual_report_marks_new_baseline_as_not_pass():
    tmp = tempfile.mkdtemp()
    try:
        current = os.path.join(tmp, "cur")
        os.makedirs(current)
        _write(os.path.join(current, "t_side.png"), _scene())
        report = compare.run(_small_manifest(), "vehicle", current, "t", None, None, ["side"])
        statuses = {e["status"] for e in report["images"]}
        assert statuses == {"new-baseline"}
        markdown = compare.to_markdown(dict(report, status="fail", summary={"total": 1}))
        assert "new-baseline" in markdown and "CLAUDE.md" in markdown
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# --- kontrola wymiarowa z metadanych ------------------------------------------

def _meta(bbox_min=(0.0, -1.35, 0.0), bbox_max=(94.0, 1.35, 3.6), vertices=100, faces=50):
    return {
        "manifest_version": MANIFEST["manifest_version"],
        "blender_version": "4.0.2",
        "resolution": [W, H],
        "scene": {
            "bbox_min": list(bbox_min),
            "bbox_max": list(bbox_max),
            "size_m": [round(bbox_max[i] - bbox_min[i], 6) for i in range(3)],
            "mesh_objects": 6,
            "vertices": vertices,
            "faces": faces,
        },
    }


def _meta_file(directory, name, payload):
    path = os.path.join(directory, name)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle)
    return path


def test_visual_geometry_check_passes_for_identical_metadata():
    tmp = tempfile.mkdtemp()
    try:
        cur = _meta_file(tmp, "cur.json", _meta())
        base = _meta_file(tmp, "base.json", _meta())
        result = compare.check_geometry(cur, base)
        assert result["status"] == "pass", result
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_visual_geometry_check_catches_translation_invisible_to_camera():
    tmp = tempfile.mkdtemp()
    try:
        cur = _meta_file(tmp, "cur.json", _meta(bbox_min=(0.0, -1.35, 1.5), bbox_max=(94.0, 1.35, 5.1)))
        base = _meta_file(tmp, "base.json", _meta())
        result = compare.check_geometry(cur, base)
        assert result["status"] == "fail"
        assert result["checks"]["bbox_min"] is False and result["checks"]["size_m"] is True
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_visual_geometry_check_uses_millimetre_tolerance():
    tmp = tempfile.mkdtemp()
    try:
        base = _meta_file(tmp, "base.json", _meta())
        near = _meta_file(tmp, "near.json", _meta(bbox_max=(94.0005, 1.35, 3.6)))
        far = _meta_file(tmp, "far.json", _meta(bbox_max=(94.002, 1.35, 3.6)))
        assert compare.check_geometry(near, base)["status"] == "pass"
        assert compare.check_geometry(far, base)["status"] == "fail"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_visual_geometry_check_reports_missing_baseline():
    tmp = tempfile.mkdtemp()
    try:
        cur = _meta_file(tmp, "cur.json", _meta())
        assert compare.check_geometry(cur, os.path.join(tmp, "nope.json"))["status"] == "new-baseline"
        assert compare.check_geometry(os.path.join(tmp, "nope.json"), cur)["status"] == "fail"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_visual_geometry_check_tolerates_gltf_vertex_splitting():
    """Eksporter glTF duplikuje wierzchołki w innej kolejności przy każdym przebiegu."""
    tmp = tempfile.mkdtemp()
    try:
        base = _meta_file(tmp, "base.json", _meta(vertices=5360, faces=4732))
        near = _meta_file(tmp, "near.json", _meta(vertices=5386, faces=4732))
        result = compare.check_geometry(near, base)
        assert result["status"] == "pass", result
        assert result["counts"]["vertices"]["delta"] == 26
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_visual_geometry_check_still_catches_real_mesh_change():
    tmp = tempfile.mkdtemp()
    try:
        base = _meta_file(tmp, "base.json", _meta(vertices=5360, faces=4732))
        coarse = _meta_file(tmp, "coarse.json", _meta(vertices=2000, faces=1500))
        result = compare.check_geometry(coarse, base)
        assert result["status"] == "fail"
        assert result["checks"]["vertices"] is False and result["checks"]["faces"] is False
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_visual_geometry_check_keeps_bbox_and_object_count_strict():
    tmp = tempfile.mkdtemp()
    try:
        base = _meta_file(tmp, "base.json", _meta(vertices=5360))
        moved = _meta_file(tmp, "moved.json", _meta(bbox_max=(94.002, 1.35, 3.6), vertices=5386))
        assert compare.check_geometry(moved, base)["status"] == "fail"
        payload = _meta(vertices=5386)
        payload["scene"]["mesh_objects"] = 5
        fewer = _meta_file(tmp, "fewer.json", payload)
        result = compare.check_geometry(fewer, base)
        assert result["status"] == "fail" and result["checks"]["mesh_objects"] is False
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_visual_inside_camera_sits_exactly_at_its_anchor():
    """Kamera z wnętrza musi stać w kotwicy, a nie kadrować scenę z zewnątrz.

    Regresja z T-210: na rzeczywistej, zakrzywionej osi kamera `inside` wpadała
    w ogólne kadrowanie po bboxie i lądowała 13,9 km od oka, poza tunelem. Na
    prostym torze testowym cofnięcie wzdłuż stycznej zostawiało ją w tunelu,
    więc błąd był niewidoczny.
    """
    spec = next(c for c in MANIFEST["scene_sets"]["infrastructure"]["cameras"] if c["id"] == "inside")
    assert spec.get("place_at_anchor") is True
    anchors = {"inside_eye": [85.9, 322.5, 1.75], "inside_target": [96.8, 333.0, 1.75]}
    solved = framing.solve_camera(spec, (0.0, -1072.0, -1.2), (5452.0, 906.0, 4.7), 960, 576, anchors)
    assert solved["distance_m"] == 0.0
    assert solved["location"] == anchors["inside_eye"]
    assert solved["clip_start"] < 0.1


def test_visual_bbox_framed_cameras_are_still_pushed_back():
    """Poprawka nie może zepsuć kamer, które mają kadrować obiekt z zewnątrz."""
    spec = next(c for c in MANIFEST["scene_sets"]["infrastructure"]["cameras"] if c["id"] == "iso")
    solved = framing.solve_camera(spec, (0.0, -1072.0, -1.2), (5452.0, 906.0, 4.7), 960, 576)
    assert solved["distance_m"] > 1000.0
    assert framing.corner_visibility(solved, (0.0, -1072.0, -1.2), (5452.0, 906.0, 4.7)) == 1.0


def test_visual_alignment_set_exists_for_long_infrastructure():
    scene_set = MANIFEST["scene_sets"]["alignment"]
    ids = [c["id"] for c in scene_set["cameras"]]
    assert ids == ["plan", "section", "side", "axis05", "axis25", "axis50", "axis75"]
    for camera in scene_set["cameras"]:
        if camera["id"].startswith("axis"):
            assert camera.get("place_at_anchor") is True
            assert camera["anchor"]["name"] == f"{camera['id']}_eye"
            assert camera["aim"]["name"] == f"{camera['id']}_target"


def test_visual_bounded_depth_camera_does_not_integrate_the_whole_line():
    spec = next(c for c in MANIFEST["scene_sets"]["alignment"]["cameras"] if c["id"] == "section")
    assert spec["depth_m"] == 30.0
    anchors = {"section_eye": [2398.2, -23.8, 1.75], "section_target": [2429.8, -34.6, 1.75]}
    solved = framing.solve_camera(spec, (0.0, -1072.0, -1.2), (5452.0, 906.0, 4.7), 960, 576, anchors)
    depth = solved["clip_end"] - solved["clip_start"]
    assert abs(depth - 30.0) < 1e-3, depth
    # bez `depth_m` ta sama kamera obejmowała ponad 37 km i zlepiała cały łuk w jedną klatkę
    unbounded = dict(spec)
    unbounded.pop("depth_m")
    wide = framing.solve_camera(unbounded, (0.0, -1072.0, -1.2), (5452.0, 906.0, 4.7), 960, 576, anchors)
    assert wide["clip_end"] - wide["clip_start"] > 1000.0


def test_visual_yaw_rotates_the_forward_direction_around_world_up():
    spec = {"id": "y", "projection": "ORTHO", "anchor": {"mode": "named", "name": "a"},
            "aim": {"mode": "named", "name": "b"}, "yaw_deg": 90.0, "frame_width_m": 80.0}
    anchors = {"a": [0.0, 0.0, 0.0], "b": [10.0, 0.0, 0.0]}
    turned = framing.solve_camera(spec, (-5.0, -5.0, -5.0), (5.0, 5.0, 5.0), 960, 576, anchors)
    straight = framing.solve_camera({k: v for k, v in spec.items() if k != "yaw_deg"},
                                    (-5.0, -5.0, -5.0), (5.0, 5.0, 5.0), 960, 576, anchors)
    assert abs(straight["direction"][0] - 1.0) < 1e-9
    assert abs(turned["direction"][1] - 1.0) < 1e-9, turned["direction"]
    # obrót jest wokół pionu świata, więc kamera nie przechyla się na bok
    assert abs(turned["up"][2] - 1.0) < 1e-9
    assert abs(framing._dot(tuple(turned["direction"]), tuple(straight["direction"]))) < 1e-9


def test_visual_side_camera_frames_a_bounded_run_not_the_whole_line():
    spec = next(c for c in MANIFEST["scene_sets"]["alignment"]["cameras"] if c["id"] == "side")
    assert spec["yaw_deg"] == 90.0 and spec["frame_width_m"] == 80.0
    anchors = {"section_eye": [2398.2, -23.8, 1.75], "section_target": [2429.8, -34.6, 1.75]}
    solved = framing.solve_camera(spec, (0.0, -1072.0, -1.2), (5452.0, 906.0, 4.7), 960, 576, anchors)
    assert abs(solved["frame_w_m"] - 80.0) < 1e-3, solved["frame_w_m"]
    # 6,7 km tunelu w kadrze 80 m dałoby kreskę grubości 2 px — o to właśnie chodzi
    assert solved["frame_h_m"] < 60.0


def test_visual_infrastructure_section_is_depth_bounded_too():
    spec = next(c for c in MANIFEST["scene_sets"]["infrastructure"]["cameras"] if c["id"] == "section")
    assert spec["depth_m"] == 30.0


# --- zestaw silnikowy ---------------------------------------------------------

def _manifest():
    path = os.path.join(ROOT, "tools", "visual", "cameras.json")
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def test_visual_godot_set_is_marked_as_engine_rendered():
    """`capture_blender.py` musi umieć odmówić: w tym zestawie nie ma czego renderować."""
    scene_set = _manifest()["scene_sets"]["godot"]
    assert scene_set["renderer"] == "godot"
    for camera in scene_set["cameras"]:
        assert "projection" not in camera, camera
        assert "anchor" not in camera, camera


def test_visual_every_other_set_is_blender_by_default():
    for name, scene_set in _manifest()["scene_sets"].items():
        if name == "godot":
            continue
        assert scene_set.get("renderer", "blender") == "blender", name


def test_visual_godot_threshold_separates_a_hud_only_frame_from_a_real_one():
    """Progi są ZMIERZONE, nie przyjęte.

    Klatka bez geometrii (sam HUD) ma ink 0,0127; najsłabsze prawdziwe ujęcie 0,5433.
    Próg musi leżeć między nimi, i to z zapasem w obie strony.
    """
    thresholds = _manifest()["scene_sets"]["godot"]["thresholds"]
    empty_ink, weakest_real_ink = 0.012721, 0.543301
    assert empty_ink < thresholds["min_ink_fraction"] < weakest_real_ink
    assert thresholds["min_ink_fraction"] > empty_ink * 10.0
    assert thresholds["min_ink_fraction"] < weakest_real_ink / 1.5


def test_visual_godot_does_not_lean_on_distinct_levels():
    """Regresja pojęciowa: dla klatek z silnika ten wskaźnik wskazuje ODWROTNIE.

    Klatka z samym HUD-em ma 235 poziomów jasności, a najbogatsza prawdziwa 213 —
    więc próg „przynajmniej N poziomów" przepuściłby pustkę i odrzuciłby geometrię.
    Dlatego w tym zestawie próg jest niski i jest tylko kontrolą „to nie jest
    jednolity kolor".
    """
    thresholds = _manifest()["scene_sets"]["godot"]["thresholds"]
    empty_levels, real_levels = 235, 210
    assert thresholds["min_distinct_levels"] < real_levels
    assert thresholds["min_distinct_levels"] < empty_levels
    assert thresholds["min_luma_std"] < 0.081944, "luma_std też nie rozróżnia — 0,0819 pusta"


def test_visual_godot_resolution_matches_the_shots():
    assert _manifest()["scene_sets"]["godot"]["resolution"] == [1280, 720]


# --- podłoga pustej klatki dla renderu kontrolnego ----------------------------

def _stats_of(pixels, width=W, height=H):
    tmp = tempfile.mkdtemp()
    try:
        path = os.path.join(tmp, "f.png")
        _write(path, pixels, width, height)
        return compare.image_stats(pngio.read_gray(path))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _uniform(level=0.06):
    return [(level, level, level)] * (W * H)


def _speck(count, level=0.9, background=0.06):
    """Tło plus `count` jasnych pikseli — analogia detalu o ułamku piksela."""
    pixels = _uniform(background)[:]
    for i in range(count):
        pixels[(i * 37) % (W * H)] = (level, level, level)
    return pixels


def test_visual_empty_frame_floor_rejects_uniform_frame():
    reason = compare.empty_frame_reason(_stats_of(_uniform()), compare.EMPTY_FRAME_FLOOR)
    assert reason is not None and "pusty" in reason


def test_visual_empty_frame_floor_rejects_a_handful_of_lit_pixels():
    # Słupek 0,2 m w kadrze 5,4 km zajmuje ułamek piksela. Taka klatka MUSI polec:
    # do tej pory `render_check.py` kończył się na niej zerem.
    stats = _stats_of(_speck(6))
    assert stats["ink_fraction"] > 0.0, "test byłby pusty, gdyby piksele nie zapaliły się"
    assert compare.empty_frame_reason(stats, compare.EMPTY_FRAME_FLOOR) is not None


def test_visual_empty_frame_floor_accepts_a_real_looking_frame():
    assert compare.empty_frame_reason(_stats_of(_scene()), compare.EMPTY_FRAME_FLOOR) is None


def test_visual_empty_frame_floor_is_not_stricter_than_the_manifest():
    """Podłoga ma łapać pustkę, nie unieważniać kadrów, które manifest dopuszcza."""
    for name, scene_set in MANIFEST["scene_sets"].items():
        thresholds = scene_set["thresholds"]
        for key, floor in compare.EMPTY_FRAME_FLOOR.items():
            assert floor <= thresholds[key], (name, key, floor, thresholds[key])


def test_visual_check_image_still_reports_the_empty_reason():
    result = _check(_uniform(), None)
    assert result["status"] == "fail" and result["checks"]["not_empty"] is False
    assert "pusty" in result["reason"]


# --- pngio: PNG-e, których pngio NIE pisze --------------------------------------
#
# Każdy dotychczasowy test czyta plik, który sam przed chwilą zapisał przez
# `write_gray`/`write_rgb`. To zawsze ten sam PNG: 8 bitów, typ koloru 0 albo 2,
# filtr 0 w każdym wierszu, trzy chunki (IHDR, IDAT, IEND) i nic poza nimi.
# Blender produkuje szerszy zbiór — 16 bitów, kanał alfa, filtry 1–4 dobierane per
# wiersz, chunki `tEXt`/`tIME` wokół obrazu. Przegląd mutacyjny 03.09.2026 pokazał
# to wprost: cały dekoder filtrów (`_unfilter`), gałąź 16-bitowa i pominięcie
# chunków dodatkowych stały bez pokrycia — 25 z 38 mutacji `pngio.py` przeżyło.
#
# Dlatego poniższe testy budują PNG-e bajt po bajcie, zamiast prosić o nie `pngio`.


def _png_chunk(tag, payload):
    return (struct.pack(">I", len(payload)) + tag + payload
            + struct.pack(">I", zlib.crc32(tag + payload) & 0xFFFFFFFF))


def _png_bytes(width, height, bit_depth, color_type, rows, filters,
               before=(), after=(), tail=b"", interlace=0):
    """PNG złożony ręcznie: `rows` to bajty NIEfiltrowane, `filters` — typ na wiersz.

    Filtrowanie liczone jest tutaj, w drugą stronę niż w `pngio._unfilter`, więc
    round-trip porównuje dwie niezależne implementacje tej samej definicji z PNG-spec.
    """
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[color_type]
    bpp = channels * (bit_depth // 8)
    stream = bytearray()
    prev = bytes(len(rows[0]))
    for row, ftype in zip(rows, filters):
        encoded = bytearray([ftype])
        for i, value in enumerate(row):
            left = row[i - bpp] if i >= bpp else 0
            up = prev[i]
            upleft = prev[i - bpp] if i >= bpp else 0
            if ftype == 1:
                value -= left
            elif ftype == 2:
                value -= up
            elif ftype == 3:
                value -= (left + up) >> 1
            elif ftype == 4:
                value -= pngio._paeth(left, up, upleft)
            encoded.append(value & 0xFF)
        stream += encoded
        prev = row
    body = _png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, bit_depth,
                                           color_type, 0, 0, interlace))
    for tag, payload in before:
        body += _png_chunk(tag, payload)
    body += _png_chunk(b"IDAT", zlib.compress(bytes(stream), 6))
    for tag, payload in after:
        body += _png_chunk(tag, payload)
    body += _png_chunk(b"IEND", b"")
    return pngio.MAGIC + body + tail


def _read_blob(blob):
    """Wczytuje surowe bajty przez `pngio.read_gray`, przez plik tymczasowy."""
    tmp = tempfile.mkdtemp()
    try:
        path = os.path.join(tmp, "hand.png")
        with open(path, "wb") as handle:
            handle.write(blob)
        return pngio.read_gray(path)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _raises(blob):
    try:
        _read_blob(blob)
    except Exception as exc:  # noqa: BLE001 — interesuje nas KAŻDA odmowa
        return exc
    return None


#: Dwa wiersze po trzy bajty. Pierwszy bajt wiersza jest CELOWO niezerowy: filtry
#: 3 i 4 sięgają po lewego sąsiada dopiero od indeksu `bpp`, a przy zerze w tym
#: miejscu błąd w warunku `i >= bpp` nie zmieniłby ani jednego piksela.
_GREY_ROWS = [bytes([200, 17, 91]), bytes([44, 250, 3])]
_GREY_VALUES = [200, 17, 91, 44, 250, 3]


def _as_bytes(image):
    return [round(value * 255) for value in image.gray]


def test_visual_png_reads_every_filter_type_the_spec_defines():
    """Pięć typów filtra PNG musi dać ten sam obraz; szósty musi zostać odrzucony.

    `write_gray` pisze wyłącznie filtr 0, więc gałęzie 1–4 w `_unfilter` nie były
    wykonywane przez żaden test. Blender dobiera filtr per wiersz i realnie używa
    wszystkich pięciu.

    Kontrola negatywna jest podwójna: filtr spoza zakresu musi dać `PngError`,
    a wiersze o dwóch RÓŻNYCH filtrach muszą dać ten sam obraz co jednorodne —
    inaczej test przechodziłby też wtedy, gdyby dekoder ignorował bajt filtra.
    """
    for ftype in range(5):
        image = _read_blob(_png_bytes(3, 2, 8, 0, _GREY_ROWS, [ftype, ftype]))
        assert image.size == (3, 2), (ftype, image.size)
        assert _as_bytes(image) == _GREY_VALUES, (ftype, _as_bytes(image))

    mixed = _read_blob(_png_bytes(3, 2, 8, 0, _GREY_ROWS, [4, 3]))
    assert _as_bytes(mixed) == _GREY_VALUES, _as_bytes(mixed)

    broken = _raises(_png_bytes(2, 1, 8, 0, [bytes([1, 2])], [7]))
    assert isinstance(broken, pngio.PngError) and "filtr" in str(broken), broken


def test_visual_png_paeth_breaks_ties_the_way_the_spec_requires():
    """Predyktor Paeth przy remisie musi wybrać a, potem b — nigdy c.

    PNG-spec rozstrzyga remisy kolejnością `pa <= pb <= pc`, i to jedyne, co
    odróżnia `<=` od `<` w tej funkcji. Trójki dobrane tak, żeby remis WYSTĄPIŁ,
    a zwycięzcy różnili się wartością:

    * `(3, 6, 5)`: pa = 1, pb = 2, pc = 1 — remis pa/pc, wygrywa a = 3.
      Przy `pa < pc` wygrałoby c = 5.
    * `(6, 3, 5)`: pa = 2, pb = 1, pc = 1 — remis pb/pc, wygrywa b = 3.
      Przy `pb < pc` wygrałoby c = 5.

    Trzeci wariant remisu — `pa == pb` — jest NIEROZSTRZYGALNY: z pa == pb wynika
    a + b = 2c, a stąd pc = 0 < pa, więc pierwsza gałąź i tak nie jest brana.
    Sprawdzone wyczerpująco na wszystkich 16 777 216 trójkach bajtów: zamiana
    `pa <= pb` na `pa < pb` nie zmienia ani jednego wyniku.
    """
    assert pngio._paeth(3, 6, 5) == 3, "remis pa/pc musi iść do a (lewego sąsiada)"
    assert pngio._paeth(6, 3, 5) == 3, "remis pb/pc musi iść do b (górnego sąsiada)"
    # Kontrola negatywna: bez remisu wybór jest jednoznaczny i nie zależy od `<=`.
    assert pngio._paeth(10, 60, 20) == 60, "bez remisu wygrywa b (górny sąsiad)"
    assert pngio._paeth(90, 10, 20) == 90, "bez remisu wygrywa a (lewy sąsiad)"
    assert pngio._paeth(0, 0, 200) == 0


def test_visual_png_luminance_uses_all_three_colour_channels():
    """Luminancja musi ważyć R, G i B — nie brać samego R jako „szarości".

    Wszystkie dotychczasowe obrazy testowe były szare (r == g == b), więc pomylenie
    gałęzi kolorowej z monochromatyczną nie zmieniało ani jednego piksela. Render
    z Blendera szary nie jest.

    Kontrola negatywna: czysty zielony i czysty niebieski MUSZĄ dać różne wyniki —
    gdyby dekoder czytał tylko pierwszy kanał, oba wyszłyby na 0.
    """
    row = bytes([255, 0, 0, 0, 255, 0, 0, 0, 255])
    image = _read_blob(_png_bytes(3, 1, 8, 2, [row], [0]))
    assert image.color_type == 2 and image.bit_depth == 8
    assert abs(image.at(0, 0) - 0.2126) < 1e-9, image.at(0, 0)
    assert abs(image.at(1, 0) - 0.7152) < 1e-9, image.at(1, 0)
    assert abs(image.at(2, 0) - 0.0722) < 1e-9, image.at(2, 0)
    assert image.at(1, 0) != image.at(2, 0), "zielony i niebieski nie mogą się zlać"

    # Ten sam obraz przepuszczony filtrem Paeth — kolor i filtrowanie naraz.
    second = bytes([9, 200, 30, 40, 5, 60, 70, 80, 255])
    filtered = _read_blob(_png_bytes(3, 2, 8, 2, [row, second], [4, 4]))
    assert abs(filtered.at(0, 0) - 0.2126) < 1e-9, filtered.at(0, 0)
    assert abs(filtered.at(1, 1) - (0.2126 * 40 + 0.7152 * 5 + 0.0722 * 60) / 255.0) < 1e-9


def test_visual_png_reads_sixteen_bit_samples():
    """Blender zapisuje 16 bitów na kanał; ta gałąź składa próbkę z dwóch bajtów.

    Sprawdzane są obie odnogi: kolorowa (trzy próbki po dwa bajty) i monochromatyczna.
    Kontrola negatywna siedzi w samej skali — 16-bitowy biały musi wyjść na 1.0,
    a nie na 255/65535, co wychodziłoby przy pomylonym dzielniku.
    """
    row = struct.pack(">HHHHHHHHH", 65535, 0, 0, 0, 65535, 0, 0, 0, 65535)
    image = _read_blob(_png_bytes(3, 1, 16, 2, [row], [0]))
    assert image.bit_depth == 16 and image.color_type == 2
    assert abs(image.at(0, 0) - 0.2126) < 1e-9, image.at(0, 0)
    assert abs(image.at(1, 0) - 0.7152) < 1e-9, image.at(1, 0)
    assert abs(image.at(2, 0) - 0.0722) < 1e-9, image.at(2, 0)

    white = _read_blob(_png_bytes(1, 1, 16, 2, [struct.pack(">HHH", 65535, 65535, 65535)], [0]))
    assert abs(white.at(0, 0) - 1.0) < 1e-12, white.at(0, 0)

    grey = _read_blob(_png_bytes(2, 1, 16, 0, [struct.pack(">HH", 65535, 0)], [0]))
    assert abs(grey.at(0, 0) - 1.0) < 1e-12 and grey.at(1, 0) == 0.0


def test_visual_png_accepts_an_alpha_channel_and_refuses_a_palette():
    """Typ 4 i 6 (z alfą) są obsługiwane, typ 3 (paleta) musi zostać odrzucony.

    `_CHANNELS` zawiera wpis dla palety, więc sam brak klucza jej nie zatrzymuje —
    zatrzymuje ją dopiero osobny warunek. Bez niego indeksy palety zostałyby wzięte
    za jasności i dekoder zwróciłby obraz, tyle że nie ten.

    Kontrola negatywna: greyA musi PRZEJŚĆ i dać wartości z kanału szarości,
    a nie z kanału alfa.
    """
    grey_alpha = _read_blob(_png_bytes(2, 1, 8, 4, [bytes([200, 255, 10, 128])], [0]))
    assert grey_alpha.color_type == 4
    assert _as_bytes(grey_alpha) == [200, 10], _as_bytes(grey_alpha)

    rgba = _read_blob(_png_bytes(2, 1, 8, 6,
                                 [bytes([255, 0, 0, 255, 0, 0, 255, 128])], [0]))
    assert abs(rgba.at(0, 0) - 0.2126) < 1e-9 and abs(rgba.at(1, 0) - 0.0722) < 1e-9

    palette = _raises(_png_bytes(2, 1, 8, 3, [bytes([0, 1])], [0],
                                 before=[(b"PLTE", bytes([255, 0, 0, 0, 255, 0]))]))
    assert isinstance(palette, pngio.PngError), palette
    assert "color_type=3" in str(palette), palette

    interlaced = _raises(_png_bytes(3, 2, 8, 0, _GREY_ROWS, [0, 0], interlace=1))
    assert isinstance(interlaced, pngio.PngError) and "przeplot" in str(interlaced)


def test_visual_png_skips_the_chunks_blender_puts_around_the_image():
    """Chunki poza IHDR/IDAT/IEND muszą być pominięte, a nie zakończyć czytanie.

    Blender zapisuje `tEXt` z nazwą oprogramowania przed IDAT i bywa, że `tIME`
    po nim. Gdyby pętla kończyła się na pierwszym nieznanym chunku, IDAT nigdy by
    się nie uzbierał, a `zlib` wysypałby się na pustym strumieniu — awarią, nie
    komunikatem bramki.

    Kontrola negatywna: śmieci ZA chunkiem IEND muszą zostać zignorowane, bo tam
    czytanie ma się właśnie zatrzymać.
    """
    around = _png_bytes(3, 2, 8, 0, _GREY_ROWS, [0, 0],
                        before=[(b"tEXt", b"Software\x00Blender")],
                        after=[(b"tIME", struct.pack(">HBBBBB", 2026, 9, 3, 10, 0, 0))])
    assert _as_bytes(_read_blob(around)) == _GREY_VALUES

    with_tail = _png_bytes(3, 2, 8, 0, _GREY_ROWS, [0, 0], tail=b"SMIECI" * 8)
    assert _as_bytes(_read_blob(with_tail)) == _GREY_VALUES


def test_visual_png_truncated_header_is_not_reported_as_a_missing_header():
    """Plik urwany W ŚRODKU IHDR nie może twierdzić, że IHDR w nim nie ma.

    Ośmiobajtowa końcówka (długość + tag, bez danych i bez CRC) to jedyne miejsce,
    w którym warunek pętli `pos + 8 <= len(blob)` różni się od `pos + 8 < len(blob)`.
    Przy `<` taki nagłówek nie zostaje nawet obejrzany i `read_gray` melduje
    „brak IHDR" — o pliku, w którym IHDR STOI. Komunikat wysyłałby czytającego
    log CI w złą stronę: kazałby szukać brakującego chunku zamiast uciętego pliku.

    Test pilnuje diagnozy, nie typu wyjątku: dziś ucięty nagłówek wychodzi jako
    `struct.error` z `struct.unpack` i to jest osobna, zapisana w raporcie usterka
    (`read_gray` deklaruje `PngError`). Test przechodzi dla obu typów — nie
    przechodzi dla kłamliwej treści.

    Kontrola negatywna: plik, w którym IHDR NAPRAWDĘ nie ma, musi dostać
    dokładnie ten komunikat.
    """
    cut = pngio.MAGIC + b"\x00\x00\x00\x0dIHDR"
    exc = _raises(cut)
    assert exc is not None, "plik bez danych IHDR został wczytany jak obraz"
    assert "brak IHDR" not in str(exc), (
        f"IHDR w tym pliku jest, tylko ucięty; komunikat kłamie: {exc}")

    without = (pngio.MAGIC + _png_chunk(b"IDAT", zlib.compress(b"\x00\x01", 6))
               + _png_chunk(b"IEND", b""))
    missing = _raises(without)
    assert isinstance(missing, pngio.PngError) and "brak IHDR" in str(missing), missing


def test_visual_png_writers_clamp_out_of_range_values_to_black_and_white():
    """Wartości spoza 0.0–1.0 mają być przycięte, a nie wysadzić zapis.

    `compare.py` liczy obraz różnicowy z wartości, które mogą minimalnie wyjść poza
    zakres po arytmetyce zmiennoprzecinkowej. Bez przycięcia `int(round(1.002 * 255))`
    daje 256, a `bytearray.append` rzuca wtedy `ValueError` — bramka wizualna padłaby
    na zapisie diffa, nie na porównaniu.

    Granica jest sprawdzana TUŻ nad progiem, nie daleko od niego: 1.002 to najmniejsza
    z okrągłych wartości, przy której brak przycięcia realnie przekracza bajt
    (1.001 * 255 = 255.255 zaokrągla się jeszcze do 255).

    Kontrola negatywna: 1.0 i 0.0 to wartości LEGALNE i muszą przejść nietknięte,
    a wartość ujemna ma wyjść na czerń, nie na przepełnienie w drugą stronę.
    """
    tmp = tempfile.mkdtemp()
    try:
        path = os.path.join(tmp, "clamp.png")
        pngio.write_gray(path, 4, 1, [-3.0, 0.0, 1.0, 1.002])
        image = pngio.read_gray(path)
        assert _as_bytes(image) == [0, 0, 255, 255], _as_bytes(image)

        pngio.write_rgb(path, 3, 1, [(-3.0, -1e-9, 0.0), (1.0, 1.0, 1.0), (1.002, 5.0, 1.5)])
        image = pngio.read_gray(path)
        assert image.at(0, 0) == 0.0, image.at(0, 0)
        assert abs(image.at(1, 0) - 1.0) < 1e-12, image.at(1, 0)
        assert abs(image.at(2, 0) - 1.0) < 1e-12, image.at(2, 0)

        # Kontrola negatywna: wartości w zakresie NIE są przycinane do skrajności.
        pngio.write_gray(path, 2, 1, [0.5, 0.25])
        assert _as_bytes(pngio.read_gray(path)) == [128, 64]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# --- kompletność chunku -------------------------------------------------------
# `read_gray` deklaruje własny wyjątek `PngError`, ale plik urwany w środku chunku
# wychodził spod `struct.unpack` jako `struct.error`, a urwany w środku IDAT — spod
# `zlib.decompress` jako `zlib.error`. Bramka wizualna łapie `PngError` i zamienia go
# na komunikat; wyjątek spoza kontraktu przelatuje przez nią jako traceback i nie mówi
# ani który chunk jest ucięty, ani ile w nim brakuje. Poniższe testy pilnują typu
# wyjątku ORAZ treści komunikatu, bo to komunikat trafia do logu CI.


def _good_png():
    """Poprawny plik odniesienia: MAGIC + IHDR + IDAT + IEND, bez ogona."""
    return _png_bytes(3, 2, 8, 0, _GREY_ROWS, [0, 0])


def _good_ihdr():
    """Poprawny chunk IHDR 3x2, 8 bitów, szarość — do sklejania ułomków ręcznie."""
    return _png_chunk(b"IHDR", struct.pack(">IIBBBBB", 3, 2, 8, 0, 0, 0, 0))


def test_visual_png_truncated_idat_is_a_png_error_not_a_struct_or_zlib_error():
    """Plik urwany w środku IDAT ma dać `PngError`, nie `zlib.error`.

    Tak wygląda render przerwany w połowie zapisu — dysk zapełniony, ubity Blender,
    artefakt CI ściągnięty częściowo. Bramka wizualna ma wtedy powiedzieć „plik jest
    ucięty", a nie wysypać się wyjątkiem z wnętrza `zlib`, po którym nie widać nawet,
    o który plik chodzi.

    Komunikat musi podać LICZBĘ brakujących bajtów, bo to jedyna informacja, która
    odróżnia plik ucięty o ogon od pliku uszkodzonego w środku.

    Kontrola negatywna jest podwójna: ten sam plik NIEucięty musi się wczytać i dać
    dokładnie te same wartości co zawsze, a komunikat o ucięciu nie może nazywać
    chunku IHDR — ten w pliku stoi cały.
    """
    good = _good_png()
    assert _as_bytes(_read_blob(good)) == _GREY_VALUES, "plik odniesienia jest zły"

    # Ucinamy IEND (12 B) i pięć bajtów ogona IDAT: 4 B CRC + 1 B danych.
    cut = good[:len(good) - 12 - 5]
    exc = _raises(cut)
    assert isinstance(exc, pngio.PngError), f"oczekiwano PngError, dostano {exc!r}"
    assert not isinstance(exc, (struct.error, zlib.error)), repr(exc)
    assert "IDAT" in str(exc), exc
    assert "IHDR" not in str(exc), f"IHDR w tym pliku jest cały; komunikat kłamie: {exc}"
    assert "brakuje 5 B" in str(exc), exc


def test_visual_png_truncated_chunk_header_is_a_png_error_too():
    """Plik urwany w środku 8-bajtowego nagłówka chunku też ma dać `PngError`.

    To druga, cichsza połowa tej samej usterki: przy mniej niż ośmiu bajtach pętla
    `while pos + 8 <= len(blob)` po prostu się kończy, ogryzek zostaje przemilczany
    i błąd wychodzi dopiero z `zlib` — albo wcale, gdy IDAT zdążył się uzbierać
    wcześniej. Wtedy bramka porównałaby NIEPEŁNY obraz z baseline i orzekła regresję
    tam, gdzie jest ucięty plik.

    Kontroli negatywnych dwie. Pierwsza: plik urwany DOKŁADNIE na granicy chunku nie
    może dostać tego komunikatu — nie ma tam żadnego ogryzka nagłówka, a komunikat
    o urwanym nagłówku byłby kłamstwem. Druga: śmieci ZA chunkiem IEND nadal muszą
    być ignorowane (`test_visual_png_skips_the_chunks_blender_puts_around_the_image`
    tego pilnuje od strony pliku poprawnego — tu pilnujemy, że nowa kontrola tego
    nie zepsuła), bo tam czytanie kończy się przez `break`, a nie przez wyczerpanie
    bufora.
    """
    head = len(pngio.MAGIC) + 8 + 13 + 4          # MAGIC + cały IHDR
    good = _good_png()

    stub = good[:head + 5]                         # pięć z ośmiu bajtów nagłówka IDAT
    exc = _raises(stub)
    assert isinstance(exc, pngio.PngError), f"oczekiwano PngError, dostano {exc!r}"
    assert not isinstance(exc, (struct.error, zlib.error)), repr(exc)
    assert "urwany w nagłówku chunku" in str(exc), exc
    assert "zostało 5 B" in str(exc), exc

    on_boundary = _raises(good[:head])
    assert on_boundary is not None, "plik bez IDAT nie może przejść jako obraz"
    assert "urwany w nagłówku chunku" not in str(on_boundary), (
        f"plik urwany na granicy chunku nie ma ogryzka nagłówka: {on_boundary}")

    with_tail = _png_bytes(3, 2, 8, 0, _GREY_ROWS, [0, 0], tail=b"SMIECI" * 8)
    assert _as_bytes(_read_blob(with_tail)) == _GREY_VALUES, "ogon za IEND-em ma być pominięty"


def test_visual_png_truncation_message_names_the_chunk_that_is_actually_cut():
    """Komunikat ma wskazać TEN chunk, który jest ucięty — dowolny, nie tylko IDAT.

    Blender wsuwa przed IDAT `tEXt`, a po nim `tIME`. Gdyby komunikat nazywał zawsze
    IDAT (albo chunk poprzedni), log CI kazałby szukać uszkodzenia w danych obrazu,
    podczas gdy plik urywa się w metadanych — i odwrotnie.

    Sprawdzana jest też odporność samej nazwy: w uszkodzonym pliku w miejscu tagu
    stoją dowolne bajty, a `decode("ascii")` rzuciłby na nich `UnicodeDecodeError`,
    czyli znowu wyjątek spoza kontraktu modułu.

    Kontrola negatywna: dla uciętego `tEXt` komunikat NIE może zawierać słowa IDAT,
    a dla tagu z bajtami niedrukowalnymi nie może udawać, że przeczytał nazwę.
    """
    text = b"Software\x00Blender"
    with_text = _png_bytes(3, 2, 8, 0, _GREY_ROWS, [0, 0], before=[(b"tEXt", text)])
    # Ucinamy w środku danych tEXt: zostaje nagłówek + 3 bajty z `len(text)` + 4 CRC.
    head = len(pngio.MAGIC) + 8 + 13 + 4
    cut = with_text[:head + 8 + 3]
    exc = _raises(cut)
    assert isinstance(exc, pngio.PngError), f"oczekiwano PngError, dostano {exc!r}"
    assert "tEXt" in str(exc), exc
    assert "IDAT" not in str(exc), f"ucięty jest tEXt, nie IDAT: {exc}"
    assert f"brakuje {len(text) - 3 + 4} B" in str(exc), exc

    # Tag z bajtami niedrukowalnymi: ma wyjść `PngError`, nie `UnicodeDecodeError`.
    bogus = pngio.MAGIC + _good_ihdr() + b"\x00\x00\x00\x20" + b"\x01\x02\xffZ"
    exc = _raises(bogus)
    assert isinstance(exc, pngio.PngError), f"oczekiwano PngError, dostano {exc!r}"
    assert not isinstance(exc, UnicodeDecodeError), repr(exc)
    assert repr(b"\x01\x02\xffZ") in str(exc), exc
    assert "brakuje 36 B" in str(exc), exc  # 32 B danych + 4 B CRC


def test_visual_png_completeness_check_leaves_correct_files_byte_for_byte():
    """Kontrola kompletności nie może ruszyć ANI JEDNEJ wartości w pliku poprawnym.

    Nowy warunek stoi na ścieżce każdego chunku każdego pliku, więc pomyłka o jeden
    (`>=` zamiast `>`) odrzucałaby PNG-i całkiem zdrowe — a IEND kończy się dokładnie
    na końcu bufora, czyli na tej właśnie granicy. Test przechodzi przez warianty,
    które realnie wychodzą z Blendera: 8 i 16 bitów, szarość, RGB, kanał alfa, filtry
    per wiersz i chunki dodatkowe po obu stronach IDAT.

    Porównanie jest bajt w bajt względem wartości WPISANYCH do pliku, a nie względem
    drugiego przebiegu `read_gray` — inaczej test przeszedłby też wtedy, gdyby dekoder
    psuł obraz w ten sam sposób za każdym razem.

    Kontrola negatywna: `write_gray` → `read_gray` w pełnym obiegu musi dać te same
    bajty, a plik z chunkami dookoła — te same co bez nich.
    """
    plain = _read_blob(_good_png())
    assert plain.size == (3, 2) and plain.bit_depth == 8 and plain.color_type == 0
    assert _as_bytes(plain) == _GREY_VALUES, _as_bytes(plain)

    for ftype in range(5):
        image = _read_blob(_png_bytes(3, 2, 8, 0, _GREY_ROWS, [ftype, ftype]))
        assert _as_bytes(image) == _GREY_VALUES, (ftype, _as_bytes(image))

    around = _png_bytes(3, 2, 8, 0, _GREY_ROWS, [0, 0],
                        before=[(b"tEXt", b"Software\x00Blender")],
                        after=[(b"tIME", struct.pack(">HBBBBB", 2026, 9, 3, 10, 0, 0))])
    assert _as_bytes(_read_blob(around)) == _GREY_VALUES

    rgb = _read_blob(_png_bytes(3, 1, 8, 2, [bytes([255, 0, 0, 0, 255, 0, 0, 0, 255])], [0]))
    assert abs(rgb.at(0, 0) - 0.2126) < 1e-9 and abs(rgb.at(2, 0) - 0.0722) < 1e-9

    deep = _read_blob(_png_bytes(2, 1, 16, 0, [struct.pack(">HH", 65535, 0)], [0]))
    assert abs(deep.at(0, 0) - 1.0) < 1e-12 and deep.at(1, 0) == 0.0

    alpha = _read_blob(_png_bytes(2, 1, 8, 4, [bytes([200, 255, 10, 128])], [0]))
    assert _as_bytes(alpha) == [200, 10], _as_bytes(alpha)

    tmp = tempfile.mkdtemp()
    try:
        path = os.path.join(tmp, "roundtrip.png")
        pngio.write_gray(path, 3, 2, [v / 255.0 for v in _GREY_VALUES])
        assert _as_bytes(pngio.read_gray(path)) == _GREY_VALUES
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
