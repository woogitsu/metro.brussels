#!/usr/bin/env python3
"""Przejście po drzewie nie wchodzi w kopie pominięte w `.gitignore` (6.D74).

**Skąd ta bramka.** Zmierzone 09.09.2026 przy 6.D36: pierwszy skan tamtej pozycji,
liczony od korzenia, dał **6 i 12** wystąpień zamiast 1 i 2, bo wszedł do kopii drzewa
leżącej pod `.claude/`. Kopie niosły STARY kod, więc skan raportowałby usterkę już
naprawioną — przyrząd meldujący sprawdzenie, którego nie zrobił.

**Dlaczego pozycja, choć dziś prawie nic nie pada.** Trzynaście z czternastu wywołań
`os.walk` w `tools/` startowało z NAZWANEGO podkatalogu, a kopie 6.D36 leżały pod
`.claude/` — ochrona była **uboczna wobec nazewnictwa**, nie zapisana. Jedno przejście
liczone od korzenia wywraca wszystkie naraz i nic tego nie zgłasza.

**„Prawie nic" nie znaczy „nic", i to jest wynik pomiaru.** Kopia drzewa położona
10.09.2026 pod `tools/build/kopia/` (`build/` stoi w `.gitignore`, więc git jej nie
widzi, a `os.walk` owszem) zmieniła **jedną z piętnastu** liczb raportowanych przez
skany: `test_dead_constants.definicje` **917 → 1511**. Pozostałe czternaście stały,
bo albo startują poza `tools/`, albo zwracają ZBIÓR nazw, w którym kopia niczego
nowego nie wnosi. Jedna nieprawdziwa liczba w drzewie jest powodem wystarczającym.
"""
import collections
import ast
import os
import re
import sys
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tree_walk as TW  # noqa: E402

#: Pliki, w których `os.walk` wolno zawołać WPROST, z powodem. Klucz to ścieżka
#: względem korzenia, zapisana ukośnikami. Wpisów są dwa i oba są konieczne, a nie
#: wygodne: bez pierwszego nie ma czego wołać, bez drugiego nie da się POKAZAĆ, że
#: odsianie cokolwiek odsiewa — dowodem jest różnica wobec przejścia gołego.
WOLNO_WPROST = {
    "tools/tests/tree_walk.py":
        "to jest samo odsianie: `TW.walk` jest cienką warstwą nad `os.walk` "
        "i nie ma jak owinąć siebie.",
    "tools/tests/test_tree_walks.py":
        "kontrola różnicy: `test_the_filter_skips_a_branch_that_os_walk_enters` "
        "puszcza OBA przejścia po tym samym drzewie probnym i żąda, żeby wynik "
        "był różny. Przejście gołe jest tam PRZEDMIOTEM pomiaru, nie skrótem.",
}

#: Zapadka na słownik wyżej. Wolno ją tylko OBNIŻAĆ — ta sama reguła, co przy
#: `MAX_EXCEPTIONS` w `test_field_paths.py`: wyjątek jest tańszym wyjściem niż
#: przepisanie wołania, więc lista rośnie w jedną stronę z definicji.
MAX_WOLNO_WPROST = 2

# --- 6.D133: kierunek zapadki, czyli czy da się ją ruszyć w zakazaną stronę -------

#: Nazwa zapadki: przedrostek mówi, w którą stronę stała jest progiem.
ZAPADKA_NAZWA = re.compile(r"^(MAX|MIN|MINIMUM)_[A-Z0-9_]+$")

#: Operator odwrócony — po to, żeby każde porównanie czytać ZAWSZE od strony stałej.
#: `len(x) <= MAX_Y` i `MAX_Y >= len(x)` są tym samym zdaniem i muszą wpaść do jednej
#: kupki; bez tej tabeli kupki byłyby dwie, a klasyfikacja zależałaby od tego, po
#: której stronie ktoś stałą napisał.
ODWROTNY_OPERATOR = {"Lt": "Gt", "Gt": "Lt", "LtE": "GtE", "GtE": "LtE",
                     "Eq": "Eq", "NotEq": "NotEq"}

#: Trzy klasy i czwarta, która mówi o granicy przyrządu, a nie o zapadce.
PRZYBITA = "przybita"
CZESCIOWA = "czesciowa"
WOLNA = "wolna"
POZA_SKANEM = "poza skanem"


def _porownania_zapadek(katalog=None, root=None):
    """`{nazwa: [(relacja stałej do drugiej strony, kształt drugiej strony)]}`.

    Relacja jest zawsze zapisana OD STRONY STAŁEJ: `GtE` znaczy „stała >= tamto".
    Kształt drugiej strony to `ast.dump`, bo do rozstrzygnięcia potrzebna jest
    TOŻSAMOŚĆ wyrażenia (czy strażnik mierzy tę samą populację, co próg), a nie
    jego wartość — tej w czasie skanu nie ma.
    """
    baza = katalog or os.path.join(ROOT, "tools", "tests")
    korzen = root or ROOT
    out = {}
    for gdzie, _katalogi, pliki in TW.walk(baza, korzen):
        for nazwa_pliku in sorted(pliki):
            if not nazwa_pliku.endswith(".py"):
                continue
            with open(os.path.join(gdzie, nazwa_pliku), encoding="utf-8") as uchwyt:
                drzewo = ast.parse(uchwyt.read())
            for wezel in ast.walk(drzewo):
                if isinstance(wezel, ast.Assign):
                    for cel in wezel.targets:
                        if isinstance(cel, ast.Name) and ZAPADKA_NAZWA.match(cel.id):
                            out.setdefault(cel.id, (nazwa_pliku, []))
                if not isinstance(wezel, ast.Compare):
                    continue
                czlony = [wezel.left] + list(wezel.comparators)
                for i, operator in enumerate(wezel.ops):
                    nazwa_op = type(operator).__name__
                    if nazwa_op not in ODWROTNY_OPERATOR:
                        continue
                    lewy, prawy = czlony[i], czlony[i + 1]
                    for stala, druga, relacja in ((lewy, prawy, nazwa_op),
                                                  (prawy, lewy,
                                                   ODWROTNY_OPERATOR[nazwa_op])):
                        if not (isinstance(stala, ast.Name)
                                and ZAPADKA_NAZWA.match(stala.id)):
                            continue
                        wpis = out.setdefault(stala.id, (nazwa_pliku, []))
                        wpis[1].append((relacja, ast.dump(druga)))
    return out


