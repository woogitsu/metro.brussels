#!/usr/bin/env python3
"""Testy kontroli krzyżowej osi wobec UrbIS i OSM — modułu bez pokrycia.

Przegląd mutacyjny z 03.09.2026: z 19 mutacji w `crosscheck_alignment.py` przeżyło
18. Jedynymi testami, jakie ten moduł miał, były cztery asercje w `test_packages.py`
dotyczące `overpass_query`, `chainage_ranges` i `_coverage_and_deviation`. Cała
reszta — test punkt-w-wielokącie, odczyt warstwy UrbIS, budowa metryk OSM,
rzutowanie na odcinek i wypisywanie raportu — nie wykonywała się ani razu.

To jest moduł, którego wynik trafia do `*.provenance.json` jako zdanie „nasza oś
zgadza się z drugim źródłem". Nieprawdziwa liczba jest tu gorsza niż brak liczby,
bo idzie dalej jako fakt.

Bez sieci: warstwa UrbIS i odpowiedź Overpassa są budowane w locie i podawane
przez `--urbis-file` / `--osm-file`, dokładnie tak, jak robi to CI.
"""
import contextlib
import io
import json
import math
import os
import sys
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "track"))
sys.path.insert(0, os.path.join(ROOT, "tools", "data"))

import crosscheck_alignment as X  # noqa: E402
import crs as CRS  # noqa: E402

#: Punkt odniesienia w Lambert 72, w środku brukselskiego pnia. Fikstury są
#: budowane w metrach wokół niego i dopiero na wyjściu zamieniane na WGS84,
#: bo tak wygląda wejście obu źródeł: UrbIS i OSM podają stopnie.
BASE_X, BASE_Y = 150000.0, 170000.0

#: Zapas na obrót przez WGS84 i z powrotem. `tools/tests/test_packages.py` mierzy
#: residuum tej pary transformacji na < 1 mm; 0,05 m to margines z zapasem.
ROUNDTRIP_M = 0.05


def _wgs(x, y):
    """Punkt Lambert 72 jako para [lon, lat] — tak, jak zapisuje go GeoJSON."""
    lon, lat = CRS.lambert72_to_wgs84(x, y)
    return [lon, lat]


def _rect(x0, x1, y0, y1):
    return [_wgs(x0, y0), _wgs(x1, y0), _wgs(x1, y1), _wgs(x0, y1)]


def _tmpjson(directory, name, payload):
    path = os.path.join(directory, name)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle)
    return path


# --- punkt w wielokącie -------------------------------------------------------
#
# `point_in_ring` jest promieniem w prawo. Trzy mutacje na jednym wierszu
# (`(y1 > y) != (y2 > y)`) i jedna na następnym przeżyły wszystkie, bo nikt nigdy
# nie wywołał tej funkcji z testu.

SQUARE = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]


def test_crosscheck_point_in_ring_separates_inside_from_outside():
    """Kontrola negatywna dla wszystkiego niżej: funkcja w ogóle rozróżnia strony.

    Bez tego testy graniczne przechodziłyby też dla funkcji, która zawsze zwraca
    `True` — a taka „kontrola krzyżowa" meldowałaby 100 % pokrycia tunelem dla
    dowolnej osi, łącznie z osią przez Antwerpię.
    """
    assert X.point_in_ring((5.0, 5.0), SQUARE) is True
    assert X.point_in_ring((15.0, 5.0), SQUARE) is False
    assert X.point_in_ring((5.0, 15.0), SQUARE) is False
    assert X.point_in_ring((-5.0, 5.0), SQUARE) is False


def test_crosscheck_point_on_a_horizontal_edge_does_not_divide_by_zero():
    """Krawędź pozioma ma być POMINIĘTA, a nie policzona.

    Warunek `(y1 > y) != (y2 > y)` jest jedyną rzeczą, która nie dopuszcza do
    dzielenia przez `y2 - y1` równe zeru. Każda z trzech mutacji tego wiersza
    — `y1 >= y`, `y2 >= y`, `!=` → `==` — sprawia, że dla punktu leżącego
    dokładnie na wysokości krawędzi poziomej warunek staje się prawdziwy
    i funkcja wywala się `ZeroDivisionError`.

    Próg jest tu trafiony dokładnie bez żadnej sztuczki: `y` punktu i `y` obu
    końców krawędzi to ta sama stała 0.0 wpisana wprost, a nie wynik działania.
    """
    assert X.point_in_ring((5.0, 0.0), SQUARE) is True
    assert X.point_in_ring((5.0, 10.0), SQUARE) is False
    assert X.point_in_ring((15.0, 0.0), SQUARE) is False


