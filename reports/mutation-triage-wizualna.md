# Triaż mutacji: bramki regresji wizualnej — `compare.py` i `framing.py`

**Data:** 03.09.2026
**Narzędzie:** `tools/tests/mutation_sweep.py` (gałąź `mutacje-raport-przeliczony`, plik roboczy — nie na `main`, usunięty przed commitem)
**Snapshot wyjściowy:** `737d592`

## Wynik

| moduł | mutacji | ocalałych przed | ocalałych po | pokrycie przed | pokrycie po |
|---|---|---|---|---|---|
| `tools/visual/compare.py` | 24 | 16 | **0** | 33,3 % | **100,0 %** |
| `tools/visual/framing.py` | 22 | 16 | **1** | 27,3 % | **95,5 %** |
| razem | 46 | 32 | **1** | 30,4 % | **97,8 %** |

Zestaw testów: 692 → 711 (19 nowych testów, wszystkie w nowym pliku
`tools/tests/test_visual_gates.py`). **Kod produkcyjny nie został zmieniony.**

Jedyna ocalała mutacja jest **równoważna** — sklasyfikowana wykonaniem, nie lekturą,
na 22 108 wejściach, z których **2 029 trafiło DOKŁADNIE w badaną granicę**.

## Dlaczego akurat te dwa moduły

To jest jedyne mechaniczne oko projektu. `compare.py` rozstrzyga, czy render różni się
od baseline'u; `framing.py` — czy kadr w ogóle pokazuje geometrię, czy pustkę.
CLAUDE.md §5 mówi wprost, że skrypt bez błędu potrafi wyprodukować pustą scenę.
Bramka, która tego nie łapie, usypia mocniej niż brak bramki: zielony przebieg jest
tu twierdzeniem „obejrzano i jest dobrze".

Przy 30,4 % pokrycia twierdzenie było w dwóch trzecich puste.

## Jedna przyczyna, ta sama w obu modułach

Testy dotykały progów **daleko od granicy**. Klatka przesunięta o 6 pikseli przekracza
wszystkie trzy progi regresji naraz; płat ±12 m łapie pierścień z zapasem; bbox
przesunięty o 1,5 m leży setki tolerancji od 1 mm. Takie wejście leży po tej samej
stronie w obu wariantach operatora, więc **nie odróżnia `>` od `>=` ani `<=` od `<`**.

Drugą przyczyną, wyłącznie w `compare.py`, było to, że `main()` — jedyne, co widzi CI —
nie było wykonywane przez żaden test. Cztery mutacje w samym wyznaczaniu kodu wyjścia
i podsumowania przeżywały, w tym `report["status"] == "pass"` → `!=`, czyli zamiana
kodów wyjścia miejscami.

## Pułapka zmiennoprzecinkowa i jak każdy test się z nią rozprawia

`abs((6700.0 + 0.01) - 6700.0)` daje 0,010000000000218 — czyli **nad** progiem 0,01.
Naiwny test „na granicy" granicy nie dotyka. Różnica jest dokładna tylko wtedy, gdy
jedna strona jest zerem albo gdy próg jest potęgą dwójki.

Trafienia w granicę są w tym triażu osiągane **bez podmieniania stałych produkcyjnych**.
Każde ma inne uzasadnienie i każde jest wypisane w docstringu swojego testu:

