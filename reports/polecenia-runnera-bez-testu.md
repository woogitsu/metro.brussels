# Osiem poleceń `Sim.Runner` bez testu kodu wyjścia — pomiar, testy i kontrole negatywne

**Zmierzone 06.09.2026 na commicie:** `08d12b689b5a03b6f307ba46b4eb5134d89b882f`

Pozycja 6.A9, bliźniak 6.A8 po stronie CLI. Blok kolejki mówił o ośmiu poleceniach
`src/Sim.Runner/Program.cs` (`drive`, `replay`, `compare`, `axis`, `parity`, `braking`,
`line`, `budget`), z których nazwę wymienia „jakikolwiek plik w `tests/Sim.Tests/`
tylko dla `axis`". Pomiar poniżej to potwierdza — i pokazuje, że nawet to jedno
trafienie jest przypadkowe, nie testem CLI. Rozbiór argumentów i kod wyjścia wszystkich
ośmiu poleceń nie miały żadnego pokrycia: testy istniejące wołają metody rdzenia
(`TrackAxis.FromJson`, `LineRun.Run`, `LineBudget.Measure`, …) bezpośrednio, z pominięciem
`Program.Main` — literówka w nazwie przełącznika albo odwrócony warunek przeszłyby
cały zestaw.

Kodu w `src/Sim.Runner/` ten commit nie zmienia ani o znak: mutacje kontroli negatywnych
były nakładane i zdejmowane skryptem podczas weryfikacji, a `git diff --stat src/` po
wszystkim jest pusty. Jedyny nowy plik to `tests/Sim.Tests/RunnerCommandTests.cs`.

---

## 1. Pomiar przed

```bash
$ grep -rln '"drive"' tests/Sim.Tests/    # (bez wyników)
$ grep -rln '"replay"' tests/Sim.Tests/   # (bez wyników)
$ grep -rln '"compare"' tests/Sim.Tests/  # (bez wyników)
$ grep -rln '"axis"' tests/Sim.Tests/
tests/Sim.Tests/CabProtectionTests.cs
$ grep -rln '"parity"' tests/Sim.Tests/   # (bez wyników)
$ grep -rln '"braking"' tests/Sim.Tests/  # (bez wyników)
$ grep -rln '"line"' tests/Sim.Tests/     # (bez wyników)
$ grep -rln '"budget"' tests/Sim.Tests/   # (bez wyników)
```

Jedyne trafienie — `axis` w `CabProtectionTests.cs` — jest przypadkowym dopasowaniem
literału niezwiązanego z rozbiorem CLI (ten plik nie importuje `MetroBxl.Sim.Runner`
i nigdy nie woła `Program.Main`), co pokrywa się z opisem w bloku 6.A9. Zero plików
testowych woła `MetroBxl.Sim.Runner.Program` przed tym zadaniem:

```bash
$ grep -rln "Program.Main\|MetroBxl.Sim.Runner" tests/Sim.Tests/
tests/Sim.Tests/LineBudgetTests.cs
```

Jedyne odwołanie do przestrzeni nazw runnera to `using MetroBxl.Sim.Runner;`
w `LineBudgetTests.cs` — potrzebne wyłącznie po to, żeby zobaczyć `LineBudgetScenario`
i `LineBudget`, klasy rdzenia pomiaru, a nie CLI. `Program` w tym pliku nie występuje.

**Liczba testów przed zadaniem** (nie 494 z pola *Weryfikacja* — blok kolejki mówił
„większej niż dzisiejsze 494", ale to liczba z innego commitu; commit, na którym
faktycznie startuje ta gałąź, ma już inną historię):

```
$ dotnet test tests/Sim.Tests -c Release
Passed!  - Failed:     0, Passed:   518, Skipped:     0, Total:   518, Duration: 10 s
         - MetroBxl.Sim.Tests.dll (net10.0)
```

## 2. Co powstało

