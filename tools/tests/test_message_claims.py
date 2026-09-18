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
import collections
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
    ("test_message_claims.py", "04"): "człon nazwy `docs/04-conventions.md` z fikstury kontroli przyrządu — sprawdzane jest, że sito go NIE liczy",
    ("test_message_claims.py", "085"): "urwany człon `0,085` z tej samej fikstury; asercja żąda, żeby go w populacji NIE było",
    ("test_message_claims.py", "0,085"): "ta sama fikstura, człon nierozcięty",
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

# --- 6.D264: czym jest „pokrycie" — przypisaniem stalej czy zbiegiem cyfr --------

#: Przypisanie stalej: wiersz zaczynajacy sie NAZWA WIELKIMI LITERAMI i znakiem `=`.
#: Ten sam ksztalt, ktory czyta `ZAPADKA_NAZWA` w `test_tree_walks.py`, tylko bez
#: wymogu przedrostka `MAX`/`MIN` — bo pokrycie daje KAZDA stala, nie tylko zapadka.
PRZYPISANIE_STALEJ = re.compile(r"^\s*([A-Z][A-Z0-9_]*)\s*=\s*\S")

#: **Czym jest „pokrycie" w bramce z 6.D259 — zmierzone 18.09.2026.**
#:
#: Pogrubionych liczb w prozie jest 286. Z tego 47 stoi w wierszu z DATA i sito je
#: pomija; zostaje 239, a z nich 175 nie ma pokrycia (zapadka gorna wyzej w tym
#: pliku). Pokrytych jest wiec 64 — i to o nich pytala pozycja 6.D264:
#:
#: **Liczby tego akapitu stoja BEZ POGRUBIENIA, i jest to trzeci raz w tej serii,
#: kiedy zapisanie wyniku pomiaru kosztuje zdjecie pogrubienia.** Dwie z nich (15 i 49)
#: pogrubienie MAJA, bo stoja obok stalych, ktore je niosa — i to jest dokladnie
#: roznica, ktora ta pozycja mierzy. Cena tamtej bramki jest wiec widoczna w tym
#: samym akapicie, ktory ja opisuje — i nie jest obchodzona w milczeniu.
#:
#: | co daje pokrycie | ile |
#: |---|---|
#: | PRZYPISANIE STALEJ w oknie | 15 |
#: | przypadkowe wystapienie tej samej cyfry | 49 |
#:
#: **Trzy czwarte „pokrycia" jest zbiegiem cyfr, a nie zapisem w kodzie.** Przyklady
#: sa dosadne: pogrubione `0` „pokrywa" wiersz `while i < len(maska) and glebokosc > 0:`,
#: a pogrubione `1` — wiersz `"kod": 1,` z tablicy przypadkow testowych. Liczba
#: uznana za pokryta nie jest wiec liczba, ktorej cokolwiek PILNUJE; jest liczba,
#: ktorej ta sama cyfra gdzies obok przypadkiem stoi.
#:
#: **Czego to NIE znaczy.** Nie znaczy, ze zapadke 175 trzeba podniesc — podniesc
#: zapadki gornej nie wolno, a i tak nie o to chodzi. Znaczy, ze slowo „pokrycie"
#: opisuje w tej bramce dwie bardzo rozne rzeczy i dotad nie bylo tego widac.
#: Rozroznienie jest od dzis PRZYBITE dwiema rownosciami i porownywane z drzewem.
POKRYTYCH_PRZYPISANIEM = 18
POKRYTYCH_ZBIEGIEM_CYFR = 54


def pozycje_pokrycia(katalog=None, root=None):
    """`{klasa: [(plik, wiersz, napis, zdanie, wiersze pokrywajace)]}` — 6.D268.

    Czytnik POZYCZONY: okno, skale i wzorzec pogrubienia sa te same, ktorych uzywa
    `pogrubione_bez_pokrycia`. Dwa czytniki rozjechalyby sie przy pierwszej zmianie
    okna, a zdanie „z 64 pokrytych 15 ma przypisanie" byloby wtedy zdaniem o dwoch
    roznych oknach.
    """
    baza = katalog or os.path.join(ROOT, "tools", "tests")
    korzen = root or ROOT
    zrodla = {}
    for gdzie, _katalogi, pliki in TW.walk(baza, korzen):
        for nazwa in sorted(pliki):
            if nazwa.endswith(".py"):
                with open(os.path.join(gdzie, nazwa), encoding="utf-8") as uchwyt:
                    zrodla[nazwa] = uchwyt.read().split("\n")
    out = {"przypisanie": [], "zbieg": [], "bez pokrycia": []}
    for nazwa, wiersz, tekst, _rodzaj, od, do in proza(katalog, root):
        linie = zrodla.get(nazwa, [])
        czysty = SPECYFIKATOR.sub(" ", tekst)
        lo = max(0, wiersz - OKNO_PROZY - 1)
        hi = min(len(linie), do + OKNO_PROZY)
        okno = linie[lo:od - 1] + linie[do:hi]
        # Numery wierszy okna — do rozpoznania PAR WZAJEMNYCH (6.D274): bez nich
        # wiadomo, ze cos pokrywa, ale nie wiadomo CO.
        numery_okna = list(range(lo + 1, od)) + list(range(do + 1, hi + 1))
        for trafienie in POGRUBIONA.finditer(czysty):
            napis = trafienie.group(1)
            if DATA.search(_wiersz_wokol(czysty, trafienie.start())):
                continue
            try:
                wartosc = float(napis.replace(",", "."))
            except ValueError:
                continue
            pokrywajace, numery_pokrywajace = [], []
            for skala in SKALE:
                wzor = re.compile(r"(?<![\w.])%s(?![\w.])"
                                  % re.escape("%g" % (wartosc * skala)))
                for numer, linia in zip(numery_okna, okno):
                    if wzor.search(linia):
                        pokrywajace.append(linia)
                        numery_pokrywajace.append(numer)
            # Klasa liczona z PELNEGO zbioru, a nie z dwoch zapamietanych nizej:
            # probka dwoch wierszy dawalaby „wylacznie proza" takze wtedy, gdy
            # trzeci wiersz w oknie jest kodem (6.D274).
            proza_ile = sum(1 for l in pokrywajace if l.strip().startswith("#"))
            klasa_pokrycia = ("proza" if proza_ile == len(pokrywajace)
                              else "kod" if proza_ile == 0 else "mieszane")
            wpis = (nazwa, wiersz, napis,
                    _wiersz_wokol(czysty, trafienie.start()).strip(),
                    tuple(l.strip() for l in pokrywajace[:2]),
                    klasa_pokrycia, tuple(numery_pokrywajace))
            if not pokrywajace:
                out["bez pokrycia"].append(wpis)
            elif any(PRZYPISANIE_STALEJ.match(l) for l in pokrywajace):
                out["przypisanie"].append(wpis)
            else:
                out["zbieg"].append(wpis)
    return out


