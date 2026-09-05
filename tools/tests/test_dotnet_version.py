#!/usr/bin/env python3
"""Runtime .NET jest zapisany w wielu miejscach i muszą się zgadzać.

Powód: migracja 8 -> 10 z 02.09.2026 dotknęła pięciu plików projektu i trzech
workflow. Rozjazd między `TargetFramework` a `dotnet-version` w `setup-dotnet`
nie daje czytelnego błędu — job instaluje SDK, po czym `dotnet build` przewraca
się na komunikat o brakującym targeting packu, który nie wskazuje na workflow.

Powód drugi: .NET 8 kończy wsparcie 10.11.2026. Test pilnuje też, żeby projekt
nie osunął się z powrotem na wersję po dacie końca wsparcia.
"""
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
WORKFLOWS = os.path.join(ROOT, ".github", "workflows")

#: Dokument, z którego CZŁOWIEK stawia środowisko. Dopisany do pilnowanych miejsc
#: 04.09.2026 z tego samego powodu co przy silniku: po podniesieniu net8 -> net10
#: (`ba93903`) `docs/23-environment.md` nadal kazał instalować `dotnet-sdk-8.0`
#: i podawał „zmierzone: 8.0.130". Testy zgodności csproj <-> workflow świeciły
#: zielono, bo dokument nie był dla nich jednym z pilnowanych miejsc. Świeża
#: maszyna postawiona z tego dokumentu wywraca się na `NETSDK1045: The current
#: .NET SDK does not support targeting .NET 10.0` — zmierzone 04.09.2026.
DOC = os.path.join(ROOT, "docs", "23-environment.md")

PROJECTS = [
    os.path.join("src", "Sim", "Sim.csproj"),
    os.path.join("src", "Sim.Runner", "Sim.Runner.csproj"),
    os.path.join("src", "Game", "MetroBxl.Game.csproj"),
    os.path.join("tests", "Sim.Tests", "Sim.Tests.csproj"),
    os.path.join("tests", "Game.Tests", "Game.Tests.csproj"),
]

# .NET 8 kończy wsparcie 10.11.2026 (Microsoft, polityka wsparcia .NET Core).
# Wersje poniżej tej granicy są odrzucane, żeby powrót do nich wymagał
# zmiany testu, a nie przeoczenia w jednym csproj.
MINIMUM_SUPPORTED_MAJOR = 10


def _read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def target_framework(text):
    """Wartość `<TargetFramework>`, np. `net10.0`."""
    match = re.search(r"<TargetFramework>\s*(net[0-9]+\.[0-9]+)\s*</TargetFramework>", text)
    return match.group(1) if match else None


def tfm_major(tfm):
    """`net10.0` -> 10."""
    if tfm is None:
        return None
    match = re.match(r"net([0-9]+)\.", tfm)
    return int(match.group(1)) if match else None


def setup_dotnet_versions(text):
    """Wszystkie `dotnet-version:` z workflow, np. ['10.0.x']."""
    return re.findall(r"^\s*dotnet-version:\s*'([^']+)'\s*$", text, re.MULTILINE)


def _workflows():
    return sorted(f for f in os.listdir(WORKFLOWS) if f.endswith((".yml", ".yaml")))


def doc_sdk_majors(text):
    """Główne wersje SDK .NET podane w dokumencie jako STAN AKTUALNY.

    Pomija wiersze, które dokument sam oznacza jako historyczne — przepisywanie
    reguły z podaniem poprzedniej wersji jest w tym projekcie regułą, nie błędem.
    """
    out = set()
    for line in text.splitlines():
        stripped = line.strip()
        if re.search(r"poprzedni|było|dawn|do 0[0-9]\.0[0-9]\.20|wcześniej", stripped, re.I):
            continue
        for match in re.finditer(r"dotnet-sdk-([0-9]+)\.[0-9]+", stripped):
            out.add(match.group(1))
        for match in re.finditer(r"dotnet-version:\s*'?([0-9]+)\.[0-9]+\.?x?'?", stripped):
            out.add(match.group(1))
        for match in re.finditer(r"\.NET SDK\D{0,4}([0-9]+)\.[0-9]+", stripped):
            out.add(match.group(1))
    return out


