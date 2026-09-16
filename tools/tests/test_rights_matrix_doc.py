#!/usr/bin/env python3
"""Pakiet A dzieł sztuki: `data/legal/rights-matrix.json` a `docs/18-rights-matrix.md`.

**Po co ta bramka istnieje — i to jest pomiar, nie przypuszczenie.** `docs/18-rights-matrix.md`
jest dziś otwierany podczas przebiegu zestawu **21 razy, przez siedem modułów**
(`test_bin_path_framework`, `test_conflict_markers`, `test_docs_ci_claims`,
`test_field_paths`, `test_mass_copies`, `test_runner_options`, `test_t401_citation`) —
zmierzone 16.09.2026 hakiem audytu `sys.addaudithook` na zdarzeniu `open` w pełnym
przebiegu `test_all.py`. **Ani jedno z tych otwarć nie czyta go jako macierzy praw.**
Każde jest przemiataniem CAŁEGO drzewa: te moduły otwierają odpowiednio 387, 847, 397,
78, 642, 815 i 568 plików, w tym 385, 394, 387, 26, 385, 394 i 387 plików `.md`, i szukają
w nich znaczników konfliktu, nieistniejących ścieżek, etykiet runnera, gołych nazw pól,
kopii mas, formy `--opcja=wartosc` i cytowań progu T-401. Dla każdego z nich doc18 jest
jednym plikiem tekstowym z prawie czterystu.

**Czyli: tabela „Dzieła sztuki — pakiet A" w doc18 nie ma dziś ani jednego czytelnika
maszynowego.** Jest to ten sam kształt, co 6.D27: przebieg melduje zielone sprawdzenie
drzewa, w którym ta tabela nie została sprawdzona ani razu. Rozjazd między rejestrem
maszynowym a dokumentem, do którego `docs/03-legal.md` odsyła człowieka podejmującego
decyzję, przeszedłby więc niezauważony — a doc18 sam kończy się zdaniem, że **brak wpisu
jest traktowany jak `excluded_until_cleared`**. Wpis, który zniknął z jednej z dwóch
stron, zmienia znaczenie tego zdania po cichu.

**Czego ta bramka NIE robi, świadomie.** Nie rozstrzyga niczego o prawach autorskich
i nie ocenia, czy wolno cokolwiek zreprodukować. Pilnuje wyłącznie **spójności zapisu**
między `data/` a doc18: czy oba dokumenty mówią o tym samym zbiorze osiemnastu pozycji.
Status prawny każdej pozycji zostaje tam, gdzie jest — w `data/legal/rights-matrix.json`
i w `docs/03-legal.md`, których ten moduł tylko czyta.
"""

import collections
import json
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MATRIX = os.path.join(ROOT, "data", "legal", "rights-matrix.json")
DOC18 = os.path.join(ROOT, "docs", "18-rights-matrix.md")

#: Nagłówek sekcji doc18, w której stoi tabela pakietu A.
NAGLOWEK_PAKIETU_A = "pakiet A"

#: Komórka pustego pola w tabeli doc18 — odpowiednik `null` w rejestrze.
PUSTA_KOMORKA = "—"

#: Kreska rozdzielająca komórki, ale NIE kreska uciekniona (`\|`) wewnątrz tytułu.
ROZDZIELACZ_KOMOREK = re.compile(r"(?<!\\)\|")

#: **Koniec sekcji to nagłówek DOWOLNEGO poziomu, a nie tylko `##`** — i to jest
#: liczba, nie ostrożność. Sekcja pakietu A w doc18 **już dziś** niesie podsekcję
#: `### Źródła inwentarza dzieł`, więc czytnik przerywający tylko na `##` wciąga do
#: tabeli pakietu A wszystko, co ktoś w tej podsekcji złoży jako tabelę — czyli
#: zapala się na redakcji bez związku z prawami (6.D27).
ZAMYKA_SEKCJE = re.compile(r"^#{1,6} ")

#: Ile pozycji ma dziś pakiet A po obu stronach. Zapadka, nie ozdoba: bez niej
#: bramka porównująca DWA ZBIORY przeszłaby także wtedy, gdyby ktoś wyciął ten sam
#: wpis z obu plików naraz — a to jest dokładnie ruch, który doc18 opisuje jako
#: zmianę statusu na `excluded_until_cleared` i który ma zostać zauważony.
POZYCJI_W_PAKIECIE_A = 18

