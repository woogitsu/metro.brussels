# 6.D290 · Dwadzieścia dwa z dwudziestu czterech — a dwa, które zostają, to dokładnie te z 6.D289

**Data:** 19.09.2026 · **Gałąź:** `claude/sharp-ramanujan-jdr51o` · **Baza:** `cc3ca84`

6.D234 zapisało wniosek: „czy typ jest używany, nie da się w C# rozstrzygnąć skanem
tekstowym", bo wołający piszą `var`. Wniosek stał bez liczby, której dotyczy.
Ta pozycja tę liczbę podaje.

---

## 1. Populacja: dwadzieścia cztery typy w całym `src/`

```
typow publicznych `src/`: 156 | z src: 117 | tylko testy: 15 | NIENAZWANE: 24
skladnikow publicznych dopasowanych: 845
```

**Kontrola spójności z 6.D289 zdana:** 156 = 109 + 42 + 5, a 24 = 13 + 10 + 1, czyli
sumy po katalogach z pozycji domkniętej godzinę wcześniej. Znaczy to także, że **żadna
nazwa typu nie powtarza się między katalogami** — gdyby się powtarzała, `typy_publiczne`
brałoby pierwszą deklarację i zbiór byłby mniejszy od sumy. Przewidziałem to przed
pomiarem jako jedyne ryzyko tej liczby.

## 2. Trzy liczby — a „typ zwracany" ma DWA czytania i podaję oba

Pole „Wyjście" pyta, ile z tych typów jest **zwracanych przez składnik publiczny**.
Pytanie nie jest jednoznaczne i rozstrzygnięcie podjąłem **przed** policzeniem:

* **WPROST** — typ stoi sam w pozycji zwracanej: `public T Nazwa(`, `public T Nazwa {`, `=>`.
* **W OPAKOWANIU** — typ stoi gdziekolwiek w pozycji zwracanej: `IReadOnlyList<T>`,
  krotka `(T A, U B)`, `T?`.

| miara | trafionych z 24 | `record struct` | `class` |
|---|---|---|---|
| WPROST | **15** | 12 | 3 |
| W OPAKOWANIU | **22** | 19 | 3 |

Obie są prawdziwe i **żadna nie jest „tą właściwą"**: różnica siedmiu typów to te,
które składnik zwraca w liście albo w krotce. Podanie samej pierwszej zaniżyłoby
odpowiedź o jedną trzecią, a samej drugiej — ukryłoby, że siedem typów nie pada
w pozycji zwracanej bez opakowania.

### Lista imienna, WPROST (15)

| nazwa | rodzaj | zwracany przez |
|---|---|---|
| `BrakingPoint` | `record struct` | `Solve()` w `src/Sim/Physics/BrakingPointSolver.cs` |
| `BrakingRunResult` | `class` | `ToStop()` w `src/Sim/Train/BrakingRun.cs` |
| `CbtcTestSpan` | `record struct` | `OnAxis()` w `src/Sim/Signalling/CbtcTestArea.cs` |
| `ChaseAvailability` | `record struct` | `Availability()` w `src/Game/World/ChaseCameraAim.cs` |
| `ChunkLod` | `record struct` | `Lod()` w `src/Game/Assets/ChunkManifest.cs` |
| `DoorInterlock` | `record struct` | `DoorRelease()` w `src/Sim/Signalling/TrainProtection.cs` |
| `LineBudgetCensus` | `class` | `Census()` w `src/Sim.Runner/LineBudget.cs` |
| `RegistryEntry` | `class` | `Get()` w `src/Sim/Physics/VehicleRegistry.cs` |
| `RunRestartValues` | `record struct` | `Values()` w `src/Sim/Train/RunRestart.cs` |
| `RunStart` | `record struct` | `Values()` w `src/Game/RunReset.cs` |
| `ServicePeak` | `record struct` | `Peak()` w `src/Sim/Line/ServiceDay.cs` |
| `StationApproach` | `record struct` | `Approach()` w `src/Sim/Train/StationService.cs` |
| `StreamWindow` | `record struct` | `Window()` w `src/Game/Assets/StreamingPlan.cs` |
| `StreamingDelta` | `record struct` | `Delta()` w `src/Game/Assets/StreamingPlan.cs` |
| `TrackFrame` | `record struct` | `Chord()` w `src/Game/World/SceneAxis.cs` |

### Siedem dochodzących w opakowaniu

