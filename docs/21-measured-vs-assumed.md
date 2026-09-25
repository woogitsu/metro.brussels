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

**Piąta nazwa, `design_model`, NIE jest tu zdefiniowana i nie ma być** (10.09.2026,
6.D105). Definiuje ją `docs/02-simulation.md`: „świadome założenie symulatora", i tam
też stoi jej znaczenie. Ten dokument klasyfikuje **wymiary geometrii**, tamten —
**parametry modelu jazdy**, i to są dwie różne role, więc tabele zostają dwie.
`design_model` pojawia się niżej **sześć razy** (stan na 10.09.2026), zawsze tam, gdzie
mowa o wartości pochodzącej z modelu jazdy, a nie z pomiaru geometrii. Tabele mają
**dwie nazwy wspólne** (`spec`, `observed`) i po dwie wyłączne: tu `design_assumption`
i `blocked`, tam `est` i `design_model`. Pilnuje tego
`tools/tests/test_provenance_classes.py`.

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
| `DESIGN_WINDOW_BAND_BOTTOM_M` | 2,05 m | dolna granica neutralnego ciemnego pasa na ścianie bocznej; nie jest pomiarem okien M7 |
| `DESIGN_WINDOW_BAND_TOP_M` | 2,78 m | górna granica tego pasa, poniżej projektowej fazy dachu |
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
| przezroczyste szyby, wnętrze, kabina, detale poszycia | poza zakresem | ciemny pas boczny jest neutralnym znacznikiem wizualnym, nie odtworzeniem okien M7 |

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

## 3. Oś trasy (`data/track/*.json`)

| wielkość | wartość | status |
|---|---|---|
| przebieg poziomy pakietu A | 447 punktów, 6686,35 m | **`spec`** — geometria STIB `ACTU_LIGNES_BRUTES` |
| chainage stacji | 12 wartości | **`spec`** — rzutowanie przystanków STIB na oś |
| profil pionowy | brak, Z = 0 | **`blocked`** — brak publicznych rzędnych główki szyny (T-901) |
| głębokości stacji | `null` | **`blocked`** — 6 z 12 stacji ma dane z dwóch **sprzecznych** źródeł oficjalnych |

Pakiety B–F powstały tą samą metodą i mają te same statusy: przebieg i chainage
`spec`, profil pionowy i głębokości `blocked`. Pomiary i rozstrzygnięcia:
`reports/packages-BF-alignment.md`.

| oś | pakiet | źródło STIB | punktów | długość |
|---|---|---|---:|---:|
| `L1_B.json` | B — Wschód 1 | `001m` v1 | 340 | 5083,23 m |
| `L5_C.json` | C — Zachód 5 | `005m` v2 | 361 | 5386,41 m |
| `L5_D.json` | D — Wschód 5 | `005m` v1 | 258 | 3847,23 m |
| `L2_E.json` | E — Pierścień 2/6 | `002m` v2 | 603 | 9020,77 m |
| `L6_F.json` | F — Północ 6 | `006m` v2 | 299 | 4456,66 m |

| wielkość | wartość | status |
|---|---|---|
| krok próbkowania 15 m | jedyny z badanych (5/10/15/20/25 m), który na **wszystkich** sześciu pakietach mieści się w granicach walidatora (odstęp ≤ 25 m, R ≥ 90 m) | **`design_assumption`** — wybór potwierdzony pomiarem, ale nie wymóg źródła |
| `niveau = 0` w UrbIS na osiach | A 4,0 %, B 0,0 %, C 8,6 %, D **37,6 %**, E 2,0 %, F 15,7 % punktów | **`observed`** — pomiar pokrycia; **znaczenia pola dataset nie definiuje**, więc nie wolno z tego wyprowadzić „ten odcinek jest naziemny" bez R-005 (#17) |
| odległość peronów Elisabeth ↔ Simonis | **18,7 m** (najbliższa para z czterech peronów) | **`observed`** — pomiar z `ACTU_STOPS`; nie rozstrzyga, czy to jedna stacja, czy dwie |

