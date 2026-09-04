#!/usr/bin/env python3
"""Testy `fetch_osm_routes.py` i `fetch_stib_shapes.py` — dwóch modułów bez pokrycia.

Do 02.09.2026 nie dotykał ich żaden test. `fetch_osm_routes` jest konsumowany przez
`crosscheck_alignment.py`, a `fetch_stib_shapes` pojawia się tylko w komunikacie
błędu w `build_alignment.py` — czyli oba są wołane, a żadnego nikt nie sprawdzał.

**Żaden test tutaj nie rusza sieci.** Testowane są funkcje czyste oraz ŚCIEŻKI
ODMOWY, czyli to, co ma się stać, gdy pobrany plik jest nie taki, jak trzeba.
Portal `data.stib-mivb.brussels` jest zresztą wygaszony i przekierowuje na
`data.belgianmobility.io` (korekta T-110 z 01.09.2026), więc wołanie prawdziwych
endpointów z testu byłoby dodatkowo bez sensu.
"""
import io
import os
import sys
import tempfile
import zipfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "track"))

import fetch_osm_routes as OSM  # noqa: E402
import fetch_stib_shapes as STIB  # noqa: E402


# --- fetch_osm_routes: numer linii z identyfikatora pakietu ----------------------

def test_route_ref_takes_the_line_number_not_the_package_id():
    """`L2_E` to pakiet E linii 2. Zwracany ma być numer LINII, nie litera pakietu."""
    assert OSM.route_ref_from_id("L2_E") == "2"
    assert OSM.route_ref_from_id("L1_A") == "1"
    assert OSM.route_ref_from_id("L1_B") == "1"


def test_route_ref_strips_leading_zeros_but_never_returns_empty():
    """`lstrip("0")` na samych zerach dałby pusty napis, a pusty `ref` pasuje do
    KAŻDEJ trasy w OSM — zapytanie zwróciłoby cudze linie. Fallback w kodzie jest
    właśnie po to i tu jest sprawdzany."""
    assert OSM.route_ref_from_id("L05_A") == "5"
    assert OSM.route_ref_from_id("L0_A") != ""


def test_route_ref_ignores_everything_after_the_first_underscore():
    assert OSM.route_ref_from_id("L6_C_wariant") == "6"


# --- fetch_osm_routes: okno wyszukiwania -----------------------------------------

def test_seed_bbox_is_centred_on_the_converted_point():
    """Okno ma otaczać punkt, a nie zaczynać się w nim."""
    (west, south, east, north), (lon, lat) = OSM.seed_bbox(148000.0, 170000.0)
    assert west < lon < east, (west, lon, east)
    assert south < lat < north, (south, lat, north)
    assert abs((west + east) / 2.0 - lon) < 1e-9
    assert abs((south + north) / 2.0 - lat) < 1e-9


def test_seed_bbox_lands_in_brussels():
    """Kontrola konwersji Lambert 72 -> WGS84 na punkcie w granicach miasta.

    Bez tego test wyżej przechodziłby także przy zepsutej konwersji: okno byłoby
    poprawnie wyśrodkowane wokół punktu na Antarktydzie.
    """
    _bbox, (lon, lat) = OSM.seed_bbox(148000.0, 170000.0)
    assert 4.2 < lon < 4.5, lon
    assert 50.7 < lat < 51.0, lat


def test_seed_window_is_small_enough_to_be_a_seed():
    """To jest wycinek mapy do znalezienia relacji, nie pobranie całej Brukseli.
    Zbyt duże okno oznacza pobranie megabajtów z API OSM przy każdym uruchomieniu."""
    assert 0.0 < OSM.SEED_HALF_DEG < 0.01, OSM.SEED_HALF_DEG
    assert OSM.MAX_SEED_WAYS > 0


# --- fetch_stib_shapes: co ma się stać, gdy archiwum jest nie takie --------------

def _zip_with(names):
    handle = tempfile.NamedTemporaryFile(suffix=".zip", delete=False)
    with zipfile.ZipFile(handle, "w") as archive:
        for name in names:
            archive.writestr(name, b"x")
    handle.close()
    return handle.name