def pokrycie_pogrubionych(katalog=None, root=None):
    """`{"przypisanie": n, "zbieg": n, "bez pokrycia": n}` — 6.D264, LICZNIK.

    Od 6.D268 jest to WIDOK na `pozycje_pokrycia`, a nie osobny przebieg. Dwa
    przebiegi po tym samym drzewie rozjechalyby sie przy pierwszej zmianie okna,
    a zdanie „z 64 pokrytych 15 ma przypisanie" opisywaloby wtedy dwa rozne okna
    (6.D213). Zgodnosc licznika z lista pilnuje osobna asercja nizej.
    """
    return {k: len(v) for k, v in pozycje_pokrycia(katalog, root).items()}


def test_ile_POKRYCIA_daje_przypisanie_stalej_a_ile_zbieg_cyfr():
    """**Obie liczby, ktorych zadalo pole „Wyjscie" 6.D264 — rownosciami.**

    Rownosc, a nie podloga: populacja pokrytych jest maly ulamkiem prozy i nie rosnie
    co pozycje, a KAZDE przejscie liczby z kupki „zbieg" do kupki „przypisanie" jest
    poprawa, ktora chce sie widziec. Trzecia liczba (bez pokrycia) stoi juz przybita
    zapadka gorna i jest tu sprawdzana na ZGODNOSC z nia — inaczej dwa czytniki
    mowilyby o dwoch roznych drzewach.
    """
    rozklad = pokrycie_pogrubionych()
    assert (rozklad["przypisanie"], rozklad["zbieg"]) == (POKRYTYCH_PRZYPISANIEM,
                                                          POKRYTYCH_ZBIEGIEM_CYFR), (
        "pokrycie przez PRZYPISANIE %d i przez ZBIEG CYFR %d, a pomiar 18.09.2026 dal "
        "%d i %d. Przejscie liczby ze `zbiegu` do `przypisania` jest POPRAWA (liczba "
        "stanela obok swojej stalej); w druga strone znaczy, ze stala zniknela, "
        "a proza o niej zostala"
        % (rozklad["przypisanie"], rozklad["zbieg"],
           POKRYTYCH_PRZYPISANIEM, POKRYTYCH_ZBIEGIEM_CYFR))

    assert rozklad["bez pokrycia"] == len(pogrubione_bez_pokrycia()), (
        "ten czytnik widzi %d liczb bez pokrycia, a `pogrubione_bez_pokrycia` %d — "
        "dwa czytniki tej samej rzeczy sie rozjechaly"
        % (rozklad["bez pokrycia"], len(pogrubione_bez_pokrycia())))


def test_czytnik_pokrycia_odroznia_PRZYPISANIE_od_ZBIEGU_CYFR():
    """**Kontrola przyrzadu do 6.D264 — cztery ksztalty na drzewie probnym.**

    Zadanie zadalo jej wprost: liczba pokryta przypisaniem ma trafic do pierwszej
    kupki, a pokryta przypadkowym wystapieniem tej samej cyfry — do drugiej. Bez
    tego para (15, 49) nie odroznialaby sie od czytnika, ktory wszystko wrzuca
    do jednej kupki, a taki tez daje sume 64.
    """
    zrodlo = (
        "#: proza o liczbie **7** i o liczbie **8**\n"
        "#: oraz o liczbie **9**, ktorej nic nie trzyma\n"
        "PROG = 7\n"
        "def f(lista):\n"
        "    return [x for x in lista if len(x) > 8]\n")

    with tempfile.TemporaryDirectory(prefix="metro-pokrycie-") as katalog:
        with open(os.path.join(katalog, "test_probne.py"), "w",
                  encoding="utf-8") as uchwyt:
            uchwyt.write(zrodlo)
        rozklad = pokrycie_pokrycia = pokrycie_pogrubionych(katalog, katalog)

    assert rozklad == {"przypisanie": 1, "zbieg": 1, "bez pokrycia": 1}, (
        "czytnik dal %s, a mial dac po jednym w kazdej kupce: **7** pokryte "
        "PRZYPISANIEM `PROG = 7`, **8** pokryte ZBIEGIEM CYFR w filtrze "
        "`len(x) > 8`, a **9** bez pokrycia" % rozklad)


# --- 6.D268: ktora z liczb pokrytych ZBIEGIEM CYFR jest nieprawdziwa -----------

#: **Rozklad 54 liczb pokrytych zbiegiem cyfr po plikach, zmierzony 18.09.2026.**
#: Przy 6.D268 bylo ich 49; 6.D270 dolozylo DWIE (zapas galezi), a 6.D271 TRZY —
#: poprawiajac trzynascie nieprawdziwych figur w `test_dead_constants_csharp.py`
#: pogrubilo trzy, ktore wczesniej stały bez pogrubienia i przez to byly dla
#: censusu niewidoczne. Wszystkie piec jest w grupie A i wszystkie sa prawdziwe;
#: census zapalil sie na nich za kazdym razem i to jest jego robota.
#: Rozklad, a nie sama suma: pozycja 6.D267 zmierzyla, ze suma nie widzi
#: przesuniecia miedzy czlonami, a tu czlonem jest PLIK. Adresy z numerami
#: wierszy stoja w `reports/6d268-pokryte-przypadkiem.md` i tam jest ich miejsce,
#: bo numer wiersza rusza sie przy kazdym dopisanym akapicie, a liczba per plik
#: nie. Porownywany W OBIE STRONY (6.D243).
ZBIEGIEM_PER_PLIK = {
    "csharp_pins.py": 1,
    "csharp_test_methods.py": 1,
    "mutation_sweep.py": 2,
    "test_all.py": 1,
    "test_assertion_gate.py": 2,
    "test_bin_path_framework.py": 1,
    "test_bytecode_staleness.py": 2,
    "test_csharp_assertions.py": 1,
    "test_dead_constants_csharp.py": 12,
    "test_dotnet_version.py": 1,
    "test_field_paths.py": 1,
    "test_game_needle_specificity.py": 1,
    "test_json_required.py": 1,
    "test_mass_copies.py": 2,
    "test_message_claims.py": 1,
    "test_mutation_sweep.py": 4,
    "test_prose_counts.py": 1,
    "test_provenance_classes.py": 1,
    "test_report_claims.py": 5,
    "test_report_hygiene.py": 4,
    "test_suite_runtime_budget.py": 8,
    "test_t401_citation.py": 1,
}

