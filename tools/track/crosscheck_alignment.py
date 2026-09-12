#!/usr/bin/env python3
"""Porównuje gotową oś z niezależnymi źródłami: UrbIS/Brussels Mobility i OSM.

    python3 tools/track/crosscheck_alignment.py --alignment data/track/L1_A.json \
        --out build/L1_A-crosscheck.json

Rozbieżności są **liczone i zapisywane**, nigdy uśredniane ani „poprawiane".
Niedostępność źródła jest wynikiem, a nie powodem do pominięcia kontroli: zapisujemy
kod HTTP i komunikat, żeby raport mówił, czego nie dało się sprawdzić i dlaczego.

UrbIS `Metro` to **poligony** tuneli (MT) i stacji (MS), a nie oś toru, więc jedyną
sensowną miarą jest, jaka część osi mieści się w tych poligonach.

DWIE DROGI DO OSM, I WYBIERA SIĘ JE JAWNIE (`--osm-source`). Overpass jest drogą
**podstawową** i tak stoi w `docs/07-open-data-research.md`: jedno zapytanie, filtr
`railway=subway` wykonany po stronie serwera. `api.openstreetmap.org/api/0.6/map` jest
drogą **zapasową** na wypadek, gdy Overpass milczy — surowe API OSM nie ma języka
zapytań, więc odsyła CAŁĄ zawartość prostokąta, a filtr wykonuje się lokalnie. Różnica
nie jest kosmetyczna i dlatego nie ma tu przełączenia automatycznego: raport, który nie
mówi, z którego z tych dwóch źródeł wziął liczby, jest w tym projekcie bezwartościowy.
Wypis nazywa źródło z osobna dla każdego przebiegu, a `osm.source` w pliku wyniku
zapisuje to samo maszynowo.
"""
import argparse
import json
import math
import os
import re
import sys
import time
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "tools", "data"))

import crs as CRS  # noqa: E402
import provenance as P  # noqa: E402
import osm_tile_cache as PAMIEC  # noqa: E402

URBIS_URL = ("https://data.mobility.brussels/geoserver/ogc/features/v1/collections/"
             "bm_public_transport%3AMetro/items?limit=10000&f=application/json")
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
OSM_COVERAGE_RADIUS_M = 50.0
# Bbox zapytania Overpassa liczony jest z **samej osi**, a nie wpisany na stałe:
# stały bbox pnia (50.835,4.310,50.855,4.400) nie obejmuje ani Stockel, ani Erasme,
# ani Roi Baudouin, więc dla pakietów B–F dawałby ciche zero pokrycia.
OVERPASS_BBOX_MARGIN_M = 300.0
OVERPASS_TEMPLATE = """[out:json][timeout:60];
(
  way["railway"="subway"](%.5f,%.5f,%.5f,%.5f);
);
out geom;
"""

# --- droga zapasowa: surowe API OSM ------------------------------------------------
#
# Powód, dla którego to w ogóle istnieje, jest zmierzony, nie przewidziany: 08.09.2026
# `overpass-api.de/api/status` odpowiadał z tego kontenera **HTTP 000** po 9,76 s
# (`Recv failure: Connection reset by peer`, proxy zapisało `ws_closed_mid_exchange`
# dla `overpass-api.de:443`), a `api.openstreetmap.org/api/0.6/capabilities` — HTTP 200
# po 0,72 s. Jedno źródło leży, drugie stoi; „brak sieci" nie jest stanem
# zero-jedynkowym.
OSM_API_URL = "https://api.openstreetmap.org/api/0.6/map"
#: Całe zapytanie drogi zapasowej — SAM PROSTOKĄT. Wyciągnięte ze środka `osm_api_ways`
#: przy 6.D53, żeby „ta końcówka nie filtruje po stronie serwera" dało się przeczytać
#: z kodu zamiast wpisać drugi raz z ręki: brak nazwy taga w tym napisie JEST tym faktem.
OSM_API_QUERY_FMT = "bbox=%.5f,%.5f,%.5f,%.5f"
#: Nazwy dróg dla `--osm-source`. Napisy, nie flagi logiczne: wchodzą wprost do wypisu
#: i do pola `osm.source` w pliku wyniku, więc czytający widzi, co pobrano.
OSM_SOURCE_OVERPASS = "overpass"
OSM_SOURCE_API = "osm-api"
#: Bok kafla siatki w stopniach. Zmierzone 08.09.2026 na środku pakietu D
#: (4,41500 E / 50,82200 N): kafel 0,006° zwraca **8012 węzłów i 2,39 MB**, czyli
#: sześciokrotny zapas do twardego limitu API. Dobór jest tu POMIAREM, a nie próbami:
#: całe bbox pakietu D w jednym wywołaniu daje `HTTP 400 — You requested too many
#: nodes (limit is 50000)` po 2,77 s, kafel 0,0012° daje 1259 węzłów (za drobny, bo
#: mnoży liczbę żądań), kafel 0,0050° — 19 320 węzłów i 5,64 MB.
OSM_API_TILE_DEG = 0.006
#: Twardy limit `/api/0.6/map` po stronie OSM, zapisany po to, żeby komunikat odmowy
#: dał się rozpoznać jako „kafel za duży", a nie jako „źródło niedostępne".
#:
#: **Od 6.D53 ta sama liczba stoi też w `data/network/sources.json`** i pilnuje tego
#: bramka `test_osm_api_fallback.test_limit_koncowki_w_rejestrze_zgadza_sie_z_kodem`.
#: Stała ZOSTAJE w kodzie, a nie przenosi się do rejestru: narzędzie musi rozpoznać
#: odmowę także wtedy, gdy rejestru nie ma pod ręką (przebieg z kopii, z kafla w pamięci
#: podręcznej, z innego drzewa). Dwie liczby o jednym fakcie są tu więc świadome —
#: i dlatego mają strażnika, zamiast zostać bez niego.
OSM_API_NODE_LIMIT = 50000

