#!/usr/bin/env python3
"""Testy odporności workflow CI.

Powód: 02.09.2026 krok instalacji Blendera zawiesił się trzy razy na trzech różnych
runnerach, za każdym razem przed uruchomieniem ciała testu. Te testy pilnują, żeby
poprawka nie wyparowała po cichu przy następnej edycji workflow.
"""
import glob
import os
import re

import yaml

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
WORKFLOWS = os.path.join(ROOT, ".github", "workflows")
ACTIONS = os.path.join(ROOT, ".github", "actions")
HELPER = os.path.join(ROOT, "tools", "ci", "apt_install.sh")
INSTALLER = os.path.join(ROOT, "tools", "ci", "blender_install.sh")

#: Akcje lokalne, w których stoi JEDNA implementacja reguł powtarzanych wcześniej
#: w każdym workflow. Testy niżej idą ZA tym odnośnikiem, a nie uznają go za dowód:
#: krok `uses:` wskazujący na akcję bez treści przechodziłby inaczej tak samo dobrze.
CLEAN_ACTION = "./.github/actions/check-workspace"
PROBE_ACTION = "./.github/actions/probe-tools"


def _workflows():
    return sorted(f for f in os.listdir(WORKFLOWS) if f.endswith((".yml", ".yaml")))


def _text(name):
    return open(os.path.join(WORKFLOWS, name), encoding="utf-8").read()


def _action(reference):
    """Sparsowana akcja lokalna wskazana przez `uses:` w kroku workflow."""
    relative = reference[len("./.github/actions/"):]
    path = os.path.join(ACTIONS, relative, "action.yml")
    assert os.path.isfile(path), f"krok wskazuje na akcję, której nie ma: {reference}"
    return yaml.safe_load(open(path, encoding="utf-8").read())


def _action_body(reference):
    """Treść wszystkich `run:` akcji, sklejona — czyli to, co naprawdę się wykona."""
    action = _action(reference)
    return "\n".join(str(step.get("run", "")) for step in action["runs"]["steps"])


def _action_files():
    out = []
    for entry in sorted(os.listdir(ACTIONS)) if os.path.isdir(ACTIONS) else []:
        candidate = os.path.join(ACTIONS, entry, "action.yml")
        if os.path.isfile(candidate):
            out.append(candidate)
    return out


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
    # Siedem, odkąd doszedł `material-style-smoke.yml` (bramka T-902). Liczba jest
    # tu po to, żeby workflow, który PRZESTAŁ instalować biblioteki, nie wypadł
    # z pętli po cichu — pętla po samych znalezionych krokach przeszłaby wtedy
    # pusta i zielona.
    assert checked == 7, f"oczekiwano siedmiu kroków instalacji, znaleziono {checked}"


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
    # Siedem, odkąd doszedł `material-style-smoke.yml` (bramka T-902). Liczba jest
    # tu po to, żeby workflow, który PRZESTAŁ instalować biblioteki, nie wypadł
    # z pętli po cichu — pętla po samych znalezionych krokach przeszłaby wtedy
    # pusta i zielona.
    assert checked == 7, f"oczekiwano siedmiu kroków instalacji, znaleziono {checked}"


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
            # Zestawy niosą już tylko BIBLIOTEKI systemowe — sam Blender przychodzi
            # z przypiętego tarballa (`test_ci_blender_workflows_install_the_pinned_...`).
            # Warunek zostaje mocny: zestaw musi dawać kontekst EGL, bo bez niego
            # Blender startuje i wywraca się dopiero przy pierwszym renderze.
            assert "libegl1" in packages, (declared, packages)
            assert "blender" not in packages, (declared, packages,
                                               "zestaw apt znów instaluje Blendera")
    # Siedem, odkąd doszedł `material-style-smoke.yml` (bramka T-902). Liczba jest
    # tu po to, żeby workflow, który PRZESTAŁ instalować biblioteki, nie wypadł
    # z pętli po cichu — pętla po samych znalezionych krokach przeszłaby wtedy
    # pusta i zielona.
    assert checked == 7, f"oczekiwano siedmiu kroków instalacji, znaleziono {checked}"


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
    paths = []
    for directory in (WORKFLOWS, os.path.join(ROOT, "tools", "ci")):
        paths += [os.path.join(directory, n) for n in sorted(os.listdir(directory))
                  if n.endswith((".yml", ".yaml", ".sh"))]
    # Akcje lokalne też, i to nie z ostrożności: po wydzieleniu 04.09.2026 właśnie
    # tam przeniosła się treść kroków, które ten test dotąd sprawdzał w workflowach.
    # Bez tej linijki reguła zostałaby zapisana, a jej przedmiot wyprowadziłby się
    # poza zasięg — dokładnie ten sposób, w jaki bramki cichną.
    paths += _action_files()
    for path in paths:
        text = open(path, encoding="utf-8").read()
        for number, line in enumerate(text.splitlines(), 1):
            # Komentarze pomijane, i to nie z pobłażliwości: ta reguła jest w tym
            # repozytorium OPISANA w komentarzach — akcja `probe-tools` wyjaśnia
            # w prozie, dlaczego nie używa `ldconfig -p | grep -q`, i wymienia przy
            # tym `| head` jako rodzinę tego samego wyścigu. Bramka grepująca po
            # całym pliku łapie własne uzasadnienie i każe usunąć wyjaśnienie,
            # zamiast kodu. Ta sama pułapka, co przy bramkach `prune-merged-branches`.
            # Dotyczy to również komentarzy shellowych wewnątrz `run: |`, bo `| head`
            # za `#` też się nie wykonuje.
            if line.lstrip().startswith("#"):
                continue
            if re.search(r"\|\s*head\b", line):
                offenders.append(f"{os.path.basename(os.path.dirname(path))}/"
                                 f"{os.path.basename(path)}:{number}")
    assert not offenders, offenders


BLENDER_WORKFLOWS = ("blender-smoke.yml", "tunnel-alignment.yml", "m7-shell.yml",
                     "visual-regression.yml", "godot-first-run.yml",
                     "station-details.yml", "material-style-smoke.yml")


