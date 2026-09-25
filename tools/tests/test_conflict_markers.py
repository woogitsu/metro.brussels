#!/usr/bin/env python3
r"""Znacznik nierozwiązanego konfliktu scalania nie wejdzie do drzewa po cichu.

**SKĄD TA BRAMKA — 6.D55, zmierzone 08.09.2026.** `docs/TASKS.md` z nierozwiązanym
konfliktem przechodził **cały zestaw na zielono**, a liczniki wychodziły poprawnie,
bo parser bloków czyta wiersze, których znaczniki nie psują:

    znaczników <<<: 1   ===: 1   >>>: 1
    2000/2000 przeszło
    KOD ZESTAWU: 0
    open_items = 16   bloki = 125   braki w blokach: {}

**Nie była to hipoteza.** Tego dnia w tym pliku były dwa konflikty. Przy jednym
mechaniczna suma stron wstawiła blok 6.D39 w środek bloku 6.D40 i **odebrała mu
cztery pola** — złapała to bramka licząca pola, czyli **przypadkiem**. Gdyby konflikt
wypadł w miejscu, którego żadna bramka nie liczy, znaczniki weszłyby do `main`.

**ZAKRES WZORCA JEST WYPROWADZONY Z POMIARU, NIE ZGADNIĘTY**, bo pole „Skończone,
gdy" tej pozycji stawia warunek twardy: bramka zapalająca się na tekście poprawnym
zostaje wyłączona (6.D27), więc fałszywych alarmów musi być **zero**. Zmierzone na
`4a4f8f2`, po całym drzewie (`git ls-files`, 573 pliki):

| wzorzec | trafień dziś | najdłuższy LEGALNY ciąg w drzewie |
|---|---:|---|
| `^<{7,}` | 0 | **1** (`<import>…`, XML) |
| `^={7}$` | 0 | **brak** — w drzewie nie ma ani jednego wiersza z samych `=` |
| `^>{7,}` | 0 | **3** |
| `^\|{7,}` | 0 | **1** (4933 wiersze tabel Markdown) |

Trzy wzorce łapią **siedem znaków albo więcej**, a `=` **równo siedem**; asymetria
jest uzasadniona pomiarem przy samej definicji `ZNACZNIKI` niżej i przybita testem
`test_dlugosc_SIEDMIU_znakow_…`.

**Trzyznakowy ciąg `>` jest tu rzeczą, którą pomiar uratował**, i dlatego stoi
w tabeli: jedyne takie wystąpienie to `reports/mutation-triage-validate.md:47`,
wiersz `>>> (885.0 + 0.01) - 885.0` — **znak zachęty Pythona**, tekst całkowicie
poprawny. Wzorzec `^>{3}` zapaliłby się na nim i bramka poszłaby do wyłączenia po
pierwszym przebiegu. Siedem znaków tego nie robi, bo git pisze dokładnie siedem.

Wzorzec `^\|{7}` (marker bazy przy `merge.conflictStyle = diff3`) wchodzi, choć
dziś w drzewie nie ma ani jednego konfliktu w tym stylu: kosztuje zero fałszywych
alarmów przy 4933 wierszach tabel, bo tabele mają **jeden** znak, nie siedem.

**Dlaczego wzorce są ZAKOTWICZONE na początku wiersza.** Szukanie podciągu zapala
się na **prozie bloku 6.D55** w `docs/TASKS.md`, który znaczniki cytuje, żeby o nich
mówić — i na docstringu tego pliku. Zmierzone 08.09.2026 przy #413: sprawdzenie
`"<<<<<<<" in tekst` daje trafienie na tekście, w którym żadnego konfliktu nie ma.
Kotwica rozstrzyga to bez żadnej listy wyjątków, a lista wyjątków byłaby tu gorsza:
plik, który raz na niej stanie, przestaje być pilnowany na zawsze.
"""
import hashlib
import json
import os
import re
import subprocess

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

