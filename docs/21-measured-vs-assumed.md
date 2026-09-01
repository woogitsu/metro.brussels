# Co jest zmierzone, a co założone

Audyt **każdego** wymiaru, na którym opiera się geometria projektu. Powstał, bo liczb
zaczęło być tyle, że przestało być widać, które z nich są faktem o brukselskim metrze,
a które decyzją projektową — a to jest różnica, na której stoi reguła 1 z `CLAUDE.md`.

Statusy używane w repo:

| status | znaczenie |
|---|---|
| **`spec`** | wartość z oficjalnego źródła, zapisana w rejestrze i sprawdzalna |
| **`observed`** | wartość zmierzona z oficjalnych danych geometrycznych, ale nie opublikowana jako wymiar |
| **`design_assumption`** | decyzja projektowa. **Nie jest faktem o sieci** i nie wolno jej tak przedstawiać |
| **`blocked`** | wymiar potrzebny, ale niemożliwy do ustalenia z dostępnych źródeł |

Pilnuje tego `tools/tests/test_dimension_audit.py`: każda stała `DESIGN_*`, każdy klucz
specyfikacji M7, każdy profil tunelu i każda stała geometryczna musi mieć w tym pliku
wpis. Dopisanie parametru bez wpisu wywraca testy.

## 1. Tabor M7

### 1.1 Ze specyfikacji (`data/vehicle/m7-spec.json`)

Źródło: `stib_m7_2020_07_13`, komunikat STIB o dostawie M7.

| wymiar | wartość | status |
|---|---|---|
| długość składu | 94,0 m | `spec` |
| szerokość pudła | 2,70 m | `spec` |
| wysokość podłogi nad główką szyny | 1,03 m | `spec` |
| liczba członów | 6 | `spec` |
| drzwi podwójnych na stronę | 18 | `spec` |
| szerokość otworu drzwi podwójnych | 1,60 m | `spec` |
| drzwi kabinowych pojedynczych, razem | 2 | `spec` |

### 1.2 Założenia projektowe (`tools/blender/m7_layout.py`)

Żadnej z tych liczb **nie ma w publicznych materiałach STIB**. Wszystkie są parametrami
generatora i wszystkie są wypisane w `DESIGN_ASSUMPTIONS`.

| stała | wartość | dlaczego taka |
|---|---|---|
| `DESIGN_TOTAL_HEIGHT_M` | 3,60 m | wysokość całkowita pojazdu nie jest publikowana |
| `DESIGN_ROOF_CHAMFER_M` | 0,35 m | ścięcie naroża dachu; brak rysunku przekroju |
| `DESIGN_SHELL_THICKNESS_M` | 0,08 m | grubość skorupy, żeby podłoga wypadła dokładnie na 1,03 m |
| `DESIGN_ARTICULATION_LENGTH_M` | 1,10 m | długość mieszka przegubu |
| `DESIGN_ARTICULATION_INSET_M` | 0,18 m | wcięcie mieszka względem pudła |
| `DESIGN_NOSE_LENGTH_M` | 2,40 m | długość strefy czołowej |
| `DESIGN_NOSE_INSET_M` | 0,45 m | zwężenie czoła |
| `DESIGN_NOSE_ROOF_DROP_M` | 0,30 m | obniżenie dachu na czole |
| `DESIGN_CAB_LENGTH_M` | 3,60 m | długość kabiny |
| `DESIGN_DOOR_OPENING_HEIGHT_M` | 1,95 m | wysokość otworu drzwi pasażerskich |
| `DESIGN_CAB_DOOR_WIDTH_M` | 0,80 m | szerokość drzwi kabinowych |
| `DESIGN_CAB_DOOR_HEIGHT_M` | 1,87 m | wysokość drzwi kabinowych |
| `DESIGN_CAB_DOOR_CENTER_FROM_END_M` | 2,90 m | położenie drzwi kabinowych |
| `DESIGN_EQUAL_CAR_SPLIT` | `True` | równy podział 94 m na 6 członów |

**Konsekwencja, którą warto znać:** równy podział daje cięciwę nominalną 15,667 m, a
rzeczywiste pudła wychodzą 15,117 m (skrajne) i 14,567 m (środkowe), bo między nimi są
mieszki. Model analityczny skrajni używa cięciwy nominalnej i jest przez to
**zachowawczy o ok. 50 mm** wobec pomiaru na siatce (`reports/M7-in-tunnel.md`, §3).

### 1.3 Świadomie niemodelowane

