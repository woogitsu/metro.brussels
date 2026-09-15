# 6.D214 — dwa urwane, jedno niewidoczne i podłoga dwadzieścia trzy poniżej stanu

**15.09.2026**, na `9f717da`. Wejście: `tests/Game.Tests/UiTextTests.cs`
(`WzorzecToStringZArgumentem`, `WzorzecToStringBezArgumentu`), `tools/tests/*.py`,
`tests/Sim.Tests/`, `src/Game/FirstRun.cs`,
`reports/6d199-jedno-wywolanie-dwa-korpusy-i-postac-ktorej-skan-nie-widzi.md` §7.

## 1. Ile czytników ma ten idiom: DWA, i oba już znane

Skan po wszystkich regeksach w `tools/**/*.py`, `tests/**/*.cs` i `src/**/*.cs`,
szukający klasy znaków z `\w` i kropką, z kwantyfikatorem, przed **escapowaną kropką**:

```
tests/Game.Tests/UiTextTests.cs:4207  new(@"([\w.]+)\.ToString\(\s*\)", …)
tests/Game.Tests/UiTextTests.cs:4392  new(@"([\w.]+)\.ToString\(\s*[^)\s]", …)
```

**Dwa wystąpienia, oba w jednym pliku, oba to czytniki z 6.D199.** Sprawdzone też trzy
inne zapisy tej samej myśli (`\w+(?:\.\w+)*`, `[A-Za-z_][\w.]*`, sam `[\w.]+`
w dowolnej pozycji) — poza tymi dwoma **nie ma ani jednego**. Obawa z pola pozycji
(„wzorzec jest idiomem, nie pomysłem jednego czytnika") jest więc **zmierzona jako
nieuzasadniona**: idiom nie rozlał się po drzewie.

## 2. Zgłoszenia urwane dziś: DWA, oba w `FirstRun.cs`

| adres | zgłoszenie starego czytnika |
|---|---|
| `FirstRun.cs:2382` | `.StopErrorM` |
| `FirstRun.cs:2447` | `.StopErrorM` |

Zero urwanych w `src/Sim/`. Diagnoza z 6.D208 potwierdza się co do znaku: urwanie robi
**indeksator**, nie przeniesienie wiersza.

## 3. Rozstrzygnięcie: POPRAWIĆ, i to jest wynik pomiaru, nie odwagi

Pole ostrzegało, że poszerzenie wzorca „daje nazwy DŁUŻSZE, ale nie POPRAWNIEJSZE".
Poszerzenie, które tu wszedło, nie jest o długości — jest **strukturalne**: człon
wyrażenia w C# może nieść indeksator, więc wzorzec opisuje człon
(`\w+(?:\[…\]|\(…\))?`), a nie liczbę znaków. Zmierzone przed zmianą:

| | zgłoszeń | różniących się |
|---|---:|---:|
| `src/Game/` bez argumentu | 3 → 3 | 0 |
| `src/Game/` z argumentem | 18 → 18 | **2** |
| `src/Sim/` bez argumentu | 3 → 3 | 0 |
| `src/Sim/` z argumentem | 5 → 5 | 0 |

Obie różnice na korzyść: `.StopErrorM` → `_line.Calls[^1].StopErrorM` oraz
`_stations.Calls[^1].StopErrorM`.

**I to jest szkoda, którą urwanie robiło naprawdę:** te dwa wyrażenia **nie są tym
samym wyrażeniem**, a stary czytnik zwijał je do jednego napisu. Komunikat bramki nie
odróżniał więc dwóch różnych miejsc — a istnieje po to, żeby nie trzeba było wracać do
pliku i szukać ręcznie. Liczby były poprawne, jak mówiło pole; **rozróżnialność
nie była**.

## 4. Trzeci przypadek, innej klasy: NIEWIDOCZNY, nie urwany

Znaleziony przy budowaniu kontroli negatywnej, nie szukany.
`SignallingPlan.cs:216` niesie

```csharp
Units.MpsToKmh(PermittedSpeedMps).ToString("R", CultureInfo.InvariantCulture)
```

i dla **obu** czytników — starego i poprawionego o indeksator — jest **niewidoczny**:
przed `.ToString` stoi `)`, więc dopasowanie nie zaczyna się w ogóle. To inna klasa niż
urwanie: tam czytnik mówi za mało, tu **nie mówi nic**.

Poszerzenie członu o `\([^()]*\)` dodaje **dokładnie to jedno** zgłoszenie i nie rusza
żadnego z pozostałych 52. Weszło, bo zmierzone.

**Granica, która zostaje:** nawiasy **zagnieżdżone** (`f(g(x)).ToString()`) nadal są
niewidoczne. Dziś takiego wyrażenia w `src/` nie ma, a kontrola przyrządu **wykonuje**
ten przypadek, żeby granica była zmierzona, a nie opowiedziana.

## 5. Moja własna podłoga stała 23 poniżej stanu — i nie zapalała się

Pierwsza wersja bramki miała `MinimumZgloszenToString = 30`, bo policzyłem dwa katalogi
(`src/Game/` 3 + 18, `src/Sim/` 3 + 6). Czytnik chodzi po **trzech**: w `src/Sim.Runner/`
jest jeszcze 1 + 22. Stan faktyczny to **53**.

Skutek zmierzyłem, zamiast go przewidzieć: przy podłodze 30 **cofnięcie wzorca nie
zapalało niczego** — wariant bez nawiasu daje 52, goły `\w+` też 52, a 52 ≥ 30. Zapas
w podłodze jest dokładnie tym, co odbiera bramce zdolność wykrywania. Po ustawieniu na
53 **każde z trzech cofnięć zapala obie bramki**.

Osobno warte zapisania: **kontrola „czy zgłoszenie zaczyna się od kropki" NIE wykrywa
cofnięcia do gołego `\w+`** — taki wzorzec daje `StopErrorM` bez kropki wiodącej, czyli
nazwę niepełną, ale wyglądającą na całą. Wykrywa to dopiero podłoga i kontrola
przyrządu. Bramka na kształcie zgłoszenia jest więc słabsza niż bramka na liczbie,
i to jest odwrotnie, niż wyglądało przy pisaniu.

## 6. Kontrole negatywne

Baza: **311/311** w `Game.Tests`, **662/662** w `Sim.Tests`, **2485/2485** w zestawie
Pythona. Po każdej `md5sum -c` na dwóch plikach: `OK`.

| | podstawienie | czerwonych testów |
|---|---|---:|
| KN-1 | człon cofnięty do `[\w.]+` (stan sprzed pozycji) | **2** |
| KN-2 | człon cofnięty do `\w+(?:\[…\])?` (bez nawiasu okrągłego) | **2** |
| KN-3 | człon cofnięty do gołego `\w+` | **2** |
| KN-4 | czytnik oślepiony całkowicie | **6** |
| KN-5 | nowe wywołanie z indeksatorem dołożone do `src/Game/` | bramka urwania **zielona** — nowy czytnik czyta je poprawnie |

**KN-5 jest tą, o którą prosiło pole „Weryfikacja"** — wyrażenie, na którym dzisiejszy
czytnik ma NIE zwrócić nazwy urwanej. Nie zwraca. (Przy okazji zapala trzy bramki
liczbowe, bo dołożenie czegokolwiek do `src/Game/` rusza pięć przypiętych liczb — to
samo zjawisko, które 6.D197 opisało przy swojej KN-1b.)

## 6a. Bramka projektu złapała mnie w trakcie — i to jest szósta pozycja kolejki

`test_every_unread_csharp_constant_is_justified` zapaliło się na `CzlonWyrazenia`:
stała jest czytana **dwa razy**, w obu wzorcach, ale **wyłącznie przez interpolację
napisu**, a skan szuka nazwy jako osobnego słowa. Dla niego wygląda dokładnie jak
martwa — a jego komunikat zachęca do usunięcia, które zepsułoby oba czytniki.

Wpis w `UZASADNIONE` zamyka sprawę dla tej jednej stałej i **nie mówi nic
o pozostałych**; ile ich jest, nie policzył nikt. Wpisane jako **6.D225**. To pierwszy
wpis na tej liście — do dziś była pusta i to też był wynik pomiaru, nie założenie.

Pełne przebiegi: `dotnet test tests/Game.Tests` — **311/311**, `dotnet test tests/Sim.Tests` — **662/662**, `python3 tools/tests/test_all.py` — **2485/2485**.

## 7. Czego świadomie nie zrobiłem

- **Nie poszerzyłem wzorca o znak nowego wiersza** — pole tego zabraniało, a pomiar
  6.D208 pokazał, że wieloliniowość nie jest przyczyną niczego z tych trzech przypadków.
- **Nie zmieniłem klasyfikacji ani układu wierszy w `src/Game/`.**
- **Nie domknąłem nawiasów zagnieżdżonych** — dziś w drzewie ich nie ma, a wzorzec
  regularny ich nie obejmie; to wymagałoby rozbioru składni, czyli decyzji o zależności.

## 8. Zauważone, nie tknięte

- **`src/Sim.Runner/` ma 23 z 53 zgłoszeń**, czyli prawie połowę, a żadna pozycja
  z rodziny 6.D199–6.D214 nigdy o tym katalogu nie mówiła. Nie sprawdzałem, czy
  któreś z nich stoi na wyliczeniu.
- Maska zamienia literał na spacje, więc `x.ToString("0.0")` — argument będący
  **samym** literałem — czyta się po masce jak wywołanie BEZ argumentu. W `src/` dziś
  takiej postaci nie ma (wszystkie 46 wywołań z argumentem mają obok literału przecinek
  albo nazwę), ale gdyby powstała, trafiłaby do niewłaściwego kubełka.
