#!/usr/bin/env python3
"""Runtime .NET jest zapisany w wielu miejscach i muszą się zgadzać.

Powód: migracja 8 -> 10 z 02.09.2026 dotknęła pięciu plików projektu i trzech
workflow. Rozjazd między `TargetFramework` a `dotnet-version` w `setup-dotnet`
nie daje czytelnego błędu — job instaluje SDK, po czym `dotnet build` przewraca
się na komunikat o brakującym targeting packu, który nie wskazuje na workflow.

Powód drugi: .NET 8 kończy wsparcie 10.11.2026. Test pilnuje też, żeby projekt
nie osunął się z powrotem na wersję po dacie końca wsparcia.
"""
import json
import os
import re
import shutil
import sys

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


#: PIN SDK — jedno miejsce prawdy dla CI, `doctor.sh` i kontenera sesji (6.D79).
#:
#: **Dlaczego to nie kosmetyka.** `dotnet-version: '10.0.x'` jest WZORCEM KANAŁU:
#: instalator rozwiązuje go do najnowszej łatki **w momencie instalacji**, więc dwa
#: czyste runnery mogą zbudować ten sam commit różnymi wersjami narzędzi. Na maszynie
#: właściciela SDK przeżywa przebiegi w cache, więc rozjazd nie następuje między
#: przebiegami jednej maszyny — następuje MIĘDZY maszynami puli i po każdym
#: czyszczeniu cache narzędzi, czyli dokładnie tam, gdzie nikt na niego nie patrzy.
#:
#: Zmierzone 10.09.2026: runner `metro-01` ma SDK **10.0.401** (log joba `sim`,
#: przebieg PR #466: `dotnet-install: .NET Core SDK with version '10.0.401' is
#: already installed`), kontener tej sesji ma **10.0.401** (`dotnet --list-sdks`).
#: Pin nie podnosi więc niczego i nie ma podnosić — pole „Poza zakresem" pozycji
#: wyklucza podniesienie wersji SDK.
PIN = os.path.join(ROOT, "global.json")

#: Pełna trójka, a nie wzorzec. `x`, `*` i pusty człon są tu tym, co pozycja tropi.
PELNA_WERSJA = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")

#: Polityki przewijania, które `dotnet` zna. Wpisana MUSI być jawnie: domyślna
#: (`latestPatch`) jest w tym pliku niewidoczna, a niewidoczna polityka jest
#: dokładnie tym, przez co wzorzec kanału przetrwał tak długo.
POLITYKI = ("disable", "patch", "feature", "minor", "major",
            "latestPatch", "latestFeature", "latestMinor", "latestMajor")


def _pin_sdk_lub_stop():
    """Blok `sdk`, albo czytelna asercja zamiast `AttributeError` na `None`.

    Bez tego trzy bramki niżej przy braku pliku padają na
    `'NoneType' object has no attribute 'get'` — czyli mówią o Pythonie zamiast
    o tym, czego brakuje. Zmierzone kontrolą negatywną KN-3.
    """
    sdk = pin_sdk()
    assert sdk, (
        "brak `global.json` albo pliku bez bloku `sdk` — pin SDK nie istnieje, "
        "a `test_the_sdk_pin_file_exists` mówi o tym wprost")
    return sdk


def pin_sdk():
    """Blok `sdk` z pliku pinu albo `None`, gdy pliku nie ma."""
    if not os.path.isfile(PIN):
        return None
    with open(PIN, encoding="utf-8") as uchwyt:
        return (json.load(uchwyt) or {}).get("sdk")


def test_the_sdk_pin_file_exists():
    """Warunek pierwszy z czterech: plik pinu jest w drzewie."""
    assert os.path.isfile(PIN), (
        "brak `global.json` — bez niego `dotnet build` bierze NAJNOWSZE SDK, jakie "
        "zastanie na maszynie, a wzorzec kanału w workflowie tego nie ogranicza")
    assert pin_sdk(), "`global.json` bez bloku `sdk`"


def test_the_pinned_version_is_a_full_triple_and_not_a_channel_pattern():
    """Warunek drugi: wersja jest pełną trójką, a polityka przewijania jest JAWNA."""
    sdk = _pin_sdk_lub_stop()
    wersja = str(sdk.get("version") or "")
    assert PELNA_WERSJA.match(wersja), (
        "`global.json` podaje `%s` — pin ma być pełną trójką, nie wzorcem kanału; "
        "wzorzec rozwiązuje się w momencie instalacji i to jest cała usterka 6.D79"
        % wersja)
    polityka = sdk.get("rollForward")
    assert polityka in POLITYKI, (
        "`global.json` bez jawnej `rollForward` (albo z nieznaną: %r). Domyślna jest "
        "w pliku NIEWIDOCZNA, a niewidoczna polityka jest tym, przez co wzorzec "
        "kanału przetrwał." % polityka)


def test_the_pinned_major_matches_what_the_projects_target():
    """Warunek trzeci: numer główny pinu zgadza się z docelową platformą projektów."""
    major = tfm_major(target_framework(_read(os.path.join(ROOT, PROJECTS[0]))))
    wersja = str(_pin_sdk_lub_stop().get("version"))
    assert wersja.split(".")[0] == str(major), (
        "`global.json` pinuje SDK %s, a projekty celują w net%s.0 — `dotnet build` "
        "padnie na NETSDK1045, a komunikat nie wskaże tego pliku" % (wersja, major))


def test_every_workflow_installs_exactly_the_pinned_version():
    """Warunek czwarty: wszystkie miejsca podające wersję w workflowach są zgodne.

    Zgodne **z pinem**, nie tylko ze sobą: trzy workflowy uzgodnione ze sobą na
    wzorcu `10.0.x` byłyby zgodne i nadal niepinowane. `setup-dotnet` z jawnym
    `dotnet-version` IGNORUJE `global.json`, więc rozjazd między nimi znaczyłby, że
    CI instaluje jedno SDK, a `dotnet build` żąda drugiego.
    """
    wersja = str(_pin_sdk_lub_stop().get("version"))
    znalezione = {}
    for name in _workflows():
        for podana in setup_dotnet_versions(_read(os.path.join(WORKFLOWS, name))):
            znalezione.setdefault(podana, []).append(name)
    assert znalezione, "żaden workflow nie podaje `dotnet-version`"
    assert list(znalezione) == [wersja], (
        "workflowy podają wersje %s, a pin mówi %s" % (znalezione, wersja))


def test_the_pin_parser_does_not_pass_by_returning_nothing():
    """Kontrola negatywna na parser — WYKONANA na podstawionych plikach.

    Bez niej wszystkie cztery warunki wyżej przechodzą przez zwrócenie pustego
    zbioru: `pin_sdk()` dające `None` na wszystkim zamienia je w pętle po niczym.
    Tego wprost żąda pole „Skończone, gdy".
    """
    import tempfile
    global PIN
    prawdziwy = PIN
    try:
        with tempfile.TemporaryDirectory() as katalog:
            PIN = os.path.join(katalog, "global.json")
            assert pin_sdk() is None, "brak pliku ma dawać None, a nie pusty słownik"

            with open(PIN, "w", encoding="utf-8") as uchwyt:
                uchwyt.write('{"sdk": {"version": "10.0.x", "rollForward": "latestPatch"}}')
            assert pin_sdk()["version"] == "10.0.x", "parser nie czyta pola version"
            for wzorzec in ("10.0.x", "10.0.*", "10.0", "10"):
                assert not PELNA_WERSJA.match(wzorzec), (
                    "`%s` przeszło jako pełna trójka — bramka na wzorzec kanału "
                    "nie ma wtedy czego łapać" % wzorzec)
            assert PELNA_WERSJA.match("10.0.401"), "pełna trójka odrzucona"

            with open(PIN, "w", encoding="utf-8") as uchwyt:
                uchwyt.write('{"sdk": {"version": "10.0.401"}}')
            assert pin_sdk().get("rollForward") is None, (
                "brak `rollForward` musi być widoczny jako None, inaczej bramka "
                "na jawną politykę nie ma czego złapać")

            with open(PIN, "w", encoding="utf-8") as uchwyt:
                uchwyt.write('{"msbuild-sdks": {}}')
            assert pin_sdk() is None, "plik bez bloku `sdk` ma dawać None"
    finally:
        PIN = prawdziwy
    # I że po przywróceniu przyrząd znów widzi prawdziwy pin — bez tego wiersza
    # wyciek podstawienia uciszyłby wszystkie cztery warunki na resztę przebiegu.
    assert pin_sdk(), "po przywróceniu przyrząd nie widzi prawdziwego pinu"
    assert PELNA_WERSJA.match(str(pin_sdk()["version"])), (
        "prawdziwy `global.json` nie ma dziś pełnej trójki: %r" % pin_sdk())


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

