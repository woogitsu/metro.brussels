#!/usr/bin/env python3
"""Zapis czasu przebiegu wychodzi z joba jako artefakt i jest kompletny.

**Skąd ten moduł (6.D93).** `test_all.py` wypisywał „czas per moduł (malejąco)" przy
każdym przebiegu, a `.github/workflows/python-tests.yml` nie miał **ani jednego** kroku
`upload-artifact`. Trend czasu istniał więc wyłącznie w logu pojedynczego przebiegu.
Lista `POMIARY` w `test_suite_runtime_budget.py` jest uzupełniana ręcznie i rośnie
tylko wtedy, gdy ktoś o niej pamięta — to zostaje bez zmiany, bo pole „Poza zakresem"
pozycji wyklucza ruszanie tamtej bramki.

**Czego te bramki pilnują NAPRAWDĘ.** Nie tego, że plik powstaje — tego, że jest
KOMPLETNY (wpisów tyle, ile modułów przebieg wykonał, nie tyle, ile jest najwolniejszych)
i że **kod wyjścia zestawu jest wobec niego obojętny**. Ten drugi warunek jest ważniejszy:
`mutation_sweep.run_suite` czyta z procesu zestawu wyłącznie `N/M przeszło` i kod wyjścia,
więc zapis, który potrafiłby wywrócić przebieg, zamieniłby awarię dysku w falę fałszywych
„zabić".
"""
import json
import os
import subprocess
import sys
import tempfile

import yaml

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools", "ci"))

import test_all as TA  # noqa: E402
import timing_record as TR  # noqa: E402

WORKFLOW = os.path.join(ROOT, ".github", "workflows", "python-tests.yml")

#: Moduł wołany w kontroli zachowania `test_all.py` jako podproces. Ma być SZYBKI,
#: bo przebieg całego zestawu wewnątrz zestawu kosztowałby tyle, co zestaw.
MODUL_PROBNY = "test_marker_gates.py"


def _kroki():
    with open(WORKFLOW, encoding="utf-8") as uchwyt:
        return yaml.safe_load(uchwyt)["jobs"]["tools"]["steps"]


def _krok_zestawu():
    for krok in _kroki():
        if "METRO_TIMING_OUT" in (krok.get("run") or ""):
            return krok
    return None


def _krok_artefaktu():
    for krok in _kroki():
        if "upload-artifact" in (krok.get("uses") or ""):
            return krok
    return None


def test_zapis_ma_tyle_wpisow_ile_modulow_przebieg_wykonal():
    """Kompletność, nie obecność: dziesięć najwolniejszych to nie jest trend.

    Pole „Weryfikacja" pozycji żąda wprost „wszystkich wykonanych modułów, a nie
    tylko dziesięciu najwolniejszych", więc bramka porównuje liczbę wpisów z liczbą
    modułów i sumę testów z sumą z liczników.
    """
    sekundy = {f"modul_{i}": 0.5 * i for i in range(1, 15)}
    liczniki = {f"modul_{i}": i for i in range(1, 15)}
    with tempfile.TemporaryDirectory() as tmp:
        cel = os.path.join(tmp, "podkatalog", "czas.json")
        dane = TA.zapisz_czasy(cel, sekundy, liczniki, 12.5, sum(liczniki.values()))
        assert os.path.isfile(cel), "zapis nie utworzył pliku w nieistniejącym katalogu"
        with open(cel, encoding="utf-8") as uchwyt:
            z_pliku = json.load(uchwyt)

    assert z_pliku == dane, "zwrócone dane różnią się od zapisanych"
    assert len(z_pliku["moduly"]) == len(sekundy) == z_pliku["modulow"], (
        f"zapis ma {len(z_pliku['moduly'])} wpisów przy {len(sekundy)} wykonanych "
        f"modułach (pole `modulow` mówi {z_pliku['modulow']}) — pole „Weryfikacja” "
        "pozycji 6.D93 żąda WSZYSTKICH, nie dziesięciu najwolniejszych")
    assert sum(m["testow"] for m in z_pliku["moduly"]) == z_pliku["wykonane"]
    # Kolejność malejąca, jak w wypisie — bez niej pierwszy wpis nic nie znaczy.
    sekundy_z_pliku = [m["sekundy"] for m in z_pliku["moduly"]]
    assert sekundy_z_pliku == sorted(sekundy_z_pliku, reverse=True), sekundy_z_pliku


