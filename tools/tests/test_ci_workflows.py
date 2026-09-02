#!/usr/bin/env python3
"""Testy odporności workflow CI. Bez zewnętrznych zależności, bez parsera YAML.

Powód: 02.09.2026 krok instalacji Blendera zawiesił się trzy razy na trzech różnych
runnerach, za każdym razem przed uruchomieniem ciała testu. Te testy pilnują, żeby
poprawka nie wyparowała po cichu przy następnej edycji workflow.
"""
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
WORKFLOWS = os.path.join(ROOT, ".github", "workflows")
HELPER = os.path.join(ROOT, "tools", "ci", "apt_install.sh")


def _workflows():
    return sorted(f for f in os.listdir(WORKFLOWS) if f.endswith((".yml", ".yaml")))


def _text(name):
    return open(os.path.join(WORKFLOWS, name), encoding="utf-8").read()


def test_ci_no_workflow_calls_apt_get_directly():
    """Instalacja pakietów idzie przez helper, żeby limit czasu był w jednym miejscu."""
    offenders = [name for name in _workflows() if "apt-get" in _text(name)]
    assert not offenders, offenders


def _steps(text):
    """Kroki workflow jako osobne bloki tekstu.

    Świadomie przez podział, nie przez `re.findall` po wzorcu zaczynającym się od
    nowej linii: taki wzorzec zjada `\n` przed następnym krokiem i kolejne dopasowanie
    nie ma od czego zacząć. Pierwsza wersja tego testu przechodziła właśnie dlatego,
    że nie widziała ANI JEDNEGO kroku instalacji — sprawdzone przez usunięcie
    `timeout-minutes` i ponowne uruchomienie.
    """
    parts = re.split(r"\n {6}- name: ", text)
    return parts[1:]


def test_ci_every_package_install_step_has_a_step_timeout():
    """Krok instalacji ma własny timeout — inaczej zawieszone pobranie zjada cały job."""
    checked = 0
    for name in _workflows():
        for step in _steps(_text(name)):
            if "apt_install.sh" not in step:
                continue
            checked += 1
            assert "timeout-minutes:" in step, (name, step.splitlines()[0].strip())
    assert checked == 5, f"oczekiwano pięciu kroków instalacji, znaleziono {checked}"


def test_ci_apt_helper_is_executable_and_retries():
    assert os.access(HELPER, os.X_OK), "tools/ci/apt_install.sh musi być wykonywalny"
    body = open(HELPER, encoding="utf-8").read()
    assert "Acquire::http::Timeout" in body and "Acquire::https::Timeout" in body
    assert "ATTEMPTS" in body and "sleep" in body


def test_ci_apt_helper_lets_apt_handle_a_dead_socket():
    """Zerwane połączenie ma łapać apt, nie zewnętrzny stoper.

    `Acquire::*::Timeout` przerywa martwe gniazdo po 30 s, a `Acquire::Retries`
    powtarza sam plik. Zewnętrzny limit jest sufitem na proces, nie mechanizmem
    ponawiania — inaczej wyrzuca do kosza 190 MB pobrane w połowie.
    """
    body = open(HELPER, encoding="utf-8").read()
    assert "sudo timeout" in body, "sygnał ma trafić w apt-get, nie w sudo"
    assert "Acquire::Retries" in body
    assert "124" in body, "kod 124 z `timeout` musi być rozpoznany i opisany"


def test_ci_install_is_not_retried_from_scratch():
    """`install` NIE jest powtarzany od zera.

    Zmierzone 02.09.2026 na `first-run`: trzy próby po 240 s, każda z postępem,
    każda ubita i zaczynająca od nowa — 13 minut na nic. Powtarzany jest tylko
    `update`, bo jest tani (11,7 MB w 2 s).
    """
    body = open(HELPER, encoding="utf-8").read()
    assert "apt_update" in body and "UPDATE_ATTEMPTS" in body
    assert "INSTALL_ATTEMPTS" not in body, "install nie ma pętli prób"
    # Podkomenda musi być czytana jako osobny token. Poprzednia wersja szukała
    # podciągu "install" w całej linii i przechodziła nawet po podmianie
    # `install` na `instalxx`, bo słowo zostaje w `--no-install-recommends`.
    subcommands = re.findall(r'(?m)^apt_run "\$[A-Z_]+" ([a-z-]+)', body)
    assert subcommands.count("install") == 1, subcommands
    assert set(subcommands) <= {"update", "install"}, subcommands


