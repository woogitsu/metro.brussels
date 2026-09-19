# 6.D234 — przypadków jest dwanaście, nie jeden, a skan po NAZWIE nie odpowiada na pytanie „czy typ jest używany"

**Data:** 19.09.2026 · **Gałąź:** `claude/sharp-ramanujan-jdr51o` · **Baza:** `323bff5`

Pozycja znała jeden przypadek (`CbtcTestArea`) i żądała pierwszej liczby: ilu typów
publicznych `src/Sim/` dotyczy to samo — „bo bramka postawiona na jednej nazwie jest
zapadką na nazwie". Liczba jest niżej. Ważniejsze od niej jest jednak to, czego pomiar
**nie może** rozstrzygnąć, i to stoi przed liczbą.

## 1. Granica przyrządu, bo ona zmienia czytanie wszystkich liczb

Skan po nazwie odpowiada na pytanie **„czy typ jest NAZYWANY"**, a nie „czy jest
UŻYWANY". W C# `var` i dekonstrukcja pozwalają użyć typu, nie pisząc jego nazwy —
i dwa przypadki z tego pomiaru pokazują to wprost:

| typ | nazwa poza własnym plikiem | a jednak |
|---|---|---|
| `BrakingRunResult` | **nigdzie** | typ zwracany `BrakingRun.ToStop` i `ToSpeed`, a `BrakingRun` jest wołany z `src/Sim.Runner/Program.cs` przez `var row in new BrakingRun(model).ReferenceTable(…)` |
| `RegistryEntry` | **nigdzie** | typ zwracany `VehicleRegistry.Get` i element `ApproximateEntries()`, a `VehicleRegistry` jest wołany z `src/Sim/Physics/VehicleModel.cs` i dwóch innych miejsc w `src/` |

Dlatego zbiór w bramce nazywa się `NIEWOLANE_PO_NAZWIE`, a **nie „martwe"**, i bramka
nie zgłasza ani jednego z nich jako martwego. Zgłaszanie ich byłoby bramką z 6.D27 —
zapalającą się na kodzie poprawnym.

## 2. Liczba, o którą pozycja pytała

Zmierzone 19.09.2026 na `323bff5`, maską literałów i komentarzy **pożyczoną**
z `tools/tests/test_dead_constants_csharp.py`:

| co | ile |
|---|---|
| typów publicznych w `src/Sim/` | **109** |
| wołanych po nazwie z `src/` | **84** |
| wołanych po nazwie **wyłącznie** z `tests/` | **12** |
| nienazwanych nigdzie poza własnym plikiem | **13** |

**Dwanaście, nie jeden** — i dwanaście z imienia:

`CbtcTestArea`, `CbtcTestStage`, `DriveSegment`, `JsonFields`, `KcvFunction`,
`LineRoute`, `LineTrain`, `ProtectionMode`, `ProtectionModeRegistry`,
`ProtectionModeStatus`, `ProtectionModeStatusParser`, `RouteGap`.

Trzynaście nienazwanych nigdzie: `BrakingPoint`, `BrakingReferenceRow`,
`BrakingRunResult`, `CbtcDynamicTestSite`, `CbtcTestSpan`, `DoorInterlock`,
`RegistryEntry`, `RouteStation`, `RunRestartValues`, `ServiceBlock`, `ServicePeak`,
`SignallingAssumption`, `StationApproach` — **jedenaście z nich to `record struct`**,
czyli dokładnie ten kształt, który konsumuje się przez `var`.

## 3. Własna pomyłka, zmierzona co do cyfry

Pierwsza wersja wzorca deklaracji czytała **71 typów zamiast 109**. Powód:
`public readonly record struct X` ma rodzaj **dwusłowny**, a wzorzec biorący `record`
za rodzaj czytał `struct` jako **nazwę typu**. Koszt:

| co | wzorzec błędny | wzorzec poprawny |
|---|---|---|
| typów publicznych | 71 | **109** |
| „tylko testy" | 10 | **12** |
| „nienazwane nigdzie" | 2 | **13** |

Trzydzieści osiem typów było dla skanu niewidocznych. **Nie znalazło tego oko, tylko
kolumna pomocnicza**: w zestawieniu sąsiadów pliku pojawiło się słowo `struct` jako
nazwa typu wołanego z `src/`. Pilnuje tego dziś
`test_wzorzec_czyta_record_struct_jako_JEDEN_rodzaj`, na próbce pięciu deklaracji.

## 4. Rozstrzygnięcie dla dwunastu — wszystkie ZOSTAJĄ

