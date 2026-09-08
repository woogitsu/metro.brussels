# Droga zapasowa do OSM przez `api.openstreetmap.org` — i czy daje to samo co Overpass

**Zmierzone na commicie:** `750b501` (`main`) + niezacommitowane zmiany gałęzi
`claude/osm-api-zamiast-overpassa` — narzędzie, którym mierzono, powstaje w tym samym
commicie, co ten raport, więc SHA bazy jest tu jedynym SHA, jaki da się podać uczciwie.
**Data pomiaru:** 2026-09-08.
**Narzędzia:** `tools/track/crosscheck_alignment.py` (`--osm-source osm-api`),
`tools/track/surface_sections.py` (`--osm-file`).
**Licencja danych:** © OpenStreetMap contributors, ODbL 1.0.

Pozycja 6.B52. Pytanie tej pozycji jest o **drogę do danych**, nie o odpowiedź 6.B26:
czy da się wykonać zapytania, których 6.B26 potrzebuje, gdy Overpass milczy — i czy
droga zapasowa daje **te same obiekty**, co datowany snapshot Overpassa, na którym
stoi `reports/surface-vs-tunnel.md`.

---

## 1. Stan sieci w dniu pomiaru — trzy próby, wykonane

```
$ curl -sS -o /dev/null -w '%{http_code} %{time_total}\n' --max-time 30 <URL>

https://overpass-api.de/api/status                     000   9,764539 s
    curl: (35) Recv failure: Connection reset by peer
    proxy: {"kind":"ws_closed_mid_exchange","host":"overpass-api.de:443",
            "detail":"tunnel closed (code 1006, Connection ended) after 10s;
                      517 B sent, 39 B received, client reading"}
https://api.openstreetmap.org/api/0.6/capabilities     200   0,719571 s
https://data.mobility.brussels/geoserver/ogc/features/v1/collections/
    bm_public_transport%3AMetro/items?limit=10000       200   1,980599 s   215 439 B
    -> 156 obiektów
```

Overpass milczy nadal, i to nie „timeoutem", a zerwaniem połączenia na poziomie
tunelu proxy. Warunek z treści zadania — „jeśli Overpass odpowiada dziś HTTP 200,
przerwij" — **nie zachodzi**, więc decyzja właściciela o obejściu ma podstawę.

`data.mobility.brussels/api/geodata/v1/collections/` (ścieżka z opisu zadania) daje
**HTTP 404 po 1,645 s**; ścieżka faktycznie używana przez narzędzia projektu, ta wyżej,
daje HTTP 200. To nie jest awaria źródła, tylko nieaktualna ścieżka w opisie.

## 2. Dlaczego droga zapasowa musi być kaflowana

`/api/0.6/map` **nie ma języka zapytań**. Nie da się poprosić o `railway=subway` —
serwer odsyła całą zawartość prostokąta. Ma za to twardy limit obszaru, i on decyduje
o całej konstrukcji:

```
$ curl ".../api/0.6/map?bbox=4.40185,50.81210,4.42926,50.83312"   # całe bbox pakietu D
400   2,765142 s   95 B
You requested too many nodes (limit is 50000). Either request a smaller area, or use planet.osm
```

Bok kafla jest więc **pomiarem, nie próbami**. Trzy kafle wokół tego samego punktu
(4,41500 E / 50,82200 N, środek pakietu D):

| bok | węzłów | bajtów | ocena |
|---|---:|---:|---|
| 0,0012° | 1 259 | 371 335 | za drobny — mnoży liczbę żądań |
| **0,006°** | **8 012** | **2 394 402** | **wybrany: sześciokrotny zapas do limitu** |
| 0,0050° | 19 320 | 5 641 198 | 2,6× zapas, ale 2,4× większy transfer na kafel |

## 3. Przebieg drogi zapasowej na pakiecie D

