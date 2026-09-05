#!/usr/bin/env python3
"""Testy generatora syntetycznej osi (`tools/track/make_test_track.py`).

**Dlaczego ten plik powstał.** Moduł był w repo jedynym osiągalnym dla zestawu
testów, którego ANI JEDEN test nie sprawdzał — `test_all.py` importował go
wyłącznie po to, żeby wyprodukować wejście dla walidatora:

    def test_validator_accepts_good_track():
        p=_tmp(M.build(False)); r=V.validate(p); os.unlink(p); assert r.ok(),r.err

    def test_validator_rejects_broken_track():
        p=_tmp(M.build(True)); r=V.validate(p); os.unlink(p); assert not r.ok() and len(r.err)>=3

Wyrocznią jest tam walidator, a `make_test_track` jest oprzyrządowaniem. Taki układ
mówi „przeszło", ale nie mówi, **co** zostało zepsute — a to jest jedyne, do czego
`--broken` służy. Zmierzone przemiataniem mutacyjnym na `ee84432`:

    python3 tools/tests/mutation_sweep.py --only tools/track/make_test_track.py --workers 4
    [MUTACJE] rozstrzygniętych 2/2, zabitych 0, ocalałych 2, nierozstrzygniętych 0
      OCALAŁA  tools/track/make_test_track.py:19 operator `==` -> `!=`
      OCALAŁA  tools/track/make_test_track.py:19 prog `130` -> `131`

Dwie mutacje na dwie, 100 % ocalałych — najgorszy udział w całym drzewie. Obie
siedzą w jednej linii, tej wstawiającej zapadnięcie niwelety, i obie przechodziły
całą suitę, bo `len(r.err) >= 3` jest prawdą także wtedy, gdy zapadnięte jest
259 punktów zamiast jednego albo gdy zapada się punkt 131 zamiast 130.

Testy niżej pytają więc o coś innego niż „czy walidator to odrzuci": o to, **które
dokładnie punkty** różnią się między osią dobrą a zepsutą i **jakimi liczbami**.
Wszystkie liczby w tym pliku są zmierzone na `ee84432`, nie przepisane ze wzorów.
"""
import json
import math
import os
import sys
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "track"))

import make_test_track as M  # noqa: E402
import validate as V  # noqa: E402

#: Punkt, w którym `--broken` zapada niweletę, i głębokość, na jaką ją zapada.
DIP_INDEX, DIP_Z = 130, -30.0
#: Punkt, który `--broken` odsuwa wzdłuż osi X od swojego poprzednika, i o ile metrów.
JUMP_INDEX, JUMP_M = 200, 60.0
#: Krok i liczba punktów osi dobrej.
POINTS, STEP_M = 260, 8.0


def _report(axis):
    """Walidator na słowniku, bez zapisywania do `data/` (reguła 6 z `CLAUDE.md`)."""
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False,
                                     encoding="utf-8") as handle:
        json.dump(axis, handle, ensure_ascii=False)
        path = handle.name
    try:
        return V.validate(path)
    finally:
        os.unlink(path)


def _gaps(points):
    return [math.dist(points[i][:2], points[i + 1][:2]) for i in range(len(points) - 1)]


# --- oś dobra ------------------------------------------------------------------

def test_make_test_track_good_axis_is_the_shape_the_module_promises():
    """260 punktów co 8 m wzdłuż X, czyli oś długości 2072 m."""
    axis = M.build(False)
    points = axis["points"]
    assert axis["id"] == "TEST", axis["id"]
    assert "crs" in axis, "brak deklaracji układu — walidator ostrzega, a nie ma o czym"
    assert len(points) == POINTS, len(points)
    assert [p[0] for p in points] == [round(i * STEP_M, 3) for i in range(POINTS)]
    assert points[-1][0] == 2072.0, points[-1]


def test_make_test_track_good_axis_geometry_follows_the_two_declared_formulas():
    """Poprzeczka i niweleta są sinusoidami z modułu, a nie tablicą wklejonych liczb.

    Sprawdzane na wszystkich 260 punktach naraz, żeby test padał także wtedy, gdy
    ktoś zmieni jeden punkt „ręcznie" — to jest dokładnie ten rodzaj zmiany, którą
    kontrola po długości osi albo po liczbie punktów przepuszcza.
    """
    points = M.build(False)["points"]
    for index, (x, y, z) in enumerate(points):
        s = index * STEP_M
        assert y == round(120 * math.sin(s / 420.0), 3), (index, y)
        assert z == round(-14.0 - 2.5 * math.sin(s / 330.0) ** 2 * 2, 3), (index, z)


