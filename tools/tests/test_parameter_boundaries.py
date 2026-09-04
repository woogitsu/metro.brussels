#!/usr/bin/env python3
"""Granice porównań w modułach parametrów geometrii i metadanych.

**Po co ten plik istnieje.** Przegląd mutacyjny na commicie `737d592` pokazał, że
siedem modułów liczących parametry geometrii i metadanych ma bramki, które przechodzą
niezależnie od tego, czy porównanie w środku brzmi `<` czy `<=`. Wzorzec był wszędzie
ten sam: testy podają wartości Z DALA od progu, więc sprawdzają kierunek nierówności,
a nie sam próg. `profiles.py` jest tu najważniejszy — z niego wynika, czy skład M7
mieści się w tunelu — i tam ocalało 11 z 13 mutacji.

**Zasada, którą ten plik stosuje.** Wartość DOKŁADNIE równa progowi jest jedynym
wejściem, które odróżnia `>` od `>=`. Wszystko inne obie wersje klasyfikują tak samo.

**Pułapka zmiennoprzecinkowa.** „Dokładnie na granicy" trzeba skonstruować, a nie
zadeklarować: `abs((6700.0 + 0.01) - 6700.0)` daje 0,010000000000218, czyli NAD progiem
0,01. Różnica dwóch liczb jest dokładna tylko wtedy, gdy jedna strona jest zerem albo
gdy próg jest potęgą dwójki. Każdy test, który tak kombinuje, mówi o tym w swoim
docstringu i pokazuje konstrukcję.

**Czego ten plik nie robi.** Nie dubluje `test_tuning_constants.py` (tam są przypięte
domyślne wartości CLI) ani `test_dimension_audit.py` (tam kod jest zestawiany
z `docs/21-measured-vs-assumed.md`). Tu są wyłącznie GRANICE porównań oraz te liczby
projektowe, których nie pilnuje ani jedno, ani drugie.
"""
import datetime
import json
import math
import os
import sys
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
for package in ("blender", "track", "data", "physics"):
    sys.path.insert(0, os.path.join(ROOT, "tools", package))

import data_freshness as DF  # noqa: E402
import detail_layout as DL  # noqa: E402
import network_chainage as NC  # noqa: E402
import profiles  # noqa: E402
import provenance as PROV  # noqa: E402
import station_layout as SL  # noqa: E402


# =============================================================================
# tools/blender/profiles.py — przekroje tuneli i skrajnia M7
# =============================================================================

def test_profiles_dedupe_drops_a_point_exactly_at_the_tolerance():
    """`_dedupe` zostawia punkt, gdy jest DALEJ niż `eps` — równo `eps` to za mało.

    Konstrukcja granicy: punkt (0,01; 0) leży od (0; 0) w odległości `math.dist`
    równej dokładnie literałowi `0.01`, bo jedna strona odejmowania jest zerem,
    a `hypot` z jedną niezerową składową zwraca ją bez zaokrąglenia. Gdyby oba
    punkty stały gdziekolwiek indziej, odległość wyszłaby o kilka ostatnich bitów
    obok progu i test „na granicy" granicy by nie dotknął.

    Bez tego testu `>` -> `>=` przechodzi całą suitę: obrysy trzech profili nie mają
    ani jednej pary sąsiednich punktów oddalonej o dokładnie 0,01 m (zmierzone:
    1 trafienie w granicę na 47 porównań, i to trafienie pochodzi z tego testu).
    """
    kept = profiles._dedupe([(0.0, 0.0), (0.01, 0.0), (1.0, 0.0)])
    assert kept == [(0.0, 0.0), (1.0, 0.0)], kept
    # Kontrola kierunku: dwa razy dalej i punkt zostaje.
    assert profiles._dedupe([(0.0, 0.0), (0.02, 0.0), (1.0, 0.0)]) == \
        [(0.0, 0.0), (0.02, 0.0), (1.0, 0.0)]


def test_profiles_dedupe_closes_the_ring_when_the_last_point_is_exactly_at_the_tolerance():
    """Domknięcie obrysu: ostatni punkt równo `eps` od pierwszego jest USUWANY.

    To ta sama granica co wyżej, tylko po drugiej stronie pętli, i ma znaczenie:
    obrys profilu jest ringiem, więc zdublowany punkt startowy dałby krawędź
    o zerowej długości, a z niej zdegenerowaną ściankę w wyciągnięciu tunelu.

    Granica skonstruowana jak w teście wyżej — (0,01; 0) względem (0; 0).
    """
    ring = profiles._dedupe([(0.0, 0.0), (1.0, 0.0), (0.01, 0.0)])
    assert ring == [(0.0, 0.0), (1.0, 0.0)], ring
    # Kontrola kierunku: dalej niż eps i punkt zostaje trzecim wierzchołkiem.
    assert len(profiles._dedupe([(0.0, 0.0), (1.0, 0.0), (0.02, 0.0)])) == 3


