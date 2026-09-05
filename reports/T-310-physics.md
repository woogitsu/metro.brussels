# T-310 — rdzeń fizyki M7

**Zmierzone na commicie:** `614bfeb` · **data:** 2026-09-01

Pierwszy kod w `src/`. Biblioteka `MetroBxl.Sim` (net8.0) odtwarza model projektowy
z `docs/02-simulation.md` i `tools/physics/reference.py`: trakcję, opory ruchu,
całkowanie ruchu krokiem stałym, bilans energii i profil prędkości. Hamowanie służbowe
jest w zakresie **wyłącznie** jako przypadek parytetu z referencją.

Zakres i granice: `docs/TASKS.md`, T-310. Ground truth pojazdu: `data/vehicle/m7-spec.json`.

---

## 1. Co powstało

```
MetroBxl.sln
src/Sim/Sim.csproj                     biblioteka, zero PackageReference
src/Sim/Physics/Units.cs               g, km/h ↔ m/s
src/Sim/Physics/FixedStep.cs           krok stały 1/120 s, czas = kroki × dt
src/Sim/Physics/ParameterStatus.cs     spec / observed / est / design_model
src/Sim/Physics/VehicleRegistry.cs     m7-spec.json jako zasób osadzony
src/Sim/Physics/DesignParameter.cs     jeden wpis katalogu założeń
src/Sim/Physics/VehicleModel.cs        parametry M7, właściwości Design* + katalog
src/Sim/Physics/RunConditions.cs       masa, pochylenie, przyczepność, otoczenie toru
src/Sim/Physics/DavisResistance.cs     r = a + b·v + c_coef·c·v²
src/Sim/Physics/TractionModel.cs       F0 → stała moc → limit przyczepności
src/Sim/Physics/TrainState.cs          stan ruchu i rozbicie sił kroku
src/Sim/Physics/TrainDynamics.cs       jeden krok całkowania
src/Sim/Physics/AccelerationRun.cs     rozruch do prędkości docelowej + energia
src/Sim/Physics/ServiceBrakingRun.cs   hamowanie kinematyczne z ograniczeniem zrywu
src/Sim/Physics/EnergyAccount.cs       bilans energii na obwodzie kół
src/Sim/Physics/SpeedProfile.cs        profil prędkości, próbkowanie co N kroków
src/Sim/Physics/RunResult.cs           wynik przebiegu
tests/Sim.Tests/                       77 testów, MSTest
.github/workflows/sim-tests.yml        CI: setup-dotnet + build + test
```

---

## 2. Parytet z referencją

`python3 tools/physics/reference.py` i `dotnet test` na tych samych czterech przypadkach,
przy `dt = 1/120 s`:

| przypadek | obciążenie | t ref [s] | t rdzeń [s] | s ref [m] | s rdzeń [m] | kroki | Δt | Δs |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `accel_0_80` | AW0 | 25,2 | 25,2 | 337,5 | 337,5 | 3023 | 7,887·10⁻¹³ s | **0** |
| `accel_0_80` | AW2 | 33,3 | 33,3 | 447,9 | 447,9 | 3998 | 1,243·10⁻¹² s | **0** |
| `brake_service_80_0` | AW0 | 20,9 | 20,9 | 240,5 | 240,5 | 2512 | 5,471·10⁻¹³ s | **0** |
| `brake_service_80_0` | AW2 | 20,9 | 20,9 | 240,5 | 240,5 | 2512 | 5,471·10⁻¹³ s | **0** |

Poza tabelą sprawdzone są jeszcze: hamowanie awaryjne 80→0, rozruch AW2 na +3% i −3%,
rozruch AW0 na mokrej szynie, opory Davisa w tunelu i na powierzchni oraz limity
przyczepnościowe — wszystkie z tymi samymi liczbami co referencja.

### Dlaczego takie tolerancje

