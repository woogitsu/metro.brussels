#!/usr/bin/env python3
"""Testy walidatora osi w miejscach, które przepuszczał milczkiem.

Walidator miał na rzut ostatniej stacji tolerancję 50 m bez uzasadnienia. Przepuszczała
ona przekroczenia rzędu pół metra we wszystkich sześciu pakietach — i przepuściłaby też
stację leżącą 49 m poza osią, czyli błąd danych, a nie artefakt rzutowania. Te testy
przypinają regułę, która zastąpiła tę liczbę: **przekroczenie nie może być większe niż
ostatni odcinek łamanej**.
"""
import json
import math
import os
import sys
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "track"))

import validate as V  # noqa: E402

#: Krok łamanej w osiach z T-210. Stały, żeby długość ostatniego odcinka była znana.
STEP_M = 15.0


def _axis(station_chainages, points=60, step=STEP_M, length_m=None):
    """Prosta oś wzdłuż osi X, z zadanymi kilometrażami stacji."""
    coords = [[i * step, 0.0, 0.0] for i in range(points)]
    total = (points - 1) * step
    return {
        "id": "T",
        "crs": "EPSG:31370",
        "length_m": total if length_m is None else length_m,
        "vertical": {"status": "not_modelled"},
        "points": coords,
        "stations": [
            {"name": f"S{i}", "chainage_m": c, "depth_m": 0.0}
            for i, c in enumerate(station_chainages)
        ],
    }


def _run(axis):
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "axis.json")
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(axis, handle)
        return V.validate(path)


def _has(messages, fragment):
    return any(fragment in m for m in messages)


# --- rzut ostatniej stacji za koniec osi --------------------------------------

def test_validate_station_exactly_on_the_end_raises_nothing():
    report = _run(_axis([0.0, 400.0, 885.0]))
    assert not report.err, report.err
    assert not _has(report.warn, "za końcem osi"), report.warn


def test_validate_small_overrun_is_a_warning_not_silence():
    """Pół metra jest nieszkodliwe, ale ma być widoczne: TrackAxis.PointAt obcina
    kilometraż do długości osi, więc symulacja i scena rozjeżdżają się po cichu."""
    report = _run(_axis([0.0, 400.0, 885.6]))
    assert not report.err, report.err
    assert _has(report.warn, "za końcem osi")
    assert _has(report.warn, "0.600 m")


def test_validate_overrun_longer_than_the_last_segment_is_an_error():
    """Rzut dalszy niż jeden odcinek łamanej nie jest artefaktem rzutowania,
    tylko stacją, która nie leży na tej osi."""
    report = _run(_axis([0.0, 400.0, 885.0 + STEP_M + 0.1]))
    assert _has(report.err, "wykracza poza oś"), report.err


def test_validate_old_fifty_metre_tolerance_would_have_passed_this():
    """Regresja z liczbą: stacja 40 m za końcem osi przechodziła poprzednią wersję."""
    report = _run(_axis([0.0, 400.0, 925.0]))
    assert _has(report.err, "wykracza poza oś"), report.err


def test_validate_tolerance_follows_the_actual_last_segment():
    """Tolerancja jest wyprowadzona, nie wpisana: przy gęstszej łamanej maleje razem
    z odcinkiem. Ta sama stacja, ten sam kilometraż, inny krok — inny werdykt."""
    # Krok 15 m: przekroczenie 6 m mieści się w ostatnim odcinku. Krok 5 m: nie mieści.
    # Odstęp stacji musi zostać w [250, 2200] m, więc gęstsza oś dostaje dwie stacje.
    coarse = _run(_axis([0.0, 400.0, 885.0 + 6.0]))
    fine = _run(_axis([0.0, (59 * 5.0) + 6.0], step=5.0))
    assert not coarse.err, coarse.err
    assert fine.err == [m for m in fine.err if "wykracza poza oś" in m], fine.err
    assert _has(fine.err, "wykracza poza oś"), fine.err


def test_validate_first_station_before_the_axis_is_caught_symmetrically():
    report = _run(_axis([-STEP_M - 0.1, 400.0, 885.0]))
    assert _has(report.err, "przed osią"), report.err


def test_validate_small_underrun_is_a_warning():
    report = _run(_axis([-0.4, 400.0, 885.0]))
    assert not report.err, report.err
    assert _has(report.warn, "przed początkiem osi")


# --- deklarowana długość kontra łamana ----------------------------------------

def test_validate_declared_length_matching_the_polyline_is_reported_in_millimetres():
    report = _run(_axis([0.0, 400.0, 885.0], length_m=885.004))
    assert not report.err, report.err
    assert _has(report.info, "length_m zgodne z łamaną")


def test_validate_declared_length_from_another_polyline_is_an_error():
    """Rozjazd większy niż zaokrąglenie zapisu znaczy, że length_m pochodzi z innej
    łamanej niż points — a wtedy wszystko, co liczy z tego pliku kilometraż, liczy go
    z czegoś innego niż geometria."""
    report = _run(_axis([0.0, 400.0, 885.0], length_m=900.0))
    assert _has(report.err, "nie zgadza się z łamaną"), report.err


def test_validate_axis_without_declared_length_still_validates():
    axis = _axis([0.0, 400.0, 885.0])
    del axis["length_m"]
    report = _run(axis)
    assert not report.err, report.err
    assert not _has(report.info, "length_m zgodne")


# --- prawdziwe osie -----------------------------------------------------------

