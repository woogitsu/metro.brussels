#!/usr/bin/env python3
"""Bryły elementów stacji ponad peronem (T-212). Bez Blendera i bez pytest.

Cała matematyka `tools/track/station_components.py` jest sprawdzana na liczbach,
nie na renderach — render pokazuje, że coś stoi, ale nie powie, czy schody DOCHODZĄ
do antresoli co do milimetra.
"""
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "track"))
sys.path.insert(0, os.path.join(ROOT, "tools", "blender"))

import profiles as PR  # noqa: E402
import station_components as SC  # noqa: E402
import station_layout as SL  # noqa: E402

#: Peron DECYZJI właściciela z 04.09.2026, nie dowolna okrągła liczba: 95,0 m, czyli
#: skład M7 94,0 m plus metr zapasu. Wcześniejsza wersja tego zadania liczyła na 110 m
#: i taki peron przekraczał obrys stacji Parc (109,1 m, R-007) — patrz
#: `test_components_platform_length_stays_within_the_tightest_station_footprint`.
PLATFORM = {"name": "T", "from_m": 100.0, "to_m": 195.0,
            "length_m": SC.DESIGN_PLATFORM_LENGTH_M}
WALL_M = max(abs(x) for x, _z in PR.profile_points("station"))


def _levels():
    ceiling = max(z for _x, z in PR.profile_points("station"))
    return SC.levels(1.03, ceiling)


# --- poziomy ------------------------------------------------------------------

def test_components_mezzanine_sits_above_the_chamber_not_inside_it():
    """Antresola wewnątrz komory dałaby górny poziom poniżej wzrostu człowieka.

    To nie jest wybór estetyczny, tylko rachunek: profil `station` ma strop na 5,30 m,
    peron na 1,03 m, więc nad peronem zostaje 4,27 m. Płyta 0,40 m i dolny poziom
    2,40 m w świetle zostawiają górnemu 1,47 m. Test liczy to wprost, żeby zmiana
    profilu albo grubości płyty pokazała, że układ przestał się mieścić.
    """
    level = _levels()
    assert level["chamber_clear_m"] == 4.27, level
    inside_upper = (level["chamber_clear_m"]
                    - SC.DESIGN_SLAB_THICKNESS_M - SC.DESIGN_MEZZANINE_CLEAR_M)
    assert inside_upper < 1.60, inside_upper
    assert level["mezzanine_floor_m"] > level["chamber_ceiling_m"], level


def test_components_levels_refuse_a_ceiling_below_the_platform():
    try:
        SC.levels(5.0, 4.0)
    except ValueError:
        return
    raise AssertionError("strop pod peronem został przyjęty")


# --- schody -------------------------------------------------------------------

def test_components_stairs_reach_the_mezzanine_exactly():
    """Suma podstopnic musi dać DOKŁADNIE wznoszenie, a nie tyle, ile wyjdzie z dzielenia.

    Wysokość stopnia jest więc wyliczana z podziału, a nie brana z nominalnej: schody
    muszą dojść tam, gdzie dochodzą. Nominalne 0,17 m przy wznoszeniu 4,67 m dałoby
    27,47 stopnia — zaokrąglenie w dół zostawia 8 cm progu na górze, w górę 9 cm w dół.
    """
    level = _levels()
    flights = SC.stair_flights(level["stair_rise_m"])
    assert flights[-1][4] == level["stair_rise_m"], flights[-1]
    assert flights[0][3] == 0.0, flights[0]
    risers = sum(count for kind, count, _l, _a, _b in flights if kind == "flight")
    assert risers == 27, risers
    actual = level["stair_rise_m"] / risers
    assert abs(actual - SC.DESIGN_STAIR_RISER_M) < 0.01, actual


def test_components_stairs_are_continuous_from_step_to_step():
    """Kontrola do testu wyżej: każdy odcinek zaczyna się tam, gdzie kończy poprzedni.

    Bez tego suma mogłaby się zgadzać przy dziurze w środku — spocznik na złej wysokości
    dałby uskok, którego render z góry w ogóle nie pokazuje.
    """
    flights = SC.stair_flights(_levels()["stair_rise_m"])
    for previous, current in zip(flights, flights[1:]):
        assert previous[4] == current[3], (previous, current)


