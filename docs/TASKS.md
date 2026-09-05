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

### [x] T-212 · Pierwsza stacja typowa
- **Przepisane 05.09.2026, a nie dopisane obok.** Ten wpis stał do dziś jako `[ ]`
  z notatką „Stan: […] Zostaje kolejność: faza 3 planu, po T-320" — to nieprawda od
  **04.09.2026**, bo zadanie jest w `main` jako **#137** (`fe14d72`). Rozjazd nie był
  kosmetyczny: `doctor.sh` bierze **pierwszy niezahaczony wpis** `^### [ ]` z tego pliku,
  więc pierwszą rzeczą, jaką widziała nowa sesja, było „Następne zadanie: T-212 ·
  Pierwsza stacja typowa — **ODBLOKOWANE**", czyli polecenie zrobienia pracy, która już
  leży w `main`. Powód rozjazdu stoi w samym commicie `a665536`, w sekcji „Czego
  świadomie nie ma": „Wpisu T-212 w `docs/TASKS.md` — konflikt przebazowania na tym
  pliku rozwiązany na rzecz `main`". Pilnuje tego teraz `tools/tests/test_next_task.py`
- **Wejście:** `data/track/L1_A.json`, `build/L1_A-platforms.json` z `station_layout.py`,
  profil `station` z `tools/blender/profiles.py`, `reports/R-007-platform-dimensions.md`
- **Wyjście:** `tools/track/station_components.py` (cała matematyka, **ani jednej linii
  `bpy`**), `tools/blender/station_kit.py --component`,
  `tools/tests/test_station_components.py`, `reports/T-212-station.md`,
  `docs/21-measured-vs-assumed.md` §4e
- **Weryfikacja:** `python3 tools/tests/test_all.py` → **1455/1455** w chwili scalenia
  #137; sześć kontroli negatywnych wypisanych w `reports/T-212-station.md` §4, każda
  wykonana — pięć mutacją, szósta **wykonaniem generatora**, bo wołanie kontroli siedzi
  za `bpy` i żaden test Pythona go nie dosięga
- **Wynik:** zespół dostępu nad peronem — **37 brył, 596 wierzchołków, 522 ściany** na
  stacji Parc (`corridor=1, edge=2, lift=1, mezzanine=2, platform=2, portal=1,
  stairs=28`), peron **95,0 m** na 4028,2–4123,2 m, krawędź 1,4374 m od toru.
  Antresola idzie **nad stropem komory** (podłoga 5,70 m, sufit 8,30 m), bo nad peronem
  zostaje 4,27 m, a płyta 0,40 m i światło 2,60 m zostawiają górnemu poziomowi 1,27 m —
  poniżej wzrostu człowieka. Wznoszenie **4,67 m** to **27 stopni po 0,1730 m**; liczba
  stopni jest wynikiem podziału, nie wartością nominalną (przy nominalnych 0,17 m
  wychodziło 27,47 stopnia). **18 jawnych założeń projektowych** w
  `SC.DESIGN_ASSUMPTIONS`, **22 testy** modułu — przed T-212 warstwa brył stacji nie
  miała ani jednego
- **Kontrola R-007 jest w kodzie, nie w komentarzu:** `SC.DESIGN_PLATFORM_LENGTH_M` = 95,0 m
  (skład M7 94,0 m ze statusem `spec` plus metr zapasu, po 0,50 m na stronę)
  i `SC.TIGHTEST_STATION_FOOTPRINT_M` = 109,1 m (**pomiar** obrysu Parc z UrbIS, więc
  świadomie poza `DESIGN_ASSUMPTIONS`). `platform_fits_the_station()` woła
  `station_kit.py` **przed** zapisem GLB: peron 110 m kończy się odmową i brakiem pliku
- **Domknięte po #137 dwoma PR-ami i to jest część tego wpisu:** **#223** wstawił peron
  **do sceny Godota** — `StationView` wczytuje 48 brył pakietu A (3456 ścian, 294 kB)
  bez transformacji, `PlatformFit` mierzy je poza silnikiem (11 testów w
  `tests/Game.Tests`), brak pliku peronów **zatrzymuje przebieg** kodem 12, a
  `assert_shot_metadata.py` żąda **4 brył** przy zrzucie z Beekkant i **zera** przy
  zrzucie ze szwu c01/c02 między stacjami. **#225** doprowadził decyzję 95,0 m **do
  pipeline'u**: obaj wołający `station_layout.py` szli bez `--platform-length-m`, czyli
  na domyślnych 94,0 m, więc do sceny wchodziły perony długości składu (Beekkant
  462,73–556,73 m); po poprawce 462,23–557,23 m, a liczba mieszka w **jednym** miejscu,
  bo `--platform-length-m design` czyta 95,0 m z `SC.DESIGN_PLATFORM_LENGTH_M`
