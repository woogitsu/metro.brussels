# 6.D312 · Cztery klasy pola nie są podziałem — sumują się do 101 przy populacji 57, a klasa, którą pole nazwało, jest PUSTA

**Data:** 20.09.2026 · **Gałąź:** `claude/sharp-ramanujan-jdr51o` · **Baza:** `654885d`

6.D303 zauważyło, że `MIN_RADIUS_M` jest martwe jako stała od 6.B25, a jego nazwa
pada dziś w prozie testów. Ta pozycja pyta, ile takich cytatów jest w całym
`tools/tests/` — i każe rozdzielić trzy klasy poprawnych cytatów, zanim policzy
się czwartą.

Czytnik prozy jest **pożyczony**: `proza` z `tools/tests/test_message_claims.py`,
ten sam, którym 6.D255 liczyło pokrycie liczb. Pole żądało tego wprost.

---

## 1. Sprostowanie przesłanki, wpisane razem z wykonaniem

Pole „Skąd" tej pozycji mówi, że `MIN_RADIUS_M` „pada dziś w **trzech** plikach
testów: raz w liście kontrolnej i dwa razy w prozie". Raport 6.D303 §7 jest
**przepisany** i mówi o **czterech** plikach. Sprawdziłem w drzewie:

```
tools/tests/test_clearance_profile.py   proza
tools/tests/test_constant_names.py      proza + asercje + lista przepisanych nazw
tools/tests/test_dead_constants.py      proza + asercje
tools/tests/test_packages.py            komentarz
```

**Cztery, nie trzy** — blok pomija `test_dead_constants.py`. Poprawiam blok i wiersz
w tym commicie, bo to przesłanka tej pozycji. Jest to **dokładnie ten kształt, który
zapisałem wczoraj jako 6.D322**: blok cytuje raport własnymi słowami, raport został
przepisany, a bloku nie tknęła żadna korekta ani żadna bramka. Drugi taki wypadek
w ciągu dwóch pozycji.

## 2. Liczby, których żądało pole „Wyjście"

```
POPULACJA (kształt spisany przed pomiarem: ALLCAPS z co najmniej jednym podkresleniem,
           nazwa BEZ przypisania gdziekolwiek pod tools/**/*.py)

   nazw:       57
   wystapien: 170
   wezlow prozy przeszukanych: 14763
   stalych przypisanych pod tools/ (odsiane):  1226
```

Wariant węższy, po konwencji projektu — **wyłącznie nazwy w grawisach**, ten sam
kształt, którego używa `CLAIM` w `test_report_claims.py`:

```
   nazw:       39
   wystapien:  63
```

Podaję obie liczby, bo mój plik definicji zapowiadał to na wypadek, gdyby dwa
kształty się rozjechały. Rozjechały się: grawis odsiewa osiemnaście nazw i przeszło
dwie trzecie wystąpień.

## 3. GŁÓWNE ZNALEZISKO: cztery klasy pola NIE SĄ PODZIAŁEM

Pole mówi: „Trzy klasy są poprawne i trzeba je **rozdzielić**, zanim policzy się
czwartą". Słowo „rozdzielić" zakłada, że klasy są rozłączne. Nie są:

```
lista_kontrolna         47     (nazwa pada w LITERALE NAPISOWYM w kodzie bramki)
wszystkie_datowane      16     (kazde wystapienie w akapicie z data DD.MM.RRRR)
srodowisko_CI           29     (nazwa stoi w .github/, *.sh albo *.yml)
src/ lub tests/          9     (nazwa gdziekolwiek pada w cudzym drzewie)
                       ---
SUMA FLAG              101     przy POPULACJI 57
```

Rozkład kombinacji — i to jest właściwa odpowiedź na pytanie pola, bo pojedyncze
liczby wyżej sumują się do nieprawdy:

```
 15  lista_kontrolna + srodowisko_CI
 11  lista_kontrolna
  8  lista_kontrolna + wszystkie_datowane
  7  *** ZADNA Z CZTERECH KLAS ***
  7  lista_kontrolna + srodowisko_CI + src
  4  lista_kontrolna + wszystkie_datowane + srodowisko_CI
  2  lista_kontrolna + wszystkie_datowane + srodowisko_CI + src
  2  wszystkie_datowane
  1  srodowisko_CI
 ---
 57
```

