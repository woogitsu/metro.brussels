#!/usr/bin/env python3
"""Testy `tools/blender/station_kit.py` — przekroju peronu liczonego bez Blendera.

**Dlaczego to nie może zostać na renderach.** Bramka wizualna T-211 pokazuje płytę
peronu i nic poza tym: pas ostrzegawczy jest wyniesiony 1 mm nad płytę, a kadr
obejmuje 94 m, więc pas ma **poniżej jednego piksela**. Obejrzałem trzy rendery
kontrolne i po nich nie dało się orzec, czy pas w ogóle powstał, ani gdzie leży —
liczby niżej odpowiadają na to, czego obraz w tej skali nie pokaże.

To jest ta sama konwencja co w `test_blender_cli.py`: atrapa `bpy` wpuszcza import,
a testowane są wyłącznie funkcje liczące bez silnika. Zamiatanie i eksport GLB
weryfikuje Blender w CI.
"""
import os
import sys
import types

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "blender"))

if "bpy" not in sys.modules:
    _bpy = types.ModuleType("bpy")
    _bpy.ops = types.SimpleNamespace()
    _bpy.data = types.SimpleNamespace(objects=[], meshes=None)
    _bpy.context = types.SimpleNamespace()
    sys.modules["bpy"] = _bpy

import profiles  # noqa: E402
import station_kit as SK  # noqa: E402

#: Wartości z rzeczywistego przebiegu na Gare Centrale — najciaśniejszym peronie
#: pakietu A (największa strzałka cięciwy, więc największe minimalne odsunięcie).
GC_MINIMUM_M = 1.5748
GC_HEIGHT_M = 1.03
GAP_M = 0.08


def _station():
    return SK.wall_offset_m("station"), max(profiles.PROFILES["station"]["track_offsets"])


def test_wall_offset_is_the_widest_point_of_the_profile():
    """Ściana komory to najdalszy punkt profilu, nie pierwszy z brzegu.

    Pętla po WSZYSTKICH profilach jest tu celowa i to ona znalazła błąd:
    `bore_single` nie ma klucza `points` (opisuje się promieniem i środkiem),
    a `--profile` przyjmuje każdy profil z rejestru. Wersja czytająca klucz
    wprost wywracała się gołym `KeyError`.
    """
    assert len(profiles.PROFILES) >= 3, "kontrola: pętla ma po czym iść"
    for name in profiles.PROFILES:
        widest = max(abs(x) for x, _z in profiles.profile_points(name))
        assert SK.wall_offset_m(name) == widest, name


def test_wall_offset_works_for_a_round_profile_that_has_no_point_list():
    """Kontrola punktowa tego samego błędu — żeby nie zniknął z pętli wyżej."""
    assert "points" not in profiles.PROFILES["bore_single"]
    assert SK.wall_offset_m("bore_single") > 0.0


def test_platform_edge_sits_at_the_minimum_plus_the_declared_gap():
    """Cała pierwsza połowa T-211 wchodzi tutaj przez JEDNĄ liczbę.

    `minimum_edge_offset_m` to pół szerokości M7 plus strzałka cięciwy członu na
    lokalnym promieniu — policzone przez `tools/track/station_layout.py`, bez ani
    jednej decyzji projektowej. Krawędź peronu ma leżeć dokładnie o zadaną
    szczelinę dalej. Gdyby ten test zniknął, peron mógłby stanąć w skrajni pojazdu
    i żaden render tego nie pokaże — 8 cm na 94 m to grubość kreski.
    """
    wall_m, track_m = _station()
    slab, _strip = SK.slab_sections(GAP_M, GC_MINIMUM_M, wall_m, GC_HEIGHT_M, track_m, 1.0)
    inner = min(y for y, _z in slab)
    assert abs(inner - (track_m + GC_MINIMUM_M + GAP_M)) < 1e-9, inner


def test_platform_stops_short_of_the_chamber_wall():
    """Płyta nie może dotykać ściany — siatka wchodziłaby w siatkę."""
    wall_m, track_m = _station()
    slab, _strip = SK.slab_sections(GAP_M, GC_MINIMUM_M, wall_m, GC_HEIGHT_M, track_m, 1.0)
    outer = max(y for y, _z in slab)
    assert abs(outer - (wall_m - SK.DESIGN_WALL_SETBACK_M)) < 1e-9, outer
    assert outer < wall_m, (outer, wall_m)


def test_slab_runs_from_the_rail_head_to_the_platform_height():
    """Peron jest pełny od główki szyny w górę — ZAŁOŻENIE 4, wprost w geometrii."""
    wall_m, track_m = _station()
    slab, _strip = SK.slab_sections(GAP_M, GC_MINIMUM_M, wall_m, GC_HEIGHT_M, track_m, 1.0)
    zs = [z for _y, z in slab]
    assert SK.DESIGN_SOLID_FROM_RAIL_HEAD is True
    assert min(zs) == 0.0 and abs(max(zs) - GC_HEIGHT_M) < 1e-9, zs