def test_components_no_flight_is_longer_than_the_limit():
    """Bieg bez spocznika ma granicę; 27 stopni jednym ciągiem to nie są schody publiczne."""
    for rise in (1.0, 2.5, 4.67, 9.0, 15.0):
        flights = SC.stair_flights(rise)
        for kind, risers, _l, _a, _b in flights:
            if kind == "flight":
                assert risers <= SC.DESIGN_STAIR_MAX_RISERS, (rise, risers)
        landings = sum(1 for kind, *_r in flights if kind == "landing")
        runs = sum(1 for kind, *_r in flights if kind == "flight")
        assert landings == runs - 1, (rise, landings, runs)


def test_components_stair_run_matches_the_sum_of_its_parts():
    rise = _levels()["stair_rise_m"]
    parts = sum(length for _k, _r, length, _a, _b in SC.stair_flights(rise))
    assert abs(SC.stair_run_length_m(rise) - parts) < 1e-9


def test_components_stairs_of_zero_rise_are_refused():
    for bad in (0.0, -1.0):
        try:
            SC.stair_flights(bad)
        except ValueError:
            continue
        raise AssertionError(f"wznoszenie {bad} zostało przyjęte")


# --- zespół dostępu -----------------------------------------------------------

def test_components_every_solid_stays_within_the_platform():
    """Zespół nie może wystawać poza peron — tam nie ma już komory, tylko tunel.

    Sprawdzane po OBU krańcach: bryła zaczynająca się przed peronem stoi w tunelu
    tak samo, jak bryła kończąca się za nim.
    """
    level = _levels()
    for side in (1, -1):
        for solid in SC.access_solids(PLATFORM, side, level, WALL_M):
            start = solid["at_m"]
            end = start + solid["length_m"]
            assert start >= PLATFORM["from_m"] - 1e-6, (solid["name"], start)
            assert end <= PLATFORM["to_m"] - 1e-6, (solid["name"], end)


def test_components_stairs_land_on_the_mezzanine_floor():
    level = _levels()
    steps = [s for s in SC.access_solids(PLATFORM, 1, level, WALL_M)
             if s["kind"] == "stairs" and "landing" not in s["name"]]
    tops = [max(z for _y, z in s["section"]) for s in steps]
    assert abs(max(tops) - level["mezzanine_floor_m"]) < 1e-3, (max(tops), level)
    assert abs(min(tops) - level["platform_top_m"]) > 0.05, min(tops)


def test_components_corridor_starts_at_the_wall_and_the_portal_continues_it():
    """Korytarz ma dotykać ściany komory, a portal — końca korytarza.

    Szczelina między nimi jest niewidoczna na renderze z góry i widoczna dopiero
    wtedy, gdy ktoś przez nią przejdzie.
    """
    level = _levels()
    for side in (1, -1):
        solids = {s["kind"]: s for s in SC.access_solids(PLATFORM, side, level, WALL_M)}
        corridor = solids["corridor"]
        portal = solids["portal"]
        c_edges = sorted({y for y, _z in corridor["section"]})
        p_edges = sorted({y for y, _z in portal["section"]})
        near_wall = min(abs(abs(y) - WALL_M) for y in c_edges)
        assert near_wall < 1e-6, (side, c_edges, WALL_M)
        shared = min(abs(c - p) for c in c_edges for p in p_edges)
        assert shared < 1e-6, (side, c_edges, p_edges)
        assert max(abs(y) for y in p_edges) > max(abs(y) for y in c_edges)


