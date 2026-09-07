#!/usr/bin/env python3
"""Raport, który podaje wartość stałej, musi podawać tę, która jest w kodzie.

**Skąd ta bramka.** Docstring `tools/tests/test_readme_claims.py` zapisał regułę,
która okazała się szersza niż README: „liczba stojąca w jednym miejscu i nigdzie nie
liczona **rozjeżdża się bezszelestnie**". `reports/` jest dziś dokładnie takim
miejscem — 48 plików, ani jednej pętli po liczbach.

**Czego ta bramka świadomie NIE sprawdza, i to jest jej najważniejsza granica.**
Większość liczb w raportach to **datowane pomiary**, których się nie przelicza
(`tools/tests/test_report_hygiene.py` trzyma tę zasadę od 6.D3). Zmierzone
06.09.2026 na ośmiu twierdzeniach postaci „`plik_testowy.py`, N testów":
**siedem z ośmiu rozjechało się z drzewem**, na przykład `test_lod.py` — raport mówi
50, plik ma 75. I to jest **poprawne**: raport opisywał plik w dniu pomiaru, a plik
od tamtej pory urósł. Bramka żądająca tam równości kazałaby przepisywać datowany
pomiar przy każdym dopisanym teście, czyli robić dokładnie to, czego zakazuje 6.D3.

Sprawdzalna jest natomiast **wartość stałej**. Nie jest pomiarem: albo zgadza się
z kodem, albo raport wysyła czytelnika po nieistniejący próg. Ta różnica — między
„ile było wtedy" a „ile wynosi ta stała" — jest jedyną, na której ten moduł stoi.

**Zasada, ta sama co w `test_readme_claims.py`:** nie ma tu ani jednej oczekiwanej
liczby. Prawdę czyta `WARTOSC_W_KODZIE` z `tools/` i `src/`; raport jest stroną
porównywaną, nigdy źródłem.
"""
import glob
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
REPORTS = os.path.join(ROOT, "reports")
SOURCE_DIRS = ("tools", "src")
SKIP_DIRS = ("/bin", "/obj", "/__pycache__", "/.git")

#: Definicja stałej liczbowej — Python (`NAZWA = 1.5`) i C# (`public const double
#: Nazwa = 1.5;`). Tylko WIELKIE_Z_PODKREŚLENIAMI, bo tylko takie nazwy raporty
#: cytują jako progi; `PascalCase` z C# jest nieodróżnialny od nazwy typu.
DEFINITION = re.compile(
    r"^\s*(?:public\s+(?:static\s+)?(?:readonly\s+)?(?:const\s+)?[A-Za-z<>?\[\]]+\s+)?"
    r"([A-Z][A-Z0-9_]{3,})\s*=\s*([-+0-9][0-9_.eE+-]*)\s*[;,)]?\s*(?:#|//|$)")

#: WZORZEC TWIERDZENIA — i jego zwężenie jest tu całą robotą.
#:
#: Wersja pierwsza brała „nazwa w grawisach, potem dowolna liczba w promieniu 80
#: znaków" i dała **3 fałszywe alarmy na 15 trafień** (20 %). Wszystkie trzy z tego
#: samego powodu: raport wymieniał stałe w tabeli odwzorowań `219 → NAZWA, 237 → INNA`,
#: a wzorzec brał numer wiersza NASTĘPNEJ pary jako wartość poprzedniej.
#:
#: Zwężenie: między nazwą a liczbą nie wolno postawić **przecinka, strzałki ani
#: grawisu**. To wycina wyliczenia i tabele odwzorowań, a zostawia wszystkie cztery
#: postacie, w których raporty naprawdę podają wartość:
#:     `M7_WIDTH_M` 2,70                      — nazwa i liczba obok siebie
#:     `SLAB_GROWTH_STEPS` = 6                — ze znakiem równości
#:     `PARALLEL_M` jest granicą włącznie: 30,0 m
#:     Szerokość równa `RUNNING_TUNNEL_MAX_M` (15,0 m)
#: Zmierzone 06.09.2026: 12 trafień, 0 rozjazdów, 0 fałszywych alarmów.
CLAIM = re.compile(r"`([A-Z][A-Z0-9_]{3,})`([^`,→\n]{0,40}?)(-?\d+(?:[.,]\d+)?(?:e-?\d+)?)")

#: Ile twierdzeń wzorzec ma znaleźć, żeby pomiar był pomiarem. Bez tego progu
#: literówka we WZORCU dałaby zero trafień, zero rozjazdów i zieloną bramkę — ta sama
#: pułapka, którą `test_report_hygiene.py` zamyka progiem `seen >= 500`. Zmierzone
#: 06.09.2026: **12**; próg stoi niżej, żeby nie ruszać go przy każdym raporcie.
MINIMUM_CLAIMS = 10

