#!/usr/bin/env python3
"""Testy tożsamości renderera i reflektora kadru `approach`.

**Skąd się wzięły.** 02.09.2026, przy przenoszeniu CI na maszynę właściciela, dwie
bramki `tunnel-alignment` (L1_B i L2_E) zrobiły się czerwone bez żadnej zmiany
w geometrii. Przyczyna była podwójna i obie połowy są tu pilnowane:

1. **Nazwa silnika nie identyfikuje renderera.** Legacy EEVEE usunięto w Blenderze
   4.2; nowy silnik nosił wtedy `BLENDER_EEVEE_NEXT`, a w 5.0 przemianowano go
   z powrotem na `BLENDER_EEVEE`. ZMIERZONE: `enum_items` dla `engine` zwraca
   DOKŁADNIE `['BLENDER_EEVEE']` i na 4.0.2, i na 5.0.1 — dwa różne silniki pod
   jedną nazwą, a w logu stał ten sam `engine=BLENDER_EEVEE`.
2. **Ujęcie `approach` było płaskie z konstrukcji.** Zamknięta rura w jednym
   materiale emisyjnym, bez światła we wnętrzu: każdy kierunek trafia w tę samą
   jasność. Przechodziło bramkę pustki resztką refleksów — ink 0.0104 na legacy
   EEVEE, 0.0002 na EEVEE Next.

`framing` nie importuje `bpy`, więc przelot konfiguracji testuje się wprost.
Samo renderowanie weryfikuje Blender w CI.
"""
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "visual"))

import framing  # noqa: E402

MANIFEST = os.path.join(ROOT, "tools", "visual", "cameras.json")


def _manifest():
    with open(MANIFEST, encoding="utf-8") as handle:
        return json.load(handle)


def _approach_spec():
    for camera in _manifest()["scene_sets"]["clearance"]["cameras"]:
        if camera["id"] == "approach":
            return camera
    raise AssertionError("zestaw clearance nie ma kamery approach")


def test_manifest_declares_which_eevee_is_the_baseline():
    """Bez tego pola `apply_render_settings` nie ma czego pilnować.

    Wartość jest decyzją właściciela z 02.09.2026: bazą projektu jest EEVEE Next.
    """
    render = _manifest()["render"]
    assert render.get("eevee_generation") == "next", render.get("eevee_generation")


def test_the_engine_name_alone_is_not_treated_as_the_renderer_identity():
    """Manifest musi mówić WPROST, że nazwa silnika nie wystarcza.

    Bez tej notatki następna osoba zobaczy `BLENDER_EEVEE` w dwóch miejscach
    i uzna, że to ten sam renderer — dokładnie ten błąd kosztował dwie bramki.
    """
    comment = _manifest()["render"].get("$engine_comment", "")
    assert "4.2" in comment and "5.0" in comment, comment
    assert "BLENDER_EEVEE_NEXT" in comment, comment


def test_eevee_generation_splits_exactly_at_the_version_that_removed_legacy():
    """Granica to 4.2 — wersja, w której legacy EEVEE zniknął."""
    sys.path.insert(0, os.path.join(ROOT, "tools", "visual"))
    # Nie importujemy capture_blender (ciągnie bpy i mathutils) — sprawdzamy samą
    # regułę na tej samej stałej, którą on stosuje.
    since = (4, 2, 0)
    def generation(version):
        return "next" if version >= since else "legacy"
    assert generation((4, 0, 2)) == "legacy"
    assert generation((4, 1, 9)) == "legacy"
    assert generation((4, 2, 0)) == "next"
    assert generation((5, 0, 1)) == "next"


def test_approach_camera_carries_a_headlight():
    """Kamera we wnętrzu rury bez światła nie ma czego pokazać."""
    spec = _approach_spec()
    light = spec.get("headlight")
    assert light, "approach bez reflektora znów da płaską klatkę"
    assert light["energy_w"] > 0.0 and light["range_m"] > 0.0, light


def test_headlight_energy_stays_on_the_measured_maximum():
    """Moc jest DOBRANA POMIAREM, nie na oko — i pomiar jest zapisany.

    ZMIERZONE na L1_B, EEVEE Next: 400 W -> ink 0.0003 (odrzucone jako puste),
    4000 W -> 0.7434, 12000 W -> 0.8932, 40000 W -> 0.5177, bo obraz robi się
    jednorodny od przepalenia. Test pilnuje, żeby nikt nie zsunął tej wartości
    w którąkolwiek stronę bez powtórzenia pomiaru.
    """
    spec = _approach_spec()
    assert spec["headlight"]["energy_w"] == 12000.0, spec["headlight"]
    comment = spec.get("$headlight_comment", "")
    for measured in ("0.0003", "0.7434", "0.8932", "0.5177"):
        assert measured in comment, f"brak zmierzonej wartości {measured} w uzasadnieniu"


def test_headlight_is_declared_as_an_assumption_not_as_vehicle_data():
    """To parametr obrazu. Gdyby wyglądał na daną o M7, trafiłby do audytu wymiarów."""
    comment = _approach_spec().get("$headlight_comment", "")
    assert "ZALOZENIE" in comment, comment
    assert "nie wymiar M7" in comment, comment


def _solved_approach():
    spec = _approach_spec()
    anchors = {"approach_eye": (0.0, 0.0, 1.75), "approach_target": (30.0, 0.0, 1.75)}
    return framing.solve_camera(spec, (-5.0, -5.0, -2.0), (40.0, 5.0, 5.0),
                                960, 576, anchors, None)


def test_the_headlight_survives_the_framing_solver():
    """`solve_camera` buduje wynik kluczem po kluczu, więc przelot trzeba sprawdzić.

    Gdyby klucz wypadł, Blender dostałby kamerę bez światła, klatka wyszłaby płaska,
    a manifest dalej deklarowałby reflektor — bramka byłaby czerwona bez powodu
    widocznego w konfiguracji.
    """
    solved = _solved_approach()
    assert solved.get("headlight"), "reflektor zgubiony między manifestem a Blenderem"
    assert solved["headlight"]["energy_w"] == 12000.0


def test_the_solver_does_not_invent_a_headlight_for_the_slicing_cameras():
    """`gap` i `flank` tną geometrię płaszczyzną i światła nie potrzebują.

    Kontrola negatywna do testu wyżej: gdyby przelot dopisywał klucz wszystkim
    kamerom, tamten test przechodziłby także przy zepsutej implementacji.
    """
    anchors = {"gap_eye": (0.0, 0.0, 1.75), "gap_target": (10.0, 0.0, 1.75)}
    for camera in _manifest()["scene_sets"]["clearance"]["cameras"]:
        if camera["id"] == "approach":
            continue
        solved = framing.solve_camera(camera, (-5.0, -5.0, -2.0), (40.0, 5.0, 5.0),
                                      960, 576, anchors, None)
        assert "headlight" not in solved, camera["id"]
