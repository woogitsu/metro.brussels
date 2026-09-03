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
    """Odfiltrowuje rozpakowany strumień IDAT. Wymaga strumienia PEŁNEGO.

    Długość sprawdza wywołujący (`read_gray`), PRZED wejściem tutaj, bo ta funkcja
    nie ma jak zameldować braku sensownie. Zmierzone 03.09.2026, height=4, filtr 0
    w każdym wierszu: dla color_type 0, 2 i 0/16-bit strumień krótszy o 1 B i więcej
    wychodzi jako `IndexError` z wnętrza pętli — wyjątek spoza kontraktu modułu,
    którego bramka wizualna nie łapie; dla greyA i RGBA krótszy o dokładnie 1 B
    plik PRZECHODZI jako gotowy obraz, bo brakującego bajtu alfa ostatniego piksela
    `read_gray` i tak nie czyta. Blender pisze RGBA.
    """
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


def _tag_name(ctype):
    """Tag chunku w formie nadającej się do logu CI.

    Plik ucięty bywa też uszkodzony, a wtedy w miejscu tagu stoją dowolne bajty.
    Zwykłe `decode("ascii")` rzuciłoby wtedy `UnicodeDecodeError` — czyli dokładnie
    ten rodzaj wyjątku, którego mamy się tu pozbyć.
    """
    text = ctype.decode("ascii", "backslashreplace")
    return text if text.isprintable() else repr(ctype)


def read_gray(path):
    """Wczytuje PNG i zwraca luminancję jako `Image`.

    Każdy chunk jest sprawdzany na kompletność PRZED użyciem: długość zadeklarowana
    w nagłówku plus cztery bajty CRC muszą się mieścić w buforze. Bez tego plik
    urwany w środku chunku wychodził jako `struct.error` albo `zlib.error` — wyjątek
    spoza kontraktu tego modułu, nie mówiący nic o tym, co jest z plikiem nie tak.

    Rozpakowany strumień jest sprawdzany na długość ODDZIELNIE od kompletności
    chunków, bo to dwie różne usterki: plik może się składać z samych całych,
    poprawnie zCRC-owanych chunków i mieć w nich za mało danych obrazu.
    """
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
        end = pos + 12 + length  # 8 B nagłówka + dane + 4 B CRC
        if end > len(blob):
            raise PngError(
                f"{path}: chunk {_tag_name(ctype)} ucięty — nagłówek deklaruje "
                f"{length} B danych + 4 B CRC, brakuje {end - len(blob)} B")
        data = blob[pos + 8:pos + 8 + length]

        # CRC jest sprawdzany dla KAŻDEGO chunku, nie tylko dla tych, z których
        # ten moduł coś czyta. Zmierzone 03.09.2026 na PNG-u 4x3 z `write_gray`:
        # przekręcenie jednego bajtu w polu CRC dowolnego z trzech chunków (IHDR,
        # IDAT, IEND) dawało plik czytany BEZ SŁOWA jako poprawny obraz 4x3.
        #
        # Dlaczego to nie jest hipotetyczne: bramka wizualna porównuje zrzuty
        # bajt po bajcie i orzeka na tej podstawie „regresja" albo „bez zmian".
        # Zrzut uszkodzony w transporcie — ucięty zapis, zła pamięć, przerwany
        # artefakt CI — wchodził do tego porównania jako pełnoprawne wejście, więc
        # bramka porównywała cudzy szum z zaufanym wzorcem i wynik nazywała
        # regresją albo, gorzej, jej brakiem. CRC jest w pliku właśnie po to.
        #
        # Kontrola sięga tylko tam, gdzie chunk jest KOMPLETNY: plik ucięty ma
        # wyżej własną, dokładniejszą diagnozę i to ona ma paść pierwsza.
        stored = struct.unpack(">I", blob[pos + 8 + length:end])[0]
        actual = zlib.crc32(blob[pos + 4:pos + 8 + length]) & 0xFFFFFFFF
        if stored != actual:
            raise PngError(
                f"{path}: chunk {_tag_name(ctype)} uszkodzony — CRC w pliku "
                f"{stored:08x}, policzony z danych {actual:08x} "
                f"({length} B danych)")

        pos = end
        if ctype == b"IHDR":
            header = struct.unpack(">IIBBBBB", data)
        elif ctype == b"IDAT":
            idat += data
        elif ctype == b"IEND":
            break
    else:
        # Pętla wyszła przez warunek, nie przez IEND: zostało mniej niż 8 bajtów,
        # więc to, co zostało, jest urwanym nagłówkiem chunku, a nie śmieciem za
        # IEND-em (tamten wypada z pętli przez `break` i tu nie trafia).
        if pos < len(blob):
            raise PngError(
                f"{path}: plik urwany w nagłówku chunku — nagłówek ma 8 B, "
                f"zostało {len(blob) - pos} B")
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
    stream = zlib.decompress(bytes(idat))
    needed = height * (stride + 1)
    # Odrzucamy TYLKO strumień za krótki, nie „różny od". Zmierzone na PNG-ach, które
    # projekt realnie produkuje (Blender 5.2.1, 960x576: trzy `renders/TEST_*.png`
    # z `render_check.py`, RGBA/color_type 6, i pięć `renders/vis/TESTVIS_*.png`
    # z `capture_blender.py`, RGB/color_type 2): nadwyżka wynosi dokładnie 0 B
    # w każdym z ośmiu plików. Warunek `!=` byłby więc dziś równoważny, ale kodery
    # PNG mają prawo dopisać wyrównanie i wtedy `!=` odrzucałby pliki zdrowe —
    # a nadwyżkę `_unfilter` i tak ignoruje, bo czyta dokładnie `height` wierszy.
    if len(stream) < needed:
        raise PngError(
            f"{path}: strumień IDAT za krótki — rozpakowano {len(stream)} B, "
            f"potrzeba {needed} B (height={height} x (stride={stride} + 1 B filtra)), "
            f"brakuje {needed - len(stream)} B")
    raw = _unfilter(stream, width, height, bpp, stride)

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


