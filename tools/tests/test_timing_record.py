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
import re
import subprocess
import sys
import tempfile

import yaml

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools", "ci"))

import test_all as TA  # noqa: E402
import test_suite_runtime_budget as B  # noqa: E402
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



#: Logi jobów `tools`, z których 6.D135 przepisało wpisy `POMIARY` RĘCZNIE. Leżą w drzewie
#: **dosłowne i NIESPAKOWANE**; przycinanie ich do „wierszy, które są potrzebne" byłoby
#: kuracją materiału — bramka sprawdzałaby wtedy wybór człowieka, a nie log.
#:
#: **Niespakowane wyszło z pomiaru i z bramki, a pierwsza wersja tej pozycji miała `.gz`.**
#: Powody są dwa i oba są zmierzone, nie wywnioskowane. Pierwszy: plik binarny odrzuca
#: `test_conflict_markers.test_skan_czyta_CALE_drzewo_a_nie_pusty_zbior`, który żąda, żeby
#: nieczytelne jako UTF-8 były DECYZJĄ, a nie cichym pominięciem — sześć `.gz` wywróciło
#: siedem jobów CI. Drugi: `.gz` w repozytorium jest DROŻSZY, bo git i tak pakuje, a blobu
#: już spakowanego nie skompresuje ani nie zdeltuje. Zmierzone na tych samych sześciu
#: logach, dwa puste repozytoria po `git gc`: **234 858 B** tekstem wobec **428 699 B**
#: gzipem, czyli tekst jest 1,83x tańszy. Oszczędność z `gzip -9` istnieje wyłącznie
#: w katalogu roboczym — a płaci się w historii.
#: Pochodzenie i sposób pobrania: `tests/data/ci-logs/README.md`.
LOGI_CI = os.path.join(ROOT, "tests", "data", "ci-logs")

#: Które pola znikają, gdy z logu zniknie wiersz niosący dane pole. Tabela jest wypisana,
#: a nie policzona, bo to ONA jest twierdzeniem: `modulow` i `testow` stoją w JEDNYM wierszu
#: `RAZEM`, więc nie da się zgubić jednego bez drugiego, a zdanie „na czym" pada razem
#: z każdą ze swoich czterech składowych.
POCIAGA_ZA_SOBA = {
    "data": {"data"},
    "sekundy": {"sekundy"},
    "modulow": {"modulow", "testow", "na_czym"},
    "testow": {"modulow", "testow", "na_czym"},
    "cpu_na_sciane": {"cpu_na_sciane", "na_czym"},
    "runner": {"runner", "maszyna"},
    "job": {"job", "na_czym"},
    "pr": {"pr", "na_czym"},
}

#: Ile wpisów runnera niesie coś PONAD to, co wychodzi z logu. **Dziś ZERO, i ten
#: akapit jest przepisany, a nie dopisany obok (6.D163).** Do 13.09.2026 stał tu jeden:
#: wpis najwolniejszego przebiegu miał doklejone „, NAJWYŻSZY na runnerze”. Ogon został
#: **zdjęty**, bo nie był zdaniem o przebiegu, tylko o LIŚCIE, i powtarzał to, co
#: `MEASURED_MAX_WALL_S` z niej liczy — czyli był drugą kopią liczby, rodzina 6.B28.
#: Zejście do zera bylo tu przewidziane jako POPRAWKA, nie jako awaria, i tak się stało.
#: Gdy liczba znowu urośnie, poprawką jest zdjęcie dopisku, nie rozluźnienie porównania:
#: mówi ona, ile listy wciąż utrzymuje się ręcznie.
WPISOW_Z_DOPISKIEM = 0

# --- 6.D164: ile materialu niesie artefakt czasu i jak daleko wstecz -----------------

#: Nazwa artefaktu, który `python-tests.yml` wynosi z każdego przebiegu (6.D93).
NAZWA_ARTEFAKTU_CZASU = "czas-zestawu"