#: Drugi argument `chk_expr_*`, czyli WYRAŻENIE idące do `eval`. Wnętrze napisu MUSI
#: dopuszczać `\"`, bo wyrażenia cytują zmienne w środku, a wzorzec `"[^"]*"` urwałby
#: się na pierwszym takim cudzysłowie (zmierzone przy 6.D81: dla siedmiu z dziesięciu
#: wywołań zwracał `[ \` albo samo `\`).
#:
#: **6.D98: wzorzec pyta o `chk_expr_*`, nie o `chk_*`.** Formy programowej nie ma
#: po co sprawdzać na cytowanie — nie idzie przez `eval`, więc spacja w ścieżce jest
#: dla niej zwykłym znakiem. Zawężenie wzorca ZŁAPAŁ próg niżej: po przemianowaniu
#: funkcji skan zobaczył zero wywołań i bramka padła, zamiast przejść nad pustką.
CHK_EXPR_CALL = re.compile(
    r'chk_expr_(?:required|optional)\s+"(?:[^"\\]|\\.)*"\s+"((?:[^"\\]|\\.)*)"')

#: Wywołanie formy PROGRAMOWEJ: nazwa, podpowiedź, a potem program i argumenty
#: podane jako osobne słowa. Łapany jest ogon po drugim napisie — to on ma być
#: tablicą, a nie napisem do ponownego sparsowania.
CHK_PROG_CALL = re.compile(
    r'chk_prog_(?:required|optional)\s+"(?:[^"\\]|\\.)*"\s+"(?:[^"\\]|\\.)*"([^\n]*)')

#: Polecenie zaczynające się od GOŁEJ zmiennej, czyli od ścieżki, która rozpadnie
#: się na spacji. `\"$X\" --version` jest w porządku, `$X --version` nie.
URUCHAMIA_ZMIENNA = re.compile(r'^\$[A-Za-z_][A-Za-z0-9_]*[/ ]')

#: Znaki, po których poznaje się WYRAŻENIE powłoki, a nie uruchomienie programu.
#: `[ "$A" -ge "$B" ]` ma nawias i operator; `"$DOTNET" --version` nie ma żadnego.
WYRAZENIE_POWLOKI = re.compile(r'(^|\s)(\[|\]|-ge|-eq|-lt|-gt|=|!=)(\s|$)')


def _doctor_sklejony():
    """Treść `doctor.sh` ze sklejonymi wierszami łamanymi odwrotnym ukośnikiem.

    Część wywołań `chk_*` jest rozbita na dwie albo trzy linie, a wzorzec liniowy
    widziałby wtedy sam nagłówek.
    """
    return open(DOCTOR, encoding="utf-8").read().replace("\\\n", " ")


def doctor_check_commands():
    """Wyrażenia z wywołań `chk_expr_*` w `doctor.sh`, wiersze sklejone."""
    return CHK_EXPR_CALL.findall(_doctor_sklejony())


def doctor_prog_calls():
    """Ogony wywołań `chk_prog_*`, czyli program z argumentami jako tablica."""
    return [ogon.strip() for ogon in CHK_PROG_CALL.findall(_doctor_sklejony())]


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



def _run_doctor(dotnet_version, home_version=None, podkatalog="bin"):
    """Uruchamia PRAWDZIWY `doctor.sh` z podstawionym `dotnet`, bez sieci i bez SDK.

    Dwie atrapy: jedna pod `DOTNET_BIN` (udaje SDK, które doctor ma sprawdzić),
    druga pod `$HOME/.dotnet/dotnet` (udaje SDK leżące na dysku poza `PATH`).
    `home_version=None` znaczy „w katalogu domowym nie ma nic".
    `podkatalog` pozwala położyć atrapę w katalogu o dowolnej NAZWIE — w tym takiej
    ze spacją, czego żąda 6.D81.

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

        fake_bin = os.path.join(tmp, podkatalog, "dotnet")
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


def test_doctor_reads_the_same_sdk_from_a_path_with_a_space_in_it():
    """Ścieżka SDK ze spacją daje TEN SAM wynik, co ścieżka bez spacji — 6.D81.

    **Skąd.** `chk_required` wykonuje swój drugi argument przez `eval`, czyli parsuje
    go DRUGI RAZ. Wiersz `"$DOTNET --version"` bez cudzysłowów wewnętrznych rozpadał
    ścieżkę ze spacją na dwa słowa. Zmierzone 10.09.2026, ta sama atrapa w dwóch
    katalogach:

        DOTNET_BIN=".../sdk with space/dotnet"  ->  BRAK  dotnet SDK
        DOTNET_BIN=".../sdk_no_space/dotnet"    ->  ok    dotnet SDK

    **Dlaczego to nie tylko fałszywy negatyw.** Kilkadziesiąt wierszy niżej
    `dotnet test` woła tę samą ścieżkę cytowaną poprawnie, więc pełny przebieg
    meldował brak SDK w sekcji środowiska i `ok` w sekcji testów — wewnętrzna
    sprzeczność JEDNEGO raportu, czytanego wedle `CLAUDE.md` §2 przed każdym zadaniem.

    Test porównuje dwa przebiegi ze sobą, a nie z wpisanym napisem: gdyby doctor
    przestał w ogóle wypisywać ten wiersz, oba byłyby puste i równe — więc obok stoi
    asercja na treść.
    """
    required = tfm_major(target_framework(open(
        os.path.join(ROOT, "src", "Sim", "Sim.csproj"), encoding="utf-8").read()))
    oczekiwany = "ok    dotnet SDK >= %d (jest 99)" % required

    ze_spacja = _run_doctor("99.1.2", podkatalog="sdk with space")
    bez_spacji = _run_doctor("99.1.2", podkatalog="sdk_no_space")

    assert oczekiwany in bez_spacji, (
        "kontrola: atrapa w katalogu BEZ spacji ma być widziana\n" + bez_spacji[:1200])
    assert oczekiwany in ze_spacja, (
        "ścieżka SDK ze spacją rozpadła się na spacji — w `eval` z `chk_*` albo "
        "w podstawieniu `$(...)`; doctor nie widzi wersji SDK, którego przed chwilą "
        "użył\n" + ze_spacja[:1200])
    # Komunikat MUSI zaczynać się zdaniem, a nie wypisem doctora: wypis zaczyna się
    # pustą linią, więc jednowierszowy raport zestawu pokazywałby `FAIL …:` i nic
    # więcej. Zmierzone przy kontroli negatywnej KN-1 tej pozycji.
    assert "BRAK  dotnet SDK" not in ze_spacja, (
        "doctor melduje BRAK SDK dla ścieżki ze spacją, choć atrapa odpowiada "
        "poprawnie — cytowanie w `chk_required` zniknęło:\n" + ze_spacja[:1200])

    # Wiersze o dotnecie muszą być IDENTYCZNE w obu przebiegach. Reszta wypisu może
    # się różnić (ścieżki katalogów tymczasowych), więc porównywane są tylko one.
    def wiersze(out):
        return [l for l in out.splitlines() if "dotnet SDK" in l]
    assert wiersze(ze_spacja) == wiersze(bez_spacji), (
        "wypis o SDK różni się między ścieżką ze spacją a bez:\n%s\n---\n%s"
        % ("\n".join(wiersze(ze_spacja)), "\n".join(wiersze(bez_spacji))))


def test_every_doctor_check_quotes_the_tool_path_it_runs():
    """Każde `chk_*` wołające narzędzie ze zmiennej cytuje je — 6.D81, klasa usterki.

    Poprawka wyżej zamyka JEDEN wiersz. Ta bramka zamyka rodzinę: `eval` parsuje
    swój argument drugi raz, więc każde `$ZMIENNA --coś` w napisie podanym do `chk_*`
    rozpadnie się na spacji tak samo. Wiersze Blendera i Godota były cytowane od
    początku i to one są wzorcem — bramka żąda go od wszystkich.
    """
    wolania = doctor_check_commands()
    # Kontrola przyrządu, i nie jest ozdobna: PIERWSZA wersja tego wzorca brała
    # `"[^"]*"` i zatrzymywała się na CUDZYSŁOWIU ESCAPOWANYM, więc dla siedmiu
    # z dziesięciu wywołań zwracała `[ \` albo samo `\`. Bramka przechodziła
    # wtedy trywialnie — nad dokładnie tą usterką, której pilnuje.
    assert len(wolania) >= 5, (
        "skan widzi %d wywołań `chk_expr_*` — wzorzec rozjechał się z treścią doctora"
        % len(wolania))
    for polecenie in wolania:
        assert polecenie.strip(), "puste polecenie — wzorzec urwał argument"
        assert not polecenie.strip().endswith("\\"), (
            "polecenie urwane na łamaniu wiersza: %r — sklejanie nie zadziałało"
            % polecenie)

    zle = [p for p in wolania if URUCHAMIA_ZMIENNA.match(p)]
    assert zle == [], (
        "wywołanie `chk_expr_*` uruchamia ścieżkę ze zmiennej BEZ cudzysłowów — "
        "`eval` parsuje ten napis drugi raz i rozbije ją na spacji: %s" % zle)


def test_doctor_uzywa_formy_tablicowej_do_uruchamiania_programow():
    """6.D98: program idzie tablicą i bez `eval`, wyrażenie idzie przez `eval`.

    Rozdzielenie jest po to, żeby przy nowym wywołaniu nie było CZEGO pamiętać:
    forma programowa nie parsuje swojego argumentu drugi raz, więc spacja w ścieżce
    jest dla niej zwykłym znakiem. Bramka pilnuje obu kierunków pomyłki — wyrażenia
    wstawionego do formy tablicowej i programu wstawionego do formy z `eval` — bo
    każdy z nich cofa dokładnie tę własność.
    """
    # Podłoga zeszła z sześciu na PIĘĆ 10.09.2026 przy 6.D112 i to nie jest
    # rozluźnienie bramki: `chk_prog_required "dotnet SDK" … "$DOTNET" --version`
    # wołało `--version` DRUGI raz w tym samym bloku, więc zostało zamienione na
    # formę wyrażeniową czytającą wynik już zapamiętany. Ubyło wywołanie programu,
    # nie ubyło używanie formy tablicowej — a tego pilnuje ta liczba. Wypis jest
    # identyczny co do bajtu, bo obie funkcje wypisują ten sam kształt wiersza.
    programowe = doctor_prog_calls()
    assert len(programowe) >= 5, (
        "skan widzi %d wywołań `chk_prog_*`, a zmierzone 10.09.2026 było pięć — "
        "albo forma zniknęła, albo wzorzec się rozjechał" % len(programowe))

    # ZMIERZONE KONTROLĄ NEGATYWNĄ, nie założone: forma tablicowa zdejmuje DRUGI
    # rozbiór (`eval`), ale nie zdejmuje PIERWSZEGO — podziału na słowa przy
    # rozwinięciu. `chk_prog_required "dotnet SDK" "…" $DOTNET --version` z atrapą
    # w katalogu `sdk with space` nadal daje `BRAK dotnet SDK`, a ta sama linia
    # z `"$DOTNET"` daje `ok`. Cudzysłowy są więc nadal potrzebne i bramka pyta
    # o nie także tutaj; 6.D98 zdejmuje jeden z dwóch rozbiorów, nie oba.
    bez_cudzyslowow = [p for p in programowe
                       if URUCHAMIA_ZMIENNA.match(p.split(" ", 1)[0] + " ")]
    assert bez_cudzyslowow == [], (
        "forma tablicowa uruchamia ścieżkę ze zmiennej BEZ cudzysłowów — podział "
        "na słowa przy rozwinięciu rozbije ją na spacji tak samo jak `eval`: %s"
        % bez_cudzyslowow)

    wyrazenia_w_tablicy = [p for p in programowe if WYRAZENIE_POWLOKI.search(p)]
    assert wyrazenia_w_tablicy == [], (
        "wyrażenie powłoki trafiło do formy TABLICOWEJ — `\"[\" \"$A\" -ge …` nie "
        "jest programem i ta forma go nie wykona: %s" % wyrazenia_w_tablicy)

    programy_w_eval = [w for w in doctor_check_commands()
                       if not WYRAZENIE_POWLOKI.search(w) and w.strip() != "false"]
    assert programy_w_eval == [], (
        "uruchomienie programu trafiło do formy z `eval` — wraca wtedy potrzeba "
        "pamiętania o cudzysłowach, którą 6.D98 zdejmuje: %s" % programy_w_eval)


def test_rozroznienie_form_dziala_na_wejsciu_syntetycznym():
    """Kontrola PRZYRZĄDU: `WYRAZENIE_POWLOKI` ma odróżniać, a nie zgadzać się zawsze.

    Cztery kształty, bo bramka wyżej pyta w obie strony: dwa prawdziwe wyrażenia
    i dwa prawdziwe uruchomienia. Bez tego „lista pusta" znaczyłoby tyle samo, co
    „wzorzec nie łapie niczego".
    """
    for wyrazenie in ('[ "$A" -ge "$B" ]', '[ $HOSTFXR_OK -eq 0 ]'):
        assert WYRAZENIE_POWLOKI.search(wyrazenie), wyrazenie
    for program in ('"$DOTNET" --version', '"$BLENDER_CMD" --background --python-expr pass'):
        assert not WYRAZENIE_POWLOKI.search(program), (
            "uruchomienie programu wzięte za wyrażenie powłoki — bramka wyżej "
            "zgłaszałaby wtedy poprawne wywołania: %r" % program)


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

    **ASERCJA PRZEKIEROWANA, NIE POLUZOWANA — 6.D57, 09.09.2026.** Poprzednia
    wersja żądała `"DOTNET_BIN=" in out and "bash doctor.sh" in out`, czyli
    **kodowała radę niepełną**. Zmierzone tym samym skryptem, Godot osiągalny:

        DOTNET_BIN=/root/.dotnet/dotnet   ->  ok dotnet SDK, ale WARN godot .NET hostfxr
        DOTNET_ROOT=/root/.dotnet + PATH  ->  ok dotnet SDK, ok godot .NET hostfxr

    Powód stoi w kontroli `hostfxr` w `doctor.sh`: `HOSTFXR_OK` bierze się
    z `DOTNET_ROOT` albo z **gołego** `command -v dotnet`, a nie z `$DOTNET_BIN`.
    Rada `DOTNET_BIN` zdejmowała więc jeden komunikat i zostawiała drugi — a ten
    drugi mówi o awarii, która zabija proces natychmiast (log: signal 11, powłoka:
    kod 134; zdanie o zawieszeniu zdjęte z `doctor.sh` przy 6.D24 — jedenaście
    wariantów w 6.D21 i 6.D24 nie odtworzyło go ani razu).

    Po przekierowaniu asercja sprawdza **więcej**, nie mniej: cztery rzeczy
    zamiast dwóch — że doctor szukał, że nazwał ZNALEZIONĄ ścieżkę (a nie radził
    ogólnie), że podał komplet `DOTNET_ROOT` **razem z** `PATH`, i że nie stawia
    gołego `DOTNET_BIN` jako polecenia do uruchomienia.
    """
    out = _run_doctor("8.0.130", home_version="99.1.2")
    assert "na dysku JEST nowsze SDK" in out, out[:1500]
    assert ".dotnet/dotnet" in out, (
        "podpowiedź nie nazywa ZNALEZIONEJ ścieżki, więc jest radą ogólną:\n"
        + out[:1500])
    assert "DOTNET_ROOT=" in out and "PATH=" in out, (
        "podpowiedź nie podaje kompletu DOTNET_ROOT + PATH, a samo DOTNET_BIN "
        "zostawia WARN godot .NET hostfxr (zmierzone):\n" + out[:1500])
    assert "uruchom: DOTNET_BIN=" not in out, (
        "podpowiedź stawia goły DOTNET_BIN jako polecenie do uruchomienia — to "
        "rada niepełna, patrz docstring:\n" + out[:1500])


