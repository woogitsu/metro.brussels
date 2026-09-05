#!/usr/bin/env python3
"""Każdy raport w `reports/` mówi, KIEDY i NA CZYM mierzono.

Raport bez daty i bez commita jest nieodróżnialny od raportu aktualnego. #86
(`4a03982`) przeliczyło kilometraż stacji i wszystko, co z niego wynika — odległości
międzystacyjne, czasy przejazdu, dolne ograniczenia prędkości. Raporty sprzed tej
poprawki nadal leżą w `reports/` i nadal czytają się jak stan bieżący, bo nic
w nagłówku nie mówi, na jakim drzewie ich liczby powstały. Ta bramka pilnuje tego
jednego: **pola się nie gubią i nie gubią się w NOWYCH raportach**.

CZEGO TA BRAMKA NIE ROBI, ŚWIADOMIE. Nie pilnuje, czy liczby w raporcie są aktualne.
Nie da się z tekstu wyczytać, czy `1339/1339 przeszło` jest zdaniem o stanie bieżącym,
czy **cytatem wyjścia polecenia** z dnia pomiaru — a cytatu nie wolno przeliczać, bo
jego wartością jest właśnie to, że pokazuje, co wyszło tamtego dnia. Bramka, która
podmieniałaby takie liczby zbiorczo, psułaby datowane pomiary; zdarzyło się to w tej
sesji dwa razy (`docs/23-environment.md` §2.3 i pierwsza wersja poprawki
w `reports/R-006-line-speed.md`). Rodziny „nieaktualna liczba podana jako stan
bieżący" poprawia się więc ręcznie, po jednym akapicie, i tak też zostały poprawione.

DLACZEGO SHA NIE JEST SPRAWDZANY NA OSIĄGALNOŚĆ. Sprawdzenie `git cat-file -e`
wyglądałoby mocniej, a byłoby czerwone z dwóch niezależnych powodów. Pierwszy:
`actions/checkout` w tym repozytorium chodzi z domyślnym `fetch-depth: 1` (wyjątkiem
jest `prune-merged-branches.yml`), więc na runnerze prawie żaden commit z historii nie
istnieje jako obiekt. Drugi: squash-merge kasuje commity gałęzi, więc raport, który
poprawnie zapisał SHA swojego przebiegu, po scaleniu wskazuje na obiekt, którego już
nie ma — zmierzone: `reports/mutation-triage-lod.md` podaje `c572eb3` i ten SHA nie
rozwiązuje się w `main`. Taki zapis jest nadal poprawnym zapisem historycznym, a nie
usterką higieny, więc bramka sprawdza **kształt pola, nie osiągalność obiektu**.

DLACZEGO NAGŁÓWEK, A NIE CAŁY PLIK. Data gdziekolwiek w treści nie mówi, kiedy
mierzono — `reports/L1_A-geometry.md` i `reports/M7-in-tunnel.md` wymieniały daty
w środku raportu, a nie miały ani jednej w nagłówku. Skan całego pliku uznawał oba
za datowane. Nagłówkiem jest tu tekst przed pierwszym śródtytułem `## `.

KONTROLE NEGATYWNE — wykonane na kopii `reports/` w katalogu tymczasowym, każda
z wypisanym komunikatem, każda MUSI paść:

  1. zdjęta data z `reports/T-113-timetable.md`
     -> raporty bez daty pomiaru w nagłówku: ['T-113-timetable.md']
  2. zdjęty commit z `reports/network-chainage.md`
     -> raporty bez commita pomiaru w nagłówku: ['network-chainage.md']
  3. katalog raportów wskazany na pusty
     -> bramka przeszła tylko 0 raportów, a w `reports/` jest ich co najmniej 40
        (padają wszystkie cztery testy z licznikiem)
  4. NOWY raport bez daty i bez commita — kontrola odwrotnego kierunku
     -> raporty bez daty pomiaru w nagłówku: ['zzz-nowy-pomiar.md']
     -> raporty bez commita pomiaru w nagłówku: ['zzz-nowy-pomiar.md']
  5. nowy raport bez ani jednego `## `, czyli nagłówek = cały plik
     -> raporty bez śródtytułu `## `, w których nagłówek to cały plik:
        ['zzz-bez-srodtytulu.md']
  6. wyjątek na `R-006-line-speed.md` przestał być potrzebny, a został na liście
     -> R-006-line-speed.md ma już commita w nagłówku — zdejmij go z listy wyjątków
  7. do `NOTATIONS` dopisana notacja, której nie używa żaden raport
     -> notacje daty, których nie używa żaden raport: ['RRRR/MM/DD (nikt nie używa)']
  8. do `NOTATIONS` dopisany wzorzec `.?`, czyli łapiący WSZYSTKO
     -> L1_A-chunks.md: wzorzec daty łapie coś po usunięciu wszystkich dat z nagłówka

  9. pięciu raportom zdjęty SHA i dopisany wyjątek z długim powodem, lista 2 -> 7
     (05.09.2026, `6c1048b`) — PRZED zapadką `MAX_COMMIT_EXCEPTIONS` cały moduł
     przechodził na zielono, PO niej pada dokładnie jeden test, ten
     -> lista wyjątków od commita urosła do 7 przy zapadce 2: ['T-113-timetable.md',
        'T-310-physics.md', 'T-311-braking.md', 'T-312-doors.md', 'T-401-line-run.md']
        ponad limit — raport bez commita ma dostać nagłówek, a nie miejsce na liście
 10. zapadka podniesiona „na zapas" do 3 przy dwóch wyjątkach na liście
     -> zapadka 3 stoi wyżej niż lista (2) — obniż ją do stanu faktycznego

Kontrole 7 i 8 są parą i pilnują dwóch przeciwnych sposobów, w które ta bramka mogłaby
udawać pomiar: wzorzec martwy (nie łapie nic, więc niczego nie sprawdza) i wzorzec
zbyt szeroki (łapie wszystko, więc każdy raport „ma datę"). Kontrole 9 i 10 są taką
samą parą dla listy wyjątków: lista rosnąca po cichu i miejsce zrobione na zapas.

DLACZEGO WYJĄTKI, A NIE DOPISANE NAGŁÓWKI — to jest wybór, nie przeoczenie. Dwa
raporty commita nie mają i mieć go nie mogą: `R-006-line-speed.md` mierzono PRZED
commitem, który go wniósł, a `T-401-line-run.md` ma sekcje mierzone na różnych
commitach i każda go nazywa u siebie. Dopisanie im wspólnego SHA byłoby dorobieniem
liczby do formularza — `CLAUDE.md` §4.1 — więc wyjątek jest tu uczciwszy od nagłówka.
Cena za to jest jedna: lista wyjątków musi być **zamknięta**, inaczej wyjątek robi się
tańszym wyjściem niż nagłówek. Zamyka ją `MAX_COMMIT_EXCEPTIONS` i kontrola 9.
"""

