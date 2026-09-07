#!/usr/bin/env python3
"""Tabela znanych opcji `Sim.Runner` zgadza sie z tym, co polecenia naprawde czytaja.

**Skad ta bramka.** 6.D15 (#301) uruchomilo komende z pola „Weryfikacja" pozycji 6.A6:
`line ... --coast-from-m X`. Opcji `--coast-from-m` nie ma nigdzie w `src/`, `X` nie
jest liczba — a proces konczyl sie **kodem 0**. Dwa przejazdy, z ta opcja i bez niej,
daly pliki identyczne co do bajtu. 6.A11 dopisala odmowe; ta bramka pilnuje, zeby
odmowa nie rozjechala sie z kodem.

**Dlaczego bramka po stronie Pythona.** Tabela `KnownOptions` w `Program.cs` jest recznie
wypisana i to jest jej zaleta: komunikat odmowy ma wymieniac opcje TEGO polecenia,
a nie wszystkie, jakie runner zna. Recznie wypisana tabela ma jednak dokladnie jedna
wade — starzeje sie po cichu. Opcja dopisana do polecenia bez dopisania jej tutaj
przechodzilaby wszystkie testy C#: kod czyta ja przez `Option`, a odmowa nigdy nie
dochodzi do glosu, bo nikt tej opcji nie poda w tescie.

Ten modul czyta wiec `Program.cs` jako TEKST i wyprowadza zbior nazw z wywolan
`Option`, `RequiredNumber`, `OptionalNumber` i `Array.IndexOf` w ciele kazdego
polecenia — po czym porownuje go z tabela. Dwa niezalezne odczyty tego samego pliku;
rozjazd jednego z nich zapala bramke.

**Czego ta bramka NIE robi.** Nie uruchamia `dotnet` i nie moze go potrzebowac: zestaw
narzedzi chodzi tam, gdzie `doctor.sh` przepuszcza brak SDK. Nie sprawdza, czy opcja
robi to, co obiecuje jej nazwa — to jest praca testow C#.
"""
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PROGRAM = os.path.join(ROOT, "src", "Sim.Runner", "Program.cs")

#: Nazwa metody C# obslugujacej polecenie -> nazwa polecenia w wierszu polecen.
#: Bierze sie z rozdzielacza `args[0] switch` i jest tu wypisana, bo rozdzielacz
#: mapuje jedno na drugie i tego odwzorowania nie da sie wyprowadzic z samej nazwy
#: metody (`line` -> `LineCommand`, `service-day` -> `ServiceDayCommand`).
HANDLERS = {
    "Drive": "drive",
    "Replay": "replay",
    "Compare": "compare",
    "Axis": "axis",
    "Parity": "parity",
    "Braking": "braking",
    "LineCommand": "line",
    "Budget": "budget",
    "ServiceDayCommand": "service-day",
}


def _source():
    with open(PROGRAM, encoding="utf-8") as handle:
        return handle.read()


def dispatcher_commands(source):
    """Nazwy polecen wprost z rozdzielacza `args[0] switch` w `Main`."""
    at = source.index("return args[0] switch")
    end = source.index("_ =>", at)
    return set(re.findall(r'"([a-z-]+)"\s*=>', source[at:end]))


def declared_table(source):
    """`KnownOptions` z `Program.cs` -> {polecenie: (wartosciowe, flagi)}."""
    at = source.index("KnownOptions =")
    # +1, zeby ostatni wpis mial swoj konczacy znak nowej linii: bez tego wyrazenie
    # nizej nie dopasowuje wpisu stojacego tuz przed klamra zamykajaca slownik.
    end = source.index("\n        };", at)
    body = source[at:end + 1]
    table = {}
    for match in re.finditer(r'\["([a-z-]+)"\]\s*=\s*\((.*?)\),\n', body, re.S):
        command, pair = match.group(1), match.group(2)
        halves = re.findall(r'new\[\]\s*\{(.*?)\}|Array\.Empty<string>\(\)', pair, re.S)
        parsed = []
        for half in halves:
            parsed.append(set(re.findall(r'"(--[a-z0-9-]+)"', half)))
        while len(parsed) < 2:
            parsed.append(set())
        table[command] = (parsed[0], parsed[1])
    return table


