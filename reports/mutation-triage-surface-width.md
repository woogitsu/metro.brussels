# Triaż ocalałych mutacji: `surface_sections.py` i `tunnel_width.py`

**Zmierzone na commicie:** `b5bcf34`

Stan: **2026-09-03**. Narzędzie: `tools/tests/mutation_sweep.py` (gałąź
`mutacje-raport-przeliczony`, plik roboczy — **nie jest** commitowany).
Mutowany jest kod pod testem, nie testy. Zestaw kontrolny: `python3 tools/tests/test_all.py`.

## 1. Wynik w liczbach

| moduł | mutacji | ocalałych PRZED | ocalałych PO | zabitych dopisanymi testami |
|---|---:|---:|---:|---:|
| `tools/track/surface_sections.py` | 29 | **24** | **1** | 23 |
| `tools/track/tunnel_width.py` | 28 | **22** | **2** | 20 |
| **razem** | **57** | **46** | **3** | **43** |

Pokrycie liczone z rozstrzygniętych: 17,2 % → **94,7 %**. Żadna mutacja w obu
przebiegach nie wyszła nierozstrzygnięta, więc żadna liczba nie jest zawyżona przez
przebieg ubity przed podsumowaniem.

Zestaw testów urósł z **692** do **719** przypadków, wszystkie zielone.

## 2. Skąd brała się dziura

Dwa wzorce, oba widoczne dopiero po zestawieniu tabeli:

1. **Progi były sprawdzane obok granicy, nie na granicy.** Istniejący test odległości
   way'a używał `NEAREST_MAX_M + 1.0`; test halo stacyjnego sprawdzał
   `120.0 <= chainage <= 480.0`, czyli warunek prawdziwy i dla `<`, i dla `<=`. Takie
   wejście nie odróżnia progu ostrego od nieostrego, bo nigdy go nie dotyka.
2. **Dwie funkcje najwyższego poziomu nie miały żadnego testu.** `surface_sections.survey()`
   (cała klasyfikacja i cała macierz rozbieżności) i `tunnel_width.main()` (jedyna droga,
   którą wynik trafia do człowieka) były sprawdzone wyłącznie pośrednio — czyli wcale.
   Stąd osiem ocalałych w jednym module w blokach `full_coverage` i `agreement_off_portal`.

Na pułapkę zmiennoprzecinkową natrafiłem w trzech miejscach i w każdym rozwiązanie
jest opisane w docstringu testu: **różnica dwóch liczb jest dokładna tylko wtedy, gdy
jedna strona jest zerem albo gdy obie leżą blisko tej samej potęgi dwójki.**
`abs((6700.0 + 0.01) - 6700.0)` daje `0.010000000000218`, czyli NAD progiem — test
„na granicy" zbudowany tak nigdy granicy nie dotyka. Dlatego:

* `range_position` sprawdzam na 640/760/840/960 wobec przedziału [700, 900] i halo 60 —
  wszystko całkowite, więc odejmowanie jest dokładne;
* tolerancję `1e-6` w `probe_chainages` stawiam na przedziale `[-1.0, 1.0]`, którego
  środek wynosi **równo 0.0**, więc `abs(0.0 - 1e-6)` jest bitowo równe literałowi z modułu;
* `ray_distance` dostaje pierścień, dla którego mianownik przecięcia wynosi **równo 1.0**
  (kierunek `(0, 1)`, krawędź `ex = -1.0`, `ey = 0.0`), przez co `t` wychodzi bitowo równe
  `y` krawędzi, a `u` bitowo równe jej `x` — bez żadnego zaokrąglenia po drodze.

## 3. Znalezione usterki kodu produkcyjnego

**Żadnej.** Kod produkcyjny obu modułów nie został zmieniony ani o znak. Wszystkie 43
zabicia pochodzą z dopisanych testów. Dwie rzeczy zauważone przy okazji, świadomie
nietknięte, są w §6.

## 4. Tabela: `tools/track/surface_sections.py`

24 ocalałe przed, 1 po.

