#!/usr/bin/env python3
"""Kazdy pisarz CSV w `Sim.Runner` zapisuje nastawy albo ma wypisany powod, dlaczego nie.

**Skad ta bramka.** 6.A20. 6.A18 naprawila to po stronie WYPISU: naglowek `[BUDZET]`
mowi od niej, jaki przejazd zmierzono. Ale wypis ginie razem z konsola, a plik
z `--out` PRZEZYWA proces i to on trafia do raportow. Zmierzone 07.09.2026: przed 6.A20
dwa przebiegi `budget` roznione jedna nastawa dawaly pliki DWUWIERSZOWE, w ktorych
roznil sie wylacznie wiersz pomiaru — a mediana krokow wyszla w nich odwrotnie
(88 935 vs 77 237 krokow/s), wiec czytajacy wyciagnalby wniosek przeciwny do
prawdziwego i nie mial czym tego sprawdzic.

**Czego ta bramka pilnuje NAPRAWDE.** Nie tego, ze kazdy pisarz zapisuje nastawy —
trzy z siedmiu nie moga i to jest zmierzone, nie zalozone. Pilnuje, ze **zaden nie
milczy bez powodu**: pisarz bez `Provenance` i bez wpisu nizej zapala bramke. Bez tego
osmy pisarz, dopisany kiedys indziej, po prostu nie mialby nastaw i nikt by nie
zauwazyl — dokladnie tak, jak nie mialo ich siedem.

**Dlaczego trzy nie moga.** Ich format jest PRZYBITY z zewnatrz i dopisanie czegokolwiek
zlamalo by porownanie, ktore na nim stoi:

- telemetria `drive` i `replay` — `Compare` wymaga, zeby pierwszy wiersz byl DOKLADNIE
  `DriveTelemetry.Header`, a kazdy wiersz mial dokladnie `ColumnCount` kolumn; ten sam
  format pisze scena Godota i `godot-first-run.yml` porownuje oba pliki przy
  `--tolerance 0`. Wiersz `#` przed naglowkiem lamie warunek na `left[0]`;
- `line --calls` — `godot-first-run.yml` porownuje plik rdzenia z plikiem SCENY, wiec
  format jest wspolny z implementacja w Godocie, nie tylko z tym repozytorium;
- `line --trace` — `tools/ci/assert_line_trace.py` liczy SHA-256 CALEGO pliku i
  porownuje z wzorcami przybitymi do RODZINY runtime'u .NET. Zmiana formatu uniewaznia
  wzorce, a ta bramka mowi wprost, ze przeliczanie wzorcow nalezy do commita, ktory
  zmienia wersje srodowiska, i ma byc w jego tresci opisane. Dopisanie metadanych
  przeliczyloby je jako skutek uboczny.

Zniesienie ktoregokolwiek z tych trzech powodow jest osobna praca, nie poprawka przy
okazji — dlatego stoja tu z nazwami, a nie w milczeniu.
"""
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PROGRAM = os.path.join(ROOT, "src", "Sim.Runner", "Program.cs")

#: Metoda polecenia -> powod, dla ktorego jej pisarz NIE ma nastaw.
#: Kluczem jest METODA, nie nazwa zmiennej, i to jest poprawka na wlasny blad: pierwsza
#: wersja tej bramki kluczowala po zmiennej (`lines`, `rows`) i sama sie zapalila, bo te
#: nazwy sa UZYWANE PONOWNIE — `lines` sklada i telemetrie `drive`, i plik `service-day`,
#: a `rows` i punkty osi, i `line --calls`, i pomiar `budget`. Klucz, ktory nie
#: rozroznia dwoch roznych formatow, nie ma prawa orzekac o zadnym z nich.
#: Pisarze, ktorych format jest PRZYBITY Z ZEWNATRZ, a nastawy ida do pliku OBOK.
#: Powod kazdego stoi w `Program.cs` przy `WriteProvenanceBeside` i w bloku 6.A21.
#: Zmierzone 09.09.2026: plik obok nie zmienia w plikach przybitych ani jednego bajtu —
#: `tools/ci/assert_line_trace.py` na szesciu osiach mowi „zgadza sie z wzorcem co do
#: bajtu", wiec zadna z czterech regul (Compare, scena Godota, --tolerance 0, SHA
#: wzorcow) nie zostala naruszona ani osłabiona.
NASTAWY_OBOK = {"Drive", "Replay", "LineCommand"}

