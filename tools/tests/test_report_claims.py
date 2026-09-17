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
import ast
import datetime
import glob
import os
import re
import shutil
import subprocess
import sys
import tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tree_walk as TW  # noqa: E402

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
#: Zwężenie: między nazwą a liczbą nie wolno postawić **przecinka, strzałki, grawisu
#: ani znaku odsyłacza (`§`, `#`)**. Ten akapit jest przepisany, a nie dopisany obok
#: (6.D27): pierwsze zwężenie wycinało trzy pierwsze znaki i to wystarczało, dopóki
#: raporty nie zaczęły odsyłać do własnych sekcji.
#:
#: To wycina wyliczenia i tabele odwzorowań, a zostawia wszystkie cztery postacie,
#: w których raporty naprawdę podają wartość:
#:     `M7_WIDTH_M` 2,70                      — nazwa i liczba obok siebie
#:     `SLAB_GROWTH_STEPS` = 6                — ze znakiem równości
#:     `PARALLEL_M` jest granicą włącznie: 30,0 m
#:     Szerokość równa `RUNNING_TUNNEL_MAX_M` (15,0 m)
#: Zmierzone 06.09.2026: 12 trafień, 0 rozjazdów, 0 fałszywych alarmów.
#:
#: **Dlaczego doszły `§` i `#` (6.D27).** Bramka zapaliła się 07.09.2026 na zdaniu
#: POPRAWNYM: „Nie tknięto `SUITE_RUNTIME_BUDGET_S` — §4. Decyzja o czułości bramki."
#: — numer sekcji jest liczbą, a wzorzec bierze pierwszą liczbę po nazwie. Zmierzone
#: na dzisiejszych raportach: **3 twierdzenia z 82** miały ten kształt i przechodziły
#: WYŁĄCZNIE przypadkiem, bo żadna z tych trzech stałych nie trafia do słownika
#: wartości (jedna usunięta, jedna napisowa, jedna o dwóch wartościach). `#` doszło
#: z tego samego pomiaru, nie z przewidywania: `kolejka-uzupelnienie.md:42` pisze
#: „`MINIMUM_DOCUMENTED_ITEMS`: sprzężenie, które #274" i jest dziś przepuszczane
#: tylko dlatego, że stoi tam przecinek.
#:
#: Cena zwężenia, powiedziana wprost: zdanie „`STAŁA` (§4) to 30,0" przestaje być
#: twierdzeniem, więc rozjazd w nim byłby przemilczany. To jest ten sam wybór, który
#: podjęto przy przecinku i strzałce — bramka świecąca na poprawnym tekście zostaje
#: wyłączona, nie poprawiona, a przemilczane twierdzenie łapie `MINIMUM_CLAIMS`.
CLAIM = re.compile(
    r"`([A-Z][A-Z0-9_]{3,})`([^`,→§#\n]{0,40}?)(-?\d+(?:[.,]\d+)?(?:e-?\d+)?)")

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
        for base, _dirs, files in TW.walk(os.path.join(ROOT, where)):
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


def claims_in_reports(values, zrodla=None):
    """`(raport, wiersz, nazwa, liczba z raportu, wartość z kodu)` dla każdego trafienia.

    Bloki ogrodzone ``` są pomijane: to cytaty, nie twierdzenia.

    `zrodla` to pary `(nazwa, tekst)`; domyślnie cały `reports/`. Wejście syntetyczne
    jest tu treścią, a nie wygodą (6.D230): bez niego nie da się postawić obok siebie
    tego czytnika i `wystapienia_w_jednych_grawisach()` na JEDNYM dokumencie, a bez
    tego nie da się zmierzyć, że granica bloku kodu jest po obu stronach ta sama.
    """
    for name, tekst in (zrodla if zrodla is not None else _zrodla_raportow()):
        w_bloku = False
        for number, line in enumerate(tekst.splitlines(), 1):
            if FENCE.match(line):
                w_bloku = not w_bloku
                continue
            if w_bloku:
                continue
            for constant, _between, said in CLAIM.findall(line):
                if constant in values:
                    yield name, number, constant, said, values[constant]


# --- 6.D108: zdanie o wartości BIEŻĄCEJ a zdanie o wartości Z DNIA POMIARU ----------
#
# **Skąd ten blok.** Do 6.D108 każde trafienie wzorca było twierdzeniem o wartości
# bieżącej, więc podniesienie dowolnej zapadki zapalało bramkę na raportach, które
# opisywały stan swojego dnia — i poprawką było przepisywanie liczby słownie, czyli
# obchodzenie bramki zamiast rozstrzygania. Zdarzyło się to trzy razy w jednej sesji
# (10.09.2026): `207 → 208`, potem „stoi na 208", potem „stoi na 209".
#
# **Mechanizm wybrał właściciel 10.09.2026: data ostatniej zmiany STAŁEJ z gita**,
# razem z `fetch-depth: 0` w workflowach. Wariantów „data z nagłówka raportu"
# i „kierunek zapadki" nie realizuje nic — powody stoją w polu pozycji.
#
# **Rozstrzyga porządek dwóch dat**: raport jest zdaniem o dniu pomiaru wtedy i tylko
# wtedy, gdy stała zmieniła się PO tym, jak raport ostatnio tknięto. Raport tknięty
# w tym samym commicie co stała ma nieść wartość nową — i to jest dobrze, bo taki
# raport właśnie o niej pisze.
#
# **Drzewo robocze rozstrzyga przed gitem i to jest treść, nie optymalizacja.** Bramka
# chodzi PRZED commitem: gdyby patrzyła wyłącznie w historię, podniesienie zapadki
# w drzewie wyglądałoby jak brak zmiany i bramka zapalałaby się dokładnie tam, gdzie
# ta pozycja każe jej milczeć — a przepisanie liczby w raporcie na nieprawdziwą
# wyglądałoby jak brak zmiany raportu i przechodziłoby. Stała zmieniona w drzewie ma
# więc datę `TERAZ`, raport zmieniony w drzewie tak samo, a dwa `TERAZ` nie są
# uporządkowane — więc raport pisany dziś o zapadce podnoszonej dziś musi podać nową
# wartość. Obie strony mierzy kontrola negatywna.

#: Znacznik „zmienione w drzewie roboczym, jeszcze nie w historii". Późniejszy od
#: każdej daty z gita, więc porządkuje się razem z nimi bez gałęzi na `None`.
TERAZ = datetime.datetime.max.replace(tzinfo=datetime.timezone.utc)

#: Kształt definicji do przeszukania historii (`git log -G`). Wymaga liczby po znaku
#: równości, bo bez tego wzorzec łapałby każde przypisanie do tej nazwy — a data zbyt
#: świeża zwalnia twierdzenie z pilnowania, czyli myli się w stronę słabszej bramki.
DEFINICJA_W_HISTORII = r"\b%s\s*=\s*[-+0-9]"


def _git(*argumenty):
    wynik = subprocess.run(("git",) + argumenty, cwd=ROOT,
                           capture_output=True, text=True)
    return wynik.stdout.strip() if wynik.returncode == 0 else ""


def _data(iso):
    """Data z wypisu `git log --format=%cI`, ODPORNA na doklejone wiersze — 6.D250.

    **Bierze OSTATNI niepusty wiersz, a nie cały napis, i to jest treść tej funkcji.**
    `log.showSignature` w konfiguracji gita każe dokleić PRZED wypisem wynik weryfikacji
    podpisu (`No signature` na commicie niepodpisanym, wiersz `signature` na
    podpisanym), więc `--format=%cI` przestaje być jedyną treścią wyjścia.
    `fromisoformat` rzucał wtedy `ValueError`, a padały TRZY zastane bramki tego
    modułu — **na kodzie POPRAWNYM**. Zmierzone 16.09.2026 na tym repozytorium:
    TRZY bramki padają bez poprawki, zero z nią, przy tym samym `~/.gitconfig`
    (proporcja była 17/20 w dniu pomiaru i 18/21 po scaleniu #640 — dlatego stoi
    tu LICZBA PADAJĄCYCH, a nie ułamek: mianownik rusza każda cudza praca).

    Wywołania mają dodatkowo `--no-show-signature`, więc te wiersze zwykle w ogóle nie
    powstają. **Obie drogi są tu celowo, bo bronią przed czym innym:** flaga usuwa
    znany powód, a ta funkcja przeżywa KAŻDY doklejony wiersz — także taki, którego
    dziś nie znamy. Sama flaga nie wystarcza, bo dotyczy wywołań wymienionych z ręki
    i nowe wywołanie `git log` w tym module odtworzyłoby usterkę bez śladu.
    """
    if not iso:
        return None
    wiersze = [w for w in iso.splitlines() if w.strip()]
    return datetime.datetime.fromisoformat(wiersze[-1].strip()) if wiersze else None


_PAMIEC = {}

#: Skróty dla testów: pamięć podręczna i budowanie dat. Testy podstawiają tu wejście
#: syntetyczne, bo gałęzi „nie wiadomo" i „zmienione w drzewie" nie da się wykonać
#: na drzewie czystym o pełnej historii.
C_PAMIEC = _PAMIEC


def _dt(rok, miesiac, dzien):
    return datetime.datetime(rok, miesiac, dzien, tzinfo=datetime.timezone.utc)


def granice_plytkiego_klonu():
    """SHA commitów granicznych płytkiego klonu. Pusty zbiór przy klonie pełnym.

    **Po co (zmierzone 12.09.2026).** W tym kontenerze klon jest płytki — 252 commity
    od `b019436` z 07.09.2026 — i `git log -G` dla stałej nietkniętej w tym oknie
    wskazuje **commit graniczny**, nie tę zmianę, która naprawdę była ostatnia.
    Zmierzone na 28 stałych cytowanych dziś w raportach: **18 dostaje datę granicy**.
    Data z granicy nie jest odpowiedzią „kiedy się zmieniła", tylko „dalej nie widzę" —
    i przyrząd ma to powiedzieć, a nie podać ją jako datę. Stąd `fetch-depth: 0`
    w workflowach: w CI ta ślepota byłaby całkowita, bo domyślna głębokość to 1.
    """
    if "granice" not in _PAMIEC:
        katalog = _git("rev-parse", "--git-dir")
        sciezka = os.path.join(ROOT, katalog, "shallow") if katalog else ""
        granice = set()
        if sciezka and os.path.isfile(sciezka):
            with open(sciezka, encoding="utf-8") as uchwyt:
                granice = {w.strip() for w in uchwyt if w.strip()}
        _PAMIEC["granice"] = granice
    return _PAMIEC["granice"]


def _git_surowy(*argumenty):
    """To samo co `_git`, ale BEZ `.strip()` — wyjście bajt w bajt.

    **Osobna funkcja, a nie zmiana `_git`, i to jest treść, nie ostrożność.**
    `.strip()` w `_git` jest NOŚNE dla czterech pozostałych wywołań w tym module:
    `rev-parse --git-dir` sklejałby się z `\n` w ścieżkę nieistniejącą, a
    `_data(_git("log", "-1", "--format=%cI", ...))` dostawałby ISO z ogonkiem, na
    którym `datetime.fromisoformat` rzuca `ValueError`. Zamiana globalna naprawiłaby
    jedno wywołanie i zepsuła trzy.

    `--porcelain -z` jest tu jedynym formatem, w którym biały znak na BRZEGU wyjścia
    NIESIE ZNACZENIE: wiodąca spacja to kolumna indeksu w polu statusu `XY`.
    """
    wynik = subprocess.run(("git",) + argumenty, cwd=ROOT,
                           capture_output=True, text=True)
    return wynik.stdout if wynik.returncode == 0 else ""


def sciezki_ze_statusu(wypis):
    """`git status --porcelain -z` -> zbiór ścieżek. Funkcja CZYSTA, bez gita.

    **Dwa pola, nie jedno, przy zmianie nazwy.** W postaci `-z` wpis `R` albo `C`
    niesie ścieżkę nową we własnym polu, a ŹRÓDŁO w polu NASTĘPNYM — **bez kolumn
    `XY`**. Pętla, która tego pola nie konsumuje, bierze `alfa.txt` za wpis statusu
    i wkłada do zbioru jego `[3:]`, czyli `a.txt`: ciąg, którego w drzewie nie ma,
    a prawdziwego źródła nie wkłada wcale. Zmierzone 16.09.2026 na repozytorium
    próbnym: `git mv alfa.txt delta.txt` daje `R  delta.txt\0alfa.txt\0`.
    """
    pola = wypis.split("\0")
    sciezki = set()
    i = 0
    while i < len(pola):
        wpis = pola[i]
        i += 1
        if len(wpis) < 4:
            continue
        sciezki.add(wpis[3:])
        if wpis[0] in "RC" or wpis[1] in "RC":
            if i < len(pola):
                zrodlo = pola[i]
                i += 1
                if zrodlo:
                    sciezki.add(zrodlo)
    return sciezki


def zmienione_w_drzewie():
    """Ścieżki (względem `ROOT`) zmienione lub nieśledzone wobec HEAD.

    **`_git_surowy`, nie `_git`, i to jest cała usterka 6.D248.** `git status
    --porcelain -z` zaczyna wpis pliku NIEZAINDEKSOWANEGO od SPACJI (` M plik`),
    a `.strip()` na CAŁYM wyjściu zjada tę spację w **pierwszym** wpisie — po czym
    `[3:]` obcina pierwszy znak ścieżki. Zmierzone: przy jednym zmienionym pliku
    funkcja zwracała `{'ools/tests/test_all.py'}`.
    """
    if "zmienione" not in _PAMIEC:
        _PAMIEC["zmienione"] = sciezki_ze_statusu(
            _git_surowy("status", "--porcelain", "-z"))
    return _PAMIEC["zmienione"]


def pliki_definicji():
    """`{NAZWA: [ścieżki względne]}` — gdzie stała jest zdefiniowana."""
    if "gdzie" not in _PAMIEC:
        gdzie = {}
        for path in _source_files():
            wzgledna = os.path.relpath(path, ROOT)
            with open(path, encoding="utf-8", errors="ignore") as handle:
                for line in handle:
                    found = DEFINITION.match(line)
                    if found:
                        gdzie.setdefault(found.group(1), []).append(wzgledna)
        _PAMIEC["gdzie"] = gdzie
    return _PAMIEC["gdzie"]


def _wartosc_w_HEAD(nazwa):
    """Wartość stałej w ostatnim commicie albo `None`, gdy niejednoznaczna lub brak."""
    klucz = ("head", nazwa)
    if klucz not in _PAMIEC:
        widziane = set()
        for wzgledna in pliki_definicji().get(nazwa, ()):
            for line in _git("show", f"HEAD:{wzgledna}").splitlines():
                found = DEFINITION.match(line)
                if found and found.group(1) == nazwa:
                    widziane.add(found.group(2))
        _PAMIEC[klucz] = next(iter(widziane)) if len(widziane) == 1 else None
    return _PAMIEC[klucz]


def data_z_commita(wypis, granice):
    """`"<sha> <iso>"` → data albo `None`. Commit GRANICZNY daje `None`.

    Osobna funkcja, bo to jest jedyne miejsce, w którym „nie wiadomo" odróżnia się od
    „dawno" — a na drzewie o pełnej historii nie da się tego wykonać ani razu.
    Wejście jest tu więc syntetyczne z konieczności, nie z wygody: ta sama bramka ma
    działać tak samo w kontenerze z klonem płytkim i na runnerze z `fetch-depth: 0`.
    """
    if not wypis:
        return None
    # OSTATNI niepusty wiersz — z tego samego powodu co w `_data` (6.D250):
    # `log.showSignature` dokleja wiersze PRZED wypisem, a `sha` stoi w tym właściwym.
    wiersze = [w for w in wypis.splitlines() if w.strip()]
    if not wiersze or " " not in wiersze[-1]:
        return None
    sha, iso = wiersze[-1].strip().split(" ", 1)
    return None if sha in granice else _data(iso)


def data_stalej(nazwa, wartosc_w_drzewie):
    """Kiedy stała zmieniła się ostatnio. `TERAZ`, `datetime` albo `None` (nie wiadomo).

    `None` znaczy dokładnie „historia tego nie pokazuje" — klon płytki, commit
    graniczny albo stała bez definicji w drzewie. Nie znaczy „dawno".
    """
    pliki = pliki_definicji().get(nazwa, [])
    if not pliki:
        return None
    if any(p in zmienione_w_drzewie() for p in pliki) and \
            _wartosc_w_HEAD(nazwa) != wartosc_w_drzewie:
        return TERAZ
    klucz = ("data", nazwa)
    if klucz not in _PAMIEC:
        # **`--full-history`, i to jest cała usterka 6.D249.** Bez niej `git log`
        # UPRASZCZA HISTORIĘ: na commicie scalenia idzie tylko jedną gałęzią i commit,
        # który naprawdę zmienił stałą, przestaje być widoczny. Przebieg `pull_request`
        # stoi ZAWSZE na scalance (`Merge <gałąź> into <baza>`), więc datowanie
        # działało inaczej w CI niż lokalnie — a lokalnie nikt tego nie widział, bo
        # `git merge` gałęzi zawierającej bazę robi przewinięcie, nie scalenie.
        # Zmierzone 16.09.2026 na odtworzonej scalance `Merge fe41b7d into 135d323`:
        #     bez `--full-history`  -> 135d323 (commit, który wniósł RAPORT)
        #     z  `--full-history`   -> fe41b7d (commit, który zmienił STAŁĄ)
        # Skutek był taki, że stała dostawała datę CUDZEGO commitu — tego samego,
        # który wniósł cytujący ją raport — więc daty wychodziły równe co do sekundy
        # i twierdzenie raportu nie było zwalniane, choć zmieniło się po nim.
        # `--no-show-signature` — patrz `data_raportu` niżej, ten sam powód.
        wypis = _git("log", "-1", "--full-history", "--no-show-signature",
                     "--format=%H %cI",
                     "-G", DEFINICJA_W_HISTORII % re.escape(nazwa), "--", *pliki)
        _PAMIEC[klucz] = data_z_commita(wypis, granice_plytkiego_klonu())
    return _PAMIEC[klucz]