#: Znaczniki, które git wypisuje w plik przy nierozwiązanym konflikcie. Każdy
#: ZAKOTWICZONY na początku wiersza — to wynika z pomiaru w docstringu modułu,
#: nie z ostrożności. Długość: trzy wzorce biorą siedem znaków ALBO WIĘCEJ, `=`
#: równo siedem; powód asymetrii stoi w komentarzu pod tą definicją.
ZNACZNIKI = (
    re.compile(r"^<{7,}(?:\s|$)"),     # `<<<<<<< HEAD`
    re.compile(r"^={7}$"),             # `=======` samo w wierszu — RÓWNO siedem
    re.compile(r"^>{7,}(?:\s|$)"),     # `>>>>>>> origin/main`
    re.compile(r"^\|{7,}(?:\s|$)"),    # `||||||| base` — styl diff3
)

# ASYMETRIA JEST WYBOREM Z POMIARU, NIE PRZEOCZENIEM, i została złapana przez
# `test_dlugosc_SIEDMIU_znakow_…` w tym pliku, na pierwszym przebiegu: wzorzec
# `^<{7}(?:\s|$)` NIE widział ośmiu znaków `<`, bo po siódmym stał kolejny `<`,
# a nie spacja. Git pisze dokładnie siedem, ale `git merge-file --marker-size=N`
# umie napisać więcej, więc pytanie „czy łapać dłuższe" jest realne.
#
# Rozstrzyga je koszt fałszywego alarmu, osobno dla każdego znaku:
#   `<`, `>`, `|`  ->  {7,}   bo najdłuższy LEGALNY ciąg w drzewie ma 1, 3 i 1 znak,
#                             więc łapanie dłuższych nie kosztuje nic;
#   `=`            ->  {7}    bo wiersz z samych `=` jest w Markdownie legalnym
#                             rozdzielaczem i nagłówkiem setext — dowolnej długości.
#                             `^={7,}$` zapaliłby się na pierwszym dopisanym
#                             rozdzielaczu, a takich wierszy w tym drzewie nie ma
#                             dziś ani jednego, co znaczy tylko tyle, że jeszcze
#                             nikt go nie napisał.

#: PODŁOGA NA LICZBĘ CZYTANYCH PLIKÓW, ale nie stała — liczona w czasie przebiegu
#: z `git ls-files`. Stała zestarzałaby się przy pierwszym dodanym pliku i byłaby
#: dokładnie tą usterką, którą 6.D45 zmierzyło na `MIN_REPORTS`: zapadką stojącą
#: sto pozycji za stanem. Poniżej stoi więc tylko **absolutny bezpiecznik** na
#: wypadek, gdyby `git ls-files` zamilkło i oba liczniki zeszły do zera razem —
#: wtedy porównanie „skan == ls-files" byłoby zielone na pustym zbiorze.
#: Zmierzone na `4a4f8f2`: 573 pliki w drzewie. Bezpiecznik stoi na 100, bo ma
#: łapać awarię narzędzia, nie zmiany w repozytorium.
BEZPIECZNIK_LICZBY_PLIKOW = 100


def _pliki_repozytorium():
    """Ścieżki plików ŚLEDZONYCH przez gita, względem `ROOT`.

    `git ls-files`, a nie chodzenie po katalogach: pilnowane ma być to, co może
    trafić do `main`, a nie śmieci w drzewie roboczym (`build/`, `renders/`,
    katalogi tymczasowe sond). Ten sam idiom co `_pliki_repozytorium()`
    w `test_runner_options.py`.
    """
    wypis = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True,
                           text=True, check=True).stdout
    return [p for p in wypis.split("\n") if p]


