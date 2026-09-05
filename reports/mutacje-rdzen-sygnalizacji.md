# Przegląd mutacyjny rdzenia sygnalizacji i linii — dwa niezależne pomiary

**Stan raportu:** scalenie dwóch przeglądów wykonanych **niezależnie i równolegle**,
bez wiedzy jednego o drugim. Scalone na `3c242f7` (`main`, 05.09.2026).

| | przegląd **A** | przegląd **B** |
|---|---|---|
| gałąź | `przeglad-mutacyjny-sygnalizacji` (PR #229) | `przeglad-mutacyjny-sygnalizacji-42` (PR #230) |
| commit raportu | `a3d8c57` | `cbd1192` |
| mierzony commit `main` | `d495051` | `b41c158` |
| mutacji | 45 | 42 |
| zabitych | 35 | 28 |
| **ocalałych** | **10** | **14** |
| niekompilowalnych | 0 | 0 |
| pokrycie tej próbki | 77,8 % | 66,7 % |

Oba przeglądy powstały przez **pomyłkę orkiestracji**: to samo zadanie poszło do dwóch
agentów naraz i oba zapisały wynik pod tą samą ścieżką. Praca żadnego z nich nie była
błędem — i to jest ważniejsze niż pomyłka, która ją wywołała, bo **dwa niezależne pomiary
tego samego kodu, zgodne w kluczowych punktach, są dowodem, którego pojedynczy przebieg
dać nie może.** Ten raport jest zbudowany wokół tej zgodności, a nie wokół sumy dwóch
plików.

**Kodu produkcyjnego nie tknięto w żadnym z trzech przebiegów** — dwóch oryginalnych ani
w rozstrzygnięciu z sekcji 2. `git status --porcelain` jest pusty, `dotnet test` daje
376/376.

---

## 0. Wynik, w jednym zdaniu

Dwa przeglądy zmierzyły **56 różnych miejsc** w pięciu plikach rdzenia; w **28 miejscach
wykonały dokładnie tę samą mutację i dokładnie tak samo ją rozstrzygnęły** — zero
sprzeczności werdyktu na całym przecięciu. Suma daje **19 miejsc, których zestaw testów
nie przybija**, a najgroźniejsze z nich, **`steps - last` → `steps + last` w dławiku
żądań tras, ocalało w obu przeglądach niezależnie**.

Dwie liczby ocalałych — 10 i 14 — **nie są sprzecznością i nie wolno ich uśredniać.**
Są wynikiem dwóch **różnych zbiorów mutacji**: 14 mutacji A nie ma w B, 11 mutacji B nie
ma w A, a trzy miejsca dostały w obu przeglądach mutację tego samego kontraktu, ale
o innej sile. Sekcja 1 rozlicza to co do sztuki.

---

## 1. Skąd 10, a skąd 14 — rozliczenie co do sztuki

Podstawą porównania nie jest identyfikator (te **kolidują**: `FB-07` u A to strażnik
długości składu w `RegisterTrain`, `FB07` u B to stała `PositionEpsilonM`), tylko
**miejsce w kodzie i treść podmiany**.

| kategoria | mutacji A | mutacji B | miejsc |
|---|---:|---:|---:|
| identyczna mutacja w obu przeglądach | 28 | 28 | 28 |
| to samo miejsce, inna siła podmiany | 3 | 3 | 3 |
| wyłącznie w A | 14 | — | 14 |
| wyłącznie w B | — | 11 | 11 |
| **razem** | **45** | **42** | **56** |

Rachunek zamyka się dokładnie w obie strony: 28 + 3 + 14 = 45 i 28 + 3 + 11 = 42.
**87 przebiegów mutacyjnych pokrywa 59 różnych podmian w 56 miejscach** — 28 podmian
wykonano dwa razy.

Ocalałe rozkładają się tak:

| | A | B |
|---|---:|---:|
| ocalałe **potwierdzone przez oba przeglądy** (ta sama mutacja) | 4 | 4 |
| ocalałe na tym samym miejscu, inna siła podmiany (`DefaultRequestIntervalSteps`) | 1 | 1 |
| ocalałe wyłącznie w A | 5 | — |
| ocalałe wyłącznie w B | — | 9 |
| **razem** | **10** | **14** |

**19 różnych miejsc rdzenia nie jest przybitych.** Ani „10", ani „14" nie jest tą liczbą;
każda z nich jest prawdziwa dla swojej próbki i tylko dla niej. Różnica 10 ↔ 14 bierze
się w całości z doboru próbki, nie z rozbieżności pomiaru.

### 1.1 Zgodność na przecięciu jest zupełna

Na **28 mutacjach wykonanych identycznie przez oba przeglądy werdykt zgadza się
28 razy na 28**. Ani jednej mutacji, którą jeden przegląd uznał za zabitą, a drugi za
ocalałą. To jest najmocniejsze pojedyncze zdanie w tym raporcie: gdyby któryś
z przebiegów miał wadę metody — źle przywracany plik, mutacja trafiająca w inne miejsce
niż deklarowane, wyrocznia licząca co innego niż deklaruje — 28-krotna zgodność z drugim,
niezależnym przebiegiem byłaby nieprawdopodobna.

---

## 2. Jedyne twierdzenie, które trzeba było rozstrzygnąć wykonaniem

**TP-08 / TP08** — `speedMps > permitted` → `>=` w `TrainProtection.Supervise`.
Oba przeglądy zgadzają się, że mutacja **ocalała**. Rozchodzą się co do tego, czy jest
groźna:

- **A** klasyfikuje ją jako **najważniejsze znalezisko całego przeglądu** i podaje pomiar:
  4492 kroki z prędkością dokładnie równą limitowi, **0 ostrzeżeń i 4492 ingerencje
  służbowe**.
- **B** klasyfikuje ją jako **klasę C — „granica, której bateria nie dotknęła"** i podaje
  pomiar: „94 060 kroków przejazdu z ATP: `v == v_dop` **0 razy**, `v > v_dop` 4576,
  `v < v_dop` 89 484".

To nie są dwie interpretacje jednej liczby — to dwa twierdzenia o osiągalności granicy,
z których jedno mówi 4492, a drugie 0. Wpisanie obu obok siebie byłoby ucieczką od
rozstrzygnięcia, więc **granicę zmierzono trzeci raz**, sondą poza drzewem repozytorium
odwołującą się do `src/Sim/Sim.csproj`, na pakiecie A (`data/design/signalling/classic-2026.json`
+ `data/track/L1_A.json`), M7 AW2, tunel, sucha szyna, ATP włączone.

### Kod czysty — dwa limity przejazdu, ta sama linia

```
LIMIT 72.00 km/h plan_dop=72.00 km/h | krokow=89666 v==dop=4492 v>dop=0    v<dop=85174 | ostrzezen=0    sluzbowych=0    awaryjnych=0 czas=747.23 s
LIMIT 76.00 km/h plan_dop=72.00 km/h | krokow=94059 v==dop=0    v>dop=4576 v<dop=89483 | ostrzezen=4576 sluzbowych=4576 awaryjnych=0 czas=783.83 s
```

**Oba przeglądy zmierzyły poprawnie, tylko nie to samo.** B jechał limitem przejazdu
76 km/h, czyli **ponad** limitem planu 72 km/h; przy takim ustawieniu `TrainController`
obcina prędkość do 76, a `permitted` wynosi 72, więc równość istotnie nie zachodzi ani
raz — wiersz drugi odtwarza liczby B co do sztuki (94 059 wobec 94 060 i 89 483 wobec
89 484 to jeden krok różnicy, ten pierwszy, w którym `Drive` jeszcze nie istnieje).
A ustawił limit przejazdu **dokładnie na limicie planu** — i wtedy równość zachodzi
4492 razy, bo `TrainController.Advance` nie zbliża się do limitu asymptotycznie, tylko
przypisuje: `if (speed > speedLimitMps) speed = speedLimitMps;`, a `PermittedSpeedMps`
przy dostatecznie długim autorytecie zwraca `_plan.PermittedSpeedMps` wczesnym wyjściem.
Dwa `double` z przypisania są równe co do bitu.

### Kod z mutacją TP-08

```
LIMIT 72.00 km/h plan_dop=72.00 km/h | krokow=89671 v==dop=4492 v>dop=0    v<dop=85179 | ostrzezen=0    sluzbowych=4492 awaryjnych=0 czas=747.27 s
LIMIT 76.00 km/h plan_dop=72.00 km/h | krokow=94059 v==dop=0    v>dop=4576 v<dop=89483 | ostrzezen=4576 sluzbowych=4576 awaryjnych=0 czas=783.83 s
```

i pełny zestaw testów przy nałożonej mutacji:

```
Passed!  - Failed:     0, Passed:   376, Skipped:     0, Total:   376, Duration: 17 s - MetroBxl.Sim.Tests.dll (net10.0)
```

**Rozstrzygnięcie: racja jest po stronie A, a klasyfikacja B jako „granica nieosiągalna"
jest błędna** — choć pomiar, na którym B ją oparł, jest poprawny. Granica jest osiągalna
4492 razy w jednym przejeździe; ochrona hamuje skład, który **niczego nie łamie**, przez
37,4 s jazdy; przejazd wydłuża się o 5 kroków; i całe 376 testów tego nie widzi.
TP-08 wchodzi do tego raportu jako **klasa A**.

Drugie znalezisko z tej samej sondy, które nie jest mutacją, tylko własnością kodu:
**ingerencja i ostrzeżenie porównują tę samą parę liczb dwoma różnymi operatorami.**
Gałąź decyzyjna to `speedMps > permitted` (wiersz 335), a flaga `Overspeed` to
`speedMps > permitted && speedMps > StandstillSpeedMps` (wiersz 358). Po mutacji powstaje
stan, którego kontrakt klasy nie przewiduje — **4492 ingerencje przy zerze ostrzeżeń** —
mimo że opis klasy mówi „ostrzeżenie, potem hamulec służbowy". Nic nie wymusza, żeby te
dwa porównania pozostały tym samym porównaniem. Widać to na wydruku: wiersz z mutacją ma
`ostrzezen=0 sluzbowych=4492`.

### 2.1 Wniosek metodyczny, który przeżyje ten raport

Klasa C („granica, której bateria nie dotknęła") jest **twierdzeniem o scenariuszu, nie
o kodzie**. B miał rację, że nie wolno pisać „mutant równoważny" bez pomiaru — i A ma
rację, że pomiar w jednym scenariuszu nie jest pomiarem osiągalności. **Wszędzie, gdzie
w tym rdzeniu stoi przypisanie albo `Math.Clamp`, równość bitowa jest normalnym stanem,
a nie zdarzeniem miary zero.** Pozostałe pozycje klasy C z obu przeglądów czekają na taki
sam pomiar, jaki dostała TP-08, i dopóki go nie dostaną, są **nierozstrzygnięte**,
a nie nieszkodliwe.

---

## 3. Co potwierdziły oba przeglądy niezależnie

Cztery mutacje ocalały w obu przebiegach. To są znaleziska **pewne** — nie w sensie
„dwa razy tak samo policzone", tylko „dwie osobne konstrukcje mutacji, dwa osobne
przebiegi wyroczni, ten sam wynik".

### 3.1 NAJGROŹNIEJSZE — `steps - last` → `steps + last` (A: RD-04, B: RD03)

```csharp
// src/Sim/Signalling/RouteDispatcher.cs:103
if (_lastRequestStep.TryGetValue(trainId, out var last) && steps - last < _intervalSteps)
```

Dławik żądań tras jest jedyną rzeczą, która trzyma strumień zdarzeń przy życiu. Po
mutacji `last` rośnie razem z `steps`, więc suma przebija próg niemal natychmiast
i strażnik przestaje kogokolwiek wstrzymywać: **nastawnia pyta co krok, 120 razy na
sekundę.**

**Zmierzone przez B** (pakiet A, dwa składy, drugi 25 s za pierwszym, 60 000 kroków = 500 s):

```
== ORYGINAL
NASTAWNIA kroki=60000 odstep=120 zaryglowanych=14 odmow=158
          zdarzen_RouteRequested=172 RouteRejected=158 zdarzen_lacznie=513
          A=4502.44 B=3639.68
== RD03: steps - last  ->  steps + last
NASTAWNIA kroki=60000 odstep=120 zaryglowanych=14 odmow=18748
          zdarzen_RouteRequested=18762 RouteRejected=18748 zdarzen_lacznie=37693
          A=4502.44 B=3642.03
```

**158 odmów wobec 18 748 — 119 razy więcej. Strumień zdarzeń rośnie z 513 do 37 693
pozycji, czyli 73-krotnie.** Liczba zaryglowanych tras jest ta sama (14), a kilometraż
drugiego składu przesuwa się o 2,35 m — więc **ruch jako taki nie pada, pada zapis
ruchu**, i to jest cała szkoda. Jedyny trwały ślad pracy sygnalizacji przestaje być
czytelny.

**Dlaczego zestaw tego nie widzi — ustalone niezależnie przez oba przeglądy, tak samo.**
Jedyny test odstępu, `RouteDispatcherTests.AsksAtMostOncePerIntervalAndTheIntervalIsMeasuredInSteps`,
wykonuje pierwsze żądanie na kroku **zero**. Zapisuje `_lastRequestStep["A"] = 0`,
a dla `last == 0` wyrażenia `steps - last` i `steps + last` są **tym samym wyrażeniem**.
Test kończy się na drugim żądaniu (krok 120) i dalej nie idzie. Od trzeciego żądania
różnica jest zasadnicza: po żądaniu na kroku 120 oryginał liczy `121 - 120 = 1 < 120`
i **milczy**, a mutant liczy `121 + 120 = 241` i **pyta** — i pyta tak co krok do końca
przebiegu. Dławik przestaje istnieć dokładnie po drugim żądaniu.

To ten sam kształt usterki, co cztery znalezione w audycie z 02.09.2026: **bramka bez
wejścia na granicy nie bramkuje granicy.**

### 3.2 `speedMps > permitted` → `>=` (A: TP-08, B: TP08)

Rozstrzygnięta w sekcji 2. Ocalała w obu; klasa A.

### 3.3 Nawrót przybity tylko od dołu (A: LC-02, B: LC04)

```csharp
// src/Sim/Line/LineCore.cs:641
if (Steps - train.FinishedAtStep.Value < _turnbackSteps)
```

`<` → `<=` opóźnia wypuszczenie pojazdu o jeden krok, czyli 8,3 ms.
`Turnback_nie_wypuszcza_pojazdu_wczesniej_niz_po_zmierzonym_czasie` pilnuje wyłącznie
granicy **od dołu** — `Assert.IsTrue(przerwa >= line.TurnbackSteps)` — więc pojazd
wypuszczony o krok później jej nie łamie. Skala jest mała, ale kierunek jest jednostronny:
**nic nie broni przed nawrotem dłuższym, niż mówi argument.** Oba przeglądy doszły do
tego samego wniosku i do tej samej poprawki: dołożyć drugi warunek.

### 3.4 Próg wyzwolenia hamowania (A: LD-10, B: LD05)

`need.DecelerationMps2 < _trigger` → `<=` w `LineDrive.Command`. Ocalała w obu.
`_trigger` jest iloczynem `BrakeUsageFraction * ServiceBrakeMps2`, a `need` wynikiem
bisekcji — równość bitowa nie zaszła w żadnym mierzonym przebiegu. Po TP-08 **nie wolno
z tego wnioskować, że nie zajdzie**: patrz 2.1 i sekcja 6.

### 3.5 Domyślny odstęp żądań nie jest przybity niczym (A: RD-06, B: RD05)

```csharp
// src/Sim/Signalling/RouteDispatcher.cs:46
public const long DefaultRequestIntervalSteps = FixedStep.SimulationHertz;
```

To samo miejsce, dwie różne podmiany, **oba ocalałe**:

| przegląd | podmiana | odstęp po mutacji | skutek |
|---|---|---|---|
| A (RD-06) | `SimulationHertz` → `1L` | 1 krok | dyspozytor pyta 120 razy na sekundę |
| B (RD05) | `SimulationHertz` → `2 * SimulationHertz` | 240 kroków (2 s) | zmierzone: 79 odmów zamiast 158 |

Pomiar B dla wersji z odstępem 2 s:

```
== RD05: DefaultRequestIntervalSteps  ->  2 * SimulationHertz
NASTAWNIA kroki=60000 odstep=240 zaryglowanych=14 odmow=79
          zdarzen_RouteRequested=93 RouteRejected=79 zdarzen_lacznie=355
          A=4502.44 B=3625.96
```

Drugi skład kończy 500-sekundowy przebieg na **3625,96 m zamiast 3639,68 m — 13,72 m
różnicy**, wzięte wyłącznie z tego, że sygnał puszcza go o sekundę później.
`LineCore` buduje nastawnię bez argumentu (`new RouteDispatcher(plan)`), więc ta stała
rządzi **każdym** przejazdem linii. Ta jedna stała da się przesunąć w **obie** strony
o rząd wielkości i zestaw testów nie drgnie — a to jest mocniejsze stwierdzenie niż
którykolwiek z przeglądów mógł postawić sam.

---

## 4. Znalezisko, które powstało dopiero ze scalenia

Dwa miejsca dostały w obu przeglądach mutację **tej samej stałej o różnej sile**,
i w obu wypadkach wyszło to samo: **słabsza podmiana ocalała, mocniejsza zginęła.**
Żaden z raportów nie mógł tego napisać osobno — A widział tylko zgon, B tylko przeżycie.

| stała | A: podmiana i wynik | B: podmiana i wynik | co z tego wynika |
|---|---|---|---|
| `TrainProtection.StandstillSpeedMps` (`1e-6`) | → `1e-1` (5 rzędów) — **zabita** | → `1e-3` (3 rzędy) — **ocalała** | próg jest przybity dopiero powyżej 3 rzędów wielkości |
| `FixedBlockSystem.PositionEpsilonM` (`1e-9`) | → `1e-1` (8 rzędów) — **zabita** | → `1e-3` (6 rzędów) — **ocalała** | tolerancja położenia jest przybita dopiero powyżej 6 rzędów |

To nie jest ciekawostka, tylko **zmierzona czułość zestawu testów na te dwie stałe**.
Zestaw wyłapuje, że ktoś zamienił próg na absurd, i nie wyłapuje, że ktoś przesunął go
o tysiąc razy. Dla obu stałych tysiąc razy to jest dokładnie ta odległość, która zmienia
zachowanie modelu:

**`StandstillSpeedMps` 1e-6 → 1e-3.** Ta jedna stała rozstrzyga trzy rzeczy naraz: czy
ochrona w ogóle reaguje (`Supervise`, wiersz 323), czy przekroczenie liczy się jako
ostrzeżenie (wiersz 358) i **czy wolno zwolnić drzwi** (`DoorRelease`, wiersz 409).
Przy 1e-3 skład toczący się 0,9 mm/s jest „stojący" i **drzwi mu się otwierają**.
Zmierzone przez B na oryginale:

```
DRZWI v=0.0E+000 m/s -> zwolnione=True (P01); ochrona=None
DRZWI v=1.0E-007 m/s -> zwolnione=True (P01); ochrona=None
DRZWI v=1.0E-006 m/s -> zwolnione=True (P01); ochrona=None
DRZWI v=1.0E-005 m/s -> zwolnione=False (moving); ochrona=None
DRZWI v=1.0E-004 m/s -> zwolnione=False (moving); ochrona=None
DRZWI v=1.0E-003 m/s -> zwolnione=False (moving); ochrona=None
```

Przejście wypada między `1e-6` a `1e-5`, dokładnie tam, gdzie deklaruje. Po mutacji
wypadłoby trzy wiersze niżej, a `Drzwi_zwalniaja_sie_tylko_na_postoju_w_bloku_peronowym`
tego nie zauważa, bo podaje zero albo prędkość jazdy, nigdy nic pomiędzy.

**`PositionEpsilonM` 1e-9 → 1e-3.** Stała stoi w trzech miejscach: w strażniku cofania
składu (`MoveTrain`, wiersz 273), w wykrywaniu przejechania końca autorytetu (wiersz 284)
i w zwalnianiu trasy (wiersz 703). Rozszerzenie do 1 mm znaczy, że skład może **cofnąć
się o milimetr bez odmowy**, przejechanie autorytetu o milimetr przestaje być zgłaszane,
a trasa zwalnia się milimetr wcześniej. Dokumentacja tej stałej mówi wprost, czym ona
**nie jest**: „Nie jest zapasem bezpieczeństwa — jest granicą, poniżej której dwie liczby
double opisujące to samo miejsce nie mają prawa być uznane za różne". **1 mm nie jest
granicą reprezentacji `double`; to jest odległość.** Zmierzone przez B:

```
EPSILON FixedBlockSystem=1.0E-009 m, LineDrive=1.0E-009 m
COFNIECIE o 1.0E-010 m -> PRZESZLO (front=499.999999999900)
COFNIECIE o 1.0E-009 m -> PRZESZLO (front=499.999999999000)
COFNIECIE o 1.0E-006 m -> ODMOWA
COFNIECIE o 1.0E-004 m -> ODMOWA
COFNIECIE o 1.0E-003 m -> ODMOWA
```

Po mutacji ostatnie trzy wiersze zmieniają się w `PRZESZLO`.
`Sklad_nie_moze_cofnac_sie_na_planie` istnieje, ale cofa skład o odległość makroskopową,
więc mieści się w jednej i w drugiej tolerancji.

---

## 5. Ocalałe znalezione tylko przez jeden przegląd

Nie są słabsze od tych z sekcji 3 — są **niepotwierdzone drugim pomiarem**, i tylko tyle
o nich wiadomo. Kolejność: szkodliwość, nie plik.

### 5.1 Tylko A

#### TP-12 · konstruktor `TrainProtection` · `||` → `&&`

```csharp
if (!double.IsFinite(emergencyBrakeMps2) && emergencyBrakeMps2 < serviceBrakeMps2)
```

Po mutacji strażnik nie odrzuca **niczego**: wartość skończona daje `!IsFinite == false`
i całe `&&` gaśnie, więc hamulec awaryjny słabszy od służbowego przechodzi; `NaN` i `+∞`
przechodzą, bo `NaN < x` i `∞ < x` są fałszem. Zdanie z dokumentacji klasy „hamulec
awaryjny nie może być słabszy od służbowego" przestaje być prawdą i nic tego nie zauważa.

#### FB-07 (A) · `FixedBlockSystem.RegisterTrain` · `lengthM <= 0.0` → `< 0.0`

Skład o długości **zero** wjeżdża na plan. Ma tył w tym samym punkcie co czoło, więc
`Overlaps(rear, front)` zachowuje się inaczej niż dla każdego prawdziwego składu,
a `ComputeAuthority` cofa indeks bloku po zajętości, której nie ma. To nie jest sytuacja
ruchowa, tylko błąd scenariusza — a klasa deklaruje, że go odrzuca. Istniejące testy
podają wyłącznie `TrainLengthM = 94.0`.

#### FB-05 (A) · `ComputeAuthority` · `while (index > 0 …)` → `>= 0`

Przy braku pokrycia bloku 0 przez skład pętla sięga `Blocks[-1]`.

#### TP-11 (A) · `DoorRelease` · `>` → `>=` — granica na `speedMps == 1e-6`

Powiązana z sekcją 4: to jest **ta sama granica**, którą B przesuwał stałą. A mutował
operator, B mutował próg — i oba ocalały.

#### TP-05 (A) · bisekcja `PermittedSpeedMps`, `BrakingDistanceM(mid) > authorityDistanceM` → `>=`

Granica na dokładnej równości wewnątrz pętli bisekcji.

### 5.2 Tylko B

#### TP10 (B) · `BrakingDistanceM` · `speedMps <= 0.0` → `< 0.0` — martwy strażnik w publicznym API

```csharp
// src/Sim/Signalling/TrainProtection.cs:295-296
public double BrakingDistanceM(double speedMps) =>
    speedMps <= 0.0 ? 0.0 : _solver.Solve(speedMps, 0.0, _serviceBrakeMps2).DistanceM;
```

Solver **nie przyjmuje zera**:

```
SOLVER_V0 rzuca ArgumentOutOfRangeException: Prędkość początkowa musi być dodatnia
i skończona. (Parameter 'startSpeedMps') Actual value was 0.
```

Po mutacji `BrakingDistanceM(0.0)` nie zwraca 0,0 — **rzuca wyjątek**. To nie jest
przesunięcie granicy, to zamiana wartości na awarię. Przechodzi 376/376, bo w obecnym
grafie wywołań nikt nie woła tej metody z zerem: `PermittedSpeedMps` podaje jej sufit
planu (dodatni) i środki bisekcji (dodatnie). Strażnik jest **martwy**, a metoda jest
`public`, więc kontrakt „zero znaczy zero metrów" jest zadeklarowany i niesprawdzony.

#### LC07 (B) · `Math.Round` → `Math.Truncate` w przeliczaniu czasu nawrotu na kroki

```
NAWROT 0.004 s  -> raw=0.4800,     Round=0,     Truncate=0
NAWROT 0.005 s  -> raw=0.6000,     Round=1,     Truncate=0
NAWROT 0.0084 s -> raw=1.0080,     Round=1,     Truncate=1
NAWROT 90 s     -> raw=10800.0000, Round=10800, Truncate=10800
NAWROT 90.004 s -> raw=10800.4800, Round=10800, Truncate=10800
```

Rozjazd jest dokładnie w jednym miejscu: **0,005 s**. Oryginał zaokrągla w górę do
jednego kroku (po cichu wydłuża nawrót o 67 %), mutant ucina do zera i wtedy wchodzi
strażnik z wiersza 307, który **odmawia** — mutant jest więc **surowszy** od oryginału.
`Turnback_krotszy_niz_krok_jest_ODMOWA_a_nie_cichym_wylaczeniem` przechodzi w obu
wersjach, bo używa wartości poniżej 0,004 s. **Tryb zaokrąglenia jest niezapisaną decyzją
projektową** — `CLAUDE.md` §8, i to nie jest zaległość testowa, tylko brak w dokumentach.

#### FB02 i FB04 (B) · granice `± PositionEpsilonM` w `MoveTrain` i zwalnianiu trasy

`FrontM >= last.StartM - eps` → `>` oraz `frontChainageM < FrontM - eps` → `<=`.
Granice na dokładnej równości; nierozstrzygnięte (2.1).

#### TP05 (B) · `BrakingDistanceM(ceiling) <= dist` → `<` — wczesne wyjście z `PermittedSpeedMps`

Inne miejsce niż TP-05 u A, ta sama metoda, ten sam wynik. Dwa różne operatory
porównania w jednej metodzie, oba nieprzybite.

#### FB08 i RD06 (B) · komunikaty — klasa D, i dlaczego nie są zaległością

| id | mutacja | dlaczego to nie jest to samo, co warunek hamowania |
|---|---|---|
| RD06 | tekst wyjątku `"Odstęp między żądaniami trasy musi być dodatni."` | `RefusesANonPositiveInterval` sprawdza **typ** wyjątku i to jest właściwa rzecz do sprawdzania. Przybijanie treści komunikatu robi z tekstu dla człowieka element API i pęka przy każdej korekcie literówki. |
| FB08 | powód odmowy `"route-already-locked"` → `"route-already-blocked"` | Ciąg nie występuje **nigdzie** poza miejscem, w którym powstaje — sprawdzone `grep`em po `.cs` i `.py` w całym drzewie. Nic go nie parsuje. |

FB08 stoi wyżej niż RD06: to jest powód odmowy **w strumieniu zdarzeń**, czyli w jedynym
trwałym zapisie pracy sygnalizacji. Dziś nikt go nie czyta maszynowo. W dniu, w którym
zacznie czytać, przestanie być klasą D.

**Te dwie pozycje nie są zaległością i nie wchodzą do sekcji 8.** Są w tabeli, bo zostały
zmierzone.

---

## 6. Klasa C po TP-08 — pozycje nierozstrzygnięte

Oba przeglądy zgodziły się, że pisanie „mutant równoważny" bez pomiaru byłoby
zgadywaniem. Po rozstrzygnięciu z sekcji 2 trzeba powiedzieć mocniej: **klasa C to nie
jest „nieszkodliwe", to jest „niezmierzone", i TP-08 pokazała, ile to kosztuje.**

| id | miejsce | różni się wyłącznie przy | zmierzona osiągalność |
|---|---|---|---|
| A TP-05 | bisekcja `PermittedSpeedMps`, `>` → `>=` | `BrakingDistanceM(mid) == authorityDistanceM` | niezmierzona |
| B TP05 | wczesne wyjście, `<=` → `<` | `BrakingDistanceM(ceiling) == dist` (196,386 m przy 72 km/h) | 94 060 kroków, 0 równości, najbliższe podejście 6,17 mm |
| A TP-11 | `DoorRelease`, `>` → `>=` | `speedMps == 1e-6` | niezmierzona |
| A LD-10 / B LD05 | próg wyzwolenia hamowania, `<` → `<=` | `need.DecelerationMps2 == _trigger` = 1,1 | niezmierzona |
| A FB-05 | `while (index > 0 …)` → `>= 0` | blok 0 nie pokrywa się ze składem | niezmierzona |
| B FB02 | `FrontM >= last.StartM - eps` → `>` | czoło dokładnie na `StartM - 1e-9` | niezmierzona |
| B FB04 | `frontChainageM < FrontM - eps` → `<=` | nowy kilometraż dokładnie `FrontM - 1e-9` | niezmierzona |

Siedem pozycji czeka na taki sam pomiar, jaki dostała TP-08 — **z doborem scenariusza
pod granicę, a nie z domyślnego przejazdu.** TP-08 była niewidoczna w scenariuszu
76 km/h i widoczna 4492 razy w scenariuszu 72 km/h; różnica to jeden argument.

---

## 7. Narzędzie: dlaczego nie `tools/tests/mutation_sweep.py`

Oba przeglądy sprawdziły to niezależnie i doszły do tego samego, wskazując te same
wiersze. `tools/tests/mutation_sweep.py` **nie da się użyć do C#** i nie jest to kwestia
przełącznika — ma **trzy niezależne wiązania z Pythonem**:

| miejsce w narzędziu | co tam jest |
|---|---|
| `ast.parse` (wiersz 106), `ast.walk` (wiersz 114) | lista mutacji budowana z drzewa składni Pythona |
| `discover()`, wiersz 180 | `if name.endswith(".py")` — inne rozszerzenia nie wchodzą |
| wyrocznia, wiersz 251 | `subprocess.run([sys.executable, ".../test_all.py"])` |

Mutacje C# poszły więc osobnymi skryptami, w obu przeglądach według tej samej dyscypliny
co tamto narzędzie: jedna mutacja = jedna podmiana tekstu w jednym pliku, z
`assert count(old) == 1` **przed** podmianą, pełne `dotnet test tests/Sim.Tests` po,
przywrócenie przez `git checkout -- <plik>` **przed** następną, i kontrola
`git status --porcelain src/Sim` na koniec.

**Czego mutować się w C# nie da — zmierzone, nie założone.** `if (false)` nie kompiluje
się, a `src/Sim` ma `GenerateDocumentationFile` i `TreatWarningsAsErrors`, więc zepsuta
dokumentacja XML też wywala build. A sprawdził to kontrolą negatywną:

| kontrola | podmiana | wynik builda |
|---|---|---|
| NK-01 | `if (speedMps <= StandstillSpeedMps)` → `if (false)` | `error CS0162: Unreachable code detected` |
| NK-02 | `<see cref="BrakingPointSolver.BisectionSteps"/>` → nieistniejący składnik | `error CS1574: XML comment has cref attribute ... that could not be resolved` |

Obie kontrole są **poza** pulą i nie wchodzą do liczników — kompilator jest tu bramką,
a nie testem, więc zaliczanie ich jako pokrycia byłoby zawyżeniem.

**Kolumna „niekompilowalnych" wyszła zerem w obu przeglądach niezależnie** i to jest
wynik, a nie brak wyniku: mutowane były wyłącznie wartości i operatory, więc dobór ich
unikał. 45 z 45 i 42 z 42 przeszły przez kompilator.

---

## 8. Co z tego wynika jako zadania

Lista brakujących testów, każdy opisany na tyle konkretnie, żeby dało się z niego zrobić
pozycję kolejki w formacie z `CLAUDE.md` §6. **Do `docs/TASKS.md` nie są wpisane** — to
osobna zmiana, poza zakresem tego raportu (§10), i wchodzi tam bramka formatu z #227/#228.

> **Stan pozycji, przepisany 05.09.2026 na `9f4ae98` — a nie dopisany obok.** Poprzednia
> wersja tej sekcji przedstawiała wszystkie trzynaście pozycji jako **otwarte**, bo taka
> była prawda w chwili pomiaru (`3c242f7`). **To już nieprawda dla pięciu z nich**: #233
> (`519b814`) i #234 (`8c3512d`) scaliły się po tym pomiarze. Lista, która o tym milczy,
> wysyła następną sesję do pracy leżącej w `main` — usterka, którą #240 wycięło z
> `docs/TASKS.md`, i nie ma powodu, żeby przeżyła tutaj. Kolumna „stan" niżej jest
> sprawdzona **lekturą plików testowych na `9f4ae98`**, po jednej nazwie metody na
> pozycję, a nie odczytana z tytułów PR-ów:
>
> | poz. | stan | czym |
> |---:|---|---|
> | 1 | **zamknięta** #233 | `RouteDispatcherTests.MeasuresEachIntervalFromTheLastRequestAndNotFromStepZero` — pierwsze żądanie na kroku 1000, żądania na 1000/1120/1240/1360 |
> | 2 | **zamknięta** #234 | `TrainProtectionTests.Predkosc_dokladnie_rowna_dopuszczalnej_nie_jest_przekroczeniem` + `..._Na_pakiecie_A_jazda_dokladnie_po_limicie_planu_nie_budzi_ochrony` |
> | 3 | **zamknięta** #234 | `TrainProtectionTests.Ingerencja_sluzbowa_zawsze_jest_tez_ostrzezeniem` |
> | 9 | **zamknięta** #234 | `TrainProtectionTests.Droga_hamowania_z_postoju_jest_zerem_a_nie_wyjatkiem`, z kontrolą negatywną na solverze |
> | 10 | **zamknięta** #234 | `TrainProtectionTests.Konstruktor_odmawia_hamulcow_bez_sensu` — 0, ujemny, `NaN`, `+∞` po obu stronach pary hamulców |
> | 4, 5, 7, 8, 11, 12, 13 | **otwarte** | żaden test w drzewie nie spełnia kryterium „skończone, gdy" tych pozycji |
> | 6 | **otwarta, choć plik już jest** | `TrainProtectionTests.Drzwi_zwalniaja_sie_tylko_na_postoju_w_bloku_peronowym` istnieje, ale podaje prędkości **liczbami** (`0.0`, `3.0`), a kryterium pozycji 6 żąda odwołania **do stałej** `StandstillSpeedMps`. `grep -rn StandstillSpeedMps tests/` nie daje ani jednego trafienia, więc mutacja `1e-6` → `1e-3` nadal nie ma czego wywrócić |
>
> Pozycja 6 jest tu ważniejsza niż pięć zamkniętych: pokazuje, że **powstanie pliku
> nie jest zamknięciem pozycji**, a raport, który by je zrównał, przekłamałby stan
> w drugą stronę.

Kolejność: szkodliwość × pewność. Pozycje 1–4 są potwierdzone przez oba przeglądy.

| # | co przybić | gdzie | kryterium „skończone, gdy" |
|---:|---|---|---|
| **1** | Dławik żądań tras od **niezerowego** `last` | `tests/Sim.Tests/RouteDispatcherTests.cs` | Po żądaniu na kroku `N = 1000` przy odstępie 120 dyspozytor milczy przez kroki 1001–1119 (`Refused` bez zmian) i odzywa się dopiero na 1120. Mutacja `steps - last` → `steps + last` ten test **wywraca** (kontrola negatywna wykonana, nie zadeklarowana). |
| **2** | Granica `speedMps == permitted` w ochronie | nowy `tests/Sim.Tests/TrainProtectionTests.cs` | Przejazd pakietu A z `LineRunSettings.SpeedLimitMps` **dokładnie** równym `plan.PermittedSpeedMps` daje `ServiceInterventions == 0` i `ProtectionWarnings == 0` przy 4492 krokach z prędkością równą limitowi. Mutacja `>` → `>=` daje 4492 ingerencje i test pada. |
| **3** | Ingerencja implikuje ostrzeżenie | ten sam plik co #2 | `ServiceInterventions > 0` implikuje `ProtectionWarnings > 0` na każdym przejeździe z ATP. Dziś nic nie wymusza, żeby wiersze 335 i 358 porównywały tę samą parę liczb tym samym operatorem. |
| **4** | Nawrót przybity **z obu stron** | `tests/Sim.Tests/LineCoreTests.cs` | Pojazd wyjeżdża dokładnie na kroku `FinishedAtStep + TurnbackSteps` — ani krok wcześniej, ani krok później. Dziś asercja jest jednostronna (`>=`). |
| **5** | `DefaultRequestIntervalSteps` przybity zachowaniem | `tests/Sim.Tests/RouteDispatcherTests.cs` | Dyspozytor zbudowany **bez** podania odstępu pyta w 240 krokach dokładnie dwa razy. Mutacja stałej w **obie** strony (`1L` i `2 * SimulationHertz`) wywraca test. Asercja `AreEqual(FixedStep.SimulationHertz, …)` to minimum, nie cel. |
| **6** | Próg postoju przybity **na progu**, nie rzędami wielkości | `TrainProtectionTests.cs` | Drzwi zwolnione przy `StandstillSpeedMps`, zablokowane z powodem `moving` przy `10 * StandstillSpeedMps`. Test odwołuje się **do stałej**, nie do liczby z niej przepisanej. Mutacja `1e-6` → `1e-3` pada. |
| **7** | `PositionEpsilonM` przybity **na progu** | `tests/Sim.Tests/FixedBlockTests.cs` | Cofnięcie o `10 * PositionEpsilonM` jest odmową, o `0.1 * PositionEpsilonM` przechodzi. Mutacja `1e-9` → `1e-3` pada. |
| **8** | Jedna tolerancja położenia, nie dwie | `tests/Sim.Tests/FixedBlockTests.cs` | `Assert.AreEqual(FixedBlockSystem.PositionEpsilonM, LineDrive.PositionEpsilonM, 0.0)` z uzasadnieniem. Jednowierszowa bramka na to, co dziś jest tylko komentarzem. |
| **9** | Kontrakt „zero znaczy zero metrów" | `TrainProtectionTests.cs` | `BrakingDistanceM(0.0)` zwraca dokładnie `0.0` i **nie rzuca**. Mutacja `<= 0.0` → `< 0.0` zamienia wartość w `ArgumentOutOfRangeException` i test pada. |
| **10** | Strażniki konstruktora `TrainProtection` | `TrainProtectionTests.cs` | Konstruktor czteroargumentowy rzuca `ArgumentOutOfRangeException` dla `emergencyBrakeMps2 = 1.0` przy `serviceBrakeMps2 = 1.2`, dla `double.NaN` i dla `double.PositiveInfinity`. Mutacja `||` → `&&` pada na każdym z trzech. |
| **11** | Strażnik długości składu | `tests/Sim.Tests/FixedBlockTests.cs` | `RegisterTrain("A", 0.0, 0.0)` rzuca `ArgumentOutOfRangeException`. Dziś każdy test podaje 94,0 m. |
| **12** | Pomiar osiągalności siedmiu granic z sekcji 6 | `reports/` (raport, nie test) | Dla każdej z siedmiu pozycji: scenariusz **dobrany pod granicę** i zmierzona liczba kroków, w których równość zachodzi. Wynik rozstrzyga, które z nich są mutantami równoważnymi, a które drugą TP-08. Zadanie jest pomiarem, nie poprawką. |
| **13** | `BrakeUsageFraction` na ścieżce z ATP | `tests/Sim.Tests/LineCoreTests.cs` | Przejazd `LineCore` z `brakeUsageFraction` innym niż 1,0 (np. 0,6) daje mierzalnie inny czas i inne `MaxBrakeDemandMps2`. Dziś **każdy** test dotykający `LineCore` podaje 1,0 — patrz 9.1. |

**Decyzja właściciela, nie zadanie** (`CLAUDE.md` §8): tryb zaokrąglenia czasu nawrotu
niebędącego wielokrotnością kroku (LC07, 5.2). Kod dziś zaokrągla w górę i po cichu
wydłuża nawrót o 67 % przy 0,005 s; docstring broni tylko przed zaokrągleniem w dół do
zera. **Która z tych dwóch rzeczy jest zamierzona, nie stoi w żadnym dokumencie** — i póki
nie stanie, test na to byłby przybiciem przypadku, a nie kontraktu.

---

## 9. Zauważone przy okazji, nie tknięte

### 9.1 `BrakeUsageFraction` — obserwacja B, poprawiona wykonaniem

B zapisał: „**we wszystkich testach `BrakeUsageFraction` wynosi 1,0**". Sprawdzone
`grep`em przy scalaniu — **to twierdzenie jest o krok za mocne**, i poprawka czyni je
ciekawszym, a nie słabszym:

```
tests/Sim.Tests/LineRunTests.cs:166:        var late  = Run.Run(axis, Level(), Settings(usage: 1.0));
tests/Sim.Tests/LineRunTests.cs:167:        var early = Run.Run(axis, Level(), Settings(usage: 0.6));
tests/Sim.Tests/LineRunTests.cs:270:        Assert.ThrowsException<ArgumentOutOfRangeException>(() => Settings(usage: 1.5));
```

Parametr **jest** ruszony — ale tylko w `LineRunTests`, na osi syntetycznej, przez jeden
test o jednostronnej asercji (`Wczesniejsze_hamowanie_wydluza_czas_jazdy`: `early >
late`), plus jedno odrzucenie wartości spoza dziedziny. **Każde miejsce, które buduje
`LineRunSettings` dla `LineCore` — czyli dla ścieżki z ochroną pociągu — podaje 1,0:**
`LineCoreTests.Settings()` (wiersz 37), `RealSettings()` (318) i `RealLineWithAtp` (503).
`LineDriveTests.Settings()` ma 1,0 w domyślnym argumencie i **żaden** test go nie nadpisuje.

Poprawione zdanie jest więc węższe i celniejsze: **`_trigger = BrakeUsageFraction *
ServiceBrakeMps2`, od którego zależy ocalała LD-10/LD05, jest na całej ścieżce z ATP
mierzony w jednym punkcie swojej dziedziny.** Stąd pozycja 13 w sekcji 8.

### 9.2 `PositionEpsilonM` istnieje w dwóch egzemplarzach

```
src/Sim/Signalling/FixedBlockSystem.cs:40:    public const double PositionEpsilonM = 1e-9;
src/Sim/Train/LineDrive.cs:35:              public const double PositionEpsilonM = 1e-9;
```

Komentarz przy drugiej mówi „ta sama co w `FixedBlockSystem`". **Nic tej równości nie
pilnuje** — jest ona dziś prawdą przez zbieg okoliczności i czyjąś uważność, nie przez
bramkę. Zmierzone sondą B: `EPSILON FixedBlockSystem=1.0E-009 m, LineDrive=1.0E-009 m`.
Pozycja 8 w sekcji 8 to jeden wiersz asercji.

### 9.3 Połowa pokrycia wisi na jednym scenariuszu

B policzył z pełnych dzienników przebiegów (nie z tabel, gdzie listy nazw są ucięte do
trzech przykładów): **`Nad_limitem_planu_ochrona_hamuje_i_da_sie_to_zmierzyc` pada przy
14 z 28 zabitych mutacji** — przy połowie, i przy mutacjach we **wszystkich pięciu
plikach**. Drugi w kolejności, `Na_prawdziwym_planie_wymagajacym_tras_linia_przejezdza_cala_os`,
pada przy 7.

To jest dobra wiadomość o tym teście i ostrzeżenie zarazem: **duża część pokrycia rdzenia
wisi na jednym scenariuszu z pakietu A**, więc jego przypadkowe osłabienie zabrałoby
pokrycie w miejscach, które z nim nie sąsiadują. Obserwacja A idzie w tę samą stronę
z drugiej strony: `LineDrive` i `LineCore` są przybite najmocniej (9/10 i 8/9 u A, 89 %
i 78 % u B), bo mają testy pisane jako **kontrole negatywne konkretnych usterek** —
komentarze przy `Postoj_przed_autorytetem_jest_naprawde_postojem_a_nie_pelzaniem` czy
`Szczyt_predkosci_jest_liczony_od_nowa_na_kazdym_odcinku` wprost opisują mutację, którą
ten test ma zabijać. Widać to w wyniku obu przeglądów.

### 9.4 `TrainProtection` wypada najgorzej w obu przeglądach i nie ma własnego pliku testów

| plik | A: zabitych/mutacji | B: zabitych/mutacji |
|---|---|---|
| `src/Sim/Signalling/TrainProtection.cs` | **8/12 (67 %)** | **6/10 (60 %)** |
| `src/Sim/Signalling/RouteDispatcher.cs` | 4/6 (67 %) | 3/6 (50 %) |
| `src/Sim/Signalling/FixedBlockSystem.cs` | 6/8 (75 %) | 4/8 (50 %) |
| `src/Sim/Line/LineCore.cs` | 8/9 (89 %) | 7/9 (78 %) |
| `src/Sim/Train/LineDrive.cs` | 9/10 (90 %) | 8/9 (89 %) |

Dwa niezależne przeglądy, dwa różne zbiory mutacji, ten sam ranking na obu krańcach:
`TrainProtection` i `RouteDispatcher` na dole, `LineDrive` i `LineCore` na górze.
Przyczyną **była** jedna rzecz, którą widać było jednym poleceniem:

```
$ ls tests/Sim.Tests/TrainProtectionTests.cs          # 05.09.2026, przed #234
ls: cannot access 'tests/Sim.Tests/TrainProtectionTests.cs': No such file or directory
```

> **Ten akapit jest przepisany, a nie dopisany obok.** Jego poprzednia wersja mówiła
> w czasie teraźniejszym: „Klasa o najgorszym wyniku w obu przeglądach **jest** jedyną
> z piątki bez własnego pliku testów" i „pięć z trzynastu pozycji sekcji 8 trafia
> do pliku, **który nie istnieje**". **To już nieprawda.** Plik powstał tego samego
> dnia w #234 (`8c3512d`) i ma 672 wiersze oraz 25 metod testowych; polecenie wyżej
> daje dziś ścieżkę, a nie błąd. Zdanie zostawione w czasie teraźniejszym opisywałoby
> lukę, której nie ma, i tym samym proponowało pracę leżącą już w `main` — dokładnie
> ten defekt, który #240 wyciął z `docs/TASKS.md`.

**Jak było.** Ochrona była testowana wyłącznie od strony scenariusza
(`ClassicSignallingScenarioTests`, `LineCoreTests`), więc jej granice i strażniki
argumentów nie miały gdzie być sprawdzone punktowo. **Pięć z trzynastu pozycji sekcji 8
(#2, #3, #6, #9, #10) trafiało do pliku, którego nie było** — i było to jedno zadanie
założycielskie, nie pięć osobnych. Tak też zostało zrobione: jednym PR-em.

`RouteDispatcher` na drugim miejscu od dołu ma inną przyczynę, też ustaloną przez oba
przeglądy niezależnie: nie ma mało testów, tylko **wszystkie jego testy stoją w jednym
punkcie stanu** — kroku zero. Stąd 3.1.

### 9.5 Testy `RouteDispatcherTests` są jedyną grupą z nazwami po angielsku

Reszta rdzenia nazywa testy po polsku. **Nie zmieniane** — to konwencja, nie usterka,
i zmiana nazw nie należy do żadnego zadania z sekcji 8.

---

## 10. Rzeczywiste wyjście weryfikacji

Punkt wyjścia obu przeglądów i stan po przywróceniu drzewa — ten sam. Poniżej wyjście
z **tej gałęzi**, na `3c242f7`:

```
$ dotnet test tests/Sim.Tests
Passed!  - Failed:     0, Passed:   376, Skipped:     0, Total:   376, Duration: 19 s - MetroBxl.Sim.Tests.dll (net10.0)

$ python3 tools/tests/test_all.py
  1493/1493 przeszło

$ git status --porcelain
(pusto)
```

### Przykład mutacji zabitej — `Math.Max` → `Math.Min` w `ProtectionDecision.Apply`

Ta sama mutacja w obu przeglądach (A: TP-02, B: TP01), zabita w obu — **ale przez różne
asercje**, i to jest właśnie sens dwóch pomiarów. A zobaczył ją licznikiem:

```
Assert.AreEqual failed. Expected:<4576>. Actual:<8182>. zmierzone: 4576 krokow z hamulcem sluzbowym ochrony
  at MetroBxl.Sim.Tests.LineCoreTests.Nad_limitem_planu_ochrona_hamuje_i_da_sie_to_zmierzyc()
Failed!  - Failed:     3, Passed:   373, Skipped:     0, Total:   376, Duration: 17 s
```

B zobaczył ją kontraktem:

```
  Failed Ochrona_nie_odpuszcza_hamulca_ktory_maszynista_juz_podal [< 1 ms]
  Error Message:
   Assert.AreEqual failed. Expected a difference no greater than <0> between expected
   value <1> and actual value <0.5>. pełny hamulec maszynisty ma zostać pełnym,
   a nie spaść do połowy
  Stack Trace:
     at MetroBxl.Sim.Tests.ClassicSignallingScenarioTests
        .Ochrona_nie_odpuszcza_hamulca_ktory_maszynista_juz_podal()
        in tests/Sim.Tests/ClassicSignallingScenarioTests.cs:line 435
```

Jedna zmiana operatora, dwa niezależne testy, dwa różne komunikaty, ten sam werdykt.
**Ta mutacja jest zabita nie „bo test przeszedł", tylko bo dwie różne asercje na niej
padły.**

### Przykład mutacji ocalałej — `steps - last` → `steps + last`

```
Sim -> .../src/Sim/bin/Debug/net10.0/MetroBxl.Sim.dll
Sim.Tests -> .../tests/Sim.Tests/bin/Debug/net10.0/MetroBxl.Sim.Tests.dll
A total of 1 test files matched the specified pattern.
Passed!  - Failed:     0, Passed:   376, Skipped:     0, Total:   376, Duration: 18 s
```

Zielono, a nastawnia pyta 119 razy częściej, niż wolno.

---

## 11. Uwaga o commitach, na których mierzono

Trzy różne commity `main` i to jest w porządku — sprawdzone, nie założone:

- **A** mierzył na `d495051`, `main` przesunął się na `0e1b161` (#225). #225 rusza
  wyłącznie narzędzia w Pythonie; `dotnet test tests/Sim.Tests` na `0e1b161` daje te same
  376/376.
- **B** mierzył na `b41c158`, i tu `main` ruszył jeden z pięciu mierzonych plików —
  `src/Sim/Line/LineCore.cs`, o 40 wierszy. Sprawdzone: **wyłącznie dokumentacja XML**
  (`<param>`, `<returns>` i jedno zdanie w `<summary>` przy `Finished`); ani jeden wiersz
  wykonywalny się nie ruszył. Wszystkie 42 wzorce mutacji odnajdują się na `0e1b161`
  dokładnie raz każdy.
- **Scalenie** stoi na `3c242f7` (#227, bramka formatu pozycji kolejki), a rozstrzygnięcie
  TP-08 z sekcji 2 zostało **wykonane na tym commicie**, nie przeniesione.

Gdyby którakolwiek z tych zmian ruszyła wiersz wykonywalny w `src/Sim/`, ten raport
wymagałby powtórzenia przebiegu, a nie dopisku. Nie ruszyła.

---

## 12. Czego ten raport świadomie nie robi

- **Nie przelicza mutacji od nowa.** 87 przebiegów obu przeglądów jest wzięte tak, jak
  zostało zmierzone. Jedynym nowym wykonaniem jest rozstrzygnięcie TP-08 (sekcja 2)
  i sprawdzenie twierdzenia o `BrakeUsageFraction` (9.1) — oba dlatego, że raporty
  mówiły rzeczy, których nie da się pogodzić przez zestawienie ich obok siebie.
- **Nie naprawia kodu i nie dopisuje testów.** Trzynaście pozycji sekcji 8 to zadania,
  nie zmiany. Dopisanie testu w tym samym commicie odebrałoby raportowi kontrolę
  negatywną: test dopisany dziś przestaje mierzyć stan `main` z chwili pomiaru.
- **Nie wpisuje pozycji sekcji 8 do `docs/TASKS.md`** — to osobna zmiana i osobna gałąź
  (§10); wchodzi tam bramka formatu z #227/#228, więc pozycje muszą mieć wszystkie sześć
  pól, a sekcja 8 podaje z nich cztery.
- **Nie uśrednia 10 i 14** i nie wybiera „ładniejszej" liczby. Obie są w tabeli na górze
  i obie są prawdziwe dla swojej próbki.
- **Nie sprowadza rozbieżności TP-08 do „obaj mieli trochę racji".** Pomiar B jest
  poprawny, klasyfikacja B jest błędna, i tak to jest tu zapisane.
- **Nie dodaje sondy do repozytorium.** Pomiary pochodzą z projektów leżących poza
  drzewem, odwołujących się do `src/Sim/Sim.csproj`. Sonda nie jest bramką i nie powinna
  udawać, że nią jest; gdyby miała zostać, to jako testy z sekcji 8.
- **Nie obejmuje `Replay`, `StateDigest`, `ToString` ani ścieżek serializacji planu.**
  Żaden z przeglądów ich nie mutował. Pokrycie 77,8 % i 66,7 % dotyczy **tych próbek**,
  a nie tych plików.
- **Nie mutowano testów** w żadnym z przeglądów. Wyrocznią jest zestaw testów, kodem pod
  testem — `src/Sim/`.

---

## 13. Jak to powtórzyć

```bash
export PATH=/root/.dotnet:$PATH DOTNET_ROOT=/root/.dotnet
dotnet test tests/Sim.Tests            # 376/376 — punkt odniesienia
```

Dla dowolnej pozycji z sekcji 3–6: podmienić w podanym pliku tekst „przed" na „po"
(z kontrolą `count == 1`), uruchomić `dotnet test tests/Sim.Tests`, przywrócić plik przez
`git checkout -- <plik>`. Przebieg jednej mutacji to ~20 s.

Dla rozstrzygnięcia TP-08 z sekcji 2 potrzebna jest sonda poza drzewem: projekt konsolowy
z `<ProjectReference Include=".../src/Sim/Sim.csproj" />`, budujący `LineCore.M7` na
pakiecie A z `LineRunSettings(Units.KmhToMps(72.0), 8.0, 1.0, 5.0)` i liczący kroki,
w których `Drive.State.SpeedMps == Protection.PermittedSpeedMps(Signalling.Authority(id).DistanceM)`.
**Limit 72,00 km/h, nie 76,00** — na 76 granica nie zachodzi ani razu i to jest dokładnie
ta pomyłka, która postawiła TP-08 w klasie C.