import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
REPORTS = os.path.join(ROOT, "reports")

#: Data pomiaru w obu notacjach, których ten repozytorium naprawdę używa. Obie są
#: policzone w `test_konwencja_naglowka_...`, więc notacja, której nikt nie stosuje,
#: nie da się tu wpisać jako „prawda o formacie" bez wywrócenia bramki.
NOTATIONS = {
    "ISO (2026-09-02)": re.compile(r'\b20\d\d-\d\d-\d\d\b'),
    "PL (02.09.2026)": re.compile(r'\b\d\d\.\d\d\.20\d\d\b'),
}

#: Commit, na którym mierzono: skrócony lub pełny SHA w grawisach.
#:
#: Pierwsza wersja odsiewała jeszcze napisy z samych cyfr, w obawie że liczba
#: w grawisach — `1339` z „1339/1339 przeszło" — trafi się jako fałszywy SHA. Filtr
#: był zły w obie strony i to jest zmierzone, nie przewidziane. Za krótkie liczby
#: `{7,40}` odsiewa samo; **skrócony SHA potrafi być z samych cyfr** i dwa takie
#: w tym repozytorium są: `4575195` (`reports/T-012-godot-capture.md`) i `1426940`
#: (`reports/T-211-station-layout.md`). Z filtrem oba raporty raportowały brak
#: commita, mając go w nagłówku. Bez filtru fałszywych trafień nie ma ani jednego:
#: przeskan 44 nagłówków daje 43 tokeny i wszystkie są SHA.
COMMIT = re.compile(r'`([0-9a-f]{7,40})`')

