#!/usr/bin/env python3
"""Rozstrzyga, czy odcinek osi biegnie w tunelu, czy poza nim — dwoma źródłami naraz.

    python3 tools/track/surface_sections.py --alignment data/track/L1_A.json \
        --out build/L1_A-surface.json

Problem, który to rozwiązuje: `data/network/sources.json` mówi wprost, że pola poziomu
w UrbIS **wymagają interpretacji**, a dataset nigdzie nie definiuje, czym `niveau = '0'`
różni się od `niveau = '-'`. Raport `reports/packages-BF-alignment.md` §9 policzył
trafienia w poligony `niveau = 0` i **świadomie nie postawił wniosku**, bo jedno źródło
bez definicji pola nie jest podstawą do twierdzenia o terenie.

Tutaj dochodzi drugie, niezależne źródło: OSM. `railway=subway` ma tam tag `tunnel`
(oraz `layer`), nadawany przez zupełnie innych ludzi, w innym procesie, z innych
przesłanek. Zgodność dwóch niezależnych źródeł jest argumentem; jedno źródło nim nie
jest. Narzędzie **mierzy zgodność**, a nie zakłada jej — macierz rozbieżności jest
częścią wyniku i to ona decyduje, czy wolno cokolwiek twierdzić.

Metoda:

1. dla wybranych kilometraży osi bierzemy punkt i pytamy UrbIS, w jakim poligonie leży;
2. dla tego samego punktu pobieramy z OSM mały wycinek mapy i szukamy **najbliższego**
   way'a `railway=subway` — nie „jakiegoś w okolicy", bo w węzłach przesiadkowych
   w jednym kwadracie leży kilka linii na różnych poziomach;
3. porównujemy: `niveau = 0` wobec braku `tunnel=yes`.

Sondowanie zamiast pełnego pobrania jest świadome: Overpass bywa niedostępny całymi
godzinami, a `api.openstreetmap.org/map` ma twardy limit obszaru. Gęstość sond dobiera
się osobno w przedziałach `niveau = 0` (krótkie, więc gęściej) i poza nimi.
"""
import argparse
import json
import math
import os
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "tools", "data"))

import crosscheck_alignment as CC  # noqa: E402
import crs as CRS  # noqa: E402
import osm_tile_cache as PAMIEC  # noqa: E402
import provenance as P  # noqa: E402

URBIS_URL = CC.URBIS_URL
OSM_MAP_URL = "https://api.openstreetmap.org/api/0.6/map?bbox=%s"
# ~130 m w każdą stronę. Mniejszy kwadrat gubi way'e, których węzły leżą poza nim;
# większy zaczyna łapać sąsiednie linie i rośnie ryzyko przekroczenia limitu API.
PROBE_HALF_DEG = 0.0012
# Sonda dalej niż to od osi nie opisuje tego odcinka — w OSM tor jest mapowany
# pojedynczo, więc kilkanaście metrów to norma, ale sto metrów to już inna linia.
NEAREST_MAX_M = 60.0
DEFAULT_STEP_INSIDE_M = 300.0
DEFAULT_STEP_OUTSIDE_M = 800.0
# Komórka indeksu przestrzennego dla pełnego snapshotu Overpassa.
OSM_GRID_CELL_M = 50.0


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Zgodność UrbIS niveau z tagiem tunnel w OSM wzdłuż osi")
    parser.add_argument("--alignment", default=os.path.join("data", "track", "L1_A.json"))
    parser.add_argument("--out", required=True)
    parser.add_argument("--urbis-file", help="lokalny snapshot warstwy UrbIS Metro")
    parser.add_argument("--osm-dir", default=PAMIEC.DOMYSLNY_KATALOG,
                        help="katalog WSPÓLNEJ pamięci kafli, kluczowanej po bboxie — ten "
                             "sam prostokąt pobiera się raz, także gdy pyta o niego "
                             "tools/track/crosscheck_alignment.py")
    parser.add_argument("--osm-refresh", action="store_true",
                        help="pomiń pamięć i pobierz kwadraty na nowo, nadpisując ją — "
                             "pamięć, której nie da się ominąć, jest gorsza od jej braku")
    parser.add_argument("--osm-file", help="snapshot way'ów railway=subway z całą siecią; wtedy "
                                           "klasyfikowany jest KAŻDY punkt osi, a nie tylko "
                                           "sondy. Overpass albo droga zapasowa "
                                           "crosscheck_alignment.py --osm-source osm-api")
    parser.add_argument("--step-inside-m", type=float, default=DEFAULT_STEP_INSIDE_M)
    parser.add_argument("--step-outside-m", type=float, default=DEFAULT_STEP_OUTSIDE_M)
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--skip-osm", action="store_true",
                        help="tylko UrbIS; sonda OSM zostaje zapisana jako niewykonana")
    return parser.parse_args(argv)