#: **Zmierzone 13.09.2026 na ŻYWYCH artefaktach, przez API repozytorium.**
#:
#:   przebieg 1213 (11.09.2026 12:36, PR #524)  artefakt utworzony 11.09 12:42:31,
#:                                              wygasa 11.10 12:42:28, `expired: false`
#:   przebieg 1315 (13.09.2026 03:07)           artefakt utworzony 13.09 03:16:26,
#:                                              wygasa 13.10 03:16:24, 2123 bajty
#:
#: Różnica między utworzeniem a wygaśnięciem wynosi w obu wypadkach **30 dni** co do
#: dwóch sekund, czyli dokładnie tyle, ile deklaruje krok w workflowie. Deklaracja
#: i zachowanie API zgadzają się, więc retencję wolno czytać z drzewa — i test niżej
#: to robi, zamiast nosić ją tu drugi raz z ręki.
RETENCJA_ZMIERZONA_DNI = 30

#: **Zasięg wstecz, zmierzony dwiema datami, a nie oszacowany.** Krok wynoszący
#: artefakt wszedł do workflowa **10.09.2026** (`9784e3b`, 6.D93) — wcześniej nie ma
#: czego szukać, bo nic się nie wynosiło. Najstarszy artefakt, który dziś jeszcze żyje,
#: jest z 11.09; najnowszy z 13.09. **Nic nie wygasło i wygasnąć nie mogło**, bo
#: wynoszenie trwa krócej niż retencja: pierwsze wygaśnięcie wypada 10.10.2026.
DZIEN_PIERWSZEGO_WYNOSZENIA = "2026-09-10"

#: **Ile przebiegów niesie dziś żywy artefakt: CO NAJMNIEJ 104.** Przebieg o numerze
#: 1213 ma artefakt żywy, a ostatni przebieg tego workflowa ma numer 1316 — czyli
#: 104 przebiegi w przedziale domkniętym, każdy z krokiem `if: always()`.
#:
#: **Dlaczego „co najmniej", a nie dokładnie — i to jest granica wypisana, nie
#: przemilczana.** Wynoszenie zaczęło się 10.09, a numer pierwszego przebiegu po tej
#: dacie nie został odczytany: API tego serwera nie filtruje przebiegów po dacie ani
#: po commicie, więc jedyną drogą byłoby przejście listy 1316 przebiegów, z których
#: każdy niesie pełną treść commita. Liczba dokładna kosztowałaby więc wielokrotnie
#: więcej niż odpowiedź, której pozycja potrzebuje, a dolna granica na nią wystarcza.
PRZEBIEGOW_Z_ARTEFAKTEM_CO_NAJMNIEJ = 104


def retencja_z_workflowa():
    """Krok wynoszący artefakt czasu i deklarowana retencja — czytane z YAML-a.

    Czytane, a nie wpisane obok: dwie kopie tej liczby rozjechałyby się przy pierwszej
    edycji jednej z nich (6.B28), a od niej zależy CAŁY zasięg wstecz tego materiału.
    """
    with open(WORKFLOW, encoding="utf-8") as uchwyt:
        plan = yaml.safe_load(uchwyt)
    for job in plan["jobs"].values():
        for krok in job.get("steps", []):
            z = krok.get("with") or {}
            if z.get("name") == NAZWA_ARTEFAKTU_CZASU:
                return krok, z.get("retention-days")
    return None, None


