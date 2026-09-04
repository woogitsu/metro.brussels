#!/usr/bin/env python3
"""Bramka na ostrzeżenia Godota: przebieg z `WARNING` nie jest zielonym przebiegiem.

DLACZEGO TA BRAMKA ISTNIEJE. `godot-first-run.yml` uruchamia scenę kilkanaście razy
i do 04.09.2026 żaden krok nie patrzył, czy silnik czegoś nie wypisał. Przebieg
`--line --limit-kmh=70` kończył się kodem 0, telemetria zgadzała się z rdzeniem CO DO
BITU, wszystkie bramki świeciły na zielono — a w logu stało **dziesięć** ostrzeżeń
`Target and up vectors are colinear` z `FirstRun.PlaceEverything`, czyli kamera
goniąca dziesięć razy dostała kierunek, którego nie ma, i dostała za niego obrót
wybrany przez silnik. To jest dokładnie ta rodzina, którą `CLAUDE.md` §5 wymienia
wprost: „skrypt wykonał się bez błędu" nie jest weryfikacją.

CO ODRÓŻNIA. Część ostrzeżeń Godota nie pochodzi od sceny, tylko od maszyny bez karty
graficznej i bez karty dźwiękowej — te muszą przechodzić, bo inaczej bramka nie da się
włączyć w ogóle. Lista dopuszczonych jest więc **jawna, krótka i z powodem przy każdej
pozycji**, a dopasowanie jest po CAŁEJ treści ostrzeżenia, nie po fragmencie: pozycja
„zawiera słowo Vulkan" przepuściłaby wszystko, co to słowo zawiera.

CZEGO NA LIŚCIE NIE MA I DLACZEGO. Wiersze `ALSA lib ... cannot find card '0'` nie są
ostrzeżeniami Godota — to własne wyjście biblioteki ALSA na stderr, bez przedrostka
`WARNING:`. Ten skrypt ich nie widzi i nie ma po co ich dopuszczać; ostrzeżenie, które
z nich WYNIKA (`All audio drivers failed`), stoi na liście wprost.
"""
import argparse
import os
import re
import sys

# Ostrzeżenie Godota to wiersz `WARNING: <treść>`, po którym idzie wcięte `at: ...`
# i ewentualnie ślad stosu C#. Bramkę interesuje wyłącznie treść.
WARNING = re.compile(r"^WARNING:\s*(.+?)\s*$")

# (treść, dlaczego wolno). Treść jest porównywana W CAŁOŚCI.
ALLOWED = (
    (
        "Could not set V-Sync mode, as changing V-Sync mode is not supported by the "
        "graphics driver.",
        "Xvfb + llvmpipe nie mają czym sterować odstępem synchronizacji; scena nie "
        "prosi o V-Sync ani go nie czyta, a na maszynie z kartą to ostrzeżenie "
        "w ogóle nie powstaje",
    ),
    (
        "All audio drivers failed, falling back to the dummy driver.",
        "runner nie ma karty dźwiękowej (`ALSA lib confmisc.c:855:(parse_card) cannot "
        "find card '0'`); scena nie odtwarza dźwięku, więc sterownik zastępczy niczego "
        "nie zmienia w tym, co bramki mierzą",
    ),
)


def warnings(text):
    """Treści wszystkich ostrzeżeń Godota z logu, w kolejności wystąpienia."""
    found = []
    for line in text.splitlines():
        match = WARNING.match(line)
        if match:
            found.append(match.group(1))
    return found


def reason(message):
    """Powód, dla którego to ostrzeżenie wolno przepuścić, albo `None`."""
    for allowed, why in ALLOWED:
        if message == allowed:
            return why
    return None


def offending(text):
    """Ostrzeżenia spoza listy dopuszczonych."""
    return [message for message in warnings(text) if reason(message) is None]


def check(path):
    """(liczba dopuszczonych, lista niedopuszczonych) dla jednego logu."""
    with open(path, encoding="utf-8", errors="replace") as handle:
        text = handle.read()
    found = warnings(text)
    bad = offending(text)
    return len(found) - len(bad), bad


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("logs", nargs="+", help="logi przebiegów Godota (stdout+stderr)")
    args = parser.parse_args(argv)

    failed = False
    for path in args.logs:
        if not os.path.isfile(path):
            print(f"BŁĄD: brak logu {path} — bramka nie ma czego sprawdzić", file=sys.stderr)
            failed = True
            continue

        allowed_count, bad = check(path)
        name = os.path.basename(path)
        if bad:
            failed = True
            print(
                f"BŁĄD: {name} — {len(bad)} ostrzeżeń Godota spoza listy dopuszczonych:",
                file=sys.stderr,
            )
            for message in bad:
                print(f"  WARNING: {message}", file=sys.stderr)
            print(
                "Ostrzeżenie znaczy, że scena zrobiła coś bez zdefiniowanej odpowiedzi. "
                "Napraw przyczynę. Jeżeli to naprawdę szum środowiska, dopisz JEGO PEŁNĄ "
                "TREŚĆ do ALLOWED w tools/ci/assert_no_godot_warnings.py razem z powodem.",
                file=sys.stderr,
            )
        else:
            print(f"[OSTRZEŻENIA] {name}: 0 spoza listy, {allowed_count} środowiskowych")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