def test_ci_blender_workflows_install_the_pinned_blender_not_whatever_apt_has():
    """Blender przychodzi z PRZYPIĘTEGO tarballa, a nie z tego, co ma dystrybucja.

    Poprzednia wersja tego testu wymagała, żeby zestaw pakietów zawierał `blender`
    i `python3-numpy`, i jest tu przepisana, a nie dopisana obok, bo tamta reguła
    już nie obowiązuje. Powód nie jest kosmetyczny: `apt` na Ubuntu 24.04 daje 4.0.2
    do końca życia wydania, a 4.0.2 renderuje LEGACY EEVEE. Baseline projektu jest
    z EEVEE Next i te dwie generacje nie są porównywalne — `enum_items` dla `engine`
    zwraca `['BLENDER_EEVEE']` na obu, więc nazwa silnika ich nie odróżnia
    (`tools/visual/capture_plan.py`, `EEVEE_NEXT_SINCE`). Kosztowało to dwie czerwone
    bramki `tunnel-alignment` (L1_B i L2_E) 02.09.2026.

    `python3-numpy` wypadł z zestawu, bo był potrzebny WYŁĄCZNIE dla Blendera z apt,
    który linkuje się z systemowym Pythonem. Tarball wozi własny Python 3.13 i numpy 2.3,
    a żaden moduł w `tools/` ani `src/` nie importuje numpy poza Blenderem.
    """
    for name in BLENDER_WORKFLOWS:
        steps = _steps(_text(name))

        # Krok, który skrypt URUCHAMIA, nie taki, który go tylko wspomina w komentarzu.
        # Pierwsza wersja tego warunku brała `"blender_install.sh" in step` i trafiała
        # w komentarz kroku sondy — test padał na kroku, który nigdy nie miał
        # eksportować `BLENDER_BIN`.
        installer = [s for s in steps if "bash tools/ci/blender_install.sh" in s]
        assert installer, f"{name}: brak kroku uruchamiającego tools/ci/blender_install.sh"
        assert 'BLENDER_BIN=' in installer[0], \
            f"{name}: krok instalacji nie eksportuje BLENDER_BIN, więc skrypty go nie zobaczą"

        apt = [s for s in steps if "apt_install.sh" in s]
        assert apt, f"{name}: brak kroku instalującego biblioteki renderu"
        declared = _declared_set(apt[0])
        packages = open(os.path.join(PACKAGE_SETS, declared + ".txt"), encoding="utf-8").read()
        assert "libegl1" in packages, (name, declared, "brak kontekstu EGL")
        assert "\nblender\n" not in packages, \
            (name, declared, "zestaw apt znów instaluje Blendera, czyli 4.0.2")


def test_ci_blender_version_is_pinned_in_exactly_one_place():
    """Numer wersji i suma kontrolna są w jednym pliku, nie w pięciu workflowach.

    Pięć kopii numeru to pięć okazji, żeby jedna została w tyle i żeby baseline
    został porównany z klatką z innego silnika EEVEE.
    """
    pin = os.path.join(os.path.dirname(PACKAGE_SETS), "blender-version.txt")
    assert os.path.isfile(pin), pin
    text = open(pin, encoding="utf-8").read()
    version = re.search(r"(?m)^version=(.+)$", text)
    sha = re.search(r"(?m)^sha256=([0-9a-f]{64})$", text)
    assert version, "plik pinu nie podaje 'version='"
    assert sha, "plik pinu nie podaje 'sha256=' o długości 64 znaków hex"

    # Żaden workflow nie ma prawa wpisywać numeru wersji u siebie.
    for name in BLENDER_WORKFLOWS:
        assert version.group(1) not in _text(name), \
            f"{name}: numer wersji Blendera wpisany w workflow zamiast czytany z pinu"


def test_ci_no_workflow_uses_blender_before_installing_it():
    """Krok, który woła `$BLENDER_BIN`, musi stać PO kroku, który go ustawia.

    Pod `set -euo pipefail` puste `BLENDER_BIN` kończy krok błędem, więc awaria byłaby
    głośna — ale byłaby też myląca: „command not found" kilkanaście kroków od powodu,
    czyli od przestawionej kolejności. Ten test nazywa powód wprost.
    """
    for name in BLENDER_WORKFLOWS:
        document = yaml.safe_load(_text(name))
        steps = list(document["jobs"].values())[0]["steps"]
        installer = None
        for index, step in enumerate(steps):
            if "bash tools/ci/blender_install.sh" in str(step.get("run", "")):
                installer = index
                break
        assert installer is not None, f"{name}: brak kroku instalacji"
        for index, step in enumerate(steps):
            run = str(step.get("run", ""))
            if "BLENDER_BIN" in run and "blender_install.sh" not in run:
                assert index > installer, (
                    f"{name}: krok {index} '{step.get('name')}' woła BLENDER_BIN, "
                    f"a instalacja jest dopiero w kroku {installer}")


def test_ci_blender_installer_verifies_the_checksum_and_stays_out_of_the_workspace():
    """Pobranie bez sprawdzenia sumy nie jest instalacją, tylko nadzieją.

    Archiwum ucięte w połowie rozpakowuje się częściowo i wywraca się dopiero
    w środku renderu, kilkanaście kroków od powodu. Drugi warunek jest z tej samej
    rodziny co `test_godot_lives_outside_the_workspace_that_checkout_wipes`:
    `actions/checkout` robi `git clean -ffdx`, a `-x` obejmuje pliki ignorowane.
    """
    script = open(os.path.join(os.path.dirname(PACKAGE_SETS), "blender_install.sh"),
                  encoding="utf-8").read()
    # Komentarze SĄ ODCINANE przed sprawdzaniem. Bez tego test przechodzi na
    # samej wzmiance w komentarzu: kontrola negatywna, która zamieniła
    # `${RUNNER_TOOL_CACHE:-...}` na inną zmienną, została NIEZŁAPANA właśnie
    # dlatego, że nazwa dalej stała w komentarzu obok.
    code = "\n".join(line for line in script.splitlines()
                     if not line.lstrip().startswith("#"))

    # Sam napis. Że suma cokolwiek ODRZUCA, pilnuje
    # `test_ci_blender_installer_refuses_a_tarball_whose_checksum_does_not_match` —
    # ten warunek przechodził z dopisanym `|| true`.
    assert "sha256sum -c" in code, "instalator nie sprawdza sumy kontrolnej"
    assert re.search(r"\$\{RUNNER_TOOL_CACHE:-", code), \
        "instalator nie czyta RUNNER_TOOL_CACHE, więc Blender może wylądować w workspace"
    assert re.search(r"\$\{GITHUB_WORKSPACE:?-?[^}]*\}|\$GITHUB_WORKSPACE", code), \
        "instalator nie sprawdza, czy katalog docelowy nie wpadł do workspace"
    # Sonda musi czytać WERSJĘ, nie obecność: `command -v blender` na maszynie
    # z Blenderem z apt znalazłby 4.0.2 i uznał środowisko za gotowe.
    assert "installed_version" in code and '--version' in code, \
        "instalator nie porównuje wersji zastanej z przypiętą"
    assert 'command -v blender' not in code, \
        "instalator sonduje obecność Blendera zamiast jego wersji"


#: Zmyślona wersja atrapy Blendera. NIGDY nie będzie prawdziwym wydaniem, bo nazwa
#: tarballa w `/tmp` jest w instalatorze zaszyta i pod prawdziwym numerem test
#: potrafiłby wejść w drogę czyjemuś pobieraniu. `installed_version` czyta
#: z pierwszej linii `--version` wyłącznie cyfry i kropki, więc atrapa musi się
#: przedstawiać dokładnie tym numerem, żeby przebieg zgodny doszedł do końca.
FAKE_BLENDER_VERSION = "0.0.1"