```
$ python3 tools/track/crosscheck_alignment.py --alignment data/track/L5_D.json \
      --out build/osm-api/L5_D-crosscheck-osmapi.json \
      --osm-source osm-api \
      --osm-snapshot-out build/osm-api/L5_D-subway-osmapi.json \
      --urbis-file /tmp/urbis.json

[OSM-API] kafel 1/30 bbox=4.39759,50.80940,4.40358,50.81468: 1509120 B, 0 way railway=subway, razem 0
...
[OSM-API] kafel 8/30 bbox=4.40358,50.81468,4.40957,50.81996: 3008324 B, 47 way railway=subway, razem 75
...
[OSM-API] kafel 30/30 bbox=4.42754,50.83053,4.43353,50.83581: 1527172 B, 0 way railway=subway, razem 97
[ŹRÓDŁO] osm: api.openstreetmap.org/api/0.6/map — droga ZAPASOWA wg docs/07-open-data-research.md: bez języka zapytań, obszar pobierany kaflami, filtr railway=subway wykonany LOKALNIE
[ŹRÓDŁO] snapshot zapisany: build/osm-api/L5_D-subway-osmapi.json (pole osm_source = osm-api)
[OSM-API] 30 kafli po 0.006°, 66137960 B pobrane, kafli odrzuconych: 0
[KONTROLA] osm: 97 way, pokrycie 100.0% (promień 50 m), odchyłka na pokrytym odcinku: mediana 1.04 m, P95 2.97 m, maks. 3.91 m

real	1m12.554s
```

**30 kafli, 66 137 960 B (66,1 MB), 0 odrzuconych, 97 way'ów i 746 węzłów metra.**
Stosunek jest tu treścią, nie ciekawostką: 66 MB przesłano po to, żeby wyjąć 97
obiektów. Zapytanie Overpassa o ten sam prostokąt zwraca same way'e metra.

## 4. Porównanie krzyżowe ze snapshotem Overpassa

### 4.1 Czego nie ma w drzewie, i to trzeba powiedzieć pierwsze

Treść zadania mówi, że „w drzewie leży datowany snapshot Overpassa". **Nie leży.**
Sprawdzone wprost:

```
$ git ls-files | grep -iE "osm|overpass|snapshot"
reports/snapshot-drift.md
tools/data/snapshot_source.py
tools/tests/test_reference_snapshot.py
tools/tests/test_snapshot_source.py
tools/track/fetch_osm_routes.py

$ git ls-files '*.json' | xargs grep -l timestamp_osm_base
(pusto)

$ git log --all --diff-filter=A --name-only -- '*osm*'
(same pliki narzędzi, żadnego snapshotu)
```

`reports/surface-vs-tunnel.md` **powołuje się** na snapshot `build/osm-subway.json`
z `timestamp_osm_base = 2026-09-01T16:37:11Z`, 448 way'ów i 2920 odcinków — ale
`build/` jest gitignored i tego pliku nie ma. Porównanie „bajt w bajt" jest więc
niewykonalne, i to jest fakt o drzewie, nie o drodze zapasowej. Zostaje porównanie
**liczb, które snapshot po sobie zostawił** — i ono jest wykonalne w całości.

### 4.2 Liczby pochodne: pakiet D, siedem wartości, wszystkie zgodne

```
$ python3 tools/track/surface_sections.py --alignment data/track/L5_D.json \
      --out build/osm-api/L5_D-surface-osmapi.json --urbis-file /tmp/urbis.json \
      --osm-file build/osm-api/L5_D-subway-osmapi.json --skip-osm

[POWIERZCHNIA] PEŁNE POKRYCIE, ŹRÓDŁO = snapshot: osm-api: 258 punktów, 649 odcinków metra
[POWIERZCHNIA]   urbis=None|osm=poza_tunelem: 39
[POWIERZCHNIA]   urbis=None|osm=tunel: 11
[POWIERZCHNIA]   urbis=poza_tunelem|osm=poza_tunelem: 93
[POWIERZCHNIA]   urbis=poza_tunelem|osm=tunel: 4
[POWIERZCHNIA]   urbis=tunel|osm=poza_tunelem: 48
[POWIERZCHNIA]   urbis=tunel|osm=tunel: 63
[POWIERZCHNIA] zgodność 75.0% na 208 punktach; OSM bez tunelu na 180 (69.8%), przedziały [[59.9, 538.9], [763.5, 1257.5], [1422.2, 1916.2], [2230.4, 3398.1]]
[POWIERZCHNIA] najdalszy way metra od osi: 3.91 m
```

Wobec `reports/surface-vs-tunnel.md` §3 (snapshot Overpassa, 01.09.2026):

