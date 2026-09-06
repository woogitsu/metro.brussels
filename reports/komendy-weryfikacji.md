# Ile komend z pól „Weryfikacja" da się w ogóle uruchomić (6.D15)

**Zmierzone 06.09.2026 na commicie:** `74f5b4a6a0a8060ab807fc92fa79dab230d76d04`

Pole „Weryfikacja" jest w tym projekcie obietnicą, której nikt nie odbierał.
`tools/tests/test_backlog.py` sprawdza, czy pole MA treść — i to jest jedyne, czego
pilnuje. Pozycja 6.C3 (#297) wyszła z bloku, którego komenda jest odrzucana przez
istniejącą w kodzie odmowę: to znalezisko otworzyło tę pozycję.

## 1. Co zebrano

Kolektor: `tools/tests/backlog_commands.py` (nowy). Czyta bloki `##### <numer> ·`
tym samym czytnikiem, którego używa `test_backlog.py`, wycina pole „Weryfikacja"
tą samą regułą cięcia i skleja wiersze płotka w komendy: kontynuacja `\`, pętla
`for … do … done` jako JEDNO polecenie, wiersz komentarza pominięty.

```

blokow z polem „Weryfikacja”: 42
komend zebranych: 83
komend z miejscem do wypełnienia (?): 2
```

Komendy są zbierane, nie przepisywane: liczba rośnie z każdym nowym blokiem, więc
wpisana tu na sztywno rozjechałaby się bezszelestnie — to ta sama rodzina usterki,
którą łapie bramka z #273. Wypis powyżej jest cytatem wyjścia z dnia pomiaru.

## 2. Werdykty — trzy kategorie

| kategoria | ile | co to znaczy |
|---|---|---|
| **uruchamialna** | **73** | da się wpisać dosłownie i kończy się werdyktem |
| **wymaga narzędzia, którego tu nie ma** | **4** | Blender albo geometria, którą Blender produkuje |
| **niewykonalna tak, jak pole obiecuje** | **5** | miejsce do wypełnienia, brak wymaganych opcji albo odmowa w kodzie |

Suma 82. Kategoria druga i trzecia wymienione z nazwy niżej; kategoria pierwsza to
reszta — w większości `python3 tools/tests/test_all.py` i `dotnet test tests/Sim.Tests`,
oba wykonane w tej sesji.

### 2.1 Wymaga narzędzia, którego tu nie ma (4)

| blok | komenda | dlaczego |
|---|---|---|
| 6.B9 | `bash tools/ci/blender_smoke.sh` | `doctor.sh` zgłasza brak Blendera |
| 6.D9 | `"$BLENDER_BIN" --background --python tools/visual/capture_blender.py -- --help` | jw. |
| 6.C4 | `"$GODOT_BIN" … --shot=build/inspect.png --view=… --at-chainage=2521.1` | wymaga chunków z Blendera, patrz §3.3 |
| 6.C4 | `python3 tools/ci/assert_shot_metadata.py build/inspect.png` | nie ma czego czytać, dopóki poprzednia nie da PNG |

### 2.2 Niewykonalna tak, jak pole obiecuje (5)

| blok | co jest nie tak | zmierzone |
|---|---|---|
| **6.D2** | `--signalling <plan> --steps <N>`; pole wymieniało 3 z 7 opcji, których `Budget` wymaga | kod 1, `BŁĄD: line wymaga --limit-kmh` |
| **6.A6** | `--coast-from-m X`; `X` nie jest wartością, a opcji nie ma w `src/` | kod 0 i **dwa pliki identyczne co do bajtu** |
| 6.C3 | `--line` nie łączy się z `--telemetry` | kod 9, odmowa jawna w kodzie |
| 6.D9 | `png_pixels_sha256.py <dwa PNG z dwóch przebiegów tej samej sceny>` | nawiasu nie da się wpisać |
| 6.B18 | `--journal <własny dziennik>` | jw. |

Trzy z tych pięciu (6.C3, 6.D9, 6.B18) to bloki pozycji **ZROBIONYCH**.
Ich poprawka jest poza zakresem tej pozycji: to zapis historyczny, a nie instrukcja
do wykonania. Poprawione zostały dwa bloki pozycji niezrobionych z tej tabeli
(**6.D2** i **6.A6**) oraz — o brakujący warunek wstępny, nie o komendę — blok
**6.C4** z tabeli §2.1. Razem trzy, wszystkie opisane w §3.

## 3. Poprawione pola

### 3.1 6.D2 — `budget` już istnieje, brakowało czterech opcji

Polecenie `budget` **jest** w `src/Sim.Runner/Program.cs` i działa; brakuje bramki,
nie polecenia. Komenda z pola, wpisana dosłownie z podstawionym planem i `N=1000`:

```
BŁĄD: line wymaga --limit-kmh
kod wyjścia: 1
```

Po przepisaniu pola (siedem wymaganych opcji, plan z `data/design/signalling/`):

```
[BUDŻET] oś L1_A, plan classic-2026-L1_A (23 bloków), 12 stacji, ATP=nie, nawrót 0 s, odstęp 120 s
[BUDŻET] okno 1000 kroków, rozgrzewka 2, powtórzeń 7, rdzeni 4, budżet kroku 1/120 s = 8333.3 µs
[BUDŻET] mieści się w 1/120 s: 5 z 5 zmierzonych N; największe zmierzone N=32 zajmuje 0.09% budżetu kroku przy 1 składach faktycznie na planie
kod wyjścia: 0
```

### 3.2 6.A6 — komenda, którą spełnia NIEZROBIENIE zadania

To jest najcięższe znalezisko tej pozycji i nie jest ono o składni. `--coast-from-m`
nie występuje dziś nigdzie w `src/`, a `Sim.Runner` **nieznaną opcję przyjmuje
w milczeniu**: obie komendy z pola kończą się kodem 0, a pliki wychodzą identyczne.

```
11d298315379ba7fbb4673250daeab830d80a3fc084bf4bd731f84a1d811b079  build/coast-off.csv
11d298315379ba7fbb4673250daeab830d80a3fc084bf4bd731f84a1d811b079  build/coast-on.csv
```

Agent wykonujący 6.A6 mógłby więc przejść całą tę weryfikację **nie napisawszy ani
jednego wiersza kodu wybiegu** i zobaczyć zielono. Pole dostało wiersz `sha256sum`
z wymaganiem, żeby sumy się **różniły** — bez niego weryfikacja jest wyrocznią
zepsutą w stronę „wszystko w porządku".

### 3.3 6.C4 — warunek wstępny, którego pole nie nazywało

Kształt komendy jest poprawny (`--shot`, `--view`, `--at-chainage` istnieją; widok
`inspect` dokłada dopiero ta pozycja i to jest w porządku). Brakowało warunku
wstępnego. Zmierzone ze **znanym** widokiem `cab`, żeby nie mylić tego z brakiem
widoku `inspect`:

```
ERROR: [ASSETS] brak manifestu …/build/t400/chunks/L1_A-chunks.json. Wygeneruj chunki
(tools/blender/tunnel_sweep.py --chunk-dir …) albo uruchom z --no-geometry.
kod: 4
```

Pole mówi teraz, że bez Blendera tej pozycji nie da się zweryfikować — i że to jest
odpowiedź, a nie usterka pola.

## 4. Co pomiar znalazł przy okazji, a czego nie tknął

- **`--only` w `mutation_sweep.py` dopasowuje podciąg, nie nazwę pliku.**
  `--only sweep.py` z bloku 6.B6 obejmuje **dwa** moduły: `tools/blender/sweep.py`
  (117 mutacji) i `tools/blender/tunnel_sweep.py` (68). Komenda jest uruchamialna
  i dlatego stoi w kategorii pierwszej, ale mierzy więcej, niż nazywa.
- **Licznik z bloku 6.A8 skanuje `src/Sim` razem z `obj/`.** Komenda jest
  uruchamialna i stąd stoi w kategorii pierwszej, ale na drzewie po `dotnet build`
  wypisuje cztery fałszywe wiersze `BRAK TESTU` dla plików wygenerowanych
  (`Sim.AssemblyInfo.cs`, `.NETCoreApp,Version=v10.0.AssemblyAttributes.cs` w `obj/Debug`
  i `obj/Release`), choć blok obiecuje „po zadaniu ma wypisać zero wierszy". Blok jest
  zapisem historycznym pozycji zrobionej, więc jego poprawka jest poza zakresem.
- **`RequiredNumber` w `Program.cs` mówi `line` niezależnie od polecenia** — stąd
  `BŁĄD: line wymaga --limit-kmh` przy poleceniu `budget`. Komunikat wskazuje na
  niewłaściwe polecenie.
- **`budget --trains 1,2,4,8,32` melduje `N_max=1`** — trzydzieści dwa zgłoszone
  składy, jeden faktycznie na planie. Liczba w kolumnie `N_zgł` nie jest liczbą
  składów, które biegły.
- **`grep -cE '^\s\*FAIL'` NIE jest sprawdzeniem zieloności zestawu.** Moduł, który
  nie daje się zaimportować (błąd składni), nie produkuje ani jednego wiersza `FAIL`
  ani wiersza `N/M przeszło`; `test_all.py` kończy się wtedy kodem 1, a sam grep
  pokazuje 0 i wygląda jak zielono. Zmierzone w tej sesji na własnym module.
  **Wyrocznią jest kod wyjścia procesu**, nie liczba dopasowań grepa.

## 5. Czego ta pozycja nie robi

Nie zmienia kodu, żeby komenda z bloku zaczęła działać — to blok ma opisywać kod,
a nie odwrotnie. Nie poprawia bloków pozycji zrobionych. Nie uruchamia komend
wymagających sieci (`fetch_gtfs.py`) ani trwających dłużej niż kilka minut
(pełne przeglądy mutacyjne) — dla nich rozstrzygnięte zostało wyłącznie to, że
**dają się** uruchomić: `--only` w każdej z dwunastu wymienionych postaci przyjmuje
argument i wypisuje listę mutacji.