def test_the_document_declares_the_same_sdk_major():
    """Dokument stawiania środowiska musi podawać ten SDK, którego wymagają projekty."""
    major = tfm_major(target_framework(_read(os.path.join(ROOT, PROJECTS[0]))))
    declared = doc_sdk_majors(_read(DOC))
    assert declared, "dokument nie podaje ani jednej wersji SDK .NET"
    obce = sorted(v for v in declared if v != str(major))
    assert not obce, (
        f"docs/23-environment.md podaje jako aktualne SDK .NET {obce}, "
        f"a projekty celują w net{major}.0 — instrukcja nie zadziała")


def test_the_document_parser_ignores_a_historical_note():
    # Bez tej kontroli bramka wyżej przechodziłaby także wtedy, gdyby parser
    # zwracał pusty zbiór na wszystkim — a wtedy `obce` jest puste zawsze.
    assert doc_sdk_majors("apt-get install -y dotnet-sdk-10.0") == {"10"}
    assert doc_sdk_majors("poprzednio: dotnet-sdk-8.0") == set()
    assert doc_sdk_majors("## 3. .NET SDK 8.0") == {"8"}
    assert doc_sdk_majors("dotnet-version: '10.0.x'") == {"10"}


def test_every_project_declares_a_target_framework():
    for rel in PROJECTS:
        tfm = target_framework(_read(os.path.join(ROOT, rel)))
        assert tfm is not None, f"{rel} bez <TargetFramework>"


def test_all_projects_share_one_target_framework():
    # Rdzeń, runner, warstwa gry i oba projekty testowe referują się nawzajem.
    # Projekt na starszym TFM nie zbuduje się wobec nowszej referencji, a błąd
    # wskaże referencję, nie rozjazd.
    found = {rel: target_framework(_read(os.path.join(ROOT, rel))) for rel in PROJECTS}
    assert len(set(found.values())) == 1, found


def test_target_framework_is_still_supported():
    for rel in PROJECTS:
        major = tfm_major(target_framework(_read(os.path.join(ROOT, rel))))
        assert major >= MINIMUM_SUPPORTED_MAJOR, (
            f"{rel} celuje w .NET {major}; wsparcie .NET 8 kończy się 10.11.2026")


def test_workflows_install_the_same_major_as_the_projects():
    major = tfm_major(target_framework(_read(os.path.join(ROOT, PROJECTS[0]))))
    for name in _workflows():
        for version in setup_dotnet_versions(_read(os.path.join(WORKFLOWS, name))):
            assert version.startswith(f"{major}."), (
                f"{name}: setup-dotnet {version} wobec projektów net{major}.0")


def test_at_least_one_workflow_installs_dotnet():
    # Bez tego test wyżej przechodziłby także wtedy, gdyby `dotnet-version`
    # zniknął ze wszystkich workflow — pętla po pustej liście nic nie sprawdza.
    total = sum(len(setup_dotnet_versions(_read(os.path.join(WORKFLOWS, n))))
                for n in _workflows())
    assert total >= 3, f"tylko {total} kroków setup-dotnet; było ich trzy"


def workflows_with_setup_dotnet():
    """Nazwy workflow, które w ogóle instalują SDK."""
    return [n for n in _workflows()
            if "actions/setup-dotnet" in _read(os.path.join(WORKFLOWS, n))]


def install_dir_step_index(text):
    """Numer linii, w której workflow ustawia `DOTNET_INSTALL_DIR`; inaczej None."""
    match = re.search(r"^\s*echo\s+\"DOTNET_INSTALL_DIR=.*>>\s*\"\$GITHUB_ENV\"",
                      text, re.MULTILINE)
    return match.start() if match else None


def setup_dotnet_index(text):
    match = re.search(r"^\s*uses:\s*actions/setup-dotnet@", text, re.MULTILINE)
    return match.start() if match else None


def test_every_setup_dotnet_gets_a_writable_install_dir():
    """CI 02.09.2026: `setup-dotnet` celował w /usr/share/dotnet i padał na prawach.

    Runner właściciela nie jest rootem, więc domyślny katalog SDK dawał serię
    `mkdir: Permission denied`. Na jednorazowej maszynie GitHuba to nie wychodziło,
    bo tam runner jest rootem — i dlatego bramka musi być tutaj, a nie w głowie.
    """
    for name in workflows_with_setup_dotnet():
        text = _read(os.path.join(WORKFLOWS, name))
        assert install_dir_step_index(text) is not None, (
            f"{name}: setup-dotnet bez DOTNET_INSTALL_DIR — poleci do /usr/share/dotnet")