| wiersz | mutacja | werdykt | uzasadnienie |
|---:|---|---|---|
| 118 | `<=` → `<` (lewa granica) | **zabita** | `range_position(640.0, [[700,900]])` — kilometraż równy `low - halo` co do bitu; oryginał daje `portal`, mutant `poza`. Test `test_surface_range_position_hits_the_halo_boundary_exactly`. |
| 118 | `<=` → `<` (prawa granica) | **zabita** | To samo dla `high + halo` = 960.0: `portal` wobec `poza`. |
| 119 | `<=` → `<` (przy `low`) | **zabita** | `abs(760.0 - 700.0) == 60.0` dokładnie; oryginał `portal`, mutant `srodek`. |
| 119 | `<=` → `<` (przy `high`) | **zabita** | `abs(840.0 - 900.0) == 60.0`; `portal` wobec `srodek`. |
| 144 | `>=` → `>` (krok wewnętrzny) | **zabita** | Siatka co 100 m i krok 300 m: sondy padają na 0/300/600/900, mutant na 0/400/800/1200. Test `test_surface_probe_step_fires_at_a_distance_exactly_equal_to_the_step`. |
| 144 | `>=` → `>` (krok zewnętrzny) | **zabita** | Oba warunki są IDENTYCZNE dla punktów poza przedziałem, więc rozdziela je dopiero `step_inside > step_outside` — regime osiągalny z CLI. Test `test_surface_probe_outside_step_fires_at_its_own_exact_boundary`. |
| 151 | `>` → `>=` | **zabita** | Środek przedziału `[-1, 1]` to równo 0.0, sonda na `1e-6`: różnica bitowo równa progowi. Oryginał środka nie dopisuje, mutant dopisuje. |
| 151 | `1e-6` → `1.01e-6` | **zabita** | Ta sama konstrukcja z sondą na `1.005e-6` — wartość mieści się między starym a nowym progiem. |
| 158 | `<=` → `<` (`sa <= target`) | **zabita** | `target = 0.0` to jedyny kilometraż równy `sa` pierwszego odcinka. Mutant nie dopasowuje żadnego odcinka i po cichu zwraca OSTATNI punkt osi. |
| 158 | `<=` → `<` (`target <= sb`) | **ocalała — remis bez znaczenia** | Zmierzone, nie przeczytane: 401 osi (losowe w skali ±500 m i w skali Lambert 72, oś z krokiem pochłanianym przez kilometraż, duplikaty, zygzaki), każda ze wszystkimi węzłami i `węzeł ± 1e-9` jako celem. Oryginał bierze koniec wcześniejszego odcinka (`a + 1.0·(b-a)`), mutant początek następnego (`b`). To ten sam punkt; **największa zmierzona różnica położenia to 8,04·10⁻¹⁴ m**. Test przybijający tę różnicę przybijałby zaokrąglenie, nie zachowanie. |
| 158 | `>` → `>=` (`sb > sa`) | **zabita** | Zdublowany punkt osi daje odcinek zerowej długości; przy `>=` interpolacja liczy `0.0 / 0.0` i przebieg pada `ZeroDivisionError`. Test `test_surface_point_at_skips_a_zero_length_segment_instead_of_dividing_by_it`. |
| 202 | `<` → `<=` | **zabita** | Dwa way'e w tym samym śladzie, różnie otagowane. Remis rozstrzyga o TREŚCI wyniku (`tunnel=yes` wobec braku tagu), więc determinizm „pierwszy wygrywa" jest tu wynikiem, nie kosmetyką. Punkt zapytania przepuszczony przez obieg WGS84↔Lambert 72, żeby odległość wyszła równo 0,0. |
| 219 | `!=` → `==` | **zabita** | Cała ścieżka `--osm-file` nie miała testu. Snapshot z węzłem i z way'em bez geometrii: oryginał `['11']`, mutant `['33']` albo `[]`. |
| 222 | `!=` → `==` | **zabita** | Snapshot z tramwajem: oryginał `['11']`, mutant `['22']` — tramwaj wchodzi do klasyfikacji metra. |
| 252 | `<` → `<=` | **zabita** | Ten sam remis na ścieżce pełnego pokrycia; odcinki podawane wprost w Lambert 72, więc odległość jest równo 0,0 bez obiegu. |
| 264 | `<=` → `<` | **zabita** | Way odległy dokładnie o `NEAREST_MAX_M`: oryginał `zgodne`, mutant `jedno_zrodlo`. Istniejący test używał wyłącznie `NEAREST_MAX_M + 1.0`. |
| 299 | `==` → `!=` | **zabita** | Test całego `survey()` na lokalnych snapshotach: `niveau0_points == 7`, przedział `[[800.0, 1400.0]]`. |
| 323 | `==` → `!=` | **zabita** | `full_coverage.osm_surface_points == 8`, `osm_surface_pct == 25.8`. |
| 334 | `==` → `!=` | **zabita** | `full_coverage.agreement_pct == 96.8` (mutant liczy sprzeczności zamiast zgodności). |
| 340 | `==` → `!=` | **zabita** | `full_coverage.osm_surface_ranges_m == [[800.0, 1500.0]]`. |
| 343 | `==` → `!=` | **zabita** | `len(full_coverage.contradictions) == 1` i jej kilometraż 1500,0 — mutant wsadza tam wszystko, co sprzeczne NIE jest. |
| 384 | `!=` → `==` | **zabita** | `comparable_off_portal == 4` przy `comparable_probes == 6`; mutant zostawia wyłącznie sondy przyportalowe. |
| 404 | `==` → `!=` | **zabita** | `agreement_off_portal_pct == 75.0` wobec `agreement_pct == 50.0` — dwie różne liczby, więc odwrócenie widać. |
| 432 | `==` → `!=` | **zabita** | Przebieg `main()` z `--skip-osm`: żadna sonda nie może być sprzeczna, więc oryginał nie wypisuje ani jednej linii `SPRZECZNE`, a mutant wypisuje sześć. Kontrola negatywna sprawdza, że reszta raportu jednak leci na konsolę. |

