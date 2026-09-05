#!/usr/bin/env python3
"""Dokumentacja nie opisuje runnera, którego nie ma w `.github/workflows/`.

**Skąd się wzięło.** `CLAUDE.md` §9 mówi, że od 02.09.2026 całe CI chodzi na maszynie
właściciela, a od 05.09.2026 na komplecie etykiet puli `woogitsu`
(`[self-hosted, Linux, X64, wsl2, woogitsu]`). Poprzednia wersja tego akapitu mówiła
„na gołej etykiecie `self-hosted`, a etykietę `wsl2` zdjęto 02.08.2026" — pierwsza
połowa to już nieprawda, druga jest faktem historycznym i dlatego stoi niżej, przy
wyjaśnieniu, po co ta bramka w ogóle istnieje. Same workflowy to spełniają
i pilnuje tego `test_ci_workflows.py`. Zmierzone 04.09.2026 na `main` (e982bc0):
`docs/17-visual-regression.md` nadal opisywał job jako `ubuntu-latest` i skrypt
bramki jako uruchamiany „na GitHub-hosted runnerze", a `docs/20-art-direction.md`
w trzech miejscach mówił „self-hosted WSL2" — czyli dokładnie tę etykietę, po
której joby wisiały. Żaden z tych zapisów nie wywracał niczego, bo bramki CI
oglądają YAML, a nie prozę.

To nie jest kosmetyka. Dokument jest jedyną instrukcją dla człowieka, który odpala
robotę ręcznie albo dopisuje nowy workflow: „job `ubuntu-latest`" każe mu napisać
`runs-on: ubuntu-latest` (minut na koncie nie ma, job nie wystartuje), a „na
self-hosted WSL2" każe mu dopisać etykietę, której żaden zarejestrowany runner nie
nosi (job wisi w `queued`, a §9 mówi wprost: „Nie uznawaj `queued` za weryfikację").
Oba błędy wyglądają w dokumencie dokładnie tak samo jak prawda.

**Prawda jest czytana z workflowów, nie z drugiej listy w teście.** Gdyby ten moduł
nosił własny spis dozwolonych etykiet, byłby trzecią kopią tej samej wiedzy (§9,
YAML, test) i rozjechałby się tak samo, jak rozjechały się te dwa dokumenty. Zbiór
dozwolonych etykiet powstaje z `runs-on` sparsowanego YAML-a.

**Zdania historyczne przechodzą, i to jest wymóg, nie ustępstwo.** Konwencja tego
projektu (§9: „jest tu przepisana, a nie dopisana obok") każe dokumentowi zapisać,
co mówiła jego poprzednia wersja, a datowanemu pomiarowi — zachować warunki, w
jakich powstał. Bramka, która tego nie odróżnia, każe kłamać albo usuwać historię.
Dlatego pomijanie idzie **z granulacją akapitu**, a nie wiersza: marker
(„poprzednia wersja tego punktu mówiła…", „Zmierzone 31.08.2026…") prawie nigdy
nie stoi w tym samym wierszu co nazwa runnera. W tabelce markdown akapitem jest
cała tabela; to świadome, bo wiersz tabeli sam z siebie nie ma miejsca na zdanie
o historii.
"""
import os
import re

import yaml

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
WORKFLOWS = os.path.join(ROOT, ".github", "workflows")
DOCS = os.path.join(ROOT, "docs")
REPORTS = os.path.join(ROOT, "reports")
README = os.path.join(ROOT, "README.md")

#: Markery, po których akapit jest opisem przeszłości albo cytatem z pomiaru,
#: a nie deklaracją stanu bieżącego. Pomiar jest na tej liście świadomie: warunki
#: pomiaru z konkretnej daty są faktem historycznym i przepisanie ich na dzisiejszy
#: runner sfałszowałoby pomiar, zamiast poprawić dokument.
HISTORICAL_MARKERS = (
    "poprzedni",          # „poprzednia wersja tego punktu mówiła…"
    "przepisan",          # „jest tu przepisana, a nie dopisana obok"
    "to już nieprawda",
    "historyczn",
    "zdjęto",
    "kiedyś",
    "wcześniej mówi",
    "do 02.09.2026",      # data przeniesienia CI na maszynę właściciela
    "zmierzone",          # cytat z pomiaru — warunków pomiaru się nie przepisuje
    "zmierzono",
)

