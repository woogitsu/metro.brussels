#!/usr/bin/env python3
"""Testy odporności workflow CI.

Powód: 02.09.2026 krok instalacji Blendera zawiesił się trzy razy na trzech różnych
runnerach, za każdym razem przed uruchomieniem ciała testu. Te testy pilnują, żeby
poprawka nie wyparowała po cichu przy następnej edycji workflow.
"""
import os
import re

import yaml

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


def test_godot_scene_knows_every_argument_the_workflow_passes():
    """Lista znanych argumentów sceny i to, czym woła ją CI, muszą się zgadzać.

    Zmierzone 02.09.2026 audytem mutacyjnym: `--at-chainag=2000` — literówka na
    jednym znaku — kończyło się kodem 0 i zrzutem `GODOT_cab_2000m.png`
    przedstawiającym stojący skład na 94 m. `ParseArguments` wrzucało każdy argument
    do słownika i nigdy nie sprawdzało, czy ktoś go odczytał. Pięć „ujęć kontrolnych"
    mogło więc być pięcioma kopiami tego samego kadru.

    Scena odrzuca teraz nieznany argument, a ten test pilnuje obu stron: że lista
    w kodzie nie zgubi argumentu, którego CI używa, i że CI nie zacznie wołać
    argumentu, którego scena nie zna.
    """
    source = open(os.path.join(ROOT, "src", "Game", "FirstRun.cs"), encoding="utf-8").read()
    block = re.search(r"KnownArguments\s*=\s*\{(.*?)\};", source, re.S)
    assert block, "lista znanych argumentów zniknęła z FirstRun.cs"
    known = set(re.findall(r'"([a-z-]+)"', block.group(1)))
    assert len(known) >= 10, known

    text = _text("godot-first-run.yml")
    scene_calls = [line for line in text.splitlines() if "--path src/Game" in line]
    assert scene_calls, "workflow przestał uruchamiać scenę"

    # Argumenty sceny to wyłącznie to, co stoi PO `--` w wywołaniu silnika, do końca
    # tego wywołania — czyli do pierwszej linii bez kontynuacji `\`. Szersze łapanie
    # wciągało argumenty compare.py i dotnet-a z tego samego kroku.
    lines = text.splitlines()
    used = set()
    for index, line in enumerate(lines):
        if "--path src/Game" not in line:
            continue
        chunk = [line.split("--path src/Game", 1)[1]]
        cursor = index
        while lines[cursor].rstrip().endswith("\\") and cursor + 1 < len(lines):
            cursor += 1
            chunk.append(lines[cursor])
        used.update(re.findall(r"(?<!-)--([a-z-]+)(?:=|\s|$)", " ".join(chunk)))

    unknown = sorted(name for name in used if name not in known)
    assert not unknown, f"CI woła argumenty, których scena nie zna: {unknown}"
    assert {"shot", "at-chainage", "view"} <= used, sorted(used)


def test_godot_scene_rejects_unknown_arguments_instead_of_ignoring_them():
    """Sama bramka w kodzie, nie tylko zgodność list."""
    source = open(os.path.join(ROOT, "src", "Game", "FirstRun.cs"), encoding="utf-8").read()
    assert "ExitUnknownArgument" in source
    assert "Array.IndexOf(KnownArguments, name) < 0" in source, \
        "zniknęło sprawdzenie, czy argument jest znany"
    assert "KnownViews" in source and "ExitBadArgumentValue" in source, \
        "nieznany --view musi być błędem, a nie cichym powrotem do kabiny"
    # `double.Parse` w środku `_Ready` rzucał wyjątkiem, `_shotPath` było już
    # ustawione i `_Process` kręciło się w nieskończoność aż do timeoutu CI.
    assert "double.Parse(" not in source, "parsowanie bez TryParse wraca do zawieszania"
    assert "long.Parse(" not in source, "parsowanie bez TryParse wraca do zawieszania"
    assert "_aborted" in source, "brak flagi zatrzymującej pętlę klatek"