def test_crosscheck_vertical_edges_belong_to_the_left_side_only():
    """`x < xin` ma być OSTRE — inaczej wielokąty stykające się bokiem nakładają się.

    Punkt na lewej krawędzi liczy się jako wewnątrz, na prawej jako na zewnątrz.
    Przy `x <= xin` obie krawędzie przełączają flagę i punkt na lewej krawędzi
    wypada na zewnątrz. Dla warstwy UrbIS, w której poligony tuneli sąsiadują ze
    sobą, to różnica między „punkt należy do jednego tunelu" a „punkt nie należy
    do żadnego".

    Granica jest tu dokładna, bo `xin` wychodzi z mnożenia przez zero:
    dla krawędzi pionowej `x2 - x1` to 0.0, więc `xin == x1` co do bitu.
    """
    assert X.point_in_ring((0.0, 5.0), SQUARE) is True
    assert X.point_in_ring((10.0, 5.0), SQUARE) is False


def test_crosscheck_polygon_rings_reads_both_geometry_kinds_and_refuses_the_rest():
    """`Polygon` i `MultiPolygon` mają być rozpoznane po nazwie, a nie „jakoś".

    Obie mutacje (`== "Polygon"` → `!=` i `== "MultiPolygon"` → `!=`) przeżyły,
    bo funkcji nie wołał żaden test. Odwrócenie pierwszego warunku sprawia, że
    warstwa złożona z samych `Polygon` daje zero pierścieni — czyli ciche
    „0 % osi w tunelu" zamiast błędu.
    """
    outer = [[0.0, 0.0], [1.0, 0.0], [1.0, 1.0]]
    hole = [[0.2, 0.2], [0.3, 0.2], [0.3, 0.3]]
    second = [[5.0, 5.0], [6.0, 5.0], [6.0, 6.0]]

    assert X.polygon_rings({"type": "Polygon", "coordinates": [outer, hole]}) == [outer]
    assert X.polygon_rings(
        {"type": "MultiPolygon", "coordinates": [[outer, hole], [second]]}) == [outer, second]
    # Kontrola negatywna: cokolwiek innego ma dać pustą listę, a nie wyjątek
    # ani przypadkowy pierwszy element.
    assert X.polygon_rings({"type": "LineString", "coordinates": outer}) == []
    assert X.polygon_rings({}) == []


# --- warstwa UrbIS ------------------------------------------------------------

def _urbis_layer():
    """Trzy poligony: tunel podziemny, tunel z `niveau=0` i stacja."""
    return {"features": [
        {"properties": {"type": "MT", "niveau": "-1", "name_fr": "Tunel A"},
         "geometry": {"type": "Polygon",
                      "coordinates": [_rect(BASE_X - 100.0, BASE_X + 100.0,
                                            BASE_Y - 50.0, BASE_Y + 50.0)]}},
        {"properties": {"type": "MT", "niveau": "0", "name_fr": "Wiadukt"},
         "geometry": {"type": "Polygon",
                      "coordinates": [_rect(BASE_X + 200.0, BASE_X + 400.0,
                                            BASE_Y - 50.0, BASE_Y + 50.0)]}},
        {"properties": {"type": "MS", "niveau": "-2", "name_nl": "Station"},
         "geometry": {"type": "Polygon",
                      "coordinates": [_rect(BASE_X + 500.0, BASE_X + 600.0,
                                            BASE_Y - 50.0, BASE_Y + 50.0)]}},
    ]}


#: Sześć punktów: dwa w tunelu podziemnym, dwa w `niveau=0`, jeden w stacji,
#: jeden poza wszystkim. Odstępy 100/200/100/200/250 m dają kilometraż
#: 0, 100, 300, 400, 600, 850 — potrzebny do sprawdzenia przedziałów.
URBIS_POINTS = [(BASE_X - 50.0, BASE_Y), (BASE_X + 50.0, BASE_Y),
                (BASE_X + 250.0, BASE_Y), (BASE_X + 350.0, BASE_Y),
                (BASE_X + 550.0, BASE_Y), (BASE_X + 800.0, BASE_Y)]


