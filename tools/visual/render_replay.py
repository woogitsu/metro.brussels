"""Render a replay at an exact resolution without editing the game project.

Godot's movie writer uses the project's viewport dimensions (not necessarily
--resolution). This tool changes those dimensions only in a temporary checkout.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import tempfile
from pathlib import Path


def set_viewport(project: str, width: int, height: int) -> str:
    for key, value in (("viewport_width", width), ("viewport_height", height)):
        pattern = rf"(?m)^(window/size/{key}=)\d+$"
        project, count = re.subn(pattern, rf"\g<1>{value}", project)
        if count != 1:
            raise ValueError(f"Expected one window/size/{key} setting, found {count}")
    return project


def png_size(path: Path) -> tuple[int, int]:
    with path.open("rb") as image:
        header = image.read(24)
    if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        raise ValueError(f"Invalid PNG: {path}")
    return int.from_bytes(header[16:20], "big"), int.from_bytes(header[20:24], "big")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--godot", required=True, type=Path)
    parser.add_argument("--assets", required=True, type=Path)
    parser.add_argument("--replay", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path, help="PNG movie base path")
    parser.add_argument("--resolution", required=True, help="WIDTHxHEIGHT")
    parser.add_argument("--steps-per-frame", type=int, default=120)
    parser.add_argument("--source-root", type=Path, default=Path(__file__).resolve().parents[2],
                        help="Repository checkout to render (default: this script's repository)")
    parser.add_argument("--line", action="store_true", help="Replay a line session instead of a single train")
    parser.add_argument("--limit-kmh", type=float, default=72.0, help="Required line speed limit")
    args = parser.parse_args()
    match = re.fullmatch(r"([1-9]\d*)x([1-9]\d*)", args.resolution)
    if match is None:
        parser.error("--resolution must be WIDTHxHEIGHT")
    width, height = map(int, match.groups())
    root = args.source_root.resolve()
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    if list(output.parent.glob(f"{output.stem}[0-9]*.png")):
        parser.error("output already contains matching movie frames; choose a new base path")
    with tempfile.TemporaryDirectory(prefix="metro-movie-") as temporary:
        temporary_root = Path(temporary)
        for folder in ("src/Game", "src/Sim", "data"):
            shutil.copytree(root / folder, temporary_root / folder,
                            ignore=shutil.ignore_patterns("bin", "obj", ".godot"))
        project = temporary_root / "src/Game/project.godot"
        project.write_text(set_viewport(project.read_text(encoding="utf-8"), width, height), encoding="utf-8")
        subprocess.run(["dotnet", "build", str(temporary_root / "src/Game/MetroBxl.Game.csproj"), "--nologo", "-v:q"], check=True)
        subprocess.run([str(args.godot.resolve()), "--headless", "--editor", "--path", str(temporary_root / "src/Game"), "--import"], check=True)
        game_args = [f"--replay={args.replay.resolve()}", f"--assets={args.assets.resolve()}",
                     f"--steps-per-frame={args.steps_per_frame}"]
        if args.line:
            game_args.extend(("--line", f"--limit-kmh={args.limit_kmh}",
                              f"--signalling={temporary_root / 'data/design/signalling/classic-2026.json'}"))
        subprocess.run([str(args.godot.resolve()), "--path", str(temporary_root / "src/Game"),
                        "--fixed-fps", "30", "--write-movie", str(output), "--",
                        *game_args], cwd=temporary_root, check=True)
    frames = sorted(output.parent.glob(f"{output.stem}[0-9]*.png"))
    if not frames:
        raise RuntimeError("Godot did not write any movie frames")
    for frame in frames:
        if png_size(frame) != (width, height):
            raise RuntimeError(f"Wrong frame resolution: {frame}: {png_size(frame)}")
    print(f"{len(frames)} frames at {width}x{height}: {frames[0]} ... {frames[-1]}")


if __name__ == "__main__":
    main()