def test_profiles_dedupe_closes_a_three_point_ring_too():
    """Warunek domknięcia brzmi `len(out) > 2`, czyli JUŻ trójkąt wolno domknąć.

    Mutacja `2` -> `3` przechodziła całą suitę, bo wszystkie trzy zacommitowane
    profile mają kilkanaście do trzydziestu wierzchołków. Zdegenerowany trójkąt
    jest jednak dokładnie tym, co `_dedupe` ma sprzątać — obrys, który po
    scaleniu bliskich punktów przestał być wielokątem.
    """
    ring = profiles._dedupe([(0.0, 0.0), (1.0, 0.0), (0.005, 0.0)])
    assert ring == [(0.0, 0.0), (1.0, 0.0)], ring


def test_profiles_a_point_exactly_on_the_tunnel_wall_counts_as_inside():
    """Ściana tunelu NALEŻY do przekroju — punkt o x równym skrajnemu x jest wewnątrz.

    Trzy porównania trzymają tę odpowiedź (`_inside` bramkuje po bbox, a
    `_vertical_hits` przycina krawędzie do przedziału x) i wszystkie sześć mutacji
    `<=` -> `<` przechodziło całą suitę. Powód jest mierzalny: siatka 1102 wejść
    trafiła w granicę 20 razy, ale ANI RAZ w punkcie, w którym `fits_gauge` pyta —
    skrajnia M7 stoi na torze ±2,10 m i przy 0,30 m luzu sięga x = ±3,75 m, czyli
    prawie metr od ściany `box_double` (±4,70 m).

    Gdyby ściana przestała należeć do przekroju, `min_clearance` szukałby przez
    bisekcję luzu, przy którym skrajnia DOTYKA ściany, i odpowiedź zależałaby od
    tego, po której stronie ostatniego bitu wypadnie środek przedziału. Wartości
    x są brane wprost z literałów w `PROFILES`, więc równość jest dokładna.
    """
    for name, edge in (("box_double", 4.70), ("station", 7.60)):
        assert profiles._inside(name, -edge, 0.0), f"{name}: lewa ściana"
        assert profiles._inside(name, edge, 0.0), f"{name}: prawa ściana"
        # Kontrola kierunku: milimetr za ścianą to już nie tunel.
        assert not profiles._inside(name, -edge - 0.001, 0.0)
        assert not profiles._inside(name, edge + 0.001, 0.0)


def test_profiles_the_floor_and_the_roof_count_as_inside_too():
    """To samo w pionie: spód koryta i sklepienie należą do przekroju.

    W osi tunelu (x = 0) interpolacja po krawędzi poziomej daje y równe literałowi
    z `PROFILES` co do bitu — t wypada dokładnie na 0,5, a oba końce krawędzi mają
    to samo y, więc `y1 + t*(y2-y1)` to `y1 + 0.5*0.0`.
    """
    for name, floor, roof in (("box_double", -1.20, 4.70), ("station", -1.20, 5.30)):
        assert profiles._inside(name, 0.0, floor), f"{name}: poziom koryta"
        assert profiles._inside(name, 0.0, roof), f"{name}: sklepienie"
        assert not profiles._inside(name, 0.0, floor - 0.001)
        assert not profiles._inside(name, 0.0, roof + 0.001)


def test_profiles_min_clearance_stops_when_the_bracket_is_no_wider_than_eps():
    """`eps` w bisekcji jest tolerancją WŁĄCZNIE: przedział równy `eps` już wystarcza.

    Granicę da się tu trafić tylko potęgami dwójki. Przy domyślnych `lo=0.0`,
    `hi=1.5`, `eps=0.005` szerokość przedziału to 1,5/2^n i nigdy nie zrówna się
    z 0,005 — dlatego mutacja `>` -> `>=` przechodzi całą suitę mimo 74 wykonań
    pętli. Tutaj `lo=0`, `hi=1`, `eps=0,125 = 2^-3`, więc kolejne szerokości
    1, 1/2, 1/4, 1/8 są dokładne i czwarta trafia w próg co do bitu.

    `box_double` mieści skrajnię z luzem ok. 1,08 m, więc każdy sprawdzany środek
    przedziału „pasuje" i dolny koniec rośnie: 0 -> 0,5 -> 0,75 -> 0,875. Wersja
    z `>=` robi jeszcze jeden krok i kończy na 0,9375.
    """
    assert profiles.min_clearance("box_double", 0.0, 1.0, 0.125) == 0.875