`BrakingReferenceRow` (`ReferenceTable()`), `CbtcDynamicTestSite` (`DynamicTestSites()`),
`RouteStation` (`Stations()`), `ServiceBlock` (`Blocks()`),
`SignallingAssumption` (`Assumptions()`), `TelemetrySample` (`Samples()`),
`ViewAssumption` (`All()`). Wszystkie siedem to `record struct`, wszystkie siedem
zwracane w liczbie mnogiej — nazwy składników same to mówią.

## 3. Dwa, które zostają — i to jest wynik, a nie reszta z odejmowania

Typów nienazwanych, które **nie są zwracane przez żaden składnik publiczny** w żadnym
z dwóch czytań, są **dwa**:

| nazwa | plik | czym naprawdę jest |
|---|---|---|
| `DriverBinding` | `src/Game/Input/DriverActions.cs` | konstruowany czternaście razy we własnym pliku; czyta go **bramka Pythona** `tools/tests/test_player_package.py:98`, cięciem po napisie `new DriverBinding(` |
| `FirstRun` | `src/Game/FirstRun.cs` | **scena główna gry**; wiązanie robi silnik przez `project.godot` → `FirstRun.tscn` → `res://FirstRun.cs` |

To są **dokładnie te dwa**, którym 6.D289 przypisało drogę użycia INNĄ niż `var`.
Pozycja 6.D298, dopisana przy tamtej, liczy cztery drogi: wiązanie silnika, punkt
wejścia środowiska, odczyt źródła C# przez bramkę Pythona i `var`.

