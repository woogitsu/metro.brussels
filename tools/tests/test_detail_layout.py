#!/usr/bin/env python3
"""Testy rozstawiania detali wzdłuż osi.

Ten moduł liczy wyłącznie kilometraże, więc testy sprawdzają **reguły miejsca**,
a nie wygląd. Wygląd nie jest tu testowany, bo go tu nie ma.
"""
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "track"))
sys.path.insert(0, os.path.join(ROOT, "tools", "physics"))

import braking as B  # noqa: E402
import detail_layout as D  # noqa: E402

CFG = B.params()


def _axis(length_m, stations):
    return {"id": "T", "length_m": length_m,
            "stations": [{"name": n, "chainage_m": c, "stop_id": f"P{i}"}
                         for i, (n, c) in enumerate(stations)]}


def _kinds(marks, kind):
    return [m for m in marks if m["kind"] == kind]


# --- hektometry ---------------------------------------------------------------

def test_layout_hectometres_start_at_zero_and_stop_at_the_axis_end():
    assert D.hectometre_marks(250.0) == [0.0, 100.0, 200.0]
    assert D.hectometre_marks(300.0) == [0.0, 100.0, 200.0, 300.0]


def test_layout_hectometre_exactly_on_the_end_is_kept():
    """Koniec osi to ostatnia stacja, więc taki hektometr i tak zniknie przy scaleniu —
    ale wypadnięcie go już tutaj ukryłoby, że oś kończy się okrągłą liczbą."""
    assert D.hectometre_marks(600.0)[-1] == 600.0


def test_layout_hectometre_step_must_be_positive():
    try:
        D.hectometre_marks(500.0, 0.0)
    except ValueError:
        return
    raise AssertionError("krok zerowy powinien zostać odrzucony")


def test_layout_denser_step_gives_proportionally_more_marks():
    assert len(D.hectometre_marks(1000.0, 50.0)) == 21
    assert len(D.hectometre_marks(1000.0, 100.0)) == 11


def test_layout_hectometre_limit_is_derived_from_the_two_numbers_it_claims():
    """`MAX_MARKS` ma być ilorazem, nie okrągłą liczbą wpisaną z ręki.

    Bez tego testu można podnieść `MAX_MARKS` do dowolnej wartości i nadal mieć
    komunikat błędu, który powołuje się na 40 km i 1 m — czyli opis rozjechany
    z liczbą. Granica jest tu **czytana z modułu** w całości.
    """
    assert D.MAX_MARKS == int(D.MAX_AXIS_LENGTH_M / D.MIN_SENSIBLE_STEP_M)
    assert D.MAX_AXIS_LENGTH_M == 40000.0
    assert D.MIN_SENSIBLE_STEP_M == 1.0
    # Realna oś pakietu przy konwencyjnym kroku ma być daleko pod granicą, inaczej
    # ogranicznik bramkowałby poprawne wejście, a nie awarię.
    assert len(D.hectometre_marks(6686.35)) < D.MAX_MARKS / 100.0


def test_layout_hectometre_grid_stops_at_max_marks_and_says_so_with_numbers():
    """Ogranicznik pętli stoi DOKŁADNIE na progu, przy dodatnim kroku.

    Którą drogą omijam pułapkę „granicy, która granicy nie dotyka": wartość graniczną
    **czytam z modułu** (`D.MAX_MARKS`, `D.MIN_SENSIBLE_STEP_M`) i dodatkowo krok
    1,0 m jest potęgą dwójki, więc `index * step_m` dla całkowitego `index` jest
    w double **dokładne**. Długość `(MAX_MARKS - 1) * 1,0` naprawdę stoi na ostatnim
    dopuszczonym znaczniku, a `MAX_MARKS * 1,0` naprawdę jest pierwszym za nim.
    Fikstura typu `granica + 0.01` nie odróżniłaby `>=` od `>` w żadną stronę.

    Krok jest tu dodatni, więc to nie strażnik `step_m` odrzuca to wejście —
    odrzuca je ogranicznik. To jedyne wejście, na którym ta liczba o czymkolwiek
    decyduje.
    """
    step = D.MIN_SENSIBLE_STEP_M
    at_limit = D.hectometre_marks((D.MAX_MARKS - 1) * step, step)
    assert len(at_limit) == D.MAX_MARKS, len(at_limit)
    assert at_limit[-1] == (D.MAX_MARKS - 1) * step
    try:
        D.hectometre_marks(D.MAX_MARKS * step, step)
    except ValueError as exc:
        message = str(exc)
        assert str(D.MAX_MARKS) in message, message
        assert "40000" in message and "1 m" in message, message
        return
    raise AssertionError("oś dłuższa niż MAX_MARKS kroków powinna dać ValueError")