def test_artefakt_czasu_jest_OKNEM_RUCHOMYM_a_nie_zapisem_trwalym():
    """ROZSTRZYGNIĘCIE 6.D164: artefakt jest materiałem na trend, ale RUCHOMY.

    **Czy jest materiału więcej niż jeden przebieg — tak, i to dużo.** Co najmniej
    **104** przebiegi niosą dziś żywy artefakt, każdy z czasami PER MODUŁ, `commit`,
    `runner`, `workflow` i podziałem `odkryte`/`wykonane` — czyli z tym wszystkim,
    czego z logu wyjąć się nie da. Materiał jest, i to nie ślad jednego przebiegu.

    **Ale jest RUCHOMY, i to jest cała odpowiedź.** Retencja wynosi 30 dni, zmierzona
    na dwóch żywych artefaktach co do dwóch sekund i zadeklarowana w workflowie. Dziś
    nic nie wygasło, bo wynoszenie trwa od 10.09.2026, czyli krócej niż retencja —
    pierwsze wygaśnięcie wypada 10.10.2026. **Od tego dnia okno przestaje rosnąć
    i zaczyna się przesuwać.**

    **Co z tego wynika dla `POMIARY`** — pytanie z pola „Skończone, gdy". Lista zostaje
    i artefakt jej nie zastąpi, bo zapisuje co innego: `POMIARY` jest **trwałe**
    (wpis z 05.09.2026 stoi w niej do dziś i będzie stał), artefakt **wygasa**. Trend
    zbudowany na artefaktach nigdy nie sięgnie dalej niż trzydzieści dni wstecz, więc
    to, co ma przeżyć dłużej, musi być **zżęte do drzewa przed wygaśnięciem** — tak
    jak sześć logów w `tests/data/ci-logs/`, które właśnie dlatego tam leżą.

    Czytnika artefaktów ta pozycja NIE pisze: pole „Poza zakresem" zabrania zmiany
    kroku CI i dopisywania wpisów automatem, a pytanie brzmiało, czy materiał jest.
    """
    krok, retencja = retencja_z_workflowa()
    assert krok is not None, (
        "w `python-tests.yml` nie ma kroku wynoszącego artefakt %r — bez niego cały "
        "ten pomiar opisuje mechanizm, którego nie ma" % NAZWA_ARTEFAKTU_CZASU)
    assert "upload-artifact" in krok.get("uses", ""), krok
    assert retencja == RETENCJA_ZMIERZONA_DNI, (
        "workflow deklaruje %r dni retencji, a na żywych artefaktach zmierzono %d — "
        "zasięg wstecz materiału zmienił się i rozstrzygnięcie 6.D164 trzeba "
        "przeliczyć" % (retencja, RETENCJA_ZMIERZONA_DNI))

    # Krok ma stac pod `if: always()`, bo inaczej przebieg CZERWONY — czyli ten,
    # ktorego czasy sa najbardziej potrzebne — nie zostawia po sobie nic (6.D93).
    assert str(krok.get("if", "")).strip() == "always()", (
        "krok wynoszący artefakt stracił `if: always()`, więc przebieg czerwony nie "
        "zostawi czasów: %r" % krok.get("if"))

    # I ARYTMETYKA OKNA, wykonana, a nie opowiedziana: wynoszenie trwa KROCEJ niz
    # retencja, wiec dzis nic nie wygaslo. Gdy ta nierownosc przestanie zachodzic,
    # zdanie o tym w docstringu wyzej staje sie nieprawdziwe.
    import datetime
    poczatek = datetime.date.fromisoformat(DZIEN_PIERWSZEGO_WYNOSZENIA)
    dni_wynoszenia = (datetime.date.today() - poczatek).days
    assert dni_wynoszenia <= RETENCJA_ZMIERZONA_DNI, (
        "wynoszenie trwa %d dni przy retencji %d — najstarsze artefakty ZACZĘŁY "
        "wygasać, więc zdanie o tym, że nic nie wygasło, przestało być prawdziwe "
        "i docstring trzeba przepisać" % (dni_wynoszenia, RETENCJA_ZMIERZONA_DNI))

    assert PRZEBIEGOW_Z_ARTEFAKTEM_CO_NAJMNIEJ > 1, (
        "dolna granica zeszła do jednego przebiegu — wtedy artefakt naprawdę jest "
        "śladem jednego przebiegu i odpowiedź tej pozycji się odwraca")


#: Numer PR-a w zdaniu „na czym" wpisu `POMIARY`. Po nim wiąże się wpis z jego logiem.
NUMER_PR = re.compile(r"PR #(\d+)")


def _log(numer_pr):
    with open(os.path.join(LOGI_CI, f"tools-pr{numer_pr}.log"),
              encoding="utf-8") as uchwyt:
        return uchwyt.read()


def _logi_w_drzewie():
    return {int(n[len("tools-pr"):-len(".log")])
            for n in os.listdir(LOGI_CI) if n.endswith(".log")}


def _wpisy_runnera_po_pr():
    po_pr = {}
    for wpis in B.POMIARY_RUNNERA:
        numer = NUMER_PR.search(wpis[4])
        assert numer, (
            "wpis runnera bez numeru PR w zdaniu „na czym” — nie da się go związać "
            f"z żadnym logiem, więc nikt nigdy nie sprawdzi, skąd wzięte są jego liczby: "
            f"{wpis!r}")
        po_pr[int(numer.group(1))] = wpis
    return po_pr


