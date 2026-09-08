#!/usr/bin/env python3
"""Droga zapasowa do OSM przez `api.openstreetmap.org` — i to, że NAZYWA swoje źródło.

**Skąd ta bramka.** 6.B52. Overpass jest z tego kontenera nieosiągalny — zmierzone
08.09.2026: `overpass-api.de/api/status` zwraca HTTP 000 po 9,76 s (`Recv failure:
Connection reset by peer`), a proxy zapisuje `ws_closed_mid_exchange` dla
`overpass-api.de:443`. `api.openstreetmap.org/api/0.6/capabilities` odpowiada w tej
samej chwili HTTP 200 po 0,72 s. Pozycja 6.B26 stoi dokładnie na tej niedostępności,
bo wymaga rozstrzygnięcia po OBU źródłach.

**Czego ta bramka pilnuje NAPRAWDĘ, i to jest jej treść.** Nie tego, że droga zapasowa
istnieje — to widać z `--help`. Tego, że **nie jest cicha**. Dwie drogi do OSM dają dwa
różne zbiory obiektów, pobrane dwoma różnymi mechanizmami, a `docs/07-open-data-research.md`
ustala między nimi hierarchię. Przebieg, który nie mówi, którą drogą poszedł, nie da się
do tej hierarchii odnieść — więc jest bezwartościowy, choć wygląda identycznie jak
przebieg wartościowy. Bramka sprawdza więc trzy rzeczy, których `--help` nie pokazuje:

1. wypis **nazywa host** źródła, osobno dla każdej drogi i osobno przy odmowie;
2. `query_sha256` przy drodze zapasowej **nie jest** sumą zapytania Overpassa —
   pole provenance z nieprawdziwą treścią jest gorsze niż jego brak;
3. snapshot zapisany przez `--osm-snapshot-out` **deklaruje** `osm_source`, a
   `surface_sections.py` czyta tę deklarację, zamiast nazywać każdy plik Overpassem.

**Prostokąt jest jeden dla obu dróg** i to też jest tu sprawdzane. Gdyby droga zapasowa
liczyła bbox po swojemu, każda różnica w zbiorze obiektów byłaby nieodróżnialna od
zmiany w samym OSM — a porównanie krzyżowe obu dróg stoi wyłącznie na tym rozróżnieniu.

**Żaden test tutaj nie rusza sieci.** Wyjściem do sieci jest jedna funkcja —
`provenance.fetch_url` — więc podstawia się ją i przepuszcza przez oba filtry wymyśloną
odpowiedź `/api/0.6/map`. Ścieżka odmowy jest testowana funkcją, która rzuca wyjątek,
tak samo jak w `test_fetchers.py` dla `--offline`.
"""
import contextlib
import io
import json
import os
import sys
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "track"))
sys.path.insert(0, os.path.join(ROOT, "tools", "data"))

import crosscheck_alignment as X  # noqa: E402
import crs as CRS  # noqa: E402
import surface_sections as SS  # noqa: E402

DOC = os.path.join(ROOT, "docs", "07-open-data-research.md")

#: Punkt odniesienia w Lambert 72, w środku pakietu D — tam, gdzie zmierzono kafel.
BASE_X, BASE_Y = 152000.0, 166000.0


def _doc_text():
    with open(DOC, encoding="utf-8") as handle:
        return handle.read()


def _map_xml(ways, nodes=None):
    """Odpowiedź `/api/0.6/map` w kształcie, w jakim ją naprawdę zwraca OSM.

    Węzły stoją POZA way'em i way odsyła do nich przez `<nd ref=…>` — to jest cała
    różnica wobec Overpassowego `out geom` i jedyny powód, dla którego droga zapasowa
    potrzebuje własnego czytnika.
    """
    nodes = nodes or {}
    parts = ['<?xml version="1.0" encoding="UTF-8"?><osm version="0.6">']
    for node_id, (x, y) in sorted(nodes.items()):
        lon, lat = CRS.lambert72_to_wgs84(x, y)
        parts.append(f'<node id="{node_id}" lon="{lon}" lat="{lat}"/>')
    for way in ways:
        parts.append(f'<way id="{way["id"]}" version="{way.get("version", 1)}" '
                     f'timestamp="{way.get("timestamp", "2026-01-01T00:00:00Z")}">')
        for ref in way["nodes"]:
            parts.append(f'<nd ref="{ref}"/>')
        for key, value in (way.get("tags") or {}).items():
            parts.append(f'<tag k="{key}" v="{value}"/>')
        parts.append("</way>")
    parts.append("</osm>")
    return "".join(parts).encode("utf-8")


