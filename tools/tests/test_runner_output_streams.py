#!/usr/bin/env python3
"""Znacznik `[XXX]` runnera idzie na JEDEN strumien — i jest nim stdout.

**Skad ta bramka.** 6.A30. Pomiar 07.09.2026 na `src/Sim.Runner/Program.cs`: wypisow
z markerem `[XXX]` bylo **38**, z czego **33 na stdout i 5 na stderr** (`[RDZEŃ]`
w `Drive`, `[LIMIT]`, dwa `[ODTWORZENIE]` i `[ATP]` w `Replay`). Znacznik `[ATP]`
stal wtedy na OBU STRUMIENIACH jednego programu: `line` wypisywal go na stdout,
`replay --atp` na stderr. `[ODTWORZENIE]` mial ten sam rozjazd przez granice
programu — scena Godota wypisuje `[ODTWORZENIE] koniec: …` przez `GD.Print`, czyli
na stdout, a rdzen swoje dwa wiersze na stderr.

**Dlaczego to bramka, a nie tylko test C#.** Test C# oglada strumienie JEDNEGO
wywolania i lapie wylacznie te wiersze, ktore to wywolanie wyprodukuje: wiersz
`[ODTWORZENIE] stacja …` wymaga przejazdu z obsluzona stacja, `[ATP]` wymaga `--atp`.
Nowy wypis dopisany na stderr w szostym poleceniu nie zlamie zadnego istniejacego
testu, dopoki nikt nie napisze mu wlasnego — a wtedy `2>/dev/null` znowu zabiera
czesc WYNIKU, nie diagnostyki. Ta bramka czyta `Program.cs` jako TEKST i orzeka
o wszystkich wypisach naraz.

**Drugi kierunek jest tu polowa roboty.** Bramka, ktora zada samego „zero markerow
na stderr", byla by zielona takze na pliku, ktory przeniosl na stdout ROWNIEZ odmowy
— a `BŁĄD: `, `nieznane polecenie:` i wiersz pomocy na stderr NALEZA i to
rozstrzygnely 6.A16 oraz 6.A27. Byla by zielona rowniez wtedy, gdyby ktos te piec
wierszy po prostu USUNAL. Dlatego sa trzy asercje, nie jedna: brak markera na
stderr, obecnosc kazdego z pieciu wierszy na stdout Z NAZWY, i odmowy nadal na
stderr.
"""
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PROGRAM = os.path.join(ROOT, "src", "Sim.Runner", "Program.cs")

#: Wzorzec znacznika informacyjnego: `[RDZEŃ]`, `[BUDŻET]`, `[PORÓWNANIE]` …
#: Wielkie litery lacinskie i polskie, co najmniej dwie — zeby `[0]` ani `[i]`
#: z indeksowania nie liczyly sie jako znacznik.
MARKER = re.compile(r"\[[A-ZĄĆĘŁŃÓŚŹŻ]{2,}\]")

#: Piec wierszy przeniesionych przez 6.A30, kazdy z nazwy. Fragment napisu, nie caly
#: wiersz z interpolacja — `{scenario.Id}` jest w kodzie, a w wyjsciu nie.
#: Sam licznik „zero markerow na stderr" przechodzilby takze wtedy, gdyby ktos
#: odmowe albo podsumowanie USUNAL, a wiersz usuniety jest gorszy od wiersza
#: na zlym strumieniu.
PRZENIESIONE = (
    "[RDZEŃ] {scenario.Id}:",
    "[LIMIT] tryb ręczny:",
    "[ODTWORZENIE] {keysPath}:",
    "[ATP] ostrzeżeń=",
    "[ODTWORZENIE] stacja {call.Name}:",
)

#: Odmowy, ktore na stderr NALEZA (6.A16, 6.A27) — pole „Poza zakresem" 6.A30.
#: Fragmenty tego, co naprawde stoi w wywolaniu wypisu.
ODMOWY_NA_STDERR = (
    '"BŁĄD: "',
    "nieznane polecenie:",
    "MetroBxl.Sim.Runner — konsolowy gospodarz rdzenia symulacji",
)

#: Ile wypisow z markerem ma stac na stdout co najmniej. Kontrola PRZYRZADU: czytnik,
#: ktory po zmianie skladni przestalby cokolwiek znajdowac, meldowalby „zero markerow
#: na stderr" i byl zielony na pustym zbiorze. Zmierzone 07.09.2026: **38**.
#:
#: Prog jest LUZNY (30, nie 38) i to jest poprawka na wlasny blad, zmierzona na
#: wlasnej kontroli negatywnej. Pierwsza wersja stala na 38 — czyli na dokladnej
#: liczbie z dnia pomiaru — i przy cofnieciu jednego wiersza na stderr zapalala sie
#: NA PROGU (`37 markerow, a ma byc 38`), zanim doszla do asercji o strumieniu.
#: Bramka meldowala wiec „przyrzad nie widzi", kiedy prawda bylo „wiersz idzie na
#: zly strumien" — komunikat mowil o czym innym niz usterka. Prog ma odrozniac
#: czytnik OSLEPIONY od czytnika dzialajacego, a nie liczyc wypisy; liczbe wypisow
#: pilnuje asercja `PRZENIESIONE`, po nazwie i po tresci.
MARKEROW_NA_STDOUT_CO_NAJMNIEJ = 30


