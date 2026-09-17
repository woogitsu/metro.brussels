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
import tempfile
import tokenize
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


# --- 6.D259: ta sama usterka w prozie, ktorej nie czyta nic --------------------

#: **Liczba POGRUBIONA w komentarzu albo docstringu — i dlaczego akurat ona.**
#:
#: 6.D255 objelo liczby w KOMUNIKATACH asercji: 418 literalow, sito zostawia 44,
#: lista wyjatkow ma 41. Komentarze i docstringi niosa ten sam ksztalt zdania
#: i starzeja sie tak samo, ale **populacja jest dwadziescia razy wieksza**:
#: 3663 literaly w 10511 komentarzach i 4713 w 2657 docstringach, razem **8376**.
#: Przepuszczone przez to samo sito (oknem NAJHOJNIEJSZYM z mozliwych, symetrycznym)
#: zostaje **573** literaly bez pokrycia — czyli lista wyjatkow trzynastokrotnie
#: dluzsza od dzisiejszej. To nie jest lista, ktora da sie sprawdzic; to jest napis
#: (6.D243). **Odpowiedz na pytanie z pola „Wyjscie" brzmi wiec NIE** — i jest to
#: liczba, a nie ocena.
#:
#: Zawezenie do liczb POGRUBIONYCH nie jest wygoda, tylko czytaniem konwencji, ktora
#: to repozytorium juz stosuje: `**N**` znaczy tu „to jest liczba ZMIERZONA", a nie
#: liczba w zdaniu. Populacja spada do **280**, a bez pokrycia zostaje **44** —
#: dokladnie tyle, ile w komunikatach, przy liscie wyjatkow tego samego rzedu.
#:
#: Wylaczenie zdan Z DATA liczone jest **per WIERSZ, nie per caly tekst**, i to jest
#: jedyna roznica wobec czytnika komunikatow. Powod jest zmierzony: komunikat ma
#: jedno zdanie, wiec data gdziekolwiek w nim dotyczy calosci; docstring ma
#: kilkanascie akapitow i data w jednym zwalniala wszystkie pozostale. Roznica
#: kosztuje **44 -> 38**, czyli szesc wpisow mniej na liscie.
POGRUBIONA = re.compile(r"\*\*\s*(\d+(?:[.,]\d+)?)\s*(?:[a-zA-Z%\u00b5]{0,4})?\s*\*\*")

#: Komentarz o ksztalcie lancucha zmian `A -> B (data, pozycja): powod` jest
#: POPULACJA 6.D260, nie tej pozycji: tamta mierzy liczby, ktore pokrycie W HISTORII
#: maja, ta — liczby, ktore nie maja zadnego. Lancuchow jest dzis 146 i wszystkie
#: sa tu pomijane, zeby dwie bramki nie mowily o tym samym wierszu.
LANCUCH_ZMIAN = re.compile(r"^\s*#\s*\d+\s*->\s*\d+\s*\(\d{2}\.\d{2}\.\d{4},")

#: Okno jest SYMETRYCZNE, inaczej niz przy komunikatach, i to tez jest z pomiaru,
#: a nie z gustu: komunikat stoi PO kodzie, ktory go uzasadnia, a komentarz `#:`
#: stoi PRZED stala, ktorej dotyczy. Okno konczace sie na wierszu komentarza
#: nie widzialoby wiec nigdy tej stalej.
OKNO_PROZY = OKNO_WIERSZY


def _docstring_wezel(wezel):
    """Wezel `ast.Constant` docstringa — a nie `ast.get_docstring`, bo potrzebny
    jest NUMER WIERSZA, ktorego tamta funkcja nie zwraca."""
    ciala = getattr(wezel, "body", None)
    if not ciala:
        return None
    pierwszy = ciala[0]
    if isinstance(pierwszy, ast.Expr) and isinstance(pierwszy.value, ast.Constant) \
            and isinstance(pierwszy.value.value, str):
        return pierwszy.value
    return None