#: Rejestr źródeł. Czytany WYŁĄCZNIE przez `koncowki_osm_z_rejestru` niżej; sam przebieg
#: krzyżowej kontroli go nie potrzebuje i nie ma się wywracać, gdy pliku nie ma.
SOURCES_JSON = os.path.join(ROOT, "data", "network", "sources.json")


def koncowki_osm_z_rejestru(sciezka=SOURCES_JSON):
    """Końcówki OSM z rejestru źródeł, po `id`. Podnosi `KeyError`, gdy wpisu nie ma.

    **Po co (6.D53).** Do tej pozycji rejestr opisywał dostęp do OSM dwoma słowami
    (`osm_or_overpass`, `endpoint-dependent`) i **żadną liczbą**: nie mówił ani o limicie
    obszaru, ani o tym, że jedna z dwóch dróg filtruje po stronie serwera, a druga nie.
    Liczba o źródle stała przez to w kodzie narzędzia, a nie w rejestrze źródeł.
    """
    with open(sciezka, encoding="utf-8") as uchwyt:
        rejestr = json.load(uchwyt)
    wpisy = [w for w in rejestr["sources"] if w["id"] == "openstreetmap"]
    if len(wpisy) != 1:
        raise KeyError(f"{sciezka}: wpisów `openstreetmap` jest {len(wpisy)}, ma być jeden")
    koncowki = wpisy[0]["access"].get("endpoints")
    if not koncowki:
        raise KeyError(f"{sciezka}: wpis `openstreetmap` nie wymienia końcówek "
                       "(`access.endpoints`) — 6.D53")
    return {k["id"]: k for k in koncowki}


#: Wartość `timeout` z zapytania Overpassa, wyjęta z szablonu, a nie wpisana drugi raz.
TIMEOUT_W_SZABLONIE = re.compile(r"\[timeout:(\d+)\]")


def pary_rejestr_kod(sciezka=SOURCES_JSON):
    """`[(co, z_rejestru, z_kodu)]` — każda para NAPRAWDĘ dwustronna.

    Pole „Weryfikacja" pozycji 6.D53 żąda wypisu, w którym obie liczby stoją **obok
    siebie**; zdanie „zgadza się" byłoby tu tym, czym `assert True` — wyglądałoby
    identycznie przy liczbach zgodnych i przy rozjechanych.

    **Żadna para nie zestawia `None` z `None`.** Pierwsza wersja tej funkcji wypisywała
    dla Overpassa „rejestr None, kod None (zgodne)" — porównanie dwóch nieobecności,
    czyli zdanie prawdziwe zawsze i o niczym. Overpass ma w rejestrze własną liczbę,
    `timeout_s`, i ta sama liczba stoi w `OVERPASS_TEMPLATE`; to jest para, którą warto
    pilnować. Brak limitu węzłów u Overpassa jest opisany osobno, jako `node_limit_note`,
    bo to jest ZDANIE o końcówce, a nie liczba do zestawienia.
    """
    k = koncowki_osm_z_rejestru(sciezka)
    dopasowanie = TIMEOUT_W_SZABLONIE.search(OVERPASS_TEMPLATE)
    timeout_z_kodu = int(dopasowanie.group(1)) if dopasowanie else None
    return [
        ("osm-api: węzłów na wywołanie", k[OSM_SOURCE_API]["node_limit_per_call"],
         OSM_API_NODE_LIMIT),
        ("osm-api: url", k[OSM_SOURCE_API]["url"], OSM_API_URL),
        ("overpass: timeout zapytania [s]", k[OSM_SOURCE_OVERPASS]["timeout_s"],
         timeout_z_kodu),
        ("overpass: url", k[OSM_SOURCE_OVERPASS]["url"], OVERPASS_URL),
        ("overpass: filtr po stronie serwera",
         k[OSM_SOURCE_OVERPASS]["server_side_filter"], "railway" in OVERPASS_TEMPLATE),
        ("osm-api: filtr po stronie serwera",
         k[OSM_SOURCE_API]["server_side_filter"], "railway" in OSM_API_QUERY_FMT),
    ]


def wiersze_limitow(sciezka=SOURCES_JSON):
    """Wypis par z `pary_rejestr_kod`, po jednym wierszu na parę."""
    return [f"[LIMIT] {co}: rejestr {z_rejestru!r}, kod {z_kodu!r} "
            f"({'zgodne' if z_rejestru == z_kodu else 'ROZJECHANE'})"
            for co, z_rejestru, z_kodu in pary_rejestr_kod(sciezka)]