def data_raportu(nazwa_pliku):
    """Kiedy raport ostatnio tknięto. `TERAZ` dla zmienionego w drzewie roboczym."""
    wzgledna = os.path.join("reports", nazwa_pliku)
    if wzgledna in zmienione_w_drzewie():
        return TERAZ
    klucz = ("raport", nazwa_pliku)
    if klucz not in _PAMIEC:
        # **BEZ `--full-history`, inaczej niż w `data_stalej` wyżej — i ta asymetria
        # jest ZMIERZONA, nie przeoczona.** Tam pytamy, który commit ZMIENIŁ stałą,
        # a odpowiedzi szuka `-G` po DIFFACH, których scalenie domyślnie nie pokazuje.
        # Tutaj pytamy, kiedy raport ostatnio TKNIĘTO — a `--full-history` dorzuca tu
        # scalenia, które raport wyłącznie PRZENIOSŁY, i przesuwa jego datę w przód.
        # Zmierzone 16.09.2026 na odtworzonej scalance: z `--full-history` po obu
        # stronach data `6d241-…md` skacze na 14:44:31 i bramka zgłasza TRZY
        # twierdzenia tego raportu jako nieaktualne, choć zmieniły się przed nim.
        # **`--no-show-signature`, i to nie jest ozdoba — 6.D250.** `log.showSignature`
        # w CUDZYM `~/.gitconfig` każe gitowi dokleić przed wypisem wiersze weryfikacji
        # podpisu, więc `--format=%cI` przestaje być jedyną treścią wyjścia:
        #     'signature\n813f660c… 2026-09-02T21:47:55+00:00'
        # `datetime.fromisoformat` rzuca na tym `ValueError`, a padają wtedy TRZY
        # zastane bramki tego modułu — na kodzie POPRAWNYM. Jest to 6.D27 od strony
        # fałszywego alarmu: bramka melduje usterkę, której nie ma, i to komunikatem
        # nie do odróżnienia od prawdziwej. Zmierzone 16.09.2026: bez flagi TRZY czerwone,
        # z flagą 20/20, przy tym samym kodzie i tym samym `~/.gitconfig`.
        # Flaga jest tu ODPORNIEJSZA niż `-c log.showSignature=false`: dotyczy tego
        # jednego wywołania i nie zależy od tego, czy ustawienie przyszło z pliku
        # globalnego, lokalnego czy ze zmiennej środowiskowej.
        _PAMIEC[klucz] = _data(_git("log", "-1", "--no-show-signature",
                                    "--format=%cI", "--", wzgledna))
    return _PAMIEC[klucz]


def zdanie_z_dnia_pomiaru(nazwa_raportu, stala, wartosc_w_drzewie):
    """`(czy przedawnione, powód)`. Przedawnione = stała zmieniła się PO raporcie.

    Powód jest zwracany zawsze, także przy odpowiedzi przeczącej, bo komunikat bramki
    ma mówić, DLACZEGO twierdzenie jest pilnowane — inaczej czytający nie odróżni
    „raport jest świeży" od „nie dało się sprawdzić".
    """
    d_stalej = data_stalej(stala, wartosc_w_drzewie)
    d_raportu = data_raportu(nazwa_raportu)
    if d_stalej is None:
        return False, ("historia nie pokazuje, kiedy stała zmieniła się ostatnio "
                       "(klon płytki albo commit graniczny) — twierdzenie jest "
                       "pilnowane jak zdanie o wartości bieżącej")
    if d_raportu is None:
        return False, "raport nie ma daty w historii — twierdzenie jest pilnowane"
    if d_stalej > d_raportu:
        return True, f"stała zmieniła się po raporcie ({d_stalej} > {d_raportu})"
    return False, f"raport jest nie starszy od stałej ({d_raportu} >= {d_stalej})"

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
    datowane = 0
    for name, number, constant, said, actual in claims_in_reports(values):
        checked += 1
        if (name, constant) in CLAIM_EXCEPTIONS:
            continue
        przedawnione, powod = zdanie_z_dnia_pomiaru(name, constant, actual)
        if przedawnione:
            # 6.D108: stała zmieniła się PO tym raporcie, więc raport mówi o dniu
            # pomiaru, a nie o wartości bieżącej. Przepisywanie takiej liczby jest
            # zakazane przez 6.D3 i było dotąd obchodzone zapisem słownym.
            datowane += 1
            continue
        if not _same_number(said, actual):
            wrong.append(f"{name}:{number}: `{constant}` mówi {said}, kod {actual} "
                         f"[{powod}]")
    assert not wrong, f"raporty podają inną wartość niż kod: {wrong}"
    assert checked >= MINIMUM_CLAIMS, (
        f"wzorzec znalazł tylko {checked} twierdzeń przy progu {MINIMUM_CLAIMS} — "
        "przestał łapać, a zielona bramka na zerze trafień nic nie mierzy")
    assert checked - datowane >= MINIMUM_CLAIMS, (
        f"datowanie zwolniło z pilnowania {datowane} z {checked} twierdzeń, zostało "
        f"{checked - datowane} przy progu {MINIMUM_CLAIMS} — mechanizm z 6.D108 ma "
        "zwalniać zdania o dniu pomiaru, a nie wygaszać bramkę")


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
    # 8-9. ODSYŁACZE (6.D27): numer sekcji i numer PR nie są wartościami. Oba wzięte
    #      z prawdziwych zdań, nie wymyślone: pierwsze zapaliło bramkę 07.09.2026,
    #      drugie stoi w `kolejka-uzupelnienie.md:42` i przechodzi dziś tylko dlatego,
    #      że rozdziela je przecinek.
    assert found("Nie tknięto `SUITE_RUNTIME_BUDGET_S` — §4. Decyzja o czułości") == []
    assert found("złapał już raz `MINIMUM_DOCUMENTED_ITEMS`: sprzężenie które #274") == []
    # 10. Kontrola drugiej strony zwężenia: sama obecność `§` w wierszu nie może
    #     unieważniać twierdzenia stojącego PRZED nim.
    assert found("`M7_WIDTH_M` 2,70 — szerzej w §3") == [("M7_WIDTH_M", "2,70")]


def test_a_section_reference_next_to_a_constant_does_not_fail_the_gate():
    """6.D27, sprawdzone CAŁĄ bramką, nie samym wzorcem.

    Kontrola wzorca wyżej dowodzi, że `CLAIM` nie widzi odsyłacza. Nie dowodzi, że
    bramka na takim raporcie przechodzi — a to jest zdanie, które trzeba postawić,
    bo 07.09.2026 nie przeszła. Podmiana `REPORTS` na katalog tymczasowy, tak jak
    w teście bloków kodu, bo `claims_in_reports` czyta katalog, nie listę plików.
    """
    import tempfile

    def rozjazdy(tresc):
        with tempfile.TemporaryDirectory() as katalog:
            with open(os.path.join(katalog, "przyklad.md"), "w", encoding="utf-8") as u:
                u.write(tresc)
            globalny = REPORTS
            try:
                globals()["REPORTS"] = katalog
                return [(c, said, mowi) for _n, _w, c, said, mowi
                        in claims_in_reports({"PROG_TESTOWY_S": "150.0"})
                        if not _same_number(said, mowi)]
            finally:
                globals()["REPORTS"] = globalny

    # Zdanie POPRAWNE z odsyłaczem — dokładnie to, na którym bramka padła.
    assert rozjazdy("Nie tknieto `PROG_TESTOWY_S` — §4. Decyzja o czulosci bramki.\n") == [], (
        "poprawne zdanie z odsylaczem uznane za rozjazd")
    # To samo z odsyłaczem do PR.
    assert rozjazdy("`PROG_TESTOWY_S`: sprzezenie ktore #274 zamknelo.\n") == []

    # DRUGA STRONA, bez ktorej pierwsza nic nie znaczy: prawdziwy rozjazd nadal jest
    # rozjazdem, czyli zwezenie nie zjadlo tego, po co ta bramka istnieje.
    zle = rozjazdy("Stala `PROG_TESTOWY_S` to 4 i nic wiecej.\n")
    assert len(zle) == 1, ("zwezenie zjadlo prawdziwy rozjazd: " + repr(zle))
    # I zdanie prawdziwe o wlasciwej wartosci nie jest rozjazdem.
    assert rozjazdy("Stala `PROG_TESTOWY_S` to 150,0 sekundy.\n") == []


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

def test_zdanie_datowane_nie_jest_pilnowane_a_zdanie_biezace_jest():
    """Rdzeń 6.D108: rozstrzyga PORZĄDEK dwóch dat, a nie kształt zdania.

    Pomiar z `reports/6d108-ksztaltu-nie-ma.md` powiedział wprost, że kształtu nie ma:
    wszystkie dziewięć zdań datowanych wyglądało wtedy dokładnie tak, jak zdanie
    o wartości bieżącej — bo w dniu napisania nim BYŁY. Informacja rozstrzygająca leży
    poza zdaniem, więc bramka bierze ją z gita, a nie z tekstu.

    Wejście jest syntetyczne, bo na dzisiejszym drzewie przedawnionych zdań jest
    **zero** — a bramka, której nie da się wykonać na drzewie, zielenieje sama z siebie.
    """
    zastane = dict(C_PAMIEC)
    try:
        C_PAMIEC["gdzie"] = {"PROBNA_STALA": ["tools/tests/probny.py"]}
        C_PAMIEC["zmienione"] = set()
        C_PAMIEC[("data", "PROBNA_STALA")] = _dt(2026, 9, 11)
        C_PAMIEC[("raport", "probny.md")] = _dt(2026, 9, 10)
        przedawnione, powod = zdanie_z_dnia_pomiaru("probny.md", "PROBNA_STALA", "1")
        assert przedawnione, powod
        assert "po raporcie" in powod, powod

        C_PAMIEC[("raport", "probny.md")] = _dt(2026, 9, 12)
        przedawnione, powod = zdanie_z_dnia_pomiaru("probny.md", "PROBNA_STALA", "1")
        assert not przedawnione, powod
        assert "nie starszy" in powod, powod

        C_PAMIEC[("raport", "probny.md")] = _dt(2026, 9, 11)
        przedawnione, powod = zdanie_z_dnia_pomiaru("probny.md", "PROBNA_STALA", "1")
        assert not przedawnione, (
            "raport tknięty w tej samej chwili co stała ma nieść wartość NOWĄ — "
            f"to o niej właśnie pisze: {powod}")
    finally:
        C_PAMIEC.clear()
        C_PAMIEC.update(zastane)


def test_stala_podniesiona_W_DRZEWIE_zwalnia_stary_raport_jeszcze_przed_commitem():
    """Bez tego bramka zapalałaby się dokładnie tam, gdzie pozycja każe jej milczeć.

    Zapadkę podnosi się i uruchamia zestaw **przed** commitem. Gdyby data stałej szła
    wyłącznie z historii, świeżo podniesiona zapadka wyglądałaby jak nietknięta, więc
    raport sprzed tygodnia byłby pilnowany jak zdanie o wartości bieżącej — i jedynym
    wyjściem zostałoby przepisanie liczby słownie, czyli to, co ta pozycja usuwa.
    """
    zastane = dict(C_PAMIEC)
    try:
        C_PAMIEC["gdzie"] = {"PROBNA_STALA": ["tools/tests/probny.py"]}
        C_PAMIEC["zmienione"] = {"tools/tests/probny.py"}
        C_PAMIEC[("head", "PROBNA_STALA")] = "97"
        assert data_stalej("PROBNA_STALA", "98") is TERAZ, (
            "stała o innej wartości w drzewie niż w HEAD nie dostała daty TERAZ")
        assert data_stalej("PROBNA_STALA", "97") is not TERAZ, (
            "plik tknięty bez zmiany TEJ stałej nie może udawać jej zmiany — "
            "inaczej dowolna edycja pliku zwalniałaby wszystkie jego stałe")
    finally:
        C_PAMIEC.clear()
        C_PAMIEC.update(zastane)


def test_raport_tkniety_w_drzewie_jest_pilnowany_mimo_starej_stalej():
    """Druga połowa pola „Skończone, gdy": nieprawdziwa wartość NADAL zapala bramkę.

    Kierunek przeciwny do testu wyżej i dlatego stoi osobno. Mechanizm zwalniający
    zdania datowane byłby wart mniej niż nic, gdyby zwalniał też zdanie, które ktoś
    dopiero co wpisał — a wpisane dziś zdanie jest zawsze zdaniem o dziś.
    """
    zastane = dict(C_PAMIEC)
    try:
        C_PAMIEC["zmienione"] = {os.path.join("reports", "probny.md")}
        assert data_raportu("probny.md") is TERAZ, (
            "raport zmieniony w drzewie roboczym nie dostał daty TERAZ — twierdzenie "
            "wpisane przed chwilą byłoby porównywane z datą sprzed commita")
        C_PAMIEC["gdzie"] = {"PROBNA_STALA": ["tools/tests/probny.py"]}
        C_PAMIEC[("data", "PROBNA_STALA")] = _dt(2026, 9, 11)
        przedawnione, powod = zdanie_z_dnia_pomiaru("probny.md", "PROBNA_STALA", "1")
        assert not przedawnione, (
            "raport tknięty w drzewie roboczym został zwolniony z pilnowania — "
            f"wpisanie do niego nieprawdziwej liczby przeszłoby bez słowa: {powod}")
    finally:
        C_PAMIEC.clear()
        C_PAMIEC.update(zastane)