def test_godot_scene_gates_the_axis_against_the_manifest():
    """Wydruk udający bramkę: rozjazd 6,7 km przechodził zielony.

    Osobny krok CI `axis-vs-manifest` tego nie łapie, bo czyta manifest WŁASNYM
    parserem z Sim.Runner — sprawdza plik na dysku, a nie to, co z tego pliku
    wyjęła scena. Zmierzone po poprawce: ta sama mutacja daje kod wyjścia 10.
    """
    source = open(os.path.join(ROOT, "src", "Game", "FirstRun.cs"), encoding="utf-8").read()
    assert "AxisManifestToleranceM" in source
    assert "ExitAxisManifestMismatch" in source
    assert re.search(r"if \(drift > AxisManifestToleranceM\)", source), \
        "porównanie osi z manifestem wróciło do bycia wydrukiem"


# --- self-hosted runner (2026-09-02, wyczerpane minuty GitHub Actions) ----------


def test_every_job_runs_on_the_self_hosted_runner():
    """Etykieta `runs-on` decyduje o tym, czy job w ogóle wystartuje.

    `runs-on` z etykietą, której żaden zarejestrowany runner nie nosi, oznacza job
    wiszący w `queued` bez końca — a `CLAUDE.md` §9 mówi wprost: „Nie uznawaj
    `queued` za weryfikację". Etykieta jest gołe `self-hosted`, bez `wsl2`:
    w matmaxalez/osadale 2026-08-19 zdjęto `wsl2`, bo maszyna z tą etykietą została
    wyłączona i joby zawisły. Gołe `self-hosted` łapie każdego runnera, jakiego
    właściciel zarejestruje.
    """
    wrong = []
    for name in _workflows():
        for match in re.finditer(r"(?m)^    runs-on: (.+)$", _text(name)):
            label = match.group(1).strip()
            if label != "self-hosted":
                wrong.append(f"{name}: {label}")
    assert not wrong, wrong

    hosted = [name for name in _workflows() if "ubuntu-latest" in _text(name)]
    assert not hosted, f"GitHub-hosted runner nadal wymieniony w: {hosted}"


def test_every_job_refuses_pull_requests_from_forks():
    """Kod z forka NIE MA prawa wykonać się na maszynie właściciela.

    To jest warunek bezpieczeństwa, nie higiena: kroki tych jobów uruchamiają kod
    ze sprawdzonego refa (`tools/**`, `doctor.sh`, skrypty CI), więc bez tego
    warunku wystarczyłby pull request z forka, żeby uruchomić tam dowolny kod.

    `metro.brussels` jest prywatne, ale ma WŁĄCZONE forkowanie (`allow_forking:
    true`), więc uzasadnienie z matmaxalez/osadale — „forka nie da się zrobić" —
    tutaj nie obowiązuje. Warunek nosi każdy job osobno; `needs:` nie jest
    zamiennikiem, bo job dopisany bez łańcucha zależności nie miałby ochrony.
    """
    required_terms = (
        "github.event_name != 'pull_request'",
        "github.event.pull_request.head.repo.full_name == github.repository",
    )
    unguarded = []
    checked = 0
    for name in _workflows():
        document = yaml.safe_load(_text(name))
        for job_id, job in document["jobs"].items():
            checked += 1
            condition = str(job.get("if", ""))
            if not all(term in condition for term in required_terms):
                unguarded.append(f"{name}:{job_id}")
    assert not unguarded, f"joby bez strażnika fork-PR: {unguarded}"
    assert checked >= 7, checked


def test_every_workflow_proves_the_workspace_was_clean():
    """Workspace self-hosted runnera jest współdzielony między przebiegami.

    Bramki tego projektu sprawdzają PLIKI WYJŚCIOWE (`CLAUDE.md` §5: skrypt bez
    błędu potrafi wyprodukować pustą scenę), więc plik z poprzedniego przebiegu
    przechodzi je tak samo dobrze jak świeży.

    Sprzątaniem zajmuje się `actions/checkout` — jego wejście `clean` ma domyślnie
    `true`, czyli `git clean -ffdx && git reset --hard HEAD`, a `-x` obejmuje pliki
    ignorowane. Krok w workflow tego NIE powtarza, tylko SPRAWDZA: `rm -rf` nie
    odróżniłby „posprzątane" od „checkout przestał sprzątać".
    """
    missing = []
    for name in _workflows():
        text = _text(name)
        if "Workspace jest czysty po checkoucie" not in text:
            missing.append(name)
        # `clean: false` wyłączyłoby jedyny mechanizm, który realnie sprząta.
        # Sprawdzane na SPARSOWANYM YAML-u, nie gremem po tekście: komentarz przy
        # tym kroku sam zawiera napis `clean: false`, więc wersja tekstowa wywracała
        # się na własnym opisie — ta sama pułapka, co przy bramce reguły 9.
        for step in yaml.safe_load(text)["jobs"][next(iter(yaml.safe_load(text)["jobs"]))]["steps"]:
            if str(step.get("uses", "")).startswith("actions/checkout"):
                assert (step.get("with") or {}).get("clean") is not False, \
                    f"{name}: checkout z clean: false"
    assert not missing, f"workflow bez bramki czystego workspace: {missing}"