## 5. Tabela: `tools/track/tunnel_width.py`

22 ocalałe przed, 2 po.

| wiersz | mutacja | werdykt | uzasadnienie |
|---:|---|---|---|
| 48 | `y1 > y` → `>=` | **zabita** | Punkt o `y` równym `y` krawędzi poziomej. Przy `>=` krawędź zaczyna się liczyć i `(y - y1)/(y2 - y1)` dzieli przez zero — mutant pada `ZeroDivisionError`. |
| 48 | `y2 > y` → `>=` | **zabita** | To samo wejście, druga strona porównania. |
| 48 | `x < xin` → `<=` | **zabita** | Punkt dokładnie na ścianie bocznej (`x == 600.0`): oryginał `False` (granica jest na zewnątrz), mutant `True`. Ma znaczenie, bo `measure()` odrzuca punkty należące do dwóch poligonów naraz. |
| 61 | `<` → `<=` | **zabita** | Mianownik równy **dokładnie** `1e-12`: kierunek `(1, 0)` i krawędź o `ey = 1e-12 - 0.0` (jedna strona odejmowania jest zerem, więc różnica jest dokładna). Źródło promienia stoi w kolumnie ściany pionowej, żeby to trafienie odpadło na epsilonie bliskim i nie przykryło wyniku: oryginał 5,0 m, mutant 10,0 m. |
| 61 | `1e-12` → `1.01e-12` | **zabita** | To samo wejście — `1e-12` leży w oknie [stary próg, nowy próg). |
| 65 | `t > 1e-6` → `>=` | **zabita** | Pierścień z mianownikiem równym 1.0, przez co `t` jest bitowo równe `y` krawędzi. `t = 1e-6`: oryginał `None`, mutant `1e-06`. |
| 65 | `1e-6` → `1.01e-6` | **zabita** | Ten sam pierścień z `t = 1.005e-6`: oryginał trafia, mutant nie. |
| 65 | `-1e-9 <= u` → `<` | **zabita** | `u` bitowo równe `x1` krawędzi; `u = -1e-9` to trafienie w koniec krawędzi. Poligony UrbIS są łamanymi, więc promień prostopadły do osi regularnie trafia w wierzchołek. |
| 65 | `u <= 1.0 + 1e-9` → `<` | **zabita** | To samo dla drugiego końca; literał `1.0 + 1e-9` w teście jest tą samą operacją co w module, więc wartości są bitowo zgodne. |
| 65 | `t < maximum` → `<=` | **zabita** | `maximum = 4.0` przy `t = 4.0`: zasięg jest wyłączny, oryginał `None`, mutant `4.0`. |
| 100 | `<=` → `<` | **zabita** | Pierścień zwinięty do punktu ma obwód równo 0,0: oryginał `None`, mutant `0.0` — czyli „najwęższy tunel w sieci" wzięty z niczego. |
| 100 | `0.0` → `0.001` | **zabita** | Pierścień o obwodzie ~0,5 mm: oryginał zwraca liczbę, mutant `None`, a `survey()` po cichu pomija takie poligony. |
| 104 | `<` → `<=` | **zabita** | Kwadrat 10×10: `(P/2)² − 4A` wynosi **równo 0.0** (400 − 400). Oryginał zwraca 10,0 (pierwiastek równania), mutant 5,0 (gałąź awaryjna `2A/P`) — dwukrotna różnica w wyniku pomiaru. |
| 104 | `0.0` → `0.001` | **zabita** | To samo wejście: wyróżnik równy zeru wpada w nowe okno i wynik spada z 10,0 na 5,0. |
| 120 | `<` → `<=` | **zabita** | `math.hypot(1e-9, 0.0)` zwraca bitowo `1e-9`. Pierścień dwupunktowy ma obie krawędzie na progu: oryginał `0.0`, mutant `None`. |
| 120 | `1e-9` → `1.01e-9` | **zabita** | To samo wejście — `1e-9` wpada w nowe okno. |
| 172 | `==` → `!=` | **zabita** | Gałąź `MultiPolygon` nie miała testu; mutant zwraca pustą listę i obiekt znika z przeglądu bez komunikatu. |
| 194 | `<` → `<=` | **zabita** | Próbka o kilometrażu równym `halo` (120,0 m — dokładnym, bo oś ma punkty co 20 m). Istniejący test sprawdzał `120.0 <= chainage`, co jest prawdziwe dla obu wariantów. |
| 199 | `<` → `<=` | **ocalała — nieosiągalna** | Strażnik długości wektora „prawo" ramki RMF. Zmierzone: 39 osi w baterii różnicującej (pionowe, helisy, korkociąg, przegięcia, duplikaty, losowe 3D z ziarnem 20260903) — **0 wejść różnicujących**; dodatkowo 3400 osi celowo prawie pionowych, gdzie najmniejsze `hypot(prawo_x, prawo_y)` wyniosło **5,79·10⁻⁴**, czyli **578 886 razy próg**. Strukturalnie: pierwsza ramka ma `right = unit(cross(t, up))` z `z = 0`, więc długość w planie wynosi równo 1; kolejne powstają z podwójnego odbicia wektora jednostkowego i zejście poniżej `1e-9` wymagałoby ramki odchylonej od pionu o mniej niż nanoradian. |
| 199 | `1e-9` → `1.01e-9` | **ocalała — nieosiągalna** | Ta sama bateria, ten sam wynik: 0 wejść różnicujących. Okno [1e-9, 1,01e-9) jest o sześć rzędów wielkości poniżej wartości, jakie ta wielkość w ogóle przyjmuje. |
| 222 | `<=` → `<` | **zabita** | Szerokość równa `RUNNING_TUNNEL_MAX_M` (15,0 m): oryginał liczy próbkę jako szlakową, mutant ją odrzuca i zaniża górny kraniec widełek. Istniejący test używał 8,8 m i 40 m — obu daleko od progu. |
| 312 | `==` → `!=` | **zabita** | Przebieg `main()` na lokalnym snapshocie: oryginał wypisuje `min 9.40 m ... mediana 9.40 m`, mutant nie wypisuje ani jednej liczby, choć JSON zostaje poprawny. Kontrola negatywna: węższy poligon zmienia liczbę i na konsoli, i w pliku naraz. |

## 6. Zauważone przy okazji, nietknięte

1. **`nearest_subway` i `nearest_segment` porównują surową odległość z zaokrągloną.**
   Warunek brzmi `distance < best["distance_m"]`, a `best["distance_m"]` to
   `round(distance, 2)`. Way odleglejszy o mniej niż pół centymetra może więc wygrać
   z bliższym, bo porównuje się z wartością zaokrągloną w górę. Nie jest to mutacja
   z tego przeglądu i nie mieści się w zadaniu, więc kodu nie ruszyłem — ale to
   właśnie ta własność zmusiła testy remisu do przepuszczenia punktu przez pełny
   obieg WGS84↔Lambert 72, żeby odległość wyszła równo 0,0.
2. **`point_at` przy zdublowanym punkcie osi** zwraca poprawny wynik tylko dzięki
   strażnikowi `sb > sa`; sam strażnik nie był testowany, co teraz jest naprawione.
   Osobne pytanie — czy oś ze zdublowanym punktem w ogóle powinna przechodzić
   `validate.py` — zostawiam otwarte, bo to decyzja projektowa, nie triaż.