#: Przerwa między kaflami. To cudza infrastruktura i nie ma tu żadnego powodu, żeby
#: strzelać w nią seriami bez oddechu.
OSM_API_SLEEP_S = 1.0


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Kontrola krzyżowa osi wobec UrbIS i OSM")
    parser.add_argument("--alignment", default=os.path.join("data", "track", "L1_A.json"))
    parser.add_argument("--out", default=os.path.join("build", "L1_A-crosscheck.json"))
    parser.add_argument("--timeout", type=float, default=90.0)
    parser.add_argument("--skip-osm", action="store_true")
    parser.add_argument("--osm-file", help="lokalny snapshot OSM zamiast zapytania sieciowego "
                                           "(Overpass albo tools/track/fetch_osm_routes.py)")
    parser.add_argument("--osm-source", choices=(OSM_SOURCE_OVERPASS, OSM_SOURCE_API),
                        default=OSM_SOURCE_OVERPASS,
                        help="skąd wziąć way'e railway=subway: 'overpass' to droga "
                             "podstawowa z docs/07, 'osm-api' to droga ZAPASOWA przez "
                             "api.openstreetmap.org — bez języka zapytań, kaflowana, "
                             "filtr wykonywany lokalnie i większy transfer")
    parser.add_argument("--osm-snapshot-out",
                        help="zapisz pobrane way'e jako snapshot w kształcie odpowiedzi "
                             "Overpassa, do podania jako --osm-file dla "
                             "tools/track/surface_sections.py")
    parser.add_argument("--osm-tile-deg", type=float, default=OSM_API_TILE_DEG,
                        help="bok kafla siatki dla --osm-source osm-api, w stopniach")
    parser.add_argument("--osm-sleep-s", type=float, default=OSM_API_SLEEP_S,
                        help="przerwa między kaflami, w sekundach")
    parser.add_argument("--osm-cache-dir", default=PAMIEC.DOMYSLNY_KATALOG,
                        help="katalog wspólnej pamięci kafli, kluczowanej po bboxie; "
                             "ten sam prostokąt pobiera się raz, także gdy pyta o niego "
                             "drugie narzędzie")
    parser.add_argument("--osm-refresh", action="store_true",
                        help="pomiń pamięć i pobierz kafle na nowo, nadpisując ją — "
                             "pamięć, której nie da się ominąć, jest gorsza od jej braku")
    parser.add_argument("--urbis-file", help="lokalny snapshot warstwy UrbIS Metro")
    parser.add_argument("--skip-urbis", action="store_true")
    parser.add_argument("--offline", action="store_true",
                        help="ODMÓW wyjścia do sieci; policz tylko to, co da się policzyć "
                             "z --osm-file / --urbis-file")
    return parser.parse_args(argv)


def load_alignment(path):
    with open(path, encoding="utf-8") as handle:
        document = json.load(handle)
    origin = document["origin_source_crs"]
    points = [(p[0] + origin[0], p[1] + origin[1]) for p in document["points"]]
    return document, points


def point_in_ring(point, ring):
    inside = False
    x, y = point
    for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1]):
        if (y1 > y) != (y2 > y):
            xin = (x2 - x1) * (y - y1) / (y2 - y1) + x1
            if x < xin:
                inside = not inside
    return inside


def polygon_rings(geometry):
    kind = geometry.get("type")
    if kind == "Polygon":
        return [geometry["coordinates"][0]]
    if kind == "MultiPolygon":
        return [poly[0] for poly in geometry["coordinates"]]
    return []


def chainage_ranges(points, flags):
    """Przedziały kilometrażu, na których flaga jest prawdziwa.

    Sama liczba trafionych punktów nie mówi generatorowi tunelu, **gdzie** ma
    przestać budować rurę; przedziały mówią.
    """
    chain = [0.0]
    for a, b in zip(points, points[1:]):
        chain.append(chain[-1] + math.dist(a, b))
    ranges = []
    start = None
    for index, flag in enumerate(flags):
        if flag and start is None:
            start = chain[index]
        elif not flag and start is not None:
            ranges.append([round(start, 1), round(chain[index - 1], 1)])
            start = None
    if start is not None:
        ranges.append([round(start, 1), round(chain[-1], 1)])
    return ranges