def test_make_test_track_good_axis_stays_well_inside_every_validator_limit():
    """Nie „przeszło", tylko z jakim zapasem — inaczej zaostrzenie progu o włos
    zamieniłoby wzorcowe wejście w wejście graniczne i nikt by tego nie zauważył."""
    points = M.build(False)["points"]
    gaps = _gaps(points)
    # Odstęp jest krokiem 8,0 m wzdłuż X powiększonym o wychylenie poprzeczki, więc
    # minimum leży odrobinę NAD krokiem (8,0000000625 m), a nie na nim.
    assert STEP_M < min(gaps) < STEP_M + 1e-6, repr(min(gaps))
    assert max(gaps) < 8.33, max(gaps)
    assert max(gaps) * 3 < V.LIMITS["max_point_gap_m"], (max(gaps), V.LIMITS)
    depths = [q[2] for q in points]
    # Niweleta jest sinusoidą o amplitudzie 5,0 m pod -14,0 m, więc oba krańce są
    # osiągane DOKŁADNIE — porównanie musi być nieostre albo test padnie na sinusie.
    assert min(depths) == -19.0 and max(depths) == -14.0, (min(depths), max(depths))


def test_make_test_track_good_axis_passes_the_validator_with_no_error_and_no_warning():
    """`test_all.py` pyta tylko o `r.ok()`. Ostrzeżenie też jest sygnałem i tu je widać."""
    report = _report(M.build(False))
    assert report.ok(), report.err
    assert report.warn == [], report.warn


# --- oś zepsuta: DOKŁADNIE dwa uszkodzenia -------------------------------------

def test_make_test_track_broken_axis_differs_from_the_good_one_at_exactly_two_points():
    """Kontrola, której brak trzymał przy życiu obie mutacje z nagłówka.

    `--broken` ma wstawić DWA uszkodzenia w znanych miejscach, a nie „jakieś błędy".
    Mutacja `i == 130` -> `i != 130` zapada 259 punktów z 260 i walidator dalej ją
    odrzuca, więc `len(r.err) >= 3` z `test_all.py` przechodzi. Ta lista indeksów
    nie przechodzi.
    """
    good, broken = M.build(False)["points"], M.build(True)["points"]
    assert len(good) == len(broken) == POINTS
    differing = [i for i, (a, b) in enumerate(zip(good, broken)) if a != b]
    assert differing == [DIP_INDEX, JUMP_INDEX], differing


def test_make_test_track_dip_is_one_point_at_a_known_chainage_and_depth():
    """Zapadnięcie siedzi w punkcie 130 (kilometraż 1040,0 m) i ma dokładnie -30,0 m.

    Mutacja progu `130` -> `131` przesuwa je o jeden punkt i nie zmienia niczego,
    co widzi walidator; tutaj zmienia i kilometraż, i indeks.
    """
    broken = M.build(True)["points"]
    assert broken[DIP_INDEX][2] == DIP_Z, broken[DIP_INDEX]
    assert broken[DIP_INDEX][0] == DIP_INDEX * STEP_M == 1040.0, broken[DIP_INDEX]
    # Poza tym jednym punktem niweleta zepsutej osi jest niweletą osi dobrej.
    elsewhere = [z for i, (_x, _y, z) in enumerate(broken) if i != DIP_INDEX]
    assert min(elsewhere) == -19.0, min(elsewhere)
    assert broken[DIP_INDEX - 1][2] == M.build(False)["points"][DIP_INDEX - 1][2]


def test_make_test_track_dip_moves_only_the_height_not_the_plan():
    """Punkt 130 zostaje na swoim X i Y — inaczej byłoby to jedno uszkodzenie
    udające dwa i nie dałoby się osobno sprawdzić bramki pochylenia."""
    good, broken = M.build(False)["points"], M.build(True)["points"]
    assert broken[DIP_INDEX][:2] == good[DIP_INDEX][:2], (good[DIP_INDEX], broken[DIP_INDEX])


def test_make_test_track_displaced_point_jumps_sixty_metres_along_x_only():
    """Punkt 200 dostaje X poprzednika + 60 m, a jego Y i Z są Y i Z poprzednika."""
    broken = M.build(True)["points"]
    previous, moved = broken[JUMP_INDEX - 1], broken[JUMP_INDEX]
    assert moved[0] == previous[0] + JUMP_M, (previous, moved)
    assert moved[1:] == previous[1:], (previous, moved)
    assert math.dist(previous[:2], moved[:2]) == JUMP_M


