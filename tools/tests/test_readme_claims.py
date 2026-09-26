#!/usr/bin/env python3
"""README podaje liczby i wersje — ta bramka liczy je z repozytorium i porównuje.

Powód: na `e982bc0` README twierdził „41 plików" w `src/Sim/` (było 44), „Siedem
workflowów" (było 10) i „Godot 4.3 mono" w dwóch miejscach (`config/features`
mówi 4.7 od #121). Żadna bramka tego nie łapała, bo README był jedynym miejscem,
w którym te liczby stały — a liczba stojąca w jednym miejscu i nigdzie nie liczona
rozjeżdża się bezszelestnie.

Zasada tego modułu: **nie ma tu ani jednej oczekiwanej liczby**. Prawdę liczy
`os.walk` po `src/Sim/`, `glob` po `.github/workflows/` i `config/features`
z `src/Game/project.godot`; README jest stroną porównywaną, nigdy źródłem.
Wpisanie tu „44" byłoby drugą kopią tej samej wiedzy i rozjechałoby się dokładnie
tak samo jak pierwsza.

Bramka działa w obie strony:
  - README mówi mniej/inaczej niż repozytorium → pada (ktoś zepsuł README);
  - repozytorium rośnie, README stoi → pada (README nie dotrzymało kroku).
Druga strona jest tą, która się faktycznie rozjechała.

Kontrakt na README, od którego zależy parsowanie:
  - **pierwszy akapit sekcji `## CI`** jest listą workflowów i niczym innym: każdy
    token w grawisach w tym akapicie jest nazwą pliku workflow bez `.yml`, a przed
    słowem „workflowów" stoi ich liczba słownie. Zdania o runnerze, etykietach
    i o tym, który workflow nie jest bramką, należą do dalszych akapitów — inaczej
    `self-hosted` wjechałby na listę workflowów;
  - liczba plików rdzenia stoi jako „N plików `.cs`" / „N pliki `.cs`" w akapicie
    o `src/Sim/`. Jednostka jest jawna, bo „41 plików" nie dało się sprawdzić
    poleceniem: nie wiadomo było, czy liczy `.csproj`;
  - każda wzmianka wersji silnika ma postać „Godot X.Y" albo „Godot X.Y.Z".
"""
import glob
import json
import os
import re
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tree_walk as TW  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "track"))
sys.path.insert(0, os.path.join(ROOT, "tools", "blender"))

import station_components as SC  # noqa: E402
import m7_cab as CAB  # noqa: E402

README = os.path.join(ROOT, "README.md")
SIM_DIR = os.path.join(ROOT, "src", "Sim")
WORKFLOW_DIR = os.path.join(ROOT, ".github", "workflows")
PROJECT_GODOT = os.path.join(ROOT, "src", "Game", "project.godot")

# Liczebniki, którymi README zapisuje liczbę workflowów. Prozą, nie cyfrą — więc
# bramka musi umieć je przeczytać. To słownik języka, nie kopia stanu repozytorium.
NUMERALS = {
    "jeden": 1, "dwa": 2, "trzy": 3, "cztery": 4, "pięć": 5, "sześć": 6,
    "siedem": 7, "osiem": 8, "dziewięć": 9, "dziesięć": 10, "jedenaście": 11,
    "dwanaście": 12, "trzynaście": 13, "czternaście": 14, "piętnaście": 15,
    "szesnaście": 16, "siedemnaście": 17, "osiemnaście": 18, "dziewiętnaście": 19,
    "dwadzieścia": 20,
}


def _read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def test_readme_package_a_distance_matches_track_data():
    """README nie może utrzymywać starego, krótszego kilometrażu pakietu A."""
    text = _read(README)
    match = re.search(r"jeden skład M7 jedzie ([0-9]+,[0-9]+) km po pakiecie A", text)
    assert match, "README nie podaje kilometrażu pakietu A w oczekiwanym zdaniu"
    with open(os.path.join(ROOT, "data", "track", "L1_A.json"), encoding="utf-8") as handle:
        length_m = json.load(handle)["length_m"]
    expected = f"{length_m / 1000:.2f}".replace(".", ",")
    assert match.group(1) == expected, (
        f"README podaje {match.group(1)} km, a data/track/L1_A.json wskazuje {expected} km"
    )


# --- prawda z repozytorium -------------------------------------------------

def core_files():
    """Pliki `.cs` w `src/Sim/`, bez wyjścia budowy. Zwraca ścieżki relatywne."""
    # 6.D97: bez własnej listy katalogów budowania. `TW.walk` odsiewa je z `.gitignore`,
    # gdzie stoją `bin` i `obj` obok `build`, `renders` i `.venv` — druga, uboższa
    # kopia tej listy rozjechałaby się przy pierwszym nowym wpisie.
    found = []
    for base, _dirs, names in TW.walk(SIM_DIR):
        for name in names:
            if name.endswith(".cs"):
                found.append(os.path.relpath(os.path.join(base, name), ROOT))
    return sorted(found)


def workflow_stems():
    """Nazwy plików `.github/workflows/*.yml` bez rozszerzenia."""
    paths = glob.glob(os.path.join(WORKFLOW_DIR, "*.yml"))
    return sorted(os.path.basename(p)[: -len(".yml")] for p in paths)