def test_zapis_niesie_commit_runner_i_rozroznia_odkryte_od_wykonanych():
    """Metadane rozstrzygają, czy dwa przebiegi wolno ze sobą zestawiać.

    Bez nazwy runnera i commita artefakt jest liczbą bez układu odniesienia; pole
    „Skończone, gdy" żąda obu. Rozróżnienie `odkryte`/`wykonane` jest tu, bo przebieg
    urwany w połowie ma je RÓŻNE i to jest jedyny ślad, po którym widać, że tabela
    czasów opisuje kawałek zestawu, a nie zestaw (6.D54).
    """
    srodowisko = {"GITHUB_SHA": "deadbee", "RUNNER_NAME": "metro-07",
                  "GITHUB_WORKFLOW": "Python tool tests"}
    zastane = {k: os.environ.get(k) for k in srodowisko}
    os.environ.update(srodowisko)
    try:
        with tempfile.TemporaryDirectory() as tmp:
            cel = os.path.join(tmp, "czas.json")
            dane = TA.zapisz_czasy(cel, {"a": 1.0}, {"a": 3}, 2.0, odkryte=5)
    finally:
        for k, v in zastane.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    assert dane["commit"] == "deadbee", dane
    assert dane["runner"] == "metro-07", dane
    assert dane["workflow"] == "Python tool tests", dane
    assert (dane["odkryte"], dane["wykonane"]) == (5, 3), (
        "przebieg, który wykonał mniej testów, niż odkrył, ma to pokazywać w zapisie: "
        f"{dane['odkryte']} odkrytych, {dane['wykonane']} wykonanych")


def test_bez_zmiennej_nie_powstaje_zaden_plik_a_kod_wyjscia_sie_nie_zmienia():
    """Dwa przebiegi tego samego modułu: bez zmiennej i ze zmienną.

    **Zapis nie ma prawa dotknąć kodu wyjścia** — `mutation_sweep.run_suite` czyta
    z tego procesu wyłącznie `N/M przeszło` i kod, więc zapis zdolny wywrócić przebieg
    zamieniłby awarię dysku w falę fałszywych „zabić". Kontrola przeciwna (przebieg ZE
    zmienną) stoi tu razem z tamtą, bo bez niej „pliku nie ma" byłoby prawdą także
    dla zapisu, który nie działa wcale.
    """
    with tempfile.TemporaryDirectory() as tmp:
        cel = os.path.join(tmp, "czas.json")

        bez = subprocess.run([sys.executable, os.path.join("tools", "tests", "test_all.py"),
                              MODUL_PROBNY],
                             cwd=ROOT, capture_output=True, text=True, timeout=300,
                             env={k: v for k, v in os.environ.items()
                                  if k != "METRO_TIMING_OUT"})
        assert not os.path.exists(cel), "plik powstał mimo braku zmiennej"
        # Sama nieobecność pliku POD ŻĄDANĄ ŚCIEŻKĄ nic nie dowodzi i to jest
        # zmierzone: mutacja zapisująca zawsze pod ustaloną nazwą w /tmp przeszła
        # tę asercję bez mrugnięcia. Rozstrzyga wypis dziecka.
        assert "[CZAS]" not in bez.stdout, (
            "przebieg bez zmiennej zapisał czasy — i to gdzie indziej, niż go proszono: "
            + bez.stdout[-300:])

        srodowisko = dict(os.environ, METRO_TIMING_OUT=cel)
        ze = subprocess.run([sys.executable, os.path.join("tools", "tests", "test_all.py"),
                             MODUL_PROBNY],
                            cwd=ROOT, capture_output=True, text=True, timeout=300,
                            env=srodowisko)
        assert os.path.isfile(cel), (
            "zmienna ustawiona, a pliku nie ma — kontrola wyżej nic by nie znaczyła: "
            + ze.stdout[-400:])
        assert f"[CZAS] zapisano {cel}" in ze.stdout, (
            "przebieg ze zmienną nie powiedział, gdzie zapisał — a to tym wypisem "
            f"mierzy się kontrolę przeciwną: {ze.stdout[-300:]}")
        with open(cel, encoding="utf-8") as uchwyt:
            zapis = json.load(uchwyt)

    assert bez.returncode == ze.returncode == 0, (bez.returncode, ze.returncode,
                                                  bez.stdout[-300:], ze.stdout[-300:])
    assert zapis["modulow"] == 1, zapis["modulow"]
    assert zapis["moduly"][0]["modul"] == MODUL_PROBNY, zapis["moduly"]
    # Ten sam wynik w wypisie i w zapisie — inaczej artefakt opisywałby inny przebieg.
    assert f"{zapis['wykonane']}/{zapis['wykonane']} przeszło" in ze.stdout, ze.stdout[-300:]


def test_scalenie_dokłada_maszyne_i_odmawia_liczb_bez_sensu():
    """`scal` liczy stosunek CPU/ściana i nie przyjmuje wejścia, z którego on nie wynika.

    Stosunek jest w artefakcie, a nie zostawiony czytającemu, bo to on mówi, czy czas
    ściany wolno z czymkolwiek porównywać (6.D42). Odmowa przy zerowej ścianie stoi tu,
    bo dzielenie przez zero dałoby wyjątek dopiero u czytającego artefakt.
    """
    baza = {"modulow": 2, "wykonane": 9, "commit": "", "runner": ""}
    scalone = TR.scal(baza, wall_s=100.0, cpu_s=132.0, runner="metro-02", commit="abc")
    assert scalone["cpu_na_sciane"] == 1.32, scalone
    assert (scalone["commit"], scalone["runner"]) == ("abc", "metro-02"), scalone
    assert baza["commit"] == "", "scal zmienił dane wejściowe w miejscu"

    z_zestawu = TR.scal({"commit": "z_zestawu", "runner": "z_zestawu"},
                        wall_s=1.0, cpu_s=1.0, runner="z_powloki", commit="z_powloki")
    assert z_zestawu["commit"] == "z_zestawu", (
        "wartość podana przez powłokę nadpisała niepustą wartość z zestawu — dwa "
        "źródła tej samej liczby mogłyby się wtedy rozjechać po cichu")

    for zla_wall, zly_cpu in ((0.0, 1.0), (-1.0, 1.0), (1.0, -0.5)):
        try:
            TR.scal(baza, wall_s=zla_wall, cpu_s=zly_cpu)
        except ValueError:
            continue
        except Exception as e:  # noqa: BLE001 — o to właśnie chodzi
            raise AssertionError(
                f"scal ze ścianą {zla_wall} i CPU {zly_cpu} wywrócił się dopiero na "
                f"arytmetyce ({type(e).__name__}: {e}) zamiast odmówić z powodem — "
                "czytający artefakt zobaczyłby wyjątek, a nie zdanie") from None
        raise AssertionError(f"scal przyjął ścianę {zla_wall} i CPU {zly_cpu}")


