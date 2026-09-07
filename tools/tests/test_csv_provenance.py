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
BEZ_NASTAW = {
    "Drive": (
        "telemetria: `Compare` wymaga, zeby pierwszy wiersz byl dokladnie "
        "`DriveTelemetry.Header`, a ten sam format pisze scena Godota i "
        "`godot-first-run.yml` porownuje oba przy --tolerance 0"),
    "Replay": (
        "ta sama telemetria, co `drive`, i to samo porownanie w "
        "`godot-first-run.yml` przy --tolerance 0 — format jest wspolny z Godotem"),
    "Axis": (
        "`axis --dump-points` zapisuje SUROWE punkty osi, bez naglowka i bez pomiaru: "
        "nie ma nastaw, ktore mialby opisac, bo nie jest wynikiem przejazdu. "
        "Sprawdzone: plik nie jest czytany przez `Compare` ani przez "
        "`godot-first-run.yml`, wiec powodem jest tresc, nie przybity format"),
    "LineCommand": (
        "dwa pisarze: `line --trace`, ktorego SHA-256 CALEGO pliku pilnuje "
        "`tools/ci/assert_line_trace.py` wobec wzorcow przybitych do rodziny "
        "runtime'u — a tamta bramka wymaga, zeby przeliczanie wzorcow stalo w commicie "
        "zmieniajacym wersje srodowiska; oraz `line --calls`, ktorego plik "
        "`godot-first-run.yml` porownuje z plikiem SCENY"),
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
    """Metody, ktorych pisarz sklada wiersze przez `Provenance(...)`."""
    source = _zrodlo() if source is None else source
    return {metoda for metoda, tresc in _zakresy(source).items()
            if "new List<string>(Provenance(" in tresc}


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


def test_budget_and_service_day_are_the_two_that_do_carry_them():
    """Kontrola pozytywna, przybijajaca ZAKRES tej pozycji. Bez niej bramka byla by
    zielona takze wtedy, gdyby wszystkie siedem pisarzy trafilo do BEZ_NASTAW —
    czyli gdyby zadanie zostalo zamienione na liste wymowek."""
    opisane = z_nastawami()
    assert opisane == {"Budget", "ServiceDayCommand"}, (
        "zakres 6.A20 to dokladnie te dwa polecenia — jedyne, ktorych formatu nie "
        "przybija nic z zewnatrz: " + repr(sorted(opisane)))
    source = _zrodlo()
    for polecenie in ('Provenance(\n            "budget"', 'Provenance(\n                "service-day"'):
        assert polecenie in source, "brak wolania Provenance dla " + polecenie


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