def test_ci_step_budget_covers_a_slow_mirror():
    """Sufit musi pomieścić pobranie 190 MB z wolnego lustra.

    Zmierzona prędkość lustra Azure w złym momencie: ~150 kB/s, czyli ponad
    20 minut samego pobierania. Sufit poniżej tego zamienia wolne, ale postępujące
    pobranie w twardą awarię — dokładnie to zrobiła pierwsza wersja tej poprawki.
    """
    body = open(HELPER, encoding="utf-8").read()
    install_s = int(re.search(r"INSTALL_TIMEOUT_S=\$\{APT_INSTALL_TIMEOUT_S:-(\d+)\}", body).group(1))
    measured_s = 190 * 1024 / 150
    assert install_s >= measured_s, (install_s, measured_s)
    checked = 0
    for name in _workflows():
        text = _text(name)
        job_budget = int(re.search(r"(?m)^    timeout-minutes: (\d+)$", text).group(1))
        for step in _steps(text):
            if "apt_install.sh" not in step:
                continue
            checked += 1
            step_budget = int(re.search(r"timeout-minutes: (\d+)", step).group(1))
            assert step_budget * 60 >= install_s, (name, step_budget * 60, install_s)
            # po instalacji ma jeszcze zostać czas na samą pracę joba
            assert job_budget - step_budget >= 10, (name, job_budget, step_budget)
    assert checked == 5, f"oczekiwano pięciu kroków instalacji, znaleziono {checked}"


PACKAGE_SETS = os.path.join(ROOT, "tools", "ci", "apt-packages")


def _declared_set(step):
    match = re.search(r"apt_install\.sh --set ([A-Za-z0-9_-]+)", step)
    return match.group(1) if match else None


def test_ci_package_lists_live_in_one_place():
    """Lista pakietów jest w pliku, nie rozsypana po pięciu workflow."""
    checked = 0
    for name in _workflows():
        for step in _steps(_text(name)):
            if "apt_install.sh" not in step:
                continue
            checked += 1
            declared = _declared_set(step)
            assert declared, (name, "instalacja musi iść przez --set <zestaw>")
            path = os.path.join(PACKAGE_SETS, declared + ".txt")
            assert os.path.isfile(path), (name, path)
            packages = [line.strip() for line in open(path, encoding="utf-8")
                        if line.strip() and not line.startswith("#")]
            assert "blender" in packages, (declared, packages)
    assert checked == 5, f"oczekiwano pięciu kroków instalacji, znaleziono {checked}"


def test_ci_cache_key_hashes_the_same_package_list_the_step_installs():
    """Klucz cache'a musi liczyć się z TEJ listy, którą krok instaluje.

    Inaczej dopisanie pakietu nie unieważnia cache'a i pierwszy job po zmianie
    dostaje komplet starych `.deb` bez nowego — a że apt dociąga brakujące,
    błąd byłby cichy i widoczny dopiero jako wolny job.
    """
    for name in _workflows():
        text = _text(name)
        steps = _steps(text)
        install = [s for s in steps if "apt_install.sh" in s]
        if not install:
            continue
        declared = _declared_set(install[0])
        cache = [s for s in steps if "actions/cache" in s and "metro-apt" in s]
        assert cache, (name, "krok instalacji bez cache'a pakietów")
        assert f"apt-packages/{declared}.txt" in cache[0], (name, declared)
        assert "~/.cache/metro-apt" in cache[0], name
        assert 'export APT_CACHE_DIR="$HOME/.cache/metro-apt"' in install[0], \
            (name, "env: w YAML nie rozwija ~ ani $HOME")


def test_ci_apt_helper_rejects_an_unknown_package_set():
    import subprocess
    result = subprocess.run(["bash", HELPER, "--set", "nie-ma-takiego"],
                            capture_output=True, text=True)
    assert result.returncode == 2, result
    assert "nie ma zestawu pakietów" in result.stderr
    empty = subprocess.run(["bash", HELPER, "--set"], capture_output=True, text=True)
    assert empty.returncode == 2 and "użycie" in empty.stderr