def _fake_blender_archive(root):
    """Poprawny `.tar.xz` z atrapą `blender` w środku. Zwraca (ścieżka, suma).

    Atrapa musi być PRAWDZIWYM archiwum, nie śmieciem: na śmieciu wywraca się
    `tar -xJf`, więc skrypt padłby również z rozbrojoną sumą i kontrola negatywna
    nie zmierzyłaby niczego. Musi też być rozpakowywalna DO KOŃCA i przedstawiać
    się przypiętym numerem — z `|| true` po `sha256sum` instalator ma dojść do
    `exit 0` i wypisać ścieżkę, żeby test miał co złapać.
    """
    import hashlib
    import tarfile

    tree = f"blender-{FAKE_BLENDER_VERSION}-linux-x64"
    payload = os.path.join(root, "payload", tree)
    os.makedirs(payload)
    binary = os.path.join(payload, "blender")
    with open(binary, "w", encoding="utf-8") as handle:
        handle.write("#!/usr/bin/env bash\n"
                     f'echo "Blender {FAKE_BLENDER_VERSION}"\n'
                     'echo "\tbuild date: atrapa testowa"\n')
    os.chmod(binary, 0o755)

    archive = os.path.join(root, "atrapa.tar.xz")
    with tarfile.open(archive, "w:xz") as tar:
        tar.add(payload, arcname=tree)
    with open(archive, "rb") as handle:
        return archive, hashlib.sha256(handle.read()).hexdigest()


def _run_blender_installer(root, label, sha256, archive, workspace=None):
    """Uruchamia PRAWDZIWY `blender_install.sh` obok podstawionego pinu, bez sieci.

    Skrypt czyta pin z katalogu, w którym sam leży (`$HERE/blender-version.txt`),
    więc podmiana sumy to kopia skryptu BAJT W BAJT do katalogu tymczasowego
    i własny pin obok — plik w repozytorium zostaje nietknięty.

    Sieci nie ma: `curl` jest podmieniony w PATH i pod ścieżkę z `-o` podkłada
    atrapę zamiast 366 MB z download.blender.org. Shim zapisuje też fakt wywołania,
    bo „skrypt padł" bez „curl został wywołany" nie dowodzi, że wykonała się
    ścieżka SUMY, a nie cokolwiek wcześniej.
    """
    import shutil
    import subprocess

    base = os.path.join(root, label)
    home = os.path.join(base, "home")
    binroot = os.path.join(base, "bin")
    ci = os.path.join(base, "ci")
    cache = os.path.join(workspace, "_tool") if workspace else os.path.join(base, "cache")
    for directory in (home, binroot, ci, cache):
        os.makedirs(directory, exist_ok=True)

    script = os.path.join(ci, "blender_install.sh")
    shutil.copyfile(INSTALLER, script)
    with open(os.path.join(ci, "blender-version.txt"), "w", encoding="utf-8") as handle:
        handle.write(f"version={FAKE_BLENDER_VERSION}\nsha256={sha256}\n")

    log = os.path.join(base, "curl-zostal-wolany")
    shim = os.path.join(binroot, "curl")
    with open(shim, "w", encoding="utf-8") as handle:
        handle.write('#!/usr/bin/env bash\n'
                     'echo "$@" >> "$CURL_LOG"\n'
                     'out=""\n'
                     'while [ $# -gt 0 ]; do\n'
                     '    [ "$1" = "-o" ] && out="$2"\n'
                     '    shift\n'
                     'done\n'
                     '[ -n "$out" ] || exit 9\n'
                     'cp "$ARCHIVE" "$out"\n')
    os.chmod(shim, 0o755)

    env = dict(os.environ)
    env.pop("GITHUB_WORKSPACE", None)
    if workspace:
        env["GITHUB_WORKSPACE"] = workspace
    env.update(PATH=binroot + os.pathsep + env.get("PATH", ""),
               HOME=home, RUNNER_TOOL_CACHE=cache,
               CURL_LOG=log, ARCHIVE=archive, LC_ALL="C")

    result = subprocess.run(["bash", script], env=env, capture_output=True, text=True)
    unpacked = os.path.join(cache, "metro-blender", FAKE_BLENDER_VERSION)
    return result, unpacked, os.path.exists(log)


