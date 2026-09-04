# Triaż mutacji: łańcuch wczytywania danych źródłowych

**Data pomiaru:** 2026-09-03

**Zmierzone na:** `737d592` (stan `main` w chwili rozpoczęcia).
**Narzędzie:** `tools/tests/mutation_sweep.py` z gałęzi `mutacje-raport-przeliczony`
(nie jest częścią tego commita — po pomiarze usunięty z drzewa).
**Bramka:** `python3 tools/tests/test_all.py`.

Objęte moduły to cztery kroki tej samej drogi: `crs.py` decyduje, **gdzie** w Brukseli
leży sieć, `fetch_osm_routes.py` — **które** relacje OSM w ogóle wejdą do danych,
`shapefile.py` — **czy** bajty ze STIB dadzą się odczytać, `normalize_stops.py` —
**ile** stacji z tego wychodzi i czy rozbieżność z dokumentacją zostanie zgłoszona.

## Wynik

| moduł | ocalałych przed | ocalałych po | zabitych tym commitem | pokrycie po |
|---|---|---|---|---|
| `tools/track/crs.py` | 8 / 8 | 6 / 8 | 2 | 25,0 % |
| `tools/track/fetch_osm_routes.py` | 9 / 9 | **0 / 9** | 9 | **100 %** |
| `tools/track/shapefile.py` | 6 / 17 | **1 / 17** | 5 | **94,1 %** |
| `tools/track/normalize_stops.py` | 3 / 9 | **0 / 9** | 3 | **100 %** |
| **razem** | **26 / 43** | **7 / 43** | **19** | **83,7 %** |

Wszystkie **siedem** mutacji, które zostały, jest zaklasyfikowanych jako niedających się
zaobserwować albo obserwowalnych poniżej progu znaczenia — z wykonanym uzasadnieniem,
nie z przeczytania kodu. Żadna nie jest odłożoną dziurą.

## Jak klasyfikowałem

Nie przez czytanie. Oryginał i mutant były ładowane **obok siebie**
(`importlib.util.spec_from_file_location` na pliku tymczasowym) i przepuszczane przez
tę samą baterię wejść. Kluczowa liczba w każdym wierszu poniżej to **ile wejść trafiło
DOKŁADNIE w granicę, na której orzekam**. „Zero różnic" nie znaczy nic, jeżeli bateria
w punkt równości nie trafiła — losowe wejścia z definicji w niego nie trafiają, a to
właśnie punkt równości odróżnia `<` od `<=`.

Tam, gdzie w granicę trafić się **nie da**, werdykt brzmi „równoważna" dopiero po
pokazaniu, dlaczego nie da się: podaję najbliższe osiągalne wartości po obu stronach
progu i odstęp między nimi.

**Pułapka zmiennoprzecinkowa.** `abs((6700.0 + 0.01) - 6700.0)` daje 0,010000000000218,
czyli **nad** progiem — naiwny test „na granicy" granicy nie dotyka. Odejmowanie jest
dokładne tylko wtedy, gdy jedna strona jest zerem albo obie leżą blisko tej samej
potęgi dwójki. Tam, gdzie granicę trzeba było trafić w liczbach zmiennoprzecinkowych
(`crs.py:145`), nie konstruuję wartości równej progowi — **odczytuję** ją: próg podaję
jako float policzony dokładnie tym samym wyrażeniem co wartość porównywana, więc obie
strony są równe co do ostatniego bitu. Droga jest opisana w docstringu testu.

## `tools/track/crs.py` — 8 ocalałych, 2 zabite

