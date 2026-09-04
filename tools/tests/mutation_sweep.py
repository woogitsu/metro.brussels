#!/usr/bin/env python3
"""Przegląd mutacyjny bramek: psuje kod i sprawdza, czy testy to zauważą.

**Po co.** Audyt z 02.09.2026 znalazł cztery zielone bramki, które niczego nie
sprawdzały, i wszystkie cztery znalazła mutacja, nie czytanie kodu. W tej samej sesji
doszły dwie kolejne. Sześć na sześć prób — to nie jest wyjątek, to stan. Zielona bramka
bez pokrycia jest gorsza niż brak bramki, bo usypia.

**Czego to narzędzie NIE robi.** Nie mutuje testów. Mutuje **kod pod testem** i pyta,
czy zestaw testów to wyłapie. Mutacja, która przeżyje, znaczy jedno z dwojga: albo
w tym miejscu nie ma pokrycia, albo jest **mutantem równoważnym** — zmianą, której nie
da się zaobserwować. Jedno i drugie trzeba obejrzeć; narzędzie nie zgaduje, które to.

**Dlaczego akurat porównania i progi.** Sweep po wszystkim byłby tydzień pracy maszyny
i utopiłby sygnał. Wszystkie sześć znalezionych dotąd usterek miało tę samą postać:
liczba albo porównanie, które wyglądało na bramkę, a nią nie było. Tu mutowane są
dokładnie te dwie rzeczy — operatory porównań i stałe liczbowe stojące w porównaniach.

**Determinizm.** Mutacje powstają z AST w ustalonej kolejności (plik, wiersz, kolumna),
więc dwa przebiegi na tym samym drzewie dają tę samą listę i te same identyfikatory.
"""
from __future__ import annotations

import argparse
import ast
import concurrent.futures
import dataclasses
import json
import os
import re
import subprocess
import sys
import tempfile
import threading

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# Dziennik jest jednym plikiem dla wszystkich robotników, więc zapis idzie
# pod zamkiem. Bez niego dwa wiersze potrafią się przepleść i oba przepadają.
JOURNAL_LOCK = threading.Lock()

# Operator -> (napis w kodzie, wzorzec szukający go, napis po mutacji).
# Wzorce pilnują, żeby `<` nie trafił w `<=` ani w `<<`.
OPERATORS = {
    ast.Lt: ("<", r"<(?!=)", "<="),
    ast.LtE: ("<=", r"<=", "<"),
    ast.Gt: (">", r">(?!=)", ">="),
    ast.GtE: (">=", r">=", ">"),
    ast.Eq: ("==", r"==", "!="),
    ast.NotEq: ("!=", r"!=", "=="),
}


@dataclasses.dataclass(frozen=True)
class Mutation:
    """Jedna zmiana: podmiana tekstu w jednym miejscu jednego pliku."""

    path: str          # ścieżka względem korzenia repo
    line: int          # 1-indeksowany wiersz, dla raportu
    start: int         # indeks znaku w pliku
    end: int
    was: str
    now: str
    kind: str          # "operator" albo "prog"

    @property
    def id(self) -> str:
        return f"{self.path}:{self.line}:{self.start}"

    def describe(self) -> str:
        return f"{self.path}:{self.line} {self.kind} `{self.was}` -> `{self.now}`"

    def apply(self, source: str) -> str:
        assert source[self.start:self.end] == self.was, (
            f"{self.id}: w pliku stoi {source[self.start:self.end]!r}, "
            f"oczekiwano {self.was!r}")
        return source[:self.start] + self.now + source[self.end:]


def line_offsets(source: str) -> list[int]:
    """Indeks pierwszego znaku każdego wiersza; wiersz 1 pod indeksem 1."""
    offsets = [0, 0]
    for line in source.splitlines(keepends=True):
        offsets.append(offsets[-1] + len(line))
    return offsets


