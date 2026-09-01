#!/usr/bin/env python3
"""Mierzy rozstaw torów metra na pakiecie A z INSPIRE Rails (EPSG:3035).

    python3 tools/track/inspire_rail.py --alignment data/track/L1_A.json \
        --out build/L1_A-track-spacing.json
    python3 tools/track/inspire_rail.py --gml-file build/TN.RailTransportNetwork.gml

Źródło: `belgian_mobility_inspire_rails` — INSPIRE Transport Networks STIB/MIVB,
`TN.RailTransportNetwork.gml` w archiwum ZIP. Zawiera tramwaj i metro w jednym pliku,
w **EPSG:3035**, `srsDimension="2"`, czyli bez jakiejkolwiek informacji pionowej.
Ten dataset nie odblokowuje T-112 i nie wolno go do tego użyć.

Co ten skrypt robi i czego nie robi:

- liczy **zmierzony** rozstaw dwóch kierunkowych polilinii pnia 1/5;
- **nie** zmienia `tools/blender/profiles.py`. Zamiana wymiaru projektowego
  (`track_offsets`) na wartość ze źródła jest decyzją właściciela i należy do R-005.

Pułapka, w którą łatwo wpaść: na odcinku Gare de l'Ouest — Beekkant obok pnia 1/5
biegną linie 2/6, w tym samym korytarzu i przez te same dwie stacje. Wybór linków
„po bliskości do osi" wciąga je do pomiaru i daje czwarty i piąty mod rozkładu
odsunięć. Dlatego linki są wybierane **topologicznie**: przez przejście po
identyfikatorach przystanków w kolejności stacji pakietu A, a nie geometrycznie.
Kontrolna selekcja korytarzowa jest liczona równolegle, właśnie po to, żeby raport
mógł pokazać różnicę zamiast ją deklarować.

Niedostępność źródła jest wynikiem, a nie powodem do pominięcia pomiaru.
"""
import argparse
import io
import json
import math
import os
import re
import statistics
import sys
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "tools", "data"))
sys.path.insert(0, os.path.join(ROOT, "tools", "blender"))

import crs as CRS  # noqa: E402
import provenance as P  # noqa: E402
import sweep as SW  # noqa: E402

SOURCE_ID = "belgian_mobility_inspire_rails"
SOURCE_REGISTRY = os.path.join(ROOT, "data", "network", "sources.json")
GML_MEMBER = "TN.RailTransportNetwork.gml"
SOURCE_CRS = "EPSG:3035"

GML = "{http://www.opengis.net/gml/3.2}"
NET = "{http://inspire.ec.europa.eu/schemas/net/5.0}"
TN = "{http://inspire.ec.europa.eu/schemas/tn/5.0}"
RA = "{http://inspire.ec.europa.eu/schemas/tn-ra/5.0}"
GN = "{http://inspire.ec.europa.eu/schemas/gn/4.0}"
XLINK = "{http://www.w3.org/1999/xlink}"

NODE_RE = re.compile(r"^(Métro|Tram) stop (\S+) serving", re.UNICODE)
LINK_RE = re.compile(r"^Link between stops (\S+) and (\S+)")
METRO = "Métro"

# Poza tym pasem od osi kontrolna selekcja korytarzowa nie ma już czego złapać;
# 60 m mieści i pień 1/5, i równoległe tory 2/6, o które w tym pomiarze chodzi.
CORRIDOR_M = 60.0
# Odsunięcia większe niż to są węzłem albo rozjazdem, nie międzytorzem szlakowym.
RUNNING_OFFSET_MAX_M = 20.0
# Kosz niosący mniej niż tyle próbek to szum digitalizacji jednego linku, nie mod.
MODE_MIN_SHARE = 0.015


# --- parsowanie GML -----------------------------------------------------------

def _text(element, path):
    found = element.find(path)
    return None if found is None else (found.text or "").strip()


