#!/usr/bin/env python3
"""Testy decyzji renderu kontrolnego (`tools/visual/capture_plan.py`).

Powód ten sam co przy `test_tunnel_manifest.py`, `test_m7_report.py`,
`test_profile_scan.py` i `test_glb_report.py`: przemiatanie mutacyjne
z 03.09.2026 dało dla `capture_blender.py` 10 mutacji i 10 ocalałych. Moduł
importuje `bpy` ORAZ `mathutils`, a decyzje leżały wewnątrz funkcji, które
dotykają scenki.

Poza zasięgiem była między innymi bramka EEVEE — ta, której brak kosztował dwie
czerwone bramki `tunnel-alignment` przy przenosinach CI. Ten plik ją przypina.

Kadrowania ten plik nie sprawdza; od niego jest `test_framing.py`.
"""
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "visual"))

import capture_plan as CP  # noqa: E402


# --- która generacja EEVEE ---------------------------------------------------

def test_eevee_generation_boundary_belongs_to_next():
    """4.2.0 to PIERWSZA wersja z nowym silnikiem, więc granica jest 'next'.

    Granica jest tu dotykalna DOKŁADNIE, bo wersja jest krotką liczb całkowitych —
    żadnego zaokrąglenia, żadnej reprezentacji binarnej. To odróżnia `>=` od `>`,
    czego mutacja `>=` -> `>` w oryginale nie musiała się bać.
    """
    assert CP.eevee_generation((4, 2, 0)) == "next"
    assert CP.eevee_generation(CP.EEVEE_NEXT_SINCE) == "next"


def test_eevee_generation_just_below_the_boundary_is_legacy():
    assert CP.eevee_generation((4, 1, 99)) == "legacy"
    assert CP.eevee_generation((4, 0, 2)) == "legacy", "Blender z apt, ten w CI"


def test_eevee_generation_recognises_the_versions_this_project_actually_uses():
    """Dwie wersje, na których projekt realnie chodzi — 4.0.2 z apt i 5.2.1 LTS."""
    assert CP.eevee_generation((4, 0, 2)) == "legacy"
    assert CP.eevee_generation((5, 2, 1)) == "next"


def test_eevee_generation_accepts_any_sequence_not_only_a_tuple():
    """`bpy.app.version` jest krotką, ale test i CI podają czasem listę."""
    assert CP.eevee_generation([5, 2, 1]) == "next"


# --- bramka EEVEE ------------------------------------------------------------

def test_eevee_conflict_is_silent_when_the_generations_agree():
    assert CP.eevee_conflict("next", "next", "5.2.1") is None
    assert CP.eevee_conflict("legacy", "legacy", "4.0.2") is None


def test_eevee_conflict_refuses_when_the_generations_differ():
    """To jest ta bramka, której brak dał dwie czerwone `tunnel-alignment`."""
    message = CP.eevee_conflict("next", "legacy", "4.0.2")
    assert message is not None
    assert "'next'" in message and "'legacy'" in message and "4.0.2" in message
    assert "EEVEE_NEXT_SINCE" in message, "komunikat ma kierować do stałej z powodem"


def test_eevee_conflict_refuses_in_both_directions():
    """Baseline legacy na nowym Blenderze jest równie nieporównywalny."""
    assert CP.eevee_conflict("legacy", "next", "5.2.1") is not None


def test_eevee_conflict_treats_a_missing_declaration_as_consent():
    """Manifest bez `eevee_generation` znaczy „nie deklaruję", nie „konflikt".

    Mutacja `if not expected` na `if expected` zablokowałaby każdy render
    z manifestu, który tego pola nie ma.
    """
    assert CP.eevee_conflict(None, "next", "5.2.1") is None
    assert CP.eevee_conflict("", "legacy", "4.0.2") is None


# --- czyj to zestaw ujęć -----------------------------------------------------

def test_renderer_conflict_lets_blender_sets_through():
    assert CP.renderer_conflict("vehicle", "blender") is None


def test_renderer_conflict_refuses_a_godot_set_by_name():
    """Bez tej odmowy Blender wygenerowałby klatki domyślną kamerą i nikt by nie zauważył."""
    message = CP.renderer_conflict("godot", "godot")
    assert message is not None
    assert "godot" in message and "nie ma czego renderować" in message


def test_renderer_conflict_refuses_every_non_blender_value_not_just_godot():
    """Mutacja `!=` -> `==` przepuściłaby wszystko poza Blenderem. Tu pada każdy obcy."""
    for renderer in ("godot", "unity", "", "BLENDER", "blender2"):
        assert CP.renderer_conflict("x", renderer) is not None, renderer


# --- kotwice -----------------------------------------------------------------

