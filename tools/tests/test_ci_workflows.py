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
import subprocess
import sys
import tempfile

import yaml

import assertion_gate as AG
import tree_walk as TW

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
    # OSIEM od 16.09.2026 (6.D240), i ten komentarz jest przepisany, a nie dopisany
    # obok. Poprzednia wersja mówiła „siedem, odkąd doszedł `material-style-smoke.yml`".
    # Ósmy krok to `python-tests.yml` i jest PIERWSZYM, który nie instaluje niczego
    # do renderowania: job `tools` nie miał dotąd ani sondy, ani instalacji, a zależał
    # od PyYAML przez pięć modułów zestawu. Powód liczby zostaje ten sam co był:
    # workflow, który PRZESTAŁ instalować, nie ma wypaść z pętli po cichu — pętla po
    # samych znalezionych krokach przeszłaby wtedy pusta i zielona.
    assert checked == 8, f"oczekiwano ośmiu kroków instalacji, znaleziono {checked}"


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
    # OSIEM od 16.09.2026 (6.D240), i ten komentarz jest przepisany, a nie dopisany
    # obok. Poprzednia wersja mówiła „siedem, odkąd doszedł `material-style-smoke.yml`".
    # Ósmy krok to `python-tests.yml` i jest PIERWSZYM, który nie instaluje niczego
    # do renderowania: job `tools` nie miał dotąd ani sondy, ani instalacji, a zależał
    # od PyYAML przez pięć modułów zestawu. Powód liczby zostaje ten sam co był:
    # workflow, który PRZESTAŁ instalować, nie ma wypaść z pętli po cichu — pętla po
    # samych znalezionych krokach przeszłaby wtedy pusta i zielona.
    assert checked == 8, f"oczekiwano ośmiu kroków instalacji, znaleziono {checked}"


PACKAGE_SETS = os.path.join(ROOT, "tools", "ci", "apt-packages")


def _declared_set(step):
    match = re.search(r"apt_install\.sh --set ([A-Za-z0-9_-]+)", step)
    return match.group(1) if match else None


def _sonda_pyta_o_sonames(name):
    """Czy KTÓRYKOLWIEK job tego workflowa sonduje biblioteki współdzielone.

    Odróżnia job renderujący od joba czysto pythonowego bez drugiej listy nazw —
    czyta to, co w drzewie naprawdę stoi w `libraries:` (6.D213).
    """
    document = yaml.safe_load(_text(name))
    for job in (document.get("jobs") or {}).values():
        for step in job.get("steps") or []:
            if str(step.get("uses", "")) != PROBE_ACTION:
                continue
            if ((step.get("with") or {}).get("libraries") or "").split():
                return True
    return False


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
            # Sam Blender przychodzi z przypiętego tarballa
            # (`test_ci_blender_workflows_install_the_pinned_...`), więc zestawy niosą
            # biblioteki systemowe i — od 16.09.2026 — moduły Pythona.
            #
            # WARUNEK EGL DOTYCZY ZESTAWÓW RENDERUJĄCYCH, a nie wszystkich, i to zdanie
            # jest przepisane, a nie dopisane obok. Poprzednia wersja żądała `libegl1`
            # od KAŻDEGO zestawu i była prawdziwa wobec drzewa, w którym każdy zestaw
            # renderował. `python.txt` nie renderuje nic — job `tools` uruchamia sam
            # zestaw testów — więc dziesięć bibliotek startowych Blendera byłoby tam
            # instalacją 190 MB pod nic.
            #
            # Kryterium jest MECHANICZNE i czytane Z DRZEWA, nie z drugiej listy nazw
            # zestawów: renderuje ten job, którego sonda pyta o sonames. Zestaw
            # instalowany przez taki job musi dawać kontekst EGL, bo bez niego Blender
            # startuje i wywraca się dopiero przy pierwszym renderze.
            if _sonda_pyta_o_sonames(name):
                assert "libegl1" in packages, (declared, packages)
            assert "blender" not in packages, (declared, packages,
                                               "zestaw apt znów instaluje Blendera")
    # OSIEM od 16.09.2026 (6.D240), i ten komentarz jest przepisany, a nie dopisany
    # obok. Poprzednia wersja mówiła „siedem, odkąd doszedł `material-style-smoke.yml`".
    # Ósmy krok to `python-tests.yml` i jest PIERWSZYM, który nie instaluje niczego
    # do renderowania: job `tools` nie miał dotąd ani sondy, ani instalacji, a zależał
    # od PyYAML przez pięć modułów zestawu. Powód liczby zostaje ten sam co był:
    # workflow, który PRZESTAŁ instalować, nie ma wypaść z pętli po cichu — pętla po
    # samych znalezionych krokach przeszłaby wtedy pusta i zielona.
    assert checked == 8, f"oczekiwano ośmiu kroków instalacji, znaleziono {checked}"


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


#: Skrypty w `tools/ci/`, które krok może zawołać; ich treść liczy się do tego, jakich
#: poleceń krok UŻYWA. Bez tego bramka niżej byłaby ślepa dokładnie na przypadek, dla
#: którego powstała: `Download Godot mono` nie ma w swoim `run:` ani `curl`, ani
#: `unzip` — ma `bash tools/ci/godot_install.sh`, a polecenia są w skrypcie.
WOLANIE_SKRYPTU = re.compile(r"bash\s+(tools/ci/[A-Za-z0-9_./-]+\.sh)")


def _polecenia_w_kodzie(kod, szukane):
    """Które z `szukane` polecenia woła ten kod, z komentarzami odciętymi."""
    kod = _bez_komentarzy_powloki(kod)
    return {p for p in szukane
            if re.search(r"(?<![\w./-])%s(?![\w-])" % re.escape(p), kod)}


def _polecenia_kroku(step, szukane):
    """Polecenia użyte przez krok — wprost albo przez skrypt, który krok uruchamia."""
    run = str(step.get("run") or "")
    uzyte = _polecenia_w_kodzie(run, szukane)
    for wzgledna in WOLANIE_SKRYPTU.findall(run):
        sciezka = os.path.join(ROOT, wzgledna)
        if os.path.isfile(sciezka):
            uzyte |= _polecenia_w_kodzie(open(sciezka, encoding="utf-8").read(), szukane)
    return uzyte


def kroki_uzywajace_przed_instalacja(document):
    """`(indeks, nazwa, polecenia)` kroków wołających pakietowane polecenie za wcześnie."""
    zle = []
    for job in document["jobs"].values():
        steps = job.get("steps") or []
        instalacja = [i for i, s in enumerate(steps)
                      if "apt_install.sh" in str(s.get("run") or "")]
        if not instalacja:
            continue
        granica = instalacja[0]
        for indeks, step in enumerate(steps):
            if indeks >= granica:
                continue
            uzyte = _polecenia_kroku(step, POLECENIA_Z_PAKIETOW)
            if uzyte:
                zle.append((indeks, step.get("name"), sorted(uzyte), granica))
    return zle


def test_ci_no_step_uses_a_packaged_command_before_installing_it():
    """Polecenie z tabeli pakietów jest wołane PO kroku, który je instaluje — 6.D77.

    **Skąd.** `godot-first-run.yml` wołał `tools/ci/godot_install.sh` na indeksie 6,
    a sonda i instalacja stały na indeksie 14 — czyli `curl` i `unzip` schodziły
    z maszyny OSIEM KROKÓW przed krokiem, który je zapewnia. Nie jest to
    „zepsułoby się, gdyby": ta droga odpaliła się już raz, 07.09.2026, jako
    `unzip: command not found` (kod 127, run 34155630333). Naprawiono wtedy sam brak
    pakietu i zostawiono kolejność, więc warunek powrotu — świeża maszyna puli albo
    nowy pin wersji silnika — został nietknięty.

    **Bramka liczy INDEKSY, nie czyta nazw kroków.** Ta sama własność, którą pilnuje
    `test_ci_no_workflow_uses_blender_before_installing_it` dla `$BLENDER_BIN`, tyle
    że dla wszystkich poleceń z `POLECENIA_Z_PAKIETOW` naraz — i **przez skrypty**,
    bo w tym jedynym zmierzonym przypadku polecenia nie było w `run:` kroku wcale.
    """
    for name in _workflows():
        document = yaml.safe_load(_text(name))
        zle = kroki_uzywajace_przed_instalacja(document)
        assert zle == [], "\n".join(
            "%s: krok %d '%s' woła %s, a instalacja jest dopiero w kroku %d"
            % (name, indeks, nazwa, polecenia, granica)
            for indeks, nazwa, polecenia, granica in zle)


def test_the_order_gate_reads_the_scripts_a_step_runs_and_names_the_file():
    """Kontrola negatywna, WYKONANA na sztucznym workflowie.

    Trzy asercje, bo trzy różne rzeczy mogą tę bramkę uciszyć: brak kroku instalacji
    (wtedy nie ma granicy), polecenie schowane w skrypcie (wtedy `run:` jest czysty)
    i polecenie w komentarzu (wtedy nie jest wołane).
    """
    def dokument(kroki):
        return {"jobs": {"j": {"steps": kroki}}}

    instalacja = {"name": "Install", "run": "bash tools/ci/apt_install.sh --set blender"}

    # (1) polecenie WPROST przed instalacją — zgłoszone, z nazwą kroku.
    zle = kroki_uzywajace_przed_instalacja(dokument(
        [{"name": "Pobierz", "run": 'curl -fL -o x "$URL"'}, instalacja]))
    assert zle == [(0, "Pobierz", ["curl"], 1)], zle

    # (2) polecenie w SKRYPCIE, którego `run:` kroku nie zawiera — zmierzony przypadek
    # 6.D77: `Download Godot mono` ma w `run:` wyłącznie `bash tools/ci/godot_install.sh`.
    zle = kroki_uzywajace_przed_instalacja(dokument(
        [{"name": "Download Godot mono", "run": "bash tools/ci/godot_install.sh"},
         instalacja]))
    assert zle == [(0, "Download Godot mono", ["curl", "unzip"], 1)], zle

    # (3) po instalacji ten sam krok jest w porządku — bramka mierzy KOLEJNOŚĆ,
    # a nie obecność polecenia.
    assert kroki_uzywajace_przed_instalacja(dokument(
        [instalacja,
         {"name": "Download Godot mono", "run": "bash tools/ci/godot_install.sh"}])) == []

    # (4) polecenie w komentarzu nie jest wołaniem.
    assert kroki_uzywajace_przed_instalacja(dokument(
        [{"name": "Komentarz", "run": "# curl tu nie chodzi\necho ok"}, instalacja])) == []


def test_the_order_gate_is_looking_at_workflows_that_actually_install_packages():
    """Kontrola przyrządu: cisza wyżej znaczy coś tylko przy istniejącej granicy.

    Bramka pomija job bez kroku `apt_install.sh` — słusznie, bo bez niego nie ma
    czego porównywać. Bez tego wiersza usunięcie instalacji ze WSZYSTKICH workflowów
    zostawiłoby bramkę zieloną.
    """
    z_instalacja = [n for n in _workflows() if "apt_install.sh" in _text(n)]
    assert len(z_instalacja) == 8, z_instalacja
    # I że jest co mierzyć: workflow RENDERUJĄCY woła co najmniej jedno polecenie
    # z tabeli, choćby przez instalator Blendera.
    #
    # **Warunek jest zawężony do renderujących 16.09.2026 (6.D240) i to zdanie jest
    # przepisane, a nie dopisane obok.** Poprzednia wersja żądała polecenia z tabeli
    # od KAŻDEGO z siedmiu i była prawdziwa wobec drzewa, w którym każdy workflow
    # instalujący cokolwiek instalował też `curl`. `python-tests.yml` instaluje
    # MODUŁ Pythona i nie woła ani `curl`, ani `unzip`, ani `xvfb-run` — nie ma tam
    # czego pilnować bramce kolejności i **to jest prawda o nim, a nie jego usterka**.
    # Zawężenie idzie po tym samym kryterium, co warunek EGL wyżej: czy sonda pyta
    # o sonames. Liczba renderujących jest asercją, więc wypadnięcie któregoś z nich
    # nie przejdzie po cichu.
    renderujace = [n for n in z_instalacja if _sonda_pyta_o_sonames(n)]
    assert len(renderujace) == 7, renderujace
    for name in renderujace:
        document = yaml.safe_load(_text(name))
        steps = list(document["jobs"].values())[0]["steps"]
        uzyte = set()
        for step in steps:
            uzyte |= _polecenia_kroku(step, POLECENIA_Z_PAKIETOW)
        assert uzyte, (name, "żaden krok nie woła polecenia z tabeli pakietów — "
                             "bramka kolejności jest tu trywialnie zielona")


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