Ograniczenie źródła, wpisane w `sources.json`: `ACTU_LIGNES_BRUTES` to **trasy handlowe**,
nie geometria tor-po-torze. Stąd rozstaw torów nie może być z niej wzięty.

## 4. Parametry generatora tunelu (`tools/blender/sweep.py`)

Żaden z nich nie jest faktem o sieci. Wszystkie są decyzjami o tym, jak geometria
powstaje, i wszystkie mają zmierzone konsekwencje.

| stała | wartość | konsekwencja |
|---|---|---|
| `DEFAULT_RING_STEP_M` | 5,0 m | zagęszczenie osi krzywą Catmull-Rom. **Dwie różne odchyłki, obie zmierzone na pakiecie A:** od surowej łamanej STIB (345 punktów, odstęp 19,44 m) **0,1064 m**, od skomitowanej łamanej 15 m **0,2499 m** — tę drugą raportuje generator jako `smoothing_max_deviation_m`. Minimalny promień spada z 97,3 m na 91,5 m. Tryb wierny `--ring-step 0` daje odchyłkę 0,0000 m |
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

## 4b. Model hamowania (`src/Sim/Physics`, T-311)

Hamowanie w T-310 i T-400 było **poleceniem**: zadane opóźnienie z ograniczeniem
zrywu, niezależne od masy i przyczepności. T-311 dokłada do tego sufit
przyczepnościowy, solver punktu hamowania i drogę hamowania liczoną z oporami ruchu.
Wartości 1,10 / 1,30 m/s² i zryw 0,75 m/s³ pochodzą z `docs/02-simulation.md` i mają
w rejestrze status `design_model` (§ wyżej). Poniżej są **wyłącznie liczby, których
w rejestrze nie ma**, i pilnuje ich `BrakingTests` po stronie C# oraz
`tools/tests/test_braking.py` po stronie Pythona.

| stała | wartość | status | dlaczego taka |
|---|---:|---|---|
| `AllAxlesBrakedMassFraction` | 1,00 | **`design_assumption`** | górny kres udziału osi hamowanych. STIB/CAF nie publikuje układu hamulcowego M7, więc 1,0 jest granicą przedziału, w którym leży wartość prawdziwa, a nie pomiarem |
| `PoweredAxlesBrakedMassFraction` | 0,6667 (4/6) | **`design_assumption`** | wariant dolny: hamują wyłącznie osie napędne. Liczba pochodzi z `parameters.powered_mass_fraction`, która w rejestrze sama jest `design_model` i jest opisana jako legacy parametr limitu adhezji **dla trakcji** — przeniesienie jej na hamowanie jest osobnym założeniem |
| `BrakeForceInertiaFactor` | 1,08 | **`design_assumption`** | siła hamulca liczona jest od masy efektywnej (`m · λ`), tak samo jak `TrainController` zamienia opóźnienie na ruch. Rozdziału bezwładności wirującej na osie hamowane i niehamowane nie ma w danych, więc raport podaje **obie** skrajne interpretacje |

**Czego tu celowo nie ma i dlaczego.** W rejestrze źródeł nie ma rozdziału hamulca
elektrodynamicznego i pneumatycznego, nie ma charakterystyki zanikania ED przy niskiej
prędkości, nie ma krzywych bezpieczeństwa STIB ani rzeczywistych czasów reakcji układu.
Żadnej z tych rzeczy T-311 **nie modeluje**. Model, który dzieli siłę hamowania na dwa
człony bez źródła na proporcję, wygląda dokładnie tak samo jak model prawdziwy —
i to jest dokładnie ta sytuacja, o której mówi reguła 1 z `CLAUDE.md`.