def test_make_test_track_broken_axis_has_exactly_two_over_long_gaps():
    """Przeskok w punkcie 200 rozrywa DWA odstępy, nie jeden: 199->200 i 200->201.

    Liczby zmierzone: 60,0 m i 44,1 m przy limicie 25,0 m. Druga z nich jest
    skutkiem ubocznym pierwszej i lepiej, żeby stała zapisana, niż żeby ktoś ją
    kiedyś odkrył jako niespodziankę.
    """
    gaps = _gaps(M.build(True)["points"])
    over = [(i, round(g, 1)) for i, g in enumerate(gaps) if g > V.LIMITS["max_point_gap_m"]]
    assert over == [(JUMP_INDEX - 1, 60.0), (JUMP_INDEX, 44.1)], over


def test_make_test_track_stations_are_untouched_by_the_two_defects():
    """Stacje stoją w punktach 0, 120 i 259 — żadne z uszkodzeń ich nie dotyka.

    Gdyby dotykało, „zepsuta" oś testowałaby przy okazji tablicę stacji i nie dałoby
    się rozdzielić, co odrzuciło walidator.
    """
    assert M.build(True)["stations"] == M.build(False)["stations"]
    assert DIP_INDEX not in (0, 120, 259) and JUMP_INDEX not in (0, 120, 259)


# --- co z tego widzi walidator -------------------------------------------------

def test_make_test_track_broken_axis_is_rejected_for_the_reasons_it_was_built_for():
    """Nie „co najmniej trzy błędy", tylko które. Pięć, i każdy nazwany.

    Piąty — promień 62 m w punkcie 201 — jest skutkiem przeskoku, a nie osobnym
    uszkodzeniem. Stoi tu wypisany, bo inaczej `len(err) == 5` byłoby liczbą bez
    pokrycia w tym, co ten generator deklaruje.
    """
    errors = _report(M.build(True)).err
    assert len(errors) == 5, errors
    joined = "\n".join(errors)
    assert "odstęp punktów 199→200 = 60.0 m" in joined, joined
    assert "odstęp punktów 200→201 = 44.1 m" in joined, joined
    assert "pochylenie 195.19% między punktami 129→130" in joined, joined
    assert "pochylenie 194.99% między punktami 130→131" in joined, joined
    assert "promień łuku 62 m w punkcie 201" in joined, joined


def test_make_test_track_broken_axis_breaks_two_different_validator_rules():
    """Kontrola negatywna do poprzedniego testu: gdyby oba uszkodzenia zapalały tę
    samą regułę, `BROKEN.json` sprawdzałby jedną bramkę, a nie dwie."""
    errors = _report(M.build(True)).err
    assert any(e.startswith("odstęp punktów") for e in errors), errors
    assert any(e.startswith("pochylenie") for e in errors), errors


# --- tablice, które oś niesie poza geometrią -----------------------------------

def test_make_test_track_stations_sit_on_real_points_of_the_axis():
    """Kilometraż i głębokość każdej stacji da się odczytać z listy punktów.

    Bez tego tablica stacji mogłaby się rozjechać z geometrią i nadal przechodzić —
    walidator sprawdza odstępy stacji, nie ich zgodność z niweletą.
    """
    axis = M.build(False)
    points = axis["points"]
    expected = {0: "Stacja A", 120: "Stacja B", 259: "Stacja C"}
    assert [s["name"] for s in axis["stations"]] == list(expected.values())
    for station in axis["stations"]:
        index = round(station["chainage_m"] / STEP_M)
        assert index in expected and expected[index] == station["name"], station
        assert station["chainage_m"] == round(index * STEP_M, 1), station
        assert station["depth_m"] == round(points[index][2], 2), station
        assert station["interpolated"] is True, station
    assert [s["chainage_m"] for s in axis["stations"]] == [0.0, 960.0, 2072.0]


def test_make_test_track_speed_limit_bands_are_ordered_and_contiguous():
    """Pasma prędkości stykają się i nie zachodzą; drugie kończy się 72 m przed
    końcem osi (2000 m wobec 2072 m) i tak jest zapisane, a nie przemilczane."""
    bands = M.build(False)["speed_limits"]
    assert [b["kmh"] for b in bands] == [50, 70], bands
    for earlier, later in zip(bands, bands[1:]):
        assert earlier["to_m"] == later["from_m"], (earlier, later)
    assert bands[0]["from_m"] == 0, bands
    assert bands[-1]["to_m"] == 2000, bands
    assert M.build(False)["points"][-1][0] == 2072.0


def test_make_test_track_default_argument_builds_the_good_axis():
    """`build()` bez argumentu to oś dobra — CLI woła `build(a.broken)`, ale
    `test_all.py` i ten plik wołają `build(False)`, więc domyślna wartość nie ma
    innego świadka."""
    assert M.build() == M.build(False)