def _package_axes():
    """Osie pakietów budowy, po `package`, a NIE po zawartości katalogu.

    `tools/track/make_test_track.py` zapisuje syntetyczne `TEST.json` i `BROKEN.json`
    prosto do `data/track/`, i robi to workflow `blender-smoke` przed uruchomieniem tej
    suity. Test liczący pliki w katalogu widział wtedy siedem osi zamiast sześciu i padał
    — co złapało CI, a lokalnie nie było widać. Kryterium jest więc **deklarowana
    przynależność do pakietu**, zgodna z `build_packages` w `lines.json`: syntetyczna oś
    pola `package` nie ma, a prawdziwa nie może go stracić po cichu.
    """
    with open(os.path.join(ROOT, "data", "network", "lines.json"), encoding="utf-8") as handle:
        declared = {p["id"] for p in json.load(handle)["build_packages"]}
    directory = os.path.join(ROOT, "data", "track")
    found = {}
    for name in sorted(os.listdir(directory)):
        if not name.endswith(".json") or name.endswith(".provenance.json"):
            continue
        path = os.path.join(directory, name)
        with open(path, encoding="utf-8") as handle:
            block = json.load(handle).get("package")
        # `package` w osi jest obiektem skopiowanym z lines.json, nie samym kodem litery.
        package = block.get("id") if isinstance(block, dict) else block
        if package in declared:
            assert package not in found, f"dwie osie dla pakietu {package}"
            found[package] = path
    missing = declared - set(found)
    assert not missing, f"brak osi dla pakietów: {sorted(missing)}"
    return found


def test_validate_every_package_axis_passes_without_errors():
    """Nowa reguła nie może zapalić się na tym, co już leży w repo — inaczej byłaby
    zaostrzeniem poprzeczki pod pozorem naprawy walidatora."""
    for package, path in sorted(_package_axes().items()):
        report = V.validate(path)
        assert not report.err, (package, report.err)


def test_validate_synthetic_axis_in_the_directory_does_not_disturb_the_check():
    """Regresja z nazwą: `blender-smoke` zapisuje TEST.json do data/track/ przed testami."""
    axes = _package_axes()
    assert all(not path.endswith(("TEST.json", "BROKEN.json")) for path in axes.values())


def test_validate_no_package_axis_overruns_its_own_end():
    """Odwrotność poprzedniej wersji tego testu, i to jest cała historia.

    Gdy powstawał, wszystkie sześć pakietów zgłaszało przekroczenie 0,25–0,64 m i test
    pilnował, żeby ta liczba nie zniknęła po cichu. Zniknęła jawnie: kilometraż stacji
    liczy się teraz na osi, która trafia do pliku, a nie na łamanej źródłowej. Test
    pilnuje więc dalej tej samej rzeczy, tylko z drugiej strony — powrót przekroczenia
    znaczyłby, że kilometraż znowu rozjechał się z geometrią.
    """
    over = [
        package for package, path in sorted(_package_axes().items())
        if _has(V.validate(path).warn, "za końcem osi")
    ]
    assert not over, f"pakiety z przekroczeniem: {over}"


def test_validate_last_station_lands_on_the_axis_end():
    """Ostatnia stacja jest końcem osi — oś jest cięta dokładnie w jej rzucie."""
    for package, path in sorted(_package_axes().items()):
        with open(path, encoding="utf-8") as handle:
            axis = json.load(handle)
        last = max(s["chainage_m"] for s in axis["stations"])
        gap = abs(axis["length_m"] - last)
        assert gap <= 0.01, f"{package}: ostatnia stacja {last:.2f} m, oś {axis['length_m']:.2f} m"


def test_validate_axes_keep_the_source_chainage_next_to_the_corrected_one():
    """Kilometraż na łamanej źródłowej nie znika — jest obok, żeby dało się zmierzyć,
    ile kosztuje przepróbkowanie osi, zamiast przyjmować to na wiarę."""
    for package, path in sorted(_package_axes().items()):
        with open(path, encoding="utf-8") as handle:
            stations = json.load(handle)["stations"]
        assert all("source_chainage_m" in s for s in stations), package
        drift = max(s["source_chainage_m"] - s["chainage_m"] for s in stations)
        assert drift >= 0.0, f"{package}: oś przepróbkowana wyszła DŁUŻSZA niż źródłowa"


# --- każdy limit z osobna ------------------------------------------------------
#
# Zmierzone 02.09.2026 audytem mutacyjnym: `test_validator_rejects_broken_track`
# sprawdzał tylko `len(r.err) >= 3`, a zepsuta oś kontrolna daje pięć błędów
# z trzech reguł. Dowolną JEDNĄ regułę można było więc wyłączyć — podnieść
# `max_grade_pct` do 10000 albo zjechać `min_radius_m` do 0,001 — i cała suita
# przechodziła. Poniższe testy stawiają każdą regułę dwustronnie: dokładnie na
# progu przechodzi, tuż za progiem pada, i pada z WŁASNYM komunikatem.


def _arc(radius_m, points=40, chord_m=15.0):
    """Punkty na łuku o zadanym promieniu — radius3 z trójki daje dokładnie ten promień."""
    import math
    theta = 2.0 * math.asin(chord_m / (2.0 * radius_m))
    return [[radius_m * math.sin(i * theta), radius_m * math.cos(i * theta), 0.0]
            for i in range(points)]


def _axis_from(points, stations=(0.0,), speed_limits=None):
    import math
    total = sum(math.dist(points[i][:2], points[i + 1][:2]) for i in range(len(points) - 1))
    axis = {
        "id": "T", "crs": "EPSG:31370", "length_m": total,
        "vertical": {"status": "not_modelled"},
        "points": [list(p) for p in points],
        "stations": [{"name": f"S{i}", "chainage_m": c, "depth_m": 0.0}
                     for i, c in enumerate(stations)],
    }
    if speed_limits is not None:
        axis["speed_limits"] = speed_limits
    return axis


