#!/usr/bin/env python3
"""Kryterium wejścia do Mapy dokumentów w `CLAUDE.md` §3 — i to, czego pomiar NIE znalazł.

**Odpowiedź na pytanie pozycji 6.D170 jest przecząca i to jest wynik, nie porażka.**
Pozycja pytała, jakie kryterium wpuszcza dokument do Mapy. Zmierzone 18.09.2026 na
`94953f3`: **żadna własność mierzalna z drzewa nie dzieli czternastu dokumentów
z tabeli od dwunastu stojących poza nią.** Cztery kandydatury, każda policzona na
całym `docs/`:

    cytowany w `CLAUDE.md` POZA §3       w tabeli 9/14   poza tabelą  0/12
    cytowany w `.claude/skills/`          w tabeli 4/14   poza tabelą  0/12
    cytowany w `tools/tests/*.py`         w tabeli 12/14  poza tabelą  6/12
    cytowany w innym `docs/*.md`          w tabeli 14/14  poza tabelą 10/12

Rozdziela podział wyłącznie **przedział numerów w nazwie pliku** — w tabeli stoi
wszystko o numerze najwyżej siódmym, wszystko o numerze co najmniej dwudziestym
drugim i wszystko bez numeru; poza nią cały przedział od ósmego do dwudziestego
pierwszego, zero niezgodności na dwadzieścia sześć plików. **To nie jest kryterium,
tylko opis numeracji**, i pomiar pokazuje, dlaczego:

* **nie jest chronologiczny** — `docs/22-heartbeat.md` powstał 01.09.2026, tego samego
  dnia co `08`, `09`, `17` i `21`, a `23` i `24` powstały 03.09.2026, czyli PO nich;
  numer nie idzie za datą;
* **nie jest tematyczny** — po dwa kontrprzykłady w każdą stronę:
  `24-clearance-profile-decisions.md` jest dokumentem faktów o dziedzinie i stoi
  W tabeli, `08-m7-ground-truth.md` jest tym samym gatunkiem i stoi POZA; odwrotnie
  `22-heartbeat.md` jest dokumentem procesu i stoi W tabeli, a `17-visual-regression.md`
  i `21-measured-vs-assumed.md` też są o procesie i stoją POZA;
* **numeracja ma dziurę** — `docs/13-*` i `docs/14-*` nie istniały NIGDY (sprawdzone
  `git log --all --diff-filter=A`), a żaden plik `docs/*.md` nie został nigdy usunięty.
  Reguła „przedział ósmy–dwudziesty pierwszy stoi poza Mapą" przypisałaby więc przyszły
  `docs/13-…` do strony, której nikt nie wybrał — czyli robiłaby dokładnie to, przed
  czym pozycja 6.D170 ostrzega.

**Czego ta bramka NIE robi.** Nie zgaduje kryterium z treści dokumentu. Bramka na
kształcie („dokument gatunku ground truth należy do Mapy") zapalałaby się dziś na
dokumentach poprawnych — czyli byłaby bramką z 6.D27, wyłączaną zamiast naprawianą.
Skład Mapy jest wyborem właściciela i tu nie jest zmieniany.

**Co ta bramka robi zamiast tego — dwie rzeczy, obie zmierzone, nie wymyślone.**

1. **Przypisanie ma być KOMPLETNE.** Każdy plik `docs/*.md` stoi albo w tabeli §3,
   albo w zbiorze `POZA_MAPA` niżej. Plik bez przypisania zapala czerwień i zostaje
   nazwany — to jest ta połowa, której żądało pole „Skończone, gdy" pozycji.
2. **Cytowanie pociąga za sobą wpis.** Dokument, na który powołuje się którykolwiek
   punkt `CLAUDE.md` POZA §3, musi stać w tabeli. Zmierzone 18.09.2026: spełniają to
   dziś **wszystkie dwanaście** dokumentów spoza tabeli, ani jednego kontrprzykładu.
   To warunek WYSTARCZAJĄCY, nie konieczny — pięć dokumentów w tabeli (`02`, `05`,
   `22`, `23`, `24`) nie jest cytowanych nigdzie poza §3 i to jest w porządku:
   reguła mówi „cytujesz, więc wpisz", a nie „nie cytujesz, więc wypisz".

Pełny pomiar: `reports/6d170-kryterium-wejscia-do-mapy.md`.
"""