def test_status_porcelain_NIE_gubi_pierwszego_znaku_pierwszej_sciezki():
    """6.D248: `zmienione_w_drzewie()` na PRAWDZIWYM gicie, w repozytorium próbnym.

    **Przez `subprocess`, a nie przez samą `sciezki_ze_statusu`, i to jest treść tej
    bramki.** Usterka siedziała w `.strip()` **NAD** parserem — kontrola wołająca samą
    funkcję czystą byłaby zielona razem z nią. Bramka musi więc przejść tę samą drogę,
    którą chodzi moduł: `git status` -> odczyt -> rozbiór.

    **Konfiguracja LOKALNA repozytorium próbnego, a nie `git -c` przy wywołaniach
    bramki** — to jest odpowiedź na 6.D27 i wyszła z pomiaru, nie z przewidywania.
    `git status` woła tu kod PRODUKCYJNY (`_git_surowy`), do którego żadne `-c`
    podane przy `init`/`add` nie dociera. Konfiguracja lokalna bije globalną i czyta
    ją każde wywołanie gita w tym katalogu, także cudze.

    **Asercje stoją na ZBIORZE ścieżek, nie na literach statusu.** Dzięki temu
    `status.renames=false` — który zamienia `R` na parę `D`+`A`, czyli zmienia
    KSZTAŁT wyjścia, a nie jego treść — nie zapala bramki na kodzie poprawnym.
    """
    import tempfile
    with tempfile.TemporaryDirectory() as katalog:
        def git(*a):
            return subprocess.run(("git", "-C", katalog) + a,
                                  capture_output=True, text=True, check=True)
        git("init", "-q", ".")
        for klucz, wartosc in (("user.email", "t@example.invalid"),
                               ("user.name", "t"),
                               ("status.showUntrackedFiles", "all"),
                               ("status.renames", "true"),
                               ("core.quotePath", "false"),
                               ("core.excludesFile", os.devnull),
                               # **Te dwa piny NIE dotycza wypisu `status`, tylko tego,
                               # czy `git commit` w ogole sie UDA — i bez nich bramka
                               # pada na kodzie POPRAWNYM pod cudza konfiguracja.**
                               # Zmierzone 16.09.2026 (6.D248, poprawka po audycie):
                               # `HOME` z `commit.gpgsign = true` i podpisywaczem,
                               # ktorego nie ma, dawal `20/21` i `git commit` konczacy
                               # sie kodem **128** — bramka meldowala usterke, ktorej
                               # nie ma. To nie jest przypadek teoretyczny: `gpgsign`
                               # stoi w `/root/.gitconfig` tego kontenera na `true`,
                               # a bramka przechodzila WYLACZNIE dlatego, ze binarka
                               # podpisujaca przypadkiem istniala. `core.hooksPath`
                               # jest z tej samej rodziny: cudzy `pre-commit`, ktory
                               # konczy sie bledem, zatrzymuje `commit` tak samo.
                               # Reszta pinow mowi o TRESCI wypisu, te dwa o tym,
                               # czy jest co wypisywac.
                               ("commit.gpgsign", "false"),
                               ("core.hooksPath", os.devnull)):
            git("config", klucz, wartosc)
        for nazwa in ("alfa.txt", "beta.txt", "gamma.txt"):
            with open(os.path.join(katalog, nazwa), "w", encoding="utf-8") as u:
                u.write("x\n")
        git("add", "-A")
        git("commit", "-q", "-m", "x")

        # **`zmienione_w_drzewie()` NAPRAWDĘ, z podmienionym `ROOT`, a nie
        # `sciezki_ze_statusu` na cudzym wypisie — i to jest poprawka z KN-1.**
        # Pierwsza wersja tej bramki wołała `git status` własnym podprocesem
        # i podawała wynik parserowi. Zmierzone: przywrócenie `.strip()`
        # w `_git_surowy` dawało przy niej **21/21 NA ZIELONO** — bramka pisana
        # na tę usterkę nie obejmowała jej ani trochę, bo usterka siedzi
        # w ODCZYCIE, a tamta droga odczyt omijała. Po tej zmianie ta sama
        # mutacja daje 20/21. Podmiana `ROOT` idzie tym samym idiomem, co
        # istniejąca w tym module podmiana `REPORTS`.
        def widziane():
            global ROOT
            stary_root, stara_pamiec = ROOT, dict(_PAMIEC)
            ROOT = katalog
            try:
                _PAMIEC.pop("zmienione", None)
                return set(zmienione_w_drzewie())
            finally:
                ROOT = stary_root
                _PAMIEC.clear()
                _PAMIEC.update(stara_pamiec)

        # Czyste repozytorium — zbiór pusty. Bez tego każda asercja niżej byłaby
        # spełniona także przez parser zwracający wszystko, co popadnie.
        assert widziane() == set(), (
            "czyste repozytorium dało niepusty zbiór: %s" % sorted(widziane()))

        # JEDEN plik niezaindeksowany — dokładnie przypadek usterki: wiodąca spacja
        # w pierwszym (i jedynym) wpisie.
        with open(os.path.join(katalog, "alfa.txt"), "a", encoding="utf-8") as u:
            u.write("zmiana\n")
        assert widziane() == {"alfa.txt"}, (
            "pierwsza ścieżka wyszła z parsera obcięta albo zgubiona: %s — "
            "`git status --porcelain -z` zaczyna wpis pliku NIEZAINDEKSOWANEGO "
            "od SPACJI, więc `.strip()` na całym wyjściu przesuwa ją o znak"
            % sorted(widziane()))

        # TRZY naraz — usterka psuła zawsze dokładnie pierwszy wpis, więc przypadek
        # jednoplikowy sam nie odróżnia „obcina pierwszy" od „obcina każdy".
        with open(os.path.join(katalog, "beta.txt"), "a", encoding="utf-8") as u:
            u.write("zmiana\n")
        with open(os.path.join(katalog, "z spacja w nazwie.txt"), "w",
                  encoding="utf-8") as u:
            u.write("x\n")
        assert widziane() == {"alfa.txt", "beta.txt", "z spacja w nazwie.txt"}, (
            "zbiór przy trzech wpisach (w tym ścieżce ze spacją i pliku "
            "nieśledzonym) się nie zgadza: %s" % sorted(widziane()))

        # ZMIANA NAZWY — źródło ORAZ cel. Pole źródłowe stoi w osobnym kawałku BEZ
        # kolumn `XY`; pętla, która go nie konsumuje, wkłada do zbioru jego `[3:]`.
        git("add", "-A")
        git("commit", "-q", "-m", "y")
        git("mv", "gamma.txt", "delta.txt")
        widzi = widziane()
        assert "gamma.txt" in widzi and "delta.txt" in widzi, (
            "zmiana nazwy: brak źródła albo brak celu w zbiorze: %s" % sorted(widzi))
        assert "ma.txt" not in widzi and "mma.txt" not in widzi, (
            "w zbiorze stoi śmieć z POLA ŹRÓDŁOWEGO, obcięty o trzy znaki: %s — "
            "pole źródłowe wpisu `R` nie jest wpisem statusu i nie wolno go ciąć"
            % sorted(widzi))

        # Zmiana ZAINDEKSOWANA nie ma wiodącej spacji, więc usterka jej nie dotykała
        # — i właśnie dlatego stoi tu osobno: bez niej bramka nie odróżnia „naprawione"
        # od „nigdy nie było zepsute dla tego kształtu".
        with open(os.path.join(katalog, "alfa.txt"), "a", encoding="utf-8") as u:
            u.write("kolejna\n")
        git("add", "alfa.txt")
        assert "alfa.txt" in widziane(), (
            "zmiana ZAINDEKSOWANA wypadła ze zbioru: %s" % sorted(widziane()))

def test_datowanie_PRZEZYWA_wiersze_doklejone_przed_wypisem_loga():
    """6.D250: `log.showSignature` psuł TRZY zastane bramki na kodzie POPRAWNYM.

    **Skąd.** `log.showSignature = true` w konfiguracji gita każe dokleić przed
    wypisem wynik weryfikacji podpisu, więc `--format=%cI` przestaje być jedyną
    treścią wyjścia i `fromisoformat` rzuca `ValueError`. Zmierzone 16.09.2026 na tym
    repozytorium: **trzy bramki czerwone** bez poprawki, **zero** z nią, ten sam kod i ten sam
    `~/.gitconfig`. Jest to 6.D27 od strony FAŁSZYWEGO ALARMU — bramka meldowała
    usterkę, której nie ma, komunikatem nieodróżnialnym od prawdziwej awarii.

    **Wejście jest SYNTETYCZNE i to jest wybór z pomiaru, nie wygoda.** Pierwsza
    wersja tej bramki budowała repozytorium próbne z `log.showSignature=true`.
    Kontrola negatywna ją obaliła: zdjęcie `--no-show-signature` z `data_raportu`
    dawało przy niej **21/21 NA ZIELONO**. Powód zmierzony — git dokleja te wiersze
    tylko wtedy, gdy commit jest PODPISANY albo gdy `gpg.format` wskazuje backend,
    który zgłasza błąd; commity repozytorium próbnego są niepodpisane, więc fixture
    nie odtwarzał niczego. **To zostaje prawdą — ale zdanie, które tu stało po niej,
    było FAŁSZYWE i jest PRZEPISANE, a nie dopisane obok (16.09.2026).** Stało:
    „bramka wierna wymagałaby kluczy podpisujących w środowisku przebiegu". Nie
    wymagałaby, i jest to zmierzone: commit z nagłówkiem `gpgsig` składa się z ręki
    przez `git hash-object -t commit -w --stdin`, a podpis może być UDAWANY, bo git
    dokleja wiersze o podpisie **niezależnie od wyniku weryfikacji**. Bramka wierna
    stoi więc niżej w tym module (`test_KAZDE_wywolanie_git_log_daje_TEN_SAM_wypis…`)
    i żadnych kluczy nie potrzebuje. Zdanie zostało obalone, bo zaczęłoby odstraszać
    od bramek behawioralnych w miejscach, gdzie są wykonalne — a to jest koszt
    większy niż jedna bramka.

    Ta bramka mierzy mimo to **zachowanie PARSERA**, i to nadal jest właściwy
    przedmiot: parser ma być odporny na wielowierszowy wypis niezależnie od tego,
    czy flaga gdziekolwiek stoi. Obie połowy poprawki mają dziś własną bramkę.
    """
    assert _data("2026-09-16T14:00:00+00:00") == datetime.datetime(
        2026, 9, 16, 14, 0, tzinfo=datetime.timezone.utc), (
        "`_data` przestała czytać zwykły wypis jednowierszowy — wtedy asercje niżej "
        "są zielone nad czytnikiem, który nie czyta niczego")
    for doklejka in ("No signature\n",
                     "signature\n813f660cf19451eac69941aecae84b33d4cfd5e7\n",
                     "gpg: Signature made Wed 16 Sep 2026\ngpg: Good signature\n"):
        assert _data(doklejka + "2026-09-16T14:00:00+00:00") == datetime.datetime(
            2026, 9, 16, 14, 0, tzinfo=datetime.timezone.utc), (
            "`_data` nie przeżyła wierszy doklejonych przed wypisem (%r) — "
            "`log.showSignature` w cudzej konfiguracji wywraca przez to bramki "
            "tego modułu na kodzie POPRAWNYM" % doklejka)
    assert data_z_commita(
        "No signature\n813f660c 2026-09-16T14:00:00+00:00", frozenset()) == \
        datetime.datetime(2026, 9, 16, 14, 0, tzinfo=datetime.timezone.utc), (
        "`data_z_commita` nie przeżyła doklejki — bierze `sha` z pierwszego wiersza "
        "zamiast z tego, który niesie format")
    # Druga strona: commit GRANICZNY ma nadal dawać `None`, także z doklejką.
    assert data_z_commita("No signature\n813f660c 2026-09-16T14:00:00+00:00",
                          frozenset({"813f660c"})) is None, (
        "doklejka zasłoniła rozpoznanie commitu GRANICZNEGO — `None` znaczy "
        "„nie wiadomo” i nie wolno go zgubić")


def _repo_z_PODPISANYM_commitem(baza):
    """Repozytorium próbne z commitem niosącym nagłówek `gpgsig` — bez ani jednej binarki.

    **Commit powstaje przez `git hash-object -t commit -w`, a nie przez `git commit`,
    i to jest wybór z pomiaru.** `git commit` na maszynie z `commit.gpgsign = true`
    w cudzym `~/.gitconfig` woła program podpisujący; gdy tego programu nie ma, kończy
    kodem **128**, a bramka melduje usterkę, której nie ma. Obiekt commitu składany
    z ręki nie woła niczego i wychodzi tak samo na każdej maszynie. Piny
    `commit.gpgsign=false` i `core.hooksPath=os.devnull` stoją tu mimo to, bo
    `git add` i `git write-tree` wykonuje się w cudzym środowisku, a pin kosztuje
    jedno wywołanie.

    Podpis jest UDAWANY (`AAAA`) i to wystarcza: git ogląda ramkę armor, próbuje
    zweryfikować i **niezależnie od wyniku** dokleja wiersz do wypisu. Weryfikacja
    udana nie jest do niczego potrzebna — potrzebna jest doklejka.
    """
    repo = os.path.join(baza, "repo")
    os.makedirs(repo)

    def g(*a, **kw):
        return subprocess.run(("git",) + a, cwd=repo, capture_output=True, text=True, **kw)

    g("init", "-q", "-b", "glowna", ".")
    for klucz, wartosc in (("user.name", "Probny"),
                           ("user.email", "probny@example.invalid"),
                           ("commit.gpgsign", "false"),
                           ("core.hooksPath", os.devnull)):
        g("config", klucz, wartosc)
    with open(os.path.join(repo, "a.txt"), "w") as plik:
        plik.write("a\n")
    g("add", "-A")
    drzewo = g("write-tree").stdout.strip()
    podpis = "-----BEGIN SSH SIGNATURE-----\nAAAA\n-----END SSH SIGNATURE-----"
    tresc = ("tree %s\n"
             "author Probny <probny@example.invalid> 1789000000 +0000\n"
             "committer Probny <probny@example.invalid> 1789000000 +0000\n"
             "gpgsig %s\n\nprobny\n" % (drzewo, podpis.replace("\n", "\n ")))
    sha = subprocess.run(["git", "hash-object", "-t", "commit", "-w", "--stdin"],
                         cwd=repo, input=tresc, capture_output=True, text=True).stdout.strip()
    g("update-ref", "HEAD", sha)
    return repo


def _srodowisko(baza, nazwa, tresc_gitconfig):
    """`HOME` (i XDG) odsunięte na własny katalog z podaną konfiguracją gita.

    Dwa takie środowiska — jedno z `log.showSignature = true`, drugie z konfiguracją
    PUSTĄ — są całą miarą tej bramki: wywołanie zgodne z regułą daje w obu ten sam
    wypis, wywołanie bez flagi daje inny.
    """
    dom = os.path.join(baza, nazwa)
    os.makedirs(dom)
    with open(os.path.join(dom, ".gitconfig"), "w") as plik:
        plik.write(tresc_gitconfig)
    srodowisko = dict(os.environ)
    srodowisko["HOME"] = dom
    # XDG odsunięty razem z HOME, żeby cudzy `~/.config/git/config` nie wchodził
    # do pomiaru trzecią drogą.
    srodowisko["XDG_CONFIG_HOME"] = os.path.join(dom, ".config")
    srodowisko.pop("GIT_CONFIG_GLOBAL", None)
    return srodowisko


def _wywolania_git_log(zrodlo):
    """`[(wiersz, argv)]` — wszystkie wywołania `git log` w module, czytane z AST.

    Znajdowanie jest STATYCZNE, a sprawdzenie BEHAWIORALNE, i ten podział jest tu
    treścią. Statyczne znajdowanie łapie także wywołanie DOPISANE jutro — czyli tę
    samą klasę, o której mówi docstring `_data`. Gdyby zamiast tego szpiegować
    `_git` w trakcie przebiegu, bramka widziałaby tylko te wywołania, które akurat
    wykonały się na dzisiejszym drzewie.
    """
    znalezione = []
    for wezel in ast.walk(ast.parse(zrodlo)):
        if not isinstance(wezel, ast.Call):
            continue
        if isinstance(wezel.func, ast.Name) and wezel.func.id == "_git":
            argv = [a.value for a in wezel.args
                    if isinstance(a, ast.Constant) and isinstance(a.value, str)]
        elif isinstance(wezel.func, ast.Attribute) and wezel.func.attr == "run" \
                and wezel.args and isinstance(wezel.args[0], (ast.List, ast.Tuple)):
            argv = [e.value for e in wezel.args[0].elts
                    if isinstance(e, ast.Constant) and isinstance(e.value, str)]
            if argv[:1] == ["git"]:
                argv = argv[1:]
        else:
            continue
        if argv[:1] == ["log"]:
            znalezione.append((wezel.lineno, argv))
    return znalezione


def _same_przelaczniki_ksztaltu(argv):
    """Argumenty WYBIERAJĄCE commit odcięte, zostają te, które rządzą WYPISEM.

    Odcięte są: pathspec (wszystko za `--`) i `-G <wzorzec>`. Commit do wypisania
    daje repozytorium próbne, a bramka mierzy KSZTAŁT wypisu — nie to, który commit
    wyszedł.
    """
    zostaje, i = [], 0
    while i < len(argv):
        if argv[i] == "--":
            break
        if argv[i] == "-G":
            i += 2
            continue
        zostaje.append(argv[i])
        i += 1
    return zostaje


def test_KAZDE_wywolanie_git_log_daje_TEN_SAM_wypis_pod_cudza_konfiguracja():
    """6.D250, połowa DRUGA: `--no-show-signature` na wywołaniach — bramka BEHAWIORALNA.

    **Czego pilnuje.** Poprawka 6.D250 ma dwie połowy: flagę na wywołaniach `git log`
    i parser biorący OSTATNI niepusty wiersz. Bramkę miała tylko druga.
    Zmierzone 16.09.2026 na gałęzi `claude/6d250-podpis-w-wypisie-loga`: zdjęcie
    `--no-show-signature` z OBU wywołań zostawia moduł na **21/21, kod 0**, także pod
    `HOME` z `log.showSignature = true`. Połowa (a) nie była więc pilnowana niczym —
    parser ją zasłaniał. Parser jest obroną DRUGĄ i ma nią pozostać; ta bramka pilnuje
    PIERWSZEJ, żeby obie były naprawdę dwie.

    **Mierzoną własnością jest RÓWNOŚĆ WYPISÓW, a nie liczba wierszy, i to jest
    poprawka z pomiaru 6.D27.** Pierwsza wersja tej bramki żądała DOKŁADNIE jednego
    niepustego wiersza. Zapalała się wtedy na kodzie POPRAWNYM — zmierzone na dwóch
    kształtach: wywołanie z `--format=%H%n%cI` (dwa pola, dwa wiersze, flaga na
    miejscu) dawało `21/22`, tak samo wywołanie, którego format przyszedł ze stałej
    modułu, więc AST nie widział go w argumentach i git wypisywał nagłówek domyślny
    (4 wiersze). Oba są poprawne i oba bramka meldowała jako usterkę. Równość wypisów
    nie zna żadnego z tych kształtów: obchodzi ją wyłącznie to, czy cudza konfiguracja
    ZMIENIA wynik.

    **Dlaczego to mierzy zachowanie, a nie napis.** Bramka nie szuka w źródle nazwy
    flagi. Bierze argumenty każdego wywołania `git log` z AST, uruchamia je **prawdziwym
    gitem** na repozytorium próbnym z commitem PODPISANYM — raz pod konfiguracją
    z `log.showSignature = true`, raz pod pustą — i porównuje wypisy. Zamiana flagi na
    `-c log.showSignature=false` albo na cokolwiek innego o tym samym skutku przejdzie
    tę bramkę, i tak ma być: pilnowany jest skutek.

    **Kontrola potencji fixture'u jest częścią bramki, nie jej przygotowaniem.**
    Zmierzone: repozytorium próbne z commitem NIEPODPISANYM daje ten sam wypis pod obiema
    konfiguracjami — czyli fixture, który nie odtwarza niczego, a bramka nad nim jest
    zielona zawsze. Pierwsza wersja bramki 6.D250 padła dokładnie na tym. Dlatego każde
    wywołanie jest puszczane także z ODJĘTĄ flagą: gdy wersja odjęta przestanie dawać
    różnicę, bramka mówi, że straciła zdolność widzenia — zamiast przejść po cichu.
    """
    zrodlo = open(os.path.abspath(__file__), encoding="utf-8").read()
    wywolania = _wywolania_git_log(zrodlo)
    assert len(wywolania) >= 2, (
        "AST znalazło %d wywołań `git log` w tym module, a datowanie stoi na dwóch "
        "(`data_stalej`, `data_raportu`) — bramka nad zerem wywołań byłaby zielona "
        "zawsze" % len(wywolania))

    baza = tempfile.mkdtemp(prefix="6d250-podpis-")
    try:
        repo = _repo_z_PODPISANYM_commitem(baza)
        cudza = _srodowisko(baza, "dom-cudzy", "[log]\n\tshowSignature = true\n")
        pusta = _srodowisko(baza, "dom-pusty", "")

        def wypis(argumenty, srodowisko):
            return subprocess.run(["git"] + argumenty, cwd=repo, capture_output=True,
                                  text=True, env=srodowisko).stdout

        for wiersz, argv in wywolania:
            ksztalt = _same_przelaczniki_ksztaltu(argv)
            odjeta = [a for a in ksztalt if a != "--no-show-signature"]
            assert wypis(odjeta, cudza) != wypis(odjeta, pusta), (
                "fixture przestał odtwarzać usterkę 6.D250: wywołanie z wiersza %d "
                "z odjętą flagą daje ten sam wypis pod obiema konfiguracjami. Dopóki to "
                "nie wróci, asercja niżej jest zielona nad niczym" % wiersz)
            pod_cudza, pod_pusta = wypis(ksztalt, cudza), wypis(ksztalt, pusta)
            assert pod_cudza == pod_pusta, (
                "wywołanie `git log` z wiersza %d wypisuje pod cudzą konfiguracją co "
                "innego niż pod pustą:\n  cudza: %r\n  pusta: %r\n"
                "Doklejone wiersze weryfikacji podpisu wywracały przez to TRZY zastane "
                "bramki tego modułu na kodzie POPRAWNYM (6.D250). Parser bierze ostatni "
                "wiersz i to zasłania skutek, ale obrona pierwsza ma działać sama"
                % (wiersz, pod_cudza, pod_pusta))
    finally:
        shutil.rmtree(baza, ignore_errors=True)

