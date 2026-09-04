# Triaż mutacji: `pngio.py` i `assert_shot_metadata.py`

**Data:** 03.09.2026
**Narzędzie:** `tools/tests/mutation_sweep.py` (gałąź `mutacje-raport-przeliczony`, plik roboczy — nie na `main`)
**Snapshot wyjściowy:** `737d592`

## Wynik

| moduł | mutacji | ocalałych przed | ocalałych po | pokrycie przed | pokrycie po |
|---|---|---|---|---|---|
| `tools/visual/pngio.py` | 38 | 25 | **7** | 34,2 % | **81,6 %** |
| `tools/ci/assert_shot_metadata.py` | 33 | 16 | **2** | 51,5 % | **93,9 %** |
| razem | 71 | 41 | **9** | 42,3 % | **87,3 %** |

Zestaw testów: 692 → 709 (dopisanych 17 testów, wszystkie w istniejących plikach
`tools/tests/test_visual.py` i `tools/tests/test_shot_metadata_gate.py`).
Kod produkcyjny nie został zmieniony.

## Jak klasyfikowane były mutacje ocalałe

Nie z lektury. Dla każdej ocalałej mutacji oryginał i mutant były ładowane **obok
siebie** (`importlib.util.spec_from_file_location` na pliku tymczasowym) i przepuszczane
przez wspólną baterię wejść — patologie plus losowe z ustalonym ziarnem — z pełnym
porównaniem wyników, łącznie z typem i treścią wyjątku.

* `pngio.py`: **31 871 wejść** na wariant — 60 ręcznie złożonych plików PNG (wszystkie
  typy koloru, obie głębie, filtry 0–4 i mieszane, chunki dodatkowe, przeplot, paleta,
  zepsute CRC, pięć rodzajów ucięcia, 12 plików losowych), 31 tys. trójek dla `_paeth`
  oraz 59 wartości dla obu zapisów, porównywanych bajt po bajcie na wyjściu.
* `assert_shot_metadata.py`: **330 wejść** na wariant — 165 zestawów metadanych
  (granice bboxa, zawierania osi, luzu, rozdzielczości, widoku, chainage'u, składu,
  25 losowych) razy dwa tryby wywołania, plus podmieniane rejestry M7.

„Równoważna" pada wyłącznie tam, gdzie **żadne** wejście nie odróżniło wariantów.

## `tools/visual/pngio.py`

Przyczyna 25 ocalałych była jedna: **każdy dotychczasowy test czytał plik, który sam
przed chwilą zapisał**. `write_gray`/`write_rgb` produkują zawsze ten sam PNG — 8 bitów,
typ koloru 0 albo 2, filtr 0 w każdym wierszu, trzy chunki. Cały dekoder filtrów, gałąź
16-bitowa, gałąź kolorowa i pomijanie chunków dodatkowych nie były wykonywane ani razu.
Blender produkuje dokładnie to, czego nie było w testach.

