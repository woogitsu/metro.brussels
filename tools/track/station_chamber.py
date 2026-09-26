"""Project station chamber cross sections and access openings along the route.

The platform positions come from station_layout, not from a guessed station plan.
This module has no Blender dependency so the transition can be checked numerically.
"""

import station_components as SC


# Project length of the flare outside each platform. It changes only the visual
# tunnel chamber, not the source axis or the recorded stopping positions.
CHAMBER_FLARE_M = 8.0
MEZZANINE_FLARE_M = 16.0


def expanded_tunnel_profile(points):
    """Insert wall vertices matching the access opening band in the chamber."""
    if len(points) != 6:
        raise ValueError("station transition requires the six-point box profile")
    left_floor, right_floor, right_shoulder, right_roof, left_roof, left_shoulder = points
    def wall_point(floor, shoulder, fraction):
        return (floor[0] + fraction * (shoulder[0] - floor[0]),
                floor[1] + fraction * (shoulder[1] - floor[1]))
    return [left_floor, right_floor,
            wall_point(right_floor, right_shoulder, 0.60),
            wall_point(right_floor, right_shoulder, 0.90), right_shoulder,
            right_roof, left_roof, left_shoulder,
            wall_point(left_shoulder, left_floor, 0.10),
            wall_point(left_shoulder, left_floor, 0.40)]


def chamber_profile(station_points, platform_height_m):
    """One open-height chamber containing the canonical mezzanine and its slab."""
    wall_m = max(abs(y) for y, _z in station_points)
    floor_m = min(z for _y, z in station_points)
    chamber_ceiling_m = max(z for _y, z in station_points)
    level = SC.levels(platform_height_m, chamber_ceiling_m)
    top_m = level["mezzanine_ceiling_m"] + SC.DESIGN_SLAB_THICKNESS_M
    band_low = level["mezzanine_floor_m"]
    band_high = band_low + SC.DESIGN_CORRIDOR_CLEAR_M
    shoulder_m = top_m - SC.DESIGN_ACCESS_SHELL_M
    roof_side_m = wall_m - SC.DESIGN_ACCESS_SHELL_M
    return [(-wall_m, floor_m), (wall_m, floor_m),
            (wall_m, band_low), (wall_m, band_high), (wall_m, shoulder_m),
            (roof_side_m, top_m), (-roof_side_m, top_m), (-wall_m, shoulder_m),
            (-wall_m, band_high), (-wall_m, band_low)]


def low_chamber_profile(station_points):
    """Keep the documented 5.30 m station roof outside the access mezzanine."""
    return expanded_tunnel_profile(station_points)


def _ease(value):
    """Cubic taper with a level tangent at both ends of a transition."""
    return value * value * (3.0 - 2.0 * value)


def transition_anchors(platforms, existing_chainages=(), min_spacing_m=0.5):
    """Sample both curved flares densely enough for the swept mesh and its LODs."""
    anchors = set()
    optional = set()
    for platform in platforms:
        start, end = platform["from_m"], platform["to_m"]
        for edge, direction, length in ((start, -1, CHAMBER_FLARE_M),
                                        (end, 1, CHAMBER_FLARE_M)):
            for quarter in range(5):
                (anchors if quarter in (0, 4) else optional).add(
                    edge + direction * length * quarter / 4.0)
        if platform["length_m"] < SC.DESIGN_MEZZANINE_LENGTH_M + SC.DESIGN_ACCESS_SETBACK_M:
            continue
        mezz_end = end - SC.DESIGN_ACCESS_SETBACK_M
        mezz_start = mezz_end - SC.DESIGN_MEZZANINE_LENGTH_M
        for edge, direction in ((mezz_start, -1), (mezz_end, 1)):
            for quarter in range(5):
                (anchors if quarter in (0, 4) else optional).add(
                    edge + direction * MEZZANINE_FLARE_M * quarter / 4.0)
    for value in sorted(optional):
        if all(abs(value - existing) >= min_spacing_m for existing in existing_chainages):
            anchors.add(value)
    return sorted(anchors)


def transition_weight(chainage_m, platforms, flare_m=CHAMBER_FLARE_M):
    """0 in the ordinary tunnel and 1 throughout each platform."""
    if flare_m <= 0:
        raise ValueError("flare must be positive")
    weight = 0.0
    for platform in platforms:
        start, end = platform["from_m"], platform["to_m"]
        if start <= chainage_m <= end:
            return 1.0
        if start - flare_m < chainage_m < start:
            weight = max(weight, _ease((chainage_m - start + flare_m) / flare_m))
        if end < chainage_m < end + flare_m:
            weight = max(weight, _ease((end + flare_m - chainage_m) / flare_m))
    return weight


def mezzanine_weight(chainage_m, platforms, flare_m=MEZZANINE_FLARE_M):
    """Raise the roof only over the canonical mezzanine at the far platform end."""
    if flare_m <= 0:
        raise ValueError("mezzanine flare must be positive")
    weight = 0.0
    for platform in platforms:
        if platform["length_m"] < SC.DESIGN_MEZZANINE_LENGTH_M + SC.DESIGN_ACCESS_SETBACK_M:
            continue
        end = platform["to_m"] - SC.DESIGN_ACCESS_SETBACK_M
        start = end - SC.DESIGN_MEZZANINE_LENGTH_M
        if start <= chainage_m <= end:
            return 1.0
        if start - flare_m < chainage_m < start:
            weight = max(weight, _ease((chainage_m - start + flare_m) / flare_m))
        if end < chainage_m < end + flare_m:
            weight = max(weight, _ease((end + flare_m - chainage_m) / flare_m))
    return weight


def profile_at(chainage_m, tunnel, chamber, platforms, low_chamber=None):
    low_chamber = chamber if low_chamber is None else low_chamber
    if len(tunnel) != len(chamber) or len(tunnel) != len(low_chamber):
        raise ValueError("transition profiles need matching vertex counts")
    width_weight = transition_weight(chainage_m, platforms)
    height_weight = mezzanine_weight(chainage_m, platforms)
    low = [(a[0] + width_weight * (b[0] - a[0]),
            a[1] + width_weight * (b[1] - a[1])) for a, b in zip(tunnel, low_chamber)]
    # The roof flare may overlap the width flare beyond a platform. Interpolating
    # toward the full-width high chamber there would push roof corners past the
    # narrowing wall and fold faces inside out. Lift the current-width profile
    # instead; the small roof inset scales with its available width.
    return [(a[0] + height_weight * width_weight * (b[0] - base[0]),
             a[1] + height_weight * (b[1] - base[1]))
            for a, b, base in zip(low, chamber, low_chamber)]


def access_windows(platforms, station_points, platform_height_m, side=1):
    """Exactly the corridor openings emitted by station_components for full platforms."""
    wall_m = max(abs(y) for y, _z in station_points)
    level = SC.levels(platform_height_m, max(z for _y, z in station_points))
    windows = []
    for platform in platforms:
        if platform["length_m"] < SC.DESIGN_MEZZANINE_LENGTH_M + SC.DESIGN_ACCESS_SETBACK_M:
            continue
        for solid in SC.access_solids(platform, side, level, wall_m):
            if solid["name"] == "corridor_floor_corridor":
                start = solid["at_m"]
                windows.append((start, start + solid["length_m"], side))
    return windows


def is_open_face(start_m, end_m, column, windows):
    """Remove only the side-wall band at a corridor, never the surrounding wall."""
    for first, last, side in windows:
        wall_column = 2 if side > 0 else 8
        if column == wall_column and first <= start_m and end_m <= last:
            return True
    return False
