# Bramka na znaczniki konfliktu scalania (6.D55)

**Zmierzone 08.09.2026 na:** `4a4f8f2` — drzewo bez znaczników (573 pliki śledzone)
oraz to samo drzewo z konfliktem wstawionym sondą w środek bloku pozycji.
**Przyrząd:** `git grep -nE` po całym drzewie, `python3 tools/tests/test_all.py; echo $?`
oraz nowa bramka `tools/tests/test_conflict_markers.py`.

---

## 1. Co było zepsute

`docs/TASKS.md` z **nierozwiązanym konfliktem** przechodził cały zestaw na zielono,
a liczniki wychodziły **poprawnie** — bo parser bloków czyta wiersze, których
znaczniki nie psują. Pomiar z treści pozycji:

```
znaczników <<<: 1   ===: 1   >>>: 1
2000/2000 przeszło
KOD ZESTAWU: 0
open_items = 16   bloki = 125   braki w blokach: {}
```

Nie była to hipoteza: tego dnia w pliku były dwa konflikty, a przy jednym mechaniczna
suma stron wstawiła blok 6.D39 w środek bloku 6.D40 i **odebrała mu cztery pola**.
Złapała to bramka licząca pola, czyli **przypadkiem**.

## 2. Zakres wzorca wyprowadzony z pomiaru, nie zgadnięty

Pole „Skończone, gdy" stawia warunek twardy: bramka zapalająca się na tekście
poprawnym zostaje wyłączona (6.D27), więc fałszywych alarmów musi być **zero**.
Dlatego najpierw policzono, ile razy każdy kandydat na wzorzec trafia w drzewie
**legalnie**, a wybór zapadł dopiero na tych liczbach.

Rozkład ciągów na początku wiersza, całe drzewo (`git ls-files`, 573 pliki):

| znak | najdłuższy ciąg w drzewie | ile wystąpień | co to jest |
|---|---:|---:|---|
| `=` | **brak** | 0 | w drzewie nie ma ani jednego wiersza z samych `=` |
| `<` | **1** | 22 | `<import>…`, XML/HTML |
| `>` | **3** | 1 | **znak zachęty Pythona** |
| `>` | 1 | 535 | cytat Markdown |
| `\|` | **1** | 4933 | wiersze i rozdzielacze tabel Markdown |

**Trzyznakowy ciąg `>` jest rzeczą, którą ten pomiar uratował.** Jedyne wystąpienie:

```
reports/mutation-triage-validate.md:47:>>> (885.0 + 0.01) - 885.0
```

To poprawny zapis sesji interaktywnej Pythona. Wzorzec `^>{3}` zapaliłby się na nim
i bramka poszłaby do wyłączenia po pierwszym przebiegu — dokładnie tak, jak 6.D27
opisuje. Siedem znaków tego nie robi.

Trafienia wybranych wzorców na dzisiejszym drzewie, czyli **fałszywe alarmy**:

| wzorzec | trafień |
|---|---:|
| `^<{7,}(?:\s\|$)` | **0** |
| `^={7}$` | **0** |
| `^>{7,}(?:\s\|$)` | **0** |
| `^\|{7,}(?:\s\|$)` | **0** |

Wzorzec `^\|{7,}` (marker bazy przy `merge.conflictStyle = diff3`) wchodzi, choć
konfliktu w tym stylu w drzewie nie ma ani jednego: kosztuje **zero** fałszywych
alarmów przy 4933 wierszach tabel, bo tabele mają jeden znak, nie siedem. Styl
`diff3` nie jest dziś ustawiony, ale jest ustawieniem lokalnym gita, nie własnością
repozytorium — może się pojawić bez żadnej zmiany w drzewie.

### Asymetria długości: trzy wzorce biorą „siedem lub więcej", `=` równo siedem

To **nie jest przeoczenie** i złapał to test w tej samej bramce, na pierwszym
przebiegu:

```
FAIL test_dlugosc_SIEDMIU_znakow_jest_wyborem_z_pomiaru_a_nie_przypadkiem: osiem `<` to nadal konflikt
```

