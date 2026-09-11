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
    out.extend(_niezgodnosci_pol(asset, properties))
    return out


def _niezgodnosci_pol(asset, properties):
    """Pola wpisu wobec `properties` — JEDEN czytnik dla poziomu najwyższego
    i dla gałęzi warunkowych.

    Drugi czytnik tych samych regul rozjechalby sie po cichu, a rozjazd akurat tej
    pary znaczylby, ze galaz `then` przyjmuje wartosc, ktora poziom najwyzszy
    odrzuca — albo odwrotnie. Rekurencja w obiekt jest tu od 6.D103, bo galaz
    `original_recording` zada `location` z wlasnym `required` i wlasnymi
    `properties`; na poziomie najwyzszym `location` ma `oneOf` i przez to zadnej
    rekurencji nie wyzwala.
    """
    out = []
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
        if rule.get("type") == "object" and isinstance(wartosc, dict):
            for brak in sorted(set(rule.get("required", [])) - set(wartosc)):
                out.append(("%s.%s" % (field, brak), "pole wymagane w obiekcie"))
            if rule.get("additionalProperties") is False:
                for obce in sorted(set(wartosc) - set(rule.get("properties", {}))):
                    out.append(("%s.%s" % (field, obce), "pole spoza schematu"))
            for pod_pole, pod_powod in _niezgodnosci_pol(
                    wartosc, rule.get("properties", {})):
                out.append(("%s.%s" % (field, pod_pole), pod_powod))
    return out


#: Liczba gałęzi `allOf` w schemacie. Kotwica KW: literówka w czytniku gałęzi daje
#: pustą listę, a pusta lista przechodzi każdy werdykt niżej bez ani jednego
#: sprawdzenia. Zmierzone 10.09.2026: **trzy** — `licensed_library`,
#: `original_recording` i `cleared`.
LICZBA_GALEZI = 3


def galezie(schema):
    """Pary `(warunek, skutek)` ze zbioru `allOf` — czyli `if`/`then` schematu."""
    return [(rule["if"], rule["then"]) for rule in schema.get("allOf", [])
            if "if" in rule and "then" in rule]


def warunek_zachodzi(asset, warunek):
    """Czy wpis wpada pod tę gałąź: pola z `required` są, a `const` się zgadza.

    **`properties` jest tu PUSTO SPEŁNIONE dla pola, którego nie ma** — tak działa
    JSON Schema i dlatego `required` w `if` jest niezbędne, a nie ozdobne: bez niego
    wpis BEZ `source_type` spełniałby warunek i wpadał pod gałąź, która go nie
    dotyczy. Pierwsza wersja pytała `asset.get(pole) != const`, czyli porównywała
    `None` ze stałą — wtedy warunek odpadał sam i klauzula `required` nie robiła NIC.
    Zmierzone kontrolą negatywną: zdjęcie `required` niczego wtedy nie zapalało,
    choć docstring twierdził, że zapala. Różnica jest widoczna dopiero przy wiernej
    pustej prawdzie i dopiero wtedy kontrola KN-4 świeci na czerwono.
    """
    for pole in warunek.get("required", []):
        if pole not in asset:
            return False
    for pole, regula in warunek.get("properties", {}).items():
        if pole not in asset:
            continue                       # pusta prawda — pola nie ma, więc nie łamie
        if "const" in regula and asset[pole] != regula["const"]:
            return False
    return True