import os
import re
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tree_walk as TW  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
KONSTYTUCJA = os.path.join(ROOT, "CLAUDE.md")
DOCS = os.path.join(ROOT, "docs")

#: Nagłówek sekcji i nagłówek następnej — granice §3 czytane z pliku, a nie z pamięci.
NAGLOWEK_3 = "## 3. Mapa dokumentów"
NAGLOWEK_4 = "\n## 4."

#: Ścieżka w pierwszej kolumnie wiersza tabeli: `| `docs/00-….md` | opis |`.
WIERSZ_TABELI = re.compile(r"\|\s*`([^`]+)`\s*\|")

#: Zdanie, które musi stać w §3, żeby reguła nie zniknęła po cichu razem z bramką.
#: Sprawdzana jest KOTWICA, a nie całe brzmienie: bramka pilnująca każdego słowa
#: zapalałaby się przy poprawianiu przecinka, a to jest bramka z 6.D27.
KOTWICA_KRYTERIUM = "świadomie poza Mapą"

#: Dwanaście dokumentów `docs/*.md`, które 18.09.2026 stały POZA tabelą §3.
#:
#: POWÓD JEST DLA WSZYSTKICH DWUNASTU TEN SAM i dlatego stoi raz, a nie dwanaście
#: razy: skład Mapy jest wyborem właściciela, a te dwanaście w niej tego dnia nie
#: było. Lista wyjątków z dwunastoma identycznymi podpisami byłaby podpisem, a nie
#: informacją — to klasa usterki, którą projekt tropi od 6.D27.
#:
#: CO TEN ZBIÓR NIESIE PONAD SAMĄ NAZWĘ: żaden z tych dwunastu nie jest cytowany
#: w `CLAUDE.md` poza §3 i pilnuje tego osobny test niżej. Wpis w tym zbiorze jest
#: więc twierdzeniem sprawdzalnym, a nie deklaracją.
#:
#: Pozycja 6.D170 NIE przenosi żadnego z nich do Mapy. Wiersz `| 6.D170 |` zauważa,
#: że pięć z nich (`08`, `09`, `10`, `11`, `12`) to dokumenty gatunku „ground truth",
#: czyli ten sam gatunek co `docs/00`, który §3 nazywa źródłem prawdy — i to jest
#: pytanie do właściciela, postawione w raporcie, a nie zmiana zrobiona po cichu.
POZA_MAPA = frozenset({
    "docs/08-m7-ground-truth.md",
    "docs/09-data-provenance.md",
    "docs/10-signalling-ground-truth.md",
    "docs/11-station-ground-truth.md",
    "docs/12-infrastructure-ground-truth.md",
    "docs/15-classic-signalling.md",
    "docs/16-protection-modes.md",
    "docs/17-visual-regression.md",
    "docs/18-rights-matrix.md",
    "docs/19-audio-rights-and-recording.md",
    "docs/20-art-direction.md",
    "docs/21-measured-vs-assumed.md",
})

#: Ile plików `.md` ma `docs/`. PODŁOGA, nie równość: nowy dokument ma podnosić tę
#: liczbę razem z przypisaniem, a nie zapalać bramkę samym swoim istnieniem.
#: Zmierzone 18.09.2026 na `94953f3`.
MIN_DOKUMENTOW = 26

#: Ile wierszy ma tabela §3 RAZEM z dwoma z `data/`. Przybite równością, bo ubytek
#: wiersza jest tu usterką tak samo jak przyrost bez przypisania.
# 16 (18.09.2026, 6.D170): pomiar pierwszy, czternaście z `docs/` i dwa z `data/`.
WIERSZY_W_MAPIE = 16


def _konstytucja():
    with open(KONSTYTUCJA, encoding="utf-8") as uchwyt:
        return uchwyt.read()