def chainage_of(points):
    chain = [0.0]
    for a, b in zip(points, points[1:]):
        chain.append(chain[-1] + math.dist(a, b))
    return chain


def urbis_rings(payload):
    """Pierścienie MT/MS w Lambert 72 razem z polem `niveau` i nazwą."""
    rings = []
    for feature in payload.get("features", []):
        properties = feature.get("properties") or {}
        if properties.get("type") not in ("MT", "MS"):
            continue
        for ring in CC.polygon_rings(feature.get("geometry") or {}):
            rings.append({
                "ring": [CRS.wgs84_to_lambert72(x, y) for x, y, *_ in ring],
                "niveau": str(properties.get("niveau")),
                "kind": properties.get("type"),
                "name": properties.get("name_fr") or properties.get("name_nl"),
            })
    return rings


def urbis_at(point, rings):
    for entry in rings:
        if CC.point_in_ring(point, entry["ring"]):
            return entry
    return None


# Sonda bliżej niż to od granicy przedziału `niveau = 0` opisuje okolice portalu,
# a nie odcinek. Przy portalu oba źródła mają prawo różnić się o kilkanaście metrów
# i taka rozbieżność nic nie mówi o tym, czy odcinek biegnie w tunelu.
PORTAL_HALO_M = 60.0


def range_position(chainage, ranges, halo_m=None):
    """Gdzie leży sonda wobec przedziałów `niveau = 0`: w środku, przy portalu, poza.

    **`halo_m=None` zamiast `halo_m=PORTAL_HALO_M` — przepisane 09.09.2026 (6.D61),
    a nie dopisane obok, i to jest zmiana zachowania, nie kosmetyka.** Wartość
    domyślna argumentu wiąże się w chwili definicji funkcji, więc podmiana stałej
    `PORTAL_HALO_M` w module **nie docierała tutaj wcale**: kontrola negatywna,
    której żąda pole „Skończone, gdy" tej pozycji — „zdjęcie halo, czyli
    `PORTAL_HALO_M = 0`" — była z tego powodu **niewykonalna**, a próba jej
    wykonania dawała niezmienione 2 punkty w halo. Odczyt w ciele funkcji sprawia,
    że stała jest jednym miejscem także w czasie wykonania, a nie tylko w zapisie.
    """
    if halo_m is None:
        halo_m = PORTAL_HALO_M
    for low, high in ranges:
        if low - halo_m <= chainage <= high + halo_m:
            if abs(chainage - low) <= halo_m or abs(chainage - high) <= halo_m:
                return "portal"
            return "srodek"
    return "poza"


