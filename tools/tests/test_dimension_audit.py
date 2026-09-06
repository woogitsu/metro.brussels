#!/usr/bin/env python3
"""Audyt wymiarów: żaden parametr geometrii nie może istnieć bez wpisu w dokumencie.

Reguła 1 z `CLAUDE.md` mówi, żeby nie zgadywać danych o sieci. Egzekwowanie tego przez
dobre chęci nie działa — zmyślona głębokość stacji wygląda dokładnie tak samo jak
prawdziwa. Ten test pilnuje, żeby każda stała, na której stoi geometria, była wypisana
w `docs/21-measured-vs-assumed.md` razem ze statusem. Dopisanie parametru bez wpisu
wywraca testy, więc autor musi świadomie zadeklarować, czy to fakt, czy decyzja.

Od 04.09.2026 audyt patrzy też na `docs/TASKS.md` — sekcja „długość peronu w prozie"
na końcu pliku. Powód jest wypisany tam, przy stałej `PLATFORM_LENGTH_PROSE`.
"""
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "blender"))

import m7_layout  # noqa: E402
import profiles  # noqa: E402
import station_components  # noqa: E402
import sweep  # noqa: E402

AUDIT = os.path.join(ROOT, "docs", "21-measured-vs-assumed.md")
STATUSES = ("spec", "observed", "design_assumption", "blocked")


def _audit_text():
    with open(AUDIT, encoding="utf-8") as handle:
        return handle.read()


def test_audit_document_exists_and_defines_every_status():
    text = _audit_text()
    for status in STATUSES:
        assert f"`{status}`" in text, status


def test_audit_covers_every_m7_design_constant():
    text = _audit_text()
    constants = [n for n in dir(m7_layout)
                 if n.startswith("DESIGN_") and n != "DESIGN_ASSUMPTIONS"]
    assert len(constants) >= 10, constants
    missing = [n for n in constants if n not in text]
    assert not missing, f"stałe bez wpisu w audycie: {missing}"


def test_audit_covers_every_m7_spec_key():
    text = _audit_text()
    spec = m7_layout.load_spec()
    numeric = {k: v for k, v in spec.items() if isinstance(v, (int, float))}
    missing = [k for k, v in numeric.items() if _format(v) not in text]
    assert not missing, f"wartości ze specyfikacji bez wpisu: {missing}"


def test_audit_covers_every_tunnel_profile_with_its_size():
    text = _audit_text()
    for name in profiles.PROFILES:
        assert f"`{name}`" in text, name
        width, height = profiles.dimensions(name)
        pair = f"{_dimension(width)} × {_dimension(height)} m"
        assert pair in text, f"{name}: brak wymiarów {pair} w audycie"


def test_audit_covers_every_sweep_constant():
    text = _audit_text()
    names = [n for n in dir(sweep)
             if n.startswith("DEFAULT_") or n in ("UV_METRES_PER_UNIT", "DEGENERATE_AREA_M2")]
    assert len(names) >= 6, names
    missing = [n for n in names if n not in text]
    assert not missing, f"stałe generatora bez wpisu: {missing}"


def test_audit_marks_profiles_as_design_not_measurement():
    """Profile są projektowe. Audyt musi to mówić wprost, a kod się z tym zgadzać."""
    text = _audit_text()
    for name, spec in profiles.PROFILES.items():
        assert spec["source_level"] == "design", name
    assert "Żaden nie jest pomiarem STIB" in text


def test_audit_records_the_measured_alternatives_that_were_not_applied():
    """Zmierzone alternatywy mają być wypisane RAZEM z powodem, dla którego nie weszły."""
    text = _audit_text()
    for marker in ("8,77", "3,294", "R-005"):
        assert marker in text, marker
    assert profiles.PROFILES["box_double"]["track_offsets"] == [-2.10, 2.10], \
        "rozstaw zmieniony w kodzie — audyt trzeba zaktualizować razem ze zmianą"
    width, _height = profiles.dimensions("box_double")
    assert abs(width - 9.40) < 1e-9, \
        "szerokość profilu zmieniona — audyt trzeba zaktualizować razem ze zmianą"