#: Pisarze BEZ nastaw, z powodem. Do 6.A21 bylo tu czterech; zostal JEDEN, i to jest
#: cala tresc tamtej pozycji — trzy pozostale dostaly plik obok, a nie nowa wymowke.
BEZ_NASTAW = {
    "Axis": (
        "`axis --dump-points` zapisuje SUROWE punkty osi, bez naglowka i bez pomiaru: "
        "nie ma nastaw, ktore mialby opisac, bo nie jest wynikiem przejazdu. "
        "Sprawdzone: plik nie jest czytany przez `Compare` ani przez "
        "`godot-first-run.yml`, wiec powodem jest tresc, nie przybity format"),
}

def _zrodlo():
    with open(PROGRAM, encoding="utf-8") as uchwyt:
        return uchwyt.read()


METODY = ("Drive", "Replay", "Compare", "Axis", "Parity", "Braking",
          "LineCommand", "Budget", "ServiceDayCommand")


def _zakresy(source):
    """Metoda -> jej tresc, wycieta po polozeniu naglowkow w pliku."""
    pozycje = []
    for metoda in METODY:
        match = re.search(r"\n    private static int " + metoda + r"\(", source)
        if match:
            pozycje.append((match.start(), metoda))
    pozycje.sort()
    zakresy = {}
    for i, (start, metoda) in enumerate(pozycje):
        koniec = pozycje[i + 1][0] if i + 1 < len(pozycje) else len(source)
        zakresy[metoda] = source[start:koniec]
    return zakresy


def pisarze(source=None):
    """Metoda -> ile plikow zapisuje. Klucz strukturalny, nie nazwa zmiennej."""
    source = _zrodlo() if source is None else source
    return {metoda: tresc.count("File.WriteAllLines(")
            for metoda, tresc in _zakresy(source).items()
            if "File.WriteAllLines(" in tresc}


def z_nastawami(source=None):
    """Metody, ktorych pisarz sklada nastawy — WPROST w pliku albo w pliku OBOK.

    **Detektor PRZEKIEROWANY, nie poluzowany — 6.A21, 09.09.2026.** Poprzednia wersja
    znala jeden kształt: `new List<string>(Provenance(`, czyli nastawy wklejone na
    poczatek pliku. Ten kształt jest dla trzech pisarzy zamkniety (format przybity
    z zewnatrz), wiec doszedl drugi: `WriteProvenanceBeside(`. Zeby przekierowanie
    sprawdzalo WIECEJ, a nie mniej, do bramek doszly trzy warunki na sam ten pomocnik
    (`test_the_sidecar_writer_cannot_be_a_no_op`) i jeden na kazde wolanie
    (`test_every_sidecar_names_the_same_path_as_the_file_it_describes`) — bez nich
    dopisanie `WriteProvenanceBeside` do metody wystarczyloby, zeby bramka zamilkla,
    nawet gdyby ten pomocnik nie zapisywal nic.
    """
    source = _zrodlo() if source is None else source
    return {metoda for metoda, tresc in _zakresy(source).items()
            if "new List<string>(Provenance(" in tresc
            or "WriteProvenanceBeside(" in tresc}


def wprost(source=None):
    """Metody wklejajace nastawy DO pliku (kształt `budget` i `service-day`)."""
    source = _zrodlo() if source is None else source
    return {metoda for metoda, tresc in _zakresy(source).items()
            if "new List<string>(Provenance(" in tresc}


