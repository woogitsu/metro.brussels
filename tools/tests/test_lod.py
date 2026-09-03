#!/usr/bin/env python3
"""Testy poziomów szczegółowości i geometrii kolizyjnej (T-210 LOD).

Bez Blendera i bez pytest. Geometria idzie przez `sweep.sweep` na prawdziwej osi
pakietu A, więc liczby są liczbami z tego samego generatora, który produkuje GLB;
manifesty do kontroli negatywnej są budowane z ręki i celowo psute — kontrola,
która przechodzi tylko na poprawnym wejściu, nie dowodzi niczego
(`docs/06-worked-example.md`).
"""
import copy
import json
import math
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "blender"))

import lod as LD  # noqa: E402
import profiles as PR  # noqa: E402
import sweep as SW  # noqa: E402

BOX = PR.profile_points("box_double")
TRACK_OFFSETS = PR.PROFILES["box_double"]["track_offsets"]


def _straight(count=40, length=400.0):
    return [(length * i / count, 0.0, 0.0) for i in range(count + 1)]


def _arc(count=60, radius=91.5, sweep_deg=90.0):
    return [(radius * math.cos(math.radians(sweep_deg) * i / count),
             radius * math.sin(math.radians(sweep_deg) * i / count), 0.0)
            for i in range(count + 1)]


def _frames(points):
    dense = SW.dedupe(points)
    frames = SW.rmf_frames(dense)
    return frames, SW.chainages([f[0] for f in frames])


def _manifest(levels=(0, 1, 2)):
    """Poprawny manifest schematu 2 o dwóch chunkach, LOD-ach i kolizji."""
    def lods(prefix, triangles):
        out = []
        for level in levels:
            out.append({
                "level": level,
                "file": f"{prefix}.glb" if level == 0 else f"{prefix}_lod{level}.glb",
                "start_m": 0.0 if prefix.endswith("c00") else 500.0,
                "end_m": 500.0 if prefix.endswith("c00") else 1000.0,
                "triangles": triangles // (level + 1),
                "vertices": 100 // (level + 1),
                "max_deviation_m": 0.0 if level == 0 else 0.1 * level,
                "median_deviation_m": 0.0 if level == 0 else 0.01 * level,
            })
        return out

    def chunk(index, start, end, triangles):
        prefix = f"T_c{index:02d}"
        return {
            "id": prefix, "index": index, "file": f"{prefix}.glb",
            "start_m": start, "end_m": end, "length_m": end - start,
            "vertices": 100, "faces": triangles // 2, "triangles": triangles,
            "bbox_min_m": [start, -5.0, -1.2], "bbox_max_m": [end, 5.0, 4.7],
            "bbox_size_m": [end - start, 10.0, 5.9],
            "geometry_sha256": "0" * 64, "sha256": "1" * 64, "bytes": 1024,
            "stations": [], "lods": lods(prefix, triangles),
            "collision": {
                "file": f"{prefix}_col.glb", "start_m": start, "end_m": end,
                "triangles": triangles // 3, "vertices": 40,
                "transversally_closed": True, "end_caps": False,
                "volume_m3": 1000.0, "wall_margin_m": 0.05,
                "gauge_margin_m": 0.65, "inset_m": 0.15,
            },
        }

    return {
        "schema_version": 2,
        "axis_length_m": 1000.0,
        "chunk_count": 2,
        "chunk_length_sum_m": 1000.0,
        "station_count": 0,
        "totals": {"vertices": 200, "faces": 600, "triangles": 1200},
        "lod_levels": [
            {"level": level, "max_chord_m": 0.0 if level == 0 else 25.0 * level,
             "max_sagitta_m": 0.15 * level, "switch_distance_m": 200.0 * level,
             "status": "design_assumption", "triangles": 600 // (level + 1),
             "max_deviation_m": 0.1 * level, "median_deviation_m": 0.01 * level}
            for level in levels],
        "chunks": [chunk(0, 0.0, 500.0, 600), chunk(1, 500.0, 1000.0, 600)],
    }