def _write_png(path, width, height, samples, channels, color_type):
    """Wspólna ścieżka zapisu 8-bitowego PNG bez przeplotu, filtr 0 w każdym wierszu.

    `samples` jest PŁASKIM ciągiem próbek 0.0–1.0 idącym wiersz po wierszu, po
    `channels` wartości na piksel; `color_type` idzie wprost do IHDR. Wartości
    spoza zakresu są przycinane do 0–1 i skalowane do 0–255.

    `write_gray` i `write_rgb` różniły się wyłącznie liczbą kanałów i tą jedną
    liczbą w IHDR, a miały po własnej kopii pętli wierszy, przycięcia, skalowania
    i składania chunków. Wyjście jest identyczne co do bajtu z tym, co pisały
    osobno — poziom kompresji zlib (6) i kolejność chunków są tu te same.
    """
    raw = bytearray()
    row_len = width * channels
    for y in range(height):
        raw.append(0)
        base = y * row_len
        for i in range(row_len):
            value = samples[base + i]
            value = 0.0 if value < 0.0 else (1.0 if value > 1.0 else value)
            raw.append(int(round(value * 255.0)))
    payload = _chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, color_type, 0, 0, 0))
    payload += _chunk(b"IDAT", zlib.compress(bytes(raw), 6))
    payload += _chunk(b"IEND", b"")
    with open(path, "wb") as handle:
        handle.write(MAGIC + payload)


def write_gray(path, width, height, gray):
    """Zapisuje 8-bitowy PNG w skali szarości z listy wartości 0.0–1.0."""
    _write_png(path, width, height, gray, 1, 0)


def write_rgb(path, width, height, rgb):
    """Zapisuje 8-bitowy PNG RGB z listy trójek 0.0–1.0 (do obrazów testowych)."""
    _write_png(path, width, height,
               [channel for pixel in rgb for channel in pixel], 3, 2)