class _FakeFetch:
    """Podstawiony `provenance.fetch_url`: bbox -> gotowa odpowiedź, plus licznik.

    Nieznany bbox jest **błędem testu**, a nie pustą odpowiedzią: zmutowana siatka
    kafli, która pyta o inny prostokąt, dostałaby cicho pustkę i wyglądała na
    równoważną.
    """

    def __init__(self, by_bbox, refuse=()):
        self.by_bbox = by_bbox
        self.refuse = dict(refuse)
        self.asked = []

    def __call__(self, url, *, expected_format, timeout=None, headers=None):
        bbox = url.split("bbox=")[-1]
        self.asked.append(bbox)
        if bbox in self.refuse:
            raise RuntimeError(self.refuse[bbox])
        assert bbox in self.by_bbox, f"nieoczekiwany kafel: {bbox}"
        return self.by_bbox[bbox], url, {}


@contextlib.contextmanager
def _fake_network(fake):
    original = X.P.fetch_url
    X.P.fetch_url = fake
    try:
        yield fake
    finally:
        X.P.fetch_url = original


# --- siatka kafli: pokrycie prostokąta bez dziur i bez wystawania ------------------

def test_osm_api_tiles_cover_the_whole_bbox_without_gaps_or_overrun():
    """Siatka ma pokryć prostokąt DOKŁADNIE.

    Dziura znaczy way'e, których droga zapasowa nie zobaczy, czyli ciche zaniżenie
    pokrycia. Wystawanie znaczy obiekty spoza bboxa zapytania Overpassa, czyli rozjazd
    wzięty z narzędzia, nie z danych. Dlatego oba brzegi są sprawdzane co do bitu, a
    bok jest przeliczany z liczby kafli — nie odwrotnie.
    """
    bbox = (4.0, 50.0, 4.019, 50.011)
    tiles = X.osm_api_tiles(bbox, tile_deg=0.006)
    # ceil(0.019/0.006) = 4 kolumny, ceil(0.011/0.006) = 2 wiersze
    assert len(tiles) == 8, tiles
    assert min(t[0] for t in tiles) == bbox[0]
    assert min(t[1] for t in tiles) == bbox[1]
    assert max(t[2] for t in tiles) == bbox[2]
    assert max(t[3] for t in tiles) == bbox[3]
    # brak dziury: prawa krawędź każdego kafla jest lewą krawędzią następnego
    xs = sorted({round(t[0], 9) for t in tiles} | {round(t[2], 9) for t in tiles})
    for low, high in zip(xs, xs[1:]):
        assert any(round(t[0], 9) == low and round(t[2], 9) == high for t in tiles), (low, high)


def test_osm_api_tiles_never_shrink_the_area_when_the_bbox_is_smaller_than_one_tile():
    """Prostokąt mniejszy od kafla ma dać JEDEN kafel równy jemu, nie zero kafli.

    `max(1, ...)` jest jedyną rzeczą, która to trzyma. Bez niego oś krótsza niż
    kafel dawałaby pustą listę, a pusta lista to „zero way'ów" — czyli wynik
    nieodróżnialny od odcinka, na którym metra nie ma.
    """
    tiles = X.osm_api_tiles((4.0, 50.0, 4.001, 50.001), tile_deg=0.006)
    assert tiles == [(4.0, 50.0, 4.001, 50.001)], tiles


def test_both_paths_to_osm_ask_about_exactly_the_same_rectangle():
    """Prostokąt drogi zapasowej to TEN SAM prostokąt, co w zapytaniu Overpassa.

    Sprawdzane przez tekst zapytania Overpassa, a nie przez powtórzenie wzoru: gdyby
    `query_bbox_lonlat` policzyło narożniki inaczej, obie strony tej asercji
    rozjechałyby się, a test na samym wzorze przechodziłby dalej.
    """
    points = [(BASE_X, BASE_Y), (BASE_X + 400.0, BASE_Y + 250.0)]
    west, south, east, north = X.query_bbox_lonlat(points)
    query = X.overpass_query(points)
    assert "%.5f,%.5f,%.5f,%.5f" % (south, west, north, east) in query, query
    # Kafle nie wychodzą poza ten prostokąt ani go nie skracają.
    tiles = X.osm_api_tiles((west, south, east, north))
    assert min(t[0] for t in tiles) == west and max(t[2] for t in tiles) == east
    assert min(t[1] for t in tiles) == south and max(t[3] for t in tiles) == north


# --- czytnik XML: filtr, kolejność węzłów, wersja i znacznik czasu -----------------

def _nodes():
    return {"1": (BASE_X, BASE_Y), "2": (BASE_X + 100.0, BASE_Y),
            "3": (BASE_X + 200.0, BASE_Y)}