def test_components_corridor_and_portal_have_walkable_openings():
    """The previous single prisms filled the entire passage volume.

    Test the actual 3-D occupancy at the centre of each access component,
    while confirming that floor, roof and both jambs still surround it.
    """
    level = _levels()
    assert SC.DESIGN_CORRIDOR_WIDTH_M - 2 * SC.DESIGN_ACCESS_SHELL_M >= SC.DESIGN_STAIR_WIDTH_M, (
        "korytarz po odjęciu dwóch ościeży nie może być węższy od schodów")
    for side in (1, -1):
        solids = SC.access_solids(PLATFORM, side, level, WALL_M)
        for kind, width, clear in (("corridor", SC.DESIGN_CORRIDOR_WIDTH_M,
                                    SC.DESIGN_CORRIDOR_CLEAR_M),
                                   ("portal", SC.DESIGN_PORTAL_WIDTH_M,
                                    SC.DESIGN_PORTAL_CLEAR_M)):
            pieces = [s for s in solids if s["kind"] == kind]
            assert len(pieces) == 4, (kind, pieces)
            start = min(s["at_m"] for s in pieces)
            y_min = min(y for s in pieces for y, _z in s["section"])
            y_max = max(y for s in pieces for y, _z in s["section"])
            centre_x = start + width / 2
            centre_y = (y_min + y_max) / 2
            floor = level["mezzanine_floor_m"]

            def occupied(x, y, z):
                return any(s["at_m"] <= x <= s["at_m"] + s["length_m"]
                           and min(v[0] for v in s["section"]) <= y <= max(v[0] for v in s["section"])
                           and min(v[1] for v in s["section"]) <= z <= max(v[1] for v in s["section"])
                           for s in pieces)

            assert not occupied(centre_x, centre_y, floor + clear / 2), kind
            assert occupied(centre_x, centre_y, floor - SC.DESIGN_ACCESS_SHELL_M / 2), kind
            assert occupied(centre_x, centre_y, floor + clear + SC.DESIGN_ACCESS_SHELL_M / 2), kind
            assert occupied(start + SC.DESIGN_ACCESS_SHELL_M / 2, centre_y, floor + clear / 2), kind
            assert occupied(start + width - SC.DESIGN_ACCESS_SHELL_M / 2,
                            centre_y, floor + clear / 2), kind


def test_components_mirroring_the_side_mirrors_every_solid():
    """Kontrola negatywna do wszystkiego wyżej: strona jest parametrem, nie wpisana."""
    level = _levels()
    right = SC.access_solids(PLATFORM, 1, level, WALL_M)
    left = SC.access_solids(PLATFORM, -1, level, WALL_M)
    assert len(right) == len(left)
    for a, b in zip(right, left):
        assert a["name"] == b["name"] and a["at_m"] == b["at_m"]
        mirrored = sorted((-y, z) for y, z in b["section"])
        assert sorted(a["section"]) == mirrored, (a["name"], a["section"], b["section"])


def test_components_mezzanine_spans_both_tracks():
    """Antresola nad komorą musi przykryć oba tory, inaczej nie jest antresolą stacji."""
    level = _levels()
    mezzanine = [s for s in SC.access_solids(PLATFORM, 1, level, WALL_M)
                 if s["kind"] == "mezzanine"][0]
    ys = [y for y, _z in mezzanine["section"]]
    assert min(ys) <= -WALL_M + 1e-9 and max(ys) >= WALL_M - 1e-9, ys
    for offset in PR.PROFILES["station"]["track_offsets"]:
        assert min(ys) < offset < max(ys), offset


def test_components_mezzanine_has_clear_headroom_between_slabs():
    """The former mezzanine prism filled the entire 2.60 m standing space."""
    level = _levels()
    pieces = SC.access_solids(PLATFORM, 1, level, WALL_M)
    floor = next(s for s in pieces if s["name"] == "mezzanine_a")
    roof = next(s for s in pieces if s["name"] == "mezzanine_a_roof")
    assert floor["at_m"] == roof["at_m"], (floor, roof)
    assert floor["length_m"] == roof["length_m"], (floor, roof)
    floor_top = max(z for _y, z in floor["section"])
    roof_bottom = min(z for _y, z in roof["section"])
    assert floor_top == level["mezzanine_floor_m"], (floor_top, level)
    assert roof_bottom == level["mezzanine_ceiling_m"], (roof_bottom, level)
    assert abs(roof_bottom - floor_top - SC.DESIGN_MEZZANINE_CLEAR_M) < 1e-9, (floor_top, roof_bottom)


# --- wybór elementów ----------------------------------------------------------

def test_components_selection_returns_only_what_was_asked_for():
    level = _levels()
    for wanted in (("stairs",), ("lift", "portal"), SC.COMPONENTS):
        got = {s["kind"] for s in SC.station_solids(PLATFORM, level, WALL_M, wanted)}
        assert got == set(wanted), (wanted, got)