def test_layout_hectometre_grid_terminates_with_the_step_guard_removed():
    """Dowód, że ogranicznik jest NIEZALEŻNY od strażnika, a nie tylko stoi obok.

    Strażnik `step_m <= 0.0` był jedyną rzeczą, która trzymała tę pętlę: przy kroku
    zerowym `index * step_m <= length_m` jest prawdziwe zawsze. Osłabienie go nie
    dawało złego wyniku, tylko proces, który się nie kończy — i dlatego przemiatanie
    mutacyjne nie mogło tej mutacji zaraportować jako zabitej, a jedynie jako
    nierozstrzygniętą (`timeout 20` -> kod 124).

    Braku zatrzymania nie da się zaobserwować w tym samym procesie, więc test
    wycina strażnika ze **źródła** modułu, uruchamia okaleczoną wersję w osobnym
    procesie i wymaga, żeby ten proces się ZAKOŃCZYŁ, i to przez `ValueError`.
    Kontrola negatywna: bez `MAX_MARKS` podproces wisi i test pada na `timeout`.
    """
    import subprocess
    import tempfile

    module = os.path.join(ROOT, "tools", "track", "detail_layout.py")
    with open(module, encoding="utf-8") as handle:
        source = handle.read()
    guard = ('    if step_m <= 0.0:\n'
             '        raise ValueError("krok hektometrów musi być dodatni")\n')
    assert guard in source, "strażnik zmienił kształt — test przestał go wycinać"
    weakened = source.replace(guard, "")
    assert weakened != source

    with tempfile.TemporaryDirectory() as tmp:
        mutant = os.path.join(tmp, "detail_layout_bez_straznika.py")
        with open(mutant, "w", encoding="utf-8") as handle:
            handle.write(weakened)
        driver = os.path.join(tmp, "driver.py")
        with open(driver, "w", encoding="utf-8") as handle:
            handle.write(
                "import sys\n"
                f"sys.path.insert(0, {os.path.join(ROOT, 'tools', 'physics')!r})\n"
                f"sys.path.insert(0, {os.path.join(ROOT, 'tools', 'data')!r})\n"
                f"sys.path.insert(0, {tmp!r})\n"
                "import detail_layout_bez_straznika as M\n"
                "assert 'if step_m <= 0.0' not in open(M.__file__, encoding='utf-8').read()\n"
                "try:\n"
                "    M.hectometre_marks(500.0, 0.0)\n"
                "except ValueError:\n"
                "    print('OGRANICZNIK')\n"
                "    raise SystemExit(0)\n"
                "raise SystemExit('brak ValueError: petla zwrocila wynik bez ogranicznika')\n")
        done = subprocess.run([sys.executable, driver], capture_output=True,
                              text=True, timeout=20)
    assert done.returncode == 0, (done.returncode, done.stdout, done.stderr)
    assert "OGRANICZNIK" in done.stdout, done.stdout


# --- pierwszeństwo w tym samym miejscu ----------------------------------------

def test_layout_station_wins_over_a_hectometre_at_the_same_place():
    """Stacja na okrągłym kilometrażu nie może dać dwóch słupków w jednym punkcie."""
    marks, _ = D.layout(_axis(600.0, [("A", 0.0), ("B", 300.0), ("C", 600.0)]))
    at_300 = [m for m in marks if abs(m["chainage_m"] - 300.0) < 0.5]
    assert len(at_300) == 1
    assert at_300[0]["kind"] == "station"


