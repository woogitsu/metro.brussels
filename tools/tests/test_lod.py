#!/usr/bin/env python3
"""Testy poziomów szczegółowości i geometrii kolizyjnej (T-210 LOD).

Bez Blendera i bez pytest. Geometria idzie przez `sweep.sweep` na prawdziwej osi
pakietu A, więc liczby są liczbami z tego samego generatora, który produkuje GLB;
manifesty do kontroli negatywnej są budowane z ręki i celowo psute — kontrola,
która przechodzi tylko na poprawnym wejściu, nie dowodzi niczego
(`docs/06-worked-example.md`).
"""
import copy
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


# --- triaż mutacyjny: granice, które wyglądały na pokryte -----------------------
#
# Wszystko poniżej powstało z przeglądu mutacyjnego `tools/tests/mutation_sweep.py`
# na tym module: 105 mutacji, 75 ocalałych. Każdy test tutaj zabija konkretną,
# wypisaną w komentarzu mutację — a mutacja jest jego kontrolą negatywną.
# Klasyfikacja całej siedemdziesiątki piątki: `reports/mutation-triage-lod.md`.


def test_lod_level_params_returns_the_level_it_was_asked_for():
    """Mutacja: 72 `==` -> `!=` — zwracałby PIERWSZY poziom o innym numerze.

    Bez tego testu `level_params(0)` mogło oddawać parametry poziomu 1 i cały LOD 0
    generowałby się z cięciwą 25 m, czyli jako LOD 1 pod cudzą nazwą.
    """
    for entry in LD.LOD_LEVELS:
        assert LD.level_params(entry["level"])["level"] == entry["level"]
        assert LD.level_params(entry["level"]) is entry
    try:
        LD.level_params(len(LD.LOD_LEVELS))
    except ValueError:
        pass
    else:
        raise AssertionError("nieistniejący poziom nie został odrzucony")


def test_lod_selection_rejects_a_chunk_of_one_ring():
    """Mutacja: 125 `<=` -> `<` — `first == last` przechodziłoby dalej."""
    station_m = [0.0, 10.0]
    positions = [(x, 0.0, 0.0) for x in station_m]
    try:
        LD.select_rings(positions, station_m, 1, 1, 10.0, 0.0)
    except ValueError:
        pass
    else:
        raise AssertionError("chunk o jednym pierścieniu nie został odrzucony")


def test_lod_chord_exactly_at_the_limit_is_still_allowed():
    """Mutacja: 135 `>` -> `>=` — cięciwa RÓWNA limitowi zaczęłaby go łamać.

    Limit znaczy „nie dłuższa niż", więc równość mieści się w limicie. Poprzedni
    zestaw testów tego nie odróżniał, bo stacje leżały co 10 m przy limicie 10 m —
    tam obie wersje dają ten sam wynik. Tutaj limit wypada dokładnie na DRUGIM
    kroku, więc różnica jest widoczna: `[0, 2, 3]` wobec `[0, 1, 2, 3]`.
    """
    station_m = [0.0, 5.0, 10.0, 15.0]
    positions = [(x, 0.0, 0.0) for x in station_m]
    assert LD.select_rings(positions, station_m, 0, 3, 10.0, 0.0) == [0, 2, 3]
    assert LD.select_rings(positions, station_m, 0, 3, 9.999, 0.0) == [0, 1, 2, 3]


def test_lod_sagitta_exactly_at_the_limit_is_still_allowed():
    """Mutacja: 137 `>` -> `>=` — strzałka RÓWNA limitowi zaczęłaby go łamać."""
    positions = [(math.cos(math.radians(a)) * 100.0, math.sin(math.radians(a)) * 100.0, 0.0)
                 for a in (0.0, 3.0, 6.0, 9.0)]
    station_m = SW.chainages(positions)
    limit = LD.sagitta_m(positions, 0, 2)
    assert limit > 0.0
    assert LD.select_rings(positions, station_m, 0, 3, 0.0, limit)[1] == 2
    assert LD.select_rings(positions, station_m, 0, 3, 0.0, limit * 0.999)[1] == 1


def test_lod_point_to_segment_survives_a_segment_of_zero_length():
    """Mutacje: 110 i 183 `<= 0.0` -> `< 0.0` — dzielenie przez zero dla a == b.

    Zdublowany punkt osi nie jest hipotezą: `sweep.dedupe` istnieje właśnie dlatego,
    że surowe dane je zawierają. Gdy mimo to trafi tu odcinek zerowy, ma wyjść
    odległość od punktu, a nie `ZeroDivisionError`.
    """
    assert LD._point_to_segment((1.0, 0.0, 0.0), (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)) == 1.0
    assert LD._point_to_segment_2d((1.0, 0.0), (0.0, 0.0), (0.0, 0.0)) == 1.0