def test_warning_strip_starts_at_the_edge_and_never_leaves_the_slab():
    """Pas ostrzegawczy ma sens tylko przy krawędzi i tylko NA płycie.

    Render tego nie rozstrzygnie — pas ma 1 mm wysokości na 94 m długości.
    """
    wall_m, track_m = _station()
    slab, strip = SK.slab_sections(GAP_M, GC_MINIMUM_M, wall_m, GC_HEIGHT_M, track_m, 1.0)
    slab_lo, slab_hi = min(y for y, _z in slab), max(y for y, _z in slab)
    strip_lo, strip_hi = min(y for y, _z in strip), max(y for y, _z in strip)
    assert abs(strip_lo - slab_lo) < 1e-9, "pas nie zaczyna się przy krawędzi peronu"
    assert strip_hi <= slab_hi + 1e-9, "pas wychodzi poza płytę"
    assert abs((strip_hi - strip_lo) - SK.DESIGN_EDGE_STRIP_M) < 1e-9, (strip_lo, strip_hi)


def test_warning_strip_is_clipped_when_the_platform_is_narrower_than_it():
    """Wąski peron nie daje pasa szerszego od siebie.

    Bez przycięcia pas wystawałby w powietrze za płytą, a że leży 1 mm nad nią,
    na renderze wyglądałby identycznie jak pas poprawny.
    """
    wall_m, track_m = _station()
    narrow_wall_m = track_m + GC_MINIMUM_M + GAP_M + SK.DESIGN_WALL_SETBACK_M + 0.25
    slab, strip = SK.slab_sections(GAP_M, GC_MINIMUM_M, narrow_wall_m, GC_HEIGHT_M,
                                   track_m, 1.0)
    slab_hi = max(y for y, _z in slab)
    strip_hi = max(y for y, _z in strip)
    assert strip_hi <= slab_hi + 1e-9, (strip_hi, slab_hi)
    assert (strip_hi - min(y for y, _z in strip)) < SK.DESIGN_EDGE_STRIP_M
    assert wall_m > narrow_wall_m, "kontrola założenia testu: ten peron ma być węższy"


def test_warning_strip_lies_on_the_slab_not_inside_it():
    """Pas leży NA płycie: spód pasa na wysokości peronu, góra wyżej."""
    wall_m, track_m = _station()
    slab, strip = SK.slab_sections(GAP_M, GC_MINIMUM_M, wall_m, GC_HEIGHT_M, track_m, 1.0)
    top_of_slab = max(z for _y, z in slab)
    assert abs(min(z for _y, z in strip) - top_of_slab) < 1e-9
    assert min(z for _y, z in strip) < max(z for _y, z in strip)


def test_the_two_side_platforms_are_mirror_images():
    """Perony boczne po obu stronach mają być symetryczne względem osi trasy.

    Profil `station` ma tory na ±2,1 m, więc każda asymetria wyniku znaczy, że
    znak `side` przecieka gdzieś do wymiaru, a nie tylko do zwrotu.
    """
    wall_m, track_m = _station()
    right, right_strip = SK.slab_sections(GAP_M, GC_MINIMUM_M, wall_m, GC_HEIGHT_M,
                                          track_m, 1.0)
    left, left_strip = SK.slab_sections(GAP_M, GC_MINIMUM_M, wall_m, GC_HEIGHT_M,
                                        -track_m, -1.0)
    for near, far in ((right, left), (right_strip, left_strip)):
        assert sorted(round(-y, 9) for y, _z in far) == sorted(round(y, 9) for y, _z in near)
        assert [z for _y, z in far] == [z for _y, z in near]


def test_a_wider_gap_moves_the_platform_away_from_the_train():
    """Szczelina jest wymiarem, nie ozdobą — większa cofa krawędź, i tylko ją."""
    wall_m, track_m = _station()
    tight, _ = SK.slab_sections(0.05, GC_MINIMUM_M, wall_m, GC_HEIGHT_M, track_m, 1.0)
    loose, _ = SK.slab_sections(0.15, GC_MINIMUM_M, wall_m, GC_HEIGHT_M, track_m, 1.0)
    assert min(y for y, _z in loose) - min(y for y, _z in tight) - 0.10 < 1e-9
    assert max(y for y, _z in loose) == max(y for y, _z in tight), "ściana się nie ruszyła"


def test_the_gap_has_no_default_because_no_source_gives_it():
    """R-007: szczeliny peron–pudło nie podaje żadne publiczne źródło.

    Wartość domyślna zamieniłaby „nie wiemy" w „przyjęliśmy" bez śladu w danych.
    """
    import contextlib
    import io as _io

    saved = sys.argv
    sys.argv = ["station_kit.py", "--", "--axis", "a", "--layout", "b", "--out", "c"]
    try:
        # argparse wypisuje `usage:` na stderr — bez tego jedyny poprawny wynik
        # tego testu wygląda w logu jak awaria.
        with contextlib.redirect_stderr(_io.StringIO()):
            SK.parse_args()
    except SystemExit:
        pass
    else:
        raise AssertionError("--platform-gap-m nie jest wymagane")
    finally:
        # Bez tego kolejne testy w tym samym procesie dostają cudze argv —
        # `test_all.py` uruchamia wszystko w jednym interpreterze.
        sys.argv = saved

    sys.argv = ["station_kit.py", "--", "--axis", "a", "--layout", "b", "--out", "c",
                "--platform-gap-m", "0.08"]
    try:
        assert SK.parse_args().platform_gap_m == 0.08
    finally:
        sys.argv = saved
