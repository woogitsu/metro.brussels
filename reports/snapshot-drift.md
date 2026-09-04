# Rozjazd snapshotów wobec `data/` — stan na 04.09.2026

**Snapshot repozytorium:** `377b59e` (`main`)
**Pobrania kontrolne:** 2026-09-04, 08:51–08:53 UTC

Pozycja 5.2 z `docs/TASKS.md`. Wynikiem jest **diff, nie podmiana**: `data/` zostaje
tylko do odczytu (reguła 6), pobrania idą do `build/drift/`, a decyzja, czy cokolwiek
podmieniać, należy do właściciela. Bez tego raportu nie ma na czym jej oprzeć.

Polecenia, którymi to powstało, są w sekcji „Jak to powtórzyć". Żaden z nich nie pisze
do `data/` — sprawdzone: `git status` po całym przebiegu pokazuje czyste drzewo, a
`build/` jest gitignored.

## Skrót

| źródło | co porównano | wynik |
|---|---|---|
| **GTFS STIB/MIVB** | suma SHA-256 pliku i 20 pól manifestu | **bez zmian** |
| **Shapefile'y STIB/MIVB** (`ACTU_LIGNES_BRUTES`) | suma SHA-256 pliku i 21 pól manifestu | **bez zmian**, ale dataset deklaruje się jako **wygasły** |
| **INSPIRE Rails** | liczby pochodne z parsera (brak sumy w `data/`) | **bez zmian**, okno ważności wygasłe **68 dni** |
| **OpenStreetMap** | relacje tras L1 | relacje istnieją, nazwy bez zmian; **dla statystyki relacyjnej nie ma w repo baseline'u** |
| **Stop Details** | — | **nie ma osobnego snapshotu**; `data/network/stops.json` jest wyprowadzone z GTFS |

Zero rozjazdu w treści danych. Trzy znaleziska, które nie są rozjazdem, ale są warte
decyzji, stoją w sekcji „Co z tego wynika".

## GTFS — bez zmian, co do bajtu

```
$ python3 tools/track/fetch_gtfs.py --out build/drift/stib_gtfs.zip \
      --manifest build/drift/gtfs-manifest.json
[POBRANO] …/api/gtfs/feed/stibmivb/static -> build/drift/stib_gtfs.zip (14543732 B)
[RAPORT] sha256=28c2fba48783e278d20f8f703759e3f729b72608d015e00d0f8215fa3b278bb6
[RAPORT] feed_version=2_20_20260831_010702 zakres=20260831..20260927
[RAPORT] calendar=20260831..20260927 services=338
[RAPORT] stops.txt: 2784   routes.txt: 89   trips.txt: 75696
[RAPORT] stop_times.txt: 1554901   shapes.txt: 269069
```

Diff manifestów, pole po polu:

```
identycznych pól: 20 z 21
  artifact_sha256, attribution, content_sha256, crs, dataset_version, etag,
  final_url, format, gtfs, input_sources, last_modified, manifest_version,
  mime_type, parser_version, requested_url, size_bytes, source_id,
  source_metadata, stats, transformations
RÓŻNI SIĘ  retrieved_at   "2026-09-01T10:35:09Z" -> "2026-09-04T08:51:40Z"
```

Jedyne różniące się pole to **data pobrania**, czyli metadana o samym pobraniu, a nie
o danych. `content_sha256` jest identyczna, więc identyczne są też wszystkie liczby
pochodne: `feed_version`, zakres kalendarza, 338 służb i liczby rekordów w dziesięciu
plikach członkowskich.

Kalendarz feedu obowiązuje **do 20260927**, czyli jeszcze 23 dni. To jedyne z czterech
źródeł, które dziś nie jest przeterminowane.

## Shapefile'y — bez zmian, ale dataset uważa się za wygasły

```
$ python3 tools/track/fetch_stib_shapes.py --out build/drift/stib_shapefiles.zip \
      --manifest build/drift/shapes-manifest.json
[POBRANO] …/api/datasets/stibmivb/static/shape-files -> … (856291 B)
[RAPORT] sha256=bc41483ba5e42d3d8b8b94e0adfc16791a609d3938d0ca1bd1791521279acd6d
[RAPORT] linie=172 przystanki=3952
[RAPORT] metro: 8 rekordów ['001m', '002m', '005m', '006m']
[RAPORT] CRS źródła: Belge_Lambert_1972
[RAPORT] okno ważności datasetu: ['02/03/2026'] .. ['28/08/2026']
```

```
identycznych pól: 21 z 22
RÓŻNI SIĘ  retrieved_at   "2026-09-01T10:48:05Z" -> "2026-09-04T08:51:58Z"
```

Tu jest znalezisko, którego suma kontrolna nie pokazuje, bo **nie jest rozjazdem między
`data/` a serwerem — jest właściwością samego datasetu**. Archiwum deklaruje w polach
`Date_debut`/`Date_fin` okno **02/03/2026 … 28/08/2026**, czyli zamknięte **7 dni przed
tym pomiarem**. STIB nadal serwuje ten sam plik, z tą samą sumą, i nie podmienił go na
nowszy — więc najświeższe dostępne shapefile'y są dziś danymi po terminie ważności
zadeklarowanym przez wydawcę.