#: Wywołanie akcji LOKALNEJ — mieszkającej w tym repozytorium, więc jej treść jest
#: kodem, który ten job wykona. Akcja z Marketplace (`actions/checkout@<sha>`) nie
#: liczy się tu wcale: jest przypięta po SHA i nie zmienia się razem z gałęzią.
AKCJA_LOKALNA = re.compile(r"uses:\s*\./(\.github/actions/[A-Za-z0-9_-]+)")

#: Wzorzec, który musi stać w `paths:` workflowa używającego akcji lokalnej.
KATALOG_AKCJI = ".github/actions/**"


def akcje_lokalne(text):
    """Akcje lokalne, których ten workflow używa — z tekstu, nie z listy w teście."""
    return sorted(set(AKCJA_LOKALNA.findall(text)))


def workflowy_bez_wzorca_akcji():
    """`(plik, akcje, wzorce)` workflowów, które używają akcji lokalnej i mają filtr,
    a filtr katalogu akcji nie obejmuje."""
    zle = []
    for name in _workflows():
        text = _text(name)
        akcje = akcje_lokalne(text)
        if not akcje:
            continue
        patterns = _paths_block(text)
        if patterns is None:      # brak filtra = odpala się zawsze
            continue
        if KATALOG_AKCJI not in patterns:
            zle.append((name, akcje, patterns))
    return zle


def test_ci_workflows_using_a_local_action_are_triggered_by_that_action():
    """Zmiana akcji lokalnej musi odpalać joby, które jej używają — 6.D78.

    **Bramka BLIŹNIACZA do `test_ci_workflows_running_tools_ci_are_triggered_by_tools_ci`,
    i to jest cały argument za jej istnieniem.** Tamta powstała z pomiaru z 02.09.2026:
    `vehicle_clearance.sh` był wołany w `tunnel-alignment.yml`, ale w `paths:` siedział
    tylko `tools/ci/tunnel_alignment.sh`, więc wstrzyknięty `exit 3` **przeszedł** —
    job w ogóle się nie uruchomił. Akcja lokalna jest dokładnie tym samym rodzajem
    kodu: mieszka w repozytorium, zmienia się razem z gałęzią i jej treść wykonuje
    ten sam runner. Brakowało jej rodzeństwa.

    Zmierzone 09.09.2026: **siedem** workflowów używa akcji lokalnej i ma filtr,
    i **żaden** nie miał w nim katalogu akcji. Sonda narzędzi
    (`.github/actions/probe-tools`) nie miała przy tym ANI JEDNEGO konsumenta bez
    filtra — czyli jej zmiana nie była przed scaleniem wykonywana wcale.
    """
    zle = workflowy_bez_wzorca_akcji()
    assert zle == [], "\n".join(
        "%s: używa %s, a `paths:` nie obejmuje `%s` — zmiana akcji nie odpali "
        "tego joba. Wzorce dziś: %s" % (name, akcje, KATALOG_AKCJI, patterns)
        for name, akcje, patterns in zle)


def test_the_local_action_gate_is_looking_at_workflows_that_use_local_actions():
    """Kontrola przyrządu, w obie strony — pusta lista wyżej sama nic nie znaczy.

    Liczby są tu ZMIERZONE, a nie okrągłe: siedem workflowów z akcją i filtrem, dwa
    z akcją i BEZ filtra (`python-tests.yml`, `sim-tests.yml` — jedyni konsumenci,
    u których zmiana akcji jest dziś przed scaleniem wykonywana), jeden z akcją
    i bez wyzwalacza `pull_request` w ogóle (`prune-merged-branches.yml`).
    Ten ostatni **ma zostać poza listą** — tego wprost żąda pole „Skończone, gdy",
    żeby bramka nie wymuszała martwych wpisów.
    """
    z_akcja = [n for n in _workflows() if akcje_lokalne(_text(n))]
    z_filtrem = [n for n in z_akcja if _paths_block(_text(n)) is not None]
    bez_filtra = [n for n in z_akcja if _paths_block(_text(n)) is None]
    assert len(z_akcja) == 10, z_akcja
    assert len(z_filtrem) == 7, z_filtrem
    assert sorted(bez_filtra) == ["prune-merged-branches.yml", "python-tests.yml",
                                  "sim-tests.yml"], sorted(bez_filtra)
    # `prune-merged-branches.yml` nie ma `pull_request` wcale — i to jest powód,
    # dla którego stoi w tej trójce, a nie razem z dwoma pozostałymi.
    assert "pull_request" not in _text("prune-merged-branches.yml").split("permissions:")[0]
    for name in ("python-tests.yml", "sim-tests.yml"):
        assert "pull_request" in _text(name).split("permissions:")[0], name


def test_the_local_action_gate_names_the_file_when_the_pattern_is_removed():
    """Kontrola negatywna, WYKONANA na sztucznym workflowie.

    Cztery przypadki, bo cztery różne rzeczy mogą tę bramkę uciszyć: brak wzorca
    (ma zapalać), brak filtra (ma milczeć), brak akcji lokalnej (ma milczeć)
    i akcja z Marketplace przypięta po SHA (ma milczeć — nie zmienia się z gałęzią).
    """
    import tempfile

    def sprawdz(tekst):
        with tempfile.TemporaryDirectory() as katalog:
            sciezka = os.path.join(katalog, "sztuczny.yml")
            with open(sciezka, "w", encoding="utf-8") as uchwyt:
                uchwyt.write(tekst)
            text = open(sciezka, encoding="utf-8").read()
            akcje = akcje_lokalne(text)
            patterns = _paths_block(text)
            return akcje, patterns

    filtr_waski = ("on:\n  pull_request:\n    paths:\n      - 'tools/ci/**'\n"
                   "jobs:\n  j:\n    steps:\n"
                   "      - uses: ./.github/actions/probe-tools\n")
    akcje, patterns = sprawdz(filtr_waski)
    assert akcje == [".github/actions/probe-tools"], akcje
    assert KATALOG_AKCJI not in patterns, patterns

    filtr_szeroki = filtr_waski.replace("      - 'tools/ci/**'\n",
                                        "      - 'tools/ci/**'\n      - '%s'\n"
                                        % KATALOG_AKCJI)
    akcje, patterns = sprawdz(filtr_szeroki)
    assert KATALOG_AKCJI in patterns, patterns

    # Bez filtra job odpala się zawsze — wzorca wymagać nie ma po co.
    akcje, patterns = sprawdz("on:\n  pull_request:\njobs:\n  j:\n    steps:\n"
                              "      - uses: ./.github/actions/probe-tools\n")
    assert akcje and patterns is None

    # Akcja z Marketplace przypięta po SHA nie jest akcją lokalną: nie mieszka
    # w tym repozytorium i nie zmienia się razem z gałęzią.
    akcje, _patterns = sprawdz(
        "on:\n  pull_request:\n    paths:\n      - 'tools/ci/**'\n"
        "jobs:\n  j:\n    steps:\n"
        "      - uses: actions/checkout@d23441a48e516b6c34aea4\n")
    assert akcje == [], akcje


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


#: 6.D52. Człon, który MUSI stać w ziarnie grupy `concurrency`, żeby grupa nie
#: zbierała przebiegów RÓŻNYCH workflowów. Nie jest to gust: 09.09.2026 na pull
#: requeście #450 ziarno `metro-ci-${{ github.ref }}` — bez tego członu, wpisane
#: do ośmiu workflowów — dało osiem przebiegów utworzonych w TEJ SAMEJ sekundzie
#: (18:43:03Z), z których jeden ruszył, JEDEN czekał, a SZEŚĆ dostało `cancelled`
#: w ciągu dwóch sekund. Wśród anulowanych był `Sim core tests`, czyli dokładnie
#: ten job, którego mierzalności miała bronić serializacja. Pomiar:
#: `reports/serializacja-jobow-ci.md`.
#:
#: Czego ta bramka NIE zakazuje: ziarna per-workflow (`${{ github.workflow }}-…`).
#: Tam przebieg anulowany jest przebiegiem WYPARTYM przez nowszy commit tej samej
#: gałęzi, a nie przebiegiem sąsiada — to jest inna rzecz i wolno jej być.
CONCURRENCY_SEPARATOR = "github.workflow"


def _concurrency_groups(document):
    """Wszystkie ziarna grup `concurrency` w dokumencie — z poziomu pliku i jobów."""
    found = []
    for where, value in [("workflow", document.get("concurrency"))] + [
            (f"job {job_id}", (job or {}).get("concurrency"))
            for job_id, job in (document.get("jobs") or {}).items()]:
        if value is None:
            continue
        group = value.get("group") if isinstance(value, dict) else value
        found.append((where, group))
    return found


def _concurrency_fault(group):
    """Powód, dla którego ziarno zbierałoby RÓŻNE workflowy — albo `None`."""
    if not isinstance(group, str) or not group.strip():
        return f"ziarno nie jest napisem: {group!r}"
    if CONCURRENCY_SEPARATOR not in group:
        return (f"ziarno {group!r} nie zawiera `{CONCURRENCY_SEPARATOR}`, więc "
                f"przebiegi różnych workflowów trafią do jednej grupy — "
                f"a tam wszystko poza jednym oczekującym jest anulowane")
    return None


def test_no_concurrency_group_collects_runs_of_different_workflows():
    """Żadna grupa `concurrency` nie miesza workflowów.

    Bramka jest tu dlatego, że 2087 testów tego zestawu przepuściło bez jednego
    czerwonego wiersza commit wkładający osiem workflowów do jednej grupy — a ten
    commit kasował sześć z ośmiu przebiegów pull requesta. Zielony zestaw mówił
    wtedy o pliku, którego skutku nikt nie oglądał.
    """
    wrong = []
    checked = 0
    for name in _workflows():
        document = yaml.safe_load(_text(name))
        checked += 1
        for where, group in _concurrency_groups(document):
            reason = _concurrency_fault(group)
            if reason:
                wrong.append(f"{name} ({where}): {reason}")
    assert not wrong, f"grupy `concurrency` mieszające workflowy: {wrong}"
    # Pętla po samych ZNALEZIONYCH grupach przeszłaby pusta i zielona także wtedy,
    # gdyby `_workflows()` przestało cokolwiek zwracać. Liczba jak w bramce runnera.
    assert checked >= 7, f"sprawdzono tylko {checked} plików — pętla nie widzi katalogu"


def test_the_concurrency_gate_fails_on_the_seed_that_cancelled_six_runs():
    """Kontrola negatywna: ziarno zmierzone na #450 musi być błędem.

    Pierwsze dwie asercje niosą DOSŁOWNIE tekst, który stał 09.09.2026 w ośmiu
    workflowach, i ziarno globalne bez żadnego wyrażenia. Trzy ostatnie pilnują,
    żeby „wszystko jest błędem" nie było dla bramki nie do odróżnienia od detekcji.
    """
    assert _concurrency_fault("metro-ci-${{ github.ref }}")
    assert _concurrency_fault("metro-ci")
    assert _concurrency_fault("${{ github.ref }}")
    assert _concurrency_fault(None)
    assert _concurrency_fault("")

    assert _concurrency_fault("${{ github.workflow }}-${{ github.ref }}") is None
    assert _concurrency_fault("${{ github.workflow }}") is None
    # Ziarno CZYTANE Z DOKUMENTU, nie z napisu podanego ręcznie — bez tego bramka
    # sprawdzałaby wyłącznie własną funkcję, a nie drogę od pliku do werdyktu.
    zly = yaml.safe_load("concurrency:\n"
                         "  group: metro-ci-${{ github.ref }}\n"
                         "  cancel-in-progress: false\n"
                         "jobs:\n  a:\n    runs-on: self-hosted\n")
    assert [_concurrency_fault(g) for _, g in _concurrency_groups(zly)] != [None]
    dobry = yaml.safe_load("jobs:\n  a:\n    runs-on: self-hosted\n"
                           "    concurrency:\n"
                           "      group: ${{ github.workflow }}-${{ github.ref }}\n")
    assert [_concurrency_fault(g) for _, g in _concurrency_groups(dobry)] == [None]
    # Plik bez `concurrency` nie ma czego naruszyć i nie może dać ani jednego wiersza.
    assert _concurrency_groups(yaml.safe_load("jobs:\n  a:\n    runs-on: self-hosted\n")) == []


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


#: 6.D63. Jedyna dozwolona OTOCZKA warunku fork-PR. Job, który ma dać sygnał także
#: wtedy, gdy job poprzedzający PRZEGRAŁ, musi nieść `always()`: bez niego `needs:`
#: zamienia awarię poprzednika w POMINIĘCIE, a job pominięty nie mówi o niczym.
#: Otoczka niczego nie zdejmuje — alternatywa dwóch członów zostaje wymagana
#: w całości, tyle że wewnątrz koniunkcji, i sprawdza to ta sama bramka.
FORK_GUARD_WRAPPER = "always()"