def _bin_bez_dotnet(katalog):
    """Katalog `bin` z symlinkami do WSZYSTKIEGO z `PATH` poza `dotnet`.

    **PRZEPISANE 09.09.2026, a nie dopisane obok.** Poprzednia wersja pomocnika niżej
    zawężała `PATH` do `/usr/bin:/bin` i ZAKŁADAŁA, że w tych dwóch katalogach nie ma
    `dotnet`. Założenie było prawdziwe na starej puli runnerów i w kontenerze sesji,
    a **fałszywe** na runnerach dodanych 09.09.2026: tam `/usr/bin/dotnet` istnieje
    i jest SDK w wersji **8**. Doctor wchodził wtedy w gałąź „SDK za stare", a nie
    w gałąź „nie ma żadnego SDK", więc oba testy pary sprawdzały nie ten scenariusz,
    o którym mówią ich nazwy — i padły na runnerze, choć przechodziły lokalnie:

        FAIL test_doctor_bez_dotnet_w_PATH_NAZYWA_sdk_lezace_na_dysku
        FAIL test_doctor_bez_dotnet_w_PATH_i_bez_sdk_na_dysku_nadal_kaze_instalowac
          2057/2059 przeszło

    To ta sama rodzina usterek, którą 6.D57 tropiła w `doctor.sh`, tylko po stronie
    testu: **test zakładał środowisko, zamiast je zagwarantować.**

    **Dlaczego symlinki, a nie odsianie katalogów z `PATH`.** Pierwsza poprawka
    wyrzucała z `PATH` każdy katalog zawierający `dotnet` — i na maszynie, gdzie
    `dotnet` leży w `/usr/bin`, zabierała razem z nim `bash`, `git` i `python3`:

        FAIL test_doctor_bez_dotnet_w_PATH_NAZYWA_sdk_lezace_na_dysku:
          [Errno 2] No such file or directory: 'bash'

    Zmierzone na atrapie odtwarzającej warunek runnera. Katalog symlinków zdejmuje
    dokładnie jedną nazwę i zostawia wszystko inne osiągalne, więc doctor probuje
    ten sam zestaw narzędzi, co zwykle. Kolejność `PATH` jest zachowana — pierwszy
    katalog wygrywa, tak jak przy prawdziwym rozwiązywaniu nazw.
    """
    sandbox = os.path.join(katalog, "bin")
    os.makedirs(sandbox, exist_ok=True)
    for kat in os.environ.get("PATH", "").split(os.pathsep):
        if not kat or not os.path.isdir(kat):
            continue
        try:
            nazwy = os.listdir(kat)
        except OSError:
            continue
        for nazwa in nazwy:
            if nazwa == "dotnet":
                continue
            cel = os.path.join(sandbox, nazwa)
            if os.path.lexists(cel):
                continue
            try:
                os.symlink(os.path.join(kat, nazwa), cel)
            except OSError:
                pass
    return sandbox