def test_lod_volume_of_a_two_ring_tube_is_not_zero():
    """Mutacje: 265 `< 2` -> `<= 2` i `2` -> `3` — rura o dwóch pierścieniach dawałaby 0.

    Dwa pierścienie to najkrótsza rura, jaka w ogóle powstaje, i ma dodatnią objętość.
    Zwrócenie zera byłoby cichym „nie umiem" w miejscu, gdzie kontrola manifestu pyta
    `volume_m3 <= 0` i zameldowałaby pustą bryłę kolizyjną tam, gdzie jej nie ma.
    """
    frames = SW.rmf_frames(SW.dedupe([(0.0, 0.0, 0.0), (10.0, 0.0, 0.0)]))
    volume = LD.tube_volume_m3(LD.rings_of(frames, BOX, [0, 1]))
    assert volume > 0.0, volume
    assert abs(volume - LD.polygon_area_m2(BOX) * 10.0) < 1e-6, volume


def test_lod_weld_keeps_a_quad_that_collapsed_into_a_triangle():
    """Mutacje: 301 `>= 3` -> `> 3` i `3` -> `4` — trójkąt po sklejeniu wypadałby.

    Czworobok, którego dwa wierzchołki leżą w tym samym punkcie, jest trójkątem,
    a nie śmieciem. Wyrzucenie go zrobiłoby dziurę w bryle kolizyjnej i test
    zamknięcia poprzecznego zgłosiłby ją jako brzeg — ale dopiero po fakcie.
    """
    count, faces = LD.weld([(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (1.0, 1.0, 0.0), (1.0, 1.0, 0.0)],
                           [(0, 1, 2, 3)])
    assert count == 3
    assert faces == [(0, 1, 2)], faces


def test_lod_inset_accepts_a_triangle_and_rejects_a_zero_length_edge():
    """Mutacje: 199 `< 3` -> `<= 3` i `3` -> `4`, 206 `<= 0.0` -> `< 0.0`.

    Trzy punkty to najmniejszy wielobok, jaki ma wnętrze; odrzucenie go zabrałoby
    profilowi trójkątnemu bryłę kolizyjną. Krawędź zerowej długości nie ma normalnej,
    więc musi być odmową, a nie dzieleniem przez zero.
    """
    inset = LD.inset_polygon([(0.0, 0.0), (4.0, 0.0), (0.0, 4.0)], 0.1)
    assert len(inset) == 3
    assert LD.polygon_area_m2(inset) < LD.polygon_area_m2([(0.0, 0.0), (4.0, 0.0), (0.0, 4.0)])
    try:
        LD.inset_polygon([(0.0, 0.0), (0.0, 0.0), (4.0, 0.0), (0.0, 4.0)], 0.1)
    except ValueError:
        pass
    else:
        raise AssertionError("krawędź zerowej długości nie została odrzucona")


def test_lod_threshold_distance_is_inclusive():
    """Mutacja: 480 `>=` -> `>` — chunk DOKŁADNIE na progu zostawałby na poziomie niżej.

    Próg jest opisany jako „dystans, od którego wolno LOD k+1", więc równość należy
    do poziomu wyższego. Dotychczasowy test sprawdzał 250 m przy progu 200 m, czyli
    punkt, w którym obie wersje dają to samo.
    """
    assert LD.lod_for_distance(200.0, [200.0, 400.0]) == 1
    assert LD.lod_for_distance(199.999, [200.0, 400.0]) == 0
    assert LD.lod_for_distance(400.0, [200.0, 400.0]) == 2


def test_lod_manifest_thresholds_are_one_per_level_above_zero():
    """Mutacja: 487 `> 0` -> `> 1` — próg poziomu 1 wypadałby z listy.

    Wtedy `lod_plan` liczyłby poziomy z listy o jeden krótszej i chunk, który miał
    dostać LOD 1, dostawałby LOD 0 — czyli pełną siatkę w dalekim planie, po cichu
    i bez żadnego błędu. Trójka poziomów w manifeście musi dać dwa progi.
    """
    manifest = _manifest()
    thresholds = LD.manifest_thresholds(manifest)
    header = sorted(manifest["lod_levels"], key=lambda e: e["level"])
    assert thresholds == [e["switch_distance_m"] for e in header[1:]], thresholds
    assert len(thresholds) == len(header) - 1


def test_collision_plan_holds_a_chunk_exactly_at_the_radius():
    """Mutacja: 519 `<=` -> `<` — chunk dokładnie na promieniu wypadałby z listy.

    Chunk `T_c01` zaczyna się na 500 m, więc przy pociągu na 350 m jego odległość
    wynosi dokładnie 150 m, czyli tyle, ile `COLLISION_RADIUS_M`. Promień znaczy
    „w tym promieniu", więc równość jest w środku.
    """
    manifest = _manifest()
    assert LD.chunk_distance_m(manifest["chunks"][1], 350.0) == LD.COLLISION_RADIUS_M
    assert "T_c01" in LD.collision_plan(manifest, 350.0)
    assert "T_c01" not in LD.collision_plan(manifest, 349.999)


def test_lod_triangles_counts_the_level_it_was_given():
    """Mutacja: 528 `==` -> `!=` — liczyłby pierwszy poziom INNY niż zadany."""
    manifest = _manifest()
    for level in (0, 1, 2):
        plan = {chunk["id"]: level for chunk in manifest["chunks"]}
        expected = sum(next(l["triangles"] for l in chunk["lods"] if l["level"] == level)
                       for chunk in manifest["chunks"])
        assert LD.lod_triangles(manifest, plan) == expected, (level, plan)


# --- kontrola manifestu: równość jest złamaniem, a nie zapasem -----------------

def test_lod_manifest_problems_detects_two_levels_with_the_same_switch_distance():
    """Mutacja: 552 `<=` -> `<` — dwa poziomy o TYM SAMYM progu przeszłyby.

    Dwa równe progi znaczą, że pomiędzy nimi nie ma przedziału odległości i jeden
    z poziomów nigdy nie zostanie wybrany — czyli generuje się siatka, której nikt
    nigdy nie zobaczy.
    """
    manifest = _manifest()
    manifest["lod_levels"][2]["switch_distance_m"] = manifest["lod_levels"][1]["switch_distance_m"]
    problems = LD.lod_problems(manifest)
    assert any("nie jest dalszy" in p for p in problems), problems


def test_lod_manifest_problems_detects_two_levels_with_the_same_chord():
    """Mutacje: 554 `<=` -> `<` oraz `> 0` -> `> 1`.

    Równa cięciwa znaczy „nie rzadszy", a więc poziom bez powodu. Druga mutacja jest
    subtelniejsza: `previous["level"] > 1` wyłączyłaby tę kontrolę dla pary 1-2,
    czyli dla jedynej pary, w której w ogóle da się ją złamać — poziom 0 ma cięciwę
    zero i nigdy nie wchodzi w porównanie.
    """
    manifest = _manifest()
    manifest["lod_levels"][2]["max_chord_m"] = manifest["lod_levels"][1]["max_chord_m"]
    problems = LD.lod_problems(manifest)
    assert any("nie jest rzadszy" in p for p in problems), problems


def test_lod_manifest_problems_detects_a_level_with_the_same_triangle_count():
    """Mutacja: 576 `>` -> `>=` — i to ta mutacja miała rację.

    Wiadomość mówi „nie jest tańszy", a poziom o TEJ SAMEJ liczbie trójkątów tańszy
    nie jest. Kontrola kolizji obok (`>=` w wierszu 594) liczy tak samo, więc te dwa
    miejsca różniły się tylko przez przeoczenie. Operator jest teraz `>=` w obu.
    """
    manifest = _manifest()
    for chunk in manifest["chunks"]:
        chunk["lods"][2]["triangles"] = chunk["lods"][1]["triangles"]
    problems = LD.lod_problems(manifest)
    assert any("nie jest tańszy" in p for p in problems), problems


def test_lod_manifest_problems_accepts_a_level_with_the_same_deviation():
    """Mutacja: 579 `<` -> `<=` — zameldowałaby równy błąd jako mniejszy.

    Tu równość jest w porządku i to jest różnica wobec testu wyżej: warunek pyta,
    czy błąd ZMALAŁ, a nie czy nie urósł. Rzadsza siatka o tym samym błędzie jest
    dziwna, ale nie jest sprzecznością, a kontrola ma meldować sprzeczności.
    """
    manifest = _manifest()
    for chunk in manifest["chunks"]:
        chunk["lods"][2]["max_deviation_m"] = chunk["lods"][1]["max_deviation_m"]
    problems = LD.lod_problems(manifest)
    assert not any("mniejszy błąd" in p for p in problems), problems


def test_lod_manifest_problems_detects_geometry_that_is_exactly_empty():
    """Mutacje: 583 `<= 0` -> `< 0` (dwie) i `0` -> `1` (dwie).

    Zero trójkątów albo zero wierzchołków to pusty plik, a nie mała siatka. Mutacja
    w drugą stronę (`<= 1`) zgłaszałaby jako pustą siatkę o jednym trójkącie, która
    pusta nie jest — dlatego test sprawdza obie strony granicy.
    """
    for field in ("triangles", "vertices"):
        manifest = _manifest()
        manifest["chunks"][0]["lods"][2][field] = 0
        problems = LD.lod_problems(manifest)
        assert any("pustą geometrię" in p for p in problems), (field, problems)

    manifest = _manifest()
    for chunk in manifest["chunks"]:
        chunk["lods"][2]["triangles"] = 1
        chunk["lods"][2]["vertices"] = 1
    assert not any("pustą geometrię" in p for p in LD.lod_problems(manifest))


def test_lod_manifest_problems_detects_a_collision_as_heavy_as_the_visual_mesh():
    """Mutacja: 594 `>=` -> `>` — kolizja o TEJ SAMEJ liczbie trójkątów przeszłaby.

    Bryła kolizyjna, która nie jest tańsza od siatki wizualnej, nie ma powodu istnieć:
    jest osobnym plikiem i osobną rezydencją właśnie po to, żeby była tańsza.
    """
    manifest = _manifest()
    for chunk in manifest["chunks"]:
        chunk["collision"]["triangles"] = chunk["lods"][0]["triangles"]
    problems = LD.lod_problems(manifest)
    assert any("nie jest tańsza" in p for p in problems), problems


def test_lod_manifest_problems_treats_a_collision_touching_the_wall_as_still_inside():
    """Mutacje: 598 `< 0.0` -> `<= 0.0` i `0.0` -> `0.001`.

    Zapas zero znaczy „dotyka światła tunelu", a nie „wystaje w mur" — pytanie brzmi,
    czy bryła WYSTAJE, i odpowiedź na styk jest przecząca. Granica jest przeciwna niż
    przy skrajni niżej i ta różnica jest zamierzona: tam zero znaczy, że pociąg dotyka
    bryły, czyli jednak w nią wchodzi.
    """
    manifest = _manifest()
    for chunk in manifest["chunks"]:
        chunk["collision"]["wall_margin_m"] = 0.0
    assert not any("wystaje poza światło" in p for p in LD.lod_problems(manifest))

    for chunk in manifest["chunks"]:
        chunk["collision"]["wall_margin_m"] = -1e-9
    assert any("wystaje poza światło" in p for p in LD.lod_problems(manifest))


def test_lod_manifest_problems_detects_a_gauge_margin_of_exactly_zero():
    """Mutacje: 601 `<= 0.0` -> `< 0.0` i `0.0` -> `0.001`.

    Zapas zero znaczy, że skrajnia M7 dotyka bryły kolizyjnej — czyli pociąg ociera
    o kolizję. To jest złamanie, nie granica dopuszczalna.
    """
    manifest = _manifest()
    for chunk in manifest["chunks"]:
        chunk["collision"]["gauge_margin_m"] = 0.0
    problems = LD.lod_problems(manifest)
    assert any("nie mieści skrajni" in p for p in problems), problems


def test_lod_manifest_problems_detects_a_collision_volume_of_exactly_zero():
    """Mutacje: 603 `<= 0.0` -> `< 0.0` i `0.0` -> `0.001`."""
    manifest = _manifest()
    for chunk in manifest["chunks"]:
        chunk["collision"]["volume_m3"] = 0.0
    problems = LD.lod_problems(manifest)
    assert any("objętość" in p for p in problems), problems


def test_lod_manifest_problems_accepts_a_seam_shift_exactly_at_the_tolerance():
    """Mutacje: 585, 595, 605 i 615 `>` -> `>=`.

    Tolerancja znaczy „do tyle wolno", więc przesunięcie RÓWNE tolerancji jeszcze
    mieści się w normie, a większe już nie.

    **Tolerancja jest potęgą dwójki i to nie jest ozdobnik.** Pierwsza wersja tego
    testu brała `1e-6` i przesuwała szew o `+1e-6`. Dla początku chunka (0,0 m) różnica
    wychodziła dokładnie `1e-6` i mutacja ginęła, ale dla końca (1000,0 m) wychodziło
    `9,999999974752427e-07`, czyli MNIEJ niż tolerancja — równość nigdy nie zachodziła
    i obie wersje warunku dawały to samo. Test wyglądał na kontrolę granicy, a granicy
    nie dotykał: dwie z czterech mutacji przeżywały. `2**-20` jest reprezentowalne
    dokładnie przy każdej z tych podstaw, więc równość jest równością.

    Założenie jest tu sprawdzane wprost, a nie zakładane — inaczej ta sama pułapka
    wróci przy pierwszej zmianie liczb w `_manifest`.
    """
    tolerance = 2.0 ** -20
    for owner, field in (("lods", "start_m"), ("lods", "end_m"),
                         ("collision", "start_m"), ("collision", "end_m")):
        manifest = _manifest()
        for chunk in manifest["chunks"]:
            target = chunk[owner][2] if owner == "lods" else chunk[owner]
            target[field] = chunk[field] + tolerance
            assert abs(target[field] - chunk[field]) == tolerance, \
                (owner, field, target[field], chunk[field])
        assert not any("zakres chainage" in p for p in LD.lod_problems(manifest, tolerance)), \
            (owner, field)

        manifest = _manifest()
        for chunk in manifest["chunks"]:
            target = chunk[owner][2] if owner == "lods" else chunk[owner]
            target[field] = chunk[field] + tolerance * 2.0
        assert any("zakres chainage" in p for p in LD.lod_problems(manifest, tolerance)), \
            (owner, field)


def test_lod_chunk_distance_is_zero_on_both_ends_and_never_negative():
    """Mutacja: 471 pierwszy `<=` -> `<` — pociąg DOKŁADNIE na początku chunka.

    Zmierzone na mutancie: chunk [500, 1000] przy pociągu na 500 m daje **-500,0 m**,
    bo strażnik przestaje łapać i ścieżka zapasowa wybiera gałąź `value - end`.
    Dzisiaj nikt tego nie zauważa — ujemna odległość i tak wypada na poziom 0 i i tak
    mieści się w promieniu kolizji — ale odległość ujemna jest liczbą bez znaczenia
    i pierwszy konsument, który ją posortuje albo podniesie do kwadratu, dostanie
    wynik nie do wytłumaczenia.

    Dlatego test pyta o obie rzeczy naraz: zero na obu krańcach i BRAK wartości
    ujemnej gdziekolwiek. Sam warunek „zero na krańcu" zabija tylko jedną z dwóch
    mutacji tego wiersza.
    """
    chunk = {"start_m": 500.0, "end_m": 1000.0}
    assert LD.chunk_distance_m(chunk, 500.0) == 0.0
    assert LD.chunk_distance_m(chunk, 1000.0) == 0.0
    assert LD.chunk_distance_m(chunk, 750.0) == 0.0
    assert LD.chunk_distance_m(chunk, 250.0) == 250.0
    assert LD.chunk_distance_m(chunk, 1200.0) == 200.0

    chainage = 0.0
    while chainage <= 1500.0:
        assert LD.chunk_distance_m(chunk, chainage) >= 0.0, chainage
        chainage += 0.5


def test_lod_a_span_that_fits_the_limit_keeps_exactly_the_two_ends():
    """Mutacja: 134 `while candidate <= last` -> `< last`.

    Ostatni pierścień przestaje być kandydatem, więc pętla stawia przedostatni,
    a `keep[-1] != last` dokłada ostatni z powrotem — i zostaje pierścień, którego
    nikt nie potrzebował. Zmierzone na łuku 91,5 m: `[..., 56, 59, 60]` zamiast
    `[..., 56, 60]`; na prostej `[0, 3, 4]` zamiast `[0, 4]`.

    Nadmiarowy pierścień jest cichy: siatka jest poprawna, szew się zgadza, tylko
    LOD oszczędza mniej, niż deklaruje manifest. Test bierze przypadek skrajny —
    cały odcinek mieści się w limicie — bo tam nadmiar to 50 % pierścieni.
    """
    station_m = [0.0, 5.0, 10.0, 15.0, 20.0]
    positions = [(x, 0.0, 0.0) for x in station_m]
    assert LD.select_rings(positions, station_m, 0, 4, 25.0, 0.0) == [0, 4]
