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

### [ ] T-112 · Profil pionowy pakietu A — **CZĘŚCIOWO ODBLOKOWANE 07.09.2026**
- **Wpis przepisany, a nie dopisany obok.** Poprzednia wersja zaczynała się od
  „**Blokada:** brak publicznych rzędnych główki szyny" i to zdanie było prawdziwe
  jako opis danych, a **nieprawdziwe jako opis tego, co da się zrobić**: decyzja
  właściciela z 07.09.2026 mówi budować z jawnym `unknown`. Blokada wariantu
  `production` zostaje; blokada zbudowania czegokolwiek — nie.
- **Decyzja właściciela 07.09.2026:** trzy znane głębokości wchodzą do profilu,
  dziewięć pozostałych stacji zostaje **nazwane niewiadomą**, a nie zinterpolowane.
  Interpolacja przez wiersz `unknown` jest zabroniona wprost: odcinek między dwiema
  niewiadomymi jest niewiadomą, nie prostą. Wykonuje to pozycja **6.B44** w fazie 6.
- **Co nadal jest blokadą:** dwa oficjalne źródła podają **sprzeczne** głębokości
  (Schuman 15 m vs 17,42 m; Botanique 21,5 vs 20 m), więc wariant `production` nadal
  nie ma z czego powstać i generator go odrzuca. Decyzja z 07.09.2026 **nie wybiera
  strony konfliktu** — wybór zostaje przy T-901.
- **Ruszyło się przy R-007:** EIE Métro 3 (Livre III Colignon) podaje głębokości peronów
  **trzech** stacji pakietu A — De Brouckère i Arts-Loi ok. 11 m, Parc 19 m — wpisane do
  `station-depths.csv` ze statusem `estimated` i notatką o dwóch przekształceniach
  (peron → główka szyny, oraz „environ" w zdaniu porównawczym, nie w tabeli pomiarowej).
  Znane jest za to górne ograniczenie na całą sieć: **21,5 m** (Botanique, najgłębsza
  stacja). Poprzednia wersja tego punktu kończyła się zdaniem „**To nie odblokowuje
  zadania**" — zdjęte, bo od 07.09.2026 jest nieprawdziwe co do zakresu: trzy z dwunastu
  stacji nie dają profilu **produkcyjnego**, ale dają profil z nazwaną dziurą.
- **Wejście:** oś + `station-depths.csv`
- **Skończone, gdy:** pochylenia interpolowanego profilu są 0–4%, a każda wygenerowana wartość ma `interpolated:true` i `design_assumption`, **a każdy odcinek bez danych ma `confidence: unknown`** i nie ma wartości wcale
- **Zależy od:** T-111. **Już nie od T-901** dla wariantu z jawną niewiadomą — tylko dla `production`

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
| 6.A6 | **ZROBIONE (06.09.2026).** `LineRunSettings.CoastFromM` w rdzeniu, przełącznik `--coast-from-m` w poleceniu `line` (`Sim.Runner`), praca trakcji **per odcinek** w `StationCall`, wypis `[ODCINEK]` i `reports/coasting.md`. Wybieg od **250 metra** każdego odcinka pakietu A kosztuje **+2,7833 s** na cały przejazd i oszczędza **30,7309 kWh** pracy trakcji (142,4516 → 111,7207 kWh, **−21,6 %**); **wszystkie jedenaście** odcinków mieści się w rezerwie rozkładowej z T-113, a odcinek **Gare de l'Ouest → Beekkant** jest nazwany wprost jako ten, dla którego rozkład STIB **nie ma pary przystanków** i rezerwy nie ma (T-401 §2 liczy z tego samego powodu „10 z 10” przy jedenastu przejechanych). Pierwszym odcinkiem, który z rozkładu wypada, jest **Schuman → Merode** przy progu **150 m** (+11,4667 s wobec rezerwy +10,68 s) — i nie jest to odcinek o najciaśniejszej rezerwie, tylko **najdłuższy**: wybieg kosztuje proporcjonalnie do tego, jak długo się nim jedzie. Pole „Weryfikacja” spełnione **parą sum SHA-256**, nie kodem wyjścia: plik bez wybiegu ma tę samą sumę, którą 6.D15 zmierzyło dla OBU plików, a plik z wybiegiem inną. Pięć kontroli negatywnych WYKONANYCH, w tym para pilnująca obu kierunków bramki `test_runner_options.py` (opcja tylko w kodzie / opcja tylko w tabeli) — każda wywraca dokładnie te testy, które ma. Poza zakresem i nietknięte: dobór profilu jazdy dla gry, model oporów, krzywa hamowania, kody wyjścia runnera. Treść pierwotna: **Wybieg zamiast trakcji: ile kosztuje w czasie, ile oszczędza w energii** | czysty eksperyment na modelu, żadnych nowych danych | M |
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
| 6.B5 | **ZROBIONE (06.09.2026).** `reports/promien-luku-szesc-osi.md` — najciaśniejszy łuk na wszystkich sześciu osiach, z kilometrażem i skrajnią punkt po punkcie. R min od **50,87 m** (A, km 2518,6) do **82,28 m** (D, km 1916,2); `box_double` przechodzi na 2107 punktach z 2107, `bore_single` **nie przechodzi na A, C i E** — o 111,7 · 87,7 · 26,2 mm, w 20 punktach z 1277 na tych trzech osiach, przy policzalnej granicy R = 62,2 m. Najciaśniejszy łuk pakietu D leży na odcinku, którego OSM nie widzi jako tunel. 14 testów w `tools/tests/test_curve_radius_axes.py`, cztery kontrole negatywne wykonane. Progu dopuszczalnego luzu **nie wybrano** — nie ma go w repozytorium. Treść pierwotna: **Wykrywanie łuków o najmniejszym promieniu na każdej osi** i sprawdzenie skrajni M7 punkt po punkcie | metoda zmierzona i opisana (`reports/M7-curve-clearance.md`), zostaje zastosowanie | M |
| 6.B6 | **ZROBIONE w #270 (05.09.2026) — wpis zostaje w kolejce z powodu zapadki**, jak 6.D6, 6.B10, 6.B1, 6.B8, 6.D5 i 6.B7. Wykonane: `reports/mutation-triage-sweep.md`, werdykt dla każdej z **36** ocalałych (nie 37 — mutację z wiersza 54 zabił w międzyczasie dopisany test, a snapshotu z `66b8301` się nie przelicza). Podział: **22 zabijalne**, każda z wejściem rozstrzygającym i testem; **4 równoważne** z powodem przy każdej; **10 nierozstrzygniętych** — progi `1e-9` i `1e-18` na normach wektorów, gdzie nie znalazłem wejścia i **nie twierdzę, że go nie ma**. To rozróżnienie nie jest ostrożnością: docstring `test_chunk_a_span_exactly_at_the_cap_is_not_split` twierdził, że mutacja 219 jest równoważna „sprawdzone wykonaniem”, i **było to nieprawdą** — autor policzył pustą pętlę, ale przeoczył `break` tuż za nią, przez który mutant zostawia całą oś za odcinkiem równym limitowi niepodzieloną (350 m przy limicie 100 m: `[100.0]` zamiast trzech cięć). Docstring przepisany. 19 testów granicznych, każdy z progiem podanym **jawnie w argumencie**, bo cztery mutowane wiersze biorą stałą generatora jako domyślny. Treść pierwotna: **triaż 37 ocalałych mutacji `tools/blender/sweep.py`** — **największy** zestaw ocalałych w repozytorium (od #206, gdy `clearance_profile.py` zszedł z 45 do 17; wcześniej ten wiersz mówił „największy **niezablokowany**", bo tamten czekał na T-906 — dziś T-906 jest rozstrzygnięte); wynik idzie do `reports/mutation-triage-sweep.md`, którego dziś nie ma | `reports/mutation-triage-lod.md` §„Czego ten triaż nie ruszał" mówi wprost: „**`sweep.py`** — ocalałe tego modułu są osobną pozycją kolejki". Triaż klasyfikuje mutacje i dopisuje testy, nie zmienia ani jednej stałej — a stałe generatora są jawnie decyzją właściciela (`docs/21-measured-vs-assumed.md` §4) i zostają poza zakresem | L |
| 6.B7 | **ZROBIONE w #269 (05.09.2026) — wpis zostaje w kolejce z powodu zapadki**, jak 6.D6, 6.B10, 6.B1, 6.B8 i 6.D5. Wykonane: `reports/mutation-triage-m7-report.md`, werdykt dla każdej z dziewięciu — **wszystkie dziewięć to mutanty równoważne**, z trzech różnych powodów: cztery (46 ×2, 52 ×2) trafiają w próg, ale `round(…, 6)` scala oba wyniki (0 różnic na 404 wejściach, w tym 129 trafiających dokładnie w próg); cztery (85, 95, 96, 169) mają próg **nieosiągalny w IEEE 754**, bo `1e-4` i `1e-3` nie są wielokrotnościami `ulp` podstaw 1,35 / 0,9 / 1,6 (końcówki `prog/ulp` to `.049622`, `.099243`, `.496094`, przy działającej kontroli dodatniej); jedna (87) siedzi za filtrem z wiersza 85, który wyklucza jedyną różniącą wartość `y == 0`. **Kryterium „Skończone, gdy” tej pozycji jest nieosiągalne uczciwie** — żąda najwyżej 3 z 31, a mutantów równoważnych jest 9; trzy wyjścia i rekomendacja są w §6 raportu i czekają na decyzję właściciela. Zero nowych testów, świadomie: test przybijający zachowanie, którego żadne wejście nie odróżnia, kupuje procent i nie mówi nic o module. Treść pierwotna: **triaż 9 ocalałych mutacji `tools/blender/m7_report.py`** — jedyny moduł z co najmniej pięcioma ocalałymi, który nie miał w `reports/` żadnego raportu triażu | wszystkie dziewięć to operatory porównań w progach raportu dopasowania M7; klasyfikacja i testy graniczne, żadnej nowej liczby o taborze — wymiary M7 pochodzą z `data/vehicle/m7-spec.json` (T-904, zrobione) | M |
| 6.B8 | **ZROBIONE — i to nie w tej pozycji, tylko w 5.8 (`f5126a3`). Wpis zostaje w kolejce z powodu zapadki**, tak jak 6.D6, 6.B10 i 6.B1. Zmierzone 05.09.2026 na `ec926a2`, na TYM SAMYM zestawie klas, na którym powstał wiersz 2 / 2: `--operators operator,prog` daje **2 mutacje, 2 zabite, 0 ocalałych**, a pełny dzisiejszy zestaw 13 / 13 zabitych. Zabijają je testy z `test_make_test_track.py`, nie rozszerzenie zestawu operatorów — rozpisane w `reports/mutation-triage-make-test-track.md`. Treść pierwotna: **Triaż 2 ocalałych mutacji `tools/track/make_test_track.py`** — pierwszy wiersz tabeli „Kolejność triażu — po udziale" w `reports/mutation-sweep.md`, udział 100 % (2 / 2) | moduł generuje `BROKEN.json`, czyli kontrolę negatywną dla walidatora osi, i karmi dwie bramki CI (`tools/ci/blender_smoke.sh`, `tools/ci/visual_smoke.sh`); obie ocalałe siedzą w warunku, który decyduje, **gdzie** oś jest zepsuta — mutant przesuwa uszkodzenie, a bramki nadal świecą zielono. Oś jest syntetyczna, więc nie ma tu ani jednego faktu o Brukseli | S |
| 6.B9 | **ZROBIONE w #276 (06.09.2026) — wpis zostaje w kolejce z powodu zapadki.** Wykonane: trzy moduły bez `bpy` (`station_sections.py`, `marker_gates.py`, `material_specs.py`) i `reports/bpy-extraction-round-2.md`. **Nieosiągalne 53 → 24** przy progu 25, mierzone starym zestawem operatorów — tylko on jest porównywalny z liczbą 51 z raportu, bo na dzisiejszym pełnym zestawie pięciu klas jest ich 350 (#258 rozszerzyło zestaw). Rozbicie: `station_kit.py` 13 → 1, `detail_markers.py` 9 → 0, `material_test_scene.py` 12 → 4. **Refaktor nie zmienił ani jednego wierzchołka**: GLB identyczny co do bajtu, wszystkie trzy rendery identyczne co do pikseli. Suma SHA-256 pliku PNG nie mogła być wyrocznią, bo Blender stempluje w każdym renderze `Date` i `RenderTime` — stąd `tools/ci/png_pixels_sha256.py`, liczące sumę po blokach `IDAT`. **Pomyłka metody warta zapamiętania:** klasyfikacja po funkcjach („czy pada tu `bpy`”) mówiła, że w `material_test_scene.py` nie ma czego wyciągać, zero z dwunastu; klasyfikacja po wierszach dała osiem — predykaty zamurowane w funkcjach z `bpy`, ale same o Blenderze nie wiedzące. Granicą do przecięcia jest wiersz, nie funkcja. Treść pierwotna: **wyciągnięcie czystej logiki spod `bpy` z trzech modułów scen** | `reports/mutation-sweep.md` §„Moduły nieosiągalne" nazywa lekarstwo wprost: „Lekarstwem tutaj nie są testy, tylko dalsze wyciąganie logiki spod `bpy`", i ma dla tego zmierzony precedens z tego samego przebiegu (`m7_shell.py` 35 → 2, `tunnel_sweep.py` 35 → 6, `profile_vehicle.py` 26 → 7). Przeniesienie funkcji czystych nie zmienia geometrii wyjściowej — kontrolą jest identyczny GLB | L |
| 6.B10 | **ZROBIONE w #264 (05.09.2026) — wpis zostaje w kolejce z powodu zapadki, nie dlatego, że jest do zrobienia**, tak samo jak 6.D6 i z tego samego powodu: zdjęcie udokumentowanej pozycji zbija `MINIMUM_DOCUMENTED_ITEMS`, a zapadkę wolno tylko podnosić. Wykonane: trzy testy w `tools/tests/test_braking.py` wołają `report()` i porównują wypis z tablicą referencyjną z `reports/T-311-braking.md` §4 — sześć wierszy po dziewięć liczb, bez tolerancji. Kontrola negatywna obaliła pierwszą wersję testu: mutacja nagłówka na `DROGA HAMOWANIA_MUTANT` przechodziła sprawdzenie `"DROGA HAMOWANIA" in text`, więc oczekiwaniem jest teraz cały wiersz. Treść pierwotna: **`report()` w `tools/physics/braking.py` nie jest wykonywane przez nic** — ani test, ani skrypt `tools/ci/*.sh`; jedyny wołający to `if __name__ == "__main__"` w wierszu 313 | `reports/mutation-triage-fizyka.md` §6 zapisał to jako znalezisko poza triażem: „Funkcja drukuje trzy tablice referencyjne T-311 i mogłaby przestać się składać bez skutku dla CI. To jest osobne zadanie, nie triaż". Tablice referencyjne T-311 są już w `docs/02-simulation.md`, więc test porównuje wypis z tym, co repo już deklaruje | S |
| 6.B13 | **ZROBIONE w #284 (06.09.2026).** Dwa moduły bez `bpy` — `tools/blender/scan_gates.py` (trzy predykaty z `profile_vehicle.py`) i `tools/blender/lod_paths.py` (dwa z `tunnel_sweep.py`) — re-eksportowane pod starymi nazwami, z testem bezpośrednim na każdą funkcję; raport `reports/bpy-extraction-round-3.md`, zestaw narzędzi **1638 → 1655**. Nieosiągalne na starym zestawie klas (`operator,prog`, jedynym porównywalnym z liczbami z tego wiersza): `profile_vehicle.py` **7 → 2**, `tunnel_sweep.py` **6 → 4**. Liczby z wiersza zgodziły się z pomiarem dokładnie, bez rozjazdu — co jest tu warte zapisania, bo trzy inne pozycje kolejki zdezaktualizowały się tego samego dnia. **Czego pozycja NIE domknęła:** przebieg zabijania mutacji wyciągniętych funkcji jest pełny tylko dla `lod_paths.py` (2/2 zabite); na `scan_gates.py` rozstrzygnięta jest **1 z 5**, a cztery przekroczyły czas pod obciążeniem maszyny dzielonej z równoległymi agentami i są zapisane jako **nierozstrzygnięte, nie ocalałe** — trzeci stan, którego nie wolno zapisać jako żadnego z dwóch pozostałych. Domknięcie: ponowny przebieg bez współbieżności, opisane w §5 raportu | metoda jest zmierzona i opisana w `reports/bpy-extraction-round-2.md` §3: granicą do przecięcia jest **wiersz**, nie funkcja | M |
| 6.B14 | **ZROBIONE w #285 (06.09.2026).** `reports/mutation-triage-round-2-modules.md` i 23 testy; zestaw narzędzi **1638 → 1661**. **Pomiar obalił liczbę z tego wiersza:** funkcji bez ani jednego testu bezpośredniego było nie dziewięć, tylko **5 z 13** — cały `material_specs.py` i `straight_prism` w `station_sections.py`; reszta miała pokrycie pośrednie. Zabite mutacje na pełnym zestawie pięciu klas: `material_specs.py` **0 → 9 z 10**, `station_sections.py` **9 → 10 z 15**, `marker_gates.py` **9 z 9 już przed**. Pozostałe ocalałe mają werdykt **równoważna** z dowodem. **Jedna mutacja (`sweep_section`, `+=` → `=`) jest zapisana jako NIEROZSTRZYGNIĘTA**, nie zabita i nie ocalała: narzędzie padło na limicie czasu, a bezpośrednie wykonanie zmutowanego kodu pokazuje pętlę nieskończoną — czyli pod prawdziwym przebiegiem skończyłaby się timeoutem. Trzeci stan istnieje właśnie po to, żeby go nie zgadywać. Kalibracja wyroczni z #268 potwierdzona przed każdym z trzech pomiarów | pozycja 6.B9 świadomie ich nie dopisała: celem było uczynić je **mierzalnymi**, a ile z nich przeżyje przegląd, mówi dopiero pomiar | M |
| 6.B15 | **ZROBIONE (06.09.2026).** Zmierzone na `045730b`, nie na `51d324a` z opisu pozycji: modułów jest dziś **80** (nie 73), fraza dosłowna `"kontrola negatywna"` stoi w **34** (nie 33) — a kryterium dosłowne samo ma dziurę, bo polski odmienia: wzorzec dowolnej odmiany (`kontrol\w*\s+negatywn\w*`) znajduje **37**, trzy więcej (`test_m7_report.py`, `test_next_task.py`, `test_readme_claims.py`), wszystkie z genuine wykonaną kontrolą pod inną odmianą frazy. Wszystkie 80 dostały werdykt w `reports/negative-control-audit.md`: **38 z frazą** (po dopisaniu jednej — patrz niżej), **40 bez frazy, ale z wykonaną kontrolą znalezioną czytaniem treści** (np. `test_data_freshness.py::test_freshness_strict_mode_fails_only_on_expired`, `test_png_pixels.py` z jawnym `raise AssertionError` na nieodrzuconym złym pliku), **2 niepotrzebne** (`test_marker_gates.py`, `test_station_sections.py` — własną kontrolę negatywną mają zmierzoną w module siostrzanym, `reports/mutation-triage-round-2-modules.md`), **0 niewykonalnych** (zmierzone: żaden z 80 nie woła prawdziwego Blendera/Godota/.NET-a; PRZED tym wierszem `test_all.py` przechodził 1710/1710 bez ani jednego `SKIP` mimo braku wszystkich trzech narzędzi w tym środowisku). Jedyna kontrola dopisana: `test_streaming_fixture.py::test_a_planted_mismatch_in_the_fixture_actually_fails_the_comparison` — moduł sam ostrzegał we własnym docstringu, że „rozjazd nie wywala niczego", a żaden test tam tego nie sprawdzał; nowy test psuje jedno pole jednego wiersza W PAMIĘCI i dowodzi, że porównanie to łapie (zweryfikowane też w drugą stronę: bez psucia nowy test sam pada z czytelnym komunikatem). Zestaw **1709 → 1710**. Znalezione i świadomie nietknięte: `test_xml_doc_blocks.py` sprawdza dziś tylko PRAWDZIWY, aktualnie czysty `src/` — żaden test nie wstrzykuje sztucznie zdublowanego `<summary>`, więc licznik nigdy nie był złapany na błędzie. **Skutek ODHACZENIA tego wiersza, zmierzony, nie przypuszczony:** `open_items`/`documented_items` stały dokładnie na zapadce **12** i ten wiersz był w nich policzony — zdjęcie go zbijało zapas kolejki do **11**, czyli pod próg — i gałąź była z tego powodu czerwona, dopóki nie przesiadła się na aktualny `main`. **Powód czerwieni leżał w koordynacji, nie w tej pozycji:** agent dostał twardy zakaz ruszania czegokolwiek poza swoim wierszem, bo cztery gałęzie pracowały równolegle na tym samym pliku, więc nie miał czym zapasu uzupełnić i **zgłosił to wprost, zamiast naruszyć zakaz albo przemilczeć czerwień**. Po rebase na `main` z uzupełnieniem z #294 zapas wynosi **13** i zestaw jest zielony (1710/1710) | `CLAUDE.md` §5 nazywa tę kontrolę częścią pętli weryfikacji, a nie jej ozdobą; policzenie, gdzie jej nie ma, i dołożenie jej tam, gdzie da się ją wykonać, nie wymaga ani jednej decyzji | M |
| 6.B16 | **ZROBIONE (07.09.2026).** Zestaw pełny, dzisiejszy domyślny (`operator, prog, logika, argument, przypisanie`) — nieporównywalny z legacy zestawem `operator,prog` z raportów cytowanych niżej: `--only tools/track/detail_layout.py` złapało nim **33 mutacje** (nie 9). Wynik: **19 ocalałych z 33** — **15 zabitych** nowymi testami (8 precyzji zaokrągleń, 7 w `main()`/CLI, wszystkie siedem dotąd NIEURUCHOMIONE, bo żaden test nie wołał `main()`), **4 równoważne** z dowodem wykonanym (kolejność `sys.path.insert` bez kolidującego modułu w całym drzewie; próg `speed_mps<=0.0` dający tę samą wartość po obu stronach `0.0`; przesunięcie progu gałęzi o 0,001 dające różnicę 9,4×10⁻¹¹ m — 11 rzędów wielkości poniżej jedynej precyzji, jaką moduł wypisuje). Osobno: **1 nierozstrzygnięta** przez narzędzie (limit 300 s), rozstrzygnięta ręcznie jako zawieszenie (`index += 1`→`index = 1` daje pętlę bez końca — dowód w izolowanym podprocesie z limitem 2 s), więc NIE liczy się do 19 ocalałych. Po przeglądzie: **4 ocalałe** (te same, dowiedzione równoważne), pokrycie wierszy sondy 26/33 → 33/33. Zestaw testów **1836 → 1845**, `1845/1845 przeszło`. Kilometraż wobec T-011 (`reports/T-011-details-BF.md`) **bez zmian** — moduł nie był ruszany, tylko testy wokół niego. **Znalezisko poza zakresem, zgłoszone, nie poprawione po cichu:** cytat w kolumnie obok („8 ocalałych z 9") nie zgadza się z treścią pliku, który cytuje — `reports/mutation-drift.md` podaje dla tego modułu **1** ocalałą z 9 (legacy zestaw), zgodnie z `reports/mutation-sweep.md` i `reports/mutation-triage-parametry.md`; frazy „najgorszy stosunek w tabeli" ten plik w ogóle nie zawiera. **Drugie znalezisko, poza zakresem:** `tools/tests/mutation_sweep.py` jest dziś złamany dla KAŻDEGO modułu — kalibracja wyroczni pada w czystym drzewie, bo zaślepka `OWN_TESTS_STUB` (6.D18) nie ma strażnika `__main__`, którego wymaga `test_module_entrypoints.py` (6.D25); zmierzone lokalnym, NIGDY niecommitowanym obejściem, opisane w `reports/mutation-triage-detail-layout.md` §1 — potrzebuje własnej pozycji kolejki. Raport: `reports/mutation-triage-detail-layout.md`. Treść pierwotna: **Triaż ośmiu mutacji ocalałych na `tools/track/detail_layout.py`** — module, który wpis T-011 opisuje jako ten z **0 założeń** | `reports/mutation-drift.md` podaje dla niego 8 ocalałych z 9 mutacji; werdykt dla każdej z nich jest pomiarem, nie decyzją | M |
| 6.B17 | **ZROBIONE w #289 (06.09.2026).** Ścieżka domyślna jest teraz **jedna na przebieg** (commit + klasy operatorów + zawężenie `--only`), a dziennik z wpisami spoza przebiegu **przerywa start** kodem 2; raport `reports/dziennik-mutacyjny.md`, zestaw **1697 → 1700**. **Wiersz opisywał to za słabo:** nie chodziło o to, że dwa przebiegi sobie przeszkadzają, tylko o **mieszanie wyników** — wynik czytany jest z CAŁEGO dziennika, więc cudze wpisy wchodziły do raportu jako wynik tego pomiaru. Wykonana kontrola: dziennik z jednym obcym wpisem daje raport z pełną sekcją modułu, którego przebieg nie dotykał. **Znalezione obok i świadomie nietknięte:** wpis nie niesie commita, a identyfikator mutacji to przesunięcie bajtowe — pole Poza zakresem tej pozycji zabrania ruszać format, więc to osobna pozycja | znalezione przy 6.B14, gdzie dwa agenty liczyły równolegle; narzędzie samo tego nie sygnalizuje. Pomiar i poprawka domyślnej ścieżki, żadnej decyzji | S |
| 6.B18 | **ZROBIONE CZESCIOWO w #293 (06.09.2026), i to jest wynik, a nie wymowka.** Zmierzone czesci, raport `reports/czas-przegladu-mutacyjnego.md`: `git worktree add` **0,10 s** (nie „nie jest tani”), zestaw w swiezym worktree **50,9 s** wobec **65,0 s** w cieplym — czyli swiezy jest SZYBSZY, a roznice robi zaslepka zdejmujaca 64 testy narzedzia, nie brak pamieci podrecznej bajtkodu. Sonda pokrycia liczy sie **RAZ na przebieg**, kosztuje **~272 s** i to jest **84 % narzutu przed pierwsza mutacja**; licznik wierszy spowalnia zestaw **5,3-krotnie**. **CZEGO POMIAR NIE WYJASNIA:** suma czesci daje ~6,2 min wobec obserwowanych ponad 20 — **co najmniej dziesieciu minut nie umiemy przypisac**, i raport mowi to wprost, zamiast dopasowywac liczby. Nie zmierzono tez mutacji na minute przy 1, 2 i 4 robotnikach, czego zadalo pole Wyjscie. Reszta w 6.B20 | pomiar narzedzia pomiarowego: gdzie idzie czas, ile kosztuje `git worktree add` na mutacje, czy sonda pokrycia liczy sie raz czy za kazdym razem | M |
| 6.B19 | **ZROBIONE (07.09.2026).** Każdy wpis dziennika niesie teraz `commit` (`check_one`, przekazany przez `worker` i `sweep`), a `main` odmawia wznowienia kodem wyjścia 2, gdy dziennik niesie choć jeden wpis z **innego** commita niż przebieg bieżący, przed dotknięciem jakiejkolwiek mutacji — wpis bez pola `commit` (dziennik sprzed tej poprawki) liczy się jako obcy z tego samego powodu, co wpis bez pola `plik`. Raport `reports/dziennik-mutacyjny-bez-drzewa.md`, zestaw narzędzi **1828 → 1831**. Wykonany pokaz CLI w obie strony: dziennik z commitem `deadbee` na drzewie `7bf5062` → `PRZERWANE`, kod 2; ten sam dziennik z commitem `7bf5062` na tym samym drzewie → wznowienie normalne (`1 z 2 już policzonych`, prawdziwy identyfikator mutacji). Dwie kontrole negatywne wykonane osobno, każda łapie dokładnie jeden test: wyłączona odmowa → `FAIL test_resume_refuses_a_journal_written_on_another_tree` (67/68); zdjęte pole `commit` z `check_one` → `FAIL test_check_one_records_the_commit_it_ran_on: 'commit'` (67/68) — obie przywrócone, zestaw z powrotem 68/68. **Poza zakresem, świadomie:** sam identyfikator mutacji (`plik:wiersz:przesunięcie bajtowe`) bez zmian, bo jego zmiana przeliczyłaby dotychczasowe dzienniki i zerwała porównywalność z raportami triażu; drzewo zmienione MIĘDZY przebiegami NA TYM SAMYM commicie (`--dirty`, ta sama wartość `git rev-parse --short HEAD`, inna zawartość pliku) nie jest złapane, bo commit się wtedy nie zmienia — nazwane wprost w komentarzu przy miejscu wznawiania w `main`. Treść pierwotna: **Wpis dziennika mutacyjnego nie wie, z jakiego drzewa pochodzi** — nie niesie commita, a identyfikator mutacji to `plik:wiersz:przesunięcie bajtowe`, więc dziennik z wcześniejszego drzewa może podstawić wynik zapisany dla innego kodu | znalezione przy 6.B17 i tam świadomie nietknięte, bo tamta pozycja dotyczyła **ścieżki**, nie formatu. Pomiar i poprawka, żadnej decyzji | S |
| 6.B21 | **ZROBIONE (06.09.2026).** `tools/tests/test_xml_doc_blocks.py`: dwa istniejące testy bramki (`test_no_member_carries_two_summary_blocks`, `test_every_summary_is_closed_in_its_own_block`) rozłożone na wywołanie zwykłej funkcji (`_duplicate_summary_offenders`, `_unclosed_summary_offenders`) branej na liście ścieżek, żeby ta sama funkcja jechała po prawdziwym `_sources()` i po pliku wstrzykniętym w kontroli. Trzy nowe testy budują `.cs` w `tempfile.TemporaryDirectory()` (na dysku, nie w pamięci — nic zewnętrznego, bez `dotnet`): zdublowany `<summary>` przy jednym składniku zapala `_duplicate_summary_offenders` (1 offender, `Duplicated.cs:3 — 2 bloków <summary>`) i NIE zapala kontroli urwanego bloku; urwany `<summary>` (bez `</summary>`) zapala drugą bramkę (`1 otwarć, 0 zamknięć`) i NIE zapala pierwszej; plik czysty (jeden `<summary>`, domknięty) nie zapala żadnej z dwóch. Wykonane osobno w obie strony poza zestawem: `_duplicate_summary_offenders` na pliku zdublowanym pod `assert not …` daje `AssertionError` (bramka się zapaliła), na pliku czystym przechodzi. Zestaw **1716 → 1719** testów, moduł bramki **3 → 6** testów, `python3 tools/tests/test_all.py`: **1719/1719 przeszło**, `grep -cE '^\s*FAIL'` daje **0**. Treść pierwotna: **`test_xml_doc_blocks.py` sprawdza tylko drzewo, ktore JEST czyste** — nikt nie wstrzykuje tam sztucznie zdublowanego bloku `<summary>`, wiec bramka nie ma dowodu, ze umie zaswiecic | znalezione przy 6.B15. Naprawa tania, kontrola negatywna wykonalna bez zadnego narzedzia zewnetrznego | S |
| 6.B22 | **ZROBIONE (06.09.2026).** Nowy raport `reports/negative-control-audit-tresc.md`, zmierzone na `936c4ad`: liczby zastane z raportu 6.B15 (`045730b`) — **80** modułów, **34** z frazą dosłowną, **38** w odmianie dowolnej, z czego **8 przeczytanych**, **30 nie**; liczby dzisiejsze — **84** modułów, **36** dosłowna, **39** odmiana (jeden moduł doszedł: `test_xml_doc_blocks.py`, dostał prawdziwą kontrolę w 6.B21). Z 39 dzisiejszych, **10 rozstrzygniętych wcześniej** (8 próbką 6.B15 + 2 przeczytane w pełni: `test_streaming_fixture.py`, `test_xml_doc_blocks.py`) nie czytane ponownie; **29 przeczytanych w tej pozycji, wszystkie z werdyktem WYKONANA** — sito ze 100 % pokryciem 149 wystąpień (blok `def`/`class` wokół frazy zawiera `assert`/`raise`), 5 wystąpień bez tego oznaczonych i doczytanych ręcznie (`test_docs_ci_claims.py`, `test_report_claims.py`, `test_report_hygiene.py`, `test_surface_sections.py`, `test_t401_citation.py` — wszystkie okazały się odsyłać do kontroli wykonanej gdzie indziej w tym samym pliku), plus ręczna próbka z pozostałych 144 wystąpień w każdym z 29 plików. Zero modułów w kategorii „fraza bez żadnej kontroli za nią" — więc zero dopisanych testów. Jeden niuans nazwany z imienia, nie usterka: `test_dimension_audit.py` niesie kontrolę wykonaną RĘCZNIE (prawdziwy `FAIL` wklejony do docstringu, plik przywrócony po pomiarze), nie jako osobny automatyczny test regresyjny — nazwane w raporcie §5, nic nie dopisane. `python3 tools/tests/test_all.py`: **1734/1734 przeszło**, `dotnet test tests/Sim.Tests`: **534/534 przeszło**, zero zmian w `src/` i w `tools/tests/`. Treść pierwotna: **Tresc 30 z 38 modulow z fraza `kontrola negatywna` nie zostala sprawdzona** — 6.B15 zweryfikowal probke 8 z 38 i powiedzial to wprost | modul moze nazwac kontrole i jej nie wykonac; fraza jest przyblizeniem, nie dowodem. Doczytanie reszty to pomiar, nie decyzja | M |
| 6.B20 | **ZROBIONE (07.09.2026).** Zmierzone JEDNYM ciaglym procesem, nie suma osobnych uruchomien jak 6.B18: trzy pelne przebiegi na `lod_paths.py` (2 mutacje) przy 1/2/4 robotnikach dały **600,3 s / 535,2 s / 534,3 s**, a suma zmierzonych faz (worktree, kalibracja wyroczni, sonda pokrycia, robotnicy) zgadza sie z kazdym z tych calkowitych czasow z dokladnoscia **<=0,0007 s (<=0,00013 %)** — to te same znaczniki `time.monotonic()`. Sonda pokrycia dominuje: **416,7-426,6 s, 80,8-89,3 % przebiegu**, niezaleznie od liczby robotnikow. Tabela mutacji na minute: sama faza robotnikow **1,03 / 2,00 / 1,95** (workers 1/2/4, srednia z 3 powtorzen), caly przebieg **0,20 / 0,22 / 0,22** — workers=2 i workers=4 wypadaja identycznie, bo `sweep()` z **2** mutacjami tworzy tylko **2** niepuste porcje niezaleznie od `--workers` (zmierzone w kodzie, w. 744-745). **Znalezisko obok pytania:** `main()` narzedzia dzis ZAWSZE przerywa sie kodem 2 na kalibracji wyroczni, zanim policzy cokolwiek — `test_module_entrypoints.py` (6.D25, scalone PO 6.B18) wymaga straznika `__main__` w KAZDYM `test_*.py`, a zaslepka `neutralise_own_tests` w KAZDYM worktree zostawia `test_mutation_sweep.py` bez niego; do tego zapas `docs/TASKS.md` jest pod progiem. Pomiar obszedl to wolajac funkcje narzedzia bezposrednio (werdykty zabita/ocalala z tego przebiegu sa przez to niewazne, czasy — nie). Raport `reports/reszta-czasu-przegladu.md`, adnotacja w `reports/czas-przegladu-mutacyjnego.md`. Zestaw narzedzi bez zmian: **1841 → 1841** (dwa pre-existing FAIL od zapasu kolejki, niezwiazane z ta pozycja). Tresc pierwotna: **Dziesieciu minut przegladu mutacyjnego nadal nikt nie umie przypisac** — 6.B18 zmierzyl czesci i wyszlo ~6,2 min wobec obserwowanych ponad 20 | pomiar, nie decyzja: 6.B18 rozlozyl narzut na czesci i **powiedzial wprost**, ze suma sie nie zgadza; zostaje znalezc reszte i domierzyc mutacje na minute przy 1, 2 i 4 robotnikach, czego tamta pozycja nie zdazyla | M |

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
| 6.D2 | **ZROBIONE (06.09.2026).** Bramka pilnuje DWOCH warunkow, i drugi jest wazniejszy: koszt kroku ponizej progu **oraz** to, ze pomiar dotyczy **dziewieciu** skladow na planie. Powod drugiego jest zmierzony: 6.A12 pokazala, ze `budget --trains 32` melduje `N_max = 1` przy oknie krotszym niz jeden odstep — kolumna µs/krok ma wtedy wartosc i **miesci sie w progu z ogromnym zapasem**, tylko opisuje inny przejazd. Prog **8,0 us/krok** = 1,71x nad najwyzszym znanym pomiarem tego scenariusza (4,665 us, §8.4) i 2,11x nad najwyzszym z trzech przebiegow tutaj (3,798 / 3,772 / 3,655 us); to **0,096 %** budzetu 1/120 s. Margines pochlania nieznana predkosc runnera wlasciciela — ten sam sposob doboru i to samo uzasadnienie co przy 6.D11. Prog i scenariusz stoja w JEDNYM miejscu (`tools/ci/linecore-step-budget.json`), krok CI wola wylacznie skrypt i nic nie porownuje sam — pilnuje tego osobny test. **Cztery WYKONANE kontrole negatywne**, kazda z innym powodem odmowy: krok 9,091 us, pomiar jednego skladu podany jako dziewiec (miesci sie w czasie, wiec odmowa wynika wylacznie z obsady), prog przepisany do YAML-a, obsada w pliku progu zmieniona na 1. Pomiar w `reports/linecore-step-budget-gate.md`. Tresc pierwotna: **Bramka na czas przebiegu** — regres wydajności rdzenia widoczny, zanim zablokuje N składów | pomiar, nie decyzja | S |
| 6.D4 | **ZROBIONE w #273 (06.09.2026) — wpis zostaje w kolejce z powodu zapadki.** Wykonane: `tools/tests/test_report_claims.py` i `reports/report-claims-audit.md`. **Pierwszy pomiar zawęził zakres pozycji i to jest jej główny wynik:** z ośmiu twierdzeń postaci „`plik_testowy`, N testów” **siedem rozjechało się z drzewem i siedem jest poprawnych** — raport opisywał plik w dniu pomiaru, a plik urósł; bramka żądająca tam równości kazałaby przeliczać datowany pomiar, czego zakazuje 6.D3. Sprawdzalna jest **wartość stałej**: 65 nazw pada w raportach, 37 ma definicję w kodzie, **12 jest zacytowanych z wartością i wszystkie 12 się zgadzają**. Wzorzec trzeba było zwęzić — wersja pierwsza dała **3 fałszywe alarmy na 15** przez tabele odwzorowań `219 → NAZWA, 237 → INNA`, w których brała numer wiersza następnej pary za wartość poprzedniej. Druga poprawka wyszła z tego, że bramka **wywróciła się na własnym raporcie**: cytat z kontroli negatywnej wygląda jak twierdzenie, więc bloki ogrodzone są pomijane. Zgłoszone, nie poprawione: `M7-shell.md` mówi 22 testy przy 21 w pliku — jedyny rozjazd w stronę, której datowanie nie tłumaczy. Treść pierwotna: **kontrola spójności liczb między `reports/` a kodem** — wartość wypisana w raporcie musi dać się odtworzyć z repo | dokładnie ta klasa rozjazdu, którą audyt znalazł w README | M |
| 6.D5 | **ZROBIONE w #259 (`08d9650`, 05.09.2026) — wpis zostaje w kolejce z powodu zapadki**, jak 6.D6, 6.B10, 6.B1 i 6.B8. Wykonane: `reports/mutation-drift.md` obejmuje **28 modułów** zamiast wymaganych dwunastu, a `tools/tests/test_mutation_sweep.py` ma sześć testów dryfu, w tym `test_drift_report_pins_the_two_cases_the_task_names`, czyli dokładnie kryterium „Skończone, gdy”. Znalezione audytem kolejki 05.09.2026, nie zgłoszone przy scaleniu. Treść pierwotna: **Audyt dryfu pokrycia mutacyjnego po triażu** — które moduły odzyskały ocalałe od czasu swojego raportu triażu, i przybicie ich z powrotem | rozjazd jest już zmierzony i leży w dwóch plikach naraz: `tools/track/crs.py` miał po triażu 6 ocalałych na 8 mutacji (`reports/mutation-triage-wczytywanie.md` §Wynik), a przebieg z `66b8301` w `reports/mutation-sweep.md` pokazuje **8 na 14**; `tools/ci/assert_shot_metadata.py` miał **2 na 33** (`reports/mutation-triage-png-metadata.md` §Wynik), a dziś ma **6 na 39**. Porównanie dwóch raportów, które już istnieją — żadnej nowej danej | M |
| 6.D6 | **ZROBIONE w #258 (05.09.2026) — wpis zostaje w kolejce z powodu zapadki, nie dlatego, że jest do zrobienia.** `test_backlog.py` trzyma `MINIMUM_DOCUMENTED_ITEMS = 8`, a udokumentowanych pozycji jest dokładnie osiem; przeniesienie którejkolwiek do tabeli domknięć zbija licznik do siedmiu i wywraca `test_the_documented_reserve_does_not_regress`, a komentarz przy zapadce mówi, że wolno ją tylko podnosić. Decyzja właściciela z 05.09.2026: wpis zostaje z tą adnotacją. Treść pierwotna: **rozszerzenie zestawu operatorów `tools/tests/mutation_sweep.py`** poza porównania i progi liczbowe — przypisania, wywołania i łączniki logiczne. Wykonane: dwie klasy urosły do pięciu (`logika`, `argument`, `przypisanie`), a stary zestaw odtwarza `--operators operator,prog` co do sztuki (1038 = 1038) | `reports/mutation-sweep.md` §„Czego ten przebieg NIE pokrywa, choć pozycja 5.1 tak brzmi" wypisuje ten brak w tabeli: pozycja 5.1 mówi „każdą kontrolę", a narzędzie mutuje „wyłącznie **operatory porównań i progi liczbowe**; nie mutuje przypisań, wywołań ani łączników logicznych". Praca w samym narzędziu pomiaru; baza do porównania jest zmierzona (980 mutacji, 51 nieosiągalnych, 929 policzonych na `66b8301`) | L |
| 6.D7 | **ZROBIONE w #278 (06.09.2026).** `NAMES_THE_PLATFORM_PARAMETER` wymaga teraz **współwystąpienia słowa „peron"** z wyrażeniem o jawnym parametrze i przyjmuje odmianę (`jawn\w+ parametr\w*`), więc zwężenie jest zarazem rozszerzeniem. W korpusie bramki **5 → 4 trafienia**: wypadło dokładnie to fałszywe (udział odzysku energii z bloku 6.A5), nie ubyło ani jedno prawdziwe, a doszły zdania w rodzaju „długość peronu **jest jawnym parametrem**", których stara wersja nie widziała, bo szukała frazy w mianowniku. Dwie kontrole negatywne wykonane; **druga jest tu ważniejsza** — zdanie dopisane bez nazwy stałej, samym zwrotem w odmianie, zapala bramkę, czego stary wzorzec nie robił. Bez niej „zwężenie” mogłoby po cichu zejść do szukania samej nazwy `DESIGN_PLATFORM_LENGTH_M` i przestać sprawdzać prozę. `PARAMETER_VALUE` zostawiony szeroki z powodem przy stałej: żąda wartości w metrach, więc zdania o procentach nie zapala, a jest ostatnią rzeczą widzącą wiersz, w którym generator dostaje wartość jawnym parametrem bez słowa „peron” obok — treść pierwotna: **`NAMES_THE_PLATFORM_PARAMETER` w `test_dimension_audit.py` łapie samo wyrażenie „jawny parametr"** i żąda od niego wartości 95,0 m — także wtedy, gdy zdanie mówi o zupełnie innym parametrze | zmierzone 06.09.2026 przy #272: zdanie o udziale odzysku energii w bloku 6.A5 zapaliło bramkę długości peronu. Zwężenie wzorca to ta sama praca co przy `test_report_claims.py` (#273), gdzie zwężenie zdjęło 3 fałszywe alarmy na 15 | S |
| 6.D8 | **ZROBIONE w #277 (06.09.2026).** Rozstrzygnięte: **liczba była nieprawdziwa od początku**, nie zestarzała się. `reports/M7-shell-liczba-testow.md` pokazuje to pomiarem, nie argumentem: plik testowy i raport wnosi do drzewa **ten sam commit** (`de574ff`, squash-merge PR-a #43), plik ma przez całą historię **jeden niezmieniony blob** `efae116`, a w każdej osiągalnej wersji — łącznie z jedynym commitem gałęzi przed squashem — `grep -c '^def test_'` daje **21**. Nie ma w historii momentu, w którym obie liczby byłyby zgodne, więc możliwość „testy usunięto” jest wykluczona pomiarem. Skąd wzięło się 22: `grep -c '^def '` daje 22, bo liczy też pomocnika `_layout()`, którego `test_all.py` nie zbiera — policzono definicje zamiast testów. `reports/M7-shell.md` **przepisany**, nie dopisany obok, z pomiarem zostawionym w wierszu 77, żeby odsyłacz z §1 audytu dalej w niego trafiał — treść pierwotna: **`reports/M7-shell.md` mówi „22 testy" przy 21 w pliku** — jedyny rozjazd liczby testów, którego datowanie NIE tłumaczy | siedem pozostałych rozjazdów z `reports/report-claims-audit.md` §1 idzie w stronę „raport mniej, plik więcej", czyli plik urósł po pomiarze. Ten idzie w drugą: raport nie mógł policzyć więcej testów, niż plik miał. Rozstrzyga `git log --follow` po `tools/tests/test_m7_shell.py`, bez ani jednej decyzji | S |
| 6.D9 | **ZROBIONE w #288 (06.09.2026).** `idat_sha256` jest wołane z `capture_blender.py` (obok sumy pliku, nie zamiast) i z `compare.py` pod przełącznikiem żądania zgodności co do bajtu; `visual_smoke.sh` używa go w teście determinizmu i ma obok kontrolę negatywną na JEDEN piksel. 9 testów, zestaw **1694 → 1703**, raport `reports/pixel-hash-oracle.md`. **Pomiar:** dwa przebiegi tej samej sceny, pięć klatek — **suma pliku różna na wszystkich pięciu, suma `IDAT` identyczna na wszystkich pięciu**; z 18 chunków PNG różnią się dokładnie dwa, oba `tEXt`: `Date` i `RenderTime`. **Co to naprawdę zmieniło:** test determinizmu pytał dotąd wyłącznie o progi, a różnica jednego kanału jednego piksela mieści się w progach z manifestu i przechodziła tędy po cichu — test nazywał się determinizmem, a mierzył podobieństwo. Progi zostają nietknięte tam, gdzie porównuje się różne sceny. Przy okazji kalibracja wyroczni z #268 złapała **mój własny test bez ani jednej asercji** | narzędzie i dowód, że suma całego pliku PNG jest bezużyteczna jako wyrocznia, są już w repo; zostaje zastosowanie | M |
| 6.D10 | **ZROBIONE w #292 (06.09.2026).** Zmierzone na HEAD (`08d12b6`), nie na `51d324a` z opisu pozycji — w tej sesji doszło 8 raportów od tamtego pomiaru: **69** raportów (nie 48) niosą SHA w nagłówku. Dla każdego zbadana relacja (`git log --follow` / `git merge-base --is-ancestor` na commicie, który wpisał ten konkretny token, przez pickaxe `-S`, nie na pierwszym dodaniu pliku — węższa wersja fałszywie dawała ŻADNA sześciu raportom, którym SHA był przodkiem edycji nagłówka): **23 dotyka, 41 przodek wprowadzenia, 4 ŻADNA (z nazwy: `bpy-extraction-round-2.md`, `bpy-extraction-round-3.md`, `energy-balance.md`, `mutation-triage-round-2-modules.md` — wszystkie ten sam wzorzec: SHA gałęzi sesyjnej, `main` dostał inny obiekt przy scaleniu), 1 NIEOSIĄGALNY (`mutation-triage-lod.md` / `c572eb3`, już opisany w `test_report_hygiene.py`)**. Bramki **nie dopisano**: cztery przypadki ŻADNA to powtarzalny tryb pracy tej sesji, nie zamknięta lista wyjątków, a relacja i tak nie przetrwałaby CI — sprawdzone wprost na płytkim klonie (`--depth 1`), gdzie `git merge-base --is-ancestor` nie ma historii do rozstrzygnięcia, dokładnie jak `actions/checkout` na self-hosted runnerze (`CLAUDE.md` §9) — pomiar w `reports/commit-naglowka-a-raport.md` | pozycja mierzy relację, a nie decyduje o niej; dopiero pomiar mówi, którą wolno przybić bramką, a której nie wolno | S |
| 6.D11 | **ZROBIONE (06.09.2026).** Liczba 1638 była już nieaktualna — zestaw ma dziś **1709** testów w **80** modułach (**1715**/**81** po dopisaniu tej pozycji). Cztery przebiegi CAŁEGO `python3 tools/tests/test_all.py` z rzędu na kontenerze dzielonym z innymi sesjami agenta: **66,20 / 68,45 / 68,96 / 77,04 s** — rozrzut 15,45 % przy tym samym kodzie. Próg **`SUITE_RUNTIME_BUDGET_S = 150,0`** w nowym `tools/tests/test_suite_runtime_budget.py` to ×2 nad najwyższym zmierzonym przebiegiem (77,04 s), zaokrąglone w dół; margines pochłania prędkość maszyny właściciela (nieznaną tej sesji) i codzienny przyrost zestawu. Bramka żyje w kroku CI (`.github/workflows/python-tests.yml`), **nie** w kodzie wyjścia `test_all.py` — `tools/tests/mutation_sweep.py` czyta z tego procesu WYŁĄCZNIE linię `N/M przeszło` i kod wyjścia jako dowód przeżycia mutacji, więc czas związany z tym kodem zamieniłby zwykłe spowolnienie maszyny w falę fałszywych „zabić". Dwie kontrole negatywne WYKONANE: próg obniżony do 10,0 w drzewie pada natychmiast na własnej bramce asercji (`1713/1715`, dwa `FAIL`), a to samo porównanie bash z kroku CI, uruchomione na realnym zmierzonym czasie z progiem obniżonym do 40,0, daje kod wyjścia 1. Pełna tabela per moduł (81 wierszy) i uzasadnienie marginesu: `reports/test-all-runtime-gate.md`. Treść pierwotna: **Bramka na czas przebiegu `test_all.py`** — 1638 testów w 62,8 s, i nikt tego nie pilnuje | bliźniak 6.D2 po stronie Pythona: pomiar, nie decyzja | S |
| 6.D12 | **ZROBIONE (06.09.2026).** Cztery miejsca piszą do `data/`: `fetch_gtfs.py` i `fetch_stib_shapes.py` bezpośrednio (manifest proweniencji zmienia się przy każdym uruchomieniu, **także w `--offline`** — zmierzone dwoma realnymi przebiegami `fetch_gtfs.py` dziś, identyczny `content_sha256`, różny tylko `retrieved_at`), `build_alignment.py` i `normalize_stops.py` pośrednio — oba osadzają `retrieved_at` manifestu w commitowanym pliku wynikowym (`data/track/*.json`, `data/network/stops.json`), więc dziedziczą tę samą niestabilność bez własnego wywołania zegara. Sprawdzone i odrzucone: `snapshot_source.py`, `data_freshness.py` i dziewięć pozostałych narzędzi `tools/track/*.py` — `--out` wymagane lub domyślnie poza `data/`, żadne udokumentowane wywołanie ich tam nie kieruje. Pomiar w `reports/zapisy-do-data.md`, cztery warianty na klasę zapisu wypisane obok siebie z kosztem każdego — treść pierwotna: **Które narzędzia piszą do `data/`, choć katalog jest tylko do odczytu** — `tools/track/fetch_gtfs.py` aktualizuje manifest proweniencji przy każdym pobraniu | `CLAUDE.md` §4.6 nie przewiduje wyjątku, a narzędzie robi to celowo. Pozycja **mierzy rozjazd i wypisuje warianty**, nie rozstrzyga go — wybór między zmianą reguły a zmianą narzędzia zostaje właścicielowi | S |
| 6.D13 | **ZROBIONE (06.09.2026).** Zmierzone na całym `reports/` (80 plików, nie 71 z opisu pozycji): wzorzec `COMMIT` łapie w nagłówkach **90** tokenów, długości `{7: 78, 12: 1, 40: 11}` — dokładnie **jeden** nie jest commitem, `9e2066aef7ef` w `T-400-stage-3b.md` (hash builda Blendera, potwierdzone jeszcze raz po 6.D10). Wzorzec w `tools/tests/test_report_hygiene.py` zawężony z zakresu `{7,40}` na dokładne długości `{7}`/`{40}` — te dwie, które faktycznie produkuje `git` (`rev-parse --short` i pełny SHA-1) i jedyne, jakich ten projekt kiedykolwiek używa (zmierzone: zero tokenów w przedziale 8..39 poza tym jednym fałszywym). Nowy test `test_wzorzec_commita_lapie_realne_dlugosci_i_nie_lapie_hasza_narzedzia` w tym samym module, kontrola negatywna WYKONANA w obie strony: podmiana z powrotem na `{7,40}` zapala dokładnie ten jeden nowy test (żaden z dziewięciu istniejących), zawężony wzorzec nadal łapie skrócony i pełny SHA. Zestaw **1734 → 1735** testów, `python3 tools/tests/test_all.py`: **1735/1735 przeszło**, kod wyjścia 0. Pomiar i pełna tabela 90 tokenów: `reports/wzorzec-commita-falszywe-trafienia.md`. Żaden nagłówek raportu nie został zmieniony — token zostaje, bo jest poprawną informacją o środowisku pomiaru. Treść pierwotna: **Wzorzec SHA w bramce higieny raportow lapie tez to, co SHA nie jest** — token `9e2066aef7ef` w naglowku jednego raportu to hash builda Blendera, nie commit | znalezione przy 6.D10. Pomiar, ile takich falszywych trafien jest w 71 raportach, i zawezenie wzorca albo nazwanie wyjatku — bez decyzji wlasciciela | S |
| 6.D14 | **ZROBIONE (06.09.2026).** Dwa nowe testy w `tools/tests/test_fetchers.py`, po jednym na narzędzie: `test_fetch_gtfs_offline_never_calls_provenance_fetch_url` i `test_fetch_stib_shapes_offline_never_calls_provenance_fetch_url`. Oba podmieniają `provenance.fetch_url` (jako `P.fetch_url` w module narzędzia) na funkcję rzucającą `RuntimeError`, budują minimalny poprawny plik wejściowy w katalogu tymczasowym — pięcioplikowy GTFS dla `fetch_gtfs.py`, dwuplikowy shapefile (linie + przystanki, zbudowany w locie bez `bpy`) dla `fetch_stib_shapes.py` — i sprawdzają, że `main(["--offline", ...])` kończy się kodem **0**; `SystemExit`, gdyby jednak padł, jest złapany jawnie i zamieniony w `AssertionError`, bo inaczej uciekłby jako `BaseException` mimo `except Exception` w `test_all.py` i wywróciłby cały zestaw zamiast tylko tych dwóch testów. `test_fetchers.py`: **16 → 18** testów; cały zestaw: **1736 testów, zielony**, kod wyjścia 0. Kontrola negatywna WYKONANA: to samo wywołanie bez `--offline` (podmieniona funkcja faktycznie zostaje wywołana) wywraca **dokładnie te dwa i tylko te** — `1734/1736 przeszło`, reszta bez zmian — po czym plik przywrócony do wersji z `--offline`. `git status --short data/` puste po całym przebiegu. Treść pierwotna: **Czy `--offline` w `fetch_gtfs.py`/`fetch_stib_shapes.py` naprawdę nie dotyka sieci** — zmierzone przy 6.D12 czytaniem kodu (`P.utc_now_iso()` zamiast `P.fetch_url()` w tej gałęzi), nie testem z zablokowaną siecią | dowód sieciowy jest testem: podmiana funkcji pobierającej na wersję rzucającą wyjątek i sprawdzenie, że `--offline` mimo to kończy się sukcesem — bez ani jednej decyzji właściciela | S |
| 6.D15 | **ZROBIONE (06.09.2026).** Zebrane **82** komendy z **42** blokow (stan bloku szczegolow w chwili pomiaru). Werdykty: **73** uruchamialne, **4** wymagaja Blendera albo geometrii, ktora Blender produkuje, **5** niewykonalnych tak, jak pole obiecuje. Piec niewykonalnych z nazwy: 6.D2 (pole wymienialo 3 z 7 opcji, ktorych wymaga `Budget` — kod 1 na `BLAD: line wymaga --limit-kmh`), 6.A6, 6.C3 (kod 9, odmowa laczenia zrodel — to znalezisko otworzylo te pozycje), 6.D9 i 6.B18 (miejsce do wypelnienia w nawiasie ostrokatnym). Najciezsze znalezisko jest w 6.A6: `--coast-from-m` nie wystepuje nigdzie w `src/`, a `Sim.Runner` **nieznana opcje przyjmuje w milczeniu**, wiec obie komendy pola koncza sie kodem 0 i daja pliki **identyczne co do bajtu** — te weryfikacje spelnia NIEZROBIENIE zadania. Poprawione trzy pola pozycji niezrobionych (6.D2, 6.A6, 6.C4 o brakujacy warunek wstepny: kod 4, `[ASSETS] brak manifestu`); bloki pozycji ZROBIONYCH zostaly nietkniete jako zapis historyczny. Kolektor komend jest w `tools/tests/backlog_commands.py`, bramka na miejsca do wypelnienia w `tools/tests/test_backlog_commands.py` (trzy WYKONANE kontrole negatywne), pomiar w `reports/komendy-weryfikacji.md`. Tresc pierwotna: **Ile komend z pol „Weryfikacja" w blokach kolejki da sie w ogole uruchomic** — komenda z bloku 6.C3 jest odrzucana przez istniejaca odmowe, kod wyjscia 9 | znalezione przy 6.C3. Pole „Weryfikacja" jest obietnica, ktorej nikt nie sprawdza; pomiar, ile z nich klamie, nie wymaga zadnej decyzji | M |
| 6.D16 | **ZROBIONE (06.09.2026).** Zdanie o `retrieved_at` w `docs/09-data-provenance.md` przepisane, nie dopisane obok: teraz nazywa różnicę między **manifestem proweniencji** (`retrieved_at` jest tam czystą metadaną obserwacji, poza `content_sha256` surowego wejścia) a **plikiem wynikowym** — `build_alignment.py` kopiuje pole do `document["source"]["retrieved_at"]` w commitowanym `data/track/*.json`, `normalize_stops.py` do `document["feed"]["retrieved_at"]` w commitowanym `data/network/stops.json`, więc dla tych dwóch plików zdanie o niezmienności nie zachodzi. Nowa bramka `tools/tests/test_provenance_retrieved_at_claim.py` (4 testy) pilnuje, żeby stare bezwarunkowe zdanie nie wróciło i żeby oba narzędzia nadal osadzały pole tam, gdzie dokument to dziś opisuje; kontrola negatywna wykonana — z przywróconym starym zdaniem bramka pada (`FAIL test_doc_names_the_manifest_vs_output_distinction_and_both_tools`, kod wyjścia `test_all.py` 1), po przywróceniu poprawki znów zielono. Zestaw narzędzi **1733/1733**, kod wyjścia 0. Poza zakresem, tak jak żądało pole „Poza zakresem": nie rozstrzygnięto, czy narzędzia mają przestać osadzać `retrieved_at`, czy reguła ma dostać jawny wyjątek — to nadal decyzja właściciela. Treść pierwotna: **`docs/09-data-provenance.md` twierdzi cos, co dla dwoch miejsc jest nieprawda** — ze `retrieved_at` nie moze zmieniac byte-deterministycznego wyjscia, a w `build_alignment.py` i `normalize_stops.py` trafia wprost do commitowanego pliku | znalezione przy 6.D12. Pomiar i przepisanie zdania, ktore przestalo byc prawdziwe | S |
| 6.D17 | **ZROBIONE (06.09.2026).** `docs/23-environment.md` ma nową §4.1 z dwoma **wykonanymi** przebiegami tego samego pliku binarnego (`Godot_v4.7.2-stable_mono_linux.x86_64 --headless --path src/Game`): bez `DOTNET_ROOT` i bez `dotnet` w `PATH` — sygnał 11, `Failed to load hostfxr`, 0,34 s; z `DOTNET_ROOT="$HOME/.dotnet"` — hostfxr się ładuje i proces idzie dalej do kodu gry (pada dopiero na osobnym, niepowiązanym braku manifestu chunków — w tym środowisku nie ma Blendera). Zmierzone: `DOTNET_ROOT` sam wystarcza, `dotnet` w `PATH` jest zbędny, jeśli `DOTNET_ROOT` wskazuje katalog z `host/fxr/*/libhostfxr.so`; zły katalog **nie** korzysta z tego skrótu i wraca do tej samej awarii przez `dotnet` odpalane przez powłokę. `doctor.sh` dostał nową sondę **`godot .NET hostfxr`**, bo istniejąca (`--version`) przechodzi identycznie z `DOTNET_ROOT` i bez niego — nie dotyka mono, więc nic by nie złapała; nowa sonda sprawdza `DOTNET_ROOT` (z `host/fxr/*/libhostfxr.so`) albo `dotnet` w `PATH` i nazywa przyczynę zamiast milczeć do limitu czasu, potwierdzone w trzech wariantach (brak obu, sam `DOTNET_ROOT`, sam `dotnet` w `PATH`). Zestaw narzędzi **1716/1716** w 81 modułach, `dotnet test tests/Sim.Tests` **528/528**. Druga postać usterki z opisu tej pozycji (zawieszenie bez wyjścia przy brakującym assembly) nie została odtworzona osobno — nie ma tu scenariusza z hostfxr załadowanym i brakującym konkretnym assembly do zademonstrowania; dokument nazywa ją i mówi wprost, że nie jest tu pokazana. Poza zakresem: `.github/workflows/` nietknięte. Treść pierwotna: **`docs/23-environment.md` nie mowi, ze Godot wymaga `DOTNET_ROOT`, nie tylko `PATH`** — bez tego pada `Failed to load hostfxr` sygnalem 11, a przy brakujacym assembly wisi bez ani jednego wiersza na stdout do wypalenia limitu czasu | znalezione przy 6.C3, na wlasnej skorze. Dokument ma powiedziec to, co trzeba ustawic | S |
| 6.A11 | **ZROBIONE (06.09.2026).** `Sim.Runner` odmawia nieznanej opcji w kazdym z **dziewieciu** polecen: `line ... --coast-from-m X` konczy sie teraz kodem **1** i komunikatem `BLAD: polecenie line nie zna opcji --coast-from-m. Zna: ...` — wczesniej kod 0 i przebieg nie do odroznienia od poprawnego. Kod wyjscia NIE jest nowa stala: to ta sama, ktora `Program.cs` daje wszystkim odmowom argumentowym przez wspolny handler `ArgumentException`. Tabela `KnownOptions` jest reczna, zeby komunikat wymienial opcje TEGO polecenia, a nie sume wszystkich — i dlatego dostala bramke `tools/tests/test_runner_options.py`, ktora czyta `Program.cs` jako tekst, wyprowadza nazwy z wywolan `Option`/`RequiredNumber`/`OptionalNumber`/`Array.IndexOf` i porownuje oba zbiory w OBIE strony, bez `dotnet`. Nietkniete i sprawdzone uruchomieniem: argument pozycyjny (`compare A B`) przechodzi, flaga `--atp` nie zjada nastepnego czlonu, ta sama komenda bez nieznanej opcji nadal konczy sie kodem 0. Cztery WYKONANE kontrole negatywne, kazda wywraca dokladnie te testy, ktore ma (`dotnet test` 528 -> **532**). Pomiar w `reports/nieznana-opcja-runnera.md`. Tresc pierwotna: **`Sim.Runner` przyjmuje nieznana opcje w milczeniu** — `line ... --coast-from-m X` konczy sie kodem 0, choc ani opcji, ani wartosci `X` nie ma w kodzie | zmierzone przy 6.D15 (#301): dwie komendy z pola „Weryfikacja" pozycji 6.A6 daly pliki identyczne co do bajtu. Wyrocznia zepsuta w strone „wszystko w porzadku" | M |
| 6.A12 | **ZROBIONE (06.09.2026).** Dwa mechanizmy, oba zmierzone, zaden nie jest bledem. **Pierwszy: okno krotsze niz jeden odstep.** Sklady sa zglaszane na krok `i x odstep`, wiec przy `--headway-s 120` (14 400 krokow) i `--steps 1000` (okno **8,3 s**) sklad numer 1 wypada poza okno pomiaru — `N_max = 1` niezaleznie od `--trains`. **Drugi: sufit 12 skladow na tej osi.** Przy oknie 1667 s i odstepie 30 s ORAZ 10 s `N_max` przestaje rosnac na **12**, a `N_sr` stoi na **7,56** — dla 12, 13, 16 i 24 zgloszonych identycznie co do cyfry; przybywa wylacznie kolumna „czeka" (4,05 -> 4,97 -> 7,72 -> 14,79). Mechanizmem jest **brama wjazdowa** `LineCore.EntryIsClear`: sklad wjezdza tylko, gdy zaden blok nakladajacy sie na jego obrys w punkcie wjazdu nie jest zajety, a plan ma 23 bloki. Dla 6.D2 istotne: **dziewiec skladow jest osiagalne** (`N_max = 9` przy odstepie 10 s i oknie 200 000 krokow), koszt **4,540 us/krok** = 0,05 % budzetu 1/120 s, a przy suficie 12 — **5,995 us/krok** = 0,07 %. Pomiar w `reports/obsada-planu.md`. Tresc pierwotna: **`budget --trains 32` melduje `N_max=1`** — kolumna `N_zgl` nie jest liczba skladow, ktore bieglyby po planie | zmierzone przy 6.D15 (#301). Pomiar wydajnosci, ktory nie obciaza tego, co obiecuje obciazyc, jest bramka bez zebow — a na tej liczbie ma stanac 6.D2 | M |
| 6.A13 | **ZROBIONE (06.09.2026).** Plik, ktory planem blokow nie jest, konczy sie teraz odmowa **kod 1** z komunikatem `dokument nie ma pola 'protection_variant' — to nie wyglada na plan sygnalizacji…`, zamiast kodem **134** i stosem wywolan. Poprawka jest jednym pomocnikiem `Required(owner, field, what)` w `SignallingPlan.FromJson`, ktory zamienia `JsonElement.GetProperty` na `TryGetProperty` + `FormatException` w **11** odczytach na poziomie dokumentu plus w `DesignValue` i w polu `generation`. **Nie wprowadza nowego kodu wyjscia**: `FormatException` jest na liscie handlera od poczatku i uzywaja jej wszystkie pozostale odmowy tego loadera. Dwa testy, oba na PRAWDZIWYCH plikach z `data/` (atrapa dowodzilaby czegos innego niz to, co sie zdarzylo): `cbtc-test-2026.json` konczy sie odmowa, `classic-2026.json` nadal przechodzi kodem 0. Kontrola negatywna WYKONANA — powrot do `GetProperty` wywraca dokladnie jeden test (535/536). `dotnet test` 534 -> **536**. Tresc pierwotna: **Plan CBTC wywraca `Sim.Runner` sygnalem, nie odmowa** — `budget --signalling data/design/signalling/cbtc-test-2026.json` konczy sie kodem **134** i stosem wywolan, bo `KeyNotFoundException` z `SignallingPlan.FromJson` nie jest lapany przez wspolny handler `Program.Main` | znalezione przy 6.A12. Plik jest opisem obszaru i trybu (`area_id`, `mode`, `status`), a nie planem blokow — komunikat ma to powiedziec, a nie sypnac stosem | S |
| 6.B23 | **ZROBIONE (06.09.2026).** Nowa bramka `tools/tests/test_sim_untested_members.py` liczy skladniki `src/Sim/**/*.cs` bez pliku pod `tests/`, ktory wzmiankuje ich nazwe jako cale slowo — tak jak liczyl wiersz powloki z 6.A8 — ale najpierw odrzuca sciezki z segmentem `obj` albo `bin`. Na drzewie po `dotnet build src/Sim` (Debug i Release) bramka widzi 57 plikow `.cs`, po pominieciu `obj/` zostaje 53, i zero z nich jest bez testu; identyczny wynik (53/53) na czystym drzewie sprzed budowania. Kontrola negatywna WYKONANA: skladnik dopisany do `src/Sim` bez wzmianki w `tests/` zapala `test_no_real_sim_member_is_missing_from_tests` (`python3 tools/tests/test_all.py` konczy sie kodem 1), po usunieciu pliku drzewo wraca do zielonego; osobny test w tym samym module dowodzi, ze cztery pliki generowane przez `dotnet build` (`Sim.AssemblyInfo.cs` i `.NETCoreApp,Version=v10.0.AssemblyAttributes.cs` w Debug i Release) nie maja swojej nazwy nigdzie w `tests/` — czyli bez pominiecia `obj/`/`bin/` bramka klamalaby na kazdym zbudowanym drzewie. Lista wyjatkow (`KNOWN_EXCEPTIONS`) jest pusta — pomiar nie pokazal zadnego prawdziwego skladnika `src/Sim`, ktory legalnie nie moze miec testu. Blok `##### 6.A8` pozostaje nietkniety jako zapis historyczny. Poza zakresem: dopisywanie brakujacych testow do `src/Sim` — bramka nie znalazla dzis ani jednego brakujacego, wiec nie ma czego dopisywac. Treść pierwotna: **Licznik „modul `src/Sim` bez testu" skanuje razem z `obj/`** — po `dotnet build` wypisuje cztery falszywe wiersze `BRAK TESTU` dla plikow generowanych | zmierzone przy 6.D15 (#301). Licznik zyje dzis wylacznie jako wiersz powloki w zapisie historycznym 6.A8; jako bramka w `tools/tests/` nie istnieje | S |
| 6.D18 | **ZROBIONE (06.09.2026).** Rozstrzygnięte pomiarem, nie gustem: podciąg jest zamierzony, bo `test_cli_lists_only_the_requested_class` już opiera się na tym, że `--only tools/track/` łapie cały katalog naraz — dopasowanie po samej nazwie pliku by to zablokowało. Cena podciągu zostaje więc widoczna zamiast cicha: `--only sweep.py --list` wypisuje teraz w PIERWSZYM wierszu, PRZED dziennikiem i przed jakąkolwiek mutacją, `[MUTACJE] --only 'sweep.py' złapało 185 mutacji z 2 moduł(ów): tools/blender/sweep.py, tools/blender/tunnel_sweep.py` (117 + 68 = 185, ta sama liczba co przy 6.D15). Docstring narzędzia i help `--only` nazywają decyzję wprost. Nowy test `test_only_is_a_substring_match_by_design_and_says_how_many_modules_it_caught` w `tools/tests/test_mutation_sweep.py` sprawdza treść komunikatu dla dopasowania dwu- i jednomodułowego; kontrola negatywna WYKONANA (komunikat wycięty) wywraca dokładnie ten jeden test, `1730/1730` po przywróceniu. Bloki 6.B6/6.B7/6.B8/6.D5 zostają nietknięte jako zapis historyczny. Treść pierwotna: **`--only` w `mutation_sweep.py` dopasowuje podciag, nie nazwe pliku** — `--only sweep.py` obejmuje `tools/blender/sweep.py` (117 mutacji) **i** `tools/blender/tunnel_sweep.py` (68) | zmierzone przy 6.D15 (#301). Kazdy raport z przegladu mutacyjnego wolany basename'em mowi o innym zbiorze plikow, niz nazywa | M |
| 6.D19 | **ZROBIONE (06.09.2026).** `_discover()` w `test_all.py` łapie teraz wyjątek z `AG.load_instrumented()` per moduł zamiast zostawiać go nieprzechwyconym — moduł, który się nie importuje, dostaje wiersz `FAIL <import>nazwa_pliku: KlasaWyjątku: komunikat`, liczy się do `failed` (kod wyjścia zostaje 1) i nie blokuje odkrycia pozostałych modułów ani wiersza `N/M przeszło`. Kontrola negatywna WYKONANA: moduł z `def test_broken(:` wrzucony do `tools/tests/` — PRZED zmianą `kod: 1`, zero dopasowań `grep -cE '^\s*FAIL'`, zero wierszy `N/M przeszło` (dokładnie usterka z opisu); PO zmianie `kod: 1`, jeden wiersz `FAIL <import>test_zzz_broken_probe: SyntaxError: invalid syntax (...)`, wiersz `1729/1729 przeszło` obecny. Nowy test `test_gate_a_broken_import_produces_a_grep_visible_fail_line_and_keeps_the_summary` w `tools/tests/test_assertion_gate.py` odtwarza to samo w jednym procesie (podmiana `AG.paths()` na piaskownicę, bez dotykania prawdziwego `tools/tests/`). Zestaw narzędzi **1729 → 1730** testów, zielony. `mutation_sweep.py --only lod_paths.py --workers 2` uruchomiony po zmianie: nadal czyta `N/M przeszło` i kod wyjścia z tego samego procesu, bez zmiany zachowania — wynik wklejony w raporcie sesji. Treść pierwotna: **Modul, ktory sie nie importuje, nie daje ani jednego wiersza `FAIL` ani wiersza `N/M przeszlo`** — `test_all.py` konczy sie wtedy kodem 1, ale kazdy grep po `FAIL` pokazuje zero i wyglada jak zielono | zmierzone przy 6.D15 (#301) na wlasnym module z bledem skladni. Ta sesja sprawdzala zielonosc grepem i przez chwile wierzyla, ze drzewo jest zielone | M |
| 6.D20 | **ZROBIONE (06.09.2026).** Nazwa polecenia bierze sie teraz z `args[0]`, a nie ze stalej w tresci komunikatu — i to jest cala poprawka, jeden wiersz. Zmierzone: `budget` bez `--limit-kmh` dawal `BLAD: line wymaga --limit-kmh`, dzis daje `BLAD: budget wymaga --limit-kmh`; `line` bez `--limit-kmh` nadal daje `BLAD: line wymaga --limit-kmh`. Oba kod 1. `RequiredNumber` jest wspolny dla **trzech** polecen (`line`, `budget`, `replay`), wiec zaszyta nazwa mylila w dwoch przypadkach na trzy. Sprawdzone po jednym: **wszystkie pozostale** komunikaty „X wymaga …" w `Program.cs` sa literalami w ciele jednego polecenia i nazywaja je poprawnie — poprawka dotyczy wylacznie tego jednego miejsca. Dwie WYKONANE kontrole negatywne, kazda wywraca dokladnie jeden test: przywrocona stala `line` wywraca `Budget_bez_limitu_nazywa_budget_a_nie_line`, a nowa, tak samo sztywna stala `budget` wywraca `Line_bez_limitu_nadal_nazywa_line` — para testow lapie wiec rozjazd w obie strony, nie tylko powrot starego bledu. `dotnet test` 534 -> **536**. Tresc pierwotna: **`RequiredNumber` w `Program.cs` nazywa `line` niezaleznie od polecenia** — `budget` bez `--limit-kmh` konczy sie komunikatem `BLAD: line wymaga --limit-kmh` | zmierzone przy 6.D15 (#301). Komunikat kieruje czytajacego do niewlasciwego polecenia; osiem pozostalych polecen ma ten sam problem, bo dziela ten sam pomocnik | S |
| 6.A14 | **ZROBIONE (07.09.2026).** Wszystkie **jedenaście** zmierzonych dróg wartości opcji do liczby odmawia dziś komunikatem `POLECENIE nie rozumie wartości OPCJA: „WARTOŚĆ” nie jest liczbą`, zamiast komunikatem platformy .NET `The input string 'abc' was not in a correct format.`, który nie mówił ani której opcji dotyczy, ani którego polecenia. **Sondowanie PRZED zmianą wykazało cztery różne pomocniki, nie jeden**: `RequiredNumber` i `OptionalNumber` (`double`), osobne `long.Parse` dla `--steps` i `--sample-every`, osobne `int.Parse` dla `--repeats`/`--warmup` i dla członów `--trains`, oraz `ParseClock` dla `--at` — poprawka jednego nie dowiodłaby niczego o pozostałych trzech, więc testy biorą wszystkie cztery drogi. `NotANumber` jest **jedynym pisarzem** treści (zasada z 6.A20), a nazwa polecenia bierze się z `args[0]` przez wspólny `Command(args)`, nie z nowej zaszytej stałej (zasada z 6.D20) — bramka pilnuje obu. **Dwie decyzje przeciwstawne i każda ze swoim testem**: `--trains 1,2,4,abc` cytuje zły **człon**, bo przy liście czytający ma zobaczyć, który z czterech jest zły, a `--at 10:xx:00` cytuje **całą** wartość, bo `xx` nie powiedziałoby, którą opcję poprawić. **Zbiór przyjmowanych postaci się nie zwężył** i to jest osobny, wykonany test (`7.2E1`, `5.5`) — bez niego cała reszta byłaby zielona także dla poprawki, która przestaje przyjmować kropkę dziesiętną. Nowa bramka `tools/tests/test_runner_number_parsing.py` (8 testów) czyta `Program.cs` jako tekst: goły `Parse` poza jedynym usprawiedliwieniem (komórki CSV w `Compare` — zła komórka nie jest złą opcją) jest błędem, lista usprawiedliwień jest sprawdzana w **obie** strony, a próg **6** na liczbę miejsc rozbioru istnieje, żeby literówka we wzorcu dawała FAIL, nie zero znalezisk. **Próg wpisałem najpierw jako 7 — z szacunku, nie z pomiaru — i sam się zapalił przy pierwszym przebiegu**: `TryParse` jest w czterech miejscach, nie pięciu. Siedem WYKONANYCH kontroli negatywnych; KN-4 (zwężony zbiór postaci) i KN-7 (nieaktualny wpis usprawiedliwienia) mierzą wartość rzeczy, których same testy treści nie łapią. `dotnet test` 554 → **562**. Pomiar w `reports/wartosc-nieliczbowa.md`. Poza zakresem, zgodnie z polem: tłumaczenie pozostałych komunikatów platformy i zmiana kodów wyjścia; rozbiór komórek CSV w `compare` wyszedł z tego samego sondowania i stoi w kolejce jako **6.A24**. Tresc pierwotna: **Nieliczbowa wartosc opcji daje komunikat po angielsku, bez nazwy opcji** — `line ... --limit-kmh abc` konczy sie `BLAD: The input string 'abc' was not in a correct format.` | znalezione przy 6.D20 (#312). Komunikat nie mowi ANI ktorej opcji dotyczy, ANI ktorego polecenia — a jest to jedyny slad, jaki dostaje czytajacy | S |
| 6.A15 | **ZROBIONE (07.09.2026).** Warunek odmowy zmieniony z `StartsWith("--")` na `StartsWith("-")` — `line … -zmyslona 7` kończy się dziś **kodem 1** i komunikatem `BŁĄD: polecenie line nie zna opcji -zmyslona. Zna: …`, a nie kodem 0 jak przed 6.A11. **Bezpieczeństwo rozszerzenia ZMIERZONE, nie założone**, tak jak żądało pole „Wyjście": członów z jednym minusem w komendach `Sim.Runner` w repozytorium jest **56** i **ani jeden** nie dochodzi do programu — 55 razy `-c` stoi PRZED separatorem `--`, czyli jest flagą `dotnet run`, a `->` to strzałka w prozie; **wartości ujemnych zero**; jedyne argumenty pozycyjne to dwie **ścieżki** polecenia `compare`, które minusem się nie zaczynają. **Goły minus jest wyjątkiem** — konwencja „standardowe wejście" nie jest pomyłką, a odmowa ma łapać pomyłki. Wartość ujemna znanej opcji nadal przechodzi, bo człon po opcji z wartością jest pomijany razem z nią: `--stop-window-m -5` dostaje **właściwą** odmowę z walidacji dziedzinowej (`Okno stacji musi być skończone i dodatnie`), nie komunikat o nieznanej opcji `-5` — zamiana cichej dziury na komunikat mówiący nieprawdę byłaby najgorszym wynikiem tej pozycji. Bramka z 6.A11 **przepisana, nie skasowana**: przybijała literalnie `StartsWith("--"`, a jej intencja — że ścieżki `compare` przechodzą nietknięte — jest nadal aktualna, więc nowa wersja żąda warunku na jednym minusie **i** wyjątku dla gołego minusa. Trzy WYKONANE kontrole negatywne, każda topi **dokładnie jeden i za każdym razem inny** test (powrót do dwóch minusów, zdjęty wyjątek gołego minusa, zdjęte pomijanie wartości), przy niezmienionej sumie 557 — co po nauczce z 6.B27 jest częścią kontroli. `dotnet test` 554 → **557**. Pomiar w `reports/jeden-minus.md`. Poza zakresem, zgodnie z polem: formy krótkie (`-o`) — to nowa funkcja; postać `--opcja=wartość` i powtórzona opcja wyszły z tego samego sondowania i stoją w kolejce jako **6.A22** i **6.A23**. Tresc pierwotna: **Odmowa nieznanej opcji nie widzi czlonu z JEDNYM minusem** — `line ... -zmyslona 7` konczy sie kodem **0**, tak jak przed 6.A11 | znalezione przy 6.A11 (#307) i wypisane tam jako nietkniete; zmierzone ponownie 06.09.2026. Dziura jest waska, ale to dokladnie ta sama wyrocznia zepsuta w strone „wszystko w porzadku" | S |
| 6.B24 | **ZROBIONE (06.09.2026).** Wzorcem 6.B21: rdzeń każdej z dwóch bramek wydzielony do zwykłej funkcji branej na liście wejść, żeby ta sama funkcja jechała po prawdziwych plikach i po wejściu wstrzykniętym. `test_dimension_audit.py`: `_platform_prose_offenders(lines, expected)` — dokładny rdzeń testu z l. ~275, dziś wołany zarówno przez `test_prose_naming_the_platform_parameter_carries_the_value_from_the_code` (prawdziwe pliki), jak i przez nowy `test_platform_prose_offender_lights_up_on_synthetic_input_and_stays_quiet_on_correct_one`, nad trzema wierszami zbudowanymi w pamięci: wiersz tabeli i zdanie prozy z ZŁĄ wartością zapalają offendera (te same dwa warianty co jednorazowa kontrola z 06.09.2026 opisana w docstringu), ta sama para z POPRAWNĄ wartością milczy. `test_report_hygiene.py`: `_reports()` rozłożone na `_reports_in(directory)`, plus `_date_offenders`, `_commit_offenders`, `_no_subheading_offenders` — te same funkcje wołane przez trzy istniejące bramki i przez nowy `test_missing_date_commit_and_subheading_offenders_light_up_on_injected_reports`, nad czterema `.md` napisanymi do `tempfile.TemporaryDirectory()` (bez daty, bez commita, bez śródtytułu, czysty) — każdy z trzech braków zapala WYŁĄCZNIE swoją bramkę, czysty raport żadnej, wyjątek zdejmuje offendera tak samo jak dla prawdziwych list. Zestaw testów **14 → 15** (`test_dimension_audit.py`) i **9 → 10** (`test_report_hygiene.py`), `python3 tools/tests/test_all.py`: **1740/1740 → 1742/1742 przeszło, kod wyjścia 0**. Kontrola negatywna WYKONANA dla obu nowych testów: podmiana `_platform_prose_offenders` na wersję martwą (zawsze `[]`) wywraca dokładnie nowy test dimension_audit z `AssertionError`; podmiana `_date_offenders` (i osobno `_no_subheading_offenders`) na wersję martwą wywraca dokładnie nowy test report_hygiene, oba przywrócone od razu po pomiarze. `git status` po przebiegu: dwa zmienione pliki, oba w `tools/tests/`, żaden plik w `reports/` ani w `docs/21-measured-vs-assumed.md` nie tknięty. Treść pierwotna: **`test_dimension_audit.py` ma kontrole negatywna wykonana RECZNIE, nie jako test regresyjny** — dowod jest wklejony w docstringu, ale zaden przebieg `test_all.py` go nie powtarza | znalezione przy 6.B22 (#317), §5 raportu, ktore swiadomie tego nie ruszylo. Kontrola, ktora odbyla sie raz, nie chroni przed regresja wzorca | M |
| 6.D21 | **ZROBIONE (06.09.2026).** Objaw nieodtworzony — zmierzone, nie zgadniete. Szesc niezaleznych, WYKONANYCH probb na tym samym pliku binarnym (`DOTNET_ROOT` ustawiony, hostfxr sie laduje), kazda z limitem czasu 20 s i wklejonym wyjsciem: usuniety `MetroBxl.Sim.dll` projektu (0,37 s, `System.TypeLoadException`, kod 0), usuniety `MetroBxl.Game.dll` (0,47 s, seria `Cannot instantiate C# script`, kod 0), usuniety `GodotSharp.dll` silnika (0,46 s, **brak zmiany** — silnik ma wlasna kopie obok `GODOT_BIN`, kod 4 jak baseline), usuniety i osobno obciety do 200 B `GodotPlugins.dll` silnika (0,23–0,34 s, sygnal 11, `Failed to get GodotPlugins initialization function pointer`), podmieniona wersja w `runtimeconfig.json` projektu (0,86 s, **brak zmiany** — silnik czyta wlasny plik obok `GODOT_BIN`), i podmieniona `project/assembly_name` w `project.godot` na nieistniejaca (0,50 s, kod 0). Zaden z szesciu wariantow nie zawiesil procesu ani nie dal pustego stdout — kazdy skonczyl sie w 0,2–0,9 s jednym z trzech sposobow: dalszy bieg (silnik ma zapasowa kopie assembly), `TypeLoadException`/`Cannot instantiate` z kodem 0, albo SIGSEGV. Zdanie w `docs/23-environment.md` §4.1 przepisane: mowi teraz wylacznie to, co zmierzono, z data proby, i nazywa niezbadane pozostale mozliwosci (inna wersja Godota/.NET, brakujaca biblioteka natywna runtime'u) jako niezbadane, nie jako fakt. Pelne wyjscia szesciu prob: `reports/6d21-objaw-nieodtworzony.md`. Drzewo przywrocone po kazdej probie — pliki w `.godot/` i katalogu instalacji Godota z kopii zapasowej (sumy/rozmiary potwierdzone), `project.godot` z `git diff` pustym. `python3 tools/tests/test_all.py` **1740/1740**, `dotnet test tests/Sim.Tests` **538/538**. Tresc pierwotna: **Drugi objaw z 6.D17 nie zostal odtworzony** — zawieszenie Godota bez ani jednego wiersza na stdout przy brakujacym assembly, z zaladowanym hostfxr | znalezione przy 6.D17 (#305), ktore powiedzialo wprost, ze tego nie pokazalo. Objaw, ktorego nikt nie odtworzyl, jest w dokumencie zdaniem z drugiej reki | M |
| 6.D22 | **ZROBIONE (06.09.2026).** Sprawdzone dzis przez `--only … --list` cztery komendy z blokow 6.B6, 6.B7, 6.B8 i 6.D5: tylko `--only sweep.py` z `reports/mutation-triage-sweep.md` (blok 6.B6) jest dwuznaczna — obejmuje **2 moduly**, `tools/blender/sweep.py` i `tools/blender/tunnel_sweep.py` (83 mutacje zestawem operatorow z raportu `operator,prog`, 185 dzisiejszym pelnym zestawem piatki klas) — i dostala adnotacje z ta liczba wprost w tresci raportu, z jawnym zdaniem, ze liczby §0/§6 (79 mutacji, 36→14 ocalalych) zostaja liczbami z dnia pomiaru i dotycza wylacznie `sweep.py`. Pozostale trzy sprawdzone komendy sa wolane jednoznacznie i adnotacji NIE dostaly: `--only m7_report.py` (`reports/mutation-triage-m7-report.md`, blok 6.B7) i `--only make_test_track.py` (`reports/mutation-triage-make-test-track.md`, blok 6.B8) trafiaja kazda w dokladnie jeden modul, a `reports/mutation-drift.md` (blok 6.D5) woła `crs.py` i `assert_shot_metadata.py` juz pelnymi sciezkami (`tools/track/crs.py`, `tools/ci/assert_shot_metadata.py`), nie basename'em, wiec dwuznacznosci tam nie ma. Zestaw narzedzi **1740/1740**, kod wyjscia 0. Treść pierwotna: **Raporty z przegladow wolanych `--only` basename'em nie mowia, ile modulow objely** — 6.D18 rozstrzygnela, ze podciag jest zamierzony, i wprost zostawila oznaczenie starych raportow poza zakresem | znalezione przy 6.D18 (#310). Datowanego pomiaru sie nie przelicza, ale wolno go OZNACZYC — i dopoki nie jest oznaczony, czyta sie jak pomiar jednego modulu | S |
| 6.A16 | **ZROBIONE (06.09.2026).** `compare` bez dwoch plikow konczy sie kodem **1** i komunikatem `BLAD: compare wymaga dwoch plikow` — przez wspolny handler, wiec ujednolicil sie nie tylko kod, ale i ksztalt wyjscia. Kod **2** zostal w **dwoch** miejscach, oba znacza „nie wiem, co uruchomic": galaz pustych argumentow i `Unknown()`. Bramka `tools/tests/test_runner_exit_codes.py` czyta `Program.cs` jako tekst i pilnuje obu kierunkow — ze `return 2` nie pojawi sie w trzecim miejscu ORAZ ze te dwa nie znikna. **Znalezisko wazniejsze od samego zadania**: przy kontroli negatywnej zestaw C# przeszedl **545/545 mimo obecnego bledu**, bo przepisujac komentarz nad testem wycialem razem z nim atrybut `[TestMethod]` — metoda zostala w pliku, miala asercje i **nie byla uruchamiana**. Objawem nie byl zaden FAIL, tylko liczba: 545 zamiast 546. Po naprawie mutacja wywraca dokladnie ten jeden test. Zestaw Pythona ma na to `assertion_gate` od #139; po stronie C# nie ma nic — dopisane do kolejki jako **6.B27**. Pomiar w `reports/kody-wyjscia-runnera.md`. Tresc pierwotna: **Ujednolicic kody wyjscia `Sim.Runner`: kazda odmowa argumentowa = 1** — `compare` przestaje byc wyjatkiem, a **2** zostaje wylacznie dla „nie wiem, co uruchomic" | **DECYZJA WLASCICIELA z 06.09.2026.** Cztery pozycje (6.A10, 6.A11, 6.A13, 6.D20) odmowily ruszenia tego bez niej i przybily stan testami. Teraz jest wybor, wiec testy przybijajace dwojke dla `compare` zmieniaja sie razem z kodem | M |
| 6.B27 | **ZROBIONE (06.09.2026).** Bramka czyta `tests/**/*.cs` jako TEKST, bez `dotnet`, i szuka jednego waskiego ksztaltu: publicznej metody `void`/`Task` bez argumentow, zadeklarowanej **bezposrednio** w klasie z `[TestClass]`. Pokrycie nazwane liczba: **708** atrybutow testowych w plikach, **668** objetych ksztaltem, **40** poza nim (`[DataTestMethod]` z argumentami) — luka jest wypisywana przy kazdym przebiegu, bo opisana samym komentarzem po roku nie ma rozmiaru; domkniecie dopisane jako 6.B28. Glebokosc liczona klamrami: pomocnik `Reset()` w zagniezdzonym przyrzadzie `RunResetTests` NIE jest brany za test i osobny test tego pilnuje. Kontrola negatywna WYKONANA na tym samym tescie, ktory stracil atrybut naprawde — bramka nazwala go **z imienia**: `RunnerCommandTests.Compare_bez_dwoch_plikow_konczy_sie_kodem_jeden`. Druga kontrola wstrzykiwana w katalogu tymczasowym. Pomiar w `reports/test-csharp-bez-atrybutu.md`. Tresc pierwotna: **Test C# bez `[TestMethod]` jest niewidzialny** — metoda zostaje w pliku, ma asercje, wyglada jak test i nie jest uruchamiana; jedynym sladem jest liczba testow, ktorej nikt nie pilnuje | znalezione przy 6.A16, **na moim wlasnym commicie**: zestaw przeszedl 545/545 mimo obecnego bledu, bo mutacja nie miala czego wywrocic. Zestaw Pythona ma `assertion_gate` od #139, C# nie ma nic | M |
| 6.B28 | **ZROBIONE (07.09.2026), i wpis mylil sie co do rozmiaru luki — pomiar to pokazal.** `[DataTestMethod]` jest **trzynaście**, nie czterdzieści; pozostałe **27** to zwyczajne `[TestMethod]` **bez** argumentów, czyli metody, które kształt bramki obejmował z definicji i których mimo to nie widziała. `tests/Sim.Tests/ServiceDayTests.cs` ma szesnaście metod testowych i bramka widziała z nich **zero**, `SignallingPlanTests.cs` z piętnastu — cztery; meldując przy tym „0 nieuruchamianych", bo nie miała czego zobaczyć. **Mechanizm**: liczenie klamr szło po surowym tekście, a pomocniki testów budują JSON — `return "}";` zbija licznik do zera w środku napisu, przejście uznaje ciało metody za skończone, prawdziwą klamrę bierze za koniec ciała klasy i przestaje szukać. Naprawia to `maska()` — kopia źródła z komentarzami i literałami zamienionymi na spacje **znak w znak**, więc indeksy zostają; obsłużone wszystkie cztery postacie napisu występujące w `tests/`. Po samej masce: 719 / **706** / 13, czyli zostało dokładnie tyle, ile jest `[DataTestMethod]`. **Rozszerzenie kształtu rozstrzygnięte pomiarem, nie wyborem z dwóch dróg wpisu**: publicznych metod `void`/`Task` z argumentami na bezpośrednim poziomie klasy `[TestClass]` jest 13 i **wszystkie** mają atrybut testowy, zero bez; metod z `[DataRow]` bez `[DataTestMethod]` zero. Obawa z 6.B27, że szerszy kształt łapałby pomocników, jest więc nieziszczona — pomocniki są tu `private`/`internal static` — a docstring modułu jest **przepisany**, nie uzupełniony. Wynik: **719 / 719 / 0**, luka zamknięta zerem, nie uzasadniona. **Sprostowanie trzech liczb, które sam opublikowałem**: 6.B27 (708/668/40), 6.D28 (674/674) i 6.D30 (676 i 676, różnica zero) szły przez ten sam zepsuty licznik; równość dwóch czytników z 6.D30 **była prawdziwa** i właśnie dlatego niczego nie złapała — dwa czytniki dzielące jedno zepsute przejście mylą się razem, a widzi to dopiero próg porównywalny z niezależnym licznikiem, tu z liczbą atrybutów w plikach. Progi podniesione w obu bramkach z przepisanym uzasadnieniem: `MINIMUM_WIDZIANYCH` 700 (poprzednio `> 100`) i `MINIMUM_METOD` 600 → 700 — stary przechodził, gdy czytnik gubił 27 z 719. Cztery WYKONANE kontrole negatywne; **KN-1 i KN-3 wywróciły się dopiero na drugiej wersji testu**, bo pierwsza używała pomocników wyrażeniowych i przechodziła także bez maski — test opisywał wtedy własną niewiedzę jako brak usterki, ta sama usterka co u czytnika asercji przy 6.D28. Treść literału surowego topiąca KN-3 jest **znaleziona pomiarem** (pięć kandydatów, dwa różnicują). Zestaw narzędzi 1828 → **1830**, C# **557** bez zmiany — i zero nowych zgłoszeń nieuruchamianych metod jest tu wynikiem, nie jego brakiem. Pomiar w `reports/ksztalt-bramki-testow-csharp.md`. Tresc pierwotna: **Czterdziesci metod `[DataTestMethod]` jest poza ksztaltem bramki z 6.B27** — maja argumenty (`[DataRow]`), wiec brakujacy atrybut w tej rodzinie nadal przeszedlby niezauwazony | zmierzone przy 6.B27: 708 atrybutow w plikach, 668 objetych, **40 poza**. Luka jest dzis wypisywana liczba przy kazdym przebiegu, ale nie jest zamknieta | M |
| 6.D23 | **ZROBIONE (06.09.2026).** `provenance.write_manifest_if_changed()` — JEDNA implementacja, oba fetchery ja wolaja. Dwa przebiegi z rzedu na niezmienionym zrodle: pierwszy `manifest utworzony`, drugi `manifest bez zmian: content_sha256 ten sam, plik nietkniety`, ta sama suma i **ten sam `mtime`** — rowny mtime jest tu wazniejszy od rownej sumy, bo zapis identycznych bajtow tez wyglada jak praca, ktorej nie bylo. Po zmianie tresci zrodla: `manifest zmieniony`, inna suma. `git status --short data/` puste. Kryterium jest **waskie celowo**: wylacznie `content_sha256`, nie caly `diff_manifests` — pytanie o inne pola wariant C dopiero otwiera i nalezy do wlasciciela; osobny test to przybija. `CLAUDE.md` §4.6 NIETKNIETY. Dwie WYKONANE kontrole negatywne, druga pilnuje wlasnie tej granicy. **Czego pomiar nie pokazal**: przebiegi uzyly syntetycznego archiwum i manifestu w katalogu tymczasowym, bo archiwum zrodlowe lezy poza repozytorium — na prawdziwym pliku z `data/` nie zostalo to wykonane i raport mowi to wprost. Pomiar w `reports/manifest-przy-zmianie-tresci.md`. Tresc pierwotna: **Wariant C: fetchery pisza manifest tylko przy zmianie tresci** — `provenance.diff_manifests()` istnieje i porownuje `content_sha256`, a `fetch_gtfs.py` i `fetch_stib_shapes.py` **go nie wolaja** | **DECYZJA WLASCICIELA z 06.09.2026** na warianty z `reports/zapisy-do-data.md` §3. Regula `CLAUDE.md` §4.6 zostaje NIETKNIETA — zmieniaja sie narzedzia, nie regula. Wariant E domyka przy tym `build_alignment.py` i `normalize_stops.py` bez zmiany ich kodu | M |
| 6.D24 | **Brakujaca biblioteka natywna runtime'u jako niezbadany mechanizm** — `libhostfxr.so` / `libcoreclr.so`, w odroznieniu od brakujacego assembly | znalezione przy 6.D21, ktore szescioma wykonanymi probami NIE odtworzylo zawieszenia i nazwalo ten mechanizm jako niezbadany, zamiast go domniemywac | S |
| 6.A17 | **ZROBIONE (07.09.2026).** Zmierzone **cztery** limity, nie dwa, bo dwa punkty nie ustalaja monotonicznosci: obciecie **506,3 / 338,6 / 210,2 / 96,9 MJ** przy 40 / 50 / 60 / 72 km/h — piecioktornie, monotonicznie. Przy 40 km/h obciecie (140,6 kWh) **przewyzsza cala prace trakcji** przejazdu przy 72 km/h. **Mechanizm z kodu, nie domysl**: predkosc przejscia sila->moc to 31,241 km/h, wiec kazdy z tych limitow lezy w obszarze STALEJ MOCY — trakcja na limicie daje `P/v`, a nizszy limit znaczy dwie rzeczy naraz, dluzszy czas na limicie ORAZ wieksza sile. Przewidywanie `(P - R(v)·v)·t` z oporami Davisa wzietymi z modelu, NIE dopasowanymi, zgadza sie **do +8,4 % i +3,6 %**, oba w te sama strone. **Per odcinek**: przy 72 km/h TRZY odcinki nie dochodza do limitu wcale i sa to **dokladnie trzy najkrotsze** (314,93 / 343,82 / 409,20 m), a przy 50 km/h dochodza wszystkie jedenascie; odcinek Schuman->Merode (1219 m) daje sam 37 % czasu na limicie. Test dopisany, bo zaleznosc JEST monotoniczna — na osi syntetycznej, bo kierunek wynika z rownania, nie z pliku w `data/`, plus para przybijajaca, ze czlon jest **dodatni i wiekszy od czlonu dyskretyzacji** (bez niej porzadek zachodzilby takze przy obcieciu zerowym). Kontrole negatywne pokazaly wiecej, niz mialy: wyzerowanie czlonu wywraca **takze dwa testy bilansu z 6.A5**, ktorych nie pisalem — czlon jest nosny, a bilans bez niego przestaje sie domykac. **Czego tabela NIE mowi**: wzrost pracy trakcji (+39,8 kWh) NIE jest rowny wzrostowi obciecia (+113,7 kWh) — kuszace „trakcja rosnie o tyle, ile obciecie" jest nieprawda i stoi w raporcie wypisane jako nieprawda. Pomiar w `reports/czlon-obciecia.md`. Tresc pierwotna: **Czlon obciecia w bilansie energii to 96,89 MJ i nikt go nie mierzy osobno** | znalezione przy 6.A6 (#323) | M |
| 6.A18 | **ZROBIONE (06.09.2026).** `budget` przyjmuje `--coast-from-m`, a naglowek `[BUDZET]` wypisuje nastawe z powrotem — bo sam kod 0 dowodzi tylko, ze opcja jest PRZYJMOWANA, i przeszedlby przy dopisaniu samej nazwy do tabeli. Dowodem, ze nastawa dochodzi do `LineCore`, jest pomiar trojstronny na jednym scenariuszu: `N_sr` **6.69** bez wybiegu, **6.67** przy 250 m, **6.40** przy 120 m, przy `czeka_sr` rosnacym 2.09 -> 2.11 -> 2.39. Kolumna `us/krok` tego NIE pokazuje (3.73-3.84 to szum), wiec gdyby dowodem miala byc ona, dowodu by nie bylo. **Zdanie pozycji bylo nieprawdziwe i pomiar to pokazal**: `LineRunSettings` buduja **dwa** polecenia, nie trzy — `replay` odtwarza ZAPIS WEJSC przez `TrainController`, wiec nastawa automatu nadpisywalaby wejscia z `--keys` i odtworzenie przestaloby byc odtworzeniem. Dzisiejsza odmowa `replay` jest przybita testem, a pytanie oddane do kolejki jako **6.A19**. Bramka 6.D2 przestala mowic o niemozliwosci: `coast_from_m` stoi w scenariuszu i stamtad biora go NARAZ wywolanie i zdanie w wypisie, wiec nie moga sie rozjechac; `null` zostaje, bo prog 8,0 us pochodzi z przejazdu bez wybiegu. Kontrola negatywna WYKONANA. **Znalezisko obok**: 84 z 89 modulow `tools/tests/` nie ma bloku `__main__`, wiec `python3 tools/tests/<modul>.py` konczy sie **kodem 0 przy zero wykonanych testach** — na tym wlasnie pierwsza probe kontroli negatywnej odczytalem jako „bramka nie zapala sie"; dopisane jako **6.D25**. Pomiar w `reports/wybieg-poza-poleceniem-line.md`. Tresc pierwotna: **`--coast-from-m` istnieje w `line`, nie istnieje w `budget` ani `replay`** | znalezione przy 6.A6 (#323), ktore swiadomie nie wyszlo poza `line`. Pomiar kosztu kroku przy wybiegu (6.D2) i odtworzenie przejazdu z wybiegiem (`replay`) sa dzis niewykonalne | S |
| 6.D25 | **ZROBIONE (07.09.2026).** `test_all.py` przyjmuje nazwe albo sciezke jednego modulu i **to jest jedyna roznica** miedzy przebiegiem jednego a calego zestawu — licznik asercji, werdykt, wypis i kod wyjscia sa ta sama droga, wiec przebieg pojedynczy nie moze byc lagodniejszy; odmowa przy zerze testow byla za darmo, bo `AG.suite_verdict` juz ja mial. Strazniki delegują do **jednego** przebiegacza, nie 91 kopii — wlasna petla po `globals()` istniala juz raz, w `test_reference_snapshot.py`, i miala DOKLADNIE te usterke: zero funkcji `test_` dawalo wypis „co do bitu" i kod 0. **Liczba z wiersza pierwotnego byla zla, bo zmierzylem ja grepem**: `grep -l '__main__'` dawal 5 trafien, a wykonywalnych straznikow bylo **2** — trzy pozostale to slowo `__main__` w prozie i w danych testowych `test_mutation_sweep.py`. Prawdziwa proporcja: **89 z 91**. Bramka czyta `ast` i ma na to osobny test. Uruchomienie wprost wyciagnelo **dwie usterki, ktorych nikt nie widzial**: `test_dimension_audit.py` wkladal `tools/blender`, a importowal `station_components` z `tools/track` — dzialal wylacznie na cudzym `sys.path` z `test_all.py`; oraz `test_gate_instrumented_this_suite_for_real` mierzyl `AG.sites() > 3000`, czyli miejsca ZALADOWANE w przebiegu, nie miejsca na drzewie — rozdzielony na dwie asercje, wyszedl z tego mocniejszy. Kryterium sprawdzone **petla po wszystkich 91**: zero problemow, a suma 3535 rozklada sie na 1745 + 45 = 1790, czyli przebiegi pojedyncze **dziela zestaw dokladnie**. **Jedna pozycja odwolana po zmierzeniu**: „inne moduly jada na cudzym `sys.path`" wygladalo na 5 przypadkow, po poprawieniu przyrzadu wyszlo **0** — trzeci raz tego samego wzorca w jednym dniu, liczba z przyrzadu patrzacego na tekst. Pomiar w `reports/modul-uruchomiony-wprost.md`. Tresc pierwotna: **`python3 tools/tests/<modul>.py` konczy sie kodem 0 przy zero wykonanych testach** | zmierzone przy 6.A18, na wlasnej kontroli negatywnej: bramka odczytana jako zielona nie zostala uruchomiona ani raz. Ten sam ksztalt usterki, ktory zestaw lapie u innych — `assertion_gate` od #139, `grep FAIL` slepy na blad importu od 6.D19 | M |
| 6.B25 | **ZROBIONE (06.09.2026).** Stala z `clearance.py` byla martwa **od pierwszego commita**, a nie „przestala byc czytana": `git log -S` daje wylacznie #50, ktory ja wprowadzil, i nic wiecej. Usunieta. Drugiego progu **nie przemianowano** — wpis kolejki proponowal nowa nazwe, a pomiar pokazal lepsze wyjscie: te trzy liczby byly **kopia** `validate.LIMITS` z komentarzem mowiacym, skad sa, i bez niczego, co pilnowaloby, zeby nadal stamtad byly. Kopia progu rozjezdza sie w JEDNA strone po cichu — os, ktora przestaje spelniac prawdziwy prog, przechodzi test, bo tutejszy zostal przy starej wartosci; przemianowanie zostawiloby te usterke pod ladniejsza nazwa. Teraz `VALIDATOR = V.LIMITS`, czytane po kluczu, wartosci nietkniete. Docstring powolywal sie na liczbe nie tylko martwa, ale **slabsza niz obowiazuje** (20 m zamiast 90 m) — przepisany, argument wychodzi z tego mocniejszy. **Pola „Skonczone, gdy" NIE nalezalo spelnic doslownie**: pomiar dal 5 nazw o roznych wartosciach i **cztery sa poprawne** (`SOURCE_ID`, `DEFAULT_SOURCE_ID`, `SOURCE_CRS` to tozsamosc modulu, `TOLERANCE_M` rozni sie tym, co mierzy), wiec regula „zadnych powtorzonych nazw" zapalilaby sie na czterech przypadkach zrobionych dobrze. Zamiast niej zapadka z uzasadnieniami, pilnowana w obie strony. **CZTERY kontrole negatywne, jedna z nich NIE zapala bramki i raport mowi to wprost**: sama martwa stala przywrocona nie tworzy kolizji, bo bramka lapie kolizje, nie martwote. Czy bramka na martwote jest wykonalna, zmierzone: 696 stalych, **jedna** nieczytana i uzasadniona (`LOCATION_STATION` z wyliczenia GTFS) — w kolejce jako **6.B29**. Pomiar w `reports/nazwa-zajeta-drugi-raz.md`. Tresc pierwotna: **`MIN_RADIUS_M` w `clearance.py` jest martwe, a nazwa zajeta drugi raz z INNA wartoscia** | znalezione przy 6.B5 (#324). Zmierzone: stala w `clearance.py` nie jest czytana przez zaden kod, a `test_clearance_profile.py` opisuje ja w docstringu jako obowiazujaca | S |
| 6.B29 | **ZROBIONE (07.09.2026).** `tools/tests/test_dead_constants.py` — **705** stalych modulowych w `tools/` i `src/`, **jedna** nieczytana nigdzie i uzasadniona (`LOCATION_STATION`), zero bez uzasadnienia. **Zasieg wybrany po zmierzeniu trzech, nie z gory**: proste 242, literalne 348, wszystkie 705 — liczba nieczytanych jest we wszystkich trzech **ta sama** (1), wiec zawezenie oddaloby zasieg, nie kupiloby czystosci; martwy slownik progow byl by dokladnie tym samym zdaniem o repozytorium. To domyka tez rozbieznosc w tym wpisie: 696 z pomiaru przy 6.B25 i 705 dzis to ta sama populacja na drzewie o dwa moduly wieksza, a 242 to jej podzbior o wartosciach prostych. Odczyt liczony przez `ast` (`Name` w `Load` ORAZ `Attribute`, bo stala jedzie jako `M.NAZWA`), a `*.sh` i `.github/` tekstem osobno, bo `vehicle_clearance.sh` i `station_details.sh` trzymaja pelne programy w `python3 -c` — stala czytana wylacznie stamtad NIE jest martwa. **CZTERY kontrole negatywne**, w tym martwy **slownik** (przy wezszym zasiegu przeszedl by w milczeniu) i **para** dla sciezki pozapythonowej: FAIL bez odczytu w `.sh`, zielono po jego dopisaniu — sam FAIL dowodzilby tylko, ze bramka cos zglasza. Dwie dalsze kontrole sa testami i chodza zawsze: przypisanie nie jest odczytem (inaczej kazda definicja czytalaby sie sama i bramka nie zglosilaby NIGDY niczego) oraz `M.NAZWA` jest odczytem. Pomiar w `reports/stala-ktorej-nikt-nie-czyta.md`. Tresc pierwotna: **Stala modulowa, ktorej nikt nie czyta, nie jest przez nic zglaszana** | zmierzone przy 6.B25: 696 stalych modulowych w `tools/` i `src/`, **jedna** nieczytana nigdzie (`LOCATION_STATION`, brakujacy element wyliczenia GTFS — wyjatek uzasadniony). Bramka jest wiec wykonalna dzis, z lista o jednym wpisie; kontrola negatywna KN-1 z 6.B25 pokazala, ze bramka na kolizje tego NIE lapie | S |
| 6.B26 | **Najciasniejszy luk pakietu D lezy na odcinku, ktorego OSM nie widzi jako tunel** — zapas +0,7043 m liczony jest wobec sciany, ktorej moze nie byc | znalezione przy 6.B5 (#324): 0,0-0,2 m od przedzialu bez tunelu, wobec >= 314 m na pozostalych pieciu osiach. Roznica jest o trzy rzedy wielkosci, wiec nie jest szumem pomiaru | M |
| 6.A20 | **ZROBIONE (07.09.2026), DWA pisarze z pieciu — i pole „Poza zakresem" tej pozycji przewidzialo dokladnie ten wynik.** `budget --out` i `service-day --out` niosa nastawy w wierszach `#` przed naglowkiem CSV; `diff` dwoch przebiegow roznionych jedna nastawa pokazuje teraz **ta nastawe**, nie tylko liczby. **Stan wyjsciowy byl gorszy, niz wygladal**: caly plik mial DWA wiersze, a w tej konkretnej parze przebieg Z wybiegiem wyszedl SZYBSZY (88 935 vs 77 237 krokow/s), bo przy krotkim oknie szum przewyzsza efekt nastawy — czytajacy wyciagnalby wniosek przeciwny do prawdziwego i nie mial czym tego sprawdzic. Trzech pisarzy odlozono, kazdego z INNEGO, zmierzonego powodu: `drive`/`replay` (Compare wymaga, by `left[0]` byl dokladnie `DriveTelemetry.Header`, a ten sam format pisze scena Godota), `line --calls` (godot-first-run.yml porownuje plik rdzenia z plikiem SCENY), `line --trace` (assert_line_trace.py liczy SHA-256 CALEGO pliku wobec wzorcow przybitych do rodziny runtime'u — a **tamta bramka wymaga**, zeby przeliczanie wzorcow stalo w commicie zmieniajacym wersje srodowiska, wiec dopisanie metadanych przeliczyloby je jako skutek uboczny, czyli zlamaloby cudza regule). Szosty pisarz, `axis --dump-points`, nie nalezy tu z innego powodu: zapisuje surowe punkty bez naglowka i bez pomiaru, a grep nie pokazuje ani jednego konsumenta. Bramka `test_csv_provenance.py` **nie** wymaga nastaw od kazdego — wymaga, zeby **zaden nie milczal bez powodu**. **Pierwsza wersja bramki sama sie zapalila i miala racje**: kluczowala po nazwie zmiennej, a `lines` i `rows` sa uzywane ponownie przez pisarzy o ROZNYCH formatach; klucz jest teraz metoda polecenia. Cztery kontrole negatywne, w tym **KN-4 na zamiane zadania w liste wymowek**: `budget` wyjety z `Provenance` i wpisany do listy powodow z wiarygodnie brzmiacym uzasadnieniem — kontrola pozytywna przybija zakres i to lapie. Pomiar w `reports/nastawy-w-pliku-nie-w-wypisie.md`. Tresc pierwotna: **Zaden CSV z `Sim.Runner` nie zapisuje nastaw, ktore go wyprodukowaly** | zmierzone 07.09.2026 przy 6.A18. Naglowek `[BUDZET]` mowi od tej pozycji o wybiegu, ale plik z `--out` nie: 13 kolumn liczb bez odstepu, nawrotu, limitu, ATP, obciazenia i wybiegu. CSV jest artefaktem, ktory PRZEZYWA proces i trafia do raportow | M |
| 6.A21 | **Trzy pisarze CSV, ktorych format jest przybity z zewnatrz, nadal nie niosa nastaw** — `drive`/`replay`, `line --calls`, `line --trace` | zmierzone 07.09.2026 przy 6.A20, ktore swiadomie nie weszlo w te trzy i wypisalo powod kazdego osobno. Kazdy wymaga zmiany po DRUGIEJ stronie porownania: sceny Godota (dwa pierwsze) albo przeliczenia wzorcow SHA-256 w commicie zmieniajacym wersje srodowiska (trzeci). Bramka `test_csv_provenance.py` trzyma te trzy powody z nazwami, wiec zniesienie ktoregokolwiek jest widoczne, nie ciche | M |
| 6.A22 | **ZROBIONE (07.09.2026).** `line --limit-kmh=72` kończy się dziś komunikatem `BŁĄD: polecenie line nie przyjmuje postaci --opcja=wartość. Opcję --limit-kmh zna — podaj ją jako dwa człony: --limit-kmh 72`, a nie zdaniem sprzecznym z tabelą, którą sam wypisuje. **Droga wybrana pomiarem, nie z góry**, tak jak żądało pole „Wyjście": wystąpienia postaci `--opcja=` policzone po sklejeniu kontynuacji wierszy i sklasyfikowane po wołanym programie — **344** razem, z tego **96** w komendach SCENY Godota i **2** w komendach `Sim.Runner`, przy czym oba te dwa są tekstem TEJ pozycji w `docs/TASKS.md`. Ani jedna prawdziwa komenda runnera nie używa równości, więc druga droga (odrzucenie z komunikatem o POSTACI) wystarcza i nie zmienia niczego, co dziś działa. **Sprostowanie liczby, którą sam wpisałem godzinę wcześniej**: pierwsza wersja komentarza mówiła „wszystkie 40 wystąpień `--limit-kmh=` należy do sceny" — 40 było liczbą WIERSZY z `grep -c`, nie wystąpień, i nie było sklasyfikowane; klasyfikacja daje 70 wystąpień, z czego do sceny należy 11. Wniosek się nie zmienił, liczba go uzasadniająca była zła. **Sedno rzeczy jest w tym, że `--limit-kmh=70` nie jest tu literówką**: tak woła się scenę Godota (`$GODOT_BIN --path src/Game -- --line --limit-kmh=70`), której `RunPlan` tej postaci WYMAGA, przybite 27 testami w `tests/Game.Tests`. Czytający przychodzi do runnera z drugiej połowy tego samego projektu i pisze to, co tam działa. **Dwa znaleziska własnego sondowania, oba naprawione**: pierwsza wersja komunikatu radziła FLADZE „podaj jako dwa człony: --atp 1", co jest nieprawdą — flaga wartości nie bierze, a `1` zostałoby członem pozycyjnym, którego odmowa nie widzi, czyli rada mówiąca nieprawdę zamiast komunikatu mówiącego nieprawdę; oraz `Program.cs` sam wypisywał `replay --limit-kmh=-5 nie jest dodatnią prędkością`, czyli radził postać, którą od tej pozycji odrzuca — pilnuje tego teraz bramka `test_no_message_writes_a_known_option_in_the_equals_form`, chodząca po wszystkich nazwach z `KnownOptions` w kodzie BEZ komentarzy. Treść odmowy nieznanej opcji ma jednego pisarza (`Nieznana`), choć wołają ją dwa miejsca. Pięć WYKONANYCH kontroli negatywnych; **KN-2 mówi coś o obu rodzajach kontroli**: zlanie gałęzi flagi z gałęzią wartości przeszło bramkę Pythona 8/8, bo oba literały wciąż stały w pliku, tylko jeden był nieosiągalny — wywrócił to dopiero test C# uruchamiający `Program.Main`, i to jest argument, dla którego OBIE istnieją, nie wada bramki. **KN-4 mierzy wartość kontroli drugiego kierunku** z pola „Skończone, gdy": bez testu na literówkę odmowa zdjęta w całości przeszłaby wszystkie testy tej pozycji. `dotnet test` 565 → **570**, zestaw narzędzi 1838 → **1841**. Pomiar w `reports/postac-z-rownosciem.md`. Poza zakresem, zgodnie z polem: przepisanie wiersza poleceń na bibliotekę do rozbioru argumentów; nietknięta została też konwencja sceny — ujednolicenie dwóch połów projektu jest decyzją właściciela, nie skutkiem ubocznym poprawki komunikatu. Tresc pierwotna: **Odmowa mowi, ze runner nie zna opcji, ktora zna** — `line --limit-kmh=72` konczy sie `BLAD: polecenie line nie zna opcji --limit-kmh=72` | zmierzone 07.09.2026 przy sondowaniu wiersza polecen: postac `--opcja=wartosc` nie jest obslugiwana i wpada w odmowe z 6.A11, ktora — poprawnie dla literowki — jest tu **mylaca**, bo `--limit-kmh` jest w tabeli `KnownOptions`. Czytajacy dostaje zdanie sprzeczne z faktem | S |
| 6.A23 | **ZROBIONE (07.09.2026).** `line --limit-kmh 72 --limit-kmh 50` kończy się dziś **kodem 1** i komunikatem `polecenie line dostało opcję --limit-kmh więcej niż raz. Wygrałaby pierwsza wartość, a pozostałe zniknęłyby bez słowa — podaj ją dokładnie raz`, w **obu** kolejnościach. Stan wyjściowy zmierzony wprost: dwa przebiegi różniły się o **81 sekund i 9760 kroków** (820,42 s / 101 872 kroki wobec 901,76 s / 111 632), bo jeden jechał 72 km/h, a drugi 50 — i oba kończyły się kodem 0 bez ani jednego zdania o tym, że komenda podawała dwie wartości. **Kierunek wybrany pomiarem, nie z góry**, tak jak żądało pole „Wyjście": powtórzeń policzonych po sklejeniu kontynuacji wierszy jest **cztery** i **ani jedno nie jest prawdziwą komendą** — trzy to proza raportu i wierszy tabeli (licznik widzi nazwy opcji w tekście zdania), czwarte to komenda z pola „Weryfikacja" tej pozycji; `--no-build` w pierwszym stoi PRZED separatorem `--`, czyli jest flagą `dotnet run` i do `args` nie dochodzi, ta sama pułapka co `-c Release` przy 6.A15. Zero prawdziwych powtórzeń, więc odmowa jest wolna i spójna z 6.A16 („każda odmowa argumentowa = 1"). **FLAG to nie dotyczy** i jest to pole „Poza zakresem", nie przeoczenie: `--atp --atp` znaczy to samo, co `--atp`, więc nie ginie żadna wartość — przybite testem, żeby przesunięcie tej granicy było widoczne, a nie ciche, i pilnowane z drugiej strony bramką, która żąda, by zbiór widzianych opcji był dotykany w JEDNYM miejscu i żeby gałąź flagi go nie widziała. **Przejazd nietknięty, z dowodem bajtowym, nie z zapewnienia**: plik `--trace` zbudowany przed zmianą i po niej ma tę samą sumę SHA-256 i `cmp` mówi „identyczne co do bajtu" na 101 873 wierszach. Trzy WYKONANE kontrole negatywne; **KN-2 mierzy dokładnie granicę z pola „Poza zakresem"** (flaga wciągnięta do zbioru robi z `--atp --atp` odmowę, czyli pozycja zrobiłaby o krok więcej, niż jej zlecono), a **KN-3 mierzy wartość kontroli pozytywnej** — odwrócony warunek robi odmowę z każdej komendy podającej choć jedną opcję i wywraca sześć testów, w tym `Opcja_podana_raz_nadal_przechodzi`. `dotnet test` 565 → **569**, zestaw narzędzi 1841 → **1842**. Pomiar w `reports/powtorzona-opcja.md`. Poza zakresem, zgodnie z polem: konflikty między opcjami RÓŻNYMI (opisane przy #246) i flagi. Nie zmieniono też `Option` ani `Provenance` — poprawka siedzi w jednym miejscu, w odmowie, która i tak przechodzi po wszystkich członach. Tresc pierwotna: **Powtorzona opcja jest przyjmowana w milczeniu, wygrywa PIERWSZA** — `--limit-kmh 72 --limit-kmh 50` jedzie 72, odwrotna kolejnosc jedzie 50, kod 0 w obu | zmierzone 07.09.2026. Wypis `[LINIA]` i `[ZALOZENIE]` podaja wartosc skuteczna, wiec nie jest niewidoczna — ale **nic nie mowi, ze druga zostala odrzucona**. Od 6.A20 nastawy trafiaja tez do plikow `--out`, wiec czytajacy CSV nie ma jak zobaczyc, ze wiersz polecen mial konflikt | S |
| 6.A24 | **ZROBIONE (07.09.2026).** Zepsuta komórka kończy się dziś komunikatem `build/d2.csv: wiersz 3 (nagłówek to wiersz 0), kolumna 1 „step” — „abc” nie jest liczbą`, a nie zdaniem platformy .NET bez pliku, wiersza i kolumny. **„Nietknięta" nie znaczyło „dobra"**: usprawiedliwienie z 6.A14 („zła komórka nie jest złą opcją") było prawdziwe i nadal jest, ale nie wynikało z niego prawo do komunikatu platformy — wynikał z niego tylko **inny nagłówek**. Komunikat nazywa plik **zepsuty**, nie pierwszy z wiersza poleceń (osobny test i KN-2), numer i nazwa kolumny idą z pozycji w wierszu (osobny test i KN-3), a **konwencja numeru wiersza jest powiedziana w nawiasie**, nie zostawiona do zgadnięcia — ten sam indeks, którym liczą dwie sąsiednie odmowy tej pętli. **Bramka z 6.A14 zażądała czterech rzeczy i każda była słuszna**: (a) lista usprawiedliwień opustoszała i wpis został zdjęty (kontrola w obie strony zrobiła dokładnie to, po co powstała); (b) próg liczby miejsc rozbioru **zszedł z 6 na 5** — jedyna zapadka w tym repozytorium, która kiedykolwiek zeszła w dół, więc jej komentarz nosi powód: dwa gołe `Parse` zamieniły się w jeden pomocnik z `TryParse`, a gołe `Parse` zniknęły z `Program.cs` **całkiem**, co pilnuje osobny test; (c) test listy usprawiedliwień **przechodził bez ani jednej asercji**, gdy lista opustoszała — złapał to `assertion_gate` (#139), a test jest przepisany na asercję bezwarunkową żądającą równości zbiorów; (d) zdanie „«x» nie jest liczbą" miało dwóch pisarzy, więc końcówka jest wydzielona do `NieJestLiczba` — nagłówek musi być inny, zdanie jest jedno (zasada z 6.A20 i 6.A22). Licznik pisarzy dostał przy tym `_kod_bez_komentarzy`, bo docstring WYJAŚNIAJĄCY treść widziany był jako drugi pisarz. Pięć WYKONANYCH kontroli negatywnych; **KN-2 pokazuje to samo, co KN-2 przy 6.A22** — bramka czytająca tekst widzi kształt, nie zachowanie, i wywraca to dopiero test uruchamiający `Program.Main` — a **KN-5** pilnuje progu w drugą stronę: zapadka wyższa od stanu faktycznego pada od razu, więc nie da się jej zostawić na zapas. `dotnet test` 574 → **578**; liczba testów Pythona **bez zmiany** (1852), bo ta pozycja żadnego nie dopisuje, tylko przepisuje trzy istniejące. Pomiar w `reports/komorka-csv.md`. Poza zakresem, zgodnie z polem: rozbiór nagłówka i tolerancja na brakującą kolumnę — obie mają własne odmowy w tej samej pętli. Zauważone i nietknięte: te dwie sąsiednie odmowy wracają `return 1`, a nie wyjątkiem, więc nie dostają przedrostka `BŁĄD:` — inaczej niż wszystko, co ujednoliciła 6.A16. Tresc pierwotna: **`compare` na nieliczbowej komorce CSV daje komunikat platformy, bez pliku, wiersza i kolumny** — `double.Parse(a[c], Inv)` w petli po kolumnach | zmierzone 07.09.2026 przy 6.A14, ktore swiadomie tego nie ruszylo i wpisalo jako jedyne usprawiedliwienie w `test_runner_number_parsing.py`: zla komorka nie jest zla opcja, wiec komunikat 6.A14 bylby tu nieprawda. Ale `compare` jest **wyrocznia parzystosci** rdzenia i sceny; jego odmowa ma nazwac plik, wiersz i kolumne, a nie sam napis | S |
| 6.A25 | **ZROBIONE (07.09.2026).** Człon pozycyjny ponad liczbę, jaką polecenie czyta, jest **odmową**: `budget … --atp 1` i `budget … zmyslony_czlon` kończą się kodem **1** i nazywają człon, a nie kodem 0 z wypisem nieodróżnialnym od `budget … --atp`. Liczba stoi jako trzecie pole `KnownOptions` (`Positional`), i to jest **pomiar, nie decyzja z góry** — pole „Wyjście" żądało rozstrzygnięcia, ile poleceń bierze dziś choć jeden człon pozycyjny, bo od tego zależało, czy wystarcza jedna liczba, czy trzeba nowego rozbioru. Przejście po `Program.cs` bez komentarzy, najwyższy indeks `args[N]` dla N ≥ 1 w ciele każdego polecenia, daje `{'compare': 2}` i **zera wszędzie indziej** — jedno polecenie, dwa człony, więc jedna liczba wystarcza. Bramka pythonowa wyprowadza tę liczbę **drugi raz** z odczytów `args[N]` i porównuje z tabelą; ten sam układ, który od 6.A11 pilnuje samych nazw, z tego samego powodu — ręcznie wypisana liczba starzeje się po cichu. Czytnik jest **osobny** od `declared_table` celowo: tamten szuka `new[] {…}` albo `Array.Empty<string>()`, liczby by nie zobaczył, a doklejenie trzeciego pola zmusiłoby go do zwracania trójki wszędzie, gdzie dziś zwraca parę. Trzy WYKONANE kontrole negatywne: **KN-1** (liczba `compare` zdjęta, 2 → 0) wywraca **pięć** testów C#, z czego **trzy starsze od tej pozycji** (6.A24) — dokładnie tego żądało pole „Skończone, gdy", i dowodzi, że liczba jest nośna, nie dokumentacyjna; **KN-2** (odmowa z własną stałą `command == "compare" ? 2 : 0` zamiast odczytu z tabeli) zostawia **wszystkie 584 testy C# zielone** i zapala wyłącznie kontrolę przyrządu — to jest usterka 6.D30 przyłapana na gorąco, dlatego ta kontrola stoi w zestawie na stałe; **KN-3** (sama odmowa zdjęta, licznik zostaje) wywraca dokładnie trzy odmowy, a testy drugiego kierunku zostają zielone. Po drodze **jeden mój test padł i to był dobry pomiar**: pierwsza wersja żądała kodu 0 dla `line … --coast-from-m -1`, a dostała kod 1 z `Początek wybiegu musi być skończone i nieujemne` — odmowa **z dziedziny**, nie z rozbioru; test mierzył zakres wartości opcji, nie to, co ta pozycja zmienia, więc jest przepisany na właściwą rzecz (wartość ujemna DOCHODZI do dziedziny). Testy C# 578 → **584**, `test_runner_options.py` 9 → **12**. Pomiar w `reports/czlon-pozycyjny.md`. Poza zakresem, zgodnie z polem: biblioteka do rozbioru argumentów; nie tknięto też odmowy `compare wymaga dwóch plików` — brak drugiej ścieżki to brak, nie nadmiar, i są to dwie różne odmowy dwóch różnych rzeczy. Zauważone, nie tknięte: **test `Zepsuta_komorka_nazywa_zepsuty_plik_a_nie_pierwszy` przechodzi w KN-1 z całkiem innego powodu, niż sądzi** — wszystkie trzy jego asercje spełnia komunikat o członie pozycyjnym, bo sprawdzają tylko, czy w treści stoi pierwsza ścieżka; właściwą poprawką jest asercja na `wiersz`/`kolumna` z 6.A24. Tresc pierwotna: **Czlon pozycyjny nieznany zadnemu poleceniu przechodzi w milczeniu, kodem 0** — `budget … --atp 1` i `budget … zmyslony_czlon` konczyly sie kodem 0, a odmowa z 6.A11 i 6.A15 odsiewa czlony bez minusa celowo, bo `compare` bierze dwie sciezki pozycyjnie | zmierzone 07.09.2026 przy 6.A22, ktore swiadomie tego nie tknelo i wypisalo powod w §11 raportu | S |
| 6.B32 | **ZROBIONE (07.09.2026).** Wpis dziennika niesie **odcisk treści** pliku, z którego policzono mutacje, a wznowienie z dziennika policzonego na innej treści **odmawia kodem 2** — przy tym samym commicie. Wykonane oba przebiegi z pola „Weryfikacja": pierwszy na czystym drzewie kończy się `rozstrzygniętych 2/2, zabitych 2` i kodem 0, wpis niesie `'odcisk': 'fcb923b7000e0dca'`; po zmianie jednego znaku BEZ commita `git rev-parse --short HEAD` daje dalej `8b1f98a`, a odcisk `3080aab246047056`, i drugi przebieg wypisuje `PRZERWANE — … 2 wpisow policzonych na INNEJ TRESCI pliku …    tools/blender/lod_paths.py (dziennik fcb923b7000e0dca, drzewo 3080aab246047056)` z kodem **2**; wznowienie na drzewie NIEZMIENIONYM nadal działa (`2 z 2 już policzonych`). **Pomiar, o który prosiło pole „Wyjście", i on wybrał drogę**: SHA-256 raz na każdą z **2346** mutacji pełnego przeglądu kosztuje **0,045 s** (63 moduły, 782 261 B), a `git status --porcelain` raz na przebieg 0,015 s — przy przebiegu 534–600 s (liczba z 6.B36) dokładna opcja to **0,008 %**, więc nie ma powodu brać tańszej, która mówi tylko „drzewo brudne", a nie CO w nim jest. Odcisk liczony raz na PLIK, nie raz na mutację; 16 znaków szesnastkowych, bo 64 bity przy 2346 mutacjach dają kolizję rzędu 10⁻¹⁴, a wiersz dziennika zostaje czytelny. **Rzecz, na której ta poprawka mogła być zbudowana źle, i dlatego ma własny test**: odcisk MUSI być liczony z **drzewa roboczego**, bo `collect` liczy mutacje z drzewa roboczego, a `check_one` stosuje je na kopii `git worktree add --detach HEAD` — te dwa źródła są tym samym plikiem tylko dopóki drzewo jest czyste, więc odcisk liczony w `check_one` miałby dokładnie wartość commita i byłby ŚLEPY na przypadek, dla którego powstał. Wpis BEZ pola `odcisk` liczy się jako obcy — ta sama zasada, którą 6.B19 postawiła dla wpisu bez pola `commit`. Dwie WYKONANE kontrole negatywne: **KN-1** (odmowa zdjęta) wywraca **dokładnie dwa nowe testy**, a odmowa z 6.B19 zostaje zielona — tego żądało pole „Skończone, gdy" wprost — i pokazuje samą usterkę, bo narzędzie wypisuje wtedy `0 z 2 już policzonych`, czyli podstawia cudzy wynik bez słowa; **KN-2** (odcisk z `HEAD` zamiast z drzewa roboczego) wywraca dokładnie ten jeden test, który to pilnuje — kontrola na moją własną możliwą pomyłkę, bo bez niego wszystkie pozostałe testy byłyby zielone przy bezwartościowej poprawce. **Po drodze padł test 6.B19 i to był dobry pomiar**: pomocnik `_dziennik_z_wpisem` budował wpis bez pola `odcisk`, więc `test_resume_still_works_when_the_journal_is_from_the_same_tree` zaczął wywracać się na odmowie o TREŚCI, choć mierzy zgodność COMMITA; pomocnik dostał pole z domyślną wartością **prawdziwą, nie stałą**, a wartownik `_BRAK` odróżnia „nie podano" od „wpis bez tego pola". **Trzecia kontrola dotyczy znaleziska na WŁASNEJ poprawce**: odmowa odcisków stoi w `main` PRZED `dirty_sources` (bo musi działać także dla `--list`), więc przy brudnym drzewie BEZ `--dirty` czytający dostawał komunikat o DZIENNIKU, choć prawdziwym problemem była jego niezacommitowana zmiana — a jaśniejszy komunikat `dirty_sources` nie dochodził do głosu wcale. Przestawienie kolejności zdjęłoby odmowę z drogi `--list`, czyli z jedynej taniej drogi, która ją sprawdza; komunikat NAZYWA więc drugą przyczynę, i tylko wtedy, gdy ona zachodzi — z `--dirty` zdania nie ma, bo przebieg jest zamierzony. **KN-3** (zdanie dopisywane zawsze) wywraca dokładnie ten test. `test_mutation_sweep.py` 72 → **78**, zestaw `1885/1885, RAZEM 69.635 s, 99 modułów`, kod 0. Pomiar w `reports/odcisk-tresci-dziennika.md`. Poza zakresem, zgodnie z polem: schemat identyfikatora mutacji. Nie dodano progu czasowego na koszt odcisku — próg na 0,045 s byłby progiem na szumie; przybity jest KSZTAŁT (`odciski_przebiegu` zwraca słownik po plikach i jest wołane raz), bo to da się zmierzyć bez zegara. Zauważone, nie tknięte: **wznowienie, w którym wszystko jest już policzone, kończy się kodem 1** (`brak mutacji do sprawdzenia po odfiltrowaniu nieosiągalnych`) — dla skryptu CI uruchamiającego przegląd w pętli do skutku jest to różnica między „gotowe" i „awaria"; zachowanie starsze od tej pozycji i innej klasy. Tresc pierwotna: **Dziennik mutacyjny nie odroznia dwoch przebiegow na TYM SAMYM commicie** — przy `--dirty` commit sie nie zmienia, a tresc mutowanego pliku owszem, wiec odmowa z 6.B19 tego nie widzi | nazwane wprost przy 6.B19 (#349) jako to, czego tamta poprawka NIE lapie | S |
| 6.D31 | **ZROBIONE (07.09.2026).** Wszystkie trzy metody (c) z 6.D29 mają dziś asercję wykonywaną **bezwarunkowo** — licznik wejść do gałęzi porównany ze zmierzoną liczbą. **Każda liczba jest ZMIERZONA, nie policzona z kodu**, tak jak żądało pole „Wyjście" („licznik przybity do złej liczby jest kolejną wyrocznią zepsutą w dobrą stronę"): wpisałem `999`, uruchomiłem test i odczytałem prawdziwą wartość z komunikatu `Assert.AreEqual failed`. `EveryKnownArgumentIsAcceptedOnItsOwnOrNamesWhatItNeeds` — **17** argumentów bez zależności, **3** z zależnością, suma równa `RunPlan.KnownArguments.Length`, więc argument dopisany bez odwiedzenia przez pętlę też jest FAIL-em, nie tylko usunięty. `Predkosc_dopuszczalna_jest_odwrotnoscia_krzywej_z_T_311` — podział pięciu odległości to **2** przy limicie planu (10, 50 m) i **3** poniżej (120, 300, 700 m); druga gałąź jest tym, o czym test mówi w nazwie, więc jej ciche zniknięcie byłoby zniknięciem sensu testu. **`NoInputThrows` dało znalezisko, którego nie było w planie**: licznik odrzuconych miał wyjść 9 na dziewięć paskudnych wejść, a wyszedł **8** — `--telemetry=` z **pustą ścieżką przechodzi jako plan POPRAWNY**, bo wartość tej opcji jest napisem i pustka nie wywraca żadnego rozbioru; scena pojechałaby z pustą ścieżką pliku telemetrii. Nie poprawiam tego tutaj (to zmiana zachowania sceny, nie wzmocnienie testu), ale fakt jest **przybity z imienia** przez `CollectionAssert.AreEqual(new[] { "--telemetry=" }, przyjete)`, więc ani nie zniknie po cichu, ani nie będzie wyglądał na przeoczenie — a poprawka zażąda zmiany tej listy razem z sobą. Cztery WYKONANE kontrole negatywne, i **KN-3 oraz KN-3b są OBIE, bo mierzą różne rzeczy**: KN-3 (`PermittedSpeedMps` zawsze `double.MaxValue`) wywraca test przez **własną asercję pierwszej gałęzi**, nie przez nowy licznik — mutacja jest tak gruba, że łamie sam warunek; dowodu, że licznik jest podłączony do właściwej gałęzi, dostarcza dopiero KN-3b (liczniki przestawione miejscami), który zmienia TYLKO liczby. Bez KN-3b zapisałbym „kontrola wykonana" o kontroli, która nie sprawdziła tego, co miała. **Liczby testów C# bez zmiany** (578 + 205 = 783) i to jest zamierzone — liczniki mieszkają wewnątrz trzech istniejących testów, a pole „Skończone, gdy" żądało, żeby liczba nie spadła. Pomiar w `reports/galaz-bez-straznika.md`. Poza zakresem, zgodnie z polem: bramka na ten wzorzec (6.D29 zmierzyła, że zapaliłaby się na 15 z 18 przypadków poprawnych) i pozostałe 15 metod. Tresc pierwotna: **Trzy metody testowe C#, ktorych asercje stoja w galezi, do ktorej nic nie musi wejsc** — `RunPlanTests.EveryKnownArgumentIsAcceptedOnItsOwnOrNamesWhatItNeeds`, `RunPlanTests.NoInputThrows`, `TrainProtectionTests.Predkosc_dopuszczalna_jest_odwrotnoscia_krzywej_z_T_311` | zmierzone i sklasyfikowane przy 6.D29 (#352), ktore swiadomie NIE zmienialo tresci zadnej z nich: 18 metod „interesujacych", z tego 14 (a) zawsze wchodzone, 1 (b) pilnowana osobnym testem i te 3 (c). W kazdej galaz zalezy od danych produkcyjnych albo od modelu, a nic w zestawie nie pilnuje, ze kiedykolwiek wejdzie. Sprawdzone przeze mnie osobno na `NoInputThrows`: wszystkie asercje poza `IsNotNull` stoja w `if (!plan.IsValid)` | M |
| 6.B33 | **ZROBIONE (07.09.2026).** `tools/tests/test_expected_exception.py` (7 testów) czyta `tests/**/*.cs` jako tekst i pilnuje jednego: metoda z `catch` **pochłaniającym** wyjątek musi mieć asercję **za** całym blokiem `try`/`catch`. Stan wyjściowy czysty — **12** wystąpień wzorca, **zero** usterek — i to jest cała treść pozycji: nic tego nie pilnowało, a trzynasta bez `Assert.Fail` przechodziłaby w milczeniu za każdym razem, gdy kod przestanie rzucać. **Zakres wyłączeń zmierzony, nie założony**: `try` w metodach testowych jest **22**, z tego **10** to `try`/`finally` BEZ `catch` (sprzątanie plików tymczasowych) — tam wyjątek nie ginie, leci dalej i wywala test głośno, więc żądanie od nich `Assert.Fail` byłoby bramką zapalającą się na poprawnym kodzie; `catch` z `throw;` też nie jest tym wzorcem. Oba wyłączenia mają swój test na wstrzykniętym wejściu. **Pierwszy detektor szukał `Assert.Fail` WEWNĄTRZ `try` i zgłosił wszystkie dwanaście jako usterkę — zero z nich nią było**; wyszło to z przeczytania dwóch metod z listy przed opublikowaniem liczby, a KN-2 odtwarza tę pomyłkę jako WYKONANĄ kontrolę, więc pułapka nie jest opisana z pamięci. **Najważniejsze znalezisko wyszło z kontroli negatywnej na własnej bramce**: KN-1 podmienił prawdziwe `Assert.Fail(...)` na komentarz `// KN-1: Assert.Fail zdjety` i bramka **została zielona 6/6**, bo szukała podciągu w surowym tekście. Bramka postawiona po to, żeby żaden test nie przechodził w milczeniu, sama przepuszczała test, któremu zdjęto wyrocznię, jeśli zdjęcie zostawiło komentarz — a ten projekt zdejmując coś zwykle komentarz zostawia (reguła „przepisuj, nie dopisuj obok"). Poprawka: `Assert.Fail` szukane na **masce** z 6.B28, plus test na dokładnie ten przypadek; po niej KN-1 wywraca bramkę w OBU wariantach (zakomentowane i usunięte). To ta sama usterka, którą opisuje **6.B34** dla bramki martwych stałych — tam daje fałszywy negatyw w liczniku odczytów, tu dawała go w liczniku wyroczni. Pięć WYKONANYCH kontroli negatywnych; **KN-3** (literówka `catchh` we wzorcu) pokazuje, po co jest próg **12**: przy „zero usterek" jako stanie oczekiwanym próg jest jedyną rzeczą odróżniającą bramkę działającą od milczącej. Zestaw narzędzi 1844 → **1851**, modułów 98 → **99**; zestawy C# nietknięte — ta pozycja żadnego testu C# nie dopisuje ani nie zmienia, tylko go czyta. Pomiar w `reports/oczekiwany-wyjatek.md`. Poza zakresem, zgodnie z polem: przepisanie dwunastu testów na `Assert.ThrowsException` — wszystkie są dziś poprawne, więc byłaby to zmiana kształtu poprawnego kodu, nie strażnik. Tresc pierwotna: **Nic nie pilnuje wzorca „oczekiwany wyjatek" w testach C#** — `try { … } catch (E) { asercja; return; } Assert.Fail(…)` dziala tylko dlatego, ze `Assert.Fail` stoi ZA blokiem `try`/`catch`; bez niego test przechodzi, gdy wyjatek nie zostal rzucony | zmierzone 07.09.2026 przy 6.A23: dwanascie metod testowych uzywa tego wzorca i **wszystkie dwanascie** maja `Assert.Fail` na wlasciwym miejscu. Nic tego nie pilnuje, a trzynasta bez niego przeszlaby w milczeniu — dokladnie klasa 6.B27, gdzie objawem byla wylacznie liczba | M |
| 6.B34 | **ZROBIONE (07.09.2026).** `martwe()` liczy odczyty na **masce** (`CTM.maska` z 6.B28), więc wzmianka o stałej w komentarzu albo w literale napisowym nie jest już jej odczytem. **Zmierzony skutek na drzewie: ZERO** — martwych stałych jest zero i przed maską, i po niej (233 deklaracje, 193 różnych nazw), więc wartość tej poprawki jest wyłącznie zapobiegawcza i dowodzi jej kontrola dodatnia na wstrzykniętym wejściu, nie zmiana liczby; powiedziane wprost, żeby nikt nie czytał „zero martwych" jako zasługi tej pozycji. **To nie było przeoczenie 6.B31, a jej świadomy wybór, który się przeżył**: tamten raport mówi, że fałszywy negatyw był tańszy niż bramka zapalająca się na poprawnym kodzie, bo odróżnienie wywołania od wzmianki wymagało wtedy własnego rozbioru literałów — a od 6.B28 `maska()` już istnieje. To trzecie miejsce, gdzie ta jedna funkcja załatwia inny problem: przejście po ciele klasy (6.B28), `Assert.Fail` wobec wzmianki (6.B33) i tutaj. **Szczególnie kłopotliwy przypadek zamknięty**: komentarz WYJAŚNIAJĄCY usunięcie stałej utrzymywał ją w stanie „żywa" na zawsze, a ten projekt takie komentarze pisze regularnie. **Koszt zmierzony osobno, bo przy tej bramce raz już nie mieścił się** (pierwsza wersja 6.B31 kosztowała 20,7 s): przejście liczące odczyty 0,118 s bez maski i 0,565 s z maską, po trzy przebiegi, na 124 plikach `.cs` i 1 615 998 znakach — **+0,45 s**, moduł w zestawie 1,406 s, czyli 0,6 % zestawu. Dwie WYKONANE kontrole negatywne, po jednej na każdy kierunek: KN-1 (maska zdjęta) wywraca oba testy wzmianki, a **KN-2 (maska ZBYT SZEROKA — całe źródło na spacje) jest równie ważny**, bo bez `test_a_real_read_still_counts` pozostałe testy byłyby zielone także dla maski zdejmującej za dużo, a taka bramka zgłasza jako martwe stałe czytane i zostaje wyłączona; drugi FAIL w KN-2 pokazuje rozmiar tej pomyłki liczbą — nie jedna nazwa, a dziesiątki. Zestaw narzędzi 1844 → **1847** (trzy testy w istniejącym module), lista `UZASADNIONE` zostaje **pusta**. Pomiar w `reports/maska-martwych-stalych.md`. Poza zakresem, zgodnie z polem: odczyty poza C# (`.tscn`, `.gd`, `*.sh`, `.github/`) — maska jest pisana dla składni C#, a w skrypcie powłoki `#` jest komentarzem, którego nie zna, więc byłaby tam zmianą znaczenia, nie poprawką. Tresc pierwotna: **Bramka martwych stalych C# liczy wzmianke w NAPISIE i w KOMENTARZU jako odczyt** — stala wymieniona wylacznie w komentarzu wyjasniajacym jej usuniecie wyglada na ZYWA | zmierzone 07.09.2026 na wstrzyknietym wejsciu: `_odczyty` daje 1 dla stalej stojacej tylko w napisie ORAZ dla stojacej tylko w komentarzu. 6.B31 wybralo ten kierunek pomylki SWIADOMIE (falszywy negatyw jest tansza pomylka), ale od 6.B28 (#348) istnieje `maska()`, ktora zdejmuje ten koszt niemal darmowo | S |
| 6.A26 | **ZROBIONE (07.09.2026).** Pomiar, na którym stoi decyzja 6.A22, jest **pilnowany po każdym commicie**, a nie zapisany raz w raporcie. Bramka klasyfikuje **każde** wystąpienie postaci `--opcja=wartość` w repozytorium po **wołanym programie** — sklejenie kontynuacji wierszy, potem podział po markerze — i odmawia, gdy trafi w komendę `Sim.Runner`. Zmierzone **trzy razy, każdy raz na nazwanym drzewie**: `409 / 1 / 99 / 309` na `main` przed 6.A25 i przed tą bramką, `419 / 1 / 99 / 319` na tej gałęzi przed przestawieniem, i `426 / 1 / 100 / 325` na drzewie, które idzie do scalenia. Cały przyrost 409 → 426 jest **rozliczony po plikach**, nie zgadnięty: `+1` w `docs/TASKS.md` (wiersze 6.A25 i 6.A26), `+5` w tym raporcie, `+11` w samym klasyfikatorze i jego kontrolach (4 → 15). **Bramka, która liczy także siebie, ma to powiedzieć wprost** — inaczej pierwszy commit dopisujący do niej test wyglądałby jak wzrost liczby komend w repozytorium; kubełek `scena` wzrósł o jeden z tego samego powodu, bo wzorce kontrolne KN-E i testu pierwszeństwa niosą marker sceny i postać z równością, i to jest poprawne: one SĄ komendami sceny, tylko syntetycznymi. Jedyna komenda runnera z równością to pole `Weryfikacja` pozycji 6.A22 — komenda, której CAŁYM sensem jest pokazanie odmowy dla tej postaci — więc stoi na liście usprawiedliwień z powodem przy sobie, a osobny test pilnuje, żeby usprawiedliwienie nie przeżyło komendy, którą opisuje (zasada z 6.D29 i 6.B34). Klucz to **(ścieżka, fragment komendy)**, nie numer wiersza: numer przesuwa każdy commit dopisujący cokolwiek wyżej, a bramka zapalająca się na tekście poprawnym zostaje wyłączona, nie naprawiona (6.D27). **To jest sprostowanie do własnego raportu i jest tu POKAZANE, nie tylko powiedziane**: §10 `reports/postac-z-rownosciem.md` obiecywał, że „bramka z §5 pokaże to jako FAIL, zamiast czekać na czyjeś oko", a bramka z §5 czyta w całości jeden plik — `src/Sim.Runner/Program.cs`; komenda w workflowie, w `docs/` albo w `tools/**/*.sh` nigdy nie przechodziła przez tamten kod. §10 dostał adnotację, zdania nie przeliczono. Pięć WYKONANYCH kontroli: **KN-A** (wstrzyknięta komenda runnera z równością, złamana na trzy wiersze) zgłoszona z plikiem i numerem PIERWSZEGO wiersza; **KN-B** (wzorzec zepsuty) wywraca cztery testy, a `test_no_runner_command…` **zostaje zielony** — zero komend runnera to zero, i to jest jedyny powód istnienia progu na łączną liczbę; **KN-C** (sklejanie kontynuacji wyłączone) sprawia, że wstrzyknięta komenda **znika z pola widzenia**, bo marker stoi w pierwszym wierszu, a równość w trzecim — sklejanie jest nośne, nie kosmetyczne; **KN-D** to **znalezisko o mojej własnej bramce**: przestawienie kolejności tak, że runner jest sprawdzany pierwszy, zostawiło zestaw **15/15 zielony**, bo w dzisiejszym drzewie nie ma ani jednego wiersza niosącego oba markery — reguła pierwszeństwa sceny była więc **komentarzem, nie bramką**, i dopisany test przybija ją na wejściu syntetycznym; **KN-E** dowodzi, że ani jedna z 99 komend sceny nie jest zgłaszana, bo bramka łapiąca scenę zostałaby wyłączona w tym samym tygodniu — scena postaci z równością WYMAGA. `test_runner_options.py` 9 → **15**. Pomiar w `reports/pomiar-rownosci.md`. Poza zakresem, zgodnie z polem: obsługa postaci w runnerze i zmiana konwencji sceny. Zauważone, nie tknięte: dwie komendy w `reports/` cytują `Sim.Runner/bin/Release/net8.0/…`, a projekt buduje `net10.0` — pomiary z datą się nie przeliczają, ale pole „Weryfikacja" cytujące taką ścieżkę BYŁOBY niewykonalne, a bramki na to nie ma. Tresc pierwotna: **Nic nie pilnuje, ze zadna komenda `Sim.Runner` w repozytorium nie uzywa postaci `--opcja=wartosc`** — a na tym pomiarze stoi decyzja 6.A22 o odrzuceniu tej postaci | zmierzone 07.09.2026 przy 6.A22 i sprostowane w tej pozycji: bramka z §5 tamtego raportu czyta wylacznie `src/Sim.Runner/Program.cs`, wiec komenda w workflowie albo w `docs/` byla poza jej zasiegiem | S |
| 6.B35 | **ZROBIONE (07.09.2026).** Pełny przegląd mutacyjny **dochodzi znów do końca**: `--only tools/blender/lod_paths.py --workers 2` kończy się `rozstrzygniętych 2/2, zabitych 2, ocalałych 0` i kodem **0**, a nie kodem 2 przed policzeniem pierwszej mutacji. Zaślepka `OWN_TESTS_STUB` jest dziś **pełnoprawnym modułem testowym**: docstring, jeden test tożsamości i strażnik `__main__` delegujący do `test_all` — trzy rzeczy, każda wymuszona inną regułą i każda ZMIERZONA, nie założona (bramka 6.D25 żąda strażnika z delegacją; `test_all.main(<plik>)` odmawia przy zerze testów; `assertion_gate` przy teście bez asercji). **Rzecz warta powiedzenia wprost: kalibracja wyroczni zadziałała.** Gdyby jej nie było, przegląd zameldowałby **100 % zabić** i nic w wyniku by tego nie zdradziło — to samo, co zdarzyło się przy OOM 02.09.2026 i przy kasacji pliku 05.09.2026, tylko że wtedy za drugim razem nie było żadnej obrony. Dziś narzędzie **odmówiło**, zamiast skłamać w stronę „wszystko w porządku". **Pomiar, o który prosiło pole „Wyjście"**: zestaw w prawdziwym drzewie roboczym `git worktree` z nową zaślepką ma **1785 testów / 99 modułów**, kod 0, wobec **1784 / 98** z zaślepką bez testu — czyli +1 test i +1 moduł; dla kalibracji jest to bez znaczenia i **to też jest zmierzone, nie wywnioskowane**, bo `baseline_problem` czyta werdykt `run_suite`, nie liczbę testów. **Asercja, która przybijała usterkę, jest PRZEPISANA, nie skasowana**: `test_przygotowanie_drzewa...` żądał, żeby zaślepka nie miała ani jednej funkcji `test_` i była „samym docstringiem"; intencja zostaje ta sama (prawdziwej treści testów w zaślepce nie ma), zmienia się to, co z niej wynika dla kształtu pliku. Nowy test kształtu czyta zaślepkę **tym samym przyrządem, który ją odrzucił** — `ma_straznik()` i `DELEGACJA` z `test_module_entrypoints.py` — bo bramka widzi tylko pliki LEŻĄCE w drzewie, a zaślepka powstaje dopiero w drzewie roboczym, i to jest dokładnie ta luka, w której usterka żyła dobę. Dwie WYKONANE kontrole negatywne: **KN-1** (powrót do samego docstringu) daje z powrotem kod 2 z tymi samymi dwiema nazwami, czyli dowodzi, że to poprawka odblokowała przegląd, a nie zbieg okoliczności; **KN-2** dowodzi, że sam strażnik NIE wystarcza — zestaw w drzewie przechodzi (kod 0) także z zaślepką bez testu, więc przegląd by ruszył, ale droga pojedynczego modułu kończy się wtedy `FAIL <bramka asercji>: nie odkryto ani jednego testu` i kodem 1. Zestaw narzędzi 1855 → **1856**. Pomiar w `reports/zaslepka-narzedzia.md`. Poza zakresem, zgodnie z polem: rozluźnienie bramki z 6.D25 — ona ma rację, usterka była w zaślepce; nie tknięto też niczego w tym, CO przegląd mierzy. Bramka uruchamiająca `main()` narzędzia to **6.B37**, wpisana właśnie dlatego, że ta usterka przeżyła dobę. Tresc pierwotna: **Przeglad mutacyjny NIE DOCHODZI DZIS DO KONCA** — `mutation_sweep.py` przerywa kodem **2** w kazdym czystym drzewie roboczym, bo zaslepka `neutralise_own_tests` nie ma strazniku `__main__` ani delegacji do `test_all`, ktorych zada bramka `test_module_entrypoints.py` z 6.D25 | zmierzone 07.09.2026 przy 6.B20 i **potwierdzone przeze mnie osobno**: `OWN_TESTS_STUB` to sam docstring, wiec kalibracja wyroczni melduje `zestaw PADA w czystym drzewie` i wymienia `test_every_module_delegates_to_the_one_runner` oraz `test_every_test_module_can_be_run_directly`. Narzedzie jest niesprawne od scalenia 6.D25 i nikt tego nie zauwazyl, bo od tamtej pory nikt nie odpalil pelnego przegladu | M |
| 6.B37 | **ZROBIONE (07.09.2026).** Trzy testy w `tools/tests/test_mutation_sweep.py`, a przy okazji **założenie tej pozycji okazało się w jednej trzeciej nieprawdziwe i zostało zmierzone, nie przyjęte**. Wpis mówił „żaden test nie uruchamia narzędzia jego własną drogą (`main()`)"; przejście po `ast` po `origin/main` daje **pięć** testów wołających `mutation_sweep.py` przez `subprocess.run` (`test_unknown_operator_class_is_rejected_by_the_cli`, `test_cli_lists_only_the_requested_class`, `test_only_is_a_substring_match…`, `test_resume_refuses_a_journal_written_on_another_tree`, `test_resume_still_works_when_the_journal_is_from_the_same_tree`) — **kod wyjścia drogi CLI był pilnowany od dawna**, i to potwierdza KN-3a: podmiana `return 0` na `return 3` w gałęzi `--list` wywraca cztery testy, z czego trzy starsze od tej pozycji. **Dwa pola tej pozycji żądały rzeczy wykluczających się**, i widać to tylko po pomiarze: „Wyjście" proponowało bramkę na `--list`, a „Skończone, gdy" żądało, żeby zaślepka pozbawiona strażnika wywróciła **dokładnie ten** test — tymczasem `--list` wraca kodem **0 także z zaślepką bez strażnika**, bo wychodzi z `main()` PRZED `add_worktree` i przed kalibracją wyroczni (zmierzone z podmienioną treścią: `razem: 2`, `kod: 0`). Kryterium **nie zostało rozluźnione** — doszła druga bramka, idąca tą drogą, na której usterka 6.B35 żyła dobę: `git worktree add` → `neutralise_own_tests` → uruchomienie modułu WPROST. **I tam kod wyjścia też nie wystarcza**: zaślepka bez strażnika daje w drzewie kod **0** i PUSTY wypis, bo moduł bez `__main__` uruchomiony wprost nie wykonuje niczego — rozstrzyga więc LICZBA wykonanych testów, czytana tym samym `_liczba_testow`, którym czyta ją bramka 6.D25, a nie własną kopią (dwa czytniki jednej rzeczy rozjeżdżają się po cichu — to była usterka 6.B28). Trzeci test to **kontrola przyrządu na stałe w zestawie**: podmienia zaślepkę na sam docstring i żąda, żeby sonda pokazała brak liczby testów mimo kodu 0. Trzy WYKONANE kontrole negatywne: **KN-1** (usterka 6.B35 przywrócona) wywraca nowy test drzewa plus dwie bramki z 6.B35 czytające zaślepkę jako napis, a test CLI **zostaje zielony** — to jest pomiarowy dowód na to, że pole „Wyjście" nie starczało; **KN-2** (sonda oślepiona, podmiana zastąpiona `pass`) wywraca dokładnie jeden test, ten właściwy; **KN-3b** (usunięty `print(f"razem: …")`) wywraca **wyłącznie** nowy test CLI, bo stare filtrują wypis po przedrostku `tools/` i podsumowania nie oglądają wcale — to jest prawdziwy, węższy wkład pierwszego z trzech. Koszt, o który prosiło pole „Wyjście", liczbą i **dwoma niezależnymi pomiarami, które zgadzają się do 0,02 s**: moduł po trzy przebiegi w każdą stronę daje mediany **14.229 s / 69 testów → 14.910 s / 72 testów**, czyli 0,681 s; suma median per test to **0,325 + 0,207 + 0,129 = 0,661 s**, z czego 0,19 s to dwa `git worktree add`. Pierwsza para pomiarów była pojedyncza (14.109 → 15.017 s) i przy szumie rzędu 0,4 s nie miała czym się potwierdzić — zastąpiona medianami, nie dopisana obok. Zestaw na commicie do scalenia, dwa przebiegi: `RAZEM 77.248 s` i `RAZEM 76.713 s`, oba `1868 testów, 99 modułów`, kod 0 (przed przestawieniem na `main` ze scalonymi #362 i #363 było 76.651 s przy tej samej liczbie testów i modułów — żaden z tych PR nie dodaje testów pythonowych, a rozrzut 0,6 s jest podany, bo pojedyncza liczba wyglądałaby na dokładniejszą, niż jest); C#: 578 w `Sim.Tests`, 205 w `Game.Tests`, zero porażek. Poza zakresem, zgodnie z polem: uruchamianie pełnego przeglądu ani `baseline_problem` przez `main()` — to jeden pełny przebieg zestawu, ~76 s w bramce chodzącej po każdym commicie, a droga przygotowania drzewa daje tę samą ochronę za 0,21 s. Pomiar w `reports/straznik-na-main.md`. Zauważone przy okazji, nie tknięte: `--list` z `--only` na wzorzec pasujący do niczego daje `razem: 0` i **kod 0**, bo odmowa `brak mutacji do sprawdzenia` stoi ZA gałęzią `--list` — przebieg CI, który przez pomyłkę zawęzi `--only` na nic, dostanie zielone zero. Tresc pierwotna: **Nic nie pilnuje, ze `mutation_sweep.main()` w ogole dochodzi do konca** — 6.B35 zyla niezauwazona przez cala dobe, bo zaden test nie uruchamia narzedzia jego wlasna droga (`main()`), tylko wola funkcje wewnetrzne | zmierzone 07.09.2026 przy 6.B20: obejscie blokera z 6.B35 polegalo na wolaniu funkcji przez `importlib`, czyli droga, ktorej nikt w praktyce nie uzywa. Bramka na `--list` jest tania (nie odpala ani jednej mutacji) i wystarczy, zeby taka awaria nie przezyla nastepnego commita | S |
| 6.A27 | **ZROBIONE (07.09.2026).** Każda odmowa `compare` ma dziś ten sam kształt wyjścia co reszta odmów runnera — przedrostek `BŁĄD: ` od wspólnego handlera i kod **1**. **Ale pozycja mówiła o DWÓCH odmowach, a jest ich CZTERY**, i to jest pomiar, nie domysł: `Console.Error.WriteLine` w ciele `Compare` występował **4** razy i `return 1;` **4** razy. Pole „Poza zakresem" wyłączało trzecią (`zła liczba kolumn`) **warunkowo** — „jeżeli pomiar pokaże, że ona już przedrostek ma" — a pomiar pokazał, że NIE miała; o czwartej (`różna faza scenariusza`) wpis nie wiedział wcale. Warunek nie zaszedł, więc pozycja objęła cztery. Wykonane wszystkie cztery drogi plus droga poprawna: `BŁĄD: różna liczba wierszy: 7641 vs 7638` (kod 1), `BŁĄD: nagłówki telemetrii nie zgadzają się z formatem rdzenia` (kod 1), `BŁĄD: wiersz 5: zła liczba kolumn` (kod 1), `BŁĄD: wiersz 5: różna faza scenariusza (INNA-FAZA vs traction)` (kod 1), a `compare d1.csv d2.csv` nadal `[PORÓWNANIE]` i kod **0**. Treści ani kodów nie zmieniono — pole „Poza zakresem"; kod był dobry już od 6.A16, niezgodny był KSZTAŁT. **Pomiar, o który prosiło pole „Wyjście", z liczbą także tam, gdzie wynosi zero**: dopasowań tych komunikatów przed zmianą było `tools: 0`, `.github: 0`, `docs: 5`, `reports: 4`, `src: 6`, `tests: 0` — **żadna bramka i żaden krok CI nie opierał się na ich treści**, więc zmiana kształtu nie mogła niczego wywrócić. Po zmianie `tools/` ma 5 dopasowań i wszystkie są `ODMOWY_COMPARE` w bramce, którą ta pozycja dopisała. **Znalezisko ważniejsze od samej poprawki: bramka z 6.A16 meldowała zgodę zamiast pomiaru.** `test_compare_refuses_through_the_common_handler` żądał, żeby w ciele `Compare` stały słowa `throw new ArgumentException` — zdanie prawdziwe od 6.A16 i pozostające prawdziwe, kiedy obok siedziały cztery odmowy omijające handler. Wykonane na drzewie PRZED tą pozycją: wszystkie trzy asercje `True`, **stara bramka ZIELONA**, a w tym samym ciele `Console.Error.WriteLine: 4` i `return 1;: 4`. Ten sam gatunek usterki co 6.D30 i 6.B28 — asercja na OBECNOŚĆ czegoś dobrego zamiast na BRAK czegoś złego. Asercja jest **przepisana, nie dopisana obok**: postać licząca to zero `Console.Error` i zero `return 1;` w ciele `Compare`, przy zachowanym końcowym werdykcie `return failed ? 1 : 0;` (który odmową nie jest), a czytnik zdejmuje komentarze, bo akapity wyjaśniające POWÓD same te napisy zawierają. Drugi nowy test przybija każdą z czterech treści z nazwy — sam licznik `Console.Error == 0` przechodziłby także wtedy, gdyby ktoś odmowę USUNĄŁ, a odmowa usunięta jest gorsza od odmowy bez przedrostka. Dwie WYKONANE kontrole negatywne: **KN-1** (jedna odmowa cofnięta) daje `FAIL … 1 odmow w compare pisze na stderr wprost`, nazywa KTÓRĄ, i wywraca po stronie C# dokładnie jeden test; **KN-2** to §4 raportu — stan przed pozycją przeciwko starej asercji, zielony przy czterech odmowach omijających handler. Testy C# **584 → 589** (nie 578 → 583: pierwszy pomiar był na drzewie sprzed scalenia #366, a różnica ma nazwane źródło, nie jest wyrównana po cichu), `test_runner_exit_codes.py` 3 → **4**, zestaw narzędzi `1872/1872, RAZEM 77.052 s, 99 modułów`, kod 0. **Bramka 6.D28 zapaliła się na moich własnych testach**: pierwsza wersja delegowała WSZYSTKIE asercje do pomocnika, więc dwa testy miały ciała bez ani jednej — `FAIL test_every_csharp_test_method_has_an_assertion_in_its_body` wymienił je z nazwy. Poprawione podziałem, który nie jest estetyczny: pomocnik sprawdza wyłącznie to, co wspólne, a treść każdej odmowy asercjonuje jej własny test w swoim ciele. W sesji, w której trzy razy trafiłem na instrument meldujący zgodę zamiast pomiaru, obca bramka złapała ten sam wzorzec u mnie. Pomiar w `reports/przedrostek-compare.md`. Zauważone, nie tknięte: wzorzec „choć jedno wystąpienie istnieje" trafił mi się dziś **trzeci raz w jednej sesji** — tutaj, w 6.A25 (wpisane jako 6.A29) i w 6.A26 (reguła pilnowana wyłącznie komentarzem); audyt asercji `in body` / `Contains` w całym zestawie byłby zadaniem z pomiarem, ale pozycji wymyślonej na miejscu nie dopisuję. Tresc pierwotna: **Dwie odmowy `compare` nie maja przedrostka `BLAD:`** — `roznia liczba wierszy` i `nagloweki telemetrii nie zgadzaja sie z formatem rdzenia` wracaja `return 1`, a nie wyjatkiem, wiec omijaja wspolny handler | zmierzone 07.09.2026 przy 6.A24, ktore swiadomie tego nie ruszylo i wypisalo w §8 | S |
| 6.B36 | **ZROBIONE (07.09.2026).** Mapa pokrycia liczona **raz na commit** i zapamiętana między przebiegami; oszczędność **328 s, czyli 74 %** z czterech przebiegów tego samego modułu: zimno **437,2 / 445,7 s**, z pamięci **112,7 / 113,6 s**. **Dwa pomiary, których żądało pole „Wyjście", i oba rozstrzygnęły kierunek.** Pierwszy: mapa **nie zależy** od mutowanego modułu — `coverage_map(out_dir, timeout)` nie bierze żadnego argumentu o module, śledzi całe `tools/` w kopii `HEAD`; potwierdzone przebiegiem na INNYM module (`crs.py`, 29 mutacji, 891,7 s), który wziął mapę policzoną dla `lod_paths.py`. Drugi: zestaw bez sondy **54,49 s**, z sondą **332,57 i 331,92 s** — narzut licznika wierszy to **~278 s**, czyli sonda kosztuje **6,1 raza** tyle, co goły zestaw (liczby niższe od 416,7–426,6 s z 6.B20; tamten pomiar ma datę i się go nie przelicza). **Znalezisko, które zmieniło implementację**: dwie sondy z TEGO SAMEGO drzewa dały po 162 klucze i te same 25 732 wiersze, ale **różne zbiory kluczy** — różnica to piaskownice zakładane przez sam zestaw (`tools/tests/test_dwa_<losowe>/…`, bramka 6.D25), a losowy przyrostek zmienia się co przebieg; **w ani jednym wspólnym module wiersze się nie różniły**. Bez obcięcia każdy test porównujący mapę z pamięci z policzoną od nowa byłby chwiejny, i to nie z winy pokrycia. `pokrycie_w_celach` obcina mapę do celów mutacji: z 162 kluczy celami jest **57** (celów 63, sześciu zestaw nie uruchamia), z 25 732 wierszy w celach leży **7 582**, a 105 kluczy to `tools/tests/` — zestaw obserwujący sam siebie. Obcięcie **nie zmienia żadnego werdyktu**, bo `was_executed` pyta wyłącznie o `mutation.path`, czyli zawsze o cel, i jest jedynym czytnikiem tej mapy. **Werdykty identyczne wiersz po wierszu**: `wpisow: 2 / 2`, `te same identyfikatory: True`, `roznice w polach istotnych: BRAK` (porównane `przezyla`, `rozstrzygniete`, `wykonana`, `kod`, `plik`, `wiersz`, `rodzaj`, `bylo`, `jest`, `commit`, `odcisk`, `ile_padlo`). **Klucz to COMMIT, nie odcisk treści z 6.B32, i to jest różnica warta nazwania**: sonda czyta kopię `git worktree add --detach HEAD`, więc zależy od HEAD i tylko od HEAD, a mutacje liczy `collect` z DRZEWA ROBOCZEGO — dwa klucze do dwóch różnych rzeczy, każdy zmierzony. Caching nie wprowadza nowego zagrożenia: mapa była z `HEAD` już przed tą pozycją. Kontrola negatywna, której żądało pole „Skończone, gdy", **WYKONANA**: commit podmieniony **wewnątrz pliku** (nazwa bez zmian, bo nazwę da się zmienić jednym `mv`) → przebieg **odrzucił** mapę, policzył sondę od nowa (**445,7 s**) i przepisał plik właściwym commitem, a następny przebieg wziął ją z pamięci (**113,6 s**) — **dowodem jest różnica czasów, nie komunikat**. **Pierwsza próba tej kontroli była nierozstrzygająca i jest to zapisane**: uruchomiłem ją z `--list`, a ta gałąź wychodzi z `main` PRZED sondą, więc nie zmierzyła niczego — ten sam kształt pomyłki, który 6.B37 zmierzyło dla `add_worktree`. Pozostałe drogi odrzucenia (plik nieczytelny, inna wersja kształtu, nie-słownik, brak pliku) sprawdzone testami: każda daje `None`, czyli „brak mapy", a nie mapę niepełną. `test_mutation_sweep.py` 78 → **83**, zestaw `1891/1891, RAZEM 68.057 s, 99 modułów`, kod 0. Pomiar w `reports/pamiec-pokrycia.md`. Poza zakresem, zgodnie z polem: wyłączenie sondy i limit czasu mutacji. Nie skrócono samej sondy — ta pozycja usuwa POWTARZANIE kosztu, nie sam koszt; nie dodano flagi wymuszającej przeliczenie, bo mapa jest samoopisująca się i stan „pamięć nieaktualna" nie ma jak powstać bez ręcznej edycji, którą odmowa łapie. Zauważone, nie tknięte: **pierwszy przyrząd pomiarowy nie ruszył wcale, a skrypt zakończył się kodem 0** — opakowałem trzy przebiegi w `/usr/bin/time`, którego w tym kontenerze nie ma, i kod wyjścia wziął się z ostatniego polecenia bloku, nie z przebiegów; dokładnie ta klasa usterki, którą ta sesja tropiła cały dzień. Tresc pierwotna: **Sonda pokrycia zjada 78 % czasu przegladu mutacyjnego** — 416,7-426,6 s z 534,3-600,3 s, wiecej niz cala reszta razem | zmierzone 07.09.2026 przy 6.B20 jako fazy jednego ciaglego przebiegu, przy 1, 2 i 4 robotnikach | M |
| 6.A28 | **ZROBIONE (07.09.2026).** Żadna opcja ścieżkowa nie przyjmuje już pustej wartości w milczeniu: `--telemetry=` kończy się kodem **9** i komunikatem nazywającym opcję, a nie kodem 0 z planem uznanym za poprawny. **Pomiar, o który prosiło pole „Wyjście", i on rozstrzygnął zakres**: pustkę przyjmowało **dziewięć z dziesięciu** opcji ścieżkowych (kod 0, `IsValid` prawdziwe, wartość równa napisowi pustemu), a dziesiąta (`--calls`) była odrzucana z powodu NIEZWIĄZANEGO z pustką — wymaga `--line`. Warunek „jeżeli wszystkie, poprawka jest jedna i wspólna" zaszedł: jedna lista `RunPlan.PathArguments` i jedna pętla w `Parse`, postawiona PRZED sprawdzeniem zależności między argumentami, bo odmowa ma padać przed przejazdem, nie przy zapisie wyniku. **Dziesięć, nie dziewięć — wpis o jednej nie wiedział**: dziesiąta to `--assets`, której wartość jest ścieżką katalogu (`Argument("assets") ?? RepoPath("build/t400")`). **Mechanizm, nie tylko objaw**: `TelemetryPath` wychodziło napisem PUSTYM, nie `null`, więc warunek `_telemetryPath is not null` w scenie był prawdziwy — scena zbierała wiersze telemetrii przez cały przejazd i próbowała je zapisać pod pustą nazwą; to różnica między „opcja jest ignorowana" i „opcja jest brana z bezsensowną wartością", a druga kosztuje cały przejazd. **Czego NIE zmierzyłem i dlaczego jest to w raporcie napisane**: pole żądało sprawdzenia, czy usterka jest cicha czy głośna, ale zapis idzie przez `Godot.FileAccess.Open`, a Godota w tym kontenerze nie ma — **nie zgaduję**; dla porównania `System.IO.File.WriteAllLines("")` rzuca `ArgumentException: The value cannot be an empty string`, ale to inna biblioteka i nie wolno z niej wnioskować o Godocie. Pozycja czyni to pytanie **bezprzedmiotowym**, bo plan jest odrzucany przed jakimkolwiek przejazdem. `NoInputThrows` zmieniony **razem z poprawką**, tak jak żądało pole „Skończone, gdy": licznik 8 → **9**, a lista `przyjete` z `{ "--telemetry=" }` na **pustą** — nie skasowana, bo `CollectionAssert.AreEqual` na pustym zbiorze jest asercją BEZWARUNKOWĄ i wywraca się, gdy rozbiór zacznie cokolwiek przyjmować, a sam licznik nie mówi KTÓRE wejście przeszło. Trzy WYKONANE kontrole negatywne: **KN-1** (sprawdzenie pustki zdjęte) wywraca cztery testy, w tym `NoInputThrows` starszy od tej pozycji, a `Lista_opcji_sciezkowych…` zostaje zielony i tak ma być — lista dalej istnieje, zdjęte jest jej UŻYCIE; **KN-2** (odmowa zbyt szeroka, `path is not null`) wywraca **27 testów**, w tym `EveryKnownArgumentIsAcceptedOnItsOwnOrNamesWhatItNeeds` i całą rodzinę limitów, co dowodzi, że kontrola drugiego kierunku istnieje NIEZALEŻNIE od moich nowych testów; **KN-3** (lista okrojona o `assets`) wywraca dokładnie jeden test, ten właściwy — bez niego pętla byłaby zielona na mniejszym zbiorze. Testy `Game.Tests` 205 → **210**. Pomiar w `reports/pusta-sciezka.md`. Poza zakresem, zgodnie z polem: `KnownArguments`, wartości nieliczbowe i nieistniejące ścieżki. **Nie dopisałem bramki po stronie Pythona**, mimo że pierwsza wersja komentarza w kodzie ją OBIECYWAŁA — obietnica usunięta i zastąpiona nazwą testu C#, który to naprawdę robi; to dokładnie ta usterka, którą 6.A26 dziś naprawiło w §10 raportu 6.A22, a drugi czytnik jednej listy rozjeżdża się po cichu (6.B28). Zauważone: **pierwsza wersja mojego testu żądała, żeby `--calls=` szło inną drogą, i padła** — założyłem kolejność sprawdzeń, przebieg pokazał odwrotną; test poprawiony według pomiaru, a nie pomiar według testu. Tresc pierwotna: **Scena przyjmuje `--telemetry=` z PUSTA sciezka jako plan poprawny** — pojechalaby z pusta sciezka pliku telemetrii | zmierzone 07.09.2026 przy 6.D31 licznikiem, ktory mial wyjsc inaczej: `Assert.AreEqual failed. Expected:<999>. Actual:<8>. paskudnych wejsc odrzuconych; przyjete: --telemetry=` | S |
| 6.B38 | **ZROBIONE (07.09.2026).** Moduł **17,255 s → 15,798 s** (mediany z trzech przebiegów na stronę, przedziały rozłączne), przy liczbie testów **104 → 108** — czas spadł, a testów jest WIĘCEJ, nie mniej. **Pomiar per test obalił założenie pozycji o trzech kupkach:** `git worktree add`+`remove` to **0,21 s, czyli 1 %** modułu (jedno drzewo 0,095 s + 0,009 s, używają go dwa testy), a największą pojedynczą pozycją jest test, który **nie uruchamia żadnego procesu** — `ast.parse` na 2346 mutacjach, **6,44 s, 37 %**. Reszta: procesy ≈ 7 s (40 %), **`collect()` wołane dziesięć razy po 0,224 s = 2,24 s (13 %)**, import 63 modułów 1,79 s (10 %). Z tych czterech kupek tylko jedna jest marnotrawstwem i tylko ona jest ruszona: pamięć `collect` kluczowana **odciskami wszystkich celów**, nie samym zestawem klas — testy tego narzędzia zmieniają pliki celów w trakcie procesu (KN 6.B32, 6.B39, 6.B40), więc klucz na klasach podstawiałby mutacje policzone dla innej treści, czyli usterkę 6.B32 przeniesioną do pamięci procesu. Klucz jest darmowy i to zmierzone: sha256 wszystkich 63 celów **0,0013 s** przy **0,224 s** na `collect()`. **Cudza bramka 6.B32 zapaliła się na tej poprawce i została PRZEKIEROWANA, nie zdjęta**: liczyła wystąpienia napisu `odciski_przebiegu(` i żądała dokładnie dwóch, a po przekierowaniu liczy **prawdziwe wywołania** `odcisk_tresci` i żąda tyle, ile celów — KN-A pokazuje, że jest mocniejsza w obu kierunkach (odcisk w pętli po mutacjach daje **2409 zamiast 63** i pada, a licznik napisu zostałby na 2 i był zielony). Zestaw **1927 → 1931**, kod wyjścia 0; efekt na całym zestawie zgodny w znaku, ale **w jego własnym rozrzucie** i tak podany. Trzy kontrole WYKONANE; **KN-C (pamięć zwraca tę samą listę, nie kopię) wywraca cztery testy, z czego dwa starsze od tej pozycji** — bo test kopii woła `.clear()` na wyniku, więc bez kopii zatruwałby pamięć wszystkim następnym. **Dwie usterki we własnych przyrządach, obie w rodzinie tego dnia**: pierwszy pomiar `git worktree add` dał 0,002 s, bo mierzył komendę z **kodem 128** i błędem `invalid reference` (zła kolejność argumentów) — prawdziwie 0,095 s, 47× więcej; a pomiar `ast.parse` dał 39,9 s przy 17,3 s całego modułu, bo gromadził drzewa w liście (bez gromadzenia 6,44 s, z gromadzeniem 28,63 s — **4,4×** z samego trzymania wyników). Pomiar w `reports/czas-modulu-mutacyjnego.md`. Tresc pierwotna: **Jeden modul zjada piata czesc czasu zestawu** — `test_mutation_sweep.py` to **15,3 s** z 76 s, bo jego testy uruchamiaja procesy i zakladaja drzewa `git worktree` | zmierzone 07.09.2026 przy 6.B37. Prog z 6.D26 stoi na czasie CALEGO zestawu, a ten modul jest jedynym, ktory sam z siebie sie do niego zbliza — i kazdy nastepny test narzedzia go podnosi. Bez pomiaru, co wewnatrz kosztuje najwiecej, pierwsza reakcja na przekroczony prog bedzie zdjeciem testow | M |
| 6.A29 | **ZROBIONE (07.09.2026).** Test `Zepsuta_komorka_nazywa_zepsuty_plik_a_nie_pierwszy` asercjonuje dziś te części komunikatu 6.A24, których **nie ma żadna inna odmowa runnera** — `wiersz 5`, `kolumna 3`, `chainage_m` i samą złą wartość — a nie tylko kod 1 i nazwę pliku. **Pomiar, o który prosiło pole „Wyjście", i on zmienił zakres poprawki**: z czterech testów rodziny 6.A24 asercję rozstrzygającą miały **TRZY**, nie zero. `Zepsuta_komorka_nazywa_plik_wiersz_i_kolumne` sprawdza `wiersz 3`, `kolumna 1`, `step`; `Numer_i_nazwa_kolumny_ida_z_pozycji_w_wierszu` sprawdza `kolumna 5`, `speed_mps`, `wiersz 7`; `Dwa_poprawne_pliki_nadal_przechodza` mierzy drugi kierunek (kod 0). Warunek z pola „Wyjście" — „jeżeli wszystkie cztery, poprawka jest jedna i wspólna" — **nie zaszedł**: poprawka dotyczy jednego testu. Licząc tylko testy asercjonujące TREŚĆ odmowy: **2 z 3 przed, 3 z 3 po**. Asercje są **dopisane, nie przepisane** — tamte trzy były prawdziwe, tylko za słabe, a skasowanie ich odebrałoby testowi to, co mierzy z nazwy (komunikat nazywa plik ZEPSUTY, nie pierwszy z wiersza poleceń). Zmierzone wykonaniem, jaki komunikat ten test naprawdę ogląda: `BŁĄD: build/zepsuty.csv: wiersz 5 (nagłówek to wiersz 0), kolumna 3 „chainage_m” — „nie-liczba” nie jest liczbą`; `DwaPlikiTelemetrii(5, 2, …)` psuje TRZECIĄ kolumnę, bo komunikat liczy kolumny od jednego — decyzja 6.A24, nie przypadek. Doszła też **bramka po stronie Pythona** z tabelą „test → części komunikatu, które musi asercjonować", plus osobna asercja na istnienie testu drugiego kierunku (bez niej bramka byłaby zielona także po usunięciu jedynego testu sprawdzającego, że dwa poprawne pliki przechodzą), plus kontrola przyrządu: gdyby czytnik ciała metody wycinał do końca pliku, bramka byłaby zielona ZAWSZE, bo `wiersz `, `kolumna ` i nazwy kolumn występują w tym pliku wielokrotnie. Trzy WYKONANE kontrole negatywne: **KN-1** — ta, której żądało pole „Skończone, gdy" — `compare` z zerową liczbą członów pozycyjnych wywraca teraz **cztery z czterech** testów 6.A24 (`Failed: 6, Passed: 578` wobec `Failed: 5, Passed: 579` przed poprawką); **KN-2** (dołożone asercje cofnięte) nazywa KTÓRY test i KTÓRYCH części mu brakuje; **KN-3** (przyrząd oślepiony) daje `wycinek ciala metody ma 8538 znakow przy pliku 63695 — czytnik bierze za duzo`. `test_csharp_assertions.py` 8 → **10**, testy C# **584** bez zmiany liczby (asercje dołożone do istniejącego testu, nie nowy test). Pomiar w `reports/asercja-rozstrzygajaca.md`. Poza zakresem, zgodnie z polem: treść komunikatu 6.A24 (on ma rację, słaby był test) i audyt wszystkich asercji `RunnerCommandTests`. Zauważone, nie tknięte: **wzorzec asercji „prawdziwej, ale nie rozstrzygającej" wyszedł dziś czwarty raz** — tutaj, w 6.A27 (`throw` istnieje, cztery `Console.Error` obok, bramka zielona), w 6.A26 (reguła pierwszeństwa pilnowana wyłącznie komentarzem) i w 6.A25 (KN-2: odmowa z własną stałą zostawia wszystkie testy C# zielone); wspólna cecha to asercja na OBECNOŚĆ czegoś dobrego zamiast na BRAK czegoś złego albo na LICZBĘ. Tresc pierwotna: **Test `Zepsuta_komorka_nazywa_zepsuty_plik_a_nie_pierwszy` przechodzi z calkiem innego powodu, niz sadzi** — jego trzy asercje spelnia dowolna odmowa, ktora nazwie PIERWSZA sciezke, wiec test nie mierzy komunikatu 6.A24 | zmierzone 07.09.2026 przy 6.A25, kontrola KN-1: przy `compare` z zerowa liczba czlonow pozycyjnych piec testow `compare` pada, a TEN zostaje zielony | S |
| 6.B39 | **ZROBIONE (07.09.2026).** `--only` bez trafień kończy się dziś **kodem 1** także na drodze `--list`, i to przez **ten sam przyrząd** `przyczyna_pustego_zbioru`, co droga bez `--list` — obie nie mogą już podać różnych przyczyn tego samego stanu (do dziś różniły się maksymalnie: `razem: 0` i kod 0 wobec komunikatu i kodu 1). **Pomiar z pola „Wyjście" zmienił zakres poprawki i znalazł DRUGĄ usterkę, o której pozycja nie wiedziała**: pytanie „moduły czy mutacje" ma odpowiedź twierdzącą i osiągalną jedną komendą — `--only tools/blender/camera_aim.py --operators prog` dopasowuje **dokładnie jeden** cel i daje zero mutacji, a komunikat mówił wtedy `nie dopasowało ani jednego pliku`, czyli zdanie **fałszywe**. Ta sama rodzina co 6.B41 (gałąź nazywająca przyczynę, która nie zachodzi), tydzień po tamtej poprawce i w tym samym pliku. Modułów bez ani jednej mutacji danej klasy jest od **2** (`operator`) do **36** (`przypisanie`) na **63** cele, więc przypadek nie jest teoretyczny; przy pełnym zestawie klas jest ich **0 z 63**, co czyni rozróżnienie nieobserwowalnym w domyślnym wywołaniu — i dokładnie dlatego wcześniej nikt go nie zobaczył. Przebieg liczy teraz **pliki docelowe** dopasowane przez `--only` niezależnie od mutacji, a wiersz nagłówka podaje dwie liczby zamiast jednej. Nic wykonywalnego nie polegało na starym kodzie 0: wywołań narzędzia w workflowach **zero**, a z **48** realnych wzorców `--only` cytowanych w `reports/` i `docs/` zero celów łapie **jeden** — umyślna atrapa opisująca tę usterkę. Zestaw **1913 → 1918**, moduł **90 → 95**. Trzy kontrole negatywne WYKONANE, każda wywraca INNY zbiór; **KN-2 (odmowa zbyt szeroka) wywraca sześć testów, z czego cztery starsze od tej pozycji**, a złapał ją najpierw `ValueError` dołożony przez 6.B41 dzień wcześniej, nie mój własny test. Pomiar w `reports/pusty-zbior-listy.md`. Tresc pierwotna: **`mutation_sweep.py --list` z `--only` pasujacym do niczego konczy sie kodem 0** — przebieg CI, ktory przez pomylke zawezi `--only`, dostanie zielone zero i wyglad poprawnego przebiegu, ktory nie mial co robic | zmierzone 07.09.2026 przy 6.B37. Odmowa `brak mutacji do sprawdzenia` (kod 1) stoi ZA galezia `--list`, wiec wypisu nie dotyczy wcale. `--only` dopasowuje podciag (6.D18), wiec literowka w sciezce daje zbior pusty, a wypis wyglada jak poprawny przebieg | S |
| 6.A30 | **ZROBIONE (07.09.2026).** Piec wypisow informacyjnych `Sim.Runner` — `[RDZEŃ]` w `Drive` oraz `[LIMIT]`, dwa `[ODTWORZENIE]` i `[ATP]` w `Replay` — idzie dzis na **stdout**, razem z cala rodzina `[XXX]`; zaden znacznik nie wystepuje na obu strumieniach, bo na stderr nie ma ani jednego. **Pole „Wyjscie" zadalo najpierw dwoch pomiarow i oba sa wykonane.** POMIAR 1 — duplikat czy unikalny: **0 duplikatow, 5 unikalnych**, sprawdzone bajt w bajt przez zestawienie kazdego wiersza `[XXX]` ze stderr ze zbiorem WSZYSTKICH 33 wierszy stdout z `drive`, `replay`, `replay --atp` i `line --signalling`. Zadnego z pieciu nie wolno bylo skasowac, wszystkie pieciu trzeba bylo przeniesc. Najblizszym kandydatem na duplikat byl `[ATP]` — jedyny znacznik, ktory naprawde stal na obu strumieniach JEDNEGO programu (stdout w `line`, stderr w `replay --atp`) — ale wiersze maja inne pola i inna interpunkcje, wiec duplikatem nie jest. POMIAR 2 — kto czyta te wiersze ze stderr: **1 miejsce, 0 krokow CI**. Tym jednym bylo `tests/Sim.Tests/RunnerCommandTests.cs:77` (`StringAssert.Contains(result.StdErr, "[RDZEŃ]")`) i jest poprawione w tym samym commicie. Zero po stronie CI nie jest domyslem: kazde wywolanie runnera w `.github/workflows/` sklada strumienie (`2>&1 | tee <log>` albo `> <log> 2>&1`) i grepuje log zlozony, wiec trzy bramki, ktore te wiersze czytaja — wiersze 608, 742 i 1010 `.github/workflows/godot-first-run.yml` — maja identyczne wejscie przed i po. **Kierunek wybral stosunek, nie gust**: markerow `[XXX]` wypisuje `Program.cs` **38**, z czego **33 stalo na stdout** i 5 na stderr; po zmianie **38 na stdout, 0 na stderr**, a wypisow na stderr zostalo **3** i sa to dokladnie odmowy (`BŁĄD: `, `nieznane polecenie:`, wiersz pomocy). Telemetria jest **bit w bit ta sama** przed i po (trzy pliki CSV `cmp`-em) — zmienil sie strumien, nie przejazd; przebieg z `2>/dev/null` nie traci ani jednego wiersza `[XXX]` (4 z 4 przy `replay --atp`, 1 z 1 przy `drive`). Doszla bramka `tools/tests/test_runner_output_streams.py` z trzema asercjami, bo test C# oglada strumienie JEDNEGO wywolania i lapie tylko to, co ono wyprodukuje: brak markera na stderr (z numerem wiersza i nazwa znacznika w komunikacie), obecnosc kazdego z pieciu przeniesionych wierszy na stdout Z NAZWY, i odmowy nadal na stderr. **Piec WYKONANYCH kontrol negatywnych.** KN-1: kazdy z pieciu wierszy cofniety na stderr osobno — za kazdym razem czerwienieje dokladnie nowa bramka (`1887/1889 przeszło`, kod 1), komunikatem nazywajacym wiersz i znacznik. KN-1 po stronie C# pokazuje, PO CO ta bramka: cofniecie `[RDZEŃ]` wywraca **jeden** test C# (`Failed: 1, Passed: 588`), a cofniecie `[LIMIT]` **ani jednego** (`Failed: 0, Passed: 589`) — cztery z pieciu tych wierszy nie mialy po stronie C# zadnego straznika. KN-2: wiersz `[ATP]` USUNIETY, a nie przeniesiony — pada `test_every_line_moved_by_6a30_is_on_stdout`, bo sam licznik „zero markerow na stderr" bylby wtedy zielony. KN-3 (drugi kierunek): odmowa `BŁĄD: ` przeniesiona na stdout — pada `test_refusals_still_go_to_stderr`. KN-4: przyrzad oslepiony — wszystkie trzy asercje padaja (`0/3 przeszło`). **KN-5 to bramka, ktora zapalila sie na moim wlasnym progu**: pierwsza wersja kontroli przyrzadu stala na dokladnej liczbie z dnia pomiaru (38) i przy KN-1 zapalala sie NA PROGU (`37 markerow, a ma byc 38`), zanim doszla do asercji o strumieniu — komunikat mowil „przyrzad nie widzi", gdy prawda bylo „wiersz idzie na zly strumien". Prog jest **przepisany, nie dopisany obok**: 30, czyli tyle, zeby odroznic czytnik oslepiony od dzialajacego; liczbe wypisow pilnuje osobna asercja po nazwie. Zestaw narzedzi **1886 → 1889** testow i **99 → 100** modulow, `1889/1889 przeszło, RAZEM 71.678 s`, kod **0**; testy C# **589 → 589** (asercja przepisana i wzmocniona druga, nowej metody nie ma), `Failed: 0, Passed: 589`. Pomiar w `reports/strumienie-wypisu.md`. Poza zakresem, zgodnie z polem: tresc wypisow, to ktore polecenia je produkuja, oraz `BŁĄD:` i `nieznane polecenie:` — one na stderr naleza (6.A16, 6.A27). Zauwazone, nie tkniete: **liczby w bloku pozycji nie zgadzaja sie z przeliczeniem** — „47 na stdout" to liczba WSZYSTKICH wywolan `Console.*WriteLine` na stdout (52), a nie wypisow z markerem (33); piatka na stderr zgadza sie co do sztuki i co do numeru wiersza, a kierunek poprawki byl ten sam przy kazdej z tych liczb. Dalej: pole „Weryfikacja" cytuje `data/keys/L1_A-manual.json`, a katalogu `data/keys` nie ma wcale — zapisy wejsc leza w `tests/data/`; weryfikacje wykonalem na istniejacych plikach. I trzecie: `drive` oraz `replay` bez `--out` pisza telemetrie na stdout, wiec teraz mieszaja sie z nia wiersze `[XXX]`. Zmierzone: ani jedno wywolanie w repozytorium z tej drogi nie korzysta (wszystkie kroki CI podaja `--out`, `compare` czyta pliki). Strumien zalezny od obecnosci `--out` byl by dokladnie tym samym „raz tu, raz tam", ktory ta pozycja likwiduje, wiec go nie wprowadzam; czysty CSV na stdout jako kontrakt (`--out -` albo wymog `--out`) to decyzja wlasciciela i osobna pozycja. Tresc pierwotna: **Piec wypisow informacyjnych idzie na stderr, a te same znaczniki ida takze na stdout** — czytajacy, ktory potokuje stdout, dostaje czesc wierszy `[ODTWORZENIE]` i nie dostaje reszty | zmierzone 07.09.2026 przy 6.A27: przejscie po `Program.cs` bez komentarzy daje 47 wypisow `[XXX]` na stdout i **5** na stderr — wiersze 426 `[RDZEŃ]`, 612 `[LIMIT]`, 712 i 735 `[ODTWORZENIE]`, 725 `[ATP]` — a `[RDZEŃ]`, `[ODTWORZENIE]` i `[ATP]` wystepuja NA OBU strumieniach. Ksztalt wyjscia jest wyrocznia dla logu CI (6.A16, 6.A27) | S |
| 6.A31 | **ZROBIONE (07.09.2026).** Spójność ścieżki `bin/…/netX.Y/` z plikiem projektu jest **pilnowana po każdym commicie**, a nie sprawdzona raz ręcznie. Bramka `tools/tests/test_bin_path_framework.py` (12 testów) **wyprowadza** `TargetFramework` z `src/Sim.Runner/Sim.Runner.csproj` i daje wyrok każdemu wystąpieniu ścieżki `bin/` w `reports/**/*.md` i `docs/**/*.md` na jednym z trzech szczebli: pole „Weryfikacja" bloku i wiersz, który **jest** wołaniem programu, są twardym błędem bez usprawiedliwienia; proza i cytat wyjścia `dotnet build` są pomiarem z datą i dostają usprawiedliwienie z powodem podanym zdaniem. **Pomiar, o który pytało pole „Wyjście": 19 ścieżek w 7 plikach, z tego 14 niezgodnych z `net10.0`, z tego w polu „Weryfikacja" ZERO i w wierszu będącym komendą ZERO — wszystkie 14 to proza albo cytat wyjścia.** Pozycja przewidywała trzy; jest ich czternaście, bo pomiar 6.A26 szukał wyłącznie wołań `Sim.Runner`, a `reports/T-310-physics.md` niesie wiersze rdzenia i projektu testowego bez wiersza runnera. **Sprostowanie do opisu tej pozycji, pokazane pomiarem, nie tylko powiedziane**: `reports/T-311-braking.md:257` i `reports/T-400-first-run.md:235` nie są „komendami" — to wiersze `Sim.Runner -> …dll` z CYTOWANEGO wyjścia `dotnet build`; jedyna prawdziwa komenda ze ścieżką `bin/` w całym drzewie stoi w `reports/linecore-budget.md:91` i jest ZGODNA. Sześć kontroli WYKONANYCH: **KD-1** (komenda `net8.0` wstrzyknięta w pole „Weryfikacja" bloku 6.A31) zgłoszona jako `docs/TASKS.md:4077` na obu twardych szczeblach naraz; **KD-2** (w `reports/linecore-budget.md:91` przestawiona wyłącznie wersja ramki, jeden znak) przenosi ten sam wiersz z „zgodna" do zgłoszenia, a szczebel pola „Weryfikacja" zostaje ZIELONY, bo wiersz w tym polu nie stoi; **KD-3** (cytat wyjścia wstrzyknięty w `reports/coasting.md`) zapala TYLKO szczebel prozy — i to jest cała różnica wobec KD-2; **KU** pokazuje, że ani jedna z pięciu ścieżek `net10.0` nie jest zgłaszana, a mutacja `!=` na `==` przenosi zbiór zgłoszeń dokładnie na te pięć (bramka łapiąca ścieżkę poprawną zostałaby wyłączona w tym samym tygodniu, 6.D27); **KP** (kontrola przyrządu) podmienia `TargetFramework` na `net8.0` i zbiór zgłoszeń przechodzi 14 → 5, bez tego „bramka wyprowadzająca wartość z pliku projektu" byłaby nieodróżnialna od stałej wpisanej z pamięci; **KW** psuje wzorzec o jedną literę (`bin/` → `bim/`) i **trzy testy szczeblowe zostają ZIELONE na zerze dopasowań** — to jedyny powód, dla którego istnieje osobny próg `MIN_PATHS_IN_TREE`. Lista usprawiedliwień jest zamknięta zapadką z obu stron i ma test, że usprawiedliwienie nie przeżyje ścieżki, którą opisuje (wzorzec 6.D29, 6.B34, 6.A26); klucz to (plik, przedrostek ścieżki), nie numer wiersza. Oba raporty z pola „Wejście" dostały **adnotację**, pomiarów nie przeliczono. Zestaw: **1886 → 1898** testów, 100 modułów, kod wyjścia **0**. Pomiar w `reports/ramka-w-sciezce.md`. Zauważone, nietknięte: poza `reports/` i `docs/` nie ma dziś ani jednej takiej ścieżki, a `reports/T-310-physics.md` adnotacji nie dostało, bo nie stoi w polu „Wejście" (CLAUDE.md §4.10). Tresc pierwotna: **Dwie komendy w `reports/` cytuja katalog, ktorego nie ma** — `Sim.Runner/bin/Release/net8.0/MetroBxl.Sim.Runner.dll`, a projekt buduje `net10.0`; nic nie pilnuje, ze komenda cytowana w polu „Weryfikacja" da sie wykonac | zmierzone 07.09.2026 przy 6.A26: `reports/T-311-braking.md:257` i `reports/T-400-first-run.md:235` niosa `net8.0`, `reports/linecore-budget.md:91` niesie `net10.0`, a `<TargetFramework>` to `net10.0`. Pomiary z data sie nie przeliczaja, ale bramka na sciezke w komendzie NIE ISTNIEJE | S |
| 6.A32 | **ZROBIONE (07.09.2026).** Pomiar rozstrzygnal, ze **bramki nie warto stawiac**, i pozycja konczy sie BEZ zmiany w kodzie — wynik dopuszczony wprost przez pole „Skonczone, gdy". Liczba, o ktora prosilo pole „Wyjscie", w rozbiciu: **Python 255** asercji `assert X in Y` „obecnosc bez licznika i bez asercji na brak" (z 595 wszystkich asercji na obecnosc, w 193 funkcjach, 61 plikach), **C# 127** (`StringAssert.Contains` 113, `Assert.IsTrue(… .Contains(…))` 11, `StartsWith` 3; z 254 wszystkich, w 79 metodach, 23 plikach) — razem **382** w 272 funkcjach i 84 plikach. Liczone w ciele WLASCIWEJ funkcji, nie grepem po pliku: Python `ast`-em, C# przez `csharp_test_methods.czlonkowie()` i `maska()`, wiec te same 756 metod testowych, ktore widzi `csharp_assertions.py`. **Rozstrzygnela kontrola przyrzadu, nie rozmiar.** Kazdy z czterech znanych przypadkow przywrocony do stanu przed poprawka i zmierzony w czterech wariantach wyjatkow: definicja z pola „Wyjscie" (bez licznika i bez braku) lapie **0 z 4** przy 382 zgloszeniach; wariant bez wyjatku na licznik 2 z 4 przy 570; bez wyjatku na brak 1 z 4 przy 518; **kazda** asercja na obecnosc 3 z 4 przy **845**, czyli przy 849 istniejacych — to nie bramka, a zakaz `Contains`. Powody, kazdy w kodzie tych testow: 6.A29 przed poprawka ma OBOK slabej asercji i licznik (`Assert.AreEqual(1, result.ExitCode)`) i asercje na brak (`Assert.IsFalse(… .Contains(dobry))`) — oba wyjatki zachodza naraz, a test i tak nie pilnowal niczego; 6.A27 w postaci z 6.A16 ma obok `assert "return 2;" not in body`; 6.A25 ma `Assert.AreEqual(1, result.ExitCode, result.StdOut)`; 6.A26 przed poprawka **nie mial zadnej asercji** — regula stala w komentarzu, wiec zaden wariant przyrzadu liczacego asercje jej nie zobaczy. **Kontrola ujemna, ktorej zadalo pole „Skonczone, gdy", PADA — WYKONANA:** wstrzyknieta KN-2 pozycji 6.A25 (trzy odczyty `known.Positional` zastapione stala `command == "compare" ? 2 : 0`) daje `FAIL test_the_refusal_counts_positional_members_against_the_table` (17/18) przy WSZYSTKICH testach C# zielonych, a ta sama funkcja jest przez klasyfikator **ZGLASZANA** (`obecnosc=2 zgloszonych=2`) — asercja dowiedziona rozstrzygajaca wykonanym pomiarem jest dwiema z 382, i nie da sie jej napisac inaczej, bo „odmowa czyta liczbe z tabeli" nie ma postaci licznika ani postaci asercji na brak. **Prog odpada z osobnego powodu, tez zmierzonego: metryka rusza sie w ZLA strone przy naprawie.** Poprawka 6.A29 podniosla liczbe asercji na obecnosc **1 → 5** (lekarstwem byly cztery kolejne asercje na obecnosc, tylko z iglami `wiersz 5`, `kolumna 3`, `chainage_m`, `nie-liczba`, ktorych nie ma zadna inna odmowa), a poprawka 6.A25 podniosla liczbe **zgloszen** 0 → 2. Rozstrzyga wiec **swoistosc igly**, nie ksztalt asercji — a swoistosc igly jest zdaniem o kodzie produkcyjnym, nie o tekscie testu. Bramka z lista recznie utrzymywana musialaby wymienic 382 pozycje, gdy bramka 6.A29 trzyma tabele **trzech** i jej wlasny raport nazywa to „jej cena". Zestaw narzedzi **1886 → 1886**, `dotnet test` **589 + 210 → 589 + 210** — ta pozycja nie dopisuje ani jednego testu. Przyrzadu NIE zostawiono w `tools/tests/`: klasyfikator pobity 0 do 4 na znanych przypadkach nie jest ani bramka, ani jej biblioteka, a martwy kod w tym katalogu jest osobna usterka (6.B34); definicja jest zapisana w raporcie na tyle, zeby pomiar dal sie powtorzyc. Raport: `reports/audyt-asercji.md`. **Poza zakresem, zgodnie z polem:** ani jedna z 382 asercji nie poprawiona — cztery przypadki dnia sa naprawione u siebie, a ta pozycja dotyczyla WYKRYWALNOSCI. **Zauwazone i niezgloszone jako nowa pozycja** (pozycja wymyslona na miejscu omija format sekcji 6 `CLAUDE.md`): rozstrzyga pomiar, ktorego ta pozycja nie robila — czy igla asercji wystepuje w INNYM komunikacie tego samego programu; jest wykonalny dla **zamknietej rodziny** komunikatow i dokladnie to robi dzis bramka 6.A29, recznie, dla trzech odmow `compare`. Tresc pierwotna: **Nic nie pilnuje, ze asercja jest ROZSTRZYGAJACA, a nie tylko prawdziwa** — cztery przypadki zmierzone w jednym dniu, kazdy inny, wszystkie tego samego kroju | zmierzone 07.09.2026: 6.A25 (KN-2 — odmowa z wlasna stala zostawia wszystkie 584 testy C# zielone), 6.A26 (KN-D — regula pierwszenstwa sceny pilnowana wylacznie komentarzem, 15/15 zielone), 6.A27 (KN-2 — `throw` istnieje, cztery `Console.Error` obok, bramka zielona), 6.A29 (KN-1 — `Contains(sciezka)` spelnione przez odmowe o czym innym). Wspolna cecha: asercja na OBECNOSC czegos dobrego zamiast na BRAK czegos zlego albo na LICZBE | L |
| 6.B40 | **ZROBIONE (07.09.2026).** Znacznik nazwy dziennika ma dziś **czwarty** składnik — odcisk całego przebiegu — więc dwa przebiegi na tym samym commicie i różnej treści dostają **różne** ścieżki: `…-98217a984dee.jsonl` przy drzewie czystym i `…-7c3dae20e6b2.jsonl` po zmianie jednego znaku bez commita, oba WYKONANE i wklejone. Wznowienie na treści niezmienionej nadal trafia w ten sam plik — pokazane dwoma pełnymi przebiegami pod rząd (`2 z 2 już policzonych`, kod 0). Odcisk składa nowa funkcja `odcisk_przebiegu`, osobna dlatego, że tej wartości pyta się **dwóch** rozmówców: nazwa dziennika i nagłówek raportu z 6.B42 — dwa niezależne składania tej samej listy rozjechałyby się po cichu (6.B28). Przebieg pusty ma odcisk **pusty**, nie `sha256("")`, bo tamto byłoby wartością wyglądającą jak zmierzona. **Ostrzeżenie z pola „Wyjście" okazało się nietrafione, i to zmierzone, nie odbite**: pole bało się, że nazwa zmieniana przy każdym zapisie „zamienia wznowienie w fikcję" — a wznowienie przez zmianę treści nie działało **już przed** tą poprawką, bo 6.B32 je odmawiało; poprawka zamienia odmowę na świeży dziennik i nie zabiera ani jednego wznowienia, które wcześniej działało. Dzienników zostaje **jeden na każdy zapisany stan pliku** (pięć zapisów → pięć różnych nazw, wypisane), po **537 B na wpis** (1074 B na 2 wpisy), czyli ok. **420 kB** dla największego realnego zawężenia (`--only tools/track/`, 782 mutacje) — liczba wyprowadzona z rozmiaru wpisu i tak oznaczona. Zestaw **1918 → 1922**, moduł **95 → 99**. **KN-2 znalazła usterkę w moim własnym teście**: odcisk liczony z samych wartości, bez nazw plików, przechodził **99/99**, bo test porównywał słowniki różniące się także multizbiorem wartości — asercja prawdziwa i NIE rozstrzygająca, ta sama klasa co 6.A32 i 6.A29. Po wzmocnieniu (te same wartości, inne przypisanie do nazw) kontrola pada, pokazując dwa **identyczne** odciski. Pomiar w `reports/sciezka-dziennika-z-odciskiem.md`. Tresc pierwotna: **Domyslna sciezka dziennika nie niesie odcisku tresci, wiec po 6.B32 dwa przebiegi na tym samym commicie sciezke DZIELA** — odmowa dziala, ale kaze podac `--journal` recznie | zmierzone 07.09.2026 przy 6.B32. `default_journal` sklada nazwe z trzech rzeczy, a docstring obiecuje „trzy rzeczy, ktore rozstrzygaja, CZEGO przebieg dotyczy" — po 6.B32 tych rzeczy jest cztery, i to jest niezgodnosc miedzy obietnica funkcji a jej dzialaniem | S |
| 6.B41 | **ZROBIONE (07.09.2026).** Pusty zbiór przeglądu nazywa dziś swoją **rzeczywistą** przyczynę, a kod wyjścia wychodzi z tego samego miejsca, co komunikat: `przyczyna_pustego_zbioru` w `tools/tests/mutation_sweep.py` pyta w kolejności etapów zawężania (wybór wywołania → wznowienie → `--limit` → filtr nieosiągalnych) i pierwszy etap, który zszedł do zera, jest przyczyną. **Cztery przyczyny WYKONANE**, każda z wklejonym wyjściem i kodem: wznowienie kompletnego dziennika daje `brak mutacji do sprawdzenia: wznowienie z /tmp/b41/d.jsonl zastało wszystkie 2 już policzone — przebieg zrobił wszystko, o co go proszono` i kod **0** (przebieg pierwszy tego samego polecenia: `rozstrzygniętych 2/2, zabitych 2`, kod 0); filtr nieosiągalnych na `tools/blender/glb_roundtrip.py` dalej mówi o filtrze — `… po odfiltrowaniu nieosiągalnych: filtr odsiał wszystkie 14` i kod **1**; `--only` pasujące do niczego nazywa wzorzec, kod 1; `--limit -2` nazywa limit, kod 1. **Pomiar, o który prosiło pole „Wyjście", i on wybrał kształt poprawki**: miejsc WYKONYWALNYCH polegających na dzisiejszym kodzie 1 jest **ZERO** — w `.github/workflows/` jedyne wystąpienie napisu `mutation_sweep` to komentarz o `run_suite` w `.github/workflows/python-tests.yml`, żaden workflow ani `*.sh` narzędzia nie uruchamia, a oba testy wznowienia (6.B19, 6.B32) chodzą przez `--list`, czyli wychodzą kodem 0 PRZED obiema gałęziami. Miejsc TEKSTOWYCH jest **9**: `reports/` 2, `docs/` 7, `.github/workflows/` 0 — wszystkie zapisy pomiaru, żadne nie jest bramką. Cztery dotyczą gałęzi za filtrem i są historyczne; pięć dotyczy gałęzi golej, a jedno z nich — wiersz 6.B39 — jest **przesłanką pozycji OTWARTEJ**, więc kod 1 zostaje wszędzie poza wznowieniem, a komunikat każdej z czterech przyczyn zaczyna się od tego samego napisu `brak mutacji do sprawdzenia`: te zapisy zostają prawdziwe co do litery. **Rzecz, na której ta poprawka mogła być zbudowana źle, i dlatego ma własną kontrolę**: nieprawdę wypisywała gałąź `if not found:` za filtrem, ale MECHANIZMEM był człon `and not done` w gałęzi wcześniejszej — przy zbiorze opróżnionym przez wznowienie ona milczała i zostawiała odpowiedź jedynej gałęzi, jaka została. Poprawka jest więc w gałęzi wcześniejszej (dziś gołe `not found`), a nie w tej, która kłamała. Dwie WYKONANE kontrole negatywne: **KN-1** (poprawka zdjęta w całości) wywraca **6 z 7** nowych testów i pokazuje samą usterkę — `kod 1` plus komunikat o filtrze przy zbiorze opróżnionym wznowieniem — a siódmy, test drogi filtra, **zostaje zielony i to jest zamierzone**, bo pilnuje przyczyny, która zmienić się nie miała; **KN-2** (pytanie o wznowienie przestawione ZA pytanie o filtr) wywraca **dokładnie te dwa** testy, które kolejność przybijają, i odpowiada trzecią z rzędu nieprawdą (`--limit 0`) — bo przy zbiorze opróżnionym wznowieniem KAŻDE pytanie zadane wcześniej trafia w zero. Testy tej rodziny idą po LICZNIKACH, nie po napisie, bo tylko licznikami da się tę kolejność zmierzyć. `test_mutation_sweep.py` 83 → **90**, zestaw `1910/1910, RAZEM 70.593 s, 100 modułów`, kod 0 (baza zmierzona osobno: `1903/1903, RAZEM 72.045 s`). **Koszt dwoma niezależnymi pomiarami, i one się zgadzają do 0,256 s**: suma median per test **0,632 s** (0,316 s droga filtra + 0,316 s droga wznowienia, oba przez podproces; pięć testów przyrządu po 0,000 s), a mediana modułu 14,884 → 15,772 s, czyli **0,888 s** przy rozrzucie trójki „po" 0,568 s. Pierwsza para pomiarów, na bazie sprzed dwóch rebase'ow, NIE zgadzała sie (0,148 s modułowo przy 0,653 s per test) i została **zastąpiona, nie dopisana obok**: rozjazd zrobił jeden odstrzał w trójce o rozrzucie 0,81 s, a liczba per test była w obu pomiarach ta sama do 0,02 s. Oba testy drogi narzędzia są tanie mimo braku `--list`, bo obie odmowy stoją PRZED `dirty_sources` i przed kalibracją wyroczni; każdy z nich pilnuje tego asercją na brak słowa „kalibracja" w wypisie, żeby przesunięcie gałęzi za kalibrację powiedziało o sobie od razu, a nie przez czas przebiegu. **Bramka zapasu kolejki zielona o włos i nie dzięki mnie, i to jest zmierzone, nie przewidziane**: zamknięcie tej pozycji zdejmuje z kolejki jedną, a na bazie sprzed rebase'u na #377 zostawiało to **11 przy progu 12** i `test_backlog.py` był wtedy czerwony dwoma asercjami; scalenie #376 dopisało pozycje, więc na dzisiejszej bazie zapas mieści się w progu. Kolejka NIE została uzupełniona w tym commicie — to zadanie właściciela, a wymyślanie pozycji na miejscu `CLAUDE.md` §8 zabrania wprost. Pomiar w `reports/pusty-zbior-przegladu.md`. Poza zakresem, zgodnie z polem: kody wyjścia pozostałych odmów przeglądu (2 dla dziennika z innego drzewa, z innej treści i dla brudnych plików). Nie dodano odmowy dla `--limit` z wartością ujemną — nazwanie przyczyny to nie odrzucenie wywołania, a nowa odmowa jest zmianą interfejsu, o którą ta pozycja nie prosiła. Zauważone, nie tknięte: docstring `test_every_real_target_except_the_blender_entry_points_is_reachable` mówi „9 z 44 modułów", a zmierzone dziś **10** nieosiągalnych — dziesiąty to `tools/visual/capture_blender.py`, więc zdanie „wszystkie to wejścia Blenderowe" zostaje prawdą, nieprawdą jest liczba; sama asercja jest na próg i przechodzi. Tresc pierwotna: **Galaz „nie ma czego liczyc" nazywa zla przyczyne i konczy sie kodem 1** — `brak mutacji do sprawdzenia po odfiltrowaniu nieosiagalnych` idzie takze wtedy, gdy filtr nieosiagalnych nie odsial NICZEGO, a zbior jest pusty bo wznowienie policzylo wszystko | zmierzone 07.09.2026 przy 6.B32: drugi przebieg na czystym drzewie daje `wznowienie z ...: 2 z 2 juz policzonych`, potem ten komunikat i **kod 1**. `if not found:` w `main` nie odroznia przyczyn, a dla skryptu CI w petli do skutku kod 1 to roznica miedzy „gotowe" i „awaria" | S |
| 6.B42 | **ZROBIONE (07.09.2026).** Nagłówek raportu niesie dziś **odcisk treści przebiegu** oraz tabelę moduł → odcisk, więc raport z przebiegu `--dirty` jest **odróżnialny** od raportu z drzewa czystego przy tym samym commicie — pokazane WYKONANIEM obu i wklejonymi nagłówkami (`ebd663d489861bb7` wobec `7d1ed5ecd86fd947`, commit w obu `5ae1b52`). **Pomiar rozstrzygnął postać na „jedno ORAZ drugie", nie „jedno z dwojga"**, a próg `MAX_ODCISKOW_W_RAPORCIE = 8` jest z niego wyprowadzony, nie okrągły z gustu: prawdziwych wywołań narzędzia w `reports/` jest **66** (naiwny `grep` daje 165, bo **99** wierszy to proza, nie komenda — ta sama pułapka, którą 6.A31 nazwało dla ścieżek `bin/`, i mój pierwszy licznik w nią wpadł), a **54 z 66** obejmuje **dokładnie jeden** moduł. Założenie pozycji („jeżeli triaż chodzi po jednym module naraz, tabela jest darmowa") jest więc **potwierdzone** — w 82 % wywołań tabela ma jeden wiersz; próg przepuszcza każdy zmierzony przebieg triażowy (najszerszy z zawężeniem to `sweep.py`, dwa moduły) i odsiewa te **7** pełnych, gdzie tabela zajęłaby 63 wiersze. Powyżej progu zostaje odcisk zbiorczy **i zdanie o liczbie pominiętych modułów**, nie milczenie. Odcisk składa `odcisk_przebiegu` z 6.B40 — ta pozycja nie dodaje ani jednej linii arytmetyki, bo tamta funkcja została wydzielona osobno **właśnie na tego rozmówcę** (6.B28). Zestaw **1922 → 1927**, moduł **99 → 104**. Cztery kontrole negatywne WYKONANE, każda na innym zbiorze; **KN-2 jest tą, dla której czwórka istnieje**: odcisk podmieniony na stałą zostawia napis w raporcie i zabiera zależność od treści — test sprawdzający samą obecność frazy przeszedłby, a ten pada, i to jest ta sama klasa co 6.A32 i 6.A29, tym razem **przewidziana**, nie znaleziona po fakcie. `reports/mutation-sweep.md` i `mutation-drift.md` dostały **adnotację**, nie przeliczenie. Pomiar w `reports/odcisk-w-naglowku-raportu.md`. Tresc pierwotna: **Raport przegladu mutacyjnego identyfikuje pomiar samym commitem** — `**Snapshot na commicie:** {commit}`, a po 6.B32 wiadomo, ze commit nie odroznia dwoch przebiegow na tej samej rewizji | zmierzone 07.09.2026 przy 6.B32. Ta sama rodzina co 6.D3: liczba bez drzewa, z ktorego pochodzi, nie da sie odtworzyc. Raport commit podaje — i to jest za malo dokladnie o tyle, o ile za malo go bylo w dzienniku | S |
| 6.D26 | **ZROBIONE (07.09.2026).** Maksimum jest teraz WYPROWADZANE z listy `POMIARY` — pieciu przebiegow z data i kontekstem — a `MARGIN` jest dzialaniem, nie zdaniem. **Zdanie z wpisu, ze „rozrzut hosta nie jest nigdzie zapisany", bylo NIEPRAWDA** i pierwsze czytanie pliku to pokazalo: docstring opisywal kontener dzielony, `ps aux` z rownoleglym `dotnet build` i rozrzut 10,84 s. Zepsute bylo wezsze i gorsze: maksimum wpisane z reki jako jedna liczba z minionej sesji, a margines liczony wobec niej — 107,331 s zmierzone dzis to o **39 %** wiecej niz zapisane 77,04. **Co to realnie przepuszczalo, zmierzone**: obnizenie progu do 100 s przechodzilo wszystkie testy (100 > 77,04, margines 1,298 > 1,2) i dawalo CZERWONE CI na drzewie bez ani jednej usterki; po zmianie jest odmowa. Prog 150,0 **nietkniety** — jego zmiana to decyzja o czulosci bramki. Nowa bramka odmawia, gdy proza podaje mnoznik, ktorego nie daje `MARGIN`, a jej ksztalt to wynik **czterech wlasnych potkniec**, kazdego zlapanego przez inne narzedzie: brala pomiar za mnoznik; skanowala wlasny docstring, ktory te mnozniki WYMIENIA jako przyklady; po wycieciu go przeszla **bez ani jednej asercji** (zlapala to bramka asercji z #139) — wiec sprawdza teraz NARZEDZIE, nie tylko dzisiejszy tekst; a okno zdania urywalo sie na kropce dziesietnej. Cztery kontrole negatywne, z ktorych **KN-4 przed ta zmiana przechodzila**. Pomiar w `reports/zapis-czasu-zestawu.md`. Tresc pierwotna: **`MEASURED_MAX_WALL_S = 77.04` jest nizsze od tego, co maszyna dziś pokazuje** | zmierzone 07.09.2026 przy 6.D25 | S |
| 6.D27 | **ZROBIONE (07.09.2026).** Miedzy nazwa stalej a liczba nie wolno teraz postawic takze `§` ani `#`. **Powod, dla ktorego to nie jest kosmetyka**: bramka swiecaca na poprawnym tekscie zostaje **wylaczona, nie poprawiona** — a obejsciem, ktore zastosowalem przy 6.D26, bylo przepisanie ZDANIA, nie naprawienie przyrzadu. Trzy wiersze mojego wlasnego raportu z tego samego dnia mialy juz ten ksztalt i przechodzily WYLACZNIE przypadkiem: zadna z tych trzech stalych nie trafia do slownika wartosci (jedna usunieta, jedna napisowa, jedna o dwoch wartosciach). Roznica miedzy zdaniem, ktore przeszlo, i tym, ktore padlo, nie lezala wiec w zdaniu. **`#` doszlo z pomiaru, nie z przewidywania**: `kolejka-uzupelnienie.md:42` pisze „`MINIMUM_DOCUMENTED_ITEMS`: sprzezenie, ktore #274" i jest przepuszczane dzis tylko dlatego, ze stoi tam przecinek. Cena zwezenia powiedziana wprost: „`STALA` (§4) to 30,0" przestaje byc twierdzeniem — ten sam wybor, co przy przecinku, i ta sama asymetria, bo przemilczane twierdzenie lapie prog `MINIMUM_CLAIMS`, a falszywy alarm tylko czyjas cierpliwosc. Po zwezeniu bramka sprawdza **15** twierdzen przy progu 10. Dwie kontrole negatywne, z ktorych **KN-2 jest wazniejsza**: dowodzi, ze zwezenie NIE zjadlo tego, po co bramka istnieje — najprostszym sposobem uciszenia falszywego alarmu jest zwezenie wzorca tak, zeby nie lapal niczego, i taka zmiana byla by zielona bez niej. Ta sama para stoi w tresci testu i chodzi przy kazdym przebiegu. Nie tknieto `pkt`, `rozdz.`, `str.` — pomiar daje **zero** wystapien, a wykluczanie form, ktorych nie ma, zwezal oby bramke o twierdzenia, ktorych juz nie sprawdzi. Pomiar w `reports/odsylacz-nie-jest-wartoscia.md`. Tresc pierwotna: **`test_report_claims.py` bierze odsylacz do sekcji za WARTOSC stalej** | zmierzone 07.09.2026 przy 6.D26, gdzie bramka zapalila sie na POPRAWNYM zdaniu | S |
| 6.D28 | **ZROBIONE (07.09.2026).** 674 metody testowe C#, **674** z asercja w tresci, **zero** bez. Dojscie do tego zera wymagalo DWOCH poprawek w czytniku i obie mowia wiecej niz sam wynik. **Pierwsza: czytnik zglaszal wlasna niewiedze jako brak.** Cialo metody C# ma dwie postacie — blok i wyrazenie `=> …;` — a pierwsza wersja znala tylko blok i zglosila `Lista_funkcji_KCV_jest_dokladnie_ta_ktora_podaje_STIB` jako metode bez asercji, choc ona asertuje `CollectionAssert` w ciele wyrazeniowym; gorzej, klamra inicjatora `new[] { … }` byla brana za poczatek bloku, wiec asercja nie trafiala nigdzie. **Druga: pomocnik `Assert*` to asercja** — bez tego wychodzilo PIEC brakow, z czego cztery asertuja przez lokalny `AssertBits`. Sprawdzone tez rozwiazywanie pomocnikow po CIELE, nie po nazwie: **nie daje ani jednej metody wiecej**, wiec zostaje regula prostsza. **Granica postawiona swiadomie**: liczone sa asercje OBECNE w tresci, nie WYKONANE — `assertion_gate` robi to drugie i dlatego zlapal moj test z asercja w petli, do ktorej nic nie weszlo. Slabsza wlasnosc, zapisana w docstringu, nie przemilczana. Cztery kontrole negatywne, kazda na innym trybie awarii; **KN-4 jest najwazniejsza**, bo drzewo ma zero brakow, wiec bramka „zero brakow" jest zielona takze wtedy, gdy czytnik uznaje za asertujaca KAZDA metode — kontrola pozytywna na syntetycznej metodzie bez asercji chodzi przy kazdym przebiegu i to ona odroznia jedno od drugiego. Bramka kosztuje 0,50 s. Liczba 674 zgadza sie z 6.B27: tam 708 atrybutow i 668 objetych ksztaltem; roznica to 34 metody Z ARGUMENTAMI, czyli **6.B28**, nietknieta. Pomiar w `reports/asercje-w-testach-csharp.md`. Tresc pierwotna: **Asercje w testach C# nie sa liczone przez nic** | nazwane jako odlozone wprost przez 6.B27 (#329) | M |
| 6.D29 | **ZROBIONE (07.09.2026), PRZELICZONE PO 6.B28.** Klasyfikacja wszystkich 18 metod „interesujacych" (imiennie, w `reports/galaz-ktora-moze-nie-wejsc.md`): **14** (a) galaz zawsze wchodzona (`WithCulture`/`finally` wola cialo bezwarunkowo; `foreach`/`while` po zbiorze albo liczniku zadanym w tescie; osiem `try`/`finally` **bez** `catch`, wiec wyjatek wywala test glosno, nie omija asercji po cichu), **1** (b) — `DriverActionsTests.PodAutopilotemPomocNazywaKlawiszeKtoreNieDzialaja`, gdzie obie strony `if`/`else` pinuje OSOBNY test tej samej klasy (`KazdaAkcjaStoiPoDokladnieJednejStronie`, `CollectionAssert.AreEqual` na dokladnej liscie), **3** (c) — realna usterka: `RunPlanTests.EveryKnownArgumentIsAcceptedOnItsOwnOrNamesWhatItNeeds`, `RunPlanTests.NoInputThrows`, `TrainProtectionTests.Predkosc_dopuszczalna_jest_odwrotnoscia_krzywej_z_T_311` — w kazdej galaz zalezy od danych produkcyjnych/modelu, a nic w zestawie nie pinuje, ze kiedykolwiek wejdzie. Decyzja o bramce: **NIE budowana** — bramka syntaktyczna zapalilaby sie na 15 z 18 przypadkow POPRAWNYCH, czyli dokladnie 6.D27 („bramka, ktora zapala sie na poprawnym kodzie, zostaje wylaczona, nie naprawiona"); rozroznienie (a)/(b) od (c) wymaga wiedzy semantycznej (czy `try` ma `catch`, czy istnieje osobny test pinujacy warunek), ktorej zaden statyczny czytnik nie ma. **Pierwsza wersja tej pozycji przeliczyla 82/65 z wpisu na 81/64 i zglosila blad czytnika jako nienaprawiony — obie liczby byly zmierzone zepsutym czytnikiem, wlacznie z MOIM WLASNYM prowizorycznym „690".** Niezaleznie od tej sesji ten sam blad zmierzyla i naprawila pozycja **6.B28** (`#348`): `czlonkowie()`/`_koniec_bloku()` dostaly `maska()` (komentarze i literaly zamienione na spacje ZNAK W ZNAK, struktura chodzi po masce), kryjacej sie tresci bylo **27** metod (nie 11 — takze **16** w `ServiceDayTests.cs`, ktorych moj wlasny prowizoryczny czytnik NIE zlapal), a ksztalt bramki objal przy okazji **13** metod `[DataTestMethod]` z argumentami. Po rebase na `main` (`07be80b`) i przeliczeniu na oficjalnym, scalonym czytniku: **727** metod testowych w drzewie (zgodne z grepem po atrybutach — druga, niezalezna metoda), **83** zagniezdzonych (nie 81, nie 82), **65** bezpiecznych, **18** interesujacych (nie 17) — jedna wiecej niz w I wersji, bo `RunnerCommandTests.Zegar_cytuje_cala_wartosc_a_nie_zly_czlon` to NOWA metoda dopisana przez 6.A14 (`#347`) miedzy pierwszym pomiarem a rebase'em, tego samego wzorca `try`/`finally` bez `catch` co siedem jej siostrzanych metod. Zbior 17 metod z I wersji jest niezmieniony co do tozsamosci i klasyfikacji — przyrost jest DOKLADNIE jedna metoda, sprawdzone petla po wszystkich 727, nie zgadniete. `dotnet test`: 565 + 205 = 770 (bylo 557+205, +8 z 6.A14), bez zmian od tej pozycji. `python3 tools/tests/test_all.py`: **1841** testow, 98 modulow, kod 0. **Przy pierwszym przebiegu po rebase kod byl 1**, i to nie z powodu tej pozycji: zapas kolejki spadl z 12 do 11, bo 6.B28 i ta pozycja domknely sie w tym samym oknie. Pierwsza reakcja byla bledna — dopisanie akapitu „Zapas udokumentowany" opisujacego luke — bo `CLAUDE.md` §8 mowi, ze przy zapasie ponizej progu **pierwszym zadaniem jest jego uzupelnienie**, nie udokumentowanie braku. Zapas uzupelniony osobnym commitem (#350, pozycje 6.A25 i 6.B32, 12 -> 14), a akapit zdjety — i zdjecia zazadala ta sama bramka, ktora go wymagala: `FAIL test_the_documented_shortfall_is_written_down_while_it_lasts: zapas doszedl do progu, a plan nadal opisuje luke`. Kontrola w obie strony, wykonana. Tresc pierwotna: **Asercja stojaca WYLACZNIE w galezi, do ktorej moze nic nie wejsc, jest dla bramki 6.D28 nierozroznialna od asercji zawsze wykonywanej** | zmierzone 07.09.2026 przy 6.D28: **82** metody testowe C# maja wszystkie asercje w bloku zagniezdzonym, ale podzial jest ostry — **65** to `for`/`foreach` po zbiorze zadanym w tescie (wykonuja sie), a interesujacych jest **17**: 7 w `try`, 4 w `if`, 2 w `while`, 4 bez rozpoznanego slowa. Bramka zbudowana na samej zagniezdzonosci zapalilaby sie na 65 testach POPRAWNYCH | M |
| 6.D30 | **ZROBIONE (07.09.2026).** Przejscie `czlonkowie()` sciagniete do `csharp_test_methods` (modul nizszy, wiec zaleznosc jest jednokierunkowa i nie ma cyklu), starsze `_poziom_bezposredni` skasowane, test zgodnosci zada **rownosci**, nie pasma. **Sprostowanie wlasnego wpisu**: zdanie „juz raz podaly rozne liczby (670 vs 674)" bylo mylace — tamte 670 wyszlo pod CELOWA mutacja w KN-2 przy 6.D28, a w normalnej pracy czytniki nigdy sie nie rozjechaly (zmierzone przed zmiana: 676 i 676, roznica **zero**). Zepsute bylo wiec co innego i trzeba to nazwac dokladnie: dwa przejscia po tym samym drzewie oraz pasmo `<= 20` postawione nie dlatego, ze 20 cokolwiek znaczylo, ale dlatego, ze majac dwa rozbiory nie umialem postawic rownosci. **Rownosc sama nie wystarcza** — byla by prawdziwa takze przy dwoch przejsciach zgadzajacych sie na dzisiejszym drzewie, dokladnie jak przy 6.D28 — wiec doszedl drugi test patrzacy na KOD: `czlonkowie` w jednym module, drugi je wola, nie kopiuje. Ten test tez wymagal poprawki tej samej co dwa razy dzisiaj: zabranial NAZWY w calym pliku i zapalil sie na komentarzu wyjasniajacym usuniecie; wzmianka nie jest powrotem, wiec warunek dotyczy `def _poziom_bezposredni(`. **KN-3 mierzy wartosc calej pozycji**: rozjazd szesciu metod (670 vs 676) lezy WEWNATRZ starego pasma, wiec test z 6.D28 przepuscilby go bez slowa — i jeszcze czternascie takich. Pomiar w `reports/jeden-czytnik-csharp.md`. Tresc pierwotna: **Dwa czytniki C# chodza po tym samym drzewie i juz raz podaly rozne liczby** | zmierzone 07.09.2026 przy 6.D28 | M |
| 6.B31 | **ZROBIONE (07.09.2026).** `tools/tests/test_dead_constants_csharp.py`: 124 pliki `.cs`, **233** deklaracje `const`/`static readonly`, 193 roznych nazw, **zero** nieczytanych i **pusta** lista uzasadnien. **Wpis mylil sie dwa razy i oba razy pomiar to pokazal**: katalogu `godot/` nie ma (scena lezy w `src/Game/`, czyli w drzewie, ktore bramka 6.B29 juz obchodzila — brak byl brakiem JEZYKA, nie katalogu), a C# pisze stale **PascalCase**, wiec kryterium „wielkimi literami" z tego wpisu nie zlapaloby ani jednej. Jedyna martwa stala — `StationChainagesM`, prywatne pole `RunHeaderTests` — zostala **usunieta, nie usprawiedliwiona**: inaczej niz `LOCATION_STATION` po stronie Pythona nie nalezala do zadnego udokumentowanego zbioru, bo wszyscy jej sasiedzi sa czytani. Oba zestawy C# po usunieciu zielone (552 + 205). Kierunek pomylki wybrany swiadomie: odczyt liczony jako wystapienie identyfikatora, wiec stala o nazwie zbiegajacej sie z metoda wyjdzie jako ZYWA, choc martwa — falszywy negatyw jest tansza pomylka, ta sama asymetria co w 6.B29 i 6.D27. Sprawdzone tez `.tscn`, `.gd`, `*.sh` i `.github/`: zero odczytow, ale warunek zostaje. **Pierwsza wersja bramki kosztowala 20,7 s** — dwie trzecie tego, co 6.B30 wlasnie zdjelo z CALEGO zestawu — bo szla po kazdej nazwie osobno; jedno przejscie z licznikiem daje **0,42 s** i ten sam wynik, sprawdzony po zmianie. Cztery kontrole negatywne, w tym **KN-2** dowodzaca, ze bramka zlapalaby stala usunieta w tym samym commicie, i **KN-4** pokazujaca, po co jest prog na liczbe deklaracji: bez niego literowka we wzorcu dawalaby zielona bramke mierzaca zero. Pomiar w `reports/martwe-stale-csharp.md`. Tresc pierwotna: **Bramka martwych stalych widzi tylko Pythona** | zmierzone 07.09.2026 przy 6.B29 | M |
| 6.B30 | **ZROBIONE (07.09.2026).** Pamiec na `_layout_for` i `_axis_document`: modul **35,1 s -> 11,0 s** (3,2x), caly zestaw **105,3 s -> 76,5 s** przy tej samej liczbie testow (1800) i tym samym werdykcie, trzy przebiegi 76,5 / 76,8 / 76,6 s. **Pytanie, ktore wpis zostawil otwarte, zostalo zmierzone PRZED zmiana**, nie odczytane z kodu: sonda zalozyla pamiec i po KAZDYM z 17 testow liczyla odcisk SHA-256 kazdego zapamietanego obiektu — testow, ktore zmutowaly strukture, jest **zero**. Odczyt pieciu miejsc wolania pokazalby `max`, `min`, `len` i iteracje, ale nie zobaczylby mutacji schowanej w wyrazeniu; odcisk widzi kazda. Docstring mowi, co robic, gdyby to przestalo byc prawda: kopia przy wydaniu albo struktura niezmienna, NIE zdjecie pamieci. **Kryterium „ponizej 10 s" NIE zostalo spelnione i liczba w nim byla bledna** — 10 s bylo moim szacunkiem przy wpisywaniu pozycji, a pomiar pokazuje dno ~11 s: 6,08 s nieusuwalnego wypelnienia pamieci (szesc osi po ~1 s, placi je pierwszy alfabetycznie test dotykajacy wszystkich) plus ~5 s testow na osiach SYNTETYCZNYCH, ktore `_layout_for` nie wolaja wcale. Zejscie ponizej 10 s wymagaloby zmniejszenia tego, co testy licza. Pomiar w `reports/pamiec-ukladu-peronow.md`. Tresc pierwotna: **`_layout_for` w `test_station_layout.py` nie ma pamieci i liczy uklad od nowa przy kazdym wolaniu** | zmierzone 07.09.2026 przy 6.D25: 17 testow, z czego cztery po ~6,0 s, a `_layout_for` jest wolane z pieciu miejsc, kazde w petli po szesciu osiach — czyli ~30 pelnych przebiegow narzedzia na tych samych szesciu plikach | S |
| 6.A19 | **Odmowa `replay --coast-from-m` mówi „nie zna opcji" o opcji, którą projekt zna** — a decyzja właściciela z 07.09.2026 czyni z tej odmowy trwałą WŁASNOŚĆ polecenia, więc komunikat ma podać powód: odtworzenie zapisu wejść nie może dostać nastawy automatu, bo przestałoby być odtworzeniem | rozstrzygnięte 07.09.2026, odczytanie (a) z wiersza w „Czego agent nie ruszy bez decyzji". Ta sama rodzina usterki co 6.A22, i tam już zmierzona: zdanie „nie zna opcji" jest poprawne dla literówki i **mylące** dla nazwy, którą runner zna z innego polecenia. Zakres jest treścią komunikatu i dokumentacją, nie zachowaniem — kod wyjścia i sama odmowa zostają | S |
| 6.B43 | **Ukrycie widoku goniącego kończy się na długości składu, a kadr jest jasny jeszcze przy 96 m** — decyzja właściciela z 07.09.2026 rozciąga pasmo do **110 m**, więc `ChaseCameraAim.Availability` przestaje być funkcją samej długości składu | rozstrzygnięte 07.09.2026. Liczba 110 m pochodzi z pomiaru, nie z gustu: 96 m → **42,0 %** pikseli jaśniejszych niż 0,80 w górnych 60 % kadru, 110 m → **0,0 %**. Seria jest przy tym **niemonotoniczna** (90 m → 0,0 %, 96 m → 42,0 %), więc pozycja ma pasmo domierzyć gęściej, a nie przepisać jeden punkt | M |
| 6.B44 | **Profil pionowy pakietu A nie istnieje, bo trzy z dwunastu stacji mają głębokość, a dziewięć `unknown`** — decyzja właściciela z 07.09.2026 mówi budować z jawną niewiadomą, więc brakuje narzędzia, które czyta `station-depths.csv` i **nazywa dziurę**, zamiast interpolować przez nią | rozstrzygnięte 07.09.2026. Dziś `data/network/station-depths.csv` nie ma w drzewie ani jednego konsumenta poza `tools/tests/test_platform_dimensions.py` — sprawdzone `grep -rln`. Pozycja nie zgaduje ani jednej głębokości: bierze trzy wpisane (`-12,0`, `-20,0`, `-12,0`, wszystkie `estimated`) i dziewięć pustych, a konflikt Schuman 15 m vs 17,42 m zostaje nierozstrzygnięty i tak oznaczony. Czysty Python w `tools/track/`, bez Blendera | M |
| 6.A33 | **ZROBIONE (07.09.2026).** Bramka `tools/tests/test_needle_specificity.py` (11 testów) czyta `src/Sim.Runner/Program.cs` i `tests/Sim.Tests/RunnerCommandTests.cs` jako tekst i dla każdej igły `StringAssert.Contains` liczy, ile komunikatów ją zawiera. Zmierzone na `2ffb0b0`: **68** różnych igieł, **15** niejednoznacznych PRZED, **7** PO — osiem wzmocnionych w teście (`--keys` → `replay wymaga --keys`, `--axis` → `axis wymaga --axis`, `--timetable` → `service-day wymaga --timetable`, `HH:MM:SS` → `czas ma mieć postać HH:MM:SS`, `[BUDŻET]` → `[BUDŻET] oś `, `nie przyjmuje postaci` → wariant z `. Opcję`, `[LINIA]` → `[LINIA] największy błąd zatrzymania`, `[PORÓWNANIE]` → `[PORÓWNANIE] wierszy=`), siedem z wpisem z powodem (`budget`, `step`, `--trains`, `--limit-kmh`, `--at`, `line`, `--steps` — wszystkie są nazwą polecenia albo opcji, a nazwa opcji stoi i w wypisie pomocy, i w każdej odmowie o niej), **zero** przemilczanych. Lista wyjątków zamknięta zapadką z OBU stron (`MAX_JUSTIFIED_NEEDLES = 7`); trzeci szczebel to zapadka na **33** igły, które nie pasują do ani jednego literału, bo runner składa te zdania interpolacją — bez niej najtańszym uciszeniem bramki byłaby zamiana niejednoznaczności na niewidzialność. Zestaw narzędzi **1931 → 1942**, `dotnet test` **589 → 589**. Cztery kontrole WYKONANE: dodatnia (osłabienie `axis wymaga --axis` do `--axis` → `1939/1942`, trzy FAIL wszystkie w nowym module i ani jeden poza nim), dodatnia druga (osłabienie do `line`, czyli do igły Z listy wyjątków → szczebel 1 milczy, zapala się próg KW na `67` igieł zamiast 68, a `dotnet test` pada na treści), skasowany jeden wpis listy (→ zgłoszenie `--steps` i zapadka „stoi wyżej niż lista"), ujemna (mutacja `> 1` na `>= 1` przenosi zbiór zgłoszeń z 0 na **28**, a przy `>= 0` bez filtru listy — na **wszystkie 68**), przyrządu (dopisany do `Program.cs` drugi komunikat z istniejącą igłą podnosi jej licznik 1 → 2 i wprowadza ją do zgłoszeń; ten sam dopisek w KOMENTARZU licznika nie podnosi). **Liczb z treści pierwotnej NIE przeliczam i to jest werdykt, nie zaniedbanie:** kodu tamtego przyrządu nie ma w drzewie, a dziesięć sprawdzonych definicji „komunikatu" (na tym samym `a4a3975`) nie daje `line`=11 przy `budget`=10 — w każdej opartej na literałach `line` wypada najsłabiej z tej czwórki, bo napis `line` stoi w tym pliku w czterech literałach, a `step` w trzynastu. Zbiór **68** igieł jest natomiast identyczny na obu commitach, więc różnica siedzi wyłącznie w definicji komunikatu. Raport: `reports/swoistosc-igly.md`. **Sprostowanie liczb z treści pierwotnej, dopisane 07.09.2026 i ustalone mechanizmem, nie domysłem:** wiersz mówił „16 z 68 igieł niejednoznacznych; najgorsza `line` w 11 komunikatach", a bramka tej pozycji daje **15** przed poprawką i **7** po. Rozjazd nie jest starzeniem się pomiaru — przyrząd, którym powstały liczby pierwotne, był zepsuty. Wzorzec `"((?:[^"\\]|\\.)*)"` na surowym źródle C# paruje cudzysłów **zamykający** jednego literału z **otwierającym** następnego i łapie wszystko pomiędzy; z 209 „komunikatów" **53 (25 %)** zawiera `///`, `return `, `};` albo `Console.`, a `line` „w jedenastu komunikatach" to `line` w komentarzach dokumentacyjnych, w znacznikach `// --- line ---` i w zmiennej `File.WriteAllLines(output, lines)`. Zbiór **68 igieł był policzony poprawnie** — rozjazd siedzi wyłącznie w definicji komunikatu. Rozbiór w `reports/kolejka-uzupelnienie-drugie.md` §3. Tresc pierwotna: **Igła asercji, która występuje w JEDENASTU różnych komunikatach tego samego programu** — `StringAssert.Contains(err, "line")` przechodzi przy odmowie o czymkolwiek. Zmierzone 07.09.2026 na `a4a3975`: **16 z 68** różnych igieł w `RunnerCommandTests.cs` mieści się w więcej niż jednym wielowyrazowym literale z `Program.cs`; najgorsze to `line` (11 komunikatów), `budget` (10), `--limit-kmh` (9) | to jest dokładnie ten pomiar, który `reports/audyt-asercji.md` §7 nazwał **rozstrzygającym** i którego świadomie nie wykonał, bo omijałby format z sekcji 6. Tu nie jest wymyślony na miejscu — 6.A32 wypisało go z nazwy jako osobną pozycję, a liczba stoi wyżej. W przeciwieństwie do 6.A32 rodzina komunikatów jest **zamknięta**: literały odmów `Program.cs` da się wyliczyć | M |
| 6.D32 | **ZROBIONE (07.09.2026).** Bramka `tools/tests/test_field_paths.py` — trzy szczeble, dwanascie testow. **Liczby przeliczone na `2ffb0b0`, nie przepisane**: blokow jest **111** (nie 101), a sciezek **442** w polach „Wejscie", **45** w „Wyjsciu" i **191** w „Weryfikacji" — razem **678** wystapien, 647 unikalnych trojek (blok, pole, sciezka). Nieistniejacych jest **7** i przeliczenie znalazlo **TRZECIA** usterke obok dwoch znanych: **6.D35** cytuje w „Wejsciu" `tests/Sim.Tests/MetroBxl.Sim.Tests.csproj`, a plik nazywa sie `tests/Sim.Tests/Sim.Tests.csproj` — `MetroBxl.Sim.Tests` jest wartoscia `<AssemblyName>` w tym wlasnie pliku. Poprawione sa wszystkie trzy, bo szczebel 1 (pole „Wejscie") nie dopuszcza wyjatku i trzeciej nie bylo jak obejsc, nie lamiac pola „Wyjscie" tej pozycji. **Cztery pozostale sciezki sa POPRAWNE i bramka ich nie zglasza**: (a) plik do wytworzenia w „Wyjsciu" (6.B44, 6.B8), (b) ten sam plik w komendzie, ktora go tworzy (6.B44, „Weryfikacja"), (c) sciezka celowo nieistniejaca (6.B39) — jedyny wpis na liscie wyjatkow, zapadka **1**, a dla pola „Wejscie" wyjatku nie ma i pilnuje tego asercja na kluczach, nie zdanie w komentarzu. **Kontrole WYKONANE, szesc.** KD: literowka w polu „Wejscie" bloku 6.D25 wywraca DOKLADNIE nowa bramke — `1941/1943`, kod 1, ani jeden z pozostalych 101 modulow nie drgnal. KD-2 i KD-3: ta sama literowka uciszana wpisem na liscie wyjatkow **nadal jest zglaszana**, a dodatkowo pada zapadka, a po jej podniesieniu — strukturalny zakaz wyjatku dla tego pola. KU: zdjecie rozroznienia pol PRZENOSI zbior zgloszen **3 -> 7** przed poprawka i **0 -> 4** po niej, a te cztery to dokladnie sciezki poprawne (a), (b), (c); liczba sciezek jest przed i po identyczna (678), bo zadna z trzech poprawek nie wyprowadza sciezki spod wzorca. KW: wzorzec zawezony do `[Q]` zapala prog („0 sciezek w polu Wejscie, a bylo ich 420"), nie zostawia zielonego zera. KW-2 pokazuje, **po co progi sa per pole**: literowka w nazwie jednego pola zabiera 45 sciezek z 678, czyli 6 %, i prog laczny by nie drgnal (633 z 678). KP: alternatywa rozszerzen w zlej kolejnosci (`cs` przed `csproj` i `csv`, `json` przed `jsonl`) produkuje **5 wystapien zgloszen z niczego** — cztery rozne uciete tokeny, wszystkie w polu „Wejscie", zaden nie istnieje. Zestaw **1931 -> 1943** testow i **101 -> 102** modulow, `1943/1943 przeszlo`, kod **0**; liczba blokow bez zmian, wiec `MINIMUM_DETAIL_BLOCKS` zostaje na 111. Pomiar w `reports/sciezki-w-polach-blokow.md`. Poza zakresem, zgodnie z polem: czy komenda z pola „Weryfikacja" DZIALA (6.D33) oraz pola „Skad" i „Zalezy od". **Zauwazone, nietkniete**: cytat `grep` w polu „Skad" bloku 6.D35 niesie te sama zla sciezke i nie mogl dac pokazanego wyjscia `0` (byloby `No such file or directory`, kod 2) — to rodzina 6.D33 i zapis z data; wzorzec sciezki w `tools/tests/test_report_hygiene.py` nie dopuszcza wiodacej kropki, wiec zadna sciezka `.github/…` nigdy nie byla w `reports/` sprawdzana, a tu takich wystapien jest 15 w 10 blokach i wszystkie istnieja. Tresc pierwotna: **Pole bloku może nazywać plik, którego w drzewie nie ma, i nic tego nie zgłasza** — zmierzone 07.09.2026 na `a4a3975` przez 101 bloków: **387** ścieżek w polach „Wejście", **40** w „Wyjściu", **149** w „Weryfikacji". Nieistniejące i będące usterką są **dwie**: **6.B5** cytuje w „Wejściu" `tools/track/profile_scan.py`, a plik leży w `tools/blender/profile_scan.py`; **6.A30** cytuje w „Weryfikacji" `data/keys/L1_A-manual.json`, a katalogu `data/keys` **nie ma wcale** — zapisy wejść leżą w `tests/data/` | pierwsza ścieżka wysyła agenta, który weźmie 6.B5, pod adres, którego nie ma; drugą znalazł niezależnie agent 6.A30 i wykonał weryfikację na plikach istniejących. Bramka musi mieć **trzy** rodzaje wyjątku zmierzone, nie zgadnięte: plik jeszcze niezbudowany w „Wyjściu" (6.B8, 6.B44), ten sam plik w komendzie, która go tworzy (6.B44), i ścieżkę **celowo nieistniejącą**, bo to o nią w teście chodzi (6.B39, `tools/nie-ma-takiego-pliku.py`). `test_report_hygiene.py` pilnuje tego dla `reports/`, dla bloków kolejki nikt | M |
| 6.D33 | **Audyt wykonalności komend z pól „Weryfikacja" objął 82 komendy z 42 bloków, a bloków jest dziś 101 i komend 279** — zmierzone 07.09.2026 na `a4a3975`. 6.D15 nie zostawiło bramki, więc pokrycie audytu **opada samo** z każdym nowym blokiem: dziś to 82 z 279, czyli 29 % | pozycja nie przelicza cudzego pomiaru — 6.D15 jest datowanym audytem i dostaje adnotację. Rzecz jest w tym, że liczba „73 uruchamialne" czytana dziś wygląda jak zdanie o kolejce, a jest zdaniem o 42 blokach z sześćdziesięciu dwóch mniej. Sama zmierzona różnica 82 → 279 rozstrzyga, czy warto bramkę, czy wystarczy adnotacja | M |
| 6.D34 | **`tests/Game.Tests` nie było objęte audytem asercji i raport mówi to wprost** — `reports/audyt-asercji.md` §7: „o tamtych 53 asercjach ten raport nie mówi nic". Zmierzone 07.09.2026 na `a4a3975` szerszym wzorcem: **63** asercje kształtu `StringAssert.Contains` / `Assert.IsTrue(… .Contains(…))` w **7** plikach `Game.Tests`, najwięcej `RunPlanTests.cs` (20) i `TelemetryTrackTests.cs` (19) | cztery przypadki z 07.09.2026 były wszystkie z runnera i z `tools/tests/`, więc wniosek 6.A32 („przyrząd łapie 0 z 4") jest zdaniem o tamtej czwórce, nie o `Game.Tests`. Pozycja nie powtarza przyrządu 6.A32 — bierze **zamkniętą rodzinę** komunikatów `RunPlan` (te same, które 6.C5 policzyło: sześć trybów, sześć literałów) i pyta o swoistość igły, tak jak 6.A33 dla runnera | M |
| 6.D35 | **ZROBIONE (07.09.2026), i pozycja kończy się BEZ bramki — pomiar to rozstrzygnął.** Zdanie §7 w `reports/audyt-asercji.md` **przepisane**, nie dopisane obok: dwa z trzech najliczniejszych plików to testy Godota, trzeci nie — `InputLogTests.cs` leży w `tests/Sim.Tests/`, ma `namespace MetroBxl.Sim.Tests`, a `Sim.Tests.csproj` ma **zero** odwołań do Godota wobec **jednego** w `Game.Tests.csproj`. **Sprzeczność była wewnątrz jednego dokumentu**: rozbicie w §2 tego samego raportu podaje pełne ścieżki i mówi to wprost, więc §7 czytał własne §2 i przepisał je z błędem. Liczby 20 / 19 / 14 **nieprzeliczone** — pomiar z datą. **Bramki nie ma i to jest wynik zmierzony, nie rezygnacja**: przyrząd na wiersze `reports/` nazywające plik `*Tests.cs` razem z markerem projektu daje **5 fałszywych alarmów na 84 trafienia (6 %) i ZERO z jednego prawdziwego** — nie zgłasza wiersza, dla którego powstał, bo `audyt-asercji.md:290` zawiera także `RunPlanTests.cs`, który **naprawdę** jest w `Game.Tests`, a mylnie opisany plik stoi w wierszu następnym. Wszystkie pięć fałszywych alarmów ma tę samą przyczynę: marker stoi w **innej komórce tabeli** niż nazwa pliku. To ta sama arytmetyka i ta sama przyczyna strukturalna, którą 6.A32 zamknęło bez bramki. Wynik dopuszczony wprost przez pole „Wyjście". Zestaw **1931 → 1931**, kod wyjścia 0 — ani jednego nowego testu, i to jest wynik pozycji. **Zauważone i NIE podane jako sprostowanie**: odtworzony klasyfikator gołych asercji daje **114**, nie 127, bo mój wzorzec uznaje za licznik także `Assert.AreEqual(x.Length, …)`; podane jako osobny pomiar o innej definicji, bo dwie liczby z dwóch definicji zlane w jedną są gorsze od obu osobno. Przy okazji proporcja dla 6.D34: w `Game.Tests` gołych jest **53 z 64** (83 %), w `Sim.Tests` **61 z 166** (37 %). Pomiar w `reports/plik-nie-z-tego-projektu.md`. Tresc pierwotna: **Raport w `main` nazywa plik z `tests/Sim.Tests` testem Godota** — `reports/audyt-asercji.md` §7 pisze „Trzy najliczniejsze pliki C# to testy Godota, nie runnera (… `InputLogTests.cs` 14)" | zmierzone 07.09.2026 na `a4a3975`, `ls` i `grep` po pliku projektu. Ta sama rodzina co 6.D4 i 6.D8: zdanie w raporcie, ktorego nikt nie liczy, i ktore przy czytaniu wyglada jak wynik pomiaru | S |
| 6.B45 | **ZROBIONE (07.09.2026), i pozycja myliła się co do własnej przesłanki — pomiar to pokazał.** Wiersz twierdził, że „obie liczby są nieprawdziwe"; sprawdzone na commicie wprowadzającym zdanie: **`ff99d13` (03.09.2026) miał 44 cele i 9 nieosiągalnych**, więc „9 z 44" zgadzało się **co do sztuki w dniu wpisania**. To był pomiar **bez daty**, nie fałsz — inna usterka i inna poprawka. Dalej: `6bbbf37` (04.09) → 55 celów i 10 nieosiągalnych, dziś **63 i 10**. Odpowiedź na pytanie z pola „Wyjście": w cztery dni celów przybyło **19**, a nieosiągalnych **jeden**. Liczby nie są więc przepisane na 10 i 63 — docstring **przepisany tak, że każda liczba ma commit**, a do tego doszła własność **wyprowadzona z drzewa**: zbiór nieosiągalnych równa się dokładnie zbiorowi modułów importujących `bpy` **na poziomie modułu** (10 = 10, zbiory identyczne), co nie wymaga utrzymywania żadnej liczby. Rozróżnienie „na poziomie modułu" jest istotne: tekstowy `grep` daje **15**, a różnica pięciu to dokładnie moduły **wyciągnięte spod `bpy`** w 6.B9 i 6.B13, więc bramka na `grep` zgłaszałaby pięć poprawnych. **Czego równość NIE łapie, i to zmierzone**: `import bpy` dopisany do `lod_paths.py` wchodzi do OBU zbiorów naraz, więc równość zostaje spełniona i próg (11 < 31) też przechodzi — dlatego tych pięciu broni osobna asercja na liście imiennej, utrzymywanej ręcznie, bo „moduł, który kiedyś importował bpy i przestał" nie jest własnością dzisiejszego drzewa. Próg zostaje: równość jest spełniona także przy obu zbiorach pustych, więc sama nie odróżnia sondy widzącej od maszyny z dostępnym `bpy`. Zestaw **1957/1957**, kod 0, liczba testów modułu bez zmian (111). **Kontrola negatywna WYKONANA za CZWARTYM podejściem, a trzy pierwsze były ślepe i dwie zdążyły przekonać mnie do wniosku**: pierwsza wstrzyknęła `import bpy` w miejsce po pierwszym napisie `import `, który w tym pliku stoi **w docstringu** (mówiącym akurat o `import bpy` na poziomie modułu), więc wylądowała **wewnątrz literału**; druga powtórzyła ten błąd; trzecia szukała ostatniego importu najwyższego poziomu i padła asercją `modul nie ma importow na poziomie modulu` — bo `lod_paths.py` nie ma ani jednego, i to jest właśnie powód, dla którego 6.B9 go wyciągnęło. Czwarta, potwierdzona trzema sprawdzeniami (`ast` mówi „na poziomie modułu", import faktycznie pada, kod 1), wywraca asercję listy imiennej ze wskazaniem pliku. Pomiar w `reports/liczba-nieosiagalnych.md`. Tresc pierwotna: **Docstring bramki osiągalności podaje „9 z 44 modułów", a zmierzone jest 10 z 63 — i obie liczby są nieprzybite** | zmierzone 07.09.2026 na `627d184`; znalazł to agent wykonujący 6.B41 i świadomie nie tknął. Asercja stoi na progu (`len(unreachable) < len(targets()) // 2`, czyli 10 < 31), więc przechodzi przy 9, przy 10 i przy 30. **Jakościowa połowa zdania JEST pilnowana** pętlą `"bpy" in reason` i pozostaje prawdziwa — dziesiąty moduł (`tools/visual/capture_blender.py`) też importuje `bpy`. Nieprawdziwe są wyłącznie dwie liczby, i to jest cała pozycja | S |
| 6.B46 | **`collect()` nie ma zawężenia, więc test potrzebujący świeżego przeliczenia płaci za wszystkie 63 cele** — 0,224 s za komplet, gdy potrzebuje jednego modułu | zmierzone 07.09.2026 przy 6.B38. Pamięć z tamtej pozycji kluczuje po odciskach **wszystkich** celów, więc zmiana JEDNEGO pliku unieważnia klucz i wymusza pełne przeliczenie — poprawnie, ale drożej niż trzeba. Kierunek do rozstrzygnięcia pomiarem: zawężenie w `collect()` (klucz per plik) kontra zostawienie jak jest. Blok 6.B38 nazwał to wprost jako osobną pozycję z własnym pomiarem | M |
| 6.D36 | **Trzy obcięcia `hexdigest()` w całym drzewie: dwa przez stałą, jedno przez literał `[:12]`** — a stała `ODCISK_ZNAKOW` obok mówi 16 | zmierzone 07.09.2026 na `627d184`, przejściem po wszystkich `.py` i `.cs`: `mutation_sweep.py:444` i `:943` przez `ODCISK_ZNAKOW`, `:990` przez literał. `test_dead_constants.py` (6.B29) łapie stałą, której nikt nie czyta; **nic nie łapie literału, który powinien być stałą**. Dwie długości tej samej wielkości, żadna liczona z drugiej | S |
| 6.D37 | **ZROBIONE (07.09.2026).** `--only ""` jest dziś **odmową kodem 2**, a nie pełnym przeglądem w milczeniu: pusty wzorzec przepuszczał wszystkie 63 pliki docelowe, czyli **2346 mutacji zamiast 2** dla typowego triażu, **1173×** więcej pracy, przy przebiegu wyglądającym na zawężony. **Pomiar z pola „Wyjście" rozstrzygnął na odmowę, nie na wiersz w wypisie, i pokazał DWIE postacie tej pomyłki o różnym zachowaniu**: w `reports/` stoją dwie prawdziwe pętle podstawiające zmienną do `--only`, a `--only "$m"` (`mutation-drift.md:455`) daje przy pustej zmiennej `--only ''`, kod **0** i pełny przegląd, gdy `--only $f` (`mutation-triage-fizyka.md:173`) gubi argument i argparse **JUŻ odmawia** (`expected one argument`, kod **2**). Druga postać była więc chroniona od zawsze, pierwsza nie była przez nic — i to jest cały powód odmowy. Kod **2**, nie 1: to błędne wywołanie, a nie „nie ma czego liczyć" (tam należą 6.B39 i 6.B41), i ten sam kod daje argparse dla drugiej postaci — jedna pomyłka, jeden kod, niezależnie od tego, czy cudzysłów ocalał. Warunek to `"--only" in sys.argv and not args.only`, a **nie** sama fałszywość `args.only`, bo obie sytuacje dają pusty napis, a tylko jedna jest pomyłką; przebieg bez `--only` (wołany w `reports/` **siedem** razy) zostaje niezmieniony. Zestaw **1931 → 1934**, moduł **108 → 111**, kod wyjścia 0. Trzy kontrole negatywne WYKONANE, każda na innym zbiorze; **KN-2 (odmowa zbyt szeroka, na samej fałszywości) pada na DOKŁADNIE JEDNYM teście** — tym, który pilnuje drogi pełnego przebiegu, i bez niego odmowa zablokowałaby wszystkie siedem wywołań. **KN-3 powtórzona**, bo pierwsza wersja zmieniła przy okazji treść komunikatu i nie izolowała kodu. Pomiar w `reports/puste-zawezenie.md`. Tresc pierwotna: **`--only ""` idzie drogą BEZ zawężenia i nic tego nie mówi** — skrypt wołający `--only "$WZORZEC"` z pustą zmienną dostaje pełny przegląd zamiast odmowy | zmierzone 07.09.2026 na `627d184`: pusty napis jest falsywy dla `if args.only`, więc gałąź zawężenia nie wchodzi wcale. Skutek jest liczbowy: **2346 mutacji zamiast 2** dla typowego triażu jednego modułu, czyli **1173×** więcej pracy, bez ani jednego słowa w wypisie. Ta sama rodzina co 6.B39 — przebieg, który wygląda poprawnie, robiąc co innego — tylko w drugą stronę: tam zbiór był pusty, tu jest pełny | S |
| 6.D38 | **Nagłówek `reports/mutation-sweep.md` niesie commit, datę i nazwę gałęzi w jednym wierszu, inaczej niż wzór z 6.D3** — `**Snapshot na commicie:** \`66b8301\` (\`main\`, 04.09.2026)` | zauważone 07.09.2026 przy 6.B42. Bramka higieny to przepuszcza, bo szuka SHA w grawisach i daty osobno, a oba tu są — więc **nie jest to brak informacji, a rozjazd kształtu**. Do rozstrzygnięcia pomiarem: ile z 128 raportów ma nagłówek niezgodny ze wzorem i czy wzór jest w ogóle jeden. Jeżeli okaże się, że wzorów jest kilka i wszystkie czytelne, pozycja kończy się adnotacją, nie ujednolicaniem | S |
| 6.D41 | **ZROBIONE (07.09.2026). Bramka budżetu kroku porównywała z progiem pomiar, o którym SAMA wypisywała, że jest niestabilny** — kolumna `rozstęp_%` była parsowana i drukowana, ale **nigdy nie asertowana**. Zmierzone na runnerze `woogitsu-host-08` przy dwunastu jobach naraz: `koszt kroku 16.022 us przekracza prog 8.000 us` przy `rozstep powtorzen 115.9 %`. Na **tej samej treści kodu**, na maszynie niezajętej, cztery przebiegi dały **4,213–4,364 µs przy rozstępie 1,9–3,7 %** — czyli rdzeń nie zwolnił czterokrotnie, tylko maszyna nie dała się zmierzyć, a bramka nazwała to regresem wydajności. Dwa różne stany świata („rdzeń zwolnił" i „nie umiem tego zmierzyć") dawały **jeden komunikat i jeden kod wyjścia**, a pierwszy z nich każe szukać regresu w kodzie, którego nie ma. Poprawka: `spread_pct_max` **wstrzymuje porównanie** z progiem czasu (warunki OBSADY zostają sprawdzane zawsze, bo liczba składów na planie nie zależy od obciążenia) i daje **osobny kod wyjścia 3**. Granica **50 %** jest wyprowadzona z czterech pomiarów, nie zgadnięta: 22,5 % to najwyższy rozstęp z kalibracji progu 8,0 µs (`reports/linecore-step-budget-gate.md`, 06.09.2026), 17,0 % niesie atrapa `ZIELONY` w module testowym, 1,9–3,7 % maszyna niezajęta, 115,9 % maszyna obciążona — czyli 2,2× powyżej najwyższego udokumentowanego pomiaru zielonego i 2,3× poniżej zaobserwowanego niemierzalnego; wartość **tymczasowa, do zaciśnięcia** przy większej liczbie pomiarów z samych runnerów. Progu 8,0 µs **nie tknięto**. Sześć nowych testów, w tym asercja **wyprowadzona** żądająca, żeby granica leżała powyżej obu udokumentowanych pomiarów zielonych i poniżej zaobserwowanego niemierzalnego. Cztery kontrole negatywne WYKONANE: strażnik zdjęty (2 FAIL), granica zaniżona do 10 % (5 FAIL, w tym na **atrapie zielonej** — dowód, że za ciasna granica zamienia bramkę w generator fałszywych alarmów, 6.D27), granica podniesiona do 200 % (4 FAIL), kod niemierzalności zrównany z kodem przekroczenia (1 FAIL). **Przy okazji znaleziona dziura w mojej własnej procedurze kontroli:** przywrócenie pliku przez `cp` po mutacji o **identycznej długości** (`= 3` → `= 1`) w tym samym oknie rozdzielczości mtime pozostawia nieświeży `.pyc`, więc weryfikacja po przywróceniu czyta STARY bajtkod — złapane, bo sprawdzam stan po przywróceniu, i od teraz kontrole czyszczą `__pycache__`. Raport: `reports/rozstep-budzetu-kroku.md` | S |

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
  `tools/blender/profile_scan.py` i `tools/blender/placement.py` (`marker_clearances`),
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

##### 6.A16 · Ujednolicenie kodów wyjścia — decyzja właściciela

- **Skąd:** **decyzja właściciela z 06.09.2026.** Cztery pozycje po kolei zatrzymały się
  na tej samej granicy i wypisały ją jako poza zakresem: 6.A10 (#302), 6.A11 (#307),
  6.A13 (#313) i 6.D20 (#312). Każda przybiła stan testem, zamiast go poprawić —
  bo wybór między 1 a 2 nie należał do pozycji, która ma opisać zastane zachowanie.
  Zmierzone: `Compare` zwraca **2** przy złej liczbie argumentów (`Program.cs`, gałąź
  `compare wymaga dwóch plików`), a wszystkie odmowy przechodzące przez wspólny handler
  `ArgumentException`/`FormatException` zwracają **1**.
- **Wejście:** `src/Sim.Runner/Program.cs` (`Compare`, `Unknown`, sprawdzenie
  `args.Length == 0`, wspólny handler wyjątków w `Main`),
  `tests/Sim.Tests/RunnerCommandTests.cs` — **trzy** testy przybijają dziś dwójkę:
  `Compare_bez_dwoch_plikow_konczy_sie_kodem_dwa`,
  `Nieznane_polecenie_konczy_sie_kodem_dwa`,
  `Brak_argumentow_w_ogole_konczy_sie_kodem_dwa`.
- **Wyjście:** `compare` bez dwóch plików kończy się kodem **1**, jak każda inna odmowa
  argumentowa. Kod **2** zostaje wyłącznie dla „nie wiem, co uruchomić": nieznane
  polecenie i brak argumentów — obie te ścieżki zostają nietknięte. Pierwszy z trzech
  testów wyżej zmienia oczekiwanie na 1 **razem ze zmianą kodu**, dwa pozostałe zostają
  bez zmian i to jest ich nowa rola: pilnują, że dwójka nie rozlała się z powrotem.
- **Weryfikacja:**
  ```bash
  dotnet run --project src/Sim.Runner -c Release -- compare
  dotnet run --project src/Sim.Runner -c Release -- nie-ma-takiego-polecenia
  dotnet test tests/Sim.Tests
  ```
  Oczekiwane: pierwsza komenda kod **1**, druga kod **2**, zestaw rdzenia zielony.
- **Skończone, gdy:** w `Program.cs` nie ma już `return 2` poza `Unknown()` i gałęzią
  pustych argumentów — sprawdzone grepem i wypisane w raporcie — a kontrola negatywna
  WYKONANA (przywrócona dwójka w `compare`) wywraca dokładnie jeden test.
- **Poza zakresem:** wprowadzanie **trzeciej** wartości kodu wyjścia. Właściciel wybrał
  wariant dwuwartościowy, nie rozdzielenie znaczeń — ten drugi był osobną opcją i nie
  został wybrany.
- **Zależy od:** #302, #307, #312, #313 (wszystkie scalone).

##### 6.D23 · Manifest proweniencji pisany tylko przy zmianie treści — decyzja właściciela

- **Skąd:** **decyzja właściciela z 06.09.2026**, wariant **C** z `reports/zapisy-do-data.md`
  §3, wybrany spośród czterech wypisanych tam z kosztem każdego. 6.D12 (#295) zmierzyła
  problem i świadomie go nie rozstrzygnęła, 6.D16 (#311) poprawiła zdanie w dokumencie,
  które dla dwóch miejsc było nieprawdą. Zmierzone dziś na tym drzewie:
  `provenance.diff_manifests()` **istnieje** (`tools/data/provenance.py`) i porównuje
  `content_sha256`, a żaden z dwóch fetcherów go nie woła — `grep` po nazwie w obu
  plikach nie daje ani jednego trafienia.
- **Wejście:** `tools/track/fetch_gtfs.py`, `tools/track/fetch_stib_shapes.py`,
  `tools/data/provenance.py` (`diff_manifests`, `utc_now_iso`), `tools/tests/test_fetchers.py`
  (w tym testy `--offline` z 6.D14, #315), `reports/zapisy-do-data.md` §3 i §4.
- **Wyjście:** oba fetchery wczytują istniejący manifest przed zapisem i **nadpisują go
  tylko wtedy, gdy `content_sha256` się różni**. Gdy treść jest ta sama — plik zostaje
  nietknięty, a proces wypisuje na konsolę, że sprawdził i nie było zmian. Ten komunikat
  nie jest ozdobą: dziś jedynym sygnałem „pobranie się odbyło" jest `git diff`, a wariant C
  ten sygnał zabiera.
- **Weryfikacja:**
  ```bash
  python3 tools/track/fetch_gtfs.py --offline --out build/gtfs/stib_gtfs.zip
  git status --short data/
  python3 tools/tests/test_all.py
  ```
  Oczekiwane: `git status --short data/` **puste** po dwóch przebiegach z rzędu na
  niezmienionym źródle, a na konsoli komunikat o braku zmian.
- **Skończone, gdy:** dwa przebiegi z rzędu na tym samym źródle zostawiają `data/`
  bajt w bajt nietknięte — **wykonane i wklejone, oba** — a kontrola negatywna WYKONANA
  (podmieniony `content_sha256`) pokazuje, że manifest JEST wtedy nadpisywany. Testy
  `--offline` z #315 nadal zielone.
- **Poza zakresem:** **zmiana `CLAUDE.md` §4.6.** Właściciel wybrał wariant zmieniający
  narzędzia, nie regułę — `data/` zostaje tylko do odczytu bez żadnego wyjątku.
  Poza zakresem także wariant D (przeniesienie `retrieved_at` poza plik śledzony) i
  rozstrzyganie, czy zmiana innych pól manifestu bez zmiany treści ma nadpisywać plik:
  to drugie jest pytaniem, które wariant C dopiero otwiera, i należy do właściciela.
- **Zależy od:** #295, #311, #315 (wszystkie scalone).

##### 6.D24 · Brakująca biblioteka natywna runtime'u — mechanizm niezbadany

- **Skąd:** 6.D21 wykonała **sześć** niezależnych prób odtworzenia zawieszenia Godota
  bez wyjścia na stdout i **żadna go nie odtworzyła** — każda skończyła się w 0,2–0,9 s
  z komunikatem i kodem wyjścia. Ta pozycja nazwała przy tym jeden mechanizm, którego
  celowo nie tknęła, bo jest inny niż „brakujący assembly" z opisu usterki: brak
  **biblioteki natywnej samego runtime'u** (`libhostfxr.so`, `libcoreclr.so`).
- **Wejście:** `reports/6d21-objaw-nieodtworzony.md`, `docs/23-environment.md` §4.1,
  `$DOTNET_ROOT/host/fxr/`, `$DOTNET_ROOT/shared/Microsoft.NETCore.App/`, `doctor.sh`
  (sonda `godot .NET hostfxr` z #305).
- **Wyjście:** pomiar zachowania Godota przy przemianowanej albo obciętej bibliotece
  natywnej — z limitem czasu, wklejonym wyjściem (albo jego brakiem) i kodem wyjścia —
  oraz adnotacja w `docs/23-environment.md`, jeżeli objaw da się tą drogą odtworzyć.
- **Weryfikacja:**
  ```bash
  bash doctor.sh
  python3 tools/tests/test_all.py
  ```
  plus **wykonana** próba z `timeout`, z wypisanym czasem i kodem wyjścia każdego wariantu.
- **Skończone, gdy:** dokument mówi o tym mechanizmie wyłącznie to, co zostało zmierzone,
  a jeżeli objaw nadal jest nieodtwarzalny — mówi to wprost, z datą, tak samo jak 6.D21.
  **Nieodtworzenie jest pełnoprawnym wynikiem tej pozycji**, nie jej porażką.
- **Poza zakresem:** trwałe uszkodzenie instalacji .NET albo Godota poza repozytorium.
  Każda podmieniona biblioteka wraca na miejsce, a raport podaje sumę kontrolną albo
  rozmiar jako dowód przywrócenia — tak jak zrobiła to 6.D21.
- **Zależy od:** 6.D21 (w locie).

##### 6.A17 · Człon obcięcia w bilansie energii

- **Skąd:** zmierzone 06.09.2026 przy 6.A6 (#323). Wypis `[ENERGIA]` przejazdu L1_A bez
  wybiegu podaje `obcięcie = 96 889 720,4 J` przy `E_trakcji = 142,4515 kWh`, a bilans
  domyka się **względnie do 2,147E-015**. Liczba nie jest więc błędem zamknięcia — jest
  osobną, nazwaną pozycją bilansu, wielkości **~27 kWh, czyli 19 % pracy trakcji**,
  i nikt jej nie śledzi. 6.A6 nazwała ją miarą tego, jak długo skład wisi na limicie
  z pełnym nastawnikiem, ale tego nie zmierzyła — to jest praca tej pozycji.
- **Wejście:** `src/Sim/` (miejsce, w którym powstaje człon obcięcia — bilans energii
  z 6.A5), `src/Sim.Runner/Program.cs` (`LineCommand`, wypis `[ENERGIA]`),
  `reports/energy-balance.md` (6.A5), `reports/coasting.md` (6.A6),
  `tests/Sim.Tests/` (testy bilansu energii).
- **Wyjście:** raport wiążący człon obcięcia z czasem spędzonym na limicie — per odcinek,
  nie jedną liczbą na całą oś — plus test przybijający tę zależność, jeżeli pomiar
  pokaże, że jest monotoniczna.
- **Weryfikacja:**
  ```bash
  dotnet run --project src/Sim.Runner -c Release -- line --axis data/track/L1_A.json \
      --limit-kmh 72 --exchange-s 20 --trace build/energia.csv
  dotnet run --project src/Sim.Runner -c Release -- line --axis data/track/L1_A.json \
      --limit-kmh 50 --exchange-s 20 --trace build/energia-50.csv
  dotnet test tests/Sim.Tests
  ```
  Oczekiwane: przy niższym limicie człon obcięcia **rośnie albo maleje w sposób, który
  raport tłumaczy** — dwie liczby obok siebie, nie jedna.
- **Skończone, gdy:** raport podaje człon obcięcia dla co najmniej **dwóch** limitów
  prędkości i tłumaczy kierunek zmiany mechanizmem z kodu, a nie domysłem. Jeżeli
  zależność nie jest monotoniczna, pozycja mówi to wprost i nie dopisuje testu.
- **Poza zakresem:** zmiana modelu oporów, krzywej hamowania i sposobu liczenia bilansu.
  Ta pozycja **mierzy** człon, który już tam jest.
- **Zależy od:** #323 (6.A6).

##### 6.A18 · Wybieg widzi jedno polecenie z trzech

- **Skąd:** 6.A6 (#323) dopisała `--coast-from-m` do polecenia `line` i **świadomie nie
  wyszła poza nie**, wypisując to jako niezrobione. Ale `LineRunSettings` czytają trzy
  polecenia: `line`, `budget` i `replay`. Skutek jest konkretny: pomiar kosztu kroku
  przy włączonym wybiegu (czyli 6.D2 z wybiegiem) i odtworzenie przejazdu z wybiegiem
  przez `replay` są dziś **niewykonalne**, bo nie ma jak podać tej nastawy.
- **Wejście:** `src/Sim.Runner/Program.cs` (`LineCommand`, `Budget`, `Replay`,
  tabela `KnownOptions`), `src/Sim/Line/LineCore.cs` (`LineRunSettings`),
  `tools/tests/test_runner_options.py` (bramka zgodności tabeli z kodem),
  `tests/Sim.Tests/RunnerCommandTests.cs`.
- **Wyjście:** `--coast-from-m` przyjmowane przez `budget` i `replay`, w tabeli
  `KnownOptions` przy obu, z testem kodu wyjścia dla każdego.
- **Weryfikacja:**
  ```bash
  dotnet run --project src/Sim.Runner -c Release -- budget \
      --axis data/track/L1_A.json \
      --signalling data/design/signalling/classic-2026.json \
      --limit-kmh 72 --exchange-s 20 --headway-s 10 --steps 200000 \
      --trains 9 --coast-from-m 250
  dotnet test tests/Sim.Tests
  ```
  Oczekiwane: kod 0 i wypis `[BUDŻET]`; dziś ta sama komenda kończy się odmową
  `polecenie budget nie zna opcji --coast-from-m`.
- **Skończone, gdy:** oba polecenia przyjmują nastawę, bramka zgodności tabeli
  z kodem jest zielona, a kontrola negatywna WYKONANA (opcja zdjęta z tabeli przy
  jednym z nich) wywraca dokładnie ten jeden wpis.
- **Poza zakresem:** **wybór profilu jazdy dla gry.** 250 m to wartość pomiarowa
  z 6.A6, nie praktyka STIB, i ta pozycja jej nie utrwala jako domyślnej.
- **Zależy od:** #323 (6.A6).

##### 6.B25 · Martwa stała i nazwa zajęta drugi raz przy innej wartości

- **Skąd:** znalezione przy 6.B5 (#324), potwierdzone grepem 06.09.2026:
  `MIN_RADIUS_M = 20.0` w `tools/blender/clearance.py:42` i `MIN_RADIUS_M = 90.0`
  w `tools/tests/test_packages.py:28`. Ta sama nazwa, **inna wartość, inne znaczenie**,
  obie żyją obok siebie. Pierwsza z nich nie jest czytana przez żaden kod — a
  `tools/tests/test_clearance_profile.py:1832` opisuje ją w docstringu jako
  obowiązującą, więc czytający ma dziś dwa sprzeczne sygnały.
- **Wejście:** `tools/blender/clearance.py`, `tools/tests/test_packages.py`,
  `tools/tests/test_clearance_profile.py` (docstring), `tools/tests/test_clearance.py`.
- **Wyjście:** martwa stała usunięta albo — jeżeli pomiar pokaże, że coś ją jednak
  czyta — dopisany test na to. Nazwa w `test_packages.py` przemianowana tak, żeby
  mówiła, czego dotyczy (próg pakietu, nie promień skrajni), a docstring poprawiony.
- **Weryfikacja:**
  ```bash
  grep -rn "MIN_RADIUS_M" tools/ src/ docs/
  python3 tools/tests/test_all.py
  ```
  Oczekiwane: grep pokazuje **jedną** nazwę w jednym znaczeniu, zestaw zielony.
- **Skończone, gdy:** w repozytorium nie ma dwóch stałych o tej samej nazwie i różnych
  wartościach — sprawdzone grepem, którego wynik jest wklejony — a docstring nie
  odsyła do stałej, która przestała istnieć.
- **Poza zakresem:** zmiana **wartości** progu 90 m w `test_packages.py`. To jest próg
  akceptacji pakietu i jego wybór nie należy do porządkowania nazw.
- **Zależy od:** #324 (6.B5).

##### 6.B29 · Stała, której nikt nie czyta, nie jest przez nic zgłaszana

- **Skąd:** 6.B25. `MIN_RADIUS_M = 20.0` stało w `tools/blender/clearance.py`
  **od swojego pierwszego commita** (#50, 01.09.2026), nieczytane przez nic — i zdążyło
  w tym czasie zostać zacytowane w docstringu `test_clearance_profile.py` jako granica
  obowiązująca. Bramka z 6.B25 (`tools/tests/test_constant_names.py`) tego **nie łapie**
  i jej kontrola negatywna KN-1 pokazała to wprost: łapie **kolizję** nazw, nie
  **martwotę**. Sama stała przywrócona do `clearance.py` nie tworzy kolizji, bo drugiej
  definicji już nie ma.
- **Że jest wykonalna, jest zmierzone, a nie założone:** przejście `ast` po `tools/`
  i `src/` daje **696** stałych modułowych o nazwie wielkimi literami i **jedną**
  nieczytaną nigdzie w drzewie — `LOCATION_STATION` w `tools/track/normalize_stops.py`.
  Ta jedna jest **uzasadniona**: stoi w trójce `LOCATION_STOP` / `LOCATION_STATION` /
  `LOCATION_ENTRANCE`, spisującej wyliczenie `location_type` z GTFS; dwie wartości są
  czytane, trzecia nie, a jej usunięcie zepsułoby czytelność zbioru zamiast zdjąć
  ciężar. Żadna z nieczytanych nie występuje też w `*.sh` ani w `.github/`.
- **Wejście:** `tools/tests/test_constant_names.py` (precedens kształtu: zapadka
  z uzasadnieniami, pilnowana w obie strony), `tools/track/normalize_stops.py`,
  `reports/nazwa-zajeta-drugi-raz.md` §6.
- **Wyjście:** bramka zgłaszająca stałą modułową, której żaden moduł w `tools/` ani
  `src/` nie czyta, z listą uzasadnień o **jednym** wpisie na dziś. Odczyt liczony
  przez `ast` — po `Name` w kontekście `Load` i po `Attribute`, bo stałą czyta się też
  jako `M.NAZWA` — a nie grepem, który złapałby nazwę w komentarzu i w napisie.
  Sprawdzone muszą być także `*.sh` i `.github/`, bo skrypty CI wołają moduły przez
  `python3 -c` i stała czytana wyłącznie stamtąd nie jest martwa.
- **Weryfikacja:**
  ```bash
  python3 tools/tests/test_all.py
  ```
  plus wypis: ile stałych modułowych jest w drzewie, ile nieczytanych i które.
- **Skończone, gdy:** bramka jest zielona na dzisiejszym drzewie, a kontrola negatywna
  WYKONANA — stała bez odczytu, dopisana do dowolnego modułu, zapala ją i **nazywa
  plik oraz nazwę**. Druga kontrola, też WYKONANA: wpis na liście uzasadnień, który
  przestał opisywać stałą martwą, również zapala bramkę, żeby lista nie gniła.
- **Poza zakresem:** funkcje i klasy nieużywane. To jest znacznie szersza praca —
  wymaga rozstrzygnięcia, czym jest publiczne API modułu — a ta pozycja dotyczy stałych
  modułowych o wartości prostej, czyli dokładnie tego kształtu, który przeżył w #50.
  Poza zakresem także usuwanie `LOCATION_STATION`.
- **Zależy od:** 6.B25.

##### 6.B26 · Zapas skrajni liczony wobec ściany, której może nie być

- **Skąd:** zmierzone 06.09.2026 przy 6.B5 (#324). Najciaśniejszy łuk pakietu D leży
  **0,0–0,2 m** od przedziału, którego OSM nie widzi jako tunel, podczas gdy na
  pozostałych pięciu osiach ta odległość wynosi **co najmniej 314 m**. Różnica jest
  o trzy rzędy wielkości, więc nie jest szumem pomiaru. Zapas **+0,7043 m** podany dla
  tego łuku jest więc liczony wobec ściany, o której nie wiadomo, czy istnieje.
- **Wejście:** `data/track/L5_D.json` i jego `*.provenance.json`,
  `reports/surface-vs-tunnel.md` (81 punktów sprzecznych między UrbIS a OSM, wszystkie
  w D i F), `tools/blender/clearance.py` (`--scan` z #324), `reports/M7-curve-clearance.md`,
  `docs/07-open-data-research.md` (hierarchia źródeł).
- **Wyjście:** raport rozstrzygający, czy ten konkretny odcinek jest w tunelu — po
  hierarchii źródeł, nie po jednym z nich — albo stwierdzający, że **na dostępnych
  danych rozstrzygnąć się nie da**, i wtedy zapas +0,7043 m zostaje w raportach
  oznaczony jako warunkowy.
- **Weryfikacja:**
  ```bash
  python3 tools/tests/test_all.py
  ```
  plus wypis: kilometraż łuku, odległość do najbliższego przedziału tunelowego w każdym
  ze źródeł osobno, i to samo dla łuku porównawczego z osi, gdzie odległość jest duża.
- **Skończone, gdy:** raport podaje odpowiedź **z nazwanym źródłem** albo mówi wprost,
  że jej nie ma — i w tym drugim przypadku każdy zapas liczony na tym odcinku jest
  oznaczony jako warunkowy tam, gdzie jest podany. `CLAUDE.md` §4.1: czego nie da się
  potwierdzić, tego się nie zgaduje.
- **Poza zakresem:** **zmiana `data/track/L5_D.json`.** `data/` jest tylko do odczytu,
  a poprawianie przebiegu osi na podstawie rozstrzygnięcia o tunelu byłoby osobną,
  znacznie większą pracą — i wymagałoby decyzji właściciela.
- **Zależy od:** #324 (6.B5).

##### 6.B27 · Test C# bez `[TestMethod]` jest niewidzialny

- **Skąd:** znalezione 06.09.2026 przy 6.A16, **na moim własnym commicie**. Przepisując
  komentarz nad testem, atrybut `[TestMethod]` został wycięty razem z nim. Metoda
  została w pliku, miała asercje, wyglądała jak test — i nie była uruchamiana. Zestaw
  C# przeszedł **545/545 mimo obecnego błędu**; objawem nie był żaden `FAIL`, tylko
  liczba testów o jeden mniejsza i mutacja, która nie miała czego wywrócić.
- **Wejście:** `tests/Sim.Tests/` (wszystkie pliki), `tools/tests/assertion_gate.py`
  jako precedens po stronie Pythona (bramka z #139 liczy asercje i nie pozwala testowi
  „przejść" bez ani jednej), `tools/tests/test_xml_doc_blocks.py` jako precedens bramki
  czytającej `src/` bez `dotnet`, `reports/kody-wyjscia-runnera.md` §5.
- **Wyjście:** bramka w `tools/tests/`, która czyta pliki `tests/**/*.cs` jako tekst
  i zgłasza **publiczną metodę bezargumentową w klasie z `[TestClass]`, która nie ma
  ani `[TestMethod]`, ani `[DataTestMethod]`, ani nie jest pomocnikiem** — kryterium
  pomocnika ma wynikać z pomiaru na dzisiejszym drzewie, nie z założenia.
- **Weryfikacja:**
  ```bash
  python3 tools/tests/test_all.py
  ```
  plus wypis: ile metod w `tests/` ma `[TestMethod]`, ile jest pomocnikami i ile — jeśli
  jakiekolwiek — wpada w kategorię „wygląda jak test, nie jest uruchamiane".
- **Skończone, gdy:** bramka jest zielona na dzisiejszym drzewie, a kontrola negatywna
  WYKONANA (atrybut zdjęty z jednego istniejącego testu) ją zapala i **nazywa ten test
  z imienia**. Bramka nie może wymagać `dotnet`: zestaw narzędzi chodzi tam, gdzie
  `doctor.sh` przepuszcza brak SDK.
- **Poza zakresem:** liczenie asercji w testach C# — to jest osobna, znacznie większa
  praca niż wykrycie brakującego atrybutu, i wymagałaby rozbioru składni C#, a nie
  czytania tekstu. Poza zakresem także dopisywanie brakujących testów.
- **Zależy od:** nic.

##### 6.B28 · Metody z argumentami poza kształtem bramki

- **Skąd:** zmierzone 06.09.2026 przy 6.B27. Bramka na brakujący `[TestMethod]` stoi na
  kształcie „publiczna metoda `void`/`Task` **bez argumentów**", bo taka jest metoda
  testowa w tym repozytorium i taka straciła atrybut przy 6.A16. Kształt obejmuje
  **668** z **708** atrybutów testowych; pozostałe **40** to `[DataTestMethod]`
  z wierszami `[DataRow]`, czyli metody **z argumentami**. W tej rodzinie brakujący
  atrybut nadal przeszedłby niezauważony.
- **Wejście:** `tools/tests/csharp_test_methods.py` (`METODA`, `coverage`),
  `tools/tests/test_csharp_test_methods.py`, `reports/test-csharp-bez-atrybutu.md` §3,
  pliki `tests/**/*.cs` z `[DataTestMethod]`.
- **Wyjście:** rozszerzony kształt albo — jeżeli pomiar pokaże, że rozszerzenie łapie
  pomocników z argumentami i bramka zaczęłaby świecić na czymś, co usterką nie jest —
  **drugie, osobne kryterium** dla tej rodziny: metoda z `[DataRow]`, ale bez
  `[DataTestMethod]`, jest tak samo nieuruchamiana jak metoda bez `[TestMethod]`.
- **Weryfikacja:**
  ```bash
  python3 tools/tests/csharp_test_methods.py
  python3 tools/tests/test_all.py
  ```
  Oczekiwane: `poza ksztaltem` schodzi do zera albo raport nazywa, ile metod zostaje
  poza i **dlaczego nie da się ich objąć**.
- **Skończone, gdy:** liczba metod poza kształtem jest zerem albo jest **uzasadniona
  pomiarem**, a kontrola negatywna WYKONANA — zdjęty `[DataTestMethod]` z istniejącej
  metody z `[DataRow]` — zapala bramkę i nazywa tę metodę z imienia.
- **Poza zakresem:** liczenie asercji w testach C#. To ta sama granica, którą postawiła
  6.B27: wymagałoby rozbioru składni C#, a nie czytania tekstu.
- **Zależy od:** 6.B27.

##### 6.D25 · Moduł testowy uruchomiony wprost kończy się zerem, nie uruchomiwszy testu

- **Skąd:** zmierzone 06.09.2026 przy 6.A18, **na własnej kontroli negatywnej**. Opcja
  została zdjęta z tabeli `KnownOptions`, bramka uruchomiona przez
  `python3 tools/tests/test_runner_options.py`, wynik: `kod: 0` — i został odczytany jako
  „bramka się nie zapala". Nieprawda: moduł nie ma bloku `if __name__ == "__main__"`,
  więc uruchomiony wprost wykonuje same definicje, **zero testów**, i kończy się zerem
  nieodróżnialnie od przebiegu, w którym wszystko przeszło. Ta sama kontrola powtórzona
  przez `test_all.py` dała `FAIL` wskazujący wpis po nazwie.
- **Ile tego jest:** `ls tools/tests/test_*.py | wc -l` → **89**;
  `grep -l '__main__' tools/tests/test_*.py | wc -l` → **5**. Czyli **84 moduły**
  zachowują się tak samo. Blok mają: `test_all`, `test_braking`, `test_ci_workflows`,
  `test_mutation_sweep`, `test_reference_snapshot`.
- **Wejście:** `tools/tests/test_all.py` (jedyny prawomocny sposób uruchomienia zestawu),
  `tools/tests/assertion_gate.py` jako precedens z #139, `reports/wybieg-poza-poleceniem-line.md` §6.
- **Wyjście:** uruchomienie pojedynczego modułu wprost przestaje kłamać. Kształt do
  wyboru **na podstawie pomiaru, nie założenia**: albo wspólny blok `__main__` wołający
  ten sam przebiegacz co `test_all.py` na jednym module, albo odmowa z kodem różnym od
  zera i zdaniem, którym poleceniem uruchomić zestaw. Czego NIE wolno: zostawić kodu 0.
- **Weryfikacja:**
  ```bash
  python3 tools/tests/test_runner_options.py; echo "kod: $?"
  python3 tools/tests/test_all.py; echo "kod: $?"
  ```
  Oczekiwane: pierwsze polecenie albo naprawdę wykonuje testy tego modułu i wypisuje ich
  liczbę, albo kończy się kodem różnym od zera z instrukcją; **nigdy** kodem 0 przy
  zerze wykonanych testów. Drugie: bez zmian, kod 0.
- **Skończone, gdy:** żaden moduł `tools/tests/test_*.py` uruchomiony wprost nie kończy
  się kodem 0, nie wykonawszy ani jednego testu — sprawdzone **pętlą po wszystkich 89**,
  której wynik jest wklejony, a nie na jednym przykładzie. Kontrola negatywna WYKONANA:
  test celowo zepsuty w jednym module jest widoczny przy uruchomieniu wprost tego modułu.
- **Poza zakresem:** zamiana zestawu na `pytest` albo `unittest`. To jest zmiana
  zależności i przebiegacza (`CLAUDE.md` §8), a ta pozycja dotyczy jednego zachowania
  przy uruchomieniu wprost.
- **Zależy od:** nic.

##### 6.A20 · Pomiar zapisany bez nastaw, które go wyprodukowały

- **Skąd:** 6.A18 (#330) naprawiła to po stronie **wypisu**: nagłówek `[BUDŻET]` mówi od
  niej, czy przejazd był z wybiegiem, bo bez tego dwa pomiary — z nim i bez niego — dawały
  się porównać jako jeden. Ale wypis leci na konsolę i giń wraz z nią; **plik z `--out`
  przeżywa proces i to on trafia do raportów.** Zmierzone 07.09.2026: żaden z pięciu
  pisarzy CSV w `src/Sim.Runner/Program.cs` nie zapisuje ani jednej kolumny scenariusza.
  `budget --out` daje 13 kolumn pomiaru
  (`trains_declared,…,us_per_step,cpu_over_wall,frame_budget_pct`) i **zero** kolumn
  z odstępem, nawrotem, limitem, ATP, obciążeniem i wybiegiem — a te sześć nastaw
  zmienia przejazd, nie tylko jego koszt (tabela w `reports/wybieg-poza-poleceniem-line.md`
  §3: `N_śr` 6,69 / 6,67 / 6,40 przy tym samym `--trains 9`).
- **Wejście:** `src/Sim.Runner/Program.cs` — pisarze w wierszach ~228 i ~437
  (`DriveTelemetry.Header`, polecenia `drive` i `replay`), ~745 (`line --trace`),
  ~791 (`line --calls`), ~1176 (`service-day --out`), ~1285 (`budget --out`);
  `tools/ci/assert_linecore_budget.py` (czyta wypis, nie plik — więc jego nie dotyczy);
  `src/Sim/Train/LineRunSettings.cs` (`Assumptions`, `CoastDescription`).
- **Wyjście:** każdy plik z `--out` niesie nastawy, z których powstał. Kształt do wyboru
  **na podstawie pomiaru**: komentarz `#` przed nagłówkiem, dodatkowe kolumny stałe
  w każdym wierszu, albo plik-rodzeństwo z manifestem. Warunek jest jeden i nie zależy
  od kształtu: czytający plik **nie może** nie wiedzieć, jaki przejazd go wyprodukował.
  Jeżeli wybrany kształt zmienia format czytany przez cokolwiek — `assert_linecore_budget.py`,
  bramkę CI, `compare` — to musi się zmienić razem z nim, w tym samym commicie.
- **Weryfikacja:**
  ```bash
  dotnet run --project src/Sim.Runner -c Release -- budget \
      --axis data/track/L1_A.json \
      --signalling data/design/signalling/classic-2026.json \
      --limit-kmh 72 --exchange-s 20 --headway-s 10 --steps 200000 \
      --trains 9 --coast-from-m 250 --out build/z-wybiegiem.csv
  dotnet run --project src/Sim.Runner -c Release -- budget \
      --axis data/track/L1_A.json \
      --signalling data/design/signalling/classic-2026.json \
      --limit-kmh 72 --exchange-s 20 --headway-s 10 --steps 200000 \
      --trains 9 --out build/bez-wybiegu.csv
  diff build/z-wybiegiem.csv build/bez-wybiegu.csv
  python3 tools/tests/test_all.py
  dotnet test tests/Sim.Tests
  ```
  Oczekiwane: `diff` pokazuje **różnicę w nastawie**, nie tylko w liczbach pomiaru.
  Dziś oba pliki różnią się wyłącznie szumem czasu i wartościami ruchu, a nastawy,
  która je rozróżnia, nie ma w żadnym z nich.
- **Skończone, gdy:** dwa przebiegi różniące się jedną nastawą dają pliki, z których
  **da się odczytać, którą** — pokazane `diff`em wklejonym do raportu. Kontrola
  negatywna WYKONANA: nastawa usunięta z zapisu przy zachowanym wypisie zapala test.
- **Poza zakresem:** zmiana **formatu** telemetrii porównywanej co do bitu przez
  `compare` i przez bramkę `visual-regression`, jeżeli pomiar pokaże, że dopisanie
  nastaw ją rusza. Wtedy `drive`/`replay` zostają na osobną pozycję, a ta domyka
  `budget`, `line` i `service-day`. Poza zakresem także wybór wartości domyślnych.
- **Zależy od:** #330 (6.A18).

##### 6.D26 · Zapisany maksymalny czas zestawu jest niższy od tego, co maszyna pokazuje

- **Skąd:** zmierzone 07.09.2026 przy 6.D25. `MEASURED_MAX_WALL_S = 77.04`
  w `tools/tests/test_suite_runtime_budget.py`, a trzy kolejne przebiegi tego samego
  drzewa dały **98,9 / 100,9 / 102,1 s** — stabilnie, więc nie jest to szum jednego
  przebiegu.
- **Co przez to nie działa tak, jak wygląda:**
  `test_budget_stays_above_the_measured_maximum_with_a_real_margin` pilnuje, żeby próg
  nie spadł poniżej **zapisanego** pomiaru. Zapisany pomiar jest o 24 % niższy od
  rzeczywistego, więc pilnowany margines to w istocie **1,47×**, a nie ~1,95×, jaki
  sugeruje para liczb w pliku. Test nie jest zepsuty — mierzy dokładnie to, co mówi;
  zepsuta jest jedna z dwóch liczb, które porównuje.
- **Czego pomiar NIE pokazał, i to jest tu najważniejsze:** to **nie jest regres**.
  Rozstrzygnięte zmierzeniem tego samego modułu w dwóch drzewach:
  `test_station_layout.py` daje **34,86 s** w drzewie sprzed 6.A18 (`a6463db`)
  i **34,91 s** na `main` — a wcześniej tego samego dnia mierzył 22,7 s. Ten sam moduł,
  ten sam kod, **1,54× rozrzutu** od obciążenia hosta. Pozycja dotyczy więc zapisu
  pomiaru, nie wydajności kodu.
- **Wejście:** `tools/tests/test_suite_runtime_budget.py`, `.github/workflows/python-tests.yml`
  (krok czytający stałą), `reports/modul-uruchomiony-wprost.md` §7.
- **Wyjście:** zapis maksimum, który mówi, **na czym** został zmierzony, albo próg
  wyrażony tak, żeby rozrzut hosta nie wchodził do marginesu. Czego NIE wolno: podnieść
  `MEASURED_MAX_WALL_S` do 102 bez powiedzenia, że to liczba z hosta pod obciążeniem —
  wtedy następny czytający zobaczy dokładnie ten sam problem, tylko z drugiej strony.
  Dat pomiarów się nie przelicza: 77,04 zostaje jako pomiar swojego dnia.
- **Weryfikacja:**
  ```bash
  for i in 1 2 3; do python3 tools/tests/test_all.py | grep RAZEM; done
  python3 tools/tests/test_all.py test_suite_runtime_budget
  ```
  Oczekiwane: trzy czasy i zapis, w którym da się je odnaleźć — a nie liczba niższa
  od wszystkich trzech.
- **Skończone, gdy:** w pliku nie stoi obok siebie próg i pomiar, których stosunek
  nazywa marginesem coś innego, niż margines naprawdę wynosi — sprawdzone trzema
  przebiegami, których wynik jest wklejony. Kontrola negatywna WYKONANA.
- **Poza zakresem:** przyspieszanie zestawu. To jest 6.B30 i osobna praca.
- **Zależy od:** nic.

##### 6.B30 · Jeden moduł to trzecia część czasu zestawu, bo liczy to samo trzydzieści razy

- **Skąd:** zmierzone 07.09.2026 przy 6.D25. `test_station_layout.py` zajmuje
  **35,1 s** z ~100 s całego zestawu, przy 17 testach — z czego **cztery po ~6,0 s**:
  ```
  6.22 s  test_station_layout_runs_on_every_package_axis_not_only_A
  6.04 s  test_the_BF_report_numbers_are_reproducible_from_the_axes
  6.02 s  test_minimum_edge_offset_holds_the_same_invariant_on_all_six_axes
  5.97 s  test_every_axis_clips_exactly_its_two_terminus_platforms
  ```
  `_layout_for(axis_id)` czyta plik osi i woła `SL.layout()` **bez żadnej pamięci**,
  a jest wołane z **pięciu** miejsc, każde w pętli po **sześciu** osiach — czyli około
  trzydziestu pełnych przebiegów narzędzia na tych samych sześciu plikach z `data/track/`.
- **Wejście:** `tools/tests/test_station_layout.py` (`_layout_for`, `_axis_document`),
  `tools/track/station_layout.py` (`layout`, `resolve_platform_length_m`).
- **Wyjście:** ten sam zestaw testów, ten sam wynik, bez trzydziestu przebiegów tego
  samego. Najprostszy kształt to pamięć na `_layout_for` — ale **wymaga pomiaru, nie
  założenia**: funkcja zwraca strukturę, a test, który ją modyfikuje, dostałby wtedy
  cudzy obiekt i psułby następny test w sposób zależny od kolejności. Jeżeli pomiar
  pokaże, że którykolwiek test ją modyfikuje, kształtem jest kopia przy wydaniu albo
  struktura niezmienna, a nie zdjęcie pamięci.
- **Weryfikacja:**
  ```bash
  python3 tools/tests/test_all.py test_station_layout
  python3 tools/tests/test_all.py
  ```
  Oczekiwane: ten sam licznik testów (17) i ten sam werdykt, przy czasie modułu
  **poniżej 10 s**; cały zestaw bez ani jednego nowego `FAIL`.
- **Skończone, gdy:** moduł schodzi poniżej 10 s przy niezmienionym licznikiem testów
  i niezmienionym werdykcie — oba wklejone — a `python3 tools/tests/test_all.py` jest
  zielony **kodem wyjścia**. Kontrola negatywna WYKONANA: pamięć oddająca współdzieloną
  strukturę, którą test modyfikuje, zapala zestaw — albo pomiar pokazuje, że żaden test
  jej nie modyfikuje, i to jest wtedy wypisane.
- **Poza zakresem:** przyspieszanie `test_mutation_sweep.py` (16,3 s) i
  `test_curve_radius_axes.py` (14,3 s). Mają inne przyczyny i każda jest osobną pracą;
  ta pozycja dotyczy jednego modułu i jednego mechanizmu. Poza zakresem także zmiana
  progu czasu zestawu — to jest 6.D26.
- **Zależy od:** #332 (6.D25), bo `test_all.py <modul>` z tamtej pozycji jest tu
  narzędziem weryfikacji.

##### 6.A21 · Trzy pisarze CSV, których format przybija coś z zewnątrz

- **Skąd:** 6.A20 domknęła dwóch pisarzy z pięciu i **wypisała powód każdego z trzech
  pozostałych osobno**, zamiast nazwać je jednym „poza zakresem". Powody są różne
  i każdy wymaga zmiany po **drugiej stronie** porównania, nie w `Program.cs`:
  - **`drive` / `replay`** — `Compare` wymaga, żeby pierwszy wiersz był **dokładnie**
    `DriveTelemetry.Header`, a każdy wiersz miał dokładnie `ColumnCount` kolumn. Ten sam
    format pisze scena Godota, a `godot-first-run.yml` porównuje oba pliki przy
    `--tolerance 0`. Wiersz `#` przed nagłówkiem łamie warunek na `left[0]`.
  - **`line --calls`** — `godot-first-run.yml:1114` porównuje plik rdzenia z plikiem
    **SCENY**, więc format jest wspólny z implementacją w Godocie, nie tylko z tym
    repozytorium.
  - **`line --trace`** — `tools/ci/assert_line_trace.py` liczy **SHA-256 całego pliku**
    wobec wzorców przybitych do RODZINY runtime'u .NET. Tamta bramka mówi wprost, że
    przeliczanie wzorców (`--update`) należy do commita zmieniającego wersję środowiska
    i ma być w jego treści opisane — dopisanie metadanych przeliczyłoby je jako skutek
    uboczny, czyli **złamałoby cudzą regułę**.
- **Wejście:** `src/Sim.Runner/Program.cs` (`Provenance`, `Drive`, `Replay`,
  `LineCommand`), `tools/tests/test_csv_provenance.py` (słownik `BEZ_NASTAW` z tymi
  trzema powodami), `tools/ci/assert_line_trace.py`, `.github/workflows/godot-first-run.yml`,
  `tools/ci/golden/` (wzorce śladu), scena Godota pisząca telemetrię i `--calls`,
  `reports/nastawy-w-pliku-nie-w-wypisie.md` §3.
- **Wyjście:** nastawy w tych trzech plikach **albo** rozstrzygnięcie, że format
  któregokolwiek zostaje nietknięty na stałe, z powodem zapisanym tak, żeby dało się go
  sprawdzić. Kolejność narzucona przez pomiar, nie przez wygodę: `line --trace` idzie
  **na końcu albo osobno**, bo przelicza wzorce; `drive`/`replay` i `--calls` wymagają
  zmiany w scenie, więc kryterium musi obejmować przebieg `godot-first-run.yml`, a nie
  tylko `dotnet test`.
- **Weryfikacja:**
  ```bash
  python3 tools/tests/test_all.py
  dotnet test tests/Sim.Tests
  git diff --stat tools/ci/golden/
  ```
  Oczekiwane: zestawy zielone **kodem wyjścia**, a `git diff --stat tools/ci/golden/`
  albo puste, albo pokazujące wzorce przeliczone **razem z opisem w treści commita** —
  bo tego wymaga `assert_line_trace.py`, nie ta pozycja.
- **Skończone, gdy:** dla każdego z trzech pisarzy w repozytorium stoi albo plik
  z nastawami, albo powód, dla którego go nie ma — i **słownik `BEZ_NASTAW` maleje**,
  a nie tylko zmienia treść. Kontrola negatywna WYKONANA dla każdego tkniętego pisarza:
  zdjęte nastawy zapalają bramkę i nazywają polecenie. Jeżeli którykolwiek wymaga
  zmiany w scenie Godota, potwierdzeniem jest **zielony przebieg
  `godot-first-run.yml`**, a nie lokalny `dotnet test`.
- **Poza zakresem:** zmiana **znaczenia** telemetrii albo kolumn pomiaru. Ta pozycja
  dotyczy metadanych o przebiegu, nie tego, co przebieg mierzy. Poza zakresem także
  `axis --dump-points`, który nastaw nie ma z innego powodu (surowe punkty, bez pomiaru
  i bez ani jednego konsumenta — sprawdzone grepem przy 6.A20).
- **Zależy od:** 6.A20.

##### 6.D27 · Odsyłacz do sekcji czytany jako wartość stałej

- **Skąd:** zmierzone 07.09.2026 przy 6.D26. Bramka zapaliła się na **poprawnym**
  zdaniu raportu: „Nie tknięto `SUITE_RUNTIME_BUDGET_S` — §4. Decyzja o czułości
  bramki." → `raporty podają inną wartość niż kod: SUITE_RUNTIME_BUDGET_S mówi 4,
  kod 150.0`. Wzorzec `CLAIM` bierze pierwszą liczbę w 40 znakach po nazwie stałej,
  a numer sekcji jest liczbą.
- **Ile tego już jest:** trzy wiersze w `reports/` mają dokładnie ten kształt
  (`nazwa-zajeta-drugi-raz.md:63, :172, :176`) i przechodzą **wyłącznie przypadkiem** —
  żadna z tych trzech stałych nie trafia do słownika wartości: `MIN_RADIUS_M` została
  usunięta przy 6.B25, `LOCATION_STATION` ma wartość napisową, a `TOLERANCE_M` ma trzy
  definicje o dwóch wartościach, więc jest wykluczona jako niejednoznaczna. Pierwszy
  raport, który postawi numer sekcji za nazwą **jednoznacznej liczbowej** stałej,
  zapali bramkę na poprawnym tekście.
- **Dlaczego to nie jest kosmetyka:** bramka, która świeci na poprawnym tekście,
  zostaje wyłączona, nie poprawiona. To samo zdanie stoi w `test_suite_runtime_budget.py`
  po 6.D26 jako powód wycięcia własnego docstringa ze skanowania.
- **Wejście:** `tools/tests/test_report_claims.py` (`CLAIM`, `claims_in_reports`,
  `test_the_claim_pattern_takes_values_and_leaves_mapping_tables_alone`),
  `reports/nazwa-zajeta-drugi-raz.md`, `reports/zapis-czasu-zestawu.md` §7.
- **Wyjście:** wzorzec, który **nie** bierze za wartość liczby poprzedzonej znakiem
  odsyłacza (`§`, `#`, `pkt`, `rozdz.`) ani numeru w cudzym cytacie. Kryterium kształtu
  ma wyjść z pomiaru na dzisiejszych raportach, a nie z listy znaków wymyślonej z góry:
  wąskie kryterium przepuszcza fałszywe trafienie, szerokie przestaje łapać prawdziwe
  rozjazdy — a te bramka łapie od #139 i tego nie wolno stracić.
- **Weryfikacja:**
  ```bash
  python3 tools/tests/test_all.py
  python3 tools/tests/test_all.py test_report_claims
  ```
  Oczekiwane: zielono, a wypis mówi, ile twierdzeń w raportach bramka **sprawdziła** —
  liczba, nie samo „ok", bo wzorzec zawężony za mocno przechodziłby przez sprawdzenie
  zera twierdzeń.
- **Skończone, gdy:** zdanie `` `STAŁA` — §4 `` przechodzi, a `` `STAŁA` to 4 ``
  przy kodzie mówiącym 150 nadal **odmawia** — oba pokazane WYKONANĄ kontrolą, nie
  opisane. Liczba sprawdzanych twierdzeń nie spada.
- **Poza zakresem:** rozbiór markdownu na drzewo. To jest bramka na tekst i taka
  zostaje; zmiana narzędzia byłaby zmianą zależności (`CLAUDE.md` §8).
- **Zależy od:** nic.

##### 6.D28 · Asercje w testach C# nie są liczone przez nic

- **Skąd:** 6.B27 (#329) nazwała to wprost w polu „Poza zakresem", dokładając bramkę na
  brakujący `[TestMethod]`, ale nie na puste ciało. Zestaw Pythona ma `assertion_gate`
  od #139: test, który przeszedł **bez ani jednej asercji**, jest tam awarią, nie
  sukcesem. Dziś ta bramka zadziałała **dwa razy** — przy 6.D26, na moim własnym teście,
  który po zawężeniu zakresu skanowania przestał cokolwiek sprawdzać, i to był jedyny
  ślad, że przestał.
- **Ile tego jest:** `grep -rhoE "\b(Assert|StringAssert|CollectionAssert)\.[A-Za-z]+"`
  po `tests/` daje **2289** wywołań w **124** plikach `.cs`. Liczba testów C# to dziś
  552 (`dotnet test`), więc średnio ponad cztery asercje na test — ale **średnia nie
  wyklucza zera** w pojedynczym teście, i to właśnie jest do zmierzenia.
- **Wejście:** `tools/tests/csharp_test_methods.py` (precedens: czytanie `tests/**/*.cs`
  jako tekstu, ze świadomością głębokości klamer, bez `dotnet`),
  `tools/tests/assertion_gate.py` (precedens po stronie Pythona, #139),
  `tests/Sim.Tests/`, `reports/test-csharp-bez-atrybutu.md`.
- **Wyjście:** wypis, ile metod testowych C# nie zawiera ani jednego wywołania
  `Assert`/`StringAssert`/`CollectionAssert` **ani** `Assert.Throws`-podobnego wyrażenia,
  i bramka na tę liczbę. Kształt musi wyjść z pomiaru: test, którego cała treść to
  wywołanie rzucające wyjątek, jest testem bez asercji, ale **nie** jest testem pustym —
  i pomiar ma powiedzieć, ile takich jest, zanim ktoś zdecyduje, czy je zgłaszać.
- **Weryfikacja:**
  ```bash
  python3 tools/tests/test_all.py
  dotnet test tests/Sim.Tests
  ```
  plus wypis: ile metod testowych, ile z asercją, ile bez i **które**.
- **Skończone, gdy:** liczba metod bez asercji jest zerem albo jest **uzasadniona
  pomiarem** wpisanym do raportu, a kontrola negatywna WYKONANA — asercje usunięte
  z jednego istniejącego testu zapalają bramkę i **nazywają go z imienia**. Bramka nie
  może wymagać `dotnet`: zestaw narzędzi chodzi tam, gdzie `doctor.sh` przepuszcza brak
  SDK. Liczba testów C# w `dotnet test` nie może spaść.
- **Poza zakresem:** liczenie asercji **wykonanych** w czasie przebiegu, jak to robi
  `assertion_gate` przez instrumentację AST. Po stronie C# wymagałoby to rozbioru
  składni albo wpięcia w runner testów — inna, znacznie większa praca. Ta pozycja
  dotyczy asercji **obecnych w treści**, czyli tego, co da się przeczytać z tekstu.
- **Zależy od:** #329 (6.B27).

##### 6.B31 · Bramka martwych stałych widzi tylko Pythona

- **Skąd:** 6.B29 (#334) samo wypisało ten brak w polu „czego nie zrobiono" — ale
  **nazwało go katalogiem `godot/`, który w tym repozytorium nie istnieje**. Sprawdzone
  07.09.2026: `ls -d */` daje `data docs reports src tests tools`, a scena Godota leży
  w `src/Game/` (`src/Game/Scenes/FirstRun.tscn`), czyli w drzewie, które bramka **już
  obchodzi** — tylko filtruje pliki po `.py`. Brak jest więc realny, ale jest brakiem
  **języka**, nie katalogu.
- **Ile tego jest:** bramka obejmuje **705** stałych modułowych z plików `.py`.
  Deklaracji `const` i `static readonly` o nazwie wielkimi literami w `src/` i `tests/`
  jest **213** i żadnej nie widzi nic. `MIN_RADIUS_M` przeżyło pięć dni po stronie
  Pythona i zdążyło zostać zacytowane w docstringu jako granica obowiązująca; po
  stronie C# nie ma odpowiednika tej bramki.
- **Wejście:** `tools/tests/test_dead_constants.py` (kształt: zapadka z uzasadnieniami,
  pilnowana w obie strony), `tools/tests/csharp_test_methods.py` (precedens czytania
  C# jako tekstu, ze świadomością głębokości klamer), `src/Sim/`, `src/Game/`,
  `reports/stala-ktorej-nikt-nie-czyta.md` §7.
- **Wyjście:** stała `const` albo `static readonly`, której żaden plik `.cs` w `src/`
  ani `tests/` nie czyta, jest zgłaszana albo uzasadniona — z listą wyjątków, której
  rozmiar wychodzi z pomiaru, a nie z założenia. Odczyt musi obejmować `NAZWA`
  i `Typ.NAZWA`, bo stałą C# czyta się przez nazwę klasy; sprawdzone muszą być także
  `*.tscn` i `*.gd`, jeżeli scena odwołuje się do nazw stałych.
- **Weryfikacja:**
  ```bash
  python3 tools/tests/test_all.py
  ```
  plus wypis: ile deklaracji, ile nieczytanych i które.
- **Skończone, gdy:** bramka jest zielona na dzisiejszym drzewie, a kontrole negatywne
  WYKONANE w **obie** strony: stała bez odczytu dopisana do dowolnego pliku `.cs` zapala
  bramkę i nazywa plik oraz nazwę; wpis na liście wyjątków, który przestał opisywać
  stałą nieczytaną, też ją zapala. Bramka nie może wymagać `dotnet`.
- **Poza zakresem:** pola, właściwości, metody i klasy nieużywane. To wymagałoby
  rozstrzygnięcia, czym jest publiczne API typu — a ta pozycja dotyczy stałych, czyli
  tego samego kształtu, który przeżył w #50. Poza zakresem także `src/Game/*.tscn` jako
  źródło definicji: scena nie definiuje stałych, tylko je czyta.
- **Zależy od:** #334 (6.B29).

MINIMUM_DETAIL_BLOCKS = 73

##### 6.D29 · Asercja w gałęzi, do której może nic nie wejść

- **Skąd:** 6.D28 (#341) postawiła granicę swojej bramki wprost: liczy asercje **obecne
  w treści**, nie **wykonane**. `assertion_gate` po stronie Pythona robi to drugie
  i dlatego złapał 07.09.2026 mój własny test, który po zawężeniu zakresu przestał
  cokolwiek sprawdzać — asercja stała w pętli, do której nic nie weszło. Po stronie C#
  taki test przechodzi.
- **Ile tego jest, i dlaczego liczba surowa jest myląca:** 82 metody testowe mają
  **wszystkie** asercje w bloku zagnieżdżonym. Podział po słowie otwierającym najbliższy
  blok jest jednak ostry:
  ```
  foreach     46      for     19      try      7
  if           4      while    2      (brak)   4
  ```
  **65 z 82 to pętle po zbiorze zadanym w samym teście** — wykonują się, więc bramka
  zbudowana na samej zagnieżdżoności zapaliłaby się na 65 testach **poprawnych**.
  Interesujących jest **17**.
- **Wejście:** `tools/tests/csharp_assertions.py`, `tools/tests/test_csharp_assertions.py`,
  `tools/tests/assertion_gate.py` (jak to robi strona Pythona),
  `reports/asercje-w-testach-csharp.md` §5, oraz te 17 metod:
  `MovementAuthorityTests`, `DriverActionsTests`, `EnergyAccountTests`, `LineDriveTests`
  i pozostałe z wypisu.
- **Wyjście:** **najpierw klasyfikacja tych 17**, dopiero potem decyzja o bramce.
  Każda ma jedną z trzech własności i tylko trzecia jest usterką: (a) gałąź wchodzi
  zawsze, bo warunek jest w teście ustawiony — asercja jest wykonywana; (b) gałąź
  może nie wejść, ale sam brak wejścia jest sprawdzany osobno (np. `Assert.Fail()`
  w drugiej gałęzi); (c) gałąź może nie wejść i nikt tego nie sprawdza — wtedy test
  przechodzi, nie sprawdziwszy nic. Bramka ma sens **tylko** na (c), a jej kształt
  ma wyjść z liczby przypadków (c), nie z góry.
- **Weryfikacja:**
  ```bash
  python3 tools/tests/csharp_assertions.py
  python3 tools/tests/test_all.py
  dotnet test tests/Sim.Tests
  dotnet test tests/Game.Tests
  ```
  plus wypis: ile metod w kategorii (a), (b) i (c), **z nazwami** dla (c).
- **Skończone, gdy:** liczba metod w kategorii (c) jest zerem albo jest **uzasadniona
  pomiarem** wpisanym do raportu, a klasyfikacja wszystkich 17 jest w raporcie
  wypisana z nazwami — nie podsumowana liczbą. Jeżeli powstaje bramka, kontrola
  negatywna WYKONANA: test z asercją tylko w niewchodzącej gałęzi ją zapala, a żaden
  z 65 testów pętlowych **nie** zapala. Liczba testów w `dotnet test` nie spada.
- **Poza zakresem:** instrumentacja C# licząca asercje wykonane. To jest ta sama
  granica, którą 6.D28 postawiła wprost: wymagałoby rozbioru składni albo wpięcia
  w runner testów. Poza zakresem także zmiana treści testów pętlowych.
- **Zależy od:** #341 (6.D28).

##### 6.D30 · Dwa czytniki C# i pasmo zamiast równości

- **Skąd:** 6.D28 dopisała `csharp_assertions.py` obok `csharp_test_methods.py` z 6.B27.
  Nowy importuje z tamtego `KLASA`, `METODA` i `ATRYBUTY_TESTU` — ale ma **własne
  przejście po ciele klasy**, bo tamto go nie obsłuży: `_poziom_bezposredni` **wycina**
  ciała członów (po to, żeby znaleźć sam poziom deklaracji), a `czlonkowie` je
  **zostawia** i dodatkowo zna ciało wyrażeniowe `=> …;`.
- **Rozjazd nie jest hipotetyczny — już był:** kontrola negatywna KN-2 przy 6.D28 dała
  `nowy czytnik widzi MNIEJ metod (670) niz starszy (674)`. Test zgodności przybija
  to dziś **pasmem**:
  ```python
  assert nowy - stary <= 20, ...
  ```
  a pasmo 20 jest liczbą wziętą z palca, nie z pomiaru — postawioną dlatego, że
  równości nie dało się postawić, mając dwa różne rozbiory. To jest fudge i wpis mówi
  o nim wprost, zamiast czekać, aż ktoś go znajdzie.
- **Wejście:** `tools/tests/csharp_test_methods.py` (`_cialo_klasy`,
  `_poziom_bezposredni`, `metody`, `coverage`), `tools/tests/csharp_assertions.py`
  (`_koniec_bloku`, `czlonkowie`, `metody_testowe`, `coverage`),
  `tools/tests/test_csharp_test_methods.py`, `tools/tests/test_csharp_assertions.py`.
- **Wyjście:** **jedno** przejście po ciele klasy, z którego korzystają oba
  zastosowania — wykrywanie brakującego atrybutu (6.B27) i liczenie asercji (6.D28) —
  a test zgodności zamienia pasmo na **równość**. Czego NIE wolno: zostawić dwóch
  przejść i podnieść pasma.
- **Weryfikacja:**
  ```bash
  python3 tools/tests/csharp_test_methods.py
  python3 tools/tests/csharp_assertions.py
  python3 tools/tests/test_all.py
  ```
  Oczekiwane: **te same** liczby metod z atrybutem z obu narzędzi, wypisane obok
  siebie, i zestaw zielony kodem wyjścia.
- **Skończone, gdy:** oba narzędzia podają identyczną liczbę metod z atrybutem
  testowym — wklejoną — a test zgodności żąda równości, nie pasma. Kontrole negatywne
  WYKONANE, obie z 6.B27 i 6.D28 nadal zapalają się na swoich usterkach: zdjęty
  `[TestMethod]` nazywa test z imienia, zdjęta asercja nazywa metodę bez asercji.
  Liczba testów w `dotnet test` nie spada.
- **Poza zakresem:** rozbiór C# biblioteką zewnętrzną. To zmiana zależności
  (`CLAUDE.md` §8), a oba narzędzia stoją na czytaniu tekstu ze świadomością głębokości
  klamer i taki zostają. Poza zakresem także obejmowanie metod z argumentami — to 6.B28.
- **Zależy od:** #341 (6.D28), #329 (6.B27).

##### 6.A22 · Odmowa mówi, że runner nie zna opcji, którą zna

- **Skąd:** zmierzone 07.09.2026 przy sondowaniu powierzchni wiersza poleceń
  `Sim.Runner` (pomiar zrobiony przy okazji 6.D30, przed wzięciem 6.A15):
  ```
  --zmyslona 7                     kod=1  BŁĄD: polecenie line nie zna opcji --zmyslona. Zna: --axis, …
  --limit-kmh=72                   kod=1  BŁĄD: polecenie line nie zna opcji --limit-kmh=72. Zna: --axis, …
  ```
  Pierwsze zdanie jest poprawne. Drugie **jest sprzeczne z faktem**: `--limit-kmh`
  stoi w tabeli `KnownOptions` polecenia `line`, więc runner tę opcję zna. Nie zna
  **postaci** `--opcja=wartość` — a to jest inna wiadomość niż ta, którą wypisuje.
- **Dlaczego to nie jest kosmetyka:** odmowa z 6.A11 istnieje po to, żeby literówka nie
  przechodziła w milczeniu, i jej wartość leży w tym, że czytający jej **wierzy**.
  Komunikat, który raz na jakiś czas mówi nieprawdę o zawartości tabeli, uczy czytać go
  z zastrzeżeniem — a wtedy przestaje działać także w tym przypadku, w którym miał rację.
- **Wejście:** `src/Sim.Runner/Program.cs` (`RejectUnknownOptions`, tabela
  `KnownOptions`), `tools/tests/test_runner_options.py`,
  `tests/Sim.Tests/RunnerCommandTests.cs`, `reports/nieznana-opcja-runnera.md` (6.A11).
- **Wyjście:** komunikat mówiący, co jest naprawdę nie tak. **Do wyboru na podstawie
  pomiaru, nie z góry**: albo postać `--opcja=wartość` zostaje obsłużona (i wtedy
  `--limit-kmh=72` po prostu działa), albo zostaje odrzucona z komunikatem nazywającym
  **postać**, nie nieznajomość opcji. Pierwsza droga jest większa i dotyka każdego
  polecenia; druga jest mniejsza i nie zmienia niczego, co dziś działa. Pomiar ma
  powiedzieć, ile miejsc w repozytorium (skrypty CI, `docs/`, README) używa postaci
  z równością — bo jeżeli zero, to druga droga wystarcza.
- **Weryfikacja:**
  ```bash
  dotnet run --project src/Sim.Runner -c Release -- line --axis data/track/L1_A.json \
      --limit-kmh=72 --exchange-s 20
  dotnet run --project src/Sim.Runner -c Release -- line --axis data/track/L1_A.json \
      --zmyslona 7 --limit-kmh 72 --exchange-s 20
  dotnet test tests/Sim.Tests
  python3 tools/tests/test_all.py
  ```
  Oczekiwane: pierwsze albo działa, albo odmawia komunikatem o **postaci**; drugie nadal
  odmawia komunikatem o nieznanej opcji, **niezmienionym** — bo ono było poprawne.
- **Skończone, gdy:** żaden komunikat odmowy nie twierdzi o opcji z tabeli, że runner
  jej nie zna — sprawdzone WYKONANĄ próbą obu wariantów, z wklejonym wyjściem. Kontrola
  negatywna WYKONANA: literówka (`--zmyslona`) nadal daje komunikat o nieznanej opcji
  i kod 1, czyli poprawka nie uciszyła odmowy, którą 6.A11 wprowadziła.
- **Poza zakresem:** przepisanie wiersza poleceń na bibliotekę do rozbioru argumentów.
  To zmiana zależności (`CLAUDE.md` §8), a `Option`/`RequiredNumber`/`OptionalNumber`
  są dziś jednym miejscem, które `test_runner_options.py` umie czytać.
- **Zależy od:** #303 (6.A11).

##### 6.A23 · Powtórzona opcja przyjmowana w milczeniu

- **Skąd:** zmierzone 07.09.2026, tym samym sondowaniem co 6.A22:
  ```
  --limit-kmh 72 --limit-kmh 50    kod=0   [LINIA] limit 72.00 km/h
  --limit-kmh 50 --limit-kmh 72    kod=0   [LINIA] limit 50.00 km/h
  ```
  **Wygrywa pierwsza**, druga jest odrzucana bez słowa. `Option` szuka pierwszego
  wystąpienia i nie patrzy dalej.
- **Co jest, a co nie jest tu problemem:** wartość skuteczna **nie jest** niewidoczna —
  `[LINIA]` i `[ZAŁOŻENIE]` ją podają, i to jest zasługa 6.A5/6.A6. Problemem jest brak
  informacji, że **coś zostało odrzucone**: czytający wypis widzi 72 i nie ma powodu
  przypuszczać, że wiersz poleceń mówił także 50. Od 6.A20 nastawy trafiają również do
  plików z `--out`, więc ta sama luka jest teraz w artefakcie, który przeżywa proces.
- **Wejście:** `src/Sim.Runner/Program.cs` (`Option`, `RequiredNumber`,
  `OptionalNumber`, `RejectUnknownOptions`, `Provenance`),
  `tests/Sim.Tests/RunnerCommandTests.cs`, `reports/nastawy-w-pliku-nie-w-wypisie.md`
  (6.A20), `reports/nieznana-opcja-runnera.md` (6.A11).
- **Wyjście:** powtórzona opcja przestaje być milcząca. **Kierunek do wyboru na
  podstawie pomiaru**: odmowa (kod 1, jak dla każdej innej złej nastawy) albo wypis
  mówiący, że wartość została nadpisana. Odmowa jest spójniejsza z 6.A16 („każda odmowa
  argumentowa = 1"), ale trzeba **najpierw sprawdzić**, czy któryś skrypt CI albo
  `docs/` nie podaje świadomie tej samej opcji dwa razy — jeżeli tak, odmowa wywróci
  przebieg, który dziś działa.
- **Weryfikacja:**
  ```bash
  grep -rn -- "--limit-kmh" .github/ tools/ docs/ | grep -c "limit-kmh.*limit-kmh"
  dotnet run --project src/Sim.Runner -c Release -- line --axis data/track/L1_A.json \
      --limit-kmh 72 --limit-kmh 50 --exchange-s 20
  dotnet test tests/Sim.Tests
  ```
  Oczekiwane: grep podaje **liczbę** miejsc z powtórzeniem (zero pozwala na odmowę),
  a przebieg albo odmawia kodem 1, albo mówi wprost, która wartość została odrzucona.
- **Skończone, gdy:** przebieg z powtórzoną opcją nie kończy się kodem 0 bez ani jednego
  zdania o powtórzeniu — pokazane WYKONANĄ próbą w obu kolejnościach, z wklejonym
  wyjściem. Kontrola negatywna WYKONANA: przebieg z opcją podaną **raz** jest
  niezmieniony, bit w bit dla telemetrii, bo ta pozycja nie ma prawa tknąć przejazdu.
- **Poza zakresem:** rozstrzyganie konfliktów między opcjami RÓŻNYMI (np. `--limit-kmh`
  ponad limit planu sygnalizacji) — to osobne zagadnienie, opisane przy #246, i ta
  pozycja go nie dotyka. Poza zakresem także flagi (`--atp`), których powtórzenie
  niczego nie zmienia.
- **Zależy od:** #303 (6.A11), #336 (6.A20).

##### 6.A24 · `compare` na nieliczbowej komórce mówi komunikatem platformy

- **Skąd:** zmierzone 07.09.2026 przy 6.A14. Ta pozycja przeszła po wszystkich
  jedenastu drogach wartości opcji do liczby i **jedną** zostawiła nietkniętą,
  wpisując ją jako jedyne usprawiedliwienie w `test_runner_number_parsing.py`:
  `Compare` rozbiera komórki CSV, a nie wartości opcji, więc komunikat nazywający
  opcję byłby tam nieprawdą. Nietknięta nie znaczy jednak dobra — komunikat jest
  dziś dokładnie ten sam, który 6.A14 wyjęła z opcji:
  `BŁĄD: The input string 'x' was not in a correct format.`
- **Wejście:** `src/Sim.Runner/Program.cs` (`Compare`, pętla po
  `DriveTelemetry.ColumnCount - 1`), `tests/Sim.Tests/RunnerCommandTests.cs`,
  `tools/tests/test_runner_number_parsing.py` (wpis `USPRAWIEDLIWIENIA`).
- **Wyjście:** odmowa nazywająca **plik** (lewy czy prawy), **numer wiersza**,
  **nazwę kolumny** z `DriveTelemetry` i samą wartość; wpis usprawiedliwienia zdjęty
  albo przepisany na to, co zostaje.
- **Weryfikacja:**
  ```bash
  dotnet run --project src/Sim.Runner -c Release -- drive --out build/d1.csv
  python3 - <<'EOF'
  rows = open("build/d1.csv").read().splitlines()
  rows[3] = ",".join(["abc"] + rows[3].split(",")[1:])
  open("build/d2.csv", "w").write("\n".join(rows) + "\n")
  EOF
  dotnet run --project src/Sim.Runner -c Release -- compare build/d1.csv build/d2.csv
  dotnet test tests/Sim.Tests
  ```
  Oczekiwane: komunikat wymienia `build/d2.csv`, wiersz **3** i nazwę pierwszej
  kolumny telemetrii; kod 1.
- **Skończone, gdy:** odmowa na zepsutej komórce nazywa plik, wiersz i kolumnę,
  `compare` dwóch poprawnych plików nadal kończy się kodem 0 — sprawdzone
  uruchomieniem, nie czytaniem — a kontrola negatywna WYKONANA wywraca dokładnie
  nowy test. Numer wiersza liczony **od zera czy od jedynki** ma być powiedziany
  w komunikacie, nie zostawiony do zgadnięcia.
- **Poza zakresem:** rozbiór nagłówka (`left[0]` wobec `DriveTelemetry.Header`) —
  ten ma już własną odmowę i własny komunikat. Poza zakresem także tolerancja na
  brakującą kolumnę: to inna klasa błędu pliku.
- **Zależy od:** 6.A14.

##### 6.A25 · Człon pozycyjny nieznany żadnemu poleceniu przechodzi w milczeniu

- **Skąd:** zmierzone 07.09.2026 przy 6.A22, które świadomie tego nie tknęło i wypisało
  powód w §11 raportu. Wykonane:
  ```
  budget … --atp 1          kod=0   [BUDŻET] … ATP=tak …      ← `1` zignorowane
  budget … --atp            kod=0   [BUDŻET] … ATP=tak …      ← wypis identyczny
  budget … zmyslony_czlon   kod=0   [BUDŻET] … ATP=nie …
  ```
  Odmowa z 6.A11 i 6.A15 odsiewa człony bez minusa **celowo**: `compare` bierze dwie
  ścieżki pozycyjnie, więc odmowa zbudowana na „wszystko, czego nie znam" wywróciłaby
  to polecenie w całości. Zaleta tamtej decyzji jest realna, a jej cena jest tutaj.
- **Dlaczego to nie jest drobiazg:** komunikat 6.A22 radzi dziś fladze „podaj samo
  `--atp`" właśnie dlatego, że `--atp 1` przechodzi bez słowa. Rada jest poprawna, ale
  jej powodem jest ta dziura — a dopóki dziura jest, literówka w wartości flagi
  wygląda dokładnie jak przebieg poprawny.
- **Wejście:** `src/Sim.Runner/Program.cs` (`RejectUnknownOptions`, tabela
  `KnownOptions`), `tools/tests/test_runner_options.py`,
  `tests/Sim.Tests/RunnerCommandTests.cs`, `reports/postac-z-rownosciem.md` §11,
  `reports/jeden-minus.md` §2 (pomiar argumentów pozycyjnych).
- **Wyjście:** liczba członów pozycyjnych, jaką bierze każde polecenie — najpewniej
  jako trzecie pole w `KnownOptions` — plus odmowa dla członu pozycyjnego ponad tę
  liczbę. **Do rozstrzygnięcia pomiarem, nie z góry**: ile poleceń bierze dziś choć
  jeden człon pozycyjny (`compare` bierze dwa; pomiar ma powiedzieć, czy któreś inne
  też), bo jeżeli tylko `compare`, wystarcza jedna liczba przy poleceniu, a nie nowy
  rozbiór.
- **Weryfikacja:**
  ```bash
  dotnet run --project src/Sim.Runner -c Release -- budget --axis data/track/L1_A.json \
      --signalling data/design/signalling/classic-2026.json --limit-kmh 72 \
      --exchange-s 20 --headway-s 90 --trains 2 --steps 100 --atp 1
  dotnet run --project src/Sim.Runner -c Release -- compare build/d1.csv build/d2.csv
  dotnet test tests/Sim.Tests
  ```
  Oczekiwane: pierwsza komenda odmawia i nazywa nadmiarowy człon; druga nadal kończy
  się kodem 0, bo dwie ścieżki `compare` są członami, które to polecenie bierze.
- **Skończone, gdy:** żaden człon, którego polecenie nie czyta, nie przechodzi
  w milczeniu — sprawdzone WYKONANIEM obu komend z wklejonym wyjściem — a `compare`
  z dwiema ścieżkami i każde polecenie bez członów pozycyjnych nadal kończy się kodem
  0. Kontrola negatywna WYKONANA: zdjęta liczba członów pozycyjnych wywraca dokładnie
  test `compare`, a nie tylko nowy test.
- **Poza zakresem:** przepisanie wiersza poleceń na bibliotekę do rozbioru argumentów
  — ta sama granica, którą postawiły 6.A11, 6.A15 i 6.A22. Poza zakresem także postać
  `--opcja=wartość` (6.A22, zrobione) i powtórzona opcja (6.A23).
- **Zależy od:** #303 (6.A11), #346 (6.A15).

##### 6.B32 · Dziennik mutacyjny nie odróżnia dwóch przebiegów na tym samym commicie

- **Skąd:** nazwane wprost przy 6.B19 (#349) — w komentarzu przy miejscu wznawiania
  w `main` i w §5–6 raportu — jako to, czego tamta poprawka **nie** łapie. 6.B19
  dopisała do każdego wpisu dziennika `commit` z `git rev-parse --short HEAD` i odmawia
  wznowienia, gdy dziennik niesie wpis z innego commita. Przy niescommitowanej zmianie
  (albo `--dirty`) commit się **nie zmienia**, a treść mutowanego pliku owszem — więc
  odmowa tego przypadku nie widzi i wznowienie podstawi wynik policzony dla innej
  treści pod dzisiejszą mutację, po cichu.
- **Wejście:** `tools/tests/mutation_sweep.py` (`check_one`, `worker`, `sweep`, miejsce
  wznawiania w `main`), `tools/tests/test_mutation_sweep.py`,
  `reports/dziennik-mutacyjny-bez-drzewa.md` §5–6.
- **Wyjście:** wpis niosący dowód treści, na której powstał — **do rozstrzygnięcia
  pomiarem, nie z góry**: albo `git status --porcelain` zapisywane obok commita (tanie,
  ale mówi tylko „drzewo brudne", nie CO w nim jest), albo SHA-256 samego mutowanego
  pliku przed mutacją (dokładne i lokalne). Pomiar ma powiedzieć, ile kosztuje drugie
  rozwiązanie na pełnym przeglądzie: liczenie odcisku raz na mutację przy dwóch
  tysiącach mutacji może być niezauważalne albo nie, i to jest liczba, nie domysł.
- **Weryfikacja:**
  ```bash
  python3 tools/tests/mutation_sweep.py --only tools/blender/lod_paths.py \
      --journal /tmp/b32/dziennik.jsonl
  # zmiana jednego znaku w tools/blender/lod_paths.py, BEZ commita
  python3 tools/tests/mutation_sweep.py --only tools/blender/lod_paths.py \
      --journal /tmp/b32/dziennik.jsonl
  python3 tools/tests/test_all.py
  ```
  Oczekiwane: drugi przebieg **odmawia** wznowienia, choć `git rev-parse --short HEAD`
  daje w obu tę samą wartość.
- **Skończone, gdy:** dziennik zapisany na drzewie zmienionym bez commita jest przy
  wznowieniu odrzucony — sprawdzone WYKONANIEM obu przebiegów z wklejonym wyjściem
  i kodem wyjścia — a wznowienie na drzewie **niezmienionym** nadal działa i liczy
  tylko to, czego brakuje. Kontrola negatywna WYKONANA wywraca dokładnie nowy test,
  a nie odmowę z 6.B19.
- **Poza zakresem:** zmiana schematu identyfikatora mutacji
  (`plik:wiersz:przesunięcie bajtowe`) — przeliczyłaby dotychczasowe dzienniki
  i zerwała porównywalność z raportami triażu; ta sama granica, którą postawiła 6.B19.
- **Zależy od:** #349 (6.B19).

##### 6.D31 · Trzy metody, których asercje stoją w gałęzi bez strażnika

- **Skąd:** 6.D29 (#352) sklasyfikowała 18 metod testowych C#, u których **wszystkie**
  asercje siedzą w bloku zagnieżdżonym, i **świadomie nie zmieniła treści żadnej** —
  jej zadaniem była klasyfikacja, a wybór kształtu testu jest osobną decyzją. Trzy
  wyszły jako (c): realna usterka bez żadnego strażnika.
  ```
  RunPlanTests.EveryKnownArgumentIsAcceptedOnItsOwnOrNamesWhatItNeeds
  RunPlanTests.NoInputThrows
  TrainProtectionTests.Predkosc_dopuszczalna_jest_odwrotnoscia_krzywej_z_T_311
  ```
  Sprawdzone osobno na `NoInputThrows`: idzie po dziewięciu paskudnych wejściach
  i **wszystkie** asercje poza `IsNotNull` stoją w `if (!plan.IsValid)`. Gdyby rozbiór
  zaczął przyjmować te wejścia jako poprawne, test przestałby sprawdzać cokolwiek
  i nie powiedziałby o tym ani słowa.
- **Wejście:** `tests/Game.Tests/RunPlanTests.cs`, `tests/Sim.Tests/TrainProtectionTests.cs`,
  `reports/galaz-ktora-moze-nie-wejsc.md` (klasyfikacja i uzasadnienie każdej z 18).
- **Wyjście:** każda z trzech metod ma asercję, która **wykonuje się bezwarunkowo** —
  najprościej licznik wejść do gałęzi porównany z liczbą oczekiwaną (`Assert.AreEqual(9,
  ile)` po pętli), ewentualnie rozbicie na `[DataRow]` po jednym wejściu. **Kształt do
  wyboru na podstawie pomiaru**: dla każdej z trzech trzeba najpierw sprawdzić, czy
  gałąź wchodzi dziś dla WSZYSTKICH wejść, czy dla części — bo licznik przybity do
  złej liczby jest kolejną wyrocznią zepsutą w dobrą stronę.
- **Weryfikacja:**
  ```bash
  dotnet test tests/Game.Tests
  dotnet test tests/Sim.Tests
  python3 tools/tests/test_all.py
  ```
  plus **wykonana** kontrola negatywna dla każdej z trzech: gałąź zmuszona do
  niewchodzenia (np. `plan.IsValid` zwracające zawsze `true`) musi wywrócić dokładnie
  ten test, a nie przechodzić.
- **Skończone, gdy:** dla każdej z trzech metod kontrola negatywna WYKONANA — gałąź
  zmuszona do niewchodzenia wywraca ten test — a liczba testów C# nie spada i wynik
  pozostałych jest niezmieniony. Raport podaje dla każdej z trzech, ile razy gałąź
  wchodzi dziś, liczbą.
- **Poza zakresem:** budowanie bramki na ten wzorzec. 6.D29 zmierzyła, że bramka
  syntaktyczna zapaliłaby się na 15 z 18 przypadków POPRAWNYCH, więc zostałaby
  wyłączona; ta pozycja poprawia trzy metody, nie stawia strażnika na przyszłość.
  Poza zakresem także pozostałe 15 metod — mają swoje uzasadnienia w raporcie 6.D29.
- **Zależy od:** #352 (6.D29).

##### 6.B33 · Wzorzec „oczekiwany wyjątek" bez strażnika

- **Skąd:** zmierzone 07.09.2026 przy 6.A23. Dwanaście metod testowych używa wzorca
  ```csharp
  try { Cos(); } catch (FormatException error) { StringAssert.Contains(…); return; }
  Assert.Fail("…");
  ```
  i **wszystkie dwanaście** mają `Assert.Fail` na właściwym miejscu — **za** blokiem
  `try`/`catch`, więc brak wyjątku wywala test. Stan jest dziś czysty i to jest cała
  treść tej pozycji: **nic tego nie pilnuje**, a trzynasta metoda bez `Assert.Fail`
  przeszłaby w milczeniu za każdym razem, gdy kod przestanie rzucać. Dokładnie klasa
  6.B27, gdzie objawem był wyłącznie licznik testów.
- **Uwaga do wykonawcy, z pierwszej ręki:** mój własny, doraźny detektor szukał
  `Assert.Fail` **wewnątrz** bloku `try` i zgłosił wszystkie dwanaście jako usterkę.
  Zero z nich nią było. Wzorzec ma `Assert.Fail` **po** `catch`, nie w `try`, więc
  bramka zbudowana na pierwszym odruchu zapali się na dwunastu poprawnych testach
  i zostanie wyłączona. Kontrola dodatnia (wstrzyknięty test BEZ `Assert.Fail`)
  **i** ujemna (dwanaście prawdziwych milczy) są tu obie obowiązkowe.
- **Wejście:** `tools/tests/csharp_test_methods.py` (`maska`, `czlonkowie`,
  `_koniec_bloku`), `tools/tests/csharp_assertions.py` (wzorzec asercji),
  nowy moduł bramki w `tools/tests/`, `tests/Sim.Tests/InputLogTests.cs`
  i `tests/Sim.Tests/DriverNotchTests.cs` (dwanaście prawdziwych wystąpień).
- **Wyjście:** bramka zgłaszająca metodę testową, w której blok `catch` kończy się
  `return` (albo pochłania wyjątek) i **za** blokiem `try`/`catch` nie ma
  `Assert.Fail` ani innej asercji bezwarunkowej. Plus próg na liczbę rozpoznanych
  wystąpień wzorca, żeby literówka we wzorcu nie dawała zera znalezisk i zielono.
- **Weryfikacja:**
  ```bash
  python3 tools/tests/test_all.py
  ```
  Oczekiwane: bramka widzi **12** wystąpień wzorca i zgłasza **zero** usterek;
  wstrzyknięty test bez `Assert.Fail` jest zgłoszony z imienia.
- **Skończone, gdy:** bramka podaje liczbę rozpoznanych wystąpień i zero usterek na
  dzisiejszym drzewie, kontrola dodatnia na wstrzykniętym wejściu zgłasza metodę
  z imienia, a kontrola ujemna WYKONANA pokazuje, że żaden z dwunastu prawdziwych
  testów nie jest zgłaszany. Liczba testów narzędzi rośnie o liczbę nowych testów
  i jest podana deltą.
- **Poza zakresem:** przepisywanie dwunastu testów na `Assert.ThrowsException` —
  to zmiana kształtu dwunastu poprawnych testów, a nie postawienie strażnika. Poza
  zakresem także `catch` z ponownym rzuceniem (`throw;`), bo tam wyjątek nie ginie.
- **Zależy od:** #348 (6.B28 — `maska()` jest tu warunkiem, bo bez niej przejście po
  ciele metody gubi się na klamrach w napisach).

##### 6.B34 · Wzmianka w napisie i w komentarzu liczona jako odczyt stałej

- **Skąd:** zmierzone 07.09.2026 na wstrzykniętym wejściu, dwiema próbami:
  ```
  stala wymieniona TYLKO w napisie      -> _odczyty daje 1  (wyglada na ZYWA)
  stala wymieniona TYLKO w komentarzu   -> _odczyty daje 1  (wyglada na ZYWA)
  ```
  6.B31 wybrała ten kierunek pomyłki **świadomie** i zapisała to w raporcie: fałszywy
  negatyw (martwa stała uznana za żywą) jest tańszą pomyłką niż bramka zapalająca się
  na poprawnym kodzie. Uzasadnienie było wtedy dobre, bo alternatywa wymagała
  własnego rozbioru literałów. **Od 6.B28 (#348) `maska()` już istnieje** — komentarze
  i literały zamienione na spacje znak w znak — więc koszt zniknął, a wraz z nim
  powód, żeby fałszywy negatyw zostawić.
- **Szczególnie kłopotliwy przypadek:** komentarz **wyjaśniający usunięcie** stałej
  utrzymuje ją w stanie „żywa" na zawsze. Ten projekt takie komentarze pisze
  regularnie (reguła „przepisuj, nie dopisuj obok"), więc mechanizm nie jest
  teoretyczny.
- **Wejście:** `tools/tests/test_dead_constants_csharp.py` (`_odczyty`, `deklaracje`,
  `UZASADNIONE`, `MINIMUM_DEKLARACJI`), `tools/tests/csharp_test_methods.py`
  (`maska`), `reports/martwe-stale-csharp.md` (pomiar 6.B31 i jego uzasadnienie).
- **Wyjście:** `_odczyty` liczy identyfikatory na **masce**, nie na surowym tekście.
  Plus pomiar: **ile stałych** przestaje być czytanych po tej zmianie — bo jeżeli
  któraś okaże się martwa, jej los (usunięcie albo uzasadnienie) rozstrzyga się tak
  samo jak przy 6.B31, czyli po sprawdzeniu, czy należy do udokumentowanego zbioru.
- **Weryfikacja:**
  ```bash
  python3 tools/tests/test_all.py test_dead_constants_csharp.py
  python3 tools/tests/test_all.py
  ```
  Oczekiwane: liczba deklaracji niezmieniona, liczba martwych stałych podana wprost
  (zero albo lista z werdyktem dla każdej).
- **Skończone, gdy:** stała wymieniona wyłącznie w napisie albo w komentarzu jest
  zgłaszana jako nieczytana — pokazane kontrolą dodatnią na wstrzykniętym wejściu —
  a każda stała, którą zmiana ujawni jako martwą, ma werdykt: usunięta albo
  uzasadniona wpisem z powodem. Adnotacja w `reports/martwe-stale-csharp.md` mówi, że
  wybór kierunku pomyłki z 6.B31 przestał być konieczny i dlaczego.
- **Poza zakresem:** rozbiór odczytów poza C# (`.tscn`, `.gd`, `*.sh`, `.github/`) —
  6.B31 zmierzyło tam zero odczytów i warunek zostaje; maska dotyczy plików `.cs`.
- **Zależy od:** #348 (6.B28), #334 (6.B31).

##### 6.A26 · Nic nie pilnuje pomiaru, na którym stoi decyzja 6.A22

- **Skąd:** 6.A22 (#351) odrzuciła postać `--opcja=wartość` **na podstawie pomiaru**:
  344 wystąpienia tej postaci w repozytorium, z tego 96 w komendach sceny Godota
  i **2** w komendach `Sim.Runner` — a oba te dwa są tekstem samej pozycji
  w `docs/TASKS.md`. Decyzja jest dobra dokładnie tak długo, jak długo ten pomiar jest
  prawdziwy.
- **Czego brakuje, i to jest sprostowanie własnego raportu:** §10 raportu
  `reports/postac-z-rownosciem.md` napisał, że gdyby komenda CI zaczęła tej postaci
  używać wobec runnera, „bramka z §5 pokaże to jako FAIL, zamiast czekać na czyjeś
  oko". **To nieprawda.** Bramka z §5
  (`test_no_message_writes_a_known_option_in_the_equals_form`) czyta **wyłącznie**
  `src/Sim.Runner/Program.cs` i pilnuje, żeby komunikaty runnera nie były pisane
  w odrzuconej postaci. Komenda w `.github/workflows/*.yml` albo w `docs/` jest poza
  jej zasięgiem.
- **Wejście:** `tools/tests/test_runner_options.py`, `.github/workflows/*.yml`,
  `docs/**/*.md`, `tools/**/*.sh`, `reports/postac-z-rownosciem.md` §10 (zdanie do
  oznaczenia adnotacją).
- **Wyjście:** bramka klasyfikująca każde wystąpienie postaci `--opcja=wartość`
  w repozytorium po **wołanym programie** — sklejenie kontynuacji wierszy (`\`),
  potem podział na komendy `Sim.Runner`, komendy sceny (`GODOT_BIN`,
  `--path src/Game`) i prozę — i odmawiająca, gdy w komendzie `Sim.Runner` pojawi się
  choć jedna. Plus próg na łączną liczbę wystąpień, żeby literówka we wzorcu nie
  dawała zera i zielono.
- **Weryfikacja:**
  ```bash
  python3 tools/tests/test_all.py
  ```
  Oczekiwane: bramka podaje rozbicie liczbowe (razem / scena / runner / proza)
  i zgłasza zero komend runnera z równością; wstrzyknięta komenda runnera z tą
  postacią jest zgłoszona z plikiem i numerem wiersza.
- **Skończone, gdy:** bramka jest zielona na dzisiejszym drzewie z rozbiciem podanym
  liczbą, kontrola dodatnia na wstrzykniętym wejściu zgłasza komendę z plikiem
  i wierszem, a kontrola ujemna WYKONANA pokazuje, że **żadna** z 96 komend sceny ani
  z prozy nie jest zgłaszana — bo bramka łapiąca scenę zostałaby wyłączona w tym
  samym tygodniu. `reports/postac-z-rownosciem.md` §10 dostaje adnotację mówiącą, co
  tamto zdanie obiecywało i czym to zostało domknięte.
- **Poza zakresem:** obsługa postaci `--opcja=wartość` w runnerze (6.A22 odrzuciła ją
  pomiarem) oraz zmiana konwencji sceny — `RunPlan` tej postaci wymaga i to jest jej
  wybór, przybity 27 testami w `tests/Game.Tests`. Ujednolicenie dwóch połów projektu
  jest decyzją właściciela.
- **Zależy od:** #351 (6.A22).

##### 6.B35 · Przegląd mutacyjny nie dochodzi dziś do końca

- **Skąd:** zmierzone 07.09.2026 przy 6.B20 i **potwierdzone osobno**. Wykonane:
  ```
  $ python3 tools/tests/mutation_sweep.py --only tools/blender/lod_paths.py --workers 1
  [MUTACJE] PRZERWANE — zestaw PADA w czystym drzewie, bez żadnej mutacji (kod 1):
    ['test_the_documented_shortfall_is_written_down_while_it_lasts:',
     'test_the_queue_holds_at_least_a_day_of_work:',
     'test_every_module_delegates_to_the_one_runner:',
     'test_every_test_module_can_be_run_directly:']
  rc=2
  ```
  Dwa ostatnie wiersze są usterką tej pozycji. `OWN_TESTS_STUB` — treść, którą
  `neutralise_own_tests` wpisuje w miejsce `tools/tests/test_mutation_sweep.py` w każdym
  drzewie roboczym — jest **samym docstringiem**, bez strażnika `__main__` i bez
  delegacji do `test_all`. Bramka `test_module_entrypoints.py` (6.D25) żąda obu od
  każdego `test_*.py`, więc kalibracja wyroczni widzi zestaw jako padający i przerywa
  przegląd, zamiast go zacząć.
- **Dlaczego to poważne:** narzędzie jest niesprawne **od scalenia 6.D25** i nikt tego
  nie zauważył, bo od tamtej pory nikt nie odpalił pełnego przeglądu. Kalibracja
  wyroczni jest tu jedyną rzeczą, która zadziałała jak należy: odmówiła zamiast
  policzyć każdą mutację jako zabitą — dokładnie to, przed czym broniła się wersja
  z 05.09.2026 (zaślepka zamiast `os.remove`).
- **Wejście:** `tools/tests/mutation_sweep.py` (`OWN_TESTS_STUB`,
  `neutralise_own_tests`, `add_worktree`, `baseline_problem`),
  `tools/tests/test_module_entrypoints.py` (bramka z 6.D25),
  `tools/tests/test_mutation_sweep.py`, `reports/reszta-czasu-przegladu.md` §1.
- **Wyjście:** zaślepka spełniająca te same reguły, co każdy inny moduł testowy —
  strażnik `__main__` delegujący do `test_all` **i** co najmniej jeden test, bo
  `test_all.main(<plik>)` odmawia przy zerze testów (6.D25). **Do rozstrzygnięcia
  pomiarem, nie z góry**: czy zaślepka z jednym testem nie zmienia liczby testów,
  na której stoi kalibracja wyroczni — bo jeżeli zmienia, trzeba wiedzieć o ile,
  zanim ta liczba zacznie znaczyć coś innego niż dotąd.
- **Weryfikacja:**
  ```bash
  python3 tools/tests/mutation_sweep.py --only tools/blender/lod_paths.py --list
  python3 tools/tests/mutation_sweep.py --only tools/blender/lod_paths.py --workers 2
  python3 tools/tests/test_all.py
  ```
  Oczekiwane: przegląd **dochodzi do końca** i podaje werdykty, a nie kod 2;
  `--list` kończy się kodem 0.
- **Skończone, gdy:** pełny przegląd jednego modułu kończy się werdyktami — pokazane
  WYKONANYM przebiegiem z wklejonym wyjściem i kodem wyjścia — a kontrola negatywna
  WYKONANA: zaślepka pozbawiona strażnika znowu przerywa przegląd, czyli poprawka
  jest tym, co go odblokowało, a nie zbiegiem okoliczności.
- **Poza zakresem:** rozluźnienie bramki z 6.D25. Ona ma rację: moduł testowy bez
  strażnika kończył się kodem 0 nie wykonawszy ani jednego testu, i po to powstała.
  Poza zakresem także zmiana czegokolwiek w tym, **co** przegląd mierzy.
- **Zależy od:** #325 (6.D25).

##### 6.B37 · Nic nie pilnuje, że narzędzie mutacyjne w ogóle się uruchamia

- **Skąd:** 6.B35 przeżyła niezauważona całą dobę, mimo że `tools/tests/test_all.py`
  chodzi po każdym commicie. Powód jest prosty i widać go w obejściu, którego 6.B20
  musiało użyć: **żaden test nie uruchamia narzędzia jego własną drogą** (`main()`),
  wszystkie wołają funkcje wewnętrzne przez `importlib`. Droga, którą chodzi człowiek
  i CI, nie jest sprawdzana wcale.
- **Wejście:** `tools/tests/test_mutation_sweep.py`, `tools/tests/mutation_sweep.py`
  (`main`, `--list`), `reports/reszta-czasu-przegladu.md` §1.
- **Wyjście:** test uruchamiający `mutation_sweep.py --only <jeden moduł> --list`
  jako **proces** (albo `main()` z podmienionym `sys.argv`) i żądający kodu wyjścia 0
  oraz wiersza z liczbą złapanych mutacji. `--list` nie odpala ani jednej mutacji,
  więc koszt jest kosztem samego rozbioru — **do zmierzenia i podania liczbą**, bo
  test w zestawie chodzącym po każdym commicie nie ma prawa kosztować sekund.
- **Weryfikacja:**
  ```bash
  python3 tools/tests/test_all.py test_mutation_sweep.py
  python3 tools/tests/test_all.py
  ```
  Oczekiwane: nowy test przechodzi, a jego czas jest widoczny w tabeli czasów modułów.
- **Skończone, gdy:** test istnieje, przechodzi, a kontrola negatywna WYKONANA —
  zaślepka pozbawiona strażnika (usterka 6.B35) — wywraca **dokładnie** ten test.
  Raport podaje koszt testu liczbą.
- **Poza zakresem:** uruchamianie pełnego przeglądu w zestawie testów. Kalibracja
  wyroczni to jeden pełny zestaw, a sonda pokrycia ponad 400 s (6.B20) — zestaw
  wołający sam siebie nie jest bramką, tylko pętlą.
- **Zależy od:** 6.B35.

##### 6.A27 · Dwie odmowy `compare` bez przedrostka `BŁĄD:`

- **Skąd:** zmierzone 07.09.2026 przy 6.A24, które świadomie tego nie ruszyło i wypisało
  w §8. Wykonane na pliku o złym nagłówku:
  ```
  $ compare /tmp/zle.csv /tmp/zle.csv
  nagłówki telemetrii nie zgadzają się z formatem rdzenia
  ```
  Bez przedrostka — bo ta odmowa wraca `return 1` zamiast rzucić wyjątek łapany
  wspólnym handlerem. Tak samo `różna liczba wierszy: N vs M`. Nowa odmowa komórki
  z 6.A24 i wszystko, co ujednoliciła 6.A16, przedrostek mają.
- **Dlaczego to nie kosmetyka:** kształt wyjścia jest wyrocznią dla czytającego log CI
  i dla `grep`. 6.A16 ujednoliciła nie tylko kod wyjścia, ale i kształt, właśnie po to,
  żeby „odmowa" dała się rozpoznać jednym wzorcem. Dwa wyjątki od tego wzorca psują
  go tak samo, jak jeden komunikat mówiący nieprawdę psuł odmowę przy 6.A22.
- **Wejście:** `src/Sim.Runner/Program.cs` (`Compare`, dwa `return 1` z `Console.Error`),
  `tests/Sim.Tests/RunnerCommandTests.cs`, `tools/tests/test_runner_exit_codes.py`,
  `reports/komorka-csv.md` §8, `reports/kody-wyjscia-runnera.md` (6.A16).
- **Wyjście:** obie odmowy przez wspólny handler (wyjątek), z zachowanym **kodem 1**
  i zachowaną treścią; plus test treści dla obu. **Do sprawdzenia pomiarem**: czy
  któryś skrypt CI albo bramka nie dopasowuje dziś tych dwóch komunikatów **bez**
  przedrostka — jeżeli tak, dopasowanie trzeba poprawić w tym samym commicie, bo
  inaczej pozycja wywróci przebieg, który dziś działa.
- **Weryfikacja:**
  ```bash
  grep -rn "nagłówki telemetrii\|różna liczba wierszy" tools/ .github/ docs/
  dotnet run --project src/Sim.Runner -c Release -- compare build/d1.csv build/d1.csv
  dotnet test tests/Sim.Tests
  ```
  Oczekiwane: grep podaje **liczbę** miejsc dopasowujących te komunikaty, oba
  komunikaty mają przedrostek `BŁĄD:` i kod 1, a porównanie dwóch poprawnych plików
  nadal kończy się kodem 0.
- **Skończone, gdy:** każda odmowa `compare` ma ten sam kształt wyjścia co reszta
  odmów runnera — pokazane WYKONANYMI próbami obu przypadków — a kontrola negatywna
  WYKONANA wywraca dokładnie nowe testy. Liczba miejsc dopasowujących te komunikaty
  jest podana w raporcie, nawet jeśli wynosi zero.
- **Poza zakresem:** zmiana kodów wyjścia (6.A16 rozstrzygnęła) i treści samych
  komunikatów. Poza zakresem także trzecia odmowa tej pętli („zła liczba kolumn"),
  jeżeli pomiar pokaże, że ona już przedrostek ma — wtedy pozycja dotyczy dwóch.
- **Zależy od:** #302 (6.A16), #357 (6.A24).

##### 6.B36 · Sonda pokrycia zjada 78 % czasu przeglądu mutacyjnego

- **Skąd:** zmierzone 07.09.2026 przy 6.B20 jako **fazy jednego ciągłego przebiegu**,
  na module o DWÓCH mutacjach, przy 1, 2 i 4 robotnikach:
  ```
  workers=1: worktree 0,086 s | kalibracja 58,13 s | sonda 426,62 s | robotnicy 115,47 s | CAŁOŚĆ 600,31 s
  workers=2: worktree 0,079 s | kalibracja 60,82 s | sonda 416,74 s | robotnicy  57,55 s | CAŁOŚĆ 535,18 s
  workers=4: worktree 0,108 s | kalibracja 57,79 s | sonda 416,75 s | robotnicy  59,61 s | CAŁOŚĆ 534,26 s
  ```
  Sonda kosztuje więcej niż **cała reszta razem** i dla dwóch mutacji więcej niż sama
  praca. Jej wynik jest potrzebny wyłącznie do rozdzielenia ocalałych na „przeżyła
  MIMO odpalenia" i „nieodpalona" — czyli do etykiety, nie do werdyktu.
- **Wejście:** `tools/tests/mutation_sweep.py` (`coverage_map`, `was_executed`,
  limit czasu sondy), `reports/reszta-czasu-przegladu.md`,
  `reports/czas-przegladu-mutacyjnego.md` (pomiar 6.B18 i jego adnotacja).
- **Wyjście:** **najpierw pomiar, potem kierunek.** Do zmierzenia: czy mapa pokrycia
  zależy od mutowanego modułu (jeśli nie — da się ją policzyć RAZ na commit
  i zapamiętać między przebiegami, kluczując po `git rev-parse HEAD` tak jak
  `default_journal` z #289 i `commit` z 6.B19), i ile z tych ~417 s to sam zestaw,
  a ile narzut instrumentacji. Bez tych dwóch liczb każde skrócenie jest zgadywaniem.
- **Weryfikacja:**
  ```bash
  python3 tools/tests/mutation_sweep.py --only tools/blender/lod_paths.py --workers 2
  python3 tools/tests/mutation_sweep.py --only tools/track/crs.py --workers 2
  python3 tools/tests/test_all.py
  ```
  Oczekiwane: drugi przebieg na TYM SAMYM commicie nie liczy sondy od nowa, a raport
  podaje oszczędność liczbą i dowodzi, że werdykty się nie zmieniły.
- **Skończone, gdy:** czas pełnego przeglądu jednego modułu spada, oszczędność jest
  podana liczbą z co najmniej trzech przebiegów, a **werdykty są identyczne** z tymi
  sprzed zmiany — pokazane porównaniem dziennika wiersz po wierszu. Kontrola negatywna
  WYKONANA: zapamiętana mapa z INNEGO commita musi być odrzucona, a nie użyta.
- **Poza zakresem:** wyłączanie sondy. Bez niej ocalałe trafiają do kupki
  „niezmierzone", co narzędzie mówi wprost w pomocy — ta sama granica, którą postawiła
  6.B20. Poza zakresem także zmiana limitu czasu mutacji: limit jest **wyrocznią** dla
  mutacji powodujących pętlę nieskończoną (zmierzone w 6.B14).
- **Zależy od:** 6.B35 (dopóki przegląd nie dochodzi do końca, nie ma czego mierzyć),
  #349 (6.B19).

##### 6.A28 · Pusta ścieżka telemetrii przechodzi jako plan poprawny

- **Skąd:** zmierzone 07.09.2026 przy 6.D31, i to nie z odczytu kodu, a z licznika,
  który miał wyjść inaczej. `RunPlanTests.NoInputThrows` idzie po dziewięciu paskudnych
  wejściach; licznik odrzuconych miał dać **9**, dał **8**:
  ```
  Assert.AreEqual failed. Expected:<999>. Actual:<8>. paskudnych wejść odrzuconych;
     przyjęte: --telemetry=
  ```
  Wartość tej opcji jest napisem, więc pustka nie wywraca żadnego rozbioru. Pozostałe
  osiem wejść rozbiór odrzuca kodem `UnknownArgument` albo `BadArgumentValue`
  z komunikatem — czyli rodzina jako całość działa i pustka wygląda na przeoczenie,
  nie na decyzję.
- **Co jest, a co nie jest tu problemem:** nie wiadomo — i **nie było mierzone** — co
  scena robi przy zapisie telemetrii do pustej ścieżki. Ta pozycja ma to najpierw
  sprawdzić, bo od tego zależy, czy pustka jest usterką cichą (plik powstaje pod
  dziwną nazwą), czy głośną (wyjątek przy zapisie). Pierwsze jest gorsze i pilniejsze.
- **Wejście:** `src/Game/RunPlan.cs` (rozbiór `--telemetry`, `KnownArguments`,
  `Error`/`ExitCode`), `tests/Game.Tests/RunPlanTests.cs`
  (`NoInputThrows` z przybitą listą `przyjete`), `reports/galaz-bez-straznika.md` §4.
- **Wyjście:** pusta wartość opcji, która oczekuje ścieżki, kończy się odmową
  z komunikatem nazywającym opcję — albo **pomiar pokazujący, że pustka ma tu
  znaczenie** (np. „nie pisz telemetrii"), i wtedy jawny zapis tego znaczenia zamiast
  poprawki. **Do rozstrzygnięcia pomiarem, nie z góry**: które z opcji ścieżkowych
  (`--telemetry`, `--shot`, `--replay`, `--from-telemetry`, `--axis`, `--manifest`,
  `--calls`, `--signalling`, `--input-log`) przyjmują dziś pustkę — bo jeżeli
  wszystkie, poprawka jest jedna i wspólna, a nie dziewięć osobnych.
- **Weryfikacja:**
  ```bash
  dotnet test tests/Game.Tests
  ```
  plus WYKONANA próba sceny z `--telemetry=` (albo, jeżeli Godota nie ma, sam rozbiór
  przez test) z wklejonym wyjściem i kodem.
- **Skończone, gdy:** żadna opcja ścieżkowa nie przyjmuje pustej wartości w milczeniu —
  albo raport nazywa liczbą, ile ich przyjmuje i dlaczego to zostaje — a lista
  `przyjete` w `NoInputThrows` jest zmieniona **razem z poprawką**, nie przy okazji.
  Kontrola negatywna WYKONANA wywraca dokładnie nowe testy.
- **Poza zakresem:** rozbiór wartości NIELICZBOWYCH i nieistniejących ścieżek — to
  osobne klasy błędu, a ta pozycja dotyczy pustki. Poza zakresem także zmiana
  `KnownArguments`.
- **Zależy od:** #362 (6.D31).

##### 6.B38 · Jeden moduł zjada piątą część czasu zestawu

- **Skąd:** zmierzone 07.09.2026 przy 6.B37, przez zdjęcie i przywrócenie dwóch nowych
  testów:
  ```
  test_mutation_sweep.py bez nowych testow:  14.196 s, 69 testow
  test_mutation_sweep.py z nowymi testami:   15.315 s, 71 testow
  caly zestaw:                               76.238 s, 1867 testow, 99 modulow
  ```
  **Adnotacja z 07.09.2026, dopisana przy scaleniu 6.B37 — pomiaru wyżej NIE
  przeliczam, bo tak wymaga `docs/04-conventions.md`.** Drzewo, z którego pochodzi,
  przestało istnieć: praca 6.B37 leżała wtedy wyłącznie jako niezacommitowane zmiany
  i została utracona, a pozycję wykonano ponownie od `origin/main` — tym razem
  z **trzema** testami, nie dwoma, i z medianami z trzech przebiegów w każdą stronę
  zamiast jednej pary:
  ```
  test_mutation_sweep.py bez nowych testow:  14.229 s, 69 testow   (mediana z 3)
  test_mutation_sweep.py z nowymi testami:   14.910 s, 72 testow   (mediana z 3)
  caly zestaw:                               76.651 s, 1868 testow, 99 modulow
  ```
  Dla tej pozycji nie zmienia to niczego w kierunku: moduł nadal jest jedynym, który
  sam z siebie zbliża się do progu z 6.D26, a **liczba testów w nim wzrosła
  z 71 do 72**, więc pole „Wejście" niżej mówi o 71 z daty wpisu, nie z dziś.
  Jeden moduł, **jedna piąta** czasu całego zestawu. Powód jest znany i nie jest
  usterką: testy narzędzia mutacyjnego uruchamiają procesy i zakładają drzewa
  `git worktree`, bo inaczej nie sprawdzają tego, co narzędzie robi naprawdę (6.B37).
- **Dlaczego to jednak pozycja:** próg z 6.D26 stoi na czasie **całego** zestawu, a ten
  moduł jest dziś jedynym, który sam z siebie się do niego zbliża — i każdy następny
  test narzędzia go podnosi. Bez pomiaru, co wewnątrz kosztuje najwięcej, pierwsza
  reakcja na przekroczony próg będzie zdjęciem testów, czyli zapłaceniem ochroną
  za czas.
- **Wejście:** `tools/tests/test_mutation_sweep.py` (71 testów, w tym uruchamiające
  procesy i zakładające drzewa), `tools/tests/test_suite_runtime_budget.py` (próg
  z 6.D26 i jego pomiary), `reports/straznik-na-main.md` §3 i §8,
  `reports/pamiec-ukladu-peronow.md` (wzorzec: pamięć zamiast zdejmowania testów).
- **Wyjście:** **najpierw pomiar per test**, potem kierunek. Do zmierzenia: które
  z 71 testów kosztują ponad 0,1 s i ile ich jest; ile z tego to `git worktree add`,
  ile uruchomienie procesu Pythona, a ile prawdziwa praca. Dopiero z tymi trzema
  liczbami wolno wybierać między współdzieleniem jednego drzewa przez kilka testów,
  pamięcią na wynik, a zostawieniem tego, co jest.
- **Weryfikacja:**
  ```bash
  python3 tools/tests/test_all.py test_mutation_sweep.py
  python3 tools/tests/test_all.py
  ```
  Oczekiwane: czas modułu spada, liczba testów **nie**, a werdykty są te same.
- **Skończone, gdy:** czas modułu jest podany liczbą przed i po, z co najmniej trzech
  przebiegów, liczba testów nie spada ani o jeden, a raport nazywa, ile z oszczędności
  wzięło się z czego. Kontrola negatywna WYKONANA: jeżeli testy zaczynają dzielić
  drzewo, to zepsucie tego drzewa musi wywrócić testy, które z niego korzystają —
  inaczej współdzielenie zamienia je w atrapy.
- **Poza zakresem:** zdejmowanie albo łączenie testów, żeby zejść z czasem. Ochrona
  jest tu droższa od sekund, a 6.B37 właśnie pokazała, ile kosztuje jej brak.
  Poza zakresem także podnoszenie progu z 6.D26.
- **Zależy od:** 6.B37 — **zrobione 07.09.2026**, pomiar w `reports/straznik-na-main.md`. Pierwsza wersja tego pola wskazywała gałąź i numer PR, którego jeszcze nie było; odsyłacz idzie dziś do raportu, bo ten istnieje niezależnie od tego, jak nazwano gałąź.

##### 6.A29 · Test, który przechodzi z całkiem innego powodu, niż sądzi

- **Skąd:** zmierzone 07.09.2026 przy 6.A25, kontrolą negatywną KN-1 (liczba członów
  pozycyjnych `compare` zdjęta z 2 na 0). Pięć testów `compare` wtedy padło, a
  `Zepsuta_komorka_nazywa_zepsuty_plik_a_nie_pierwszy` **został zielony** — mimo że
  mierzy tę samą komendę. Powód, wykonany:
  ```
  $ compare build/zepsuty.csv build/dobry.csv     # przy compare Positional=0
  BŁĄD: polecenie compare dostało człon pozycyjny build/zepsuty.csv, a nie bierze ani
  jednego. Człon bez minusa nie jest opcją, …
  kod=1
  ```
  Trzy asercje tego testu — kod 1, treść zawiera `zepsuty`, treść NIE zawiera `dobry` —
  są spełnione przez komunikat o rzeczy zupełnie innej.
- **Dlaczego to nie jest drobiazg:** test wierzy, że przybija komunikat 6.A24 („odmowa
  nazywa zepsuty plik, a nie pierwszy"). Przybija w rzeczywistości zdanie słabsze:
  „gdzieś w treści stoi pierwsza ścieżka". Każda przyszła regresja w numerze wiersza,
  numerze kolumny albo nazwie kolumny przejdzie przez niego bez śladu, a raport z jego
  zieloności będzie brzmiał tak samo jak dziś. To ten sam gatunek usterki, co 6.D30
  (dwa martwe pola zgadzają się zawsze) i 6.B28 (dwa czytniki z jednym błędem).
- **Wejście:** `tests/Sim.Tests/RunnerCommandTests.cs`
  (`Zepsuta_komorka_nazywa_zepsuty_plik_a_nie_pierwszy` oraz trzy sąsiednie testy
  z 6.A24), `src/Sim.Runner/Program.cs` (`Cell` — pisarz komunikatu),
  `reports/komorka-csv.md`, `reports/czlon-pozycyjny.md` §7.
- **Wyjście:** asercja na te części komunikatu, które 6.A24 wprowadziła i które
  odróżniają go od każdej innej odmowy: numer wiersza, numer kolumny **i** nazwa
  kolumny. **Najpierw pomiar, potem poprawka**: ile z czterech testów 6.A24 ma dziś
  asercję rozstrzygającą, a ile tylko na nazwę pliku — bo jeżeli wszystkie cztery,
  poprawka jest jedna i wspólna, a nie cztery osobne.
- **Weryfikacja:**
  ```bash
  dotnet test tests/Sim.Tests
  ```
  Oczekiwane: cztery testy 6.A24 przechodzą, a kontrola negatywna je wywraca.
- **Skończone, gdy:** kontrola negatywna WYKONANA — ta sama, która to znalazła
  (`compare` z zerową liczbą członów pozycyjnych) — wywraca **wszystkie** testy 6.A24,
  a nie cztery z pięciu. Raport podaje, ile testów miało asercję rozstrzygającą przed
  poprawką i ile po.
- **Poza zakresem:** zmiana treści komunikatu 6.A24 — on ma rację, słaby jest test.
  Poza zakresem także reszta `RunnerCommandTests`: audyt wszystkich asercji tego pliku
  to inna pozycja niż naprawa czterech, które ta wskazuje z nazwy.
- **Zależy od:** 6.A24, 6.A25.

##### 6.B39 · Zawężenie `--only` na nic kończy się zielonym zerem

- **Skąd:** zmierzone 07.09.2026 przy 6.B37. Wykonane:
  ```
  $ python3 tools/tests/mutation_sweep.py --only tools/nie-ma-takiego-pliku.py --list \
        --journal /tmp/n2.jsonl
  [MUTACJE] --only 'tools/nie-ma-takiego-pliku.py' złapało 0 mutacji z 0 moduł(ów):
  razem: 0
  kod: 0
  ```
  Odmowa `brak mutacji do sprawdzenia` (kod 1) stoi **za** gałęzią `--list`, więc
  wypisu nie dotyczy wcale.
- **Dlaczego to nie jest drobiazg:** `--only` dopasowuje **podciąg** ścieżki i to jest
  decyzja z 6.D18, która ma swoje powody. Cena podciągu jest jednak dwustronna: raz
  łapie za dużo (`--only sweep.py` bierze też `tunnel_sweep.py`, zmierzone przy 6.D15)
  i raz za mało — literówka w ścieżce daje zbiór pusty, a wypis wygląda jak poprawny
  przebieg, który po prostu nie miał co robić. Pierwszą stronę 6.D18 już nazwało
  w pierwszym wierszu wypisu; druga nadal milczy kodem 0.
- **Wejście:** `tools/tests/mutation_sweep.py` (`main`, gałąź `--list`, odmowa
  `brak mutacji do sprawdzenia`), `tools/tests/test_mutation_sweep.py`
  (`test_the_cli_lists_mutations_as_a_process_and_exits_zero` i sąsiednie testy CLI),
  `reports/straznik-na-main.md` §8.
- **Wyjście:** odmowa dla `--only`, które nie złapało **ani jednego** modułu — z kodem
  różnym od 0 i z komunikatem nazywającym wzorzec. **Do rozstrzygnięcia pomiarem, nie
  z góry**: czy odmowa ma być na pustym zbiorze MODUŁÓW, czy MUTACJI, bo to nie to samo
  (moduł bez ani jednej mutacji jest możliwy i nie jest błędem wywołania), i czy któryś
  przebieg w `reports/` albo w workflowach polega dziś na `--only` łapiącym zero.
- **Weryfikacja:**
  ```bash
  python3 tools/tests/mutation_sweep.py --only tools/nie-ma-takiego-pliku.py --list
  python3 tools/tests/test_all.py test_mutation_sweep.py
  ```
  Oczekiwane: pierwsza komenda odmawia i nazywa wzorzec; druga przechodzi w całości,
  bo `--only tools/track/` i `--only sweep.py` łapią po kilka modułów i mają zostać.
- **Skończone, gdy:** `--only` bez trafień kończy się kodem różnym od 0 i nazywa
  wzorzec, a kontrola negatywna WYKONANA: `--only` z trafieniami (`tools/track/`,
  `sweep.py`, jeden plik) nadal kończy się kodem 0 — z wklejonym wyjściem wszystkich
  trzech, bo odmowa zbudowana zbyt szeroko wywróciłaby całą drogę `--list`, a testy
  odmowy byłyby wtedy nadal zielone.
- **Poza zakresem:** zmiana dopasowania `--only` z podciągu na nazwę pliku — decyzja
  6.D18, z powodem wypisanym w kodzie; ta pozycja dotyczy zbioru PUSTEGO, nie za
  szerokiego. Poza zakresem także odmowa dla przebiegu bez `--only`.
- **Zależy od:** 6.D18, 6.B37.

##### 6.A30 · Pięć wypisów informacyjnych idzie na stderr, a te same znaczniki także na stdout

- **Skąd:** zmierzone 07.09.2026 przy 6.A27, przejściem po `Program.cs` bez komentarzy.
  Wypisów `[XXX]` jest **52**: **47** na stdout i **5** na stderr:
  ```
  426  [RDZEŃ]
  612  [LIMIT]
  712  [ODTWORZENIE]
  725  [ATP]
  735  [ODTWORZENIE]
  ```
  Rzecz, która czyni z tego usterkę, a nie decyzję: `[RDZEŃ]`, `[ODTWORZENIE]`
  i `[ATP]` występują **na obu strumieniach**. Czytający, który potokuje stdout,
  dostaje część wierszy `[ODTWORZENIE]` i nie dostaje reszty.
- **Dlaczego to nie kosmetyka:** ten sam powód, który 6.A16 i 6.A27 podały dla odmów.
  Kształt wyjścia jest wyrocznią dla czytającego log CI i dla `grep`; znacznik, który
  raz idzie tu, a raz tam, psuje rozpoznanie jednym wzorcem. Dodatkowo `2>/dev/null`
  — odruch przy skryptach — usuwa wtedy część **wyniku**, nie tylko diagnostyki.
- **Wejście:** `src/Sim.Runner/Program.cs` (pięć wierszy wyżej, `Drive`, `Replay`),
  `tests/Sim.Tests/RunnerCommandTests.cs`, `tools/tests/test_runner_exit_codes.py`,
  `reports/przedrostek-compare.md`, `reports/kody-wyjscia-runnera.md` (6.A16).
- **Wyjście:** **najpierw pomiar, potem kierunek.** Do zmierzenia: które z tych pięciu
  wierszy są duplikatem wiersza, który już idzie na stdout, a które są unikalne — bo
  duplikat wolno usunąć, a unikalny trzeba przenieść. Do sprawdzenia osobno, czy
  któryś test C# albo krok CI czyta te wiersze **ze stderr** (`result.StdErr`,
  `2>&1`), bo wtedy przeniesienie wywróci przebieg, który dziś działa. Dopiero z tymi
  dwiema liczbami wolno przenosić.
- **Weryfikacja:**
  ```bash
  grep -rn "StdErr" tests/Sim.Tests/ | grep -c "RDZEŃ\|ODTWORZENIE\|ATP\|LIMIT"
  dotnet run --project src/Sim.Runner -c Release -- replay --keys tests/data/manual-keys.log 2>/dev/null
  dotnet test tests/Sim.Tests
  ```
  Oczekiwane: liczba miejsc czytających te wiersze ze stderr jest podana, a przebieg
  z `2>/dev/null` nie traci ani jednego wiersza `[XXX]`.
- **Skończone, gdy:** żaden znacznik `[XXX]` nie występuje na obu strumieniach —
  pokazane pomiarem przed i po — a kontrola negatywna WYKONANA: przywrócenie jednego
  wiersza na stderr wywraca dokładnie nowy test, a nie tylko liczbę wypisów. Raport
  podaje, ile z pięciu było duplikatami, a ile unikalnymi.
- **Poza zakresem:** treść samych wypisów i to, które polecenia je produkują. Poza
  zakresem także `BŁĄD:` i `nieznane polecenie:` — one na stderr **należą** i to
  rozstrzygnęły 6.A16 oraz 6.A27.
- **Zależy od:** 6.A16, 6.A27.

##### 6.A31 · Dwie komendy w `reports/` cytują katalog, którego nie ma

- **Skąd:** zmierzone 07.09.2026 przy 6.A26, przy okazji wykrywania wołań runnera:
  ```
  reports/T-311-braking.md:257    Sim.Runner/bin/Release/net8.0/…
  reports/T-400-first-run.md:235  Sim.Runner/bin/Release/net8.0/…
  reports/linecore-budget.md:91   Sim.Runner/bin/Release/net10.0/…
  $ grep TargetFramework src/Sim.Runner/Sim.Runner.csproj
      <TargetFramework>net10.0</TargetFramework>
  ```
- **Dlaczego to jednak pozycja, choć pomiarów się nie przelicza:** te dwa raporty są
  pomiarami z datą i miały rację w dniu, w którym je wykonano — ich się **nie rusza**.
  Rzeczą, której brakuje, jest **bramka**: `test_report_hygiene.py` sprawdza, czy każda
  ścieżka wymieniona w raporcie rozwiązuje się w drzewie, ale ścieżka **w komendzie**
  wskazująca na katalog wytworzony przez budowanie nie jest tym samym co ścieżka do
  pliku w repozytorium — i nikt jej nie sprawdza. Pole „Weryfikacja" pozycji cytujące
  taką ścieżkę byłoby niewykonalne, a nikt by tego nie zauważył.
- **Wejście:** `tools/tests/test_report_hygiene.py`, `reports/T-311-braking.md`,
  `reports/T-400-first-run.md`, `reports/linecore-budget.md`,
  `src/Sim.Runner/Sim.Runner.csproj` (`TargetFramework`), `docs/TASKS.md` (pola
  „Weryfikacja" wszystkich pozycji).
- **Wyjście:** bramka wyprowadzająca `TargetFramework` **z pliku projektu** i zgłaszająca
  każdą komendę w `reports/` i w `docs/`, która cytuje inny `netX.Y` w ścieżce
  `bin/`. **Do rozstrzygnięcia pomiarem:** ile takich ścieżek jest w całym drzewie
  i ile z nich stoi w polu „Weryfikacja" (te są groźne) wobec prozy raportu (te są
  pomiarem z datą i dostają adnotację, nie poprawkę).
- **Weryfikacja:**
  ```bash
  python3 tools/tests/test_all.py test_report_hygiene.py
  python3 tools/tests/test_all.py
  ```
  Oczekiwane: bramka podaje liczbę ścieżek z niezgodnym `netX.Y` i wskazuje plik
  z numerem wiersza; kontrola dodatnia na wstrzykniętej ścieżce zgłasza ją.
- **Skończone, gdy:** bramka jest zielona na dzisiejszym drzewie po dopisaniu
  adnotacji do dwóch raportów (albo po dodaniu ich do listy usprawiedliwień z powodem),
  kontrola dodatnia WYKONANA na wstrzykniętej ścieżce `net8.0`, a kontrola ujemna
  WYKONANA pokazuje, że ścieżka `net10.0` **nie** jest zgłaszana. Liczba ścieżek jest
  w raporcie podana, także jeśli wynosi trzy.
- **Poza zakresem:** przeliczanie pomiarów w tych dwóch raportach — one mają datę.
  Poza zakresem także zmiana `TargetFramework` i sprawdzanie, czy komenda **działa**;
  to jest bramka na spójność ścieżki z plikiem projektu, nie na wykonanie.
- **Zależy od:** 6.D3, 6.A26.

##### 6.A32 · Nic nie pilnuje, że asercja jest rozstrzygająca, a nie tylko prawdziwa

- **Skąd:** cztery przypadki zmierzone **w jednym dniu**, każdy inną kontrolą
  negatywną, wszystkie tego samego kroju:

  | pozycja | co pokazała kontrola |
  |---|---|
  | 6.A25 (KN-2) | odmowa z własną stałą zamiast odczytu z tabeli — **wszystkie 584 testy C# zielone** |
  | 6.A26 (KN-D) | reguła pierwszeństwa sceny pilnowana wyłącznie komentarzem — **15/15 zielone** |
  | 6.A27 (KN-2) | `throw` istnieje, cztery `Console.Error` obok — **stara bramka zielona** |
  | 6.A29 (KN-1) | `Contains(ścieżka)` spełnione przez odmowę o czymś zupełnie innym |

  Wspólna cecha wszystkich czterech: asercja na **obecność** czegoś dobrego zamiast na
  **brak** czegoś złego albo na **liczbę**.
- **Dlaczego to nie jest pozycja wymyślona na miejscu:** nie jest pomysłem, a czterema
  wykonanymi pomiarami z jednego dnia, każdy z wklejonym wyjściem w swoim raporcie.
  Wzorzec jest przy tym **wykrywalny mechanicznie**: asercja postaci
  `assert X in Y` / `StringAssert.Contains` bez towarzyszącego licznika albo bez
  asercji na brak.
- **Wejście:** `tools/tests/*.py` (wszystkie asercje `in`), `tests/**/*.cs`
  (`StringAssert.Contains`, `Assert.IsTrue(... .Contains(...))`),
  `tools/tests/csharp_assertions.py`, raporty `czlon-pozycyjny.md` §3,
  `pomiar-rownosci.md` §3, `przedrostek-compare.md` §4, `asercja-rozstrzygajaca.md` §2.
- **Wyjście:** **najpierw pomiar, i to on rozstrzyga, czy jest tu w ogóle pozycja.**
  Do zmierzenia: ile asercji w zestawie ma postać „obecność bez licznika i bez
  asercji na brak", w rozbiciu na Pythona i C#. Dopiero z tą liczbą wolno wybierać
  między bramką (jeżeli liczba jest mała i da się ją utrzymać na liście), progiem
  (jeżeli jest duża) i **niczym** (jeżeli okaże się, że większość takich asercji jest
  rozstrzygająca z innego powodu — na przykład sąsiaduje z asercją na brak).
- **Weryfikacja:**
  ```bash
  python3 tools/tests/test_all.py
  ```
  Oczekiwane: liczba podana w rozbiciu, a każdy wybór kierunku uzasadniony tą liczbą,
  nie przekonaniem.
- **Skończone, gdy:** liczba jest podana dla Pythona i dla C# osobno, a jeżeli
  powstaje bramka — kontrola dodatnia WYKONANA na jednej z czterech asercji wymienionych
  wyżej (przywróconej do stanu przed poprawką) i kontrola ujemna WYKONANA pokazująca,
  że asercje rozstrzygające **nie** są zgłaszane. Jeżeli pomiar pokaże, że bramki nie
  warto stawiać, raport mówi to wprost i pozycja kończy się bez zmiany w kodzie —
  **to też jest poprawnym wynikiem**.
- **Poza zakresem:** poprawianie asercji hurtem. Cztery przypadki z tego dnia są już
  naprawione u siebie; ta pozycja dotyczy tego, czy da się je wykrywać, a nie
  przepisywania zestawu.
- **Zależy od:** 6.A25, 6.A26, 6.A27, 6.A29, 6.D28.

##### 6.B40 · Domyślna ścieżka dziennika nie niesie odcisku treści

- **Skąd:** zmierzone 07.09.2026 przy 6.B32. `default_journal` składa nazwę z trzech
  rzeczy — commita, klas operatorów i `--only` — więc po dopisaniu odcisku treści dwa
  przebiegi na tym samym commicie **dzielą** ścieżkę:
  ```
  czyste: /tmp/metro-mutacje-58804969c2a4.jsonl
  brudne: /tmp/metro-mutacje-58804969c2a4.jsonl     ← ta sama nazwa
  odcisk: 4e495be9c4159f96                          ← inna treść
  ```
- **Dlaczego to pozycja, a nie usterka 6.B32:** odmowa **działa** i to jest ważne —
  cudzy wynik nie wchodzi. Ale skutek jest taki, że przebieg `--dirty` na tym samym
  commicie wymaga podania `--journal` **ręcznie**, a docstring `default_journal` mówi
  wprost, że nazwa zawiera „trzy rzeczy, które rozstrzygają, CZEGO przebieg dotyczy".
  Po 6.B32 tych rzeczy jest **cztery** — i to jest niezgodność między tym, co funkcja
  obiecuje, a tym, co robi.
- **Wejście:** `tools/tests/mutation_sweep.py` (`default_journal`, `main`),
  `tools/tests/test_mutation_sweep.py`
  (`test_domyslny_dziennik_jest_jeden_na_przebieg_a_nie_jeden_na_maszyne`),
  `reports/odcisk-tresci-dziennika.md` §2 i §9, `reports/dziennik-mutacyjny-bez-drzewa.md`.
- **Wyjście:** odcisk w znaczniku nazwy — **albo pomiar pokazujący, że tak być NIE ma**.
  Do rozstrzygnięcia: czy wznowienie po **zacommitowaniu** zmiany ma znaleźć dziennik
  z przebiegu sprzed commita. Dziś nie znajdzie (inny commit → inna nazwa) i to jest
  poprawne; po dodaniu odcisku nie znajdzie też dziennika z tego samego commita i innej
  treści, co też jest poprawne. Trzeba jednak sprawdzić, ile dzienników zostaje wtedy
  w `/tmp` przy pracy na brudnym drzewie — bo nazwa zmieniająca się przy każdym
  zapisie pliku zamienia wznowienie w fikcję.
- **Weryfikacja:**
  ```bash
  python3 tools/tests/test_all.py test_mutation_sweep.py
  python3 tools/tests/mutation_sweep.py --only tools/blender/lod_paths.py --list
  # zmiana jednego znaku bez commita, potem to samo
  ```
  Oczekiwane: dwie różne ścieżki domyślne dla dwóch różnych treści, przy tym samym
  commicie — obie wypisane.
- **Skończone, gdy:** dwa przebiegi na tym samym commicie i różnej treści używają
  **różnych** ścieżek domyślnych, pokazane WYKONANIEM z wklejonymi obiema nazwami,
  a wznowienie na treści **niezmienionej** nadal trafia w ten sam plik. Kontrola
  negatywna WYKONANA: zdjęcie odcisku ze znacznika wywraca dokładnie nowy test.
  Raport podaje, ile dzienników powstaje przy pracy na brudnym drzewie.
- **Poza zakresem:** sprzątanie starych dzienników z `/tmp` i zmiana katalogu, w którym
  stoją. Poza zakresem także odmowa z 6.B32 — ona zostaje niezależnie od nazwy.
- **Zależy od:** 6.B19, 6.B32.

##### 6.B41 · Gałąź „nie ma czego liczyć" nazywa złą przyczynę i kończy się kodem 1

- **Skąd:** zmierzone 07.09.2026 przy 6.B32, drugim przebiegiem na czystym drzewie:
  ```
  [MUTACJE] wznowienie z /tmp/b32/dziennik.jsonl: 2 z 2 już policzonych
  brak mutacji do sprawdzenia po odfiltrowaniu nieosiągalnych
  kod=1
  ```
  Filtr nieosiągalnych nie odsiał **niczego** — zbiór jest pusty, bo wznowienie
  policzyło wszystko. `if not found:` w `main` nie odróżnia tych dwóch przyczyn
  i wypisuje jedną, nieprawdziwą.
- **Dlaczego to dwie rzeczy w jednej pozycji:** komunikat i kod wyjścia wychodzą
  z **tych samych trzech wierszy**. Rozbicie na dwie pozycje dałoby dwie gałęzie
  dotykające jednego `if`, a to jest przepis na konflikt bez żadnego zysku.
  Kod 1 znaczy tu „nie zostało nic do policzenia" — dla skryptu CI uruchamiającego
  przegląd w pętli do skutku jest to różnica między „gotowe" i „awaria".
- **Wejście:** `tools/tests/mutation_sweep.py` (`main`, gałąź `if not found:` oraz
  wcześniejsza `if not found and not done:`), `tools/tests/test_mutation_sweep.py`,
  `reports/odcisk-tresci-dziennika.md` §9, `reports/kody-wyjscia-runnera.md` (6.A16 —
  wzorzec: kod wyjścia jest wyrocznią i ma jedno znaczenie).
- **Wyjście:** komunikat nazywający **rzeczywistą** przyczynę pustego zbioru — filtr
  nieosiągalnych, wznowienie, albo `--limit` — i kod wyjścia **0**, gdy przyczyną jest
  wznowienie, bo przebieg zrobił wszystko, o co go proszono. **Do rozstrzygnięcia
  pomiarem:** ile miejsc w `reports/` i w workflowach polega dziś na kodzie 1 z tej
  gałęzi, bo zmiana kodu wyjścia bez tego pomiaru wywróci przebieg, który dziś działa.
- **Weryfikacja:**
  ```bash
  python3 tools/tests/mutation_sweep.py --only tools/blender/lod_paths.py \
      --journal /tmp/b41/d.jsonl --workers 2 --no-coverage
  python3 tools/tests/mutation_sweep.py --only tools/blender/lod_paths.py \
      --journal /tmp/b41/d.jsonl --workers 2 --no-coverage
  python3 tools/tests/test_all.py test_mutation_sweep.py
  ```
  Oczekiwane: drugi przebieg mówi, że wszystko jest już policzone, i kończy się kodem
  **0**; przebieg, w którym zbiór wyczyścił filtr nieosiągalnych, dalej mówi o filtrze.
- **Skończone, gdy:** obie przyczyny mają swój komunikat, sprawdzone WYKONANIEM obu
  przypadków z wklejonym wyjściem i kodem, a liczba miejsc polegających na dzisiejszym
  kodzie 1 jest w raporcie podana — także jeśli wynosi zero. Kontrola negatywna
  WYKONANA wywraca dokładnie nowe testy.
- **Poza zakresem:** kody wyjścia pozostałych odmów przeglądu (2 dla dziennika
  z innego drzewa i dla brudnych plików) — rozstrzygnięte przy 6.B19 i 6.B32.
- **Zależy od:** 6.B19, 6.B32.

##### 6.B42 · Raport przeglądu identyfikuje pomiar samym commitem

- **Skąd:** zmierzone 07.09.2026 przy 6.B32. Nagłówek raportu przeglądu to
  `**Snapshot na commicie:** {commit}`, a `report(results, commit)` nie dostaje odcisków
  treści **wcale**. Po 6.B32 wiadomo, że commit nie odróżnia dwóch przebiegów na tej
  samej rewizji — więc raport z przebiegu `--dirty` jest nieodróżnialny od raportu
  z drzewa czystego.
- **Dlaczego to ta sama rodzina, co 6.D3:** 6.D3 postawiło bramkę na to, żeby każdy
  `reports/*.md` mówił, na jakim commicie powstały jego liczby. Powód był ten sam:
  liczba bez drzewa, z którego pochodzi, nie da się odtworzyć. Raport przeglądu
  mutacyjnego commit podaje — i to jest za mało dokładnie o tyle, o ile za mało było
  go w dzienniku.
- **Wejście:** `tools/tests/mutation_sweep.py` (`report`, wywołanie w `main`),
  `tools/tests/test_mutation_sweep.py` (rodzina `test_report_*`),
  `reports/mutation-sweep.md`, `reports/mutation-drift.md`,
  `reports/odcisk-tresci-dziennika.md` §2, `tools/tests/test_report_hygiene.py` (6.D3).
- **Wyjście:** odciski w nagłówku raportu — **do rozstrzygnięcia pomiarem, w jakiej
  postaci**: jeden odcisk całego przebiegu (krótki, ale nie mówi, który moduł się
  różni) albo tabela plik → odcisk (dokładna, ale przy 63 modułach zajmuje ekran).
  Pomiar ma powiedzieć, ile modułów ma typowy przebieg z `reports/`: jeżeli triaż
  chodzi po jednym module naraz, tabela jest darmowa.
- **Weryfikacja:**
  ```bash
  python3 tools/tests/test_all.py test_mutation_sweep.py
  python3 tools/tests/test_all.py test_report_hygiene.py
  ```
  Oczekiwane: nagłówek raportu niesie odcisk każdego modułu przebiegu, a bramka
  higieny raportów nadal przechodzi.
- **Skończone, gdy:** raport z przebiegu na treści zmienionej bez commita jest
  **odróżnialny** od raportu z drzewa czystego — pokazane WYKONANIEM obu i wklejonymi
  nagłówkami — a kontrola negatywna WYKONANA (zdjęty odcisk z nagłówka) wywraca
  dokładnie nowy test. Liczba modułów typowego przebiegu jest w raporcie podana.
- **Poza zakresem:** przeliczanie istniejących `reports/mutation-*.md` — są pomiarami
  z datą i dostają adnotację, nie poprawkę. Poza zakresem także format samych sekcji
  raportu.
- **Zależy od:** 6.D3, 6.B32.

##### 6.A19 · Odmowa `replay` mówi nieprawdę o tym, czego odmawia

- **Skąd:** wiersz w „Czego agent nie ruszy bez decyzji" wyliczał trzy wykluczające się
  odczytania; **rozstrzygnięte 07.09.2026 na (a)** — odmowa zostaje na stałe i jest
  udokumentowaną własnością polecenia. Zmierzone dziś w
  `tests/Sim.Tests/RunnerCommandTests.cs:594`: `replay … --coast-from-m 250` kończy się
  kodem **1** i komunikatem zawierającym `nie zna opcji`. Zdanie jest **nieprawdziwe
  co do sensu**: runner tę opcję zna, przyjmuje ją w `line` i w `budget` (6.A18), a
  `replay` jej odmawia **z powodu**, nie z niewiedzy. Czytający dostaje diagnozę
  „literówka" na zachowanie, które jest projektem.
- **Dlaczego to ta sama rodzina, co 6.A22:** tam `line --limit-kmh=72` dostawało
  `nie zna opcji --limit-kmh=72` o opcji stojącej w `KnownOptions`, i poprawką była
  treść komunikatu, nie zachowanie. Tu jest to samo o jeden krok dalej: nie postać
  członu, a przynależność opcji do polecenia.
- **Wejście:** `src/Sim.Runner/Program.cs` (`Replay`, `Nieznana`, tabela `KnownOptions`),
  `tests/Sim.Tests/RunnerCommandTests.cs`
  (`Replay_nie_zna_wybiegu_bo_odtwarza_zapis_wejsc`, wiersz 594),
  `tools/tests/test_runner_options.py` (bramka zgodności tabeli z kodem),
  `reports/wybieg-poza-poleceniem-line.md` §1 (rozbiór trzech odczytań),
  blok 6.A18 wyżej w tym pliku (pomiar, z którego wyszło pytanie).
- **Wyjście:** odmowa `replay --coast-from-m` z komunikatem, który **nazywa powód**
  — odtworzenie zapisu wejść z `--keys` idzie przez `TrainController` i `DriverNotch`,
  więc nastawa automatu nadpisałaby to, co zrobił maszynista. Do tego zdanie o decyzji
  właściciela w dokumentacji XML polecenia, z datą, żeby zniesienie odmowy było
  decyzją podjętą, a nie skutkiem ubocznym czyjegoś refaktoru.
- **Weryfikacja:**
  ```bash
  dotnet test tests/Sim.Tests
  python3 tools/tests/test_all.py test_runner_options.py
  ```
  Oczekiwane: `replay … --coast-from-m 250` nadal kończy się kodem **1**, ale komunikat
  wymienia `--keys` albo `zapis wejść` jako powód; bramka zgodności tabeli z kodem
  zielona — opcja **nie** wchodzi do `KnownOptions` przy `replay`.
- **Skończone, gdy:** komunikat odmowy nie zawiera już frazy `nie zna opcji` dla
  `--coast-from-m` w `replay`, a zawiera powód; kod wyjścia jest **niezmieniony**
  (1, pokazane wykonaniem obu przebiegów); kontrola negatywna WYKONANA — zdjęcie
  powodu z komunikatu wywraca dokładnie jeden test, a wpisanie `--coast-from-m` do
  `KnownOptions` przy `replay` wywraca bramkę Pythona. Liczba testów `dotnet test`
  podana przed i po.
- **Poza zakresem:** odczytania **(b)** i **(c)** z wiersza decyzji — wybieg
  nadpisujący zapis pod inną nazwą polecenia oraz drugi tryb `replay`, w którym
  prowadzi automat. Decyzja wybrała (a); wprowadzenie któregokolwiek z tamtych byłoby
  zmianą decyzji, nie wykonaniem tej pozycji. Poza zakresem także dołożenie wybiegu
  do jakiegokolwiek dalszego polecenia.
- **Zależy od:** 6.A18 (pomiar trójstronny, z którego wyszło pytanie), 6.A22 (wzorzec
  poprawki treści odmowy), 6.A11 (mechanizm odmowy nieznanej opcji).

##### 6.B43 · Ukrycie kamery goniącej kończy się tam, gdzie kadr jest jeszcze biały

- **Skąd:** decyzja właściciela z 05.09.2026 ukryła widok `chase` na paśmie
  **0..94,0 m** — „dopóki cały skład nie wjedzie na oś" — a `ChaseCameraAim.Availability`
  realizuje to jako `frontChainageM > trainLengthM`, czyli funkcję samej długości M7.
  Pasmo **94..106 m** zostało wtedy świadomie odsłonięte i wpisane do „Czego agent nie
  ruszy bez decyzji", bo za granicą kamera jest już za ogonem, ale bliżej niż nominalne
  12,0 m. **Rozstrzygnięte 07.09.2026: rozciągnąć ukrycie do 110 m.**
- **Czego pomiar NIE mówi, a wyglądałby, jakby mówił:** seria z 05.09.2026 jest
  niemonotoniczna. Ułamek pikseli o jasności > 0,80 w górnych 60 % kadru:
  20 m → 0,1 %, 48 m → 56,4 %, 50 m → 38,3 %, **90 m → 0,0 %**, **96 m → 42,0 %**,
  110 m → 0,0 %, 2000 m → 0,0 %. Między 90 m i 110 m jest więc dziura 20 m z jednym
  jasnym punktem w środku, a 110 m to **najniższy zmierzony czysty punkt powyżej 96 m**,
  nie zmierzony początek czystego pasma. Pozycja ma tę dziurę domierzyć.
- **Wejście:** `src/Game/World/ChaseCameraAim.cs` (`Availability`, `IsAvailable`,
  `ChaseAvailability.Reason`, `ChaseFraming.CameraWithinTrainSpan`),
  `src/Game/FirstRun.cs` (`_chaseAvailable`, odmowa `--shot --view=chase`, szósty
  wiersz HUD-u), `src/Game/DesignAssumptions.cs`,
  `tests/Game.Tests/ChaseCameraAimTests.cs`, `data/vehicle/m7-spec.json` (94,0 m,
  status `spec`), wiersz 6.B11 w tabeli fazy 6 (pełny pomiar z 05.09.2026).
- **Wyjście:** próg odsłonięcia jako **osobna stała** obok długości składu — ukrycie
  do `max(trainLengthM, próg)` — z pomiarem gęstszym niż dzisiejsza siatka: co **2 m**
  na paśmie 90..112 m, wynik w raporcie w `reports/`. Jeżeli pomiar pokaże, że czyste
  pasmo zaczyna się wcześniej niż 110 m, **liczba właściciela zostaje** (110 m jest
  decyzją, nie wynikiem pomiaru), a raport nazywa różnicę.
- **Weryfikacja:**
  ```bash
  dotnet test tests/Game.Tests
  $GODOT_BIN --path src/Game -- --shot --view=chase --at-m=96 --out=build/chase-96.png
  ```
  Oczekiwane: przy czole 96 m zrzut **odmawia** (kod 13, tak jak dziś odmawia przy
  50 m), a przy 112 m zapisuje plik; `ChaseAvailability.Reason` podaje 110,0 m, nie
  94,0 m, i podaje **jedną** liczbę — HUD i odmowa nie mogą się rozjechać.
- **Skończone, gdy:** pasmo 90..112 m jest zmierzone co 2 m (**12 punktów**), każdy
  z ułamkiem jasnych pikseli w raporcie; odmowa i wiersz HUD-u mówią 110,0 m; test na
  tożsamość `Availability` z `CameraWithinTrainSpan` jest **przepisany, a nie usunięty**
  — po zmianie te dwa twierdzenia przestają być tożsame i to musi być w kodzie
  napisane, nie przemilczane. Kontrola negatywna WYKONANA: powrót progu do długości
  składu wywraca dokładnie test na nową granicę.
- **Poza zakresem:** cokolwiek estetycznego w samym kadrze goniącym — odstęp, wysokość,
  punkt celowania. Pozycja rusza **granicę dostępności**, nie kompozycję. Poza zakresem
  także wyciszanie ostrzeżeń Godota; tym zajęło się #226 i bramka
  `tools/ci/assert_no_godot_warnings.py`.
- **Zależy od:** 6.B11 (obie połowy, w `main`), decyzji właściciela z 05.09.2026
  (pasmo 0..94,0 m) i z 07.09.2026 (rozciągnięcie do 110 m). **Wymaga Godota** — sam
  `dotnet test` przybije arytmetykę, ale nie zmierzy ani jednego piksela.

##### 6.B44 · Profil pionowy pakietu A z dziurą nazwaną, a nie zinterpolowaną

- **Skąd:** T-112 stoi zablokowane od początku, bo dwa oficjalne źródła podają sprzeczne
  głębokości stacji. R-007 wpisało **trzy** wartości do `data/network/station-depths.csv`
  (De Brouckère `-12,0`, Parc `-20,0`, Arts-Loi `-12,0`, wszystkie `estimated`), a
  dziewięć wierszy zostało `unknown`. **Rozstrzygnięte 07.09.2026: budować z jawnym
  `unknown`** — trzy znane wchodzą do profilu, dziewięć zostaje nazwane niewiadomą.
- **Co jest dziś mierzalnie nie tak:** `grep -rln station-depths` daje w całym drzewie
  **jeden** konsument — `tools/tests/test_platform_dimensions.py`. Plik z danymi, po
  który nie sięga ani jedno narzędzie, nie ma jak się zestarzeć widocznie: wpisanie
  do niego dziesiątej głębokości nie zmieni dziś ani jednego bajtu wyjścia.
- **Wejście:** `data/network/station-depths.csv` (**tylko do odczytu**, `CLAUDE.md`
  §4.6), `data/track/L1_A.json` (oś i kilometraże stacji po #86),
  `tools/track/build_alignment.py` i `tools/track/network_chainage.py` (wzorzec
  narzędzia i wzorzec czytania kilometraży), `tools/blender/tunnel_manifest.py`
  (`flat-preview` / `production`, wiersze 178–186), `docs/21-measured-vs-assumed.md`,
  `reports/R-007-platform-dimensions.md` (skąd trzy wartości i dlaczego `estimated`).
- **Wyjście:** `tools/track/vertical_profile.py` — czyta oś i CSV, pisze do `build/`
  profil, w którym **każdy** punkt niesie albo rzędną z interpolacji między dwiema
  ZNANYMI stacjami, albo `"depth_m": null, "confidence": "unknown"`. Interpolacja
  **nie przechodzi** przez wiersz `unknown`: odcinek między dwiema niewiadomymi jest
  niewiadomą, nie prostą. Do tego testy w `tools/tests/` i raport z pokryciem osi
  w metrach i procentach.
- **Weryfikacja:**
  ```bash
  python3 tools/track/vertical_profile.py --axis data/track/L1_A.json \
      --depths data/network/station-depths.csv --out build/L1_A-vertical.json
  python3 tools/tests/test_all.py
  ```
  Oczekiwane: kod 0, wypis z liczbą metrów osi ze rzędną i bez, oraz zestaw zielony.
- **Skończone, gdy:** raport podaje **ile metrów z 6686,35 m osi pakietu A dostaje
  rzędną, a ile zostaje `unknown`**, obie liczby z wykonanego przebiegu; ani jedna
  głębokość nie jest zgadnięta — liczba niepustych rzędnych w wyjściu równa się liczbie
  niepustych wierszy w CSV (**3**), sprawdzone testem; pochylenia na odcinkach ze
  rzędną mieszczą się w 0–4 % albo pozycja nazywa ten, który nie mieści, razem
  z liczbą; konflikt Schuman 15 m vs 17,42 m jest w wyjściu **oznaczony**, a nie
  rozstrzygnięty. Kontrola negatywna WYKONANA: interpolacja puszczona przez wiersz
  `unknown` wywraca dokładnie ten test, który liczy niepuste rzędne.
- **Poza zakresem:** **zapis czegokolwiek do `data/`** — wyjście idzie do `build/`,
  którego `CLAUDE.md` §4.8 zabrania commitować. Poza zakresem także wybór strony
  konfliktu Schuman (to nadal T-901, wiersz właściciela zostaje), zdjęcie z T-112
  statusu `flat-preview` dla wariantu `production` oraz jakakolwiek geometria
  w Blenderze — ta pozycja produkuje **dane**, nie siatkę.
- **Zależy od:** T-111 i #86 (oś i kilometraże), R-007 (trzy głębokości), decyzji
  właściciela z 07.09.2026. **Nie zależy** od T-901: cała jej treść to zbudowanie
  profilu, w którym brak danych z T-901 jest widoczny.

##### 6.A33 · Igła asercji, która pasuje do jedenastu różnych komunikatów

- **Skąd:** `reports/audyt-asercji.md` §7 nazwał ten pomiar **rozstrzygającym** i świadomie
  go nie wykonał: „czy igła asercji występuje w INNYM komunikacie tego samego programu".
  6.A32 zamknęło się bez bramki, bo przyrząd liczący *kształt* asercji łapał 0 z 4 znanych
  przypadków; wniosek tamtej pozycji brzmiał, że rozstrzyga **swoistość igły**, a to jest
  zdanie o kodzie produkcyjnym, nie o tekście testu. Zmierzone 07.09.2026 na `a4a3975`:
  **16 z 68** różnych igieł `StringAssert.Contains` w `tests/Sim.Tests/RunnerCommandTests.cs`
  mieści się w więcej niż jednym wielowyrazowym literale z `src/Sim.Runner/Program.cs`.

  | igła | ile komunikatów ją zawiera |
  |---|---|
  | `line` | **11** |
  | `budget` | 10 |
  | `--limit-kmh` | 9 |
  | `step` | 8 |
  | `[BUDŻET]`, `[LINIA]` | 6 |

- **Dlaczego to jest wykonalne, choć 6.A32 nie było:** rodzina komunikatów jest
  **zamknięta**. Literały odmów i wypisów `Program.cs` da się wyliczyć z jednego pliku
  (**209** wielowyrazowych na `a4a3975`), więc pytanie „ile komunikatów zawiera tę igłę"
  ma odpowiedź liczbową, a nie heurystykę. 6.A32 upadło na tym, że pytało o kształt
  asercji w całym zestawie, gdzie żadnej zamkniętej rodziny nie ma.
- **Wejście:** `src/Sim.Runner/Program.cs` (literały komunikatów),
  `tests/Sim.Tests/RunnerCommandTests.cs` (igły), `tools/tests/csharp_test_methods.py`
  (`maska`, `czlonkowie` — czytanie C# bez `dotnet`),
  `tools/tests/csharp_assertions.py`, `reports/audyt-asercji.md` §2, §3 i §7,
  `reports/asercja-rozstrzygajaca.md` §2 (6.A29: bramka trzymająca tabelę trzech igieł
  ręcznie i nazywająca to swoją ceną).
- **Wyjście:** bramka w `tools/tests/`, która dla każdej igły z testów runnera liczy,
  **ile** literałów `Program.cs` ją zawiera, i zgłasza igły pasujące do więcej niż
  jednego. Lista wyjątków **zamknięta zapadką z obu stron** — wzorzec 6.A31
  (`MAX_JUSTIFICATIONS`) — bo igła niejednoznaczna z dobrego powodu (np. asercja
  o nazwie polecenia, która ma pasować do wielu komunikatów) musi być wypisana z powodu,
  a nie przemilczana.
- **Weryfikacja:**
  ```bash
  python3 tools/tests/test_all.py
  dotnet test tests/Sim.Tests
  ```
  Oczekiwane: zestaw zielony kodem wyjścia, a nowa bramka wypisuje 16 zgłoszeń przy
  starcie i schodzi do zera dopiero po wpisaniu każdego z powodem albo po wzmocnieniu
  igły w teście.
- **Skończone, gdy:** dla każdej z 16 igieł jest **albo** wzmocniona asercja (igła
  pasująca do dokładnie jednego komunikatu), **albo** wpis na liście wyjątków z powodem
  podanym zdaniem; kontrola dodatnia WYKONANA — osłabienie jednej igły do `line` wywraca
  dokładnie nową bramkę; kontrola ujemna WYKONANA — igła jednoznaczna **nie** jest
  zgłaszana, a mutacja warunku `> 1` na `>= 1` przenosi zbiór zgłoszeń na wszystkie 68,
  czyli „nie zgłasza" jest rozróżnieniem, nie pustym zbiorem; kontrola przyrządu
  WYKONANA — dopisanie do `Program.cs` drugiego komunikatu z istniejącą igłą podnosi
  jej licznik, więc bramka czyta plik, a nie tabelę wpisaną z pamięci.
- **Poza zakresem:** **wzmacnianie igieł hurtem w `tests/Game.Tests`** — to jest 6.D34
  i ma osobną, też zamkniętą rodzinę komunikatów (`RunPlan`). Poza zakresem także
  zmiana treści któregokolwiek komunikatu `Program.cs`: pozycja mierzy swoistość igły,
  nie przepisuje komunikatów, a rozjazd naprawia się **w teście**, nie w programie.
- **Zależy od:** 6.A32 (pomiar, który tę pozycję nazwał), 6.A29 (wzorzec bramki
  z tabelą igieł), 6.B28 i 6.D30 (`csharp_test_methods`), 6.A31 (wzorzec zapadki
  na liście wyjątków).

##### 6.D32 · Pole bloku nazywa plik, którego w drzewie nie ma

- **Skąd:** dwie ścieżki znalezione 07.09.2026 niezależnie od siebie — jedną moim
  pomiarem, drugą przez agenta wykonującego 6.A30, który natrafił na nią, próbując
  wykonać pole „Weryfikacja" swojego własnego bloku. Zmierzone na `a4a3975` przez
  wszystkie 101 bloków:

  | pole | ścieżek | nieistniejących | z tego usterek |
  |---|---|---|---|
  | „Wejście" | **387** | 1 | **1** |
  | „Wyjście" | **40** | 2 | 0 |
  | „Weryfikacja" | **149** | 3 | **1** |

  Usterki są dwie: **6.B5** cytuje w „Wejściu" `tools/track/profile_scan.py`, a plik leży
  w `tools/blender/profile_scan.py`; **6.A30** cytuje w „Weryfikacji"
  `data/keys/L1_A-manual.json`, a katalogu `data/keys` nie ma w drzewie **wcale**.
- **Dlaczego to nie jest bramka „każda ścieżka musi istnieć":** cztery z sześciu
  nieistniejących ścieżek są **poprawne**, każda z innego powodu, i to one wyznaczają
  kształt bramki:
  - plik, który pozycja ma **wytworzyć** — `tools/track/vertical_profile.py` (6.B44),
    `tools/tests/test_test_track_fixture.py` (6.B8) w polu „Wyjście";
  - ten sam plik w komendzie, **która go tworzy** — 6.B44 w polu „Weryfikacja";
  - ścieżka **celowo nieistniejąca**, bo o nią w teście chodzi —
    `tools/nie-ma-takiego-pliku.py` (6.B39).

  Bramka bez tego rozróżnienia zgłasza cztery poprawne pozycje na dwie usterki i zostaje
  wyłączona w tym samym tygodniu (6.D27).
- **Wejście:** `docs/TASKS.md` (bloki `##### <numer> · …`), `tools/tests/test_backlog.py`
  (`detail_sections`, `REQUIRED_FIELDS` — to samo cięcie pól),
  `tools/tests/test_report_hygiene.py`
  (`test_kazda_sciezka_wymieniona_w_raporcie_rozwiazuje_sie_w_drzewie` — ta sama bramka
  dla `reports/`, wzorzec do naśladowania), `tools/tests/test_bin_path_framework.py`
  (6.A31: trzy szczeble i zapadka na liście wyjątków).
- **Wyjście:** bramka w `tools/tests/`, która dla pola „Wejście" żąda istnienia pliku
  **bez wyjątku możliwego do dopisania po cichu**, a dla „Wyjścia" i „Weryfikacji"
  przyjmuje nieistnienie tylko wtedy, gdy plik stoi w polu „Wyjście" tego samego bloku
  albo ma wpis na liście wyjątków z powodem. Plus poprawka dwóch ścieżek: 6.B5
  i 6.A30.
- **Weryfikacja:**
  ```bash
  python3 tools/tests/test_all.py
  python3 tools/tests/test_all.py test_backlog.py
  ```
  Oczekiwane: zestaw zielony kodem wyjścia, a bramka po poprawce dwóch ścieżek
  zgłasza **zero**.
- **Skończone, gdy:** liczba ścieżek jest podana per pole (dziś 387 / 40 / 149), obie
  usterki poprawione, a każdy z trzech rodzajów wyjątku ma **wypisany powód i test**;
  kontrola dodatnia WYKONANA — literówka wstawiona w pole „Wejście" dowolnego bloku
  wywraca dokładnie nową bramkę; kontrola ujemna WYKONANA — cztery poprawne ścieżki
  **nie** są zgłaszane, a zdjęcie rozróżnienia pól przenosi zbiór zgłoszeń z 2 na 6,
  czyli wyjątki mierzą coś, a nie milczą; kontrola wzorca WYKONANA — zepsucie wzorca
  ścieżki zapala próg na liczbie ścieżek, nie zostawia zielonego zera (wzorzec KW
  z 6.A31).
- **Poza zakresem:** sprawdzanie, czy komenda z pola „Weryfikacja" **działa** — to jest
  6.D33 i osobny pomiar. Poza zakresem także ścieżki w polach „Skąd" i „Zależy od":
  tam plik bywa cytowany jako historia („`reports/X.md` §3 podaje"), a nie jako wejście,
  i objęcie ich zmieniłoby bramkę w zakaz cytowania czegokolwiek usuniętego.
- **Zależy od:** 6.D3 (bramka higieny raportów), 6.A31 (wzorzec szczebli i zapadki),
  6.D6 (`test_backlog.py` i cięcie bloków). **Nie zależy** od 6.B5 ani 6.A30 — poprawia
  ich pola, nie wykonuje ich pracy.

##### 6.D33 · Audyt wykonalności komend objął 82 z 279 dzisiejszych komend

- **Skąd:** 6.D15 zebrało **82** komendy z **42** bloków i wydało werdykty (73
  uruchamialne). Zmierzone 07.09.2026 na `a4a3975`: bloków jest **101**, a wierszy
  komend w polach „Weryfikacja" — **279**. Audyt pokrywa więc **29 %** dzisiejszej
  liczby, i to nie przez zaniedbanie: 6.D15 nie zostawiło bramki, więc pokrycie
  **opada samo** z każdym dopisanym blokiem.
- **Co jest tu naprawdę nie tak:** liczba „73 uruchamialne" czytana dziś wygląda jak
  zdanie o kolejce, a jest zdaniem o czterdziestu dwóch blokach z sześćdziesięciu
  dwóch mniej. Ta sama rodzina, którą 6.D3 zamknęło dla raportów: pomiar bez zapisu,
  ilu rzeczy dotyczył, nie da się odtworzyć ani unieważnić.
- **Wejście:** `docs/TASKS.md` (pola „Weryfikacja" wszystkich bloków),
  `reports/komendy-weryfikacji.md` (metoda i werdykty 6.D15),
  `tools/tests/test_backlog.py` (`detail_sections`),
  `tools/tests/test_bin_path_framework.py` (6.A31 — cięcie pola „Weryfikacja" i podział
  na komendę kontra prozę, już zrobiony i przetestowany).
- **Wyjście:** **najpierw liczba, i ona rozstrzyga kierunek.** Do zmierzenia: ile
  z 279 komend jest dziś uruchamialnych w tym środowisku, ile wymaga Blendera, Godota
  albo `dotnet` (czyli jest niewykonalna nie z winy zapisu), a ile jest niewykonalna
  **z winy zapisu** — zła ścieżka, zła nazwa opcji, brakujący argument. Dopiero z tym
  rozbiciem wolno wybierać między bramką na liczbę pokrytych komend, adnotacją
  w raporcie 6.D15 i **niczym**.
- **Weryfikacja:**
  ```bash
  python3 tools/tests/test_all.py
  ```
  Oczekiwane: rozbicie 279 komend na cztery kategorie w raporcie, każda z liczbą,
  i zestaw zielony kodem wyjścia.
- **Skończone, gdy:** raport podaje **279** (albo liczbę zmierzoną tego dnia) w rozbiciu
  na uruchamialne, wymagające narzędzia nieobecnego, niewykonalne z winy zapisu
  i nierozstrzygnięte — a `reports/komendy-weryfikacji.md` dostaje **adnotację**
  mówiącą, ilu bloków dotyczył tamten pomiar. Jeżeli powstaje bramka, ma kontrolę
  dodatnią i ujemną WYKONANE; jeżeli pomiar pokaże, że bramki nie warto — raport mówi
  to wprost i pozycja kończy się na adnotacji, **co też jest poprawnym wynikiem**
  (wzorzec 6.A32).
- **Poza zakresem:** **przeliczanie werdyktów 6.D15**. Tamten audyt jest pomiarem
  z datą i dostaje adnotację, nie poprawkę (`docs/04-conventions.md`). Poza zakresem
  także poprawianie komend niewykonalnych z winy zapisu — pozycja je **liczy i nazywa**,
  a poprawka każdej należy do jej własnego bloku.
- **Zależy od:** 6.D15 (audyt, którego pokrycie ta pozycja mierzy), 6.A31 (cięcie pola
  „Weryfikacja"), 6.D3 (zasada: pomiar mówi, na czym powstał).

##### 6.D34 · `tests/Game.Tests` nie było objęte audytem asercji, i raport mówi to wprost

- **Skąd:** `reports/audyt-asercji.md` §7 kończy się zdaniem, którego nie da się czytać
  inaczej: „o tamtych 53 asercjach ten raport nie mówi nic — i nie udaje, że mówi".
  Cztery przypadki asercji nierozstrzygającej z 07.09.2026 były wszystkie z runnera
  i z `tools/tests/`, więc wniosek 6.A32 („przyrząd łapie 0 z 4") jest **zdaniem o tamtej
  czwórce**, nie o `Game.Tests`. Zmierzone 07.09.2026 na `a4a3975` wzorcem
  `StringAssert.Contains` / `Assert.IsTrue(… .Contains(…))` na masce:

  ```
    20  tests/Game.Tests/RunPlanTests.cs
    19  tests/Game.Tests/TelemetryTrackTests.cs
     7  tests/Game.Tests/SignallingHudTests.cs
  razem Game.Tests: 63 w 7 plikach
  ```

- **Dlaczego to jest wykonalne:** tak samo jak 6.A33 i z tego samego powodu — rodzina
  komunikatów jest **zamknięta**. `RunPlan.Mode` zwraca sześć literałów, a 6.C5 już to
  policzyło i przybiło bramką `tools/tests/test_run_mode_claims.py`; odmowy łączenia
  źródeł ruchu to sześć par wymienionych z nazwy (6.C3). Pytanie „ile komunikatów
  `RunPlan` zawiera tę igłę" ma więc odpowiedź liczbową.
- **Wejście:** `src/Game/RunPlan.cs` (literały odmów i nazwy trybów),
  `src/Game/TelemetryTrack.cs`, `src/Game/SignallingHud.cs`,
  `tests/Game.Tests/RunPlanTests.cs`, `TelemetryTrackTests.cs`, `SignallingHudTests.cs`,
  `tools/tests/csharp_test_methods.py`, `tools/tests/test_run_mode_claims.py` (6.C5),
  `reports/audyt-asercji.md` §7, `reports/liczba-trybow-run-plan.md`.
- **Wyjście:** liczba niejednoznacznych igieł dla `Game.Tests`, policzona tą samą
  metodą co 6.A33, i wzmocnienie tych igieł albo wpis z powodem. Jeżeli pomiar pokaże,
  że w tej rodzinie niejednoznacznych jest zero — raport mówi to wprost i pozycja kończy
  się bez zmiany w testach, **co jest poprawnym wynikiem**, nie porażką.
- **Weryfikacja:**
  ```bash
  python3 tools/tests/test_all.py
  dotnet test tests/Game.Tests
  ```
  Oczekiwane: liczba podana, zestaw zielony kodem wyjścia, `Game.Tests` zielone.
- **Skończone, gdy:** dla `tests/Game.Tests` podana jest liczba igieł pasujących do
  więcej niż jednego komunikatu `src/Game/`, imiennie; każda ma wzmocnioną asercję albo
  wpis z powodem; kontrola dodatnia WYKONANA na jednej z nich (osłabienie do igły
  pasującej do wielu) i kontrola ujemna WYKONANA (igła jednoznaczna nie jest zgłaszana).
  Zdanie z §7 raportu 6.A32 przestaje być prawdą i **dostaje adnotację**, a nie
  poprawkę — tamten raport ma datę.
- **Poza zakresem:** `tests/Sim.Tests` — to jest 6.A33. Poza zakresem także uruchamianie
  czegokolwiek w Godocie: `Game.Tests` chodzi bez silnika i cała ta pozycja jest
  tekstowa. Poza zakresem wreszcie zmiana treści komunikatów `RunPlan` — rozjazd
  naprawia się w teście.
- **Zależy od:** 6.A32 (pomiar, który wyłączył `Game.Tests` z zakresu i to zapisał),
  6.C5 (zamknięta rodzina trybów), 6.A33 (metoda liczenia swoistości igły —
  ta pozycja stosuje ją do drugiej rodziny, nie wymyśla drugiej metody).

##### 6.D35 · Raport w `main` nazywa plik z `Sim.Tests` testem Godota

- **Skąd:** `reports/audyt-asercji.md` §7, scalony do `main` w #375, pisze: „Trzy
  najliczniejsze pliki C# to testy Godota, nie runnera (`RunPlanTests.cs` 20,
  `TelemetryTrackTests.cs` 19, `InputLogTests.cs` 14 gołych asercji na obecność)".
  Sprawdzone 07.09.2026 na `a4a3975`:

  ```
  $ ls tests/*/InputLogTests.cs
  tests/Sim.Tests/InputLogTests.cs
  $ grep -n "namespace" tests/Sim.Tests/InputLogTests.cs
  7:namespace MetroBxl.Sim.Tests;
  $ grep -c Godot tests/Sim.Tests/*.csproj
  0
  ```

  **Trzeci wiersz sprostowany 07.09.2026 (przy 6.D32).** Stała tu komenda
  `grep -c Godot tests/Sim.Tests/MetroBxl.Sim.Tests.csproj` z odpowiedzią `0`,
  przedstawiona jako wykonana — a pliku o tej nazwie nie ma, więc `grep` skończyłby
  się `No such file or directory` i kodem 2. Plik nazywa się `Sim.Tests.csproj`;
  `MetroBxl.Sim.Tests` jest wartością `<AssemblyName>` **w tym właśnie pliku**.
  Wykonana była postać z globem, i to ona stoi wyżej. Wniosek — zero odwołań do
  Godota — jest niezmieniony i sprawdzony ponownie; nieprawdziwy był **zapis
  komendy**, i to jest różnica warta odnotowania, bo cytat komendy czyta się jak
  dowód, a nie jak parafrazę.

  `InputLogTests.cs` nie jest testem Godota ani przez katalog, ani przez przestrzeń
  nazw, ani przez odwołanie w pliku projektu. Zdanie jest przy tym **własnym argumentem
  raportu** za tym, że audyt minął `Game.Tests` — a jeden z trzech plików, na których
  ten argument stoi, do `Game.Tests` nie należy.
- **Dlaczego to nie jest literówka bez konsekwencji:** `CLAUDE.md` §9 i cała rodzina
  6.D3 / 6.D4 / 6.D8 stoją na jednym: zdanie w raporcie, którego nikt nie liczy,
  czyta się identycznie jak wynik pomiaru. Tutaj czytający wyciągnąłby wniosek
  o rozkładzie usterki między dwa projekty testowe, a rozkład jest inny.
- **Wejście:** `reports/audyt-asercji.md` §7, `tests/Sim.Tests/InputLogTests.cs`,
  `tests/Sim.Tests/Sim.Tests.csproj`, `tests/Game.Tests/` (co tam faktycznie
  leży), `tools/tests/test_report_claims.py` (6.D4 — bramka na twierdzenia raportów).
- **Wyjście:** zdanie w §7 **przepisane, a nie dopisane obok**, z liczbą policzoną
  ponownie i z podziałem na projekty testowe podanym wprost. Do rozstrzygnięcia
  pomiarem, czy `test_report_claims.py` da się rozszerzyć o twierdzenia postaci
  „plik X należy do projektu Y" — jeżeli tak, to wchodzi razem z poprawką; jeżeli nie,
  raport dostaje adnotację i pozycja kończy się na niej.
- **Weryfikacja:**
  ```bash
  python3 tools/tests/test_all.py test_report_claims.py
  python3 tools/tests/test_all.py
  ```
  Oczekiwane: zestaw zielony kodem wyjścia; `grep` na frazę „testy Godota" w
  `reports/audyt-asercji.md` nie zwraca zdania wymieniającego `InputLogTests.cs`.
- **Skończone, gdy:** zdanie §7 jest zgodne z drzewem, a rozkład gołych asercji między
  `Sim.Tests` i `Game.Tests` podany osobno, z liczbami; jeżeli powstaje bramka, ma
  kontrolę dodatnią WYKONANĄ (przywrócone stare zdanie ją wywraca) — a jeżeli nie,
  raport nazywa wprost, dlaczego tego twierdzenia nie da się policzyć mechanicznie.
- **Poza zakresem:** **przeliczanie liczb 255 / 127 / 382** z §2 tamtego raportu —
  są pomiarem z datą i nie ta pozycja je rusza. Poza zakresem także audyt samych
  asercji `Game.Tests`; to jest 6.D34.
- **Zależy od:** 6.A32 (scalone w #375 — raport, którego zdanie poprawia), 6.D4 (bramka
  na twierdzenia raportów), 6.D3 (nagłówek z datą i commitem).

##### 6.B45 · Docstring podaje 9 z 44, a zmierzone jest 10 z 63

- **Skąd:** znalazł to agent wykonujący 6.B41 i świadomie nie tknął, bo to nie był
  jego plik ani jego pozycja. Zmierzone 07.09.2026 na `627d184`:

  ```
  celow: 63   nieosiagalnych: 10
     tools/blender/detail_markers.py … tools/blender/tunnel_sweep.py   (dziewięć)
     tools/visual/capture_blender.py                                   (dziesiąty)
  ```

  Docstring `test_every_real_target_except_the_blender_entry_points_is_reachable`
  mówi „9 z 44 modułów", czyli **obie liczby są nieprawdziwe**.
- **Co jest, a co nie jest przybite — i to rozstrzyga kształt poprawki:** asercja
  jakościowa **jest** pilnowana pętlą `assert "bpy" in reason` i pozostaje prawdziwa
  (dziesiąty moduł też importuje `bpy`). Asercja liczbowa to **próg**:
  `len(unreachable) < len(targets()) // 2`, czyli 10 < 31 — przechodzi przy 9, przy 10
  i przy 30. Liczby w docstringu nie są więc pilnowane przez nic.
- **Dlaczego nie wolno ich po prostu przepisać na 10 i 63:** przybicie dokładnej liczby
  zapaliłoby bramkę przy każdym dodanym albo usuniętym module z `bpy` — czyli przy
  pracy, która jest normalna. Repozytorium ma na to wzorzec: **liczbę się WYPROWADZA,
  nie wpisuje** (6.D26 wyprowadza maksimum z listy pomiarów, 6.A31 wyprowadza ramkę
  z pliku projektu). Tu wyprowadzeniem jest sama lista celów.
- **Wejście:** `tools/tests/test_mutation_sweep.py`
  (`test_every_real_target_except_the_blender_entry_points_is_reachable`, wiersze
  762–775), `tools/tests/mutation_sweep.py` (`unreachable_modules`, `targets`),
  `reports/pusty-zbior-przegladu.md` §„Zauważone" (skąd znalezisko),
  `tools/tests/test_suite_runtime_budget.py` (6.D26 — wzorzec wyprowadzania liczby).
- **Wyjście:** docstring podający liczby **jako datowany pomiar** albo asercja
  wyprowadzająca je z drzewa — **do rozstrzygnięcia pomiarem, które z dwojga**:
  do zmierzenia, ile modułów z `bpy` doszło i odeszło w `tools/` od 04.09.2026, bo od
  tej liczby zależy, czy asercja na dokładną wartość byłaby bramką, czy udręką.
- **Weryfikacja:**
  ```bash
  python3 tools/tests/test_all.py test_mutation_sweep.py
  ```
  Oczekiwane: moduł zielony, a docstring i asercja mówią tę samą liczbę co drzewo.
- **Skończone, gdy:** żadna liczba w tym docstringu nie jest nieprawdziwa, a jeżeli
  którakolwiek zostaje wpisana ręcznie, to **jako pomiar z datą**; kontrola negatywna
  WYKONANA — dołożenie jedenastego modułu bez `bpy`, który się nie importuje, wywraca
  dokładnie tę asercję, a dołożenie jedenastego Z `bpy` **nie** wywraca niczego.
- **Poza zakresem:** zmiana progu `< len(targets()) // 2` na dokładną równość bez
  pomiaru z pola „Wyjście". Poza zakresem także samo `unreachable_modules` — pozycja
  dotyczy zdania o nim, nie jego zachowania.
- **Zależy od:** 6.B41 (tam znalezione), 6.D26 (wzorzec wyprowadzania liczby).

##### 6.B46 · `collect()` bez zawężenia: świeże przeliczenie kosztuje wszystkie 63 cele

- **Skąd:** zmierzone 07.09.2026 przy 6.B38 i nazwane tam wprost jako osobna pozycja
  z własnym pomiarem. `collect(kinds)` przechodzi **zawsze** po całej liście celów;
  zawężenie `--only` działa dopiero **po** nim, w `main`. Skutek jest dwustronny:
  - test, który potrzebuje świeżego przeliczenia dla **jednego** modułu, płaci
    **0,224 s** za komplet 63;
  - pamięć z 6.B38 kluczuje po odciskach **wszystkich** celów, więc zmiana treści
    **jednego** pliku unieważnia klucz i wymusza pełne przeliczenie. Jest to poprawne
    — inaczej podstawiałaby cudzą treść — ale drożej, niż wymaga poprawność.
- **Dlaczego to nie jest przedwczesna optymalizacja:** kontrole negatywne tego modułu
  zmieniają pliki celów w trakcie procesu (6.B32, 6.B39, 6.B40, 6.B38), a każda taka
  zmiana to dziś pełne przeliczenie. Zmierzone przy 6.B38: `collect()` był wołany
  **dziesięć razy** w jednym module i to była największa dająca się usunąć pozycja
  jego czasu.
- **Wejście:** `tools/tests/mutation_sweep.py` (`collect`, `_PAMIEC_COLLECT`,
  `targets`, `mutations_for`), `tools/tests/test_mutation_sweep.py` (rodzina
  `test_pamiec_collect_*`), `reports/czas-modulu-mutacyjnego.md` §2 i §10
  (pomiar per test i nazwanie tej pozycji).
- **Wyjście:** **najpierw pomiar, potem kierunek.** Do zmierzenia: ile z dzisiejszych
  wywołań `collect()` w zestawie potrzebuje **wszystkich** celów, a ile jednego albo
  kilku; oraz ile kosztowałoby klucz pamięci **per plik** zamiast per przebieg
  (odcisk jednego pliku to dziś 0,00002 s, komplet 63 — 0,0013 s). Dopiero z tymi
  liczbami wolno wybierać między parametrem zawężenia w `collect()`, pamięcią
  per plik i zostawieniem tego, co jest.
- **Weryfikacja:**
  ```bash
  python3 tools/tests/test_all.py test_mutation_sweep.py
  python3 tools/tests/test_all.py
  ```
  Oczekiwane: czas modułu podany przed i po, z co najmniej trzech przebiegów, przy
  **niezmienionej** liczbie testów i niezmienionych werdyktach.
- **Skończone, gdy:** raport podaje, ile wywołań potrzebuje kompletu, a ile nie, oraz
  czas modułu przed i po; jeżeli powstaje zawężenie, **kontrola negatywna WYKONANA**:
  `collect` z zawężeniem na jeden plik nie może zwrócić mutacji z innego, a pamięć
  per plik musi unieważniać się przy zmianie **tego** pliku i **nie** przy zmianie
  cudzego — obie strony pokazane wykonaniem. Jeżeli pomiar pokaże, że oszczędność
  jest w szumie, pozycja kończy się bez zmiany w kodzie i raport mówi to wprost.
- **Poza zakresem:** zdejmowanie albo łączenie testów (to samo, co w 6.B38) oraz
  ruszanie `ast.parse` w `test_every_mutation_still_parses` — 6,44 s tamtego testu jest
  pracą, nie marnotrawstwem, i 6.B38 nazwało to pomiarem.
- **Zależy od:** 6.B38, 6.B32.

##### 6.D36 · Jedno obcięcie odcisku przez literał, dwa przez stałą

- **Skąd:** zmierzone 07.09.2026 na `627d184`, przejściem po wszystkich `.py` i `.cs`
  w drzewie:

  ```
  obcięć hexdigest RAZEM: 3
    przez STALA:  tools/tests/mutation_sweep.py:444  [:ODCISK_ZNAKOW]
                  tools/tests/mutation_sweep.py:943  [:ODCISK_ZNAKOW]
    przez LITERAL: tools/tests/mutation_sweep.py:990  [:12]
  ```

  Wszystkie trzy w jednym pliku. `ODCISK_ZNAKOW` mówi **16** i ma przy sobie akapit
  wyjaśniający, skąd ta liczba (64 bity, kolizja rzędu 10⁻¹⁴ przy 2346 mutacjach);
  znacznik nazwy dziennika obcina do **12** i nie ma przy sobie nic.
- **Dlaczego to pozycja, a nie kosmetyka:** `tools/tests/test_dead_constants.py` (6.B29)
  pilnuje stałej, **której nikt nie czyta**. Nic nie pilnuje odwrotności — **literału,
  który powinien być stałą** — a to ten sam rodzaj cichego rozjazdu: dwie długości tej
  samej wielkości, żadna liczona z drugiej, i żadna nie wie o istnieniu tamtej.
  Dziś bez skutku, bo znacznik jest skrótem z konkatenacji, a nie z odcisku.
- **Wejście:** `tools/tests/mutation_sweep.py` (`ODCISK_ZNAKOW`, `odcisk_tresci`,
  `odcisk_przebiegu`, `default_journal`), `tools/tests/test_dead_constants.py`
  (6.B29 — wzorzec bramki na stałe), `reports/sciezka-dziennika-z-odciskiem.md` §9
  (tam zauważone), `reports/odcisk-tresci-dziennika.md` (skąd 16).
- **Wyjście:** **do rozstrzygnięcia pomiarem, czy w ogóle warto**: albo nazwana stała
  dla długości znacznika z własnym uzasadnieniem (12 znaków to 48 bitów — do policzenia,
  czy przy dzisiejszej liczbie przebiegów kolizja nazw jest zaniedbywalna), albo
  bramka na literały obcinające `hexdigest()`. Przy **trzech** wystąpieniach w całym
  drzewie bramka może być droższa od problemu i raport ma to powiedzieć liczbą.
- **Weryfikacja:**
  ```bash
  python3 tools/tests/test_all.py test_dead_constants.py
  python3 tools/tests/test_all.py test_mutation_sweep.py
  ```
  Oczekiwane: zestaw zielony, a jeżeli powstaje stała — czytana z co najmniej jednego
  miejsca, więc 6.B29 jej nie zgłasza.
- **Skończone, gdy:** długość znacznika nazwy dziennika ma **uzasadnienie liczbą**
  (ile bitów, jaka szansa kolizji przy dzisiejszej liczbie przebiegów), a jeżeli
  powstaje bramka — kontrola negatywna WYKONANA: literał wstawiony w miejsce stałej
  ją wywraca. **Zmiana samej długości z 12 na 16 przenazwałaby wszystkie dzienniki
  i jest osobną decyzją**; ta pozycja jej nie podejmuje bez pomiaru.
- **Poza zakresem:** zmiana `ODCISK_ZNAKOW` (ma uzasadnienie i pomiar) oraz
  przenazwanie istniejących dzienników w `/tmp`.
- **Zależy od:** 6.B29, 6.B40.

##### 6.D37 · `--only ""` przechodzi drogą bez zawężenia i nic tego nie mówi

- **Skąd:** zmierzone 07.09.2026 na `627d184`. Pusty napis jest fałszywy dla
  `if args.only`, więc gałąź zawężenia nie wchodzi wcale — ani filtr, ani wypis
  „dopasowało N plików", ani odmowa z 6.B39. Skutek jest liczbowy:

  ```
  mutacji bez zawezenia:        2346
  mutacji dla lod_paths.py:        2
  stosunek:                     1173×
  ```

  Skrypt wołający `--only "$WZORZEC"` z pustą zmienną dostaje więc **pełny przegląd**
  zamiast odmowy, i wypis nie zawiera ani jednego słowa o tym, że zawężenia nie było.
- **Dlaczego to ta sama rodzina co 6.B39, tylko odwrócona:** tam zbiór był **pusty**,
  a przebieg wychodził zerem, wyglądając na poprawny. Tu zbiór jest **pełny**, a
  przebieg wygląda na zawężony, bo wołający go o to prosił. W obu przypadkach
  przebieg robi co innego, niż czytający sądzi, i w obu milczy.
- **Wejście:** `tools/tests/mutation_sweep.py` (`main`, gałęzie `if args.only`,
  `przyczyna_pustego_zbioru`), `tools/tests/test_mutation_sweep.py` (rodzina
  `test_only_*`), `reports/pusty-zbior-listy.md` §9 (tam zauważone),
  `.github/workflows/python-tests.yml` (jedyne miejsce, gdzie napis `mutation_sweep`
  stoi w workflow — komentarz, nie wywołanie).
- **Wyjście:** **do rozstrzygnięcia pomiarem, czy odmowa, czy zdanie w wypisie.**
  Do zmierzenia: czy istnieje w drzewie albo w `reports/` choć jedno wywołanie, które
  podaje `--only` z wartością mogącą być pusta (podstawienie zmiennej). Jeżeli tak —
  odmowa; jeżeli nie — wystarczy jeden wiersz wypisu nazywający brak zawężenia,
  bo odmowa dla wołania podanego wprost byłaby uciążliwością bez zmierzonego powodu.
- **Weryfikacja:**
  ```bash
  python3 tools/tests/mutation_sweep.py --only "" --list
  python3 tools/tests/test_all.py test_mutation_sweep.py
  ```
  Oczekiwane: pierwsza komenda **nie milczy** o braku zawężenia; druga zielona, bo
  przebieg bez `--only` wcale ma zostać niezmieniony.
- **Skończone, gdy:** `--only ""` jest odróżnialne od przebiegu bez `--only` w wypisie
  albo w kodzie wyjścia — pokazane WYKONANIEM obu — a kontrola negatywna WYKONANA:
  przebieg **bez** `--only` nadal nie mówi nic o zawężeniu i nadal kończy się kodem 0.
- **Poza zakresem:** odmowa dla przebiegu bez `--only` (to jest normalne wołanie
  i 6.B39 zostawiło je poza zakresem z tego samego powodu) oraz zmiana dopasowania
  podciągiem (6.D18).
- **Zależy od:** 6.B39, 6.D18.

##### 6.D38 · Nagłówek raportu przeglądu ma inny kształt niż wzór z 6.D3

- **Skąd:** zauważone 07.09.2026 przy 6.B42. `reports/mutation-sweep.md` niesie
  `**Snapshot na commicie:** \`66b8301\` (\`main\`, 04.09.2026)` — commit, nazwę gałęzi
  i datę w **jednym** wierszu, gdy wzór 6.D3 rozdziela datę i commit. Bramka higieny
  to przepuszcza, bo szuka SHA w grawisach i daty osobno, a oba tu są.
- **Dlaczego to nie jest brak informacji:** wszystko potrzebne w tym nagłówku **jest**.
  Rozjazd dotyczy **kształtu**, a kształt ma znaczenie tylko wtedy, gdy ktoś na nim
  stoi — i to jest pytanie do pomiaru, nie do gustu.
- **Wejście:** `tools/tests/test_report_hygiene.py` (`COMMIT`, `DATE`, wzorce
  nagłówka i ich uzasadnienia), wszystkie `reports/*.md`, `docs/04-conventions.md`
  (zapis o nagłówku), `reports/odcisk-w-naglowku-raportu.md` §8 (tam zauważone).
- **Wyjście:** **najpierw pomiar.** Do zmierzenia: ile z dzisiejszych raportów ma
  nagłówek w kształcie `**Zmierzone <data> na commicie:** \`<sha>\``, ile w innym,
  i ile kształtów jest w sumie. Dopiero z tą liczbą wolno wybierać między
  ujednoliceniem, bramką na kształt i **niczym**. Jeżeli kształtów jest kilka i każdy
  czytelny, pozycja kończy się adnotacją w `docs/04-conventions.md` mówiącą, że wzór
  jest zaleceniem, nie wymogiem — **co też jest poprawnym wynikiem**.
- **Weryfikacja:**
  ```bash
  python3 tools/tests/test_all.py test_report_hygiene.py
  python3 tools/tests/test_all.py
  ```
  Oczekiwane: rozbicie kształtów nagłówka z liczbami w raporcie i zestaw zielony.
- **Skończone, gdy:** liczba raportów w każdym kształcie jest podana, a wybór kierunku
  uzasadniony tą liczbą, nie przekonaniem; jeżeli powstaje bramka na kształt, ma
  kontrolę dodatnią i ujemną WYKONANE, w tym kontrolę na nagłówku **poprawnym**, bo
  bramka zapalająca się na dobrym tekście zostaje wyłączona (6.D27).
- **Poza zakresem:** **przepisywanie nagłówków datowanych pomiarów** — data i commit
  zostają takie, jakie były w dniu pomiaru (`docs/04-conventions.md`), zmienić może się
  najwyżej ich układ. Poza zakresem także dopisywanie odcisków treści do starych
  raportów (6.B42 dało im adnotację i to zostaje).
- **Zależy od:** 6.D3, 6.B42.

##### 6.D41 · Bramka porównywała z progiem pomiar, który sama nazwała niestabilnym

- **Skąd:** zmierzone 07.09.2026 na runnerze `woogitsu-host-08`, gdy dwanaście jobów
  liczyło naraz. Job `sim` padł na `tools/ci/assert_linecore_budget.py`:

  ```
  BLAD: koszt kroku 16.022 us przekracza prog 8.000 us
  [BUDZET-BRAMKA] ... 16.022 us/krok przy progu 8.000; rozstep powtorzen 115.9 %
  ```

  Na **tej samej treści kodu**, na maszynie niezajętej, cztery przebiegi dały
  **4,213–4,364 µs przy rozstępie 1,9–3,7 %**, kod 0. Rdzeń nie zwolnił czterokrotnie
  — maszyna nie dała się zmierzyć.
- **Co było mierzalnie nie tak:** kolumna `rozstęp_%` była **parsowana i wypisywana,
  ale nigdy nie asertowana** (`spread_pct` czytany w `parse`, użyty tylko w `describe`).
  Bramka znała liczbę mówiącą, że jej własny pomiar jest niestabilny, i porównywała go
  z progiem mimo to — a potem nazywała wynik regresem wydajności. „Rdzeń zwolnił"
  i „nie umiem tego zmierzyć" dawały **jeden komunikat i jeden kod wyjścia**, choć
  pierwsze każe szukać regresu w kodzie, a drugie powtórzyć pomiar.
- **Wejście:** `tools/ci/assert_linecore_budget.py` (`parse`, `verdict`, `describe`,
  `main`), `tools/ci/linecore-step-budget.json` (próg i scenariusz w jednym miejscu),
  `tools/tests/test_linecore_budget_gate.py`, `reports/linecore-step-budget-gate.md`
  (podstawa progu 8,0 µs i rozstępy z kalibracji), `reports/linecore-budget.md`.
- **Wyjście:** granica rozstępu, która **wstrzymuje porównanie** z progiem czasu,
  z osobnym kodem wyjścia, i granica **wyprowadzona z pomiarów**, nie wpisana z ręki.
  Warunki obsady zostają sprawdzane zawsze — liczba składów na planie nie zależy od
  obciążenia maszyny.
- **Weryfikacja:**
  ```bash
  python3 tools/tests/test_all.py test_linecore_budget_gate.py
  python3 tools/ci/assert_linecore_budget.py
  ```
  Oczekiwane: moduł zielony, bramka na prawdziwym pomiarze kodem 0, a kontrole
  negatywne pokazują, że zdjęcie strażnika wraca do porównywania niestabilnego pomiaru.
- **Skończone, gdy:** pomiar z rozstępem powyżej granicy **nie jest** porównywany
  z progiem, dwa werdykty mają **dwa różne kody wyjścia**, a granica ma przy sobie
  wszystkie pomiary, z których wyszła — łącznie z tymi, które ją ograniczają od dołu.
- **Poza zakresem:** **próg 8,0 µs**. Ma udokumentowaną podstawę z 06.09.2026 i ta
  pozycja go nie tyka; podniesienie progu byłoby osłabieniem bramki, a nie naprawą
  pomiaru. Poza zakresem także **automatyczne powtarzanie pomiaru** przy niestabilnym
  wyniku: to osobna decyzja, wymagająca pomiaru, jak często powtórzenie pomaga.
- **Zależy od:** 6.D2 (bramka i jej próg), 6.A12 (warunek obsady).

### Czego agent nie ruszy bez decyzji

Poniższe **nie są kolejką** — są listą rzeczy, które czekają na właściciela. Agent po nie
nie sięga, nawet gdy nie ma nic innego do roboty; wtedy sięga po fazę 5.

| | dlaczego |
|---|---|
| **T-901** głębokości stacji | 9 z 12 stacji pakietu A `unknown`; Schuman ma konflikt 15 m vs 17,42 m, i **wyboru strony konfliktu ta lista nie zdejmuje**. **Wiersz przepisany 07.09.2026, a nie dopisany obok:** poprzednia wersja kończyła się słowami „Blokuje T-112, a przez to scenę z dwoma pakietami", i to już nieprawda. Decyzja właściciela z 07.09.2026 (budować z jawnym `unknown`) odblokowała T-112 dla wariantu z nazwaną dziurą — wykonuje to 6.B44 — a `production` blokuje nadal, bo do niego trzeba rozstrzygnąć konflikt. Blokada zeszła więc z „profilu" na „profil produkcyjny", i to jest cała różnica |
| **T-902** kierunek artystyczny | ocena estetyczna (`CLAUDE.md` §8) |
| **T-903** kontakt ze STIB | `docs/03-legal.md` |
| **T-905** nagrania | praca w terenie |
| **4034 m dziur** między pakietami | kilometraż nie jest ciągły; przejazd całą linią wymaga decyzji o zakresie |
| pakiety **C, D, F** bez tuneli | decyzja, co budować zamiast rury |
| **6.A4** propagacja opóźnienia | przeniesione z kolejki 05.09.2026. Wpis T-320 ma sekcję STOP: „model perturbacji i polityka dyspozytora **nie są opisane w żadnym dokumencie**. Agent zatrzymuje się i pyta, zamiast wybierać sam”. Wiersz kolejki bronił się liczbą — „rozkład postojów jest zmierzony, 29 554 zatrzymań, 12–45 s” — ale zmierzony jest **rozkład postojów**, nie wielkość zaburzenia. Skąd wzięło się 30 s, nie mówi żadne źródło, a to jest właśnie model perturbacji |
| **6.B3** LOD tuneli pakietów B–F | przeniesione z kolejki 05.09.2026, po tym jak audyt (`reports/kolejka-audyt-aktualnosci.md` §1) pokazał, że pozycja opisuje trzy różne stany naraz. **B i E mają LOD od T-210** — wpis T-210 podaje „szczelina między chunkami, poziomami LOD i w bryle kolizyjnej 0,0000 mm w każdym pakiecie”. **C, D i F czekają na wiersz wyżej**, czyli na decyzję, co budować zamiast rury: `reports/surface-vs-tunnel.md` §1 podaje, że wszystkie 81 punktów sprzecznych między UrbIS a OSM leży w D (48) i F (33). Zostaje więc zero pracy, której nie blokuje tamta decyzja |
| **turnback, perturbacje, dispatcher** w T-320 | nie ma ich w żadnym dokumencie |

#### Rozstrzygnięte 07.09.2026 — cztery decyzje właściciela

Cztery pozycje przedstawione właścicielowi w formie klikalnej 07.09.2026 dostały
odpowiedzi. Zapis jest **tutaj, w drzewie**, a nie tylko w rozmowie, i to nie jest
formalność: kopia decyzji żyjąca w czacie starzeje się osobno od repozytorium, a ta
sesja trzy razy tego dnia zobaczyła, co z tego wynika (6.A22, 6.A26, 6.B32 — za każdym
razem liczba albo reguła stała w jednym miejscu i nigdzie nie była pilnowana).

Trzy z czterech decyzji **odblokowują pracę** i mają w fazie 6 pozycję z kompletem
sześciu pól: 6.A19, 6.B43 i 6.B44. Czwarta nie odblokowuje niczego, bo dotyczy pulsu
sesji, a nie repozytorium — i to też jest wynik, nie luka.

| decyzja | odpowiedź właściciela | co z tego wynika |
|---|---|---|
| **6.A19** — wybieg w `replay` | **odczytanie (a): odmowa zostaje**, i to na stałe, jako udokumentowana **własność** polecenia | pozycja **6.A19** w fazie 6: odmowa dostaje treść mówiącą POWÓD, a nie zdanie „nie zna opcji" o opcji, którą projekt ma. Wariantów (b) „wybieg nadpisuje zapis pod inną nazwą" i (c) „`replay` uczy się drugiego trybu" nie realizuje nic i nie wolno ich wprowadzać skutkiem ubocznym |
| **pasmo 94..106 m** kamery goniącej | **rozciągnąć ukrycie do 110 m** | pozycja **6.B43** w fazie 6. Granica przestaje być tożsama z długością składu i to jest istotne: `Availability` pyta dziś o kilometraż i długość składu **i o nic więcej**, a po zmianie musi znać jeszcze jeden próg — próg jasności kadru, który z długością M7 nie ma nic wspólnego |
| **T-901** głębokości stacji | **budować z jawnym `unknown`** — trzy znane głębokości wchodzą do profilu, dziewięć pozostałych zostaje nazwane niewiadomą, a nie zinterpolowane | pozycja **6.B44** w fazie 6 i zmiana statusu **T-112** wyżej w tym pliku. Konflikt Schuman 15 m vs 17,42 m zostaje **nierozstrzygnięty** i tak oznaczony; decyzja mówi „buduj z dziurą widoczną", a nie „wybierz jedną ze stron" |
| **puls sesji** co godzinę | **zostawić godzinę** | zero pracy w repozytorium poza jednym: `docs/22-heartbeat.md` §5 przepisane, bo mówiło o stanie z 01.09.2026. Decyzja nazywa też przyczynę, dla której pytanie w ogóle padło — usterka była w **zachowaniu agenta** (punktem zatrzymania było „PR otwarty" zamiast „PR scalony"), nie w kadencji pobudki. Zagęszczenie pulsu tej usterki by nie tknęło |

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