#: Ile raportów musi wpaść do pętli. Bez tego progu wskazanie katalogu na pusty
#: albo literówka w globie dawałyby pustą pętlę i zieloną bramkę. Raportów jest
#: **48** (zmierzone 05.09.2026 na `6c1048b`); liczba 44 stała tu od `839ad78`
#: i przestała być prawdziwa po czterech nowych raportach — jest więc przepisana,
#: a nie dopisana obok. Próg stoi niżej, żeby nie trzeba go było ruszać przy
#: każdym nowym raporcie.
MIN_REPORTS = 40

#: ZAPADKA NA DŁUGOŚĆ LISTY WYJĄTKÓW. Wolno ją tylko OBNIŻAĆ — jak
#: `MINIMUM_DOCUMENTED_ITEMS` w `tools/tests/test_backlog.py`, tylko w drugą stronę.
#:
#: SKĄD SIĘ WZIĘŁA, ZMIERZONE 05.09.2026 na `6c1048b`. Do tej zmiany lista wyjątków
#: nie miała ŻADNEGO ograniczenia rozmiaru, a jedyny test, który ją pilnował
#: (`test_lista_wyjatkow_nie_gnije`), sprawdza po jednym wpisie — czy powód jest
#: dłuższy niż 40 znaków i czy raport nadal pola nie ma. Wpis, który oba te warunki
#: spełnia, przechodził bez względu na to, ilu takich wpisów już jest. Pomiar: sześciu
#: raportom (`T-310-physics.md`, `T-311-braking.md`, `T-312-doors.md`,
#: `T-113-timetable.md`, `M7-shell.md`, `clearance-BE.md`) zdjęty SHA z nagłówka
#: i dopisany wyjątek z długim powodem — **wszystkie osiem testów tego modułu
#: zostało zielonych**, a lista urosła z 2 do 8. Bramka na „każdy raport niesie
#: commit" umiała więc przestać obejmować raporty jeden po drugim i nie powiedzieć
#: o tym ani słowa.
#:
#: Drugie ostrze tego samego: podłoga w `test_konwencja_naglowka_...` liczyła się
#: jako `MIN_REPORTS - len(COMMIT_EXCEPTIONS)`, czyli **malała o jeden z każdym
#: dopisanym wyjątkiem** (38 przy dwóch, 32 przy ośmiu, −8 przy czterdziestu ośmiu).
#: Dziś liczy się od zapadki, więc dopisanie wyjątku podłogi nie obniża.
MAX_COMMIT_EXCEPTIONS = 2

#: To samo dla daty. Zero jest wynikiem pomiaru — każdy raport datę ma — więc
#: zapadka mówi wprost: pierwszy raport bez daty nie prześlizgnie się przez listę
#: wyjątków, tylko dostanie datę albo zatrzyma bramkę.
MAX_DATE_EXCEPTIONS = 0

#: JAWNE WYJĄTKI OD WYMOGU COMMITA. Każdy z powodem, każdy pilnowany przez
#: `test_lista_wyjatkow_nie_gnije` — wyjątek, który przestał być potrzebny, wywraca
#: bramkę, więc lista nie może po cichu rosnąć ani po cichu zostać. Ilu ich może być,
#: mówi `MAX_COMMIT_EXCEPTIONS` i pilnuje `test_lista_wyjatkow_jest_zamknieta`.
COMMIT_EXCEPTIONS = {
    "R-006-line-speed.md":
        "Raport z 02.09.2026 nie zapisał commita pomiaru w chwili powstania, a dziś "
        "nie da się go ustalić bez zgadywania: wniósł go `78fa1f7`, ale pomiar "
        "wykonano PRZED tym commitem, na drzewie, którego raport nie nazywa. "
        "Wpisanie tam czegokolwiek byłoby dorobieniem liczby do formularza.",
    "T-401-line-run.md":
        "Sekcje tego raportu są mierzone na RÓŻNYCH commitach i każda go nazywa: "
        "§2 na `28e0d82`, §4 na `7d15987` (04.09.2026). Jeden SHA w nagłówku "
        "spłaszczyłby dwa różne pomiary do jednego i mówiłby nieprawdę o jednym "
        "z nich; nagłówek odsyła więc do sekcji, a nie udaje wspólnego commita.",
}

