#!/usr/bin/env python3
"""Testy `tools/blender/station_sections.py` — modułu wyciągniętego spod `bpy`
w #276 (`reports/bpy-extraction-round-2.md`), na te funkcje, których
`tools/tests/test_station_kit.py` NIE dotyka.

**Czego ten plik świadomie NIE dubluje.** Pięć z sześciu funkcji tego modułu
(`wall_offset_m`, `slab_sections`, `selected_platforms`, `side_tag`,
`sweep_section`) `station_kit.py` przypisuje pod STARE nazwy — `wall_offset_m =
SS.wall_offset_m` i tak dalej — więc to jest DOKŁADNIE ten sam obiekt funkcji,
który `test_station_kit.py` woła jako `SK.wall_offset_m`. Mutacja w ciele tych
funkcji jest widoczna dla tamtego zestawu tak samo, jakby siedziała w tym pliku
pod własną nazwą, i pomiar mutacyjny (patrz `reports/mutation-triage-round-2-modules.md`)
to potwierdza: dziewięć z piętnastu mutacji tego modułu ginie właśnie tam. Ten
plik testuje wyłącznie to, czego tamten zestaw nie rusza:

1. `straight_prism` — jedyna funkcja tego modułu, której `main()` używa, ale
   której nie woła NIC w `tools/tests/`. Zero pośredniego pokrycia.
2. Granicę `side > 0` w `slab_sections` przy `side == 0.0` dokładnie —
   wszystkie istniejące testy wołają ją wyłącznie z `side` równym `1.0`
   albo `-1.0`, nigdy z zerem.
"""
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "blender"))
sys.path.insert(0, os.path.join(ROOT, "tools", "track"))

import station_sections as SS  # noqa: E402
import sweep as SW  # noqa: E402


def _straight_axis(length_m, points):
    step = length_m / (points - 1)
    axis = [(i * step, 0.0, 0.0) for i in range(points)]
    return axis, SW.chainages(axis)


# --- straight_prism ------------------------------------------------------------


def test_straight_prism_puts_one_ring_at_the_start_and_one_at_length_m_away():
    """Dwa pierścienie: jeden w `at_m`, drugi `length_m` DALEJ wzdłuż `forward`
    tej samej ramki — nie wzdłuż łuku, bo bryła jest PROSTA, nie zamiatana.
    """
    axis, stations = _straight_axis(10.0, 11)
    section = [(-1.0, 0.0), (1.0, 0.0), (1.0, 1.0), (-1.0, 1.0)]
    verts, faces = SS.straight_prism(axis, stations, 3.0, 4.0, section)

    assert len(verts) == 2 * len(section)
    near, far = verts[:len(section)], verts[len(section):]
    # Oś jest prosta wzdłuż X: `forward` = (1,0,0), `right` = (0,-1,0) (z
    # `cross(forward, UP_WORLD)`), więc pierwszy pierścień stoi w x=3, drugi
    # dokładnie `length_m`=4 dalej, w x=7 — obie wartości z chainage, nie z
    # przybliżenia.
    assert {round(x, 9) for x, _y, _z in near} == {3.0}
    assert {round(x, 9) for x, _y, _z in far} == {7.0}


def test_straight_prism_is_closed_with_two_caps():
    """Bez denek render `_inside` pokazywałby wnętrze — ta sama zasada co
    w `sweep_section` (patrz jego docstring i test w `test_station_kit.py`).
    """
    axis, stations = _straight_axis(10.0, 11)
    section = [(-1.0, 0.0), (1.0, 0.0), (1.0, 1.0), (-1.0, 1.0)]
    verts, faces = SS.straight_prism(axis, stations, 0.0, 2.0, section)
    width = len(section)
    # Ściany boczne (jeden pas, bo dwa pierścienie) plus dwa denka.
    assert len(faces) == width + 2


def test_straight_prism_at_a_zero_length_collapses_the_two_rings_onto_each_other():
    """Nie granica bramkowana — `length_m` nie ma tu żadnej asercji na
    dodatniość — ale warto przypiąć, że zerowa długość NIE podnosi wyjątku,
    tylko daje zdegenerowaną bryłę (oba pierścienie w tym samym miejscu).
    """
    axis, stations = _straight_axis(10.0, 11)
    section = [(-1.0, 0.0), (1.0, 0.0), (1.0, 1.0), (-1.0, 1.0)]
    verts, _faces = SS.straight_prism(axis, stations, 5.0, 0.0, section)
    near, far = verts[:len(section)], verts[len(section):]
    assert near == far


# --- granica `side > 0` w slab_sections, przy side == 0.0 dokładnie -----------


def test_slab_sections_at_side_zero_takes_the_negative_branch_without_raising():
    """`side == 0.0` nie jest wołane przez ŻADEN dzisiejszy pipeline — perony
    stoją po `+1` albo `-1` — ale funkcja sama nie odmawia zera (w
    przeciwieństwie do `side_tag`, które robi to wprost), więc `side > 0`
    naprawdę rozstrzyga o gałęzi także w tym punkcie.

    Przy `side = 0.0`: `inner = track_offset_m` (drugi składnik znika),
    `outer = 0.0` (iloczyn przez zero). Warunek `side > 0` jest FAŁSZEM, więc
    droga idzie przez `assert outer < inner` — i to jest jedyny test w całym
    zestawie, który w ogóle dotyka tej gałęzi z niezerowym `track_offset_m`
    z tej strony granicy.

    Mutacja `>` -> `>=` zmienia to na PRAWDĘ przy zerze i przerzuca wykonanie
    na gałąź `assert outer > inner`, czyli `0.0 > track_offset_m` — fałsz dla
    dodatniego `track_offset_m`, więc mutant PODNOSI `AssertionError` tam,
    gdzie oryginał cicho zwraca poprawny przekrój.
    """
    slab, strip = SS.slab_sections(0.5, 0.5, 10.0, 1.0, 1.0, 0.0)
    inner, outer = 1.0, 0.0
    assert [y for y, _z in slab] == [inner, outer, outer, inner]
    assert min(z for _y, z in slab) == 0.0 and max(z for _y, z in slab) == 1.0
    # Sam pas: `strip_far = max(outer, inner - DESIGN_EDGE_STRIP_M)`, gałąź
    # ujemnej strony — potwierdza, że poszło przez `else`, nie przez `if`.
    strip_far = max(outer, inner - SS.DESIGN_EDGE_STRIP_M)
    assert min(y for y, _z in strip) == strip_far