def probe_chainages(chain, inside_flags, step_inside_m, step_outside_m, ranges=()):
    """Kilometraże sond: gęściej tam, gdzie UrbIS twierdzi `niveau = 0`.

    Dwie rzeczy, obie wymuszone przez pomiar, nie przez wygodę:

    * przedziały `niveau = 0` mają po kilkaset metrów, więc stały krok „co 800 m"
      potrafi minąć cały odcinek i zostawić niesprawdzonym dokładnie ten odcinek,
      o który chodzi — dlatego krok zależy od flagi;
    * **środek każdego przedziału jest sondowany zawsze**. Pierwszy przebieg tego
      nie robił i trafiał sondą w pierwszy punkt po wejściu w przedział, czyli tuż
      za portal: wszystkie trzy rozbieżności między UrbIS a OSM (pakiety A, D i F)
      wypadły wtedy w kilometrażu 688-704 m, o kilkanaście metrów od granicy.
      Twierdzenie „ten odcinek nie jest w tunelu" trzeba sprawdzać w jego środku.
    """
    picks = []
    last_inside = last_any = -1e9
    for value, inside in zip(chain, inside_flags):
        step = step_inside_m if inside else step_outside_m
        reference = last_inside if inside else last_any
        if value - reference >= step or value - last_any >= step_outside_m:
            picks.append((value, inside))
            last_any = value
            if inside:
                last_inside = value
    for low, high in ranges:
        middle = 0.5 * (low + high)
        if all(abs(middle - value) > 1e-6 for value, _flag in picks):
            picks.append((middle, True))
    return sorted(picks)


def point_at(points, chain, target):
    for (a, b), (sa, sb) in zip(zip(points, points[1:]), zip(chain, chain[1:])):
        if sa <= target <= sb and sb > sa:
            t = (target - sa) / (sb - sa)
            return (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]))
    return points[-1]


def fetch_osm_box(lon, lat, half_deg, timeout, cache_dir=None, refresh=False, licznik=None):
    """Kwadrat sondy z API OSM, przez WSPÓLNĄ pamięć kafli (`osm_tile_cache`).

    **PRZEPISANE 09.09.2026 (6.D62), a nie dopisane obok.** Poprzednia wersja brała
    `cache_path` gotowy z wołającego, a wołający budował go z **nazwy osi
    i kilometrażu** — więc ten sam prostokąt pytany przy innej osi albo przez
    `tools/track/crosscheck_alignment.py` schodził z sieci drugi raz. Klucz jest
    teraz bboxem i niczym więcej, a katalog ten sam dla obu narzędzi.
    """
    bbox = (lon - half_deg, lat - half_deg, lon + half_deg, lat + half_deg)
    zapytanie = "%.5f,%.5f,%.5f,%.5f" % bbox
    return PAMIEC.wez_kafel(bbox, OSM_MAP_URL % zapytanie, timeout,
                            katalog=cache_dir, wymus=refresh, licznik=licznik)


def nearest_subway(content, point):
    """Najbliższy way `railway=subway` wraz z jego tagami poziomu.

    Bierzemy najbliższy, a nie pierwszy z brzegu: w rejonie Beekkant w jednym kwadracie
    leży osiem way'ów na czterech poziomach i „jakiś w okolicy" nie odpowiada na pytanie
    o ten odcinek.
    """
    root = ET.fromstring(content)
    nodes = {n.get("id"): (float(n.get("lon")), float(n.get("lat")))
             for n in root.findall("node")}
    best, best_distance = None, None
    for way in root.findall("way"):
        tags = {t.get("k"): t.get("v") for t in way.findall("tag")}
        if tags.get("railway") != "subway":
            continue
        coords = [nodes[nd.get("ref")] for nd in way.findall("nd") if nd.get("ref") in nodes]
        if len(coords) < 2:
            continue
        metric = [CRS.wgs84_to_lambert72(x, y) for x, y in coords]
        distance = min(CC._distance_to_polyline(point, [a, b])
                       for a, b in zip(metric, metric[1:]))
        # Porównujemy odległość SUROWĄ, a zaokrąglamy dopiero to, co idzie do raportu.
        # Przy `distance < best["distance_m"]` po prawej stronie stała wartość już
        # zaokrąglona do 2 miejsc, więc way dalszy o mniej niż pół centymetra wygrywał
        # z bliższym, a wynik zależał od kolejności way'ów w dokumencie.
        if best is None or distance < best_distance:
            best_distance = distance
            best = {"way_id": way.get("id"), "distance_m": round(distance, 2),
                    "tunnel": tags.get("tunnel"), "layer": tags.get("layer"),
                    "bridge": tags.get("bridge")}
    return best