def test_map_reader_keeps_subway_ways_and_nothing_else():
    """Surowe `/map` nie ma języka zapytań — filtr `railway=subway` jest LOKALNY.

    W odpowiedzi leży wszystko, co jest w prostokącie: ulica, budynek, tramwaj,
    peron. Odwrócenie tego filtru nie daje pustki — daje geometrię, która torem nie
    jest, a odchyłka od niej wygląda jak liczba. Dlatego fikstura ma obok metra
    tramwaj i drogę o TAKIEJ SAMEJ geometrii: różnica jest wyłącznie w tagu.
    """
    xml = _map_xml([
        {"id": 11, "nodes": ["1", "2", "3"], "tags": {"railway": "subway"}},
        {"id": 22, "nodes": ["1", "2", "3"], "tags": {"railway": "tram"}},
        {"id": 33, "nodes": ["1", "2", "3"], "tags": {"highway": "residential"}},
        {"id": 44, "nodes": ["1", "2", "3"], "tags": {}},
    ], _nodes())
    ways = X.parse_osm_map_xml(xml)
    assert [w["id"] for w in ways] == [11], ways
    assert ways[0]["tags"]["railway"] == "subway"


def test_map_reader_preserves_node_order_and_the_level_tags():
    """Kolejność węzłów i tagi poziomu to cały ładunek tego czytnika.

    Odwrócona albo posortowana geometria daje ten sam zbiór punktów i tę samą
    długość, więc kontrola odchyłki tego nie zauważy. `tunnel` i `layer` są z kolei
    jedynym, po co ten snapshot jest robiony dla 6.B26 — snapshot bez nich przeszedłby
    każdą kontrolę spójności i nie odpowiedziałby na pytanie o tunel.
    """
    xml = _map_xml([{"id": 11, "nodes": ["3", "1", "2"],
                     "tags": {"railway": "subway", "tunnel": "yes", "layer": "-2"}}], _nodes())
    ways = X.parse_osm_map_xml(xml)
    lons = [round(point["lon"], 6) for point in ways[0]["geometry"]]
    expected = [round(CRS.lambert72_to_wgs84(*_nodes()[r])[0], 6) for r in ("3", "1", "2")]
    assert lons == expected, (lons, expected)
    assert ways[0]["tags"]["tunnel"] == "yes"
    assert ways[0]["tags"]["layer"] == "-2"


def test_map_reader_keeps_version_and_timestamp_because_they_attribute_the_drift():
    """`version` i `timestamp` way'a są tu JEDYNYM przyrządem do przyczyny rozjazdu.

    Rozjazd wobec datowanego snapshotu ma dwie możliwe przyczyny — droga zapasowa
    pobrała co innego albo OSM się zmienił — i bez znacznika czasu way'a nie da się
    ich rozróżnić. Overpass w `out geom` tych pól nie daje, więc gdyby czytnik je
    zgubił, przyrządu nie byłoby wcale.
    """
    xml = _map_xml([{"id": 11, "nodes": ["1", "2"], "version": 7,
                     "timestamp": "2026-01-19T22:36:21Z",
                     "tags": {"railway": "subway"}}], _nodes())
    ways = X.parse_osm_map_xml(xml)
    assert ways[0]["version"] == "7", ways[0]
    assert ways[0]["timestamp"] == "2026-01-19T22:36:21Z", ways[0]


def test_map_reader_drops_a_way_that_has_fewer_than_two_usable_nodes():
    """Bramka `len(geometry) < 2` liczona DOKŁADNIE NA GRANICY, obie strony.

    Way dwuwęzłowy to normalny kawałek tunelu między rozjazdami i musi zostać;
    way, którego drugi węzeł nie przyszedł, nie jest odcinkiem i policzenie go
    jako odcinka wywaliłoby `zip` na pustce albo dało odległość do punktu.
    """
    xml = _map_xml([
        {"id": 11, "nodes": ["1", "2"], "tags": {"railway": "subway"}},     # granica
        {"id": 12, "nodes": ["1"], "tags": {"railway": "subway"}},          # pod granicą
        {"id": 13, "nodes": ["1", "999"], "tags": {"railway": "subway"}},   # 999 nieznane
    ], _nodes())
    ways = X.parse_osm_map_xml(xml)
    assert [w["id"] for w in ways] == [11], ways
    assert len(ways[0]["geometry"]) == 2


# --- pobranie kaflami: scalanie i odmowy ------------------------------------------

def _tile_key(tile):
    return "%.5f,%.5f,%.5f,%.5f" % tile