def test_layout_brake_point_wins_over_a_hectometre_but_loses_to_a_station():
    order = {"station": 0, "brake": 1, "hectometre": 2}
    marks, _ = D.layout(_axis(2000.0, [("A", 0.0), ("B", 1000.0), ("C", 2000.0)]),
                        speed_mps=20.0, decel_mps2=CFG["service"], jerk_mps3=CFG["jerk"])
    for a, b in zip(marks, marks[1:]):
        assert a["chainage_m"] < b["chainage_m"], (a, b)
    assert all(order[m["kind"]] is not None for m in marks)


def test_layout_marks_are_sorted_and_never_duplicated():
    marks, _ = D.layout(_axis(3000.0, [("A", 0.0), ("B", 1400.0), ("C", 3000.0)]),
                        speed_mps=20.0, decel_mps2=CFG["service"], jerk_mps3=CFG["jerk"])
    chainages = [m["chainage_m"] for m in marks]
    assert chainages == sorted(chainages)
    for a, b in zip(chainages, chainages[1:]):
        assert b - a > D.SAME_PLACE_M


# --- punkty hamowania ---------------------------------------------------------

def test_layout_braking_distance_matches_the_t311_closed_form():
    speed = 72.0 / 3.6
    got = D.braking_distance_m(speed, CFG["service"], CFG["jerk"])
    want = B.braking_distance_m(speed, 0.0, CFG["service"], CFG["jerk"])
    assert abs(got - want) < 1e-12


def test_layout_braking_below_the_plateau_falls_back_to_the_jerk_only_distance():
    """Przy małej prędkości cel wypada w trakcie narastania hamulca, więc zadane `b`
    nigdy nie zdąży zadziałać — droga nie zależy już od niego."""
    slow = 0.5
    assert CFG["service"] >= B.plateau_ceiling_mps2(slow, 0.0, CFG["jerk"])
    got = D.braking_distance_m(slow, CFG["service"], CFG["jerk"])
    assert abs(got - B.ramp_only_distance_m(slow, 0.0, CFG["jerk"])) < 1e-12


def test_layout_standstill_needs_no_braking_distance():
    assert D.braking_distance_m(0.0, CFG["service"], CFG["jerk"]) == 0.0


def test_layout_brake_point_sits_exactly_one_braking_distance_before_the_station():
    stations = [{"name": "A", "chainage_m": 0.0}, {"name": "B", "chainage_m": 1000.0}]
    marks, _ = D.braking_marks(stations, 20.0, CFG["service"], CFG["jerk"])
    assert len(marks) == 1
    assert abs(marks[0]["chainage_m"] + marks[0]["braking_distance_m"] - 1000.0) < 0.01


def test_layout_first_station_gets_no_brake_point():
    stations = [{"name": "A", "chainage_m": 0.0}, {"name": "B", "chainage_m": 900.0}]
    marks, _ = D.braking_marks(stations, 20.0, CFG["service"], CFG["jerk"])
    assert [m["for_station"] for m in marks] == ["B"]


def test_layout_brake_point_before_the_previous_station_is_skipped_with_a_reason():
    """Odcinek za krótki na tę prędkość. Przesunięcie punktu w prawo udawałoby, że
    da się ją osiągnąć — pominięcie z powodem mówi prawdę."""
    stations = [{"name": "A", "chainage_m": 0.0}, {"name": "B", "chainage_m": 150.0}]
    marks, skipped = D.braking_marks(stations, 20.0, CFG["service"], CFG["jerk"])
    assert marks == []
    assert len(skipped) == 1
    assert skipped[0]["station"] == "B"
    assert skipped[0]["would_be_at_m"] < 0.0
    assert "za krótki" in skipped[0]["reason"]


def test_layout_higher_speed_pushes_the_brake_point_further_back():
    stations = [{"name": "A", "chainage_m": 0.0}, {"name": "B", "chainage_m": 2000.0}]
    slow, _ = D.braking_marks(stations, 14.0, CFG["service"], CFG["jerk"])
    fast, _ = D.braking_marks(stations, 22.0, CFG["service"], CFG["jerk"])
    assert fast[0]["chainage_m"] < slow[0]["chainage_m"]