def test_audit_lists_what_is_blocked_and_by_what():
    text = _audit_text()
    for marker in ("T-112", "R-004", "R-005", "flat-preview"):
        assert marker in text, marker


def _row(text, name):
    """Wiersz tabeli audytu opisujący daną stałą, albo None."""
    for line in text.splitlines():
        if line.startswith("|") and f"`{name}`" in line.split("|")[1]:
            return [cell.strip() for cell in line.strip("|").split("|")]
    return None


def _documented_value(cell):
    """Druga kolumna wiersza jako liczba albo wartość logiczna.

    Dokument zapisuje liczby po polsku i z jednostką, w różnej liczbie miejsc
    po przecinku (`2,40 m`, `5,0 m`, `1e-06`), więc porównanie idzie po WARTOŚCI,
    a nie po napisie — inaczej test wywracałby się na formatowaniu zamiast
    na rozjeździe kodu z dokumentem.
    """
    raw = cell.replace("`", "").replace("\u00a0", " ").strip()
    if raw in ("True", "False"):
        return raw == "True"
    raw = raw.split(" ")[0].replace(",", ".")
    return float(raw)


def _assert_values_match(text, module, names):
    mismatched = []
    for name in names:
        row = _row(text, name)
        assert row is not None, f"brak wiersza dla {name} w audycie"
        assert len(row) >= 2, (name, row)
        expected = getattr(module, name)
        found = _documented_value(row[1])
        if isinstance(expected, bool) or isinstance(found, bool):
            if bool(expected) != bool(found):
                mismatched.append(f"{name}: kod {expected}, audyt {found}")
        elif abs(float(found) - float(expected)) > 1e-12:
            mismatched.append(f"{name}: kod {expected}, audyt {found}")
    assert not mismatched, mismatched


def test_audit_records_the_value_of_every_m7_design_constant():
    """Nie tylko NAZWA stałej ma być w dokumencie, ale jej WARTOŚĆ.

    Zmierzone 02.09.2026 audytem mutacyjnym: `DESIGN_NOSE_LENGTH_M` 2,40 -> 6,00,
    `DESIGN_SHELL_THICKNESS_M` 0,08 -> 0,50 i pięć innych przechodziło przez całą
    suitę, bo test szukał w dokumencie samej nazwy. Docstring tego pliku mówi
    wprost, po co on jest — „zmyślona głębokość stacji wygląda dokładnie tak samo
    jak prawdziwa" — a w tej postaci pozwalał kodowi i dokumentowi rozjechać się
    co do liczby. Dla profili tuneli było to zrobione dobrze od początku
    (`test_audit_covers_every_tunnel_profile_with_its_size`); asymetria była
    przypadkowa.
    """
    text = _audit_text()
    names = [n for n in dir(m7_layout)
             if n.startswith("DESIGN_") and n != "DESIGN_ASSUMPTIONS"]
    assert len(names) >= 10, names
    _assert_values_match(text, m7_layout, names)


def test_audit_records_the_value_of_every_sweep_constant():
    """To samo dla domyślnych wartości generatora tuneli.

    Te stałe są domyślnymi wartościami CLI, a każdy test podaje wartość jawnie
    w wywołaniu — więc testują algorytm, ale nie liczbę, którą realnie dostaje
    pipeline. Zmierzone: `DEFAULT_RING_STEP_M` 5,0 -> 50,0,
    `DEFAULT_STATION_HALO_M` 90,0 -> 5,0, `DEFAULT_MIN_CHUNK_M` 120 -> 1,
    `DEFAULT_MAX_CHUNK_M` 800 -> 80000, `UV_METRES_PER_UNIT` 4,0 -> 40,0 —
    wszystkie przechodziły.
    """
    text = _audit_text()
    names = [n for n in dir(sweep)
             if n.startswith("DEFAULT_") or n in ("UV_METRES_PER_UNIT", "DEGENERATE_AREA_M2")]
    assert len(names) >= 6, names
    _assert_values_match(text, sweep, names)


def _dimension(value):
    """Wymiary profili zapisujemy w dokumencie z dwoma miejscami, po polsku."""
    return f"{value:.2f}".replace(".", ",")