| granica | wartość | dlaczego dokładna |
|---|---|---|
| `BACKGROUND_TOLERANCE` 0,02 | `abs(0.02 - 0.0)` | tło wypada na 0,0 — jedna strona odejmowania jest zerem |
| progi pustki (3 ×) | wynik `image_stats` | progi są **argumentem** funkcji: po obu stronach stoi ten sam double |
| progi regresji (3 ×) | wynik `diff_metrics` | jw. — `check_image` przyjmuje progi z zewnątrz |
| `changed_fraction` 0,02 | baseline w zerze | jw. co tolerancja tła |
| `GEOMETRY_TOLERANCE_M` 0,001 | `round(0.001 - 0.0, 6)` | bryła stoi przy zerze; na wysokości 6700 m ta sama różnica wyszłaby 0,0010000000000218 |
| dopuszczalna delta liczników | `max(1.0, 5 * 0.10)` = 1,0 | podłoga `max` przycina do liczby całkowitej — dokładnej; tolerancja 10 % **nietknięta** |
| `1e-12` w `_norm` | `sqrt((1e-12)**2)` | pierwiastek jest poprawnie zaokrąglony i wraca bit w bit (sprawdzone asercją w teście) |
| `UP_PARALLEL_EPS` 0,995 | `_norm((sqrt(1-0.995²), 0, 0.995))[2]` | normalizacja zwraca Z równe bit w bit 0,995 — **nie jest to regułą**: dla skali 10× ta sama konstrukcja daje 0,9949999999999999, więc test asercją pilnuje, że granica została trafiona |
| `slab_thickness_m` 10,0 | kotwica w zerze | `dot(offset, forward)` to wprost współrzędna punktu |
| `slab_radius_m` 5,0 | trójka pitagorejska 3-4-5 | `3² + 4² = 25` i `5.0² = 25.0` — wszystkie te liczby są w double dokładne |
| `near > 0.2` | `distance = 0.0` + `depth_min = 0.2` | kamera `place_at_anchor` stoi w kotwicy, więc dodawanie jest dokładne |
| `ortho_scale` → pół kadru | 4,0 przy 100×100 → 2,0 | dzielenie przez potęgi dziesiątki bez reszty |
| `d <= 1e-9` | bryła zdegenerowana na X = 1e-9 | kamera w zerze, odejmowanie dokładne |
| ściana ostrosłupa | `d * tan(radians(fov)/2)` | test liczy limit **tym samym wyrażeniem** co bramka; wpisanie go dziesiętnie by nie działało, bo `tan(radians(90)/2)` to 0,9999999999999999, a nie 1,0 |

Dwie mutacje stałych (`0.2` → `0.202`, `1e-9` → `1.01e-9`) mają dodatkowy punkt
pomiarowy leżący **w przedziale między starym a nowym progiem** — sam punkt równości
ich nie odróżnia, bo leży po tej samej stronie obu.

## Kontrola negatywna — uruchomiona, nie opisana

Nie osobnym przebiegiem, tylko dziennikiem tego samego przeglądu mutacyjnego:
`mutation_sweep.py` wstrzykuje mutację, uruchamia cały `test_all.py` i **zapisuje nazwy
testów, które padły**. Poniższe tabele nie są deklaracją, którą mutację który test
łapie — są zapisem tego, co się stało po wstrzyknięciu.

## `tools/visual/compare.py` — 16 ocalałych → 0

| wiersz | mutacja | werdykt | uzasadnienie / test, który padł po wstrzyknięciu |
|---|---|---|---|
| 71 | `> BACKGROUND_TOLERANCE` → `>=` | **dziura → zabita** | Piksel równo na tolerancji policzony jako tusz podnosi `ink_fraction` pustej klatki z 0,0 do 0,01. Takiego obrazu **nie da się zapisać w 8-bitowym PNG** (0,02 · 255 = 5,1), więc test buduje `pngio.Image` wprost. `test_gate_ink_counts_a_pixel_exactly_at_the_background_tolerance` |
| 96 | `ink_fraction >=` → `>` | **dziura → zabita** | Kadr leżący równo na progu miał przechodzić; mutant odrzuca. `test_gate_empty_frame_floor_accepts_stats_exactly_equal_to_the_thresholds` |
| 97 | `luma_std >=` → `>` | **dziura → zabita** | jw. |
| 98 | `distinct_levels >=` → `>` | **dziura → zabita** | jw. |
| 135 | `d > 0.02` → `>=` | **dziura → zabita** | `changed_fraction` nie wchodzi do żadnego werdyktu — trafia wyłącznie do raportu, na który patrzy człowiek — więc nie ruszał jej ani jeden test. 0,25 → 0,50. `test_gate_changed_fraction_counts_only_pixels_strictly_over_two_percent` |
| 135 | `0.02` → `0.0202` | **dziura → zabita** | jw., 0,25 → 0,00 |
| 147 | `getsize(path) == 0` → `== 1` | **dziura → zabita** | Pusty plik przechodziłby do `pngio.read_gray` i przerywał cały przebieg `PngError`-em zamiast dać status `fail` mówiący, **która kamera** nie ma renderu. `test_gate_missing_render_is_reported_as_missing_not_as_a_broken_png` |
| 185 | `mean_abs_diff >` → `>=` | **dziura → zabita** | Metryka równa progowi to jeszcze nie regresja. Każde kryterium badane w izolacji (pozostałe dwa wyłączone), bo ta implementacja SSIM reaguje na wszystko, co porusza p95. `test_gate_metrics_exactly_on_the_thresholds_are_not_a_regression` |
| 186 | `p95_abs_diff >` → `>=` | **dziura → zabita** | jw. |
| 187 | `ssim <` → `<=` | **dziura → zabita** | jw. |
| 248 | `abs(d) <= tolerance` → `<` | **dziura → zabita** | Istniejący test tolerancji milimetrowej ma punkty 0,5 mm i 2 mm — po obu stronach granicy, ale ani jednego **na** niej. `test_gate_bbox_delta_exactly_at_the_millimetre_tolerance_still_passes` |
| 258 | `abs(delta) <= allowed` → `<` | **dziura → zabita** | Istniejące testy liczników: delta 26 i 3360 przy dopuszczalnej 536. Mutant odrzuciłby przebieg różniący się o **jeden** wierzchołek — a po to ta tolerancja istnieje, bo eksporter glTF dzieli wierzchołki inaczej za każdym razem. `test_gate_vertex_delta_exactly_at_the_allowed_count_still_passes` |
| 325 | `status == "fail"` → `!=` | **dziura → zabita** | Cała `main()` nie była wykonywana. Zgodny przebieg trafiałby w całości na listę „padło". `test_gate_cli_returns_zero_and_counts_every_entry_as_passed`, `test_gate_cli_treats_a_missing_baseline_as_failure_unless_allowed` |
| 326 | `status == "new-baseline"` → `!=` | **dziura → zabita** | jw., przez `fresh`: brak baseline'u przechodziłby bez `--allow-new-baseline`. |
| 329 | `status == "pass"` → `!=` | **dziura → zabita** | Licznik `pass` w podsumowaniu pokazywałby 0 zamiast 2. `test_gate_cli_returns_zero_and_counts_every_entry_as_passed` |
| 374 | `report["status"] == "pass"` → `!=` | **dziura → zabita** | **Kod wyjścia bramki.** Mutant zamienia 0 i 1 miejscami: CI byłoby czerwone przy zgodnym renderze i zielone przy regresji. jw. |