def test_validate_point_gap_limit_holds_at_the_limit_and_breaks_past_it():
    ok = _run(_axis_from([[i * V.LIMITS["max_point_gap_m"], 0.0, 0.0] for i in range(10)]))
    assert ok.ok(), ok.err
    over = V.LIMITS["max_point_gap_m"] * 1.01
    bad = _run(_axis_from([[i * over, 0.0, 0.0] for i in range(10)]))
    assert _has(bad.err, "odstęp punktów"), bad.err


def test_validate_dense_points_are_warned_only_below_the_limit():
    ok = _run(_axis_from([[i * V.LIMITS["min_point_gap_m"], 0.0, 0.0] for i in range(10)],
                         stations=(0.0,)))
    assert not _has(ok.warn, "bardzo gęsto"), ok.warn
    under = V.LIMITS["min_point_gap_m"] * 0.5
    dense = _run(_axis_from([[i * under, 0.0, 0.0] for i in range(10)], stations=(0.0,)))
    assert _has(dense.warn, "bardzo gęsto"), dense.warn
    # Gęsto, ale niezerowo — to zostaje OSTRZEŻENIEM. Gęste punkty w danych STIB są
    # normalne i podniesienie ich do błędu wywróciłoby walidację realnych osi.
    assert not dense.err, dense.err


def test_validate_duplicate_vertex_is_an_error_not_a_dense_warning():
    """Odstęp DOKŁADNIE zerowy to błąd, a nie „bardzo gęsto".

    Którą drogą omijam pułapkę „granicy, która granicy nie dotyka": zero jest tu
    **dokładne**, bo powstaje z odejmowania dwóch identycznych liczb — `math.dist`
    na powtórzonym wierzchołku zwraca 0.0 co do bitu, bez żadnego zaokrąglenia.
    To ta sama droga, z której korzysta
    `test_point_at_chainage_survives_a_duplicate_at_the_very_start`.

    Powód, dla którego to jest błąd: segment o zerowej długości daje zerowy
    mianownik. `capture_plan.point_at_chainage` broni się gałęzią `span <= 0.0`,
    a `build_alignment.slice_polyline` ostrym `<` (#143) — ale to obrony PRZED
    danymi, które ten walidator wpuszczał jako ostrzeżenie.
    """
    step = 15.0
    points = [[i * step, 0.0, 0.0] for i in range(10)]
    points.insert(1, list(points[0]))
    import math
    assert math.dist(points[0][:2], points[1][:2]) == 0.0, "zero musi być dokładne"
    report = _run(_axis_from(points, stations=(0.0,)))
    assert _has(report.err, "zdublowany wierzchołek"), report.err
    assert not _has(report.warn, "bardzo gęsto"), report.warn
    # Kontrola negatywna fikstury: bez wstawionej kopii ta sama oś jest czysta.
    clean = _run(_axis_from([[i * step, 0.0, 0.0] for i in range(10)], stations=(0.0,)))
    assert not clean.err, clean.err


def test_validate_duplicate_threshold_is_open_at_exactly_a_micrometre():
    """Odstęp równy dokładnie progowi to jeszcze DWA punkty, nie duplikat.

    Którą drogą omijam pułapkę: wartość graniczną **czytam z modułu**
    (`V.LIMITS["duplicate_point_gap_m"]`) i stawiam drugi punkt w odległości tej
    liczby od zera, więc `math.dist` zwraca ją **bez zaokrąglenia** — odejmowanie
    od dokładnego zera jest dokładne. Fikstura typu „próg razy 1,01" nie
    odróżniłaby `<` od `<=` w żadną stronę.

    Ta strona nierówności jest ta sama, co w `build_alignment.slice_polyline`,
    i to jest cały powód, dla którego wolno było użyć tamtej liczby.
    """
    import math
    gap = V.LIMITS["duplicate_point_gap_m"]
    step = 15.0
    points = [[0.0, 0.0, 0.0], [gap, 0.0, 0.0]] + [[i * step, 0.0, 0.0] for i in range(1, 10)]
    assert math.dist(points[0][:2], points[1][:2]) == gap, "próg musi być dokładny"
    at_threshold = _run(_axis_from(points, stations=(0.0,)))
    assert not _has(at_threshold.err, "zdublowany wierzchołek"), at_threshold.err
    assert _has(at_threshold.warn, "bardzo gęsto"), at_threshold.warn

    under = points[:]
    under[1] = [gap * 0.5, 0.0, 0.0]
    below = _run(_axis_from(under, stations=(0.0,)))
    assert _has(below.err, "zdublowany wierzchołek"), below.err


def test_validate_duplicate_threshold_matches_the_alignment_merge_threshold():
    """Ta liczba nie jest nowa i nie wolno jej rozjechać z miejscem, z którego pochodzi.

    `build_alignment.slice_polyline` skleja punkty bliższe niż `1e-6` m, więc każda
    oś wyprodukowana tą ścieżką ma odstęp co najmniej mikrometrowy — i dlatego próg
    duplikatu w walidatorze może być dokładnie ten sam. Test sprawdza to
    **zachowaniem**, nie odczytem literału: gdyby którakolwiek strona się przesunęła,
    walidator albo odrzucałby własne dane, albo znów przepuszczał duplikat.
    """
    import math
    sys.path.insert(0, os.path.join(ROOT, "tools", "track"))
    import build_alignment as A  # noqa: E402

    gap = V.LIMITS["duplicate_point_gap_m"]
    merged = A.slice_polyline([(0.0, 0.0), (gap * 0.5, 0.0), (100.0, 0.0)], 0.0, 100.0)
    assert len(merged) == 2, merged          # poniżej progu -> sklejone tam
    kept = A.slice_polyline([(0.0, 0.0), (gap, 0.0), (100.0, 0.0)], 0.0, 100.0)
    assert len(kept) == 3, kept              # dokładnie na progu -> zostaje tam
    assert math.dist(kept[0], kept[1]) == gap