def test_tool_installation_is_conditional_on_the_tool_being_missing():
    """Na trwałej maszynie instalacja przy każdym przebiegu to strata i zbędny sudo.

    Blender to 162 pakiety i 190 MB. Na jednorazowej maszynie GitHuba trzeba go było
    stawiać za każdym razem; na maszynie właściciela zostaje. Krok sondujący ustawia
    wyjście, a instalacja i cache odpalają się tylko przy jego braku — świeży runner
    nadal działa bez ręcznego przygotowania.
    """
    checked = 0
    for name in _workflows():
        text = _text(name)
        if "apt_install.sh" not in text:
            continue
        checked += 1
        document = yaml.safe_load(text)
        steps = list(document["jobs"].values())[0]["steps"]

        probe = [s for s in steps if s.get("id") == "tools"]
        assert probe, f"{name}: brak kroku sondującego obecność Blendera"
        assert "command -v blender" in probe[0]["run"], name

        for step in steps:
            run = str(step.get("run", ""))
            if "apt_install.sh" in run or (step.get("uses", "").startswith("actions/cache")
                                           and "metro-apt" in str(step)):
                assert step.get("if") == "steps.tools.outputs.blender == 'missing'", \
                    f"{name}: krok '{step.get('name')}' nie jest zabramkowany sondą"
    assert checked == 5, checked


def test_godot_lives_outside_the_workspace_that_checkout_wipes():
    """Silnik w workspace znikał przy każdym `git clean -ffdx` i był pobierany od nowa.

    70 MB na przebieg. Na jednorazowej maszynie nieuniknione, na trwałej — strata,
    którą usuwa przeniesienie katalogu poza workspace.

    Pierwsza wersja tego testu żądała `runner.tool_cache` w `env:` na górze pliku
    i przeszła — a GitHub odmówił uruchomienia całego workflow, bo kontekstu `runner`
    tam nie ma. Test pilnował więc dokładnie tej postaci, która nie działa. Teraz
    sprawdza WŁASNOŚĆ (katalog poza workspace), nie zapis.
    """
    text = _text("godot-first-run.yml")
    document = yaml.safe_load(text)
    assert "GODOT_DIR" not in (document.get("env") or {}), (
        "GODOT_DIR w workflow-level env: tam nie ma kontekstu runner, "
        "a bez niego ścieżka wskaże workspace"
    )

    steps = list(document["jobs"].values())[0]["steps"]
    setter = [s for s in steps if "GODOT_DIR=" in (s.get("run") or "")]
    assert setter, "żaden krok nie ustawia GODOT_DIR"
    body = setter[0]["run"]
    assert "GITHUB_ENV" in body, "GODOT_DIR musi trafić do GITHUB_ENV, inaczej widzi go jeden krok"
    assert "RUNNER_TOOL_CACHE" in body, body
    # Katalog poza workspace to cała racja bytu tego kroku — więc krok sam to
    # sprawdza i przerywa, gdy ścieżka jednak wyląduje w workspace.
    assert "GITHUB_WORKSPACE" in body, (
        "krok nie sprawdza, czy katalog nie wylądował w workspace"
    )

    index = steps.index(setter[0])
    users = [s for s in steps[:index] if "$GODOT_DIR" in (s.get("run") or "")]
    assert not users, f"kroki używają GODOT_DIR zanim zostanie ustawiony: {users}"

    probe = [s for s in steps if s.get("id") == "godot"]
    assert probe, "brak kroku sprawdzającego, czy Godot już jest"
    # Sam plik wykonywalny nie wystarcza — bez GodotSharp silnik wywala się
    # dopiero przy starcie sceny, kilkanaście kroków od powodu.
    assert "GodotSharp" in probe[0]["run"], probe[0]["run"]

    download = [s for s in steps if s.get("name") == "Download Godot mono"]
    assert download and download[0].get("if") == "steps.godot.outputs.engine == 'missing'", download


