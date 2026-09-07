#!/usr/bin/env python3
"""Testy sumy pikselowej PNG — narzędzia, bez którego nie da się porównać renderów.

Skąd się wzięło: zmierzone 06.09.2026, dwa przebiegi `render_check.py` na TYM SAMYM
`build/TEST.glb` dały trzy różne sumy plików i trzy identyczne sumy `IDAT`. Różniły
się dokładnie dwa bloki `tEXt`, które Blender stempluje w każdym renderze:

    Date        2026/09/06 03:50:00   ->   2026/09/06 03:53:44
    RenderTime  00:37.93              ->   00:22.96

Kryterium pozycji 6.B9 żąda renderów „identycznych co do sumy SHA-256". W literze
jest to nieosiągalne niezależnie od kodu; w intencji — w pełni sprawdzalne, i tym
sprawdzeniem jest `idat_sha256`.
"""
import os
import struct
import sys
import tempfile
import zlib

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "ci"))

import png_pixels_sha256 as P  # noqa: E402


def _png(path, pixels=b"\x00\xff\x00", text=None):
    """Najmniejszy poprawny PNG 1x1 z opcjonalnym blokiem `tEXt`."""
    def blok(kind, data):
        return (struct.pack(">I", len(data)) + kind + data
                + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF))

    ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    idat = zlib.compress(b"\x00" + pixels)
    out = [P.PNG_MAGIC, blok(b"IHDR", ihdr)]
    if text is not None:
        out.append(blok(b"tEXt", text))
    out += [blok(b"IDAT", idat), blok(b"IEND", b"")]
    with open(path, "wb") as handle:
        handle.write(b"".join(out))
    return path


def test_png_pixels_two_files_differing_only_in_metadata_hash_the_same():
    """Sedno narzędzia: `tEXt` się zmienia, piksele nie — suma ma się nie ruszyć."""
    with tempfile.TemporaryDirectory() as katalog:
        a = _png(os.path.join(katalog, "a.png"), text=b"Date\x002026/09/06 03:50:00")
        b = _png(os.path.join(katalog, "b.png"), text=b"Date\x002026/09/06 03:53:44")
        assert open(a, "rb").read() != open(b, "rb").read(), "pliki miały się różnić"
        assert P.idat_sha256(a) == P.idat_sha256(b)


def test_png_pixels_a_changed_pixel_changes_the_hash():
    """Kontrola dodatnia: bez niej funkcja zwracająca stałą przechodziłaby test wyżej."""
    with tempfile.TemporaryDirectory() as katalog:
        a = _png(os.path.join(katalog, "a.png"), pixels=b"\x00\xff\x00")
        b = _png(os.path.join(katalog, "b.png"), pixels=b"\x00\xfe\x00")
        assert P.idat_sha256(a) != P.idat_sha256(b)


def test_png_pixels_a_file_that_is_not_a_png_is_refused():
    """Milczące zero na cudzym pliku byłoby gorsze od błędu."""
    with tempfile.TemporaryDirectory() as katalog:
        obcy = os.path.join(katalog, "obcy.bin")
        with open(obcy, "wb") as handle:
            handle.write(b"to nie jest png")
        try:
            P.idat_sha256(obcy)
        except ValueError as blad:
            assert "nie jest PNG" in str(blad), blad
        else:
            raise AssertionError("plik bez nagłówka PNG przeszedł")


def test_png_pixels_a_png_without_idat_is_refused():
    """PNG bez pikseli to nie jest obraz o sumie zerowej, tylko plik do zgłoszenia."""
    with tempfile.TemporaryDirectory() as katalog:
        pusty = os.path.join(katalog, "pusty.png")
        ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
        def blok(kind, data):
            return (struct.pack(">I", len(data)) + kind + data
                    + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF))
        with open(pusty, "wb") as handle:
            handle.write(P.PNG_MAGIC + blok(b"IHDR", ihdr) + blok(b"IEND", b""))
        try:
            P.idat_sha256(pusty)
        except ValueError as blad:
            assert "bez ani jednego bloku IDAT" in str(blad), blad
        else:
            raise AssertionError("PNG bez IDAT przeszedł")

# 6.D25: uruchomienie tego pliku WPROST idzie ta sama droga, co caly zestaw —
# z licznikiem asercji i z odmowa przy zerze testow. Bez tej gałęzi `python3
# tools/tests/<modul>.py` konczyl sie kodem 0, nie wykonawszy ani jednego testu.
if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))