#: Wyjątków od wymogu DATY nie ma i to jest wynik pomiaru, nie założenie: po tej
#: zmianie każdy raport w `reports/` podaje datę w nagłówku.
DATE_EXCEPTIONS = {}


def _reports():
    """(nazwa, treść) dla każdego raportu, posortowane."""
    for name in sorted(os.listdir(REPORTS)):
        if not name.endswith(".md"):
            continue
        with open(os.path.join(REPORTS, name), encoding="utf-8") as handle:
            yield name, handle.read()


def _header(text):
    """Tekst przed pierwszym śródtytułem `## ` — tam stoi nagłówek raportu."""
    match = re.search(r'^## ', text, re.M)
    return text[:match.start()] if match else text


def _dates(header):
    return [raw for pattern in NOTATIONS.values() for raw in pattern.findall(header)]


def _commits(header):
    return COMMIT.findall(header)


def test_kazdy_raport_podaje_date_pomiaru():
    """Data gdziekolwiek w treści nie mówi, kiedy mierzono — musi być w nagłówku."""
    missing = []
    checked = 0
    for name, text in _reports():
        checked += 1
        if name in DATE_EXCEPTIONS:
            continue
        if not _dates(_header(text)):
            missing.append(name)
    assert not missing, f"raporty bez daty pomiaru w nagłówku: {missing}"
    assert checked >= MIN_REPORTS, (
        f"bramka przeszła tylko {checked} raportów, a w `reports/` jest ich "
        f"co najmniej {MIN_REPORTS} — skan przestał czytać katalog")


def test_kazdy_raport_podaje_commit_na_ktorym_mierzono():
    """Bez SHA nie da się odtworzyć drzewa, na którym liczby powstały.

    Mutacja, która przed tą bramką przechodziła całą suitę: skasowanie linii
    `**Zmierzone na commicie:**` z dowolnego z 32 raportów, które ją dostały.
    """
    missing = []
    checked = 0
    for name, text in _reports():
        checked += 1
        if name in COMMIT_EXCEPTIONS:
            continue
        if not _commits(_header(text)):
            missing.append(name)
    assert not missing, f"raporty bez commita pomiaru w nagłówku: {missing}"
    assert checked >= MIN_REPORTS, (
        f"bramka przeszła tylko {checked} raportów, a w `reports/` jest ich "
        f"co najmniej {MIN_REPORTS} — skan przestał czytać katalog")


