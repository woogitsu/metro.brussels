#!/usr/bin/env python3
"""Klasy pochodzenia parametrów mają JEDNO źródło: `docs/02-simulation.md` — 6.D89.

**Skąd ta bramka.** Zmierzone 09.09.2026 i przeliczone 10.09.2026 na trzech zapisach
stojących obok siebie:

    docs/02-simulation.md   spec, observed, est, design_model     (definicja, 4 klasy)
    .claude/skills/sim-physics/SKILL.md   spec, est, design       (kopia, 3 klasy)
    docs/07-open-data-research.md         spec, est, design       (kopia, 3 klasy)
    data/vehicle/m7-spec.json             spec 15x, design_model 18x

Rozjeżdżała się **jedna nazwa z trzech**: `design` nie jest klasą tego dokumentu
(jest `design_model`), a czwartej klasy — `observed` — obie kopie nie wymieniały
wcale. `est` nie występuje w danych pojazdu **ani razu**, choć dokument nadal ją
definiuje: i to jest poprawne, bo definiuje ją jako „oszacowanie historyczne do
usunięcia/weryfikacji", czyli jako klasę, której obecność byłaby usterką.

**Dlaczego to nie jest „skrót rozjechał się z dokumentacją".** Starsza litera
słownika przetrwała w DWÓCH plikach, gdy dokument modelu i dane pojazdu przeszły na
nowszą — rozjazd jest dwustronny, nie jednostronnym uproszczeniem skrótu.

**Zbiór jest PARSOWANY, nie przepisany.** Gdyby stał tu jako lista w Pythonie, byłby
trzecią kopią tej samej wiedzy i rozjechałby się jak dwie poprzednie. Dopisanie klasy
do dokumentu ma nie zapalać niczego — dokument jest źródłem, nie kopią, i tego wprost
żąda pole „Skończone, gdy" pozycji 6.D89.
"""
import csv
import json
import os
import re
import tempfile
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tree_walk as TW  # noqa: E402

#: Dokument, który klasy DEFINIUJE. Jedyne źródło.
MODEL = os.path.join(ROOT, "docs", "02-simulation.md")

#: Miejsca, w których klasy są CYTOWANE. Każde musi mieścić się w zbiorze z `MODEL`.
CYTUJACY = (
    os.path.join(".claude", "skills", "sim-physics", "SKILL.md"),
    os.path.join("docs", "07-open-data-research.md"),
)

#: Dane pojazdu — wartości pola `status`. Tylko do czytania (`CLAUDE.md` §4.6).
POJAZD = os.path.join(ROOT, "data", "vehicle", "m7-spec.json")

#: Zdanie definiujące, w postaci „`nazwa` = opis, `nazwa` = opis…". Wzorzec bierze
#: nazwy stojące PRZED znakiem równości — sam grep po grawisach złapałby też nazwy
#: parametrów i ścieżki plików, których w tym samym akapicie jest kilka.
DEFINICJA = re.compile(r"`([a-z_]+)`\s*=")

#: Nazwy WYCOFANE — stały w plikach cytujących, a dokument modelu ich nie zna.
#: Lista jest zamknięta i każdy wpis ma powód; rośnie wyłącznie przez pomiar.
WYCOFANE = {
    "design": "stało w skrócie `sim-physics` i w `docs/07` jako trzecia klasa; "
              "dokument modelu zna `design_model`, a `design` nie występuje ani "
              "w nim, ani w danych pojazdu (zmierzone 10.09.2026, 6.D89)",
}


#: **6.D134: cały katalog danych, a nie jeden plik.** `klasy_w_danych` czyta wyłącznie
#: `data/vehicle/m7-spec.json`, bo 6.D89 pytało o klasy modelu jazdy. Pole `status`
#: stoi jednak w **20** plikach JSON pod `data/` (zmierzone 11.09.2026) i niesie w nich
#: słowniki ZUPEŁNIE INNE — `ok`, `unknown`, `source_backed`, `permission_required`.
#: Nazwa wycofana mogłaby więc wrócić w dowolnym z pozostałych dziewiętnastu i nie
#: zgłosiłoby tego nic.
DANE = os.path.join(ROOT, "data")

#: Klasy, które dokument DEFINIUJE, ale których w danych być nie wolno. Wpis nie jest
#: tym samym co `WYCOFANE`: tamte są nazwami, których dokument modelu **nie zna**,
#: a `est` zna i opisuje — jako „oszacowanie historyczne do usunięcia/weryfikacji",
#: czyli klasę, której obecność jest usterką, a brak stanem docelowym.
ZAKAZANE_W_DANYCH = {
    "est": "dokument modelu definiuje ją jako oszacowanie historyczne DO USUNIĘCIA, "
           "więc wpis o tym statusie znaczy, że do danych wróciła liczba, której "
           "nikt nie potwierdził (6.D134)",
}

#: Gołe słowo `est` w plikach `data/`, ZE WSZYSTKIMI wystąpieniami — zmierzone
#: 11.09.2026: **7 w 4 plikach i wszystkie siedem to francuszczyzna.** Cztery stoją
#: w adresach STIB (`…-on-en-est-ou`, `…-m7-est-arrive-…`), trzy w cytacie z EIE
#: («la profondeur des quais … **est** d'environ 11 m») w `station-depths.csv`.
#: Trafień prawdziwych: **zero**.
#:
#: Liczba stoi tu po to, żeby bramka niżej mogła POKAZAĆ, czemu nie jest grepem —
#: a nie tylko o tym napisać. Skan po samym słowie dałby siedem fałszywych alarmów
#: i ani jednego prawdziwego, czyli byłby czystym szumem.
EST_JAKO_SLOWO_W_DANYCH = 7
EST_JAKO_SLOWO_PLIKOW = 4

#: Wzorzec gołego słowa — używany WYŁĄCZNIE do pokazania, że grep tu nie działa.
SLOWO_EST = re.compile(r"(?<![A-Za-z_])est(?![A-Za-z_])")


#: Nagłówki kolumn, które w plikach tabelarycznych `data/` NIOSĄ STATUS — 6.D150.
#:
#: Tabela, nie reguła po kształcie: nagłówek jest nazwą wybraną przez człowieka, a nie
#: wzorcem, i zgadywany byłby zgadniętym faktem. Dziś ma jedną pozycję, bo pod `data/`
#: stoi **jeden** plik CSV. `status` jest w niej obok `confidence`, bo tak nazywa się
#: to pole w JSON-ach i nowy plik najpewniej weźmie tę nazwę; gdy weźmie inną, zapali
#: się `test_kazdy_plik_CSV_pod_data_ma_kolumne_statusu_w_tabeli`.
KOLUMNY_STATUSU_CSV = ("confidence", "status")