def test_ci_no_pipe_into_head_under_pipefail():
    """`| head -n N` pod `set -o pipefail` to wyścig, nie skrót.

    `head` zamyka potok po N wierszach, piszący dostaje SIGPIPE i kończy się 141,
    a `pipefail` przenosi to na cały krok. Zwykle przechodzi, bo krótkie wyjście
    mieści się w 64 KB bufora potoku i piszący zdąży skończyć — ale to jest
    wyścig, nie gwarancja. Zmierzone: `ls -la build/t400 build/t400/chunks`
    (64 wiersze) dawało lokalnie 0 dziesięć razy na dziesięć, a `find /` już 141
    za każdym razem. Na runnerze pod obciążeniem przegrał wariant krótki
    (`first-run` na #88, 02.09.2026: sweep zapisał komplet 12 chunków, a krok
    i tak padł).

    `sed -n '1,Np'` czyta do końca, więc piszący nigdy nie dostaje SIGPIPE.
    """
    offenders = []
    for directory in (WORKFLOWS, os.path.join(ROOT, "tools", "ci")):
        for name in sorted(os.listdir(directory)):
            if not name.endswith((".yml", ".yaml", ".sh")):
                continue
            text = open(os.path.join(directory, name), encoding="utf-8").read()
            for number, line in enumerate(text.splitlines(), 1):
                if re.search(r"\|\s*head\b", line):
                    offenders.append(f"{name}:{number}")
    assert not offenders, offenders


def test_ci_blender_workflows_still_install_blender():
    """Odporność nie może po cichu zgubić samego pakietu."""
    for name in ("blender-smoke.yml", "tunnel-alignment.yml", "m7-shell.yml",
                 "visual-regression.yml", "godot-first-run.yml"):
        text = _text(name)
        declared = None
        for step in _steps(text):
            if "apt_install.sh" in step:
                declared = _declared_set(step)
        assert declared, name
        packages = open(os.path.join(PACKAGE_SETS, declared + ".txt"), encoding="utf-8").read()
        assert "libegl1" in packages and "python3-numpy" in packages, (name, declared)


def _paths_block(text):
    """Lista wzorców z `paths:` w `on: pull_request`. Brak filtra => None."""
    match = re.search(r"(?m)^    paths:\n((?:      - .*\n|      #.*\n)+)", text)
    if not match:
        return None
    return re.findall(r"      - '([^']+)'", match.group(1))


def test_ci_workflows_running_tools_ci_are_triggered_by_tools_ci():
    """Skrypt, którego zmiana nie odpala własnego CI, nie jest bramką.

    Zmierzone 02.09.2026: `tools/ci/vehicle_clearance.sh` (495 linii) jest
    wywoływane w `tunnel-alignment.yml`, ale w `paths:` siedział wyłącznie
    `tools/ci/tunnel_alignment.sh`. Wstrzyknięty `exit 3` przechodził — bo job
    w ogóle się nie uruchamiał. To samo dotyczyło `apt_install.sh` i list
    pakietów, których nie było w `paths:` żadnego workflow.
    """
    offenders = []
    for name in _workflows():
        text = _text(name)
        if not re.search(r"tools/ci/[A-Za-z0-9_]+\.sh", text.split("permissions:", 1)[-1]):
            continue
        patterns = _paths_block(text)
        if patterns is None:      # brak filtra = odpala się zawsze
            continue
        if "tools/ci/**" not in patterns:
            offenders.append((name, patterns))
    assert not offenders, offenders


def test_ci_grep_gates_check_that_their_target_exists():
    """`grep` bez celu kończy się kodem 2, a `if grep ...; then` czyta to jak brak trafień.

    Bramka reguły 9 ogłaszała wtedy „src/Sim: brak odwołań do Godota" dla
    katalogu, którego nie ma. Każdy krok z takim `if grep` musi najpierw
    sprawdzić istnienie celu.
    """
    offenders = []
    checked = 0
    for name in _workflows():
        for step in _steps(_text(name)):
            if not re.search(r"(?m)^\s*if grep\b", step):
                continue
            head = step.splitlines()[0]
            # Cały krok, nie pojedyncza linia: wzorzec reguły 9 jest łamany
            # odwrotnym ukośnikiem i ścieżka `src/Sim` siedzi w linii NASTĘPNEJ.
            # Wersja linia-po-linii w ogóle jej nie widziała i przechodziła
            # po usunięciu `test -d` — sprawdzone.
            command = step[re.search(r"(?m)^\s*if grep\b", step).start():]
            command = command[:command.index("; then")]
            targets = set()
            for token in command.replace("\\\n", " ").split():
                token = token.strip("'\"")
                if os.path.exists(os.path.join(ROOT, token)):
                    targets.add(token)
            assert targets, f"{name}: {head} — nie rozpoznano celu grepa"
            for target in sorted(targets):
                checked += 1
                if not re.search(r"test -[df] " + re.escape(target) + r"\b", step):
                    offenders.append(f"{name}: {head} -> {target}")
    assert not offenders, offenders
    assert checked >= 2, checked