def test_konwencja_naglowka_jest_wyczytana_z_raportow_ktore_ja_juz_maja():
    """Bramka nie trzyma DRUGIEJ LISTY tego, jak wygląda nagłówek.

    Prawdę o formacie bierze z raportów, które datę i commit już mają, i sprawdza
    na nich dwie rzeczy naraz:

    - każda notacja daty, którą bramka zna, jest przez jakiś raport UŻYWANA — notacja
      martwa udawałaby prawdę o formacie, nie będąc nią;
    - usunięcie pola z prawdziwego nagłówka **przestaje przechodzić** kontrolę. To jest
      kontrola negatywna wpisana w bramkę: wzorzec, który łapie wszystko, wywraca ten
      test, a wzorzec, który nie łapie nic, wywraca dwa poprzednie.
    """
    usage = {label: 0 for label in NOTATIONS}
    reference = []
    checked = 0
    for name, text in _reports():
        checked += 1
        header = _header(text)
        for label, pattern in NOTATIONS.items():
            if pattern.search(header):
                usage[label] += 1
        if _dates(header) and _commits(header):
            reference.append((name, header))
    assert checked >= MIN_REPORTS, f"tylko {checked} raportów w pętli"
    unused = [label for label, count in usage.items() if count == 0]
    assert not unused, f"notacje daty, których nie używa żaden raport: {unused}"
    # PODŁOGA LICZY SIĘ OD ZAPADKI, NIE OD DŁUGOŚCI LISTY. Z `len(COMMIT_EXCEPTIONS)`
    # malała o jeden przy każdym dopisanym wyjątku, czyli sama sobie ustępowała:
    # zmierzone 05.09.2026 — 38 przy dwóch wyjątkach, 32 przy ośmiu.
    assert len(reference) >= MIN_REPORTS - MAX_COMMIT_EXCEPTIONS, (
        f"tylko {len(reference)} raportów ma oba pola — konwencja, którą bramka "
        "czyta z repozytorium, przestała być konwencją")
    for name, header in reference:
        bez_daty = header
        for pattern in NOTATIONS.values():
            bez_daty = pattern.sub("", bez_daty)
        assert not _dates(bez_daty), (
            f"{name}: wzorzec daty łapie coś po usunięciu wszystkich dat z nagłówka")
        assert not _commits(COMMIT.sub("", header)), (
            f"{name}: wzorzec commita łapie coś po usunięciu wszystkich SHA")


def test_data_i_commit_stoja_w_naglowku_a_nie_gdziekolwiek_w_raporcie():
    """Nagłówek musi być WĘŻSZY niż plik, inaczej bramka cicho robi się skanem całości.

    Raport bez ani jednego śródtytułu `## ` daje nagłówek równy całej treści —
    i wtedy data wspomniana w §9 „co zauważyłem" liczyłaby się jak data pomiaru.
    """
    bez_srodtytulu = []
    checked = 0
    for name, text in _reports():
        checked += 1
        if len(_header(text)) >= len(text):
            bez_srodtytulu.append(name)
    assert not bez_srodtytulu, (
        f"raporty bez śródtytułu `## `, w których nagłówek to cały plik: "
        f"{bez_srodtytulu}")
    assert checked >= MIN_REPORTS, f"tylko {checked} raportów w pętli"


def test_lista_wyjatkow_nie_gnije():
    """Wyjątek, który przestał być potrzebny, musi z listy ZNIKNĄĆ.

    Bez tego testu lista wyjątków jest miejscem, w którym raport bez nagłówka
    przeżywa na zawsze: dopisanie się na nią kosztuje jedną linijkę, a zdjęcie
    z niej nie kosztuje nic, więc nikt tego nie robi.
    """
    existing = {name for name, _text in _reports()}
    checked = 0
    for table, reader, what in ((COMMIT_EXCEPTIONS, _commits, "commita"),
                                (DATE_EXCEPTIONS, _dates, "daty")):
        for name, reason in table.items():
            checked += 1
            assert name in existing, f"wyjątek na {name} — takiego raportu nie ma"
            assert len(reason) > 40, f"wyjątek na {name} bez powodu: {reason!r}"
            # POWÓD NIE MOŻE OBIECYWAĆ WŁASNEGO USUNIĘCIA, i to jest usterka
            # zmierzona na tej bramce, nie ostrożność. Oba pierwotne wyjątki brzmiały
            # „gałąź w locie przepisuje ten nagłówek, wyjątek do zdjęcia po scaleniu".
            # Gałąź (#195) scaliła się 04.09.2026 — a asercja niżej sprawdza tylko,
            # czy plik JUŻ MA pole. Nie ma, bo nikt go nie dopisał, więc wyjątek
            # zostawał uzasadniony na zawsze przez powód, który dawno wygasł.
            # Bramka nie umie dopilnować obietnicy, więc jej nie przyjmuje: powód
            # musi opisywać stan TRWAŁY, taki jak „raport nie zapisał commita
            # i nie da się go dziś ustalić" albo „sekcje mierzono na różnych".
            obietnice = ("po scaleniu", "do zdjęcia", "w locie", "gałęzi w locie",
                         "tymczasow", "na razie", "docelowo")
            znalezione = [f for f in obietnice if f in reason.lower()]
            assert not znalezione, (
                f"wyjątek na {name} uzasadnia się obietnicą {znalezione} — bramka nie "
                "umie sprawdzić, czy obietnica została dotrzymana, więc powód musi "
                "opisywać stan trwały")
            with open(os.path.join(REPORTS, name), encoding="utf-8") as handle:
                header = _header(handle.read())
            assert not reader(header), (
                f"{name} ma już {what} w nagłówku — zdejmij go z listy wyjątków")
    assert checked == len(COMMIT_EXCEPTIONS) + len(DATE_EXCEPTIONS)