def test_ci_blender_installer_refuses_a_tarball_whose_checksum_does_not_match():
    """Bramka na ZACHOWANIE instalatora, nie na napis `sha256sum -c` w jego kodzie.

    Zmierzone 04.09.2026: dopisanie `|| true` po `sha256sum -c -` w
    `tools/ci/blender_install.sh` (wiersz 82) przechodziło CAŁY zestaw, 1335/1335.
    `test_..._verifies_the_checksum_and_stays_out_of_the_workspace` pyta wyłącznie,
    czy napis stoi w pliku, a suma z `tools/ci/blender-version.txt` była sprawdzana
    tylko pod kątem formatu (64 znaki hex) — cała ścieżka „przypięta wersja
    Blendera" nie miała ani jednej bramki wykonawczej. Podmieniony tarball
    rozpakowywał się dalej, a joby chodzą na maszynie właściciela.

    Trzy przebiegi, bo żaden z nich osobno nie mierzy tego, co mówi:

    1. suma ZGODNA — skrypt musi dojść do końca i wypisać ścieżkę do pliku
       wykonywalnego. Bez tego „padł" z przebiegu 2 mógłby pochodzić z zepsutego
       shima albo z byle czego w otoczeniu, a nie z sumy.
    2. suma NIEZGODNA — skrypt musi PAŚĆ i NIE zostawić rozpakowanego katalogu.
       Sam kod wyjścia tu nie wystarcza: przy `|| true` atrapa rozpakowuje się
       i przedstawia przypiętym numerem, więc instalator kończy się ZEREM —
       łapie go dopiero istnienie katalogu i kodu wyjścia razem.
    3. katalog docelowy W WORKSPACE — skrypt musi paść PRZED pobraniem
       (shim nietknięty), bo `git clean -ffdx` z checkoutu i tak by to skasował.

    Czego ta bramka NIE obejmuje: że suma w pinie jest sumą PRAWDZIWEGO archiwum
    z download.blender.org. Tego nie da się sprawdzić bez sieci — zestaw
    `tools/tests/test_all.py` chodzi offline i żaden inny jego test nie wychodzi
    na zewnątrz. Zejście po `blender-<wersja>.sha256` z serwera Blender Foundation
    zamieniłoby te testy w bramkę zależną od cudzego serwera; poprawność samego
    numeru zostaje przy człowieku, który podnosi pin.
    """
    import shutil
    import tempfile

    root = tempfile.mkdtemp(prefix="metro-blender-pin-")
    # Nazwa tarballa jest w instalatorze zaszyta na `/tmp`, a przy odmowie skrypt
    # nie dochodzi do `rm -f` — sprzątamy po nim sami.
    leftover = f"/tmp/blender-{FAKE_BLENDER_VERSION}-linux-x64.tar.xz"
    try:
        archive, digest = _fake_blender_archive(root)
        wrong = "0" * 63 + "1"
        assert wrong != digest

        good, unpacked, called = _run_blender_installer(root, "zgodna", digest, archive)
        assert good.returncode == 0, (good.returncode, good.stderr)
        assert called, "shim `curl` nie został wywołany, więc przebieg nie mierzy pobrania"
        binary = os.path.join(unpacked, f"blender-{FAKE_BLENDER_VERSION}-linux-x64", "blender")
        assert good.stdout.strip() == binary, (good.stdout, binary)
        assert os.access(binary, os.X_OK), binary

        bad, unpacked, called = _run_blender_installer(root, "niezgodna", wrong, archive)
        assert called, "shim `curl` nie został wywołany, więc odmowa nie jest odmową sumy"
        assert bad.returncode != 0, (
            "instalator z niezgodną sumą zakończył się zerem — suma nie bramkuje niczego")
        assert "FAILED" in bad.stderr, bad.stderr
        assert not os.path.exists(unpacked), (
            f"instalator rozpakował archiwum o niezgodnej sumie do {unpacked}")

        workspace = os.path.join(root, "w-workspace", "workspace")
        os.makedirs(workspace)
        inside, unpacked, called = _run_blender_installer(
            root, "w-workspace", digest, archive, workspace=workspace)
        assert inside.returncode == 1, (inside.returncode, inside.stderr)
        assert "W WORKSPACE" in inside.stderr, inside.stderr
        assert not called, "instalator pobrał 366 MB do katalogu, który skasuje checkout"
        assert not os.path.exists(unpacked), unpacked
    finally:
        shutil.rmtree(root, ignore_errors=True)
        if os.path.exists(leftover):
            os.unlink(leftover)


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
    # Lista przeprowadziła się 03.09.2026 do `RunPlan.cs`, razem z całym
    # rozstrzyganiem wiersza poleceń — bo tamten plik nie importuje Godota i daje
    # się przetestować jednostkowo. Ten test celuje w nowy adres, a nie został
    # usunięty: porównanie listy z tym, czym CI WOŁA scenę, jest czymś, czego
    # test jednostkowy nie zrobi, bo nie widzi workflow.
    source = open(os.path.join(ROOT, "src", "Game", "RunPlan.cs"), encoding="utf-8").read()
    block = re.search(r"KnownArguments\s*=\s*\{(.*?)\};", source, re.S)
    assert block, "lista znanych argumentów zniknęła z RunPlan.cs"
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


def test_godot_argument_gate_stays_testable_outside_the_engine():
    """Rozstrzyganie argumentów sceny ma zostać W PLIKU BEZ GODOTA i mieć testy.

    Ten test jest PRZEPISANY, nie dopisany obok, i warto powiedzieć dlaczego.
    Poprzednia wersja sprawdzała obecność NAPISÓW w `FirstRun.cs`:
    `"Array.IndexOf(KnownArguments, name) < 0" in source`. Taki test nie odróżnia
    kodu wykonywanego od zakomentowanego i nie dotyka ani jednej gałęzi — a był
    JEDYNYM, co pilnowało 847-liniowej klasy, bo `grep -rn "FirstRun" tests/`
    nie dawał ani jednego trafienia.

    Od 03.09.2026 te gałęzie mają prawdziwe testy jednostkowe (`RunPlanTests.cs`,
    23 przypadki), więc ten test nie musi już udawać, że je sprawdza. Pilnuje
    natomiast czegoś, czego test jednostkowy nie wyrazi: że logika NIE WRÓCI pod
    Godota, bo wtedy przestałaby być testowalna i wszystko zaczęłoby się od nowa.
    """
    plan_path = os.path.join(ROOT, "src", "Game", "RunPlan.cs")
    assert os.path.isfile(plan_path), "RunPlan.cs zniknął — rozstrzyganie wróciło pod Godota"
    plan = open(plan_path, encoding="utf-8").read()

    assert "using Godot" not in plan, \
        "RunPlan.cs zaczął importować Godota — testy jednostkowe przestaną go widzieć"
    assert "KnownArguments" in plan and "KnownViews" in plan
    # Bramki, nie napisy: `TryParse` zamiast `Parse`, bo `double.Parse` w środku
    # `_Ready` rzucał wyjątkiem, `_shotPath` było już ustawione, a `_Process`
    # kręciło się w nieskończoność aż do wypalenia `timeout-minutes` w CI.
    assert "double.Parse(" not in plan and "long.Parse(" not in plan, \
        "parsowanie bez TryParse wraca do zawieszania przebiegu"
    assert "double.IsFinite" in plan, \
        "TryParse sam przyjmuje Infinity i NaN — bez IsFinite wraca pętla bez końca"

    tests_path = os.path.join(ROOT, "tests", "Game.Tests", "RunPlanTests.cs")
    assert os.path.isfile(tests_path), "RunPlan stracił testy jednostkowe"
    tests = open(tests_path, encoding="utf-8").read()
    cases = tests.count("[TestMethod]")
    assert cases >= 20, f"RunPlanTests ma tylko {cases} przypadków"

    # Scena nadal musi umieć zatrzymać pętlę klatek — to jest po stronie Godota
    # i zostaje w `FirstRun.cs`.
    scene = open(os.path.join(ROOT, "src", "Game", "FirstRun.cs"), encoding="utf-8").read()
    assert "ExitUnknownArgument" in scene and "ExitBadArgumentValue" in scene
    assert "_aborted" in scene, "brak flagi zatrzymującej pętlę klatek"
    assert "RunPlan.Parse(" in scene, "scena przestała wołać RunPlan"


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

        # Od 04.09.2026 ten krok NIE jest kopią w workflow, tylko odnośnikiem do
        # jednej akcji lokalnej. Test idzie ZA odnośnikiem, bo sama nazwa kroku
        # niczego nie dowodzi: `- name: Workspace jest czysty` wskazujące na akcję
        # bez treści przechodziłoby tak samo dobrze. Zmierzone przy tej zmianie —
        # poprzednia wersja tego testu sprawdzała WYŁĄCZNIE nazwę i po wydzieleniu
        # przeszła bez jednej modyfikacji, choć cała treść bramki wyprowadziła się
        # do innego pliku.
        document = yaml.safe_load(text)
        references = [str(s.get("uses", "")) for job in document["jobs"].values()
                      for s in job["steps"]]
        assert CLEAN_ACTION in references, \
            f"{name}: krok czystego workspace nie woła {CLEAN_ACTION}"
        # `clean: false` wyłączyłoby jedyny mechanizm, który realnie sprząta.
        # Sprawdzane na SPARSOWANYM YAML-u, nie gremem po tekście: komentarz przy
        # tym kroku sam zawiera napis `clean: false`, więc wersja tekstowa wywracała
        # się na własnym opisie — ta sama pułapka, co przy bramce reguły 9.
        for step in yaml.safe_load(text)["jobs"][next(iter(yaml.safe_load(text)["jobs"]))]["steps"]:
            if str(step.get("uses", "")).startswith("actions/checkout"):
                assert (step.get("with") or {}).get("clean") is not False, \
                    f"{name}: checkout z clean: false"
    assert not missing, f"workflow bez bramki czystego workspace: {missing}"