#: **Wyjątek jest POJEDYNCZY, NAZWANY i NIESIE WARUNEK SPRAWDZANY W DRZEWIE.**
#:
#: Klucz to `(station_id, work)` z rejestru — czyli wyjątek wskazuje JEDEN wiersz,
#: a nie klasę wierszy. Wartość to nie zdanie, tylko trzy pola, z których **każde
#: jest osobno weryfikowane niżej w tym module**:
#:
#: * `inventory_state` — stan, który ten wpis MUSI mieć w rejestrze i który musi być
#:   w całym pakiecie A **unikalny**. To jest zawias całej konstrukcji: dopóki stan
#:   `identified_shared_corridor` opisuje dokładnie jeden wiersz danych, wyjątku nie
#:   da się po cichu rozlać na drugi, bo drugi wpis musiałby najpierw ten stan dostać
#:   w `data/`, czyli w pliku tylko do odczytu (CLAUDE.md §4 pkt 6).
#: * `opis_w_doc18` — tekst, który w komórce „Dzieło” STOI ZAMIAST tytułu. Bramka
#:   nie przepuszcza tego wiersza obok siebie: żąda, żeby doc18 niósł DOKŁADNIE ten
#:   opis, w wierszu tej właśnie stacji i przy tym właśnie twórcy.
#: * `powod` — proza dla czytającego. **Sam by nie wystarczył** i dlatego nie stoi
#:   tu sam. Bramka, w której wyjątek jest napisem, a napisu nikt nie sprawdza,
#:   jest tym, co ten projekt tropi pod 6.D243.
#:
#: **Wyjątek musi być POTRZEBNY** — sprawdza to
#: `test_wyjatek_ktory_przestal_byc_potrzebny_ZAPALA_bramke`. Gdy tytuł z rejestru
#: pojawi się w doc18 dosłownie, wpis tutaj staje się martwy i bramka czerwienieje,
#: żądając jego zdjęcia. Ta sama asercja jest zaporą przed rozlaniem wyjątku na cały
#: pakiet: piętnaście pozostałych tytułów W doc18 stoi, więc piętnaście dopisanych
#: wyjątków byłoby piętnastoma wyjątkami niepotrzebnymi.
WYJATKI_OD_DOSLOWNEGO_TYTULU = {
    ("gare_centrale", "enamel-panel corridor artwork"): {
        "inventory_state": "identified_shared_corridor",
        "opis_w_doc18": "praca w emaliowanych panelach w korytarzu "
                        "łączącym kolej–metro",
        "powod": (
            "Pole `work` tego wpisu nie jest TYTUŁEM dzieła, tylko jego opisem: "
            "rejestr nie zna tytułu, bo źródło (Beliris) go nie podaje, a pozostałe "
            "siedemnaście pozycji ma tytuł z regionalnego inwentarza. Doc18 jest "
            "dokumentem polskim i w komórce „Dzieło\" niesie ten sam opis po polsku, "
            "a nie angielską frazę roboczą z rejestru. Przepisanie doc18 na frazę "
            "z `data/` byłoby wstawieniem do dokumentu tytułu, którego dzieło nie ma; "
            "przepisanie `data/` byłoby zmianą pliku tylko do odczytu. Wyjątek "
            "zostaje więc na styku i niesie warunek: opis po polsku ma stać w doc18 "
            "dosłownie, w wierszu Gare Centrale i przy twórcy Daniel Deltour."),
    },
}


def _rejestr():
    with open(MATRIX, encoding="utf-8") as uchwyt:
        return json.load(uchwyt)["package_a_artworks"]


def _doc18():
    with open(DOC18, encoding="utf-8") as uchwyt:
        return uchwyt.read()


def odkotwiczona(komorka):
    """Treść komórki tabeli bez ozdób Markdowna.

    Zdejmuje backticki (doc18 składa w nich tytuły) i **cofa ucieczki `\\X`**.
    To drugie nie jest ostrożnością na zapas: tytuł zawierający `|` MUSI w komórce
    tabeli stać jako `\\|`, więc porównanie z surowym tekstem doc18 zapaliłoby się
    na danych POPRAWNYCH. Ta sama pułapka dotyczy `_` i `*` w tytule.
    """
    tekst = komorka.strip().strip("`").strip()
    wynik = []
    i = 0
    while i < len(tekst):
        if tekst[i] == "\\" and i + 1 < len(tekst):
            wynik.append(tekst[i + 1])
            i += 2
        else:
            wynik.append(tekst[i])
            i += 1
    return "".join(wynik)