#: Statusy w kolumnach CSV pod `data/`. **Zmierzone 12.09.2026: jeden plik, kolumna
#: `confidence`, `unknown` 9 i `estimated` 3.**
#:
#: **Wpis pozycji 6.D150 podawał trzecią wartość — `confidence` 1× — i to jest ODCISK
#: czytnika, który nie pominął nagłówka.** Plik ma cztery wiersze komentarza `#`,
#: a dopiero piąty jest nagłówkiem; `csv.DictReader` puszczony wprost bierze za
#: nagłówek pierwszy komentarz i całą resztę czyta jako jedną kolumnę. Liczba 1 przy
#: `confidence` jest więc policzonym NAGŁÓWKIEM, a nie wartością — i dokładnie dlatego
#: czytnik niżej pomija wiersze `#`, a kontrola przyrządu to wykonuje.
STATUSY_CSV = {
    "network/station-depths.csv": {"confidence": {"unknown": 9, "estimated": 3}},
}

#: Słownik, który `station-depths.csv` deklaruje we WŁASNYM nagłówku komentarza:
#: `# confidence: measured | counted | estimated | unknown`.
SLOWNIK_STATION_DEPTHS = ("measured", "counted", "estimated", "unknown")


def _wiersze_csv(sciezka):
    """`(nagłówek, wiersze)` — z pominięciem wierszy komentarza `#`.

    Nagłówkiem jest PIERWSZY wiersz niekomentarzowy. Bez tego pominięcia nagłówkiem
    zostaje pierwszy komentarz, a plik czyta się jako jedna kolumna — patrz
    `STATUSY_CSV`.
    """
    with open(sciezka, encoding="utf-8") as uchwyt:
        tresc = [w for w in uchwyt.read().split("\n")
                 if w.strip() and not w.lstrip().startswith("#")]
    if not tresc:
        return [], []
    czytnik = list(csv.reader(tresc))
    return czytnik[0], czytnik[1:]


def statusy_w_kolumnach_csv(katalog=None):
    """`{ścieżka względna: {kolumna: {status: ile}}}` dla CSV pod `data/` — 6.D150.

    Czyta KOLUMNĘ wskazaną nagłówkiem, a nie tekst pliku. Różnica jest ta sama, co
    między `statusy_w_katalogu_danych` a grepem z `EST_JAKO_SLOWO_W_DANYCH`: trzy
    z siedmiu fałszywych trafień tamtego grepu leżą właśnie w tym pliku, w cytacie
    «la profondeur des quais … **est** d'environ 11 m».
    """
    baza = katalog or DANE
    out = {}
    for gdzie, _katalogi, pliki in TW.walk(baza, baza):
        for nazwa in sorted(pliki):
            if not nazwa.endswith(".csv"):
                continue
            sciezka = os.path.join(gdzie, nazwa)
            naglowek, wiersze = _wiersze_csv(sciezka)
            per_kolumna = {}
            for kolumna in KOLUMNY_STATUSU_CSV:
                if kolumna not in naglowek:
                    continue
                k = naglowek.index(kolumna)
                licznik = {}
                for wiersz in wiersze:
                    if k >= len(wiersz):
                        continue
                    wartosc = wiersz[k].strip()
                    if wartosc:
                        licznik[wartosc] = licznik.get(wartosc, 0) + 1
                if licznik:
                    per_kolumna[kolumna] = licznik
            if per_kolumna:
                out[os.path.relpath(sciezka, baza).replace(os.sep, "/")] = per_kolumna
    return out


def pliki_csv_pod_danymi(katalog=None):
    """Wszystkie CSV pod `data/` — do sprawdzenia, że żaden nie stoi poza skanem."""
    baza = katalog or DANE
    out = []
    for gdzie, _katalogi, pliki in TW.walk(baza, baza):
        out += [os.path.relpath(os.path.join(gdzie, n), baza).replace(os.sep, "/")
                for n in sorted(pliki) if n.endswith(".csv")]
    return sorted(out)


def statusy_w_katalogu_danych(katalog=None):
    """`{ścieżka względna: {status: ile}}` dla każdego JSON-a pod `data/`.

    Czyta POLE `status`, a nie tekst pliku — i to jest cała różnica między tą bramką
    a grepem, którego wynik stoi w `EST_JAKO_SLOWO_W_DANYCH`.
    """
    baza = katalog or DANE
    out = {}
    for gdzie, _katalogi, pliki in TW.walk(baza, baza):
        for nazwa in sorted(pliki):
            if not nazwa.endswith(".json"):
                continue
            sciezka = os.path.join(gdzie, nazwa)
            try:
                dane = json.loads(_read(sciezka))
            except (ValueError, OSError):
                continue
            licznik = {}

            def obejdz(wezel):
                if isinstance(wezel, dict):
                    status = wezel.get("status")
                    if isinstance(status, str):
                        licznik[status] = licznik.get(status, 0) + 1
                    for wartosc in wezel.values():
                        obejdz(wartosc)
                elif isinstance(wezel, list):
                    for wartosc in wezel:
                        obejdz(wartosc)

            obejdz(dane)
            if licznik:
                out[os.path.relpath(sciezka, baza).replace(os.sep, "/")] = licznik
    return out


#: Drugi dokument z WŁASNĄ tabelą statusów — 6.D105. Klasyfikuje wymiary geometrii,
#: a nie parametry modelu jazdy, więc ma prawo definiować swoje nazwy i NIE jest
#: plikiem cytującym. Reguła jest tu inna niż w `CYTUJACY`: nie „nie wymieniaj klas",
#: tylko „każdy status UŻYTY musi być gdzieś ZDEFINIOWANY".
GEOMETRIA = os.path.join(ROOT, "docs", "21-measured-vs-assumed.md")

#: Nagłówek kolumny, w której stoi status. Rozpoznanie jest STRUKTURALNE — po nazwie
#: kolumny tabeli — a nie po zgadywaniu, który napis w grawisach jest statusem.
#: Zmierzone 10.09.2026: sam skan „komórka będąca pojedynczym napisem w grawisach"
#: łapie też `box_double`, `bore_single`, `station` i `null`, czyli nazwy profili
#: tunelu i wartość pustą — cztery fałszywe trafienia na cztery prawdziwe nazwy.
KOLUMNA_STATUSU = "status"