#: Etykieta snapshotu bez własnej deklaracji pochodzenia. Takie pliki powstały przed
#: 6.B52, gdy jedyną drogą do całej sieci był Overpass — ale zapisanie tu wprost
#: „overpass" byłoby przypisaniem źródła NA PODSTAWIE MILCZENIA pliku, a to jest
#: dokładnie ten błąd, którego zakazuje `docs/07-open-data-research.md`.
SNAPSHOT_SOURCE_UNDECLARED = "snapshot bez deklaracji osm_source"


def snapshot_source_label(payload):
    """Skąd pochodzi snapshot podany przez `--osm-file`, wprost z jego deklaracji.

    Do 6.B52 to pole niosło stałą `"overpass snapshot"` niezależnie od zawartości
    pliku. Odkąd `crosscheck_alignment.py --osm-source osm-api` potrafi zbudować
    snapshot z surowego API OSM, ta stała była już nazwaniem złego źródła — i to
    w polu, którego jedynym zadaniem jest powiedzieć, skąd są dane.
    """
    declared = payload.get("osm_source")
    return f"snapshot: {declared}" if declared else SNAPSHOT_SOURCE_UNDECLARED


def overpass_segments(payload):
    """Odcinki `railway=subway` z Overpassa w Lambert 72, z tagami poziomu.

    Overpass daje całą sieć w jednym zapytaniu, więc klasyfikacja przestaje być
    sondowaniem: każdy punkt osi dostaje najbliższy way. Sondowanie przez
    `api.openstreetmap.org/map` zostaje jako droga awaryjna — w dniu pomiaru
    Overpass był niedostępny przez ponad godzinę na czterech instancjach.
    """
    segments = []
    for element in payload.get("elements", []):
        if element.get("type") != "way" or not element.get("geometry"):
            continue
        tags = element.get("tags") or {}
        if tags.get("railway") != "subway":
            continue
        points = [CRS.wgs84_to_lambert72(n["lon"], n["lat"]) for n in element["geometry"]]
        for a, b in zip(points, points[1:]):
            segments.append((a, b, str(element.get("id")), tags.get("tunnel"), tags.get("layer")))
    return segments


