"""Pomiar i bramka akceptacji bryły M7 — czysty Python, bez Blendera.

Wydzielone z `m7_shell.py`, który importuje `bpy` i przez to nie daje się
zaimportować w `tools/tests/test_all.py`. Przemiatanie mutacyjne z 03.09.2026
pokazało tam 35 mutacji i 35 ocalałych — 100 %, bo nie istniała droga, którą
test mógłby je dotknąć. Wśród nich cała bramka: kontrola długości, szerokości,
wysokości dachu, liczby członów, liczby i szerokości otworów drzwiowych oraz
symetrii obrotowej składu dwukierunkowego.

**Granica przebiega po `MeshRecord`.** Wszystko, czego bramka potrzebuje od
Blendera, mieści się w jednym zwykłym słowniku na siatkę:

    {"name": str, "vertices": [(x, y, z), ...], "faces": int,
     "dimensions": (dx, dy, dz)}

Wierzchołki są już w układzie świata — przemnożenie przez `matrix_world` jest
po stronie `m7_shell.py`, bo to jedyna rzecz, której bez bpy zrobić się nie da.
Wszystko dalej to arytmetyka na krotkach i da się uruchomić w testach.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

NOSE_STEP_M = 0.20
BODY_STEP_M = 1.00
TOLERANCE_M = 0.001
VERTEX_EPS = 1e-4
MIN_PLAUSIBLE_VERTICES = 1000
MAX_PLAUSIBLE_VERTICES = 500000
OVERSIZE_MARGIN_M = 1.0
ENVELOPE_EPS_M = 1e-6


def x_stations(layout, start, end, taper_aware=True):
    """Punkty podziału wzdłuż X: gęściej tam, gdzie przekrój się zmienia."""
    stations = {round(start, 6), round(end, 6)}
    span = end - start
    steps = max(1, int(math.ceil(span / BODY_STEP_M)))
    for i in range(steps + 1):
        stations.add(round(start + span * i / steps, 6))
    if taper_aware:
        from m7_layout import DESIGN_NOSE_LENGTH_M
        for nose_end in (DESIGN_NOSE_LENGTH_M, layout.length - DESIGN_NOSE_LENGTH_M):
            if start - 1e-9 <= nose_end <= end + 1e-9:
                stations.add(round(nose_end, 6))
        nose_steps = int(math.ceil(DESIGN_NOSE_LENGTH_M / NOSE_STEP_M))
        for i in range(nose_steps + 1):
            for candidate in (DESIGN_NOSE_LENGTH_M * i / nose_steps,
                              layout.length - DESIGN_NOSE_LENGTH_M * i / nose_steps):
                if start - 1e-9 <= candidate <= end + 1e-9:
                    stations.add(round(candidate, 6))
    return sorted(stations)

def all_points(records):
    """Wszystkie wierzchołki wszystkich siatek, w kolejności wejścia."""
    out = []
    for record in records:
        out.extend(record["vertices"])
    return out


def bounds(points):
    return ((min(p[0] for p in points), min(p[1] for p in points), min(p[2] for p in points)),
            (max(p[0] for p in points), max(p[1] for p in points), max(p[2] for p in points)))


def check_no_nan(points):
    for point in points:
        for component in point:
            if math.isnan(component) or math.isinf(component):
                return False
    return True

def measure_openings(layout, records):
    """Mierzy rzeczywistą szerokość otworów W WYGENEROWANEJ GEOMETRII, nie w parametrach.

    Różnica jest tu cała: parametry zawsze się zgadzają same ze sobą. Pytanie brzmi,
    czy modyfikator wycinający naprawdę zrobił dziurę tam, gdzie layout ją zaplanował.
    """
    by_x = {}
    for record in records:
        for point in record["vertices"]:
            if abs(abs(point[1]) - layout.half_width) > VERTEX_EPS:
                continue
            key = (round(point[0], 4), 1 if point[1] > 0 else -1)
            by_x.setdefault(key, []).append(round(point[2], 4))

    measured = []
    for door in layout.all_doors():
        side = door["side"]
        left = by_x.get((round(door["x0"], 4), side), [])
        right = by_x.get((round(door["x1"], 4), side), [])
        has_bottom = any(abs(z - door["z0"]) <= VERTEX_EPS for z in left + right)
        has_top = any(abs(z - door["z1"]) <= VERTEX_EPS for z in left + right)
        measured.append({
            "kind": door["kind"],
            "car": door["car"],
            "side": side,
            "center_x": door["center_x"],
            "edges_found": bool(left) and bool(right),
            "corners_found": has_bottom and has_top,
            "measured_width_m": round(door["x1"] - door["x0"], 6) if left and right else None,
            "measured_height_m": round(door["z1"] - door["z0"], 6) if has_bottom and has_top else None,
        })
    return measured

def verify(layout, cars, joints, report):
    problems = []
    body = cars + joints
    vertices = all_points(body)
    bmin, bmax = bounds(vertices)
    size = [bmax[i] - bmin[i] for i in range(3)]
    report["body"] = {
        "bbox_min": [round(c, 6) for c in bmin],
        "bbox_max": [round(c, 6) for c in bmax],
        "size_m": [round(c, 6) for c in size],
        "objects": len(body),
        "cars": len(cars),
        "articulations": len(joints),
        "vertices": sum(len(r["vertices"]) for r in body),
        "faces": sum(r["faces"] for r in body),
        "object_names": [r["name"] for r in body],
    }

    if abs(size[0] - layout.length) > TOLERANCE_M:
        problems.append(f"długość {size[0]:.6f} m != {layout.length} m")
    if abs(size[1] - layout.width) > TOLERANCE_M:
        problems.append(f"szerokość {size[1]:.6f} m != {layout.width} m")
    if abs(bmin[0]) > TOLERANCE_M or abs(bmax[0] - layout.length) > TOLERANCE_M:
        problems.append(f"origin/zasięg X = [{bmin[0]:.6f}, {bmax[0]:.6f}]")
    if abs(bmax[2] - layout.roof_z) > TOLERANCE_M:
        problems.append(f"wysokość dachu {bmax[2]:.6f} m != {layout.roof_z} m")
    if abs(bmin[2] - layout.body_bottom_z) > TOLERANCE_M:
        problems.append(f"spód pudła {bmin[2]:.6f} m != {layout.body_bottom_z} m")
    if len(cars) != layout.cars:
        problems.append(f"członów {len(cars)} != {layout.cars}")
    if not check_no_nan(vertices):
        problems.append("geometria zawiera NaN/Inf")
    if not MIN_PLAUSIBLE_VERTICES < report["body"]["vertices"] < MAX_PLAUSIBLE_VERTICES:
        problems.append(f"podejrzana liczba wierzchołków: {report['body']['vertices']}")
    for record in body:
        dims = record["dimensions"]
        if max(dims) > layout.length + OVERSIZE_MARGIN_M or max(dims) <= 0.0:
            problems.append(f"absurdalna skala obiektu {record['name']}: "
                            f"{tuple(round(d, 3) for d in dims)}")

    openings = measure_openings(layout, body)
    report["openings"] = openings
    doubles = [o for o in openings if o["kind"] == "double"]
    cabs = [o for o in openings if o["kind"] == "cab"]
    report["opening_summary"] = {
        "double_total": len(doubles),
        "double_per_side": len(doubles) // 2,
        "cab_total": len(cabs),
        "double_edges_found": sum(1 for o in doubles if o["edges_found"]),
        "double_corners_found": sum(1 for o in doubles if o["corners_found"]),
        "cab_edges_found": sum(1 for o in cabs if o["edges_found"]),
    }
    if len(doubles) // 2 != layout.doors_per_side:
        problems.append(f"drzwi podwójnych na stronę {len(doubles) // 2} != {layout.doors_per_side}")
    if len(cabs) != layout.cab_doors:
        problems.append(f"drzwi kabinowych {len(cabs)} != {layout.cab_doors}")
    for opening in openings:
        if not opening["edges_found"] or not opening["corners_found"]:
            problems.append(f"otwór {opening['kind']} x={opening['center_x']} strona {opening['side']}"
                            " nie ma krawędzi w geometrii")
        elif opening["kind"] == "double" and abs(opening["measured_width_m"] - layout.door_width) > TOLERANCE_M:
            problems.append(f"otwór x={opening['center_x']}: zmierzone {opening['measured_width_m']} m")

    # Skład jest dwukierunkowy: bryła musi być niezmiennicza na obrót 180 stopni
    # wokół środka pojazdu. To łapie błędy generatora, których nie widać na renderze,
    # bo cieniowanie i tak jest asymetryczne.
    keys = {(round(v[0], 4), round(v[1], 4), round(v[2], 4)) for v in vertices}
    rotated = {(round(layout.length - x, 4), round(-y, 4), z) for x, y, z in keys}
    missing = keys - rotated
    report["rotational_symmetry"] = {
        "vertices": len(keys),
        "mismatched": len(missing),
        "ok": not missing,
        "rule": "(x, y, z) -> (94 - x, -y, z)",
    }
    if missing:
        problems.append(f"bryła nie jest symetryczna obrotowo: {len(missing)} z {len(keys)} wierzchołków")

    gauge_ok, gauge_message = layout.fits_vehicle_gauge()
    tunnel = layout.fits_tunnel_profiles()
    report["gauge"] = {"vehicle_gauge_ok": gauge_ok, "vehicle_gauge_message": gauge_message, "tunnel_profiles": tunnel}
    if not gauge_ok:
        problems.append(f"skrajnia pojazdu: {gauge_message}")
    for name, entry in tunnel.items():
        if not entry["ok"]:
            problems.append(f"profil {name}: {entry['message']}")
    return problems


def roundtrip_result(records, expected_objects, expected_bbox):
    """Ocena re-importu GLB: ta sama liczba siatek i to samo pudełko."""
    bmin, bmax = bounds(all_points(records))
    deltas = [round(bmin[i] - expected_bbox[0][i], 6) for i in range(3)] + \
             [round(bmax[i] - expected_bbox[1][i], 6) for i in range(3)]
    result = {
        "objects": len(records),
        "expected_objects": expected_objects,
        "bbox_min": [round(c, 6) for c in bmin],
        "bbox_max": [round(c, 6) for c in bmax],
        "max_delta_m": max(abs(d) for d in deltas),
        "names": sorted(r["name"] for r in records),
    }
    result["ok"] = result["objects"] == expected_objects and result["max_delta_m"] <= TOLERANCE_M
    return result


def envelope_problems(envelope_bbox, body_bbox):
    """Skrajnia ma OBEJMOWAĆ bryłę w szerokości i wysokości — inaczej nie jest skrajnią."""
    (emin, emax), (bmin, bmax) = envelope_bbox, body_bbox
    problems = []
    for axis, label in ((1, "szerokość"), (2, "wysokość")):
        if emax[axis] + ENVELOPE_EPS_M < bmax[axis] or emin[axis] - ENVELOPE_EPS_M > bmin[axis]:
            problems.append(f"skrajnia nie obejmuje bryły w osi {label}")
    return problems
