"""Deterministyczne wyliczanie kamer kontrolnych — czysty Python, bez bpy.

Ten moduł zawiera całą matematykę kadrowania, żeby dało się ją testować bez
Blendera. `capture_blender.py` tylko przekłada wynik na obiekty kamer.

Konwencja osi: `docs/04-conventions.md` — Blender, Z w górę, 1 jednostka = 1 m.
Wektor `direction` kamery to kierunek patrzenia (od kamery do celu).
Baza kamery jest liczona tak samo jak w `tools/blender/render_check.py`
(`level_camera`), żeby oba narzędzia dawały identyczne ustawienie.
"""
import math

SENSOR_MM = 36.0
UP_PARALLEL_EPS = 0.995


def _norm(v):
    length = math.sqrt(sum(c * c for c in v))
    if length < 1e-12:
        raise ValueError(f"wektor zerowy nie ma kierunku: {v}")
    return tuple(c / length for c in v)


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def _sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


def _add(a, b):
    return tuple(x + y for x, y in zip(a, b))


def _mul(v, s):
    return tuple(c * s for c in v)


def camera_basis(direction):
    """Zwraca (right, up, forward) dokładnie jak render_check.level_camera."""
    forward = _norm(direction)
    world_up = (0.0, 0.0, 1.0)
    if abs(_dot(forward, world_up)) > UP_PARALLEL_EPS:
        world_up = (0.0, 1.0, 0.0)
    right = _norm(_cross(forward, world_up))
    up = _norm(_cross(right, forward))
    return right, up, forward


def bbox_corners(bmin, bmax):
    return [(x, y, z) for x in (bmin[0], bmax[0]) for y in (bmin[1], bmax[1]) for z in (bmin[2], bmax[2])]


def bbox_center(bmin, bmax):
    return tuple((a + b) / 2.0 for a, b in zip(bmin, bmax))


def bbox_size(bmin, bmax):
    return tuple(b - a for a, b in zip(bmin, bmax))


def resolve_anchor(spec, bmin, bmax, named=None):
    """Punkt, na który kamera patrzy.

    Tryby: `bbox_center`, `bbox_fraction` (u,v,w w [0,1] wzdłuż X,Y,Z),
    `named` (punkt podany z zewnątrz, np. wyliczony z osi trasy).
    """
    named = named or {}
    mode = spec.get("mode", "bbox_center")
    if mode == "bbox_center":
        return bbox_center(bmin, bmax)
    if mode == "bbox_fraction":
        u, v, w = float(spec.get("u", 0.5)), float(spec.get("v", 0.5)), float(spec.get("w", 0.5))
        return (bmin[0] + (bmax[0] - bmin[0]) * u,
                bmin[1] + (bmax[1] - bmin[1]) * v,
                bmin[2] + (bmax[2] - bmin[2]) * w)
    if mode == "named":
        name = spec["name"]
        if name not in named:
            raise KeyError(name)
        return tuple(float(c) for c in named[name])
    raise ValueError(f"nieznany tryb kotwicy: {mode}")


def fov(lens_mm, res_x, res_y):
    """Kąty widzenia w poziomie i pionie dla sensor_fit=AUTO (36 mm na dłuższym boku)."""
    if res_x >= res_y:
        sensor_x = SENSOR_MM
        sensor_y = SENSOR_MM * res_y / res_x
    else:
        sensor_y = SENSOR_MM
        sensor_x = SENSOR_MM * res_x / res_y
    return 2.0 * math.atan(sensor_x / (2.0 * lens_mm)), 2.0 * math.atan(sensor_y / (2.0 * lens_mm))


def _extents(corners, anchor, right, up, forward):
    r = [abs(_dot(_sub(c, anchor), right)) for c in corners]
    u = [abs(_dot(_sub(c, anchor), up)) for c in corners]
    d = [_dot(_sub(c, anchor), forward) for c in corners]
    return max(r), max(u), max(d), min(d)