#: Nazwy runnerów GitHub-hosted rozpoznawane po KSZTAŁCIE (`system-latest`,
#: `system-wersja`), a nie po spisie. Kształt wystarcza, bo o tym, czy taka nazwa
#: jest dziś prawdą, decyduje `allowed_labels()` przeczytane z workflowów.
#:
#: Rocznik (`[0-9]{4}`) doszedł 05.09.2026, razem z przepisaniem `github_hosted_in_use`
#: na ten wzorzec. Obrazy Windowsa nazywają się `windows-2022` i `windows-2019`, a
#: `[0-9]{1,2}` łapało z tego samo `20` i wywracało się na `\b` przed `22` — czyli
#: żadna z tych dwóch nazw nie była rozpoznawana ani w prozie, ani (od dziś) w `runs-on`.
#: Zmierzone na kontroli negatywnej `{"self-hosted", "wsl2", "windows-2022"}`, która
#: przed tą poprawką przechodziła jako „to nie jest maszyna GitHuba".
HOSTED_NAME = re.compile(
    r"\b(?:ubuntu|windows|macos)-(?:latest|[0-9]{2}\.[0-9]{2}|[0-9]{4}|[0-9]{1,2})\b",
    re.I)

#: „GitHub-hosted runner" jako klasa maszyny.
#:
#: Lookaroundy `(?<![\w/-])` i `(?![\w-])` odsiewają **identyfikator**, w którym ten
#: napis jest tylko członem. Nie jest to ostrożność, tylko naprawa zmierzonego
#: fałszywego trafienia: po włączeniu `reports/` do bramki (05.09.2026) sam `\b`
#: łapał nazwę gałęzi `chore/github-hosted-actions` w rejestrze skasowanych gałęzi
#: (`reports/branch-audit.md`, wiersze 108 i 218) i raportował ją jako twierdzenie
#: o runnerze. Nazwa gałęzi z 08.2026 jest faktem historycznym o repozytorium, a nie
#: zdaniem o tym, gdzie dziś chodzą joby — i przepisać jej się nie da, bo z niej
#: odtwarza się `git branch <nazwa> <sha>`.
GITHUB_HOSTED = re.compile(r"(?<![\w/-])github[-\s]hosted(?![\w-])", re.I)

#: Miejsca, po których w prozie stoi lista etykiet: `self-hosted …` i `runs-on …`.
LABEL_ANCHOR = re.compile(r"\bself-hosted\b|\bruns-on\b", re.I)

#: Kolejna etykieta w takiej liście: do trzech znaków rozdzielających (spacja,
#: przecinek, ukośnik, plus, backtick, nawias, dwukropek) i token etykiety.
NEXT_LABEL = re.compile(r"[`\s,/+\[\]:]{0,3}([A-Za-z][A-Za-z0-9_.-]*)")


def _read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def workflow_files():
    """Pliki workflow, po nazwie — źródło prawdy o runnerach."""
    return sorted(os.path.join(WORKFLOWS, name) for name in os.listdir(WORKFLOWS)
                  if name.endswith((".yml", ".yaml")))