def _format(value):
    """Liczby w dokumencie są zapisane po polsku, z przecinkiem dziesiętnym."""
    if isinstance(value, float) and value != int(value):
        return f"{value}".replace(".", ",")
    return str(int(value)) if isinstance(value, float) else str(value)


def test_audit_covers_every_station_component_constant():
    """Stała projektowa bez wpisu w audycie jest liczbą, która udaje pomiar.

    T-212 dokłada siedemnaście takich stałych naraz — schody, winda, antresola,
    korytarz, portal — i żadna nie ma źródła. To jest dokładnie ta sytuacja, dla
    której audyt powstał: dużo liczb naraz, wszystkie brzmiące rozsądnie, żadna
    nie pochodząca ze STIB.
    """
    text = _audit_text()
    constants = [n for n in dir(station_components)
                 if n.startswith("DESIGN_") and n != "DESIGN_ASSUMPTIONS"]
    assert len(constants) >= 15, constants
    missing = [n for n in constants if f"`{n}`" not in text]
    assert not missing, f"stałe T-212 bez wpisu w audycie: {missing}"
    assert "design_assumption" in text


# --- długość peronu w prozie -----------------------------------------------------

TASKS = os.path.join(ROOT, "docs", "TASKS.md")

#: Dokumenty, w których długość peronu z generatora stoi jako liczba w zdaniu, a nie
#: jako wynik czegokolwiek. `docs/21` audyt sprawdzał od początku, `docs/TASKS.md` nie —
#: i dlatego wiersz „Co blokuje co" niósł 94,0 m przez dwa dni po decyzji T-212 (#137),
#: podczas gdy generator, `docs/21` §4e i `reports/T-212-station.md` miały 95,0 m.
#: 94,0 m to długość składu M7, czyli DOLNE OGRANICZENIE z R-007, a nie parametr —
#: liczba wyglądała więc sensownie i nic jej nie porównywało.
PLATFORM_LENGTH_PROSE = (AUDIT, TASKS)

#: Zdania, które przedstawiają liczbę jako parametr peronu w generatorze.
#:
#: WZORZEC I JEGO ZWĘŻENIE — metodą z `tools/tests/test_report_claims.py`, czyli
#: pomiarem przed i po, nie przeczuciem.
#:
#: Wersja pierwsza brała **goły napis „jawny parametr"** i żądała od takiego wiersza
#: wartości 95,0 m. To nie jest wzorzec na długość peronu, tylko na dowolny parametr:
#: „jawny parametr" jest w tym repozytorium zwrotem technicznym o wszystkim, co zostało
#: wystawione zamiast zgadnięte. Zmierzone 06.09.2026 na korpusie bramki
#: (`PLATFORM_LENGTH_PROSE`) w brzmieniu sprzed obejścia: **5 trafień, 1 fałszywe** —
#: zdanie z bloku 6.A5 `docs/TASKS.md` o **udziale odzysku energii** („dwa warianty
#: skrajne, 0 % i 100 %, jako jawny parametr") zapaliło bramkę długości peronu. Autor
#: #272 obszedł to przeformułowaniem **własnej prozy**, co jest ceną płaconą przez
#: teksty, które z peronem nie mają nic wspólnego.
#:
#: Zwężenie: sam zwrot już nie wystarcza. Wchodzi wiersz, który albo **nazywa stałą**
#: (`DESIGN_PLATFORM_LENGTH_M`, także z przedrostkiem `SC.` — nazwa jest jednoznaczna
#: sama w sobie), albo **mówi o peronie** i dopiero wtedy nazywa go jawnym parametrem.
#: Odmiana zwrotu wchodzi (`jawn\w+ parametr\w*`), bo „jest jawnym parametrem" znaczy
#: dokładnie to samo co „ma jawny parametr", a wersja pierwsza tej formy nie łapała.
#: Zmierzone na tym samym korpusie: **4 trafienia, 0 fałszywych, 0 utraconych
#: prawdziwych**. Poglądowo na `docs/` + `reports/` (85 plików, poza korpusem bramki):
#: 18 → 14; cztery zdjęte to trzy wiersze **o samym wzorcu** w raportach 6.D4 i #272
#: oraz jeden akapit `reports/T-212-station.md`, w którym „jawny parametr" i słowo
#: „peron" rozeszły się na dwa wiersze przez zawinięcie tekstu.
#:
#: `re.IGNORECASE`, bo „Peron w generatorze…" na początku zdania jest tym samym
#: zdaniem co „…peron w generatorze…" w środku, a wielkość litery zależy tu wyłącznie
#: od tego, gdzie autor zaczął akapit.
NAMES_THE_PLATFORM_PARAMETER = re.compile(
    r"DESIGN_PLATFORM_LENGTH_M"
    r"|peron\w* w generatorze"
    r"|^(?=.*\bperon)[^\n]*jawn\w+ parametr\w*",
    re.IGNORECASE)