## `tools/visual/framing.py` — 16 ocalałych → 1

| wiersz | mutacja | werdykt | uzasadnienie / test, który padł po wstrzyknięciu |
|---|---|---|---|
| 19 | `length < 1e-12` → `<=` | **dziura → zabita** | Wektor o długości równo 1e-12 ma jeszcze kierunek. `test_gate_norm_rejects_only_vectors_shorter_than_the_epsilon` |
| 19 | `1e-12` → `1.01e-12` | **dziura → zabita** | jw. — ten sam punkt równości rozstrzyga obie |
| 48 | `abs(dot) > UP_PARALLEL_EPS` → `>=` | **dziura → zabita** | Wybór zapasowego „góra" jest binarny i obraca kadr o 90°: `right` skacze z `(0,-1,0)` na `(-0.995, 0, 0.0999)`. Różnica względem baseline'u byłaby ogromna **bez żadnej zmiany geometrii**. `test_gate_camera_basis_keeps_world_up_exactly_at_the_parallel_epsilon` |
| 92 | `res_x >= res_y` → `>` | **równoważna** | patrz niżej |
| 164 | `abs(dot) > thickness` → `>=` | **dziura → zabita** | Punkt równo na krawędzi płata wypadałby z niego, płat rósłby do 20 m i `slab_thickness_used_m` w `visual-metadata.json` kłamałby o tym, jak szeroki wycinek trasy naprawdę widać. `test_gate_slab_keeps_a_point_exactly_at_its_half_thickness` |
| 168 | `r² + u² <= radius²` → `<` | **dziura → zabita** | Promień ma odcinać to, co jest **dalej** niż promień, a nie to, co leży równo na nim. Mutant wypycha przekrój z płata, płat rośnie przez sześć podwojeń i kadr spada na `fit_fallback`, czyli na bbox całego chunka — dokładnie ta awaria, przed którą promień miał chronić. `test_gate_slab_keeps_a_point_exactly_on_its_radius` |
| 256 | `near > 0.2` → `>=` | **dziura → zabita** | Płaszczyzna bliska decyduje, czy kamera we wnętrzu tunelu widzi ścianę, czy ją przecina. Gałęzie różnią się o rząd wielkości: 0,1 m kontra 0,01 m. `test_gate_near_clip_switches_exactly_at_twenty_centimetres` |
| 256 | `0.2` → `0.202` | **dziura → zabita** | jw., drugi punkt pomiarowy przy `near = 0.201` |
| 286 | `d > 0` → `d > 1` | **dziura → zabita** | `corner_visibility` jest **miarą, na której stoją testy kadrowania**; gdy myli się o krawędź, wszystkie testy kadrowania mierzą co innego, niż deklarują. 1,0 → 0,5. `test_gate_ortho_visibility_counts_corners_exactly_on_the_frame_edge` |
| 286 | `d > 0` → `d >= 0` | **dziura → zabita** | Narożniki w płaszczyźnie kamery uznane za widoczne: bryła przecinana przez kamerę raportowana jako „w pełni skadrowana", 0,5 → 1,0. `test_gate_ortho_visibility_drops_corners_exactly_in_the_camera_plane` |
| 286 | `abs(r) <= half_w` → `<` | **dziura → zabita** | 1,0 → 0,0. `test_gate_ortho_visibility_counts_corners_exactly_on_the_frame_edge` |
| 286 | `abs(u) <= half_h` → `<` | **dziura → zabita** | jw. |
| 289 | `d <= 1e-9` → `<` | **dziura → zabita** | 0,0 → 1,0. `test_gate_perspective_visibility_skips_corners_exactly_at_the_depth_epsilon` |
| 289 | `1e-9` → `1.01e-9` | **dziura → zabita** | jw., drugi punkt przy `d = 1.005e-9`, czyli w przedziale (1e-9; 1,01e-9] |
| 293 | `abs(r) <= d*tan_x` → `<` | **dziura → zabita** | Narożniki równo na ścianie ostrosłupa obcięte, 1,0 → 0,0. `test_gate_perspective_visibility_counts_corners_exactly_on_the_frustum_wall` |
| 293 | `abs(u) <= d*tan_y` → `<` | **dziura → zabita** | jw. |

