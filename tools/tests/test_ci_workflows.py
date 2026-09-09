#!/usr/bin/env python3
"""Testy odporności workflow CI.

Powód: 02.09.2026 krok instalacji Blendera zawiesił się trzy razy na trzech różnych
runnerach, za każdym razem przed uruchomieniem ciała testu. Te testy pilnują, żeby
poprawka nie wyparowała po cichu przy następnej edycji workflow.
"""
import glob
import os
import re
import secrets

import yaml

import assertion_gate as AG

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


# --- bramki na `tools/ci/*.sh`: WYKONANIE, nie napis w pliku --------------------
#
# Wspólny powód całej rodziny niżej, zmierzony 04.09.2026: bramka pytająca „czy ten
# napis stoi w pliku" przechodzi tak samo dobrze wtedy, gdy polecenie jest
# WYKONYWANE, jak wtedy, gdy jest tylko WSPOMNIANE — w komentarzu, w `echo`, w treści
# `--help`. Pomiar był zawsze ten sam: mutacja wyłączająca ochronę i zostawiająca
# napis, a potem cały zestaw na zielono. Wszystkie cztery bramki `apt_install.sh`
# przechodziły takie mutacje — każda opisana w docstringu swojego testu (M1–M4)
# i wypisana w commicie, który tę zmianę wprowadził.
#
# Napisy zostają tam, gdzie WSKAZUJĄ fragment do uruchomienia (nazwa funkcji
# shellowej, prefiks heredoca) — werdykt wydaje uruchomienie tego fragmentu.


def _shim(directory, name, body):
    """Atrapa polecenia w `PATH`: zapisuje swoje argv i kończy się zadanym kodem."""
    path = os.path.join(directory, name)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("#!/usr/bin/env bash\n" + body)
    os.chmod(path, 0o755)
    return path