def test_tiled_download_merges_a_way_that_arrives_from_two_tiles():
    """Way dotykający dwóch kafli ma dać JEDEN wpis z PEŁNĄ geometrią.

    `/api/0.6/map` zwraca way'e kompletne, więc scalenie po `id` jest dokładne —
    ale gdyby kiedyś przyszła geometria obcięta, `setdefault` przybiłby właśnie tę
    obciętą. Fikstura podaje dlatego ten sam way raz z dwoma, raz z trzema węzłami
    i sprawdza, że zostaje ta dłuższa. Kontrola negatywna jest w samych liczbach:
    2 i 3 to inne wartości, więc wynik odróżnia wybór od przypadku.
    """
    # 0,007° / 0,006° daje dwie kolumny i jeden wiersz. Prostokąt o boku będącym
    # dokładną wielokrotnością kafla jest tu świadomie omijany: `4.012 - 4.0` wychodzi
    # w double 0,012000000000000455, więc `ceil` daje TRZY kolumny, nie dwie. Fikstura
    # opierająca się na takim boku sprawdzałaby zaokrąglenie double'a, nie siatkę.
    bbox = (4.0, 50.0, 4.007, 50.003)
    tiles = X.osm_api_tiles(bbox, tile_deg=0.006)
    assert len(tiles) == 2, tiles
    short = _map_xml([{"id": 11, "nodes": ["1", "2"], "tags": {"railway": "subway"}}], _nodes())
    full = _map_xml([{"id": 11, "nodes": ["1", "2", "3"], "tags": {"railway": "subway"}}],
                    _nodes())
    fake = _FakeFetch({_tile_key(tiles[0]): short, _tile_key(tiles[1]): full})
    with _fake_network(fake):
        ways, stats = X.osm_api_ways(bbox, timeout=1.0, tile_deg=0.006, sleep_s=0,
                                     log=lambda *_a, **_k: None)
    assert [w["id"] for w in ways] == [11], ways
    assert len(ways[0]["geometry"]) == 3, ways[0]
    assert stats["tiles"] == 2 and stats["tiles_refused"] == [], stats
    assert stats["bytes_downloaded"] == len(short) + len(full), stats


def test_the_throttle_waits_between_tiles_and_never_before_the_first():
    """Przerwa między kaflami jest zobowiązaniem wobec cudzego serwera, nie ozdobą.

    **Cztery mutacje na tym jednym wierszu przeżyły sweep** (6.B52, `7f116a4`):
    `index > 1` → `>= 1` i `sleep_s > 0` → `>= 0`, każda w dwóch postaciach. Żadna nie
    wywala testu, bo żaden test nie patrzył na `time.sleep` — a pierwsza z nich każe
    czekać przed PIERWSZYM kaflem (czyli bez powodu), a druga woła `sleep(0)` przy
    wyłączonej przerwie. Osobno to drobiazgi; razem to znaczy, że kontrakt „nie
    strzelamy w OSM seriami bez oddechu" nie był sprawdzany przez nic.

    Sprawdzane są obie strony progu naraz: przy trzech kaflach przerw ma być DWIE,
    a przy `sleep_s = 0` ani jednej.
    """
    bbox = (4.0, 50.0, 4.013, 50.003)
    tiles = X.osm_api_tiles(bbox, tile_deg=0.006)
    assert len(tiles) == 3, tiles
    xml = _map_xml([{"id": 11, "nodes": ["1", "2"], "tags": {"railway": "subway"}}], _nodes())
    waits = []
    original_sleep = X.time.sleep
    X.time.sleep = waits.append
    try:
        with _fake_network(_FakeFetch({_tile_key(t): xml for t in tiles})):
            X.osm_api_ways(bbox, timeout=1.0, tile_deg=0.006, sleep_s=0.5,
                           log=lambda *_a, **_k: None)
        assert waits == [0.5, 0.5], waits
        waits.clear()
        with _fake_network(_FakeFetch({_tile_key(t): xml for t in tiles})):
            X.osm_api_ways(bbox, timeout=1.0, tile_deg=0.006, sleep_s=0,
                           log=lambda *_a, **_k: None)
        assert waits == [], waits
    finally:
        X.time.sleep = original_sleep


def test_a_refused_tile_is_named_in_the_result_not_swallowed():
    """Kafel, który padł, musi być WYMIENIONY — niepełne pokrycie wygląda w liczbach
    dokładnie jak obszar, na którym metra nie ma.

    Sprawdzane są obie strony naraz: kafel, który się udał, wnosi way'e, a kafel
    odrzucony wnosi wpis na listę. Sam status też się zmienia, bo `ok` przy niepełnym
    pobraniu byłby zdaniem nieprawdziwym.
    """
    # 0,007° / 0,006° daje dwie kolumny i jeden wiersz. Prostokąt o boku będącym
    # dokładną wielokrotnością kafla jest tu świadomie omijany: `4.012 - 4.0` wychodzi
    # w double 0,012000000000000455, więc `ceil` daje TRZY kolumny, nie dwie. Fikstura
    # opierająca się na takim boku sprawdzałaby zaokrąglenie double'a, nie siatkę.
    bbox = (4.0, 50.0, 4.007, 50.003)
    tiles = X.osm_api_tiles(bbox, tile_deg=0.006)
    good = _map_xml([{"id": 11, "nodes": ["1", "2"], "tags": {"railway": "subway"}}], _nodes())
    fake = _FakeFetch({_tile_key(tiles[0]): good},
                      refuse={_tile_key(tiles[1]): "HTTP Error 500: Internal Server Error"})
    with _fake_network(fake):
        ways, stats = X.osm_api_ways(bbox, timeout=1.0, tile_deg=0.006, sleep_s=0,
                                     log=lambda *_a, **_k: None)
    assert [w["id"] for w in ways] == [11], ways
    assert len(stats["tiles_refused"]) == 1, stats
    assert stats["tiles_refused"][0]["bbox"] == "bbox=" + _tile_key(tiles[1]), stats
    assert stats["tiles_refused"][0]["kind"] == "źródło niedostępne", stats


