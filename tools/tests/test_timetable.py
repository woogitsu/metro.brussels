#!/usr/bin/env python3
"""Testy odczytu rozkładu z GTFS. Bez sieci — archiwum budowane w locie."""
import io
import json
import os
import sys
import tempfile
import zipfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "track"))

import timetable as TT  # noqa: E402


def _zip(members):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, text in members.items():
            archive.writestr(name, text)
    buffer.seek(0)
    return zipfile.ZipFile(buffer)


def _feed(**overrides):
    members = {
        "routes.txt": ("route_id,route_short_name,route_long_name,route_type\n"
                       "R1,1,A - B,1\n"
                       "RT,T,tramwaj,0\n"),
        "calendar.txt": ("service_id,monday,tuesday,wednesday,thursday,friday,saturday,sunday,"
                         "start_date,end_date\n"
                         "S1,1,1,1,1,1,0,0,20260101,20261231\n"
                         "S2,0,0,0,0,0,1,1,20260101,20261231\n"),
        "calendar_dates.txt": "service_id,date,exception_type\n",
        "trips.txt": ("route_id,service_id,trip_id,direction_id,block_id\n"
                      "R1,S1,T1,0,B1\n"
                      "R1,S1,T2,0,B1\n"
                      "RT,S1,TT1,0,BT\n"),
        # Trzy zatrzymania, bo postój liczy się tylko na POŚREDNICH: kurs dwuprzystankowy
        # składa się z samych krańców i nie ma w nim ani jednego postoju do zmierzenia.
        "stop_times.txt": ("trip_id,arrival_time,departure_time,stop_id,stop_sequence\n"
                           "T1,06:00:00,06:00:15,A,1\n"
                           "T1,06:02:00,06:02:20,B,2\n"
                           "T1,06:04:00,06:04:00,C,3\n"
                           "T2,06:05:00,06:05:15,A,1\n"
                           "T2,06:07:10,06:07:30,B,2\n"
                           "T2,06:09:10,06:09:10,C,3\n"
                           "TT1,06:00:00,06:00:00,X,1\n"),
        "stops.txt": ("stop_id,stop_name\n"
                      "A,Alfa\n"
                      "B,Beta\n"
                      "C,Gamma\n"
                      "X,Iks\n"),
        "feed_info.txt": ("feed_publisher_name,feed_start_date,feed_end_date\n"
                          "TEST,20260101,20261231\n"),
    }
    members.update(overrides)
    return _zip(members)


# --- czas ---------------------------------------------------------------------

def test_timetable_parses_hours_past_midnight():
    """GTFS dopuszcza 25:14:00. Obcięcie do doby zrobiłoby z nocnych kursów rzadki takt."""
    assert TT.parse_time("25:14:00") == 25 * 3600 + 14 * 60
    assert TT.parse_time("00:00:00") == 0
    assert TT.parse_time("nonsens") is None
    assert TT.parse_time("6:00") is None


def test_timetable_clock_round_trips_past_midnight():
    assert TT.clock(25 * 3600 + 14 * 60) == "25:14:00"


def test_timetable_weekday_column_matches_calendar_txt():
    assert TT.weekday_column("20260902") == "wednesday"
    assert TT.weekday_column("20260906") == "sunday"


# --- służby --------------------------------------------------------------------

def test_timetable_uses_the_weekday_column():
    archive = _feed()
    active, added, removed = TT.services_on(archive, "20260902")
    assert active == {"S1"} and (added, removed) == (0, 0)
    weekend, _a, _r = TT.services_on(archive, "20260906")
    assert weekend == {"S2"}


def test_timetable_calendar_dates_add_and_remove_services():
    """STIB ma 571 wyjątków przy 338 służbach — sam calendar.txt dałby rozkład, którego nie ma."""
    archive = _feed(**{"calendar_dates.txt": ("service_id,date,exception_type\n"
                                              "S1,20260902,2\n"
                                              "S2,20260902,1\n")})
    active, added, removed = TT.services_on(archive, "20260902")
    assert active == {"S2"}
    assert (added, removed) == (1, 1)


def test_timetable_exception_on_another_day_is_ignored():
    archive = _feed(**{"calendar_dates.txt": "service_id,date,exception_type\nS1,20260903,2\n"})
    active, _a, _r = TT.services_on(archive, "20260902")
    assert active == {"S1"}


# --- linie i takty --------------------------------------------------------------

def test_timetable_keeps_only_metro_by_route_type_not_by_name():
    """route_type 1 jest polem znormalizowanym; nazwa linii to tekst redakcyjny."""
    routes = TT.metro_routes(_feed())
    assert set(routes) == {"R1"}


def test_timetable_headways_are_gaps_between_consecutive_departures():
    assert TT.headways([100, 400, 250]) == [150, 150]
    assert TT.headways([]) == []
    assert TT.headways([5]) == []


def test_timetable_headway_summary_reports_mode_not_only_median():
    summary = TT.summarise_headways([300, 300, 300, 900])
    assert summary["mode_s"] == 300
    assert summary["min_s"] == 300 and summary["max_s"] == 900
    assert summary["count"] == 4


