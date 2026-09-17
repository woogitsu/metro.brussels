#!/usr/bin/env python3
"""Liczba wpisana w KOMUNIKAT asercji nie jest pilnowana przez nic (6.D255).

**Skąd ta bramka.** Twierdzenia liczbowe w `reports/` pilnuje `claims_in_reports()`
z `test_report_claims.py`, a w `README.md` — `test_readme_claims.py`. Komunikatów
asercji pod `tools/tests/` nie czytał do 17.09.2026 ani jeden czytnik, choć są to
zdania pisane w tym samym trybie i starzejące się z tej samej przyczyny: kod obok
nich rośnie, a proza zostaje.

**Zmierzone 17.09.2026 na całym drzewie.** Komunikatów asercji z napisem: **2668**.
Literałów liczbowych w nich, po zdjęciu specyfikatorów `%`: **418**, w **234**
komunikatach. Z tego **19** to twierdzenia o dzisiejszym stanie repozytorium,
a **cztery były nieprawdziwe**:

* `test_assertion_gate.py` mówił **849** przy 925 w drzewie — a docstring obok
  ogłaszał tę liczbę „strażnikiem listy, a nie ozdobą";
* `test_report_claims.py` mówił **32** nagłówki przy 39 w katalogu;
* `test_runner_options.py` mówił **27 testów** `RunPlan` przy 61 w pliku
  (i 318 w całym `tests/Game.Tests`);
* `test_clearance_profile.py` mówi „**6700** m, czyli na realnej długości pakietu
  A", a `data/track/L1_A.json` podaje 6686,35 m.

Trzy pierwsze poprawiono tym samym commitem: liczba jest teraz PODSTAWIANA z kodu
albo znika, bo nie była treścią zdania. **Czwartego ta bramka nie złapie i to jest
zmierzona granica, nie przeoczenie:** 6700 stoi w samym warunku asercji jako podstawa
arytmetyczna zmiennoprzecinkowa i jest tam poprawne; nieprawdziwy jest przymiotnik
„realnej". Żadna bramka licząca liczby tego nie zobaczy.

**Dlaczego nie da się pożyczyć czytnika z `test_report_claims` (6.D213).** Próbowano
najpierw tego, bo pożyczka jest tańsza od drugiej kopii. Wzorzec `CLAIM` szuka nazwy
stałej w grawisach, po której stoi liczba — kształt, który w komunikatach asercji
nie występuje. Puszczony na wszystkie 2652 komunikaty dał **dwa** trafienia i **oba
były artefaktem specyfikatora formatu**: `%d.` dało „-00", a `%.4f` dało „4".
Pożyczka jest więc wykluczona POMIAREM, a nie uznana za niewygodną.

**Jak działa sito.** Literał w komunikacie ma POKRYCIE, gdy zachodzi cokolwiek z tego:

* stoi jako literał w samym warunku tej asercji (`assert len(x) == 18` i „jest 18"),
* stoi w ciele testu dwadzieścia wierszy nad asercją — także w innej skali
  (2 cm ↔ `0.02`, 0,5 mm ↔ `1.0005`), bo komunikat opisuje tę samą wielkość
  w jednostce, w której się o niej mówi,
* stoi tuż za znakiem odsyłacza (`§`, `#`, `docs/NN-`, `MB-NN`, `T-NNN`, `kodem`,
  `Ubuntu`), czyli jest numerem czegoś, a nie wielkością,
* albo komunikat niesie datę — wtedy jest zdaniem o dniu pomiaru (6.D108),
  a nie o dziś.

Sito zdejmuje **374 z 418**; zostaje **44 wystąpienia w 41 parach** `(plik, liczba)`.
Reszta stoi niżej z powodem, bo listy wyjątków, której nikt nie sprawdza, ten projekt
nie uznaje za bramkę (6.D243) — dlatego jest porównywana z drzewem W OBIE STRONY.

**Sito samo raz skłamało i to jest zapisane, a nie poprawione po cichu.** W pierwszej
wersji okno „dwadzieścia wierszy nad asercją" obejmowało też **wiersz samej asercji**,
więc liczba z komunikatu pokrywała SAMĄ SIEBIE: sito zostawiało 34 zamiast 44 i
wyglądało na skuteczniejsze, niż jest. Złapała to kontrola przyrządu na wejściu
syntetycznym przy pierwszym przebiegu modułu — dokładnie po to jest.
"""
import ast
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tree_walk as TW  # noqa: E402