- **Droga: zero.** Test `Droga_zgadza_sie_z_referencja_co_do_bitu` porównuje
  `BitConverter.DoubleToInt64Bits`. Zgadza się co do bitu, bo kolejność działań
  zmiennoprzecinkowych jest przeniesiona jeden do jednego — `1.5 + 0.006*v + 0.00035*c*v*v`,
  `r*(m/1000.0)*g`, `mu*m*frac*g`, `min(target, v + a*dt)`, `s += v*dt` po nowej prędkości.
  Napisane inaczej (np. mnożenie przez `1/3.6` zamiast dzielenia przez `3.6`) rozjeżdża
  się w ostatnim bicie mantysy i ten test tego nie przepuszcza.
- **Liczba kroków: dokładnie.** To jest właściwe kryterium parytetu — identyczna liczba
  kroków oznacza tę samą trajektorię krok po kroku, a nie tylko ten sam koniec.
- **Czas: 1 ns**, przy zmierzonym rozjeździe 7,9·10⁻¹³ s. **To jedyna świadoma różnica
  wobec referencji** i wynika z decyzji, nie z niedokładności: referencja sumuje
  `t += dt`, rdzeń liczy `kroki × dt`. Suma przyrostów dryfuje z długością przebiegu
  (po 3024 krokach jest o 7,9·10⁻¹³ s *mniejsza* niż wartość dokładna), iloczyn nie
  dryfuje nigdy. `docs/01-architecture.md` wymaga determinizmu, a czas, który zależy od
  długości przebiegu, jest dokładnie tym, czego determinizm nie znosi.

Skutek uboczny tej różnicy jest jeden i dotyczy tylko bezpiecznika pętli: referencja
przy limicie 300 s wykona o jeden krok więcej niż rdzeń, bo jej zsumowane `t` po 36 000
krokach jest jeszcze minimalnie mniejsze od 300. Żaden przypadek parytetu nie dochodzi
do tego limitu; różnica ujawni się dopiero w przebiegu, który utknął.

---

## 3. Decyzje projektowe

### 3.1 `.sln` czy same `.csproj` — jest `.sln`

`MetroBxl.sln` w katalogu głównym. Powód: bez pliku solucji `dotnet build` uruchomiony
w katalogu repo kończy się błędem MSBuild o braku projektu, a to jest pierwsze polecenie,
które ktoś wpisze. Solucja jest też jedynym miejscem, w którym widać komplet projektów
repo. Koszt — GUID-y w diffie — jest jednorazowy przy dwóch projektach.
`dotnet test tests/Sim.Tests` z `CLAUDE.md` §5 działa niezależnie od solucji.

### 3.2 Parametry: zasób osadzony, nie odczyt pliku i nie wklejone liczby

`data/vehicle/m7-spec.json` wchodzi do assembly jako `EmbeddedResource` (`LogicalName`
`MetroBxl.Sim.Data.m7-spec.json`) i jest parsowany przy pierwszym użyciu.

- **Nie wklejone liczby**, bo kopia w kodzie rozjeżdża się z rejestrem po cichu.
- **Nie odczyt z `data/` w runtime**, bo rdzeń ma działać w Godocie bez katalogu `data/`
  na dysku, a `docs/01-architecture.md` nie przewiduje zależności rdzenia od układu repo.
- Osadzenie łączy oba warunki: w repo jest jedna kopia pliku, w runtime zero plików.
  Test `Osadzony_rejestr_jest_identyczny_z_plikiem_w_data` porównuje treść zasobu z
  plikiem na dysku, więc zasób nie może zestarzeć się niezauważony.

Parser używa `System.Text.Json` z shared framework — to nie jest pakiet NuGet.
`src/Sim/Sim.csproj` nie ma ani jednego `PackageReference` i pilnuje tego osobny krok CI.

### 3.3 `design_model` jest widoczne w nazwie, nie w komentarzu