def _run_doctor_bez_dotnet_w_path(home_version=None):
    """`doctor.sh` bez ŻADNEGO `dotnet` osiągalnego — scenariusz 6.D57.

    **To jest luka, przez którą usterka 6.D57 przeżyła**, i dlatego ta pomocnicza
    funkcja istnieje osobno od `_run_doctor`. Wszystkie cztery istniejące bramki
    podpowiedzi podstawiają `DOTNET_BIN` na atrapę, więc `$DOTNET --version`
    zawsze coś zwracało i `HAVE_SDK_MAJOR` nigdy nie było puste. Przypadek
    „w `PATH` nie ma nic" nie był sprawdzany przez nic — a szukanie SDK na dysku
    stało właśnie wewnątrz `if [ -n "$HAVE_SDK_MAJOR" ]`.

    `PATH` ustawiony na katalog symlinków bez `dotnet` (patrz `_bin_bez_dotnet`),
    `DOTNET_BIN` i `DOTNET_ROOT` zdjęte, `HOME` podstawiony na katalog tymczasowy.
    """
    import subprocess
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        home = os.path.join(tmp, "home")
        os.makedirs(home, exist_ok=True)
        if home_version is not None:
            sciezka = os.path.join(home, ".dotnet", "dotnet")
            os.makedirs(os.path.dirname(sciezka), exist_ok=True)
            with open(sciezka, "w", encoding="utf-8") as handle:
                handle.write("#!/bin/sh\n"
                             'if [ "$1" = "--version" ]; then echo "%s"; exit 0; fi\n'
                             "exit 1\n" % home_version)
            os.chmod(sciezka, 0o755)

        sciezka_bez_dotnet = _bin_bez_dotnet(tmp)
        # DOWÓD SCENARIUSZA, nie założenie. Bez tej asercji maszyna z `dotnet`
        # w miejscu, którego odsianie nie objęło, cicho zamieniłaby ten test
        # na test innej gałęzi `doctor.sh` — i tak właśnie padł on 09.09.2026.
        assert shutil.which("dotnet", path=sciezka_bez_dotnet) is None, (
            "po odsianiu nazwy `dotnet` nadal jest on osiągalny na "
            + repr(sciezka_bez_dotnet) + " — scenariusz bez dotnet w PATH nie "
            "został zagwarantowany, więc ten test nie mówi o tym, co ma w nazwie")

        env = dict(os.environ)
        env.pop("DOTNET_BIN", None)
        env.pop("DOTNET_ROOT", None)
        env.update(HOME=home, PATH=sciezka_bez_dotnet, LC_ALL="C")
        done = subprocess.run(["bash", DOCTOR, "--no-tests"], cwd=ROOT, env=env,
                              capture_output=True, text=True, timeout=120)
        return done.stdout + done.stderr


def test_doctor_bez_dotnet_w_PATH_NAZYWA_sdk_lezace_na_dysku():
    """Rdzeń 6.D57: „BRAK, zainstaluj" o SDK, które leży na dysku, to ślepota.

    **Zmierzone 08.09.2026 na kontenerze sesji, przed poprawką:**
    `/root/.dotnet/dotnet` zgłaszał `10.0.400`, a `doctor.sh` meldował
    `BRAK dotnet SDK -> zainstaluj .NET SDK 10.0+` i kończył kodem 1. Przyczyna
    była w kodzie: przejście po katalogach kandydatów stało wewnątrz
    `if [ -n "$HAVE_SDK_MAJOR" ]`, a ta zmienna bierze się z `$DOTNET --version` —
    bez `dotnet` w `PATH` była pusta, więc cały blok się nie wykonywał. Podpowiedź
    o katalogach działała WYŁĄCZNIE wtedy, gdy w `PATH` stało SDK za stare.

    Komentarz w `doctor.sh` opisywał tę usterkę od 04.09.2026 („brzmi jak brak,
    a jest ślepotą") — i mimo to poprawka objęła tylko przypadek SDK za starego.
    **Zdanie w prozie nie jest bramką**; ta jest.
    """
    out = _run_doctor_bez_dotnet_w_path(home_version="99.1.2")
    assert "BRAK  dotnet SDK" in out, out[:1500]
    assert "SDK JEST na dysku" in out, (
        "doctor melduje brak SDK, choć leży ono na dysku — to usterka 6.D57:\n"
        + out[:1500])
    assert ".dotnet/dotnet" in out, (
        "podpowiedź nie nazywa znalezionej ścieżki:\n" + out[:1500])
    assert "DOTNET_ROOT=" in out and "PATH=" in out, (
        "podpowiedź nie podaje kompletu DOTNET_ROOT + PATH:\n" + out[:1500])
    assert "zainstaluj .NET SDK" not in out, (
        "doctor nadal każe INSTALOWAĆ SDK, które ma na dysku:\n" + out[:1500])


def test_doctor_bez_dotnet_w_PATH_i_bez_sdk_na_dysku_nadal_kaze_instalowac():
    """Druga strona pary — bez niej bramka wyżej byłaby spełnialna zawsze.

    Podpowiedź „SDK jest na dysku" wypisana wtedy, gdy go tam nie ma, to ten sam
    błąd, tylko w drugą stronę. Pole „Skończone, gdy" pozycji 6.D57 żąda tej
    kontroli osobno: zachowanie przy SDK **naprawdę** nieobecnym zostaje bez zmian.
    """
    out = _run_doctor_bez_dotnet_w_path(home_version=None)
    assert "BRAK  dotnet SDK" in out, out[:1500]
    assert "zainstaluj .NET SDK" in out, (
        "przy braku SDK doctor przestał radzić instalację:\n" + out[:1500])
    assert "SDK JEST na dysku" not in out, (
        "doctor obiecuje SDK, którego na dysku nie ma:\n" + out[:1500])
    assert "na dysku JEST nowsze SDK" not in out, out[:1500]


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
DECISION_OPEN = 'if command -v "${DOTNET_BIN:-dotnet}" >/dev/null 2>&1; then'
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

#: 6.D60. Sonda `godot .NET hostfxr` w `doctor.sh`. Pięć zepsuć, po których Godot
#: pada kodem 134 w 0,19–0,35 s (6.D24, `reports/6d24-biblioteka-natywna.md` §5) —
#: i szósty wariant kontrolny, w którym nic nie jest zepsute.
#:
#: `None` znaczy „nic nie psuj". Drugi człon to biblioteka, trzeci to sposób:
#: `brak` — plik usunięty, `obc` — obcięty do 200 B, czyli z POPRAWNYM nagłówkiem
#: ELF. Ten drugi jest tu najważniejszy: to on przewraca każdy pomysł oparty
#: na nagłówku albo na obecności nazwy w katalogu.
ZEPSUCIA = (
    ("kontrola", None, None),
    ("hostfxr-brak", "hostfxr", "brak"),
    ("hostfxr-obc", "hostfxr", "obc"),
    ("coreclr-brak", "coreclr", "brak"),
    ("coreclr-obc", "coreclr", "obc"),
    ("hostpolicy-brak", "hostpolicy", "brak"),
)

#: Ścieżki, pod którymi `dotnet-install.sh` kładzie trzy biblioteki, z wersją
#: podstawioną na stałą — atrapa nie udaje żadnego prawdziwego SDK i nie potrzebuje
#: go na dysku. **To jest wybór, nie skrót:** job `tools` w CI .NET-a nie instaluje,
#: więc bramka wymagająca prawdziwej instalacji byłaby zielona tylko tam, gdzie SDK
#: akurat stoi — czyli mówiłaby o maszynie, a nie o sondzie.
UKLAD_ATRAPY = {
    "hostfxr": "host/fxr/10.0.0/libhostfxr.so",
    "hostpolicy": "shared/Microsoft.NETCore.App/10.0.0/libhostpolicy.so",
    "coreclr": "shared/Microsoft.NETCore.App/10.0.0/libcoreclr.so",
}


def _atrapa_dotnet_root(katalog, biblioteka=None, sposob=None):
    """Katalog o układzie SDK, w którym trzy pliki są PRAWDZIWYMI bibliotekami.

    Wzorcem jest skompilowany moduł `_ctypes` samego Pythona — plik, który na pewno
    istnieje wszędzie, gdzie ten zestaw w ogóle się uruchamia, i który `dlopen`
    naprawdę ładuje. Bez prawdziwej biblioteki wariant kontrolny nie odróżniałby
    sondy działającej od sondy odmawiającej zawsze.
    """
    import _ctypes
    import shutil

    wzor = _ctypes.__file__
    for nazwa, wzgledna in UKLAD_ATRAPY.items():
        cel = os.path.join(katalog, wzgledna)
        os.makedirs(os.path.dirname(cel), exist_ok=True)
        if nazwa == biblioteka and sposob == "brak":
            continue
        if nazwa == biblioteka and sposob == "obc":
            with open(wzor, "rb") as zrodlo, open(cel, "wb") as plik:
                plik.write(zrodlo.read(200))
            continue
        shutil.copy2(wzor, cel)
    return katalog