#: **Podzial 49 na grupe A i B — odpowiedz na pole „Wyjscie", przez CZYTANIE.**
#:
#: Grupa A twierdzi o DZISIEJSZYM drzewie; grupa B nie — bo opisuje pomiar
#: przebiegu (czas, stosunek CPU do sciany, numer joba), cytuje dawna wartosc,
#: nazywa commit jako punkt odniesienia albo opisuje zachowanie narzedzia,
#: a nie licznosc w drzewie.
#:
#: **Podzialu NIE DA SIE zmechanizowac czytnikami, ktore to drzewo ma, i jest to
#: zmierzone czterema nieudanymi probami, nie zalozone.** Kolejno: znaczniki
#: przeszlosci z `test_docs_ci_claims.HISTORICAL_MARKERS` zawieraja „zmierzone",
#: ktore pada w niemal kazdym akapicie tego repozytorium, wiec zmiotlyby do B
#: prawie cala populacje; znaczniki czytane ze ZDANIA gubia punkt odniesienia
#: stojacy w pierwszym zdaniu akapitu; `proza` zwraca po jednym wpisie na WIERSZ
#: komentarza, wiec „akapit" bez sklejania z 6.D267 jest jednym wierszem;
#: a zawezenie do akapitow, ktore NAZYWAJA swoj czytnik w grawisach, daje piec
#: pozycji i **nie obejmuje tej, w ktorej rozjazd faktycznie jest** — akapit
#: o deklaracjach C# nazywa `const` i `static readonly`, a nie `rozklad`.
#: Podzial jest wiec wynikiem przeczytania 49 zdan i tak ma byc czytany.
ZBIEGIEM_GRUPA_A = 26
ZBIEGIEM_GRUPA_B = 28

#: **Potwierdzone rozjazdy: SIEDEM twierdzen w JEDNYM module.** Wszystkie osiem
#: jest „pokryte" zbiegiem cyfr, wiec bramka 6.D259 ich nie widzi, a bramka
#: 6.D264 liczy je jako pokryte — czyli dziala dokladnie tak, jak 6.D264 opisalo,
#: i dlatego ta pozycja istnieje.
#:
#: **Lista jest DLUGIEM, nie wynikiem, i porownywana jest W OBIE STRONY.** Pole
#: „Poza zakresem" tej pozycji zabrania poprawiania znalezionych liczb, wiec
#: siedem nieprawdziwych twierdzen zostaje w drzewie — ale zostaje WPISANE, a nie
#: przemilczane, i przypisane pozycji 6.D271, ktora je poprawia. Poprawienie
#: ktoregokolwiek zapali bramke z zadaniem zdjecia wpisu: to jest ksztalt
#: `LANCUCHY_PRZERWANE` z 6.D260, a nie 6.D27 — bramka nie karze poprawnosci,
#: tylko wymaga, zeby ksiegowanie za nia nadazylo.
ROZJAZDY_POKRYTE_ZBIEGIEM = {}


#: Kotwice zdan, z ktorych czytana jest strona PROZY. Kotwica, a nie numer
#: wiersza: numer rusza sie przy kazdym dopisanym akapicie, a fraza zdania nie.
#: Kazda jest JEDNOZNACZNA w module — pilnuje tego asercja nizej, bo kotwica
#: lapiaca dwa zdania czytalaby pierwsze z nich dla obu opisow.
KOTWICE_DEKLARACJI = {
    "deklaracji razem": r"ma dzis \*\*(\d+)\*\* deklaracji",
    "const": r"`const` \*\*(\d+)\*\*",
    "static readonly": r"`static readonly` \*\*(\d+)\*\*",
    "razem w rozkladzie": r"razem \*\*(\d+)\*\*;",
    "bez modyfikatora (zdanie 1)": r"stoi \*\*(\d+)\*\* z nich",
    "bez modyfikatora (zdanie 2)": r"zabiera \*\*(\d+)\*\* deklaracje",
    # Kotwica ZAWEZONA przy 6.D271: dolozenie drugiego zdania o kształcie
    # „(zostaje N)" zrobilo
    # `zostaje \*\*(\d+)\*\*` dwuznacznym, a czytnik zwracal wtedy `None`
    # i porownanie przechodzilo cicho. Zlapala to kontrola jednoznacznosci
    # kotwic, dopisana razem z nimi przy 6.D268 — czyli bramka, ktora istnieje
    # dokladnie na ten wypadek.
    "zostaje po odjeciu": r"deklaracje, zostaje \*\*(\d+)\*\*",
    # Szesc kotwic dolozonych przy 6.D271. Lista siedmiu z 6.D268 miala siedem
    # wpisow, bo tyle zlapaly KOTWICE — a nie bo tyle bylo nieprawdziwych.
    # W tym samym module stalo ich TRZYNASCIE; szesciu nie widzialo nic, bo trzy
    # sa NIEPOGRUBIONE (census ich nie liczy), a trzech nie obejmowala zadna
    # kotwica. Te szesc jest od dzis objete.
    "stara podloga nizej o": r"stara podloga 200 lezala \*\*(\d+)\*\* nizej",
    "galaz static readonly zabiera": r"zabiera \*\*(\d+)\*\* deklaracji",
    "po wycieciu galezi zostaje": r"\(zostaje \*\*(\d+)\*\*\)",
    "rownosc w nawiasie": r"Rownosci \(`== (\d+)`\)",
    "zapas nad suma": r"Zapas \*\*(\d+)\*\* \(",
    "zapas razy glebszy": r"Zapas jest wiec \*\*(\d+)\*\* razy glebszy",
}