def niezgodnosci_podschematu(asset, pod):
    """`[(pole, powód)]` dla jednego `then` albo jednej gałęzi `anyOf`.

    Trzy rzeczy, bo tyle stoi w schemacie: `required`, `properties` (przez ten sam
    czytnik, co poziom najwyższy) i `anyOf`. Trzecia gałąź schematu ma w `then`
    WYŁĄCZNIE `anyOf` — zgoda ALBO licencja — więc sama para `const`/`required`
    by jej nie obsłużyła, i to jest zmierzona część roboty, nie szczegół.
    """
    out = []
    for pole in pod.get("required", []):
        # OBECNOSC KLUCZA, nie „niepusta wartosc", i to jest zgodnosc ze specyfikacja,
        # nie uproszczenie: JSON Schema `required` pyta wylacznie o klucz, a wartosc
        # `null` odrzuca dopiero regula typu z `properties` tej samej galezi. Pierwsza
        # wersja odrzucala tu takze `None` — werdykt wychodzil ten sam, ale POWOD byl
        # inny niz ten, ktory poda walidator, a dzisiejszy manifest nie ma ani jednego
        # z tych kluczy, wiec roznicy nie mialoby co zmierzyc. Mierzy ja test nizej.
        if pole not in asset:
            out.append((pole, "gałąź warunkowa wymaga tego pola"))
    out.extend(_niezgodnosci_pol(asset, pod.get("properties", {})))

    if "anyOf" in pod:
        warianty = [niezgodnosci_podschematu(asset, wariant) for wariant in pod["anyOf"]]
        if all(warianty):
            powody = " ALBO ".join(
                ", ".join("%s: %s" % para for para in wariant) for wariant in warianty)
            out.append(("anyOf", "żaden wariant gałęzi nie jest spełniony (%s)" % powody))
    return out


def niezgodnosci_warunkowe(asset, schema):
    """`[(pole, powód)]` z tych gałęzi `allOf`, pod które wpis NAPRAWDĘ wpada."""
    out = []
    for warunek, skutek in galezie(schema):
        if warunek_zachodzi(asset, warunek):
            out.extend(niezgodnosci_podschematu(asset, skutek))
    return out


def test_audio_placeholders_satisfy_the_conditional_branches_too():
    """Wpisy manifestu wobec gałęzi `allOf`, a nie tylko wobec poziomu najwyższego.

    **Skąd.** Pętla zgodności z 6.D85 czyta wyłącznie `properties` najwyższego
    poziomu, a `license` nie stoi w jego `required` — więc wpis z
    `source_type = licensed_library` BEZ licencji przechodził ją cicho, choć
    schemat go w tej gałęzi żąda. Trzy istniejące testy tego modułu czytają `allOf`,
    ale pytają „czy SCHEMAT tego wymaga", a nie „czy WPIS to spełnia".

    **Dzisiejszy manifest nie wpada pod ani jedną gałąź** — wszystkie 13 wpisów ma
    `source_type = placeholder` i `rights_status = placeholder`. Ta pętla jest więc
    dziś cicha nie dlatego, że wpisy gałęzie spełniają, tylko dlatego, że ich nie
    dotyczą. Cały ciężar dowodu niesie kontrola na wejściu syntetycznym niżej i to
    jest powiedziane tutaj, żeby cisza nie została kiedyś wzięta za wynik.
    """
    schema = _schema()
    widziane = len(galezie(schema))
    assert widziane == LICZBA_GALEZI, (
        "czytnik gałęzi widzi %d, a zmierzone 10.09.2026 było %d: mniej znaczy "
        "literówkę we wzorcu (pusta lista przechodzi każdy werdykt bez sprawdzenia), "
        "więcej — nową gałąź schematu, której nikt jeszcze nie opisał"
        % (widziane, LICZBA_GALEZI))

    for asset in _placeholders()["assets"]:
        zle = niezgodnosci_warunkowe(asset, schema)
        assert zle == [], (asset["asset_id"], zle)