**Konsekwencja, którą warto znać** (`reports/T-311-braking.md` §2): przy μ = 0,13
(mokra szyna, `design_model`) hamowanie awaryjne 1,30 m/s² wymaga udziału osi
hamowanych **1,101**, czyli jest nieosiągalne przy każdym układzie hamulcowym.
Wniosek nie zależy od decyzji o masach wirujących — bez współczynnika λ potrzebny
udział to nadal 1,020. Hamowanie służbowe 1,10 m/s² na mokrej szynie wymaga **0,932**,
czyli jest osiągalne dopiero, gdy hamuje ponad 93 % masy składu.

## 4c. Cykl drzwi i czas postoju (`src/Sim/Train/DoorCycle.cs`, T-312)

`docs/02-simulation.md` podaje cykl wprost: odryglowanie 0,5 s → otwieranie 2,0 s →
wymiana pasażerów → sygnał zamykania 3,0 s → zamykanie 2,5 s → kontrola 0,5 s, wszystko
`design_model`. Pięć faz o stałym czasie jest więc przepisane z dokumentu i nie dokłada
żadnej nowej liczby. **Jedna wielkość cyklu nie ma w dokumencie wartości i nie dostała
jej też tutaj.**

| wielkość | wartość | status | dlaczego taka |
|---|---:|---|---|
| `MinimumDwellSeconds` | 8,5 s | **wyprowadzone** | suma pięciu faz stałych, nie osobna liczba. Test przypina równość sumie, żeby nikt nie mógł jej „poprawić" bez zmiany faz |
| czas wymiany pasażerów | **brak** | **argument, nie stała** | zależy od potoku, pory dnia i stacji — w rejestrze źródeł nie ma ani jednej z tych rzeczy. `DoorCycle` przyjmuje go jako parametr konstruktora; scenariusz, który go poda, musi zadeklarować własne założenie |

**Dlaczego nie ma tu domyślnej wartości wymiany pasażerów.** Domyślna liczba w tym
miejscu byłaby wpisaniem czasu postoju metra brukselskiego bez żadnej podstawy — a to
jest liczba, którą ktoś potem zacytuje. Kod woli nie skompilować się bez niej, niż
podać zmyśloną. Zero jest dopuszczalne i znaczy „nikt nie wysiada", a nie „drzwi się
nie otwierają": cykl i tak trwa pełne 8,5 s.

**Blokada jazdy nie jest parametrem.** `docs/02` mówi „jazda zablokowana do
potwierdzenia zamknięcia", więc trakcja jest wolna wyłącznie w fazie `Closed` — po
kontroli, a nie w chwili zetknięcia skrzydeł. To jest własność bezpieczeństwa i test
sprawdza ją dla **każdej** fazy wyliczeniowo, a nie dla wybranych.

## 4d. Rozkład jazdy i koperta prędkości liniowej (`tools/track/timetable.py`, T-113)

Wszystko w tej sekcji jest **zmierzone** z oficjalnego GTFS STIB. Ani jedna liczba nie
jest tu założeniem — jest to jedyna sekcja tego dokumentu, w której kolumna „status" ma
wyłącznie wartość `zmierzone`, i dlatego warto ją czytać jako punkt odniesienia dla reszty.

| wielkość | wartość (środa 2026-09-02) | status |
|---|---:|---|
| takt L1, L5 (mediana i szczyt) | 5:10 | zmierzone |
| takt L2, L6 (mediana i szczyt) | 5:40 | zmierzone |
| rozpiętość służby | ok. 05:00–24:30 | zmierzone |
| postój na zatrzymaniu pośrednim | 12–45 s, mediana 19 s (L1/L5) i 24 s (L2/L6) | zmierzone |
| udział zatrzymań pośrednich z postojem | **100,0 %** (29 554 z 29 554) | zmierzone |
| kursów naraz w ruchu | 48 | zmierzone |
| obiegów pojazdów (`block_id`) | 71, naraz w służbie 56 | zmierzone |