def test_timetable_headway_summary_of_nothing_is_none():
    assert TT.summarise_headways([]) is None


# --- postój i czas jazdy --------------------------------------------------------

def test_timetable_separates_dwell_from_run_time():
    """Postój = departure - arrival; czas jazdy = arrival(następna) - departure(ta)."""
    report = TT.survey(_feed(), "20260902", {6})
    assert report["metro_trips"] == 2, "tramwaj nie może wejść do rozkładu metra"
    dwell = report["dwell"][0]
    # Pośrednie jest tylko B, w obu kursach: 06:02:00 -> 06:02:20 i 06:07:10 -> 06:07:30.
    assert dwell["stops"] == 2
    assert dwell["non_zero"] == 2
    assert dwell["min_non_zero_s"] == 20
    assert dwell["max_s"] == 20
    segment = report["segments"][0]
    # T1: 06:00:15 -> 06:02:00 = 105 s;  T2: 06:05:15 -> 06:07:10 = 115 s
    assert segment["samples"] == 2
    assert segment["min_s"] == 105 and segment["max_s"] == 115
    assert abs(segment["mean_s"] - 110.0) < 1e-9


def test_timetable_histogram_covers_every_intermediate_stop():
    report = TT.survey(_feed(), "20260902", {6})
    assert sum(report["dwell_histogram_s"].values()) == 2


def test_timetable_does_not_count_a_trip_end_as_a_zero_dwell():
    """Kraniec kursu ma arrival == departure z definicji. Wliczony do rozkładu postoju
    wygląda jak postój zerowy i zaniża udział postojów niezerowych — dokładnie ten błąd
    zamienił 100 % zatrzymań z postojem na fałszywe 94 %."""
    report = TT.survey(_feed(), "20260902", {6})
    assert 0 not in {int(k) for k in report["dwell_histogram_s"]}
    assert report["dwell"][0]["non_zero_pct"] == 100.0
    assert report["terminus_stops"] == 4, "dwa kursy po dwa krańce"
    # Kraniec początkowy bywa niezerowy — to postój przed odjazdem, nie wymiana pasażerów
    # w biegu. Dlatego krańce raportujemy osobno, a nie wyrzucamy po cichu.
    assert report["terminus_non_zero"] == 2


def test_timetable_reports_service_span_and_first_last():
    report = TT.survey(_feed(), "20260902", {6})
    line = report["lines"][0]
    assert line["first_departure"] == "06:00:15"
    assert line["last_departure"] == "06:05:15"
    assert line["service_span_s"] == 300
    assert line["trips"] == 2


# --- złączenie z osią z T-210 -------------------------------------------------

def _axis(tmpdir, axis_id, stations):
    path = os.path.join(tmpdir, axis_id + ".json")
    with open(path, "w", encoding="utf-8") as handle:
        json.dump({"id": axis_id, "stations": [
            {"stop_id": stop, "chainage_m": chainage} for stop, chainage in stations
        ]}, handle)
    return path


def test_timetable_reads_stop_names_so_segments_are_readable():
    """Odcinek opisany parą identyfikatorów nie da się zestawić z niczym ręcznie."""
    names = TT.stop_names(_feed())
    assert names["A"] == "Alfa" and names["B"] == "Beta"


def test_timetable_joins_axis_by_stop_id_not_by_name():
    with tempfile.TemporaryDirectory() as tmp:
        path = _axis(tmp, "L1_A", [("A", 0.0), ("B", 1234.5)])
        table = TT.axis_chainage([path])
    assert table["A"] == [("L1_A", 0.0)]
    package, distance = TT.segment_distance(table, "A", "B")
    assert package == "L1_A" and abs(distance - 1234.5) < 1e-9


def test_timetable_distance_is_absolute_so_direction_does_not_flip_its_sign():
    with tempfile.TemporaryDirectory() as tmp:
        table = TT.axis_chainage([_axis(tmp, "L1_A", [("A", 500.0), ("B", 100.0)])])
    assert TT.segment_distance(table, "A", "B") == TT.segment_distance(table, "B", "A")
    assert TT.segment_distance(table, "A", "B")[1] == 400.0


def test_timetable_refuses_distance_across_two_packages():
    """Chainage każdego pakietu zaczyna się od własnego zera — odjęcie ich dałoby
    liczbę wyglądającą jak metry i nie będącą metrami. Ciągłość zamyka T-112."""
    with tempfile.TemporaryDirectory() as tmp:
        table = TT.axis_chainage([_axis(tmp, "L1_A", [("A", 0.0)]),
                                  _axis(tmp, "L1_B", [("B", 900.0)])])
    assert TT.segment_distance(table, "A", "B") == (None, None)