def read_by_code(source):
    """Nazwy opcji, ktore CIALO kazdego polecenia naprawde czyta."""
    positions = []
    for method in HANDLERS:
        match = re.search(r"\n    private static int " + method + r"\(", source)
        if match:
            positions.append((match.start(), method))
    positions.sort()
    found = {}
    for index, (start, method) in enumerate(positions):
        end = positions[index + 1][0] if index + 1 < len(positions) else len(source)
        body = source[start:end]
        values = set(re.findall(r'Option\(args,\s*"(--[a-z0-9-]+)"', body))
        values |= set(re.findall(
            r'(?:Required|Optional)Number\(args,\s*"(--[a-z0-9-]+)"', body))
        flags = set(re.findall(r'Array\.IndexOf\(args,\s*"(--[a-z0-9-]+)"', body))
        found[HANDLERS[method]] = (values, flags)
    return found


def test_the_table_covers_every_command_the_dispatcher_knows():
    source = _source()
    assert dispatcher_commands(source) == set(declared_table(source)), (
        "rozdzielacz i tabela znanych opcji wymieniaja rozne polecenia: "
        f"{sorted(dispatcher_commands(source))} vs {sorted(declared_table(source))}")


def test_every_option_the_code_reads_is_in_the_table():
    source = _source()
    table = declared_table(source)
    for command, (values, flags) in read_by_code(source).items():
        declared_values, declared_flags = table[command]
        assert values <= declared_values, (
            f"polecenie {command} czyta opcje spoza tabeli: "
            f"{sorted(values - declared_values)} — dopisz je do KnownOptions, "
            "inaczej odmowa odrzuci opcje, ktora dziala")
        assert flags <= declared_flags, (
            f"polecenie {command} czyta flagi spoza tabeli: "
            f"{sorted(flags - declared_flags)}")


def test_the_table_does_not_declare_options_nobody_reads():
    """Drugi kierunek. Nazwa w tabeli, ktorej kod nie czyta, jest gorsza niz jej brak:
    odmowa przepuszcza taka opcje, a polecenie i tak jej nie uzyje — czyli literowka
    znowu przechodzi w milczeniu."""
    source = _source()
    read = read_by_code(source)
    for command, (values, flags) in declared_table(source).items():
        code_values, code_flags = read[command]
        assert values <= code_values, (
            f"tabela deklaruje dla {command} opcje, ktorych kod nie czyta: "
            f"{sorted(values - code_values)}")
        assert flags <= code_flags, (
            f"tabela deklaruje dla {command} flagi, ktorych kod nie czyta: "
            f"{sorted(flags - code_flags)}")


def test_the_refusal_is_actually_wired_into_main():
    """Tabela bez wywolania jest dekoracja. Sprawdzane jest jedno: `Main` wola
    odmowe PRZED rozdzielaczem, bo po nim polecenie zdazyloby juz przeczytac
    argumenty i wykonac prace."""
    source = _source()
    call = source.index("RejectUnknownOptions(args[0], args);")
    switch = source.index("return args[0] switch")
    assert call < switch, "odmowa wolana po rozdzielaczu — polecenie zdazy zadzialac"


def test_the_refusal_skips_positional_arguments():
    """`compare` bierze dwie sciezki pozycyjnie. Odmowa zbudowana na „wszystko, czego
    nie znam" wywrocilaby to polecenie w calosci, wiec sprawdzenie ogranicza sie do
    czlonow zaczynajacych sie od dwoch minusow — i ten warunek ma stac w kodzie."""
    source = _source()
    at = source.index("private static void RejectUnknownOptions")
    body = source[at:source.index("\n    private static int Unknown", at)]
    assert 'StartsWith("--"' in body, "odmowa nie odsiewa argumentow pozycyjnych"
    assert "known.Flags" in body and "known.Values" in body, (
        "odmowa nie rozroznia flagi od opcji z wartoscia — flaga zjadlaby nastepny czlon")

# 6.D25: uruchomienie tego pliku WPROST idzie ta sama droga, co caly zestaw —
# z licznikiem asercji i z odmowa przy zerze testow. Bez tej gałęzi `python3
# tools/tests/<modul>.py` konczyl sie kodem 0, nie wykonawszy ani jednego testu.
if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))