**Co to zmienia dla §4c.** Czas wymiany pasażerów nadal nie ma wartości i `DoorCycle`
nadal jej nie dostaje. Ale rozkład go **ogranicza od góry**: postój ≥ cykl drzwi 8,5 s +
wymiana, więc przy medianowym postoju 19 s wymiana nie przekracza 10,5 s, a przy
najkrótszym w sieci (12 s) nie przekracza 3,5 s. Jest to pierwszy zmierzony przedział,
jaki repo ma dla tej wielkości. Górny, nie dolny — postój może zawierać także rezerwę.
To **nie jest** licencja na wpisanie liczby.

**Koperta prędkości liniowej.** `speed_limits` w każdej z sześciu osi z T-210 jest pustą
listą, a `max_speed_kmh` = 80 w rejestrze M7 to `design_model` bez `source_id` — prędkość
konstrukcyjna pojazdu, nie dopuszczalna na torze. Rozkład ogranicza tę dziurę od dołu:
dla odcinka o zmierzonej długości i rozkładowym czasie jazdy istnieje najmniejsza prędkość
szczytowa, przy której profil rozpęd–jazda–hamowanie się mieści.

| wielkość | wartość | status |
|---|---:|---|
| dolne ograniczenie prędkości liniowej, AW0 | **57,65 km/h** (Beaulieu → Demey) | wyprowadzone, warunkowe |
| to samo dla AW2 | 61,42 km/h (Aumale → Saint-Guidon) | wyprowadzone, warunkowe |
| odcinków nierealizowalnych przy modelu z T-310/T-311 | **0 z 55** | zmierzone |

**Warunkowe względem czego.** Względem krzywej trakcyjnej z T-310 i hamulca służbowego
1,10 m/s² z `docs/02` — obu `design_model`. Mocniejszy rozpęd obniżyłby to ograniczenie.
Liczba mówi „przy tym modelu nie da się wolniej", a nie „tak jeździ metro". Do
`data/track/*.json` **nie została wpisana** i nie powinna: w polu `speed_limits`
wyglądałaby dokładnie tak samo jak ograniczenie ze źródła STIB.

Szczegóły i pełne wyjście: `reports/T-113-timetable.md`.

## 4e. Elementy stacji ponad peronem (`tools/track/station_components.py`, T-212)

**Wszystkie wartości w tej sekcji mają status `design_assumption`. Żadna nie pochodzi
ze STIB.** R-007 ustalił, że STIB nie publikuje rzutów stacji, a obrysy z UrbIS mówią
tylko, ile miejsca stacja zajmuje na powierzchni. Układ zbudowany przez T-212 jest
**kanoniczny**, a nie odwzorowaniem którejkolwiek brukselskiej stacji, i tak jest opisany
w `not_modelled` metryk oraz w `reports/T-212-station.md`.

| stała | wartość | co opisuje |
|---|---|---|
| `DESIGN_STAIR_RISER_M` | 0,17 m | wysokość stopnia; z `DESIGN_STAIR_GOING_M` daje wzór Blondela 2·podstopnica + stopnica = 0,63 m |
| `DESIGN_STAIR_GOING_M` | 0,29 m | głębokość stopnia |
| `DESIGN_STAIR_WIDTH_M` | 2,40 m | szerokość biegu |
| `DESIGN_STAIR_MAX_RISERS` | 16 | najwięcej stopni w biegu bez spocznika |
| `DESIGN_STAIR_LANDING_M` | 1,20 m | długość spocznika |
| `DESIGN_LIFT_PLAN_M` | 2,10 × 2,60 m | rzut szybu windy |
| `DESIGN_SLAB_THICKNESS_M` | 0,40 m | grubość płyty antresoli |
| `DESIGN_MEZZANINE_CLEAR_M` | 2,60 m | wysokość w świetle na antresoli |
| `DESIGN_MEZZANINE_LENGTH_M` | 24,0 m | rozciągłość antresoli wzdłuż osi |
| `DESIGN_CORRIDOR_WIDTH_M` | 3,00 m | szerokość korytarza do portalu |
| `DESIGN_CORRIDOR_CLEAR_M` | 2,40 m | wysokość korytarza w świetle |
| `DESIGN_CORRIDOR_LENGTH_M` | 12,0 m | długość korytarza od ściany komory |
| `DESIGN_PORTAL_WIDTH_M` | 4,00 m | szerokość portalu wejściowego |
| `DESIGN_PORTAL_CLEAR_M` | 2,60 m | wysokość portalu w świetle |
| `DESIGN_PORTAL_DEPTH_M` | 1,50 m | głębokość portalu |
| `DESIGN_ACCESS_SETBACK_M` | 4,0 m | odsunięcie zespołu dostępu od końca peronu |
| `DESIGN_VOID_MARGIN_M` | 0,30 m | zapas otworu antresoli wokół obrysu schodów i windy |
| `DESIGN_PLATFORM_LENGTH_M` | 95,0 m | długość peronu, na której stoi zespół dostępu — decyzja właściciela z 04.09.2026 (patrz akapit niżej) |