#: Specyfikator `%`-formatu. Zdejmowany PRZED szukaniem liczb, bo inaczej `%.4f`
#: jest czytane jako twierdzenie „4" — tak właśnie pomylił się czytnik z
#: `test_report_claims` puszczony na ten korpus.
SPECYFIKATOR = re.compile(r"%[-+ #0]*[\d.*]*[hlL]?[diouxXeEfFgGcrsa%]")

#: Liczba w prozie: nie fragment identyfikatora, nie część słowa.
LICZBA = re.compile(r"(?<![\w.])(\d+(?:[.,]\d+)?)(?![\w.])")

#: Co stoi PRZED liczbą, gdy liczba jest numerem, a nie wielkością.
ODSYLACZ = re.compile(
    r"(§\s*|#|docs/|MB-|6\.[A-D]|T-|KN-|fazy? |faz |szczebel |"
    r"\.so\.|UTF-|Ubuntu |kodem |kod |kodu |exit |maxdepth |minLength:? |"
    r"runner-|\.NET |net|reguły |regule |punkt |punktu |pozycja |pozycji )$",
    re.IGNORECASE)

#: Data dzienna. Jej obecność czyni całe zdanie zdaniem o dniu pomiaru — mechanizm
#: 6.D108, ten sam, którym zwalniane są twierdzenia w `reports/`.
DATA = re.compile(r"\d{2}\.\d{2}\.\d{4}")

#: Ile wierszy nad asercją czytać w poszukiwaniu tej samej liczby. Dwadzieścia,
#: bo tyle obejmuje typową fiksturę budowaną w ciele testu; wartość jest progiem
#: CZYTNIKA, nie zapadką, więc nie ma przedrostka `MIN_`/`MAX_`.
OKNO_WIERSZY = 20

#: Przeliczniki jednostek. Komunikat mówi „2 cm" o literale `0.02`, „0,5 mm"
#: o różnicy `1.0005 - 1.0`, „52 µm" o `0.900 - 0.899948` — i wszystkie trzy są
#: POKRYCIEM, a nie twierdzeniem. Bez tej listy trzy poprawne komunikaty wyszłyby
#: fałszywie jako twierdzenia o drzewie; zmierzone przy 6.D255.
SKALE = (1.0, 1e-3, 1e-2, 1e-6, 1e3, 1e2)