def klasa_zapadki(nazwa, porownania):
    """Czy ruszenie tej zapadki w ZAKAZANĄ stronę cokolwiek zapala.

    Zakazana strona wynika z przedrostka: `MAX_` wolno tylko obniżać, `MIN_`
    i `MINIMUM_` tylko podnosić. Ale to jest zdanie dla człowieka — bramką jest
    dopiero porównanie, które przy takim ruchu pada.

    * **nośne** — porównanie, dla którego zapadka jest progiem (`MAX_X >= ile`);
      pada, gdy rośnie DRZEWO, a nie gdy rusza się stała;
    * **strzegące** — porównanie z drugiej strony (`MAX_X <= ile`); pada, gdy stała
      idzie w zakazaną stronę. Równość strzeże w obie.

    `przybita` znaczy: strażnik mierzy TĘ SAMĄ populację, co próg (albo jest
    równością), więc ruch o jeden pada. `czesciowa`: strażnik jest, ale o innej
    populacji — ruch o jeden przechodzi, pada dopiero ruch daleki; zmierzone na
    trzech takich zapadkach 11.09.2026, wszystkie trzy przeszły przy ruchu o jeden.
    `wolna`: strażnika nie ma i ruch w zakazaną stronę nie zapala niczego.
    """
    gorna = nazwa.startswith("MAX")
    nosne = {"GtE", "Gt"} if gorna else {"LtE", "Lt"}
    strzegace = {"LtE", "Lt"} if gorna else {"GtE", "Gt"}

    populacja = {ksztalt for relacja, ksztalt in porownania if relacja in nosne}
    straze = [(relacja, ksztalt) for relacja, ksztalt in porownania
              if relacja in strzegace or relacja in ("Eq", "NotEq")]
    if not porownania:
        return POZA_SKANEM
    if not straze:
        return WOLNA
    if any(relacja in ("Eq", "NotEq") or ksztalt in populacja
           for relacja, ksztalt in straze):
        return PRZYBITA
    return CZESCIOWA


