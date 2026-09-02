# Rozpiska zadań

`[ ]` do zrobienia · `[x]` zweryfikowane · **[CZŁOWIEK]** nie dla agenta.

**Źródłem prawdy o statusie są GitHub Issues**, nie ten plik. Ten plik jest mapą
zależności i zakresów. Statusy poniżej odzwierciedlają to, co **realnie leży w repo**
na dzień 01.09.2026, wieczorem — zadanie jest odhaczone tylko wtedy, gdy jego artefakty istnieją
w `main` i przechodzą CI.

## Gotowe w szkielecie
- `[x]` **T-100** — walidator osi trasy
- `[x]` **T-001** — profile przekrojów z kontrolą skrajni M7
- `[x]` **T-002** — model referencyjny dynamiki M7
- `[x]` **T-003** — testy narzędzi

## Narzędzia

### [x] T-010 · Pierwsze uruchomienie Blendera
- **Wyjście:** `tools/ci/blender_smoke.sh`, workflow `blender-smoke.yml`
- **Weryfikacja:** generacja → render → obejrzenie trzech PNG, plus cztery testy negatywne

### [ ] T-011 · Rozstawianie detali wzdłuż osi
- **Zależy od:** T-010

### [~] T-012 · Zrzuty kontrolne i wykrywanie regresji
- **Zrobione:** część Blenderowa — canonical manifest kamer `tools/visual/cameras.json`,
  deterministyczny render, metryki, odrzucanie pustej klatki, `docs/17-visual-regression.md`
- **Zostaje:** przechwytywanie z Godota
- **Zależy od:** T-400 (tylko część Godotowa)

## Dane

### [x] T-110 · Pobranie i normalizacja GTFS STIB
- **Wyjście:** `tools/track/fetch_gtfs.py`, `tools/track/normalize_stops.py`, `data/network/stops.json`

### [x] T-111 · Osie pakietów A–F z oficjalnych danych + kontrola OSM
- **Wejście:** STIB Shapefiles, Brussels Mobility `Metro`, OSM, GTFS
- **Wyjście:** `tools/track/build_alignment.py`, `data/track/L1_A.json`, provenance
- **Weryfikacja:** `python3 tools/track/validate.py data/track/L1_A.json --line L1`
- **Wynik:** sześć osi, razem 34 480,6 m; pakiet A to 447 punktów, 6686,35 m, 12 stacji.
  Kontrola krzyżowa w `reports/L1_A-crosscheck.md` i `reports/packages-BF-alignment.md`
- **Poza zakresem:** profil pionowy, szczegółowe rozjazdy Beekkant, odcinki międzypakietowe
- **Znane:** żadne dwa pakiety nie stykają się końcami — 4034 m w pięciu dziurach
  (`reports/network-chainage.md`)
- **Zależy od:** T-110

### [ ] T-112 · Profil pionowy pakietu A — **ZABLOKOWANE**
- **Blokada:** brak publicznych rzędnych główki szyny; dwa oficjalne źródła podają
  **sprzeczne** głębokości stacji (Schuman 15 m vs 17,42 m; Botanique 21,5 vs 20 m).
  Dopóki to trwa, tunel jest wariantem `flat-preview`, a generator odrzuca `--variant production`
- **Wejście:** oś + `station-depths.csv`
- **Skończone, gdy:** pochylenia interpolowanego profilu są 0–4%, a każda wygenerowana wartość ma `interpolated:true` i `design_assumption`
- **Zależy od:** T-111, T-901

### [x] T-113 · Rozkład jazdy i służby
- **Zależy od:** T-110 (zrobione); odległości wymagają osi z T-210
- **Wyjście:** `tools/track/timetable.py`, `tools/physics/schedule_envelope.py`,
  `reports/T-113-timetable.md`, `docs/21-measured-vs-assumed.md` §4d
- **Wynik:** takt 5:10 (L1/L5) i 5:40 (L2/L6), służba ok. 05:00–24:30, 48 kursów naraz
  w ruchu, 71 obiegów pojazdów z `block_id`. Postój rozkładowy na **100,0 %** zatrzymań
  pośrednich (29 554 z 29 554), 12–45 s. 55 odcinków toru ze zmierzoną długością wzdłuż osi