def test_krok_ci_zapisuje_poza_workspace_i_wynosi_artefakt():
    """Trzy warunki kroku, każdy z innym trybem cichej awarii.

    Cel zapisu w `$RUNNER_TEMP`, a nie w drzewie: plik w workspace byłby oknem, w którym
    równoległa kontrola czystości widzi zmianę, której nikt nie popełnił (6.D90) — a przy
    tym `git clean -ffdx` z checkoutu i tak zabrałby go przy następnym przebiegu.
    Sklejenie PRZED werdyktem: przebieg przekraczający próg jest dokładnie tym, którego
    czasy chce się potem obejrzeć. `if: always()` na kroku artefaktu z tego samego powodu.
    """
    krok = _krok_zestawu()
    assert krok is not None, "żaden krok nie ustawia METRO_TIMING_OUT"
    cialo = krok["run"]
    # Wartość zmiennej, a nie samo „gdzieś w ciele kroku pada $RUNNER_TEMP".
    # Zmierzone: pierwsza wersja tej asercji przechodziła przy zapisie do workspace,
    # bo `$RUNNER_TEMP` padał niżej, w argumencie `--in` sklejenia.
    import re as _re
    dopasowanie = _re.search(r'METRO_TIMING_OUT="([^"]*)"', cialo)
    assert dopasowanie, "nie da się odczytać wartości METRO_TIMING_OUT z kroku"
    cel_zapisu = dopasowanie.group(1)
    assert cel_zapisu.startswith("$RUNNER_TEMP/"), (
        "zapis czasu nie idzie do $RUNNER_TEMP, czyli ląduje w workspace — "
        f"`git clean -ffdx` zabierze go, a równoległa kontrola czystości zobaczy: "
        f"{cel_zapisu!r}")
    assert f'--in "{cel_zapisu}"' in cialo, (
        f"sklejenie czyta inny plik, niż zapisuje zestaw: {cel_zapisu!r}")
    assert "tools/ci/timing_record.py" in cialo, cialo[:300]
    assert cialo.index("tools/ci/timing_record.py") < cialo.index("B.werdykt"), (
        "sklejenie artefaktu stoi PO werdykcie, więc przebieg przekraczający próg "
        "nie zostawi po sobie czasów — a to jego czasy są najbardziej potrzebne")

    artefakt = _krok_artefaktu()
    assert artefakt is not None, "python-tests.yml nie wynosi żadnego artefaktu"
    assert artefakt.get("if") == "always()", (
        "krok artefaktu bez `if: always()` pominie przebieg czerwony: "
        f"{artefakt.get('if')!r}")
    sciezka = artefakt["with"]["path"]
    assert "runner.temp" in sciezka, sciezka
    nazwa_pliku = sciezka.rsplit("/", 1)[-1]
    assert nazwa_pliku in cialo, (
        f"krok wynosi {nazwa_pliku}, a zestaw zapisuje coś innego — artefakt byłby pusty")


def test_wykrywacz_krokow_reaguje_na_tresc_a_nie_na_kolejnosc():
    """Kontrola PRZYRZĄDU: bramka wyżej czyta YAML, więc ma umieć NIE znaleźć.

    Bez tego „krok jest i ma `always()`" znaczyłoby tyle samo, co „parser zwraca
    cokolwiek". Wejście syntetyczne, bo prawdziwy plik ma zawsze przechodzić.
    """
    global _kroki
    zastane = _kroki
    try:
        _kroki = lambda: [{"name": "coś", "run": "echo bez zmiennej"}]  # noqa: E731
        assert _krok_zestawu() is None, "wykrywacz znalazł krok, którego nie ma"
        assert _krok_artefaktu() is None

        _kroki = lambda: [{"run": 'METRO_TIMING_OUT="$RUNNER_TEMP/x.json" python3 a.py'},
                          {"uses": "actions/upload-artifact@sha", "if": "always()",
                           "with": {"path": "${{ runner.temp }}/x.json"}}]  # noqa: E731
        assert _krok_zestawu() is not None
        assert _krok_artefaktu()["if"] == "always()"
    finally:
        _kroki = zastane


if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))