# --- wybór pierścieni ---------------------------------------------------------

def test_lod_level_zero_keeps_every_ring():
    frames, station = _frames(_arc())
    positions = [f[0] for f in frames]
    kept = LD.select_rings(positions, station, 0, len(frames) - 1, 0.0, 0.0)
    assert kept == list(range(len(frames)))


def test_lod_selection_always_keeps_both_chunk_ends():
    frames, station = _frames(_arc())
    positions = [f[0] for f in frames]
    for chord, sag in ((25.0, 0.15), (60.0, 0.35), (1000.0, 10.0)):
        kept = LD.select_rings(positions, station, 3, 44, chord, sag)
        assert kept[0] == 3 and kept[-1] == 44, (chord, sag, kept)


def test_lod_selection_respects_the_chord_limit():
    frames, station = _frames(_straight())
    positions = [f[0] for f in frames]
    kept = LD.select_rings(positions, station, 0, len(frames) - 1, 25.0, 0.0)
    spans = [station[b] - station[a] for a, b in zip(kept, kept[1:])]
    assert max(spans) <= 25.0 + 1e-9, spans


def test_lod_selection_respects_the_sagitta_limit_on_a_tight_curve():
    frames, station = _frames(_arc())
    positions = [f[0] for f in frames]
    kept = LD.select_rings(positions, station, 0, len(frames) - 1, 200.0, 0.15)
    for a, b in zip(kept, kept[1:]):
        assert LD.sagitta_m(positions, a, b) <= 0.15 + 1e-9


def test_lod_sagitta_limit_is_what_saves_a_tight_curve_from_a_plain_step():
    """Sam krok metryczny na łuku R=91,5 m daje błąd rzędu metrów, para limitów nie."""
    frames, station = _frames(_arc())
    positions = [f[0] for f in frames]
    last = len(frames) - 1
    step_only = LD.select_rings(positions, station, 0, last, 60.0, 0.0)
    both = LD.select_rings(positions, station, 0, last, 60.0, 0.35)
    worst_step = max(LD.sagitta_m(positions, a, b) for a, b in zip(step_only, step_only[1:]))
    worst_both = max(LD.sagitta_m(positions, a, b) for a, b in zip(both, both[1:]))
    assert worst_step > 1.0, worst_step
    assert worst_both <= 0.35 + 1e-9, worst_both


def test_lod_a_sparser_level_never_keeps_more_rings():
    frames, station = _frames(_arc())
    positions = [f[0] for f in frames]
    last = len(frames) - 1
    counts = [len(LD.select_rings(positions, station, 0, last,
                                  p["max_chord_m"], p["max_sagitta_m"]))
              for p in LD.LOD_LEVELS]
    assert counts == sorted(counts, reverse=True), counts


# --- błąd geometryczny --------------------------------------------------------

def test_lod_deviation_of_level_zero_against_itself_is_zero():
    frames, station = _frames(_arc())
    stats = LD.deviation_stats(frames, BOX, station, 0, len(frames) - 1,
                               list(range(len(frames))))
    assert stats["max_m"] == 0.0 and stats["median_m"] == 0.0


def test_lod_deviation_grows_with_the_level():
    frames, station = _frames(_arc())
    positions = [f[0] for f in frames]
    last = len(frames) - 1
    worst = []
    for params in LD.LOD_LEVELS:
        kept = LD.select_rings(positions, station, 0, last,
                               params["max_chord_m"], params["max_sagitta_m"])
        worst.append(LD.deviation_stats(frames, BOX, station, 0, last, kept)["max_m"])
    assert worst == sorted(worst), worst


def test_lod_deviation_stays_within_the_declared_sagitta_plus_profile_radius():
    """Odchyłka powierzchni nie może być gorsza niż strzałka osi razy zasięg profilu."""
    frames, station = _frames(_arc())
    positions = [f[0] for f in frames]
    last = len(frames) - 1
    kept = LD.select_rings(positions, station, 0, last, 25.0, 0.15)
    stats = LD.deviation_stats(frames, BOX, station, 0, last, kept)
    reach = max(math.hypot(x, y) for x, y in BOX)
    assert stats["max_m"] <= 0.15 * (1.0 + reach), (stats["max_m"], reach)


