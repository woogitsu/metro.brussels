#!/usr/bin/env python3
"""Kierunek artystyczny z T-902 — neutralny baseline, który nie czeka na prawa.

`docs/03-legal.md` zabrania kopiowania liverii, logo, map i wystroju STIB/MIVB.
Sam zakaz nie mówi jednak, JAK ma wyglądać świat, dopóki prawa są nierozstrzygnięte,
i to jest treść tej warstwy: trzy warstwy wizualne, z których pierwsza — `technical` —
wystarcza do całej produkcji geometrii i nie potrzebuje ani jednej zewnętrznej tekstury.
Maszynowa postać tej decyzji leży w `data/design/visual-style.json`.

Testy przyszły z gałęzi `t-902-art-direction`, gdzie leżały WEWNĄTRZ
`tools/tests/test_all.py`. Tamta gałąź stoi na historii bez wspólnego przodka
z dzisiejszym `main` (dwa różne commity korzeniowe), więc nie dało się jej przebazować —
treść jest przeniesiona, a testy przy okazji rozdzielone do własnego modułu, zgodnie
z dzisiejszą konwencją `test_all.py`, który sam odkrywa `tools/tests/test_*.py`.
Tak samo zrobiono z T-903 (`test_rights_matrix.py`) i T-905 (`test_audio_rights.py`).

GRANICA TEGO MODUŁU JEST WĄSKA I TO JEST ŚWIADOME. Tutaj sprawdza się KONFIGURACJĘ:
czy zapisana decyzja jest wewnętrznie spójna i czy nie wpuszcza brandingu tylnymi
drzwiami. Czy generator naprawdę zbudował z niej scenę, sprawdza bramka
`tools/ci/material_style.sh` — bo tego nie da się sprawdzić bez Blendera, a plik
JSON przeczytany testem jednostkowym przechodzi tak samo dobrze przy pustej scenie
(CLAUDE.md §5).
"""

import json
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
STYLE = os.path.join(ROOT, "data", "design", "visual-style.json")
GENERATOR = os.path.join(ROOT, "tools", "blender", "material_test_scene.py")

#: Warstwy pipeline'u w kolejności, w jakiej wolno je włączać. Kolejność jest
#: treścią decyzji, nie kosmetyką: warstwa brandowana stoi na końcu, bo wchodzi
#: dopiero po konkretnej zgodzie z macierzy praw T-903.
PIPELINE = ["technical", "neutral_realistic", "licensed_stib_optional"]


def _style():
    with open(STYLE, encoding="utf-8") as handle:
        return json.load(handle)


def test_visual_style_has_three_layer_pipeline():
    document = _style()
    assert document["pipeline"] == PIPELINE
    assert document["current_default"] == "technical"
    assert (document["layers"]["licensed_stib_optional"]["rights_gate"]
            == "data/legal/rights-matrix.json")


def test_visual_style_rights_gate_points_at_a_file_that_exists():
    """Bramka praw wskazująca na nieistniejący plik jest bramką tylko z nazwy.

    Warstwa `licensed_stib_optional` odsyła do macierzy z T-903. Gdyby ten plik
    zniknął albo został przeniesiony, warstwa nadal deklarowałaby, że jest
    bramkowana — i nikt by się nie dowiedział, że bramki nie ma. Dwa zadania
    scalone osobno (#179 wniosło macierz, T-902 wnosi ten odnośnik) to dokładnie
    ta sytuacja, w której odnośnik potrafi się rozjechać po cichu.
    """
    gate = _style()["layers"]["licensed_stib_optional"]["rights_gate"]
    assert os.path.isfile(os.path.join(ROOT, gate)), gate


def test_visual_material_presets_are_neutral_design_values():
    document = _style()
    ids = []
    for preset in document["material_presets"]:
        ids.append(preset["id"])
        assert preset["status"] == "design_model", preset["id"]
        assert "stib" not in preset["id"].lower(), preset["id"]
        assert "mivb" not in preset["id"].lower(), preset["id"]
        assert len(preset["base_color"]) == 4
        assert 0.0 <= preset.get("metallic", 0.0) <= 1.0
        assert 0.0 <= preset.get("roughness", 0.5) <= 1.0
    assert len(ids) == len(set(ids))
    assert {"concrete_clean", "brushed_metal", "glass", "rubber", "rail_steel",
            "generic_safety_strip"} <= set(ids)