**Powód jest strukturalny, a nie przypadkowy.** Trzy z czterech klas mówią o tym,
gdzie nazwa pada **poza prozą** (lista kontrolna, cudze drzewo, środowisko), a jedna
o **samej prozie** (czy akapit ma datę). Nazwa może być jednocześnie na liście
kontrolnej i w datowanym akapicie — i osiem nazw takie jest. Pole zadało pytanie
o podział, a populacja ma **cztery niezależne własności**.

## 4. Klasa, którą pole nazwało wprost, jest PUSTA

Pole każe odsiać „**cytat cudzego drzewa** (nazwa z `src/`, nie z `tools/`)".
Dziewięć nazw rzeczywiście pada gdzieś pod `src/` albo `tests/` — ale **ani jedna
nie jest tam przypisana**:

```
GITHUB_TOKEN    9 wystapien   PRZYPISAN: 0   tests/data/ci-logs/README.md
GODOT_BIN       1             PRZYPISAN: 0   src/Sim.Runner/Program.cs
L1_A          104             PRZYPISAN: 0   src/Game/Assets/StreamingPlan.cs
L1_B           29             PRZYPISAN: 0   tests/Sim.Tests/LineRouteTests.cs
L2_E           26             PRZYPISAN: 0   tests/Sim.Tests/LineRouteTests.cs
L5_C           25             PRZYPISAN: 0   tests/data/ci-logs/tools-pr524.log
L5_D           26             PRZYPISAN: 0   tests/Sim.Tests/SignallingPlanTests.cs
L6_F           25             PRZYPISAN: 0   tests/data/ci-logs/tools-pr524.log
RUNNER_TEMP    56             PRZYPISAN: 0   tests/data/ci-logs/tools-pr524.log
```

`L1_A`, `L5_D` i reszta tej rodziny to **identyfikatory odcinków linii** — napisy
z `data/network/`, nie stałe. `RUNNER_TEMP` i `GITHUB_TOKEN` padają tam wyłącznie
w **zapisanych logach CI**. Osobny pomiar potwierdza to niezależnie: nazw o kształcie
stałej **przypisanych** pod `src/` jest **zero**.

**Cudze drzewo, o które pole pyta, nie zawiera ani jednej z tych nazw** — a drzewo,
które je zawiera, pole nazywa gdzie indziej albo wcale.

## 5. Gdzie te nazwy naprawdę mieszkają: środowisko, CI i biblioteki cudze

Największa rodzina poza `tools/` to **zmienne środowiskowe i CI — dwadzieścia
dziewięć z pięćdziesięciu siedmiu**, czyli ponad połowa:

```
APT_INSTALL_TIMEOUT_S  APT_OPTS  APT_UPDATE_ATTEMPTS  BLENDER_BIN  BLENDER_EEVEE
DOTNET_INSTALL_DIR  GITHUB_ENV  GITHUB_TOKEN  GODOT_BIN  GODOT_VERSION
HAVE_SDK_MAJOR  HOSTFXR_OK  INSTALL_TIMEOUT_S  L1_A  L1_B  L2_E  L5_C  L5_D  L6_F
MBXL_DOCTOR_RUNNING  MBXL_WYCIAG_FAILI  METRO_TIMING_OUT  REQUIRED_TFM
RUNNER_TEMP  RUNNER_TOOL_CACHE  RUN_TESTS  SDK_NA_DYSKU  SDK_NA_LISCIE  WYCIAG_FAILI
```

Dziewięć z nich należy do drzew **jeszcze innych**, sprawdzonych importem, a nie
domyślonych z nazwy:

```
RUSAGE_CHILDREN                         modul `resource` biblioteki standardowej
FSTRING_START / FSTRING_MIDDLE / FSTRING_END    modul `token` (przez nazwy tokenow CPythona)
BLENDER_EEVEE / BLENDER_EEVEE_NEXT      wartosci enuma silnika Blendera
GITHUB_ENV / GITHUB_TOKEN / RUNNER_NAME / RUNNER_TEMP / RUNNER_TOOL_CACHE
                                        srodowisko GitHub Actions
```

**Mój klasyfikator pomylił się tu w jedną stronę i mówię to, zamiast poprawić
po cichu:** regułą „nazwa zaczyna się od `BLENDER_`" wrzuciłem do enumów Blendera
także `BLENDER_BIN`, które jest **własną zmienną tego projektu** (CLAUDE.md §9
wymienia ją razem z `GODOT_BIN`). To ten sam błąd przedrostka, który 6.D310 zmierzyło
u siebie dwa dni temu — i popełniłem go ponownie, w pozycji o dwa numery dalej.

