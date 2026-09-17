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

#: Operator ZAPRZECZONY — i to jest INNA tabela niż ta wyżej, mimo podobieństwa.
#: Tamta zamienia STRONY (`PRÓG >= x` na `x <= PRÓG`), ta zaprzecza CAŁEMU zdaniu
#: (`not (x >= PRÓG)` na `x < PRÓG`). Pomylenie ich daje klasyfikator, który czyta
#: `if x < PRÓG: raise` jako strażnika mierzącego odwrotnie, zamiast jako tę samą
#: asercję napisaną inaczej — czyli dokładnie usterkę 6.D258.
ZAPRZECZONY_OPERATOR = {"Lt": "GtE", "GtE": "Lt", "Gt": "LtE", "LtE": "Gt",
                        "Eq": "NotEq", "NotEq": "Eq"}

#: Trzy klasy i czwarta, która mówi o granicy przyrządu, a nie o zapadce.
PRZYBITA = "przybita"
CZESCIOWA = "czesciowa"
WOLNA = "wolna"
POZA_SKANEM = "poza skanem"


#: **6.D258: która postać zdania COKOLWIEK twierdzi, a która tylko wygląda.**
#: Do 17.09.2026 `_porownania_zapadek` czytał każde `ast.Compare` z nazwą zapadki
#: tak, jak stoi napisane — a to jest czytanie PISOWNI, nie treści. `assert x >= PRÓG`
#: i `if x < PRÓG: raise AssertionError(...)` są tym samym zdaniem, różnią się
#: wyłącznie zapisem, a klasyfikator przestawiał przez to klasę z `wolna` na
#: `czesciowa` i wypisywał „doszedł strażnik". Żaden strażnik nie dochodził.
#: Zmierzone 6.D254 (KN-1), pełne wyjście: `reports/6d254-klasa-zapadki-a-zachowanie.md` §5.
BEZ_TWIERDZENIA = "bez twierdzenia"


def _wyjatki_bloku(ciala):
    """Czy ten blok zdań podnosi wyjątek — wprost albo przez `assert False`."""
    for zdanie in ciala:
        for pod in ast.walk(zdanie):
            if isinstance(pod, ast.Raise):
                return True
    return False