def crosscheck_urbis(points, timeout, local_file=None, offline=False):
    if local_file:
        with open(local_file, "rb") as handle:
            content = handle.read()
        final_url = f"file:{os.path.basename(local_file)}"
    elif offline:
        # Odmowa jest WYNIKIEM, nie awarią: raport ma powiedzieć, że nie sprawdzono,
        # i dlaczego, a nie udawać pomiaru ani czekać na timeout gniazda.
        return {"status": "odmowa --offline", "reason": "tryb --offline bez --urbis-file",
                "url": P.sanitize_url(URBIS_URL)}
    else:
        try:
            content, final_url, _headers = P.fetch_url(URBIS_URL, expected_format="json",
                                                       timeout=timeout)
        except Exception as exc:
            return {"status": "niedostępne", "reason": str(exc), "url": P.sanitize_url(URBIS_URL)}
    payload = json.loads(content.decode("utf-8"))
    features = payload.get("features", [])
    rings = {"MT": [], "MS": []}
    for feature in features:
        properties = feature.get("properties") or {}
        kind = properties.get("type")
        if kind in rings:
            for ring in polygon_rings(feature.get("geometry") or {}):
                rings[kind].append({
                    "ring": [CRS.wgs84_to_lambert72(x, y) for x, y, *_ in ring],
                    "niveau": str(properties.get("niveau")),
                    "name": properties.get("name_fr") or properties.get("name_nl"),
                })

    counts = {"MT": 0, "MS": 0, "outside": 0}
    # `niveau` jest jedynym polem w tym datasecie, które w ogóle mówi coś o poziomie
    # względem terenu, a `sources.json` zapisuje wprost, że **wymaga interpretacji**.
    # Liczymy je, bo 12 z 87 poligonów tuneli ma `0` i pokrywa się z odcinkami znanymi
    # z biegu po powierzchni — ale wniosku „to jest naziemne" tu nie stawiamy.
    niveau_hits = {}
    named_niveau0 = {}
    niveau0_flags = []
    for point in points:
        hit = next((r for r in rings["MT"] if point_in_ring(point, r["ring"])), None)
        kind = "MT"
        if hit is None:
            hit = next((r for r in rings["MS"] if point_in_ring(point, r["ring"])), None)
            kind = "MS"
        if hit is None:
            counts["outside"] += 1
            niveau0_flags.append(False)
            continue
        counts[kind] += 1
        key = f"{kind}/niveau={hit['niveau']}"
        niveau_hits[key] = niveau_hits.get(key, 0) + 1
        niveau0_flags.append(hit["niveau"] == "0")
        if hit["niveau"] == "0":
            named_niveau0[hit["name"]] = named_niveau0.get(hit["name"], 0) + 1
    total = max(1, len(points))
    niveau0 = sum(v for k, v in niveau_hits.items() if k.endswith("niveau=0"))
    return {
        "status": "ok",
        "url": P.sanitize_url(final_url),
        "features": len(features),
        "polygons": {k: len(v) for k, v in rings.items()},
        "points_checked": len(points),
        "inside_tunnel_pct": round(100.0 * counts["MT"] / total, 1),
        "inside_station_pct": round(100.0 * counts["MS"] / total, 1),
        "outside_pct": round(100.0 * counts["outside"] / total, 1),
        "by_niveau": dict(sorted(niveau_hits.items())),
        "niveau0_points": niveau0,
        "niveau0_pct": round(100.0 * niveau0 / total, 1),
        "niveau0_polygons": dict(sorted(named_niveau0.items())),
        "niveau0_chainage_ranges_m": chainage_ranges(points, niveau0_flags),
        "note": "UrbIS Metro to poligony tuneli i stacji, nie oś toru; miarą jest pokrycie, "
                "nie odchyłka liniowa. Znaczenie pola 'niveau' nie jest potwierdzone przez "
                "dataset — liczba punktów w poligonach z niveau=0 jest wejściem dla R-005, "
                "nie stwierdzeniem, że odcinek biegnie po powierzchni.",
    }


def query_bbox_lonlat(points, margin_m=OVERPASS_BBOX_MARGIN_M):
    """Prostokąt zapytania jako `(west, south, east, north)` w WGS84.

    Wydzielone z `overpass_query`, żeby **obie** drogi do OSM brały DOKŁADNIE ten sam
    prostokąt. Gdyby droga zapasowa liczyła go po swojemu, każda różnica w zbiorze
    obiektów byłaby nieodróżnialna od zmiany w OSM — a porównanie krzyżowe obu dróg
    stoi właśnie na tym rozróżnieniu.

    Narożniki są przeliczane z Lambert 72 pojedynczo, więc prostokąt w stopniach nie
    jest ścisłą obwiednią obróconego prostokąta metrycznego. Zostaje tak, jak było:
    ta niedokładność jest wspólna dla obu dróg i mieści się w marginesie 300 m.
    """
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    corners = [(min(xs) - margin_m, min(ys) - margin_m), (max(xs) + margin_m, max(ys) + margin_m)]
    lonlat = [CRS.lambert72_to_wgs84(x, y) for x, y in corners]
    return (lonlat[0][0], lonlat[0][1], lonlat[1][0], lonlat[1][1])


def overpass_query(points, margin_m=OVERPASS_BBOX_MARGIN_M):
    """Zapytanie Overpassa z bboxem policzonym z osi, w WGS84."""
    west, south, east, north = query_bbox_lonlat(points, margin_m)
    return OVERPASS_TEMPLATE % (south, west, north, east)


def osm_api_tiles(bbox, tile_deg=OSM_API_TILE_DEG):
    """Podział prostokąta na siatkę kafli — bez dziur i bez nakładania.

    Liczba kafli w każdej osi jest zaokrąglana W GÓRĘ, a bok wyliczany z powrotem
    z tej liczby, więc siatka pokrywa prostokąt **dokładnie**. Wariant „stały bok,
    ostatni kafel wystaje" pobierałby obszar poza bboxem, czyli obiekty, których
    zapytanie Overpassa nie widzi — i rozjazd z drogą podstawową brałby się z samego
    narzędzia, nie z danych.
    """
    west, south, east, north = bbox
    nx = max(1, math.ceil((east - west) / tile_deg))
    ny = max(1, math.ceil((north - south) / tile_deg))
    dx, dy = (east - west) / nx, (north - south) / ny
    return [(west + i * dx, south + j * dy, west + (i + 1) * dx, south + (j + 1) * dy)
            for j in range(ny) for i in range(nx)]