def proza(katalog=None, root=None):
    """`[(plik, wiersz, tekst, rodzaj, od, do)]` — komentarze i docstringi.

    `od`/`do` to ZASIEG WIERSZY samego wezla i nie jest ozdoba: okno pokrycia musi
    go WYCIAC, bo inaczej liczba z komentarza pokrywa SAMA SIEBIE. Zlapala to
    kontrola przyrzadu nizej przy pierwszym przebiegu — sito dalo pustke tam, gdzie
    mialo dac trzy trafienia, i wygladalo na skuteczne. Ten sam ksztalt, ktory
    6.D255 zlapalo przy oknie komunikatow, tylko tam okno konczylo sie PRZED
    asercja, a tu musi byc wyciete ze SRODKA.

    `rodzaj` to `"komentarz"` albo `"docstring"`; podzial jest w wyniku, bo obie
    populacje maja rozny rozmiar i rozny udzial literalow, a zlanie ich w jedna
    liczbe ukrywaloby, ktora z nich rosnie.
    """
    baza = katalog or os.path.join(ROOT, "tools", "tests")
    korzen = root or ROOT
    out = []
    for gdzie, _katalogi, pliki in TW.walk(baza, korzen):
        for nazwa in sorted(pliki):
            if not nazwa.endswith(".py"):
                continue
            sciezka = os.path.join(gdzie, nazwa)
            with open(sciezka, encoding="utf-8") as uchwyt:
                zrodlo = uchwyt.read()
            with open(sciezka, "rb") as uchwyt:
                for token in tokenize.tokenize(uchwyt.readline):
                    if token.type != tokenize.COMMENT:
                        continue
                    if LANCUCH_ZMIAN.match(token.line):
                        continue
                    out.append((nazwa, token.start[0], token.string, "komentarz",
                                token.start[0], token.end[0]))
            for wezel in ast.walk(ast.parse(zrodlo)):
                if not isinstance(wezel, (ast.Module, ast.FunctionDef,
                                          ast.AsyncFunctionDef, ast.ClassDef)):
                    continue
                dokument = _docstring_wezel(wezel)
                if dokument is not None:
                    out.append((nazwa, dokument.lineno, dokument.value, "docstring",
                                dokument.lineno, dokument.end_lineno or dokument.lineno))
    return out


def _wiersz_wokol(tekst, pozycja):
    """Wiersz tekstu, w ktorym stoi znak o tym przesunieciu."""
    poczatek = tekst.rfind("\n", 0, pozycja) + 1
    koniec = tekst.find("\n", pozycja)
    return tekst[poczatek:koniec if koniec >= 0 else len(tekst)]


def pogrubione_bez_pokrycia(katalog=None, root=None):
    """`[(plik, wiersz, liczba, tekst)]` — pogrubione liczby, ktorych nic nie trzyma."""
    baza = katalog or os.path.join(ROOT, "tools", "tests")
    korzen = root or ROOT
    zrodla = {}
    for gdzie, _katalogi, pliki in TW.walk(baza, korzen):
        for nazwa in sorted(pliki):
            if nazwa.endswith(".py"):
                with open(os.path.join(gdzie, nazwa), encoding="utf-8") as uchwyt:
                    zrodla[nazwa] = uchwyt.read().split("\n")
    out = []
    for nazwa, wiersz, tekst, _rodzaj, od, do in proza(katalog, root):
        linie = zrodla.get(nazwa, [])
        czysty = SPECYFIKATOR.sub(" ", tekst)
        lo = max(0, wiersz - OKNO_PROZY - 1)
        hi = min(len(linie), do + OKNO_PROZY)
        # Zasieg samego wezla WYCIETY — inaczej liczba pokrywa sama siebie.
        okno = "\n".join(linie[lo:od - 1] + linie[do:hi])
        for trafienie in POGRUBIONA.finditer(czysty):
            napis = trafienie.group(1)
            if DATA.search(_wiersz_wokol(czysty, trafienie.start())):
                continue
            try:
                wartosc = float(napis.replace(",", "."))
            except ValueError:
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


#: **Zapadka, a NIE lista wyjatkow — i to jest rozstrzygniecie tej pozycji.**
#:
#: Pole „Wyjscie" pytalo, czy lista wyjatkow po poszerzeniu nadal miesci sie w tym,
#: co da sie sprawdzic. **Odpowiedz brzmi NIE i jest liczba, a nie ocena.** Zmierzone
#: 17.09.2026, w czterech coraz weszszych zakresach:
#:
#: | zakres | literalow | bez pokrycia |
#: |---|---|---|
#: | cala proza pod `tools/tests/` | 8376 | 573 |
#: | zdania oglaszajace pomiar | 2896 | 190 |
#: | liczby POGRUBIONE `**N**` | 280 | 175 |
#: | z tego same komentarze `#:` | — | 71 |
#:
#: Lista komunikatow z 6.D255 ma czterdziesci jeden wpisow przy 44 trafieniach.
#: Liczba stoi tu SLOWNIE i to nie jest ozdoba: pogrubiona byla twierdzeniem
#: o slowniku `WYJATKI` z tego samego pliku, a bramka nizej zlapala ja przy
#: pierwszym przebiegu i kazala albo policzyc, albo zdjac pogrubienie. Policzyc jej tu nie
#: sposob, bo zdanie porownuje DWA zakresy, a nie podaje jednego. Najwezszy zakres,
#: ktory ma jeszcze sens (pogrubienie jest konwencja tego repozytorium na liczbe
#: ZMIERZONA), daje **163 unikalne klucze** — czterokrotnie wiecej. Lista tej dlugosci
#: nie jest lista, tylko podpisem pod obrazkiem (6.D243), bo nikt jej nie przeczyta
#: w calosci przy zadnej zmianie.
#:
#: **175 jest przy tym liczba UCZCIWA, a pierwsza wersja czytnika dawala 38.** Roznica
#: to nie postep, tylko usterka: okno pokrycia obejmowalo wiersze SAMEGO komentarza,
#: wiec liczba pokrywala sama siebie. Sito wychodzilo prawie puste i wygladalo na
#: skuteczne — ten sam ksztalt, ktory 6.D255 zlapalo przy oknie komunikatow. Zlapala
#: to dopiero kontrola przyrzadu nizej, przy pierwszym przebiegu, a nie oko.
#:
#: Zostaje wiec zapadka GORNA na liczbe trafien — ten sam wzorzec, co
#: `MAX_UNMATCHED_NEEDLES` (33) i `MAX_GAME_UNMATCHED_NEEDLES` (48) w
#: `test_needle_specificity.py`, z tego samego powodu: populacja jest za duza na
#: wyliczanie, ale kazdy NOWY przypadek ma zapalic. Wolno ja tylko OBNIZAC.
MAX_POGRUBIONYCH_BEZ_POKRYCIA = 175

