"""Build neutral, readable track furniture for the playable tunnel.

The geometry is deliberately separate from the measured tunnel chunks. It is a
design preview, not a claim about STIB rail, sleeper or luminaire dimensions.
Each GLB has the same world coordinates and chunk id as tunnel_sweep.py.
"""
import argparse
import bisect
import json
import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(__file__))
import sweep as SW
from profiles import PROFILES, profile_points
from tunnel_sweep import load_centerline


def arguments():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--centerline", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--design-preview", action="store_true",
                        help="add visible conceptual alignment markers to the design preview only")
    return parser.parse_args(args)


def frame_at(frames, chainages, value):
    index = max(0, min(len(chainages) - 2, bisect.bisect_right(chainages, value) - 1))
    amount = (value - chainages[index]) / (chainages[index + 1] - chainages[index])
    a, b = frames[index], frames[index + 1]
    lerp = lambda x, y: tuple(x[i] * (1 - amount) + y[i] * amount for i in range(3))
    # A linear position interpolation leaves the track on the 5 m chords of
    # the tunnel axis, even when extra rail rings are added between them. Use
    # the axis tangents as Hermite derivatives: the track still meets every
    # measured frame and both sides of a chunk seam exactly.
    span = chainages[index + 1] - chainages[index]
    t = amount
    h00, h10 = 2*t**3 - 3*t**2 + 1, t**3 - 2*t**2 + t
    h01, h11 = -2*t**3 + 3*t**2, t**3 - t**2
    position = tuple(h00*a[0][i] + h10*span*a[1][i]
                     + h01*b[0][i] + h11*span*b[1][i] for i in range(3))
    derivative = tuple((6*t*t - 6*t)*a[0][i]
                       + (3*t*t - 4*t + 1)*span*a[1][i]
                       + (-6*t*t + 6*t)*b[0][i]
                       + (3*t*t - 2*t)*span*b[1][i] for i in range(3))
    forward = SW.unit(derivative)
    # Preserve the transported frame used by the tunnel sweep. World-up would
    # detach furniture on any future graded or banked alignment.
    carried_right = lerp(a[2], b[2])
    right = SW.unit(SW.sub(carried_right, SW.scale(forward, SW.dot(carried_right, forward))))
    up = SW.unit(SW.cross(right, forward))
    return position, forward, right, up


class Solids:
    def __init__(self):
        self.vertices = []
        self.faces = []

    def box(self, frame, lateral, height, length, width, depth):
        centre, forward, right, up = frame
        centre = SW.add(centre, SW.add(SW.scale(right, lateral), SW.scale(up, height)))
        half = (length / 2, width / 2, depth / 2)
        start = len(self.vertices)
        for x, y, z in ((-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),
                        (-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)):
            self.vertices.append(SW.add(centre, SW.add(
                SW.scale(forward, x * half[0]), SW.add(
                    SW.scale(right, y * half[1]), SW.scale(up, z * half[2])))))
        self.faces.extend(tuple(start + i for i in face) for face in (
            (0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)))

    def wall_plate(self, frame, lateral, height, length, plate_height):
        """A thin, double-sided quad on the tunnel wall, not a light source."""
        centre, forward, right, up = frame
        centre = SW.add(centre, SW.add(SW.scale(right, lateral), SW.scale(up, height)))
        start = len(self.vertices)
        for along, vertical in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            self.vertices.append(SW.add(centre, SW.add(
                SW.scale(forward, along * length / 2),
                SW.scale(up, vertical * plate_height / 2))))
        self.faces.append((start, start + 1, start + 2, start + 3))

    def swept_prism(self, frames, chainages, samples, lateral, height, width, depth):
        """One connected rectangular prism; only the two ends need caps."""
        first = len(self.vertices)
        for at in samples:
            centre, _, right, up = frame_at(frames, chainages, at)
            centre = SW.add(centre, SW.add(SW.scale(right, lateral),
                                          SW.scale(up, height)))
            for side, vertical in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                self.vertices.append(SW.add(centre, SW.add(
                    SW.scale(right, side * width / 2),
                    SW.scale(up, vertical * depth / 2))))
        self.faces.extend(((first, first + 1, first + 2),
                           (first, first + 2, first + 3)))
        for ring in range(len(samples) - 1):
            base = first + ring * 4
            following = base + 4
            for side in range(4):
                a, b = base + side, base + (side + 1) % 4
                c, d = following + side, following + (side + 1) % 4
                self.faces.extend(((a, c, d), (a, d, b)))
        last = first + 4 * (len(samples) - 1)
        self.faces.extend(((last, last + 2, last + 1),
                           (last, last + 3, last + 2)))


