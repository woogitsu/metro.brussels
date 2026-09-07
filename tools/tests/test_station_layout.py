#!/usr/bin/env python3
"""T-211: rozmieszczenie peronów — połowa, która nie ma decyzji projektowych.

Testy pilnują trzech rzeczy, z których każda była w tym repo osobnym błędem
w przeszłości:

1. wysokość peronu jest TĄ SAMĄ liczbą co wysokość podłogi M7, a nie jej kopią;
2. brakująca dana zostaje `None`, a nie zerem (T-011: `braking_distance_m`);
3. przycięcie do końca osi jest zgłaszane, a nie chowane (R-007: `CbtcTestSpan`).
"""
import functools
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "track"))
sys.path.insert(0, os.path.join(ROOT, "tools", "blender"))

import profiles  # noqa: E402
import station_layout as SL  # noqa: E402

AXIS = os.path.join(ROOT, "data", "track", "L1_A.json")


def _axis():
    with open(AXIS, encoding="utf-8") as handle:
        return json.load(handle)


def _straight(stations, length_m=2000.0, step_m=20.0):
    count = int(length_m / step_m) + 1
    return {
        "id": "T",
        "points": [[i * step_m, 0.0, 0.0] for i in range(count)],
        "stations": [{"name": f"S{i}", "chainage_m": c} for i, c in enumerate(stations)],
    }


# --- wysokość: jedna liczba, nie dwie ------------------------------------------


def test_platform_height_is_the_m7_floor_height_from_the_registry():
    """R-007: STIB pisze, że podłoga M7 jest „à hauteur du quai".

    To nie są dwie wielkości, tylko jedna. Gdyby wysokość peronu była osobną stałą,
    dałoby się ją przestawić bez ruszania rejestru — i repo miałoby dwie prawdy.
    """
    height, status = SL.platform_height_m()
    with open(os.path.join(ROOT, "data", "vehicle", "m7-spec.json"), encoding="utf-8") as handle:
        floor = json.load(handle)["parameters"]["floor_height_m"]
    assert height == floor["value"] == 1.03, (height, floor)
    assert status == floor["status"] == "spec"


def test_layout_reports_the_height_with_its_status():
    report = SL.layout(_straight([500.0]), 94.0)
    assert report["platform_height_m"] == 1.03
    assert report["platform_height_status"] == "spec"
    assert report["platforms"][0]["height_m"] == 1.03


def test_profile_station_platform_height_is_not_used_as_the_source():
    """Profil `station` ma 1,05 m — to wysokość podłogi M6, nie M7.

    STIB: „Hauteur du plancher : 1m03 contre 1m05 pour les M6". Symulator jeździ M7
    po liniach 1 i 5, więc 1,05 m opisuje inny pojazd. Ten test nie zmienia profilu —
    pilnuje, żeby rozmieszczenie peronów brało liczbę z rejestru, a nie stamtąd.
    """
    assert profiles.PROFILES["station"]["platform_height_m"] == 1.05
    height, _status = SL.platform_height_m()
    assert height != profiles.PROFILES["station"]["platform_height_m"]


# --- długość: dolna granica z faktu --------------------------------------------


def test_platform_length_defaults_to_the_train_length_which_is_spec():
    assert SL.train_length_m() == 94.0
    report = SL.layout(_straight([500.0]), SL.train_length_m())
    assert report["platform_length_m"] == 94.0
    assert "R-007" in report["platform_length_basis"]


def test_platform_shorter_than_the_train_is_refused():
    """Peron krótszy od składu jest sprzeczny z ruchem — R-007 wyprowadza z tego granicę."""
    try:
        SL.layout(_straight([500.0]), 93.9)
    except SystemExit as error:
        assert "krótszy od składu" in str(error), error
    else:
        raise AssertionError("peron krótszy od składu przeszedł")

    # Dokładnie długość składu jest dozwolona; to jest granica, nie zakaz.
    assert SL.layout(_straight([500.0]), 94.0)["platforms"]


def test_footprint_bound_is_a_check_not_a_dimension():
    """Górna granica z obrysu stacji: peron dłuższy niż bryła jest na pewno błędny."""
    inside = SL.layout(_straight([500.0]), 94.0, footprint_m=109.1)
    assert inside["platforms"][0]["within_footprint"] is True

    outside = SL.layout(_straight([500.0]), 120.0, footprint_m=109.1)
    assert outside["platforms"][0]["within_footprint"] is False