def test_lod_deviation_is_measured_on_the_dropped_rings_not_on_the_kept_ones():
    frames, station = _frames(_arc())
    positions = [f[0] for f in frames]
    last = len(frames) - 1
    kept = LD.select_rings(positions, station, 0, last, 60.0, 0.35)
    stats = LD.deviation_stats(frames, BOX, station, 0, last, kept)
    assert stats["samples"] == (last + 1) * len(BOX)
    assert stats["max_m"] > 0.0
    assert stats["median_m"] < stats["max_m"]


# --- objętość i bbox ----------------------------------------------------------

def test_lod_volume_of_a_straight_tube_equals_area_times_length():
    frames, _station = _frames(_straight(count=4, length=200.0))
    rings = LD.rings_of(frames, BOX, list(range(len(frames))))
    assert math.isclose(LD.tube_volume_m3(rings), LD.polygon_area_m2(BOX) * 200.0,
                        rel_tol=1e-9)


def test_lod_volume_only_shrinks_and_by_under_one_percent_on_a_tight_arc():
    """Cięciwa ścina naroże łuku, więc objętość może tylko spaść — i to nieznacznie."""
    frames, station = _frames(_arc())
    positions = [f[0] for f in frames]
    last = len(frames) - 1
    base = LD.tube_volume_m3(LD.rings_of(frames, BOX, list(range(last + 1))))
    kept = LD.select_rings(positions, station, 0, last, 60.0, 0.35)
    sparse = LD.tube_volume_m3(LD.rings_of(frames, BOX, kept))
    assert 0.0 < base - sparse < 0.01 * base, (base, sparse, (base - sparse) / base)


def test_lod_bbox_never_grows_beyond_the_full_resolution_one():
    frames, station = _frames(_arc())
    positions = [f[0] for f in frames]
    last = len(frames) - 1
    base = SW.build_chunk_from_rings(frames, station, BOX, list(range(last + 1)))
    lo0, hi0 = SW.bounding_box([base])
    for params in LD.LOD_LEVELS[1:]:
        kept = LD.select_rings(positions, station, 0, last,
                               params["max_chord_m"], params["max_sagitta_m"])
        lo, hi = SW.bounding_box([SW.build_chunk_from_rings(frames, station, BOX, kept)])
        for i in range(3):
            assert lo[i] >= lo0[i] - 1e-9 and hi[i] <= hi0[i] + 1e-9


# --- szwy ---------------------------------------------------------------------

def test_lod_seam_is_tight_between_any_pair_of_levels():
    """Streaming ma prawo trzymać chunk n w LOD 0 i chunk n+1 w LOD 2."""
    frames, station = _frames(_arc(count=80))
    positions = [f[0] for f in frames]
    cut = 40
    columns = len(BOX) + 1
    meshes = {}
    for params in LD.LOD_LEVELS:
        for tag, (a, b) in (("left", (0, cut)), ("right", (cut, len(frames) - 1))):
            kept = LD.select_rings(positions, station, a, b,
                                   params["max_chord_m"], params["max_sagitta_m"])
            meshes[(params["level"], tag)] = SW.build_chunk_from_rings(frames, station,
                                                                      BOX, kept)
    for low in (0, 1, 2):
        for high in (0, 1, 2):
            gap = SW.chunk_gap_m(meshes[(low, "left")], meshes[(high, "right")], columns)
            assert gap < 1e-9, (low, high, gap)


def test_lod_mesh_normals_stay_inside_at_every_level():
    frames, station = _frames(_arc())
    positions = [f[0] for f in frames]
    last = len(frames) - 1
    columns = len(BOX) + 1
    for params in LD.LOD_LEVELS:
        kept = LD.select_rings(positions, station, 0, last,
                               params["max_chord_m"], params["max_sagitta_m"])
        mesh = SW.build_chunk_from_rings(frames, station, BOX, kept)
        assert SW.outward_faces(mesh, frames, columns) == 0, params["level"]
        assert SW.degenerate_faces(mesh) == []
        assert SW.non_finite([mesh]) == 0