def test_install_dir_is_set_before_setup_dotnet_runs():
    # Kolejność nie jest kosmetyczna: `setup-dotnet` czyta zmienną w momencie
    # uruchomienia, więc krok ustawiający ją PO nim nie zmienia niczego.
    for name in workflows_with_setup_dotnet():
        text = _read(os.path.join(WORKFLOWS, name))
        assert install_dir_step_index(text) < setup_dotnet_index(text), (
            f"{name}: DOTNET_INSTALL_DIR ustawiany po kroku setup-dotnet")


def without_comments(text):
    """Linie workflow bez komentarzy YAML i bez komentarzy powłoki.

    Pierwsza wersja tego testu szukała `RUNNER_TOOL_CACHE` w całym pliku i
    przechodziła, bo napis stoi też w KOMENTARZU tłumaczącym, po co ten katalog.
    Mutacja podmieniająca kod na `$HOME` przeżyła. Bramka czytająca komentarze
    sprawdza dokumentację, nie zachowanie.
    """
    return "\n".join(l for l in text.splitlines() if not l.lstrip().startswith("#"))


def test_install_dir_comes_from_the_runner_tool_cache():
    # `RUNNER_TOOL_CACHE` wskazuje `_tool` — rodzeństwo workspace'u, którego
    # `git clean -ffdx` z `actions/checkout` nie dotyka. Katalog w workspace
    # znikałby przy każdym checkoucie, a w /usr — nie dałby się utworzyć.
    for name in workflows_with_setup_dotnet():
        code = without_comments(_read(os.path.join(WORKFLOWS, name)))
        assert "RUNNER_TOOL_CACHE" in code, (
            f"{name}: katalog SDK nie pochodzi z tool cache (komentarz się nie liczy)")
        assert 'echo "::error::katalog SDK' in code, (
            f"{name}: brak kontroli, że katalog nie leży w workspace ani w /usr")


def test_the_comment_stripper_actually_strips():
    # Kontrola negatywna do poprawki wyżej.
    assert "RUNNER_TOOL_CACHE" not in without_comments("      # RUNNER_TOOL_CACHE\n")
    assert "RUNNER_TOOL_CACHE" in without_comments('      cache="$RUNNER_TOOL_CACHE"\n')


def test_there_is_something_to_check():
    # Bez tego trzy testy wyżej przechodziłyby po pustej liście workflow.
    assert len(workflows_with_setup_dotnet()) >= 3, workflows_with_setup_dotnet()


def test_parsers_reject_what_they_should():
    assert target_framework("<TargetFramework>netstandard2.0</TargetFramework>") is None
    assert target_framework("<TargetFrameworks>net10.0;net8.0</TargetFrameworks>") is None
    assert setup_dotnet_versions("  dotnet-version: 10.0.x\n") == [], "bez cudzysłowów"
    assert tfm_major("net10.0") == 10
    assert tfm_major("net8.0") == 8
    assert tfm_major("net8.0") < MINIMUM_SUPPORTED_MAJOR


# --- doctor.sh sprawdza WERSJĘ SDK, nie samą obecność `dotnet` -----------------------

DOCTOR = os.path.join(ROOT, "doctor.sh")


def test_doctor_compares_the_sdk_major_against_the_target_framework():
    """`chk_required "dotnet SDK" "dotnet --version"` sprawdzało tylko, czy `dotnet`
    się uruchamia.

    Zmierzone 04.09.2026, zaraz po podniesieniu rdzenia na `net10.0`: doctor na
    SDK 8.0.130 wypisywał `ok dotnet SDK`, a dwadzieścia wierszy niżej
    `BLAD dotnet test nie przechodzi` z błędem NETSDK1045 — czyli mówił „ok"
    o tym samym SDK, przez które przed chwilą padł. Podpowiedź obiecywała
    „.NET SDK 10.0+", ale nikt tego nie sprawdzał.

    Wymagana wersja ma pochodzić z `<TargetFramework>`, a nie być wpisana w doctora
    z ręki — inaczej przy następnym podniesieniu byłyby dwa źródła prawdy.
    """
    with open(DOCTOR, encoding="utf-8") as handle:
        doctor = handle.read()

    assert "REQUIRED_TFM" in doctor, "doctor nie czyta wymaganej wersji znikąd"
    assert "src/Sim/Sim.csproj" in doctor, (
        "doctor musi brać wymaganą wersję z csproj, a nie z liczby wpisanej obok")
    assert "NETSDK1045" in doctor, "podpowiedź nie nazywa błędu, który tu pada"

    # Liczba major NIE może stać w doctorze jako literał obok warunku.
    major = tfm_major(target_framework(open(
        os.path.join(ROOT, "src", "Sim", "Sim.csproj"), encoding="utf-8").read()))
    assert f'-ge "{major}"' not in doctor and f"-ge {major}" not in doctor, (
        f"doctor porównuje z wpisaną liczbą {major} zamiast z odczytaną z csproj")


