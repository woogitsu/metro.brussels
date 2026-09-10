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
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

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


# 6.D25: uruchomienie tego pliku WPROST idzie tą samą drogą, co cały zestaw.
if __name__ == "__main__":
    sys.path.insert(0, os.path.join(ROOT, "tools", "tests"))
    import test_all
    raise SystemExit(test_all.main(__file__))