def parse_osm_map_xml(content):
    """Way'e `railway=subway` z odpowiedzi `/api/0.6/map`, w kształcie `out geom`.

    Trzy rzeczy, które trzeba tu zrobić i których Overpass robi za nas:

    1. **filtr `railway=subway` jest lokalny.** Surowe API nie ma języka zapytań, więc
       w odpowiedzi leży wszystko: ulice, budynki, perony, tramwaj. Bez tego filtru
       odchyłka liczyłaby się od pierwszej lepszej krawędzi budynku;
    2. **węzły trzeba złożyć w geometrię samemu** — `/map` podaje `<nd ref=…>`, nie
       współrzędne w way'u;
    3. **`version` i `timestamp` way'a zostają w wyniku.** Overpass ich w `out geom`
       nie daje, a to jedyna rzecz, która pozwala odróżnić „droga zapasowa pobrała co
       innego" od „OSM się zmienił od daty snapshotu". Bez nich rozjazd byłby jedną
       liczbą bez przyczyny.

    `/map` zwraca way'e kompletne — także węzły leżące poza prostokątem, jeżeli należą
    do way'a, który go dotyka. Dlatego geometria z jednego kafla jest pełna i nie
    trzeba jej zszywać.
    """
    root = ET.fromstring(content)
    nodes = {n.get("id"): (float(n.get("lon")), float(n.get("lat")))
             for n in root.findall("node")}
    ways = []
    for way in root.findall("way"):
        tags = {t.get("k"): t.get("v") for t in way.findall("tag")}
        if tags.get("railway") != "subway":
            continue
        refs = [nd.get("ref") for nd in way.findall("nd")]
        geometry = [{"lon": nodes[r][0], "lat": nodes[r][1]} for r in refs if r in nodes]
        if len(geometry) < 2:
            continue
        ways.append({"type": "way", "id": int(way.get("id")), "tags": tags,
                     "geometry": geometry, "version": way.get("version"),
                     "timestamp": way.get("timestamp")})
    return ways


def osm_api_ways(bbox, timeout, tile_deg=OSM_API_TILE_DEG, sleep_s=OSM_API_SLEEP_S,
                 log=print, cache_dir=None, refresh=False):
    """Way'e metra z prostokąta, kafel po kaflu. Zwraca `(way'e, statystyka pobrania)`.

    Kafel, który padł, jest **wymieniony w wyniku**, a nie pominięty milczeniem:
    niepełne pokrycie wygląda w liczbach dokładnie jak sieć, w której czegoś nie ma.
    Pętli ponawiającej to samo zapytanie tu nie ma — cudza infrastruktura.
    """
    tiles = osm_api_tiles(bbox, tile_deg)
    merged, refused = {}, []
    licznik = PAMIEC.Licznik()
    for index, tile in enumerate(tiles, start=1):
        query = OSM_API_QUERY_FMT % tile
        content, origin, reason = PAMIEC.wez_kafel(
            tile, f"{OSM_API_URL}?{query}", timeout,
            katalog=cache_dir, wymus=refresh, licznik=licznik)
        if content is None:
            kind = ("kafel przekracza limit %d węzłów" % OSM_API_NODE_LIMIT
                    if "too many nodes" in reason.lower() else "źródło niedostępne")
            refused.append({"bbox": query, "kind": kind, "reason": reason})
            log(f"[OSM-API] kafel {index}/{len(tiles)} ODMOWA ({kind}): {reason}")
            continue
        # Przerwa obowiązuje TYLKO po wyjściu do sieci. Czekanie sekundy przed
        # odczytem z dysku byłoby uprzejmością wobec serwera, którego nikt nie pytał:
        # 30 kafli z pamięci trwałoby 30 s bez jednego żądania.
        if origin == "osm-api" and licznik.pobrane > 1 and sleep_s > 0:
            time.sleep(sleep_s)
        found = parse_osm_map_xml(content)
        for way in found:
            # Ten sam way wraca z każdego kafla, którego dotyka. Zostaje wersja
            # o NAJWIĘKSZEJ liczbie węzłów — gdyby kiedyś API zwróciło geometrię
            # obciętą, `setdefault` przybiłby właśnie tę obciętą.
            previous = merged.get(way["id"])
            if previous is None or len(way["geometry"]) > len(previous["geometry"]):
                merged[way["id"]] = way
        log(f"[OSM-API] kafel {index}/{len(tiles)} {query}: {len(content)} B "
            f"({origin}), {len(found)} way railway=subway, razem {len(merged)}")
    log(f"[OSM-API] {licznik}")
    stats = {"tiles": len(tiles), "tiles_refused": refused, "tile_deg": tile_deg,
             "cache_dir": cache_dir or PAMIEC.DOMYSLNY_KATALOG, "refresh": bool(refresh)}
    stats.update(licznik.jako_slownik())
    return [merged[key] for key in sorted(merged)], stats


