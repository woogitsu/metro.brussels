#!/usr/bin/env python3
"""Bramka: koszt kroku `LineCore.Step` przy dziewięciu składach nie przekroczył progu.

**Po co.** `reports/linecore-budget.md` zmierzył koszt kroku raz, 05.09.2026, i na tym
się skończyło. Pomiar wykonany raz mówi o dniu, w którym go wykonano; regres wydajności
rdzenia wyszedłby dopiero wtedy, gdy ktoś zechciałby go powtórzyć.

**Czego ta bramka pilnuje NAPRAWDĘ — i dlaczego to nie jest oczywiste.** Nie samej
liczby mikrosekund. Pilnuje też, że pomiar dotyczy **dziewięciu składów na planie**,
a nie jednego. 6.A12 (#308) zmierzyła, że `budget --trains 32` melduje `N_max = 1`,
kiedy okno pomiaru jest krótsze niż jeden odstęp — a wtedy kolumna µs/krok nadal ma
wartość, tylko opisuje zupełnie inny przejazd. Bramka, która czyta wyłącznie µs,
przechodziłaby wtedy na zielono z pomiarem jednego składu i nazywała go dziewięcioma.
Dlatego `trains_on_line_expected` jest warunkiem **twardym**, nie ozdobą raportu.

**Czego ta bramka NIE mierzy, świadomie.** Przejazdu z wybiegiem: `budget` nie zna
`--coast-from-m` (pozycja 6.A18), więc mierzony jest przejazd **bez wybiegu**. To jest
powiedziane tutaj, w wypisie i w raporcie, zamiast milcząco mierzyć jeden wariant
i nazywać go „kosztem kroku". Nie mierzy też progu klatki z ekstrapolacji `N ≈ 330–390`
— `reports/linecore-budget.md` §7 mówi wprost, że to ekstrapolacja 56–65× poza zakres
pomiaru, więc nie jest materiałem na bramkę.

Próg i scenariusz stoją w `tools/ci/linecore-step-budget.json`, w jednym miejscu.
"""
import argparse
import json
import os
import re
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CONFIG = os.path.join(ROOT, "tools", "ci", "linecore-step-budget.json")

#: Wiersz pomiaru z `Sim.Runner budget`. Kolumny, w kolejności:
#: N_zgł;N_max;N_śr;czeka_śr;mediana_kroków_s;min;max;rozstęp_%;µs_krok;CPU/ścienny;%budżetu
ROW = re.compile(r"^\[BUDŻET\] (\d+);(\d+);([\d.]+);([\d.]+);(\d+);(\d+);(\d+);([\d.]+);([\d.]+);([\d.]+);([\d.]+)\s*$")


def load_config(path=CONFIG):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def parse(output):
    """Wiersze pomiaru z wyjścia `budget` — jako słowniki, w kolejności wystąpienia."""
    rows = []
    for line in output.splitlines():
        match = ROW.match(line.strip())
        if match:
            rows.append({
                "declared": int(match.group(1)),
                "on_line_max": int(match.group(2)),
                "on_line_mean": float(match.group(3)),
                "waiting_mean": float(match.group(4)),
                "spread_pct": float(match.group(8)),
                "us_per_step": float(match.group(9)),
                "frame_budget_pct": float(match.group(11)),
            })
    return rows


def command(config, project="src/Sim.Runner"):
    """Wywołanie `budget` odtwarzające scenariusz z pliku progu."""
    s = config["scenario"]
    return [
        "dotnet", "run", "--project", project, "--configuration", "Release",
        "--no-build", "--", "budget",
        "--axis", s["axis"],
        "--signalling", s["signalling"],
        "--limit-kmh", str(s["limit_kmh"]),
        "--exchange-s", str(s["exchange_s"]),
        "--headway-s", str(s["headway_s"]),
        "--turnback-s", str(s["turnback_s"]),
        "--steps", str(s["steps"]),
        "--warmup", str(s["warmup"]),
        "--repeats", str(s["repeats"]),
        "--trains", str(s["trains_declared"]),
    ]


def verdict(config, output):
    """`(ok, komunikaty)` — pusta lista zarzutów znaczy zielono."""
    rows = parse(output)
    problems = []
    if not rows:
        return False, ["wyjście `budget` nie ma ani jednego wiersza pomiaru"]
    if len(rows) != 1:
        problems.append(
            "scenariusz ma dawać JEDEN wiersz pomiaru, a dał %d — próg dotyczy "
            "jednej obsady, nie średniej z kilku" % len(rows))
    row = rows[0]
    expected = config["trains_on_line_expected"]
    if row["on_line_max"] != expected:
        problems.append(
            "na planie było %d składów, a próg jest ustawiony na %d. Pomiar dotyczy "
            "INNEGO przejazdu niż ten, o którym mówi próg — najczęstsza przyczyna to "
            "okno krótsze niz (N-1) x odstep (6.A12)"
            % (row["on_line_max"], expected))
    limit = config["microseconds_per_step_max"]
    if row["us_per_step"] > limit:
        problems.append(
            "koszt kroku %.3f us przekracza prog %.3f us" % (row["us_per_step"], limit))
    frame = config["frame_budget_pct_max"]
    if row["frame_budget_pct"] > frame:
        problems.append(
            "krok zajmuje %.3f %% budzetu klatki przy progu %.3f %%"
            % (row["frame_budget_pct"], frame))
    return not problems, problems


def describe(config, output):
    rows = parse(output)
    if not rows:
        return "brak wiersza pomiaru"
    row = rows[0]
    return (
        "zgloszonych %d, na planie %d (srednio %.2f, czeka %.2f); "
        "%.3f us/krok przy progu %.3f; %.3f %% budzetu klatki; rozstep powtorzen %.1f %%"
        % (row["declared"], row["on_line_max"], row["on_line_mean"], row["waiting_mean"],
           row["us_per_step"], config["microseconds_per_step_max"],
           row["frame_budget_pct"], row["spread_pct"]))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--config", default=CONFIG)
    parser.add_argument(
        "--from-output", default=None,
        help="plik z gotowym wyjsciem `budget` zamiast uruchamiania go "
             "(uzywane przez kontrole negatywna i przez testy bez .NET)")
    parser.add_argument("--project", default="src/Sim.Runner")
    arguments = parser.parse_args(argv)

    config = load_config(arguments.config)
    if arguments.from_output:
        with open(arguments.from_output, encoding="utf-8") as handle:
            output = handle.read()
    else:
        run = subprocess.run(command(config, arguments.project), cwd=ROOT,
                             capture_output=True, text=True)
        output = run.stdout
        if run.returncode != 0:
            sys.stderr.write(run.stderr)
            sys.stderr.write("BLAD: `budget` skonczyl sie kodem %d\n" % run.returncode)
            return 1

    print("[BUDZET-BRAMKA] " + describe(config, output))
    print("[BUDZET-BRAMKA] mierzony jest przejazd BEZ wybiegu: `budget` nie zna "
          "--coast-from-m (6.A18)")
    ok, problems = verdict(config, output)
    for problem in problems:
        sys.stderr.write("BLAD: " + problem + "\n")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