def parse_posbags(text):
    """`gml:posList` w EPSG:3035 idzie w kolejności osi **northing, easting**.

    To nie jest kosmetyka: zamiana kolejności przenosi Brukselę na Atlantyk
    (-10,4°E / 56,9°N zamiast 4,41°E / 50,84°N), więc błąd byłby widoczny.
    Kolejność bierze się z rejestru EPSG dla 3035 i z tego, że `srsName` jest
    podany jako URI OGC, a nie jako `EPSG:3035` — wtedy obowiązuje osiowanie rejestru.
    """
    values = [float(v) for v in text.split()]
    return [(values[i + 1], values[i]) for i in range(0, len(values), 2)]


def parse_gml(data):
    """Zwraca węzły, linki, linie i sekwencje linków z pliku INSPIRE.

    `xml.etree.ElementTree` wystarcza i jest w stdlib; GML to zwykły XML
    z przestrzeniami nazw, a regeksy na strukturze XML są błędem, nie skrótem.
    """
    root = ET.fromstring(data)
    nodes, links, lines, sequences = {}, [], [], []
    node_features = 0
    duplicates = []
    for member in root:
        for feature in member:
            tag = feature.tag
            if tag == RA + "RailwayNode":
                node_features += 1
                parsed = _parse_node(feature)
                duplicates += [code for code in parsed if code in nodes]
                nodes.update(parsed)
            elif tag == RA + "RailwayLink":
                link = _parse_link(feature)
                if link:
                    links.append(link)
            elif tag == RA + "RailwayLine":
                lines.append(_parse_line(feature))
            elif tag == RA + "RailwayLinkSequence":
                sequences.append(_parse_sequence(feature))
    return {"nodes": nodes, "links": links, "lines": lines, "sequences": sequences,
            # Mapa jest kluczowana kodem przystanku, a ten nie jest unikalny w całym
            # pliku (dwa perony tramwajowe potrafią dzielić kod), więc surowa liczba
            # obiektów i liczba kluczy to dwie różne liczby i obie idą do raportu.
            "node_features": node_features, "duplicate_stop_codes": sorted(set(duplicates))}


def _parse_node(feature):
    description = _text(feature, GML + "description") or ""
    match = NODE_RE.match(description)
    if not match:
        return {}
    position = _text(feature, ".//" + GML + "pos")
    name = _text(feature, ".//" + GN + "text")
    return {match.group(2): {
        "id": feature.get(GML + "id"),
        "mode": match.group(1),
        "station": name,
        "point": parse_posbags(position)[0] if position else None,
    }}


def _parse_link(feature):
    description = _text(feature, GML + "description") or ""
    match = LINK_RE.match(description)
    pos_list = _text(feature, ".//" + GML + "posList")
    if not match or not pos_list:
        return None
    return {
        "id": feature.get(GML + "id"),
        "from": match.group(1),
        "to": match.group(2),
        "points": parse_posbags(pos_list),
        "valid_from": _text(feature, TN + "validFrom"),
        "valid_to": _text(feature, TN + "validTo"),
    }


def _parse_line(feature):
    sequence = feature.find(NET + "link")
    return {
        "id": feature.get(GML + "id"),
        "code": _text(feature, RA + "railwayLineCode"),
        "description": _text(feature, GML + "description"),
        "sequence_href": None if sequence is None else sequence.get(XLINK + "href"),
        "valid_from": _text(feature, TN + "validFrom"),
        "valid_to": _text(feature, TN + "validTo"),
    }


def _parse_sequence(feature):
    hrefs = [element.get(XLINK + "href")
             for element in feature.iter(NET + "link") if element.get(XLINK + "href")]
    return {"id": feature.get(GML + "id"), "link_hrefs": hrefs}


def topology_health(parsed):
    """Ile referencji `net:link` z sekwencji trafia w istniejący `RailwayLink`.

    W pobranym pliku odpowiedź brzmi „zero", więc powiązanie linia -> linki trzeba
    zbudować inaczej. Liczba jest w raporcie, żeby dało się zauważyć, gdyby wydawca
    to naprawił, i wtedy uprościć ten skrypt.
    """
    known = {link["id"] for link in parsed["links"]}
    total = resolved = 0
    for sequence in parsed["sequences"]:
        for href in sequence["link_hrefs"]:
            total += 1
            resolved += 1 if href.lstrip("#") in known else 0
    return {"link_references": total, "resolved": resolved,
            "note": "Sekwencje wskazują na identyfikatory, których w pliku nie ma "
                    "(np. #link_560011 wobec realnego link_5655295532)."}