#: Nagłówek tabeli DEFINIUJĄCEJ w dokumencie geometrii.
NAGLOWEK_DEFINICJI = ["status", "znaczenie"]

#: Komórka będąca samą nazwą statusu, z opcjonalnym pogrubieniem.
KOMORKA_STATUSU = re.compile(r"^\*{0,2}`([a-z_]+)`\*{0,2}$")

#: Nazwa w grawisach — do przeszukania PROZY, ale wyłącznie po SŁOWNIKU ZAMKNIĘTYM
#: (suma obu tabel). Wzorzec sam nie rozstrzyga, co jest statusem, bo rozstrzygnąć
#: tego na prozie nie sposób: pierwsza wersja bramki z 6.D89 zgłosiła `as_of` z listy
#: pól metadanych. Nazwa nieznana jest łapana gdzie indziej — w kolumnie tabeli.
W_GRAWISACH = re.compile(r"`([a-z_]+)`")


def _read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def klasy_z_dokumentu():
    """Zbiór klas zdefiniowanych w `docs/02-simulation.md`."""
    return set(DEFINICJA.findall(_read(MODEL)))


def klasy_w_danych():
    """Wartości pola `status` z danych pojazdu, z licznikiem."""
    z_danych = {}

    def obejdz(node):
        if isinstance(node, dict):
            status = node.get("status")
            if isinstance(status, str):
                z_danych[status] = z_danych.get(status, 0) + 1
            for wartosc in node.values():
                obejdz(wartosc)
        elif isinstance(node, list):
            for wartosc in node:
                obejdz(wartosc)

    obejdz(json.loads(_read(POJAZD)))
    return z_danych


def _tabele(tekst):
    """`(naglowek, wiersze)` dla każdej tabeli markdownu w tekście."""
    linie = tekst.split("\n")
    i = 0
    while i < len(linie) - 1:
        if linie[i].startswith("|") and re.match(r"^\|[\s:|-]+\|$", linie[i + 1]):
            naglowek = [c.strip() for c in linie[i].strip().strip("|").split("|")]
            j, body = i + 2, []
            while j < len(linie) and linie[j].startswith("|"):
                body.append([c.strip() for c in linie[j].strip().strip("|").split("|")])
                j += 1
            yield naglowek, body
            i = j
        else:
            i += 1


def klasy_dokumentu_geometrii():
    """Zbiór statusów, które `docs/21` definiuje we WŁASNEJ tabeli."""
    znane = set()
    for naglowek, body in _tabele(_read(GEOMETRIA)):
        if naglowek != NAGLOWEK_DEFINICJI:
            continue
        for wiersz in body:
            trafienie = KOMORKA_STATUSU.match(wiersz[0]) if wiersz else None
            if trafienie:
                znane.add(trafienie.group(1))
    return znane


def statusy_w_kolumnach_geometrii(tekst=None):
    """`{status: ile}` z KOLUMN `status` tabel `docs/21`, bez tabeli definiującej.

    Tu łapie się nazwa NIEZNANA: kolumna jest miejscem, w którym stoi status i nic
    innego, więc nie trzeba zgadywać.
    """
    znalezione = {}
    for naglowek, body in _tabele(_read(GEOMETRIA) if tekst is None else tekst):
        if naglowek == NAGLOWEK_DEFINICJI or KOLUMNA_STATUSU not in naglowek:
            continue
        k = naglowek.index(KOLUMNA_STATUSU)
        for wiersz in body:
            if k >= len(wiersz):
                continue
            trafienie = KOMORKA_STATUSU.match(wiersz[k])
            if trafienie:
                nazwa = trafienie.group(1)
                znalezione[nazwa] = znalezione.get(nazwa, 0) + 1
    return znalezione


def statusy_uzyte_w_geometrii(tekst=None):
    """`{status: ile}` — wszystkie użycia nazw ze SŁOWNIKA ZAMKNIĘTEGO w `docs/21`.

    `tekst` służy WYŁĄCZNIE kontroli przyrządu: podstawia treść dokumentu bez
    pisania po drzewie. Ta sama droga, co `nadpisz` w bramce swoistości igieł.

    Słownik to suma obu tabel. Nazwa spoza sumy nie jest tu szukana i nie ma być:
    rozstrzyganie na prozie, czy dowolny napis w grawisach jest statusem, jest
    heurystyką, którą 6.D89 zmierzyło jako zawodną.
    """
    slownik = klasy_z_dokumentu() | klasy_dokumentu_geometrii()
    znalezione = {}
    for nazwa in W_GRAWISACH.findall(_read(GEOMETRIA) if tekst is None else tekst):
        if nazwa in slownik:
            znalezione[nazwa] = znalezione.get(nazwa, 0) + 1
    return znalezione


def statusy_obce_bez_zrodla(tekst=None):
    """Statusy użyte w `docs/21`, których ten dokument nie definiuje ani nie przypisuje.

    „Przypisuje" znaczy: w tym samym AKAPICIE stoi nazwa statusu i ścieżka dokumentu,
    który ją definiuje. Nie po całym pliku, bo zdanie o źródle ma stać PRZY nazwie;
    i nie po wierszu, bo zdanie prozy w markdownie łamie się na kilka wierszy — na
    tym pierwsza wersja tej funkcji się wywróciła, uznając za nieprzypisaną nazwę
    opisaną akapit wyżej niż ścieżka (zmierzone 10.09.2026 na własnej poprawce).
    """
    wlasne = klasy_dokumentu_geometrii()
    zrodlo = os.path.relpath(MODEL, ROOT).replace(os.sep, "/")
    tresc = _read(GEOMETRIA) if tekst is None else tekst
    akapity = re.split(r"\n\s*\n", tresc)
    bez = []
    for nazwa in sorted(set(statusy_uzyte_w_geometrii(tekst)) - wlasne):
        przypisany = any("`%s`" % nazwa in akapit and zrodlo in akapit
                         for akapit in akapity)
        if not przypisany:
            bez.append(nazwa)
    return bez


def nazwy_w_grawisach(relative):
    """Napisy `w_grawisach` z pliku — bez rozstrzygania, czy są klasą."""
    return set(re.findall(r"`([a-z_]+)`", _read(os.path.join(ROOT, relative))))