## 6. Odpowiedź na pytanie zadane wprost

Pole pyta, „ile z nich stoi w akapicie **BEZ daty**".

```
nazw, ktorych KAZDE wystapienie stoi w akapicie z data:  16
nazw z CO NAJMNIEJ JEDNYM wystapieniem bez daty:         41
nazw poza WSZYSTKIMI czterema klasami:                    7
```

Siedmiu, które nie wpadają do żadnej z czterech klas, nie nazywam usterką — pole
tego zabrania i ma rację. Wypisuję je z nazwy, żeby następna pozycja nie musiała
ich szukać:

```
GAME_SOURCE_GLOB       test_game_needle_specificity.py
GAME_SOURCE_SKIP       test_game_needle_specificity.py
MIN_GOLYCH_ROZNYCH     test_field_paths.py
POLECENIE_KOMPILACJI   test_bytecode_staleness.py
RUSAGE_CHILDREN        test_suite_runtime_budget.py
WIELKIE_LITERY         test_dead_constants_csharp.py
WIELKIMI_LITERAMI      test_prose_counts.py
```

Dwie ostatnie są zresztą **zwykłymi polskimi słowami pisanymi wielkimi literami**,
a nie nazwami stałych — wpadły, bo mają podkreślenie w środku. Kształt składniowy
ich nie odróżnia i mój czytnik też nie; liczę je, a nie odsiewam, bo odsianie
byłoby oceną.

## 7. KONTROLA PRZYRZĄDU: NIE ODTWARZA SIĘ W LITERZE

Pole żąda: „`MIN_RADIUS_M` ma wyjść z **dwoma** wystąpieniami w prozie i jednym
w liście kontrolnej". Wychodzi inaczej:

```
w prozie:  8 wystapien w 4 plikach
   test_clearance_profile.py w.2011   docstring
   test_constant_names.py    w.2      docstring
   test_constant_names.py    w.119    docstring
   test_dead_constants.py    w.2      docstring   (dwa trafienia w tym samym wezle)
   test_dead_constants.py    w.81     docstring
   test_dead_constants.py    w.195    docstring
   test_packages.py          w.32     komentarz
w literalach kodu: 3 pliki
datowanych wezlow prozy: 4 z 8
```

**Mówię to wprost, zamiast ogłaszać kontrolę zdaną albo dopasowywać czytnik.**
Przyczyna jest w **jednostce**, nie w przyrządzie: 6.D303 §7 liczyło **pliki, w których
wzmianka jest WYŁĄCZNIE prozą** — takich jest dwa (`test_clearance_profile.py`
i `test_packages.py`) — a pole przepisało to jako „dwa wystąpienia w prozie".
Czytnik `proza` liczy **węzły**, a sam `test_dead_constants.py` ma ich cztery.

Litera kontroli jest więc niespełniona, a **zgodność z 6.D303 zachodzi**: dwa pliki
prozy-wyłącznie, jeden z listą kontrolną, jeden z asercją — razem cztery, dokładnie
jak w przepisanym §7. Jednostka jest tu treścią, tak samo jak przy 6.D309 i 6.D310.

## 8. Przewidywania spisane PRZED pomiarem — dwa obalone, jedno trafione POŁOWICZNIE

| # | przewidywanie | wynik |
|---|---|---|
| W1 | nazw: 15–60 | trafione (57, a wariantem grawisowym 39) |
| W2 | największa klasa to **akapit datowany** | **OBALONE** — największa to lista kontrolna (47), datowane ma 16 |
| W3 | klasa „reszta" jest niepusta | trafione (siedem) |
| W4 | cztery klasy NIE zsumują się do populacji — będzie **klasa piąta** | trafione w pierwszej połowie, **obalone w drugiej** |
| W5 | kontrola przyrządu się odtworzy | **OBALONE** — §7 |
| W6 | co najmniej jedna z dziesiątki 6.D303 padnie w prozie | trafione — **pięć z dziesięciu** |

**W4 jest najciekawsze i nie zaliczam go jako trafionego.** Przewidziałem, że suma
klas nie zgodzi się z populacją, i nie zgadza się — ale w **przeciwną stronę**, niż
zapowiedziałem. Spodziewałem się **niedoboru** (klasa piąta, nazwy poza podziałem)
i taki niedobór istnieje, siedmioosobowy; przeoczyłem natomiast, że dominuje
**nadmiar**: suma flag wynosi 101 przy populacji 57, bo klasy się **nakładają**.
Nazwałem właściwy objaw i **złą przyczynę**, i tak to liczę.

