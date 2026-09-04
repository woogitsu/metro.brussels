# T-210 — eksport per chunk i manifest streamingowy pakietu A

**Zmierzone na commicie:** `51fd842` · **data:** 2026-09-01

Wariant: **`flat-preview`, nieprodukcyjny** — jak w `reports/L1_A-geometry.md`. Oś
`data/track/L1_A.json` ma `vertical.status = "not_modelled"`, cała geometria leży na Z = 0,
generator odmawia wariantu `production` do zamknięcia T-112 (#10).

## 0. Po co to jest

Wymaganie 4 z #12 mówiło, że segmentacja ma umożliwiać streamowanie w Godot. Chunki
istniały jako 12 **osobnych obiektów wewnątrz jednego pliku GLB** — a Godot i tak
wczytuje plik całością, czyli 6,7 km tunelu naraz. To nie jest streaming, tylko podział
sceny. Streaming potrzebuje dwóch rzeczy, których nie było: **osobnych plików** i
**indeksu po chainage**, z którego da się w czasie rzeczywistym odpowiedzieć, co
wczytać i co zwolnić.

Zmierzona różnica na pakiecie A, przy oknie 600 m przed składem i 300 m za nim
(`docs/01-architecture.md`):

| | jeden GLB | 12 plików + manifest |
|---|---|---|
| minimalny rezydentny zestaw | 867,1 kB (całość) | **275,9 kB** (najgorszy przypadek okna) |
| chunków w pamięci naraz | 12 z 12 | **maks. 4 z 12** |
| wczytań na przejazd 6,7 km | 1 × całość | 12 pojedynczych chunków |
| narzut na duplikaty pierścieni szwu | — | +4,8 kB (+0,5 %) |

Ten sam podział, te same 16176 trójkątów, te same szwy w połowie odległości między
stacjami. Zmienia się tylko granulacja wczytywania — i to jest cała rzecz.

## 1. Uruchomienie

```bash
blender --background --python-exit-code 7 --python tools/blender/tunnel_sweep.py -- \
  --centerline data/track/L1_A.json --profile box_double --name L1_A \
  --out build/t210/L1_A.glb --metrics build/t210/L1_A-metrics.json \
  --chunk-dir build/t210/chunks --chunk-manifest build/t210/chunks/L1_A-chunks.json
```

`--chunk-dir` jest **dodatkiem**, nie zamiennikiem: pojedynczy `--out` powstaje jak
wcześniej, bo jest wejściem renderów kontrolnych i baseline'u T-012. Stare wywołania
z `tools/ci/blender_smoke.sh` i `tools/ci/visual_smoke.sh` (bez `--chunk-dir`) działają
bez zmian — sprawdzone przez uruchomienie obu skryptów.

Pełny pipeline kontrolny: `bash tools/ci/tunnel_alignment.sh` (~62 s, Blender 4.0.2).
Nic z `build/` ani `renders/` nie jest komitowane — manifest ma powstawać z generatora.

## 2. Schemat manifestu

`schema_version: 1`, JSON z `sort_keys=True` i `indent=2`, więc diff jest czytelny.
Plik przykładowy dla pakietu A ma 11 098 B.

### Nagłówek

| klucz | typ | znaczenie |
|---|---|---|
| `schema_version` | int | wersja schematu manifestu (`sweep.CHUNK_MANIFEST_SCHEMA_VERSION`) |
| `generator` | str | narzędzie, które to wyprodukowało |
| `id` / `name` | str | `L1_A` / nazwa wariantu w scenie (`L1_A_flat_preview`) |
| `variant` | str | `flat-preview` albo `production` |
| `production_ready` | bool | `false` dopóki T-112 nie da profilu pionowego |
| `profile`, `profile_size_m` | str, [w, h] | `box_double`, 9,40 × 5,90 m |
| `units`, `up_axis` | str | `m`, `Z` — 1 jednostka = 1 metr (`docs/04-conventions.md`) |
| `axis_length_m` | float | 6686,739 m |
| `chunk_count`, `chunk_length_sum_m` | int, float | 12, 6686,739 m |
| `station_count` | int | 12 |
| `totals` | obj | `vertices` 9520, `faces` 8088, `triangles` 16176 |
| `bbox_min_m`, `bbox_max_m` | [x,y,z] | bbox całego pakietu |
| `streaming` | obj | domyślne okno, źródło założenia, wskaźnik na predykat, lista pól nieodtwarzalnych |
| `chunks` | lista | wpisy poniżej, posortowane po `start_m` |

### Wpis chunka

| klucz | typ | znaczenie |
|---|---|---|
| `id`, `index`, `file` | str, int, str | `L1_A_flat_preview_c05`, 5, `L1_A_flat_preview_c05.glb` |
| `start_m`, `end_m`, `length_m` | float | zakres chainage; `end_m` chunka *n* == `start_m` chunka *n+1* co do 1e-6 m |
| `rings` | int | pierścienie siatki, łącznie ze wspólnym pierścieniem szwu |
| `bbox_min_m`, `bbox_max_m`, `bbox_size_m` | [x,y,z] | bryła chunka w metrach — do zapytań przestrzennych i frustum culling |
| `vertices`, `faces`, `triangles` | int | liczniki **generatora**; sumują się do `totals` |
| `geometry_sha256` | str | odcisk samej siatki (wierzchołki + UV + ściany) |
| `sha256`, `bytes` | str, int | odcisk i rozmiar **pliku GLB** — jedyne pola nieodtwarzalne |
| `stations` | lista | `{name, chainage_m}` stacji leżących w tym chunku |

`vertices` w manifeście to liczniki generatora, **nie** liczniki z GLB: eksporter glTF
rozszczepia wierzchołki na szwach UV, więc w pliku jest ich więcej (np. c00: 364 wobec
1016 po ponownym imporcie). Liczniki generatora sumują się do metryk co do jedności,
liczniki GLB nie — dokładnie ta pułapka jest ustalona w PR #44.

### Nazwy plików

`{name}_c{index:02d}.glb`, gdzie `name` niesie wariant. Nazwa jest funkcją wariantu
i indeksu chunka, więc jest **stabilna między przebiegami** i da się ją trzymać
w ścieżkach scen Godota. `flat_preview` w nazwie jest celowe: plik podglądowy ma się
nazywać podglądowym, tak samo jak obiekt w scenie i wariant w metrykach.

## 3. Predykat okna — sedno zadania

`tools/blender/sweep.py`, czysty Python, bez bpy, testowalny gołym `python3`
i przepisywalny 1:1 na GDScript:

```python
stream_window(chainage_m, radius_m=None, ahead_m=None, behind_m=None, heading=1.0)
chunks_in_range(manifest, low_m, high_m)
chunks_for_train(manifest, chainage_m, radius_m=None, ahead_m=None, behind_m=None, heading=1.0)
streaming_plan(manifest, chainage_m, loaded_ids, ...) -> {"load", "keep", "free"}
```

Decyzje, które są w tym zaszyte i warto je znać:

- **przedział domknięty z obu stron.** Pociąg dokładnie na szwie dostaje *oba* chunki.
  Nadmiarowy chunk kosztuje pamięć, brakujący daje dziurę w tunelu pod pociągiem.
- **`heading` zamiast bezwzględnych kierunków.** `ahead` leży po stronie jazdy, więc
  ten sam manifest obsługuje oba kierunki pakietu A bez odwracania chainage.
- **`streaming_plan` zwraca trzy listy, nie zbiór.** Pętla w Godocie nie ma przeliczać
  różnicy zbiorów w każdej klatce; dostaje gotowe `load` / `keep` / `free`.
- **domyślne 600/300 m to `design_assumption`**, nie fakt o metrze brukselskim —
  wartość pochodzi z `docs/01-architecture.md` i jest w manifeście oznaczona
  `"status": "design_assumption"`. Predykat przyjmuje dowolne liczby.

Przykłady na pakiecie A:

```
chunks_for_train(manifest, 3200.0)              -> c04, c05, c06     (okno 2900..3800 m)
chunks_for_train(manifest, 3200.0, 150.0)       -> c05               (okno 3050..3350 m)
chunks_for_train(manifest, 400.0, 0.0)          -> c00, c01          (szew, oba)
```

## 4. Tabela chunków

Granice idą w połowie odległości między sąsiednimi stacjami, więc **żadna stacja nie
leży na szwie** — to warunek streamowania z #12. Podział jest ten sam co w T-210;
nowe są kolumny plików i liczników.

| # | plik | od [m] | do [m] | dług. [m] | pierśc. | wierzch. | trójkąty | GLB [kB] | stacja w chunku |
|---|---|---|---|---|---|---|---|---|---|
| 0 | `..._c00.glb` | 0,00 | 254,88 | 254,88 | 52 | 364 | 612 | 36,6 | Gare de l'Ouest / Weststation |
| 1 | `..._c01.glb` | 254,88 | 979,52 | 724,64 | 147 | 1029 | 1752 | 90,6 | Beekkant |
| 2 | `..._c02.glb` | 979,52 | 1754,15 | 774,63 | 157 | 1099 | 1872 | 106,3 | Étangs Noirs / Zwarte Vijvers |
| 3 | `..._c03.glb` | 1754,15 | 2388,85 | 634,70 | 129 | 903 | 1536 | 79,0 | Comte de Flandre / Graaf van Vlaanderen |
| 4 | `..._c04.glb` | 2388,85 | 2923,54 | 534,69 | 109 | 763 | 1296 | 71,6 | Sainte-Catherine / Sint-Katelijne |
| 5 | `..._c05.glb` | 2923,54 | 3433,26 | 509,72 | 104 | 728 | 1236 | 72,7 | De Brouckère |
| 6 | `..._c06.glb` | 3433,26 | 3903,02 | 469,76 | 96 | 672 | 1140 | 65,6 | Gare Centrale / Centraal Station |
| 7 | `..._c07.glb` | 3903,02 | 4317,81 | 414,79 | 85 | 595 | 1008 | 55,1 | Parc / Park |
| 8 | `..._c08.glb` | 4317,81 | 4857,57 | 539,76 | 110 | 770 | 1308 | 64,0 | Arts-Loi / Kunst-Wet |
| 9 | `..._c09.glb` | 4857,57 | 5312,36 | 454,79 | 93 | 651 | 1104 | 53,3 | Maelbeek / Maalbeek |
| 10 | `..._c10.glb` | 5312,36 | 6077,02 | 764,65 | 155 | 1085 | 1848 | 99,8 | Schuman |
| 11 | `..._c11.glb` | 6077,02 | 6686,74 | 609,72 | 123 | 861 | 1464 | 77,1 | Merode |
| | **suma** | | | **6686,74** | | **9520** | **16176** | **872,0** | **12 stacji** |

Chainage Merode w `data/track/L1_A.json` to **6686,35 m** — dokładnie `length_m` osi.
Merode leży więc wewnątrz osi, a nie za jej końcem. Przycięcie chainage do osi
w `sweep.stations_by_chunk` zostaje jako zabezpieczenie, nie jako obejście: stacja
spoza końca osi **nie może wypaść z manifestu**, bo Godot nie zobaczyłby peronu
ostatniej stacji. Jest na to test
(`test_chunk_station_beyond_the_axis_end_is_clamped_not_dropped`).

Do #86 (`4a03982`, 02.09.2026) ten akapit mówił, że chainage Merode to 6686,99 m i że
stacja wypada **za** końcem osi — kilometraż stacji brał się wtedy z łamanej źródłowej,
sprzed przepróbkowania. Tabela chunków wyżej jest sprzed tej poprawki i **nie jest
przeliczona**: #86 nie tknęło `points` ani `length_m`, więc granice chunków, sumy
trójkątów i `6686,74 m` w wierszu sumy zostają tym, co zmierzył ten przebieg.

## 5. Kontrole automatyczne

Wszystkie dopięte do `tools/ci/tunnel_alignment.sh`, blok `[CHUNKI]`.

| kontrola | narzędzie | wynik na pakiecie A |
|---|---|---|
| suma długości chunków == długość osi | `sweep.manifest_problems` | 6686,739 m == 6686,739 m |
| zakresy chainage stykają się bez dziur i zakładek (tol. 1e-6 m) | `sweep.manifest_problems` | 11 szwów, 0 problemów |
| liczniki sumują się do `totals` i do metryk generatora | manifest + `L1_A-chunked-metrics.json` | 9520 / 8088 / 16176 |
| każdy plik istnieje, ma magic `glTF`, rozmiar i sha256 z manifestu | `check_files` w CI | 12/12, 892 756 B |
| **negatyw:** przekręcony bajt w chunku musi zostać wykryty | `check_files` na kopii | wykryty, `sha256 nie zgadza się z manifestem` |
| każdy chunk da się zaimportować w Blenderze | `tools/blender/glb_roundtrip.py` × 12 | 12/12 OK, `obiekty=1`, bbox zgodny |
| żadna stacja na granicy chunka | `sweep.splits_station` | `stations_split == []` |
| każda stacja w dokładnie jednym chunku, wewnątrz jego zakresu | CI + `stations_by_chunk` | 12/12 |
| predykat: chunk pod pociągiem zawsze wczytany, okno bez dziur | `sweep.streaming_plan`, przejazd co 25 m | 268 kroków, 0 problemów |
| okno trzyma mniej chunków niż cały pakiet | CI | maks. 4 z 12 |
| determinizm manifestu poza sha256 plików | `sweep.deterministic_view` | identyczny |
| determinizm geometrii | `geometry_sha256` | 12/12 identyczne |

### Determinizm — dlaczego nie po bajtach GLB

Eksporter glTF nie gwarantuje kolejności bufora, więc **bajty GLB nie są odtwarzalne**,
choć geometria jest (ustalone w PR #44 i w §4 `reports/L1_A-geometry.md`). Kontrola jest
zbudowana pod ten fakt, a nie przeciw niemu:

- `sweep.deterministic_view(manifest)` usuwa z kopii manifestu wyłącznie `sha256`
  i `bytes` chunków oraz `glb_bytes`; **reszta musi być identyczna co do znaku**;
- `geometry_sha256` liczy się z wierzchołków, UV i ścian po stronie Pythona, więc
  **zostaje w porównaniu** i odpowiada na pytanie „czy siatka się zmieniła" wtedy, gdy
  odcisk pliku i tak nic nie mówi. Nadaje się też na klucz cache'u po stronie Godota;
- pola nieodtwarzalne są wypisane w manifeście (`streaming.volatile_keys`), żeby
  następne narzędzie nie musiało tego odkrywać ponownie.

W tym przebiegu bajty GLB wyszły identyczne w 12/12 chunkach — ale kontrola tego
**nie wymaga** i nie wywróci się, gdy wyjdą różne.

### Rzeczywiste wyjście

```
[CHUNKI] chunki=12 suma=6686.739 m os=6686.739 m stacje=12 pliki=892756 B
[CHUNKI] negatyw OK — L1_A_flat_preview_c00: sha256 nie zgadza się z manifestem
[CHUNKI] okno 300.0+600.0 m: maks. 4 chunków naraz, 12 wczytań na całym przejeździe
         (bez streamowania: 12 naraz)
[CHUNKI] manifest OK
  L1_A_flat_preview_c05 [ROUNDTRIP] obiekty=1 wierzcholki=2056 sciany=1236
  L1_A_flat_preview_c05 [ROUNDTRIP] bbox_m: [420.6897, 289.1122, 5.9]
  L1_A_flat_preview_c05 [ROUNDTRIP] OK
[CHUNKI] geometria identyczna w 12/12 chunkach; bajty GLB identyczne w 12/12
         (nie jest to wymagane)
```

Testy jednostkowe: `tools/tests/test_chunks.py`, 29 testów bez Blendera i bez pytest —
przypisanie stacji, przycinanie chainage poza osią, okno symetryczne i asymetryczne,
kierunek jazdy, zakres ujemny, pokrycie okna, ciągłość wyboru, szew, końce osi,
plan `load`/`keep`/`free`, przejazd bez zgubienia chunka pod pociągiem, oraz **osiem
negatywów** `manifest_problems` (dziura, zakładka, zła suma, złe `totals`, powtórzone
id i pliki, pusta geometria, zgubiona stacja, pusty manifest). Cały zestaw:
`179/179 przeszło`.

## 6. Oględziny renderów pojedynczego chunka

Renderowany chunk: **`L1_A_flat_preview_c05`**, 2923,5–3433,3 m, De Brouckère,
zestaw `alignment`, `build/t210/renders/chunk/CHUNK_*.png`.

Kotwice kamer są **liczone jawnie** i podawane przez `--anchor`, zamiast zdawać się na
`render_check.local_vertical_mid`: ono wybiera przekrój po stałym X, a na chunku
biegnącym prawie równolegle do X taki plaster łapie samą płytę stropu i stawia oko
kamery w ścianie (widziałem to — `[SECTION-Z] zmin=4.70 zmax=4.70 mid=4.70`, render
wychodził jednolitą płaszczyzną). Wysokość oka bierze się teraz ze środka profilu
(z = 1,75 m dla `box_double`), a kierunek patrzenia z osi chunka, 25 m w przód.

- **`plan`** — jedna ciągła wstęga od górnego-lewego do dolnego-prawego rogu: łagodny
  łuk w prawo, prosty odcinek w środku, na końcu odgięcie w dół. Brak przerw, pętli
  i odgałęzień; szerokość wstęgi stała na całej długości, więc przekrój nigdzie nie
  znika ani nie puchnie. Kształt to fragment rzutu całej osi z T-111 między
  Sainte-Catherine i Gare Centrale.
- **`section`** — obrys prostokąta wyraźnie szerszego niż wyższego, z widocznymi
  ścięciami obu górnych naroży. Proporcja zgadza się z 9,40 × 5,90 m profilu
  `box_double`. Wnętrze jest ciemniejsze od krawędzi bocznych — patrzymy w rurę,
  nie na bryłę. Ograniczona głębia (`depth_m: 30`) daje jeden przekrój, nie
  scałkowany łuk.
- **`axis05`** — wnętrze prostokątnego tunelu z wysokości oczu maszynisty. Ściany,
  strop i płyta denna widoczne **od wewnątrz**, więc normalne są poprawne — nie widać
  „przez" ścianę. Pierścienie siatki zbiegają się regularnie do punktu zbiegu, linia
  stropu i linia posadzki pozostają poziome na całej głębi (brak skrętu profilu).
  Wyraźny łuk w prawo, na końcu jaśniejsza szczelina — otwarty koniec chunka.
- **`axis25`** — to samo od wewnątrz, łuk w prawo ostrzejszy, pierścienie gęstsze
  po stronie wewnętrznej łuku. Brak szczelin między pierścieniami, brak zanikających
  sekcji, brak podwójnych krawędzi w miejscu, gdzie chunk ma zdublowaną kolumnę szwu UV.
- **`axis50`** — środek chunka, odcinek prawie prosty; korytarz ciągnie się do punktu
  zbiegu bez przewężeń, wszystkie cztery powierzchnie oświetlone od środka.
- **`axis75`** — łuk w lewo i **widoczny koniec chunka**: jasny prostokątny otwór
  w oddali, za nim tło scenowe. Krawędź otworu jest czystym pierścieniem — na końcach
  nie ma śmieci: żadnej wystającej ścianki, żadnej zaślepki, żadnych luźnych trójkątów.
  To jest to, co ma być widać, bo sąsiedni chunk jest osobnym plikiem i w tej klatce
  po prostu nie jest wczytany.

Automat obok oględzin: `ink=0,080..0,090`, `luma_std=0,037..0,045`, `poziomy=180..185`
dla czterech kamer wnętrza — żadna klatka nie jest pusta ani jednolita. **Ta metryka
nie zastępuje obejrzenia PNG** i nie zastąpiła.

## 7. Czego ten manifest jeszcze NIE rozwiązuje dla Godota

Rzeczy, których w manifeście nie ma i które trzeba dołożyć, zanim to zacznie działać
jako streaming w grze:

1. **Przejścia między chunkami.** Manifest mówi, *co* wczytać, nie *kiedy* i nie
   *jak długo trzymać*. Nie ma histerezy — przy tym predykacie skład stojący dokładnie
   na szwie i drgający o metr będzie wczytywał i zwalniał ten sam chunk w kółko.
   Nie ma budżetu czasu na wczytanie (`ResourceLoader` asynchroniczny), nie ma kolejki
   priorytetów „najpierw to, na czym stoję". Nie ma też polityki, kiedy zwalniać:
   `free` jest liczony natychmiast, bez okresu łaski.
2. **LOD.** *(rozwiązane później — `reports/L1_A-lod.md`)* Jeden poziom szczegółu na chunk. Nie ma ani drugiej siatki, ani progów
   odległości, ani impostora dla chunka widocznego z 500 m przez prostą. Przy 16176
   trójkątach na całe 6,7 km to jeszcze nie boli, ale przy torowisku, wyposażeniu
   i oświetleniu zaboli.
3. **Kolizje.** *(rozwiązane później — `reports/L1_A-lod.md` §4)* GLB zawiera samą siatkę wizualną. Nie ma `CollisionShape3D`, nie ma
   uproszczonej geometrii kolizyjnej płyty dennej, nie ma warstw kolizji. Fizyka
   pociągu i tak jest 1D w `src/Sim/`, więc to jest potrzebne dopiero dla widoku
   kabiny i dla obiektów w tunelu.
4. **Materiały.** Każdy chunk niesie własną kopię materiału `tunnel_neutral`
   (szary, roughness 0,85) — kontrolnego, nie docelowego. Nie ma tekstur, nie ma
   wspólnej biblioteki materiałów, nie ma atlasu. UV są policzone i ciągłe przez szew
   (4 m na jednostkę, `design_assumption`), więc jest na czym to zawiesić, ale
   materiału docelowego nie ma.
5. **Stacje.** Manifest wie, *która* stacja leży w *którym* chunku, i to wystarcza,
   żeby doczepić scenę stacji po kilometrażu. Ale samej komory stacyjnej w geometrii
   nie ma — profil `station` istnieje w `profiles.py`, brakuje długości i głębokości
   peronów w `data/`. Chunk ze stacją jest w tej chwili zwykłą rurą.
6. **Profil pionowy.** Wszystko na Z = 0 (T-112, #10). `bbox_min_m[2]` = −1,20 m
   i `bbox_max_m[2]` = 4,70 m w każdym chunku — czyli bbox nie nadaje się jeszcze do
   pytań o głębokość ani do occlusion culling po wysokości.
7. **Scena Godota.** Nie ma `.tscn`, nie ma węzła streamującego, nie ma importu GLB
   do `.res`. Predykat jest w Pythonie i jest przepisywalny 1:1 na GDScript, ale nie
   jest przepisany — to zadanie z serii T-4xx.
8. **Drugi tor i rozjazdy.** `box_double` deklaruje `track_offsets [−2,10; +2,10]`,
   ale geometria toru nie jest modelowana, a oś pakietu A jest pojedynczą polilinią.
   Manifest nie ma pojęcia o torze, tylko o chainage.

## 8. Założenia projektowe dołożone w tym zadaniu

| założenie | wartość | uzasadnienie |
|---|---|---|
| `design_assumption` — domyślne okno streamowania | 600 m przed, 300 m za składem | wprost z `docs/01-architecture.md`; w manifeście oznaczone `status: design_assumption`, **nie** `spec` |
| `design_assumption` — cel kotwicy kamery wnętrza | 25 m przed okiem | wartość robocza kontroli wizualnej, nie fakt o sieci |
| decyzja implementacyjna — przedział domknięty w predykacie | oba chunki na szwie | brakujący chunk to dziura, nadmiarowy to pamięć |
| decyzja implementacyjna — liczniki z generatora, nie z GLB | — | eksporter glTF rozszczepia wierzchołki na szwach UV (PR #44) |

Nic z tego nie jest twierdzeniem o metrze brukselskim i nic nie zmienia `data/`.

## 9. Czego świadomie nie zrobiłem

- **nie ruszyłem `tools/visual/cameras.json`, `tools/visual/framing.py`,
  `docs/17-visual-regression.md`, `tools/track/crs.py`, `data/network/sources.json`** —
  praca równoległa; kotwice chunka podane przez istniejące `--anchor`, bez zmiany
  manifestu kamer;
- **nie naprawiłem `render_check.local_vertical_mid`** — patrz §10; to plik T-012,
  zmiana wysokości oka kamery unieważniłaby baseline pełnej osi, a to jest poza
  zakresem tego zadania;
- **nie skomitowałem żadnego GLB, PNG ani manifestu** — reguła 8 z `CLAUDE.md`;
  manifest powstaje z generatora;
- **nie dodałem LOD, kolizji, materiałów, `.tscn` ani węzła streamującego** — §7;
- **nie chunkowałem wariantu wiernego (`--ring-step 0`)** w CI — ten sam kod, ten sam
  podział, dwa razy dłuższy pipeline bez nowej informacji.

## 10. Zauważone przy okazji, nietknięte

- **`render_check.local_vertical_mid` wybiera przekrój po stałym X.** Na osi biegnącej
  lokalnie równolegle do X plaster o grubości `max(1, scene_size*0,0015)` łapie tylko
  wierzchołki stropu i zwraca `mid = 4,70` m, czyli wysokość stropu — kamera wnętrza
  ląduje w płycie. Na pełnej osi 6,7 km trafia się to rzadko (tolerancja rośnie ze
  `scene_size`), na 510-metrowym chunku trafiło się w 2 z 4 kamer. Obejściem w tym
  zadaniu są jawne kotwice; właściwą poprawką byłoby cięcie po chainage, nie po X.
- **Kamera `section` w zestawie `infrastructure` nadal nie ma `depth_m`** i na chunku
  scałkowała 510 m łuku w jedną klatkę ortho — to samo, co T-210 zapisało dla pełnej
  osi. Dlatego kontrola chunka idzie zestawem `alignment`.
- **Zestaw `alignment` ma nazwy kamer zabite na sztywno** (`axis05/25/50/75`), więc
  `--axis-fractions` z innymi ułamkami cicho pomija kamery (`[SKIP] brak kotwicy`).
  Zadziałało to poprawnie i głośno, ale kadrowanie chunka innymi ułamkami wymagałoby
  zmiany manifestu kamer.
- **Manifest jest per pakiet, nie per linia.** Pakiet A to pień 1/5; przy kolejnych
  pakietach trzeba będzie rozstrzygnąć, czy chainage jest ciągły przez całą linię
  i co się dzieje ze wspólnym pniem 12 stacji. To pytanie do T-1xx, nie do generatora.