| wiersz | mutacja | werdykt | uzasadnienie i trafienia w granicę |
|---|---|---|---|
| 145 | `abs(dx) < tol` → `<=` | **realna dziura → zabita** | Przy `abs(dx)` równym progowi co do bitu i `abs(dy)` mniejszym mutant przerywa pętlę w iteracji **zerowej** i zwraca `LAMBERT_INVERSE_SEED` — punkt oddalony o **2 112,6 m** od pytanego. Trafień w granicę: **1 na 1** (próg odczytany, nie skonstruowany). Test: `test_crs_lambert_inverse_ignores_a_lone_x_residual_equal_to_the_tolerance`. |
| 145 | `abs(dy) < tol` → `<=` | **realna dziura → zabita** | To samo dla drugiego porównania; granica musi stać na `dy`, a `dx` być od niej mniejsze, inaczej pierwsze porównanie zatrzyma warunek i mutacja przejdzie niezauważona. Trafień w granicę: **1 na 1**. Test: `..._a_lone_y_residual_equal_to_the_tolerance`. |
| 153 | `abs(determinant) < 1e-12` → `<=` | **równoważna** | Strażnik rozbieżności. Bateria 509 celów (siatka sieci co 2,5 km, zero, ±1e6, 1e9, biegun odwzorowania) dała **3 414** wyznaczników: min **1,32e+6**, max 3,69e+17. Trafień dokładnie w 1e-12: **0**. Skan po szerokości pokazuje, dlaczego trafić się nie da: `\|det\|` schodzi z **3,14e+2** (lat = 90−1e-8) wprost do **0,0** (lat = 90) — między nimi nie ma osiągalnej wartości, więc nie ma jej też w (0, 1,01e-12). Strażnik jest w praktyce testem „wyznacznik jest zerem", a zero spełnia i `<`, i `<=`. |
| 153 | `1e-12` → `1.01e-12` | **równoważna** | Ta sama bateria: trafień w pas [1e-12, 1,01e-12): **0**, i z powodu wyżej trafić w niego nie można. |
| 234 | `abs(step) < 1e-14` → `<=` | **równoważna** | Newton w `_authalic_to_geodetic`. Bateria 40 000 wartości `beta` (siatka po całym zakresie + losowe) = **154 114** kroków; kroków równych 1e-14: **0**. Że to nie przypadek, pokazuje bisekcja po sąsiednich floatach `beta`: dwie **sąsiadujące osiągalne** wartości kroku to 9,946931628522577e-15 i 1,064496191824346e-14, odstęp **6,98e-16**, czyli 4,4e+14 ulp-ów. Krok przy zbieżności jest resztą po katastrofalnym skróceniu i jest skwantowany grubiej, niż wynosi odległość do progu — 1e-14 leży w dziurze między dwoma możliwymi wynikami. |
| 234 | `1e-14` → `1.0100000000000001e-14` | **obserwowalna, poniżej progu znaczenia** | Tu granicę bateria **trafiła**: **23 z 40 000** wartości `beta` mają krok w paśmie [1e-14, 1,01e-14), więc mutant przerywa iterację o krok wcześniej. Zmierzony skutek: `max \|Δφ\| = 5,11e-15 rad = 3,3e-8 m`, czyli **33 nanometry**. Zamknięcie tego wymagałoby asercji bit w bit na wyniku `math.log`/`math.sin`, czyli przypięcia zachowania libm konkretnej maszyny — a sama transformacja BD72↔WGS84 ma w EPSG **deklarowaną dokładność 1 metra**. Świadomie nie zamykam; zapis tutaj jest tym, co zostaje zamiast testu. |
| 244 | `rho < 1e-12` → `<=` | **równoważna** | `east` i `north` są odległościami od 4 321 000 i 3 210 000 m, więc `rho` liczone z ich różnic jest skwantowane: najmniejsza **niezerowa** osiągalna wartość to **4,658593770712678e-10**, czyli **466 razy** powyżej progu. Bateria 599 punktów (początek odwzorowania, jego sąsiedzi co 1 ulp, Bruksela, cała Europa): trafień dokładnie w 1e-12 — **0**, i trafić się nie da. Strażnik jest testem „rho jest zerem"; zero spełnia oba operatory. Trafień w `rho == 0,0`: **6**. |
| 244 | `1e-12` → `1.01e-12` | **równoważna** | Jak wyżej: trafień w pas [1e-12, 1,01e-12) — **0**, przy odstępie osiągalnych wartości 4,66e-10. |

**Kontrola negatywna, która nie jest mutacją z listy:** próg `1e-12` w wierszu 244
zastąpiony przez `-1.0` (czyli strażnik wyłączony) wywraca trzy testy, w tym nowy
`test_crs_laea_origin_is_the_only_point_taking_the_degenerate_branch`, z
`ZeroDivisionError`. To dowód, że nowy test naprawdę wchodzi w gałąź zdegenerowaną,
a nie tylko obok niej przechodzi.

Dołożone przy okazji, choć żadnej mutacji nie zabijają — bo mierzą to, czego mutacje
progów nie ruszają: residuum inwersji na siatce całej sieci, round-trip LAEA 3035 od
Brukseli po równik i zgodność skrótu `laea3035_to_lambert72` ze złożeniem, które
udaje.

## `tools/track/fetch_osm_routes.py` — 9 ocalałych, 9 zabitych

Cały moduł nie był dotknięty żadnym testem poza `route_ref_from_id` i `seed_bbox`,
bo `discover_relations` i `fetch_relation_ways` wołają sieć. Wołają ją jednak przez
**jedną** funkcję — `api_get` — więc wystarczy ją podstawić. Żaden nowy test nie rusza
sieci.