| wymiar | status | co blokuje |
|---|---|---|
| rozstaw czopów skrętu | `blocked` | brak w publicznych materiałach; **działa przeciwnie do strzałki cięciwy, więc rzeczywisty luz jest mniejszy niż policzony** |
| geometria wózków | `blocked` | to samo |
| podział długości między człony | `design_assumption` | patrz `DESIGN_EQUAL_CAR_SPLIT` |
| okna, wnętrze, kabina, poszycie | poza zakresem | T-220 celowo tego nie robi |

## 2. Profile tuneli (`tools/blender/profiles.py`)

Wszystkie trzy mają `source_level: design`. **Żaden nie jest pomiarem STIB.**

| profil | wymiary | tory | status |
|---|---|---|---|
| `box_double` | 9,40 × 5,90 m | ±2,10 m | `design_assumption` |
| `bore_single` | 6,08 × 5,70 m | 0,0 m | `design_assumption` |
| `station` | 15,20 × 6,50 m | ±2,10 m | `design_assumption` |
| `CLEARANCE_M` (luz skrajni) | 0,30 m | — | `design_assumption` |

### 2.1 Zmierzone alternatywy — NIE wpisane do kodu

Dwie z tych liczb mają już zmierzone odpowiedniki z oficjalnych źródeł. **Nie zostały
podstawione**, bo zamiana wymiaru projektowego na wartość ze źródła jest decyzją
właściciela i należy do R-005 (#17).

| wymiar | w kodzie | zmierzone | źródło | dlaczego nie podstawione |
|---|---|---|---|---|
| szerokość otworu `box_double` | 9,40 m | mediana **8,77 m**, P05–P95 8,25–9,92 m | poligony `MT` UrbIS, CC0 (`reports/M7-curve-clearance.md` §4) | dataset nie mówi, czy poligon jest **światłem tunelu**, czy **obrysem konstrukcji z murami** |
| rozstaw torów | 4,20 m (±2,10 m) | **3,294 m** (±1,647 m), P05–P95 3,03–4,37 m | INSPIRE Rails STIB (`reports/L1_A-track-spacing.md`) | zmierzono odległość dwóch polilinii **tras handlowych**, nie rozstaw torów; trzy źródła dają 3,29 / 3,34 / 3,88 m, a `docs/07` zabrania uśredniania; rozstaw nie jest stały |
| szerokość `bore_single` | 6,08 m | najwęższy tunel w **całej sieci**: **6,75 m** | 87 poligonów `MT` UrbIS, `tunnel_width.py --survey` | nic w sieci nie jest tak wąskie, a najwęższy kandydat leży poza pakietem A; ale poligon może być obrysem konstrukcji z murami, więc światło bywa węższe |
| szerokość `station` | 15,20 m | mediana sieci **15,55 m**, P05–P95 11,22–24,75 m | 69 poligonów `MS` UrbIS | **wartość projektowa trafia w medianę** — inaczej niż `bore_single`. Ale poligon `MS` to całe pudło stacji z antresolami, nie komora na poziomie peronu, więc waliduje rząd wielkości, nie wymiar |

Stacje pakietu A rozpinają się od **12,02 m** (Merode) do **24,64 m** (De Brouckère) —
ponad dwukrotnie. **Jeden profil `station` nie odwzoruje ich wszystkich**; to wejście
dla T-211 (#18) i R-004 (#16).

**Cztery niepewności działają w tę samą stronę** (mniejszy promień, węższy otwór, zwis
czopów, przechyłka), a **piąta w przeciwną** (węższy rozstaw torów). Żadnej nie wolno
domykać zgadywaniem, i żadnej nie wolno liczyć w oderwaniu od pozostałych.

### 2.2 Ustalenie, które wymaga decyzji

`bore_single` **nie mieści** 94-metrowego składu na łuku R = 51 m — brakuje 11 cm
(`reports/M7-curve-clearance.md` §3). Zgodnie z regułą z #14 pociąg **nie jest zwężany**;
problem leży po stronie placeholderowego profilu i wymaga albo źródła z R-005, albo
świadomej zmiany wymiaru projektowego.

## 3. Oś trasy (`data/track/L1_A.json`)

| wielkość | wartość | status |
|---|---|---|
| przebieg poziomy pakietu A | 447 punktów, 6686,35 m | **`spec`** — geometria STIB `ACTU_LIGNES_BRUTES` |
| chainage stacji | 12 wartości | **`spec`** — rzutowanie przystanków STIB na oś |
| profil pionowy | brak, Z = 0 | **`blocked`** — brak publicznych rzędnych główki szyny (T-901) |
| głębokości stacji | `null` | **`blocked`** — 6 z 12 stacji ma dane z dwóch **sprzecznych** źródeł oficjalnych |

Ograniczenie źródła, wpisane w `sources.json`: `ACTU_LIGNES_BRUTES` to **trasy handlowe**,
nie geometria tor-po-torze. Stąd rozstaw torów nie może być z niej wzięty.

## 4. Parametry generatora tunelu (`tools/blender/sweep.py`)

Żaden z nich nie jest faktem o sieci. Wszystkie są decyzjami o tym, jak geometria
powstaje, i wszystkie mają zmierzone konsekwencje.

| stała | wartość | konsekwencja |
|---|---|---|
| `DEFAULT_RING_STEP_M` | 5,0 m | zagęszczenie osi krzywą Catmull-Rom. Odchyłka od surowej łamanej STIB **0,1064 m**; minimalny promień spada z 97,3 m na 91,5 m. Tryb wierny `--ring-step 0` daje odchyłkę 0,0000 m |
| `DEFAULT_STATION_HALO_M` | 90,0 m | promień wokół stacji, w którym nie wolno postawić szwu chunka. Przyjęte ≈ długość składu M7 (94,0 m), bo **długość peronów STIB nie jest publiczna** |
| `DEFAULT_MAX_CHUNK_M` | 800,0 m | granulacja streamowania. Ograniczenie **miękkie**: przy stacjach bliżej niż 2 × halo chunk zostaje dłuższy |
| `DEFAULT_MIN_CHUNK_M` | 120,0 m | minimalna długość chunka |
| `DEFAULT_STREAM_AHEAD_M` | 600,0 m | okno streamowania przed składem, z `docs/01-architecture.md` |
| `DEFAULT_STREAM_BEHIND_M` | 300,0 m | okno za składem |
| `UV_METRES_PER_UNIT` | 4,0 m | gęstość UV. Wartość robocza, nie decyzja materiałowa |
| `DEGENERATE_AREA_M2` | 1e-06 | próg uznania ściany za zdegenerowaną |

## 4a. Parametry pomiaru skrajni (`tools/blender/clearance_profile.py`)

| parametr | wartość | uzasadnienie |
|---|---|---|
| krok skanu | 5,0 m | równy krokowi pierścieni osi; poniżej tego geometria nie ma własnej informacji, tylko interpolację. Przebieg kontrolny krokiem 2 m daje **to samo** minimum |
| doszlifowanie wokół dołka | 0,25 m | samo doszlifowanie obniża znalezione minimum o 3,194 mm wobec siatki zgrubnej |
| zakres zamiatanej obwiedni | ±150 m wokół minimum | pełna trasa to 3,5 MB w jednym GLB — kształt pliku odrzucony już przez T-210 na rzecz chunków |
| progi raportowania miejsc krytycznych | 1,000 / 0,950 / 0,900 / 0,500 / 0,300 / 0,000 m | wyłącznie do raportu; żaden nie jest wymogiem źródła |

## 5. Co jest zablokowane i czym

| potrzebne | blokuje | zadanie |
|---|---|---|
| rzędne główki szyny, profil pionowy | brak publicznych danych; dwa oficjalne źródła podają **sprzeczne** głębokości (Schuman 15 m vs 17,42 m; Botanique 21,5 vs 20 m) | T-112 (#10), research T-901 (#29) |
| długość i wysokość peronów, wyjścia, komunikacja pionowa | brak ground truth | R-004 (#16) → T-211 (#18) |
| przekrój tunelu, geometria toru, trzecia szyna, rozjazdy | brak ground truth | R-005 (#17) |
| rozstaw czopów skrętu M7 | brak w publicznych materiałach | pełna skrajnia kinematyczna |

Dopóki te pozycje są otwarte, **geometria produkcyjna nie może powstać** — obecny tunel
jest jawnie oznaczonym wariantem `flat-preview`, a generator odrzuca `--variant production`.

## 6. Jak to czytać przy podejmowaniu decyzji

1. Liczba ze statusem `spec` jest sprawdzalna — jest w rejestrze źródeł z URL-em i hashem.
2. Liczba ze statusem `design_assumption` **wolno zmienić bez pytania nikogo o zgodę**,
   ale nie wolno o niej powiedzieć „takie jest brukselskie metro".
3. Liczba ze statusem `observed` jest pomiarem z oficjalnych danych, ale nie wymiarem
   publikowanym — jej awans do `spec` wymaga rozstrzygnięcia, co dokładnie zmierzono.
4. `blocked` znaczy, że **zatrzymanie się jest poprawnym wynikiem pracy**, a nie porażką
   (`CLAUDE.md` §8).