def test_lista_wyjatkow_jest_zamknieta():
    """Lista wyjątków ma ROZMIAR, nie tylko wpisy — inaczej rośnie po cichu.

    `test_lista_wyjatkow_nie_gnije` ogląda każdy wpis OSOBNO: powód dłuższy niż 40
    znaków, bez obietnicy własnego usunięcia, raport nadal bez pola. Wpis spełniający
    te trzy warunki przechodził niezależnie od tego, ilu takich wpisów już jest —
    a wyjątek jest tańszy niż nagłówek, więc lista rośnie w jedną stronę z definicji.

    KONTROLA NEGATYWNA WYKONANA 05.09.2026 na `6c1048b`: pięciu raportom zdjęty SHA
    z nagłówka i dopisany wyjątek z długim powodem, lista 2 -> 7. PRZED tą zapadką
    komplet testów modułu był zielony przy takiej mutacji — zmierzone, nie
    przewidziane. PO niej pada ten jeden test i tylko on:

        lista wyjątków od commita urosła do 7 przy zapadce 2: ['T-113-timetable.md',
        'T-310-physics.md', 'T-311-braking.md', 'T-312-doors.md', 'T-401-line-run.md']
        ponad limit — raport bez commita ma dostać nagłówek, a nie miejsce na liście

    Zapadkę wolno tylko OBNIŻAĆ. Podniesienie jej jest widoczną zmianą stałej w diffie
    i wymaga powodu tam, gdzie powody tego repozytorium stoją — w treści commita —
    a nie jednej dopisanej linijki w słowniku.
    """
    assert len(COMMIT_EXCEPTIONS) <= MAX_COMMIT_EXCEPTIONS, (
        f"lista wyjątków od commita urosła do {len(COMMIT_EXCEPTIONS)} przy zapadce "
        f"{MAX_COMMIT_EXCEPTIONS}: {sorted(COMMIT_EXCEPTIONS)[MAX_COMMIT_EXCEPTIONS:]} "
        "ponad limit — raport bez commita ma dostać nagłówek, a nie miejsce na liście")
    assert len(DATE_EXCEPTIONS) <= MAX_DATE_EXCEPTIONS, (
        f"lista wyjątków od daty urosła do {len(DATE_EXCEPTIONS)} przy zapadce "
        f"{MAX_DATE_EXCEPTIONS}: {sorted(DATE_EXCEPTIONS)} — daty da się ustalić "
        "dla każdego raportu, więc wyjątku od niej nie ma")
    # ZAPADKA NIE MOŻE STAĆ WYŻEJ, NIŻ POTRZEBA. Gdyby wolno jej było wyprzedzać
    # listę, podniesienie „na zapas" otwierałoby miejsce na przyszłe wyjątki bez
    # ani jednego raportu, który by ich potrzebował — czyli dokładnie ta cicha
    # rezerwa, której ta bramka ma nie dopuszczać.
    assert MAX_COMMIT_EXCEPTIONS == len(COMMIT_EXCEPTIONS), (
        f"zapadka {MAX_COMMIT_EXCEPTIONS} stoi wyżej niż lista "
        f"({len(COMMIT_EXCEPTIONS)}) — obniż ją do stanu faktycznego")
    assert MAX_DATE_EXCEPTIONS == len(DATE_EXCEPTIONS), (
        f"zapadka {MAX_DATE_EXCEPTIONS} stoi wyżej niż lista "
        f"({len(DATE_EXCEPTIONS)}) — obniż ją do stanu faktycznego")
    # Podłoga w `test_konwencja_naglowka_...` liczy się od zapadki, więc zapadka
    # równa MIN_REPORTS zdjęłaby tamtą kontrolę do zera. Ten limit mówi, że wyjątek
    # jest wyjątkiem: najwyżej co dziesiąty raport przy dzisiejszym progu.
    assert MAX_COMMIT_EXCEPTIONS + MAX_DATE_EXCEPTIONS <= MIN_REPORTS // 10, (
        f"zapadki wyjątków ({MAX_COMMIT_EXCEPTIONS} + {MAX_DATE_EXCEPTIONS}) sięgają "
        f"dziesiątej części progu {MIN_REPORTS} — wyjątek przestaje być wyjątkiem")