#: Kontekst `runner` jest dostępny DOPIERO w kroku. Workflow-level `env` widzi
#: `github`, `secrets`, `inputs`, `vars`; job-level `env` dokłada `needs`,
#: `strategy`, `matrix`. Nigdzie tam nie ma `runner`.
_RUNNER_CONTEXT_IS_A_STEP_THING = ("env", "runs-on", "if", "timeout-minutes")


def test_no_workflow_uses_the_runner_context_where_github_refuses_to_start_it():
    """Zła gałąź kontekstu nie jest literówką — GitHub NIE URUCHAMIA takiego workflow.

    To nie jest hipoteza. `${{ runner.tool_cache }}` w `env:` na górze
    `godot-first-run.yml` dało przebieg 73: `conclusion: failure` w tej samej
    sekundzie, w której powstał, ZERO jobów, a pole `name` przebiegu to ścieżka
    pliku zamiast „Godot first run" — bo GitHub nie zdołał go sparsować, żeby
    odczytać `name:`.

    Żaden z pozostałych testów tego nie łapał: wszystkie czytają treść YAML-a,
    a ten YAML jest poprawny składniowo. Niepoprawna jest dopiero reguła GitHuba
    o dostępności kontekstów — i to ona jest tu sprawdzana.
    """
    offenders = []
    for name in _workflows():
        document = yaml.safe_load(_text(name))
        top = document.get("env") or {}
        for key, value in top.items():
            if "runner." in str(value):
                offenders.append(f"{name}: env.{key} = {value}")
        for job_id, job in document["jobs"].items():
            for key in _RUNNER_CONTEXT_IS_A_STEP_THING:
                value = job.get(key)
                if key == "env":
                    for sub, sub_value in (value or {}).items():
                        if "runner." in str(sub_value):
                            offenders.append(f"{name}: {job_id}.env.{sub} = {sub_value}")
                elif "runner." in str(value or ""):
                    offenders.append(f"{name}: {job_id}.{key} = {value}")
    assert not offenders, (
        "kontekst runner poza krokiem — GitHub odmówi uruchomienia workflow:\n  "
        + "\n  ".join(offenders)
    )


# --- warstwa silnika ma własne testy jednostkowe ---------------------------------

GAME_TESTS = os.path.join(ROOT, "tests", "Game.Tests", "Game.Tests.csproj")
SOLUTION = os.path.join(ROOT, "MetroBxl.sln")


def test_the_engine_layer_has_a_unit_test_project():
    """Do 02.09.2026 `src/Game` nie miał ANI JEDNEGO testu jednostkowego.

    13 typów weryfikowanych wyłącznie integracyjnie przez `godot-first-run.yml`.
    Audyt mutacyjny pokazał, co przez to przechodziło: `TrackOffsetM 2.10→0.0`
    i `CabEyeHeightM 2.20→0.0` zostawiały wszystkie bramki zielone.
    """
    assert os.path.isfile(GAME_TESTS), GAME_TESTS


def test_the_engine_test_project_stays_out_of_the_core_solution():
    """Reguła 9 w drugą stronę: `tests/Game.Tests` referuje Godota.

    Gdyby wszedł do `MetroBxl.sln`, `dotnet build MetroBxl.sln` z `sim-tests.yml`
    zaczęłoby ściągać Godot.NET.Sdk — i rdzeń przestałby się budować bez silnika.
    To jest ta sama decyzja, którą `MetroBxl.Game.csproj` opisuje w swoim komentarzu
    jako „decyzja, nie przeoczenie".
    """
    assert os.path.isfile(SOLUTION), SOLUTION
    with open(SOLUTION, encoding="utf-8") as handle:
        solution = handle.read()
    # Sprawdzana jest ŚCIEŻKA, nie nazwa projektu. Wpisy w .sln wyglądają tak:
    #   Project(...) = "Sim.Tests", "tests\\Sim.Tests\\Sim.Tests.csproj", ...
    # Napis `MetroBxl.Game` pada tylko dla `src\\Game\\MetroBxl.Game.csproj`;
    # `tests\\Game.Tests\\Game.Tests.csproj` nie zawiera go wcale. Pierwsza wersja
    # tej bramki szukała właśnie nazwy i PRZEPUŚCIŁA projekt testowy do solucji —
    # sprawdzone mutacją.
    for forbidden in ("src\\Game", "src/Game", "tests\\Game.Tests", "tests/Game.Tests"):
        assert forbidden not in solution, \
            f"{forbidden} w solucji rdzenia — rdzeń przestałby się budować bez silnika"