def test_layout_without_a_speed_there_are_no_brake_points_at_all():
    """Prędkość dopuszczalna na torze nie ma źródła (R-006), więc brak podanej
    prędkości musi znaczyć brak punktów, a nie cichy domyślny wybór."""
    marks, skipped = D.layout(_axis(2000.0, [("A", 0.0), ("B", 2000.0)]))
    assert _kinds(marks, "brake") == []
    assert skipped == []


# --- raport -------------------------------------------------------------------

def test_layout_survey_counts_every_kind_and_carries_its_assumptions():
    axis = _axis(2000.0, [("A", 0.0), ("B", 1000.0), ("C", 2000.0)])
    report = D.survey(axis, "T", speed_kmh=72.0, cfg=CFG)
    assert report["counts"]["station"] == 3
    assert report["brake_from_kmh"] == 72.0
    assert report["service_brake_mps2"] == CFG["service"]
    assert report["jerk_mps3"] == CFG["jerk"]
    assert report["braking_distance_m"] > 0.0


def test_layout_survey_without_speed_reports_none_not_zero():
    """Zero znaczyłoby „hamowanie na zerowej drodze", a nie „nie liczyliśmy"."""
    report = D.survey(_axis(500.0, [("A", 0.0), ("B", 500.0)]), "T", cfg=CFG)
    assert report["brake_from_kmh"] is None
    assert report["braking_distance_m"] is None
    assert report["service_brake_mps2"] is None


def test_layout_station_marks_carry_the_stop_id_for_joining_with_the_timetable():
    report = D.survey(_axis(900.0, [("A", 0.0), ("B", 900.0)]), "T", cfg=CFG)
    stations = _kinds(report["marks"], "station")
    assert [s["stop_id"] for s in stations] == ["P0", "P1"]


# --- prawdziwe osie -----------------------------------------------------------

def test_layout_every_package_axis_places_a_mark_on_every_station():
    import json, glob
    for path in sorted(glob.glob(os.path.join(ROOT, "data", "track", "*.json"))):
        if path.endswith(".provenance.json"):
            continue
        with open(path, encoding="utf-8") as handle:
            axis = json.load(handle)
        if not isinstance(axis.get("package"), dict):
            continue
        report = D.survey(axis, axis["id"], speed_kmh=72.0, cfg=CFG)
        assert report["counts"]["station"] == len(axis["stations"]), axis["id"]
        last = max(m["chainage_m"] for m in report["marks"])
        assert last <= axis["length_m"] + D.SAME_PLACE_M, axis["id"]


# --- luz słupka przy torze ----------------------------------------------------

sys.path.insert(0, os.path.join(ROOT, "tools", "blender"))
import placement as PL  # noqa: E402
from profiles import profile_points, vehicle_gauge  # noqa: E402

BOX = profile_points("box_double")
GAUGE = vehicle_gauge()


def test_marker_clearance_is_positive_for_the_committed_default():
    """Odsunięcie 2,10 m ze skryptu ma mieścić się między skrajnią a ścianą — i to jest
    jedyny powód, dla którego wolno je nazwać założeniem, a nie zgadywaniem."""
    for height in (0.60, 1.00, 1.60):
        to_gauge, to_wall = PL.marker_clearances(BOX, GAUGE, 2.10, 0.20, -0.10, height)
        assert to_gauge > 0.0, (height, to_gauge)
        assert to_wall > 0.0, (height, to_wall)


def test_marker_too_close_to_the_axis_fouls_the_vehicle_gauge():
    to_gauge, _ = PL.marker_clearances(BOX, GAUGE, 1.60, 0.20, -0.10, 1.60)
    assert to_gauge < 0.0


def test_marker_too_far_pierces_the_tunnel_wall():
    _to_gauge, to_wall = PL.marker_clearances(BOX, GAUGE, 4.70, 0.20, -0.10, 1.60)
    assert to_wall < 0.0


def test_marker_clearance_uses_the_near_edge_not_the_centre():
    """Liczenie od środka słupka zawyżałoby luz o pół szerokości i przepuściłoby
    bryłę, która realnie wchodzi w skrajnię."""
    narrow, _ = PL.marker_clearances(BOX, GAUGE, 2.10, 0.02, -0.10, 1.60)
    wide, _ = PL.marker_clearances(BOX, GAUGE, 2.10, 0.60, -0.10, 1.60)
    assert wide < narrow
    assert abs((narrow - wide) - (0.60 - 0.02) / 2.0) < 1e-9


