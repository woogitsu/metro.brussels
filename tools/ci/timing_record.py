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
import re
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


#: Pola wpisu listy `POMIARY` w `tools/tests/test_suite_runtime_budget.py`, w kolejności
#: krotki. Nazwy stoją tu po to, żeby „pięć pól" z pozycji 6.D152 miało w kodzie przedmiot,
#: a nie było liczbą w zdaniu raportu.
POLA_WPISU = ("data", "sekundy", "modulow", "maszyna", "na_czym")

#: Wartość pola `maszyna` dla wpisu wyprowadzonego z logu joba — i **cała odpowiedź
#: pozycji 6.D152 na pytanie, co zostaje człowiekowi**. Log kroku „Run tool tests" powstaje
#: WYŁĄCZNIE na runnerze, bo `python-tests.yml` ma `runs-on: self-hosted`; pomiar zrobiony
#: w kontenerze sesji nie ma żadnego logu i przez tego czytelnika nie przejdzie. Ręcznego
#: wpisu wymagają więc dokładnie te pomiary, których nic nie zapisało maszynowo — a nie,
#: jak zakładała pozycja, jakieś pole wpisu z CI.
#: Równości z `test_suite_runtime_budget.MASZYNA_RUNNER` pilnuje bramka w
#: `tools/tests/test_timing_record.py`: dwa napisy o tym samym nie mogą się rozjechać.
MASZYNA_Z_LOGU = "runner"

#: Stempel czasu, którym runner poprzedza KAŻDY wiersz logu: `2026-09-11T12:40:55.2867490Z`.
#: Czytany z wiersza SUROWEGO (pole `data`) i zdejmowany przed resztą wzorców.
_STEMPEL = re.compile(r"^(\d{4}-\d{2}-\d{2})T\d{2}:\d{2}:\d{2}\.\d+Z ")

#: Kolorowanie, którym runner ozdabia echo ciała kroku. Bez zdjęcia go wzorce zakotwiczone
#: na początku wiersza nie trafiają w nic.
_ANSI = re.compile(r"\x1b\[[0-9;]*m")

#: Wiersz logu → pole wpisu. Klucz jest nazwą pola, wartość wzorcem z JEDNĄ grupą.
#:
#: **Skąd ta tabela (6.D152).** Pozycja zakładała, że log nie podaje wprost maszyny ani
#: zdania o warunkach, więc automat wypełniłby je zgadując. Zmierzone na sześciu logach
#: przebiegów, z których 6.D135 przepisało wpisy RĘCZNIE (PR #524 … #529): log podaje
#: **wszystko**, a wyprowadzone wartości zgadzają się z przepisanymi co do znaku.
#: Przesłanka pozycji jest więc nieprawdziwa dla wpisów z CI i ten komentarz jest jej
#: przepisaniem, a nie dopiskiem obok. Liczby i tabela: `reports/6d152-pola-wpisu-z-logu.md`.
WZORY_LOGU = {
    "sekundy": re.compile(r"^czas sciany test_all\.py: ([\d.]+) s \(prog [\d.]+ s\)$"),
    "modulow": re.compile(r"^ *RAZEM [\d.]+ s, \d+ testów, (\d+) modułów$"),
    "testow": re.compile(r"^ *RAZEM [\d.]+ s, (\d+) testów, \d+ modułów$"),
    "cpu_na_sciane": re.compile(
        r"^czas sciany [\d.]+ s w progu [\d.]+ s, "
        r"stosunek CPU/sciana ([\d.]+) \(podloga [\d.]+\)$"),
    "runner": re.compile(r"^Runner name: '(.+)'$"),
    "job": re.compile(r"^Complete job name: (.+)$"),
    "pr": re.compile(r"^\[command\].*refs/remotes/pull/(\d+)/merge$"),
}

#: Przeliczenia wartości wyjętych z logu. Czego tu nie ma, zostaje napisem — `cpu_na_sciane`
#: ZOSTAJE napisem świadomie, bo w zdaniu „na czym" liczy się jego ZAPIS (trzy miejsca po
#: przecinku, z zerem końcowym w `1,810`), a `float` to zero by zgubił.
_PRZELICZ = {"sekundy": float, "modulow": int, "testow": int, "pr": int}

#: Wszystko, co `z_logu` ma zwrócić. Pola pochodne (`maszyna`, `na_czym`) są tu razem
#: z surowymi, bo `brakujące` ma mówić o WPISIE, a nie o tabeli wzorców.
WYPROWADZANE = tuple(WZORY_LOGU) + ("data", "maszyna", "na_czym")


def _bez_ozdob(wiersz):
    """Wiersz logu bez BOM-u, stempla czasu i kolorowania."""
    wiersz = wiersz.lstrip("﻿")
    wiersz = _STEMPEL.sub("", wiersz, count=1)
    return _ANSI.sub("", wiersz).rstrip("\r")