def test_the_node_limit_refusal_is_told_apart_from_a_dead_source():
    """„Kafel za duży" i „źródło leży" to dwie różne diagnozy i dwa różne remedia.

    Pierwsza znaczy: zmniejsz `--osm-tile-deg`. Druga znaczy: nie ma po co próbować.
    Zlanie ich w jeden komunikat kazałoby zgadywać, którą się właśnie dostało —
    a dokładnie ten limit jest zmierzony: całe bbox pakietu D w jednym wywołaniu
    daje `HTTP 400 — You requested too many nodes (limit is 50000)`.
    """
    bbox = (4.0, 50.0, 4.001, 50.001)
    tiles = X.osm_api_tiles(bbox, tile_deg=0.006)
    message = "HTTP Error 400: You requested too many nodes (limit is 50000)"
    fake = _FakeFetch({}, refuse={_tile_key(tiles[0]): message})
    with _fake_network(fake):
        _ways, stats = X.osm_api_ways(bbox, timeout=1.0, tile_deg=0.006, sleep_s=0,
                                      log=lambda *_a, **_k: None)
    assert len(stats["tiles_refused"]) == 1, stats
    assert str(X.OSM_API_NODE_LIMIT) in stats["tiles_refused"][0]["kind"], stats
    assert stats["tiles_refused"][0]["kind"] != "źródło niedostępne", stats


# --- provenance: suma zapytania nie może opisywać zapytania, którego nie było ------

def test_the_fallback_records_its_own_query_hash_not_the_overpass_one():
    """`query_sha256` przy drodze zapasowej NIE MOŻE być sumą zapytania Overpassa.

    To jest pole provenance i jedyne, co mówi, o co zapytano. Wpisanie tam sumy
    zapytania, którego nikt nie wysłał, jest gorsze niż brak pola: wygląda jak
    potwierdzenie, że dane wzięto z Overpassa. Kontrola negatywna jest wbudowana —
    ta sama funkcja bez `query_text` MA dać sumę Overpassową, więc test odróżnia
    „inna suma" od „suma się nie liczy".
    """
    points = [(BASE_X, BASE_Y), (BASE_X + 100.0, BASE_Y)]
    payload = {"elements": [{"type": "way", "id": 11, "geometry": [
        {"lon": lon, "lat": lat} for lon, lat in
        (CRS.lambert72_to_wgs84(BASE_X - 50.0, BASE_Y + 1.0),
         CRS.lambert72_to_wgs84(BASE_X + 150.0, BASE_Y + 1.0))]}]}
    overpass_hash = X.P.sha256_bytes(X.overpass_query(points).encode("utf-8"))
    default = X._osm_metrics(points, payload, {"status": "ok"})
    assert default["query_sha256"] == overpass_hash, default["query_sha256"]
    fallback = X._osm_metrics(points, payload, {"status": "ok"},
                              query_text="https://api.openstreetmap.org/api/0.6/map kafle 8")
    assert fallback["query_sha256"] != overpass_hash, fallback["query_sha256"]


# --- zdanie o pochodzeniu: musi NAZYWAĆ źródło -------------------------------------

def test_every_osm_route_has_a_sentence_that_names_its_host():
    """Każda droga ma zdanie, a w zdaniu stoi HOST — nie samo słowo „ok".

    Host jest brany z `OSM_API_URL` i `OVERPASS_URL`, więc podmiana adresu w kodzie
    bez podmiany zdania zapala tę bramkę. Zdanie „ok, pobrano" przechodziłoby test
    na obecność zdania i nie mówiłoby nic — dlatego sprawdzana jest treść.
    """
    api_host = X.OSM_API_URL.split("//")[1].split("/")[0]
    overpass_host = X.OVERPASS_URL.split("//")[1].split("/")[0]
    assert overpass_host in X.OSM_SOURCE_SENTENCES[X.OSM_SOURCE_OVERPASS]
    assert api_host in X.OSM_SOURCE_SENTENCES[X.OSM_SOURCE_API]
    for route, sentence in X.OSM_SOURCE_SENTENCES.items():
        assert len(sentence.split()) >= 5, (route, sentence)