Konwencja przeniesiona z `tools/blender/m7_layout.py`: wartość ze źródła pierwotnego ma
nazwę zwykłą (`EmptyMassKg`, `InstalledPowerW`), każde założenie projektowe ma przedrostek
`Design` (`DesignStartupForceN`, `DesignAdhesionWet`) i wpis w `VehicleModel.DesignAssumptions`
— odpowiedniku `DESIGN_ASSUMPTIONS`. Ładowanie parametru wymaga podania oczekiwanego
statusu (`RequireValue(path, ParameterStatus.Spec)`), więc awans `design_model` na `spec`
bez źródła nie przechodzi cicho, tylko wywraca konstrukcję modelu.

Pilnują tego cztery testy, w obie strony:

- każda właściwość `Design*` ma wpis w katalogu z tą samą wartością i z uzasadnieniem,
- katalog nie wymienia właściwości, których nie ma,
- każdy wpis katalogu wskazuje parametr o statusie `design_model` w rejestrze,
- każdy parametr `design_model` z rejestru (jest ich 18) jest zadeklarowany w modelu.

To jest po stronie rdzenia ten sam mechanizm, co `tools/tests/test_dimension_audit.py`
po stronie geometrii: dopisanie parametru bez deklaracji pochodzenia wywraca testy.

### 3.4 Determinizm

- Czas wynika z licznika kroków (`long`), nie z sumowania przyrostów.
- Zero `DateTime`, zero `Random`, zero `Environment`. Rdzeń nie ma źródła entropii.
- Rejestr wystawia parametry w porządku ordinalnym, a nie w kolejności iteracji po
  słowniku; katalog założeń ma kolejność deklaracji.
- Wszystkie formatowania idą przez `CultureInfo.InvariantCulture` — przecinek dziesiętny
  w kulturze systemu nie zmienia ani wyniku, ani treści komunikatu błędu.
- Testy: dwa przebiegi tego samego scenariusza porównane bit w bit (razem z profilem i
  energią), przebieg policzony w ośmiu wątkach naraz, przebieg po wykonaniu innych
  przebiegów, próbkowanie profilu nie zmieniające wyniku.

### 3.5 Framework testowy: MSTest, trzy pakiety

`Microsoft.NET.Test.Sdk`, `MSTest.TestAdapter`, `MSTest.TestFramework` — wszystkie
Microsoftowe, wersje dokładnie te, które szablon `dotnet new mstest` przypisuje
zainstalowanemu SDK 8.0.130. `dotnet test` z `CLAUDE.md` §5 wymaga runnera i adaptera;
mniej niż trzy pakiety się nie da bez zmiany polecenia weryfikacji. xUnit ani NUnit
dokładałyby pakiety spoza platformy bez żadnej korzyści dla testów, które sprowadzają
się do porównywania liczb. `coverlet.collector` z szablonu został usunięty — nie mierzymy
pokrycia. Rdzeń zostaje bezzależnościowy.

### 3.6 Bilans energii jako druga droga do wyniku

`docs/06-worked-example.md`: dobre zadanie kończy się dwiema niezależnymi drogami do tej
samej liczby. Drugą drogą jest tu bilans energii przebiegu — praca trakcji musi się
równać sumie energii kinetycznej, pracy oporów, pracy na pochyleniu, członu dyskretyzacji
i pracy odrzuconej przez obcięcia modelu.

Pierwsze podejście nie domykało się o **1,79·10⁻⁴** pracy trakcji (11,25 kJ). To nie był
błąd zaokrągleń, tylko konkretny fizyczny ubytek: na **ostatnim kroku** rozruchu prędkość
jest obcinana do docelowej (`min(target, v + a·dt)`), więc model wkłada pełną siłę, a
przyjmuje mniejszy przyrost prędkości. Po wyodrębnieniu tego członu (`ClampedWorkJ`)
bilans domyka się do **4,4·10⁻¹⁶**, czyli do precyzji `double`:

```
AW2 0→80 poziom: E_trakcji = 17.4535 kWh, opory = 3.620 MJ, pochylenie = 0.000 MJ,
E_kin = 59.184 MJ, dyskretyzacja = 16902.9 J, obcięcie = 11250.0 J, reszta = 2.788E-008 J
niedomknięcie względne = 4.438E-016
```

Wniosek, który z tego zostaje w kodzie: obcięcie do prędkości docelowej jest artefaktem
modelu, nie fizyką — prawdziwy maszynista zdejmuje nastawnik przed osiągnięciem prędkości.
`EnergyAccount` nazywa ten człon zamiast go rozmazywać w tolerancji.

Energia jest liczona **na obwodzie kół**. Sprawność przetwornic, silników i przekładni,
pobór potrzeb własnych i sprawność odzysku nie mają w źródłach STIB żadnych wartości —
karta M7 potwierdza sam fakt odzysku energii hamowania i nic ponadto.

---

## 4. Parametry `design_model` w rdzeniu

Pełna lista, każda z ścieżką w rejestrze. To są **decyzje symulatora**, nie fakty
o brukselskim metrze; wolno je zmienić bez pytania kogokolwiek o zgodę, ale nie wolno
o nich powiedzieć „takie jest M7" (`docs/21-measured-vs-assumed.md`, §6).

| właściwość | wartość | wpis w rejestrze | dlaczego taka |
|---|---:|---|---|
| `DesignMaxSpeedKmh` | 80 km/h | `parameters.max_speed_kmh` | audyt T-904 nie znalazł źródła pierwotnego na Vmax M7 |
| `DesignPoweredMassFraction` | 4/6 | `parameters.powered_mass_fraction` | historyczne; używane wyłącznie przez limit przyczepności |
| `DesignPassengerMassKg` | 70 kg | `reference_model.passenger_mass_kg` | brak publicznej definicji obciążenia |
| `DesignAw2Passengers` | 742 | `reference_model.aw2_model_passengers` | pojemność manualna użyta jako obłożenie modelu |
| `DesignAw2MassKg` | 221 940 kg | `reference_model.aw2_model_mass_kg` | 170 t + 742 × 70 kg; brak publicznej masy AW2 |
| `DesignStartupForceN` | 248 900 N | `reference_model.startup_force_n` | kalibracja modelu; charakterystyka siła–prędkość nie jest publiczna |
| `DesignForcePowerTransitionSpeedMps` | 8,678184 m/s | `reference_model.force_power_transition_speed_kmh` | pochodna 2160 kW / 248,9 kN = 31,24 km/h |
| `DesignServiceBrakeMps2` | 1,10 m/s² | `reference_model.service_brake_mps2` | brak źródła pierwotnego |
| `DesignEmergencyBrakeMps2` | 1,30 m/s² | `reference_model.emergency_brake_mps2` | brak źródła pierwotnego |
| `DesignJerkMps3` | 0,75 m/s³ | `reference_model.jerk_mps3` | brak źródła pierwotnego |
| `DesignEffectiveMassFactor` | 1,08 | `reference_model.effective_mass_factor` | brak danych o wirnikach, przekładniach i kołach |
| `DesignAdhesionDry` | 0,25 | `reference_model.adhesion_dry` | brak danych adhezyjnych STIB |
| `DesignAdhesionWet` | 0,13 | `reference_model.adhesion_wet` | brak danych adhezyjnych STIB |
| `DesignDavisA` | 1,5 kgf/t | `reference_model.davis_a` | współczynnik do kalibracji |
| `DesignDavisB` | 0,006 | `reference_model.davis_b` | współczynnik do kalibracji |
| `DesignDavisC` | 0,00035 | `reference_model.davis_c` | współczynnik do kalibracji |
| `DesignTunnelResistanceMultiplier` | 1,40 | `reference_model.tunnel_resistance_multiplier` | brak pomiaru dla przekroju tuneli STIB |
| `DesignSurfaceResistanceMultiplier` | 1,00 | `reference_model.surface_resistance_multiplier` | wartość odniesienia dla mnożnika tunelowego |