def _urbis_result():
    with tempfile.TemporaryDirectory() as tmp:
        path = _tmpjson(tmp, "urbis.json", _urbis_layer())
        return X.crosscheck_urbis(URBIS_POINTS, timeout=1.0, local_file=path)


def test_crosscheck_urbis_counts_tunnel_station_and_outside_separately():
    """Trzy liczby, które trafiają do raportu pakietu, mają się sumować do 100 %.

    Fikstura jest tak dobrana, żeby każda z nich była INNA — przy równych
    wartościach test przechodziłby dla funkcji, która zwraca zawsze to samo.
    """
    result = _urbis_result()
    assert result["status"] == "ok"
    assert result["features"] == 3
    assert result["polygons"] == {"MT": 2, "MS": 1}
    assert result["points_checked"] == 6
    assert result["inside_tunnel_pct"] == round(100.0 * 4 / 6, 1), result
    assert result["inside_station_pct"] == round(100.0 * 1 / 6, 1), result
    assert result["outside_pct"] == round(100.0 * 1 / 6, 1), result


def test_crosscheck_urbis_niveau0_is_measured_not_assumed():
    """`niveau=0` jest wejściem dla R-005 i musi opisywać TE poligony, co trzeba.

    Dwie mutacje (`hit["niveau"] == "0"` w obu wierszach zamienione na `!=`)
    przeżyły. Odwrócenie tego porównania nie wywala niczego — po prostu
    przypisuje etykietę „prawdopodobnie naziemne" wszystkim odcinkom
    PODZIEMNYM, a raport niesie to dalej jako pomiar.

    Dlatego fikstura ma trzy różne poziomy (`-1`, `0`, `-2`) i test sprawdza
    zarówno nazwę poligonu, jak i przedział kilometrażu.
    """
    result = _urbis_result()
    assert result["by_niveau"] == {"MS/niveau=-2": 1, "MT/niveau=-1": 2, "MT/niveau=0": 2}
    assert result["niveau0_points"] == 2, result
    assert result["niveau0_pct"] == round(100.0 * 2 / 6, 1), result
    assert result["niveau0_polygons"] == {"Wiadukt": 2}, result
    # Punkty 2 i 3 leżą na kilometrażu 300 i 400 (odstępy 100, 200, 100, 200, 250).
    assert result["niveau0_chainage_ranges_m"] == [[300.0, 400.0]], result


def test_crosscheck_urbis_names_come_from_french_or_dutch_column():
    """Poligon bez `name_fr` ma być rozpoznany po `name_nl`, a nie zniknąć.

    Kontrola negatywna dla testu wyżej: gdyby nazwa była brana tylko z jednego
    pola, `niveau0_polygons` bywałby pusty i asercja o `{"Wiadukt": 2}` nadal
    by przechodziła dla innych fikstur.
    """
    layer = _urbis_layer()
    layer["features"][1]["properties"] = {"type": "MT", "niveau": "0", "name_nl": "Viaduct"}
    with tempfile.TemporaryDirectory() as tmp:
        path = _tmpjson(tmp, "urbis.json", layer)
        result = X.crosscheck_urbis(URBIS_POINTS, timeout=1.0, local_file=path)
    assert result["niveau0_polygons"] == {"Viaduct": 2}, result


def test_crosscheck_urbis_empty_layer_reports_everything_outside():
    """Pusta warstwa to wynik „nic nie potwierdzone", a nie dzielenie przez zero."""
    with tempfile.TemporaryDirectory() as tmp:
        path = _tmpjson(tmp, "urbis.json", {"features": []})
        result = X.crosscheck_urbis(URBIS_POINTS, timeout=1.0, local_file=path)
    assert result["outside_pct"] == 100.0, result
    assert result["niveau0_chainage_ranges_m"] == [], result


# --- rzut punktu na łamaną ----------------------------------------------------

def test_crosscheck_distance_to_polyline_projects_onto_the_segment():
    """Podstawa wszystkich odchyłek: rzut prostopadły, nie odległość do wierzchołka."""
    line = [(0.0, 0.0), (100.0, 0.0)]
    assert X._distance_to_polyline((50.0, 3.0), line) == 3.0
    assert X._distance_to_polyline((-10.0, 0.0), line) == 10.0
    assert X._distance_to_polyline((0.0, 0.0), line) == 0.0