def _refuses(path, fragment):
    try:
        STIB.inspect_archive(path)
    except SystemExit as exc:
        assert fragment in str(exc), f"inny powód odmowy: {exc}"
        return
    finally:
        os.unlink(path)
    raise AssertionError(f"przeszło, a miało odmówić: {fragment}")


def test_a_file_that_is_not_a_zip_is_refused():
    """Pobranie z wygaszonego portalu zwraca stronę HTML z przekierowaniem, a nie ZIP.
    Bez tej kontroli błąd wyszedłby dopiero przy parsowaniu shapefile'a."""
    handle = tempfile.NamedTemporaryFile(suffix=".zip", delete=False)
    handle.write(b"<!DOCTYPE html><html>302 Found</html>")
    handle.close()
    _refuses(handle.name, "nie jest archiwum ZIP")


def test_an_archive_without_the_required_members_is_refused():
    """Niekompletne archiwum ma zostać odrzucone Z NAZWAMI brakujących plików."""
    path = _zip_with(["cokolwiek.txt"])
    _refuses(path, "niekompletne archiwum")


def test_the_required_members_cover_geometry_attributes_and_projection():
    """Shapefile to trzy pliki, nie jeden. Bez `.dbf` nie ma atrybutów, bez `.prj`
    nie wiadomo, w jakim układzie są współrzędne — a projekt pracuje w EPSG:31370."""
    required = set(STIB.REQUIRED)
    assert any(n.endswith(".shp") for n in required), required
    assert any(n.endswith(".dbf") for n in required), required
    assert any(n.endswith(".prj") for n in required), required


def test_the_archive_prefix_is_optional():
    """Archiwum bywa spakowane z katalogiem nadrzędnym i bez niego. Kod wykrywa to
    sam; test pilnuje, żeby wykrywanie nie zniknęło przy uproszczeniu."""
    assert STIB.PREFIX.endswith("/"), STIB.PREFIX
    path = _zip_with([STIB.PREFIX + "cokolwiek.shp"])
    # Prefiks jest wykryty, więc brakujące pliki są raportowane BEZ prefiksu w nazwie.
    _refuses(path, "niekompletne archiwum")


# --- fetch_osm_routes: filtry, które decydują, co w ogóle wejdzie do danych --------
#
# Przegląd mutacyjny z 03.09.2026 pokazał, że wszystkie dziewięć mutacji w tym module
# przeżywa: `discover_relations` i `fetch_relation_ways` nie były dotknięte żadnym
# testem, bo obie wołają sieć. Wołają ją jednak przez JEDNĄ funkcję — `api_get` —
# więc wystarczy podstawić ją w module, żeby przepuścić przez oba filtry wymyśloną
# odpowiedź OSM. Poniższe testy nie ruszają sieci.


class _FakeApi:
    """Podstawiony `api_get`: mapa ścieżka -> gotowa odpowiedź, plus licznik zapytań.

    Zwraca `(payload, url)` dokładnie jak oryginał. Ścieżka nieznana jest błędem
    testu, a nie pustą odpowiedzią — inaczej zmutowany filtr, który pyta o cudzy
    obiekt, dostałby cicho `{}` i wyglądał na równoważny.
    """

    def __init__(self, responses):
        self.responses = responses
        self.asked = []

    def __call__(self, path, timeout):
        self.asked.append(path)
        assert path in self.responses, f"nieoczekiwane zapytanie: {path}"
        return self.responses[path], "https://example.invalid/" + path


def _relation(rid, ref="2", rtype="route", route="subway", name=None):
    return {"type": "relation", "id": rid,
            "tags": {"type": rtype, "route": route, "ref": ref,
                     "name": name or f"relacja {rid}", "operator": "STIB/MIVB"}}


def _with_fake_api(responses, body):
    original = OSM.api_get
    fake = _FakeApi(responses)
    OSM.api_get = fake
    try:
        return body(fake)
    finally:
        OSM.api_get = original


