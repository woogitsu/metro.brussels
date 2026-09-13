#!/usr/bin/env python3
"""Bramka: peron, który NAPRAWDĘ wychodzi z pipeline'u, ma długość z decyzji właściciela.

DLACZEGO TA BRAMKA POWSTAJE. 04.09.2026 w repozytorium stały dwie długości peronu
i generowała się niewłaściwa:

* `station_components.DESIGN_PLATFORM_LENGTH_M = 95.0` — decyzja właściciela (T-212,
  PR #137): skład M7 94,0 m plus metr zapasu, po 0,50 m z każdej strony;
* `station_layout.py` bez `--platform-length-m` bierze 94,0 m, czyli DOLNĄ GRANICĘ
  z R-007 §5 pkt 2, a nie decyzję;
* obaj wołający — `tools/ci/station_details.sh` i `.github/workflows/godot-first-run.yml`
  — wołali go **bez tego argumentu**.

Zmierzone przed poprawką, na `data/track/L1_A.json`: Beekkant 462,73–556,73 m
i Parc 4028,66–4122,66 m, czyli **94,0 m**. Decyzja właściciela stała w stałej,
której pipeline nie używał, i nic tych dwóch liczb ze sobą nie porównywało.

DLACZEGO TEST MIERZY, A NIE CZYTA. Bramka sprawdzająca, czy w pliku `.sh` stoi napis
`--platform-length-m`, przeszłaby na wołaniu z literówką w wartości, na wołaniu
zakomentowanym i na trzecim wołającym, który tego napisu nie ma. Ten test **uruchamia
wywołania wyjęte z pipeline'u** i mierzy `to_m - from_m` peronów w wyprodukowanym
pliku. Sprawdzany jest wynik generatora, a nie jego wiersz poleceń.

Wołający są znajdowani, a nie wypisani z nazwy: trzeci, który dojdzie i zapomni
o decyzji, wpadnie w tę samą bramkę bez edytowania tego pliku.
"""
import glob
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "blender"))
sys.path.insert(0, os.path.join(ROOT, "tools", "track"))

import station_components as SC  # noqa: E402
import station_layout as SL  # noqa: E402

#: Oś pakietu A — ta sama, którą wołają oba miejsca w pipeline.
AXIS = os.path.join(ROOT, "data", "track", "L1_A.json")

#: Plik, którego wywołań szukamy. Ścieżka względna, bo tak stoi w pipeline.
GENERATOR = "tools/track/station_layout.py"

#: Milimetr. `from_m` i `to_m` są w wyjściu zaokrąglone do trzech miejsc, więc
#: ciaśniejsza tolerancja porównywałaby szum zaokrąglenia, a nie długość peronu.
TOLERANCE_M = 1e-3

#: Ile najmniej wywołań ma się znaleźć. Gdyby ekstraktor przestał cokolwiek łapać,
#: pętla po zerze wywołań byłaby ZIELONA i bramka zniknęłaby po cichu — dokładnie
#: ta sama usterka, którą ten plik ma łapać. 04.09.2026 wywołań są dwa.
MINIMUM_CALLERS = 2


def _pipeline_files():
    """Pliki, które pipeline naprawdę wykonuje: skrypty CI, skrypty MB-01 i workflow.

    **`tools/dev/` dołączone 13.09.2026 przy MB-01, i to nie jest poszerzenie korpusu
    „na wszelki wypadek".** Przepis generacji pakietu A przeniósł się tam z kroku
    `Generate package A geometry`, który go dotąd niósł; workflow woła teraz
    `tools/dev/prepare-playable.sh`. Bez tego wiersza ta bramka liczyłaby jedno
    wywołanie zamiast dwóch i zapalała się na przeniesieniu, a nie na usterce —
    a jej treścią jest to, że **obaj wołający** podają `--platform-length-m design`.
    """
    return (sorted(glob.glob(os.path.join(ROOT, "tools", "ci", "*.sh")))
            + sorted(glob.glob(os.path.join(ROOT, "tools", "dev", "*.sh")))
            + sorted(glob.glob(os.path.join(ROOT, ".github", "workflows", "*.yml")))
            + sorted(glob.glob(os.path.join(ROOT, ".github", "workflows", "*.yaml"))))


def _calls_in(path):
    """Wywołania generatora w jednym pliku, jako listy argumentów.

    Kontynuacje wiersza (`\\` na końcu) sklejane są PRZED szukaniem, bo w obu
    miejscach w pipeline wywołanie jest rozbite na dwa wiersze. Wpis w `paths:`
    workflow nie jest wywołaniem i nie łapie się, bo wymagane jest `python3` przed
    ścieżką.
    """
    with open(path, encoding="utf-8") as handle:
        text = handle.read()
    joined = re.sub(r"\\\n\s*", " ", text)
    pattern = re.compile(r"^\s*(python3?\s+" + re.escape(GENERATOR) + r"[^\n]*)$",
                         re.MULTILINE)
    return [shlex.split(match.group(1)) for match in pattern.finditer(joined)]


def _pipeline_calls():
    calls = []
    for path in _pipeline_files():
        for argv in _calls_in(path):
            calls.append((os.path.relpath(path, ROOT), argv))
    return calls