#: „…jawny parametr 95,0 m…" — sama liczba podana jako wartość parametru.
#: Ten wzorzec zostaje szeroki ŚWIADOMIE i to jest różnica mierzalna, nie gust: żąda
#: wartości **w metrach**, więc zdanie o udziale odzysku („0 % i 100 %") go nie zapala,
#: a wiersz „generator dostał jawny parametr 94,0 m" bez słowa „peron" zostaje po
#: zwężeniu wyżej jedyną rzeczą, która taki wiersz jeszcze widzi.
PARAMETER_VALUE = re.compile(r"jawny parametr \*{0,2}(\d+,\d+) m")


def _polish(value):
    return f"{value:.1f}".replace(".", ",")


def _prose_lines():
    for path in PLATFORM_LENGTH_PROSE:
        with open(path, encoding="utf-8") as handle:
            for number, line in enumerate(handle.read().splitlines(), 1):
                yield path, number, line


def test_prose_naming_the_platform_parameter_carries_the_value_from_the_code():
    """Zdanie o parametrze peronu niesie liczbę, którą ma generator.

    Kontrola negatywna WYKONANA 06.09.2026 po zwężeniu wzorca, dwa razy, oba na
    `docs/21-measured-vs-assumed.md`, plik za każdym razem przywrócony.

    1. Wartość w wierszu tabeli 95,0 -> 94,0 m:

        FAIL test_prose_naming_the_platform_parameter_carries_the_value_from_the_code:
        długość peronu inna niż 95,0 m w kodzie:
        ['docs/21-measured-vs-assumed.md:290: | `DESIGN_PLATFORM_LENGTH_M` | 94,0 m |
        długość peronu, na której stoi zespół dostępu — decyzja właściciela
        z 04.09.2026 (patrz akapit niżej) |']

    2. Zdanie dopisane **bez nazwy stałej**, samym zwrotem w odmianie — kontrola, że
       zwężenie nie zeszło do „szukaj `DESIGN_PLATFORM_LENGTH_M`" i że gałąź
       współwystąpienia naprawdę strzela:

        FAIL test_prose_naming_the_platform_parameter_carries_the_value_from_the_code:
        długość peronu inna niż 95,0 m w kodzie:
        ['docs/21-measured-vs-assumed.md:293: Dla peronu generator dostał wartość
        jawnym parametrem: 94,0 m.']

       Wzorca sprzed zwężenia tego zdania **nie łapał** — „jawnym parametrem" nie jest
       napisem „jawny parametr". Zwężenie o odmianę jest więc zarazem rozszerzeniem
       zasięgu na zdania o peronie.
    """
    expected = _polish(station_components.DESIGN_PLATFORM_LENGTH_M)
    seen = {path: 0 for path in PLATFORM_LENGTH_PROSE}
    offenders = []
    for path, number, line in _prose_lines():
        if not NAMES_THE_PLATFORM_PARAMETER.search(line):
            continue
        seen[path] += 1
        if expected not in line:
            offenders.append(f"{os.path.relpath(path, ROOT)}:{number}: {line.strip()[:160]}")
    assert not offenders, f"długość peronu inna niż {expected} m w kodzie: {offenders}"
    missing = [os.path.relpath(p, ROOT) for p, count in seen.items() if count == 0]
    assert not missing, f"zdanie o parametrze peronu zniknęło — bramka przestałaby patrzeć: {missing}"


