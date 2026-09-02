# T-314 — tryby ochrony pociągu i strefa testowa CBTC

Cztery tryby z rejestru R-003, rozstrzyganie który z nich jest historyczny, i zasięg
odcinka testowego CBTC. Ten dokument opisuje, **czego ta warstwa nie robi** — bo to
jest w niej najważniejsze.

Ground truth: [`docs/10-signalling-ground-truth.md`](10-signalling-ground-truth.md),
maszynowo `data/signalling/ground-truth.json`.
Definicja strefy: `data/design/signalling/cbtc-test-2026.json`.
Kod: `src/Sim/Signalling/ProtectionMode.cs`, `src/Sim/Signalling/CbtcTestArea.cs`.
Tryb klasyczny: [`docs/15-classic-signalling.md`](15-classic-signalling.md).

---

## 1. Jednym zdaniem

Warstwa trybów odpowiada na pytanie **„czym sieć jeździła tego dnia"** i odmawia
odpowiedzi tam, gdzie nie ma faktu — nie zawiera ani jednej liczby opisującej działanie
CBTC, bo STIB żadnej nie publikuje.

## 2. Odpowiedź, o którą chodziło w T-314

Kryterium ukończenia brzmiało: *tryb CBTC nie jest aktywny w scenariuszu historycznym
31.08.2026 bez potwierdzenia pełnego uruchomienia STIB*. Odpowiedź jest w danych, nie
w kodzie:

```
cbtc_lines_1_5_full_service  ::  observed  ::  false
historical_default           ::  "classic_2026"
as_of                        ::  2026-08-31
```

`ProtectionModeRegistry.ForHistoricalDate(2026-08-31)` zwraca `classic_2026` dlatego, że
tak mówi rejestr — a nie dlatego, że ktoś to wpisał w C#. Gdyby STIB uruchomił CBTC na
liniach 1 i 5, zmiana jednego pola w ground truth wywraca test
`Tryb_historyczny_powoluje_sie_na_fakt_o_braku_ruchu_pasazerskiego_CBTC` i zmusza do
świadomej zmiany scenariusza. Sprawdzone mutacją: `false → true` daje czerwony.

## 3. Cztery tryby i ich stan

| tryb | stan | historyczny | co niesie |
|---|---|---|---|
| `classic_2026` | `operational_baseline` | **tak** | linie 1/5 bloki stałe, linie 2/6 bloki plus KCV |
| `cbtc_test` | `installation_and_validation` | nie | instalacja Erasme–Stockel ukończona, testy trwają; **nie** ruch pasażerski w skali sieci |
| `cbtc_future` | `future_scenario` | nie | separacja ruchoma, ATS, kontrakt na 35,5 km i 37 stacji |
| `cbtc_mini_future` | `future_scenario` | nie | linie 2/6: lokalizacja plus istniejące KCV |

Rejestr wymusza, że **dokładnie jeden** tryb ma `historical_default`, i że pole
`historical_default` na górze pliku zgadza się z flagą przy trybie. Rozjazd tych dwóch
zapisów jest błędem wczytania, a nie sytuacją, w której rdzeń wybiera jeden po cichu.

## 4. Dwie drogi do trybu — i dlaczego są dwie

```csharp
registry.ForHistoricalDate(date)   // „czym sieć jeździła" — nie da się tym włączyć CBTC
registry.Named("cbtc_future")      // „co by było gdyby" — dowolny tryb
registry.RequireHistorical(m, d)   // strażnik: scenariusz deklaruje, że jest historyczny
```

Rozdzielenie jest celowe. Gdyby wybór trybu szedł jedną ścieżką z parametrem,
przypadkowe włączenie CBTC w przejeździe historycznym byłoby odległe o jedną literówkę.
`Named` istnieje, bo scenariusze przyszłe są potrzebne; `RequireHistorical` jest
miejscem, w którym kod woła „to jest przejazd historyczny" i dostaje wyjątek, gdy tryb
się nie zgadza.

**Poza `as_of` rejestr odmawia.** Ground truth jest zweryfikowany na 31.08.2026.
Dla późniejszej daty `ForHistoricalDate` rzuca wyjątkiem, bo jedyne, co repo ma o roku
2027, to **plany** — `cbtc_jacques_brel_merode_2026_plan` i
`cbtc_herrmann_debroux_plan` — a ground truth sam pisze przy nich: *a plan is not proof
of commissioning*.

## 5. Strefa testowa — co jest faktem, co modelem

**Faktem** jest, że instalacja na odcinku Erasme–Stockel jest ukończona i trwają testy
(`cbtc_test_erasme_stockel`), że sekwencja to najpierw łączność statyczna, potem jazda,
i że testy dynamiczne przy Beekkant ruszyły pod koniec maja 2026
(`cbtc_test_method_and_beekkant`).