def _bez_wiersza(tekst, pole):
    """Ten sam log bez wierszy niosących dane pole — wejście syntetyczne z prawdziwego materiału."""
    wiersze = tekst.splitlines()
    if pole == "data":
        # Stempel czasu nosi KAŻDY wiersz, więc „usunięcie wiersza” znaczy tu zdjęcie stempli.
        return "\n".join(TR._STEMPEL.sub("", w.lstrip("﻿"), count=1) for w in wiersze)
    wzor = TR.WZORY_LOGU[pole]
    return "\n".join(w for w in wiersze if not wzor.match(TR._bez_ozdob(w)))


def test_kazde_pole_wpisu_runnera_wychodzi_z_logu_i_zgadza_sie_z_lista():
    """Odpowiedź pozycji 6.D152, zmierzona, a nie opisana: pięć pól z pięciu.

    Pozycja zakładała, że wpis niesie „maszynę i zdanie o warunkach, których log nie podaje
    wprost, więc automat wypełniłby je zgadując". **Ta bramka jest przepisaniem tamtego
    zdania, a nie dopiskiem obok**: dla wpisów z CI log podaje wszystko, a wyprowadzone
    wartości zgadzają się z przepisanymi ręcznie co do znaku. Człowiek jest potrzebny tam,
    gdzie logu NIE MA — czyli przy pomiarach z kontenera sesji, i tylko tam.
    """
    po_pr = _wpisy_runnera_po_pr()
    znak_w_znak = 0
    for numer, (data, sekundy, modulow, maszyna, proza) in sorted(po_pr.items()):
        pola, brakujace = TR.z_logu(_log(numer))
        assert not brakujace, (
            f"log PR #{numer} nie dał pól {brakujace} — albo krok „Run tool tests” "
            "zmienił wypisy, albo to nie jest log tego kroku")
        assert set(TR.POLA_WPISU) <= set(pola), (numer, sorted(pola))
        assert pola["data"] == data, (numer, pola["data"], data)
        assert pola["sekundy"] == sekundy, (numer, pola["sekundy"], sekundy)
        assert pola["modulow"] == modulow, (numer, pola["modulow"], modulow)
        assert pola["maszyna"] == maszyna, (numer, pola["maszyna"], maszyna)
        assert proza.startswith(pola["na_czym"]), (
            f"zdanie „na czym” wpisu PR #{numer} nie zaczyna się od tego, co wychodzi "
            f"z logu:\n  z listy: {proza!r}\n  z logu:  {pola['na_czym']!r}")
        znak_w_znak += proza == pola["na_czym"]

    z_dopiskiem = len(po_pr) - znak_w_znak
    assert z_dopiskiem == WPISOW_Z_DOPISKIEM, (
        f"{znak_w_znak} z {len(po_pr)} wpisów zgadza się z logiem znak w znak, czyli "
        f"{z_dopiskiem} niesie dopisek człowieka przy `WPISOW_Z_DOPISKIEM` "
        f"= {WPISOW_Z_DOPISKIEM}. Jeśli dopisek zniknął — obniż tę liczbę; jeśli doszedł — "
        "zapytaj najpierw, czego log o nim nie mówi, bo do dziś nie mówił o niczym")


def test_kazdy_wpis_runnera_ma_log_w_drzewie():
    """Bramka, przez którą następny wpis przepisany z ręki nie przejdzie bez materiału.

    Bez niej odpowiedź pozycji 6.D152 byłaby zdaniem w raporcie: ktoś dopisałby wpis
    z pamięci, a bramka wyżej sprawdzałaby tylko te wpisy, dla których log akurat jest.
    """
    w_liscie = set(_wpisy_runnera_po_pr())
    w_drzewie = _logi_w_drzewie()
    assert w_liscie == w_drzewie, (
        f"wpisy runnera bez logu: {sorted(w_liscie - w_drzewie)}; logi bez wpisu: "
        f"{sorted(w_drzewie - w_liscie)} — pierwszego zbioru nie da się sprawdzić, "
        "a drugi znaczy, że materiał leży w drzewie i nikt go nie czyta")