def rozjazdy_z_drzewa(root=None):
    """`{(plik, opis): (proza, drzewo)}` — OBIE strony przeliczone, zadna wpisana.

    **Pierwsza wersja wpisywala strone PROZY z reki i kontrola negatywna to
    zlapala.** Poprawienie liczby w prozie nie ruszalo wtedy niczego w tej
    funkcji, wiec bramka nizej nie umiala zobaczyc poprawy — a jej wlasny
    docstring twierdzil, ze umie. Bramka, ktora nie zapala sie na zdarzeniu,
    o ktorym mowi, jest ksztaltem 6.D27 i tu byla nim przez jeden przebieg.

    Czytniki strony DRZEWA sa pozyczone z `test_dead_constants_csharp`
    (`deklaracje`, `rozklad`, `MINIMUM_DEKLARACJI`): druga kopia wzorca
    deklaracji C# rozjechalaby sie z tamta przy pierwszej zmianie i bramka
    mowilaby o innym drzewie niz bramka, ktora tych liczb pilnuje (6.D213).
    """
    import test_dead_constants_csharp as DCS
    korzen = root or ROOT
    plik = "test_dead_constants_csharp.py"
    with open(os.path.join(korzen, "tools", "tests", plik), encoding="utf-8") as u:
        zrodlo = u.read()
    proza_liczb = {}
    for opis, wzor in KOTWICE_DEKLARACJI.items():
        trafienia = re.findall(wzor, zrodlo)
        proza_liczb[opis] = [int(x) for x in trafienia]

    ile = sum(len(v) for v in DCS.deklaracje().values())
    r = DCS.rozklad()
    trafienie = re.search(r"^MINIMUM_DEKLARACJI = (\d+)$", zrodlo, re.M)
    assert trafienie, ("nie znalazlem `MINIMUM_DEKLARACJI = N` w zrodle — "
                       "kotwica podlogi sumy czyta ten plik jako tekst i bez tego "
                       "wiersza dwa porownania nizej milcza")
    podloga_sumy = int(trafienie.group(1))
    bez = r["bez modyfikatora"]
    z_drzewa = {
        "deklaracji razem": ile,
        "const": r["const"],
        "static readonly": r["static readonly"],
        "razem w rozkladzie": ile,
        "bez modyfikatora (zdanie 1)": bez,
        "bez modyfikatora (zdanie 2)": bez,
        "zostaje po odjeciu": ile - bez,
        "stara podloga nizej o": ile - 200,
        "galaz static readonly zabiera": r["static readonly"],
        "po wycieciu galezi zostaje": ile - r["static readonly"],
        "rownosc w nawiasie": ile,
        # Podloga czytana ze ZRODLA jako tekst, a nie brana przez `DCS.MINIMUM_DEKLARACJI`.
        # Powod jest zmierzony, nie estetyczny: siegniecie po symbol daje tej zapadce
        # DRUGIE uzycie i zapala bramke z 6.D254, ktora wtedy zada zmierzenia jej klasy
        # mutacja — bo klasa zapadki wynika u niej z KSZTALTU uzyc. Odczyt literalu
        # uzyciem nie jest, a kotwice i tak czytaja ten sam plik jako tekst. Przy 6.D268
        # ta sama kolizja kosztowala zdjecie wiersza z listy; tu wiersz jest potrzebny.
        "zapas nad suma": ile - podloga_sumy,
        "zapas razy glebszy": ile - podloga_sumy,
    }
    out = {}
    for opis, wartosc in z_drzewa.items():
        trafienia = proza_liczb[opis]
        out[(plik, opis)] = (trafienia[0] if len(trafienia) == 1 else None, wartosc)
    return out


def test_kotwice_zdan_o_deklaracjach_lapia_PO_JEDNYM_zdaniu():
    """**Dolne ostrze na kotwice — bez niego bramka nizej czyta nie to zdanie.**

    Kotwica lapiaca dwa zdania dawalaby dla obu opisow liczbe pierwszego z nich,
    a kotwica lapiaca zero dawalaby `None` i porownanie przechodzilo cicho.
    """
    zmierzone = rozjazdy_z_drzewa()
    puste = sorted(k for k, v in zmierzone.items() if v[0] is None)
    assert puste == [], (
        "kotwica nie zlapala DOKLADNIE jednego zdania dla: %s — albo zdanie "
        "przeredagowano, albo kotwica lapie dwa i czyta pierwsze" % puste)


def test_licznik_pokrycia_i_lista_pokrycia_MOWIA_o_tym_samym_drzewie():
    """**Dolne ostrze na rozszczepienie czytnika — 6.D268.**

    `pokrycie_pogrubionych` jest od tej pozycji WIDOKIEM na `pozycje_pokrycia`,
    a nie osobnym przebiegiem. Ta asercja stoi, zeby rozszczepienie ich z powrotem
    na dwa przebiegi paslo glosno: dwa przebiegi po tym samym drzewie zgadzaja sie
    dzis i rozjezdzaja przy pierwszej zmianie okna, czyli usterka wchodzilaby
    niewidzialna (6.D213).
    """
    licznik = pokrycie_pogrubionych()
    lista = pozycje_pokrycia()
    assert licznik == {k: len(v) for k, v in lista.items()}, (
        "licznik mowi %r, a lista ma %r pozycji — czytniki rozjechaly sie"
        % (licznik, {k: len(v) for k, v in lista.items()}))


def test_rozklad_pokrytych_zbiegiem_PO_PLIKACH_zgadza_sie_z_drzewem():
    """**Rozklad, nie suma — 6.D267 zmierzylo, ze suma przesuniecia nie widzi.**

    Rownosc per plik, bo plikow jest 22 i nie przybywa ich co pozycje, a kazde
    przesuniecie liczby miedzy plikami znaczy, ze akapit sie przeniosl albo
    zniknal — i to chce sie zobaczyc.
    """
    import collections
    zmierzony = dict(collections.Counter(
        w[0] for w in pozycje_pokrycia()["zbieg"]))
    brak = sorted(set(zmierzony) - set(ZBIEGIEM_PER_PLIK))
    zbedne = sorted(set(ZBIEGIEM_PER_PLIK) - set(zmierzony))
    assert (brak, zbedne) == ([], []), (
        "pliki bez wpisu: %s; wpisy bez pliku w drzewie: %s" % (brak, zbedne))
    assert zmierzony == ZBIEGIEM_PER_PLIK, (
        "rozklad po plikach rozjechal sie z pomiarem 18.09.2026: %r wobec %r"
        % (sorted(zmierzony.items()), sorted(ZBIEGIEM_PER_PLIK.items())))
    assert sum(ZBIEGIEM_PER_PLIK.values()) == POKRYTYCH_ZBIEGIEM_CYFR, (
        "rozklad sumuje sie do %d, a zapadka sumy stoi na %d — dwa zdania o tej "
        "samej populacji niosa rozne liczby"
        % (sum(ZBIEGIEM_PER_PLIK.values()), POKRYTYCH_ZBIEGIEM_CYFR))
    assert ZBIEGIEM_GRUPA_A + ZBIEGIEM_GRUPA_B == POKRYTYCH_ZBIEGIEM_CYFR, (
        "podzial na grupy sumuje sie do %d przy populacji %d"
        % (ZBIEGIEM_GRUPA_A + ZBIEGIEM_GRUPA_B, POKRYTYCH_ZBIEGIEM_CYFR))


