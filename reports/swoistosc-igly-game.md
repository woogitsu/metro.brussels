# Swoistość igły asercji wobec komunikatów `src/Game/` (6.D34)

**Zmierzone 07.09.2026 na commicie:** `f684e40a3af52272f9cd1d32d241e9bf3abf644d`
(baza gałęzi `claude/6d34-audyt-game-tests`, czyli `main` po scaleniu #391).
**Dotyczy:** `tools/tests/test_game_needle_specificity.py` (nowa bramka),
`tests/Game.Tests/RunPlanTests.cs`, `tests/Game.Tests/RunHeaderTests.cs`,
`tests/Game.Tests/TelemetryTrackTests.cs`, `tests/Game.Tests/EmergencyBrakeTests.cs`,
`tests/Game.Tests/SignallingHudTests.cs` (dwanaście wzmocnionych igieł),
`reports/audyt-asercji.md` §7 (adnotacja), `docs/TASKS.md`.
**Po co:** `reports/audyt-asercji.md` §7 mówi wprost, że o asercjach `Game.Tests` ten
raport „nie mówi nic — i nie udaje, że mówi". Tu jest o nich powiedziane i zamknięte
bramką, tą samą metodą, co 6.A33 dla runnera (`reports/swoistosc-igly.md`).

## 1. Werdykt, na początku, bo pozycja o niego prosiła wprost

| | PRZED (`f684e40`) | PO (ten commit) |
|---|---|---|
| różnych igieł | **42** | **45** |
| swoistych (dokładnie 1 komunikat) | 13 | **25** |
| niejednoznacznych (>1 komunikat `src/Game/`) | **13** | **4** |
| z tego kolizja WEWNĄTRZ jednego pliku | **9** | **2** |
| z tego zgłoszonych przez bramkę | — | **0** |
| z tego z wpisem z powodem | — | **4** (zapadka `MAX_GAME_JUSTIFIED_NEEDLES = 4`) |
| bez ani jednego dopasowania | 16 | 16 (zapadka `MAX_GAME_UNMATCHED_NEEDLES = 16`) |

Igły niejednoznaczne PRZED i PO, w całości, z rozbiciem na pliki:

```
PRZED (origin/main): igiel 42, swoistych 13, niejednoznacznych 13 (w jednym pliku 9), bez dopasowania 16
      6 1PLIK '--from-telemetry'   ['src/Game/RunPlan.cs']
      4 1PLIK '--replay'           ['src/Game/RunPlan.cs']
      4 1PLIK '--signalling'       ['src/Game/RunPlan.cs', 'src/Game/SignallingHud.cs']
      3 1PLIK '80 km/h'            ['src/Game/RunHeader.cs', 'src/Game/RunPlan.cs']
      2 1PLIK '--input-log'        ['src/Game/RunPlan.cs']
      2 1PLIK '--limit-kmh'        ['src/Game/RunPlan.cs']
      2 1PLIK '--telemetry'        ['src/Game/RunPlan.cs']
      2 1PLIK 'Znane:'             ['src/Game/RunPlan.cs']
      2       'awaryjny'           ['src/Game/FirstRun.cs', 'src/Game/Input/DriverActions.cs']
      2 1PLIK 'nagłówek'           ['src/Game/TelemetryTrack.cs']
      2       'pusty'              ['src/Game/RunPlan.cs', 'src/Game/TelemetryTrack.cs']
      2       'skończoną'          ['src/Game/RunPlan.cs', 'src/Game/TelemetryTrack.cs']
      2       'skończoną liczbą'   ['src/Game/RunPlan.cs', 'src/Game/TelemetryTrack.cs']

PO (ten commit): igiel 45, swoistych 25, niejednoznacznych 4 (w jednym pliku 2), bez dopasowania 16
      6 1PLIK '--from-telemetry'   ['src/Game/RunPlan.cs']
      2 1PLIK '--telemetry'        ['src/Game/RunPlan.cs']
      2       'skończoną'          ['src/Game/RunPlan.cs', 'src/Game/TelemetryTrack.cs']
      2       'skończoną liczbą'   ['src/Game/RunPlan.cs', 'src/Game/TelemetryTrack.cs']
```

Dwanaście asercji wzmocnionych (dziesięć różnych igieł), cztery z wpisem z powodem,
**zero przemilczanych**. Odpowiedź na pytanie pozycji jest więc liczbą, nie zdaniem:
niejednoznacznych igieł w `tests/Game.Tests` było **13 z 42**, z czego **9** to kolizje
wewnątrz jednego pliku; po tym commicie jest **4 z 45**, wszystkie z powodem.

## 2. Wpis kolejki mówił „63 asercje w 7 plikach" i to się zgadza — co do jednej

Wiersz `6.D34` podaje **63** asercje kształtu `StringAssert.Contains` /
`Assert.IsTrue(… .Contains(…))` w **7** plikach `Game.Tests`. Przyrząd tej pozycji
liczy **wywołania**, nie wiersze, i dlatego wychodzi mu **64**. Różnica jest jedna
i daje się wskazać palcem: `RunPlanTests.cs:140` niesie DWA `.Contains` w jednym
`Assert.IsTrue`, po jednym na człon `||`. Rozliczenie w całości:

| co | ile |
|---|---|
| wierszy z `StringAssert.Contains` | 51 |
| wierszy z `Assert.IsTrue(… .Contains(…))` | 12 |
| **razem wierszy — liczba z wiersza kolejki** | **63** |
| wywołań (jeden wiersz niesie dwa) | **64** |
| z tego MIERZALNYCH (igła jest zwykłym literałem) | **53** |
| różnych igieł mierzalnych | **45** |
| plików, w których stoją | **7** |

Jedenaście wywołań nie jest mierzalnych i to jest wypisane, nie zaokrąglone — z tekstu
nie da się powiedzieć, jaki napis test naprawdę poda:

```
  tests/Game.Tests/DriverActionsTests.cs  :186   $"{binding.KeyName} {binding.Meaning}"
  tests/Game.Tests/DriverActionsTests.cs  :335   binding.KeyName
  tests/Game.Tests/DriverActionsTests.cs  :344   $"{binding.KeyName} {binding.Meaning}"
  tests/Game.Tests/EmergencyBrakeTests.cs :67    EmergencyBrake.KeyName
  tests/Game.Tests/EmergencyBrakeTests.cs :120   EmergencyBrake.KeyName
  tests/Game.Tests/RunPlanTests.cs        :1084  "--" + nazwa
  tests/Game.Tests/RunPlanTests.cs        :140   goly  [IsTrue]
  tests/Game.Tests/RunPlanTests.cs        :140   $"--{name}"  [IsTrue]
  tests/Game.Tests/RunPlanTests.cs        :1008  nazwa  [IsTrue]
  tests/Game.Tests/SignallingHudTests.cs  :73    string.Create(CultureInfo.InvariantCulture, $"v_dop  58.4 km/h")
  tests/Game.Tests/TelemetryTrackTests.cs :155   DriveTelemetry.Header
```

**Trzy z nich to igły INTERPOLOWANE i ich pominięcie jest rozstrzygnięciem, nie
przeoczeniem.** Naiwny czytnik bierze `$"--{name}"` za literał `--{name}`, znajduje
w `RunPlan.cs` cztery komunikaty, w których źródłowo stoi ten sam zapis, i zgłasza igłę
niejednoznaczną — a wzmocnić jej nie sposób, bo żadnej stałej igły w tym miejscu nie ma.
Byłoby to dopasowanie ZAPISU ŹRÓDŁA do ZAPISU ŹRÓDŁA i nie mówiłoby nic o komunikacie.

## 3. Metoda: ta sama, co 6.A33, z jednym dodatkiem i jednym odjęciem

**Ta sama.** Komunikat to maksymalna grupa literałów zszytych `+`, wielowyrazowa.
Czytnik literałów, maska i zszywanie są importowane WPROST z
`tools/tests/test_needle_specificity.py` — nie przepisane. Drugi czytnik tego samego
języka rozjeżdża się po cichu i jest to w tym repozytorium usterka zmierzona (6.D30),
nie przewidywana; pilnuje tego `test_the_message_reader_is_the_one_from_the_runner_gate`.

**Dodatek: `Assert.IsTrue(… .Contains(…))`.** W `Game.Tests` ten kształt nie jest
marginesem — **12 wierszy na 63**, czyli co piąty — więc czytnik, który widzi tylko
`StringAssert.Contains`, przegapiłby wszystkie igły odmów `--from-telemetry`,
`--replay`, `--input-log`, `--limit-kmh` i `--signalling`, a to one są tu najgorsze.
(W całym zestawie proporcja jest inna: §7 audytu 6.A32 podaje 25 wobec 226 i nazywa ten
kształt rzadkim. Obie liczby są prawdziwe o swoich zbiorach; nie przeliczam tamtej.)

**Odjęcie: `Assert.IsFalse(x.Contains("igła"))` igłą tej bramki NIE jest.** Przy asercji
na BRAK igła pospolita jest MOCNIEJSZA od swoistej: `ChaseCameraAimTests` żąda, żeby
zdanie na granicy pasma nie zawierało słowa „jeszcze" w żadnej postaci, więc krótkie
`jeszcze` jest tam dokładnie tym, czym ma być. Rodzina usterki, o której mówi 6.A32
i której szuka ta pozycja, to asercja na OBECNOŚĆ. Bez tego odjęcia bramka zgłosiłaby
`jeszcze` (4 komunikaty) i kazała wzmocnić asercję, która wzmocniona byłaby SŁABSZA.

**Rodzina komunikatów to całe `src/Game/`** (18 plików, **142** komunikaty
wielowyrazowe, bez wygenerowanego `.godot/`), a nie plik o nazwie pasującej do pliku
testu. Powód jest zmierzony: `EmergencyBrakeTests` asertuje `DriverInput.Help`, którego
treść stoi w `src/Game/Input/DriverActions.cs`, a nie w `src/Game/Input/EmergencyBrake.cs`.
Rodzina zawężona do pliku o pasującej nazwie uznałaby tę igłę za „bez dopasowania",
czyli **przemilczałaby** jedną z trzynastu.

**Werdykt rozróżnia jednak kolizję WEWNĄTRZ pliku od kolizji MIĘDZY plikami, i to nie
jest kosmetyka.** Igła pasująca do dwóch komunikatów jednej klasy jest usterką wprost:
ten sam program potrafi wypisać oba zdania, więc asercja nie odróżnia gałęzi od gałęzi.
Igła pasująca do jednego komunikatu `RunPlan` i jednego `TelemetryTrack` jest czymś
innym: test stoi na jednej z tych klas i drugiego zdania nie ma jak zobaczyć. Bramka
liczy oba przypadki i **oba żądają decyzji** (wzmocnienie albo powód), ale komunikat
awarii mówi, o który chodzi — bo od tego zależy, czy wzmocnienie jest w ogóle możliwe.

**Czego ta bramka nie robi, świadomie: nie rozwiązuje interpolacji.** Komunikat
`$"[ARGUMENT] '--{name}={text}' nie jest liczbą całkowitą"` daje przy różnych
argumentach różne zdania. Igieł bez ani jednego dopasowania jest **16 z 45** i bramka
ich nie zgłasza, bo nie ma o nich nic prawdziwego do powiedzenia. Ma natomiast zapadkę
na ich liczbę — bez niej najtańszym uciszeniem szczebla 1 byłoby przepisanie igły na
tekst, którego w literałach nie ma wcale, czyli zamiana niejednoznaczności na
niewidzialność.

## 4. Dwanaście asercji wzmocnionych — w teście, nie w programie

Pole „Poza zakresem" zabrania ruszać treść komunikatów, więc rozjazd naprawia się po
stronie testu. Każda nowa igła stoi w komunikacie, który ten test NAPRAWDĘ oglądа —
sprawdzone przebiegiem `dotnet test` (210/210), nie czytaniem kodu.

| plik testu i wiersz | igła PRZED | ile | igła PO | ile |
|---|---|---|---|---|
| `RunPlanTests.cs`:75 | `Znane:` | 2 | `Znane: --` | 1 |
| `RunPlanTests.cs`:680 | `--limit-kmh` | 2 | `--line wymaga --limit-kmh` | 1 |
| `RunPlanTests.cs`:707 | `--telemetry` | 2 | `--line nie łączy się z --telemetry` | 1 |
| `RunPlanTests.cs`:728 | `--limit-kmh` | 2 | `--limit-kmh wymaga --line albo --signalling` | 1 |
| `RunPlanTests.cs`:785 | `--signalling` | 4 | `--signalling nie łączy się z przebiegiem skryptowym` | 1 |
| `RunPlanTests.cs`:807 | `--signalling` | 4 | `--limit-kmh wymaga --line albo --signalling` | 1 |
| `RunPlanTests.cs`:888 | `--replay` | 4 | `--replay nie łączy się z --line` | 1 |
| `RunPlanTests.cs`:908 | `--input-log` | 2 | `--input-log ma sens tylko` | 1 |
| `RunHeaderTests.cs`:348 | `80 km/h` | 3 | `Przejazd ręczny bez planu sygnalizacji` | 1 |
| `TelemetryTrackTests.cs`:138 | `pusty` | 2 | `plik jest pusty` | 1 |
| `TelemetryTrackTests.cs`:154 | `nagłówek` | 2 | `nie jest nagłówkiem rdzenia` | 1 |
| `EmergencyBrakeTests.cs`:121 | `awaryjny` | 2 | `hamulec awaryjny` | 1 |
| `SignallingHudTests.cs`:102 | `--signalling` | 4 | `(podaj --signalling)` | 1 |

Trzy wzmocnienia są ciekawsze od pozostałych i dlatego stoją tu z powodem:

- **`80 km/h` (`RunHeaderTests.cs`:348) to najostrzejszy przypadek w tym pliku.**
  `RunHeader.SpeedLimitMps` ma DWIE odmowy różniące się jednym członem: „Przejazd
  linią bez prowadzenia z rdzenia…" i „Przejazd ręczny bez planu sygnalizacji…", oba
  kończące się identycznie na „a scenariusz podaje 80 km/h — prędkość konstrukcyjną M7".
  Test mierzy tryb RĘCZNY, a igła pasowała do obu, więc przestawienie gałęzi przechodziło
  przezeń bez śladu. Wykonane w §6.1 jako kontrola negatywna.
- **`awaryjny` (`EmergencyBrakeTests.cs`:121) trafiało w `awaryjnych=` wiersza `[ATP]`
  `FirstRun`, bo dopasowanie idzie po podnapisie.** Ta asercja mówi o stałej
  `DriverInput.Help`, a wpadła w komunikat statystyk ochrony pociągu; `hamulec awaryjny`
  wskazuje wiersz opisu sterowania i nic poza nim.
- **`--signalling` stało w TRZECH testach o trzech różnych odmowach** i po wzmocnieniu
  znikło z pliku jako igła zupełnie: każdy z trzech testów dostał zdanie swojej odmowy.
  Dwa z nich (`RunPlanTests.cs`:728 i :807) mierzą tę samą odmowę
  (`--limit-kmh wymaga --line albo --signalling`) i mają teraz tę samą igłę — to nie
  powtórzenie, a dwie drogi do tego samego komunikatu.

## 5. Cztery igły z wpisem z powodem — bo niejednoznaczne z dobrego powodu

| igła | ile | gdzie | dlaczego zostaje |
|---|---|---|---|
| `--from-telemetry` | 6 | jeden plik | cała treść testu: sześć par odmów (6.C3) i asercja obok żąda, żeby komunikat nazwał DRUGI tryb pary — igła jest nazwą PIERWSZEGO i ma pasować do wszystkich sześciu |
| `--telemetry` | 2 | jeden plik | został jeden użytek: odmowa o PUSTEJ ścieżce, składana interpolacją, więc oba dopasowania dotyczą komunikatów innych niż mierzony (jak `--steps` w 6.A33) |
| `skończoną` | 2 | dwa pliki | `RunPlan` i `TelemetryTrack` kończą odmowy tym samym zwrotem; test stoi na `RunPlan.Parse`, człony rozstrzygające są za dziurą interpolacyjną |
| `skończoną liczbą` | 2 | dwa pliki | ta sama kolizja z drugiej strony: test stoi na `TelemetryTrack`, a numer wiersza i nazwa kolumny są interpolowane |

Pełne powody, zdaniem każdy, stoją w `POWODY` w
`tools/tests/test_game_needle_specificity.py`; lista jest zamknięta zapadką z obu stron
(`MAX_GAME_JUSTIFIED_NEEDLES = 4`), tak jak przy 6.A31.

## 6. Kontrole — WYKONANE, z wklejonym wyjściem

Trzy pierwsze są kontrolami **kodu produkcyjnego**: do `src/Game/` wprowadzona usterka,
którą STARA igła przepuszczała, i pokazane, że nowa ją łapie. Każda mutacja uruchomiona
dwa razy — raz ze starą igłą, raz z nową — bo bez pierwszego przebiegu nie wiadomo, czy
stara igła naprawdę przepuszczała.

### 6.1 KN-1: `RunHeader` odmawia trybowi ręcznemu ZDANIEM O TRYBIE LINII

Mutacja: w `src/Game/RunHeader.cs` odmowa trybu ręcznego dostaje treść odmowy trybu
linii (jedna podmieniona linia literału).

```
$ dotnet test tests/Game.Tests          # STARA igła "80 km/h", mutacja obecna
Passed!  - Failed:     0, Passed:   210, Skipped:     0, Total:   210
```

```
$ dotnet test tests/Game.Tests          # NOWA igła, ta sama mutacja
  Failed TrybRecznyBezPlanuNieDostajeLimituZeScenariusza [7 ms]
  Error Message:
   StringAssert.Contains failed. String 'Przejazd linią bez prowadzenia z rdzenia nie ma skąd wziąć limitu, a scenariusz podaje 80 km/h — prędkość konstrukcyjną M7, nie ograniczenie na torze. (Parameter 'manualPlan')' does not contain string 'Przejazd ręczny bez planu sygnalizacji'.
  Stack Trace:
     at MetroBxl.Game.Tests.RunHeaderTests.TrybRecznyBezPlanuNieDostajeLimituZeScenariusza()
Failed!  - Failed:     1, Passed:   209, Skipped:     0, Total:   210
```

### 6.2 KN-2: `TelemetryTrack` przestaje mówić, CO jest z nagłówkiem nie tak

Mutacja: odmowa o obcym nagłówku skrócona do `$"[TELEMETRIA] nagłówek rdzenia: '{…}'"`
— nadal zawiera słowo „nagłówek" i nadal pokazuje nagłówek rdzenia, ale już nie mówi,
że nagłówek pliku jest inny.

```
$ dotnet test tests/Game.Tests          # STARA igła "nagłówek", mutacja obecna
Passed!  - Failed:     0, Passed:   210, Skipped:     0, Total:   210
```

```
$ dotnet test tests/Game.Tests          # NOWA igła, ta sama mutacja
  Failed AForeignHeaderIsRefusedAndShowsTheCoresOne [6 ms]
   StringAssert.Contains failed. String '[TELEMETRIA] nagłówek rdzenia: 'step,t_s,chainage_m,distance_m,speed_mps,speed_kmh,accel_mps2,throttle,brake,phase'' does not contain string 'nie jest nagłówkiem rdzenia'.
Failed!  - Failed:     1, Passed:   209, Skipped:     0, Total:   210
```

**Pierwsza próba tej kontroli była nierozstrzygająca i to jest warte zapisania.**
Mutacja polegająca na wstawieniu w tę gałąź treści „plik ma sam nagłówek, bez ani
jednej próbki" padała TAKŻE ze starą igłą — bo w tym teście stoi obok druga asercja,
`StringAssert.Contains(reason, DriveTelemetry.Header, …)`, i to ona ją łapała. Igła
w zmiennej jest dla tej bramki niemierzalna (§2), więc przyrząd jej nie widzi, ale
`dotnet test` widzi. Mutację trzeba było dobrać tak, żeby stara igła BYŁA jedynym
strażnikiem — i wtedy różnica jest czysta.

### 6.3 KN-3: `RunPlan` odmawia parze `--replay --line` zdaniem o parze `--replay --shot`

```
$ dotnet test tests/Game.Tests          # STARA igła "--replay", mutacja obecna
Passed!  - Failed:     0, Passed:   210, Skipped:     0, Total:   210
```

```
$ dotnet test tests/Game.Tests          # NOWA igła, ta sama mutacja
  Failed ReplayRefusesASecondSourceOfCommand [5 ms]
   Assert.IsTrue failed. [ARGUMENT] --replay nie łączy się z --shot: odtworzenie kończy się na ostatnim kroku zapisu, a zrzut na zadanym kilometrażu — to dwa warunki końca naraz
Failed!  - Failed:     1, Passed:   209, Skipped:     0, Total:   210
```

Wszystkie trzy mutacje przywrócone; `git diff --stat -- src/` po nich **bez ani jednego
wiersza**, czyli ani jeden plik produkcyjny nie został tym zadaniem zmieniony.

### 6.4 KD (dodatnia bramki): osłabienie igły swoistej wywraca DOKŁADNIE tę bramkę

Igła `--replay nie łączy się z --line` w prawdziwym pliku testu osłabiona z powrotem
do `--replay`, przebieg CAŁEGO zestawu:

```
  FAIL test_a_weakened_needle_lights_up_the_first_rung: igla-przyrzad '--replay nie łączy się z --line' zniknela z tests/Game.Tests/RunPlanTests.cs — kontrola dodatnia nie ma czego oslabiac
  FAIL test_every_needle_matches_at_most_one_message_or_is_justified: igla asercji pasuje do wiecej niz jednego komunikatu `src/Game/` i nie ma wpisu z powodem — wzmocnij ja w tescie albo wpisz na liste: ["'--replay' w 4 komunikatach (w JEDNYM pliku): {'src/Game/RunPlan.cs': 4} [test [('tests/Game.Tests/RunPlanTests.cs', 888)]]"]
  FAIL test_the_verdict_follows_the_source_files: igla-przyrzad '--replay nie łączy się z --line' nie stoi juz w tescie albo nie jest swoista (licznik None) — kontrola przyrzadu stracila punkt odniesienia
  1964/1967 przeszło
kod=1
```

Trzy zapalone testy stoją **wszystkie w nowym module** i ani jeden poza nim; dwa z nich
to własne kontrole bramki, które tę samą igłę mają za próbkę i mówią to w komunikacie
awarii — bez tego zniknięcie próbki wyglądałoby jak zepsuta bramka. Plik przywrócony,
`git diff --stat` z powrotem na pięciu plikach testów i trzynastu wierszach.

### 6.5 KU (ujemna): „nie zgłasza" jest rozróżnieniem, nie pustym zbiorem

```
zgloszen przy > 1 (bramka)   : 0
zgloszen przy >= 1 (mutacja) : 25
  przyklady                  : ['(podaj --signalling)', '--calls', '--input-log ma sens tylko', '--limit-kmh wymaga --line albo --signalling', '--line nie łączy się z --telemetry', '--line wymaga --limit-kmh']
bez listy powodow, > 1       : 4 ['--from-telemetry', '--telemetry', 'skończoną', 'skończoną liczbą']
bez listy powodow, >= 1      : 29 z 45 igiel
```

Przy `>= 1` zbiór zgłoszeń przenosi się z zera na **25**, a ze zdjętym filtrem listy
powodów — na **29**, czyli na wszystkie 45 minus 16 bez dopasowania. Że nie na 45, ma
jedną przyczynę i jest nią szczebel 3: **16 igieł nie pasuje do ani jednego literału**,
bo scena składa te zdania interpolacją (§3).

### 6.6 Zapadka listy powodów działa w OBIE strony

Skasowany JEDEN wpis (`skończoną liczbą`), nic więcej:

```
  FAIL test_a_weakened_needle_lights_up_the_first_rung: szczebel 1 zapalony JUZ przed oslabieniem: ['skończoną liczbą'] — kontrola dodatnia nie pokazuje wtedy niczego
  FAIL test_every_needle_matches_at_most_one_message_or_is_justified: igla asercji pasuje do wiecej niz jednego komunikatu `src/Game/` i nie ma wpisu z powodem — wzmocnij ja w tescie albo wpisz na liste: ["'skończoną liczbą' w 2 komunikatach (miedzy plikami): {'src/Game/RunPlan.cs': 1, 'src/Game/TelemetryTrack.cs': 1} [test [('tests/Game.Tests/TelemetryTrackTests.cs', 213)]]"]
  FAIL test_the_justification_list_stays_closed: zapadka 4 stoi wyzej niz lista (3) — obniz ja do stanu faktycznego
  7/10 przeszło
kod=1
```

Lista krótsza od zapadki jest awarią tak samo jak dłuższa. Plik bramki przywrócony,
`cmp` z kopią sprzed mutacji: identyczne.

### 6.7 KP (przyrząd) i KW (wzorzec) — zamknięte testami, nie opisem

`test_the_verdict_follows_the_source_files` dopisuje do `src/Game/RunPlan.cs` drugi
komunikat z istniejącą igłą i żąda, żeby licznik poszedł z 1 na 2, a igła trafiła do
zgłoszeń; ten sam dopisek **w komentarzu** licznika podnieść NIE może, bo komentarz
maska zamienia na spacje. Podstawienie idzie przez argument `nadpisz`, więc kontrola
nie pisze po drzewie ani razu.

Progi KW to `MIN_GAME_MESSAGES = 142`, `MIN_GAME_SOURCES = 18` i
`MIN_GAME_NEEDLES = 45`: literówka we wzorcu daje zero dopasowań, zero zgłoszeń i cały
moduł zielony, a te trzy liczby są jedynym powodem, dla którego taka literówka jest
widoczna. Osobno dwa testy granicy na wejściu syntetycznym — czytnik igieł odróżnia
literał od zmiennej, widzi wywołanie rozbite na dwa wiersze, przyjmuje
`Assert.IsTrue(… .Contains(…))`, odrzuca `Assert.IsFalse(…)` i odrzuca igłę
interpolowaną; czytnik komunikatów jest ten sam, co w bramce runnera, i to też jest
sprawdzone wprost.

## 7. Weryfikacja

```
$ python3 tools/tests/test_all.py
  1967/1967 przeszło
  RAZEM 74.194 s, 1967 testów, 104 modułów
kod: 0
```

```
$ dotnet test tests/Game.Tests
Passed!  - Failed:     0, Passed:   210, Skipped:     0, Total:   210, Duration: 470 ms
kod: 0
```

Zestaw narzędzi **1957 → 1967** (dziesięć testów nowego modułu; 1957 zmierzone na tym
samym drzewie z modułem chwilowo odłożonym poza `tools/tests/`), `dotnet test`
**210 → 210** — wzmocnienie dwunastu igieł nie dodaje ani nie zabiera asercji, tylko
zawęża je do jednego komunikatu. Pełny przebieg licznika bramki zajmuje **0,0707 s**
(`time.perf_counter()`, średnia z pięciu), cały moduł **1,05 s** — przy progu
`SUITE_RUNTIME_BUDGET_S` nie ruszam żadnej zapadki czasu.

## 8. Czego świadomie NIE zrobiłem

- **Nie tknąłem treści ani jednego komunikatu `src/Game/`.** Pole „Poza zakresem"
  mówi to wprost, a rozjazd naprawia się w teście. Jedyne zmiany w tym drzewie, jakie
  w ogóle zaszły, to trzy mutacje kontroli negatywnej z §6, wszystkie przywrócone
  i sprawdzone `git diff --stat -- src/`.
- **Zdania z §7 `reports/audyt-asercji.md` nie poprawiłem** — dostało adnotację
  z datą, tak jak żąda pole „Skończone, gdy". Tamten raport ma datę
  (`docs/04-conventions.md`), a jego zdanie było prawdziwe w dniu wpisania: to ta
  pozycja je unieważnia, nie pomyłka autora.
- **Nie przeliczyłem liczb 20 / 19 / 14 ani 25 / 226 z §2 i §7 tamtego raportu.** Są
  pomiarem z datą i innym przyrządem; §3 podaje proporcję dla `Game.Tests` osobno,
  jako osobny pomiar o innej definicji, bo dwie liczby z dwóch definicji zlane w jedną
  są gorsze od obu osobno.
- **Nie ruszyłem `tests/Sim.Tests`** — to jest 6.A33, zamknięte bramką
  `tools/tests/test_needle_specificity.py`, i osobna rodzina komunikatów.
- **Nie uruchamiałem niczego w Godocie.** `Game.Tests` chodzi bez silnika i cała ta
  pozycja jest tekstowa; Godota w tym środowisku nie ma i nie był potrzebny.
- **Nie rozwiązuję interpolacji** i nie udaję, że przyrząd wie, co scena wypisze przy
  konkretnych argumentach. Zamiast tego 16 igieł bez dopasowania stoi pod zapadką,
  a granica jest nazwana w docstringu bramki.
- **Nie podniosłem `MINIMUM_DETAIL_BLOCKS`** w `tools/tests/test_backlog.py`. Blok
  6.D34 zostaje w pliku razem z adnotacją, więc liczba bloków nie rusza się z 111
  w żadną stronę; podniesienie zapadki byłoby tu zmianą bez przedmiotu.

## 9. Zauważone przy okazji, nie tknięte

- **`src/Game/World/ChaseCameraAim.cs` ma dwa razy IDENTYCZNY literał
  `skład nie ma ujemnej długości`** (wiersze 162 i 217, dwie różne metody). Dla tej
  bramki są to dwa komunikaty i każda igła na to zdanie byłaby niejednoznaczna
  z definicji — dziś żaden test `Game.Tests` na nie nie asertuje, więc nie ma czego
  wzmacniać. Gdyby kiedyś asertował, wzmocnienie wymagałoby zmiany treści jednego
  z tych dwóch komunikatów, czyli wyjścia z zakresu tej pozycji.
- **`RunPlanTests.cs`:1084 asertuje igłę `"--" + nazwa`**, składaną w pętli po
  `RunPlan.PathArguments`. Z tekstu nie da się powiedzieć, jaki to napis, więc bramka
  ją pomija — a jest to asercja MOCNA, bo pętla przechodzi dziesięć opcji i każda musi
  nazwać siebie. Granica przyrządu, nie słabość testu; ta sama, którą
  `tools/tests/csharp_assertions.py` opisuje dla asercji w gałęzi nigdy nie wchodzonej.
- **Igła `abc` stoi w `RunPlanTests.cs`:216 i nie pasuje do żadnego literału**, bo
  wartość cytuje interpolacja — dokładnie jak w `RunnerCommandTests.cs` (§9 raportu
  6.A33). Jest przez to najtańszą igłą tego pliku i jej swoistość bierze się wyłącznie
  z igły stojącej obok (`skończoną`).
- **`--at` z 6.A33 miał brata w tym drzewie i już go nie ma.** Dopasowanie idzie po
  podnapisie, nie po granicy członu, i właśnie tak `awaryjny` trafiało w `awaryjnych=`.
  Po wzmocnieniu żadna igła `Game.Tests` nie zawdzięcza dopasowania samemu
  przedrostkowi, ale dopasowanie po granicy członu byłoby innym przyrządem i innym
  pomiarem — nie robię go tutaj.