def test_every_status_in_the_geometry_document_is_defined_somewhere():
    """Status z KOLUMNY tabeli `docs/21` należy do sumy obu tabel — 6.D105.

    **Reguła jest tu inna niż dla plików cytujących i to jest cała treść podziału.**
    `CYTUJACY` mają NIE wymieniać klas, tylko odsyłać; dla `docs/21` ta reguła jest
    nieprawdziwa, bo on klasyfikuje wymiary geometrii i ma prawo definiować własne
    nazwy. Reguła dla tej roli brzmi: każdy status UŻYTY musi być gdzieś ZDEFINIOWANY.

    Kolumna, a nie proza: pytanie „czy ten napis w grawisach jest statusem" nie ma
    na prozie pewnej odpowiedzi (6.D89 zgłosiło tak `as_of`). Kolumna `status` jest
    miejscem, w którym stoi status i nic innego.
    """
    slownik = klasy_z_dokumentu() | klasy_dokumentu_geometrii()
    obce = sorted(set(statusy_w_kolumnach_geometrii()) - slownik)
    assert obce == [], (
        "kolumna `status` w %s ma nazwy spoza sumy obu tabel: %s"
        % (os.path.relpath(GEOMETRIA, ROOT), obce))


def test_every_foreign_status_in_the_geometry_document_names_its_source():
    """Nazwa z cudzej tabeli musi mieć w `docs/21` wskazane źródło definicji.

    **Zmierzona usterka 6.D105:** `docs/21` używał `design_model` sześć razy, nie
    definiując go i nie odsyłając po niego nigdzie. Nazwa była czytelna wyłącznie
    dla kogoś, kto wie o istnieniu drugiej tabeli — a dokument nie mówił, że taka
    istnieje.
    """
    bez = statusy_obce_bez_zrodla()
    assert bez == [], (
        "%s używa statusów, których nie definiuje i nie przypisuje do %s: %s"
        % (os.path.relpath(GEOMETRIA, ROOT), os.path.relpath(MODEL, ROOT), bez))


def test_the_two_status_tables_share_exactly_the_two_measured_names():
    """Dwie tabele, dwie nazwy wspólne, po dwie wyłączne — 6.D105.

    Ta asercja jest kotwicą na PODZIAŁ, nie na treść: zlanie tabel w jedną albo
    przeniesienie nazwy z jednej do drugiej jest decyzją właściciela (pole „Poza
    zakresem" pozycji), a nie skutkiem ubocznym edycji dokumentu. Zmierzone
    10.09.2026: wspólne `observed` i `spec`; wyłączne tu `blocked`
    i `design_assumption`, tam `design_model` i `est`.
    """
    geometria = klasy_dokumentu_geometrii()
    model = klasy_z_dokumentu()
    assert geometria & model == {"observed", "spec"}, sorted(geometria & model)
    assert geometria - model == {"blocked", "design_assumption"}, sorted(geometria - model)
    assert model - geometria == {"design_model", "est"}, sorted(model - geometria)


def test_the_geometry_readers_are_parsing_and_not_returning_a_constant():
    """Kontrola przyrządu dla obu czytników `docs/21`, na wejściu syntetycznym.

    Oba mogą zwrócić pusty zbiór i wtedy oba werdykty wyżej są zielone z niewiedzy.
    Sprawdzane jest więc, że czytnik kolumn NAPRAWDĘ czyta kolumnę — i że odsiewa
    komórki, które statusem nie są.
    """
    # Dolne ostrza na dzisiejszym drzewie.
    assert len(klasy_dokumentu_geometrii()) == 4, sorted(klasy_dokumentu_geometrii())
    w_kolumnach = statusy_w_kolumnach_geometrii()
    assert sum(w_kolumnach.values()) >= 17, (
        "kolumny `status` dają %d wystąpień, a 10.09.2026 było ich 17 — czytnik "
        "przestał widzieć tabele" % sum(w_kolumnach.values()))
    assert statusy_uzyte_w_geometrii().get("design_model", 0) >= 6, (
        "`design_model` znika z `docs/21` — jeśli naprawdę zniknął, zdejmij zdanie "
        "o źródle; jeśli nie, czytnik prozy przestał go widzieć")

    # Czytnik kolumn ODSIEWA komórki, które statusem nie są: nazwy profili tunelu
    # i wartość pustą. Zmierzone 10.09.2026 — skan „komórka w grawisach" bez
    # rozpoznania kolumny łapał `box_double`, `bore_single`, `station` i `null`.
    for nie_status in ("box_double", "bore_single", "station", "null"):
        assert nie_status not in w_kolumnach, (
            "czytnik kolumn wziął %r za status — rozpoznanie po nazwie kolumny "
            "przestało działać" % nie_status)

    # PRZYPISANIE IDZIE PO AKAPICIE, nie po całym pliku, i to jest sprawdzane na
    # wejściu syntetycznym — bo na dzisiejszym dokumencie obie reguły dają to samo.
    # Zmierzone 10.09.2026: rozluźnienie do „gdziekolwiek w pliku" nie zapalało
    # niczego, więc granica akapitu nie była przez nic przybita.
    zrodlo = os.path.relpath(MODEL, ROOT).replace(os.sep, "/")
    rozdzielone = ("Tu stoi `design_model` i nic poza tym.\n"
                   "\n"
                   "A tu, akapit dalej, stoi ścieżka %s.\n" % zrodlo)
    assert statusy_obce_bez_zrodla(rozdzielone) == ["design_model"], (
        "nazwa i ścieżka w RÓŻNYCH akapitach uchodzą za przypisanie: %s"
        % statusy_obce_bez_zrodla(rozdzielone))
    razem = "Tu stoi `design_model`, a definiuje ją %s.\n" % zrodlo
    assert statusy_obce_bez_zrodla(razem) == [], (
        "nazwa i ścieżka w TYM SAMYM akapicie nie uchodzą za przypisanie: %s"
        % statusy_obce_bez_zrodla(razem))

    # TABELA DEFINIUJĄCA NIE JEST UŻYCIEM, i to też idzie przez wejście syntetyczne:
    # na dzisiejszym dokumencie wliczenie jej podniosłoby tylko liczby, nie zmieniając
    # ani jednego werdyktu, więc wyłączenie nie było przez nic przybite (zmierzone
    # 10.09.2026 kontrolą, która wyszła zielona).
    sama_definicja = ("| status | znaczenie |\n|---|---|\n"
                      "| **`spec`** | wartość ze źródła |\n")
    assert statusy_w_kolumnach_geometrii(sama_definicja) == {}, (
        "tabela DEFINIUJĄCA policzona jako użycie: %s"
        % statusy_w_kolumnach_geometrii(sama_definicja))
    uzycie = ("| wymiar | wartość | status |\n|---|---|---|\n"
              "| coś | 1 m | `spec` |\n")
    assert statusy_w_kolumnach_geometrii(uzycie) == {"spec": 1}, (
        "tabela UŻYWAJĄCA nie została policzona: %s"
        % statusy_w_kolumnach_geometrii(uzycie))

    # I że rozpoznanie tabeli jest strukturalne, a nie po tekście dokumentu.
    syntetyk = ("| wymiar | wartość | status |\n|---|---|---|\n"
                "| coś | 1 m | `nie_ma_takiego` |\n")
    naglowki = [n for n, _b in _tabele(syntetyk)]
    assert naglowki == [["wymiar", "wartość", "status"]], naglowki


