# Swoistość igły asercji wobec zamkniętej rodziny komunikatów runnera (6.A33)

**Zmierzone 07.09.2026 na commicie:** `2ffb0b00cce5a66d688647ccb603c1011416aa6f`
(baza gałęzi `claude/6a33-swoistosc-igly`, czyli `main` po scaleniu #386).
**Dotyczy:** `tools/tests/test_needle_specificity.py` (nowa bramka),
`tests/Sim.Tests/RunnerCommandTests.cs` (osiem wzmocnionych igieł), `docs/TASKS.md`.
**Po co:** `reports/audyt-asercji.md` §7 nazwał ten pomiar **rozstrzygającym**
i świadomie go nie wykonał. Tu jest wykonany i zamknięty bramką.

## 1. Werdykt, na początku, bo pozycja o niego prosiła wprost

Przyrząd czyta `src/Sim.Runner/Program.cs` i `tests/Sim.Tests/RunnerCommandTests.cs`
jako tekst, bez `dotnet`, i dla każdej igły `StringAssert.Contains` liczy, ile
komunikatów `Program.cs` ją zawiera.

| | PRZED (`2ffb0b0`) | PO (ten commit) |
|---|---|---|
| różnych igieł | **68** | **68** |
| swoistych (dokładnie 1 komunikat) | 20 | **28** |
| niejednoznacznych (>1 komunikat) | **15** | **7** |
| z tego zgłoszonych przez bramkę | — | **0** |
| z tego z wpisem na liście wyjątków | — | **7** (zapadka `MAX_JUSTIFIED_NEEDLES = 7`) |
| bez ani jednego dopasowania | 33 | 33 (zapadka `MAX_UNMATCHED_NEEDLES = 33`) |

Igły niejednoznaczne PRZED tym commitem, w całości:

```
PRZED (origin/main): igiel 68, swoistych 20, niejednoznacznych 15, bez dopasowania 33
     7  'budget'
     6  'step'
     6  '[BUDŻET]'
     5  '[LINIA]'
     4  '--axis'
     3  '[PORÓWNANIE]'
     3  '--trains'
     3  '--limit-kmh'
     3  '--at'
     2  'nie przyjmuje postaci'
     2  'line'
     2  'HH:MM:SS'
     2  '--timetable'
     2  '--steps'
     2  '--keys'

PO (ten commit): igiel 68, swoistych 28, niejednoznacznych 7, bez dopasowania 33
     7  'budget'
     6  'step'
     3  '--trains'
     3  '--limit-kmh'
     3  '--at'
     2  'line'
     2  '--steps'
```

Osiem igieł wzmocnionych w teście, siedem z wpisem z powodem, zero przemilczanych.

## 2. Liczby z wiersza kolejki NIE dały się odtworzyć, i to jest znalezisko, nie usterka

Wiersz `6.A33` i `reports/kolejka-uzupelnienie-drugie.md` §3 podają pomiar z `a4a3975`:
**209** komunikatów wielowyrazowych, **16 z 68** igieł niejednoznacznych, a w tabeli
`line` w **11** komunikatach, `budget` w 10, `--limit-kmh` w 9, `step` w 8, `[BUDŻET]`
i `[LINIA]` po 6. Kodu tamtego przyrządu nie ma w drzewie — jest w raporcie samo
wyjście — więc odtwarzałem definicję po definicji, na **tym samym** commicie
`a4a3975`, żeby różnica nie brała się z tego, że `Program.cs` od tamtej pory urósł
o 41 wierszy.

**Liczba igieł zgadza się dokładnie: 68 na `a4a3975` i 68 dziś.** Nie zgadza się
liczba komunikatów ani żaden wiersz tabeli. Sprawdzone definicje „komunikatu"
i wynikające z nich liczniki dla `line` / `budget` / `--limit-kmh` / `step` /
`[BUDŻET]` / `[LINIA]`:

| definicja komunikatu | ile | line | budget | --limit-kmh | step | [BUDŻET] | [LINIA] |
|---|---|---|---|---|---|---|---|
| **cel z wiersza kolejki** | **209** | **11** | **10** | **9** | **8** | **6** | **6** |
| literał, wielowyrazowy | 155 | 1 | 6 | 2 | 4 | 6 | 5 |
| literał, każdy | 390 | 4 | 11 | 8 | 13 | 6 | 5 |
| literał + wiersze wypisu pomocy | 180 | 2 | 7 | 5 | 5 | 6 | 5 |
| wiersz źródła z cudzysłowem | 320 | 4 | 10 | 9 | 10 | 6 | 5 |
| instrukcja (cięcie na `;`) | 166 | 14 | 15 | 11 | 12 | 6 | 6 |
| grupa literałów zszytych `+` | 152 | 5 | 11 | 7 | 9 | 6 | 5 |
| wiersze komentarzy `///` | 207 | 9 | 4 | 5 | 1 | 0 | 0 |
| komentarze `///` i `//` razem | 428 | 13 | 9 | 12 | 3 | 0 | 1 |
| argumenty wypisów i wyjątków | 90 | 2 | 7 | 3 | 5 | 6 | 5 |

Ani jedna nie daje `line` = 11 przy `budget` = 10, `--limit-kmh` = 9 i `step` = 8
naraz; kolejność sama jest tu rozstrzygająca — w każdej definicji opartej na
literałach `line` wypada NAJSŁABIEJ z tej czwórki, bo napis `line` stoi w tym pliku
w czterech literałach, a `step` w trzynastu. Werdykt: **liczby z wiersza kolejki są
pomiarem innego przyrządu, którego nie umiem odtworzyć, i nie przepisuję ich** —
mają datę (`docs/04-conventions.md`). To, co stoi w tym raporcie, jest pomiarem
przyrządu, który w drzewie leży i który można wywrócić kontrolą.

Jedno da się o tamtym pomiarze powiedzieć z pewnością: **jego 68 to te same 68.**
Zbiór igieł jest identyczny, więc różnica siedzi wyłącznie w definicji komunikatu.

## 3. Czym jest komunikat w tej bramce — i dlaczego są trzy szczeble

**Komunikat to maksymalna grupa literałów zszytych `+`, wielowyrazowa.** Zszycie
jest konieczne: jedno zdanie odmowy stoi w tym pliku regularnie w dwóch albo trzech
literałach obok siebie i policzenie ich osobno zmyśliłoby niejednoznaczność, której
nie ma. Warunek wielowyrazowości też: literał jednowyrazowy w `Program.cs` to nazwa
opcji z tabeli, nagłówek CSV albo klucz słownika, nie zdanie do czytania.

**Czego bramka nie robi, świadomie: nie rozwiązuje interpolacji.** Komunikat
`$"{command} nie rozumie wartości {name}: "` daje przy różnych argumentach różne
zdania. Igła `line nie rozumie wartości --limit-kmh` — najlepsza, jaką ten test
mógłby mieć — nie pasuje więc do ŻADNEGO literału, choć runner dokładnie to wypisuje.
Takich igieł jest **33 z 68** i bramka ich nie zgłasza, bo nie ma o nich nic
prawdziwego do powiedzenia.

Właśnie dlatego ma trzeci szczebel: **zapadkę na ich liczbę**. Bez niej najtańszym
sposobem uciszenia szczebla pierwszego byłoby przepisanie igły na tekst, którego
w literałach nie ma wcale, czyli zamiana niejednoznaczności na niewidzialność. Ze
zapadką taka podmiana wymaga podniesienia stałej w tym samym commicie, czyli w diffie.

## 4. Osiem igieł wzmocnionych — w teście, nie w programie

Pole „Poza zakresem" zabrania ruszać treść komunikatów `Program.cs`, więc rozjazd
naprawia się po stronie testu. Każda nowa igła stoi w komunikacie, który ten test
NAPRAWDĘ oglądа — sprawdzone przebiegiem `dotnet test`, nie czytaniem kodu.

| test | igła PRZED | ile | igła PO | ile |
|---|---|---|---|---|
| `Replay_bez_wymaganego_argumentu_konczy_sie_kodem_jeden` | `--keys` | 2 | `replay wymaga --keys` | 1 |
| `Axis_bez_wymaganego_argumentu_konczy_sie_kodem_jeden` | `--axis` | 4 | `axis wymaga --axis` | 1 |
| `ServiceDay_bez_wymaganego_argumentu_konczy_sie_kodem_jeden` | `--timetable` | 2 | `service-day wymaga --timetable` | 1 |
| `ServiceDay_z_niepoprawnym_formatem_at_konczy_sie_kodem_jeden` | `HH:MM:SS` | 2 | `czas ma mieć postać HH:MM:SS` | 1 |
| `Prawdziwy_plan_nadal_przechodzi` | `[BUDŻET]` | 6 | `[BUDŻET] oś ` | 1 |
| `Postac_z_rownosciem_nazywa_postac_a_nie_nieznana_opcje` | `nie przyjmuje postaci` | 2 | `nie przyjmuje postaci --opcja=wartość. Opcję` | 1 |
| `Opcja_podana_raz_nadal_przechodzi` i `Wartosci_znanych_opcji_nie_licza_sie_jako_czlony_pozycyjne` | `[LINIA]` | 5 | `[LINIA] największy błąd zatrzymania` | 1 |
| trzy testy `compare` drugiego kierunku | `[PORÓWNANIE]` | 3 | `[PORÓWNANIE] wierszy=` | 1 |

Dwa wzmocnienia są ciekawsze od pozostałych i dlatego stoją tu z powodem:

- `nie przyjmuje postaci` pasowało do **obu** wariantów odmowy 6.A22 — tego dla opcji
  z wartością i tego dla FLAGI, która wartości nie bierze. Nowa igła bierze zdanie
  dalej, do `. Opcję`, czyli dokładnie do miejsca, w którym te dwa warianty się
  rozchodzą; test flagi już wcześniej miał igłę swoistą
  (`jest flagą i wartości nie bierze`).
- `[BUDŻET]`, `[LINIA]` i `[PORÓWNANIE]` to znaczniki wierszy informacyjnych, których
  każde polecenie wypisuje po kilka. Asercja „na stdout jest jakiś wiersz `[LINIA]`"
  przechodziła też wtedy, gdyby przejazd wypisał sam wiersz śladu i nic więcej;
  po wzmocnieniu mierzy wiersz, który stoi na KOŃCU przejazdu, po wszystkich stacjach.

## 5. Siedem igieł z wpisem z powodem — bo niejednoznaczne z dobrego powodu

Pole „Wyjście" nazwało ten przypadek wprost: „asercja o nazwie polecenia, która ma
pasować do wielu komunikatów, musi być wypisana z powodem, a nie przemilczana".
Wszystkie siedem to nazwy polecenia albo opcji, a nazwa opcji stoi i w wypisie pomocy,
i w każdej odmowie, która o niej mówi.

| igła | ile | dlaczego zostaje |
|---|---|---|
| `budget` | 7 | druga połowa kontroli 6.D20 — test istnieje po to, żeby poprawka z nową sztywną nazwą nie przeszła |
| `step` | 6 | nazwa KOLUMNY telemetrii; stoi obok czterech igieł swoistych tego samego testu |
| `--trains` | 3 | dwie różne role, obie o nazwie opcji, obie treści składane w czasie wykonania |
| `--limit-kmh` | 3 | nazwa opcji w trzech testach, w każdym obok igły swoistej (`abc`, `więcej niż raz`) |
| `--at` | 3 | cała treść testu „odmowa wymienia opcje TEGO polecenia" |
| `line` | 2 | sedno 6.D20: test asertuje NAZWĘ WOŁANEGO POLECENIA, nie treść jednej odmowy |
| `--steps` | 2 | oba dopasowania dotyczą komunikatów INNYCH niż mierzony — mierzony jest interpolowany |

Pełne powody, zdaniem każdy, stoją w `JUSTIFICATIONS` w
`tools/tests/test_needle_specificity.py`; lista jest zamknięta zapadką z obu stron
(`MAX_JUSTIFIED_NEEDLES = 7`), tak jak przy 6.A31.

## 6. Kontrole — WYKONANE, z wklejonym wyjściem

### 6.1 KD-1 (dodatnia): osłabienie igły swoistej wywraca DOKŁADNIE tę bramkę

Igła `axis wymaga --axis` w prawdziwym pliku testu osłabiona z powrotem do `--axis`,
przebieg CAŁEGO zestawu:

```
  FAIL test_a_weakened_needle_lights_up_the_first_rung: igła-przyrząd 'axis wymaga --axis' zniknęła z tests/Sim.Tests/RunnerCommandTests.cs — kontrola dodatnia nie ma czego osłabiać
  FAIL test_every_needle_matches_at_most_one_message_or_is_justified: igła asercji pasuje do więcej niż jednego komunikatu `Program.cs` i nie ma wpisu z powodem — wzmocnij ją w teście albo wpisz na listę: ["'--axis' w 4 komunikatach (test w wierszach [173])"]
  FAIL test_the_verdict_follows_the_program_file: igła-przyrząd 'axis wymaga --axis' nie stoi już w teście albo nie jest swoista (licznik None) — kontrola przyrządu straciła punkt odniesienia
  1939/1942 przeszło
```

Trzy zapalone testy stoją **wszystkie w nowym module** i ani jeden poza nim — to jest
ta „dokładność", o którą prosiło pole „Skończone, gdy". Dwa z nich to własne kontrole
bramki, które tę samą igłę mają za próbkę i mówią to w komunikacie awarii; bez tego
zniknięcie próbki wyglądałoby jak zepsuta bramka. Plik przywrócony, `cmp` z kopią
sprzed mutacji: identyczne.

### 6.2 KD-2: osłabienie do `line`, czyli do igły Z LISTY wyjątków

Pole „Skończone, gdy" żąda osłabienia „do `line`". `line` **jest** na liście wyjątków,
więc szczebel 1 milczy — i to jest cena listy, powiedziana wprost. Zapala się jednak
próg KW, bo zbiór igieł traci jeden element:

```
  FAIL test_the_message_family_and_the_needles_are_both_read_from_the_files: wzorzec złapał 67 różnych igieł, a 07.09.2026 było ich 68
```

A ta sama mutacja w `dotnet test` pada tam, gdzie ma paść — na treści, nie na kształcie:

```
' does not contain string 'line'. .
  Stack Trace:
     at MetroBxl.Sim.Tests.RunnerCommandTests.Axis_bez_wymaganego_argumentu_konczy_sie_kodem_jeden()
Failed!  - Failed:     1, Passed:     0, Skipped:     0, Total:     1
```

### 6.3 KD-3: skasowanie JEDNEGO wpisu z listy wyjątków

Wpis `--steps` usunięty z `JUSTIFICATIONS`, nic więcej:

```
  FAIL test_every_needle_matches_at_most_one_message_or_is_justified: igła asercji pasuje do więcej niż jednego komunikatu `Program.cs` i nie ma wpisu z powodem — wzmocnij ją w teście albo wpisz na listę: ["'--steps' w 2 komunikatach (test w wierszach [861])"]
  FAIL test_the_justification_list_stays_closed: zapadka 7 stoi wyżej niż lista (6) — obniż ją do stanu faktycznego
  8/11 przeszło
```

Zapadka działa w OBIE strony: lista krótsza od zapadki jest awarią tak samo jak
dłuższa. Bez dolnego ostrza zapadka przyjmowałaby nowy wpis bez śladu w diffie.

### 6.4 KU (ujemna): „nie zgłasza" jest rozróżnieniem, nie pustym zbiorem

Igieł swoistych jest **28** i ani jedna nie jest zgłaszana. Mutacja warunku w
`zgloszenia()` z `> 1` na `>= 1`, na prawdziwym pliku bramki:

```
zgloszen przy >= 1 : 28
  przyklady        : ['--coast-from-m', '--headway-s', '--repeats', '--stop-window-m', 'DROGA HAMOWANIA', '[BUDŻET] oś ']
zgloszen przy >= 0 : 61
bez listy wyjatkow, >= 1 : 35
bez listy wyjatkow, >= 0 : 68 z 68 igiel: 68
```

Czyli: przy `>= 1` zbiór zgłoszeń przenosi się z zera na **28**, a przy `>= 0` i ze
zdjętym filtrem listy wyjątków — na **wszystkie 68**, dokładnie jak żądało pole
„Skończone, gdy". Że „wszystkie 68" wychodzi przy `>= 0`, a nie przy `>= 1`, ma jedną
przyczynę i jest nią szczebel 3: **33 igły nie pasują do ani jednego literału**, bo
runner składa te zdania interpolacją (§3). Plik bramki przywrócony, `cmp`: identyczne.

### 6.5 KP (przyrząd): bramka czyta plik, a nie tabelę wpisaną z pamięci

Do `src/Sim.Runner/Program.cs` dopisany DRUGI komunikat z istniejącą igłą
(`"axis wymaga --axis, i to jest drugi komunikat"`, jako stała w klasie, nie jako
komentarz). Licznik tej igły idzie z 1 na 2, a igła trafia do zgłoszeń:

```
  ZGLOSZONA          2  'axis wymaga --axis'                      test l. [173]
  swoistych (dokladnie 1 komunikat): 27
  niejednoznacznych (>1):            8
  bez ani jednego dopasowania:       33 (zapadka 33)
    ZGLOSZONA: 'axis wymaga --axis' w 2 komunikatach

  FAIL test_every_needle_matches_at_most_one_message_or_is_justified: igła asercji pasuje do więcej niż jednego komunikatu `Program.cs` i nie ma wpisu z powodem — wzmocnij ją w teście albo wpisz na listę: ["'axis wymaga --axis' w 2 komunikatach (test w wierszach [173])"]
```

Wewnątrz tej samej kontroli, jednym testem wyżej, stoi jej druga połowa: ten sam
dopisek **w komentarzu** licznika NIE podnosi, bo komentarz maska zamienia na spacje.
Bramka liczy więc kod, nie tekst pliku. `Program.cs` przywrócony, `cmp`: identyczne,
`git diff` bez ani jednego wiersza.

### 6.6 KW (wzorzec): zepsuty czytnik nie może dać zielonej bramki

Progi `MIN_MESSAGES = 97` i `MIN_NEEDLES = 68` istnieją wyłącznie po to. Do tego dwa
testy granicy na wejściu syntetycznym: czytnik igieł odróżnia literał od zmiennej
i widzi wywołanie rozbite na dwa wiersze (jedno takie w tym pliku jest), a czytnik
komunikatów zszywa konkatenację i odrzuca literał jednowyrazowy. Bez nich oba czytniki
mogłyby zwracać pustkę i cały moduł świeciłby zielono.

Osobno `test_the_literal_spans_agree_with_the_mask`: każdy literał widziany przez
`_spany` jest w masce `csharp_test_methods.maska` zamazany znak w znak. Dwa przejścia
po tej samej strukturze rozjeżdżają się po cichu (6.D30), a maska i lista literałów
to dokładnie dwa spojrzenia na jedno drzewo.

## 7. Weryfikacja

```
$ python3 tools/tests/test_all.py
  1942/1942 przeszło
  RAZEM 75.268 s, 1942 testów, 102 modułów
kod=0
```

```
$ dotnet test tests/Sim.Tests
Passed!  - Failed:     0, Passed:   589, Skipped:     0, Total:   589, Duration: 27 s
```

Zestaw narzędzi **1931 → 1942** (jedenaście testów nowego modułu), `dotnet test`
**589 → 589** — wzmocnienie ośmiu igieł nie dodaje ani nie zabiera asercji, tylko
zawęża je do jednego komunikatu. Nowy moduł liczy **0,026 s** na jeden pełny przebieg
licznika (`time.perf_counter()`, średnia z pięciu), czyli **0,44 s** na cały moduł —
przy progu `SUITE_RUNTIME_BUDGET_S = 150.0` nie ruszam żadnej zapadki czasu.

## 8. Czego świadomie NIE zrobiłem

- **Nie przeliczyłem liczb z wiersza kolejki na moje** (209 → 97, 16 → 15). Mają datę
  i cudzy przyrząd; §2 pokazuje dziesięć sprawdzonych definicji i mówi wprost, że
  żadna ich nie odtwarza. Wiersz `6.A33` dostaje adnotację z liczbami mojego pomiaru,
  a treść pierwotna zostaje nietknięta.
- **Nie tknąłem treści ani jednego komunikatu `Program.cs`** — pole „Poza zakresem"
  mówi to wprost, a rozjazd naprawia się w teście. Jedyna zmiana w tym pliku, jaka
  w ogóle zaszła, to dopisek kontroli przyrządu, przywrócony i sprawdzony `cmp`.
- **Nie ruszyłem `tests/Game.Tests`** — to jest 6.D34, z własną zamkniętą rodziną
  komunikatów (`RunPlan`).
- **Nie rozwiązuję interpolacji** i nie udaję, że przyrząd wie, co runner wypisze przy
  konkretnych argumentach. Zamiast tego 33 igły bez dopasowania stoją pod zapadką,
  a granica jest nazwana w docstringu bramki.
- **Nie dopisałem wpisu do `UZASADNIONE` w `tools/tests/test_constant_names.py`.**
  Bramka kolizji nazw zapaliła się na `MAX_JUSTIFICATIONS` — ta nazwa jest już
  w `tools/tests/test_bin_path_framework.py` przy innej wartości (14). Poprawiłem
  NAZWĘ u siebie (`MAX_JUSTIFIED_NEEDLES`), bo tamta jest po prostu za ogólna: nie jest
  to „maksimum usprawiedliwień w ogóle", a maksimum usprawiedliwionych IGIEŁ. Wzorzec
  6.A31 zostaje ten sam, zmienia się jedno słowo w nazwie i nie dotykam cudzej bramki
  (`CLAUDE.md` §4.10).
- **Nie uzupełniałem kolejki.** Bramka zapasu nie zapaliła się przy tym commicie.

## 9. Zauważone przy okazji, nie tknięte

- **Wypis pomocy `Usage()` jest JEDNYM komunikatem i to on stoi za większością
  niejednoznaczności.** Dziewięć z piętnastu igieł PRZED tym commitem pasowało do
  wypisu pomocy — bo `nieznane polecenie:` woła `Usage()` na ten sam strumień, więc
  każda odmowa o nieznanym poleceniu niesie ze sobą nazwy wszystkich opcji runnera.
  Igła będąca nazwą opcji jest z tego powodu niejednoznaczna z definicji, a nie
  z niedbalstwa; nie ma tu nic do naprawienia po stronie testu i dlatego te igły
  dostały powody, nie wzmocnienia.
- **Dwa wywołania `StringAssert.Contains` w `RunnerCommandTests.cs` mają igłę
  w zmiennej** (`zepsuty`, ścieżka pliku tymczasowego), więc z tekstu nie da się
  powiedzieć, jaki to napis, i przyrząd je pomija. Wywołań jest 87, mierzalnych 85.
  To ta sama granica, którą `tools/tests/csharp_assertions.py` opisuje dla asercji
  w gałęzi nigdy nie wchodzonej: czytnik tekstu nie wie rzeczy, których w tekście nie ma.
- **Igła `abc` stoi w SZEŚCIU testach** (l. 800, 843, 862, 880, 899, 1186) i w żadnym
  nie pasuje do literału, bo wartość cytuje interpolacja. Jest przez to najtańszą
  igłą w tym pliku — przechodzi przy każdej odmowie, która zacytuje wartość — a jej
  swoistość bierze się wyłącznie z igieł stojących obok. Wzmocnienie wymagałoby
  asercji na całe zdanie odmowy, czyli igły spod szczebla 3; nie ruszam, bo to jest
  osobne pytanie o to, czy bramka ma umieć czytać interpolację.
- **`--at` pasuje do odmowy o `--atp`, bo jest jej przedrostkiem.** Dopasowanie idzie
  po podnapisie, nie po całym członie, i dla nazw opcji z przedrostkiem wspólnym
  (`--at` / `--atp`, `--steps` / `--sample-every`) potrafi to dodać jedno trafienie
  z niczego. Dopasowanie po granicy członu byłoby innym przyrządem i innym pomiarem.
