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
import math
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
import placement as PL  # noqa: E402
import station_kit as SK  # noqa: E402
import sweep as SW  # noqa: E402

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


# --- granice przekroju, dotknięte dokładnie ---------------------------------
#
# Dopisane 03.09.2026 po przemiataniu mutacyjnym, które dało dla `station_kit.py`
# 9 mutacji i 8 ocalałych. Naprawą są TESTY, nie ekstrakcja: atrapa `bpy` na górze
# tego pliku wpuszcza import od 02.09.2026, a `slab_sections` i `sweep_section`
# nie dotykają scenki — używają tylko `placement` i `sweep`, które importują się
# bez Blendera. Nie ma czego przenosić; było czego nie sprawdzać.


def test_platform_exactly_as_wide_as_the_chamber_is_refused():
    """Granica `outer > inner` dotknięta DOKŁADNIE: peron zerowej szerokości.

    `assert outer > inner` jest jedyną rzeczą, która nie dopuszcza płyty o zerowej
    albo ujemnej szerokości. Żeby odróżnić `>` od `>=`, trzeba trafić w punkt
    dokładnej równości — a `inner` i `outer` to wyniki dwóch różnych działań
    zmiennoprzecinkowych i „prawie równe" tu nie wystarczy.

    Droga: obie strony sprowadzone do ZERA, bo zero z odejmowania identycznych
    liczb jest dokładne. `inner` = track + (minimum + gap) = −1,0 + (0,5 + 0,5) = 0,0,
    a `outer` = wall − DESIGN_WALL_SETBACK_M, przy `wall` odczytanym z modułu jako
    sam `DESIGN_WALL_SETBACK_M`. Wtedy `inner == outer` bit w bit i porównanie
    jest sprawdzalne. Naiwne `wall = inner + 0.10` NIE działa: `(x + c) - c` nie
    jest równe `x` w arytmetyce zmiennoprzecinkowej.
    """
    inner = -1.0 + (0.5 + 0.5)
    outer = SK.DESIGN_WALL_SETBACK_M - SK.DESIGN_WALL_SETBACK_M
    assert inner == outer == 0.0, (inner, outer)

    try:
        SK.slab_sections(0.5, 0.5, SK.DESIGN_WALL_SETBACK_M, GC_HEIGHT_M, -1.0, 1.0)
    except AssertionError:
        pass
    else:
        raise AssertionError("peron zerowej szerokości przeszedł po prawej stronie")


def test_platform_exactly_as_wide_as_the_chamber_is_refused_on_the_left_side_too():
    """To samo dla `side = -1`, gdzie warunkiem jest `outer < inner`.

    Lewa strona ma osobny assert i osobną mutację, więc potrzebuje osobnego testu.
    Granica jest tu równie dokładna: `outer` wychodzi jako `-0.0`, a `-0.0 == 0.0`
    jest w Pythonie prawdą, więc porównanie stoi w punkcie równości.
    """
    inner = 1.0 + (-1.0) * (0.5 + 0.5)
    outer = (-1.0) * (SK.DESIGN_WALL_SETBACK_M - SK.DESIGN_WALL_SETBACK_M)
    assert inner == outer, (inner, outer)

    try:
        SK.slab_sections(0.5, 0.5, SK.DESIGN_WALL_SETBACK_M, GC_HEIGHT_M, 1.0, -1.0)
    except AssertionError:
        pass
    else:
        raise AssertionError("peron zerowej szerokości przeszedł po lewej stronie")


def test_platform_a_hair_narrower_than_the_chamber_still_passes():
    """Druga strona granicy: peron węższy o jeden bit od komory jeszcze wolno zbudować.

    Bez tego przypadku test wyżej nie odróżniałby `>` od `>=` — sprawdzałby tylko,
    że coś odmawia, a nie GDZIE leży granica.
    """
    wall = math.nextafter(SK.DESIGN_WALL_SETBACK_M, math.inf)
    slab, strip = SK.slab_sections(0.5, 0.5, wall, GC_HEIGHT_M, -1.0, 1.0)
    assert len(slab) == 4 and len(strip) == 4


def _straight_axis(length_m, points):
    step = length_m / (points - 1)
    axis = [(i * step, 0.0, 0.0) for i in range(points)]
    return axis, SW.chainages(axis)


def test_sweep_places_a_ring_at_both_ends_of_the_platform():
    """Pierścienie od `from_m` do `to_m`, z ostatnim dokładnie na końcu."""
    axis, stations = _straight_axis(100.0, 11)
    section = [(-1.0, 0.0), (1.0, 0.0), (1.0, 1.0), (-1.0, 1.0)]
    verts, faces = SK.sweep_section(axis, stations, 0.0, 100.0, section, 25.0)
    assert len(verts) % len(section) == 0
    rings = len(verts) // len(section)
    assert rings == 5, rings          # 0, 25, 50, 75 + domknięcie na 100
    # Denka są dwa, żeby bryła była zamknięta.
    assert len(faces) == (rings - 1) * len(section) + 2, len(faces)