def znaczniki_w_drzewie():
    """`(trafienia, przeczytane, nieczytelne)` — jedno miejsce dla bramki i testów.

    `trafienia` to lista `(ścieżka, numer wiersza, treść)`. `nieczytelne` to pliki,
    których nie dało się zdekodować jako UTF-8; są zwracane osobno, **a nie
    pomijane po cichu**, bo plik binarny dopisany do repozytorium zmniejszałby
    skan bez ani jednego słowa. Zmierzone na `4a4f8f2`: nieczytelnych **zero**.
    """
    trafienia = []
    przeczytane = 0
    nieczytelne = []
    evidence_prefixes = (
        "reports/visual-evidence/t400-run-36078093066/",
        "reports/visual-evidence/parc-arrival/",
        "reports/visual-evidence/t400-side/",
        "reports/visual-evidence/t400-platform/",
        "reports/visual-evidence/t400-stop-target/",
    )
    evidence = {}
    for prefix in evidence_prefixes:
        manifest_path = os.path.join(ROOT, prefix, "manifest.json")
        with open(manifest_path, encoding="utf-8") as manifest_file:
            for item in json.load(manifest_file)["files"]:
                if item["name"].endswith((".png", ".gif")):
                    evidence[prefix + item["name"]] = item
    seen_images = set()
    for wzgledna in _pliki_repozytorium():
        pelna = os.path.join(ROOT, wzgledna)
        if not os.path.isfile(pelna):
            continue
        if any(wzgledna.startswith(prefix) for prefix in evidence_prefixes) and wzgledna.endswith((".png", ".gif")):
            data = open(pelna, "rb").read()
            item = evidence.get(wzgledna)
            signature_ok = (data.startswith(b"\x89PNG\r\n\x1a\n")
                            if wzgledna.endswith(".png")
                            else data.startswith((b"GIF87a", b"GIF89a")))
            if (item is None or len(data) != item["bytes"] or
                    hashlib.sha256(data).hexdigest() != item["sha256"] or
                    not signature_ok):
                nieczytelne.append(wzgledna)
                continue
            seen_images.add(wzgledna)
            przeczytane += 1
            continue
        try:
            with open(pelna, encoding="utf-8") as uchwyt:
                wiersze = uchwyt.read().split("\n")
        except (UnicodeDecodeError, OSError):
            nieczytelne.append(wzgledna)
            continue
        przeczytane += 1
        for numer, wiersz in enumerate(wiersze, start=1):
            if any(wzorzec.match(wiersz) for wzorzec in ZNACZNIKI):
                trafienia.append((wzgledna, numer, wiersz[:60]))
    if seen_images != set(evidence):
        nieczytelne.append("manifest visual evidence mismatch")
    return trafienia, przeczytane, nieczytelne


def test_zadny_sledzony_plik_nie_niesie_znacznika_konfliktu():
    """Rdzeń 6.D55: nierozwiązany konflikt nie wejdzie do `main` po cichu.

    Komunikat podaje **plik i numer wiersza**, bo tego żąda pole „Wyjście" tej
    pozycji: bramka mówiąca tylko „gdzieś jest konflikt" zostawia szukanie
    czytającemu, a plik chroniony ma dziś 5900 wierszy.
    """
    trafienia, _, _ = znaczniki_w_drzewie()
    assert not trafienia, "znaczniki nierozwiązanego konfliktu scalania:\n" + "\n".join(
        f"  {sciezka}:{numer}: {tresc}" for sciezka, numer, tresc in trafienia)