def test_ci_reference_parity_step_is_a_gate_not_a_print():
    """Krok o tej nazwie był do 02.09.2026 samym `print` i nie mógł wywalić joba.

    Obcięcie mocy trakcji w `reference.py` o 10 % przechodziło przez całe CI,
    mimo że snapshot w `tests/Sim.Tests/PythonReference.cs` zostawał stary.
    """
    step = [s for s in _steps(_text("sim-tests.yml")) if s.startswith("Reference parity")]
    assert len(step) == 1, "krok zniknął albo zmienił nazwę"
    assert "tools/tests/test_reference_snapshot.py" in step[0], step[0]


def _reaches_dotnet(body):
    """Czy krok workflow dochodzi do `dotnet` — wprost albo przez skrypt z tools/ci."""
    if re.search(r"(?m)^\s*(-\s*)?(run:\s*)?.*\bdotnet\b", body):
        return True
    for script in set(re.findall(r"(tools/ci/[A-Za-z0-9_]+\.sh)", body)):
        path = os.path.join(ROOT, script)
        if not os.path.isfile(path):
            continue
        text = open(path, encoding="utf-8").read()
        if "dotnet" in text or "doctor.sh" in text:
            return True
    return False


def test_ci_workflows_using_dotnet_pin_the_sdk():
    """`doctor.sh` odpala `dotnet test`. Bez pinu job jedzie na tym, co akurat ma obraz.

    Zmierzone 02.09.2026: `blender-smoke.yml` przez `tools/ci/blender_smoke.sh`
    woła `doctor.sh`, a ten `dotnet test tests/Sim.Tests` — i nigdzie nie było
    `actions/setup-dotnet`. Wersja szukająca słowa „dotnet" tylko w samym YAML-u
    tego nie widziała, więc test schodzi o poziom niżej, do skryptów.
    """
    offenders = []
    checked = []
    for name in _workflows():
        text = _text(name)
        body = text.split("permissions:", 1)[-1]
        if not _reaches_dotnet(body):
            continue
        checked.append(name)
        if "actions/setup-dotnet" not in text:
            offenders.append(name)
    assert not offenders, offenders
    assert "blender-smoke.yml" in checked and "sim-tests.yml" in checked, checked


def test_ci_negative_screenshot_control_checks_why_it_failed():
    """Negatyw musi wywalić się na pustej klatce, nie na braku metadanych.

    Zmierzone 02.09.2026: `--no-geometry` nie ładuje tunelu, więc FirstRun.cs
    nie zapisuje `GODOT_metadata.json`, a compare.py przerywał na „brak
    metadanych bieżącego przebiegu". Sam niezerowy kod wyjścia nie odróżniał
    tych dwóch powodów — negatyw przechodziłby także przy rozluźnionych
    progach pustej klatki.
    """
    step = [s for s in _steps(_text("godot-first-run.yml"))
            if s.startswith("Negative control of the screenshot check")]
    assert len(step) == 1, "krok zniknął albo zmienił nazwę"
    body = step[0]
    assert "GODOT_metadata.json" in body, "negatyw nie ma metadanych do porównania"
    assert "tools/ci/assert_empty_frame_negative.py" in body, body


def test_ci_negative_assertion_script_reads_the_reason():
    """Sam skrypt kontrolny: przyjmuje tylko raport z pustymi klatkami."""
    import json
    import subprocess
    import tempfile
    script = os.path.join(ROOT, "tools", "ci", "assert_empty_frame_negative.py")
    empty = "obraz pusty/jednorodny: ink=0.00001 std=0.00010 poziomy=3"
    good = {"images": [{"camera": f"c{i}", "status": "fail", "reason": empty} for i in range(5)],
            "geometry": {"status": "new-baseline", "reason": "brak metadanych baseline"}}
    on_geometry = json.loads(json.dumps(good))
    on_geometry["geometry"] = {"status": "fail", "reason": "brak metadanych bieżącego przebiegu"}
    accepted = json.loads(json.dumps(good))
    accepted["images"][2] = {"camera": "c2", "status": "pass", "reason": None}
    for data, expected in ((good, 0), (on_geometry, 1), (accepted, 1), ({"images": []}, 1)):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False,
                                         encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False)
            path = handle.name
        try:
            code = subprocess.run(["python3", script, path], capture_output=True).returncode
        finally:
            os.unlink(path)
        assert code == expected, (data, code, expected)