def test_validate_grade_limit_holds_at_the_limit_and_breaks_past_it():
    step = 15.0
    # Tuż pod progiem, nie dokładnie na nim: dz/h liczone w double bywa o ostatni
    # bit większe niż 4,0 i wtedy „na progu" znaczyłoby „ledwo ponad".
    at_limit = step * V.LIMITS["max_grade_pct"] / 100.0 * 0.99
    ok = _run(_axis_from([[i * step, 0.0, i * at_limit] for i in range(10)]))
    assert not _has(ok.err, "pochylenie"), ok.err
    over = step * V.LIMITS["max_grade_pct"] / 100.0 * 1.02
    bad = _run(_axis_from([[i * step, 0.0, i * over] for i in range(10)]))
    assert _has(bad.err, "pochylenie"), bad.err


def test_validate_radius_limit_holds_at_the_limit_and_breaks_past_it():
    ok = _run(_axis_from(_arc(V.LIMITS["min_radius_m"] * 1.02)))
    assert not _has(ok.err, "promień łuku"), ok.err
    bad = _run(_axis_from(_arc(V.LIMITS["min_radius_m"] * 0.98)))
    assert _has(bad.err, "promień łuku"), bad.err


def test_validate_station_spacing_limits_hold_at_the_limits():
    points = [[i * 15.0, 0.0, 0.0] for i in range(400)]
    tight = V.LIMITS["min_station_spacing_m"]
    ok = _run(_axis_from(points, stations=(0.0, tight)))
    assert not _has(ok.err, "za mało"), ok.err
    bad = _run(_axis_from(points, stations=(0.0, tight * 0.9)))
    assert _has(bad.err, "za mało"), bad.err

    wide = V.LIMITS["max_station_spacing_m"]
    quiet = _run(_axis_from(points, stations=(0.0, wide)))
    assert not _has(quiet.warn, "nietypowo dużo"), quiet.warn
    loud = _run(_axis_from(points, stations=(0.0, wide * 1.1)))
    assert _has(loud.warn, "nietypowo dużo"), loud.warn


def test_validate_requires_at_least_three_points():
    two = _run(_axis_from([[0.0, 0.0, 0.0], [15.0, 0.0, 0.0]]))
    assert _has(two.err, "potrzeba co najmniej 3"), two.err
    three = _run(_axis_from([[0.0, 0.0, 0.0], [15.0, 0.0, 0.0], [30.0, 0.0, 0.0]]))
    assert not _has(three.err, "potrzeba co najmniej 3"), three.err


def test_validate_speed_limits_are_actually_checked():
    """Cała ta gałąź była martwa: żaden test nie podawał osi z `speed_limits`."""
    points = [[i * 15.0, 0.0, 0.0] for i in range(20)]
    good = _run(_axis_from(points, speed_limits=[{"from_m": 0.0, "to_m": 100.0, "kmh": 50}]))
    assert not _has(good.err, "ograniczenie"), good.err

    reversed_span = _run(_axis_from(
        points, speed_limits=[{"from_m": 100.0, "to_m": 100.0, "kmh": 50}]))
    assert _has(reversed_span.err, "from_m >= to_m"), reversed_span.err

    for kmh in (4, 81):
        out = _run(_axis_from(points, speed_limits=[{"from_m": 0.0, "to_m": 100.0, "kmh": kmh}]))
        assert _has(out.err, "poza zakresem 5–80"), (kmh, out.err)


def _line_stops(line_id):
    with open(os.path.join(ROOT, "data", "network", "lines.json"), encoding="utf-8") as handle:
        lines = json.load(handle)["lines"]
    return next(line["stops"] for line in lines if line["id"] == line_id)


def _named_axis(names):
    points = [[i * 15.0, 0.0, 0.0] for i in range(400)]
    axis = _axis_from(points, stations=tuple(i * 300.0 for i in range(len(names))))
    for station, name in zip(axis["stations"], names):
        station["name"] = name
    return axis


def test_validate_station_order_against_lines_json_is_executed():
    """`--line` nie było przekazywane przez żaden test, choć CI woła z nim każdą oś.

    Kontrola kolejności stacji względem `lines.json` — jedyne miejsce, które łapie
    oś z zamienionymi stacjami — nie wykonywała się więc ani razu.
    """
    stops = _line_stops("L1")
    assert len(stops) >= 6, stops

    def run(names):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "axis.json")
            with open(path, "w", encoding="utf-8") as handle:
                json.dump(_named_axis(names), handle)
            return V.validate(path, expect_line="L1")

    forward = run(stops[:5])
    assert not _has(forward.err, "kolejność stacji niezgodna"), forward.err
    assert _has(forward.info, "kolejność stacji zgodna"), forward.info

    backward = run(list(reversed(stops[:5])))
    assert not _has(backward.err, "kolejność stacji niezgodna"), backward.err
    assert _has(backward.info, "oś biegnie odwrotnie"), backward.info

    swapped = [stops[0], stops[3], stops[1], stops[4]]
    assert run(swapped).err, "zamiana kolejności stacji ma być błędem"
    assert _has(run(swapped).err, "kolejność stacji niezgodna"), run(swapped).err

    assert _has(run(["Nie ma takiej stacji", stops[1]]).err, "kolejność stacji niezgodna")