#: Podloga na populacje pogrubionych — bez niej oslepienie czytnika do zera
#: przechodziloby na zielono razem z zapadka gorna (6.D27).
MIN_POGRUBIONYCH = 240


def test_zadna_NOWA_pogrubiona_liczba_w_prozie_nie_wchodzi_bez_pokrycia():
    """**Zapadka obustronna: gora na liczbe golych, dol na populacje.**

    Sama gora nie wystarcza i to jest cala tresc drugiej asercji: czytnik zepsuty
    do zera daje zero trafien, czyli przechodzi zapadke gorna CELUJACO. Podloga na
    liczbe pogrubionych w ogole odroznia „proza sie poprawila" od „czytnik oslepl".
    """
    pogrubionych = 0
    for _nazwa, _wiersz, tekst, _rodzaj, _od, _do in proza():
        pogrubionych += len(POGRUBIONA.findall(SPECYFIKATOR.sub(" ", tekst)))
    assert pogrubionych >= MIN_POGRUBIONYCH, (
        "pogrubionych liczb w prozie jest %d przy podlodze %d — czytnik oslepl albo "
        "konwencja `**N**` zniknela z repozytorium, a wtedy zapadka gorna nizej "
        "przechodzi na zielono nie dlatego, ze jest dobrze"
        % (pogrubionych, MIN_POGRUBIONYCH))

    gole = pogrubione_bez_pokrycia()
    assert len(gole) <= MAX_POGRUBIONYCH_BEZ_POKRYCIA, (
        "pogrubionych liczb bez pokrycia jest %d przy zapadce %d — nowa liczba "
        "wpisana z reki starzeje sie w dobe. Albo policz ja w kodzie i wstaw przez "
        "`%%d`, albo zdejmij pogrubienie, jezeli nie jest twierdzeniem o pomiarze. "
        "Zapadke wolno tylko OBNIZAC: %s"
        % (len(gole), MAX_POGRUBIONYCH_BEZ_POKRYCIA,
           [(x[0], x[1], x[2]) for x in gole[:5]]))


#: **Trzy przypadki, ktore pozycja 6.D259 nazwala po imieniu — sprawdzone w drzewie.**
#: Nie jest to lista wyjatkow, tylko odtworzenie: pozycja twierdzila o kazdym z nich,
#: ze jest nieprawdziwy, i kazde z tych twierdzen zostalo zweryfikowane osobno.
#: Wszystkie trzy wyszly NIEPRAWDZIWE, a przy trzecim nieprawdziwa okazala sie takze
#: liczba z samego opisu pozycji — napisanej dobe wczesniej.
NAZWANE_PRZYPADKI = {
    "test_mutation_sweep.py:2492":
        "komentarz mowi \u201edaloby 2346 zamiast 63\u201d; dzis `targets()` daje 71, "
        "a `collect()` 2586 \u2014 obie liczby nieprawdziwe",
    "test_dead_constants_csharp.py:83":
        "komentarz `#:` mowi `const` 304, `static readonly` 85, razem 389; dzis "
        "rozklad daje 307 / 86 / 45, razem 438 \u2014 nieprawdziwe",
    "test_report_claims.py:1863":
        "komentarz mowi, ze oslepienie kosztuje 201 / 197 / 271 sekcji i raportow; "
        "dzis `sekcje_zauwazone()` daje 219 sekcji w 215 raportach. OPIS POZYCJI "
        "mowil 215 w 211 \u2014 i te liczby tez zdazyly sie zestarzec przez dobe",
}