def test_profiles_design_numbers_that_no_other_test_pins():
    """Liczby projektowe `profiles.py` przypięte WPROST, bo mutacja ich nie widzi.

    Przemiatanie mutacyjne rusza literały stojące w PORÓWNANIACH, a te siedzą
    w przypisaniach i w słowniku `PROFILES` — dla przeglądu są niewidoczne, a dla
    geometrii są wszystkim. `docs/21-measured-vs-assumed.md` pilnuje wymiarów
    zewnętrznych (`test_dimension_audit.py`) i rozstawu torów `box_double`;
    reszta nie była pilnowana przez nic.

    Skąd te liczby: wszystkie trzy profile mają `source_level="design"`, czyli są
    **wartościami projektowymi, nie pomiarami STIB** — dokument audytu mówi to
    wprost („Żaden nie jest pomiarem STIB"). Ten test nie twierdzi więc, że tak
    wygląda tunel w Brukseli; twierdzi, że nikt nie zmieni projektu po cichu.
    """
    assert profiles.M7_WIDTH_M == 2.70
    assert profiles.M7_HEIGHT_M == 3.60
    assert profiles.M7_ROOF_CHAMFER_M == 0.35
    assert profiles.CLEARANCE_M == 0.30

    bore = profiles.PROFILES["bore_single"]
    assert (bore["radius"], bore["center_y"], bore["floor_offset"], bore["segments"]) == \
        (3.05, 1.45, -1.20, 28), bore
    assert bore["track_offsets"] == [0.0]

    station = profiles.PROFILES["station"]
    assert station["track_offsets"] == [-2.10, 2.10]
    assert station["platform_height_m"] == 1.05
    assert station["platform_edge_x"] == [-4.05, 4.05]
    assert profiles.PROFILES["box_double"]["track_offsets"] == [-2.10, 2.10]


def test_profiles_vehicle_gauge_is_the_m7_box_grown_by_the_clearance():
    """Skrajnia to pudło M7 powiększone o luz, a nie osobna lista liczb.

    Przypinam WYPROWADZENIE: szerokość skrajni ma iść za `M7_WIDTH_M`, a nie stać
    obok niej. Gdyby ktoś zmienił pudło, a skrajnia została, „mieści się w tunelu"
    zaczęłoby odpowiadać na inne pytanie niż zadane.
    """
    gauge = profiles.vehicle_gauge()
    xs = [p[0] for p in gauge]
    ys = [p[1] for p in gauge]
    assert max(xs) - min(xs) == profiles.M7_WIDTH_M + 2 * profiles.CLEARANCE_M
    assert max(ys) == profiles.M7_HEIGHT_M + profiles.CLEARANCE_M
    # Spód skrajni siedzi 0,10 m PONIŻEJ główki szyny — patrz docstring `placement.py`.
    assert min(ys) == -0.10
    assert profiles.vehicle_gauge(0.0)[1][0] - profiles.vehicle_gauge(0.0)[0][0] == \
        profiles.M7_WIDTH_M


# =============================================================================
# tools/blender/m7_layout.py — bryła składu i jej skrajnia
# =============================================================================

def _m7_layout():
    import m7_layout
    return m7_layout


def test_m7_doors_exactly_filling_their_slot_are_still_accepted():
    """Próg brzmi „nie mieści się", a nie „ledwo się mieści".

    `double_doors` odrzuca układ, gdy krok drzwi jest MNIEJSZY niż otwór. Otwór
    równy krokowi to układ styk w styk — dopuszczony, choć bez zapasu. Bez wejścia
    dokładnie na granicy `<` -> `<=` przechodzi całą suitę, bo zacommitowany M7
    ma krok 2,13 m przy otworze 1,60 m, czyli pół metra luzu.

    Granica jest dokładna z konstrukcji: szerokość otworu bierzemy z TEJ SAMEJ
    operacji, którą wykona kod — `(end - start) / doors_per_car` na tym samym
    rozkładzie — zamiast wpisywać liczbę i liczyć na to, że trafi w ostatni bit.
    """
    m7_layout = _m7_layout()
    spec = dict(m7_layout.load_spec(), cars=1, double_doors_per_side=1,
                length_m=20.0, double_door_opening_width_m=0.1)
    probe = m7_layout.Layout(spec)
    start, end = probe.door_usable_span(0)
    exact = (end - start) / probe.doors_per_car

    doors = m7_layout.Layout(dict(spec, double_door_opening_width_m=exact)).double_doors()
    assert len(doors) == 2, doors  # jeden otwór na stronę
    # Kontrola kierunku: otwór szerszy o promil już się nie mieści.
    try:
        m7_layout.Layout(dict(spec, double_door_opening_width_m=exact * 1.000001)).double_doors()
    except ValueError:
        pass
    else:
        raise AssertionError("otwór szerszy niż krok powinien zostać odrzucony")


