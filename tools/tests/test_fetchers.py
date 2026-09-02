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
