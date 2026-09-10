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
import re

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


#: Typy JSON Schema na typy Pythona. Mapa wystarcza — pole „Poza zakresem" pozycji
#: 6.D85 zabrania dopisywania zależności, a walidator z biblioteki byłby właśnie nią.
#: `bool` stoi PRZED `integer` świadomie: w Pythonie `True` jest instancją `int`, więc
#: kolejność bez tego rozróżnienia przepuszczałaby wartość logiczną w polu liczbowym.
TYPY_SCHEMATU = {
    "string": str,
    "boolean": bool,
    "array": list,
    "object": dict,
    "number": (int, float),
    "integer": int,
    "null": type(None),
}


def _zgodny_typ(wartosc, nazwa_typu):
    """Czy wartość ma typ o tej nazwie — z rozróżnieniem `bool` od liczby."""
    oczekiwany = TYPY_SCHEMATU[nazwa_typu]
    if nazwa_typu in ("number", "integer") and isinstance(wartosc, bool):
        return False
    return isinstance(wartosc, oczekiwany)


def niezgodnosci(asset, properties, additional_allowed):
    """Lista `(pole, powód)` — puste znaczy „ten wpis pasuje do schematu".

    Sprawdzane są cztery rzeczy, każda z osobnym powodem w komunikacie: TYP,
    WZORZEC, długość minimalna i przynależność do `enum`, plus zakaz pól spoza
    schematu. Do 10.09.2026 ta pętla brała wyłącznie `enum`, więc trzy z czterech
    mutacji z pola „Skąd" przechodziły 9/9 i kodem 0.
    """
    out = []
    if not additional_allowed:
        for field in sorted(set(asset) - set(properties)):
            out.append((field, "pole spoza schematu"))

    for field, rule in properties.items():
        if field not in asset:
            continue
        wartosc = asset[field]

        typy = rule.get("type")
        if typy is not None:
            dozwolone = [typy] if isinstance(typy, str) else list(typy)
            if not any(_zgodny_typ(wartosc, t) for t in dozwolone):
                out.append((field, "typ %r, oczekiwano %s"
                            % (type(wartosc).__name__, dozwolone)))
                continue

        if "enum" in rule and wartosc not in rule["enum"]:
            out.append((field, "wartość %r spoza enum" % (wartosc,)))
        if "pattern" in rule and isinstance(wartosc, str) \
                and re.search(rule["pattern"], wartosc) is None:
            out.append((field, "napis %r nie pasuje do wzorca %s"
                        % (wartosc, rule["pattern"])))
        if "minLength" in rule and isinstance(wartosc, str) \
                and len(wartosc) < rule["minLength"]:
            out.append((field, "napis krótszy niż minLength %d" % rule["minLength"]))
        if rule.get("type") == "array" and isinstance(wartosc, list):
            typ_elementu = (rule.get("items") or {}).get("type")
            if typ_elementu is not None:
                for i, element in enumerate(wartosc):
                    if not _zgodny_typ(element, typ_elementu):
                        out.append((field, "element %d ma typ %r, oczekiwano %s"
                                    % (i, type(element).__name__, typ_elementu)))
    return out


def test_audio_placeholders_satisfy_the_schema_they_ship_next_to():
    """Rejestr zastępników i schemat leżą w jednym katalogu i muszą do siebie pasować.

    Bez tego schemat opisywałby jedno, a jedyny istniejący manifest niósł drugie —
    i nikt by tego nie zauważył, dopóki nie doszedłby pierwszy prawdziwy dźwięk.

    **Przepisane 10.09.2026 (6.D85), a nie dopisane obok.** Poprzednia wersja pytała
    o obecność pól wymaganych i o `enum` — i o nic więcej. Zmierzone czterema
    mutacjami manifestu: typ listy, wzorzec identyfikatora i pole spoza schematu
    przechodziły **9/9, kod 0**. Najostrzejszy przypadek nie jest jednak żadnym
    z tych trzech: `redistribution_allowed` podmienione z wartości logicznej na napis
    przechodziło tak samo cicho — a to POLE, na którym `docs/03-legal.md` stawia
    blokadę prawną. (Dwa pozostałe pola logiczne, `contains_voice`
    i `contains_stib_brand_audio`, były chronione **przypadkiem**, przez dwa inne
    testy tego modułu: jeden pyta o RODO, drugi o markę STIB.)
    """
    schema = _schema()
    required = set(schema["required"])
    properties = schema["properties"]
    additional_allowed = schema.get("additionalProperties", True)

    for asset in _placeholders()["assets"]:
        missing = required - set(asset)
        assert not missing, (asset["asset_id"], sorted(missing))
        zle = niezgodnosci(asset, properties, additional_allowed)
        assert zle == [], (asset["asset_id"], zle)


def test_the_schema_check_tells_the_four_measured_shapes_apart():
    """Kontrola przyrządu na wpisie syntetycznym, dla każdego z czterech kształtów.

    Pętla po prawdziwym manifeście jest dziś cicha — i ma być. Cisza znaczy coś
    dopiero wtedy, gdy widać, że pętla ma czym zgłaszać.
    """
    schema = _schema()
    properties = schema["properties"]
    additional = schema.get("additionalProperties", True)
    wzorcowy = dict(_placeholders()["assets"][0])

    def powody(**podmiana):
        asset = dict(wzorcowy)
        asset.update(podmiana)
        return [powod for _pole, powod in niezgodnosci(asset, properties, additional)]

    assert powody() == [], "wzorcowy wpis z manifestu ma być zgodny"

    # Cztery kształty z pola „Skąd" pozycji 6.D85, każdy zgłaszany z INNEGO powodu.
    assert any("oczekiwano ['boolean']" in p for p in powody(redistribution_allowed="tak"))
    assert any("oczekiwano ['array']" in p for p in powody(processing_chain="normalizacja"))
    assert any("wzorca" in p for p in powody(asset_id="ZŁY ID!"))
    assert any("spoza schematu" in p for p in powody(pole_ktorego_nie_ma=1))

    # I kierunki przeciwne: poprawne wartości nie mogą się zgłaszać.
    assert powody(redistribution_allowed=True) == []
    assert powody(processing_chain=["normalizacja"]) == []
    assert powody(asset_id="doors-close-01") == []

    # `bool` w polu liczbowym: w Pythonie `True` JEST instancją `int`, więc bez
    # osobnego rozróżnienia mapa typów przepuściłaby to po cichu.
    assert not _zgodny_typ(True, "integer")
    assert _zgodny_typ(True, "boolean")
    assert _zgodny_typ(1, "integer")

# 6.D25: uruchomienie tego pliku WPROST idzie ta sama droga, co caly zestaw —
# z licznikiem asercji i z odmowa przy zerze testow. Bez tej gałęzi `python3
# tools/tests/<modul>.py` konczyl sie kodem 0, nie wykonawszy ani jednego testu.
if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))