#: **Wszystkie zapadki pod `tools/tests/`, każda z klasą i modułem.**
#: 47 zapadek: **17 przybitych, 3 częściowe, 26 WOLNE i 1 poza zasięgiem skanu.**
#:
#: **To zdanie jest przepisane, a nie dopisane obok (12.09.2026).** Stało tu
#: „Trzydzieści osiem: 13 przybitych, 3 częściowe, 21 WOLNYCH i 1 poza zasięgiem
#: skanu", zmierzone 11.09.2026 na `52752c9` — i przestało być prawdą, gdy rejestr
#: urósł o cztery pozycje. Nie zauważył tego żaden test, bo bramka niżej porównuje
#: SŁOWNIK z drzewem, a nie to zdanie ze słownikiem. Od 12.09.2026 porównuje je
#: `test_prose_counts.py`, więc liczby wyżej nie mogą się już rozjechać po cichu.
#: Suma stoi CYFRAMI, nie słownie, i to jest warunek działania tamtej bramki.
#:
#: **Lista jest z NAZWAMI, nie z samymi liczbami, i to jest wybór.** Same liczby
#: przepuściłyby zamianę jednej zapadki przybitej na inną wolną — suma stoi, a zdanie
#: o konkretnej zapadce przestaje być prawdziwe. Rozjechać się ta lista nie może, bo
#: jest porównywana z drzewem W OBIE STRONY, tak samo jak `NIEME_ASERCJE` z 6.D127.
#:
#: **Czego klasyfikator NIE widzi, i jest to zmierzone, a nie zastrzeżone na wszelki
#: wypadek.** Czyta wyłącznie węzły `Compare`, w których stała stoi PO IMIENIU.
#: `MIN_PATHS` jest słownikiem trzech progów, a do porównania trafia przez zmienną
#: pętli (`for field, floor in MIN_PATHS.items()`), więc jego nazwa w żadnym
#: porównaniu nie pada. Klasa `POZA_SKANEM` mówi dokładnie to i nic więcej — a NIE
#: mówi „nieużywana".
ZAPADKI = {
    "MAX_COMMIT_EXCEPTIONS": (PRZYBITA, "test_report_hygiene.py"),
    "MAX_DATE_EXCEPTIONS": (PRZYBITA, "test_report_hygiene.py"),
    "MAX_EXCEPTIONS": (PRZYBITA, "test_field_paths.py"),
    "MAX_GAME_JUSTIFIED_NEEDLES": (PRZYBITA, "test_game_needle_specificity.py"),
    "MAX_GAME_UNMATCHED_NEEDLES": (PRZYBITA, "test_game_needle_specificity.py"),
    "MAX_GLOB_WPROST": (WOLNA, "test_tree_walks.py"),
    "MAX_JUSTIFICATIONS": (PRZYBITA, "test_bin_path_framework.py"),
    "MAX_JUSTIFIED_NEEDLES": (PRZYBITA, "test_needle_specificity.py"),
    "MAX_ODCISKOW_W_RAPORCIE": (WOLNA, "mutation_sweep.py"),
    "MAX_REPORTS_WITHOUT_FIELD_LINE": (PRZYBITA, "test_report_hygiene.py"),
    "MAX_ROZSZERZEN_BEZ_TRAFIEN": (WOLNA, "test_report_hygiene.py"),
    "MAX_SEKWENCJI_UCIECZKI": (PRZYBITA, "test_bytecode_staleness.py"),
    "MAX_UNMATCHED_NEEDLES": (PRZYBITA, "test_needle_specificity.py"),
    "MAX_WOLNO_WPROST": (WOLNA, "test_tree_walks.py"),
    "MAX_ZAPISOW_W_DRZEWIE": (PRZYBITA, "test_tree_writes.py"),
    "MINIMUM_CALLERS": (WOLNA, "test_platform_length_in_pipeline.py"),
    "MINIMUM_CLAIMS": (WOLNA, "test_report_claims.py"),
    "MINIMUM_DEKLARACJI": (WOLNA, "test_dead_constants_csharp.py"),
    "MINIMUM_DETAIL_BLOCKS": (PRZYBITA, "test_backlog.py"),
    "MINIMUM_DOCUMENTED_ITEMS": (CZESCIOWA, "test_backlog.py"),
    # 6.D203: dolne ostrze na skan liczebników z `test_prose_counts.py` — pilnuje,
    # że przyrząd nie oślepł, bo werdykt „skanu postawić się nie da" stoi na jego
    # trafieniach. WOLNA, bo jest progiem jednostronnym, a nie porównaniem z drzewem.
    # 6.D207: podloga na skan zdan deklarujacych pomiar w docstringach. WOLNA, bo jest
    # progiem jednostronnym: deklaracji przybywa z kazda pozycja, ktora cos zmierzy.
    # Werdykt 6.D207 („odsiac sie NIE DA") nie stoi zreszta na niej, tylko na ZBIORZE
    # `DEKLARACJE_BEZ_ASERCJI`, porownywanym z drzewem w obie strony.
    "MIN_DEKLARACJI_POMIARU": (WOLNA, "test_prose_counts.py"),
    "MINIMUM_LICZB_SLOWNYCH": (WOLNA, "test_prose_counts.py"),
    "MINIMUM_METOD": (WOLNA, "test_csharp_assertions.py"),
    "MINIMUM_MIEJSC": (WOLNA, "test_runner_number_parsing.py"),
    "MINIMUM_MODES": (WOLNA, "test_run_mode_claims.py"),
    "MINIMUM_POWODU": (CZESCIOWA, "test_field_paths.py"),
    "MINIMUM_READY_ITEMS": (PRZYBITA, "test_backlog.py"),
    "MINIMUM_SUPPORTED_MAJOR": (CZESCIOWA, "test_dotnet_version.py"),
    "MINIMUM_WIDZIANYCH": (WOLNA, "test_csharp_test_methods.py"),
    "MINIMUM_WYSTAPIEN": (WOLNA, "test_expected_exception.py"),
    "MINIMUM_WYSTAPIEN_ROWNOSCI": (WOLNA, "test_runner_options.py"),
    "MIN_FILES_WITH_PATHS": (PRZYBITA, "test_bin_path_framework.py"),
    "MIN_GAME_MESSAGES": (WOLNA, "test_game_needle_specificity.py"),
    "MIN_GAME_NEEDLES": (PRZYBITA, "test_game_needle_specificity.py"),
    "MIN_GAME_SOURCES": (WOLNA, "test_game_needle_specificity.py"),
    "MIN_GOLYCH_W_DOKUMENTACH": (WOLNA, "test_field_paths.py"),
    "MIN_GOLYCH_W_POLACH": (WOLNA, "test_field_paths.py"),
    "MIN_MESSAGES": (WOLNA, "test_needle_specificity.py"),
    "MIN_BLOKOW_WYKONANYCH": (WOLNA, "test_field_paths.py"),
    "MINIMUM_MODULOW_SKANOWANYCH": (WOLNA, "test_bytecode_staleness.py"),
    "MIN_MODULE_NAMES": (WOLNA, "test_field_paths.py"),
    "MIN_WYWOLAN_W_WYKONANYCH": (WOLNA, "test_field_paths.py"),
    "MIN_NEEDLES": (WOLNA, "test_needle_specificity.py"),
    "MIN_PATHS": (POZA_SKANEM, "test_field_paths.py"),
    "MIN_PATHS_IN_TREE": (PRZYBITA, "test_bin_path_framework.py"),
    "MIN_REPORTS": (PRZYBITA, "test_report_hygiene.py"),
    "MIN_WPISOW_RUNNERA": (WOLNA, "test_suite_runtime_budget.py"),
}

#: Ile zapadek razem. Liczba jest POCHODNA ze słownika wyżej i stoi osobno po to,
#: żeby komunikat podał ją, zanim ktoś zacznie czytać trzydzieści osiem wierszy.
#:
#: **Osobnej zapadki na LICZBĘ WOLNYCH tu nie ma i to jest wynik pomiaru, nie
#: przeoczenie.** Napisałem ją najpierw — `test_wolnych_zapadek_moze_tylko_UBYWAC`,
#: z oboma kierunkami — po czym kontrole pokazały, że nie zapala się nigdy sama:
#: KN-1 (nowa wolna zapadka w drzewie) zapaliła RAZEM z testem listy, KN-5c
#: (wolnej zapadce przybywa strażnik) zapaliła SAM test listy, a KN-5 (zdjęcie
#: połowy o przybyciu strażnika) wyszła ZIELONA. Lista z nazwami jest ściśle
#: mocniejsza od liczby, więc liczba zostaje jako wiersz w komunikacie, a nie
#: jako druga bramka mówiąca to samo słabiej.
ZAPADEK_RAZEM = len(ZAPADKI)


def zapadki_w_drzewie(katalog=None, root=None):
    """`{nazwa: klasa}` dla każdej stałej o kształcie zapadki pod `tools/tests/`."""
    return {nazwa: klasa_zapadki(nazwa, porownania)
            for nazwa, (_modul, porownania) in _porownania_zapadek(katalog, root).items()}


#: Pliki, w których `glob.glob(…, recursive=True)` wolno zawołać WPROST, z powodem.
#: To jest TRZECI kształt przejścia po drzewie (6.D117): 6.D74 zamknęło `os.walk`
#: w `tree_walk.walk`, 6.D97 zdjęło kopie listy katalogów — a rekurencyjny `glob`
#: przechodził bokiem przez oba.
#:
#: **Zmierzone 11.09.2026 na `3fa2bec`: takich wywołań było TRZY**, każde z własną
#: regułą odsiania — `.godot` w `test_game_needle_specificity`, `obj`/`bin`
#: w `test_xml_doc_blocks` i w `test_sim_untested_members`, po jednej kopii na
#: miejsce. Dwa zostały przepisane na `TW.znajdz`, z wynikiem IDENTYCZNYM co do pliku
#: (22, 75 i 53 pliki przed i po). Zostało jedno i ma powód.
GLOB_WPROST = {
    "tools/tests/test_sim_untested_members.py":
        "`_all_sim_cs_files` ma z definicji widzieć `obj/` i `bin/` — jest pomiarem "
        "stanu PRZED dla bramki, która pokazuje, ile plików odsiewa; przepisanie go "
        "na odsianie zabrałoby jej punkt odniesienia, a pole o zakresie 6.D117 "
        "wyklucza zmianę zachowania tej funkcji.",
}