**Przewidziałem, że te dwa zbiory „przetną się, ale nie pokryją". Zmierzone jest
coś mocniejszego: są KOMPLEMENTARNE.** Dwadzieścia dwa typy, które składnik zwraca,
to rodzina `var`; dwa, których nie zwraca, mają obie pozostałe drogi z 6.D298.
Pytanie strukturalne („czy typ jest zwracany") i pytanie o użytkownika („kto go
używa") tną tę samą dwudziestkę czwórkę na te same dwie części.

Przewidywanie było więc **za słabe, a nie chybione** — i zapisuję to tak, zamiast
odhaczać je jako trafione.

**Czego to NIE znaczy.** Komplementarność jest zmierzona na dziś i na dwudziestu
czterech typach. Nie wynika z niej, że każdy typ zwracany jest konsumowany przez `var`
— wynika tylko, że w tej populacji te dwie własności się pokrywają. Bramki na to
nie stawiam, bo pole „Wyjście" żąda trzech liczb i listy, a policzenie czterech dróg
jest treścią 6.D298; tam to zdanie będzie miało liczbę, na której da się je oprzeć.

## 4. Kontrola przyrządu — zdana, i SŁABSZA, niż wygląda

Pole „Weryfikacja" żąda: typ zwracany, którego nazwa PADA u wołającego, ma NIE trafić
na listę.

```
KONTROLA PRZYRZADU: typow zwracanych WPROST, ktorych nazwa PADA u wolajacego: 59
   z nich na liscie wyniku: [] (ma byc puste)
```

Populacja kontroli liczy **pięćdziesiąt dziewięć** typów, więc nie jest to kontrola
na jednym przypadku. Ale **spisałem przed przebiegiem, że ta kontrola jest słaba,
i tak jest**: sito „nienazwany nigdzie" działa PRZED pytaniem o zwracanie, więc cała
pięćdziesiątka dziewiątka odpada na pierwszym kroku, a nie dzięki logice typu
zwracanego. Kontrola potwierdza kolejność sit, nie poprawność rozbioru składników.
Tego, co sprawdza rozbiór, dostarcza §5.

## 5. GRANICA PRZYRZĄDU — a moja kontrola tej granicy myliła się DWA RAZY

Wzorzec `SKLADNIK` jest wyrażeniem regularnym, nie analizatorem symboli (pole
„Poza zakresem" zabrania analizatora wprost). Trzeba więc powiedzieć, czego nie widzi.
Mierzyłem to trzy razy i **dwa pierwsze pomiary były nieprawdziwe**.

**Pomiar pierwszy, nieprawdziwy.** Karmiłem wzorzec POJEDYNCZYMI WIERSZAMI i wyszło,
że nie dopasowuje 159 wierszy `public`, z czego dwa istotne. Fałsz: w `\s*` przed
grupą `[({]|=>` mieści się `\n`, więc wzorzec **przechodzi przez łamanie wiersza**
i właściwości wieloliniowe łapie. Sprawdzone wprost:

```
wzorzec na CALYM tekscie (z lamaniem wiersza): [('ServicePeak', 'Peak', '{')]
wzorzec na SAMYM wierszu: []
```

**Co ten fałsz złapało: sprzeczność między dwiema moimi własnymi liczbami.**
`ServicePeak` stał na liście wyniku jako zwracany przez `Peak()`, a kontrola granicy
mówiła, że wiersz `public ServicePeak Peak` jest NIEDOPASOWANY. Obie rzeczy nie mogły
być prawdziwe. Nie zapalił się żaden test — zapaliła się niezgodność dwóch liczb,
z których żadna nie była bramką.

**Pomiar drugi, też nieprawdziwy.** Liczyłem wiersz dopasowania z `m.start()`, a `^\s*`
może zacząć dopasowanie na KOŃCU POPRZEDNIEGO wiersza. Wyszło 599 „niewidzianych",
w tym `public ChunkLod Lod(int level)`, czyli deklaracja, którą wzorzec oczywiście
łapie — i to było widać gołym okiem na pierwszej pozycji listy.

**Pomiar trzeci, ten podaję.** Wiersz liczony od słowa `public`, nie od początku
dopasowania:

```
skladnikow dopasowanych przez wzorzec: 845
wierszy `public` poza deklaracjami i poza dopasowaniem: 144
  po klasach: {'const': 92, 'static readonly': 7, 'konstruktor': 42, 'INNE': 3}
```

Dziewięćdziesiąt dwa `const`, siedem `static readonly` i czterdzieści dwa konstruktory
są pomijane **słusznie**: pole i konstruktor nie mają typu zwracanego w sensie, o który
pyta ta pozycja. Naprawdę niewidziane są **trzy** składniki:

```
FixedStep.cs       public static bool operator ==(FixedStep left, FixedStep right) => …
FixedStep.cs       public static bool operator !=(FixedStep left, FixedStep right) => …
SignallingPlan.cs  public static string[] DefaultUnknownParameters() => new[]
```

**Żaden z tych trzech nie zwraca typu publicznego `src/`** (`bool`, `bool`, `string[]`),
więc granica przyrządu **nie rusza żadnej z trzech liczb**. Jest to stwierdzenie
sprawdzalne, a nie zapewnienie.

## 6. Przewidywania spisane PRZED pomiarem

| # | przewidywanie | wynik |
|---|---|---|
| 1 | zbiór nienazwanych w całym `src/` = 24 | trafione, i ryzyko kolizji nazw nazwane z góry |
| 2 | zwracanych przez składnik publiczny: 6–12 | **PUDŁO**, jest 15 wprost i 22 w opakowaniu |
| 3 | z nich `record struct`: 4–9 | **PUDŁO**, jest 12 i 19 |
| 4 | kontrola przyrządu zda, ale jest słaba | trafione co do obu połów |
| 5 | 6.D290 i 6.D298 nie liczą tego samego | trafione, ale ZA SŁABO — są komplementarne |
| 6 | pierwsza wersja czytnika się pomyli | trafione, i pomyliła się **kontrola granicy**, nie sam czytnik |

Oba pudła liczbowe są **w tę samą stronę**: zakładałem zjawisko węższe, niż jest.
Jest to czwarta pozycja z rzędu, w której moje przedziały wychodzą za niskie.

Przewidywanie 6 warto odczytać dokładnie: spodziewałem się pomyłki w rozbiorze
składników i zapisałem, że „trzeba będzie nazwać, czego czytnik NIE widzi". Rozbiór
wyszedł poprawny za pierwszym razem. Pomyliło się **narzędzie do mierzenia jego
granicy** — i to dwa razy.

## 7. Czego świadomie nie zrobiono

- **Nie usunięto ani nie podłączono żadnego typu** (pole „Poza zakresem").
- **Nie napisano analizatora symboli** — pole zabrania go wprost; stąd §5.
- **Nie postawiono bramki.** Pole „Wyjście" żąda trzech liczb i listy, a nie sita
  w drzewie; precedens 6.D286 i 6.D288. Zdanie o komplementarności, które byłoby
  najlepszym kandydatem do przybicia, należy do 6.D298 i tam dostanie liczbę.
- **Nie dotknięto `data/`.**
- **Nie wybrano jednej z dwóch miar** jako „tej właściwej" — obie stoją w tabeli,
  bo obie są odpowiedzią na to samo pytanie zadane inaczej.

## 8. Zauważone przy okazji, nietknięte

Siedem typów dochodzących w opakowaniu jest zwracanych **wyłącznie w liczbie mnogiej**
(`ReferenceTable`, `DynamicTestSites`, `Stations`, `Blocks`, `Assumptions`, `Samples`,
`All`). Czy „typ zwracany tylko jako element kolekcji" jest osobną klasą użycia —
piątą obok czterech z 6.D298 — ta pozycja nie pyta i nie rozstrzyga.
