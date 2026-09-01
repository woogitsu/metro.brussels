"""Minimalne czytanie i zapisywanie PNG bez zewnętrznych zależności.

Świadomie nie używamy Pillow ani numpy: `compare.py` musi działać na gołym
`python3` na dowolnym runnerze, także wtedy, gdy Blender nie jest zainstalowany.
Obsługiwane jest to, co realnie produkuje Blender: 8- i 16-bitowe PNG bez
przeplotu, w wariantach grey/greyA/RGB/RGBA.
"""
import struct
import zlib

MAGIC = b"\x89PNG\r\n\x1a\n"
_CHANNELS = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}


class PngError(ValueError):
    pass


class Image:
    """Obraz w skali szarości, wartości 0.0–1.0, wiersz po wierszu."""

    __slots__ = ("width", "height", "gray", "color_type", "bit_depth")

    def __init__(self, width, height, gray, color_type=2, bit_depth=8):
        self.width = width
        self.height = height
        self.gray = gray
        self.color_type = color_type
        self.bit_depth = bit_depth

    @property
    def size(self):
        return (self.width, self.height)

    def at(self, x, y):
        return self.gray[y * self.width + x]


def _paeth(a, b, c):
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    if pb <= pc:
        return b
    return c


def _unfilter(raw, width, height, bpp, stride):
    out = bytearray(height * stride)
    pos = 0
    prev = bytearray(stride)
    for y in range(height):
        ftype = raw[pos]
        pos += 1
        line = bytearray(raw[pos:pos + stride])
        pos += stride
        if ftype == 1:
            for i in range(bpp, stride):
                line[i] = (line[i] + line[i - bpp]) & 0xFF
        elif ftype == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 0xFF
        elif ftype == 3:
            for i in range(stride):
                left = line[i - bpp] if i >= bpp else 0
                line[i] = (line[i] + ((left + prev[i]) >> 1)) & 0xFF
        elif ftype == 4:
            for i in range(stride):
                left = line[i - bpp] if i >= bpp else 0
                upleft = prev[i - bpp] if i >= bpp else 0
                line[i] = (line[i] + _paeth(left, prev[i], upleft)) & 0xFF
        elif ftype != 0:
            raise PngError(f"nieznany filtr PNG: {ftype}")
        out[y * stride:(y + 1) * stride] = line
        prev = line
    return out


def read_gray(path):
    """Wczytuje PNG i zwraca luminancję jako `Image`."""
    with open(path, "rb") as handle:
        blob = handle.read()
    if not blob.startswith(MAGIC):
        raise PngError(f"{path}: zły magic PNG")
    pos = len(MAGIC)
    header = None
    idat = bytearray()
    while pos + 8 <= len(blob):
        (length,) = struct.unpack(">I", blob[pos:pos + 4])
        ctype = blob[pos + 4:pos + 8]
        data = blob[pos + 8:pos + 8 + length]
        pos += 12 + length
        if ctype == b"IHDR":
            header = struct.unpack(">IIBBBBB", data)
        elif ctype == b"IDAT":
            idat += data
        elif ctype == b"IEND":
            break
    if header is None:
        raise PngError(f"{path}: brak IHDR")
    width, height, bit_depth, color_type, _comp, _filt, interlace = header
    if interlace:
        raise PngError(f"{path}: PNG z przeplotem nie jest obsługiwany")
    if bit_depth not in (8, 16) or color_type not in _CHANNELS or color_type == 3:
        raise PngError(f"{path}: nieobsługiwany PNG bit_depth={bit_depth} color_type={color_type}")
    channels = _CHANNELS[color_type]
    sample_bytes = bit_depth // 8
    bpp = channels * sample_bytes
    stride = width * bpp
    raw = _unfilter(zlib.decompress(bytes(idat)), width, height, bpp, stride)

    gray = [0.0] * (width * height)
    scale = 255.0 if bit_depth == 8 else 65535.0
    for y in range(height):
        row = y * stride
        base = y * width
        for x in range(width):
            off = row + x * bpp
            if sample_bytes == 1:
                if channels >= 3:
                    r, g, b = raw[off], raw[off + 1], raw[off + 2]
                else:
                    r = g = b = raw[off]
            else:
                if channels >= 3:
                    r = (raw[off] << 8) | raw[off + 1]
                    g = (raw[off + 2] << 8) | raw[off + 3]
                    b = (raw[off + 4] << 8) | raw[off + 5]
                else:
                    r = g = b = (raw[off] << 8) | raw[off + 1]
            gray[base + x] = (0.2126 * r + 0.7152 * g + 0.0722 * b) / scale
    return Image(width, height, gray, color_type, bit_depth)


def _chunk(tag, payload):
    return struct.pack(">I", len(payload)) + tag + payload + struct.pack(">I", zlib.crc32(tag + payload) & 0xFFFFFFFF)


def write_gray(path, width, height, gray):
    """Zapisuje 8-bitowy PNG w skali szarości z listy wartości 0.0–1.0."""
    raw = bytearray()
    for y in range(height):
        raw.append(0)
        base = y * width
        for x in range(width):
            value = gray[base + x]
            value = 0.0 if value < 0.0 else (1.0 if value > 1.0 else value)
            raw.append(int(round(value * 255.0)))
    payload = _chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0))
    payload += _chunk(b"IDAT", zlib.compress(bytes(raw), 6))
    payload += _chunk(b"IEND", b"")
    with open(path, "wb") as handle:
        handle.write(MAGIC + payload)


def write_rgb(path, width, height, rgb):
    """Zapisuje 8-bitowy PNG RGB z listy trójek 0.0–1.0 (do obrazów testowych)."""
    raw = bytearray()
    for y in range(height):
        raw.append(0)
        base = y * width
        for x in range(width):
            for channel in rgb[base + x]:
                channel = 0.0 if channel < 0.0 else (1.0 if channel > 1.0 else channel)
                raw.append(int(round(channel * 255.0)))
    payload = _chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
    payload += _chunk(b"IDAT", zlib.compress(bytes(raw), 6))
    payload += _chunk(b"IEND", b"")
    with open(path, "wb") as handle:
        handle.write(MAGIC + payload)