#: Zapadka na słownik wyżej. Wolno ją tylko OBNIŻAĆ — ta sama reguła, co przy
#: `MAX_WOLNO_WPROST`: wyjątek jest tańszy niż przepisanie wołania.
MAX_GLOB_WPROST = 1

#: Drzewa przeszukiwane w poszukiwaniu wywołań.
DRZEWA = ("tools",)


def _pliki_python():
    for drzewo in DRZEWA:
        for katalog, _pod, pliki in TW.walk(os.path.join(ROOT, drzewo)):
            for plik in sorted(pliki):
                if plik.endswith(".py"):
                    yield os.path.relpath(os.path.join(katalog, plik), ROOT)


def wywolania_os_walk():
    """`(plik, wiersz)` każdego wołania `os.walk` — z drzewa składni, nie z grepa.

    Grep po napisie `os.walk(` łapie też docstringi i komentarze, a w tym projekcie
    stoi tam pół tuzina zdań O `os.walk` — czyli miejsca, w których przejście jest
    OPISANE, a nie wykonane.
    """
    found = []
    for relative in _pliki_python():
        try:
            drzewo = ast.parse(open(os.path.join(ROOT, relative), encoding="utf-8").read())
        except (OSError, SyntaxError):
            continue
        for node in ast.walk(drzewo):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "walk"
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "os"):
                found.append((relative.replace(os.sep, "/"), node.lineno))
    return sorted(found)


def wywolania_odsiane():
    """To samo dla `TW.walk` — żeby cisza wyżej znaczyła „idzie przez odsianie",
    a nie „przejść nie ma wcale"."""
    found = []
    for relative in _pliki_python():
        try:
            drzewo = ast.parse(open(os.path.join(ROOT, relative), encoding="utf-8").read())
        except (OSError, SyntaxError):
            continue
        for node in ast.walk(drzewo):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "walk"
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "TW"):
                found.append((relative.replace(os.sep, "/"), node.lineno))
    return sorted(found)


def _drzewo_probne(baza, pominiety):
    """Dwa pliki: jeden w gałęzi widzianej, drugi w gałęzi `pominiety`."""
    os.makedirs(os.path.join(baza, "widoczne"), exist_ok=True)
    os.makedirs(os.path.join(baza, pominiety, "kopia"), exist_ok=True)
    with open(os.path.join(baza, "widoczne", "a.py"), "w", encoding="utf-8") as u:
        u.write("STALA_WIDZIANA = 1\n")
    with open(os.path.join(baza, pominiety, "kopia", "a.py"), "w", encoding="utf-8") as u:
        u.write("STALA_Z_KOPII = 1\n")


# --------------------------------------------------------------------------- testy


def wywolania_globa_rekurencyjnego():
    """`[(plik, wiersz)]` — wywołania `glob`/`iglob` z argumentem `recursive`.

    Rozpoznanie idzie po ARGUMENCIE, a nie po nazwie modułu: `glob.glob(x)` bez
    `recursive` schodzi o jeden poziom i przejściem po drzewie nie jest. Wartość
    argumentu nie jest tu czytana — `recursive=False` też ma być wołane przez
    `TW.znajdz`, jeśli ktoś je kiedyś wpisze, bo o kształcie mówi obecność opcji.
    """
    znalezione = []
    for drzewo in DRZEWA:
        for sciezka in TW.znajdz(os.path.join(ROOT, drzewo), "*.py"):
            with open(sciezka, encoding="utf-8") as uchwyt:
                drzewo_skladni = ast.parse(uchwyt.read())
            wzgledna = os.path.relpath(sciezka, ROOT).replace(os.sep, "/")
            for wezel in ast.walk(drzewo_skladni):
                if not isinstance(wezel, ast.Call):
                    continue
                if isinstance(wezel.func, ast.Attribute):
                    nazwa = wezel.func.attr
                elif isinstance(wezel.func, ast.Name):
                    nazwa = wezel.func.id
                else:
                    continue
                if nazwa in ("glob", "iglob") and any(
                        slowo.arg == "recursive" for slowo in wezel.keywords):
                    znalezione.append((wzgledna, wezel.lineno))
    return sorted(znalezione)


def test_zaden_rekurencyjny_glob_nie_omija_wspolnego_odsiania():
    """Trzeci kształt przejścia po drzewie — 6.D117.

    Bramka jest na WOŁANIU, tak samo jak przy `os.walk` i z tego samego powodu:
    wynik zależy od tego, co akurat leży na dysku. `src/Game/obj/` dziś nie istnieje,
    więc dawna reguła z jedną pozycją (`.godot`) dawała ten sam wynik co odsianie —
    cisza, której warunkiem jest stan katalogu, nie jest bramką.
    """
    zle = [(p, w) for p, w in wywolania_globa_rekurencyjnego() if p not in GLOB_WPROST]
    assert zle == [], (
        "rekurencyjny `glob` z pominięciem odsiania z `.gitignore`: %s "
        "— użyj `tree_walk.znajdz`" % zle)


def test_lista_globow_wprost_nie_gnije():
    """Wpis bez wołania jest zdaniem o repozytorium, które przestało być prawdziwe."""
    assert len(GLOB_WPROST) <= MAX_GLOB_WPROST, sorted(GLOB_WPROST)
    wprost = {p for p, _w in wywolania_globa_rekurencyjnego()}
    for plik, powod in sorted(GLOB_WPROST.items()):
        assert plik in wprost, (
            "wyjątek na `%s` nie dotyczy już żadnego wołania — zdejmij go" % plik)
        assert len(powod) >= 40, plik