### Jedyna ocalała: `framing.py:92`, `res_x >= res_y` → `res_x > res_y`

**Werdykt: mutant równoważny.** Nie z lektury — z wykonania.

```python
def fov(lens_mm, res_x, res_y):
    if res_x >= res_y:
        sensor_x = SENSOR_MM
        sensor_y = SENSOR_MM * res_y / res_x
    else:
        sensor_y = SENSOR_MM
        sensor_x = SENSOR_MM * res_x / res_y
```

Granicą tego porównania jest `res_x == res_y`, czyli kadr kwadratowy. Na granicy
gałąź „pozioma" liczy `sensor_y = 36.0 * n / n`, a gałąź „pionowa"
`sensor_x = 36.0 * n / n` — obie dają `(36.0, 36.0)`.

Oryginał i mutant załadowane obok siebie
(`importlib.util.spec_from_file_location` na plikach tymczasowych) i przepuszczone
przez wspólną baterię, z porównaniem **bitowym**, nie z tolerancją:

| | |
|---|---|
| wejść razem | **22 108** |
| w tym **dokładnie w granicy** (`res_x == res_y`) | **2 029** |
| różnic oryginał / mutant | **0** |
| w tym na granicy | **0** |

Bateria: 12 rozdzielczości z manifestu i skrajnych (1×1, 2×1, 1×2, 4096×4096, 3×5)
× 9 ogniskowych; wszystkie kwadraty 1×1 … 2000×2000; 20 000 wejść losowych
z ziarnem 20260903.

**Liczba trafień w granicę jest tu tym, co nadaje sens zeru.** Wejścia losowe
w punkt równości nie trafiają z definicji — dwie niezależne liczby z `randint(1, 8192)`
zrównają się średnio raz na 8192 — więc bateria bez jawnie wpisanych kwadratów
raportowałaby „zero różnic" nie badając ani razu tego, co mutacja zmienia.

**Kontrola baterii.** Zero różnic znaczy coś tylko wtedy, gdy bateria umie różnicę
zobaczyć. Ten sam zestaw wejść puszczony na mutancie jawnie obserwowalnym
(`sensor_y = SENSOR_MM * res_y / res_x * 1.000001`) daje **12 076 różnic**.

**Dowód poza baterią.** Dla `res_x == res_y == n` warianty są tożsame wtedy i tylko
wtedy, gdy `36.0 * n / n == 36.0`. Rozdzielczości w tym projekcie są **całkowite** —
pochodzą z `scene_sets[...]["resolution"]` w `cameras.json` i idą przez
`solve_set`/`solve_camera` bez konwersji. Dla całkowitego `n` iloczyn `36·n` jest
liczbą całkowitą reprezentowaną dokładnie, dopóki mieści się w 53 bitach, więc
dzielenie wraca dokładnie do 36. Sprawdzone: wszystkie `n` z 1…10⁶, wszystkie potęgi
dwójki 2⁰…2⁴⁷ oraz wartości brzegowe (2²³±1, 2³¹−1, 2⁴⁰+12345, 2⁴⁷−1) — **zero
rozjazdów**.