# --- ścieżka w raporcie musi wskazywać na plik, który istnieje --------------------

#: DLACZEGO TO JEST W TYM MODULE, A NIE NOWY.
#:
#: Docstring wyżej mówi, czego ta bramka świadomie NIE robi: nie pilnuje, czy liczby
#: w raporcie są aktualne, bo z tekstu nie da się odróżnić cytatu wyjścia polecenia od
#: zdania o stanie bieżącym. **Ścieżka nie jest liczbą i tej dwuznaczności nie ma.**
#: `src/Sim/Line/LineDrive.cs` albo się rozwiązuje, albo nie, i sprawdza to system
#: plików, a nie druga lista w teście.
#:
#: SKĄD SIĘ WZIĘŁO. Zmierzone 05.09.2026 na `9f4ae98`, skan 48 raportów: dokładnie
#: jedna ścieżka nie rozwiązywała się w drzewie — `reports/T-400-stage-3b.md` §1
#: wymieniało w tabeli zmian `src/Sim/Line/LineDrive.cs`, podczas gdy plik od chwili
#: powstania (`90a8c31`, T-320) leży w `src/Sim/Train/`. `git log --follow` nie
#: pokazuje ani jednego przeniesienia, więc nie jest to zapis historyczny — to była
#: literówka, prawdziwa już w dniu pomiaru, i przeżyła przegląd PR-a, bo nazwa pliku
#: się zgadzała, a katalog wyglądał sensownie (`Line/` obok `LineDrive`).
#:
#: DLACZEGO SYGNAŁ JEST CZYSTY. Jedno trafienie na 48 plików i ~1500 tokenów w
#: grawisach. Wzorzec bierze wyłącznie tokeny z ukośnikiem i ze znanym rozszerzeniem,
#: więc `sweep.max_deviation` czy `docs/24` przez niego nie przechodzą.
PATH_TOKEN = re.compile(r'`([A-Za-z0-9_][A-Za-z0-9_./-]*\.'
                        r'(?:py|cs|md|json|sh|yml|yaml|txt|csproj|tscn|geojson|csv))`')

#: Przedrostki, których nie ma po co sprawdzać: wytwory przebiegu (reguła 8 zabrania
#: ich komitować, więc ich BRAK jest stanem poprawnym), ścieżki Godota, katalogi
#: tymczasowe i adresy.
IGNORED_PREFIXES = ("build/", "renders/", "res://", "/tmp/", "http://", "https://",
                    "/opt/", "/usr/", "~/")

#: JAWNE WYJĄTKI: ścieżki, które w raporcie stoją słusznie, choć w drzewie ich nie ma.
#: Pusto — i to jest wynik pomiaru, nie założenie. Gdy pierwszy raport będzie musiał
#: nazwać plik skasowany albo przemianowany, wyjątek wchodzi tutaj z powodem, tak samo
#: jak `COMMIT_EXCEPTIONS` wyżej, i tak samo pilnowany przez test „nie gnije".
PATH_EXCEPTIONS = {}