def test_the_platform_pattern_takes_platform_sentences_and_leaves_the_rest_alone():
    """Kontrola detektora: co ma wejść i co ma NIE wejść, zdanie po zdaniu.

    Bez tego testu bramka wyżej jest zielona zarówno przy wzorcu martwym, jak i przy
    wzorcu rozszerzonym z powrotem do gołego „jawny parametr" — a wtedy każde zdanie
    o dowolnym parametrze znów zaczyna być mierzone długością peronu.
    """
    def lapie(line):
        return NAMES_THE_PLATFORM_PARAMETER.search(line) is not None

    # WCHODZĄ — cztery postacie zmierzone w korpusie bramki 06.09.2026.
    assert lapie("| `DESIGN_PLATFORM_LENGTH_M` | 95,0 m | długość peronu … |")
    assert lapie("- **Kontrola R-007 jest w kodzie:** `SC.DESIGN_PLATFORM_LENGTH_M` = 95,0 m")
    assert lapie("bo `--platform-length-m design` czyta 95,0 m z `SC.DESIGN_PLATFORM_LENGTH_M`")
    assert lapie("| ~~długość peronu~~ | generator ma jawny parametr 95,0 m (T-212) |")
    # WCHODZI ODMIANA — „jest jawnym parametrem" znaczy to samo; wersja pierwsza
    # wzorca łapała wyłącznie mianownik i takie zdanie przepuszczała.
    assert lapie("długość peronu jest jawnym parametrem generatora: 95,0 m")
    # WCHODZI trzecia postać, ta z wcześniejszego brzmienia raportu T-400 — i ta sama
    # od wielkiej litery, bo o tym decyduje tylko miejsce w akapicie.
    assert lapie("peron w generatorze ma 95,0 m (R-007 daje kontrolę górną 109,1 m)")
    assert lapie("Peron w generatorze ma 95,0 m, a dolne ograniczenie to 94,0 m")

    # NIE WCHODZI — zdanie z bloku 6.A5 `docs/TASKS.md`, dla którego ta pozycja
    # powstała: mówi o udziale odzysku energii, a zapalało bramkę długości peronu.
    assert not lapie(
        "  wariantów skrajnych odzysku, 0 % i 100 %**, jako jawny parametr — dokładnie")
    # NIE WCHODZI — udział osi hamowanych, `docs/TASKS.md` wiersz 213. Drugi parametr
    # tej samej klasy, dziś w odmianie, którą zwężony wzorzec musi rozpoznawać
    # w zdaniach o peronie i mijać w każdym innym.
    assert not lapie(
        "  Udział osi hamowanych jest jawnym parametrem o dwóch wariantach skrajnych")
    # NIE WCHODZI — meta-zdanie o samej bramce; takich są w `reports/` trzy.
    assert not lapie('łapie sam napis „jawny parametr" i przy #272 zapalił się na zdaniu')
    # NIE WCHODZI — peron bez ani jednego słowa o parametrze.
    assert not lapie("Peron najciaśniejszej stacji sieci leży w łuku R = 97,11 m")


def test_no_document_calls_a_different_number_the_explicit_platform_parameter():
    """Osobno od testu wyżej: łapie liczbę PODANĄ jako wartość parametru.

    Test wyżej wymaga obecności 95,0 m w zdaniu; ten wymaga, żeby przy słowach
    „jawny parametr" nie stała inna liczba. Wiersz z 04.09.2026 przechodziłby pierwszy
    z nich, gdyby ktoś dopisał 95,0 m obok pozostawionego 94,0 m.
    """
    expected = _polish(station_components.DESIGN_PLATFORM_LENGTH_M)
    offenders = []
    for path, number, line in _prose_lines():
        for found in PARAMETER_VALUE.findall(line):
            if found != expected:
                offenders.append(
                    f"{os.path.relpath(path, ROOT)}:{number}: „jawny parametr {found} m", )
    assert not offenders, f"kod ma {expected} m: {offenders}"
