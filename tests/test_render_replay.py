"""Small checks for the isolated replay renderer's resolution handling."""

import importlib.util
from pathlib import Path
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "tools/visual/render_replay.py"
SPEC = importlib.util.spec_from_file_location("render_replay", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class RenderReplayTests(unittest.TestCase):
    def test_only_viewport_dimensions_change(self):
        original = "[display]\nwindow/size/viewport_width=1280\nwindow/size/viewport_height=720\nwindow/stretch/mode=1\n"
        changed = MODULE.set_viewport(original, 800, 600)
        self.assertEqual(changed, original.replace("1280", "800").replace("720", "600"))
        with self.assertRaises(ValueError):
            MODULE.set_viewport("[display]\n", 800, 600)

    def test_real_png_header(self):
        import tempfile
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "frame.png"
            path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00\x00\x00\x0dIHDR" + (800).to_bytes(4, "big") + (600).to_bytes(4, "big"))
            self.assertEqual(MODULE.png_size(path), (800, 600))


if __name__ == "__main__":
    unittest.main()
