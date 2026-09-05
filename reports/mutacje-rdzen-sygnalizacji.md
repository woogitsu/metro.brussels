# Przegląd mutacyjny rdzenia sygnalizacji i linii

**Zmierzone na commicie:** `d495051` (`main`, 05.09.2026)
**Zestaw testów w punkcie wyjścia:** 376 pozycji, wszystkie zielone, przebieg ~18 s.

W trakcie pomiaru `main` przesunął się na `0e1b161` (scalenie #225) i ta gałąź jest na
nim przebazowana. Liczby niżej pochodzą z `d495051` i **nie zostały przeliczone** —
zostały sprawdzone: #225 rusza wyłącznie narzędzia w Pythonie, a `dotnet test
tests/Sim.Tests` na `0e1b161` daje te same 376/376. Gdyby ruszyło `src/Sim/`, ten raport
wymagałby powtórzenia przebiegu, a nie dopisku.

Zielony zestaw testów nie mówi, że kod jest sprawdzony — mówi, że nie jest sprzeczny
sam ze sobą. Ten raport mierzy, ile z pięciu plików, które weszły na `main` w ostatnich
godzinach, jest naprawdę przybite: ochrona pociągu, nastawnia automatyczna, system
blokowy, rdzeń linii i prowadzenie składu.

**Kodu produkcyjnego nie tknięto.** Każda mutacja była przywracana przez
`git checkout -- <plik>` przed następną; na koniec `dotnet test tests/Sim.Tests` daje
znowu 376/376. Jedyna zmiana w repozytorium to ten plik.

---

## 0. Wynik, w jednym zdaniu

Na 45 mutacjach **35 zabitych, 10 ocalałych, 0 niekompilowalnych** — 77,8 % pokrycia.
Z tych dziesięciu **trzy są groźne**, dwie są nieprzetestowanymi strażnikami argumentów,
a pięć to granice na dokładnej równości `double`, których osiągalności **nie zmierzyłem**
— i sekcja 5 mówi, dlaczego to zastrzeżenie nie jest formalnością.

Najważniejsze pojedyncze znalezisko: **TP-08**. Ochrona pociągu porównuje prędkość
z dopuszczalną przez `>`, i zamiana na `>=` przechodzi przez wszystkie 376 testów —
podczas gdy zmierzony skutek to **4492 ingerencje hamulcem służbowym w składzie, który
jedzie dokładnie na limicie planu i nie łamie niczego**. Sekcja 4.1.

---

## 1. Narzędzie: dlaczego nie `tools/tests/mutation_sweep.py`

Sprawdzone, nie założone. `tools/tests/mutation_sweep.py` **nie da się użyć do C#**
i nie jest to kwestia przełącznika:

| miejsce w narzędziu | co tam jest |
|---|---|
| `discover()`, wiersz 180 | `if name.endswith(".py")` — inne rozszerzenia nie wchodzą |
| budowa listy mutacji | `ast.parse` z biblioteki standardowej Pythona |
| wyrocznia, wiersz 251 | `subprocess.run([sys.executable, ".../test_all.py"])` |

Trzy niezależne wiązania z Pythonem. Mutacje C# poszły więc osobnym skryptem, według
tej samej dyscypliny co tamten: jedna mutacja = jedna podmiana tekstu w jednym pliku,
z `assert s.count(old) == 1` **przed** podmianą, przywrócenie pliku przed następną,
dziennik JSONL dopisywany i `fsync`-owany po każdym wyniku.

## 2. Czego mutować się w C# nie da — i to jest zmierzone, nie założone

`if (false)` **nie kompiluje się**, a `src/Sim` ma `GenerateDocumentationFile`
i `TreatWarningsAsErrors`, więc zepsuta dokumentacja XML też wywala build. Obie rzeczy
zostały sprawdzone kontrolą negatywną, żeby kolumna „niekompilowalnych" była pomiarem,
a nie deklaracją:

| kontrola | podmiana | wynik builda |
|---|---|---|
| NK-01 | `if (speedMps <= StandstillSpeedMps)` → `if (false)` | `error CS0162: Unreachable code detected` |
| NK-02 | `<see cref="BrakingPointSolver.BisectionSteps"/>` → nieistniejący składnik | `error CS1574: XML comment has cref attribute ... that could not be resolved` |

Obie kontrole są **poza** pulą 45 i nie wchodzą do liczników — kompilator jest tu bramką,
a nie testem, więc zaliczenie ich jako pokrycia testowego byłoby zawyżeniem wyniku.

Mutowane były wyłącznie **wartości i operatory**: `>` ↔ `>=`, `<` ↔ `<=`, `&&` ↔ `||`,
`Math.Max` → `Math.Min`, `+` ↔ `-`, `*` → `/`, `++` → `--`, stała → inna stała.
Wszystkie 45 się skompilowały, więc kolumna „niekompilowalnych" wyszła zerem — nie
dlatego, że takich mutacji nie ma, tylko dlatego, że dobór ich unikał.

## 3. Wynik liczbowo

| plik | zastosowanych | zabitych | ocalałych | niekompilowalnych |
|---|---:|---:|---:|---:|
| `src/Sim/Signalling/TrainProtection.cs` | 12 | 8 | **4** | 0 |
| `src/Sim/Signalling/RouteDispatcher.cs` | 6 | 4 | **2** | 0 |
| `src/Sim/Signalling/FixedBlockSystem.cs` | 8 | 6 | **2** | 0 |
| `src/Sim/Line/LineCore.cs` | 9 | 8 | **1** | 0 |
| `src/Sim/Train/LineDrive.cs` | 10 | 9 | **1** | 0 |
| **razem** | **45** | **35** | **10** | **0** |

Bez timeoutów i bez mutacji nierozstrzygniętych.

`LineDrive` i `LineCore` są przybite najmocniej (9/10 i 8/9) i to nie jest przypadek:
obie mają testy pisane jako kontrole negatywne konkretnych usterek — komentarze przy
`Postoj_przed_autorytetem_jest_naprawde_postojem_a_nie_pelzaniem` czy
`Szczyt_predkosci_jest_liczony_od_nowa_na_kazdym_odcinku` wprost opisują mutację,
którą ten test ma zabijać. Widać to w wyniku.

`TrainProtection` wypada najsłabiej (8/12) i to też nie jest przypadek: **nie ma pliku
`TrainProtectionTests.cs`**. Ochrona jest testowana wyłącznie od strony scenariusza
(`ClassicSignallingScenarioTests`, `LineCoreTests`), więc jej granice i strażniki
argumentów nie mają gdzie być sprawdzone punktowo.

### Przykład zabicia — TP-02

Podmiana `Math.Max` na `Math.Min` w `ProtectionDecision.Apply`, czyli ochrona
odpuszczająca hamulec, który maszynista już podał:

```
Assert.AreEqual failed. Expected:<4576>. Actual:<8182>. zmierzone: 4576 krokow z hamulcem sluzbowym ochrony
  at MetroBxl.Sim.Tests.LineCoreTests.Nad_limitem_planu_ochrona_hamuje_i_da_sie_to_zmierzyc()
Failed!  - Failed:     3, Passed:   373, Skipped:     0, Total:   376, Duration: 17 s
```

### Przykład ocalenia — RD-04

Podmiana `steps - last` na `steps + last` w dławiku żądań `RouteDispatcher.Dispatch`:

```
Sim -> .../src/Sim/bin/Debug/net10.0/MetroBxl.Sim.dll
Sim.Tests -> .../tests/Sim.Tests/bin/Debug/net10.0/MetroBxl.Sim.Tests.dll
A total of 1 test files matched the specified pattern.
Passed!  - Failed:     0, Passed:   376, Skipped:     0, Total:   376, Duration: 18 s
```

---

## 4. Ocalałe

Każda pozycja: co zmieniono, dlaczego to jest zmiana **zachowania**, i jakiego testu
brakuje, żeby ją zabić. Kolejność jest kolejnością szkodliwości, nie kolejnością pliku.

### 4.1 GROŹNE — warunek decydujący o hamowaniu

#### TP-08 · `TrainProtection.Supervise` · `speedMps > permitted` → `>=`

**Zmierzone, nie wywnioskowane.** `TrainController.Advance` obcina prędkość zdaniem
`if (speed > speedLimitMps) speed = speedLimitMps;` — skład na pełnej trakcji jedzie
więc z prędkością **dokładnie równą** limitowi, bit w bit. `PermittedSpeedMps` przy
dostatecznie długim autorytecie zwraca **dokładnie** `_plan.PermittedSpeedMps`
(wczesne wyjście, wiersz 266). Gdy limit przejazdu równa się limitowi planu, mamy
`speedMps == permitted` na każdym kroku jazdy ustalonej.

Sonda na pakiecie A, limit przejazdu ustawiony na limit planu (20 m/s = 72,00 km/h),
jeden skład, ochrona włączona:

| | kod czysty | z TP-08 |
|---|---:|---:|
| kroków z prędkością **dokładnie** równą limitowi | 4492 | 4492 |
| ostrzeżeń (`ProtectionWarnings`) | 0 | **0** |
| ingerencji służbowych | 0 | **4492** |

To nie jest granica bez skutku. To ochrona hamująca skład, który nie łamie niczego,
przez **4492 kroki, czyli 37,4 s** jednego przejazdu — i cały zestaw 376 testów tego
nie zauważa.

Drugie znalezisko z tej samej sondy, które nie jest mutacją, tylko własnością kodu:
**ingerencja i ostrzeżenie porównują tę samą parę liczb dwoma różnymi operatorami.**
Gałąź decyzyjna to `speedMps > permitted` (wiersz 335), a flaga `Overspeed` to
`speedMps > permitted && speedMps > StandstillSpeedMps` (wiersz 358). Po mutacji
wychodzi stan, którego kontrakt klasy nie przewiduje: **4492 ingerencje przy zerze
ostrzeżeń**, choć opis klasy mówi „ostrzeżenie, potem hamulec służbowy". Nic nie pilnuje,
żeby te dwa porównania pozostały tym samym porównaniem.

**Brakujący test.** W `LineCoreTests` (albo w nieistniejącym `TrainProtectionTests`):
przejazd z `LineRunSettings.SpeedLimitMps` ustawionym **dokładnie** na
`plan.PermittedSpeedMps` ma dać `ServiceInterventions == 0` i `ProtectionWarnings == 0`.
Istniejące testy jadą 70 km/h (pod limitem 72) i 74/76/80 km/h (nad nim) — **granicy
72,00 km/h nie dotyka żaden**. Drugi test, tańszy: `ServiceInterventions > 0` ma
implikować `ProtectionWarnings > 0`.

#### RD-04 · `RouteDispatcher.Dispatch` · `steps - last` → `steps + last`

Dławik żądań tras, czyli jedyna rzecz, która trzyma strumień zdarzeń przy życiu — opis
klasy podaje zmierzone 3050 odmów przy odstępie sekundy wobec 366 000 przy pytaniu co krok.

Mutacja przechodzi, bo test `AsksAtMostOncePerIntervalAndTheIntervalIsMeasuredInSteps`
zaczyna od kroku **zero**. Pierwsze żądanie zapisuje `last = 0`, a dla `last == 0`
`steps - last` i `steps + last` są tą samą liczbą. Test kończy się na drugim żądaniu
(krok 120) i dalej nie idzie.

Od trzeciego żądania różnica jest zasadnicza. Po żądaniu na kroku 120 mamy `last = 120`;
w kroku 121 oryginał liczy `121 - 120 = 1 < 120` i **milczy**, a mutant liczy
`121 + 120 = 241`, co nie jest mniejsze od 120, więc **pyta**. I pyta tak co krok, do
końca przebiegu. Dławik przestaje istnieć dokładnie po drugim żądaniu.

**Brakujący test.** Rozszerzyć istniejący o **trzecie** żądanie: po odmowie na kroku 120
dyspozytor ma milczeć przez kroki 121–239 (`Refused` nadal 2) i odezwać się dopiero na
kroku 240. Jedna dodatkowa pętla w teście, który już jest.

#### RD-06 · `RouteDispatcher.DefaultRequestIntervalSteps` · `FixedStep.SimulationHertz` → `1L`

Ta sama dziura od drugiej strony: domyślny odstęp to udokumentowana **jedna sekunda
symulacji**, a jego wartości nie pilnuje nic. Po mutacji domyślny dyspozytor pyta co krok
— 120 razy na sekundę — i 376 testów przechodzi. Test
`AsksAtMostOncePerIntervalAndTheIntervalIsMeasuredInSteps` podaje odstęp jawnie (120L),
a `DoesNothingPastTheLastPlatform` bierze domyślny, ale nie mierzy nim niczego.

**Brakujący test.** `Assert.AreEqual(FixedStep.SimulationHertz, RouteDispatcher.DefaultRequestIntervalSteps)`
to minimum; lepszy jest test zachowania — dyspozytor zbudowany **bez** podania odstępu
ma w 240 krokach zapytać dokładnie dwa razy.

### 4.2 ŚREDNIE — strażniki, które nie wpuszczają bzdury do modelu

Inna klasa niż 4.1: te mutacje nie zmieniają jazdy ani jednego składu na żadnym
istniejącym scenariuszu. Zmieniają to, **co model w ogóle przyjmie na wejściu**.

#### TP-12 · konstruktor `TrainProtection` · `||` → `&&`

```csharp
if (!double.IsFinite(emergencyBrakeMps2) && emergencyBrakeMps2 < serviceBrakeMps2)
```

Po mutacji strażnik nie odrzuca **niczego**. Wartość skończona daje `!IsFinite == false`
i całe `&&` gaśnie, więc hamulec awaryjny słabszy od służbowego przechodzi; `NaN`
i `+∞` przechodzą, bo `NaN < x` i `∞ < x` są fałszem. Zdanie z dokumentacji klasy
„hamulec awaryjny nie może być słabszy od służbowego" przestaje być prawdą, a nic tego
nie zauważa.

**Brakujący test.** Konstruktor czteroargumentowy ma rzucić `ArgumentOutOfRangeException`
dla `emergencyBrakeMps2` równego `1.0` przy `serviceBrakeMps2 = 1.2`, dla `double.NaN`
i dla `double.PositiveInfinity`. Test bliźniaczy dla `serviceBrakeMps2` już istnieje
w innych klasach — tutaj po prostu nie ma go wcale.

#### FB-07 · `FixedBlockSystem.RegisterTrain` · `lengthM <= 0.0` → `< 0.0`

Skład o długości **zero** wjeżdża na plan. Taki skład ma tył w tym samym punkcie co czoło,
więc `Overlaps(rear, front)` zachowuje się inaczej niż dla każdego prawdziwego składu,
a `ComputeAuthority` cofa indeks bloku po zajętości, której nie ma. To nie jest sytuacja
ruchowa, tylko błąd scenariusza — i klasa deklaruje, że go odrzuca.

**Brakujący test.** `RegisterTrain("A", 0.0, 0.0)` ma rzucić `ArgumentOutOfRangeException`.
Istniejące testy podają wyłącznie `TrainLengthM = 94.0`.

### 4.3 NIEGROŹNE — granice na dokładnej równości `double`

Pięć mutacji różni się od oryginału **tylko wtedy, gdy dwie liczby zmiennoprzecinkowe są
równe co do bitu**:

| id | miejsce | różni się wyłącznie przy |
|---|---|---|
| TP-05 | bisekcja `PermittedSpeedMps`, `>` → `>=` | `BrakingDistanceM(mid) == authorityDistanceM` |
| TP-11 | `DoorRelease`, `>` → `>=` | `speedMps == 1e-6` |
| LD-10 | próg wyzwolenia hamowania, `<` → `<=` | `need.DecelerationMps2 == _trigger` |
| FB-05 | `while (index > 0 …)` → `>= 0` | blok 0 nie pokrywa się ze składem (wtedy `Blocks[-1]`) |
| LC-02 | turnback `<` → `<=` | zawsze — nawrót o **jeden krok** (1/120 s) dłuższy |

LC-02 jest tu z innego powodu niż pozostałe: nie jest granicą nieosiągalną, tylko
przesunięciem o jeden krok, którego test nie łapie, bo jest **jednostronny** —
`Assert.IsTrue(przerwa >= line.TurnbackSteps)`. Zabiłby ją drugi warunek, np.
`Assert.IsTrue(przerwa <= line.TurnbackSteps + 2)`. Skutek jest realny, ale wynosi
8,3 ms na nawrót.

## 5. Zastrzeżenie do sekcji 4.3, i nie jest ono formalnością

Napisanie „granica na równości `double` jest praktycznie nieosiągalna" byłoby dokładnie
tym błędem, który **ten sam przebieg właśnie obalił**. TP-08 jest granicą na dokładnej
równości `double` — i okazała się osiągalna **4492 razy w jednym przejeździe**, bo
`TrainController` przypisuje prędkość limitowi zdaniem `speed = speedLimitMps`, a nie
zbliża się do niego asymptotycznie. Wszędzie, gdzie w tym rdzeniu stoi przypisanie
albo `Math.Clamp`, równość bitowa jest normalnym stanem, a nie zdarzeniem miary zero.

Dlatego sekcja 4.3 mówi „**nie zmierzyłem osiągalności**", a nie „są nieosiągalne".
Pięć pozycji z 4.3 czeka na taki sam pomiar, jaki dostała TP-08 — i dopiero ten pomiar
rozstrzygnie, czy to mutanty równoważne, czy druga TP-08.

## 6. Czego ten przegląd NIE objął

- **Nie naprawiono niczego.** Zadanie było pomiarem; każda ocalała mutacja jest opisana
  tak, żeby dało się z niej zrobić osobne zadanie w formacie z sekcji 6 `CLAUDE.md`.
  Testów nie dopisano — dopisanie testu jest zmianą w kodzie i należy do tamtych zadań.
- **Nie mutowano konstruktorów `LineCore`, `Replay`, `StateDigest`, `ToString`
  ani ścieżek serializacji planu.** 45 mutacji rozłożonych po pięciu plikach to próbka
  celowana w logikę decyzyjną, nie sweep wyczerpujący. Pokrycie 77,8 % dotyczy **tej
  próbki**, a nie tych plików.
- **Nie mutowano testów.** Wyrocznią jest zestaw testów, kodem pod testem — `src/Sim/`.
- **Nie wyliczono osiągalności granic z sekcji 4.3.** Powód w sekcji 5.

## 7. Zauważone przy okazji, nie tknięte

- **Nie ma `tests/Sim.Tests/TrainProtectionTests.cs`.** Klasa o najgorszym wyniku
  w tym przeglądzie (8/12) jest jedyną z piątki bez własnego pliku testów. Trzy z jej
  czterech ocalałych to rzeczy, które test jednostkowy złapałby w trzech wierszach.
- **`Overspeed` i gałąź ingerencji porównują tę samą parę liczb dwoma operatorami**
  (`TrainProtection.cs`, wiersze 335 i 358). Dziś dają zgodny wynik, ale nic tego nie
  wymusza — sonda z 4.1 pokazała stan „4492 ingerencje, 0 ostrzeżeń".
- **Testy `RouteDispatcherTests` są jedyną grupą w tym zestawie z nazwami po angielsku.**
  Reszta rdzenia nazywa testy po polsku. Nie zmieniam — to konwencja, nie usterka.

## 8. Jak to powtórzyć

```bash
git checkout d495051
export PATH=/root/.dotnet:$PATH DOTNET_ROOT=/root/.dotnet
dotnet test tests/Sim.Tests            # 376/376 — punkt odniesienia
```

Dla każdej pozycji z aneksu: podmienić w podanym pliku tekst „przed" na „po"
(z kontrolą `count == 1`), uruchomić `dotnet test tests/Sim.Tests`, przywrócić plik
przez `git checkout -- <plik>`. Przebieg jednej mutacji to ~20 s, całości ~16 min.

## Aneks — pełna lista 45 mutacji

| id | plik | mutacja | werdykt |
|---|---|---|---|
| TP-01 | `TrainProtection` | DemandExceedsServiceBrake: > na >= (żądanie równe pełnemu służbowemu uznane za przekroczenie) | zabita |
| TP-02 | `TrainProtection` | Apply/ServiceIntervention: Math.Max na Math.Min — ochrona ODPUSZCZA hamulec maszynisty | zabita |
| TP-03 | `TrainProtection` | Apply/EmergencyIntervention: pełny hamulec 1.0 na 0.5 | zabita |
| TP-04 | `TrainProtection` | próg postoju 1e-6 na 1e-1 m/s | zabita |
| TP-05 | `TrainProtection` | bisekcja prędkości dopuszczalnej: > na >= | **OCALAŁA** |
| TP-06 | `TrainProtection` | kroki bisekcji 64 na 4 — prędkość dopuszczalna grubo zaniżona | zabita |
| TP-07 | `TrainProtection` | Supervise: authority wyczerpane <= 0 na < 0 | zabita |
| TP-08 | `TrainProtection` | Supervise: przekroczenie prędkości > na >= | **OCALAŁA** |
| TP-09 | `TrainProtection` | Supervise: && na || w wyborze służbowa/awaryjna | zabita |
| TP-10 | `TrainProtection` | Supervise: flaga Overspeed && na || | zabita |
| TP-11 | `TrainProtection` | DoorRelease: warunek ruchu > na >= | **OCALAŁA** |
| TP-12 | `TrainProtection` | konstruktor: || na && w kontroli hamulca awaryjnego | **OCALAŁA** |
| RD-01 | `RouteDispatcher` | konstruktor: odstęp <= 0 na < 0 (zero przestaje być odmową) | zabita |
| RD-02 | `RouteDispatcher` | Dispatch: || na && — dyspozytor rusza także przy planie bez tras | zabita |
| RD-03 | `RouteDispatcher` | Dispatch: dławik żądań < na <= | zabita |
| RD-04 | `RouteDispatcher` | Dispatch: odstęp liczony steps + last zamiast steps - last | **OCALAŁA** |
| RD-05 | `RouteDispatcher` | Dispatch: licznik zaryglowanych tras w dół | zabita |
| RD-06 | `RouteDispatcher` | domyślny odstęp żądań z 1 s na 1 krok | **OCALAŁA** |
| FB-01 | `FixedBlockSystem` | MoveTrain: strażnik cofania - eps na + eps | zabita |
| FB-02 | `FixedBlockSystem` | MoveTrain: próg AuthorityViolation + eps na - eps | zabita |
| FB-03 | `FixedBlockSystem` | ComputeAuthority: Math.Max na Math.Min przy końcu autorytetu | zabita |
| FB-04 | `FixedBlockSystem` | ComputeAuthority: margines autorytetu odejmowany na dodawany | zabita |
| FB-05 | `FixedBlockSystem` | ComputeAuthority: cofanie do bloku zajętego > 0 na >= 0 | **OCALAŁA** |
| FB-06 | `FixedBlockSystem` | ReleaseCompletedRoute: zwolnienie na StartM bloku docelowego zamienione na EndM | zabita |
| FB-07 | `FixedBlockSystem` | RegisterTrain: długość składu <= 0 na < 0 | **OCALAŁA** |
| FB-08 | `FixedBlockSystem` | tolerancja chainage 1e-9 na 1e-1 m | zabita |
| LC-01 | `LineCore` | Step/wyjazdy: krok wyjazdu > na >= (skład rusza o krok później) | zabita |
| LC-02 | `LineCore` | turnback: czas nawrotu < na <= | **OCALAŁA** |
| LC-03 | `LineCore` | Step/faza 4: turnback włączony przy > 0 na >= 0 (działa też przy wyłączonym) | zabita |
| LC-04 | `LineCore` | Add: wyjazd w przeszłości < na <= | zabita |
| LC-05 | `LineCore` | Step: maksimum żądania hamulca liczone jako minimum | zabita |
| LC-06 | `LineCore` | Finished: linia bez składów uznana za skończoną | zabita |
| LC-07 | `LineCore` | EntryIsClear: warunek zajętości peronu odwrócony | zabita |
| LC-08 | `LineCore` | Run: bezpiecznik pętli < na <= (jeden krok ponad budżet) | zabita |
| LC-09 | `LineCore` | Step: licznik ostrzeżeń ochrony w dół | zabita |
| LD-01 | `LineDrive` | Step: cel hamowania — bliższy z dwóch zamieniony na dalszy | zabita |
| LD-02 | `LineDrive` | Step: zwolnienie zatrzasku hamowania + eps na - eps | zabita |
| LD-03 | `LineDrive` | Step: zatrzymanie przed autorytetem — pierwsze && na || | zabita |
| LD-04 | `LineDrive` | Step: zatrzask hamowania zakładany także przy zerowym hamulcu | zabita |
| LD-05 | `LineDrive` | Step: okno zatrzymania na stacji - na + | zabita |
| LD-06 | `LineDrive` | Step: prędkość szczytowa liczona jako minimum | zabita |
| LD-07 | `LineDrive` | konstruktor: próg wyzwolenia hamowania mnożenie na dzielenie | zabita |
| LD-08 | `LineDrive` | Command: kinematyka v²/2d na v²/4d | zabita |
| LD-09 | `LineDrive` | Command: odjęcie oporów ruchu zamienione na dodanie | zabita |
| LD-10 | `LineDrive` | Command: próg wyzwolenia hamowania < na <= | **OCALAŁA** |

**Kontrole negatywne poza pulą** (sekcja 2): NK-01 `if (false)` → `error CS0162`;
NK-02 zepsuty `cref` w dokumentacji XML → `error CS1574`.