def test_commit_GRANICZNY_nie_jest_data_tylko_koncem_widzenia():
    """„Nie wiadomo" ma być odróżnione od „dawno" — inaczej to 6.D27 w czystej postaci.

    Zmierzone 12.09.2026 w kontenerze tej sesji: klon jest płytki (252 commity od
    `b019436`), a `git log -G` dla stałej nietkniętej w tym oknie wskazuje **commit
    graniczny**. Na 28 stałych cytowanych wtedy w raportach **18** dostawało w ten
    sposób datę, która nie jest datą ich ostatniej zmiany, tylko datą, za którą nic
    nie widać. Stąd `fetch-depth: 0` w workflowach: w CI domyślna głębokość to 1,
    więc ślepota byłaby zupełna.

    Wejście syntetyczne, bo na klonie pełnym tej gałęzi nie da się wykonać ani razu.
    """
    granice = {"b019436f608f3836a6c3ad0d2261815e5c1ed96f"}
    assert data_z_commita("b019436f608f3836a6c3ad0d2261815e5c1ed96f 2026-09-07T16:20:56+02:00",
                          granice) is None, "commit graniczny podał się za datę zmiany"
    zwykly = data_z_commita("745814efdc0f1c11edea0de47b7d5b0c4c6e44ac "
                            "2026-09-12T04:00:00+00:00", granice)
    assert zwykly is not None and zwykly.year == 2026, zwykly
    assert data_z_commita("", granice) is None, (
        "pusty wypis `git log` znaczy „historia tego nie pokazuje”, a nie datę")
    assert data_z_commita("bezspacji", granice) is None, (
        "wypis bez spacji nie jest parą `sha data` — czytelnik ma odmówić, nie zgadywać")


def test_kazde_twierdzenie_dostaje_POWOD_takze_gdy_jest_pilnowane():
    """Komunikat ma mówić, DLACZEGO twierdzenie jest pilnowane.

    Bez tego czytający nie odróżni „raport jest świeższy od stałej" od „historia tego
    nie pokazuje" — a to są dwie różne rzeczy i druga znaczy, że bramka odpowiada
    z mniejszą wiedzą, niż się wydaje.
    """
    values = constant_values()
    bez_powodu = []
    for name, _number, constant, _said, actual in claims_in_reports(values):
        _przedawnione, powod = zdanie_z_dnia_pomiaru(name, constant, actual)
        if not powod or not powod.strip():
            bez_powodu.append(f"{name}: {constant}")
    assert not bez_powodu, bez_powodu


def test_wszystkie_workflowy_biora_PELNA_historie():
    """`fetch-depth: 0` jest połową tej pozycji, nie szczegółem wdrożenia.

    `actions/checkout` bez tego wejścia daje głębokość **1**, więc `git log -G` nie ma
    czego przeszukać i KAŻDA stała wygląda na zmienioną w jedynym widocznym commicie.
    Mechanizm datowania odpowiadałby wtedy w CI, nie sprawdziwszy niczego — rodzina
    6.D27. Decyzja właściciela z 10.09.2026 obejmuje oba kroki naraz.

    Bramka stoi TUTAJ, a nie tylko w `test_ci_workflows.py`, bo to ten moduł na tym
    stoi: kto zdejmie `fetch-depth`, ma zobaczyć nazwę przyrządu, który przez to oślepł.
    """
    import yaml
    braki = []
    for sciezka in sorted(glob.glob(os.path.join(ROOT, ".github", "workflows", "*.yml"))):
        with open(sciezka, encoding="utf-8") as uchwyt:
            dokument = yaml.safe_load(uchwyt)
        for job, cialo in (dokument.get("jobs") or {}).items():
            for krok in cialo.get("steps") or []:
                if "actions/checkout" not in (krok.get("uses") or ""):
                    continue
                glebokosc = (krok.get("with") or {}).get("fetch-depth")
                if glebokosc != 0:
                    braki.append(f"{os.path.basename(sciezka)}:{job}: "
                                 f"fetch-depth={glebokosc!r}")
    assert not braki, (
        "checkout bez `fetch-depth: 0` — datowanie twierdzeń z 6.D108 oślepnie w CI, "
        f"bo domyślna głębokość to 1: {braki}")


# --- 6.D251: BRAMKA NA UPRASZCZANIE HISTORII — PRAWDZIWA SCALANKA JAKO WEJSCIE ------
#
# **Skad ta bramka.** 6.D249 zapalilo `main` na czerwono: `data_stalej` wolala
# `git log -1 -G<definicja> -- <pliki>` BEZ `--full-history`, a `git log` z pathspec
# UPRASZCZA HISTORIE — na commicie scalenia TREESAME wobec pierwszego rodzica idzie
# wylacznie tym rodzicem, wiec commit z galezi, ktory stala naprawde zmienil, jest
# niewidoczny i stala dostaje date CUDZEGO commitu: tego, ktory wniosl cytujacy ja
# raport. Przebieg `pull_request` stoi ZAWSZE na scalance, wiec datowanie odpowiadalo
# w CI inaczej niz lokalnie. Poprawka weszla bez bramki, bo `main` plonal; ta pozycja
# ja dostawia.
#
# **Wejsciem jest PRAWDZIWE repozytorium z PRAWDZIWYM `git merge --no-ff`**, a nie
# podstawiona pamiec podreczna, i wolana jest PRAWDZIWA `data_stalej`. Podstawienie
# `_PAMIEC[("data", …)]` opisywaloby odpowiedz, ktorej ta bramka ma dowodzic, a kontrola
# na funkcji czystej byla by zielona RAZEM z usterka: caly mechanizm siedzi w argumentach
# `git log`, a nie w tym, co z jego wypisem robi Python.
#
# **Ksztalt scalanki jest TRESCIA, nie dekoracja — i to jest ZMIERZONE.** „Oczywista"
# topologia (galaz zmienia stala, `main` jej nie rusza) usterki NIE POKAZUJE: scalanka
# nie jest wtedy TREESAME wobec pierwszego rodzica, upraszczanie idzie w strone galezi
# i obie wersje `git log` odpowiadaja TAK SAMO. Zmierzone 16.09.2026 na obu repo
# probnych z tego bloku:
#
#     scalanka TREESAME       bez `--full-history` -> commit RAPORTU  (09-02)
#                             z  `--full-history` -> commit STALEJ   (09-04)
#     scalanka NIE-TREESAME   obie wersje         -> commit STALEJ   (09-04)
#
# Dlatego commit galezi przepisuje stala na wartosc, KTORA `main` JUZ MA — drzewo
# scalanki jest wtedy identyczne z drzewem pierwszego rodzica. Testy nizej pilnuja obu
# polowek: ze scalanka TREESAME wersje odroznia, i ze NIE-TREESAME ich nie odroznia.
# Bez tej drugiej polowki nastepny czytajacy uproscilby fixture do topologii oczywistej
# i dostal bramke zielona na usterce.
#
# **Asymetria `--full-history` jest pilnowana Z OBU STRON.** `data_stalej` pyta, ktory
# commit ZMIENIL stala, a odpowiedzi szuka `-G` po diffach, ktorych uproszczona historia
# nie pokazuje. `data_raportu` pyta, kiedy raport TKNIETO — i tam `--full-history`
# dorzuca scalenia, ktore raport wylacznie PRZENIOSLY, przesuwajac jego date w przod.
# Na tej samej scalance: bez `--full-history` raport ma date 09-02 (swojego commitu),
# z `--full-history` — 09-05 (scalenia). Obie usterki dzialaja w te sama strone: zdanie
# datowane przestaje byc zwalniane i bramka zapala sie na raporcie POPRAWNYM.

#: Daty commitow repozytorium probnego. Rozne co do DOBY i to jest treść: `data_stalej`
#: zwraca date, nie SHA, wiec wylacznie po niej da sie powiedziec, KTORY commit funkcja
#: wskazala. Dwa commity o tej samej dacie bylyby nieodroznialne, a bramka mowilaby
#: wtedy „zwrocila jakas date" zamiast „zwrocila ten commit".
DATA_KORZENIA = "2026-09-01T10:00:00+00:00"
DATA_COMMITU_RAPORTU = "2026-09-02T10:00:00+00:00"
DATA_COMMITU_STALEJ = "2026-09-04T10:00:00+00:00"
DATA_SCALENIA = "2026-09-05T10:00:00+00:00"


def _repozytorium_ze_scaleniem(katalog, main_podnosi_stala):
    """Repo gita z PRAWDZIWYM `git merge --no-ff`. Zwraca SHA scalanki.

    `main_podnosi_stala=True` daje scalanke TREESAME wobec pierwszego rodzica — ksztalt,
    na ktorym usterka 6.D249 jest widoczna. `False` daje topologie „oczywista", na
    ktorej nie jest. Ksztalt jest sprawdzany porownaniem DRZEW, a nie zakladany.
    """
    import subprocess

    def git(*argumenty, kiedy=None):
        srodowisko = dict(os.environ)
        if kiedy:
            srodowisko["GIT_AUTHOR_DATE"] = kiedy
            srodowisko["GIT_COMMITTER_DATE"] = kiedy
        wynik = subprocess.run(("git",) + argumenty, cwd=katalog, env=srodowisko,
                               capture_output=True, text=True)
        assert wynik.returncode == 0, (
            "repozytorium probne nie powstalo: git %s -> %d\n%s\n%s"
            % (" ".join(argumenty), wynik.returncode, wynik.stdout, wynik.stderr))
        return wynik.stdout.strip()

    def zapisz(wzgledna, tresc):
        pelna = os.path.join(katalog, wzgledna)
        os.makedirs(os.path.dirname(pelna), exist_ok=True)
        with open(pelna, "w", encoding="utf-8") as uchwyt:
            uchwyt.write(tresc)

    git("init", "-q", "-b", "main")
    # 6.D27: konfiguracja gita WLASCICIELA nie moze rozstrzygac o wyniku bramki, a `-c`
    # podane przez bramke NIE dociera do kodu produkcyjnego — `data_stalej` wola `_git`,
    # ktory sklada wlasne argv. Przypiete jest wiec LOKALNIE w repozytorium probnym:
    # tam, i tylko tam, siega `cwd=ROOT` z `_git`. `log.showSignature` wywracalo juz
    # trzy bramki na kodzie POPRAWNYM (6.D250), bo dokleja do wypisu `git log` wiersze,
    # ktorych zaden z tych parserow sie nie spodziewa.
    for klucz, wartosc in (("user.email", "probne@example.invalid"),
                           ("user.name", "probne"),
                           ("commit.gpgsign", "false"),
                           ("tag.gpgsign", "false"),
                           ("log.showSignature", "false"),
                           # 6.D251, ZMIERZONE: `merge.verifySignatures = true` w konfiguracji
                           # globalnej wywraca `git merge --no-ff` kodem 128 („does not have
                           # a GPG signature") i te trzy testy padają na KODZIE POPRAWNYM.
                           # Pin na `commit.gpgsign` tego NIE załatwia: tamten dotyczy
                           # PISANIA podpisu, ten — SPRAWDZANIA cudzego przy scalaniu.
                           ("merge.verifySignatures", "false"),
                           ("merge.ff", "false"),
                           ("status.showUntrackedFiles", "normal"),
                           ("gc.auto", "0"),
                           # `os.devnull` zamiast nieistniejącego katalogu w `katalog`:
                           # tamten fixture sam zapisuje pliki pod `katalog`, więc ścieżka
                           # „na pewno pustego katalogu" jest założeniem, a `/dev/null`
                           # katalogiem nie będzie nigdy.
                           ("core.hooksPath", os.devnull)):
        git("config", "--local", klucz, wartosc)

    zapisz("tools/stale.py", "PROG_PROBNY = 1\n")
    git("add", "-A")
    git("commit", "-qm", "korzen", kiedy=DATA_KORZENIA)
    git("branch", "galaz")

    # `main`: commit, ktory wnosi RAPORT. Przy ksztalcie TREESAME podnosi przy okazji
    # stala — bo wlasnie o to chodzi: galaz przepisze ja potem na wartosc, KTORA `main`
    # JUZ MA, i drzewo scalanki wyjdzie identyczne z drzewem tego commitu.
    if main_podnosi_stala:
        zapisz("tools/stale.py", "PROG_PROBNY = 2\n")
    zapisz("reports/probny.md", "Stala `PROG_PROBNY` to 1 w dniu pomiaru.\n")
    git("add", "-A")
    git("commit", "-qm", "raport", kiedy=DATA_COMMITU_RAPORTU)

    # Galaz: commit, ktory STALA ZMIENIL. To jego ma wskazac `data_stalej`.
    git("checkout", "-q", "galaz")
    zapisz("tools/stale.py", "PROG_PROBNY = 2\n")
    git("add", "-A")
    git("commit", "-qm", "stala", kiedy=DATA_COMMITU_STALEJ)

    git("checkout", "-q", "main")
    git("merge", "--no-ff", "-q", "-m", "Merge galaz into main", "galaz",
        kiedy=DATA_SCALENIA)

    drzewo_scalanki = git("rev-parse", "HEAD^{tree}")
    drzewo_rodzica = git("rev-parse", "HEAD^1^{tree}")
    assert (drzewo_scalanki == drzewo_rodzica) is main_podnosi_stala, (
        "ksztalt scalanki wyszedl inny, niz fixture zamawial: TREESAME wobec pierwszego "
        "rodzica=%s przy zamowieniu %s — a to OD NIEGO zalezy, czy usterka jest w ogole "
        "widoczna" % (drzewo_scalanki == drzewo_rodzica, main_podnosi_stala))
    return git("rev-parse", "HEAD")


#: Flagi, ktore WYLACZAJA upraszczanie historii. Rodzina, nie jedna flaga, i to jest
#: ZMIERZONE (6.D27, 16.09.2026): `--simplify-merges` sama z siebie IMPLIKUJE pelna
#: historie, wiec przy zapisie `--full-history --simplify-merges` — rownowaznym,
#: dajacym te sama poprawna odpowiedz 09-04 — odjecie samego `--full-history` usterki
#: NIE odtwarza i ten test zapala sie na KODZIE POPRAWNYM komunikatem „fixture przestal
#: odwzorowywac usterke". Odejmowana jest wiec cala rodzina.
BEZ_UPRASZCZANIA = ("--full-history", "--simplify-merges", "--sparse", "--dense")


def _bez_full_history(prawdziwy):
    """`_git` z odjeta rodzina `BEZ_UPRASZCZANIA` — usterka 6.D249 na zywym kodzie."""
    return lambda *a: prawdziwy(*[x for x in a if x not in BEZ_UPRASZCZANIA])


def _z_full_history(prawdziwy):
    """`_git` z DOLOZONYM `--full-history` — druga strona asymetrii."""
    def opakowany(*a):
        if a and a[0] == "log" and "--full-history" not in a:
            a = (a[0], "--full-history") + a[1:]
        return prawdziwy(*a)
    return opakowany


def _na_repozytorium_probnym(katalog):
    """Podstawia `ROOT` i czysci `_PAMIEC` — idiom tego modulu, tylko z `ROOT` w komplecie.

    `data_stalej` i `data_raportu` wolaja gita z `cwd=ROOT`, wiec samo podstawienie
    pamieci podrecznej nie wystarcza: to wlasnie wypis gita jest tu mierzony.
    """
    globals()["ROOT"] = katalog
    _PAMIEC.clear()
    _PAMIEC["gdzie"] = {"PROG_PROBNY": [os.path.join("tools", "stale.py")]}
    _PAMIEC["zmienione"] = set()
    _PAMIEC["granice"] = set()