def test_validate_limits_are_pinned_to_their_stated_values():
    """Same wartości progów, nie tylko to, że reguła je stosuje.

    Testy dwustronne wyżej budują oś z `V.LIMITS[...]`, więc razem z podniesionym
    progiem podnosi się fikstura i mutacja przechodzi. To jest ten sam kształt
    błędu, co „`assert ... is not None`" — sprawdza mechanizm, nie liczbę.

    Skąd te liczby:
    * 25 m i 90 m — `docs/21-measured-vs-assumed.md`, wiersz o kroku próbkowania:
      krok 15 m został wybrany właśnie dlatego, że wszystkie sześć pakietów mieści
      się w „odstęp ≤ 25 m, R ≥ 90 m";
    * 4 % — kryterium ukończenia T-112 w `docs/TASKS.md` („pochylenia 0–4%");
    * 250 m i 2200 m — obwiednia rzeczywistych odstępów stacji sieci; zmiana
      któregokolwiek przebazowuje wszystkie sześć osi bez ani jednego czerwonego testu;
    * 0,5 m — próg „bardzo gęsto", czyli podejrzenie nadmiarowych punktów. Ten
      wiersz był wcześniej opisany jako „próg wykrywania zdublowanych wierzchołków"
      i to była nieprawda, dlatego jest przepisany, a nie dopisany obok: przy 0,5 m
      duplikat i gęsta polilinia dostawały ten sam status, czyli ostrzeżenie;
    * 1e-6 m — próg duplikatu. Nie jest nową liczbą projektową: dokładnie tyle
      wynosi próg sklejania w `build_alignment.slice_polyline`, więc każda oś
      wyprodukowana tą ścieżką gwarantuje odstęp co najmniej mikrometrowy;
    * 0,01 m — rozdzielczość zapisu `length_m` i `chainage_m` w plikach osi.
    """
    assert V.LIMITS == {
        "max_grade_pct": 4.0,
        "min_radius_m": 90.0,
        "max_point_gap_m": 25.0,
        "duplicate_point_gap_m": 1e-6,
        "min_point_gap_m": 0.5,
        "max_station_spacing_m": 2200.0,
        "min_station_spacing_m": 250.0,
        "length_tolerance_m": 0.01,
    }, V.LIMITS

    with open(os.path.join(ROOT, "docs", "21-measured-vs-assumed.md"), encoding="utf-8") as handle:
        audit = handle.read()
    assert "odstęp ≤ 25 m, R ≥ 90 m" in audit, \
        "dokument audytu przestał wymieniać granice walidatora — rozjazd kodu z opisem"


# --- progi, których nie dotykał żaden test ------------------------------------
#
# Przegląd mutacyjny z 03.09.2026: z 36 mutacji w `validate.py` przeżyły 23.
# Testy wyżej sprawdzały każdą regułę „gdzieś obok progu" — a `>` różni się od `>=`
# WYŁĄCZNIE w punkcie równości. Poniższe testy stają dokładnie na progu.
#
# PUŁAPKA, która kosztowała najwięcej: `(885.0 + 0.01) - 885.0` daje
# 0.009999999999990905, czyli PONIŻEJ progu 0,01. Naiwna fikstura „dokładnie na
# granicy" nie dotyka granicy i nie odróżnia `>` od `>=` w żadną stronę. Różnica
# dwóch double'i jest równa dokładnie 0,01 tylko wtedy, gdy jedna strona jest zerem
# albo gdy obie mieszczą się na tyle nisko, że 0,01 daje się w nich zapisać bez
# zaokrąglenia. Oba te warianty są niżej wykorzystane i każdy jest opisany na miejscu.


def _bare_axis(points, stations, length_m=None):
    """Oś bez ustawiania czegokolwiek za plecami testu.

    `_axis` i `_axis_from` wyżej dopisują `length_m` i `depth_m`; tutaj są testy,
    w których obecność tych pól decyduje o wyniku, więc fikstura ich nie zgaduje.
    """
    axis = {"id": "T", "crs": "EPSG:31370",
            "vertical": {"status": "not_modelled"},
            "points": [list(p) for p in points],
            "stations": [dict(s) for s in stations]}
    if length_m is not None:
        axis["length_m"] = length_m
    return axis


def _station(name, chainage, depth=0.0):
    station = {"name": name, "chainage_m": chainage}
    if depth is not None:
        station["depth_m"] = depth
    return station


# --- radius3: próg zdegenerowanego wyznacznika --------------------------------

