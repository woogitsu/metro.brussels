#!/usr/bin/env python3
"""Project chamber transitions, openings, LOD and collision in real metre units."""

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "track"))
sys.path.insert(0, os.path.join(ROOT, "tools", "blender"))

import lod as LD  # noqa: E402
import profiles as PR  # noqa: E402
import station_chamber as CH  # noqa: E402
import sweep as SW  # noqa: E402


PLATFORM = {"from_m": 100.0, "to_m": 195.0, "length_m": 95.0}
TUNNEL = CH.expanded_tunnel_profile(PR.profile_points("box_double"))
STATION = PR.profile_points("station")
CHAMBER = CH.chamber_profile(STATION, 1.03)
LOW_CHAMBER = CH.low_chamber_profile(STATION)


def test_chamber_uses_platform_limits_and_tapers_continuously():
    assert CH.transition_weight(92.0, [PLATFORM]) == 0.0, "flare starts before the platform"
    assert CH.transition_weight(100.0, [PLATFORM]) == 1.0, "full chamber at platform start"
    assert CH.transition_weight(195.0, [PLATFORM]) == 1.0, "full chamber at platform end"
    assert CH.transition_weight(203.0, [PLATFORM]) == 0.0, "flare ends after the platform"
    midpoint = CH.profile_at(96.0, TUNNEL, CHAMBER, [PLATFORM], LOW_CHAMBER)
    assert abs(midpoint[1][0] - 6.15) < 1e-9, "halfway flare interpolates wall position"
    assert CH.profile_at(100.0, TUNNEL, CHAMBER, [PLATFORM], LOW_CHAMBER) == LOW_CHAMBER, "platform has the documented low roof"
    assert CH.profile_at(180.0, TUNNEL, CHAMBER, [PLATFORM], LOW_CHAMBER) == CHAMBER, "only access mezzanine raises the roof"
    for boundary in (151.0, 167.0, 191.0, 207.0):
        before = CH.profile_at(boundary - 0.001, TUNNEL, CHAMBER, [PLATFORM], LOW_CHAMBER)
        after = CH.profile_at(boundary + 0.001, TUNNEL, CHAMBER, [PLATFORM], LOW_CHAMBER)
        assert max(abs(a[1] - b[1]) for a, b in zip(before, after)) < 0.01, "roof transition remains continuous"


def test_chamber_band_matches_corridor_and_window_only_opens_its_wall():
    windows = CH.access_windows([PLATFORM], STATION, 1.03)
    assert len(windows) == 1, "one canonical corridor per full platform"
    first, last, side = windows[0]
    assert side == 1 and abs(last - first - 3.0) < 1e-9, "opening matches corridor width"
    assert CHAMBER[2][1] == 5.7 and CHAMBER[3][1] == 8.1, "band matches corridor clear height"
    assert CH.is_open_face(first, last, 2, windows), "right wall opens at the corridor"
    assert not CH.is_open_face(first, last, 1, windows), "lower wall stays closed"
    assert not CH.is_open_face(first - 1.0, first, 2, windows), "wall before corridor stays closed"
    assert not CH.is_open_face(last, last + 1.0, 2, windows), "wall after corridor stays closed"


def test_chamber_mesh_lod_and_train_collision_keep_safe_sections():
    points = [(float(x), 0.0, 0.0) for x in range(0, 301, 2)]
    windows = CH.access_windows([PLATFORM], STATION, 1.03)
    anchors = [92.0, 100.0, 195.0, 203.0] + [v for w in windows for v in w[:2]]
    def profile_at(value):
        return CH.profile_at(value, TUNNEL, CHAMBER, [PLATFORM], LOW_CHAMBER)
    def open_face(low, high, column):
        return CH.is_open_face(low, high, column, windows)
    result = SW.sweep(points, TUNNEL, ring_step=0, station_chainages=[147.5],
                      max_chunk_m=500, profile_at_m=profile_at, open_face=open_face,
                      anchor_chainages=anchors)
    chunk = result["chunks"][0]
    ring_m = result["station_m"]
    rings = result["profiles_by_ring"]
    required = [i for i, v in enumerate(ring_m)
                if CH.transition_weight(v, [PLATFORM]) > 0.0
                or CH.mezzanine_weight(v, [PLATFORM]) > 0.0]
    required += [SW._nearest_ring(ring_m, value) for value in anchors]
    required = sorted({neighbor for index in required
                       for neighbor in (index - 1, index, index + 1)
                       if 0 <= neighbor < len(ring_m)})
    def open_indices(low, high, column):
        return open_face(ring_m[low], ring_m[high], column)
    lods = [LD.lod_chunk(result["frames"], ring_m, TUNNEL, chunk["first_ring"],
                         chunk["last_ring"], level, profiles_by_ring=rings,
                         face_open=open_indices, required_rings=required)
            for level in (1, 2)]
    collision = LD.collision_solid(result["frames"], ring_m, TUNNEL,
                                   chunk["first_ring"], chunk["last_ring"],
                                   profiles_by_ring=rings, required_rings=required)
    assert len(chunk["faces"]) < (len(ring_m) - 1) * len(TUNNEL), "window removes faces"
    for lod in lods:
        assert len(lod["faces"]) < (len(lod["ring_indices"]) - 1) * len(TUNNEL), "both LODs keep opening"
        assert LD.deviation_stats(result["frames"], TUNNEL, ring_m, 0, len(ring_m) - 1,
                                  lod["ring_indices"], rings)["max_m"] < 0.4, "LOD tracks both roof flares"
    closed, _actual, _expected = LD.transversally_closed(collision, len(TUNNEL) + 1)
    assert closed, "train collision remains a closed cross section"
    assert LD.wall_margin_m(result["frames"], TUNNEL, collision["profile"], ring_m,
                            0, len(ring_m) - 1, collision["ring_indices"], rings,
                            collision["profiles_by_ring"]) >= 0.0, "collision stays inside variable roof"
    assert LD.gauge_margin_m(collision["profile"], PR.vehicle_gauge(),
                             PR.PROFILES["box_double"]["track_offsets"]) > 0.0, "M7 fits"


if __name__ == "__main__":
    import test_all

    raise SystemExit(test_all.main(__file__))