def _region_sekcji(linie):
    """Wiersze między nagłówkiem sekcji pakietu A a NASTĘPNYM nagłówkiem."""
    poczatek = None
    for numer, linia in enumerate(linie):
        if linia.startswith("## ") and NAGLOWEK_PAKIETU_A in linia:
            poczatek = numer
            break
    if poczatek is None:
        return []
    region = []
    for linia in linie[poczatek + 1:]:
        if ZAMYKA_SEKCJE.match(linia):
            break
        region.append(linia)
    return region


def _pierwszy_zwarty_blok(region):
    """Pierwszy CIĄGŁY ciąg wierszy zaczynających się od `|`.

    Puste wiersze PRZED blokiem są pomijane, pierwszy niepusty wiersz spoza
    tabeli blok KOŃCZY.
    """
    blok = []
    for linia in region:
        if linia.strip().startswith("|"):
            blok.append(linia)
        elif blok:
            break
    return blok


def wiersze_surowe(tekst):
    """Komórki tabeli „Dzieła sztuki — pakiet A" W POSTACI ŹRÓDŁOWEJ.

    Backticki ZOSTAJĄ — są treścią: doc18 składa w nich KAŻDY tytuł, więc ich brak
    odróżnia opis od tytułu, a na tym odróżnieniu stoi warunek wyjątku.

    **Granica wycinka jest podwójna i obie połowy są ZMIERZONE na 204 sekcjach
    `##` w `docs/` (16.09.2026), a nie dobrane z gustu.** Region kończy się na
    nagłówku **dowolnego** poziomu, a z regionu bierzemy **pierwszy zwarty blok**
    wierszy `|`:

    * gdyby region kończył się tylko na `##`, czytnik **scalałby dwie sąsiednie
      tabele w 7 z 204 sekcji** korpusu (m.in. `docs/17-visual-regression.md`
      „## Zestawy kamer" i `docs/23-environment.md` „## 2. Blender — dwie drogi");
      w tym pliku dotyczyłoby to każdej tabeli złożonej pod `### Źródła inwentarza
      dzieł`, czyli podsekcją, którą doc18 **ma dziś**;
    * gdyby brać sam pierwszy zwarty blok, bez ucinania na nagłówku, tryb awarii
      byłby **1 z 204** — i taki sam jest po złożeniu. Ta jedna to tabela rozbita
      pustym wierszem (`docs/21-measured-vs-assumed.md`, „## 3. Oś trasy"), gdzie
      oba warianty ucinają ogon. Region złożenia zawiera się w regionie samego
      bloku, więc złożenie nie potrafi paść tam, gdzie sam blok stoi.

    **Granica wypisana wprost:** tabela pakietu A rozbita pustym wierszem albo
    nagłówkiem `###` w środku zostanie przycięta — i zapali wtedy zapadkę
    `POZYCJI_W_PAKIECIE_A`, czyli głośno. W dzisiejszym doc18 takich rozbić jest
    **zero**.
    """
    surowe = []
    for linia in _pierwszy_zwarty_blok(_region_sekcji(tekst.splitlines())):
        # Rozdzielacz omija `\|` — i to NIE jest ostrożność na zapas, tylko
        # poprawka po własnej kontroli przyrządu: `str.split("|")` rozcinał wiersz
        # z uciekniętą kreską w tytule na sześć komórek i przesuwał WSZYSTKIE
        # kolumny, więc bramka zapalała się na danych POPRAWNYCH (6.D27).
        komorki = ROZDZIELACZ_KOMOREK.split(linia.strip())
        surowe.append([k.strip() for k in komorki[1:-1]])
    tresc = [w for w in surowe if not set("".join(w)) <= set("-: ")]
    return tresc[1:]


def wiersze_tabeli(tekst):
    """`[(stacja, dzieło, twórca)]` — komórki bez ozdób Markdowna."""
    return [(odkotwiczona(w[0]), odkotwiczona(w[1]), odkotwiczona(w[2]))
            for w in wiersze_surowe(tekst)]