def segment_grid(segments, cell_m=OSM_GRID_CELL_M):
    index = {}
    for i, (a, b, *_rest) in enumerate(segments):
        x0, x1 = sorted((a[0], b[0]))
        y0, y1 = sorted((a[1], b[1]))
        for cx in range(int(x0 // cell_m), int(x1 // cell_m) + 1):
            for cy in range(int(y0 // cell_m), int(y1 // cell_m) + 1):
                index.setdefault((cx, cy), []).append(i)
    return index


def nearest_segment(point, segments, index, cell_m=OSM_GRID_CELL_M, rings=2):
    """Najbliższy odcinek metra wraz z tagami — bez indeksu byłoby to O(n*m)."""
    cx, cy = int(point[0] // cell_m), int(point[1] // cell_m)
    candidates = set()
    for i in range(-rings, rings + 1):
        for j in range(-rings, rings + 1):
            candidates.update(index.get((cx + i, cy + j), ()))
    best, best_distance = None, None
    for i in candidates:
        a, b, way_id, tunnel, layer = segments[i]
        distance = CC._distance_to_polyline(point, [a, b])
        # jak w `nearest_subway`: surowa odległość rozstrzyga, zaokrąglona tylko raportuje
        if best is None or distance < best_distance:
            best_distance = distance
            best = {"way_id": way_id, "distance_m": round(distance, 2),
                    "tunnel": tunnel, "layer": layer, "bridge": None}
    return best


def classify(urbis_entry, osm_entry):
    """Trzy stany, nie dwa: `nieznane` jest wynikiem, a nie okazją do zgadywania."""
    urbis = None
    if urbis_entry is not None:
        urbis = "poza_tunelem" if urbis_entry["niveau"] == "0" else "tunel"
    osm = None
    if osm_entry is not None and osm_entry["distance_m"] <= NEAREST_MAX_M:
        osm = "tunel" if osm_entry.get("tunnel") in ("yes", "building_passage",
                                                     "covered") else "poza_tunelem"
    if urbis is None and osm is None:
        return "nieznane", urbis, osm
    if urbis is None or osm is None:
        return "jedno_zrodlo", urbis, osm
    return ("zgodne" if urbis == osm else "sprzeczne"), urbis, osm


def survey(alignment_path, args):
    document, points = CC.load_alignment(alignment_path)
    chain = chainage_of(points)

    urbis_payload, urbis_source = None, {}
    if args.urbis_file:
        with open(args.urbis_file, "rb") as handle:
            content = handle.read()
        urbis_source = {"status": "ok", "source": "snapshot lokalny",
                        "file": os.path.basename(args.urbis_file),
                        "file_sha256": P.sha256_bytes(content)}
        urbis_payload = json.loads(content.decode("utf-8"))
    else:
        try:
            content, url, _headers = P.fetch_url(URBIS_URL, expected_format="json",
                                                 timeout=args.timeout)
            urbis_payload = json.loads(content.decode("utf-8"))
            urbis_source = {"status": "ok", "source": "ogc-features",
                            "url": P.sanitize_url(url),
                            "file_sha256": P.sha256_bytes(content)}
        except Exception as exc:
            urbis_source = {"status": "niedostępne", "reason": str(exc)}

    rings = urbis_rings(urbis_payload) if urbis_payload else []
    hits = [urbis_at(p, rings) for p in points]
    inside = [h is not None and h["niveau"] == "0" for h in hits]

    # Przedziały `niveau = 0` liczone RAZ, przed obiema ścieżkami. Do 6.D61 stały
    # niżej, czyli za ścieżką pełnego pokrycia — i to jest cała przyczyna usterki,
    # którą ta pozycja zamyka: ścieżka pełnego pokrycia nie miała ich skąd wziąć,
    # więc nie liczyła `range_position` wcale i podawała JEDEN licznik zgodności
    # tam, gdzie ścieżka sond podaje dwa.
    ranges = CC.chainage_ranges(points, inside)

    # Ścieżka pełnego pokrycia: snapshot Overpassa niesie CAŁĄ sieć, więc każdy punkt
    # osi dostaje odpowiedź. Sondowanie jest wtedy zbędne i byłoby gorszą wersją tego
    # samego pomiaru.
    full = None
    if args.osm_file:
        with open(args.osm_file, "rb") as handle:
            content = handle.read()
        payload = json.loads(content.decode("utf-8"))
        segments = overpass_segments(payload)
        index = segment_grid(segments)
        rows = []
        for point, chainage, hit in zip(points, chain, hits):
            entry = nearest_segment(point, segments, index)
            verdict, urbis_state, osm_state = classify(hit, entry)
            rows.append({"chainage_m": round(chainage, 1), "osm": entry,
                         "range_position": range_position(chainage, ranges),
                         "verdict": verdict, "urbis_state": urbis_state,
                         "osm_state": osm_state})
        matrix, counts = {}, {}
        for row in rows:
            key = f"urbis={row['urbis_state']}|osm={row['osm_state']}"
            matrix[key] = matrix.get(key, 0) + 1
            counts[row["verdict"]] = counts.get(row["verdict"], 0) + 1
        comparable = [r for r in rows if r["verdict"] in ("zgodne", "sprzeczne")]
        # Rozbieżność PRZY PORTALU nic nie mówi — tak stoi przy `PORTAL_HALO_M` od
        # dnia, w którym ta stała powstała. Ścieżka sond odsiewała je od początku,
        # ścieżka pełnego pokrycia do 6.D61 nie odsiewała ich wcale, a to jej liczba
        # jest cytowana w raportach.
        away = [r for r in comparable if r["range_position"] != "portal"]
        in_halo = [r for r in rows if r["range_position"] == "portal"]
        surface = [r["chainage_m"] for r in rows if r["osm_state"] == "poza_tunelem"]
        full = {
            "source": {"status": "ok", "source": snapshot_source_label(payload),
                       "declared_osm_source": payload.get("osm_source"),
                       "file": os.path.basename(args.osm_file),
                       "file_sha256": P.sha256_bytes(content),
                       "segments": len(segments),
                       "attribution": "© OpenStreetMap contributors, ODbL 1.0"},
            "points": len(rows),
            "matrix": dict(sorted(matrix.items())),
            "verdicts": dict(sorted(counts.items())),
            "agreement_pct": None if not comparable else round(
                100.0 * sum(1 for r in comparable if r["verdict"] == "zgodne")
                / len(comparable), 1),
            "agreement_off_portal_pct": None if not away else round(
                100.0 * sum(1 for r in away if r["verdict"] == "zgodne") / len(away), 1),
            "comparable_points": len(comparable),
            "comparable_off_portal": len(away),
            "points_in_halo": len(in_halo),
            "portal_halo_m": PORTAL_HALO_M,
            "osm_surface_points": len(surface),
            "osm_surface_pct": round(100.0 * len(surface) / max(1, len(rows)), 1),
            "osm_surface_ranges_m": CC.chainage_ranges(
                points, [r["osm_state"] == "poza_tunelem" for r in rows]),
            "osm_max_distance_m": round(max(
                (r["osm"]["distance_m"] for r in rows if r["osm"]), default=0.0), 2),
            "contradictions": [r for r in rows if r["verdict"] == "sprzeczne"],
        }

    probes = []
    counts = {}
    licznik_kafli = PAMIEC.Licznik()
    for chainage, is_inside in probe_chainages(chain, inside, args.step_inside_m,
                                               args.step_outside_m, ranges):
        point = point_at(points, chain, chainage)
        entry = urbis_at(point, rings)
        record = {
            "chainage_m": round(chainage, 1),
            "range_position": range_position(chainage, ranges),
            "urbis": None if entry is None else
                     {"niveau": entry["niveau"], "kind": entry["kind"], "name": entry["name"]},
            "osm": None,
        }
        if not args.skip_osm:
            lon, lat = CRS.lambert72_to_wgs84(*point)
            content, origin, reason = fetch_osm_box(lon, lat, PROBE_HALF_DEG,
                                                    args.timeout, args.osm_dir,
                                                    args.osm_refresh, licznik_kafli)
            if content is None:
                record["osm_error"] = reason
            else:
                record["osm"] = nearest_subway(content, point)
                record["osm_origin"] = origin
        verdict, urbis_state, osm_state = classify(record["urbis"] and entry, record["osm"])
        record.update({"verdict": verdict, "urbis_state": urbis_state, "osm_state": osm_state})
        counts[verdict] = counts.get(verdict, 0) + 1
        probes.append(record)

    matrix = {}
    for record in probes:
        key = f"urbis={record['urbis_state']}|osm={record['osm_state']}"
        matrix[key] = matrix.get(key, 0) + 1

    comparable = [r for r in probes if r["verdict"] in ("zgodne", "sprzeczne")]
    away = [r for r in comparable if r["range_position"] != "portal"]
    agree = counts.get("zgodne", 0)
    return {
        "alignment_id": document["id"],
        "axis_length_m": round(chain[-1], 2),
        "checked_at": P.utc_now_iso(),
        "urbis_source": urbis_source,
        "osm_source": {"status": "pominięte" if args.skip_osm else "ok",
                       "url": P.sanitize_url(OSM_MAP_URL % "BBOX"),
                       "probe_half_deg": PROBE_HALF_DEG,
                       "nearest_max_m": NEAREST_MAX_M,
                       "tile_cache": {"dir": args.osm_dir, "refresh": bool(args.osm_refresh),
                                      **licznik_kafli.jako_slownik()},
                       "attribution": "© OpenStreetMap contributors, ODbL 1.0"},
        "niveau0_points": sum(inside),
        "niveau0_pct": round(100.0 * sum(inside) / max(1, len(points)), 1),
        "niveau0_chainage_ranges_m": CC.chainage_ranges(points, inside),
        "probe_count": len(probes),
        "verdicts": dict(sorted(counts.items())),
        "matrix": dict(sorted(matrix.items())),
        "agreement_pct": None if not comparable else round(100.0 * agree / len(comparable), 1),
        "agreement_off_portal_pct": None if not away else round(
            100.0 * sum(1 for r in away if r["verdict"] == "zgodne") / len(away), 1),
        "comparable_probes": len(comparable),
        "comparable_off_portal": len(away),
        "probes": probes,
        "full_coverage": full,
        "note": "Zgodność liczona tylko na sondach, gdzie oba źródła coś mówią. "
                "Sonda z jednym źródłem nie jest ani potwierdzeniem, ani zaprzeczeniem.",
    }


def main(argv=None):
    args = parse_args(argv)
    path = args.alignment if os.path.isabs(args.alignment) else os.path.join(ROOT, args.alignment)
    report = survey(path, args)
    out = args.out if os.path.isabs(args.out) else os.path.join(ROOT, args.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=1, sort_keys=True)
        handle.write("\n")
    print(f"[POWIERZCHNIA] {report['alignment_id']}: {report['probe_count']} sond, "
          f"niveau=0 na {report['niveau0_points']} punktach ({report['niveau0_pct']}%)")
    pamiec = (report.get("osm_source") or {}).get("tile_cache")
    if pamiec:
        print(f"[OSM-KAFLE] {pamiec['tiles_from_cache']} z pamięci "
              f"({pamiec['bytes_from_cache']} B), {pamiec['tiles_downloaded']} pobranych "
              f"({pamiec['bytes_downloaded']} B), katalog {pamiec['dir']}"
              + (" (POMINIĘTA, --osm-refresh)" if pamiec["refresh"] else ""))
    for key, value in report["matrix"].items():
        print(f"[POWIERZCHNIA]   {key}: {value}")
    print(f"[POWIERZCHNIA] zgodność źródeł: {report['agreement_pct']}% "
          f"na {report['comparable_probes']} sondach; poza portalami "
          f"{report['agreement_off_portal_pct']}% na {report['comparable_off_portal']} "
          f"({report['verdicts']})")
    for record in report["probes"]:
        if record["verdict"] == "sprzeczne":
            print(f"[POWIERZCHNIA] SPRZECZNE @{record['chainage_m']} m "
                  f"({record['range_position']}): urbis={record['urbis_state']} "
                  f"osm={record['osm_state']} ({record['osm']})")
    full = report.get("full_coverage")
    if full:
        print(f"[POWIERZCHNIA] PEŁNE POKRYCIE, ŹRÓDŁO = {full['source']['source']}: "
              f"{full['points']} punktów, {full['source']['segments']} odcinków metra")
        for key, value in full["matrix"].items():
            print(f"[POWIERZCHNIA]   {key}: {value}")
        roznica = (None if full["agreement_pct"] is None
                   or full["agreement_off_portal_pct"] is None
                   else round(full["agreement_off_portal_pct"] - full["agreement_pct"], 1))
        print(f"[POWIERZCHNIA] zgodność {full['agreement_pct']}% na "
              f"{full['comparable_points']} punktach; poza portalami "
              f"{full['agreement_off_portal_pct']}% na {full['comparable_off_portal']}; "
              f"punktów w halo portalu ({full['portal_halo_m']} m): "
              f"{full['points_in_halo']}; RÓŻNICA dwóch liczb: {roznica} pkt")
        print(f"[POWIERZCHNIA] OSM bez tunelu na "
              f"{full['osm_surface_points']} ({full['osm_surface_pct']}%), "
              f"przedziały {full['osm_surface_ranges_m']}")
        print(f"[POWIERZCHNIA] najdalszy way metra od osi: {full['osm_max_distance_m']} m")
    print(f"[POWIERZCHNIA] zapisano {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