def test_doctor_sdk_check_actually_reads_the_current_target_framework():
    """Sam `sed` z doctora, puszczony na tym samym pliku, ma dać dzisiejszą wersję."""
    import re
    import subprocess

    match = re.search(r'REQUIRED_TFM="\$\((.+?)\)"', open(DOCTOR, encoding="utf-8").read())
    assert match, "nie znalazłem podstawienia REQUIRED_TFM w doctor.sh"

    got = subprocess.run(["bash", "-c", match.group(1)], cwd=ROOT,
                         capture_output=True, text=True).stdout.strip()
    expected = tfm_major(target_framework(open(
        os.path.join(ROOT, "src", "Sim", "Sim.csproj"), encoding="utf-8").read()))
    assert got == str(expected), (got, expected)


def test_doctor_sdk_condition_actually_rejects_an_old_sdk():
    """Kontrola, która sprawdza OBECNOŚĆ warunku, nie sprawdza, czy warunek działa.

    Kontrola negatywna 04.09.2026: podmiana samego porównania na `true` przechodziła
    cały zestaw — dwa poprzednie testy pilnowały, że w doctorze STOI odczyt wersji
    z csproj, ale żaden nie pytał, czy porównanie cokolwiek odrzuca. Ten wyciąga
    warunek z pliku i URUCHAMIA go dla SDK starszego i nowszego od wymaganego.
    """
    import re
    import subprocess

    doctor = open(DOCTOR, encoding="utf-8").read()
    # Wyrażenie `"([^"]+)"` urywało się na pierwszym `\"` i wyciągało `[ \\` —
    # warunek z cudzysłowami w środku trzeba brać po wierszu, nie po parze cudzysłowów.
    #
    # Selektor wymaga też, żeby wiersz był ARGUMENTEM `chk_required`, czyli zaczynał
    # się od cudzysłowa. Bez tego łapał dwa wiersze od 04.09.2026, gdy doszła
    # podpowiedź szukająca nowszego SDK na dysku — ona też porównuje `-ge` z
    # `REQUIRED_TFM`, ale jest osobnym warunkiem i nie jest tym, co ten test mierzy.
    # Zawężony jest SELEKTOR, nie asercja: dalej wyciąga warunek i go URUCHAMIA.
    lines = [line.strip() for line in doctor.splitlines()
             if "-ge" in line and "REQUIRED_TFM" in line
             and line.strip().startswith('"')]
    assert len(lines) == 1, lines
    condition = lines[0].rstrip("\\").strip()
    assert condition.startswith('"') and condition.endswith('"'), condition
    condition = condition[1:-1].replace('\\"', '"')

    required = tfm_major(target_framework(open(
        os.path.join(ROOT, "src", "Sim", "Sim.csproj"), encoding="utf-8").read()))

    def run(have):
        script = f'HAVE_SDK_MAJOR="{have}"; REQUIRED_TFM="{required}"; {condition}'
        return subprocess.run(["bash", "-c", script]).returncode

    assert run(required - 1) != 0, f"warunek przepuścił SDK {required - 1} przy wymaganym {required}"
    assert run(required) == 0, f"warunek odrzucił SDK {required} przy wymaganym {required}"
    assert run(required + 1) == 0, "warunek odrzucił SDK nowsze niż wymagane"



def _run_doctor(dotnet_version, home_version=None):
    """Uruchamia PRAWDZIWY `doctor.sh` z podstawionym `dotnet`, bez sieci i bez SDK.

    Dwie atrapy: jedna pod `DOTNET_BIN` (udaje SDK, które doctor ma sprawdzić),
    druga pod `$HOME/.dotnet/dotnet` (udaje SDK leżące na dysku poza `PATH`).
    `home_version=None` znaczy „w katalogu domowym nie ma nic".

    Bramka na obecność napisu `DOTNET_BIN` w pliku nie odróżniłaby zmiennej użytej
    od zmiennej wspomnianej w komentarzu — a ten plik ma jej w komentarzach cztery.
    """
    import subprocess
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        def stub(path, version):
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as handle:
                handle.write("#!/bin/sh\n"
                             'if [ "$1" = "--version" ]; then echo "%s"; exit 0; fi\n'
                             "exit 1\n" % version)
            os.chmod(path, 0o755)

        fake_bin = os.path.join(tmp, "bin", "dotnet")
        stub(fake_bin, dotnet_version)
        fake_home = os.path.join(tmp, "home")
        os.makedirs(fake_home, exist_ok=True)
        if home_version is not None:
            stub(os.path.join(fake_home, ".dotnet", "dotnet"), home_version)

        env = dict(os.environ)
        env.update(DOTNET_BIN=fake_bin, HOME=fake_home, LC_ALL="C")
        # `--no-tests`, bo doctor bez tej flagi uruchamia `test_all.py` — czyli
        # ten zestaw uruchamiałby sam siebie, cztery razy pod rząd. Pierwsza wersja
        # tej bramki tak robiła i przekroczyła limit czasu; flaga powstała po to.
        done = subprocess.run(["bash", DOCTOR, "--no-tests"], cwd=ROOT, env=env,
                              capture_output=True, text=True, timeout=120)
        return done.stdout + done.stderr