def _bez_komentarzy(source):
    """`Program.cs` z wygaszonymi wierszami komentarza — numeracja zachowana.

    Wzmianka w komentarzu nie jest wypisem, a akapity wyjasniajace, DLACZEGO wiersz
    idzie na stdout, same te znaczniki zawieraja — ta sama potrzeba, co w
    `test_runner_exit_codes.py` od 6.A27. Wiersze sa PODMIENIANE na puste, a nie
    wyrzucane, zeby numer w komunikacie bledu zgadzal sie z plikiem.
    """
    return [
        "" if line.strip().startswith(("//", "///")) else line
        for line in source.splitlines()
    ]


def _wypisy(lines):
    """Wywolania `Console.*WriteLine` -> lista `(numer wiersza, strumien, tresc)`.

    Tresc to caly argument wywolania, sklejony przez wiersze do domkniecia nawiasow —
    bo wiekszosc wypisow runnera to `string.Create(Inv, $"…" + $"…")` rozlozone na
    piec wierszy i marker stoi w drugim z nich.
    """
    wypisy = []
    i = 0
    while i < len(lines):
        match = re.search(r"Console\.(Out\.WriteLine|Error\.WriteLine|WriteLine)", lines[i])
        if match is None:
            i += 1
            continue
        strumien = "stderr" if "Error" in match.group(1) else "stdout"
        depth = 0
        started = False
        j = i
        kawalki = []
        while j < len(lines):
            kawalki.append(lines[j])
            for ch in lines[j]:
                if ch == "(":
                    depth += 1
                    started = True
                elif ch == ")":
                    depth -= 1
            if started and depth <= 0:
                break
            j += 1
        wypisy.append((i + 1, strumien, "\n".join(kawalki)))
        i = j + 1
    return wypisy


def test_no_information_line_of_the_runner_goes_to_stderr():
    """Zero wypisow z markerem `[XXX]` na stderr — i przyrzad, ktory to mierzy, widzi.

    Asercja na LICZBE i na NAZWE: komunikat wymienia numer wiersza i znacznik, bo
    „jakis wypis idzie na zly strumien" nie mowi, ktory.
    """
    lines = _bez_komentarzy(open(PROGRAM, encoding="utf-8").read())
    wypisy = _wypisy(lines)
    na_stdout = [(n, MARKER.findall(t)) for n, s, t in wypisy if s == "stdout"]
    markerow_na_stdout = sum(len(m) for _, m in na_stdout)
    assert markerow_na_stdout >= MARKEROW_NA_STDOUT_CO_NAJMNIEJ, (
        "czytnik wypisow znalazl %d markerow na stdout, a ma ich byc co najmniej %d — "
        "przyrzad jest oslepiony i bramka orzekalaby o pustym zbiorze"
        % (markerow_na_stdout, MARKEROW_NA_STDOUT_CO_NAJMNIEJ))

    zle = [(n, MARKER.findall(t)) for n, s, t in wypisy if s == "stderr" and MARKER.search(t)]
    assert zle == [], (
        "wypisy z markerem `[XXX]` na stderr: "
        + ", ".join("wiersz %d %s" % (n, "/".join(m)) for n, m in zle)
        + ". Znacznik, ktory raz idzie na stdout, a raz na stderr, psuje rozpoznanie "
          "jednym wzorcem `grep`, a `2>/dev/null` usuwa wtedy czesc WYNIKU, nie "
          "diagnostyki (6.A30). Na stderr naleza wylacznie odmowy.")


def test_every_line_moved_by_6a30_is_on_stdout():
    """Piec przeniesionych wierszy nadal ISTNIEJE i stoi na stdout — kazdy z nazwy.

    Pomiar pola „Wyjscie" pozycji 6.A30 dal **0 duplikatow i 5 unikalnych**: ani jeden
    z tych wierszy nie mial bajt w bajt odpowiednika na stdout, wiec zadnego nie wolno
    bylo skasowac. Bez tej asercji bramka wyzej byla by zielona takze po skasowaniu.
    """
    lines = _bez_komentarzy(open(PROGRAM, encoding="utf-8").read())
    na_stdout = "\n".join(t for _, s, t in _wypisy(lines) if s == "stdout")
    for tresc in PRZENIESIONE:
        assert tresc in na_stdout, (
            "wiersz przeniesiony przez 6.A30 zniknal ze stdout: " + tresc)


def test_refusals_still_go_to_stderr():
    """Drugi kierunek: odmowy zostaja na stderr.

    Bez tej asercji „zero markerow na stderr" bylo by spelnione takze przez plik,
    ktory na stdout przeniosl RAZEM Z NIMI `BŁĄD: `, `nieznane polecenie:` i wiersz
    pomocy — a te na stderr naleza i to rozstrzygnely 6.A16 oraz 6.A27. To jest pole
    „Poza zakresem" pozycji 6.A30, wiec bramka ma je pilnowac, a nie tylko o nich
    milczec.
    """
    lines = _bez_komentarzy(open(PROGRAM, encoding="utf-8").read())
    na_stderr = "\n".join(t for _, s, t in _wypisy(lines) if s == "stderr")
    assert na_stderr, "w `Program.cs` nie ma ani jednego wypisu na stderr — odmowy tez"
    for tresc in ODMOWY_NA_STDERR:
        assert tresc in na_stderr, (
            "odmowa zeszla ze stderr: " + tresc)


# 6.D25: uruchomienie tego pliku WPROST idzie ta sama droga, co caly zestaw —
# z licznikiem asercji i z odmowa przy zerze testow.
if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))