def material(name, color, metallic=0.0, emission=0.0):
    mat = bpy.data.materials.new(name)
    if name in ("curve_cue", "preview_marker"):
        mat.use_backface_culling = False
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    node = mat.node_tree.nodes.get("Principled BSDF")
    node.inputs["Base Color"].default_value = (*color, 1)
    node.inputs["Metallic"].default_value = metallic
    node.inputs["Roughness"].default_value = 0.72 if metallic == 0 else 0.35
    if emission:
        node.inputs["Emission Color"].default_value = (*color, 1)
        node.inputs["Emission Strength"].default_value = emission
    return mat


MATERIALS = {
    "ballast": ((0.16, 0.18, 0.19), 0, 0),
    "sleepers": ((0.10, 0.12, 0.13), 0, 0),
    # A strongly metallic rail loses its unlit side in the Godot tunnel. Keep
    # enough metal response to distinguish it from the dark sleepers.
    "rails": ((0.57, 0.61, 0.62), 0.55, 0),
    "wall": ((0.22, 0.29, 0.32), 0, 0),
    "lamp": ((0.58, 0.49, 0.37), 0, 0.60),
    "curve_cue": ((0.55, 0.61, 0.62), 0, 0.60),
    "station_panel": ((0.16, 0.18, 0.19), 0, 0),
}

# A separate warm accent makes the unsurveyed continuation readable from the
# stationary cab. It is visual annotation, not infrastructure or a signal.
PREVIEW_MATERIAL = {"preview_marker": ((0.90, 0.48, 0.11), 0, 1.10)}


def mesh_object(name, solids, mat, smooth=False):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(solids.vertices, [], solids.faces)
    mesh.update()
    if smooth:
        for face in mesh.polygons:
            face.use_smooth = True
        # Smooth the lengthwise bends, but keep the rectangular rail head and
        # ballast shoulders crisp rather than rounding their cross-sections.
        mesh.set_sharp_from_angle(angle=math.radians(35))
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat)
    return obj


def positions(start, end, pitch):
    first = math.ceil((start + 0.001) / pitch)
    last = math.floor((end - 0.001) / pitch)
    return (index * pitch for index in range(first, last + 1))


def outside_of_curve(frames, chainages, at):
    """Return the outer wall on a pronounced 16 m bend; omit near-straights."""
    before = frame_at(frames, chainages, max(chainages[0], at - 8.0))[1]
    after = frame_at(frames, chainages, min(chainages[-1], at + 8.0))[1]
    up = frame_at(frames, chainages, at)[3]
    signed_turn = math.atan2(SW.dot(SW.cross(before, after), up),
                             SW.dot(before, after))
    if abs(signed_turn) < 0.025:
        return 0
    return 1 if signed_turn > 0 else -1


def sweep_samples(frames, chainages, start, end):
    """Use shorter rings on bends while sharing every cross-section along a chunk."""
    samples = [start]
    at = start
    while at < end - 0.001:
        forward = frame_at(frames, chainages, at)[1]
        ahead = frame_at(frames, chainages, min(end, at + 4.0))[1]
        turn = math.acos(max(-1.0, min(1.0, SW.dot(forward, ahead))))
        step = 1.0 if turn > 0.01 else 2.0 if turn > 0.004 else 4.0 if turn > 0.0015 else 6.0
        at = min(end, at + step)
        samples.append(at)
    return samples