def test_no_workflow_reinlines_what_the_local_actions_now_own():
    """Reguła powtórzona w dziesięciu plikach wraca do dziesięciu plików sama.

    Do 04.09.2026 kontrola czystego workspace stała w DZIESIĘCIU workflowach
    (w dziewięciu bajt w bajt, w jednym skrócona), a sonda narzędzi w SIEDMIU
    (w sześciu bajt w bajt). Dziesiąta kopia sondy powstała tego samego dnia przez
    skopiowanie bloku z sąsiedniego workflow — czyli dokładnie tym mechanizmem,
    przed którym ten test ma bronić.

    Wydzielenie do akcji lokalnej samo tego nie utrzyma: następny workflow równie
    łatwo wklei blok z powrotem, a wszystkie pozostałe bramki będą wtedy zielone.
    Ten test pyta o jedno: czy treść, która ma jednego właściciela, nie stoi znowu
    w workflow.
    """
    # Fragmenty CIAŁA, nie nazwy kroków. Nazwa zostaje w workflow i ma zostać — to ona
    # mówi czytającemu logi, co się właśnie dzieje.
    #
    # Lista jest WYPROWADZONA Z POMIARU, nie z intuicji. Pierwsza wersja miała tu
    # `ldconfig -p` jako własność sondy i test od razu wskazał siedem workflowów —
    # słusznie co do faktu, błędnie co do wniosku. Tamto `ldconfig -p | grep -E` stoi
    # w kroku `Install render libraries` i jest BRAMKĄ PO INSTALACJI, czyli zupełnie
    # inną robotą niż sonda przed nią: sprawdza, że apt naprawdę położył biblioteki.
    # Wpisanie go tutaj kazałoby usunąć działającą bramkę w imię porządków.
    #
    # Zostają fragmenty, które są wyłączne — sprawdzone: żaden nie występuje dziś
    # w treści kroków ani jednego workflow.
    owned = (
        ('stale=""', CLEAN_ACTION),
        ("::error::wyjścia z poprzedniego przebiegu", CLEAN_ACTION),
        ("MUST_BE_ABSENT", CLEAN_ACTION),
        ("libs=present", PROBE_ACTION),
        ("libs=missing", PROBE_ACTION),
        ("catalogue=", PROBE_ACTION),
    )
    offenders = []
    for name in _workflows():
        document = yaml.safe_load(_text(name))
        bodies = "\n".join(str(step.get("run", ""))
                           for job in document["jobs"].values()
                           for step in job["steps"])
        # Liczy się TREŚĆ KROKÓW `run:`, a nie cały plik: komentarz w workflow wolno
        # napisać o czymkolwiek, a właśnie komentarze odsyłają do tych akcji.
        for fragment, owner in owned:
            if fragment in bodies:
                offenders.append(f"{name}: {fragment!r} należy do {owner}")
    assert not offenders, offenders


def test_the_local_actions_carry_the_rule_they_took_over():
    """Akcja bez treści przechodzi przez każdy test, który pyta tylko o `uses:`.

    Ten test jest drugą połową poprzedniego: tam sprawdza się, że reguły NIE MA
    w workflowach, tu — że JEST tam, gdzie się przeniosła. Bez tej pary da się
    przejść całą suitę z akcją, która nie robi nic.
    """
    clean = _action_body(CLEAN_ACTION)
    assert 'stale=""' in clean, "akcja nie zbiera listy przetrwałych katalogów"
    assert "exit 1" in clean, "akcja nie przewraca kroku, gdy coś przetrwało"
    assert "::error::" in clean, "akcja nie zgłasza błędu w formacie, który GitHub pokaże"
    # Kontrola czystości NIE MOŻE sprzątać. `rm -rf` nie odróżnia „posprzątane"
    # od „checkout przestał sprzątać", a to drugie jest tym, co ma wyjść na wierzch.
    assert "rm -rf" not in clean, "akcja sprząta, zamiast sprawdzać"

    probe = _action_body(PROBE_ACTION)
    assert "ldconfig" in probe, "akcja sondy nie pyta o biblioteki"
    assert "command -v" in probe, "akcja sondy nie pyta o polecenia"
    assert "libs=present" in probe and "libs=missing" in probe, \
        "akcja sondy nie ustawia wyjścia, na które patrzą warunki w workflowach"

    # Wyjście musi być ZADEKLAROWANE, inaczej `steps.tools.outputs.libs` jest puste
    # i każdy warunek `== 'missing'` wychodzi fałszywy — czyli instalacja nigdy się
    # nie odpali, a job padnie dopiero na braku biblioteki, kilka kroków dalej.
    declared = _action(PROBE_ACTION).get("outputs") or {}
    assert "libs" in declared, "akcja sondy nie deklaruje wyjścia `libs`"
    assert "steps.probe.outputs.libs" in str(declared["libs"].get("value")), \
        "wyjście `libs` nie jest podłączone do kroku sondującego"


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
        assert probe, f"{name}: brak kroku sondującego biblioteki renderu"
        # Sonda pyta o BIBLIOTEKI, nie o Blendera, i to jest zmiana świadoma.
        # `command -v blender` na maszynie, która kiedykolwiek dostała Blendera z apt,
        # znajduje 4.0.2 i uznaje środowisko za gotowe — a to legacy EEVEE. Wersję
        # sprawdza `tools/ci/blender_install.sh`, który jest własną sondą.
        # Treść sondy leży od 04.09.2026 w akcji lokalnej, więc test czyta ją stamtąd.
        # `probe[0]["run"]` przestało istnieć i to jest właściwy moment, żeby test
        # poszedł za odnośnikiem, a nie żeby warunek złagodzić do „jakoś sonduje".
        assert str(probe[0].get("uses", "")) == PROBE_ACTION, \
            f"{name}: sonda nie woła {PROBE_ACTION}"
        body = _action_body(PROBE_ACTION)
        assert "ldconfig" in body, "akcja sondy nie sprawdza bibliotek renderu"
        assert "command -v blender" not in body, \
            "akcja sondy pyta o obecność Blendera zamiast o jego wersję"
        # Biblioteka, o którą pyta TEN workflow, musi być podana w `with:` — inaczej
        # akcja z domyślnie pustym wejściem nie sonduje niczego i mówi `present`.
        wanted = (probe[0].get("with") or {})
        assert wanted.get("libraries"), \
            f"{name}: sonda nie podaje ani jednej biblioteki, więc zawsze zwróci present"

        for step in steps:
            run = str(step.get("run", ""))
            if "apt_install.sh" in run or (step.get("uses", "").startswith("actions/cache")
                                           and "metro-apt" in str(step)):
                assert step.get("if") == "steps.tools.outputs.libs == 'missing'", \
                    f"{name}: krok '{step.get('name')}' nie jest zabramkowany sondą"
            # Instalator Blendera NIE jest bramkowany z workflow i tak ma być:
            # sam czyta pin, sam porównuje wersję i przy zgodzie kończy w 0,12 s.
            if "blender_install.sh" in run:
                assert step.get("if") is None, \
                    f"{name}: instalator Blendera jest własną sondą i nie ma być bramkowany"
    assert checked == 7, checked


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