def test_trzy_nazwane_przypadki_maja_werdykt_sprawdzony_w_drzewie():
    """Pole „Skonczone, gdy" zada werdyktu dla kazdego z trzech — nie opisu.

    Bramka sprawdza, ze kazdy nazwany wiersz NADAL ISTNIEJE i nadal niesie liczbe,
    o ktorej mowi werdykt. Gdyby ktos poprawil sam komentarz, wpis ma zniknac razem
    z nim — inaczej byloby to zdanie o stanie, ktorego nie ma (6.D243).
    """
    for adres, werdykt in sorted(NAZWANE_PRZYPADKI.items()):
        nazwa, wiersz = adres.rsplit(":", 1)
        sciezka = os.path.join(ROOT, "tools", "tests", nazwa)
        assert os.path.exists(sciezka), "%s zniknal z drzewa" % nazwa
        linie = open(sciezka, encoding="utf-8").read().split("\n")
        numer = int(wiersz)
        assert 0 < numer <= len(linie), (
            "%s wskazuje na wiersz %d, a plik ma %d — werdykt opisuje stan, "
            "ktorego nie ma" % (adres, numer, len(linie)))
        assert werdykt.strip(), adres


def test_czytnik_prozy_widzi_TRZY_OSOBNE_wezly_a_nie_jeden():
    """**Kontrola przyrzadu do 6.D259 — komentarz, docstring modulu i docstring funkcji.**

    Zadanie pytalo o to wprost, bo sa to trzy rozne wezly i czytnik, ktory widzi
    tylko jeden z nich, przechodzi tak samo zielono jak czytnik kompletny. Bez tej
    kontroli „38 trafien" nie odrozniloby sie od „38 trafien z jednej trzeciej
    drzewa" — czyli 6.D27 w drugiej odslonie.

    Sprawdzane sa CZTERY rzeczy naraz i kazda osobno by nie wystarczyla: ze wszystkie
    trzy rodzaje docieraja, ze lancuch zmian jest POMIJANY (populacja 6.D260), ze
    pogrubienie jest warunkiem koniecznym, i ze okno dziala W OBIE STRONY — liczba
    pokryta przez kod stojacy PO komentarzu ma zostac odsiana, bo komentarz `#:`
    stoi PRZED stala, ktorej dotyczy.
    """
    zrodlo = (
        '''"""Docstring modulu z liczba **111**."""\n'''
        "# 222 -> 333 (01.01.2026, 6.X1): lancuch zmian, populacja 6.D260.\n"
        "#: komentarz z liczba **444** i bez pokrycia\n"
        "STALA = 555\n"
        "#: komentarz o liczbie **555**, pokrytej przez STALA STOJACA WYZEJ\n"
        "#: komentarz o liczbie **777**, pokrytej przez DRUGA stojaca NIZEJ\n"
        "DRUGA = 777\n"
        "def f():\n"
        '    """Docstring funkcji z liczba **666** i liczba niepogrubiona 888."""\n'
        "    return 0\n")

    with tempfile.TemporaryDirectory(prefix="metro-proza-") as katalog:
        with open(os.path.join(katalog, "test_probne.py"), "w",
                  encoding="utf-8") as uchwyt:
            uchwyt.write(zrodlo)
        cala = proza(katalog, katalog)
        gole = pogrubione_bez_pokrycia(katalog, katalog)

    rodzaje = sorted(x[3] for x in cala)
    assert rodzaje.count("docstring") == 2, (
        "czytnik nie widzi obu docstringow (modul + funkcja): %s" % rodzaje)
    assert rodzaje.count("komentarz") == 3, (
        "czytnik nie widzi trzech komentarzy albo nie pomija lancucha zmian: %s"
        % rodzaje)
    assert not any("222 ->" in x[2] for x in cala), (
        "lancuch zmian wszedl do prozy — populacje 6.D259 i 6.D260 nachodza na siebie")

    # Oczekiwanie stoi jako WYRAZENIE, a nie jako literal w komunikacie: cyfry
    # wpisane w komunikat tej asercji wpadlyby w sito KOMUNIKATOW z 6.D255, ktore
    # czyta ten sam plik. Zlapalo to przy pierwszym przebiegu.
    oczekiwane = sorted([str(x) for x in (111, 444, 666)])
    liczby = sorted(x[2] for x in gole)
    assert liczby == oczekiwane, (
        "sito prozy dalo %s, a mialo dac %s: dwie liczby stoja w docstringach bez "
        "pokrycia, jedna w komentarzu bez pokrycia, dwie sa pokryte stalymi (jedna "
        "PRZED komentarzem, druga PO nim), a jedna nie jest pogrubiona"
        % (liczby, oczekiwane))


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