- **Świadomie nie zrobione:** w scenie stoją **wyłącznie** `platform` i `edge`. Schody,
  winda, antresola, korytarz i portal sięgają 8,30 m nad główkę szyny, a strop profilu
  `box_double`, którym zamiatany jest tunel pakietu A, stoi na 4,70 m — komora stacyjna
  nie jest jeszcze wstawiana w przebieg tunelu, więc te bryły przebijałyby strop.
  Poza tym: słupy, balustrady, bramki, kasy i rzut którejkolwiek brukselskiej stacji —
  układ jest **kanoniczny**, bo STIB nie publikuje rzutów, a UrbIS daje sam obrys
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
- **Zostaje (przepisane 05.09.2026, a nie dopisane obok):** takt i obiegi z T-113 —
  **48 kursów naraz na 71 obiegach**. Poprzednia wersja tego punktu dodawała „bez
  turnbacku nie da się ich domknąć, bo skład, który dojechał do ostatniej stacji,
  zajmuje peron na zawsze" i to już nieprawda: nawrót wszedł w **#218** na oba końce
  osi, a jego czas jest **zmierzony z GTFS STIB**, nie zmyślony — 194 obiegi,
  4289 nawrotów, minimum 240 s, mediana 445 s, **ani jednego poniżej 240 s**
  (`docs/21-measured-vs-assumed.md` §4f). Zostaje samo domknięcie taktu i obiegów
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
- **STOP (przepisany 04.09.2026):** model perturbacji i polityka dyspozytora **nie są
  opisane w żadnym dokumencie**. Agent zatrzymuje się i pyta, zamiast wybierać sam.
  **Turnback z tego STOP-u wyszedł** i dlatego ten punkt jest przepisany, a nie dopisany
  obok: czas nawrotu jest **zmierzony z GTFS STIB** (194 obiegi, 4289 nawrotów, minimum
  240 s, mediana 445 s, ani jednego poniżej 240 s — `docs/21-measured-vs-assumed.md` §4f),
  a sam nawrót jest w `LineCore` jako argument, którego zero wyłącza. Nawrót na Merode
  zostaje `design_assumption`, bo Merode nie jest krańcówką w żadnym źródle — to granica
  pakietu

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
- **Zrobione (etap 3b):** scena **zatrzymuje się na stacjach** (#210, #212). Poprzednia
  wersja tego punktu mówiła, że cykl drzwi „jest w rdzeniu, ale scena go jeszcze nie
  woła" — to już nieprawda i dlatego jest tu przepisana, a nie dopisana obok. Dwa widoki
  tej samej linii: tryb **ręczny** przez `StationService` (okno zatrzymania dwustronne,
  blokada trakcji, minięta stacja liczona osobno) i tryb **`--line`** przez `LineDrive`,
  czyli linia, która jedzie bez gracza. Zmierzone na pakiecie A: scena i rdzeń dają
  **11 zatrzymań i identyczne kolumny** (`chainage_m`, `stopped_at_m`, `stop_error_m`,
  `arrival_s`, `departure_s` — wszystkie max |Δ| = 0,000E+00), a przejazd trwa 733,14 s
  z postojami 181,59 s. Pilnuje tego `tools/ci/assert_line_calls_match.py` przy progu
  **zerowym**. Migawka z peronu Beekkant łapie skład o prędkości 0,0 km/h na 509,4 m
  z drzwiami w fazie `Open`
- **Zostaje (przepisane 05.09.2026, a nie dopisane obok):** **wiele składów (T-320)** —
  i tylko to. Poprzednia wersja wymieniała jeszcze dwie pozycje i obie przestały być
  prawdziwe. Pierwsza: „sygnalizacja w kabinie (T-313 jest w rdzeniu, ale HUD nie
  pokazuje ani prędkości dopuszczalnej, ani autorytetu jazdy)" — HUD pokazuje oba od
  **#215**, piątym wierszem `v_dop 72.0 km/h   autorytet 989 m (BlockNotReserved,
  blok S03)`, a od **#221** ochrona nie tylko pokazuje, lecz **wchodzi w polecenie**:
  pod limitem planu ślad jest identyczny **co do bitu**, a nad nim limit planu staje się
  faktycznym pułapem — 74, 76 i 80 km/h dają ten sam przejazd (94 060 kroków,
  4576 ostrzeżeń i 4576 ingerencji). Druga: „stacje jako geometria (T-212). **Na stacji
  nie ma dziś czego zobaczyć:** zrzut kabinowy z Beekkant to pusty tunel, bo peronu
  w scenie nie ma" — peron jest w scenie od **#223**, `StationView` wczytuje 48 brył
  pakietu A, a bramka zrzutów żąda **4 brył** przy Beekkant i **zera** przy szwie
  c01/c02 między stacjami
- **Uwaga:** scena wczytuje **jeden** pakiet. Przy `vertical.status = not_modelled` cała
  sieć leży na Z = 0, więc pakiety A i E przenikają się w planie w rejonie Arts-Loi
  (`reports/network-chainage.md`) — sceny z dwoma pakietami nie da się zbudować uczciwie
  przed T-112
- **Zależy od:** T-210 (zrobione), T-212 (zrobione), T-320

## Zadania dla człowieka

### [x] **[CZŁOWIEK]** T-906 · Jedenaście progów w `clearance_profile.py`
**Przepisane 05.09.2026, a nie dopisane obok.** Poprzednia wersja tego wpisu stała jako
`[ ]` i mówiła: „Triaż 72 ocalałych mutacji tego modułu — najwięcej w repozytorium —
czeka na te odpowiedzi". Nieprawdziwe są dziś obie połowy tego zdania.
- **Odpowiedzi padły 04.09.2026.** `docs/24-clearance-profile-decisions.md` ma **zero
  otwartych pozycji**: wszystkie trzynaście nosi nagłówek `ROZSTRZYGNIĘTE` albo
  `SKREŚLONE`. Pozycje 6, 7 i 8 rozstrzygnął właściciel, pozycje 1, 2, 3, 5, 9, 10 i 11
  poszły pod **pomiar** wypisany w dokumencie (#209), a pozycje 12 i 13 doszły i zostały
  rozstrzygnięte razem z nim (#207, #208)
- **Wynik:** triaż, który na te odpowiedzi czekał, jest wykonany —
  `tools/blender/clearance_profile.py` zszedł z **45 ocalałych mutacji na 76 do 17**
  (#206: dwadzieścia nowych testów zabiło 28 mutacji), po wcześniejszym etapie
  `reports/mutation-triage-clearance.md` (#128), który zszedł z **72 do 66**.
  „Najwięcej w repozytorium" przestało być prawdą przy tej samej okazji: największym
  zestawem ocalałych jest dziś `tools/blender/sweep.py` (**37**), czyli pozycja 6.B6
- **Świadomie zostaje do zrobienia w CI, i to nie jest decyzja właściciela:** minimum
  luzu 0,899948 m z pozycji 3 zmierzono przy kilometrażach sprzed #86, a ponowny skan
  wymaga Blendera **5.2.1** z przypięcia. `docs/24` §„Co z liczbami po #86" mówi wprost,
  że 52 µm z tej pozycji to rząd wielkości, nie przypięty pomiar
- ~~**Uwaga:** `reports/mutation-sweep.md` nadal wypisuje dla tego modułu **66 / 77** —
  ten przebieg jest z `66b8301` i **poprzedza** #206.~~ **Zdjęte 05.09.2026 i przepisane,
  a nie dopisane obok:** `reports/mutation-sweep.md` nosi dziś przy tym wierszu pomiar
  z `9f4ae98` — **77 mutacji, 61 zabitych, 16 ocalałych, 20,8 %** — obok liczby
  historycznej, wraz z powodem różnicy 16 wobec 17 z etapu trzeciego (`82cc22e`
  i `df36903` dołożyły jedną mutację i jedno zabicie). Pozostała część rozjazdu
  pokrycia mutacyjnego w `reports/` — jedenaście modułów poza `clearance_profile.py`
  — nadal należy do **6.D5**, którego zakres jawnie wyłącza ten moduł

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
| ~~długość i wysokość peronu~~ | ~~T-211~~ → ~~T-212~~ (oba zrobione) | **rozstrzygnięte przez R-007**: wysokość 1,03 m `source_backed`, długość zostaje `unknown`, ale generator ma jawny parametr 95,0 m (`DESIGN_PLATFORM_LENGTH_M`, decyzja właściciela T-212 z #137), między dolnym ograniczeniem 94,0 m — długością składu M7, nie parametrem — a kontrolą górną 109,1 m |
| przekrój tunelu, geometria odbioru prądu | wiarygodność wymiarów w `profiles.py` | R-005 jest w `main`: 1435 mm to `secondary_reference_only`, `contact_geometry` = `unknown` |
| ~~ground truth sygnalizacji, CBTC, ATS, KCV~~ | ~~T-313~~ → T-314, T-320 | **odblokowane** — R-003 w `main` (#34), T-313 zrobione (#91) |
| prędkość dopuszczalna na torze | T-320; `speed_limits` puste we wszystkich osiach | **rozstrzygnięte przez R-006 (#85): źródła nie ma.** 72/50 km/h pochodzi z notatki DH z 11.02.2008 o sieci sprzed układu z 2009 — klasa `manufacturer_or_trade_press`, poniżej OSM. Ograniczenie dolne z T-401: 58,68 km/h |
| rozstaw czopów skrętu M7 | pełna skrajnia kinematyczna | brak źródła publicznego |
| rzędne główki szyny (ta sama co wyżej) | scena z **dwoma** pakietami — przy Z = 0 rury A i E przenikają się w rejonie Arts-Loi | T-901 |
| odcinki międzypakietowe (4034 m) | przejazd całą linią; kilometraż nie jest ciągły | decyzja właściciela o zakresie pakietów |
| znaczenie `niveau = 0` dla pakietów C, D i F | tunele tych pakietów | **rozstrzygnięte pomiarem** w `reports/surface-vs-tunnel.md`; zostaje decyzja, co budować zamiast rury |

Zmierzone alternatywy dla wymiarów projektowych i powody, dla których **nie zostały
podstawione do kodu**: `docs/21-measured-vs-assumed.md`.

**Jeśli trafiłeś do tej tabeli z `doctor.sh`** — a od 05.09.2026 trafisz, bo po
odhaczeniu T-212 nie ma w tym pliku ani jednego wpisu `### [ ]`, który nie byłby
`ZABLOKOWANE` albo `[CZŁOWIEK]` — **to nie jest koniec pracy i nie jest powód, żeby
stanąć.** Tabela wyżej mówi, czego brakuje, a nie co robić. Praca czeka niżej, w sekcji
**Plan**: faza 2 (T-320, wpis `[~]` wyżej) jest w toku, a fazy **5 i 6** trzymają
31 pozycji, z których żadna nie wymaga decyzji właściciela. Tak mówi `CLAUDE.md` §8:
„agent bierze następną pozycję z fazy 5 lub 6 w `docs/TASKS.md`". Sam komunikat doctora
nadal odsyła wyłącznie do tabeli wyżej i to jest **znalezisko zgłoszone, nie naprawione**
— poprawka po stronie `doctor.sh` jest poza zakresem zadania, które ten akapit dopisało.

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