def test_skan_globow_widzi_ksztalt_ktory_ma_widziec():
    """Kontrola PRZYRZĄDU: pusta lista wyżej byłaby zielona także przy skanie ślepym.

    Dwie strony na wejściu syntetycznym, bo tylko razem coś znaczą: wywołanie
    z `recursive` ma być widziane, a `glob.glob(x)` bez tego argumentu — nie, bo
    schodzi o jeden poziom i przejściem po drzewie nie jest.
    """
    znalezione = wywolania_globa_rekurencyjnego()
    assert znalezione, (
        "skan nie widzi ANI JEDNEGO rekurencyjnego globa — a co najmniej jeden stoi "
        "w `GLOB_WPROST`, więc albo wzorzec się rozjechał, albo wołanie zniknęło")

    def policz(zrodlo):
        drzewo = ast.parse(zrodlo)
        return sum(1 for w in ast.walk(drzewo)
                   if isinstance(w, ast.Call)
                   and isinstance(w.func, ast.Attribute)
                   and w.func.attr in ("glob", "iglob")
                   and any(s.arg == "recursive" for s in w.keywords))

    assert policz("import glob\nglob.glob('a/**/b', recursive=True)\n") == 1
    assert policz("import glob\nglob.glob('a/*.py')\n") == 0, (
        "skan bierze zwykłego globa za przejście po drzewie")


def test_no_tool_walks_the_tree_without_the_shared_filter():
    """Każde `os.walk` w `tools/` idzie przez odsianie — poza samym odsianiem.

    Bramka jest na WOŁANIU, a nie na wyniku, bo wynik zależy od tego, co akurat leży
    na dysku: przejście bez odsiania jest dziś ciche wyłącznie dlatego, że nikt nie
    położył kopii pod `tools/`. Cisza, której warunkiem jest stan katalogu, nie jest
    bramką.
    """
    zle = [(p, w) for p, w in wywolania_os_walk() if p not in WOLNO_WPROST]
    assert zle == [], (
        "przejście po drzewie z pominięciem odsiania z `.gitignore`: %s "
        "— użyj `tree_walk.walk`" % zle)


def test_the_direct_call_list_stays_closed_and_every_entry_is_still_used():
    """Dwa wyjątki, z powodem, i każdy MUSI mieć w swoim pliku wołanie, którego dotyczy.

    Wpis bez wołania jest zdaniem o repozytorium, które przestało być prawdziwe —
    ta sama choroba, co martwa stała z 6.B29. Powód krótszy niż 40 znaków też nie
    przechodzi: „bo tak" jest wpisem, nie uzasadnieniem.
    """
    assert len(WOLNO_WPROST) <= MAX_WOLNO_WPROST, sorted(WOLNO_WPROST)
    wprost = {p for p, _w in wywolania_os_walk()}
    for plik, powod in sorted(WOLNO_WPROST.items()):
        assert plik in wprost, (
            "wyjątek na `%s` nie dotyczy już żadnego wołania — zdejmij go" % plik)
        assert len(powod) >= 40, plik


def test_the_gate_is_looking_at_a_tree_that_still_has_walks_in_it():
    """Kontrola przyrządu: pusta lista wyżej byłaby zielona także przy zepsutym skanie.

    Liczba jest PODŁOGĄ, nie zapadką: wołań może przybyć i to jest normalne. Zejście
    poniżej znaczy, że skan przestał widzieć pliki, a nie że przejść ubyło — tego
    pilnuje osobno lista plików niżej.
    """
    odsiane = wywolania_odsiane()
    assert len(odsiane) >= 14, (
        "skan widzi %d wołań `TW.walk` — wzorzec albo lista plików się rozjechały: %s"
        % (len(odsiane), odsiane))
    pliki = {p for p, _w in odsiane}
    assert "tools/track/data_freshness.py" in pliki, (
        "skan nie widzi `tools/track/`, czyli chodzi po węższym drzewie niż `tools`")
    assert len([p for p in pliki if p.startswith("tools/tests/")]) >= 11, sorted(pliki)


def test_the_ignored_directory_list_is_read_from_gitignore_not_copied():
    """Lista bierze się z `.gitignore`, więc nowy wpis działa bez ruszania kodu."""
    nazwy, sciezki = TW.wzorce_katalogow(
        "# komentarz\n"
        "build/\n"
        "data/gtfs/\n"
        "/tylko-w-korzeniu/\n"
        "*.pyc\n"
        "!nie-pomijaj/\n"
        "plik.txt\n")
    assert nazwy == {"build"}, nazwy
    assert sciezki == {"data/gtfs", "tylko-w-korzeniu"}, sciezki
    # Wpisy plikowe i zaprzeczenia NIE wchodzą: przycięcie gałęzi na `*.pyc` odcięłoby
    # katalog o takiej nazwie, a na `!` — wręcz odwróciłoby znaczenie wpisu.
    assert "*.pyc" not in nazwy and "plik.txt" not in nazwy
    assert "nie-pomijaj" not in nazwy and "nie-pomijaj" not in sciezki


def test_the_real_gitignore_has_no_directory_pattern_with_a_star():
    """Gwiazdki w nazwie katalogu ten moduł NIE zna — i mówi to, zamiast milczeć.

    Wpis w rodzaju `tmp-*/` przeszedłby dziś przez `wzorce_katalogow` jako nazwa
    dosłowna i nie odciąłby niczego. Bramka pilnuje, żeby taki wpis był widoczny
    w tym samym commicie, w którym powstaje.
    """
    nazwy, sciezki = TW.pominiete()
    z_gwiazdka = [w for w in nazwy | sciezki if "*" in w or "?" in w or "[" in w]
    assert z_gwiazdka == [], (
        "`.gitignore` ma katalogowy wzorzec z maską: %s — `tree_walk.wzorce_katalogow` "
        "traktuje go dosłownie i niczego nie odetnie" % z_gwiazdka)