Pole „Wyjście" dopuszczało to wprost: „zostaje, bo niesie wiedzę o sieci, i jest to
zapisane". Powód jest **wspólny** i dlatego stoi raz, a nie dwanaście razy: to są typy
opisujące **sieć i jej reguły** — obszary testowe CBTC, tryby ochrony, trasę linii,
pola JSON-a danych — a nie kod pomocniczy testów. Usunięcie ich byłoby usunięciem
**danych**, nie kodu, a dane w tym projekcie mają źródło (`CLAUDE.md` §4.1).
Podłączenie któregokolwiek do gry jest decyzją projektową i pozycja wyklucza je wprost.

## 5. Kontrole, przewidywania spisane PRZED przebiegami

Wszystkie na **pełnej** kopii drzewa z `.git`, `__pycache__` czyszczony przed każdym
przebiegiem.

| kontrola | zmiana na kopii | przewidziane | zmierzone | zgodne |
|---|---|---|---|---|
| KN-0 | nic | zielone | **8/8** | tak |
| KN-1 | typ publiczny bez wołającego dopisany do `src/Sim/` | czerwień, lista go widzi | **7/8**, `('Zmyslony', 'niewołany po nazwie')` | tak |
| KN-2 | ten sam typ wołany z `tests/` | klasa „tylko testy" | **7/8**, `('Zmyslony', 'tylko testy')` | tak |
| KN-3 | ten sam typ wołany z `src/Game/` | nie trafia na żadną listę | **8/8** | tak |
| KN-5 | wzorzec cofnięty do wersji bez `record struct` | czerwień | **5/8**, w tym „71 przy podłodze 109" | tak |

**KN-1 i KN-2 dały najpierw komunikat NIEODRÓŻNIALNY** — oba mówiły tylko
`['Zmyslony']`, choć to dwa różne rozstrzygnięcia i dwa różne zbiory. Komunikat został
poprawiony tak, żeby **nazywał klasę**, i dopiero po tej poprawce para kontroli mówi
o czymś różnym. To nie jest kosmetyka: bez niej następny czytający nie wiedziałby,
do którego zbioru ma dopisać typ.

## 6. Weryfikacja

```
$ python3 tools/tests/test_all.py
  2649/2649 przeszło
  RAZEM 323.866 s, 2649 testów, 138 modułów
  KOD=0
```

Druga połowa polecenia z pola „Weryfikacja", `dotnet test tests/Sim.Tests`, jest
w tym kontenerze **niewykonalna**: `/root/.dotnet` nie istnieje, a `command -v dotnet`
milczy. Mówię to wprost zamiast pominąć — sprawdzi to job `sim` w CI. Ta zmiana nie
dotyka ani jednego pliku `.cs`, więc wynik tamtego zestawu nie ma się od czego zmienić;
to jest jednak **oczekiwanie, a nie pomiar**, i tak je zapisuję.

Zapadki podniesione w tym samym commicie, w zapisie „stoi dziś (stało wczoraj)":
`MODULOW_W_CALYM_DRZEWIE` = 218 (było 217), `BAJTKOD_PO_COMPILEALL_PLIKI` = 218
(było 217), `ROZKLAD_MODULOW` dla `tools/tests` = 146 (było 145),
`ASERCJI_NAPISOWYCH_RAZEM` = 934 (było 933), `KANDYDATOW_ODWZOROWAN` = 42 (było 41),
`ZAPADEK_RAZEM` = 87 (było 86), rozkład klas 18/3/64/2, para wolnych (64, 63),
zdanie o modułach zestawu 138 (było 137) oraz `MIN_REPORTS` o jeden.

## 7. Czego świadomie nie zrobiono

* **Nie usunięto żadnego typu** i nie podłączono `CbtcTestArea` do gry — pole „Poza
  zakresem" i §8.
* **Nie tknięto `docs/16-protection-modes.md`** — pole „Poza zakresem".
* **Nie napisano drugiej kopii rozbioru C#.** Maska literałów i komentarzy jest
  pożyczona; własna byłaby uboższa o dziury interpolacji, które tamta zna.
* **Nie zgłoszono trzynastu nienazwanych jako martwych** — §1 mówi, dlaczego byłby to
  fałsz.

## 8. Zauważone przy okazji, nietknięte

Pytanie „czy ten typ jest używany" w C# **nie da się rozstrzygnąć skanem tekstowym**
i ten pomiar jest na to dowodem: potrzeba by kompilatora albo analizatora symboli,
bo `var` zrywa związek między użyciem a nazwą. Dzisiejsza bramka mierzy więc to, co
zmierzyć może — NAZYWANIE — i mówi o tym w swojej pierwszej linii, żeby następny
czytający nie wziął jej za coś innego.