def sekcja_mapy(tekst=None):
    """Treść §3, od nagłówka Mapy do nagłówka §4."""
    tekst = _konstytucja() if tekst is None else tekst
    assert NAGLOWEK_3 in tekst, "w CLAUDE.md nie ma nagłówka Mapy dokumentów"
    ogon = tekst.split(NAGLOWEK_3, 1)[1]
    assert NAGLOWEK_4 in ogon, "w CLAUDE.md nie ma nagłówka §4 po Mapie"
    return ogon.split(NAGLOWEK_4, 1)[0]


def wiersze_mapy(tekst=None):
    """Wszystkie ścieżki z pierwszej kolumny tabeli §3, w kolejności z pliku."""
    return WIERSZ_TABELI.findall(sekcja_mapy(tekst))


def mapa_docs(tekst=None):
    """Same dokumenty `docs/` z tabeli — bez dwóch wpisów z `data/`."""
    return {p for p in wiersze_mapy(tekst) if p.startswith("docs/")}


def dokumenty_w_docs(root=ROOT):
    """Pliki `.md` leżące BEZPOŚREDNIO w `docs/`, ścieżkami względem korzenia.

    Bezpośrednio, bo tabela §3 wymienia pliki, a nie drzewo, i pole „Weryfikacja"
    pozycji liczy je wzorcem `docs/*.md`. Przejście idzie przez `TW.znajdz`, żeby
    nie było czwartego kształtu chodzenia po drzewie (6.D74, 6.D97, 6.D117).
    """
    katalog = os.path.join(root, "docs")
    znalezione = TW.znajdz(katalog, "*.md", root)
    wzgledne = {os.path.relpath(p, root).replace(os.sep, "/") for p in znalezione}
    return {p for p in wzgledne if p.count("/") == 1}


def poza_paragrafem_3(tekst=None):
    """Treść `CLAUDE.md` z WYCIĘTĄ sekcją §3."""
    tekst = _konstytucja() if tekst is None else tekst
    return tekst.replace(sekcja_mapy(tekst), "")


def cytowane_poza_mapa(tekst=None):
    """Dokumenty `docs/`, na które powołuje się `CLAUDE.md` poza §3."""
    reszta = poza_paragrafem_3(tekst)
    return {p for p in dokumenty_w_docs() if p in reszta}


def test_przyrzad_naprawde_czyta_tabele():
    """Kontrola przyrządu: bramka zielona na zerze trafień nic nie mierzy."""
    assert len(wiersze_mapy()) == WIERSZY_W_MAPIE, (
        "tabela §3 ma %d wierszy, a pomiar z 18.09.2026 dał %d — zmienił się skład "
        "Mapy albo czytnik przestał ją czytać" % (len(wiersze_mapy()), WIERSZY_W_MAPIE))
    assert len(dokumenty_w_docs()) >= MIN_DOKUMENTOW, (
        "w docs/ jest %d plików .md przy podłodze %d — któryś zniknął albo skan "
        "przestał czytać katalog" % (len(dokumenty_w_docs()), MIN_DOKUMENTOW))


def test_kazdy_dokument_docs_stoi_po_jednej_ze_stron():
    """Połowa pola „Skończone, gdy" 6.D170: przypisanie ma być KOMPLETNE."""
    przypisane = mapa_docs() | POZA_MAPA
    nieprzypisane = sorted(dokumenty_w_docs() - przypisane)
    assert not nieprzypisane, (
        "te pliki docs/ nie stoją ani w tabeli CLAUDE.md §3, ani w POZA_MAPA: %s "
        "— dopisz je do jednej ze stron w tym samym commicie, w którym powstały"
        % nieprzypisane)


def test_zadna_strona_nie_wymienia_pliku_ktorego_nie_ma():
    """Druga strona tej samej reguły — przypisanie nie ma być SZERSZE od drzewa."""
    widma = sorted(przypisane for przypisane in (mapa_docs() | POZA_MAPA)
                   if przypisane not in dokumenty_w_docs())
    assert not widma, (
        "te ścieżki są przypisane, ale w drzewie ich nie ma: %s" % widma)