#: Literały, które sito przepuszcza, a które twierdzeniem o drzewie NIE są —
#: każdy z powodem. Klucz to `(plik, liczba jak w komunikacie)`; NIE numer wiersza,
#: bo kotwice po numerze wiersza ruszyły się w tym repozytorium ósmy raz w niecałe
#: cztery doby (6.D229). Porównywane z drzewem W OBIE STRONY.
WYJATKI = {
    ("test_blender_cli.py", "5"): "krok zagęszczania, argument wywołania w tym samym teście",
    ("test_blender_cli.py", "15"): "odstęp łamanej z fikstury `[[i * 15.0, …]]` tego testu",
    ("test_braking.py", "30"): "kraniec tablicy §4 T-311, czytany przez `reference_distance_rows`",
    ("test_braking.py", "80"): "drugi kraniec tej samej tablicy",
    ("test_bytecode_staleness.py", "1"): "wartość zmiennej `PYTHONDONTWRITEBYTECODE=1`, nie wielkość",
    ("test_ci_workflows.py", "190"): "wielkość pobrania apt, cytat wypisu `Need to get 190 MB` — o repozytorium Ubuntu, nie o tym drzewie",
    ("test_ci_workflows.py", "366"): "wielkość archiwum Blendera, ta sama liczba w `tools/ci/blender_install.sh` — o serwerze pobrań, nie o drzewie",
    ("test_ci_workflows.py", "512"): "człon nazwy sumy `sha512=`, nie wielkość",
    ("test_ci_workflows.py", "6"): "człon sonamy `libX11.so.6`",
    ("test_clearance_profile.py", "2,4"): "zapas fikstury wobec `CONVEXITY_EPS`, przeliczalny: log10(2.5e-7 / 1e-9)",
    ("test_clearance_profile.py", "94"): "długość składu, odejmowana w tej samej asercji",
    ("test_clearance_profile.py", "0,5"): "0,5 mm = różnica argumentów `scan_positions(94.0005, 94.0, …)`",
    ("test_clearance_profile.py", "50"): "50 mm = różnica `0,900 - 0,850` z wiersza obok",
    ("test_clearance_profile.py", "0,4"): "0,4 mm = `_millimetres(0.0004)` w tej samej asercji",
    ("test_clearance_profile.py", "0,6"): "0,6 mm = `_millimetres(0.0006)` w tej samej asercji",
    ("test_constant_names.py", "20,0"): "wartość stałej, która BYŁA martwa — zdanie w czasie przeszłym",
    ("test_constant_names.py", "90,0"): "próg `min_radius_m` z `tools/track/validate.py`, sprawdzony 17.09.2026",
    ("test_csharp_assertions.py", "0.0"): "cytat zapisu tolerancji w C#, nie wielkość",
    ("test_csharp_pins.py", "0.0"): "jak wyżej",
    ("test_dead_constants.py", "90,0"): "to samo zdanie co w `test_constant_names.py`",
    ("test_line_calls_gate.py", "80"): "prędkość konstrukcyjna M7 z `data/network/lines.json`, sprawdzona 17.09.2026",
    ("test_linecore_budget_gate.py", "115,9"): "rozstęp atrapy `NIESTABILNY_W_PROGU`, składanej w tym samym pliku",
    ("test_linecore_budget_gate.py", "16,000"): "pomiar atrapy `SLABO_UWARUNKOWANY_PONAD_PROGIEM`",
    ("test_linecore_budget_gate.py", "100"): "`spread_pct_max` z `tools/ci/linecore-step-budget.json`, sprawdzone 17.09.2026",
    ("test_linecore_budget_gate.py", "9,572"): "zapisany pomiar z 08.09.2026, przebieg 34194126232",
    ("test_lod.py", "0,5"): "0,5 mm = `margins(0.0005)` w tej samej asercji",
    ("test_next_task.py", "6"): "numer fazy w `docs/TASKS.md`",
    ("test_osm_api_fallback.py", "66,1"): "wielkość pobrania z API OSM, zapisany pomiar w `reports/osm-api-droga-zapasowa.md`",
    ("test_osm_api_fallback.py", "97"): "liczba way'ów w tamtym pobraniu, jak wyżej",
    ("test_report_claims.py", "1"): "domyślna głębokość `actions/checkout` — fakt o cudzym narzędziu",
    ("test_report_claims.py", "2"): "artefakt ekstraktora: `2` stoi w argumencie krotki `%`, nie w treści komunikatu",
    ("test_runner_options.py", "1"): "wartość w przykładzie komendy `--atp 1`",
    ("test_runner_output_streams.py", "2"): "deskryptor w zapisie powłoki `2>/dev/null`",
    ("test_runner_process_exit.py", "3"): "liczba testów sondy, przybita wzorcem `przeszlo.group(2) == \"3\"` obok",
    ("test_station_components.py", "0,9"): "110,0 - 109,1; `TIGHTEST_STATION_FOOTPRINT_M` przybite asercją dwa wiersze wyżej",
    ("test_suite_runtime_budget.py", "08.09"): "data incydentu zapisana bez roku",
    ("test_suite_runtime_budget.py", "0.002"): "wartość z napisu wejściowego `0m0.002s` tego testu",
    ("test_suite_runtime_budget.py", "17"): "17 % = `> 1.17` w tej samej asercji",
    ("test_suite_runtime_budget.py", "40"): "40 % = `* 1.4` w tej samej asercji",
    ("test_visual.py", "0,0819"): "zaokrąglenie literału `0.081944` z tej samej asercji; ta sama liczba w `tools/visual/cameras.json`",
    ("test_visual_gates.py", "0.5"): "mnożnik gałęzi `blisko` z `tools/visual/framing.py:256`",
}