def _log_lines(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as handle:
        return [line for line in handle.read().splitlines() if line]


def _run_apt_helper(update_code=0, install_code=0, attempts=None, packages=("libegl1",)):
    """Uruchamia PRAWDZIWY `tools/ci/apt_install.sh` bez sieci, bez sudo i bez czekania.

    `sudo`, `apt-get` i `sleep` są podmienione w `PATH`. Atrapa `sudo` zapisuje swoje
    argv i wykonuje resztę wiersza, więc widać, CO dostanie sygnał od stopera: przy
    `sudo timeout … apt-get` pierwszym argumentem `sudo` jest `timeout`, a przy
    `timeout … sudo apt-get` — `apt-get`. Atrapa `apt-get` zapisuje argv i kończy się
    kodem zadanym z testu, stąd wiadomo, jakie opcje `-o` naprawdę do apta doszły
    i ile razy każda podkomenda została wywołana. Atrapa `sleep` tylko notuje, żeby
    pętla ponawiania nie kosztowała testu 45 sekund.

    Zwraca kod wyjścia, oba strumienie oraz wywołania `sudo`, `apt-get` i `sleep`.
    """
    import shutil
    import subprocess
    import tempfile

    root = tempfile.mkdtemp(prefix="metro-apt-")
    try:
        binroot = os.path.join(root, "bin")
        os.makedirs(binroot)
        logs = {name: os.path.join(root, name + ".log")
                for name in ("sudo", "apt", "sleep")}
        _shim(binroot, "sudo", 'printf "%s\\n" "$*" >> "$SUDO_LOG"\nexec "$@"\n')
        _shim(binroot, "apt-get",
              'printf "%s\\n" "$*" >> "$APT_LOG"\n'
              'for argument in "$@"; do\n'
              '    [ "$argument" = update ] && exit "$FAKE_UPDATE_CODE"\n'
              '    [ "$argument" = install ] && exit "$FAKE_INSTALL_CODE"\n'
              'done\n'
              'exit 0\n')
        _shim(binroot, "sleep", 'printf "%s\\n" "$*" >> "$SLEEP_LOG"\n')

        env = dict(os.environ)
        env.update(PATH=binroot + os.pathsep + env.get("PATH", ""),
                   SUDO_LOG=logs["sudo"], APT_LOG=logs["apt"], SLEEP_LOG=logs["sleep"],
                   FAKE_UPDATE_CODE=str(update_code),
                   FAKE_INSTALL_CODE=str(install_code),
                   APT_CACHE_DIR="", LC_ALL="C.UTF-8")
        if attempts is not None:
            env["APT_UPDATE_ATTEMPTS"] = str(attempts)
        result = subprocess.run(["bash", HELPER, *packages], env=env,
                                capture_output=True, text=True,
                                encoding="utf-8", errors="replace")
        return {"code": result.returncode, "out": result.stdout, "err": result.stderr,
                "sudo": _log_lines(logs["sudo"]), "apt": _log_lines(logs["apt"]),
                "sleeps": _log_lines(logs["sleep"])}
    finally:
        shutil.rmtree(root, ignore_errors=True)


def _apt_calls(run, subcommand):
    """Wywołania `apt-get`, które dostały tę podkomendę jako OSOBNY token.

    Osobny token, bo słowo `install` stoi też w `--no-install-recommends`; wersja
    szukająca podciągu liczyłaby jedno wywołanie za dwa.
    """
    return [call for call in run["apt"] if subcommand in call.split()]


def test_ci_apt_helper_passes_its_own_socket_timeouts_to_apt():
    """Limity gniazda muszą DOJŚĆ DO APTA, a nie stać w pliku.

    Ten test jest PRZEPISANY, nie dopisany obok. Poprzednia wersja
    (`test_ci_apt_helper_is_executable_and_retries`) pytała wyłącznie, czy napisy
    `Acquire::http::Timeout` i `Acquire::https::Timeout` stoją gdziekolwiek
    w skrypcie. Mutacja M1, zmierzona 04.09.2026: usunięcie obu opcji z `APT_OPTS`
    i przeniesienie ich do komentarza obok — cały zestaw na zielono, 1343/1343,
    a apt jechał bez limitu na martwe gniazdo, czyli dokładnie tak, jak
    02.09.2026, kiedy trzy joby zawisły.

    Teraz argumenty są czytane z ATRAPY `apt-get`, więc liczy się to, co proces
    naprawdę dostał.
    """
    assert os.access(HELPER, os.X_OK), "tools/ci/apt_install.sh musi być wykonywalny"

    run = _run_apt_helper()
    assert run["code"] == 0, (run["code"], run["err"])
    installs = _apt_calls(run, "install")
    assert len(installs) == 1, run["apt"]
    for option in ("-o Acquire::http::Timeout=30",
                   "-o Acquire::https::Timeout=30",
                   "-o Acquire::Retries=3"):
        for call in run["apt"]:
            assert option in call, (option, call)


def test_ci_apt_helper_really_retries_a_failing_update():
    """Pętla ponawiania `update` musi się WYKONAĆ tyle razy, ile zapowiada.

    Poprzednia wersja tej reguły sprawdzała obecność napisów `ATTEMPTS` i `sleep`.
    Oba zostają w pliku po każdej mutacji, która pętlę usuwa — nazwa zmiennej
    i tak stoi w deklaracji na górze skryptu.

    Dwa przebiegi, bo jeden nie mierzy tego, co mówi: przy domyślnych dwóch próbach
    liczba 2 mogłaby być przypadkiem (na przykład jednym wywołaniem i jednym
    ponowieniem wpisanym z ręki). Podniesienie `APT_UPDATE_ATTEMPTS` do trzech
    pokazuje, że pętla czyta ZMIENNĄ, a nie stałą.
    """
    two = _run_apt_helper(update_code=100)
    assert two["code"] != 0, two
    assert len(_apt_calls(two, "update")) == 2, two["apt"]
    assert "nie powiodło się po 2 próbach" in two["err"], two["err"]
    # `install` nie ma prawa się zacząć, gdy indeksy nie zjechały.
    assert _apt_calls(two, "install") == [], two["apt"]
    # Odczekanie między próbami jest częścią reguły: bez niego ponowienie trafia
    # w tę samą blokadę dpkg co próba poprzednia.
    assert two["sleeps"], "między próbami nie ma odczekania"

    three = _run_apt_helper(update_code=100, attempts=3)
    assert len(_apt_calls(three, "update")) == 3, three["apt"]


def test_ci_apt_helper_lets_apt_handle_a_dead_socket():
    """Zerwane połączenie ma łapać apt, nie zewnętrzny stoper.

    `Acquire::*::Timeout` przerywa martwe gniazdo po 30 s, a `Acquire::Retries`
    powtarza sam plik. Zewnętrzny limit jest sufitem na proces, nie mechanizmem
    ponawiania — inaczej wyrzuca do kosza 190 MB pobrane w połowie.

    Sprawdzane na WYKONANIU. Mutacja M2, zmierzona 04.09.2026: zamiana
    `sudo timeout … apt-get` na `timeout … sudo apt-get`. Napis `sudo timeout`
    zostaje w pliku, bo stoi w komentarzu, który tę właśnie kolejność tłumaczy —
    bramka łapała więc własne uzasadnienie i przechodziła, choć sygnał trafiał
    w `sudo`, a pobieranie zostawało sierotą. Atrapa `sudo` zapisuje swoje argv,
    więc kolejność jest widoczna wprost.
    """
    run = _run_apt_helper()
    assert run["sudo"], "skrypt nie wywołał sudo ani razu"
    for call in run["sudo"]:
        first = call.split()[0]
        assert first == "timeout", (
            f"sudo dostało jako pierwszy argument '{first}', a nie 'timeout' — "
            "sygnał ze stopera trafi w sudo, nie w apt-get")
        assert "--kill-after=" in call, call

    # Kod 124 (i 137 po `--kill-after`) musi być ROZPOZNANY i opisany, inaczej
    # w logu zostaje samo „zakończyło się kodem 124" bez słowa o limicie.
    for code in (124, 137):
        timed_out = _run_apt_helper(install_code=code)
        assert timed_out["code"] != 0, timed_out
        assert "przekroczyło" in timed_out["err"], (code, timed_out["err"])
    other = _run_apt_helper(install_code=100)
    assert "zakończyło się kodem 100" in other["err"], other["err"]


def test_ci_install_is_not_retried_from_scratch():
    """`install` NIE jest powtarzany od zera.

    Zmierzone 02.09.2026 na `first-run`: trzy próby po 240 s, każda z postępem,
    każda ubita i zaczynająca od nowa — 13 minut na nic. Powtarzany jest tylko
    `update`, bo jest tani (11,7 MB w 2 s).

    Mutacja M3, zmierzona 04.09.2026: dopisane za `apt_run … install` alternatywne
    `|| { sleep …; sudo timeout … apt-get … install …; }`. Warunek strukturalny
    niżej tego NIE łapie (wiersz `^apt_run "$…" install` zostaje dokładnie jeden,
    nazwa `INSTALL_ATTEMPTS` nie pada), a `install` startował dwa razy. Dlatego
    liczy się LICZBA WYWOŁAŃ atrapy `apt-get`, a nie kształt pliku.
    """
    failed = _run_apt_helper(install_code=100)
    assert failed["code"] != 0, failed
    assert len(_apt_calls(failed, "install")) == 1, (
        f"`install` wywołany {len(_apt_calls(failed, 'install'))} razy po porażce — "
        "190 MB pobrane w połowie idzie do kosza")

    good = _run_apt_helper()
    assert len(_apt_calls(good, "install")) == 1, good["apt"]
    assert len(_apt_calls(good, "update")) == 1, good["apt"]

    # Warunek strukturalny zostaje jako druga linia obrony: podkomenda musi być
    # czytana jako osobny token. Poprzednia wersja szukała podciągu "install"
    # w całej linii i przechodziła nawet po podmianie `install` na `instalxx`,
    # bo słowo zostaje w `--no-install-recommends`.
    body = open(HELPER, encoding="utf-8").read()
    subcommands = re.findall(r'(?m)^apt_run "\$[A-Z_]+" ([a-z-]+)', body)
    assert subcommands.count("install") == 1, subcommands
    assert set(subcommands) <= {"update", "install"}, subcommands


def test_ci_step_budget_covers_a_slow_mirror():
    """Sufit musi pomieścić pobranie 190 MB z wolnego lustra.

    Zmierzona prędkość lustra Azure w złym momencie: ~150 kB/s, czyli ponad
    20 minut samego pobierania. Sufit poniżej tego zamienia wolne, ale postępujące
    pobranie w twardą awarię — dokładnie to zrobiła pierwsza wersja tej poprawki.

    Sufit jest odczytywany z WYWOŁANIA, nie z pliku. Mutacja M4, zmierzona
    04.09.2026: `INSTALL_TIMEOUT_S=${APT_INSTALL_TIMEOUT_S:-60}` z poprzednim
    wierszem przepisanym do komentarza obok. `re.search` bierze PIERWSZE trafienie,
    czyli to z komentarza, więc test widział 1500 s, a stoper dostawał 60 —
    i przechodził. Teraz liczba pochodzi z argumentów, jakie `timeout` naprawdę
    dostał w przebiegu instalacji.
    """
    run = _run_apt_helper()
    installs = [call for call in run["sudo"] if "install" in call.split()]
    assert len(installs) == 1, run["sudo"]
    # `timeout --kill-after=30 <budżet> apt-get …` — budżet to trzeci token.
    install_s = int(installs[0].split()[2])
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
#: Zmyślona wersja Blendera dla bramek wykonawczych — UNIKALNA NA PROCES, i to jest
#: naprawa zmierzonej usterki, nie ostrożność.
#:
#: `tools/ci/blender_install.sh` wyprowadza ścieżkę archiwum z wersji:
#: `TARBALL="/tmp/blender-${VERSION}-linux-x64.tar.xz"`. Przy stałym `0.0.1` była to
#: więc jedna GLOBALNA ścieżka w `/tmp`, a przegląd mutacyjny puszcza cały zestaw
#: w trzech równoległych robotnikach. Odtworzone 04.09.2026, sześć przebiegów po trzy
#: naraz — **padły dwa**:
#:
#:     AssertionError: (1, '...[BLENDER] sprawdzam sumę SHA-256\n
#:                          /tmp/blender-0.0.1-linux-x64.tar.xz: FAILED...')
#:     AssertionError: (1, '...sha256sum: /tmp/blender-0.0.1-linux-x64.tar.xz:
#:                          No such file or directory...')
#:
#: Jeden robotnik podmieniał archiwum drugiemu, drugi je usuwał trzeciemu.
#:
#: Skutek był GORSZY niż czerwony test: `mutation_sweep.py` liczy „padł jakikolwiek
#: test" jako zabicie mutacji, więc ten flak dał FAŁSZYWE ZABICIE i przekłamał
#: werdykt przeglądu dla mutacji w `clearance_profile.py:142` — pozycji, która jest
#: w rzeczywistości równoważna (99 840 trafień w próg, 0 różnic). Bramka
#: niedeterministyczna nie jest tylko uciążliwa; ona kłamie w pomiarze, który ktoś
#: potem wpisuje do raportu.
#:
#: Unikalność NIE opiera się na PID, i to też jest zmierzone. Pierwsza wersja tej
#: naprawy dawała `0.<pid>.<licznik>` z uzasadnieniem „`mutation_sweep` zrównolegla
#: procesami". Sprawdzone tym samym testem wyścigu, tylko na WĄTKACH: padło 10 z 12,
#: bo każdy wątek importuje moduł od nowa, dostaje świeży licznik od 1, a PID ma ten
#: sam — wszystkie dwanaście dostało `0.25530.1`. Naprawa, która działa tylko przy
#: jednym modelu równoległości, jest naprawą przypadkiem.
#:
#: `secrets.randbits(48)` nie zależy od żadnego modelu: ani od procesu, ani od wątku,
#: ani od tego, czy moduł został zaimportowany raz czy dwadzieścia razy.
def fake_blender_version():
    """Wersja i przez to ścieżka w `/tmp` unikalna dla KAŻDEGO wywołania.

    `installed_version` w instalatorze czyta z `--version` wyłącznie cyfry i kropki,
    więc numer musi mieć tę postać — stąd `0.<losowe>.<losowe>` zamiast UUID-a.
    """
    return f"0.{secrets.randbits(24)}.{secrets.randbits(24)}"


def test_ci_blender_fake_version_is_unique_so_the_gate_cannot_race_itself():
    """Bramka niedeterministyczna nie jest uciążliwa — ona KŁAMIE W POMIARZE.

    `tools/ci/blender_install.sh` wyprowadza ścieżkę archiwum z wersji
    (`TARBALL="/tmp/blender-${VERSION}-linux-x64.tar.xz"`), a `mutation_sweep.py`
    puszcza cały ten zestaw w trzech równoległych robotnikach. Przy STAŁEJ zmyślonej
    wersji była to jedna globalna ścieżka w `/tmp` i robotnicy podmieniali sobie
    archiwum: odtworzone 04.09.2026, **2 padnięcia na 6** przebiegów po trzy naraz.

    Skutek był gorszy niż czerwony test. `mutation_sweep` liczy „padł jakikolwiek
    test" jako zabicie mutacji, więc ten flak dał FAŁSZYWE ZABICIE i przekłamał
    werdykt dla `clearance_profile.py:142` — mutacji, która jest w rzeczywistości
    równoważna (99 840 trafień w próg, 0 różnic). Liczba z przeglądu trafia potem
    do raportu, więc niedeterminizm tutaj to nieprawda tam.

    Ten test nie sprawdza samej losowości, a KONSEKWENCJĘ: dwie wersje muszą dać
    dwie różne ścieżki w `/tmp`.
    """
    versions = [fake_blender_version() for _ in range(64)]
    assert len(set(versions)) == len(versions), "wersje się powtarzają"

    paths = {f"/tmp/blender-{v}-linux-x64.tar.xz" for v in versions}
    assert len(paths) == len(versions), "różne wersje dały tę samą ścieżkę"

    # Kształt musi zostać taki, jaki czyta instalator: `installed_version` bierze
    # z `--version` wyłącznie cyfry i kropki, więc litery czy myślnik wywróciłyby
    # przebieg ZGODNY, a nie odmowę — czyli zepsułyby akurat tę stronę pomiaru,
    # która dowodzi, że skrypt w ogóle dochodzi do końca.
    for version in versions:
        assert re.fullmatch(r"[0-9]+(\.[0-9]+)+", version), version


def _fake_blender_archive(root, version, cialo=None):
    """Poprawny `.tar.xz` z atrapą `blender` w środku. Zwraca (ścieżka, suma).

    Atrapa musi być PRAWDZIWYM archiwum, nie śmieciem: na śmieciu wywraca się
    `tar -xJf`, więc skrypt padłby również z rozbrojoną sumą i kontrola negatywna
    nie zmierzyłaby niczego. Musi też być rozpakowywalna DO KOŃCA i przedstawiać
    się przypiętym numerem — z `|| true` po `sha256sum` instalator ma dojść do
    `exit 0` i wypisać ścieżkę, żeby test miał co złapać.
    """
    import hashlib
    import tarfile

    tree = f"blender-{version}-linux-x64"
    payload = os.path.join(root, "payload", tree)
    os.makedirs(payload)
    binary = os.path.join(payload, "blender")
    if cialo is None:
        cialo = (f'echo "Blender {version}"\n'
                 'echo "\tbuild date: atrapa testowa"\n')
    with open(binary, "w", encoding="utf-8") as handle:
        handle.write("#!/usr/bin/env bash\n" + cialo)
    os.chmod(binary, 0o755)

    archive = os.path.join(root, "atrapa.tar.xz")
    with tarfile.open(archive, "w:xz") as tar:
        tar.add(payload, arcname=tree)
    with open(archive, "rb") as handle:
        return archive, hashlib.sha256(handle.read()).hexdigest()


def _run_blender_installer(root, label, sha256, archive, version, workspace=None):
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
        handle.write(f"version={version}\nsha256={sha256}\n")

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
    unpacked = os.path.join(cache, "metro-blender", version)
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
    version = fake_blender_version()
    leftover = f"/tmp/blender-{version}-linux-x64.tar.xz"
    try:
        archive, digest = _fake_blender_archive(root, version)
        wrong = "0" * 63 + "1"
        assert wrong != digest

        good, unpacked, called = _run_blender_installer(
            root, "zgodna", digest, archive, version)
        assert good.returncode == 0, (good.returncode, good.stderr)
        assert called, "shim `curl` nie został wywołany, więc przebieg nie mierzy pobrania"
        binary = os.path.join(unpacked, f"blender-{version}-linux-x64", "blender")
        assert good.stdout.strip() == binary, (good.stdout, binary)
        assert os.access(binary, os.X_OK), binary

        bad, unpacked, called = _run_blender_installer(
            root, "niezgodna", wrong, archive, version)
        assert called, "shim `curl` nie został wywołany, więc odmowa nie jest odmową sumy"
        assert bad.returncode != 0, (
            "instalator z niezgodną sumą zakończył się zerem — suma nie bramkuje niczego")
        assert "FAILED" in bad.stderr, bad.stderr
        assert not os.path.exists(unpacked), (
            f"instalator rozpakował archiwum o niezgodnej sumie do {unpacked}")

        workspace = os.path.join(root, "w-workspace", "workspace")
        os.makedirs(workspace)
        inside, unpacked, called = _run_blender_installer(
            root, "w-workspace", digest, archive, version, workspace=workspace)
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


def _runner_labels(job):
    """Etykiety `runs-on` joba, niezależnie od formy zapisu — albo `None`.

    GitHub przyjmuje na `runs-on` trzy różne typy dla tej samej rzeczy: napis
    (`runs-on: self-hosted`), listę (`runs-on:` i pod nim `- self-hosted`) oraz mapę
    (`group:` / `labels:`). Sprawdzanie tego wyrażeniem regularnym po tekście widzi
    wyłącznie pierwszą z tych form — patrz komentarz o mutacji w teście niżej.

    Grupa wraca jako pseudo-etykieta `group:<nazwa>`, żeby wywróciła porównanie
    i pokazała się w komunikacie: grupa to ZBIÓR maszyn dobierany po stronie GitHuba,
    a nie komplet etykiet z `CLAUDE.md` §9, i o tym, co do niej należy, decyduje
    ustawienie w organizacji, którego w tym repozytorium nie widać.
    """
    if "runs-on" not in job:
        return None
    value = job["runs-on"]
    if isinstance(value, str):
        return [value.strip()]
    if isinstance(value, (list, tuple)):
        return [str(item).strip() for item in value]
    if isinstance(value, dict):
        labels = value.get("labels", [])
        if isinstance(labels, str):
            labels = [labels]
        found = [str(item).strip() for item in labels]
        if value.get("group"):
            found.append(f"group:{value['group']}")
        return found
    return [repr(value)]


#: Celowo jedyna etykieta w workflowach. Repozytorium ma trzy własne runnery,
#: a GitHub przypisuje do nich automatycznie `Linux` i `X64`; wybór nie może
#: zależeć od nazwy konkretnego CPU/GPU.
REQUIRED_RUNNER_LABELS = ("self-hosted",)


def _runner_mismatch(labels):
    """Powód, dla którego `runs-on` nie jest dokładnie `self-hosted` — albo `None`."""
    if labels is None:
        return "job bez `runs-on`"
    found = sorted(label.lower() for label in labels)
    expected = sorted(label.lower() for label in REQUIRED_RUNNER_LABELS)
    if found != expected:
        return (f"runs-on = {labels}, oczekiwano kompletu "
                f"{list(REQUIRED_RUNNER_LABELS)}")
    return None


def test_every_job_runs_on_a_self_hosted_runner():
    """Każdy job używa dokładnie `runs-on: self-hosted`.

    YAML jest parsowany, nie sprawdzany wyrażeniem regularnym, aby zmiana formy
    zapisu nie mogła ominąć tej bramki.
    """
    wrong = []
    checked = 0
    for name in _workflows():
        document = yaml.safe_load(_text(name))
        for job_id, job in document["jobs"].items():
            checked += 1
            reason = _runner_mismatch(_runner_labels(job))
            if reason:
                wrong.append(f"{name}:{job_id}: {reason}")
    assert not wrong, f"joby na złym runnerze: {wrong}"
    # Liczba jak w bramce fork-PR niżej: pętla po samych znalezionych jobach
    # przeszłaby pusta i zielona, gdyby `jobs:` przestało być czytane.
    assert checked >= 7, f"sprawdzono tylko {checked} jobów — pętla nie widzi `jobs:`"

    hosted = [name for name in _workflows() if "ubuntu-latest" in _text(name)]
    assert not hosted, f"GitHub-hosted runner nadal wymieniony w: {hosted}"


def test_the_runner_gate_fails_on_every_selector_that_would_miss_the_pool():
    """Kontrola negatywna: dodatkowa albo brakująca etykieta musi być błędem."""
    # Każda dodatkowa etykieta zawęża pulę i jest sprzeczna z konfiguracją repo.
    assert _runner_mismatch(["self-hosted", "Linux"])
    assert _runner_mismatch(["self-hosted", "gpu"])
    assert _runner_mismatch(["self-hosted", "self-hosted"])
    assert _runner_mismatch(["Linux"])
    # Grupa: zbiór maszyn dobierany po stronie GitHuba, niewidoczny z repozytorium.
    assert _runner_mismatch(_runner_labels({"runs-on": {"group": "own"}}))
    # Maszyna GitHuba, czyli minuty, których na koncie nie ma.
    assert _runner_mismatch(["ubuntu-latest"])
    assert _runner_mismatch(None)

    # …a komplet z §9 przechodzi niezależnie od kolejności i wielkości liter, bo
    # GitHub dobiera maszynę koniunkcją etykiet. Bez tych dwóch asercji „wszystko
    # jest błędem" byłoby dla bramki nie do odróżnienia od poprawnej detekcji.
    assert _runner_mismatch(list(REQUIRED_RUNNER_LABELS)) is None
    assert _runner_mismatch(["SELF-HOSTED"]) is None
    assert _runner_mismatch(
        _runner_labels({"runs-on": list(REQUIRED_RUNNER_LABELS)})) is None


#: Ścieżka pod `/tmp`, wpisana na sztywno. Lookbehind odsiewa człony dłuższych
#: napisów (`$RUNNER_TEMP/tmp`, `/var/tmp`), bo tam katalog wybiera runner, a nie
#: autor skryptu — a to jest cała różnica, o którą tej bramce chodzi.
FIXED_TMP_PATH = re.compile(r"(?<![\w/$}])/tmp(?:/|\b)")


def _fixed_tmp_paths(text):
    """`[(numer wiersza, wiersz)]` dla wierszy KODU, które piszą pod stałe `/tmp`.

    Wiersz komentarza się nie liczy: powód, dla którego ta bramka istnieje, trzeba
    dało się opisać przy kodzie, którego dotyczy, a opis musi móc zacytować ścieżkę,
    która ten wyścig wywołała. Konsekwencja: komentarz DOKLEJONY na końcu wiersza
    kodu zostanie zgłoszony. To jest świadome — łatwiej przenieść komentarz do
    osobnego wiersza niż zgadywać, gdzie w wierszu kończy się polecenie.
    """
    found = []
    for number, line in enumerate(text.splitlines(), start=1):
        if line.lstrip().startswith("#"):
            continue
        if FIXED_TMP_PATH.search(line):
            found.append((number, line.strip()))
    return found


def _shared_machine_files():
    """Wszystko, co runner wykonuje: workflowy, akcje lokalne, skrypty `tools/ci`."""
    found = [os.path.join(WORKFLOWS, name) for name in _workflows()]
    found += _action_files()
    found += sorted(glob.glob(os.path.join(ROOT, "tools", "ci", "*.sh")))
    return found


def test_no_ci_file_writes_to_a_hardcoded_tmp_path():
    """Cztery runnery puli stoją na JEDNEJ maszynie i dzielą jedno `/tmp`.

    Stała nazwa pliku w `/tmp` przestała być wtedy nazwą pliku tego joba i stała się
    nazwą WSPÓŁDZIELONĄ. Zmierzone 05.09.2026 na `tunnel-alignment (L1_A)`
    (run 33981627757), krok „Blender w przypiętej wersji":

        [BLENDER] sprawdzam sumę SHA-256
        /tmp/blender-5.2.1-linux-x64.tar.xz: OK
        tar (child): /tmp/blender-5.2.1-linux-x64.tar.xz: Cannot open: No such file

    Suma zgadza się, a chwilę później pliku nie ma — drugi job skończył swój `tar`
    i wykonał `rm -f` na tej samej nazwie. Wyścig był w skrypcie wcześniej, ale
    strzelał rzadko: dopiero pula czterech równoległych jobów robi z niego regułę.

    TRZY RODZINY SKUTKÓW, i tylko pierwsza jest głośna:

    1. plik znika między `sha256sum` a `tar` — job pada, widać w logu;
    2. dwa `curl -o` piszą do jednego pliku — suma może przejść u tego, kto akurat
       trafił w moment po cudzym zapisie, i rozpakuje się archiwum, którego ten job
       nie pobrał;
    3. bramka porównująca DWA pliki (`sim-tests`: rdzeń kontra referencja hamowania)
       zestawia wtedy wynik jednego przebiegu z wynikiem drugiego. Wychodzi zielona
       albo czerwona, ale nie o tym, o co pyta — i nikt się nie dowie.

    Dlatego bramka nie pyta o żaden konkretny plik, tylko o KLASĘ zapisu: żaden
    plik wykonywany przez runnera nie podaje ścieżki pod `/tmp` z ręki. Katalog
    daje `RUNNER_TEMP`, per runner i per job.
    """
    wrong = []
    checked = 0
    for path in _shared_machine_files():
        checked += 1
        text = open(path, encoding="utf-8").read()
        for number, line in _fixed_tmp_paths(text):
            wrong.append(f"{os.path.relpath(path, ROOT)}:{number}: {line}")
    assert not wrong, (
        "stała ścieżka w /tmp na maszynie z czterema runnerami — użyj "
        f"\"$RUNNER_TEMP/…\": {wrong}")
    # Pętla, która nie znalazła plików, przeszłaby pusta i zielona. Dziesięć
    # workflowów, dwie akcje lokalne i dwa skrypty `tools/ci` to dzisiejsze minimum.
    assert checked >= 12, f"przejrzano tylko {checked} plików — pętla ich nie widzi"


def test_the_tmp_gate_catches_the_write_that_broke_l1_a():
    """Kontrola do bramki wyżej — na dokładnie tym zapisie, który padł 05.09.2026.

    Bez niej „brak trafień" znaczyłoby tyle samo przy sprawnym detektorze, co przy
    wyrażeniu, które nie łapie niczego.
    """
    # Zapis, który wywrócił `tunnel-alignment (L1_A)`, i trzy jego odmiany.
    assert _fixed_tmp_paths('TARBALL="/tmp/blender-5.2.1-linux-x64.tar.xz"')
    assert _fixed_tmp_paths("          curl -fsSL -o /tmp/godot-mono.zip \"$url\"")
    assert _fixed_tmp_paths("          : > /tmp/prune-plan.txt")
    assert _fixed_tmp_paths("          diff -u /tmp/a.txt /tmp/b.txt")
    assert _fixed_tmp_paths("cd /tmp && rm -rf robota")

    # …i to, co ma przechodzić: katalog od runnera, `mktemp`, oraz ścieżka, w której
    # `tmp` jest tylko członem cudzej nazwy. Bez tych czterech asercji bramka mogłaby
    # zwracać trafienie na wszystkim i nadal wyglądać na działającą.
    assert _fixed_tmp_paths('TARBALL="${RUNNER_TEMP:-$(mktemp -d)}/blender.tar.xz"') == []
    assert _fixed_tmp_paths('curl -o "$RUNNER_TEMP/godot-mono.zip" "$url"') == []
    assert _fixed_tmp_paths('echo x > "$RUNNER_TEMP/tmp/plan.txt"') == []
    assert _fixed_tmp_paths("mv archiwum /var/tmp/gdziekolwiek") == []

    # Komentarz cytujący awarię ma przechodzić — inaczej ta bramka kazałaby usunąć
    # opis powodu, dla którego istnieje.
    assert _fixed_tmp_paths("    # padło na /tmp/blender-5.2.1-linux-x64.tar.xz") == []
    # Numer wiersza musi być numerem WIERSZA, nie indeksem od zera: komunikat bramki
    # jest jedyną rzeczą, po której ktoś ten zapis znajdzie.
    assert _fixed_tmp_paths("czysto\nczysto\nrm /tmp/x")[0][0] == 3


def _unwrap_expression(condition):
    """Warunek `if:` sprowadzony do samego wyrażenia, ze zbitą spacją.

    `if:` wolno zapisać i bez `${{ }}`, i w nim; zapis wielowierszowy (`>-`) wstawia
    dodatkowo znaki nowej linii. Bez tej normalizacji ta sama logika w innym zapisie
    wyglądałaby dla testu jak inna.
    """
    text = " ".join(str(condition).split())
    if text.startswith("${{") and text.endswith("}}"):
        text = text[3:-2].strip()
    return text


def _strip_parens(expression):
    """Zdejmuje nawiasy OTACZAJĄCE całe wyrażenie, i tylko takie.

    `(a || b) && c` nawiasu otwierającego na początku ma, ale on nie obejmuje całości
    — dlatego liczona jest głębokość, a nie sprawdzane pierwszy i ostatni znak.
    """
    text = expression.strip()
    while len(text) > 1 and text.startswith("(") and text.endswith(")"):
        depth = 0
        for index, char in enumerate(text):
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0 and index != len(text) - 1:
                    return text
        text = text[1:-1].strip()
    return text


def _split_top_level(expression, operator):
    """Członki wyrażenia GitHub Actions rozdzielone `operator` na NAJWYŻSZYM poziomie.

    Nie `str.split`: `||` wewnątrz nawiasu albo wewnątrz napisu nie jest tym samym
    operatorem, a test, który tego nie odróżnia, znowu czyta napis, a nie strukturę.
    """
    parts, depth, quote, start, index = [], 0, None, 0, 0
    while index < len(expression):
        char = expression[index]
        if quote is not None:
            if char == quote:
                quote = None
        elif char in "'\"":
            quote = char
        elif char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
        elif depth == 0 and expression.startswith(operator, index):
            parts.append(expression[start:index])
            index += len(operator)
            start = index
            continue
        index += 1
    parts.append(expression[start:])
    return [part.strip() for part in parts]


def test_every_job_refuses_pull_requests_from_forks():
    """Kod z forka NIE MA prawa wykonać się na maszynie właściciela.

    To jest warunek bezpieczeństwa, nie higiena: kroki tych jobów uruchamiają kod
    ze sprawdzonego refa (`tools/**`, `doctor.sh`, skrypty CI), więc bez tego
    warunku wystarczyłby pull request z forka, żeby uruchomić tam dowolny kod.

    `metro.brussels` jest prywatne, ale ma WŁĄCZONE forkowanie (`allow_forking:
    true`), więc uzasadnienie z matmaxalez/osadale — „forka nie da się zrobić" —
    tutaj nie obowiązuje. Warunek nosi każdy job osobno; `needs:` nie jest
    zamiennikiem, bo job dopisany bez łańcucha zależności nie miałby ochrony.

    Sprawdzana jest STRUKTURA warunku, nie obecność podnapisów. Mutacja, która tego
    testu NIE wywracała, zmierzona 04.09.2026 na `python-tests.yml`: zamiana `||`
    na `&&` w warunku joba. Poprzednia wersja pytała tylko, czy oba napisy gdzieś
    w warunku stoją — a po tej zamianie stoją oba, więc test przechodził zielony.
    Skutek jest podwójnie zły. Job z `&&` nie wystartuje NIGDY: na `push`
    `github.event_name != 'pull_request'` jest prawdą, ale drugi człon czyta pola
    `pull_request`, których na `push` nie ma, więc koniunkcja jest fałszem; na
    `pull_request` fałszem jest pierwszy człon. Bramka wtedy nie broni, tylko
    cichnie — a to jest ten sam rodzaj awarii, co job wiszący w `queued`.
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
            if "if" not in job:
                unguarded.append(f"{name}:{job_id}: job bez `if:`")
                continue
            members = [_strip_parens(part) for part
                       in _split_top_level(_unwrap_expression(job["if"]), "||")]
            if sorted(members) != sorted(required_terms):
                unguarded.append(
                    f"{name}:{job_id}: `if:` nie jest ALTERNATYWĄ (`||`) dwóch "
                    f"wymaganych członów, tylko {members}")
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

    Test idzie za odnośnikiem `uses:` I ZA JEGO ARGUMENTAMI. Dwa razy zmierzone,
    dwa razy ta sama luka o jeden poziom głębiej:

    * 04.09.2026, wydzielenie do akcji: poprzednia wersja sprawdzała WYŁĄCZNIE
      nazwę kroku i przeszła bez jednej modyfikacji, choć cała treść bramki
      wyprowadziła się do innego pliku;
    * ta zmiana: krok `uses: ./.github/actions/check-workspace` z dopisanym
      `with: paths: ""` też przechodził — a puste `paths` wprowadza akcję
      w gałąź `exit 0` („preflight: nie zadano katalogów do sprawdzenia"),
      czyli bramka przestaje sprawdzać cokolwiek, a job zostaje zielony.
    """
    missing = []
    toothless = []
    unclean = []
    checked = 0

    # Wywołanie bez `with:` bierze wartość domyślną akcji — więc puste `paths`
    # w SAMEJ akcji wyłączyłoby bramkę we wszystkich dziesięciu workflowach
    # naraz, nie zmieniając w nich ani jednego znaku.
    declared = ((_action(CLEAN_ACTION).get("inputs") or {}).get("paths") or {})
    default_paths = str(declared.get("default", ""))
    assert default_paths.strip(), (
        f"{CLEAN_ACTION}: domyślne `paths` jest puste, więc wywołanie bez `with:` "
        "wchodzi w gałąź `exit 0` i nie sprawdza żadnego katalogu")

    for name in _workflows():
        text = _text(name)
        if "Workspace jest czysty po checkoucie" not in text:
            missing.append(name)

        document = yaml.safe_load(text)
        calls = [step for job in document["jobs"].values() for step in job["steps"]
                 if str(step.get("uses", "")) == CLEAN_ACTION]
        assert calls, f"{name}: krok czystego workspace nie woła {CLEAN_ACTION}"
        for call in calls:
            checked += 1
            given = call.get("with") or {}
            # Klucz nieobecny znaczy „wartość domyślna akcji", a klucz obecny
            # i pusty znaczy „nie sprawdzaj". To dwie różne rzeczy i tylko druga
            # jest luką, więc rozstrzyga OBECNOŚĆ klucza, nie sama wartość.
            paths = str(given["paths"]) if "paths" in given else default_paths
            if not paths.strip():
                toothless.append(f"{name}: {CLEAN_ACTION} z pustym `paths`")

        # `clean: false` wyłączyłoby jedyny mechanizm, który realnie sprząta.
        # Sprawdzane na SPARSOWANYM YAML-u, nie gremem po tekście: komentarz przy
        # tym kroku sam zawiera napis `clean: false`, więc wersja tekstowa wywracała
        # się na własnym opisie — ta sama pułapka, co przy bramce reguły 9.
        #
        # KAŻDY job, nie pierwszy. Poprzednia wersja czytała
        # `next(iter(document["jobs"]))`, czyli wyłącznie job zadeklarowany jako
        # pierwszy. Dziś każdy workflow ma dokładnie jeden job, więc luka była
        # utajona — ale zmierzona: drugi job z `clean: false` w checkoucie
        # przechodził ten test i całą suitę.
        for job_id, job in document["jobs"].items():
            for step in job["steps"]:
                if not str(step.get("uses", "")).startswith("actions/checkout"):
                    continue
                given = step.get("with") or {}
                # Cokolwiek innego niż jawne `true` — `false`, `"false"`, `0` —
                # wyłącza sprzątanie. Brak klucza to domyślne `true`.
                if "clean" in given and str(given["clean"]).strip().lower() != "true":
                    unclean.append(f"{name}:{job_id}: clean: {given['clean']!r}")

    assert not missing, f"workflow bez bramki czystego workspace: {missing}"
    assert not toothless, \
        f"bramka woła akcję, ale nie zadaje jej ani jednego katalogu: {toothless}"
    assert not unclean, f"checkout, który nie sprząta workspace'u: {unclean}"
    assert checked >= 10, checked


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


#: Zestawy pakietów apt: `tools/ci/apt-packages/<nazwa>.txt`, komentarze pomijane.
APT_SETS = os.path.join(ROOT, "tools", "ci", "apt-packages")


def _apt_set_of(text):
    """Nazwa zestawu apt, który instaluje ten workflow (`apt_install.sh --set X`)."""
    found = re.findall(r"apt_install\.sh --set (\S+)", text)
    assert found, "workflow woła apt_install.sh bez --set"
    assert len(set(found)) == 1, f"workflow instaluje więcej niż jeden zestaw: {found}"
    return found[0]


def _apt_set_packages(name):
    """Pakiety z zestawu, bez komentarzy i pustych wierszy."""
    path = os.path.join(APT_SETS, f"{name}.txt")
    assert os.path.isfile(path), f"nie ma zestawu apt: {path}"
    with open(path, encoding="utf-8") as handle:
        packages = {line.strip() for line in handle
                    if line.strip() and not line.lstrip().startswith("#")}
    assert packages, f"zestaw {name} nie wymienia ani jednego pakietu"
    return packages


#: Sonames, dla których reguła mechaniczna niżej daje ZŁĄ nazwę pakietu.
#:
#: Tabela jest tu wbrew temu, co obiecywał docstring `_debian_package_for` do
#: 07.09.2026 („przekształcenie jest MECHANICZNE, nie tablicą wyjątków"). Obietnica
#: była prawdziwa dla DWÓCH bibliotek, wobec których ją napisano (`libEGL.so.1`
#: i `libGL.so.1`), i złamała się na pierwszej nowej: Debian nazywa pakiet
#: `libX11.so.6` jako `libx11-6`, z DYWIZEM, bo bez niego numer ABI zlałby się
#: z „11" w nazwie biblioteki (`libx116` czyta się dwuznacznie).
#:
#: Zmierzone 07.09.2026 na Ubuntu 24.04.4 przez `dpkg -S` na dziesięciu sonames
#: z domknięcia startowego Blendera 5.2.1: reguła mechaniczna trafiła w DZIEWIĘĆ
#: z dziesięciu, rozjazd jest JEDEN. Dlatego reguła zostaje, a tabela jest wyjątkiem
#: od niej — nie zamiennikiem.
#:
#: Wpisów w tej tabeli pilnuje `test_the_package_name_exceptions_are_all_necessary`:
#: każdy MUSI dawać wynik inny od reguły mechanicznej. Bez tego testu tabela stałaby
#: się wysypiskiem, w którym redundantny wpis przesłania działającą regułę i nikt
#: nie zauważy, gdy reguła przestanie działać dla czegoś innego.
#: Polecenia, o które pyta sonda, i pakiety, które je dostarczają.
#:
#: Dla bibliotek nazwa pakietu wyprowadza się z sonamu regułą (`_debian_package_for`).
#: Dla poleceń takiej reguły NIE MA — `unzip` przychodzi z pakietu `unzip`, a
#: `xvfb-run` z pakietu `xvfb` — więc tabela jest tu jedynym uczciwym rozwiązaniem
#: i nie udaje reguły. Rośnie o wpis przy każdym nowym poleceniu, a bramka niżej
#: wymusza, żeby każdy wpis szedł za zestawem apt w OBIE strony.
POLECENIA_Z_PAKIETOW = {
    "xvfb-run": "xvfb",
    "unzip": "unzip",
}


NAZWY_PAKIETOW_WYJATKI = {
    "libX11.so.6": "libx11-6",
}


def _debian_package_for(soname):
    """`libEGL.so.1` -> `libegl1`, `libGL.so.1` -> `libgl1`, `libX11.so.6` -> `libx11-6`.

    Reguła jest MECHANICZNA: małe litery, `.so` wypada, numer ABI zostaje przyklejony.
    Dzięki temu bramka nie trzyma pełnej drugiej listy „soname -> pakiet", która
    rozjechałaby się przy pierwszej nowej bibliotece.

    **Docstring jest przepisany, a nie dopisany obok — 07.09.2026.** Poprzednia wersja
    mówiła „nie tablicą wyjątków" i to już nieprawda: `NAZWY_PAKIETOW_WYJATKI` wyżej
    ma jeden wpis, bo reguła mechaniczna trafia w dziewięć sonames z dziesięciu i myli
    się na `libX11.so.6`. Zdanie o mechaniczności zostaje, bo opisuje ścieżkę
    dziewięciu przypadków; zniknęło z niego wyłącznie „nie tablicą wyjątków", które
    było prawdziwe tylko wobec dwóch bibliotek, dla jakich je napisano.
    """
    wyjatek = NAZWY_PAKIETOW_WYJATKI.get(soname)
    if wyjatek:
        return wyjatek
    match = re.fullmatch(r"(lib[A-Za-z0-9_+-]*)\.so\.(\d+)", soname)
    assert match, f"nie umiem wyprowadzić pakietu z sonamu {soname!r}"
    return (match.group(1) + match.group(2)).lower()


def test_the_package_name_exceptions_are_all_necessary():
    """Wyjątek, który powtarza regułę, przesłania ją i nikt tego nie zauważy.

    Tabela `NAZWY_PAKIETOW_WYJATKI` istnieje po to, żeby obsłużyć nazwy, których
    reguła mechaniczna nie wyprowadza. Wpis dający TO SAMO co reguła jest gorszy od
    braku wpisu: nie zmienia dziś zachowania, a jutro — gdy reguła przestanie
    działać dla czegoś innego — będzie dowodem, że „tabela i tak jest, więc dosypmy".

    Dlatego każdy wpis musi być POTRZEBNY, i to jest asercja na LICZBĘ różnic,
    nie na obecność wpisu.
    """
    zbedne = []
    for soname, pakiet in NAZWY_PAKIETOW_WYJATKI.items():
        match = re.fullmatch(r"(lib[A-Za-z0-9_+-]*)\.so\.(\d+)", soname)
        assert match, f"wyjątek na sonamie, którego reguła nawet nie rozbiera: {soname}"
        mechanicznie = (match.group(1) + match.group(2)).lower()
        if mechanicznie == pakiet:
            zbedne.append(f"{soname}: reguła sama daje {pakiet}")
    assert not zbedne, f"wyjątki powtarzające regułę mechaniczną: {zbedne}"

    # Kontrola w drugą stronę: tabela nie może być pusta bez powodu. Gdyby ktoś
    # wyczyścił ją „bo mechanicznie działa", `libX11.so.6` przestałby się mapować
    # i bramka sondy zapaliłaby się na siedmiu workflowach naraz — więc lepiej,
    # żeby zapaliła się tutaj, z nazwą przyczyny.
    assert _debian_package_for("libX11.so.6") == "libx11-6", (
        "libX11.so.6 nie mapuje się na libx11-6 — reguła mechaniczna daje libx116, "
        "a taki pakiet w Ubuntu 24.04 nie istnieje")


def kopie_listy_sonames():
    """Wszystkie kopie listy sonames w drzewie — `{(soname, …): [gdzie, …]}`.

    **Kopie liczone Z DRZEWA, nie z listy wpisanej w test**, i tego żąda pole
    „Skończone, gdy" pozycji 6.D44: liczba kopii jest POMIAREM. Wpisana tutaj
    zestarzałaby się przy pierwszym nowym workflowie i byłaby tą samą usterką,
    którą 6.D45 zmierzyło na `MIN_REPORTS`.

    Kopią jest **niepusta wartość `libraries:`** przekazywana akcji sondującej —
    to ona decyduje, o co job pyta `ldconfig`. Wzmianka o jednej bibliotece
    w prozie kopią NIE jest, i to rozróżnienie jest zmierzone: napis
    `libEGL.so.1` niesie 13 plików w drzewie, ale listę — siedem.
    """
    kopie = {}
    for name in _workflows():
        document = yaml.safe_load(_text(name))
        for jobname, job in (document.get("jobs") or {}).items():
            for step in job.get("steps") or []:
                if str(step.get("uses", "")) != PROBE_ACTION:
                    continue
                sonames = ((step.get("with") or {}).get("libraries") or "").split()
                if sonames:
                    kopie.setdefault(tuple(sorted(sonames)), []).append(
                        f"{name}:{jobname}")
    return kopie


def test_kazda_kopia_listy_sonames_niesie_TEN_SAM_zestaw():
    """6.D44: siedem kopii listy, a zgodności nie sprawdzało nic.

    **To ta sama rodzina co 6.D40, tylko o kopię dalej.** Tam sonda pytała
    o JEDNĄ bibliotekę z dziesięciu i mówiła prawdę o tej jednej, więc krok
    instalacji nie odpalał się nigdy. Tu każda kopia może pytać o INNY zestaw,
    a job, który sonduje jeden zestaw i instaluje drugi, wywraca się dopiero przy
    pierwszym renderze.

    **Dlaczego istniejąca bramka tego nie widziała, zmierzone 09.09.2026 na
    `d51b5df`.** `test_tool_installation_is_conditional_on_the_tool_being_missing`
    sprawdza, że każdy workflow sonduje to, co SAM instaluje — czyli każdą kopię
    osobno, wobec jej własnego zestawu apt. Podzbiór przechodzi: sonda zawężona
    w `blender-smoke.yml` z dziesięciu bibliotek do jednej dała **cały zestaw
    2050/2050 i kod 0**, bo `libEGL.so.1` mapuje się na `libegl1`, a `libegl1`
    w `blender.txt` stoi. Job zameldowałby `libs = present` po znalezieniu jednej
    biblioteki, pominął instalację i wywrócił się na pierwszym renderze.

    Ten test porównuje kopie **ze sobą**, więc podzbiór już nie przejdzie:
    zawężona kopia tworzy drugi zestaw i liczba zestawów przestaje być równa
    jedności.

    Kolejność w wartości `libraries:` jest **nieistotna** i dlatego sonames są
    sortowane: `ldconfig` jest pytany o każdą osobno, więc przestawienie dwóch
    nazw nie zmienia niczego w zachowaniu, a bramka na kolejność zapalałaby się
    na zmianie bez skutku (6.D27).
    """
    kopie = kopie_listy_sonames()
    assert kopie, (
        "ani jedna kopia listy sonames nie została znaleziona — skan przestał "
        "czytać workflowy albo krok sondujący zmienił kształt, a wtedy ta bramka "
        "jest zielona nad dowolnym rozjazdem")
    assert len(kopie) == 1, (
        "kopie listy sonames NIE są zgodne — job, który sonduje jeden zestaw, "
        "a instaluje drugi, wywraca się dopiero przy pierwszym renderze:\n"
        + "\n".join(
            "  zestaw %d (%d bibliotek), %d kopii: %s\n    %s"
            % (i, len(libs), len(gdzie), ", ".join(gdzie), " ".join(libs))
            for i, (libs, gdzie) in enumerate(sorted(kopie.items()), 1)))


def test_kopii_listy_sonames_jest_TYLE_ILE_WOLA_AKCJI_SONDUJACEJ():
    """Podłoga na liczbę kopii, ale **nie stała** — liczona z drzewa.

    Bramka wyżej porównuje kopie ze sobą i przy JEDNEJ kopii jest trywialnie
    zielona. Gdyby skan przestał widzieć szcześć z siedmiu wywołań — literówka
    w `PROBE_ACTION`, zmiana kształtu kroku, nowy sposób przekazania listy —
    zostałaby jedna kopia, jeden zestaw i **zielono**.

    Podłogą jest więc liczba wywołań akcji sondującej policzona **niezależnie**,
    prostym przejściem po tekście, i porównana z liczbą kopii, które zebrał
    parser YAML-a. Stałej tu nie ma świadomie: zestarzałaby się przy pierwszym
    nowym workflowie. Zmierzone 09.09.2026 na `d51b5df`: siedem wywołań, siedem
    kopii, jeden zestaw dziesięciu sonames.
    """
    wolania = sum(_text(name).count(PROBE_ACTION) for name in _workflows())
    zebrane = sum(len(gdzie) for gdzie in kopie_listy_sonames().values())
    assert wolania > 1, (
        "w drzewie jest %d wywołań %s — skan tekstowy przestał je widzieć, więc "
        "podłoga tej bramki nie chroni niczego" % (wolania, PROBE_ACTION))
    assert zebrane == wolania, (
        "parser YAML-a zebrał %d kopii listy sonames, a wywołań akcji sondującej "
        "jest w tekście %d — skan przestał czytać część workflowów, a wtedy "
        "porównanie kopii ze sobą jest zielone nad rozjazdem w tych nieczytanych"
        % (zebrane, wolania))


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
        document = yaml.safe_load(text)
        # KAŻDY job, nie pierwszy. `list(...values())[0]` czytał wyłącznie pierwszy
        # job i była to ta sama luka, którą #191 naprawiło w bramce czystego
        # workspace'u — utajona, bo dziś każdy workflow ma jeden job. Drugi job
        # z niebramkowaną instalacją przechodziłby tę kontrolę.
        for jobname, job in document["jobs"].items():
          steps = job["steps"]
          if not any("apt_install.sh" in str(step.get("run", "")) for step in steps):
              continue
          checked += 1

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
          # Sonda musi pytać o TO, co ten workflow instaluje — nie o „cokolwiek".
          #
          # Poprzednia wersja wymagała tylko `wanted.get("libraries")` niepustego,
          # choć komentarz obok obiecywał „bibliotekę, o którą pyta TEN workflow".
          # Sonda na `libfoo.so.1` przechodziła: niepusta, więc akcja czegoś szuka,
          # tylko nie tego, czego brak wywraca render. Prawda bierze się teraz
          # z zestawu apt, który ten sam workflow instaluje — nie z drugiej listy
          # wpisanej do testu.
          wanted = (probe[0].get("with") or {})
          packages = _apt_set_packages(_apt_set_of(text))
          sonames = (wanted.get("libraries") or "").split()
          assert sonames, \
              f"{name}: sonda nie podaje ani jednej biblioteki, więc zawsze zwróci present"
          for soname in sonames:
              package = _debian_package_for(soname)
              assert package in packages, (
                  f"{name}: sonda pyta o {soname} (pakiet {package}), a zestaw apt "
                  f"tego workflow tego nie instaluje: {sorted(packages)}")

          # Sonda poleceń musi iść za zestawem apt W OBIE STRONY, dla KAŻDEGO
          # polecenia z `POLECENIA_Z_PAKIETOW`, nie tylko dla `xvfb-run`.
          #
          # **Przepisane, a nie dopisane obok — 07.09.2026.** Poprzednia wersja
          # sprawdzała wyłącznie `xvfb-run` i uzasadniała to zdaniem „`xvfb-run`
          # jest jedyną RÓŻNICĄ między dwoma zestawami, więc jest też jedynym
          # miejscem, w którym sonda poleceń ma sens". Zdanie było prawdziwe, dopóki
          # różnica była jedna — i przestało być, gdy `godot-first-run.yml` padł na
          # `unzip: command not found` (kod 127, `woogitsu-linux-02`, run
          # 34155630333). `unzip` nie był ani sondowany, ani w żadnym zestawie apt,
          # więc sonda mówiła `present`, krok instalacji się nie odpalał, a job
          # wywracał się dopiero na rozpakowywaniu Godota — czternaście kroków dalej
          # niż powód. Ta sama usterka co przy bibliotekach, w drugim wymiarze.
          commands = (wanted.get("commands") or "").split()
          for polecenie, pakiet in sorted(POLECENIA_Z_PAKIETOW.items()):
              if pakiet in packages:
                  assert polecenie in commands, (
                      f"{name}: instaluje pakiet {pakiet}, a sonda o `{polecenie}` "
                      f"nie pyta — krok instalacji nie dostanie sygnału, że go brakuje")
              else:
                  assert polecenie not in commands, (
                      f"{name}: sonda pyta o `{polecenie}`, a zestaw apt tego "
                      f"workflow nie instaluje pakietu {pakiet}")

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
    name = "godot-first-run.yml"
    text = _text(name)

    # Rozstrzyga TREŚĆ `run:` kroków, nie surowy tekst pliku, i nie z ostrożności:
    # `dotnet test tests/Game.Tests` wpisane w KOMENTARZ przechodziło poprzednią
    # wersję tak samo dobrze jak polecenie, które się wykonuje. Ten plik ma
    # kilkadziesiąt wierszy komentarza i wyjaśnia w prozie, co uruchamia.
    document = yaml.safe_load(text)
    runs = "\n".join(str(step.get("run", ""))
                     for job in document["jobs"].values()
                     for step in job["steps"])

    assert "tests/Game.Tests/Game.Tests.csproj" in runs, (
        f"{name}: żaden krok nie odnosi się do tests/Game.Tests/Game.Tests.csproj — "
        f"projekt testowy warstwy silnika istniałby, a nie chodził")
    # Komunikat tej asercji był `text[:0]`, czyli PUSTY NAPIS: przy czerwonym
    # przebiegu dostawało się `AssertionError` bez ani jednej wskazówki. Teraz
    # mówi, czego nie znalazł i gdzie szukał.
    assert "dotnet test tests/Game.Tests" in runs, (
        f"{name}: w treści `run:` nie ma `dotnet test tests/Game.Tests`; "
        f"kroki wołają: {[s.get('name') for j in document['jobs'].values() for s in j['steps']]}")


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


def _shell_function(script, name):
    """Definicja funkcji shellowej wyjęta ze skryptu — po klamrach, nie po napisie.

    Nazwa funkcji jest tu WSKAŹNIKIEM, co uruchomić, a nie werdyktem: samo
    `expect_refusal()` w pliku nie mówi jeszcze, czy funkcja czegokolwiek wymaga.
    Ciało wychodzi stąd do harnessu i tam się WYKONUJE.

    Klamry liczone po odcięciu komentarza od `#` do końca wiersza. Wystarcza,
    bo ani `fail()`, ani `expect_refusal()` nie mają klamry wewnątrz napisu —
    gdyby kiedyś miały, `assert` na domknięcie niżej pokaże to wprost, zamiast
    po cichu wyciąć pół funkcji.
    """
    lines = script.splitlines()
    start = None
    for index, line in enumerate(lines):
        if re.match(r"^\s*" + re.escape(name) + r"\(\)\s*\{", line):
            start = index
            break
    assert start is not None, f"w skrypcie nie ma definicji `{name}()`"
    depth, collected = 0, []
    for line in lines[start:]:
        bare = line.split("#", 1)[0]
        depth += bare.count("{") - bare.count("}")
        collected.append(line)
        if depth == 0:
            break
    assert depth == 0, f"definicja `{name}()` nie domyka się klamrą"
    return "\n".join(collected)


#: Cztery przebiegi, którymi sprawdza się `expect_refusal()`: (etykieta, kod wyjścia
#: atrapy, czy atrapa zostawia plik, co wypisuje, czego test wymaga od harnessu).
#: Pierwszy MUSI przejść — bez niego „padło" z pozostałych trzech mogłoby pochodzić
#: z zepsutego harnessu, a nie z warunku, który jest mierzony.
REFUSAL_RUNS = (
    ("poprawna odmowa", 1, False, "odmowa: powód konkretny", 0, "[NEGATYW]"),
    ("polecenie nie padło", 0, False, "odmowa: powód konkretny", 1, "NIE padło"),
    ("odmowa zostawiła plik", 1, True, "odmowa: powód konkretny", 1, "zostawiła plik"),
    ("brak diagnozy w logu", 1, False, "traceback z innego powodu", 1, "nie ma diagnozy"),
)


def _run_expect_refusal(script_name, exit_code, leaves_file, message):
    """Uruchamia funkcję `expect_refusal()` WYJĘTĄ z bramki, na atrapie generatora.

    Blendera tu nie ma i nie jest potrzebny: mierzona jest funkcja, która czyta
    kod wyjścia, obecność pliku i log — a nie generator, który ją karmi. Atrapa
    kończy się zadanym kodem, opcjonalnie zostawia plik wyjściowy i wypisuje zadany
    komunikat, więc każdy z trzech warunków `expect_refusal()` da się rozbroić
    z osobna i zobaczyć, czy funkcja to zauważy.
    """
    import shutil
    import subprocess
    import tempfile

    script = open(os.path.join(ROOT, "tools", "ci", script_name),
                  encoding="utf-8").read()
    root = tempfile.mkdtemp(prefix="metro-negatyw-")
    try:
        generator = _shim(root, "generator",
                          'if [ -n "${FAKE_MESSAGE:-}" ]; then echo "$FAKE_MESSAGE"; fi\n'
                          'if [ "$FAKE_LEAVE" = 1 ]; then : > "$1"; fi\n'
                          'exit "$FAKE_CODE"\n')
        artefact = os.path.join(root, "wynik.glb")
        log = os.path.join(root, "przebieg.log")
        harness = os.path.join(root, "harness.sh")
        with open(harness, "w", encoding="utf-8") as handle:
            handle.write("#!/usr/bin/env bash\nset -euo pipefail\n"
                         + _shell_function(script, "fail") + "\n"
                         + _shell_function(script, "expect_refusal") + "\n"
                         + f'expect_refusal "proba" "{artefact}" "{log}"'
                           f' "odmowa: powód konkretny" "{generator}" "{artefact}"\n')
        env = dict(os.environ)
        env.update(FAKE_CODE=str(exit_code), FAKE_LEAVE="1" if leaves_file else "0",
                   FAKE_MESSAGE=message, LC_ALL="C.UTF-8")
        return subprocess.run(["bash", harness], env=env, capture_output=True,
                              text=True, encoding="utf-8", errors="replace")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def _assert_refusal_function_has_teeth(script_name):
    """Wspólny pomiar dla obu bramek: `expect_refusal()` wymaga wszystkich trzech rzeczy."""
    for label, code, leaves, message, expected, needle in REFUSAL_RUNS:
        result = _run_expect_refusal(script_name, code, leaves, message)
        where = result.stdout if expected == 0 else result.stderr
        assert (result.returncode == 0) == (expected == 0), (
            f"{script_name} / {label}: expect_refusal zwróciło {result.returncode}, "
            f"oczekiwano {'zera' if expected == 0 else 'niezera'}\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}")
        assert needle in where, (
            f"{script_name} / {label}: brak diagnozy /{needle}/ w wyjściu\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}")


def test_ci_the_station_details_gate_reads_the_reason_of_every_refusal():
    """Odmowa bez przeczytanego powodu nie jest bramką, tylko awarią.

    `station_details.sh` sprawdza sześć odmów i każda musi spełnić trzy warunki:
    polecenie padło, NIE zostawiło pliku wyjściowego, a w logu stoi konkretna
    diagnoza. Trzeci warunek jest tym, który odróżnia bramkę od „coś się wywaliło":
    bez niego test przechodzi także wtedy, gdy generator pada z zupełnie innego
    powodu — na przykład na literówce w nazwie pliku.

    Trzy warunki są tu SPRAWDZANE PRZEZ URUCHOMIENIE, a nie przez obecność napisu.
    Mutacja M5, zmierzona 04.09.2026: `if "$@" …; then fail …` zamienione na
    `"$@" … || true` plus `if false; then fail …; fi`, a `test ! -e "$glb"`
    i `grep -Eq "$pattern" "$log"` domknięte `|| true`. Wszystkie trzy napisy,
    o które pytała poprzednia wersja, zostały w pliku bez zmiany — bramka
    przechodziła zielono, a funkcja przyjmowała każdą odmowę, także taką, której
    nie było.

    Ta sama konwencja co negatywy w `blender_smoke.sh`.
    """
    _assert_refusal_function_has_teeth("station_details.sh")

    script = open(os.path.join(ROOT, "tools", "ci", "station_details.sh"),
                  encoding="utf-8").read()
    code = "\n".join(line for line in script.splitlines()
                     if not line.lstrip().startswith("#"))

    # Sześć odmów: dwie na peronach, cztery na słupkach. To liczba wywołań,
    # nie kształt funkcji — funkcję mierzy pomiar wyżej.
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

    Trzy warunki `expect_refusal()` są tu sprawdzane PRZEZ URUCHOMIENIE — mutacja
    M6 (04.09.2026) rozbroiła je wszystkie, zostawiając w pliku każdy napis,
    o który pytała poprzednia wersja, i bramka przeszła zielono.
    """
    _assert_refusal_function_has_teeth("material_style.sh")

    script = open(os.path.join(ROOT, "tools", "ci", "material_style.sh"),
                  encoding="utf-8").read()
    code = "\n".join(line for line in script.splitlines()
                     if not line.lstrip().startswith("#"))

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


def _env_prefixed_python_blocks(script):
    """Ciała heredoców `python3 - <<'PY'` poprzedzonych przypisaniami zmiennych.

    Prefiks `NAZWA=…` jest tu WSKAŹNIKIEM, który blok wziąć — to jedyny w tym
    skrypcie blok, który dostaje wejście przez otoczenie, więc jedyny, który da
    się uruchomić w oderwaniu od Blendera. Werdykt wydaje jego uruchomienie.
    """
    lines = script.splitlines()
    blocks = []
    for index, line in enumerate(lines):
        if not re.match(r"^[A-Z_]+=.*python3 - <<'PY'$", line):
            continue
        body = []
        for follow in lines[index + 1:]:
            if follow == "PY":
                break
            body.append(follow)
        blocks.append("\n".join(body))
    return blocks


def _glb_with_nodes(names):
    """Minimalny, poprawny GLB z chunkiem JSON o zadanych nazwach węzłów."""
    import json
    import struct

    document = json.dumps({"asset": {"version": "2.0"},
                           "nodes": [{"name": name} for name in names]}).encode("utf-8")
    document += b" " * ((4 - len(document) % 4) % 4)
    chunk = struct.pack("<II", len(document), 0x4E4F534A) + document
    return b"glTF" + struct.pack("<II", 2, 12 + len(chunk)) + chunk


def _run_scene_check(body, ids, nodes, report, blob=None):
    """Uruchamia wyjęty blok porównania presetów z GLB na podstawionym wejściu."""
    import json
    import shutil
    import subprocess
    import tempfile

    root = tempfile.mkdtemp(prefix="metro-glb-")
    try:
        config = os.path.join(root, "visual-style.json")
        out = os.path.join(root, "materials.glb")
        log = os.path.join(root, "run.log")
        with open(config, "w", encoding="utf-8") as handle:
            json.dump({"material_presets": [{"id": i} for i in ids]}, handle)
        with open(out, "wb") as handle:
            handle.write(blob if blob is not None else _glb_with_nodes(nodes))
        with open(log, "w", encoding="utf-8") as handle:
            handle.write(report + "\n")
        env = dict(os.environ)
        env.update(CONFIG=config, OUT=out, LOG=log, LC_ALL="C.UTF-8")
        return subprocess.run(["python3", "-"], input=body, env=env,
                              capture_output=True, text=True,
                              encoding="utf-8", errors="replace")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_ci_the_material_style_gate_checks_the_scene_not_only_the_generator_report():
    """Raport generatora nie jest weryfikacją generatora — to ta sama strona umowy.

    Pierwsza wersja tej bramki miała tu `grep -q "material_presets="`, czyli
    sprawdzała, że generator COKOLWIEK o sobie powiedział. Preset dopisany do
    `visual-style.json`, a nieobecny w scenie, przechodził przez to bez śladu.
    Dlatego bramka czyta chunk JSON wyeksportowanego GLB — bez Blendera, wprost
    ze struktury pliku — i porównuje nazwy węzłów z listą presetów.

    Ten test jest PRZEPISANY, nie dopisany obok. Poprzednia wersja pytała, czy
    w skrypcie stoją napisy `0x4E4F534A`, `swatch_` i `presety bez bryły w GLB`.
    Mutacja M7, zmierzona 04.09.2026: `missing = [i for i in declared if not …]`
    zamienione na `missing = []`. Wszystkie trzy napisy zostały w pliku, wiersz
    `problems.append("presety bez bryły w GLB: " …)` też — tylko nigdy się już nie
    wykonywał. Bramka przeszła zielono, a preset bez bryły w scenie znów byłby
    niewidoczny. Teraz blok porównania jest WYJMOWANY ze skryptu i URUCHAMIANY
    na pięciu podstawionych wejściach; Blender nie jest do tego potrzebny, bo
    struktura GLB czyta się z bajtów.
    """
    script = open(os.path.join(ROOT, "tools", "ci", "material_style.sh"),
                  encoding="utf-8").read()
    code = "\n".join(line for line in script.splitlines()
                     if not line.lstrip().startswith("#"))
    assert 'grep -q "material_presets="' not in code, (
        "bramka wróciła do sprawdzania samego raportu generatora")

    blocks = _env_prefixed_python_blocks(script)
    assert len(blocks) == 1, (
        f"oczekiwano jednego bloku porównania presetów z GLB, znaleziono {len(blocks)}")
    body = blocks[0]

    healthy = dict(ids=["a", "b"], nodes=["swatch_a", "swatch_b", "floor"],
                   report="material_presets=2 mesh_objects=3")
    # 1. Wejście zgodne MUSI przejść. Bez tego przebiegu „padło" z pozostałych
    #    czterech mogłoby pochodzić z podstawionego wejścia, a nie z porównania.
    ok = _run_scene_check(body, **healthy)
    assert ok.returncode == 0, (ok.returncode, ok.stdout, ok.stderr)
    assert "[ZGODNOŚĆ]" in ok.stdout, ok.stdout

    # 2. Preset z konfiguracji bez własnej bryły w GLB — liczba brył się zgadza,
    #    więc łapie to WYŁĄCZNIE porównanie nazw.
    missing = _run_scene_check(body, ids=["a", "b"],
                               nodes=["swatch_a", "swatch_zz", "floor"],
                               report="material_presets=2 mesh_objects=3")
    assert missing.returncode != 0, (missing.stdout, missing.stderr)
    assert "presety bez bryły w GLB" in missing.stderr, missing.stderr
    assert missing.stderr.rstrip().endswith("b"), (
        "diagnoza nie nazywa presetu, którego brakuje: " + missing.stderr)

    # 3. Bryła `swatch_` ponad liczbę presetów — drugi kierunek tej samej niezgody.
    extra = _run_scene_check(body, ids=["a", "b"],
                             nodes=["swatch_a", "swatch_b", "swatch_c", "floor"],
                             report="material_presets=2 mesh_objects=4")
    assert extra.returncode != 0, extra.stdout
    assert "ponad liczbę presetów" in extra.stderr, extra.stderr

    # 4. Raport generatora niezgodny z konfiguracją.
    lying = _run_scene_check(body, ids=["a", "b"],
                             nodes=["swatch_a", "swatch_b", "floor"],
                             report="material_presets=3 mesh_objects=3")
    assert lying.returncode != 0, lying.stdout
    assert "raport mówi" in lying.stderr, lying.stderr

    # 5. Plik, który nie jest GLB — bramka nie ma prawa uznać go za zgodny.
    junk = _run_scene_check(body, ids=["a"], nodes=[],
                            report="material_presets=1 mesh_objects=2",
                            blob=b"NIEGLB" + b"\0" * 26)
    assert junk.returncode != 0, junk.stdout
    assert "nie jest plikiem GLB" in junk.stderr, junk.stderr
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

# Komentarz łapany LENIWIE i do końca wiersza (`(.*?)`), nie jako jeden token.
# Z `(\S+)` wiersz `uses: actions/cache@v4 # nie wersja` nie pasował do wzorca
# W CAŁOŚCI, więc wywołanie na ruchomym tagu wypadało z zasięgu obu bramek —
# nie było „bez wersji", było niewidzialne.
#
# `(?:-\s*)?` NIE jest ostrożnością. YAML zapisuje krok na dwa sposoby i oba są
# poprawne: `- name: …` z `uses:` w następnym wierszu, albo `- uses: …` jednym
# wierszem. Dziś wszystkie 44 wywołania w tym repozytorium są w pierwszej formie,
# więc dziura była UTAJONA — dokładnie jak `next(iter(...))` niżej, gdzie wszystkie
# workflowy miały po jednym jobie. Zmierzone 04.09.2026: krok `- uses: actions/cache@v4`
# dopisany do `.github/actions/probe-tools/action.yml` przechodził wszystkie trzy
# bramki przypinania (`3/3 przeszło`), bo `^\s*uses:` nie pasuje do wiersza
# z myślnikiem. Rozszerzenie zasięgu na akcje lokalne bez tego nie domykało reguły
# §9 — zamykało ją dla jednej z dwóch składni.
ACTION_USE = re.compile(r"(?m)^\s*(?:-\s*)?uses:\s*(\S+)\s*(?:#\s*(.*?))?\s*$")


def _pinned_sources():
    """Pliki, w których `uses:` może stać: workflowy I akcje lokalne.

    Akcje lokalne nie z ostrożności. Po wydzieleniu 04.09.2026 treść kroków
    wyprowadziła się z dziesięciu workflowów DO `.github/actions/`, a trzy bramki
    przypinania zostały przy `_workflows()`. Zmierzone: krok `uses: actions/cache@v4`
    (ruchomy tag, bez komentarza z wersją) dopisany do
    `.github/actions/probe-tools/action.yml` przechodził wszystkie trzy — i całą
    suitę, 47/47. Akcja `composite` wolno wołać inne akcje, więc to nie jest
    hipoteza: reguła `CLAUDE.md` §9 nie obowiązywała dokładnie tam, gdzie dziś
    mieszka treść kroków. Ten sam powód i ten sam wzór, co
    `_action_files()` w `test_ci_no_pipe_into_head_under_pipefail`.
    """
    sources = [(name, _text(name)) for name in _workflows()]
    for path in _action_files():
        label = f"{os.path.basename(os.path.dirname(path))}/{os.path.basename(path)}"
        sources.append((label, open(path, encoding="utf-8").read()))
    return sources


def _external_uses(text):
    """Pary (odnośnik, komentarz) dla `uses:` wskazujących POZA to repozytorium.

    Komentarze pomijane, i to nie z pobłażliwości: oba pliki w `.github/actions/`
    OPISUJĄ w prozie własne wywołanie — `uses: ./.github/actions/...` stoi tam
    w komentarzu — a komentarze workflowów odsyłają do tych akcji tym samym
    napisem. Bramka czytająca cały plik łapie własne uzasadnienie i każe poprawić
    wyjaśnienie zamiast kodu. Ta sama pułapka, co przy bramce `| head` i przy
    bramkach `prune-merged-branches`.
    """
    for line in text.splitlines():
        if line.lstrip().startswith("#"):
            continue
        match = ACTION_USE.match(line)
        if not match:
            continue
        ref, comment = match.group(1), match.group(2)
        # `./…` to akcja lokalna: mieszka w tym repozytorium, więc nie ma czego
        # przypinać — jej treść jest w tym samym commicie co workflow.
        if "@" not in ref or ref.startswith("./"):
            continue
        yield ref, comment


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

    Zasięg to workflowy I akcje lokalne (`_pinned_sources()`) — powód tam.
    """
    unpinned = []
    checked = 0
    for label, text in _pinned_sources():
        for ref, _comment in _external_uses(text):
            checked += 1
            _name, version = ref.rsplit("@", 1)
            if not re.fullmatch(r"[0-9a-f]{40}", version):
                unpinned.append(f"{label}: {ref}")
    assert not unpinned, f"akcje na ruchomym tagu: {unpinned}"
    assert checked >= 20, checked


def test_every_pinned_action_says_which_version_the_commit_is():
    """SHA bez wersji jest nieczytelny i przez to nieaktualizowalny.

    `actions/checkout@d23441a4…` nie mówi człowiekowi nic: nie da się zobaczyć, czy to
    wersja sprzed roku, ani zdecydować, czy warto podnieść. Komentarz z wersją zamienia
    przypięcie z bariery w informację — i jest jedyną rzeczą, która sprawia, że
    przypinanie po SHA nie zamienia się w porzucanie akcji na zawsze.

    Zasięg to workflowy I akcje lokalne (`_pinned_sources()`) — powód tam.
    """
    missing = []
    checked = 0
    for label, text in _pinned_sources():
        for ref, comment in _external_uses(text):
            checked += 1
            if not re.fullmatch(r"v\d+(\.\d+)*", comment or ""):
                missing.append(f"{label}: {ref} # {comment}")
    assert not missing, f"przypięcia bez czytelnej wersji: {missing}"
    assert checked >= 20, checked


def test_the_same_action_is_pinned_to_the_same_commit_everywhere():
    """Dwa różne SHA tej samej akcji w jednym repozytorium to stan, nie decyzja.

    Bez tej kontroli aktualizacja „wszystkich checkoutów" zostawia jeden na starym
    commicie i nikt tego nie widzi — a właśnie ten jeden będzie potem tłumaczył, czemu
    jeden job zachowuje się inaczej niż wszystkie pozostałe.

    Zasięg to workflowy I akcje lokalne (`_pinned_sources()`) — powód tam.
    """
    seen = {}
    for label, text in _pinned_sources():
        for ref, _comment in _external_uses(text):
            action, sha = ref.rsplit("@", 1)
            seen.setdefault(action, {}).setdefault(sha, []).append(label)
    split = {a: v for a, v in seen.items() if len(v) > 1}
    assert not split, f"ta sama akcja na różnych commitach: {split}"
    assert len(seen) >= 4, seen


#: Stała sceny, z której tryb ręczny czyta prędkość dopuszczalną. `Sim.Runner` nie ma
#: prawa jej zobaczyć — `src/Sim.Runner` nie zależy od `src/Game`, bo tam mieszka Godot
#: (CLAUDE.md §4.9) — więc ścieżkę podaje CI. To znaczy, że w repozytorium leżą DWA
#: napisy, które muszą być tym samym napisem, i nic tego nie trzymało.
RUN_PLAN = os.path.join("src", "Game", "RunPlan.cs")
MANUAL_PLAN_CONST = re.compile(
    r'public const string ManualSpeedLimitPlanPath\s*=\s*"([^"]+)"')
#: Wywołanie `Sim.Runner replay` w kroku workflow, razem z jego argumentami. Szukane
#: w tekście z ROZWINIĘTYM łamaniem wiersza (`_unwrapped`), bo polecenia w tych krokach
#: są łamane odwrotnym ukośnikiem i wzorzec liniowy widziałby wyłącznie `--keys`.
REPLAY_CALL = re.compile(r"replay --keys [^\n]*")


def _manual_plan_path():
    text = open(os.path.join(ROOT, RUN_PLAN), encoding="utf-8").read()
    found = MANUAL_PLAN_CONST.findall(text)
    assert len(found) == 1, f"{RUN_PLAN}: stałych ManualSpeedLimitPlanPath {len(found)}"
    return found[0]


def _unwrapped(text):
    """Tekst workflow z rozwiniętym łamaniem wiersza odwrotnym ukośnikiem."""
    return re.sub(r"\\\n\s*", " ", text)


def _replay_calls():
    for name in _workflows():
        for call in REPLAY_CALL.findall(_unwrapped(_text(name))):
            yield name, " ".join(call.split())


def test_every_replayed_manual_run_reads_the_limit_from_the_scene_own_plan():
    """Rdzeń i scena mają brać prędkość dopuszczalną z JEDNEGO pliku.

    Powód jest zmierzony, nie hipotetyczny. #246 przestawiło scenę na 72,00 km/h
    z planu sygnalizacji, a `Sim.Runner replay` został wtedy pominięty i dalej brał
    80 km/h z `DriveScenario` — prędkość konstrukcyjną M7. Bramka trybu ręcznego
    porównuje obie strony przy progu 0 i była zielona przez cały ten czas, bo jej
    wzorzec wejść dochodzi do 65,22 km/h i limitu nie dotyka.

    Sam przebieg CI też to dziś łapie (obie strony wypisują wiersz `[LIMIT]`, a krok
    robi na nich `diff`), ale tamto wymaga runnera z Godotem. Ta kontrola pada
    natychmiast i bez niego.
    """
    expected = _manual_plan_path()
    calls = list(_replay_calls())
    assert len(calls) >= 4, f"wywołań replay w workflowach: {len(calls)}"

    # DOKŁADNIE JEDNO wywołanie wolno mieć bez planu: negatyw, który sprawdza, że taki
    # przejazd jest ODMOWĄ. Gdyby zwolnienie było regułą („pomiń wywołania bez planu"),
    # to każde nowe wywołanie bez `--signalling` wchodziłoby przez tę samą furtkę.
    bare = [(name, call) for name, call in calls if "--signalling" not in call]
    assert len(bare) == 1, (
        "wywołań `replay` bez --signalling: "
        + str([f"{n}: {c}" for n, c in bare])
        + " — wolno mieć jedno, i to negatyw odmowy")
    negative_name = bare[0][0]
    assert "replay wymaga --signalling" in _text(negative_name), (
        f"{negative_name}: jest wywołanie `replay` bez planu, ale nic nie sprawdza, "
        f"że to odmowa")

    for name, call in calls:
        if "--signalling" not in call:
            continue
        path = call.split("--signalling", 1)[1].split()[0]
        # Negatyw bramki sufitu celowo podaje plan podmieniony, w `build/`. To jest
        # jego treść, a nie usterka — ale plan spoza `build/` musi być TYM planem.
        if path.startswith("build/"):
            continue
        assert path == expected, (
            f"{name}: replay czyta plan `{path}`, a scena `{expected}` "
            f"({RUN_PLAN}) — dwa napisy, które miały być jednym")


def test_the_manual_plan_constant_is_the_one_the_scene_actually_reads():
    """Kontrola negatywna do testu wyżej, wykonana w pamięci.

    Sam test wyżej przeszedłby tak samo dobrze, gdyby `MANUAL_PLAN_CONST` przestał
    cokolwiek znajdować i `_manual_plan_path()` zwracał pustą ścieżkę — a wtedy
    porównywałby napis z workflow z niczym. Ta kontrola trzyma oba końce: stała
    istnieje, wskazuje na plik, który leży w repozytorium, i to jest plan.
    """
    path = _manual_plan_path()
    assert path.endswith(".json"), path
    full = os.path.join(ROOT, path)
    assert os.path.isfile(full), f"stała wskazuje na plik, którego nie ma: {path}"
    plan = open(full, encoding="utf-8").read()
    assert '"default_permitted_speed_kmh"' in plan, (
        f"{path} nie ma pola, z którego tryb ręczny bierze limit")


#: Wywołanie SCENY w trybie odtworzenia z planem sygnalizacji — czyli z ochroną kabiny.
SCENE_REPLAY_WITH_PLAN = ("--replay=", "--signalling=")


def _steps_with_run(name):
    """Kroki workflow, które mają blok `run:`, jako pary (nazwa kroku, treść)."""
    text = _unwrapped(_text(name))
    for match in re.finditer(r"^      - name: (.+?)$(.*?)(?=^      - name: |\Z)",
                             text, re.M | re.S):
        yield match.group(1).strip(), match.group(2)


def test_the_scene_and_the_core_switch_cab_protection_on_the_same_way():
    """`--signalling` znaczy po każdej stronie CO INNEGO i bramka musi to obejść.

    Scena nie ma przełącznika ATP: plan w trybie `classic_2026` JEST systemem
    z ochroną, a osobny przełącznik znaczyłby, że istnieje sieć z blokadami i bez
    ochrony (ten sam argument, co przy `LineCore.M7(atp: true)` w #234).
    `Sim.Runner replay` ma natomiast `--atp` osobno, bo bez tego nie dałoby się
    zbudować negatywu „ten sam przejazd bez ochrony musi się różnić".

    Skutek jest ZMIERZONY, nie teoretyczny: scena z samym `--signalling` zgadza się
    co do bajtu z rdzeniem `--signalling --atp` (201 wierszy), a z rdzeniem
    `--signalling` bez `--atp` NIE. Krok, który porównuje te dwie strony i zapomni
    `--atp`, pada dopiero na runnerze z Godotem — ta kontrola pada natychmiast
    i bez niego.
    """
    seen = 0
    for name in _workflows():
        for step, body in _steps_with_run(name):
            if not all(needle in body for needle in SCENE_REPLAY_WITH_PLAN):
                continue

            seen += 1
            calls = [" ".join(call.split()) for call in REPLAY_CALL.findall(body)]
            assert calls, (
                f"{name} / '{step}': scena dostaje plan sygnalizacji, a krok nie woła "
                f"rdzenia ani razu — nie ma czego z czym porównać")
            assert any("--atp" in call for call in calls), (
                f"{name} / '{step}': scena z `--signalling` MA ochronę kabiny, a rdzeń "
                f"bez `--atp` jej nie ma — porównanie przy progu 0 nie ma prawa przejść. "
                f"Wywołania rdzenia w tym kroku: {calls}")

    assert seen >= 1, (
        "żaden krok nie porównuje sceny pod sygnalizacją z rdzeniem — bramka kabiny "
        "pod ochroną zniknęła z workflow")

# 6.D25: uruchomienie tego pliku WPROST idzie ta sama droga, co caly zestaw —
# z licznikiem asercji i z odmowa przy zerze testow. Bez tej gałęzi `python3
# tools/tests/<modul>.py` konczyl sie kodem 0, nie wykonawszy ani jednego testu.
if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))