def test_doctor_honours_dotnet_bin_the_same_way_as_blender_bin():
    """`DOTNET_BIN` musi być UŻYWANY, nie tylko wspomniany w komentarzu.

    Ta sama konwencja co `${BLENDER_BIN:-blender}` w sześciu skryptach `tools/ci/`
    i co `GODOT_BIN`, i z tego samego powodu: SDK potrafi leżeć poza `PATH`.
    Zmierzone w środowisku tej sesji 04.09.2026 — `dotnet` z `PATH` to 8.0.130,
    a obok stoi 10.0.400 w katalogu domowym.

    Test podstawia atrapę zgłaszającą wersję 99 i wymaga, żeby doctor ją zobaczył.
    Gdyby czytał `dotnet` z `PATH`, wypisałby wersję systemową i test by padł.
    """
    out = _run_doctor("99.1.2")
    required = tfm_major(target_framework(open(
        os.path.join(ROOT, "src", "Sim", "Sim.csproj"), encoding="utf-8").read()))
    assert f"ok    dotnet SDK >= {required} (jest 99)" in out, out[:1500]


def test_doctor_points_at_the_newer_sdk_that_is_already_on_disk():
    """Kazać pobrać SDK, które leży na dysku, jest gorsze od milczenia.

    Brzmi jak brak, a jest ślepotą narzędzia. Doctor ma najpierw POSZUKAĆ,
    i podpowiedzieć gotowe polecenie.
    """
    out = _run_doctor("8.0.130", home_version="99.1.2")
    assert "na dysku JEST nowsze SDK" in out, out[:1500]
    assert "DOTNET_BIN=" in out and "bash doctor.sh" in out, out[:1500]


def test_doctor_does_not_invent_an_sdk_that_is_not_there():
    """Kontrola po DRUGIEJ stronie podpowiedzi — bez niej byłaby ona zawsze prawdziwa.

    Gdy nowszego SDK naprawdę nie ma, doctor musi zgłosić brak i NIE obiecywać
    niczego na dysku. Podpowiedź o SDK, którego tam nie ma, to ten sam błąd,
    tylko w drugą stronę.
    """
    out = _run_doctor("8.0.130", home_version=None)
    required = tfm_major(target_framework(open(
        os.path.join(ROOT, "src", "Sim", "Sim.csproj"), encoding="utf-8").read()))
    assert f"BRAK  dotnet SDK >= {required} (jest 8)" in out, out[:1500]
    assert "na dysku JEST nowsze SDK" not in out, out[:1500]


def test_doctor_does_not_offer_an_sdk_that_is_also_too_old():
    """Kandydat, który ISTNIEJE, ale jest za stary, nie może być podpowiedziany.

    Ta kontrola powstała z pomiaru na samej bramce, nie z ostrożności. Mutacja
    `if [ "$cand_major" -ge "$REQUIRED_TFM" ]` -> `if true` PRZECHODZIŁA cały zestaw:
    pozostałe testy podstawiały `home_version=None`, czyli brak pliku, więc pętla
    wychodziła już na `[ -x "$candidate" ]` i do porównania wersji nigdy nie docierała.
    Sprawdzanie wersji kandydata było niepokryte, a to ono decyduje, czy podpowiedź
    jest prawdą.

    Tutaj kandydat istnieje i jest NOWSZY od tego pod `DOTNET_BIN`, ale nadal
    starszy od wymaganego — doctor ma zgłosić brak i milczeć o dysku.
    """
    required = tfm_major(target_framework(open(
        os.path.join(ROOT, "src", "Sim", "Sim.csproj"), encoding="utf-8").read()))
    za_stary = required - 1
    assert za_stary >= 1, required

    out = _run_doctor("8.0.130", home_version="%d.0.100" % za_stary)
    assert "BRAK  dotnet SDK >= %d (jest 8)" % required in out, out[:1200]
    assert "na dysku JEST nowsze SDK" not in out, (
        "doctor podpowiedzial SDK %d.x przy wymaganym %d:\n%s"
        % (za_stary, required, out[:1000]))