Jeden nowy plik: `tests/Sim.Tests/RunnerCommandTests.cs`, klasa `RunnerCommandTests`,
10 testów. Wchodzi wyłącznie przez `Program.Main(string[])` — publiczny punkt wejścia
runnera — z przechwyceniem `Console.Out`/`Console.Error` w `StringWriter` i zwróceniem
strumieni na miejsce w `finally`. Żaden test nie sprawdza treści telemetrii ani liczby
o sieci: patrzy wyłącznie na kod wyjścia i, dodatkowo, na fragment komunikatu — żeby
zielony wynik nie mógł wyjść z niewłaściwego powodu.

| polecenie | scenariusz testu | oczekiwany kod wyjścia | testów przed | testów po |
|---|---|---|---|---|
| `drive` | brak argumentów (wszystkie opcjonalne) → poprawne wywołanie | 0 | 0 | 1 |
| `replay` | brak `--keys` | 1 | 0 | 1 |
| `compare` | brak dwóch plików pozycyjnych | 2 | 0 | 1 |
| `axis` | brak `--axis` | 1 | 0 | 1 |
| `parity` | brak argumentów (nie ma żadnych) → poprawne wywołanie | 0 | 0 | 1 |
| `braking` | brak argumentów (nie ma żadnych) → poprawne wywołanie | 0 | 0 | 1 |
| `line` | brak `--axis` (pierwszy wymagany w kolejności rozbioru) | 1 | 0 | 1 |
| `budget` | brak `--axis` (pierwszy wymagany w kolejności rozbioru) | 1 | 0 | 1 |
| *(nazwa spoza ósemki)* | `nie-ma-takiego-polecenia` | 2 | 0 | 1 |
| *(dodatkowo, poza minimum zadania)* | brak argumentów w ogóle | 2 | 0 | 1 |