def obok(source=None):
    """Metody zapisujace nastawy w pliku OBOK (kształt trzech przybitych pisarzy)."""
    source = _zrodlo() if source is None else source
    return {metoda for metoda, tresc in _zakresy(source).items()
            if "WriteProvenanceBeside(" in tresc}


def test_the_helper_exists_and_prefixes_every_setting_with_a_hash():
    """Blok nastaw musi byc KOMENTARZEM, nie wierszami danych — inaczej plik przestaje
    byc CSV-em, ktory cokolwiek otworzy."""
    source = _zrodlo()
    at = source.index("private static IEnumerable<string> Provenance(")
    body = source[at:source.index("\n    /// <summary>Punkt wejścia", at)]
    assert 'yield return "# polecenie: " + command;' in body, body[:400]
    assert 'yield return "# " + name + ": " + value;' in body, body[:400]


def test_every_csv_writer_either_carries_settings_or_says_why_not():
    source = _zrodlo()
    opisane = z_nastawami(source)
    milczace = sorted(set(pisarze(source)) - opisane - set(BEZ_NASTAW))
    assert not milczace, (
        "polecenie zapisuje plik bez nastaw i bez wpisu w BEZ_NASTAW: " + ", ".join(milczace)
        + " — albo wola `Provenance(...)`, albo ma tu jednozdaniowy powod, dla ktorego "
          "jego format jest przybity z zewnatrz. Plik bez nastaw przezywa proces "
          "i trafia do raportu jako pomiar bez scenariusza (6.A20)")


def test_no_excuse_outlives_the_writer_it_describes():
    """Drugi kierunek. Wpis o pisarzu, ktorego juz nie ma — albo ktory nastawy JUZ
    zapisuje — opisuje stan miniony i przy nastepnym czytaniu wyglada na przemyslany."""
    source = _zrodlo()
    istniejacy = set(pisarze(source))
    opisane = z_nastawami(source)
    martwe = sorted(n for n in BEZ_NASTAW if n not in istniejacy or n in opisane)
    assert not martwe, (
        "BEZ_NASTAW opisuje polecenia, ktore nie zapisuja pliku albo juz maja nastawy: "
        + ", ".join(martwe) + " — skresl wpis razem z powodem, dla ktorego stal")


def test_every_writer_lands_in_exactly_one_of_the_three_boxes():
    """Kontrola pozytywna PRZEKIEROWANA — 6.A21, i sprawdza WIECEJ, nie mniej.

    Poprzednia wersja przybijala JEDEN zbior (`opisane == {Budget, ServiceDayCommand}`)
    i byla zielona nad kazdym ukladem pozostalych pieciu pisarzy — w tym nad takim,
    w ktorym wszyscy trafiaja do BEZ_NASTAW, czyli nad zamiana zadania na liste
    wymowek. Dzis przybite sa TRZY zbiory naraz i kazdy pisarz musi lezec w dokladnie
    jednym: nastawy w pliku, nastawy obok, albo powod. Piaty warunek — rozlacznosc —
    jest tu dlatego, ze bez niego pisarz z nastawami I z wymowka przechodzilby oba
    testy osobno.
    """
    source = _zrodlo()
    w_pliku, w_obok = wprost(source), obok(source)
    assert w_pliku == {"Budget", "ServiceDayCommand"}, (
        "nastawy WPROST w pliku maja dokladnie te dwa polecenia — jedyne, ktorych "
        "formatu nie przybija nic z zewnatrz: " + repr(sorted(w_pliku)))
    assert w_obok == NASTAWY_OBOK, (
        "nastawy w pliku OBOK maja dokladnie trzy polecenia z przybitym formatem: "
        + repr(sorted(w_obok)))
    assert not (w_pliku & w_obok), (
        "pisarz sklada nastawy dwiema drogami naraz: " + repr(sorted(w_pliku & w_obok)))
    assert not ((w_pliku | w_obok) & set(BEZ_NASTAW)), (
        "pisarz ma nastawy I wymowke: " + repr(sorted((w_pliku | w_obok) & set(BEZ_NASTAW))))
    assert set(pisarze(source)) == w_pliku | w_obok | set(BEZ_NASTAW), (
        "pisarz poza wszystkimi trzema pudelkami: "
        + repr(sorted(set(pisarze(source)) ^ (w_pliku | w_obok | set(BEZ_NASTAW)))))
    for polecenie in ('Provenance(\n            "budget"', 'Provenance(\n                "service-day"'):
        assert polecenie in source, "brak wolania Provenance dla " + polecenie