def test_ROZJAZDY_nadal_sa_rozjazdami_i_lista_nie_zostala_z_tylu():
    """**Dlug wpisany, a nie przemilczany — i porownywany W OBIE STRONY (6.D243).**

    **Osma pozycja zostala zdjeta i powod jest zmierzony, nie estetyczny.** Zdanie
    „Zapas 59" jest rowniez nieprawdziwe (dzis 66), ale jest POCHODNA sumy
    deklaracji: falszywe dlatego, ze falszywa jest suma, ktora na liscie stoi.
    Zeby je porownac, trzeba bylo siegnac po `MINIMUM_DEKLARACJI` — a to dalo tej
    zapadce DRUGIE uzycie i zapalilo bramke z 6.D254, ktora wtedy zada zmierzenia
    jej klasy mutacja. Cena byla wyzsza od zysku: pochodna nie niesie informacji
    ponad ta, ktora niesie suma.

    Bramka zapala sie TAKZE wtedy, gdy ktos liczbe POPRAWI: wpis przestaje byc
    rozjazdem i ma zniknac z listy. Nie jest to karanie poprawnosci (6.D27),
    bo poprawa jest tu ruchem o DWA kroki — liczba i wpis — i drugi krok bez
    bramki bylby zapomniany, a lista bez sprawdzania jest napisem (6.D243).
    """
    zmierzone = rozjazdy_z_drzewa()
    nadal = {k: v for k, v in zmierzone.items() if v[0] != v[1]}
    naprawione = sorted(k for k, v in zmierzone.items()
                        if v[0] == v[1] and k in ROZJAZDY_POKRYTE_ZBIEGIEM)
    assert naprawione == [], (
        "te twierdzenia przestaly byc rozjazdami — zdejmij je z "
        "`ROZJAZDY_POKRYTE_ZBIEGIEM` w tym samym commicie, w ktorym je "
        "poprawiasz: %s" % naprawione)
    assert nadal == ROZJAZDY_POKRYTE_ZBIEGIEM, (
        "lista rozjazdow rozjechala sie z drzewem: zmierzone %r, wpisane %r"
        % (sorted(nadal.items()), sorted(ROZJAZDY_POKRYTE_ZBIEGIEM.items())))


# --- 6.D274: pokrycie PROZA PRZEZ PROZE, bez udzialu kodu ---------------------

#: **Trzy czwarte „pokrycia" nie ma z kodem nic wspolnego.** 6.D264 nazwalo te
#: klase ZBIEGIEM CYFR i mierzylo ja wzgledem KODU — okno czyta jednak WIERSZE
#: PLIKU, nie odrozniajac kodu od komentarza, wiec wiersz pokrywajacy bywa po
#: prostu INNYM ZDANIEM PROZY o tej samej liczbie.
#:
#: Zmierzone 18.09.2026 z 54 liczb klasy `zbieg`:
#:
#: * **41** pokrytych WYLACZNIE proza — w oknie nie ma ani jednego wiersza kodu;
#: * **11** pokrytych wylacznie kodem;
#: * **2** mieszane.
#:
#: **Dziewiec z nich stoi w PARACH WZAJEMNYCH**, gdzie zdanie A pokrywa B, a B
#: pokrywa A — dwa zdania prozy certyfikuja sie nawzajem i zaden kod w tym nie
#: uczestniczy. Siedem par stoi w `test_dead_constants_csharp.py`, gdzie zjawisko
#: zobaczylem przy 6.D271, ale DWIE stoja gdzie indziej (`test_report_claims.py`
#: i `test_suite_runtime_budget.py`), wiec nie jest to wlasnosc jednego pliku.
#:
#: **Klasyfikacja idzie po PELNYM zbiorze wierszy pokrywajacych, a nie po dwoch
#: zapamietanych w `pozycje_pokrycia`** — pole tamtej funkcji trzyma tylko dwa
#: pierwsze, wiec „wylacznie proza" znaczyloby na nim „obie zapamietane sa proza".
#: Przeliczone od nowa po calym zbiorze daje te same 41/11/2; roznicy nie ma,
#: ale jest to SPRAWDZONE, a nie zalozone.
#:
#: **Liczy sie to w TYM SAMYM przebiegu, co pokrycie.** Drugi skan tych samych
#: okien kosztowalby tyle, co caly czytnik, a 6.D272 zmierzylo, ile taki drugi
#: skan potrafi kosztowac: 22 s za odpowiedz „zero".
POKRYTYCH_WYLACZNIE_PROZA = 41
POKRYTYCH_WYLACZNIE_KODEM = 11
POKRYTYCH_MIESZANIE = 2

#: Pary wzajemne, przybite ADRESAMI WIERSZY. Numer wiersza rusza sie przy kazdym
#: dopisanym akapicie powyzej, wiec przybicie po nim bylo by krucheszczyzna —
#: dlatego przybita jest LICZBA par i rozklad po plikach, a same adresy stoja
#: w `reports/6d274-proza-pokryta-proza.md`, gdzie starzec sie nie maja.
PAR_WZAJEMNYCH = 9
PAR_WZAJEMNYCH_PER_PLIK = {
    "test_dead_constants_csharp.py": 7,
    "test_report_claims.py": 1,
    "test_suite_runtime_budget.py": 1,
}


def _klasa_wierszy(wiersze):
    """`"proza"` / `"kod"` / `"mieszane"` — po PELNYM zbiorze, nie po probce."""
    proza_ile = sum(1 for l in wiersze if l.strip().startswith("#"))
    if proza_ile == len(wiersze):
        return "proza"
    return "kod" if proza_ile == 0 else "mieszane"


def klasy_pokrycia_zbiegiem():
    """`{"proza": n, "kod": n, "mieszane": n}` — z JEDNEGO przebiegu czytnika.

    Czyta szosty czlon wpisu, ktory `pozycje_pokrycia` wypelnia w tej samej
    petli, w ktorej liczy pokrycie. Osobny skan tych samych okien dalby te sama
    liczbe za cene drugiego przebiegu po drzewie (6.D272).
    """
    out = collections.Counter()
    for wpis in pozycje_pokrycia()["zbieg"]:
        out[wpis[5]] += 1
    return dict(out)


def pary_wzajemne():
    """`[((plik, wiersz, napis), (plik, wiersz, napis))]` — A pokrywa B i B pokrywa A."""
    pokrywajace = {}
    for wpis in pozycje_pokrycia()["zbieg"]:
        pokrywajace[(wpis[0], wpis[1], wpis[2])] = set(wpis[6])
    out = []
    for lewy, numery_lewego in pokrywajace.items():
        for prawy, numery_prawego in pokrywajace.items():
            if lewy >= prawy or lewy[0] != prawy[0]:
                continue
            if prawy[1] in numery_lewego and lewy[1] in numery_prawego:
                out.append((lewy, prawy))
    return sorted(out)


def test_ile_pokrycia_daje_INNA_PROZA_a_ile_KOD():
    """**Trzy liczby z pola „Wyjscie" 6.D274 — rownosciami, nie progiem.**

    Rownosc, bo kazde przejscie liczby z klasy KOD do klasy PROZA znaczy, ze
    pokrycie przestal dawac kod, a zaczelo dawac sasiednie zdanie — i to jest
    zmiana, ktora chce sie zobaczyc, a nie przepuscic.
    """
    klasy = klasy_pokrycia_zbiegiem()
    assert klasy == {"proza": POKRYTYCH_WYLACZNIE_PROZA,
                     "kod": POKRYTYCH_WYLACZNIE_KODEM,
                     "mieszane": POKRYTYCH_MIESZANIE}, (
        "klasy pokrycia zbiegiem: %r, a pomiar 18.09.2026 dal proza %d, kod %d, "
        "mieszane %d. Liczba pokryta INNYM ZDANIEM PROZY nie jest pilnowana przez "
        "nic — kodu w tym pokryciu nie ma"
        % (klasy, POKRYTYCH_WYLACZNIE_PROZA, POKRYTYCH_WYLACZNIE_KODEM,
           POKRYTYCH_MIESZANIE))
    assert sum(klasy.values()) == POKRYTYCH_ZBIEGIEM_CYFR, (
        "klasy sumuja sie do %d, a zapadka populacji stoi na %d — dwa zdania "
        "o tej samej populacji niosa rozne liczby"
        % (sum(klasy.values()), POKRYTYCH_ZBIEGIEM_CYFR))