def test_ci_blender_installer_NAZYWA_powod_gdy_wersja_wyszla_pusta():
    """6.D39: `2>/dev/null` zamieniało trzy przyczyny w jeden pusty napis.

    Zmierzone 07.09.2026 na runnerze `woogitsu-linux-01`, run 34153517889, job
    `tunnel-alignment (L1_B)`: pobranie udane, suma SHA-256 zgodna, a jedyne, co
    job powiedział o przyczynie, to `zgłasza '', oczekiwano '5.2.1'`. Czytający
    nie miał z czego rozstrzygnąć, czy rozpakowanie poszło w złe miejsce, czy
    Blender nie wystartował — a różnią się one tym, kto ma co zrobić.

    Ta bramka jest WYKONAWCZA i sprawdza DWIE przyczyny osobno, bo bramka na jedną
    przechodziłaby z komunikatem, który mówi zawsze to samo zdanie.
    """
    import tempfile

    with tempfile.TemporaryDirectory() as root:
        # PRZYCZYNA 1: Blender nie startuje — ładowacz pisze na stderr, stdout pusty.
        # Dokładnie ten kształt, który `2>/dev/null` wyrzucało.
        brak = ("echo \"blender: error while loading shared libraries: "
                "libXi.so.6: cannot open shared object file\" >&2\n"
                "exit 127\n")
        archive, sha = _fake_blender_archive(os.path.join(root, "a"), "0.0.2", cialo=brak)
        wynik, _, wolany = _run_blender_installer(root, "nie-startuje", sha, archive, "0.0.2")

        assert wolany, "curl nie został wywołany, więc ścieżka rozpakowania się nie wykonała"
        assert wynik.returncode == 1, (wynik.returncode, wynik.stderr[-400:])
        assert "libXi.so.6" in wynik.stderr, (
            "instalator nie powtórzył stderr Blendera, czyli nadal gubi jedyną "
            f"informację o przyczynie: {wynik.stderr[-400:]}")
        assert "powód:" in wynik.stderr, wynik.stderr[-400:]

        # PRZYCZYNA 2: Blender startuje, kończy się zerem i NIC nie wypisuje.
        # Przedtem nieodróżnialne od przyczyny 1 — ten sam pusty napis.
        cicho = "exit 0\n"
        archive2, sha2 = _fake_blender_archive(os.path.join(root, "b"), "0.0.3", cialo=cicho)
        wynik2, _, _ = _run_blender_installer(root, "cichy", sha2, archive2, "0.0.3")

        assert wynik2.returncode == 1, (wynik2.returncode, wynik2.stderr[-400:])
        assert "nie wypisuje numeru" in wynik2.stderr, wynik2.stderr[-400:]

        # ROZSTRZYGAJĄCE: dwie przyczyny dają DWA RÓŻNE zdania. Bez tego bramka
        # przechodziłaby na komunikacie, który zawsze mówi to samo — czyli na
        # przyrządzie, który nadal nie mierzy.
        powod = lambda t: [w for w in t.splitlines() if "powód:" in w][0]
        assert powod(wynik.stderr) != powod(wynik2.stderr), (
            "obie przyczyny dostały ten sam komunikat, więc nadal są "
            f"nierozróżnialne: {powod(wynik.stderr)}")