def komunikaty(katalog=None, root=None):
    """`[(plik, wiersz, tekst)]` — napisowa treść każdego `assert …, MSG`."""
    baza = katalog or os.path.join(ROOT, "tools", "tests")
    korzen = root or ROOT
    out = []
    for gdzie, _katalogi, pliki in TW.walk(baza, korzen):
        for nazwa in sorted(pliki):
            if not nazwa.endswith(".py"):
                continue
            with open(os.path.join(gdzie, nazwa), encoding="utf-8") as uchwyt:
                zrodlo = uchwyt.read()
            linie = zrodlo.split("\n")
            for wezel in ast.walk(ast.parse(zrodlo)):
                if not (isinstance(wezel, ast.Assert) and wezel.msg is not None):
                    continue
                czesci = [n.value for n in ast.walk(wezel.msg)
                          if isinstance(n, ast.Constant) and isinstance(n.value, str)]
                if czesci:
                    out.append((nazwa, wezel.lineno, " ".join(czesci), wezel, linie))
    return out


def _literaly_warunku(wezel):
    return {float(n.value) for n in ast.walk(wezel.test)
            if isinstance(n, ast.Constant)
            and isinstance(n.value, (int, float)) and not isinstance(n.value, bool)}


def literaly_w_komunikatach(katalog=None, root=None):
    """`[(plik, wiersz, liczba, tekst)]` dla każdego literału liczbowego w prozie."""
    out = []
    for nazwa, wiersz, tekst, _wezel, _linie in komunikaty(katalog, root):
        czysty = SPECYFIKATOR.sub(" ", tekst)
        for trafienie in LICZBA.finditer(czysty):
            out.append((nazwa, wiersz, trafienie.group(1), czysty))
    return out


def bez_pokrycia(katalog=None, root=None):
    """`[(plik, wiersz, liczba, tekst)]` — literały, których nic nie trzyma."""
    out = []
    for nazwa, wiersz, tekst, wezel, linie in komunikaty(katalog, root):
        czysty = SPECYFIKATOR.sub(" ", tekst)
        z_warunku = _literaly_warunku(wezel)
        # Okno kończy się WIERSZ PRZED asercją, nie na niej. Gdy obejmowało samą
        # asercję, liczba z komunikatu pokrywała SAMĄ SIEBIE — sito wychodziło
        # puste i wyglądało na skuteczne. Złapała to kontrola przyrządu niżej,
        # przy pierwszym przebiegu tego modułu.
        # Bez `.replace(",", ".")` na oknie: źródło pisze ułamki kropką, a zamiana
        # przecinków psuła dopasowanie `0.02` w `[(0.02, 0)]`, bo po liczbie
        # stawała kropka i granica słowa przestawała zachodzić.
        okno = "\n".join(linie[max(0, wiersz - OKNO_WIERSZY - 1):wiersz - 1])
        datowany = bool(DATA.search(czysty))
        for trafienie in LICZBA.finditer(czysty):
            napis = trafienie.group(1)
            if ODSYLACZ.search(czysty[:trafienie.start()]):
                continue
            if datowany:
                continue
            try:
                wartosc = float(napis.replace(",", "."))
            except ValueError:
                continue
            if any(abs(wartosc - x) < 1e-12 for x in z_warunku):
                continue
            if any(re.search(r"(?<![\w.])%s(?![\w.])" % re.escape("%g" % (wartosc * skala)),
                             okno) for skala in SKALE):
                continue
            out.append((nazwa, wiersz, napis, czysty))
    return out