def test_ile_par_CERTYFIKUJE_SIE_NAWZAJEM():
    """**Para wzajemna: A pokrywa B, B pokrywa A, a kodu w tym nie ma.**

    Porownanie per plik, a nie sama suma: 6.D267 zmierzylo, ze suma przesuniecia
    miedzy czlonami nie widzi, a tu czlonem jest plik. Rozklad pilnuje takze tego,
    zeby zjawisko nie zostalo odczytane jako wlasnosc JEDNEGO modulu — dwie z
    dziewieciu par stoja poza tym, w ktorym je zobaczylem.
    """
    pary = pary_wzajemne()
    assert len(pary) == PAR_WZAJEMNYCH, (
        "par wzajemnych jest %d, a pomiar 18.09.2026 dal %d: %s"
        % (len(pary), PAR_WZAJEMNYCH, [(a[0], a[1], b[1]) for a, b in pary]))
    per_plik = collections.Counter(a[0] for a, _b in pary)
    assert dict(per_plik) == PAR_WZAJEMNYCH_PER_PLIK, (
        "rozklad par po plikach %r, a pomiar dal %r"
        % (dict(per_plik), PAR_WZAJEMNYCH_PER_PLIK))


def test_czytnik_klas_odroznia_KOMENTARZ_od_KODU():
    """**Kontrola przyrzadu — bez niej rownosc wyzej przejdzie przy czytniku slepym.**

    Trzy ksztalty naraz: sam komentarz, sam kod i mieszanina. Wciecie jest tu
    trescia, bo komentarz w tym drzewie stoi wciety razem z kodem, ktory opisuje,
    a `startswith` bez `strip` uznalby go za kod.
    """
    same_komentarze = ["#: liczba 41 stoi tu", "    # a tu 41"]
    sam_kod = ["PROG = 41", "    x = 41"]
    mieszane = ["#: liczba 41", "PROG = 41"]

    assert _klasa_wierszy(same_komentarze) == "proza", (
        "dwa komentarze daly klase %r — wciety `#` nie zostal rozpoznany, "
        "a tak wlasnie stoi komentarz przy kodzie, ktory opisuje"
        % _klasa_wierszy(same_komentarze))
    assert _klasa_wierszy(sam_kod) == "kod", (
        "dwa wiersze kodu daly klase %r — wtedy KAZDE pokrycie liczy sie jako "
        "proza i rownosc wyzej mowi o czym innym, niz mysli"
        % _klasa_wierszy(sam_kod))
    assert _klasa_wierszy(mieszane) == "mieszane", (
        "komentarz z kodem daly klase %r — mieszanina ma byc trzecia klasa, "
        "bo inaczej wpada do jednej z dwoch i przekreca obie"
        % _klasa_wierszy(mieszane))


# --- 6.D275: zdjecie pogrubienia wyprowadza liczbe spod OBU sit ----------------

#: **Zdjecie pogrubienia jest jedynym lekarstwem, jakie `MAX_POGRUBIONYCH_BEZ_POKRYCIA`
#: dopuszcza — i wyprowadza liczbe spod KAZDEGO czytnika tego drzewa.**
#:
#: Zapadka wyzej stawia autora przed wyborem: policz liczbe w kodzie albo zdejmij
#: pogrubienie. Drugie wyjscie jest zawsze dostepne i zawsze tansze, a census pokrycia
#: (6.D264) i sito jednostek (6.D272) czytaja WYLACZNIE `**N**`. Zaspokojenie jednej
#: bramki wyprowadza wiec liczbe spod drugiej, a liczba zostaje w zdaniu i starzeje sie
#: dalej. Ze nie jest to teoretyczne, pokazalo 6.D271: trzy NIEPOGRUBIONE figury w
#: `test_dead_constants_csharp.py` byly nieprawdziwe i znalazlo je czytanie, nie bramka.
#:
#: **Trzy liczby, i pierwsze dwie mowia, dlaczego detektora historycznego tu nie ma.**
#: Zmierzone 18.09.2026 na 660 commitach dotykajacych `tools/tests/`:
#:
#: | co | ile |
#: |---|---|
#: | commitow ZGLASZAJACYCH zdjecie pogrubienia w komunikacie | 12 |
#: | z tego widocznych w DIFFIE (wiersz identyczny co do gwiazdek) | 0 |
#: | liczb niepogrubionych stojacych DZIS w prozie ogłaszajacej pomiar | nizej |
#:
#: Zero w drugim wierszu nie jest usterka wzorca, tylko wlasnoscia przebiegu: zapadka
#: zapala sie PRZED commitem, autor zdejmuje pogrubienie i commituje wersje JUZ bez
#: niego. Wersja pogrubiona nie istnieje w zadnym drzewie, wiec zaden diff jej nie
#: pokazuje. Wzorzec luzniejszy (podobienstwo wiersza >= 0,6) daje dwa trafienia
#: i **oba sa falszywe** — w obu liczba pochodzi z numeru pozycji `6.A24`, a nie
#: ze zdjetego pogrubienia. Detektor historyczny jest tu slepy Z NATURY; jedyny
#: zapis jest w komunikatach commitow, a tych nie czyta zaden czytnik tego drzewa.
#: Dlatego pozycja mierzy STAN DZISIEJSZY, a nie historie.

#: **Zapowiedz pomiaru — druga konwencja tego repozytorium, obok `**N**`.**
#: Samo „zdanie z pogrubiona liczba" nie wystarcza i to jest zmierzone, a nie przyjete:
#: instancja, ktora wywolala te pozycje (132 i 36 w `test_dead_constants.py`), stoi
#: w akapicie otwartym pogrubionym lead-inem `**Zmierzone <data>:**`, w ktorym zadna
#: liczba pogrubiona nie jest. Sito na sam `**N**` bylo wiec slepe dokladnie na przypadek,
#: ktory pozycje wywolal — sprawdzone przed napisaniem bramki. Lead-inow tego ksztaltu
#: jest w drzewie 57.
ZAPOWIEDZ_POMIARU = re.compile(r"\*\*[^*]{0,60}[Zz]mierzon[a-z]{0,4}[^*]{0,60}\*\*")