def test_datowanie_stalej_na_SCALANCE_wskazuje_commit_KTORY_STALA_ZMIENIL():
    """6.D249 na prawdziwej scalance: `--full-history` w `data_stalej` jest OBOWIAZKOWE.

    Wejscie: repo z `git merge --no-ff`, scalanka TREESAME wobec pierwszego rodzica.
    Stala zmienil commit galezi (09-04); raport wniosl commit `main` (09-02).

    Druga polowa testu odtwarza usterke na ZYWYM kodzie — odejmuje `--full-history`
    z argumentow gita i sprawdza, ze odpowiedz przeskakuje na commit RAPORTU. Bez niej
    fixture moglby z czasem zgnic w taki, na ktorym obie wersje odpowiadaja tak samo,
    a bramka byla by zielona nie wiadomo z czego.
    """
    import tempfile

    zastany_root, zastana_pamiec, zastany_git = ROOT, dict(_PAMIEC), _git
    try:
        with tempfile.TemporaryDirectory() as katalog:
            _repozytorium_ze_scaleniem(katalog, main_podnosi_stala=True)
            _na_repozytorium_probnym(katalog)

            assert data_stalej("PROG_PROBNY", "2") == _data(DATA_COMMITU_STALEJ), (
                "`data_stalej` na scalance wskazala %s zamiast commitu, ktory stala "
                "ZMIENIL (%s) — `git log` z pathspec uproscil historie i poszedl samym "
                "pierwszym rodzicem" % (data_stalej("PROG_PROBNY", "2"),
                                        _data(DATA_COMMITU_STALEJ)))

            # Zdanie raportu o wartosci 1 ma byc ZWOLNIONE: stala zmieniła się PO nim.
            przedawnione, powod = zdanie_z_dnia_pomiaru("probny.md", "PROG_PROBNY", "2")
            assert przedawnione, (
                "twierdzenie raportu nie zostalo zwolnione, choc stala zmienila sie po "
                "nim — to jest dokladnie ten skutek, ktory zapalil `main`: %s" % powod)

            # DRUGA STRONA: usterka odtworzona na zywym kodzie.
            _na_repozytorium_probnym(katalog)
            globals()["_git"] = _bez_full_history(zastany_git)
            zle = data_stalej("PROG_PROBNY", "2")
            globals()["_git"] = zastany_git
            assert zle == _data(DATA_COMMITU_RAPORTU), (
                "bez `--full-history` odpowiedz NIE przeskoczyla na commit raportu (%s) "
                "— fixture przestal odwzorowywac usterke 6.D249" % zle)

            _PAMIEC.pop(("raport", "probny.md"), None)
            globals()["_git"] = _bez_full_history(zastany_git)
            przedawnione_zle, _p = zdanie_z_dnia_pomiaru("probny.md", "PROG_PROBNY", "2")
            globals()["_git"] = zastany_git
            assert not przedawnione_zle, (
                "usterka odtworzona, a twierdzenie mimo to zwolnione — wtedy ten test "
                "nie mierzy tego, co opisuje")
    finally:
        globals()["ROOT"] = zastany_root
        globals()["_git"] = zastany_git
        _PAMIEC.clear()
        _PAMIEC.update(zastana_pamiec)


def test_datowanie_RAPORTU_na_scalance_nie_liczy_scalenia_ktore_raport_PRZENIOSLO():
    """Druga strona asymetrii: w `data_raportu` `--full-history` PSUJE.

    Ta sama scalanka, to samo repo. `data_raportu` ma odpowiedziec data commitu, ktory
    raport wniosl (09-02), a nie data scalenia, ktore raport wylacznie PRZENIOSLO
    (09-05). Bez tego testu ktos „naprawilby" asymetrie symetria — dolozyl
    `--full-history` po obu stronach — i bramka zaczela by zapalac sie na raportach
    poprawnych, bo kazdy z nich datowalby sie ostatnim scaleniem, ktore go dotknelo.
    """
    import tempfile

    zastany_root, zastana_pamiec, zastany_git = ROOT, dict(_PAMIEC), _git
    try:
        with tempfile.TemporaryDirectory() as katalog:
            _repozytorium_ze_scaleniem(katalog, main_podnosi_stala=True)
            _na_repozytorium_probnym(katalog)

            assert data_raportu("probny.md") == _data(DATA_COMMITU_RAPORTU), (
                "`data_raportu` wskazala %s zamiast commitu, ktory raport wniosl (%s)"
                % (data_raportu("probny.md"), _data(DATA_COMMITU_RAPORTU)))

            _na_repozytorium_probnym(katalog)
            globals()["_git"] = _z_full_history(zastany_git)
            zle = data_raportu("probny.md")
            globals()["_git"] = zastany_git
            assert zle == _data(DATA_SCALENIA), (
                "z `--full-history` data raportu NIE przeskoczyla na scalenie (%s) — "
                "wtedy asymetria opisana w `data_raportu` przestaje byc prawda" % zle)
            assert zle > _data(DATA_COMMITU_STALEJ), (
                "scalenie ma byc PO zmianie stalej — inaczej ta usterka nie zabieralaby "
                "zwolnienia zadnemu twierdzeniu i test nie mowilby o niczym")
    finally:
        globals()["ROOT"] = zastany_root
        globals()["_git"] = zastany_git
        _PAMIEC.clear()
        _PAMIEC.update(zastana_pamiec)


def test_scalanka_NIE_TREESAME_usterki_NIE_POKAZUJE_i_dlatego_fixture_jest_taki():
    """Dlaczego fixture wyzej ma ksztalt, ktory ma — zmierzone, nie zalozone.

    Topologia „oczywista" (galaz zmienia stala, `main` jej nie rusza) daje scalanke
    NIE-TREESAME wobec pierwszego rodzica: upraszczanie idzie wtedy w strone galezi
    i obie wersje `git log` — z `--full-history` i bez — odpowiadaja TAK SAMO.
    Bramka zbudowana na tym ksztalcie byla by zielona razem z usterka 6.D249.
    """
    import tempfile

    zastany_root, zastana_pamiec, zastany_git = ROOT, dict(_PAMIEC), _git
    try:
        with tempfile.TemporaryDirectory() as katalog:
            _repozytorium_ze_scaleniem(katalog, main_podnosi_stala=False)

            _na_repozytorium_probnym(katalog)
            z_poprawka = data_stalej("PROG_PROBNY", "2")

            _na_repozytorium_probnym(katalog)
            globals()["_git"] = _bez_full_history(zastany_git)
            z_usterka = data_stalej("PROG_PROBNY", "2")
            globals()["_git"] = zastany_git

            assert z_poprawka == _data(DATA_COMMITU_STALEJ), z_poprawka
            assert z_usterka == z_poprawka, (
                "na scalance NIE-TREESAME wersje jednak sie roznia (%s vs %s) — wtedy "
                "powod, dla ktorego fixture wyzej ma ksztalt TREESAME, przestal byc "
                "prawda i ten blok trzeba przeliczyc" % (z_usterka, z_poprawka))
    finally:
        globals()["ROOT"] = zastany_root
        globals()["_git"] = zastany_git
        _PAMIEC.clear()
        _PAMIEC.update(zastana_pamiec)


# --- 6.D209: KSZTALT `NAZWA = N` W `reports/` — POSZERZYC CZY ZAPISAC GRANICE --------
#
# **ODPOWIEDZ: NIE poszerzac, i sa to CZTERY trafienia falszywe przy ZERZE prawdziwych.**
#
# `CLAIM` wyzej rozpoznaje twierdzenie w ksztalcie ``` `NAZWA` ``` … liczba i zakazuje
# grawisa w przerwie — zwezenie swiadome, zeby tabele odwzorowan nie dawaly falszywych
# trafien. Ksztalt ``` `NAZWA = N` ```, w ktorym nazwa i liczba stoja w JEDNEJ parze
# grawisow, jest dla niego niewidzialny. Pozycja 6.D209 pytala, ilu twierdzen to dotyczy
# i czy wzorzec ma je obejmowac.
#
# Zmierzone 14.09.2026 na `b941625`, przyrzadem tego modulu (`constant_values`,
# `zdanie_z_dnia_pomiaru`) i wzorcem `test_backlog.CLAIM_W_JEDNYCH_GRAWISACH` —
# jednym, WSPOLNYM, zeby drugi wzorzec nie zaczal zyc wlasnym zyciem:
#
#     wystapien ksztaltu w `reports/`                      51  (13.09 bylo 41)
#     z nazwa, ktora drzewo zna                            45  (13.09 bylo 35)
#     roznych nazw wsrod wystapien                         42
#     ROZJECHANYCH z drzewem                               15
#     z nich ZWOLNIONYCH przez datowanie (6.D108)          11
#     z nich TWARDYCH — raport nie starszy od stalej        4
#
# **Wszystkie CZTERY twarde sa CYTATAMI, nie twierdzeniami autora**, i widac to dopiero
# w zdaniu obok liczby:
#
#   * `6d156…:16` — „Odtwarza `NIEROZSTRZYGNIETYCH = 72` dokladnie, wiec mierzy to, co
#     bramka": wartosc WEJSCIOWA sondy z dnia raportu, nie stan drzewa;
#   * `odsylacz-nie-jest-wartoscia.md:121` — „Czytajacy mial prawo przeczytac ja jako
#     `MINIMUM_CLAIMS = 15`": cytat BLEDNEGO odczytu, opisany jako bledny;
#   * `rozstep-budzetu-kroku.md:127` — „Przyrzad czytal `KOD_NIEMIERZALNY = 1`, gdy
#     w pliku stalo `3`": cytat odczytu PRZYRZADU, ktory raport zglasza jako usterke;
#   * `sciezki-w-polach-blokow.md:128` — „z zapadka podniesiona razem z wpisem
#     (`MAX_EXCEPTIONS = 2`)": opis nastawy KONTROLI NEGATYWNEJ.
#
# **Datowanie tych czterech NIE ZWALNIA i to jest osobne znalezisko.** Dla dwoch raport
# i stala maja TEN SAM commit (raport i zapadka weszly razem), dla dwoch raport jest
# nowszy od stalej. Mechanizm z 6.D108 odsiewa zdania, ktore zestarzaly sie w czasie —
# a te nie zestarzaly sie wcale, tylko nigdy nie byly zdaniami o stanie drzewa.
#
# **ROZSTRZYGNIECIE: `CLAIM` zostaje taki, jaki jest.** Poszerzenie dalo by dzis
# 4 czerwienie na tekscie poprawnym i 0 na usterce — czyli bramke, ktora 6.D27 kaze
# wylaczyc, a nie poprawiac. Granica jest zapisana tutaj, razem z liczbami i z czterema
# nazwanymi przypadkami, ktore ja rozstrzygnely.

#: Podloga na liczbe wystapien ksztaltu `NAZWA = N` w `reports/`. PODLOGA, nie rownosc:
#: raportow przybywa. Broni przed wzorcem, ktory zgnil i odpowiada zerem tak samo, jak
#: wzorzec dzialajacy (6.D27). Zmierzone 14.09.2026: 51; 16.09.2026 (6.D230): 58 przy
#: dawnej granicy i 55 przy dzisiejszej, bo trzy wystapienia stoja w blokach kodu.
#: Zapadka zostaje WOLNA i zostaje na 40: 6.D230 obnizylo populacje o 3, a nie podnioslo
#: podlogi — podniesienie jej do 55 zamienialoby ja w rownosc na katalogu, ktory rosnie.
MIN_WYSTAPIEN_W_JEDNYCH_GRAWISACH = 40

#: Cztery twarde rozjazdy, WSZYSTKIE bedace cytatami. Zbior, nie liczba (6.D131): to on
#: niesie werdykt „4 trafienia falszywe, 0 prawdziwych", a czworka jest jego dlugoscia.
#: Wpis piaty znaczy, ze ktos napisal w raporcie twierdzenie tego ksztaltu rozjechane
#: z drzewem — i wtedy rozstrzygniecie 6.D209 trzeba przeliczyc, bo przestaje byc prawda,
#: ze prawdziwych trafien nie ma.
#: Raport, ktory OPISUJE te cztery przypadki, a przez to je CYTUJE — i staje sie ich
#: piatym, szostym, siodmym i osmym wystapieniem. Wylaczony z populacji, bo inaczej
#: pomiar mierzylby wlasny zapis: bramka zapalila sie na nim przy pierwszym przebiegu
#: po dopisaniu raportu (2477/2481, cztery nowe pary).
#:
#: **Wylaczenie jest WASKIE i przybite z dwoch stron:** dotyczy jednego pliku, a bramka
#: nizej zada, zeby ten plik NAPRAWDE cytowal wszystkie cztery nazwy — wiec amnestia
#: nie obejmuje twierdzenia, ktore ktos w tym raporcie napisalby o czyms innym.
#: Ta sama rodzina co `_moduly_do_pomiaru` z 6.D203: liczba, ktora da sie zmienic
#: zdaniem o niej samej, nie jest pomiarem drzewa.
RAPORT_SAMOZWROTNY = "6d209-cztery-cytaty-i-ani-jednego-twierdzenia.md"

CYTATY_NIE_TWIERDZENIA = {
    ("6d156-zawezenie-szczelne-i-odrzucone.md", "NIEROZSTRZYGNIETYCH"),
    ("odsylacz-nie-jest-wartoscia.md", "MINIMUM_CLAIMS"),
    ("rozstep-budzetu-kroku.md", "KOD_NIEMIERZALNY"),
    ("sciezki-w-polach-blokow.md", "MAX_EXCEPTIONS"),
}


#: **GRANICA BLOKU KODU JEST TA SAMA PO OBU STRONACH — 6.D230.**
#:
#: Do 16.09.2026 ten czytnik czytal `reports/` petla po WSZYSTKICH wierszach, a
#: `claims_in_reports()` bloki ogrodzone pomijal. Ten sam katalog, dwie granice, i nikt
#: tego nie zapisal — autor cytujacy cudze twierdzenie musial wiedziec, ktorym z dwoch
#: ksztaltow go zapisac. 6.D219 tej wiedzy uzylo: wypisalo cytat BEZ grawisow i nazwalo
#: to „wyborem, nie niechlujstwem". To jest zmiana tekstu pod bramke, czyli to, co
#: 6.D108 nazwalo obchodzeniem zamiast rozstrzygania.
#:
#: **Ujednolicone W STRONE POMIJANIA i to jest pomiar, nie domysl.** Pole pozycji
#: ostrzegalo, ze pominiecie blokow zdejmuje spod pomiaru ksztalt, na ktorym 6.D209
#: oparlo werdykt. Zmierzone 16.09.2026 na `e420f14`: wystapien ksztaltu `NAZWA = N`
#: w `reports/` jest 58, z czego W BLOKACH KODU stoja 3 — wszystkie trzy w jednym
#: raporcie (`6d196-…:61,73,74`), a WSZYSTKIE CZTERY wystapienia, na ktorych stoi
#: `CYTATY_NIE_TWIERDZENIA`, oraz wszystkie cztery ich cytaty w `RAPORT_SAMOZWROTNY`
#: stoja POZA blokami. Ostrzezenie nie potwierdzilo sie: baza dowodowa 6.D209 nie
#: traci ani jednego wystapienia, a wylaczenie samozwrotne zostaje nosne.
#:
#: **Powod jest ten sam, ktory stoi przy `FENCE`, i tu tez jest zmierzony.** Trojka
#: z blokow to raz przyklad dydaktyczny („<- CLAIM nie widzi"), a dwa razy CYTAT
#: WYJSCIA wlasnej bramki — z liczbami, ktore byly prawdziwe w dniu raportu i sa
#: dzis nieprawdziwe (19 przy 24, 10 przy 9). Dzis zwalnia je datowanie, ale zwalnia
#: je WARUNKOWO: `data_raportu` liczy sie od ostatniego ruszenia PLIKU, wiec poprawka
#: literowki gdziekolwiek w tym raporcie przedatowuje go na dzis i obie pary staja
#: sie TWARDE. Zmierzone kontrola negatywna KN-5: bramka czerwienieje po edycji
#: KOSMETYCZNEJ raportu — czyli na tekscie poprawnym (6.D27).
def _wystapienia_w_tekscie(tekst, pomijaj_bloki):
    """`[(wiersz, nazwa, liczba)]` — ksztalt `NAZWA = N` w JEDNYM dokumencie.

    Wzorzec jest POZYCZONY z `test_backlog`, a nie przepisany: dwie kopie tego samego
    wyrazenia rozjechalyby sie przy pierwszej poprawce, a ta bramka i tamta maja mowic
    o tym samym ksztalcie.
    """
    import test_backlog as BL

    out = []
    w_bloku = False
    for numer, wiersz in enumerate(tekst.split("\n"), 1):
        if pomijaj_bloki:
            if FENCE.match(wiersz):
                w_bloku = not w_bloku
                continue
            if w_bloku:
                continue
        for nazwa, liczba in BL.CLAIM_W_JEDNYCH_GRAWISACH.findall(wiersz):
            out.append((numer, nazwa, liczba))
    return out


def wystapienia_w_jednych_grawisach(zrodla=None, pomijaj_bloki=True):
    """`[(raport, wiersz, nazwa, liczba)]` — ksztalt `NAZWA = N` we wszystkich raportach.

    `pomijaj_bloki` stoi w sygnaturze NIE jako nastawa do wybierania, tylko zeby
    kontrola negatywna KN-1 mogla postawic dawna granice obok dzisiejszej bez
    przepisywania funkcji. Wolanie produkcyjne nie podaje jej nigdy.
    """
    out = []
    for plik, tekst in (zrodla if zrodla is not None else _zrodla_raportow()):
        for numer, nazwa, liczba in _wystapienia_w_tekscie(tekst, pomijaj_bloki):
            out.append((plik, numer, nazwa, liczba))
    return out