def test_doctor_does_not_offer_the_sdk_it_was_already_told_to_use():
    """Podpowiedź „użyj tego, czego właśnie użyłem" byłaby szumem.

    Gdy `DOTNET_BIN` już wskazuje na SDK z katalogu domowego, a ono samo jest
    za stare, doctor ma zgłosić brak bez odsyłania do tego samego pliku.
    """
    import subprocess
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        home = os.path.join(tmp, "home")
        path = os.path.join(home, ".dotnet", "dotnet")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write('#!/bin/sh\nif [ "$1" = "--version" ]; then echo "8.0.130"; '
                         "exit 0; fi\nexit 1\n")
        os.chmod(path, 0o755)
        env = dict(os.environ)
        env.update(DOTNET_BIN=path, HOME=home, LC_ALL="C")
        done = subprocess.run(["bash", DOCTOR, "--no-tests"], cwd=ROOT, env=env,
                              capture_output=True, text=True, timeout=120)
        out = done.stdout + done.stderr
    assert "BRAK  dotnet SDK >= " in out, out[:1500]
    assert "na dysku JEST nowsze SDK" not in out, out[:1500]


def test_doctor_no_tests_flag_really_skips_both_suites():
    """Flaga musi POMIJAĆ zestawy, nie tylko istnieć.

    Bez tej kontroli `--no-tests` mogłoby być przyjmowanym argumentem, który nic
    nie robi — a wtedy bramki wyżej uruchamiałyby `test_all.py` wewnątrz
    `test_all.py`. Rozstrzyga porównanie WYJŚĆ: z flagą nie ma nagłówków sekcji
    testowych, bez flagi są.
    """
    import subprocess

    env = dict(os.environ)
    env["LC_ALL"] = "C"
    # Limit 60 s jest tu CZĘŚCIĄ ASERCJI, nie ostrożnością. Zdrowy przebieg
    # z `--no-tests` trwa ~1,5 s. Mutant, który flagę ignoruje, MUSI uruchomić oba
    # zestawy — więc albo przekroczy limit, albo wypisze nagłówki sekcji testowych.
    # Jedno i drugie wywraca ten test, i to jest cała jego treść. Zmierzone
    # 04.09.2026 na mutacji `--no-tests) RUN_TESTS=1`.
    szybko = subprocess.run(["bash", DOCTOR, "--no-tests"], cwd=ROOT, env=env,
                            capture_output=True, text=True, timeout=60)
    out = szybko.stdout + szybko.stderr
    assert "Testy narzędzi:" not in out, out[-800:]
    assert "Testy rdzenia symulacji:" not in out, out[-800:]
    # ...a kontrola środowiska nadal się wykonuje, inaczej flaga wyłączałaby wszystko.
    assert "dotnet SDK" in out, out[-800:]
    assert "python3" in out, out[-800:]


def test_doctor_rejects_an_unknown_argument():
    """Cichy `doctor.sh --no-test` (literówka) byłby pełnym przebiegiem udającym szybki."""
    import subprocess

    env = dict(os.environ)
    env["LC_ALL"] = "C"
    # `--no-tests` PRZED literówką, i to nie z wygody: gdyby doctor przestał
    # odrzucać nieznany argument, `--no-test` wpadłby w gałąź `*)`, `RUN_TESTS`
    # zostałoby na 1 i mutant uruchomiłby oba zestawy testów WEWNĄTRZ tego testu.
    # Pierwsza wersja tak robiła i mierzyła limit czasu zamiast zachowania.
    done = subprocess.run(["bash", DOCTOR, "--no-tests", "--no-test"], cwd=ROOT,
                          env=env, capture_output=True, text=True, timeout=120)
    assert done.returncode == 2, done.returncode
    assert "nieznany argument" in done.stdout + done.stderr