def project_godot_minor(text):
    """`4.7` z `config/features=PackedStringArray("4.7", ...)`."""
    match = re.search(r'config/features=PackedStringArray\("([0-9]+\.[0-9]+)"', text)
    return match.group(1) if match else None


# --- to, co twierdzi README ------------------------------------------------

def readme_core_file_count(text):
    """Liczba z „`src/Sim/`, N plików `.cs`". None, gdy README tego nie podaje."""
    match = re.search(r"`src/Sim/`,\s*([0-9]+)\s+plik\w*\s+`\.cs`", text)
    return int(match.group(1)) if match else None


def ci_list_paragraph(text):
    """Pierwszy akapit sekcji `## CI`. None, gdy sekcji nie ma."""
    match = re.search(r"^## CI\s*$(.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL)
    if not match:
        return None
    paragraphs = [p for p in match.group(1).split("\n\n") if p.strip()]
    return paragraphs[0] if paragraphs else None


def readme_workflow_count(paragraph):
    """Liczebnik przed słowem „workflowów", np. „Dziesięć" -> 10."""
    match = re.search(r"(\w+)\s+workflow\w*", paragraph or "", re.UNICODE)
    if not match:
        return None
    return NUMERALS.get(match.group(1).lower())


def readme_workflow_names(paragraph):
    """Tokeny w grawisach z akapitu listy workflowów."""
    return sorted(set(re.findall(r"`([^`]+)`", paragraph or "")))


def readme_godot_versions(text):
    """Wszystkie wzmianki „Godot X.Y[.Z]" w README, w kolejności wystąpienia."""
    return re.findall(r"Godot\s+([0-9]+\.[0-9]+(?:\.[0-9]+)?)", text)


def minor(version):
    """`4.7.2` i `4.7` sprowadzone do wspólnego `4.7`."""
    match = re.match(r"([0-9]+\.[0-9]+)", version or "")
    return match.group(1) if match else None


# --- bramki ---------------------------------------------------------------

#: Sekcja README, w której stoją zdania o BRAKACH.
SEKCJA_BRAKOW = "**Czego nie ma i dlaczego:**"

#: Zdanie o braku ZDOLNOŚCI wobec nazw, których istnienie mu przeczy — 6.D87.
#:
#: Klucz to fragment zdania z README; wartość to nazwy, które muszą znaleźć się
#: w `src/Sim/`, żeby zdanie było NIEPRAWDZIWE. Bramka pada, gdy oba są obecne
#: naraz: zdanie mówi „rdzeń tego nie potrafi", a nazwa dowodzi, że potrafi.
#:
#: **Nazwy, nie liczby.** Pole „Skończone, gdy" pozycji 6.D87 zabrania liczenia
#: plików i wierszy wprost, i słusznie: liczba rośnie od pisania czegokolwiek, więc
#: bramka na liczbie zapala się na zmianie bez skutku (6.D27). Nazwa albo w rdzeniu
#: jest, albo jej nie ma.
#:
#: **Zmierzone 10.09.2026.** README mówiło „Rdzeń prowadzi jeden skład. T-320 jest
#: następnym zadaniem" — obie połowy nieprawdziwe: `LineCore` trzyma
#: `List<LineTrain> _trains`, wystawia `IReadOnlyList<LineTrain> Trains` i ma testy
#: `Drugi_sklad_zatrzymuje_sie_przed_blokiem_zajetym_przez_pierwszy` oraz
#: `Zaden_sklad_nie_wjezdza_w_blok_zajety_przez_inny`, a T-320 stoi w `docs/TASKS.md`
#: jako `[~] W TOKU` z etapem 2 zrobionym, nie jako następne zadanie. Jeden skład
#: jest prawdą o WIDOKU: `src/Game/FirstRun.cs` ma jeden węzeł `TrainView`.
ZAPRZECZENIA = {
    "Rdzeń prowadzi jeden skład": ("src/Sim/Line/LineCore.cs",
                                   ["List<LineTrain> _trains",
                                    "IReadOnlyList<LineTrain> Trains"]),
}


#: Pięć punktów sekcji „Czego nie ma", każdy identyfikowany fragmentem swojego
#: pierwszego zdania. Lista jest zamknięta i sprawdzana: bramka niżej żąda, żeby
#: KAŻDY punkt sekcji miał rozstrzygnięcie, a każde rozstrzygnięcie — swój punkt.
PUNKTY_BRAKOW = (
    "profilu pionowego",
    "stacji wynikających z danych",
    "wielu składów W SCENIE",
    "wiernego wnętrza kabiny",
    "ciągłego kilometrażu linii",
)


def _osie():
    """Pliki osi z `data/track/`, bez plików pochodzenia. Tylko do czytania."""
    import glob
    return sorted(f for f in glob.glob(os.path.join(ROOT, "data", "track", "*.json"))
                  if ".provenance." not in os.path.basename(f))


def osie_plaskie():
    """Ile osi ma nadal `vertical.status = not_modelled` i wszystkie Z równe zeru.

    To jest liczba, przy której zdanie „nie ma profilu pionowego" jest PRAWDZIWE.
    Spadnie w chwili, w której pierwsza oś dostanie rzędne — i wtedy README ma
    o tym powiedzieć, zamiast zostać przy zdaniu z dnia, w którym rzędnych nie było.
    """
    ile = 0
    for sciezka in _osie():
        with open(sciezka, encoding="utf-8") as handle:
            dane = json.load(handle)
        plaska = all(abs(punkt[2]) == 0.0 for punkt in dane["points"])
        if plaska and (dane.get("vertical") or {}).get("status") == "not_modelled":
            ile += 1
    return ile


def wezly_skladu_w_scenie():
    """Ile węzłów `TrainView` ma scena pierwszego przejazdu.

    Zdanie „scena pokazuje jeden [skład]" jest prawdziwe dokładnie przy jedynce.
    Liczone w SCENIE, a nie w kodzie: `FirstRun.cs` mógłby wołać `GetNode` w pętli,
    a i tak zobaczyłby tyle składów, ile ich w `.tscn` stoi.
    """
    sciezka = os.path.join(ROOT, "src", "Game", "Scenes", "FirstRun.tscn")
    tekst = _read(sciezka)
    zasob = re.search(r'\[ext_resource type="Script" path="res://World/TrainView\.cs" '
                      r'id="([^"]+)"\]', tekst)
    if zasob is None:
        return 0
    return len(re.findall(r'script = ExtResource\("%s"\)' % re.escape(zasob.group(1)),
                          tekst))


def dlugosc_pakietow_m():
    """Suma `length_m` sześciu osi pakietów, w metrach, zaokrąglona do metra.

    Zdanie „`data/track/` pokrywa pakiety, nie linie" jest prawdziwe, dopóki ta
    suma stoi poniżej długości sieci (39,9 km z `lines.json`). Liczba jest z drzewa,
    nie z raportu: `reports/packages-BF-alignment.md` §8 podaje 34 481 m i to jest
    ta sama liczba, ale raport opisuje dzień, a plik opisuje dziś.
    """
    suma = 0.0
    for sciezka in _osie():
        with open(sciezka, encoding="utf-8") as handle:
            suma += json.load(handle)["length_m"]
    return round(suma)


def wymiary_stacji_z_zalozenia():
    """Ile wymiarów stacji stoi jako `design_assumption`, a nie jako dana ze STIB.

    Zdanie „układ stacji jest kanoniczny" jest prawdziwe dopóty, dopóki ta liczba
    obejmuje WSZYSTKIE wymiary generatora. Spadnie w dniu, w którym pierwszy wymiar
    dostanie źródło — i wtedy README ma o tym powiedzieć.

    Liczba jest w README wypisana wprost, więc gra w obie strony: zmiana w module
    bez zmiany w README zapala bramkę i odwrotnie. `TIGHTEST_STATION_FOOTPRINT_M`
    do tej tabeli NIE należy i stoi poza nią — to pomiar z UrbIS, nie założenie.
    """
    return len(SC.DESIGN_ASSUMPTIONS)


def wymiary_kabiny_z_zalozenia():
    """To samo dla kabiny M7 — 6.D119 postawiło bryły, ale ani jednego wymiaru z danych.

    `m7_cab` jest modułem BEZ `bpy` i to jest warunek tego pomiaru: bramka README
    nie może wymagać Blendera, bo chodzi też tam, gdzie Blendera nie ma.
    """
    return len(CAB.DESIGN_ASSUMPTIONS)


#: Punkty, których prawdziwość PILNUJE liczba z drzewa — 6.D104.
#:
#: **Semantyka ODWROTNA do `ZAPRZECZENIA` i to jest cała treść tego podziału.**
#: Tamta tabela mówi „zdanie twierdzi, że czegoś nie ma, a te nazwy dowodzą, że
#: jest" — więc trzyma zdania JUŻ FAŁSZYWE i jej kontrola przyrządu żąda, żeby
#: wskazane nazwy dziś w drzewie BYŁY. Zdania prawdziwego nie da się w niej
#: zapisać: wpis wskazywałby nazwę, której nie ma, a taki wpis nie zapali się
#: nigdy i tamten test odrzuca go wprost. Tutaj jest odwrotnie: zdanie jest dziś
#: prawdziwe, a wpis podaje liczbę, przy której pozostaje prawdziwe.
#:
#: Zmierzone 10.09.2026 na `a202423`.
POMIARY_BRAKOW = {
    "profilu pionowego": (osie_plaskie, 6,
                          "osi z `vertical.status = not_modelled` i Z = 0",
                          r"Wszystkie \*\*(\w+)\*\* osi"),
    "stacji wynikających z danych": (wymiary_stacji_z_zalozenia, 19,
                                     "wymiarów stacji jako `design_assumption`",
                                     r"\*\*(\d+)\*\* wymiarów jako `design_assumption`"),
    "wielu składów W SCENIE": (wezly_skladu_w_scenie, 1,
                               "węzłów `TrainView` w `FirstRun.tscn`",
                               r"Scena pokazuje \*\*(\w+)\*\*"),
    "wiernego wnętrza kabiny": (wymiary_kabiny_z_zalozenia, 19,
                                "wymiarów kabiny jako `design_assumption`",
                                r"\*\*(\d+)\*\* wymiarów"),
    "ciągłego kilometrażu linii": (dlugosc_pakietow_m, 34481,
                                   "metrów osi w sześciu pakietach",
                                   None),
}

#: Punkty, które wpisu w `POMIARY_BRAKOW` mieć NIE MOGĄ, z powodem podanym zdaniem.
#:
#: **Tabela jest dziś PUSTA i to jest stan zmierzony, nie przeoczenie — 6.D121.**
#: 6.D104 wpisało tu dwa punkty i oba z tego samego powodu: ich fałszyfikatorem
#: byłaby NAZWA, której w drzewie nie ma, a bramka na zgadniętej nazwie milczy tym
#: ciszej, im lepiej ktoś nazwie plik inaczej. Obie nazwy tymczasem powstały:
#: `tools/track/station_components.py` stoi w drzewie od #137 (T-212), a
#: `tools/blender/m7_cab.py` od 6.D119. Zdania README, które je wyprzedzały, były
#: więc **nieprawdą** — i to jest cała treść pozycji 6.D121.
#:
#: Mechanizm zostaje, bo powód pisany jest pełnoprawnym rozstrzygnięciem i następny
#: punkt sekcji może go potrzebować. Pustkę tej tabeli **przybija asercją**
#: `test_each_written_reason_says_why_the_table_cannot_hold_the_entry`: pętla po
#: pustym słowniku jest zielona, nie sprawdziwszy niczego, i dokładnie taki przyrząd
#: projekt tropi od 6.D27.
#:
#: **Czego pomiar punktu o kabinie NIE obejmuje.** `wymiary_kabiny_z_zalozenia`
#: pilnuje połowy zdania — tej o wymiarach. Druga połowa, „scena nie ma węzła
#: wnętrza", zostaje **niepilnowana** i to jest świadome: jej fałszyfikatorem jest
#: węzeł o nazwie, której nikt jeszcze nie wybrał, a licznik po WSZYSTKICH zasobach
#: `FirstRun.tscn` zapalałby się na każdym dodanym drzewie i słupku. Zapisane tutaj,
#: żeby nie trzeba było tego odkrywać z samego kodu.
POWODY_BEZ_WPISU = {}


def sekcja_brakow():
    """Treść sekcji „Czego nie ma" — od nagłówka do następnego nagłówka `##`."""
    tekst = _read(README)
    start = tekst.index(SEKCJA_BRAKOW)
    dalej = tekst.find("\n## ", start)
    return tekst[start:] if dalej < 0 else tekst[start:dalej]


def test_no_absence_claim_denies_a_capability_the_core_has():
    """Zdanie „rdzeń tego nie potrafi" nie może stać obok nazwy, która dowodzi, że potrafi.

    README jest pierwszym, co czyta nowy człowiek i agent. Zdanie o braku zdolności,
    która ISTNIEJE, kieruje pracę w złe miejsce — szkody wykonawczej nie ma, bo kod
    jest poprawny, myli się podsumowanie.
    """
    braki = sekcja_brakow()
    zle = []
    for zdanie, (plik, nazwy) in sorted(ZAPRZECZENIA.items()):
        if zdanie not in braki:
            continue
        zrodlo = _read(os.path.join(ROOT, plik))
        obecne = [n for n in nazwy if n in zrodlo]
        if obecne:
            zle.append((zdanie, plik, obecne))
    assert zle == [], "\n".join(
        "README mówi w „Czego nie ma\u201d: %r, a %s zawiera %s — zdanie zaprzecza "
        "istniejącej zdolności rdzenia" % (zdanie, plik, obecne)
        for zdanie, plik, obecne in zle)


def test_the_denial_table_points_at_names_that_are_really_in_the_core():
    """Kontrola przyrządu: wpis wskazujący nazwę, której nie ma, nie zapali się NIGDY.

    Bramka wyżej milczy z dwóch różnych powodów — bo zdania nie ma w README (dobrze)
    albo bo nazwy nie ma w rdzeniu (źle, bo wtedy wpis jest martwy). Ten test odcina
    ten drugi: każda nazwa z tabeli musi dziś w rdzeniu **być**.
    """
    for zdanie, (plik, nazwy) in sorted(ZAPRZECZENIA.items()):
        sciezka = os.path.join(ROOT, plik)
        assert os.path.isfile(sciezka), (zdanie, plik)
        zrodlo = _read(sciezka)
        for nazwa in nazwy:
            assert nazwa in zrodlo, (
                "wpis %r wskazuje nazwę %r, której w %s nie ma — wpis jest martwy "
                "i bramka nie zapali się nigdy" % (zdanie, nazwa, plik))

    # I że sekcja, po której chodzi bramka, w ogóle się wycina.
    braki = sekcja_brakow()
    assert braki.startswith(SEKCJA_BRAKOW), braki[:80]
    assert braki.count("\n- **") >= 4, (
        "sekcja „Czego nie ma\u201d ma %d punktów — cięcie się rozjechało"
        % braki.count("\n- **"))


def punkt_tekst(fragment):
    """Treść JEDNEGO punktu sekcji — od jego myślnika do myślnika następnego.

    Bez tego cięcia liczba „18" z jednego punktu zaliczałaby się drugiemu: wzorce
    z `POMIARY_BRAKOW` szukałyby jej w całej sekcji i każdy trafiałby na pierwszą
    z brzegu. Punkt jest jednostką zdania, więc jest też jednostką sprawdzania.
    """
    czesci = sekcja_brakow().split("\n- **")
    for czesc in czesci[1:]:
        if fragment in czesc:
            return "- **" + czesc
    return None


def liczba_z_readme(tekst, wzorzec):
    """Liczba złapana wzorcem — cyfrą albo liczebnikiem. None, gdy wzorzec nie trafia."""
    import re as _re
    trafienie = _re.search(wzorzec, tekst or "")
    if trafienie is None:
        return None
    zlapane = trafienie.group(1)
    if zlapane.isdigit():
        return int(zlapane)
    return NUMERALS.get(zlapane.lower())


def punkty_sekcji():
    """Fragmenty rozpoznawcze punktów sekcji „Czego nie ma", w kolejności z pliku."""
    braki = sekcja_brakow()
    return [p for p in PUNKTY_BRAKOW if p in braki]


def test_every_absence_bullet_has_a_measurement_or_a_written_reason():
    """Każdy z pięciu punktów sekcji ma rozstrzygnięcie, i suma wychodzi na pięć.

    Tego żąda pole „Skończone, gdy" pozycji 6.D104: albo wpis z wykonaną kontrolą
    negatywną, albo zapisany powód, dla którego wpisu mieć nie może. Test pilnuje
    ARYTMETYKI, bo bez niej szósty punkt dopisany do README nie zostałby przez nic
    zauważony — a właśnie tak powstała ta pozycja: tabela miała jeden wpis na pięć
    punktów i nikt tego nie liczył.
    """
    obecne = punkty_sekcji()
    assert len(obecne) == len(PUNKTY_BRAKOW), (
        "sekcja „Czego nie ma\u201d ma punkty, których lista `PUNKTY_BRAKOW` nie zna "
        "(albo odwrotnie): rozpoznano %s z %s"
        % (sorted(obecne), sorted(PUNKTY_BRAKOW)))

    # Ile punktów naprawdę stoi w sekcji — liczone z myślników, nie z listy wyżej,
    # bo lista jest tym, co ten test ma z sekcją zestawić.
    ile_w_sekcji = sekcja_brakow().count("\n- **")
    assert ile_w_sekcji == len(PUNKTY_BRAKOW), (
        "sekcja ma %d punktów, a lista zna %d — dopisany punkt nie ma "
        "rozstrzygnięcia" % (ile_w_sekcji, len(PUNKTY_BRAKOW)))

    rozstrzygniete = set(POMIARY_BRAKOW) | set(POWODY_BEZ_WPISU)
    assert rozstrzygniete == set(PUNKTY_BRAKOW), (
        "punkty bez rozstrzygnięcia: %s; rozstrzygnięcia bez punktu: %s"
        % (sorted(set(PUNKTY_BRAKOW) - rozstrzygniete),
           sorted(rozstrzygniete - set(PUNKTY_BRAKOW))))
    assert not (set(POMIARY_BRAKOW) & set(POWODY_BEZ_WPISU)), (
        "punkt ma naraz pomiar i powód, dla którego pomiaru mieć nie może: %s"
        % sorted(set(POMIARY_BRAKOW) & set(POWODY_BEZ_WPISU)))
    assert len(POMIARY_BRAKOW) + len(POWODY_BEZ_WPISU) == 5, (
        "%d pomiarów plus %d powodów nie daje pięciu"
        % (len(POMIARY_BRAKOW), len(POWODY_BEZ_WPISU)))


def test_the_true_absence_claims_still_match_the_numbers_in_the_tree():
    """Zdanie o braku jest prawdziwe dopóty, dopóki liczba z drzewa się nie ruszy.

    Odwrotna strona `ZAPRZECZENIA`: tamta tabela łapie zdanie, które JUŻ jest
    nieprawdziwe, ta — zdanie, które PRZESTAJE być prawdziwe. Bez drugiej strony
    README starzeje się w jedną stronę i nikt tego nie widzi, dopóki ktoś nie
    przeczyta go obok kodu.
    """
    zle = []
    for zdanie, (pomiar, oczekiwane, opis, _wzorzec) in sorted(POMIARY_BRAKOW.items()):
        assert zdanie in sekcja_brakow(), (
            "punkt %r zniknął z README, a pomiar dla niego został — zdejmij wpis "
            "albo przywróć punkt" % zdanie)
        wartosc = pomiar()
        if wartosc != oczekiwane:
            zle.append((zdanie, opis, wartosc, oczekiwane))
    assert zle == [], "\n".join(
        "README mówi w „Czego nie ma\u201d: %r, a drzewo ma %d %s zamiast %d — "
        "zdanie przestało być prawdziwe albo liczba wymaga przeliczenia"
        % (zdanie, wartosc, opis, oczekiwane)
        for zdanie, opis, wartosc, oczekiwane in zle)


def test_every_number_the_section_prints_is_the_number_the_tree_counts():
    """Liczba WYPISANA w punkcie musi się zgadzać z liczoną z drzewa — 6.D121.

    Bramka wyżej porównuje drzewo z wartością zapisaną TUTAJ, więc milczy, gdy ktoś
    zmieni samo README: „18 wymiarów" przerobione na „19" nie ruszy ani modułu, ani
    tego pliku. To jest ta sama dziura, przez którą README twierdził „41 plików"
    przy czterdziestu czterech — liczba stojąca w jednym miejscu i nigdzie nie
    liczona rozjeżdża się bezszelestnie.

    Wpis bez wzorca (`None`) znaczy „ta liczba w README nie stoi" i jest legalny:
    34 481 m jest w gałce bramki, a w prozie nie — wpisanie jej tam zrobiłoby
    z README drugą kopię tej samej wiedzy.
    """
    sprawdzone = 0
    zle = []
    for zdanie, (pomiar, _oczekiwane, opis, wzorzec) in sorted(POMIARY_BRAKOW.items()):
        tekst = punkt_tekst(zdanie)
        assert tekst is not None, (
            "punktu %r nie da się wyciąć z sekcji — cięcie po myślnikach się "
            "rozjechało" % zdanie)
        if wzorzec is None:
            continue
        z_readme = liczba_z_readme(tekst, wzorzec)
        if z_readme is None:
            zle.append((zdanie, "wzorzec %r nie trafia w tekst punktu" % wzorzec))
            continue
        sprawdzone += 1
        if z_readme != pomiar():
            zle.append((zdanie, "README pisze %d, drzewo liczy %d %s"
                        % (z_readme, pomiar(), opis)))
    assert zle == [], "\n".join("%s: %s" % para for para in zle)

    # Bramka nie przechodzi pusta: gdyby każdy wpis stracił wzorzec, pętla wyżej
    # nie porównałaby ani jednej pary i test byłby zielony z powodu, który nie ma
    # nic wspólnego ze zgodnością.
    z_wzorcem = [z for z, w in POMIARY_BRAKOW.items() if w[3] is not None]
    assert sprawdzone == len(z_wzorcem) and sprawdzone >= 4, (
        "porównano %d liczb przy %d wpisach ze wzorcem" % (sprawdzone, len(z_wzorcem)))


def test_each_written_reason_says_why_the_table_cannot_hold_the_entry():
    """Powód ma być zdaniem, nie pustym miejscem — i ma nazywać mechanizm.

    Wpis „nie da się" bez powodu jest tańszy od pomiaru i rośnie z tego samego
    powodu, co lista wyjątków bez zapadki (6.A31). Test żąda długości zdania
    i nazwania tego, co przeszkadza.
    """
    if not POWODY_BEZ_WPISU:
        # 6.D121: tabela jest pusta, więc pętla niżej nie sprawdziłaby NICZEGO
        # i zieleń tego testu znaczyłaby co innego, niż mówi jego nazwa. Zamiast
        # milczeć — asercja na to, DLACZEGO jest pusta: skoro powodu nie ma ani
        # jednego, pomiar musi mieć każdy z pięciu punktów.
        assert set(POMIARY_BRAKOW) == set(PUNKTY_BRAKOW), (
            "`POWODY_BEZ_WPISU` jest puste, a pomiaru nie mają: %s — punkt bez "
            "żadnego z dwóch rozstrzygnięć nie jest pilnowany przez nic"
            % sorted(set(PUNKTY_BRAKOW) - set(POMIARY_BRAKOW)))
        return

    sprawdzone = 0
    for zdanie, powod in sorted(POWODY_BEZ_WPISU.items()):
        assert zdanie in sekcja_brakow(), (
            "powód opisuje punkt %r, którego w README nie ma" % zdanie)
        assert len(powod) >= 200, (
            "powód dla %r ma %d znaków — to za mało, żeby nazwać mechanizm"
            % (zdanie, len(powod)))
        sprawdzone += 1
    assert sprawdzone == len(POWODY_BEZ_WPISU)


def test_the_absence_measurements_are_not_all_reading_the_same_thing():
    """Kontrola przyrządu: pięć pomiarów czyta pięć różnych miejsc drzewa.

    Pięć funkcji zwracających tę samą liczbę z tego samego pliku wyglądałoby
    w werdykcie identycznie jak pięć niezależnych. Ten test przybija, że każda
    naprawdę patrzy gdzie indziej — i że każda umie zwrócić coś innego niż
    dziś, bo pomiar, który zwraca stałą, nie jest pomiarem.
    """
    assert osie_plaskie() == len(_osie()), (
        "nie wszystkie osie są dziś płaskie (%d z %d) — README mówi, że wszystkie"
        % (osie_plaskie(), len(_osie())))
    assert len(_osie()) == 6, (
        "osi pakietów jest %d, a nie sześć — pomiar czyta nie ten katalog"
        % len(_osie()))

    # Scena: zasób skryptu MUSI być znaleziony, inaczej licznik zwraca zero
    # i wygląda jak „scena nie pokazuje ani jednego składu".
    tscn = _read(os.path.join(ROOT, "src", "Game", "Scenes", "FirstRun.tscn"))
    assert "World/TrainView.cs" in tscn, (
        "scena nie odwołuje się do `TrainView` — licznik węzłów mierzy nic")

    # Suma długości: pomiar ma być SUMĄ, a nie długością jednej osi.
    najdluzsza = 0.0
    for sciezka in _osie():
        with open(sciezka, encoding="utf-8") as handle:
            najdluzsza = max(najdluzsza, json.load(handle)["length_m"])
    assert dlugosc_pakietow_m() > round(najdluzsza), (
        "suma długości pakietów (%d m) nie jest większa od najdłuższego pakietu "
        "(%d m) — pomiar bierze jeden plik zamiast wszystkich"
        % (dlugosc_pakietow_m(), round(najdluzsza)))

    # I że suma NIE pokrywa sieci — to jest treść zdania o kilometrażu.
    dlugosc_sieci_m = round(
        json.load(open(os.path.join(ROOT, "data", "network", "lines.json"),
                       encoding="utf-8"))["network"]["metro_length_km"] * 1000)
    assert dlugosc_pakietow_m() < dlugosc_sieci_m, (
        "pakiety pokrywają %d m przy sieci %d m — zdanie „pokrywa pakiety, nie "
        "linie\u201d przestało być prawdziwe" % (dlugosc_pakietow_m(), dlugosc_sieci_m))

    # Dwa pomiary z 6.D121 liczą ZAŁOŻENIA, a nie wszystkie stałe modułu. Gdyby
    # liczyły wszystko, do stacji wliczyłby się `TIGHTEST_STATION_FOOTPRINT_M` —
    # a to jest POMIAR z UrbIS i stoi poza tabelą właśnie dlatego.
    assert "TIGHTEST_STATION_FOOTPRINT_M" not in SC.DESIGN_ASSUMPTIONS, (
        "obrys stacji z UrbIS wpadł do tabeli założeń — pomiar zaczął się liczyć "
        "jako zgadnięcie")
    assert wymiary_stacji_z_zalozenia() == len(SC.DESIGN_ASSUMPTIONS) > 0
    assert wymiary_kabiny_z_zalozenia() == len(CAB.DESIGN_ASSUMPTIONS) > 0

    # Liczby mogą się przypadkowo zrównać. Sonda zmienia tylko słownik stacji
    # i sprawdza, że odczyt kabiny nie drgnął; to rzeczywiście rozdziela źródła.
    original = SC.DESIGN_ASSUMPTIONS
    try:
        SC.DESIGN_ASSUMPTIONS = {**original, "probe_only_station": -1}
        assert wymiary_stacji_z_zalozenia() == len(original) + 1, (
            "pomiar stacji nie reaguje na własny słownik założeń")
        assert wymiary_kabiny_z_zalozenia() == len(CAB.DESIGN_ASSUMPTIONS), (
            "pomiar kabiny zmienił się po podmianie słownika stacji")
    finally:
        SC.DESIGN_ASSUMPTIONS = original
    assert SC.DESIGN_ASSUMPTIONS is not CAB.DESIGN_ASSUMPTIONS

    # Kabina musi się liczyć BEZ Blendera: ta bramka chodzi też tam, gdzie `bpy`
    # nie ma, a import `bpy` w `m7_cab` wywróciłby cały moduł README.
    #
    # Liczone ze ŹRÓDŁA, nie z `sys.modules` — i to jest pomiar, nie wybór stylu.
    # Pierwsza wersja asertowała `"bpy" not in sys.modules` i przechodziła w tym
    # module SAMYM, a padała w pełnym zestawie: `test_blender_cli.py`,
    # `test_detail_markers.py` i `test_marker_gates.py` wstawiają ATRAPĘ `bpy`
    # do `sys.modules`, więc asercja mówiła o stanie całego przebiegu, a nie
    # o tym, co wciągnął import kabiny. Przyrząd meldował sprawdzenie, którego
    # nie zrobił — ta sama rodzina co 6.D27.
    import ast
    drzewo = ast.parse(_read(os.path.join(ROOT, "tools", "blender", "m7_cab.py")))
    importy = set()
    for wezel in ast.walk(drzewo):
        if isinstance(wezel, ast.Import):
            importy.update(a.name.split(".")[0] for a in wezel.names)
        elif isinstance(wezel, ast.ImportFrom) and wezel.module:
            importy.add(wezel.module.split(".")[0])
    assert "bpy" not in importy, (
        "`tools/blender/m7_cab.py` importuje `bpy` — bramka README przestała "
        "chodzić bez Blendera; importy: %s" % sorted(importy))


def test_readme_core_file_count_matches_repository():
    files = core_files()
    claimed = readme_core_file_count(_read(README))
    assert claimed is not None, (
        "README nie podaje liczby plików `.cs` w `src/Sim/` w formie „N plików `.cs``; "
        "bez jednostki tej liczby nie da się sprawdzić poleceniem")
    # Bramka nie przechodzi pusta: pusty `src/Sim/` znaczy zepsute liczenie,
    # a nie zgodę na dowolną liczbę w README.
    assert len(files) > 0, f"nie znaleziono ani jednego pliku .cs w {SIM_DIR}"
    assert claimed == len(files), (
        f"README mówi {claimed} plików `.cs` w src/Sim/, repozytorium ma "
        f"{len(files)}: {files}")


def test_readme_workflow_count_and_names_match_repository():
    stems = workflow_stems()
    assert len(stems) > 0, f"nie znaleziono ani jednego *.yml w {WORKFLOW_DIR}"

    paragraph = ci_list_paragraph(_read(README))
    assert paragraph is not None, "README nie ma sekcji `## CI`"

    claimed_count = readme_workflow_count(paragraph)
    assert claimed_count is not None, (
        "pierwszy akapit sekcji `## CI` nie podaje liczby workflowów słownie "
        f"przed słowem „workflowów”; akapit: {paragraph!r}")
    assert claimed_count == len(stems), (
        f"README mówi {claimed_count} workflowów, .github/workflows/ ma "
        f"{len(stems)}: {stems}")

    claimed_names = readme_workflow_names(paragraph)
    assert claimed_names == stems, (
        f"README wymienia {claimed_names}, repozytorium ma {stems}; "
        f"brakuje w README: {sorted(set(stems) - set(claimed_names))}, "
        f"nadmiar w README: {sorted(set(claimed_names) - set(stems))}")


def test_readme_godot_version_matches_project_godot():
    features = project_godot_minor(_read(PROJECT_GODOT))
    assert features is not None, "brak `config/features` w src/Game/project.godot"

    mentions = readme_godot_versions(_read(README))
    # Bramka nie przechodzi pusta: gdyby README przestał podawać wersję silnika,
    # pętla poniżej nie wykonałaby ani jednego obrotu i test byłby zielony
    # z powodu, który nie ma nic wspólnego ze zgodnością.
    assert len(mentions) > 0, "README nie podaje wersji Godota w formie „Godot X.Y”"
    checked = 0
    for version in mentions:
        assert minor(version) == features, (
            f"README mówi „Godot {version}”, src/Game/project.godot ma "
            f"config/features {features}")
        checked += 1
    assert checked == len(mentions)


def test_parsers_reject_a_mismatch():
    """Kontrole negatywne parserów.

    Bez nich testy wyżej przechodziłyby także wtedy, gdyby każdy parser zwracał
    `None` albo pustą listę na wszystkim: `None == None` jest prawdziwe, a pętla
    po pustej liście nie sprawdza niczego. Każda asercja `is not None` i każdy
    licznik wyżej ma tu swoją drugą stronę.
    """
    # Parsery nie widzą tego, czego nie ma.
    assert readme_core_file_count("`src/Sim/`, 41 plików, i tyle") is None
    assert project_godot_minor('config/features=PackedStringArray("C#")') is None
    assert readme_godot_versions("bez Godota, ale z Godotem") == []
    assert ci_list_paragraph("## Struktura\n\ncoś\n") is None
    assert readme_workflow_count("Siedemnaścioro workflowów") is None
    assert readme_workflow_names("") == []

    # I że parsery czytają to, co README naprawdę pisze.
    assert readme_core_file_count("`src/Sim/`, 44 pliki `.cs`, kompiluje się") == 44
    assert readme_core_file_count("`src/Sim/`, 7 plików `.cs`") == 7
    assert project_godot_minor('config/features=PackedStringArray("4.7", "C#")') == "4.7"
    assert readme_godot_versions("Godot 4.3 mono i Godot 4.7.2") == ["4.3", "4.7.2"]
    assert readme_workflow_count("Siedem workflowów, jeden na bramkę") == 7
    assert readme_workflow_count("Dziesięć workflowów") == 10
    assert readme_workflow_names("`a-b`, `c-d`.") == ["a-b", "c-d"]

    # I że zgodność wersji naprawdę jest sprawdzana, a nie zawsze prawdziwa.
    assert minor("4.7.2") == "4.7"
    assert minor("4.3") != minor("4.7")

    # Akapit listy workflowów to pierwszy akapit sekcji, nie cała sekcja —
    # inaczej `self-hosted` z akapitu o runnerze byłby nazwą workflow.
    sample = "## CI\n\n`a-b`, `c-d`.\n\nna etykiecie `self-hosted`.\n\n## Dalej\n"
    assert readme_workflow_names(ci_list_paragraph(sample)) == ["a-b", "c-d"]

    # Liczenie plików rdzenia pomija wyjście budowy — od 6.D97 przez wspólne
    # odsianie z `.gitignore`, a nie przez własną listę. Asercja na ZAWARTOŚĆ tej
    # listy zniknęła razem z nią; zostaje asercja na WYNIK, bo to ona mówi o tym,
    # co ten moduł liczy.
    assert all("/obj/" not in p and "/bin/" not in p for p in core_files())

# 6.D25: uruchomienie tego pliku WPROST idzie ta sama droga, co caly zestaw —
# z licznikiem asercji i z odmowa przy zerze testow. Bez tej gałęzi `python3
# tools/tests/<modul>.py` konczyl sie kodem 0, nie wykonawszy ani jednego testu.
if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))