#: JAWNE WYJĄTKI: `(raport, nazwa stałej)`, gdzie raport słusznie podaje inną liczbę.
#: Pusto — i to jest wynik pomiaru, nie założenie. Pierwszy wyjątek wchodzi tu
#: z powodem i zostaje objęty testem „nie gnije", tak samo jak `PATH_EXCEPTIONS`
#: w `test_report_hygiene.py`.
CLAIM_EXCEPTIONS = set()


def _source_files():
    for where in SOURCE_DIRS:
        for base, _dirs, files in os.walk(os.path.join(ROOT, where)):
            if any(skip in base for skip in SKIP_DIRS):
                continue
            for name in sorted(files):
                if name.endswith((".py", ".cs")):
                    yield os.path.join(base, name)


def constant_values():
    """`{NAZWA: wartość}` dla stałych zdefiniowanych w drzewie **jednoznacznie**.

    Nazwa zdefiniowana w dwóch miejscach z różnymi wartościami wypada: raport cytujący
    taką stałą nie ma jednej prawdy do porównania, a zgadywanie, którą miał na myśli,
    byłoby gorsze od milczenia.
    """
    seen = {}
    for path in _source_files():
        with open(path, encoding="utf-8", errors="ignore") as handle:
            for line in handle:
                found = DEFINITION.match(line)
                if found:
                    seen.setdefault(found.group(1), set()).add(found.group(2))
    return {name: next(iter(values)) for name, values in seen.items() if len(values) == 1}


def _same_number(from_report, from_code):
    """Czy liczba z raportu i z kodu to ta sama wartość. Przecinek dziesiętny wchodzi."""
    try:
        return abs(float(from_report.replace(",", ".")) - float(from_code)) < 1e-12
    except ValueError:
        return False


#: Ogrodzenie bloku kodu. Wiersze między jednym a drugim są CYTATEM — wyjściem
#: polecenia, kontrolą negatywną, fragmentem źródła — a nie twierdzeniem raportu
#: o stanie drzewa.
#:
#: SKĄD TEN WARUNEK. Pierwsza wersja bramki wywróciła się na własnym raporcie:
#: `reports/report-claims-audit.md` cytuje w bloku kodu wyjście swojej kontroli
#: negatywnej, w którym stoi „`BACKGROUND_TOLERANCE` mówi 0,03, kod 0.02" — i wzorzec
#: przeczytał cytat z sabotażu jako twierdzenie. Klasa jest szersza niż ten jeden
#: przypadek: każdy raport triażu cytuje wyjścia poleceń, a te zawierają liczby, które
#: BYŁY nieprawdziwe z założenia.
FENCE = re.compile(r"^\s*```")


def claims_in_reports(values):
    """`(raport, wiersz, nazwa, liczba z raportu, wartość z kodu)` dla każdego trafienia.

    Bloki ogrodzone ``` są pomijane: to cytaty, nie twierdzenia.
    """
    for path in sorted(glob.glob(os.path.join(REPORTS, "*.md"))):
        name = os.path.basename(path)
        with open(path, encoding="utf-8") as handle:
            w_bloku = False
            for number, line in enumerate(handle.read().splitlines(), 1):
                if FENCE.match(line):
                    w_bloku = not w_bloku
                    continue
                if w_bloku:
                    continue
                for constant, _between, said in CLAIM.findall(line):
                    if constant in values:
                        yield name, number, constant, said, values[constant]


def test_every_constant_quoted_in_a_report_carries_the_value_from_the_code():
    """Raport podający wartość stałej podaje tę, która jest w kodzie.

    Kontrola negatywna WYKONANA 06.09.2026, na kopii `reports/` w katalogu roboczym:
    po zmianie w `reports/mutation-triage-wizualna.md` liczby przy
    `BACKGROUND_TOLERANCE` z 0,02 na 0,03 test pada komunikatem

        raporty podają inną wartość niż kod:
        ['mutation-triage-wizualna.md:54: `BACKGROUND_TOLERANCE` mówi 0,03, kod 0.02']
    """
    values = constant_values()
    wrong = []
    checked = 0
    for name, number, constant, said, actual in claims_in_reports(values):
        checked += 1
        if (name, constant) in CLAIM_EXCEPTIONS:
            continue
        if not _same_number(said, actual):
            wrong.append(f"{name}:{number}: `{constant}` mówi {said}, kod {actual}")
    assert not wrong, f"raporty podają inną wartość niż kod: {wrong}"
    assert checked >= MINIMUM_CLAIMS, (
        f"wzorzec znalazł tylko {checked} twierdzeń przy progu {MINIMUM_CLAIMS} — "
        "przestał łapać, a zielona bramka na zerze trafień nic nie mierzy")