def _obecnosc_pliku_o_tej_nazwie(root):
    """DAWNA kontrola z `doctor.sh`, przepisana w Pythonie jeden do jednego.

    Stoi tu jako **przyrząd kontrolny**, nie jako kod produkcyjny: bez niej zdanie
    „nowa kontrola łapie więcej" byłoby twierdzeniem, a nie pomiarem wykonanym
    w tym samym przebiegu, na tych samych sześciu atrapach.
    """
    import glob as _glob

    return bool(_glob.glob(os.path.join(root, "host", "fxr", "*", "libhostfxr.so")))


def test_the_hostfxr_probe_refuses_every_one_of_the_five_measured_breakages():
    """Kontrola przechodzi TYLKO na atrapie kontrolnej — i to jest treść 6.D60."""
    import tempfile

    sys.path.insert(0, os.path.join(ROOT, "tools", "ci"))
    import dotnet_native_probe as SONDA

    werdykty = {}
    with tempfile.TemporaryDirectory() as tmp:
        for nazwa, biblioteka, sposob in ZEPSUCIA:
            root = _atrapa_dotnet_root(os.path.join(tmp, nazwa), biblioteka, sposob)
            werdykty[nazwa] = SONDA.powod_odmowy(root)

    assert werdykty["kontrola"] is None, (
        "sonda odmawia na atrapie, w której NIC nie jest zepsute — mierzy wtedy "
        f"samą siebie, nie instalację: {werdykty['kontrola']}")
    for nazwa, biblioteka, _ in ZEPSUCIA[1:]:
        powod = werdykty[nazwa]
        assert powod is not None, f"{nazwa}: sonda mówi ok przy zepsuciu, które wywraca silnik"
        assert biblioteka in powod, (
            f"{nazwa}: sonda odmawia, ale nie nazywa biblioteki `{biblioteka}`: {powod}")
    # Liczba jak w bramkach CI: pętla po pustym zbiorze wariantów przeszłaby zielona.
    assert len(werdykty) == 6, f"sprawdzono {len(werdykty)} wariantów zamiast sześciu"


def test_the_probe_catches_what_the_old_presence_check_let_through():
    """Kontrola negatywna: dawna kontrola musi na tych samych atrapach przepuścić 4 z 5.

    Bez tej pary poprzedni test byłby zielony także dla kontroli, która niczego nie
    poprawiła — a różnica 1/5 wobec 5/5 jest jedynym powodem, dla którego 6.D60
    w ogóle istnieje.
    """
    import tempfile

    sys.path.insert(0, os.path.join(ROOT, "tools", "ci"))
    import dotnet_native_probe as SONDA

    stara_przepuscila, nowa_przepuscila = [], []
    with tempfile.TemporaryDirectory() as tmp:
        for nazwa, biblioteka, sposob in ZEPSUCIA[1:]:
            root = _atrapa_dotnet_root(os.path.join(tmp, nazwa), biblioteka, sposob)
            if _obecnosc_pliku_o_tej_nazwie(root):
                stara_przepuscila.append(nazwa)
            if SONDA.powod_odmowy(root) is None:
                nowa_przepuscila.append(nazwa)

    assert len(stara_przepuscila) == 4, (
        "dawna kontrola nie przepuszcza już czterech z pięciu zepsuć — atrapa "
        f"przestała odtwarzać pomiar 6.D24: {stara_przepuscila}")
    assert nowa_przepuscila == [], (
        f"nowa sonda przepuszcza zepsucie: {nowa_przepuscila}")


def test_doctor_asks_the_probe_and_not_the_name_of_a_file():
    """`doctor.sh` woła sondę, a dawnego `find … -name` nie ma już w KODZIE.

    Czytany jest kod bez komentarzy — tym samym `without_comments`, co przy
    `RUNNER_TOOL_CACHE` i z tego samego powodu, TYLKO ODWRÓCONEGO. Tam bramka
    przechodziła na napisie stojącym w komentarzu; tu **padała** na nim: komentarz
    nad kontrolą CYTUJE dawną postać, żeby było widać, co i czemu zostało
    przepisane, a bramka czytająca prozę uznała cytat za nawrót. Zmierzone
    09.09.2026 przy wprowadzaniu tej bramki — pierwsza wersja zapaliła się na
    własnym commicie, na komentarzu, który sama kazała napisać.
    """
    doctor = _read(DOCTOR)
    kod = without_comments(doctor)
    assert "tools/ci/dotnet_native_probe.py" in kod, (
        "doctor nie woła sondy ładowania — kontrola `godot .NET hostfxr` wróciła "
        "do pytania o samą nazwę pliku")
    assert "-name 'libhostfxr.so'" not in kod, (
        "w KODZIE doctora stoi znów `find … -name`, czyli kontrola, która przy "
        "czterech z pięciu zepsuć mówiła `ok` (6.D24 §5)")
    # Bez tej pary powyższe przechodziłoby także wtedy, gdyby cytat z komentarza
    # zniknął razem z uzasadnieniem — a to jest jedyne miejsce, gdzie stoi powód.
    assert "-name 'libhostfxr.so'" in doctor, (
        "z komentarza nad kontrolą zniknął cytat dawnej postaci — zostaje kod bez "
        "zapisu, przed czym broni")




# --- 6.D96: pin niespełniony a „brak SDK" ----------------------------------------
#
# Zmierzone 10.09.2026 przy 6.D79, podstawianiem pinu i czytaniem KODU WYJŚCIA:
#
#     pin 10.0.401 (zainstalowane 10.0.401)  ->  kod 0
#     pin 10.0.402                            ->  kod 155
#
# Przy niespełnialnym pinie `dotnet --version` kończy błędem i wypisuje NA STDOUT
# listę zainstalowanych SDK. Doctor wypisywał wtedy NARAZ dwa zdania o tym samym
# SDK: `BRAK dotnet SDK -> zainstaluj` (kod niezerowy) i `ok dotnet SDK >= 10
# (jest 10)` — bo `--version | cut -d. -f1` nie widzi kodu wyjścia pierwszego członu
# potoku i brał `10` z pierwszego wiersza wypisanej listy. Jedno zdanie radziło
# zainstalować coś, co leży na dysku; drugie meldowało sprawdzenie zrobione na
# wyjściu polecenia, które padło.


def _atrapa_dotnet(sciezka, zainstalowane, pin):
    """Atrapa oddająca ZMIERZONE zachowanie `dotnet` przy pinie z `global.json`.

    `--list-sdks` wypisuje listę i kończy zerem ZAWSZE (pinu nie czyta).
    `--version` kończy zerem tylko wtedy, gdy pin jest na liście; inaczej wypisuje
    tę samą listę **na stdout** i kończy kodem 155 — dokładnie tak, jak zmierzono
    na kontenerze tej sesji. To ta druga część jest usterką: stdout wygląda jak
    odpowiedź, a nie jest.
    """
    # 6.D129: PRAWDZIWY nowy wiersz, nie ukośnik z literą `n`. Do 11.09.2026 stało
    # tu `\\n` w f-stringu, czyli dwa znaki tekstu — a `dotnet --list-sdks` kończy
    # każdą pozycję nowym wierszem. Wypis doctora niósł przez to
    # `na dysku: 10.0.401 [/atrapa/sdk]\\n` w JEDNYM wierszu, a przy dwóch SDK —
    # obie pozycje w jednym wierszu z jednym przedrostkiem. Atrapa, która nie
    # oddaje kształtu wyjścia, mierzy nie to narzędzie, co trzeba.
    lista = "".join(f"{w} [/atrapa/sdk]\n" for w in zainstalowane)
    spelniony = "0" if pin in zainstalowane else "1"
    with open(sciezka, "w", encoding="utf-8") as uchwyt:
        uchwyt.write(
            "#!/bin/sh\n"
            # 6.D112: atrapa LICZY swoje wywołania. Bez tego „jedno wywołanie"
            # dałoby się sprawdzić wyłącznie czytaniem `doctor.sh`, czyli tak samo,
            # jak sprawdzało się je przed tą pozycją — i tak samo bezskutecznie.
            'if [ -n "$LICZNIK" ]; then echo "$1" >> "$LICZNIK"; fi\n'
            'if [ "$1" = "--list-sdks" ]; then printf %s "$LISTA"; exit 0; fi\n'
            'if [ "$1" = "--version" ]; then\n'
            '  if [ "$SPELNIONY" = "0" ]; then echo "$PIN"; exit 0; fi\n'
            '  printf %s "$LISTA"; exit 155\n'
            "fi\n"
            "exit 1\n")
    os.chmod(sciezka, 0o755)
    return {"LISTA": lista, "SPELNIONY": spelniony, "PIN": pin}


def _doctor_z_pinem(pin, zainstalowane):
    """Wypis i kod wyjścia `doctor.sh` — bez dziennika wywołań atrapy."""
    wypis, kod, _wolania = _przebieg_doctora(pin, zainstalowane)
    return wypis, kod