def test_anchors_parse_name_and_three_coordinates():
    got = CP.parse_anchors(["axis05_eye=1.0,2.0,3.5"])
    assert got == {"axis05_eye": [1.0, 2.0, 3.5]}


def test_anchors_keep_every_entry_not_only_the_last():
    got = CP.parse_anchors(["a=1,0,0", "b=0,1,0", "c=0,0,1"])
    assert sorted(got) == ["a", "b", "c"]
    assert got["b"] == [0.0, 1.0, 0.0]


def test_anchors_without_an_equals_sign_are_refused_by_name():
    try:
        CP.parse_anchors(["axis05_eye 1,2,3"])
    except ValueError as err:
        assert "nazwa=X,Y,Z" in str(err)
    else:
        raise AssertionError("kotwica bez `=` przeszła")


def test_anchors_with_the_wrong_number_of_coordinates_are_refused():
    """Granica dotknięta z obu stron: trzy przechodzą, dwie i cztery nie.

    Odróżnia `!= 3` od `< 3` i od `> 3`. Sama liczba współrzędnych jest liczbą
    całkowitą, więc granica jest dokładna bez żadnych zabiegów.
    """
    assert CP.parse_anchors(["a=1,2,3"]) == {"a": [1.0, 2.0, 3.0]}
    for bad in ("a=1,2", "a=1,2,3,4", "a=1"):
        try:
            CP.parse_anchors([bad])
        except ValueError as err:
            assert "trzy współrzędne" in str(err), (bad, err)
        else:
            raise AssertionError(f"kotwica {bad} przeszła")


def test_anchors_strip_whitespace_around_the_name():
    assert CP.parse_anchors([" a =1,2,3"]) == {"a": [1.0, 2.0, 3.0]}


def test_anchors_of_nothing_is_an_empty_mapping_not_an_error():
    assert CP.parse_anchors([]) == {}
    assert CP.parse_anchors(None) == {}


def test_anchor_coordinates_may_be_negative_and_fractional():
    """Kotwice przychodzą w Lambercie 72 i bywają ujemne — to nie jest błąd."""
    got = CP.parse_anchors(["s=-1.5,2084.8404,-20.25"])
    assert got["s"] == [-1.5, 2084.8404, -20.25]


# --- punkt na osi ------------------------------------------------------------

def _axis():
    return [(0.0, 0.0, 0.0), (10.0, 0.0, 0.0), (10.0, 10.0, 0.0)]


def _stations():
    return [0.0, 10.0, 20.0]


def test_point_at_chainage_hits_the_vertices_exactly():
    """Chainage RÓWNY stacji trafia w wierzchołek. To granica `<=` z lewej strony."""
    assert CP.point_at_chainage(_axis(), _stations(), 0.0) == (0.0, 0.0, 0.0)
    assert CP.point_at_chainage(_axis(), _stations(), 10.0) == (10.0, 0.0, 0.0)
    assert CP.point_at_chainage(_axis(), _stations(), 20.0) == (10.0, 10.0, 0.0)


def test_point_at_chainage_interpolates_inside_a_segment():
    assert CP.point_at_chainage(_axis(), _stations(), 5.0) == (5.0, 0.0, 0.0)
    assert CP.point_at_chainage(_axis(), _stations(), 15.0) == (10.0, 5.0, 0.0)


def test_point_at_chainage_clamps_outside_the_axis_instead_of_failing():
    """Kotwica z zewnątrz ma prawo minąć koniec chunka; sensowną odpowiedzią jest koniec."""
    assert CP.point_at_chainage(_axis(), _stations(), -100.0) == (0.0, 0.0, 0.0)
    assert CP.point_at_chainage(_axis(), _stations(), 1e6) == (10.0, 10.0, 0.0)


def test_point_at_chainage_survives_a_duplicate_at_the_very_start():
    """`span` dokładnie 0.0 — i duplikat musi być NA POCZĄTKU osi, nie w środku.

    To kosztowało jedno podejście i jest warte zapisania. Duplikat w środku osi
    (`stations = [0, 5, 5, 10]`, chainage 5) NIE dotyka tej gałęzi: pętla trafia
    już przy `index = 0`, gdzie `span` wynosi 5.0, i kończy wcześniej. Gałąź
    `span <= 0.0` pozostawała martwa, a mutacja `<=` -> `<` ją przeżywała.

    Dopiero duplikat w pierwszym segmencie (`stations = [0, 0, 10]`, chainage 0)
    daje `span` równy zeru. Zero jest DOKŁADNE, bo powstaje z odejmowania dwóch
    identycznych liczb. Bez tej gałęzi to jest dzielenie przez zero czekające na
    pierwszą oś z powtórzonym punktem — a `validate.py` przepuszcza taką oś jako
    OSTRZEŻENIE, nie błąd (znalezisko 7 z przejęcia).
    """
    axis = [(1.0, 2.0, 3.0), (1.0, 2.0, 3.0), (9.0, 9.0, 9.0)]
    stations = [0.0, 0.0, 10.0]
    assert stations[1] - stations[0] == 0.0, "span musi być dokładnym zerem"
    assert CP.point_at_chainage(axis, stations, 0.0) == (1.0, 2.0, 3.0)