def test_no_citing_file_repeats_the_class_list():
    """Plik cytujący ODSYŁA do dokumentu, zamiast powtarzać listę klas — 6.D89.

    **Reguła jest odwrotna, niż wygląda na pierwszy rzut oka, i to jest wybór.**
    Naturalne „każda cytowana nazwa musi być znana" wymaga rozstrzygnięcia, KTÓRY
    napis w grawisach jest nazwą klasy — a to jest heurystyka. Pierwsza wersja tej
    bramki próbowała po akapicie zawierającym słowo „klas" i zgłosiła `as_of`
    z listy pól metadanych, czyli nazwę, która klasą nie jest. Heurystyka na tekście
    prozy nie ma jak być pewna.

    Reguła dzisiejsza pytania nie stawia: plik cytujący **nie wymienia klas w ogóle**,
    tylko odsyła do `docs/02-simulation.md`. Powtórzona lista jest drugą kopią tej
    samej wiedzy i rozjeżdża się z pierwszą — dokładnie to zmierzono w 6.D89.

    **Czego ta bramka nie złapie i mówię to wprost:** nazwy zupełnie nowej, która nie
    jest ani klasą zdefiniowaną, ani wycofaną. Złapie ponowne wpisanie listy i powrót
    nazwy wycofanej — czyli dwa kształty, które w tym repozytorium wystąpiły.
    """
    znane = klasy_z_dokumentu()
    assert len(znane) >= 4, (
        "dokument modelu definiuje %d klas — wzorzec definicji rozjechał się "
        "z treścią `docs/02-simulation.md`: %s" % (len(znane), sorted(znane)))

    zle = []
    for relative in CYTUJACY:
        w_pliku = nazwy_w_grawisach(relative)
        for nazwa in sorted(w_pliku & znane):
            zle.append((relative, nazwa, "klasa wymieniona zamiast odesłania"))
        for nazwa in sorted(w_pliku & set(WYCOFANE)):
            zle.append((relative, nazwa, WYCOFANE[nazwa]))
    assert zle == [], "\n".join(
        "%s: `%s` — %s" % (relative, nazwa, powod) for relative, nazwa, powod in zle)


def test_every_citing_file_points_at_the_document():
    """Odesłanie musi BYĆ, a nie tylko nie być listą.

    Bez tego wiersza bramka wyżej jest zielona także dla pliku, który o klasach nie
    mówi NIC — czyli dla skrótu, z którego wypadło jedyne zdanie kierujące czytelnika
    do definicji.
    """
    for relative in CYTUJACY:
        tekst = _read(os.path.join(ROOT, relative))
        assert "docs/02-simulation.md" in tekst, (
            "%s nie odsyła do `docs/02-simulation.md`, a to jedyne źródło nazw klas"
            % relative)


def test_every_status_in_the_vehicle_data_is_a_defined_class():
    """Każda wartość `status` w danych pojazdu należy do zbioru z dokumentu."""
    znane = klasy_z_dokumentu()
    w_danych = klasy_w_danych()
    assert w_danych, "w danych pojazdu nie ma ani jednego pola `status` — skan oślepł"

    obce = sorted(k for k in w_danych if k not in znane)
    assert obce == [], (
        "dane pojazdu używają klas %s, których `docs/02-simulation.md` nie definiuje "
        "(zna: %s)" % (obce, ", ".join(sorted(znane))))


def test_the_class_set_is_parsed_and_not_a_third_copy():
    """Kontrola przyrządu: zbiór ma pochodzić z dokumentu, a nie z listy w teście.

    Dopisanie klasy do dokumentu **nie może** niczego zapalić — tego wprost żąda pole
    „Skończone, gdy". Test podstawia dokument z klasą dodatkową i sprawdza, że parser
    ją widzi; gdyby zbiór był wpisany w ten plik, nowa nazwa byłaby dla niego obca.
    """
    import tempfile

    global MODEL
    prawdziwy = MODEL
    prawdziwe_klasy = klasy_z_dokumentu()
    try:
        with tempfile.TemporaryDirectory(prefix="mbxl-klasy-") as katalog:
            MODEL = os.path.join(katalog, "02-simulation.md")
            with open(MODEL, "w", encoding="utf-8") as uchwyt:
                uchwyt.write("Parametry mają provenance: `spec` = źródło, "
                             "`nowa_klasa` = coś nowego.\n")
            assert klasy_z_dokumentu() == {"spec", "nowa_klasa"}, klasy_z_dokumentu()

            # I kierunek przeciwny: napis w grawisach BEZ znaku równości nie jest
            # definicją klasy, tylko nazwą parametru albo ścieżką.
            with open(MODEL, "w", encoding="utf-8") as uchwyt:
                uchwyt.write("Wartość `masa_awo` jest w `data/vehicle/m7-spec.json`.\n")
            assert klasy_z_dokumentu() == set(), klasy_z_dokumentu()
    finally:
        MODEL = prawdziwy

    assert klasy_z_dokumentu() == prawdziwe_klasy, (
        "po przywróceniu parser nie widzi prawdziwego dokumentu — podstawienie "
        "wyciekło i dwie bramki wyżej mierzyłyby atrapę")