def test_m7_body_exactly_on_the_gauge_tolerance_still_fits():
    """Tolerancja 1e-9 m w kontroli skrajni jest WŁĄCZNIE, po wszystkich czterech stronach.

    `fits_vehicle_gauge` porównuje obrys pudła ze skrajnią z `profiles.py` z zapasem
    jednego nanometra na błąd zaokrągleń. Cztery mutacje (`<` -> `<=` i `>` -> `>=`
    dla szerokości i dla wysokości) przechodziły całą suitę, bo prawdziwy M7 ma
    do skrajni 0 m zapasu dokładnie, a nigdy nanometr.

    Granica dokładnie: nadpisujemy JEDEN wymiar egzemplarza wartością policzoną tym
    samym wyrażeniem, którego użyje warunek (`min(gy) - 1e-9` itd.). Negacja i
    dzielenie przez dwa są w IEEE 754 dokładne, więc `-(max(gy) + 1e-9)` to co do
    bitu ta sama liczba co `min(gy) - 1e-9`.
    """
    m7_layout = _m7_layout()
    gauge = profiles.vehicle_gauge(clearance=0.0)
    gy = [p[0] for p in gauge]
    gz = [p[1] for p in gauge]

    for attribute, value in (("half_width", max(gy) + 1e-9),
                             ("body_bottom_z", min(gz) - 1e-9),
                             ("roof_z", max(gz) + 1e-9)):
        layout = m7_layout.Layout()
        setattr(layout, attribute, value)
        ok, message = layout.fits_vehicle_gauge()
        assert ok, f"{attribute} dokładnie na tolerancji: {message}"

    # Kontrola kierunku: milimetr, a nie nanometr, i bryła wychodzi ze skrajni.
    for attribute, value in (("half_width", max(gy) + 0.001),
                             ("body_bottom_z", min(gz) - 0.001),
                             ("roof_z", max(gz) + 0.001)):
        layout = m7_layout.Layout()
        setattr(layout, attribute, value)
        assert not layout.fits_vehicle_gauge()[0], attribute


# =============================================================================
# tools/track/detail_layout.py — kilometraże detali
# =============================================================================

CFG = None


def _cfg():
    global CFG
    if CFG is None:
        import braking
        CFG = braking.params()
    return CFG


def test_detail_hectometre_step_of_a_millimetre_is_still_positive():
    """Próg kroku brzmi „dodatni", a nie „większy od milimetra".

    Mutacja `0.0` -> `0.001` przechodziła całą suitę, bo jedyny test progu podaje
    krok zerowy — a zero jest po tej samej stronie obu wartości. Krok milimetrowy
    nie ma sensu praktycznego dla słupków hektometrowych, ale rozstrzyga, czy
    warunek pilnuje ZNAKU, czy przemyconej wartości minimalnej.
    """
    assert len(DL.hectometre_marks(0.1, 0.001)) == 111
    assert DL.hectometre_marks(0.01, 0.0005)[:2] == [0.0, 0.0]


def test_detail_hectometre_one_centimetre_past_the_end_is_still_kept():
    """Tolerancja `SAME_PLACE_M` na końcu osi jest WŁĄCZNIE.

    Oś krótsza o centymetr od okrągłego hektometru dostaje ten hektometr, bo
    `chainage_m` w osi jest zapisany z dokładnością do centymetra — rozróżnianie
    czegokolwiek poniżej byłoby rozróżnianiem szumu zapisu.

    Granica dokładna: `100.0 - 0.01` i z powrotem `+ 0.01` daje w IEEE 754 znowu
    dokładnie 100,0 (asercja poniżej to sprawdza, żeby konstrukcja nie zgniła po
    cichu). Nie każda para liczb tak działa — `(6700.0 + 0.01) - 6700.0` daje
    0,010000000000218, czyli NAD progiem.
    """
    length = 100.0 - DL.SAME_PLACE_M
    assert length + DL.SAME_PLACE_M == 100.0, "konstrukcja granicy przestała być dokładna"
    assert DL.hectometre_marks(length, 100.0) == [0.0, 100.0]
    # Kontrola kierunku: dwa centymetry za krótko i hektometru już nie ma.
    assert DL.hectometre_marks(100.0 - 2 * DL.SAME_PLACE_M, 100.0) == [0.0]


def test_detail_a_creeping_train_still_has_a_braking_distance():
    """Zerem jest POSTÓJ, a nie „prawie postój".

    Mutacja progu `0.0` -> `0.001` w `braking_distance_m` przechodziła całą suitę:
    jedyny test podaje 0 m/s, a 0 leży po tej samej stronie obu progów. Podmieniony
    próg zwracałby zero drogi hamowania dla prędkości pełzania, czyli po cichu
    kasowałby punkt hamowania zamiast go policzyć.
    """
    assert DL.braking_distance_m(0.001, _cfg()["service"], _cfg()["jerk"]) > 0.0
    assert DL.braking_distance_m(0.0, _cfg()["service"], _cfg()["jerk"]) == 0.0


def test_detail_deceleration_exactly_at_the_plateau_ceiling_uses_the_ramp_formula():
    """Przy opóźnieniu równym sufitowi plateau ma zerową długość — liczy rampa.

    Obie gałęzie są tu matematycznie zgodne (zmierzona różnica: 4·10⁻¹⁶ m, czyli
    znacznie poniżej centymetra, do którego kilometraże i tak są zaokrąglane), więc
    ten test nie broni liczby, tylko WYBORU GAŁĘZI: `>=` znaczy „sufit należy do
    rampy". Granicę konstruujemy tym samym wywołaniem, którego użyje warunek.
    """
    import braking
    speed = 2.0
    ceiling = braking.plateau_ceiling_mps2(speed, 0.0, _cfg()["jerk"])
    assert DL.braking_distance_m(speed, ceiling, _cfg()["jerk"]) == \
        braking.ramp_only_distance_m(speed, 0.0, _cfg()["jerk"])