Osiem rekordów metra na cztery kody linii (`001m`, `002m`, `005m`, `006m`) to po dwa
warianty na linię, tak samo jak w commitcie w `data/`.

## INSPIRE Rails — bez zmian, wygasłe od 68 dni

`data/` nie trzyma sumy kontrolnej tego źródła, więc porównanie idzie po **liczbach
pochodnych z parsera** wobec tych zapisanych w `reports/L1_A-track-spacing.md`.

```
$ python3 tools/track/inspire_rail.py --out build/drift/inspire-rail.json
[ROZSTAW] obiekty: 810 linków, 791 węzłów, 44 linii; metro: 130 linków
[ROZSTAW] okno ważności 2026-03-02 … 2026-06-28 — wygasłe
[ROZSTAW] referencje LinkSequence: 0/1036 rozwiązanych
[ROZSTAW] zgodność z osią (kierunek osi): mediana 0.068 m, P95 0.241 m, maks. 0.37 m
[ROZSTAW] tor osi: mediana 0.012 m (373 próbek); tor przeciwny: mediana -3.282 m (382 próbek)
[ROZSTAW] rozstaw 3.294 m (P05–P95 3.029–4.367 m), pół rozstawu 1.647 m
```

| liczba | w `reports/L1_A-track-spacing.md` | dziś |
|---|---|---|
| `tn-ra:RailwayLink` | 810 | **810** |
| `tn-ra:RailwayNode` | 791 | **791** |
| referencje `net:link xlink:href` | 1036, rozwiązanych 0 | **1036, rozwiązanych 0** |
| rozstaw torów | 3,294 m | **3,294 m** |
| pół rozstawu | 1,647 m | **1,647 m** |
| okno ważności | 2026-03-02 … 2026-06-28 | **2026-03-02 … 2026-06-28** |

Wszystkie sześć się zgadza, więc plik po drugiej stronie jest ten sam.

Jedna liczba w tamtym raporcie **postarzała się i nie jest to rozjazd danych**: pisał
o oknie zamkniętym „65 dni" wcześniej, bo mierzył 01.09.2026. Dziś to 68 dni.
Liczby liczone od „teraz" starzeją się w ciszy — dlatego stoi tu data pomiaru przy
każdej z nich.

## OpenStreetMap — relacje żyją, ale baseline'u dla tej statystyki nie ma

```
$ python3 tools/track/fetch_osm_routes.py --alignment data/track/L1_A.json \
      --relation 58240 --relation 7006075 --out build/drift/osm-L1_A.json
[OSM] relacje: 58240 (Metro 1: Gare de l'Ouest/Weststation → Stockel/Stokkel),
      7006075 (Metro 1: Stockel/Stokkel → Gare de l'Ouest/Weststation)
[OSM] way'ów: 118, węzłów: 1166

$ python3 tools/track/crosscheck_alignment.py --alignment data/track/L1_A.json \
      --osm-file build/drift/osm-L1_A.json --out build/drift/crosscheck-L1_A.json
[KONTROLA] osm: 118 way, pokrycie 100.0% (promień 50 m),
           odchyłka: mediana 0.94 m, P95 4.12 m, maks. 5.93 m
[KIERUNEK] 58240 …: 56 way, pokrycie 100.0%, mediana 0.97 m, P95 4.65 m, maks. 7.82 m
[KIERUNEK] 7006075 …: 63 way, pokrycie 100.0%, mediana 4.17 m, P95 8.77 m, maks. 12.92 m
```

Co się potwierdza: **obie relacje istnieją**, mają te same identyfikatory, tego samego
operatora (`STIB/MIVB`), ten sam `ref=1` i te same punkty końcowe co w commitcie.
Pokrycie osi jest pełne w promieniu 50 m dla każdego kierunku osobno.

**Czego NIE porównałem, i dlaczego jest to ważniejsze niż wygląda.** Tabela w
`reports/L1_A-crosscheck.md` podaje dla tych samych dwóch relacji „węzłów 214 / 229,
mediana 0,97 m / 3,88 m, maks. 26,31 m / 105,23 m". To **inna statystyka** niż powyższa:
tam liczono odsunięcie **węzłów OSM od osi**, tu liczy się odchyłkę **punktów osi od
way'ów OSM**. Widać to po liczbie próbek — `points_checked` wynosi 447, czyli tyle, ile
oś ma punktów, a nie 214 ani 229.

Mediana kierunku wschodniego wypada w obu 0,97 m i **to jest zbieżność, nie dowód
zgodności**. Maksima rozjeżdżają się o rząd wielkości (7,82 m wobec 26,31 m i 12,92 m
wobec 105,23 m), co dla dwóch różnych statystyk jest normalne, a dla jednej byłoby
alarmem. Pierwsza wersja tej sekcji wpisywała tę parę jako rozjazd danych — i była
nieprawdziwa.