def rozjazdy_w_jednych_grawisach():
    """`{(raport, nazwa)}` — WSZYSTKIE rozjechane z drzewem, bez pytania o datowanie.

    **Datowanie jest tu CELOWO pominięte i to jest poprawka z pomiaru, nie uproszczenie.**
    Pierwsza wersja tej funkcji odsiewała przez `zdanie_z_dnia_pomiaru` — i zbiór
    zmienił się z czterech par na trzy **przez commit, który nie tknął ani jednej
    liczby**: `data_stalej` datuje stałą commitem, który ostatnio ruszył jej plik, więc
    dopisanie tej bramki do `test_report_claims.py` przedatowało `MINIMUM_CLAIMS`
    na dziś i datowanie zaczęło je zwalniać. Zbiór przypięty na takim warunku
    rozjeżdżałby się przy każdej edycji modułu, w którym stoi pilnowana stała.

    Rozjazd z drzewem tej wady nie ma: nie zależy od tego, kto i kiedy ruszył plik.
    """
    import test_backlog as BL

    wartosci = constant_values()
    out = set()
    for plik, _numer, nazwa, liczba in wystapienia_w_jednych_grawisach():
        if plik == RAPORT_SAMOZWROTNY:
            continue
        if nazwa not in wartosci:
            continue
        if not BL._rowne(liczba, wartosci[nazwa]):
            out.add((plik, nazwa))
    return out


def twarde_rozjazdy_w_jednych_grawisach():
    """`{(raport, nazwa)}` — rozjechane i NIE zwolnione przez datowanie.

    Liczba, którą ta funkcja zwraca, jest **ruchoma** z powodu opisanego wyżej; stoi
    w bramce jako obserwacja, a nie jako przypięcie.
    """
    wartosci = constant_values()
    return {(plik, nazwa) for plik, nazwa in rozjazdy_w_jednych_grawisach()
            if not zdanie_z_dnia_pomiaru(plik, nazwa, wartosci[nazwa])[0]}


def test_ksztalt_w_jednych_grawisach_daje_SAME_CYTATY():
    """Werdykt 6.D209 w jednej asercji: 4 trafienia falszywe, 0 prawdziwych.

    Poszerzenie `CLAIM` na ten ksztalt dalo by dzis cztery czerwienie na tekscie
    poprawnym — bo wszystkie cztery twarde rozjazdy sa CYTATAMI: wartoscia wejsciowa
    sondy, cytatem bledu, odczytem przyrzadu i nastawa kontroli negatywnej. Bramka
    swiecaca na poprawnym tekscie zostaje wylaczona, nie poprawiona (6.D27).
    """
    wystapienia = wystapienia_w_jednych_grawisach()
    assert len(wystapienia) >= MIN_WYSTAPIEN_W_JEDNYCH_GRAWISACH, (
        "wystapien ksztaltu `NAZWA = N` w `reports/` jest %d przy podlodze %d — wzorzec "
        "zgnil albo katalog sie skurczyl, a zero odpowiada tak samo, jak wzorzec "
        "dzialajacy" % (len(wystapienia), MIN_WYSTAPIEN_W_JEDNYCH_GRAWISACH))

    # **BRAMKA PYTA O WERDYKT, NIE O CZLONKOSTWO — i to jest poprawka z dwoch pomiarow.**
    # Przypiecie zbioru TWARDYCH rozjazdow (rozjechane minus zwolnione datowaniem)
    # rozjechalo sie z czterech par na trzy przez commit, ktory nie tknal ani jednej
    # liczby: `data_stalej` datuje stala commitem, ktory ostatnio ruszyl jej PLIK.
    # Przypiecie zbioru WSZYSTKICH rozjechanych dalo z kolei 13 par, bo rosnie przy
    # kazdym podniesieniu zapadki po raporcie, ktory ja cytowal — czyli przy pracy
    # poprawnej. Trwale jest dopiero zdanie, ktore ta pozycja rozstrzygnela:
    #
    #     kazdy rozjazd jest ALBO zwolniony datowaniem, ALBO jednym z czterech cytatow
    #
    # Nowy rozjazd, ktorego datowanie nie zwalnia, zapala te bramke; przedatowanie
    # ktoregokolwiek z czworki nie zapala niczego, bo przenosi ja do pierwszego czlonu.
    rozjechane = rozjazdy_w_jednych_grawisach()
    twarde = twarde_rozjazdy_w_jednych_grawisach()
    poza_lista = twarde - CYTATY_NIE_TWIERDZENIA
    assert not poza_lista, (
        "rozjazd ksztaltu `NAZWA = N`, ktorego datowanie NIE zwalnia i ktorego nie ma "
        "na liscie cytatow: %s — jesli to twierdzenie autora o stanie drzewa, werdykt "
        "6.D209 („cztery trafienia falszywe, zero prawdziwych\") przestal byc prawdziwy"
        % sorted(poza_lista))
    assert CYTATY_NIE_TWIERDZENIA <= rozjechane, (
        "wpis z listy cytatow przestal byc rozjechany z drzewem: %s — wtedy opisuje "
        "rozjazd, ktorego nie ma" % sorted(CYTATY_NIE_TWIERDZENIA - rozjechane))

    # I DRUGA STRONA: kazdy wymieniony ma NAPRAWDE byc rozjechany i NAPRAWDE nie byc
    # zwolniony przez datowanie. Bez tego „same cytaty" byloby prawda takze o zbiorze
    # wpisow, ktorych zadna z tych dwoch wlasnosci nie dotyczy. Licznik obrotow, bo
    # pusta petla przechodzi kazda regule w srodku (6.D27).
    import test_backlog as BL

    wartosci = constant_values()
    sprawdzonych = 0
    for plik, nazwa in sorted(CYTATY_NIE_TWIERDZENIA):
        assert nazwa in wartosci, (
            "`%s` nie jest juz stala jednoznaczna w drzewie — wpis opisuje rozjazd, "
            "ktorego nie da sie policzyc" % nazwa)
        liczby = [l for p, _n, n2, l in wystapienia if p == plik and n2 == nazwa]
        assert liczby, (
            "w `%s` nie ma juz ani jednego wystapienia `%s = N`" % (plik, nazwa))
        assert all(not BL._rowne(l, wartosci[nazwa]) for l in liczby), (
            "`%s` w `%s` zgadza sie dzis z drzewem — wpis opisuje rozjazd, ktorego nie "
            "ma" % (nazwa, plik))
        assert (plik, nazwa) in rozjechane, (plik, nazwa)
        sprawdzonych += 1
    assert sprawdzonych == len(CYTATY_NIE_TWIERDZENIA), sprawdzonych

    # WYLACZENIE SAMOZWROTNE PRZYBITE Z DRUGIEJ STRONY: raport, ktory pomijamy, ma
    # NAPRAWDE cytowac wszystkie cztery nazwy. Bez tego „wylaczylem raport o tej
    # bramce" bylo by amnestia na cokolwiek, co ktos w nim napisze.
    with open(os.path.join(ROOT, "reports", RAPORT_SAMOZWROTNY), encoding="utf-8") as u:
        samozwrotny = u.read()
    for _plik, nazwa in sorted(CYTATY_NIE_TWIERDZENIA):
        assert "`%s = " % nazwa in samozwrotny, (
            "`%s` nie jest juz cytowane w `%s` — wylaczenie tego raportu z populacji "
            "przestaje mieć powod i staje sie amnestia" % (nazwa, RAPORT_SAMOZWROTNY))


def test_granica_bloku_kodu_jest_TA_SAMA_po_obu_stronach():
    """ODPOWIEDZ 6.D230: jedna granica, i jest ona WYKONANA, a nie opisana.

    **Dlaczego wejscie syntetyczne, a nie `reports/`.** Katalog nie moze tego
    rozstrzygnac: oba czytniki sa nad nim ZIELONE i byly zielone takze wtedy, gdy
    granice mialy rozne — roznica zapala sie dopiero, gdy ktos napisze raport
    cytujacy cudze twierdzenie w jego wlasnym ksztalcie. Bramka oparta na liczbach
    z katalogu mierzylaby wiec wielkosc katalogu, a nie granice. Ta sama rodzina, co
    `test_twierdzenie_DOPISANE_do_sekcji_WCHODZI_do_pomiaru` z 6.D216.

    **Probka niesie KAZDY z czterech przypadkow**: oba ksztalty (`CLAIM`
    i `` `NAZWA = N` ``) raz w bloku i raz poza nim. Bez czlonu „poza blokiem"
    bramke przeszedlby czytnik, ktory nie widzi NICZEGO — pusty zbior spelnia
    „nie widzi cytatu" tak samo dobrze, jak czytnik dzialajacy (6.D27).
    """
    probka = "\n".join([
        "# Raport probny 6.D230",
        "",
        "Poza blokiem: `MINIMUM_CLAIMS = 4242` oraz `MINIMUM_CLAIMS` mowi 4242.",
        "",
        "```",
        "W bloku:    `MINIMUM_CLAIMS = 7777` oraz `MINIMUM_CLAIMS` mowi 7777.",
        "```",
        "",
    ])
    zrodla = [("probka.md", probka)]

    jedne = wystapienia_w_jednych_grawisach(zrodla)
    claim = list(claims_in_reports({"MINIMUM_CLAIMS": MINIMUM_CLAIMS}, zrodla))

    liczby_jedne = [l for _n, _w, _z, l in jedne]
    liczby_claim = [said for _n, _w, _c, said, _v in claim]

    # 1. ZADEN czytnik nie widzi czlonu W BLOKU. To jest cale rozstrzygniecie 6.D230
    #    i dlatego stoi PIERWSZE: gdy granica sie rozjedzie, komunikat ma mowic
    #    o granicy, a nie o liczniku obrotow ponizej.
    assert [l for l in liczby_jedne if l == "7777"] == [], (
        "`wystapienia_w_jednych_grawisach()` czyta twierdzenie z BLOKU KODU jako "
        "twierdzenie autora, a `claims_in_reports()` go pomija — granica rozjechala "
        "sie z powrotem i cytowanie cudzego twierdzenia w jego wlasnym ksztalcie "
        "znowu zapala bramke na tekscie poprawnym (6.D219, 6.D27)")
    assert [l for l in liczby_claim if l == "7777"] == [], (
        "`claims_in_reports()` przestal pomijac bloki ogrodzone — powod stoi przy "
        "`FENCE` i jest zmierzony na `reports/report-claims-audit.md`")

    # 2. LICZNIK OBROTOW: oba widza czlon POZA blokiem. Bez tego warunek 1 spelnia
    #    takze czytnik, ktory nie widzi NICZEGO (6.D27). Rownosc, a nie `in`:
    #    ksztalt `literal in cos` jest pilnowany przez `test_assertion_gate.py`,
    #    a ta asercja stoi na ZWROCIE czytnika, nie na napisie.
    assert liczby_jedne == ["4242"], (
        "czytnik `NAZWA = N` na probce dal %r zamiast samego czlonu SPOZA bloku — "
        "jesli pusto, to nie widzi NICZEGO i warunek wyzej nie mowi o niczym"
        % (jedne,))
    assert liczby_claim == ["4242"], (
        "czytnik `CLAIM` na probce dal %r zamiast samego czlonu SPOZA bloku"
        % (claim,))

    # 3. DAWNA granica ma te probke przeciac — inaczej zdanie „ujednolicone" byloby
    #    prawda takze o probce, ktorej roznica nigdy nie dotyczyla.
    dawne = wystapienia_w_jednych_grawisach(zrodla, pomijaj_bloki=False)
    assert [l for _n, _w, _z, l in dawne] == ["4242", "7777"], (
        "probka nie odroznia dawnej granicy od dzisiejszej (%r) — kontrola przyrzadu "
        "nie mowi o niczym" % (dawne,))


# 6.D25: uruchomienie tego pliku WPROST idzie ta sama droga, co caly zestaw —
# z licznikiem asercji i z odmowa przy zerze testow. Bez tej gałęzi `python3
# tools/tests/<modul>.py` konczyl sie kodem 0, nie wykonawszy ani jednego testu.
if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))


# --- 6.D216: sekcja „zauwazone, nie tkniete” — czytnik, podlogi i GRANICA -----------
#
# **Skad ten blok.** Sekcja „zauwazone, nie tkniete” stoi w 153 raportach z 343 i niesie
# **205 twierdzen liczbowych** (punkt z cyfra po zamaskowaniu adresow; liczebnikow
# zapisanych slowem jest osobno 92). `CLAIM` wyzej pilnuje z nich **DWA**. Dla porownania
# w calych raportach `CLAIM` pilnuje 54 twierdzen — sekcja „zauwazone” dostarcza bramce
# 2 z 54, a sama niesie 205. Zmierzone 15.09.2026, pelny wykaz:
# `reports/6d216-dwiescie-piec-twierdzen-i-dwa-pilnowane.md`.
#
# **Adres jest pilnowany, liczba nie jest.** W zdaniu „`src/Sim.Runner/` ma 23 z 53
# zgloszen" `test_report_hygiene.test_kazda_sciezka_wymieniona_w_raporcie_rozwiazuje_sie_w_drzewie`
# sprawdza, ze `src/Sim.Runner/` istnieje. Ze jest ich 23 — nie sprawdza nic.
#
# **ROZSTRZYGNIECIE: bramki na PRAWDZIWOSCI tych zdan NIE MA, i sa to trzy powody.**
#
# 1. Automat, ktory istnieje, pilnuje 2 z 205. Poszerzenie `CLAIM` o ksztalt bez
#    grawisow rozstrzygnelo 6.D209 — przeciw, pomiarem.
# 2. **Przeliczalnosc jest wlasnoscia CZYTNIKA, nie zdania.** Twierdzen 6.D207 nie da sie
#    dzis przeliczyc nie dlatego, ze sa niejasne, tylko dlatego, ze sito, ktore je
#    wyprodukowalo, nie zostalo w drzewie — i nie zostalo SLUSZNIE (5 trafien falszywych
#    na 5, 6.D27). Bramka zadajaca przeliczalnosci karalaby te pozycje, ktore posluchaly
#    reguly projektu.
# 3. **Automat nie odrozni falszu od zdania, ktore sie zestarzalo.** Mechanizm 6.D108
#    (`zdanie_z_dnia_pomiaru`) zwalnia twierdzenie po dacie STALEJ z gita; te zdania
#    zadnej stalej nie cytuja, wiec kotwicy nie maja. Zmierzone na parze z jednego dnia:
#    „51” z 6.D209 (dzis 55, POPRAWNE w swoim dniu) i „ramion `when` w `src/Sim/` nie ma”
#    z 6.D210 (dzis cztery, od 05.09.2026, czyli FALSZYWE w swoim dniu) wygladaja dla
#    automatu porownujacego z dzisiejszym drzewem IDENTYCZNIE.
#
# **Co wiec tu stoi.** Czytnik sekcji z podlogami i kontrola przyrzadu. Prawdziwosci nie
# pilnuje i nie udaje, ze pilnuje — pilnuje, ze nastepna pozycja pytajaca o to samo nie
# bedzie musiala odtwarzac sita z prozy, czyli zamyka dokladnie to, co powod drugi nazwal
# po imieniu.

#: Naglowek dowolnego poziomu w raporcie.
NAGLOWEK_RAPORTU = re.compile(r"^(#{1,6})\s+(.*)$")

#: Rdzen nazwy sekcji. Brzmien jest w katalogu **36** po odjeciu numeru, a numer sekcji
#: waha sie **od 2 do 12** — dlatego pytanie idzie o rdzen, nie o cale zdanie.
#:
#: **`zauwa[zż]on` -> `zauwa[zż]` (16.09.2026, 6.D228, decyzja wlasciciela). Ten akapit
#: jest PRZEPISANY, a nie dopisany obok, i zmienia sie w nim ZDANIE O GRANICY, nie tylko
#: rdzen.** Stalo tu: „sekcja nazwana »Uwagi na marginesie« wypadlaby z pomiaru". Zdanie
#: bylo o przypadku HIPOTETYCZNYM — naglowka „Uwagi na marginesie" nie ma w katalogu ani
#: razu — a prawdziwa granica biegla o wiele blizej i kosztowala **32 realne sekcje**:
#: rdzen z koncowka imieslowu nie widzial rodziny odmian `zauwazylem`, czyli naglowkow
#: „Co zauwazylem przy okazji, ale nie tknalem" (i dziesieciu dalszych brzmien).
#: Zmierzone 16.09.2026 na `e1c63f7`: przed rozszerzeniem **169** sekcji w **165**
#: raportach, po nim **201** w **197**; twierdzen liczbowych 219 -> 271.
#:
#: **Gdzie granica biegnie TERAZ, z liczbami zamiast przykladu hipotetycznego:**
#:
#: 1. Rdzen pyta o SLOWO, wiec poza pomiarem zostaje sekcja o tej samej tresci nazwana
#:    slowem INNYM: „Znalezione po drodze, nie tkniete", „Co wyszlo przy okazji",
#:    „Czego nie tknalem". Objecie ich wymaga LISTY SYNONIMOW, nie rdzenia — inna klasa
#:    i ta pozycja jej nie podejmuje.
#: 2. W druga strone: rdzen nie pyta, czy naglowek JEST sekcja — wchodzi slowo w dowolnej
#:    roli. Zmierzone: 1 z 32 dolozonych taka sekcja nie jest
#:    (`serializacja-jobow-ci.md` §7 „Bramka, bo zestaw tej zmiany nie zauwazyl"),
#:    czyli zanieczyszczenie **3,1 %**, i jest ono POLICZONE, a nie oszacowane.
SEKCJA_ZAUWAZONE = re.compile(r"zauwa[zż]", re.IGNORECASE)