def test_kazda_liczba_w_komunikacie_ma_POKRYCIE_albo_stoi_na_liscie():
    """**Porównanie W OBIE STRONY, bo lista wyjątków bez tego gnije (6.D243).**

    Nowa liczba bez pokrycia zapala pierwszą połowę; wpis o liczbie, która pokrycie
    już ma, zapala drugą. Jedno bez drugiego dałoby listę rosnącą w jedną stronę,
    czyli podpis pod obrazkiem zamiast bramki.
    """
    widziane = {(nazwa, liczba): (wiersz, tekst)
                for nazwa, wiersz, liczba, tekst in bez_pokrycia()}

    nowe = sorted(k for k in widziane if k not in WYJATKI)
    assert nowe == [], (
        "liczba w komunikacie asercji, której nic nie trzyma: %s — albo podstaw ją "
        "z kodu (`%%d` z tego, co asercja liczy), albo dopisz do `WYJATKI` z powodem. "
        "Liczba wpisana z ręki starzeje się w dobę i nie zapala niczego — 17.09.2026 "
        "znaleziono cztery takie, z tego jedna ogłaszała samą siebie strażnikiem listy"
        % [(k, widziane[k][0]) for k in nowe])

    znikniete = sorted(k for k in WYJATKI if k not in widziane)
    assert znikniete == [], (
        "wpis w `WYJATKI` dla liczby, która dziś ma pokrycie albo zniknęła: %s "
        "— zdejmij wpis w tym samym commicie, w którym znika powód" % znikniete)


def test_ile_liczb_stoi_w_komunikatach_i_ile_sito_zdejmuje():
    """Pomiar 6.D255 przybity, żeby „sito działa" dało się sprawdzić, a nie przeczytać.

    Bez tej pary literówka we wzorcu dałaby zero literałów, zero winnych i ZIELEŃ —
    stan nieodróżnialny od drzewa, w którym żaden komunikat nie niesie liczby (6.D27).
    """
    wszystkie = literaly_w_komunikatach()
    zostalo = bez_pokrycia()

    assert len(wszystkie) >= 400, (
        "literałów liczbowych w komunikatach jest %d — 17.09.2026 było 418; spadek "
        "o dziesiątki znaczy, że czytnik oślepł, a nie że proza zniknęła"
        % len(wszystkie))
    klucze = {(nazwa, liczba) for nazwa, _w, liczba, _t in zostalo}
    assert klucze == set(WYJATKI), (
        "zbiór par (plik, liczba) rozjechał się z listą wyjątków: %s"
        % sorted(klucze ^ set(WYJATKI)))
    assert len(wszystkie) - len(zostalo) >= 350, (
        "sito zdejmuje tylko %d z %d — przy tak niskiej skuteczności lista wyjątków "
        "przestaje być listą wyjątków" % (len(wszystkie) - len(zostalo), len(wszystkie)))


def test_sito_widzi_ksztalty_ktore_ma_widziec():
    """Kontrola PRZYRZĄDU na wejściu syntetycznym — pięć kształtów osobno.

    Każdy z czterech powodów pokrycia sprawdzony z osobna, plus przypadek, który
    pokryty NIE jest. Bez tego nie wiadomo, czy sito odsiewa, czy po prostu nic
    nie znajduje.
    """
    import tempfile
    zrodlo = (
        "def test_a():\n"
        "    assert len(x) == 18, 'jest 18 wpisow'\n"          # literał w warunku
        "\n"
        "def test_b():\n"
        "    maly = [(0.02, 0)]\n"
        "    assert maly, 'przesuniecie 2 cm'\n"                # inna skala w oknie
        "\n"
        "def test_c():\n"
        "    assert x, 'patrz docs/24-decyzje.md i CLAUDE.md §8'\n"   # odsyłacz
        "\n"
        "def test_d():\n"
        "    assert x, '11.09.2026 bylo ich 92'\n"             # data
        "\n"
        "def test_e():\n"
        "    assert x, 'takich plikow jest w katalogu 77'\n"    # NIC tego nie trzyma
    )
    with tempfile.TemporaryDirectory() as katalog:
        with open(os.path.join(katalog, "test_probka.py"), "w",
                  encoding="utf-8") as uchwyt:
            uchwyt.write(zrodlo)
        wszystkie = literaly_w_komunikatach(katalog, katalog)
        zostalo = bez_pokrycia(katalog, katalog)

    liczby = {x[2] for x in wszystkie}
    assert {"18", "2", "24", "8", "92", "77"} <= liczby, (
        "czytnik nie zobaczył wszystkich pięciu kształtów wejścia: %s" % sorted(liczby))

    winni = sorted((x[0], x[2]) for x in zostalo)
    assert winni == [("test_probka.py", "77")], (
        "sito przepuściło co innego niż jedyną liczbę bez pokrycia: %s" % winni)


if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))