def test_the_sidecar_writer_cannot_be_a_no_op():
    """Trzy warunki na sam pomocnik, bez ktorych przekierowanie detektora BYLOBY
    poluzowaniem: `WriteProvenanceBeside` w metodzie starczyloby wtedy za nastawy,
    nawet gdyby pomocnik nie zapisywal nic.

    Kontrola negatywna WYKONANA 09.09.2026 na kazdym z trzech warunkow osobno
    (`reports/6a21-nastawy-obok-pliku.md` §5).
    """
    source = _zrodlo()
    at = source.index("private static void WriteProvenanceBeside(")
    body = source[at:source.index("\n    /// <summary>", at)]
    assert "File.WriteAllLines(" in body, ("pomocnik nic nie zapisuje", body)
    assert "Provenance(command, settings)" in body, (
        "pomocnik nie sklada tresci przez `Provenance`, wiec kształt `#` nie jest "
        "wspolny z nastawami wklejanymi do pliku", body)
    assert "ProvenancePathFor(path)" in body, (
        "pomocnik nie liczy nazwy przez `ProvenancePathFor`, wiec nazwa pliku obok "
        "powstaje w dwoch miejscach", body)
    nazwa = source[source.index("static string ProvenancePathFor("):]
    nazwa = nazwa[:nazwa.index("\n")]
    assert "path +" in nazwa, ("nazwa pliku obok nie wychodzi ze sciezki pliku "
                               "wyniku, wiec moze wskazac cokolwiek", nazwa)
    assert ".csv" not in nazwa, (
        "plik obok nazywa sie jak plik wyniku — bramki CI zbieraja slady po `*.csv` "
        "i wciagnelyby nastawy jako slad", nazwa)


def test_every_sidecar_names_the_same_path_as_the_file_it_describes():
    """Nastawy obok PLIKU, ktory opisuja — nie obok jakiegokolwiek.

    Bez tego warunku `WriteProvenanceBeside(tracePath, ...)` przy zapisie do
    `callsPath` przechodzilby bramke wyzej i produkowal plik nastaw opisujacy inny
    przebieg niz ten, ktory lezy obok. Klucz jest strukturalny: pierwszy argument
    obu wolan w tej samej metodzie, nie numer wiersza.
    """
    for metoda, tresc in _zakresy(_zrodlo()).items():
        if metoda not in NASTAWY_OBOK:
            continue
        pliki = re.findall(r"File\.WriteAllLines\(\s*(\w+)", tresc)
        nastawy = re.findall(r"WriteProvenanceBeside\(\s*(\w+)", tresc)
        assert pliki, (metoda, "metoda w NASTAWY_OBOK nie zapisuje zadnego pliku")
        assert sorted(pliki) == sorted(nastawy), (
            metoda + ": plik wyniku i plik nastaw wskazuja rozne sciezki — "
            f"zapisane {sorted(pliki)}, opisane {sorted(nastawy)}")


def test_the_reasons_name_what_pins_the_format():
    """Powod ma mowic, CO przybija format, a nie ze jest przybity. „Bo tak" i „na
    razie" starzeja sie bez sladu; nazwa bramki albo pliku da sie sprawdzic."""
    for nazwa, powod in BEZ_NASTAW.items():
        assert len(powod) > 60, (nazwa, powod)
        assert any(slad in powod for slad in
                   ("Compare", "godot-first-run.yml", "assert_line_trace.py")), (nazwa, powod)


# 6.D25: uruchomienie tego pliku WPROST idzie ta sama droga, co caly zestaw.
if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))