def _run(argv, out_path):
    """Uruchamia wywołanie z pipeline'u, podstawiając tylko wejście i wyjście.

    Podstawiane są WYŁĄCZNIE `--axis` i `--out`, bo tylko one niosą w pipeline
    zmienne powłoki i katalogi robocze. Każdy inny argument — w szczególności
    `--platform-length-m` — idzie do generatora dokładnie taki, jaki wykona CI.
    """
    argv = list(argv)
    argv[0] = sys.executable
    for flag, value in (("--axis", AXIS), ("--out", out_path)):
        if flag in argv:
            argv[argv.index(flag) + 1] = value
        else:
            argv += [flag, value]
    leftover = [a for a in argv if "$" in a]
    assert not leftover, (
        f"wywołanie niesie nierozwiniętą zmienną powłoki {leftover}; ekstraktor "
        "w tym teście przestał odwzorowywać pipeline i trzeba go poprawić, "
        "a nie obejść")
    done = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True, timeout=180)
    assert done.returncode == 0, (argv, done.returncode, done.stdout, done.stderr)
    with open(out_path, encoding="utf-8") as handle:
        return json.load(handle)


def _measured_lengths_m(report):
    """Zmierzone długości peronów: `to_m - from_m` z wyjścia, nie deklaracja.

    Perony przycięte do końca osi są pomijane — na `L1_A` są dwa (Gare de l'Ouest
    i Merode) i ich długość mówi o długości osi, a nie o decyzji właściciela.
    """
    return [platform["to_m"] - platform["from_m"] for platform in report["platforms"]
            if not platform["clipped_at_start"] and not platform["clipped_at_end"]]


def test_pipeline_platforms_measure_the_owner_decision():
    """Każde wywołanie generatora w pipeline daje perony DESIGN_PLATFORM_LENGTH_M."""
    calls = _pipeline_calls()
    assert len(calls) >= MINIMUM_CALLERS, (
        f"znaleziono {len(calls)} wywołań {GENERATOR} w pipeline, a mają być co "
        f"najmniej {MINIMUM_CALLERS}: pusta pętla byłaby zieloną bramką bez treści")
    design_m = SC.DESIGN_PLATFORM_LENGTH_M
    with tempfile.TemporaryDirectory() as workdir:
        for index, (where, argv) in enumerate(calls):
            report = _run(argv, os.path.join(workdir, f"platforms-{index}.json"))
            lengths = _measured_lengths_m(report)
            assert lengths, f"{where}: wyjście nie ma ani jednego nieprzyciętego peronu"
            worst = max(lengths, key=lambda m: abs(m - design_m))
            assert abs(worst - design_m) <= TOLERANCE_M, (
                f"{where}: peron zmierzony w wyjściu generatora ma {worst:.3f} m, "
                f"a decyzja właściciela (DESIGN_PLATFORM_LENGTH_M) to {design_m:.3f} m")


def test_the_measurement_follows_the_generator_and_not_the_constant():
    """Kontrola niepustości: pomiar ma iść za wyjściem, a nie zwracać stałą.

    Bez tego testu `_measured_lengths_m` mogłoby zwracać cokolwiek stałego i test
    wyżej byłby zielony zawsze. 96,0 m mieści się między dolną granicą R-007 (94,0 m)
    a obrysem stacji (109,1 m), więc generator je przyjmuje i nie ma prawa oddać 95,0.
    """
    with tempfile.TemporaryDirectory() as workdir:
        out = os.path.join(workdir, "explicit.json")
        report = _run(["python3", GENERATOR, "--platform-length-m", "96.0"], out)
        lengths = _measured_lengths_m(report)
        assert lengths
        assert all(abs(m - 96.0) <= TOLERANCE_M for m in lengths), lengths
        assert all(abs(m - SC.DESIGN_PLATFORM_LENGTH_M) > TOLERANCE_M for m in lengths), \
            "pomiar oddał decyzję właściciela na wywołaniu, które jej nie prosiło"


def test_design_keyword_resolves_to_the_single_constant():
    """`--platform-length-m design` czyta stałą, a nie własną kopię liczby."""
    metres, source = SL.resolve_platform_length_m(SL.DESIGN_LENGTH_KEYWORD)
    assert metres == SC.DESIGN_PLATFORM_LENGTH_M, (metres, SC.DESIGN_PLATFORM_LENGTH_M)
    assert "DESIGN_PLATFORM_LENGTH_M" in source, source

    # Bez argumentu zostaje dolna granica z R-007 — to fakt STIB, nie decyzja.
    default_m, default_source = SL.resolve_platform_length_m(None)
    assert default_m == SL.train_length_m(), (default_m, SL.train_length_m())
    assert "R-007" in default_source, default_source

    # Słowo, którego generator nie zna, ma być ODMOWĄ z diagnozą, a nie cichym 0.0
    # ani `ValueError` z tracebacku argparse.
    try:
        SL.resolve_platform_length_m("desing")
    except SystemExit as error:
        assert "design" in str(error), error
    else:
        raise AssertionError("literówka w wartości --platform-length-m przeszła")


def test_the_owner_decision_lives_in_exactly_one_place():
    """95,0 m stoi w repozytorium raz — reszta pipeline'u prosi o nie po nazwie.

    Kontrola przeciw „naprawie" polegającej na dopisaniu `--platform-length-m 95.0`
    u każdego wołającego: to jest ta sama usterka co pierwotna, tylko rozmnożona.
    """
    for where, argv in _pipeline_calls():
        if "--platform-length-m" not in argv:
            continue
        value = argv[argv.index("--platform-length-m") + 1]
        assert not re.fullmatch(r"[0-9]+(\.[0-9]+)?", value), (
            f"{where}: pipeline niesie własną kopię długości peronu ({value}); "
            f"ma prosić o decyzję właściciela słowem '{SL.DESIGN_LENGTH_KEYWORD}', "
            "żeby liczba w repozytorium została jedna")

# 6.D25: uruchomienie tego pliku WPROST idzie ta sama droga, co caly zestaw —
# z licznikiem asercji i z odmowa przy zerze testow. Bez tej gałęzi `python3
# tools/tests/<modul>.py` konczyl sie kodem 0, nie wykonawszy ani jednego testu.
if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))