**Modelem jest wszystko, co ma wymiar.** `data/design/signalling/cbtc-test-2026.json`
ma status `design_model` w całości i nie dodaje ani jednej liczby, której nie ma
w źródle:

- granice strefy są **nazwami stacji**, nie kilometrażem — kilometraż powstaje dopiero
  przy rzucie na konkretną oś;
- rozpoczęcie testów zostaje **etykietą** (`started_late_may_2026`), nie datą. Źródło
  podaje miesiąc, nie dzień; `DateOnly` wymagałoby wybrania dnia, którego nikt nie
  opublikował. Osobny test sprawdza, że żadna etykieta nie daje się przeczytać jako data;
- `unknown_parameters` wymienia protokół radiowy, dokładność lokalizacji, bufory
  bezpieczeństwa i formaty telegramów — czyli dokładnie to, co ground truth przypisuje
  trybowi `cbtc_test` jako `design_model_required`.

### Przycięcie zasięgu nie jest ukrywane

Odcinek testowy jest opisany stacjami końcowymi całych linii 1 i 5. Osie w repo to
pakiety: pakiet A biegnie z Gare de l'Ouest do Merode, więc **ani Erasme, ani Stockel na
nim nie leży**. Rzut daje wtedy całą oś, ale z dwiema flagami:

```
CbtcTestSpan { AxisId = L1_A, StartM = 0,00, EndM = 6686,74,
               ClippedAtStart = true, ClippedAtEnd = true }
```

(6686,74 m, a nie 6686,35 m z pola `length_m`: `TrackAxis` zagęszcza łamaną krzywą
Catmull-Rom krokiem `DEFAULT_RING_STEP_M` = 5,0 m, więc długość liczona po zagęszczeniu
jest o 0,39 m większa od zadeklarowanej. Test porównuje zasięg z `axis.LengthM`, czyli
z tą samą liczbą, którą widzi reszta rdzenia.)

„Strefa obejmuje całą oś" i „oś kończy się przed granicą strefy" to dwie różne rzeczy
i nie wolno ich zapisać tą samą liczbą. Test
`Zasieg_na_osi_zawierajacej_obie_stacje_nie_jest_przyciety` pilnuje drugiej strony:
gdy obie stacje są na osi, flagi są fałszywe, a granice to ich kilometraż.

## 6. Czego ta warstwa **nie** robi

To jest lista rzeczy, których brak jest świadomy, a nie zapomniany:

- **nie liczy movement authority po CBTC** — separacja ruchoma, bufor ochronny i krzywe
  ATO są w `unknown_parameters`; ochroną nadal steruje `TrainProtection` na planie
  bloków z T-313;
- **nie zna protokołu radiowego ani parametrów baliz** — źródło nie publikuje ani
  formatów telegramów, ani algorytmu pozycjonowania;
- **nie modeluje trybów awaryjnych ani GoA** ponad opublikowany stan;
- **nie implementuje ATS.** `ats_transition` mówi wprost: *ATS is a distinct
  supervision/dispatch layer and must not bypass train protection*. Warstwa trybów nie
  wystawia więc **żadnej** metody, którą dałoby się prowadzić skład — pilnuje tego test
  `Warstwa_trybow_nie_wystawia_zadnej_drogi_omijajacej_ochrone`, sprawdzający przez
  refleksję, że w `ProtectionMode`, `ProtectionModeRegistry` i `CbtcTestArea` nie ma
  składowej o nazwie zawierającej `Authority`, `PermittedSpeed`, `BrakeDemand`
  ani `Supervise`.

Listy `design_model_required` przy trybach CBTC są jedynym miejscem, w którym ta dziura
jest widoczna. Wyczyszczenie ich wyglądałoby jak ukończenie pracy — dlatego osobny test
wymaga, żeby zostały niepuste.

## 7. Weryfikacja

```
dotnet test tests/Sim.Tests   →  Passed: 277, Failed: 0   (przed T-314: 259)
```

Dziesięć kontroli negatywnych, każda wpisana i cofnięta:

| mutacja | wynik |
|---|---|
| `cbtc_lines_1_5_full_service` → `true` | Failed: 1 |
| `cbtc_test` dostaje `historical_default` | Failed: 10 |
| `ForHistoricalDate` zwraca `cbtc_test` | Failed: 2 |
| `RequireHistorical` nic nie robi | Failed: 1 |
| `ForHistoricalDate` przyjmuje datę po `as_of` | Failed: 1 |
| `OnAxis` zawsze melduje brak przycięcia | Failed: 1 |
| loader strefy bez bramki na status | Failed: 1 |
| etapy testów w odwrotnej kolejności | Failed: 1 |
| Beekkant dostaje wymyśloną datę `2026-05-25` | Failed: 1 |
| strefa gubi niewiadome swojego trybu | Failed: 1 |
