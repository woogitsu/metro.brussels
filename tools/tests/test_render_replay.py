"""Checks for exact-resolution replay rendering without starting Godot."""

import importlib.util
import tempfile
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "visual/render_replay.py"
SPEC = importlib.util.spec_from_file_location("render_replay", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_only_viewport_dimensions_change():
    original = ("[display]\nwindow/size/viewport_width=1280\n"
                "window/size/viewport_height=720\nwindow/stretch/mode=1\n")
    changed = MODULE.set_viewport(original, 800, 600)
    assert changed == original.replace("1280", "800").replace("720", "600"), (
        "the isolated render must change only viewport dimensions")
    try:
        MODULE.set_viewport("[display]\n", 800, 600)
    except ValueError:
        pass
    else:
        assert False, "missing viewport settings must be rejected"


def test_real_png_header():
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "frame.png"
        path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00\x00\x00\x0dIHDR"
                         + (800).to_bytes(4, "big") + (600).to_bytes(4, "big"))
        assert MODULE.png_size(path) == (800, 600), (
            "PNG dimensions must come from the IHDR header")


if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))
