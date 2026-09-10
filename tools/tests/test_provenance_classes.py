#!/usr/bin/env python3
"""Klasy pochodzenia parametrów mają JEDNO źródło: `docs/02-simulation.md` — 6.D89.

**Skąd ta bramka.** Zmierzone 09.09.2026 i przeliczone 10.09.2026 na trzech zapisach
stojących obok siebie:

    docs/02-simulation.md   spec, observed, est, design_model     (definicja, 4 klasy)
    .claude/skills/sim-physics/SKILL.md   spec, est, design       (kopia, 3 klasy)
    docs/07-open-data-research.md         spec, est, design       (kopia, 3 klasy)
    data/vehicle/m7-spec.json             spec 15x, design_model 18x

Rozjeżdżała się **jedna nazwa z trzech**: `design` nie jest klasą tego dokumentu
(jest `design_model`), a czwartej klasy — `observed` — obie kopie nie wymieniały
wcale. `est` nie występuje w danych pojazdu **ani razu**, choć dokument nadal ją
definiuje: i to jest poprawne, bo definiuje ją jako „oszacowanie historyczne do
usunięcia/weryfikacji", czyli jako klasę, której obecność byłaby usterką.

**Dlaczego to nie jest „skrót rozjechał się z dokumentacją".** Starsza litera
słownika przetrwała w DWÓCH plikach, gdy dokument modelu i dane pojazdu przeszły na
nowszą — rozjazd jest dwustronny, nie jednostronnym uproszczeniem skrótu.

**Zbiór jest PARSOWANY, nie przepisany.** Gdyby stał tu jako lista w Pythonie, byłby
trzecią kopią tej samej wiedzy i rozjechałby się jak dwie poprzednie. Dopisanie klasy
do dokumentu ma nie zapalać niczego — dokument jest źródłem, nie kopią, i tego wprost
żąda pole „Skończone, gdy" pozycji 6.D89.
"""
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

#: Dokument, który klasy DEFINIUJE. Jedyne źródło.
MODEL = os.path.join(ROOT, "docs", "02-simulation.md")

#: Miejsca, w których klasy są CYTOWANE. Każde musi mieścić się w zbiorze z `MODEL`.
CYTUJACY = (
    os.path.join(".claude", "skills", "sim-physics", "SKILL.md"),
    os.path.join("docs", "07-open-data-research.md"),
)

#: Dane pojazdu — wartości pola `status`. Tylko do czytania (`CLAUDE.md` §4.6).
POJAZD = os.path.join(ROOT, "data", "vehicle", "m7-spec.json")

#: Zdanie definiujące, w postaci „`nazwa` = opis, `nazwa` = opis…". Wzorzec bierze
#: nazwy stojące PRZED znakiem równości — sam grep po grawisach złapałby też nazwy
#: parametrów i ścieżki plików, których w tym samym akapicie jest kilka.
DEFINICJA = re.compile(r"`([a-z_]+)`\s*=")

#: Nazwy WYCOFANE — stały w plikach cytujących, a dokument modelu ich nie zna.
#: Lista jest zamknięta i każdy wpis ma powód; rośnie wyłącznie przez pomiar.
WYCOFANE = {
    "design": "stało w skrócie `sim-physics` i w `docs/07` jako trzecia klasa; "
              "dokument modelu zna `design_model`, a `design` nie występuje ani "
              "w nim, ani w danych pojazdu (zmierzone 10.09.2026, 6.D89)",
}


def _read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def klasy_z_dokumentu():
    """Zbiór klas zdefiniowanych w `docs/02-simulation.md`."""
    return set(DEFINICJA.findall(_read(MODEL)))


def klasy_w_danych():
    """Wartości pola `status` z danych pojazdu, z licznikiem."""
    z_danych = {}

    def obejdz(node):
        if isinstance(node, dict):
            status = node.get("status")
            if isinstance(status, str):
                z_danych[status] = z_danych.get(status, 0) + 1
            for wartosc in node.values():
                obejdz(wartosc)
        elif isinstance(node, list):
            for wartosc in node:
                obejdz(wartosc)

    obejdz(json.loads(_read(POJAZD)))
    return z_danych


def nazwy_w_grawisach(relative):
    """Napisy `w_grawisach` z pliku — bez rozstrzygania, czy są klasą."""
    return set(re.findall(r"`([a-z_]+)`", _read(os.path.join(ROOT, relative))))


def test_no_citing_file_repeats_the_class_list():
    """Plik cytujący ODSYŁA do dokumentu, zamiast powtarzać listę klas — 6.D89.

    **Reguła jest odwrotna, niż wygląda na pierwszy rzut oka, i to jest wybór.**
    Naturalne „każda cytowana nazwa musi być znana" wymaga rozstrzygnięcia, KTÓRY
    napis w grawisach jest nazwą klasy — a to jest heurystyka. Pierwsza wersja tej
    bramki próbowała po akapicie zawierającym słowo „klas" i zgłosiła `as_of`
    z listy pól metadanych, czyli nazwę, która klasą nie jest. Heurystyka na tekście
    prozy nie ma jak być pewna.

    Reguła dzisiejsza pytania nie stawia: plik cytujący **nie wymienia klas w ogóle**,
    tylko odsyła do `docs/02-simulation.md`. Powtórzona lista jest drugą kopią tej
    samej wiedzy i rozjeżdża się z pierwszą — dokładnie to zmierzono w 6.D89.

    **Czego ta bramka nie złapie i mówię to wprost:** nazwy zupełnie nowej, która nie
    jest ani klasą zdefiniowaną, ani wycofaną. Złapie ponowne wpisanie listy i powrót
    nazwy wycofanej — czyli dwa kształty, które w tym repozytorium wystąpiły.
    """
    znane = klasy_z_dokumentu()
    assert len(znane) >= 4, (
        "dokument modelu definiuje %d klas — wzorzec definicji rozjechał się "
        "z treścią `docs/02-simulation.md`: %s" % (len(znane), sorted(znane)))

    zle = []
    for relative in CYTUJACY:
        w_pliku = nazwy_w_grawisach(relative)
        for nazwa in sorted(w_pliku & znane):
            zle.append((relative, nazwa, "klasa wymieniona zamiast odesłania"))
        for nazwa in sorted(w_pliku & set(WYCOFANE)):
            zle.append((relative, nazwa, WYCOFANE[nazwa]))
    assert zle == [], "\n".join(
        "%s: `%s` — %s" % (relative, nazwa, powod) for relative, nazwa, powod in zle)