def test_doctor_cannot_recurse_into_itself():
    """Zagnieżdżony doctor pomija zestawy BEZ WZGLĘDU na argumenty.

    Powód jest zmierzony, nie przewidziany. Doctor uruchamia `test_all.py`, a ten
    zestaw zawiera bramki uruchamiające doctora — pętla jest przerwana tylko tym,
    że bramki podają `--no-tests`. Mutacja `--no-tests) RUN_TESTS=1` zamieniła to
    04.09.2026 w rekurencję wykładniczą: w systemie zostało 174 procesy
    `test_all.py`. Marker w środowisku zamyka całą tę klasę, a nie jedną mutację.
    """
    import subprocess

    env = dict(os.environ)
    env.update(LC_ALL="C", MBXL_DOCTOR_RUNNING="1")
    done = subprocess.run(["bash", DOCTOR], cwd=ROOT, env=env,
                          capture_output=True, text=True, timeout=120)
    out = done.stdout + done.stderr
    assert "doctor jest już uruchomiony wyżej" in out, out[-800:]
    assert "Testy narzędzi:" not in out, out[-800:]
    assert "Testy rdzenia symulacji:" not in out, out[-800:]
    # Kontrola środowiska musi się nadal wykonać — inaczej marker wyłączałby wszystko.
    assert "dotnet SDK" in out, out[-800:]

# --- doctor.sh nie mówi „testy nie przechodzą", gdy testy nie pobiegły ---------------
#
# Zmierzone 05.09.2026, dwa razy niezależnie: na maszynie, gdzie `dotnet` z PATH to
# 8.0.130, a 10.0.400 stoi obok w `$HOME/.dotnet`, doctor kończył twardym
# `BLAD  dotnet test nie przechodzi`. W logu nie było ANI JEDNEGO niezaliczonego
# testu — było `NETSDK1045`. Testy nie padły; one się nie odbyły.
#
# KOMUNIKAT NIE JEST WYNIKIEM. „Testy nie przechodzą" wysyła czytającego w `src/Sim`,
# a usterka leży w PATH. Oba przeglądy zgłosiły to jako blokadę środowiska i oba
# pomyliły się co do przyczyny — właśnie przez ten komunikat.
#
# DLACZEGO TEN TEST WYCINA GAŁĄŹ, A NIE URUCHAMIA CAŁEGO DOCTORA.
#
# Pierwsza wersja wołała `bash doctor.sh` z podstawionym `dotnet`. Przechodziła
# lokalnie i PADAŁA w CI, w jobie `blender-smoke` — bo tam `test_all.py` jest
# uruchamiany PRZEZ doctora, więc zagnieżdżony doctor trafiał na strażnik
# `MBXL_DOCTOR_RUNNING` i pomijał obie sekcje testów. Asercja o „NIE URUCHOMIONE"
# nie miała wtedy czego zobaczyć.
#
# Strażnika nie wolno osłabić: jest celowy i przybity osobnym testem
# (`test_doctor_cannot_recurse_into_itself`), a mutacja, która go zdjęła, zostawiła
# 04.09.2026 w systemie 174 procesy. Dlatego ten test idzie drogą, którą ten plik już
# zna z `test_doctor_sdk_condition_actually_rejects_an_old_sdk`: WYCINA fragment
# doctora i URUCHAMIA go. Bramka na napis nie odróżniłaby kodu wykonywanego od
# komentarza, więc czytanie tekstu nie wchodzi w grę.

#: Kotwice gałęzi decyzyjnej w `doctor.sh`. Gdy któraś zniknie, test PADA zamiast
#: cicho przejść na pustym zbiorze — bramka bez wejścia jest gorsza niż jej brak.
DECISION_OPEN = 'if ! command -v "${DOTNET_BIN:-dotnet}" >/dev/null 2>&1; then'
DECISION_CLOSE = '  echo "  BLAD  dotnet test nie przechodzi — zobacz $sim_log"'


def _decision_branch():
    """Sama gałąź „co zrobić z testami rdzenia", wycięta z doctora."""
    doctor = _read(DOCTOR)
    assert DECISION_OPEN in doctor, (
        "nie znalazłem początku gałęzi decyzyjnej w doctor.sh — kotwica się rozjechała "
        "i ten test przestałby cokolwiek sprawdzać")
    assert DECISION_CLOSE in doctor, (
        'nie znalazłem gałęzi o niezaliczonych testach w doctor.sh '
        '— kotwica się rozjechała')
    begin = doctor.index(DECISION_OPEN)
    # Gałąź ma zagnieżdżone `if`, więc szukamy `fi` w PIERWSZEJ kolumnie — tego,
    # które domyka blok zewnętrzny. `doctor.index("fi", ...)` trafiłby w domknięcie
    # wewnętrzne i wyciął fragment niedomknięty; złapane wykonaniem, nie na oko.
    end = doctor.index("\nfi\n", doctor.index(DECISION_CLOSE)) + len("\nfi")
    branch = doctor[begin:end]
    assert branch.count("if ") - branch.count("elif ") == branch.count("fi"), (
        "wycięty fragment nie ma domkniętych warunków — kotwice się rozjechały:\n" + branch)
    return branch