# --- szczelina: brak źródła zostaje None ---------------------------------------


def test_platform_gap_has_no_default_and_stays_none():
    """R-007: szczeliny peron–pudło nie podaje żadne publiczne źródło.

    Zero znaczyłoby „peron dotyka pudła", a nie „nie wiem". Ten sam wzorzec, co
    `braking_distance_m` w T-011.
    """
    report = SL.layout(_straight([500.0]), 94.0)
    assert report["platform_gap_m"] is None
    platform = report["platforms"][0]
    assert platform["edge_offset_m"] is None
    assert platform["minimum_edge_offset_m"] is not None, (
        "dolna granica jest policzalna z geometrii i ma być podana")

    given = SL.layout(_straight([500.0]), 94.0, platform_gap_m=0.08)
    assert given["platforms"][0]["edge_offset_m"] == round(
        platform["minimum_edge_offset_m"] + 0.08, 4)


def test_minimum_edge_offset_is_half_width_plus_the_versine():
    """Na prostej odsunięcie to samo pół szerokości; na łuku rośnie o strzałkę."""
    straight = SL.layout(_straight([500.0]), 94.0)["platforms"][0]
    assert abs(straight["minimum_edge_offset_m"] - profiles.M7_WIDTH_M / 2.0) < 1e-6
    assert straight["versine_m"] == 0.0
    assert straight["min_radius_m"] is None

    curved = SL.layout(_axis(), 94.0)
    on_curve = [p for p in curved["platforms"] if p["min_radius_m"] is not None]
    assert on_curve, "pakiet A ma łuki — brak promienia znaczy, że pomiar nie działa"
    for platform in on_curve:
        assert platform["versine_m"] > 0.0, platform["name"]
        assert platform["minimum_edge_offset_m"] > profiles.M7_WIDTH_M / 2.0, platform["name"]


def test_profile_clearance_boundary_is_wider_than_the_geometric_minimum():
    """`platform_edge_x` z profilu to granica skrajni, nie krawędź peronu.

    Zmierzone: tory na ±2,10 m, krawędzie na ±4,05 m, czyli 1,95 m od toru — a to
    jest 1,35 (pół szerokości M7) + 2 × 0,30 (`CLEARANCE_M`). Szczelina peron–pudło
    wyszłaby **0,600 m**, czyli przepaść. Dolna granica z geometrii jest o połowę
    mniejsza i to ona jest punktem wyjścia dla peronu.
    """
    station = profiles.PROFILES["station"]
    track = max(station["track_offsets"])
    edge = min(e for e in station["platform_edge_x"] if e > track)
    profile_offset = edge - track
    assert abs(profile_offset - (profiles.M7_WIDTH_M / 2.0 + 2.0 * profiles.CLEARANCE_M)) < 1e-9
    assert abs(profile_offset - profiles.M7_WIDTH_M / 2.0 - 0.60) < 1e-9, profile_offset

    worst = max(p["minimum_edge_offset_m"] for p in SL.layout(_axis(), 94.0)["platforms"])
    assert worst < profile_offset, (worst, profile_offset)


# --- przycięcie do osi ----------------------------------------------------------


def test_clipping_at_the_axis_ends_is_reported_not_hidden():
    """Pierwsza i ostatnia stacja pakietu A leżą na końcach osi."""
    report = SL.layout(_axis(), 94.0)
    assert len(report["platforms"]) == 12

    first, last = report["platforms"][0], report["platforms"][-1]
    assert first["clipped_at_start"] is True, first
    assert first["from_m"] == 0.0
    assert last["clipped_at_end"] is True, last
    assert abs(last["to_m"] - report["axis_length_m"]) < 1e-6

    middle = report["platforms"][5]
    assert middle["clipped_at_start"] is False and middle["clipped_at_end"] is False
    assert abs(middle["length_m"] - 94.0) < 1e-6, (
        "peron w środku osi ma mieć pełną długość — inaczej przycięcie jest wszędzie")


def test_platform_is_centred_on_the_station_chainage():
    report = SL.layout(_straight([500.0, 900.0]), 94.0)
    for platform in report["platforms"]:
        centre = (platform["from_m"] + platform["to_m"]) / 2.0
        assert abs(centre - platform["station_chainage_m"]) < 1e-6, platform