### Faza 3 — T-212 pierwsza stacja typowa · ZROBIONE 04.09.2026

**Przepisane 05.09.2026, a nie dopisane obok.** Poprzednia wersja tego punktu mówiła
„Po T-320. Blokada danych zdjęta przez R-007, T-211 scalone" — to nieprawda: faza
**wyprzedziła** fazę 2. T-212 jest scalone jako **#137** (`fe14d72`, 04.09.2026),
zanim T-320 doszło do końca; peron wszedł do sceny w **#223**, a decyzja 95,0 m dotarła
do pipeline'u w **#225**. Liczby są we wpisie T-212 wyżej.

### Faza 4 — T-400 etap 3 · ZROBIONE 05.09.2026

**Przepisane 05.09.2026, a nie dopisane obok.** Poprzednia wersja brzmiała „Wpiąć
w scenę to, co **już jest w rdzeniu i przetestowane, a scena tego nie woła**:
`DoorCycle`, `StationStop`, `FixedBlockSystem`, `TrainProtection`" — to już nieprawda
dla **wszystkich czterech**. `DoorCycle` i `StationStop` scena woła od #210 i #212
(etap 3b wpisu T-400 wyżej: 11 zatrzymań, wszystkie kolumny max |Δ| = 0,000E+00),
`FixedBlockSystem` od #215 (`--signalling=PLIK`, HUD z prędkością dopuszczalną
i autorytetem jazdy), a `TrainProtection` od #221 — i to nie jako odczyt, tylko jako
filtr polecenia przed kontrolerem. Streamowanie chunków i przełączanie LOD wypadły
z tej fazy wcześniej, bo są zrobione (#174, #177). Zostaje to, co stoi w „Zostaje"
wpisu T-400: **wiele składów**, czyli T-320.

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
| 5.7 | nikt nie wiedział, ile kosztuje krok linii przy N składach — a „120 Hz wystarczy" było zdaniem bez ani jednego pomiaru | `reports/linecore-budget.md`, zmierzone 05.09.2026 na `6c1048b`. Oś pakietu A **nasyca się przy 9 składach naraz** (12 bez ryglowania tras) i kosztuje wtedy **4,56 µs na krok = 0,055 % budżetu 1/120 s**, zapas 1827× — granica jest fizyczna, nie procesorowa. Koszt rośnie **kwadratowo**, nie liniowo (reszty dopasowania liniowego 4× większe i ułożone w łuk; człon N² pochodzi z `FixedBlockSystem.PublishAuthorities` wołanego raz na skład z `MoveTrain`); próg klatki wypada przy **N ≈ 330–390** i jest **wyekstrapolowany 56–65× poza zakres pomiaru**. Skład zgłoszony, ale niewpuszczony na oś kosztuje 0,0375 µs, liniowo. Narzędzie: polecenie `budget` w `src/Sim.Runner` (`LineBudget.cs`) z 9 testami w `tests/Sim.Tests/LineBudgetTests.cs`; cztery mutacje narzędzia, wszystkie złapane; powtarzalność między dwoma commitami w granicach 2,3 % |
| 6.B12 | `TrainView.PlaceAt` nie miał ani jednego testu — mutacja `body.Node.Visible = covered` → `= true` przeżyła przegląd przy #212, sprawdzone ponownie na `619b179`: 84/84 przeszło z mutacją w środku | **#217**, i pozycja **stała w tabeli kolejki jeszcze po scaleniu** — dopisana przy #213, zrobiona przy #217, zdjęta stąd dopiero 05.09.2026. Decyzja o widoczności wyszła z silnika do `TrainLayout`, `PlaceAt` jest jedną linią, granicą jest `ITrainBody`. Przybite liczbami dla prawdziwego składu M7 (11 brył, 94,0 m) na osi prostej 300 m: czoło na 0 m → **11 ukrytych**, 20 m → 8, 50 m → 4, 94 m → 0. `dotnet test tests/Game.Tests` → 97/97 |
| 6.C1 | scena wczytywała wszystkie chunki naraz | #174 (predykat i LOD po stronie sceny), #177 (`TunnelView.Stream` zamiast `LoadAll`) — wpis T-400, etap 3a |
| 6.C2 | poziomy LOD istniały, scena ich nie używała | to samo, `StreamingPlan.LodPlan`; przybite tablicą oczekiwań wspólną dla Pythona i C# |
| 6.B11 | kamera obserwacyjna miała siedzieć wewnątrz geometrii „przez pierwsze ~106 m", a klatka wychodzić białą plamą — i sama ta liczba była nieprawdziwa | **Dwie połowy, obie zrobione.** KIERUNEK — #226: `ChaseCameraAim.LookTarget` podstawia kierunek osi tam, gdzie kamera i cel wypadają w jednym punkcie; 10 ostrzeżeń `Target and up vectors are colinear` na przebieg `--line` zeszło do zera i pilnuje tego `tools/ci/assert_no_godot_warnings.py`. GEOMETRIA — decyzja właściciela z 05.09.2026: widok `chase` jest NIEDOSTĘPNY, dopóki cały skład nie wjedzie na oś. Scena schodzi wtedy do kabiny i mówi o tym szóstym wierszem HUD-u, a `--shot --view=chase` w tym paśmie ODMAWIA kodem 13 zamiast zapisać białą płytę pod nazwą `chase`. **Poprawka liczby:** 106,0 m to kilometraż, od którego kamera odzyskuje pełne 12,0 m odstępu, a NIE koniec pasma w geometrii; w skorupie kamera siedzi przez **0..94,0 m** (długość M7 z `data/vehicle/m7-spec.json`, status `spec`), a kierunek jest nieokreślony przez **0..47,0 m** (połowa składu). Zmierzone 05.09.2026 na `--line --limit-kmh=70`, ułamek pikseli o jasności > 0,80 w górnych 60 % kadru: 20 m → 0,1 %, 48 m → 56,4 %, 50 m → 38,3 %, 90 m → 0,0 %, 96 m → 42,0 %, 110 m → 0,0 %, 2000 m → 0,0 %. Pasmo 94..106 m zostaje jasne ŚWIADOMIE — patrz „Czego agent nie ruszy bez decyzji" |
| 6.D3 | żaden `reports/*.md` nie musiał mówić, na jakim commicie i kiedy powstały jego liczby — raport sprzed przeliczenia kilometrażu (#86, `4a03982`) czytał się identycznie jak dzisiejszy | **#247, a pozycja stała w kolejce jeszcze po scaleniu** — bramka weszła z `839ad78` (04.09.2026), zdjęta stąd 05.09.2026, tak samo jak 6.B12 wyżej. `tools/tests/test_report_hygiene.py`: nagłówkiem jest tekst przed pierwszym `## `, dwie notacje daty i SHA w grawisach, osiem kontroli negatywnych z wyjściem w docstringu. Zmierzone 05.09.2026 na `6c1048b`: **48 raportów w pętli, 48 z datą w nagłówku, 46 z commitem**, dwa bez — `R-006-line-speed.md` (pomiar wykonany PRZED commitem, który raport wniósł) i `T-401-line-run.md` (sekcje mierzone na `28e0d82` i `7d15987`, jeden SHA w nagłówku spłaszczyłby dwa pomiary). Domknięcie dołożyło temu, czego bramce brakowało: lista wyjątków była **otwarta** — pięć raportów pozbawionych SHA i dopisanych do niej z długim powodem (lista 2 → 7) przechodziło komplet testów modułu na zielono, a podłoga `MIN_REPORTS - len(COMMIT_EXCEPTIONS)` malała o jeden z każdym wyjątkiem (38 → 32). Zamyka to zapadka `MAX_COMMIT_EXCEPTIONS = 2` i `MAX_DATE_EXCEPTIONS = 0`, wolno je tylko obniżać, a podłoga liczy się od zapadki, nie od długości listy |

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
5. Pozycja liczona do zapasu ma mieć **blok szczegółów** `##### <numer> · tytuł`
   z sześcioma polami. Wiersz tabeli mówi, *dlaczego* pozycja nie wymaga decyzji;
   dopiero blok mówi, *jak ją wykonać i po czym poznać, że jest skończona*.

**Zapas udokumentowany:** punkt 5 wszedł 05.09.2026 i od razu pokazał, że reguła
zapasu mierzyła dotąd nie to, co deklaruje. Blok z sześcioma polami ma **8** pozycji —
6.A8, 6.B6, 6.B7, 6.B8, 6.B9, 6.B10, 6.D5 i 6.D6, czyli dokładnie te dopisane
04.09.2026. Reszta to wiersz tabeli i nic więcej: żadnego Wejścia, Wyjścia,
Weryfikacji, „Skończone, gdy", „Poza zakresem" ani „Zależy od". Próg doby pracy wynosi
dwanaście, więc **brakuje czterech** udokumentowanych pozycji.

**Liczba pozycji w tym akapicie jest przepisana, a nie dopisana obok.** Pierwsza wersja
mówiła „Zmierzone na `b41c158`: kolejka ma **33 pozycje** […] Pozostałe **25**" i to
przestało być prawdą, zanim akapit zdążył się zestarzeć: 6.B11 wyszło do tabeli
domknięć (#226 i #236), a 6.B12 **było zrobione już przy #217** i stało w kolejce
o dwanaście scaleń za długo. Zmierzone 05.09.2026 tym samym licznikiem
(`tools/tests/test_backlog.py`): kolejka ma **31 pozycji**, udokumentowanych jest **8**,
bez kompletu sześciu pól zostają **23**.

Tej luki **nie domyka się dopisywaniem pól z głowy.** `CLAUDE.md` §8 zabrania brać
zadanie wymyślone na miejscu, a wymyślenie cudzej „Weryfikacji" jest tym samym o jeden
krok wcześniej. Pola dopisuje ten, kto ma z czego je odczytać — z `docs/`, `reports/`
albo `data/` — i mówi w commicie, skąd wzięło się każde. Bramką jest zapadka
`MINIMUM_DOCUMENTED_ITEMS` w `tools/tests/test_backlog.py`: wolno ją tylko podnosić,
a gdy dojdzie do dwunastu, ten akapit ma zniknąć — i wtedy jego zniknięcia pilnuje
`test_the_documented_shortfall_is_written_down_while_it_lasts`.

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
| 6.A8 | **Testy jednostkowe sześciu typów `src/Sim`, których nie nazywa żaden plik z `tests/`** — `EnergyAccount`, `BrakingEnergyAccount`, `SpeedProfile`, `MovementAuthority`, `Block`, `DesignParameter` | zmierzone licznikiem, nie na oko (polecenie w szczegółach pozycji); praca idzie wyłącznie do `tests/Sim.Tests/`, więc nie dotyka ani jednej liczby o sieci ani kodu produkcyjnego | M |

#### Pasmo B — narzędzia i geometria (`tools/`)

| # | zadanie | dlaczego bez decyzji | rozmiar |
|---|---|---|---|
| 6.B1 | **ZROBIONE w #265 (05.09.2026) — wpis zostaje w kolejce z powodu zapadki, nie dlatego, że jest do zrobienia**, tak samo jak 6.D6 i 6.B10. Wykonane: 49 peronów pakietów B–F (61 w sześciu pakietach), `reports/T-211-stations-BF.md` z tabelą bramkowaną przez `tools/tests/test_station_layout.py`. Najciaśniejszy peron sieci to Trône|Troon na `L2_E`, R = 97,11 m — **nie jest w pakiecie A**; każda oś ma dokładnie dwa perony przycięte, bo zaczyna się i kończy w środku stacji krańcowej. Treść pierwotna: **`station_layout.py` na pakietach B–F**, dziś liczy tylko pakiet A | osie sześciu pakietów są w `data/track/`, wysokość peronu `source_backed` z R-007 | M |
| 6.B2 | **Znaczniki kilometrażu (T-011) na pozostałych pakietach** | to samo narzędzie, inne wejście | S |
| 6.B3 | **LOD tuneli pakietów B–F** | wzorzec z pakietu A, `reports/L1_A-lod.md` | M |
| 6.B4 | **Kontrola krzyżowa osi B–F wobec OSM**, jak `reports/L1_A-crosscheck.md` dla A | hierarchia źródeł rozstrzygnięta w `docs/07`; rozbieżności się **liczy i zapisuje**, nigdy nie uśrednia | M |
| 6.B5 | **Wykrywanie łuków o najmniejszym promieniu na każdej osi** i sprawdzenie skrajni M7 punkt po punkcie | metoda zmierzona i opisana (`reports/M7-curve-clearance.md`), zostaje zastosowanie | M |
| 6.B6 | **Triaż 37 ocalałych mutacji `tools/blender/sweep.py`** — **największy** zestaw ocalałych w repozytorium (od #206, gdy `clearance_profile.py` zszedł z 45 do 17; wcześniej ten wiersz mówił „największy **niezablokowany**", bo tamten czekał na T-906 — dziś T-906 jest rozstrzygnięte); wynik idzie do `reports/mutation-triage-sweep.md`, którego dziś nie ma | `reports/mutation-triage-lod.md` §„Czego ten triaż nie ruszał" mówi wprost: „**`sweep.py`** — ocalałe tego modułu są osobną pozycją kolejki". Triaż klasyfikuje mutacje i dopisuje testy, nie zmienia ani jednej stałej — a stałe generatora są jawnie decyzją właściciela (`docs/21-measured-vs-assumed.md` §4) i zostają poza zakresem | L |
| 6.B7 | **Triaż 9 ocalałych mutacji `tools/blender/m7_report.py`** — jedyny moduł z co najmniej pięcioma ocalałymi, który nie ma w `reports/` żadnego raportu triażu | wszystkie dziewięć to operatory porównań w progach raportu dopasowania M7; klasyfikacja i testy graniczne, żadnej nowej liczby o taborze — wymiary M7 pochodzą z `data/vehicle/m7-spec.json` (T-904, zrobione) | M |
| 6.B8 | **Triaż 2 ocalałych mutacji `tools/track/make_test_track.py`** — pierwszy wiersz tabeli „Kolejność triażu — po udziale" w `reports/mutation-sweep.md`, udział 100 % (2 / 2) | moduł generuje `BROKEN.json`, czyli kontrolę negatywną dla walidatora osi, i karmi dwie bramki CI (`tools/ci/blender_smoke.sh`, `tools/ci/visual_smoke.sh`); obie ocalałe siedzą w warunku, który decyduje, **gdzie** oś jest zepsuta — mutant przesuwa uszkodzenie, a bramki nadal świecą zielono. Oś jest syntetyczna, więc nie ma tu ani jednego faktu o Brukseli | S |
| 6.B9 | **Wyciągnięcie czystej logiki spod `bpy` z `material_test_scene.py` (12), `station_kit.py` (11) i `detail_markers.py` (9)** — 32 z 51 nieosiągalnych mutacji w trzech plikach | `reports/mutation-sweep.md` §„Moduły nieosiągalne" nazywa lekarstwo wprost: „Lekarstwem tutaj nie są testy, tylko dalsze wyciąganie logiki spod `bpy`", i ma dla tego zmierzony precedens z tego samego przebiegu (`m7_shell.py` 35 → 2, `tunnel_sweep.py` 35 → 6, `profile_vehicle.py` 26 → 7). Przeniesienie funkcji czystych nie zmienia geometrii wyjściowej — kontrolą jest identyczny GLB | L |
| 6.B10 | **`report()` w `tools/physics/braking.py` nie jest wykonywane przez nic** — ani test, ani skrypt `tools/ci/*.sh`; jedyny wołający to `if __name__ == "__main__"` w wierszu 313 | `reports/mutation-triage-fizyka.md` §6 zapisał to jako znalezisko poza triażem: „Funkcja drukuje trzy tablice referencyjne T-311 i mogłaby przestać się składać bez skutku dla CI. To jest osobne zadanie, nie triaż". Tablice referencyjne T-311 są już w `docs/02-simulation.md`, więc test porównuje wypis z tym, co repo już deklaruje | S |

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
| 6.D4 | **Kontrola spójności liczb między `reports/` a kodem** — wartość wypisana w raporcie musi dać się odtworzyć z repo | dokładnie ta klasa rozjazdu, którą audyt znalazł w README | M |
| 6.D5 | **Audyt dryfu pokrycia mutacyjnego po triażu** — które moduły odzyskały ocalałe od czasu swojego raportu triażu, i przybicie ich z powrotem | rozjazd jest już zmierzony i leży w dwóch plikach naraz: `tools/track/crs.py` miał po triażu 6 ocalałych na 8 mutacji (`reports/mutation-triage-wczytywanie.md` §Wynik), a przebieg z `66b8301` w `reports/mutation-sweep.md` pokazuje **8 na 14**; `tools/ci/assert_shot_metadata.py` miał **2 na 33** (`reports/mutation-triage-png-metadata.md` §Wynik), a dziś ma **6 na 39**. Porównanie dwóch raportów, które już istnieją — żadnej nowej danej | M |
| 6.D6 | **ZROBIONE w #258 (05.09.2026) — wpis zostaje w kolejce z powodu zapadki, nie dlatego, że jest do zrobienia.** `test_backlog.py` trzyma `MINIMUM_DOCUMENTED_ITEMS = 8`, a udokumentowanych pozycji jest dokładnie osiem; przeniesienie którejkolwiek do tabeli domknięć zbija licznik do siedmiu i wywraca `test_the_documented_reserve_does_not_regress`, a komentarz przy zapadce mówi, że wolno ją tylko podnosić. Decyzja właściciela z 05.09.2026: wpis zostaje z tą adnotacją. Treść pierwotna: **rozszerzenie zestawu operatorów `tools/tests/mutation_sweep.py`** poza porównania i progi liczbowe — przypisania, wywołania i łączniki logiczne. Wykonane: dwie klasy urosły do pięciu (`logika`, `argument`, `przypisanie`), a stary zestaw odtwarza `--operators operator,prog` co do sztuki (1038 = 1038) | `reports/mutation-sweep.md` §„Czego ten przebieg NIE pokrywa, choć pozycja 5.1 tak brzmi" wypisuje ten brak w tabeli: pozycja 5.1 mówi „każdą kontrolę", a narzędzie mutuje „wyłącznie **operatory porównań i progi liczbowe**; nie mutuje przypisań, wywołań ani łączników logicznych". Praca w samym narzędziu pomiaru; baza do porównania jest zmierzona (980 mutacji, 51 nieosiągalnych, 929 policzonych na `66b8301`) | L |

#### Szczegóły ośmiu pozycji dopisanych 04.09.2026

Wiersze tabel wyżej mówią, **dlaczego** pozycja nie wymaga decyzji. Poniżej stoi to,
czego wymaga `CLAUDE.md` §6 i `docs/TASK-TEMPLATE.md`: sześć pól na pozycję, plus jedno
zdanie o tym, **z czego ta pozycja się wzięła** — plik i sekcja. Pozycja bez takiego
odnośnika byłaby zadaniem wymyślonym na miejscu, a §8 zabrania takie brać.

Wspólne dla wszystkich ośmiu: **Poza zakresem** zawiera zawsze `docs/03-legal.md`,
zapis do `data/`, ocenę estetyczną i podnoszenie albo obniżanie jakiejkolwiek stałej
wymienionej w `docs/21-measured-vs-assumed.md`. Pozycje wypisują poniżej tylko to,
co dochodzi ponad ten wspólny zakaz.

##### 6.A8 · Sześć typów `src/Sim` bez ani jednego testu, który je nazywa

- **Skąd:** pomiar własny, nie lektura. Faza 1 tego planu liczyła „Moduły `tools/` bez
  testu: **2**" i z tego wyszła pozycja 5.8; ten sam licznik po stronie rdzenia nie był
  dotąd puszczony. Wynik: **6 z 45** plików `src/Sim` nie jest nazwane w żadnym pliku
  pod `tests/`.
- **Wejście:** `src/Sim/Physics/EnergyAccount.cs`, `src/Sim/Physics/BrakingEnergyAccount.cs`,
  `src/Sim/Physics/SpeedProfile.cs`, `src/Sim/Physics/DesignParameter.cs`,
  `src/Sim/Signalling/MovementAuthority.cs`, `src/Sim/Signalling/Block.cs`;
  tablice referencyjne z `docs/02-simulation.md` i `reports/T-310-physics.md`.
- **Wyjście:** `tests/Sim.Tests/EnergyAccountTests.cs`,
  `tests/Sim.Tests/SpeedProfileTests.cs`, `tests/Sim.Tests/MovementAuthorityTests.cs`
  (podział na pliki wynika z przestrzeni nazw, nie z upodobania).
- **Weryfikacja:**
  ```bash
  # licznik, który wskazał te sześć — po zadaniu ma wypisać zero wierszy
  for f in $(find src/Sim -name '*.cs'); do n=$(basename $f .cs); \
      [ "$(grep -rlw "$n" tests/ | wc -l)" -eq 0 ] && echo "BRAK TESTU: $f"; done
  dotnet test tests/Sim.Tests
  ```
  Oczekiwane: pusty wypis licznika i zielony `dotnet test`.
- **Skończone, gdy:** licznik wypisuje **0** plików zamiast 6, a każdy z nowych testów ma
  kontrolę negatywną sprawdzoną wykonaniem — w szczególności `ResidualJ`
  i `RelativeResidual` (oba konta energii), `PeakSpeedMps` i `FirstAtLeast` na profilu
  pustym i jednopróbkowym, oraz `ResistanceShorteningM` przy zerowym opóźnieniu.
- **Poza zakresem:** zmiana czegokolwiek w `src/Sim/` — commit zawiera wyłącznie
  `tests/` i ten plik. Nie dotyka `src/Game/` ani warstwy Godota.
- **Zależy od:** nic.

##### 6.B6 · Triaż 37 ocalałych mutacji `tools/blender/sweep.py`

- **Skąd:** `reports/mutation-triage-lod.md` §„Czego ten triaż nie ruszał", ostatni
  punkt: „**`sweep.py`** — ocalałe tego modułu są osobną pozycją kolejki". Liczba jest
  z `reports/mutation-sweep.md` §„Kolejność triażu — po udziale": **37 / 79, 47 %**.
  Przy zakładaniu tej pozycji był to drugi zestaw w repozytorium po
  `clearance_profile.py`, a tamten był zablokowany przez T-906 — **to już nieprawda**
  i dlatego zdanie jest przepisane, a nie dopisane obok: T-906 jest rozstrzygnięte,
  a `clearance_profile.py` zszedł do 17 ocalałych (#206), więc `sweep.py` jest po
  prostu **największym** zestawem ocalałych w repozytorium.
- **Wejście:** `tools/blender/sweep.py`, `reports/mutation-sweep.md`
  §`tools/blender/sweep.py` (37 wierszy z numerem wiersza i rodzajem mutacji),
  `tools/tests/mutation_sweep.py`, istniejące `tools/tests/test_sweep.py`
  i `tools/tests/test_chunks.py`.
- **Wyjście:** `reports/mutation-triage-sweep.md` (dziś **nie istnieje** — triaż z 03.09.2026
  zostawił wynik wyłącznie w treści commita `a6793ed`, PR #132) oraz nowe testy
  w `tools/tests/test_sweep.py` i `tools/tests/test_chunks.py`.
- **Weryfikacja:**
  ```bash
  python3 tools/tests/mutation_sweep.py --only sweep.py --workers 4 \
      --journal build/sweep-po.jsonl --json build/sweep-po.json
  python3 tools/tests/test_all.py
  ```
  Oczekiwane: liczba ocalałych z `--only sweep.py` niższa od 37, cały zestaw zielony,
  a każda ocalała, która **zostaje**, ma w raporcie werdykt „mutant równoważny" albo
  „remis bez znaczenia" — z powodem, nie z etykietą (tabela klas z `reports/mutation-sweep.md`
  §„Jak czytać ocalałe").
- **Skończone, gdy:** z 37 ocalałych **każda** ma werdykt, liczba ocalałych spada
  co najmniej do poziomu, przy którym udział modułu schodzi poniżej 20 % (czyli
  najwyżej 15 z 79), a każdy dopisany test ma kontrolę negatywną pokazaną wypisem
  `python3 tools/tests/test_all.py` z nazwą padającego testu.
- **Poza zakresem:** ośmiu stałych generatora z `docs/21-measured-vs-assumed.md` §4
  (`DEFAULT_RING_STEP_M`, `DEFAULT_STATION_HALO_M`, `DEFAULT_MAX_CHUNK_M`,
  `DEFAULT_MIN_CHUNK_M`, `DEFAULT_STREAM_AHEAD_M`, `DEFAULT_STREAM_BEHIND_M`,
  `UV_METRES_PER_UNIT`, `DEGENERATE_AREA_M2`) się **nie rusza** — testy przypinają
  granice porównań, nie liczby po prawej stronie. Nie dotyka `tools/blender/lod.py`
  ani `clearance_profile.py`.
- **Zależy od:** nic. 5.1 jest wykonane — jego wynikiem jest `reports/mutation-sweep.md`.

##### 6.B7 · Triaż 9 ocalałych mutacji `tools/blender/m7_report.py`

- **Skąd:** `reports/mutation-sweep.md` §„Kolejność triażu — po udziale" i
  §`tools/blender/m7_report.py`: **9 / 31, 29 %**. Przegląd `reports/mutation-triage-*.md`
  (dwanaście plików) nie wymienia tego modułu ani razu — to jedyny moduł z co najmniej
  pięcioma ocalałymi bez własnego raportu triażu.
- **Wejście:** `tools/blender/m7_report.py`, dziewięć wierszy z
  `reports/mutation-sweep.md` (46 ×2, 52 ×2, 85, 87, 95, 96, 169),
  `tools/tests/test_m7_report.py` (43 testy dziś), `data/vehicle/m7-spec.json`,
  `reports/M7-in-tunnel.md`.
- **Wyjście:** `reports/mutation-triage-m7-report.md` i nowe testy w
  `tools/tests/test_m7_report.py`.
- **Weryfikacja:**
  ```bash
  python3 tools/tests/mutation_sweep.py --only m7_report.py --workers 4 \
      --journal build/m7report-po.jsonl --json build/m7report-po.json
  python3 tools/tests/test_all.py
  ```
  Oczekiwane: mniej niż 9 ocalałych, zestaw zielony, każda pozostała z werdyktem.
- **Skończone, gdy:** wszystkie 9 ma werdykt, a udział modułu schodzi z 29 % poniżej
  10 % (najwyżej 3 z 31); pary z wierszy 46 i 52 są rozróżnione po
  `plik:wiersz:przesunięcie`, a nie po `plik:wiersz` — `reports/mutation-sweep.md`
  §„Pułapka odczytu" mówi, dlaczego to nie jest formalność.
- **Poza zakresem:** wymiary M7 (`data/vehicle/m7-spec.json`, siedem wartości `spec`
  z T-904 i reszta jako jawne założenia projektowe) i progi raportowania miejsc
  krytycznych z `docs/21-measured-vs-assumed.md` §4a.
- **Zależy od:** nic.

##### 6.B8 · Triaż 2 ocalałych mutacji `tools/track/make_test_track.py`

- **Skąd:** `reports/mutation-sweep.md` §„Kolejność triażu — po udziale", **pierwszy
  wiersz tabeli**: `tools/track/make_test_track.py`, **2 / 2, 100 %** — jedyny moduł
  z udziałem pełnym. Pozycja jest mała, ale ta tabela jest własną kolejnością triażu
  tego projektu i ten moduł stoi w niej na szczycie.
- **Wejście:** `tools/track/make_test_track.py` (wiersz 19: `if broken and i == 130`),
  dwa wiersze z `reports/mutation-sweep.md` (`== → !=` i `130 → 131`),
  `tools/ci/blender_smoke.sh` (wiersz 88), `tools/ci/visual_smoke.sh` (wiersz 59),
  `tools/tests/test_validate_axis.py`.
- **Wyjście:** testy w `tools/tests/test_validate_axis.py` albo nowy
  `tools/tests/test_test_track_fixture.py`, oraz `reports/mutation-triage-make-test-track.md`.
- **Weryfikacja:**
  ```bash
  python3 tools/tests/mutation_sweep.py --only make_test_track.py --workers 2 \
      --journal build/mtt-po.jsonl --json build/mtt-po.json
  python3 tools/tests/test_all.py
  ```
  Oczekiwane: **0 ocalałych z 2**, zestaw zielony.
- **Skończone, gdy:** obie mutacje są **zabite**, a nie zaklasyfikowane jako równoważne:
  test sprawdza, że uszkodzenie w `BROKEN.json` siedzi dokładnie w punkcie **130** z 260
  (a nie 131 i nie w każdym punkcie), bo to ten punkt czyni z pliku kontrolę negatywną
  walidatora osi. Kontrola negatywna obu mutacji pokazana wypisem z nazwą padającego testu.
- **Poza zakresem:** oś jest **syntetyczna** (`"crs": "syntetyczny, origin (0,0)"`), więc
  zadanie nie dotyka ani jednego faktu o brukselskiej sieci; nie zmienia `tools/ci/*.sh`
  ani kształtu `TEST.json`, bo od tego kształtu zależą dwie bramki.
- **Zależy od:** nic.

##### 6.B9 · Wyciągnięcie czystej logiki spod `bpy` z trzech modułów scen

- **Skąd:** `reports/mutation-sweep.md` §„Moduły nieosiągalne — 51 mutacji w 9 plikach":
  „Lekarstwem tutaj nie są testy, tylko dalsze wyciąganie logiki spod `bpy`". Trzy
  pierwsze pliki tej tabeli — `material_test_scene.py` (12), `station_kit.py` (11),
  `detail_markers.py` (9) — to **32 z 51** nieosiągalnych mutacji, i ten sam raport mówi,
  że wszystkie trzy **urosły**, a nie zostały po ekstrakcji.
- **Wejście:** `tools/blender/material_test_scene.py`, `tools/blender/station_kit.py`,
  `tools/blender/detail_markers.py`; wzorzec ekstrakcji zmierzony w tym samym raporcie
  (`m7_shell.py` 35 → 2, `tunnel_sweep.py` 35 → 6, `profile_vehicle.py` 26 → 7,
  `glb_roundtrip.py` 10 → 1, `place_vehicle.py` 7 → 1).
- **Wyjście:** funkcje czyste przeniesione do `tools/track/` albo `tools/visual/`
  (jak zrobiono dla poprzednich pięciu), testy w `tools/tests/`, raport
  `reports/bpy-extraction-round-2.md`.
- **Weryfikacja:**
  ```bash
  bash tools/ci/blender_smoke.sh          # ta sama geometria, suma SHA-256 przed i po
  python3 tools/tests/mutation_sweep.py --workers 4 \
      --journal build/bpy-po.jsonl --json build/bpy-po.json
  python3 tools/tests/test_all.py
  ```
  Oczekiwane: te same pliki wyjściowe co przed ekstrakcją (suma SHA-256 zgodna),
  liczba nieosiągalnych mutacji poniżej 51, zestaw zielony.
- **Skończone, gdy:** nieosiągalne schodzą z **51** do najwyżej **25**, każda wyciągnięta
  funkcja ma test z kontrolą negatywną, a GLB i PNG z bramek są **identyczne co do sumy
  SHA-256** z tymi przed ekstrakcją — czyli refaktor nie zmienił ani jednego wierzchołka.
- **Poza zakresem:** materiały, kolory i cokolwiek z `docs/03-legal.md` lub kierunku
  artystycznego (T-902); nie zmienia interfejsu CLI żadnego z trzech skryptów, bo wołają
  je bramki.
- **Zależy od:** nic. Jeśli 6.B6 idzie równolegle, wchodzi po nim — oba dotykają
  `tools/blender/`.

##### 6.B10 · `report()` w `tools/physics/braking.py` nie jest wykonywane przez nic

- **Skąd:** `reports/mutation-triage-fizyka.md` §6 „Co zauważyłem przy okazji, a czego
  nie ruszałem": „**`report()` w `braking.py` nie jest wykonywane przez żaden test.**
  (…) Funkcja drukuje trzy tablice referencyjne T-311 i mogłaby przestać się składać bez
  skutku dla CI. To jest osobne zadanie, nie triaż." Sprawdzone ponownie na tym drzewie:
  jedynym wołającym jest blok `__main__` w wierszu 313, i nie woła jej żaden plik
  z `tools/tests/` ani żaden `tools/ci/*.sh`.
- **Wejście:** `tools/physics/braking.py` (wiersze 267–313), tablice referencyjne
  T-311 w `docs/02-simulation.md` i `reports/T-311-braking.md`,
  `tools/tests/test_braking.py`.
- **Wyjście:** testy w `tools/tests/test_braking.py`, które wołają `report()`
  i porównują wypis z liczbami, które repo już deklaruje.
- **Weryfikacja:**
  ```bash
  python3 tools/tests/test_all.py
  python3 -c "import sys; sys.path.insert(0,'tools/physics'); import braking; braking.report()"
  ```
  Oczekiwane: zielony zestaw, a wypis funkcji zgodny wiersz w wiersz z tablicą
  referencyjną z `reports/T-311-braking.md`.
- **Skończone, gdy:** `report()` jest wołane przez co najmniej jeden test, a kontrola
  negatywna pokazuje, że usunięcie dowolnej z **trzech** tablic z wypisu wywraca test
  z nazwą — wypis z `python3 tools/tests/test_all.py`, nie opis.
- **Poza zakresem:** wartości progów hamowania (`docs/21-measured-vs-assumed.md` §4b)
  i `data/vehicle/m7-spec.json`; nie zmienia formatu wypisu, bo raporty T-311 cytują go
  jako stan bieżący.
- **Zależy od:** nic.

##### 6.D5 · Audyt dryfu pokrycia mutacyjnego po triażu

- **Skąd:** porównanie dwóch raportów, które **już leżą w repo**.
  `reports/mutation-triage-wczytywanie.md` §Wynik podaje `tools/track/crs.py`
  **6 ocalałych na 8** po triażu (pokrycie 25,0 %), a `reports/mutation-sweep.md`
  (przebieg na `66b8301`) podaje dla tego samego pliku **8 na 14**.
  `reports/mutation-triage-png-metadata.md` §Wynik podaje
  `tools/ci/assert_shot_metadata.py` **2 na 33**, a przebieg z `66b8301` — **6 na 39**.
  W obu przypadkach urosła i liczba mutacji, i liczba ocalałych.
- **Wejście:** `reports/mutation-sweep.md` i wszystkie dwanaście
  `reports/mutation-triage-*.md`; `tools/tests/mutation_sweep.py`.
- **Wyjście:** `reports/mutation-drift.md` (moduł, ocalałe w swoim raporcie triażu,
  ocalałe dziś, różnica, commit każdej z dwóch liczb) i nowe testy w
  `tools/tests/test_mutation_sweep.py`.
- **Weryfikacja:**
  ```bash
  python3 tools/tests/mutation_sweep.py --only crs.py --workers 2 \
      --journal build/drift-crs.jsonl --json build/drift-crs.json
  python3 tools/tests/mutation_sweep.py --only assert_shot_metadata.py --workers 2 \
      --journal build/drift-shot.jsonl --json build/drift-shot.json
  python3 tools/tests/test_all.py
  ```
  Oczekiwane: liczby z przebiegu zgadzają się z tabelą w `reports/mutation-drift.md`
  co do jedności, a nie „w przybliżeniu".
- **Skończone, gdy:** tabela wymienia **wszystkie dwanaście** modułów z raportem triażu
  z liczbą po obu stronach, dwa znane przypadki dryfu (`crs.py` 6 → 8,
  `assert_shot_metadata.py` 2 → 6) są przybite testami, a każda różnica, która
  **zostaje**, ma powód wpisany w raporcie: nowy kod albo mutant równoważny.
- **Poza zakresem:** `tools/blender/clearance_profile.py` — jego 66 ocalałych czeka na
  T-906 i **nie należy do tej pozycji**; nie zmienia zestawu operatorów narzędzia
  (to jest 6.D6).
- **Zależy od:** nic. Wykonane przed 6.B6 i 6.B7 daje im punkt odniesienia; wykonane po
  nich musi je uwzględnić.

##### 6.D6 · Rozszerzenie zestawu operatorów `mutation_sweep.py`

- **Skąd:** `reports/mutation-sweep.md` §„Czego ten przebieg NIE pokrywa, choć pozycja
  5.1 tak brzmi", trzeci wiersz tabeli: pozycja 5.1 mówi „każdą kontrolę", a narzędzie
  mutuje „wyłącznie **operatory porównań i progi liczbowe**; nie mutuje przypisań,
  wywołań ani łączników logicznych". Rozjazd jest w repozytorium nazwany, ale
  niedomknięty.
- **Wejście:** `tools/tests/mutation_sweep.py` (generator mutacji z AST, wiersze
  ok. 114 i 176), `tools/tests/test_mutation_sweep.py`, baza porównania z
  `reports/mutation-sweep.md`: **980 mutacji, 51 nieosiągalnych, 929 policzonych,
  661 zabitych, 268 ocalałych, 71,2 % pokrycia** na `66b8301`.
- **Wyjście:** nowe klasy mutacji w `tools/tests/mutation_sweep.py`, testy w
  `tools/tests/test_mutation_sweep.py`, przeliczony `reports/mutation-sweep.md`
  z **dwiema kolumnami**: stary zestaw operatorów i nowy.
- **Weryfikacja:**
  ```bash
  python3 tools/tests/test_all.py
  python3 tools/tests/mutation_sweep.py --workers 4 \
      --journal build/ops-po.jsonl --json build/ops-po.json --out build/ops-po.md
  ```
  Oczekiwane: przebieg na **starym** zestawie operatorów daje te same 980 mutacji
  i te same identyfikatory `plik:wiersz:przesunięcie` co `66b8301` (narzędzie generuje
  je w ustalonej kolejności, więc to jest sprawdzalne co do wiersza), a nowy zestaw
  daje ich więcej.
- **Skończone, gdy:** narzędzie mutuje co najmniej trzy nowe klasy (`and` ↔ `or`,
  podmiana argumentu wywołania na wartość neutralną, usunięcie przypisania
  augmentowanego), stary zestaw jest **odtwarzalny co do identyfikatora** — kontrola
  regresji na 980 pozycjach — a przyrost ocalałych jest w raporcie rozbity na klasy,
  nie podany jedną liczbą.
- **Poza zakresem:** mutowanie bramek shellowych z `tools/ci/*.sh` — ten sam raport
  mówi, że wymaga „drugiego narzędzia i osobnej wyroczni", i to jest osobna pozycja,
  której tu **nie zakładam**; nie zmienia ani jednego pliku pod testem.
- **Zależy od:** nic. Wykonane po 6.D5 unieważnia jego tabelę bazową, więc kolejność
  6.D5 → 6.D6 jest tańsza.

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
| **pasmo 94..106 m** kamery goniącej | decyzja z 05.09.2026 domyka 6.B11 na paśmie 0..94,0 m — „dopóki cały skład nie wjedzie na oś". Za tą granicą kamera jest już za ogonem, ale bliżej niż nominalne 12,0 m, i kadr bywa nadal jasny: zmierzone 96 m → **42,0 %** pikseli jaśniejszych niż 0,80 w górnych 60 % kadru, wobec 0,0 % od 110 m. Czy ukrywać także to pasmo, jest kolejną decyzją o rozgrywce — liczba 94,0 m padła wprost i agent jej nie rozciąga |

### Znane rozjazdy w dokumentach

- ~~`CLAUDE.md` §2 mówi „25 testów narzędzi"~~ — **zamknięte**: liczba zeszła z pliku,
  bo zaszywanie jej w konstytucji generowało rozjazd przy każdym nowym module.
  **Przepisane 05.09.2026:** poprzednia wersja dopisywała tu „dla porządku:
  `test_all.py` zbiera dziś **700** testów z 31 modułów" — i wpadła dokładnie w rozjazd,
  przed którym ten punkt ostrzega, bo liczba przestała być prawdziwa przy pierwszym
  nowym module (tego dnia było ich 68). Liczby nie ma sensu tu utrwalać; podaje ją
  `python3 tools/tests/test_all.py` i wypisuje `doctor.sh`.
- **Przepisane 05.09.2026, a nie dopisane obok.** Poprzednia wersja mówiła „Dziesięć
  Issues jest otwartych, choć zadanie leży w `main` (#9, #15–#17, #20–#24, #27)" —
  nieprawdziwa jest i liczba, i lista. Odpytane tego dnia przez API GitHuba: **#9, #20,
  #21, #22, #23, #24 i #27 są zamknięte**. Otwartych Issues z pracą leżącą w `main` jest
  **pięć**: #15, #16 i #17 (R-003, R-004, R-005 — wszystkie trzy w `main`), #18 (T-211,
  wpis `[x]` wyżej) i #19 (T-212, wpis `[x]` wyżej). Ten plik deklaruje Issues źródłem
  prawdy o statusie, więc rozjazd jest realny; część z nich właściciel poprosił,
  żeby zostawić otwarte.
