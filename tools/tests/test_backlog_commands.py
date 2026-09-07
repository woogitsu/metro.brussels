#!/usr/bin/env python3
"""Bramka: pole „Weryfikacja" bloku niesie komendy, a nie samą obietnicę.

Zmierzone 06.09.2026 przy pozycji 6.D15. `tools/tests/test_backlog.py` pilnuje, żeby
pole „Weryfikacja" MIAŁO treść — i to jest jedyne, czego pilnuje. Treść może dziś być
zdaniem po polsku, komendą bez wymaganych opcji albo komendą, którą kod odrzuca:
licznik pól zobaczy w każdym z tych przypadków to samo.

Pomiar tej pozycji pokazał trzy klasy usterek w polach, a każda z nich wygląda w
`test_backlog.py` jak pole wypełnione:

1. **komenda z miejscem do wypełnienia** — `--signalling <plan>`, `--steps <N>`,
   `--journal <własny dziennik>`. Nawiasu ostrokątnego nie da się wpisać do terminala,
   a co ma stać w środku, wie tylko autor bloku;
2. **komenda bez opcji, których kod wymaga** — pełna komenda `budget` z bloku 6.D2
   kończy się kodem 1 na `BŁĄD: line wymaga --limit-kmh`, bo pole wymienia trzy opcje
   z siedmiu wymaganych;
3. **komenda, którą kod odrzuca z zasady** — blok 6.C3 łączy `--line` z `--telemetry`,
   a to jest jawna odmowa z kodem wyjścia 9.

Ta bramka nie łapie klasy 2 ani 3 — do tego trzeba uruchomić komendę, a część z nich
potrzebuje Blendera, sieci albo kwadransa. Łapie klasę 1, która jest **składniowa**,
i pilnuje, że kolektor komend z `backlog_commands.py` nie przestanie ich widzieć.

Dlaczego to nie jest zapadka na liczbę komend: liczba rośnie z każdą nową pozycją
i malałaby z każdą domkniętą, więc próg na nią świeciłby na czerwono za wykonaną pracę
— dokładnie tak, jak `MINIMUM_DOCUMENTED_ITEMS` przed przepisaniem 06.09.2026.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import backlog_commands as bc  # noqa: E402

#: Bloki, ktore po pomiarze 6.D15 nadal maja w komendzie miejsce do wypelnienia.
#: Pomiar zastal trzy takie bloki: 6.D2, 6.D9 i 6.B18. Poprawiony zostal wylacznie
#: 6.D2, bo tylko on jest pozycja NIEZROBIONA; blok pozycji zrobionej jest zapisem
#: historycznym i jego poprawka lezy poza zakresem 6.D15. Dlatego lista nie jest pusta
#: i nie ma byc: to linia bazowa, zeby nowe pole z nawiasem ostrokatnym dalo sie
#: odroznic od zastanego.
KNOWN_PLACEHOLDER_BLOCKS = {"6.D9", "6.B18"}


def test_collector_sees_the_commands_that_are_in_the_file():
    found = bc.inventory()
    assert found, "kolektor nie zebrał ani jednego bloku"
    assert "6.D15" in found, "brak bloku tej pozycji — kolektor czyta nie ten plik"
    every = [c for commands in found.values() for c in commands]
    assert len(every) > len(found), (
        "komend jest nie więcej niż bloków — kolektor zwija płotek do jednego wiersza")


def test_every_block_with_a_fence_yields_at_least_one_command():
    for number, commands in bc.inventory().items():
        assert commands, ('blok ' + number + ' ma puste pole Weryfikacja mimo plotka')


def test_a_loop_comes_out_as_one_pasteable_command():
    """Pętla `for … do … done` jest JEDNYM poleceniem, i musi dać się wkleić.

    Sklejenie wierszy spacją dawało `--out "…json" done` — tekst, który liczy się
    jako jedna komenda, ale którego nie da się uruchomić. Licznik był wtedy dobry,
    a wypis z raportu — nie.
    """
    fence = (
        'for AXIS in L1_B L2_E; do\n'
        '    python3 narzedzie.py --axis "$AXIS" \\\n'
        '        --out "build/$AXIS.json"\n'
        'done\n'
    )
    got = bc.commands(fence)
    assert len(got) == 1, got
    assert got[0].endswith("; done"), got[0]
    assert " done" not in got[0].replace("; done", ""), got[0]
    assert "\\" not in got[0], got[0]


def test_a_comment_line_is_not_a_command():
    fence = "# licznik, który wskazał te sześć\npython3 tools/tests/test_all.py\n"
    got = bc.commands(fence)
    assert got == ["python3 tools/tests/test_all.py"], got


def test_a_backslash_continuation_is_one_command():
    fence = 'blender --background \\\n    --python tools/blender/x.py -- \\\n    --out build/x.glb\n'
    got = bc.commands(fence)
    assert len(got) == 1, got
    assert got[0] == "blender --background --python tools/blender/x.py -- --out build/x.glb", got[0]


def test_placeholders_are_detected_and_are_not_everywhere():
    assert bc.has_placeholder("dotnet run -- budget --signalling <plan>")
    assert not bc.has_placeholder("python3 tools/tests/test_all.py")
    # Kontrola, że wykrywacz nie zjada zwykłego przekierowania powłoki.
    assert not bc.has_placeholder("python3 x.py 2>&1 | tail -3")


def test_the_blocks_with_placeholders_are_the_ones_the_measurement_named():
    """Nowe pole z `<…>` ma być widoczne, a nie utopione w liczbie.

    Zbiór, nie liczba: kiedy blok z nawiasem zostanie poprawiony, test zapali się
    z nazwą bloku, którego nie ma na liście — i to jest informacja, a nie hałas.
    """
    found = bc.inventory()
    with_placeholder = {number for number, commands in found.items()
                        if any(bc.has_placeholder(c) for c in commands)}
    assert with_placeholder == KNOWN_PLACEHOLDER_BLOCKS, (
        f"bloki z miejscem do wypełnienia: {sorted(with_placeholder)}, "
        f"spodziewane: {sorted(KNOWN_PLACEHOLDER_BLOCKS)}")


def test_the_verification_field_is_cut_at_the_next_field():
    """Pole kończy się na następnym punkcie, inaczej wciąga cudze płotki."""
    body = (
        "##### 9.Z9 · przyklad\n"
        "- **Weryfikacja:**\n"
        "  ```bash\n"
        "  python3 moje.py\n"
        "  ```\n"
        "- **Skończone, gdy:** zielono\n"
        "  ```bash\n"
        "  python3 cudze.py\n"
        "  ```\n"
    )
    field = bc.verification_field(body)
    assert "moje.py" in field, field
    assert "cudze.py" not in field, field

# 6.D25: uruchomienie tego pliku WPROST idzie ta sama droga, co caly zestaw —
# z licznikiem asercji i z odmowa przy zerze testow. Bez tej gałęzi `python3
# tools/tests/<modul>.py` konczyl sie kodem 0, nie wykonawszy ani jednego testu.
if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))