# --- geometria kolizyjna ------------------------------------------------------

def test_collision_hull_is_strictly_inside_the_tunnel_profile():
    hull = LD.inset_polygon(BOX, LD.COLLISION_INSET_M)
    assert len(hull) == len(BOX)
    for x, y in hull:
        assert LD.polygon_signed_distance_m(BOX, x, y) > 0.0, (x, y)
    assert LD.polygon_area_m2(hull) < LD.polygon_area_m2(BOX)


def test_collision_hull_still_holds_the_m7_gauge_on_both_tracks():
    """Skrajnia pojazdu to NIE światło tunelu — to kontrola, że wcięcie jej nie zjadło."""
    hull = LD.inset_polygon(BOX, LD.COLLISION_INSET_M)
    margin = LD.gauge_margin_m(hull, PR.vehicle_gauge(), TRACK_OFFSETS)
    assert margin > 0.0, margin
    assert margin < LD.gauge_margin_m(BOX, PR.vehicle_gauge(), TRACK_OFFSETS)


def test_collision_inset_is_at_least_the_sagitta_it_has_to_absorb():
    assert LD.COLLISION_INSET_M > LD.COLLISION_MAX_SAGITTA_M


def test_collision_solid_never_pokes_out_through_the_tunnel_wall():
    frames, station = _frames(_arc())
    last = len(frames) - 1
    solid = LD.collision_solid(frames, station, BOX, 0, last)
    margin = LD.wall_margin_m(frames, BOX, solid["profile"], station, 0, last,
                              solid["ring_indices"])
    assert margin > 0.0, margin


def test_collision_solid_with_no_inset_would_poke_out_negative_control():
    """Kontrola negatywna: bez wcięcia bryła WYCHODZI poza ścianę i pomiar to widzi."""
    frames, station = _frames(_arc())
    last = len(frames) - 1
    naked = LD.collision_solid(frames, station, BOX, 0, last, inset_m=0.0)
    margin = LD.wall_margin_m(frames, BOX, naked["profile"], station, 0, last,
                              naked["ring_indices"])
    assert margin < 0.0, margin


def test_collision_solid_is_transversally_closed_but_open_along_the_axis():
    frames, station = _frames(_arc())
    solid = LD.collision_solid(frames, station, BOX, 0, len(frames) - 1)
    columns = len(solid["profile"]) + 1
    closed, boundary, expected = LD.transversally_closed(solid, columns)
    assert closed
    assert boundary == expected == 2 * len(solid["profile"])


def test_collision_solid_is_cheaper_than_the_visual_mesh():
    frames, station = _frames(_arc())
    last = len(frames) - 1
    visual = SW.build_chunk_from_rings(frames, station, BOX, list(range(last + 1)))
    solid = LD.collision_solid(frames, station, BOX, 0, last)
    assert len(solid["faces"]) < len(visual["faces"])


def test_collision_solid_shares_the_seam_ring_with_its_neighbour():
    frames, station = _frames(_arc(count=80))
    cut = 40
    left = LD.collision_solid(frames, station, BOX, 0, cut)
    right = LD.collision_solid(frames, station, BOX, cut, len(frames) - 1)
    columns = len(left["profile"]) + 1
    assert SW.chunk_gap_m(left, right, columns) < 1e-9


def test_collision_solid_normals_point_inside_like_the_visual_mesh():
    frames, station = _frames(_arc())
    solid = LD.collision_solid(frames, station, BOX, 0, len(frames) - 1)
    columns = len(solid["profile"]) + 1
    assert SW.outward_faces(solid, frames, columns) == 0