def test_the_conditional_branches_light_up_on_synthetic_entries():
    """Kontrola przyrządu dla wszystkich trzech gałęzi, w obie strony.

    Pętla wyżej milczy na dzisiejszym manifeście i milczałaby tak samo, gdyby
    czytnik gałęzi przestał cokolwiek widzieć. Każda gałąź ma tu więc wpis, który
    ją łamie, i wpis, który ją spełnia.
    """
    schema = _schema()
    wzorcowy = dict(_placeholders()["assets"][0])

    def powody(**podmiana):
        asset = dict(wzorcowy)
        asset.update(podmiana)
        return [powod for _pole, powod in niezgodnosci_warunkowe(asset, schema)]

    assert powody() == [], (
        "wzorcowy wpis manifestu zapala gałąź, pod którą nie wpada: %s" % powody())

    # 1. `licensed_library` bez licencji — przypadek z pola „Dlaczego" pozycji.
    assert powody(source_type="licensed_library"), (
        "wpis z licensed_library bez `license` nie zapalił gałęzi")
    assert powody(source_type="licensed_library", license="") != [], (
        "pusta licencja też ma być zgłoszona — gałąź żąda minLength 1")
    assert powody(source_type="licensed_library", license="Freesound CC0") == [], (
        "niepusta licencja nie ma być zgłaszana")

    # 2. `original_recording` bez proweniencji.
    assert powody(source_type="original_recording"), (
        "wpis z original_recording bez `recorded_by`/`recorded_at`/`location`/hash "
        "nie zapalił gałęzi")
    pelne = dict(
        source_type="original_recording",
        recorded_by="Jan Kowalski",
        recorded_at="2026-09-10T10:00:00Z",
        location={"description": "peron", "access_class": "public_passenger_area"},
        source_file_hash="sha256:" + "0" * 64)
    assert powody(**pelne) == [], (
        "kompletna proweniencja została zgłoszona: %s" % powody(**pelne))

    # …a niekompletny `location` ma być widziany W ŚRODKU obiektu.
    bez_dostepu = dict(pelne)
    bez_dostepu["location"] = {"description": "peron"}
    assert any("obiekcie" in p for p in powody(**bez_dostepu)), (
        "brak `access_class` w `location` nie został zauważony: %s"
        % powody(**bez_dostepu))

    # 3. `cleared` — `anyOf`: zgoda ALBO licencja, i to jest jedyna gałąź,
    #    której sama para `const`/`required` nie obsłuży. **Od decyzji właściciela
    #    z 11.09.2026 gałąź żąda ponadto `as_of`**, więc „sama zgoda" znaczy dziś
    #    „zgoda I data" — asercje niżej są przepisane, a nie dopisane obok.
    assert any("anyOf" in p or "wariant" in p for p in powody(rights_status="cleared")), (
        "`cleared` bez zgody i bez licencji nie zapalił gałęzi `anyOf`: %s"
        % powody(rights_status="cleared"))
    assert powody(rights_status="cleared", permission_ref="STIB/2026/17",
                  as_of="2026-09-11") == [], (
        "zgoda z datą obowiązywania ma wystarczyć")
    assert powody(rights_status="cleared", license="CC-BY-4.0",
                  as_of="2026-09-11") == [], (
        "licencja z datą obowiązywania ma wystarczyć")

    # 3a. I strona druga tej samej decyzji: zgoda BEZ daty ma być zgłoszona, a powód
    #     ma nazywać pole — inaczej czytający zobaczy tylko komunikat o `anyOf`.
    bez_daty = powody(rights_status="cleared", permission_ref="STIB/2026/17")
    assert any("wymaga tego pola" in p for p in bez_daty), (
        "`cleared` ze zgodą, ale BEZ `as_of`, nie został zgłoszony: %s" % bez_daty)
    pusta_data = powody(rights_status="cleared", permission_ref="STIB/2026/17", as_of="")
    assert pusta_data != [], (
        "pusta data obowiązywania przeszła — gałąź żąda `minLength: 1`")
    null_data = powody(rights_status="cleared", permission_ref="STIB/2026/17", as_of=None)
    assert any("oczekiwano ['string']" in p for p in null_data), (
        "`as_of: null` ma być odrzucone przez regułę typu, tak jak `permission_ref`: %s"
        % null_data)

    # 3b. Wartość `null` łamie gałąź przez REGUŁĘ TYPU, a nie przez `required` —
    #     tak jak zrobiłby to walidator. Klucz jest, więc `required` jest spełnione.
    #     Sprawdzane na POJEDYNCZYM wariancie, a nie na złożonym komunikacie `anyOf`:
    #     tamten skleja powody obu wariantów, więc „wymaga tego pola" stoi w nim
    #     zgodnie z prawdą — dla `license`, którego klucza naprawdę nie ma. Pierwsza
    #     wersja tej asercji czytała komunikat złożony i padła właśnie na tym.
    wariant_zgody = _schema()["allOf"][2]["then"]["anyOf"][0]
    z_nullem = niezgodnosci_podschematu(
        dict(wzorcowy, rights_status="cleared", permission_ref=None), wariant_zgody)
    powody_wariantu = [powod for _pole, powod in z_nullem]
    assert any("oczekiwano ['string']" in p for p in powody_wariantu), (
        "`permission_ref: null` ma być odrzucone przez regułę typu: %s" % powody_wariantu)
    assert not any("wymaga tego pola" in p for p in powody_wariantu), (
        "`permission_ref: null` zgłoszone jako BRAK pola — `required` pyta "
        "o obecność klucza, a klucz jest: %s" % powody_wariantu)

    # 4. Warunek NIE zachodzi bez pola — inaczej wpis bez `source_type` wpadałby
    #    pod gałąź, która go nie dotyczy.
    bez_typu = {k: v for k, v in wzorcowy.items() if k != "source_type"}
    assert niezgodnosci_warunkowe(bez_typu, schema) == [], (
        "wpis BEZ `source_type` wpadł pod gałąź warunkową: %s"
        % niezgodnosci_warunkowe(bez_typu, schema))