def validity_window(parsed, today=None):
    """Okno ważności linków i to, czy jest już przeterminowane wobec dnia pobrania."""
    starts = sorted(l["valid_from"] for l in parsed["links"] if l["valid_from"])
    ends = sorted(l["valid_to"] for l in parsed["links"] if l["valid_to"])
    if not starts or not ends:
        return {"status": "brak deklaracji"}
    today = today or datetime.utcnow().strftime("%Y-%m-%d")
    latest_end = ends[-1][:10]
    return {
        "valid_from": starts[0][:10],
        "valid_to": latest_end,
        "checked_against": today,
        "status": "wygasłe" if latest_end < today else "aktualne",
    }


# --- wybór linków pnia --------------------------------------------------------

def metro_links(parsed):
    nodes = parsed["nodes"]
    return [link for link in parsed["links"]
            if nodes.get(link["from"], {}).get("mode") == METRO
            and nodes.get(link["to"], {}).get("mode") == METRO]


def walk_stations(links, nodes, station_names, start_codes):
    """Wszystkie ścieżki linków przechodzące przez `station_names` w tej kolejności.

    Przejście dopuszcza skok wewnątrz jednej stacji (na Schumanie reverse idzie
    8071 -> 8065 -> 8061, czyli dwa linki na jednej nazwie), ale nie dopuszcza
    odwiedzenia tego samego węzła dwa razy — inaczej pętla w węźle Beekkant
    produkowałaby nieskończenie wiele „ścieżek".
    """
    outgoing = {}
    for link in links:
        outgoing.setdefault(link["from"], []).append(link)
    paths = []

    def step(code, index, chain, visited):
        if index == len(station_names) - 1:
            paths.append(list(chain))
            return
        for link in outgoing.get(code, []):
            target = link["to"]
            if target in visited:
                continue
            station = nodes.get(target, {}).get("station")
            if station == station_names[index + 1]:
                step(target, index + 1, chain + [link], visited | {target})
            elif station == station_names[index]:
                step(target, index, chain + [link], visited | {target})

    for code in start_codes:
        step(code, 0, [], {code})
    return paths


def package_chains(parsed, stop_ids):
    """Dwie kierunkowe ścieżki pnia: „w przód" wg `stop_id` z osi i przeciwna.

    Kierunek zgodny z osią bierzemy wprost ze skomitowanego `L1_A.json` — to jedyne
    miejsce, w którym wiadomo, który tor opisuje oś. Kierunek przeciwny trzeba
    znaleźć, bo w danych nie ma pola, które by go wskazywało.
    """
    nodes = parsed["nodes"]
    links = metro_links(parsed)
    names = [nodes[code]["station"] for code in stop_ids if code in nodes]
    missing = [code for code in stop_ids if code not in nodes]

    forward = walk_stations(links, nodes, names, [stop_ids[0]])
    forward = [p for p in forward if [l["to"] for l in p] == list(stop_ids[1:])]

    terminus = {code for code, node in nodes.items()
                if node["station"] == names[-1] and node["mode"] == METRO} - {stop_ids[-1]}
    reverse = walk_stations(links, nodes, list(reversed(names)), sorted(terminus))
    return {"forward": forward, "reverse": reverse, "missing_stops": missing,
            "station_names": names}


def corridor_links(parsed, axis, radius_m=CORRIDOR_M):
    """Kontrolna selekcja „po bliskości": to ona wciąga linie 2/6 do pomiaru."""
    out = []
    for link in metro_links(parsed):
        points = [CRS.laea3035_to_lambert72(x, y) for x, y in link["points"]]
        if min(SW.point_to_polyline((p[0], p[1], 0.0), axis) for p in points) <= radius_m:
            out.append(link)
    return out


# --- pomiar rozstawu ----------------------------------------------------------