Tamtej statystyki **nie da się dziś odtworzyć narzędziem z repozytorium**: żaden moduł
w `tools/` nie liczy odsunięcia węzłów OSM per relacja, a sam raport zaznacza, że wynik
„odtworzono niezależnie od raportu badawczego". Nie ma więc czego z czym porównać
i **nie zgaduję**. Liczby z tego przebiegu zapisuję jako baseline dla statystyki
punkt-osi-do-way'a, żeby następny przebieg miał już od czego odejmować.

Znacznik czasu danych OSM przesunął się z `2026-09-01T10:29:56Z` na
`2026-09-04T08:52:59Z`. Dla OSM to nie rozjazd, tylko żywe źródło — i jedyne z czterech,
przy którym zmiana treści między pobraniami jest oczekiwana, nie podejrzana.

## Stop Details — nie ma czego porównywać, i to jest poprawny wynik

Pozycja 5.2 wymienia Stop Details jako czwarte źródło. W `data/` **nie ma osobnego
snapshotu tego datasetu**: `data/network/stops.json` nosi wprost `$comment` „Stacje
metra wyprowadzone z feedu GTFS STIB/MIVB. Generowane przez
`tools/track/normalize_stops.py` — nie edytować ręcznie", czyli jest **pochodną GTFS**,
a nie drugim źródłem. Skoro GTFS jest bez zmian co do bajtu, `stops.json` też nie ma
z czego się rozjechać.

Dawny dataset Opendatasoft `stop-details-production` nie jest już serwowany — portal
`data.stib-mivb.brussels` zwraca 302 na `data.belgianmobility.io`, co jest opisane
w docstringu `tools/track/fetch_gtfs.py`. Wpisanie tu „sprawdzone, bez zmian" byłoby
nieprawdą o kroku, którego nie da się wykonać.

## Co z tego wynika — trzy rzeczy do decyzji

Żadna z nich nie jest rozjazdem danych i żadnej nie ruszam.

1. **Dwa z czterech źródeł nie mają w `data/` sumy kontrolnej.** GTFS i shapefile'y mają
   (`gtfs-manifest.json`, `shapes-manifest.json`); INSPIRE Rails i OSM nie mają żadnego
   commitowanego manifestu z `content_sha256`. Dla nich rozjazd da się wykryć **wyłącznie
   pośrednio**, przez liczby pochodne — a to znaczy, że zmiana, która nie rusza żadnej
   z tych liczb, przejdzie niezauważona. Manifest dla tych dwóch byłby osobnym zadaniem.

2. **Najświeższe dostępne shapefile'y są po zadeklarowanym terminie ważności** (7 dni),
   a INSPIRE Rails po nim od 68 dni. Nie ma nowszej wersji do pobrania — to nie zaległość
   w repozytorium, tylko stan po stronie wydawcy. Pytanie do decyzji brzmi: czy geometria
   z wygasłego okna nadal jest podstawą dla `data/track/`, i czy `data/network/sources.json`
   ma to odnotowywać jako ostrzeżenie, a nie tylko jako pole `dataset_validity`.

3. **Statystyka relacyjna OSM z `reports/L1_A-crosscheck.md` nie jest odtwarzalna
   z repozytorium.** Liczby 214/229 węzłów i mediany 0,97/3,88 m stoją w raporcie bez
   narzędzia, które by je wyliczyło — czyli następny człowiek albo agent nie ma jak
   sprawdzić, czy nadal są prawdziwe. To ta sama klasa problemu, którą pozycja 6.D4
   nazywa dla `reports/` w ogóle: wartość w raporcie musi dać się odtworzyć z repo.

## Jak to powtórzyć

```bash
mkdir -p build/drift
python3 tools/track/fetch_gtfs.py         --out build/drift/stib_gtfs.zip \
                                          --manifest build/drift/gtfs-manifest.json
python3 tools/track/fetch_stib_shapes.py  --out build/drift/stib_shapefiles.zip \
                                          --manifest build/drift/shapes-manifest.json
python3 tools/track/inspire_rail.py       --out build/drift/inspire-rail.json
python3 tools/track/fetch_osm_routes.py   --alignment data/track/L1_A.json \
                                          --relation 58240 --relation 7006075 \
                                          --out build/drift/osm-L1_A.json
python3 tools/track/crosscheck_alignment.py --alignment data/track/L1_A.json \
                                          --osm-file build/drift/osm-L1_A.json \
                                          --out build/drift/crosscheck-L1_A.json
```

Diff manifestów pole po polu robi się porównaniem `json.load` obu plików; różnica
wyłącznie na `retrieved_at` znaczy „bez zmian".

**Limity, o których trzeba wiedzieć przed powtórzeniem:** kanał BMC daje anonimowo
**100 żądań na dobę i 10 na minutę**, a przekroczenie zwraca HTTP 429
(`tools/track/fetch_gtfs.py`). Ten przebieg zużył **cztery** żądania: GTFS, shapefile'y,
INSPIRE Rails i jedno zapytanie Overpass, które idzie do innej usługi i nie liczy się
do tej puli. `--offline` w obu fetcherach liczy manifest dla pliku, który już leży
na dysku — do powtórnego policzenia sum nie trzeba pobierać niczego drugi raz.