def test_detail_brake_point_exactly_one_centimetre_after_the_previous_station_is_dropped():
    """Punkt hamowania dokładnie na granicy tolerancji liczy się jako „na stacji".

    Konstrukcja granicy: kilometraż poprzedniej stacji bierzemy jako
    `punkt - SAME_PLACE_M`, a potem sprawdzamy asercją, że dodanie tolerancji
    wraca DOKŁADNIE do punktu. Odwrotna kolejność (dodać centymetr do okrągłego
    kilometrażu) rozjeżdża się na ostatnich bitach — patrz docstring modułu.
    """
    distance = DL.braking_distance_m(20.0, _cfg()["service"], _cfg()["jerk"])
    station_at = 1000.0
    point = station_at - distance
    previous_at = point - DL.SAME_PLACE_M
    assert previous_at + DL.SAME_PLACE_M == point, "konstrukcja granicy przestała być dokładna"

    stations = [{"name": "A", "chainage_m": previous_at},
                {"name": "B", "chainage_m": station_at}]
    marks, skipped = DL.braking_marks(stations, 20.0, _cfg()["service"], _cfg()["jerk"])
    assert marks == [], marks
    assert len(skipped) == 1 and skipped[0]["station"] == "B"


def test_detail_two_marks_exactly_one_centimetre_apart_are_one_place():
    """Scalanie znaczników: dokładnie `SAME_PLACE_M` to JESZCZE to samo miejsce.

    Granica jest dokładna, bo jedna strona odejmowania jest zerem — stacja na
    kilometrażu 0,01 m i słupek hektometrowy na 0,0 m dają różnicę równą literałowi
    `0.01` co do bitu. Ta sama para liczb dalej od zera już by nie trafiła:
    `abs((6700.0 + 0.01) - 6700.0)` to 0,010000000000218, czyli NAD progiem.
    """
    axis = {"id": "T", "length_m": 100.0,
            "stations": [{"name": "A", "chainage_m": DL.SAME_PLACE_M, "stop_id": "P0"}]}
    kept, _skipped = DL.layout(axis)
    assert [(e["chainage_m"], e["kind"]) for e in kept] == \
        [(0.0, "hectometre"), (100.0, "hectometre")], kept

    # Kontrola kierunku: dwa centymetry to już dwa miejsca.
    axis["stations"][0]["chainage_m"] = 2 * DL.SAME_PLACE_M
    kept, _skipped = DL.layout(axis)
    assert [e["kind"] for e in kept] == ["hectometre", "station", "hectometre"], kept


# =============================================================================
# tools/track/network_chainage.py — dziury i kolizje między pakietami
# =============================================================================

def _line(x0, y0, x1, y1, count=100):
    return [(x0 + (x1 - x0) * i / count, y0 + (y1 - y0) * i / count) for i in range(count + 1)]


def _axis(points, from_station="A", to_station="B"):
    return {
        "document": {"package": {"id": "X", "name": "pakiet X",
                                 "from": from_station, "to": to_station},
                     "stations": [], "vertical": {"status": "not_modelled"},
                     "length_m": None},
        "points": points,
        "chainages": NC.chainages(points),
    }


def test_network_gap_of_exactly_two_kilometres_is_still_reported():
    """Limit dziury to „dalej niż 2 km", a nie „2 km i dalej".

    Istniejący test odrzucania podaje 50 km, więc przechodzi zarówno z progiem
    2000, jak i 2020 m i zarówno z `>`, jak i z `>=`. Dwa kilometry to dolne
    ograniczenie na brakujący tor między pakietami — dziura akurat tej długości
    jest tą, o której raport ma powiedzieć, a nie tą, którą ma przemilczeć.

    Granica dokładna: `math.dist((100,0),(2100,0))` to `hypot` z jedną niezerową
    składową, czyli dokładnie 2000,0.
    """
    axes = {"P": _axis(_line(0.0, 0.0, 100.0, 0.0)),
            "Q": _axis(_line(2100.0, 0.0, 2200.0, 0.0))}
    assert [g["chord_m"] for g in NC.endpoint_gaps(axes, NC.DEFAULT_CONFLICT_M)] == [2000.0]

    # Kontrola progu w drugą stronę: 10 m dalej i dziura wypada z raportu.
    # Ta para odróżnia próg 2000 od progu 2020 — bez niej mutacja przechodzi.
    far = {"P": _axis(_line(0.0, 0.0, 100.0, 0.0)),
           "Q": _axis(_line(2110.0, 0.0, 2210.0, 0.0))}
    assert NC.endpoint_gaps(far, NC.DEFAULT_CONFLICT_M) == []


