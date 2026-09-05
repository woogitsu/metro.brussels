# Przegląd mutacyjny rdzenia sygnalizacji i linii

**Data pomiaru:** 2026-09-05
**Mierzony commit:** `b41c158` (Scalenie #222)
**Sprawdzone ponownie na:** `0e1b161` (Scalenie #225) — patrz niżej
**Zestaw testów na wejściu:** 376/376 zielonych, `dotnet test tests/Sim.Tests`

> **`main` przesunął się w trakcie pomiaru** z `b41c158` na `0e1b161` i ruszył jeden
> z pięciu mierzonych plików — `src/Sim/Line/LineCore.cs`, o 40 wierszy. Sprawdzone:
> ta zmiana to **wyłącznie dokumentacja XML** (`<param>`, `<returns>` i jedno zdanie
> w `<summary>` przy `Finished`); ani jeden wiersz wykonywalny się nie ruszył.
> Wszystkie 42 wzorce mutacji odnajdują się na `0e1b161` dokładnie raz każdy, a zestaw
> testów daje na nim te same 376/376. Wyniki poniżej przenoszą się więc bez zmian —
> ale mierzone są na `b41c158` i tak są tu podane.

Pięć plików, które weszły albo mocno urosły w ostatnich godzinach: ochrona pociągu,
która naprawdę hamuje, nastawnia automatyczna, turnback i `ReleaseTrain`.

Zielony zestaw testów nie mówi, że kod jest sprawdzony — mówi, że nie jest sprzeczny
sam ze sobą. Ten raport mierzy, **ile z niego jest naprawdę przybite**.

Kodu produkcyjnego nie tknięto. Jedyną zmianą w repozytorium jest ten plik.

---

## 0. Wynik, w jednym zdaniu

Z 42 mutacji **28 zabito, 14 ocalało, żadna nie okazała się niekompilowalna** — czyli
zestaw wyłapuje **dwie trzecie** wstrzykniętych zmian zachowania, a z czternastu
ocalałych **pięć to realne dziury o mierzalnym skutku**, jedna z nich duża.

| plik | zastosowanych | zabitych | ocalałych | niekompilowalnych | zabitych |
|---|---:|---:|---:|---:|---:|
| `src/Sim/Signalling/TrainProtection.cs` | 10 | 6 | 4 | 0 | 60 % |
| `src/Sim/Signalling/RouteDispatcher.cs` | 6 | 3 | 3 | 0 | 50 % |
| `src/Sim/Signalling/FixedBlockSystem.cs` | 8 | 4 | 4 | 0 | 50 % |
| `src/Sim/Line/LineCore.cs` | 9 | 7 | 2 | 0 | 78 % |
| `src/Sim/Train/LineDrive.cs` | 9 | 8 | 1 | 0 | 89 % |
| **razem** | **42** | **28** | **14** | **0** | **67 %** |

Najsłabiej przybita jest **nastawnia** (`RouteDispatcher`) — i to nie dlatego, że ma
mało testów, tylko dlatego, że wszystkie jej testy stoją w jednym punkcie stanu.
Sekcja 3.2 pokazuje, jak to wygląda od środka.

---

## 1. Jak to było robione

`tools/tests/mutation_sweep.py` **nie nadaje się do C#** i nie został użyty. Nie jest to
kwestia konfiguracji: narzędzie buduje listę mutacji z `ast.walk` na drzewie Pythona
(wiersz 114), szuka plików przez `os.walk` po katalogu `tools` z filtrem `name.endswith(".py")`
(wiersze 176–180) i uruchamia `tools/tests/test_all.py` (wiersz 251). Ani jeden z tych
trzech kroków nie ma odpowiednika dla `src/Sim`.

Mutacje zastosowano więc skryptem o tym samym kontrakcie, co tamto narzędzie:

- jedna mutacja = **jedna podmiana tekstu**, poprzedzona `assert source.count(old) == 1`
  — wzorzec niejednoznaczny jest błędem przebiegu, nie cichym trafieniem w inne miejsce;
- po każdej mutacji pełne `dotnet test tests/Sim.Tests`;
- przywrócenie przez `git checkout -- <plik>` **przed** następną mutacją;
- na końcu przebiegu kontrola `git status --porcelain src/Sim`, która wyszła pusta.

**Czego nie mutowano i dlaczego.** `if (false)` w C# nie kompiluje się (CS0162 przy
`TreatWarningsAsErrors`, a bez tego i tak jest to mutacja nieodróżnialna od usunięcia
gałęzi). Mutowane są **wartości i operatory**: `>` → `>=`, `&&` → `||`, `Math.Max` →
`Math.Min`, `Math.Round` → `Math.Truncate`, `+` → `-`, stała → inna stała, tekst
komunikatu → inny tekst.

**Mutacji niekompilowalnych nie było ani jednej** — 42 z 42 przeszły przez kompilator.
Kolumna zostaje w tabeli, bo jej zerowa wartość jest wynikiem, a nie brakiem wyniku.

### 1.1 Skąd wzięły się liczby w triażu

Zdanie „ta mutacja niczego nie zmienia" bez pomiaru jest zgadywaniem, więc każda
z czternastu ocalałych została dodatkowo **wykonana**, a nie tylko przeczytana. Służyła
do tego sonda leżąca **poza drzewem repozytorium**, odwołująca się do `src/Sim/Sim.csproj`
projektem — dzięki temu ani jeden plik nie doszedł do gałęzi, a `dotnet run` przebudowywał
rdzeń z tym, co akurat stało w mutowanym pliku. Scenariuszem był prawdziwy pakiet A
(`data/design/signalling/classic-2026.json` + `data/track/L1_A.json`), te same warunki co
w `LineCoreTests.RealLineWithAtp`: M7 AW2, tunel, sucha szyna, limit 76 km/h.

Odczyt jest ten sam, co w `reports/mutation-triage-fizyka.md`: mutacja, której **punktu
przerzutu bateria nie dotknęła ani razu**, nie jest udowodnioną równoważnością — jest
mutacją, o której wynik nic nie mówi. Te są w sekcji 4, osobno od realnych dziur.

---

## 2. Ocalałe — pełna lista

Klasa: **A** = groźna (warunek albo stała rozstrzygająca o hamowaniu, blokadzie drzwi
albo o zapisie ruchu), **B** = realna dziura o małej skali, **C** = granica nieosiągalna
przez obecną baterię, **D** = nieszkodliwa (komunikat).

| id | plik | mutacja | klasa |
|---|---|---|---|
| RD03 | `RouteDispatcher.cs` | `steps - last` → `steps + last` | **A** |
| TP04 | `TrainProtection.cs` | `StandstillSpeedMps = 1e-6` → `1e-3` | **A** |
| FB07 | `FixedBlockSystem.cs` | `PositionEpsilonM = 1e-9` → `1e-3` | **A** |
| TP10 | `TrainProtection.cs` | `speedMps <= 0.0` → `speedMps < 0.0` | **A** |
| RD05 | `RouteDispatcher.cs` | domyślny odstęp `SimulationHertz` → `2 * SimulationHertz` | **B** |
| LC04 | `LineCore.cs` | `Steps - FinishedAtStep < _turnbackSteps` → `<=` | **B** |
| LC07 | `LineCore.cs` | `Math.Round` → `Math.Truncate` | **B** |
| TP05 | `TrainProtection.cs` | `BrakingDistanceM(ceiling) <= dist` → `<` | C |
| TP08 | `TrainProtection.cs` | `speedMps > permitted` → `>=` | C |
| FB02 | `FixedBlockSystem.cs` | `FrontM >= last.StartM - eps` → `>` | C |
| FB04 | `FixedBlockSystem.cs` | `frontChainageM < FrontM - eps` → `<=` | C |
| LD05 | `LineDrive.cs` | `need.DecelerationMps2 < _trigger` → `<=` | C |
| FB08 | `FixedBlockSystem.cs` | `"route-already-locked"` → `"route-already-blocked"` | D |
| RD06 | `RouteDispatcher.cs` | tekst komunikatu wyjątku | D |

**Mutacja w komunikacie błędu nie jest tą samą klasą, co mutacja w warunku
rozstrzygającym o hamowaniu, i nie jest tu tak liczona.** RD06 i FB08 zostają w tabeli
jako zmierzone, ale **nie są zaległością** — sekcja 5 mówi, dlaczego.

---

## 3. Realne dziury — klasa A i B

### 3.1 RD03 — odstęp między żądaniami trasy nie działa po pierwszym żądaniu

```csharp
// src/Sim/Signalling/RouteDispatcher.cs:103
if (_lastRequestStep.TryGetValue(trainId, out var last) && steps - last < _intervalSteps)
```

Mutacja: `steps - last` → `steps + last`.

**Dlaczego to jest zmiana zachowania.** `last` rośnie razem z `steps`, więc `steps + last`
przekracza próg odstępu prawie natychmiast i strażnik przestaje kogokolwiek wstrzymywać:
nastawnia pyta **co krok**, czyli 120 razy na sekundę. Opis klasy wymienia to jako rzecz,
która nie ma prawa się zdarzyć — „pytanie 120 razy na sekundę zalałoby ten strumień
niczym" — a strumień zdarzeń jest jedynym zapisem tego, co robiła sygnalizacja.

**Zmierzone** (pakiet A, dwa składy, drugi 25 s za pierwszym, 60 000 kroków = 500 s):

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

**158 odmów wobec 18 748 — 119 razy więcej.** Strumień zdarzeń rośnie z 513 do 37 693
pozycji, czyli **73-krotnie**, a kilometraż drugiego składu przesuwa się o 2,35 m.
Liczba zaryglowanych tras jest ta sama (14), więc ruch jako taki nie pada — pada
**zapis** ruchu i to jest cała szkoda.

**Dlaczego zestaw tego nie widzi.** Jedyny test odstępu,
`RouteDispatcherTests.AsksAtMostOncePerIntervalAndTheIntervalIsMeasuredInSteps`, wykonuje
pierwsze żądanie na kroku 0. Zapisuje więc `_lastRequestStep["A"] = 0` i wszystkie
kolejne asercje liczą `steps - 0` przeciwko `steps + 0`. **Dla `last == 0` obie wersje
wyrażenia są tym samym wyrażeniem.** Test jest poprawny i sprawdza, co deklaruje — po
prostu nigdy nie wychodzi z punktu, w którym mutacja jest niewidoczna. To dokładnie ten
sam kształt usterki, co cztery znalezione w audycie z 02.09.2026: bramka bez wejścia na
granicy nie bramkuje granicy.

**Brakujący test.** Drugi odstęp, liczony od niezerowego `last`: zaryglować albo odrzucić
żądanie na kroku `N > 0`, po czym sprawdzić, że przez kolejne `interval - 1` kroków
nastawnia milczy, a pyta dopiero na `N + interval`. Przy `N = 1000` i odstępie 120
oryginał milczy do kroku 1119, a mutant pyta już na 1001.

### 3.2 TP04 — próg „skład stoi" nie jest przybity, a rozstrzyga o drzwiach

```csharp
// src/Sim/Signalling/TrainProtection.cs:183
public const double StandstillSpeedMps = 1e-6;
```

Mutacja: `1e-6` → `1e-3`, czyli próg w górę o **trzy rzędy wielkości**.

**Dlaczego to jest zmiana zachowania.** Ta jedna stała rozstrzyga trzy rzeczy naraz:
czy ochrona w ogóle reaguje (`Supervise`, wiersz 323), czy przekroczenie liczy się jako
ostrzeżenie (wiersz 358) i **czy wolno zwolnić drzwi** (`DoorRelease`, wiersz 409).
Podniesienie progu do 1e-3 znaczy, że skład toczący się 0,9 mm/s jest „stojący" i drzwi
mu się otwierają.

**Zmierzone** — próg na oryginale leży dokładnie tam, gdzie deklaruje:

```
DRZWI v=0.0E+000 m/s -> zwolnione=True (P01); ochrona=None
DRZWI v=1.0E-007 m/s -> zwolnione=True (P01); ochrona=None
DRZWI v=1.0E-006 m/s -> zwolnione=True (P01); ochrona=None
DRZWI v=1.0E-005 m/s -> zwolnione=False (moving); ochrona=None
DRZWI v=1.0E-004 m/s -> zwolnione=False (moving); ochrona=None
DRZWI v=1.0E-003 m/s -> zwolnione=False (moving); ochrona=None
```

Przejście wypada między `1e-6` a `1e-5`. Po mutacji wypadłoby między `1e-3` a `1e-2`,
czyli trzy wiersze niżej — i **żaden test tego nie zauważa**, bo
`Drzwi_zwalniaja_sie_tylko_na_postoju_w_bloku_peronowym` podaje zero albo prędkość
jazdy, nigdy nic pomiędzy.

**Brakujący test.** Blokada drzwi na obu krańcach progu: przy `StandstillSpeedMps`
drzwi zwolnione, przy `10 * StandstillSpeedMps` zablokowane z powodem `moving`. Test ma
odwoływać się do stałej, a nie do liczby przepisanej z niej ręcznie — inaczej przybija
literał w dwóch miejscach zamiast progu w jednym.

### 3.3 FB07 — tolerancja położenia jest zadeklarowana jako szum, a nikt nie pilnuje, żeby nią została

```csharp
// src/Sim/Signalling/FixedBlockSystem.cs:40
public const double PositionEpsilonM = 1e-9;
```

Mutacja: `1e-9` → `1e-3`.

**Dlaczego to jest zmiana zachowania.** Ta stała stoi w trzech miejscach: w strażniku
cofania składu (`MoveTrain`, wiersz 273), w wykrywaniu przejechania końca autorytetu
(wiersz 284) i w zwalnianiu trasy (wiersz 703). Rozszerzenie jej do 1 mm znaczy, że
skład może **cofnąć się o milimetr bez odmowy**, przejechanie autorytetu o milimetr
przestaje być zgłaszane, a trasa zwalnia się milimetr wcześniej. Dokumentacja tej stałej
w `LineDrive` mówi wprost, czym ona **nie jest**: „Nie jest zapasem bezpieczeństwa — jest
granicą, poniżej której dwie liczby double opisujące to samo miejsce nie mają prawa być
uznane za różne". 1 mm nie jest granicą reprezentacji `double`; to jest odległość.

**Zmierzone** — strażnik cofania na oryginale:

```
EPSILON FixedBlockSystem=1.0E-009 m, LineDrive=1.0E-009 m
COFNIECIE o 1.0E-010 m -> PRZESZLO (front=499.999999999900)
COFNIECIE o 1.0E-009 m -> PRZESZLO (front=499.999999999000)
COFNIECIE o 1.0E-006 m -> ODMOWA
COFNIECIE o 1.0E-004 m -> ODMOWA
COFNIECIE o 1.0E-003 m -> ODMOWA
```

Po mutacji ostatnie trzy wiersze zmieniają się w `PRZESZLO`. Test
`Sklad_nie_moze_cofnac_sie_na_planie` istnieje, ale cofa skład o odległość makroskopową,
więc mieści się i w jednej, i w drugiej tolerancji.

**Brakujący test.** Cofnięcie o `10 * PositionEpsilonM` musi być odmową, a o
`0.1 * PositionEpsilonM` — przejść. Przy okazji: sonda pokazuje, że
`FixedBlockSystem.PositionEpsilonM` i `LineDrive.PositionEpsilonM` to **dwie osobne
stałe o tej samej wartości**, a komentarz przy tej drugiej mówi „ta sama co
w `FixedBlockSystem`". Nic nie pilnuje, żeby pozostały równe; to osobna, jednowierszowa
bramka.

### 3.4 TP10 — strażnik zera w `BrakingDistanceM` jest martwy, a metoda jest publiczna

```csharp
// src/Sim/Signalling/TrainProtection.cs:295-296
public double BrakingDistanceM(double speedMps) =>
    speedMps <= 0.0 ? 0.0 : _solver.Solve(speedMps, 0.0, _serviceBrakeMps2).DistanceM;
```

Mutacja: `<= 0.0` → `< 0.0`.

**Dlaczego to jest zmiana zachowania, i to ostra.** Solver **nie przyjmuje zera**:

```
SOLVER_V0 rzuca ArgumentOutOfRangeException: Prędkość początkowa musi być dodatnia
i skończona. (Parameter 'startSpeedMps') Actual value was 0.
```

Po mutacji `BrakingDistanceM(0.0)` nie zwraca 0,0 — **rzuca wyjątek**. To nie jest
różnica rzędu ulp ani przesunięcie granicy: to zamiana wartości na awarię. Mimo to
mutacja przechodzi 376/376, bo w obecnym grafie wywołań nikt nie woła tej metody z zerem:
`PermittedSpeedMps` podaje jej sufit planu (dodatni) i środki bisekcji (dodatnie).
Strażnik jest więc **martwy** — a metoda jest `public`, więc kontrakt „zero znaczy zero
metrów", który on realizuje, jest zadeklarowany i niesprawdzony.

**Brakujący test.** `BrakingDistanceM(0.0)` zwraca dokładnie `0.0` i nie rzuca. Jeden
wiersz, a przybija granicę, przy której publiczne API zachowuje się inaczej niż solver
pod spodem.

### 3.5 RD05 — domyślny odstęp żądań zmienia przejazd i nie jest nigdzie przybity

```csharp
// src/Sim/Signalling/RouteDispatcher.cs:46
public const long DefaultRequestIntervalSteps = FixedStep.SimulationHertz;
```

Mutacja: `SimulationHertz` → `2 * SimulationHertz`, czyli odstęp 1 s → 2 s. `LineCore`
buduje nastawnię bez argumentu (`new RouteDispatcher(plan)`), więc ta stała rządzi
**każdym** przejazdem linii.

**Zmierzone**, ten sam scenariusz co w 3.1:

```
== RD05: DefaultRequestIntervalSteps  ->  2 * SimulationHertz
NASTAWNIA kroki=60000 odstep=240 zaryglowanych=14 odmow=79
          zdarzen_RouteRequested=93 RouteRejected=79 zdarzen_lacznie=355
          A=4502.44 B=3625.96
```

Drugi skład kończy 500-sekundowy przebieg na 3625,96 m zamiast 3639,68 m — **13,72 m
różnicy**, wzięte wyłącznie z tego, że sygnał puszcza go o sekundę później. Mierzalna
zmiana odstępu między składami, czyli dokładnie tej wielkości, dla której ten scenariusz
istnieje. Klasa B, a nie A, bo skutkiem jest przesunięcie w rozkładzie, nie utrata
zapisu ani nie zachowanie ochrony.

**Brakujący test.** Asercja, że `DefaultRequestIntervalSteps == FixedStep.SimulationHertz`
z uzasadnieniem „jedna sekunda symulacji", albo — mocniej — test na `LineCore`, w którym
podwojenie odstępu wydłuża przejazd drugiego składu o mierzalną wartość.

### 3.6 LC04 i LC07 — czas nawrotu jest przybity od dołu, ale nie co do kroku

```csharp
// src/Sim/Line/LineCore.cs:641
if (Steps - train.FinishedAtStep.Value < _turnbackSteps)
// src/Sim/Line/LineCore.cs:305
? (long)Math.Round(turnbackSeconds / step.Seconds)
```

**LC04** (`<` → `<=`) opóźnia wypuszczenie pojazdu o jeden krok, czyli 1/120 s. Test
`Turnback_nie_wypuszcza_pojazdu_wczesniej_niz_po_zmierzonym_czasie` pilnuje wyłącznie
granicy **od dołu** — pojazd wypuszczony o krok później nadal jej nie łamie. Skala jest
mała, ale kierunek jest jednostronny: nic nie broni przed nawrotem dłuższym, niż mówi
argument.

**LC07** (`Math.Round` → `Math.Truncate`) rozstrzyga, co się dzieje z czasem nawrotu,
który nie jest wielokrotnością kroku. Zmierzone:

```
NAWROT 0.004 s  -> raw=0.4800,     Round=0,     Truncate=0
NAWROT 0.005 s  -> raw=0.6000,     Round=1,     Truncate=0
NAWROT 0.0084 s -> raw=1.0080,     Round=1,     Truncate=1
NAWROT 90 s     -> raw=10800.0000, Round=10800, Truncate=10800
NAWROT 90.004 s -> raw=10800.4800, Round=10800, Truncate=10800
```

Rozjazd jest dokładnie w jednym miejscu: **0,005 s**. Oryginał zaokrągla to w górę do
jednego kroku (czyli po cichu wydłuża nawrót o 67 %), mutant ucina do zera i wtedy
wchodzi strażnik z wiersza 307, który **odmawia**. Mutant jest więc surowszy od
oryginału, a `Turnback_krotszy_niz_krok_jest_ODMOWA_a_nie_cichym_wylaczeniem` przechodzi
w obu wersjach, bo używa wartości leżącej poniżej 0,004 s. Tryb zaokrąglenia jest
niezapisaną decyzją projektową.

**Brakujące testy.** Dla LC04: nawrót o zadanej długości wypuszcza pojazd dokładnie na
kroku `FinishedAtStep + TurnbackSteps`, ani krok wcześniej, ani krok później. Dla LC07:
nawrót 0,005 s przy kroku 1/120 s — z asercją na to, co ma się stać, bo dziś kod robi
tu jedno, a docstring broni tylko przed drugim.

---

## 4. Granice, których bateria nie dotknęła — klasa C

Te pięć **nie jest udowodnioną równoważnością**. Są to mutacje, których punkt przerzutu
wymaga dokładnej równości dwóch liczb zmiennoprzecinkowych, a takiej równości w żadnym
przebiegu nie zmierzono. Wpisanie ich jako usterek zawyżyłoby znalezisko tak samo, jak
liczenie ich za równoważne zaniżyłoby ryzyko.

| id | mutacja | co musiałoby zajść | pomiar |
|---|---|---|---|
| TP08 | `speedMps > permitted` → `>=` | prędkość składu **równa co do bitu** dopuszczalnej | 94 060 kroków przejazdu z ATP: `v == v_dop` **0 razy**, `v > v_dop` 4576, `v < v_dop` 89 484 |
| TP05 | `BrakingDistanceM(ceiling) <= dist` → `<` | odległość autorytetu równa co do bitu drodze hamowania z sufitu planu (196,386 m przy 72 km/h) | 94 060 kroków: **0 równości**, najbliższe podejście 6,17 mm |
| FB02 | `FrontM >= last.StartM - eps` → `>` | czoło dokładnie na `StartM - 1e-9` | kilometraż jest sumą przyrostów kroku; trafienie w tę wartość co do bitu nie zaszło |
| FB04 | `frontChainageM < FrontM - eps` → `<=` | nowy kilometraż dokładnie równy `FrontM - 1e-9` | jw. |
| LD05 | `need.DecelerationMps2 < _trigger` → `<=` | wyjście solvera równe co do bitu `BrakeUsageFraction * ServiceBrakeMps2` = 1,1 | `_trigger` jest iloczynem dwóch stałych, `need` wynikiem bisekcji; równość nie zaszła |

Osobna uwaga do LD05: **we wszystkich testach `BrakeUsageFraction` wynosi 1,0** — jedyne
wywołanie `new LineRunSettings(...)` w `LineCoreTests` i oba pomocniki `Settings(...)`
w `LineDriveTests` i `LineRunTests` podają tę samą wartość. Parametr jest więc
zadeklarowany jako założenie bez źródła, a mierzony tylko w jednym punkcie swojej
dziedziny. To nie jest ta mutacja, ale widać to przy niej.

---

## 5. Komunikaty — klasa D, i dlaczego nie są zaległością

| id | mutacja | dlaczego nie zrównuję jej z warunkiem hamowania |
|---|---|---|
| RD06 | tekst wyjątku `"Odstęp między żądaniami trasy musi być dodatni."` | `RefusesANonPositiveInterval` sprawdza **typ** wyjątku i to jest właściwa rzecz do sprawdzania. Przybijanie treści komunikatu robi z tekstu dla człowieka element API i pęka przy każdej korekcie literówki. |
| FB08 | powód odmowy `"route-already-locked"` → `"route-already-blocked"` | Ciąg nie występuje **nigdzie** poza miejscem, w którym powstaje — sprawdzone `grep`em po `.cs` i `.py` w całym drzewie. Nic go nie parsuje, więc jest napisem dla czytającego strumień, a nie stanem. |

FB08 stoi wyżej niż RD06 i warto to powiedzieć: to jest powód odmowy **w strumieniu
zdarzeń**, czyli w jedynym trwałym zapisie pracy sygnalizacji. Dziś nikt go nie czyta
maszynowo. W dniu, w którym zacznie czytać, przestanie być klasą D.

---

## 6. Rzeczywiste wyjście weryfikacji

Punkt wyjścia i stan po przywróceniu drzewa — ten sam:

```
$ dotnet test tests/Sim.Tests
Passed!  - Failed:     0, Passed:   376, Skipped:     0, Total:   376, Duration: 17 s

$ python3 tools/tests/test_all.py
  1467/1467 przeszło

$ git status --porcelain
(pusto)
```

Przykład mutacji **zabitej** — TP01, `Math.Max` → `Math.Min` w `ProtectionDecision.Apply`:

```
  Failed Ingerencja_sluzbowa_zeruje_trakcje_i_podaje_zadany_hamulec [15 ms]
  Failed Ochrona_nie_odpuszcza_hamulca_ktory_maszynista_juz_podal [< 1 ms]
  Failed Nad_limitem_planu_ochrona_hamuje_i_da_sie_to_zmierzyc [760 ms]

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

Przykład mutacji **ocalałej** — RD03, `steps - last` → `steps + last`, czyli usterka
z sekcji 3.1:

```
  Sim -> src/Sim/bin/Debug/net10.0/MetroBxl.Sim.dll
  Sim.Tests -> tests/Sim.Tests/bin/Debug/net10.0/MetroBxl.Sim.Tests.dll
Test run for tests/Sim.Tests/bin/Debug/net10.0/MetroBxl.Sim.Tests.dll (.NETCoreApp,Version=v10.0)
A total of 1 test files matched the specified pattern.

Passed!  - Failed:     0, Passed:   376, Skipped:     0, Total:   376, Duration: 21 s
```

Zielono, a nastawnia pyta 119 razy częściej, niż wolno.

Pełny wykaz 42 przebiegów, z nazwami testów, które padły przy każdej zabitej mutacji,
jest w sekcji 7.

---

## 7. Wszystkie 42 mutacje

Kolumna „padło na" wymienia testy, które zgłosiły błąd; przy mutacjach walących szeroko
podana jest liczba i trzy przykłady.

### `src/Sim/Signalling/TrainProtection.cs`

| id | mutacja | wynik | padło na |
|---|---|---|---|
| TP01 | `Math.Max(requested.Brake, …)` → `Math.Min` | zabita 3/376 | `Ochrona_nie_odpuszcza_hamulca_ktory_maszynista_juz_podal`, `Ingerencja_sluzbowa_zeruje_trakcje_i_podaje_zadany_hamulec`, `Nad_limitem_planu_ochrona_hamuje_i_da_sie_to_zmierzyc` |
| TP02 | ingerencja awaryjna `DriverCommand(0.0, 1.0)` → `0.5` | zabita 1/376 | `Ingerencja_awaryjna_daje_pelny_hamulec_niezaleznie_od_zadania` |
| TP03 | `BrakeDemandMps2 > serviceBrakeMps2` → `>=` | zabita 1/376 | `Zadanie_ponad_hamulec_sluzbowy_jest_widoczne_a_nie_zamiecione` |
| TP04 | `StandstillSpeedMps = 1e-6` → `1e-3` | **ocalała** | — |
| TP05 | `BrakingDistanceM(ceiling) <= dist` → `<` | **ocalała** | — |
| TP06 | `TryRequiredDeceleration(…) && need <= brake` → `\|\|` | zabita 3/376 | `Gdy_hamulec_sluzbowy_nie_wystarcza_ingerencja_jest_awaryjna`, `Prog_miedzy_sluzbowym_a_awaryjnym_wypada_tam_gdzie_sluzbowy_przestaje_wystarczac`, `Hamowanie_na_zadanie_ATP_konczy_sie_przed_koncem_authority` |
| TP07 | `overspeed = v > permitted && v > Standstill` → `\|\|` | zabita 3/376 | `Predkosc_ponad_krzywa_wywoluje_ostrzezenie_i_ingerencje`, `Pod_limitem_planu_ochrona_nie_zmienia_przejazdu_ani_o_bit`, `Nad_limitem_planu_ochrona_hamuje_i_da_sie_to_zmierzyc` |
| TP08 | `speedMps > permitted` → `>=` | **ocalała** | — |
| TP09 | `Variant == LegacyWithKcv && !kcvAvailable` → `\|\|` | zabita 3/376 | `W_wariancie_KCV_brak_potwierdzenia_blokuje_drzwi`, `Drzwi_zwalniaja_sie_tylko_na_postoju_w_bloku_peronowym`, `Dwa_sklady_na_pakiecie_A_dojezdzaja_bez_kolizji` |
| TP10 | `speedMps <= 0.0` → `< 0.0` | **ocalała** | — |

### `src/Sim/Signalling/RouteDispatcher.cs`

| id | mutacja | wynik | padło na |
|---|---|---|---|
| RD01 | `!RequireRoute \|\| RouteOf(…) is not null` → `&&` | zabita 3/376 | `DoesNothingWhenThePlanDoesNotRequireRoutes`, `DoesNotAskAgainWhileTheTrainAlreadyHoldsARoute`, `Na_prawdziwym_planie_wymagajacym_tras_linia_przejezdza_cala_os` |
| RD02 | `steps - last < _intervalSteps` → `<=` | zabita 1/376 | `AsksAtMostOncePerIntervalAndTheIntervalIsMeasuredInSteps` |
| RD03 | `steps - last` → `steps + last` | **ocalała** | — |
| RD04 | `requestIntervalSteps <= 0L` → `< 0L` | zabita 1/376 | `RefusesANonPositiveInterval` |
| RD05 | domyślny odstęp → `2 * SimulationHertz` | **ocalała** | — |
| RD06 | tekst komunikatu wyjątku | **ocalała** | — |

### `src/Sim/Signalling/FixedBlockSystem.cs`

| id | mutacja | wynik | padło na |
|---|---|---|---|
| FB01 | `target > EndChainageM + eps` → `- eps` | zabita 1/376 | `Dwa_sklady_w_kolejnych_blokach_nie_moga_sie_zejsc` |
| FB02 | `FrontM >= last.StartM - eps` → `>` | **ocalała** | — |
| FB03 | `last.StartM` → `last.EndM` w zwalnianiu trasy | zabita 14/376 | `Trasa_zwalnia_sie_gdy_sklad_wjedzie_do_bloku_docelowego`, `Turnback_zwalnia_ostatni_peron_i_drugi_sklad_dojezdza_do_konca`, `Na_prawdziwym_planie_wymagajacym_tras_linia_przejezdza_cala_os` |
| FB04 | `frontChainageM < FrontM - eps` → `<=` | **ocalała** | — |
| FB05 | `Math.Max(FrontM, end - margin)` → `Math.Min` | zabita 28/376 | `Bez_innych_skladow_authority_siega_konca_planu`, `Dwa_sklady_w_kolejnych_blokach_nie_moga_sie_zejsc`, `LocksTheRouteLeavingTheBlockTheTrainStandsIn` |
| FB06 | `end - AuthorityMarginM` → `end + AuthorityMarginM` | zabita 1/376 | `Zapas_za_koncem_authority_skraca_droge_o_dokladnie_tyle_ile_deklaruje` |
| FB07 | `PositionEpsilonM = 1e-9` → `1e-3` | **ocalała** | — |
| FB08 | `"route-already-locked"` → `"route-already-blocked"` | **ocalała** | — |

### `src/Sim/Line/LineCore.cs`

| id | mutacja | wynik | padło na |
|---|---|---|---|
| LC01 | `ReleaseStep > Steps` → `>=` | zabita 3/376 | `Sklad_nie_wjezdza_na_zajety_peron_poczatkowy_tylko_czeka`, `Skladowi_na_pustej_linii_autorytet_konczy_sie_dopiero_na_koncu_planu`, `Ochrona_pociagu_jest_domyslnie_wylaczona` |
| LC02 | drugie `\|\|` w warunku wyjazdu → `&&` | zabita 3/376 | `Sklad_nie_wjezdza_na_zajety_peron_poczatkowy_tylko_czeka`, `Wynik_nie_zalezy_od_kolejnosci_zgloszenia_skladow`, `Z_ochrona_wynik_nadal_nie_zalezy_od_kolejnosci_zgloszenia_skladow` |
| LC03 | `BrakeDemandMps2 > MaxBrakeDemandMps2` → `<` | zabita 1/376 | `Nad_limitem_planu_ochrona_hamuje_i_da_sie_to_zmierzyc` |
| LC04 | `Steps - FinishedAtStep < _turnbackSteps` → `<=` | **ocalała** | — |
| LC05 | `Steps - FinishedAtStep` → `Steps + FinishedAtStep` | zabita 2/376 | `Turnback_nie_wypuszcza_pojazdu_wczesniej_niz_po_zmierzonym_czasie`, `Turnback_zwalnia_ostatni_peron_i_drugi_sklad_dojezdza_do_konca` |
| LC06 | `releaseStep < Steps` → `<=` | zabita 25/376 | `Czas_linii_jest_funkcja_liczby_krokow`, `Dwa_przebiegi_tego_samego_scenariusza_daja_ten_sam_odcisk_stanu`, `Na_prawdziwym_planie_wymagajacym_tras_linia_przejezdza_cala_os` |
| LC07 | `Math.Round` → `Math.Truncate` | **ocalała** | — |
| LC08 | `_trains.Count > 0` → `>= 0` | zabita 1/376 | `Linia_bez_skladow_nigdy_nie_jest_skonczona` |
| LC09 | `Overlaps(…) && StateOf(…) != Clear` → `\|\|` | zabita 18/376 | `Sklad_nie_wjezdza_na_zajety_peron_poczatkowy_tylko_czeka`, `Odstep_wydluza_przejazd_drugiego_skladu_wobec_pustej_linii`, `Drugi_sklad_zatrzymuje_sie_przed_blokiem_zajetym_przez_pierwszy` |

### `src/Sim/Train/LineDrive.cs`

| id | mutacja | wynik | padło na |
|---|---|---|---|
| LD01 | `limit < target ? limit : target` → `limit > target` | zabita 16/376 | `Autorytet_blizej_niz_stacja_zatrzymuje_sklad_przed_nim`, `Autorytet_dalej_niz_stacja_nie_zmienia_ani_jednego_kroku`, `Skladowi_na_pustej_linii_autorytet_konczy_sie_dopiero_na_koncu_planu` |
| LD02 | `stopAt > _brakingToM + eps` → `- eps` | zabita 8/376 | `Raz_zaczete_hamowanie_nie_wraca_do_trakcji`, `Postoj_przed_autorytetem_jest_naprawde_postojem_a_nie_pelzaniem`, `Zaden_sklad_nie_wjezdza_w_blok_zajety_przez_inny` |
| LD03 | `_braking && stopAt < target && v <= 0` → `\|\|` | zabita 9/376 | `Postoj_przed_autorytetem_jest_naprawde_postojem_a_nie_pelzaniem`, `Otwarty_autorytet_puszcza_sklad_dalej_zamiast_zostawic_go_na_wybiegu`, `Staje_na_peronie_a_nie_gdziekolwiek_w_oknie` |
| LD04 | `BrakeUsageFraction * ServiceBrakeMps2` → `/` | zabita 1/376 | `Nad_limitem_planu_ochrona_hamuje_i_da_sie_to_zmierzyc` |
| LD05 | `need.DecelerationMps2 < _trigger` → `<=` | **ocalała** | — |
| LD06 | `v² / (2.0 * remainingM)` → `(3.0 * remainingM)` | zabita 5/376 | `Staje_na_peronie_a_nie_gdziekolwiek_w_oknie`, `Autorytet_blizej_niz_stacja_zatrzymuje_sklad_przed_nim`, `Zaden_sklad_nie_wjezdza_w_blok_zajety_przez_inny` |
| LD07 | `chainage >= target - StopWindowM` → `+ StopWindowM` | zabita 29/376 | `Blad_zatrzymania_nie_kumuluje_sie_wzdluz_linii`, `Dluzsza_wymiana_pasazerow_wydluza_przejazd_o_dokladnie_tyle_ile_postojow`, `Chainage_i_postoj_sa_widoczne_w_trakcie_jazdy` |
| LD08 | `_state.SpeedMps > _topSpeed` → `<` | zabita 2/376 | `Szczyt_predkosci_jest_liczony_od_nowa_na_kazdym_odcinku`, `Otwarty_autorytet_puszcza_sklad_dalej_zamiast_zostawic_go_na_wybiegu` |
| LD09 | `(required - passive)` → `(required + passive)` | zabita 1/376 | `Nad_limitem_planu_ochrona_hamuje_i_da_sie_to_zmierzyc` |

---

## 8. Czego świadomie nie zrobiono

**Nie naprawiono niczego.** Zadanie było pomiarem, a nie łataniem, i mieszanie tych
dwóch rzeczy w jednym commicie zabrałoby raportowi kontrolę negatywną: dopisany test
przestaje mierzyć stan `main` z chwili pomiaru. Siedem realnych dziur z sekcji 3 nadaje
się na osobne zadania w formacie z `CLAUDE.md` §6 i każda ma tam wpisany brakujący test.

**Nie mutowano testów**, tylko kod pod testem. Ocalała mutacja mówi o zestawie testów,
nie o module.

**Nie tknięto `data/`** (reguła 6), żadnego workflow CI ani `docs/`.

**Nie dodano sondy do repozytorium.** Pomiary z sekcji 3 pochodzą z projektu leżącego
poza drzewem, odwołującego się do `src/Sim/Sim.csproj`. Sonda nie jest bramką i nie
powinna udawać, że nią jest; gdyby miała zostać, to jako testy z sekcji 3, a nie jako
program konsolowy.

**Nie rozstrzygnięto, jak ma się zachować nawrót krótszy niż krok** (LC07). Kod dziś
zaokrągla w górę, docstring broni tylko przed zaokrągleniem w dół do zera. Która z tych
dwóch rzeczy jest zamierzona, jest decyzją projektową, której nie ma w dokumentach —
`CLAUDE.md` §8.

**Nie mutowano `Replay` ani `StateDigest`** w `FixedBlockSystem`, mimo że są w zakresie
pliku. Budżet 42 mutacji rozłożono na warunki decydujące o ruchu, hamowaniu i zapisie;
odtwarzanie stanu ma własny test tożsamościowy
(`Odtworzenie_ze_strumienia_zdarzen_daje_identyczny_stan`), który jest silniejszą bramką
niż pojedyncza mutacja operatora, i sprawdzenie tego założenia to osobny pomiar.

---

## 9. Co zauważono przy okazji, a czego nie ruszono

**`BrakeUsageFraction` jest mierzony w jednym punkcie.** Wszystkie trzy miejsca, które
w testach budują `LineRunSettings`, podają `1.0`. Parametr jest zadeklarowany jako
założenie bez źródła i sam typ `LineRunSettings` istnieje po to, żeby takie liczby były
widoczne — ale bateria nie sprawdza ani jednej innej wartości. To nie jest ustalenie tego
przeglądu, tylko to, co przy nim widać.

**`PositionEpsilonM` istnieje w dwóch egzemplarzach.** `FixedBlockSystem.PositionEpsilonM`
i `LineDrive.PositionEpsilonM` mają tę samą wartość `1e-9` i komentarz przy drugiej
mówi „ta sama co w `FixedBlockSystem`". Nic tej równości nie pilnuje. Zmierzone sondą:
`EPSILON FixedBlockSystem=1.0E-009 m, LineDrive=1.0E-009 m` — dziś zgodne.

**`Nad_limitem_planu_ochrona_hamuje_i_da_sie_to_zmierzyc` jest najczęstszym zabójcą
w całym przeglądzie** — pada przy **14 z 28** zabitych mutacji, czyli przy połowie,
i przy mutacjach we wszystkich pięciu plikach. Drugi w kolejności,
`Na_prawdziwym_planie_wymagajacym_tras_linia_przejezdza_cala_os`, pada przy 7. To dobra
wiadomość o tych testach i ostrzeżenie zarazem: duża część pokrycia rdzenia wisi na
jednym scenariuszu z pakietu A, więc jego przypadkowe osłabienie zabrałoby pokrycie
w miejscach, które z nim nie sąsiadują.

(Liczby policzone z pełnych dzienników przebiegów, nie z tabel w sekcji 7 — tam listy
nazw są ucięte do trzech przykładów.)

**Trzy mutacje kompilują się i przechodzą w mniej niż 8 s** (LC06 6,0 s, LC09 7,8 s)
zamiast typowych ~20 s, bo wywracają tak dużo testów, że przebieg kończy się wcześniej.
Nie ma to wpływu na wynik, ale tłumaczy nierówne czasy w dzienniku przebiegu.