def test_czytelnik_logu_MOWI_czego_nie_znalazl_zamiast_zmyslac():
    """Kontrola PRZYRZĄDU na wejściu syntetycznym: osiem logów z jedną dziurą każdy.

    Prawdziwy log ma wszystko, więc na nim samym „pola są" nie odróżnia czytelnika od
    takiego, który wstawia wartości domyślne — a to jest dokładnie rodzina 6.D27. Materiał
    jest prawdziwy, dziura sztuczna: z logu znika wiersz niosący jedno pole, a bramka żąda,
    żeby zapaliło się **dokładnie** tyle, ile od tego wiersza zależy.
    """
    wzorcowy = _log(sorted(_logi_w_drzewie())[0])
    pelne, brak_w_pelnym = TR.z_logu(wzorcowy)
    assert not brak_w_pelnym, brak_w_pelnym

    for pole, spodziewane in sorted(POCIAGA_ZA_SOBA.items()):
        pola, brakujace = TR.z_logu(_bez_wiersza(wzorcowy, pole))
        assert set(brakujace) == spodziewane, (
            f"po usunięciu wiersza z polem `{pole}` zgłoszone braki to {sorted(brakujace)}, "
            f"a spodziewane {sorted(spodziewane)}")
        for nazwa in spodziewane:
            assert nazwa not in pola, (
                f"pole `{nazwa}` powstało mimo braku wiersza, z którego wychodzi — "
                f"czytelnik je ZMYŚLIŁ: {pola[nazwa]!r}")
        for nazwa in set(pelne) - spodziewane:
            assert pola.get(nazwa) == pelne[nazwa], (
                f"usunięcie wiersza z polem `{pole}` ruszyło niezależne pole `{nazwa}`")


def test_nazwa_maszyny_nie_moze_sie_rozjechac_z_bramka_progu():
    """Dwa napisy o tej samej maszynie stoją w dwóch plikach — więc mają być pilnowane.

    `timing_record` nie importuje modułu testowego (to narzędzie CI, nie test), a
    `test_suite_runtime_budget` nie importuje narzędzia — przy rozjeździe wpis wyprowadzony
    z logu przestałby pasować do `POMIARY_RUNNERA` po cichu, a `MEASURED_MAX_WALL_S`
    liczyłby maksimum z pustego zbioru.
    """
    assert TR.MASZYNA_Z_LOGU == B.MASZYNA_RUNNER, (TR.MASZYNA_Z_LOGU, B.MASZYNA_RUNNER)
    assert TR.MASZYNA_Z_LOGU in B.MASZYNY, (TR.MASZYNA_Z_LOGU, B.MASZYNY)
    assert len(TR.POLA_WPISU) == len(B.POMIARY[0]), (
        f"wpis `POMIARY` ma {len(B.POMIARY[0])} pól, a `POLA_WPISU` wymienia "
        f"{len(TR.POLA_WPISU)} — liczba „pięć pól” z pozycji 6.D152 przestała mieć "
        "przedmiot")


def test_pomiar_bez_logu_zostaje_czlowiekowi_i_to_jest_rozstrzygniecie():
    """Druga połowa odpowiedzi: czego ten czytelnik NIE umie i umieć nie może.

    Wpisy kontenerowe nie mają logu joba — kontener sesji nie jest runnerem i nikt nie
    zapisuje z niego niczego maszynowo. Ich zdania „na czym" („host pod obciążeniem",
    „`ps aux` pokazywał równoległy `dotnet build`") są obserwacją człowieka i **tylko one**
    uzasadniają utrzymywanie listy ręcznie. Bramka pilnuje, żeby to rozróżnienie miało
    w liście przedmiot: każdy wpis jest albo runnera z logiem, albo nie-runnera bez logu.
    """
    kontenerowe = [w for w in B.POMIARY if w[3] != B.MASZYNA_RUNNER]
    assert kontenerowe, "lista straciła wpisy spoza runnera — rozróżnienie 6.D135 zniknęło"
    for wpis in kontenerowe:
        assert not NUMER_PR.search(wpis[4]), (
            f"wpis spoza runnera powołuje się na PR: {wpis!r} — albo jest z CI i ma "
            "maszynę `runner`, albo nie ma i wtedy numer PR-a niczego nie dowodzi")
    assert len(B.POMIARY) == len(B.POMIARY_RUNNERA) + len(kontenerowe), (
        "wpis, który nie jest ani runnera, ani kontenera — `MASZYNY` wymienia dwie")


if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))