# --- 6.D125: `cleared` bez daty obowiązywania -----------------------------------

#: Status, którego dotyczy cała ta sekcja.
STATUS_CLEARED = "cleared"

#: Pole, w którym stałaby data obowiązywania prawa.
POLE_DATY = "as_of"

#: **Rozstrzygnięcie 6.D125 zostało ODWRÓCONE decyzją właściciela z 11.09.2026, i ten
#: blok jest PRZEPISANY, a nie dopisany obok.** Poprzednia wersja kończyła się zdaniem
#: „przeniesienie reguły do schematu zostaje decyzją właściciela, z policzonym kosztem:
#: dziś zero wpisów, jedna linia w `allOf[2].then`". Decyzja zapadła i brzmi **tak**.
#:
#: Pomiar, na którym stała tamta rekomendacja, zostaje prawdziwy i nie zmienia się ani
#: o cyfrę (zmierzone na `fdabff4`, powtórzone na `feb4ea1`):
#:
#:   * manifest ma **13** wpisów i **wszystkie** mają `rights_status: placeholder`;
#:   * wpisów `cleared` jest **zero**, więc wymaganie daty nie dotyka dziś ani jednego;
#:   * **ani jeden** wpis nie niesie własnego `as_of`;
#:   * manifest niesie za to `as_of` w KORZENIU: `2026-08-31`.
#:
#: **Co się zmieniło.** Nie liczby, tylko to, czyja jest decyzja. 6.D125 mierzyło koszt
#: i wskazywało, że dołożenie daty do gałęzi `cleared` jest regułą, której
#: `docs/03-legal.md` NIE stawia — dokument żąda zakresu („konkretne zamierzone użycie"),
#: nie terminu — więc nie jest to uzupełnienie luki, tylko decyzja o modelu danych.
#: Właściciel tę decyzję podjął, a §4.6 (`data/` tylko do odczytu) wymienia dokładnie
#: taki przypadek: „chyba że zadanie mówi inaczej wprost".
#:
#: **Co stoi dziś w schemacie.** Gałąź `allOf[2].then` (warunek `rights_status == cleared`)
#: dostała `required: ["as_of"]` oraz `properties.as_of` o typie `string`, `minLength: 1`
#: i `format: date`. Trzy linie, nie jedna — bo samo `required` przepuściłoby `null`
#: i pusty napis, a to jest ta sama pułapka, którą ten moduł opisuje przy `permission_ref`:
#: `required` pyta WYŁĄCZNIE o obecność klucza.
#:
#: **Bramka niżej ZOSTAJE, choć schemat mówi już to samo** — i to nie jest duplikat,
#: tylko dwa różne czytniki tego samego zdania. Schemat jest deklaracją, a w tym
#: repozytorium **nie ma walidatora JSON Schema** (6.D85 odrzuciło tę zależność), więc
#: jedynym, co go WYKONUJE, są czytniki tego modułu. Reguła w schemacie bez bramki byłaby
#: zdaniem, którego nic nie sprawdza.
POWOD_BRAKU_DATY = (
    "wpis `cleared` musi nieść `as_of` — datę, od której zgoda albo licencja "
    "obowiązuje. `as_of` w korzeniu manifestu datuje AUDYT PLIKU, nie PRAWO"
)