Pierwotny wzorzec `^<{7}(?:\s|$)` nie widział ośmiu znaków `<`, bo po siódmym stał
kolejny `<`, a nie spacja. Git pisze dokładnie siedem, ale `git merge-file
--marker-size=N` umie napisać więcej, więc pytanie było realne. Rozstrzyga je koszt
fałszywego alarmu, osobno dla każdego znaku:

- **`<`, `>`, `|` → `{7,}`** — najdłuższy legalny ciąg w drzewie ma 1, 3 i 1 znak,
  więc łapanie dłuższych nie kosztuje nic;
- **`=` → `{7}`** — wiersz z samych `=` jest w Markdownie legalnym rozdzielaczem
  i nagłówkiem setext, **dowolnej długości**. `^={7,}$` zapaliłby się na pierwszym
  dopisanym rozdzielaczu. Że takich wierszy dziś nie ma, znaczy tylko tyle, że
  jeszcze nikt go nie napisał.

## 3. Dlaczego wzorce są ZAKOTWICZONE na początku wiersza

Szukanie podciągu zapala się na **prozie bloku 6.D55** w `docs/TASKS.md`, który
znaczniki cytuje, żeby o nich mówić — i na docstringu nowej bramki, i na tym
raporcie. Zmierzone przy #413: `"<<<<<<<" in tekst` daje trafienie na tekście,
w którym żadnego konfliktu nie ma.

Kotwica rozstrzyga to **bez listy wyjątków**, i to jest wybór: plik, który raz
stanie na liście wyjątków, przestaje być pilnowany na zawsze — a `docs/TASKS.md`
jest jednocześnie plikiem chronionym i plikiem, który znaczniki cytuje.

## 4. Sonda: znaczniki wstawione w ŚRODEK bloku pozycji

Tak samo jak sonda z treści 6.D55 — w środek bloku `6.D56`, żeby nie wypadły
w miejscu, które akurat liczy jakaś inna bramka.

**Bramka:**

```
FAIL test_zadny_sledzony_plik_nie_niesie_znacznika_konfliktu: znaczniki nierozwiązanego konfliktu scalania:
  docs/TASKS.md:5866: <<<<<<< HEAD
  docs/TASKS.md:5868: =======
  docs/TASKS.md:5870: >>>>>>> origin/main
```

Plik i numer wiersza dla każdego z trzech znaczników — tego żąda pole „Wyjście",
bo plik chroniony ma dziś prawie 5900 wierszy.

**Cały zestaw na tym samym drzewie:**

```
KOD ZESTAWU: 1
  2047/2049 przeszło
  RAZEM 92.198 s, 2049 testów, 109 modułów
--- liczniki na drzewie ze znacznikami:
open_items = 17
```

**To jest rozstrzygnięcie pozycji.** Przed zmianą to samo drzewo dawało 2000/2000
i **kod 0**; dziś daje kod 1. A `open_items` nadal wychodzi **17**, czyli liczniki
są wciąż „poprawne" — co potwierdza diagnozę z treści pozycji: parser czyta wiersze,
których znaczniki nie psują, więc żadna istniejąca bramka nie miała jak tego zobaczyć.

`md5` `docs/TASKS.md` przed wstawieniem i po przywróceniu:
`884db6123af8e28783b86aa6249354da` — ta sama, więc plik wrócił co do bajtu. Po
przywróceniu `find tools -name __pycache__ -type d -exec rm -rf {} +`.

## 5. Drzewo bez znaczników

```
5/5 przeszło
RAZEM 0.381 s, 5 testów, 1 modułów
kod: 0
```

Zero fałszywych alarmów, czego żąda warunek 6.D27.

## 6. Pięć testów, i po co każdy z nich

1. **`test_zadny_sledzony_plik_nie_niesie_znacznika_konfliktu`** — rdzeń, z plikiem
   i numerem wiersza w komunikacie.