def project_signed(point, axis, frames):
    """Kilometraż i **znakowane** odsunięcie punktu od osi.

    Znak jest liczony wzdłuż wektora „prawo" ramki RMF (`frames[i][2]`), czyli tej
    samej ramki, na której `tunnel_sweep.py` stawia profil. Dzięki temu zmierzone
    odsunięcie jest w dokładnie tym samym układzie co `track_offsets` w profilu
    i obie liczby wolno porównywać.
    """
    best = None
    station = 0.0
    for index in range(len(axis) - 1):
        ax, ay = axis[index][0], axis[index][1]
        bx, by = axis[index + 1][0], axis[index + 1][1]
        dx, dy = bx - ax, by - ay
        segment = dx * dx + dy * dy
        length = math.sqrt(segment)
        if segment <= 0.0:
            station += length
            continue
        t = ((point[0] - ax) * dx + (point[1] - ay) * dy) / segment
        t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
        foot = (ax + t * dx, ay + t * dy)
        distance = math.dist(point, foot)
        if best is None or distance < best[0]:
            right = frames[index][2]
            offset = (point[0] - foot[0]) * right[0] + (point[1] - foot[1]) * right[1]
            best = (distance, station + t * length, offset)
        station += length
    return best[1], best[2], best[0]


def offsets_for(links, axis, frames):
    """Odsunięcia wszystkich wierzchołków linków, z flagą „poza zakresem osi".

    Oś pakietu A kończy się na kotwicy Merode, a linki kierunku przeciwnego wchodzą
    kilkadziesiąt metrów dalej. Rzut takiego punktu przykleja się do ostatniego
    segmentu, więc jego „odsunięcie" jest w rzeczywistości odległością wzdłuż osi
    i nie ma nic wspólnego z międzytorzem. Takie punkty są liczone, ale oznaczone
    i wykluczane z pomiaru rozstawu.
    """
    total = SW.chainages(axis)[-1]
    rows = []
    for link in links:
        for x, y in link["points"]:
            point = CRS.laea3035_to_lambert72(x, y)
            chainage, offset, distance = project_signed(point, axis, frames)
            rows.append({"link": link["id"], "chainage_m": chainage,
                         "offset_m": offset, "distance_m": distance,
                         "beyond_axis": chainage <= 1e-3 or chainage >= total - 1e-3})
    return rows


def on_axis(rows):
    return [r for r in rows if not r["beyond_axis"]]


def histogram(rows, bin_m=1.0, lo=-20.0, hi=20.0):
    """Rozkład odsunięć — dowód, że filtr zadziałał, ma być widoczny, nie deklarowany.

    Zakres ±20 m obcina próbki z linków, które tylko przecinają korytarz osi
    (Arts-Loi -> Madou odchodzi na 470 m). Bez obcięcia histogram miałby setki
    jednoelementowych koszy i przestałby cokolwiek pokazywać.
    """
    bins = {}
    for row in rows:
        offset = row["offset_m"]
        if offset < lo or offset >= hi:
            continue
        key = math.floor(offset / bin_m) * bin_m
        bins[key] = bins.get(key, 0) + 1
    return [{"from_m": round(k, 3), "to_m": round(k + bin_m, 3), "count": v}
            for k, v in sorted(bins.items())]


def modes(rows, bin_m=1.0, min_share=MODE_MIN_SHARE):
    """Lokalne maksima rozkładu odsunięć — liczba modów jest testem filtra.

    Sam próg udziału nie wystarczy: dwa sąsiednie kosze rozjeżdżonego jednego moda
    (np. -1..0 i 0..1 dla toru osi) oba przekraczają każdy sensowny próg i dają
    fałszywe „cztery mody". Dlatego mod to kosz, który jest **ściśle większy** od
    obu sąsiadów i niesie co najmniej `min_share` próbek.
    """
    bins = histogram(rows, bin_m)
    if not bins:
        return []
    by_key = {b["from_m"]: b["count"] for b in bins}
    total = sum(by_key.values()) or 1
    out = []
    for edge, count in sorted(by_key.items()):
        if count / total < min_share:
            continue
        if count > by_key.get(round(edge - bin_m, 3), 0) and count > by_key.get(round(edge + bin_m, 3), 0):
            out.append({"from_m": edge, "to_m": round(edge + bin_m, 3), "count": count,
                        "share": round(count / total, 4)})
    return out