def char_index(source: str, offsets: list[int], lineno: int, col_offset: int) -> int:
    """Pozycja AST (wiersz, offset BAJTOWY) na indeks znaku w pliku.

    `col_offset` w module `ast` liczy **bajty UTF-8**, nie znaki. W pliku z polskimi
    komentarzami te dwie liczby się rozjeżdżają, a splice pod złym indeksem rozwaliłby
    kod tak, że nie skompilowałby się i mutacja wyszłaby „zabita" bez sprawdzenia
    czegokolwiek.
    """
    start = offsets[lineno]
    end = offsets[lineno + 1] if lineno + 1 < len(offsets) else len(source)
    line = source[start:end]
    prefix = line.encode("utf-8")[:col_offset].decode("utf-8", errors="strict")
    return start + len(prefix)


def mutations_for(path: str, source: str) -> list[Mutation]:
    """Mutacje dla jednego pliku, w ustalonej kolejności."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    offsets = line_offsets(source)
    rel = os.path.relpath(path, ROOT)
    found: list[Mutation] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Compare):
            continue

        operands = [node.left, *node.comparators]
        # `if __name__ == "__main__"` NIE jest bramką, tylko konwencją modułu.
        # Zamiana na `!=` sprawia, że moduł uruchamia swoje CLI przy imporcie i zabija
        # cały zestaw — co narzędzie liczyło jako „test wykrył mutację". Na 996 mutacji
        # takich strażników było 35, z czego 27 zaliczono jako zabite. Zawyżały pokrycie
        # i nie mówiły nic o tym, czy jakakolwiek bramka bramkuje.
        if any(isinstance(x, ast.Name) and x.id == "__name__" for x in operands):
            continue
        for index, op in enumerate(node.ops):
            left, right = operands[index], operands[index + 1]
            spec = OPERATORS.get(type(op))
            if spec is None:
                continue
            was, pattern, now = spec

            span_start = char_index(source, offsets, left.end_lineno, left.end_col_offset)
            span_end = char_index(source, offsets, right.lineno, right.col_offset)
            span = source[span_start:span_end]
            match = re.search(pattern, span)
            if match is None:
                # Zapis, którego nie umiemy zlokalizować (np. nawiasy albo komentarz
                # w środku). Pomijamy, zamiast zgadywać pozycję.
                continue

            at = span_start + match.start()
            found.append(Mutation(
                rel, source.count("\n", 0, at) + 1, at, at + len(was), was, now, "operator"))

        for operand in operands:
            if not isinstance(operand, ast.Constant):
                continue
            value = operand.value
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                continue

            at = char_index(source, offsets, operand.lineno, operand.col_offset)
            end = char_index(source, offsets, operand.end_lineno, operand.end_col_offset)
            text = source[at:end]
            if isinstance(value, int):
                replacement = repr(value + 1)
            else:
                # Przesunięcie względne, żeby próg 0,001 i próg 1000 dostały zmianę
                # tego samego rzędu co one same. Zero nie ma względnego sąsiedztwa,
                # więc dostaje wartość wprost.
                replacement = repr(value * 1.01 if value else 0.001)
            if replacement == text:
                continue

            found.append(Mutation(
                rel, operand.lineno, at, end, text, replacement, "prog"))

    found.sort(key=lambda m: (m.path, m.start))
    return found


def targets() -> list[str]:
    """Moduły pod mutację: kod narzędzi, bez samych testów."""
    out = []
    for base, _dirs, files in os.walk(os.path.join(ROOT, "tools")):
        if os.sep + "tests" in base or "__pycache__" in base:
            continue
        for name in sorted(files):
            if name.endswith(".py"):
                out.append(os.path.join(base, name))
    return sorted(out)


def unreachable_modules(paths) -> dict[str, str]:
    """Moduły, których zestaw testów NIE MOŻE zaimportować, z powodem.

    Bez tego narzędzie kłamie w najbardziej mylący sposób, jaki umie. Mutacja w module,
    którego `tools/tests/test_all.py` nie potrafi wczytać, **nie ma jak zostać zabita** —
    żaden test nigdy nie wykona ani jednej jej linii. Narzędzie liczyło ją dotąd jako
    „ocalałą", czyli tak samo jak prawdziwą dziurę w pokryciu bramki.

    Zmierzone na tym repozytorium: **138 mutacji siedzi w siedmiu modułach z `import bpy`
    i 135 z nich przeżywa — 98 %**. Cała reszta, czysty Python, ma 66 %. Te 135 pozycji
    zawyżało „nieprzetestowane bramki" o jedną trzecią i kierowało triaż na moduły,
    w których żaden test nie pomoże, dopóki nie wyjdzie z nich matematyka.

    Pytanie jest zadawane WYKONANIEM, nie grepem po `import bpy`: liczy się to, czy
    import się udaje w tym środowisku, a nie która biblioteka go blokuje. Świeży runner
    bez Blendera i maszyna z Blenderem dadzą przez to różne odpowiedzi — i to jest
    poprawne, bo pytanie brzmi „czy TEN zestaw testów może to wykonać".
    """
    out = {}
    for path in sorted(set(paths)):
        module = os.path.splitext(os.path.basename(path))[0]
        probe = subprocess.run(
            [sys.executable, "-c", f"import {module}"],
            cwd=os.path.dirname(path), capture_output=True, text=True, timeout=120)
        if probe.returncode == 0:
            continue
        reason = (probe.stderr or "").strip().splitlines()
        out[path] = reason[-1] if reason else f"kod wyjścia {probe.returncode}"
    return out


def collect() -> list[Mutation]:
    found: list[Mutation] = []
    for path in targets():
        with open(path, encoding="utf-8") as handle:
            found.extend(mutations_for(path, handle.read()))
    return found


# --- uruchamianie -----------------------------------------------------------------


# Zestaw kończy się linią „  N/M przeszło". Jej BRAK znaczy, że przebieg nie doszedł
# do końca — a to co innego niż „testy wykryły mutację".
SUMMARY = re.compile(r"^\s*(\d+)/(\d+) przeszło\s*$", re.MULTILINE)


def run_suite(worktree: str, timeout: int) -> tuple[bool | None, list[str], int | None]:
    """Zestaw testów w podanym drzewie.

    Zwraca `(werdykt, nazwy tych, co padły)`, gdzie werdykt to `True` (przeszedł,
    czyli mutacja PRZEŻYŁA), `False` (testy ją złapały) albo **`None` —
    nierozstrzygnięte**.

    Trzeci stan nie jest ozdobnikiem. Pierwszy przebieg tego narzędzia (02.09.2026)
    leciał, gdy kontener dławił się pamięcią; `test_all.py` bywał ubijany przez OOM,
    zwracał kod różny od zera i był czytany jako „test wykrył mutację". Kontrola
    wykazała, że **16 z 20 tak zaliczonych zabić** to w rzeczywistości mutacje ocalałe.
    Narzędzie do mierzenia pokrycia ZAWYŻAŁO pokrycie — kłamało w tę stronę, w którą
    najłatwiej uwierzyć.

    Dowodem, że przebieg doszedł do końca, jest linia podsumowania. Bez niej wynik
    jest nieznany i tak trafia do raportu, zamiast udawać zabicie.
    """
    try:
        done = subprocess.run(
            [sys.executable, os.path.join(worktree, "tools", "tests", "test_all.py")],
            cwd=worktree, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return None, ["<przekroczony czas>"], None

    summary = SUMMARY.search(done.stdout)
    if summary is None:
        # Zestaw nie wypisał podsumowania. Zapisujemy KOD WYJŚCIA, bo to jedyna rzecz,
        # która odróżnia przyczyny: ujemny kod albo 137/143 znaczy zabicie sygnałem
        # (najczęściej OOM), czyli coś, co z mutacją nie ma związku.
        #
        # Pierwsza wersja zapisywała tu ostatnią linię stderr jako „powód" i było to
        # mylące: zestaw NORMALNIE wypisuje na stderr błędy argparse z testów, które
        # sprawdzają, czy narzędzia odrzucają złe argumenty. Ostatnia linia stderr
        # opisywała więc test negatywny, a nie awarię.
        # Kod ujemny albo 137/143 znaczy zabicie sygnałem — najczęściej OOM. To jedyna
        # przyczyna, która NIE mówi nic o mutacji, więc tylko ona daje „nierozstrzygnięte".
        #
        # Każdy inny kod jest skutkiem mutacji i liczy się jako WYKRYCIE. Kod 2 to
        # `SystemExit` z argparse, które wychodzi poza `test_all.py`: zmutowany moduł
        # woła `parse_args()` w miejscu, w którym nie powinien, a zestaw ginie podczas
        # odkrywania testów. Sprawdzone na trzech mutacjach po dwa przebiegi — kod 2
        # za każdym razem. W CI taki przebieg jest czerwony, czyli mutacja jest złapana.
        if done.returncode < 0 or done.returncode in (137, 143):
            return None, [f"<zabity sygnałem, kod {done.returncode}>"], done.returncode
        return False, [f"<zestaw zginął przed podsumowaniem, kod {done.returncode}>"], done.returncode

    failed = re.findall(r"^\s*FAIL (\S+)", done.stdout, re.MULTILINE)
    passed, total = int(summary.group(1)), int(summary.group(2))
    if passed == total and done.returncode == 0:
        return True, failed, done.returncode
    return False, failed, done.returncode


def check_one(worktree: str, mutation: Mutation, timeout: int) -> dict:
    """Jedna mutacja w jednym drzewie roboczym, z przywróceniem pliku."""
    path = os.path.join(worktree, mutation.path)
    with open(path, encoding="utf-8") as handle:
        original = handle.read()

    try:
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(mutation.apply(original))
        passed, failed, code = run_suite(worktree, timeout)
    finally:
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(original)

    return {
        "id": mutation.id,
        "rozstrzygniete": passed is not None,
        "kod": code,
        "opis": mutation.describe(),
        "plik": mutation.path,
        "wiersz": mutation.line,
        "rodzaj": mutation.kind,
        "bylo": mutation.was,
        "jest": mutation.now,
        "przezyla": bool(passed),
        "padly": failed[:5],
        "ile_padlo": len(failed),
    }


def worker(slot: int, chunk: list[Mutation], timeout: int, out_dir: str,
           journal: str) -> int:
    """Jeden robotnik na własnym drzewie roboczym git.

    Wynik KAŻDEJ mutacji leci od razu do dziennika, wiersz po wierszu. Pierwsza wersja
    zapisywała dopiero po całej porcji — i gdy przebieg padł po siedemdziesięciu
    minutach, nie zostało ani jedno z ponad sześciuset sprawdzeń. Przebieg trwający
    godzinę musi znosić śmierć procesu, bo jej doświadczy.
    """
    worktree = os.path.join(out_dir, f"wt{slot}")
    subprocess.run(
        ["git", "worktree", "add", "--detach", "--quiet", worktree, "HEAD"],
        cwd=ROOT, check=True, capture_output=True)

    # Testy SAMEGO narzędzia lecą z drzewa roboczego. Mierzą narzędzie, nie kod pod
    # testem, a przy tym dominują czas: `test_every_mutation_still_parses` parsuje
    # wszystkie ~1000 mutacji w KAŻDYM z setek przebiegów. Zostawione podniosły koszt
    # przeglądu z 66 do 120 minut, nie mówiąc przy tym nic o pokryciu bramek.
    own = os.path.join(worktree, "tools", "tests", "test_mutation_sweep.py")
    if os.path.isfile(own):
        os.remove(own)

    done = 0
    try:
        for mutation in chunk:
            entry = check_one(worktree, mutation, timeout)
            with JOURNAL_LOCK:
                with open(journal, "a", encoding="utf-8") as handle:
                    handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
                    handle.flush()
                    os.fsync(handle.fileno())
            done += 1
    finally:
        subprocess.run(["git", "worktree", "remove", "--force", worktree],
                       cwd=ROOT, capture_output=True)
    return done


def read_journal(path: str) -> list[dict]:
    """Wyniki z dziennika; wiersz ucięty w połowie zapisu jest pomijany."""
    if not os.path.isfile(path):
        return []
    out = []
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def sweep(mutations: list[Mutation], workers: int, timeout: int, out_dir: str,
          journal: str) -> list[dict]:
    os.makedirs(out_dir, exist_ok=True)
    chunks: list[list[Mutation]] = [[] for _ in range(workers)]
    for index, mutation in enumerate(mutations):
        chunks[index % workers].append(mutation)

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(worker, slot, chunk, timeout, out_dir, journal)
                   for slot, chunk in enumerate(chunks) if chunk]
        for future in concurrent.futures.as_completed(futures):
            future.result()

    results = read_journal(journal)
    results.sort(key=lambda r: (r["plik"], r["wiersz"]))
    return results


def report(results: list[dict], commit: str) -> str:
    # Starsze dzienniki nie mają pola `rozstrzygniete`; brak pola traktujemy jako
    # „rozstrzygnięte", żeby raport z nich nadal się składał.
    unknown = [r for r in results if not r.get("rozstrzygniete", True)]
    decided = [r for r in results if r.get("rozstrzygniete", True)]
    survived = [r for r in decided if r["przezyla"]]
    killed = len(decided) - len(survived)
    by_file: dict[str, list[dict]] = {}
    for entry in survived:
        by_file.setdefault(entry["plik"], []).append(entry)

    lines = [
        "# Przegląd mutacyjny bramek",
        "",
        f"**Snapshot na commicie:** `{commit}`",
        "",
        "Narzędzie: `tools/tests/mutation_sweep.py`. Mutowany jest **kod pod testem**,",
        "nie testy. Mutacja, która przeżyła, znaczy jedno z dwojga: brak pokrycia albo",
        "mutant równoważny — zmiana, której nie da się zaobserwować. Narzędzie nie zgaduje,",
        "które to; każdą trzeba obejrzeć.",
        "",
        "## Wynik",
        "",
        "| | |",
        "|---|---|",
        f"| mutacji | {len(results)} |",
        f"| rozstrzygniętych | {len(decided)} |",
        f"| zabitych | {killed} |",
        f"| **ocalałych** | **{len(survived)}** |",
        f"| **nierozstrzygniętych** | **{len(unknown)}** |",
        ("| pokrycie (z rozstrzygniętych) | "
         f"{killed / len(decided) * 100:.1f} % |") if decided else "| pokrycie | — |",
        "",
        "**Nierozstrzygnięta** znaczy, że przebieg testów nie doszedł do końca — ubity,",
        "bez pamięci, błąd poza samą mutacją. Taki wynik NIE liczy się jako zabicie.",
        "Pierwsza wersja tego narzędzia liczyła go właśnie tak i przez to zawyżała",
        'pokrycie: kontrola wykazała, że 16 z 20 „zabić” z przebiegu pod presją pamięci',
        "to w rzeczywistości mutacje ocalałe.",
        "",
    ]

    if not survived:
        lines += ["Żadna mutacja nie przeżyła.", ""]
        return "\n".join(lines)

    lines += [
        "## Jak czytać ocalałe",
        "",
        "Ocalała mutacja **nie jest** automatycznie usterką. Trzeba ją zakwalifikować",
        "do jednej z trzech klas, a narzędzie tego nie zrobi za czytającego:",
        "",
        "| klasa | co znaczy | co z tym zrobić |",
        "|---|---|---|",
        "| **realna dziura** | zmiana zmienia zachowanie, które ktoś kiedyś zobaczy, "
        "a żaden test tego nie sprawdza | dopisać test z kontrolą negatywną |",
        "| **mutant równoważny** | zmiany nie da się zaobserwować (np. tolerancja "
        "`1e-12` przesunięta o procent) | zapisać jako równoważną, nie „naprawiać” |",
        "| **remis bez znaczenia** | `<` kontra `<=` przy wyborze minimum: przy remisie "
        "obie gałęzie dają tę samą wartość | jak wyżej, chyba że liczy się INDEKS |",
        "",
        "Rozróżnienie wymaga przeczytania kodu. Wpisanie mutanta równoważnego jako",
        "usterki zawyża znalezisko dokładnie tak samo, jak liczenie zepsutego przebiegu",
        "jako zabicia zawyżało pokrycie.",
        "",
        "**Kolejność triażu:** od pliku o najwyższym UDZIALE ocalałych, nie od pliku",
        "o największej ich liczbie. Wysoki udział znaczy, że testy tego modułu sprawdzają",
        "co innego, niż deklarują; duża liczba przy niskim udziale znaczy tylko, że moduł",
        "jest duży.",
        "",
        "## Ocalałe, per plik",
        "",
    ]
    for path in sorted(by_file):
        lines += [f"### `{path}` — {len(by_file[path])}", "",
                  "| wiersz | rodzaj | było | jest |", "|---|---|---|---|"]
        for entry in by_file[path]:
            lines.append(
                f"| {entry['wiersz']} | {entry['rodzaj']} | `{entry['bylo']}` | `{entry['jest']}` |")
        lines.append("")

    return "\n".join(lines)


def dirty_sources(paths) -> list[str]:
    """Które z podanych plików różnią się między drzewem roboczym a `HEAD`.

    Istnieje po to, żeby przebieg przerwał się w pierwszej sekundzie, a nie w piętnastej
    minucie. Mutacje powstają z pliku w DRZEWIE ROBOCZYM — z jego przesunięciami bajtowymi
    — a wykonywane są w kopii z `HEAD` (`run_worker`). Gdy plik jest zmieniony i
    niezacommitowany, te dwa źródła to dwa różne pliki i mutacja trafia w inne miejsce,
    niż myśli.

    Zdarzyło się przy triażu `lod.py`: dopisany komentarz przesunął ofsety i przebieg padł
    po 88 mutacjach na `AssertionError` mówiącym, że „w pliku stoi 'ł', oczekiwano '<'".
    Strażnik wklejki zadziałał — nikt nie policzył złych wyników — ale kosztowało to
    piętnaście minut maszyny i minutę zastanawiania się, skąd tam polska litera.

    Pyta o KONKRETNE mutowane pliki, a nie o czystość całego repozytorium: dopisywanie
    testów w tej samej sesji jest normalne i nie ma powodu, żeby blokowało przegląd.
    """
    wanted = sorted(set(paths))
    if not wanted:
        return []
    changed = subprocess.run(
        ["git", "diff", "--name-only", "HEAD", "--"] + wanted,
        cwd=ROOT, capture_output=True, text=True)
    if changed.returncode != 0:
        return []
    return [line for line in changed.stdout.splitlines() if line]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--limit", type=int, default=0,
                        help="tylko pierwsze N mutacji; 0 = wszystkie")
    parser.add_argument("--only", default="", help="mutuj wyłącznie pliki z tym fragmentem ścieżki")
    parser.add_argument("--journal", default="",
                        help="dziennik JSONL: każdy wynik dopisywany od razu. Wznowienie "
                             "pomija to, co już w nim jest. Bez tego przerwany przebieg "
                             "traci wszystko")
    parser.add_argument("--json", default="", help="zapisz surowe wyniki tutaj")
    parser.add_argument("--out", default="", help="zapisz raport markdown tutaj")
    parser.add_argument("--list", action="store_true", help="wypisz mutacje i wyjdź")
    parser.add_argument("--include-unreachable", action="store_true",
                        help="mutuj także moduły, których zestaw testów nie potrafi "
                             "zaimportować. Ich mutacje policzą się jako ocalałe, choć "
                             "nie mają jak zostać zabite — patrz `unreachable_modules`")
    parser.add_argument("--dirty", action="store_true",
                        help="nie przerywaj, gdy mutowane pliki mają niezacommitowane "
                             "zmiany. Wyniki będą wtedy liczone dla innego pliku niż ten "
                             "w drzewie roboczym")
    args = parser.parse_args()

    found = collect()
    journal = args.journal or os.path.join(tempfile.gettempdir(), "metro-mutacje.jsonl")
    done = read_journal(journal)
    if done:
        # Wznowienie liczy tylko to, czego jeszcze nie ma — ale WYŁĄCZNIE dla mutacji
        # o tym samym identyfikatorze, więc zmiana kodu między przebiegami nie przemyci
        # starego wyniku pod nową mutację.
        seen = {entry["id"] for entry in done}
        before = len(found)
        found = [m for m in found if m.id not in seen]
        print(f"[MUTACJE] wznowienie z {journal}: {before - len(found)} z {before} "
              "już policzonych")

    if args.only:
        found = [m for m in found if args.only in m.path]
    if args.limit:
        found = found[:args.limit]

    if args.list:
        for mutation in found:
            print(mutation.describe())
        print(f"razem: {len(found)}")
        return 0

    if not found and not done:
        print("brak mutacji do sprawdzenia", file=sys.stderr)
        return 1

    dirty = dirty_sources(m.path for m in found)
    if dirty and not args.dirty:
        print("[MUTACJE] przerwane: mutowane pliki mają niezacommitowane zmiany:",
              file=sys.stderr)
        for path in dirty:
            print(f"    {path}", file=sys.stderr)
        print(
            "\n  Mutacje są liczone z DRZEWA ROBOCZEGO, a robotnicy pracują na kopii\n"
            "  `git worktree add --detach HEAD`. Gdy te dwa źródła się różnią, przesunięcia\n"
            "  bajtowe mutacji nie pasują do pliku, na którym mają być wykonane. Strażnik\n"
            "  wklejki to wyłapie, ale dopiero po kilkunastu minutach liczenia i w postaci\n"
            "  AssertionError o nieoczywistej treści.\n\n"
            "  Zacommituj zmiany albo uruchom z --dirty, jeśli wiesz, że robisz co innego.",
            file=sys.stderr)
        return 2

    unreachable = unreachable_modules(m.path for m in found)
    if unreachable:
        blocked = [m for m in found if m.path in unreachable]
        print(f"[MUTACJE] {len(blocked)} mutacji w {len(unreachable)} modułach, których "
              "zestaw testów nie potrafi zaimportować — nie mają jak zostać zabite:",
              file=sys.stderr)
        for path, reason in unreachable.items():
            count = sum(1 for m in blocked if m.path == path)
            print(f"    {path} ({count}): {reason[:80]}", file=sys.stderr)
        if not args.include_unreachable:
            found = [m for m in found if m.path not in unreachable]
            print("[MUTACJE] pominięte; --include-unreachable liczy je razem z resztą",
                  file=sys.stderr)

    if not found:
        print("brak mutacji do sprawdzenia po odfiltrowaniu nieosiągalnych", file=sys.stderr)
        return 1

    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
                            capture_output=True, text=True).stdout.strip()
    print(f"[MUTACJE] {len(found)} mutacji do policzenia, {args.workers} robotników, "
          f"commit {commit}, dziennik {journal}")

    with tempfile.TemporaryDirectory(prefix="metro-mutacje-") as work:
        results = sweep(found, args.workers, args.timeout, work, journal)

    decided = [r for r in results if r.get("rozstrzygniete", True)]
    survived = [r for r in decided if r["przezyla"]]
    unknown = len(results) - len(decided)
    print(f"[MUTACJE] rozstrzygniętych {len(decided)}/{len(results)}, "
          f"zabitych {len(decided) - len(survived)}, ocalałych {len(survived)}, "
          f"nierozstrzygniętych {unknown}")
    for entry in survived:
        print(f"  OCALAŁA  {entry['opis']}")

    if args.json:
        with open(args.json, "w", encoding="utf-8") as handle:
            json.dump(results, handle, ensure_ascii=False, indent=1)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as handle:
            handle.write(report(results, commit))
        print(f"[MUTACJE] raport -> {args.out}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
