#!/usr/bin/env python3
"""Suma SHA-256 samych PIKSELI pliku PNG, z pominięciem metadanych.

**Po co osobne narzędzie, skoro jest `sha256sum`.** Blender stempluje w każdym
renderze dwa bloki `tEXt`, które zmieniają się przy każdym przebiegu:

    Date        2026/09/06 03:50:00
    RenderTime  00:37.93

Suma pliku jest więc różna po każdym renderze **tej samej geometrii**, i nie nadaje
się na wyrocznię „czy refaktor czegoś nie zmienił". Zmierzone 06.09.2026: dwa
przebiegi `render_check.py` na tym samym `build/TEST.glb` dały trzy różne sumy plików
i **trzy identyczne sumy `IDAT`**, co do bajtu i co do długości (542 620 / 546 075 /
640 500 B).

Ten skrypt liczy sumę po sklejonych blokach `IDAT`, czyli po skompresowanym
strumieniu pikseli. Nie rozpakowuje go: dwa identyczne obrazy zapisane tym samym
koderem dają ten sam strumień, a o to tu chodzi — o porównanie wyjścia z wyjściem
tego samego narzędzia, nie o porównanie obrazów w ogóle.
"""
import hashlib
import struct
import sys

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def idat_sha256(path):
    """SHA-256 sklejonych bloków `IDAT`. Rzuca `ValueError` na pliku, który nie jest PNG."""
    with open(path, "rb") as handle:
        data = handle.read()
    if data[:8] != PNG_MAGIC:
        raise ValueError(f"{path}: to nie jest PNG")
    digest = hashlib.sha256()
    offset, seen = 8, 0
    while offset + 8 <= len(data):
        length = struct.unpack(">I", data[offset:offset + 4])[0]
        kind = data[offset + 4:offset + 8]
        if kind == b"IDAT":
            digest.update(data[offset + 8:offset + 8 + length])
            seen += 1
        offset += 12 + length
    if not seen:
        raise ValueError(f"{path}: PNG bez ani jednego bloku IDAT")
    return digest.hexdigest()


def main(argv=None):
    paths = (argv if argv is not None else sys.argv[1:])
    if not paths:
        print("użycie: png_pixels_sha256.py PLIK.png [PLIK.png ...]", file=sys.stderr)
        return 2
    for path in paths:
        print(f"{idat_sha256(path)}  {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