def test_the_claim_pattern_takes_values_and_leaves_mapping_tables_alone():
    """Kontrola detektora: cztery postacie, które mają wejść, i trzy, które nie.

    Bez tego testu bramka wyżej byłaby zielona zarówno przy martwym wzorcu, jak i przy
    wzorcu z powrotem rozszerzonym do wersji, która dawała 20 % fałszywych alarmów.
    """
    def found(line):
        return [(n, v) for n, _b, v in CLAIM.findall(line)]

    # 1–4. Cztery postacie, w których raporty naprawdę podają wartość.
    assert found("`M7_WIDTH_M` 2,70 i nic więcej") == [("M7_WIDTH_M", "2,70")]
    assert found("* `SLAB_GROWTH_STEPS` = 6 nie jest progiem") == [("SLAB_GROWTH_STEPS", "6")]
    assert found("`PARALLEL_M` jest granicą włącznie: 30,0 m") == [("PARALLEL_M", "30,0")]
    assert found("Szerokość równa `RUNNING_TUNNEL_MAX_M` (15,0 m)") == [
        ("RUNNING_TUNNEL_MAX_M", "15,0")]

    # 5. Tabela odwzorowań „wiersz → stała". To jest ten przypadek, który dawał
    #    fałszywe alarmy: 237 jest numerem wiersza NASTĘPNEJ pary, nie wartością.
    assert found("219 → `DEFAULT_MAX_CHUNK_M`, 237 → `DEFAULT_STATION_HALO_M`") == []
    # 6. Odsyłacz z nazwą stałej w nawiasie, liczba w innym zdaniu.
    assert found("(wiersz `DEFAULT_RING_STEP_M`) podnosił próg → 0,1064") == []
    # 7. Nazwa bez żadnej liczby po niej.
    assert found("stała `CLEARANCE_M` jest opisana wyżej") == []


def test_a_number_quoted_inside_a_code_block_is_not_a_claim():
    """Cytat z wyjścia polecenia nie jest twierdzeniem raportu o stanie drzewa.

    Bramka wywróciła się na tym przy pierwszym przebiegu, na własnym raporcie:
    `reports/report-claims-audit.md` cytuje w bloku kodu wyjście swojej kontroli
    negatywnej, a w nim stoi liczba, która **z założenia** jest nieprawdziwa.
    Bez pomijania bloków każdy raport triażu zapalałby tę bramkę własnymi cytatami.
    """
    import tempfile
    with tempfile.TemporaryDirectory() as katalog:
        sciezka = os.path.join(katalog, "przyklad.md")
        with open(sciezka, "w", encoding="utf-8") as handle:
            handle.write(
                "Poza blokiem: `M7_WIDTH_M` 2,70 — to jest twierdzenie.\n"
                "```\n"
                "FAIL: `M7_WIDTH_M` mówi 9,99, kod 2.70\n"
                "```\n"
                "Znowu poza blokiem: `CLEARANCE_M` 0,30.\n")
        globalny = REPORTS
        try:
            globals()["REPORTS"] = katalog
            trafienia = [(c, said) for _n, _w, c, said, _a in claims_in_reports(
                {"M7_WIDTH_M": "2.70", "CLEARANCE_M": "0.30"})]
        finally:
            globals()["REPORTS"] = globalny
    assert trafienia == [("M7_WIDTH_M", "2,70"), ("CLEARANCE_M", "0,30")], trafienia


def test_the_constant_reader_finds_both_languages_and_refuses_the_ambiguous():
    """Kontrola czytnika kodu: bez niej pusty słownik dałby zielone wszystko."""
    values = constant_values()
    assert len(values) > 100, f"czytnik znalazł tylko {len(values)} stałych"
    # Wartości z obu języków, sprawdzone na stałych, które są w drzewie od dawna.
    assert values["M7_WIDTH_M"] == "2.70", values.get("M7_WIDTH_M")
    assert values["DEFAULT_MAX_CHUNK_M"] == "800.0", values.get("DEFAULT_MAX_CHUNK_M")
    # Wzorzec definicji nie łapie wywołania ani porównania.
    assert DEFINITION.match("PROG_M = 1.5") is not None
    assert DEFINITION.match("    if PROG_M == 1.5:") is None
    assert DEFINITION.match("wynik = policz(PROG_M)") is None


def test_the_claim_exception_list_does_not_rot():
    """Wyjątek, który przestał być potrzebny, ma z listy ZNIKNĄĆ.

    Dziś lista jest pusta i ten test sprawdza to wprost: pustka jest wynikiem pomiaru
    („żaden raport nie potrzebuje wyjątku"), a nie miejscem, w którym nic jeszcze nie
    zdążyło się nazbierać.
    """
    values = constant_values()
    zbedne = []
    for report, constant in CLAIM_EXCEPTIONS:
        pasuje = [c for c in claims_in_reports(values)
                  if c[0] == report and c[2] == constant and not _same_number(c[3], c[4])]
        if not pasuje:
            zbedne.append(f"{report}:{constant}")
    assert not zbedne, f"wyjątki bez powodu — zdejmij je: {zbedne}"

# 6.D25: uruchomienie tego pliku WPROST idzie ta sama droga, co caly zestaw —
# z licznikiem asercji i z odmowa przy zerze testow. Bez tej gałęzi `python3
# tools/tests/<modul>.py` konczyl sie kodem 0, nie wykonawszy ani jednego testu.
if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))
