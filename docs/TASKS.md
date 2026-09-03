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

### [ ] T-212 · Pierwsza stacja typowa — **ZABLOKOWANE tylko przez T-211**
- **Stan:** blokada danych zdjęta przez R-007; zostaje kolejność zadań
- **Zależy od:** T-211 (odblokowane, ale niezrobione), T-210 (zrobione)

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
- **Zrobione (etap 1):** `src/Game/` — Godot 4.3 mono, jeden skład M7 jedzie 6,56 km po
  pakiecie A, napędzany rdzeniem. Rozjazd Godot ↔ rdzeń **0,000 m** przy progu 0, ten sam
  odcisk telemetrii przy nierównym podziale kroków. `reports/T-400-first-run.md`
- **Zrobione (etap 2):** zrzuty z silnika idą przez kontrolę wizualną z T-012,
  odtwarzalne co do bajtu również między maszynami (`reports/T-012-godot-capture.md`)
- **Zrobione (etap 3, część 1):** scena zatrzymuje się na stacjach. `--drive=line`
  prowadzi `LineDrive` z rdzenia — ten sam kod, co `Sim.Runner line` — więc skład staje
  na KAŻDEJ stacji i odbywa pełny cykl drzwi z T-312. HUD pokazuje fazę drzwi.
  Bramka CI czyta raport przejazdu i porównuje liczbę zatrzymań z liczbą stacji oraz
  błąd każdego zatrzymania z oknem, plus kontrola negatywna psująca raport
- **Zostaje:** wiele składów (T-320 `LineCore` jest w rdzeniu, scena go nie woła),
  sygnalizacja (T-313), stacje (T-212 jest w geometrii, scena jej nie wczytuje),
  streamowanie chunków, przełączanie LOD
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
- **R-002 … R-007** — ground truth źródeł, sygnalizacji, stacji, infrastruktury torowej,
  prędkości dopuszczalnej i wymiarów peronu. **R-003, R-004, R-005, R-006 i R-007 są
  w `main`** (#34, #90, #35, #85, R-007);
- **T-401** — przejazd linii z zatrzymaniem na każdej stacji, **zrobione** (#82):
  49 z 49 odcinków sieci dopasowanych, na żadnym model nie jest wolniejszy od rozkładu
  przy 72 km/h; dolne ograniczenie prędkości liniowej rośnie z 57,65 do **58,75 km/h**
  (`reports/T-401-line-run.md`);
- **T-901** — rzędne i głębokości pakietu A, blokuje T-112.

## Co blokuje co, w jednym miejscu

| brakująca dana | blokuje | gdzie szukać |
|---|---|---|
| rzędne główki szyny, głębokości stacji | T-112 → produkcyjny tunel | T-901, `data/network/station-depths.csv` |
| ~~długość i wysokość peronu~~ | ~~T-211~~ → T-212 | **rozstrzygnięte przez R-007**: wysokość 1,03 m `source_backed`, długość zostaje `unknown`, ale generator ma jawny parametr 94,0 m i kontrolę górną 109,1 m |
| przekrój tunelu, geometria odbioru prądu | wiarygodność wymiarów w `profiles.py` | R-005 jest w `main`: 1435 mm to `secondary_reference_only`, `contact_geometry` = `unknown` |
| ~~ground truth sygnalizacji, CBTC, ATS, KCV~~ | ~~T-313~~ → T-314, T-320 | **odblokowane** — R-003 w `main` (#34), T-313 zrobione (#91) |
| prędkość dopuszczalna na torze | T-320; `speed_limits` puste we wszystkich osiach | **rozstrzygnięte przez R-006 (#85): źródła nie ma.** 72/50 km/h pochodzi z notatki DH z 11.02.2008 o sieci sprzed układu z 2009 — klasa `manufacturer_or_trade_press`, poniżej OSM. Ograniczenie dolne z T-401: 58,75 km/h |
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

### Faza 4 — T-400 etap 3 · W TOKU

Wpiąć w scenę to, co **już jest w rdzeniu i przetestowane, a scena tego nie woła**.

- **`DoorCycle` i `StationStop`: zrobione 03.09.2026** przez `--drive=line`, które prowadzi
  `LineDrive`. Scena nie liczy przy tym ani jednej rzeczy sama — bramka
  `test_the_scene_line_mode_is_driven_by_the_core_not_by_the_scene` tego pilnuje, bo dwie
  fizyki jazdy w jednym repozytorium znaczyłyby, że nie wiadomo, która jest prawdziwa;
- **`FixedBlockSystem` i `TrainProtection`:** zostaje. Wymaga `LineCore` w scenie, czyli
  wielu składów — a to dotyka turnbacku, który jest decyzją właściciela (T-320, STOP);
- **streamowanie chunków i przełączanie LOD:** zostaje;
- **stacje z T-212:** zostaje — geometria jest, scena jej nie wczytuje.

### Czego agent nie ruszy bez decyzji

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

- `CLAUDE.md` §2 mówi „**25 testów narzędzi**". Jest **691**. Liczba pochodzi z czasów,
  gdy `test_all.py` był jednym plikiem; dziś zbiera 30 modułów.
- Dziesięć Issues jest otwartych, choć zadanie leży w `main` (#9, #15–#17, #20–#24, #27).
  Ten plik deklaruje Issues źródłem prawdy o statusie, więc rozjazd jest realny.
  Część z nich właściciel poprosił, żeby zostawić otwarte.
