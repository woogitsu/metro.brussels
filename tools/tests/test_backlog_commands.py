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


def test_a_heredoc_body_is_not_a_command():
    """Ciało heredoku to DANE dla polecenia, nie polecenia — 6.D100.

    Kontrola negatywna z pola „Skończone, gdy": płotek z heredokiem o dwóch
    wierszach ciała ma dać JEDNĄ komendę, a nie cztery (otwarcie, dwa wiersze
    ciała, terminator). Cztery to liczba, którą dawał kolektor przed tą pozycją.
    """
    fence = (
        "  cat > build/x.txt <<'EOF'\n"
        "  pierwszy wiersz\n"
        "  drugi wiersz\n"
        "  EOF\n"
    )
    got = bc.commands(fence)
    assert len(got) == 1, got

    # I ma się dać WKLEIĆ: terminator w osobnym wierszu, ciało bez wcięcia płotka.
    assert got[0] == (
        "cat > build/x.txt <<'EOF'\n"
        "pierwszy wiersz\n"
        "drugi wiersz\n"
        "EOF"
    ), repr(got[0])


def test_a_heredoc_body_keeps_what_a_command_line_would_lose():
    """W ciele zostaje to, co poza nim jest pomijane: puste wiersze, `#`, wcięcie.

    Wiersz `#` w ciele heredoku Pythona jest komentarzem PYTHONA i jest treścią;
    pominięcie go zmieniłoby program, który komenda wkleja na wejście.
    """
    fence = (
        "  python3 - <<'EOF'\n"
        "  # to jest komentarz Pythona\n"
        "\n"
        "  if True:\n"
        "      print(1)\n"
        "  EOF\n"
    )
    got = bc.commands(fence)
    assert len(got) == 1, got
    assert "# to jest komentarz Pythona" in got[0], repr(got[0])
    assert "\n\n" in got[0], ("pusty wiersz ciała zniknął: " + repr(got[0]))
    assert "\n    print(1)" in got[0], ("wcięcie ciała zniknęło: " + repr(got[0]))


def test_a_heredoc_inside_a_loop_does_not_break_the_loop():
    """Heredok w pętli nie kończy pętli — terminator zamyka ciało, nie komendę."""
    fence = (
        "  for X in a b; do\n"
        "      cat <<EOF\n"
        "      linia $X\n"
        "  EOF\n"
        "  done\n"
    )
    got = bc.commands(fence)
    assert len(got) == 1, got
    assert got[0].endswith("\ndone"), repr(got[0])


def test_a_conflict_marker_is_not_a_heredoc():
    """`<<<<<<< HEAD` czyta się jak heredok o terminatorze `HEAD` — i nie jest nim.

    Kontrola przyrządu dla `HEREDOC`. Wzorzec bez strażników `(?<!<)` i `(?!<)`
    łapie parę `<` na piątym znaku znacznika konfliktu; taki znacznik stoi
    w opisie 6.D55 w `docs/TASKS.md` (wiersz 912 w dniu pomiaru). Do płotka
    „Weryfikacja" nie wchodzi, ale wzorzec ma być prawdziwy, a nie prawdziwy
    przypadkiem.
    """
    for otwiera, terminator in (
        ("python3 - <<'EOF'", "EOF"),
        ('cat <<"KONIEC"', "KONIEC"),
        ("cat <<-EOF", "EOF"),
        ("cat <<EOF", "EOF"),
    ):
        m = bc.HEREDOC.search(otwiera)
        assert m, otwiera
        assert (m.group(1) or m.group(2) or m.group(3)) == terminator, otwiera

    for nie_heredok in ("<<<<<<< HEAD", ">>>>>>> gałąź", 'grep x <<<"abc"'):
        assert not bc.HEREDOC.search(nie_heredok), nie_heredok


def test_an_unterminated_heredoc_keeps_its_body_instead_of_swallowing_it():
    """Płotek urwany w środku ciała: wiersze zostają przy komendzie, nie znikają.

    Połknięcie ich po cichu byłoby tą samą usterką, którą ta pozycja zdejmuje,
    tylko w drugą stronę — licznik zgodny, a wypis niepełny.
    """
    fence = "  python3 - <<'EOF'\n  print(1)\n"
    got = bc.commands(fence)
    assert len(got) == 1, got
    assert got[0] == "python3 - <<'EOF'\nprint(1)", repr(got[0])