def _wpis_objety(rejestr, klucz):
    """Wiersz rejestru wskazany przez wyjątek — albo NAZWANY werdykt.

    Stoi tu zamiast `[...][0]` i to jest cała jego treść: przy wyjątku wskazującym
    wpis, którego już nie ma, indeksowanie dawało `IndexError: list index out of
    range` w czterech testach naraz. Zestaw taką czerwień łapie, ale komunikat nie
    mówi czytającemu ani który wyjątek, ani czego brakuje — czyli **błąd bramki
    czytany jak werdykt o danych**.
    """
    dopasowane = [wpis for wpis in rejestr
                  if (wpis["station_id"], wpis.get("work")) == klucz]
    assert len(dopasowane) == 1, (
        "wyjątek %r pasuje do %d wierszy `package_a_artworks` zamiast do jednego. "
        "Zero znaczy, że wpis zniknął z rejestru albo zmienił pole `work`, a wyjątek "
        "został jako napis, którego nikt nie sprawdza (6.D243); więcej niż jeden "
        "znaczy, że wyjątek opisuje KLASĘ wierszy, a decyzja właściciela mówi "
        "o jednym nazwanym wierszu" % (klucz, len(dopasowane)))
    return dopasowane[0]


def _trojki_z_rejestru(rejestr):
    """`Counter{(stacja, dzielo, tworca): krotnosc}` — postać, w jakiej MA stać w doc18.

    Dla wpisu objętego wyjątkiem w miejsce `work` wchodzi `opis_w_doc18` — czyli
    wyjątek NIE wyłącza wiersza ze sprawdzania, tylko podmienia oczekiwany tekst
    na inny, równie dosłownie sprawdzany.

    **`Counter`, a nie `set`, i to jest poprawka po zmierzonej dziurze.** Na zbiorach
    rejestr z dwoma wpisami `Ortem` i doc18 z dwoma wierszami `Isjtar` — czyli dwa
    RÓŻNE zbiory po 19 pozycji — dawały bramkę ZIELONĄ w komplecie 13/13. Zapadka
    `POZYCJI_W_PAKIECIE_A` zasłaniała to tylko dopóki stała na 18; zapadka jest
    jednak po to, żeby ją podnosić, więc dziura otwierała się w dniu, w którym
    pakiet A urośnie. Krotność jest tu treścią, nie ostrożnością.
    """
    out = collections.Counter()
    for wpis in rejestr:
        klucz = (wpis["station_id"], wpis.get("work"))
        wyjatek = WYJATKI_OD_DOSLOWNEGO_TYTULU.get(klucz)
        if wyjatek is not None:
            dzielo = wyjatek["opis_w_doc18"]
        elif wpis.get("work") is None:
            dzielo = PUSTA_KOMORKA
        else:
            dzielo = wpis["work"]
        tworca = wpis.get("creator") or PUSTA_KOMORKA
        out[(wpis["station"], dzielo, tworca)] += 1
    return out


# --- kontrola PRZYRZĄDU ------------------------------------------------------
# Bez niej liczba osiemnastu wierszy nie znaczy nic: czytnik, który z każdej tabeli
# zwraca pustą listę, dałby ZGODNOŚĆ dwóch pustych zbiorów. To rodzina 6.D159.

def test_czytnik_tabeli_WIDZI_to_co_ma_widziec():
    prubka = "\n".join([
        "## Inna tabela",
        "| A | B | C |",
        "|---|---|---|",
        "| nie | ta | tabela |",
        "",
        "## Dzieła sztuki — pakiet A",
        "",
        "| Stacja | Dzieło | Twórca | Stan | Produkcja |",
        "|---|---|---|---|---|",
        "| Alfa | `Tytuł z \\| kresą` | Ktoś | x | y |",
        "| Beta | — | — | x | y |",
        "",
        "## Po tabeli",
        "| Gamma | `Poza sekcją` | Nikt | x | y |",
    ])
    dostane = wiersze_tabeli(prubka)
    assert dostane == [("Alfa", "Tytuł z | kresą", "Ktoś"),
                       ("Beta", PUSTA_KOMORKA, PUSTA_KOMORKA)], (
        "czytnik dał %r — czytnik, który nie cofa ucieczki `\\|`, zapala "
        "bramkę na danych POPRAWNYCH, a czytnik, który nie kończy na "
        "nagłówku, wciąga cudzą tabelę" % (dostane,))