def test_marker_gauge_narrows_with_height_so_a_low_post_may_stand_closer():
    """Skrajnia ma ścięte naroża, więc pół-rozstawienie do 1,0 m nie może być mniejsze
    niż do 3,9 m — i przy M7 jest wręcz większe."""
    low = PL.gauge_half_width_m(GAUGE, 1.00)
    high = PL.gauge_half_width_m(GAUGE, 3.90)
    assert low >= high


def test_marker_gauge_below_the_rail_head_has_no_points_and_says_so():
    try:
        PL.gauge_half_width_m(GAUGE, -5.0)
    except ValueError:
        return
    raise AssertionError("skrajnia bez punktów poniżej progu powinna dać ValueError")


# --- narzędzie wypuszczone na prawdziwe osie (T-011 na pakietach B–F) -----------

#: DLACZEGO TE PIĘĆ TESTÓW STOI OSOBNO OD RESZTY MODUŁU.
#:
#: Osiem testów wyżej bada REGUŁY na figurach liczonych w locie: co się dzieje, gdy
#: hektometr wypada dokładnie na końcu osi, gdy stacja i hektometr trafiają w to samo
#: miejsce, gdy punkt hamowania wypada przed poprzednią stacją. Żaden z nich nie
#: uruchamia narzędzia na prawdziwej osi — a między „reguła jest poprawna" a „na
#: sześciu osiach sieci wychodzi to, co raport twierdzi" jest cała pozycja 6.B2.
#:
#: Liczby są **odczytywane z raportu**, nie wpisane tutaj. Gdyby stały w teście,
#: byłyby drugą kopią tej samej wiedzy i rozjechałyby się dokładnie tak samo jak
#: pierwsza — to zdanie jest przepisane z `test_readme_claims.py`, bo dotyczy tej
#: samej pułapki.

import json  # noqa: E402
import re  # noqa: E402

DETAILS_REPORT = os.path.join(ROOT, "reports", "T-011-details-BF.md")
TRACK_DIR = os.path.join(ROOT, "data", "track")

#: Prędkość, przy której powstała tabela §1 raportu. NIE jest prędkością dopuszczalną
#: na torze — ta nie ma źródła (R-006) — tylko zadeklarowanym parametrem przebiegu,
#: dokładnie tym samym, który stoi w wierszu polecenia w §1.
REPORT_SPEED_KMH = 72.0

#: Wiersz tabeli §1: `| A | `L1_A` | 6686,4 | 66 | 12 | 11 | **89** |`
REPORT_ROW = re.compile(
    r"^\|\s*([A-F])\s*\|\s*`([A-Z0-9_]+)`\s*\|\s*([\d\s,]+)\s*\|\s*(\d+)\s*\|"
    r"\s*(\d+)\s*\|\s*(\d+)\s*\|\s*\*\*(\d+)\*\*\s*\|")


def _report_rows():
    """`{oś: (pakiet, długość, hektometry, stacje, hamowania, razem)}` z tabeli §1."""
    rows = {}
    with open(DETAILS_REPORT, encoding="utf-8") as handle:
        for line in handle:
            found = REPORT_ROW.match(line.strip())
            if found:
                package, axis, length, hecto, stations, brakes, total = found.groups()
                rows[axis] = (package, float(length.replace(" ", "").replace(",", ".")),
                              int(hecto), int(stations), int(brakes), int(total))
    return rows


def _measure(axis_id, speed_kmh=REPORT_SPEED_KMH):
    with open(os.path.join(TRACK_DIR, f"{axis_id}.json"), encoding="utf-8") as handle:
        axis = json.load(handle)
    return D.survey(axis, axis_id, speed_kmh=speed_kmh, cfg=CFG)


