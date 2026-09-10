#!/usr/bin/env python3
"""Sklejenie zapisu czasu przebiegu: moduły z zestawu, maszyna z powłoki.

**Po co (6.D93).** `tools/tests/test_all.py` wypisuje „czas per moduł (malejąco)"
przy każdym przebiegu, a `python-tests.yml` nie miał **ani jednego** kroku
`upload-artifact`. Trend czasu istniał więc wyłącznie w logu pojedynczego przebiegu,
a lista `POMIARY` w `test_suite_runtime_budget.py` jest utrzymywana ręcznie i rośnie
tylko wtedy, gdy ktoś o niej pamięta.

**Dlaczego sklejenie, a nie jeden pisarz.** Dwie liczby mierzy się w dwóch różnych
miejscach i żadnego z nich nie da się przenieść do drugiego bez straty:

- czasy modułów zna WYŁĄCZNIE proces zestawu, bo mierzy je wokół każdego testu;
- czas CPU zna WYŁĄCZNIE powłoka, przez wbudowane `times` wokół całego procesu.
  Interesuje nas CPU **dzieci**, a nie tego interpretera, i `times` w podstawieniu
  poleceń zwraca zera — zmierzone przy 6.D42, nie założone.

Ten skrypt bierze jedno i drugie i zapisuje artefakt. Sam niczego nie mierzy.

**Stosunek CPU/ściana jest liczony tutaj, a nie zostawiony czytającemu**, bo to on
mówi, czy czas ściany w ogóle wolno z czymkolwiek porównywać (6.D42, podłoga
`MIERZALNOSC_MIN`). Artefakt bez tej liczby zapraszałby do zestawiania przebiegu
z maszyny spokojnej z przebiegiem z maszyny obciążonej — a to jest dokładnie ten
błąd, przed którym 6.D42 postawiło podłogę.

**Kod wyjścia**: 0, gdy artefakt powstał; 1 przy braku wejścia albo złych liczbach.
Krok CI woła ten skrypt PO zakończeniu zestawu, więc jego kod wyjścia nie ma prawa
zamienić spowolnienia maszyny w porażkę testów — o tym decyduje osobny werdykt
`test_suite_runtime_budget.werdykt`, tak samo jak przed tą pozycją.
"""
import argparse
import json
import os
import sys


def scal(dane, wall_s, cpu_s, runner="", commit=""):
    """Zapis modułów wzbogacony o pomiar maszyny. Nie zmienia wpisów modułów."""
    if wall_s <= 0:
        raise ValueError(f"czas ściany ma być dodatni, jest {wall_s}")
    if cpu_s < 0:
        raise ValueError(f"czas CPU nie może być ujemny, jest {cpu_s}")
    out = dict(dane)
    out["wall_powloki_s"] = round(wall_s, 3)
    out["cpu_s"] = round(cpu_s, 3)
    out["cpu_na_sciane"] = round(cpu_s / wall_s, 3)
    # Zestaw czyta `GITHUB_SHA` i `RUNNER_NAME` sam, ale gdy ich nie widział —
    # a nie widzi ich przy przebiegu lokalnym — wolno je podać tutaj. Wartość
    # niepusta z zestawu ma pierwszeństwo, żeby dwa źródła nie mogły się rozjechać
    # po cichu w stronę tego, które akurat wołano później.
    if commit and not out.get("commit"):
        out["commit"] = commit
    if runner and not out.get("runner"):
        out["runner"] = runner
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--in", dest="wejscie", required=True,
                    help="JSON zapisany przez test_all.py (METRO_TIMING_OUT)")
    ap.add_argument("--out", dest="wyjscie", required=True)
    ap.add_argument("--wall", type=float, required=True, help="czas ściany z powłoki, s")
    ap.add_argument("--cpu", type=float, required=True, help="czas CPU dzieci, s")
    ap.add_argument("--runner", default=os.environ.get("RUNNER_NAME", ""))
    ap.add_argument("--commit", default=os.environ.get("GITHUB_SHA", ""))
    a = ap.parse_args(argv)

    if not os.path.isfile(a.wejscie):
        print(f"BRAK: {a.wejscie} — zestaw nie zapisał czasów; czy krok ustawił "
              "METRO_TIMING_OUT?", file=sys.stderr)
        return 1
    with open(a.wejscie, encoding="utf-8") as uchwyt:
        dane = json.load(uchwyt)
    try:
        scalone = scal(dane, a.wall, a.cpu, runner=a.runner, commit=a.commit)
    except ValueError as e:
        print(f"ODMOWA: {e}", file=sys.stderr)
        return 1
    with open(a.wyjscie, "w", encoding="utf-8") as uchwyt:
        json.dump(scalone, uchwyt, ensure_ascii=False, indent=1)
    print(f"[CZAS] {a.wyjscie}: {scalone['modulow']} modułów, "
          f"{scalone['wykonane']} testów, ściana {scalone['wall_powloki_s']} s, "
          f"CPU {scalone['cpu_s']} s, CPU/ściana {scalone['cpu_na_sciane']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