def test_skan_czyta_CALE_drzewo_a_nie_pusty_zbior():
    """Bramka, która nic nie przeczytała, jest zielona — i to jest jej usterka.

    Podłoga NIE jest stałą: liczba plików jest liczona w czasie przebiegu
    z `git ls-files` i porównywana z liczbą plików, które skan naprawdę otworzył.
    Stała zestarzałaby się przy pierwszym dodanym pliku, czyli powtórzyłaby
    usterkę, którą 6.D45 zmierzyło na `MIN_REPORTS` (zapadka sto pozycji za
    stanem). Osobno stoi absolutny bezpiecznik: gdyby `git ls-files` zamilkło,
    oba liczniki zeszłyby do zera i samo porównanie byłoby zielone na pustce.

    Pliki nieczytelne jako UTF-8 są **wymienione**, nie przemilczane — plik
    binarny dopisany do repozytorium zmniejsza skan i musi to powiedzieć.
    """
    trafienia, przeczytane, nieczytelne = znaczniki_w_drzewie()
    sledzone = [p for p in _pliki_repozytorium()
                if os.path.isfile(os.path.join(ROOT, p))]
    assert przeczytane > BEZPIECZNIK_LICZBY_PLIKOW, (
        f"skan przeczytał {przeczytane} plików przy bezpieczniku "
        f"{BEZPIECZNIK_LICZBY_PLIKOW} — `git ls-files` albo odczyt przestały działać")
    assert przeczytane + len(nieczytelne) == len(sledzone), (
        f"skan otworzył {przeczytane} plików i odrzucił {len(nieczytelne)}, "
        f"a git śledzi {len(sledzone)} — skan przestał czytać część drzewa")
    assert not nieczytelne, (
        f"pliki nieczytelne jako UTF-8, więc niepilnowane: {nieczytelne} — "
        "jeżeli mają w drzewie zostać, wzorzec pilnowanych plików wymaga decyzji, "
        "a nie cichego pominięcia")
    # Trafień ten test świadomie NIE sprawdza, choć je ma pod ręką: to robi
    # `test_zadny_sledzony_plik_…` z komunikatem podającym plik i wiersz.
    # Dwa FAIL-e o jednej przyczynie, z których jeden wypisuje surową krotkę,
    # kazałyby czytającemu zgadywać, czy to dwie usterki, czy jedna — a ten
    # test ma mówić o POKRYCIU skanu, nie o jego wyniku.


def test_detektor_ZAPALA_sie_na_prawdziwym_konflikcie_w_kazdym_z_czterech_stylow():
    """Kontrola negatywna: gdyby detektor nie widział niczego, test wyżej byłby
    zielony na zawsze i nikt by tego nie zauważył.

    Cztery znaczniki są sprawdzane **osobno**, bo wzorzec zepsuty w jednym z nich
    nie łamie pozostałych trzech i przeszedłby niezauważony przy sprawdzeniu
    „czy cokolwiek się zapala".
    """
    for etykieta, wiersz in (
        ("HEAD", "<<<<<<< HEAD"),
        ("rozdzielacz", "======="),
        ("gałąź", ">>>>>>> origin/main"),
        ("baza diff3", "||||||| 4a4f8f2"),
    ):
        assert any(wzorzec.match(wiersz) for wzorzec in ZNACZNIKI), (
            f"detektor nie widzi znacznika {etykieta}: {wiersz!r}")


def test_detektor_MILCZY_na_tekscie_poprawnym_ktory_znaczniki_CYTUJE():
    """Warunek 6.D27, bez którego ta bramka poszłaby do wyłączenia.

    Trzy kształty tekstu poprawnego, każdy zmierzony w tym drzewie:

    * **znaczniki cytowane w prozie** — tak robi blok 6.D55 w `docs/TASKS.md`
      i docstring tego pliku; sprawdzenie podciągiem zapala się na nich, kotwica
      nie (zmierzone przy #413);
    * **znak zachęty Pythona** `>>> ` — jedyny wiersz z `>>>` w drzewie stoi
      w `reports/mutation-triage-validate.md:47` i jest poprawnym zapisem sesji
      interaktywnej; wzorzec `^>{3}` zapaliłby się na nim;
    * **wiersz tabeli Markdown** i **cytat Markdown** — 4933 i 535 wystąpień
      w drzewie, po jednym znaku każde.
    """
    for etykieta, wiersz in (
        ("cytat w prozie", "wzorzec `<<<<<<< HEAD` na początku wiersza"),
        ("cytat w prozie, środek", "między `=======` i `>>>>>>> origin/main`"),
        ("znak zachęty Pythona", ">>> (885.0 + 0.01) - 885.0"),
        ("cytat Markdown", "> zdanie w cytacie"),
        ("wiersz tabeli", "| kolumna | druga |"),
        ("rozdzielacz tabeli", "|---|---:|"),
        ("nagłówek setext", "==="),
        ("dłuższy rozdzielacz", "=" * 40),
    ):
        assert not any(wzorzec.match(wiersz) for wzorzec in ZNACZNIKI), (
            f"detektor zapala się na poprawnym tekście ({etykieta}): {wiersz!r}")