def test_the_workflow_with_the_engine_actually_runs_those_tests():
    """Projekt testowy poza solucją nie uruchomi się sam.

    `sim-tests.yml` buduje solucję, więc tych testów nie zobaczy. Musi je wołać
    workflow, który silnik i tak ma — inaczej istniałyby, a nie chodziły.
    """
    text = _text("godot-first-run.yml")
    assert "tests/Game.Tests/Game.Tests.csproj" in text, \
        "godot-first-run.yml nie uruchamia testów warstwy silnika"
    assert "dotnet test tests/Game.Tests" in text, text[:0]


def test_no_other_workflow_tries_to_run_the_engine_tests():
    """Kontrola negatywna: gdyby wołał je workflow bez Godota, padłby na SDK."""
    for name in _workflows():
        if name == "godot-first-run.yml":
            continue
        assert "Game.Tests" not in _text(name), name


def test_a_workflow_with_path_filters_watches_every_test_project_it_runs():
    """Workflow, który URUCHAMIA projekt testowy, musi się odpalać przy jego zmianie.

    ZMIERZONE 02.09.2026 na PR #116: gałąź dotykała wyłącznie `tests/Game.Tests/**`
    i dostała DWIE bramki — `sim` i `tools`. `godot-first-run.yml`, czyli jedyny job
    wykonujący te testy, w ogóle nie wystartował, bo `tests/Game.Tests` nie było
    w jego `paths`. Zmiana w testach warstwy silnika poszłaby do `main`
    NIEURUCHOMIONA, a PR wyglądałby na zielony.

    Poprzedni PR (#114) przeszedł przez PRZYPADEK: ruszał też sam plik workflow,
    który w filtrze jest.

    Ten sam błąd repozytorium miało już raz w `blender-smoke.yml` przy wąskim
    wzorcu na `tools/ci` — komentarz tamże opisuje go tymi samymi słowami.
    """
    pattern = re.compile(r"dotnet test ([A-Za-z0-9_./-]+)")
    checked = 0
    for name in _workflows():
        document = yaml.safe_load(_text(name))
        triggers = (document.get(True) or document.get("on") or {})
        paths = ((triggers.get("pull_request") or {}) or {}).get("paths")
        if not paths:
            continue  # bez filtra workflow chodzi na każdym PR, więc nie ma czego gubić

        # Tylko KOD, nie komentarze. Pierwsza wersja tego testu skanowała cały plik
        # i zgłosiła `blender-smoke.yml`, bo jego komentarz WSPOMINA
        # `dotnet test tests/Sim.Tests` przy opisie, co robi `doctor.sh`. To ten sam
        # błąd, przed którym ostrzega komentarz przy bramce reguły 9: wzorzec ma
        # celować w kod, a nie wywracać się na własnym opisie.
        code = "\n".join(line for line in _text(name).splitlines()
                         if not line.lstrip().startswith("#"))
        for target in pattern.findall(code):
            # `dotnet test tests/Game.Tests/Game.Tests.csproj` -> katalog projektu
            directory = os.path.dirname(target) or target
            checked += 1
            covered = any(entry.rstrip("/*").rstrip("/") == directory for entry in paths)
            assert covered, (
                f"{name} uruchamia {target}, ale nie ma {directory}/** w paths — "
                "zmiana w tym projekcie nie odpali workflow, który go wykonuje")
    assert checked >= 1, "żaden workflow z filtrem nie uruchamia projektu testowego"


# --- scena zatrzymuje się na stacjach (T-400 etap 3) ---------------------------

def _scene_source():
    with open(os.path.join(ROOT, "src", "Game", "FirstRun.cs"), encoding="utf-8") as handle:
        return handle.read()