**Długość peronu 95,0 m ma dwie granice, których nie wybrano — udowodniono je w R-007.**
Dolna to długość składu M7 **94,0 m** (`data/vehicle/m7-spec.json`, status `spec`): peron
krótszy od składu jest sprzeczny z ruchem bez selektywnego otwierania drzwi, którego STIB
nie stosuje. Górna to obrys stacji z UrbIS (poligony `MS`, CC0), najciaśniej **Parc
109,1 m** — R-007 §5 pkt 3 robi z niej **kontrolę**: „generator dający peron dłuższy niż
obrys stacji jest na pewno błędny". Sama liczba 109,1 m **nie jest** `design_assumption`,
jest pomiarem, i dlatego stoi w kodzie poza `DESIGN_ASSUMPTIONS`, jako
`TIGHTEST_STATION_FOOTPRINT_M`. Kontrolę wykonuje `platform_fits_the_station()`, wołane
przez `station_kit.py` przed postawieniem zespołu, i pilnuje jej
`test_components_platform_length_stays_within_the_tightest_station_footprint`.

Wybór **95,0 m** wewnątrz tych granic jest jedyną decyzją i jest to składowa suma:
94,0 m składu **plus metr zapasu, po 0,50 m z każdej strony**. Zapas nie jest okrągły dla
ozdoby — 1,00 m to **3,2×** największy zmierzony błąd zatrzymania autopilota na pakiecie A
(0,307 m, `reports/T-401-line-run.md` §2). Wartość mieści się też w rozrzucie peronów OSM
z R-007 §4: 26 z 28 leży w 94,76 ± 0,78 m, czyli do 95,54 m. **Poprzednia wartość tego
zadania, 110 m, wpadała w kontrolę** — przekraczała obrys Parc o 0,9 m — i została
zmieniona 04.09.2026 decyzją właściciela.

**Co NIE jest tu założeniem.** Poziomy stacji nie są wpisane — są liczone z profilu
`station` i z wysokości peronu: strop komory 5,30 m i peron 1,03 m dają 4,27 m w świetle,
a stąd wynika, że antresola nie mieści się WEWNĄTRZ komory (płyta 0,40 m plus 2,60 m
w świetle zostawiłyby górnemu poziomowi 1,27 m). Antresola idzie więc nad stropem
i to jest rachunek, nie wybór. Wysokość peronu 1,03 m ma status `spec`.

**Świadomie niemodelowane w T-212:** rzut stacji, liczba i położenie wyjść, bramki
biletowe i kasy, konstrukcja (słupy, belki, dylatacje), instalacje.

