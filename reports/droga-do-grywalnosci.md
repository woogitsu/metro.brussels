# Droga do grywalnego przejazdu — co dzieli repozytorium od człowieka za nastawnikiem

**Zmierzone na commicie:** `3c242f7` (scalenie #227) · **data:** 2026-09-05
**Rodzaj pracy:** rozpoznanie. Ani jeden plik w `src/` nie został zmieniony; jedyną
zmianą w repozytorium jest ten raport.

Środowisko pomiaru: .NET SDK **10.0.400**, Godot **4.7.2-stable mono**
(`/opt/metro-godot/4.7.2-stable`), `python3 tools/tests/test_all.py` → **1493/1493**.
Geometria pakietu A **nie była generowana** — wszystkie uruchomienia sceny szły
z `--no-geometry`, bo pytanie tego rozpoznania dotyczy łańcucha sterowania,
a nie obrazu.

**Skąd pochodzi każda liczba w tym raporcie.** Trzy źródła i nic więcej:

| oznaczenie | znaczenie |
|---|---|
| **[URUCHOMIONE]** | wynik **mojego** uruchomienia w tym środowisku, wklejony |
| **[ZMIERZONE]** | wynik osobnej próby liczbowej, której metoda jest opisana w miejscu użycia |
| **[Z KODU]** | odczyt z pliku, z numerem wiersza — nie wykonanie |

---

## 1. Stan dzisiejszy: co z łańcucha „wejście → polecenie → fizyka → obraz" istnieje

### 1.1 Tryb ręczny **istnieje i jest trybem domyślnym**

To jest pierwsza rzecz do sprostowania, bo zmienia całą resztę. Zlecenie tego
rozpoznania mówiło, że „scena chodzi w trybie autopilota (`--line`) albo odtwarza
scenariusz". Scena bez argumentów robi coś trzeciego: **czyta klawiaturę**.
`project.godot` ustawia `run/main_scene="res://Scenes/FirstRun.tscn"`, a ta scena bez
argumentów wchodzi w gałąź ręczną.

[URUCHOMIONE] `Godot_v4.7.2-stable_mono_linux.x86_64 --headless --path src/Game -- --no-geometry`:

```
[ASSETS] --no-geometry: scena bez tunelu i bez składu; fizyka bez zmian
[PRZEJAZD] tryb=manual widok=Cab scenariusz=package-a-first-run krok=1/120 s masa=221940 kg limit=80.0 km/h
[OŚ] L1_A: 1349 punktów, 6686.739 m, 12 stacji
```

Proces **nie zakończył się sam** — `timeout 60` zabił go kodem 124. To nie jest usterka
uruchomienia, tylko własność trybu: §1.4 niżej.

### 1.2 Łańcuch, człon po członie

| człon | gdzie | stan |
|---|---|---|
| odczyt klawiszy | `src/Game/Input/DriverInput.cs:51,61,69` | **jest** — W/↑ ciąg, S/↓ hamulec, X wybieg, po położeniu fizycznym (AZERTY nie przestawia sterowania) |
| klawisze → `DriverCommand` | `DriverInput.Poll`, `src/Game/Input/DriverInput.cs:44` | **jest** — nastawnik przesuwa się o `0,80 · Δt`, hamulec ma pierwszeństwo, `Clamped()` odrzuca NaN |
| wołanie wejścia w pętli | `src/Game/FirstRun.cs:602` | **jest** — `_command = _input.Poll(delta)` raz na **klatkę** |
| polecenie → fizyka | `src/Game/FirstRun.cs:735–737` | **jest** — `_stations.Filter(...)` a potem `_controller.Advance(...)`, ten sam kontroler co w rdzeniu |
| obsługa stacji dla człowieka | `src/Sim/Train/StationService.cs` | **jest** — okno **dwustronne** ±5,0 m, blokada trakcji na czas cyklu drzwi, rejestr `Calls` i `Missed` |
| fizyka → obraz | `FirstRun.PlaceEverything`, `src/Game/FirstRun.cs:774` | **jest** — kamera kabinowa, streaming chunków, perony |
| HUD | `src/Game/UI/Hud.cs` | **jest** — prędkość, przyspieszenie, kilometraż, słupki nastawników, wiersz stacji |
| sygnalizacja i ATP w kabinie | — | **NIE MA** w trybie ręcznym, patrz §1.3 |
| koniec przejazdu | — | **NIE MA**, patrz §1.4 |
| ograniczenie prędkości na torze | `src/Game/RunHeader.cs:81` | **jest 80 km/h — prędkość konstrukcyjna M7**, patrz §1.5 |
| pomoc o sterowaniu na ekranie | `DriverInput.Help`, `src/Game/Input/DriverInput.cs:39` | **stała istnieje i nie jest wołana przez nic** |

`grep -rn "DriverInput" --include=*.cs --include=*.py --include=*.yml .` daje poza samym
plikiem **dwa** trafienia — `FirstRun.cs:66` (pole) i `FirstRun.cs:314` (konstrukcja).
`DriverInput.Help` nie ma **ani jednego**.

### 1.3 Cztery tryby, i to, że sterowanie i sygnalizacja są rozłączne

`RunPlan` rozstrzyga tryb z wiersza poleceń [Z KODU, `src/Game/RunPlan.cs:129–131`]:

> **TA SEKCJA JEST PRZEPISANA 05.09.2026 I OPISYWAŁA STAN, KTÓRY JUŻ NIE ISTNIEJE.**
> Stało w niej, że „**jedyny tryb, w którym prowadzi człowiek, jest jedynym trybem,
> w którym nie ma ani blokad, ani ochrony pociągu, ani prędkości dopuszczalnej
> z zewnątrz**", i że „kabina i sygnalizacja nie spotykają się dziś nigdzie". Rozpoznanie
> było trafne i z niego wzięło się zadanie G-5; **G-5 zostało zrobione w #257** i to
> zdanie przestało być prawdziwe. Przepisane, a nie dopisane obok — konwencja jak w §5.1.

| tryb | jak się uruchamia | kto podaje polecenie | sygnalizacja / ATP | koniec |
|---|---|---|---|---|
| `manual` | bez argumentów | **człowiek** (`DriverInput`) | **`--signalling` → tak, z ATP** (#257) | brak, dopóki nie ma zapisu wejść |
| `replay` | `--replay=PLIK` | zapis wejść, tą samą drogą co człowiek | jw. | koniec zapisu (#239) |
| `line` | `--line --limit-kmh=N` | `LineDrive` albo `LineCore` (autopilot) | `--signalling` → tak, z ATP | ostatnia stacja |
| `telemetry` | `--telemetry=PLIK` | `ScenarioDrive` (skrypt) | nie | koniec scenariusza |
| `from-telemetry` | `--from-telemetry=PLIK` | **nikt — ruch jest zadany plikiem**, fizyka nie liczy się ani razu (6.C3) | nie, i to jest odmowa: ochrona ingeruje w polecenie, którego tu nie ma | ostatnia próbka pliku |
| `shot` | `--shot=PLIK --at-chainage=X` | jw. albo `LineDrive` | jw. | migawka |

> Wiersz `from-telemetry` dopisany 06.09.2026 (6.C3). Nagłówek sekcji mówi „cztery
> tryby" i mówił tak już przy pięciu wierszach tabeli — liczby w nim nie poprawiam,
> bo nie jest ona wynikiem żadnego pomiaru, a tabela stoi obok i liczy się sama.
> **`--telemetry` a `--from-telemetry` to ten sam format pliku w dwóch różnych rolach**:
> pierwszy jest wyjściem, drugi wejściem. Odtwarzanie z `--from-telemetry` jest przy
> tym czymś innym niż odtworzenie z `--replay`, i to jest cała różnica między dwoma
> ostatnimi wierszami o odtwarzaniu: zapis wejść niesie POLECENIE i przechodzi przez
> fizykę, telemetria niesie WYNIK i fizyki nie dotyka. Bramka `--replay` pyta więc,
> czy rdzeń policzy to samo drugi raz; bramka `--from-telemetry` — czy scena pokaże to,
> co już policzono.

Z trzech odmów w `RunPlan` została **jedna, i to celowo**: `--limit-kmh` bez `--line`
dalej jest błędem, bo sufit prędkości bez prowadzenia z rdzenia nie ma skąd wziąć
liczby innej niż konstrukcyjna prędkość M7 — to usterka naprawiona w #246 i odmowa jest
tu treścią, nie pozostałością. `--signalling` bez `--line` **przestało** być błędem:
to jest właśnie G-5.

Prędkość dopuszczalną tryb ręczny bierze od #246 z planu sygnalizacji
(`data/design/signalling/classic-2026.json`, 72,00 km/h), a nie z rejestru pojazdu —
także wtedy, gdy plan jest tylko czytany i nie prowadzi.

**Wejście gracza w trybie `--line` nadal jest odczytywane i wyrzucane** — to zdanie
zostaje prawdziwe. Zmieniło się co innego: od #256 HUD to **mówi**. Ostatni wiersz
pod `--line` brzmi `C widok · Esc wyjście · prowadzi rdzeń: W, S, X, Spacja, R nie
działają`, więc trzymanie W nadal nic nie robi, ale już nie milczy o tym.

### 1.4 Przejazd ręczny nie ma końca — i dlatego nie ma bramki

`_done` ustawia wyłącznie `FinishScriptedRun` (`FirstRun.cs:1052`) i `FinishLineRun`
(`FirstRun.cs:1069`). Gałąź ręczna nie ustawia go nigdy; nie ma też `--max-steps`
ani `--until-chainage`. Przebieg kręci klatki, aż ktoś naciśnie Esc.

Konsekwencja jest w CI, nie na ekranie. W `.github/workflows/godot-first-run.yml`
**każde** uruchomienie sceny niesie `--telemetry`, `--line` albo `--shot`.
Ani jeden krok nie uruchamia trybu ręcznego, bo taki krok wisiałby do
`timeout-minutes`. Czyli: **cała gałąź `DriverInput` → `StationService` →
`TrainController` w scenie nie jest sprawdzana przez żadną bramkę.**
`StationService` ma testy jednostkowe (`tests/Sim.Tests/StationServiceTests.cs`), ale
jego *wpięcia* w scenę nie pilnuje nic.

### 1.5 Nagłówek trybu ręcznego mówi 80 km/h i to jest ta sama usterka, którą naprawiał `RunHeader`

`src/Game/RunHeader.cs` powstał 04.09.2026 dokładnie dlatego, że przy `--line
--limit-kmh=70` nagłówek wypisywał `limit=80.0 km/h` — prędkość **konstrukcyjną** M7
z rejestru pojazdu. Naprawa objęła ścieżkę `--line`. Ścieżka ręczna ma tę liczbę
nadal, i nie jest to już tylko napis: `FirstRun.SpeedLimitMps` (`FirstRun.cs:757`)
podaje ją **kontrolerowi**. [URUCHOMIONE, §1.1]: `tryb=manual … limit=80.0 km/h`.

Człowiek prowadzący dziś ma pod nastawnikiem 80 km/h — liczbę, o której
`docs/TASKS.md` mówi wprost, że *„prędkość konstrukcyjna nie jest prędkością
dopuszczalną na torze"*, a `RunPlan` nie pozwala jej nadpisać (`--limit-kmh` bez
`--line` jest odmową). Znane ograniczenia to 58,68 km/h od dołu (T-401) i 80 km/h
od góry (rejestr); źródła prędkości liniowej nie ma (R-006, #85).

### 1.6 Co mówią dokumenty

- **`docs/01-architecture.md`, §Determinizm** stawia trzy warunki; dwa z nich dotyczą
  wprost wejścia gracza i **żaden z tych dwóch nie jest dziś spełniony**:
  „wejścia gracza ze znacznikiem
  **kroku**, nie czasu ściennego", „z ziarna + **zapisu wejść** da się odtworzyć
  przejazd". Zapisu wejść nie ma; wejście jest próbkowane czasem klatki (§5.1).
- **`docs/01-architecture.md`, §Moduły** wymienia `Game/UI/ HUD i pulpit`. Pulpitu nie
  ma i nie może być: `tools/blender/m7_shell.py` celowo nie modeluje kabiny (T-220),
  a `FirstRun.cs:771` w widoku kabinowym **ukrywa cały skład**, bo inaczej widać
  wnętrze skorupy. Widok z kabiny jest dziś kamerą wiszącą w pustce 2,20 m nad
  główką szyny.
- **`docs/TASKS.md`, faza 5 i 6** — w całej kolejce nie ma **ani jednej** pozycji
  o prowadzeniu przez człowieka. Najbliższe są 6.C3 (odtwarzanie przejazdu z pliku
  telemetrii) i 6.C4 (kamera inspekcyjna); obie są widokami, nie sterowaniem.
  Grywalność nie jest dziś w kolejce agenta w ogóle.
- **Issue #26** („Pierwszy grywalny vertical slice") **jest specyfikacją właściciela
  i rozstrzyga więcej, niż wygląda.** Rozstrzygnięte tam już: sterowanie przez
  `InputMap`, nie przez layout klawiatury; **„nie można ominąć ATP przez input
  gracza"**; „drzwi nie otwierają się w ruchu"; „30/60/120 FPS daje ten sam stan Sim
  po tej samej liczbie ticków"; „scenariusz headless Sim i scenariusz uruchomiony
  przez Godot kończą się tym samym hash state **przy tych samych commandach**".
  Te punkty **nie są pytaniami do właściciela** — są odpowiedziami, których kod
  jeszcze nie wykonał.
- **`docs/20-art-direction.md`, §UI/HUD** — HUD ma być oryginalnym interfejsem
  diagnostycznym i nie odtwarzać paneli kabinowych STIB; statusy safety mają mieć
  redundancję tekst/ikona/kształt, nie sam kolor. Dzisiejszy HUD jest zgodny.
- **`docs/03-legal.md`** — **nic w tym zakresie nie dotyka blokad prawnych.**
  Sterowanie, ATP, drzwi i wynik przejazdu to mechanika, nie znaki towarowe.
  Ograniczenie z §Materiały referencyjne dotknie dopiero **wyglądu** pulpitu M7,
  a ten jest poza zakresem #26 („finalna kabina M7").

---

## 2. Czego brakuje, w kolejności zależności

Kolejność jest wymuszona: każda pozycja wymaga poprzedniej. „decyzja właściciela"
znaczy, że **nie da się tego rozstrzygnąć z `docs/`, `data/` ani z Issue #26**.

| # | czego brakuje | praca czy decyzja |
|---|---|---|
| 1 | wejście gracza krokowane numerem kroku, nie czasem klatki | **praca** — wymaga tego `docs/01-architecture.md` §Determinizm i #26 |
| 2 | zapis wejść gracza i odtworzenie przejazdu z zapisu | **praca** — jw.; bez tego nie da się zbudować żadnej bramki na tryb ręczny |
| 3 | warunek końca przejazdu ręcznego (choćby techniczny: koniec zapisu wejść) | **praca** — bez niego przebieg nie kończy się i CI go nie uruchomi |
| 4 | bramka CI porównująca odtworzony przejazd ręczny z rdzeniem | **praca** — metoda istnieje (`Sim.Runner compare`, próg 0) |
| 5 | reset (R) obejmujący całą obsługę stacji, nie tylko stan dynamiczny | **praca** — usterka, §5.4 |
| 6 | `InputMap` zamiast fizycznych klawiszy w kodzie + pomoc na ekranie | **praca** — #26 rozstrzyga wprost; domyślne przypisanie już stoi w `DriverInput.Help` |
| 7 | prędkość dopuszczalna dla trybu ręcznego | **decyzja właściciela** — pytanie P1 |
| 8 | sygnalizacja i ATP w kabinie: `--signalling` i `--limit-kmh` dla trybu ręcznego | **praca** — #26 rozstrzyga („nie można ominąć ATP"), rdzeń ma wszystko (`TrainProtection`, `ProtectionDecision.Apply`), brakuje wpięcia i **szwu na źródło polecenia w `LineDrive`** |
| 9 | co się dzieje po minięciu stacji | **decyzja właściciela** — pytanie P3; `StationService` ma dziś regułę (liczy w `Missed`, jedzie dalej), ale nikt jej nie zatwierdził jako reguły **gry** |
| 10 | wynik przejazdu i stan „koniec przejazdu" widoczny dla gracza | **decyzja właściciela** — pytania P2 i P4 |
| 11 | hamulec awaryjny jako **polecenie** | **decyzja właściciela** — pytanie P5; #26 wymienia go w sterowaniu, a rdzeń mówi wprost, że go nie ma |
| 12 | przejęcie i oddanie składu (`take/release control`) | **praca**, ale **zależy od T-320** — poza najkrótszą drogą, §3.6 |
| 13 | pulpit i wnętrze kabiny jako geometria | **decyzja właściciela**, i to podwójna: T-902 (estetyka) i brak publicznego rysunku pulpitu M7 (`docs/21`, T-220). #26 stawia to poza zakresem |

---

## 3. Propozycje zadań — sześć pól, gotowe do przeniesienia do `docs/TASKS.md`

Pięć pozycji. Tyle wynika z §2 po odjęciu decyzji właściciela i po odjęciu tego, co
zależy od T-320. **Numeracja `G-n` jest robocza** — do `docs/TASKS.md` wejdą jako
pozycje fazy 6 albo jako etapy T-400, o czym rozstrzyga właściciel, nie ten raport.

> **G-1 JEST ZROBIONE. Ten akapit jest dopisany 05.09.2026 właśnie po to, żeby
> propozycja nie wysłała nikogo drugi raz w to samo miejsce.** Rozpoznanie mierzyło
> na `3c242f7`; jeszcze tego samego dnia #239 (`c787198`, gałąź `2c19026`) zrobiło
> G-1 co do litery — z tymi samymi liczbami pomiaru „przed", które stoją w §5.1
> tego raportu. Sprawdzone lekturą drzewa na `9f4ae98`:
>
> | czego G-1 żądało | co jest |
> |---|---|
> | `--input-log=PLIK` i `--replay=PLIK` w `RunPlan.KnownArguments` | `src/Game/RunPlan.cs:38` — `"input-log", "replay"`, z odmowami dla `--replay` razem z `--line` i z `--shot` |
> | format zapisu w `src/Sim/Train/`, bez Godota, kolumny „krok, klawisze" | `src/Sim/Train/InputLog.cs` — `InputLogEntry(long Step, DriverKeys Keys)`, nagłówek `wersja=`/`kroki=`, wiersze `krok;klawisze`; plus `InputLogRecorder.cs`, `DriverKeys.cs` |
> | przesuw nastawnika **wewnątrz** kroku, nie raz na klatkę | `src/Game/FirstRun.cs` — komentarz przy `StepOnce` mówi wprost „na krok symulacji — nie raz na klatkę", nastawnik żyje w `src/Sim/Train/DriverNotch.cs` (`tests/Sim.Tests/DriverNotchTests.cs`) |
> | testy | `tests/Sim.Tests/InputLogTests.cs`, `tests/Sim.Tests/DriverNotchTests.cs`, `tests/Sim.Tests/StepAccumulatorTests.cs` |
>
> **G-2, G-3 i G-4 TEŻ SĄ ZROBIONE. To zdanie jest przepisane, a nie dopisane obok:**
> do 05.09.2026 stało tu, że „reszta pozycji (G-2 … G-5) nie została sprawdzona pod tym
> kątem w tym przeglądzie i zostaje jako propozycja". Wtedy była to prawda i jawne
> ograniczenie zakresu; kilka godzin później przestała nią być, a zdanie o nieznanym
> stanie czyta się dokładnie tak samo, jak zdanie o stanie otwartym. Sprawdzone lekturą
> drzewa na `4284fc1`:
>
> | pozycja | co ją zrobiło | sprawdzone w drzewie |
> |---|---|---|
> | **G-2** · bramka CI na tryb ręczny | #245 (bramka) i #248 (limit po obu stronach) | `godot-first-run.yml` ma **cztery** kroki tej rodziny: „Manual run — the replayed input log must be the core's own drive", „Negative control of the manual comparison", „Manual mode — both sides must hold the same speed ceiling", „Negative control of the speed-ceiling gate"; `Sim.Runner replay` istnieje; `DriveTelemetry.Row` ma dziś **dwa** przeciążenia — jedno bierze `ScenarioDrive`, drugie przejazd ręczny |
> | **G-3** · `InputMap` i wiersz pomocy | #249 | `grep -cE '^(driver_\|view_\|run_)' src/Game/project.godot` = **7**; `grep -rn IsPhysicalKeyPressed src/Game --include=*.cs \| grep -v '///'` = **0 trafień**; `src/Game/Input/DriverActions.cs`; `Hud` bierze węzeł `Panel/Rows/Help`; `tests/Game.Tests/DriverActionsTests.cs` |
> | **G-4** · reset resetuje cały przejazd | #251 | `src/Game/RunReset.cs`; `StationService` ma `public void Reset() => StartFromScratch()`, czyli reset dzieli inicjalizator z konstruktorem; `tests/Game.Tests/RunResetTests.cs` |
>
> Numerów wierszy w tej tabeli nie ma celowo: liczba w prozie, której nikt nie
> porównuje, rozjeżdża się przy pierwszym `git rebase` i wygląda potem tak samo
> wiarygodnie jak prawdziwa. Nazwy kroków, ścieżki i sygnatury są greppowalne
> i mówią, gdzie sprawdzić.
>
> **G-5 (kabina pod sygnalizacją) zostaje otwarte** i to jest jedyna pozycja z tej
> piątki, która jeszcze nie ma swojego PR-a.
>
> **UWAGA DO §G-2 NIŻEJ: wypisane tam polecenie weryfikacji już nie zadziała.**
> Propozycja podaje `replay --keys tests/data/manual-keys.log --out build/g2/core.csv`,
> a od #248 `--signalling` jest **obowiązkowe** i takie wywołanie kończy się odmową
> („replay wymaga --signalling PLIK.json"). Polecenie zostaje w propozycji jako zapis
> tego, co proponowano; działa dziś to:
>
> ```bash
> dotnet run --project src/Sim.Runner -c Release -- \
>   replay --keys tests/data/manual-keys.log \
>   --signalling data/design/signalling/classic-2026.json \
>   --notch-rate 0.80 --exchange-s 8 --stop-window-m 5 --out build/g2/core.csv
> "$GODOT_BIN" --headless --path src/Game -- \
>   --replay="$PWD/tests/data/manual-keys.log" --telemetry="$PWD/build/g2/scene.csv"
> dotnet run --project src/Sim.Runner -c Release -- \
>   compare build/g2/core.csv build/g2/scene.csv --tolerance 0
> ```
>
> Powód odmowy jest treścią, nie formalnością: bez planu tryb ręczny brał 80 km/h
> ze scenariusza — prędkość konstrukcyjną M7 — podczas gdy scena od #246 czyta
> 72 km/h z planu, i bramka tego nie widziała, bo ten wzorzec wejść dochodzi
> do 65,22 km/h. Limitu pilnuje osobny wzorzec `tests/data/manual-keys-limit.log`.

### G-1 · Wejście gracza krokowane numerem kroku i zapisywalne

- **Skąd:** `docs/01-architecture.md` §Determinizm („wejścia gracza ze znacznikiem
  kroku, nie czasu ściennego"; „z ziarna + zapisu wejść da się odtworzyć przejazd")
  i Issue #26 §Weryfikacja funkcjonalna („30/60/120 FPS daje ten sam stan Sim po tej
  samej liczbie ticków"). Rozjazd zmierzony w §5.1 tego raportu.
- **Wejście:** `src/Game/Input/DriverInput.cs`, `src/Game/FirstRun.cs` (`_Process`
  wiersz 574, `AdvanceBy` 636, `StepOnce` 659), `src/Game/RunPlan.cs`,
  `src/Sim/Train/DriverCommand.cs`, `src/Sim/Physics/StepAccumulator.cs`.
- **Wyjście:** `DriverInput` rozdzielony na odczyt **stanu klawiszy** (raz na klatkę)
  i przesuw nastawnika o `rate · step.Seconds` wykonywany **wewnątrz `StepOnce`**;
  nowe argumenty `--input-log=PLIK` (zapis) i `--replay=PLIK` (odtworzenie) w
  `RunPlan.KnownArguments`; format zapisu w `src/Sim/Train/` (bez Godota), kolumny
  `step,keys`; testy w `tests/Game.Tests/`.
- **Weryfikacja:**
  ```bash
  # ten sam zapis wejść, trzy różne liczby klatek na sekundę
  for spf in 1 2 4; do
    "$GODOT_BIN" --headless --path src/Game -- \
      --replay="$PWD/build/g1/keys.log" --steps-per-frame=$spf \
      --telemetry="$PWD/build/g1/replay-$spf.csv"
  done
  dotnet run --project src/Sim.Runner -c Release -- \
    compare build/g1/replay-1.csv build/g1/replay-4.csv --tolerance 0
  ```
  Oczekiwane: `compare` przy progu **0** zgłasza zgodność dla każdej pary; kontrola
  negatywna — zapis z jednym przestawionym numerem kroku daje rozjazd, z numerem
  wiersza w wypisie.
- **Skończone, gdy:** ten sam plik wejść odtworzony przy `--steps-per-frame` 1, 2 i 4
  daje telemetrię identyczną **co do bitu** (próg 0, jak dzisiejsze bramki
  `godot-first-run.yml`), a `--jitter=0.45` tego nie zmienia. Dziś ta sama sekwencja
  klawiszy przy 60 i 120 kl./s rozjeżdża się o **0,234166 m na 60 s** (§5.1).
- **Poza zakresem:** `docs/03-legal.md`; zapis do `data/`; ocena estetyczna; zmiana
  jakiejkolwiek stałej z `docs/21-measured-vs-assumed.md` (w szczególności
  `ControlNotchRatePerSecond = 0,80`); `InputMap` (to G-3); sygnalizacja (to G-5).
- **Zależy od:** nic.

### G-2 · Bramka CI na tryb ręczny: odtworzony przejazd wobec rdzenia

- **Skąd:** §1.4 tego raportu — w `.github/workflows/godot-first-run.yml` żaden krok
  nie uruchamia trybu ręcznego, więc gałąź `DriverInput → StationService →
  TrainController` w scenie nie ma ani jednej bramki. Metoda porównania istnieje
  i jest udowodniona kontrolą negatywną (kroki „Negative control of the comparison"
  i „Negative control of the line comparison").
- **Wejście:** `src/Sim.Runner/Program.cs` (dziś: `drive`, `compare`, `axis`,
  `parity`, `braking`, `line`), format zapisu wejść z G-1,
  `.github/workflows/godot-first-run.yml`, `src/Sim/Train/DriveTelemetry.cs`.
- **Wyjście:** polecenie `Sim.Runner replay --keys PLIK --out CSV` liczące ten sam
  przejazd bez silnika; przeciążenie `DriveTelemetry.Row` przyjmujące przejazd ręczny
  (dziś przyjmuje **wyłącznie** `ScenarioDrive`, `DriveTelemetry.cs:28`); dwa nowe
  kroki w `godot-first-run.yml` — porównanie i kontrola negatywna.
- **Weryfikacja:**
  ```bash
  dotnet run --project src/Sim.Runner -c Release -- \
    replay --keys tests/data/manual-keys.log --out build/g2/core.csv
  "$GODOT_BIN" --headless --path src/Game -- \
    --replay="$PWD/tests/data/manual-keys.log" --telemetry="$PWD/build/g2/scene.csv"
  dotnet run --project src/Sim.Runner -c Release -- \
    compare build/g2/core.csv build/g2/scene.csv --tolerance 0
  ```
  Oczekiwane: zgodność przy progu 0; kontrola negatywna z jednym zmienionym wierszem
  zapisu kończy się kodem różnym od zera i wypisuje numer rozjeżdżającego się wiersza.
- **Skończone, gdy:** job `Godot first run` ma krok, który uruchamia scenę **bez**
  `--line`, `--shot` i `--telemetry=` sterowanego scenariuszem, kończy się sam
  (bez `timeout`), a jego kontrola negatywna jest wykonana i wklejona w treści
  commitu — jak przy sześciu istniejących bramkach tego workflow.
- **Poza zakresem:** `docs/03-legal.md`; zapis do `data/`; zmiana modelu fizyki;
  zmiana progu istniejących bramek `--line` i `--telemetry`.
- **Zależy od:** G-1.

### G-3 · Sterowanie przez `InputMap` i wiersz pomocy w HUD

- **Skąd:** Issue #26 §Sterowanie: „Nie wiązać logiki tylko z konkretnym keyboard
  layoutem; input actions Godot mapują QWERTY/AZERTY niezależnie od domeny".
  Oraz `src/Game/Input/DriverInput.cs:39` — stała `Help` opisująca sterowanie
  **nie jest wołana przez nic**, więc gracz nie ma skąd wiedzieć, czym prowadzi.
- **Wejście:** `src/Game/project.godot` (dziś **nie ma sekcji `[input]`**),
  `src/Game/Input/DriverInput.cs`, `src/Game/UI/Hud.cs`,
  `src/Game/Scenes/FirstRun.tscn`.
- **Wyjście:** sekcja `[input]` w `project.godot` z akcjami
  `driver_power`, `driver_brake`, `driver_coast`, `view_toggle`, `run_reset`,
  domyślnie przypisanymi do klawiszy, które już deklaruje `DriverInput.Help`;
  `DriverInput` czytający akcje zamiast `IsPhysicalKeyPressed`; szósty wiersz HUD
  z treścią `DriverInput.Help`; test w `tests/Game.Tests/` sprawdzający, że każda
  akcja z listy ma w `project.godot` co najmniej jedno przypisanie.
- **Weryfikacja:**
  ```bash
  dotnet test tests/Game.Tests/Game.Tests.csproj --configuration Release
  grep -c '^driver_' src/Game/project.godot
  xvfb-run -a "$GODOT_BIN" --rendering-driver opengl3 --resolution 1280x720 \
    --path src/Game -- --shot="$PWD/build/g3/HUD_cab_2000m.png" \
    --at-chainage=2000 --view=cab
  ```
  Oczekiwane: zielony `dotnet test`, `grep -c` daje liczbę akcji, a na zrzucie
  **widać wiersz pomocy** — opisany słowami w raporcie zadania, nie „wygląda dobrze".
- **Skończone, gdy:** `grep -rn "IsPhysicalKeyPressed" src/Game/` daje **0** trafień
  poza ewentualnym Esc, wszystkie akcje mają przypisanie w `project.godot`, a wiersz
  pomocy jest widoczny na zrzucie z kabiny i **niewidoczny** w trybach skryptowych
  (tak jak wiersze stacji i sygnalizacji, `Hud.cs:44–45`) — inaczej bramka wizualna
  zapłaci za tekst, którego nie było w baseline.
- **Poza zakresem:** `docs/03-legal.md`; zapis do `data/`; ocena estetyczna układu
  HUD poza dopisaniem jednego wiersza; nowe akcje sterujące (hamulec awaryjny, drzwi,
  przejęcie składu) — te czekają na odpowiedź P5 i na T-320.
- **Zależy od:** G-1 (bo `DriverInput` i tak jest wtedy otwierany).

### G-4 · Reset przejazdu resetuje cały przejazd

- **Skąd:** `src/Game/FirstRun.cs:865–872` — klawisz R zeruje `_state`,
  `_accumulator` i `_input`, ale **nie dotyka `_stations`**. Odczyt z kodu, nie
  z uruchomienia: `StationService` trzyma `_next`, `_calls`, `_missed` i ewentualny
  trwający `StationStop`, a chainage po resecie wraca do `_scenario.StartChainageM`
  (94,0 m). Skład wraca na początek osi z kolejką stacji ustawioną na tę, do której
  dojechał — a `_next` idzie tylko w przód (`StationService.cs` §„Przejechana stacja
  jest przejechana na zawsze"). Trwający cykl drzwi przeżywa reset.
- **Wejście:** `src/Game/FirstRun.cs` (`HandleViewKeys` 848, `BuildSimulation` 286),
  `src/Sim/Train/StationService.cs`.
- **Wyjście:** reset budujący `StationService` od nowa (albo jawna metoda `Reset`
  w rdzeniu, przybita testem w `tests/Sim.Tests/StationServiceTests.cs`);
  test w `tests/Game.Tests/` na czystej funkcji, która rozstrzyga, co reset obejmuje.
- **Weryfikacja:**
  ```bash
  dotnet test tests/Sim.Tests --configuration Release
  # odtworzenie z zapisu wejść: jedź do drugiej stacji, R, jedź jeszcze raz
  "$GODOT_BIN" --headless --path src/Game -- \
    --replay="$PWD/tests/data/manual-reset.log" --telemetry="$PWD/build/g4/po-resecie.csv"
  ```
  Oczekiwane: w logu po resecie `[STACJA]` wypisuje **Beekkant** jako obsłużoną
  po raz drugi, a nie stację leżącą 1,5 km dalej; licznik `obsłużone` wraca do zera.
- **Skończone, gdy:** przejazd po resecie ma tę samą sekwencję wywołań stacji, co
  przejazd bez resetu z tym samym zapisem wejść, przy progu **0** dla kolumn
  `chainage_m` i `stop_error_m`; kontrola negatywna — reset bez wyzerowania
  `StationService` daje inną sekwencję i test to pokazuje z nazwą padającego testu.
- **Poza zakresem:** `docs/03-legal.md`; zapis do `data/`; ocena estetyczna; zmiana
  reguły „przejechana stacja jest przejechana na zawsze" — ta jest świadoma
  i udokumentowana, zadanie jej nie rusza.
- **Zależy od:** G-1 (weryfikacja wymaga odtwarzalnego wejścia).

### G-5 · Kabina pod sygnalizacją: człowiek prowadzi, ATP pilnuje

> **G-5 JEST ZROBIONE — #257, 05.09.2026.** Ten akapit jest dopisany po to samo, co
> blok nad §G-1: żeby propozycja nie wysłała nikogo drugi raz w to samo miejsce. Sekcja
> niżej zostaje jako zapis tego, co proponowano, i **nie opisuje dzisiejszego stanu**.
> Sprawdzone lekturą drzewa na `6fa604c`:
>
> | czego G-5 żądało | co jest |
> |---|---|
> | źródło polecenia jako parametr, autopilot bez zmiany śladu | tożsamość `--line` zmierzona: trzy pliki zatrzymań identyczne co do bajtu wobec drzewa sprzed zmiany |
> | `--signalling` dopuszczone bez `--line` | tak; `--limit-kmh` bez `--line` **zostaje odmową** i to jest treść, nie pozostałość (usterka z #246) |
> | ATP wpięte tym samym hakiem, co w `LineCore` | `src/Sim/Signalling/CabProtection.cs` + `tests/Sim.Tests/CabProtectionTests.cs` |
> | wiersz sygnalizacji HUD działający w trybie ręcznym | `src/Game/SignallingHud.cs` + `tests/Game.Tests/SignallingHudTests.cs` |
>
> **Zmierzone, nie zadeklarowane:** sufit 76 km/h wobec limitu planu 72 daje **307,239 m**
> różnicy drogi i 3253 ingerencje służbowe; przy suficie równym limitowi planu ślad jest
> **identyczny co do bitu** z przejazdem bez ochrony (`manual-keys.log`: 0 ostrzeżeń,
> 0 ingerencji). Scena wobec rdzenia pod ATP: 201 wierszy identycznych co do bajtu,
> próg 0.
>
> **Znalezisko, którego ta propozycja nie przewidziała:** przejazd ręczny startuje
> z czołem na 94,000 m, czyli już w bloku szlakowym S01, z ogonem w peronowym P01.
> Dopóki nastawnia pytała tylko o blok czoła, kabina nie dostawała **ani jednej trasy** —
> autorytet 462,730 m, `BlockNotReserved`, 1998 kroków hamowania awaryjnego przed
> pierwszą stacją. „Stoi w bloku" czyta się teraz jako „zajmuje blok".
>
> **Zostało otwarte i czeka na decyzję właściciela:** przy suficie równym limitowi planu
> przejazd dostaje 2118 ingerencji **awaryjnych** — nie przez większość przejazdu, tylko
> przez **8,8 %**: trzy epizody po 5,883 s na ostatnich 102,3 m dojazdu do peronu, każdy
> kończący się przy wjeździe czoła w blok peronowy, przy prędkości dokładnie 72,00 km/h.
> Maszynista niczego nie łamie — kończy się autorytet, a krzywą prędkości dopuszczalnej
> wyznacza hamulec służbowy, więc jej przekroczenie od razu wymaga więcej niż służbowego.
> Pytanie brzmi: **czy nastawnia ma ryglować trasę o odcinek do przodu.** Nie zgadnięte.
>
> **Bramka CI dla kabiny pod sygnalizacją** — jedyna część G-5 niezrobiona w #257 —
> **jest od #261**. Krok „Cab under signalling…" porównuje scenę z rdzeniem przy progu 0
> na obu rytmach klatek i osobno sprawdza, że obie strony wypisały ten sam wiersz `[ATP]`;
> telemetria nie ma kolumny z ochroną, więc bez tego dwie strony mogłyby trafić w ten sam
> przejazd, licząc ostrzeżenia inaczej.
>
> Przy zakładaniu tej bramki wyszła pułapka: **`--signalling` znaczy po każdej stronie co
> innego.** Scena nie ma przełącznika ATP, bo plan `classic_2026` JEST systemem z ochroną
> (ten sam argument, co przy `LineCore.M7(atp: true)` w #234), a `Sim.Runner replay` ma
> `--atp` osobno, bo bez tego nie dałoby się zbudować negatywu „ten sam przejazd bez
> ochrony musi się różnić". Zmierzone: scena z samym `--signalling` zgadza się co do bajtu
> z rdzeniem `--signalling --atp` (201 wierszy), a z rdzeniem bez `--atp` **nie**.

- **Skąd:** §1.3 tego raportu (tryb ręczny i tryb z sygnalizacją są rozłączne
  z powodu trzech odmów w `RunPlan`) oraz Issue #26 §Weryfikacja funkcjonalna:
  „nie można ominąć ATP przez input gracza". Rdzeń ma wszystko:
  `TrainProtection.Supervise`, `ProtectionDecision.Apply` (decyzja właściciela
  z 04.09.2026: „ostrzeżenie, potem hamulec służbowy") i hak
  `LineDrive.Supervisor` (`src/Sim/Train/LineDrive.cs:185`). Brakuje **szwu na
  źródło polecenia**: `LineDrive.Command` jest prywatne (`LineDrive.cs:337`)
  i nie da się go zastąpić człowiekiem.
- **Wejście:** `src/Sim/Train/LineDrive.cs`, `src/Sim/Train/StationService.cs`,
  `src/Sim/Line/LineCore.cs`, `src/Sim/Signalling/TrainProtection.cs`,
  `src/Game/RunPlan.cs:237,246,253`, `src/Game/FirstRun.cs`,
  `data/design/signalling/classic-2026.json`.
- **Wyjście:** w rdzeniu — źródło polecenia jako parametr (`Func<double,
  DriverCommand>?` albo równoważny), domyślnie dzisiejszy autopilot, więc ślad
  przejazdu `--line` **nie zmienia się o ani jeden bit**; w scenie — `--signalling`
  i `--limit-kmh` dopuszczone także bez `--line`, ATP wpięte tym samym hakiem co
  w `LineCore`; wiersz sygnalizacji HUD (`FirstRun.SignallingLine`, dziś zwraca
  pustkę poza `--line`, `FirstRun.cs:940`) działający w trybie ręcznym.
- **Weryfikacja:**
  ```bash
  # 1. tożsamość: autopilot z nowym szwem daje ten sam przejazd co przed zmianą
  dotnet run --project src/Sim.Runner -c Release -- \
    line --axis data/track/L1_A.json --limit-kmh 70 --exchange-s 8 --load AW2 \
    --brake-usage 1.0 --stop-window-m 5 --calls build/g5/core-calls.csv
  dotnet run --project src/Sim.Runner -c Release -- \
    compare build/g5/core-calls.csv build/t400/linia/core-calls.csv --tolerance 0
  # 2. ATP hamuje za człowieka: zapis wejść z pełnym ciągiem przez blok zajęty
  "$GODOT_BIN" --headless --path src/Game -- \
    --replay="$PWD/tests/data/manual-overspeed.log" --limit-kmh=76 \
    --signalling="$PWD/data/design/signalling/classic-2026.json" \
    --telemetry="$PWD/build/g5/atp.csv"
  ```
  Oczekiwane: (1) próg **0**, przejazd autopilota niezmieniony; (2) w logu
  `ATP HAMUJE: ServiceIntervention` i prędkość szczytowa **niższa** od tej samej
  jazdy bez `--signalling` — kontrola negatywna jak w kroku „Negative control — the
  same run without ATP must differ" istniejącego workflow.
- **Skończone, gdy:** przy tym samym zapisie wejść „pełny ciąg do końca" przejazd
  z `--signalling` ma prędkość szczytową **mniejszą** niż bez niego o zmierzoną
  liczbę wpisaną do raportu zadania, `[STACJA]` nie odnotowuje żadnego wywołania
  z otwarciem drzwi poza oknem ±5,0 m, a ślad `--line` bez wejścia gracza jest
  identyczny co do bitu z `build/t400/linia/core-calls.csv` sprzed zmiany.
- **Poza zakresem:** `docs/03-legal.md`; zapis do `data/`; ocena estetyczna;
  przejęcie i oddanie składu (`take/release control`) — zależy od T-320;
  hamulec awaryjny jako polecenie — czeka na odpowiedź P5; **jakakolwiek możliwość
  wyłączenia ATP przez gracza** — #26 zabrania wprost.
- **Zależy od:** G-1, G-2.

### 3.6 Czego świadomie **nie** proponuję

- **Przejęcie i oddanie składu** (`take control` / `release control` z #26) —
  wymaga linii z wieloma składami, czyli **T-320**, który `docs/TASKS.md` ma jako
  fazę 2, „NASTĘPNA", i który nie jest zamknięty. Kabina jako widok linii,
  po której jeżdżą inne składy, nie ma dziś czego być widokiem — i to jest ta sama
  zasada porządkująca, którą `docs/TASKS.md` §Plan już zapisał.
- **Pulpit, wnętrze kabiny, dźwięk** — T-902, T-905, `docs/03-legal.md`, brak
  publicznego rysunku pulpitu M7. #26 stawia je poza zakresem vertical slice'a.
- **Menu, wybór scenariusza, zapis stanu gry** — nie ma o nich ani słowa
  w `docs/`, ani w #26. Zadanie wymyślone tutaj byłoby dokładnie tym, czego
  zabrania `CLAUDE.md` §8.

---

## 4. Pytania do właściciela

Każde ma warianty i zmierzoną albo odczytaną konsekwencję. Żadne nie da się
rozstrzygnąć z repozytorium — sprawdziłem `docs/`, `data/` i Issue #26.

### P1 · Jaką prędkość dopuszczalną ma tryb ręczny?

Dziś: **80 km/h, prędkość konstrukcyjna M7**, i nie da się jej podać (`--limit-kmh`
bez `--line` jest odmową, `RunPlan.cs:253`). To jest ta sama klasa usterki, którą
naprawiał `RunHeader` dla `--line`.

| wariant | konsekwencja |
|---|---|
| (a) tryb ręczny **wymaga** `--limit-kmh`, tak jak `--line` | spójne z tym, co repo już zrobiło; ale **uruchomienie bez argumentów przestaje działać**, a to jest dziś jedyny sposób, w jaki „gra się uruchamia" |
| (b) bez argumentów startuje z **58,68 km/h** jako jawnym założeniem | 58,68 km/h to **zmierzone dolne ograniczenie** z rozkładu (T-401, `reports/T-401-line-run.md`), nie zgadnięta liczba; gra jedzie wolniej, niż jest w rzeczywistości możliwe, i mówi o tym w nagłówku i w HUD |
| (c) zostaje 80 km/h | gracz prowadzi z prędkością konstrukcyjną pojazdu jako limitem toru; `docs/TASKS.md` mówi wprost, że to nie jest prędkość dopuszczalna — usterka zostaje, tylko przestaje być nowa |

### P2 · Czy przejazd ma wynik?

Rdzeń **już mierzy** wszystko, czego wynik by potrzebował: `StationCall` niesie
`StopErrorM`, `ArrivalSeconds`, `DepartureSeconds`, a `StationService` liczy
`Calls` i `Missed`. T-113 ma zmierzony rozkład (29 554 zatrzymań).

| wariant | konsekwencja |
|---|---|
| (a) brak wyniku — przejazd po prostu się kończy | zero pracy poza G-1…G-5; gra jest symulatorem bez pętli zwrotnej dla gracza |
| (b) **tabela liczb bez oceny** na koniec: błędy zatrzymania, czasy postoju, odchyłka od rozkładu T-113 | tanie — wszystkie liczby już są; nic nie trzeba zgadywać; nie wymaga żadnej nowej danej o sieci |
| (c) ocena / punktacja | wymaga **progów**, których nie ma w żadnym źródle („dobre zatrzymanie" to ile centymetrów?); w tym projekcie taki próg wraca potem jako pytanie w `docs/24` |

### P3 · Co się dzieje po minięciu stacji?

`StationService` ma dziś regułę i jest ona świadoma: stacja minięta o więcej niż
5,0 m ląduje w `Missed`, kolejka idzie dalej, i **nie da się tego cofnąć**, bo
`DriverCommand` nie ma kierunku — nie ma biegu wstecznego.

| wariant | konsekwencja |
|---|---|
| (a) tak jak dziś: licznik `minięte` rośnie, przejazd trwa | zero pracy; gracz może przejechać cały pakiet, nie zatrzymując się ani razu, i nic mu nie powie, że to jest źle |
| (b) minięta stacja kończy przejazd | wymaga stanu „koniec przejazdu" (P4); jest to najostrzejsza możliwa reguła i nie ma dla niej źródła w praktyce STIB |
| (c) wolno cofnąć na peron | **zmiana modelu rdzenia**: `DriverCommand` musiałby dostać kierunek, a `TrainController` jawnie „nie odtacza się w tył" (`TrainController.cs` §Skąd różnica). To jest praca w T-310, nie w warstwie gry |

### P4 · Czy istnieje stan „koniec przejazdu", i co gracz wtedy widzi?

Dziś przejazd ręczny **nie kończy się nigdy** (§1.4). Tryby `--line` i `--telemetry`
kończą się `GetTree().Quit()`, czyli zamknięciem okna.

| wariant | konsekwencja |
|---|---|
| (a) okno się zamyka, jak dziś w `--line` | zero pracy; dla gracza wygląda jak awaria |
| (b) przejazd zatrzymuje się na ostatniej stacji, HUD pokazuje podsumowanie, Esc zamyka | mała praca; łączy się z P2 wariant (b); nadal nie ma menu |
| (c) powrót do menu / wybór następnego przejazdu | menu **nie istnieje** i nie ma go w żadnym dokumencie ani w #26; byłoby to nowe zadanie o nieokreślonym zakresie |

### P5 · Które akcje sterujące z #26 istnieją w pierwszej grywalnej wersji?

#26 §Sterowanie wymienia: traction ±, brake ±, **emergency brake**, door
release/open/close, camera switch, take/release control. Trzy pierwsze grupy mają
problem, którego #26 nie mógł znać:

- **hamulec awaryjny jako polecenie w rdzeniu nie istnieje** i jest to zapisane
  wprost: *„Hamowanie awaryjne jako **polecenie** nie istnieje w T-310/T-400
  i T-313 go nie dokłada"* (`src/Sim/Signalling/TrainProtection.cs`,
  `ProtectionDecision.Apply`);
- **drzwi** są dziś prowadzone przez `DoorCycle` automatycznie po zatrzymaniu
  w oknie; ręczne otwieranie i zamykanie to nowy stan w `StationStop`;
- **take/release control** wymaga T-320.

| wariant | konsekwencja |
|---|---|
| (a) minimum: ciąg, hamulec, wybieg, kamera — czyli to, co `DriverInput` już ma | G-1…G-5 wystarczają; „przejechać odcinek" jest osiągalne, ale gracz nie obsługuje drzwi ręcznie |
| (b) + hamulec awaryjny **jako pełny hamulec służbowy** (dokładnie to, co robi dziś `ProtectionDecision` dla `EmergencyIntervention`) | jeden klawisz, zero nowej fizyki, ale nazwa obiecuje więcej, niż model daje — i `DemandExceedsServiceBrake` już dziś to pokazuje zamiast zamiatać |
| (c) + hamulec awaryjny jako **osobne opóźnienie** w modelu | praca w rdzeniu (T-310/T-311), nie w warstwie gry; `VehicleModel.DesignEmergencyBrakeMps2` istnieje, więc liczba jest, ale nie ma jej jako **polecenia** i to jest świadome |

---

## 5. Ryzyka

### 5.1 Wejście gracza było próbkowane czasem klatki — **ryzyko zdjęte przez #239**

> **Ten punkt jest przepisany, a nie dopisany obok.** Jego poprzednia wersja mówiła
> „wejście gracza **jest** próbkowane czasem klatki" i kończyła się zdaniem
> „**Lekarstwo jest w G-1**". Lekarstwo weszło tego samego dnia jako #239 (gałąź
> `2c19026`, scalona jako `c787198`), więc czas teraźniejszy tu kłamie.
> Pomiar zostaje **nieprzeliczony i w całości**, bo to on jest uzasadnieniem tamtej
> naprawy — te same pięć wierszy stoi w komunikacie commita `2c19026` jako „pomiar
> przed naprawą". Rozjazd 0,234166 m na 60 s jest faktem o drzewie `3c242f7`, a nie
> o dzisiejszym.

**Było to największe ryzyko techniczne tego rozpoznania**, bo uderzało wprost w regułę
z `docs/01-architecture.md` i w kryterium odbioru z #26.

Pętla wygląda tak [Z KODU, `FirstRun.cs:602` i `:636–658`]: raz na klatkę
`_input.Poll(delta)` przesuwa nastawnik o `0,80 · Δt_klatki`, po czym **wszystkie**
kroki tej klatki dostają to samo polecenie. Przy 60 kl./s nastawnik rośnie
skokami po 0,01333 stosowanymi przez 2 kroki; przy 120 kl./s — po 0,00667
stosowanymi przez 1 krok. To są dwie różne trajektorie polecenia dla tej samej
sekwencji wciśnięć klawiszy.

[ZMIERZONE] Metoda: odtworzyłem tę pętlę **bez Godota** w programie konsolowym
przeciw `src/Sim/Sim.csproj` — arytmetyka `DriverInput.Poll` przepisana jeden do
jednego, `StepAccumulator.StepsForFrame(1/fps)` i `TrainController.Advance`
z warunkami M7/AW2/tunel, limit 70 km/h. Scenariusz: 30 s trzymanego W, potem 30 s
trzymanego S. Program leżał poza repozytorium (`--no-geometry` nie jest tu potrzebne,
bo nie ma sceny) i **nie jest komitowany**; jego pętla to dosłownie:

```csharp
for (var f = 0L; f < frames; f++) {
    (throttle, brake) = Poll(throttle, brake, 0.80, 1.0 / fps, key);
    var command = new DriverCommand(throttle, brake).Clamped();
    for (var i = 0L; i < accumulator.StepsForFrame(1.0 / fps); i++)
        state = controller.Advance(state, conditions, command, limit, step, out _);
}
```

Wynik:

```
tempo nastawnika 0.80 1/s, 60 s: 30 s trzymanego W, potem 30 s trzymanego S
  fps        kroki      droga [m]     v [km/h]
120.00         7200     566.407284      0.0000   Δdroga vs 120 fps =   0.000000 m
 60.00         7200     566.641450      0.0000   Δdroga vs 120 fps =  +0.234166 m
 59.94         7199     566.178225      0.0000   Δdroga vs 120 fps =  -0.229059 m
 30.00         7200     566.485619      0.0000   Δdroga vs 120 fps =  +0.078335 m
144.00         7199     566.502278      0.0000   Δdroga vs 120 fps =  +0.094993 m
```

Rozjazd **0,234166 m na 60 s** i różnica **jednego kroku** przy 59,94 i 144 kl./s.
Dla porównania: dzisiejsze bramki `godot-first-run.yml` porównują telemetrię przy
progu **0**, a okno zatrzymania na stacji ma ±5,0 m. Rozjazd jest więc dziś
nieszkodliwy dla rozgrywki i **śmiertelny dla każdej bramki**, jaką dałoby się na
tryb ręczny założyć. Lekarstwo jest w G-1 i jest dokładnie tym, co
`docs/01-architecture.md` już nakazuje: znacznik **kroku**, nie czasu ściennego.

### 5.2 Wejście gracza a bramki porównujące telemetrię co do bitu

Dzisiejsze bramki działają dlatego, że po obu stronach porównania stoi **ten sam
skrypt**: `ScenarioDrive` w `Sim.Runner` i `ScenarioDrive` w scenie. Człowiek nie ma
odpowiednika w `Sim.Runner`, więc przejazdu ręcznego nie da się porównać z niczym —
i to jest realny powód, dla którego tej bramki dziś nie ma, a nie przeoczenie.

Jedyne uczciwe wyjście jest już zapisane w #26: *„scenariusz headless Sim
i scenariusz uruchomiony przez Godot kończą się tym samym hash state **przy tych
samych commandach**"*. Czyli: zapis wejść staje się scenariuszem, a bramka porównuje
odtworzenie z odtworzeniem. To jest G-1 + G-2 i **nie da się tego obejść** —
porównywanie „na żywo" prowadzonego przejazdu z czymkolwiek nie ma sensu.

~~Drobna przeszkoda techniczna, na którą warto się przygotować:
`DriveTelemetry.Row` przyjmuje **wyłącznie** `ScenarioDrive`
(`src/Sim/Train/DriveTelemetry.cs:28`), więc przejazd ręczny nie umie dziś nawet
wypisać wiersza w formacie, którym mierzy się wszystko inne.~~
**Przeszkoda zniknęła w #239 i to zdanie jest przepisane, a nie dopisane obok:**
`DriveTelemetry` ma dziś **dwa** przeciążenia `Row` — jedno bierze `ScenarioDrive`,
drugie składniki (`DriveState`, `FixedStep`, chainage, przyspieszenie, …), a
`FirstRun.ManualTelemetryRow()` woła to drugie. Przejazd ręczny wypisuje więc wiersz
w tym samym formacie co reszta i wiersz zerowy przed pierwszym krokiem także.

### 5.3 `LineDrive` ma okno zatrzymania **jednostronne** — dla człowieka to znaczy drzwi w tunelu

Zapisał to `StationService` w swoim własnym komentarzu i warto to podnieść, bo
najprostsza droga do „kabiny pod sygnalizacją" prowadzi przez `LineDrive`:

> `LineDrive` uznaje zatrzymanie za wywołanie stacji, gdy czoło stanie w
> `chainage >= cel − okno`, **bez ograniczenia z góry**. Dla autopilota, który staje
> z błędem 0,31 m, ten warunek nigdy nie wychodzi poza peron. Dla CZŁOWIEKA wychodzi
> natychmiast: skład zatrzymany 200 m za stacją spełniałby go tak samo dobrze
> i otworzyłby drzwi w tunelu.

Czyli: G-5 **nie może** po prostu podstawić człowieka pod `LineDrive.Command`.
Reguła rozpoznania stacji musi zostać ta z `StationService` (dwustronna, ±5,0 m),
a `LineDrive` dostać źródło polecenia jako parametr — inaczej dwie reguły stacji
zaczną się rozjeżdżać, a to jest wprost ta klasa błędu, przed którą broni się cały
ten kod („dwie kopie tej samej wiedzy w jednym przebiegu rozjechałyby się").

### 5.4 Reset (R) rozsynchronizowywał obsługę stacji — **ryzyko zdjęte przez G-4**

> **Ten punkt jest przepisany, a nie dopisany obok.** Jego poprzednia wersja mówiła
> „`FirstRun.cs:865–872` zeruje stan dynamiczny i **nie dotyka** `StationService`"
> i kończyła się zdaniem „Naprawa: G-4". Naprawa weszła, więc czas teraźniejszy tu
> kłamie. Odczyt z kodu zostaje jako opis usterki, bo to on jest uzasadnieniem tamtej
> zmiany.

**Było:** reset zerował stan dynamiczny składu i nie dotykał `StationService`.
Po resecie skład stał na 94,0 m, a kolejka stacji wskazywała tę, do której zdążył
dojechać; `_next` idzie tylko w przód, więc pominiętych peronów nie dało się obsłużyć.
Trwający cykl drzwi przeżywał reset.

**Jest:** decyzja „co reset obejmuje" wyszła z węzła Godota do `src/Game/RunReset.cs`
(bez Godota, więc wołalna z testu), a `StationService` dostał jawny `Reset()`, którego
konstruktor i reset dzielą jeden prywatny `StartFromScratch()` — stan po resecie nie ma
jak różnić się od stanu po utworzeniu. [ZMIERZONE, `RunResetTests`] przejazd wzorcową
sekwencją klawiszy z `tests/data/manual-keys.log`, 5401 kroków: przed resetem
`drzwi=Open postoj=12,975 s trakcja=ZABLOKOWANA obsluzone=1`, po resecie
`drzwi=Closed postoj=0,000 s trakcja=WOLNA obsluzone=0 nastepna=Beekkant`.
Przejazd powtórzony po resecie daje ten sam `StationCall` co przejazd bez resetu,
przy progu **0** na wszystkich polach rekordu.

**Domknięte 05.09.2026 decyzją właściciela — wariant W1.** Ten akapit jest przepisany,
a nie dopisany obok: stało w nim, że „`C` i `R` nadal nie trafiają do zapisu wejść, więc
przejazd Z RESETEM nie odtworzy się z pliku". Dla `R` przestało to być prawdą.
Format zapisu ma wersję **2** z wpisem `krok;reset`, a numer kroku został rozdzielony
na dwa: zapis indeksuje **sesję** i nie wraca po resecie, `DriveState.Steps` indeksuje
**przejazd** i zaczyna od zera. [ZMIERZONE] wzorzec `tests/data/manual-keys-reset.log`
(dwie połowy po 5400 kroków, reset między nimi, w 45,000 s, czyli w środku cyklu drzwi
na Beekkant) odtwarza się rdzeniem i sceną **co do bajtu**, przy 120 i przy 7 krokach
na klatkę, a przejazd po resecie jest co do bajtu tym samym przejazdem, co niezależny
przejazd bez resetu. Bramka: krok „Manual mode — a run with a reset replays to the same
bytes" w `godot-first-run.yml`.

**`C` (widok) świadomie do zapisu NIE wchodzi** i to nie jest niedokończona połowa:
klawisz widoku nie wpływa na fizykę o ani jeden bit, więc do odtworzenia przejazdu nie
jest potrzebny. Miałby znaczenie wyłącznie przy odtwarzaniu ZRZUTU, a zrzuty i tak
zamawia `--view`.

W trybie `--line` klawisz R jest **bezgłośnie bezskuteczny** — `_state` jest
w następnym kroku nadpisywane z `_line.State`. Nie jest to usterka, ale jest to
zachowanie, o którym HUD **do 05.09.2026** nie mówił ani słowa. Decyzja właściciela
z tego dnia: zachowanie zostaje, HUD ma to powiedzieć — i mówi.

Przy okazji okazało się, że sprawa jest szersza niż sam `R`: pod `--line` nie działa
też `W`, `S`, `X` ani `Spacja`, bo `StepOnce` nadpisuje stan składu z `_line.State`.
Wiersz pomocy obiecywał **siedem** klawiszy, z których działały **dwa**.
[OBEJRZANE, klatka `--line` z Movie Makera 1280×720] ostatni wiersz HUD-u brzmi dziś:
`C widok · Esc wyjście · prowadzi rdzeń: W, S, X, Spacja, R nie działają`.
W trybie ręcznym wiersz jest bez zmian — pełne siedem pozycji.

### 5.5 Tryb ręczny nie ma żadnej bramki i wisi w nieskończoność

[URUCHOMIONE] `timeout 60 … --no-geometry` → kod **124**. Nie ma `--max-steps`,
nie ma `--until-chainage`, nie ma warunku końca. Dopóki tak jest, CI go nie
uruchomi — a to znaczy, że `TrainView.PlaceAt` (co `docs/TASKS.md` 6.B12 już
odnotowuje), wpięcie `StationService` i cała warstwa wejścia mogą się zepsuć
i wszystkie dziesięć workflow zostanie zielonych. To jest dokładnie ta rodzina
„zielonych bramek, które niczego nie sprawdzały", którą audyt z 02.09.2026 znalazł
cztery razy.

### 5.6 Ryzyko oczekiwań: widok z kabiny jest dziś kamerą w pustce

`FirstRun.cs:771` w widoku kabinowym **ukrywa cały skład**, bo skorupa M7 ma po
`solidify` obie powierzchnie i z bliska widać jej wnętrze. Kabina jako model nie
istnieje i nie powstanie bez T-902 (estetyka) i bez rysunku pulpitu, którego STIB
nie publikuje (`docs/21`, T-220). „Człowiek siada w kabinie" znaczy dziś:
kamera 2,20 m nad główką szyny, 1,80 m za czołem, i HUD. To jest zgodne z #26
(„finalna kabina M7" jest poza zakresem) — ale warto, żeby oczekiwanie było
wypowiedziane przed, a nie po pierwszym uruchomieniu.

### 5.7 Prawo

**Żadna z pozycji §3 nie dotyka `docs/03-legal.md`.** Sterowanie, ATP, cykl drzwi,
wynik przejazdu i `InputMap` to mechanika. Pierwsza rzecz z tej drogi, która blokad
dotknie, to wygląd pulpitu i oznakowanie w kabinie — a te są poza zakresem #26
i czekają na T-902 i T-903.

---

## 6. Co zauważyłem przy okazji i czego nie tknąłem

- **`DriverInput.Help` jest martwą stałą** — nie ma żadnego wołającego. Gracz
  uruchamiający scenę nie ma na ekranie ani jednego znaku o tym, czym prowadzić.
  Objęte G-3, nie naprawiane tutaj.
- **`--line` odczytuje klawiaturę i wyrzuca wynik** co klatkę (`FirstRun.cs:602`
  vs `:678` i `:698`). Kosztuje to jedno wołanie na klatkę i nic nie psuje, ale
  czytelnik kodu może wziąć to za działające sterowanie.
- **W kolejce agenta (`docs/TASKS.md` fazy 5 i 6) nie ma ani jednej pozycji
  o prowadzeniu przez człowieka.** Zapas kolejki liczy `tools/tests/test_backlog.py`
  i jest dziś powyżej progu, więc nic tego nie wymusi; grywalność wejdzie do kolejki
  tylko decyzją właściciela.
- **`docs/TASKS.md` §Plan stawia T-320 przed Issue #26** i uzasadnia to zdaniem
  przewodnim z `docs/01-architecture.md`. Propozycje §3 tego **nie odwracają**:
  G-1…G-5 dotyczą jednego składu na osi i nie wymagają T-320. Dopiero
  `take/release control` wymaga.
- **Nie generowałem geometrii pakietu A** (`build/t400/` nie istnieje w tym
  środowisku), więc nie oglądałem ani jednego zrzutu. Rozpoznanie dotyczy łańcucha
  sterowania; §5.6 opiera się na odczycie kodu i na `docs/21`, nie na obrazie —
  i jest tak oznaczone.
- **Nie uruchomiłem `doctor.sh`** — środowisko tej sesji odmówiło wykonania skryptu.
  Zamiast tego wykonałem obie kontrole, które on zbiera:
  `python3 tools/tests/test_all.py` → **1493/1493 przeszło**, oraz budowę warstwy
  silnika (`dotnet build src/Game/MetroBxl.Game.csproj` → `Build succeeded,
  0 Warning(s), 0 Error(s)`).
