#!/usr/bin/env python3
"""Macierz praw z T-903 — co wolno wpuścić do świata gry, a czego nie.

`docs/03-legal.md` jest w tym projekcie regułą twardą (CLAUDE.md §4 pkt 7):
nie proponuje się obejść i nie robi „podobnych, ale innych" wariantów cudzego
dzieła. Ta macierz przekłada tamten zakaz na listę, którą da się sprawdzić
maszynowo — bo zakaz zapisany wyłącznie prozą przechodzi dokładnie tak długo,
jak długo ktoś go pamięta.

Testy przyszły z gałęzi `t-903-rights-matrix`, gdzie leżały WEWNĄTRZ
`tools/tests/test_all.py`. Tamta gałąź stoi na historii bez wspólnego przodka
z dzisiejszym `main` (dwa różne commity korzeniowe), więc nie dało się jej
przebazować — treść jest przeniesiona, a testy przy okazji rozdzielone do
własnego modułu, zgodnie z dzisiejszą konwencją `test_all.py`, który sam
odkrywa `tools/tests/test_*.py`.
"""

import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MATRIX = os.path.join(ROOT, "data", "legal", "rights-matrix.json")

#: Statusy, które ZOBOWIĄZUJĄ do podania neutralnego zastępnika. Wpis bez
#: fallbacku przy takim statusie zostawiałby dziurę w świecie zamiast decyzji.
NEEDS_FALLBACK = {
    "permission_required",
    "replace_with_original",
    "reference_only",
    "excluded_until_cleared",
}


def _rights():
    with open(MATRIX, encoding="utf-8") as handle:
        return json.load(handle)


def test_rights_matrix_statuses_and_fallbacks():
    document = _rights()
    allowed = set(document["statuses"])
    for row in document["asset_classes"]:
        assert row["status"] in allowed, row["asset_or_element"]
        if row["status"] in NEEDS_FALLBACK:
            assert row.get("fallback"), row["asset_or_element"]


def test_rights_open_data_logo_is_not_general_brand_permission():
    """Licencja na dane otwarte NIE jest zgodą na używanie znaku towarowego.

    To są dwie różne rzeczy i pomylenie ich jest najłatwiejszym sposobem, żeby
    wpuścić logo STIB do świata gry „bo dane są otwarte".
    """
    document = _rights()
    assert document["open_data_logo_rule"]["status"] == "licence_specific_review"

    branded = next(row for row in document["asset_classes"]
                   if row["asset_or_element"]
                   == "stib_mivb_logo_as_world_asset_livery_or_marketing_brand")
    assert branded["status"] == "permission_required"


def test_rights_package_a_station_inventory_is_explicit():
    """Dwanaście stacji pakietu A wymienionych z nazwy, nie „wszystkie stacje".

    Lista zbiorcza starzeje się w ciszy: dochodzi stacja, nikt nie zauważa, że
    nie ma jej w macierzy, i jej wystrój wchodzi do gry bez decyzji.
    """
    document = _rights()
    station_ids = {row["station_id"] for row in document["package_a_artworks"]}
    expected = {
        "gare_de_l_ouest", "beekkant", "etangs_noirs", "comte_de_flandre",
        "sainte_catherine", "de_brouckere", "gare_centrale", "parc",
        "arts_loi", "maelbeek", "schuman", "merode",
    }
    assert station_ids == expected, (expected - station_ids, station_ids - expected)

    for row in document["package_a_artworks"]:
        assert row["status"] in {"permission_required", "excluded_until_cleared"}, row


def test_rights_every_single_artwork_entry_is_pinned_not_just_the_station_set():
    """Zbiór stacji NIE wystarczy: na jedną stację przypada po kilka dzieł.

    Zmierzone: 18 wpisów na 12 stacji, z czego pięć stacji (De Brouckère, Parc,
    Arts-Loi, Maelbeek, Merode) ma po więcej niż jednym dziele. Kontrola
    negatywna 04.09.2026: usunięcie ostatniego wpisu z listy NIE wywracało
    testu na zbiorze `station_id`, bo tę stację pokrywał inny wpis. Dzieło
    znikało z macierzy praw po cichu — a to jest dokładnie ten plik, w którym
    cisza jest najgroźniejsza.
    """
    rows = _rights()["package_a_artworks"]
    assert len(rows) == 18, f"wpisów jest {len(rows)}, a było 18 — dzieło doszło albo zniknęło"

    for row in rows:
        for field in ("station_id", "station", "status", "inventory_state"):
            assert row.get(field), (field, row)

    # Niezmiennik jest o TREŚCI wpisu, nie o słowniku stanów inwentarza: nazwane
    # dzieło musi mieć autora, a wpis bez nazwy dzieła musi nieść status
    # wykluczający. Pierwsza wersja tego testu rozdzielała wpisy po `inventory_state
    # == "identified"` i wywróciła się na prawdziwych danych — stanów jest pięć,
    # w tym `identified_shared_corridor` i `identified_current_project`, które mają
    # i dzieło, i autora. Reguła oparta na słowniku pękłaby przy każdym nowym stanie;
    # ta pyta o to, co naprawdę jest w wierszu.
    for row in rows:
        if row.get("work"):
            assert row.get("creator"), row
            assert row.get("source_url"), row
        else:
            assert row["status"] == "excluded_until_cleared", row
            assert not row.get("creator"), row

    # Słownik stanów jest jednak PRZYBITY osobno: nowy stan ma zmusić do decyzji,
    # a nie wejść po cichu pod regułę napisaną dla poprzednich.
    states = {row["inventory_state"] for row in rows}
    assert states == {
        "identified",
        "identified_shared_corridor",
        "identified_current_project",
        "identified_temporary_presence_requires_2026_check",
        "inventory_pending",
    }, sorted(states)

    # Para (stacja, dzieło) musi być unikalna wśród wpisów z nazwanym dziełem.
    named = [(r["station_id"], r["work"]) for r in rows if r.get("work")]
    assert len(set(named)) == len(named), "powtórzona para stacja+dzieło"


def test_rights_contributor_policy_requires_provenance():
    document = _rights()
    fields = set(document["contributor_policy"]["required_metadata"])
    assert {"asset_id", "source_url", "licence_or_permission_ref",
            "redistribution_allowed"} <= fields


def test_rights_matrix_is_referenced_from_the_hard_legal_document():
    """Macierz, do której nie prowadzi żaden odnośnik z `docs/03-legal.md`,
    jest plikiem, którego nikt nie przeczyta w chwili podejmowania decyzji."""
    with open(os.path.join(ROOT, "docs", "03-legal.md"), encoding="utf-8") as handle:
        legal = handle.read()
    assert "18-rights-matrix" in legal or "rights-matrix.json" in legal, (
        "docs/03-legal.md nie odsyła do macierzy praw")