def _fork_guard_members(condition):
    """Człony alternatywy fork-PR, z dozwoloną jedną otoczką `always() && (...)`.

    Rozpoznawana jest KONIUNKCJA DOKŁADNIE DWÓCH członów, której pierwszym jest
    `always()`. Wszystko inne — `always() ||`, `always() && A && B`, koniunkcja bez
    `always()` — przechodzi dalej nietknięte i rozjeżdża się z wymaganym zestawem,
    czyli pada.
    """
    expression = _strip_parens(_unwrap_expression(condition))
    conjuncts = _split_top_level(expression, "&&")
    drugi = conjuncts[1].strip() if len(conjuncts) == 2 else ""
    # Nawias wokół alternatywy jest WYMAGANY, choć `&&` wiąże mocniej niż `||`,
    # więc `always() && A || B` znaczyłoby to samo. Zapis bez nawiasu czyta się
    # jak koniunkcja z A — czyli jak mutacja, którą ta bramka złapała 04.09.2026 —
    # i odróżnienie jednego od drugiego wymagałoby od czytającego pamiętania
    # o priorytecie operatorów. Bramka woli zapis, który mówi wprost.
    if (len(conjuncts) == 2 and conjuncts[0].strip() == FORK_GUARD_WRAPPER
            and drugi.startswith("(") and drugi.endswith(")")):
        expression = _strip_parens(drugi)
    return [_strip_parens(part) for part in _split_top_level(expression, "||")]


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
            members = _fork_guard_members(job["if"])
            if sorted(members) != sorted(required_terms):
                unguarded.append(
                    f"{name}:{job_id}: `if:` nie jest ALTERNATYWĄ (`||`) dwóch "
                    f"wymaganych członów, tylko {members}")
    assert not unguarded, f"joby bez strażnika fork-PR: {unguarded}"
    assert checked >= 7, checked


VISUAL = "visual-regression.yml"


def test_the_visual_workflow_tells_a_found_regression_apart_from_a_refused_upload():
    """Dwa zdarzenia, dwa sygnały w liście checków (6.D63).

    **Skąd.** Job `visual-regression` czerwieniał tak samo od kroku bramki
    (`tools/ci/visual_smoke.sh` — znaleziona różnica), jak od kroku wysyłki
    (`actions/upload-artifact`, `if: always()`), a z listy checków nie dało się tego
    rozróżnić. Zmierzony przypadek na #415: `403 Forbidden` przy `FinalizeArtifact`,
    artefakt **716 055 B**, a `blender-smoke` sześć minut później wgrał
    **1 905 203 B** — więc ani limit rozmiaru, ani wyczerpana kwota; jedno ponowienie
    dało zielono bez zmiany w kodzie.

    **Czego ta bramka pilnuje.** Że los wysyłki **wychodzi z joba** i że istnieje
    drugi job, który jest czerwony wyłącznie od niego. Sprawdzana jest struktura
    dokumentu, nie obecność napisów: komentarz opisujący rozróżnienie przeszedłby
    tak samo dobrze jak rozróżnienie.
    """
    document = yaml.safe_load(_text(VISUAL))
    bramka = document["jobs"]["visual-regression"]
    artefakty = document["jobs"].get("visual-artifacts")

    assert artefakty, (
        f"{VISUAL}: nie ma drugiego joba, więc lista checków ma jeden wiersz na dwa "
        "różne zdarzenia")

    wysylka = [s for s in bramka["steps"]
               if str(s.get("uses", "")).startswith("actions/upload-artifact@")]
    assert len(wysylka) == 1, f"{VISUAL}: kroków wysyłki jest {len(wysylka)}, oczekiwano 1"
    assert wysylka[0].get("id"), (
        f"{VISUAL}: krok wysyłki nie ma `id`, więc jego losu nie da się wynieść z joba")
    assert wysylka[0].get("if") == "always()", (
        f"{VISUAL}: krok wysyłki bez `if: always()` nie ruszy po przegranej bramce")
    assert "continue-on-error" not in wysylka[0], (
        f"{VISUAL}: `continue-on-error` na kroku wysyłki chowa prawdziwą awarię "
        "wysyłki — to jest naprawa ODRZUCONA we wpisie 6.D63")

    zapis = [s for s in bramka["steps"]
             if s.get("id") and "GITHUB_OUTPUT" in str(s.get("run", ""))
             and f"steps.{wysylka[0]['id']}.outcome" in str(s.get("run", ""))]
    assert len(zapis) == 1, (
        f"{VISUAL}: nie ma kroku zapisującego `outcome` wysyłki do `GITHUB_OUTPUT`")
    assert zapis[0].get("if") == "always()", (
        f"{VISUAL}: krok zapisujący los wysyłki bez `if: always()` nie ruszy właśnie "
        "wtedy, gdy wysyłka padnie — czyli w jedynym przypadku, o którym ma mówić")

    wyjscia = bramka.get("outputs") or {}
    assert any(f"steps.{zapis[0]['id']}.outputs." in str(v) for v in wyjscia.values()), (
        f"{VISUAL}: job bramki nie wystawia losu wysyłki jako wyjścia: {wyjscia}")

    assert artefakty.get("needs") == "visual-regression", artefakty.get("needs")
    cialo = "\n".join(str(s.get("run", "")) for s in artefakty["steps"])
    assert "needs.visual-regression.outputs." in cialo, (
        f"{VISUAL}: drugi job nie czyta losu wysyłki, więc jego kolor nie mówi o niej")
    # Job, który przy PUSTEJ wartości kończy zerem, byłby zielony dokładnie wtedy,
    # gdy job bramki padł przed zapisem losu — czyli milczałby o najgorszym przypadku.
    assert "exit 1" in cialo, f"{VISUAL}: drugi job nie umie zaczerwienieć"


def test_the_fork_guard_accepts_only_the_always_wrapper_and_nothing_looser():
    """Kontrola negatywna do otoczki `always() &&` dopuszczonej przy 6.D63.

    Otoczka jest jedynym rozluźnieniem zapisu, jakie ta bramka zna, więc każde inne
    użycie `always()` musi zostać odrzucone. Bez tej pary rozpoznawanie otoczki
    dałoby się rozciągnąć na koniunkcję, która strażnika **znosi** — a to jest
    dokładnie ta mutacja, którą bramka złapała 04.09.2026 (zamiana `||` na `&&`).
    """
    wymagane = sorted(("github.event_name != 'pull_request'",
                       "github.event.pull_request.head.repo.full_name == github.repository"))
    alternatywa = ("github.event_name != 'pull_request' || "
                   "github.event.pull_request.head.repo.full_name == github.repository")

    # PRZECHODZI: goła alternatywa i alternatywa w otoczce `always() &&`.
    assert sorted(_fork_guard_members(alternatywa)) == wymagane
    assert sorted(_fork_guard_members(f"always() && ({alternatywa})")) == wymagane
    assert sorted(_fork_guard_members(f"${{{{ always() && ({alternatywa}) }}}}")) == wymagane

    # PADA: otoczka bez nawiasu wokół alternatywy rozbija koniunkcję na trzy człony…
    assert sorted(_fork_guard_members(f"always() && {alternatywa}")) != wymagane
    # …`always()` na alternatywie zamiast na koniunkcji…
    assert sorted(_fork_guard_members(f"always() || ({alternatywa})")) != wymagane
    # …jeden człon zamiast dwóch…
    assert sorted(_fork_guard_members(
        "always() && (github.event_name != 'pull_request')")) != wymagane
    # …koniunkcja członów zamiast alternatywy, czyli mutacja z 04.09.2026…
    assert sorted(_fork_guard_members(alternatywa.replace("||", "&&"))) != wymagane
    assert sorted(_fork_guard_members(
        f"always() && ({alternatywa.replace('||', '&&')})")) != wymagane
    # …i cokolwiek dopisanego obok otoczki.
    assert sorted(_fork_guard_members(f"always() && true && ({alternatywa})")) != wymagane


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
    # `curl` dopisany 10.09.2026 (6.D77). Wpis jest TOŻSAMOŚCIOWY — pakiet i polecenie
    # nazywają się tak samo — i to go nie czyni zbędnym: bez niego
    # `test_ci_no_step_uses_a_packaged_command_before_installing_it` nie ma czego
    # pilnować dla `curl`, a to właśnie `curl` woła oba instalatory.
    "curl": "curl",
}