def _przebieg_doctora(pin, zainstalowane):
    """`doctor.sh` na drzewie z podmienionym `global.json` i atrapą `dotnet`.

    Symlinki do wszystkiego poza `global.json`, bo doctor sprawdza kilkanaście
    ścieżek i przy braku którejkolwiek kończy przed interesującym nas blokiem.

    Trzeci element wyniku to **dziennik wywołań atrapy** — lista pierwszych
    argumentów, w kolejności. Dopisany w 6.D112: „blok pyta o wersję raz" jest
    zdaniem o PRZEBIEGU, a nie o treści skryptu, więc czytaniem `doctor.sh` go
    nie sprawdzisz.
    """
    import subprocess
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        drzewo = os.path.join(tmp, "repo")
        os.makedirs(drzewo)
        for nazwa in os.listdir(ROOT):
            if nazwa == "global.json":
                continue
            os.symlink(os.path.join(ROOT, nazwa), os.path.join(drzewo, nazwa))
        with open(os.path.join(drzewo, "global.json"), "w", encoding="utf-8") as uchwyt:
            json.dump({"sdk": {"version": pin, "rollForward": "latestPatch"}}, uchwyt)

        atrapa = os.path.join(tmp, "bin", "dotnet")
        os.makedirs(os.path.dirname(atrapa))
        zmienne = _atrapa_dotnet(atrapa, zainstalowane, pin)
        dom = os.path.join(tmp, "home")
        os.makedirs(dom)

        licznik = os.path.join(tmp, "wolania")
        srodowisko = dict(os.environ, DOTNET_BIN=atrapa, HOME=dom, LC_ALL="C",
                          LICZNIK=licznik, **zmienne)
        srodowisko.pop("DOTNET_ROOT", None)
        gotowe = subprocess.run(["bash", DOCTOR, "--no-tests"], cwd=drzewo,
                                env=srodowisko, capture_output=True, text=True,
                                timeout=180)
        wolania = []
        if os.path.isfile(licznik):
            with open(licznik, encoding="utf-8") as uchwyt:
                wolania = uchwyt.read().split()
        # Kod wyjścia obok wypisu, bo o WADZE zdania mówi tylko on: `doctor.sh`
        # kończy liczbą pozycji wymaganych do naprawienia. WARN zamiast BRAK dałby
        # ten sam napis o pinie i zero na wyjściu — czyli środowisko, w którym
        # `dotnet build` nie ruszy, zameldowane jako gotowe do pracy.
        return gotowe.stdout + gotowe.stderr, gotowe.returncode, wolania


def test_niespelniony_pin_nie_daje_dwoch_sprzecznych_zdan():
    """Sedno 6.D96: ani „BRAK dotnet SDK", ani „ok dotnet SDK >= N" — jedno zdanie.

    Obie połowy są tu potrzebne. Bez pierwszej wystarczyłoby zdjąć kontrolę wersji,
    żeby test przeszedł; bez drugiej — zostawić `ok` wypisywane z wyjścia polecenia,
    które padło, czyli usterkę, dla której ta pozycja powstała.
    """
    wypis, kod = _doctor_z_pinem("10.0.999", ["10.0.401"])

    assert "vs pin z global.json" in wypis, (
        "doctor nie nazwał pinu przy SDK, które go nie spełnia:\n" + wypis[-800:])
    assert "BRAK  dotnet SDK  ->" not in wypis, (
        "doctor nadal radzi zainstalować SDK, które leży na dysku:\n" + wypis[-800:])
    assert not re.search(r"ok\s+dotnet SDK >= \d", wypis), (
        "doctor melduje `ok dotnet SDK >= N` na podstawie wyjścia polecenia, które "
        "zakończyło się błędem:\n" + wypis[-800:])
    assert "na dysku: 10.0.401" in wypis, (
        "wypis nie pokazuje, CO leży na dysku — czytający nie wie, czy zmienić pin, "
        "czy doinstalować:\n" + wypis[-800:])
    assert kod > 0, (
        "doctor kończy zerem przy pinie, którego żadne SDK nie spełnia — a w tym "
        "stanie `dotnet build` też nie ruszy, więc zdanie o pinie musi być pozycją "
        "WYMAGANĄ, nie ostrzeżeniem")


def test_pin_spelniony_zostawia_wypis_bez_zmiany():
    """Kontrola przeciwna: przy pinie spełnionym wraca zwykła kontrola SDK.

    Bez niej „nie ma zdania o braku SDK" byłoby prawdą także dla doctora, który
    przestał tę kontrolę wypisywać w ogóle.
    """
    wypis, kod = _doctor_z_pinem("10.0.401", ["10.0.401"])

    assert re.search(r"ok\s+dotnet SDK\b", wypis), (
        "przy pinie spełnionym zniknęła zwykła kontrola SDK:\n" + wypis[-800:])
    assert re.search(r"ok\s+dotnet SDK >= \d", wypis), (
        "przy pinie spełnionym zniknęła kontrola wersji:\n" + wypis[-800:])
    assert "SDK SĄ na dysku, ale ŻADNE nie spełnia pinu" not in wypis, wypis[-800:]


def test_brak_jakiegokolwiek_sdk_nadal_kaze_instalowac():
    """Trzeci stan, którego pole „Skończone, gdy" żąda nie ruszyć.

    Atrapa odmawia OBU poleceniom, czyli `--list-sdks` też — wtedy nie ma czego
    pinować i jedyną prawdziwą radą jest instalacja. Gdyby rozróżnienie oparło się
    na treści stdout zamiast na kodzie wyjścia, ten przypadek zlałby się z poprzednim.
    """
    wypis, kod = _doctor_z_pinem("10.0.401", [])

    assert "BRAK  dotnet SDK  ->" in wypis, (
        "przy braku JAKIEGOKOLWIEK SDK doctor przestał kazać je zainstalować:\n"
        + wypis[-800:])
    assert "SDK SĄ na dysku, ale ŻADNE nie spełnia pinu" not in wypis, (
        "doctor mówi o niespełnionym pinie, choć żadnego SDK nie ma:\n" + wypis[-800:])


def test_liczba_wersji_nie_bierze_sie_z_polecenia_ktore_padlo():
    """`HAVE_SDK_MAJOR` liczone z `--version`, które SIĘ POWIODŁO, a nie z potoku.

    Potok `--version | cut` nie widzi kodu wyjścia pierwszego członu — to jest
    mechanizm usterki i on właśnie jest tu przybity, osobno od wypisu. Atrapa
    wypisuje przy porażce listę zaczynającą się od `10.`, więc `cut -d. -f1` dałby
    z niej `10` i kontrola `>= 10` przeszłaby jako `ok`.
    """
    zrodlo = _read(DOCTOR)
    assert 'HAVE_SDK_MAJOR="$("$DOTNET" --version 2>/dev/null | cut -d. -f1)"' not in zrodlo, (
        "liczba wersji znów bierze się z potoku, który nie widzi kodu wyjścia")
    # 6.D112 zmieniło KSZTAŁT tej gałęzi, nie jej własność: `--version` woła się raz
    # na cały blok, a kod wyjścia niesie zmienna. Asercja pyta więc o warunek na
    # ZAPAMIĘTANYM kodzie zamiast o dawny literał z podstawieniem polecenia.
    assert '[ "$DOTNET_WERSJA_KOD" -eq 0 ] && [ -n "$DOTNET_WERSJA" ]' in zrodlo, (
        "nie widać gałęzi liczącej wersję wyłącznie z udanego `--version`")

#: Trzy stany bloku SDK z 6.D96, każdy z wypisem OGRANICZONYM DO WIERSZY O SDK
#: i kodem wyjścia. Ograniczenie jest konieczne: pełny wypis `doctor.sh` niesie też
#: wiersze o Blenderze i Godocie, których obecność zależy od maszyny — zapadka na
#: całym wypisie byłaby czerwona w CI i zielona lokalnie, czyli nie mierzyłaby nic.
#: Wiersze niżej zależą wyłącznie od atrapy, więc są takie same wszędzie.
#:
#: Zapisane 10.09.2026 PRZED zmianą z 6.D112 i po niej NIE DRGNĘŁY — to jest właśnie
#: warunek odbioru tamtej pozycji, przybity, a nie sprawdzony raz ręcznie. Przetrwały
#: też 6.D128 (jedno wywołanie `--list-sdks` zamiast dwóch).
#:
#: **Jeden wiersz PRZELICZONY 11.09.2026 przy 6.D129, i to jest jedyna zmiana tej
#: zapadki od jej powstania.** Wiersz `na dysku:` stanu „pin niespełniony" brzmiał:
#:
#:     "        na dysku: 10.0.401 [/atrapa/sdk]\\n"
#:
#: — z literalnym ukośnikiem i literą `n` NA KOŃCU, bo atrapa budowała listę jako
#: `f"{w} [/atrapa/sdk]\\n"`, czyli dwa znaki tekstu zamiast nowego wiersza. Zapadka
#: zapisywała ten wypis takim, jaki był, i dlatego była zielona; usterka siedziała
#: w atrapie, nie w doctorze. Dziś brzmi:
#:
#:     "        na dysku: 10.0.401 [/atrapa/sdk]"
#:
#: Różnica widać dopiero przy DWÓCH SDK i wtedy jest duża: przed zmianą obie pozycje
#: stały w JEDNYM wierszu z JEDNYM przedrostkiem `na dysku:`, dziś każda ma swój —
#: tak, jak wypisuje je `dotnet --list-sdks`. Pilnuje tego
#: `test_lista_sdk_ma_tyle_wierszy_ile_jest_sdk`.
STANY_SDK = {
    "pin niespełniony": {
        "pin": "10.0.999",
        "zainstalowane": ["10.0.401"],
        "kod": 1,
        "wiersze": [
            "  BRAK  dotnet SDK vs pin z global.json (10.0.999)  -> SDK SĄ na dysku, "
            "ale ŻADNE nie spełnia pinu 10.0.999 z global.json; `dotnet --version` "
            "kończy błędem — zmień pin albo doinstaluj tę wersję, NIE instaluj SDK "
            "od nowa",
            "        na dysku: 10.0.401 [/atrapa/sdk]",
        ],
    },
    "pin spełniony": {
        "pin": "10.0.401",
        "zainstalowane": ["10.0.401"],
        "kod": 0,
        "wiersze": [
            "  ok    dotnet SDK",
            "  ok    dotnet SDK >= 10 (jest 10)",
            "  ok    dotnet SDK == pin z global.json (10.0.401)",
        ],
    },
    "brak jakiegokolwiek SDK": {
        "pin": "10.0.401",
        "zainstalowane": [],
        "kod": 1,
        "wiersze": [
            "  BRAK  dotnet SDK  -> zainstaluj .NET SDK 10.0+ "
            "(https://dotnet.microsoft.com/download)",
        ],
    },
}