def test_network_axes_exactly_the_corridor_width_apart_share_a_corridor():
    """`PARALLEL_M` jest granicą WŁĄCZNIE — 30,0 m to jeszcze wspólny korytarz.

    Warunek korytarza stoi w dwóch miejscach (dla osi A i dla osi B) i obie mutacje
    `<=` -> `<` przechodziły całą suitę, bo istniejące testy podają 15 m (wyraźnie
    w środku) albo 5000 m (wyraźnie poza). Odległość równa dokładnie progowi jest
    tu dokładna: rzut prostopadły punktu (x, 30) na oś y = 0 daje `hypot(0, 30)`.
    """
    axes = {"P": _axis(_line(0.0, 0.0, 400.0, 0.0)),
            "Q": _axis(_line(0.0, 30.0, 400.0, 30.0))}
    rows = NC.proximity(axes, NC.DEFAULT_CONFLICT_M, NC.PARALLEL_M)
    assert len(rows) == 1, rows
    assert rows[0]["corridor_ranges_a_m"], "korytarz osi A pusty przy odległości równej progowi"
    assert rows[0]["corridor_ranges_b_m"], "korytarz osi B pusty przy odległości równej progowi"
    assert rows[0]["min_distance_m"] == 30.0

    # Kontrola kierunku: 30,5 m i korytarza już nie ma.
    apart = {"P": _axis(_line(0.0, 0.0, 400.0, 0.0)),
             "Q": _axis(_line(0.0, 30.5, 400.0, 30.5))}
    assert NC.proximity(apart, NC.DEFAULT_CONFLICT_M, NC.PARALLEL_M) == []


def test_network_axes_exactly_the_profile_width_apart_are_not_a_conflict():
    """`DEFAULT_CONFLICT_M` jest granicą WYŁĄCZNIE: 9,40 m to jeszcze nie kolizja.

    Próg jest szerokością `box_double`, czyli światłem rury. Dwie osie odległe
    dokładnie o tę szerokość mają rury STYKAJĄCE się, a nie przenikające — i tak
    właśnie odpowiada kod. Obie mutacje `<` -> `<=` (zakresy kolizji i lista
    punktów) przechodziły całą suitę, bo testy podają 15 m albo skrzyżowanie
    pod kątem prostym.
    """
    axes = {"P": _axis(_line(0.0, 0.0, 400.0, 0.0)),
            "Q": _axis(_line(0.0, NC.DEFAULT_CONFLICT_M, 400.0, NC.DEFAULT_CONFLICT_M))}
    row = NC.proximity(axes, NC.DEFAULT_CONFLICT_M, NC.PARALLEL_M)[0]
    assert row["min_distance_m"] == NC.DEFAULT_CONFLICT_M
    assert row["conflict_points"] == 0, row["conflicts"]
    assert row["conflict_ranges_a_m"] == [], row["conflict_ranges_a_m"]

    # Kontrola kierunku: pół metra bliżej i rury się przenikają.
    closer = {"P": _axis(_line(0.0, 0.0, 400.0, 0.0)),
              "Q": _axis(_line(0.0, 8.9, 400.0, 8.9))}
    tight = NC.proximity(closer, NC.DEFAULT_CONFLICT_M, NC.PARALLEL_M)[0]
    assert tight["conflict_points"] > 0 and tight["conflict_ranges_a_m"]


# =============================================================================
# tools/track/station_layout.py — perony
# =============================================================================

def _clothoid(n=120, step=10.0, r0=1000.0, r1=120.0):
    """Łuk o malejącym promieniu — żeby minimum promienia dało się umieścić na krawędzi."""
    points, x, y, angle = [], 0.0, 0.0, 0.0
    for i in range(n + 1):
        points.append((x, y, 0.0))
        radius = r0 + (r1 - r0) * i / n
        angle += step / radius
        x += step * math.cos(angle)
        y += step * math.sin(angle)
    return points


def _straight_axis(chainage_m, length_m=2000.0, step_m=20.0):
    count = int(length_m / step_m) + 1
    return {"id": "T", "points": [[i * step_m, 0.0, 0.0] for i in range(count)],
            "stations": [{"name": "S", "chainage_m": chainage_m}]}


def test_station_platform_edge_sample_belongs_to_the_platform():
    """Łuk leżący DOKŁADNIE na krawędzi peronu liczy się do peronu.

    `radius_within` bierze próbki o kilometrażu z przedziału `[from_m, to_m]`
    obustronnie domkniętego. Obie mutacje `<=` -> `<` przechodziły całą suitę,
    bo kilometraże próbek są ułamkami wynikającymi z zagęszczania osi i żaden
    test nie podał ich jako granic przedziału.

    Granicę konstruujemy z tych samych liczb, które porównuje kod: kilometraż
    próbki z najmniejszym promieniem bierzemy wprost z `radii_along` i podajemy
    raz jako `from_m`, raz jako `to_m`. Równość jest wtedy dokładna z definicji.
    """
    import clearance
    import sweep as sweep_tool

    points = sweep_tool.catmull_rom([tuple(map(float, p)) for p in _clothoid()],
                                    SL.RING_STEP_M)
    chord = clearance.car_chord_m({"length_m": SL.train_length_m(), "cars": 6})
    samples = [(s, r) for s, r in clearance.radii_along(points, chord) if r is not None]
    assert len(samples) > 10, samples
    tightest_s, tightest_r = min(samples, key=lambda pair: pair[1])
    first_s, last_s = samples[0][0], samples[-1][0]
    assert first_s < tightest_s < last_s, "łuk musi mieć minimum w środku zakresu"

    assert SL.radius_within(points, chord, tightest_s, last_s) == tightest_r, \
        "próbka na POCZĄTKU peronu wypadła z zakresu"
    assert SL.radius_within(points, chord, first_s, tightest_s) == tightest_r, \
        "próbka na KOŃCU peronu wypadła z zakresu"
    # Kontrola kierunku: milimetr za krawędzią i ta próbka już nie należy.
    assert SL.radius_within(points, chord, tightest_s + 0.001, last_s) != tightest_r