def runner_labels(job):
    """Etykiety `runs-on` joba, niezależnie od formy zapisu — albo `None`.

    Te same trzy formy, które przyjmuje GitHub: napis, lista i mapa
    (`group:`/`labels:`). Regex po tekście widziałby wyłącznie pierwszą, a wtedy
    zbiór dozwolonych etykiet wyszedłby pusty i **każdy** zapis w dokumencie byłby
    dryfem — bramka krzyczałaby na wszystko, czyli na nic.
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


def allowed_labels():
    """Zbiór etykiet, na których CI naprawdę dziś chodzi. Małymi literami."""
    found = set()
    for path in workflow_files():
        document = yaml.safe_load(_read(path)) or {}
        for job in (document.get("jobs") or {}).values():
            for label in runner_labels(job) or []:
                found.add(label.lower())
    return found


def github_hosted_in_use(allowed):
    """Czy którykolwiek job chodzi na maszynie GitHuba, a nie na własnej.

    Rozstrzyga KSZTAŁT nazwy (`HOSTED_NAME`: `ubuntu-latest`, `windows-2022`,
    `macos-14`), a nie to, czy etykieta jest różna od `self-hosted`. Poprzednia
    wersja pytała o to drugie i była prawdziwa tylko dopóty, dopóki selektor był
    gołym `self-hosted`. Od 05.09.2026 komplet z §9 to pięć etykiet
    (`Linux`, `X64`, `wsl2`, `woogitsu` obok `self-hosted`) — przy tamtym warunku
    każda z tych czterech ogłaszała „jakiś job chodzi na maszynie GitHuba"
    i bramka przestawała łapać zapis „GitHub-hosted runner" w prozie, czyli cichła
    dokładnie tam, gdzie ma bronić.
    """
    return any(HOSTED_NAME.fullmatch(label) for label in allowed)


def paragraphs(text):
    """`(numer pierwszego wiersza, [wiersze])` dla akapitów rozdzielonych pustym.

    Akapit, nie wiersz, bo marker historyczny stoi zwykle w innym wierszu niż
    nazwa runnera — patrz docstring modułu.
    """
    blocks, current, first = [], [], 1
    for number, line in enumerate(text.splitlines(), start=1):
        if line.strip():
            if not current:
                first = number
            current.append(line)
        elif current:
            blocks.append((first, current))
            current = []
    if current:
        blocks.append((first, current))
    return blocks


def is_historical(lines):
    """Czy akapit jest oznaczony jako opis przeszłości albo cytat z pomiaru."""
    joined = " ".join(lines).lower()
    return any(marker in joined for marker in HISTORICAL_MARKERS)


def _looks_like_a_label(token):
    """Czy token wygląda na etykietę runnera, a nie na zwykłe słowo prozy.

    Po `self-hosted` w polskim zdaniu stoi „runnerze", „maszynie", „sprzęcie" —
    słowa pisane małymi literami i bez cyfr. Etykiety wyglądają inaczej: `WSL2`,
    `wsl2`, `GPU`, `X64`, `ubuntu-22.04`. Bez tego rozróżnienia bramka uznałaby za
    etykietę pierwsze napotkane słowo i wywracała się na zdaniu poprawnym.
    """
    if len(token) > 32:
        return False
    return any(char.isdigit() for char in token) or token != token.lower()


def extra_labels(line):
    """Etykiety dopisane w prozie po `self-hosted`/`runs-on`, małymi literami."""
    found = []
    for anchor in LABEL_ANCHOR.finditer(line):
        rest = line[anchor.end():]
        while True:
            match = NEXT_LABEL.match(rest)
            if not match:
                break
            # Kropka i dywiz są w klasie tokenu (`ubuntu-22.04`), ale na końcu są
            # interpunkcją zdania — bez tego komunikat mówiłby o etykiecie `wsl2.`.
            token = match.group(1).rstrip(".-")
            if not token or not _looks_like_a_label(token):
                break
            found.append(token.lower())
            rest = rest[match.end():]
    return found


def claims_in_line(line, allowed):
    """Powody, dla których TEN wiersz opisuje runnera nieistniejącego w CI."""
    reasons = []
    for match in HOSTED_NAME.finditer(line):
        if match.group(0).lower() not in allowed:
            reasons.append(f"runner `{match.group(0)}`, a workflowy używają "
                           f"{sorted(allowed)}")
    if GITHUB_HOSTED.search(line) and not github_hosted_in_use(allowed):
        reasons.append("„GitHub-hosted runner\", a żaden job nie chodzi na maszynie "
                       f"GitHuba — workflowy używają {sorted(allowed)}")
    for label in extra_labels(line):
        if label not in allowed:
            reasons.append(f"etykieta `{label}` dopisana do runnera, a żaden job jej "
                           f"nie nosi — workflowy używają {sorted(allowed)}")
    return reasons


def documents():
    """Pliki objęte bramką: `docs/*.md`, `reports/*.md` i `README.md`.

    **Dlaczego `reports/` doszło 05.09.2026.** Ten sam dryf, który ta bramka wycięła
    z `docs/`, siedział przez trzy dni w `reports/` — bo nic tam nie patrzyło.
    Zmierzone na `9f4ae98`: pięć raportów opisywało runnera, którego nie ma
    (`T-400-first-run.md` dwa razy, `T-310-physics.md`, `T-311-braking.md`,
    `L1_A-geometry.md`, `m7-ground-truth-verification.md`), a `T-310-physics.md` §7
    robił to **z odsyłaczem do `CLAUDE.md` §9**, który od 02.09.2026 mówi coś
    dokładnie przeciwnego. Odsyłacz do dokumentu, który zaprzecza zdaniu, przy którym
    stoi, jest gorszy niż brak odsyłacza: wygląda na sprawdzony.

    **Dlaczego to nie kłóci się z datowanym pomiarem.** Raport z etapu 1 ma prawo
    opisywać maszynę z etapu 1 — pod warunkiem że mówi to wprost. Pomijanie idzie
    z granulacją akapitu i `HISTORICAL_MARKERS` zawiera „zmierzone"/„zmierzono", więc
    zdanie „Zmierzone 01.09.2026 na GitHub-hosted `ubuntu-latest`, ~32 s" przechodzi,
    a „job chodzi na `ubuntu-latest`" nie. To jest dokładnie ta granica, o którą
    chodzi: nie wolno przeliczać cytatu, wolno wymagać, żeby cytat był oznaczony.

    **Czego to NIE obejmuje i dlaczego nie da się objąć tak samo tanio.** Bramka
    porównuje prozę z **jednym** źródłem prawdy sparsowanym maszynowo — etykietami
    `runs-on` z YAML-a. Rodzina „nieaktualna liczba w prozie raportu" nie ma jednego
    takiego źródła: `reports/` cytuje wyjścia poleceń, bloki kodu sprzed poprawki
    i liczby z przebiegów, których nie da się odróżnić od twierdzeń o stanie
    bieżącym bez czytania zdania. Bramka, która by je przeliczała zbiorczo, psułaby
    datowane pomiary — powód rozpisany w `tools/tests/test_report_hygiene.py`.
    """
    found = sorted(os.path.join(DOCS, name) for name in os.listdir(DOCS)
                   if name.endswith(".md"))
    found += sorted(os.path.join(REPORTS, name) for name in os.listdir(REPORTS)
                    if name.endswith(".md"))
    if os.path.exists(README):
        found.append(README)
    return found


def drift_in_text(text, allowed, name):
    """Dryf w jednym tekście jako lista `"plik:wiersz: powód"`."""
    drift = []
    for first, lines in paragraphs(text):
        if is_historical(lines):
            continue
        for offset, line in enumerate(lines):
            for reason in claims_in_line(line, allowed):
                drift.append(f"{name}:{first + offset}: {reason}")
    return drift


def scan(paths, allowed):
    """`(lista dryfów, liczba przejrzanych plików)`."""
    drift = []
    for path in paths:
        drift += drift_in_text(_read(path), allowed, os.path.relpath(path, ROOT))
    return drift, len(paths)


def test_allowed_labels_come_from_the_parsed_workflows():
    """Bez tego testu cała bramka mogłaby stać na pustym zbiorze prawdy.

    Puste `allowed` daje dwa fałszywe wyniki naraz: każda nazwa runnera w prozie
    staje się dryfem, a `github_hosted_in_use` zwraca False i przepuszcza zapis
    „GitHub-hosted". Dlatego zbiór musi być niepusty i zawierać etykietę z §9.
    """
    allowed = allowed_labels()
    assert allowed, "zbiór dozwolonych etykiet jest pusty — YAML nie jest czytany"
    assert "self-hosted" in allowed, allowed
    assert not github_hosted_in_use(allowed), (
        f"jakiś job chodzi na maszynie GitHuba: {sorted(allowed)}")
    assert len(workflow_files()) >= 7, workflow_files()

    # Kontrola do `github_hosted_in_use` po zmianie z 05.09.2026: rozstrzyga kształt
    # nazwy, nie „etykieta inna niż self-hosted". Bez pierwszej asercji komplet z §9
    # ogłaszałby maszynę GitHuba (tak robiła poprzednia wersja), a bez pozostałych
    # trzech funkcja mogłaby zwracać stałe False i nikt by tego nie zobaczył.
    assert not github_hosted_in_use({"self-hosted", "linux", "x64", "wsl2", "woogitsu"})
    assert not github_hosted_in_use({"self-hosted"})
    assert github_hosted_in_use({"ubuntu-latest"})
    assert github_hosted_in_use({"self-hosted", "wsl2", "windows-2022"}), (
        "mieszanka self-hosted z maszyną GitHuba musi się liczyć jako maszyna GitHuba")

    # Kontrola parsera: trzy formy `runs-on` i job bez `runs-on`.
    assert runner_labels({"runs-on": "self-hosted"}) == ["self-hosted"]
    assert runner_labels({"runs-on": ["self-hosted", "wsl2"]}) == ["self-hosted", "wsl2"]
    assert runner_labels({"runs-on": {"group": "own", "labels": "wsl2"}}) == [
        "wsl2", "group:own"]
    assert runner_labels({"steps": []}) is None


def test_no_document_states_a_runner_that_no_workflow_uses():
    """Główna bramka: proza w `docs/`, `reports/` i `README.md` wobec workflowów."""
    allowed = allowed_labels()
    drift, checked = scan(documents(), allowed)
    assert not drift, ("dokumenty opisują runnera, którego nie ma w CI: "
                       + "; ".join(drift))
    # Liczba jak w bramkach CI: pętla, która nie znalazła ani jednego dokumentu,
    # przeszłaby pusta i zielona — a to jest awaria bramki, nie brak dryfu. Próg
    # podniesiony z 20 na 60, gdy doszło `reports/`: samych raportów jest 48, więc
    # próg 20 przeszedłby również wtedy, gdyby cały katalog wypadł z pętli.
    assert checked >= 60, f"przejrzano tylko {checked} dokumentów — pętla ich nie widzi"
    reports = [p for p in documents() if os.path.dirname(p) == REPORTS]
    assert len(reports) >= 40, (
        f"w pętli jest tylko {len(reports)} raportów — `reports/` wypadło z bramki")


def test_the_detector_catches_the_drifts_that_were_measured_on_main():
    """Kontrola pozytywna na dokładnie tych zapisach, które były na `main`.

    Bez niej test wyżej przechodziłby także wtedy, gdyby `claims_in_line` nie
    wykrywało niczego — zielone „brak dryfu" znaczyłoby „brak detekcji".
    """
    allowed = {"self-hosted"}
    assert claims_in_line("| `visual-regression.yml` | job `ubuntu-latest` |", allowed)
    assert claims_in_line("`tools/ci/visual_smoke.sh` na `ubuntu-latest`:", allowed)
    assert claims_in_line("pięć testów pipeline'u na GitHub-hosted runnerze", allowed)
    assert claims_in_line("dopóki ten job nie wykona się na self-hosted WSL2", allowed)
    assert claims_in_line("na docelowym self-hosted WSL2/GPU:", allowed)
    assert claims_in_line("    runs-on: [self-hosted, wsl2]", allowed)

    # I że to naprawdę porównanie z workflowami, a nie stała lista zakazanych słów:
    # gdyby CI wróciło na maszynę GitHuba, te same zdania byłyby prawdą.
    assert not claims_in_line("job `ubuntu-latest`", {"ubuntu-latest"})
    assert not claims_in_line("na GitHub-hosted runnerze", {"ubuntu-latest"})
    assert not claims_in_line("na self-hosted WSL2", {"self-hosted", "wsl2"})

    # NAZWA GAŁĘZI NIE JEST TWIERDZENIEM O RUNNERZE — kontrola negatywna na dokładnie
    # tym fałszywym trafieniu, które wyszło przy włączaniu `reports/` do bramki.
    # Bez lookaroundów w `GITHUB_HOSTED` oba wiersze niżej były raportowane jako dryf.
    assert not claims_in_line(
        "| `chore/github-hosted-actions` | #40 | `2fa599de` |", allowed)
    assert not claims_in_line("    chore/github-hosted-actions \\", allowed)
    # …ale sama klasa maszyny w prozie nadal musi być łapana, inaczej lookaroundy
    # zjadłyby detekcję razem z fałszywym trafieniem.
    assert claims_in_line("job chodzi na GitHub-hosted runnerze", allowed)
    assert claims_in_line("(GitHub-hosted `ubuntu-latest`, ~32 s)", allowed)


def test_a_sentence_marked_as_history_is_not_treated_as_drift():
    """Kontrola negatywna wymagana konwencją §9: historia zostaje w dokumencie.

    Ten sam napis `ubuntu-latest` raz jest dryfem, a raz poprawną treścią —
    rozstrzyga marker w akapicie, nie sam wiersz. Dlatego marker stoi tu w INNYM
    wierszu niż nazwa runnera: przy granulacji wiersza ten test byłby czerwony.
    """
    allowed = {"self-hosted"}

    history = ("Poprzednia wersja tego punktu mówiła, że standardem jest\n"
               "`ubuntu-latest`; to już nieprawda i dlatego jest tu przepisana.\n")
    assert drift_in_text(history, allowed, "<test>") == []

    measured = ("Zmierzone 31.08.2026, jeszcze przed zdjęciem etykiety, na\n"
                "self-hosted WSL2: pięć klatek w 12,4 s.\n")
    assert drift_in_text(measured, allowed, "<test>") == []

    # A ten sam napis BEZ markera musi zostać dryfem — inaczej pomijanie zjadałoby
    # wszystko i bramka byłaby dekoracją.
    plain = ("Wstęp bez znaczenia.\n\n"
             "Job chodzi na `ubuntu-latest`, artefakty także przy fail.\n")
    drift = drift_in_text(plain, allowed, "<test>")
    assert len(drift) == 1, drift
    assert drift[0].startswith("<test>:3: "), drift


def test_polish_prose_after_self_hosted_is_not_mistaken_for_a_label():
    """Kontrola negatywna do wykrywania etykiet dopisanych po `self-hosted`.

    Bez rozróżnienia „etykieta kontra słowo" bramka wywracałaby się na zdaniach
    poprawnych — a takie są dziś w `README.md` i `docs/23-environment.md`, i to
    właśnie one opisują stan zgodny z §9.
    """
    allowed = {"self-hosted"}
    for line in ("Na self-hosted runnerze `actions/checkout` robi `git clean -ffdx`.",
                 "**Wszystkie chodzą na self-hosted runnerze**, na gołej etykiecie "
                 "`self-hosted`, po wyczerpaniu minut.",
                 "na rzeczywistym rendererze i sprzęcie self-hosted.",
                 "    runs-on: self-hosted"):
        assert not claims_in_line(line, allowed), line
    assert extra_labels("na self-hosted maszynie właściciela") == []
    assert extra_labels("na self-hosted WSL2/GPU") == ["wsl2", "gpu"]
    # Kropka na końcu zdania nie jest częścią etykiety, a dywiz i kropka w środku są.
    assert extra_labels("a bramka na self-hosted WSL2.") == ["wsl2"]
    assert extra_labels("na self-hosted ubuntu-22.04 dzisiaj") == ["ubuntu-22.04"]