def test_ci_every_blender_generator_has_a_gate():
    """Każdy generator geometrii w `tools/blender/` musi być wołany przez BRAMKĘ.

    Powód jest wprost z `CLAUDE.md` §5: skrypt bez błędu potrafi wyprodukować pustą
    scenę, więc pokrycie testem jednostkowym przez atrapę `bpy` NIE jest weryfikacją
    generatora — atrapa nigdy nie dotyka Blendera i nie umie wykonać ani jednej
    ścieżki, która wczytuje scenkę.

    Zmierzone 03.09.2026: `station_kit.py` i `detail_markers.py` nie były wołane
    z żadnego workflow ani skryptu w `tools/ci`. Oba generują geometrię, oba noszą
    jawne stałe projektowe, i oba miały bramki ODMOWY, których nie sprawdzał nikt:
    `--only-station` z literówką, okno bez znaczników, słupek wchodzący w skrajnię.

    GRANICA REGUŁY JEST WĄSKA I TO JEST ŚWIADOME. Obejmuje `tools/blender/`, a nie
    każde CLI w `tools/`. Czternaście modułów w `tools/track/` też nie jest wołanych
    z CI i większość z nich SŁUSZNIE: `fetch_gtfs.py`, `fetch_osm_routes.py`
    i `fetch_stib_shapes.py` chodzą po sieci, a `build_alignment.py`,
    `crosscheck_alignment.py`, `inspire_rail.py`, `network_chainage.py`,
    `normalize_stops.py`, `surface_sections.py` i `timetable.py` potrzebują danych,
    których w repozytorium nie ma (reguła 8). Rozszerzenie tej reguły na `tools/track/`
    wymagałoby sieci w CI, więc byłoby żądaniem, nie bramką.
    """
    # Kryterium: moduł IMPORTUJE `bpy` i ma własne CLI. Obie połowy są konieczne.
    #
    # `bpy`, bo tylko taki moduł produkuje scenę — a §5 mówi właśnie o pustej scenie
    # z bezbłędnego skryptu. `m7_layout.py` ma CLI (`print(report())`), ale nie tyka
    # Blendera i jest importowany przez `m7_shell`, `clearance` i `m7_report`, więc
    # jego kod i tak się wykonuje; żądanie osobnej bramki dla niego byłoby żądaniem,
    # nie regułą. Pierwsza wersja tego testu brała samo CLI i wskazała go jako
    # niepokrytego — słusznie co do faktu, błędnie co do wniosku.
    #
    # CLI, bo moduł bez `__main__` (jak `render_check.py`) jest wołany PRZEZ inny
    # generator i nie ma własnej ścieżki do zabramkowania.
    generators = []
    for path in sorted(glob.glob(os.path.join(ROOT, "tools", "blender", "*.py"))
                       + glob.glob(os.path.join(ROOT, "tools", "visual", "*.py"))):
        source = open(path, encoding="utf-8").read()
        if '__name__ == "__main__"' not in source:
            continue
        if not re.search(r"(?m)^import bpy$", source):
            continue
        generators.append(os.path.relpath(path, ROOT))
    assert len(generators) >= 7, generators

    # Skrypt w `tools/ci`, którego NIE URUCHAMIA żaden workflow, nie jest bramką.
    # To nie jest hipoteza: pierwsza wersja tego testu sklejała po prostu wszystkie
    # skrypty i wszystkie workflowy, więc kontrola negatywna „workflow przestaje
    # wołać skrypt" przeszła NIEZŁAPANA — generator dalej stał w pliku, którego
    # nikt nie odpala. Dlatego najpierw ustalamy, które skrypty są realnie wołane.
    # Liczy się TREŚĆ KROKÓW `run:`, a nie cały YAML. Druga pułapka tej samej
    # rodziny: nazwa generatora stoi też w `paths:`, czyli w WYZWALACZU workflow —
    # a wyzwalacz mówi tylko „odpal się, gdy ten plik się zmieni", nie „uruchom go".
    # Kontrola negatywna „workflow przestaje wołać skrypt" przechodziła NIEZŁAPANA
    # jeszcze raz, właśnie na tym.
    workflows = ""
    for path in sorted(glob.glob(os.path.join(ROOT, ".github", "workflows", "*.yml"))):
        document = yaml.safe_load(open(path, encoding="utf-8"))
        for job in document["jobs"].values():
            for step in job["steps"]:
                workflows += str(step.get("run", "")) + "\n"

    haystack = workflows
    invoked = []
    for path in sorted(glob.glob(os.path.join(ROOT, "tools", "ci", "*.sh"))):
        name = "tools/ci/" + os.path.basename(path)
        if re.search(r"bash\s+" + re.escape(name) + r"\b", workflows):
            invoked.append(name)
            haystack += open(path, encoding="utf-8").read()
    assert len(invoked) >= 5, ("skrypty CI wołane przez workflow: " + ", ".join(invoked))

    missing = [name for name in generators if name not in haystack]
    assert not missing, ("generatory geometrii bez bramki w CI: " + ", ".join(missing)
                         + " (skrypty realnie wołane: " + ", ".join(invoked) + ")")