| wartość | snapshot Overpassa | droga zapasowa 08.09.2026 | |
|---|---:|---:|---|
| punktów osi | 258 | 258 | **zgodne** |
| porównywalnych | 208 | 208 | **zgodne** |
| zgodność źródeł | 75,0 % | 75,0 % | **zgodne** |
| UrbIS `niveau = 0` | 37,6 % | 37,6 % | **zgodne** |
| OSM: poza tunelem | 69,8 % | 69,8 % (180 pkt) | **zgodne** |
| UrbIS zawyża tunel | 48 | 48 | **zgodne** |
| przedziały bez tunelu | 60–539; 764–1258; 1422–1916; 2230–3398 | 59,9–538,9; 763,5–1257,5; 1422,2–1916,2; 2230,4–3398,1 | **zgodne** (raport zaokrągla) |

**Siedem na siedem.** Droga zapasowa daje na pakiecie D dokładnie ten sam pomiar co
snapshot Overpassa — łącznie z macierzą sprzeczności i z granicami przedziałów
podanymi do dziesiątej części metra.

### 4.3 Liczby obiektów: 97 wobec 448 i dlaczego to NIE jest rozjazd danych

Snapshot Overpassa miał **448 way'ów i 2920 odcinków** dla **całej sieci**. Droga
zapasowa dała **97 way'ów i 649 odcinków** dla **prostokąta jednego pakietu**. To są
dwa różne obszary, nie dwa różne odczyty tego samego obszaru: `crosscheck_alignment.py`
liczy bbox **z osi** (`query_bbox_lonlat`, margines 300 m), a snapshot z
`surface-vs-tunnel.md` powstał zapytaniem o całą sieć.

Pobranie całej sieci tą drogą jest **zmierzone i świadomie niewykonane**:

```
$ python3 - (bbox z sześciu osi data/track/L*.json)
cala siec bbox [4.26309, 50.80936, 4.46893, 50.9002]
  kafel 0.006 -> 560 kafli
  kafel 0.01  -> 210 kafli
  kafel 0.012 -> 144 kafli
```

**560 wywołań i około 1,2 GB** przy zmierzonym boku kafla. To cudza infrastruktura
i taki przebieg nie należy do tej pozycji — należy do decyzji właściciela. Kafel
0,012° zmniejszyłby liczbę żądań do 144, ale w gęstym centrum przekroczyłby limit
50 000 węzłów (w rejonie Beekkant w kwadracie 260 × 260 m leży osiem way'ów metra na
czterech poziomach, `surface-vs-tunnel.md` §2) — czyli byłby dobrany przez próby, a nie
przez pomiar.

### 4.4 Rozróżnienie przyczyn: (a) inne dane czy (b) OSM się zmienił

Przyrządem jest `version` i `timestamp` **każdego way'a** — pola, których Overpass
w `out geom` nie podaje, a droga zapasowa zachowuje właśnie po to:

```
$ python3 - build/osm-api/L5_D-subway-osmapi.json
way ów: 97
wezlow razem: 746
way ów z timestampem: 97
najstarszy edit: 2025-07-31T20:50:50Z
najnowszy edit : 2026-01-19T22:36:21Z
edytowane PO 2026-09-01T16:37:11Z: 0
rozklad tagu tunnel: {'yes': 17, None: 80}
rozklad layer     : {'-3': 6, None: 79, '-1': 8, '-2': 2, '1': 2}
```

**Przyczyna (b) jest wykluczona pomiarem, nie założeniem:** ani jeden z 97 way'ów nie
był edytowany po dacie snapshotu, a najnowsza edycja w tym zbiorze jest o **siedem
i pół miesiąca** starsza od niego. Przyczyna (a) jest wykluczona przez §4.2: siedem
wartości pochodnych zgadza się co do dziesiątej części metra, a taka zgodność nie
powstaje z innego zbioru obiektów.

Kontrola samego scalania kafli — way przechodzący przez granicę kafla:

```
$ curl ".../api/0.6/way/475903350/full"        200  0,773851 s  5401 B
wezlow w way (autorytatywnie): 24   wersja 5   2026-01-17T20:11:25Z
$ (ten sam way w snapshocie drogi zapasowej)
24 wezly, v5
```

`/api/0.6/map` zwraca way'e **kompletne**, także z węzłami leżącymi poza prostokątem,
więc scalenie po `id` jest dokładne i geometrii nie trzeba zszywać.

### 4.5 Czego zmierzyć nie umiem

- **Zgodności bajt w bajt ze snapshotem Overpassa** — snapshotu nie ma w drzewie (§4.1).
- **Zgodności zbiorów way'ów dla całej sieci** (448 wobec ?) — wymagałaby 560 wywołań
  i ~1,2 GB (§4.3). Porównanie jest wykonalne, ale nie za tę cenę bez decyzji.