def test_report_names_what_it_does_not_model():
    report = SL.layout(_axis(), 94.0)
    joined = " ".join(report["not_modelled"])
    assert "czopów skrętu" in joined, "brak zastrzeżenia o wychyleniu końców składu"
    assert "R-007" in joined, "brak zastrzeżenia o szczelinie bez źródła"


# --- pakiety B–F: to samo narzędzie, inne wejście (6.B1) -------------------------
#
# Do 05.09.2026 `station_layout.py` był uruchamiany wyłącznie na pakiecie A — tak
# w testach, jak w `tools/ci/station_details.sh`. Pięć pozostałych osi leży
# w `data/track/` od T-111 i nikt nigdy nie policzył na nich peronów, więc każdy błąd
# zależny od kształtu osi (ciasny łuk, stacja w punkcie zero, oś krótsza od dwóch
# peronów) był poza zasięgiem CI.
#
# Liczby są porównywane Z RAPORTEM, nie wpisane tutaj drugi raz. Kopia liczb w teście
# starzeje się osobno od raportu — to jest ta sama rodzina rozjazdu, którą
# `test_report_hygiene.py` łapie dla dat i commitów.

import re  # noqa: E402

BF_REPORT = os.path.join(ROOT, "reports", "T-211-stations-BF.md")

#: Sześć osi pakietów A–F. Kolejność jak w `data/track/`, nie jak w raporcie:
#: raport grupuje po literze pakietu, a plik po nazwie osi.
PACKAGE_AXES = ("L1_A", "L1_B", "L2_E", "L5_C", "L5_D", "L6_F")


@functools.lru_cache(maxsize=None)
def _axis_document(axis_id):
    """Plik osi z `data/track/`. Też z pamięcią (6.B30): czytany jest wielokrotnie,
    a `data/` jest tylko do odczytu (`CLAUDE.md` §4.6), więc treść nie ma jak się
    zmienić w trakcie przebiegu."""
    with open(os.path.join(ROOT, "data", "track", f"{axis_id}.json"), encoding="utf-8") as h:
        return json.load(h)


@functools.lru_cache(maxsize=None)
def _layout_for(axis_id):
    """Przebieg narzędzia na prawdziwej osi, z długością peronu z decyzji T-212.

    **Pamięć (6.B30), i nie jest ona założona, tylko zmierzona.** Ta funkcja jest
    wołana z pięciu miejsc, każde w pętli po sześciu osiach, czyli **około trzydziestu**
    pełnych przebiegów `SL.layout` na tych samych sześciu plikach z `data/track/`.
    Kosztowało to **35,1 s** z ~100 s całego zestawu — trzecią część czasu na jeden
    moduł, który liczył to samo trzydzieści razy.

    Pamięć oddaje **ten sam obiekt** każdemu wołającemu, więc test, który by go
    zmodyfikował, psułby następny test w sposób zależny od kolejności — usterka gorsza
    od tych 35 s, bo niewidoczna. Zmierzone, zanim pamięć weszła: sonda zapamiętała
    układ, po **każdym** z 17 testów policzyła odcisk każdego zapamiętanego obiektu
    i porównała z odciskiem z chwili zapamiętania. Testów, które zmutowały strukturę:
    **zero**. Gdyby kiedykolwiek przestało to być prawdą, właściwą odpowiedzią jest
    kopia przy wydaniu albo struktura niezmienna, a nie zdjęcie pamięci — bo wtedy
    wraca trzydzieści przebiegów.
    """
    length, _basis = SL.resolve_platform_length_m("design")
    return SL.layout(_axis_document(axis_id), length)


def _cells(line):
    """Komórki wiersza tabeli markdown, z `\\|` w nazwie stacji zamienionym na `|`."""
    parts = re.split(r"(?<!\\)\|", line.strip())
    return [cell.strip().replace("\\|", "|") for cell in parts[1:-1]]


def _number(text):
    return float(text.replace(" ", "").replace(" ", "").replace(",", "."))