def test_collision_weld_sees_through_the_duplicated_uv_seam_column():
    """Bez sklejenia kolumna szwu UV udaje brzeg i test rozmaitości kłamie."""
    frames, station = _frames(_straight(count=6, length=60.0))
    solid = LD.collision_solid(frames, station, BOX, 0, len(frames) - 1)
    raw = LD.open_edges([tuple(f) for f in solid["faces"]])
    welded_count, welded = LD.weld(solid["vertices"], [tuple(f) for f in solid["faces"]])
    assert len(LD.open_edges(welded)) < len(raw)
    assert welded_count < len(solid["vertices"])


# --- predykat poziomu ---------------------------------------------------------

def test_lod_predicate_is_separate_from_the_window_predicate():
    """`chunks_for_train` odpowiada za rezydencję i nie wie nic o poziomach."""
    manifest = _manifest()
    resident = SW.chunks_for_train(manifest, 250.0)
    plan = LD.lod_plan(manifest, 250.0)
    assert {c["id"] for c in resident} == set(plan)
    assert all("lod" not in key for c in resident for key in ("start_m", "end_m"))


def test_lod_predicate_gives_level_zero_to_the_chunk_under_the_train():
    manifest = _manifest()
    for chainage in (0.0, 120.0, 499.9, 500.0, 700.0, 1000.0):
        plan = LD.lod_plan(manifest, chainage)
        under = [c["id"] for c in manifest["chunks"]
                 if c["start_m"] <= chainage <= c["end_m"]]
        for chunk_id in under:
            assert plan[chunk_id] == 0, (chainage, chunk_id, plan)


def test_lod_predicate_uses_a_coarser_level_further_away():
    manifest = _manifest()
    chunk = manifest["chunks"][1]
    assert LD.lod_for_distance(0.0, [200.0, 400.0]) == 0
    assert LD.lod_for_distance(250.0, [200.0, 400.0]) == 1
    assert LD.lod_for_distance(900.0, [200.0, 400.0]) == 2
    assert LD.chunk_distance_m(chunk, 100.0) == 400.0
    assert LD.chunk_distance_m(chunk, 700.0) == 0.0


def test_lod_predicate_saves_triangles_over_the_flat_full_resolution_plan():
    manifest = _manifest()
    plan = LD.lod_plan(manifest, 0.0, ahead_m=1000.0, behind_m=0.0)
    flat = {chunk_id: 0 for chunk_id in plan}
    assert LD.lod_triangles(manifest, plan) < LD.lod_triangles(manifest, flat)


def test_collision_plan_always_holds_the_chunk_under_the_train():
    manifest = _manifest()
    chainage = 0.0
    while chainage <= 1000.0:
        ids = LD.collision_plan(manifest, chainage)
        under = [c["id"] for c in manifest["chunks"]
                 if c["start_m"] <= chainage <= c["end_m"]]
        assert set(under) <= set(ids), (chainage, ids)
        chainage += 25.0


def test_collision_plan_is_narrower_than_the_streaming_window():
    manifest = _manifest()
    ids = LD.collision_plan(manifest, 30.0)
    resident = [c["id"] for c in SW.chunks_for_train(manifest, 30.0)]
    assert set(ids) < set(resident), (ids, resident)


# --- kontrola manifestu, w tym negatywy ---------------------------------------

def test_lod_manifest_problems_accepts_a_consistent_manifest():
    assert LD.lod_problems(_manifest()) == []


def test_lod_manifest_problems_rejects_schema_one():
    manifest = _manifest()
    manifest["schema_version"] = 1
    assert LD.lod_problems(manifest)


def test_lod_manifest_problems_detects_a_missing_level():
    manifest = _manifest()
    manifest["chunks"][1]["lods"] = manifest["chunks"][1]["lods"][:2]
    assert any("poziomy nie zgadzają się" in p for p in LD.lod_problems(manifest))


def test_lod_manifest_problems_detects_a_level_that_is_not_cheaper():
    manifest = _manifest()
    manifest["chunks"][0]["lods"][2]["triangles"] = 10_000
    assert any("nie jest tańszy" in p for p in LD.lod_problems(manifest))