def test_detail_the_report_table_is_read_and_covers_all_six_packages():
    """Kontrola detektora: bez niej cztery testy niżej byłyby zielone na pustej tabeli.

    Wyrażenie czyta wiersze tabeli §1. Gdyby przestało pasować — inny separator,
    inne pogrubienie, przestawiona kolumna — pętla po zerowej liczbie wierszy
    przechodziłaby każdy assert w tym pliku.
    """
    rows = _report_rows()
    assert sorted(package for package, *_rest in rows.values()) == list("ABCDEF"), rows
    assert len(rows) == 6, rows
    # Wiersz „razem" NIE ma litery pakietu, więc nie może wejść na listę osi.
    assert "razem" not in rows


def test_detail_every_package_axis_matches_the_report_count_by_count():
    """Sześć osi, cztery liczby na oś, zero tolerancji.

    Kryterium pozycji 6.B2 podaje wiersz pakietu A wprost: **89 miejsc = 66 hektometrów
    + 12 stacji + 11 punktów hamowania**. Ten test sprawdza go razem z pięcioma
    pozostałymi, tą samą drogą.
    """
    mismatches = []
    for axis_id, (package, length, hecto, stations, brakes, total) in _report_rows().items():
        survey = _measure(axis_id)
        counts = survey["counts"]
        measured = (round(survey["axis_length_m"], 1),
                    counts.get("hectometre", 0), counts.get("station", 0),
                    counts.get("brake", 0), sum(counts.values()))
        expected = (round(length, 1), hecto, stations, brakes, total)
        if measured != expected:
            mismatches.append(f"{package} ({axis_id}): raport {expected}, pomiar {measured}")
    assert not mismatches, mismatches


def test_detail_hectometres_are_the_floor_of_the_axis_length():
    """Hektometrów jest `floor(długość / krok)`, bo kilometraż 0 jest stacją.

    Ta zależność wiąże tabelę z geometrią: gdyby narzędzie zaczęło liczyć znacznik
    na zerze albo gubić ostatni, liczby w tabeli nadal by się zgadzały same ze sobą,
    a przestałyby zgadzać z długością osi.
    """
    wrong = []
    for axis_id in _report_rows():
        survey = _measure(axis_id)
        expected = int(survey["axis_length_m"] // survey["hectometre_step_m"])
        found = survey["counts"].get("hectometre", 0)
        if found != expected:
            wrong.append(f"{axis_id}: {found} hektometrów, oczekiwano {expected}")
    assert not wrong, wrong


def test_detail_every_station_on_every_package_axis_carries_a_stop_id():
    """Stacja bez `stop_id` jest znacznikiem, którego nie da się powiązać z rozkładem.

    61 stacji na sześciu osiach — liczba większa od 59 stacji sieci, bo osie zachodzą
    na siebie na krańcówkach i ta sama stacja bywa policzona dwa razy. Raport §3
    mówi o tym wprost; tu liczy się tylko to, że **żadna** nie jest bez identyfikatora.
    """
    missing = []
    seen = 0
    for axis_id in _report_rows():
        for mark in _measure(axis_id)["marks"]:
            if mark["kind"] != "station":
                continue
            seen += 1
            if not mark.get("stop_id"):
                missing.append(f"{axis_id}: {mark.get('label')}")
    assert not missing, missing
    assert seen >= 55, f"policzono tylko {seen} stacji na sześciu osiach — skan przestał czytać"


def test_detail_without_a_declared_speed_no_axis_gets_a_single_brake_point():
    """Bez `--brake-from-kmh` znika dokładnie tyle miejsc, ile jest punktów hamowania.

    Prędkość dopuszczalna na torze **nie ma źródła** (R-006), więc 72 km/h jest
    parametrem scenariusza, nie danymi. Bez niego `braking_distance_m` ma być `None`,
    a nie `0.0`: zero znaczyłoby, że pociąg hamuje na długości zerowej, a `None` —
    że nikt nie zadeklarował, z jakiej prędkości.
    """
    for axis_id, (_package, _length, _hecto, _stations, brakes, total) in _report_rows().items():
        bez = _measure(axis_id, speed_kmh=None)
        assert bez["counts"].get("brake", 0) == 0, axis_id
        assert bez["braking_distance_m"] is None, axis_id
        assert sum(bez["counts"].values()) == total - brakes, axis_id