def test_the_only_heredoc_in_the_file_is_the_one_the_measurement_named():
    """Zbiór, nie liczba: nowy blok z heredokiem ma być widoczny z nazwy.

    Zmierzone 10.09.2026: jeden płotek z heredokiem w całym `docs/TASKS.md`
    (blok 6.A24), a ten blok daje **cztery** komendy — przed 6.D100 dawał osiem.
    """
    found = bc.inventory()
    z_heredokiem = {number for number, commands in found.items()
                    if any(bc.HEREDOC.search(c) for c in commands)}
    assert z_heredokiem == {"6.A24"}, sorted(z_heredokiem)
    assert len(found["6.A24"]) == 4, found["6.A24"]

    # Dolne ostrze na sam kolektor: gdyby przestał cokolwiek zbierać, zbiór wyżej
    # też byłby pusty i test świeciłby na zielono z niewiedzy.
    every = [c for commands in found.values() for c in commands]
    assert len(every) >= 320, len(every)


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


def test_operator_w_ciele_heredoku_nie_jest_miejscem_do_wypelnienia():
    """6.D118: `<plan>` kontra `a < b` — obie strony na wejściu syntetycznym.

    Od 6.D100 kolektor skleja z komendą także ciało heredoku, a ciało bywa PROGRAMEM
    (w 6.A24 są to trzy wiersze Pythona). Dawny wzorzec `<[^>]+>` brał w takim ciele
    każdy odcinek między `<` a `>` za miejsce do wypełnienia — czyli zgłaszałby tekst
    poprawny, a bramka zgłaszająca tekst poprawny jest bramką do wyłączenia (6.D27).

    Kontrola stoi na wejściu SYNTETYCZNYM, bo dzisiejszy jedyny heredok nawiasu
    ostrokątnego nie ma: na samym drzewie obie reguły — dawna i dzisiejsza — dają ten
    sam werdykt, więc drzewo ich nie odróżnia.
    """
    for komenda in ("dotnet run -- budget --signalling <plan>",
                    "python3 png.py <dwa PNG z dwóch przebiegów tej samej sceny>",
                    "python3 sweep.py --journal <własny dziennik>",
                    "python3 t.py --out <x>"):
        assert bc.has_placeholder(komenda), komenda

    for komenda in ("if a < b and b > c:",
                    "x <- y",
                    "cmd < wejscie > wyjscie",
                    "python3 x.py 2>&1 | tail -3",
                    "grep -c '' < plik"):
        assert not bc.has_placeholder(komenda), (
            "operator wzięty za miejsce do wypełnienia: %r" % komenda)


def test_cialo_heredoku_z_operatorem_przechodzi_CALA_droga():
    """Nie sam wzorzec, tylko droga: płotek → `commands` → `has_placeholder`.

    To jest przypadek, o który chodzi w 6.D118 i którego dzisiejszy `docs/TASKS.md`
    nie ma: heredok, którego ciałem jest program używający `<` jako operatora.
    Test na samym wzorcu nie powiedziałby, czy ciało w ogóle dochodzi do pytania —
    a dochodzi dopiero od 6.D100, które skleiło ciało z komendą.
    """
    plotek = (
        "python3 - <<'PY'\n"
        "a, b, c = 1, 2, 3\n"
        "if a < b and b > c:\n"
        "    print('tak')\n"
        "PY\n"
    )
    zebrane = bc.commands(plotek)
    assert len(zebrane) == 1, zebrane
    assert "if a < b and b > c:" in zebrane[0], (
        "ciało heredoku nie doszło do komendy — bez tego reszta testu mierzy nic")
    assert not bc.has_placeholder(zebrane[0]), (
        "operator w ciele heredoku wzięty za miejsce do wypełnienia: %r" % zebrane[0])

    # Druga strona: miejsce do wypełnienia W CIELE ma zostać zauważone.
    z_miejscem = bc.commands(
        "python3 - <<'PY'\n"
        "sciezka = '<własny dziennik>'\n"
        "PY\n"
    )
    assert len(z_miejscem) == 1, z_miejscem
    assert bc.has_placeholder(z_miejscem[0]), z_miejscem


def test_granica_reguly_miejsca_jest_ZAPISANA_a_nie_udawana():
    """Czego reguła nie rozstrzyga — przybite, żeby nikt nie wziął tego za pokryte.

    Porównanie BEZ spacji z późniejszym `>` w tym samym wierszu nadal czyta się jako
    miejsce do wypełnienia. Odróżnienie wymagałoby rozbioru składni języka, którym
    akurat jest ciało heredoku, a kolektor poleceń tego nie wie. Ten test nie żąda
    poprawy — żąda, żeby granica była WIDOCZNA i żeby jej przesunięcie było zmianą,
    którą ktoś zobaczy.
    """
    assert bc.has_placeholder("if (a<b) return a>b;"), (
        "granica reguły przesunęła się — porównanie bez spacji przestało być brane "
        "za miejsce do wypełnienia; to jest poprawa, ale ma zostać opisana")
    assert not bc.has_placeholder("if (a < b) return a > b;"), (
        "to samo porównanie ze spacjami przestało być odróżniane")


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