def test_osm_seed_window_probes_only_subway_ways():
    """Wycinek `/map` zwraca wszystko, co leży pod stacją: perony, ulice, tramwaj.

    Filtr `type == "way" and railway == "subway"` decyduje, których obiektów w ogóle
    zapytamy o relacje macierzyste. Gdy przepuści węzeł albo tramwaj, do snapshotu
    wejdzie cudza linia — a to jest dokładnie ta pomyłka, przez którą „rozstaw torów"
    z ekstraktu bboxowego wyszedł 11 m zamiast 3,9 m (`reports/L1_A-crosscheck.md`).

    Każdy z trzech obiektów ma INNĄ relację macierzystą o tym samym `ref`, więc
    zmutowany filtr nie zwraca pustki, tylko podmienia relację na cudzą — i test
    to widzi.
    """
    responses = {
        "map.json?bbox=4.340000,50.840000,4.360000,50.860000": {"elements": [
            {"type": "way", "id": 11, "tags": {"railway": "subway"}},
            {"type": "way", "id": 12, "tags": {"railway": "tram"}},
            {"type": "node", "id": 13, "tags": {"railway": "subway"}},
            {"type": "way", "id": 14},
        ]},
        "way/11/relations.json": {"elements": [_relation(900)]},
        "way/12/relations.json": {"elements": [_relation(901)]},
        "way/13/relations.json": {"elements": [_relation(902)]},
        "way/14/relations.json": {"elements": [_relation(903)]},
    }
    bbox = (4.34, 50.84, 4.36, 50.86)
    found = _with_fake_api(responses, lambda fake: OSM.discover_relations(
        bbox, "2", 5.0, log=lambda *_a, **_k: None))
    assert [r["id"] for r in found] == [900], found
    fake_asked = _with_fake_api(responses, lambda fake: (OSM.discover_relations(
        bbox, "2", 5.0, log=lambda *_a, **_k: None), fake.asked)[1])
    assert "way/12/relations.json" not in fake_asked, fake_asked
    assert "way/13/relations.json" not in fake_asked, fake_asked


def test_osm_discovery_keeps_only_route_subway_relations():
    """Way metra należy też do relacji, które trasą nie są.

    Prawdziwy way pod Brukselą wisi w `type=route` (kierunek), ale i w relacjach
    `type=route_master` czy w multipoligonach. Bramka `type == "route"` **oraz**
    `route == "subway"` jest jedyną rzeczą, która odróżnia trasę od jej rodzica
    i od obiektu administracyjnego; bez niej do snapshotu wchodzi relacja, której
    `full.json` nie ma geometrii torów.
    """
    responses = {
        "map.json?bbox=4.340000,50.840000,4.360000,50.860000": {"elements": [
            {"type": "way", "id": 11, "tags": {"railway": "subway"}}]},
        "way/11/relations.json": {"elements": [
            _relation(900),
            _relation(901, rtype="route_master"),
            _relation(902, route="tram"),
            {"type": "relation", "id": 903, "tags": {"ref": "2"}},
        ]},
    }
    found = _with_fake_api(responses, lambda _f: OSM.discover_relations(
        (4.34, 50.84, 4.36, 50.86), "2", 5.0, log=lambda *_a, **_k: None))
    assert [r["id"] for r in found] == [900], found


def test_osm_discovery_keeps_only_the_line_ref_that_was_asked_for():
    """Pod Arts-Loi biegną trasy 1, 2, 5 i 6 naraz.

    `ref` jest jedynym kryterium, które je rozdziela. Odwrócenie tej bramki nie daje
    pustego wyniku — daje CUDZĄ LINIĘ z poprawnym kształtem, czyli wynik, który
    przejdzie każdą kontrolę spójności i skończy jako oś nie tej linii.
    """
    responses = {
        "map.json?bbox=4.340000,50.840000,4.360000,50.860000": {"elements": [
            {"type": "way", "id": 11, "tags": {"railway": "subway"}}]},
        "way/11/relations.json": {"elements": [
            _relation(900, ref="2"), _relation(906, ref="6"), _relation(901, ref="1")]},
    }
    found = _with_fake_api(responses, lambda _f: OSM.discover_relations(
        (4.34, 50.84, 4.36, 50.86), "2", 5.0, log=lambda *_a, **_k: None))
    assert [r["id"] for r in found] == [900], found
    assert found[0]["ref"] == "2"


