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
* **ciało heredoku** (`<<'EOF'` … `EOF`) — dane dla polecenia, nie polecenia;
* wiersz komentarza (`#`) — nie jest komendą i nie jest liczony.

**Heredok dopisany 10.09.2026 (6.D100).** Zmierzone: w dzisiejszym `docs/TASKS.md`
jest **jeden** płotek z heredokiem — blok 6.A24 — i kolektor liczył go jako **pięć**
komend (otwarcie, trzy wiersze ciała, `EOF`) zamiast jednej, zawyżając licznik całego
pliku o cztery: **324 zamiast 320**. Zawyżenie nie jest kosmetyką licznika: ta sama
liczba jest mianownikiem każdego zdania o pokryciu audytu komend (6.D15, 6.D33).

**Ciało heredoku bierze się DOSŁOWNIE**, inaczej niż każdy inny wiersz płotka: bez
`strip()`, bez pomijania wierszy pustych i bez pomijania `#`. W ciele to są dane —
komentarz Pythona jest treścią, a nie komentarzem powłoki, i wcięcie bywa składnią.

**Dwa znaki mniej i dwa znaki więcej to nie heredok**, i to jest zmierzone, a nie
przewidziane: w tym pliku stoją trzy wystąpienia `<<`, z czego heredokiem jest
**jedno**. Pozostałe to `<<<<<<< HEAD` z opisu 6.D55 (znacznik konfliktu) i cytat
cytat samego zapisu heredoku w opisie tej właśnie pozycji. Pierwsze złapałby wzorzec bez
strażników — `<<` na piątym znaku, spacja, `HEAD` — i ogłosiłby heredok o terminatorze
`HEAD`. Dlatego `HEREDOC` żąda, żeby po lewej i po prawej stronie pary `<` nie było
trzeciego. Do płotka „Weryfikacja" żadne z tych dwóch i tak nie wchodzi, ale wzorzec
ma być prawdziwy, a nie prawdziwy przypadkiem.
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

#: Otwarcie heredoku: `<<EOF`, `<<'EOF'`, `<<"EOF"` i wariant `<<-` (obcinający
#: tabulatory). Strażnicy `(?<!<)` i `(?!<)` odsiewają `<<<` (herestring) oraz
#: znacznik konfliktu `<<<<<<< HEAD`, który bez nich czyta się jako heredok
#: o terminatorze `HEAD` — zmierzone na wierszu 912 `docs/TASKS.md`.
HEREDOC = re.compile(
    r"(?<!<)<<-?(?!<)\s*(?:'([^']+)'|\"([^\"]+)\"|([A-Za-z_][A-Za-z0-9_]*))")


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
    """Wiersze plotka sklejone w komendy: kontynuacje, petle, heredoki, bez komentarzy."""
    out = []
    parts = []
    ciala = {}              # indeks w `parts` -> (wiersze ciala, terminator)
    continuing = False
    depth = 0
    terminator = None       # nie-None: jestesmy W SRODKU ciala heredoku
    body = None
    wciecie = ""            # wciecie plotka, zdjete z ciala heredoku

    for line in fence.splitlines():
        stripped = line.strip()

        # CIALO HEREDOKU idzie pierwsze i bierze wiersz DOSLOWNIE: bez pomijania
        # pustych, bez pomijania `#`, bez sklejania kontynuacji. To sa dane dla
        # polecenia, a nie polecenia — `#` jest tam komentarzem Pythona, a nie
        # powloki, i wciecie bywa skladnia.
        if terminator is not None:
            if stripped == terminator:
                ciala[len(parts) - 1] = (body, terminator)
                terminator, body = None, None
                # Terminator KONCZY tylko heredok, nie komende: dalej idzie ta
                # sama sciezka, co po zwyklym wierszu, wiec heredok w petli
                # `do … done` nie wypada z niej przedwczesnie.
                tail = parts[-1]
                if depth and tail != "done":
                    continue
                out.append(_join(parts, ciala))
                parts, ciala = [], {}
                continue
            body.append(_bez_wciecia(line, wciecie))
            continue

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

        # Heredok otwarty w tym wierszu: reszta komendy jest ponizej, wiec komendy
        # jeszcze nie wypuszczamy.
        opened = HEREDOC.search(tail)
        if opened:
            terminator = opened.group(1) or opened.group(2) or opened.group(3)
            body = []
            # Wciecie WIERSZA OTWIERAJACEGO, nie calego plotka: to ono jest
            # formatowaniem markdownu wokol tego heredoku. Bez zdjecia go cialo
            # wyjezdza wcieta o dwie spacje, a `python3 - <<'EOF'` z wcietym
            # cialem to `IndentationError`, nie komenda do wklejenia.
            wciecie = line[:len(line) - len(line.lstrip())]
            continue

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
        out.append(_join(parts, ciala))
        parts, ciala = [], {}
    if terminator is not None:
        # Plotek skonczyl sie W SRODKU heredoku. Cialo zebrane do tej pory zostaje
        # PRZY komendzie, a nie znika: wiersze polkniete po cichu byłyby
        # dokladnie ta usterka, ktora ta pozycja zdejmuje, tylko w druga strone.
        # Terminatora nie dopisujemy, bo w pliku go nie ma — komenda ma wygladac
        # na urwana, bo urwana jest.
        ciala[len(parts) - 1] = (body, None)
    if parts:
        out.append(_join(parts, ciala))
    return out


def _bez_wciecia(line, wciecie):
    """Wiersz ciala bez wciecia plotka; reszta bialych znakow ZOSTAJE."""
    if line.startswith(wciecie):
        return line[len(wciecie):]
    return line.lstrip()


def _join(parts, ciala=None):
    """Kilka wierszy powloki w jedna komende; ciala heredokow zostaja w wierszach.

    Srednik tam, gdzie go brakuje — z jednym wyjatkiem: po terminatorze heredoku
    idzie ZNAK NOWEGO WIERSZA, bo `EOF; nastepne` nie jest tym samym poleceniem,
    ktore stalo w pliku. Ta funkcja sklada komende do WKLEJENIA, a nie do
    policzenia, wiec wyjatek jest jej trescia, a nie ozdoba.
    """
    ciala = ciala or {}

    def kawalek(i):
        tresc = parts[i]
        if i in ciala:
            wiersze, terminator = ciala[i]
            ogon = wiersze if terminator is None else wiersze + [terminator]
            tresc = "\n".join([tresc] + ogon)
        return tresc

    joined = kawalek(0)
    for i in range(1, len(parts)):
        if i - 1 in ciala:
            separator = "\n"
        elif joined.endswith((";", "do", "|", "&&", "||")):
            separator = " "
        else:
            separator = "; "
        joined = joined + separator + kawalek(i)
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