def test_the_sentence_separates_the_primary_route_from_the_fallback():
    """Dwa zdania nie mogą być wymienne — inaczej wypis nie odróżnia dróg.

    Zapasowa mówi też, czego NIE daje: brak języka zapytań i filtr lokalny. To nie
    ozdoba — czytający raport ma z tego jednego zdania wiedzieć, że pobrano cały
    prostokąt i przesiano go u siebie.
    """
    primary = X.osm_source_sentence({"status": "ok", "source": X.OSM_SOURCE_OVERPASS})
    fallback = X.osm_source_sentence({"status": "ok", "source": X.OSM_SOURCE_API})
    assert primary != fallback
    assert "PODSTAWOWA" in primary and "ZAPASOWA" in fallback, (primary, fallback)
    assert "LOKALNIE" in fallback, fallback
    assert "bez języka zapytań" in fallback, fallback


def test_a_status_other_than_ok_is_prefixed_to_the_sentence_and_ok_is_not():
    """Warunek `status != "ok"` steruje tym, czy zdanie niesie status — obie strony.

    **Znaleziona przeglądem mutacyjnym własnej bramki** (6.B52, `7f116a4`): mutacja
    `!=` → `==` w `osm_source_sentence` PRZEŻYŁA. Odwrócona gałąź nie wywala niczego —
    dokleja słowo „ok" do zdania o źródle sprawdzonym i **zdejmuje** słowo
    „niedostępne" ze zdania o źródle, którego nie udało się pobrać. Czyli dokładnie
    zamienia stan zdrowy w chory i chory w zdrowy, w wypisie, którego jedynym zadaniem
    jest powiedzieć, co się stało. Pozostałe testy tego nie widziały, bo sprawdzały
    treść zdania, nie obecność przedrostka.

    Dlatego tu są OBIE strony progu naraz: `ok` bez przedrostka, `niedostępne`
    z przedrostkiem. Jednostronna asercja przechodziłaby dla obu wersji kodu.
    """
    healthy = X.osm_source_sentence({"status": "ok", "source": X.OSM_SOURCE_API})
    broken = X.osm_source_sentence({"status": "niedostępne", "source": X.OSM_SOURCE_API})
    partial = X.osm_source_sentence({"status": "częściowe", "source": X.OSM_SOURCE_API})
    assert broken.startswith("niedostępne — "), broken
    assert partial.startswith("częściowe — "), partial
    assert not healthy.startswith("ok"), healthy
    assert healthy == X.OSM_SOURCE_SENTENCES[X.OSM_SOURCE_API], healthy
    assert broken.endswith(healthy), (broken, healthy)


def test_an_unknown_source_is_called_unknown_instead_of_getting_a_default():
    """Źródło, którego słownik nie zna, ma być NAZWANE nieznanym.

    Domyślne „overpass" byłoby tu przypisaniem źródła na podstawie milczenia — i to
    jest dokładnie ta pomyłka, przed którą ta bramka broni.
    """
    sentence = X.osm_source_sentence({"status": "ok", "source": "cokolwiek"})
    assert "NIEZNANE" in sentence, sentence
    assert "cokolwiek" in sentence, sentence
    assert X.osm_source_sentence({"status": "pominięte"}) == "NIE PYTANO (--skip-osm)"


def test_a_local_snapshot_says_whether_it_declares_its_own_origin():
    """Snapshot bez `osm_source` ma to POWIEDZIEĆ, a nie zostać uznanym za Overpass."""
    declared = X.osm_source_sentence({"status": "ok", "source": "snapshot lokalny",
                                      "snapshot_osm_source": X.OSM_SOURCE_API})
    silent = X.osm_source_sentence({"status": "ok", "source": "snapshot lokalny"})
    assert X.OSM_SOURCE_API in declared, declared
    assert "NIE deklaruje" in silent, silent


# --- surface_sections: snapshot nie jest nazywany Overpassem na wiarę ---------------

def test_surface_sections_reads_the_declared_origin_of_the_snapshot():
    """Do 6.B52 to pole niosło stałą „overpass snapshot" dla KAŻDEGO pliku.

    Odkąd snapshot da się zbudować z surowego API OSM, ta stała nazywała złe źródło
    — i to w polu, którego jedynym zadaniem jest powiedzieć, skąd są dane. Test
    podaje oba warianty: z deklaracją i bez, bo różnica między nimi jest tu całą
    treścią.
    """
    assert SS.snapshot_source_label({"osm_source": "osm-api"}) == "snapshot: osm-api"
    assert SS.snapshot_source_label({"osm_source": "overpass"}) == "snapshot: overpass"
    silent = SS.snapshot_source_label({"elements": []})
    assert silent == SS.SNAPSHOT_SOURCE_UNDECLARED, silent
    assert "overpass" not in silent.lower(), silent


# --- main(): wypis, snapshot i tryb odmowy -----------------------------------------

def _alignment(directory):
    path = os.path.join(directory, "axis.json")
    with open(path, "w", encoding="utf-8") as handle:
        json.dump({"id": "T_FALLBACK", "source_crs": "EPSG:31370",
                   "origin_source_crs": [BASE_X, BASE_Y],
                   "points": [[0.0, 0.0, 0.0], [100.0, 0.0, 0.0], [200.0, 0.0, 0.0]]}, handle)
    return path