def test_osm_relation_geometry_comes_from_node_elements_only():
    """`relation/<id>/full.json` miesza w jednej liście węzły, way'e i relacje.

    Słownik współrzędnych wolno budować WYŁĄCZNIE z węzłów: tylko one mają `lon`/`lat`.
    Test pilnuje też, że kolejność węzłów way'a jest zachowana — odwrócona albo
    posortowana geometria daje ten sam zbiór punktów i tę samą długość, więc
    kontrola odchyłki by tego nie zauważyła.
    """
    responses = {"relation/900/full.json": {"elements": [
        {"type": "node", "id": 1, "lon": 4.35, "lat": 50.85},
        {"type": "node", "id": 2, "lon": 4.36, "lat": 50.86},
        {"type": "node", "id": 3, "lon": 4.37, "lat": 50.87},
        {"type": "way", "id": 11, "nodes": [3, 1, 2], "tags": {"railway": "subway"}},
        {"type": "relation", "id": 900, "tags": {"type": "route"}},
    ]}}
    ways = _with_fake_api(responses, lambda _f: OSM.fetch_relation_ways(900, 5.0))
    assert [w["id"] for w in ways] == [11], ways
    assert ways[0]["geometry"] == [{"lon": 4.37, "lat": 50.87},
                                   {"lon": 4.35, "lat": 50.85},
                                   {"lon": 4.36, "lat": 50.86}]
    assert ways[0]["route_relations"] == [900]


def test_osm_relation_ways_skip_members_that_are_not_ways():
    """Relacja trasy ma członków-węzłów (stacje jako `stop`/`platform`).

    Gdyby przeszły przez filtr `type != "way"`, snapshot dostałby wpisy bez geometrii
    i `crosscheck_alignment.py` liczyłby odchyłkę od punktów peronowych zamiast od torów.
    """
    responses = {"relation/900/full.json": {"elements": [
        {"type": "node", "id": 1, "lon": 4.35, "lat": 50.85, "tags": {"public_transport": "stop_position"}},
        {"type": "node", "id": 2, "lon": 4.36, "lat": 50.86},
        {"type": "way", "id": 11, "nodes": [1, 2]},
    ]}}
    ways = _with_fake_api(responses, lambda _f: OSM.fetch_relation_ways(900, 5.0))
    assert [w["id"] for w in ways] == [11], ways
    assert all(w["type"] == "way" for w in ways)


def test_osm_way_with_exactly_two_nodes_survives_the_length_gate():
    """Bramka `len(geometry) < 2` liczona DOKŁADNIE NA GRANICY.

    Odcinek dwuwęzłowy to normalny way w OSM — prosty kawałek tunelu między
    rozjazdami bywa opisany dwoma węzłami i jest pełnoprawnym fragmentem trasy.
    Podniesienie progu o jeden (`< 3` albo `<= 2`) wyrzuca go po cichu: snapshot
    nadal się zapisuje, nadal ma way'e, tylko trasa ma dziurę.

    Granica jest tu całkowitoliczbowa, więc trafia się w nią wprost — `len()` zwraca
    dokładnie 2, bez pułapki zmiennoprzecinkowej. Dlatego test podaje OBIE strony
    progu: way o dwóch węzłach ma zostać, way o jednym ma wypaść.
    """
    responses = {"relation/900/full.json": {"elements": [
        {"type": "node", "id": 1, "lon": 4.35, "lat": 50.85},
        {"type": "node", "id": 2, "lon": 4.36, "lat": 50.86},
        {"type": "way", "id": 11, "nodes": [1, 2]},            # dokładnie granica
        {"type": "way", "id": 12, "nodes": [1]},               # pod granicą
        {"type": "way", "id": 13, "nodes": [1, 999]},          # 999 nieznane -> zostaje 1
    ]}}
    ways = _with_fake_api(responses, lambda _f: OSM.fetch_relation_ways(900, 5.0))
    assert [w["id"] for w in ways] == [11], ways
    assert len(ways[0]["geometry"]) == 2