def test_visual_style_declares_every_material_the_generator_requires_by_name():
    """Generator wymienia materiały Z NAZWY i taka para musi być przybita z obu stron.

    `material_test_scene.py` celuje kamerę `close` w trzy konkretne presety
    (`close_ids`) i odmawia, gdy któregoś nie ma. Poprzedni test pilnuje tylko
    sześciu identyfikatorów wpisanych ręcznie w listę oczekiwań — a to jest DRUGA
    kopia tej samej wiedzy, która potrafi się rozjechać z pierwszą. Ten test czyta
    listę Z GENERATORA, więc dopisanie tam czwartej nazwy natychmiast żąda presetu,
    zamiast czekać na czerwoną bramkę w CI z Blenderem.

    Odwrotny kierunek — preset bez bryły w scenie — sprawdza `tools/ci/material_style.sh`
    na wyeksportowanym GLB, bo tego nie da się rozstrzygnąć bez uruchomienia Blendera.
    """
    source = open(GENERATOR, encoding="utf-8").read()
    match = re.search(r'close_ids\s*=\s*\(([^)]*)\)', source)
    assert match, "nie znaleziono close_ids w generatorze"
    required = set(re.findall(r'"([^"]+)"', match.group(1)))
    assert required, match.group(1)

    available = {preset["id"] for preset in _style()["material_presets"]}
    assert required <= available, sorted(required - available)


def test_visual_external_sources_have_licence_and_provenance_policy():
    document = _style()
    for source in document["external_asset_sources"]:
        assert source["license"], source["id"]
        if source["id"] != "project_procedural":
            assert source.get("url") and source.get("checked_at"), source["id"]
    fields = set(document["asset_metadata_required"])
    assert {"asset_id", "source_url", "license", "source_hash",
            "redistribution_allowed"} <= fields


def test_visual_cc0_sources_do_not_extend_the_licence_to_the_site_itself():
    """„Assety są CC0" NIE znaczy „logo i regulamin serwisu też".

    To ta sama pomyłka, którą macierz praw T-903 łapie po stronie danych otwartych
    (`test_rights_open_data_logo_is_not_general_brand_permission`): licencja na
    treść i licencja na markę dostawcy to dwie różne rzeczy. Tutaj konsekwencja
    jest praktyczna — status ma zobowiązywać do zapisania pochodzenia KONKRETNEGO
    pliku, a nie zezwalać hurtem na wszystko, co stoi w danym serwisie.
    """
    for source in _style()["external_asset_sources"]:
        if source["license"] != "CC0":
            continue
        assert source["status"] == "allowed_with_asset_provenance", source["id"]


def test_visual_regression_baseline_is_deterministic():
    baseline = _style()["render_baseline"]
    assert baseline["auto_exposure"] is False
    assert baseline["temporal_jitter"] is False
    assert baseline["resolution"] == [960, 576]
    assert isinstance(baseline["deterministic_seed"], int)


def test_visual_baseline_prefers_eevee_next_over_the_legacy_engine():
    """Kolejność w `engine_preference` jest bramką, nie listą życzeń.

    `apt` na Ubuntu 24.04 daje Blendera 4.0.2, który renderuje LEGACY EEVEE,
    a `enum_items` dla `engine` zwraca `['BLENDER_EEVEE']` na obu generacjach —
    nazwa silnika ich NIE odróżnia (`tools/visual/capture_plan.py`, `EEVEE_NEXT_SINCE`;
    CLAUDE.md §9). Generator bierze pierwszy silnik, który się ustawi, więc jedyne
    miejsce, w którym ta konfiguracja może wybrać źle, to kolejność tej listy.
    """
    preference = _style()["render_baseline"]["engine_preference"]
    assert preference[0] == "BLENDER_EEVEE_NEXT", preference
    assert "BLENDER_EEVEE" in preference, preference
    assert preference.index("BLENDER_EEVEE_NEXT") < preference.index("BLENDER_EEVEE")


def test_visual_performance_budgets_wait_for_measurement():
    policy = _style()["performance_policy"]
    assert policy["status"] == "measure_first"
    for key in ("poly_budget", "draw_call_budget", "texture_budget",
                "shadow_light_budget", "lod_distances"):
        assert policy[key] is None, key


def test_visual_style_is_referenced_from_the_document_that_explains_it():
    """Plik konfiguracyjny bez odnośnika z dokumentu to plik, którego nikt nie znajdzie
    w chwili, gdy podejmuje decyzję o wyglądzie sceny.

    Ta sama reguła co dla macierzy praw
    (`test_rights_matrix_is_referenced_from_the_hard_legal_document`).
    """
    with open(os.path.join(ROOT, "docs", "20-art-direction.md"), encoding="utf-8") as handle:
        doc = handle.read()
    assert "data/design/visual-style.json" in doc, (
        "docs/20-art-direction.md nie odsyła do własnej konfiguracji")
    assert "rights-matrix" in doc or "T-903" in doc, (
        "dokument nie mówi, skąd bierze się zgoda na warstwę brandowaną")