def polaryzacja_porownania(wezel, rodzic):
    """Czy to porównanie coś TWIERDZI, a jeśli tak — czy wprost, czy przez zaprzeczenie.

    Zwraca ``+1`` (zdanie twierdzi to, co stoi napisane), ``-1`` (zdanie twierdzi
    ZAPRZECZENIE tego, co stoi napisane) albo ``None`` (nie twierdzi nic).

    Trzy postacie twierdzą, i każda jest w drzewie zmierzona:

    * ``assert <cmp>`` — ``+1``; 134 porównania z nazwą zapadki, czyli prawie całość;
    * ``assert not <cmp>`` — ``-1``; jedno porównanie;
    * ``if <cmp>: ... raise ...`` — ``-1``, bo warunek gałęzi opisuje wtedy PORAŻKĘ,
      a twierdzeniem jest jego zaprzeczenie. W drzewie z 17.09.2026 takiego zdania
      NIE MA ANI JEDNEGO — ta gałąź istnieje po to, żeby przepisanie asercji na tę
      postać nie ruszało klasy, a nie dlatego, że coś tak dziś stoi.

    Nie twierdzą nic — i to jest druga połowa treści tej funkcji:

    * ``if <cmp>:`` bez ``raise`` w ciele — gałąź redakcyjna albo wybór MIĘDZY
      asercjami; dwa porównania (`mutation_sweep.py:1427` wybiera szerokość tabeli,
      `test_backlog.py:1090` wybiera, KTÓRĄ asercję puścić);
    * filtr wyrażenia listowego — jedno (`test_field_paths.py:1533`).

    **Dlaczego „nie twierdzi nic", skoro dwa ostatnie kształty na wynik WPŁYWAJĄ.**
    Wpływają — ale nie własnym padem, tylko przez asercję stojącą DALEJ, której ten
    czytnik nie widzi i widzieć nie może bez przejścia przepływu danych. Zaliczenie
    ich do strażników byłoby więc twierdzeniem mocniejszym niż pomiar: klasa `przybita`
    znaczy „ruch o jeden PADA", a tego o gałęzi redakcyjnej nie wiadomo. Ten sam wybór
    co w 6.D254: przyrząd ma mówić o tym, co widzi.
    """
    gora = rodzic.get(wezel)
    znak = 1
    while gora is not None:
        if isinstance(gora, ast.UnaryOp) and isinstance(gora.op, ast.Not):
            znak = -znak
            gora = rodzic.get(gora)
            continue
        if isinstance(gora, ast.Assert):
            return znak if gora.test is not None else None
        if isinstance(gora, ast.If):
            if wezel is gora.test or _pod_testem(wezel, gora.test):
                # Wyjatek w CIELE: warunek opisuje porazke, twierdzeniem jest
                # jego zaprzeczenie. Wyjatek w ODNODZE `else`: warunek opisuje
                # przypadek dobry, wiec twierdzeniem jest on sam. Zadnej z tych
                # dwoch postaci nie ma dzis w drzewie ani razu — obie sa tu po to,
                # zeby przepisanie asercji nie ruszalo klasy, i obie maja wlasny
                # przypadek w kontroli przyrzadu, bo bez niego druga bylaby
                # zgadywaniem.
                if _wyjatki_bloku(gora.body):
                    return -znak
                if _wyjatki_bloku(gora.orelse):
                    return znak
                return None
            return None
        if isinstance(gora, (ast.comprehension, ast.IfExp, ast.While,
                             ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            return None
        gora = rodzic.get(gora)
    return None


def _pod_testem(wezel, test):
    return any(pod is wezel for pod in ast.walk(test))


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
            rodzic = {}
            for wezel in ast.walk(drzewo):
                for dziecko in ast.iter_child_nodes(wezel):
                    rodzic[dziecko] = wezel
            for wezel in ast.walk(drzewo):
                if isinstance(wezel, ast.Assign):
                    for cel in wezel.targets:
                        if isinstance(cel, ast.Name) and ZAPADKA_NAZWA.match(cel.id):
                            out.setdefault(cel.id, (nazwa_pliku, []))
                if not isinstance(wezel, ast.Compare):
                    continue
                # 6.D258: najpierw POSTAĆ ZDANIA, dopiero potem operator. Porównanie,
                # które niczego nie twierdzi, nie jest ani nośne, ani strzegące —
                # a zdanie zaprzeczone twierdzi operator ZAPRZECZONY, nie zapisany.
                znak = polaryzacja_porownania(wezel, rodzic)
                if znak is None:
                    continue
                czlony = [wezel.left] + list(wezel.comparators)
                for i, operator in enumerate(wezel.ops):
                    nazwa_op = type(operator).__name__
                    if nazwa_op not in ODWROTNY_OPERATOR:
                        continue
                    if znak < 0:
                        nazwa_op = ZAPRZECZONY_OPERATOR[nazwa_op]
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
#: Zapadek: 68. **Przybitych: 17, częściowych: 3, WOLNYCH: 46, poza zasięgiem skanu: 2.**
#:
#: **To zdanie jest przepisane, a nie dopisane obok — po raz DRUGI (15.09.2026).**
#: Stało tu najpierw „Trzydzieści osiem: 13 przybitych…" (11.09.2026, `52752c9`)
#: i przestało być prawdą, gdy rejestr urósł o cztery pozycje; nie zauważył tego żaden
#: test, bo bramka niżej porównuje SŁOWNIK z drzewem, a nie to zdanie ze słownikiem.
#: Od 12.09.2026 porównuje je `test_prose_counts.py`, więc liczby nie mogą się już
#: rozjechać po cichu. Suma stoi CYFRAMI, nie słownie, i to jest warunek działania
#: tamtej bramki.
#:
#: **Dziś zmienia się KSZTAŁT, nie liczby, i powód jest gramatyczny (6.D218).** Do
#: 15.09.2026 zdanie brzmiało „N zapadek: **A przybitych, B częściowe, C WOLNE i D poza
#: zasięgiem skanu.**", a `WZORZEC_ZAPADEK` miał te cztery formy wpisane na sztywno —
#: więc wymuszał je **bez względu na liczebnik, który przed nimi stoi**. Po polsku forma
#: zależy od końcówki liczebnika, a rejestr rośnie, więc zdanie **było błędne przy
#: KAŻDEJ wartości w swojej historii**: 46/25, 48/27, 49/28, 50/29 i 51/30 żądały
#: „WOLNYCH", a przy 54/33 błąd przeskoczył o słowo — `WOLNE` po 33 jest poprawne,
#: ale „54 zapadek" po 54 już nie (ma być „zapadki").
#:
#: **Nowy kształt nie wymusza żadnej formy**, bo liczba stoi PO etykiecie, a rzeczownik
#: jest rządzony dwukropkiem, nie liczebnikiem. Wzór był w tym samym pliku od początku:
#: `WZORZEC_MODULOW` czyta „dla N modulow" i jest odporny, bo przypadek narzuca przyimek
#: „dla", a nie liczba. Wzorzec przechwytuje nadal te same PIĘĆ liczb i nie jest przez
#: to ani o jotę luźniejszy — a poszerzenie go o obie formy byłoby, i dlatego odpada.
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
    # 6.D258: `wolna` -> `poza skanem`, i to JEDYNY werdykt, który poprawka
    # polaryzacji rusza na dzisiejszym drzewie. Jedyne porównanie tej zapadki
    # to `if len(odciski) <= PRÓG:` w `mutation_sweep.py:1427` — gałąź wybierająca
    # SZEROKOŚĆ TABELI w raporcie, bez `raise` w żadnej z odnóg. Nie twierdzi nic,
    # więc klasyfikator jej już nie widzi, a zapadka zostaje bez ani jednego
    # porównania. `wolna` mówiła „strażnika nie ma"; `poza skanem` mówi „nie ma
    # też nośnego" — i to drugie jest prawdą, której pierwsze nie niosło.
    "MAX_ODCISKOW_W_RAPORCIE": (POZA_SKANEM, "mutation_sweep.py"),
    # Pomiar 6.D254 NIE ZNIKA razem z wpisem w `ROZSTRZYGALNE_POMIAREM`,
    # z ktorego ta zapadka wypadla, bo tamten slownik opisuje wylacznie klase
    # `wolna`: dwa uzycia w `test_mutation_sweep.py` przez `sweep.NAZWA` buduja
    # wejscie jako `range(PROG)` i `range(PROG + 1)`, czyli PARE na granicy —
    # ksztalt najmocniejszy z mozliwych. Zmierzone mutacja: granica jedzie RAZEM
    # z progiem, wiec 8 -> 1008 daje 133/133 i nie zapala nic. Werdykt sie wiec
    # nie zmienil; zmienila sie tylko jego NAZWA, z „nie ma straznika" na
    # „nie ma tez nosnego".
    # 6.D259: obie WOLNE i obie z tego samego powodu co reszta podlog tej klasy —
    # stoja wylacznie jako prawa strona jednego porownania. Para jest tu trescia:
    # gorna pilnuje, zeby nie przybylo golych liczb, dolna — zeby czytnik nie oslepl,
    # bo oslepiony przechodzi gorna CELUJACO (6.D27).
    # 6.D260: obie WOLNE, obie stoja wylacznie jako prawa strona jednej podlogi.
    # 6.D261: podloga na liczbe podpisow `private static`, WOLNA — stoi wylacznie
    # jako prawa strona jednego porownania, obok DWoCH rownosci na liczby rodzin.
    "MIN_PODPISOW_POMOCNIKA": (WOLNA, "test_csharp_test_methods.py"),
    "MIN_OGNIW_RAZEM": (WOLNA, "test_value_chains.py"),
    "MIN_STALYCH_Z_LANCUCHEM": (WOLNA, "test_value_chains.py"),
    "MAX_POGRUBIONYCH_BEZ_POKRYCIA": (WOLNA, "test_message_claims.py"),
    "MIN_POGRUBIONYCH": (WOLNA, "test_message_claims.py"),
    "MAX_REPORTS_WITHOUT_FIELD_LINE": (PRZYBITA, "test_report_hygiene.py"),
    "MAX_ROZSZERZEN_BEZ_TRAFIEN": (WOLNA, "test_report_hygiene.py"),
    "MAX_SEKWENCJI_UCIECZKI": (PRZYBITA, "test_bytecode_staleness.py"),
    "MAX_UNMATCHED_NEEDLES": (PRZYBITA, "test_needle_specificity.py"),
    "MAX_WOLNO_WPROST": (WOLNA, "test_tree_walks.py"),
    "MAX_ZAPISOW_W_DRZEWIE": (PRZYBITA, "test_tree_writes.py"),
    "MINIMUM_CALLERS": (WOLNA, "test_platform_length_in_pipeline.py"),
    "MINIMUM_CLAIMS": (WOLNA, "test_report_claims.py"),
    "MINIMUM_DEKLARACJI": (WOLNA, "test_dead_constants_csharp.py"),
    # 6.D232: trzy podłogi na GAŁĘZIE wzorca deklaracji, obok podłogi na sumę.
    # Suma broni przed wzorcem MARTWYM, a nie przed OKALECZONYM: wymuszenie
    # modyfikatora dostępu zabiera 43 z 389 deklaracji i sumę przechodzi.
    # Wszystkie trzy WOLNE z tego samego powodu co `MINIMUM_DZIUR` obok: stałych
    # przybywa razem z kodem, więc przybicie czerwieniałoby przy każdej nowej.
    "MINIMUM_BEZ_MODYFIKATORA": (WOLNA, "test_dead_constants_csharp.py"),
    "MINIMUM_CONST": (WOLNA, "test_dead_constants_csharp.py"),
    "MINIMUM_STATIC_READONLY": (WOLNA, "test_dead_constants_csharp.py"),
    # 6.D225: dolne ostrze na skan dziur interpolacji. Bez niego oślepiony
    # czytnik dziur jest dziś ZIELONY — martwych nie przybywa, bo dziś żadna
    # stała nie wychodzi przez to na martwą. Klasa WOLNA: liczba dziur rośnie
    # razem z kodem i przybicie jej czerwieniałoby przy każdej nowej interpolacji.
    "MINIMUM_DZIUR": (WOLNA, "test_dead_constants_csharp.py"),
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
    # 6.D209: podloga na skan ksztaltu `NAZWA = N` w `reports/`. WOLNA, bo jest progiem
    # jednostronnym: raportow przybywa. Werdykt 6.D209 nie stoi na niej, tylko na ZBIORZE
    # `CYTATY_NIE_TWIERDZENIA`, porownywanym z drzewem w obie strony.
    "MIN_WYSTAPIEN_W_JEDNYCH_GRAWISACH": (WOLNA, "test_report_claims.py"),
    "MINIMUM_LICZB_SLOWNYCH": (WOLNA, "test_prose_counts.py"),
    # 6.D206: dwie podlogi na skan stalych, ktorych `#:` deklaruje datowany pomiar.
    # WOLNE, bo sa progami jednostronnymi: obie populacje rosna przy kazdym nowym
    # datowanym komentarzu, czyli przy pracy poprawnej, wiec rownosc kazalaby je
    # podnosic bez powodu. Rozstrzygniecie 6.D206 nie stoi zreszta na nich, tylko
    # na ZBIORZE `Z_DATA_ISO_W_LITERALE`, ktory jest porownywany z drzewem w obie
    # strony — te dwie bronia wylacznie przed skanem, ktory oslepl (6.D27).
    "MIN_KONTENEROW_Z_POMIAREM_W_KOMENTARZU": (WOLNA, "test_suite_runtime_budget.py"),
    "MIN_PLIKOW_YAML_CI": (WOLNA, "test_ci_workflows.py"),
    # 6.D216: trzy podlogi na czytnik sekcji „zauwazone, nie tkniete". WOLNE i to jest
    # wlasnosc przedmiotu, nie niedbalstwo: raportow przybywa z kazda pozycja, wiec
    # rownosc kazalaby je podnosic przy kazdym commicie z raportem. Przed ruszeniem
    # w zakazana strone broni ich `test_twierdzenie_DOPISANE_do_sekcji_WCHODZI_do_pomiaru`
    # — kontrola przyrzadu na wejsciu syntetycznym, ktora nie zalezy od katalogu.
    "MIN_RAPORTOW_Z_SEKCJA": (WOLNA, "test_report_claims.py"),
    "MIN_SEKCJI_ZAUWAZONE": (WOLNA, "test_report_claims.py"),
    # 6.D227: obie podlogi slajsu zakresu. WOLNE z tego samego powodu co sasiedzi
    # wyzej — raportow przybywa, przepisywac ich nie wolno (6.D108), wiec rownosc
    # zapalalaby sie na kazdym nowym poprawnym raporcie. Sa DWIE, bo zwezenie
    # WZORCA i zwezenie OKNA zapalaja rozne: bez pary nie da sie ich odroznic.
    "MIN_SLAJS_SZEROKI": (WOLNA, "test_report_claims.py"),
    "MIN_STALYCH_Z_POMIAREM_W_KOMENTARZU": (WOLNA, "test_suite_runtime_budget.py"),
    "MIN_TWIERDZEN_O_ZAKRESIE": (WOLNA, "test_report_claims.py"),
    "MIN_TWIERDZEN_W_ZAUWAZONYCH": (WOLNA, "test_report_claims.py"),
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
    # 6.D240: podłoga na liczbę plików `tools/tests/*.py`, po których chodzi skan
    # zależności zestawu. Bez niej oślepiony czytnik oddaje PUSTY zbiór zależności,
    # a pusty zbiór czyta się jako „zestaw niczego nie potrzebuje" i bramka sondy
    # wychodzi zielona nad każdym brakiem. Klasa WOLNA: modułów przybywa razem
    # z zadaniami, więc przybicie czerwieniałoby przy każdym nowym module.
    "MINIMUM_MODULOW_ZESTAWU": (WOLNA, "test_ci_workflows.py"),
    "MIN_MODULE_NAMES": (WOLNA, "test_field_paths.py"),
    # 6.D237: podłoga na liczbę nazw modułu przychodzących z DRUGIEGO i dalszego
    # argumentu `test_all.py`, na blokach WSZYSTKICH. WOLNA, i to jest własność
    # przedmiotu: bloków wykonanych tylko przybywa, więc równość kazałaby podnosić
    # ten próg przy każdej domkniętej pozycji z wywołaniem dwuargumentowym. Przed
    # ruchem w zakazaną stronę broni jej kontrola przyrządu na wejściu syntetycznym,
    # niezależna od zawartości drzewa.
    "MIN_NAZW_Z_DALSZEGO_ARGUMENTU": (WOLNA, "test_field_paths.py"),
    "MIN_WYWOLAN_W_WYKONANYCH": (WOLNA, "test_field_paths.py"),
    "MIN_NEEDLES": (WOLNA, "test_needle_specificity.py"),
    "MIN_PATHS": (POZA_SKANEM, "test_field_paths.py"),
    "MIN_PATHS_IN_TREE": (PRZYBITA, "test_bin_path_framework.py"),
    "MIN_REPORTS": (PRZYBITA, "test_report_hygiene.py"),
    # 6.D238: podłoga na liczbę wierszy tabeli §4 `reports/T-401-line-run.md`,
    # które czyta wiązanie arytmetyczne kolumny różnicy. WOLNA, i to jest wybór
    # wymuszony przez 6.D108: raport jest zapisem swojego dnia, a równość zapalałaby
    # się na DOPISANIU wiersza, czyli na pracy poprawnej (6.D27). Zapasu nie ma i mieć
    # nie musi, ale POWÓD JEST INNY, NIŻ NAPISAŁEM NAJPIERW, i poprawiła to kontrola
    # negatywna. Zdanie brzmiało: „liczbę wierszy przybija już `set(found) == PACKAGES`
    # w `lower_bound_kmh`, więc usunięcie wiersza zapala TAMTĄ równość, a NIE tę
    # podłogę". Zmierzone: usunięcie wiersza zapala SZEŚĆ bramek i ta podłoga jest
    # wśród nich. Prawdziwe zostaje tylko to, że podłoga nie jest JEDYNYM strażnikiem
    # liczby wierszy; nieprawdziwe było, że nic nie dokłada. Dokłada komunikat, który
    # nazywa POWÓD spadku („oślepły wzorzec, a nie skrócona tabela"), a tamta równość
    # wypisuje sam zbiór pakietów.
    "MIN_WIERSZY_Z_ARYTMETYKA": (WOLNA, "test_t401_citation.py"),
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


# --- 6.D254: czy KLASA mówi prawdę o ZACHOWANIU -------------------------------

def swiadkowie_klasy(nazwa, katalog=None, root=None):
    """`[(plik, wiersz, postac)]` — gdzie stoi kazde TWIERDZACE porownanie tej zapadki.

    **Po co, skoro klase i tak liczy `klasa_zapadki` (6.D258).** Bo komunikat bramki
    klas twierdzil dotad PRZYCZYNE („doszedl straznik", „ubyl straznik"), a przyczyny
    nie mierzyl: widzial wylacznie klase PRZED i PO. Przy przepisaniu asercji na
    `if … : raise` mowil wiec o straznku, ktory nie doszedl, a przy dzisiejszej
    poprawce polaryzacji mowilby o straznku przy zmianie do `poza skanem`, ktorej
    zdanie nie przewiduje w ogole.

    Ten czytnik nie zgaduje przyczyny — podaje MIEJSCA I POSTACIE, z ktorych klasa
    wyszla. Czytajacy widzi wtedy sam, czy ten sam wiersz zmienil pisownie, czy
    doszedl wiersz nowy. **Odroznienia „tresc kontra pisownia" bramka nie zrobi za
    niego i to jest granica przyrzadu, nie przeoczenie:** do tego potrzebny bylby
    stan PRZED zmiana, a bramka ma do dyspozycji tylko rejestr (klase) i dzisiejsze
    drzewo. Ten sam ksztalt, ktory 6.D255 nazwalo czwarta nieprawda nie do zlapania.
    """
    baza = katalog or os.path.join(ROOT, "tools", "tests")
    korzen = root or ROOT
    out = []
    for gdzie, _katalogi, pliki in TW.walk(baza, korzen):
        for nazwa_pliku in sorted(pliki):
            if not nazwa_pliku.endswith(".py"):
                continue
            with open(os.path.join(gdzie, nazwa_pliku), encoding="utf-8") as uchwyt:
                drzewo = ast.parse(uchwyt.read())
            rodzic = {}
            for wezel in ast.walk(drzewo):
                for dziecko in ast.iter_child_nodes(wezel):
                    rodzic[dziecko] = wezel
            for wezel in ast.walk(drzewo):
                if not isinstance(wezel, ast.Compare):
                    continue
                if not any((isinstance(n, ast.Name) and n.id == nazwa)
                           or (isinstance(n, ast.Attribute) and n.attr == nazwa)
                           for n in ast.walk(wezel)):
                    continue
                znak = polaryzacja_porownania(wezel, rodzic)
                postac = {1: "wprost", -1: "zaprzeczone",
                          None: BEZ_TWIERDZENIA}[znak]
                out.append((nazwa_pliku, wezel.lineno, postac))
    return sorted(out)


def _argumenty_wyjatku(exc):
    """Wyrażenia liczone WYŁĄCZNIE przy padzie — argumenty `raise <Wyjątek>(…)`.

    Sam `raise NAZWA` bez wywołania nie niesie żadnego wyrażenia, więc daje pustkę;
    `raise AssertionError(f"… {PRÓG} …")` niesie f-string i to on jest komunikatem.
    """
    if isinstance(exc, ast.Call):
        return list(exc.args) + [k.value for k in exc.keywords]
    return []


def uzycia_zapadek(katalog=None, root=None):
    """`{nazwa: [(plik, wiersz, rola)]}` dla wszystkich użyć nazw o kształcie zapadki.

    Cztery role, i podział na nie jest CAŁĄ treścią tego czytnika:

    * ``definicja`` — przypisanie,
    * ``nosna`` — nazwa stoi wprost w `ast.Compare`, czyli od niej coś zależy,
    * ``komunikat`` — nazwa stoi w `Assert.msg`, czyli w wyrażeniu liczonym
      WYŁĄCZNIE przy padzie; nie zależy od niej nic,
    * ``inna`` — wszystko pozostałe: argument, arytmetyka, `range(PRÓG + 1)`.

    **Czyta `ast.Attribute` na równi z `ast.Name`, i to jest różnica wobec
    `_porownania_zapadek`.** Tamten czytnik widzi wyłącznie `ast.Name`, więc zapadka
    używana w innym module jako `moduł.NAZWA` jest dla klasyfikatora niewidzialna.
    Zmierzone 17.09.2026: tak stoją `MAX_ODCISKOW_W_RAPORCIE` (`sweep.` w
    `test_mutation_sweep.py`) i `MINIMUM_DETAIL_BLOCKS` (`tb.` w `test_field_paths.py`).
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
            rodzic = {}
            for wezel in ast.walk(drzewo):
                for dziecko in ast.iter_child_nodes(wezel):
                    rodzic[dziecko] = wezel
            w_komunikacie = set()
            for wezel in ast.walk(drzewo):
                if isinstance(wezel, ast.Assert) and wezel.msg is not None:
                    for pod in ast.walk(wezel.msg):
                        w_komunikacie.add(id(pod))
                # 6.D258, DRUGA GŁOWA tej samej usterki: komunikat przeniesiony
                # z `assert …, (…)` do `raise AssertionError(…)` przestawał być
                # komunikatem i stawał się roli `inna` — czyli DRUGIM UŻYCIEM,
                # o którym bramka `wolnych` mówiła „werdykt przestał wynikać
                # z kształtu". Nie przestawał; zmieniła się PISOWNIA. Zmierzone
                # 17.09.2026 przy KN-1: ta bramka (moja własna, z 6.D254) padała
                # razem z bramką klas, a pozycja 6.D258 znała tylko tę drugą.
                if isinstance(wezel, ast.Raise) and wezel.exc is not None:
                    for arg in _argumenty_wyjatku(wezel.exc):
                        for pod in ast.walk(arg):
                            w_komunikacie.add(id(pod))
            for wezel in ast.walk(drzewo):
                if isinstance(wezel, ast.Assign):
                    for cel in wezel.targets:
                        if isinstance(cel, ast.Name) and ZAPADKA_NAZWA.match(cel.id):
                            out.setdefault(cel.id, []).append(
                                (nazwa_pliku, wezel.lineno, "definicja"))
                nazwa = None
                if isinstance(wezel, ast.Name) and isinstance(wezel.ctx, ast.Load) \
                        and ZAPADKA_NAZWA.match(wezel.id):
                    nazwa = wezel.id
                elif isinstance(wezel, ast.Attribute) and ZAPADKA_NAZWA.match(wezel.attr):
                    nazwa = wezel.attr
                if nazwa is None:
                    continue
                if id(wezel) in w_komunikacie:
                    rola = "komunikat"
                elif isinstance(rodzic.get(wezel), ast.Compare):
                    rola = "nosna"
                else:
                    rola = "inna"
                out.setdefault(nazwa, []).append((nazwa_pliku, wezel.lineno, rola))
    return out


def wolne_rozstrzygalne_pomiarem(katalog=None, root=None):
    """Które zapadki klasy `wolna` NIE mają werdyktu przesądzonego kształtem.

    **Podział, którego rejestr sam nie robi, a który zmienia sens słowa `wolna`.**
    Zapadka używana wyłącznie jako prawa strona JEDNEJ podłogi `assert len(X) >= PRÓG`
    jest `wolna` z arytmetyki, a nie z pomiaru: `len(X) >= 0` zachodzi przy KAŻDEJ
    zawartości repozytorium, więc obniżenie progu nie może zapalić niczego — także
    przy czytniku oślepionym do zera, czyli przy dokładnie tej awarii, przed którą
    ta podłoga ma bronić (6.D27). Mutacja takiej zapadki niczego nie rozstrzyga;
    jej jedyna treść to „nazwa nie jest użyta nigdzie indziej".

    Zapadka, która ma DRUGIE użycie — drugie porównanie, arytmetykę na progu,
    odwołanie z innego modułu — mogła zapalić i musiała zostać zmierzona.
    """
    out = {}
    for nazwa, gdzie in uzycia_zapadek(katalog, root).items():
        if ZAPADKI.get(nazwa, (None,))[0] != WOLNA:
            continue
        nosne = [x for x in gdzie if x[2] == "nosna"]
        inne = [x for x in gdzie if x[2] == "inna"]
        if len(nosne) != 1 or inne:
            out[nazwa] = sorted(nosne + inne)
    return out


#: Zapadki `wolna`, których werdykt trzeba było ZMIERZYĆ, a nie odczytać z kształtu
#: — z powodem, bo sam fakt drugiego użycia nie mówi, czy to użycie cokolwiek trzyma.
#:
#: Obie zmierzono mutacją 17.09.2026 (6.D254) i obie wyszły `wolna` mimo drugiego
#: użycia; liczby są w `reports/6d254-klasa-zapadki-a-zachowanie.md`.
ROZSTRZYGALNE_POMIAREM = {
    "MINIMUM_CLAIMS":
        "drugie porównanie (`checked - datowane >= PRÓG`) i wejście syntetyczne 6.D230 "
        "w `test_report_claims.py:1722`. Zmierzone: 10 -> 0 daje 29/29, bo asercje "
        "przy wejściu syntetycznym stoją na liczbach z próbki, nie na wartości z kodu.",
}

#: Jak DALEKO trzeba ruszyć zapadkę `czesciowa`, żeby cokolwiek padło — zmierzone
#: mutacją 17.09.2026 (6.D254), po jednym kroku aż do granicy zapłonu.
#:
#: **Klasa `czesciowa` nie upadła w pomiarze i to jest wynik odwrotny do tego, którego
#: pozycja szukała.** Wszystkie trzy zachowują się dokładnie tak, jak twierdzą: ruch
#: o jeden przechodzi, ruch dostatecznie daleki zapala. Upadło co innego — słowo
#: „daleki". Odległość zapłonu jest zmierzona i wynosi od **3** do **113** kroków
#: przy wartościach 10 i 120, a klasa o niej nie mówi NIC.
#:
#: Skutek jest praktyczny, nie stylistyczny: pomiar krokiem proporcjonalnym
#: (ćwierć wartości) pokazuje `MINIMUM_SUPPORTED_MAJOR` jako `czesciowa`, a dwie
#: pozostałe jako `wolna` — czyli **ta sama klasa, ten sam przyrząd, dwa różne
#: werdykty**, w zależności od tego, jak duży krok ktoś wybierze. Dla dwóch z trzech
#: zapala się dopiero strażnik mierzący ATRAPĘ z kontroli przyrządu: napis `"bo tak"`
#: (7 znaków) i warunek `0 < próg`. Klasa mówi „strażnik o innej populacji" i to jest
#: prawda — tyle że tą populacją jest wejście syntetyczne, a nie drzewo, więc zapadka
#: przejeżdża cały swój legalny zakres, zanim cokolwiek drgnie.
#:
#: Trójka: `(wartość w drzewie, najwyższa wartość, przy której PADA, co pada)`.
ODLEGLOSC_ZAPLONU_CZESCIOWYCH = {
    "MINIMUM_SUPPORTED_MAJOR": (
        10, 7,
        "`test_parsers_reject_what_they_should`; 10 -> 9 daje 51/51 kod 0, "
        "10 -> 7 daje 50/51 kod 1. Strażnikiem jest `tfm_major('net8.0')`, czyli 8 "
        "— odległość zapłonu TRZY i jako jedyna mieści się w kroku proporcjonalnym."),
    "MINIMUM_POWODU": (
        120, 7,
        "`test_kazda_poprawka_zapisu_wykonanego_niesie_date_i_powod`; 119 i 90 dają "
        "43/43 kod 0, 8 daje 43/43 kod 0, 7 daje 42/43 kod 1. Strażnikiem jest napis "
        "`bo tak` z kontroli przyrządu, długość 7 — odległość zapłonu STO TRZYNAŚCIE."),
    "MINIMUM_DOCUMENTED_ITEMS": (
        6, 0,
        "`test_the_ratchet_cannot_be_set_above_what_it_guards`; 5, 3 i 1 dają 36/36 "
        "kod 0, dopiero 0 daje 35/36 kod 1. Strażnikiem jest warunek o KSZTAŁCIE "
        "stałej (`0 < próg < próg doby pracy`), a nie podłoga na liczbę pozycji "
        "— odległość zapłonu SZEŚĆ, czyli cały legalny zakres."),
}


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
    # 6.D258: komunikat podaje ZMIERZONE miejsca i postacie porownan, a nie
    # domyslana przyczyne. Poprzednia wersja mowila „doszedl straznik" takze
    # wtedy, gdy nikt nie doszedl, a tylko przepisano asercje na `if … : raise`
    # — i nie miala zdania o zmianie do `poza skanem`, ktora dzis jest mozliwa.
    swiadkowie = {n: swiadkowie_klasy(n) for n, _b, _j in inna_klasa}
    assert inna_klasa == [], (
        "zapadka zmieniła klasę (nazwa, było, jest): %s. Porownania tej zapadki "
        "w drzewie, z postacia zdania: %s. Ten sam wiersz w innej postaci znaczy, "
        "ze zmienila sie PISOWNIA i poprawic trzeba czytnik, a nie wpis; wiersz "
        "nowy albo znikniety znaczy, ze zmienila sie TRESC i poprawic trzeba wpis. "
        "Bramka tego za czytajacego nie rozstrzygnie, bo nie ma stanu PRZED zmiana."
        % (inna_klasa, swiadkowie))

    assert len(w_drzewie) == ZAPADEK_RAZEM == 68, (
        "zapadek w drzewie %d, na liście %d, pomiar z 11.09.2026 mówił 38, "
        "po 6.D146 — 40, po 6.D147 — 42 (doszła zapadka na sekwencje ucieczki "
        "i próg KW jej skanu), po 6.D187 — 44 (dwa progi KW skanu gołych nazw), "
        "po 6.D190 — 45 (podłoga na liczbę wpisów runnera), po 6.D203 — 46 "
        "(dolne ostrze na skan liczebników), po 6.D206 — 48 (dwie podłogi na skan "
        "stałych z datowaną deklaracją pomiaru w komentarzu `#:`), a po 6.D207 — 49 "
        "(podłoga na skan zdań deklarujących pomiar w docstringach), a po 6.D209 — 50 "
        "(podłoga na skan kształtu `NAZWA = N` w raportach), a po 6.D222 — 51 "
        "(podłoga na liczbę plików YAML-a CI oglądanych przez loader ścisły), "
        "a po 6.D216 — 54 (trzy podłogi na czytnik sekcji „zauważone”: sekcje, raporty "
        "i twierdzenia liczbowe), a po 6.D227 — 57 (dwie podłogi na czytnik slajsu "
        "zakresu: wąski i szeroki; szeroki stoi obok wąskiego, bo zwężenie WZORCA "
        "i zwężenie OKNA zapalają różne), a po scaleniu 6.D225 — 58 (podłoga "
        "`MINIMUM_DZIUR` na czytnik dziur interpolacji). **Liczba jest PRZELICZONA "
        "z drzewa scalonego, a nie wzięta z żadnej strony konfliktu:** gałąź miała 56, "
        "`main` 57, a scalone drzewo niesie OBIE zapadki i ma 58, a po 6.D237 — 59 "
        "(podłoga na liczbę nazw modułu przychodzących z DRUGIEGO i dalszego "
        "argumentu `test_all.py`), a po 6.D238 — 60 (podłoga na liczbę wierszy tabeli §4 "
        "T-401 czytanych przez wiązanie arytmetyczne kolumny różnicy), a po 6.D232 — 63 "
        "(TRZY podłogi na GAŁĘZIE wzorca deklaracji C#: `const`, `static readonly` "
        "i przekrój „bez modyfikatora dostępu”, bo suma deklaracji broni przed wzorcem "
        "MARTWYM, a nie przed OKALECZONYM). Liczba 63 jest PRZELICZONA z drzewa po "
        "scaleniu, a nie wzięta z żadnej strony konfliktu: gałąź 6.D232 mierzyła bazę "
        "59 i dawała 62, `main` miał w tym czasie 60, a scalone drzewo niesie WSZYSTKIE "
        "zapadki obu stron"
        % (len(w_drzewie), ZAPADEK_RAZEM))

    # Liczby zbiorcze. **Nie jest to ozdobnik komunikatu i pokazała to KN-7.**
    # Asercje wyżej pilnują, żeby lista zgadzała się z DRZEWEM — a te cztery liczby
    # są zdaniem o samej liście, publikowanym w jej komentarzu i w raporcie. Gdy ktoś
    # przybije wolną zapadkę i UCZCIWIE poprawi jej wpis, wszystko wyżej przechodzi,
    # a „21 wolnych" staje się nieprawdą, której nie zgłasza nic. KN-7 wykonała
    # dokładnie ten scenariusz: jedyną czerwienią była ta asercja.
    ile = collections.Counter(w_drzewie.values())
    assert (ile[PRZYBITA], ile[CZESCIOWA], ile[WOLNA], ile[POZA_SKANEM]) == (17, 3, 46, 2), (
        "klasy zapadek: przybitych %d, częściowych %d, WOLNYCH %d, poza skanem %d — "
        "pomiar z 11.09.2026 mówił 13/3/21/1, po 6.D146 — 13/3/23/1, a po 6.D147 — "
        "14/3/24/1, po 6.D151 — 15/3/23/1, po 6.D167 — 17/3/21/1, po 6.D187 — "
        "17/3/23/1, po 6.D190 — 17/3/24/1, po 6.D203 — 17/3/25/1, po 6.D206 — "
        "17/3/27/1, po 6.D207 — 17/3/28/1, a po 6.D209 — 17/3/29/1, a po 6.D222 — "
        "17/3/30/1, a po 6.D216 — 17/3/33/1, a po 6.D240 — 17/3/34/1, a po 6.D227 — "
        "17/3/36/1, a po 6.D225 — 17/3/37/1, a po 6.D237 — 17/3/38/1, a po 6.D238 — "
        "17/3/39/1, a po 6.D232 — 17/3/42/1, a po 6.D258 — 17/3/41/2, "
        "a po 6.D259 — 17/3/43/2 (dwie zapadki bramki prozy), a po 6.D260 — 17/3/45/2 "
        "(dwie podlogi bramki lancuchow), a po 6.D261 — 17/3/46/2 (podloga bramki rodzin) "
        "(poprawka polaryzacji przestala widziec galaz, ktora niczego nie twierdzi); "
        "wolne to te, "
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


def test_czytnik_polaryzacji_widzi_ksztalt_ktory_ma_widziec():
    """**Kontrola przyrzadu do 6.D258 — piec postaci zdania na drzewie probnym.**

    Bez niej poprawka polaryzacji bylaby nie do odroznienia od czytnika, ktory
    po prostu przestal cokolwiek widziec: klasyfikator odkladajacy KAZDE porownanie
    daje same `poza skanem` i tez „nie zmienia klasy przy przepisaniu asercji".
    To jest 6.D27 w czystej postaci, wiec kazda z piaciu postaci ma tu wlasny
    oczekiwany werdykt, a nie wspolny.

    Pary sa dobrane tak, zeby ROZNICA byla trescia: `MAX_ASERCJA` i `MAX_GALAZ_RAISE`
    to TO SAMO zdanie napisane dwoma sposobami i musza dostac te sama klase; gdyby
    czytnik czytal pisownie, dostalyby rozne.
    """
    zrodlo = (
        # 1. straznik wprost — `assert PROG <= …` strzeze zapadki MAX
        "MAX_ASERCJA = 3\n"
        "def a():\n"
        "    assert len(lista) <= MAX_ASERCJA\n"
        "    assert MAX_ASERCJA <= len(lista)\n"
        # 2. TO SAMO zdanie jako galaz z podniesieniem wyjatku
        "MAX_GALAZ_RAISE = 3\n"
        "def b():\n"
        "    if len(lista) > MAX_GALAZ_RAISE:\n"
        "        raise AssertionError('za duzo')\n"
        "    if MAX_GALAZ_RAISE > len(lista):\n"
        "        raise AssertionError('za malo')\n"
        # 3. galaz BEZ podniesienia wyjatku — nie twierdzi nic
        "MAX_GALAZ_CICHA = 3\n"
        "def c():\n"
        "    if len(lista) <= MAX_GALAZ_CICHA:\n"
        "        print('waska tabela')\n"
        "    else:\n"
        "        print('szeroka tabela')\n"
        # 4. zaprzeczenie pod `assert not`
        "MAX_POD_NOT = 3\n"
        "def d():\n"
        "    assert not len(lista) > MAX_POD_NOT\n"
        "    assert not MAX_POD_NOT > len(lista)\n"
        # 5. wyjatek w ODNODZE, nie w ciele - twierdzeniem jest sam warunek
        "MAX_ODNOGA_RAISE = 3\n"
        "def f():\n"
        "    if len(lista) <= MAX_ODNOGA_RAISE:\n"
        "        pass\n"
        "    else:\n"
        "        raise AssertionError('za duzo')\n"
        "    if MAX_ODNOGA_RAISE <= len(lista):\n"
        "        pass\n"
        "    else:\n"
        "        raise AssertionError('za malo')\n"
        # 6. filtr wyrazenia listowego - nie twierdzi nic
        "MAX_FILTR = 3\n"
        "def e():\n"
        "    krotkie = [x for x in lista if len(x) < MAX_FILTR]\n"
        "    assert krotkie == []\n")

    with tempfile.TemporaryDirectory(prefix="metro-polaryzacja-") as katalog:
        with open(os.path.join(katalog, "test_probne.py"), "w",
                  encoding="utf-8") as uchwyt:
            uchwyt.write(zrodlo)
        klasy = zapadki_w_drzewie(katalog, katalog)

    oczekiwane = {
        "MAX_ASERCJA": PRZYBITA,
        "MAX_GALAZ_RAISE": PRZYBITA,
        "MAX_GALAZ_CICHA": POZA_SKANEM,
        "MAX_POD_NOT": PRZYBITA,
        "MAX_ODNOGA_RAISE": PRZYBITA,
        "MAX_FILTR": POZA_SKANEM,
    }
    assert klasy == oczekiwane, (
        "czytnik polaryzacji dal %s, a mial dac %s"
        % (sorted(klasy.items()), sorted(oczekiwane.items())))

    # Para jest tu trescia: to samo zdanie dwoma sposobami, jedna klasa.
    assert klasy["MAX_ASERCJA"] == klasy["MAX_GALAZ_RAISE"], (
        "asercja i rownowazna jej galaz z `raise` dostaly rozne klasy — czytnik "
        "wrocil do czytania pisowni")
    # I kontrola w druga strone: gdyby czytnik odkladal WSZYSTKO, te trzy
    # bylyby `poza skanem` razem z dwoma pozostalymi i test wyzej by to zlapal.
    assert klasy["MAX_GALAZ_CICHA"] != klasy["MAX_ASERCJA"], (
        "galaz bez `raise` dostala klase straznika — polaryzacja nie jest czytana")


def test_klasa_POZA_SKANEM_mowi_o_granicy_przyrzadu_a_nie_o_zapadce():
    """Klasa opisuje DWIE granice przyrzadu i kazda ma wlasny ksztalt w drzewie.

    **Ten test jest przepisany, a nie dopisany obok (6.D258).** Do 17.09.2026 zdal
    jedno zdanie: „jedyny taki dzis to `MIN_PATHS`" — i to przestalo byc prawda,
    gdy poprawka polaryzacji przestala widziec porownania, ktore niczego nie
    twierdza. Klasa ma od dzis dwoch czlonkow z DWOCH ROZNYCH powodow, a lista
    nazw bez powodow bylaby napisem (6.D243), wiec kazdy powod jest tu sprawdzany
    W DRZEWIE, osobno:

    * ``MIN_PATHS`` — slownik trzech progow, porownywany PRZEZ ZMIENNA PETLI.
      Skan czyta `ast.Name` po stronie stalej, a tam stoi `floor`, wiec progu nie
      widzi. Granica dotyczy CZYTNIKA NAZWY.
    * ``MAX_ODCISKOW_W_RAPORCIE`` — jedyne porownanie stoi w galezi `if`, ktorej
      zadna odnoga nie podnosi wyjatku; galaz wybiera szerokosc tabeli w raporcie.
      Skan widzi nazwe doskonale i swiadomie ja odklada. Granica dotyczy
      POLARYZACJI, czyli tego, ze zdanie niczego nie twierdzi.

    Roznica miedzy nimi jest tresc, a nie formalnosc: pierwszego da sie wciagnac
    do skanu lepszym czytnikiem, drugiego nie da sie nigdy — bo tam nie ma czego
    czytac.
    """
    poza = sorted(n for n, (k, _m) in ZAPADKI.items() if k == POZA_SKANEM)
    assert poza == ["MAX_ODCISKOW_W_RAPORCIE", "MIN_PATHS"], poza

    w_drzewie = zapadki_w_drzewie()
    for nazwa in poza:
        assert w_drzewie[nazwa] == POZA_SKANEM, (
            "%s przestal byc poza skanem — sprawdz, ktory z dwoch ksztaltow "
            "zniknal, i przenies wpis do wlasciwej klasy" % nazwa)

    # Ksztalt pierwszy: prog przez zmienna petli.
    zrodlo = open(os.path.join(ROOT, "tools", "tests", "test_field_paths.py"),
                  encoding="utf-8").read()
    assert "for field, floor in MIN_PATHS.items()" in zrodlo, (
        "ksztalt, na ktorym stoi POZA_SKANEM dla MIN_PATHS, zniknal "
        "z `test_field_paths.py` — klasa opisuje wtedy stan, ktorego nie ma")

    # Ksztalt drugi: jedyne porownanie w galezi, ktora nie podnosi wyjatku.
    # Sprawdzone POLARYZACJA, a nie napisem: gdyby ktos dopisal tam `raise`,
    # zdanie zaczeloby twierdzic i klasa musialaby sie zmienic.
    drzewo = ast.parse(open(os.path.join(ROOT, "tools", "tests",
                                         "mutation_sweep.py"),
                            encoding="utf-8").read())
    rodzic = {}
    for wezel in ast.walk(drzewo):
        for dziecko in ast.iter_child_nodes(wezel):
            rodzic[dziecko] = wezel
    znalezione = []
    for wezel in ast.walk(drzewo):
        if not isinstance(wezel, ast.Compare):
            continue
        if not any(isinstance(n, ast.Name) and n.id == "MAX_ODCISKOW_W_RAPORCIE"
                   for n in ast.walk(wezel)):
            continue
        znalezione.append((wezel.lineno, polaryzacja_porownania(wezel, rodzic)))
    assert znalezione and all(znak is None for _w, znak in znalezione), (
        "porownanie MAX_ODCISKOW_W_RAPORCIE zaczelo cos twierdzic: %s — zapadka "
        "wyszla poza swoja klase i wpis trzeba przeliczyc" % znalezione)


def test_ktore_wolne_zapadki_sa_PRZESADZONE_ksztaltem_a_ktore_zmierzone():
    """**Słowo `wolna` znaczy w rejestrze dwie różne rzeczy — 6.D254.**

    Czterdzieści z czterdziestu dwóch zapadek tej klasy pada w drzewie wyłącznie jako
    prawa strona jednej podłogi `assert len(X) >= PRÓG`. Dla nich `wolna` jest
    TAUTOLOGIĄ kształtu: `len(X) >= 0` zachodzi zawsze, więc żaden ruch w dół nie ma
    czego zapalić i pomiar był rozstrzygnięty, zanim cokolwiek uruchomiono. Dwie mają
    drugie użycie i musiały zostać zmierzone naprawdę.

    Porównanie jest W OBIE STRONY, bo inaczej bramka byłaby wolna dokładnie w tym
    znaczeniu, które opisuje.
    """
    widziane = wolne_rozstrzygalne_pomiarem()

    nowe = sorted(n for n in widziane if n not in ROZSTRZYGALNE_POMIAREM)
    assert nowe == [], (
        "zapadka `wolna` dostała DRUGIE użycie: %s — jej werdykt przestał wynikać "
        "z kształtu i trzeba go zmierzyć mutacją, a wynik dopisać z powodem"
        % [(n, widziane[n]) for n in nowe])

    znikniete = sorted(n for n in ROZSTRZYGALNE_POMIAREM if n not in widziane)
    assert znikniete == [], (
        "wpis o zapadce rozstrzygalnej pomiarem, która dziś ma już tylko jedną "
        "podłogę: %s — zdejmij wpis, bo powód zniknął" % znikniete)

    wolnych = sum(1 for _n, (k, _m) in ZAPADKI.items() if k == WOLNA)
    przesadzonych = wolnych - len(ROZSTRZYGALNE_POMIAREM)
    assert (wolnych, przesadzonych) == (46, 45), (
        "wolnych %d, z tego przesądzonych kształtem %d — pomiar 17.09.2026 dał 42 i 40, "
        "a po 6.D258 daje 41 i 40: `MAX_ODCISKOW_W_RAPORCIE` wyszło z klasy `wolna` "
        "do `poza skanem`, więc ubyla ZAPADKA i ubyl jej WPIS w słowniku rozstrzygnięć; "
        "a po 6.D259 daje 43 i 42, bo doszły dwie zapadki bramki prozy, obie stojące "
        "wyłącznie jako prawa strona jednego porównania, więc obie PRZESĄDZONE "
        "kształtem; a po 6.D260 daje 45 i 44 z tego samego powodu, dwiema podlogami "
        "bramki lancuchow; a po 6.D261 daje 46 i 45, podloga bramki rodzin "
        "— różnica została ta sama; "
        "obie liczby są POCHODNE, więc rozjazd znaczy, że zmienił się rejestr albo "
        "kształt użycia, a nie że ktoś pomylił się w arytmetyce" % (wolnych, przesadzonych))


def test_kazda_zapadka_czesciowa_ma_ZMIERZONA_odleglosc_zaplonu():
    """**Klasa `czesciowa` jest jedyną, która twierdzi coś o ODLEGŁOŚCI — i nie mówi,
    o jakiej (6.D254).**

    Pomiar 17.09.2026 ruszył każdą z trzech aż do granicy zapłonu. Wszystkie trzy
    zachowały się zgodnie z klasą, ale odległości są nieporównywalne: 3 kroki przy
    wartości 10, 113 przy 120 i 6 przy 6, czyli cały legalny zakres. Ten sam przyrząd
    z krokiem proporcjonalnym daje więc dla tej jednej klasy DWA różne werdykty,
    zależnie od tego, jak duży krok ktoś wybierze — i dlatego odległość ma stać
    zapisana, a nie być domyślana.

    Bramka nie mierzy zachowania (mutacja nie mieści się w zestawie), tylko pilnuje,
    żeby żadna `czesciowa` nie została bez pomiaru i żeby nie dało się dopisać pomiaru
    dla zapadki, która `czesciowa` nie jest. Porównanie idzie W OBIE STRONY.
    """
    czesciowe = sorted(n for n, (k, _m) in ZAPADKI.items() if k == CZESCIOWA)

    bez_pomiaru = [n for n in czesciowe if n not in ODLEGLOSC_ZAPLONU_CZESCIOWYCH]
    assert bez_pomiaru == [], (
        "zapadka `czesciowa` bez zmierzonej odległości zapłonu: %s — klasa twierdzi, "
        "że „daleki ruch zapala\", więc dopóki nikt nie poda JAK daleki, twierdzenie "
        "jest niesprawdzalne" % bez_pomiaru)

    nie_czesciowe = sorted(n for n in ODLEGLOSC_ZAPLONU_CZESCIOWYCH if n not in czesciowe)
    assert nie_czesciowe == [], (
        "pomiar odległości zapłonu dla zapadki, która w rejestrze `czesciowa` nie jest: "
        "%s — dla pozostałych klas odległość nie znaczy nic" % nie_czesciowe)

    for nazwa, (wartosc, prog, _co) in sorted(ODLEGLOSC_ZAPLONU_CZESCIOWYCH.items()):
        assert 0 <= prog < wartosc, (
            "%s: zapłon przy %d, a wartość w drzewie %d — zapłon w granicach albo "
            "powyżej wartości znaczy, że zapadka jest CZERWONA już dziś albo że "
            "pomiar opisuje inną stałą" % (nazwa, prog, wartosc))

    odleglosci = {n: w - p for n, (w, p, _c) in ODLEGLOSC_ZAPLONU_CZESCIOWYCH.items()}
    assert min(odleglosci.values()) == 3 and max(odleglosci.values()) == 113, (
        "odległości zapłonu %s — pomiar 17.09.2026 dał od 3 do 113; rozjazd znaczy, "
        "że któraś zapadka albo jej strażnik się ruszyły i pomiar trzeba powtórzyć"
        % sorted(odleglosci.items()))


def test_czytnik_uzyc_widzi_ksztalt_ktory_ma_widziec():
    """Kontrola przyrządu na wejściu SYNTETYCZNYM — bez niej literówka we wzorcu
    dałaby zero „rozstrzygalnych" i zieleń, czyli stan NIEODRÓŻNIALNY od drzewa,
    w którym każda zapadka jest jednostronną podłogą (6.D27).

    Cztery role czytnika sprawdzone osobno, bo trzy z nich decydują o podziale:
    `komunikat` i `definicja` NIE liczą się jako użycie, `nosna` i `inna` liczą.
    """
    import tempfile
    zrodlo = (
        "MIN_JEDNA_PODLOGA = 5\n"
        "MIN_Z_KOMUNIKATEM = 5\n"
        "MIN_Z_DRUGIM_UZYCIEM = 5\n"
        "MAX_PRZEZ_MODUL = 5\n"
        "def t():\n"
        "    assert len(x) >= MIN_JEDNA_PODLOGA\n"
        "    assert len(x) >= MIN_Z_KOMUNIKATEM, 'próg %d' % MIN_Z_KOMUNIKATEM\n"
        "    assert len(x) >= MIN_Z_DRUGIM_UZYCIEM\n"
        "    y = range(MIN_Z_DRUGIM_UZYCIEM + 1)\n"
        "    assert len(y) <= inny.MAX_PRZEZ_MODUL\n"
    )
    with tempfile.TemporaryDirectory() as katalog:
        with open(os.path.join(katalog, "test_probka.py"), "w",
                  encoding="utf-8") as uchwyt:
            uchwyt.write(zrodlo)
        widziane = uzycia_zapadek(katalog, katalog)

    role = {n: sorted(r for _p, _l, r in gdzie) for n, gdzie in widziane.items()}
    assert role["MIN_JEDNA_PODLOGA"] == ["definicja", "nosna"], role
    assert role["MIN_Z_KOMUNIKATEM"] == ["definicja", "komunikat", "nosna"], (
        "nazwa w `Assert.msg` została policzona jako użycie nośne — a jest liczona "
        "WYŁĄCZNIE przy padzie i nie zależy od niej nic: %s" % role)
    assert role["MIN_Z_DRUGIM_UZYCIEM"] == ["definicja", "inna", "nosna"], role
    assert role["MAX_PRZEZ_MODUL"] == ["definicja", "nosna"], (
        "`moduł.NAZWA` nie został zobaczony — a to jest cały powód, dla którego ten "
        "czytnik istnieje obok `_porownania_zapadek`: %s" % role)


if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))