def test_czytnik_tabeli_odmawia_gdy_sekcji_NIE_MA():
    """Brak sekcji ma dać pustą listę, a nie wyjątek — bo pustą listę łapie
    zapadka `POZYCJI_W_PAKIECIE_A`, a wyjątek byłby błędem bramki, nie danych."""
    dostane = wiersze_tabeli("# dokument bez tabeli\n")
    assert dostane == [], (
        "czytnik na dokumencie bez sekcji dał %r zamiast pustej listy — wyjątek "
        "z czytnika byłby błędem BRAMKI, a nie danych, i czytałby się jak czerwień "
        "od dokumentu" % (dostane,))


def test_odkotwiczona_zdejmuje_backticki_i_cofa_ucieczki():
    assert odkotwiczona("`Millefeuille`") == "Millefeuille", (
        "backticki doc18 nie schodzą — wtedy ŻADEN tytuł nie zgadza się z rejestrem "
        "i bramka jest czerwona na danych poprawnych")
    assert odkotwiczona("a \\_b\\_ c") == "a _b_ c", (
        "ucieczka `\\_` nie jest cofana — tytuł z podkreśleniem MUSI stać "
        "w Markdownie uciekniony, więc bramka zapaliłaby się na danych poprawnych")
    assert odkotwiczona("  —  ") == PUSTA_KOMORKA, (
        "pusta komórka po obcięciu spacji nie jest rozpoznana — wtedy dwa wpisy "
        "`inventory_pending` nie mają odpowiednika w tabeli")


def test_czytnik_NIE_wciaga_tabeli_z_PODSEKCJI_tej_samej_sekcji():
    """**Kontrola na 6.D27: dane POPRAWNE nie mogą zapalać bramki.**

    doc18 niesie wewnątrz sekcji pakietu A podsekcję `### Źródła inwentarza dzieł`.
    Zamiana tamtej listy punktowej na tabelę jest ruchem czysto redakcyjnym,
    o zerowym związku z prawami — a czytnik przerywający tylko na `##` wciągał
    jej wiersze do pakietu A i dawał trzy czerwienie na poprawnym dokumencie.
    """
    prubka = "\n".join([
        "## Dzieła sztuki — pakiet A",
        "",
        "| Stacja | Dzieło | Twórca | Stan | Produkcja |",
        "|---|---|---|---|---|",
        "| Alfa | `Tytuł` | Ktoś | x | y |",
        "",
        "### Źródła inwentarza dzieł",
        "",
        "| Źródło | Zakres | Uwaga |",
        "|---|---|---|",
        "| Heritage Brussels | inwentarz | podstawa tytułów |",
    ])
    dostane = wiersze_tabeli(prubka)
    assert dostane == [("Alfa", "Tytuł", "Ktoś")], (
        "czytnik dał %r — wiersze z podsekcji `###` wchodzą do tabeli pakietu A, "
        "czyli bramka zapala się na redakcji dokumentu, a nie na rozjeździe "
        "rejestru z doc18" % (dostane,))


def test_czytnik_NIE_SCALA_dwoch_tabel_rozdzielonych_PROZA():
    """Druga połowa granicy: sam nagłówek nie wystarcza.

    Zmierzone na 204 sekcjach `##` w `docs/`: tabele stojące w jednej sekcji bez
    nagłówka między nimi są w korpusie w **7** sekcjach, więc to nie jest kształt
    hipotetyczny.
    """
    prubka = "\n".join([
        "## Dzieła sztuki — pakiet A",
        "",
        "| Stacja | Dzieło | Twórca |",
        "|---|---|---|",
        "| Alfa | `Tytuł` | Ktoś |",
        "",
        "Zdanie prozą, które rozdziela dwie tabele.",
        "",
        "| Inna | `Tabela` | Nikt |",
    ])
    dostane = wiersze_tabeli(prubka)
    assert dostane == [("Alfa", "Tytuł", "Ktoś")], (
        "czytnik dał %r — druga tabela tej samej sekcji weszła do pakietu A"
        % (dostane,))