def test_components_unknown_component_is_refused():
    """Literówka w `--component` ma być odmową, a nie cicho pustą stacją."""
    try:
        SC.station_solids(PLATFORM, _levels(), WALL_M, ("schody",))
    except ValueError as error:
        assert "schody" in str(error)
        return
    raise AssertionError("nieznany element został przyjęty")


def test_components_rectangle_refuses_a_degenerate_side():
    for bad in ((1.0, 1.0, 0.0, 2.0), (0.0, 2.0, 3.0, 3.0), (2.0, 1.0, 0.0, 1.0)):
        try:
            SC.rectangle(*bad)
        except ValueError:
            continue
        raise AssertionError(f"zdegenerowany prostokąt {bad} został przyjęty")


def test_components_every_design_constant_is_listed_in_the_assumptions():
    """Stała bez wpisu w `DESIGN_ASSUMPTIONS` nie trafia do metryk i znika z raportu."""
    declared = set(SC.DESIGN_ASSUMPTIONS)
    actual = {n for n in dir(SC) if n.startswith("DESIGN_") and n != "DESIGN_ASSUMPTIONS"}
    assert declared == actual, (actual - declared, declared - actual)


# --- długość peronu: kontrola z R-007 -----------------------------------------

def test_components_platform_length_stays_within_the_tightest_station_footprint():
    """R-007 §5 pkt 3: „generator dający peron dłuższy niż obrys stacji jest na pewno
    błędny". Najciaśniejszy przypadek pakietu A to Parc, 109,1 m.

    Ta bramka istnieje, bo pierwsza wersja T-212 stała na peronie 110 m — czyli
    0,9 m ZA obrysem Parc — i nic tego nie porównywało: liczba mieszkała w wywołaniu
    generatora i w komentarzu raportu, a nie w kodzie. Test sprawdza obie strony
    granicy osobno, bo granica należy do peronu: peron równy obrysowi jeszcze się
    mieści, dopiero dłuższy wypada.
    """
    assert SC.TIGHTEST_STATION_FOOTPRINT_M == 109.1, SC.TIGHTEST_STATION_FOOTPRINT_M
    assert SC.platform_fits_the_station(SC.DESIGN_PLATFORM_LENGTH_M), \
        (SC.DESIGN_PLATFORM_LENGTH_M, SC.TIGHTEST_STATION_FOOTPRINT_M)
    assert not SC.platform_fits_the_station(110.0), \
        "110 m przekracza obrys Parc o 0,9 m, a kontrola tego nie widzi"
    assert SC.platform_fits_the_station(SC.TIGHTEST_STATION_FOOTPRINT_M), \
        "peron równy obrysowi stacji jeszcze się w nim mieści"
    assert not SC.platform_fits_the_station(SC.TIGHTEST_STATION_FOOTPRINT_M + 0.001), \
        "peron milimetr dłuższy od obrysu stacji już się w nim nie mieści"


def test_components_platform_length_is_the_train_plus_a_metre():
    """Dolna granica z R-007 §4: peron krótszy od składu M7 jest sprzeczny z ruchem.

    Zapas nad składem jest jawny i policzony, a nie „na oko": 1,00 m to 3,2× największy
    zmierzony błąd zatrzymania autopilota na pakiecie A (0,307 m, `reports/T-401-line-run.md`).
    Test wiąże stałą z długością składu ze specyfikacji, więc zmiana specyfikacji M7
    nie zostawi cicho peronu krótszego od pociągu.
    """
    train_m = SL.train_length_m()
    assert train_m == 94.0, train_m
    assert SC.DESIGN_PLATFORM_LENGTH_M >= train_m, (SC.DESIGN_PLATFORM_LENGTH_M, train_m)
    assert abs(SC.DESIGN_PLATFORM_LENGTH_M - train_m - 1.0) < 1e-9, \
        (SC.DESIGN_PLATFORM_LENGTH_M, train_m)