def test_crosscheck_duplicated_vertex_does_not_divide_by_zero():
    """`seg <= 0` musi obejmować zero — inaczej powtórzony wierzchołek wywala moduł.

    Powtórzone wierzchołki są w OSM normalne (koniec jednego way'a i początek
    drugiego po scaleniu). Mutacja `seg < 0` zamienia je w `ZeroDivisionError`
    w środku kontroli krzyżowej. Granica jest dokładna: `dx` i `dy` wychodzą
    z odejmowania dwóch identycznych double'i, więc `seg` to dokładnie 0.0.
    """
    degenerate = [(0.0, 0.0), (0.0, 0.0)]
    assert X._distance_to_polyline((3.0, 4.0), degenerate) == 5.0


def test_crosscheck_short_segment_is_still_projected_not_collapsed():
    """`seg <= 0` ma odsiewać TYLKO odcinki zerowe, nie krótkie.

    Mutacja podnosząca próg do 1 (czyli metr kwadratowy — `seg` jest kwadratem
    długości) każe zastąpić rzutowanie odległością do początku odcinka. Dla
    odcinka pół metra różnica wychodzi 1,0 m wobec 1,118 m, czyli w tym samym
    rzędzie, co cała mierzona odchyłka od OSM.
    """
    short = [(0.0, 0.0), (0.5, 0.0)]
    assert X._distance_to_polyline((0.5, 1.0), short) == 1.0
    assert math.isclose(X._distance_to_polyline((0.0, 0.0), [(0.0, 0.0), (0.5, 0.0)]), 0.0)


def test_crosscheck_projection_is_clamped_exactly_at_the_segment_ends():
    """Parametr `t` ma być przycięty do [0, 1] — dokładnie, nie „mniej więcej".

    Punkt 0,5 m za końcem stumetrowego odcinka daje `t = 1.005`. Przy progu
    przesuniętym na 1,01 przycięcie się nie odpala i funkcja liczy odległość
    do punktu POZA odcinkiem, czyli zwraca 0,0 zamiast 0,5. Odchyłka zerowa
    tam, gdzie jej nie ma, to dokładnie ten rodzaj kłamstwa, przed którym
    ma bronić kontrola krzyżowa.

    `t` jest tu dokładne: 100,5 · 100 / 10000 to działanie na liczbach
    o krótkich mantysach binarnych.
    """
    line = [(0.0, 0.0), (100.0, 0.0)]
    assert ((100.5 - 0.0) * 100.0 + 0.0) / 10000.0 == 1.005, "fikstura minęła próg"
    assert X._distance_to_polyline((100.5, 0.0), line) == 0.5
    assert X._distance_to_polyline((-0.5, 0.0), line) == 0.5


def test_crosscheck_coverage_radius_is_inclusive_at_exactly_the_radius():
    """Punkt oddalony DOKŁADNIE o promień pokrycia jeszcze się liczy.

    50 m da się trafić co do bitu: rzut punktu (50, 50) na odcinek
    (0,0)–(100,0) wypada w (50, 0) — `t` wychodzi 0,5, a `math.dist` na
    różnicy (0, 50) zwraca 50.0 bez żadnego zaokrąglenia. To jedyne miejsce
    w tym module, w którym próg jest okrągłą liczbą, a mimo to daje się
    dotknąć dokładnie.

    Kontrola negatywna po drugiej stronie jest w `test_packages.py`
    (`coverage_radius_is_pinned_and_two_sided`), ale tamta stoi pół metra od
    progu, więc nie odróżnia `<=` od `<`.
    """
    segments = [[(0.0, 0.0), (100.0, 0.0)]]
    assert X._distance_to_polyline((50.0, 50.0), segments[0]) == X.OSM_COVERAGE_RADIUS_M

    on_radius = X._coverage_and_deviation([(50.0, X.OSM_COVERAGE_RADIUS_M)], segments)
    assert on_radius["coverage_pct"] == 100.0, on_radius
    assert on_radius["deviation_max_m"] == 50.0, on_radius

    past = X._coverage_and_deviation(
        [(50.0, math.nextafter(X.OSM_COVERAGE_RADIUS_M, math.inf))], segments)
    assert past["coverage_pct"] == 0.0, past
    assert "deviation_median_m" not in past, past