def test_the_document_still_defines_the_four_classes_the_measurement_found():
    """Kotwica na pomiarze z 10.09.2026 — bo cztery bramki wyżej są dziś ciche.

    Zbiór jest parsowany, więc jego ZAWĘŻENIE nie zapala niczego: gdyby dokument
    przestał definiować `observed`, obie bramki nadal by milczały, bo nikt jej nie
    cytuje. Ten wiersz mówi, że zawężenie ma być WIDOCZNE w diffie.
    """
    znane = klasy_z_dokumentu()
    zmierzone = {"spec", "observed", "est", "design_model"}
    assert zmierzone <= znane, (
        "z dokumentu zniknęły klasy %s — zawężenie słownika ma być widoczne "
        "w commicie, a nie ciche" % sorted(zmierzone - znane))

    # `est` nie występuje w danych ANI RAZU i to jest stan poprawny: dokument
    # definiuje ją jako „oszacowanie historyczne do usunięcia/weryfikacji", więc
    # jej obecność w danych byłaby usterką, a nie jej brak.
    w_danych = klasy_w_danych()
    assert w_danych.get("est", 0) == 0, (
        "w danych pojazdu pojawiła się klasa `est` (%d razy) — dokument opisuje ją "
        "jako oszacowanie DO USUNIĘCIA" % w_danych.get("est", 0))
    assert set(w_danych) == {"spec", "design_model"}, (
        "rozkład klas w danych pojazdu zmienił się: %s" % sorted(w_danych))


def test_zadna_klasa_zakazana_nie_wraca_do_danych():
    """6.D134: `est` ma zero użyć w CAŁYM katalogu danych, nie tylko w pliku pojazdu.

    **Co tu jest nowe wobec asercji z 6.D89.** Tamta pytała `klasy_w_danych()`, czyli
    wyłącznie `data/vehicle/m7-spec.json`. Pole `status` stoi w **21** plikach JSON
    pod `data/`, o zupełnie różnych słownikach, więc nazwa wycofana mogła wrócić
    w dowolnym z pozostałych dwudziestu i nie zgłosiłoby tego nic.

    **Zakazane są WYMIENIONE z nazwy, a nie wyliczone ze słownika modelu** — i nie jest
    to ostrożność, tylko liczba. Gdyby bramka żądała, żeby każdy status w `data/` należał
    do klas z `docs/02-simulation.md`, zapaliłaby się na **17 z 21 plików** i **18
    nazwach** (`ok`, `unknown`, `source_backed`, `permission_required`, `not_modelled`…),
    bo to słowniki INNYCH dziedzin — praw, torów, stacji — a nie provenance modelu jazdy.
    Asercja niżej wykonuje tamtą regułę i żąda dokładnie tych liczb, żeby zdanie „byłaby
    szumem" nie stało się opinią.
    """
    w_danych = statusy_w_katalogu_danych()
    assert len(w_danych) >= 21, (
        "pole `status` znaleziono w %d plikach — obecny pomiar mówił 21, "
        "więc skan oślepł albo katalog się skurczył" % len(w_danych))

    trafienia = sorted(
        (plik, nazwa, ile)
        for plik, licznik in w_danych.items()
        for nazwa, ile in licznik.items()
        if nazwa in ZAKAZANE_W_DANYCH)
    assert trafienia == [], (
        "do danych wróciła klasa zakazana (plik, nazwa, ile): %s — powody: %s"
        % (trafienia, "; ".join("`%s`: %s" % (n, p)
                                for n, p in sorted(ZAKAZANE_W_DANYCH.items()))))

    # Reguła ODRZUCONA, wykonana tutaj: „każdy status musi być klasą modelu".
    znane = klasy_z_dokumentu()
    obce = {plik: sorted(n for n in licznik if n not in znane)
            for plik, licznik in w_danych.items()}
    plikow = sorted(plik for plik, nazwy in obce.items() if nazwy)
    nazw = sorted({n for nazwy in obce.values() for n in nazwy})
    assert (len(plikow), len(nazw)) == (17, 18), (
        "reguła „każdy status jest klasą modelu” zapaliłaby się dziś na %d plikach "
        "i %d nazwach, a obecny pomiar mówił 17 i 18 — pliki: %s, nazwy: %s"
        % (len(plikow), len(nazw), plikow, nazw))


def test_kazda_klasa_zakazana_jest_ZDEFINIOWANA_w_dokumencie_modelu():
    """Zakaz dotyczy nazwy, którą dokument zna — inaczej byłby zakazem na wyrost.

    `est` jest w danych zakazane WŁAŚNIE dlatego, że `docs/02-simulation.md` opisuje ją
    jako oszacowanie do usunięcia. Gdyby dokument przestał ją definiować, zakaz
    straciłby podstawę i miałby zniknąć razem z nią — a nie zostać jako reguła bez
    źródła. To jest ta sama zasada, którą 6.D89 zapisało dla `WYCOFANE`, tylko
    z przeciwnym znakiem.
    """
    znane = klasy_z_dokumentu()
    bez_definicji = sorted(n for n in ZAKAZANE_W_DANYCH if n not in znane)
    assert bez_definicji == [], (
        "zakaz na klasę, której dokument modelu nie definiuje: %s — zakaz ma stać "
        "przy definicji, a nie zamiast niej" % bez_definicji)

    assert set(ZAKAZANE_W_DANYCH) == {"est"}, (
        "lista zakazanych to %s — pomiar z 11.09.2026 znał jedną taką nazwę"
        % sorted(ZAKAZANE_W_DANYCH))


def test_wpis_est_w_danych_syntetycznych_ZAPALA_bramke():
    """Kontrola przyrządu na drzewie probnym, obie strony w jednym teście.

    Skan idzie przez `statusy_w_katalogu_danych`, a nie przez ręcznie złożony słownik —
    inaczej mierzyłby moje wyobrażenie o czytniku zamiast czytnika (lekcja z 6.D131).
    """
    import tempfile

    with tempfile.TemporaryDirectory(prefix="mbxl-est-") as katalog:
        with open(os.path.join(katalog, "czyste.json"), "w", encoding="utf-8") as u:
            json.dump({"a": {"status": "spec"}, "b": [{"status": "design_model"}]}, u)
        czyste = statusy_w_katalogu_danych(katalog)
        assert czyste == {"czyste.json": {"spec": 1, "design_model": 1}}, czyste
        assert [n for l in czyste.values() for n in l if n in ZAKAZANE_W_DANYCH] == [], (
            "czyste dane syntetyczne zgłosiły klasę zakazaną: %s" % czyste)

        with open(os.path.join(katalog, "zepsute.json"), "w", encoding="utf-8") as u:
            json.dump({"masa": {"status": "est", "wartosc": 155000}}, u)
        zepsute = statusy_w_katalogu_danych(katalog)
        trafienia = sorted((plik, nazwa) for plik, licznik in zepsute.items()
                           for nazwa in licznik if nazwa in ZAKAZANE_W_DANYCH)
        assert trafienia == [("zepsute.json", "est")], (
            "wpis `est` w danych syntetycznych NIE zapalił skanu: %s" % zepsute)


