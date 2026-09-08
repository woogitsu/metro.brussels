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

**Czego ta bramka NIE mierzy, świadomie.** Przejazdu z wybiegiem — i od 6.A18 jest to
**wybór, a nie brak możliwości**; poprzednia wersja tego akapitu mówiła, że `budget` nie
zna `--coast-from-m`, i to już nieprawda, dlatego jest tu przepisana, a nie dopisana obok.
Nastawa stoi w scenariuszu jako `coast_from_m: null` i stamtąd bierze ją zarówno
wywołanie, jak i zdanie w wypisie, więc jej włączenie nie wymaga tknięcia tego pliku.
`null` zostaje celowo: próg 8,0 µs zmierzono na przejeździe **bez** wybiegu, a wybieg
zmienia przejazd, nie tylko jego koszt — pomiar z wybiegiem porównywałby się z progiem
wziętym z innego przejazdu. To jest powiedziane tutaj, w wypisie i w raporcie, zamiast
milcząco mierzyć jeden wariant i nazywać go „kosztem kroku". Nie mierzy też progu klatki z ekstrapolacji `N ≈ 330–390`
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
    ] + ([] if s.get("coast_from_m") is None
         else ["--coast-from-m", str(s["coast_from_m"])])


#: Kod wyjścia dla przekroczonego progu. Zachowany bez zmian — CI i kontrola negatywna
#: sprawdzają, że bramka „potrafi zaczerwienić", i ten kod jest tym, co widzą.
KOD_PRZEKROCZONY = 1

#: Kod wyjścia dla pomiaru, którego NIE DA SIĘ porównać z progiem. Osobny od
#: `KOD_PRZEKROCZONY`, bo to dwa różne zdania o dwóch różnych rzeczach, a do 07.09.2026
#: bramka mówiła oba tym samym kodem i tym samym komunikatem.
KOD_NIEMIERZALNY = 3


def niemierzalny(config, row):
    """Powód, dla którego tego pomiaru nie wolno porównać z progiem — albo `None`.

    **Skąd to się wzięło.** Zmierzone 07.09.2026 na runnerze `woogitsu-host-08`, gdy
    dwanaście jobów liczyło naraz:

        BLAD: koszt kroku 16.022 us przekracza prog 8.000 us
        [BUDZET-BRAMKA] ... 16.022 us/krok przy progu 8.000; rozstep powtorzen 115.9 %

    Na tej samej treści kodu, na maszynie niezajętej, cztery przebiegi dały
    **4,213–4,364 µs przy rozstępie 1,9–3,7 %**. Kod nie zwolnił czterokrotnie —
    maszyna nie dała się zmierzyć.

    **A bramka powiedziała, że kod jest za wolny.** Kolumna `rozstęp_%` była
    **parsowana i wypisywana, ale nie asertowana**: bramka znała liczbę mówiącą, że jej
    własny pomiar jest niestabilny, i porównywała go z progiem mimo to. Dwa różne stany
    świata — „rdzeń zwolnił" i „nie umiem tego zmierzyć" — dawały jeden komunikat
    i jeden kod wyjścia, a pierwszy z nich każe szukać regresu w kodzie, którego nie ma.

    Zwrócony powód **wstrzymuje porównanie**, a nie tylko dokłada zdanie: porównanie
    wykonane na niestabilnym pomiarze jest właśnie tym fałszem, którego ta funkcja ma
    nie dopuścić.
    """
    limit = config["spread_pct_max"]
    if row["spread_pct"] <= limit:
        return None
    return ("rozstep powtorzen %.1f %% przekracza granice %.1f %%, wiec koszt kroku "
            "%.3f us NIE JEST porownywany z progiem %.3f us — ten pomiar nie mowi nic "
            "o kodzie, tylko o maszynie, na ktorej go zrobiono"
            % (row["spread_pct"], limit, row["us_per_step"],
               config["microseconds_per_step_max"]))


def verdict(config, output):
    """`(ok, komunikaty)` — pusta lista zarzutów znaczy zielono.

    Warunki OBSADY i kształtu wyjścia sprawdzane są zawsze; warunki CZASU wyłącznie
    wtedy, gdy `niemierzalny` zwróci `None`. Rozdział jest zamierzony: liczba składów
    na planie nie zależy od obciążenia maszyny, a koszt kroku zależy.
    """
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
    powod = niemierzalny(config, row)
    if powod:
        problems.append(powod)
    else:
        limit = config["microseconds_per_step_max"]
        if row["us_per_step"] > limit:
            problems.append(
                "koszt kroku %.3f us przekracza prog %.3f us"
                % (row["us_per_step"], limit))
        frame = config["frame_budget_pct_max"]
        if row["frame_budget_pct"] > frame:
            problems.append(
                "krok zajmuje %.3f %% budzetu klatki przy progu %.3f %%"
                % (row["frame_budget_pct"], frame))
    return not problems, problems


def coasting(config):
    """Zdanie o wybiegu — wyprowadzone ze scenariusza, nie wpisane z reki.

    Do 6.A18 stalo tu zdanie na sztywno: „budget nie zna --coast-from-m". Bylo prawdziwe
    w dniu, w ktorym je napisano, i przestaloby byc prawdziwe po cichu — bo nic nie
    laczylo go z tym, co bramka NAPRAWDE uruchamia. Teraz laczy: obie strony czytaja
    `scenario.coast_from_m`, wiec zdanie nie moze sie rozjechac z wywolaniem.
    """
    coast = config["scenario"].get("coast_from_m")
    if coast is None:
        return ("mierzony jest przejazd BEZ wybiegu — scenariusz ma coast_from_m: null; "
                "od 6.A18 `budget` zna --coast-from-m, wiec to jest wybor, nie brak")
    return ("mierzony jest przejazd Z WYBIEGIEM od %s m odcinka — prog musi pochodzic "
            "z tego samego wariantu przejazdu" % coast)


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
    print("[BUDZET-BRAMKA] " + coasting(config))
    ok, problems = verdict(config, output)
    for problem in problems:
        sys.stderr.write("BLAD: " + problem + "\n")
    if ok:
        return 0
    # Kod niemierzalności należy się WYŁĄCZNIE wtedy, gdy jest to jedyny zarzut.
    # Pomiar niestabilny, który przy okazji mierzy jeden skład zamiast dziewięciu, jest
    # nadal usterką scenariusza i musi wychodzić kodem 1 — inaczej „nie umiem zmierzyć"
    # przesłoniłoby zarzut, który od obciążenia maszyny nie zależy wcale.
    rows = parse(output)
    if len(problems) == 1 and rows and niemierzalny(config, rows[0]):
        return KOD_NIEMIERZALNY
    return KOD_PRZEKROCZONY


if __name__ == "__main__":
    raise SystemExit(main())