def test_station_platform_ending_exactly_on_the_tolerance_is_not_clipped():
    """Tolerancja 1e-9 m przy końcu osi jest WYŁĄCZNIE: równo tyle to jeszcze nie przycięcie.

    Konstrukcja: kilometraż stacji liczymy WSTECZ od progu — `(długość osi + 1e-9)
    minus połowa peronu` — a potem asercją sprawdzamy, że dodanie połowy wraca
    dokładnie do progu. Odwrotna kolejność by nie zadziałała: `1e-9` nie jest
    całkowitą wielokrotnością ostatniego bitu liczby rzędu tysiąca metrów, więc
    „dodać nanometr" zwykle znaczy „dodać coś innego niż nanometr".
    """
    import sweep as sweep_tool

    document = _straight_axis(0.0)
    points = sweep_tool.catmull_rom(
        [tuple(float(c) for c in p) for p in document["points"]], SL.RING_STEP_M)
    axis_length_m = sweep_tool.chainages(points)[-1]

    platform_length_m = 94.0
    edge = axis_length_m + 1e-9
    centre = edge - platform_length_m / 2.0
    assert centre + platform_length_m / 2.0 == edge, "konstrukcja granicy przestała być dokładna"

    report = SL.layout(_straight_axis(centre), platform_length_m)
    platform = report["platforms"][0]
    assert platform["clipped_at_end"] is False, platform
    # Kontrola kierunku: milimetr dalej i peron jest przycięty.
    later = SL.layout(_straight_axis(centre + 0.001), platform_length_m)
    assert later["platforms"][0]["clipped_at_end"] is True


def test_station_platform_exactly_at_the_footprint_tolerance_still_fits():
    """`within_footprint` też ma tolerancję WŁĄCZNIE — nanometr ponad obrys jeszcze wchodzi.

    Konstrukcja granicy: obrys ustawiamy na `długość peronu - 1e-9` i asercją
    sprawdzamy, że dodanie tolerancji wraca dokładnie do długości peronu. Długość
    peronu jest tu zaokrąglona do milimetra (`round(..., 3)`), więc ostatni bit
    jest przewidywalny — dla dowolnej liczby ta sztuczka by nie przeszła.
    """
    plain = SL.layout(_straight_axis(500.0), 94.0, footprint_m=200.0)
    length_m = plain["platforms"][0]["length_m"]
    footprint = length_m - 1e-9
    assert footprint + 1e-9 == length_m, "konstrukcja granicy przestała być dokładna"

    tight = SL.layout(_straight_axis(500.0), 94.0, footprint_m=footprint)
    assert tight["platforms"][0]["within_footprint"] is True, tight["platforms"][0]
    # Kontrola kierunku: milimetr za mało obrysu i peron się nie mieści.
    short = SL.layout(_straight_axis(500.0), 94.0, footprint_m=length_m - 0.001)
    assert short["platforms"][0]["within_footprint"] is False


# =============================================================================
# tools/data/provenance.py — walidacja pobranych ładunków i różnice manifestów
# =============================================================================

def test_provenance_json_payload_is_actually_parsed():
    """Gałąź `json` ma sprawdzać JSON — i tylko JSON.

    Mutacja `==` -> `!=` przechodziła całą suitę: żaden test nie podawał ZEPSUTEGO
    JSON-a, a przy odwróconym warunku gałąź w ogóle się nie odpala i uszkodzony
    ładunek przechodzi jako dobry. Druga asercja pilnuje drugiej strony: CSV nie
    ma być parsowany jako JSON.
    """
    PROV.validate_payload(b'{"x": 1}', "json")
    try:
        PROV.validate_payload(b"{ to nie jest json", "json")
    except PROV.ProvenanceError:
        pass
    else:
        raise AssertionError("uszkodzony JSON przeszedł walidację")
    PROV.validate_payload(b"a,b\n1,2\n", "csv")


def test_provenance_pbf_of_exactly_eight_bytes_is_accepted():
    """Próg PBF brzmi „krótszy niż 8 bajtów", a nie „nie dłuższy niż 8".

    Nagłówek PBF to czterobajtowa długość i początek bloku, więc osiem bajtów to
    najmniejszy ładunek, który jeszcze może być prawdziwy. Ani mutacja operatora,
    ani mutacja progu `8` -> `9` nie miały testu, bo żaden nie podawał ładunku
    o długości dokładnie ośmiu bajtów. Długość jest liczbą całkowitą, więc granica
    jest tu dokładna bez żadnych sztuczek.
    """
    PROV.validate_payload(b"\x00\x00\x00\rOSMH", "pbf")
    try:
        PROV.validate_payload(b"\x00\x00\x00\rOSM", "pbf")
    except PROV.ProvenanceError:
        pass
    else:
        raise AssertionError("siedmiobajtowy ładunek PBF przeszedł walidację")