def test_the_filter_skips_a_branch_that_os_walk_enters():
    """Pomiar różnicy na drzewie probnym: `os.walk` wchodzi, `TW.walk` nie.

    Bez tej pary „bramka przeszła" znaczyłoby tylko tyle, że nazwy funkcji się
    zgadzają — a nie że odsianie cokolwiek odsiewa.
    """
    import tempfile
    with tempfile.TemporaryDirectory() as baza:
        _drzewo_probne(baza, "build")
        with open(os.path.join(baza, ".gitignore"), "w", encoding="utf-8") as u:
            u.write("build/\n")
        goly = sorted(n for _b, _d, pliki in os.walk(baza) for n in pliki)
        odsiany = sorted(n for _b, _d, pliki in TW.walk(baza, baza) for n in pliki)
        assert goly == [".gitignore", "a.py", "a.py"], goly
        assert odsiany == [".gitignore", "a.py"], odsiany


def test_a_copy_under_an_ignored_directory_does_not_move_the_dead_constant_scan():
    """Zmierzony przypadek 6.D74 odtworzony na drzewie probnym.

    Pomiar z drzewa projektu (`tools/build/kopia/`, `definicje` **917 → 1511**) jest
    zapisany w raporcie, a nie tutaj: kopia 12 MB w zestawie testów kosztuje sekundy
    i zostawia pliki w drzewie projektu (nauczka z 6.D62, gdzie atrapa sieci zostawiła
    dwa kafle w prawdziwej pamięci). Tutaj stoi ten sam kształt na drzewie w `/tmp`.
    """
    import tempfile
    import test_dead_constants as DC
    with tempfile.TemporaryDirectory() as baza:
        for drzewo in DC.DRZEWA:
            os.makedirs(os.path.join(baza, drzewo), exist_ok=True)
        with open(os.path.join(baza, ".gitignore"), "w", encoding="utf-8") as u:
            u.write("build/\n")
        with open(os.path.join(baza, "tools", "a.py"), "w", encoding="utf-8") as u:
            u.write("STALA_WIDZIANA = 1\n")
        przed = len(DC.definicje(baza))
        os.makedirs(os.path.join(baza, "tools", "build", "kopia"))
        with open(os.path.join(baza, "tools", "build", "kopia", "a.py"),
                  "w", encoding="utf-8") as u:
            u.write("STALA_Z_KOPII = 1\n")
        po = len(DC.definicje(baza))
    assert (przed, po) == (1, 1), (
        "kopia pod katalogiem pominiętym w `.gitignore` zmieniła liczbę skanu: "
        "%d -> %d" % (przed, po))


# 6.D25: uruchomienie tego pliku WPROST idzie tą samą drogą, co cały zestaw —
# z licznikiem asercji i z odmową przy zerze testów.


# --- 6.D97: własna lista katalogów obok wspólnego odsiania ------------------------
#
# Po 6.D74 czternaście przejść poszło przez `TW.walk`, ale w drzewie zostały cztery
# filtry robiące to samo drugi raz. Trzy z nich były DRUGĄ, uboższą kopią listy
# z `.gitignore`: `BUILD_DIRS = {"bin", "obj"}` (`test_readme_claims.py`),
# `"__pycache__" in katalog` (`test_dead_constants.py`) i `os.sep + "obj" in katalog
# or os.sep + "bin" in katalog` (`test_dead_constants_csharp.py`). Dopóki stały obok
# wspólnego odsiania, czytający nie wiedział, która lista rozstrzyga — a przy
# następnym wpisie w `.gitignore` rozjechałyby się po cichu.
#
# Czwarty (`os.sep + "tests" in base` w `mutation_sweep.py`) NIE jest kopią i został:
# tego katalogu `.gitignore` nie zna i znać nie powinien, bo jest śledzony. Odsiewa
# go reguła NARZĘDZIA („mutujemy kod pod testem, nigdy testów"), nie reguła
# repozytorium — i różnica między tymi dwiema regułami jest treścią tej bramki.

#: JAWNE, ZAMKNIĘTE wyjątki: `(plik, nazwa katalogu, powód)` dla filtrów, które
#: odsiewają katalog Z WŁASNEGO powodu, nie dlatego, że stoi w `.gitignore`.
#: Pusto, i to jest wynik pomiaru: jedyny taki filtr w drzewie odsiewa `tests`,
#: a `tests` w `.gitignore` NIE STOI, więc bramka go nie widzi i nie musi.
FILTRY_Z_WLASNEGO_POWODU = {
    ("tools/tests/test_sim_untested_members.py", "obj"): (
        '`_is_generated` NIE odsiewa katalogu z przejścia — klasyfikuje ścieżki '
        'z `glob.glob`, żeby moduł mógł policzyć stan PRZED (z plikami generowanymi) '
        'i PO (bez nich). Zdjęcie tego filtru zabrałoby pomiar, nie duplikat'),
    ("tools/tests/test_sim_untested_members.py", "bin"): (
        "druga połowa tego samego warunku, ten sam powód"),
    ("tools/tests/tree_walk.py", "__pycache__"): (
        "`wyczysc_bajtkod` (6.D122) nie POMIJA tego katalogu — ona go SZUKA. Jest to "
        "jedyne narzędzie w drzewie, którego przedmiotem jest katalog pominięty "
        "w `.gitignore`, więc odsianie przez `walk` zabrałoby mu wszystko, co ma "
        "znaleźć. Kopią listy z `.gitignore` ten filtr nie jest z definicji: nie "
        "wybiera, gdzie NIE wchodzić, tylko co skasować"),
}