def summarise_side(rows):
    values = sorted(r["offset_m"] for r in rows)
    if not values:
        return {"samples": 0}
    return {
        "samples": len(values),
        "median_m": round(statistics.median(values), 3),
        "mean_m": round(statistics.fmean(values), 3),
        "stdev_m": round(statistics.pstdev(values), 3),
        "p05_m": round(values[int(0.05 * (len(values) - 1))], 3),
        "p95_m": round(values[int(0.95 * (len(values) - 1))], 3),
        "min_m": round(values[0], 3),
        "max_m": round(values[-1], 3),
    }


def measure_spacing(forward_rows, reverse_rows, running_max_m=RUNNING_OFFSET_MAX_M):
    """Rozstaw jako odległość median dwóch chmur po przeciwnych stronach osi."""
    forward_rows = on_axis(forward_rows)
    running = [r for r in on_axis(reverse_rows) if abs(r["offset_m"]) <= running_max_m]
    left = [r for r in running if r["offset_m"] < 0.0]
    right = [r for r in running if r["offset_m"] > 0.0]
    dominant, minor = (left, right) if len(left) >= len(right) else (right, left)
    axis_side = summarise_side(forward_rows)
    other_side = summarise_side(dominant)
    if not other_side.get("samples"):
        return {"status": "brak próbek toru przeciwnego"}
    spacing = abs(other_side["median_m"] - axis_side["median_m"])
    spread = sorted(abs(other_side[key] - axis_side["median_m"]) for key in ("p05_m", "p95_m"))
    return {
        "status": "ok",
        "running_offset_max_m": running_max_m,
        "axis_track": axis_side,
        "opposite_track": other_side,
        "wrong_side_samples": len(minor),
        "spacing_m": round(spacing, 3),
        "spacing_p05_p95_m": [round(spread[0], 3), round(spread[1], 3)],
        "half_spacing_m": round(spacing / 2.0, 3),
    }


def spacing_by_link(rows, links, nodes):
    """Rozstaw odcinek po odcinku — jedna liczba na 6,7 km ukrywałaby węzeł Beekkant."""
    label = {}
    for link in links:
        label[link["id"]] = (f"{nodes.get(link['from'], {}).get('station', link['from'])}"
                             f" -> {nodes.get(link['to'], {}).get('station', link['to'])}")
    out = []
    for link in links:
        values = sorted(r["offset_m"] for r in rows if r["link"] == link["id"])
        if not values:
            continue
        out.append({
            "link": link["id"],
            "section": label[link["id"]],
            "samples": len(values),
            "median_offset_m": round(statistics.median(values), 3),
            "min_offset_m": round(values[0], 3),
            "max_offset_m": round(values[-1], 3),
        })
    return out


# --- wejście/wyjście ----------------------------------------------------------

def load_alignment(path):
    with open(path, encoding="utf-8") as handle:
        document = json.load(handle)
    origin = document["origin_source_crs"]
    axis = [(p[0] + origin[0], p[1] + origin[1], 0.0) for p in document["points"]]
    stop_ids = [station["stop_id"] for station in document["stations"]]
    return document, axis, stop_ids


def download_url(registry_path=None):
    """URL bierzemy z rejestru źródeł, nie ze stałej w kodzie — inaczej rejestr
    przestaje być jedynym miejscem, w którym wolno zmienić adres pobierania."""
    registry = P.load_source_registry(registry_path or SOURCE_REGISTRY)
    return (registry.get(SOURCE_ID) or {}).get("download_url")