**Neutralne tablice nazw stacji** (`tools/blender/station_board.py`,
`StationView.AddNameMarkers`) mają status `design_assumption`. Nazwy pochodzą z osi
trasy; pełna nazwa dwujęzyczna zajmuje dwa wiersze. Jednorzędna płytka ma wysokość
0,80 m i środek na 4,25 m nad główką szyny, a dwurzędna 1,10 m i środek na 4,40 m.
Obie zaczynają się na 3,85 m: 0,25 m nad projektowym dachem M7 (3,60 m).
Dwurzędna kończy się na 4,95 m: 0,35 m pod stropem komory (5,30 m).
Położenie 15 m za osią stacji i neutralny wygląd są wyborem dla czytelności z kabiny,
nie odwzorowaniem oznakowania STIB/MIVB.

## 4g. Kabina maszynisty — układ kanoniczny (`tools/blender/m7_cab.py`, 6.D119)

**Wszystkie wartości w tej sekcji mają status `design_assumption`. Żadna nie pochodzi
ze STIB.** STIB nie publikuje rzutów kabiny, a `docs/03-legal.md` nie daje prawa do
cudzych rysunków ani do odwzorowywania kabiny ze zdjęć. Układ zbudowany przez 6.D119
jest **kanoniczny** — podłoga, ściana do przedziału pasażerskiego z jednymi drzwiami
i fotel, obecnie bez pulpitu — a nie odwzorowaniem kabiny M7, i tak jest opisany w `not_modelled`
raportu generatora oraz w `reports/6d119-kabina-kanoniczna.md`.

Ze `spec` przychodzą tu **wyłącznie** wymiary skorupy, przez `m7_layout.Layout`:
szerokość pudła, wysokość podłogi i długość składu. Wszystko poniżej jest decyzją.

| stała | wartość | co opisuje |
|---|---|---|
| `DESIGN_BULKHEAD_DOOR_HEIGHT_M` | 1,90 m | wysokość światła tych drzwi |
| `DESIGN_BULKHEAD_DOOR_WIDTH_M` | 0,70 m | szerokość drzwi w tej ścianie |
| `DESIGN_CAB_BULKHEAD_FRONT_M` | 0,35 m | odległość czubka czoła od wewnętrznego lica szyby czołowej; kabina zaczyna się za nosem |
| `DESIGN_CAB_BULKHEAD_M` | 0,08 m | grubość ściany do przedziału pasażerskiego |
| `DESIGN_CAB_CLEAR_HEIGHT_M` | 2,05 m | światło kabiny nad podłogą |
| `DESIGN_CAB_FLOOR_SLAB_M` | 0,06 m | grubość płyty podłogowej kabiny; leży na wysokości podłogi pudła ze `spec` |
| `DESIGN_CAB_LINING_M` | 0,05 m | grubość wykładziny ściany bocznej, od lica skorupy do wnętrza |
| `DESIGN_CAB_WINDOW_HEAD_M` | 1,60 m | nadproże okna bocznego |
| `DESIGN_CAB_WINDOW_LENGTH_M` | 0,70 m | długość okna bocznego kabiny wzdłuż osi |
| `DESIGN_CAB_WINDOW_SILL_M` | 1,00 m | parapet okna bocznego |
| `DESIGN_SEAT_BACK_HEIGHT_M` | 0,55 m | wysokość oparcia nad siedziskiem |
| `DESIGN_SEAT_BACK_M` | 0,10 m | grubość oparcia |
| `DESIGN_SEAT_CUSHION_M` | 0,48 m | wysokość górnego lica siedziska nad podłogą |
| `DESIGN_SEAT_DEPTH_M` | 0,45 m | głębokość siedziska |
| `DESIGN_SEAT_FRONT_M` | 1,45 m | początek siedziska od czoła składu; utrzymuje fotel pod okiem kamery bez pulpitu |
| `DESIGN_SEAT_WIDTH_M` | 0,50 m | szerokość siedziska |
| `DESIGN_WINDSCREEN_HEAD_M` | 1,95 m | nadproże szyby czołowej |
| `DESIGN_WINDSCREEN_MARGIN_M` | 0,15 m | margines szyby czołowej od ściany bocznej |
| `DESIGN_WINDSCREEN_SILL_M` | 0,95 m | parapet szyby czołowej nad podłogą kabiny |

