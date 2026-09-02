# Kontrola wizualna i regresja obrazu

Etap Blender zadania T-012 (#27). Część Godot aktywuje się dopiero po T-400 (#26)
i **nie jest** tu zaimplementowana.

Zasada nadrzędna, z `CLAUDE.md` §5:

> Metryka automatyczna **nie zastępuje** obejrzenia PNG. CI wykrywa regresje;
> wykonujący zadanie i tak opisuje w raporcie, co widzi na każdym renderze.

## Elementy

| plik | rola |
|---|---|
| `tools/visual/cameras.json` | canonical manifest kamer, ustawień renderu i progów |
| `tools/visual/framing.py` | matematyka kadrowania, czysty Python, testowalna bez Blendera |
| `tools/visual/capture_blender.py` | render wg manifestu, zapis `*_metadata.json` |
| `tools/visual/compare.py` | sanity, metryki, porównanie z baseline, raport JSON/MD |
| `tools/visual/pngio.py` | czytanie i zapis PNG bez Pillow i bez numpy |
| `tools/ci/visual_smoke.sh` | pięć testów pipeline'u na GitHub-hosted runnerze |
| `.github/workflows/visual-regression.yml` | job `ubuntu-latest`, artefakty także przy fail |

## Użycie

```bash
# render zestawu kamer dla pojazdu
blender --background --python-exit-code 7 --python tools/visual/capture_blender.py -- \
    --in build/M7_shell.glb --set vehicle --prefix M7_shell --out renders \
    --anchor door=12.5,-1.35,1.9

# render zestawu kamer dla infrastruktury (oś trasy daje kotwice inside/section)
blender --background --python-exit-code 7 --python tools/visual/capture_blender.py -- \
    --in build/L1_A.glb --set infrastructure --prefix L1_A --out renders \
    --centerline data/track/L1_A.json

# porównanie z baseline
python3 tools/visual/compare.py --set vehicle --current renders --prefix M7_shell \
    --baseline visual-baseline --diff-dir build/visual/diff \
    --out build/visual/report.json --markdown build/visual/report.md
```

## Zestawy kamer

**`vehicle`** — 1280x720:

| kamera | projekcja | co wykrywa |
|---|---|---|
| `side` | ortho | podział na człony, regularność i rozstaw drzwi, długość |
| `front` | ortho | szerokość, proporcje przekroju, asymetria generatora |
| `iso` | persp 50 mm | ciągłość członów, geometria odwrócona lub nakładająca się |
| `roof` | ortho z góry | dach i obrys skrajni, elementy wystające poza envelope |
| `door` | persp 50 mm, kadr 4,2 m | pojedynczy otwór drzwiowy — **wyłącznie** wymiar, nie branding |

**`infrastructure`** — 960x576: `iso`, `side`, `top`, `inside`, `section`.

**`alignment`** — 960x576: `plan`, `section`, `side`, `axis05`, `axis25`, `axis50`, `axis75`.
Zestaw dla długiej infrastruktury liniowej. Tunel pakietu A ma proporcję 5452 : 6,
więc kamera kadrująca po bboxie daje kreskę grubości 2 px, a ortho bez ograniczenia
głębi całkuje kilka kilometrów łuku w jedną klatkę. Dlatego kontrola idzie przez
kadry **ograniczone**, a nie przez widok całości:

| kamera | co ogranicza kadr | co wykrywa |
|---|---|---|
| `plan` | nic — cała trasa z góry | ucięcie trasy, pętlę, zły odcinek |
| `section` | `depth_m` 30 m + `slab_radius_m` 40 m + `clip_at_anchor` | kształt i proporcje przekroju |
| `side` | `frame_width_m` 80 m + `yaw_deg` 90 + `depth_m` 60 m | pomylone jednostki, skoki skali, profil pionowy |
| `axisNN` | perspektywa z wnętrza | ciągłość, odwrócone normalne, skręt profilu |

**`yaw_deg`** obraca kierunek wyznaczony z kotwic wokół pionu świata. Elewacji bocznej
odcinka trasy nie da się opisać stałym `direction`: oś jest zakrzywiona, więc
„prostopadle do toru" zmienia się z chainage. Obrót pochodnej kierunku z kotwic
załatwia to bez wpisywania współrzędnych do manifestu.

**`depth_m`** ustawia płaszczyznę daleką na `clip_start + depth_m`. Bez tego kamera
ortho przekroju widzi wszystko aż po koniec sceny — na prostym torze testowym
wygląda to poprawnie, bo tunel nie wychodzi z kadru, ale na rzeczywistej, zakrzywionej
osi daje dwa bloki i pozorną „szczelinę" w miejscu, gdzie bore wychodzi z kadru i wraca.
Dlatego ma je też `section` w zestawie `infrastructure`.

**`slab_radius_m`** odrzuca punkty leżące w płaszczyźnie cięcia, ale dalej w bok niż
zadany promień. Płaszczyzna przecina trasę w **kilku** miejscach, gdy trasa zawraca:
oś pakietu E (pierścień 2/6) łapie w płacie także drugą stronę pierścienia, przez co
`ortho_scale` rośnie z 16,5 m do 4777,7 m. Kadr formalnie „znajduje geometrię", a
pokazuje pustkę, bo przekrój pod kotwicą ma wtedy kilka pikseli.

**Płat rośnie, gdy jest pusty.** Grubość +-12 m zakłada pierścienie co kilka metrów.
Na LOD 2 stoją co kilkadziesiąt i płat bywa pusty; wtedy kadr cicho spadał na bbox
całego chunka (`fit_fallback`). Teraz grubość podwaja się do sześciu razy, aż złapie
geometrię, a użytą wartość widać w metadanych jako `slab_thickness_used_m`.
`tools/ci/tunnel_alignment.sh` **wywraca się**, jeśli którakolwiek kamera zgłosi
`fit_fallback` — kadr zastępczy jest cichy i wykrywanie go przez „obraz jest
jednorodny" było zgadywanką.

**Nie każda kamera odpowiada na pytanie przy każdej skali.** `side` na pojedynczym
chunku patrzy na 500-metrową rurę z boku i widzi pasek jednolitej szarości; czy ten
pasek ma w sobie czarny prostokąt otwartego wylotu, zależy wyłącznie od azymutu
chunka. Zmierzone: chunk pakietu A daje 67 poziomów jasności i przechodzi, chunk
pakietu E daje 7 i jest odrzucany, a obie siatki są poprawne. Dlatego rendery
pojedynczego chunka są oceniane tylko na `plan`, `section` i `axisNN`.

`door` wymaga kotwicy `--anchor door=X,Y,Z`; `inside`, `section` i wszystkie `axisNN`
wymagają `--centerline`. Kotwice `axisNN_eye`/`axisNN_target` powstają dla ułamków
chainage podanych w `--axis-fractions` (domyślnie `0.05,0.25,0.5,0.75`).

**Ułamki liczą się w zakresie, który pokrywa wczytana geometria, nie w całej osi.**
Dla pełnej osi to jedno i to samo. Dla chunka 2923–3433 m ułamek 0,05 wskazywałby
86 m, czyli 2,8 km przed jego początkiem — kamera trafiałaby w pustkę, a przekrój
zjeżdżałby na najbliższy pierścień skraju. Zakres pokrycia jest wypisywany w logu
jako `[POKRYCIE]`.

**Kamera `wire` w manifeście.** Camera może zadeklarować `"wire": true` i wtedy
dostaje overlay siatki niezależnie od flagi `--wire-cameras`, która tylko dodaje
kamery do tego zbioru. To wiedza o kamerze, nie o wywołaniu: bez siatki widok wnętrza
tunelu jest jednolicie szary i **przechodzi** kontrolę „nie jest pusta", choć nie
odpowiada na żadne pytanie o geometrię. W scenie złożonej z pojazdu i tunelu bez siatki
nie da się w ogóle odróżnić pudła od ściany, bo materiał kontrolny jest jeden dla
całej sceny.

**Wysokość oka kamery bierze się z przekroju PROSTOPADŁEGO do osi**, nie z płata
o stałym X. Płat o stałym X jest przekrojem tunelu tylko wtedy, gdy tunel biegnie
wzdłuż X; na odcinku pod innym kątem łapie sam strop i zwraca 4,70 m zamiast 1,75 m,
stawiając oko kamery w płycie stropowej. Przekrój zbyt płaski (poniżej 0,5 m) jest
**błędem**, nie wynikiem do cichego użycia. Płat jest poszerzany kilka razy i brany
jest najwyższy znaleziony przekrój, bo ramki liczone z surowej łamanej mają nieco inne
styczne niż pierścienie z osi zagęszczonej i potrafią ciąć pierścień ukośnie.

Brakująca kotwica **pomija kamerę jawnie** (wpis `skipped` w metadanych i w logu) —
nigdy po cichu.

## Co w tym łańcuchu jest odtwarzalne, a co nie — zmierzone

Generator jest deterministyczny. **Eksporter glTF nie jest**, i to nie tylko co do
kolejności bajtów. Zmierzone na czterech niezależnych buildach tej samej skorupy M7,
przy identycznym wejściu (2334 wierzchołki, 1862 ściany, wymiary zgodne co do sześciu
miejsc po przecinku):

| wielkość | rozrzut | nadaje się na kontrolę regresji |
|---|---|---|
| wyjście generatora (wierzchołki, ściany, bbox) | **0** | tak, dokładnie |
| **ściany po re-imporcie GLB** | **0** (4732 za każdym razem) | **tak, dokładnie** |
| wierzchołki po re-imporcie | 5314…5362, czyli **0,9 %** | tylko z tolerancją |
| rozmiar pliku GLB | 149 660…155 904 B, czyli **4 %** | **nie** |
| sha256 pliku GLB | inny za każdym razem | **nie** |

Przyczyna: rozszczepienie wierzchołków na szwach UV i normalnych nie ma ustalonej
kolejności. **Topologia jednak nie drga** — liczba ścian jest niezmiennikiem i to na niej
opiera się kontrola `[TOPOLOGIA]` w `tools/ci/m7_shell_check.sh`: dwa eksporty tej samej
bryły muszą dać tę samą liczbę ścian i identyczny bbox, przy wierzchołkach w tolerancji
5 % (zmierzony rozrzut jest 5–10× mniejszy).

Praktyczne konsekwencje, wszystkie już uwzględnione w kodzie:

- tolerancja 10 % na liczniki w `compare.check_geometry` (PR #44) ma wobec zmierzonego
  0,9 % **dziesięciokrotny zapas** — nie jest ani za luźna, ani zagrożona;
- `sweep.deterministic_view` usuwa `sha256` i `bytes` z porównania manifestu, a zostawia
  `geometry_sha256` liczony po stronie Pythona — i to jest właściwa granica;
- porównywanie bajtów GLB między buildami **zawsze** da fałszywy alarm.

## Determinizm

- stałe transformy kamer liczone wyłącznie z bboxa/kotwic, bez losowości;
- jawna rozdzielczość per zestaw, `resolution_percentage = 100`;
- stałe światło i tło z manifestu (reużyte `render_check.setup_world`);
- `dither_intensity = 0`, motion blur wyłączony, `view_transform = Standard`;
- stała liczba próbek;
- metadane każdego przebiegu: commit, wersja Blendera, silnik, wersja manifestu,
  sha256 wejściowego GLB, sha256 każdego PNG, rozwiązane transformy kamer, bbox,
  liczba obiektów/wierzchołków/ścian.

Zmierzone na Blenderze 4.0.2 (EEVEE, CPU/software EGL): dwa niezależne przebiegi
tego samego GLB dają **bit-identyczne** PNG — MAE `0.00000`, SSIM `1.00000` na
wszystkich pięciu kamerach. Wersja Blendera i wersja manifestu są porównywane,
bo baseline z innej wersji nie jest porównywalny.

## Metryki i progi

Progi są w manifeście, per zestaw kamer:

| próg | znaczenie |
|---|---|
| `mean_abs_diff` | średnia różnica luminancji względem baseline |
| `p95_abs_diff` | percentyl 95 różnicy — odporny na pojedyncze piksele |
| `ssim_min` | uproszczone SSIM na oknach 8x8 zdecymowanego obrazu |
| `min_ink_fraction`, `min_luma_std`, `min_distinct_levels` | klatka nie jest pusta |

„Nie-pusty" **nie** może być samym pokryciem tła. Render 2 km tunelu z daleka to
włos w kadrze (pokrycie ~0,6 %), a widok z wnętrza wypełnia kadr geometrią, więc
modalny poziom jasności *jest* geometrią. Pusta klatka to klatka jednorodna:
zerowa wariancja i kilka poziomów jasności.

### Ta sama podłoga w renderze kontrolnym

`tools/blender/render_check.py` — ten z `CLAUDE.md` §5 — nie miał **żadnej** kontroli
obrazu: pusty PNG wyglądał identycznie jak brak geometrii i kończył się kodem 0.
Teraz każda zapisana klatka jest mierzona tą samą funkcją (`compare.empty_frame_reason`)
i tą samą podłogą (`compare.EMPTY_FRAME_FLOOR` = najłagodniejszy zestaw progów
z manifestu), a klatka pod podłogą kończy skrypt błędem.

Zmierzone na Blenderze 4.0.2, profil `box_double` (9,4 x 5,9 m), kadr po całym bboxie,
960x576 — kolumna „bok" to widok z boku, „iso" izometria:

| oś | iso ink / poziomy | bok ink / poziomy | wynik |
|---|---|---|---|
| L1_A, 5 452 m, zakrzywiona | 0,00252 / 110 | 0,00271 / 100 | przechodzi |
| prosta 5 000 m | 0,00235 / 105 | 0,00220 / **16** | przechodzi (bok dokładnie na podłodze) |
| prosta 10 000 m | 0,00179 / 87 | 0,00220 / **13** | bok pod podłogą |
| prosta 20 000 m | 0,00153 / 67 | 0,00219 / **8** | bok pod podłogą |
| prosta 40 000 m | 0,00138 / 52 | 0,00219 / **11** | bok pod podłogą |
| okno 45 m na L1_A | 0,21568 / 111 | 0,21109 / 112 | przechodzi |

Dwie rzeczy widać w tej tabeli i obie trzeba powiedzieć wprost:

1. **Progiem jest liczba poziomów jasności, nie pokrycie.** `ink` prawie nie drgnęło
   między 5 a 40 km, bo jednopikselowa kreska zajmuje tyle samo pikseli niezależnie
   od tego, ile metrów reprezentuje. Zmienia się gładkość cieniowania.
2. **To jest podłoga, nie miara czytelności.** Izometria osi 40 km jest równie
   bezużyteczna jak jej widok z boku, a mimo to przechodzi — kreska po skosie dostaje
   od antyaliasingu więcej poziomów niż pozioma. Klatka nad podłogą znaczy tylko
   „jest się czemu przyjrzeć", nie „widać, co miało być widać". Obejrzenie PNG zostaje
   obowiązkowe.

Lekarstwem na włos w kadrze jest okno: `render_check.py --from-m X --to-m Y` kadruje
wycinek osi zamiast całego bboxa (wymaga `--centerline`). Okno ramuje **oś**, nie scenę
— geometria odsunięta od osi dalej niż połowa okna może wypaść poza kadr, i właśnie
dlatego pusta klatka musi być błędem, a nie ciszą.

Koszt: 0,40 s na klatkę 960x576 (0,24 s odczyt PNG + 0,16 s statystyki), czysty Python
bez Pillow i numpy — 1,2 s na trzy klatki renderu kontrolnego.

## Kontrola wymiarowa jest osobna od obrazowej

Kadr jest liczony względem bboxa modelu, więc kamera jedzie razem z modelem:
**przesunięcie całej geometrii jest z definicji niewidoczne na obrazie**. Do tego
dochodzi skala: w widoku `iso` tunelu 2 km na 960 px jeden piksel to ~2,2 m, więc
przesunięcie o 1,5 m jest podpikselowe.

Dlatego `compare.py` porównuje też `*_metadata.json`: `bbox_min`, `bbox_max`,
`size_m` z tolerancją **1 mm** oraz liczbę obiektów — te wartości są odtwarzalne
dokładnie. Metryka obrazowa łapie zmianę kształtu i kadru, metryka wymiarowa łapie
bezwzględne położenie i rozmiar.

### Liczniki wierzchołków nie są niezmiennikiem

Eksporter glTF dzieli wierzchołki na duplikaty w innej kolejności przy każdym
przebiegu, więc **liczba wierzchołków po imporcie GLB nie jest odtwarzalna**, nawet
gdy geometria jest identyczna. Zmierzone na bryle M7 (T-220): dwa przebiegi
generatora dały 5360 i 5386 wierzchołków po imporcie przy dokładnie 2334 unikalnych
pozycjach wierzchołków i 4732 ścianach — różnica zbiorów zero, a rendery obu
przebiegów bit-identyczne (MAE `0.00000`, SSIM `1.00000`). Strumień bajtów GLB też
się różni, więc sha256 pliku GLB nie nadaje się na identyfikator artefaktu.

`vertices` i `faces` są więc porównywane z tolerancją względną **10 %**
(`GEOMETRY_COUNT_TOLERANCE`), co nadal łapie realną zmianę gęstości siatki, ale nie
zgłasza fałszywej regresji po zwykłej regeneracji assetu. `mesh_objects` i bbox
pozostają twarde.

## Baseline

- baseline **nigdy** nie jest nadpisywany automatycznie;
- brak baseline daje status `new-baseline`, który jest błędem, dopóki nie poda się
  jawnie `--allow-new-baseline`;
- zapis baseline wymaga osobnego `--accept-baseline` i nie zadziała, gdy
  którykolwiek obraz nie przeszedł kontroli sanity;
- surowe rendery w `renders/` i `build/` pozostają gitignored;
- canonical baseline PNG **nie są** wersjonowane w repo do czasu decyzji
  właściciela o rozmiarze i licencji (Issue #27, sekcja „Retencja w repo");
- CI trzyma before/current/diff jako artefakt, także przy fail.

## Co sprawdza CI

`tools/ci/visual_smoke.sh` na `ubuntu-latest`:

1. brak baseline → `new-baseline`, kod wyjścia != 0, żaden baseline nie powstaje;
2. dwa niezależne przebiegi renderu → `pass`, MAE 0;
3. czarna klatka → `fail` z diagnostyką pustego obrazu;
4. zmieniona rozdzielczość → `fail` z diagnostyką wymiaru;
5. geometria przesunięta **po** ustaleniu kamer → regresja ponad próg + artefakty
   `before`/`current`/`diff`.

Hak `--test-shift` służy wyłącznie do punktu 5. Przesunięcie stosuje się po
rozwiązaniu kamer, bo przed nim byłoby niewidoczne (patrz sekcja wyżej).

## Świadomie poza zakresem etapu Blender

- capture i visual regression dla Godota — dopiero po T-400 (#26);
- kamery vertical slice (approach tunnel, station entry, driver view, HUD);
- wersjonowanie canonical baseline PNG w repo;
- ocena estetyczna i final art.