def test_validate_radius3_degenerate_threshold_is_strict_at_1e_9():
    """`abs(d)<1e-9` ma być OSTRE, bo `d` dokładnie równe 1e-9 to jeszcze łuk.

    Fikstura trafia w próg dokładnie, a nie „mniej więcej": dla punktów
    (0,0), (1,0), (0,5e-10) wyznacznik to `2*(5e-10)`, a mnożenie double'a przez
    dwa jest w arytmetyce binarnej DOKŁADNE i nie zmienia mantysy. Najbliższy
    double do 5e-10 razy dwa to więc najbliższy double do 1e-9 — te dwie liczby
    są równe co do bitu. To jedyny sposób, żeby stanąć na tym progu; próg 1e-9
    nie jest potęgą dwójki, więc żadna suma ani różnica dwóch „ładnych" liczb
    dziesiętnych w niego nie trafia.

    Bez tego testu przechodziły dwie mutacje naraz: `<` → `<=` oraz podniesienie
    progu o procent. Obie zamieniają realny łuk o promieniu 0,5 m — czyli błąd
    danych, który walidator ma krzyczeć — w `inf`, czyli „prosta, nie ma sprawy".
    """
    d_at_threshold = 2 * (5e-10)
    assert d_at_threshold == 1e-9, "fikstura przestała trafiać w próg"

    on_threshold = V.radius3((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 5e-10, 0.0))
    assert on_threshold == 0.5, on_threshold

    # Kontrola negatywna: punkty naprawdę współliniowe mają dawać `inf`, inaczej
    # test wyżej przechodziłby też dla walidatora, który nigdy nie zwraca `inf`.
    collinear = V.radius3((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (2.0, 0.0, 0.0))
    assert collinear == float("inf"), collinear


# --- length_m: próg 0,01 m ----------------------------------------------------

def test_validate_length_drift_exactly_at_tolerance_is_not_an_error():
    """Rozjazd równy tolerancji to jeszcze zgodność, dopiero większy jest błędem.

    Fikstura jest tu **przepisana, nie dopisana obok**. Poprzednia wersja brała trzy
    identyczne punkty, żeby `total` wyszło dokładnym zerem, i tłumaczyła to tak:
    „0,01 nie jest potęgą dwójki, więc przy `total` rzędu setek metrów najbliższy
    double do `total + 0,01` różni się od `total` o 0,00999999999999 — jedna strona
    musi być zerem". Rozumowanie było poprawne, ale wniosek za wąski, a od 03.09.2026
    łamana o zerowej długości jest **błędem walidacji** (zdublowany wierzchołek), więc
    ta fikstura nie mogła już mierzyć „braku błędów".

    Zerowy `total` nie jest jedynym wejściem, które staje na progu dokładnie. Wystarczy,
    żeby `total` było tego samego rzędu co 0,01, bo wtedy odejmowanie nie wymaga
    zaokrąglenia. Tu `total` to `0,005 + 0,005`, czyli podwojenie double'a — operacja
    w arytmetyce binarnej DOKŁADNA, nie ruszająca mantysy — więc `total` jest bit
    w bit najbliższym double'em do 0,01, a `0,02` jest bit w bit jego podwojeniem.
    Stąd `abs(0,02 - total)` to dokładnie ten sam double, co `LIMITS`, i test
    naprawdę stoi na granicy, a nie tuż nad nią.

    Odstęp 0,005 m jest poniżej `min_point_gap_m`, więc oś dostaje ostrzeżenia
    „bardzo gęsto" — i o to chodzi: gęsto nie jest błędem, duplikat jest.
    """
    tiny = [[0.0, 0.0, 0.0], [0.005, 0.0, 0.0], [0.01, 0.0, 0.0]]
    on_threshold = _run(_bare_axis(tiny, [_station("S0", 0.0)], length_m=0.02))
    assert math.dist(tiny[0][:2], tiny[1][:2]) * 2.0 == 0.01, "fikstura zgubiła dokładność"
    assert abs(0.02 - 0.01) == V.LIMITS["length_tolerance_m"], "fikstura minęła próg"
    assert not on_threshold.err, on_threshold.err
    assert _has(on_threshold.info, "length_m zgodne z łamaną"), on_threshold.info

    # Kontrola negatywna: o jeden krok dalej ma być dokładnie jeden błąd i ma to
    # być TEN błąd. Bez tego test przechodziłby dla walidatora, który nie sprawdza
    # length_m w ogóle.
    past = _run(_bare_axis(tiny, [_station("S0", 0.0)], length_m=0.03))
    assert len(past.err) == 1, past.err
    assert _has(past.err, "nie zgadza się z łamaną"), past.err

    # Kontrola negatywna drugiej strony: dawna fikstura (trzy identyczne punkty) jest
    # dziś błędem i ma nim pozostać. Gdyby wróciła, test wyżej mierzyłby co innego,
    # niż mówi jego nazwa.
    degenerate = _run(_bare_axis([[0.0, 0.0, 0.0]] * 3, [_station("S0", 0.0)],
                                 length_m=0.01))
    assert _has(degenerate.err, "zdublowany wierzchołek"), degenerate.err


# --- pochylenie: próg h < 1e-6 i próg 4 % -------------------------------------

def test_validate_segment_of_exactly_one_micrometre_still_gets_a_grade():
    """`h<1e-6` chroni przed dzieleniem przez zero, a nie przed liczeniem pochylenia.

    Odcinek o długości dokładnie 1e-6 m ma być POLICZONY. Próg da się trafić
    dokładnie, bo `math.dist((1e-6, 0), (0, 0))` to `hypot(1e-6, 0.0)`, a to
    zwraca sam argument bez żadnej arytmetyki — bit w bit ten sam double, co
    stała w kodzie.

    Przeżywały tu dwie mutacje: `<` → `<=` i podniesienie progu o procent. Obie
    każą walidatorowi PRZESKOCZYĆ odcinek o pochyleniu 100 % i nie powiedzieć
    o tym ani słowa.
    """
    assert math.dist((1e-6, 0.0), (0.0, 0.0)) == 1e-6, "fikstura przestała trafiać w próg"

    on_threshold = _run(_bare_axis(
        [[0.0, 0.0, 0.0], [1e-6, 0.0, 1e-6], [2e-6, 0.0, 2e-6]],
        [_station("S0", 0.0)]))
    steep = [m for m in on_threshold.err if "pochylenie" in m]
    assert len(steep) == 2, on_threshold.err
    assert "100.00%" in steep[0], steep[0]

    # Kontrola negatywna: PONIŻEJ progu odcinek ma być pominięty, inaczej test
    # wyżej przechodziłby też dla walidatora bez żadnej ochrony przed dzieleniem
    # przez długość zerową.
    below = _run(_bare_axis(
        [[0.0, 0.0, 0.0], [5e-7, 0.0, 5e-7], [1e-6, 0.0, 1e-6]],
        [_station("S0", 0.0)]))
    assert not [m for m in below.err if "pochylenie" in m], below.err


def test_validate_grade_of_exactly_four_percent_passes_and_names_the_first_segment():
    """Trzy progi naraz, wszystkie na jednej osi o stałym pochyleniu 4,00 %.

    * `g>4.0` ma być ostre — 4 % to wartość dopuszczalna, nie przekroczenie
      (`docs/TASKS.md`, T-112: „pochylenia 0–4%").
    * `g>abs(worst_g)` ma być ostre, żeby przy remisie raportowany był PIERWSZY
      odcinek. Numer punktu idzie do komunikatu, więc remis nie jest tu obojętny:
      przy `>=` ten sam plik dawałby raz „punkt 0", raz „punkt 1".
    * `worst_i>=0` ma obejmować zero, inaczej oś, której najostrzejszy odcinek
      jest PIERWSZY, w ogóle traci wiersz o pochyleniu.

    0,6/15 · 100 daje dokładnie 4.0 w double — sprawdzone asercją niżej, bo bez
    niej fikstura mogłaby po cichu wylądować minimalnie nad progiem i test
    przestałby cokolwiek znaczyć.
    """
    assert abs(0.6) / 15.0 * 100 == V.LIMITS["max_grade_pct"], "fikstura minęła próg"

    on_limit = _run(_bare_axis(
        [[0.0, 0.0, 0.0], [15.0, 0.0, 0.6], [30.0, 0.0, 1.2]],
        [_station("S0", 0.0)]))
    assert not on_limit.err, on_limit.err
    assert _has(on_limit.info, "największe pochylenie: 4.00% (punkt 0)"), on_limit.info

    # Kontrola negatywna: minimalnie stromiej ma dać błędy i tylko takie.
    past = _run(_bare_axis(
        [[0.0, 0.0, 0.0], [15.0, 0.0, 0.61], [30.0, 0.0, 1.22]],
        [_station("S0", 0.0)]))
    assert past.err and all("pochylenie" in m for m in past.err), past.err


# --- promień: próg 90 m i wybór najmniejszego ---------------------------------

def test_validate_radius_of_exactly_ninety_metres_passes_and_names_the_first_point():
    """Trzy progi naraz na okręgu o promieniu dokładnie 90 m.

    Cztery punkty (±90, 0) i (0, ±90) dają `radius3` równe 90.0 co do bitu:
    wyznacznik i oba liczniki wychodzą na całkowitych wielokrotnościach 8100,
    więc dzielenie jest dokładne, a środek wypada w (0, 0). Łuku o promieniu
    90 m NIE da się zbudować z odstępów ≤ 25 m i jednocześnie trafić w próg
    dokładnie — okrąg o promieniu 90 nie ma punktów wymiernych bliżej niż 127 m
    od siebie (jedyna trójka pitagorejska o przeciwprostokątnej 90 to 54–72–90).
    Dlatego ta oś ŁAMIE limit odstępu punktów i test mówi to wprost: jedyne
    dopuszczone błędy to błędy odstępu.

    Przeżywały tu trzy mutacje: `rad<90` → `<=`, `rad<worst_r` → `<=` oraz
    `worst_r!=inf` → `==`. Ostatnia kasuje wiersz „najmniejszy promień"
    z KAŻDEGO raportu — warunek jest spełniony zawsze, gdy `worst_ri>=0`.
    """
    circle = [[-90.0, 0.0, 0.0], [0.0, 90.0, 0.0], [90.0, 0.0, 0.0], [0.0, -90.0, 0.0]]
    assert V.radius3(circle[0], circle[1], circle[2]) == 90.0, "fikstura minęła próg"

    on_limit = _run(_bare_axis(circle, [_station("S0", 0.0)]))
    assert all("odstęp punktów" in m for m in on_limit.err), on_limit.err
    assert not _has(on_limit.err, "promień łuku"), on_limit.err
    assert _has(on_limit.info, "najmniejszy promień: 90 m (punkt 1)"), on_limit.info

    # Kontrola negatywna: ten sam kształt ciut ciaśniej ma dać błąd promienia.
    tight = [[-89.0, 0.0, 0.0], [0.0, 89.0, 0.0], [89.0, 0.0, 0.0], [0.0, -89.0, 0.0]]
    past = _run(_bare_axis(tight, [_station("S0", 0.0)]))
    assert _has(past.err, "promień łuku"), past.err


# --- rzut stacji: dwa progi z każdej strony osi -------------------------------

def test_validate_overrun_equal_to_the_last_segment_is_a_warning_not_an_error():
    """Granica między „artefakt rzutowania" a „stacja nie leży na tej osi".

    Przekroczenie równe ostatniemu odcinkowi jest jeszcze artefaktem. Różnica
    900,0 − 885,0 jest w double dokładna (obie liczby są całkowite), więc ta
    fikstura naprawdę staje na progu, w odróżnieniu od prób z ułamkami.
    """
    on_limit = _run(_axis([0.0, 400.0, 900.0]))
    assert 900.0 - 885.0 == STEP_M, "fikstura minęła próg"
    assert not on_limit.err, on_limit.err
    assert _has(on_limit.warn, "za końcem osi"), on_limit.warn

    # Kontrola negatywna: jeden krok dalej i to już jest błąd, i tylko ten błąd.
    past = _run(_axis([0.0, 400.0, 900.1]))
    assert len(past.err) == 1, past.err
    assert _has(past.err, "wykracza poza oś"), past.err


def test_validate_overrun_exactly_at_tolerance_stays_silent():
    """Rzut przesunięty dokładnie o rozdzielczość zapisu nie jest przekroczeniem.

    Ta fikstura wygląda absurdalnie — oś ma 14 milimetrów — i to jest jej sens.
    `over = ch[-1] - total` może być równe DOKŁADNIE 0,01 tylko wtedy, gdy oba
    double'e leżą na tyle nisko, że 0,01 mieści się w ich najmłodszych bitach:
    mantysa 0,01 jest nieparzysta na poziomie 2⁻⁵⁹, więc przy `total` rzędu
    metrów różnica zawsze wypada obok progu (dla 885 m: 0,00999999999999).
    Jednocześnie ostatni odcinek musi być DŁUŻSZY niż 0,01, inaczej zadziała
    wcześniejsza reguła i do progu 0,01 sprawdzanie nigdy nie dojdzie. Oba
    warunki spełnia dopiero łamana 2 mm + 12 mm; wartości sprawdzone asercją.
    """
    points = [[0.0, 0.0, 0.0], [0.002, 0.0, 0.0], [0.014, 0.0, 0.0]]
    total = 0.002 + 0.012
    assert (total + 0.01) - total == V.LIMITS["length_tolerance_m"], "fikstura minęła próg"

    on_threshold = _run(_bare_axis(points, [_station("S0", total + 0.01)]))
    assert not on_threshold.err, on_threshold.err
    assert not _has(on_threshold.warn, "za końcem osi"), on_threshold.warn

    # Kontrola negatywna: o milimetr dalej i ostrzeżenie ma się pojawić, wciąż
    # bez błędu — bo mieści się w ostatnim odcinku (12 mm).
    past = _run(_bare_axis(points, [_station("S0", total + 0.011)]))
    assert not past.err, past.err
    assert _has(past.warn, "za końcem osi"), past.warn


def test_validate_underrun_equal_to_the_first_segment_is_a_warning_not_an_error():
    """Symetria progu z drugiej strony osi: −15,0 wobec pierwszego odcinka 15,0."""
    on_limit = _run(_axis([-STEP_M, 400.0, 885.0]))
    assert not on_limit.err, on_limit.err
    assert _has(on_limit.warn, "przed początkiem osi"), on_limit.warn

    past = _run(_axis([-STEP_M - 0.1, 400.0, 885.0]))
    assert len(past.err) == 1, past.err
    assert _has(past.err, "przed osią"), past.err


def test_validate_underrun_exactly_at_tolerance_stays_silent():
    """Tu próg da się trafić bez sztuczek: `ch[0]` jest porównywane z `-0,01`
    wprost, bez odejmowania, więc wystarczy wpisać −0,01 do pliku."""
    on_threshold = _run(_axis([-0.01, 400.0, 885.0]))
    assert not on_threshold.err, on_threshold.err
    assert not _has(on_threshold.warn, "przed początkiem osi"), on_threshold.warn

    past = _run(_axis([-0.02, 400.0, 885.0]))
    assert not past.err, past.err
    assert _has(past.warn, "przed początkiem osi"), past.warn


# --- lista brakujących głębokości ---------------------------------------------

def test_validate_missing_depth_list_is_elided_only_past_five_names():
    """Wielokropek w komunikacie ma znaczyć „lista jest ucięta", a nie nic.

    Komunikat pokazuje `missing[:5]`, więc przy dokładnie pięciu brakach nic nie
    jest ucięte i wielokropka być nie może; przy sześciu — musi. Bez obu stron
    przechodziły dwie mutacje: `>5` → `>=5` (wielokropek przy pełnej liście)
    i `>5` → `>6` (ucięta lista bez znaku, że jest ucięta).
    """
    points = [[i * 15.0, 0.0, 0.0] for i in range(400)]

    def run(count):
        stations = [_station(f"S{i}", i * 300.0, depth=None) for i in range(count)]
        return _run(_bare_axis(points, stations))

    five = [m for m in run(5).warn if "brak głębokości" in m]
    assert len(five) == 1, five
    assert "…" not in five[0], five[0]
    assert five[0].endswith("S4"), five[0]

    six = [m for m in run(6).warn if "brak głębokości" in m]
    assert len(six) == 1, six
    assert six[0].endswith("…"), six[0]
    assert "S5" not in six[0], six[0]

    # Kontrola negatywna: komplet głębokości nie może dawać tego ostrzeżenia
    # w ogóle — inaczej obie asercje wyżej sprawdzałyby tylko formatowanie.
    full = [_station(f"S{i}", i * 300.0, depth=-10.0) for i in range(6)]
    assert not [m for m in _run(_bare_axis(points, full)).warn if "brak głębokości" in m]


# --- zakres ograniczeń prędkości ----------------------------------------------

def test_validate_speed_limit_range_is_inclusive_at_both_ends():
    """5 i 80 km/h to wartości DOPUSZCZALNE, nie granice do odrzucenia.

    Istniejący test sprawdzał tylko 4 i 81, czyli obie strony NA ZEWNĄTRZ.
    Przeżywały przez to trzy mutacje: oba `<=` ścięte do `<` i dolna granica
    podniesiona do 6 — czyli walidator, który odrzuca prawidłowy manewrowy
    5 km/h albo prawidłowe 80 km/h, i żaden test tego nie zauważa.
    """
    points = [[i * 15.0, 0.0, 0.0] for i in range(20)]

    def run(kmh):
        axis = _bare_axis(points, [_station("S0", 0.0)])
        axis["speed_limits"] = [{"from_m": 0.0, "to_m": 100.0, "kmh": kmh}]
        return _run(axis)

    for kmh in (5, 80):
        out = run(kmh)
        assert not out.err, (kmh, out.err)

    for kmh in (4, 81):
        out = run(kmh)
        assert len(out.err) == 1, (kmh, out.err)
        assert _has(out.err, "poza zakresem 5–80"), (kmh, out.err)
