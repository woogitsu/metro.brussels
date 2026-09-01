#!/usr/bin/env python3
"""Testy pipeline'u kontroli wizualnej (T-012). Bez Blendera i bez pytest.

Dowodzą tego, czego wymaga #27: identyczny render przechodzi, czarny obraz i zły
rozmiar są odrzucane, przesunięty obiekt przekracza próg, drobny szum nie, a brak
baseline nigdy nie prowadzi do automatycznego nadpisania.
"""
import json
import os
import shutil
import sys
import tempfile

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
