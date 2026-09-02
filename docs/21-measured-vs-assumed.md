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

## 5. Co jest zablokowane i czym

| potrzebne | blokuje | zadanie |
|---|---|---|
| rzędne główki szyny, profil pionowy | brak publicznych danych; dwa oficjalne źródła podają **sprzeczne** głębokości (Schuman 15 m vs 17,42 m; Botanique 21,5 vs 20 m) | T-112 (#10), research T-901 (#29) |
| długość i wysokość peronów, wyjścia, komunikacja pionowa | brak ground truth | R-004 (#16) → T-211 (#18) |
| przekrój tunelu, geometria toru, trzecia szyna, rozjazdy | brak ground truth | R-005 (#17) |
| rozstaw czopów skrętu M7 | brak w publicznych materiałach | pełna skrajnia kinematyczna |
| udział osi hamowanych, rozdział hamulca ED/P, krzywe bezpieczeństwa STIB | brak w publicznych materiałach; §4b modeluje wyłącznie sam udział osi i to jako parametr o dwóch wariantach skrajnych | T-311 zostawia otwarte, T-313 (#22) będzie tego potrzebować |
| prędkość dopuszczalna na torze | brak źródła; `speed_limits` puste we wszystkich sześciu osiach. §4d daje wyłącznie ograniczenie **dolne** (57,65 km/h), warunkowe względem modelu | T-011, T-320; wpis do `data/track/` wymaga źródła STIB |
| czas wymiany pasażerów | brak źródła; §4d daje wyłącznie ograniczenie **górne** z postoju rozkładowego | T-312 zostawia jako argument |

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
