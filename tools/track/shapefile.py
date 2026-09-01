"""Minimalny czytnik ESRI Shapefile — czysty stdlib, bez pyshp i bez GDAL.

Projekt nie ma manifestu zależności, a CI odpala goły `python3`, więc geometria
STIB musi być czytana bez bibliotek zewnętrznych.

Obsługiwane typy: 1 (Point), 3 (PolyLine), 11 (PointZ), 13 (PolyLineZ) — czyli to,
co realnie występuje w `2603_STIB_MIVB_Network`. Inne typy są odrzucane jawnie.
"""
import struct

SHP_MAGIC = 9994
TYPE_POINT = 1
TYPE_POLYLINE = 3
TYPE_POINTZ = 11
TYPE_POLYLINEZ = 13
SUPPORTED = (TYPE_POINT, TYPE_POLYLINE, TYPE_POINTZ, TYPE_POLYLINEZ)


class ShapefileError(ValueError):
    pass


def read_shp(data):
    """Zwraca listę kształtów: {'type', 'points', 'parts'} we współrzędnych źródła."""
    if len(data) < 100:
        raise ShapefileError("plik .shp krótszy niż nagłówek")
    magic, = struct.unpack(">i", data[0:4])
    if magic != SHP_MAGIC:
        raise ShapefileError(f"zły magic .shp: {magic}")
    file_type, = struct.unpack("<i", data[32:36])
    if file_type not in SUPPORTED:
        raise ShapefileError(f"nieobsługiwany typ shapefile: {file_type}")

    shapes = []
    offset = 100
    while offset + 8 <= len(data):
        _number, length_words = struct.unpack(">ii", data[offset:offset + 8])
        content = data[offset + 8:offset + 8 + length_words * 2]
        offset += 8 + length_words * 2
        if not content:
            continue
        shape_type, = struct.unpack("<i", content[0:4])
        if shape_type == 0:
            shapes.append({"type": 0, "points": [], "parts": []})
            continue
        if shape_type in (TYPE_POINT, TYPE_POINTZ):
            x, y = struct.unpack("<dd", content[4:20])
            shapes.append({"type": shape_type, "points": [(x, y)], "parts": [0]})
        elif shape_type in (TYPE_POLYLINE, TYPE_POLYLINEZ):
            num_parts, num_points = struct.unpack("<ii", content[36:44])
            parts = list(struct.unpack(f"<{num_parts}i", content[44:44 + 4 * num_parts]))
            base = 44 + 4 * num_parts
            coords = struct.unpack(f"<{2 * num_points}d", content[base:base + 16 * num_points])
            points = [(coords[i], coords[i + 1]) for i in range(0, len(coords), 2)]
            shapes.append({"type": shape_type, "points": points, "parts": parts})
        else:
            raise ShapefileError(f"nieobsługiwany typ rekordu: {shape_type}")
    return shapes


def read_dbf(data, encoding="utf-8"):
    """Zwraca listę słowników atrybutów w kolejności rekordów .shp."""
    if len(data) < 32:
        raise ShapefileError("plik .dbf krótszy niż nagłówek")
    record_count, header_length, record_length = struct.unpack("<iHH", data[4:12])
    fields = []
    offset = 32
    while offset < len(data) and data[offset] != 0x0D:
        name = data[offset:offset + 11].split(b"\x00")[0].decode("latin-1").strip()
        field_type = chr(data[offset + 11])
        field_length = data[offset + 16]
        decimals = data[offset + 17]
        fields.append((name, field_type, field_length, decimals))
        offset += 32

    rows = []
    for index in range(record_count):
        start = header_length + index * record_length
        raw = data[start:start + record_length]
        if not raw or raw[:1] == b"*":  # rekord skasowany
            continue
        cursor = 1
        row = {}
        for name, field_type, field_length, decimals in fields:
            chunk = raw[cursor:cursor + field_length]
            cursor += field_length
            text = chunk.decode(encoding, errors="replace").strip()
            if field_type == "N":
                row[name] = _number(text, decimals)
            elif field_type == "F":
                row[name] = _number(text, 1)
            elif field_type == "L":
                row[name] = text.upper() in ("Y", "T")
            else:
                row[name] = text
            row[name] = row[name] if row[name] != "" else ""
        rows.append(row)
    return rows


def _number(text, decimals):
    if text in ("", "*"):
        return None
    try:
        return float(text) if decimals else int(text)
    except ValueError:
        try:
            return float(text)
        except ValueError:
            return None


def read_pair(shp_bytes, dbf_bytes, encoding="utf-8"):
    """Łączy geometrię z atrybutami; liczby rekordów muszą się zgadzać."""
    shapes = read_shp(shp_bytes)
    rows = read_dbf(dbf_bytes, encoding)
    if len(shapes) != len(rows):
        raise ShapefileError(f"niezgodna liczba rekordów: .shp={len(shapes)} .dbf={len(rows)}")
    return [{"geometry": shape, "attributes": row} for shape, row in zip(shapes, rows)]


def read_prj(text):
    """Wyciąga nazwę odwzorowania i kluczowe parametry z .prj (WKT ESRI)."""
    name = ""
    if text.startswith("PROJCS["):
        name = text[8:].split('"')[0]
    params = {}
    for key in ("False_Easting", "False_Northing", "Central_Meridian",
                "Standard_Parallel_1", "Standard_Parallel_2", "Latitude_Of_Origin"):
        marker = f'PARAMETER["{key}",'
        if marker in text:
            tail = text.split(marker, 1)[1]
            params[key] = float(tail.split("]", 1)[0])
    return {"name": name, "parameters": params}