#: Ksztalty, ktore NIOSA cyfre, a twierdzeniem o drzewie nie sa: data, numer pozycji,
#: numer PR-a, numer sekcji, sciezka z numerem wiersza, skrot commita. Bez tej maski
#: kazdy punkt powolujacy sie na `6.D200` liczylby sie jako twierdzenie liczbowe —
#: zmierzone: 320 punktow przed maska, 205 po.
ADRES_NIE_TWIERDZENIE = re.compile(
    r"\b\d{2}\.\d{2}\.\d{4}\b"
    r"|\b6\.D\d+\b|\bMB-\d+\b|\bKN-\d+[a-z]?\b"
    r"|#\d+\b|§\s?\d+(?:\.\d+)*"
    r"|[\w./-]+\.(?:cs|py|md|json|yml|glb|sh|txt|csproj)(?::\d+(?:-\d+)?)?"
    r"|\b[0-9a-f]{7,40}\b"
    r"|\bwiersz\w*\s+\d+\b")

#: Liczba w prozie. `(?<![\w.])` odcina koncowke wersji i numer po kropce, `(?![\w])`
#: odcina `2026-09` i `net10`.
CYFRA_W_PROZIE = re.compile(r"(?<![\w.])\d+(?![\w])")

#: Podlogi, nie rownosci: raportow przybywa z kazda pozycja, a rownosc kazalaby podnosic
#: te liczbe przy kazdym commicie z raportem.
#:
#: **Przeliczone 16.09.2026 (6.D228) razem z rozszerzeniem rdzenia, w TYM SAMYM commicie,
#: bo rozszerzenie przesuwa populacje o 32 sekcje.** Zmierzone na `e1c63f7`: **201**
#: sekcji w **197** raportach, **271** twierdzen liczbowych.
#:
#: **Zapas 5 / 5 / 8 jest tu NOWY i ma powod, ktorego poprzednia wersja nie miala.**
#: Tamte podlogi staly na wartosci z dnia commita, czyli z zapasem ZERO, i nigdy sie nie
#: zapalily — bo w calej historii `reports/` nie ma ANI JEDNEGO usuniecia pliku ani
#: zmiany nazwy (`--diff-filter=D` i `--diff-filter=R` daja zero). Teraz zapas jest
#: potrzebny, bo ISTNIEJE ZNANA POPRAWKA, ktora te liczby OBNIZY: jeden z 32 dolozonych
#: naglowkow sekcja nie jest i wnosi 1 sekcje, 1 raport i 2 twierdzenia. Podloga bez
#: zapasu zapalilaby sie na jego poprawieniu, czyli na pracy POPRAWNEJ (6.D27).
#:
#: **Zapas nie oslepia bramki i to jest zmierzone, nie zalozone:** najmniejsza awaria,
#: ktora te podlogi maja lapac — cofniecie rdzenia do `zauwa[zż]on` — kosztuje
#: **32 / 32 / 52**, czyli szesc razy wiecej niz zapas. Oslepienie czytnika do zera
#: kosztuje 201 / 197 / 271.
MIN_SEKCJI_ZAUWAZONE = 196
MIN_RAPORTOW_Z_SEKCJA = 192
MIN_TWIERDZEN_W_ZAUWAZONYCH = 263


def _zrodla_raportow():
    for path in sorted(glob.glob(os.path.join(REPORTS, "*.md"))):
        with open(path, encoding="utf-8") as handle:
            yield os.path.basename(path), handle.read()


def sekcje_zauwazone(zrodla=None):
    """`(raport, naglowek, wiersze)` dla kazdej sekcji „zauwazone” w katalogu.

    `zrodla` to pary `(nazwa, tekst)`; domyslnie caly `reports/`. Wejscie syntetyczne
    jest tu trescia, a nie wygoda: bez niego kontrola przyrzadu nie mialaby czym
    udowodnic, ze dopisane twierdzenie WCHODZI do pomiaru.
    """
    for nazwa, tekst in (zrodla if zrodla is not None else _zrodla_raportow()):
        wiersze = tekst.splitlines()
        otwarta = None
        for i, w in enumerate(wiersze):
            naglowek = NAGLOWEK_RAPORTU.match(w)
            if not naglowek:
                continue
            if otwarta is not None:
                yield nazwa, otwarta[0], wiersze[otwarta[1]:i]
                otwarta = None
            if SEKCJA_ZAUWAZONE.search(naglowek.group(2)):
                otwarta = (naglowek.group(2), i + 1)
        if otwarta is not None:
            yield nazwa, otwarta[0], wiersze[otwarta[1]:]


def punkty_sekcji(tresc):
    """Wypunktowania i akapity sekcji; wiersze ciagu dalszego sklejone w jeden punkt.

    Bloki ogrodzone ``` i wiersze tabeli wypadaja — to cytat i zestawienie, a nie
    zdanie raportu. Ta sama granica, co przy `FENCE` wyzej, i z tego samego powodu.
    """
    out, biezacy, w_bloku = [], [], False
    for w in tresc:
        if FENCE.match(w):
            w_bloku = not w_bloku
            continue
        if w_bloku or w.lstrip().startswith("|"):
            continue
        if not w.strip():
            if biezacy:
                out.append(" ".join(biezacy))
                biezacy = []
            continue
        if re.match(r"^\s*(?:[-*]|\d+\.)\s", w) and biezacy:
            out.append(" ".join(biezacy))
            biezacy = []
        biezacy.append(w.strip())
    if biezacy:
        out.append(" ".join(biezacy))
    return out


def twierdzenia_liczbowe_w_zauwazonych(zrodla=None):
    """`(raport, naglowek, punkt)` dla punktow niosacych liczbe po masce adresow."""
    for nazwa, naglowek, tresc in sekcje_zauwazone(zrodla):
        for punkt in punkty_sekcji(tresc):
            if CYFRA_W_PROZIE.search(ADRES_NIE_TWIERDZENIE.sub(
                    lambda m: "·" * len(m.group(0)), punkt)):
                yield nazwa, naglowek, punkt


#: Orzeczenia UNIWERSALNE i NEGATYWNE — 6.D227.
#:
#: Lista jest WYBOREM, nie prawdą o języku, i dlatego stoi tu z liczbą obok: przy niej
#: slajs wąski ma **35** pozycji, a slajs szeroki (zakres nazwany + orzeczenie
#: gdziekolwiek w punkcie) — **64**. Różnica jest tu treścią, nie szumem: wąski pyta
#: o zdania, w których zakres i orzeczenie STOJĄ OBOK SIEBIE, czyli o kształt, na
#: którym potknęło się 6.D210.
ORZECZENIA_ZAKRESU = (
    "nie ma", "nie istnieje", "brak", "ani jeden", "ani jednej", "ani jednego",
    "żaden", "żadna", "żadnego", "wszystkie", "każdy", "każda", "jedyny", "jedyna",
    "nigdzie", "zero", "nie znalazłem", "nigdy",
)

#: Ile znaków może dzielić zakres od orzeczenia, żeby uznać je za stojące OBOK.
#: Zmierzone 16.09.2026, na tym samym czytniku i tym samym katalogu: przy oknie **60**
#: slajs wąski ma **35** pozycji, przy **20** — **17**, czyli mniej niż połowę. Okno
#: jest więc WYBOREM, który zmienia wynik dwukrotnie, i dlatego stoi tu z obiema
#: liczbami zamiast samo.
OKNO_ZAKRESU = 60

#: Katalog albo plik w grawisach — ZAKRES NAZWANY. **Plik jest tu policzony razem
#: z katalogiem i to jest wybór, nie przeoczenie:** zdanie „w `src/Sim/Line/LineCore.cs`
#: nie ma ani jednego" nazywa zakres tak samo jak zdanie o katalogu, a klasa, o którą
#: pyta ta pozycja, bierze się z tego, że NAZWANY zakres jest szerszy od ZMIERZONEGO —
#: bez względu na to, czy nazwą jest katalog, czy plik.
#:
#: Zmierzone, bo różnica jest duża i chcę, żeby następny czytający ją widział:
#: wzorzec obejmujący **wyłącznie katalogi** (kończące się ukośnikiem) daje przy tym
#: samym oknie **14** pozycji, a ten — **35**. Zawężenie do katalogów odcina więc
#: dwie trzecie slajsu.
ZAKRES_W_GRAWISACH = re.compile(r"`[A-Za-z_][\w./-]*/[\w./*-]*`")

#: Podłogi obu slajsów. **Podłogi, nie równości, i to jest wybór z powodem:** raportów
#: przybywa, a przepisywać ich nie wolno (6.D108), więc równość zapalałaby się na
#: każdym nowym poprawnym raporcie (6.D27). Zero znaczyłoby „czytnik oślepł", a nie
#: „nie ma takich zdań" — i dlatego podłoga w ogóle stoi.
MIN_TWIERDZEN_O_ZAKRESIE = 35
MIN_SLAJS_SZEROKI = 64


def twierdzenia_o_zakresie(zrodla=None):
    """`(raport, naglowek, punkt)` dla punktów, w których zakres stoi OBOK orzeczenia.

    **Czego ta funkcja NIE robi, i to jest jej treść, nie zastrzeżenie:** nie mówi ani
    słowa o tym, czy zdanie jest PRAWDZIWE. Liczy KSZTAŁT. 6.D216 zmierzyło trzema
    powodami, że sito prawdziwości postawić się nie da, a 6.D227 sprawdziło to jeszcze
    raz i znalazło trzy przypadki tekstu POPRAWNEGO, na których takie sito by się
    zapaliło: `6d197` („domyślnych PO WYLICZENIU jest w `src/Sim/` zero" — prawdziwe
    i zawężone, kształt identyczny), `6d209` („wystąpień … 51", dziś 55 — poprawne
    w swoim dniu) i `6d185` („`KcvFunction` w `src/Game/` nie pada ani razu" — bez
    kotwicy, a prawdziwe).

    **Po co więc ta funkcja istnieje.** Bo slajsu, o który pyta ta klasa, nie liczy
    dziś NIC — zmierzone podstawieniem: trzy mutacje w trzech różnych raportach,
    w tym jedna zamieniająca zdanie prawdziwe w fałszywe, dały `2493/2493 przeszło`
    i kod 0. Podłogi 6.D216 nie drgnęły, bo liczą sekcje i punkty z cyfrą, a żadna
    z mutacji nie zmienia ani jednego, ani drugiego. Następna pozycja pytająca o tę
    klasę nie będzie więc odtwarzać slajsu z prozy — i to jest cała zdobycz.
    """
    for nazwa, naglowek, tresc in sekcje_zauwazone(zrodla):
        for punkt in punkty_sekcji(tresc):
            maly = punkt.lower()
            for trafienie in ZAKRES_W_GRAWISACH.finditer(punkt):
                od = max(0, trafienie.start() - OKNO_ZAKRESU)
                do = min(len(punkt), trafienie.end() + OKNO_ZAKRESU)
                okno = maly[od:do]
                if any(o in okno for o in ORZECZENIA_ZAKRESU):
                    yield nazwa, naglowek, punkt
                    break


def slajs_szeroki(zrodla=None):
    """Punkty z zakresem nazwanym i orzeczeniem GDZIEKOLWIEK — druga, luźniejsza miara.

    Stoi obok wąskiej, bo bez niej zwężenie WZORCA i zwężenie OKNA zapalałyby tę samą
    asercję i nie dałoby się ich odróżnić. Przy dzisiejszym drzewie: **64** wobec **35**.
    """
    for nazwa, naglowek, tresc in sekcje_zauwazone(zrodla):
        for punkt in punkty_sekcji(tresc):
            maly = punkt.lower()
            if ZAKRES_W_GRAWISACH.search(punkt) and any(
                    o in maly for o in ORZECZENIA_ZAKRESU):
                yield nazwa, naglowek, punkt


def test_slajs_zakresu_jest_LICZONY_a_nie_odtwarzany_z_prozy():
    """6.D227: klasa 6.D210 ma co najmniej pięć wystąpień, a nie liczy jej nic.

    **Skąd.** 6.D210 §9 pisze „ramion `when` w `src/Sim/` dziś nie ma", a są cztery
    (`src/Sim/Train/DriverKeys.cs:143,146,149,152`), od `877ab66` z 05.09.2026 — dziewięć
    dni przed tamtym zdaniem (6d210 nosi nagłówek 14.09.2026; do 16.09 stało tu „dziesięć",
    rozbieżne z raportem i komunikatem commitu tej samej pozycji). Nie jest to zwykła pomyłka: switch w `DriverKeys.cs`
    chodzi po `const char`, więc do populacji klasyfikatora 6.D210 **nie należy**
    i w tym zakresie zdanie jest PRAWDZIWE. Fałszywe robi je to, że zakres wzięto
    z kontekstu akapitu, a zapisano jako nazwę całego katalogu.

    **Zmierzone 16.09.2026, ręcznym przeglądem slajsu zawężonego do samych katalogów
    (14 pozycji przy dzisiejszym wzorcu): CZTERY pewne.** Poza przypadkiem
    założycielskim: `6d191` („nigdy nie trafia w to samo" przy populacji dwóch
    przebiegów), `6d201` („wszystkie 42 … sprawdzone na próbce pięciu pierwszych")
    i `ramka-w-sciezce` („poza `reports/` i `docs/` nie ma ani jednej" — pomiar objął
    pięć miejsc, a katalogów najwyższego poziomu jest osiem).

    **Ten akapit jest PRZEPISANY, a nie dopisany obok, i powód jest zawstydzający.**
    Pierwsza wersja mówiła „pięć pewnych i jeden graniczny" i wymieniała wśród nich
    `podloga-sciezek-na-raport`. **Tego raportu nie ma w ŻADNYM z dwóch slajsów** —
    zmierzone: `waski=False szeroki=False`. Powód: jego zdanie mówi o `` `.github/` ``,
    a `ZAKRES_W_GRAWISACH` żąda `[A-Za-z_]` jako pierwszego znaku, więc ścieżka
    zaczynająca się KROPKĄ jest dla czytnika niewidzialna. Zakres, który tamto zdanie
    NAZYWAŁO („slajs czternastu pozycji"), był więc szerszy od ZMIERZONEGO — czyli
    dokładnie klasa 6.D210, popełniona w commicie, który ją gasi. Granica jest teraz
    NAZWANA i ma własną bramkę
    (`test_czytnik_zakresu_MILCZY_na_sciezce_zaczynajacej_sie_KROPKA`), zamiast czekać
    na kolejny przegląd.
    """
    waski = list(twierdzenia_o_zakresie())
    szeroki = list(slajs_szeroki())
    assert len(waski) >= MIN_TWIERDZEN_O_ZAKRESIE, (
        "slajs wąski ma %d pozycji przy podłodze %d — czytnik przestał widzieć "
        "zakresy albo orzeczenia, a pusty slajs czyta się jak „nie ma takich zdań”"
        % (len(waski), MIN_TWIERDZEN_O_ZAKRESIE))
    assert len(szeroki) >= MIN_SLAJS_SZEROKI, (
        "slajs szeroki ma %d pozycji przy podłodze %d — zwężenie WZORCA zapala się "
        "tutaj, a zwężenie OKNA w asercji wyżej; bez dwóch podłóg nie da się ich "
        "odróżnić" % (len(szeroki), MIN_SLAJS_SZEROKI))
    assert len(waski) <= len(szeroki), (
        "slajs wąski (%d) jest szerszy od szerokiego (%d) — jeden z czytników "
        "przestał być zawężeniem drugiego" % (len(waski), len(szeroki)))


def test_czytnik_zakresu_liczy_KSZTALT_a_nie_prawdziwosc():
    """Kontrola przyrządu na wejściu SYNTETYCZNYM, w obie strony — i to jest sedno.

    Zdanie ZAWĘŻONE („w switchach po wyliczeniu") ma wejść do pomiaru tak samo, jak
    niezawężone. Bez tej asercji ktoś wziąłby tę bramkę za sito prawdziwości — a nią
    nie jest i być nie może (6.D216, trzy powody; 6.D227, trzy nazwane przypadki
    tekstu poprawnego).
    """
    def slajs(tekst):
        return list(twierdzenia_o_zakresie([("p.md", "# R\n\n## 8. Zauważone\n\n" + tekst + "\n")]))

    assert len(slajs("- ramion `when` w `src/Sim/` dziś nie ma")) == 1, (
        "przypadek ZAŁOŻYCIELSKI tej pozycji — dosłowne zdanie z 6.D210 — wypadł "
        "ze slajsu; bramka jest wtedy zielona nad klasą, dla której powstała")
    assert len(slajs(
        "- ramion `when` w switchach po wyliczeniu w `src/Sim/` dziś nie ma")) == 1, (
        "zdanie ZAWĘŻONE wypadło ze slajsu — wtedy bramka zaczyna orzekać "
        "o prawdziwości, a tego 6.D216 zabroniło trzema powodami")
    # Druga strona: sam zakres bez orzeczenia i samo orzeczenie bez zakresu.
    assert slajs("- czytnik chodzi po `src/Sim/` i zlicza ramiona") == [], (
        "sam ZAKRES, bez orzeczenia uniwersalnego, wszedł do slajsu — czytnik liczy "
        "wtedy każdą wzmiankę o katalogu i podłoga przestaje cokolwiek znaczyć")
    assert slajs("- nie ma tu ani jednego takiego przypadku") == [], (
        "samo ORZECZENIE, bez nazwanego zakresu, weszło do slajsu — a klasa 6.D210 "
        "bierze się właśnie z tego, że zakres jest NAZWANY szerzej niż zmierzony")