def osm_api_payload(points, timeout, tile_deg=OSM_API_TILE_DEG, sleep_s=OSM_API_SLEEP_S,
                    log=print, cache_dir=None, refresh=False):
    """Odpowiedź `/api/0.6/map` przepakowana w kształt snapshotu Overpassa.

    Kształt jest ten sam, więc `surface_sections.py --osm-file` czyta to bez
    rozgałęzień — ale pole `osm_source` mówi, że to droga zapasowa, i nie pozwala
    podać tego pliku dalej jako pomiaru z Overpassa.
    """
    bbox = query_bbox_lonlat(points)
    ways, stats = osm_api_ways(bbox, timeout, tile_deg, sleep_s, log,
                               cache_dir=cache_dir, refresh=refresh)
    payload = {
        "version": 0.6,
        "generator": "tools/track/crosscheck_alignment.py --osm-source " + OSM_SOURCE_API,
        "osm_source": OSM_SOURCE_API,
        "osm_api_url": P.sanitize_url(OSM_API_URL),
        "bbox_lonlat": [round(v, 6) for v in bbox],
        "download": stats,
        "attribution": "© OpenStreetMap contributors, ODbL 1.0",
        "elements": ways,
    }
    return payload, stats


def crosscheck_osm(points, timeout, local_file=None, source=OSM_SOURCE_OVERPASS, offline=False,
                   tile_deg=OSM_API_TILE_DEG, sleep_s=OSM_API_SLEEP_S, snapshot_out=None,
                   cache_dir=None, refresh=False,
                   log=print):
    query = overpass_query(points)
    if local_file:
        with open(local_file, "rb") as handle:
            content = handle.read()
        payload = json.loads(content.decode("utf-8"))
        return _osm_metrics(points, payload, {
            "status": "ok",
            "source": "snapshot lokalny",
            # Snapshot niesie własną deklarację pochodzenia od 6.B52. Plik bez niej
            # powstał wcześniej i wtedy `None` jest uczciwsze niż domyślenie się
            # Overpassa: to właśnie milczące przypisanie źródła jest tu zakazane.
            "snapshot_osm_source": payload.get("osm_source"),
            "file": os.path.basename(local_file),
            "file_sha256": P.sha256_bytes(content),
            # `osm_timestamp` bierze się WYŁĄCZNIE z `osm3s`, bo tylko Overpass podaje
            # stan bazy. Snapshot z drogi `/api/0.6` tego pola nie ma i wtedy `None`
            # jest odpowiedzią prawdziwą — 6.D64. Obok stoi DOLNA GRANICA policzona
            # z way'ów, pod nazwą, która mówi, czym jest: najświeższa edycja wśród
            # pobranych way'ów nie jest stanem bazy.
            "osm_timestamp": (payload.get("osm3s") or {}).get("timestamp_osm_base"),
            "way_timestamp_max": max(
                (w["timestamp"] for w in (payload.get("elements") or [])
                 if w.get("timestamp")), default=None),
            "snapshot_retrieved_at": payload.get("retrieved_at"),
            "routes": payload.get("routes"),
            "attribution": "© OpenStreetMap contributors, ODbL 1.0",
        })
    if offline:
        return {"status": "odmowa --offline",
                "reason": "tryb --offline bez --osm-file",
                "source": source,
                "query_sha256": P.sha256_bytes(query.encode("utf-8"))}
    if source == OSM_SOURCE_API:
        payload, stats = osm_api_payload(points, timeout, tile_deg, sleep_s, log,
                                         cache_dir=cache_dir, refresh=refresh)
        if snapshot_out:
            _write_snapshot(snapshot_out, payload)
        base = {
            "status": "ok",
            "source": OSM_SOURCE_API,
            "url": P.sanitize_url(OSM_API_URL),
            "bbox_lonlat": payload["bbox_lonlat"],
            "download": stats,
            "osm_timestamp": None,
            "way_timestamp_max": max((w["timestamp"] for w in payload["elements"]
                                      if w.get("timestamp")), default=None),
            "note_source": "droga ZAPASOWA: api.openstreetmap.org/api/0.6/map bez języka "
                           "zapytań, filtr railway=subway wykonany lokalnie",
            "attribution": "© OpenStreetMap contributors, ODbL 1.0",
        }
        if stats["tiles_refused"]:
            base["status"] = "częściowe"
        return _osm_metrics(points, payload, base,
                            query_text=f"{OSM_API_URL} kafle {stats['tiles']}x{tile_deg}° "
                                       f"bbox={payload['bbox_lonlat']}")
    try:
        content, final_url, _headers = P.fetch_url(
            OVERPASS_URL + "?data=" + _quote(query), expected_format="json", timeout=timeout)
    except Exception as exc:
        return {"status": "niedostępne", "reason": str(exc), "url": P.sanitize_url(OVERPASS_URL),
                "source": OSM_SOURCE_OVERPASS,
                "query_sha256": P.sha256_bytes(query.encode("utf-8"))}
    payload = json.loads(content.decode("utf-8"))
    if snapshot_out:
        _write_snapshot(snapshot_out, dict(payload, osm_source=OSM_SOURCE_OVERPASS))
    return _osm_metrics(points, payload, {
        "status": "ok",
        "source": OSM_SOURCE_OVERPASS,
        "url": P.sanitize_url(final_url),
        "osm_timestamp": (payload.get("osm3s") or {}).get("timestamp_osm_base"),
        "attribution": "© OpenStreetMap contributors, ODbL 1.0",
    })


#: Statusy, przy których w wyniku SĄ liczby. `częściowe` to droga zapasowa, której
#: część kafli padła: liczby są, ale pokrycie prostokąta jest niepełne i wynik mówi to
#: wprost, zamiast udawać pełny pomiar.
OSM_STATUS_WITH_METRICS = ("ok", "częściowe")