# --- metryki OSM --------------------------------------------------------------

def _way(offset_m, relations, x0=-200.0, x1=400.0):
    """Way biegnący równolegle do osi, odsunięty o `offset_m` metrów."""
    return {"type": "way", "route_relations": list(relations),
            "geometry": [{"lon": lon, "lat": lat} for lon, lat in
                         (CRS.lambert72_to_wgs84(BASE_X + x0, BASE_Y + offset_m),
                          CRS.lambert72_to_wgs84(BASE_X + x1, BASE_Y + offset_m))]}


OSM_POINTS = [(BASE_X, BASE_Y), (BASE_X + 100.0, BASE_Y), (BASE_X + 200.0, BASE_Y)]


def _osm_payload():
    return {"elements": [_way(2.0, [111]), _way(4.0, [222])],
            "routes": [{"id": 111, "name": "L1 → Stockel"},
                       {"id": 222, "name": "L1 → Erasme"}]}


def test_crosscheck_osm_metrics_measure_deviation_per_direction():
    """Odchyłka ma być liczona osobno dla każdej relacji kierunkowej.

    Mutacja `route.get("id") == relation` → `!=` przeżyła: podpina do kierunku
    nazwę SĄSIEDNIEGO kierunku. Raport wygląda wtedy identycznie i jest
    nieprawdziwy. Fikstura ma dlatego dwie relacje o różnych odsunięciach
    (2 m i 4 m) — sama nazwa bez różnicy w liczbach by tego nie złapała.
    """
    result = X._osm_metrics(OSM_POINTS, _osm_payload(), {"status": "ok"})
    assert result["ways"] == 2, result
    assert result["coverage_pct"] == 100.0, result
    assert abs(result["deviation_median_m"] - 2.0) < ROUNDTRIP_M, result

    by_relation = {d["relation"]: d for d in result["per_relation"]}
    assert set(by_relation) == {111, 222}, result["per_relation"]
    assert by_relation[111]["name"] == "L1 → Stockel", by_relation[111]
    assert by_relation[222]["name"] == "L1 → Erasme", by_relation[222]
    assert abs(by_relation[111]["deviation_median_m"] - 2.0) < ROUNDTRIP_M, by_relation[111]
    assert abs(by_relation[222]["deviation_median_m"] - 4.0) < ROUNDTRIP_M, by_relation[222]


def test_crosscheck_osm_metrics_take_ways_and_nothing_else():
    """Filtr `type == "way"` ma wybierać way'e, a nie „wszystko oprócz".

    Overpass zwraca w jednej odpowiedzi także obiekty innych typów. Mutacja
    `!=` odwraca wybór: moduł liczyłby odchyłkę od geometrii, która nie jest
    torem. Fikstura wkłada dlatego obok way'a element `relation` z geometrią
    odsuniętą o 5 km — na tyle daleko, że odwrócenie filtru widać w wyniku
    jako „brak pokrycia", a nie jako drobną zmianę liczby.
    """
    payload = _osm_payload()
    payload["elements"].append({"type": "relation", "geometry": [
        {"lon": lon, "lat": lat} for lon, lat in
        (CRS.lambert72_to_wgs84(BASE_X, BASE_Y + 5000.0),
         CRS.lambert72_to_wgs84(BASE_X + 400.0, BASE_Y + 5000.0))]})

    result = X._osm_metrics(OSM_POINTS, payload, {"status": "ok"})
    assert result["ways"] == 2, result
    assert result["coverage_pct"] == 100.0, result


def test_crosscheck_osm_metrics_report_no_coverage_instead_of_faking_zero():
    """Brak pokrycia ma być nazwany, a nie zamieniony w odchyłkę 0 m."""
    far = {"elements": [{"type": "way", "geometry": [
        {"lon": lon, "lat": lat} for lon, lat in
        (CRS.lambert72_to_wgs84(BASE_X, BASE_Y + 5000.0),
         CRS.lambert72_to_wgs84(BASE_X + 400.0, BASE_Y + 5000.0))]}]}
    result = X._osm_metrics(OSM_POINTS, far, {"status": "ok"})
    assert result["status"] == "brak pokrycia", result
    assert "deviation_median_m" not in result, result

    empty = X._osm_metrics(OSM_POINTS, {"elements": []}, {"status": "ok"})
    assert empty["status"] == "brak danych" and empty["ways"] == 0, empty