| wiersz | mutacja | werdykt | uzasadnienie i trafienia w granicę |
|---|---|---|---|
| 81 | `e.get("type") == "way"` → `!=` | **realna dziura → zabita** | Filtr wycinka `/map`. Każdy obiekt w atrapie ma **inną** relację macierzystą o tym samym `ref`, więc mutant nie zwraca pustki, tylko **cudzą relację** — wynik, który przeszedłby każdą kontrolę spójności. To ta sama pomyłka, przez którą rozstaw torów z ekstraktu bboxowego wyszedł 11 m zamiast 3,9 m (`reports/L1_A-crosscheck.md`). |
| 81 | `railway == "subway"` → `!=` | **realna dziura → zabita** | Jak wyżej; mutant zaczepia się o way tramwajowy i o way bez tagów. |
| 88 | `tags.get("type") != "route"` → `==` | **realna dziura → zabita** | Way metra wisi też w `route_master` i w multipoligonach; mutant bierze dokładnie te, których `full.json` nie ma geometrii torów. |
| 88 | `tags.get("route") != "subway"` → `==` | **realna dziura → zabita** | Mutant bierze relację `route=tram` o tym samym `ref`. |
| 90 | `str(tags.get("ref")) != str(route_ref)` → `==` | **realna dziura → zabita** | Pod Arts-Loi biegną trasy 1, 2, 5 i 6; `ref` jest jedynym kryterium, które je rozdziela. Mutant zwraca cudzą linię z poprawnym kształtem. |
| 101 | `e["type"] == "node"` → `!=` | **realna dziura → zabita** | Słownik współrzędnych wolno budować wyłącznie z węzłów; test pilnuje też **kolejności** węzłów w way'u, bo odwrócona geometria ma ten sam zbiór punktów i tę samą długość. |
| 104 | `element.get("type") != "way"` → `==` | **realna dziura → zabita** | Relacja trasy ma członków-węzłów (`stop_position`, `platform`); przepuszczone dałyby odchyłkę liczoną od peronów zamiast od torów. |
| 108 | `len(geometry) < 2` → `<=` | **realna dziura → zabita** | **Granica całkowitoliczbowa, trafiona wprost**: `len(geometry)` równe dokładnie **2**. Way dwuwęzłowy to normalny odcinek tunelu; podniesienie progu wyrzuca go po cichu — snapshot nadal się zapisuje i nadal ma way'e, tylko trasa ma dziurę. Test podaje obie strony: 2 zostaje, 1 wypada. Trafień w granicę: **1 na 3 way'e w atrapie**. |
| 108 | `2` → `3` | **realna dziura → zabita** | Ta sama granica, ten sam test. |

## `tools/track/shapefile.py` — 6 ocalałych, 5 zabitych

| wiersz | mutacja | werdykt | uzasadnienie i trafienia w granicę |
|---|---|---|---|
| 25 | `len(data) < 100` → `<=` | **realna dziura → zabita** | Nagłówek `.shp` ma **dokładnie 100** bajtów i sam w sobie jest poprawnym plikiem (warstwa bez geometrii to normalny eksport z GIS-a). Mutant myli plik pusty z uciętym. Granica całkowitoliczbowa, trafiona wprost, obie strony w teście: 100 przechodzi, 99 odpada. Trafień w granicę: **1 na 2 wejścia**. |
| 25 | `100` → `101` | **realna dziura → zabita** | Ta sama granica, ten sam test. |
| 36 | `offset + 8 <= len(data)` → `<` | **równoważna** | Jedyny przypadek, w którym te dwa warunki się różnią, to `offset + 8 == len(data)`, czyli osiem bajtów ogona za ostatnim rekordem. Wtedy `content = data[offset+8 : ...]` startuje **na końcu bufora**, więc jest pusty **zawsze** — niezależnie od zadeklarowanej długości rekordu — i sterowanie idzie w `if not content: continue`. Żaden kształt nie powstaje, `offset` wychodzi poza bufor, pętla i tak się kończy. Sprawdzone wykonaniem na 4 plikach; trafień dokładnie w granicę: **3**, różnic w wyniku: **0** (także przy `length_words = 99`, czyli ogonie kłamiącym o swojej długości). Test `test_alignment_shapefile_ignores_a_record_header_flush_with_the_end_of_file` zostaje mimo werdyktu — pilnuje zachowania, nie mutacji. |
| 63 | `len(data) < 32` → `<=` | **realna dziura → zabita** | Nagłówek `.dbf` ma **dokładnie 32** bajty i tyle wystarczy, żeby odczytać `record_count`, `header_length`, `record_length`. Obie strony w teście: 32 przechodzi, 31 odpada. Trafień w granicę: **1 na 2 wejścia**. |
| 63 | `32` → `33` | **realna dziura → zabita** | Ta sama granica, ten sam test. |
| 68 | `offset < len(data)` → `<=` | **realna dziura → zabita** | Tablica pól `.dbf` kończy się bajtem `0x0D`, którego w pliku uciętym **nie ma**. Bez warunku „jest jeszcze bufor" plik urwany dokładnie na końcu tablicy pól daje `IndexError` — wyjątek, który nie mówi wołającemu nic o niekompletnym archiwum; kontrakt modułu to `ShapefileError` albo poprawny odczyt. Granica: `offset` równe `len(data)` co do jednego bajtu (32 B nagłówka + 32 B deskryptora = 64 B). Trafień w granicę: **1 na 1**. |