- **Tego, czy Overpass i `/api/0.6/map` widzą tę samą chwilę bazy danych.** Droga
  zapasowa nie ma `timestamp_osm_base`; ma tylko daty poszczególnych way'ów. Dwa
  przebiegi kaflowe rozłożone w czasie mogą teoretycznie złapać różne stany, a
  jedno zapytanie Overpassa nie może. Na tym zbiorze różnicy nie ma (§4.4), ale to
  jest wynik pomiaru, nie właściwość metody.

## 5. Co dostało bramkę

`tools/tests/test_osm_api_fallback.py`, **23 testy, bez sieci**. Do 6.B52
`docs/07-open-data-research.md` nie miał na `tools/tests/` **ani jednej** bramki, choć
nazywa siebie źródłem prawdy o pochodzeniu danych — trzy testy tego modułu czytają
teraz jego treść, a host bierzą **z kodu** (`OSM_API_URL`, `OVERPASS_URL`), nie
z wpisanej tutaj stałej.

## 6. Dryf pokrycia mutacyjnego

Bramka `test_drift_report_mutation_count_is_the_one_the_tool_gives_today` zapaliła się
przy tym commicie i to jest jej robota:

```
FAIL test_drift_report_mutation_count_is_the_one_the_tool_gives_today:
  reports/mutation-drift.md rozjechał się z drzewem — przelicz audyt dla tych modułów:
  ['tools/track/crosscheck_alignment.py: raport mówi 19, narzędzie liczy 30']
```

Liczba mutacji zestawu starego (`operator,prog`) w tym module wzrosła **19 → 30**;
wiersz w `reports/mutation-drift.md` jest przeliczony, a kolumna ocalałych zostaje
nieprzeliczona, bo jest pomiarem z datą.

Przebieg **wykonany na drzewie czystym**, na commicie `7f116a4` — nie przed commitem
i nie z `--dirty`: `mutation_sweep.py` stosuje mutacje na kopii
`git worktree add --detach HEAD`, a listę liczy z drzewa roboczego, więc przy
`--dirty` są to **dwa różne pliki** (narzędzie samo to zapisuje w docstringu
`odcisk_tresci`) i wyniki policzone dla treści `750b501` podstawiłyby się pod
dzisiejsze mutacje po cichu.

```
$ python3 tools/tests/mutation_sweep.py --only tools/track/crosscheck_alignment.py \
      --operators operator,prog --workers 4 \
      --journal build/drift-6b52/crosscheck_alignment.jsonl

[MUTACJE] 30 mutacji do policzenia, 4 robotników, commit 7f116a4, klasy operator,prog
[MUTACJE] drzewo bazowe zielone, wyrocznia ma prawo mówić „zabita”
[MUTACJE] wykonywanych wierszy dotyczy 30 z 30 mutacji; pozostałe 0 siedzą w kodzie, którego zestaw nie uruchamia
[MUTACJE] rozstrzygniętych 30/30, zabitych 22, ocalałych 8 (w tym 0 nieuruchomionych), nierozstrzygniętych 0
  OCALAŁA  tools/track/crosscheck_alignment.py:330 operator `>` -> `>=`
  OCALAŁA  tools/track/crosscheck_alignment.py:330 prog `0` -> `1`
  OCALAŁA  tools/track/crosscheck_alignment.py:330 operator `>` -> `>=`
  OCALAŁA  tools/track/crosscheck_alignment.py:330 prog `1` -> `2`
  OCALAŁA  tools/track/crosscheck_alignment.py:349 operator `>` -> `>=`
  OCALAŁA  tools/track/crosscheck_alignment.py:483 operator `!=` -> `==`
  OCALAŁA  tools/track/crosscheck_alignment.py:574 operator `<` -> `<=`
  OCALAŁA  tools/track/crosscheck_alignment.py:574 operator `>` -> `>=`
```

**Ani jedna z 30 mutacji nie siedzi w kodzie, którego zestaw nie uruchamia** —
30 z 30 dotyczy wierszy wykonywanych, więc każda ocalała jest albo dziurą
w pokryciu, albo mutantem równoważnym, a nie „nikt jej nie odpalił".

Sześć z ośmiu ocalałych stoi w kodzie dopisanym w tym commicie i **dwie z nich były
prawdziwymi dziurami**. Zostały zamknięte, każda z celowaną kontrolą negatywną:

| wiersz | co to jest | wynik |
|---|---|---|
| **483** `if entry.get("status") != "ok"` | **dziura.** `==` zamienia stan zdrowy w chory i chory w zdrowy: dokleja „ok" do zdania o źródle sprawdzonym i **zdejmuje** „niedostępne" ze zdania o źródle, którego nie pobrano. Pozostałe testy patrzyły na treść zdania, nie na przedrostek | zamknięta testem `test_a_status_other_than_ok_is_prefixed_to_the_sentence_and_ok_is_not`; **KN-8**, mutacja nałożona wprost: `FAIL … 23/24, kod 1` |
| **330** `if index > 1 and sleep_s > 0` | **dziura, cztery mutacje.** Kontrakt „nie strzelamy w OSM seriami bez oddechu" nie był sprawdzany przez nic: `index >= 1` każe czekać przed pierwszym kaflem, `sleep_s >= 0` woła `sleep(0)` przy wyłączonej przerwie | zamknięta testem `test_the_throttle_waits_between_tiles_and_never_before_the_first`; **KN-9**: `index >= 1` → `FAIL … [0.5, 0.5, 0.5]`, `sleep_s >= 0` → `FAIL … [0, 0]`, oba `24/25, kod 1` |
| **349** `len(way["geometry"]) > len(previous["geometry"])` | **mutant równoważny.** `>=` znaczy „way tej samej długości z późniejszego kafla wygrywa" — a `/api/0.6/map` zwraca way'e kompletne, więc te dwa są identyczne co do węzła (potwierdzone w §4.4 przez `way/475903350/full`). Nie ma czego zaobserwować | zostaje, nazwana |
| **574** `t < 0` / `t > 1.0` | **NIE MOJE.** Przycięcie rzutu na odcinek w `_distance_to_polyline`, kod sprzed tego commita. `test_crosscheck_projection_is_clamped_exactly_at_the_segment_ends` stoi na `t = 1.005`, więc nie odróżnia progu w samym 1,0 | poza zakresem tej pozycji (§4.10), zgłoszone niżej |

## 7. Kontrole negatywne — WYKONANE

Każda z czyszczeniem `__pycache__` i z `md5sum` po przywróceniu.

**KN-1 · droga podstawowa przy nieosiągalnym Overpassie (prawdziwa sieć, bez mutacji).**

```
[ŹRÓDŁO] osm: niedostępne — overpass-api.de/api/interpreter — droga PODSTAWOWA wg docs/07-open-data-research.md, filtr railway=subway po stronie serwera
[KONTROLA] osm: niedostępne — <urlopen error [Errno 104] Connection reset by peer>
real 0m6.950s      kod wyjścia: 0
```

Niedostępność jest **wynikiem**: kod 0, 6,95 s, źródło nazwane, powód zapisany.

**KN-2 · droga zapasowa przy nieosiągalnym źródle** (`OSM_API_URL` → host `.invalid`,
kafel 0,02° dla skrócenia przebiegu):

```
[OSM-API] kafel 1/4 ODMOWA (źródło niedostępne): <urlopen error Tunnel connection failed: 502 Bad Gateway>
[OSM-API] kafel 2/4 ODMOWA (źródło niedostępne): ...
[OSM-API] kafel 3/4 ODMOWA (źródło niedostępne): ...
[OSM-API] kafel 4/4 ODMOWA (źródło niedostępne): ...
[ŹRÓDŁO] osm: brak danych — api.openstreetmap.org/api/0.6/map — droga ZAPASOWA ...
[KONTROLA] osm: brak danych
real 0m1.528s      kod wyjścia: 0
```

Cztery kafle odrzucone, **każdy wymieniony**, status `brak danych`, kod 0, 1,53 s —
nie zawieszenie i nie ciche zero way'ów.

**KN-3 · ten sam podmieniony `OSM_API_URL` a bramka** — host czytany z kodu, więc
podmiana adresu bez podmiany dokumentu i zdania zapala dwa testy:

```
FAIL test_every_osm_route_has_a_sentence_that_names_its_host
FAIL test_the_source_doc_records_the_fallback_with_its_host_and_its_limits: api.openstreetmap.invalid
21/23 przeszło        (przywrócone: md5 4fec4e1fd748cc9e0bf2307e1b0c7cce)
```

**KN-4 · przełącznik zdjęty** (`--osm-source` wycięty z `parse_args`, 477 znaków):