def report_package_rows():
    """Tabela §1 raportu → {oś: {peronów, przyciętych, nazwa, R, strzałka, offset, rozpiętość}}."""
    with open(BF_REPORT, encoding="utf-8") as handle:
        section = handle.read().split("## 1. Sześć pakietów")[1].split("\n## ")[0]
    rows = {}
    for line in section.splitlines():
        if not line.startswith("|"):
            continue
        cells = _cells(line)
        if len(cells) != 10 or not cells[1].startswith("`L"):
            continue
        rows[cells[1].strip("`")] = {
            "platforms": int(cells[3]),
            "clipped": int(cells[4]),
            "name": cells[5],
            "radius_m": _number(cells[6]),
            "versine_m": _number(cells[7]),
            "offset_m": _number(cells[8]),
            "spread_m": _number(cells[9]),
        }
    return rows


def measured_package_rows():
    """To samo, ale policzone teraz z `data/track/` — bez zaglądania do raportu."""
    rows = {}
    for axis_id in PACKAGE_AXES:
        platforms = _layout_for(axis_id)["platforms"]
        worst = max(platforms, key=lambda r: r["minimum_edge_offset_m"])
        best = min(platforms, key=lambda r: r["minimum_edge_offset_m"])
        rows[axis_id] = {
            "platforms": len(platforms),
            "clipped": sum(1 for r in platforms
                           if r["clipped_at_start"] or r["clipped_at_end"]),
            "name": worst["name"],
            "radius_m": round(worst["min_radius_m"], 2),
            "versine_m": round(worst["versine_m"], 4),
            "offset_m": round(worst["minimum_edge_offset_m"], 4),
            "spread_m": round(worst["minimum_edge_offset_m"]
                              - best["minimum_edge_offset_m"], 4),
        }
    return rows


def package_mismatches(reported=None, measured=None):
    """Rozjazdy raportu wobec przebiegu — pusta lista znaczy zgodność."""
    reported = report_package_rows() if reported is None else reported
    measured = measured_package_rows() if measured is None else measured
    problems = []
    if set(reported) != set(measured):
        problems.append(f"raport opisuje osie {sorted(reported)}, "
                        f"a policzone są {sorted(measured)}")
        return problems
    for axis_id in sorted(measured):
        for key, got in measured[axis_id].items():
            want = reported[axis_id][key]
            if got != want:
                problems.append(f"{axis_id}.{key}: przebieg {got}, raport {want}")
    return problems


def test_station_layout_runs_on_every_package_axis_not_only_A():
    """Sześć osi, nie jedna — i każda ma tyle peronów, ile stacji w pliku osi.

    Liczba peronów to jedyne miejsce, gdzie zgubienie stacji jest widoczne bez
    oglądania geometrii: narzędzie nie ma prawa ani pominąć wpisu ze `stations`,
    ani dołożyć peronu, którego w osi nie ma.
    """
    total = 0
    for axis_id in PACKAGE_AXES:
        document = _axis_document(axis_id)
        platforms = _layout_for(axis_id)["platforms"]
        assert len(platforms) == len(document["stations"]), (
            axis_id, len(platforms), len(document["stations"]))
        total += len(platforms)
    assert total == 61, f"sześć pakietów ma dać 61 peronów, policzono {total}"


def test_minimum_edge_offset_holds_the_same_invariant_on_all_six_axes():
    """`minimum_edge_offset_m = pół szerokości M7 + strzałka` — na 61 peronach.

    Ten sam niezmiennik sprawdza wyżej `test_minimum_edge_offset_is_half_width_plus_
    the_versine`, ale na osi SYNTETYCZNEJ o zadanym promieniu. Tutaj wchodzą osie
    prawdziwe, z promieniami od 97,11 m (Trône) do ponad 700 m (Demey) — czyli
    zakres, którego oś testowa nie ćwiczy.
    """
    checked = 0
    for axis_id in PACKAGE_AXES:
        layout = _layout_for(axis_id)
        half = layout["m7_half_width_m"]
        for row in layout["platforms"]:
            assert abs(row["minimum_edge_offset_m"]
                       - (half + row["versine_m"])) < 1e-9, (axis_id, row["name"])
            checked += 1
    assert checked == 61, checked


