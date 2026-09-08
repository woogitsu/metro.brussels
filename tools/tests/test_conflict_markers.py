#!/usr/bin/env python3
"""Znacznik nierozwiązanego konfliktu scalania nie wejdzie do drzewa po cichu.

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
    for wzgledna in _pliki_repozytorium():
        pelna = os.path.join(ROOT, wzgledna)
        if not os.path.isfile(pelna):
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


if __name__ == "__main__":
    import test_all
    raise SystemExit(test_all.main(__file__))