def _urbis(directory):
    path = os.path.join(directory, "urbis.json")
    with open(path, "w", encoding="utf-8") as handle:
        json.dump({"features": []}, handle)
    return path


def _run_main(extra, fake=None):
    with tempfile.TemporaryDirectory() as tmp:
        args = ["--alignment", _alignment(tmp), "--urbis-file", _urbis(tmp),
                "--out", os.path.join(tmp, "build", "crosscheck.json")] + [
            a.replace("@TMP@", tmp) for a in extra]
        buffer = io.StringIO()
        # `SystemExit` z argparse musi być tu ZŁAPANY i zamieniony w `AssertionError`.
        # Inaczej ucieka z testu jako `BaseException`, którego `test_all.py` nie łapie
        # (`except Exception`), i wywraca CAŁY zestaw zamiast tylko tego testu —
        # zmierzone przy kontroli negatywnej ze zdjętym `--osm-source`: przebieg kończył
        # się kodem 2 na trzecim teście i osiem następnych nie wykonało się wcale.
        # Ten sam wzorzec i ten sam powód, co w `test_fetchers.py` dla `--offline`.
        try:
            if fake is None:
                with contextlib.redirect_stdout(buffer):
                    code = X.main(args)
            else:
                with _fake_network(fake), contextlib.redirect_stdout(buffer):
                    code = X.main(args)
        except SystemExit as exc:
            raise AssertionError(f"main() odmówiło uruchomienia: {exc}") from exc
        with open(args[args.index("--out") + 1], encoding="utf-8") as handle:
            report = json.load(handle)
        snapshot = None
        if "--osm-snapshot-out" in args:
            with open(args[args.index("--osm-snapshot-out") + 1], encoding="utf-8") as handle:
                snapshot = json.load(handle)
        return code, buffer.getvalue(), report, snapshot


def test_main_prints_a_source_line_that_names_the_fallback_host():
    """**To jest ta asercja, dla której ta bramka istnieje.**

    Wypis musi nazwać host, z którego przyszły dane. Zmutowanie zdania — zdjęcie
    hosta, zamiana `[ŹRÓDŁO]` na cokolwiek innego, zlanie obu dróg w jedno „ok" —
    zapala dokładnie ten test. Sprawdzany jest też plik wyniku, bo wypis ginie razem
    z konsolą, a `osm.source` przeżywa proces i to on trafia do raportów.
    """
    bbox = X.query_bbox_lonlat([(BASE_X, BASE_Y), (BASE_X + 200.0, BASE_Y)])
    tiles = X.osm_api_tiles(bbox)
    nodes = {"1": (BASE_X - 50.0, BASE_Y + 1.0), "2": (BASE_X + 250.0, BASE_Y + 1.0)}
    xml = _map_xml([{"id": 11, "nodes": ["1", "2"],
                     "tags": {"railway": "subway", "tunnel": "yes"}}], nodes)
    fake = _FakeFetch({_tile_key(t): xml for t in tiles})
    code, output, report, snapshot = _run_main(
        ["--osm-source", X.OSM_SOURCE_API, "--osm-sleep-s", "0",
         "--osm-snapshot-out", os.path.join("@TMP@", "snapshot.json")], fake)
    assert code == 0, code
    assert "[ŹRÓDŁO] osm: " in output, output
    assert "api.openstreetmap.org/api/0.6/map" in output, output
    assert "ZAPASOWA" in output, output
    assert report["osm"]["source"] == X.OSM_SOURCE_API, report["osm"]
    assert snapshot["osm_source"] == X.OSM_SOURCE_API, snapshot
    assert snapshot["elements"][0]["id"] == 11, snapshot


def test_main_names_the_primary_route_differently_from_the_fallback():
    """Kontrola negatywna dla testu wyżej: przy drodze podstawowej w wypisie stoi
    host Overpassa i słowo PODSTAWOWA, a nie hosta OSM. Bez tej pary asercji test
    wyżej przechodziłby dla wypisu, który zawsze mówi „ZAPASOWA"."""
    def refuses(*_args, **_kwargs):
        raise RuntimeError("overpass-api.de: Connection reset by peer")

    _code, output, report, _snapshot = _run_main([], refuses)
    assert "overpass-api.de/api/interpreter" in output, output
    assert "PODSTAWOWA" in output, output
    assert "api.openstreetmap.org" not in output, output
    assert report["osm"]["status"] == "niedostępne", report["osm"]
    assert report["osm"]["source"] == X.OSM_SOURCE_OVERPASS, report["osm"]