def _run_decision(tmp_path, reported_major, required_major):
    """Uruchamia wyciętą gałąź z podstawionym `dotnet` i zadanymi wersjami.

    Atrapa odmawia `test` komunikatem NETSDK1045 — dokładnie tak, jak robi to
    prawdziwe SDK 8 wobec `net10.0`.
    """
    import subprocess
    import stat

    shim = os.path.join(tmp_path, "dotnet")
    with open(shim, "w", encoding="utf-8") as handle:
        handle.write(
            "#!/bin/sh\n"
            "if [ \"$1\" = test ]; then\n"
            "  echo 'error NETSDK1045: The current .NET SDK does not support"
            " targeting .NET 10.0.' >&2\n"
            "  exit 1\n"
            "fi\n"
            f'echo "{reported_major}.0.130"\n')
    os.chmod(shim, os.stat(shim).st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

    script = os.path.join(tmp_path, "branch.sh")
    with open(script, "w", encoding="utf-8") as handle:
        handle.write(
            f'DOTNET_BIN="{shim}"\n'
            f'REQUIRED_TFM="{required_major}"\n'
            f'HAVE_SDK_MAJOR="{reported_major}"\n'
            "required_bad=0\n"
            f'TMPDIR="{tmp_path}"\n'
            + _decision_branch()
            + "\necho \"required_bad=$required_bad\"\n")

    syntax = subprocess.run(["bash", "-n", script], capture_output=True, text=True)
    assert syntax.returncode == 0, (
        "wycięty fragment doctora nie jest poprawnym shellem — test mierzyłby wtedy "
        "błąd składni, a nie decyzję:\n" + syntax.stderr)

    done = subprocess.run(["bash", script], cwd=ROOT, capture_output=True,
                          text=True, timeout=300)
    return done.stdout + done.stderr


def test_doctor_does_not_call_an_unbuilt_project_a_failing_test():
    """Za stare SDK ma dać „testy NIE URUCHOMIONE", a nie „testy nie przechodzą"."""
    import tempfile

    required = tfm_major(target_framework(_read(os.path.join(ROOT, PROJECTS[0]))))
    assert required is not None

    with tempfile.TemporaryDirectory() as tmp_path:
        output = _run_decision(tmp_path, required - 2, required)

    assert "dotnet test nie przechodzi" not in output, (
        "doctor twierdzi, że testy nie przechodzą, choć wcale ich nie uruchomił — "
        "to wysyła czytającego w kod symulacji zamiast w PATH:\n" + output)
    assert "NIE URUCHOMIONE" in output, (
        "doctor nie mówi wprost, że testy się nie odbyły:\n" + output)
    assert "NETSDK1045" in output, (
        "doctor nie nazywa błędu, przez który nie da się zbudować:\n" + output)
    assert "required_bad=1" in output, (
        "niesprawne środowisko przestało się liczyć jako błąd wymagany:\n" + output)


def test_doctor_reads_the_log_when_the_version_probe_said_nothing_useful():
    """Sonda wersji mogła zawieść, a build i tak padł na NETSDK1045 — rozstrzyga log.

    Kontrola przeciwna do poprzedniego testu: tutaj sonda podaje wersję DOSTATECZNĄ,
    więc gałąź „za stare SDK" nie zachodzi i doctor MUSI dojść do uruchomienia. Bez
    tego testu poprzedni przechodziłby także wtedy, gdyby doctor przestał uruchamiać
    testy w ogóle.
    """
    import tempfile

    required = tfm_major(target_framework(_read(os.path.join(ROOT, PROJECTS[0]))))

    with tempfile.TemporaryDirectory() as tmp_path:
        output = _run_decision(tmp_path, required, required)

    assert "NIE URUCHOMIONE" in output, (
        "doctor doszedł do uruchomienia, build padł na NETSDK1045, a mimo to nazywa "
        "to niezaliczonym testem:\n" + output)
    assert "nie zbuduje net" not in output, (
        "doctor zatrzymał się na sondzie wersji, choć wersja jest dostateczna:\n" + output)
    assert "required_bad=1" in output, output