W6 było najsłabsze z sześciu: jedna nazwa z dziesięciu wystarczała do trafienia,
a `MIN_RADIUS_M` stoi wprost w polu „Skąd". Pięć z dziesięciu jest liczbą wartą
zapisania, ale trafienie samego przewidywania nie jest zasługą.

## 9. Czego świadomie nie zrobiono

- **Nie poprawiono ani nie przepisano niczyjej prozy.** 6.D300 zmierzyło, ile to
  kosztuje, a pole „Poza zakresem" zabrania tego wprost.
- **Nie usunięto żadnej nazwy z listy kontrolnej** ani z `UZASADNIONE`.
- **Nie postawiono bramki** na wyniku — ani na kształcie nazwy, ani na dacie akapitu.
- **Nie odsiano `WIELKIE_LITERY` i `WIELKIMI_LITERAMI`**, choć są zwykłymi słowami:
  odsianie byłoby oceną, a pozycja liczy.
- **Nie uzgodniono litery kontroli przyrządu z 6.D303** — §7 pokazuje, że różnica
  jest w jednostce, a nie w pomiarze, i zostawiam obie liczby zamiast wybierać.
- **Nie tknięto `src/`, `data/`** ani kodu bramek.

## 10. Zauważone przy okazji, nietknięte

**Rozjazd bloku z przepisanym raportem wyszedł DRUGI RAZ z rzędu** — przy 6.D311
i przy tej pozycji. Za każdym razem znalazło go czytanie bloku przed wzięciem
pozycji, a nie bramka. Pozycja 6.D322 jest już w kolejce i teraz ma dwa
potwierdzone wypadki zamiast jednego podejrzenia.

**Identyfikatory odcinków (`L1_A`, `L5_D`, `L6_F` …) mają kształt stałej, a są
napisami z `data/network/`** — i to one, a nie stałe, dają największą liczbę
wystąpień w całej populacji (`L1_A` sam ma trzydzieści siedem). Każdy skan szukający
„nazwy stałej" w prozie tego repozytorium będzie je łapał, dopóki ktoś nie zapisze,
że identyfikator odcinka nie jest stałą.

**Cztery nazwy tokenów CPythona (`FSTRING_START`, `FSTRING_MIDDLE`, `FSTRING_END`)
padają w prozie `test_bytecode_staleness.py`** i są prawdziwe, tylko należą do
`token` z biblioteki standardowej. Żaden czytnik tego projektu nie odróżnia nazwy
z cudzej biblioteki od własnej martwej stałej.

## 11. Weryfikacja — rzeczywiste wyjście

```
$ find . -name __pycache__ -prune -exec rm -rf {} +
$ python3 tools/tests/test_all.py
  [DRZEWO] 0 plikow drzewa roboczego poza zasiegiem bramek czytajacych `git ls-files` — 6.D165
  [BAJTKOD] wyczyszczono 1 kat. __pycache__ (1 plikow) pod tools/ — 6.D122
  2664/2664 przeszło
  RAZEM 361.079 s, 2664 testów, 139 modułów
EXIT=0
```

Zero `FAIL`. **Bramki nie przybyło** — pozycja LICZY, a pole „Poza zakresem"
zabrania stawiania bramki na wyniku; liczba testów jest ta sama co przy 6.D311
i 6.D310, i mówię to wprost, zamiast pokazywać wzrost, którego nie ma.

Bramki dotknięte tą pozycją przeszły wcześniej osobno — `test_report_hygiene`,
`test_backlog`, `test_field_paths`, `test_report_claims`, `test_message_claims`
i `test_docs_map`, **159/159**.

**Czas przebiegu jest o pięćdziesiąt sekund krótszy niż przy dwóch poprzednich
pozycjach** (361,079 s wobec 414,695 i 418,599 s na tym samym kontenerze), co daje
iloraz **1,16** przy tej samej liczbie testów. Nie wyciągam z tego wniosku i nie
ruszam żadnego progu: to jest ściana, nie CPU, a pytanie o rozrzut stoi już
w kolejce jako 6.D313 i ma tam własne pole „Weryfikacja". Zapisuję liczbę, żeby
tamta pozycja zastała trzeci pomiar, a nie dwa.