def test_ci_the_station_details_gate_reads_the_reason_of_every_refusal():
    """Odmowa bez przeczytanego powodu nie jest bramką, tylko awarią.

    `station_details.sh` sprawdza sześć odmów i każda musi spełnić trzy warunki:
    polecenie padło, NIE zostawiło pliku wyjściowego, a w logu stoi konkretna
    diagnoza. Trzeci warunek jest tym, który odróżnia bramkę od „coś się wywaliło":
    bez niego test przechodzi także wtedy, gdy generator pada z zupełnie innego
    powodu — na przykład na literówce w nazwie pliku.

    Ta sama konwencja co negatywy w `blender_smoke.sh`.
    """
    script = open(os.path.join(ROOT, "tools", "ci", "station_details.sh"),
                  encoding="utf-8").read()
    code = "\n".join(line for line in script.splitlines()
                     if not line.lstrip().startswith("#"))

    assert "expect_refusal()" in code, "brak wspólnej funkcji sprawdzającej odmowy"
    # Trzy warunki w jednym miejscu, więc żadna odmowa nie może ich pominąć.
    assert 'fail "$label: polecenie NIE padło' in code
    assert 'test ! -e "$glb"' in code, "odmowa nie sprawdza, czy nie powstał plik"
    assert 'grep -Eq "$pattern" "$log"' in code, "odmowa nie czyta powodu z logu"

    # Sześć odmów: dwie na peronach, cztery na słupkach.
    assert code.count("expect_refusal ") >= 6, code.count("expect_refusal ")
    for pattern in ("nie zbudowano ani jednej bryły",
                    "okno .* jest puste",
                    "nie ma ani jednego znacznika",
                    "wchodzi w skrajnię pojazdu",
                    "przebija ścianę profilu"):
        assert pattern in code, f"brak odmowy o wzorcu /{pattern}/"


def test_ci_the_material_style_gate_reads_the_reason_of_every_refusal():
    """Ta sama konwencja co w `station_details.sh`, dla bramki T-902.

    Powód, dla którego ten test istnieje osobno, a nie jako pętla po obu skryptach:
    wzorce odmów są RÓŻNE i to one są treścią bramki. Test napisany „dla każdego
    skryptu w tools/ci sprawdź, że ma expect_refusal" przechodziłby także wtedy,
    gdyby `material_style.sh` sprawdzał pięć razy tę samą odmowę.

    Pięć odmów: dwie na wywołaniu (brak pliku konfiguracji, brak argumentu) i trzy
    na TREŚCI konfiguracji (pusta lista materiałów, powtórzony identyfikator, brak
    materiału wymaganego przez kamerę `close`). Te trzy są tu istotne, bo żadnej
    z nich nie da się wykonać bez uruchomionego Blendera — testy jednostkowe
    T-902 czytają wyłącznie JSON i nie wchodzą w generator ani na krok.
    """
    script = open(os.path.join(ROOT, "tools", "ci", "material_style.sh"),
                  encoding="utf-8").read()
    code = "\n".join(line for line in script.splitlines()
                     if not line.lstrip().startswith("#"))

    assert "expect_refusal()" in code, "brak wspólnej funkcji sprawdzającej odmowy"
    assert 'fail "$label: polecenie NIE padło' in code
    assert 'test ! -e "$artefact"' in code, "odmowa nie sprawdza, czy nie powstał plik"
    assert 'grep -Eq "$pattern" "$log"' in code, "odmowa nie czyta powodu z logu"

    assert code.count("expect_refusal ") >= 5, code.count("expect_refusal ")
    for pattern in ("FileNotFoundError",
                    "material_presets jest puste",
                    "niepuste i unikalne",
                    "wymaganych przez kamerę close"):
        assert pattern in code, f"brak odmowy o wzorcu /{pattern}/"

    # Wzorzec odmowy musi się zgadzać z tym, co generator NAPRAWDĘ wypisuje.
    # Literówka po jednej ze stron zamienia bramkę w test „coś się wywaliło":
    # `expect_refusal` sprawdza wtedy wyłącznie, że polecenie padło.
    generator = open(os.path.join(ROOT, "tools", "blender", "material_test_scene.py"),
                     encoding="utf-8").read()
    for pattern in ("material_presets jest puste",
                    "niepuste i unikalne",
                    "wymaganych przez kamerę close"):
        assert pattern in generator, (
            f"bramka szuka /{pattern}/, a generator tego nie wypisuje")


def test_ci_the_material_style_gate_checks_the_scene_not_only_the_generator_report():
    """Raport generatora nie jest weryfikacją generatora — to ta sama strona umowy.

    Pierwsza wersja tej bramki miała tu `grep -q "material_presets="`, czyli
    sprawdzała, że generator COKOLWIEK o sobie powiedział. Preset dopisany do
    `visual-style.json`, a nieobecny w scenie, przechodził przez to bez śladu.
    Dlatego bramka czyta chunk JSON wyeksportowanego GLB — bez Blendera, wprost
    ze struktury pliku — i porównuje nazwy węzłów z listą presetów.
    """
    script = open(os.path.join(ROOT, "tools", "ci", "material_style.sh"),
                  encoding="utf-8").read()
    code = "\n".join(line for line in script.splitlines()
                     if not line.lstrip().startswith("#"))

    assert 'grep -q "material_presets="' not in code, (
        "bramka wróciła do sprawdzania samego raportu generatora")
    assert "0x4E4F534A" in code, "bramka nie czyta chunku JSON z GLB"
    assert 'swatch_' in code, "bramka nie porównuje nazw brył z presetami"
    assert 'presety bez bryły w GLB' in code, "bramka nie nazywa brakującego presetu"
# --- kasowanie gałęzi: workflow, który musi sprawdzać, zanim skasuje ------------

def _prune_workflow():
    return _text("prune-merged-branches.yml")


def _prune_without_comments():
    """Sam kod workflow, bez komentarzy.

    Bramka, która grepuje po całym pliku, łapie własne uzasadnienie: komentarz
    tłumaczący, czemu czegoś NIE używamy, zawiera tę frazę tak samo jak użycie.
    Ta pułapka wywróciła już bramkę reguły 9 w tym repozytorium — powtarzanie jej
    z pełną świadomością byłoby wyborem, nie przeoczeniem.
    """
    return "\n".join(
        line.split(" #", 1)[0] if not line.lstrip().startswith("#") else ""
        for line in _prune_workflow().splitlines())


def _prune_document():
    """Sparsowany workflow. `on` w YAML 1.1 jest wartością logiczną, nie napisem —
    `safe_load` daje klucz `True`, więc `document["on"]` wywraca się na KeyError."""
    document = yaml.safe_load(_prune_workflow())
    return document, document.get("on", document.get(True))