def test_dokument_definiujacy_status_bramki_nie_zapala():
    """Druga połowa pola „Skończone, gdy": definicja ma być cicha — SPRAWDZONE WPROST.

    Pierwsza wersja tego testu twierdziła, że dokument nie wchodzi do skanu, bo filtr
    rozszerzeń przepuszcza tylko `.json`. Uzasadnienie było niepełne i pokazały to
    **dwie kontrole ZIELONE**: KN-5 (dopisanie `.md` do filtru) 14/14 i KN-5b (czytnik
    tekstowy zamiast parsera) 14/14. Obrony są **dwie i każda wystarcza sama**, więc
    zdjęcie jednej nie zmienia nic; dopiero KN-5c, zdejmująca obie naraz, jest czerwona
    i wypisuje dokument z `est: 1` jako UŻYCIEM.

    Test kładzie więc dziś prawdziwy dokument w drzewie probnym i pyta skan wprost,
    zamiast wnioskować z rozszerzenia albo z parsera — bo o tym, które z dwóch zabezpieczeń
    zadziałało, wnioskować nie trzeba, gdy można zapytać o wynik.
    """
    import shutil
    import tempfile

    assert "est" in klasy_z_dokumentu(), (
        "dokument modelu przestał definiować `est` — wtedy zakaz ma zniknąć razem "
        "z definicją, a nie zostać regułą bez źródła")

    with tempfile.TemporaryDirectory(prefix="mbxl-def-") as katalog:
        shutil.copy(MODEL, os.path.join(katalog, "02-simulation.md"))
        with open(os.path.join(katalog, "dane.json"), "w", encoding="utf-8") as u:
            json.dump({"x": {"status": "spec"}}, u)
        widziane = statusy_w_katalogu_danych(katalog)

    assert widziane == {"dane.json": {"spec": 1}}, (
        "skan obok danych zobaczył dokument DEFINIUJĄCY klasy: %s — wtedy definicja "
        "`est` byłaby jej użyciem i bramka zapalałaby się na źródle" % widziane)


def test_gole_slowo_est_w_danych_to_francuszczyzna_a_nie_status():
    """**Dlaczego ta bramka nie jest grepem — pokazane liczbą, a nie opisane.**

    Gołe słowo `est` stoi w `data/` **7 razy w 4 plikach**, i wszystkie siedem to
    francuski: cztery w adresach STIB (`…-on-en-est-ou`, `…-m7-est-arrive-…`), trzy
    w cytacie z EIE («la profondeur des quais … est d'environ 11 m»). Prawdziwych
    trafień: **zero**. Bramka po samym słowie byłaby więc czystym szumem — siedem
    alarmów, z których ani jeden nie mówi o statusie.

    Liczba jest przybita równością w OBIE strony: jej spadek znaczyłby, że któryś
    z cytatów zniknął (a `data/` jest do odczytu), a wzrost — że doszedł tekst, którego
    ta bramka nie obejrzała.
    """
    trafienia = {}
    for gdzie, _katalogi, pliki in TW.walk(DANE, DANE):
        for nazwa in sorted(pliki):
            sciezka = os.path.join(gdzie, nazwa)
            try:
                tresc = _read(sciezka)
            except (OSError, UnicodeDecodeError):
                continue
            ile = len(SLOWO_EST.findall(tresc))
            if ile:
                trafienia[os.path.relpath(sciezka, DANE).replace(os.sep, "/")] = ile

    assert sum(trafienia.values()) == EST_JAKO_SLOWO_W_DANYCH, (
        "gołych wystąpień słowa `est` w `data/` jest %d, pomiar z 11.09.2026 mówił "
        "%d: %s" % (sum(trafienia.values()), EST_JAKO_SLOWO_W_DANYCH,
                    sorted(trafienia.items())))
    assert len(trafienia) == EST_JAKO_SLOWO_PLIKOW, (
        "plików z gołym `est` jest %d, pomiar mówił %d: %s"
        % (len(trafienia), EST_JAKO_SLOWO_PLIKOW, sorted(trafienia)))

    # I strona druga: ani jedno z tych siedmiu nie jest wartością pola `status`.
    w_polach = [nazwa for licznik in statusy_w_katalogu_danych().values()
                for nazwa in licznik if nazwa == "est"]
    assert w_polach == [], (
        "słowo `est` jest jednak wartością pola `status` — wtedy zdanie o siedmiu "
        "fałszywych trafieniach przestaje być prawdziwe: %s" % w_polach)


# 6.D25: uruchomienie tego pliku WPROST idzie tą samą drogą, co cały zestaw.
def test_statusy_w_kolumnach_csv_zgadzaja_sie_z_pomiarem():
    """Spis statusów spoza JSON-ów, przybity — 6.D150.

    Skan z 6.D134 czyta wyłącznie pliki JSON, a status potrafi stać w KOLUMNIE.
    Bez tego spisu nazwa wycofana mogłaby wrócić do `data/` w formacie, którego
    nie ogląda nic.
    """
    zmierzone = statusy_w_kolumnach_csv()
    assert zmierzone == STATUSY_CSV, (
        "statusy w kolumnach CSV rozjechały się z pomiarem z 12.09.2026: %s zamiast %s"
        % (zmierzone, STATUSY_CSV))


def test_kazdy_plik_CSV_pod_data_ma_kolumne_statusu_w_tabeli():
    """Pole „Skończone, gdy" 6.D150: żaden plik poza skanem bez zapisanego powodu.

    Plik CSV bez rozpoznanej kolumny statusu wypadałby ze spisu po cichu — a spis
    pusty czyta się jak „czysto", nie jak „nie przeczytano".
    """
    wszystkie = pliki_csv_pod_danymi()
    assert wszystkie, "pod `data/` nie ma ani jednego CSV — skan mierzy wtedy nic"

    poza = [p for p in wszystkie if p not in statusy_w_kolumnach_csv()]
    assert poza == [], (
        "plik CSV pod `data/` stoi poza skanem statusów: %s — albo jego nagłówek "
        "kolumny trzeba dopisać do `KOLUMNY_STATUSU_CSV`, albo zapisać, dlaczego "
        "statusu nie niesie" % poza)