def solve_camera(spec, bmin, bmax, res_x, res_y, named_anchors=None, points=None):
    """Zwraca deterministyczny opis kamery dla jednego wpisu z manifestu.

    Wynik jest czystym słownikiem liczb — trafia zarówno do Blendera, jak i do
    `visual-metadata.json`, więc kadr da się odtworzyć i zaudytować.

    `points` (opcjonalne wierzchołki świata) są używane tylko dla `fit: slab`,
    czyli dla przekroju, gdzie bbox całego obiektu nie opisuje kadru.
    """
    anchor = resolve_anchor(spec.get("anchor", {"mode": "bbox_center"}), bmin, bmax, named_anchors)
    if "aim" in spec:
        target = resolve_anchor(spec["aim"], bmin, bmax, named_anchors)
        direction = _sub(target, anchor)
    else:
        direction = tuple(float(c) for c in spec["direction"])
    right, up, forward = camera_basis(direction)

    corners = bbox_corners(bmin, bmax)
    half_r, half_u, depth_max, depth_min = _extents(corners, anchor, right, up, forward)
    scene_size = max(max(bbox_size(bmin, bmax)), 1.0)
    fit_fallback = False
    if spec.get("fit") == "slab":
        thickness = float(spec.get("slab_thickness_m", 10.0))
        slab = [p for p in (points or []) if abs(_dot(_sub(p, anchor), forward)) <= thickness]
        if slab:
            # przekrój kotwiczy się na geometrii w płaszczyźnie cięcia, nie na środku bboxa
            mean_r = sum(_dot(_sub(p, anchor), right) for p in slab) / len(slab)
            mean_u = sum(_dot(_sub(p, anchor), up) for p in slab) / len(slab)
            anchor = _add(anchor, _add(_mul(right, mean_r), _mul(up, mean_u)))
            out_anchor_shift = (round(mean_r, 6), round(mean_u, 6))
            half_r = max(abs(_dot(_sub(p, anchor), right)) for p in slab)
            half_u = max(abs(_dot(_sub(p, anchor), up)) for p in slab)
            _, _, depth_max, depth_min = _extents(corners, anchor, right, up, forward)
        else:
            fit_fallback = True
            out_anchor_shift = None
    margin = float(spec.get("margin", 1.05))
    projection = spec.get("projection", "PERSP").upper()
    lens = float(spec.get("lens", 50.0))
    out = {
        "id": spec["id"],
        "projection": projection,
        "anchor": [round(c, 6) for c in anchor],
        "direction": [round(c, 6) for c in forward],
        "right": [round(c, 6) for c in right],
        "up": [round(c, 6) for c in up],
        "resolution": [res_x, res_y],
        "margin": margin,
    }
    if spec.get("fit"):
        out["fit"] = spec["fit"]
        out["fit_fallback"] = fit_fallback
        out["anchor_shift_right_up"] = out_anchor_shift

    if projection == "ORTHO":
        need_w = 2.0 * half_r
        need_h = 2.0 * half_u
        long_side = max(res_x, res_y)
        # ortho_scale odwzorowuje dłuższy bok obrazu na jednostki świata
        scale_from_w = need_w * (long_side / res_x)
        scale_from_h = need_h * (long_side / res_y)
        if "frame_width_m" in spec:
            ortho_scale = float(spec["frame_width_m"]) * (long_side / res_x)
        else:
            ortho_scale = max(scale_from_w, scale_from_h) * margin
        ortho_scale = max(ortho_scale, 1e-3)
        distance = max(depth_max, 0.0) + max(scene_size * 0.5, 1.0)
        out["ortho_scale"] = round(ortho_scale, 6)
        out["frame_w_m"] = round(ortho_scale * res_x / long_side, 6)
        out["frame_h_m"] = round(ortho_scale * res_y / long_side, 6)
    else:
        fov_x, fov_y = fov(lens, res_x, res_y)
        if "frame_width_m" in spec:
            distance = (float(spec["frame_width_m"]) / 2.0) / math.tan(fov_x / 2.0)
        else:
            fit = max((half_r * margin) / math.tan(fov_x / 2.0), (half_u * margin) / math.tan(fov_y / 2.0))
            distance = fit + max(depth_max, 0.0)
        out["lens"] = lens
        out["fov_x_deg"] = round(math.degrees(fov_x), 5)
        out["fov_y_deg"] = round(math.degrees(fov_y), 5)

    location = _add(anchor, _mul(forward, -distance))
    out["location"] = [round(c, 6) for c in location]
    out["distance_m"] = round(distance, 6)

    near = distance + depth_min
    if spec.get("clip_at_anchor"):
        # przekrój: płaszczyzna bliska tnie geometrię dokładnie w kotwicy
        clip_start = distance
    else:
        clip_start = max(0.01, min(0.1, scene_size / 100000.0)) if near > 0.2 else max(0.001, near * 0.5)
    clip_end = max(1000.0, scene_size * 8.0, (distance + max(depth_max, 0.0)) * 3.0)
    out["clip_start"] = round(clip_start, 6)
    out["clip_end"] = round(clip_end, 3)
    return out


def corner_visibility(cam, bmin, bmax):
    """Ułamek narożników bboxa mieszczących się w kadrze — do testów kadrowania."""
    right = tuple(cam["right"])
    up = tuple(cam["up"])
    forward = tuple(cam["direction"])
    loc = tuple(cam["location"])
    res_x, res_y = cam["resolution"]
    inside = 0
    corners = bbox_corners(bmin, bmax)
    for c in corners:
        rel = _sub(c, loc)
        d = _dot(rel, forward)
        r = _dot(rel, right)
        u = _dot(rel, up)
        if cam["projection"] == "ORTHO":
            long_side = max(res_x, res_y)
            half_w = cam["ortho_scale"] * res_x / long_side / 2.0
            half_h = cam["ortho_scale"] * res_y / long_side / 2.0
            if d > 0 and abs(r) <= half_w and abs(u) <= half_h:
                inside += 1
        else:
            if d <= 1e-9:
                continue
            tan_x = math.tan(math.radians(cam["fov_x_deg"]) / 2.0)
            tan_y = math.tan(math.radians(cam["fov_y_deg"]) / 2.0)
            if abs(r) <= d * tan_x and abs(u) <= d * tan_y:
                inside += 1
    return inside / len(corners)


def solve_set(manifest, set_name, bmin, bmax, named_anchors=None, points=None):
    """Rozwiązuje wszystkie kamery zestawu. Brakująca kotwica => kamera pominięta jawnie."""
    scene_set = manifest["scene_sets"][set_name]
    res_x, res_y = scene_set["resolution"]
    solved, skipped = [], []
    for spec in scene_set["cameras"]:
        try:
            solved.append(solve_camera(spec, bmin, bmax, res_x, res_y, named_anchors, points))
        except KeyError as missing:
            skipped.append({"id": spec["id"], "reason": f"brak kotwicy {missing}"})
    return solved, skipped