def test_porownanie_liczy_KROTNOSC_a_nie_samą_OBECNOSC():
    """**Kontrola dziury zmierzonej na `set()`.**

    Rejestr z DWOMA identycznymi wpisami wobec doc18 z jednym takim wierszem
    i jednym innym to dwa RÓŻNE zbiory wielokrotne o tej samej liczności. Na
    `set()` obie strony zwijały się do tego samego zbioru i bramka szła zielona
    w komplecie; `Counter` widzi brak drugiego egzemplarza.
    """
    wpis = {"station_id": "alfa", "station": "Alfa", "work": "Tytuł",
            "creator": "Ktoś", "inventory_state": "identified"}
    oczekiwane = _trojki_z_rejestru([dict(wpis), dict(wpis)])
    assert oczekiwane[("Alfa", "Tytuł", "Ktoś")] == 2, (
        "rejestr z dwoma identycznymi wpisami dał krotność %d zamiast 2 — "
        "porównanie zwijające duplikaty przepuszcza rozjazd, w którym obie strony "
        "mają tyle samo pozycji, ale nie te same"
        % oczekiwane[("Alfa", "Tytuł", "Ktoś")])

    doc = "\n".join([
        "## Dzieła sztuki — pakiet A",
        "| Stacja | Dzieło | Twórca |",
        "|---|---|---|",
        "| Alfa | `Tytuł` | Ktoś |",
        "| Beta | `Inny` | Ktoś |",
    ])
    obecne = collections.Counter(wiersze_tabeli(doc))
    brakujace = sorted((oczekiwane - obecne).elements())
    nadmiarowe = sorted((obecne - oczekiwane).elements())
    assert brakujace == [("Alfa", "Tytuł", "Ktoś")], (
        "różnica wielozbiorów dała %r — drugi egzemplarz wpisu rejestru nie "
        "został zauważony" % (brakujace,))
    assert nadmiarowe == [("Beta", "Inny", "Ktoś")], (
        "różnica w drugą stronę dała %r" % (nadmiarowe,))


# --- sama bramka -------------------------------------------------------------

def test_pakiet_A_ma_po_obu_stronach_tyle_samo_pozycji():
    rejestr = _rejestr()
    tabela = wiersze_tabeli(_doc18())
    assert len(rejestr) == POZYCJI_W_PAKIECIE_A, (
        "`package_a_artworks` ma %d pozycji przy zapadce %d — jeśli pakiet "
        "A urósł albo się skurczył, podnieś liczbę z powodem"
        % (len(rejestr), POZYCJI_W_PAKIECIE_A))
    assert len(tabela) == POZYCJI_W_PAKIECIE_A, (
        "tabela pakietu A w doc18 ma %d wierszy przy zapadce %d"
        % (len(tabela), POZYCJI_W_PAKIECIE_A))


def test_kazdy_wpis_rejestru_ma_swoj_wiersz_w_doc18():
    """Kierunek `data/` -> doc18. To jest ten kierunek, w którym dziś
    brakuje jednej pozycji i w którym nikt by tego nie zobaczył."""
    oczekiwane = _trojki_z_rejestru(_rejestr())
    obecne = collections.Counter(wiersze_tabeli(_doc18()))
    brakujace = sorted((oczekiwane - obecne).elements())
    assert not brakujace, (
        "rejestr zna pozycje, których tabela doc18 nie niesie: %r — doc18 "
        "kończy się zdaniem, że brak wpisu znaczy `excluded_until_cleared`, "
        "więc pozycja nieobecna w dokumencie zmienia znaczenie tamtego zdania"
        % (brakujace,))


def test_doc18_nie_niesie_dziela_ktorego_rejestr_NIE_ZNA():
    """Kierunek doc18 -> `data/`. Bez niego bramka przepuszczałaby wiersz
    dopisany do dokumentu, któremu nic nie odpowiada w rejestrze maszynowym —
    czyli pozycję wyglądającą na rozstrzygniętą, której
    żadne narzędzie nie widzi."""
    oczekiwane = _trojki_z_rejestru(_rejestr())
    obecne = collections.Counter(wiersze_tabeli(_doc18()))
    nadmiarowe = sorted((obecne - oczekiwane).elements())
    assert not nadmiarowe, (
        "tabela doc18 niesie wiersze bez odpowiednika w `package_a_artworks`: %r"
        % (nadmiarowe,))


# --- warunki, które musi spełnić WYJĄTEK ------------------

def test_wyjatek_wskazuje_ISTNIEJACY_wiersz_rejestru():
    """Wyjątek opisujący nieistniejący wpis jest napisem, którego
    nikt nie sprawdza — i to jest dokładnie kształt 6.D243."""
    rejestr = _rejestr()
    klucze = [(w["station_id"], w.get("work")) for w in rejestr]
    for klucz in sorted(WYJATKI_OD_DOSLOWNEGO_TYTULU, key=repr):
        ile = klucze.count(klucz)
        assert ile == 1, (
            "wyjątek %r pasuje do %d wierszy rejestru — wyjątek ma "
            "wskazywać JEDEN wiersz, nie klasę wierszy i nie wiersz, "
            "którego już nie ma" % (klucz, ile))