#: Ile razy blok SDK ma zapytać `dotnet --version` w JEDNYM przebiegu.
WOLAN_WERSJI = 1

#: Ile razy blok SDK ma zapytać `dotnet --list-sdks` w JEDNYM przebiegu — 6.D128.
#:
#: **Zmierzone 11.09.2026 PRZED zmianą, tym samym dziennikiem atrapy:** pin
#: niespełniony **2**, pin spełniony **1**, brak SDK **1**. Dwójka brała się stąd,
#: że o listę pytało dwóch rozmówców — sonda `SDK_NA_LISCIE` i wypis „na dysku:"
#: w gałęzi niespełnionego pinu — a wynik drugiego szedł WPROST na stdout, więc
#: nie było czego zapamiętać.
#:
#: Osobna stała od `WOLAN_WERSJI`, bo to dwa różne pytania i cała 6.D96 na tej
#: różnicy stoi: `--list-sdks` pyta „czy jakiekolwiek SDK jest", `--version` —
#: „czy któreś spełnia pin". Jedna stała na oba znaczyłaby, że da się je policzyć
#: razem, a pole „Poza zakresem" 6.D128 wyklucza nawet ich połączenie.
WOLAN_LISTY_SDK = 1


def _wiersze_o_sdk(wypis):
    """Wiersze wypisu dotyczące SDK — te, które ta pozycja mogła ruszyć."""
    return [w for w in wypis.splitlines()
            if "dotnet SDK" in w or w.startswith("        na dysku: ")]


def test_blok_sdk_pyta_o_wersje_dokladnie_raz():
    """6.D112: jedno wywołanie `--version` na przebieg, we WSZYSTKICH trzech stanach.

    **Zmierzone przed zmianą atrapą liczącą swoje wywołania:** pin niespełniony
    **2**, pin spełniony **4**, brak SDK **3**. Wpis kolejki mówił o trzech — trzy
    to liczba MIEJSC w kodzie, a nie wywołań w przebiegu, i ani w jednym z trzech
    stanów nie wychodziła.

    Liczy się dziennik atrapy, a nie treść skryptu: „blok pyta raz" jest zdaniem
    o PRZEBIEGU. Czytanie `doctor.sh` odpowiada na inne pytanie i odpowiadało na nie
    zielono także wtedy, gdy wywołań było cztery.
    """
    for nazwa, stan in STANY_SDK.items():
        _wypis, _kod, wolania = _przebieg_doctora(stan["pin"], stan["zainstalowane"])
        ile = wolania.count("--version")
        assert ile == WOLAN_WERSJI, (
            f"stan „{nazwa}”: blok SDK pyta o wersję {ile} raz(y) zamiast "
            f"{WOLAN_WERSJI}; dziennik atrapy: {wolania}")


def test_blok_sdk_pyta_o_liste_dokladnie_raz():
    """6.D128: jedno wywołanie `--list-sdks` na przebieg, we WSZYSTKICH trzech stanach.

    Liczy się dziennik atrapy, a nie treść skryptu — ten sam powód, co przy
    `--version` w 6.D112: „blok pyta raz" jest zdaniem o PRZEBIEGU, a czytanie
    `doctor.sh` odpowiada na inne pytanie i odpowiadało na nie zielono także wtedy,
    gdy wywołań było dwa.
    """
    for nazwa, stan in STANY_SDK.items():
        _wypis, _kod, wolania = _przebieg_doctora(stan["pin"], stan["zainstalowane"])
        ile = wolania.count("--list-sdks")
        assert ile == WOLAN_LISTY_SDK, (
            f"stan „{nazwa}”: blok SDK pyta o listę SDK {ile} raz(y) zamiast "
            f"{WOLAN_LISTY_SDK}; dziennik atrapy: {wolania}")

    # Kontrola przyrządu: dziennik naprawdę widzi OBA pytania osobno. Bez tego
    # licznik zliczający jedno w miejsce drugiego dałby te same jedynki.
    _w, _k, wolania = _przebieg_doctora("10.0.999", ["10.0.401"])
    assert "--list-sdks" in wolania and "--version" in wolania, (
        "dziennik atrapy nie rozdziela `--list-sdks` od `--version`: %s" % wolania)
    assert wolania[0] == "--list-sdks", (
        "sonda listy przestała być pierwsza — kolejność jest tu treścią, bo "
        "`PIN_NIESPELNIONY` czyta wynik obu: %s" % wolania)


def test_wypis_listy_sdk_konczy_sie_nowym_wierszem():
    """`printf '%s\\n'`, nie gołe podstawienie — bo `$(...)` obcina nowe wiersze.

    **Docstring i nazwa PRZEPISANE 11.09.2026 przy 6.D129, bo pierwsza wersja — moja,
    z 6.D128 — twierdziła nieprawdę.** Mówiła, że bez końcowego nowego wiersza „`sed`
    pokazałby listę krótszą o ostatnią pozycję, co przy JEDNYM SDK znaczy listę
    pustą". Zmierzone: GNU `sed` **wypisuje** ostatni wiersz niepełny —
    `printf '%s' "$V" | sed 's/^/X: /'` daje `X: a` i `X: b`, tyle że bez zakończenia.

    Prawdziwy skutek jest mniejszy i wciąż wart tej linijki: brakujące zakończenie
    zjada **pusty wiersz** oddzielający listę od następnej sekcji doctora. Zmierzone
    na dwóch SDK: `…[/atrapa/sdk]\\nWymagane dopiero…` zamiast
    `…[/atrapa/sdk]\\n\\nWymagane dopiero…`.

    Sprawdzane na POWŁOCE, a nie na atrapie — i to było prawdą **do 6.D129**: atrapa
    wypisywała listę w jednym wierszu (ukośnik zamiast nowego wiersza), więc na niej
    ta różnica nie zachodziła. Od 6.D129 zachodzi i mierzy ją
    `test_lista_sdk_ma_tyle_wierszy_ile_jest_sdk`; ten test zostaje przy powłoce, bo
    pyta o sam konstrukt, nie o wypis doctora.
    """
    import subprocess

    def przez(polecenie):
        wynik = subprocess.run(
            ["bash", "-c", 'V="$(printf \'a\\nb\\n\')"\n' + polecenie],
            capture_output=True, text=True)
        assert wynik.returncode == 0, wynik.stderr
        return wynik.stdout

    dzisiaj = przez("""printf '%s\\n' "$V" | sed 's/^/        na dysku: /'""")
    assert dzisiaj == "        na dysku: a\n        na dysku: b\n", repr(dzisiaj)

    # Kontrola negatywna wbudowana, z POPRAWIONYM opisem (6.D129): bez `printf`
    # ostatni wiersz WYCHODZI, tylko bez zakończenia — GNU `sed` wypisuje wiersz
    # niepełny. Różnicą jest ostatni ZNAK, nie ostatni wiersz, i asercja niżej
    # pyta dokładnie o to, żeby dawne, nieprawdziwe zdanie nie wróciło.
    urwane = przez("""printf '%s' "$V" | sed 's/^/        na dysku: /'""")
    assert urwane == "        na dysku: a\n        na dysku: b", repr(urwane)
    assert dzisiaj == urwane + "\n", (
        "różnicą między obiema formami miał być ostatni ZNAK, a jest coś innego: "
        "%r wobec %r" % (urwane, dzisiaj))

    # I że `doctor.sh` używa tej pierwszej formy, a nie drugiej.
    zrodlo = _read(DOCTOR)
    assert """printf '%s\\n' "$SDK_LISTA" | sed""" in zrodlo, (
        "wypis listy SDK nie idzie przez `printf '%s\\n'` — zniknie pusty wiersz "
        "oddzielający listę od następnej sekcji doctora")
    assert '"$DOTNET" --list-sdks 2>/dev/null | sed' not in zrodlo, (
        "wypis listy SDK znów woła `dotnet` drugi raz zamiast czytać `SDK_LISTA`")