#: Moduł Pythona -> pakiet Debiana, który go dostarcza — 6.D240.
#:
#: **Ta tabela NIE jest tożsamościowa i to jest cały powód, dla którego istnieje.**
#: `POLECENIA_Z_PAKIETOW` wyżej ma wpisy, gdzie polecenie i pakiet nazywają się tak
#: samo (`curl`, `unzip`); tutaj nie zachodzi to ANI RAZ: moduł `yaml` przychodzi
#: z pakietu `python3-yaml`. Reguły mechanicznej („dopisz przedrostek") świadomie nie
#: ma — trafiałaby w PyYAML i myliła się na pierwszym module, którego pakiet nazywa
#: się inaczej, a takich w Debianie jest więcej niż zgodnych.
MODULY_Z_PAKIETOW = {
    "yaml": "python3-yaml",
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


#: Ile wywołań akcji sondującej NIE podaje ani jednej biblioteki — 6.D240.
#: Jedno: `python-tests.yml`, job `tools`, który nic nie renderuje i sonduje MODUŁY
#: Pythona. Bez tej stałej podłoga niżej porównywałaby liczbę kopii listy sonames
#: z liczbą wszystkich wywołań sondy i zapalałaby się na wywołaniu poprawnym (6.D27),
#: a rozluźnienie jej do nierówności zdjęłoby ochronę, po którą powstała: przy
#: `zebrane <= wolania` oślepienie parsera YAML-a przechodzi na zielono.
#: Stała jest liczona w drugą stronę osobną asercją, więc nie może zestarzeć się cicho.
WYWOLAN_SONDY_BEZ_BIBLIOTEK = 1


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
    assert zebrane + WYWOLAN_SONDY_BEZ_BIBLIOTEK == wolania, (
        "parser YAML-a zebrał %d kopii listy sonames, wywołań sondy bez bibliotek "
        "jest zadeklarowanych %d, a wywołań akcji sondującej jest w tekście %d — "
        "skan przestał czytać część workflowów, a wtedy porównanie kopii ze sobą "
        "jest zielone nad rozjazdem w tych nieczytanych"
        % (zebrane, WYWOLAN_SONDY_BEZ_BIBLIOTEK, wolania))
    bez = [n for n in _workflows()
           if PROBE_ACTION in _text(n) and not _sonda_pyta_o_sonames(n)]
    assert len(bez) == WYWOLAN_SONDY_BEZ_BIBLIOTEK, (
        "wywołań sondy BEZ bibliotek jest %d (%s), a stała mówi %d — podnieś ją "
        "razem z powodem albo sprawdź, czy sonda renderująca nie zgubiła listy"
        % (len(bez), ", ".join(bez), WYWOLAN_SONDY_BEZ_BIBLIOTEK))


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
          moduly = (wanted.get("python-modules") or "").split()
          # **Sonda ma pytać o COKOLWIEK, co ten workflow instaluje — 16.09.2026
          # (6.D240), i ten warunek jest przepisany, a nie dopisany obok.** Poprzednia
          # wersja żądała niepustego `libraries:` i była prawdziwa wobec drzewa,
          # w którym każdy job instalujący cokolwiek renderował. Job `tools`
          # z `python-tests.yml` instaluje MODUŁ Pythona i bibliotek nie sonduje;
          # żądanie od niego sonames kazałoby mu pytać o coś, czego nie instaluje,
          # czyli robić dokładnie tę usterkę, którą ta bramka tropi.
          #
          # Zostaje to, po co bramka powstała: sonda pusta zawsze zwróci `present`,
          # więc instalacja nie odpali się NIGDY — i wtedy brak wychodzi dopiero
          # w środku pracy joba. Dokładnie to zdarzyło się 15.09.2026, gdy `tools`
          # nie miał sondy w ogóle.
          assert sonames or moduly, (
              f"{name}: sonda nie podaje ani jednej biblioteki i ani jednego modułu, "
              "więc zawsze zwróci present, a instalacja nie odpali się nigdy")
          for soname in sonames:
              package = _debian_package_for(soname)
              assert package in packages, (
                  f"{name}: sonda pyta o {soname} (pakiet {package}), a zestaw apt "
                  f"tego workflow tego nie instaluje: {sorted(packages)}")
          for modul in moduly:
              package = MODULY_Z_PAKIETOW.get(modul)
              assert package, (
                  f"{name}: sonda pyta o moduł {modul!r}, którego nie ma "
                  "w MODULY_Z_PAKIETOW — dopisz go razem z nazwą pakietu, bo nazwa "
                  "modułu i nazwa pakietu NIE są tym samym napisem")
              assert package in packages, (
                  f"{name}: sonda pyta o moduł {modul} (pakiet {package}), a zestaw "
                  f"apt tego workflow tego nie instaluje: {sorted(packages)}")

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
    # OSIEM od 16.09.2026 (6.D240): doszedł job `tools` z `python-tests.yml`, pierwszy
    # bramkowany sondą, który nie renderuje. Podłoga jest tu po to, żeby job, który
    # PRZESTAŁ bramkować instalację, nie wypadł z pętli po cichu.
    assert checked == 8, checked


#: Moduły, bez których `tools/tests/test_all.py` nie wstaje — 6.D240. Liczone
#: Z DRZEWA przez `_moduly_spoza_biblioteki_standardowej()`, nie wpisane tutaj:
#: lista wpisana z ręki rozjechałaby się przy pierwszym nowym imporcie i byłaby
#: tą samą usterką, którą 6.D45 zmierzyło na `MIN_REPORTS`.
#: Podłoga jest na LICZBĘ skanowanych modułów, żeby oślepiony skan nie wyszedł
#: zielony na pustym zbiorze (rodzina 6.D159).
MINIMUM_MODULOW_ZESTAWU = 100


def _moduly_spoza_biblioteki_standardowej():
    """Nazwy modułów spoza stdlib importowane przez `tools/tests/*.py`.

    Czyta AST, nie grep: `import yaml` w komentarzu albo w napisie nie jest importem,
    a `from yaml import safe_load` jest. Odsiew po `sys.stdlib_module_names` bierze
    wiedzę z interpretera, a nie z drugiej listy nazw wpisanej do testu (6.D213).
    """
    import ast as _ast
    katalog = os.path.join(ROOT, "tools", "tests")
    # **`wlasne` to KAŻDY moduł pod `tools/`, nie tylko `tools/tests/`** — i ten wiersz
    # jest tu dlatego, że pierwsza wersja brała wyłącznie `tools/tests/*.py`
    # i zameldowała 63 „zależności spoza stdlib", wśród nich `braking`, `sweep`
    # i `validate`, czyli własny kod projektu wołany przez `sys.path.insert`.
    # Złapała to ta sama bramka, którą ten czytnik obsługuje — czyli ślepota czytnika
    # nie zdążyła stać się wynikiem (rodzina 6.D221).
    # Przejście idzie `tree_walk.walk`, nie `os.walk` — 6.D36. Bez wspólnego filtra
    # skan wchodzi do kopii drzewa leżących pod katalogami z `.gitignore` i bierze
    # STARE nazwy modułów za własne. Złapała to bramka
    # `test_no_tool_walks_the_tree_without_the_shared_filter`, u mnie, przed werdyktem.
    wlasne = set()
    for _gdzie, _pod, pliki in TW.walk(os.path.join(ROOT, "tools"), ROOT):
        wlasne |= {n[:-3] for n in pliki if n.endswith(".py")}
    obce = set()
    zeskanowanych = 0
    for nazwa in sorted(os.listdir(katalog)):
        if not nazwa.endswith(".py"):
            continue
        zeskanowanych += 1
        with open(os.path.join(katalog, nazwa), encoding="utf-8") as uchwyt:
            drzewo = _ast.parse(uchwyt.read(), filename=nazwa)
        for wezel in _ast.walk(drzewo):
            if isinstance(wezel, _ast.Import):
                korzenie = [a.name.split(".")[0] for a in wezel.names]
            elif isinstance(wezel, _ast.ImportFrom):
                korzenie = [(wezel.module or "").split(".")[0]] if wezel.level == 0 else []
            else:
                continue
            for korzen in korzenie:
                if korzen and korzen not in wlasne and korzen not in sys.stdlib_module_names:
                    obce.add(korzen)
    return obce, zeskanowanych


def _uruchom_sonde(libraries="", commands="", python_modules=""):
    """Uruchamia CIAŁO kroku sondy z akcji i zwraca wartość `libs`.

    **Wykonanie, a nie napis w pliku** — rodzina bramek `apt_install.sh` z 04.09.2026.
    Powód jest tu zmierzony, nie zapożyczony: KN-3 przy 6.D240 zastąpiła pętlę
    sondującą moduły napisem `true`, zostawiając w pliku i opis wejścia, i komentarz,
    i **cały zestaw wyszedł 87/87 na zielono**. Bramka pytająca „czy w akcji stoi
    `python3 -c`" przeszłaby tę mutację tak samo, bo napis by został.
    """
    body = _action_body(PROBE_ACTION)
    with tempfile.TemporaryDirectory(prefix="metro-sonda-") as katalog:
        wyjscie = os.path.join(katalog, "github_output")
        open(wyjscie, "w", encoding="utf-8").close()
        skrypt = os.path.join(katalog, "sonda.sh")
        with open(skrypt, "w", encoding="utf-8") as uchwyt:
            uchwyt.write(body)
        srodowisko = dict(os.environ,
                          WANT_LIBRARIES=libraries,
                          WANT_COMMANDS=commands,
                          WANT_PYTHON_MODULES=python_modules,
                          GITHUB_OUTPUT=wyjscie)
        proces = subprocess.run(["bash", skrypt], env=srodowisko,
                                capture_output=True, text=True)
        assert proces.returncode == 0, (proces.returncode, proces.stderr)
        tresc = open(wyjscie, encoding="utf-8").read()
    for wiersz in tresc.splitlines():
        if wiersz.startswith("libs="):
            return wiersz.split("=", 1)[1].strip()
    raise AssertionError("sonda nie zapisała `libs=` do GITHUB_OUTPUT: " + tresc)


def test_sonda_modulow_NAPRAWDE_sonduje_a_nie_tylko_o_tym_pisze():
    """Kontrola przyrządu sondy, wykonana na jej WŁASNYM ciele — 6.D240.

    Trzy przebiegi, bo dwa pierwsze osobno nic nie znaczą: sonda zwracająca zawsze
    `missing` przeszłaby przebieg drugi, a sonda zwracająca zawsze `present` —
    pierwszy. Trzeci pilnuje, żeby pusta lista nie zaczęła nagle meldować braku,
    bo wtedy siedem jobów renderujących instalowałoby pakiety przy każdym przebiegu.

    **Zmierzone, dlaczego ta bramka istnieje:** bez niej zastąpienie pętli
    sondującej moduły napisem `true` przechodzi CAŁY zestaw na zielono (KN-3), a job
    melduje wtedy `present` nad brakującym modułem — czyli instalacja nie odpala się
    nigdy i brak wychodzi w środku przebiegu. To jest dokładnie ta awaria, po której
    ta pozycja powstała, tylko wpuszczona z powrotem inną drogą.
    """
    assert _uruchom_sonde(python_modules="yaml") == "present", (
        "sonda melduje brak modułu `yaml`, który ten interpreter ma — sonda "
        "zawsze-missing kazałaby siedmiu jobom instalować pakiety przy każdym przebiegu")
    nieistniejacy = "metro_bxl_modul_ktorego_nie_ma_" + secrets.token_hex(8)
    assert _uruchom_sonde(python_modules=nieistniejacy) == "missing", (
        "sonda melduje `present` dla modułu %r, którego NIE MA — pętla sondująca "
        "moduły nie wykonuje się, więc instalacja nie odpali się nigdy" % nieistniejacy)
    assert _uruchom_sonde() == "present", (
        "sonda z pustymi listami melduje brak — wtedy każdy job instalowałby pakiety "
        "przy każdym przebiegu, czyli odwrotność tego, po co ta sonda powstała")


def test_kazdy_workflow_uruchamiajacy_zestaw_SONDUJE_jego_zaleznosci():
    """6.D240: zależność realna, zadeklarowana nigdzie, kosztowała cztery joby naraz.

    15.09.2026 `tools`, `visual-regression`, `station-details` i `tunnel-alignment`
    padły JEDNOCZEŚNIE na `ModuleNotFoundError: No module named 'yaml'`, na trzech
    różnych maszynach puli, przy **2386 testach przechodzących z 2389**. PyYAML nie był
    ani sondowany, ani w żadnym zestawie apt — działał wyłącznie dlatego, że maszyny
    puli miały go z innych powodów. Trzeci raz ta sama klasa: `unzip` doszedł do kodu
    127 (07.09.2026), `curl` do 6.D77 (10.09.2026).

    **Dlaczego to bramka, a nie sama poprawka konfiguracji.** Poprawka gasi dzisiejszy
    pożar; bez tej bramki nowy workflow wołający zestaw wchodzi bez sondy i awaria
    wraca tą samą drogą. Bramka pyta o to, co jest naprawdę sprawdzalne z drzewa:
    **każdy workflow, który uruchamia `test_all.py` — wprost albo przez skrypt
    z `tools/ci/` — musi sondować każdą pozabibliotekową zależność tego zestawu.**

    **Czego ta bramka NIE robi, i to jest wypisane, a nie przemilczane:** nie sprawdza,
    czy pakiet jest zainstalowany na maszynie — tego z repozytorium sprawdzić się nie
    da. Sprawdza, że job **spyta**, zanim zacznie pracę. Cała wartość jest w momencie:
    `station-details` i `tunnel-alignment` zdążyły 15.09.2026 **poprawnie wyrenderować**
    geometrię, zanim brak wyszedł — czyli osiem minut pracy poszło na komunikat, który
    sonda oddaje w sekundę.
    """
    obce, zeskanowanych = _moduly_spoza_biblioteki_standardowej()
    assert zeskanowanych >= MINIMUM_MODULOW_ZESTAWU, (
        "skan przeszedł po %d plikach `tools/tests/*.py` przy podłodze %d — czytnik "
        "przestał widzieć katalog, a wtedy pusty zbiór zależności czyta się jako "
        "jako brak zaleznosci" % (zeskanowanych, MINIMUM_MODULOW_ZESTAWU))
    assert obce, (
        "skan nie znalazł ANI JEDNEJ zależności spoza stdlib — to jest dokładnie ten "
        "wynik, który dostałby czytnik oślepiony, a `yaml` w drzewie stoi")

    skrypty_z_zestawem = {
        nazwa for nazwa in os.listdir(os.path.join(ROOT, "tools", "ci"))
        if nazwa.endswith(".sh")
        and "test_all.py" in open(os.path.join(ROOT, "tools", "ci", nazwa),
                                  encoding="utf-8").read()}
    sprawdzonych = 0
    for name in _workflows():
        text = _text(name)
        wola_zestaw = "test_all.py" in text or any(
            skrypt in text for skrypt in skrypty_z_zestawem)
        if not wola_zestaw:
            continue
        document = yaml.safe_load(text)
        for jobname, job in (document.get("jobs") or {}).items():
            kroki = job.get("steps") or []
            if not any("test_all.py" in str(k.get("run", "")) or any(
                    s in str(k.get("run", "")) for s in skrypty_z_zestawem)
                    for k in kroki):
                continue
            sprawdzonych += 1
            sondowane = set()
            for krok in kroki:
                if str(krok.get("uses", "")) == PROBE_ACTION:
                    sondowane |= set(
                        ((krok.get("with") or {}).get("python-modules") or "").split())
            brakujace = sorted(obce - sondowane)
            assert not brakujace, (
                "%s:%s uruchamia zestaw testów, a nie sonduje jego zależności %s — "
                "brak wyjdzie dopiero w środku przebiegu, po minutach pracy, zamiast "
                "w sondzie (6.D240; 15.09.2026 kosztowało to cztery joby naraz)"
                % (name, jobname, ", ".join(brakujace)))
    assert sprawdzonych >= 4, (
        "bramka obejrzała tylko %d jobów uruchamiających zestaw — 15.09.2026 padły "
        "CZTERY naraz, więc skan widzący mniej nie widzi tego, co się zepsuło"
        % sprawdzonych)


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
    # **PRZEKIEROWANE 09.09.2026 (6.D67), i szuka WIĘCEJ, nie mniej.** Wzorzec
    # `push origin --delete` przestał istnieć w tym pliku, bo kasowanie idzie teraz
    # przez `--force-with-lease` z sha z planu — a bramka, która przestała cokolwiek
    # znajdować, zapaliłaby się dopiero na liczniku „dokładnie jeden". Dziś krok
    # rozpoznaje się po tym, że KASUJE (`--delete "$branch"`), niezależnie od tego,
    # jakie warunki niesie po drodze, i osobno sprawdza się, że warunek na czubek
    # w nim stoi — więc żadna z dwóch bramek nie da się przesunąć bez drugiej.
    deleting = [s for s in steps if '--delete "$branch"' in str(s.get("run", ""))]
    assert len(deleting) == 1, "krok kasujący ma być dokładnie jeden"
    assert "inputs.dry_run == false" in str(deleting[0]["if"]), deleting[0].get("if")
    assert "--force-with-lease=" in str(deleting[0]["run"]), (
        "krok znaleziony jako kasujący nie stawia warunku na czubek — patrz "
        "`test_prune_workflow_deletes_only_the_tip_its_plan_wrote_down`")
    # Kontrola przyrządu: gdyby wzorzec przestał cokolwiek łapać, lista byłaby pusta
    # i asercja wyżej powiedziałaby to samo, co przy dwóch krokach. Ta mówi, którą
    # z dwóch rzeczy zobaczono.
    assert any('--delete "$branch"' in str(s.get("run", "")) for s in steps), (
        "żaden krok nie kasuje gałęzi — wzorzec rozjechał się z treścią workflowa")


def test_prune_workflow_never_deletes_the_base_branch():
    """Baza musi być wykluczona jawnie, a nie przez to, że „i tak jest przodkiem siebie".

    `merge-base --is-ancestor main main` jest prawdą, więc bez tego wykluczenia
    workflow skasowałby gałąź, względem której liczy scalenie — czyli dokładnie tę,
    której nie wolno tknąć.
    """
    assert '[ "$branch" = "$BASE" ]' in _prune_without_comments(), \
        "brak jawnego wykluczenia bazy"


#: Pobranie czegokolwiek z sieci WŁASNĄ ręką: `curl` albo `wget`. Akcje przypięte po
#: SHA (np. `actions/setup-dotnet`) pobierają po swojemu i mają własną weryfikację —
#: tu chodzi o miejsca, w których to REPOZYTORIUM ściąga plik i zaraz go uruchamia.
POBRANIE = re.compile(r"(?<![\w-])(curl|wget)(?![\w-])")

#: Sprawdzenie sumy, w formie, która UMIE ODMÓWIĆ: `-c` porównuje i kończy błędem.
#: Samo `sha256sum plik` wypisuje sumę i zawsze kończy zerem — czyli wygląda jak
#: kontrola i nią nie jest.
SPRAWDZENIE_SUMY = re.compile(r"(?<![\w-])(sha256sum|sha512sum)\s+-c(?![\w-])")


def _bez_komentarzy_powloki(text):
    return "\n".join(l for l in text.splitlines() if not l.lstrip().startswith("#"))


def _cialo_run(wezel, zebrane):
    """Wszystkie wartości `run:` w dokumencie YAML, na dowolnej głębokości."""
    if isinstance(wezel, dict):
        for klucz, wartosc in wezel.items():
            if klucz == "run" and isinstance(wartosc, str):
                zebrane.append(wartosc)
            else:
                _cialo_run(wartosc, zebrane)
    elif isinstance(wezel, list):
        for element in wezel:
            _cialo_run(element, zebrane)
    return zebrane


def _kod_powloki(sciezka):
    """Kod POWŁOKI z pliku CI — a nie cały jego tekst.

    **Przepisane 10.09.2026 (6.D77), a nie dopisane obok.** Poprzednia wersja brała
    surowy tekst pliku, więc każde wystąpienie napisu `curl` liczyła jako pobranie —
    także w `with: commands: curl`, czyli w NAZWIE polecenia, o które pyta sonda.
    Dopisanie `curl` do sondy zapaliło przez to bramkę sumy kontrolnej w siedmiu
    workflowach naraz, z których żaden niczego nie pobiera. Zawężenie do ciał `run:`
    sprawdza WIĘCEJ, nie mniej: dane wejściowe akcji przestają udawać kod, a każde
    prawdziwe `curl` w `run:` — na dowolnej głębokości dokumentu, w jobie i w akcji
    złożonej — nadal wchodzi.
    """
    tekst = open(sciezka, encoding="utf-8").read()
    if not sciezka.endswith((".yml", ".yaml")):
        return _bez_komentarzy_powloki(tekst)
    document = yaml.safe_load(tekst)
    return _bez_komentarzy_powloki("\n".join(_cialo_run(document, [])))


def _miejsca_pobrania():
    """Pliki CI, które same ściągają coś z sieci — z drzewa, nie z listy."""
    kandydaci = [os.path.join(WORKFLOWS, n) for n in _workflows()]
    kandydaci += _action_files()
    ci = os.path.join(ROOT, "tools", "ci")
    kandydaci += [os.path.join(ci, n) for n in sorted(os.listdir(ci))
                  if n.endswith(".sh")]
    znalezione = {}
    for sciezka in kandydaci:
        kod = _kod_powloki(sciezka)
        if POBRANIE.search(kod):
            znalezione[os.path.relpath(sciezka, ROOT)] = kod
    return znalezione


def test_every_place_that_downloads_a_tool_checks_its_checksum():
    """Każde własne pobranie narzędzia ma sprawdzaną sumę — 6.D68.

    **Skąd.** `.github/workflows/godot-first-run.yml` pobierał archiwum Godota,
    rozpakowywał je i URUCHAMIAŁ binarium bez ani jednego `sha256`, a obok, w tym
    samym repozytorium i na tym samym runnerze, `tools/ci/blender_install.sh` wołał
    `sha256sum -c`. Joby chodzą na maszynie właściciela, z dostępem do workspace'u,
    `runner.tool_cache` i `GITHUB_TOKEN` — nierówność standardu była całą treścią
    pozycji.

    **Bramka WYLICZA miejsca pobrania z drzewa**, a nie sprawdza dwóch znanych dziś:
    tego wprost żąda pole „Skończone, gdy". Nowe `curl` w dowolnym workflowie,
    akcji lokalnej albo skrypcie `tools/ci/` zapala ją, dopóki nie dostanie sumy.
    """
    bez_sumy = []
    znalezione = _miejsca_pobrania()
    for sciezka, kod in znalezione.items():
        if not SPRAWDZENIE_SUMY.search(kod):
            bez_sumy.append(sciezka)
    assert not bez_sumy, (
        "pobranie z sieci bez sprawdzenia sumy — plik ląduje na maszynie właściciela "
        f"i jest uruchamiany: {bez_sumy}")
    # Pętla po samych ZNALEZIONYCH miejscach przeszłaby pusta i zielona także wtedy,
    # gdyby wzorzec przestał cokolwiek łapać. Liczba MIERZY drzewo i rośnie razem
    # z nim — dziś dwa instalatory, Blendera i Godota.
    assert len(znalezione) >= 2, (
        f"bramka znalazła {len(znalezione)} miejsc pobrania — wzorzec rozjechał się "
        "z treścią repozytorium")


def test_the_download_gate_tells_a_real_check_apart_from_a_printed_sum():
    """Kontrola negatywna: co bramka ma łapać, a czego nie ma brać za kontrolę."""
    assert POBRANIE.search('curl -fL -o "$T" "$URL"')
    assert POBRANIE.search("wget -q $URL")
    # Nie każde słowo z `curl` w środku jest pobraniem.
    assert not POBRANIE.search("libcurl4-openssl-dev")
    assert not POBRANIE.search("echo curling")

    assert SPRAWDZENIE_SUMY.search('echo "$SHA256  $T" | sha256sum -c -')
    assert SPRAWDZENIE_SUMY.search('echo "$SHA512  $Z" | sha512sum -c - >&2')
    # `sha256sum plik` bez `-c` WYPISUJE sumę i kończy zerem — wygląda jak kontrola
    # i nią nie jest. To jest ta sama rodzina co „skrypt wykonał się bez błędu".
    assert not SPRAWDZENIE_SUMY.search("sha256sum $TARBALL")
    assert not SPRAWDZENIE_SUMY.search("sha256sum-check $TARBALL")

    # Kontrola przyrządu odsiewającego komentarze: pobranie schowane w komentarzu
    # nie jest pobraniem, a suma sprawdzana w komentarzu nie jest sprawdzeniem.
    assert not POBRANIE.search(_bez_komentarzy_powloki("  # curl -o x $URL\n"))
    assert not SPRAWDZENIE_SUMY.search(_bez_komentarzy_powloki("# sha256sum -c -\n"))
    assert POBRANIE.search(_bez_komentarzy_powloki('  curl -o x "$URL"\n'))

    # ZMIERZONY PRZYPADEK 6.D77: `curl` jako NAZWA sondowanego polecenia w `with:`
    # nie jest pobraniem, a `curl` w `run:` jest — i to na dowolnej głębokości.
    import tempfile
    with tempfile.TemporaryDirectory() as katalog:
        sonda = os.path.join(katalog, "sonda.yml")
        with open(sonda, "w", encoding="utf-8") as uchwyt:
            uchwyt.write("jobs:\n  j:\n    steps:\n"
                         "      - uses: ./.github/actions/probe-tools\n"
                         "        with:\n          commands: curl unzip\n")
        assert not POBRANIE.search(_kod_powloki(sonda))
        pobranie = os.path.join(katalog, "pobranie.yml")
        with open(pobranie, "w", encoding="utf-8") as uchwyt:
            uchwyt.write("jobs:\n  j:\n    steps:\n"
                         "      - run: curl -fL -o x \"$URL\"\n")
        assert POBRANIE.search(_kod_powloki(pobranie))


def test_the_godot_pin_carries_a_version_and_a_publisher_checksum():
    """Pin Godota ma kształt pinu Blendera: numer i suma, oba czytane ze skryptu."""
    pin = open(os.path.join(ROOT, "tools", "ci", "godot-version.txt"),
               encoding="utf-8").read()
    wersja = re.search(r"(?m)^version=(\S+)$", pin)
    suma = re.search(r"(?m)^sha512=([0-9a-f]{128})$", pin)
    assert wersja, "pin Godota nie podaje `version=`"
    assert suma, "pin Godota nie podaje `sha512=` o długości sumy SHA-512"
    instalator = open(os.path.join(ROOT, "tools", "ci", "godot_install.sh"),
                      encoding="utf-8").read()
    kod = _bez_komentarzy_powloki(instalator)
    assert "godot-version.txt" in kod, "instalator nie czyta pinu"
    # Kolejność jest treścią: suma sprawdzana PO rozpakowaniu opisuje archiwum,
    # które zdążyło już wysypać pliki na dysk.
    assert kod.index("sha512sum -c") < kod.index("unzip"), (
        "suma sprawdzana PO rozpakowaniu — archiwum jest wypakowane, zanim ktokolwiek "
        "zapyta, co w nim było")


def test_prune_workflow_deletes_only_the_tip_its_plan_wrote_down():
    """Kasowanie stawia warunek na czubek, i to na czubek Z PLANU (6.D67).

    **Skąd.** Warunek kwalifikowania sprawdza czubek sprzed zapisania planu, a samo
    polecenie kasujące nie sprawdzało niczego, więc push, który wylądował między
    planem a kasowaniem, ginął. Zmierzone 09.09.2026 w lokalnym repozytorium bare:
    plan zapisał `f18f2ba`, zdalne stało na `b17dfb1`, a `git push origin --delete`
    skasowało ref **kodem 0**, razem z cudzym commitem. Ta sama próba
    z `--force-with-lease=refs/heads/<gałąź>:<sha>`:
    `! [rejected] (delete) -> audit-branch (stale info)`, kod 1, ref na miejscu;
    z sha aktualnym — skasowany, kod 0.

    Czytany jest KOD bez komentarzy, bo komentarz nad krokiem cytuje dawną postać.
    """
    kod = _prune_without_comments()

    assert "--force-with-lease=" in kod, (
        "krok kasujący nie stawia żadnego warunku na czubek — push, który wylądował "
        "po zapisaniu planu, zginie razem z gałęzią")
    assert 'refs/heads/$branch:$sha' in kod, (
        "`--force-with-lease` bez JAWNEGO sha z planu bierze lokalny ref śledzący, "
        "czyli mówi o tym samym czubku, co plan — i nie sprawdza niczego nowego")
    # Gołe `--delete` bez warunku nie ma prawa zostać obok, bo pierwsza asercja
    # przeszłaby także dla kroku, który próbuje obu form po kolei.
    assert "git push origin --delete" not in kod, (
        "obok formy z warunkiem stoi nadal forma bez warunku")
    assert "::error::" in kod and "::warning::nie udało się skasować" not in kod, (
        "nieudane kasowanie jest tu ostrzeżeniem, a nie błędem")
    assert 'test "$failed" -eq 0' in kod, (
        "krok kończy się zerem także wtedy, gdy któreś kasowanie odmówiło")


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


# --- 6.D91: krok walidacji osi nie wnioskuje linii z nazwy pliku ------------------


def _kroki_walidacji_osi():
    """Ciała `run:` z kroków, które wołają `tools/track/validate.py`."""
    zebrane = []
    for nazwa in _workflows():
        dokument = yaml.safe_load(_text(nazwa))
        for cialo in _cialo_run(dokument, []):
            if "tools/track/validate.py" in cialo:
                zebrane.append((nazwa, cialo))
    return zebrane


def test_ci_walidacja_osi_sprawdza_kazda_linie_a_nie_prefiks_nazwy_pliku():
    """Prefiks nazwy pliku unosi JEDNĄ linię, a pakiety A i E obsługują po dwie.

    Do 10.09.2026 krok wołał `--line "${id%%_*}"`, więc dla `L1_A` nie sprawdzał
    nigdy L5, a dla `L2_E` nigdy L6 — usunięcie stacji z tej drugiej przechodziło
    bez śladu (6.D91). Bramka pilnuje kształtu WYWOŁANIA, bo sam walidator umie
    obie drogi i wybór należy do kroku.
    """
    kroki = _kroki_walidacji_osi()
    assert kroki, "żaden workflow nie woła walidatora osi — kontrola przestała istnieć"
    for nazwa, cialo in kroki:
        assert "--all-lines" in cialo, (
            f"{nazwa}: krok walidacji osi nie woła `--all-lines`, więc sprawdza tylko "
            "tę linię, którą sam poda")
        assert "${id%%_*}" not in cialo, (
            f"{nazwa}: linia nadal wyprowadzana z prefiksu nazwy pliku")

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


# --- 6.D148: gdzie stoi krok kompilujacy `tools/` -------------------------------

#: Workflow, ktore niosa krok `compileall`. **Zmierzone 12.09.2026: jeden z dziesieciu.**
WORKFLOWY_Z_COMPILEALL = ("python-tests.yml",)

#: Workflow, ktore NIE wykonuja ani jednego pliku z `tools/`. Zmierzone 12.09.2026:
#: jeden z dziesieciu — i jest nim jedyny workflow uruchamiany recznie
#: (`workflow_dispatch`), ktory kasuje scalone galezie przez API GitHuba.
#:
#: **Wpis pozycji 6.D148 mowil, ze „dziewiec pozostalych workflowow w ogole nie musi
#: importowac `tools/`" — i to jest NIEPRAWDA.** Osiem z tych dziewieciu wykonuje
#: skrypty z `tools/ci/`, ktore z kolei wolaja Pythona z `tools/blender/`,
#: `tools/track/`, `tools/visual/` i `tools/tests/`.
WORKFLOWY_BEZ_TOOLS = ("prune-merged-branches.yml",)

#: Workflow uruchamiane na KAZDYM pull requescie, bez filtra `paths`. Zmierzone
#: 12.09.2026: dwa z dziesieciu. Na tej liczbie stoi cale rozstrzygniecie tej
#: pozycji — patrz `test_krok_compileall_stoi_w_workflow_BEZWARUNKOWYM`.
WORKFLOWY_BEZWARUNKOWE = ("python-tests.yml", "sim-tests.yml")


def _wyzwalacze(nazwa):
    """Sekcja `on:` workflow, jako slownik.

    **`on` w YAML-u to wartosc logiczna, nie napis.** `yaml.safe_load` zamienia
    klucz `on:` na `True` i `dokument["on"]` rzuca `KeyError` — a bramka, ktora
    zlapie ten wyjatek i pojdzie dalej, zamelduje „brak wyzwalaczy" dla KAZDEGO
    workflow i bedzie zielona. Kontrola przyrzadu nizej wykonuje ten przypadek.
    """
    dokument = yaml.safe_load(_text(nazwa))
    return dokument.get("on", dokument.get(True)) or {}


def bezwarunkowy_na_pull_request(nazwa):
    """Czy workflow rusza na KAZDYM pull requescie, bez filtra sciezek."""
    pr = _wyzwalacze(nazwa).get("pull_request", "BRAK")
    if pr == "BRAK":
        return False
    if not pr:                                  # `pull_request:` bez ciala
        return True
    return not (pr.get("paths") or pr.get("paths-ignore"))


def _cialo_z_tekstu(tekst):
    """Wszystko, co ten workflow WYKONA: `run:` krokow plus `run:` akcji lokalnych.

    Filtry `paths:` i klucze `cache` tez wymieniaja `tools/`, a kodu nie wykonuja.

    **Zawezenie do `run:` jest dzis UBEZPIECZENIEM, nie zmierzona koniecznoscia —
    i mowie to wprost.** Kontrola KN-4 tej pozycji (czytanie calego pliku zamiast
    samych `run:`) wyszla **ZIELONA na 80 testach**: jedyny workflow, ktory kodu
    z `tools/` nie wykonuje, nie wymienia `tools/` takze nigdzie indziej, wiec
    dzisiejsze dziesiec plikow obu czytnikow nie odroznia. Zawezenie zostaje, bo
    kosztuje zero, a workflow filtrowany na `tools/**` i NIEURUCHAMIAJACY stamtad
    niczego jest ksztaltem najzupelniej mozliwym — ale zdanie o nim ma mowic, ile
    jest warte. Sam mechanizm jest przybity wejsciem syntetycznym w kontroli
    przyrzadu nizej.
    """
    dokument = yaml.safe_load(tekst)
    czesci = []
    for job in (dokument.get("jobs") or {}).values():
        for krok in (job.get("steps") or []):
            if krok.get("run"):
                czesci.append(str(krok["run"]))
            uses = str(krok.get("uses", ""))
            if uses.startswith("./.github/actions/"):
                czesci.append(_action_body(uses))
    return "\n".join(czesci)


def _cialo_wykonywane(nazwa):
    return _cialo_z_tekstu(_text(nazwa))


def wykonuje_kod_z_tools(nazwa):
    """Czy ten workflow uruchamia cokolwiek spod `tools/`."""
    return "tools/" in _cialo_wykonywane(nazwa)


def workflowy_z_compileall():
    return tuple(n for n in _workflows() if "compileall" in _cialo_wykonywane(n))


def test_krok_compileall_stoi_dokladnie_w_jednym_workflow():
    """Liczba przybita rownoscia — 6.D148.

    Nie progiem: krok dopisany do kolejnego workflow ma byc widoczny w diffie razem
    z powodem, a zdjety z jedynego, ktory go ma, tym bardziej.
    """
    assert workflowy_z_compileall() == WORKFLOWY_Z_COMPILEALL, (
        "krok `compileall` stoi w %s, a pomiar z 12.09.2026 dal %s"
        % (list(workflowy_z_compileall()), list(WORKFLOWY_Z_COMPILEALL)))


def test_krok_compileall_stoi_w_workflow_BEZWARUNKOWYM():
    """ROZSTRZYGNIECIE pozycji, wykonane zamiast opisane — 6.D148.

    Jeden workflow z dziesieciu wyglada na asymetrie dopoty, dopoki nie zapyta sie,
    KTORY. `python-tests.yml` jest jednym z DWOCH, ktore rusza na kazdym pull
    requescie bez filtra `paths` — wiec kompilacja calego `tools/` dzieje sie na
    kazdym PR, niezaleznie od tego, ktore z pozostalych osmiu filtr wybierze.
    Skopiowanie kroku do tamtych nie dodaloby ani jednego pokrycia, a kosztowaloby
    0,33 s razy osiem.

    **Ten test pilnuje rzeczy, ktora moze sie zmienic po cichu:** dopisanie filtra
    `paths` do `python-tests.yml` zamienia kompilacje `tools/` z bezwarunkowej
    w warunkowa, nie ruszajac ani jednego wiersza kroku `compileall`.
    """
    for nazwa in WORKFLOWY_Z_COMPILEALL:
        assert bezwarunkowy_na_pull_request(nazwa), (
            "`%s` niesie krok `compileall`, ale przestal ruszac na KAZDYM pull "
            "requescie — kompilacja calego `tools/` jest odtad warunkowa i "
            "rozstrzygniecie 6.D148 trzeba przeczytac jeszcze raz" % nazwa)

    zmierzone = tuple(n for n in _workflows() if bezwarunkowy_na_pull_request(n))
    assert zmierzone == WORKFLOWY_BEZWARUNKOWE, (
        "workflowow bez filtra `paths` jest %s, a pomiar z 12.09.2026 dal %s — "
        "liczba jest tu trescia, bo na niej stoi zdanie „jeden wystarczy"
        % (list(zmierzone), list(WORKFLOWY_BEZWARUNKOWE)))


def test_dla_kazdego_workflow_wiadomo_czy_uruchamia_kod_z_tools():
    """Pole „Skonczone, gdy" 6.D148 zada tego dla wszystkich dziesieciu.

    **Wpis pozycji byl tu nieprawdziwy i pomiar to pokazuje:** nie „dziewiec
    workflowow nie musi importowac `tools/`", tylko DZIEWIEC Z DZIESIECIU ten kod
    wykonuje. Jedyny, ktory nie — `prune-merged-branches.yml` — chodzi recznie
    i rozmawia wylacznie z API GitHuba.
    """
    bez = tuple(n for n in _workflows() if not wykonuje_kod_z_tools(n))
    assert bez == WORKFLOWY_BEZ_TOOLS, (
        "workflowy nieuruchamiajace kodu z `tools/`: %s, a pomiar z 12.09.2026 dal "
        "%s" % (list(bez), list(WORKFLOWY_BEZ_TOOLS)))

    wszystkich = len(_workflows())
    assert wszystkich - len(bez) == 9 and wszystkich == 10, (
        "workflowow jest %d, z czego %d uruchamia kod z `tools/` — pomiar "
        "z 12.09.2026 mowil 10 i 9" % (wszystkich, wszystkich - len(bez)))


def test_czytnik_wyzwalaczy_radzi_sobie_z_kluczem_on_ktory_jest_wartoscia_logiczna():
    """Kontrola przyrzadu — 6.D148.

    Na drzewie repozytorium czytnik poprawny i czytnik pytajacy o `dokument["on"]`
    roznia sie tym, ze drugi rzuca `KeyError` na KAZDYM pliku. Gdyby ktos ten wyjatek
    zlapal i poszedl dalej, obie bramki wyzej bylyby zielone na pustce.
    """
    dokument = yaml.safe_load(_text(WORKFLOWY_Z_COMPILEALL[0]))
    assert True in dokument, (
        "`on:` przestal parsowac sie jako wartosc logiczna — jesli PyYAML zmienil "
        "zachowanie, komentarz przy `_wyzwalacze` jest nieaktualny")
    assert "on" not in dokument, (
        "`on` stoi w kluczach jako napis — patrz wyzej, to ta sama zmiana")
    assert set(_wyzwalacze(WORKFLOWY_Z_COMPILEALL[0])) == {"push", "pull_request"}, (
        _wyzwalacze(WORKFLOWY_Z_COMPILEALL[0]))

    # I ze filtr `paths` naprawde przelacza odpowiedz, a nie jest ozdoba wzorca:
    # `blender-smoke.yml` go ma, `python-tests.yml` nie.
    assert not bezwarunkowy_na_pull_request("blender-smoke.yml"), (
        "workflow z filtrem `paths` policzony jako bezwarunkowy")
    assert bezwarunkowy_na_pull_request("python-tests.yml"), (
        "workflow bez filtra `paths` policzony jako warunkowy")

    # I ze `tools/` w filtrze `paths` NIE jest wykonaniem. Na dzisiejszych dziesieciu
    # plikach nie odroznia tego nic (KN-4 zielona), wiec rozstrzyga wejscie
    # syntetyczne — inaczej zawezenie do `run:` byloby zdaniem bez pokrycia.
    tylko_filtr = (
        "name: x\n"
        "on:\n"
        "  pull_request:\n"
        "    paths:\n"
        "      - 'tools/**'\n"
        "jobs:\n"
        "  j:\n"
        "    runs-on: self-hosted\n"
        "    steps:\n"
        "      - run: echo nic\n")
    assert "tools/" not in _cialo_z_tekstu(tylko_filtr), (
        "`tools/` wymienione WYLACZNIE w filtrze `paths` policzone jako wykonanie: %r"
        % _cialo_z_tekstu(tylko_filtr))
    z_krokiem = tylko_filtr.replace("      - run: echo nic\n",
                                    "      - run: python3 tools/x.py\n")
    assert "tools/" in _cialo_z_tekstu(z_krokiem), (
        "`tools/` w kroku `run:` NIE policzone jako wykonanie: %r"
        % _cialo_z_tekstu(z_krokiem))


# --- 6.D194: dziewięć retencji, jedna z zapisanym sensem ----------------------------
#
# **Pole „Skąd" tej pozycji podawało rozkład, który się nie sumuje: „30 dni dla czasu
# zestawu, po 14 dla PIĘCIU workflowów i po 7 dla dwóch" — czyli osiem miejsc przy
# dziewięciu deklarowanych.** Zmierzone: **14 występuje SZEŚĆ razy**. Szósty krok stoi
# w `godot-first-run.yml` (plik ma 96 KB, krok w okolicy wiersza 1536) i został przy
# liczeniu pominięty. Błąd wszedł do drzewa z `reports/6d164-artefakt-okno-ruchome.md`
# i stamtąd do dwóch miejsc w `docs/TASKS.md`.
#
# **Bramka liczy rozkład z YAML-a, a nie z prozy**, więc następny krok wynoszący artefakt
# musi zostać rozstrzygnięty, zamiast wejść po cichu.

#: Rozkład retencji, ZMIERZONY 13.09.2026: `{dni: ile kroków}`. Równość, bo każdy nowy
#: krok wynoszący artefakt ma być decyzją, a nie liczbą, która się dopisała.
RETENCJE_W_WORKFLOWACH = {30: 1, 14: 6, 7: 2}

#: Po ile razy sięgnięto w historii tego repozytorium po artefakt starszy niż doba —
#: policzone z `reports/` i `docs/TASKS.md` przy 6.D194.
#:
#: **Raz po METADANE, ZERO po TREŚĆ**, i to rozróżnienie jest tu całą odpowiedzią.
#: Jedyny przypadek to 6.D164 (13.09.2026): artefakt `czas-zestawu` z przebiegu 1213
#: (utworzony 11.09 12:42) odczytany przez API po **około dwóch dobach** — ale wyłącznie
#: `created_at`, `expires_at`, `expired` i rozmiar. Treść artefaktu starszego niż doba
#: nie została przeczytana **ani razu**; jedyny odczyt treści to 6.D93, tego samego dnia,
#: w którym przebieg chodził.
SIEGNIEC_PO_ARTEFAKT_STARSZY_NIZ_DOBA = 1
SIEGNIEC_PO_TRESC_STARSZA_NIZ_DOBA = 0

#: Rozstrzygnięcie dla KAŻDEJ z trzech wartości — powód albo zapisana granica.
#: Pole „Wyjście" pozycji dopuszcza oba, pod warunkiem że stoi to zapisane.
POWOD_RETENCJI = {
    30: "ZMIERZONY SENS (6.D164): trzydzieści dni to zasięg trendu, który da się "
        "zbudować z artefaktu czasu, i `test_timing_record` ten zasięg CZYTA z YAML-a "
        "zamiast nosić drugą kopię. Jedyna z dziewięciu, która ma powód, a nie tylko "
        "wartość.",
    14: "NIE DA SIĘ ROZSTRZYGNĄĆ Z HISTORII TEGO REPOZYTORIUM, i to jest wynik pomiaru, "
        "nie brak pomiaru: po żaden z tych sześciu artefaktów (rendery kontrolne T-010, "
        "T-012, T-210, T-211, T-220, T-400) nie sięgnięto ANI RAZU. Wszystkie oglądane "
        "rendery powstawały lokalnie. Ani „czternaście za mało”, ani „w sam raz” nie da "
        "się z tego materiału pokazać — a zmiana bez pomiaru stoi w „Poza zakresem”.",
    7: "TO SAMO, z tą samą podstawą: zero udokumentowanych sięgnięć po `t-902` "
       "(material-style) i po `line-trace` (sim, jedyny krok pod `failure()`). Siedem "
       "dni jest tu wartością wybraną raz i nietkniętą — co wiadomo, a czego nie da się "
       "obalić ani potwierdzić bez pierwszego sięgnięcia.",
}


def kroki_wynoszace_artefakt():
    """`[(plik, job, krok, nazwa, retencja)]` — czytane z YAML-a, nie z tekstu.

    Z YAML-a, bo `grep` po `retention-days` trafiłby też w komentarz z liczbą, a ten
    projekt ma ich w workflowach sporo.
    """
    out = []
    for plik in _workflows():
        plan = yaml.safe_load(_text(plik))
        for nazwa_joba, job in (plan.get("jobs") or {}).items():
            for krok in job.get("steps", []):
                if "upload-artifact" not in str(krok.get("uses", "")):
                    continue
                z = krok.get("with") or {}
                out.append((plik, nazwa_joba, krok.get("name"),
                            z.get("name"), z.get("retention-days")))
    return out


def test_rozklad_retencji_zgadza_sie_z_YAMLEM_a_nie_z_proza():
    """ODPOWIEDŹ 6.D194, połowa pierwsza: rozkład jest **14 SZEŚĆ razy**, nie pięć.

    Pole „Skąd" pozycji podawało 30×1, 14×5 i 7×2 — co sumuje się do **ośmiu** przy
    dziewięciu deklarowanych miejscach, więc było wewnętrznie sprzeczne. Liczba weszła
    do drzewa z raportu 6.D164 i stamtąd do `docs/TASKS.md`; raportu nie przepisuję
    (mówi o swoim dniu pomiaru), ale od teraz rozkład **liczy się z YAML-a**.
    """
    kroki = kroki_wynoszace_artefakt()
    assert len(kroki) == sum(RETENCJE_W_WORKFLOWACH.values()), (
        "kroków wynoszących artefakt jest %d, a rozkład sumuje się do %d: %s"
        % (len(kroki), sum(RETENCJE_W_WORKFLOWACH.values()),
           sorted((p, j) for p, j, _n, _a, _r in kroki)))

    import collections
    rozklad = collections.Counter(r for _p, _j, _n, _a, r in kroki)
    assert dict(rozklad) == RETENCJE_W_WORKFLOWACH, (
        "rozkład retencji to %s, a zmierzony 13.09.2026 był %s — nowy krok wynoszący "
        "artefakt ma być ROZSTRZYGNIĘCIEM, a nie liczbą, która się dopisała"
        % (dict(rozklad), RETENCJE_W_WORKFLOWACH))

    for plik, job, krok, nazwa, retencja in kroki:
        assert retencja is not None, (
            "krok `%s` w `%s` (job `%s`) wynosi artefakt `%s` BEZ `retention-days` — "
            "wtedy obowiązuje domyślna retencja repozytorium, o której ten projekt "
            "nie powiedział ani słowa" % (krok, plik, job, nazwa))


def test_kazda_wartosc_retencji_ma_POWOD_albo_ZAPISANA_GRANICE():
    """ODPOWIEDŹ 6.D194, połowa druga: jedna z trzech ma sens, dwie mają granicę.

    **Sięgnięć po artefakt starszy niż doba jest JEDNO w całej historii** — 6.D164,
    `czas-zestawu` z przebiegu 1213, po około dwóch dobach — i dotyczyło wyłącznie
    METADANYCH. Po **treść** artefaktu starszego niż doba nie sięgnięto ani razu.

    Dla ośmiu pozostałych artefaktów materiału nie ma **żadnego**: zero udokumentowanych
    sięgnięć, więc ani „za krótko", ani „w sam raz" nie da się pokazać. To jest wynik,
    a nie brak wyniku — pole „Wyjście" pozycji dopuszcza go wprost, pod warunkiem że
    stoi zapisany. Stoi, w `POWOD_RETENCJI`.
    """
    assert SIEGNIEC_PO_TRESC_STARSZA_NIZ_DOBA <= SIEGNIEC_PO_ARTEFAKT_STARSZY_NIZ_DOBA, (
        "sięgnięć po TREŚĆ jest więcej niż po artefakt w ogóle (%d > %d) — jedno jest "
        "podzbiorem drugiego, więc któraś liczba opisuje co innego, niż mówi"
        % (SIEGNIEC_PO_TRESC_STARSZA_NIZ_DOBA, SIEGNIEC_PO_ARTEFAKT_STARSZY_NIZ_DOBA))

    wartosci = set(RETENCJE_W_WORKFLOWACH)
    assert set(POWOD_RETENCJI) == wartosci, (
        "powody opisują wartości %s, a w workflowach stoją %s — wartość bez powodu "
        "wchodzi po cichu, a powód bez wartości opisuje krok, którego nie ma"
        % (sorted(POWOD_RETENCJI), sorted(wartosci)))

    # LICZNIK OBROTÓW, nie długość słownika — lekcja z 6.D193, gdzie kontrola negatywna
    # wyszła ZIELONA dwa razy, bo równość pilnowała słownika, a podstawienie oślepiało
    # pętlę. Pusta pętla przechodzi każdą asercję w środku.
    sprawdzonych = 0
    for dni, powod in sorted(POWOD_RETENCJI.items()):
        assert len(powod) > 120, (
            "powód przy retencji %d dni ma %d znaków — to za mało, żeby powiedzieć "
            "ALBO dlaczego tyle, ALBO czego zabrakło do rozstrzygnięcia"
            % (dni, len(powod)))
        sprawdzonych += 1
    assert sprawdzonych == len(RETENCJE_W_WORKFLOWACH), (
        "pętla powodów wykonała %d obrotów przy %d wartościach — pusta pętla przechodzi "
        "każdą asercję w środku (zmierzone przy 6.D193)"
        % (sprawdzonych, len(RETENCJE_W_WORKFLOWACH)))

    # I DRUGA STRONA: jedyna wartość z POWODEM ma go mieć wykonanym, a nie opowiedzianym.
    # `test_timing_record` czyta trzydziestkę z YAML-a; gdyby przestał, zostałby powód
    # bez mechanizmu — czyli zdanie o wartości, której nikt nie pilnuje.
    z_powodem = [p for p, _j, _n, _a, r in kroki_wynoszace_artefakt() if r == 30]
    assert z_powodem == ["python-tests.yml"], (
        "trzydziestodniową retencję ma dziś %s — powód z 6.D164 mówi o artefakcie CZASU "
        "i o nim jednym; przy drugim kroku z tą wartością trzeba go przeliczyć"
        % sorted(z_powodem))


# ---------------------------------------------------------------------------
# 6.D222 — duplikat klucza, którego `yaml.safe_load` nie widzi, a Actions odrzuca
# ---------------------------------------------------------------------------

class LoaderBezDuplikatow(yaml.SafeLoader):
    """`SafeLoader`, który odrzuca duplikat klucza — tak jak parser Actions.

    PyYAML przyjmuje duplikat **bez wyjątku i bez ostrzeżenia**, ostatni wygrywa;
    parser Actions tworzy wtedy przebieg, który kończy się startup failure **bez
    ani jednego joba**. Różnica kosztowała ten projekt 161 martwych przebiegów
    `prune-merged-branches.yml` — patrz `WORKFLOW_KTORY_NIE_WYSTARTOWAL`.
    """

    def construct_mapping(self, node, deep=False):
        widziane = set()
        for klucz_node, _ in node.value:
            klucz = self.construct_object(klucz_node, deep=deep)
            if klucz in widziane:
                raise yaml.constructor.ConstructorError(
                    None, None,
                    "duplikat klucza `%s`" % (klucz,), klucz_node.start_mark)
            widziane.add(klucz)
        return super().construct_mapping(node, deep=deep)


def _wczytaj_scisle(path):
    """Plik YAML przez loader odrzucający duplikaty; `ConstructorError` puszczamy dalej."""
    with open(path, encoding="utf-8") as uchwyt:
        return yaml.load(uchwyt.read(), Loader=LoaderBezDuplikatow)


def _pliki_yaml_ci():
    """Workflowy i akcje lokalne — wszystko, co parsuje Actions."""
    return sorted(
        [os.path.join(WORKFLOWS, n) for n in _workflows()] + _action_files())


#: Ile plików YAML-a czyta Actions w tym repozytorium. Podłoga, nie równość:
#: skan, który przestałby cokolwiek znajdować, odpowiedziałby „zero duplikatów"
#: tak samo przekonująco jak skan widzący.
MIN_PLIKOW_YAML_CI = 11

#: Kształty, które `yaml.safe_load` PRZEPUSZCZA — zmierzone 15.09.2026 na dziewięciu
#: próbkach syntetycznych; przechodzi osiem, odpada tylko tabulator we wcięciu.
#: **Dowód, że Actions odrzuca, istnieje dla JEDNEGO z nich** — duplikatu klucza,
#: i jest nim 161 przebiegów startup failure. O pozostałych siedmiu ten moduł nie
#: twierdzi nic, bo tego nie zmierzył.
PRZEPUSZCZANYCH_PRZEZ_PYYAML = 8

#: Workflow, którego duplikat `with:` zabił od 6.D108 (`2b95084`, PR #550).
WORKFLOW_KTORY_NIE_WYSTARTOWAL = "prune-merged-branches.yml"


def test_zaden_plik_yaml_CI_nie_ma_duplikatu_klucza():
    """Duplikat klucza jest dla Actions błędem SKŁADNI, a dla PyYAML-a nie jest niczym.

    Zmierzone przy 6.D222: `prune-merged-branches.yml` miał dwa klucze `with:`
    w kroku `Checkout` (wiersze 52 i 54) od commita `2b95084` i przez to **nie
    wystartował ani razu** — 161 przebiegów, sto na sto `push`/`failure`, każdy
    z ZEREM jobów. Osiemdziesiąt kilka testów tego modułu było na nim zielonych,
    bo `yaml.safe_load` duplikat po cichu przyjmuje.
    """
    pliki = _pliki_yaml_ci()
    assert len(pliki) >= MIN_PLIKOW_YAML_CI, (
        "plików YAML-a CI znaleziono %d przy podłodze %d — skan oślepł albo katalog "
        "się skurczył, a pusty skan odpowiada „zero duplikatów” tak samo jak widzący"
        % (len(pliki), MIN_PLIKOW_YAML_CI))

    zle = []
    for path in pliki:
        try:
            _wczytaj_scisle(path)
        except yaml.YAMLError as blad:
            zle.append("%s: %s" % (os.path.relpath(path, ROOT), blad))
    assert not zle, (
        "plik YAML-a, którego parser Actions nie przyjmie — przebieg powstanie "
        "i zginie jako startup failure, BEZ ani jednego joba:\n" + "\n".join(zle))


def test_loader_scisly_WIDZI_duplikat_ktorego_safe_load_NIE_widzi():
    """Kontrola PRZYRZĄDU, nie drzewa.

    Po poprawce 6.D222 duplikatów w drzewie jest **zero**, więc bramka wyżej stoi
    na zbiorze pustym i sama z siebie nie znaczy nic (6.D27, 6.D159): loader, który
    przestałby cokolwiek odrzucać, dałby tę samą zieleń. Ta próbka wykonuje oba
    czytniki na tym samym tekście i żąda, żeby ODPOWIEDZIAŁY RÓŻNIE.
    """
    z_duplikatem = ("jobs:\n  a:\n    runs-on: self-hosted\n"
                    "    with:\n      x: 1\n    with:\n      x: 2\n")
    bez_duplikatu = "jobs:\n  a:\n    runs-on: self-hosted\n    with:\n      x: 2\n"

    # PyYAML: duplikat przechodzi i wygrywa ostatni — czyli usterka wygląda jak kod.
    cichy = yaml.safe_load(z_duplikatem)
    assert cichy["jobs"]["a"]["with"] == {"x": 2}, (
        "`yaml.safe_load` przestał po cichu przyjmować duplikat — gdyby tak było "
        "naprawdę, cała ta bramka jest niepotrzebna i trzeba ją zdjąć, a nie poprawić")

    # Loader ścisły: ten sam tekst jest błędem, i komunikat nazywa klucz.
    try:
        yaml.load(z_duplikatem, Loader=LoaderBezDuplikatow)
        raise AssertionError("loader ścisły przepuścił duplikat — nie odróżnia się "
                             "już od `safe_load` i bramka wyżej nic nie znaczy")
    except yaml.constructor.ConstructorError as blad:
        assert "with" in str(blad), (
            "loader ścisły odrzucił duplikat, ale nie nazwał klucza `with` — "
            "komunikat bez nazwy nie mówi, gdzie szukać: %s" % blad)

    # I druga strona: tekst POPRAWNY ma przejść przez oba tak samo.
    assert (yaml.load(bez_duplikatu, Loader=LoaderBezDuplikatow)
            == yaml.safe_load(bez_duplikatu)), (
        "loader ścisły zmienia wynik na tekście bez duplikatu — to już nie jest "
        "zawężenie `safe_load`, tylko inny czytnik")


def test_ile_ksztaltow_PyYAML_przepuszcza_a_ile_odrzuca():
    """Osiem z dziewięciu — i tylko o jednym wiadomo, że Actions go odrzuca.

    Liczba jest tu po to, żeby nie dało się przeczytać tej pozycji jako „duplikat
    klucza to jedyna różnica między PyYAML-em a Actions". Różnic jest więcej;
    zmierzone jest, ile z nich PyYAML przepuszcza, a NIE zmierzone — które
    z nich Actions odrzuca. Jedyny dowód po tamtej stronie to 161 przebiegów
    `WORKFLOW_KTORY_NIE_WYSTARTOWAL`.
    """
    probki = {
        "duplikat klucza w mapowaniu": "a:\n  x: 1\na:\n  x: 2\n",
        "duplikat klucza na jednym poziomie": "jobs:\n  a:\n    r: x\n  a:\n    r: y\n",
        "kotwica i alias": "krok: &k\n  uses: a/b\ninny: *k\n",
        "klucz scalajacy": "baza: &b\n  x: 1\nnowy:\n  <<: *b\n  y: 2\n",
        "`on:` jako klucz": "on:\n  push:\n",
        "`yes`/`no` jako wartosc": "flaga: yes\n",
        "liczba osemkowa": "tryb: 0755\n",
        "liczba szescdziesietna": "czas: 1:30\n",
        "tabulator we wcieciu": "a:\n\tx: 1\n",
    }
    przeszlo, sprawdzonych = [], 0
    for nazwa, tekst in probki.items():
        try:
            yaml.safe_load(tekst)
            przeszlo.append(nazwa)
        except yaml.YAMLError:
            pass
        sprawdzonych += 1

    assert sprawdzonych == len(probki), (
        "pętla po próbkach wykonała %d obrotów przy %d próbkach — pusta pętla "
        "przechodzi każdą regułę w środku" % (sprawdzonych, len(probki)))
    assert len(przeszlo) == PRZEPUSZCZANYCH_PRZEZ_PYYAML, (
        "`yaml.safe_load` przepuszcza dziś %d kształtów z %d, a zmierzono %d: %s"
        % (len(przeszlo), len(probki), PRZEPUSZCZANYCH_PRZEZ_PYYAML, przeszlo))
    assert "tabulator we wcieciu" not in przeszlo, (
        "tabulator we wcięciu przestał być błędem — próbka, która miała być "
        "kontrolą od strony ODRZUCENIA, przestała nią być")


def test_workflow_ktory_nie_wystartowal_ma_JEDEN_klucz_with_w_checkoucie():
    """Przybita jest USTERKA, a nie tylko jej brak.

    Bramka wyżej mówi „żaden plik nie ma duplikatu" i to zdanie byłoby prawdziwe
    także wtedy, gdyby ktoś ten workflow skasował. Ten test pyta o konkretny plik
    i konkretny krok — czyli o to, co 6.D222 naprawiło.
    """
    tekst = _text(WORKFLOW_KTORY_NIE_WYSTARTOWAL)
    checkout = [w for w in tekst.split("\n") if "actions/checkout@" in w]
    assert len(checkout) == 1, (
        "`%s` ma %d kroków `actions/checkout@` — wpis 6.D222 opisuje jeden"
        % (WORKFLOW_KTORY_NIE_WYSTARTOWAL, len(checkout)))
    po_checkoucie = tekst.split("actions/checkout@", 1)[1]
    do_nastepnego_kroku = po_checkoucie.split("\n      - name:", 1)[0]
    assert do_nastepnego_kroku.count("\n        with:") == 1, (
        "krok `Checkout` w `%s` ma %d kluczy `with:` — dwa są dla Actions błędem "
        "składni i zabijają CAŁY przebieg, a `yaml.safe_load` ich nie widzi"
        % (WORKFLOW_KTORY_NIE_WYSTARTOWAL,
           do_nastepnego_kroku.count("\n        with:")))


#: Pakiety, które zestaw apt instaluje, a ŻADNA sonda o nie nie pyta — z powodem.
#:
#: Wpis na tej liście jest deklaracją: „ten pakiet nie ma sonamu, o który da się
#: spytać, i wiemy dlaczego". Bez niej bramka niżej zapalałaby się na konfiguracji
#: poprawnej (6.D27); z listą wpisaną bez powodów byłaby workaroundem.
PAKIETY_BEZ_SONDY = {
    "libgl1-mesa-dri":
        "nie dostarcza ANI JEDNEGO pliku `libGL.so*` — `dpkg -L` daje zero dopasowań; "
        "wozi wyłącznie sterowniki DRI ładowane przez `libGL.so.1` w czasie pracy, "
        "więc sondy na soname postawić się na nim nie da (zmierzone 07.09.2026, "
        "`reports/biblioteki-startowe-blendera.md`)",
}


def pakiety_bez_pokrycia_sonda(name):
    """Pakiety z zestawu apt tego workflow, o które nie pyta ANI JEDNA sonda — 6.D243.

    Kierunek ODWROTNY do `test_tool_installation_is_conditional_on_the_tool_being_missing`,
    i to jest cała treść tej funkcji. Tamta pyta „czy zestaw instaluje to, o co sonda
    pyta"; ta pyta „czy sonda pyta o to, co zestaw instaluje".
    """
    text = _text(name)
    document = yaml.safe_load(text)
    # Workflow bez kroku instalacji apt nie ma czego sondować — `_apt_set_of` w takim
    # przypadku ASERTUJE, więc warunek stoi PRZED wywołaniem, a nie po nim.
    if "apt_install.sh --set " not in text:
        return set()
    zestaw = _apt_set_of(text)
    pakiety = set(_apt_set_packages(zestaw))
    pokryte = set()
    for job in (document.get("jobs") or {}).values():
        for krok in job.get("steps") or []:
            if str(krok.get("uses", "")) != PROBE_ACTION:
                continue
            wanted = krok.get("with") or {}
            for soname in (wanted.get("libraries") or "").split():
                pokryte.add(_debian_package_for(soname))
            for polecenie in (wanted.get("commands") or "").split():
                pokryte.add(POLECENIA_Z_PAKIETOW.get(polecenie, polecenie))
            for modul in (wanted.get("python-modules") or "").split():
                pokryte.add(MODULY_Z_PAKIETOW.get(modul, modul))
    return {p for p in pakiety if p not in pokryte and p not in PAKIETY_BEZ_SONDY}


def test_kazdy_pakiet_zestawu_apt_jest_O_COS_PYTANY_przez_sonde():
    """Pakiet instalowany, o który nikt nie pyta, NIGDY się nie zainstaluje — 6.D243.

    **Skąd, i to nie jest rozumowanie, tylko kontrola negatywna.** 16.09.2026, przy
    domykaniu tej pozycji, KN-3 zdjęła `libXcursor.so.1` i `libwayland-cursor.so.0`
    z **wszystkich siedmiu** sond, zostawiając `libxcursor1` i `libwayland-cursor0`
    w obu zestawach apt. Zestaw przeszedł **88/88** — a jest to konfiguracja, w której
    pakiet stoi na liście i **nie zainstaluje się nigdy**: instalacja odpala się
    warunkowo (`if: steps.tools.outputs.libs == 'missing'`), więc sonda niepytająca
    o nic z tej biblioteki melduje `present` i krok jest pomijany.

    **To jest dokładnie droga, którą przyszła awaria tej pozycji.** `libXcursor.so.1`
    nie stał ani w sondzie, ani w zestawie — ale gdyby ktoś dopisał sam pakiet,
    naprawa byłaby POZORNA, a drzewo milczałoby tak samo. Wiązanie było
    jednokierunkowe: `test_tool_installation_is_conditional_on_the_tool_being_missing`
    pyta, czy zestaw instaluje to, o co sonda pyta. Ta bramka pyta w drugą stronę.

    **Czego ta bramka NIE robi:** nie sprawdza, czy pakiet jest na maszynie — tego
    z repozytorium sprawdzić się nie da. Sprawdza, czy job ma jak zauważyć jego brak.
    """
    for name in _workflows():
        bez_pokrycia = sorted(pakiety_bez_pokrycia_sonda(name))
        assert not bez_pokrycia, (
            "%s: zestaw apt instaluje %s, a żadna sonda o to nie pyta — instalacja "
            "jest warunkowa, więc ten pakiet nie zainstaluje się NIGDY, a brak wyjdzie "
            "dopiero w środku pracy joba. Dopisz sondę albo wpisz pakiet do "
            "`PAKIETY_BEZ_SONDY` Z POWODEM." % (name, bez_pokrycia))


def test_lista_pakietow_bez_sondy_NIE_jest_workaroundem():
    """Każdy wpis `PAKIETY_BEZ_SONDY` niesie powód i naprawdę jest w jakimś zestawie.

    Bez tej asercji poprzednia bramka dałaby się uciszyć dopisaniem nazwy — czyli
    byłaby bramką, którą się wyłącza zamiast naprawiać (6.D27, od drugiej strony).
    """
    assert PAKIETY_BEZ_SONDY, "lista pusta — wtedy wyjątek przestał być wyjątkiem"
    wszystkie = set()
    for nazwa in os.listdir(PACKAGE_SETS):
        if nazwa.endswith(".txt"):
            wszystkie |= set(_apt_set_packages(nazwa[:-len(".txt")]))
    for pakiet, powod in sorted(PAKIETY_BEZ_SONDY.items()):
        assert len(powod) >= 60, (
            "wyjątek na %s ma powód krótszy niż 60 znaków — to nie jest powód, "
            "tylko zgoda" % pakiet)
        assert pakiet in wszystkie, (
            "%s stoi w `PAKIETY_BEZ_SONDY`, a nie ma go w ŻADNYM zestawie apt — "
            "wyjątek przeżył pakiet, którego dotyczył" % pakiet)