def read_gml_from_zip(content):
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        names = [n for n in archive.namelist() if n.endswith(".gml")]
        if GML_MEMBER in names:
            names = [GML_MEMBER]
        if not names:
            raise ValueError("archiwum nie zawiera pliku .gml")
        return archive.read(names[0]), names[0]


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Rozstaw torów metra wg INSPIRE Rails")
    parser.add_argument("--alignment", default=os.path.join("data", "track", "L1_A.json"))
    parser.add_argument("--out", default=os.path.join("build", "L1_A-track-spacing.json"))
    parser.add_argument("--gml-file", help="lokalny snapshot .gml zamiast pobierania")
    parser.add_argument("--url", help="nadpisuje download_url z rejestru źródeł")
    parser.add_argument("--timeout", type=float, default=90.0)
    return parser.parse_args(argv)


def _write(path, report):
    target = path if os.path.isabs(path) else os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(target) or ".", exist_ok=True)
    with open(target, "wb") as handle:
        handle.write(P.canonical_json(report))
    return target


def main(argv=None):
    args = parse_args(argv)
    alignment_path = (args.alignment if os.path.isabs(args.alignment)
                      else os.path.join(ROOT, args.alignment))
    document, axis, stop_ids = load_alignment(alignment_path)

    report = {
        "alignment": document.get("id", ""),
        "source_id": SOURCE_ID,
        "checked_at": P.utc_now_iso(),
        "source_crs": SOURCE_CRS,
        "target_crs": document.get("source_crs"),
        "caveat": "Pomiar dotyczy dwóch kierunkowych polilinii sieci INSPIRE, nie "
                  "przekroju konstrukcyjnego. Nie upoważnia sam z siebie do zmiany "
                  "track_offsets w tools/blender/profiles.py — to decyzja R-005.",
    }

    if args.gml_file:
        path = args.gml_file if os.path.isabs(args.gml_file) else os.path.join(ROOT, args.gml_file)
        with open(path, "rb") as handle:
            data = handle.read()
        report["source"] = {"kind": "snapshot lokalny", "member": os.path.basename(path),
                            "gml_sha256": P.sha256_bytes(data)}
    else:
        url = args.url or download_url()
        if not url:
            report["status"] = "brak download_url w rejestrze źródeł"
            print(f"[ROZSTAW] {report['status']}")
            _write(args.out, report)
            return 0
        try:
            content, final_url, headers = P.fetch_url(url, expected_format="zip",
                                                      timeout=args.timeout)
            data, member = read_gml_from_zip(content)
        except Exception as exc:
            report["status"] = "niedostępne"
            report["reason"] = str(exc)
            report["url"] = P.sanitize_url(url)
            _write(args.out, report)
            print(f"[ROZSTAW] źródło niedostępne: {exc}")
            return 0
        report["manifest"] = P.build_manifest(
            source_id=SOURCE_ID, requested_url=url, final_url=final_url, content=content,
            data_format="zip", crs=SOURCE_CRS, parser_version="inspire_rail/v1",
            artifact=data, mime_type=headers.get("Content-Type"),
            etag=headers.get("ETag"), last_modified=headers.get("Last-Modified"),
            transformations=["unzip", "parse_gml", "laea3035_to_lambert72"],
            input_sources=[SOURCE_ID])
        report["source"] = {"kind": "download", "member": member,
                            "gml_sha256": P.sha256_bytes(data)}

    parsed = parse_gml(data)
    report["features"] = {
        "links": len(parsed["links"]),
        "nodes": parsed["node_features"],
        "node_stop_codes": len(parsed["nodes"]),
        "duplicate_stop_codes": parsed["duplicate_stop_codes"],
        "lines": len(parsed["lines"]),
        "link_sequences": len(parsed["sequences"]),
    }
    report["metro_lines"] = [{"id": l["id"], "code": l["code"], "description": l["description"]}
                             for l in parsed["lines"] if (l["description"] or "").startswith(METRO)]
    report["metro_links"] = len(metro_links(parsed))
    report["topology"] = topology_health(parsed)
    report["validity"] = validity_window(parsed)
    report["vertical"] = {
        "status": "brak",
        "note": "srsDimension=2 w każdej geometrii; dataset nie odblokowuje T-112.",
    }

    chains = package_chains(parsed, stop_ids)
    report["chains"] = {
        "station_names": chains["station_names"],
        "missing_stops": chains["missing_stops"],
        "forward_paths": len(chains["forward"]),
        "reverse_paths": len(chains["reverse"]),
    }
    if len(chains["forward"]) != 1 or len(chains["reverse"]) != 1:
        report["status"] = "niejednoznaczne przejście po stacjach"
        _write(args.out, report)
        print(f"[ROZSTAW] {report['status']}: "
              f"{len(chains['forward'])} w przód, {len(chains['reverse'])} wstecz")
        return 0

    forward, reverse = chains["forward"][0], chains["reverse"][0]
    report["chains"]["forward_links"] = [l["id"] for l in forward]
    report["chains"]["reverse_links"] = [l["id"] for l in reverse]

    frames = SW.rmf_frames(axis)
    forward_rows = offsets_for(forward, axis, frames)
    reverse_rows = offsets_for(reverse, axis, frames)
    control = corridor_links(parsed, axis)
    control_rows = offsets_for(control, axis, frames)
    report["control_corridor"] = {
        "radius_m": CORRIDOR_M,
        "links": len(control),
        "links_in_chains": len(forward) + len(reverse),
        "note": "Selekcja po bliskości do osi wciąga linki linii 2/6 na odcinku "
                "Gare de l'Ouest — Beekkant; jest tu wyłącznie jako kontrola filtra.",
    }

    report["axis_agreement"] = summarise_side(
        [{"offset_m": r["distance_m"]} for r in on_axis(forward_rows)])
    report["beyond_axis_samples"] = sum(1 for r in forward_rows + reverse_rows if r["beyond_axis"])
    report["spacing"] = measure_spacing(forward_rows, reverse_rows)
    report["spacing_by_link"] = spacing_by_link(on_axis(reverse_rows), reverse, parsed["nodes"])
    report["histogram_filtered"] = histogram(on_axis(forward_rows) + on_axis(reverse_rows))
    report["histogram_corridor"] = histogram(on_axis(control_rows))
    report["modes_filtered"] = modes(on_axis(forward_rows) + on_axis(reverse_rows))
    report["modes_corridor"] = modes(on_axis(control_rows))
    report["status"] = report["spacing"]["status"]

    target = _write(args.out, report)
    _print_summary(report)
    print(f"[RAPORT] {target}")
    return 0