Ze źródła pierwotnego pochodzą w rdzeniu dokładnie dwie liczby: `EmptyMassKg` = 170 000 kg
(STIB podaje „około") i `InstalledPowerW` = 2 160 000 W (16 × 135 kW).

Bezpiecznik pętli — 300 s dla rozruchu i 120 s dla hamowania — nie jest parametrem
pojazdu i nie ma wpisu w rejestrze. To wartość z referencji, chroniąca przed
nieskończonym przebiegiem.

---

## 5. Dwie rzeczy, które wyglądają na błąd referencji i nie są

Obie zostały odtworzone wiernie i obie są opisane w kodzie w miejscu, w którym działają.

1. **Masa efektywna tylko w mianowniku przyspieszenia.** `a = F_wyp / (m · 1,08)`,
   ale opory Davisa i składowa styczna ciężaru liczą się od masy rzeczywistej `m`.
   Współczynnik mas wirujących opisuje bezwładność wirujących części napędu, a nie ich
   ciężar: masa wirująca nie zwiększa nacisku na szynę ani składowej stycznej na
   pochyleniu. Test `Masa_efektywna_wchodzi_tylko_do_przyspieszenia` przypina to na stałe.

2. **Hamowanie nie zależy od masy.** `sim_brake` w referencji nie przyjmuje masy w ogóle
   i dlatego AW0 i AW2 dają identyczne 20,9 s i 240,5 m. Model jest czysto kinematyczny:
   zadane opóźnienie z ograniczeniem zrywu, bez bilansu sił. Rdzeń zachowuje to
   uproszczenie i **nie przyjmuje masy w sygnaturze** `ServiceBrakingRun.ToStop` —
   parametr po cichu ignorowany kłamie gorzej niż jego brak. Oba wiersze tabeli parytetu
   powstają z jednego wywołania.

---

## 6. Weryfikacja — rzeczywiste wyjście

### `python3 tools/physics/reference.py`

```
moc zainstalowana trakcji (spec) = 2160 kW
prędkość przejścia modelu F0→P = 31.24 km/h (derived design_model)
{'case': 'accel_0_80', 'load': 'AW0', 'time_s': 25.2, 'distance_m': 337.5}
{'case': 'accel_0_80', 'load': 'AW2', 'time_s': 33.3, 'distance_m': 447.9}
{'case': 'brake_service_80_0', 'load': 'AW0', 'time_s': 20.9, 'distance_m': 240.5}
{'case': 'brake_service_80_0', 'load': 'AW2', 'time_s': 20.9, 'distance_m': 240.5}
```

### `dotnet build MetroBxl.sln --configuration Release`

```
  Sim -> src/Sim/bin/Release/net8.0/MetroBxl.Sim.dll
  Sim.Tests -> tests/Sim.Tests/bin/Release/net8.0/MetroBxl.Sim.Tests.dll

Build succeeded.
    0 Warning(s)
    0 Error(s)
```

### `dotnet test tests/Sim.Tests`

```
Passed!  - Failed:     0, Passed:    77, Skipped:     0, Total:    77, Duration: 258 ms - MetroBxl.Sim.Tests.dll (net8.0)
```

Tabela parytetu wypisana przez test `Tabela_parytetu_do_raportu`:

```
| accel_0_80         | AW0 | 25.2 | 25.2 | 337.5 | 337.5 | 3023 | dt=7.887E-013 s | ds=0.000E+000 m |
| accel_0_80         | AW2 | 33.3 | 33.3 | 447.9 | 447.9 | 3998 | dt=1.243E-012 s | ds=0.000E+000 m |
| brake_service_80_0 | AW0 | 20.9 | 20.9 | 240.5 | 240.5 | 2512 | dt=5.471E-013 s | ds=0.000E+000 m |
| brake_service_80_0 | AW2 | 20.9 | 20.9 | 240.5 | 240.5 | 2512 | dt=5.471E-013 s | ds=0.000E+000 m |
```

### `python3 tools/tests/test_all.py`

```
  318/318 przeszło
```

### `bash doctor.sh`

```
METRO BXL — kontrola środowiska
--------------------------------------------------
Wymagane dla bazy:
  ok    python3
  ok    git

Wymagane dla rdzenia symulacji (T-310 jest zrobione, src/Sim istnieje):
  ok    dotnet SDK

Wymagane dopiero przez konkretne zadania:
  ok    blender w PATH
  ok    blender headless
  WARN  godot w PATH  -> wymagany od T-400

Struktura projektu:
  ok    CLAUDE.md
  ...
  ok    src/Sim
  ok    tests/Sim.Tests

Testy narzędzi:
  ok    318/318 przeszło

Testy rdzenia symulacji:
  ok    77/77 przeszło

--------------------------------------------------
  Baza projektu jest gotowa. Następne zadanie: T-010.
```

### Kontrola negatywna kontroli

`doctor.sh`, który mówi „ok" tylko wtedy, gdy nic nie sprawdza, jest bezużyteczny.
Po podmianie jednej stałej referencyjnej w `tests/Sim.Tests/PythonReference.cs`
(337,478 m → 337,9 m):

```
Testy rdzenia symulacji:
  BLAD  dotnet test nie przechodzi — zobacz /tmp/mbxl_sim_tests.log

--------------------------------------------------
  1 wymaganych pozycji do naprawienia przed pracą.

exit=1
```

Stała została przywrócona; różnica 0,4 m na 337 m to rozjazd rzędu jednego promila
i kontrola go łapie.

### CI (PR #69)

Zmierzone 01.09.2026, gdy joby chodziły jeszcze na maszynie GitHuba — poprzednia
wersja tego śródtytułu brzmiała „CI na `ubuntu-latest`" i przestała być prawdą
02.09.2026, kiedy całe CI zeszło na gołą etykietę `self-hosted` (`CLAUDE.md` §9).
Śródtytuł jest tu przepisany, a nie dopisany obok; liczby przebiegów zostają.

`CLAUDE.md` §9: `queued` nie jest weryfikacją. Stan po zakończonych jobach:

| workflow | run | wynik |
|---|---|---|
| Sim core tests | #1 | **failure** — krok kontrolny „brak `PackageReference`", opis niżej |
| Sim core tests | #2 | success — wszystkie 10 kroków, w tym `dotnet test` |
| Python tool tests | #126 | success |
| Blender smoke | #45 | success |

Blender smoke ma znaczenie osobne: `tools/ci/blender_smoke.sh` uruchamia `bash doctor.sh`
pod `set -euo pipefail`, więc zielony job jest dowodem, że `doctor.sh` z `dotnet`
w sekcji **wymaganej** i z sekcją testów rdzenia przechodzi na czystej maszynie,
a nie tylko na tej, na której pisałem kod. (Zmierzone 01.09.2026 — była to wtedy
maszyna GitHuba; dziś ten sam job chodzi na `self-hosted`.) Pozostałe trzy workflow
(`tunnel-alignment`, `visual-regression`, `m7-shell`) mają filtry ścieżek, których ten
PR nie rusza, więc się nie uruchamiają.

---

## 7. `doctor.sh` i CI

`doctor.sh`: `dotnet` przeniesiony z sekcji opcjonalnej do **wymaganej** — od T-310
rdzeń istnieje i bez SDK nie da się go zbudować ani przetestować. Doszła sekcja
„Testy rdzenia symulacji", będąca odpowiednikiem istniejącej sekcji dla testów Pythona,
oraz trzy pozycje w kontroli struktury: `data/vehicle/m7-spec.json`, `src/Sim`,
`tests/Sim.Tests`. Sekcja testów rdzenia jest pomijana z komunikatem, gdy `dotnet`
nie istnieje, żeby raport nie sypał dwa razy tym samym błędem.

> Poprzednia wersja akapitu niżej opisywała ten workflow jako stojący „na
> `ubuntu-latest` (`CLAUDE.md` §9)". **To już nieprawda i było mylące podwójnie**:
> od 02.09.2026 §9 mówi coś przeciwnego — całe CI chodzi na gołej etykiecie
> `self-hosted` — więc odsyłacz kierował czytelnika do dokumentu, który zaprzecza
> zdaniu, przy którym stał. Nazwa runnera jest tu skreślona, a nie podmieniona na
> dzisiejszą: opis kroków jest pomiarem z 01.09.2026 i nie staje się przez to
> opisem dzisiejszego pliku.

`.github/workflows/sim-tests.yml`, nowy, pięć
kroków po instalacji SDK przez `actions/setup-dotnet@v4`:
restore → build Release (ostrzeżenia w `src/Sim` są błędami) → `dotnet test` → kontrola
braku odwołań do Godota w `src/Sim` → kontrola braku `PackageReference` w rdzeniu →
wypisanie wyjścia referencji Pythona obok, żeby rozjazd parytetu był widoczny w logu.
Pięć istniejących workflow nie zostało tknięte.

**Pierwszy przebieg CI wywalił się na moim własnym kroku kontrolnym** i warto to
odnotować, bo jest to dokładnie ten rodzaj błędu, którego szuka `CLAUDE.md` §5.
Build, testy i kontrola Godota przeszły; kontrola „brak `PackageReference` w rdzeniu"
zgłosiła naruszenie, bo `grep 'PackageReference'` trafił w **komentarz w `Sim.csproj`,
który tę regułę opisuje**. Kontrola wywróciła się na własnym uzasadnieniu. Oba wzorce
zostały zawężone do kodu — element XML `<PackageReference` i dyrektywa `using Godot`
albo kwalifikowany typ `Godot.X` zamiast gołego słowa — i sprawdzone lokalnie w obie
strony: na czystym drzewie nie znajdują nic, a po wstawieniu `using Godot;` do
`src/Sim` i `<PackageReference>` do przykładowego `.csproj` znajdują naruszenie.

---

## 8. Czego świadomie nie zrobiłem

- **T-311 (hamowanie).** Brak udziału hamulca elektrodynamicznego i pneumatycznego, brak
  wpływu masy i przyczepności na hamowanie, brak krzywych bezpieczeństwa i trybu
  awaryjnego jako stanu. `ServiceBrakingRun` jest kinematycznym przypadkiem testowym
  i tyle ma zostać. Bilans energii hamowania i odzysku również należy do T-311 —
  dlatego `RunResult.Energy` jest dla hamowania `null`, a nie zerem.
- **T-312 (drzwi i postój).** Cykl drzwi z `docs/02-simulation.md` (0,5 / 2,0 / 3,0 /
  2,5 / 0,5 s) nie został przeniesiony do kodu, choć liczby są znane. To jest zakres
  T-312, a przeniesienie ich „przy okazji" łamie regułę 10.
- **T-313/T-314 (sygnalizacja).** Zero abstrakcji bloków, aspektów, ATP i CBTC.
- **Nie ruszałem `tools/physics/reference.py`.** Nie znalazłem w niej błędu — dwie
  rzeczy, które wyglądają jak błąd, są opisane w §5 i zostały odtworzone celowo.
- **Nie ruszałem `data/`** (reguła 6). Rejestr M7 jest czytany, nie zmieniany.
- **Nie ruszałem `docs/TASKS.md`.** Odhaczenie T-310 jest zmianą stanu projektu i
  należy do właściciela repo po przejrzeniu PR, tym bardziej że Issue #20 zostaje otwarte.
- **Nie dodałem `Sim/Train`, `Sim/Line`, `Sim/Passengers`** z mapy modułów
  `docs/01-architecture.md`. `docs/TASKS.md` wskazuje jako wyjście T-310 wyłącznie
  `src/Sim/Physics/`, a puste katalogi na zapas są tylko obietnicą.
- **Nie dodałem odczytu profilu trasy ani pochylenia z `data/track/`.** Przebieg dostaje
  jedno stałe pochylenie. Sprzęgnięcie fizyki z osią to T-320, a na `tools/track/**` i
  `data/track/**` trwa równoległa praca.

---

## 9. Zauważone przy okazji, nie tknięte

1. **`docs/02-simulation.md` mówi „przyspieszenie maks. 1,10 m/s²", a model tego nie
   egzekwuje.** Przy F0 = 248,9 kN i AW0 (masa efektywna 183,6 t) przyspieszenie
   startowe wychodzi **1,342 m/s²**, czyli o 22% powyżej deklarowanej wartości
   projektowej (dla AW2 jest to 1,025 m/s², czyli poniżej). Referencja też tego nie
   ogranicza, więc odtworzyłem zachowanie referencji, a nie zdanie z dokumentu.
   Rozstrzygnięcie — czy F0 ma zostać obniżone do ~204,5 kN, czy model ma dostać osobne
   ograniczenie przyspieszenia, czy dokument ma przestać deklarować limit — jest decyzją projektową
   (`CLAUDE.md` §8), a nie zmianą w rdzeniu. Dotyczy tego samego `design_model`, który
   generuje punkt przejścia 31,24 km/h.
2. ~~**`doctor.sh` kończy się zdaniem „Następne zadanie: T-010"**, choć T-010 i cały
   pakiet T-2xx są zrobione. Napis jest zaszyty na stałe i wprowadza w błąd.~~
   **Zamknięte; ten punkt jest przepisany, a nie dopisany obok.** Napis nie jest już
   zaszyty na stałe: `doctor.sh` wyprowadza następne zadanie z `docs/TASKS.md`
   (`grep -E '^### \[ \]'` z odsianiem pozycji `ZABLOKOWANE` i `CZŁOWIEK`), a nad tym
   miejscem stoi komentarz z powodem — „wpisane na sztywno przestaje być prawdą
   pierwszego dnia po zrobieniu tego zadania i wysyła kolejną sesję do roboty, która
   już leży w main". Sprawdzone lekturą `doctor.sh` na `9f4ae98`. Ta sama obserwacja
   stała jeszcze w `reports/T-311-braking.md` §7.4 i `reports/T-400-first-run.md` §8.2
   i tam też jest przepisana — trzy raporty niosły ją niezależnie, bo każdy odsyłał
   do poprzedniego zamiast do kodu.
3. **W repo są dwa sposoby zapisu statusu wartości**: `design_model` w
   `data/vehicle/m7-spec.json` i `design_assumption` w `docs/21-measured-vs-assumed.md`.
   Rdzeń rozumie ten pierwszy, bo taki jest w rejestrze. Ujednolicenie słownika
   ułatwiłoby życie, ale dotyka dokumentów spoza zakresu T-310.
4. **`tools/tests/test_dimension_audit.py` skanuje wyłącznie stałe `DESIGN_*` z modułów
   Pythona**, więc nie widzi właściwości `Design*` z `src/Sim`. Ich audyt zrobiłem po
   stronie testów C# (§3.3), ale są to dwa niezależne mechanizmy pilnujące tej samej
   reguły. Połączenie ich wymagałoby, żeby testy Pythona uruchamiały .NET — nie zrobiłem
   tego, bo `tools/tests/test_all.py` ma z założenia działać bez zależności zewnętrznych.