def _prawdziwy_elf_bez_biblioteki(katalog, version):
    """Prawdziwy ELF, któremu BRAKUJE biblioteki współdzielonej. `None` bez gcc.

    Atrapa w postaci skryptu bash nie nadaje się do sprawdzenia gałęzi `ldd`:
    `ldd` na skrypcie mówi „not a dynamic executable" i nie wypisuje ani jednego
    `=> not found`, więc ta gałąź — jedyna, która na zepsutej maszynie podaje
    NAZWY brakujących pakietów — zostałaby bez kontroli.

    Konstrukcja odtwarza objaw dosłownie: program linkuje się z `libatrapa.so`,
    biblioteka jest po zlinkowaniu USUWANA, a ładowacz wypisuje wtedy dokładnie
    ten komunikat, który przyszedł z runnera `woogitsu-linux-01`:

        ./blender: error while loading shared libraries: libatrapa.so:
        cannot open shared object file: No such file or directory
    """
    import shutil
    import subprocess

    if shutil.which("gcc") is None or shutil.which("ldd") is None:
        return None

    tree = f"blender-{version}-linux-x64"
    payload = os.path.join(katalog, "payload", tree)
    os.makedirs(payload, exist_ok=True)
    with open(os.path.join(katalog, "lib.c"), "w", encoding="utf-8") as handle:
        handle.write("int fake_symbol(void){return 7;}\n")
    with open(os.path.join(katalog, "main.c"), "w", encoding="utf-8") as handle:
        handle.write('#include <stdio.h>\nint fake_symbol(void);\n'
                     f'int main(void){{printf("Blender {version}\\n");'
                     'return fake_symbol()-7;}\n')
    lib = os.path.join(katalog, "libatrapa.so")
    binary = os.path.join(payload, "blender")
    for cmd in (["gcc", "-shared", "-fPIC", "-o", lib, os.path.join(katalog, "lib.c")],
                ["gcc", "-o", binary, os.path.join(katalog, "main.c"),
                 "-L" + katalog, "-latrapa", "-Wl,-rpath,$ORIGIN"]):
        if subprocess.run(cmd, capture_output=True).returncode != 0:
            return None
    os.unlink(lib)          # od tej chwili ładowacz nie ma czego wczytać
    return payload, tree