def test_components_the_test_platform_is_the_decided_one():
    """Zespół dostępu jest liczony na peronie DECYZJI, nie na dowolnym peronie.

    Bez tego wiązania fixture mógłby zostać na starej długości i wszystkie testy
    zespołu przechodziłyby na peronie, którego generator już nie buduje.
    """
    assert PLATFORM["length_m"] == SC.DESIGN_PLATFORM_LENGTH_M
    assert abs((PLATFORM["to_m"] - PLATFORM["from_m"])
               - SC.DESIGN_PLATFORM_LENGTH_M) < 1e-9, PLATFORM


def test_components_footprint_control_refuses_degenerate_input():
    """Zero i wartość ujemna nie są długością peronu ani obrysem stacji."""
    for length_m, footprint_m in ((0.0, 109.1), (-95.0, 109.1), (95.0, 0.0), (95.0, -1.0)):
        try:
            SC.platform_fits_the_station(length_m, footprint_m)
        except ValueError:
            continue
        raise AssertionError(f"przyjęte: peron {length_m} m, obrys {footprint_m} m")


# --- otwór w antresoli --------------------------------------------------------

def test_components_mezzanine_has_an_opening_over_the_stairs_and_lift():
    """Render `_side` pierwszej wersji pokazał to natychmiast: schody dobijały do spodu
    zamkniętej płyty i kończyły się sufitem.

    Otwór nie jest wymyślony — wynika z obrysu tego, co ma przez niego przechodzić.
    Test sprawdza to samo od drugiej strony: żaden schodek ani szyb windy nie może
    leżeć pod płytą.
    """
    level = _levels()
    for side in (1, -1):
        solids = SC.access_solids(PLATFORM, side, level, WALL_M)
        slabs = [s for s in solids if s["kind"] == "mezzanine"]
        through = [s for s in solids if s["kind"] in ("stairs", "lift")]
        assert len(slabs) > 1, "antresola nie została przecięta otworem"

        for item in through:
            top = max(z for _y, z in item["section"])
            if top < level["mezzanine_floor_m"] - 1e-6:
                continue
            i_from, i_to = item["at_m"], item["at_m"] + item["length_m"]
            iy = [y for y, _z in item["section"]]
            for slab in slabs:
                s_from, s_to = slab["at_m"], slab["at_m"] + slab["length_m"]
                sy = [y for y, _z in slab["section"]]
                overlaps_m = min(i_to, s_to) - max(i_from, s_from) > 1e-6
                overlaps_y = min(max(iy), max(sy)) - max(min(iy), min(sy)) > 1e-6
                assert not (overlaps_m and overlaps_y), \
                    (side, item["name"], slab["name"], (i_from, i_to), (s_from, s_to))


def test_components_mezzanine_pieces_still_cover_the_full_length():
    """Kontrola negatywna do testu wyżej: otwór ma być otworem, a nie zniknięciem płyty.

    Bez tego „antresola z otworem" mogłaby oznaczać brak antresoli — i test wyżej
    przeszedłby wzorowo.
    """
    level = _levels()
    slabs = [s for s in SC.access_solids(PLATFORM, 1, level, WALL_M)
             if s["kind"] == "mezzanine"]
    spans = sorted((s["at_m"], s["at_m"] + s["length_m"]) for s in slabs)
    covered = []
    for start, end in spans:
        if covered and start <= covered[-1][1] + 1e-6:
            covered[-1] = (covered[-1][0], max(covered[-1][1], end))
        else:
            covered.append((start, end))
    assert len(covered) == 1, covered
    assert abs((covered[0][1] - covered[0][0]) - SC.DESIGN_MEZZANINE_LENGTH_M) < 1e-6, covered

    at_void = [s for s in slabs if s["name"].endswith(("_near", "_far"))]
    assert at_void, "przy otworze nie został ani jeden pas płyty"
    widest = max(max(y for y, _z in s["section"]) - min(y for y, _z in s["section"])
                 for s in at_void)
    assert widest > 1.0, f"pas przy otworze ma tylko {widest:.2f} m — to nie jest antresola"

# 6.D25: uruchomienie tego pliku WPROST idzie ta sama droga, co caly zestaw —
# z licznikiem asercji i z odmowa przy zerze testow. Bez tej gałęzi `python3
# tools/tests/<modul>.py` konczyl sie kodem 0, nie wykonawszy ani jednego testu.
if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))