def test_dlugosc_SIEDMIU_znakow_jest_wyborem_z_pomiaru_a_nie_przypadkiem():
    """Sześć znaków to nie konflikt, siedem to konflikt, osiem to nadal konflikt.

    Git pisze dokładnie siedem. Pomiar drzewa pokazał, że najdłuższy legalny ciąg
    `>` na początku wiersza ma **trzy** znaki (znak zachęty Pythona), a `<` i `|`
    po **jednym** — więc siedem jest bezpieczne z zapasem, a trzy nie byłoby.
    Ten test przybija OBIE granice: gdyby ktoś rozluźnił wzorzec do trzech znaków,
    padnie tutaj, a nie po fałszywym alarmie na cudzym raporcie.
    """
    assert not any(w.match("<<<<<<") for w in ZNACZNIKI), "sześć `<` to nie konflikt"
    assert not any(w.match("======") for w in ZNACZNIKI), "sześć `=` to nie konflikt"
    assert not any(w.match(">>>>>>") for w in ZNACZNIKI), "sześć `>` to nie konflikt"
    assert any(w.match("<<<<<<<<") for w in ZNACZNIKI), (
        "osiem `<` to nadal konflikt — `git merge-file --marker-size` umie napisać "
        "dłuższy znacznik, a legalny ciąg `<` w tym drzewie ma jeden znak")
    assert any(w.match(">>>>>>>>") for w in ZNACZNIKI), "osiem `>` to nadal konflikt"
    # `=======` jest pilnowany na RÓWNOŚĆ siedmiu, bo dłuższy ciąg samych `=`
    # jest w Markdownie legalnym rozdzielaczem; w tym drzewie takich wierszy nie
    # ma ani jednego, ale wzorzec `^={7,}$` zapaliłby się na pierwszym dopisanym.
    assert not any(w.match("========") for w in ZNACZNIKI), (
        "osiem `=` to rozdzielacz Markdown, nie konflikt — git pisze dokładnie siedem")



# --- 6.D165: ktore bramki pytaja gita o liste plikow, i co przebieg o tym mowi ------

#: Moduly, ktore NAPRAWDE wykonuja `git ls-files` — policzone 13.09.2026, nie zgadniete.
#: Wpis pozycji 6.D165 wymienial trzy; trzeci (`test_report_hygiene.py`) tylko CYTUJE
#: to polecenie w komunikacie bledu, a nie wola go, wiec do listy nie nalezy.
#:
#: **`test_all.py` dolaczyl do nich przy 6.D165 i jest tu z INNEGO powodu niz dwa
#: pozostale.** Tamte sa BRAMKAMI i sa na pliki niesledzone SLEPE — pytaja o indeks,
#: zeby pilnowac tego, co moze trafic do `main`. `test_all.py` pyta o to, czego
#: w indeksie NIE MA, i nie ocenia tego, tylko wypisuje. Jedna lista, dwie role,
#: i rozdziela je stala nizej — inaczej zapadka mowilaby, ze slepych bramek jest trzy.
#: Zrodlo przebiegu — czytane, zeby sprawdzic, ze wypis o drzewie w nim STOI.
TA_ZRODLO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_all.py")

