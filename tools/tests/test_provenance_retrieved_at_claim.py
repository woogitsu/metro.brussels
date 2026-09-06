#!/usr/bin/env python3
"""6.D16: `docs/09-data-provenance.md` twierdziło, że `retrieved_at` „nie może
zmieniać byte-deterministycznego canonical outputu" — dla dwóch miejsc to nieprawda.

**Skąd się wzięło.** Zmierzone przy pozycji 6.D12 (#295) i opisane w
`reports/zapisy-do-data.md` §4.3–4.4: `build_alignment.py` kopiuje
`retrieved_at` z `data/network/shapes-manifest.json` do
`document["source"]["retrieved_at"]`, a `normalize_stops.py` — z
`data/network/gtfs-manifest.json` do `document["feed"]["retrieved_at"]`. Oba
`document` są potem serializowane `P.canonical_json(document)` do plików, które
repo **commituje** (`data/track/*.json`, `data/network/stops.json`), nie tylko do
`.provenance.json`. Zdanie w dokumencie mówiło inaczej, bez wyjątku.

**Co ta bramka pilnuje.** Dwóch rzeczy naraz, żeby żadna z nich nie wróciła po
cichu:

1. że kod naprawdę robi to, co teraz mówi dokument — `retrieved_at` z manifestu
   trafia do `document[...]`, a `document` (nie sam manifest) jest zapisywany
   przez `canonical_json` do pliku wynikowego. Gdyby ktoś to zmienił bez
   aktualizacji dokumentu (albo odwrotnie), ten test by to złapał.
2. że akapit dokumentu, który to opisuje, nadal nazywa rozróżnienie
   „manifest proweniencji" / „plik wynikowy" i wymienia oba narzędzia z nazwy —
   a nie wraca do starego, bezwarunkowego zdania „nie mogą zmieniać
   byte-deterministycznego canonical outputu" bez zastrzeżenia.

Parsery mają kontrolę negatywną (`test_detectors_reject_code_and_docs_without_the_pattern`)
tak jak `test_run_mode_claims.py` i `test_docs_ci_claims.py` — bez niej bramka
byłaby zielona równie chętnie na martwym regexie, co na prawdziwym dopasowaniu.
"""
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DOC = os.path.join(ROOT, "docs", "09-data-provenance.md")
BUILD_ALIGNMENT = os.path.join(ROOT, "tools", "track", "build_alignment.py")
NORMALIZE_STOPS = os.path.join(ROOT, "tools", "track", "normalize_stops.py")

#: Klucz `retrieved_at` skopiowany wprost z manifestu do słownika `feed`.
FEED_HAS_RETRIEVED_AT = re.compile(r'"retrieved_at":\s*manifest\.get\("retrieved_at"\)')

#: `feed` (zawierający `retrieved_at`) trafia do `document["source"]`/`document["feed"]`
#: — jako przypisanie po fakcie (`build_alignment.py`) albo jako klucz w literale
#: słownika `document = {...}` (`normalize_stops.py`) — czyli do treści dokumentu
#: wynikowego, nie tylko manifestu.
FEED_EMBEDDED_IN_DOCUMENT = re.compile(
    r'document\["(?:source|feed)"\]\s*=\s*feed\b|"(?:source|feed)":\s*feed\b')

#: `document` (ten sam obiekt) jest serializowany kanonicznie — czyli to on, a nie
#: tylko `.provenance.json`, staje się bajtami pliku, który repo commituje.
DOCUMENT_WRITTEN_CANONICALLY = re.compile(r'canonical_json\(document\)')

#: Stare, bezwarunkowe zdanie z dokumentu sprzed 6.D16 — jeśli wróci w tej
#: dosłownej formie (bez zastrzeżenia o pliku wynikowym), bramka ma je złapać.
OLD_UNCONDITIONAL_CLAIM = (
    "Nie są częścią hasha treści i nie mogą zmieniać byte-deterministycznego "
    "canonical outputu."
)

#: Frazy, które muszą współwystępować w akapicie o `retrieved_at`: rozróżnienie
#: manifestu proweniencji od pliku wynikowego jest tym, co rozstrzyga, kiedy
#: zdanie o niezmienności zachodzi, a kiedy nie (pole „Skończone, gdy" 6.D16).
REQUIRES_MANIFEST_PHRASE = re.compile(r"manifest\w* proweniencji", re.I)
REQUIRES_OUTPUT_PHRASE = re.compile(r"plik\w* wynikow\w*", re.I)


def _read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def code_embeds_retrieved_at_in_committed_output(source_text):
    """Czy dany plik narzędzia kopiuje `retrieved_at` do dokumentu, który potem
    zapisuje kanonicznie — czyli do pliku wynikowego, a nie tylko manifestu."""
    return bool(FEED_HAS_RETRIEVED_AT.search(source_text)
                and FEED_EMBEDDED_IN_DOCUMENT.search(source_text)
                and DOCUMENT_WRITTEN_CANONICALLY.search(source_text))


def retrieved_at_section(doc_text):
    """Akapity dokumentu od zdania o `retrieved_at` do najbliższego nagłówka `##`."""
    match = re.search(
        r"`retrieved_at`, ETag i Last-Modified są metadanymi obserwacji.*?"
        r"(?=^## |\Z)",
        doc_text, re.MULTILINE | re.DOTALL)
    return match.group(0) if match else ""


def names_manifest_vs_output_distinction(section_text):
    return bool(REQUIRES_MANIFEST_PHRASE.search(section_text)
                and REQUIRES_OUTPUT_PHRASE.search(section_text))