**Co NIE jest tu założeniem.** Połowa szerokości wnętrza nie jest wpisana — liczy się
z przekroju skorupy w najwęższym miejscu kabiny (przy licu szyby czołowej) minus
wykładzina, więc zmiana szerokości pudła we `spec` przechodzi do kabiny sama.
Że każda bryła mieści się w tym przekroju, pilnuje `tools/tests/test_m7_cab.py`,
a nie zdanie w tym dokumencie.

**Świadomie niemodelowane obecnie:** pulpit i nastawniki (usunięte, by odsłonić tory),
kształt fotela, przyrządy i wskaźniki, rzeczywiste wymiary kabiny M7. Wycięcie szyb
w skorupie należy do generatora skorupy i nie jest zrobione — otwory są tu policzone
jako dane i sprawdzone, że mieszczą się w przekroju pudła.

## 4f. Czas nawrotu na krańcówce (`src/Sim/Line/LineCore.cs`, turnback, T-320)

`docs/TASKS.md` mówił o tym: „**logika turnback**, model perturbacji i polityka dyspozytora
**nie są opisane w żadnym dokumencie**". Dla samego czasu nawrotu to już **nieprawda**
i dlatego ta sekcja istnieje — reszta tamtego zdania (perturbacje, polityka dyspozytora)
obowiązuje dalej.

### Zmierzone 04.09.2026 z feedu GTFS STIB

Feed pobrany z adresu z `data/network/gtfs-manifest.json`; suma `sha256` pliku **zgadza się
z zapisanym `content_sha256`** co do znaku (`28c2fba4…78bb6`), czyli to ten sam feed, który
projekt już zarejestrował. Kursy połączone po `block_id` — GTFS wiąże w ten sposób kursy
wykonywane po kolei tym samym pojazdem — i ograniczone do **linii 1 i 5**, bo pakiet A to
ta para linii.

Nawrót policzony jako luka między **ostatnim przyjazdem** jednego kursu i **pierwszym
odjazdem** następnego w tym samym obiegu:

| wielkość | wartość |
|---|---|
| obiegów (linie 1 i 5) | **194** |
| nawrotów w łańcuchach | **4289** |
| minimum | **240 s** |
| p05 | 259 s |
| mediana | **445 s** |
| p95 | 841 s |
| maksimum | **1005 s** |
| nawrotów poniżej 240 s | **0** |
| nawrotów nakładających się (ujemnych) | 0 |

Stacje nawrotu, po liczbie wystąpień:

| stacja | nawrotów | minimum | mediana |
|---|---|---|---|
| Gare de l'Ouest | 1126 | 377 s | 556 s |
| Herrmann-Debroux | 1070 | 375 s | 615 s |
| Stockel | 1067 | 240 s | 468 s |
| Erasme | 1026 | 240 s | 352 s |

### Dwa zastrzeżenia, bez których ta liczba kłamie

1. **To nie jest techniczne minimum nawrotu.** Luka między kursami zawiera też postój
   wyrównawczy, więc 240 s jest ograniczeniem **na rozkład**: STIB nie planuje nawrotu
   krótszego. Ile trwa sam manewr, tego GTFS nie mówi i nie powie.