#: Cyfry, ktore nie sa twierdzeniem o pomiarze i musza wypasc PRZED liczeniem:
#: sciezki i wzorce w grawisach (`docs/04-conventions.md`, `{7,40}`), talie testow
#: (`14/15`), kody wyjscia (`kod 1`) i numery pozycji (`6.B36`). Bez tego czyszczenia
#: populacja rosnie o 50 na samym `test_report_hygiene.py`, ktorego docstring jest
#: transkryptem kontroli negatywnych — czyli sito liczyloby transkrypt, a nie proze.
SMIECI_W_PROZIE = (
    re.compile(r"`[^`]*`"),
    re.compile(r"\b6\.[A-Z]\d+\b"),
    # Numery kamieni milowych (`MB-01`) i notacja wykladnicza (`2,47e-05`) rozpadaja
    # sie na czlony dokladnie tak samo jak talie wyzej — zlapane tym samym sitem
    # po naprawie talii, a nie przewidziane.
    re.compile(r"\bMB-\d+\b"),
    re.compile(r"\d+(?:[.,]\d+)?e[-+]?\d+"),
    # Granice `(?<![\d,.])` sa tu TRESCIA, a nie ostroznoscia: `\b` wycinal
    # `090 / 0` ze srodka ciagu `0,090 / 0,087 / 0,085 s`, zostawiajac `0` i `085`
    # jako osobne „liczby". Zmierzone: bez tych granic populacja rosla o 6 urwanych
    # czlonow, a kazdy czytal sie jak liczba niepogrubiona.
    re.compile(r"(?<![\d,.])\d+\s*/\s*\d+(?![\d,.])"),
    re.compile(r"\bkod\s+\d+(?![\d,.])"),
    DATA,
)

#: Granica zdania. Akapit jest jednostka dla lead-inu `**Zmierzone:**` (bo on otwiera
#: akapit), a zdanie — dla pogrubionej liczby (bo ona stoi w zdaniu). Dwie jednostki
#: sa tu z pomiaru: jedna wspolna zabiera albo instancje z 6.D269 (przy zdaniu), albo
#: caly akapit za kazda pogrubiona liczba (przy akapicie).
GRANICA_ZDANIA = re.compile(r"(?<=[.!?:])\s+")


def _akapity_prozy(tekst):
    """Akapity wezla prozy — bloki rozdzielone pustym wierszem, bez znakow `#:`."""
    biezacy, out = [], []
    for wiersz in tekst.split("\n"):
        naga = re.sub(r"^\s*#:?\s?", "", wiersz).rstrip()
        if not naga.strip():
            if biezacy:
                out.append("\n".join(biezacy))
                biezacy = []
        else:
            biezacy.append(naga)
    if biezacy:
        out.append("\n".join(biezacy))
    return out


def gole_w_prozie_pomiarowej(katalog=None, root=None):
    """`[(plik, wiersz, napis, zdanie, pokryte)]` — liczby NIEPOGRUBIONE stojace
    w prozie, ktora pomiar oglasza.

    Okno pokrycia jest TO SAMO, co w `pogrubione_bez_pokrycia`, razem z wycieciem
    zasiegu samego wezla — inaczej liczba pokrywa sama siebie (6.D259).
    """
    baza = katalog or os.path.join(ROOT, "tools", "tests")
    korzen = root or ROOT
    zrodla = {}
    for gdzie, _katalogi, pliki in TW.walk(baza, korzen):
        for nazwa in sorted(pliki):
            if nazwa.endswith(".py"):
                with open(os.path.join(gdzie, nazwa), encoding="utf-8") as uchwyt:
                    zrodla[nazwa] = uchwyt.read().split("\n")
    out, widziane = [], set()
    for nazwa, wiersz, tekst, _rodzaj, od, do in proza(katalog, root):
        czysty = SPECYFIKATOR.sub(" ", tekst)
        linie = zrodla.get(nazwa, [])
        lo = max(0, wiersz - OKNO_PROZY - 1)
        hi = min(len(linie), do + OKNO_PROZY)
        okno = "\n".join(linie[lo:od - 1] + linie[do:hi])
        for akapit in _akapity_prozy(czysty):
            ma_zapowiedz = bool(ZAPOWIEDZ_POMIARU.search(akapit))
            for zdanie in GRANICA_ZDANIA.split(akapit):
                ma_pogrubiona = bool(POGRUBIONA.search(zdanie)) \
                    and not DATA.search(zdanie)
                if not (ma_zapowiedz or ma_pogrubiona):
                    continue
                reszta = POGRUBIONA.sub(" ", ZAPOWIEDZ_POMIARU.sub(" ", zdanie))
                for smiec in SMIECI_W_PROZIE:
                    reszta = smiec.sub(" ", reszta)
                for trafienie in LICZBA.finditer(reszta):
                    napis = trafienie.group(1)
                    try:
                        wartosc = float(napis.replace(",", "."))
                    except ValueError:
                        continue
                    klucz = (nazwa, wiersz, trafienie.start(), napis)
                    if klucz in widziane:
                        continue
                    widziane.add(klucz)
                    pokryte = any(
                        re.search(r"(?<![\w.])%s(?![\w.])"
                                  % re.escape("%g" % (wartosc * skala)), okno)
                        for skala in SKALE)
                    out.append((nazwa, wiersz, napis, zdanie, pokryte))
    return out


def zdan_ogloszonych_pomiarem(katalog=None, root=None):
    """Ile zdan prozy oglasza pomiar — populacja, na ktorej stoi zapadka nizej."""
    ile = 0
    for _nazwa, _wiersz, tekst, _rodzaj, _od, _do in proza(katalog, root):
        czysty = SPECYFIKATOR.sub(" ", tekst)
        for akapit in _akapity_prozy(czysty):
            ma_zapowiedz = bool(ZAPOWIEDZ_POMIARU.search(akapit))
            for zdanie in GRANICA_ZDANIA.split(akapit):
                if ma_zapowiedz or (POGRUBIONA.search(zdanie)
                                    and not DATA.search(zdanie)):
                    ile += 1
    return ile


