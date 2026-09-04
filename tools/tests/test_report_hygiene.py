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

Kontrole 7 i 8 są parą i pilnują dwóch przeciwnych sposobów, w które ta bramka mogłaby
udawać pomiar: wzorzec martwy (nie łapie nic, więc niczego nie sprawdza) i wzorzec
zbyt szeroki (łapie wszystko, więc każdy raport „ma datę").
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
#: albo literówka w globie dawałyby pustą pętlę i zieloną bramkę. Dziś raportów
#: jest 44; próg stoi niżej, żeby nie trzeba go było ruszać przy każdym nowym.
MIN_REPORTS = 40

#: JAWNE WYJĄTKI OD WYMOGU COMMITA. Każdy z powodem, każdy pilnowany przez
#: `test_lista_wyjatkow_nie_gnije` — wyjątek, który przestał być potrzebny, wywraca
#: bramkę, więc lista nie może po cichu rosnąć ani po cichu zostać.
COMMIT_EXCEPTIONS = {
    "R-006-line-speed.md":
        "Nagłówek jest przepisywany na gałęzi w locie (poprawka cytatu dolnego "
        "ograniczenia prędkości); dopisanie commita tutaj dałoby konflikt. "
        "Wyjątek do zdjęcia razem ze scaleniem tej gałęzi.",
    "T-401-line-run.md":
        "Ten sam powód: `t401-cytowanie-bez-dryfu` przepisuje §2 i §4 tego raportu. "
        "SHA w treści raport ma, w nagłówku nie; wyjątek do zdjęcia po scaleniu.",
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
    assert len(reference) >= MIN_REPORTS - len(COMMIT_EXCEPTIONS), (
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
            with open(os.path.join(REPORTS, name), encoding="utf-8") as handle:
                header = _header(handle.read())
            assert not reader(header), (
                f"{name} ma już {what} w nagłówku — zdejmij go z listy wyjątków")
    assert checked == len(COMMIT_EXCEPTIONS) + len(DATE_EXCEPTIONS)