2. **Merode nie jest krańcówką.** W GTFS krańcówkami linii 1 są Gare de l'Ouest i Stockel,
   linii 5 — Erasme i Herrmann-Debroux. Merode jest **granicą pakietu A**, czyli cięciwem
   sieci na potrzeby tego projektu. Nawrót tam jest `design_assumption` wynikającym
   z decyzji właściciela z 04.09.2026 („nawrót na oba końce osi"), a **nie** faktem o ruchu
   STIB. Nawrót na Gare de l'Ouest ma pokrycie w danych; na Merode nie ma i nie będzie miał.

### Co z tego weszło do kodu

`LineCore` przyjmuje czas nawrotu jako **argument bez wartości domyślnej dodatniej**: zero
wyłącza turnback i wtedy linia zachowuje się jak przed tą zmianą. Wołający musi liczbę
podać, tak samo jak w `LineRunSettings`. Turnback **nie jest jazdą w przeciwną stronę** —
oś pakietu biegnie w jednym kierunku, a przeciwny to osobna oś (pakiet A ma parę w B);
„nawrót" znaczy tu, że pojazd znika z tego planu i wraca na jego początek jako następny
obieg.

---

## 5. Co jest zablokowane i czym

| potrzebne | blokuje | zadanie |
|---|---|---|
| rzędne główki szyny, profil pionowy | brak publicznych danych; dwa oficjalne źródła podają **sprzeczne** głębokości (Schuman 15 m vs 17,42 m; Botanique 21,5 vs 20 m). **R-007** dołożył trzy stacje z EIE Métro 3 jako `estimated` (De Brouckère i Arts-Loi ok. 11 m, Parc 19 m) — trzy z dwunastu to nadal nie profil | T-112 (#10), research T-901 (#29) |
| **wysokość peronu nad główką szyny** | **1,03 m, `source_backed`** — STIB pisze, że podłoga M7 (1 m 03) jest „à hauteur du quai", w dwóch niezależnych publikacjach. **Zastrzeżenie:** STIB nie deklaruje, względem czego mierzy tę wysokość; baza odniesienia to konwencja branżowa | `reports/R-007-platform-dimensions.md` |
| **długość peronu** | **brak źródła w ogóle.** Udowodnione ograniczenie `94,0 m ≤ L ≤ obrys stacji`; najciaśniej Parc 109,1 m. Pomiar OSM 94,76 ± 0,78 m to `openstreetmap`, klasa niżej, i dwa z 28 obrysów wypadają PONIŻEJ długości składu — błąd obrysu co najmniej ±0,5 m. Liczba „125 m średnio" z Wikipedii wstawiona 2007 bez źródła i sprzeczna z pomiarem o ~30 % | `reports/R-007-platform-dimensions.md`, T-211 |
| długość i wysokość peronów, wyjścia, komunikacja pionowa | brak ground truth | R-004 (#16) → T-211 (#18) |
| przekrój tunelu, geometria toru, trzecia szyna, rozjazdy | brak ground truth | R-005 (#17) |
| rozstaw czopów skrętu M7 | brak w publicznych materiałach | pełna skrajnia kinematyczna |
| udział osi hamowanych, rozdział hamulca ED/P, krzywe bezpieczeństwa STIB | brak w publicznych materiałach; §4b modeluje wyłącznie sam udział osi i to jako parametr o dwóch wariantach skrajnych | T-311 zostawia otwarte, T-313 (#22) będzie tego potrzebować |
| prędkość dopuszczalna na torze | brak źródła; `speed_limits` puste we wszystkich sześciu osiach. §4d daje wyłącznie ograniczenie **dolne** (57,65 km/h), warunkowe względem modelu | T-011, T-320; wpis do `data/track/` wymaga źródła STIB |
| czas wymiany pasażerów | brak źródła; §4d daje wyłącznie ograniczenie **górne** z postoju rozkładowego | T-312 zostawia jako argument |
| ~~czas nawrotu na krańcówce~~ | **zmierzony 04.09.2026 z GTFS**: 194 obiegi, 4289 nawrotów, minimum 240 s, mediana 445 s, ani jednego poniżej 240 s. Ograniczenie **na rozkład**, nie techniczne minimum manewru — §4f | `LineCore` przyjmuje jako argument |
| model perturbacji, polityka dyspozytora | brak w jakimkolwiek dokumencie; to **zostaje** ze STOP-u T-320, mimo że czas nawrotu z niego wyszedł | T-320 |

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