| wiersz | mutacja | werdykt | uzasadnienie |
|---|---|---|---|
| 42 | `pa <= pb` → `pa < pb` | **równoważna** | Z `pa == pb` wynika `a + b = 2c`, a stąd `pc = 0 < pa`, więc pierwsza gałąź i tak nie jest brana. Sprawdzone **wyczerpująco na wszystkich 16 777 216 trójkach bajtów** — zero rozjazdów. Zapisane w docstringu testu Paetha. |
| 42 | `pa <= pc` → `pa < pc` | **dziura → zabita** | Remis `pa == pc` jest osiągalny i zmienia wynik: `_paeth(3, 6, 5)` daje 3, mutant 5. Test `test_visual_png_paeth_breaks_ties_the_way_the_spec_requires`. |
| 44 | `pb <= pc` → `pb < pc` | **dziura → zabita** | `_paeth(6, 3, 5)` daje 3, mutant 5. Ten sam test. |
| 58 | `1` → `2` (filtr Sub) | **dziura → zabita** | Żaden test nie czytał PNG z filtrem ≠ 0. `test_visual_png_reads_every_filter_type_the_spec_defines`. |
| 61 | `2` → `3` (filtr Up) | **dziura → zabita** | jw. |
| 64 | `3` → `4` (filtr Average) | **dziura → zabita** | jw. |
| 66 | `i >= bpp` → `i > bpp` (Average) | **dziura → zabita** | Lewy sąsiad na pierwszym krytym bajcie. Obrazy testowe mają **celowo niezerowy pierwszy bajt wiersza** — przy zerze ta mutacja nie zmieniłaby ani jednego piksela. |
| 68 | `4` → `5` (filtr Paeth) | **dziura → zabita** | jw. co 58. |
| 70 | `i >= bpp` → `i > bpp` (left, Paeth) | **dziura → zabita** | jw. co 66. |
| 71 | `i >= bpp` → `i > bpp` (upleft, Paeth) | **dziura → zabita** | jw. co 66. |
| 89 | `pos + 8 <= len` → `<` | **dziura → zabita** | Odróżnia je jedno wejście na 31 871: plik urwany dokładnie na granicy nagłówka chunku. Mutant nie ogląda tego nagłówka i melduje „brak IHDR" o pliku, w którym IHDR **stoi**. Test pilnuje diagnozy, nie typu wyjątku (patrz *Usterka* niżej). |
| 98 | `ctype == IEND` → `!=` | **dziura → zabita** | Dla PNG o trzech chunkach mutant jest nieodróżnialny — dlatego przeżył. Dla PNG z chunkiem dodatkowym (`tEXt`, który pisze Blender) urywa czytanie przed IDAT i `zlib` wysypuje się na pustym strumieniu. `test_visual_png_skips_the_chunks_blender_puts_around_the_image`. |
| 105 | `color_type == 3` → `== 4` | **dziura → zabita** | Paleta jest w `_CHANNELS`, więc zatrzymuje ją dopiero ten warunek; mutant przepuszcza paletę (indeksy wzięte za jasności) i odrzuca greyA. `test_visual_png_accepts_an_alpha_channel_and_refuses_a_palette`. |
| 121 | `channels >= 3` → `> 3` (8 bit) | **dziura → zabita** | Wszystkie obrazy testowe były szare (`r == g == b`), więc czytanie samego R nie zmieniało nic. `test_visual_png_luminance_uses_all_three_colour_channels`. |
| 121 | `3` → `4` | **dziura → zabita** | jw. |
| 126 | `channels >= 3` → `> 3` (16 bit) | **dziura → zabita** | Gałąź 16-bitowa nie była wykonywana ani razu. `test_visual_png_reads_sixteen_bit_samples`. |
| 126 | `3` → `4` | **dziura → zabita** | jw. |
| 148 | `value < 0.0` → `<= 0.0` | **równoważna** | Dla `value == 0.0` obie gałęzie dają 0.0. Zero rozjazdów na 31 871 wejściach. |
| 148 | `0.0` → `0.001` | **równoważna** | `int(round(v * 255))` dla `v < 0.001` daje 0 tak samo jak przycięcie do zera (0,001 · 255 = 0,255). Zero rozjazdów. |
| 148 | `value > 1.0` → `>= 1.0` | **równoważna** | Dla `value == 1.0` obie gałęzie dają 1.0. Zero rozjazdów. |
| 148 | `1.0` → `1.01` | **dziura → zabita** | `1.002 · 255 = 255.51` → 256 → `ValueError` z `bytearray.append`. Zapis diffa padłby wyjątkiem zamiast przyciąć. `test_visual_png_writers_clamp_out_of_range_values_to_black_and_white`. |
| 165 | cztery jw. w `write_rgb` | **3 × równoważna, 1 × zabita** | Identyczna analiza i ten sam test. |

### Ocalałe po zmianie — 7, wszystkie równoważne

`42` (`pa <= pb`), `148` × 3, `165` × 3. Wszystkie siedem zostały udowodnione
wykonaniem: dla Paetha wyczerpująco na całej dziedzinie bajtów, dla przycinania na
59 wartościach obejmujących obie granice, wartości ujemne i wielokrotności progu.
**Żadna z nich nie jest usterką i żadnej nie należy „naprawiać".**

### Usterka zauważona przy okazji — nie naprawiona

