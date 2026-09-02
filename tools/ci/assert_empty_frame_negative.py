#!/usr/bin/env python3
"""Sprawdza, że negatyw kontroli zrzutów wywrócił się z właściwego powodu.

Kontrola negatywna w `godot-first-run.yml` renderuje klatkę bez geometrii
i oczekuje, że `tools/visual/compare.py` ją odrzuci. Do 2026-09 wystarczał
sam niezerowy kod wyjścia — a ten brał się z czegoś innego, niż deklarowała
nazwa kroku: `--no-geometry` nie ładuje tunelu, więc `FirstRun.cs` nie
zapisuje `GODOT_metadata.json` i compare.py przerywał na „brak metadanych
bieżącego przebiegu". Progi pustej klatki nie były w ogóle sprawdzane.

Ten skrypt czyta raport JSON i wymaga, żeby KAŻDA klatka miała status
`fail` z powodem o pustym obrazie, a geometria nie była tym, co wywróciło
przebieg.
"""
import json
import sys

EMPTY = "obraz pusty/jednorodny"


def check(path):
    with open(path, encoding="utf-8") as handle:
        report = json.load(handle)
    problems = []
    images = report.get("images") or []
    if not images:
        problems.append("raport nie zawiera ani jednej klatki")
    for entry in images:
        if entry.get("status") != "fail" or EMPTY not in (entry.get("reason") or ""):
            problems.append(f"{entry.get('camera')}: {entry.get('status')} "
                            f"<- {entry.get('reason')}")
    geometry = report.get("geometry") or {}
    if geometry.get("status") == "fail":
        problems.append("negatyw wywrócił się na geometrii, a miał na zawartości klatki: "
                        + str(geometry.get("reason")))
    if problems:
        print("BŁĄD: negatyw nie dowodzi tego, co deklaruje:", file=sys.stderr)
        for line in problems:
            print(f"  {line}", file=sys.stderr)
        return 1
    print(f"[NEGATYW] {len(images)} klatek odrzuconych jako puste, "
          f"geometria: {geometry.get('status')}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("użycie: assert_empty_frame_negative.py <raport.json>", file=sys.stderr)
        sys.exit(2)
    sys.exit(check(sys.argv[1]))
