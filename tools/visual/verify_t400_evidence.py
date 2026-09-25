"""Verify that the reviewed T-400 PNG evidence has not changed."""

import hashlib
import json
import struct
from pathlib import Path


def main() -> None:
    folder = Path(__file__).resolve().parents[2] / "reports/visual-evidence/t400-run-36078093066"
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    for item in manifest["files"]:
        path = folder / item["name"]
        data = path.read_bytes()
        assert hashlib.sha256(data).hexdigest() == item["sha256"], path
        if path.suffix == ".png":
            assert data[:8] == b"\x89PNG\r\n\x1a\n", path
            assert struct.unpack(">II", data[16:24]) == (1280, 720), path
    print(f"Verified {len(manifest['files'])} unchanged evidence files")


if __name__ == "__main__":
    main()