```
FAIL test_main_names_the_primary_route_differently_from_the_fallback: 'Namespace' object has no attribute 'osm_source'
FAIL test_main_prints_a_source_line_that_names_the_fallback_host: main() odmówiło uruchomienia: 2
FAIL test_offline_refuses_both_routes_without_touching_the_network: main() odmówiło uruchomienia: 2
FAIL test_offline_refuses_urbis_too_and_says_so: 'Namespace' object has no attribute 'osm_source'
19/23 przeszło        kod: 1
```

Ta kontrola **znalazła usterkę we własnej bramce**, i to jest jej treść. W pierwszym
przebiegu `SystemExit` z argparse uciekł z testu jako `BaseException`, którego
`test_all.py` nie łapie (`except Exception`): przebieg skończył się kodem **2** na
trzecim teście i osiem następnych **nie wykonało się wcale**. Ta sama rodzina, którą
`test_fetchers.py` opisuje dla `--offline`. `_run_main` łapie teraz `SystemExit`
i zamienia go w `AssertionError`; wynik wyżej jest z przebiegu PO utwardzeniu.

**KN-5 · mutacja zdania o źródle** (host zdjęty ze zdania drogi zapasowej,
`"api.openstreetmap.org/api/0.6/map — droga ZAPASOWA…"` → `"ok, pobrano — droga
ZAPASOWA…"`):

```
FAIL test_every_osm_route_has_a_sentence_that_names_its_host
FAIL test_main_prints_a_source_line_that_names_the_fallback_host
21/23 przeszło        kod: 1
```

**KN-6 · wypis o źródle usunięty z `main()` całkowicie:**

```
FAIL test_main_names_the_primary_route_differently_from_the_fallback
FAIL test_main_prints_a_source_line_that_names_the_fallback_host
21/23 przeszło        kod: 1
```

**KN-7 · `surface_sections.py` znów nazywa KAŻDY snapshot Overpassem**
(`snapshot_source_label` → `return "overpass snapshot"`):

```
FAIL test_surface_sections_reads_the_declared_origin_of_the_snapshot
22/23 przeszło        kod: 1
```

**Sumy po przywróceniu wszystkich siedmiu:**

```
4fec4e1fd748cc9e0bf2307e1b0c7cce  tools/track/crosscheck_alignment.py
78835814a4c74e9613ccd4e81d23f26c  tools/track/surface_sections.py
572dd8deb59d37210a45be23ff0276bf  docs/07-open-data-research.md
```

— identyczne z sumami przed kontrolami. `tools/tests/test_osm_api_fallback.py` różni
się **celowo**: to utwardzenie `SystemExit` z KN-4.

## 8. Czego ten raport NIE rozstrzyga

- **Nie rozstrzyga 6.B26.** Zadaniem tej pozycji jest droga do danych. Pomiar
  drogą zapasową pokazuje wprawdzie, że najciaśniejszy łuk pakietu D leży w przedziale
  `2230,4–3398,1 m`, którego OSM nie widzi jako tunel — ale pole „Skończone, gdy"
  pozycji 6.B26 żąda raportu z nazwanym źródłem **po hierarchii**, wraz z odległością
  do najbliższego przedziału tunelowego w każdym źródle osobno i z łukiem
  porównawczym z innej osi. Tego tu nie ma i nie oznaczam 6.B26 jako rozstrzygniętej.
- **Nie zmienia niczego w `data/`.** Ani snapshotu (którego nie ma), ani
  `data/network/sources.json` — wpis, którego rejestr potrzebuje, jest zgłoszony jako
  pozycja **6.D52**, nie dopisany.
- **Nie dopisuje `--offline` do pozostałych sześciu narzędzi sięgających do sieci.**
  To jest praca, którą ma uzasadnić 6.D51, i osobna pozycja; tutaj `--offline` dostało
  wyłącznie narzędzie, które ta pozycja i tak rusza.
- **Nie pobiera całej sieci drogą zapasową** — 560 wywołań i ~1,2 GB, patrz §4.3.
- **Nie domyka dwóch ocalałych mutacji w `_distance_to_polyline`** (wiersz 574,
  przycięcie rzutu na odcinek). To kod sprzed tego commita, a próg trafiony dokładnie
  w 1,0 wymaga własnej fikstury — praca poza zakresem tej pozycji (§4.10) i warta
  osobnego wpisu.