def wpisy_cleared(manifest=None):
    """Wpisy manifestu o statusie `cleared`. Dziś pusta lista — i to jest pomiar."""
    dane = manifest if manifest is not None else _placeholders()
    return [a for a in dane["assets"] if a.get("rights_status") == STATUS_CLEARED]


def brak_daty_obowiazywania(asset):
    """`[(pole, powod)]` — pusta lista, gdy wpisowi nic nie brakuje.

    Kształt zwracany taki sam jak w `niezgodnosci_warunkowe`, żeby dało się to
    zsumować z resztą werdyktu bez tłumaczenia jednego formatu na drugi.
    """
    if asset.get("rights_status") != STATUS_CLEARED:
        return []
    wartosc = asset.get(POLE_DATY)
    if isinstance(wartosc, str) and wartosc.strip():
        return []
    return [(POLE_DATY, POWOD_BRAKU_DATY)]


def test_ile_wpisow_dotknelaby_data_obowiazywania():
    """Pomiar, o który prosi pole „Wyjście" — cztery liczby, wszystkie z drzewa.

    Liczba wpisów `cleared` jest tu najważniejsza i wynosi **zero**: wymaganie daty
    nie dotknęłoby dziś ani jednego wpisu. Pozostałe trzy liczby mówią, dlaczego to
    nie jest cała odpowiedź.
    """
    manifest = _placeholders()
    wszystkie = manifest["assets"]

    assert len(wszystkie) == 13, len(wszystkie)
    assert len(wpisy_cleared(manifest)) == 0, (
        "pojawił się wpis `cleared` — rozstrzygnięcie 6.D125 trzeba przeczytać "
        "jeszcze raz, bo liczyło na zero: %s" % wpisy_cleared(manifest))
    assert {a.get("rights_status") for a in wszystkie} == {"placeholder"}, (
        {a.get("rights_status") for a in wszystkie})
    assert [a for a in wszystkie if a.get(POLE_DATY)] == [], (
        "wpis niesie własne `as_of` — dotąd nie niósł go żaden")

    # Pole ISTNIEJE w schemacie na poziomie najwyższym jako opcjonalne — i tak zostaje,
    # bo wpisy `placeholder` daty prawa nie mają. Wymaganie stoi w GAŁĘZI `cleared`,
    # od decyzji właściciela z 11.09.2026; asercje niżej czytają jedno i drugie.
    schema = _schema()
    assert POLE_DATY in schema["properties"], (
        "schemat nie ma pola `as_of` — rozstrzygnięcie 6.D125 opiera się na tym, "
        "że ono już tam jest")
    assert POLE_DATY not in schema["required"], (
        "`as_of` stał się polem wymaganym BEZWARUNKOWO — decyzja z 11.09.2026 żądała "
        "go wyłącznie w gałęzi `cleared`, a wpisy `placeholder` daty prawa nie mają")
    assert schema["properties"][POLE_DATY].get("format") == "date", (
        schema["properties"][POLE_DATY])

    # **Decyzja właściciela z 11.09.2026, sprawdzona na schemacie, a nie na pamięci.**
    # Trzy warunki, bo samo `required` przepuściłoby `null` i pusty napis — ta sama
    # pułapka, którą ten moduł opisuje przy `permission_ref`.
    galaz = schema["allOf"][2]["then"]
    assert POLE_DATY in galaz.get("required", []), (
        "gałąź `cleared` nie wymaga `as_of` — decyzja z 11.09.2026 mówiła, że ma "
        "wymagać: %s" % galaz.get("required"))
    regula = galaz.get("properties", {}).get(POLE_DATY, {})
    assert regula.get("type") == "string", (
        "`as_of` w gałęzi `cleared` przyjmuje `null` — `required` pyta tylko "
        "o obecność klucza: %s" % regula)
    assert regula.get("minLength") == 1 and regula.get("format") == "date", (
        "`as_of` w gałęzi `cleared` przyjmuje pusty napis albo nie jest datą: %s"
        % regula)

    # I że korzeń manifestu ma SWOJE `as_of` — datę audytu pliku, nie prawa.
    assert manifest.get(POLE_DATY) == "2026-08-31", manifest.get(POLE_DATY)


