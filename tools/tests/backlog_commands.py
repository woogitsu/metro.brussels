#!/usr/bin/env python3
"""Komendy z pól „Weryfikacja" bloków `docs/TASKS.md` — zebrane, nie zapamiętane.

**Po co ten moduł istnieje.** `tools/tests/test_backlog.py` sprawdza, czy blok pozycji
ma sześć pól i czy każde ma treść. Nie sprawdza — i nie ma jak sprawdzić — czy treść
pola „Weryfikacja" da się w ogóle wpisać do terminala. Pole jest obietnicą, a obietnicy
nikt nie odbierał: pozycja 6.C3 (#297) wyszła z bloku, którego komenda jest odrzucana
przez istniejącą w kodzie odmowę łączenia źródeł, kod wyjścia 9. Agent zbudował własną
drogę pomiaru i zrobił zadanie, ale pole kłamało od chwili, w której powstało.

**Czego ten moduł NIE robi.** Nie uruchamia komend i nie ocenia, czy działają. Wyrok dla
każdej komendy jest pomiarem ręcznym i stoi w `reports/komendy-weryfikacji.md`; tutaj
jest wyłącznie ta część, która musi dawać ten sam wynik za tydzień: **ile komend stoi
dziś w blokach i które to są**. Liczba policzona raz i wpisana do raportu rozjeżdża się
bezszelestnie — to ta sama rodzina usterki, którą łapie bramka z #273.

**Co jest komendą.** Płotek ``` w polu „Weryfikacja" bywa wielowierszowy, a wiersze
nie są niezależne. Sklejane są trzy rzeczy, bo inaczej licznik liczyłby fragmenty
składni zamiast poleceń:

* kontynuacja wiersza (`\\` na końcu) — jedna komenda rozbita na kilka wierszy;
* pętla `for … ; do` … `done` — jedno polecenie powłoki, nie trzy;
* wiersz komentarza (`#`) — nie jest komendą i nie jest liczony.
"""
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TASKS = os.path.join(ROOT, "docs", "TASKS.md")

#: Pole, którego treść nas interesuje, w brzmieniu z `docs/TASK-TEMPLATE.md`.
FIELD = "Weryfikacja"

#: Znaczniki, po których widać, że komendy NIE da się wpisać dosłownie: nawias
#: ostrokątny jest w tym pliku używany jako miejsce do wypełnienia (`<plan>`,
#: `<N>`, `<własny dziennik>`). Wykrycie jest składniowe i celowo głupie —
#: rozstrzygnięcie, czy komenda działa, należy do pomiaru, nie do tego pliku.
PLACEHOLDER = re.compile(r"<[^>]+>")


def _tasks():
    with open(TASKS, encoding="utf-8") as handle:
        return handle.read()


def verification_field(body):
    """Treść pola „Weryfikacja" bloku albo `None`, gdy pola nie ma.

    Pole kończy się na następnym punkcie listy `- **…:**`, tak samo jak w
    `test_backlog.missing_fields` — to ten sam kształt dokumentu i celowo ta sama
    reguła cięcia.
    """
    marker = "- **%s:**" % FIELD
    at = body.find(marker)
    if at < 0:
        return None
    rest = body[at + len(marker):]
    nxt = re.search(r"\n- \*\*", rest)
    return rest if nxt is None else rest[:nxt.start()]


def fenced_blocks(field):
    """Wszystkie płotki ``` z treści pola, w kolejności wystąpienia."""
    return re.findall(r"```(?:bash|sh|console)?\n(.*?)```", field or "", re.S)


def commands(fence):
    """Wiersze plotka sklejone w komendy: kontynuacje, petle, bez komentarzy."""
    out = []
    parts = []
    continuing = False
    depth = 0
    for line in fence.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if not parts and depth == 0 and stripped.startswith("#"):
            continue
        more = stripped.endswith("\\")
        if more:
            stripped = stripped[:-1].strip()
        if continuing:
            parts[-1] = (parts[-1] + " " + stripped).strip()
        else:
            parts.append(stripped)
        continuing = more
        if continuing:
            continue
        tail = parts[-1]
        if re.search(r"(^|;)\s*do$", tail):
            depth += 1
            continue
        if depth:
            if tail == "done":
                depth -= 1
                if depth:
                    continue
            else:
                continue
        out.append(_join(parts))
        parts = []
    if parts:
        out.append(_join(parts))
    return out


def _join(parts):
    """Kilka wierszy powloki w jeden wiersz: srednik tam, gdzie go brakuje."""
    joined = parts[0]
    for part in parts[1:]:
        separator = " " if joined.endswith((";", "do", "|", "&&", "||")) else "; "
        joined = joined + separator + part
    return joined


def inventory(text=None):
    """`{numer: [komenda, …]}` dla każdego bloku, który ma pole „Weryfikacja"."""
    import test_backlog

    text = _tasks() if text is None else text
    found = {}
    for number, body in test_backlog.detail_sections(text).items():
        field = verification_field(body)
        if field is None:
            continue
        collected = []
        for fence in fenced_blocks(field):
            collected.extend(commands(fence))
        found[number] = collected
    return found


def has_placeholder(command):
    """Czy komenda ma miejsce do wypełnienia, którego nie da się wpisać dosłownie."""
    return bool(PLACEHOLDER.search(command))


def main():
    import sys

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    found = inventory()
    total = 0
    placeholders = 0
    for number in sorted(found):
        for command in found[number]:
            total += 1
            mark = "  ?" if has_placeholder(command) else "   "
            if has_placeholder(command):
                placeholders += 1
            print(f"{number:>7}{mark} {command}")
    print("\nblokow z polem " + '„' + FIELD + '”' + ": %d" % len(found))
    print(f"komend zebranych: {total}")
    print(f"komend z miejscem do wypełnienia (?): {placeholders}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