def test_provenance_diff_says_the_url_did_not_change_when_it_did_not():
    """`url_changed` ma znaczyć „adres się zmienił", a nie „adres jest ten sam".

    `content_sha256` i lista `changes` mają testy, `final_url` nie miał — mutacja
    `!=` -> `==` przechodziła całą suitę. To jest pole, po którym poznaje się
    przekierowanie źródła pod inny adres, więc odwrócone znaczy „każde pobranie
    z tego samego URL-a wygląda jak przeniesione".
    """
    common = dict(source_id="stib_gtfs", requested_url="https://example.test/a.json",
                  final_url="https://example.test/a.json",
                  retrieved_at="2026-09-01T00:00:00Z", data_format="json")
    same = PROV.build_manifest(content=b'{"x":1}', **common)
    other = PROV.build_manifest(content=b'{"x":2}', **common)
    assert PROV.diff_manifests(same, other)["url_changed"] is False

    moved = PROV.build_manifest(content=b'{"x":1}',
                                **dict(common, final_url="https://example.test/b.json"))
    assert PROV.diff_manifests(same, moved)["url_changed"] is True


# =============================================================================
# tools/track/data_freshness.py — okna ważności danych
# =============================================================================

def _freshness_rows(payload, today):
    with tempfile.TemporaryDirectory() as directory:
        os.makedirs(os.path.join(directory, "data"), exist_ok=True)
        with open(os.path.join(directory, "data", "a.json"), "w", encoding="utf-8") as handle:
            json.dump(payload, handle)
        return DF.audit(DF.data_files(directory), today)


def test_freshness_a_window_closing_today_is_not_yet_expired():
    """Dzień wygaśnięcia jest jeszcze WAŻNY — okno kończy się z jego końcem.

    Istniejące testy podają −4 dni i +19 dni, więc próg `days < 0` przechodzi
    zarówno z `<`, jak i z `<=`, i zarówno z zerem, jak i z jedynką. Zero dni to
    jedyne wejście, które je rozróżnia. Liczba dni jest tu całkowita, więc granica
    jest dokładna bez sztuczek.
    """
    today = datetime.date(2026, 9, 1)
    rows = _freshness_rows({"validity": {"valid_to": today.isoformat()}}, today)
    assert rows[0]["days_left"] == 0
    assert rows[0]["status"] == "kończy się", rows[0]
    # Kontrola kierunku: dzień później i okno jest przeterminowane.
    later = _freshness_rows({"validity": {"valid_to": today.isoformat()}},
                            today + datetime.timedelta(days=1))
    assert later[0]["status"] == "przeterminowane"


def test_freshness_warning_window_includes_its_last_day():
    """`WARN_DAYS` to granica WŁĄCZNIE: dokładnie 30 dni to jeszcze „kończy się"."""
    today = datetime.date(2026, 9, 1)
    end = today + datetime.timedelta(days=DF.WARN_DAYS)
    rows = _freshness_rows({"validity": {"valid_to": end.isoformat()}}, today)
    assert rows[0]["days_left"] == DF.WARN_DAYS
    assert rows[0]["status"] == "kończy się", rows[0]
    # Kontrola kierunku: dzień dalej i okno jest po prostu aktualne.
    rows = _freshness_rows(
        {"validity": {"valid_to": (end + datetime.timedelta(days=1)).isoformat()}}, today)
    assert rows[0]["status"] == "aktualne"


def test_freshness_data_fetched_on_the_last_valid_day_is_not_fetched_after_expiry():
    """Pobranie W DNIU wygaśnięcia to jeszcze nie pobranie PO wygaśnięciu.

    To jest ostrzeżenie z `sources.json` — archiwum bywa nieważne już w chwili
    pobrania — i jedyna rzecz, która je odróżnia od pobrania na styk, to data
    równa dacie końca okna. Istniejące testy mają pobranie 4 dni po i pobranie
    bez daty; żadne nie stoi na granicy.
    """
    today = datetime.date(2026, 9, 1)
    end = datetime.date(2026, 9, 20)
    rows = _freshness_rows({"validity": {"valid_to": end.isoformat()},
                            "retrieved_at": end.isoformat() + "T10:00:00Z"}, today)
    assert rows[0]["retrieved_after_expiry"] is False, rows[0]
    # Kontrola kierunku: dzień po i ostrzeżenie się zapala.
    rows = _freshness_rows(
        {"validity": {"valid_to": end.isoformat()},
         "retrieved_at": (end + datetime.timedelta(days=1)).isoformat() + "T10:00:00Z"}, today)
    assert rows[0]["retrieved_after_expiry"] is True