def make_chunk(entry, frames, chainages, stations, out_dir, mats,
               design_preview=False):
    start, end = entry["start_m"], entry["end_m"]
    solids = {name: Solids() for name in mats}
    offsets = PROFILES["box_double"]["track_offsets"]
    # One connected mesh per bed and rail; cap only the ends of each chunk.
    samples = sweep_samples(frames, chainages, start, end)
    for offset in offsets:
        solids["ballast"].swept_prism(frames, chainages, samples, offset,
                                       -0.75, 2.75, 0.90)
        for rail in (-0.72, 0.72):
            solids["rails"].swept_prism(frames, chainages, samples,
                                        offset + rail, -0.075, 0.09, 0.15)
    for at in positions(start, end, 1.5):
        frame = frame_at(frames, chainages, at)
        for offset in offsets:
            solids["sleepers"].box(frame, offset, -0.225, 0.26, 2.35, 0.15)
    # Side-wall bays and warm light strips supply near-field parallax in cab view.
    for at in positions(start, end, 16.0):
        frame = frame_at(frames, chainages, at)
        for side in (-1, 1):
            solids["wall"].box(frame, side * 4.61, 2.18, 0.30, 0.12, 3.9)
            solids["lamp"].box(frame, side * 4.48, 3.35, 1.8, 0.14, 0.08)
        # One shallow neutral panel between wall posts within each 95 m
        # platform. It gives the otherwise blank station wall a readable bay
        # rhythm without adding lights or projecting into the train envelope.
        panel_at = at + 8.0
        if panel_at + 3.6 < end and any(
            abs(panel_at - station) <= 43.5 for station in stations
        ):
            panel_frame = frame_at(frames, chainages, panel_at)
            for side in (-1, 1):
                solids["station_panel"].box(panel_frame, side * 4.56, 1.40,
                                             7.2, 0.04, 0.38)
    # Low-emission plates mark only the OUTER wall of bends. Their
    # eight-metre rhythm reveals where the track continues without any new
    # dynamic lights or operator branding. The 4.63 m lateral offset sits just
    # inside the 4.70 m tunnel wall, clear of the rail and train envelope.
    for at in positions(start, end, 8.0):
        side = outside_of_curve(frames, chainages, at)
        if side:
            solids["curve_cue"].wall_plate(frame_at(frames, chainages, at),
                                           side * 4.63, 2.0, 0.22, 1.0)
    if design_preview:
        # Paired narrow plates sit ahead of the Merode stop, away from the
        # train envelope. A 12 m rhythm gives the projected bend depth cues.
        for at in positions(start, end, 12.0):
            frame = frame_at(frames, chainages, at)
            for side in (-1, 1):
                solids["preview_marker"].wall_plate(frame, side * 4.62,
                                                     1.95, 0.35, 2.20)
    objects = [mesh_object(entry["id"] + "_" + name, solids[name], mats[name],
                           smooth=name in ("ballast", "rails"))
               for name in mats if solids[name].faces]
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    path = os.path.join(out_dir, entry["id"] + "_detail.glb")
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True)
    for obj in objects:
        bpy.data.objects.remove(obj, do_unlink=True)
    return path


def main():
    args = arguments()
    with open(args.manifest, encoding="utf-8") as handle:
        manifest = json.load(handle)
    if manifest["profile"] != "box_double":
        raise SystemExit("track detail currently supports box_double only")
    points, stations, _, _ = load_centerline(args.centerline)
    result = SW.sweep(points, profile_points("box_double"),
                      station_chainages=[s["chainage_m"] for s in stations])
    chunks = result["chunks"]
    entries = manifest["chunks"]
    if len(chunks) != len(entries) or any(
        abs(a["start_m"] - b["start_m"]) > 0.01 or
        abs(a["end_m"] - b["end_m"]) > 0.01
        for a, b in zip(chunks, entries)
    ):
        raise SystemExit("detail chunks do not match the tunnel manifest")
    os.makedirs(args.out_dir, exist_ok=True)
    specs = MATERIALS | (PREVIEW_MATERIAL if args.design_preview else {})
    mats = {name: material(name, *spec) for name, spec in specs.items()}
    for entry in entries:
        print("[DETAIL]", make_chunk(entry, result["frames"], result["station_m"],
                                     [s["chainage_m"] for s in stations],
                                     args.out_dir, mats, args.design_preview), flush=True)


if __name__ == "__main__":
    main()
