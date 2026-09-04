# Rozpiska zadań

`[ ]` do zrobienia · `[x]` zweryfikowane · **[CZŁOWIEK]** nie dla agenta.

**Źródłem prawdy o statusie są GitHub Issues**, nie ten plik. Ten plik jest mapą
zależności i zakresów. Statusy poniżej odzwierciedlają to, co **realnie leży w repo**
na dzień 02.09.2026, po scaleniu #34, #35, #80–#98 oraz #101–#116 — zadanie jest odhaczone
tylko wtedy, gdy jego artefakty istnieją w `main` i przechodzą CI.

**Kolejność prac jest na dole tego pliku**, w sekcji „Plan". Tam też jest lista rzeczy,
których agent nie ruszy bez decyzji właściciela.

## Gotowe w szkielecie
- `[x]` **T-100** — walidator osi trasy
- `[x]` **T-001** — profile przekrojów z kontrolą skrajni M7
- `[x]` **T-002** — model referencyjny dynamiki M7
- `[x]` **T-003** — testy narzędzi

## Narzędzia

### [x] T-010 · Pierwsze uruchomienie Blendera
- **Wyjście:** `tools/ci/blender_smoke.sh`, workflow `blender-smoke.yml`
- **Weryfikacja:** generacja → render → obejrzenie trzech PNG, plus cztery testy negatywne

### [x] T-011 · Rozstawianie detali wzdłuż osi
- **Wyjście:** `tools/track/detail_layout.py` (kilometraże, **0 założeń**),
  `tools/blender/detail_markers.py` (bryły, 4 założenia, każde wypisywane i sprawdzane),
  `tools/blender/placement.py` (`marker_clearances`, `axis_window`),
  `reports/T-011-detail-markers.md`
- **Wynik:** pakiet A — 89 miejsc na 6686,4 m osi: 66 hektometrów co 100 m, 12 stacji
  ze `stop_id`, 11 punktów hamowania liczonych solverem z T-311 (72 km/h → 196,39 m)
- **Uwaga:** `--brake-from-kmh` **nie ma wartości domyślnej** — prędkość dopuszczalna
  na torze nie ma źródła (R-006). Bez niej narzędzie nie stawia punktów hamowania,
  a `braking_distance_m` wychodzi `None`, nie `0.0`
- **Zależy od:** T-010

### [x] T-012 · Zrzuty kontrolne i wykrywanie regresji
- **Wyjście:** `tools/visual/` (manifest kamer `cameras.json`, render, metryki, porównanie),
  `src/Game/FirstRun.cs` (zrzuty z silnika + `GODOT_metadata.json`),
  `docs/17-visual-regression.md`, `reports/T-012-godot-capture.md`
- **Wynik:** zrzuty z Godota idą przez tę samą kontrolę co rendery Blendera. Odtwarzalne
  **co do bajtu** między przebiegami i między maszynami — pięć plików z runnera GitHuba
  ma te same rozmiary co z kontenera. Odróżnia to zrzuty od eksportu glTF, który
  odtwarzalny bajtowo **nie jest**
- **Uwaga:** bbox sceny trafia do metadanych i jest porównywany liczbowo, bo metryka
  obrazowa nie wykryje przesunięcia całej sceny — kamera jedzie razem z nią