MODULY_PYTAJACE_GITA = ("test_all.py", "test_conflict_markers.py",
                        "test_runner_options.py")

#: Te z nich, ktore sa BRAMKAMI slepymi na pliki niesledzone. `test_all.py` nie jest
#: bramka i do tej liczby nie wchodzi.
BRAMKI_SLEPE_NA_NIESLEDZONE = ("test_conflict_markers.py", "test_runner_options.py")

#: **Przez `tree_walk` NIE PYTA GITA ANI JEDEN — i to jest wynik pomiaru, nie
#: zalozenie.** Pole „Ile bramek to dotyczy" pozycji 6.D165 mowilo, ze liczba modulow
#: chodzacych po `git ls-files` POSREDNIO, przez `tree_walk`, jest do zmierzenia.
#: Zmierzona wynosi ZERO: `tree_walk` importuje wylacznie `fnmatch`, `os` i `shutil`,
#: czyta `.gitignore` jako TEKST i chodzi po katalogach. Slepota na pliki niesledzone
#: nie rozlewa sie wiec na dwadziescia kilka modulow, ktore `tree_walk` importuja —
#: siedzi w dwoch wymienionych wyzej.
IMPORTY_TREE_WALK_BEZ_GITA = ("fnmatch", "os", "shutil")


def _repozytorium_probne(katalog):
    """Prawdziwe repo gita z jednym plikiem SLEDZONYM i jednym NIE — wejscie syntetyczne.

    Na drzewie tego projektu funkcji liczacej nie da sie sprawdzic: plikow niesledzonych
    jest dzis ZERO, wiec funkcja zwracajaca zawsze zero bylaby nie do odroznienia od
    dzialajacej. Ta sama nauka, co przy bramce polozenia modulow w 6.D159.
    """
    import subprocess

    def git(*a):
        return subprocess.run(("git",) + a, cwd=katalog, capture_output=True, text=True)

    git("init", "-q")
    git("config", "user.email", "probne@example.invalid")
    git("config", "user.name", "probne")
    with open(os.path.join(katalog, "sledzony.txt"), "w", encoding="utf-8") as u:
        u.write("w indeksie\n")
    git("add", "sledzony.txt")
    git("commit", "-qm", "probny")
    with open(os.path.join(katalog, "niesledzony.txt"), "w", encoding="utf-8") as u:
        u.write("poza indeksem\n")


def test_przebieg_MOWI_ile_plikow_lezy_poza_zasiegiem_bramek_czytajacych_gita():
    """6.D165: wypis istnieje, liczy naprawde, i nie jest bramka.

    **Co zmierzono.** Gita o liste plikow pytaja **dwa** moduly, nie trzy — trzeci
    tylko cytuje to polecenie w komunikacie. Przez `tree_walk` nie pyta **ani jeden**,
    bo `tree_walk` gita nie wola wcale. Slepota jest wiec waska i nazwana.

    **Czego wypis NIE robi.** Nie zmienia kodu wyjscia i nie jest bramka: liczba
    wieksza od zera znaczy „tyle plikow ten przebieg pominal", a nie „blad". Zmiana
    tego w bramke zatrzymywalaby prace na kazdym pliku roboczym w drzewie, czyli
    bylaby karą za normalny sposob pracy — a usterka z PR #548 polegala na CISZY,
    nie na istnieniu takich plikow.
    """
    import tempfile
    import test_all as TA

    # 1. NA DZISIEJSZYM DRZEWIE: liczba jest znana i wynosi zero.
    ile, powod = TA.poza_zasiegiem_git_ls_files()
    assert powod == "", "nie udalo sie zapytac gita o wlasne drzewo: %s" % powod
    assert ile == 0, (
        "w drzewie roboczym lezy %d plikow niesledzonych — to nie jest blad, ale "
        "znaczy, ze dwie bramki czytajace `git ls-files` ich nie widza" % ile)

    # 2. NA REPOZYTORIUM PROBNYM: liczba NIE jest zawsze zerem. Bez tej polowy
    #    punkt pierwszy przechodzilby tak samo dla funkcji `return 0, ""`.
    with tempfile.TemporaryDirectory() as tmp:
        _repozytorium_probne(tmp)
        ile_probne, powod_probne = TA.poza_zasiegiem_git_ls_files(tmp)
        assert powod_probne == "", powod_probne
        assert ile_probne == 1, (
            "na repozytorium z jednym plikiem niesledzonym licznik zwrocil %r — "
            "wypis nie liczy niczego i zero na drzewie projektu nic nie znaczy"
            % ile_probne)

    # 3. I ZE NIEWIEDZA JEST ZADEKLAROWANA, a nie zamieniona na zero: katalog, ktory
    #    repozytorium NIE JEST, ma dac `None` i powod, a nie ciche `0`.
    with tempfile.TemporaryDirectory() as tmp:
        ile_niegit, powod_niegit = TA.poza_zasiegiem_git_ls_files(tmp)
        assert ile_niegit is None and powod_niegit, (
            "poza repozytorium licznik zwrocil %r — ciche zero wygladaloby tak samo "
            "jak czyste drzewo" % (ile_niegit,))


