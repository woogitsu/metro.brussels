# 6.D335 · Na bibliotece standardowej kończy się PIĘĆDZIESIĄT SZEŚĆ z dwustu dwudziestu pięciu wywołań, a nie dwieście osiem — tytuł pozycji jest nieprawdziwy

**Data:** 20.09.2026 · **Gałąź:** `claude/new-session-1xabcy` · **Baza:** `df2e8f8`

6.D326 §4 zmierzyło, że z 428 czytników o nierozstrzygniętym kluczu **208 kończy
łańcuch na wywołaniu, którego celu nie ma w `tools/tests/`**, i nazwało tę klasę
`WOLANIE SPOZA tools/tests`. Pole tej pozycji przetłumaczyło ją na „kończy się na
bibliotece standardowej" i wymieniło `subprocess`, `re`, `json`, `os.path`,
`collections`. **Ta pozycja liczy i czyta dokumentację**; żadnego czytnika nie
przepisuje i żadnego klasyfikatora nie rozszerza.

---

## 1. Kontrola przyrządu ZDANA co do jedynki

```
   populacja: 208   [6.D326: 208]
```

Przyrząd 6.D326 przeniosłem bez zmian, z jedną rozbudową **spisaną w pliku definicji
przed pomiarem**: tamten zapisywał samą nazwę atrybutu (`run`, `load`), przez co
moduł docelowy ginął. Zapisuję pełną ścieżkę wywołania.

**Rozbudowa kosztowała dwie pomyłki i obie zgłaszam.** Pierwsza wersja miała własną
pętlę domykania, krótszą niż `domknij`, i dawała **zero wywołań przy 208
czytnikach** — czyli rozkład nie miałby czego sumować. Druga: podmiana pola
`wolania` nie objęła jego oryginalnego zapisu i klucz `pelne` w ogóle nie powstawał;
wynik był ten sam zerowy, ale z innego powodu. Dopiero trzecia wersja liczy.

## 2. GŁÓWNE ZNALEZISKO: tytuł pozycji jest nieprawdziwy i mówię to liczbą

Dwieście osiem czytników robi **225 wywołań** (jeden czytnik bywa domykany więcej
niż jednym). Czym naprawdę jest ich cel:

```
=== CZYM JEST CEL WYWOLANIA (225 wywolan w 208 czytnikach) ===
   ODBIORCA NIE JEST NAZWA              56
   BIBLIOTEKA STANDARDOWA               56
   ZMIENNA LOKALNA                      50
   KOD PROJEKTU spoza tools/tests       32
   WBUDOWANE                            29
   PAKIET ZEWNETRZNY                     2
   SUMA                                225
```

**Na bibliotece standardowej kończy się 56 z 225, czyli jedna czwarta.** Tytuł
pozycji — „dwieście osiem czytników kończy się na bibliotece standardowej" —
opisuje więc klasę **czterokrotnie mniejszą**, niż podaje.

Nie jest to zarzut wobec 6.D326: tamta pozycja nazwała klasę `WOLANIE SPOZA
tools/tests` i to jest nazwa **poprawna**. Nieprawdziwe jest dopiero tłumaczenie
tej nazwy na „bibliotekę standardową", które wszedłem do pola tej pozycji — i które
sam bym powtórzył, gdybym nie policzył.

### 2.1 Największa klasa to LITERAŁ NAPISOWY, a nie żaden moduł

```
--- ODBIORCA NIE JEST NAZWA (56)
      <literal>.join                      32
      <?>.encode                           5
      <indeks>.strip                       4
      <?>.replace                          3
      <wywolanie>.replace                  3
```

Trzydzieści dwa z pięćdziesięciu sześciu to `"…".join(...)` — **metoda literału
napisowego**. Żaden klasyfikator szukający modułu jej nie dosięgnie, bo odbiorcy nie
ma w żadnym imporcie: jest nim napis wpisany w miejscu wywołania.

### 2.2 Trzydzieści dwa wywołania to KOD TEGO PROJEKTU, tylko katalog dalej

```
--- KOD PROJEKTU spoza tools/tests (32)
      G.check · V.validate · TM.geometry_problems · CRS._geodetic_to_ecef
      stop_names.kanoniczny_czlon · braking.params · compare.check_image
      CL.car_chord_m · gate.load_config · SW.catmull_rom · DF.audit · Layout
```

Te wywołania mają cel **w tym repozytorium** — w `tools/blender/`, `tools/track/`,
`tools/physics/`, `tools/visual/`. Klasa nazywa się „spoza `tools/tests`" i to jest
dosłownie prawda, ale wniosek z 6.D326, że „żadna liczba skoków tego nie domknie, bo
cel nie jest czytnikiem tego projektu", **dla tych trzydziestu dwóch nie zachodzi**:
cel jest czytnikiem tego projektu, tylko skan go nie widzi, bo skanuje jeden katalog.

### 2.3 Pięćdziesiąt to zmienna lokalna, a nie wywołanie modułu

`handle.read` (9), `uchwyt.read` (6), `wynik.stdout.strip` (4), `done.stdout.strip`
(3), `match.group`, `body.replace`, `expression.strip` — to metody wołane na
zmiennej z ciała funkcji. Łańcuch skoków kończy się tu nie dlatego, że cel jest
obcy, tylko dlatego, że **reguła jednego skoku z 6.D309 nie wchodzi w atrybut
zmiennej**.

