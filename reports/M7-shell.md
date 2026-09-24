# M7 — proceduralna bryła zewnętrzna (T-220)

**Zmierzone na commicie:** `51fd842`

Generator: `tools/blender/m7_shell.py` + `tools/blender/m7_layout.py`.
Stan: **techniczna skorupa**, nie asset finalny. Data: 2026-09-01.

Model powstaje w 100 % ze skryptu. W repozytorium nie ma pliku `.blend` ani
żadnego kroku ręcznego; `build/M7_shell.glb`, `build/M7_envelope.glb` i
`build/M7_shell.json` są generowane i **nie** są commitowane.

## Wymiary `spec` — źródło pierwotne

Wszystkie poniższe są czytane z `data/vehicle/m7-spec.json` (T-904, #8) i muszą
mieć w rejestrze status `spec`. Generator **odmawia startu**, jeśli któryś ma inny
status — to jest testowane, także negatywnie, w CI.

Źródło: STIB/MIVB, 13.07.2020 — <https://stib.prezly.com/le-nouveau-metro-m7-est-arrive-a-bruxelles>

| parametr | wartość | jak realizuje go geometria |
|---|---:|---|
| długość całkowita | 94,0 m | bbox X = `[0,000; 94,000]`, zmierzone 94,000000 m |
| szerokość | 2,70 m | bbox Y = `[-1,350; 1,350]`, zmierzone 2,700000 m |
| wysokość podłogi | 1,03 m | próg każdego otworu drzwiowego; lico wewnętrzne płyty podłogowej |
| liczba członów | 6 | sześć osobnych obiektów `M7_car_1..6` |
| drzwi podwójne / stronę | 18 | po 3 na człon na stronę, 36 otworów razem |
| pojedyncze drzwi kabinowe | 2 | po jednych przy każdej kabinie, na przeciwnych stronach |
| szerokość otwarcia | 1,60 m | zmierzone w wygenerowanej siatce dla wszystkich 36 otworów |

## `design_assumption` — wymiary bez źródła pierwotnego

Żadna z tych wartości **nie jest** `spec` i nie awansuje do `spec` bez źródła
pierwotnego znalezionego w T-904 (#8). Wszystkie są stałymi `DESIGN_*` w
`m7_layout.py`; test pilnuje, żeby każda stała miała wpis z uzasadnieniem.

| założenie | wartość | dlaczego taka |
|---|---:|---|
| wysokość całkowita | 3,60 m | wartość projektowa skrajni już obecna w repo (`profiles.M7_HEIGHT_M`); reużyta, żeby bryła i profile tuneli nie miały dwóch różnych „prawd" |
| faza dachu | 0,35 m | jw., `profiles.M7_ROOF_CHAMFER_M` |
| grubość skorupy | 0,08 m | bez grubości otwór drzwiowy byłby wnęką, nie otworem; spód pudła leży dokładnie o tę grubość poniżej podłogi, więc lico podłogi wypada na source-backed 1,03 m |
| długość przegubu | 1,10 m | przewężenie między członami |
| wcięcie przegubu | 0,18 m / stronę | jw. |
| długość ścięcia czoła | 2,40 m | ścięcie **liniowe** zamiast zgadywania promieni czoła ze zdjęć |
| zwężenie czoła | 0,45 m / stronę | jw. |
| obniżenie dachu na czole | 0,30 m | jw. |
| strefa kabiny | 3,60 m | odcinek bez drzwi pasażerskich |
| wysokość światła drzwi | 1,95 m | spec podaje tylko szerokość otwarcia |
| drzwi kabinowe | 0,80 × 1,87 m, oś 2,90 m od czoła | spec podaje tylko ich liczbę |
| podział długości | równy, 15,666667 m / człon | brak źródła na rzeczywisty podział między człony |

**Świadomie nieustalane, bo nie ma danych:** rozstaw i geometria wózków, podwozie,
rozkład mas i naciski osi, dokładne szyby, kształt i promienie nosa, urządzenia
dachowe, odbiór prądu w kontekście pojazdu, kinematyka przegubów.

## Wynik generatora

```
[RAPORT] wymiary_m: X=94.000000 Y=2.700000 Z=2.650000
[RAPORT] bbox_min=[0.0, -1.35, 0.95] bbox_max=[94.0, 1.35, 3.6]
[RAPORT] obiekty=11 (członów=6, przegubów=5)
[RAPORT] wierzcholki=2334 sciany=1862
[RAPORT] drzwi podwójne: 18/stronę, krawędzie zmierzone: 36/36
[RAPORT] drzwi kabinowe: 2
[RAPORT] skrajnia pojazdu: ok
[RAPORT]   profil bore_single: OK luz_max=0.49 m
[RAPORT]   profil box_double: OK luz_max=1.08 m
[RAPORT]   profil station: OK luz_max=1.50 m
[RAPORT] symetria obrotowa 180°: 0 niezgodnych z 2334 wierzchołków
[RAPORT] re-import GLB: obiekty=11 max_delta=0.0 m ok=True
```

Bryła zajmuje w pionie `0,95–3,60 m`; 2,65 m to wysokość samego pudła, nie
wysokość pojazdu nad główką szyny (3,60 m obejmuje przestrzeń pod pudłem).

## Kontrole automatyczne

Rozkład (`tools/tests/test_m7_shell.py`, bez Blendera) — 21 testów:

- wymiary czytane wyłącznie z rejestru i tylko o statusie `spec`;
- podmiana wartości w rejestrze zmienia model (dowód, że nic nie jest wpisane na sztywno);
- każda stała `DESIGN_*` ma udokumentowane uzasadnienie;
- 6 członów, 5 przegubów, kafelkowanie całych 94 m bez szczelin i nakładek;
- 18 drzwi podwójnych na stronę, po 3 na człon, rozstaw równy w obrębie członu;
- otwory nie nachodzą na siebie, nie wchodzą w przeguby ani w strefy kabin;
- rozkład drzwi niezmienniczy na obrót 180° (skład jest dwukierunkowy);
- przekrój osiąga dokładnie 2,700 m między ścięciami i nigdzie go nie przekracza;
- skrajnia pojazdu i wszystkie trzy istniejące profile tuneli.

**SPROSTOWANIE z 06.09.2026 (pozycja 6.D8).** Poprzednia wersja zdania nad tą listą
mówiła „**22 testy**". **To była nieprawda** — i nie jest to datowany pomiar, który
się zestarzał, więc liczba jest przepisana, a nie dopisana obok. Plik nigdy tylu
testów nie miał: wnosi go do drzewa ten sam commit, co ten raport (`de574ff`,
squash-merge PR-a #43), przez całą historię ma jeden niezmieniony blob i w każdej
osiągalnej wersji — łącznie z jedynym commitem gałęzi przed squashem — daje 21 przy
`grep -c '^def test_'`. Dwudziestka dwójka to liczba wszystkich definicji na
marginesie modułu, czyli 21 testów **plus pomocnik** `_layout()`, który testem nie
jest i którego `tools/tests/test_all.py` nie zbiera. Całe rozstrzygnięcie, z pomiarami
i z odtworzeniem: `reports/M7-shell-liczba-testow.md`.

Siatka (`tools/ci/m7_shell_check.sh`, w Blenderze):

- bbox długości i szerokości z tolerancją **1 mm**;
- origin w `x = 0`, spód pudła równy `1,03 − 0,08`;
- szerokość każdego otworu **zmierzona w wygenerowanej geometrii**, nie w parametrach;
- brak NaN/Inf, brak obiektów o absurdalnej skali, sensowna liczba wierzchołków;
- symetria obrotowa całej siatki: 0 niezgodnych wierzchołków z 2334;
- GLB ma magic `glTF`, eksport i ponowny import dają `max_delta = 0,0 m`;
- test negatywny: wymiar oznaczony jako `design_model` zatrzymuje generator i nie
  powstaje żaden GLB;
- szerokość otworu **zmierzona na renderze**: 488 px przy 3,2812 mm/px = **1,6012 m**;
- sylwetka czoła na renderze: 2,703 × 2,658 m przy 4,969 mm/px, odchylenie środka
  od osi kadru 0,5 px.

## Skrajnia i kolizje

`build/M7_envelope.glb` to uproszczona skrajnia pojazdu do testów kolizji:
prosty graniastosłup `94,0 × 2,70 × 3,70 m` (`z ∈ [−0,10; 3,60]`) z
`profiles.vehicle_gauge(clearance=0.0)`. Jest **osobnym plikiem**, nie częścią
bryły — inaczej przesłaniałby model na renderach kontrolnych i psuł bbox.

Skrajnia mieści się we wszystkich trzech projektowych profilach tuneli z zapasem
0,49 m (`bore_single`), 1,08 m (`box_double`) i 1,50 m (`station`). Test skrajni
przeszedł, więc nie było potrzeby rozstrzygać, czy problemem jest profil tunelu
czy bryła. Gdyby nie przeszedł: profile tuneli mają w `profiles.py` status
`source_level: design`, a wymiary pojazdu są `spec` — pierwszeństwo miałaby
korekta profilu, nie zmniejszanie pociągu.

## Prawo

Zgodnie z `docs/03-legal.md`: neutralny materiał techniczny (szary, bez tekstur),
**brak** logo i znaków STIB/MIVB, brak liverii, brak map sieci, brak piktogramów,
brak tapicerki i wzorów, brak jakiejkolwiek rekonstrukcji identyfikacji wizualnej.
Nie użyto żadnych cudzych zdjęć, modeli ani wymiarów z Wikipedii, Sketchfaba,
Train Simulatora, gier ani modeli fanowskich.

## Poza zakresem T-220

Kabina, wnętrze pasażerskie, finalne szyby i materiały, realistyczne wózki,
finalne podwozie, art pass, dźwięki, animacja drzwi i kinematyka przegubów.
Człony są rozdzielone jako osobne obiekty pod przyszłą animację, ale nic tu nie
udaje rzeczywistej kinematyki, bo nie ma na nią danych.

Stan źródeł potrzebnych do wykonania prawdziwych szyb opisuje
`reports/m7-window-evidence.md`.