def test_wyjatek_ktory_przestal_byc_potrzebny_ZAPALA_bramke():
    """**Zawias tego modułu.** Wyjątek jest legalny tylko dopóki jest
    POTRZEBNY: tytuł z rejestru NIE MOŻE stać w doc18 dosłownie.

    Ta jedna asercja jest jednocześnie zaporą przed rozlaniem wyjątku na
    cały pakiet — piętnaście pozostałych tytułów
    w doc18 STOI, więc piętnaście dopisanych wyjątków byłoby
    piętnastoma wyjątkami zbędnymi i bramka zapali się na każdym.
    """
    doc = _doc18()
    for (stacja_id, tytul) in sorted(WYJATKI_OD_DOSLOWNEGO_TYTULU, key=repr):
        assert tytul not in doc, (
            "wyjątek dla %r/%r jest ZBĘDNY: ten tytuł stoi w doc18 "
            "dosłownie, więc zwykła ścieżka bramki by go "
            "przepuściła — zdejmij wpis z "
            "`WYJATKI_OD_DOSLOWNEGO_TYTULU`" % (stacja_id, tytul))


def test_wyjatek_stoi_na_UNIKALNYM_stanie_inwentarza():
    """Warunek sprawdzany W DRZEWIE, nie zdanie w słowniku.

    Dopóki stan inwentarza wskazany przez wyjątek opisuje dokładnie
    JEDEN wiersz `package_a_artworks`, wyjątku nie da się rozlać po
    cichu: drugi wiersz musiałby ten stan najpierw dostać w `data/`.
    """
    rejestr = _rejestr()
    stany = [w.get("inventory_state") for w in rejestr]
    for klucz, wyjatek in sorted(WYJATKI_OD_DOSLOWNEGO_TYTULU.items(), key=repr):
        wpis = _wpis_objety(rejestr, klucz)
        oczekiwany = wyjatek["inventory_state"]
        assert wpis.get("inventory_state") == oczekiwany, (
            "wyjątek %r deklaruje stan %r, a rejestr ma %r"
            % (klucz, oczekiwany, wpis.get("inventory_state")))
        assert stany.count(oczekiwany) == 1, (
            "stan %r opisuje %d wierszy pakietu A — wyjątek oparty na stanie "
            "współdzielonym da się rozlać na wszystkie z nich"
            % (oczekiwany, stany.count(oczekiwany)))


def test_wyjatek_zada_od_doc18_dokladnie_tego_opisu_przy_tym_tworcy():
    """Wyjątek nie zwalnia wiersza ze sprawdzania — podmienia oczekiwany
    tekst. Opis ma stać w doc18 w wierszu TEJ stacji i przy TYM twórcy."""
    rejestr = _rejestr()
    tabela = wiersze_tabeli(_doc18())
    for klucz, wyjatek in sorted(WYJATKI_OD_DOSLOWNEGO_TYTULU.items(), key=repr):
        wpis = _wpis_objety(rejestr, klucz)
        oczekiwany = (wpis["station"], wyjatek["opis_w_doc18"], wpis["creator"])
        assert oczekiwany in tabela, (
            "doc18 nie niesie wiersza %r — wyjątek deklaruje opis, "
            "którego w tabeli nie ma przy tej stacji i tym twórcy"
            % (oczekiwany,))