def test_prune_workflow_verifies_the_merge_itself_instead_of_trusting_a_list():
    """Kasowanie gałęzi to operacja nieodwracalna wykonywana bez nadzoru.

    Workflow powstał dlatego, że agent w środowisku Claude Code dostaje 403 na
    usuwanie refów — to ograniczenie środowiska, nie brak uprawnień właściciela.
    Lista 79 gałęzi zweryfikowanych w #120 wisiała przez to w opisie PR-a.

    Przeniesienie tej roboty na runnera nie może polegać na WKLEJENIU tamtej listy:
    lista sprzed tygodnia opisuje repozytorium sprzed tygodnia, a gałąź, do której
    ktoś w międzyczasie dopisał commit, wygląda na niej tak samo jak przedtem.
    Dlatego workflow wyznacza listę sam i pyta o relację COMMITÓW, nie o nazwy.

    `git branch --merged` nie wystarcza i to nie jest formalność: przy scaleniu ze
    squashem gałąź ma inny commit niż baza, więc bywa raportowana jako niescalona,
    a przy scaleniu przez merge — jako scalona nawet wtedy, gdy dopisano do niej
    później. `merge-base --is-ancestor` odpowiada na pytanie, które ma znaczenie:
    czy w tej gałęzi jest cokolwiek, czego nie ma w bazie.
    """
    text = _prune_without_comments()
    assert "merge-base --is-ancestor" in text, \
        "workflow nie sprawdza, czy czubek gałęzi jest przodkiem bazy"
    assert "--merged" not in text, \
        "pytanie o samą nazwę gałęzi myli się przy squashu — ma nie być używane"
    assert "gh pr list --state open" in text, \
        "workflow nie pyta o otwarte pull requesty"
    assert "rev-list --count" in text, \
        "workflow nie liczy, ILE commitów gałąź ma poza bazą — bez tego log nie mówi, czemu została"


def test_prune_workflow_defaults_to_a_dry_run():
    """Domyślne uruchomienie ma NIC nie skasować.

    Krok kasujący jest warunkowany `inputs.dry_run == false`, a samo wejście ma
    `default: true`. Kolejność jest istotna: gdyby domyślną wartością było
    kasowanie, jedno kliknięcie „Run workflow" bez czytania formularza usuwałoby
    gałęzie nieodwracalnie.
    """
    document, triggers = _prune_document()
    inputs = triggers["workflow_dispatch"]["inputs"]
    assert inputs["dry_run"]["default"] is True, inputs["dry_run"]
    steps = document["jobs"]["prune"]["steps"]
    deleting = [s for s in steps if "push origin --delete" in str(s.get("run", ""))]
    assert len(deleting) == 1, "krok kasujący ma być dokładnie jeden"
    assert "inputs.dry_run == false" in str(deleting[0]["if"]), deleting[0].get("if")


def test_prune_workflow_never_deletes_the_base_branch():
    """Baza musi być wykluczona jawnie, a nie przez to, że „i tak jest przodkiem siebie".

    `merge-base --is-ancestor main main` jest prawdą, więc bez tego wykluczenia
    workflow skasowałby gałąź, względem której liczy scalenie — czyli dokładnie tę,
    której nie wolno tknąć.
    """
    assert '[ "$branch" = "$BASE" ]' in _prune_without_comments(), \
        "brak jawnego wykluczenia bazy"


def test_prune_workflow_asks_for_the_write_permission_it_needs_and_no_more():
    """`contents: write` jest konieczne do usunięcia refa i wystarczające.

    Domyślne `contents: read` z pozostałych workflow tego repozytorium dałoby 403 —
    czyli dokładnie ten sam objaw, dla którego ten workflow powstał, tylko przeniesiony
    na runnera. `pull-requests: read` jest potrzebne do listy otwartych PR-ów.
    """
    document, _triggers = _prune_document()
    assert document["permissions"] == {"contents": "write", "pull-requests": "read"}, \
        document["permissions"]


# --- akcje przypięte po SHA ----------------------------------------------------

ACTION_USE = re.compile(r"(?m)^\s*uses:\s*(\S+)\s*(?:#\s*(\S+))?\s*$")


def test_every_action_is_pinned_to_a_commit_not_a_moving_tag():
    """Te joby chodzą na MASZYNIE WŁAŚCICIELA, a nie na jednorazowej maszynie GitHuba.

    `actions/checkout@v6` to tag RUCHOMY: wskazuje na to, co właściciel akcji ostatnio
    tam przesunął. Kto przejmie konto `actions` albo dopisze commit i przesunie tag,
    ten wykonuje swój kod na maszynie w mieszkaniu właściciela tego repozytorium,
    z dostępem do `runner.tool_cache`, do workspace'u i do `GITHUB_TOKEN`. Ten sam tag,
    ten sam workflow, inny kod — i nic w repozytorium tego nie odnotowuje.

    SHA commita jest niezmienny. Przesunięcie tagu przestaje mieć znaczenie, a każda
    zmiana wersji akcji staje się widocznym commitem w tym repozytorium.

    Zmierzone przy wprowadzaniu: 21 wywołań, 4 różne akcje, wszystkie na tagach `v4`/`v6`.
    """
    unpinned = []
    checked = 0
    for name in _workflows():
        for match in ACTION_USE.finditer(_text(name)):
            ref = match.group(1)
            if "@" not in ref or ref.startswith("./"):
                continue
            checked += 1
            _action, version = ref.rsplit("@", 1)
            if not re.fullmatch(r"[0-9a-f]{40}", version):
                unpinned.append(f"{name}: {ref}")
    assert not unpinned, f"akcje na ruchomym tagu: {unpinned}"
    assert checked >= 20, checked


def test_every_pinned_action_says_which_version_the_commit_is():
    """SHA bez wersji jest nieczytelny i przez to nieaktualizowalny.

    `actions/checkout@d23441a4…` nie mówi człowiekowi nic: nie da się zobaczyć, czy to
    wersja sprzed roku, ani zdecydować, czy warto podnieść. Komentarz z wersją zamienia
    przypięcie z bariery w informację — i jest jedyną rzeczą, która sprawia, że
    przypinanie po SHA nie zamienia się w porzucanie akcji na zawsze.
    """
    missing = []
    for name in _workflows():
        for match in ACTION_USE.finditer(_text(name)):
            ref, comment = match.group(1), match.group(2)
            if "@" not in ref or ref.startswith("./"):
                continue
            if not re.fullmatch(r"v\d+(\.\d+)*", comment or ""):
                missing.append(f"{name}: {ref} # {comment}")
    assert not missing, f"przypięcia bez czytelnej wersji: {missing}"


def test_the_same_action_is_pinned_to_the_same_commit_everywhere():
    """Dwa różne SHA tej samej akcji w jednym repozytorium to stan, nie decyzja.

    Bez tej kontroli aktualizacja „wszystkich checkoutów" zostawia jeden na starym
    commicie i nikt tego nie widzi — a właśnie ten jeden będzie potem tłumaczył, czemu
    jeden job zachowuje się inaczej niż wszystkie pozostałe.
    """
    seen = {}
    for name in _workflows():
        for match in ACTION_USE.finditer(_text(name)):
            ref = match.group(1)
            if "@" not in ref or ref.startswith("./"):
                continue
            action, sha = ref.rsplit("@", 1)
            seen.setdefault(action, {}).setdefault(sha, []).append(name)
    split = {a: v for a, v in seen.items() if len(v) > 1}
    assert not split, f"ta sama akcja na różnych commitach: {split}"
    assert len(seen) >= 4, seen