Trzy polecenia (`drive`, `parity`, `braking`) nie mają **żadnego** argumentu
wymaganego — dla nich „test na kod wyjścia" jest testem poprawnego wywołania (0),
nie odmowy, bo brak wymaganego argumentu nie ma tu czego dotyczyć (dokładnie to mówi
pole *Skończone, gdy*: „przy braku wymaganego argumentu **tam, gdzie polecenie
argumenty ma**"). Pięć poleceń (`replay`, `compare`, `axis`, `line`, `budget`) ma
argumenty wymagane bez wartości domyślnej — dla nich test sprawdza odmowę przy ich
braku. Dziewiąty test pokrywa „nazwę polecenia, którego nie ma" wprost z pola
*Skończone, gdy*; dziesiąty (brak argumentów w ogóle) jest dodatkiem tej samej rodziny,
tanim do dopisania obok, ale nie był wymagany.

`service-day` **nie jest** w tym pliku — blok 6.A9 wymienia dokładnie osiem poleceń
i `service-day` (dziewiąte w `switch`) nie jest jednym z nich; patrz §5.

### Znalezisko, nie poprawka: dwie różne liczby dla tej samej kategorii błędu

`compare` sprawdza liczbę argumentów ręcznie (`args.Length < 3`) i zwraca **2**.
Pozostałe cztery odmowy z argumentami wymaganymi (`replay`, `axis`, `line`, `budget`)
rzucają `ArgumentException`, którą łapie wspólny handler w `Program.Main` i zwraca
**1**. Ta sama kategoria błędu — brak wymaganego argumentu — kończy się dwiema różnymi
liczbami zależnie od tego, KTÓRE polecenie się woła. Test `Compare_bez_dwoch_plikow_
konczy_sie_kodem_dwa` i cztery testy sąsiednie razem PRZYBIJAJĄ tę niespójność liczbą,
a nie opisem. Zgodnie z polem *Poza zakresem* pozycji 6.A9 — to zgłoszenie, nie poprawka
przy okazji.

## 3. Kontrole negatywne — wykonane, w czterech seriach

Każda seria: mutacja w `src/Sim.Runner/Program.cs` → `dotnet test --filter
"FullyQualifiedName~RunnerCommandTests"` → wklejone wyjście → cofnięcie mutacji.
Cztery serie pokrywają wszystkie dziesięć testów.

### Seria A — wspólny handler wyjątków (`return 1;` → `return 3;`)

Dotyczy czterech testów opartych o `ArgumentException`: `replay`, `axis`, `line`,
`budget`.

```
  Failed Replay_bez_wymaganego_argumentu_konczy_sie_kodem_jeden [11 ms]
   Assert.AreEqual failed. Expected:<1>. Actual:<3>.
  Failed Axis_bez_wymaganego_argumentu_konczy_sie_kodem_jeden [1 ms]
   Assert.AreEqual failed. Expected:<1>. Actual:<3>.
  Failed Line_bez_wymaganego_argumentu_konczy_sie_kodem_jeden [2 ms]
   Assert.AreEqual failed. Expected:<1>. Actual:<3>.
  Failed Budget_bez_wymaganego_argumentu_konczy_sie_kodem_jeden [1 ms]
   Assert.AreEqual failed. Expected:<1>. Actual:<3>.

Failed!  - Failed:     4, Passed:     6, Skipped:     0, Total:    10, Duration: 146 ms
```

### Seria B — rozbiór `compare` (`return 2;` → `return 0;`)

```
  Failed Compare_bez_dwoch_plikow_konczy_sie_kodem_dwa [8 ms]
   Assert.AreEqual failed. Expected:<2>. Actual:<0>.

Failed!  - Failed:     1, Passed:     9, Skipped:     0, Total:    10, Duration: 141 ms
```

### Seria C — nieznane polecenie i brak argumentów w ogóle (oba `return 2;` → `return 0;` naraz)

```
  Failed Nieznane_polecenie_konczy_sie_kodem_dwa [7 ms]
   Assert.AreEqual failed. Expected:<2>. Actual:<0>.
  Failed Brak_argumentow_w_ogole_konczy_sie_kodem_dwa [< 1 ms]
   Assert.AreEqual failed. Expected:<2>. Actual:<0>.

Failed!  - Failed:     2, Passed:     8, Skipped:     0, Total:    10, Duration: 132 ms
```

### Seria D — poprawne wywołanie trzech poleceń bez argumentów (trzy `return 0;`/`return failed ? 1 : 0;` naraz)

`Drive` (`return 0;` → `return 9;`), `Parity` (`return failed ? 1 : 0;` →
`return failed ? 1 : 9;`), `Braking` (`return 0;` → `return 9;`) — trzy niezależne
mutacje w jednym przebiegu.

```
  Failed Drive_bez_argumentow_konczy_sie_kodem_zero [50 ms]
   Assert.AreEqual failed. Expected:<0>. Actual:<9>.
  Failed Parity_bez_argumentow_konczy_sie_kodem_zero [7 ms]
   Assert.AreEqual failed. Expected:<0>. Actual:<9>.
  Failed Braking_bez_argumentow_konczy_sie_kodem_zero [16 ms]
   Assert.AreEqual failed. Expected:<0>. Actual:<9>.

Failed!  - Failed:     3, Passed:     7, Skipped:     0, Total:    10, Duration: 155 ms
```

Cztery serie × (4 + 1 + 2 + 3) = 10 testów — dokładnie tyle, ile ich jest. Każdy z
dziesięciu testów padł raz, na własnej mutacji, i tylko na niej (żadna seria nie
zepsuła testu spoza swojego zestawu).

### Sprzątanie

```
$ git diff --stat src/
(pusto)
```

## 4. Pomiar po

```
$ dotnet test tests/Sim.Tests -c Release
Passed!  - Failed:     0, Passed:   528, Skipped:     0, Total:   528, Duration: 8 s
         - MetroBxl.Sim.Tests.dll (net10.0)
```

518 → 528, czyli **10 dopisanych testów**, jak w tabeli §2.

```
$ python3 tools/tests/test_all.py 2>&1 | tail -3
  ok   test_xml_doc_scan_actually_reads_the_sources

  1709/1709 przeszło
```

## 5. Czego świadomie nie zrobiono

* **`service-day` nie ma tu testu.** Blok 6.A9 wymienia dokładnie osiem poleceń
  (`drive`, `replay`, `compare`, `axis`, `parity`, `braking`, `line`, `budget`) —
  `service-day`, dziewiąte w `switch` `Program.Main`, nie jest jednym z nich. Poza
  zakresem pola *Wejście/Wyjście* tej pozycji, nie dopisane przy okazji.
* **Kod wyjścia `compare` (2) wobec reszty odmów (1) nie jest ujednolicony.** Opisane
  w §2 jako znalezisko — zmiana zachowania `Program.cs` jest wprost poza zakresem
  6.A9 („test przybija stan, jaki jest; błąd rozbioru ujawniony testem jest
  zgłoszeniem, nie poprawką przy okazji").
* **Drugi wymagany argument `line`/`budget` (np. `--limit-kmh` przy podanym
  `--axis`) nie ma osobnego testu.** Test sprawdza pierwszy brakujący argument
  w kolejności rozbioru (zawsze `--axis` dla obu poleceń) — to wystarcza do pokrycia
  kodu wyjścia „brak wymaganego argumentu" z pola *Skończone, gdy*; wyczerpujące
  sprawdzenie wszystkich kombinacji brakujących flag nie było wymogiem zadania.
* **`tools/tests/test_backlog.py` i wiersze `docs/TASKS.md` poza `6.A9` nie są
  ruszone** — zgodnie z poleceniem, dotknięty jest wyłącznie wiersz tej pozycji.

## 6. Co zauważono przy okazji, ale nie tknięto

* **Liczba „494" z pola *Weryfikacja* pozycji 6.A9 jest już nieaktualna** na commicie,
  na którym faktycznie wykonano to zadanie (`08d12b6…`, 518 przed, nie 494) — dokładnie
  to, przed czym ostrzega instrukcja nadrzędna („dziś trzy pozycje okazały się
  nieaktualne"). Nie zmieniono treści bloku 6.A9 w `docs/TASKS.md` poza dopisaniem
  adnotacji „ZROBIONE" — właściciel kolejki decyduje o przepisywaniu pól historycznych.
* **`LineBudgetTests.cs` importuje `MetroBxl.Sim.Runner`, ale nigdy nie woła
  `Program`** — import jest tam wyłącznie po klasy pomiaru (`LineBudgetScenario`,
  `LineBudget`), nie po CLI. Widoczne w §1, nieruszone: to plik z innego zadania (5.7).
* **`Unknown(string)` i gałąź `args.Length == 0`** w `Program.Main` zwracają ten sam
  kod (2) dwiema oddzielnymi ścieżkami kodu, co seria C w §3 pokazuje wprost mutując je
  osobno. Nie jest to niespójność w sensie §2 — obie ścieżki reprezentują tę samą
  kategorię odmowy („nie wiadomo, co uruchomić") i dają tę samą liczbę; zanotowane,
  bo dwa niezależne miejsca w kodzie dające tę samą stałą to coś, co następna zmiana
  mogłaby rozjechać po cichu, gdyby zmieniła jedno bez drugiego.

## 7. Domknięcie luki — 6.A10 (06.09.2026)

Dziewiąte polecenie, `service-day`, wymienione w §5 jako świadomie nieruszone, ma teraz
własne testy kodu wyjścia w `RunnerCommandTests.cs`: brak `--timetable` (kod 1, komunikat
zawiera „--timetable") i niepoprawny format `--at` (kod 1, komunikat zawiera „HH:MM:SS"),
oba przez ten sam wspólny handler wyjątków co `replay`/`axis`/`line`/`budget`. Obie
kontrole negatywne wykonane osobno (mutacja treści komunikatu wyjątku, nie kodu wyjścia
handlera — bo ten drugi jest współdzielony z czterema testami już istniejącymi
i mutacja tam wywróciłaby więcej niż jeden test): każda zepsuła wyłącznie swój jeden
test, reszta zestawu została zielona, kod źródłowy przywrócony bit w bit po każdej
serii (`git diff --stat src/` puste na końcu).

Dwa znaleziska z §2 i §6 powyżej **nie zostały tym ruszone** — pozycja 6.A10 przybija
stan, nie poprawia go:

* `compare` nadal zwraca **2** tam, gdzie reszta odmów z argumentami wymaganymi
  (`replay`, `axis`, `line`, `budget`, a teraz i `service-day`) zwraca **1** przez
  wspólny handler wyjątków.
* `Unknown(string)` i gałąź pustych argumentów w `Program.Main` nadal dają tę samą
  stałą (2) dwiema niezależnymi ścieżkami kodu, nie jedną.