def test_ci_blender_installer_WYLICZA_brakujace_biblioteki_z_ldd():
    """6.D39: na zepsutej maszynie to JEDYNY komunikat, z którego wynika działanie.

    Pozostałe gałęzie mówią „coś nie tak z plikiem"; ta podaje NAZWY bibliotek,
    czyli wprost listę pakietów do doinstalowania. Lista jest wyliczona przez
    `ldd`, nie wpisana z ręki — wpisana z ręki byłaby zgadnięta, a zgadnięta lista
    braków wygląda jak pomiar i nim nie jest.
    """
    import hashlib
    import tarfile
    import tempfile

    with tempfile.TemporaryDirectory() as root:
        zrobione = _prawdziwy_elf_bez_biblioteki(root, "0.0.4")
        if zrobione is None:
            AG.skip("brak gcc albo ldd — tej gałęzi nie da się sprawdzić uczciwie")
        payload, tree = zrobione

        archive = os.path.join(root, "atrapa-elf.tar.xz")
        with tarfile.open(archive, "w:xz") as tar:
            tar.add(payload, arcname=tree)
        with open(archive, "rb") as handle:
            sha = hashlib.sha256(handle.read()).hexdigest()

        wynik, _, wolany = _run_blender_installer(root, "elf", sha, archive, "0.0.4")

        assert wolany, "curl nie został wywołany, więc ścieżka rozpakowania się nie wykonała"
        assert wynik.returncode == 1, (wynik.returncode, wynik.stderr[-500:])
        powod = [w for w in wynik.stderr.splitlines() if "powód:" in w]
        assert powod, wynik.stderr[-500:]
        assert "brakuje bibliotek systemowych" in powod[0], (
            "instalator nie doszedł do gałęzi `ldd`, więc nie podał NAZW brakujących "
            f"bibliotek: {powod[0]}")
        assert "libatrapa.so" in powod[0], (
            f"komunikat mówi o brakach, ale żadnego nie nazywa: {powod[0]}")
