# T-400 — pierwszy przejazd (etap 1 z Issue #26)

Pierwsza scena Godota w tym repozytorium. Do tej pory istniały wyłącznie narzędzia,
dane i rdzeń symulacji; nic z tego nie dawało się obejrzeć w ruchu.

Wariant geometrii: **`flat-preview`, nieprodukcyjny** — jak w `reports/L1_A-geometry.md`,
`reports/L1_A-chunks.md` i `reports/L1_A-lod.md`. Oś `data/track/L1_A.json` ma
`vertical.status = "not_modelled"`, cała geometria leży na Z = 0, generator odmawia
wariantu `production` do zamknięcia T-112 (#10).

**To nie jest całe #26** i nie zamyka T-400. Czego nie ma — §7.

---

## 0. Co powstało

```
src/Game/                              projekt Godota 4.3 mono
  project.godot                        krok fizyki silnika 120 Hz, renderer gl_compatibility
  MetroBxl.Game.csproj                 Godot.NET.Sdk 4.3.0, jedna zależność: ../Sim
  Scenes/FirstRun.tscn                 struktura węzłów, zero zapisanej geometrii
  FirstRun.cs                          tryby, pętla klatkowa, kamery, zakończenie
  DesignAssumptions.cs                 wszystkie liczby warstwy silnika bez źródła
  Assets/GlbLoader.cs                  wczytywanie GLB w runtime + materiał neutralny
  Assets/ChunkManifest.cs              odczyt manifestu streamingowego T-210
  World/SceneAxis.cs                   układ danych -> układ Godota, cięciwy członów
  World/TunnelView.cs                  12 chunków pakietu A
  World/TrainView.cs                   11 brył M7 na własnych cięciwach
  Input/DriverInput.cs                 klawiatura -> DriverCommand
  UI/Hud.cs                            prędkość, chainage, przyspieszenie, nastawniki

src/Sim/Line/TrackAxis.cs              oś: Catmull-Rom 1:1 z sweep.py, chainage -> punkt
src/Sim/Train/DriverCommand.cs         nastawnik jazdy i hamulec jako polecenie
src/Sim/Train/DriveState.cs            stan ruchu + opóźnienie hamulca
src/Sim/Train/TrainController.cs       jeden krok prowadzonego składu
src/Sim/Train/DriveScenario.cs         zapisany przejazd, katalog założeń
src/Sim/Train/ScenarioDrive.cs         pętla przejazdu, wspólna dla obu gospodarzy
src/Sim/Train/DriveTelemetry.cs        jeden format wiersza CSV

src/Sim.Runner/                        konsolowy gospodarz rdzenia: drive/compare/axis/parity

tests/Sim.Tests/TrainControllerTests.cs   trakcja częściowa, zryw, brak obcięcia, bilans energii
tests/Sim.Tests/ScenarioDriveTests.cs     determinizm krokowy, bezpiecznik pętli, telemetria
tests/Sim.Tests/TrackAxisTests.cs         przypadki brzegowe osi + kontrola na pakiecie A
.github/workflows/godot-first-run.yml  CI na ubuntu-latest, Godot z GitHub Releases
```

Nic z `build/` ani `renders/` nie jest komitowane (reguła 8). `.gitignore` dostał
sekcję na to, co Godot generuje obok projektu.

---

## 1. Decyzje i uzasadnienia

### 1.1 Projekt Godota leży w `src/Game`, ale **nie jest** w `MetroBxl.sln`

Katalog wskazuje `docs/01-architecture.md` i nie ma powodu wymyślać innego.

Solucja to inna sprawa. `MetroBxl.sln` jest tym, co buduje `sim-tests.yml`
poleceniem `dotnet build MetroBxl.sln`. Wrzucenie tam projektu z `Godot.NET.Sdk`
sprawiłoby, że **CI rdzenia zaczęłoby ściągać silnik** — a reguła 9 z `CLAUDE.md`
mówi, że rdzeń ma się kompilować i testować bez Godota. Solucja została więc
listą projektów bezsilnikowych: doszedł do niej `Sim.Runner`, nie doszedł `Game`.
Pilnuje tego osobny krok nowego workflow, który wywraca się, gdy `MetroBxl.Game`
pojawi się w `.sln`.

### 1.2 Co poszło do `src/Sim` i dlaczego to nie jest druga fizyka

Rdzeń z T-310 umiał policzyć **przebieg** (rozruch do prędkości, hamowanie do
zatrzymania), ale nie umiał wykonać **kroku pod dyktando maszynisty**:
`TrainDynamics.Advance` zawsze daje pełną trakcję i obcina przyspieszenie od dołu
do zera, bo przebieg rozruchowy z definicji przyspiesza. Prowadzony skład musi
umieć jechać wybiegiem i hamować.

Dołożone są dokładnie dwie rzeczy, których w rdzeniu nie było:

1. **trakcja częściowa** — `F = nastawnik · F_pełna`;
2. **hamulec jako polecenie** — zadane opóźnienie z ograniczeniem zrywu.

Wszystko inne — `TractionModel`, `DavisResistance`, składowa pochylenia, masa
efektywna — jest wywoływane z T-310, nie przepisane. Kontrola tego jest liczbowa
i jest w §3: przy `throttle = 1`, `brake = 0` i rozruchu z postoju kontroler daje
**co do bitu** ten sam wynik, co `AccelerationRun`, czyli ten sam, co
`tools/physics/reference.py`.

`TrackAxis` trafił do `Sim/Line`, bo `docs/01-architecture.md` przypisuje tam „oś".
Gdyby oś mieszkała w Godocie, chainage składu — czyli stan symulacji — zależałby
od kodu widoku, a rdzeń nie miałby jak odpowiedzieć na pytanie „gdzie jest pociąg".
Klasa nie czyta plików, tylko dostaje treść JSON-a: rdzeń ma działać bez katalogu
`data/` na dysku (ten sam powód, dla którego rejestr M7 jest zasobem osadzonym).

### 1.3 `src/Sim.Runner` — drugi gospodarz tego samego przejazdu

Wymaganie „przejazd w Godocie i ten sam scenariusz policzony bezpośrednio przez
`MetroBxl.Sim` muszą dać zgodne wyniki" wymaga czegoś, co uruchomi rdzeń **bez
silnika**. Stąd konsolowa binarka: `drive` liczy przejazd, `compare` porównuje dwie
telemetrie kolumna po kolumnie, `axis` sprawdza oś wobec manifestu chunków,
`parity` sprawdza kontroler wobec T-310. Zero `PackageReference`, tak jak rdzeń.

**Czego to porównanie dowodzi, a czego nie.** Obie strony wykonują ten sam kod
rdzenia — i o to chodzi. Ryzykiem nie jest fizyka (ta ma parytet z Pythonem od
T-310), tylko **pętla klatkowa**: zmienne `delta`, sprzężenie z liczbą klatek,
kumulacja błędu czasu. Dlatego przejazd w Godocie jest liczony przy trzech różnych
rytmach klatek, w tym celowo nierównym.

### 1.4 GLB wczytywane w runtime, nie importowane do `res://`

Chunki tunelu i skorupa M7 są produktem generatora w `build/` i nie wchodzą do repo
(reguła 8). Import Godota wymagałby, żeby leżały pod `res://` i miały obok
skomitowane pliki `.import`. `GltfDocument.AppendFromFile` czyta plik z dowolnej
ścieżki i buduje scenę w pamięci, więc repo zostaje czyste, a generator pozostaje
jedynym źródłem siatek.

Cena, powiedziana wprost: nie ma wstępnego przetworzenia siatek, a wczytanie
kosztuje czas przy starcie sceny. Dla 12 chunków (867 kB, 16176 trójkątów) jest to
nieistotne; dla całej sieci trzeba będzie do tej decyzji wrócić.

### 1.5 **Streamowania nie ma. Wczytywane jest wszystkie 12 chunków naraz.**

To jest świadoma decyzja, nie przeoczenie, i tak brzmi w kodzie
(`World/TunnelView.LoadAll`).

| | co jest teraz | co dałby predykat okna |
|---|---|---|
| chunków rezydentnych | 12 z 12 | maks. **4 z 12** |
| bajtów rezydentnych | 867,1 kB | **275,9 kB** (najgorszy przypadek okna) |
| trójkątów rezydentnych | 16176 (LOD 0) | 16176 → ok. 3900–5000 przy LOD 1/2 |

Liczby z `reports/L1_A-chunks.md` §0 i `reports/L1_A-lod.md` §2. Powód, dla którego
port nie został zrobiony **w tym zadaniu**: predykaty `sweep.chunks_for_train`,
`sweep.streaming_plan` i `lod.lod_plan` są przetestowane po stronie Pythona
(`tools/tests/test_sweep.py`, `test_chunks.py`, `test_lod.py`, plus przejazd co 25 m
w `tools/ci/tunnel_alignment.sh`). Przepisanie ich do C# bez przeniesienia tych
testów dałoby **drugą implementację bez kontroli** — a rozjazd predykatu objawia się
dziurą w tunelu pod pociągiem, czyli dokładnie tym, czego te testy pilnują.
Manifest jest już czytany w scenie (`Assets/ChunkManifest`), razem z zakresami
chainage, poziomami LOD i domyślnym oknem 600/300 m, więc port jest następnym
krokiem o jasno zarysowanym zakresie, a nie odległym pomysłem.

### 1.6 Zakresy członów czytane z bryły, nie przepisane

M7 jest przegubowy: sześć pudeł i pięć mieszków, każde na własnej cięciwie
(`tools/blender/placement.py: place_spans`). Warstwa silnika musi znać lokalny
zakres X każdej bryły — i **odczytuje go z AABB siatki**, zamiast powtarzać podział
z `m7_layout.py`. Dzięki temu w `src/Game` nie ma ani jednej skopiowanej stałej
pojazdu, a zmiana podziału członów w generatorze nie wymaga tu żadnej poprawki.
Skopiowana stała rozjeżdża się po cichu; odczytana nie.

Ta sama zasada dotyczy długości składu: ogon liczy się od czoła przez **zmierzone**
94,000 m, a nie przez liczbę wpisaną w kod.

### 1.7 Konwersja układów jest w jednym miejscu

Eksporter glTF przelicza Blenderowe Z-w-górę na Y-w-górę przy zapisie, więc chunki
i skorupa przychodzą **już** w układzie Godota. Oś z rdzenia przychodzi w układzie
danych. `World/SceneAxis.ToScene` robi dokładnie tę samą zamianę `(x, y, z) → (x, z, −y)`
i jest jedynym miejscem, w którym ta zamiana występuje. Chunki nie dostają żadnej
transformacji — każda byłaby drugą zamianą i rozjechałaby tunel z osią.

### 1.8 Kabina nie widzi własnego pudła

Kamera kabinowa stoi **wewnątrz** skorupy M7, a ta po `solidify` ma obie powierzchnie.
Bez ukrycia składu widać z bliska jego wnętrze i nic poza tym — co widać było na
pierwszym zrzucie, zanim to poprawiłem. Model wnętrza kabiny nie istnieje: T-220
świadomie go nie robi (`docs/21-measured-vs-assumed.md` §1.3). Jedyne uczciwe
rozwiązanie na tym etapie to schować bryłę w widoku kabiny i powiedzieć, że pulpitu
nie ma, zamiast go zgadywać.

### 1.9 Zrzuty ekranu: `--headless` nie wystarczy

`--headless` w Godocie **wyłącza renderer** — `GetViewport().GetTexture()` nie ma
wtedy czego zwrócić. Obraz powstaje pod `xvfb-run` ze sterownikiem `opengl3`
(llvmpipe, renderowanie programowe). Scena wykrywa headless i zamiast zapisać pusty
plik zgłasza błąd z instrukcją. Telemetria działa w obu trybach, bo fizyka nie
zależy od renderera.

---

## 2. Scenariusz przejazdu

`DriveScenario.PackageAFirstRun`: czoło składu startuje na chainage 94,0 m
(Gare de l'Ouest), pełny nastawnik z ograniczeniem 80 km/h, na chainage 6420,0 m
pełne hamowanie służbowe do zatrzymania. Bez postojów na stacjach pośrednich —
cykl drzwi to T-312, a rozkład i dyspozytor to T-320.

Warunki: obciążenie AW2 (221 940 kg), sucha szyna (μ = 0,25), otoczenie `Tunnel`
(c = 1,40), pochylenie **0**. Zero pochylenia nie jest wyborem estetycznym:
profil pionowy pakietu A ma status `not_modelled`, a `docs/21-measured-vs-assumed.md`
§3 zabrania wyprowadzania z niego rzędnych.

Wynik: **38194 kroków, 318,283 s, czoło zatrzymane na chainage 6653,791 m**,
czyli 32,95 m przed końcem osi (6686,739 m).

---

## 3. Weryfikacja — rzeczywiste wyjście

### 3.1 `dotnet build MetroBxl.sln --configuration Release`

```
  Sim -> src/Sim/bin/Release/net8.0/MetroBxl.Sim.dll
  Sim.Runner -> src/Sim.Runner/bin/Release/net8.0/MetroBxl.Sim.Runner.dll
  Sim.Tests -> tests/Sim.Tests/bin/Release/net8.0/MetroBxl.Sim.Tests.dll

Build succeeded.
    0 Warning(s)
    0 Error(s)
```

### 3.2 `dotnet test tests/Sim.Tests --configuration Release`

```
Passed!  - Failed:     0, Passed:   127, Skipped:     0, Total:   127, Duration: 388 ms - MetroBxl.Sim.Tests.dll (net8.0)
```

**77 → 127.** Siedemdziesiąt siedem testów z T-310 przechodzi bez zmian — żaden
istniejący plik rdzenia nie zmienił zachowania. Pięćdziesiąt nowych pokrywa dokładnie
to, co T-400 dokłada, i nic ponadto:

| plik | co sprawdza |
|---|---|
| `TrainControllerTests` | parytet pełnej trakcji z `AccelerationRun` co do bitu; trakcja częściowa (0,5 · F dokładnie, 0 to 0, hamulec zeruje ciąg); **brak obcięcia przyspieszenia od dołu** — jawna różnica wobec `TrainDynamics.Advance`; ograniczenie zrywu przy narastaniu **i** zdejmowaniu hamulca; zatrzymanie rampy dokładnie na wartości zadanej; obcięcie do ograniczenia prędkości i do zera (skład nie odtacza się w tył, także pod górę); bilans energii hamowania; walidacja argumentów |
| `ScenarioDriveTests` | powtarzalność co do bitu; **podział kroków na nierówne partie nie zmienia stanu** (odpowiednik przebiegu z nierównym czasem klatki, ale bez silnika); bezpiecznik pętli; `SegmentAt`; katalog założeń scenariusza; kształt wiersza telemetrii |
| `TrackAxisTests` | pojedynczy odcinek, tryb wierny, duplikaty punktów, chainage na wierzchołku, oba końce osi, wartości poza zakresem, `NaN`, sortowanie stacji, status profilu pionowego oraz kontrola na prawdziwej osi pakietu A (447 → 1349 punktów, 6686,739 m, 12 stacji) |

#### Kontrola negatywna testów

Test, który przechodzi także wtedy, gdy kod jest zepsuty, nic nie kontroluje. Dwie
mutacje wprowadzone celowo do `TrainController` i wycofane po sprawdzeniu:

| mutacja | co się wywróciło |
|---|---|
| `acceleration = Math.Max(0.0, mechanical) - brakeRate` (przywrócenie obcięcia z T-310) i zryw × 1000 | **5 testów**: wybieg bez obcięcia, zryw w obie strony, bilans energii, skrócenie drogi hamowania |
| `traction = tractionFull` (nastawnik ignorowany) i usunięcie obcięcia prędkości do zera | **9 testów**: trakcja częściowa, zerowy nastawnik, pierwszeństwo hamulca, wybieg, brak odtaczania (na poziomie i pod górę), koniec przejazdu pakietu A, bilans energii, skrócenie drogi |

Po wycofaniu obu mutacji `git diff` na `src/Sim/Train/TrainController.cs` jest pusty.

### 3.3 `python3 tools/tests/test_all.py`

```
  347/347 przeszło
```

### 3.4 `bash doctor.sh`

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
...
Testy narzędzi:
  ok    347/347 przeszło

Testy rdzenia symulacji:
  ok    127/127 przeszło

--------------------------------------------------
  Baza projektu jest gotowa. Następne zadanie: T-010.
  1 narzędzi opcjonalnych brakuje; instaluj je dopiero przed zadaniem, które ich wymaga.

exit=0
```

`WARN` przy Godocie jest prawdziwy i nie da się go zamaskować: w tym środowisku
silnik leży pod `/opt/godot/godot4`, a `doctor.sh` szuka `godot` w `PATH`. Nie
poprawiam tego pliku — patrz §8.

### 3.5 Oś w C# to ta sama krzywa, po której zamiatany jest tunel

```
[OŚ] L1_A: punktów źródłowych=447 zagęszczonych=1349 długość_źródłowa=6686.350 m długość_zagęszczona=6686.739 m
[OŚ] odchyłka od łamanej STIB = 0.2499 m, stacji=12, profil_pionowy=not_modelled
[OŚ] zrzut 1349 punktów -> build/t400/axis_cs.csv
[OŚ] manifest chunków: 6686.739 m, C#: 6686.739 m, |Δ| = 1.335E-005 m -> ZGODNE
```

Sama zgodność długości byłaby słabym dowodem, więc oś została porównana z Pythonem
**punkt po punkcie**:

```
$ python3 - (catmull_rom z tools/blender/sweep.py vs zrzut z C#)
len py 1349 cs 1349
max |delta| = 0.0   niezgodnych składowych co do bitu = 0 z 4047
```

Wszystkie 4047 współrzędnych zgadzają się **co do bitu**. To znaczy, że skład jedzie
po osi tunelu, a nie równolegle do niej — a rozjazd byłby tu rzędu 0,25 m, czyli
piątej części luzu do ściany.

### 3.6 Kontroler to nadal rdzeń z T-310

```
[PARYTET] Aw0: kroki 3023 vs 3023 (==), droga 337.478 m vs 337.478 m (co do bitu)
[PARYTET] Aw2: kroki 3998 vs 3998 (==), droga 447.920 m vs 447.920 m (co do bitu)
[HAMOWANIE] kinematyczne (T-310) 240.479 m / 20.933 s, kontroler z oporami 233.723 m / 20.450 s, różnica 6.757 m = praca oporów Davisa
```

Rozruch: identyczna liczba kroków i droga zgodna co do bitu z `AccelerationRun`,
czyli z tabelą parytetu z `reports/T-310-physics.md` §2 (25,2 s / 337,5 m i
33,3 s / 447,9 m).

Hamowanie: **kontroler celowo nie daje tej samej drogi** i to jest różnica, którą
trzeba nazwać, a nie schować w tolerancji. `ServiceBrakingRun` jest modelem czysto
kinematycznym i **nie zna oporów ruchu** — zadaje opóźnienie i tyle. Kontroler
dokłada do niego opory Davisa, bo prowadzony skład jedzie w tunelu. Różnica
**6,757 m na 240 m (2,8 %)** jest pracą oporów na drodze hamowania — i **nie jest to
już twierdzenie, tylko pomiar**, bo policzone niezależnie w dwóch testach:

```
[BILANS HAMOWANIA] E_kin = 59184000.000 J, opory = 1776596.274 J, hamulec = 57382762.017 J,
                   dyskretyzacja = 24641.708 J, reszta = -4.235E-008 J, względnie = 7.155E-016
[SKRÓCENIE] kinematyczne 240.479 m, kontroler 233.723 m, zmierzone skrócenie 6.757 m,
            z pracy oporów 6.738 m, różnica 0.019 m
```

Pierwsza linia to bilans `½·m_ef·v₀² = ∫F_oporu ds + m_ef·∫b ds + dyskretyzacja`,
domknięty do **7,2·10⁻¹⁶** względnie, czyli do precyzji `double`. Człon dyskretyzacji
(24,6 kJ) jest wypisany osobno, a nie rozmazany w tolerancji — bierze się stąd, że
krok liczy siły od prędkości z **początku**, a drogę od prędkości z **końca**.

Druga linia zamienia pracę oporów na metry: `Δs = (∫F_oporu ds) / (m_ef · b)` daje
**6,738 m** wobec zmierzonych **6,757 m**, czyli zgodność do **0,019 m (0,3 %)**.
Resztę wyjaśnia narastanie hamulca w pierwszych 1,47 s, kiedy `b` nie jest jeszcze
stałe. Oba testy mają progi wzięte z tych pomiarów (1·10⁻¹² i 0,05 m), nie z sufitu.

### 3.7 Przejazd w Godocie vs przejazd z rdzenia — rozjazd i próg

Trzy przebiegi, trzy różne rytmy klatek, jeden scenariusz:

| przebieg | gospodarz | kroków na klatkę | klatek | kroków | chainage końcowy |
|---|---|---:|---:|---:|---:|
| `core.csv` | `src/Sim.Runner` | — (goła pętla) | — | 38194 | 6653,791 m |
| `godot.csv` | Godot headless | 120 | 319 | 38194 | 6653,791 m |
| `godot_repeat.csv` | Godot headless | 120 | 319 | 38194 | 6653,791 m |
| `godot_jitter.csv` | Godot headless | 37 ± 45 % | **1032** | 38194 | 6653,791 m |

```
$ sha256sum build/t400/*.csv
8183100f0cced5bd5a088b00b2e50afc79726479329598204f1095d77fc953d4  build/t400/core.csv
8183100f0cced5bd5a088b00b2e50afc79726479329598204f1095d77fc953d4  build/t400/godot.csv
8183100f0cced5bd5a088b00b2e50afc79726479329598204f1095d77fc953d4  build/t400/godot_repeat.csv
8183100f0cced5bd5a088b00b2e50afc79726479329598204f1095d77fc953d4  build/t400/godot_jitter.csv
```

Cztery pliki, jeden odcisk. Porównanie kolumna po kolumnie, próg **0** (nie „małe
epsilon" — dokładnie zero):

```
[PORÓWNANIE] wierszy=320 identyczne co do bajtu=TAK
[PORÓWNANIE] step         max |Δ| = 0.000E+000 (wiersz 0) ok
[PORÓWNANIE] t_s          max |Δ| = 0.000E+000 (wiersz 0) ok
[PORÓWNANIE] chainage_m   max |Δ| = 0.000E+000 (wiersz 0) ok
[PORÓWNANIE] distance_m   max |Δ| = 0.000E+000 (wiersz 0) ok
[PORÓWNANIE] speed_mps    max |Δ| = 0.000E+000 (wiersz 0) ok
[PORÓWNANIE] speed_kmh    max |Δ| = 0.000E+000 (wiersz 0) ok
[PORÓWNANIE] accel_mps2   max |Δ| = 0.000E+000 (wiersz 0) ok
[PORÓWNANIE] throttle     max |Δ| = 0.000E+000 (wiersz 0) ok
[PORÓWNANIE] brake        max |Δ| = 0.000E+000 (wiersz 0) ok
[PORÓWNANIE] próg = 0.000E+000
```

Ten sam wynik dla pary `godot.csv` ↔ `godot_repeat.csv` (powtarzalność) i dla pary
`core.csv` ↔ `godot_jitter.csv` (1032 klatki zamiast 319, czasy klatek nierówne
o ±45 %). **Rozjazd wynosi 0,000 m na 6,56 km.**

Dlaczego akurat zero, a nie „metry na kilometr": telemetria jest formatowana
formatem `R` (round-trip) w kulturze niezmiennej, a stan po N krokach nie zależy od
tego, jak kroki rozłożyły się na klatki — akumulator zamienia dowolny czas klatki na
całkowitą liczbę kroków 1/120 s i przenosi resztę dalej.

### 3.8 Kontrola negatywna porównania

Porównanie, które mówi „ok" także wtedy, gdy nic nie sprawdza, jest bezużyteczne.
Po zepsuciu jednej liczby o **4 mm na 4129 m**:

```
perturbed row 200: 23880,199,4223.772109988554,4129.776109988554,22.22222222222222,80,...
[PORÓWNANIE] wierszy=320 identyczne co do bajtu=NIE
[PORÓWNANIE] distance_m   max |Δ| = 4.000E-003 (wiersz 200) PONAD PRÓG
[PORÓWNANIE] próg = 1.000E-009
exit=1
```

Wykryte. Rozjazd „rzędu metrów na kilometrze" byłby o trzy rzędy wielkości większy
od tego, co ta kontrola łapie.

### 3.9 Scena i geometria — wyjście z przejazdu

```
[TUNEL] L1_A flat-preview: wczytano 12/12 chunków, 12 siatek, profil box_double 9.40×5.90 m, production_ready=False
[SKŁAD] brył=11 długość=94.000 m szerokość=2.700 m dach=3.600 m nad główką szyny
[OŚ] manifest 6686.739 m vs oś z rdzenia 6686.739 m, |Δ| = 1.335E-005 m
[PRZEJAZD] tryb=telemetry widok=Cab scenariusz=package-a-first-run krok=1/120 s masa=221940 kg limit=80.0 km/h
[OŚ] L1_A: 1349 punktów, 6686.739 m, 12 stacji
[TELEMETRIA] 320 próbek -> build/t400/godot.csv
[PRZEJAZD] koniec: kroków=38194 t=318.283 s chainage=6653.791 m droga=6559.791 m klatek=319 powód=stopped
```

Wczytane 11 brył = 6 członów + 5 mieszków, wymiary zmierzone z siatki zgadzają się
ze `spec` M7 (94,0 m × 2,70 m) i z `DESIGN_TOTAL_HEIGHT_M` = 3,60 m.

Przebieg headless kończy się czysto:

```
$ grep -cE "ERROR|WARNING" build/t400/clean.log
0
```

---

## 4. Zrzuty ekranu — co na nich widzę

Pięć obrazów 1280 × 720, `xvfb-run` + `--rendering-driver opengl3` (llvmpipe).
Każdy powstaje przez przewinięcie tego samego, deterministycznego przejazdu do
zadanego chainage, więc stan na obrazie da się odtworzyć liczbą kroków.
Pliki są w `renders/t400/` i **nie są komitowane** (reguła 8).

### `cab_2000m.png` — kabina, chainage 2000,1 m, 80,0 km/h, 11872 kroków

Widok z wnętrza tunelu do przodu. Widać podłogę, dwie ściany boczne i strop, które
zbiegają się do ciemnego punktu zbiegu mniej więcej w środku kadru. W prawym górnym
rogu wyraźnie widać **ścięcie naroża stropu** — to faza profilu `box_double` między
4,30 a 4,70 m. Powierzchnie są ciągłe: żadnej szczeliny, żadnego prześwitu, żadnego
miejsca, w którym widać „przez" ścianę na tło. Kadr jest **asymetryczny** i to jest
poprawne: prawa ściana jest wyraźnie bliżej i jaśniejsza od lewej, bo kamera stoi
na torze przesuniętym o +2,10 m od osi tunelu — do prawej ściany jest
4,70 − 2,10 = 2,60 m, do lewej 4,70 + 2,10 = 6,80 m. HUD na dole podaje
`80.0 km/h`, `a = 0.36 m/s²`, `chainage 2000.1 m / 6686.7 m`,
`Comte de Flandre|Graaf van Vlaanderen za 55 m` i pełny ciąg przy odpuszczonym hamulcu.

### `seam_c01_c02.png` — kabina 3,3 m przed szwem chunków, chainage 976,2 m

Ten sam widok, wybrany celowo tuż przed granicą chunków c01/c02 (979,52 m).
Tunel jest **ciągły przez szew**: nie ma poprzecznej krechy, uskoku ani jaśniejszej
szczeliny w miejscu, w którym kończy się jedna siatka, a zaczyna druga. To jest
wizualne potwierdzenie tego, co T-210 zmierzył liczbowo (szczelina 0,000 mm).

### `chase_2000m.png` — kamera 12 m za ogonem, w tunelu, chainage 2000,1 m

Widać czoło tunelu w przekroju i **tył składu** jako ośmiobok z wyraźnymi ściętymi
narożami — obrys pudła M7 (2,70 m szerokości, dach 3,60 m nad główką szyny, ścięcie
0,35 m). Skład stoi **w świetle tunelu, nie w ścianie**: wokół niego widać ciemniejszą
przestrzeń, a ściany, podłoga i strop tunelu są poza obrysem pudła po wszystkich
czterech stronach. Wysokość pudła na obrazie to ok. 135 px; przy tej odległości i pionowym
kącie widzenia 60° na 720 px odpowiada to obiektowi o wysokości ok. 2,6 m, czyli
widocznej wysokości pudła 3,60 − 0,95 = 2,65 m. Skala jest wiarygodna.

### `curve_R91_chase.png` — ten sam widok na najciaśniejszym łuku, chainage 2560,1 m

Wybrany pomiarem, nie na oko: minimum promienia zagęszczonej osi pakietu A wynosi
**91,50 m przy chainage 2488,8 m**. Na obrazie tył składu jest **skręcony** — widać
lewe czoło ostatniego pudła i wystający zza niego kolejny człon. To jest dowód, że
osadzenie przegubowe działa: gdyby skład był jedną sztywną bryłą, tył byłby na łuku
ustawiony równo z kamerą, a sąsiedni człon by się nie pokazał. Ściany tunelu są
asymetryczne, tak jak na łuku być powinny. Skład nadal mieści się w świetle.

### `outside_2000m.png` — kamera kontrolna z sąsiedniego toru, 26 m przed czołem

Widok wzdłuż tunelu na nadjeżdżający skład. Widać czoło M7 (ścięty ośmiobok),
zwężenie strefy czołowej i **kolejne człony uciekające w głąb**, a na bokach pudeł
jasne pionowe szczeliny — otwory drzwi wycięte przez `m7_shell.py`. Skład jest
wyraźnie węższy od tunelu i stoi po jednej jego stronie. Ściany tunelu są widoczne
wokół, więc pojazd nie jest wtopiony w geometrię.

**Co na tym obrazie widać, a czego nie chciałbym przemilczeć:** pod pudłem jest pusto.
Spód skorupy M7 leży 0,95 m nad główką szyny, a podłoga tunelu 1,20 m **pod** nią —
więc skład wisi 2,15 m nad podłogą tunelu i nie ma pod nim niczego. To nie jest błąd
osadzenia: wózków, szyn, podsypki i koryta po prostu nie ma. Wózki są `blocked`
(`docs/21` §1.3), a geometria toru czeka na R-005 (#17).

### Kontrola rachunkowa luzów, do zestawienia z obrazem

Z osadzenia (środek pudła +2,10 m od osi tunelu, półszerokość 1,35 m, dach 3,60 m)
i z profilu `box_double` (ściany ±4,70 m, strop 4,70 m, faza od 4,15 m):

| kierunek | luz |
|---|---:|
| do prawej ściany | 4,70 − (2,10 + 1,35) = **1,25 m** |
| do lewej ściany | 4,70 + 2,10 − 1,35 = **5,45 m** |
| do stropu | 4,70 − 3,60 = **1,10 m** |

Skrajna prawa krawędź pudła wypada na 3,45 m, czyli przed początkiem fazy stropu
(4,15 m), więc ścięcie naroża nie wchodzi w grę. Zgadza się to z niezależnym
pomiarem generatora: `m7_shell.py` raportuje `profil box_double: OK luz_max=1.08 m`
(największy jednakowy luz, przy którym skrajnia jeszcze się mieści).

---

## 5. Założenia projektowe warstwy silnika i scenariusza

Wszystkie są `design_assumption`. **Żadna nie jest faktem o brukselskim metrze**
i wolno je zmienić bez pytania kogokolwiek o zgodę (`docs/21-measured-vs-assumed.md` §6).
Katalog żyje w kodzie (`src/Game/DesignAssumptions.cs`, `DriveScenario.Assumptions`)
i jest wypisywany do logu przy każdym przejeździe.

| stała | wartość | dlaczego taka |
|---|---:|---|
| `CabEyeHeightM` | 2,20 m | wysokość oka nad główką szyny; podłoga M7 jest na 1,03 m (`spec`), reszta to postawa siedzącego maszynisty — **STIB nie publikuje rysunku pulpitu M7** |
| `CabEyeSetbackM` | 1,80 m | odsunięcie oka od czoła; mieści się w strefie kabiny 3,60 m z `m7_layout.py`, ale samo w sobie nie ma źródła |
| `CabEyeLateralM` | 0,00 m | oko na osi pudła; rozmieszczenie pulpitu nie jest publiczne, a zgadnięta strona byłaby zgadniętym faktem |
| `CabFovDeg` | 70° | parametr obrazu, nie wymiar pojazdu |
| `ChaseBehindM` | 12,0 m | kadr kamery obserwacyjnej |
| `ChaseHeightM` | 2,60 m | j.w., z zapasem pod stropem 4,70 m |
| `OutsideAheadM` | 26,0 m | kamera kontrolna, nie widok gry |
| `OutsideLateralM` | −4,20 m | kamera na sąsiednim torze; wartość = rozstaw torów `box_double` |
| `OutsideHeightM` | 2,60 m | j.w. |
| `ControlNotchRatePerSecond` | 0,80 1/s | czułość sterowania to decyzja o obsłudze, nie parametr M7 |
| `TrackOffsetM` | +2,10 m | wartość z `profiles.py` (`design`); **wybór prawego toru nie ma źródła** — `ACTU_LIGNES_BRUTES` to trasa handlowa, nie geometria tor-po-torze |
| `HeadlightRangeM` | 70,0 m | oświetlenie sceny, nie dane o taborze |
| `HeadlightEnergy` | 2,5 | j.w. |
| `StartChainageM` | 94,0 m | czoło składu na starcie, równe długości M7, żeby cały skład stał na osi |
| `BrakeChainageM` | 6420,0 m | dobrane do zmierzonej drogi hamowania; czoło staje 32,95 m przed końcem osi |

Nie dopisywałem ich do `docs/21-measured-vs-assumed.md`: ten dokument jest wspólnym
rejestrem, na którym równolegle pracują inne gałęzie, a dopisanie sekcji „warstwa
Godota" jest zmianą stanu projektu należącą do właściciela repo. Katalogi w kodzie
i ta tabela wystarczają, żeby nic nie zniknęło.

---

## 6. CI

`.github/workflows/godot-first-run.yml`, `ubuntu-latest`, 18 kroków:

1. .NET SDK 8.0.x przez `actions/setup-dotnet@v4`;
2. Godot **4.3 mono** z GitHub Releases (~70 MB), z cache po wersji. Sam plik
   wykonywalny nie wystarczy — obok musi leżeć katalog `GodotSharp`, inaczej silnik
   nie znajduje assembly .NET i **wywraca się z SIGSEGV** przy starcie. Sprawdziłem
   to na własnej skórze w tym środowisku, gdzie `/opt/godot/` miał tylko binarkę;
3. kontrola, że `MetroBxl.Game` **nie jest** w `MetroBxl.sln`;
4. build rdzenia, runnera i projektu Godota;
5. Blender + `xvfb` + `libgl1`/`libegl1`/`libgl1-mesa-dri` z apt;
6. generowanie chunków i skorupy M7 **w jobie** — scena wczytuje więc świeżo
   wygenerowaną geometrię, a nie kopię sprzed miesięcy;
7. `axis`, `parity`, `drive`;
8. dwa przejazdy w Godocie (120 kroków/klatkę i 37 ± 45 %), oba porównane z rdzeniem
   z progiem **0**;
9. kontrola negatywna porównania;
10. pięć zrzutów pod `xvfb`, wrzucanych jako artefakt razem z telemetriami.

Sześć istniejących workflow nie zostało tknięte. `sim-tests.yml` buduje teraz przy
okazji `Sim.Runner`, bo doszedł on do solucji — to projekt bez zależności NuGet i bez
Godota, więc dyscyplina rdzenia jest zachowana.

### Stan CI — job zakończony

`CLAUDE.md` §9: `queued` nie jest weryfikacją. Stan po **zakończonych** jobach na PR:

| workflow | wynik na gałęzi | co potwierdza |
|---|---|---|
| **Godot first run** | **success** — wszystkie 19 kroków | przejazd w Godocie, porównanie z rdzeniem, zrzuty |
| Sim core tests | success | `dotnet test tests/Sim.Tests` — 127/127 |
| Python tool tests | success | 347/347 testów narzędzi |

Pierwszy zielony przebieg `Godot first run` to
[run #1](https://github.com/matmaxalez/metro.brussels/actions/runs/33534163101);
kolejne przebiegi tej gałęzi dają te same liczby, bo przejazd jest deterministyczny.

Pozostałe cztery workflow (`blender-smoke`, `tunnel-alignment`, `visual-regression`,
`m7-shell`) mają filtry ścieżek, których ten PR nie rusza, więc się nie uruchomiły.

Uwaga o filtrze ścieżek, bo łatwo się na tym pomylić: dla zdarzenia `pull_request`
GitHub liczy filtr wobec **całego diffu wobec bazy**, a nie wobec ostatniego pusha.
`Godot first run` uruchamia się więc przy każdej aktualizacji tej gałęzi — także
wtedy, gdy zmienił się sam raport — i jego wynik zawsze dotyczy aktualnej treści PR-a.
Wynik dotyczy więc zawsze aktualnej treści PR-a, także po dołożeniu testów.

Kroki weryfikacyjne, wszystkie zielone: `Core stays free of the engine`,
`Axis in C# matches the sweep manifest`, `Controller is still the T-310 core`,
`Reference run from the core alone`, `Godot run, 120 steps per frame`,
`Godot run, uneven frames`, `Negative control of the comparison`,
`Screenshots under Xvfb`.

Zrzuty powstały na runnerze, na llvmpipe, i zostały wrzucone jako artefakt razem
z telemetriami (622 kB):

```
[ZRZUT] .../renders/t400/curve_R91_chase.png 1280x720 err=Ok widok=Chase kroków=14896 chainage=2560.1 m v=80.0 km/h
[ZRZUT] .../renders/t400/seam_c01_c02.png 1280x720 err=Ok widok=Cab kroków=6343 chainage=976.2 m v=80.0 km/h
-rw-r--r-- 1 runner runner 139984 Sep  1 16:51 cab_2000m.png
-rw-r--r-- 1 runner runner  92686 Sep  1 16:51 chase_2000m.png
-rw-r--r-- 1 runner runner  98901 Sep  1 16:51 curve_R91_chase.png
-rw-r--r-- 1 runner runner 121077 Sep  1 16:51 outside_2000m.png
-rw-r--r-- 1 runner runner 139841 Sep  1 16:51 seam_c01_c02.png
```

Liczba kroków przy zrzucie zgadza się co do jedności z przebiegiem lokalnym
(14896 na łuku, 6343 przed szwem), więc przewijanie przejazdu jest deterministyczne
także między maszynami.

Jedyny `ERROR` w logu pochodzi od ALSA — runner nie ma karty dźwiękowej, Godot
przechodzi na sterownik pozorny. Do fizyki i obrazu nic z tego nie wchodzi.

---

## 7. Czego z Issue #26 tutaj **nie ma**

Issue #26 mówi o „obserwacji autonomicznej linii i przejęciu jednego M7". Ten PR
realizuje pierwszy etap i **nie zamyka ani #26, ani T-400**.

| brakuje | dlaczego |
|---|---|
| **wiele składów na linii** | wymaga T-320 (`LineCore`, dispatcher, rozkład), którego nie ma |
| **rozkład jazdy i opóźnienia** | j.w. |
| **przejęcie składu w ruchu** | nie ma czego przejmować, dopóki nie ma autonomicznych składów |
| **postoje na stacjach, drzwi, czas postoju** | T-312; cykl 0,5 / 2,0 / 3,0 / 2,5 / 0,5 s jest w `docs/02-simulation.md`, ale przeniesienie go „przy okazji" łamie regułę 10 |
| **sygnalizacja, bloki, ATP, CBTC** | T-313 / T-314 |
| **streamowanie chunków i przełączanie LOD** | §1.5 — świadomie odłożone, z liczbami |
| **kolizje** | bryły `_col.glb` są generowane i opisane w manifeście, ale scena ich nie wczytuje: nie ma jeszcze niczego, co mogłoby w tunel uderzyć |
| **stacje, perony, wnętrza, kabina** | T-211 / R-004 (#16, #18); peronów nie ma z czego zrobić |
| **dźwięk** | poza zakresem pierwszego przejazdu |
| **mapa akcji `InputMap` w projekcie** | sterowanie czyta klawisze fizycznie; konfigurowalne akcje to osobna decyzja o obsłudze |
| **hamowanie awaryjne jako stan, hamulec postojowy** | T-311; kontroler ma tylko hamulec służbowy i nie odtacza się w tył |
| **`docs/TASKS.md` odhaczone** | odhaczenie zadania jest zmianą stanu projektu i należy do właściciela repo po przejrzeniu PR |

Nie ma też **żadnego brandingu**: materiały są neutralnymi szarościami, HUD to goły
tekst, nie ma logo, map sieci, piktogramów, livery ani wystroju STIB/MIVB
(`docs/03-legal.md`).

---

## 8. Zauważone przy okazji, nie tknięte

1. **`doctor.sh` szuka `godot` w `PATH`.** W tym środowisku silnik leży pod
   `/opt/godot/godot4` i nie ma dowiązania, więc kontrola daje `WARN` mimo że Godot
   jest zainstalowany i działa. Do tego sam plik wykonywalny **nie wystarcza** —
   bez katalogu `GodotSharp` obok binarki wersja mono kończy się SIGSEGV, a
   `doctor.sh` nie ma jak tego zobaczyć. Sensowna poprawka to sprawdzać
   `${GODOT_BIN:-godot}` i istnienie `GodotSharp/Api`, ale to zmiana w pliku,
   którego dotyka kilka równoległych gałęzi, i nie należy do tego zadania.
2. **`doctor.sh` nadal kończy zdaniem „Następne zadanie: T-010"**, choć T-010, cały
   pakiet T-2xx i T-310 są zrobione. Odnotowane już w `reports/T-310-physics.md` §9.2
   i nadal nieprawdziwe.
3. **`data/track/L1_A.json` ma `speed_limits: []`.** Ograniczenie 80 km/h w przejeździe
   pochodzi z `VehicleModel.DesignMaxSpeedKmh`, czyli z **pojazdu**, nie z **linii**.
   Prawdziwe ograniczenia odcinkowe są puste we wszystkich sześciu pakietach i to jest
   dziura w danych, którą widać dopiero wtedy, gdy ktoś spróbuje pojechać.
4. **`docs/21-measured-vs-assumed.md` §4 podaje odchyłkę zagęszczenia 0,1064 m**,
   a `sweep.max_deviation` policzone na pełnym zbiorze punktów Catmull-Rom daje
   **0,2499 m** (ta sama liczba w Pythonie i w C#, sprawdzone). Podejrzewam, że
   0,1064 m odnosi się do pierścieni próbkowanych co 5 m, a nie do wszystkich punktów
   krzywej — ale to jest różnica w tym, co dokument opisuje, a nie w kodzie, więc
   niczego nie zmieniałem.
5. **Skorupa M7 nie ma wózków ani podwozia**, więc w widoku zewnętrznym skład wisi
   2,15 m nad podłogą tunelu. To znany zakres T-220, ale w ruchu wygląda to znacznie
   bardziej rzucająco się w oczy niż na renderach kontrolnych Blendera.
6. **Bryły kolizyjne `_col.glb` są generowane i nikt ich nie używa.** T-210 zmierzył
   dla nich zapas do ściany 0,0536 m i zapas do skrajni M7 0,650 m; scena ich nie
   wczytuje, bo nie ma jeszcze fizyki kolizji. Warto o nich pamiętać, zanim ktoś
   zacznie robić kolizje od zera.