## `tools/track/normalize_stops.py` — 3 ocalałe, 3 zabite

Wszystkie trzy siedziały w `main()`, a testy modułu wołały wyłącznie `normalize()` —
więc cała warstwa raportowania, ta, która ma **krzyczeć**, gdy dane rozjeżdżają się
z `docs/00-network-data.md`, nie była dotknięta niczym.

| wiersz | mutacja | werdykt | uzasadnienie i trafienia w granicę |
|---|---|---|---|
| 250 | `declared == summary["metro_stations"]` → `!=` | **realna dziura → zabita** | `matches_declared` steruje jedynym ostrzeżeniem, jakie ten moduł wypisuje. Odwrócenie zamienia raport w jego przeciwieństwo: narzędzie milczy dokładnie wtedy, gdy dane rozjechały się z dokumentacją, i alarmuje, gdy wszystko gra. W pliku wyjściowym objaw jest niewidoczny — stacje są te same, zmienia się jedno pole i jedna linia na stdout. Test pokazuje obie strony granicy równości na tym samym feedzie: deklaracja 1 (zgadza się) i 2 (nie zgadza się). Trafień w granicę: **1 na 2 wejścia**. |
| 264 | `len(rejected) > 10` → `>=` | **realna dziura → zabita** | To jedyna linia, z której czytający dowiaduje się, że lista na ekranie jest **ucięta** i że pełna leży w `--report`; bez niej dziesiąte odrzucenie wygląda jak ostatnie. Granica całkowitoliczbowa, trafiona wprost: przy **dokładnie 10** odrzuceniach dopisku ma nie być (mutant wypisuje „i 0 więcej"). Trafień w granicę: **1 na 2 wejścia**. |
| 264 | `10` → `11` | **realna dziura → zabita** | Druga strona tej samej granicy: przy **dokładnie 11** odrzuceniach mutant przemilcza to jedenaste. Ten sam test. |

## Czego świadomie nie zrobiłem

- **Nie tknąłem kodu produkcyjnego.** Ani jednej linii w `tools/track/`. Commit zawiera
  wyłącznie testy i ten raport.
- **Nie zamykam `crs.py:234` (próg `1e-14`).** Mutacja jest obserwowalna — pokazałem to
  liczbą, nie domysłem — ale jej skutek to 33 nanometry przy transformacji o deklarowanej
  dokładności 1 metra, a jedyny test, który by ją złapał, przypinałby bity `math.log`
  konkretnej implementacji libm. Uznaję to za gorsze niż ocalała mutacja.
- **Nie dopisywałem testów do modułów spoza zadania**, mimo że sweep pokazuje ocalałe
  także gdzie indziej.

## Co zauważyłem przy okazji i czego NIE naprawiłem

Dwie rzeczy, obie w `crs.py`, obie **poza zakresem tego zadania** — naprawa byłaby
zmianą kodu produkcyjnego, czyli drugim zadaniem. Zapisuję z liczbami, żeby nie
przepadły.

1. **`lambert72_to_wgs84` nie sprawdza zbieżności i po cichu zwraca wynik niezbieżny.**
   Dla `(1e9, 1e9)` zwraca `lat = -46040,3°` przy residuum **1,41e+9 m**. Dla dokładnego
   bieguna odwzorowania `(150000,013, 5400088,438)` zwraca `lon = 395,8°` przy residuum
   **2 435 m**. Docstring mówi, że residuum jest **mierzone** — ale mierzy je osobna
   funkcja `lambert_inverse_residual_m()`, którą wołający musi sobie zawołać sam.
   Kto tego nie zrobi, dostanie liczby wyglądające jak współrzędne. W obszarze
   udokumentowanym (siatka sieci co 3 km) residuum nie przekracza 1e-3 mm i tego
   pilnuje nowy `test_crs_lambert_inverse_converges_across_the_whole_network_extent`.
2. **`_authalic_to_geodetic` przy `beta` bliskim ±90° wychodzi z pętli niezbieżny.**
   Osiem iteracji nie wystarcza: największy zaobserwowany krok **kończący** pętlę to
   2,25e-11 rad ≈ **0,14 mm**. Poniżej jakiegokolwiek znaczenia dla tego projektu
   (LAEA 3035 jest tu używane dla Brukseli), ale pętla nie sygnalizuje, że skończyła
   z powodu wyczerpania iteracji, a nie z powodu zbieżności.