def test_lod_manifest_problems_detects_a_level_whose_error_went_down():
    manifest = _manifest()
    manifest["chunks"][0]["lods"][2]["max_deviation_m"] = 0.0
    assert any("mniejszy błąd" in p for p in LD.lod_problems(manifest))


def test_lod_manifest_problems_detects_a_level_with_a_shifted_chainage_range():
    manifest = _manifest()
    manifest["chunks"][0]["lods"][1]["end_m"] += 5.0
    assert any("inny zakres chainage" in p for p in LD.lod_problems(manifest))


def test_lod_manifest_problems_detects_a_missing_collision():
    manifest = _manifest()
    del manifest["chunks"][0]["collision"]
    assert any("brak geometrii kolizyjnej" in p for p in LD.lod_problems(manifest))


def test_lod_manifest_problems_detects_a_collision_poking_through_the_wall():
    manifest = _manifest()
    manifest["chunks"][1]["collision"]["wall_margin_m"] = -0.02
    assert any("wystaje poza światło" in p for p in LD.lod_problems(manifest))


def test_lod_manifest_problems_detects_a_collision_that_does_not_hold_the_gauge():
    manifest = _manifest()
    manifest["chunks"][1]["collision"]["gauge_margin_m"] = -0.01
    assert any("skrajni M7" in p for p in LD.lod_problems(manifest))


def test_lod_manifest_problems_detects_an_open_collision_solid():
    manifest = _manifest()
    manifest["chunks"][0]["collision"]["transversally_closed"] = False
    assert any("zamknięta poprzecznie" in p for p in LD.lod_problems(manifest))


def test_lod_manifest_problems_detects_a_collision_heavier_than_the_visual_mesh():
    manifest = _manifest()
    manifest["chunks"][0]["collision"]["triangles"] = 99_999
    assert any("nie jest tańsza" in p for p in LD.lod_problems(manifest))


def test_lod_manifest_problems_detects_thresholds_not_marked_as_assumptions():
    manifest = _manifest()
    manifest["lod_levels"][1]["status"] = "spec"
    assert any("założenie" in p for p in LD.lod_problems(manifest))


def test_lod_manifest_problems_detects_fewer_than_three_levels():
    manifest = _manifest(levels=(0, 1))
    assert any("wymagane co najmniej 3" in p for p in LD.lod_problems(manifest))


def test_lod_deterministic_view_drops_the_nested_file_hashes_too():
    manifest = _manifest()
    manifest["chunks"][0]["lods"][1]["sha256"] = "a" * 64
    manifest["chunks"][0]["lods"][1]["bytes"] = 111
    manifest["chunks"][0]["collision"]["sha256"] = "b" * 64
    other = copy.deepcopy(manifest)
    other["chunks"][0]["lods"][1]["sha256"] = "c" * 64
    other["chunks"][0]["lods"][1]["bytes"] = 222
    other["chunks"][0]["collision"]["sha256"] = "d" * 64
    assert SW.deterministic_view(manifest) == SW.deterministic_view(other)


def test_lod_deterministic_view_still_sees_a_changed_lod_geometry():
    manifest = _manifest()
    other = copy.deepcopy(manifest)
    other["chunks"][0]["lods"][1]["triangles"] += 2
    assert SW.deterministic_view(manifest) != SW.deterministic_view(other)


# --- próg odległości ----------------------------------------------------------

def test_lod_switch_distance_follows_from_the_measured_error():
    near = LD.switch_distance_m(0.15)
    far = LD.switch_distance_m(0.40)
    assert far > near > 0.0
    assert math.isclose(LD.switch_distance_m(0.30), 2.0 * LD.switch_distance_m(0.15))
    assert 140.0 < near < 170.0, near


def test_lod_switch_distance_of_a_perfect_level_is_zero():
    assert LD.switch_distance_m(0.0) == 0.0


# --- zgodność wstecz ----------------------------------------------------------

