"""Verify the reviewed T-400 capture files, including the Parc side view."""

import hashlib
import json
import struct
from pathlib import Path


def verify_folder(folder: Path, expected: set[str]) -> int:
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    declared = [item["name"] for item in manifest["files"]]
    actual = [path.name for path in folder.iterdir() if path.is_file() and path.name != "manifest.json"]
    if len(declared) != len(set(declared)):
        raise ValueError("duplicate manifest entries")
    if set(declared) != expected or set(actual) != expected:
        raise ValueError(f"evidence files differ from expected set: {folder}")
    if "sources" in manifest:
        source_files = [name for source in manifest["sources"] for name in source["files"]]
        if len(source_files) != len(set(source_files)) or set(source_files) != expected:
            raise ValueError(f"evidence files differ from manifest sources: {folder}")
    for item in manifest["files"]:
        path = folder / item["name"]
        data = path.read_bytes()
        if len(data) != item["bytes"]:
            raise ValueError(f"unexpected file size: {path}")
        if hashlib.sha256(data).hexdigest() != item["sha256"]:
            raise ValueError(f"SHA-256 mismatch: {path}")
        if path.suffix == ".png":
            if not data.startswith(b"\x89PNG\r\n\x1a\n"):
                raise ValueError(f"invalid PNG signature: {path}")
            if struct.unpack(">II", data[16:24]) != (1280, 720):
                raise ValueError(f"unexpected PNG dimensions: {path}")
    return len(declared)


def main() -> None:
    root = Path(__file__).resolve().parents[2] / "reports/visual-evidence"
    original = root / "t400-run-36078093066"
    original_manifest = json.loads((original / "manifest.json").read_text(encoding="utf-8"))
    original_files = {name for source in original_manifest["sources"] for name in source["files"]}
    count = verify_folder(original, original_files)
    count += verify_folder(root / "t400-side", {"PARC_side.png", "PARC_side.log"})
    print(f"Verified {count} unchanged evidence files")


if __name__ == "__main__":
    main()