def test_wyjatek_stoi_na_komorce_ktora_NIE_JEST_TYTULEM():
    """Trzeci warunek w drzewie — i jedyny, który nie jest pinem na tekście.

    doc18 składa KAŻDY tytuł w backtickach; komórka wyjątku jest prozą bez nich.
    Ta asercja pyta więc o STRUKTURĘ dokumentu, a nie o jego brzmienie, i zapala
    się, gdy ktoś obejmie wyjątkiem wiersz, który tytuł ma. Bez niej wyjątek dałoby
    się przenieść na dowolny inny wiersz przez samo przepisanie pola `opis_w_doc18`
    — czyli przez zmianę napisu w słowniku.

    **Obietnica jest wąska i taka ma być — poprzednia była szersza od pomiaru.**
    Stało tu „przetrwa przeredagowanie opisu"; zmierzone jest, że przeredagowanie
    polskiego opisu w komórce „Dzieło" przepuszcza **ta jedna** asercja, a zapala
    **trzy inne** w tym module (`test_wyjatek_zada_od_doc18_dokladnie_tego_opisu…`
    oraz oba kierunki porównania). Moduł jako całość redakcji opisu **nie
    przetrwa** i to jest świadomy koszt tego, że wyjątek ma być dosłowny —
    komunikaty odsyłają wtedy do właściciela. Zdanie jest przepisane, a nie
    dopisane obok, bo obietnica szersza od zachowania jest tym samym, co wyjątek
    będący napisem.
    """
    rejestr = _rejestr()
    surowe = wiersze_surowe(_doc18())
    objete = set()
    for klucz in WYJATKI_OD_DOSLOWNEGO_TYTULU:
        wpis = _wpis_objety(rejestr, klucz)
        objete.add((wpis["station"], wpis["creator"]))
    for wiersz in surowe:
        stacja, dzielo, tworca = (odkotwiczona(wiersz[0]), wiersz[1].strip(),
                                  odkotwiczona(wiersz[2]))
        w_backtickach = dzielo.startswith("`") and dzielo.endswith("`")
        if (stacja, tworca) in objete:
            assert not w_backtickach, (
                "wiersz %r jest objęty wyjątkiem, a jego komórka „Dzieło” stoi "
                "w backtickach — czyli doc18 uznaje to za TYTUŁ i wyjątek nie ma "
                "podstawy" % (stacja,))
            assert dzielo and dzielo != PUSTA_KOMORKA, (
                "wiersz %r objęty wyjątkiem ma pustą komórkę „Dzieło”" % (stacja,))
        elif dzielo != PUSTA_KOMORKA:
            assert w_backtickach, (
                "wiersz %r NIE jest objęty wyjątkiem, a jego komórka „Dzieło” nie "
                "stoi w backtickach — albo to drugi taki przypadek i wymaga decyzji "
                "właściciela, albo doc18 zgubił skład" % (stacja,))


def test_wyjatek_niesie_zrodlo_ktore_doc18_cytuje():
    """Drugi warunek w drzewie: `source_url` wpisu objętego wyjątkiem musi
    być w doc18 zacytowany. Skoro tytułu nie ma, to źródło jest
    jedyną rzeczą, po której czytelnik dokumentu doprowadzi opis do wpisu."""
    doc = _doc18()
    rejestr = _rejestr()
    for klucz in sorted(WYJATKI_OD_DOSLOWNEGO_TYTULU, key=repr):
        wpis = _wpis_objety(rejestr, klucz)
        zrodlo = wpis.get("source_url")
        assert zrodlo, "wpis objęty wyjątkiem %r nie ma `source_url`" % (klucz,)
        assert zrodlo in doc, (
            "doc18 nie cytuje źródła %r wpisu %r" % (zrodlo, klucz))


def test_wyjatkow_jest_DOKLADNIE_JEDEN_i_kazdy_niesie_powod():
    """Decyzja właściciela: wyjątek jest POJEDYNCZY i NAZWANY.

    Ta asercja jest najsłabszą z zapór tego modułu i stoi tu
    świadomie jako druga, nie pierwsza: liczbę da się podnieść
    jednym znakiem. Rozlanie wyjątku łapią przed nią dwie asercje
    stojące na ZACHOWANIU — „wyjątek musi być potrzebny" i „stan
    inwentarza musi być unikalny".
    """
    assert len(WYJATKI_OD_DOSLOWNEGO_TYTULU) == 1, (
        "wyjątków jest %d — decyzja właściciela mówi "
        "o jednym; każdy kolejny wymaga osobnego rozstrzygnięcia"
        % len(WYJATKI_OD_DOSLOWNEGO_TYTULU))
    for klucz, wyjatek in sorted(WYJATKI_OD_DOSLOWNEGO_TYTULU.items(), key=repr):
        assert set(wyjatek) == {"inventory_state", "opis_w_doc18", "powod"}, (
            "wyjątek %r ma pola %r — brak któregokolwiek znaczy warunek, "
            "którego nikt nie sprawdza" % (klucz, sorted(wyjatek)))
        assert len(wyjatek["powod"]) > 200, (
            "powód przy %r ma %d znaków — za mało, żeby "
            "powiedzieć, DLACZEGO ten jeden wiersz jest inny"
            % (klucz, len(wyjatek["powod"])))


# 6.D25: uruchomienie tego pliku WPROST idzie ta sama droga, co caly zestaw.
if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))