def test_timetable_uses_the_shared_package_when_a_stop_lies_on_two_axes():
    with tempfile.TemporaryDirectory() as tmp:
        table = TT.axis_chainage([_axis(tmp, "L1_A", [("A", 0.0), ("B", 700.0)]),
                                  _axis(tmp, "L2_E", [("A", 3000.0)])])
    package, distance = TT.segment_distance(table, "A", "B")
    assert package == "L1_A" and distance == 700.0


def test_timetable_segment_without_axis_gets_no_distance_not_a_zero():
    """Brak odległości musi być brakiem klucza, a nie zerem — zero przeszłoby dalej
    jako 'stacje w tym samym miejscu' i wyprodukowało nieskończoną prędkość."""
    report = TT.survey(_feed(), "20260902", {6})
    assert "distance_m" not in report["segments"][0]
    assert report["segments_with_distance"] == 0


def test_timetable_mean_speed_comes_from_the_median_run_time():
    with tempfile.TemporaryDirectory() as tmp:
        path = _axis(tmp, "L1_A", [("A", 0.0), ("B", 1100.0)])
        report = TT.survey(_feed(), "20260902", {6}, [path])
    segment = report["segments"][0]
    assert segment["package"] == "L1_A" and segment["distance_m"] == 1100.0
    # mediana z [105, 115] wg konwencji narzędzia to 115 s
    assert segment["mean_speed_kmh"] == round(3.6 * 1100.0 / segment["median_s"], 2)
    assert report["segments_with_distance"] == 1


# --- służby: ile kursów naraz -------------------------------------------------

def test_timetable_concurrency_counts_overlapping_trips():
    assert TT.peak_concurrency([(0, 100), (50, 150), (200, 300)]) == (2, 50)


def test_timetable_concurrency_of_nothing_is_zero_without_a_moment():
    assert TT.peak_concurrency([]) == (0, None)


def test_timetable_touching_trips_do_not_count_as_two():
    """Kurs kończący się dokładnie wtedy, gdy zaczyna się następny, to jeden pojazd
    na odcinku, a nie dwa. Zdarzenie końca musi wyprzedzić zdarzenie początku."""
    assert TT.peak_concurrency([(0, 100), (100, 200)])[0] == 1


def test_timetable_network_concurrency_is_not_the_sum_of_line_maxima():
    """Maksima linii wypadają o różnych porach; ich suma zawyżałaby flotę."""
    report = TT.survey(_feed(), "20260902", {6})
    assert report["max_concurrent_trips"] <= sum(r["max_concurrent_trips"] for r in report["lines"])


def test_timetable_reports_when_the_line_is_fullest():
    report = TT.survey(_feed(), "20260902", {6})
    line = report["lines"][0]
    # T1 jedzie 06:00:15–06:04:00, T2 06:05:15–06:09:10 — nigdy razem.
    assert line["max_concurrent_trips"] == 1
    assert line["max_concurrent_at"] == "06:00:15"


# --- obiegi pojazdów ----------------------------------------------------------

def test_timetable_reads_vehicle_blocks_from_the_feed():
    """`block_id` wiąże kursy tego samego pojazdu. Feed STIB go ma, więc liczba obiegów
    jest odczytem, a nie oszacowaniem z taktu i czasu obrotu."""
    report = TT.survey(_feed(), "20260902", {6})
    duties = report["duties"]
    assert duties["blocks"] == 1, "oba kursy metra są jednym obiegiem B1"
    assert duties["trips_per_block"] == {2: 1}
    assert duties["overlapping_trips_in_a_block"] == 0


def test_timetable_block_span_runs_from_first_departure_to_last_arrival():
    duties = TT.survey(_feed(), "20260902", {6})["duties"]
    row = duties["rows"][0]
    assert row["first_departure"] == "06:00:15" and row["last_arrival"] == "06:09:10"
    assert row["span_s"] == 535


def test_timetable_flags_a_block_whose_trips_overlap():
    """Jeden pojazd nie jedzie dwoma kursami naraz. Cichy przelot takiego bloku dałby
    obieg, którego żaden pojazd nie wykona."""
    summary = TT.block_summary({"B1": [(0, 600), (300, 900)]})
    assert summary["overlapping_trips_in_a_block"] == 1


def test_timetable_blocks_in_service_outnumber_trips_in_motion():
    """Pojazd na obrocie na krańcu jest w służbie, ale nie jest w ruchu. Liczba obiegów
    naraz nie może być mniejsza niż liczba kursów naraz."""
    summary = TT.block_summary({"B1": [(0, 100), (200, 300)], "B2": [(50, 250)]})
    assert summary["max_concurrent_blocks"] == 2
    assert TT.peak_concurrency([(0, 100), (200, 300), (50, 250)])[0] == 2


def test_timetable_without_block_id_reports_no_duties_instead_of_guessing():
    feed = _feed(**{"trips.txt": ("route_id,service_id,trip_id,direction_id\n"
                                  "R1,S1,T1,0\n"
                                  "R1,S1,T2,0\n")})
    duties = TT.survey(feed, "20260902", {6})["duties"]
    assert duties["blocks"] == 0
    assert duties["max_concurrent_blocks"] == 0
    assert duties["span_median_s"] is None
