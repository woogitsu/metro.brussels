"""Build a short reviewed GIF from consecutive Godot movie frames.

Requires Pillow 12.3.0. Raw 1835-frame movie stays in build/, outside Git.
"""

import argparse
import hashlib
import json
from pathlib import Path
import shutil

START = 1720
END = 1825
KEYFRAMES = (1720, 1790, 1820)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("frames_dir", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    from PIL import Image  # Optional only when building the GIF; CI can import this tool.

    frames = []
    for number in range(START, END + 1):
        source = args.frames_dir / f"arrival{number:08d}.png"
        with Image.open(source) as image:
            if image.size != (1280, 720):
                raise ValueError(f"Unexpected frame size: {source}: {image.size}")
            if number in KEYFRAMES:
                image.save(args.output_dir / f"frame-{number}.png")
            frames.append(image.convert("RGB").resize((960, 540)).quantize(colors=96))

    movie = args.output_dir / "parc-arrival.gif"
    frames[0].save(
        movie, save_all=True, append_images=frames[1:],
        duration=[80] * (len(frames) - 1) + [1000], loop=0,
        optimize=True, disposal=2,
    )
    with Image.open(movie) as image:
        if image.n_frames != len(frames):
            raise ValueError(f"GIF contains {image.n_frames} frames, expected {len(frames)}")

    capture_log = args.output_dir / "capture.log"
    shutil.copyfile(args.frames_dir / "arrival.log", capture_log)
    files = [movie, *(args.output_dir / f"frame-{n}.png" for n in KEYFRAMES), capture_log]
    manifest = {
        "source_commit": "1afb4d6235b5811699f5221cac58e47e8ac5957f",
        "godot_version": "4.7.2-stable Mono",
        "movie_frame_range_inclusive": [START, END],
        "movie_frame_count": len(frames),
        "steps_per_frame": 30,
        "simulation_seconds_per_raw_frame": 0.25,
        "gif_ms_per_frame": 80,
        "files": [
            {"name": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "bytes": path.stat().st_size}
            for path in files
        ],
    }
    (args.output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Built {len(frames)}-frame GIF: {movie}")


if __name__ == "__main__":
    main()