def test_czytnik_zakresu_MILCZY_na_zakresie_nazwanym_SLOWEM_i_to_jest_zapisane():
    """Granica, o którą pozycja prosi wprost: na czym sito MILCZY.

    Zakres nazwany słowem, bez grawisów i bez ukośnika, jest dla czytnika niewidzialny.
    Nie jest to usterka do naprawienia przy okazji: poszerzenie na prozę wymagałoby
    rozpoznawania nazw katalogów po znaczeniu, a nie po kształcie, i zapalałoby się
    na zdaniach o czymkolwiek. Granica ma być NAZWANA, a nie zostawiona do odkrycia —
    to jest ta sama cicha granica, o którą pyta 6.D228 dla rdzenia słowa.
    """
    def slajs(tekst):
        return list(twierdzenia_o_zakresie([("p.md", "# R\n\n## 8. Zauważone\n\n" + tekst + "\n")]))

    assert slajs("- w całym rdzeniu symulacji nie ma ani jednego takiego ramienia") == [], (
        "czytnik zaczął widzieć zakres nazwany SŁOWEM — jeśli to zamierzone, "
        "zdanie o granicy trzeba przepisać, a nie zostawić")
    assert len(slajs("- w `src/Sim/` nie ma ani jednego takiego ramienia")) == 1, (
        "ten sam zakres w grawisach też przestał być widziany — wtedy asercja wyżej "
        "jest zielona nad czytnikiem ślepym na wszystko")
    # **Trzecia asercja, dopisana 16.09.2026 po przeglądzie adwersaryjnym.** Bez niej
    # zdanie kontrolne wyżej („w całym rdzeniu symulacji…") nie ma ANI grawisów, ANI
    # ukośnika — więc nie odróżnia „milczy bez grawisów" od „milczy bez ukośnika".
    # Zmierzone: skreślenie grawisów ze wzorca (`ZAKRES_W_GRAWISACH` bez nich) daje
    # 40/70 zamiast 35/64, a ta bramka zostawała ZIELONA. Bramka nazwana od granicy
    # nie mierzyła granicy, którą nazywa.
    assert slajs("- w src/Sim/ nie ma ani jednego takiego ramienia") == [], (
        "zakres BEZ grawisów wszedł do slajsu — nazwa stałej mówi `W_GRAWISACH`, "
        "a czytnik przestał ich wymagać; wtedy do pomiaru wchodzi każda ścieżka "
        "z prozy, także wymieniona mimochodem")


def test_czytnik_zakresu_MILCZY_na_sciezce_zaczynajacej_sie_KROPKA():
    """DRUGA cicha granica, nazwana 16.09.2026 — i nazwana, bo mnie na niej złapano.

    `ZAKRES_W_GRAWISACH` żąda `[A-Za-z_]` jako pierwszego znaku, więc `` `.github/` ``
    i `` `.claude/` `` są dla czytnika niewidzialne. Nie jest to granica teoretyczna:
    `reports/podloga-sciezek-na-raport.md` niesie zdanie „22 wzmianki … **wszystkie**
    pod `.github/`", czyli podręcznikowy okaz klasy 6.D210 — a slajs go NIE WIDZI
    (zmierzone: `waski=False szeroki=False`). Pierwsza wersja docstringa nad
    `test_slajs_zakresu_jest_LICZONY…` wymieniała ten raport wśród znalezisk slajsu,
    co było **nieprawdą tej samej klasy, którą ta pozycja gasi**.

    **Dlaczego granica ZOSTAJE, a nie znika.** Dopuszczenie kropki na początku każe
    wzorcowi łapać też skróty zdaniowe w rodzaju `` `.md` `` i końcówki ścieżek
    cytowane bez katalogu, a te nie nazywają żadnego zakresu. Poszerzenie jest do
    zrobienia, ale zmienia POPULACJĘ obu slajsów i obie podłogi, więc jest osobną
    pozycją — nie przypisem do tej. Do tego czasu granica ma stać ZMIERZONA
    i psuć się głośno w obie strony, zamiast czekać na następny przegląd.
    """
    def slajs(tekst):
        return list(twierdzenia_o_zakresie([("p.md", "# R\n\n## 8. Zauważone\n\n" + tekst + "\n")]))

    assert slajs("- wzmianek jest 22 i wszystkie leżą pod `.github/`") == [], (
        "czytnik zaczął widzieć ścieżkę zaczynającą się KROPKĄ — jeżeli to zamierzone, "
        "przepisz zdanie o granicy i przelicz OBIE podłogi, bo populacja slajsu rośnie")
    assert len(slajs("- wzmianek jest 22 i wszystkie leżą pod `github/akcje`")) == 1, (
        "ta sama ścieżka BEZ wiodącej kropki też przestała być widziana — wtedy "
        "asercja wyżej jest zielona nad czytnikiem ślepym na wszystko")


def test_czytnik_sekcji_zauwazone_widzi_caly_katalog():
    """Podloga, nie rownosc — a zero znaczyloby „czytnik oslepl”, nie „nie ma sekcji”."""
    sekcje = list(sekcje_zauwazone())
    raporty = {s[0] for s in sekcje}
    assert len(sekcje) >= MIN_SEKCJI_ZAUWAZONE, (
        "sekcji „zauwazone” znaleziono %d przy podlodze %d — czytnik przestal widziec "
        "naglowki, a pusty skan odpowiada „zero twierdzen” tak samo przekonujaco jak "
        "widzacy" % (len(sekcje), MIN_SEKCJI_ZAUWAZONE))
    assert len(raporty) >= MIN_RAPORTOW_Z_SEKCJA, (
        "raportow z taka sekcja znaleziono %d przy podlodze %d"
        % (len(raporty), MIN_RAPORTOW_Z_SEKCJA))

    twierdzenia = list(twierdzenia_liczbowe_w_zauwazonych())
    assert len(twierdzenia) >= MIN_TWIERDZEN_W_ZAUWAZONYCH, (
        "twierdzen liczbowych w tych sekcjach znaleziono %d przy podlodze %d — maska "
        "adresow zjadla za duzo albo czytnik punktow przestal sklejac wiersze"
        % (len(twierdzenia), MIN_TWIERDZEN_W_ZAUWAZONYCH))


def test_twierdzenie_DOPISANE_do_sekcji_WCHODZI_do_pomiaru():
    """Kontrola przyrzadu, o ktora prosilo pole „Weryfikacja” pozycji 6.D216.

    Podlogi wyzej sa spelnione takze przez czytnik, ktory czyta polowe katalogu. Dowodem,
    ze pomiar naprawde obejmuje zdanie dopisane do sekcji, moze byc tylko wejscie
    syntetyczne — tu cztery probki, kazda o innej granicy.
    """
    probka = "\n".join([
        "# Raport probny",
        "",
        "## 1. Cos",
        "",
        "- zdanie bez liczby",
        "",
        "## 8. Zauwazone przy okazji, nietkniete",
        "",
        "- **`src/Sim/Train/Probka.cs` ma 17 wywolan** i nikt tego nie pilnuje.",
        "- zdanie bez zadnej liczby, wiec nie jest twierdzeniem liczbowym",
        "- powolanie sie na 6.D200 i §7 z 13.09.2026, i nic wiecej",
        "",
        "```",
        "liczba w bloku kodu: 999",
        "```",
        "",
        "## 9. Dalej",
        "",
        "- 42 stoi poza sekcja",
    ])
    sekcje = list(sekcje_zauwazone([("probka.md", probka)]))
    assert len(sekcje) == 1, "czytnik znalazl %d sekcji zamiast jednej" % len(sekcje)

    twierdzenia = [t[2] for t in twierdzenia_liczbowe_w_zauwazonych([("probka.md", probka)])]
    assert len(twierdzenia) == 1, (
        "z sekcji probnej wyszlo %d twierdzen zamiast jednego: %r" % (len(twierdzenia), twierdzenia))
    assert "17" in twierdzenia[0], (
        "twierdzenie dopisane do sekcji NIE weszlo do pomiaru — kontrola przyrzadu "
        "nie przechodzi, wiec podlogi wyzej nie mowia o niczym: %r" % (twierdzenia,))
    assert "999" not in twierdzenia[0], "liczba z bloku kodu weszla jako twierdzenie"
    assert "42" not in twierdzenia[0], "liczba spoza sekcji weszla jako twierdzenie"


def test_rdzen_widzi_rodzine_ZAUWAZYLEM_a_nie_tylko_ZAUWAZONE():
    """Rozszerzenie rdzenia z 6.D228 postawione na ZACHOWANIU, nie na podlodze.

    Podloga `MIN_SEKCJI_ZAUWAZONE` zapala sie po cofnieciu rdzenia, ale mowi tylko
    „sekcji jest za malo” — a taki komunikat da sie uciszyc obnizeniem podlogi, czyli
    dokladnie tym ruchem, przed ktorym 6.D27 ostrzega. Ta bramka mowi, KTOREGO
    brzmienia zabraklo, i na wejsciu syntetycznym, wiec obnizenie podlogi jej nie
    dotyczy. Cztery probki: dwie MAJA wejsc, dwie NIE MAJA — i te dwie sa granica
    wypisana przy stalej, wykonana zamiast opisanej.
    """
    def naglowek(tekst):
        return "\n".join(["# Raport probny", "", "## 8. " + tekst, "",
                           "- **`src/Sim/Probka.cs` ma 17 wywolan** i nikt tego nie pilnuje."])

    for tekst in ("Co zauwazylem przy okazji, ale nie tknalem",
                  "Co zauważyłem przy okazji, ale nie tknąłem",
                  "Zauważone przy okazji, nie tknięte"):
        probka = [("probka.md", naglowek(tekst))]
        assert len(list(sekcje_zauwazone(probka))) == 1, (
            "rdzen NIE widzi naglowka %r — a takich naglowkow jest w katalogu %d "
            "i to one byly cala trescia 6.D228; jesli `SEKCJA_ZAUWAZONE` wrocilo do "
            "koncowki imieslowu, ta asercja jest pierwsza, ktora to powie"
            % (tekst, len(list(sekcje_zauwazone()))))

    for tekst in ("Uwagi na marginesie", "Znalezione po drodze, nie tkniete"):
        probka = [("probka.md", naglowek(tekst))]
        assert list(sekcje_zauwazone(probka)) == [], (
            "naglowek %r wszedl do pomiaru, a komentarz przy `SEKCJA_ZAUWAZONE` mowi "
            "wprost, ze rdzen pyta o SLOWO i takie brzmienia zostaja poza nim — "
            "rozeszly sie kod i zdanie o granicy" % tekst)


def test_maska_adresow_wycina_adres_a_zostawia_liczbe():
    """Granica maski, wykonana a nie opisana: szesc ksztaltow adresu i jedna liczba.

    Bez maski punkt „zmierzone 13.09.2026 przy 6.D201 (PR #550), §7, `plik.cs:42`”
    liczylby sie jako twierdzenie liczbowe — a nie mowi o drzewie ani jednej liczby.
    """
    adresy = [
        "zmierzone 13.09.2026 przy 6.D201",
        "PR #550 i MB-07, KN-4b",
        "sekcja §7 oraz §4.1",
        "`tools/tests/test_backlog.py:1564`",
        "commit 2b95084 i 877ab66",
        "wiersz 362 tego pliku",
    ]
    for adres in adresy:
        po = ADRES_NIE_TWIERDZENIE.sub(lambda m: "·" * len(m.group(0)), adres)
        assert not CYFRA_W_PROZIE.search(po), (
            "maska zostawila liczbe w adresie %r -> %r — punkt powolujacy sie na numer "
            "pozycji liczylby sie jako twierdzenie o drzewie" % (adres, po))

    zostaje = "ma 23 z 53 zgloszen"
    po = ADRES_NIE_TWIERDZENIE.sub(lambda m: "·" * len(m.group(0)), zostaje)
    assert CYFRA_W_PROZIE.findall(po) == ["23", "53"], (
        "maska zjadla liczbe z twierdzenia %r -> %r — bramka milczalaby o tym, o co pyta"
        % (zostaje, po))


# --- 6.D219: REMIS dat raportu i stałej — ćwierć populacji, a nie przypadek brzegowy --
#
# **Zmierzone 15.09.2026 na całym katalogu, obu kształtach twierdzeń:**
#
#     klasa dat          CLAIM   `NAZWA = N`   razem   rozjechanych
#     REMIS                  3            23      26              2
#     stała nowsza          15            14      29             27
#     raport nowszy         38             8      46              1
#
# **Remis to 26 ze 101, czyli ćwierć populacji** — a dla kształtu `` `NAZWA = N` ``
# 23 z 45, czyli ponad połowę. Teza „remis to brzeg" jest zmierzona jako nieprawdziwa.
#
# **ROZSTRZYGNIĘCIE: `>=` ZOSTAJE, remis NIE zwalnia.** Powód jest z odsetka rozjazdu,
# nie z wygody: klasa zwalniana dziś (`stała nowsza`) ma **93,1 %** rozjazdu, remis
# **7,7 %**, a klasa pilnowana (`raport nowszy`) — 2,2 %. Datowanie z 6.D108 istnieje po
# to, żeby zwalniać zdania ZESTARZAŁE; remis zachowuje się jak populacja świeża, nie jak
# zestarzała. Oba rozjechane remisy to zresztą dokładnie ten przypadek, przed którym
# ostrzegało pole pozycji — twierdzenie wpisane w commicie, który stałą ustawił
# (`6d156…/NIEROZSTRZYGNIETYCH`, `sciezki-w-polach-blokow.md/MAX_EXCEPTIONS`); pod `>=`
# są łapane i skierowane do oceny człowieka, pod `>` zniknęłyby bez słowa.
#
# **Czego ta pozycja NIE robi: nie przybija populacji remisu.** Klasa zależy od
# `data_stalej`, a ta datuje stałą commitem, który ruszył jej PLIK, nie jej wiersz —
# zapadka na 26 rozjechałaby się przy pierwszej edycji dowolnego modułu niosącego
# cytowaną stałą. Zmierzone na żywo: zbiór twardych rozjazdów z 6.D209 zmalał z 4 na 3
# bez zmiany jednej cyfry w raporcie, bo `test_report_claims.py` został tknięty.


def test_REMIS_dat_NIE_zwalnia_twierdzenia():
    """Decyzja o remisie, nazwana z imienia — bo dotąd nie była nazwana nigdzie.

    **To nie jest druga bramka, tylko nazwanie istniejącej.** Zmierzone 15.09.2026:
    odwrócenie operatora w `zdanie_z_dnia_pomiaru` zapala w całym zestawie DOKŁADNIE
    JEDEN test — trzeci blok `test_zdanie_datowane_nie_jest_pilnowane_a_zdanie_biezace_jest`,
    czyli kontrolę na wejściu SYNTETYCZNYM. Żadna bramka czytająca dzisiejsze raporty tej
    zmiany nie widzi i widzieć nie może: remis nie daje dziś ani jednej czerwieni.
    Decyzja jest więc pilnowana wyłącznie syntetycznie, od 6.D108 — a nazwa tamtego testu
    mówi o zdaniu DATOWANYM, nie o remisie, więc następny agent szukałby jej w środku
    testu o czym innym.

    Wejście syntetyczne, bo remisu nie da się wytworzyć w drzewie roboczym: raport tknięty
    w drzewie dostaje `TERAZ`, a stała nietknięta ma datę z historii — wychodzi klasa
    „raport nowszy", nie remis.
    """
    zastane = dict(C_PAMIEC)
    try:
        C_PAMIEC["gdzie"] = {"PROBNA_STALA": ["tools/tests/probny.py"]}
        C_PAMIEC["zmienione"] = set()
        C_PAMIEC[("data", "PROBNA_STALA")] = _dt(2026, 9, 11)

        # REMIS: zapadka i raport weszły jednym commitem — raport pisze o NOWEJ wartości.
        C_PAMIEC[("raport", "probny.md")] = _dt(2026, 9, 11)
        przedawnione, powod = zdanie_z_dnia_pomiaru("probny.md", "PROBNA_STALA", "1")
        assert not przedawnione, (
            "REMIS dat zwolnił twierdzenie z pilnowania — a zmierzone 15.09.2026: remis "
            "to 26 twierdzeń ze 101 (ćwierć populacji, dla kształtu `NAZWA = N` ponad "
            f"połowa), z czego rozjechane są DWA. Powód: {powod}")

        # O DOBĘ WCZEŚNIEJ: stała ruszyła PO raporcie — zdanie jest o swoim dniu.
        C_PAMIEC[("raport", "probny.md")] = _dt(2026, 9, 10)
        przedawnione, _ = zdanie_z_dnia_pomiaru("probny.md", "PROBNA_STALA", "1")
        assert przedawnione, (
            "zdanie starsze od stałej PRZESTAŁO być zwalniane — wtedy asercja wyżej "
            "przechodzi dlatego, że mechanizm 6.D108 nie działa wcale, a nie dlatego, "
            "że remis jest pilnowany")

        # O DOBĘ PÓŹNIEJ: raport nowszy — pilnowany, tak samo jak remis.
        C_PAMIEC[("raport", "probny.md")] = _dt(2026, 9, 12)
        przedawnione, _ = zdanie_z_dnia_pomiaru("probny.md", "PROBNA_STALA", "1")
        assert not przedawnione, "raport nowszy od stałej ma być pilnowany"
    finally:
        C_PAMIEC.clear()
        C_PAMIEC.update(zastane)