def test_zadna_klasa_zakazana_nie_stoi_w_kolumnie_csv():
    """`est` jest zakazane W DANYCH, a kolumna CSV jest danymi — 6.D150.

    To NIE jest złączenie słowników (patrz test niżej): klasa zakazana obowiązuje
    wszędzie, gdzie stoi status, niezależnie od tego, jakim słownikiem posługuje się
    dany plik.
    """
    trafienia = []
    for sciezka, kolumny in statusy_w_kolumnach_csv().items():
        for kolumna, licznik in kolumny.items():
            for nazwa in licznik:
                if nazwa in ZAKAZANE_W_DANYCH:
                    trafienia.append((sciezka, kolumna, nazwa, licznik[nazwa]))
    assert trafienia == [], (
        "klasa zakazana wróciła do danych przez kolumnę CSV: %s — %s"
        % (trafienia, [ZAKAZANE_W_DANYCH[t[2]] for t in trafienia]))


def test_slownik_CSV_jest_OSOBNY_od_slownika_modelu():
    """ROZSTRZYGNIĘCIE 6.D150, policzone — słowniki się NIE spotykają.

    Pole „Dlaczego" pytało, czy `estimated` z CSV i `est` z modelu mają wejść do
    jednego słownika. Odpowiada przecięcie zbiorów:

    - słownik `station-depths.csv` (zadeklarowany w NAGŁÓWKU tego pliku:
      `# confidence: measured | counted | estimated | unknown`) a klasy modelu
      z `docs/02-simulation.md` — **przecięcie puste**;
    - ten sam słownik a statusy z JSON-ów pod `data/` — wspólne jest **jedno** słowo,
      `unknown`, stojące w JSON-ach 268 razy, czyli najogólniejsze, jakie może być.

    Dwa słowniki opisują dwie różne rzeczy: klasy modelu mówią, SKĄD wzięto parametr
    jazdy, a kolumna `confidence` — jak pewny jest POMIAR głębokości. Złączenie ich
    uczyniłoby `estimated` zakazanym, czyli wymagałoby zmiany klasyfikacji trzech
    wierszy, których pole „Poza zakresem" tej pozycji dotykać zabrania — i akurat
    tych trzech, które jako jedyne w pliku niosą cytat ze źródła i podaną precyzję.
    """
    slownik_csv = set(SLOWNIK_STATION_DEPTHS)
    assert slownik_csv & klasy_z_dokumentu() == set(), (
        "słownik CSV zaczął się przecinać z klasami modelu: %s — wtedy pytanie "
        "o złączenie trzeba postawić od nowa"
        % sorted(slownik_csv & klasy_z_dokumentu()))

    w_jsonach = set()
    for licznik in statusy_w_katalogu_danych().values():
        w_jsonach |= set(licznik)
    assert slownik_csv & w_jsonach == {"unknown"}, (
        "wspólne słowa CSV i JSON-ów to %s, a pomiar z 12.09.2026 dał samo `unknown`"
        % sorted(slownik_csv & w_jsonach))

    # I że słownik z nagłówka pliku jest tym, którego plik NAPRAWDĘ używa — inaczej
    # zdanie wyżej mówiłoby o deklaracji, a nie o danych.
    uzyte = set(statusy_w_kolumnach_csv()["network/station-depths.csv"]["confidence"])
    assert uzyte <= slownik_csv, (
        "kolumna niesie status spoza słownika zadeklarowanego w nagłówku pliku: %s"
        % sorted(uzyte - slownik_csv))


def test_czytnik_csv_pomija_komentarze_i_widzi_est_wstawione_do_kolumny():
    """Kontrola przyrządu na drzewie probnym — 6.D150.

    **Dwie pułapki naraz, obie zmierzone.** Pierwsza: `csv.DictReader` puszczony na
    ten plik wprost bierze za nagłówek pierwszy wiersz komentarza i czyta całość jako
    JEDNĄ kolumnę — stąd `confidence` 1× we wpisie pozycji, czyli policzony NAGŁÓWEK.
    Druga: pole „Weryfikacja" żąda, żeby `est` wstawione do kolumny zapaliło bramkę,
    a na dzisiejszym drzewie żadnego `est` nie ma, więc rozstrzyga wejście syntetyczne.
    """
    with tempfile.TemporaryDirectory() as katalog:
        sciezka = os.path.join(katalog, "proba.csv")
        with open(sciezka, "w", encoding="utf-8") as uchwyt:
            uchwyt.write("# komentarz jeden\n"
                         "# confidence: measured | estimated\n"
                         "line,confidence,note\n"
                         "L1,estimated,x\n"
                         "L2,est,y\n"
                         "L3,,pusty status nie liczy sie\n")

        wynik = statusy_w_kolumnach_csv(katalog)
        assert wynik == {"proba.csv": {"confidence": {"estimated": 1, "est": 1}}}, wynik

        zakazane = [n for n in wynik["proba.csv"]["confidence"] if n in ZAKAZANE_W_DANYCH]
        assert zakazane == ["est"], (
            "`est` wstawione do kolumny CSV nie zostało rozpoznane jako klasa "
            "zakazana: %s" % wynik)

        # Pułapka pierwsza, wykonana: czytnik NIEPOMIJAJĄCY komentarzy widzi jedną
        # kolumnę o nazwie pierwszego komentarza i ani jednego statusu.
        with open(sciezka, encoding="utf-8") as uchwyt:
            naiwny = list(csv.DictReader(uchwyt))
        assert list(naiwny[0]) == ["# komentarz jeden"], (
            "`csv.DictReader` przestał brać komentarz za nagłówek — jeśli to zmiana "
            "w bibliotece, akapit przy `STATUSY_CSV` trzeba przeczytać jeszcze raz: %s"
            % list(naiwny[0]))
        assert "confidence" not in naiwny[0], naiwny[0]


if __name__ == "__main__":
    sys.path.insert(0, os.path.join(ROOT, "tools", "tests"))
    import test_all
    raise SystemExit(test_all.main(__file__))
