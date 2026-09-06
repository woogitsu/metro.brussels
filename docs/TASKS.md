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
| 5.6 | **Domknąć „Czego brakuje w tej rozpisce"** — T-114, R-002…R-007, T-401 mają Issues, ale nie mają wpisu tutaj | ten plik sam deklaruje, że dopóki wpisu nie ma, **Issues są jedynym źródłem prawdy** — czyli rozjazd jest zapisany, ale niezamknięty | sekcja znika, bo każde zadanie ma wpis z sześcioma polami |

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
| 5.1 | przegląd mutacyjny wszystkich bramek, z rejestrem ocalałych | **#184** — `reports/mutation-sweep.md`, snapshot na `66b8301`. Pozycja jest generatorem: jej wynikiem są zadania triażu (6.B6, 6.B7, 6.B8, 6.B9) i one zostają w kolejce osobno. Znalezione audytem kolejki 05.09.2026 |
| 5.2 | świeże snapshoty STIB — raport różnic, bez zapisu do `data/` | **`470632d`**, „Pozycja 5.2: rozjazd snapshotów wobec data/ — zero w treści, trzy znaleziska obok” (scalenie #185). Wynik: `reports/snapshot-drift.md`, pobrania kontrolne 04.09.2026, snapshot repozytorium `377b59e`. Decyzja o podmianie `data/` zostaje właścicielowi i nie należała do tej pozycji. Znalezione audytem kolejki 05.09.2026 |
| 5.3 | T-401 zmierzone tylko na L1_A, i to na kilometrażach przed #86 | `reports/T-401-line-run.md` §3 i §4 przeliczone 04.09.2026 na sześciu pakietach: 49 z 49 odcinków dopasowanych, 0 wolniejszych, wszystkie sześć odcinków wiążących identycznych z pierwszą wersją. §3a dokumentuje, że stare liczby były sprzed #86, z bisekcją po commitach i metodą wyszukiwania limitu zapisaną wprost |
| 5.4 | ten sam blok preflightu w dziesięciu workflowach (kontrola czystego workspace) i w siedmiu (sonda narzędzi) | `.github/actions/check-workspace` i `.github/actions/probe-tools`; **warunek odrzucający forki ZOSTAJE w każdym jobie** i nie mógł się przenieść — akcja lokalna uruchamia się dopiero po checkoucie, czyli gdy kod z forka już leży na maszynie. Utrzymanie pilnują `test_no_workflow_reinlines_what_the_local_actions_now_own` i `test_the_local_actions_carry_the_rule_they_took_over` |
| 5.5 | akcje GitHuba przypięte po tagu, nie po SHA | wszystkie cztery `uses:` mają pełny SHA i komentarz z wersją; pilnują tego `test_ci_workflows.py::test_every_action_is_pinned_to_a_commit_not_a_moving_tag`, `..._every_pinned_action_says_which_version_the_commit_is` i `..._the_same_action_is_pinned_to_the_same_commit_everywhere` |
| 5.7 | nikt nie wiedział, ile kosztuje krok linii przy N składach — a „120 Hz wystarczy" było zdaniem bez ani jednego pomiaru | `reports/linecore-budget.md`, zmierzone 05.09.2026 na `6c1048b`. Oś pakietu A **nasyca się przy 9 składach naraz** (12 bez ryglowania tras) i kosztuje wtedy **4,56 µs na krok = 0,055 % budżetu 1/120 s**, zapas 1827× — granica jest fizyczna, nie procesorowa. Koszt rośnie **kwadratowo**, nie liniowo (reszty dopasowania liniowego 4× większe i ułożone w łuk; człon N² pochodzi z `FixedBlockSystem.PublishAuthorities` wołanego raz na skład z `MoveTrain`); próg klatki wypada przy **N ≈ 330–390** i jest **wyekstrapolowany 56–65× poza zakres pomiaru**. Skład zgłoszony, ale niewpuszczony na oś kosztuje 0,0375 µs, liniowo. Narzędzie: polecenie `budget` w `src/Sim.Runner` (`LineBudget.cs`) z 9 testami w `tests/Sim.Tests/LineBudgetTests.cs`; cztery mutacje narzędzia, wszystkie złapane; powtarzalność między dwoma commitami w granicach 2,3 % |
| 6.B12 | `TrainView.PlaceAt` nie miał ani jednego testu — mutacja `body.Node.Visible = covered` → `= true` przeżyła przegląd przy #212, sprawdzone ponownie na `619b179`: 84/84 przeszło z mutacją w środku | **#217**, i pozycja **stała w tabeli kolejki jeszcze po scaleniu** — dopisana przy #213, zrobiona przy #217, zdjęta stąd dopiero 05.09.2026. Decyzja o widoczności wyszła z silnika do `TrainLayout`, `PlaceAt` jest jedną linią, granicą jest `ITrainBody`. Przybite liczbami dla prawdziwego składu M7 (11 brył, 94,0 m) na osi prostej 300 m: czoło na 0 m → **11 ukrytych**, 20 m → 8, 50 m → 4, 94 m → 0. `dotnet test tests/Game.Tests` → 97/97 |
| 6.C1 | scena wczytywała wszystkie chunki naraz | #174 (predykat i LOD po stronie sceny), #177 (`TunnelView.Stream` zamiast `LoadAll`) — wpis T-400, etap 3a |
| 6.C2 | poziomy LOD istniały, scena ich nie używała | to samo, `StreamingPlan.LodPlan`; przybite tablicą oczekiwań wspólną dla Pythona i C# |
| 6.B11 | kamera obserwacyjna miała siedzieć wewnątrz geometrii „przez pierwsze ~106 m", a klatka wychodzić białą plamą — i sama ta liczba była nieprawdziwa | **Dwie połowy, obie zrobione.** KIERUNEK — #226: `ChaseCameraAim.LookTarget` podstawia kierunek osi tam, gdzie kamera i cel wypadają w jednym punkcie; 10 ostrzeżeń `Target and up vectors are colinear` na przebieg `--line` zeszło do zera i pilnuje tego `tools/ci/assert_no_godot_warnings.py`. GEOMETRIA — decyzja właściciela z 05.09.2026: widok `chase` jest NIEDOSTĘPNY, dopóki cały skład nie wjedzie na oś. Scena schodzi wtedy do kabiny i mówi o tym szóstym wierszem HUD-u, a `--shot --view=chase` w tym paśmie ODMAWIA kodem 13 zamiast zapisać białą płytę pod nazwą `chase`. **Poprawka liczby:** 106,0 m to kilometraż, od którego kamera odzyskuje pełne 12,0 m odstępu, a NIE koniec pasma w geometrii; w skorupie kamera siedzi przez **0..94,0 m** (długość M7 z `data/vehicle/m7-spec.json`, status `spec`), a kierunek jest nieokreślony przez **0..47,0 m** (połowa składu). Zmierzone 05.09.2026 na `--line --limit-kmh=70`, ułamek pikseli o jasności > 0,80 w górnych 60 % kadru: 20 m → 0,1 %, 48 m → 56,4 %, 50 m → 38,3 %, 90 m → 0,0 %, 96 m → 42,0 %, 110 m → 0,0 %, 2000 m → 0,0 %. Pasmo 94..106 m zostaje jasne ŚWIADOMIE — patrz „Czego agent nie ruszy bez decyzji" |
| 5.8 | dwa moduły `tools/` bez testu jednostkowego: `make_test_track.py` (2 / 2 ocalałych) i `crs.py` (8 / 14) | **`f5126a3`**, „Testy jednostkowe dla dwóch modułów tools/ pokrytych dotąd tylko integracyjnie”. Wyrocznią `make_test_track.py` był dotąd walidator, a `len(r.err) >= 3` przechodziło także wtedy, gdy `--broken` zapadało 259 punktów zamiast jednego albo punkt 131 zamiast 130; testy przybijają, KTÓRE punkty się różnią (130 i 200) i jakimi liczbami. Potwierdzone pomiarem 05.09.2026 na `ec926a2`: **0 ocalałych** przy obu zestawach operatorów (`reports/mutation-triage-make-test-track.md`). Z `crs.py` ten commit wziął cztery z ośmiu ocalałych; reszta należy do 6.D5, nie do tej pozycji |
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

**Akapit przepisany, a nie dopisany obok — i to czwarty raz, bo za każdym razem
przestawał być prawdą.** Poprzednie wersje mówiły „kolejka ma **33 pozycje** […] Pozostałe
**25**" (`b41c158`), potem „**31 pozycji**, udokumentowanych **8**", potem „**29 pozycji**,
udokumentowanych **12** […] luka jest domknięta" — zdanie prawdziwe co do liczby i fałszywe
co do sensu — a wreszcie „**24 pozycje w tabeli, 14 do wzięcia, 11 z nich udokumentowanych**".
Ta ostatnia wersja niosła **nagłówek `Zapas udokumentowany:`**, którego bramka
`test_the_documented_shortfall_is_written_down_while_it_lasts` żąda dokładnie wtedy, gdy
zapas jest pod progiem — i to jest powód, dla którego nagłówek stąd znika, a nie ozdoba.

**Dlaczego przestała być prawdą, i to nie przez niedopatrzenie.** Ta wersja mówiła
„11 udokumentowanych przy progu 12", a zmierzone 06.09.2026 na `51d324a`, przed tym
commitem, było ich **osiem**. Różnicy nie zrobiła żadna zmiana w planie: zrobiło ją
**scalenie pięciu zadań** (#275, #276, #277, #278, #279). Każde z nich dostało w swoim
wierszu adnotację `ZROBIONE`, a `open_items` takie wiersze odsiewa — więc licznik
udokumentowanego zapasu **opada wtedy, gdy praca idzie dobrze**. Liczba wpisana do planu
ręcznie nie ma jak za tym nadążyć i dlatego rozjechała się o trzy w ciągu jednego dnia.

Ten sam dzień pokazał drugą połowę tej mechaniki. Kolejka zeszła do **12 pozycji do
wzięcia**, czyli równo do progu `MINIMUM_READY_ITEMS`, przy pięciu dalszych zadaniach
**w robocie** — których scalenie zbiłoby ją do siedmiu i **zapaliłoby**
`test_the_queue_holds_at_least_a_day_of_work`. Bramka złapałaby to dopiero po fakcie,
na czerwonym zestawie w cudzym pull requeście. `CLAUDE.md` §8 mówi o tym wprost:
„Gdy kolejka zejdzie poniżej dwunastu pozycji, **pierwszym zadaniem jest jej
uzupełnienie**" — i to jest ten commit.

**Zmierzone po uzupełnieniu, na tym drzewie:** **18 pozycji do wzięcia, wszystkie 18
udokumentowane**, bloków z kompletem sześciu pól **29**. Po scaleniu pięciu zadań
w robocie zostanie 13 do wzięcia i 13 udokumentowanych — nadal nad progiem, i to jest
zapas policzony **na stan po**, nie na stan przed.

**Od 06.09.2026 te dwie rzeczy pilnują dwie różne liczby**, bo jedna nie mogła pilnować
obu naraz. `MINIMUM_DETAIL_BLOCKS` jest **zapadką** na liczbę *napisanych* bloków —
rośnie tylko przez pisanie, maleje tylko przez kasowanie, więc „wolno tylko podnosić"
ma tu sens. `MINIMUM_DOCUMENTED_ITEMS` jest **podłogą alarmową** zapasu pozycji do
wzięcia — tej wolno opadać, gdy zadania są domykane, bo inaczej **wykonanie pracy
wywracałoby zestaw**. Zdarzyło się to dwa razy tego samego wieczoru, przy 6.D4
i przy 6.B2, a pozycji bez bloku zostały wtedy dwie; po ich zużyciu bramki nie dałoby
się już spełnić. Opis rozdzielenia: `reports/zapadka-dwie-role.md`.

Tej luki **nie domykało się dopisywaniem pól z głowy** i następnej też nie wolno.
`CLAUDE.md` §8 zabrania brać zadanie wymyślone na miejscu, a wymyślenie cudzej
„Weryfikacji" jest tym samym o jeden krok wcześniej. Pola dopisuje ten, kto ma z czego
je odczytać — z `docs/`, `reports/` albo `data/` — i mówi w commicie, skąd wzięło się
każde. Cztery bloki dopisane 05.09.2026 mają to zapisane w polu **Skąd**: 6.A7 z tablicy
referencyjnej T-311 w `docs/02-simulation.md`, 6.B1 z wpisu T-211 i klucza `stations`
w pięciu plikach osi, 6.B2 z wpisu T-011 i `reports/T-011-detail-markers.md`, 6.D2
z `reports/linecore-budget.md` §8.4. Zapadki wolno tylko podnosić i nie wolno jej
ustawić wyżej niż próg — pilnują tego `test_the_documented_reserve_does_not_regress`,
`test_the_documented_ratchet_does_not_lag_behind_the_file`
i `test_the_ratchet_cannot_be_set_above_what_it_guards`.

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
| 6.A1 | **ZROBIONE w T-320, etapy 1 i 2 (`90a8c31`, `8f2d118`) — znalezione audytem kolejki 05.09.2026.** `LineDrive.AuthorityEndM` (wiersz 160) ogranicza cel hamowania w wierszu 246: `var stopAt = AuthorityEndM is double limit && limit < target ? limit : target`. Podpina to `LineCore` w wierszu 603. Cztery testy w `tests/Sim.Tests/LineDriveTests.cs` nazywają zachowanie wprost: autorytet dalej niż stacja nie zmienia ani jednego kroku, bliżej — zatrzymuje skład przed nim, postój przed autorytetem jest postojem, a nie pełzaniem, autorytet otwarty puszcza skład dalej. Wpis T-320 podaje pomiar: staje **0,29 m przed blokiem zajętym, zero naruszeń autorytetu**. Treść pierwotna: **autorytet jazdy w `LineDrive`** — skład pyta `FixedBlockSystem` o zajętość bloku przed sobą i hamuje przed zajętym | plan bloków jest **wynikiem reguły**, nie tabelką (T-313, `SignallingPlan.FromAxis`); ATP korzysta z krzywej T-311. Nic nowego do zgadnięcia | L |
| 6.A2 | **ZROBIONE w T-320, etap 2 (`8f2d118`) — znalezione audytem kolejki 05.09.2026.** `LineCore` ma `Add(trainId, releaseStep)` (wiersz 515), `Step()` w trzech fazach (544) i `Trains` (467); `tests/Sim.Tests/LineCoreTests.cs` liczy 34 metody testowe. Że N składów chodzi naprawdę, a nie tylko się kompiluje, mierzy `reports/linecore-budget.md` (pozycja 5.7, `6c1048b`): oś pakietu A **nasyca się przy 9 składach naraz**, 12 bez ryglowania tras. Nierozliczony zostaje wyłącznie takt i 71 obiegów z GTFS — a to jest pozycja 6.A3, nie ta. Treść pierwotna: **`LineCore`: N składów na wspólnym zegarze** z autorytetem z 6.A1 | takt 310 s / 340 s jest **zmierzony** z GTFS (T-113), nie założony | L |
| 6.A3 | **ZROBIONE w #286 (06.09.2026).** `ServiceDay` w rdzeniu, polecenie `service-day` w `Sim.Runner`, 16 testów i `reports/service-day.md`; rdzeń **502 → 518**, narzędzia **1677 → 1680**. Trzy liczby z T-113 wychodzą z rdzenia i różnią się od tamtych o **zero**: obiegów **71**, naraz w służbie **56** o **07:06:44**, nakładających się par kursów w jednym obiegu **0**. **To nie jest przepisanie liczby Pythona do C#** i o to w tej pozycji chodziło: rozkład niósł dotąd WYNIK, a nie dane, więc rdzeń mógłby co najwyżej wypisać cudzą liczbę. `timetable.py` eksportuje teraz okna kursów przy każdym obiegu, a rdzeń liczy z nich wszystko od nowa i **odmawia** rozkładu bez nich. Cztery kontrole negatywne wykonane; jedna z nich znalazła błąd w moim własnym teście (okno kursu zaczyna się ODJAZDEM, nie przyjazdem) | wszystkie liczby zmierzone w T-113, leżą w wytworze przebiegu rozkładu | L |
| 6.A5 | **ZROBIONE w #283 (06.09.2026).** `TripEnergyAccount` w `src/Sim/Train/`, wypis kilowatogodzin z polecenia `line`, `reports/energy-balance.md` i 13 testów; rdzeń **494 → 498**. Zmierzone na pakiecie A: praca trakcji **142,4515 kWh**, praca hamulca **104,3574 kWh**, netto z sieci **142,4515 kWh** przy odzysku 0 % i **38,0941 kWh** przy 100 %. Względne niedomknięcie bilansu **2,147·10⁻¹⁵** na 101 872 krokach, czyli poniżej progu z `reports/T-310-physics.md` — druga, niezależna droga do tej samej liczby, tak jak żądało pole Weryfikacja. **Żadnej sprawności odzysku nie wpisano** i to jest powód, dla którego warianty są skrajne: karta M7 potwierdza sam fakt hamowania odzyskowego i nic ponadto, więc liczba pośrednia byłaby zmyśloną liczbą o taborze (`CLAUDE.md` §1 i §8). Nie dodano też przełącznika CLI wybierającego wariant: oba liczą się zawsze razem, żeby nie było parametru na wymyśloną trzecią liczbę | model energii jest w rdzeniu od T-310; to pomiar na istniejącym kodzie | M |
| 6.A6 | **Wybieg zamiast trakcji: ile kosztuje w czasie, ile oszczędza w energii** | czysty eksperyment na modelu, żadnych nowych danych | M |
| 6.A7 | **ZROBIONE w #281 (06.09.2026).** `tests/Sim.Tests/BrakingPropertyTests.cs`, cztery własności na losowych wejściach ze stałym ziarnem; rdzeń **494 → 498**. Każda kontrola negatywna wywraca **1 z 4** testów własnościowych — i to jest właściwy pomiar, bo test własnościowy padający razem z całym zestawem nie mówi nic o SWOJEJ własności (promienie rażenia w pełnym zestawie: 31, 66, 6 i 2 testy). **Wiersz mówił o monotoniczności drogi hamowania po prędkości i masie, i co do masy był nieścisły:** model T-311 jest matematycznie NIEZALEŻNY od masy — opór Davisa na tonę, sufit przyczepnościowy i hamulec jako polecenie kasują ją w każdym torze obliczeń. Własność zachodzi więc jako **nie-malejąca**, nie rosnąca, i tak jest zapisana w teście. To nie jest błąd modelu, tylko jego udokumentowany wybór (`ServiceBrakingRun.cs`, `TrainController.cs`), nazwany już przez istniejący `Droga_hamowania_z_oporami_nie_zalezy_od_masy_skladu` | wzmacnia to, co jest; nie dodaje ani jednej liczby o metrze | M |
| 6.A8 | **ZROBIONE w #279 (06.09.2026).** **39 testów** w trzech plikach (`EnergyAccountTests.cs`, `MovementAuthorityTests.cs`, `SpeedProfileTests.cs`) i `reports/typy-sim-bez-testu.md`; rdzeń **455 → 494**, `src/Sim/` bez ani jednej zmiany. Pomiar obalił liczbę z bloku: nie 6 z 45, tylko **5 z 52** — `MovementAuthority` zszedł z listy, bo nazywa go zaślepka w `tests/Game.Tests`, ale testu jednostkowego nadal nie miał i dostał go razem z resztą. **Licznik z pola Weryfikacja tego bloku jest zepsuty i to jest główne znalezisko:** po pierwszym `dotnet test` daje **fałszywe zero**, bo `grep -r tests/` wchodzi do `tests/Sim.Tests/bin/`, gdzie leży skompilowany `MetroBxl.Sim.dll` z nazwą każdego typu rdzenia, a `find src/Sim` wciąga wygenerowane pliki z `obj/`. Narzędzie weryfikujące, które po jednym przebiegu testów zawsze melduje „wszystko pokryte” — ta sama klasa usterki co fałszywa wyrocznia mutacyjna z #268. 39 kontroli negatywnych, po jednej na test, każda jako osobna mutacja `src/Sim` z natychmiastowym przywróceniem pliku; `BEZ KONTROLI: []`. Jedną z nich powtórzyłem samodzielnie: zdjęcie osłony `TractionWorkJ == 0.0` daje `Expected <0>, actual <Infinity>`, a cały istniejący `EnergyAndProfileTests` zostaje przy tej mutacji **zielony** — treść pierwotna: **Testy jednostkowe sześciu typów `src/Sim`, których nie nazywa żaden plik z `tests/`** — `EnergyAccount`, `BrakingEnergyAccount`, `SpeedProfile`, `MovementAuthority`, `Block`, `DesignParameter` | zmierzone licznikiem, nie na oko (polecenie w szczegółach pozycji); praca idzie wyłącznie do `tests/Sim.Tests/`, więc nie dotyka ani jednej liczby o sieci ani kodu produkcyjnego | M |
| 6.A9 | **ZROBIONE w #291 (06.09.2026).** Polecenia `Sim.Runner` bez testu — osiem poleceń, nazwy siedmiu z nich nie wymienia ani jeden plik w `tests/Sim.Tests/` | bliźniak 6.A8 po stronie CLI: pomiar na istniejącym kodzie, ani jednej nowej liczby o Brukseli | M |
| 6.A10 | **ZROBIONE (06.09.2026).** `service-day` ma teraz dwa testy kodu wyjścia w `tests/Sim.Tests/RunnerCommandTests.cs` — brak `--timetable` i niepoprawny format `--at`, oba przez ten sam wspólny handler wyjątków co `replay`/`axis`/`line`/`budget` (kod 1). Obie kontrole negatywne WYKONANE osobno (mutacja treści komunikatu, nie kodu wyjścia handlera — bo ten jest współdzielony z czterema testami z #291): każda wywróciła dokładnie jeden test, `git diff --stat src/` puste po przywróceniu. Zestaw: **528 → 530** testów, zielony. Adnotacja w `reports/polecenia-runnera-bez-testu.md` §7; dwa znaleziska z #291 (`compare` zwraca 2 tam, gdzie reszta odmów zwraca 1; `Unknown()` i gałąź pustych argumentów dają tę samą stałą dwiema niezależnymi ścieżkami) nazwane, nieruszone — poza zakresem tej pozycji. Treść pierwotna: **Dziewiate polecenie `Sim.Runner` bez testu kodu wyjscia** — `service-day`, dopisane w #286, gdy blok 6.A9 wymienial juz osiem | 6.A9 swiadomie nie wyszlo poza swoja osemke i to byla wlasciwa decyzja, ale luka zostaje. Przy okazji: `compare` zwraca 2 tam, gdzie reszta odmow zwraca 1, a `Unknown()` i galaz pustych argumentow daja te sama stala dwiema niezaleznymi sciezkami | S |

#### Pasmo B — narzędzia i geometria (`tools/`)

| # | zadanie | dlaczego bez decyzji | rozmiar |
|---|---|---|---|
| 6.B1 | **ZROBIONE w #265 (05.09.2026) — wpis zostaje w kolejce z powodu zapadki, nie dlatego, że jest do zrobienia**, tak samo jak 6.D6 i 6.B10. Wykonane: 49 peronów pakietów B–F (61 w sześciu pakietach), `reports/T-211-stations-BF.md` z tabelą bramkowaną przez `tools/tests/test_station_layout.py`. Najciaśniejszy peron sieci to Trône|Troon na `L2_E`, R = 97,11 m — **nie jest w pakiecie A**; każda oś ma dokładnie dwa perony przycięte, bo zaczyna się i kończy w środku stacji krańcowej. Treść pierwotna: **`station_layout.py` na pakietach B–F**, dziś liczy tylko pakiet A | osie sześciu pakietów są w `data/track/`, wysokość peronu `source_backed` z R-007 | M |
| 6.B2 | **ZROBIONE w #275 (06.09.2026) — wpis zostaje w kolejce z powodu zapadki.** Wykonane: `reports/T-011-details-BF.md` i pięć testów w `tools/tests/test_detail_layout.py`. Sześć osi, **457 miejsc na 34 480,6 m**: 341 hektometrów, 61 stacji, 55 punktów hamowania. Wiersz pakietu A zgadza się co do sztuki z kryterium tej pozycji (89 = 66 + 12 + 11), więc pozostałe pięć policzono tą samą drogą. Trzy zależności sprawdzone osobno: hektometry to `floor(długość / krok)` (znacznik na zerze jest stacją), punkty hamowania to stacje − 1 (pierwsza stacja nie ma przed sobą odcinka), a `skipped_brake_points` jest puste dla **każdej** osi — co przy najkrótszych odcinkach pakietu D nie było oczywiste. 61 stacji przy 59 w sieci, bo osie zachodzą na siebie na krańcówkach; §3 raportu mówi o tym wprost. Testy czytają liczby **z tabeli raportu**, nie mają ich wpisanych. Etap brył znaczników zostaje otwarty — wymaga Blendera, którego w tym środowisku nie ma. Treść pierwotna: **znaczniki kilometrażu (T-011) na pozostałych pakietach** | to samo narzędzie, inne wejście | S |
| 6.B4 | **ZROBIONE — `reports/packages-BF-alignment.md` §6.3, zmierzone na `d47ae47`; znalezione audytem kolejki 05.09.2026.** Kontrola idzie po **relacjach tras**, nie po bboxie, bo Overpass jest z tego środowiska nieosiągalny; `tools/track/fetch_osm_routes.py` nie ma w kodzie ani jednego identyfikatora relacji. Pokrycie przy r = 50 m wynosi **100,0 % dla wszystkich sześciu pakietów**, mediany 0,72–1,35 m, druga tabela podaje wynik osobno dla każdej z dwunastu relacji kierunkowych. Warunek z kolumny obok jest spełniony: rozjazd pakietu B (1,81 m wobec 3,16 m) jest **zapisany jako nierozstrzygnięty**, a nie uśredniony. Treść pierwotna: **kontrola krzyżowa osi B–F wobec OSM**, jak `reports/L1_A-crosscheck.md` dla A | hierarchia źródeł rozstrzygnięta w `docs/07`; rozbieżności się **liczy i zapisuje**, nigdy nie uśrednia | M |
| 6.B5 | **Wykrywanie łuków o najmniejszym promieniu na każdej osi** i sprawdzenie skrajni M7 punkt po punkcie | metoda zmierzona i opisana (`reports/M7-curve-clearance.md`), zostaje zastosowanie | M |
| 6.B6 | **ZROBIONE w #270 (05.09.2026) — wpis zostaje w kolejce z powodu zapadki**, jak 6.D6, 6.B10, 6.B1, 6.B8, 6.D5 i 6.B7. Wykonane: `reports/mutation-triage-sweep.md`, werdykt dla każdej z **36** ocalałych (nie 37 — mutację z wiersza 54 zabił w międzyczasie dopisany test, a snapshotu z `66b8301` się nie przelicza). Podział: **22 zabijalne**, każda z wejściem rozstrzygającym i testem; **4 równoważne** z powodem przy każdej; **10 nierozstrzygniętych** — progi `1e-9` i `1e-18` na normach wektorów, gdzie nie znalazłem wejścia i **nie twierdzę, że go nie ma**. To rozróżnienie nie jest ostrożnością: docstring `test_chunk_a_span_exactly_at_the_cap_is_not_split` twierdził, że mutacja 219 jest równoważna „sprawdzone wykonaniem”, i **było to nieprawdą** — autor policzył pustą pętlę, ale przeoczył `break` tuż za nią, przez który mutant zostawia całą oś za odcinkiem równym limitowi niepodzieloną (350 m przy limicie 100 m: `[100.0]` zamiast trzech cięć). Docstring przepisany. 19 testów granicznych, każdy z progiem podanym **jawnie w argumencie**, bo cztery mutowane wiersze biorą stałą generatora jako domyślny. Treść pierwotna: **triaż 37 ocalałych mutacji `tools/blender/sweep.py`** — **największy** zestaw ocalałych w repozytorium (od #206, gdy `clearance_profile.py` zszedł z 45 do 17; wcześniej ten wiersz mówił „największy **niezablokowany**", bo tamten czekał na T-906 — dziś T-906 jest rozstrzygnięte); wynik idzie do `reports/mutation-triage-sweep.md`, którego dziś nie ma | `reports/mutation-triage-lod.md` §„Czego ten triaż nie ruszał" mówi wprost: „**`sweep.py`** — ocalałe tego modułu są osobną pozycją kolejki". Triaż klasyfikuje mutacje i dopisuje testy, nie zmienia ani jednej stałej — a stałe generatora są jawnie decyzją właściciela (`docs/21-measured-vs-assumed.md` §4) i zostają poza zakresem | L |
| 6.B7 | **ZROBIONE w #269 (05.09.2026) — wpis zostaje w kolejce z powodu zapadki**, jak 6.D6, 6.B10, 6.B1, 6.B8 i 6.D5. Wykonane: `reports/mutation-triage-m7-report.md`, werdykt dla każdej z dziewięciu — **wszystkie dziewięć to mutanty równoważne**, z trzech różnych powodów: cztery (46 ×2, 52 ×2) trafiają w próg, ale `round(…, 6)` scala oba wyniki (0 różnic na 404 wejściach, w tym 129 trafiających dokładnie w próg); cztery (85, 95, 96, 169) mają próg **nieosiągalny w IEEE 754**, bo `1e-4` i `1e-3` nie są wielokrotnościami `ulp` podstaw 1,35 / 0,9 / 1,6 (końcówki `prog/ulp` to `.049622`, `.099243`, `.496094`, przy działającej kontroli dodatniej); jedna (87) siedzi za filtrem z wiersza 85, który wyklucza jedyną różniącą wartość `y == 0`. **Kryterium „Skończone, gdy” tej pozycji jest nieosiągalne uczciwie** — żąda najwyżej 3 z 31, a mutantów równoważnych jest 9; trzy wyjścia i rekomendacja są w §6 raportu i czekają na decyzję właściciela. Zero nowych testów, świadomie: test przybijający zachowanie, którego żadne wejście nie odróżnia, kupuje procent i nie mówi nic o module. Treść pierwotna: **triaż 9 ocalałych mutacji `tools/blender/m7_report.py`** — jedyny moduł z co najmniej pięcioma ocalałymi, który nie miał w `reports/` żadnego raportu triażu | wszystkie dziewięć to operatory porównań w progach raportu dopasowania M7; klasyfikacja i testy graniczne, żadnej nowej liczby o taborze — wymiary M7 pochodzą z `data/vehicle/m7-spec.json` (T-904, zrobione) | M |
| 6.B8 | **ZROBIONE — i to nie w tej pozycji, tylko w 5.8 (`f5126a3`). Wpis zostaje w kolejce z powodu zapadki**, tak jak 6.D6, 6.B10 i 6.B1. Zmierzone 05.09.2026 na `ec926a2`, na TYM SAMYM zestawie klas, na którym powstał wiersz 2 / 2: `--operators operator,prog` daje **2 mutacje, 2 zabite, 0 ocalałych**, a pełny dzisiejszy zestaw 13 / 13 zabitych. Zabijają je testy z `test_make_test_track.py`, nie rozszerzenie zestawu operatorów — rozpisane w `reports/mutation-triage-make-test-track.md`. Treść pierwotna: **Triaż 2 ocalałych mutacji `tools/track/make_test_track.py`** — pierwszy wiersz tabeli „Kolejność triażu — po udziale" w `reports/mutation-sweep.md`, udział 100 % (2 / 2) | moduł generuje `BROKEN.json`, czyli kontrolę negatywną dla walidatora osi, i karmi dwie bramki CI (`tools/ci/blender_smoke.sh`, `tools/ci/visual_smoke.sh`); obie ocalałe siedzą w warunku, który decyduje, **gdzie** oś jest zepsuta — mutant przesuwa uszkodzenie, a bramki nadal świecą zielono. Oś jest syntetyczna, więc nie ma tu ani jednego faktu o Brukseli | S |
| 6.B9 | **ZROBIONE w #276 (06.09.2026) — wpis zostaje w kolejce z powodu zapadki.** Wykonane: trzy moduły bez `bpy` (`station_sections.py`, `marker_gates.py`, `material_specs.py`) i `reports/bpy-extraction-round-2.md`. **Nieosiągalne 53 → 24** przy progu 25, mierzone starym zestawem operatorów — tylko on jest porównywalny z liczbą 51 z raportu, bo na dzisiejszym pełnym zestawie pięciu klas jest ich 350 (#258 rozszerzyło zestaw). Rozbicie: `station_kit.py` 13 → 1, `detail_markers.py` 9 → 0, `material_test_scene.py` 12 → 4. **Refaktor nie zmienił ani jednego wierzchołka**: GLB identyczny co do bajtu, wszystkie trzy rendery identyczne co do pikseli. Suma SHA-256 pliku PNG nie mogła być wyrocznią, bo Blender stempluje w każdym renderze `Date` i `RenderTime` — stąd `tools/ci/png_pixels_sha256.py`, liczące sumę po blokach `IDAT`. **Pomyłka metody warta zapamiętania:** klasyfikacja po funkcjach („czy pada tu `bpy`”) mówiła, że w `material_test_scene.py` nie ma czego wyciągać, zero z dwunastu; klasyfikacja po wierszach dała osiem — predykaty zamurowane w funkcjach z `bpy`, ale same o Blenderze nie wiedzące. Granicą do przecięcia jest wiersz, nie funkcja. Treść pierwotna: **wyciągnięcie czystej logiki spod `bpy` z trzech modułów scen** | `reports/mutation-sweep.md` §„Moduły nieosiągalne" nazywa lekarstwo wprost: „Lekarstwem tutaj nie są testy, tylko dalsze wyciąganie logiki spod `bpy`", i ma dla tego zmierzony precedens z tego samego przebiegu (`m7_shell.py` 35 → 2, `tunnel_sweep.py` 35 → 6, `profile_vehicle.py` 26 → 7). Przeniesienie funkcji czystych nie zmienia geometrii wyjściowej — kontrolą jest identyczny GLB | L |
| 6.B10 | **ZROBIONE w #264 (05.09.2026) — wpis zostaje w kolejce z powodu zapadki, nie dlatego, że jest do zrobienia**, tak samo jak 6.D6 i z tego samego powodu: zdjęcie udokumentowanej pozycji zbija `MINIMUM_DOCUMENTED_ITEMS`, a zapadkę wolno tylko podnosić. Wykonane: trzy testy w `tools/tests/test_braking.py` wołają `report()` i porównują wypis z tablicą referencyjną z `reports/T-311-braking.md` §4 — sześć wierszy po dziewięć liczb, bez tolerancji. Kontrola negatywna obaliła pierwszą wersję testu: mutacja nagłówka na `DROGA HAMOWANIA_MUTANT` przechodziła sprawdzenie `"DROGA HAMOWANIA" in text`, więc oczekiwaniem jest teraz cały wiersz. Treść pierwotna: **`report()` w `tools/physics/braking.py` nie jest wykonywane przez nic** — ani test, ani skrypt `tools/ci/*.sh`; jedyny wołający to `if __name__ == "__main__"` w wierszu 313 | `reports/mutation-triage-fizyka.md` §6 zapisał to jako znalezisko poza triażem: „Funkcja drukuje trzy tablice referencyjne T-311 i mogłaby przestać się składać bez skutku dla CI. To jest osobne zadanie, nie triaż". Tablice referencyjne T-311 są już w `docs/02-simulation.md`, więc test porównuje wypis z tym, co repo już deklaruje | S |
| 6.B13 | **ZROBIONE w #284 (06.09.2026).** Dwa moduły bez `bpy` — `tools/blender/scan_gates.py` (trzy predykaty z `profile_vehicle.py`) i `tools/blender/lod_paths.py` (dwa z `tunnel_sweep.py`) — re-eksportowane pod starymi nazwami, z testem bezpośrednim na każdą funkcję; raport `reports/bpy-extraction-round-3.md`, zestaw narzędzi **1638 → 1655**. Nieosiągalne na starym zestawie klas (`operator,prog`, jedynym porównywalnym z liczbami z tego wiersza): `profile_vehicle.py` **7 → 2**, `tunnel_sweep.py` **6 → 4**. Liczby z wiersza zgodziły się z pomiarem dokładnie, bez rozjazdu — co jest tu warte zapisania, bo trzy inne pozycje kolejki zdezaktualizowały się tego samego dnia. **Czego pozycja NIE domknęła:** przebieg zabijania mutacji wyciągniętych funkcji jest pełny tylko dla `lod_paths.py` (2/2 zabite); na `scan_gates.py` rozstrzygnięta jest **1 z 5**, a cztery przekroczyły czas pod obciążeniem maszyny dzielonej z równoległymi agentami i są zapisane jako **nierozstrzygnięte, nie ocalałe** — trzeci stan, którego nie wolno zapisać jako żadnego z dwóch pozostałych. Domknięcie: ponowny przebieg bez współbieżności, opisane w §5 raportu | metoda jest zmierzona i opisana w `reports/bpy-extraction-round-2.md` §3: granicą do przecięcia jest **wiersz**, nie funkcja | M |
| 6.B14 | **ZROBIONE w #285 (06.09.2026).** `reports/mutation-triage-round-2-modules.md` i 23 testy; zestaw narzędzi **1638 → 1661**. **Pomiar obalił liczbę z tego wiersza:** funkcji bez ani jednego testu bezpośredniego było nie dziewięć, tylko **5 z 13** — cały `material_specs.py` i `straight_prism` w `station_sections.py`; reszta miała pokrycie pośrednie. Zabite mutacje na pełnym zestawie pięciu klas: `material_specs.py` **0 → 9 z 10**, `station_sections.py` **9 → 10 z 15**, `marker_gates.py` **9 z 9 już przed**. Pozostałe ocalałe mają werdykt **równoważna** z dowodem. **Jedna mutacja (`sweep_section`, `+=` → `=`) jest zapisana jako NIEROZSTRZYGNIĘTA**, nie zabita i nie ocalała: narzędzie padło na limicie czasu, a bezpośrednie wykonanie zmutowanego kodu pokazuje pętlę nieskończoną — czyli pod prawdziwym przebiegiem skończyłaby się timeoutem. Trzeci stan istnieje właśnie po to, żeby go nie zgadywać. Kalibracja wyroczni z #268 potwierdzona przed każdym z trzech pomiarów | pozycja 6.B9 świadomie ich nie dopisała: celem było uczynić je **mierzalnymi**, a ile z nich przeżyje przegląd, mówi dopiero pomiar | M |
| 6.B15 | **ZROBIONE (06.09.2026).** Zmierzone na `045730b`, nie na `51d324a` z opisu pozycji: modułów jest dziś **80** (nie 73), fraza dosłowna `"kontrola negatywna"` stoi w **34** (nie 33) — a kryterium dosłowne samo ma dziurę, bo polski odmienia: wzorzec dowolnej odmiany (`kontrol\w*\s+negatywn\w*`) znajduje **37**, trzy więcej (`test_m7_report.py`, `test_next_task.py`, `test_readme_claims.py`), wszystkie z genuine wykonaną kontrolą pod inną odmianą frazy. Wszystkie 80 dostały werdykt w `reports/negative-control-audit.md`: **38 z frazą** (po dopisaniu jednej — patrz niżej), **40 bez frazy, ale z wykonaną kontrolą znalezioną czytaniem treści** (np. `test_data_freshness.py::test_freshness_strict_mode_fails_only_on_expired`, `test_png_pixels.py` z jawnym `raise AssertionError` na nieodrzuconym złym pliku), **2 niepotrzebne** (`test_marker_gates.py`, `test_station_sections.py` — własną kontrolę negatywną mają zmierzoną w module siostrzanym, `reports/mutation-triage-round-2-modules.md`), **0 niewykonalnych** (zmierzone: żaden z 80 nie woła prawdziwego Blendera/Godota/.NET-a; PRZED tym wierszem `test_all.py` przechodził 1710/1710 bez ani jednego `SKIP` mimo braku wszystkich trzech narzędzi w tym środowisku). Jedyna kontrola dopisana: `test_streaming_fixture.py::test_a_planted_mismatch_in_the_fixture_actually_fails_the_comparison` — moduł sam ostrzegał we własnym docstringu, że „rozjazd nie wywala niczego", a żaden test tam tego nie sprawdzał; nowy test psuje jedno pole jednego wiersza W PAMIĘCI i dowodzi, że porównanie to łapie (zweryfikowane też w drugą stronę: bez psucia nowy test sam pada z czytelnym komunikatem). Zestaw **1709 → 1710**. Znalezione i świadomie nietknięte: `test_xml_doc_blocks.py` sprawdza dziś tylko PRAWDZIWY, aktualnie czysty `src/` — żaden test nie wstrzykuje sztucznie zdublowanego `<summary>`, więc licznik nigdy nie był złapany na błędzie. **Skutek ODHACZENIA tego wiersza, zmierzony, nie przypuszczony:** `open_items`/`documented_items` stały dokładnie na zapadce **12** i ten wiersz był w nich policzony — zdjęcie go zbijało zapas kolejki do **11**, czyli pod próg — i gałąź była z tego powodu czerwona, dopóki nie przesiadła się na aktualny `main`. **Powód czerwieni leżał w koordynacji, nie w tej pozycji:** agent dostał twardy zakaz ruszania czegokolwiek poza swoim wierszem, bo cztery gałęzie pracowały równolegle na tym samym pliku, więc nie miał czym zapasu uzupełnić i **zgłosił to wprost, zamiast naruszyć zakaz albo przemilczeć czerwień**. Po rebase na `main` z uzupełnieniem z #294 zapas wynosi **13** i zestaw jest zielony (1710/1710) | `CLAUDE.md` §5 nazywa tę kontrolę częścią pętli weryfikacji, a nie jej ozdobą; policzenie, gdzie jej nie ma, i dołożenie jej tam, gdzie da się ją wykonać, nie wymaga ani jednej decyzji | M |
| 6.B16 | **Triaż ośmiu mutacji ocalałych na `tools/track/detail_layout.py`** — module, który wpis T-011 opisuje jako ten z **0 założeń** | `reports/mutation-drift.md` podaje dla niego 8 ocalałych z 9 mutacji; werdykt dla każdej z nich jest pomiarem, nie decyzją | M |
| 6.B17 | **ZROBIONE w #289 (06.09.2026).** Ścieżka domyślna jest teraz **jedna na przebieg** (commit + klasy operatorów + zawężenie `--only`), a dziennik z wpisami spoza przebiegu **przerywa start** kodem 2; raport `reports/dziennik-mutacyjny.md`, zestaw **1697 → 1700**. **Wiersz opisywał to za słabo:** nie chodziło o to, że dwa przebiegi sobie przeszkadzają, tylko o **mieszanie wyników** — wynik czytany jest z CAŁEGO dziennika, więc cudze wpisy wchodziły do raportu jako wynik tego pomiaru. Wykonana kontrola: dziennik z jednym obcym wpisem daje raport z pełną sekcją modułu, którego przebieg nie dotykał. **Znalezione obok i świadomie nietknięte:** wpis nie niesie commita, a identyfikator mutacji to przesunięcie bajtowe — pole Poza zakresem tej pozycji zabrania ruszać format, więc to osobna pozycja | znalezione przy 6.B14, gdzie dwa agenty liczyły równolegle; narzędzie samo tego nie sygnalizuje. Pomiar i poprawka domyślnej ścieżki, żadnej decyzji | S |
| 6.B18 | **ZROBIONE CZESCIOWO w #293 (06.09.2026), i to jest wynik, a nie wymowka.** Zmierzone czesci, raport `reports/czas-przegladu-mutacyjnego.md`: `git worktree add` **0,10 s** (nie „nie jest tani”), zestaw w swiezym worktree **50,9 s** wobec **65,0 s** w cieplym — czyli swiezy jest SZYBSZY, a roznice robi zaslepka zdejmujaca 64 testy narzedzia, nie brak pamieci podrecznej bajtkodu. Sonda pokrycia liczy sie **RAZ na przebieg**, kosztuje **~272 s** i to jest **84 % narzutu przed pierwsza mutacja**; licznik wierszy spowalnia zestaw **5,3-krotnie**. **CZEGO POMIAR NIE WYJASNIA:** suma czesci daje ~6,2 min wobec obserwowanych ponad 20 — **co najmniej dziesieciu minut nie umiemy przypisac**, i raport mowi to wprost, zamiast dopasowywac liczby. Nie zmierzono tez mutacji na minute przy 1, 2 i 4 robotnikach, czego zadalo pole Wyjscie. Reszta w 6.B20 | pomiar narzedzia pomiarowego: gdzie idzie czas, ile kosztuje `git worktree add` na mutacje, czy sonda pokrycia liczy sie raz czy za kazdym razem | M |
| 6.B19 | **Wpis dziennika mutacyjnego nie wie, z jakiego drzewa pochodzi** — nie niesie commita, a identyfikator mutacji to `plik:wiersz:przesunięcie bajtowe`, więc dziennik z wcześniejszego drzewa może podstawić wynik zapisany dla innego kodu | znalezione przy 6.B17 i tam świadomie nietknięte, bo tamta pozycja dotyczyła **ścieżki**, nie formatu. Pomiar i poprawka, żadnej decyzji | S |
| 6.B21 | **ZROBIONE (06.09.2026).** `tools/tests/test_xml_doc_blocks.py`: dwa istniejące testy bramki (`test_no_member_carries_two_summary_blocks`, `test_every_summary_is_closed_in_its_own_block`) rozłożone na wywołanie zwykłej funkcji (`_duplicate_summary_offenders`, `_unclosed_summary_offenders`) branej na liście ścieżek, żeby ta sama funkcja jechała po prawdziwym `_sources()` i po pliku wstrzykniętym w kontroli. Trzy nowe testy budują `.cs` w `tempfile.TemporaryDirectory()` (na dysku, nie w pamięci — nic zewnętrznego, bez `dotnet`): zdublowany `<summary>` przy jednym składniku zapala `_duplicate_summary_offenders` (1 offender, `Duplicated.cs:3 — 2 bloków <summary>`) i NIE zapala kontroli urwanego bloku; urwany `<summary>` (bez `</summary>`) zapala drugą bramkę (`1 otwarć, 0 zamknięć`) i NIE zapala pierwszej; plik czysty (jeden `<summary>`, domknięty) nie zapala żadnej z dwóch. Wykonane osobno w obie strony poza zestawem: `_duplicate_summary_offenders` na pliku zdublowanym pod `assert not …` daje `AssertionError` (bramka się zapaliła), na pliku czystym przechodzi. Zestaw **1716 → 1719** testów, moduł bramki **3 → 6** testów, `python3 tools/tests/test_all.py`: **1719/1719 przeszło**, `grep -cE '^\s*FAIL'` daje **0**. Treść pierwotna: **`test_xml_doc_blocks.py` sprawdza tylko drzewo, ktore JEST czyste** — nikt nie wstrzykuje tam sztucznie zdublowanego bloku `<summary>`, wiec bramka nie ma dowodu, ze umie zaswiecic | znalezione przy 6.B15. Naprawa tania, kontrola negatywna wykonalna bez zadnego narzedzia zewnetrznego | S |
| 6.B22 | **ZROBIONE (06.09.2026).** Nowy raport `reports/negative-control-audit-tresc.md`, zmierzone na `936c4ad`: liczby zastane z raportu 6.B15 (`045730b`) — **80** modułów, **34** z frazą dosłowną, **38** w odmianie dowolnej, z czego **8 przeczytanych**, **30 nie**; liczby dzisiejsze — **84** modułów, **36** dosłowna, **39** odmiana (jeden moduł doszedł: `test_xml_doc_blocks.py`, dostał prawdziwą kontrolę w 6.B21). Z 39 dzisiejszych, **10 rozstrzygniętych wcześniej** (8 próbką 6.B15 + 2 przeczytane w pełni: `test_streaming_fixture.py`, `test_xml_doc_blocks.py`) nie czytane ponownie; **29 przeczytanych w tej pozycji, wszystkie z werdyktem WYKONANA** — sito ze 100 % pokryciem 149 wystąpień (blok `def`/`class` wokół frazy zawiera `assert`/`raise`), 5 wystąpień bez tego oznaczonych i doczytanych ręcznie (`test_docs_ci_claims.py`, `test_report_claims.py`, `test_report_hygiene.py`, `test_surface_sections.py`, `test_t401_citation.py` — wszystkie okazały się odsyłać do kontroli wykonanej gdzie indziej w tym samym pliku), plus ręczna próbka z pozostałych 144 wystąpień w każdym z 29 plików. Zero modułów w kategorii „fraza bez żadnej kontroli za nią" — więc zero dopisanych testów. Jeden niuans nazwany z imienia, nie usterka: `test_dimension_audit.py` niesie kontrolę wykonaną RĘCZNIE (prawdziwy `FAIL` wklejony do docstringu, plik przywrócony po pomiarze), nie jako osobny automatyczny test regresyjny — nazwane w raporcie §5, nic nie dopisane. `python3 tools/tests/test_all.py`: **1734/1734 przeszło**, `dotnet test tests/Sim.Tests`: **534/534 przeszło**, zero zmian w `src/` i w `tools/tests/`. Treść pierwotna: **Tresc 30 z 38 modulow z fraza `kontrola negatywna` nie zostala sprawdzona** — 6.B15 zweryfikowal probke 8 z 38 i powiedzial to wprost | modul moze nazwac kontrole i jej nie wykonac; fraza jest przyblizeniem, nie dowodem. Doczytanie reszty to pomiar, nie decyzja | M |
| 6.B20 | **Dziesieciu minut przegladu mutacyjnego nadal nikt nie umie przypisac** — 6.B18 zmierzyl czesci i wyszlo ~6,2 min wobec obserwowanych ponad 20 | pomiar, nie decyzja: 6.B18 rozlozyl narzut na czesci i **powiedzial wprost**, ze suma sie nie zgadza; zostaje znalezc reszte i domierzyc mutacje na minute przy 1, 2 i 4 robotnikach, czego tamta pozycja nie zdazyla | M |

#### Pasmo C — warstwa silnika (`src/Game`)

| # | zadanie | dlaczego bez decyzji | rozmiar |
|---|---|---|---|
| 6.C3 | **ZROBIONE (06.09.2026).** Tryb `--from-telemetry=PLIK` rozstrzyga `src/Game/RunPlan.cs`, prowadzi `src/Game/FirstRun.cs`, a format czyta nowy `src/Game/TelemetryTrack.cs` (bez Godota, więc z testami jednostkowymi). Czwarta odmowa łączenia źródeł ruchu weszła w ten sam wzorzec co trzy istniejące i wymienia oba tryby z nazwy — sześć par: z `--line`, `--replay`, `--input-log`, `--shot`, `--signalling` i `--sample-every`. Testy: `tests/Game.Tests/RunPlanTests.cs` i `tests/Game.Tests/TelemetryTrackTests.cs`; bramka i kontrola negatywna w `.github/workflows/godot-first-run.yml`. Zmierzone: echo wczytanego pliku wychodzi identyczne co do bajtu przy 319 i przy 5457 klatkach, a rozjazd 0,0001 m w jednym wierszu `compare` odrzuca ze wskazaniem numeru wiersza. **Blok sześciu pól niżej ma dwie liczby nieaktualne i jedną komendę niewykonalną** — odmowy stoją w wierszach 339, 353 i 360, nie 356 i 363, a `--line --telemetry` z pola „Weryfikacja" istniejąca odmowa odrzuca kodem 9; nietknięte, bo zadanie dotyczyło wiersza kolejki, nie bloku. Treść pierwotna: **Odtwarzanie przejazdu z pliku telemetrii** — scena jako widok zapisanego przebiegu | wynika wprost z zasady „linia jest symulacją, kabina jednym z jej widoków" | M |
| 6.C4 | **Kamera inspekcyjna** do oglądania geometrii bez jazdy | narzędzie weryfikacji, nie decyzja estetyczna: nie zmienia ani jednego materiału | S |
| 6.C5 | **ZROBIONE (06.09.2026).** Trzy liczby policzone osobno — `RunPlan.Mode` zwraca sześć literałów (`from-telemetry`, `replay`, `telemetry`, `shot`, `line`, `manual`), tabela §1.3 ma sześć wierszy z tymi samymi nazwami, nagłówek mówił cztery. Nagłówek przepisany na „Sześć trybów", nie zdjęty: liczba dała się policzyć z kodu, więc dostała bramkę zamiast zniknąć — `tools/tests/test_run_mode_claims.py`, dwie kontrole negatywne wykonane (rozjazd nagłówka i dopisana siódma gałąź w kodzie), obie złapane i przywrócone. Raport `reports/liczba-trybow-run-plan.md`. Treść pierwotna: **Naglowek §1.3 raportu o drodze do grywalnosci liczy tryby recznie** — mowi „Cztery tryby" nad tabela, ktora ma dzis szesc wierszy | znalezione przy 6.C3, ktory dopisal zdanie obok, ale liczby nie ruszyl. Ta sama rodzina usterki co #273: liczba stojaca w jednym miejscu i nigdzie nie liczona rozjezdza sie bezszelestnie | S |

#### Pasmo D — weryfikacja i CI

| # | zadanie | dlaczego bez decyzji | rozmiar |
|---|---|---|---|
| 6.D1 | **ZROBIONE w #282 (06.09.2026).** Bramka chodzi w `sim-tests.yml` (krok + kontrola negatywna + artefakt przy porażce), narzędzie w `tools/ci/assert_line_trace.py`, wzorzec w `tests/data/golden-trace/`, 16 testów, raport `reports/golden-trace-gate.md`. **Pierwszy pomiar obalił liczbę z treści pozycji:** sześć osi daje dziś **515 807** wierszy, nie 453 107 — o 62 700 więcej, i to dokładnie **+1140 na każdy postój**, na wszystkich sześciu osiach bez wyjątku. Drugi pomiar pokazał, że to NIE `src/Sim`: drzewo commita `90a8c31`, zbudowane i uruchomione dziś, daje na L5_D 56 733 wiersze, czyli tyle co `main`, a nie 49 893 z własnej tabeli. Różnicę zrobiło środowisko uruchomieniowe (.NET 8 → .NET 10), i stąd wniosek projektowy bramki: **wersja runtime jest częścią wzorca**, porównywana co do rodziny, nie co do łatki, bo workflow pina `10.0.x`. Rozstrzygnięte także pytanie o miejsce wzorców: pełne ślady to **32,0 MiB**, więc wzorcem jest para — suma SHA-256 wykrywa rozjazd, a próbka co 100 wierszy (332 KiB) go lokalizuje. Kontrola negatywna z `90a8c31` odtworzona: próg hamowania przesunięty o 0,1 % daje na L1_A przedział **2903..3002**, a więc zawierający wiersz 2910, który podała tamta ręczna kontrola | metoda sprawdzona i udowodniona w `90a8c31`; zostaje uruchomienie jej cyklicznie | L |
| 6.D2 | **Bramka na czas przebiegu** — regres wydajności rdzenia widoczny, zanim zablokuje N składów | pomiar, nie decyzja | S |
| 6.D4 | **ZROBIONE w #273 (06.09.2026) — wpis zostaje w kolejce z powodu zapadki.** Wykonane: `tools/tests/test_report_claims.py` i `reports/report-claims-audit.md`. **Pierwszy pomiar zawęził zakres pozycji i to jest jej główny wynik:** z ośmiu twierdzeń postaci „`plik_testowy`, N testów” **siedem rozjechało się z drzewem i siedem jest poprawnych** — raport opisywał plik w dniu pomiaru, a plik urósł; bramka żądająca tam równości kazałaby przeliczać datowany pomiar, czego zakazuje 6.D3. Sprawdzalna jest **wartość stałej**: 65 nazw pada w raportach, 37 ma definicję w kodzie, **12 jest zacytowanych z wartością i wszystkie 12 się zgadzają**. Wzorzec trzeba było zwęzić — wersja pierwsza dała **3 fałszywe alarmy na 15** przez tabele odwzorowań `219 → NAZWA, 237 → INNA`, w których brała numer wiersza następnej pary za wartość poprzedniej. Druga poprawka wyszła z tego, że bramka **wywróciła się na własnym raporcie**: cytat z kontroli negatywnej wygląda jak twierdzenie, więc bloki ogrodzone są pomijane. Zgłoszone, nie poprawione: `M7-shell.md` mówi 22 testy przy 21 w pliku — jedyny rozjazd w stronę, której datowanie nie tłumaczy. Treść pierwotna: **kontrola spójności liczb między `reports/` a kodem** — wartość wypisana w raporcie musi dać się odtworzyć z repo | dokładnie ta klasa rozjazdu, którą audyt znalazł w README | M |
| 6.D5 | **ZROBIONE w #259 (`08d9650`, 05.09.2026) — wpis zostaje w kolejce z powodu zapadki**, jak 6.D6, 6.B10, 6.B1 i 6.B8. Wykonane: `reports/mutation-drift.md` obejmuje **28 modułów** zamiast wymaganych dwunastu, a `tools/tests/test_mutation_sweep.py` ma sześć testów dryfu, w tym `test_drift_report_pins_the_two_cases_the_task_names`, czyli dokładnie kryterium „Skończone, gdy”. Znalezione audytem kolejki 05.09.2026, nie zgłoszone przy scaleniu. Treść pierwotna: **Audyt dryfu pokrycia mutacyjnego po triażu** — które moduły odzyskały ocalałe od czasu swojego raportu triażu, i przybicie ich z powrotem | rozjazd jest już zmierzony i leży w dwóch plikach naraz: `tools/track/crs.py` miał po triażu 6 ocalałych na 8 mutacji (`reports/mutation-triage-wczytywanie.md` §Wynik), a przebieg z `66b8301` w `reports/mutation-sweep.md` pokazuje **8 na 14**; `tools/ci/assert_shot_metadata.py` miał **2 na 33** (`reports/mutation-triage-png-metadata.md` §Wynik), a dziś ma **6 na 39**. Porównanie dwóch raportów, które już istnieją — żadnej nowej danej | M |
| 6.D6 | **ZROBIONE w #258 (05.09.2026) — wpis zostaje w kolejce z powodu zapadki, nie dlatego, że jest do zrobienia.** `test_backlog.py` trzyma `MINIMUM_DOCUMENTED_ITEMS = 8`, a udokumentowanych pozycji jest dokładnie osiem; przeniesienie którejkolwiek do tabeli domknięć zbija licznik do siedmiu i wywraca `test_the_documented_reserve_does_not_regress`, a komentarz przy zapadce mówi, że wolno ją tylko podnosić. Decyzja właściciela z 05.09.2026: wpis zostaje z tą adnotacją. Treść pierwotna: **rozszerzenie zestawu operatorów `tools/tests/mutation_sweep.py`** poza porównania i progi liczbowe — przypisania, wywołania i łączniki logiczne. Wykonane: dwie klasy urosły do pięciu (`logika`, `argument`, `przypisanie`), a stary zestaw odtwarza `--operators operator,prog` co do sztuki (1038 = 1038) | `reports/mutation-sweep.md` §„Czego ten przebieg NIE pokrywa, choć pozycja 5.1 tak brzmi" wypisuje ten brak w tabeli: pozycja 5.1 mówi „każdą kontrolę", a narzędzie mutuje „wyłącznie **operatory porównań i progi liczbowe**; nie mutuje przypisań, wywołań ani łączników logicznych". Praca w samym narzędziu pomiaru; baza do porównania jest zmierzona (980 mutacji, 51 nieosiągalnych, 929 policzonych na `66b8301`) | L |
| 6.D7 | **ZROBIONE w #278 (06.09.2026).** `NAMES_THE_PLATFORM_PARAMETER` wymaga teraz **współwystąpienia słowa „peron"** z wyrażeniem o jawnym parametrze i przyjmuje odmianę (`jawn\w+ parametr\w*`), więc zwężenie jest zarazem rozszerzeniem. W korpusie bramki **5 → 4 trafienia**: wypadło dokładnie to fałszywe (udział odzysku energii z bloku 6.A5), nie ubyło ani jedno prawdziwe, a doszły zdania w rodzaju „długość peronu **jest jawnym parametrem**", których stara wersja nie widziała, bo szukała frazy w mianowniku. Dwie kontrole negatywne wykonane; **druga jest tu ważniejsza** — zdanie dopisane bez nazwy stałej, samym zwrotem w odmianie, zapala bramkę, czego stary wzorzec nie robił. Bez niej „zwężenie” mogłoby po cichu zejść do szukania samej nazwy `DESIGN_PLATFORM_LENGTH_M` i przestać sprawdzać prozę. `PARAMETER_VALUE` zostawiony szeroki z powodem przy stałej: żąda wartości w metrach, więc zdania o procentach nie zapala, a jest ostatnią rzeczą widzącą wiersz, w którym generator dostaje wartość jawnym parametrem bez słowa „peron” obok — treść pierwotna: **`NAMES_THE_PLATFORM_PARAMETER` w `test_dimension_audit.py` łapie samo wyrażenie „jawny parametr"** i żąda od niego wartości 95,0 m — także wtedy, gdy zdanie mówi o zupełnie innym parametrze | zmierzone 06.09.2026 przy #272: zdanie o udziale odzysku energii w bloku 6.A5 zapaliło bramkę długości peronu. Zwężenie wzorca to ta sama praca co przy `test_report_claims.py` (#273), gdzie zwężenie zdjęło 3 fałszywe alarmy na 15 | S |
| 6.D8 | **ZROBIONE w #277 (06.09.2026).** Rozstrzygnięte: **liczba była nieprawdziwa od początku**, nie zestarzała się. `reports/M7-shell-liczba-testow.md` pokazuje to pomiarem, nie argumentem: plik testowy i raport wnosi do drzewa **ten sam commit** (`de574ff`, squash-merge PR-a #43), plik ma przez całą historię **jeden niezmieniony blob** `efae116`, a w każdej osiągalnej wersji — łącznie z jedynym commitem gałęzi przed squashem — `grep -c '^def test_'` daje **21**. Nie ma w historii momentu, w którym obie liczby byłyby zgodne, więc możliwość „testy usunięto” jest wykluczona pomiarem. Skąd wzięło się 22: `grep -c '^def '` daje 22, bo liczy też pomocnika `_layout()`, którego `test_all.py` nie zbiera — policzono definicje zamiast testów. `reports/M7-shell.md` **przepisany**, nie dopisany obok, z pomiarem zostawionym w wierszu 77, żeby odsyłacz z §1 audytu dalej w niego trafiał — treść pierwotna: **`reports/M7-shell.md` mówi „22 testy" przy 21 w pliku** — jedyny rozjazd liczby testów, którego datowanie NIE tłumaczy | siedem pozostałych rozjazdów z `reports/report-claims-audit.md` §1 idzie w stronę „raport mniej, plik więcej", czyli plik urósł po pomiarze. Ten idzie w drugą: raport nie mógł policzyć więcej testów, niż plik miał. Rozstrzyga `git log --follow` po `tools/tests/test_m7_shell.py`, bez ani jednej decyzji | S |
| 6.D9 | **ZROBIONE w #288 (06.09.2026).** `idat_sha256` jest wołane z `capture_blender.py` (obok sumy pliku, nie zamiast) i z `compare.py` pod przełącznikiem żądania zgodności co do bajtu; `visual_smoke.sh` używa go w teście determinizmu i ma obok kontrolę negatywną na JEDEN piksel. 9 testów, zestaw **1694 → 1703**, raport `reports/pixel-hash-oracle.md`. **Pomiar:** dwa przebiegi tej samej sceny, pięć klatek — **suma pliku różna na wszystkich pięciu, suma `IDAT` identyczna na wszystkich pięciu**; z 18 chunków PNG różnią się dokładnie dwa, oba `tEXt`: `Date` i `RenderTime`. **Co to naprawdę zmieniło:** test determinizmu pytał dotąd wyłącznie o progi, a różnica jednego kanału jednego piksela mieści się w progach z manifestu i przechodziła tędy po cichu — test nazywał się determinizmem, a mierzył podobieństwo. Progi zostają nietknięte tam, gdzie porównuje się różne sceny. Przy okazji kalibracja wyroczni z #268 złapała **mój własny test bez ani jednej asercji** | narzędzie i dowód, że suma całego pliku PNG jest bezużyteczna jako wyrocznia, są już w repo; zostaje zastosowanie | M |
| 6.D10 | **ZROBIONE w #292 (06.09.2026).** Zmierzone na HEAD (`08d12b6`), nie na `51d324a` z opisu pozycji — w tej sesji doszło 8 raportów od tamtego pomiaru: **69** raportów (nie 48) niosą SHA w nagłówku. Dla każdego zbadana relacja (`git log --follow` / `git merge-base --is-ancestor` na commicie, który wpisał ten konkretny token, przez pickaxe `-S`, nie na pierwszym dodaniu pliku — węższa wersja fałszywie dawała ŻADNA sześciu raportom, którym SHA był przodkiem edycji nagłówka): **23 dotyka, 41 przodek wprowadzenia, 4 ŻADNA (z nazwy: `bpy-extraction-round-2.md`, `bpy-extraction-round-3.md`, `energy-balance.md`, `mutation-triage-round-2-modules.md` — wszystkie ten sam wzorzec: SHA gałęzi sesyjnej, `main` dostał inny obiekt przy scaleniu), 1 NIEOSIĄGALNY (`mutation-triage-lod.md` / `c572eb3`, już opisany w `test_report_hygiene.py`)**. Bramki **nie dopisano**: cztery przypadki ŻADNA to powtarzalny tryb pracy tej sesji, nie zamknięta lista wyjątków, a relacja i tak nie przetrwałaby CI — sprawdzone wprost na płytkim klonie (`--depth 1`), gdzie `git merge-base --is-ancestor` nie ma historii do rozstrzygnięcia, dokładnie jak `actions/checkout` na self-hosted runnerze (`CLAUDE.md` §9) — pomiar w `reports/commit-naglowka-a-raport.md` | pozycja mierzy relację, a nie decyduje o niej; dopiero pomiar mówi, którą wolno przybić bramką, a której nie wolno | S |
| 6.D11 | **ZROBIONE (06.09.2026).** Liczba 1638 była już nieaktualna — zestaw ma dziś **1709** testów w **80** modułach (**1715**/**81** po dopisaniu tej pozycji). Cztery przebiegi CAŁEGO `python3 tools/tests/test_all.py` z rzędu na kontenerze dzielonym z innymi sesjami agenta: **66,20 / 68,45 / 68,96 / 77,04 s** — rozrzut 15,45 % przy tym samym kodzie. Próg **`SUITE_RUNTIME_BUDGET_S = 150,0`** w nowym `tools/tests/test_suite_runtime_budget.py` to ×2 nad najwyższym zmierzonym przebiegiem (77,04 s), zaokrąglone w dół; margines pochłania prędkość maszyny właściciela (nieznaną tej sesji) i codzienny przyrost zestawu. Bramka żyje w kroku CI (`.github/workflows/python-tests.yml`), **nie** w kodzie wyjścia `test_all.py` — `tools/tests/mutation_sweep.py` czyta z tego procesu WYŁĄCZNIE linię `N/M przeszło` i kod wyjścia jako dowód przeżycia mutacji, więc czas związany z tym kodem zamieniłby zwykłe spowolnienie maszyny w falę fałszywych „zabić". Dwie kontrole negatywne WYKONANE: próg obniżony do 10,0 w drzewie pada natychmiast na własnej bramce asercji (`1713/1715`, dwa `FAIL`), a to samo porównanie bash z kroku CI, uruchomione na realnym zmierzonym czasie z progiem obniżonym do 40,0, daje kod wyjścia 1. Pełna tabela per moduł (81 wierszy) i uzasadnienie marginesu: `reports/test-all-runtime-gate.md`. Treść pierwotna: **Bramka na czas przebiegu `test_all.py`** — 1638 testów w 62,8 s, i nikt tego nie pilnuje | bliźniak 6.D2 po stronie Pythona: pomiar, nie decyzja | S |
| 6.D12 | **ZROBIONE (06.09.2026).** Cztery miejsca piszą do `data/`: `fetch_gtfs.py` i `fetch_stib_shapes.py` bezpośrednio (manifest proweniencji zmienia się przy każdym uruchomieniu, **także w `--offline`** — zmierzone dwoma realnymi przebiegami `fetch_gtfs.py` dziś, identyczny `content_sha256`, różny tylko `retrieved_at`), `build_alignment.py` i `normalize_stops.py` pośrednio — oba osadzają `retrieved_at` manifestu w commitowanym pliku wynikowym (`data/track/*.json`, `data/network/stops.json`), więc dziedziczą tę samą niestabilność bez własnego wywołania zegara. Sprawdzone i odrzucone: `snapshot_source.py`, `data_freshness.py` i dziewięć pozostałych narzędzi `tools/track/*.py` — `--out` wymagane lub domyślnie poza `data/`, żadne udokumentowane wywołanie ich tam nie kieruje. Pomiar w `reports/zapisy-do-data.md`, cztery warianty na klasę zapisu wypisane obok siebie z kosztem każdego — treść pierwotna: **Które narzędzia piszą do `data/`, choć katalog jest tylko do odczytu** — `tools/track/fetch_gtfs.py` aktualizuje manifest proweniencji przy każdym pobraniu | `CLAUDE.md` §4.6 nie przewiduje wyjątku, a narzędzie robi to celowo. Pozycja **mierzy rozjazd i wypisuje warianty**, nie rozstrzyga go — wybór między zmianą reguły a zmianą narzędzia zostaje właścicielowi | S |
| 6.D13 | **Wzorzec SHA w bramce higieny raportow lapie tez to, co SHA nie jest** — token `9e2066aef7ef` w naglowku jednego raportu to hash builda Blendera, nie commit | znalezione przy 6.D10. Pomiar, ile takich falszywych trafien jest w 71 raportach, i zawezenie wzorca albo nazwanie wyjatku — bez decyzji wlasciciela | S |
| 6.D14 | **ZROBIONE (06.09.2026).** Dwa nowe testy w `tools/tests/test_fetchers.py`, po jednym na narzędzie: `test_fetch_gtfs_offline_never_calls_provenance_fetch_url` i `test_fetch_stib_shapes_offline_never_calls_provenance_fetch_url`. Oba podmieniają `provenance.fetch_url` (jako `P.fetch_url` w module narzędzia) na funkcję rzucającą `RuntimeError`, budują minimalny poprawny plik wejściowy w katalogu tymczasowym — pięcioplikowy GTFS dla `fetch_gtfs.py`, dwuplikowy shapefile (linie + przystanki, zbudowany w locie bez `bpy`) dla `fetch_stib_shapes.py` — i sprawdzają, że `main(["--offline", ...])` kończy się kodem **0**; `SystemExit`, gdyby jednak padł, jest złapany jawnie i zamieniony w `AssertionError`, bo inaczej uciekłby jako `BaseException` mimo `except Exception` w `test_all.py` i wywróciłby cały zestaw zamiast tylko tych dwóch testów. `test_fetchers.py`: **16 → 18** testów; cały zestaw: **1736 testów, zielony**, kod wyjścia 0. Kontrola negatywna WYKONANA: to samo wywołanie bez `--offline` (podmieniona funkcja faktycznie zostaje wywołana) wywraca **dokładnie te dwa i tylko te** — `1734/1736 przeszło`, reszta bez zmian — po czym plik przywrócony do wersji z `--offline`. `git status --short data/` puste po całym przebiegu. Treść pierwotna: **Czy `--offline` w `fetch_gtfs.py`/`fetch_stib_shapes.py` naprawdę nie dotyka sieci** — zmierzone przy 6.D12 czytaniem kodu (`P.utc_now_iso()` zamiast `P.fetch_url()` w tej gałęzi), nie testem z zablokowaną siecią | dowód sieciowy jest testem: podmiana funkcji pobierającej na wersję rzucającą wyjątek i sprawdzenie, że `--offline` mimo to kończy się sukcesem — bez ani jednej decyzji właściciela | S |
| 6.D15 | **ZROBIONE (06.09.2026).** Zebrane **82** komendy z **42** blokow (stan bloku szczegolow w chwili pomiaru). Werdykty: **73** uruchamialne, **4** wymagaja Blendera albo geometrii, ktora Blender produkuje, **5** niewykonalnych tak, jak pole obiecuje. Piec niewykonalnych z nazwy: 6.D2 (pole wymienialo 3 z 7 opcji, ktorych wymaga `Budget` — kod 1 na `BLAD: line wymaga --limit-kmh`), 6.A6, 6.C3 (kod 9, odmowa laczenia zrodel — to znalezisko otworzylo te pozycje), 6.D9 i 6.B18 (miejsce do wypelnienia w nawiasie ostrokatnym). Najciezsze znalezisko jest w 6.A6: `--coast-from-m` nie wystepuje nigdzie w `src/`, a `Sim.Runner` **nieznana opcje przyjmuje w milczeniu**, wiec obie komendy pola koncza sie kodem 0 i daja pliki **identyczne co do bajtu** — te weryfikacje spelnia NIEZROBIENIE zadania. Poprawione trzy pola pozycji niezrobionych (6.D2, 6.A6, 6.C4 o brakujacy warunek wstepny: kod 4, `[ASSETS] brak manifestu`); bloki pozycji ZROBIONYCH zostaly nietkniete jako zapis historyczny. Kolektor komend jest w `tools/tests/backlog_commands.py`, bramka na miejsca do wypelnienia w `tools/tests/test_backlog_commands.py` (trzy WYKONANE kontrole negatywne), pomiar w `reports/komendy-weryfikacji.md`. Tresc pierwotna: **Ile komend z pol „Weryfikacja" w blokach kolejki da sie w ogole uruchomic** — komenda z bloku 6.C3 jest odrzucana przez istniejaca odmowe, kod wyjscia 9 | znalezione przy 6.C3. Pole „Weryfikacja" jest obietnica, ktorej nikt nie sprawdza; pomiar, ile z nich klamie, nie wymaga zadnej decyzji | M |
| 6.D16 | **ZROBIONE (06.09.2026).** Zdanie o `retrieved_at` w `docs/09-data-provenance.md` przepisane, nie dopisane obok: teraz nazywa różnicę między **manifestem proweniencji** (`retrieved_at` jest tam czystą metadaną obserwacji, poza `content_sha256` surowego wejścia) a **plikiem wynikowym** — `build_alignment.py` kopiuje pole do `document["source"]["retrieved_at"]` w commitowanym `data/track/*.json`, `normalize_stops.py` do `document["feed"]["retrieved_at"]` w commitowanym `data/network/stops.json`, więc dla tych dwóch plików zdanie o niezmienności nie zachodzi. Nowa bramka `tools/tests/test_provenance_retrieved_at_claim.py` (4 testy) pilnuje, żeby stare bezwarunkowe zdanie nie wróciło i żeby oba narzędzia nadal osadzały pole tam, gdzie dokument to dziś opisuje; kontrola negatywna wykonana — z przywróconym starym zdaniem bramka pada (`FAIL test_doc_names_the_manifest_vs_output_distinction_and_both_tools`, kod wyjścia `test_all.py` 1), po przywróceniu poprawki znów zielono. Zestaw narzędzi **1733/1733**, kod wyjścia 0. Poza zakresem, tak jak żądało pole „Poza zakresem": nie rozstrzygnięto, czy narzędzia mają przestać osadzać `retrieved_at`, czy reguła ma dostać jawny wyjątek — to nadal decyzja właściciela. Treść pierwotna: **`docs/09-data-provenance.md` twierdzi cos, co dla dwoch miejsc jest nieprawda** — ze `retrieved_at` nie moze zmieniac byte-deterministycznego wyjscia, a w `build_alignment.py` i `normalize_stops.py` trafia wprost do commitowanego pliku | znalezione przy 6.D12. Pomiar i przepisanie zdania, ktore przestalo byc prawdziwe | S |
| 6.D17 | **ZROBIONE (06.09.2026).** `docs/23-environment.md` ma nową §4.1 z dwoma **wykonanymi** przebiegami tego samego pliku binarnego (`Godot_v4.7.2-stable_mono_linux.x86_64 --headless --path src/Game`): bez `DOTNET_ROOT` i bez `dotnet` w `PATH` — sygnał 11, `Failed to load hostfxr`, 0,34 s; z `DOTNET_ROOT="$HOME/.dotnet"` — hostfxr się ładuje i proces idzie dalej do kodu gry (pada dopiero na osobnym, niepowiązanym braku manifestu chunków — w tym środowisku nie ma Blendera). Zmierzone: `DOTNET_ROOT` sam wystarcza, `dotnet` w `PATH` jest zbędny, jeśli `DOTNET_ROOT` wskazuje katalog z `host/fxr/*/libhostfxr.so`; zły katalog **nie** korzysta z tego skrótu i wraca do tej samej awarii przez `dotnet` odpalane przez powłokę. `doctor.sh` dostał nową sondę **`godot .NET hostfxr`**, bo istniejąca (`--version`) przechodzi identycznie z `DOTNET_ROOT` i bez niego — nie dotyka mono, więc nic by nie złapała; nowa sonda sprawdza `DOTNET_ROOT` (z `host/fxr/*/libhostfxr.so`) albo `dotnet` w `PATH` i nazywa przyczynę zamiast milczeć do limitu czasu, potwierdzone w trzech wariantach (brak obu, sam `DOTNET_ROOT`, sam `dotnet` w `PATH`). Zestaw narzędzi **1716/1716** w 81 modułach, `dotnet test tests/Sim.Tests` **528/528**. Druga postać usterki z opisu tej pozycji (zawieszenie bez wyjścia przy brakującym assembly) nie została odtworzona osobno — nie ma tu scenariusza z hostfxr załadowanym i brakującym konkretnym assembly do zademonstrowania; dokument nazywa ją i mówi wprost, że nie jest tu pokazana. Poza zakresem: `.github/workflows/` nietknięte. Treść pierwotna: **`docs/23-environment.md` nie mowi, ze Godot wymaga `DOTNET_ROOT`, nie tylko `PATH`** — bez tego pada `Failed to load hostfxr` sygnalem 11, a przy brakujacym assembly wisi bez ani jednego wiersza na stdout do wypalenia limitu czasu | znalezione przy 6.C3, na wlasnej skorze. Dokument ma powiedziec to, co trzeba ustawic | S |
| 6.A11 | **ZROBIONE (06.09.2026).** `Sim.Runner` odmawia nieznanej opcji w kazdym z **dziewieciu** polecen: `line ... --coast-from-m X` konczy sie teraz kodem **1** i komunikatem `BLAD: polecenie line nie zna opcji --coast-from-m. Zna: ...` — wczesniej kod 0 i przebieg nie do odroznienia od poprawnego. Kod wyjscia NIE jest nowa stala: to ta sama, ktora `Program.cs` daje wszystkim odmowom argumentowym przez wspolny handler `ArgumentException`. Tabela `KnownOptions` jest reczna, zeby komunikat wymienial opcje TEGO polecenia, a nie sume wszystkich — i dlatego dostala bramke `tools/tests/test_runner_options.py`, ktora czyta `Program.cs` jako tekst, wyprowadza nazwy z wywolan `Option`/`RequiredNumber`/`OptionalNumber`/`Array.IndexOf` i porownuje oba zbiory w OBIE strony, bez `dotnet`. Nietkniete i sprawdzone uruchomieniem: argument pozycyjny (`compare A B`) przechodzi, flaga `--atp` nie zjada nastepnego czlonu, ta sama komenda bez nieznanej opcji nadal konczy sie kodem 0. Cztery WYKONANE kontrole negatywne, kazda wywraca dokladnie te testy, ktore ma (`dotnet test` 528 -> **532**). Pomiar w `reports/nieznana-opcja-runnera.md`. Tresc pierwotna: **`Sim.Runner` przyjmuje nieznana opcje w milczeniu** — `line ... --coast-from-m X` konczy sie kodem 0, choc ani opcji, ani wartosci `X` nie ma w kodzie | zmierzone przy 6.D15 (#301): dwie komendy z pola „Weryfikacja" pozycji 6.A6 daly pliki identyczne co do bajtu. Wyrocznia zepsuta w strone „wszystko w porzadku" | M |
| 6.A12 | **ZROBIONE (06.09.2026).** Dwa mechanizmy, oba zmierzone, zaden nie jest bledem. **Pierwszy: okno krotsze niz jeden odstep.** Sklady sa zglaszane na krok `i x odstep`, wiec przy `--headway-s 120` (14 400 krokow) i `--steps 1000` (okno **8,3 s**) sklad numer 1 wypada poza okno pomiaru — `N_max = 1` niezaleznie od `--trains`. **Drugi: sufit 12 skladow na tej osi.** Przy oknie 1667 s i odstepie 30 s ORAZ 10 s `N_max` przestaje rosnac na **12**, a `N_sr` stoi na **7,56** — dla 12, 13, 16 i 24 zgloszonych identycznie co do cyfry; przybywa wylacznie kolumna „czeka" (4,05 -> 4,97 -> 7,72 -> 14,79). Mechanizmem jest **brama wjazdowa** `LineCore.EntryIsClear`: sklad wjezdza tylko, gdy zaden blok nakladajacy sie na jego obrys w punkcie wjazdu nie jest zajety, a plan ma 23 bloki. Dla 6.D2 istotne: **dziewiec skladow jest osiagalne** (`N_max = 9` przy odstepie 10 s i oknie 200 000 krokow), koszt **4,540 us/krok** = 0,05 % budzetu 1/120 s, a przy suficie 12 — **5,995 us/krok** = 0,07 %. Pomiar w `reports/obsada-planu.md`. Tresc pierwotna: **`budget --trains 32` melduje `N_max=1`** — kolumna `N_zgl` nie jest liczba skladow, ktore bieglyby po planie | zmierzone przy 6.D15 (#301). Pomiar wydajnosci, ktory nie obciaza tego, co obiecuje obciazyc, jest bramka bez zebow — a na tej liczbie ma stanac 6.D2 | M |
| 6.A13 | **ZROBIONE (06.09.2026).** Plik, ktory planem blokow nie jest, konczy sie teraz odmowa **kod 1** z komunikatem `dokument nie ma pola 'protection_variant' — to nie wyglada na plan sygnalizacji…`, zamiast kodem **134** i stosem wywolan. Poprawka jest jednym pomocnikiem `Required(owner, field, what)` w `SignallingPlan.FromJson`, ktory zamienia `JsonElement.GetProperty` na `TryGetProperty` + `FormatException` w **11** odczytach na poziomie dokumentu plus w `DesignValue` i w polu `generation`. **Nie wprowadza nowego kodu wyjscia**: `FormatException` jest na liscie handlera od poczatku i uzywaja jej wszystkie pozostale odmowy tego loadera. Dwa testy, oba na PRAWDZIWYCH plikach z `data/` (atrapa dowodzilaby czegos innego niz to, co sie zdarzylo): `cbtc-test-2026.json` konczy sie odmowa, `classic-2026.json` nadal przechodzi kodem 0. Kontrola negatywna WYKONANA — powrot do `GetProperty` wywraca dokladnie jeden test (535/536). `dotnet test` 534 -> **536**. Tresc pierwotna: **Plan CBTC wywraca `Sim.Runner` sygnalem, nie odmowa** — `budget --signalling data/design/signalling/cbtc-test-2026.json` konczy sie kodem **134** i stosem wywolan, bo `KeyNotFoundException` z `SignallingPlan.FromJson` nie jest lapany przez wspolny handler `Program.Main` | znalezione przy 6.A12. Plik jest opisem obszaru i trybu (`area_id`, `mode`, `status`), a nie planem blokow — komunikat ma to powiedziec, a nie sypnac stosem | S |
| 6.B23 | **Licznik „modul `src/Sim` bez testu" skanuje razem z `obj/`** — po `dotnet build` wypisuje cztery falszywe wiersze `BRAK TESTU` dla plikow generowanych | zmierzone przy 6.D15 (#301). Licznik zyje dzis wylacznie jako wiersz powloki w zapisie historycznym 6.A8; jako bramka w `tools/tests/` nie istnieje | S |
| 6.D18 | **`--only` w `mutation_sweep.py` dopasowuje podciag, nie nazwe pliku** — `--only sweep.py` obejmuje `tools/blender/sweep.py` (117 mutacji) **i** `tools/blender/tunnel_sweep.py` (68) | zmierzone przy 6.D15 (#301). Kazdy raport z przegladu mutacyjnego wolany basename'em mowi o innym zbiorze plikow, niz nazywa | M |
| 6.D19 | **ZROBIONE (06.09.2026).** `_discover()` w `test_all.py` łapie teraz wyjątek z `AG.load_instrumented()` per moduł zamiast zostawiać go nieprzechwyconym — moduł, który się nie importuje, dostaje wiersz `FAIL <import>nazwa_pliku: KlasaWyjątku: komunikat`, liczy się do `failed` (kod wyjścia zostaje 1) i nie blokuje odkrycia pozostałych modułów ani wiersza `N/M przeszło`. Kontrola negatywna WYKONANA: moduł z `def test_broken(:` wrzucony do `tools/tests/` — PRZED zmianą `kod: 1`, zero dopasowań `grep -cE '^\s*FAIL'`, zero wierszy `N/M przeszło` (dokładnie usterka z opisu); PO zmianie `kod: 1`, jeden wiersz `FAIL <import>test_zzz_broken_probe: SyntaxError: invalid syntax (...)`, wiersz `1729/1729 przeszło` obecny. Nowy test `test_gate_a_broken_import_produces_a_grep_visible_fail_line_and_keeps_the_summary` w `tools/tests/test_assertion_gate.py` odtwarza to samo w jednym procesie (podmiana `AG.paths()` na piaskownicę, bez dotykania prawdziwego `tools/tests/`). Zestaw narzędzi **1729 → 1730** testów, zielony. `mutation_sweep.py --only lod_paths.py --workers 2` uruchomiony po zmianie: nadal czyta `N/M przeszło` i kod wyjścia z tego samego procesu, bez zmiany zachowania — wynik wklejony w raporcie sesji. Treść pierwotna: **Modul, ktory sie nie importuje, nie daje ani jednego wiersza `FAIL` ani wiersza `N/M przeszlo`** — `test_all.py` konczy sie wtedy kodem 1, ale kazdy grep po `FAIL` pokazuje zero i wyglada jak zielono | zmierzone przy 6.D15 (#301) na wlasnym module z bledem skladni. Ta sesja sprawdzala zielonosc grepem i przez chwile wierzyla, ze drzewo jest zielone | M |
| 6.D20 | **ZROBIONE (06.09.2026).** Nazwa polecenia bierze sie teraz z `args[0]`, a nie ze stalej w tresci komunikatu — i to jest cala poprawka, jeden wiersz. Zmierzone: `budget` bez `--limit-kmh` dawal `BLAD: line wymaga --limit-kmh`, dzis daje `BLAD: budget wymaga --limit-kmh`; `line` bez `--limit-kmh` nadal daje `BLAD: line wymaga --limit-kmh`. Oba kod 1. `RequiredNumber` jest wspolny dla **trzech** polecen (`line`, `budget`, `replay`), wiec zaszyta nazwa mylila w dwoch przypadkach na trzy. Sprawdzone po jednym: **wszystkie pozostale** komunikaty „X wymaga …" w `Program.cs` sa literalami w ciele jednego polecenia i nazywaja je poprawnie — poprawka dotyczy wylacznie tego jednego miejsca. Dwie WYKONANE kontrole negatywne, kazda wywraca dokladnie jeden test: przywrocona stala `line` wywraca `Budget_bez_limitu_nazywa_budget_a_nie_line`, a nowa, tak samo sztywna stala `budget` wywraca `Line_bez_limitu_nadal_nazywa_line` — para testow lapie wiec rozjazd w obie strony, nie tylko powrot starego bledu. `dotnet test` 534 -> **536**. Tresc pierwotna: **`RequiredNumber` w `Program.cs` nazywa `line` niezaleznie od polecenia** — `budget` bez `--limit-kmh` konczy sie komunikatem `BLAD: line wymaga --limit-kmh` | zmierzone przy 6.D15 (#301). Komunikat kieruje czytajacego do niewlasciwego polecenia; osiem pozostalych polecen ma ten sam problem, bo dziela ten sam pomocnik | S |
| 6.A14 | **Nieliczbowa wartosc opcji daje komunikat po angielsku, bez nazwy opcji** — `line ... --limit-kmh abc` konczy sie `BLAD: The input string 'abc' was not in a correct format.` | znalezione przy 6.D20 (#312). Komunikat nie mowi ANI ktorej opcji dotyczy, ANI ktorego polecenia — a jest to jedyny slad, jaki dostaje czytajacy | S |
| 6.A15 | **Odmowa nieznanej opcji nie widzi czlonu z JEDNYM minusem** — `line ... -zmyslona 7` konczy sie kodem **0**, tak jak przed 6.A11 | znalezione przy 6.A11 (#307) i wypisane tam jako nietkniete; zmierzone ponownie 06.09.2026. Dziura jest waska, ale to dokladnie ta sama wyrocznia zepsuta w strone „wszystko w porzadku" | S |
| 6.B24 | **`test_dimension_audit.py` ma kontrole negatywna wykonana RECZNIE, nie jako test regresyjny** — dowod jest wklejony w docstringu, ale zaden przebieg `test_all.py` go nie powtarza | znalezione przy 6.B22 (#317), §5 raportu, ktore swiadomie tego nie ruszylo. Kontrola, ktora odbyla sie raz, nie chroni przed regresja wzorca | M |
| 6.D21 | **Drugi objaw z 6.D17 nie zostal odtworzony** — zawieszenie Godota bez ani jednego wiersza na stdout przy brakujacym assembly, z zaladowanym hostfxr | znalezione przy 6.D17 (#305), ktore powiedzialo wprost, ze tego nie pokazalo. Objaw, ktorego nikt nie odtworzyl, jest w dokumencie zdaniem z drugiej reki | M |
| 6.D22 | **Raporty z przegladow wolanych `--only` basename'em nie mowia, ile modulow objely** — 6.D18 rozstrzygnela, ze podciag jest zamierzony, i wprost zostawila oznaczenie starych raportow poza zakresem | znalezione przy 6.D18 (#310). Datowanego pomiaru sie nie przelicza, ale wolno go OZNACZYC — i dopoki nie jest oznaczony, czyta sie jak pomiar jednego modulu | S |

#### Szczegóły pozycji z kompletem sześciu pól

**Nagłówek przepisany, a nie dopisany obok — trzeci raz i z tego samego powodu.**
Pierwsza wersja mówiła „Szczegóły **ośmiu** pozycji dopisanych 04.09.2026", druga
poprawiła ją na dwanaście („doszły cztery kolejne — 6.A7, 6.B1, 6.B2 i 6.D2"), i obie
przestały być prawdą, bo **liczba bloków stała w nagłówku wypisana ręcznie**. Bloków
jest dziś **29**: dwanaście z 04–05.09.2026 i siedemnaście z 06.09.2026, z czego dziesięć
z jednego commita uzupełniającego kolejkę. Który blok jest z kiedy, mówi pole **Skąd**
przy nim — i to jest jedyne miejsce, w którym ta informacja się nie starzeje.

Liczby nie ma sensu tu utrwalać niczym więcej niż zdaniem o pomiarze: pilnuje jej
`MINIMUM_DETAIL_BLOCKS` w `tools/tests/test_backlog.py`, a nie ten akapit.

Wiersze tabel wyżej mówią, **dlaczego** pozycja nie wymaga decyzji. Poniżej stoi to,
czego wymaga `CLAUDE.md` §6 i `docs/TASK-TEMPLATE.md`: sześć pól na pozycję, plus jedno
zdanie o tym, **z czego ta pozycja się wzięła** — plik i sekcja. Pozycja bez takiego
odnośnika byłaby zadaniem wymyślonym na miejscu, a §8 zabrania takie brać.

Wspólne dla wszystkich dwunastu: **Poza zakresem** zawiera zawsze `docs/03-legal.md`,
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
- **Skończone, gdy:** wszystkie 9 ma **werdykt poparty pomiarem** — wejście
  rozstrzygające przy mutacji zabijalnej, powód przy równoważnej — a pary z wierszy 46
  i 52 są rozróżnione po `plik:wiersz:przesunięcie`, a nie po `plik:wiersz`.
  `reports/mutation-sweep.md` §„Pułapka odczytu” mówi, dlaczego to nie jest formalność,
  a triaż `sweep.py` (#270) pokazał to kosztem czterdziestu minut: wiersz z czterema
  literałami dostał test przypięty do dwóch niewłaściwych.

  **Poprzednia wersja tego kryterium żądała „udział poniżej 10 %, najwyżej 3 z 31"
  i była nieosiągalna uczciwie** — dlatego jest przepisana, a nie uzupełniona obok.
  Triaż z 05.09.2026 (`reports/mutation-triage-m7-report.md`, #269) pokazał pomiarem,
  że **wszystkie dziewięć to mutanty równoważne**: cztery dlatego, że `round(…, 6)`
  scala trafienie w próg, cztery dlatego, że próg jest nieosiągalny w IEEE 754
  (`1e-4` i `1e-3` nie są wielokrotnościami `ulp` podstaw 1,35 / 0,9 / 1,6), jedna
  dlatego, że stoi za filtrem wykluczającym jedyną różniącą wartość. Zejście do trzech
  wymagałoby albo dopisania testów do zachowania, którego żadne wejście nie odróżnia,
  albo zmiany progów w działającym kodzie pod metrykę. Decyzja właściciela
  z 05.09.2026: kryterium ma żądać werdyktów, nie liczby.
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

##### 6.A7 · Testy własnościowe fizyki

- **Skąd:** wiersz `| 6.A7 |` pasma A („wzmacnia to, co jest; nie dodaje ani jednej
  liczby o metrze") plus tablica referencyjna T-311 w `docs/02-simulation.md`, którą
  `CLAUDE.md` §3 nazywa wprost „tablicą referencyjną **dla testów fizyki**". Pozycja
  dopisana 04.09.2026 jako wiersz tabeli; sześć pól dopisane 05.09.2026.
- **Wejście:** `src/Sim` (model trakcji z T-310, solver punktu hamowania z T-311),
  `docs/02-simulation.md`, istniejące `tests/Sim.Tests/BrakingTests.cs`
  i `tests/Sim.Tests/EnergyAndProfileTests.cs` — żeby nie powtórzyć tego, co już jest.
- **Wyjście:** osobny plik testów własnościowych w `tests/Sim.Tests/`.
- **Weryfikacja:**
  ```bash
  dotnet test tests/Sim.Tests
  ```
  Oczekiwane: zielony zestaw z liczbą testów większą niż dzisiejsze 455.
- **Skończone, gdy:** trzy własności wymienione w wierszu tabeli mają test —
  monotoniczność drogi hamowania po prędkości **i** po masie, zachowanie energii, brak
  ujemnego czasu — a każda ma **wykonaną** kontrolę negatywną z wklejonym wyjściem
  (odwrócenie nierówności w mutancie musi wywrócić dokładnie tę własność, a nie zestaw).
- **Poza zakresem:** żadnej nowej stałej fizycznej ani zmiany w `src/Sim` — test opisuje
  zachowanie, które kod ma dziś; jeżeli własność nie zachodzi, wynikiem jest zgłoszenie,
  nie poprawka modelu przy okazji.
- **Zależy od:** T-310, T-311 (oba zrobione).

##### 6.B1 · `station_layout.py` na pakietach B–F

- **Skąd:** wiersz `| 6.B1 |` pasma B („osie sześciu pakietów są w `data/track/`,
  wysokość peronu `source_backed` z R-007") plus wpis T-211, który ma komplet pól dla
  pakietu A i którego metodę ta pozycja wyłącznie **stosuje do innego wejścia**.
  Wiersz tabeli z 04.09.2026, sześć pól z 05.09.2026.
- **Wejście:** `data/track/L1_B.json`, `L2_E.json`, `L5_C.json`, `L5_D.json`,
  `L6_F.json` (klucz `stations`: 9, 17, 9, 7, 7 — razem **49 peronów**),
  `data/vehicle/m7-spec.json`, `reports/R-007-platform-dimensions.md`,
  `tools/track/station_layout.py` (CLI: `--axis`, `--out`, `--platform-length-m`,
  `--platform-gap-m`, `--footprint-m`, `--ring-step-m`).
- **Wyjście:** raport w `reports/` z układem peronów pięciu pakietów oraz testy
  w `tools/tests/test_station_layout.py` na to, co w tych pakietach jest inne niż w A.
- **Weryfikacja:**
  ```bash
  for AXIS in L1_B L2_E L5_C L5_D L6_F; do
      python3 tools/track/station_layout.py --axis "data/track/$AXIS.json" \
          --out "build/stations/$AXIS.json"
  done
  python3 tools/tests/test_all.py
  ```
  Oczekiwane: pięć plików wyjściowych i zielony zestaw.
- **Skończone, gdy:** wszystkie **49** peronów ma kilometraż, promień lokalny
  i policzoną dolną granicę odsunięcia krawędzi, a raport podaje **najciaśniejszy peron
  każdego pakietu** tak, jak T-211 podaje Gare Centrale dla A (R = 137 m → strzałka
  22,5 cm → krawędź 1,5748 m zamiast 1,35 m). Rozpiętość wewnątrz pakietu podana
  liczbą, bo to ona rozstrzyga, czy peron z prostej wchodzi w kolizję na łuku —
  dla A wyszło 22,4 cm.
- **Poza zakresem:** `--platform-gap-m` **nie dostaje wartości domyślnej**. R-007
  ustalił, że szczeliny peron–pudło nie podaje żadne źródło, więc `edge_offset_m`
  zostaje `None`, nie zero (T-211, „Świadomie nie zrobione"). Bryły w Blenderze są
  etapem 2 T-211, nie tą pozycją.
- **Zależy od:** T-111 (osie B–F, zrobione), T-211 (zrobione), R-007 (zrobione).

##### 6.B2 · Znaczniki kilometrażu i detale na pakietach B–F

- **Skąd:** wiersz `| 6.B2 |` pasma B („to samo narzędzie, inne wejście") plus wpis
  T-011 i `reports/T-011-detail-markers.md`, który podaje wynik dla pakietu A i sam
  nazywa brak wartości domyślnej dla punktów hamowania. Wiersz z 04.09.2026, sześć pól
  z 05.09.2026.
- **Wejście:** te same pięć osi co w 6.B1, `tools/track/detail_layout.py`
  (CLI: `--axis`, `--out`, `--step-m`, `--brake-from-kmh`),
  `tools/blender/detail_markers.py`.
- **Wyjście:** raport z liczbą miejsc na pakiet i testy w `tools/tests/`.
- **Weryfikacja:**
  ```bash
  for AXIS in L1_B L2_E L5_C L5_D L6_F; do
      python3 tools/track/detail_layout.py --axis "data/track/$AXIS.json" \
          --out "build/details/$AXIS.json"
  done
  python3 tools/tests/test_all.py
  ```
  Oczekiwane: pięć plików i zielony zestaw. Bryły znaczników wymagają Blendera
  (`BLENDER_BIN`) i pętli weryfikacji z `CLAUDE.md` §5 — bez niego kończy się
  na kilometrażach.
- **Skończone, gdy:** każdy z pięciu pakietów ma hektometry co 100 m i wszystkie
  stacje ze `stop_id`, a raport podaje rozbicie jak dla A: **89 miejsc na 6686,4 m
  osi = 66 hektometrów + 12 stacji + 11 punktów hamowania**. Suma hektometrów zgadza
  się z `length_m` osi podzieloną przez `--step-m`.
- **Poza zakresem:** punkty hamowania bez jawnego `--brake-from-kmh`. Prędkość
  dopuszczalna na torze **nie ma źródła** (R-006), 72 km/h wolno użyć wyłącznie jako
  zadeklarowanego parametru scenariusza, a bez niego `braking_distance_m` wychodzi
  `None`, nie `0.0` (T-011, „Uwaga").
- **Zależy od:** T-010, T-011 (zrobione), T-111 (zrobione).

##### 6.D2 · Bramka na czas kroku rdzenia

- **Skąd:** wiersz `| 6.D2 |` pasma D („pomiar, nie decyzja") plus
  `reports/linecore-budget.md`, który domknął pozycję 5.7 i zostawił gotowe narzędzie
  pomiarowe. Wiersz z 04.09.2026, sześć pól z 05.09.2026.
- **Wejście:** polecenie `budget` w `src/Sim.Runner` (`Program.cs`, wymaga `--axis`,
  `--signalling`, `--steps`, `--trains`), `tests/Sim.Tests/LineBudgetTests.cs`,
  `reports/linecore-budget.md` §8.4 jako baza progu.
- **Wyjście:** krok bramkowy w `.github/workflows/sim-tests.yml` i próg zapisany
  w repozytorium w jednym miejscu, nie wpisany w YAML z ręki.
- **Weryfikacja:**
  ```bash
  dotnet build src/Sim.Runner -c Release
  dotnet run --project src/Sim.Runner -c Release -- budget \
      --axis data/track/L1_A.json \
      --signalling data/design/signalling/classic-2026.json \
      --limit-kmh 72 --exchange-s 20 --headway-s 120 --steps 1000 \
      --trains 1,2,4,8,32
  dotnet test tests/Sim.Tests
  ```
  **Komenda przepisana 06.09.2026 przy 6.D15, a nie dopisana obok.** Poprzednia
  wersja mowila `--signalling <plan> --steps <N>` i wymieniala trzy opcje z siedmiu,
  ktorych `Budget` wymaga; uruchomiona doslownie konczyla sie kodem 1 na
  `BLAD: line wymaga --limit-kmh`. Powyzsza zostala wykonana i konczy sie kodem 0.
  Polecenie `budget` **juz istnieje** w `Program.cs` — brakuje bramki, nie polecenia.
  Oczekiwane: koszt kroku przy pełnej obsadzie osi poniżej progu, a przy sztucznie
  spowolnionym kroku — bramka czerwona.
- **Skończone, gdy:** bramka wywraca job, gdy koszt `LineCore.Step` przy **9 składach**
  przekroczy próg, a próg wynika ze **zmierzonej powtarzalności**, nie z życzenia:
  §8.4 daje różnicę **2,2 %** (9 składów) i **2,3 %** (12 składów) między `dfbde8f`
  a `6c1048b` przy różnym obciążeniu maszyny, więc próg ciaśniejszy od tego pasma
  świeciłby czerwono od samego sąsiedztwa na runnerze. Punktem odniesienia jest
  4,56 µs na krok = 0,055 % budżetu 1/120 s.
- **Poza zakresem:** próg oparty na ekstrapolacji `N ≈ 330–390`. §7 raportu mówi
  wprost, że to ekstrapolacja **56–65× poza zakres pomiaru** (N ≤ 6,9), więc nie jest
  materiałem na bramkę. Pozycja nie zmienia `FixedStep` ani niczego w `src/Sim`.
- **Zależy od:** 5.7 (zrobione, `reports/linecore-budget.md`). Wykonana przed
  domknięciem T-320 przybija stan przejściowy — to jest zamierzone, bo bramka ma
  pokazać regres, a nie czekać na koniec zadania, którego pilnuje.

##### 6.D1 · Wzorcowy ślad jako bramka CI

- **Skąd:** treść commita **`90a8c31`** („T-320: skład krokowany z zewnątrz, ślad
  identyczny co do bajtu"), i **wyłącznie ona** — liczb 453 107 i 2910 nie ma w żadnym
  pliku `reports/` ani `docs/`. Tamten commit podaje tabelę sześciu osi
  (`L1_A` 89 333, `L1_B` 66 322, `L2_E` 125 833, `L5_C` 68 136, `L5_D` 49 893,
  `L6_F` 53 590 wierszy, razem **453 107**) i kontrolę negatywną metody: „próg hamowania
  przesunięty o 0,1 % daje rozjazd **w wierszu 2910** pliku L1_A". Porównanie zostało
  więc wykonane raz, ręcznie, i od tamtej pory nie chodzi.
- **Wejście:** `src/Sim.Runner/Program.cs` (polecenia `line --trace PLIK.csv` i
  `compare PLIK_A PLIK_B [--tolerance METRY]`, wiersze 51, 55, 85), sześć osi
  `data/track/*.json`, `data/design/signalling/classic-2026.json`,
  `.github/workflows/sim-tests.yml` (wzorzec bramki parytetu: kroki „Reference parity is
  still reproducible from Python" i „Braking reference matches the core byte for byte"),
  `.github/workflows/godot-first-run.yml` (wzorzec pary „bramka + kontrola negatywna"),
  `tools/tests/test_ci_workflows.py`.
- **Wyjście:** krok w `.github/workflows/sim-tests.yml` z kontrolą negatywną obok,
  wzorce śladów tam, gdzie rozstrzygnie pomiar rozmiaru (patrz **Poza zakresem**), oraz
  `reports/golden-trace-gate.md` z liczbą wierszy na oś i czasem przebiegu.
- **Weryfikacja:**
  ```bash
  for AXIS in L1_A L1_B L2_E L5_C L5_D L6_F; do
      dotnet run --project src/Sim.Runner -c Release -- line \
          --axis "data/track/$AXIS.json" --limit-kmh 72 --exchange-s 20 \
          --trace "build/trace/$AXIS.csv"
  done
  wc -l build/trace/*.csv
  ```
  Oczekiwane: sześć plików, razem **453 107 wierszy**, każdy identyczny co do bajtu
  z wzorcem; przebieg całej szóstki mieści się w czasie, który raport podaje liczbą.
- **Skończone, gdy:** bramka chodzi przy każdej zmianie `src/Sim`, a jej kontrola
  negatywna jest **wykonana i wklejona**: próg hamowania przesunięty o 0,1 % zapala ją
  i wskazuje **numer wiersza** rozjazdu, a nie samo „różni się". Bez tej pary bramka
  jest zdaniem o sobie, nie pomiarem.
- **Poza zakresem:** zmiana czegokolwiek w `src/Sim` — bramka ma przybić stan, nie
  poprawić go. **Nierozstrzygnięte i do rozstrzygnięcia pomiarem w tej pozycji:** gdzie
  mieszkają wzorce. 453 107 wierszy CSV to rząd 40–60 MB, a `CLAUDE.md` §4.8 zabrania
  komitować plików > 10 MB; jeśli pomiar to potwierdzi, wzorcem musi być suma SHA-256
  na oś albo artefakt CI, nie plik w repo.
- **Zależy od:** nic. T-320 jest domknięte w części, której ta pozycja dotyczy
  (`90a8c31`, `8f2d118`).

##### 6.D4 · Kontrola spójności liczb między `reports/` a kodem

- **Skąd:** docstring `tools/tests/test_readme_claims.py`: na `e982bc0` README twierdził
  „41 plików" w `src/Sim/` (było 44), „Siedem workflowów" (było 10) i „Godot 4.3 mono"
  w dwóch miejscach. „Żadna bramka tego nie łapała, bo README był jedynym miejscem,
  w którym te liczby stały — a **liczba stojąca w jednym miejscu i nigdzie nie liczona
  rozjeżdża się bezszelestnie**." `reports/` jest dziś dokładnie takim miejscem: 48
  plików, żadnej pętli po liczbach.
- **Wejście:** pięć precedensów, każdy z innej rodziny —
  `tools/tests/test_readme_claims.py` (liczby liczone `os.walk`/`glob`),
  `tools/tests/test_t401_citation.py` (jedna liczba w ośmiu wystąpieniach w pięciu
  plikach), `tools/tests/test_axis_claims.py` (twierdzenia o geometrii wobec
  `data/track/*.json`), `tools/tests/test_dimension_audit.py` (parametr bez wpisu
  w `docs/21-measured-vs-assumed.md`), `tools/tests/test_report_hygiene.py:413`
  (`test_kazda_sciezka_wymieniona_w_raporcie_rozwiazuje_sie_w_drzewie` — ta sama pętla
  po `reports/`, tylko dla ścieżek). Do tego `reports/*.md` w komplecie.
- **Wyjście:** bramka w `tools/tests/test_report_claims.py` i
  `reports/report-claims-audit.md` z listą rozjazdów znalezionych przy pierwszym
  przebiegu.
- **Weryfikacja:**
  ```bash
  python3 tools/tests/test_all.py
  python3 tools/tests/test_report_claims.py
  ```
  Oczekiwane: pętla obejmuje wszystkie **48** raportów, liczba sprawdzanych twierdzeń
  jest podana i większa od zera, a każdy rozjazd nazywa plik, wiersz i obie liczby.
- **Skończone, gdy:** bramka ma **próg na liczbę sprawdzonych twierdzeń** (jak
  `seen >= 500` w bramce ścieżek), bo literówka we wzorcu dałaby inaczej zero trafień
  i zieloną bramkę; lista wyjątków jest **zamknięta zapadką** wzorem
  `MAX_COMMIT_EXCEPTIONS = 2` z 6.D3, gdzie lista otwarta obniżała podłogę 38 → 32;
  a kontrola negatywna jest wykonana i wklejona z nazwą padającego testu.
- **Poza zakresem:** liczby, których nie da się odtworzyć z repozytorium — czasy
  przebiegów, rozmiary plików w `build/`, wyniki pomiarów wykonanych na cudzej maszynie.
  Raport jest **stroną porównywaną, nigdy źródłem**; bramka nie ma prawa nieść ani
  jednej oczekiwanej liczby wpisanej z ręki.
- **Zależy od:** 6.D3 (zrobione, #247) — nagłówek raportu z datą i SHA jest tym, co
  pozwala odróżnić datowany pomiar od zdania o stanie bieżącym.

##### 6.C3 · Odtwarzanie przejazdu z pliku telemetrii

- **Skąd:** `README.md:8` — „linia jest symulacją, kabina jest jednym z jej widoków".
  Dziś `--telemetry` jest wyłącznie **wyjściem**: `src/Game/FirstRun.cs:1717` otwiera
  plik w trybie zapisu. Odtwarzanie istnieje, ale z **zapisu wejść** (`--replay=PLIK`,
  `src/Sim/Train/InputLog.cs`, #239), co jest inną rzeczą — zapis wejść przechodzi przez
  fizykę, telemetria byłaby odtwarzana jako gotowy ruch.
- **Wejście:** `src/Sim/Train/DriveTelemetry.cs` (format przybity trzema stałymi:
  `Header` z dziesięcioma kolumnami, `ColumnCount = 10`, `DefaultSampleEverySteps = 120`),
  `src/Game/RunPlan.cs` (rozpoznawanie trybów i **odmowy łączenia źródeł polecenia**,
  wiersze 335–377), `src/Game/FirstRun.cs`, `src/Sim.Runner/Program.cs` (`compare`),
  `reports/droga-do-grywalnosci.md` §1.3 (tabela pięciu trybów),
  `.github/workflows/godot-first-run.yml`, `tests/Game.Tests/RunPlanTests.cs`.
- **Wyjście:** tryb `--from-telemetry=PLIK` w `src/Game`, testy w
  `tests/Game.Tests/RunPlanTests.cs` i krok w `.github/workflows/godot-first-run.yml`
  z kontrolą negatywną obok.
- **Weryfikacja:**
  ```bash
  "$GODOT_BIN" --headless --path src/Game -- --no-geometry --line --limit-kmh=72 \
      --telemetry=build/ref.csv
  "$GODOT_BIN" --headless --path src/Game -- --no-geometry \
      --from-telemetry=build/ref.csv --telemetry=build/echo.csv
  dotnet run --project src/Sim.Runner -- compare build/ref.csv build/echo.csv --tolerance 0
  ```
  Oczekiwane: `compare` przy tolerancji **0** mówi „identyczne", a kontrola negatywna —
  jeden wiersz zmieniony na czwartym miejscu po przecinku — wskazuje **numer wiersza**
  rozjazdu.
- **Skończone, gdy:** czwarte źródło polecenia wchodzi w ten sam wzorzec odmów co trzy
  istniejące (`RunPlan.cs:339`, `:356`, `:363`) — `--from-telemetry` **nie daje się
  połączyć** z `--line`, `--replay` ani sterowaniem ręcznym, a próba kończy się błędem
  argumentu z nazwą obu trybów, nie cichym wyborem jednego.
- **Poza zakresem:** zmiana formatu `DriveTelemetry` — dziesięć kolumn zostaje, bo
  czyta je dziś bramka CI i `Sim.Runner compare`. Pozycja nie dotyka fizyki: telemetria
  jest odtwarzana jako **ruch zadany**, a nie liczona ponownie.
- **Zależy od:** nic. `--replay` (#239) jest precedensem, nie warunkiem.

##### 6.C4 · Kamera inspekcyjna

- **Skąd:** `src/Game/RunPlan.cs:42` — `KnownViews = { "cab", "chase", "outside" }`.
  Oglądanie geometrii wymaga dziś przejechania do niej: `--shot --at-chainage` robi
  migawkę, ale z kamery jednego z trzech widoków jazdy. Sprawdzanie, czy tunel wygląda
  tak, jak mówi manifest, odbywa się więc renderami z `tools/blender/render_check.py`,
  czyli **poza sceną**.
- **Wejście:** `src/Game/RunPlan.cs` (wiersze 42, 325–332 — nieznany widok jest
  **błędem**, nie cichą kabiną; 457–461 — mapowanie na `ViewKind`),
  `src/Game/FirstRun.cs` (`enum ViewKind` w wierszu 19, wybór kamery w 1165–1177),
  `src/Game/DesignAssumptions.cs` (stałe kamer jako `ViewAssumption`, wiersze 35–50
  i 123–133), `tools/visual/cameras.json` (precedens deklarowania kamery danymi),
  `tools/ci/assert_shot_metadata.py`, `tests/Game.Tests/DesignAssumptionsTests.cs`.
- **Wyjście:** czwarty widok w `KnownViews` i `ViewKind`, jego stałe w
  `DesignAssumptions` jako `ViewAssumption`, testy w `tests/Game.Tests/RunPlanTests.cs`.
- **Weryfikacja:**
  ```bash
  "$GODOT_BIN" --headless --path src/Game -- --shot=build/inspect.png \
      --view=inspect --at-chainage=2521.1
  python3 tools/ci/assert_shot_metadata.py build/inspect.png
  "$GODOT_BIN" --headless --path src/Game -- --view=zmyslony
  ```
  **Warunek wstepny dopisany 06.09.2026 przy 6.D15:** pierwsza komenda wymaga
  wygenerowanych chunkow (`build/t400/chunks/L1_A-chunks.json`), czyli Blendera.
  Bez nich konczy sie kodem 4 i komunikatem `[ASSETS] brak manifestu ...` — zmierzone,
  ze znanym widokiem `--view=cab`, zeby nie mylic tego z brakiem widoku `inspect`.
  Na maszynie bez Blendera ta pozycja nie da sie zweryfikowac i to jest odpowiedz,
  a nie usterka pola.
  Oczekiwane: zrzut z metadanymi opisującymi tę scenę; ostatnie polecenie kończy się
  **błędem argumentu** wymieniającym cztery znane widoki, a nie cichym zejściem do kabiny.
- **Skończone, gdy:** każda nowa stała kamery jest w `DesignAssumptions` jako
  `ViewAssumption` — czyli łapie ją `DesignAssumptionsTests` — a `--view=inspect`
  z `--at-chainage` daje zrzut w zadanym kilometrażu **bez przejeżdżania trasy**,
  co pokazuje pomiar czasu obu wariantów.
- **Poza zakresem:** materiały i światło (`docs/03-legal.md` i T-902 — ocena
  estetyczna), oraz **pasmo 94..106 m kamery goniącej**, które jest osobną decyzją
  właściciela w tabeli niżej. Nowy widok nie ma być obejściem tamtej decyzji.
- **Zależy od:** nic.

##### 6.A6 · Wybieg zamiast trakcji

- **Skąd:** `DriverCommand.Coast` istnieje (`src/Sim/Train/DriverCommand.cs:22`) i jest
  używane jako **stan domyślny** poza fazą ciągu i hamowania (`LineDrive.cs:355`), ale
  nie jako **strategia jazdy**: `src/Sim.Runner/Program.cs` nie ma ani jednego
  przełącznika z „coast", więc nikt nigdy nie zmierzył, ile wybieg kosztuje w czasie
  i ile oszczędza w energii.
- **Wejście:** `src/Sim/Train/DriverCommand.cs`, `src/Sim/Train/LineDrive.cs`,
  `src/Sim/Physics/EnergyAccount.cs`, `src/Sim/Physics/DavisResistance.cs`,
  `src/Sim.Runner/Program.cs` (polecenia `drive` i `line`),
  `reports/T-113-timetable.md` (rezerwa rozkładowa **4,3 s najciaśniej, 45,3 s
  najluźniej**, wiersz 149 — to jest budżet czasu, jaki wybieg ma do wydania),
  `reports/T-401-line-run.md`.
- **Wyjście:** przełącznik wybiegu w `src/Sim.Runner` i `reports/coasting.md` z tabelą
  per odcinek: przyrost czasu, ubytek pracy trakcji, i obie liczby wobec rezerwy z T-113.
- **Weryfikacja:**
  ```bash
  dotnet run --project src/Sim.Runner -c Release -- line --axis data/track/L1_A.json \
      --limit-kmh 72 --exchange-s 20 --trace build/coast-off.csv
  dotnet run --project src/Sim.Runner -c Release -- line --axis data/track/L1_A.json \
      --limit-kmh 72 --exchange-s 20 --coast-from-m 250 --trace build/coast-on.csv
  sha256sum build/coast-off.csv build/coast-on.csv   # sumy MUSZA sie roznic
  dotnet test tests/Sim.Tests
  ```
  **Komenda przepisana 06.09.2026 przy 6.D15, a nie dopisana obok**, i wiersz
  `sha256sum` nie jest ozdoba. Poprzednia wersja mowila `--coast-from-m X`, gdzie `X`
  nie jest wartoscia. Zmierzone: `--coast-from-m` nie wystepuje dzis nigdzie w `src/`,
  a `Sim.Runner` **nieznana opcje przyjmuje w milczeniu** — obie komendy skonczyly sie
  kodem 0 i daly pliki identyczne co do bajtu
  (`11d298315379ba7fbb4673250daeab830d80a3fc084bf4bd731f84a1d811b079` oba).
  Bez porownania sum ta weryfikacja jest spelniona przez NIEZROBIENIE zadania.
  Oczekiwane: przyrost czasu i ubytek pracy trakcji podane **per odcinek**, nie jako
  jedna liczba na całą oś.
- **Skończone, gdy:** dla każdego z jedenastu odcinków pakietu A raport mówi, czy
  przyrost czasu **mieści się w rezerwie rozkładowej z T-113** — a odcinek, który się
  nie mieści, jest nazwany wprost. To jest wynik, nie porażka: rezerwa 4,3 s przy
  najciaśniejszym odcinku jest liczbą zmierzoną i wybieg może się w nią nie zmieścić.
- **Poza zakresem:** dobór strategii wybiegu jako **decyzji projektowej** — pozycja
  mierzy koszt i zysk, nie wybiera profilu jazdy dla gry. Żadnej zmiany w modelu oporów
  ani w krzywej hamowania.
- **Zależy od:** nic. Model energii jest w rdzeniu od T-310.

##### 6.A5 · Bilans energii przejazdu z odzyskiem i bez

- **Skąd:** `src/Sim/Physics/EnergyAccount.cs` i `BrakingEnergyAccount.cs` są w rdzeniu
  od T-310/T-311, ale **żaden przejazd liniowy nie raportuje kilowatogodzin** — w
  `reports/` nie ma ani jednego pliku o energii. Klasy liczą, nikt nie pyta.
- **Wejście:** `src/Sim/Physics/EnergyAccount.cs` (`TractionWorkJ`, `ResidualJ`,
  `RelativeResidual`, `TractionWorkKwh`), `src/Sim/Physics/BrakingEnergyAccount.cs`
  (`BrakeWorkJ`, `ResistanceShorteningM`), `src/Sim/Train/LineRun.cs`,
  `src/Sim.Runner/Program.cs`, `tests/Sim.Tests/EnergyAndProfileTests.cs`,
  `reports/T-310-physics.md`, `reports/T-311-braking.md` §4.1 („Bilans energii — druga
  droga, także na pochyleniu"), `docs/02-simulation.md`,
  `docs/21-measured-vs-assumed.md` §4b.
- **Wyjście:** raport `reports/energy-balance.md` z bilansem na całym przejeździe
  pakietu A i pracą hamulca podaną osobno.
- **Weryfikacja:**
  ```bash
  dotnet run --project src/Sim.Runner -c Release -- line --axis data/track/L1_A.json \
      --limit-kmh 72 --exchange-s 20 --trace build/energy-A.csv
  dotnet test tests/Sim.Tests
  ```
  Oczekiwane: `RelativeResidual` bilansu na całym przejeździe poniżej progu, który
  `reports/T-310-physics.md` już podaje — czyli druga, niezależna droga do tej samej
  liczby.
- **Skończone, gdy:** praca trakcji i praca hamulca są podane w kWh dla **dwóch
  wariantów skrajnych odzysku, 0 % i 100 %**, podawanych wprost jako nastawa przebiegu
  — dokładnie tak, jak T-311 potraktowało udział osi hamowanych: dwa warianty skrajne
  zamiast jednej liczby, której nikt nie opublikował.
- **Poza zakresem:** **wpisanie jakiejkolwiek sprawności odzysku.**
  `BrakingEnergyAccount.cs` mówi wprost: „To jest energia mechaniczna, nie odzysk. Karta
  M7 potwierdza sam fakt hamowania odzyskowego i nic ponadto — nie ma sprawności
  odzysku, nie ma podziału na hamulec elektrodynamiczny i pneumatyczny, nie ma progu
  zanikania ED przy niskiej prędkości." Liczba wpisana z głowy byłaby zmyśloną liczbą
  o taborze (`CLAUDE.md` §1 i §8).
- **Zależy od:** nic. Pozycja dotyka tych samych dwóch typów co 6.A8 (nienazwane przez
  żaden test) — wykonana po 6.A8 dostanie je już opisane, wykonana przed niczego jej
  nie brakuje.

##### 6.A3 · Odtworzenie doby służby z bloków GTFS

- **Skąd:** `reports/T-113-timetable.md` wiersz 41 i 213 — wypis narzędzia:
  „[SŁUŻBY] obiegów pojazdów (block_id): **71**, naraz w służbie **56 o 07:06:44**,
  kursów na obieg 6–35, czas w służbie mediana 13 h 27 min", dzień odniesienia
  **2026-09-02, środa**. Rdzeń tego nie umie: `Sim.Runner line` dodaje **jeden** skład,
  a `budget` dodaje N składów na **równym takcie**, nie z obiegów. Wpis T-320 wypisuje
  to wprost jako część, która „Zostaje".
- **Wejście:** `tools/track/fetch_gtfs.py` (pobiera archiwum i zapisuje manifest
  źródła), `tools/track/timetable.py` (`--gtfs`, `--out`, `--date`, `--axis`),
  `reports/T-113-timetable.md`, `src/Sim/Line/LineCore.cs` (`Add(trainId,
  releaseStep)`, `Step()`, `TurnbackSteps`), `src/Sim/Line/LineRoute.cs`,
  `data/network/sources.json`, `docs/21-measured-vs-assumed.md` §4d i §4f.
- **Wyjście:** polecenie doby służby w `src/Sim.Runner`, testy w
  `tests/Sim.Tests/LineCoreTests.cs` i `reports/service-day.md`.
- **Weryfikacja:**
  ```bash
  python3 tools/track/fetch_gtfs.py --out build/gtfs/stib_gtfs.zip
  python3 tools/track/timetable.py --gtfs build/gtfs/stib_gtfs.zip \
      --out build/timetable.json --date 2026-09-02
  dotnet run --project src/Sim.Runner -c Release -- service-day \
      --timetable build/timetable.json --out build/service-day.csv
  dotnet test tests/Sim.Tests
  ```
  Oczekiwane: liczba obiegów odtworzonych przez rdzeń wynosi **71**, maksimum składów
  jednocześnie w służbie **56** i wypada o **07:06:44**, a żadna para kursów z tym samym
  `block_id` się nie nakłada.
- **Skończone, gdy:** trzy liczby z T-113 (71, 56, 07:06:44) wychodzą z **rdzenia**,
  a nie z narzędzia Pythona, i różnią się od tamtych o zero. Rozjazd choćby o jeden
  obieg jest wynikiem do zapisania, nie do zaokrąglenia — `reports/T-113-timetable.md`
  wiersz 231 mówi, że nakładanie się kursów w jednym `block_id` jest już sprawdzane po
  stronie Pythona, więc obie strony mają czym się różnić.
- **Poza zakresem:** **perturbacje i polityka dyspozytora** — to jest 6.A4, przeniesione
  05.09.2026 do „Czego agent nie ruszy bez decyzji" na mocy sekcji STOP z T-320. Doba
  służby ma być odtworzeniem rozkładu, nie modelem zakłóceń. Poza zakresem także
  zapis czegokolwiek do `data/`: archiwum GTFS i `build/timetable.json` są wytworami
  przebiegu i `CLAUDE.md` §4.8 zabrania ich komitować.
- **Zależy od:** nic w repozytorium, ale **wymaga sieci** przy pierwszym przebiegu —
  archiwum GTFS nie leży w drzewie (`data/gtfs/` i `build/` są w `.gitignore`).
  `fetch_gtfs.py --offline` odmawia pobierania, więc brak sieci jest widoczny od razu,
  a nie w postaci pustego rozkładu.

##### 5.6 · Domknąć „Czego brakuje w tej rozpisce"

- **Skąd:** sekcja `## Czego brakuje w tej rozpisce` w tym pliku otwiera się zdaniem
  „Dopóki go nie mają, **Issues są jedynym źródłem prawdy** o ich zakresie" — a plan
  deklaruje wyżej, że to on jest mapą zależności i zakresów. Rozjazd jest więc zapisany
  wprost i **niezamknięty**: siedem pozycji (T-114, R-002…R-007, T-401, T-901) ma zakres
  poza tym plikiem. Zmierzone 06.09.2026: z tych siedmiu **pięć jest już w `main`**
  (R-003, R-004, R-005, R-006, R-007), T-114 i T-401 sekcja sama nazywa zrobionymi,
  a T-901 jest pozycją właściciela i ma wpis w „Czego agent nie ruszy bez decyzji".
  Do dopisania zostaje więc **R-002**, a resztę sekcji zamyka przeniesienie faktów,
  nie nowa praca.
- **Wejście:** sekcja `## Czego brakuje w tej rozpisce` w `docs/TASKS.md`, wpisy `[x]`
  wyżej w tym pliku (wzorzec formy wpisu zamkniętego), `docs/TASK-TEMPLATE.md`,
  `tools/tests/test_backlog.py` (bramki liczące wpisy i pola),
  `reports/kolejka-audyt-aktualnosci.md` (metoda audytu: fakt kontra zapis).
- **Wyjście:** wpisy z kompletem pól dla pozycji, które ich nie mają, w `docs/TASKS.md`;
  sekcja `## Czego brakuje w tej rozpisce` **usunięta**, bo nie ma już czego wymieniać.
- **Weryfikacja:**
  ```bash
  python3 tools/tests/test_all.py
  grep -n "Czego brakuje w tej rozpisce" docs/TASKS.md
  ```
  Oczekiwane: zestaw zielony, a `grep` **nic nie zwraca** — sekcja zniknęła.
- **Skończone, gdy:** każda z siedmiu pozycji wymienionych dziś w tej sekcji ma w tym
  pliku albo wpis `[x]` z artefaktami, albo wiersz w „Czego agent nie ruszy bez decyzji"
  z powodem — a `grep` na nazwę sekcji nie zwraca nic. Status każdej z siedmiu jest
  **sprawdzony w drzewie**, nie przepisany z sekcji: plik, który sam siebie nazywa mapą,
  nie ma prawa nieść cudzej deklaracji o gotowości.
- **Poza zakresem:** wykonywanie którejkolwiek z siedmiu pozycji. To jest zamknięcie
  rozjazdu w zapisie, nie praca nad zadaniami. Poza zakresem także zmiana zdania o tym,
  że **Issues są źródłem prawdy o statusie** — pozycja usuwa wyjątek, nie regułę.
- **Zależy od:** nic.

##### 6.B5 · Łuk o najmniejszym promieniu na każdej osi

- **Skąd:** `reports/M7-curve-clearance.md` ma metodę zmierzoną i opisaną, ale zastosowaną
  do jednego przypadku. Wiersz `| 6.B5 |` mówi wprost: „metoda zmierzona i opisana,
  zostaje zastosowanie". Sześć osi pakietów A–F leży w `data/track/`, a skrajnia M7
  jest w `data/vehicle/m7-spec.json` — czyli oba wejścia istnieją i pozycja nie dodaje
  ani jednej nowej liczby o sieci.
- **Wejście:** `data/track/L1_A.json`, `L1_B.json`, `L2_E.json`, `L5_C.json`,
  `L5_D.json`, `L6_F.json`, `data/vehicle/m7-spec.json`,
  `reports/M7-curve-clearance.md` (metoda i wzór raportu),
  `tools/track/profile_scan.py` i `tools/blender/placement.py` (`marker_clearances`),
  `docs/24-clearance-profile-decisions.md` — **progi luzu czekają tam na właściciela**
  i pozycja ich nie rozstrzyga.
- **Wyjście:** raport w `reports/` z łukiem o najmniejszym promieniu **na każdej z sześciu
  osi**, z kilometrażem i promieniem w metrach, oraz testy w `tools/tests/` na to,
  co w pakietach B–F jest inne niż w A.
- **Weryfikacja:**
  ```bash
  python3 tools/tests/test_all.py
  ```
  plus wypis narzędzia dla każdej z sześciu osi, wklejony do raportu.
- **Skończone, gdy:** dla każdej z sześciu osi raport podaje **promień najmniejszego
  łuku, jego kilometraż i wynik sprawdzenia skrajni punkt po punkcie** — a oś, na której
  skrajnia nie przechodzi, jest nazwana wprost razem z liczbą, o jaką nie przechodzi.
  To jest wynik, nie porażka.
- **Poza zakresem:** **wybór progu luzu.** `docs/24-clearance-profile-decisions.md` trzyma
  tę decyzję dla właściciela; pozycja podaje zmierzony luz i mówi, przy którym progu
  przechodzi, a przy którym nie — nie wybiera progu. Poza zakresem także jakikolwiek
  zapis do `data/`.
- **Zależy od:** nic. Osie pakietów B–F są w drzewie od #86. **Ta pozycja nie czeka na
  decyzję „co budować zamiast rury"** — czeka na nią 6.B3 (LOD tuneli pakietów C, D, F),
  wiersz obok w tabeli decyzji właściciela. Komentarz w `tools/tests/test_backlog.py`
  przypisywał tę blokadę 6.B5 i jest w tym samym commicie przepisany: promień łuku
  i skrajnia liczą się **z osi**, a nie z tunelu, więc brak tunelu w C, D i F niczego
  tu nie blokuje.

##### 6.B13 · Trzecia runda wyciągania spod `bpy`

- **Skąd:** `reports/bpy-extraction-round-2.md` §3 — ustalenie drugiej rundy (#276) brzmi:
  **granicą do przecięcia jest wiersz, nie funkcja.** Klasyfikacja po funkcjach dała
  w `material_test_scene.py` 0 z 12 kandydatów, po wierszach 8 z 12. `profile_vehicle.py`
  i `tunnel_sweep.py` przeszły pierwszą rundę klasyfikowaną po funkcjach, więc to, co
  w nich zostało nieosiągalne, jest dokładnie tą klasą, którą tamta metoda gubiła.
  Wiersz kolejki podaje 7 i 6 mutacji — liczby z pomiaru przy #276, do potwierdzenia.
- **Wejście:** `tools/blender/profile_vehicle.py`, `tools/blender/tunnel_sweep.py`,
  `reports/bpy-extraction-round-2.md` (metoda i wzór raportu), trzy moduły z #276 —
  `tools/blender/station_sections.py`, `tools/blender/marker_gates.py`,
  `tools/blender/material_specs.py` — jako **wzorzec kształtu**, zwłaszcza re-eksport
  wyciągniętych nazw w module źródłowym, żeby nic wołające stare nazwy nie przestało
  działać; `tools/tests/mutation_sweep.py` jako narzędzie pomiaru osiągalności.
- **Wyjście:** nowe moduły bez `bpy` w `tools/blender/`, re-eksporty w modułach
  źródłowych, testy w `tools/tests/` na każdą wyciągniętą funkcję i raport
  `reports/bpy-extraction-round-3.md` w formie raportu z rundy drugiej.
- **Weryfikacja:**
  ```bash
  python3 tools/tests/test_all.py
  python3 tools/tests/mutation_sweep.py --only tools/blender/profile_vehicle.py --workers 4
  python3 tools/tests/mutation_sweep.py --only tools/blender/tunnel_sweep.py --workers 4
  ```
  Oczekiwane: zestaw zielony, a liczba mutacji **nieosiągalnych** w obu modułach mniejsza
  niż przed ekstrakcją — obie liczby zmierzone tym samym narzędziem.
- **Skończone, gdy:** raport podaje liczbę nieosiągalnych **przed** i **po** dla obu
  modułów, zmierzoną na **tym samym zestawie klas operatorów** i z nazwaniem tego
  zestawu wprost (`operator,prog` i pięć klas dają różne mianowniki i **nie są
  porównywalne**), a każda wyciągnięta funkcja ma co najmniej jeden test bezpośredni.
- **Poza zakresem:** zmiana **zachowania** czegokolwiek — to jest przeniesienie kodu,
  nie jego poprawianie; błąd zobaczony przy okazji jest zgłoszeniem, nie poprawką.
  Poza zakresem także `material_test_scene.py` i moduły z rund pierwszej i drugiej.
- **Zależy od:** #276 (scalone).

##### 6.B14 · Triaż funkcji, które ekstrakcja z #276 uczyniła osiągalnymi

- **Skąd:** wiersz `| 6.B14 |` i `reports/bpy-extraction-round-2.md`. Pozycja 6.B9 (#276)
  wyciągnęła spod `bpy` trzynaście funkcji do trzech modułów i **świadomie nie dopisała
  im testów** — jej celem było uczynić je *mierzalnymi*. Ile z nich przeżyje przegląd,
  mówi dopiero pomiar. Wiersz kolejki mówi o dziewięciu funkcjach bez ani jednego testu
  bezpośredniego; potwierdzenie albo obalenie tej liczby jest pierwszym krokiem pozycji.
- **Wejście:** `tools/blender/station_sections.py`, `tools/blender/marker_gates.py`,
  `tools/blender/material_specs.py`, `reports/bpy-extraction-round-2.md`,
  `tools/tests/mutation_sweep.py`, istniejące moduły w `tools/tests/` (żeby nie dublować
  pokrycia pośredniego), oraz `reports/mutation-triage-sweep.md`
  i `reports/mutation-triage-m7-report.md` jako **wzorzec formy triażu**: werdykt dla
  każdej ocalałej z osobna i osobna kategoria dla mutantów równoważnych.
- **Wyjście:** testy w `tools/tests/` (po jednym nowym pliku na moduł) i raport triażu
  w `reports/`.
- **Weryfikacja:**
  ```bash
  python3 tools/tests/mutation_sweep.py --only tools/blender/station_sections.py --workers 4
  python3 tools/tests/mutation_sweep.py --only tools/blender/marker_gates.py --workers 4
  python3 tools/tests/mutation_sweep.py --only tools/blender/material_specs.py --workers 4
  python3 tools/tests/test_all.py
  ```
  Oczekiwane: liczba zabitych rośnie na każdym z trzech modułów, przy zielonym zestawie.
- **Skończone, gdy:** każda mutacja, która przeżyła przegląd na tych trzech modułach,
  ma w raporcie werdykt — **zabita nowym testem**, **równoważna** (z dowodem, dlaczego
  żadne wejście jej nie odróżni, i z zapisem, czego szukano, żeby to obalić), albo
  **ocalała i dlaczego zostaje** — a raport nazywa wprost zestaw klas operatorów,
  na którym mierzono.
- **Poza zakresem:** zmiana **zachowania** któregokolwiek z trzech modułów; test opisuje
  kod, jaki jest dziś, a błąd ujawniony testem jest zgłoszeniem, nie poprawką przy
  okazji. Poza zakresem także `profile_vehicle.py` i `tunnel_sweep.py` — to jest 6.B13.
- **Zależy od:** #276 (scalone). **Kalibracja wyrocznii jest warunkiem, nie formalnością:**
  przegląd, który zabija wszystko, jest podejrzany, nie znakomity — dokładnie tak kłamało
  to narzędzie przed #268.

##### 6.A9 · Polecenia `Sim.Runner` bez testu

- **Skąd:** `src/Sim.Runner/Program.cs` rozdziela osiem poleceń — `drive`, `replay`,
  `compare`, `axis`, `parity`, `braking`, `line`, `budget`. Zmierzone 06.09.2026 na
  `51d324a`: nazwę polecenia wymienia jakikolwiek plik w `tests/Sim.Tests/` **tylko dla
  `axis`**; pozostałych siedmiu nie wymienia ani jeden. Testy wołają metody rdzenia
  bezpośrednio, więc **rozbiór argumentów i kody wyjścia nie mają pokrycia** — literówka
  w nazwie przełącznika przejdzie zestaw. Pozycja jest bliźniakiem 6.A8 (#279), tylko
  po stronie CLI, nie typów.
- **Wejście:** `src/Sim.Runner/Program.cs`, `tests/Sim.Tests/LineRunTests.cs`,
  `tests/Sim.Tests/LineBudgetTests.cs`, `tests/Sim.Tests/TrackAxisTests.cs`,
  `tests/Sim.Tests/ClassicSignallingScenarioTests.cs` (żeby nie dublować tego, co jest),
  `reports/typy-sim-bez-testu.md` jako wzorzec formy raportu z 6.A8.
- **Wyjście:** testy w nowym pliku w `tests/Sim.Tests/` oraz raport w `reports/`
  z tabelą polecenie → liczba testów przed i po.
- **Weryfikacja:**
  ```bash
  dotnet test tests/Sim.Tests
  ```
  Oczekiwane: zielony zestaw o liczbie testów większej niż dzisiejsze **494**.
- **Skończone, gdy:** każde z ośmiu poleceń ma test na **kod wyjścia** — przy braku
  wymaganego argumentu tam, gdzie polecenie argumenty ma, i przy nazwie polecenia,
  którego nie ma — a każdy test ma **wykonaną** kontrolę negatywną z wklejonym wyjściem.
- **Poza zakresem:** zmiana zachowania `Program.cs`, w tym „poprawienie" kodu wyjścia
  albo komunikatu. Test przybija stan, jaki jest; błąd rozbioru ujawniony testem jest
  zgłoszeniem, nie poprawką przy okazji.
- **Zależy od:** nic. 6.A8 zrobione (#279), ale ta pozycja go nie potrzebuje.

##### 6.B15 · Bramki bez wykonanej kontroli negatywnej

- **Skąd:** `CLAUDE.md` §5 wymienia „skrypt wykonał się bez błędu" i „powinno działać"
  jako **zakazane formy weryfikacji**, a konwencja projektu żąda kontroli negatywnej
  *wykonanej*, nie opisanej. Zmierzone 06.09.2026 na `51d324a`: modułów `test_*.py`
  w `tools/tests/` jest **73**, a wyrażenie „kontrola negatywna" stoi w **33**. Czterdzieści
  modułów nie mówi więc o sobie, czy ktokolwiek sprawdził, że ich bramka **umie
  zaświecić** — a bramka, która nigdy nie zaświeciła, jest zdaniem o sobie, nie pomiarem.
  Dokładnie taka była wyrocznia mutacyjna przed #268: zielona, bo zepsuta.
- **Wejście:** wszystkie moduły `tools/tests/test_*.py`, `CLAUDE.md` §5,
  `reports/wyrocznia-mutacyjna-falszywe-zabicia.md` (przypadek bramki, która nie umiała
  zaświecić), oraz moduły z tych 33 jako **wzorzec zapisu** kontroli — zwłaszcza te,
  które wklejają wyjście, a nie tylko je opisują.
- **Wyjście:** raport w `reports/` z listą modułów bez zapisanej kontroli negatywnej
  i werdyktem dla każdego, oraz **wykonane i zapisane** kontrole dla tych, w których
  da się je wykonać bez Blendera i Godota.
- **Weryfikacja:**
  ```bash
  python3 tools/tests/test_all.py
  grep -rlEi "kontrola negatywna" tools/tests/test_*.py | wc -l
  ls tools/tests/test_*.py | wc -l
  ```
  Oczekiwane: zestaw zielony, a pierwsza liczba większa niż dzisiejsze 33 przy tej
  samej albo większej drugiej.
- **Skończone, gdy:** raport podaje dla **każdego** z 73 modułów jedną z trzech
  odpowiedzi — kontrola **wykonana i zapisana**, kontrola **niewykonalna w tym
  środowisku** (z nazwaniem brakującego narzędzia), albo kontrola **niepotrzebna**
  (z powodem: moduł nie jest bramką) — i żaden nie zostaje bez odpowiedzi.
- **Poza zakresem:** zmiana zachowania jakiejkolwiek bramki, w tym rozluźnienie progu,
  żeby kontrola „ładniej wychodziła". Poza zakresem także pisanie nowych bramek —
  pozycja mierzy i domyka to, co jest.
- **Zależy od:** nic.

##### 6.B16 · Triaż mutacji ocalałych na `tools/track/detail_layout.py`

- **Skąd:** `reports/mutation-drift.md` podaje dla tego modułu **8 ocalałych z 9**
  mutacji — najgorszy stosunek w tabeli, a moduł nie jest byle jaki: wpis T-011 opisuje
  go jako ten liczący kilometraże z **0 założeń**, w odróżnieniu od
  `tools/blender/detail_markers.py`, który ma cztery i każde wypisuje. Moduł bez założeń
  i bez zabijanych mutacji to moduł, o którym nie wiadomo, czy liczy dobrze.
- **Wejście:** `tools/track/detail_layout.py`, `tools/tests/test_detail_layout.py`,
  `reports/mutation-drift.md` (wiersz tego modułu i polecenie przeglądu),
  `reports/T-011-detail-markers.md` i `reports/T-011-details-BF.md` (liczby, które ten
  moduł produkuje — 89 miejsc na osi pakietu A, 457 na sześciu osiach),
  `reports/mutation-triage-sweep.md` jako wzorzec formy triażu.
- **Wyjście:** testy w `tools/tests/test_detail_layout.py` i raport triażu w `reports/`.
- **Weryfikacja:**
  ```bash
  python3 tools/tests/mutation_sweep.py --only tools/track/detail_layout.py --workers 4
  python3 tools/tests/test_all.py
  ```
  Oczekiwane: liczba zabitych większa niż dzisiejsza, przy zielonym zestawie.
- **Skończone, gdy:** każda z ocalałych ma werdykt — **zabita nowym testem**,
  **równoważna** (z dowodem i z zapisem, czego szukano, żeby ten dowód obalić), albo
  **ocalała i dlaczego zostaje** — a raport nazywa wprost zestaw klas operatorów,
  na którym mierzono, bo mianowniki różnych zestawów nie są porównywalne.
- **Poza zakresem:** zmiana wyniku, jaki moduł liczy. Jeżeli test ujawni, że kilometraż
  wychodzi inaczej, niż mówią raporty T-011 — **wynikiem jest zgłoszenie**, nie cicha
  poprawka ani modułu, ani raportu.
- **Zależy od:** nic.

##### 6.D9 · Wzorcem klatki jest suma pikseli, nie suma pliku

- **Skąd:** `tools/visual/capture_blender.py` wpisuje do manifestu `sha256` **całego
  pliku** PNG. Blender stempluje w PNG chunk `tEXt` z kluczami `Date` i `RenderTime`,
  więc suma całego pliku zmienia się przy każdym renderze tej samej sceny — a suma
  samych chunków `IDAT` nie. Narzędzie liczące tę drugą leży w
  `tools/ci/png_pixels_sha256.py` z czterema testami i zmierzone 06.09.2026 na `51d324a`
  **nie jest wołane z żadnego workflowu ani skryptu**: jedyne odwołanie w drzewie
  pochodzi z jego własnego testu. Narzędzie napisane i nieużyte jest tym samym rodzajem
  rzeczy co bramka, która nigdy nie zaświeciła.
- **Wejście:** `tools/ci/png_pixels_sha256.py` (`idat_sha256`),
  `tools/tests/test_png_pixels.py`, `tools/visual/capture_blender.py`,
  `tools/visual/compare.py`, `tools/visual/pngio.py`, `docs/17-visual-regression.md`,
  `.github/workflows/visual-regression.yml`, `tools/tests/test_ci_workflows.py`.
- **Wyjście:** suma `IDAT` w manifeście zrzutów obok sumy pliku (nie zamiast — obie
  liczby mówią co innego i obie są potrzebne), użycie jej w porównaniu, oraz raport
  w `reports/` z pomiarem: dwa rendery tej samej sceny, suma pliku różna, suma `IDAT`
  identyczna.
- **Weryfikacja:**
  ```bash
  "$BLENDER_BIN" --background --python tools/visual/capture_blender.py -- --help
  python3 tools/ci/png_pixels_sha256.py <dwa PNG z dwóch przebiegów tej samej sceny>
  python3 tools/tests/test_all.py
  ```
  Oczekiwane: dwie różne sumy plików i **jedna** suma `IDAT` dla obu klatek.
- **Skończone, gdy:** raport pokazuje **wykonanym pomiarem**, że suma całego pliku
  różni się między dwoma renderami tej samej sceny, a suma `IDAT` nie — i że porównanie
  zrzutów opiera się na tej drugiej. Kontrola negatywna: podmiana jednego piksela
  zmienia sumę `IDAT`, a podmiana wpisu `tEXt` jej nie zmienia; obie **wykonane**.
- **Poza zakresem:** progi tolerancji porównania klatek i cokolwiek z oceny estetycznej
  (`docs/03-legal.md`, T-902). Pozycja zmienia **wyrocznię**, nie kryterium.
- **Zależy od:** **Blendera w wersji z pinu** — kontrola pozytywna wymaga dwóch renderów
  tej samej sceny, więc na maszynie bez Blendera pozycji nie da się domknąć i agent
  ma przerwać, a nie ją obejść (`CLAUDE.md` §2).

##### 6.D10 · Czy commit z nagłówka raportu ma cokolwiek wspólnego z raportem

- **Skąd:** `tools/tests/test_report_hygiene.py` wymaga, żeby raport podawał commit,
  na którym mierzono, i **świadomie nie sprawdza osiągalności tego SHA** — powód stoi
  w docstringu: po scaleniu z rebase albo squashem SHA przebiegu wskazuje na obiekt,
  którego już nie ma. Nie sprawdza natomiast **żadnej** relacji między tym SHA
  a raportem. Zmierzone 06.09.2026 na `51d324a`: raportów z SHA w nagłówku jest **48**,
  a commit podany w nagłówku **nigdy nie dotknął pliku raportu w 25 z nich**; sam
  `51fd842` stoi w siedmiu. Ta liczba nie jest jednak dowodem błędu i to jest sedno
  pozycji: naturalna kolejność pracy to zmierzyć na HEAD, a raport dopisać commitem
  następnym — przy której „SHA dotyka raportu" jest relacją **niewłaściwą**.
- **Wejście:** wszystkie `reports/*.md`, `tools/tests/test_report_hygiene.py`
  (wzorzec nagłówka, lista wyjątków i uzasadnienie, dlaczego osiągalność nie jest
  sprawdzana), `tools/tests/test_report_claims.py`, `git log --follow` jako narzędzie
  pomiaru.
- **Wyjście:** raport w `reports/` z pomiarem dla każdego raportu z SHA w nagłówku,
  oraz — **tylko jeśli pomiar to uzasadni** — bramka w `tools/tests/` na tę relację,
  którą pomiar pokaże jako prawdziwą.
- **Weryfikacja:**
  ```bash
  python3 tools/tests/test_all.py
  ```
  plus wypis pomiaru wklejony do raportu: dla każdego raportu SHA z nagłówka i werdykt.
- **Skończone, gdy:** raport podaje dla każdego z 48 raportów, która z relacji zachodzi
  — **SHA dotyka pliku raportu**, **raport dopisany commitem będącym potomkiem tego SHA**,
  albo **żadna** — i wymienia z nazwy każdy przypadek trzeciej klasy. Bramka powstaje
  **tylko wtedy**, gdy pomiar pokaże relację prawdziwą dla wszystkich poza wymienionymi
  wyjątkami, i ma **wykonaną** kontrolę negatywną. Wynik „żadnej relacji nie wolno
  przybić bramką, bo historia jest przepisywana" jest **poprawnym zakończeniem pozycji**.
- **Poza zakresem:** dopisywanie albo podmienianie SHA w nagłówkach raportów. Pozycja
  mierzy zapis, nie poprawia go; poprawka bez pomiaru zamazałaby dowód.
- **Zależy od:** nic.

##### 6.D11 · Bramka na czas przebiegu `test_all.py`

- **Skąd:** zmierzone 06.09.2026 na `51d324a`: `python3 tools/tests/test_all.py` zbiera
  **1638** testów i chodzi **62,8 s**. Nikt tego nie pilnuje, a zestaw rośnie z każdym
  zadaniem — w tej sesji o kilkadziesiąt testów dziennie. Bramka `tools` chodzi przy
  każdym pull requeście, więc jej czas jest kosztem stałym każdej zmiany. Pozycja jest
  bliźniakiem 6.D2 po stronie Pythona i różni się od niego jednym: rdzeń mierzy
  wydajność **modelu**, ten pomiar mierzy wydajność **własnych bramek**.
- **Wejście:** `tools/tests/test_all.py`, `.github/workflows/python-tests.yml`,
  `tools/tests/test_ci_workflows.py`, `doctor.sh` (wypisuje liczbę testów),
  `reports/` — wzorzec raportu z pomiarem czasu; `tools/tests/mutation_sweep.py`
  jako przykład narzędzia, które **samo** raportuje swój czas.
- **Wyjście:** wypis czasu przebiegu z `test_all.py` (per moduł i razem), krok bramki
  w `.github/workflows/python-tests.yml` z progiem, oraz raport w `reports/`
  z rozkładem czasu po modułach.
- **Weryfikacja:**
  ```bash
  python3 tools/tests/test_all.py
  ```
  Oczekiwane: wypis kończy się czasem przebiegu, a bramka zapala się przy przekroczeniu
  progu — pokazane **wykonaną** kontrolą negatywną, nie opisem.
- **Skończone, gdy:** raport podaje czas **per moduł** dla wszystkich 73 modułów
  i wskazuje trzy najdroższe z liczbami, próg bramki jest **wyliczony z tego pomiaru,
  a nie wpisany z głowy** (i raport mówi, jak go wyliczono), a kontrola negatywna
  — próg obniżony pod zmierzony czas — jest wykonana i wklejona.
- **Poza zakresem:** **przyspieszanie testów.** Pozycja stawia miarę, nie optymalizuje;
  moduł drogi jest wynikiem pomiaru i osobnym zadaniem, nie okazją do przepisania go
  przy okazji. Poza zakresem także kasowanie albo pomijanie testu, żeby zmieścić się
  w progu — `CLAUDE.md` §5 nazywa to wprost zakazaną formą weryfikacji.
- **Zależy od:** nic.

##### 6.B17 · Wspólny dziennik przeglądu mutacyjnego

- **Skąd:** `tools/tests/mutation_sweep.py` wiersz 939 —
  `journal = args.journal or os.path.join(tempfile.gettempdir(), "metro-mutacje.jsonl")`.
  Ścieżka domyślna jest **jedna dla całej maszyny**, a dziennik służy do wznawiania:
  przebieg pomija to, co w nim już jest. Dwa przeglądy na jednej maszynie dopisują
  więc do tego samego pliku, a każdy z nich uzna cudze wpisy za swoje i ich nie
  policzy. Znalezione 06.09.2026 przy pozycji 6.B14, kiedy dwa agenty liczyły
  równolegle; obejściem był własny `--journal`, ale **narzędzie samo tego nie
  sygnalizuje** i nic nie chroni następnego, który o tym nie będzie wiedział.
- **Wejście:** `tools/tests/mutation_sweep.py` (wiersz 939 i miejsce wznawiania),
  `tools/tests/test_mutation_sweep.py`, `reports/mutation-triage-round-2-modules.md`
  (opis przypadku), `reports/wyrocznia-mutacyjna-falszywe-zabicia.md` jako precedens
  usterki w samym narzędziu pomiarowym.
- **Wyjście:** poprawiona ścieżka domyślna (albo odmowa użycia cudzego dziennika)
  w `mutation_sweep.py` plus testy w `tools/tests/test_mutation_sweep.py`.
- **Weryfikacja:**
  ```bash
  python3 tools/tests/test_all.py
  ```
  plus **wykonany** pokaz: dwa przebiegi na tym samym module z domyślnym dziennikiem,
  drugi nie ma prawa uznać wyników pierwszego za swoje ani po cichu ich pominąć.
- **Skończone, gdy:** dwa równoległe przeglądy na jednej maszynie albo **nie dzielą
  dziennika**, albo **odmawiają startu z komunikatem**, a kontrola negatywna jest
  wykonana i wklejona: przebieg wystartowany na cudzym dzienniku zachowuje się
  dokładnie tak, jak mówi poprawka, a nie „jakoś".
- **Poza zakresem:** zmiana formatu dziennika i mechaniki wznawiania — pozycja dotyczy
  **ścieżki**, nie tego, co się w niej zapisuje. Poza zakresem także zmiana klas
  operatorów ani czegokolwiek, co przesuwałoby mianowniki dotychczasowych pomiarów.
- **Zależy od:** nic.

##### 6.B18 · Ile naprawdę trwa przegląd jednego modułu

- **Skąd:** zmierzone 06.09.2026. `tools/visual/compare.py` ma **25** mutacji zestawem
  starym, zestaw testów chodzi **63 s**, robotników było **4** — arytmetyka daje
  rząd siedmiu minut. Przebieg **nie domknął się w dwadzieścia** i został przerwany;
  dziennik nie powstał, więc nie było nawet wyniku częściowego. To samo, w większej
  skali, zatrzymało pomiary w pozycjach 6.B13 i 6.B14, gdzie cztery mutacje
  `scan_gates.py` i jedna `station_sections.py` wyszły jako **nierozstrzygnięte**.
  Po przegonieniu szeregowym `scan_gates.py` dało 5 z 5 zabitych — czyli tamte cztery
  były **artefaktem obciążenia**, a nie własnością kodu.
- **Wejście:** `tools/tests/mutation_sweep.py` (przygotowanie worktree, sonda pokrycia,
  pętla robotników, limit czasu), `tools/tests/test_all.py` (czas zestawu),
  `reports/mutation-drift.md` i `reports/mutation-triage-round-2-modules.md` §5
  (opisy przerwanych przebiegów), pozycja 6.D11 (bramka na czas zestawu — ta sama
  rodzina pomiaru, inny obiekt).
- **Wyjście:** raport w `reports/` z rozbiciem czasu przebiegu na części — utworzenie
  worktree na mutację, sonda pokrycia, sam zestaw — oraz liczbą mutacji na minutę
  przy 1, 2 i 4 robotnikach.
- **Weryfikacja:**
  ```bash
  python3 tools/tests/mutation_sweep.py --only tools/visual/compare.py \
      --operators operator,prog --workers 1 --journal <własny dziennik>
  python3 tools/tests/test_all.py
  ```
  Oczekiwane: przebieg **domyka się** i raport podaje, ile z jego czasu poszło na co.
- **Skończone, gdy:** raport odpowiada liczbą na pytanie „dlaczego 25 mutacji przy
  zestawie 63 s i czterech robotnikach nie mieści się w dwudziestu minutach" —
  a jeśli odpowiedzią jest narzut, którego da się uniknąć, mówi **ile** go jest.
  Wynik „narzutu nie da się uniknąć i oto z czego się składa" jest **poprawnym
  zakończeniem pozycji**.
- **Poza zakresem:** przyspieszanie samego zestawu testów — to jest 6.D11. Poza
  zakresem także zmiana limitu czasu mutacji: limit jest **wyrocznią** dla mutacji
  powodujących pętlę nieskończoną (zmierzone w 6.B14), więc jego podniesienie zmienia
  znaczenie wyniku i wymaga osobnej kontroli negatywnej.
- **Zależy od:** nic, ale **6.B17 jest jego naturalnym sąsiadem**: pomiar czasu na
  maszynie dzielonej z drugim przebiegiem mierzyłby obciążenie, nie narzędzie.

##### 6.D12 · Które narzędzia piszą do `data/`

- **Skąd:** `CLAUDE.md` §4.6 mówi „**`data/` jest tylko do odczytu**, chyba że zadanie
  mówi inaczej wprost". Zmierzone 06.09.2026 przy pozycji 6.A3:
  `tools/track/fetch_gtfs.py` przy każdym pobraniu aktualizuje
  `data/network/gtfs-manifest.json` — pole `retrieved_at`. Robi to **celowo**, jako
  zapis proweniencji z T-114, a reguła nie przewiduje wyjątku. W 6.A3 plik został
  przywrócony, bo pole „Poza zakresem" tamtej pozycji zabraniało zapisu — ale rozjazd
  między narzędziem a regułą został.
- **Wejście:** `CLAUDE.md` §4.6, `tools/data/provenance.py` i wpis T-114,
  `tools/track/fetch_gtfs.py`, pozostałe narzędzia w `tools/` (skan po zapisach),
  `data/network/sources.json`, `docs/09` (proweniencja), `reports/service-day.md` §8.
- **Wyjście:** raport w `reports/` z listą **każdego** miejsca w `tools/`, które pisze
  do `data/`, co dokładnie zapisuje i czy zapis jest deterministyczny (czyli czy
  ponowne pobranie tych samych bajtów zmienia plik).
- **Weryfikacja:**
  ```bash
  python3 tools/tests/test_all.py
  git status --short data/
  ```
  Oczekiwane: raport wymienia wszystkie miejsca, a `git status` po przebiegu narzędzi
  pokazuje **dokładnie to**, co raport zapowiada — ani mniej, ani więcej.
- **Skończone, gdy:** raport podaje dla każdego znalezionego miejsca trzy rzeczy —
  **co pisze**, **czy to zmienia plik przy niezmienionej treści źródła**, i **jaki
  wariant proponuje** — a warianty są wypisane obok siebie z kosztem każdego.
  Zmierzone przy 6.A3: suma treści feedu była identyczna z zapisaną, a plik i tak się
  zmienił; to jest dokładnie ta klasa zapisu, o którą pyta pozycja.
- **Poza zakresem:** **rozstrzygnięcie rozjazdu.** Wybór między zmianą reguły
  a zmianą narzędzia jest decyzją właściciela (`CLAUDE.md` §8) i pozycja go nie
  podejmuje — kończy się na pomiarze i wariantach. Poza zakresem także zmiana
  czegokolwiek w `data/`.
- **Zależy od:** nic.

##### 6.B19 · Wpis dziennika mutacyjnego nie wie, z jakiego drzewa pochodzi

- **Skąd:** znalezione przy pozycji 6.B17 (#289) i tam **świadomie nietknięte**, bo
  pole „Poza zakresem" tamtej pozycji mówiło wprost: dotyczy **ścieżki**, nie tego, co
  się w dzienniku zapisuje. Wpis powstający w `check_one` niesie `id`, `plik`, `wiersz`,
  `rodzaj`, `bylo`, `jest` i wynik — **ale nie commit**. Identyfikatorem mutacji jest
  `plik:wiersz:przesunięcie bajtowe`, więc dwie różne mutacje z dwóch różnych drzew
  mogą mieć **ten sam identyfikator**, jeśli przesunięcie wypadnie tak samo. Docstring
  przy wznawianiu twierdzi, że „zmiana kodu między przebiegami nie przemyci starego
  wyniku pod nową mutację" — i jest to prawdą **tylko wtedy**, gdy zmiana przesunie
  offsety. Poprawka z #289 tego nie dotyka: ona pilnuje, żeby dziennik nie mieszał
  **modułów**, a nie żeby nie mieszał **drzew**.
- **Wejście:** `tools/tests/mutation_sweep.py` (`check_one` — literał wpisu; `Mutation.id`;
  miejsce wznawiania w `main`; `default_journal` z #289),
  `tools/tests/test_mutation_sweep.py`, `reports/dziennik-mutacyjny.md` §5,
  `reports/wyrocznia-mutacyjna-falszywe-zabicia.md` jako precedens usterki w samym
  narzędziu pomiarowym.
- **Wyjście:** commit w każdym wpisie dziennika plus odmowa wznowienia z dziennika
  o innym commicie, oraz testy w `tools/tests/test_mutation_sweep.py`.
- **Weryfikacja:**
  ```bash
  python3 tools/tests/test_all.py
  ```
  plus **wykonany** pokaz: dziennik zapisany na jednym drzewie, wznowienie próbowane
  na drugim — narzędzie ma powiedzieć, że to inne drzewo, a nie policzyć cudzy wynik.
- **Skończone, gdy:** wznowienie z dziennika zapisanego na innym commicie **odmawia
  albo liczy od nowa**, nigdy nie przyjmuje cudzego wyniku po cichu — a kontrola
  negatywna jest wykonana i wklejona **w obie strony**: dziennik z tego samego commita
  ma nadal wznawiać, bo poprawka odmawiająca zawsze przeszłaby połowę tego testu.
- **Poza zakresem:** zmiana samego identyfikatora mutacji na coś innego niż
  przesunięcie bajtowe. To by przeliczyło wszystkie dotychczasowe dzienniki i zerwało
  porównywalność z raportami triażu — a te są datowanymi pomiarami i nie przelicza się
  ich (`reports/mutation-drift.md`). Poza zakresem także domyślna ścieżka dziennika:
  to jest zrobione w #289.
- **Zależy od:** #289 (scalone).

##### 6.B20 · Reszta czasu przeglądu mutacyjnego

- **Skąd:** pozycja 6.B18 (#293) rozłożyła narzut na części i **powiedziała wprost, że
  suma się nie zgadza**: `git worktree add` 0,10 s, kalibracja wyroczni 50,9 s, sonda
  pokrycia ~272 s, dwie mutacje na dwóch robotnikach ~51 s — razem **~6,2 min** wobec
  **obserwowanych ponad 20**. Co najmniej dziesięciu minut nikt nie umie przypisać.
  Tamta pozycja nie zdążyła też domierzyć mutacji na minutę przy 1, 2 i 4 robotnikach,
  czego żądało jej pole „Wyjście".
- **Wejście:** `reports/czas-przegladu-mutacyjnego.md` (rozbicie na części i metoda
  pomiaru), `tools/tests/mutation_sweep.py` (`sweep`, `worker`, `check_one`, sonda
  pokrycia i jej limit czasu), `tools/tests/assertion_gate.py` (instrumentacja AST —
  6.B18 zmierzył, że kosztuje tyle samo w ciepłym i świeżym drzewie), `tools/tests/test_all.py`.
- **Wyjście:** raport w `reports/` domykający rachunek — albo wskazujący liczbą, gdzie
  idzie brakujący czas, albo pokazujący, że obserwacja „ponad 20 minut" była mierzona
  inaczej, niż zakładał rachunek części.
- **Weryfikacja:**
  ```bash
  python3 tools/tests/test_all.py
  ```
  plus wykonany przebieg na module o **dwóch** mutacjach, ze zmierzonym czasem
  całkowitym i czasem każdej części osobno, przy 1, 2 i 4 robotnikach.
- **Skończone, gdy:** suma zmierzonych części **zgadza się z czasem całkowitym** tego
  samego przebiegu, z dokładnością, którą raport podaje liczbą — albo raport nazywa
  konkretną przyczynę, dla której zgodzić się nie może. Tabela mutacji na minutę przy
  1, 2 i 4 robotnikach jest wypełniona.
- **Poza zakresem:** przyspieszanie zestawu testów (6.D11) oraz zmiana limitu czasu
  mutacji — limit jest **wyrocznią** dla mutacji powodujących pętlę nieskończoną
  (zmierzone w 6.B14), więc jego zmiana zmienia znaczenie wyników i wymaga osobnej
  kontroli negatywnej. Poza zakresem także wyłączanie sondy pokrycia: bez niej ocalałe
  trafiają do kupki „niezmierzone", co narzędzie mówi wprost w pomocy.
- **Zależy od:** #293 (scalone).

##### 6.A10 · Dziewiąte polecenie `Sim.Runner`

- **Skąd:** blok 6.A9 wymieniał **osiem** poleceń, bo powstał przed scaleniem #286,
  które dopisało dziewiąte — `service-day`. Agent wykonujący 6.A9 świadomie nie wyszedł
  poza wymienioną ósemkę i **to była właściwa decyzja**, ale luka została: `service-day`
  nie ma testu kodu wyjścia, choć osiem pozostałych ma go od #291.
- **Wejście:** `src/Sim.Runner/Program.cs` (rozdzielacz poleceń, `ServiceDayCommand`,
  `ParseClock`), `tests/Sim.Tests/RunnerCommandTests.cs` (wzorzec z #291 — testy wołają
  wyłącznie `Program.Main`), `src/Sim/Line/ServiceDay.cs`,
  `reports/polecenia-runnera-bez-testu.md`.
- **Wyjście:** testy w `tests/Sim.Tests/RunnerCommandTests.cs` i adnotacja w raporcie
  z #291, że dziewiąte polecenie zostało domknięte.
- **Weryfikacja:**
  ```bash
  dotnet test tests/Sim.Tests
  ```
  Oczekiwane: zielony zestaw o liczbie testów większej niż stan po #291.
- **Skończone, gdy:** `service-day` ma test kodu wyjścia przy braku `--timetable`
  i przy niepoprawnym formacie `--at`, każdy z **wykonaną** kontrolą negatywną, która
  wywraca **tylko** ten test. Raport nazywa też dwa znaleziska z #291, których tamta
  pozycja nie ruszyła: `compare` zwraca 2 tam, gdzie reszta odmów zwraca 1, a `Unknown()`
  i gałąź pustych argumentów dają tę samą stałą **dwiema niezależnymi ścieżkami**.
- **Poza zakresem:** **ujednolicanie kodów wyjścia.** To jest zmiana zachowania
  `Program.cs`, a nie dopisanie testu — i decyzja, czy `compare` ma zwracać 1 czy 2,
  nie należy do pozycji, która ma przybić stan.
- **Zależy od:** #291 i #286 (oba scalone).

##### 6.D13 · Wzorzec SHA łapie to, co SHA nie jest

- **Skąd:** znalezione przy pozycji 6.D10 (#292). Nagłówek jednego raportu cytuje token
  `9e2066aef7ef` — wygląda jak skrócony SHA i łapie go ten sam wzorzec, którego używa
  `tools/tests/test_report_hygiene.py`, ale to **hash builda Blendera 5.2.1**,
  zacytowany w opisie środowiska pomiaru. Docstring tamtej bramki opisuje już jeden
  taki filtr („`1339` z «1339/1339 przeszło» trafi się jako fałszywy SHA") i mówi, że
  `{7,40}` odsiewa go sam — ten przypadek pokazuje, że nie odsiewa wszystkiego.
- **Wejście:** `tools/tests/test_report_hygiene.py` (wzorzec commita i jego docstring),
  `reports/commit-naglowka-a-raport.md` §4 (opis fałszywego trafienia), wszystkie
  `reports/*.md`.
- **Wyjście:** pomiar, ile fałszywych trafień jest we wszystkich raportach, oraz
  zawężenie wzorca albo nazwanie wyjątku — plus testy w `tools/tests/`.
- **Weryfikacja:**
  ```bash
  python3 tools/tests/test_all.py
  ```
  plus wypis wszystkich tokenów łapanych przez wzorzec, z werdyktem dla każdego.
- **Skończone, gdy:** raport podaje **dla każdego** tokenu łapanego przez wzorzec, czy
  jest commitem, czy nie, a bramka albo przestaje łapać te, które nie są, albo ma
  zamkniętą listę wyjątków z powodem przy każdym. Kontrola negatywna **wykonana**:
  zawężony wzorzec nadal łapie prawdziwe SHA, bo wzorzec, który przestał łapać
  wszystko, jest gorszy niż ten, który łapie za dużo.
- **Poza zakresem:** zmiana nagłówków raportów. Wzorzec ma się dopasować do zapisu,
  a nie zapis do wzorca — zwłaszcza że kwestionowany token jest **poprawną i pożyteczną
  informacją** o środowisku pomiaru.
- **Zależy od:** #292 (scalone).

##### 6.B21 · Bramka bloków XML sprawdza tylko drzewo, które JEST czyste

- **Skąd:** znalezione przy pozycji 6.B15 (#296). `tools/tests/test_xml_doc_blocks.py`
  sprawdza dziś prawdziwe `src/`, które jest aktualnie czyste — i przechodzi. Nikt nie
  wstrzykuje tam **sztucznie** zdublowanego bloku `<summary>` ani opisu osieroconego,
  więc bramka **nie ma dowodu, że umie zaświecić**. To jest dokładnie ten stan, przed
  którym ostrzega `CLAUDE.md` §5: zielona bramka bez pokrycia usypia.
- **Wejście:** `tools/tests/test_xml_doc_blocks.py`, `src/Sim/Sim.csproj` (komentarz
  o `GenerateDocumentationFile` i o tym, że CS1591 łapie blok osierocony — to on
  wyłapał trzy z czterech sztuk w #222), `reports/negative-control-audit.md`.
- **Wyjście:** kontrola negatywna w `tools/tests/test_xml_doc_blocks.py`, wykonana
  na wstrzykniętym w pamięci albo w katalogu tymczasowym pliku `.cs`.
- **Weryfikacja:**
  ```bash
  python3 tools/tests/test_all.py
  ```
  plus **wykonana i wklejona** kontrola: plik z dwoma blokami `<summary>` przy jednym
  składniku zapala bramkę, plik czysty jej nie zapala.
- **Skończone, gdy:** bramka ma kontrolę negatywną **wykonaną w obu kierunkach** —
  zdublowany blok zapala, czysty nie zapala — i nie wymaga do tego ani `dotnet`,
  ani żadnego innego narzędzia zewnętrznego, bo zestaw narzędzi chodzi tam, gdzie
  `doctor.sh` przepuszcza ich brak.
- **Poza zakresem:** zmiana czegokolwiek w `src/`. Bramka ma dowieść, że umie
  zaświecić, a nie znaleźć realną usterkę — realnych dziś nie ma i to jest w porządku.
- **Zależy od:** nic.

##### 6.B22 · Treść trzydziestu modułów z frazą niesprawdzona

- **Skąd:** pozycja 6.B15 (#296) policzyła moduły z frazą „kontrola negatywna" i
  **powiedziała wprost**, że sprawdziła treść tylko **ośmiu z trzydziestu ośmiu**.
  Fraza jest przybliżeniem, nie dowodem: moduł może kontrolę **nazwać i jej nie
  wykonać**, dokładnie tak samo, jak może ją wykonać i nie nazwać (czterdzieści takich
  6.B15 znalazło czytaniem treści). Pozycja domyka drugą połowę tego pomiaru.
- **Wejście:** `reports/negative-control-audit.md` (lista modułów i kryterium),
  trzydzieści modułów `tools/tests/test_*.py` z frazą, których treści tamta pozycja
  nie przejrzała, `CLAUDE.md` §5.
- **Wyjście:** **nowy** raport `reports/negative-control-audit-tresc.md` z werdyktem
  dla każdego z brakujących modułów oraz — tam, gdzie fraza okaże się pusta —
  **wykonana** kontrola.

  **Dlaczego nowy plik, a nie dopisek do audytu z 6.B15.** Pierwsza wersja tego pola
  nazywała istniejący raport i **położyła `main` na czerwono**: scalenie #299 (ten blok)
  i #296 (tamten raport) były osobno zielone, a razem zapaliły
  `test_a_documented_item_whose_reports_all_exist_says_so_in_its_row` — bo pozycja
  udokumentowana, której całe „Wyjście" już leży w `reports/`, wygląda dla bramki na
  zrobioną. Docstring tej bramki przewidział dokładnie ten przypadek („pozycja, której
  raport **rozszerza** plik już istniejący") i podał to lekarstwo: pole ma nazwać nowy
  plik albo sekcję. Tu jest zastosowane.
- **Weryfikacja:**
  ```bash
  python3 tools/tests/test_all.py
  ```
  plus tabela: moduł → czy fraza ma za sobą wykonaną kontrolę → czym to sprawdzono.
- **Skończone, gdy:** wszystkie trzydzieści osiem modułów z frazą ma werdykt oparty
  na **treści**, a nie na obecności frazy, a każdy przypadek „fraza bez kontroli" ma
  albo dopisaną kontrolę, albo nazwany powód, dla której jej nie ma.
- **Poza zakresem:** zmiana zachowania jakiejkolwiek bramki i pisanie nowych bramek —
  ta pozycja domyka pomiar, nie rozszerza zakresu.
- **Zależy od:** #296 (scalone).

##### 6.C5 · Nagłówek raportu o drodze do grywalności liczy tryby ręcznie

- **Skąd:** znalezione przy pozycji 6.C3 (#297). Nagłówek §1.3
  `reports/droga-do-grywalnosci.md` mówi „Cztery tryby" nad tabelą, która miała pięć
  wierszy, a po dopisaniu `--from-telemetry` ma **sześć**. 6.C3 dopisał obok zdanie,
  ale liczby nie ruszył — i słusznie, bo nie była wynikiem jego pomiaru. To ta sama
  rodzina usterki, którą opisuje bramka z #273: **liczba stojąca w jednym miejscu
  i nigdzie nie liczona rozjeżdża się bezszelestnie**.
- **Wejście:** `reports/droga-do-grywalnosci.md` §1.3, `src/Game/RunPlan.cs`
  (`KnownViews` i rozpoznawanie trybów — źródło prawdy o ich liczbie),
  `tools/tests/test_report_claims.py` i `tools/tests/test_readme_claims.py` jako
  precedensy liczenia liczby z kodu, a nie z pamięci autora.
- **Wyjście:** poprawiony nagłówek **albo** zdjęta z niego liczba, plus bramka
  w `tools/tests/`, jeżeli pomiar pokaże, że da się ją policzyć z kodu.
- **Weryfikacja:**
  ```bash
  python3 tools/tests/test_all.py
  ```
  plus wypis: ile trybów widzi kod, ile mówi nagłówek, ile ma tabela.
- **Skończone, gdy:** trzy liczby — z kodu, z nagłówka i z tabeli — są **zgodne albo
  nagłówek przestaje którąkolwiek podawać**, a decyzja między tymi dwoma wariantami
  jest w raporcie uzasadniona pomiarem. Precedens jest: `CLAUDE.md` §2 zdjął liczbę
  testów narzędzi, bo zaszywanie jej generowało rozjazd przy każdym nowym module.
- **Poza zakresem:** dopisywanie nowych trybów jazdy i zmiana `RunPlan.cs`.
- **Zależy od:** #297 (scalone).

##### 6.D15 · Ile komend z pól „Weryfikacja" da się w ogóle uruchomić

- **Skąd:** znalezione przy pozycji 6.C3 (#297). Komenda z pola „Weryfikacja" bloku
  6.C3 jest **niewykonalna** — `--no-geometry --line --telemetry=…` odrzuca istniejąca
  odmowa łączenia źródeł, kod wyjścia 9. Agent musiał zbudować własną drogę pomiaru
  i to zrobił, ale pole obiecywało coś, czego nie da się wpisać do terminala.
  Pole „Weryfikacja" jest w tym projekcie **obietnicą, której nikt nie sprawdza**,
  a bloków z sześcioma polami jest dziś kilkadziesiąt.
- **Wejście:** wszystkie bloki `##### <numer> ·` w `docs/TASKS.md` (pole „Weryfikacja"),
  `tools/tests/test_backlog.py` (parser pól — `missing_fields` sprawdza, czy pole ma
  treść, ale nie czy ta treść działa), `docs/TASK-TEMPLATE.md`.
- **Wyjście:** raport w `reports/` z werdyktem dla każdej komendy — **uruchamialna**,
  **wymaga narzędzia, którego tu nie ma**, albo **niewykonalna z powodu w kodzie** —
  oraz poprawione pola tam, gdzie komenda jest po prostu błędna.
- **Weryfikacja:**
  ```bash
  python3 tools/tests/test_all.py
  ```
  plus wypis: ile komend zebrano, ile uruchomiono, ile odmówiło i dlaczego.
- **Skończone, gdy:** raport podaje liczbę komend w trzech kategoriach i wymienia
  z nazwy **każdą niewykonalną**, a pola „Weryfikacja" bloków niezrobionych pozycji są
  poprawione tam, gdzie komenda kłamie. Poprawka bloku pozycji **ZROBIONEJ** jest poza
  zakresem: to zapis historyczny, a nie instrukcja do wykonania.
- **Poza zakresem:** wykonywanie komend, które wymagają sieci albo trwają dłużej niż
  kilka minut — wystarczy rozstrzygnąć, że **dają się** uruchomić. Poza zakresem także
  zmiana kodu, żeby komenda z bloku zaczęła działać: to blok ma opisywać kod, nie odwrotnie.
- **Zależy od:** nic.

##### 6.D16 · Zdanie o proweniencji, które dla dwóch miejsc jest nieprawdą

- **Skąd:** znalezione przy pozycji 6.D12 (#295). `docs/09-data-provenance.md` twierdzi,
  że `retrieved_at` „nie może zmieniać byte-deterministycznego canonical outputu".
  Zmierzone: `build_alignment.py` i `normalize_stops.py` **osadzają to pole wprost
  w plikach, które są commitowane** — więc dla tych dwóch miejsc zdanie jest dziś
  nieprawdziwe.
- **Wejście:** `docs/09-data-provenance.md`, `reports/zapisy-do-data.md` §8 (pomiar),
  `tools/track/build_alignment.py`, `tools/track/normalize_stops.py`,
  `tools/data/provenance.py`, wpis T-114.
- **Wyjście:** zdanie **przepisane, a nie dopisane obok**, plus — jeżeli pomiar to
  uzasadni — bramka w `tools/tests/` na to, żeby nie wróciło.
- **Weryfikacja:**
  ```bash
  python3 tools/tests/test_all.py
  ```
  plus wypis pokazujący, gdzie `retrieved_at` trafia do pliku commitowanego.
- **Skończone, gdy:** dokument mówi o tych dwóch miejscach prawdę, a różnica między
  „manifest proweniencji" a „plik wynikowy" jest w nim nazwana — bo to ona rozstrzyga,
  kiedy zdanie zachodzi, a kiedy nie.
- **Poza zakresem:** **rozstrzygnięcie, czy to narzędzia mają przestać osadzać
  `retrieved_at`, czy reguła ma dopuścić wyjątek.** To jest ta sama decyzja
  właściciela, której nie podjęła 6.D12, i ta pozycja też jej nie podejmuje —
  poprawia wyłącznie zdanie, które opisuje stan.
- **Zależy od:** #295 (scalone).

##### 6.D17 · Godot wymaga `DOTNET_ROOT`, a dokument o tym nie mówi

- **Skąd:** znalezione przy pozycji 6.C3 (#297), na własnej skórze. Bez `DOTNET_ROOT`
  Godot pada z `Failed to load hostfxr` i sygnałem 11, a przy brakującym assembly
  **wisi bez ani jednego wiersza na stdout** do wypalenia limitu czasu — czyli objaw
  nie wskazuje przyczyny. `docs/23-environment.md` mówi, skąd wziąć Godota, ale nie
  mówi, co ustawić, żeby wystartował.
- **Wejście:** `docs/23-environment.md`, `.github/workflows/godot-first-run.yml`
  (jak zmienne są ustawiane w CI — tam działa, więc różnica jest w opisie, nie w CI),
  `doctor.sh` (sonda Godota), `src/Game/`.
- **Wyjście:** uzupełniony `docs/23-environment.md` oraz — jeżeli sonda `doctor.sh`
  tego nie łapie — jej poprawka, żeby brak `DOTNET_ROOT` był widoczny **przed**
  pierwszym zawieszonym przebiegiem.
- **Weryfikacja:**
  ```bash
  bash doctor.sh
  python3 tools/tests/test_all.py
  ```
  plus **wykonana** kontrola: uruchomienie Godota bez `DOTNET_ROOT` i z nim, z wklejonym
  wyjściem obu przebiegów.
- **Skończone, gdy:** dokument podaje komplet zmiennych potrzebnych do uruchomienia
  Godota, a `doctor.sh` zgłasza ich brak **komunikatem nazywającym przyczynę**, nie
  ciszą do limitu czasu. Kontrola negatywna wykonana w obie strony.
- **Poza zakresem:** zmiana czegokolwiek w `.github/workflows/` — w CI to działa,
  więc różnica jest w dokumencie i w sondzie, nie w workflow.
- **Zależy od:** #297 (scalone).

**Aktualizacja tej listy jest częścią pracy, nie dodatkiem do niej.** Pozycja zrobiona
znika stąd i pojawia się jako wpis z sześcioma polami wyżej w tym pliku.

##### 6.D14 · Czy `--offline` naprawdę nie dotyka sieci

- **Skąd:** zmierzone 06.09.2026 przy 6.D12 (`reports/zapisy-do-data.md` §4.1/§4.2):
  gałąź `--offline` w `tools/track/fetch_gtfs.py` i `tools/track/fetch_stib_shapes.py`
  czyta plik już leżący na dysku i woła `P.utc_now_iso()` zamiast `P.fetch_url()` — to
  jest dziś ustalone **czytaniem kodu**, nie testem, który udowadnia brak żądania
  sieciowego wprost. `tools/tests/test_fetchers.py` sprawdza inne zachowanie obu
  narzędzi, ale żaden test nie podmienia funkcji pobierającej na coś, co by się
  wywróciło, gdyby `--offline` jednak spróbowało wyjść w sieć.
- **Wejście:** `tools/track/fetch_gtfs.py`, `tools/track/fetch_stib_shapes.py`,
  `tools/data/provenance.py` (`fetch_url`), `tools/tests/test_fetchers.py`.
- **Wyjście:** po jednym nowym teście na narzędzie w `tools/tests/test_fetchers.py`,
  każdy podmieniający `provenance.fetch_url` (albo `urllib.request.urlopen`) na
  funkcję rzucającą wyjątkiem, uruchamiający `main(["--offline", ...])` na pliku
  przygotowanym w katalogu tymczasowym i sprawdzający, że proces kończy się kodem 0.
- **Weryfikacja:**
  ```bash
  python3 tools/tests/test_all.py
  ```
  Oczekiwane: oba nowe testy przechodzą, a kontrola negatywna — to samo wywołanie
  bez flagi `--offline`, więc podmieniona funkcja faktycznie zostaje wywołana —
  wywraca dokładnie te dwa testy i tylko je.
- **Skończone, gdy:** oba testy są zielone, kontrola negatywna wykonana i wklejona,
  a treść testu nazywa wprost, którą funkcję podmieniono i jakim wyjątkiem.
- **Poza zakresem:** samo pytanie 6.D12 — czy manifest proweniencji ma się zmieniać
  przy niezmienionej treści źródła. Ta pozycja dowodzi wyłącznie, że `--offline` nie
  sięga do sieci; nie zajmuje się plikiem, który mimo to zapisuje.
- **Zależy od:** nic.

##### 6.A11 · Nieznana opcja `Sim.Runner` przyjmowana w milczeniu

- **Skąd:** zmierzone 06.09.2026 przy 6.D15 (#301). Komenda z pola „Weryfikacja"
  pozycji 6.A6 wola `line ... --coast-from-m X`. Opcji `--coast-from-m` nie ma dzis
  nigdzie w `src/`, `X` nie jest liczba — a proces konczy sie **kodem 0** i wypisuje
  normalny przebieg. Dwie komendy tego pola daly pliki identyczne co do bajtu
  (`11d298315379ba7fbb4673250daeab830d80a3fc084bf4bd731f84a1d811b079` oba). Jest to
  wyrocznia zepsuta w strone „wszystko w porzadku": literowka w nazwie opcji nie
  odroznia sie od opcji dzialajacej.
- **Wejście:** `src/Sim.Runner/Program.cs` (`Option`, `RequiredNumber`,
  `OptionalNumber`, rozdzielacz polecen), `tests/Sim.Tests/RunnerCommandTests.cs`
  (wzorzec z #291 i #302 — testy wolaja wylacznie `Program.Main`),
  `src/Game/RunPlan.cs` (`KnownArguments` — strona Godota **juz** odmawia nieznanemu
  argumentowi i to jest precedens, z ktorego bierze sie ksztalt odmowy).
- **Wyjście:** odmowa przy nieznanej opcji w `Sim.Runner`, z komunikatem wymieniajacym
  opcje znane danemu poleceniu, plus testy kodu wyjscia dla co najmniej dwoch polecen.
- **Weryfikacja:**
  ```bash
  dotnet build src/Sim.Runner -c Release
  dotnet run --project src/Sim.Runner -c Release -- line --axis data/track/L1_A.json \
      --limit-kmh 72 --exchange-s 20 --zmyslona-opcja 7 --trace build/x.csv
  dotnet test tests/Sim.Tests
  ```
  Oczekiwane: druga komenda konczy sie **odmowa** nazywajaca nieznana opcje, a nie
  kodem 0; zestaw rdzenia zielony o liczbie testow wiekszej niz przed zmiana.
- **Skończone, gdy:** nieznana opcja konczy sie odmowa w kazdym z dziewieciu polecen,
  a kontrola negatywna WYKONANA pokazuje, ze zdjecie odmowy wywraca dokladnie nowe
  testy. Komunikat wymienia opcje znane **temu** poleceniu, nie wszystkim.
- **Poza zakresem:** **wybor kodu wyjscia dla tej odmowy, jesli mialby byc nowy.**
  Pozycja uzywa stalej, ktora `Program.cs` juz ma dla odmow argumentowych; wprowadzenie
  kolejnej wartosci jest decyzja z tej samej rodziny, ktora 6.A10 zostawila wlascicielowi
  (`compare` zwraca 2 tam, gdzie reszta zwraca 1).
- **Zależy od:** #302 (scalone albo w locie — wzorzec testu kodu wyjscia).

##### 6.A12 · `--trains 32` melduje `N_max=1`

- **Skąd:** zmierzone 06.09.2026 przy 6.D15 (#301) przy okazji naprawiania komendy
  z bloku 6.D2. Wykonane wyjscie:
  `[BUDZET] 32;1;1.00;0.00;132528;...` i podsumowanie „najwieksze zmierzone N=32
  zajmuje 0.09% budzetu kroku **przy 1 skladach faktycznie na planie**". Kolumna
  `N_zgl` mowi wiec, ile skladow **zglooszono**, a nie ile ich bieglo — i zdanie
  podsumowania samo to przyznaje, tyle ze na koncu wiersza.
- **Wejście:** `src/Sim.Runner/Program.cs` (`Budget`, `ParseTrainCounts`),
  `src/Sim/Line/` (wpuszczanie skladu na plan, odstep `--headway-s`),
  `data/design/signalling/classic-2026.json`.
- **Wyjście:** raport w `reports/` mowiacy, **dlaczego** przy `--trains 32` na planie
  stoi jeden sklad (odstep? dlugosc osi? nawrot?), oraz — jesli pomiar pokaze, ze da
  sie obciazyc plan naprawde — komenda, ktora to robi, wpisana do bloku 6.D2.
- **Weryfikacja:**
  ```bash
  dotnet build src/Sim.Runner -c Release
  dotnet run --project src/Sim.Runner -c Release -- budget \
      --axis data/track/L1_A.json \
      --signalling data/design/signalling/classic-2026.json \
      --limit-kmh 72 --exchange-s 20 --headway-s 120 --steps 1000 --trains 1,2,4,8,32
  ```
  plus ten sam przebieg z odstepem, przy ktorym `N_max` przestaje byc rowne 1.
- **Skończone, gdy:** raport podaje liczbe skladow, ktore **faktycznie** biegly, dla
  co najmniej dwoch roznych wartosci `--headway-s`, i nazywa mechanizm, ktory ogranicza
  ta liczbe. Jesli mechanizmem jest blad, pozycja go **nazywa**, a nie poprawia.
- **Poza zakresem:** bramka na czas kroku — to jest 6.D2, i to ona ma stanac **na tej
  liczbie**. Poza zakresem takze zmiana modelu wpuszczania skladow.
- **Zależy od:** nic. Blokuje 6.D2.

##### 6.B23 · Licznik modulow bez testu liczy pliki generowane

- **Skąd:** zmierzone 06.09.2026 przy 6.D15 (#301). Wiersz powloki z bloku 6.A8 —
  jedyne miejsce, gdzie ten licznik dzis zyje — wypisuje na drzewie po `dotnet build`
  cztery wiersze `BRAK TESTU`, wszystkie dla plikow **generowanych**:
  `src/Sim/obj/{Debug,Release}/net10.0/Sim.AssemblyInfo.cs` i
  `.NETCoreApp,Version=v10.0.AssemblyAttributes.cs`. Blok 6.A8 obiecywal „po zadaniu
  ma wypisac zero wierszy"; obietnica jest dzis nie do spelnienia na drzewie, ktore
  ktokolwiek zbudowal.
- **Wejście:** blok `##### 6.A8` w `docs/TASKS.md` (zapis historyczny, **nietykany**),
  `src/Sim/`, `tests/Sim.Tests/`, `tools/tests/test_xml_doc_blocks.py` jako precedens
  bramki chodzacej po `src/` bez `dotnet`, `.gitignore`.
- **Wyjście:** bramka w `tools/tests/`, ktora liczy skladniki `src/Sim` bez testu,
  pomijajac `obj/` i `bin/`, z lista wyjatkow, jesli pomiar pokaze, ze jakis skladnik
  testu miec nie moze.
- **Weryfikacja:**
  ```bash
  python3 tools/tests/test_all.py
  ```
  plus wypis: ile plikow `.cs` widzi bramka przed pominieciem `obj/` i `bin/`, ile po,
  i ile z nich nie ma testu.
- **Skończone, gdy:** bramka jest zielona na czystym drzewie **i na drzewie po
  `dotnet build`** — oba przebiegi wykonane i wklejone — a kontrola negatywna
  (skladnik dopisany do `src/Sim` bez testu) ja zapala.
- **Poza zakresem:** dopisywanie brakujacych testow do `src/Sim`. Ta pozycja stawia
  licznik, ktory nie klamie; co pokaze, jest praca na osobna pozycje.
- **Zależy od:** nic.

##### 6.D18 · `--only` dopasowuje podciag, nie nazwe pliku

- **Skąd:** zmierzone 06.09.2026 przy 6.D15 (#301). `--only sweep.py` zwraca mutacje
  z **dwoch** modulow: `tools/blender/sweep.py` (117) i `tools/blender/tunnel_sweep.py`
  (68). Bloki 6.B6, 6.B7, 6.B8 i 6.D5 wolaja `--only` basename'em, wiec kazdy raport
  z tych przebiegow mowi o innym zbiorze plikow, niz nazywa jego komenda.
- **Wejście:** `tools/tests/mutation_sweep.py` (dopasowanie `--only`),
  `tools/tests/test_mutation_sweep.py`, bloki 6.B6/6.B7/6.B8/6.D5 w `docs/TASKS.md`
  (tylko do odczytu — zapis historyczny), `reports/mutation-sweep.md`.
- **Wyjście:** rozstrzygniecie, ktore z dwoch znaczen `--only` jest zamierzone,
  wpisane do docstringa narzedzia, plus test na to znaczenie. Jesli zamierzone jest
  dopasowanie po nazwie pliku — poprawka dopasowania; jesli po podciagu — komunikat
  wypisujacy, ILE modulow zostalo zlapanych, zanim przeglad ruszy.
- **Weryfikacja:**
  ```bash
  python3 tools/tests/mutation_sweep.py --only sweep.py --list
  python3 tools/tests/test_all.py
  ```
  Oczekiwane: pierwsza komenda mowi wprost, ile modulow objela.
- **Skończone, gdy:** wywolanie `--only` basename'em, ktory pasuje do wiecej niz
  jednego pliku, **nazywa te pliki** albo odmawia, a kontrola negatywna WYKONANA
  pokazuje, ze poprzednie zachowanie wywraca nowy test.
- **Poza zakresem:** przeliczanie raportow z przegladow, ktore uzyly starego `--only`.
  To sa datowane pomiary i ich sie nie przelicza; wolno je co najwyzej **oznaczyc**.
- **Zależy od:** nic.

##### 6.D19 · Modul, ktory sie nie importuje, jest niewidzialny dla grepa

- **Skąd:** zmierzone 06.09.2026 przy 6.D15 (#301) na wlasnym module z bledem skladni.
  `test_all.py` wypisuje wtedy `SyntaxError` i konczy sie **kodem 1** — to dziala. Ale
  nie produkuje ani jednego wiersza `FAIL`, ani wiersza `N/M przeszlo`. Sesja, ktora
  sprawdza zielonosc przez `grep -cE '^\s*FAIL'`, dostaje **zero** i widzi zielono.
  Ta sesja tak wlasnie robila.
- **Wejście:** `tools/tests/test_all.py` (zbieranie i importowanie modulow),
  `tools/tests/assertion_gate.py`, `.github/workflows/python-tests.yml` (czy krok CI
  patrzy na kod wyjscia, czy na tresc wyjscia), `CLAUDE.md` §5,
  `tools/tests/mutation_sweep.py` (czyta z tego procesu linie `N/M przeszlo`
  **i** kod wyjscia — patrz 6.D11).
- **Wyjście:** wiersz, ktory `test_all.py` wypisuje przy nieudanym imporcie i ktory
  wyglada jak porazka takze dla czytajacego grepem, plus test na to zachowanie.
- **Weryfikacja:**
  ```bash
  python3 tools/tests/test_all.py
  ```
  plus **wykonana** kontrola: modul z bledem skladni wrzucony do `tools/tests/`
  w katalogu tymczasowym, z wklejonym wyjsciem i kodem wyjscia przed i po zmianie.
- **Skończone, gdy:** nieudany import produkuje wiersz dajacy sie zlapac tym samym
  wzorcem co porazka testu, kod wyjscia nadal wynosi 1, a `mutation_sweep.py` nadal
  czyta z tego procesu to, czego potrzebuje — sprawdzone uruchomieniem, nie czytaniem.
- **Poza zakresem:** zmiana tego, jak `test_all.py` liczy testy, i zmiana kroku CI.
  Kod wyjscia juz jest poprawny; brakuje **widocznosci**, nie wyroczni.
- **Zależy od:** nic.

##### 6.D20 · Komunikat odmowy nazywa niewlasciwe polecenie

- **Skąd:** zmierzone 06.09.2026 przy 6.D15 (#301). `budget` bez `--limit-kmh` konczy
  sie komunikatem `BLAD: line wymaga --limit-kmh`. Pomocnik `RequiredNumber` ma nazwe
  polecenia zaszyta na sztywno, wiec kieruje czytajacego do polecenia, ktorego nie
  uruchamial. Osiem pozostalych polecen dzieli ten sam pomocnik.
- **Wejście:** `src/Sim.Runner/Program.cs` (`RequiredNumber`, `OptionalNumber`,
  wszystkie miejsca wolania), `tests/Sim.Tests/RunnerCommandTests.cs`.
- **Wyjście:** komunikat nazywajacy polecenie, ktore faktycznie wolano, plus test
  kodu wyjscia **i tresci komunikatu** dla co najmniej dwoch roznych polecen.
- **Weryfikacja:**
  ```bash
  dotnet test tests/Sim.Tests
  ```
  plus wykonane: `budget` bez `--limit-kmh` i `line` bez `--limit-kmh`, z wklejonymi
  komunikatami obu.
- **Skończone, gdy:** oba komunikaty nazywaja swoje polecenie, a kontrola negatywna
  WYKONANA (przywrocona zaszyta nazwa) wywraca dokladnie nowe testy.
- **Poza zakresem:** zmiana kodow wyjscia i ujednolicanie ich — ta sama granica,
  ktora postawila 6.A10.
- **Zależy od:** nic.

##### 6.A13 · Plan, ktorego rdzen nie umie wczytac, wywraca proces sygnalem

- **Skąd:** zmierzone 06.09.2026 przy 6.A12 (`reports/obsada-planu.md` §5). Proba
  uzycia `data/design/signalling/cbtc-test-2026.json` jako planu dla polecenia
  `budget` konczy sie kodem **134** i stosem wywolan z
  `SignallingPlan.FromJson … JsonElement.GetProperty`. Powod jest prosty i nie jest
  bledem danych: ten plik opisuje **obszar i tryb** (`area_id`, `mode`, `status`),
  a nie plan blokow — brakuje mu `blocks` i `plan_id`. Bledem jest reakcja:
  `KeyNotFoundException` nie stoi na liscie wyjatkow lapanych przez wspolny handler
  w `Program.Main` (`IOException`, `ArgumentException`, `FormatException`,
  `InvalidOperationException`), wiec zamiast odmowy z komunikatem leci stos.
- **Wejście:** `src/Sim/Signalling/SignallingPlan.cs` (`FromJson`),
  `src/Sim.Runner/Program.cs` (handler wyjatkow w `Main`),
  `data/design/signalling/cbtc-test-2026.json`, `data/design/signalling/classic-2026.json`
  (plik, ktory sie wczytuje — roznica miedzy nimi jest tu cala trescia),
  `tests/Sim.Tests/RunnerCommandTests.cs` (wzorzec testu kodu wyjscia z #291 i #302).
- **Wyjście:** odmowa nazywajaca brakujace pole i plik, kod wyjscia z rodziny odmow
  argumentowych, plus test kodu wyjscia na pliku, ktory planem nie jest.
- **Weryfikacja:**
  ```bash
  dotnet run --project src/Sim.Runner -c Release -- budget \
      --axis data/track/L1_A.json \
      --signalling data/design/signalling/cbtc-test-2026.json \
      --limit-kmh 72 --exchange-s 20 --headway-s 10 --steps 2000 --trains 2
  dotnet test tests/Sim.Tests
  ```
  Oczekiwane: pierwsza komenda konczy sie odmowa nazywajaca brakujace pole, a nie
  kodem 134 ze stosem; zestaw rdzenia zielony o liczbie testow wiekszej niz przed.
- **Skończone, gdy:** kazdy plik JSON, ktory nie jest planem blokow, konczy sie odmowa
  z nazwa brakujacego pola, a kontrola negatywna WYKONANA (zdjeta obsluga) wywraca
  dokladnie nowy test. Test uzywa pliku z `data/`, ktory naprawde tam lezy — nie
  atrapy — bo to ten plik wywrocil proces.
- **Poza zakresem:** **dopisywanie planu CBTC w formacie, ktory rdzen czyta.** To jest
  praca projektowa i osobna decyzja; ta pozycja zajmuje sie wylacznie tym, ze zly plik
  ma dac odmowe, a nie sygnal. Poza zakresem takze ujednolicanie kodow wyjscia — ta
  sama granica, ktora postawily 6.A10 i 6.A11.
- **Zależy od:** nic.

##### 6.A14 · Nieliczbowa wartość opcji: komunikat bez nazwy opcji i po angielsku

- **Skąd:** zmierzone 06.09.2026 przy 6.D20 (#312). Wykonane:
  `line --axis data/track/L1_A.json --limit-kmh abc --exchange-s 20 --trace build/x.csv`
  daje `BŁĄD: The input string 'abc' was not in a correct format.` i kod 1. Komunikat
  pochodzi wprost z `double.Parse` i nie mówi **ani** której opcji dotyczy, **ani**
  którego polecenia — a jest jedynym śladem, jaki dostaje czytający. 6.D20 poprawiła
  komunikat o BRAKU opcji; ten o złej WARTOŚCI został nietknięty i to było świadome.
- **Wejście:** `src/Sim.Runner/Program.cs` (`RequiredNumber`, `OptionalNumber`,
  `ParseTrainCounts`, `ParseClock`), `tests/Sim.Tests/RunnerCommandTests.cs`
  (wzorzec testu kodu wyjścia i treści komunikatu z #291, #302, #312).
- **Wyjście:** komunikat nazywający opcję, jej wartość i polecenie, plus test kodu
  wyjścia **i treści** dla co najmniej dwóch różnych opcji.
- **Weryfikacja:**
  ```bash
  dotnet run --project src/Sim.Runner -c Release -- line --axis data/track/L1_A.json \
      --limit-kmh abc --exchange-s 20 --trace build/x.csv
  dotnet test tests/Sim.Tests
  ```
  Oczekiwane: komunikat wymienia `--limit-kmh` i `abc`, kod 1; zestaw rdzenia zielony
  o liczbie testów większej niż przed zmianą.
- **Skończone, gdy:** każda opcja liczbowa odmawia komunikatem nazywającym siebie,
  a kontrola negatywna WYKONANA (przywrócone gołe `double.Parse`) wywraca dokładnie
  nowe testy. Nazwa polecenia bierze się z `args[0]`, tak jak w 6.D20 — nie z nowej
  zaszytej stałej.
- **Poza zakresem:** tłumaczenie pozostałych komunikatów platformy .NET i zmiana
  kodów wyjścia. Ta sama granica, którą postawiły 6.A10, 6.A11, 6.A13 i 6.D20.
- **Zależy od:** #312 (scalone).

##### 6.A15 · Człon z jednym minusem przechodzi obok odmowy

- **Skąd:** 6.A11 (#307) dopisała odmowę nieznanej opcji i **sama wypisała tę dziurę**
  jako nietkniętą: sprawdzane są wyłącznie człony zaczynające się od dwóch minusów.
  Zmierzone ponownie 06.09.2026:
  `line --axis … --limit-kmh 72 --exchange-s 20 -zmyslona 7 --trace build/x.csv`
  kończy się **kodem 0**, dokładnie tak jak przed 6.A11.
- **Wejście:** `src/Sim.Runner/Program.cs` (`RejectUnknownOptions`, `KnownOptions`),
  `tools/tests/test_runner_options.py` (bramka zgodności tabeli z kodem),
  `tests/Sim.Tests/RunnerCommandTests.cs`, `reports/nieznana-opcja-runnera.md` §6.
- **Wyjście:** odmowa obejmująca także człony z jednym minusem — albo **pomiar
  pokazujący, że nie wolno jej rozszerzyć**, jeżeli któreś polecenie przyjmuje dziś
  wartość ujemną jako argument pozycyjny. Rozstrzygnięcie ma być zmierzone, nie
  założone: liczba ujemna po opcji z wartością jest pomijana razem z nią, ale
  pozycyjna nie.
- **Weryfikacja:**
  ```bash
  dotnet run --project src/Sim.Runner -c Release -- line --axis data/track/L1_A.json \
      --limit-kmh 72 --exchange-s 20 -zmyslona 7 --trace build/x.csv
  dotnet test tests/Sim.Tests
  ```
  Oczekiwane: pierwsza komenda kończy się odmową, a nie kodem 0.
- **Skończone, gdy:** człon z jednym minusem, którego polecenie nie zna, kończy się
  odmową, żadna istniejąca komenda z `docs/` ani z workflow nie zaczyna odmawiać —
  sprawdzone uruchomieniem, nie czytaniem — a kontrola negatywna WYKONANA wywraca
  dokładnie nowy test.
- **Poza zakresem:** dodanie form krótkich (`-o` jako skrót `--out`). To jest nowa
  funkcja, a nie domknięcie odmowy.
- **Zależy od:** #307 (scalone).

##### 6.B24 · Kontrola negatywna, która odbyła się raz

- **Skąd:** 6.B22 (#317) przeczytała treść 29 modułów i w §5 raportu nazwała jeden
  niuans, którego świadomie nie ruszyła: `tools/tests/test_dimension_audit.py` (l. 275)
  i częściowo `tools/tests/test_report_hygiene.py` (l. 35) dokumentują kontrolę
  **wykonaną naprawdę**, z wklejonym `FAIL` z uruchomienia na czasowo zmutowanym
  pliku — ale nie jako test, który psuje wejście przy KAŻDYM przebiegu. Kontrola,
  która odbyła się raz, jest dowodem historycznym; nie chroni przed regresją wzorca.
- **Wejście:** `tools/tests/test_dimension_audit.py`, `tools/tests/test_report_hygiene.py`,
  `reports/negative-control-audit-tresc.md` §5, `tools/tests/test_xml_doc_blocks.py`
  jako wzorzec kontroli wstrzykiwanej w katalogu tymczasowym (6.B21, #303).
- **Wyjście:** test regresyjny w każdym z tych dwóch modułów, budujący wejście
  w katalogu tymczasowym albo w pamięci — bez mutowania prawdziwych plików repozytorium.
- **Weryfikacja:**
  ```bash
  python3 tools/tests/test_all.py
  ```
  plus **wykonana i wklejona** kontrola: zepsuty wzorzec zapala nowy test, poprawny
  go nie zapala.
- **Skończone, gdy:** oba moduły mają kontrolę powtarzaną przy każdym przebiegu,
  docstring odsyła do niej zamiast cytować jednorazowy pomiar, a `git status` po
  przebiegu jest czysty — test, który mutuje plik w repozytorium i go nie przywraca,
  jest gorszy niż brak testu.
- **Poza zakresem:** przepisywanie datowanych pomiarów wklejonych w docstringach.
  To są zapisy historyczne i zostają.
- **Zależy od:** #317 (scalone).

##### 6.D21 · Objaw, którego nikt nie odtworzył

- **Skąd:** 6.D17 (#305) opisała dwa objawy braku konfiguracji .NET dla Godota
  i **odtworzyła jeden**: brak `DOTNET_ROOT` daje `Failed to load hostfxr` i sygnał 11,
  wykonane, z wklejonym wyjściem. Drugi — zawieszenie bez ani jednego wiersza na
  stdout przy brakującym assembly, z hostfxr JUŻ załadowanym — został w dokumencie
  jako zdanie, którego ta pozycja nie pokazała, i sama to napisała wprost.
- **Wejście:** `docs/23-environment.md` §4.1, `src/Game/`, `.github/workflows/godot-first-run.yml`,
  `doctor.sh` (sonda `godot .NET hostfxr` z #305).
- **Wyjście:** albo odtworzenie objawu z wklejonym wyjściem i limitem czasu, po którym
  proces został ubity, albo **pomiar pokazujący, że dziś nie da się go odtworzyć** —
  i wtedy zdanie w dokumencie przepisane tak, żeby mówiło, czego dotyczyło.
- **Weryfikacja:**
  ```bash
  bash doctor.sh
  python3 tools/tests/test_all.py
  ```
  plus **wykonana** próba: Godot uruchomiony z celowo usuniętym assembly, z limitem
  czasu i wklejonym wyjściem (albo jego brakiem) oraz kodem wyjścia.
- **Skończone, gdy:** dokument mówi o tym objawie **wyłącznie to, co zostało
  zmierzone**, a jeśli objaw jest nieodtwarzalny — mówi to wprost, z datą próby.
  Zdanie z drugiej ręki znika stąd tak samo jak z każdego innego miejsca w tym repo.
- **Poza zakresem:** zmiana czegokolwiek w `.github/workflows/` i dodawanie nowych
  sond do `doctor.sh` ponad tę z #305, jeżeli pomiar ich nie uzasadni.
- **Zależy od:** #305 (scalone).

##### 6.D22 · Raporty z przeglądów wołanych basename'em nie mówią, ile modułów objęły

- **Skąd:** 6.D18 (#310) rozstrzygnęła, że dopasowanie `--only` po podciągu jest
  **zamierzone** — istnieje test opierający się na `--only tools/track/` łapiącym cały
  katalog — i dopisała komunikat mówiący, ile modułów złapano. Stare raporty tego
  komunikatu nie mają: powstały wcześniej. 6.D18 wprost zostawiła je poza zakresem,
  z zasady „datowanego pomiaru się nie przelicza, wolno go co najwyżej OZNACZYĆ".
- **Wejście:** `reports/mutation-sweep.md` i pozostałe raporty z przeglądów mutacyjnych
  wołanych basename'em (bloki 6.B6, 6.B7, 6.B8, 6.D5 podają użyte komendy),
  `tools/tests/mutation_sweep.py` (`--only`, komunikat z #310).
- **Wyjście:** adnotacja przy każdym takim raporcie mówiąca, ile modułów objęła jego
  komenda — policzona **dziś**, przez `--only … --list`, a nie przepisana z pamięci —
  wraz z jawnym zdaniem, że liczby w raporcie pozostają liczbami z dnia pomiaru.
- **Weryfikacja:**
  ```bash
  python3 tools/tests/mutation_sweep.py --only sweep.py --list
  python3 tools/tests/test_all.py
  ```
  plus wypis: które raporty oznaczono i ile modułów objęła komenda każdego z nich.
- **Skończone, gdy:** każdy raport wołany basename'em pasującym do więcej niż jednego
  modułu ma adnotację z liczbą, a raport wołany jednoznacznie **nie dostaje jej wcale**
  — adnotacja bez powodu jest szumem. Żadna liczba wewnątrz datowanego pomiaru nie
  zostaje przeliczona.
- **Poza zakresem:** ponowne uruchamianie przeglądów mutacyjnych. Ta pozycja oznacza
  zakres komend, nie odtwarza wyników.
- **Zależy od:** #310.

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
| **6.A4** propagacja opóźnienia | przeniesione z kolejki 05.09.2026. Wpis T-320 ma sekcję STOP: „model perturbacji i polityka dyspozytora **nie są opisane w żadnym dokumencie**. Agent zatrzymuje się i pyta, zamiast wybierać sam”. Wiersz kolejki bronił się liczbą — „rozkład postojów jest zmierzony, 29 554 zatrzymań, 12–45 s” — ale zmierzony jest **rozkład postojów**, nie wielkość zaburzenia. Skąd wzięło się 30 s, nie mówi żadne źródło, a to jest właśnie model perturbacji |
| **6.B3** LOD tuneli pakietów B–F | przeniesione z kolejki 05.09.2026, po tym jak audyt (`reports/kolejka-audyt-aktualnosci.md` §1) pokazał, że pozycja opisuje trzy różne stany naraz. **B i E mają LOD od T-210** — wpis T-210 podaje „szczelina między chunkami, poziomami LOD i w bryle kolizyjnej 0,0000 mm w każdym pakiecie”. **C, D i F czekają na wiersz wyżej**, czyli na decyzję, co budować zamiast rury: `reports/surface-vs-tunnel.md` §1 podaje, że wszystkie 81 punktów sprzecznych między UrbIS a OSM leży w D (48) i F (33). Zostaje więc zero pracy, której nie blokuje tamta decyzja |
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