def _paths_in(text):
    """Ścieżki repozytoryjne wymienione w grawisach: `(token, numer wiersza)`."""
    for number, line in enumerate(text.splitlines(), 1):
        for token in PATH_TOKEN.findall(line):
            if "/" not in token or token.startswith(IGNORED_PREFIXES):
                continue
            yield token, number


def test_kazda_sciezka_wymieniona_w_raporcie_rozwiazuje_sie_w_drzewie():
    """Raport, który nazywa nieistniejący plik, wysyła czytelnika w puste miejsce.

    Kontrola negatywna WYKONANA 05.09.2026, na kopii katalogu w `/tmp` (opis metody
    niżej, w teście detektora): po przywróceniu w `reports/T-400-stage-3b.md`
    poprzedniego zapisu `src/Sim/Line/LineDrive.cs` ten test pada komunikatem

        ścieżki, których nie ma w drzewie:
        ['T-400-stage-3b.md:92: `src/Sim/Line/LineDrive.cs`']
    """
    missing = []
    checked = 0
    seen = 0
    for name, text in _reports():
        checked += 1
        for token, number in _paths_in(text):
            seen += 1
            if token in PATH_EXCEPTIONS:
                continue
            if not os.path.exists(os.path.join(ROOT, token)):
                missing.append(f"{name}:{number}: `{token}`")
    assert not missing, f"ścieżki, których nie ma w drzewie: {missing}"
    assert checked >= MIN_REPORTS, (
        f"bramka przeszła tylko {checked} raportów, a w `reports/` jest ich "
        f"co najmniej {MIN_REPORTS} — skan przestał czytać katalog")
    # Bez tego progu literówka we WZORCU dawałaby zero tokenów, zero braków i zieloną
    # bramkę. Zmierzone 05.09.2026: 623 trafienia w 48 raportach; próg stoi niżej,
    # żeby nie trzeba go było ruszać przy każdym nowym raporcie.
    assert seen >= 500, (
        f"wzorzec znalazł tylko {seen} ścieżek w {checked} raportach — przestał łapać")


def test_wzorzec_sciezki_lapie_to_co_ma_i_nie_lapie_prozy():
    """Kontrola detektora: bez niej test wyżej byłby zielony także przy martwym wzorcu.

    Cztery pary, każda z powodem — po jednej na sposób, w jaki ten wzorzec mógłby
    cicho przestać być pomiarem.
    """
    def found(line):
        return [t for t, _n in _paths_in(line)]

    # 1. Ścieżka repozytoryjna — musi wejść.
    assert found("zmiana w `src/Sim/Train/LineDrive.cs` i nic więcej") == [
        "src/Sim/Train/LineDrive.cs"]
    # 2. Kwalifikowana nazwa w kodzie NIE jest ścieżką — brak ukośnika.
    assert found("`sweep.max_deviation` i `lod.lod_plan`") == []
    # 3. Wytwór przebiegu NIE jest brakiem — reguła 8 zabrania go komitować.
    assert found("artefakt `build/t400/scene-line.log`") == []
    # 4. Odsyłacz bez rozszerzenia nie jest ścieżką pliku.
    assert found("patrz `docs/24` i `tools/ci`") == []


def test_lista_wyjatkow_od_sciezek_nie_gnije():
    """Wyjątek, który przestał być potrzebny, musi z listy ZNIKNĄĆ — jak wyżej.

    Dziś lista jest pusta i ten test to sprawdza wprost: pusta lista jest wynikiem
    pomiaru („żaden raport nie potrzebuje wyjątku"), a nie miejscem, w którym nic
    jeszcze nie zdążyło się nazbierać.
    """
    for token, reason in PATH_EXCEPTIONS.items():
        assert len(reason) > 40, f"wyjątek na {token} bez powodu: {reason!r}"
        assert not os.path.exists(os.path.join(ROOT, token)), (
            f"`{token}` już istnieje — zdejmij go z listy wyjątków")
    assert isinstance(PATH_EXCEPTIONS, dict)