def test_lista_sdk_ma_tyle_wierszy_ile_jest_sdk():
    """6.D129: atrapa kończy pozycję NOWYM WIERSZEM, tak jak `dotnet --list-sdks`.

    **Różnicy nie widać przy jednym SDK i to jest cała pułapka.** Do 11.09.2026
    atrapa budowała listę jako `f"{w} [/atrapa/sdk]\\n"` — dwa znaki tekstu zamiast
    nowego wiersza — więc wypis niósł `na dysku: 10.0.401 [/atrapa/sdk]\\n` i przy
    jednym SDK wyglądał **prawie** dobrze. Przy dwóch obie pozycje stały w JEDNYM
    wierszu z JEDNYM przedrostkiem, czego żaden stan zapadki nie pokazywał, bo
    wszystkie trzy mają najwyżej jedno SDK.

    Ten test pyta więc o DWA, i to jest jedyne miejsce w module, gdzie kształt
    wyjścia atrapy jest w ogóle sprawdzalny.
    """
    wypis, _kod, _wolania = _przebieg_doctora("10.0.999", ["10.0.401", "9.0.100"])
    na_dysku = [w for w in wypis.splitlines() if w.startswith("        na dysku: ")]

    assert na_dysku == [
        "        na dysku: 10.0.401 [/atrapa/sdk]",
        "        na dysku: 9.0.100 [/atrapa/sdk]",
    ], ("lista SDK nie ma po jednym wierszu na pozycję — tak wygląda wypis atrapy "
        "z ukośnikiem zamiast nowego wiersza: %s" % na_dysku)

    assert not any("\\n" in w for w in na_dysku), (
        "wiersz listy niesie literalny ukośnik z literą `n`: %s" % na_dysku)

    # Kontrola przyrządu: przy JEDNYM SDK wiersz jest jeden — czyli licznik nie
    # zwraca dwójki z niczego, a stan zapadki „pin niespełniony" nadal go opisuje.
    jeden, _k, _w = _przebieg_doctora("10.0.999", ["10.0.401"])
    assert [w for w in jeden.splitlines() if w.startswith("        na dysku: ")] == [
        "        na dysku: 10.0.401 [/atrapa/sdk]"], jeden

    # I że sama atrapa buduje listę z PRAWDZIWEGO nowego wiersza — bez tego
    # asercje wyżej byłyby spełnialne także przez zmianę w `doctor.sh`, a pole
    # „Poza zakresem" tej pozycji wyklucza zmianę zachowania doctora.
    import inspect
    zrodlo = inspect.getsource(_atrapa_dotnet)
    assert 'f"{w} [/atrapa/sdk]\\n"' in zrodlo, (
        "atrapa nie składa pozycji listy z nowym wierszem")
    assert 'f"{w} [/atrapa/sdk]\\\\n"' not in zrodlo, (
        "ukośnik z literą `n` wrócił do atrapy")


def test_wypis_trzech_stanow_nie_drgnal():
    """Druga połowa warunku odbioru 6.D112: wypis identyczny co do bajtu.

    Bez tej bramki „jedno wywołanie" dałoby się osiągnąć, zmieniając przy okazji
    treść zdań — a pole „Poza zakresem" wyklucza to wprost. Kod wyjścia stoi obok
    wypisu, bo o WADZE zdania mówi tylko on.
    """
    for nazwa, stan in STANY_SDK.items():
        wypis, kod, _wolania = _przebieg_doctora(stan["pin"], stan["zainstalowane"])
        assert _wiersze_o_sdk(wypis) == stan["wiersze"], (
            f"stan „{nazwa}”: wypis o SDK zmienił się wobec zapisanego "
            f"10.09.2026:\n{_wiersze_o_sdk(wypis)}")
        assert kod == stan["kod"], (nazwa, kod, stan["kod"])


# 6.D25: uruchomienie tego pliku WPROST idzie ta sama droga, co caly zestaw —
# z licznikiem asercji i z odmowa przy zerze testow. Bez tej gałęzi `python3
# tools/tests/<modul>.py` konczyl sie kodem 0, nie wykonawszy ani jednego testu.

def _run_decision_bez_path(tmp_path, sdk_na_dysku):
    """Uruchamia gałąź decyzyjną z PUSTYM `PATH` i zadanym `SDK_NA_DYSKU`.

    **Po co osobny pomocnik, skoro `_run_decision` już jest.** Tamten zawsze podaje
    `DOTNET_BIN` wskazujący na atrapę, więc sonda `command -v` zawsze się udaje —
    i gałąź „nie ma czym uruchomić" nie zachodzi tam ANI RAZU. Ta usterka (6.D252)
    żyła dokładnie w tej gałęzi, której tamten pomocnik nie umie osiągnąć.
    """
    import subprocess
    import stat

    if sdk_na_dysku:
        shim = os.path.join(tmp_path, "sdk-na-dysku")
        with open(shim, "w", encoding="utf-8") as handle:
            handle.write(
                "#!/bin/sh\n"
                "if [ \"$1\" = test ]; then\n"
                "  echo 'Passed!  - Failed: 0, Passed: 7, Total: 7'\n"
                "  exit 0\n"
                "fi\n"
                "echo '10.0.401'\n")
        os.chmod(shim, os.stat(shim).st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    else:
        shim = ""

    script = os.path.join(tmp_path, "branch-bez-path.sh")
    with open(script, "w", encoding="utf-8") as handle:
        handle.write(
            # `PATH` ZOSTAJE prawdziwy, a nieosiągalna jest sama NAZWA binarki.
            # Pierwsza wersja tego pomocnika zerowała `PATH` i to był błąd zmierzony,
            # nie teoretyczny: bez `PATH` znikają `grep`, `cut` i `tail`, których
            # doctor używa do odczytania liczby testów z logu, więc wypisywał
            # `ok    / przeszło` — puste liczby. Test mierzyłby wtedy brak coreutils,
            # a nie gałąź decyzyjną.
            'DOTNET_BIN="dotnet-nie-ma-takiej-binarki"\n'
            'REQUIRED_TFM=""\n'
            'HAVE_SDK_MAJOR=""\n'
            f'SDK_NA_DYSKU="{shim}"\n'
            "required_bad=0\n"
            f'TMPDIR="{tmp_path}"\n'
            + _decision_branch()
            + "\necho \"required_bad=$required_bad\"\n")

    done = subprocess.run(["bash", script], cwd=ROOT, capture_output=True,
                          text=True, timeout=300)
    return done.stdout + done.stderr


def test_doctor_uruchamia_testy_z_SDK_POZA_PATH_zamiast_meldowac_brak():
    """SDK poza `PATH`, ale ZNALEZIONE na dysku, ma uruchomić testy — 6.D252.

    <b>Konfiguracja, DLA KTÓREJ ta poprawka powstała.</b> Do 17.09.2026 gałąź pytała
    `command -v "${DOTNET_BIN:-dotnet}"`, czyli o obecność w `PATH`, i przy pustym
    `PATH` wypisywała „pomijam — brak dotnet" — mimo że `SDK_NA_DYSKU` niosło działającą
    ścieżkę, którą doctor wypisuje cztery wiersze wyżej we własnej podpowiedzi.
    Jeden przebieg przeczył wtedy sam sobie.
    """
    import tempfile

    with tempfile.TemporaryDirectory() as tmp_path:
        output = _run_decision_bez_path(tmp_path, sdk_na_dysku=True)

    assert "pomijam — brak dotnet" not in output, (
        "doctor melduje brak `dotnet`, choć SDK na dysku zostało znalezione i jego "
        "ścieżka stoi w podpowiedzi tego samego przebiegu — to jest fałszywy brak, "
        "który czyta się jak poprawne zatrzymanie z §8, a jest pominięciem połowy "
        "pętli weryfikacji z §5:\n" + output)
    assert "7/7 przeszło" in output, (
        "doctor nie uruchomił testów rdzenia SDK znalezionym na dysku:\n" + output)
    assert "required_bad=0" in output, (
        "uruchomione i zaliczone testy policzyły się jako błąd wymagany:\n" + output)


def test_doctor_NADAL_melduje_brak_gdy_nie_ma_ANI_JEDNEGO_dotneta():
    """Kontrola negatywna: poprawka nie zamienia sondy w atrapę mówiącą zawsze „jest".

    Bez tego testu poprzedni przeszedłby także wtedy, gdyby gałąź „brak dotnet"
    została usunięta w ogóle — a wtedy doctor na maszynie bez SDK próbowałby
    uruchomić pusty napis i mówił o niezaliczonych testach zamiast o braku narzędzia.
    """
    import tempfile

    with tempfile.TemporaryDirectory() as tmp_path:
        output = _run_decision_bez_path(tmp_path, sdk_na_dysku=False)

    assert "pomijam — brak dotnet" in output, (
        "na maszynie bez ŻADNEGO `dotnet` doctor przestał meldować brak — sonda "
        "zamieniła się w atrapę, która zawsze mówi „jest”:\n" + output)
    assert "nie przechodzi" not in output, (
        "doctor mówi o niezaliczonych testach, choć nie miał czym ich uruchomić — "
        "to wysyła czytającego w kod symulacji zamiast w środowisko:\n" + output)

if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))