def test_every_axis_clips_exactly_its_two_terminus_platforms():
    """Perony krańcowe są przycięte na KAŻDEJ osi — to własność danych, nie usterka.

    Oś każdego pakietu zaczyna się i kończy w środku stacji krańcowej (T-111), więc
    peron wyśrodkowany na tym kilometrażu wystaje poza oś dokładnie połową. Test
    pilnuje trzech rzeczy naraz: że przyciętych jest dokładnie dwa, że są to peron
    pierwszy i ostatni, i że przycięcie jest ZGŁOSZONE, a nie ciche skrócenie długości.
    """
    for axis_id in PACKAGE_AXES:
        platforms = _layout_for(axis_id)["platforms"]
        clipped = [i for i, r in enumerate(platforms)
                   if r["clipped_at_start"] or r["clipped_at_end"]]
        assert clipped == [0, len(platforms) - 1], (axis_id, clipped)
        assert platforms[0]["clipped_at_start"] is True, axis_id
        assert platforms[-1]["clipped_at_end"] is True, axis_id
        # Peron przycięty na starcie to dokładnie połowa: oś zaczyna się na kilometrażu
        # stacji, więc zostaje `length/2`. To jest liczba, nie wrażenie.
        assert abs(platforms[0]["length_m"] - 47.5) < 1e-6, platforms[0]["length_m"]
        # …a peron nieprzycięty ma pełne 95,0 m z decyzji T-212.
        middle = [r for r in platforms[1:-1]]
        assert middle, axis_id
        for row in middle:
            assert abs(row["length_m"] - 95.0) < 1e-6, (axis_id, row["name"])


def test_the_BF_report_numbers_are_reproducible_from_the_axes():
    """Raport kontra przebieg — liczba w liczbę, bez tolerancji.

    `reports/T-211-stations-BF.md` §1 podaje dla każdego pakietu najciaśniejszy peron,
    jego promień, strzałkę, odsunięcie i rozpiętość. Wszystkie te liczby dają się
    policzyć z `data/track/`, więc raport nie ma prawa się z nimi rozjechać — a bez
    tej bramki rozjechałby się po cichu przy pierwszej zmianie osi albo narzędzia.
    """
    reported = report_package_rows()
    assert len(reported) == 6, (
        f"parser wyciągnął {len(reported)} wierszy z §1 raportu — mają być sześć osi; "
        "pusta lista znaczy, że przestał trafiać w sekcję albo w kształt tabeli")
    assert not package_mismatches(), package_mismatches()


def test_the_BF_report_check_catches_a_number_that_drifted():
    """Kontrola negatywna wykonana: bez niej porównanie mogłoby czytać samo siebie."""
    reported = report_package_rows()
    measured = measured_package_rows()
    assert not package_mismatches(reported, measured), "punkt wyjścia nie jest czysty"

    # 1. Jedna liczba w raporcie przesunięta o ostatnią cyfrę.
    dryf = {axis: dict(row) for axis, row in reported.items()}
    dryf["L2_E"]["offset_m"] += 0.0001
    problems = package_mismatches(dryf, measured)
    assert len(problems) == 1 and "L2_E.offset_m" in problems[0], problems

    # 2. Zgubiony peron w przebiegu — liczność jest częścią porównania.
    braki = {axis: dict(row) for axis, row in measured.items()}
    braki["L5_D"]["platforms"] -= 1
    assert package_mismatches(reported, braki), "zgubiony peron przeszedł niezauważony"

    # 3. Cała oś zniknięta z raportu — komunikat ma nazwać zbiory, nie milczeć.
    bez_osi = {axis: row for axis, row in reported.items() if axis != "L6_F"}
    problems = package_mismatches(bez_osi, measured)
    assert len(problems) == 1 and "L6_F" in problems[0], problems

    # 4. Kontrola w drugą stronę: parser NAPRAWDĘ czyta nazwy z raportu, razem
    #    z `\|` w nazwie dwujęzycznej. Gdyby zwracał puste napisy, porównanie nazw
    #    byłoby zawsze prawdziwe i punkt 1 nadal by przechodził.
    assert reported["L2_E"]["name"] == "Trône|Troon", reported["L2_E"]["name"]
    assert reported["L5_D"]["name"] == "Demey", reported["L5_D"]["name"]

# 6.D25: uruchomienie tego pliku WPROST idzie ta sama droga, co caly zestaw —
# z licznikiem asercji i z odmowa przy zerze testow. Bez tej gałęzi `python3
# tools/tests/<modul>.py` konczyl sie kodem 0, nie wykonawszy ani jednego testu.
if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))