def filtry_katalogow_z_gitignore():
    """`[(plik, wiersz, nazwa)]` — miejsca odsiewające katalog, który jest w `.gitignore`.

    Szukane w drzewie składni, w plikach, które w ogóle chodzą po drzewie: literał
    napisowy równy nazwie katalogu z `.gitignore`, użyty w warunku albo w zbiorze.
    Grep po nazwie łapałby też komentarze i docstringi — a w tym module stoi ich
    kilkanaście, bo cała ta sekcja jest O tych nazwach.
    """
    nazwy, _sciezki = TW.pominiete()
    chodzace = {plik for plik, _wiersz in wywolania_odsiane() + wywolania_os_walk()}
    znalezione = []
    for relative in sorted(chodzace):
        try:
            zrodlo = open(os.path.join(ROOT, relative), encoding="utf-8").read()
            drzewo = ast.parse(zrodlo)
        except (OSError, SyntaxError):
            continue
        # Wnętrza funkcji `test_*` są POMIJANE i to jest poprawka z pomiaru: pierwsza
        # wersja skanu zgłosiła `build` z wejścia syntetycznego w
        # `test_the_ignored_directory_list_is_read_from_gitignore_not_copied` — czyli
        # napis, który jest DANYMI testu parsera, a nie filtrem. Filtry mieszkają
        # w pomocnikach i na poziomie modułu, fixture w testach.
        wnetrza = set()
        for funkcja in ast.walk(drzewo):
            if (isinstance(funkcja, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and funkcja.name.startswith("test_")):
                for pod in ast.walk(funkcja):
                    wnetrza.add(id(pod))
        for node in ast.walk(drzewo):
            if not isinstance(node, (ast.If, ast.Set, ast.ListComp, ast.Compare)):
                continue
            for pod in ast.walk(node):
                if id(pod) in wnetrza:
                    continue
                if (isinstance(pod, ast.Constant) and isinstance(pod.value, str)
                        and pod.value in nazwy):
                    znalezione.append((relative, pod.lineno, pod.value))
    return sorted(set(znalezione))


def test_zaden_skan_nie_trzyma_wlasnej_kopii_listy_z_gitignore():
    """Druga lista tych samych katalogów rozjeżdża się przy pierwszym nowym wpisie."""
    znalezione = [w for w in filtry_katalogow_z_gitignore()
                  if (w[0], w[2]) not in FILTRY_Z_WLASNEGO_POWODU]
    assert not znalezione, (
        "skan chodzący po drzewie odsiewa katalog, który JUŻ odsiewa `TW.walk` "
        "z `.gitignore` — dwie listy tej samej rzeczy rozjadą się przy następnym "
        f"wpisie: {znalezione}")


def test_lista_wyjatkow_filtrow_nie_gnije():
    """Wyjątek bez pokrycia w drzewie ma zniknąć z listy.

    Asercja o PUSTOŚCI stoi tu, bo pusta pętla nie wykonuje żadnej i test byłby
    cichym pominięciem. Dziś lista jest pusta i to jest zmierzony stan.
    """
    obecne = {(w[0], w[2]) for w in filtry_katalogow_z_gitignore()}
    if not FILTRY_Z_WLASNEGO_POWODU:
        assert obecne == set(), sorted(obecne)
        return
    for klucz, powod in sorted(FILTRY_Z_WLASNEGO_POWODU.items()):
        assert klucz in obecne, f"{klucz} nie ma już filtru — zdejmij wpis ({powod})"


def test_skan_filtrow_widzi_ksztalt_ktory_ma_widziec():
    """Kontrola PRZYRZĄDU: cisza ma znaczyć „czysto", a nie „skan ślepy".

    Bramka wyżej jest dziś zielona, więc bez tego testu nie dałoby się odróżnić
    drzewa bez kopii od skanu, który przestał czegokolwiek szukać. Sprawdzane jest
    to, na czym skan stoi: że nazwy katalogów bierze z `.gitignore` (a nie z listy
    wpisanej tutaj) i że `tests` — jedyny filtr, który został — do tego zbioru
    NIE należy, więc jego obecność w drzewie bramki nie zapala.
    """
    nazwy, _sciezki = TW.pominiete()
    for oczekiwana in ("bin", "obj", "__pycache__", "build", "renders", ".venv"):
        assert oczekiwana in nazwy, (
            f"{oczekiwana!r} zniknęło z listy katalogów czytanej z `.gitignore` — "
            "bramka wyżej przestała widzieć kopię akurat tego katalogu")
    assert "tests" not in nazwy, (
        "`tests` trafiło do listy z `.gitignore`; filtr w `mutation_sweep.py` "
        "zapaliłby wtedy bramkę, choć odsiewa katalog z własnego powodu")
    assert len(nazwy) >= 10, (
        f"lista z `.gitignore` skurczyła się do {len(nazwy)} nazw — skan miałby "
        "wtedy czego nie szukać")

def test_kazda_zapadka_ma_klase_i_klasa_zgadza_sie_z_drzewem():
    """Zapadka na zapadki — porównanie W OBIE STRONY, bo inaczej byłaby wolna.

    Ironia byłaby tu kosztowna: bramka pilnująca, czy zapadki da się ruszyć po cichu,
    napisana jako `len(w_drzewie) <= ZAPADEK_RAZEM`, dałaby się ruszyć po cichu.
    """
    w_drzewie = zapadki_w_drzewie()

    nowe = {n: k for n, k in w_drzewie.items() if n not in ZAPADKI}
    assert nowe == {}, (
        "zapadka spoza listy: %s — dopisz ją razem z klasą w tym samym commicie, "
        "w którym ją wprowadzasz" % sorted(nowe.items()))

    znikniete = sorted(n for n in ZAPADKI if n not in w_drzewie)
    assert znikniete == [], (
        "wpis na liście dla zapadki, której w drzewie nie ma: %s — zdejmij wpis "
        "w tym samym commicie" % znikniete)

    inna_klasa = [(n, ZAPADKI[n][0], k) for n, k in sorted(w_drzewie.items())
                  if k != ZAPADKI[n][0]]
    assert inna_klasa == [], (
        "zapadka zmieniła klasę (nazwa, było, jest): %s — zmiana W STRONĘ `wolna` "
        "znaczy, że komuś ubył strażnik; w stronę `przybita`, że doszedł i wpis "
        "trzeba poprawić" % inna_klasa)

    assert len(w_drzewie) == ZAPADEK_RAZEM == 47, (
        "zapadek w drzewie %d, na liście %d, pomiar z 11.09.2026 mówił 38, "
        "po 6.D146 — 40, po 6.D147 — 42 (doszła zapadka na sekwencje ucieczki "
        "i próg KW jej skanu), po 6.D187 — 44 (dwa progi KW skanu gołych nazw), "
        "po 6.D190 — 45 (podłoga na liczbę wpisów runnera), po 6.D203 — 46 "
        "(dolne ostrze na skan liczebników), a po 6.D207 — 47 (podłoga na skan zdań "
        "deklarujących pomiar w docstringach)"
        % (len(w_drzewie), ZAPADEK_RAZEM))

    # Liczby zbiorcze. **Nie jest to ozdobnik komunikatu i pokazała to KN-7.**
    # Asercje wyżej pilnują, żeby lista zgadzała się z DRZEWEM — a te cztery liczby
    # są zdaniem o samej liście, publikowanym w jej komentarzu i w raporcie. Gdy ktoś
    # przybije wolną zapadkę i UCZCIWIE poprawi jej wpis, wszystko wyżej przechodzi,
    # a „21 wolnych" staje się nieprawdą, której nie zgłasza nic. KN-7 wykonała
    # dokładnie ten scenariusz: jedyną czerwienią była ta asercja.
    ile = collections.Counter(w_drzewie.values())
    assert (ile[PRZYBITA], ile[CZESCIOWA], ile[WOLNA], ile[POZA_SKANEM]) == (17, 3, 26, 1), (
        "klasy zapadek: przybitych %d, częściowych %d, WOLNYCH %d, poza skanem %d — "
        "pomiar z 11.09.2026 mówił 13/3/21/1, po 6.D146 — 13/3/23/1, a po 6.D147 — "
        "14/3/24/1, po 6.D151 — 15/3/23/1, po 6.D167 — 17/3/21/1, po 6.D187 — "
        "17/3/23/1, po 6.D190 — 17/3/24/1, po 6.D203 — 17/3/25/1, a po 6.D207 — "
        "17/3/26/1; wolne to te, "
        "które da się ruszyć "
        "w zakazaną stronę bez zapalenia czegokolwiek: %s"
        % (ile[PRZYBITA], ile[CZESCIOWA], ile[WOLNA], ile[POZA_SKANEM],
           sorted(n for n, k in w_drzewie.items() if k == WOLNA)))


def test_klasyfikator_rozroznia_trzy_ksztalty_na_drzewie_probnym():
    """Kontrola przyrządu: trzy zapadki o znanych kształtach, jeden przebieg skanu.

    Skan idzie przez `zapadki_w_drzewie`, a nie przez ręcznie złożoną listę porównań —
    inaczej mierzyłby moje wyobrażenie o czytniku zamiast czytnika (lekcja z 6.D131,
    gdzie test maski składał maskę sam i nie pilnował `piny()` wcale).
    """
    with tempfile.TemporaryDirectory(prefix="metro-zapadki-") as katalog:
        with open(os.path.join(katalog, "test_probne.py"), "w",
                  encoding="utf-8") as uchwyt:
            uchwyt.write(
                "MAX_WOLNA = 3\n"
                "MAX_PRZYBITA = 3\n"
                "MAX_CZESCIOWA = 3\n"
                "MIN_WOLNA = 3\n"
                "def t():\n"
                "    assert len(lista) <= MAX_WOLNA\n"
                "    assert len(lista) <= MAX_PRZYBITA\n"
                "    assert MAX_PRZYBITA <= len(lista)\n"
                "    assert len(lista) <= MAX_CZESCIOWA\n"
                "    assert MAX_CZESCIOWA <= len(wszystkie)\n"
                "    assert len(inna) >= MIN_WOLNA\n")
        klasy = zapadki_w_drzewie(katalog, katalog)

    assert klasy == {"MAX_WOLNA": WOLNA, "MAX_PRZYBITA": PRZYBITA,
                     "MAX_CZESCIOWA": CZESCIOWA, "MIN_WOLNA": WOLNA}, (
        "klasyfikator na drzewie probnym dał %s" % sorted(klasy.items()))


def test_strona_zapisu_porownania_nie_zmienia_klasy():
    """`len(x) <= MAX_Y` i `MAX_Y >= len(x)` to jedno zdanie, więc jedna klasa.

    Bez tabeli `ODWROTNY_OPERATOR` klasyfikacja zależałaby od tego, po której stronie
    ktoś stałą napisał — a to jest nawyk pisania, nie właściwość bramki.
    """
    with tempfile.TemporaryDirectory(prefix="metro-zapadki-") as katalog:
        with open(os.path.join(katalog, "test_probne.py"), "w",
                  encoding="utf-8") as uchwyt:
            uchwyt.write(
                "MAX_LEWA = 3\n"
                "MAX_PRAWA = 3\n"
                "def t():\n"
                "    assert MAX_LEWA >= len(lista)\n"
                "    assert len(lista) <= MAX_PRAWA\n")
        klasy = zapadki_w_drzewie(katalog, katalog)

    assert klasy == {"MAX_LEWA": WOLNA, "MAX_PRAWA": WOLNA}, (
        "ta sama zapadka zapisana z dwóch stron dostała różne klasy: %s"
        % sorted(klasy.items()))


def test_klasa_POZA_SKANEM_mowi_o_granicy_przyrzadu_a_nie_o_zapadce():
    """Próg trafiający do porównania przez zmienną jest dla skanu niewidzialny.

    Jedyny taki dziś w drzewie to `MIN_PATHS` — słownik trzech progów, porównywany
    przez zmienną pętli. Zdanie „skan go nie widzi" jest tu WYNIKIEM, a nie
    zastrzeżeniem na wszelki wypadek, i ma własny kształt klasy, żeby nikt nie
    przeczytał go jako „nieużywany".
    """
    poza = sorted(n for n, (k, _m) in ZAPADKI.items() if k == POZA_SKANEM)
    assert poza == ["MIN_PATHS"], poza
    assert zapadki_w_drzewie()["MIN_PATHS"] == POZA_SKANEM, (
        "MIN_PATHS przestał być poza skanem — sprawdź, czy porównanie nie przestało "
        "iść przez zmienną, i przenieś go do właściwej klasy")

    zrodlo = open(os.path.join(ROOT, "tools", "tests", "test_field_paths.py"),
                  encoding="utf-8").read()
    assert "for field, floor in MIN_PATHS.items()" in zrodlo, (
        "kształt, na którym stoi klasa POZA_SKANEM, zniknął z `test_field_paths.py` "
        "— klasa opisuje wtedy stan, którego nie ma")


if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))