- **Odblokowuje:** górne ograniczenie czasu wymiany pasażerów dla T-312 (≤ 10,5 s przy
  medianowym postoju) oraz dolne ograniczenie prędkości liniowej **57,65 km/h** dla AW0 —
  pierwsza liczba, jaką repo ma dla wielkości, której `speed_limits` nie zawiera
- **Kontrola modelu:** żaden z 55 odcinków nie jest nierealizowalny przy fizyce
  z T-310/T-311; rezerwa rozkładowa 4,3–45,3 s, mediana 10,7 s

## Geometria

### [x] T-210 · Tunele z prawdziwych osi — pakiety A, B i E
- **Wyjście:** `tools/blender/sweep.py` + `tunnel_sweep.py`, `tools/ci/tunnel_alignment.sh <ID_OSI>`,
  `reports/L1_A-geometry.md`, `reports/L1_A-chunks.md`, `reports/packages-BE-tunnels.md`
- **Wynik:** A 12 chunków / 6686,7 m, B 9 / 5083,5 m, E 17 / 9021,1 m; szczelina między
  chunkami, poziomami LOD i w bryle kolizyjnej 0,0000 mm w każdym pakiecie, zero normalnych
  na zewnątrz, zero szwów na peronie. Skrajnia M7 zmierzona wzdłuż całych osi obu torów:
  najgorszy luz 0,8999 m w pakiecie A (`reports/clearance-BE.md`)
- **Wybór pakietów:** tylko te, którym żadne z dwóch niezależnych źródeł nie zarzuca
  zamkniętej rury na odcinku poza tunelem (`reports/surface-vs-tunnel.md`). C czeka na
  decyzję właściciela (8,6 % poza tunelem), D i F na model odcinka poza tunelem
- **Uwaga:** wyłącznie wariant `flat-preview` — profil pionowy czeka na T-112

### [ ] T-211 · Zestaw wspólny elementów stacji — **ZABLOKOWANE**
- **Blokada:** brak długości i wysokości peronów, wyjść i komunikacji pionowej (R-004)
- **Zależy od:** T-010, R-004, R-005

### [ ] T-212 · Pierwsza stacja typowa — **ZABLOKOWANE**
- **Zależy od:** T-211 (samo zablokowane), T-210

### [x] T-220 · Bryła zewnętrzna M7
- **Wyjście:** `tools/blender/m7_shell.py`, `m7_layout.py`, `reports/M7-shell.md`
- **Wynik:** 94,0 m, 6 członów, 18 drzwi podwójnych na stronę; skrajnia w tunelu zmierzona
  na siatce i wzorem, zgodność 3,9 mm (`reports/M7-in-tunnel.md`)
- **Uwaga:** bez wózków — rozstaw czopów skrętu nie ma źródła

## Symulacja

### [x] T-310 · Trakcja i opory ruchu
- **Wejście:** `docs/02-simulation.md`, `tools/physics/reference.py`
- **Wyjście:** `src/Sim/Physics/`, `reports/T-310-physics.md`, workflow `sim-tests.yml`
- **Wynik:** parytet z modelem referencyjnym **co do bitu**; zero zależności NuGet;
  nic w `src/Sim/` nie importuje Godota
- **Zależy od:** nic

### [ ] T-311 · Hamowanie — **ODBLOKOWANE, następne w kolejce**
- **Stan:** `TrainController` z T-400 ma hamulec jako **polecenie** — zadane opóźnienie
  z ograniczeniem zrywu, niezależne od masy i przyczepności. To jest świadome
  uproszczenie, nie model hamulca
- **Zostaje:** udział hamulca ED i pneumatycznego, zależność od masy i przyczepności,
  krzywe bezpieczeństwa
- **Uwaga:** `docs/02-simulation.md` daje wartości projektowe (1,10 m/s² służbowe,
  1,30 awaryjne, zryw 0,75 m/s³). Rozdziału ED/P i charakterystyk nie ma w rejestrze
  źródeł — czego nie da się potwierdzić, ma zostać `design_assumption`
- **Zależy od:** T-310

### [ ] T-312 · Drzwi i czas postoju
- **Zależy od:** T-310

### [ ] T-313 · Sygnalizacja klasyczna
- **Zależy od:** T-311