def test_cleared_bez_daty_obowiazywania_jest_zglaszany():
    """Bramka stoi TUTAJ, nie w schemacie — powód przy `POWOD_BRAKU_DATY`.

    **Dzisiejszy manifest nie ma ani jednego wpisu `cleared`**, więc pętla po nim
    milczałaby niezależnie od tego, czy reguła działa. Zieleń takiej pętli czyta
    się jako „wszystko w porządku", a znaczy „nie było czego sprawdzić" — ta sama
    rodzina, którą projekt tropi od 6.D27. Przed jałowością chroni więc **blok
    syntetyczny niżej**, a nie pętla.

    **Asercja `wpisy_cleared(manifest) == []` jest DROGOWSKAZEM DLA CZYTAJĄCEGO,
    nie bramką — i to jest zmierzone, a nie przypuszczone.** KN-5 zdjęła ją i test
    przeszedł **14/14**: blok syntetyczny działa bez niej. Zostaje, bo mówi
    w miejscu, w którym ktoś czyta pętlę, dlaczego ta pętla nic nie dowiodła;
    wartości tej liczby pilnuje osobno
    `test_ile_wpisow_dotknelaby_data_obowiazywania`, i to tam jest bramka.
    """
    manifest = _placeholders()
    zgloszenia = [(a["asset_id"], brak_daty_obowiazywania(a)) for a in manifest["assets"]]
    zle = [(aid, powody) for aid, powody in zgloszenia if powody]
    assert zle == [], zle
    assert len(zgloszenia) == 13, len(zgloszenia)
    assert wpisy_cleared(manifest) == [], (
        "pętla wyżej przeszła, ale NIE dlatego, że daty są — dlatego, że nie ma "
        "ani jednego wpisu `cleared`; ten test mierzy regułę na wpisach "
        "syntetycznych niżej")

    wzorcowy = dict(manifest["assets"][0])

    # 1. `cleared` bez `as_of` — zgłoszone.
    powody = brak_daty_obowiazywania(dict(wzorcowy, rights_status=STATUS_CLEARED,
                                          permission_ref="STIB/2026/17"))
    assert [pole for pole, _p in powody] == [POLE_DATY], powody
    assert "AUDYT PLIKU" in powody[0][1], powody[0][1]

    # 2. `cleared` z datą — milczy.
    assert brak_daty_obowiazywania(
        dict(wzorcowy, rights_status=STATUS_CLEARED, permission_ref="STIB/2026/17",
             **{POLE_DATY: "2026-09-11"})) == []

    # 3. `as_of: null` i `as_of: ""` to NIE jest data. Klucz jest, więc sama
    #    obecność pola niczego nie dowodzi — a schemat dopuszcza `null` wprost.
    for pusta in (None, "", "   "):
        assert brak_daty_obowiazywania(
            dict(wzorcowy, rights_status=STATUS_CLEARED, permission_ref="x",
                 **{POLE_DATY: pusta})), ("pusta data przeszła: %r" % (pusta,))

    # 4. Reguła dotyczy WYŁĄCZNIE `cleared`. Wpis `placeholder` bez daty jest
    #    poprawny i ma taki zostać — inaczej bramka zapaliłaby się na wszystkich
    #    trzynastu i zmusiła do zmiany w `data/`, której ta pozycja nie robi.
    for status in ("placeholder", "permission_required", "rejected"):
        assert brak_daty_obowiazywania(dict(wzorcowy, rights_status=status)) == [], status


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