#: Zdania o pochodzeniu, jedno na drogę. Stoją w słowniku, a nie w `if`-ach, żeby dało
#: się sprawdzić bramką, że KAŻDA droga ma swoje i że żadne nie jest puste.
OSM_SOURCE_SENTENCES = {
    OSM_SOURCE_OVERPASS: "overpass-api.de/api/interpreter — droga PODSTAWOWA wg "
                         "docs/07-open-data-research.md, filtr railway=subway po stronie "
                         "serwera",
    OSM_SOURCE_API: "api.openstreetmap.org/api/0.6/map — droga ZAPASOWA wg "
                    "docs/07-open-data-research.md: bez języka zapytań, obszar pobierany "
                    "kaflami, filtr railway=subway wykonany LOKALNIE",
    "snapshot lokalny": "plik lokalny podany przez --osm-file — pochodzenie danych "
                        "zapisuje pole osm_source samego snapshotu",
}


def osm_source_sentence(entry):
    """Jedno zdanie mówiące, SKĄD są dane OSM w tym przebiegu.

    Wypis bez tego zdania byłby nieodróżnialny między drogą podstawową a zapasową —
    a to są dwa różne zbiory obiektów, pobrane dwoma różnymi mechanizmami. `docs/07`
    ustala między nimi hierarchię, więc raport, który nie mówi, którą drogą poszedł,
    nie da się do niej odnieść.
    """
    if entry.get("status") == "pominięte":
        return "NIE PYTANO (--skip-osm)"
    source = entry.get("source")
    sentence = OSM_SOURCE_SENTENCES.get(source, f"NIEZNANE ŹRÓDŁO ({source!r})")
    if source == "snapshot lokalny":
        declared = entry.get("snapshot_osm_source")
        sentence += (f"; snapshot deklaruje: {declared}" if declared
                     else "; snapshot NIE deklaruje pochodzenia")
    if entry.get("status") != "ok":
        sentence = f"{entry['status']} — {sentence}"
    return sentence


def _write_snapshot(path, payload):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "wb") as handle:
        handle.write(P.canonical_json(payload))
    return path


def _lambert_segments(ways):
    return [[CRS.wgs84_to_lambert72(node["lon"], node["lat"]) for node in way["geometry"]]
            for way in ways]


