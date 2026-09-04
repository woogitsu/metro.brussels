# T-210 — tunel pakietu A z rzeczywistej osi

**Zmierzone na commicie:** `51fd842` · **data:** 2026-09-01

Wariant: **`flat-preview`, nieprodukcyjny.** Oś `data/track/L1_A.json` ma
`vertical.status = "not_modelled"`, więc cała geometria leży na Z = 0. Generator
odmawia wariantu `production`, dopóki T-112 (#10) nie dostarczy profilu pionowego;
niedostępność publicznych rzędnych główki szyny jest udokumentowana w raporcie T-901.

- generator: `tools/blender/tunnel_sweep.py` (adapter bpy) + `tools/blender/sweep.py` (matematyka, czysty Python)
- oś: `data/track/L1_A.json` — 447 punktów, `origin_source_crs = [146633.4, 170956.0]`, EPSG:31370
- profil: `box_double` z `tools/blender/profiles.py`, klasa **`design`** — wymiary projektowe, **nie** pomiar STIB
- wyjście (nie commitowane): `build/t210/L1_A.glb`, `build/t210/renders/L1_A_*.png`
- odtworzenie: `bash tools/ci/tunnel_alignment.sh`

## 1. Metryki

| wielkość | wariant renderowy (`--ring-step 5`) | wariant wierny (`--ring-step 0`) |
|---|---|---|
| punkty osi źródłowej | 447 | 447 |
| pierścienie | 1349 | 447 |
| długość osi | 6686,74 m | 6686,35 m |
| odchyłka od łamanej źródłowej | 0,2499 m | 0,0000 m |
| chunki | 12 | 12 |
| suma długości chunków | 6686,739 m | 6686,354 m |
| maks. szczelina na szwie | **0,000 mm** | **0,000 mm** |
| szwy przecinające stację | 0 | 0 |
| wierzchołki / ściany / trójkąty | 9520 / 8088 / 16176 | 3206 / 2676 / 5352 |
| ściany z normalną na zewnątrz | 0 | 0 |
| ściany zdegenerowane | 0 | 0 |
| wierzchołki NaN/Inf | 0 | 0 |
| skręt ramki wobec pionu | 0,0000° | 0,0000° |
| gęstość UV | 3,802–4,198 m/jednostkę | 3,813–4,187 m/jednostkę |
| bbox | 5452,5 × 1986,9 × 5,9 m | 5452,5 × 1986,9 × 5,9 m |

Wysokość bboxa równa się co do 1e-6 m wysokości profilu (5,90 m) — potwierdzenie,
że nic nie skaluje geometrii i że 1 jednostka = 1 metr.

## 2. Podział na chunki

Granice idą **w połowie odległości między sąsiednimi stacjami**, więc żadna stacja
nie leży na szwie — to warunek późniejszego streamowania w Godot (wymaganie 4 z #12).
Chunk dłuższy niż 800 m jest dzielony dalej, a kandydat na cięcie wpadający w halo
90 m wokół stacji jest odsuwany poza nie albo porzucany.

| # | od [m] | do [m] | dług. [m] | pierścienie | stacja w chunku |
|---|---|---|---|---|---|
| 0 | 0,0 | 254,9 | 254,9 | 52 | Gare de l'Ouest |
| 1 | 254,9 | 979,5 | 724,6 | 147 | Beekkant |
| 2 | 979,5 | 1754,1 | 774,6 | 157 | Étangs Noirs |
| 3 | 1754,1 | 2388,8 | 634,7 | 129 | Comte de Flandre |
| 4 | 2388,8 | 2923,5 | 534,7 | 109 | Sainte-Catherine |
| 5 | 2923,5 | 3433,3 | 509,7 | 104 | De Brouckère |
| 6 | 3433,3 | 3903,0 | 469,8 | 96 | Gare Centrale |
| 7 | 3903,0 | 4317,8 | 414,8 | 85 | Parc |
| 8 | 4317,8 | 4857,6 | 539,8 | 110 | Arts-Loi |
| 9 | 4857,6 | 5312,4 | 454,8 | 93 | Maelbeek |
| 10 | 5312,4 | 6077,0 | 764,7 | 155 | Schuman |
| 11 | 6077,0 | 6686,7 | 609,7 | 123 | Merode (koniec osi) |

Szew jest zbudowany na **wspólnym pierścieniu**: ostatni pierścień chunka *n* i pierwszy
pierścień chunka *n+1* mają identyczne współrzędne, więc szczelina wynosi 0 z konstrukcji,
a nie z zaokrąglenia. Mierzy to `sweep.chunk_gap_m` i sprawdza test
`test_sweep_mesh_has_no_gap_between_chunks`.

Ograniczenie 800 m jest **miękkie**: gdyby dwie stacje stały bliżej niż 180 m, żadne
cięcie nie mieściłoby się poza halo i chunk zostałby dłuższy. Na pakiecie A ten
przypadek nie występuje — najkrótszy odstęp międzystacyjny to Maelbeek–Schuman, 314,9 m.

## 3. Założenia projektowe (nie dane)

| założenie | wartość | uzasadnienie |
|---|---|---|
| `design_assumption` — zagęszczenie osi | centripetal Catmull-Rom, krok 5 m | łamana źródłowa STIB ma cięciwy ~19 m; przy promieniu 92–97 m daje to widoczne załamania. Krzywa przechodzi przez **wszystkie** punkty źródłowe i nie przesuwa żadnego. |
| `design_assumption` — halo stacji | 90 m | **brak publicznej długości peronów STIB w `data/` i `docs/`.** Przyjęte ≈ długość składu M7 (94,0 m, `data/vehicle/m7-spec.json`), czyli szew leży co najmniej o cały pociąg od chainage stacji |
| `design_assumption` — docelowa długość chunka | 800 m | granulacja streamowania, nie fakt o sieci |
| `design_assumption` — gęstość UV | 4 m na jednostkę UV | wartość robocza; T-210 nie jest zadaniem materiałowym |
| profil `box_double` | 9,40 × 5,90 m, `source_level: design` | wymiary projektowe z `profiles.py`, **nie** pomiar STIB |

Zmierzona konsekwencja wygładzenia, nieukrywana:

- odchyłka krzywej od **skomitowanej łamanej 15 m**: 0,2499 m
- odchyłka krzywej od **surowej łamanej STIB** (`ACTU_LIGNES_BRUTES`, `001m`/`Variante 1`,
  345 punktów na pakiecie A, średni odstęp 19,44 m): **0,1064 m**
- odchyłka skomitowanej łamanej 15 m od surowej łamanej STIB: 0,0006 m
- minimalny promień: 97,3 m na łamanej → **91,5 m** na krzywej zagęszczonej (P05: 149,1 → 147,7 m)

Wygładzenie wybrzusza trasę na zewnątrz cięciwy o ok. 0,11 m wobec danych STIB i o ok. 6 m
zacieśnia lokalny promień minimalny. **Nie da się rozstrzygnąć z dostępnych źródeł**, czy
prawdziwy tor biegnie po cięciwie, czy po łuku — geometria STIB jest linią trasy handlowej,
nie osią toru z pomiaru. Dlatego generator ma tryb wierny `--ring-step 0` (odchyłka 0,0000 m),
oba warianty są budowane i sprawdzane w CI, a wybór domyślny jest decyzją renderową,
nie twierdzeniem o rzeczywistości.

## 4. Kontrole automatyczne

`bash tools/ci/tunnel_alignment.sh` (GitHub-hosted `ubuntu-latest`, Blender 4.0.2, ~32 s):

1. generacja obu wariantów + wewnętrzne kontrole generatora,
2. **test negatywny**: `--variant production` musi zostać odrzucony przy `vertical.status != "modelled"`,
3. kontrola metryk (szczelina, szwy na stacjach, normalne, degeneracje, NaN/Inf, skręt, UV, bbox),
4. **determinizm**: drugi przebieg daje identyczne metryki (bajty GLB *nie* są odtwarzalne — eksporter glTF nie gwarantuje kolejności bufora),
5. **round-trip**: `tools/blender/glb_roundtrip.py` wczytuje GLB z powrotem, sprawdza liczbę obiektów, obecność UV, bbox wobec metryk generatora,
6. render zestawu `alignment` i odrzucenie klatek pustych/jednolitych,
7. `python3 tools/tests/test_all.py` — 131 testów.

Testy jednostkowe geometrii: `tools/tests/test_sweep.py` (17 testów, bez Blendera) —
brak wywrotki ramki na przegięciu i na helisie, przejście krzywej przez punkty źródłowe,
tryb wierny, granice chunków wobec halo stacji i limitu długości, zerowa szczelina,
normalne do wnętrza, brak degeneracji, zdublowana kolumna szwu UV, ciągłość UV przez szew,
niezmienność przekroju.

## 5. Oględziny renderów

Zestaw `alignment` (nowy w manifeście, `manifest_version: 2026-09-01.2`) — pojedynczy
render 6,7 km tunelu daje kreskę grubości 2 px i nie odpowiada na pytanie „czy przekrój
gdzieś znika", dlatego kontrola idzie przez rzut w planie, przekrój o ograniczonej
głębi i cztery zbliżenia wnętrza.

- **`plan`** — jedna ciągła linia od górnego-lewego rogu, ostry łuk w prawo, długi łagodny
  odcinek na wschód, kilka odgięć w środkowej części, na końcu prosta w dół-prawo.
  Brak przerw, pętli, nawrotów i odcinków odbiegających od trasy. Kształt zgadza się
  z rzutem osi z T-111 (`build/L1_A.svg`).
- **`section`** — obrys `box_double` z widocznymi ścięciami naroży stropu, szerszy niż
  wyższy w proporcji zgodnej z 9,40 × 5,90 m. Płaszczyzna bliska tnie geometrię dokładnie
  w kotwicy, głębia ograniczona do 30 m, więc widać jeden przekrój, a nie kilka kilometrów
  łuku scałkowanych w jedną klatkę ortho (tak wyglądało to przed `depth_m`).
- **`axis05` / `axis25` / `axis50` / `axis75`** — wnętrze prostokątnego tunelu z punktu
  widzenia maszynisty. We wszystkich czterech: ściany, strop i płyta denna widoczne
  **od wewnątrz** (normalne poprawne — nie widać „przez" ścianę), pierścienie siatki
  zbiegają się regularnie do punktu zbiegu, linia stropu i linia posadzki pozostają
  poziome na całej głębi (brak skrętu profilu), brak szczelin i brak zanikających sekcji.
  `axis25` i `axis50` pokazują wyraźny łuk w prawo, `axis75` długą prostą — zgodnie
  z rzutem w planie.

## 6. Czego świadomie nie ma

- **profilu pionowego** — T-112 (#10) zablokowane brakiem publicznych rzędnych główki
  szyny; cała geometria na Z = 0, wariant `flat-preview`;
- **komór stacyjnych** — profil `station` istnieje w `profiles.py`, ale wstawienie go
  wymagałoby długości i głębokości peronów, których nie ma w `data/`;
- **materiałów finalnych, wyposażenia tunelu, torowiska, trzeciej szyny** — poza zakresem #12;
- **rozjazdów i odgałęzień** — oś pakietu A jest pojedynczą polilinią;
- **rozdzielenia na dwa tory** — profil `box_double` deklaruje `track_offsets [-2,10; +2,10]`,
  ale sama geometria toru nie jest modelowana;
- **komitowania `build/` i `renders/`** — zgodnie z regułą 8 z `CLAUDE.md`.

## 7. Zauważone przy okazji, nietknięte

- ~~Kamera `section` w zestawie `infrastructure` nie ma `depth_m`~~ — **naprawione**:
  `depth_m` 30 m dostały oba zestawy (`manifest_version` 2026-09-01.3).
- ~~Zestaw `alignment` nie ma widoku z boku~~ — **naprawione**: doszła kamera `side`
  (`yaw_deg` 90, `frame_width_m` 80 m), czyli elewacja 80-metrowego odcinka.
- Kamery `iso` i `side` z zestawu `infrastructure` przy obiekcie o proporcji 5452 : 6
  dają kreskę grubości ok. 2 px. To ograniczenie kadrowania po bboxie, nie defekt
  geometrii — dla długiej infrastruktury właściwym zestawem jest `alignment`.
- **Część osi leży w poligonach UrbIS oznaczonych `niveau: 0`**, czyli tym samym markerem,
  co odcinki znane z biegu po powierzchni (Erasme, Pannenhuis, Delacroix–Clemenceau).
  Zmierzone pokrycie: **18 z 447 punktów osi**, w dwóch krótkich przedziałach —
  45–135 m (90 m) i 690–840 m (150 m), oba w rejonie Gare de l'Ouest / Beekkant.
  Razem **240 m z 6686 m, czyli 3,6 %**.

  Pierwsze odczytanie było mocniejsze i **fałszywe**: nazwa poligonu
  („Tunnel STIB Beekkant – Gare de l'Ouest") sugerowała, że cały pierwszy odcinek
  pakietu A, 510 m, jest na poziomie terenu. Pomiar pokrycia punkt po punkcie pokazał
  co innego. Warto to zapisać, bo z samej listy nazw wniosek wyglądał na pewny.

  **Interpretacja pozostaje nierozstrzygnięta.** `data/network/sources.json` mówi
  wprost, że pola poziomu względnego wymagają interpretacji, a `niveau: '-'` wobec
  `'0'` nie ma w datasecie definicji. Jeżeli `0` znaczy „na poziomie terenu", to model
  zamkniętej rury jest na tych 240 m niewłaściwy. Rozstrzygnięcie należy do R-005 (#17)
  i R-004 (#16). **Geometria nie została na tej podstawie zmieniona.**

  Osobno: **191 z 447 punktów osi nie leży w żadnym poligonie `MT`**, więc warstwa
  UrbIS nie pokrywa całego pnia i brak pokrycia nie jest dowodem na cokolwiek.

- `data/track/L1_A.json` podaje chainage Merode **6686,35 m**, czyli dokładnie
  `length_m` osi. Różnicy nie ma i nie ma tu nic do rozstrzygnięcia.

  Do #86 (`4a03982`, 02.09.2026) stało tu 6686,99 m przy `length_m` 6686,35 m i ten
  raport zapisał rozbieżność 0,64 m jako obserwację do rozstrzygnięcia. #86 rozstrzygnęło
  ją: kilometraż stacji liczy się teraz na osi **po** przepróbkowaniu, a nie na łamanej
  źródłowej. Pomiary geometrii wyżej zostają nieprzeliczone — `points` i `length_m`
  #86 nie tknęło.
