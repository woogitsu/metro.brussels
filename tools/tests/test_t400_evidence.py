"""Integrity checks for the published Parc side-view capture."""

import hashlib
import json
import shutil
import struct
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/visual"))
import verify_t400_evidence as evidence  # noqa: E402

SIDE = ROOT / "reports/visual-evidence/t400-side"
EXPECTED = {"PARC_side.png", "PARC_side.log"}


def _copy_side():
    temporary = tempfile.TemporaryDirectory()
    folder = Path(temporary.name) / "side"
    shutil.copytree(SIDE, folder)
    return temporary, folder


def _rejects(folder, reason):
    try:
        evidence.verify_folder(folder, EXPECTED)
    except ValueError as error:
        assert reason in str(error), str(error)
    else:
        raise AssertionError(f"corrupted side-view evidence passed: {reason}")


def test_published_side_view_png_and_log_match_manifest():
    assert evidence.verify_folder(SIDE, EXPECTED) == 2, "published side capture must include image and log"


def test_side_view_png_and_log_byte_changes_are_rejected():
    for name in sorted(EXPECTED):
        temporary, folder = _copy_side()
        try:
            path = folder / name
            data = bytearray(path.read_bytes())
            data[-1] ^= 1
            path.write_bytes(data)
            _rejects(folder, "SHA-256 mismatch")
        finally:
            temporary.cleanup()


def test_side_view_png_wrong_dimensions_rejected_even_with_updated_hash():
    temporary, folder = _copy_side()
    try:
        path = folder / "PARC_side.png"
        data = bytearray(path.read_bytes())
        data[16:20] = struct.pack(">I", 1279)
        path.write_bytes(data)
        manifest_path = folder / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        png = next(item for item in manifest["files"] if item["name"] == path.name)
        png["sha256"] = hashlib.sha256(data).hexdigest()
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        _rejects(folder, "unexpected PNG dimensions")
    finally:
        temporary.cleanup()


def test_side_view_missing_log_is_rejected():
    temporary, folder = _copy_side()
    try:
        (folder / "PARC_side.log").unlink()
        _rejects(folder, "evidence files differ")
    finally:
        temporary.cleanup()


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT / "tools/tests"))
    import test_all
    test_all.main(__file__)