def test_sweep_of_a_span_shorter_than_the_epsilon_makes_a_single_ring():
    """Granica `cursor < to_m - 1e-9` dotknięta DOKŁADNIE.

    `from_m` jest tu ustawione na `to_m - 1e-9`, czyli na sam próg, i to jest
    jedyny sposób, żeby odróżnić `<` od `<=`: przy `<` pętla nie wchodzi ani raz
    i zostaje sam pierścień domykający, przy `<=` wchodzi i pierścieni jest dwa.

    Odejmowanie `to_m - 1e-9` policzone jest RAZ i ta sama liczba idzie jako
    `from_m`, więc obie strony porównania są bit w bit tą samą wartością.
    Gdyby test podał `99.999999999` wpisane z ręki, trafiłby obok.
    """
    axis, stations = _straight_axis(200.0, 5)
    section = [(-1.0, 0.0), (1.0, 0.0), (1.0, 1.0), (-1.0, 1.0)]
    to_m = 100.0
    from_m = to_m - 1e-9
    assert not from_m < to_m - 1e-9, "from_m musi stać dokładnie na progu"

    verts, _ = SK.sweep_section(axis, stations, from_m, to_m, section, 25.0)
    assert len(verts) // len(section) == 1


def test_sweep_step_shorter_than_the_span_adds_rings_in_between():
    """Kontrola, że pierścienie naprawdę zależą od kroku, a nie są stałą."""
    axis, stations = _straight_axis(100.0, 11)
    section = [(-1.0, 0.0), (1.0, 0.0), (1.0, 1.0), (-1.0, 1.0)]
    counts = []
    for step in (50.0, 25.0, 10.0):
        verts, _ = SK.sweep_section(axis, stations, 0.0, 100.0, section, step)
        counts.append(len(verts) // len(section))
    assert counts == sorted(counts) and counts[0] < counts[-1], counts


def test_sweep_forward_fallback_branch_is_dead_not_untested():
    """`index + 1 < len(points)` jest ZAWSZE prawdziwe — gałąź `else` jest martwa.

    To nie jest luka w pokryciu i dlatego ten test nie próbuje jej dosięgnąć,
    tylko PRZYPINA powód. `placement.frame_at` przycina indeks do `len - 2`, więc
    `index + 1` nigdy nie osiąga `len(points)`. Zmierzone, nie wyczytane: 24 000
    wywołań `frame_at` na 6000 losowych osiach (od jednego do ośmiu punktów,
    z duplikatami i z segmentami po 0,5 mm), chainage celowo często równy stacji.

        trafień DOKŁADNIE w granicę index+1==len: 0
        najmniejsze zaobserwowane len-(index+1):  1

    Dlatego mutacja `<` -> `<=` w tym miejscu jest równoważna: warunek jest
    prawdziwy po obu stronach. Zdejmowanie tej gałęzi to zmiana kodu produkcyjnego
    i decyzja właściciela, nie zakres dopisywania testów — ten test pilnuje
    niezmiennika, na którym ta decyzja się opiera.
    """
    for count in (1, 2, 3, 8, 447):
        axis = [(float(i), 0.0, 0.0) for i in range(count)]
        stations = SW.chainages(axis)
        for chainage in (stations[0], stations[-1], stations[-1] / 2.0):
            _, index, _ = PL.frame_at(axis, stations, chainage)
            assert index + 1 < len(axis), (count, chainage, index)


# --- dwie decyzje wyjęte z main() -------------------------------------------


def _platforms():
    return [{"name": "De Brouckère"}, {"name": "Arts-Loi"}, {"name": "Arts"}]


def test_only_station_empty_means_every_platform():
    """Brak `--only-station` to WSZYSTKIE perony, nie żaden.

    Mutacja `if not only_station` na `if only_station` zbudowałaby pustą listę
    i job padłby na „nie zbudowano ani jednej bryły" — czyli na komunikacie
    sugerującym błąd wołającego, a nie błąd filtru.
    """
    assert len(SK.selected_platforms(_platforms(), None)) == 3
    assert len(SK.selected_platforms(_platforms(), "")) == 3


def test_only_station_matches_the_whole_name_not_a_fragment():
    """Dopasowanie po fragmencie byłoby gorsze niż brak filtru.

    „Arts" musi trafić w „Arts", a nie w „Arts-Loi" — inaczej `--only-station Arts`
    budowałby dwa perony i nikt by nie zauważył, bo oba są poprawne.
    """
    got = SK.selected_platforms(_platforms(), "Arts")
    assert [p["name"] for p in got] == ["Arts"], got


def test_only_station_with_a_typo_gives_an_empty_list():
    """Pusta lista jest właściwą odpowiedzią — `main()` zamienia ją w odmowę."""
    assert SK.selected_platforms(_platforms(), "Arts-Loi ") == []
    assert SK.selected_platforms(_platforms(), "arts-loi") == []


def test_side_tag_maps_the_sign_to_the_name():
    assert SK.side_tag(1.0) == "R"
    assert SK.side_tag(-1.0) == "L"


def test_side_tag_of_zero_is_refused_instead_of_guessing_left():
    """Zero nie jest stroną. Granica `side > 0` jest tu całkowita, więc dokładna.

    Poprzednia wersja tego kodu, `"R" if side > 0 else "L"`, odpowiadała na zero
    „L" po cichu. Mutacja `>` -> `>=` odpowiadałaby „R" — i to jest dokładnie ten
    rodzaj pomyłki, którego żadna kontrola geometryczna nie widzi: bryły powstają
    poprawne, tylko peron prawy nazywa się lewym.
    """
    for bad in (0.0, -0.0):
        try:
            SK.side_tag(bad)
        except ValueError as err:
            assert "nie zero" in str(err), err
        else:
            raise AssertionError(f"side_tag({bad!r}) nie odmówiło")