- **Zależy od:** T-400 (część Godotowa)

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
- **Ruszyło się przy R-007:** EIE Métro 3 (Livre III Colignon) podaje głębokości peronów
  **trzech** stacji pakietu A — De Brouckère i Arts-Loi ok. 11 m, Parc 19 m — wpisane do
  `station-depths.csv` ze statusem `estimated` i notatką o dwóch przekształceniach
  (peron → główka szyny, oraz „environ" w zdaniu porównawczym, nie w tabeli pomiarowej).
  **To nie odblokowuje zadania:** trzy z dwunastu stacji nie dają profilu, a Schuman
  zostaje pusty, bo 15 m potwierdza jedną stronę konfliktu. Znane jest za to górne
  ograniczenie na całą sieć: **21,5 m** (Botanique, najgłębsza stacja)
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

### [x] T-211 · Zestaw wspólny elementów stacji
- **Wejście:** `data/track/L1_A.json`, `data/vehicle/m7-spec.json`,
  `reports/R-007-platform-dimensions.md`
- **Wyjście (etap 1):** `tools/track/station_layout.py`,
  `tools/tests/test_station_layout.py`, `reports/T-211-station-layout.md`
- **Wyjście (etap 2):** `tools/blender/station_kit.py`, `tools/tests/test_station_kit.py`
- **Weryfikacja:** `python3 tools/tests/test_all.py`; osiem kontroli negatywnych etapu 1
  i siedem etapu 2, każda wypisana w commicie. Etap 2 scalony w #110
- **Wynik:** 12 peronów pakietu A z kilometrażem, promieniem lokalnym i **policzoną
  dolną granicą odsunięcia krawędzi** (pół szerokości M7 + strzałka cięciwy członu).
  Najciaśniej Gare Centrale: R = 137 m daje strzałkę 22,5 cm, więc krawędź musi odsunąć
  się o 1,5748 m zamiast 1,35 m. Rozpiętość między najprostszym a najciaśniejszym
  peronem to **22,4 cm** — dość, żeby peron zaprojektowany na prostej wchodził
  w kolizję na łuku
- **Znalezisko:** `platform_edge_x` z profilu `station` **nie jest krawędzią peronu**.
  Przy torach na ±2,10 m i krawędziach na ±4,05 m szczelina peron–pudło wychodzi
  **0,600 m**, bo 1,95 = 1,35 + 2 × `CLEARANCE_M`. To granica skrajni; nazwa pola myli.
  Nic w repo tego pola nie czytało
- **Świadomie nie zrobione:** szczelina peron–pudło nie dostała wartości —
  `--platform-gap-m` nie ma domyślnej, bo R-007 ustalił, że nie podaje jej żadne
  źródło. Bez niej `edge_offset_m` wychodzi `None`, nie zero
- **Zostaje (etap 2):** bryły w Blenderze — płyta peronu, krawędź, komora stacyjna,
  z renderem kontrolnym. Wtedy też `platform_height_m` w profilu `station` (1,05 → 1,03;
  **1,05 to wysokość podłogi M6**, nie M7) i nazwa `platform_edge_x` — obie zmieniają
  geometrię tunelu i muszą przejść przez `tunnel-alignment.yml`
- **Poza zakresem:** wyjścia, komunikacja pionowa i wnętrza — rejestr R-004 ma je
  jako `unknown` i `docs/11` zabrania liczenia wind z listy wyjść
- **Zależy od:** T-010, R-004 (zrobione), R-005 (zrobione), R-007 (zrobione)

### [ ] T-212 · Pierwsza stacja typowa — **ODBLOKOWANE**
- **Stan:** blokada danych zdjęta przez R-007 (wysokość peronu 1,03 m `source_backed`),
  blokada zadaniowa zdjęta przez T-211 — oba etapy scalone (#110). Zostaje kolejność:
  faza 3 planu, po T-320
- **Zależy od:** T-211 (zrobione), T-210 (zrobione), R-007 (zrobione)

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

### [x] T-311 · Hamowanie — sufit przyczepnościowy i solver punktu hamowania
- **Wyjście:** `src/Sim/Physics/{BrakingAssumptions,BrakeAdhesionLimit,BrakingPointSolver,BrakingEnergyAccount}.cs`,
  `src/Sim/Train/BrakingRun.cs`, `tools/physics/braking.py`, `reports/T-311-braking.md`,
  `docs/02-simulation.md` §Hamowanie, `docs/21-measured-vs-assumed.md` §4b
- **Wynik:** sufit `b_max = μ·f·g/λ`, wzór zamknięty `s(b)` i jego odwrotność, bilans
  energii. Zgodność rdzenia C# z niezależną referencją Pythona **co do bitu**; przejazd
  z T-400 został co do bitu (3023 kroków / 337,478 m dla AW0, 3998 / 447,920 m dla AW2)
- **Świadomie nie zrobione:** rozdział hamulca ED i pneumatycznego — rejestr nie ma
  proporcji, a model dzielący siłę bez źródła wygląda tak samo jak model prawdziwy.
  Udział osi hamowanych jest jawnym parametrem o dwóch wariantach skrajnych, nie liczbą
- **Zależy od:** T-310

### [x] T-312 · Drzwi i czas postoju
- **Wyjście:** `src/Sim/Train/{DoorCycle,StationStop}.cs`, `reports/T-312-doors.md`,
  `docs/21-measured-vs-assumed.md` §4c
- **Wynik:** `MinimumDwellSeconds` = 8,5 s jako **suma pięciu faz stałych**, nie osobna
  stała; trakcja wolna wyłącznie w fazie `Closed`, sprawdzane wyliczeniowo dla każdej fazy
- **Świadomie nie zrobione:** czas wymiany pasażerów **nie dostał wartości** — jest
  argumentem konstruktora, bo nie ma go w żadnym źródle. `DoorCycle` nie ma konstruktora
  bezargumentowego, żeby kod wolał nie skompilować się niż podstawić zmyśloną liczbę.
  T-113 daje dla niego ograniczenie **górne** (≤ 10,5 s przy medianowym postoju), nie wartość
- **Zależy od:** T-310

### [x] T-313 · Sygnalizacja klasyczna
- **Wyjście:** `src/Sim/Signalling/`, `data/design/signalling/classic-2026.json`,
  `docs/15-classic-signalling.md`
- **Wynik:** 23 bloki na 6733,35 m pakietu A — 12 peronowych (11 po 94,0 m, pierwszy
  przycięty do 47 m) i 11 szlakowych 220,93–1125,00 m, mediana 497,47 m. Najkrótszy
  blok szlakowy mieści drogę hamowania z 72 km/h (220,93 m wobec 196,39 m), pilnuje
  tego osobny test. ATP korzysta z krzywej hamowania T-311, nie z drugiej fizyki
- **Plan jest wynikiem reguły, nie tabelką:** `SignallingPlan.FromAxis` wykonuje regułę
  (blok peronowy długości składu wyśrodkowany na kilometrażu stacji, między peronami
  dokładnie jeden blok szlakowy), a test przypina do niej plik — kod nie zna ani jednej
  granicy bloku
- **Świadomie zostawione jako `design_model`:** granice bloków, prędkość dopuszczalna,
  zapas za końcem authority, logika konfliktu tras i czasy reakcji urządzeń. Ground truth
  R-003 wprost mówi w `unknown_parameters`, że STIB ich nie publikuje
- **Zależy od:** T-311 (zrobione), R-003 (zrobione)

### [x] T-314 · CBTC + ATS jako osobny tryb
- **Wejście:** `data/signalling/ground-truth.json` (R-003), `data/track/L1_A.json`
- **Wyjście:** `src/Sim/Signalling/{ProtectionMode,CbtcTestArea}.cs`,
  `data/design/signalling/cbtc-test-2026.json`, `docs/16-protection-modes.md`
- **Weryfikacja:** `dotnet test tests/Sim.Tests` → `Passed: 277, Failed: 0` (przed: 259)
- **Wynik:** cztery tryby z rejestru R-003, dokładnie jeden z `historical_default`.
  `ForHistoricalDate(2026-08-31)` daje `classic_2026`, bo `cbtc_lines_1_5_full_service`
  jest `false` — odpowiedź jest **czytana z danych**, nie zakodowana. Poza `as_of`
  rejestr odmawia, bo o roku 2027 repo ma tylko **plany**, a plan nie jest dowodem
  uruchomienia. Dwie drogi do trybu rozdzielone celowo: `ForHistoricalDate` nie umie
  włączyć CBTC, `Named` daje dowolny tryb do scenariuszy „co by było gdyby",
  `RequireHistorical` jest strażnikiem. Strefa testowa Erasme–Stockel opisana
  **nazwami stacji**, nie kilometrażem; rzut na pakiet A daje `[0,00, 6686,74)`
  z dwiema flagami przycięcia, bo żadnej z tych stacji na pakiecie A nie ma
- **Świadomie nie zrobione:** movement authority po CBTC, bufor ochronny, krzywe ATO,
  protokół radiowy, parametry baliz, tryby awaryjne, ATS. Wszystko to jest
  w `unknown_parameters` ground truth. Listy `design_model_required` przy trybach CBTC
  zostają niepuste i osobny test tego pilnuje — wyczyszczenie ich wyglądałoby jak
  ukończenie pracy. Rozpoczęcie testów przy Beekkant zostaje **etykietą**
  `started_late_may_2026`, nie datą: źródło podaje miesiąc, nie dzień
- **Poza zakresem:** implementacja ATS jako warstwy dyspozytorskiej — `ats_transition`
  mówi wprost, że ATS nie ma prawa omijać ochrony pociągu, więc warstwa trybów nie
  wystawia niczego, czym dałoby się prowadzić skład
- **Zależy od:** T-313 (zrobione), R-003 (zrobione)

### [~] T-320 · Rdzeń linii — wiele składów naraz — **W TOKU**
- **Zrobione (etap 1):** `LineDrive` — skład krokowany z zewnątrz. Ciało pętli przeniesione
  z `LineRun` bez zmiany kolejności; ślad co krok identyczny co do bajtu (PR #123)
- **Zrobione (etap 2):** `src/Sim/Line/LineCore.cs` — N składów na jednym zegarze, jednej
  osi i jednym planie bloków z T-313. Krok idzie w trzech fazach nad wszystkimi składami
  (wyjazdy → odczyt autorytetów ze stanu sprzed kroku → jazda i meldunek ruchu), przez co
  wynik nie zależy od kolejności zgłoszenia. Zmierzone na osi syntetycznej 0/600/1400/2000 m,
  takt 30 s: drugi skład przejeżdża pierwszy odcinek w 96,03 s wobec 50,37 s na pustej linii,
  staje 0,29 m przed blokiem zajętym przez poprzedzający i zostaje tam; **zero naruszeń
  autorytetu** w całym przebiegu
- **Decyzja modelowa podjęta po drodze (do rewizji przez właściciela):** skład, który stanął
  przed autorytetem, **stoi**, zamiast dopełzać do granicy. Bez tego `Command` przy prędkości
  zero daje pełną trakcję — zmierzone 0,30 m w 58 s i przekroczenie autorytetu o 1,1 mm.
  Warunek nie wnosi ani jednej liczby; do stacji podpełznąć nadal wolno, bo tam łapie okno
  zatrzymania
- **Zostaje:** takt i obiegi z T-113 (48 kursów naraz, 71 obiegów) — bez turnbacku nie da się
  ich domknąć, bo skład, który dojechał do ostatniej stacji, zajmuje peron na zawsze
- **Wejście z T-113:** takt 5:10 (L1/L5) i 5:40 (L2/L6), 48 kursów naraz w ruchu,
  71 obiegów pojazdów, rozkładowe czasy jazdy i postoju per odcinek (`build/timetable.json`)
- **Wejście z T-313:** plan bloków pakietu A, zajętość, movement authority i ATP
- **Wejście z T-314:** tryb scenariusza; dla 31.08.2026 zawsze `classic_2026`
- **Wyjście:** `src/Sim/Line/` — LineCore z wieloma składami; testy w `tests/Sim.Tests`
- **Weryfikacja:** `dotnet test tests/Sim.Tests`. Druga, niezależna droga do tych samych
  liczb to **zmierzony** rozkład z T-113 (jedyna sekcja `docs/21` w całości bez założeń):
  takt, liczba kursów naraz i liczba obiegów policzone przez LineCore mają się zgadzać
  z GTFS, a nie z niczym
- **Skończone, gdy:** LineCore prowadzi 48 kursów naraz na 71 obiegach z taktem 5:10
  i 5:40, bez kolizji w blokach z T-313, a odtworzony z niego rozkład mieści się
  w zmierzonych czasach jazdy i postoju
- **Poza zakresem:** widok w Godocie (to T-400 etap 3), pasażerowie, opóźnienia losowe
  bez modelu, ATO i ATS poza tym, co daje T-314
- **Zależy od:** T-313 (zrobione), T-113 (zrobione), T-314 (zrobione)
- **STOP:** logika turnback, model perturbacji i polityka dyspozytora **nie są opisane
  w żadnym dokumencie**. Agent zatrzymuje się i pyta, zamiast wybierać sam

## Silnik

### [~] T-400 · Scena Godota i pierwszy przejazd
- **Zrobione (etap 1):** `src/Game/` — Godot 4.7.2 mono, jeden skład M7 jedzie 6,56 km po
  pakiecie A, napędzany rdzeniem. Rozjazd Godot ↔ rdzeń **0,000 m** przy progu 0, ten sam
  odcisk telemetrii przy nierównym podziale kroków. `reports/T-400-first-run.md`
- **Zrobione (etap 2):** zrzuty z silnika idą przez kontrolę wizualną z T-012,
  odtwarzalne co do bajtu również między maszynami (`reports/T-012-godot-capture.md`)
- **Zrobione (etap 3a):** scena **streamuje** chunki i przełącza LOD. `TunnelView.Stream`
  zastąpił `LoadAll`; predykat okna i wybór poziomu liczy `StreamingPlan` (#174), scena
  go woła (#177). Zmierzone na pakiecie A, w trójkątach, co 50 m na całej osi 6686,7 m
  (134 próbki): rezydentne **22,6 % szczytowo i 14,9 % średnio** z 16 176 trójkątów
  pakietu, od 1 do 3 chunków z 12. Predykat jest przybity **z dwóch stron** — wzorcowa
  implementacja w Pythonie (`sweep`, `lod`) i runtime C# stoją przy jednej tablicy
  oczekiwań na 138 wierszach, oba kierunki jazdy, wszystkie 13 szwów trafione dokładnie
- **Zostaje:** wiele składów (T-320), sygnalizacja (T-313), stacje (T-212). Cykl drzwi
  jest w rdzeniu (T-312, `DoorCycle`), ale **scena go jeszcze nie woła** — przejazd
  nadal nie zatrzymuje się na stacjach
- **Uwaga:** scena wczytuje **jeden** pakiet. Przy `vertical.status = not_modelled` cała
  sieć leży na Z = 0, więc pakiety A i E przenikają się w planie w rejonie Arts-Loi
  (`reports/network-chainage.md`) — sceny z dwoma pakietami nie da się zbudować uczciwie
  przed T-112
- **Zależy od:** T-210 (zrobione), T-212, T-320

## Zadania dla człowieka

### [ ] **[CZŁOWIEK]** T-906 · Jedenaście progów w `clearance_profile.py`
`docs/24-clearance-profile-decisions.md`. Triaż 72 ocalałych mutacji tego modułu — najwięcej
w repozytorium — czeka na te odpowiedzi. Każde pytanie ma zmierzoną konsekwencję obu
odpowiedzi. Najpilniejsze: krawędzie 12 i 17 profilu `bore_single` mają `|ny| = 0,892173`,
czyli 0,0078 poniżej progu, który decyduje o tym, czy są stropem, czy ścięciem naroża.

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
- **R-002 … R-007** — ground truth źródeł, sygnalizacji, stacji, infrastruktury torowej,
  prędkości dopuszczalnej i wymiarów peronu. **R-003, R-004, R-005, R-006 i R-007 są
  w `main`** (#34, #90, #35, #85, R-007);
- **T-401** — przejazd linii z zatrzymaniem na każdej stacji, **zrobione** (#82):
  49 z 49 odcinków sieci dopasowanych, na żadnym model nie jest wolniejszy od rozkładu
  przy 72 km/h; dolne ograniczenie prędkości liniowej rośnie z 57,64 do **58,68 km/h**
  (`reports/T-401-line-run.md`);
- **T-901** — rzędne i głębokości pakietu A, blokuje T-112.

## Co blokuje co, w jednym miejscu

| brakująca dana | blokuje | gdzie szukać |
|---|---|---|
| rzędne główki szyny, głębokości stacji | T-112 → produkcyjny tunel | T-901, `data/network/station-depths.csv` |
| ~~długość i wysokość peronu~~ | ~~T-211~~ → T-212 | **rozstrzygnięte przez R-007**: wysokość 1,03 m `source_backed`, długość zostaje `unknown`, ale generator ma jawny parametr 94,0 m i kontrolę górną 109,1 m |
| przekrój tunelu, geometria odbioru prądu | wiarygodność wymiarów w `profiles.py` | R-005 jest w `main`: 1435 mm to `secondary_reference_only`, `contact_geometry` = `unknown` |
| ~~ground truth sygnalizacji, CBTC, ATS, KCV~~ | ~~T-313~~ → T-314, T-320 | **odblokowane** — R-003 w `main` (#34), T-313 zrobione (#91) |
| prędkość dopuszczalna na torze | T-320; `speed_limits` puste we wszystkich osiach | **rozstrzygnięte przez R-006 (#85): źródła nie ma.** 72/50 km/h pochodzi z notatki DH z 11.02.2008 o sieci sprzed układu z 2009 — klasa `manufacturer_or_trade_press`, poniżej OSM. Ograniczenie dolne z T-401: 58,68 km/h |
| rozstaw czopów skrętu M7 | pełna skrajnia kinematyczna | brak źródła publicznego |
| rzędne główki szyny (ta sama co wyżej) | scena z **dwoma** pakietami — przy Z = 0 rury A i E przenikają się w rejonie Arts-Loi | T-901 |
| odcinki międzypakietowe (4034 m) | przejazd całą linią; kilometraż nie jest ciągły | decyzja właściciela o zakresie pakietów |
| znaczenie `niveau = 0` dla pakietów C, D i F | tunele tych pakietów | **rozstrzygnięte pomiarem** w `reports/surface-vs-tunnel.md`; zostaje decyzja, co budować zamiast rury |

Zmierzone alternatywy dla wymiarów projektowych i powody, dla których **nie zostały
podstawione do kodu**: `docs/21-measured-vs-assumed.md`.

## Plan

Kolejność, w jakiej agent bierze zadania, gdy nikt nie stoi nad nim z poleceniem.
Puls z `docs/22-heartbeat.md` po pobudce sięga właśnie tutaj.

**Zasada porządkująca** wynika ze zdania przewodniego z `docs/01-architecture.md`:
*„Linia jest symulacją, która działa bez gracza. Kabina jest jednym z jej widoków."*
Z tego wynika kolejność, której nie da się odwrócić — **T-320 jest warunkiem koniecznym
dla Issue #26**, bo kabina bez działającej linii nie ma czego być widokiem.

**Zasada druga**, wyprowadzona z audytu mutacyjnego 02.09.2026: każde zadanie musi mieć
**dwie niezależne drogi do tej samej liczby**. Zielona bramka bez pokrycia jest gorsza
niż brak bramki, bo usypia.

### Faza 1 — dziury w weryfikacji · ZROBIONE 02.09.2026

Wykonana przed T-320 celowo, mimo że T-320 jest ciekawsze i ważniejsze
architektonicznie. Powód jest w liczbach: audyt znalazł **cztery zielone bramki, które
niczego nie sprawdzały**, i wszystkie cztery znalazła mutacja, nie czytanie kodu.

| co | jak było widoczne | gdzie |
|---|---|---|
| ujęcie `approach` pokazywało płaską ścianę | przechodziło progiem resztką refleksów | #109 |
| scena bez składu zostawiała CI zielone | metadane opisywały wyłącznie tunel | #111 |
| akumulator przepuszczał „1 krok zamiast 120" | telemetria próbkuje po liczniku kroków | #112 |
| bramka reguły 9 nie łapała `Game.Tests` | szukała nazwy projektu, nie ścieżki | #114 |

Pokrycie po fazie: **691 testów Pythona** (było 623), **289 testów rdzenia** (było 277)
i **23 testy warstwy silnika** (nie było żadnego). Moduły `tools/` bez testu: **2**
(oba z pokryciem integracyjnym), było 5.

### Faza 2 — T-320 LineCore · NASTĘPNA

Rdzeń bez Godota, bez estetyki, bez nowych danych o sieci — najbezpieczniejsza duża
praca do wykonania autonomicznie. Zakres i kryteria: wpis T-320 wyżej.

### Faza 3 — T-212 pierwsza stacja typowa

Po T-320. Blokada danych zdjęta przez R-007, T-211 scalone.

### Faza 4 — T-400 etap 3

Wpiąć w scenę to, co **już jest w rdzeniu i przetestowane, a scena tego nie woła**:
`DoorCycle`, `StationStop`, `FixedBlockSystem`, `TrainProtection`. Streamowanie chunków
i przełączanie LOD **wypadły z tej fazy, bo są zrobione** (#174, #177 — wpis T-400 wyżej).
Ta faza dotknie miejsc wymagających decyzji właściciela.

### Faza 5 — kolejka, która nie kończy się na czekaniu

Zadania poniżej **nie wymagają ani jednej decyzji właściciela**. Nie dotykają `data/`
zapisem, nie wymagają oceny estetycznej, nie ruszają `docs/03-legal.md` i nie potrzebują
danych, których repo nie ma. Agent bierze je w tej kolejności, gdy fazy 1–4 są zamknięte
albo gdy faza w toku czeka na cudzy przebieg CI.

Kolejność wynika z jednej zasady: **najpierw to, co może pokazać, że coś innego jest
nieprawdą.** Zadanie, które ujawnia błąd, jest warte więcej niż zadanie, które dokłada
funkcję do kodu, o którym nie wiadomo, czy działa.

| # | zadanie | dlaczego bez decyzji | jak się kończy |
|---|---|---|---|
| 5.1 | **Przegląd mutacyjny wszystkich bramek** — po jednej mutacji na każdą kontrolę w `tools/ci/*.sh` i `tools/tests/test_*.py`, z rejestrem, która przeżyła | audyt z 02.09.2026 znalazł **cztery zielone bramki, które niczego nie sprawdzały**, i wszystkie cztery znalazła mutacja, nie czytanie kodu. Do tego dwie kolejne w tej samej sesji (`RUNNER_TOOL_CACHE` w komentarzu, szczyt prędkości na osi bez ograniczenia). Sześć na sześć prób — to nie jest wyjątek, to stan | `reports/mutation-sweep.md` z listą bramek, mutacji i wyniku; każda ocalała mutacja to osobne zadanie naprawcze |
| 5.2 | **Świeże snapshoty STIB — raport różnic, bez zapisu do `data/`** | `data/` zostaje tylko do odczytu: pobranie idzie do `build/`, a wynikiem jest **diff**, nie podmiana. Decyzja, czy podmieniać, zostaje właścicielowi — ale bez raportu nie ma na czym jej oprzeć | `reports/snapshot-drift.md`: co się zmieniło w GTFS, `ACTU_LIGNES_BRUTES`, Stop Details i INSPIRE Rails wobec commitów w `data/`, z liczbami. INSPIRE Rails miał okno ważności **02.03–28.06.2026** i był wygaśnięty już w chwili pobrania 01.09.2026 |
| 5.6 | **Domknąć „Czego brakuje w tej rozpisce"** — T-114, R-002…R-007, T-401 mają Issues, ale nie mają wpisu tutaj | ten plik sam deklaruje, że dopóki wpisu nie ma, **Issues są jedynym źródłem prawdy** — czyli rozjazd jest zapisany, ale niezamknięty | sekcja znika, bo każde zadanie ma wpis z sześcioma polami |
| 5.7 | **Budżet kroków dla wielu składów** — ile kosztuje 120 Hz przy N składach na osi | czysty pomiar na istniejącym kodzie; nie wymaga ani jednej nowej liczby o sieci | `reports/linecore-budget.md`: kroki na sekundę wobec N, i przy jakim N krok stały przestaje się mieścić w klatce |
| 5.8 | **Pokrycie dwóch modułów `tools/` bez testu jednostkowego** | oba mają dziś wyłącznie pokrycie integracyjne, czyli takie, które mówi „przeszło", ale nie mówi, co dokładnie | testy jednostkowe z kontrolami negatywnymi, jak reszta |

#### Domknięte i zdjęte z kolejki

Pozycja zrobiona znika z tabeli wyżej, a jej wynik stoi w odpowiednim wpisie w tym pliku.
Tabela jest tu po to, żeby numer, który kiedyś istniał, nie wyglądał na zgubiony.

**Licznik zapasu tej sekcji NIE liczy** i pilnuje tego `tools/tests/test_backlog.py`.
Bez tego wykluczenia domknięcie pozycji podnosiłoby zapas zamiast go obniżać: wiersz
`| 6.C1 | ... |` wygląda dla parsera dokładnie tak samo, niezależnie od tego, w której
tabeli stoi. Zmierzone przy pisaniu tej sekcji — licznik pokazywał 28 przy 25 pozycjach
realnych.

| # | co było | gdzie zostało zrobione |
|---|---|---|
| 5.3 | T-401 zmierzone tylko na L1_A, i to na kilometrażach przed #86 | `reports/T-401-line-run.md` §3 i §4 przeliczone 04.09.2026 na sześciu pakietach: 49 z 49 odcinków dopasowanych, 0 wolniejszych, wszystkie sześć odcinków wiążących identycznych z pierwszą wersją. §3a dokumentuje, że stare liczby były sprzed #86, z bisekcją po commitach i metodą wyszukiwania limitu zapisaną wprost |
| 5.4 | ten sam blok preflightu w dziesięciu workflowach (kontrola czystego workspace) i w siedmiu (sonda narzędzi) | `.github/actions/check-workspace` i `.github/actions/probe-tools`; **warunek odrzucający forki ZOSTAJE w każdym jobie** i nie mógł się przenieść — akcja lokalna uruchamia się dopiero po checkoucie, czyli gdy kod z forka już leży na maszynie. Utrzymanie pilnują `test_no_workflow_reinlines_what_the_local_actions_now_own` i `test_the_local_actions_carry_the_rule_they_took_over` |
| 5.5 | akcje GitHuba przypięte po tagu, nie po SHA | wszystkie cztery `uses:` mają pełny SHA i komentarz z wersją; pilnują tego `test_ci_workflows.py::test_every_action_is_pinned_to_a_commit_not_a_moving_tag`, `..._every_pinned_action_says_which_version_the_commit_is` i `..._the_same_action_is_pinned_to_the_same_commit_everywhere` |
| 6.C1 | scena wczytywała wszystkie chunki naraz | #174 (predykat i LOD po stronie sceny), #177 (`TunnelView.Stream` zamiast `LoadAll`) — wpis T-400, etap 3a |
| 6.C2 | poziomy LOD istniały, scena ich nie używała | to samo, `StreamingPlan.LodPlan`; przybite tablicą oczekiwań wspólną dla Pythona i C# |

**Czego w tej kolejce świadomie NIE ma:** wszystkiego, co wymagałoby wymyślenia liczby
o brukselskim metrze. Zmyślona głębokość stacji wygląda dokładnie tak samo jak prawdziwa,
a zadanie „na przeczekanie" jest najgorszym momentem, żeby o tym zapomnieć.

**Cztery z tych ośmiu są generatorami, nie pozycjami.** 5.1 daje jedno zadanie naprawcze
na każdą ocalałą mutację, 5.2 jedno na każdy wykryty rozjazd danych, 5.3 jedno na każdy
odcinek, gdzie model nie mieści się w rozkładzie, 5.8 jedno na każdy moduł bez pokrycia.
Ile ich będzie, wiadomo dopiero po wykonaniu — i **to jest właściwa własność kolejki**:
kolejka złożona z samych pozycji stałych wyczerpuje się z definicji.

### Reguła zapasu

> **Agent nigdy nie ma mniej niż 24 godziny pracy przed sobą. Uzupełnienie zapasu jest
> zadaniem samo w sobie i ma pierwszeństwo przed zatrzymaniem się.**

Powód nie jest wydajnościowy, tylko taki: agent, który skończył kolejkę, ma do wyboru
stanąć albo **wymyślić sobie zadanie na miejscu**. Drugie jest gorsze, bo zadanie
wymyślone w pośpiechu omija format z sekcji 6 `CLAUDE.md` i zwykle ląduje w miejscu,
które akurat wygląda na niedokończone — czyli w kodzie, którego nikt nie prosił o zmianę.

Mechanika:

1. Przed wzięciem zadania agent liczy **niezrobione** pozycje w fazie 5 i 6.
2. Poniżej **dwunastu** pierwszym zadaniem jest uzupełnienie fazy 6 — nowe pozycje muszą
   mieć wszystkie sześć pól z `docs/TASK-TEMPLATE.md` i kolumnę „dlaczego bez decyzji".
3. Pilnuje tego `tools/tests/test_backlog.py`; bramka jest czerwona, gdy zapas spadnie
   poniżej progu, więc nie da się tego przeoczyć między sesjami.
4. Zadanie, którego nie da się zrobić bez decyzji, **nie liczy się do zapasu** i wędruje
   do sekcji „Czego agent nie ruszy bez decyzji".

Szacunki godzin niżej są zgrubne i celowo podane jako przedziały. Podstawa: w sesji
02.09.2026 jedno zadanie z pełną weryfikacją, przeglądem mutacyjnym, commitem i PR-em
zajmowało **20–45 minut**. Zadanie oznaczone `L` to takie, które ma więcej niż jeden
przyrost i kończy się osobnym PR-em na każdy.

### Faza 6 — zapas

Kolejność w obrębie pasma jest sugestią, nie zobowiązaniem. Pasma można przeplatać;
`docs/22-heartbeat.md` opisuje, kiedy agent w ogóle po tę listę sięga.

#### Pasmo A — rdzeń symulacji (`src/Sim`, bez Godota, bez nowych danych o sieci)

| # | zadanie | dlaczego bez decyzji | rozmiar |
|---|---|---|---|
| 6.A1 | **Autorytet jazdy w `LineDrive`** — skład pyta `FixedBlockSystem` o zajętość bloku przed sobą i hamuje przed zajętym | plan bloków jest **wynikiem reguły**, nie tabelką (T-313, `SignallingPlan.FromAxis`); ATP korzysta z krzywej T-311. Nic nowego do zgadnięcia | L |
| 6.A2 | **`LineCore`: N składów na wspólnym zegarze** z autorytetem z 6.A1 | takt 310 s / 340 s jest **zmierzony** z GTFS (T-113), nie założony | L |
| 6.A3 | **Odtworzenie doby służby z bloków GTFS** — 71 obiegów, maks. 56 równocześnie o 07:06:44 | wszystkie liczby zmierzone w T-113, leżą w `build/timetable.json` | L |
| 6.A4 | **Propagacja opóźnienia przy zmierzonym rozkładzie postojów** — co robi z taktem jeden skład spóźniony o 30 s | rozkład postojów jest **zmierzony** (29 554 zatrzymań, 12–45 s), więc perturbacja nie jest zmyślona; sama polityka reakcji dyspozytora zostaje poza zakresem | M |
| 6.A5 | **Bilans energii przejazdu z odzyskiem i bez** | model energii jest w rdzeniu od T-310; to pomiar na istniejącym kodzie | M |
| 6.A6 | **Wybieg zamiast trakcji: ile kosztuje w czasie, ile oszczędza w energii** | czysty eksperyment na modelu, żadnych nowych danych | M |
| 6.A7 | **Testy własnościowe fizyki** — monotoniczność drogi hamowania po prędkości i masie, zachowanie energii, brak ujemnego czasu | wzmacnia to, co jest; nie dodaje ani jednej liczby o metrze | M |

#### Pasmo B — narzędzia i geometria (`tools/`)

| # | zadanie | dlaczego bez decyzji | rozmiar |
|---|---|---|---|
| 6.B1 | **`station_layout.py` na pakietach B–F**, dziś liczy tylko pakiet A | osie sześciu pakietów są w `data/track/`, wysokość peronu `source_backed` z R-007 | M |
| 6.B2 | **Znaczniki kilometrażu (T-011) na pozostałych pakietach** | to samo narzędzie, inne wejście | S |
| 6.B3 | **LOD tuneli pakietów B–F** | wzorzec z pakietu A, `reports/L1_A-lod.md` | M |
| 6.B4 | **Kontrola krzyżowa osi B–F wobec OSM**, jak `reports/L1_A-crosscheck.md` dla A | hierarchia źródeł rozstrzygnięta w `docs/07`; rozbieżności się **liczy i zapisuje**, nigdy nie uśrednia | M |
| 6.B5 | **Wykrywanie łuków o najmniejszym promieniu na każdej osi** i sprawdzenie skrajni M7 punkt po punkcie | metoda zmierzona i opisana (`reports/M7-curve-clearance.md`), zostaje zastosowanie | M |

#### Pasmo C — warstwa silnika (`src/Game`)

| # | zadanie | dlaczego bez decyzji | rozmiar |
|---|---|---|---|
| 6.C3 | **Odtwarzanie przejazdu z pliku telemetrii** — scena jako widok zapisanego przebiegu | wynika wprost z zasady „linia jest symulacją, kabina jednym z jej widoków" | M |
| 6.C4 | **Kamera inspekcyjna** do oglądania geometrii bez jazdy | narzędzie weryfikacji, nie decyzja estetyczna: nie zmienia ani jednego materiału | S |

#### Pasmo D — weryfikacja i CI

| # | zadanie | dlaczego bez decyzji | rozmiar |
|---|---|---|---|
| 6.D1 | **Wzorcowy ślad jako bramka CI** — to, co przy `LineDrive` robiłem ręcznie (453 107 wierszy, sześć osi, porównanie co do bajtu), ma chodzić samo przy każdej zmianie rdzenia | metoda sprawdzona i udowodniona kontrolą negatywną: próg przesunięty o 0,1 % daje rozjazd w wierszu 2910 | M |
| 6.D2 | **Bramka na czas przebiegu** — regres wydajności rdzenia widoczny, zanim zablokuje N składów | pomiar, nie decyzja | S |
| 6.D3 | **Kontrola, że każdy `reports/*.md` niesie commit i datę pomiaru** | konwencja już obowiązuje, brakuje bramki | S |
| 6.D4 | **Kontrola spójności liczb między `reports/` a kodem** — wartość wypisana w raporcie musi dać się odtworzyć z repo | dokładnie ta klasa rozjazdu, którą audyt znalazł w README | M |

**Aktualizacja tej listy jest częścią pracy, nie dodatkiem do niej.** Pozycja zrobiona
znika stąd i pojawia się jako wpis z sześcioma polami wyżej w tym pliku.

### Czego agent nie ruszy bez decyzji

Poniższe **nie są kolejką** — są listą rzeczy, które czekają na właściciela. Agent po nie
nie sięga, nawet gdy nie ma nic innego do roboty; wtedy sięga po fazę 5.

| | dlaczego |
|---|---|
| **T-901** głębokości stacji | 9 z 12 stacji pakietu A `unknown`; Schuman ma konflikt 15 m vs 17,42 m. Blokuje T-112, a przez to scenę z dwoma pakietami |
| **T-902** kierunek artystyczny | ocena estetyczna (`CLAUDE.md` §8) |
| **T-903** kontakt ze STIB | `docs/03-legal.md` |
| **T-905** nagrania | praca w terenie |
| **4034 m dziur** między pakietami | kilometraż nie jest ciągły; przejazd całą linią wymaga decyzji o zakresie |
| pakiety **C, D, F** bez tuneli | decyzja, co budować zamiast rury |
| **turnback, perturbacje, dispatcher** w T-320 | nie ma ich w żadnym dokumencie |

### Znane rozjazdy w dokumentach

- ~~`CLAUDE.md` §2 mówi „25 testów narzędzi"~~ — **zamknięte**: liczba zeszła z pliku,
  bo zaszywanie jej w konstytucji generowało rozjazd przy każdym nowym module.
  Dla porządku: `test_all.py` zbiera dziś **700** testów z 31 modułów.
- Dziesięć Issues jest otwartych, choć zadanie leży w `main` (#9, #15–#17, #20–#24, #27).
  Ten plik deklaruje Issues źródłem prawdy o statusie, więc rozjazd jest realny.
  Część z nich właściciel poprosił, żeby zostawić otwarte.