def test_gita_o_liste_plikow_pyta_DOKLADNIE_tyle_modulow_ile_wymieniono():
    """Zapadka na zasieg slepoty — 6.D165.

    Trzeci modul wolajacy `git ls-files` ma zmusic do rozstrzygniecia, czy jego wypis
    tez ma o pominieciu mowic, a nie dojsc po cichu.
    """
    import tree_walk

    katalog = os.path.dirname(os.path.abspath(__file__))
    wolajace = []
    for nazwa in sorted(os.listdir(katalog)):
        if not nazwa.endswith(".py"):
            continue
        with open(os.path.join(katalog, nazwa), encoding="utf-8") as uchwyt:
            tresc = uchwyt.read()
        if '["git", "ls-files"' in tresc or "('git', 'ls-files'" in tresc:
            wolajace.append(nazwa)

    assert tuple(wolajace) == MODULY_PYTAJACE_GITA, (
        "gita o liste plikow pyta %s, a wymieniono %s — kolejny taki modul wymaga "
        "rozstrzygniecia, czy jest BRAMKA slepa na pliki niesledzone, czy tylko "
        "o nich wypisuje" % (wolajace, list(MODULY_PYTAJACE_GITA)))

    # I ZE PODZIAL NA ROLE JEST PELNY: kazda bramka slepa jest wsrod wolajacych,
    # a `test_all.py` do slepych NIE nalezy. Bez tego obie stale moglyby sie
    # rozjechac, a liczba slepych bramek rosla by po cichu razem z lista wolajacych.
    assert set(BRAMKI_SLEPE_NA_NIESLEDZONE) < set(MODULY_PYTAJACE_GITA), (
        "bramki slepe %s nie sa WLASCIWYM podzbiorem wolajacych %s — albo doszla "
        "bramka spoza listy wolajacych, albo reporter zostal policzony jako slepy "
        "i liczba slepych bramek urosla po cichu"
        % (list(BRAMKI_SLEPE_NA_NIESLEDZONE), list(MODULY_PYTAJACE_GITA)))
    assert "test_all.py" not in BRAMKI_SLEPE_NA_NIESLEDZONE, (
        "`test_all.py` trafil miedzy bramki slepe — on wlasnie pyta o to, czego "
        "w indeksie nie ma, i niczego nie ocenia")

    # I DRUGA POLOWA: `tree_walk` nadal gita NIE wola, wiec slepota sie nie rozlewa.
    with open(tree_walk.__file__, encoding="utf-8") as uchwyt:
        zrodlo_tw = uchwyt.read()
    # I ZE PRZEBIEG TEN WYPIS NAPRAWDE ROBI. Bez tej asercji kontrola negatywna
    # zdejmujaca wypis z `test_all.py` wychodzila ZIELONA: funkcja byla sprawdzona,
    # a jej UZYCIE nie — czyli mechanizm dalby sie wylaczyc bez ani jednego czerwonego
    # testu. Zmierzone przy 6.D165, KN-3.
    # Sprawdzane PRZEBIEGIEM, a nie szukaniem napisu w zrodle — i to jest poprawka
    # po kontroli, ktora wyszla ZIELONA DWA RAZY. Wersja pytajaca, czy nazwa
    # `_metro_drzewo_policzone` wystepuje w pliku, przechodzila zarowno po zdjeciu
    # wartowni, jak i po zamianie jej warunku na `if False:` — bo nazwa zostawala
    # w drugiej polowie konstrukcji. Napis w zrodle nie jest wypisem na wyjsciu.
    import subprocess
    import sys as _sys
    wypis = subprocess.run(
        [_sys.executable, TA_ZRODLO, "test_lod_paths.py"],
        cwd=ROOT, capture_output=True, text=True, timeout=300)
    assert "[DRZEWO]" in wypis.stdout, (
        "przebieg NIE wypisuje, ile plikow lezy poza zasiegiem bramek czytajacych "
        "gita — funkcja moze byc poprawna, a przebieg znowu o tym MILCZY (6.D165). "
        "Wyjscie zaczyna sie tak:\n%s" % wypis.stdout[:400])
    # CZEGO TA KONTROLA NIE SPRAWDZA I DLACZEGO — zmierzone, nie zalozone. Wartownia
    # `sys._metro_drzewo_policzone` chroni przed podwojnym wypisem, gdy `_discover`
    # laduje `test_all.py` po raz drugi pod nazwa `test_all__mierzony`. Przy wywolaniu
    # z JEDNYM nazwanym modulem to sie nie dzieje: kontrola negatywna zdejmujaca
    # wartownie wyszla ZIELONA, a wypis nadal padl dokladnie raz. Asercji na liczbe
    # wystapien tu wiec NIE MA, bo nie moglaby zapalic sie nigdy — czyli bylaby
    # kontrola pusta z konstrukcji, rodzina liczona w 6.D161. Wartownia zostaje jako
    # ubezpieczenie BEZ wejscia, i jest to powiedziane wprost zamiast udawane asercja.

    # Czytane Z DRZEWA SKLADNI, a nie szukaniem napisu: `"subprocess" not in zrodlo`
    # bylo by zielone takze wtedy, gdyby modul wolal gita przez `os.popen`, i czerwone
    # na samym slowie w komentarzu. Lista importow jest tu faktem sprawdzalnym.
    import ast as _ast
    importowane = set()
    for wezel in _ast.walk(_ast.parse(zrodlo_tw)):
        if isinstance(wezel, _ast.Import):
            importowane.update(a.name.split(".")[0] for a in wezel.names)
        elif isinstance(wezel, _ast.ImportFrom) and wezel.module:
            importowane.add(wezel.module.split(".")[0])
    assert importowane == set(IMPORTY_TREE_WALK_BEZ_GITA), (
        "`tree_walk` importuje %s, a pomiar 6.D165 zastal %s — jesli doszedl "
        "`subprocess` albo cokolwiek, co umie zawolac gita, to slepota na pliki "
        "niesledzone rozlewa sie na wszystkie moduly, ktore `tree_walk` importuja, "
        "i liczbe „przez tree_walk pyta ZERO” trzeba przeliczyc"
        % (sorted(importowane), sorted(IMPORTY_TREE_WALK_BEZ_GITA)))
    assert "ls-files" not in zrodlo_tw, (
        "`tree_walk` wymienia `git ls-files` — nawet jesli tylko w komentarzu, "
        "warto sprawdzic, czy nie zaczal go wolac")


if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))