def test_point_at_chainage_interpolates_a_segment_shorter_than_a_millimetre():
    """Segment krótszy niż mutowany próg — to on odróżnia `<= 0.0` od `<= 0.001`.

    Gałąź „span zerowy" ma się włączać WYŁĄCZNIE dla zera. Segment o długości
    0,5 mm jest krótki, ale niezerowy, więc pozycję w nim trzeba policzyć,
    a nie sprowadzić do jego początku. Mutacja progu `0.0` -> `0.001` daje tu
    (0.0, 0.0, 0.0) zamiast środka segmentu i dopiero ten przypadek ją widzi:
    testu z dokładnym zerem obie wersje przechodzą identycznie.

    Osie chunków mają punkty gęste — `validate.py` ostrzega poniżej
    `min_point_gap_m` — więc bardzo krótki segment nie jest wymysłem testu.
    """
    axis = [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (2.0, 0.0, 0.0)]
    stations = [0.0, 0.0005, 10.0]
    assert CP.point_at_chainage(axis, stations, 0.00025) == (0.5, 0.0, 0.0)


def test_point_at_chainage_lands_before_a_chainage_duplicate_not_after():
    """Prawe `<=` w porównaniu łańcuchowym decyduje, po której stronie duplikatu wypadniesz.

    Oś może mieć dwa punkty o TYM SAMYM chainage i różnej wysokości — tak wygląda
    pionowy uskok, gdyby dane go zawierały. Wtedy `chainage` równy duplikatowi ma
    dwie poprawne odpowiedzi i wybór jednej z nich jest zachowaniem, nie szczegółem:
    kotwica kamery skacze o całą różnicę wysokości.

    Ta mutacja NIE jest równoważna i to jest zmierzone, nie wyczytane. Bateria
    4000 wejść puszczona przez oryginał i przez oba warianty mutacji dała
    1267 różnic dla lewego `<=` i 2288 dla prawego, przy 1267 i 2856 trafieniach
    DOKŁADNIE w granicę. Bez policzenia trafień „zero różnic" nic by nie znaczyło —
    losowanie samo z siebie w punkty równości nie trafia (lekcja §5.2 z przejęcia).
    """
    axis = [(0.0, 0.0, 0.0), (5.0, 0.0, 0.0), (5.0, 0.0, 9.0), (10.0, 0.0, 9.0)]
    stations = [0.0, 5.0, 5.0, 10.0]
    assert CP.point_at_chainage(axis, stations, 5.0) == (5.0, 0.0, 0.0)
    assert CP.point_at_chainage(axis, stations, 7.5) == (7.5, 0.0, 9.0)


def test_point_at_chainage_reads_all_three_axes():
    """Mutacja `range(3)` -> `range(2)` zgubiłaby wysokość, czyli oko kamery."""
    axis = [(0.0, 0.0, 0.0), (0.0, 0.0, 10.0)]
    assert CP.point_at_chainage(axis, [0.0, 10.0], 5.0) == (0.0, 0.0, 5.0)


def test_point_at_chainage_on_a_single_point_axis_returns_that_point():
    assert CP.point_at_chainage([(3.0, 4.0, 5.0)], [7.0], 7.0) == (3.0, 4.0, 5.0)


# --- rodzaj rzutu ------------------------------------------------------------

def test_projection_ortho_is_recognised_by_the_exact_word():
    assert CP.is_orthographic({"projection": "ORTHO"}) is True


def test_projection_anything_else_is_perspective_including_typos():
    """Mutacja `==` -> `!=` zamieniłaby każdą perspektywę w ortogonalność.

    Literówka w manifeście ma dać perspektywę zgodnie z domyślną gałęzią,
    a nie ortogonalność „bo napis niepusty". `ortho_scale` i `lens` nie są
    przeliczalne jedna na drugą, więc pomyłka daje ujęcie w poprawnym miejscu
    i z niepoprawnym kadrem — render, który przechodzi bramkę metryczną
    i kłamie na oko.
    """
    for projection in ("PERSP", "ortho", "Ortho", "", "ORTHOGRAPHIC"):
        assert CP.is_orthographic({"projection": projection}) is False, projection

# 6.D25: uruchomienie tego pliku WPROST idzie ta sama droga, co caly zestaw —
# z licznikiem asercji i z odmowa przy zerze testow. Bez tej gałęzi `python3
# tools/tests/<modul>.py` konczyl sie kodem 0, nie wykonawszy ani jednego testu.
if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))