## 3. Rozkład po module docelowym — imiennie

```
--- BIBLIOTEKA STANDARDOWA (56)
      os.path.join                      22        ast.fix_missing_locations   1
      json.load                         12        datetime.datetime           1
      subprocess.run                     9        os.path.abspath             1
      ast.parse                          2        json.loads                  1
      math.nextafter                     2        argparse.Namespace          1
      re.sub                             2        subprocess.Popen            1
                                                  types.ModuleType            1
--- PAKIET ZEWNETRZNY (2)
      yaml.safe_load 1 · yaml.load 1
```

**`collections` nie pada ani razu**, mimo że pole wymienia je jako jeden z pięciu
modułów. **`re` pada dwa razy**, i oba to `re.sub`, a nie `re.search`, którego pole
używa jako sztandarowego przykładu. Największym modułem jest **`os`** (23 wywołania
z `os.path.join` i `os.path.abspath`), a nie `re`.

## 4. Kształt zwrotu — dwie klasy pola, PLUS trzecia, liczone osobno

Pole ostrzegało, żeby nie mylić „daje się rozstrzygnąć z dokumentacji" z „zwraca
zawsze ten sam kształt". Czytałem dokumentację i **sprawdzałem ją wykonaniem**,
zamiast zgadywać z nazwy:

```
os.path.join      -> str          json.loads('1')   -> int
os.path.abspath   -> str          json.loads('{}')  -> dict
math.nextafter    -> float        json.loads('[]')  -> list
subprocess.run    -> CompletedProcess
re.sub(str)       -> str          ast.parse         -> Module
re.sub(bytes)     -> bytes        ast.parse(eval)   -> Expression
```

| klasa | wywołań | które |
|---|---|---|
| **JEDNOZNACZNY** | **39** | `os.path.join` 22, `subprocess.run` 9, `math.nextafter` 2, `ast.fix_missing_locations`, `datetime.datetime`, `os.path.abspath`, `argparse.Namespace`, `subprocess.Popen`, `types.ModuleType` |
| **ZALEŻNY OD ARGUMENTU** | **4** | `ast.parse` 2 (`mode=` daje `Module` albo `Expression`), `re.sub` 2 (napis albo bajty, zależnie od typu wejścia) |
| **ZALEŻNY OD DANYCH** | **13** | `json.load` 12, `json.loads` 1 |

**39 + 4 + 13 = 56 — zgadza się z klasą z §3.**

**Odpowiedź na pytanie zadane wprost: kształt zależny od danych ma TRZYNAŚCIE
wywołań**, wszystkie z `json`. Pole żądało tej liczby także wtedy, gdy wynosi zero,
bo „wtedy klasyfikator dałoby się domknąć słownikiem". Nie wynosi zera, więc
słownikiem domknąć się **nie da** — ale warto zobaczyć, jak mało brakuje: trzynaście
wywołań na 225, z jednego modułu i z dwóch funkcji.

Dwa wywołania `yaml` są tego samego rodzaju (`safe_load` zwraca, co napotka), ale
stoją w klasie „pakiet zewnętrzny" i do tabeli ich nie doliczam.

## 5. Przewidywania — trzy trafione, dwa obalone, jedno połowicznie

| # | przewidywanie | wynik |
|---|---|---|
| T1 | suma wyjdzie równo 208 | **trafione** (§1) |
| T2 | najliczniejszym modułem będzie `re` | **OBALONE**: `os` (23), a `re` pada dwa razy |
| T3 | zależnych od danych co najmniej dziesięć | **trafione**: trzynaście |
| T4 | WBUDOWANE niepusta i liczniejsza niż `collections` | **trafione, ale trywialnie**: 29 wobec **zera** — `collections` nie pada ani razu |
| T5 | `json.load` i `re.search` będą w populacji | **połowicznie**: `json.load` tak, `re.search` NIE |
| T6 | przypisanie modułu pomyli się co najmniej raz | **trafione**, i nie raz: §1 opisuje dwie pomyłki przyrządu, a §2 pokazuje, że samo pojęcie „moduł docelowy" nie obejmuje 169 z 225 wywołań |

## 6. Czego świadomie nie zrobiłem

Nie rozszerzyłem klasyfikatora 6.D315, nie przepisałem żadnego czytnika, nie
postawiłem bramki na kształcie zwrotu, nie tknąłem `src/` ani `data/` — wszystko to
stoi w polu „Poza zakresem".

**Nie poprawiłem pola tej pozycji ani tytułu 6.D335 w `docs/TASKS.md`.** Tytuł jest
nieprawdziwy i §2 mówi to liczbą; przepisanie go byłoby zacieraniem śladu, po którym
widać, że tłumaczenie nazwy klasy na potoczną zmieniło jej treść.

## 7. Co zauważyłem przy okazji, ale nie tknąłem

`os.path.join` z dwudziestoma dwoma wywołaniami jest **najczęstszym pojedynczym
powodem**, dla którego czytnik tego katalogu nie ma rozstrzygniętego kształtu zwrotu
— a jego zwrot jest `str` zawsze, bez wyjątku i bez zależności od argumentu. Jedna
para (`os.path.join`, `str`) w słowniku klasyfikatora domknęłaby dziesiątą część
całej klasy 208. Czy klasyfikator ma znać bibliotekę standardową, jest decyzją
o narzędziu pomiarowym i nie podejmuję jej.