def test_zbiory_sa_rozlaczne():
    """Dokument nie może stać po obu stronach naraz."""
    obie = sorted(mapa_docs() & POZA_MAPA)
    assert not obie, (
        "te dokumenty stoją i w tabeli §3, i w POZA_MAPA: %s — jedna ze stron jest "
        "nieaktualna" % obie)


def test_cytowanie_w_konstytucji_pociaga_za_soba_wpis_do_mapy():
    """Zmierzone 18.09.2026: dwanaście z dwunastu, ani jednego kontrprzykładu."""
    cytowane = cytowane_poza_mapa()
    zle = sorted(cytowane & POZA_MAPA)
    assert not zle, (
        "CLAUDE.md powołuje się poza §3 na dokumenty, których w Mapie NIE MA: %s "
        "— albo wpisz je do tabeli §3, albo nie odsyłaj do nich z konstytucji"
        % zle)
    assert cytowane, (
        "wzorzec nie znalazł ANI JEDNEGO dokumentu cytowanego poza §3 — czytnik "
        "przestał czytać CLAUDE.md, a bramka na zerze trafień nic nie mierzy")


def test_kryterium_stoi_w_konstytucji_a_nie_tylko_w_tej_bramce():
    """Reguła zapisana wyłącznie w teście znika razem z testem."""
    assert KOTWICA_KRYTERIUM in sekcja_mapy(), (
        "w CLAUDE.md §3 nie ma zdania o kryterium (kotwica %r) — reguła stoi wtedy "
        "tylko w tym pliku i czytający konstytucję o niej nie wie"
        % KOTWICA_KRYTERIUM)


def test_reguly_reaguja_na_obie_polowy_swojego_warunku():
    """Kontrola negatywna WBUDOWANA, na tekście podstawionym, nie na drzewie.

    Bez niej trzy testy wyżej są zielone także wtedy, gdy czytnik `mapa_docs`
    zwraca pusty zbiór — a wtedy „wszystko przypisane" znaczy „nic nie sprawdzono".
    """
    udawana = ("## 3. Mapa dokumentów\n\n| plik | do czego |\n|---|---|\n"
               "| `docs/00-network-data.md` | fakty |\n\nświadomie poza Mapą\n"
               "\n## 4. Twarde reguły\n")
    assert mapa_docs(udawana) == {"docs/00-network-data.md"}, (
        "czytnik tabeli na podstawionym §3 zwrócił %s zamiast jednego wiersza"
        % sorted(mapa_docs(udawana)))
    assert KOTWICA_KRYTERIUM in sekcja_mapy(udawana), (
        "czytnik §3 zgubił kotwicę kryterium na tekście, który ją ma")

    bez_kotwicy = udawana.replace(KOTWICA_KRYTERIUM, "cokolwiek innego")
    assert KOTWICA_KRYTERIUM not in sekcja_mapy(bez_kotwicy), (
        "czytnik §3 widzi kotwicę w tekście, z którego została usunięta — test "
        "kryterium byłby wtedy zielony zawsze")

    # Cytat spoza §3 jest widziany, a cytat WEWNĄTRZ §3 — nie. To jest cała
    # różnica, na której stoi reguła „cytujesz, więc wpisz".
    assert "docs/00-network-data.md" not in poza_paragrafem_3(udawana), (
        "wycięcie §3 zostawiło w tekście ścieżkę z tabeli — reguła o cytowaniu "
        "zapalałaby się na każdym wierszu Mapy")
    z_cytatem = udawana + "\nPatrz `docs/00-network-data.md`.\n"
    assert "docs/00-network-data.md" in poza_paragrafem_3(z_cytatem), (
        "wycięcie §3 usunęło też cytat spoza §3 — reguła o cytowaniu nie "
        "zapaliłaby się nigdy")


# 6.D25: uruchomienie tego pliku WPROST idzie ta sama droga, co caly zestaw —
# z licznikiem asercji i z odmowa przy zerze testow.
if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))