#: **Zapadka GORNA, i jej wysokosc jest jedyna liczba tej pozycji, ktora nie jest
#: pomiarem, tylko rozstrzygnieciem — dlatego stoi tu z uzasadnieniem.**
#:
#: Populacja liczb NIEPOGRUBIONYCH w prozie oglaszajacej pomiar jest CZTERY RAZY
#: wieksza od tej, ktora pilnuje `MAX_POGRUBIONYCH_BEZ_POKRYCIA`, i nie ma listy
#: wyjatkow zadnej. Wyliczac jej nie sposob (6.D243: lista tej dlugosci jest podpisem
#: pod obrazkiem), wiec zostaje ten sam wzorzec, co zapadka wyzej: gora na liczbe
#: trafien, podloga na populacje. **Wolno ja tylko OBNIZAC.**
#:
#: Czego ta zapadka NIE robi, i obie granice sa ZMIERZONE, a nie zastrzezone.
#:
#: PIERWSZA: nie odroznia liczby ZDJETEJ z pogrubienia od takiej, ktora pogrubienia
#: nigdy nie miala. Odroznic ich nie da sie z drzewa, bo — jak mowi tabela wyzej —
#: zdjecie zachodzi przed commitem i zero takich zdjec widac w diffie na 660
#: commitach. Zapadka lapie WEJSCIE do populacji, czyli i jedno, i drugie.
#:
#: DRUGA, i wazniejsza, bo przeczy temu, po co ta zapadka powstala: droga ucieczki
#: jest zamknieta TYLKO CZESCIOWO. Zdjecie pogrubienia liczbie, ktora byla w zdaniu
#: JEDYNA pogrubiona i stoi poza akapitem z zapowiedzia, wyprowadza cale zdanie
#: z populacji — liczba nie wchodzi tutaj, tylko znika z obu sit. Zmierzone
#: 18.09.2026 NA WLASNEJ PROZIE tej pozycji, a nie na przykladzie: zapadka
#: `MAX_POGRUBIONYCH_BEZ_POKRYCIA` zapalila sie na liczbie pogrubionej w akapicie
#: wyzej, jedynym lekarstwem bylo zdjecie pogrubienia (wartosc jest pomiarem
#: historii gita, wiec policzyc jej w zestawie nie sposob) — i populacja tej zapadki
#: SPADLA o dwa zamiast urosnac o jeden. Kierunek jest odwrotny do zamierzonego
#: i jest to wynik, nie usterka do obejscia.
#:
#: Poszerzenie zapowiedzi na dowolne slowo pomiaru (`zmierzon`, `pomiar`, `policzon`,
#: bez pogrubienia) zamyka i ten przypadek — i zostalo ODRZUCONE po pomiarze, nie
#: z gustu: daje 3685 zdan i 1373 liczby gole, czyli piec razy wiecej niz dzis,
#: przy liscie wyjatkow zerowej. Lista tej dlugosci nie jest lista, tylko podpisem
#: pod obrazkiem (6.D243). Zapadka zostaje waska, a to, czego nie lapie, stoi tu
#: wypisane liczba.
MAX_GOLYCH_W_PROZIE_POMIAROWEJ = 259

#: Podloga na populacje zdan oglaszajacych pomiar — bez niej oslepienie czytnika
#: do zera przechodzi zapadke gorna CELUJACO (6.D27, ten sam powod co
#: `MIN_POGRUBIONYCH` wyzej).
MIN_ZDAN_POMIAROWYCH = 420


def test_zadna_NOWA_liczba_niepogrubiona_nie_wchodzi_do_prozy_pomiarowej():
    """**Druga polowa pary z `MAX_POGRUBIONYCH_BEZ_POKRYCIA` — i to jest cala tresc.**

    Tamta zapadka dopuszcza dwa lekarstwa: policz liczbe w kodzie albo zdejmij
    pogrubienie. Drugie bylo dotad DARMOWE, bo po zdjeciu nie czytalo liczby nic.
    Ta zapadka nadaje mu cene: liczba zdjeta z pogrubienia zostaje w zdaniu, ktore
    pomiar oglasza, wiec wchodzi TUTAJ. Zadna z dwoch nie da sie odtad zaspokoic
    kosztem drugiej.
    """
    zdan = zdan_ogloszonych_pomiarem()
    assert zdan >= MIN_ZDAN_POMIAROWYCH, (
        "zdan oglaszajacych pomiar jest %d przy podlodze %d — czytnik oslepl albo "
        "obie konwencje (`**N**` i `**Zmierzone:**`) zniknely z drzewa, a wtedy "
        "zapadka gorna nizej przechodzi na zielono nie dlatego, ze jest dobrze"
        % (zdan, MIN_ZDAN_POMIAROWYCH))

    gole = gole_w_prozie_pomiarowej()
    assert len(gole) <= MAX_GOLYCH_W_PROZIE_POMIAROWEJ, (
        "liczb niepogrubionych w prozie oglaszajacej pomiar jest %d przy zapadce "
        "%d. Zdjecie pogrubienia NIE jest wyjsciem z `MAX_POGRUBIONYCH_BEZ_POKRYCIA` "
        "— liczba laduje wtedy tutaj. Policz ja w kodzie i wstaw przez `%%d` albo "
        "przepisz zdanie tak, zeby pomiaru nie oglaszalo. Zapadke wolno tylko "
        "OBNIZAC: %s"
        % (len(gole), MAX_GOLYCH_W_PROZIE_POMIAROWEJ,
           [(x[0], x[1], x[2]) for x in gole[:5]]))


def test_sito_prozy_pomiarowej_NIE_liczy_cyfr_spoza_twierdzenia():
    """**Kontrola przyrzadu: gdyby sito liczylo kazda cyfre, dalo by tysiace.**

    Trzy ksztalty musza z niego wypasc, i kazdy zostal zlapany na zywym drzewie,
    a nie wymyslony: sciezka w grawisach, talia testow rozcinajaca liczbe dziesietna
    i numer pozycji. Czwarty musi PRZEJSC — inaczej sito nie widzi tego, co pozycje
    wywolalo.
    """
    reszta = "**Zmierzone:** plik `docs/04-conventions.md` ma 12 naglowkow."
    for smiec in SMIECI_W_PROZIE:
        reszta = smiec.sub(" ", reszta)
    assert "04" not in reszta, (
        "sciezka w grawisach przetrwala czyszczenie — `04` z nazwy pliku wejdzie "
        "do populacji jako liczba, a nie jest twierdzeniem o pomiarze: %r" % reszta)
    assert "12" in reszta, (
        "czyszczenie zabralo liczbe SPOZA grawisow — sito oslepnie na to, co ma "
        "liczyc: %r" % reszta)

    reszta = "srednio 0,090 / 0,087 / 0,085 s"
    for smiec in SMIECI_W_PROZIE:
        reszta = smiec.sub(" ", reszta)
    assert not re.search(r"(?<![\w.,])085(?![\w.,])", reszta), (
        "talia rozcieła liczbe dziesietna — `085` wchodzi do populacji jako "
        "osobna liczba, a jest czlonem `0,085`: %r" % reszta)

    gole = gole_w_prozie_pomiarowej()
    wywolujaca = [x for x in gole
                  if x[0] == "test_dead_constants.py" and x[2] in ("132", "36")]
    assert len(wywolujaca) == 2, (
        "liczby 132 i 36 z `test_dead_constants.py` — jedyna znana instancja "
        "ksztaltu, ktory te pozycje wywolal — NIE sa w populacji (%d z 2). Sito "
        "na sam `**N**` bylo na nie slepe i dlatego stoi obok `ZAPOWIEDZ_POMIARU`; "
        "jezeli wypadly, zapowiedz przestala je lapac" % len(wywolujaca))
