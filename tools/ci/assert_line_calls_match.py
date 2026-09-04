#!/usr/bin/env python3
"""Przejazd linią: scena Godota i rdzeń muszą wywołać TE SAME stacje.

Bramka porównuje dwa pliki `--calls` — jeden z `Sim.Runner line`, drugi ze sceny
uruchomionej z `--line`. Porównanie idzie po ZATRZYMANIACH, nie po kodzie wyjścia:
dwa przebiegi kończące się zerem mogą różnić się liczbą obsłużonych stacji, czasem
przyjazdu albo błędem zatrzymania, a z kodu wyjścia tego nie widać.

PRÓG JEST ZEROWY. Oba przebiegi liczy ten sam `LineDrive` na tym samym kroku stałym,
więc każda różnica jest różnicą w tym, JAK scena go woła, a nie w fizyce — i nie ma
tolerancji, w której warto ją schować.

    python3 tools/ci/assert_line_calls_match.py RDZEN.csv SCENA.csv [--expect-calls N]
"""

import argparse
import csv
import sys

#: Kolumny porównywane co do bitu. `name` i `stop_id` sprawdzane osobno, jako napisy.
NUMERIC_COLUMNS = (
    "chainage_m", "stopped_at_m", "stop_error_m", "arrival_s", "departure_s",
)


def load(path):
    with open(path, newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def compare(core_rows, scene_rows, expect_calls=None):
    """Lista problemów; pusta znaczy „zgodne". Czysta funkcja, więc da się ją przetestować."""
    problems = []
    if len(core_rows) != len(scene_rows):
        problems.append(
            f"rdzeń {len(core_rows)} zatrzymań, scena {len(scene_rows)}")
        return problems

    if expect_calls is not None and len(core_rows) != expect_calls:
        problems.append(
            f"oczekiwano {expect_calls} zatrzymań, jest {len(core_rows)}")

    if not core_rows:
        problems.append("zero zatrzymań — przejazd bez ani jednej stacji nie jest przejazdem linią")
        return problems

    worst = {column: 0.0 for column in NUMERIC_COLUMNS}
    for core, scene in zip(core_rows, scene_rows):
        for column in ("name", "stop_id"):
            if core[column] != scene[column]:
                problems.append(
                    f"{column}: rdzeń {core[column]!r}, scena {scene[column]!r}")
        for column in NUMERIC_COLUMNS:
            delta = abs(float(core[column]) - float(scene[column]))
            worst[column] = max(worst[column], delta)

    for column in NUMERIC_COLUMNS:
        print(f"[LINIA] {column:<14} max |Δ| = {worst[column]:.3E}")
        if worst[column] != 0.0:
            problems.append(f"{column}: max |Δ| = {worst[column]:.3E}, a próg jest ZEROWY")

    return problems


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("core", help="zatrzymania z Sim.Runner line --calls")
    parser.add_argument("scene", help="zatrzymania ze sceny --line --calls")
    parser.add_argument("--expect-calls", type=int, default=None,
                        help="ile zatrzymań ma być; pakiet A ma 12 stacji, czyli 11 wywołań")
    args = parser.parse_args(argv)

    problems = compare(load(args.core), load(args.scene), args.expect_calls)
    if problems:
        for problem in problems:
            print(f"BŁĄD: {problem}", file=sys.stderr)
        return 1

    print(f"[LINIA] scena i rdzeń: {len(load(args.core))} zatrzymań, "
          "wszystkie kolumny identyczne")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
