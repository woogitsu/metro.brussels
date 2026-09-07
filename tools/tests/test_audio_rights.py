#!/usr/bin/env python3
"""Prawa do dźwięku z T-905 — czego wolno użyć jako dźwięku w grze.

`docs/03-legal.md` zabrania wprost brania cudzego dzieła i robienia z niego
„podobnego, ale innego" wariantu. Dla dźwięku ten zakaz ma dwa konkretne
kształty: zapowiedzi i sygnały STIB są cudze, a nagranie zrobione na peronie
niesie głosy ludzi, którzy się na to nie godzili. Schemat manifestu przekłada
oba na pola, których nie da się zostawić pustych.

Testy przyszły z gałęzi `t-905-audio-rights`, gdzie leżały WEWNĄTRZ
`tools/tests/test_all.py`. Tamta gałąź stoi na historii bez wspólnego przodka
z dzisiejszym `main`, więc treść jest przeniesiona, a testy rozdzielone do
własnego modułu — zgodnie z dzisiejszą konwencją auto-odkrywania.
"""

import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SCHEMA = os.path.join(ROOT, "data", "audio", "audio-manifest.schema.json")
PLACEHOLDERS = os.path.join(ROOT, "data", "audio", "placeholders.json")


def _schema():
    with open(SCHEMA, encoding="utf-8") as handle:
        return json.load(handle)


def _placeholders():
    with open(PLACEHOLDERS, encoding="utf-8") as handle:
        return json.load(handle)


def _branch_for(schema, key, value):
    """Gałąź `then` z `allOf` dla warunku `key == value`."""
    return next(rule["then"] for rule in schema["allOf"]
                if rule.get("if", {}).get("properties", {}).get(key, {}).get("const") == value)


def test_audio_schema_has_required_rights_fields():
    schema = _schema()
    required = set(schema["required"])
    assert {"asset_id", "source_type", "creator", "rights_status", "processing_chain",
            "contains_voice", "contains_stib_brand_audio", "redistribution_allowed",
            "notes"} <= required
    assert "cleared" in schema["properties"]["rights_status"]["enum"]


def test_audio_schema_cleared_cannot_be_satisfied_by_null_rights():
    """`rights_status: cleared` musi wskazywać ZGODĘ albo LICENCJĘ, nie pustkę.

    Bez `minLength` pusty napis spełniałby „pole jest" i zasób bez żadnych praw
    wchodziłby do gry jako rozliczony.
    """
    cleared = _branch_for(_schema(), "rights_status", "cleared")
    branches = cleared["anyOf"]
    assert len(branches) == 2

    by_field = {next(iter(branch["properties"])): branch for branch in branches}
    for field in ("permission_ref", "license"):
        branch = by_field[field]
        assert field in branch["required"]
        rule = branch["properties"][field]
        assert rule.get("type") == "string" and rule.get("minLength", 0) >= 1, (field, rule)


def test_audio_schema_original_recording_requires_real_provenance_values():
    rule = _branch_for(_schema(), "source_type", "original_recording")
    assert {"recorded_by", "recorded_at", "location", "source_file_hash"} <= set(rule["required"])
    assert rule["properties"]["recorded_by"]["type"] == "string"
    assert rule["properties"]["recorded_by"]["minLength"] >= 1
    assert rule["properties"]["recorded_at"]["type"] == "string"
    assert rule["properties"]["location"]["type"] == "object"
    assert rule["properties"]["source_file_hash"]["type"] == "string"


def test_audio_schema_licensed_library_requires_nonempty_license():
    rule = _branch_for(_schema(), "source_type", "licensed_library")
    assert "license" in rule["required"]
    assert rule["properties"]["license"]["type"] == "string"
    assert rule["properties"]["license"]["minLength"] >= 1


def test_audio_placeholders_are_neutral_and_non_stib():
    document = _placeholders()
    seen = set()
    for asset in document["assets"]:
        assert asset["asset_id"] not in seen, asset["asset_id"]
        seen.add(asset["asset_id"])
        assert asset["source_type"] == "placeholder", asset["asset_id"]
        assert asset["rights_status"] == "placeholder", asset["asset_id"]
        assert asset["contains_stib_brand_audio"] is False, asset["asset_id"]

    categories = {asset["category"] for asset in document["assets"]}
    assert "doors" in categories and "announcement" in categories


def test_audio_placeholder_registry_has_no_ripped_source_urls():
    """Zastępnik z adresem do YouTube'a albo do aplikacji STIB nie jest zastępnikiem,
    tylko instrukcją, skąd zerżnąć cudzy dźwięk."""
    text = json.dumps(_placeholders(), ensure_ascii=False).lower()
    for forbidden in ("youtube.com", "youtu.be", "app.stib", "soundcloud.com"):
        assert forbidden not in text, forbidden


def test_audio_raw_paths_are_gitignored():
    """Surowe nagrania zostają poza repo — niosą głosy osób postronnych."""
    with open(os.path.join(ROOT, ".gitignore"), encoding="utf-8") as handle:
        ignore = handle.read().splitlines()
    for path in ("recordings/", "data/audio/raw/", "assets/audio/raw/"):
        assert path in ignore, path


def test_audio_every_placeholder_declares_whether_it_carries_a_voice():
    """Pole `contains_voice` rozstrzyga o RODO, więc nie może go zabraknąć ani być
    zgadywane z nazwy kategorii.

    Zmierzone przy przenoszeniu: testy z gałęzi źródłowej sprawdzały
    `contains_stib_brand_audio`, ale ani jeden nie pytał o `contains_voice` —
    mimo że schemat wymaga obu, a to drugie jest tym, które dotyczy ludzi.
    """
    for asset in _placeholders()["assets"]:
        assert isinstance(asset.get("contains_voice"), bool), asset["asset_id"]
        if asset["category"] == "announcement":
            assert asset["contains_voice"] is True, asset["asset_id"]


def test_audio_placeholders_satisfy_the_schema_they_ship_next_to():
    """Rejestr zastępników i schemat leżą w jednym katalogu i muszą do siebie pasować.

    Bez tego schemat opisywałby jedno, a jedyny istniejący manifest niósł drugie —
    i nikt by tego nie zauważył, dopóki nie doszedłby pierwszy prawdziwy dźwięk.
    """
    schema = _schema()
    required = set(schema["required"])
    properties = schema["properties"]

    for asset in _placeholders()["assets"]:
        missing = required - set(asset)
        assert not missing, (asset["asset_id"], sorted(missing))
        for field, rule in properties.items():
            if field not in asset or "enum" not in rule:
                continue
            assert asset[field] in rule["enum"], (asset["asset_id"], field, asset[field])

# 6.D25: uruchomienie tego pliku WPROST idzie ta sama droga, co caly zestaw —
# z licznikiem asercji i z odmowa przy zerze testow. Bez tej gałęzi `python3
# tools/tests/<modul>.py` konczyl sie kodem 0, nie wykonawszy ani jednego testu.
if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))