Dla argumentów **niecałkowitych** równoważność już nie zachodzi: na 500 000 losowych
dodatnich `float` znalazło się 4751 kontrprzykładów, najmniejszy z nich
`n = 60191946.30585104`, dla którego `36.0*n/n` daje 35,99999999999999.
Wszystkie mają mantysę wymagającą ponad 47 bitów. Żadna rozdzielczość rastra takiej
postaci nie przyjmie, więc mutacja pozostaje nieobserwowalna **na całej rzeczywistej
dziedzinie** — ale nie jest równoważna „matematycznie" i tak jest odnotowana.

Zamiast jej zabijać, fakt jest **utrwalony testem**
`test_gate_fov_is_the_same_on_both_sides_of_the_square_resolution`: sprawdza, że dla
kadru kwadratowego oba kąty są identyczne, i przy okazji, że 36 mm siada na dłuższym
boku. Zmiana, która uczyni gałęzie nierównoważnymi, zapali się tam — a następny
przegląd mutacyjny nie będzie musiał odkrywać tego po raz drugi. Zabicie samej
mutacji wymagałoby testu, który utrwala rachunek zależny od kolejności gałęzi;
byłby to test na implementację, nie na bramkę.

## Czego świadomie nie zrobiono

* **Kod produkcyjny nietknięty.** Żadna z 32 ocalałych nie okazała się usterką
  w kodzie — wszystkie były brakiem pokrycia po stronie testów.
* **`pngio.py` nie był ruszany.** Jest triażowany równolegle (PR #149) i jego mutacje
  nie wchodzą do liczb w tym raporcie, mimo że `compare.py` z niego korzysta.
  `pngio.Image` jest tu używany wyłącznie jako konstruktor obrazu w pamięci — jako
  wejście, nie jako przedmiot badania.
* **Nowe testy są w osobnym pliku** `tools/tests/test_visual_gates.py`, a nie na końcu
  `test_visual.py`. Powód jest mechaniczny: PR #149 dopisuje swój blok dokładnie tam,
  a dwa dopiski w to samo miejsce tego samego pliku zderzyłyby się przy scalaniu.
  `test_all.py` zbiera testy przez `glob("test_*.py")`, więc nowy plik wchodzi sam.
* **`capture_blender.py` nie był mierzony** — importuje `bpy`, więc jego mutacje są
  nierozstrzygalne bez Blendera i nie należą do tego zadania.

## Co odnotowano przy okazji, ale nie tknięto

* `check_image` deklaruje w docstringu moduł „bez ciężkich zależności", ale przy
  pustym pliku ratuje się wyłącznie sprawdzeniem rozmiaru. Plik **niepusty, a nie
  będący PNG-iem** (np. ucięty render, którego Blender nie dokończył) wychodzi
  z bramki nie jako status `fail`, tylko jako wyjątek z `pngio` — i przerywa cały
  przebieg `run()`, zamiast zaraportować, która kamera zawiodła. Zachowanie jest
  utrwalone w `test_gate_missing_render_is_reported_as_missing_not_as_a_broken_png`
  jako **stan faktyczny**, nie jako postulat. To ta sama rodzina co usterka
  `read_gray` opisana w raporcie PR #149; naprawa należy do właściciela, nie do
  triażu.
* `changed_fraction` liczy piksele powyżej 0,02, a `BACKGROUND_TOLERANCE` to również
  0,02 — dwa niezależne progi o tej samej wartości, zapisane osobno. Nic z tego nie
  wynika dziś, ale zmiana jednego z nich w przekonaniu, że zmienia się oba (albo
  odwrotnie), jest tanią pomyłką.
* `SLAB_GROWTH_STEPS` = 6 nie jest porównaniem ani progiem w porównaniu, więc
  `mutation_sweep.py` go nie mutuje. Sześć podwojeń z 12 m to 768 m i tę liczbę
  utrwala istniejący `test_visual_section_camera_reports_fallback_when_there_is_no_geometry`
  — ale zmiana samej stałej nie zapali niczego, dopóki fallback nadal wypada.