def test_offline_refuses_both_routes_without_touching_the_network():
    """`--offline` ma ODMÓWIĆ, a nie czekać na timeout gniazda.

    Podstawiony `fetch_url` rzuca wyjątek przy każdym wywołaniu, więc gdyby tryb
    odmowy jednak sięgnął do sieci, status byłby `niedostępne`, nie `odmowa`.
    Sprawdzane są obie drogi, bo przełącznik źródła i tryb odmowy to dwa niezależne
    parametry i odmowa nie może zależeć od tego, którą drogę wybrano.
    """
    def refuses(*_args, **_kwargs):
        raise AssertionError("fetch_url wywołane mimo --offline")

    for source in (X.OSM_SOURCE_OVERPASS, X.OSM_SOURCE_API):
        code, output, report, _snapshot = _run_main(
            ["--offline", "--osm-source", source], refuses)
        assert code == 0, (source, code)
        assert report["osm"]["status"] == "odmowa --offline", (source, report["osm"])
        assert report["osm"]["source"] == source, report["osm"]
        assert "odmowa --offline" in output, output


def test_offline_refuses_urbis_too_and_says_so():
    """UrbIS odpowiadał w dniu pomiaru HTTP 200, a Overpass nie — więc „brak sieci"
    nie jest stanem zero-jedynkowym i tryb odmowy musi obejmować OBA źródła.
    Inaczej `--offline` nadal wychodziłby w sieć, tylko po drugie źródło."""
    def refuses(*_args, **_kwargs):
        raise AssertionError("fetch_url wywołane mimo --offline")

    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, "build", "crosscheck.json")
        buffer = io.StringIO()
        with _fake_network(refuses), contextlib.redirect_stdout(buffer):
            code = X.main(["--alignment", _alignment(tmp), "--out", out, "--offline"])
        with open(out, encoding="utf-8") as handle:
            report = json.load(handle)
    assert code == 0, code
    assert report["urbis"]["status"] == "odmowa --offline", report["urbis"]
    assert "--urbis-file" in report["urbis"]["reason"], report["urbis"]
    assert "[KONTROLA] urbis: odmowa --offline" in buffer.getvalue(), buffer.getvalue()


# --- docs/07: droga bez wpisu w hierarchii jest usterką, nie skrótem ---------------

def test_the_source_doc_records_the_fallback_with_its_host_and_its_limits():
    """`docs/07-open-data-research.md` nazywa siebie źródłem prawdy o pochodzeniu
    danych, a do 6.B52 nie miał na `tools/tests/` ani jednej bramki.

    Host jest brany z kodu, nie wpisany tutaj: podmiana `OSM_API_URL` bez podmiany
    dokumentu zapala tę bramkę. Sprawdzane są też trzy rzeczy, których droga zapasowa
    NIE daje — bo wpis, który wymienia tylko zalety, jest reklamą, nie hierarchią.
    """
    text = _doc_text()
    api_host = X.OSM_API_URL.split("//")[1].split("/")[0]
    assert api_host in text, api_host
    assert "/api/0.6/map" in text
    for needle in ("języka zapytań", "kafl", "lokalnie", "transfer"):
        assert needle in text.lower(), needle


def test_the_source_doc_says_when_the_fallback_stops_being_allowed():
    """Wpis bez warunku powrotu zostaje na zawsze — a droga zapasowa jest niżej
    w hierarchii i ma zniknąć, gdy Overpass wróci. Warunek musi stać w dokumencie
    razem z hostem drogi podstawowej, żeby dało się go sprawdzić poleceniem."""
    text = _doc_text()
    overpass_host = X.OVERPASS_URL.split("//")[1].split("/")[0]
    assert overpass_host in text, overpass_host
    assert "ZAPASOWA" in text or "zapasowa" in text
    assert "HTTP 200" in text, "warunek powrotu musi być sprawdzalny poleceniem"


def test_the_source_doc_keeps_osm_below_the_official_sources():
    """Kontrola negatywna dla dwóch testów wyżej: dopisanie drogi zapasowej nie może
    awansować OSM w hierarchii. Kolejność sześciu klas źródeł zostaje ta sama, co
    w `data/network/sources.json`, i to jest sprawdzane wprost."""
    text = _doc_text()
    with open(os.path.join(ROOT, "data", "network", "sources.json"), encoding="utf-8") as handle:
        priority = json.load(handle)["policy"]["priority"]
    assert priority.index("openstreetmap") > priority.index("official_stib")
    assert priority.index("openstreetmap") > priority.index("official_brussels_region")
    stib_at = text.index("STIB/MIVB Open Data i oficjalne publikacje STIB")
    osm_at = text.index("**OpenStreetMap** — szczegóły torowe")
    assert stib_at < osm_at, (stib_at, osm_at)


# 6.D25: uruchomienie tego pliku WPROST idzie ta sama droga, co caly zestaw —
# z licznikiem asercji i z odmowa przy zerze testow. Bez tej gałęzi `python3
# tools/tests/<modul>.py` konczyl sie kodem 0, nie wykonawszy ani jednego testu.
if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))