def test_crosscheck_osm_snapshot_path_records_the_file_hash():
    """Ścieżka `--osm-file`: wynik ma nieść skąd pochodzi, bo nie ma URL-a."""
    with tempfile.TemporaryDirectory() as tmp:
        path = _tmpjson(tmp, "osm.json", _osm_payload())
        result = X.crosscheck_osm(OSM_POINTS, timeout=1.0, local_file=path)
    assert result["source"] == "snapshot lokalny"
    assert result["file"] == "osm.json"
    assert len(result["file_sha256"]) == 64, result["file_sha256"]
    assert result["coverage_pct"] == 100.0, result


# --- raport z main() ----------------------------------------------------------

def _alignment_document():
    """Oś w formacie, jakiego oczekuje `load_alignment`: punkty względem origin."""
    return {"id": "T_TEST", "source_crs": "EPSG:31370",
            "origin_source_crs": [BASE_X, BASE_Y],
            "points": [[x - BASE_X, y - BASE_Y, 0.0] for x, y in URBIS_POINTS]}


def _run_main(extra):
    with tempfile.TemporaryDirectory() as tmp:
        alignment = _tmpjson(tmp, "axis.json", _alignment_document())
        urbis = _tmpjson(tmp, "urbis.json", _urbis_layer())
        out = os.path.join(tmp, "build", "crosscheck.json")
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = X.main(["--alignment", alignment, "--out", out,
                           "--urbis-file", urbis] + extra)
        with open(out, encoding="utf-8") as handle:
            report = json.load(handle)
        return code, buffer.getvalue(), report


def test_crosscheck_main_prints_details_for_ok_and_a_status_line_for_the_rest():
    """`if entry["status"] != "ok": continue` steruje CAŁYM wypisywaniem raportu.

    Mutacja na `==` odwraca to: źródło sprawdzone dostaje jednolinijkowe
    „ok" bez ani jednej liczby, a źródło pominięte wpada w gałąź szczegółów
    i moduł wywala się na brakującym kluczu. Drugą mutację na tym fragmencie
    (`if name == "urbis"` → `!=`) widać tak samo — UrbIS trafia do gałęzi OSM.

    Dlatego jeden przebieg musi mieć OBA stany naraz: UrbIS ze statusem `ok`
    i OSM pominięty. Test sprawdza treść obu wierszy, a nie ich obecność.
    """
    code, output, report = _run_main(["--skip-osm"])
    assert code == 0
    assert report["alignment_id"] == "T_TEST"
    assert report["points"] == len(URBIS_POINTS)
    assert report["osm"] == {"status": "pominięte"}
    assert report["urbis"]["status"] == "ok"

    assert "[KONTROLA] osm: pominięte" in output, output
    assert "[KONTROLA] urbis: tunel 66.7%, stacja 16.7%, poza 16.7%" in output, output
    assert "niveau=0 na 2 punktach (33.3%)" in output, output
    assert "[NIVEAU0]" in output and "Wiadukt" in output, output
    assert "kilometraż 300.0–400.0 m (100.0 m)" in output, output


def test_crosscheck_main_writes_a_canonical_report_file():
    """Raport ma powstać jako plik — to on trafia do prowenancji pakietu."""
    _code, _output, report = _run_main(["--skip-osm"])
    assert set(report) == {"alignment_id", "checked_at", "source_crs", "points",
                           "urbis", "osm"}, sorted(report)
    assert report["source_crs"] == "EPSG:31370"
    assert report["urbis"]["niveau0_chainage_ranges_m"] == [[300.0, 400.0]]


def test_crosscheck_main_skipping_both_sources_prints_two_status_lines():
    """Kontrola negatywna: gdy nic nie jest sprawdzone, raport ma to powiedzieć
    dwa razy i nie udawać, że coś zmierzył."""
    _code, output, report = _run_main(["--skip-osm", "--skip-urbis"])
    assert report["urbis"] == {"status": "pominięte"}
    assert "[KONTROLA] urbis: pominięte" in output, output
    assert "[KONTROLA] osm: pominięte" in output, output
    assert "[NIVEAU0]" not in output, output