### [ ] T-314 · CBTC + ATS jako osobny tryb
- **Wejście:** zweryfikowany stan wdrożenia z `sources.json`
- **Skończone, gdy:** tryb CBTC nie jest aktywny w scenariuszu historycznym 31.08.2026 bez potwierdzenia pełnego uruchomienia STIB
- **Zależy od:** T-313

### [ ] T-320 · Rdzeń linii — wiele składów naraz
- **Zależy od:** T-313, T-113

## Silnik

### [~] T-400 · Scena Godota i pierwszy przejazd
- **Zrobione (etap 1):** `src/Game/` — Godot 4.3 mono, jeden skład M7 jedzie 6,56 km po
  pakiecie A, napędzany rdzeniem. Rozjazd Godot ↔ rdzeń **0,000 m** przy progu 0, ten sam
  odcisk telemetrii przy nierównym podziale kroków. `reports/T-400-first-run.md`
- **Zostaje:** wiele składów (T-320), postoje i drzwi (T-312), sygnalizacja (T-313),
  stacje (T-212), streamowanie chunków, przełączanie LOD
- **Uwaga:** scena wczytuje **jeden** pakiet. Przy `vertical.status = not_modelled` cała
  sieć leży na Z = 0, więc pakiety A i E przenikają się w planie w rejonie Arts-Loi
  (`reports/network-chainage.md`) — sceny z dwoma pakietami nie da się zbudować uczciwie
  przed T-112
- **Zależy od:** T-210 (zrobione), T-212, T-320

## Zadania dla człowieka

### [ ] **[CZŁOWIEK]** T-901 · Głębokości stacji pakietu A
Wypełnić `data/network/station-depths.csv`; agent nie zgaduje.

### [ ] **[CZŁOWIEK]** T-902 · Kierunek artystyczny tunelu

### [ ] **[CZŁOWIEK]** T-903 · Kontakt ze STIB w sprawie marki/oznaczeń/sztuki

### [x] **[CZŁOWIEK]** T-904 · Weryfikacja parametrów M7
Wynik w `docs/08-m7-ground-truth.md` i `data/vehicle/m7-spec.json`; siedem wartości
ze statusem `spec`, reszta wymiarów pojazdu to jawne założenia projektowe.

### [ ] **[CZŁOWIEK]** T-905 · Nagrania dźwiękowe

## Czego brakuje w tej rozpisce

Poniższe zadania istnieją jako Issues, ale nie mają tu wpisu. Dopóki go nie mają,
**Issues są jedynym źródłem prawdy** o ich zakresie:

- **T-114** — proweniencja pobranych danych (`tools/data/provenance.py`, `docs/09`), **zrobione**;
- **R-002 … R-005** — ground truth źródeł, sygnalizacji, stacji i infrastruktury torowej;
- **T-901** — rzędne i głębokości pakietu A, blokuje T-112.

## Co blokuje co, w jednym miejscu

| brakująca dana | blokuje | gdzie szukać |
|---|---|---|
| rzędne główki szyny, głębokości stacji | T-112 → produkcyjny tunel | T-901, `data/network/station-depths.csv` |
| długości i wysokości peronów, wyjścia | T-211 → T-212 | R-004 |
| przekrój tunelu, geometria toru, trzecia szyna | wiarygodność wymiarów w `profiles.py` | R-005 |
| rozstaw czopów skrętu M7 | pełna skrajnia kinematyczna | brak źródła publicznego |
| rzędne główki szyny (ta sama co wyżej) | scena z **dwoma** pakietami — przy Z = 0 rury A i E przenikają się w rejonie Arts-Loi | T-901 |
| odcinki międzypakietowe (4034 m) | przejazd całą linią; kilometraż nie jest ciągły | decyzja właściciela o zakresie pakietów |
| znaczenie `niveau = 0` dla pakietów C, D i F | tunele tych pakietów | **rozstrzygnięte pomiarem** w `reports/surface-vs-tunnel.md`; zostaje decyzja, co budować zamiast rury |

Zmierzone alternatywy dla wymiarów projektowych i powody, dla których **nie zostały
podstawione do kodu**: `docs/21-measured-vs-assumed.md`.