2. **`test_skan_czyta_CALE_drzewo_a_nie_pusty_zbior`** — bramka, która nic nie
   przeczytała, jest zielona. Podłoga **nie jest stałą**: liczba plików jest liczona
   w czasie przebiegu z `git ls-files` i porównywana z liczbą plików, które skan
   naprawdę otworzył. Stała zestarzałaby się przy pierwszym dodanym pliku, czyli
   powtórzyłaby usterkę, którą 6.D45 zmierzyło na `MIN_REPORTS`. Obok stoi
   **absolutny bezpiecznik** (100): gdyby `git ls-files` zamilkło, oba liczniki
   zeszłyby do zera i samo porównanie byłoby zielone na pustce.
3. **`test_detektor_ZAPALA_sie_na_prawdziwym_konflikcie_w_kazdym_z_czterech_stylow`**
   — cztery znaczniki sprawdzane **osobno**, bo wzorzec zepsuty w jednym nie łamie
   pozostałych trzech i przeszedłby niezauważony przy sprawdzeniu „czy cokolwiek się
   zapala".
4. **`test_detektor_MILCZY_na_tekscie_poprawnym_ktory_znaczniki_CYTUJE`** — osiem
   kształtów tekstu poprawnego, każdy zmierzony w tym drzewie: cytat w prozie, znak
   zachęty Pythona, cytat Markdown, wiersz tabeli, rozdzielacz tabeli, nagłówek
   setext, rozdzielacz czterdziestu `=`.
5. **`test_dlugosc_SIEDMIU_znakow_jest_wyborem_z_pomiaru_a_nie_przypadkiem`** —
   przybija OBIE granice, żeby rozluźnienie wzorca do trzech znaków padło tutaj,
   a nie fałszywym alarmem na cudzym raporcie.

## 7. Pliki nieczytelne jako UTF-8

Zmierzone: **zero**. Skan zwraca je osobno i **wymienia w komunikacie**, a nie
pomija po cichu — plik binarny dopisany do repozytorium zmniejszałby pokrycie skanu
bez ani jednego słowa. Asercja żąda pustej listy, więc pierwszy taki plik wymusi
decyzję o wzorcu pilnowanych plików, zamiast cicho wypaść z pilnowania.

## 8. Czego świadomie nie zrobiłem

- **Nie dodałem hooka `pre-commit`** — zabrania tego pole „Poza zakresem"; bramka
  chodzi w zestawie, tam gdzie reszta.
- **Nie zmieniłem sposobu rozwiązywania konfliktów** ani nie tknąłem żadnego bloku
  pozycji.
- **Nie dodałem listy wyjątków od skanu.** Powód stoi w §3 i jest merytoryczny, nie
  ostrożnościowy: `docs/TASKS.md` musi być jednocześnie pilnowany i wolno mu cytować
  znaczniki, a kotwica daje jedno i drugie.
- **Nie objąłem plików nieśledzonych przez gita.** Pilnowane ma być to, co może
  trafić do `main`; `build/`, `renders/` i katalogi sond są gitignorowane i pełne
  plików, których nikt nie scala.

## 9. Zauważone przy okazji, nie tknięte

**Pole „Wejście" tej pozycji wskazało `tools/tests/test_marker_gates.py` jako plik
do przeczytania — związek jest czysto nominalny.** Tamten moduł dotyczy luzów
skrajni w Blenderze (`select_marks`, `side_sign`, `clearance_problems`), a nie
znaczników scalania; wspólne jest tylko słowo „marker". Bramka powstała więc
w osobnym pliku. Nie jest to zgłoszone jako pozycja, bo dotyczy jednego pola jednej
pozycji, a nie kodu — ale jest to **czwarty raz tego dnia**, kiedy pole „Wejście"
wskazało plik o związku pozornym albo ścieżkę, której nie ma w drzewie
(6.D52 i 6.D58 wskazywały raporty spoza drzewa, 6.D45 podawało numery wierszy
starsze o dwanaście raportów). Warunek zgłoszenia osobnej pozycji: piąty przypadek.