def zdanie_na_czym(job, pr, cpu_na_sciane, testow):
    """Piąte pole wpisu złożone z czterech wartości logu, w zapisie z `POMIARY`.

    Kształt nie jest wymyślony tutaj: jest przepisany z wpisów, które 6.D135 wstawiło
    z ręki, i bramka porównuje go z nimi znak w znak. Przecinek dziesiętny, bo lista jest
    po polsku; półpauza, bo tak stoi w oryginale.
    """
    return (f"job `{job}`, PR #{pr}, CPU/ściana {str(cpu_na_sciane).replace('.', ',')} "
            f"— {testow} testów")


def z_logu(tekst):
    """Pola wpisu `POMIARY` wyprowadzone z logu joba. Zwraca `(pola, brakujące)`.

    **`brakujące` jest treścią, a nie dodatkiem.** Czytelnik, który po nieznalezieniu
    wiersza wstawiałby wartość domyślną, byłby kolejnym przyrządem meldującym sprawdzenie,
    którego nie zrobił — rodzina 6.D27, tropiona w tym projekcie od tamtej pozycji. Tutaj
    pole, którego w logu nie ma, po prostu NIE POWSTAJE, a jego nazwa ląduje w drugim
    elemencie krotki. Kontrola przyrządu (`test_timing_record.py`) usuwa z prawdziwego logu
    po jednym wierszu naraz i żąda, żeby za każdym razem zapaliło się dokładnie to pole.

    Sam niczego nie mierzy i niczego nie zapisuje — tak samo jak `scal` wyżej.
    """
    pola = {}
    for wiersz in tekst.splitlines():
        if "data" not in pola:
            stempel = _STEMPEL.match(wiersz.lstrip("﻿"))
            if stempel:
                pola["data"] = stempel.group(1)
        goly = _bez_ozdob(wiersz)
        for nazwa, wzor in WZORY_LOGU.items():
            if nazwa in pola:
                continue
            trafienie = wzor.match(goly)
            if trafienie:
                wartosc = trafienie.group(1)
                pola[nazwa] = _PRZELICZ.get(nazwa, str)(wartosc)
    if "runner" in pola:
        pola["maszyna"] = MASZYNA_Z_LOGU
    if all(k in pola for k in ("job", "pr", "cpu_na_sciane", "testow")):
        pola["na_czym"] = zdanie_na_czym(pola["job"], pola["pr"],
                                         pola["cpu_na_sciane"], pola["testow"])
    return pola, tuple(n for n in WYPROWADZANE if n not in pola)


def wypisz_z_logu(sciezka):
    """Gotowy do wklejenia wpis `POMIARY` z logu joba. Wypisuje; NICZEGO nie dopisuje.

    Dopisywanie wpisów automatem stoi w polu „Poza zakresem" pozycji 6.D152 i tam zostaje:
    o tym, czy pomiar wchodzi do listy, decyduje człowiek. Ten tryb zdejmuje z niego
    wyłącznie przepisywanie liczb — czyli tę część, która przy 6.D135 była robiona z ręki
    siedem razy.
    """
    with open(sciezka, encoding="utf-8", errors="replace") as uchwyt:
        pola, brakujace = z_logu(uchwyt.read())
    if brakujace:
        print(f"BRAK w {sciezka}: {', '.join(brakujace)} — to nie jest log kroku "
              "\u201eRun tool tests\u201d albo krok zmieni\u0142 wypisy", file=sys.stderr)
        return 1
    # Trzy miejsca po przecinku, bo tyle ma wiersz logu: krok „Run tool tests" liczy
    # `elapsed` przez `print(f'{...:.3f}')`. Samo `{float}` zgubiłoby zero końcowe
    # (109.420 → 109.42) i wklejony wpis czytałby się inaczej niż log, z którego wyszedł.
    print(f'    ("{pola["data"]}", {pola["sekundy"]:.3f}, {pola["modulow"]}, '
          f'MASZYNA_RUNNER,\n     "{pola["na_czym"]}"),')
    print(f"# runner: {pola['runner']}", file=sys.stderr)
    return 0

def main(argv=None):
    # Tryb czytania logu stoi PRZED parserem i celowo nie jest jego argumentem: reszta
    # wywołania ma cztery argumenty wymagane, a ten trybu nie potrzebuje żadnego z nich.
    # Wpuszczenie go do parsera znaczyłoby zdjęcie `required=True` z tamtych — czyli
    # osłabienie kontroli, która dziś łapie krok CI wołający sklejenie bez wejścia.
    argumenty = sys.argv[1:] if argv is None else list(argv)
    if argumenty and argumenty[0] == "--z-logu":
        if len(argumenty) != 2:
            print("użycie: timing_record.py --z-logu <log joba `tools`>", file=sys.stderr)
            return 1
        return wypisz_z_logu(argumenty[1])

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