def test_build_alignment_really_embeds_retrieved_at_in_its_committed_output():
    text = _read(BUILD_ALIGNMENT)
    assert code_embeds_retrieved_at_in_committed_output(text), (
        f"{BUILD_ALIGNMENT} nie kopiuje już retrieved_at do document[...] "
        "zapisywanego przez canonical_json — albo dokument trzeba poprawić, "
        "albo ten test zaczął patrzeć w złe miejsce")


def test_normalize_stops_really_embeds_retrieved_at_in_its_committed_output():
    text = _read(NORMALIZE_STOPS)
    assert code_embeds_retrieved_at_in_committed_output(text), (
        f"{NORMALIZE_STOPS} nie kopiuje już retrieved_at do document[...] "
        "zapisywanego przez canonical_json — albo dokument trzeba poprawić, "
        "albo ten test zaczął patrzeć w złe miejsce")


def test_doc_names_the_manifest_vs_output_distinction_and_both_tools():
    doc_text = _read(DOC)
    section = retrieved_at_section(doc_text)
    assert section, (
        f'{DOC} nie ma już zdania „retrieved_at, ETag i Last-Modified są '
        'metadanymi obserwacji" — sekcja zniknęła albo zmieniło się jej brzmienie')

    assert names_manifest_vs_output_distinction(section), (
        'akapit o retrieved_at w ' + DOC + ' nie nazywa rozróżnienia '
        '„manifest proweniencji" / „plik wynikowy" — a to ono rozstrzyga, kiedy '
        'zdanie o niezmienności zachodzi (pole „Skończone, gdy" pozycji 6.D16)')

    assert "build_alignment.py" in section and "normalize_stops.py" in section, (
        "akapit o retrieved_at nie wymienia z nazwy obu narzędzi, dla których "
        "zdanie o niezmienności jest dziś nieprawdziwe")

    assert OLD_UNCONDITIONAL_CLAIM not in doc_text, (
        "stare, bezwarunkowe zdanie o retrieved_at wróciło do dokumentu bez "
        "zastrzeżenia o pliku wynikowym")


def test_detectors_reject_code_and_docs_without_the_pattern():
    """Kontrola negatywna: bez niej bramka wyżej mogłaby być zielona i na martwym
    regexie (zero trafień zawsze), i na regexie, który łapie wszystko."""
    # Kod, który liczy retrieved_at, ale nigdzie go nie osadza w dokumencie —
    # to jest dokładnie kształt „tylko manifest", który dokument opisuje jako OK.
    only_manifest = (
        'feed = {"retrieved_at": manifest.get("retrieved_at")}\n'
        'with open(prov_path, "wb") as handle:\n'
        '    handle.write(P.canonical_json(feed))\n'
    )
    assert not code_embeds_retrieved_at_in_committed_output(only_manifest), (
        "detektor kodu zapalił się na przykładzie, który NIE osadza retrieved_at "
        "w dokumencie wynikowym — fałszywy alarm")

    # Kod bez żadnego retrieved_at.
    unrelated_code = 'document["source"] = feed\nhandle.write(P.canonical_json(document))\n'
    assert not code_embeds_retrieved_at_in_committed_output(unrelated_code), (
        "detektor kodu zapalił się bez klucza retrieved_at w ogóle — fałszywy alarm")

    # Prawdziwy kształt, ten sam co w obu narzędziach — musi się złapać.
    real_shape = (
        'feed = {"source_id": manifest.get("source_id"),\n'
        '        "retrieved_at": manifest.get("retrieved_at")}\n'
        'document["source"] = feed\n'
        'with open(out_path, "wb") as handle:\n'
        '    handle.write(P.canonical_json(document))\n'
    )
    assert code_embeds_retrieved_at_in_committed_output(real_shape), (
        "detektor kodu NIE złapał kształtu identycznego z build_alignment.py/"
        "normalize_stops.py — regex się popsuł")

    # Stary dokument: samo bezwarunkowe zdanie, bez rozróżnienia i bez nazw narzędzi.
    old_doc = (
        "## Minimalny manifest\n\n"
        "`retrieved_at`, ETag i Last-Modified są metadanymi obserwacji. Nie są "
        "częścią hasha treści i nie mogą zmieniać byte-deterministycznego "
        "canonical outputu.\n\n"
        "## Bezpieczeństwo sekretów\n"
    )
    old_section = retrieved_at_section(old_doc)
    assert old_section, "parser sekcji nie złamał się na starym kształcie dokumentu"
    assert not names_manifest_vs_output_distinction(old_section), (
        "detektor rozróżnienia manifest/plik wynikowy uznał stary, bezwarunkowy "
        "akapit za poprawny — fałszywie zielone")
    assert OLD_UNCONDITIONAL_CLAIM in old_doc, (
        "stała ze starym zdaniem nie zgadza się już z samym sobą — literówka w teście")

    # Nowy dokument (kształt tego, co ta pozycja wpisuje) — musi przejść oba testy.
    new_doc = (
        "## Minimalny manifest\n\n"
        "`retrieved_at`, ETag i Last-Modified są metadanymi obserwacji **manifestu** "
        "— nie są częścią hasha treści.\n\n"
        "Ale gdy downstream generator kopiuje to pole z manifestu do **pliku "
        "wynikowego** — tak robią `build_alignment.py` i `normalize_stops.py` — "
        "różnica między **manifestem proweniencji** a **plikiem wynikowym** "
        "rozstrzyga, kiedy zdanie zachodzi.\n\n"
        "## Bezpieczeństwo sekretów\n"
    )
    new_section = retrieved_at_section(new_doc)
    assert names_manifest_vs_output_distinction(new_section), (
        "detektor rozróżnienia nie złapał kształtu identycznego z poprawionym "
        "dokumentem — regex się popsuł")
    assert "build_alignment.py" in new_section and "normalize_stops.py" in new_section
    assert OLD_UNCONDITIONAL_CLAIM not in new_doc