def _coverage_and_deviation(points, segments):
    """Pokrycie i odchyłka to **dwie różne wielkości** i nie wolno ich mieszać.

    Pokrycie mówi, na jakiej części osi drugie źródło w ogóle coś ma. Odchyłka jest
    liczona **tylko** na pokrytym odcinku — punkty bez pokrycia dawałyby setki metrów
    i zamazywały wynik.
    """
    deviations = sorted(min(_distance_to_polyline(point, seg) for seg in segments)
                        for point in points)
    covered = [d for d in deviations if d <= OSM_COVERAGE_RADIUS_M]
    result = {"points_checked": len(points),
              "coverage_radius_m": OSM_COVERAGE_RADIUS_M,
              "coverage_pct": round(100.0 * len(covered) / max(1, len(points)), 1)}
    if not covered:
        return result
    result.update({"deviation_median_m": round(covered[len(covered) // 2], 2),
                   "deviation_p95_m": round(covered[int(0.95 * (len(covered) - 1))], 2),
                   "deviation_max_m": round(covered[-1], 2)})
    return result


def _osm_metrics(points, payload, base, query_text=None):
    """`query_text` domyślnie opisuje zapytanie Overpassa — i przy drodze zapasowej
    trzeba je podać, bo inaczej wynik niósłby sumę zapytania, którego nikt nie wysłał.
    `query_sha256` jest polem provenance: nieprawdziwe jest tu gorsze niż żadne."""
    ways = [e for e in payload.get("elements", []) if e.get("type") == "way" and e.get("geometry")]
    segments = _lambert_segments(ways)
    if not segments:
        return dict(base, status="brak danych", ways=0)
    overall = _coverage_and_deviation(points, segments)
    if "deviation_median_m" not in overall:
        return dict(base, status="brak pokrycia", ways=len(ways), **overall)
    # Snapshot z `fetch_osm_routes.py` zna przynależność way'a do relacji kierunkowej,
    # więc da się policzyć odchyłkę osobno dla każdego toru. Ekstrakt bboxowy tego nie
    # ma — i właśnie dlatego mieszał cztery linie w jedną statystykę (raport pakietu A).
    per_relation = {}
    for way, segment in zip(ways, segments):
        for relation in way.get("route_relations", []):
            per_relation.setdefault(relation, []).append(segment)
    directions = []
    for relation in sorted(per_relation):
        entry = {"relation": relation}
        for route in payload.get("routes") or []:
            if route.get("id") == relation:
                entry["name"] = route.get("name")
        entry.update(_coverage_and_deviation(points, per_relation[relation]))
        entry["ways"] = len(per_relation[relation])
        directions.append(entry)
    if query_text is None:
        query_text = overpass_query(points)
    return dict(base, **{
        "query_sha256": P.sha256_bytes(query_text.encode("utf-8")),
        "ways": len(ways),
        "nodes": sum(len(s) for s in segments),
        "per_relation": directions,
        "note": "OSM mapuje tory pojedynczo, więc odchyłka od osi trasy handlowej odpowiada "
                "mniej więcej połowie rozstawu torów i nie jest błędem żadnego ze źródeł.",
    }, **overall)


def _quote(text):
    from urllib.parse import quote
    return quote(text, safe="")


def _distance_to_polyline(point, polyline):
    best = float("inf")
    for a, b in zip(polyline, polyline[1:]):
        dx, dy = b[0] - a[0], b[1] - a[1]
        seg = dx * dx + dy * dy
        if seg <= 0:
            best = min(best, math.dist(point, a))
            continue
        t = ((point[0] - a[0]) * dx + (point[1] - a[1]) * dy) / seg
        t = 0.0 if t < 0 else (1.0 if t > 1.0 else t)
        best = min(best, math.dist(point, (a[0] + t * dx, a[1] + t * dy)))
    return best


def main(argv=None):
    args = parse_args(argv)
    path = args.alignment if os.path.isabs(args.alignment) else os.path.join(ROOT, args.alignment)
    document, points = load_alignment(path)

    report = {"alignment_id": document["id"], "checked_at": P.utc_now_iso(),
              "source_crs": document["source_crs"], "points": len(points)}
    report["urbis"] = ({"status": "pominięte"} if args.skip_urbis
                       else crosscheck_urbis(points, args.timeout, args.urbis_file,
                                             offline=args.offline))
    report["osm"] = ({"status": "pominięte"} if args.skip_osm
                     else crosscheck_osm(points, args.timeout, args.osm_file,
                                         source=args.osm_source, offline=args.offline,
                                         tile_deg=args.osm_tile_deg,
                                         sleep_s=args.osm_sleep_s,
                                         cache_dir=args.osm_cache_dir,
                                         refresh=args.osm_refresh,
                                         snapshot_out=args.osm_snapshot_out))

    out = args.out if os.path.isabs(args.out) else os.path.join(ROOT, args.out)
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    with open(out, "wb") as handle:
        handle.write(P.canonical_json(report))

    # Zdanie o pochodzeniu idzie PRZED liczbami i stoi poza gałęzią statusu, bo dotyczy
    # każdego przebiegu — także tego, w którym nic się nie pobrało. Czytający ma wiedzieć,
    # czego się nie udało pobrać skąd, a nie tylko, że się nie udało.
    print("[ŹRÓDŁO] osm: " + osm_source_sentence(report["osm"]))
    if args.osm_snapshot_out and report["osm"]["status"] in OSM_STATUS_WITH_METRICS:
        print(f"[ŹRÓDŁO] snapshot zapisany: {args.osm_snapshot_out} "
              f"(pole osm_source = {report['osm'].get('source')})")

    for name in ("urbis", "osm"):
        entry = report[name]
        if entry["status"] not in OSM_STATUS_WITH_METRICS:
            print(f"[KONTROLA] {name}: {entry['status']}"
                  + (f" — {entry.get('reason', '')}" if entry.get("reason") else ""))
            continue
        if name == "urbis":
            print(f"[KONTROLA] urbis: tunel {entry['inside_tunnel_pct']}%, "
                  f"stacja {entry['inside_station_pct']}%, poza {entry['outside_pct']}% "
                  f"({entry['features']} obiektów)")
            print(f"[KONTROLA] urbis niveau: {entry['by_niveau']}; "
                  f"niveau=0 na {entry['niveau0_points']} punktach ({entry['niveau0_pct']}%)")
            for polygon, hits in entry["niveau0_polygons"].items():
                print(f"[NIVEAU0] {hits:>4} punktów w poligonie: {polygon}")
            for low, high in entry["niveau0_chainage_ranges_m"]:
                print(f"[NIVEAU0] kilometraż {low:.1f}–{high:.1f} m ({high - low:.1f} m)")
        else:
            download = entry.get("download")
            if download:
                print(f"[OSM-API] {download['tiles']} kafli po {download['tile_deg']}°, "
                      f"{download.get('tiles_from_cache', 0)} z pamięci "
                      f"({download.get('bytes_from_cache', 0)} B), "
                      f"{download.get('tiles_downloaded', 0)} pobranych "
                      f"({download['bytes_downloaded']} B), "
                      f"kafli odrzuconych: {len(download['tiles_refused'])}")
                print(f"[OSM-API] pamięć kafli: {download.get('cache_dir')}"
                      + (" (POMINIĘTA, --osm-refresh)" if download.get("refresh") else ""))
                for refused in download["tiles_refused"]:
                    print(f"[OSM-API] ODRZUCONY {refused['bbox']}: {refused['kind']}")
            print(f"[KONTROLA] osm: {entry['ways']} way, pokrycie {entry['coverage_pct']}% "
                  f"(promień {entry['coverage_radius_m']:.0f} m), odchyłka na pokrytym odcinku: "
                  f"mediana {entry['deviation_median_m']} m, P95 {entry['deviation_p95_m']} m, "
                  f"maks. {entry['deviation_max_m']} m")
            for direction in entry.get("per_relation", []):
                print(f"[KIERUNEK] {direction['relation']} {direction.get('name', '')}: "
                      f"{direction['ways']} way, pokrycie {direction['coverage_pct']}%, "
                      f"mediana {direction.get('deviation_median_m')} m, "
                      f"P95 {direction.get('deviation_p95_m')} m, "
                      f"maks. {direction.get('deviation_max_m')} m")
    print(f"[RAPORT] {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