def test_lod_ring_subset_builder_matches_the_contiguous_builder():
    """`build_chunk` musi zostać dokładnie tym, czym był — LOD 0 nie zmienia siatki."""
    frames, station = _frames(_arc())
    last = len(frames) - 1
    old = SW.build_chunk(frames, station, BOX, 0, last)
    new = SW.build_chunk_from_rings(frames, station, BOX, list(range(last + 1)))
    assert old["vertices"] == new["vertices"]
    assert old["faces"] == new["faces"]
    assert old["uvs"] == new["uvs"]
    assert SW.chunk_geometry_sha256(old) == SW.chunk_geometry_sha256(new)


def test_lod_uv_along_the_axis_does_not_shift_between_levels():
    """Przełączenie LOD-a nie może przesunąć tekstury: `v` liczy się z chainage ramki."""
    frames, station = _frames(_arc())
    positions = [f[0] for f in frames]
    last = len(frames) - 1
    columns = len(BOX) + 1
    base = SW.build_chunk_from_rings(frames, station, BOX, list(range(last + 1)))
    kept = LD.select_rings(positions, station, 0, last, 25.0, 0.15)
    sparse = SW.build_chunk_from_rings(frames, station, BOX, kept)
    for row, ring in enumerate(kept):
        assert sparse["uvs"][row * columns] == base["uvs"][ring * columns]


def test_lod_streaming_saving_on_package_a_is_measured_not_assumed():
    """Decyzja „scena nie streamuje" stoi w `TunnelView.cs` i ma być poparta liczbą.

    Bez tego testu liczby w tamtym komentarzu są tekstem, który starzeje się po cichu:
    zmiana długości chunka albo kroku pierścienia przesuwa je, a komentarz zostaje.
    Test liczy je z manifestu, jeśli manifest jest w drzewie, i pilnuje rzędu wielkości,
    a nie konkretnej cyfry — bo argument dotyczy rzędu wielkości.

    Pomija się, gdy manifestu nie ma: to jest artefakt `build/`, a `build/` nie jest
    commitowane (`CLAUDE.md` reguła 8).
    """
    path = os.path.join(ROOT, "build", "t400", "chunks", "L1_A-chunks.json")
    if not os.path.isfile(path):
        return

    with open(path, encoding="utf-8") as handle:
        manifest = json.load(handle)
    if int(manifest.get("schema_version", 0)) < 2:
        return

    total = sum(int(c["triangles"]) for c in manifest["chunks"])
    assert total > 0, total

    worst = 0.0
    for chainage in (0.0, 3000.0, 6500.0):
        plan = LD.lod_plan(manifest, chainage)
        assert 0 < len(plan) < len(manifest["chunks"]), (chainage, len(plan))
        worst = max(worst, LD.lod_triangles(manifest, plan) / total)

    assert worst < 0.25, (
        f"rezydentne {worst:.0%} całości — komentarz w TunnelView.cs mówi o 6–17 %, "
        "więc albo manifest się zmienił, albo argument za brakiem streamowania osłabł")


def test_lod_streaming_measurement_would_notice_a_window_that_loads_everything():
    """Kontrola negatywna do testu wyżej: okno obejmujące całą oś ma go wywrócić.

    Test, który mierzy oszczędność, musi umieć zobaczyć jej brak — inaczej przechodzi
    także wtedy, gdy predykat okna przestanie cokolwiek odsiewać.
    """
    path = os.path.join(ROOT, "build", "t400", "chunks", "L1_A-chunks.json")
    if not os.path.isfile(path):
        return

    with open(path, encoding="utf-8") as handle:
        manifest = json.load(handle)
    if int(manifest.get("schema_version", 0)) < 2:
        return

    total = sum(int(c["triangles"]) for c in manifest["chunks"])
    everything = LD.lod_plan(manifest, 3000.0, ahead_m=10_000.0, behind_m=10_000.0)
    assert len(everything) == len(manifest["chunks"]), len(everything)
    assert LD.lod_triangles(manifest, everything) / total > 0.25, \
        "okno na całą oś nadal wygląda na oszczędne — miara nie mierzy"