`read_gray` deklaruje `PngError` jako swój typ błędu, ale plik ucięty w środku chunku
wychodzi z niego jako `struct.error` („unpack requires a buffer of 13 bytes") albo
`zlib.error` („incomplete or truncated stream") — czyli surowym wyjątkiem biblioteki.
Poprawka to jedna kontrola kompletności chunku (`pos + 12 + length > len(blob)`).

**Nie zrobiona świadomie:** to zmiana kodu produkcyjnego wykraczająca poza zadanie,
a jedyny konsument (`compare.py`) nie łapie żadnego z tych wyjątków, więc w obu
wariantach bramka pada z tracebackiem — różni się treść, nie skutek. Dopisany test
pilnuje tego, co realnie boli w logu CI (komunikat nie może kłamać, że IHDR nie ma),
i przechodzi niezależnie od tego, czy usterka zostanie kiedyś naprawiona.

## `tools/ci/assert_shot_metadata.py`

Przyczyna 16 ocalałych: testy sprawdzały wartości **daleko** od progów — bbox przesunięty
o 1000 m, `mesh_objects: 0`, skład o 6 m za krótki, wystawanie o pół i o dwa przekroje
tunelu. Takie wejście nie odróżnia `>` od `>=` ani `1e-3` od `1,01e-3`: leży po tej samej
stronie granicy w obu wariantach.

| wiersz | mutacja | werdykt | uzasadnienie |
|---|---|---|---|
| 126 | `length <= 0.0` → `< 0.0` | **dziura → zabita** | Obie wersje odrzucają zerowy skład, ale różnym **komunikatem**: „zwinięty w punkt albo nieobecny" kontra „rozjazd 94 m z rejestrem". To komunikat trafia do loga i mówi, czy szukać złej skorupy, czy jej braku. `test_a_train_of_zero_length_is_reported_as_absent_not_as_a_wrong_size`. |
| 126 | `0.0` → `0.001` | **ocalała świadomie** | Odróżnia je wyłącznie `length_m ∈ (0; 1 mm]` — i tam obie wersje i tak **odrzucają** skład, różniąc się tylko wyborem komunikatu. Zabicie wymagałoby testu twierdzącego, że skład o długości 0,5 mm ma być zgłoszony jako „rozjazd z rejestrem", a nie jako „zwinięty w punkt" — czyli utrwalenia gorszej z dwóch diagnoz. Nie warto. |
| 132 | `> nominal * 0.01` → `>=` | **dziura → zabita** | Patrz *Pułapka zmiennoprzecinkowa* niżej. |
| 139 | `> nominal_w * 0.01` → `>=` | **dziura → zabita** | jw. |
| 143 | `roof <= 0.0` → `<= 0.001` | **ocalała świadomie** | Odróżnia je `roof_height_m ∈ (0; 1 mm]`. Mutant czyni bramkę **ostrzejszą** w zakresie wysokości dachu fizycznie niemożliwych. Zabicie wymagałoby testu pinującego, że dach o wysokości 0,5 mm **przechodzi** bramkę — utrwalenia słabości, nie kontraktu. |
| 166 | `value <= 0` → `<= 1` | **dziura → zabita** | Testy sprawdzały wyłącznie zero, a zero nie odróżnia progu 0 od progu 1. Scena z jednej scalonej siatki jest normalnym wynikiem eksportu i musi przechodzić. `test_a_scene_of_one_mesh_object_is_still_a_scene`. |
| 176 | `> 1e-3` → `>=` | **dziura → zabita** | Granica osiągalna dokładnie tylko przy zerze — patrz niżej. `test_size_must_follow_from_the_bbox_down_to_the_millimetre`. |
| 176 | `1e-3` → `0.00101` | **dziura → zabita** | Kontrola negatywna tego samego testu: rozjazd 1,005 mm leży MIĘDZY progiem a progiem podniesionym o procent. |
| 178 | `s <= 0.0` → `< 0.0` | **dziura → zabita** | Poprzedni test zerował `size_m`, ale zostawiał bbox — zapalała się więc kontrola spójności z bboxem, nie kontrola zwinięcia. `test_a_scene_axis_collapsed_to_zero_is_reported` zwija oba naraz. |
| 178 | `0.0` → `0.001` | **zabita ubocznie** | Zabita przez test granicy z wiersza 176, w którym scena ma wzdłuż Y rozmiar dokładnie 1 mm i musi przejść kontrolę zwinięcia. Odnotowane jako uboczne, nie jako zamiar. |
| 189 | `lo > axis_lo + 1e-6` → `>=` | **dziura → zabita** | Zapas mikrometra jest inkluzywny. Granica osiągalna dokładnie, bo test liczy ją **tym samym wyrażeniem** co bramka i wstawia wynik do metadanych — porównywane są dwie identyczne liczby. `test_the_scene_may_touch_the_axis_exactly_at_the_micrometre_slack`. |
| 189 | `hi < axis_hi - 1e-6` → `<=` | **dziura → zabita** | jw., druga strona. |
| 195 | `> profile_width_m` → `>=` | **dziura → zabita** | Wystawanie równe przekrojowi tunelu (9,40 m) ma jeszcze przechodzić. Osiągalne dokładnie, bo oś L1_A zaczyna się w scenicznym X równym **zeru**. `test_an_overhang_of_exactly_one_tunnel_cross_section_still_passes`. |
| 204 | `> AXIS_TOLERANCE_M` → `>=` | **dziura → zabita** | Granicy `1e-3` nie da się dotknąć dla osi dłuższej niż ~2 mm; test podmienia tolerancję na potęgę dwójki. Patrz niżej. |
| 219 | `> 1.0` → `>=` | **dziura → zabita** | Jedyny próg w tym pliku bez żadnej sztuczki: `1.0` jest potęgą dwójki, `abs(2001.0 - 2000.0) == 1.0` dokładnie. |
| 219 | `1.0` → `1.01` | **dziura → zabita** | Druga kontrola negatywna tego samego testu: 1,005 m. |

### Ocalałe po zmianie — 2

`126 prog` i `143 prog`. Obie **są obserwowalne** (harmonogram różnicowy je odróżnia) —
nie są mutantami równoważnymi i tak nie są opisane. Obie odróżnia wyłącznie przedział
`(0; 1 mm]`, w którym mutant jest ostrzejszy albo lepiej opisuje ten sam werdykt.
Test zabijający którąkolwiek musiałby stwierdzić, że wartość fizycznie niemożliwa ma
przechodzić bramkę albo dostawać gorszy komunikat. Zostawione świadomie, z tym wpisem
jako uzasadnieniem.

## Pułapka zmiennoprzecinkowa — gdzie granica jest, a gdzie jej nie ma

Próg sprawdzony „na oko na granicy" granicy nie dotyka. `abs((6700.0 + 0.01) - 6700.0)`
daje `0.010000000000218`, czyli **nad** progiem — po tej samej stronie co wartość zdrowa.
Test napisany naiwnie przechodzi wtedy dla obu wariantów operatora i niczego nie dowodzi.
Różnica dwóch liczb zmiennoprzecinkowych jest dokładna tylko wtedy, gdy **jedna strona
jest zerem** albo **próg jest potęgą dwójki** (a wtedy jeszcze musi być wielokrotnością
kroku siatki w okolicy wartości).

W tych dwóch modułach wypadło to tak — i każdy przypadek jest wyjaśniony w docstringu
odpowiedniego testu:

| próg | granica osiągalna? | jak dotknięta |
|---|---|---|
| `chainage ± 1.0 m` (219) | **tak, wprost** | `1.0` to potęga dwójki, a krok siatki przy 2000 m to 2^-41. `abs(2001.0 - 2000.0) == 1.0` dokładnie. |
| zapas osi `1e-6` (189) | **tak, przez tożsamość** | Test liczy `axis_lo + 1e-6` tym samym wyrażeniem co bramka i porównuje liczbę z samą sobą. Żadnej arytmetyki pośredniej, więc żadnego zaokrąglenia. |
| przekrój tunelu `9.4 m` (195) | **tak, przy zerze** | Oś L1_A zaczyna się w scenicznym X = 0, więc `0.0 - (-9.4) == 9.4` dokładnie. Ta sama różnica policzona przy 5446,6 m zgubiłaby się w zaokrągleniu. Test sprawdza to założenie jawnie (`assert axis_lo[0] == 0.0`). |
| spójność bboxa `1e-3` (176) | **tak, przy zerze** | Oś jest płaska w scenicznym Y (składowa Z danych jest wszędzie zerowa), więc wzdłuż Y bryła może stać przy samym zerze: `(0.001 - (-0.001)) - 0.001 == 1e-3` dokładnie, bo `2d − d = d`. Przy bboxie rzędu tysięcy metrów wartość `1e-3` nie wypada w siatce liczb. |
| tolerancja składu `nominal * 0.01` (132, 139) | **nie dla 94,0 m** | `94.0 * 0.01` to `0.9400000000000001`, a różnice liczb w okolicy 94,94 są wielokrotnościami 2^-46 — próg wymaga rozdzielczości 2^-53. Naiwne `94.0 + 94.0*0.01` daje `0.9399999999999977`, czyli POD progiem. Test bada granicę na **podmienionym rejestrze** z nominałem 100,0 m, bo `100.0 * 0.01 == 1.0` (potęga dwójki) i `abs(101.0 - 100.0) == 1.0` bez błędu. Prawdziwe 94,0 m jest w tym samym teście potwierdzone osobną asercją. |
| `AXIS_TOLERANCE_M = 1e-3` (204) | **nie dla żadnej realnej osi** | Przy osi 6686,74 m sąsiednie liczby są oddalone o 2^-40 (≈ 9,1e-13), więc żadna różnica nie wynosi dokładnie `1e-3`: `(oś + 1e-3) - oś` daje `0.0010000000002037268`. Granica `1e-3` jest osiągalna wyłącznie dla osi krótszej niż ~2 mm. Test podmienia tolerancję na `2^-10` (0,977 mm) — dokładną wielokrotność 2^-40 — i zaraz obok potwierdza, że w kodzie stoi nadal `1e-3`. |

Obie podmiany (rejestr M7, `AXIS_TOLERANCE_M`) dotyczą **wyłącznie arytmetyki progu**
i w obu testach stoi asercja pilnująca, że wartość produkcyjna została nietknięta.

## Dopisane testy

`tools/tests/test_visual.py` (8):

* `test_visual_png_reads_every_filter_type_the_spec_defines`
* `test_visual_png_paeth_breaks_ties_the_way_the_spec_requires`
* `test_visual_png_luminance_uses_all_three_colour_channels`
* `test_visual_png_reads_sixteen_bit_samples`
* `test_visual_png_accepts_an_alpha_channel_and_refuses_a_palette`
* `test_visual_png_skips_the_chunks_blender_puts_around_the_image`
* `test_visual_png_truncated_header_is_not_reported_as_a_missing_header`
* `test_visual_png_writers_clamp_out_of_range_values_to_black_and_white`

`tools/tests/test_shot_metadata_gate.py` (9):

* `test_train_tolerance_is_one_percent_and_the_boundary_itself_passes`
* `test_a_train_of_zero_length_is_reported_as_absent_not_as_a_wrong_size`
* `test_a_scene_of_one_mesh_object_is_still_a_scene`
* `test_size_must_follow_from_the_bbox_down_to_the_millimetre`
* `test_a_scene_axis_collapsed_to_zero_is_reported`
* `test_the_scene_may_touch_the_axis_exactly_at_the_micrometre_slack`
* `test_an_overhang_of_exactly_one_tunnel_cross_section_still_passes`
* `test_axis_length_off_by_exactly_the_tolerance_still_passes`
* `test_a_shot_exactly_one_metre_off_is_still_the_same_frame`

Każdy ma kontrolę negatywną: wejście zdrowe przechodzi **oraz** wejście zepsute
w jednym miejscu daje **dokładnie jeden** problem. Testy bramki metadanych liczą
problemy (`len(problems) == 1`), a nie tylko sprawdzają, że lista jest niepusta —
bramka przepuszczająca wszystko przeszłaby ten drugi wariant.

Pomocnicze `_png_bytes` w `test_visual.py` składa PNG bajt po bajcie i **liczy
filtrowanie w drugą stronę** niż `pngio._unfilter`, więc round-trip porównuje dwie
niezależne implementacje tej samej definicji z PNG-spec, a nie funkcję samą ze sobą.