def test_every_citing_file_points_at_the_document():
    """Odesłanie musi BYĆ, a nie tylko nie być listą.

    Bez tego wiersza bramka wyżej jest zielona także dla pliku, który o klasach nie
    mówi NIC — czyli dla skrótu, z którego wypadło jedyne zdanie kierujące czytelnika
    do definicji.
    """
    for relative in CYTUJACY:
        tekst = _read(os.path.join(ROOT, relative))
        assert "docs/02-simulation.md" in tekst, (
            "%s nie odsyła do `docs/02-simulation.md`, a to jedyne źródło nazw klas"
            % relative)


def test_every_status_in_the_vehicle_data_is_a_defined_class():
    """Każda wartość `status` w danych pojazdu należy do zbioru z dokumentu."""
    znane = klasy_z_dokumentu()
    w_danych = klasy_w_danych()
    assert w_danych, "w danych pojazdu nie ma ani jednego pola `status` — skan oślepł"

    obce = sorted(k for k in w_danych if k not in znane)
    assert obce == [], (
        "dane pojazdu używają klas %s, których `docs/02-simulation.md` nie definiuje "
        "(zna: %s)" % (obce, ", ".join(sorted(znane))))


def test_the_class_set_is_parsed_and_not_a_third_copy():
    """Kontrola przyrządu: zbiór ma pochodzić z dokumentu, a nie z listy w teście.

    Dopisanie klasy do dokumentu **nie może** niczego zapalić — tego wprost żąda pole
    „Skończone, gdy". Test podstawia dokument z klasą dodatkową i sprawdza, że parser
    ją widzi; gdyby zbiór był wpisany w ten plik, nowa nazwa byłaby dla niego obca.
    """
    import tempfile

    global MODEL
    prawdziwy = MODEL
    prawdziwe_klasy = klasy_z_dokumentu()
    try:
        with tempfile.TemporaryDirectory(prefix="mbxl-klasy-") as katalog:
            MODEL = os.path.join(katalog, "02-simulation.md")
            with open(MODEL, "w", encoding="utf-8") as uchwyt:
                uchwyt.write("Parametry mają provenance: `spec` = źródło, "
                             "`nowa_klasa` = coś nowego.\n")
            assert klasy_z_dokumentu() == {"spec", "nowa_klasa"}, klasy_z_dokumentu()

            # I kierunek przeciwny: napis w grawisach BEZ znaku równości nie jest
            # definicją klasy, tylko nazwą parametru albo ścieżką.
            with open(MODEL, "w", encoding="utf-8") as uchwyt:
                uchwyt.write("Wartość `masa_awo` jest w `data/vehicle/m7-spec.json`.\n")
            assert klasy_z_dokumentu() == set(), klasy_z_dokumentu()
    finally:
        MODEL = prawdziwy

    assert klasy_z_dokumentu() == prawdziwe_klasy, (
        "po przywróceniu parser nie widzi prawdziwego dokumentu — podstawienie "
        "wyciekło i dwie bramki wyżej mierzyłyby atrapę")


def test_the_document_still_defines_the_four_classes_the_measurement_found():
    """Kotwica na pomiarze z 10.09.2026 — bo cztery bramki wyżej są dziś ciche.

    Zbiór jest parsowany, więc jego ZAWĘŻENIE nie zapala niczego: gdyby dokument
    przestał definiować `observed`, obie bramki nadal by milczały, bo nikt jej nie
    cytuje. Ten wiersz mówi, że zawężenie ma być WIDOCZNE w diffie.
    """
    znane = klasy_z_dokumentu()
    zmierzone = {"spec", "observed", "est", "design_model"}
    assert zmierzone <= znane, (
        "z dokumentu zniknęły klasy %s — zawężenie słownika ma być widoczne "
        "w commicie, a nie ciche" % sorted(zmierzone - znane))

    # `est` nie występuje w danych ANI RAZU i to jest stan poprawny: dokument
    # definiuje ją jako „oszacowanie historyczne do usunięcia/weryfikacji", więc
    # jej obecność w danych byłaby usterką, a nie jej brak.
    w_danych = klasy_w_danych()
    assert w_danych.get("est", 0) == 0, (
        "w danych pojazdu pojawiła się klasa `est` (%d razy) — dokument opisuje ją "
        "jako oszacowanie DO USUNIĘCIA" % w_danych.get("est", 0))
    assert set(w_danych) == {"spec", "design_model"}, (
        "rozkład klas w danych pojazdu zmienił się: %s" % sorted(w_danych))


# 6.D25: uruchomienie tego pliku WPROST idzie tą samą drogą, co cały zestaw.
if __name__ == "__main__":
    sys.path.insert(0, os.path.join(ROOT, "tools", "tests"))
    import test_all
    raise SystemExit(test_all.main(__file__))