def _print_summary(report):
    validity = report["validity"]
    print(f"[ROZSTAW] obiekty: {report['features']['links']} linków, "
          f"{report['features']['nodes']} węzłów, {report['features']['lines']} linii; "
          f"metro: {report['metro_links']} linków")
    print(f"[ROZSTAW] okno ważności {validity.get('valid_from')} … "
          f"{validity.get('valid_to')} — {validity.get('status')}")
    topology = report["topology"]
    print(f"[ROZSTAW] referencje LinkSequence: {topology['resolved']}/"
          f"{topology['link_references']} rozwiązanych")
    agreement = report["axis_agreement"]
    print(f"[ROZSTAW] zgodność z osią (kierunek osi): mediana {agreement['median_m']} m, "
          f"P95 {agreement['p95_m']} m, maks. {agreement['max_m']} m")
    spacing = report["spacing"]
    if spacing["status"] == "ok":
        print(f"[ROZSTAW] tor osi: mediana {spacing['axis_track']['median_m']} m "
              f"({spacing['axis_track']['samples']} próbek); tor przeciwny: "
              f"mediana {spacing['opposite_track']['median_m']} m "
              f"({spacing['opposite_track']['samples']} próbek)")
        print(f"[ROZSTAW] rozstaw {spacing['spacing_m']} m "
              f"(P05–P95 {spacing['spacing_p05_p95_m'][0]}–"
              f"{spacing['spacing_p05_p95_m'][1]} m), pół rozstawu "
              f"{spacing['half_spacing_m']} m")
    print(f"[ROZSTAW] mody rozkładu: filtr topologiczny {len(report['modes_filtered'])}, "
          f"selekcja korytarzowa {len(report['modes_corridor'])}")
    print(f"[ROZSTAW] {report['caveat']}")


if __name__ == "__main__":
    sys.exit(main())
