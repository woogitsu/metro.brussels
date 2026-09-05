# T-210 — poziomy szczegółowości i geometria kolizyjna chunków pakietu A

**Zmierzone na commicie:** `51fd842` · **data:** 2026-09-01

Wariant: **`flat-preview`, nieprodukcyjny** — jak w `reports/L1_A-geometry.md`
i `reports/L1_A-chunks.md`. Oś `data/track/L1_A.json` ma `vertical.status = "not_modelled"`,
cała geometria leży na Z = 0, generator odmawia wariantu `production` do zamknięcia
T-112 (#10).

## 0. Po co to jest

Manifest streamingowy z poprzedniego kroku mówi Godotowi, **co** wczytać. Nie mówi
**w jakiej rozdzielczości** ani **czym testować kolizje**. Chunk odległy o 500 m
dostawał tę samą gęstość pierścieni co chunk pod pociągiem, a kolizja nie istniała
w ogóle — GLB niósł samą siatkę wizualną (§7.2 i §7.3 `reports/L1_A-chunks.md`).

Ten krok dokłada trzy poziomy szczegółowości i osobną bryłę kolizyjną, **każde
z pomiarem tego, co kosztuje i co traci**. Progi odległości są policzone ze
zmierzonego błędu, nie zgadnięte, i są jawnie oznaczone jako `design_assumption` —
docelowe budżety mają wyjść z pomiaru na sprzęcie w T-400.

Uruchomienie bez zmian wobec poprzedniego kroku; LOD-y i kolizja powstają zawsze,
gdy podany jest `--chunk-dir`:

```bash
blender --background --python-exit-code 7 --python tools/blender/tunnel_sweep.py -- \
  --centerline data/track/L1_A.json --profile box_double --name L1_A \
  --out build/t210/L1_A.glb --metrics build/t210/L1_A-metrics.json \
  --chunk-dir build/t210/chunks --chunk-manifest build/t210/chunks/L1_A-chunks.json
```

Pełny pipeline kontrolny: `bash tools/ci/tunnel_alignment.sh` (~111 s, Blender 4.0.2;
było ~73 s). Nic z `build/` ani `renders/` nie jest komitowane.

## 1. Czym jest LOD w tym generatorze

**Podzbiorem pierścieni LOD 0, nie nowym zagęszczeniem osi.** Generator jest
parametryczny, więc rzadszy poziom dałoby się zrobić przez `--ring-step 20`. Tak
tego nie zrobiono, bo `catmull_rom` z innym krokiem daje inną długość osi i inne
chainage pierścieni: granice chunków przestałyby się pokrywać między poziomami,
a wtedy przełączenie LOD-a otwierałoby dziurę dokładnie na szwie. Tutaj wszystkie
poziomy siedzą na **tych samych ramkach**, pierwszy i ostatni pierścień chunka jest
zawsze zachowany, więc szczelina jest zerowa z konstrukcji — także wtedy, gdy chunk
*n* jest w LOD 0, a chunk *n+1* w LOD 2. Zmierzone: **0,0000 mm we wszystkich
dziewięciu parach poziomów.**

UV liczy się z chainage ramki (`v = station_m[i] / 4`), więc jest identyczne
w każdym poziomie i **przełączenie LOD-a nie przesuwa tekstury**. Jest na to test
(`test_lod_uv_along_the_axis_does_not_shift_between_levels`).

### 1.1 Krok pierścieni ma dwa parametry, nie jeden

Sam krok metryczny jest zły na osi, która ma i 700-metrowe proste, i łuki o R = 91,5 m.
Zmierzone na pakiecie A:

| selekcja | trójkąty | udział | błąd maks. | próg z tego błędu |
|---|---:|---:|---:|---:|
| cięciwa ≤ 25 m, bez limitu strzałki | 3312 | 20,5 % | **0,793 m** | 801 m |
| cięciwa ≤ 25 m, strzałka ≤ 0,15 m | 3912 | 24,2 % | **0,156 m** | 158 m |
| cięciwa ≤ 60 m, bez limitu strzałki | 1404 | 8,7 % | **4,350 m** | 4396 m |
| cięciwa ≤ 60 m, strzałka ≤ 0,35 m | 1992 | 12,3 % | **0,400 m** | 404 m |

Za 18 % więcej trójkątów drugi limit zbija błąd **pięciokrotnie**, a przy kroku 60 m
**jedenastokrotnie**. Dlatego każdy poziom jest opisany parą (`max_chord_m`,
`max_sagitta_m`): na prostej rządzi pierwszy, na łuku drugi. Selekcja jest zachłannym
dopasowaniem cięciwy (`lod.select_rings`), deterministycznym i czysto pythonowym.

### 1.2 Poziomy

| poziom | cięciwa | strzałka | do czego |
|---|---:|---:|---|
| 0 | — | — | chunk pod pociągiem i bliski plan; pełny zestaw pierścieni, referencja pomiaru |
| 1 | ≤ 25 m | ≤ 0,15 m | plan średni |
| 2 | ≤ 60 m | ≤ 0,35 m | plan daleki |

## 2. Zmierzony koszt

| poziom | trójkąty | udział | pliki GLB razem | udział bajtów |
|---|---:|---:|---:|---:|
| 0 | 16176 | 100,0 % | 892,8 kB | 100,0 % |
| 1 | 3912 | **24,2 %** | 235,5 kB | 26,4 % |
| 2 | 1992 | **12,3 %** | 131,6 kB | 14,7 % |
| kolizja | 4452 | 27,5 % | 268,5 kB | 30,1 % |

Cały katalog chunków urósł z 892,8 kB do **1 528,3 kB** (12 plików → 48), manifest
z 11,1 kB do **71,7 kB**. To jest cena spoczynkowa na dysku; w pamięci liczy się
zestaw rezydentny, §5.

## 3. Zmierzony błąd

Odchylenie mierzy się w **jedynym kierunku, który coś znaczy**: wierzchołki rzadszego
poziomu są podzbiorem wierzchołków LOD 0, więc odległość LOD → LOD 0 jest tożsamościowo
zerowa i nie dowodzi niczego. Liczona jest odległość **każdego wierzchołka LOD 0 od
powierzchni rzadszego poziomu**; ta powierzchnia między zachowanymi pierścieniami jest
w każdej kolumnie odcinkiem, więc punktem porównania jest interpolacja po chainage
w tej samej kolumnie (`lod.deviation_stats`). Mediana i p95 liczą się po wszystkich
wierzchołkach LOD 0 chunka, razem z zachowanymi pierścieniami — te dają zero, bo leżą
na powierzchni rzadszego poziomu.

| # | pierścienie L0/L1/L2/kol | trójkąty L0/L1/L2/kol | kB L0/L1/L2/kol | L1 maks./med. [m] | L2 maks./med. [m] | ΔV L1/L2 [%] | zapas kolizji [m] |
|---|---|---|---|---|---|---|---|
|  0 |  52 /  12 /   7 /  12 |  612 / 132 /  72 / 132 | 37,5 / 9,2 / 5,7 / 9,2 | 0,107 / 0,036 | 0,322 / 0,151 | −0,009 / −0,031 | 0,0539 |
|  1 | 147 /  37 /  20 /  42 | 1752 / 432 / 228 / 492 | 92,8 / 25,5 / 14,2 / 28,7 | 0,156 / 0,000 | 0,356 / 0,005 | −0,022 / −0,062 | 0,0599 |
|  2 | 157 /  37 /  21 /  43 | 1872 / 432 / 240 / 504 | 108,8 / 26,7 / 15,6 / 30,9 | 0,150 / 0,032 | 0,356 / 0,163 | −0,023 / −0,062 | 0,0584 |
|  3 | 129 /  30 /  15 /  31 | 1536 / 348 / 168 / 360 | 80,9 / 20,1 / 10,9 / 20,4 | 0,141 / 0,000 | 0,347 / 0,001 | −0,011 / −0,031 | 0,0539 |
|  4 | 109 /  37 /  22 /  56 | 1296 / 432 / 252 / 660 | 73,4 / 26,6 / 16,3 / 40,2 | 0,152 / 0,000 | 0,388 / 0,075 | −0,047 / −0,135 | 0,0536 |
|  5 | 104 /  31 /  18 /  37 | 1236 / 360 / 204 / 432 | 74,5 / 22,8 / 13,5 / 27,0 | 0,152 / 0,075 | **0,400** / 0,199 | −0,042 / −0,118 | 0,0537 |
|  6 |  96 /  29 /  15 /  32 | 1140 / 336 / 168 / 372 | 67,2 / 21,3 / 11,4 / 23,5 | 0,152 / 0,018 | 0,353 / 0,141 | −0,033 / −0,110 | 0,0569 |
|  7 |  85 /  23 /  13 /  27 | 1008 / 264 / 144 / 312 | 56,4 / 16,6 / 9,9 / 19,8 | 0,155 / 0,001 | 0,351 / 0,022 | −0,031 / −0,077 | 0,0592 |
|  8 | 110 /  24 /  11 /  24 | 1308 / 276 / 120 / 276 | 65,5 / 14,8 / 7,9 / 15,2 | 0,116 / 0,000 | 0,322 / 0,000 | −0,002 / −0,007 | 0,0544 |
|  9 |  93 /  20 /   9 /  20 | 1104 / 228 /  96 / 228 | 54,6 / 11,8 / 5,9 / 12,5 | **0,002** / 0,000 | **0,003** / 0,000 | −0,000 / −0,000 | 0,1485 |
| 10 | 155 /  32 /  15 /  33 | 1848 / 372 / 168 / 384 | 102,2 / 22,6 / 11,2 / 23,2 | 0,136 / 0,001 | 0,347 / 0,023 | −0,002 / −0,005 | 0,0619 |
| 11 | 123 /  26 /  12 /  26 | 1464 / 300 / 132 / 300 | 79,0 / 17,5 / 9,1 / 17,9 | 0,088 / 0,000 | 0,319 / 0,030 | −0,003 / −0,010 | 0,0643 |

Podsumowanie po pakiecie:

| wielkość | LOD 1 | LOD 2 |
|---|---:|---:|
| odchylenie maks. | **0,1564 m** | **0,4002 m** |
| p95 najgorszego chunka | 0,1417 m | 0,3417 m |
| mediana najgorszego chunka | 0,0755 m | 0,1990 m |
| objętość światła tunelu | 369 299,8 m³ (**−0,018 %**) | 369 173,7 m³ (**−0,052 %**) |
| bbox: wzrost / skurcz | 0,000 m / 0,091 m | 0,000 m / 0,091 m |
| pole przekroju | 55,24 m² (bez zmiany — obrys nietknięty) | 55,24 m² |

Trzy rzeczy, które z tych liczb widać, a które nie są oczywiste:

1. **Mediana jest o rząd–dwa rzędy mniejsza od maksimum.** Błąd nie jest rozłożony
   równomiernie: siedzi w kilku łukach, a na prostych jest zerowy. Chunk 9
   (Maelbeek–Schuman, najprostszy odcinek pakietu) ma błąd LOD 2 równy **0,003 m** —
   tam limit strzałki w ogóle nie działa, bo nie ma czego ścinać, i rządzi sama cięciwa.
2. **Objętość praktycznie się nie zmienia** (−0,05 % w najrzadszym poziomie). Cięciwa
   ścina naroże łuku po stronie zewnętrznej i wybrzusza po wewnętrznej, więc błędy
   objętościowe się znoszą. To znaczy, że **objętość jest złą metryką jakości LOD-a**
   i dobrą metryką kontrolną: jej duża zmiana oznaczałaby, że coś się wywróciło,
   a nie że poziom jest gorszy. Właściwą liczbą jest odchylenie powierzchni.
3. **Bbox nigdy nie rośnie** (0,000 m) i kurczy się najwyżej o 0,091 m, czyli poniżej
   zmierzonego błędu poziomu. Rośnięcie bboxa oznaczałoby, że interpolacja wyniosła
   powierzchnię poza LOD 0 — CI sprawdza to osobno i osobnym progiem dla obu kierunków.

### 3.1 Progi odległości — skąd się biorą

`design_assumption`, nie specyfikacja. Wzór jest jawny (`lod.switch_distance_m`):
błąd `e` widziany z odległości `d` ma rozmiar kątowy `e/d`; jeden piksel to
`hfov / szerokość`, a dla kamer wnętrza zestawu `alignment` (obiektyw 35 mm na
matrycy 36 mm, 960 px) to 9,889·10⁻⁴ rad. Próg dla poziomu = odległość, na której
zmierzone odchylenie tego poziomu schodzi poniżej **1 px**:

| poziom | odchylenie zmierzone | próg |
|---|---:|---:|
| 1 | 0,1564 m | **158 m** |
| 2 | 0,4002 m | **404 m** |

Oba mieszczą się w oknie 600 m przed składem z `docs/01-architecture.md`, więc oba
poziomy mają w tym oknie sens. **To nie jest budżet klatki** — budżet ma zostać
zmierzony na rzeczywistym sprzęcie w T-400 (`docs/20-art-direction.md` nie istnieje
w tym repo na dzień pisania). Wpis w manifeście ma `"status": "design_assumption"`
i kontrola manifestu odrzuca poziom, który tego nie ma.

## 4. Geometria kolizyjna — decyzja i uzasadnienie

Bryła reprezentuje **wnętrze tunelu** — przestrzeń, w której może się poruszać
pociąg — a nie jego ściany. Cztery decyzje, każda z pomiarem:

### 4.1 Obrys zamiatany rzadziej, nie uproszczony wielobok

`box_double` ma sześć punktów. Sprowadzenie go do prostokąta oszczędza 2 z 6 kolumn,
czyli 8 trójkątów na parę pierścieni zamiast 12 — **33 %**. Zmierzona cena:

| wariant | punkty | pole | co się psuje |
|---|---:|---:|---|
| `box_double` | 6 | 55,24 m² | — |
| prostokąt opisany | 4 | 55,46 m² (+0,4 %) | naroże stropu wychodzi **0,3235 m** poza prawdziwy obrys — bryła kolizyjna wystaje w ścianę |
| prostokąt wpisany | 4 | 51,70 m² (−6,4 %) | strop spada z 4,70 m do 4,30 m na **całej** szerokości 9,40 m |

Rzadszy krok pierścieni daje w tym samym miejscu **72,5 % oszczędności** przy błędzie
0,12 m. Cała oszczędność siedzi w kroku, nie w obrysie — więc obrys zostaje sześciopunktowy.
Wymiarów profilu nie tykam: to decyzja właściciela i R-005 (#17), a wcięcie jest
liczone w `lod.inset_polygon` z odczytanego obrysu, bez zmiany `profiles.py`.

### 4.2 Obrys wcięty o 0,15 m do środka

Cięciwa **po wewnętrznej stronie łuku** wypycha powierzchnię na zewnątrz prawdziwego
światła tunelu o co najwyżej strzałkę. Bryła kolizyjna, która wystaje w ścianę,
przepuszcza pociąg przez mur — błąd kolizji nie jest kosmetyczny, więc kierunek błędu
musi być kontrolowany. Wcięcie = strzałka (0,10 m) + zapas (0,05 m).

Zmierzone: **najmniejszy zapas do prawdziwej ściany na całym pakiecie wynosi
0,0536 m** — dokładnie tyle, ile przewiduje konstrukcja (0,15 − 0,10 + zaokrąglenia).
Kontrola negatywna w testach: ta sama bryła **bez** wcięcia daje zapas **ujemny**,
czyli pomiar naprawdę widzi przebicie ściany
(`test_collision_solid_with_no_inset_would_poke_out_negative_control`).

Wcięcie kosztuje światło, więc jest sprawdzone od drugiej strony: **skrajnia pojazdu
M7 mieści się w bryle z zapasem 0,650 m** (w pełnym profilu 0,800 m). To jest tylko
kontrola — **skrajnia pojazdu nie jest światłem tunelu i nie jest tu geometrią
kolizyjną**; `profiles.vehicle_gauge` służy do sprawdzenia, że wcięcie nie zjadło
miejsca, w którym musi się zmieścić pociąg.

Rozważone i odrzucone alternatywy, zmierzone:

| strzałka / wcięcie | trójkąty | udział LOD 0 | zapas do ściany | zapas do skrajni |
|---|---:|---:|---:|---:|
| **0,10 / 0,15 (wybrane)** | **4452** | **27,5 %** | 0,0536 m | **0,650 m** |
| 0,15 / 0,20 | 3912 | 24,2 % | 0,0514 m | 0,600 m |
| 0,25 / 0,30 | 3564 | 22,0 % | 0,0568 m | 0,500 m |
| 0,35 / 0,40 | 3432 | 21,2 % | 0,0687 m | 0,400 m |

Rozluźnienie strzałki prawie nic nie oszczędza (27,5 % → 21,2 %), bo na prostych
i tak rządzi cięciwa 25 m, a kosztuje 0,25 m światła. Wybrany jest wariant najostrzejszy.

### 4.3 Bez czapek na szwach chunków

**Świadome odstępstwo od dosłownego „zamknięta bryła" i najważniejsza decyzja tego
kroku.** Zamknięcie każdego chunka czapkami na obu końcach dałoby bryłę domkniętą
w sensie rozmaitości — i postawiłoby **niewidzialną ścianę w poprzek toru na każdym
z 11 szwów**, czyli dokładnie tam, gdzie pociąg jedzie. Kolizja jest potrzebna
widokowi kabiny i obiektom w tunelu (§7.3 `reports/L1_A-chunks.md`), więc ściana
co pół kilometra jest defektem, a nie cechą.

Co jest zamiast tego i co jest zmierzone:

- **zamknięcie poprzeczne**: po sklejeniu zdublowanej kolumny szwu UV (`lod.weld`)
  krawędzi brzegowych jest **dokładnie 12 = 2 × 6**, czyli tylko obwody dwóch
  pierścieni końcowych, i wszystkie leżą na tych pierścieniach. Każdy przekrój
  jest domkniętą pętlą — bokiem nie da się wyjść;
- **szczelność sumy po chunkach**: sąsiednie bryły dzielą pierścień szwu, zmierzona
  szczelina **0,0000 mm** na wszystkich 11 szwach;
- **objętość**: liczona na kopii domkniętej wirtualnymi czapkami (`lod.tube_volume_m3`),
  bo bez domknięcia objętość nie jest zdefiniowana. Czapki **nie trafiają do eksportu**.
  Wynik: 339 735,9 m³, czyli **91,98 % światła tunelu** — cała różnica to wcięcie
  obrysu (50,81 / 55,24 m² = 91,98 %), nie krok pierścieni. Poprawność wzoru pilnuje
  test na prostej rurze o znanej objętości (pole × długość, zgodność do 1e-9).

Manifest zapisuje to jawnie: `"end_caps": false`, `"transversally_closed": true`,
`"boundary_edges": 12`. Jedynymi prawdziwymi otworami są końce pakietu (0 m
i 6686,74 m) — tam tunel po prostu biegnie dalej, w pakiet B.

### 4.4 Osobny plik, nie nazwany obiekt w GLB LOD-a

Kolizja jest **jedna na chunk**, a LOD-ów jest trzy. W pliku LOD-a musiałaby albo
istnieć trzy razy (marnotrawstwo i ryzyko rozjazdu wersji między poziomami), albo
tylko w LOD 0 — a wtedy **rezydencja fizyki zależałaby od decyzji o rozdzielczości
obrazu**. To jest sprzężenie, którego się nie chce: kolizja ma być wczytana, bo
pociąg jest blisko, a nie dlatego, że kamera akurat rysuje ten chunk w pełnej
rozdzielczości. Stąd `{chunk_id}_col.glb` obok `{chunk_id}.glb`,
`{chunk_id}_lod1.glb` i `{chunk_id}_lod2.glb`.

Normalne idą **do wnętrza**, tak samo jak w siatce wizualnej: kolizja typu trimesh
z wyłączonymi tylnymi ścianami blokuje tylko od strony lica, a pociąg jest w środku.
To jest **założenie implementacyjne o Godocie, do potwierdzenia w T-4xx**, nie fakt
udokumentowany w tym repo. Zmierzone: `outward_faces = 0` we wszystkich 12 bryłach.

## 5. Manifest i predykaty

`schema_version` podbity z **1 na 2**. Pola schematu 1 (`file`, `vertices`, `faces`,
`triangles`, `sha256`, `bytes`, `geometry_sha256`, `bbox_*`) **zostają nietknięte
i nadal opisują LOD 0**, więc `sweep.chunks_for_train`, `sweep.streaming_plan`
i `sweep.manifest_problems` działają bez żadnej zmiany i bez świadomości LOD-ów.
Dochodzi:

| klucz | gdzie | co niesie |
|---|---|---|
| `lod_levels` | nagłówek | parametry, koszt i błąd każdego poziomu, próg odległości, `status: design_assumption` |
| `streaming.lod_predicate` | nagłówek | wskaźnik na `lod.lod_plan` |
| `streaming.collision_predicate`, `collision_radius_m` | nagłówek | wskaźnik na `lod.collision_plan` i promień 150 m (`design_assumption`) |
| `lods` | wpis chunka | trzy wpisy z plikiem, licznikami, bboxem, hashami i **zmierzonym** błędem oraz objętością |
| `collision` | wpis chunka | plik, liczniki, wcięcie, zamknięcie poprzeczne, objętość, zapas do ściany i do skrajni |

`sweep.deterministic_view` czyści teraz także zagnieżdżone `lods` i `collision`
z `sha256` i `bytes` — każdy z tych plików niesie własny nieodtwarzalny odcisk,
a bajty GLB nie są odtwarzalne (ustalony fakt projektu, PR #44). Odtwarzalna jest
geometria i to sprawdza `geometry_sha256`. Zmierzone w tym przebiegu:
**geometria identyczna w 12/12 chunkach.**

### 5.1 Dlaczego wybór LOD-a to osobny predykat

`chunks_for_train` zostaje bez zmiany. LOD liczy **osobne** `lod.lod_plan`, bo to są
dwa różne pytania:

- **rezydencja** („czy plik jest w pamięci") zależy od chainage i zmienia się skokowo
  na granicach chunków;
- **rozdzielczość** („którą siatkę pokazać") zależy od odległości do kamery i zmienia
  się w sposób ciągły.

Wsadzenie LOD-a do predykatu okna zmusiłoby do przeładowania chunka, który **jest już
rezydentny**, tylko dlatego że zmienił się dystans — a to jest dokładnie ta operacja,
której streaming ma unikać. `lod_plan` bierze listę rezydentną z niezmienionego
`chunks_for_train` i dokłada do niej poziom, więc jest jedno źródło prawdy o pamięci
i osobne o rozdzielczości.

Niezmiennik, który z tego wypada i jest sprawdzany na całym przejeździe: **chunk,
w którym stoi pociąg, ma odległość 0, więc zawsze jest w LOD 0** — i zawsze ma
wczytaną bryłę kolizyjną.

Przykład na chainage 3200 m:

```
okno  (chunks_for_train) -> c04, c05, c06
LOD   (lod_plan)         -> c04: 1, c05: 0, c06: 1
kolizja (collision_plan) -> c05
```

### 5.2 Ile to naprawdę oszczędza na pakiecie A — uczciwie

| wielkość, szczyt na przejeździe | bez LOD | z LOD |
|---|---:|---:|
| trójkąty rezydentne | 5160 | **3660 (70,9 %)** |
| bajty rezydentne (z kolizją) | 282 556 B | **261 256 B (92,5 %)** |
| bryły kolizyjne naraz | — | 2 z 12 |

**To jest mało i trzeba to powiedzieć wprost.** Powód jest arytmetyczny: okno ma
900 m, chunki mają 250–775 m, więc rezydentne są najwyżej 3–4 chunki, a ten pod
pociągiem — z definicji największy udział — jest zawsze w LOD 0. Przy 16 176
trójkątach na całe 6,7 km pustej rury LOD nie zwraca się sam z siebie. Zwróci się,
gdy chunk zacznie nieść torowisko, wyposażenie, oświetlenie i trzecią szynę, i gdy
okno urośnie — a wtedy mechanizm, progi i pomiar błędu już będą, zmierzone.

## 6. Kontrole automatyczne

Wszystko dopięte do `tools/ci/tunnel_alignment.sh`, blok `[LOD]`.

| kontrola | narzędzie | wynik na pakiecie A |
|---|---|---|
| liczniki i bbox każdego poziomu | metryki generatora + manifest | 16176 / 3912 / 1992 trójkątów |
| bbox nie rośnie; kurczy się nie więcej niż błąd poziomu | `lod_max_bbox_growth_m`, `lod_max_bbox_shrink_m` | wzrost 0,000 m, skurcz 0,091 m < 0,400 m |
| brak NaN/Inf i degeneracji w **każdym** poziomie | `sweep.non_finite`, `sweep.degenerate_faces` | 0 / 0 |
| normalne do wnętrza w **każdym** poziomie i w kolizji | `sweep.outward_faces` | 0 / 0 |
| szczelina na szwie **w każdym poziomie osobno i w każdej parze poziomów** | `sweep.chunk_gap_m`, 9 par | **0,0000 mm** |
| szczelina na szwie brył kolizyjnych | `sweep.chunk_gap_m` | **0,0000 mm** |
| bryła kolizyjna zamknięta poprzecznie | `lod.transversally_closed` | 12/12, 12 krawędzi brzegowych z 12 oczekiwanych |
| bryła kolizyjna nie wystaje poza światło tunelu | `lod.wall_margin_m` | min **+0,0536 m** |
| bryła kolizyjna mieści skrajnię M7 na obu torach | `lod.gauge_margin_m` | min **+0,650 m** |
| kolizja tańsza od siatki wizualnej | `lod.lod_problems` | 4452 < 16176 |
| każdy poziom tańszy od poprzedniego, każdy o większym błędzie | `lod.lod_problems` | OK |
| każdy poziom ma ten sam zakres chainage co chunk | `lod.lod_problems` | OK |
| każdy plik LOD-a i kolizji: istnieje, magic `glTF`, rozmiar i sha256 | `check_meshes` w CI | 48/48 |
| **negatyw:** przekręcony bajt w pliku LOD 2 musi zostać wykryty | `check_meshes` na kopii | wykryty |
| **negatyw:** zepsuty manifest (kolizja w ścianie, przesunięty zakres LOD-a) | `lod.lod_problems` | wykryty |
| round-trip GLB LOD 1, LOD 2 i kolizji | `tools/blender/glb_roundtrip.py` × 3 | OK, `obiekty=1`, bbox zgodny |
| determinizm poza sha256 plików, z zagnieżdżonymi `lods`/`collision` | `sweep.deterministic_view` | identyczny |
| determinizm geometrii | `geometry_sha256` | 12/12 identyczne |
| predykat: chunk pod pociągiem zawsze w LOD 0, zawsze z kolizją | `lod.lod_plan`, `lod.collision_plan`, przejazd co 25 m | 268 kroków, 0 problemów |
| plan LOD oszczędza trójkąty wobec pełnej rozdzielczości | `lod.lod_triangles` | 3660 < 5160 |
| **metryka renderu:** LOD 2 musi mieć rzadszą siatkę niż LOD 0 | `tools/visual/compare.py`, `ink_fraction` | −51 % do −64 % na czterech kamerach wnętrza |

Testy jednostkowe: `tools/tests/test_lod.py`, **50 testów** bez Blendera i bez pytest —
wybór pierścieni, oba limity i ich rozdział, monotoniczność poziomów, pomiar błędu
i jego kierunek, objętość prostej rury o znanej wartości, bbox, szew między każdą
parą poziomów, wcięcie obrysu, skrajnia M7, zamknięcie poprzeczne, sklejanie kolumny
szwu UV, predykaty LOD i kolizji, zgodność `build_chunk` z nowym budowniczym
podzbiorów oraz **czternaście negatywów** manifestu. Cały zestaw: **259/259 przeszło**
(50 nowych).

## 7. Oględziny renderów

Renderowany chunk: **`L1_A_flat_preview_c05`**, 2923,5–3433,3 m, De Brouckère.
Ten sam chunk, te same kotwice kamer, ta sama kamera — jedyną zmienną jest siatka.
`CHUNK_*` to dosłownie plik LOD 0 (`c05.glb`), `LOD2_*` to `c05_lod2.glb`,
`COL_*` to `c05_col.glb`. Siatka drutowa włączona dla kamer wnętrza i przekroju:
bez niej wnętrze rury jest jednolicie szare i nie widać, gdzie stoją pierścienie,
a właśnie one są tu treścią.

- **`CHUNK_axis25` (LOD 0)** — wnętrze prostokątnego tunelu z wysokości oczu
  maszynisty. Gęsta drabina pierścieni biegnie regularnie do punktu zbiegu, ściany,
  strop i płyta denna widoczne **od wewnątrz**, linia stropu i linia posadzki poziome
  na całej głębi. Wyraźny łuk w prawo — pierścienie po wewnętrznej stronie łuku
  są ciaśniejsze. Brak szczelin, brak zanikających sekcji.
- **`LOD2_axis25` (LOD 2)** — **ten sam korytarz, ta sama sylwetka, ta sama pozycja
  odległego otworu, ale drabiny pierścieni nie ma**. Zamiast kilkudziesięciu
  poprzeczek widać trzy–cztery; między nimi ściana jest jedną długą, płaską taflą.
  W kadrze bliskim wielobok jest tak duży, że jego krawędzie przecinają cały ekran
  po przekątnych i to one dominują obraz. Na wysokości ok. jednej trzeciej głębi
  widać **załamanie ściany** — miejsce, gdzie stoi zachowany pierścień i gdzie
  fasetowana rura zmienia kierunek skokowo zamiast płynnie. Dokładnie to opisuje
  liczba 0,400 m: łuk jest cięty cięciwami, nie wygładzony.
- **`CHUNK_axis50` vs `LOD2_axis50`** — to samo w środku chunka. W LOD 0 korytarz
  ciągnie się do punktu zbiegu bez przewężeń; w LOD 2 widać dwa–trzy segmenty i jasny
  klin na płycie dennej po prawej, czyli długi czworokąt łapiący światło jednolicie
  na całej długości zamiast stopniowo. **Nie widzę** ani dziury, ani wywróconej ściany,
  ani zanikającej sekcji.
- **`CHUNK_plan` vs `LOD2_plan`** — dwie wstęgi praktycznie nie do odróżnienia:
  ten sam łuk w prawo, ten sam prosty środek, to samo odgięcie w dół na końcu, ta sama
  stała szerokość na całej długości. Fasetowanie jest w tej skali niewidoczne. To jest
  wizualny odpowiednik liczby „bbox nie urósł i objętość zmieniła się o 0,05 %":
  **rzadszy LOD nie przesuwa trasy**, zmienia tylko lokalną gładkość.
- **`LOD2_section`** — obrys prostokąta wyraźnie szerszego niż wyższego, z widocznymi
  ścięciami obu górnych naroży. **Identyczny w kształcie z przekrojem LOD 0** —
  potwierdzenie, że obrys profilu nie jest w LOD-zie upraszczany, upraszczany jest
  wyłącznie krok wzdłuż osi.
- **`COL_section`** — ten sam kształt: prostokąt ze ściętymi górnymi narożami,
  proporcja zgodna z 9,10 × 5,60 m (czyli 9,40 × 5,90 m wciętym o 0,15 m z każdej
  strony). Ściany boczne oświetlone, wnętrze ciemne — patrzymy w rurę, nie na bryłę.
- **`COL_axis50`** — bryła kolizyjna od wewnątrz. Drabina pierścieni gęstsza niż
  w LOD 2 i rzadsza niż w LOD 0, zgodnie z ostrzejszym limitem strzałki. Ściany,
  strop i płyta denna widoczne od wewnątrz (normalne poprawne). **Widać na wylot do
  końca chunka — nie ma czapki zamykającej przekrój**, czyli to, co §4.3 opisuje
  słowami, jest widoczne na klatce.

Automat obok oględzin, nie zamiast nich: `ink=0,030..0,050`, `luma_std=0,027..0,038`,
`poziomy=176..188` dla kamer wnętrza LOD 2 i kolizji — żadna klatka nie jest pusta
ani jednolita. Dodatkowo CI wymaga, żeby **tusz siatki drutowej LOD 2 był mniejszy
niż LOD 0** na wszystkich czterech kamerach wnętrza (zmierzone −51 % do −64 %);
gdyby był taki sam, renderowałby się nie ten plik. **Ta metryka nie zastępuje
obejrzenia PNG** i nie zastąpiła.

## 8. Założenia projektowe dołożone w tym kroku

| założenie | wartość | uzasadnienie |
|---|---|---|
| `design_assumption` — parametry LOD 1 | cięciwa ≤ 25 m, strzałka ≤ 0,15 m | dobrane tak, żeby próg 1 px wypadł ok. 150 m, czyli dobrze wewnątrz okna 600 m |
| `design_assumption` — parametry LOD 2 | cięciwa ≤ 60 m, strzałka ≤ 0,35 m | jw., próg ok. 400 m; przy strzałce 0,60 m próg wychodzi 678 m, czyli poza okno |
| `design_assumption` — budżet błędu ekranowego | 1 px przy 960 px i obiektywie 35 mm | parametry kamer wnętrza zestawu `alignment`; **do zastąpienia pomiarem w T-400** |
| `design_assumption` — strzałka kolizji | 0,10 m | błąd kolizji nie jest kosmetyczny, więc ostrzej niż w LOD 1 |
| `design_assumption` — wcięcie obrysu kolizji | 0,15 m = strzałka + 0,05 m | gwarantuje, że bryła jest w całości wewnątrz światła tunelu; zmierzony zapas +0,0536 m |
| `design_assumption` — promień rezydencji kolizji | 150 m | długość składu M7 94,0 m (`data/vehicle/m7-spec.json`) z zapasem po obu stronach |
| decyzja implementacyjna — LOD jako podzbiór ramek | — | inny `--ring-step` przesuwałby granice chunków i otwierał dziurę na szwie |
| decyzja implementacyjna — kolizja w osobnym pliku | — | kolizja jest jedna na chunk, LOD-ów trzy; inaczej fizyka zależałaby od rozdzielczości obrazu |
| decyzja implementacyjna — brak czapek na szwach | — | czapka = niewidzialna ściana w poprzek toru na każdym z 11 szwów |
| założenie o Godocie — normalne do wnętrza dla trimesh | — | `backface_collision` domyślnie wyłączone; **do potwierdzenia w T-4xx** |

Nic z tego nie jest twierdzeniem o metrze brukselskim i nic nie zmienia `data/`.

## 9. Czego to NIE rozwiązuje dla Godota

1. **Ziarno LOD-a równa się ziarnu chunka.** Chunk c02 ma 775 m. Jeśli jego bliższy
   koniec jest 10 m od pociągu, cały chunk — łącznie z fragmentem oddalonym o 785 m —
   dostaje LOD 0. Prawdziwy LOD ciąłby po odległości, nie po pliku. Wymagałoby to
   dzielenia chunków na podsegmenty albo LOD-a per pierścień, czego ten generator
   nie robi.
2. **Nie ma histerezy ani przenikania.** Poziom przełącza się skokowo na progu, więc
   skład drgający wokół 158 m będzie przeskakiwał LOD 0 ↔ LOD 1 w kółko — ten sam
   problem, który §7.1 `reports/L1_A-chunks.md` opisuje dla rezydencji. Nie ma
   `distance_hysteresis`, nie ma dithered fade, nie ma budżetu czasu na podmianę siatki.
3. **Progi nie są zmierzonym budżetem klatki.** Są przeliczeniem zmierzonego błędu
   geometrycznego na błąd ekranowy przy jawnie podanych parametrach kamery. Ile
   trójkątów naprawdę wolno, powie dopiero T-400 na rzeczywistym sprzęcie.
4. **Nie ma impostora ani żadnego poziomu „bilbord".** Najrzadszy poziom to nadal
   pełna rura o poprawnym przekroju. Dla chunka widocznego z 2 km przez prostą to
   wciąż za dużo.
5. **Nie ma `LOD`/`VisualInstance3D.lod_bias` po stronie sceny.** Manifest podaje
   pliki i progi; nikt ich jeszcze nie podpina do węzła Godota. Predykaty są w Pythonie
   i są przepisywalne 1:1 na GDScript, ale nie są przepisane — to zadanie z serii T-4xx.
6. **Kolizja nie ma warstw, masek ani materiału fizycznego.** Jest jedna bryła na
   chunk, bez rozróżnienia płyty dennej, ścian i stropu, bez `physics_material`,
   bez oznaczenia, co jest podłożem, po którym da się chodzić.
7. **Konwencja importu kolizji w Godocie nie jest w tym repo potwierdzona.** Plik
   nazywa się `_col.glb`, obiekt w środku `..._col`; czy Godot ma to podnieść przez
   sufiks nazwy (`-col`/`-colonly`), przez `ImporterMeshInstance3D`, czy przez skrypt
   importu, jest **decyzją T-4xx**, nie faktem tego kroku.
8. **Kolizja jest LOD-owa tylko w jednym poziomie.** Nie ma osobnej, grubszej bryły
   dla chunków dalekich — bo dla chunków dalekich kolizja po prostu nie jest wczytywana
   (promień 150 m). Gdyby okazało się, że fizyka potrzebuje zasięgu większego niż
   okno kolizji, trzeba będzie dorobić drugi poziom kolizji.
9. **Nic z tego nie dotyczy stacji, torowiska ani wyposażenia.** Zdanie „bo tej
   geometrii nadal nie ma" jest tu **sprostowane 05.09.2026, a nie dopisane obok**:
   geometria peronów powstała w T-212 (`tools/blender/station_kit.py`) i jest
   w scenie od #223 (`src/Game/World/StationView.cs`) — jako **osobny GLB obok
   chunków**, więc nie wchodzi do tej tabeli LOD-ów i nie ma dla niej poziomów.
   Prawdziwa zostaje druga połowa: **chunk ze stacją jest w każdym poziomie zwykłą
   rurą**, bo halo stacji w `tools/blender/sweep.py` wpływa wyłącznie na miejsce
   cięcia chunka, a nie na profil przekroju.
10. **Profil pionowy dalej nie istnieje** (T-112, #10). Wszystko leży na Z = 0, więc
    bbox nie odpowiada na pytania o głębokość, a błąd LOD-a jest zmierzony wyłącznie
    w planie — na trasie z pochyleniami dojdzie składowa pionowa, której tu nie ma.

## 10. Czego świadomie nie zrobiłem

- **nie ruszyłem `tools/visual/cameras.json`, `tools/visual/framing.py`,
  `tools/visual/capture_blender.py`, `tools/blender/render_check.py`,
  `tools/blender/placement.py`, `docs/17-visual-regression.md`** — praca równoległa;
  rendery LOD-a i kolizji idą istniejącym zestawem `alignment` i istniejącym
  mechanizmem `--anchor`;
- **nie ruszyłem `tools/blender/profiles.py`** — wymiary profilu to decyzja właściciela
  i R-005 (#17). Wcięty obrys kolizji jest **wyprowadzony** w `lod.inset_polygon`
  z odczytanego `box_double`, a nie zapisany jako nowy profil;
- **nie ruszyłem `tools/track/**` ani `data/network/sources.json`**;
- **nie dodałem czwartego poziomu ani impostora** — trzy poziomy plus kolizja to tyle,
  ile da się obronić pomiarem na pustej rurze;
- **nie dodałem histerezy przełączania** — to decyzja o zachowaniu w czasie, a nie
  o geometrii, i należy do węzła streamującego w Godocie (§9.2);
- **nie zmieniłem `chunks_for_train` ani schematu pól LOD 0** — stary manifest ma
  dalej działać, a stare kontrole mają dalej znaczyć to samo;
- **nie chunkowałem LOD-ów wariantu wiernego (`--ring-step 0`)** — ten sam kod, ten
  sam podział, dłuższy pipeline bez nowej informacji;
- **nie skomitowałem żadnego GLB, PNG ani manifestu** — reguła 8 z `CLAUDE.md`.

## 11. Zauważone przy okazji, nietknięte

- ~~**`docs/20-art-direction.md` nie istnieje** w tym repo, choć zadanie się na niego
  powołuje jako na miejsce, gdzie mają wylądować budżety T-400.~~ **Ten punkt jest
  przepisany, a nie dopisany obok: dokument istnieje** (`docs/20-art-direction.md`).
  Progi zostały opisane w manifeście i w tym raporcie i nadal tam są; przeniesienie
  ich do `docs/20` jest osobną robotą i ten raport jej nie wykonał.
- ~~**`tools/visual/capture_blender.py` w `main` nie ma logu `[POKRYCIE]`** ani
  automatycznego liczenia kotwic w zakresie wczytanej geometrii — kotwice trzeba
  podawać jawnie przez `--anchor`.~~ **Też przepisane: log jest.**
  `tools/visual/capture_blender.py:190` wypisuje `[POKRYCIE] geometria zajmuje
  chainage …`, a `named_anchors_from_args` liczy kotwice z ułamków osi, gdy
  `--anchor` nie podano. Zdanie „w `main` nie ma" było prawdą 01.09.2026 i nie
  przestało wyglądać na prawdę, bo nic go z kodem nie porównywało. Rendery LOD-a
  w tym raporcie nadal korzystają z jawnie policzonych kotwic — to zostaje faktem
  o tym pomiarze, niezależnie od tego, co potrafi dzisiejsze narzędzie.
- **`switch_distance_m` dla poziomu 0 wychodzi 0 m** i jest tak zapisane w manifeście.
  Czytelnik może to wziąć za „LOD 0 obowiązuje od 0 m", co jest prawdą, ale wygląda
  jak brakująca wartość. Zostawione, bo alternatywą jest `null`, którego kontrola
  monotoniczności progów nie umiałaby porównać.
- **Chunk 9 ma błąd LOD 2 równy 0,003 m**, czyli praktycznie zero, bo Maelbeek–Schuman
  jest prosty. Na takich odcinkach cięciwa mogłaby być znacznie dłuższa niż 60 m bez
  żadnej straty — limit cięciwy jest tam narzutem, nie ochroną. Nie tknięte, bo dłuższe
  czworokąty psują granulację frustum cullingu, a tego nie ma jak zmierzyć bez Godota.
- **Kolizja jest droższa od LOD 1** (4452 wobec 3912 trójkątów) i to jest zamierzone:
  ma ostrzejszy limit strzałki, bo jej błąd nie jest kosmetyczny. Wygląda to jednak
  jak anomalia w tabeli i warto o tym pamiętać przy czytaniu.