def test_the_scene_line_mode_is_driven_by_the_core_not_by_the_scene():
    """Tryb `line` ma WOŁAĆ `LineDrive`, a nie liczyć jazdy po swojemu.

    Gdyby scena liczyła sama, w repozytorium byłyby dwie fizyki jazdy — jedna
    przypięta testami rdzenia, druga nie — i nie dałoby się powiedzieć, która jest
    prawdziwa. Reguła 9 z `CLAUDE.md` broni rdzenia przed silnikiem; ta bramka broni
    w drugą stronę: silnik nie ma prawa mieć własnego modelu.
    """
    text = _scene_source()
    assert "_line!.Step(" in text, "scena nie woła LineDrive.Step"
    assert "new LineDrive(" in text, "scena nie buduje LineDrive"

    branch = text[text.index("if (_lineMode)", text.index("private bool StepOnce()")):]
    branch = branch[:branch.index("_state = _controller.Advance(")]
    assert "_controller.Advance(" not in branch, \
        "gałąź trybu line liczy krok sama zamiast oddać go rdzeniowi"


def test_the_scene_refuses_a_line_run_without_the_exchange_time():
    """Czasu wymiany pasażerów nie podaje żadne źródło (T-312, R-007).

    `DoorCycle` i `LineRunSettings` nie mają dla niego wartości domyślnej i scena
    ma trzymać tę samą linię: woli odmówić uruchomienia, niż podstawić liczbę, która
    potem wyjdzie w nagraniu jako fakt o metrze w Brukseli.
    """
    text = _scene_source()
    assert 'Argument("exchange-s") is null' in text, "scena nie sprawdza braku --exchange-s"
    marker = text.index('Argument("exchange-s") is null')
    assert "Abort(" in text[marker:marker + 400], "brak --exchange-s nie przerywa uruchomienia"


def test_the_workflow_gates_on_what_the_line_run_did_not_that_it_started():
    """Uruchomienie bez błędu potrafi dojechać do końca osi nie zatrzymawszy się ani razu.

    Bramka musi więc czytać RAPORT i porównywać liczbę zatrzymań z liczbą stacji,
    a nie sprawdzać kod wyjścia sceny. Bez tego cały etap 3 byłby zielony także wtedy,
    gdyby `LineDrive` przestał zatrzymywać skład.
    """
    text = _text("godot-first-run.yml")
    assert "--drive=line" in text, "workflow nie uruchamia sceny w trybie line"
    assert "--line-report=" in text, "workflow nie żąda raportu z przejazdu"

    step = [s for s in _steps(text) if "--line-report=" in s]
    assert len(step) == 1, len(step)
    body = step[0]

    # Sprawdzane jest POROWNANIE, a nie obecność nazw. Pierwsza wersja tej bramki
    # szukała samych `report["calls"]` i `report["stations_on_axis"]` — i przechodziła
    # także wtedy, gdy warunek porównujący je został zastąpiony przez `if False`,
    # bo obie nazwy zostawały w komunikacie obok. Kontrola negatywna to pokazała.
    for needle in ("calls != stations - 1",
                   'report["total_distance_m"] <= 0.0',
                   'report["dwell_seconds"] <= 0.0',
                   'abs(stop["stop_error_m"]) > window',
                   'stop["departure_s"] > stop["arrival_s"]',
                   "sys.exit(1)"):
        assert needle in body, f"bramka nie sprawdza: {needle}"

    assert body.index("calls != stations - 1") < body.index("sys.exit(1)"), \
        "porównanie stoi za wyjściem z błędem — nie ma jak go wywołać"


def test_the_line_gate_has_a_negative_control_that_can_fail_it():
    """Bramka, która nie umie paść, nie jest bramką — cała lekcja audytu z 02.09.2026.

    Kontrola negatywna psuje raport o jedno zatrzymanie i wymaga, żeby ta sama
    reguła go odrzuciła.
    """
    text = _text("godot-first-run.yml")
    control = [s for s in _steps(text) if "line_bad.json" in s]
    assert len(control) == 1, len(control)
    body = control[0]
    assert 'report["calls"] -= 1' in body, "kontrola nie psuje liczby zatrzymań"
    assert "kontrola negatywna przeszła" in body, "kontrola nie ma komunikatu o własnej porażce"
