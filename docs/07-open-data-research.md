# Otwarte źródła danych i research

Stan researchu: **31.08.2026**.

Ten dokument określa hierarchię źródeł dla danych, których nie ma jeszcze w `data/network/`.
Maszynowy rejestr źródeł znajduje się w `data/network/sources.json`.

## Hierarchia źródeł

1. **STIB/MIVB Open Data i oficjalne publikacje STIB** — dane operacyjne, GTFS, przebieg linii, przystanki, stan wdrożeń i tabor.
2. **Brussels Mobility / Paradigm / UrbIS** — geometria tuneli i stacji, wejścia, warstwy przestrzenne i wysokości powierzchni Regionu Brukselskiego.
3. **Belgian Mobility Open Data Portal** — oficjalna warstwa dystrybucji i niezależna kontrola feedów STIB, m.in. GTFS, NeTEx i INSPIRE Rails.
4. **OpenStreetMap** — szczegóły torowe, rozjazdy, wejścia, perony i kontrola krzyżowa.
5. **Dokumentacja producenta / prasa branżowa** — parametry techniczne, gdy źródło operatora nie jest publiczne.
6. **Wikipedia, fanowskie mapy i repozytoria GitHub** — wyłącznie trop lub kontrola, nigdy jedyne źródło faktu.

Jeżeli dwa źródła są sprzeczne, **nie uśredniaj**. Zapisz rozbieżność, zachowaj provenance
obu wejść i preferuj źródło wyżej w hierarchii. Większa szczegółowość geometrii nie oznacza
automatycznie większej wiarygodności.

## Zasady dostępu, licencji i provenance

- Każdy nowy fakt lub artefakt pochodny ma `source_id` zgodny z `data/network/sources.json`.
- Każde pobranie danych zapisuje datę/czas, finalny URL po redirectach i hash wejścia zgodnie z T-114.
- Klucze API, `Ocp-Apim-Subscription-Key`, bearer tokens, cookies i inne sekrety **nie trafiają**
  do repo, manifestów ani logów.
- Metadane publicznego datasetu nie gwarantują, że każdy endpoint pobierania jest anonimowy.
  Jeżeli usługa wymaga autoryzacji, zapisujemy to jako właściwość dostępu i konfigurujemy sekret
  poza repo.
- Dużych lub szybko zmieniających się dumpów GTFS, GPKG, SHP, LAS i podobnych nie commitujemy.
  Commitujemy małe, deterministyczne artefakty pochodne oraz provenance.
- Przy transformacji CRS zapisujemy **CRS źródłowy i docelowy**. Nie zakładamy CRS na podstawie
  rozszerzenia pliku lub przybliżonego zakresu współrzędnych.
- Dataset regionalny może być dostępny w różnych projekcjach zależnie od usługi, m.in. WGS84,
  Lambert 72, Lambert 2008 albo Web/Pseudo-Mercator. Pipeline ma odczytać metadane konkretnego
  wejścia i wykonać jawną transformację.

## STIB/MIVB Open Data

> **Korekta 2026-09-01 (T-110).** Portal `data.stib-mivb.brussels` został wygaszony.
> Każda sprawdzona ścieżka — `/`, `/explore/dataset/<nazwa>/`, `/api/explore/v2.1/…`,
> `/api/records/1.0/search/…`, a także `terms/terms-and-conditions.pdf` — zwraca
> **HTTP 302 na `https://data.belgianmobility.io/`**. Dawne identyfikatory datasetów
> Opendatasoft (`gtfs-files-production`, `stop-details-production`,
> `shapefiles-production`) **nie są już serwowane**; URL-e w sekcjach poniżej zachowano
> jako zapis historyczny researchu z 31.08.2026.
>
> Zweryfikowane, anonimowe endpointy zastępcze (bez klucza API, HTTP 200):
>
> | dane | endpoint |
> |---|---|
> | GTFS static | `https://api-management-discovery-production.azure-api.net/api/gtfs/feed/stibmivb/static` |
> | Stop details | `…/api/datasets/stibmivb/static/StopDetails` |
> | Stops by line | `…/api/datasets/stibmivb/static/stopsByLine` |
> | Shapefiles | `…/api/datasets/stibmivb/static/shape-files` |
> | INSPIRE Rails | `…/api/datasets/stibmivb/static/rail` |
>
> Licencja kanału dystrybucji: **CC BY 4.0**,
> `https://data.belgianmobility.io/en/terms.html`, wymagana atrybucja
> `Source: STIB-MIVB - Open Data - <data aktualizacji>`. Limity anonimowe:
> **100 żądań/dobę i 10/minutę**, powyżej HTTP 429.
>
> Feed **NeTEx EPIP** z katalogu BMC (`epip-stibmivb-bmc-latest.xml`) zwraca **HTTP 401**
> z `WWW-Authenticate: Bearer` (Azure AD). Zapowiadana w tym dokumencie kontrola krzyżowa
> NeTEx jest więc obecnie **niewykonalna anonimowo**.

### Shapefiles — podstawowe źródło przebiegu sieci

Dataset `shapefiles-production`:

https://data.stib-mivb.brussels/explore/dataset/shapefiles-production/

STIB opisuje go jako dane zawierające podstawową strukturę przestrzenną sieci:
**przebieg linii i pozycje przystanków** dla komercyjnych wariantów tras.

**Wniosek:** T-111 nie buduje osi wyłącznie z OSM. Najpierw pobiera geometrię STIB,
a OSM, UrbIS i INSPIRE Rails służą do kontroli i doprecyzowania topologii. Shapefiles
nie są jednak automatycznie geometrią tor-po-torze ani profilem pionowym.

### GTFS

Dataset `gtfs-files-production`:

https://data.stib-mivb.brussels/explore/dataset/gtfs-files-production/api/

GTFS jest źródłem prawdy dla kolejności przystanków, service patterns i rozkładów,
ale nie wystarcza do modelowania tunelu tor po torze. `stops.txt` nie jest licznikiem
fizycznych stacji: T-110 musi uwzględnić `location_type`, `parent_station`,
warianty peronów i wielojęzyczne nazwy.

### Stop Details i realtime

- `stop-details-production` — ID, nazwa FR/NL, geolokalizacja.
- `vehicle-position-rt-production` — pozycje pojazdów; STIB publikuje dane realtime.
- `waiting-time-rt-production` — czasy oczekiwania.
- `travellers-information-rt-production` — prace, zdarzenia i zakłócenia.

Realtime może później służyć do kalibracji czasów przejazdu, postoju, częstotliwości
i zachowania ruchu liniowego. Snapshot realtime zawsze wymaga timestampu i nie może
nadpisywać danych historycznych bez daty odniesienia.

### Licencja STIB Open Data

Warunki:

https://data.stib-mivb.brussels/terms/terms-and-conditions.pdf

Warunki STIB dopuszczają ponowne wykorzystanie informacji, także komercyjne, oraz ich
adaptowanie i łączenie z własnym produktem, przy zachowaniu wymaganej atrybucji i daty
aktualizacji. Nie oznacza to automatycznej zgody na kopiowanie całej identyfikacji
wizualnej, dzieł sztuki, fotografii, map, fontów ani innych chronionych zasobów.
Polityka projektu pozostaje w `docs/03-legal.md`.

## Belgian Mobility Open Data Portal

Katalog STIB/MIVB:

https://data.belgianmobility.io/en/data.html?agency=stibmivb

Portal jest ważny nie dlatego, że ma zastąpić STIB, lecz dlatego, że udostępnia kilka
standardowych reprezentacji tych samych danych i pozwala wykrywać niespójności
między feedami.

### GTFS Static

Portal publikuje statyczny GTFS STIB i wskazuje aktualizację dzienną.

**Rola:** kontrola dostępności aktualnego feedu i niezależny kanał dystrybucji.
Fakty o sieci nadal preferują pierwotny dataset STIB.

### NeTEx EPIP

Portal publikuje dla STIB/MIVB feed **NeTEx EPIP**, wskazując aktualizację dzienną.

NeTEx jest użyteczny jako niezależna kontrola:
- struktury przystanków i miejsc postoju;
- semantyki linii i service patterns;
- relacji między obiektami, które w GTFS bywają reprezentowane płasko;
- wielojęzycznych nazw i identyfikatorów, jeżeli występują w feedzie.

**Nie jest** automatycznie źródłem dokładniejszej geometrii toru. T-110 może używać
NeTEx do wykrywania rozbieżności, ale nie powinien po cichu zastępować nim GTFS.

### INSPIRE Rails

Portal publikuje również **INSPIRE Rails** dla STIB/MIVB i wskazuje aktualizację tygodniową.

**Rola:** niezależna kontrola infrastruktury szynowej względem:
1. STIB Shapefiles;
2. regionalnego UrbIS/Brussels Mobility;
3. OpenStreetMap.

Jeżeli przebieg INSPIRE różni się od Shapefiles, T-111 zapisuje statystykę odchyłek
i źródła obu geometrii. Nie wybiera automatycznie „bardziej gładkiej” linii.

### Licencja i dostęp

Portal opisuje własną dystrybucję w modelu CC BY 4.0; przy wykorzystaniu danych operatora
zachowujemy również warunki i atrybucję źródła pierwotnego, jeżeli mają zastosowanie.
Część usług/API może wymagać klucza lub innego mechanizmu autoryzacji. Endpoint bez
autoryzacji w dniu researchu nie jest gwarancją, że pozostanie taki na zawsze.

## Brussels Mobility / Paradigm / UrbIS

### Warstwa `Metro`

https://data.mobility.brussels/en/info/Metro/

Warstwa `bm_public_transport:Metro` jest wyciągiem obiektów UrbIS typu:
- `MS` — stacja metra;
- `MT` — tunel metra.

Jest publikowana przez Paradigm na licencji **CC0** i stanowi niezależne regionalne
źródło geometrii stacji/tuneli.

OGC API Features używane w researchu:

https://data.mobility.brussels/geoserver/ogc/features/v1/collections/bm_public_transport%3AMetro/items

**Ograniczenie:** obiekt `MT` nie jest automatycznie osią toru, a pole poziomu względnego
nie jest publiczną niweletą toru. T-112 nie może zamienić `niveau` na metry bez dodatkowego źródła.

### Wejścia do metra — `metro_access`

Metadane:

https://data.mobility.brussels/en/info/0aa53fcf-939f-49a3-9a91-b9ec475be30d/

Dataset `bm_public_transport:metro_access` pochodzi ze STIB i jest publikowany jako
**CC0**.

**Rola:**
- kotwice wejść stacji na powierzchni;
- kontrola tekstowych opisów wyjść publikowanych przez STIB;
- punkt startowy do późniejszego modelowania połączenia powierzchnia → stacja.

**Nie wolno wyprowadzać z punktu wejścia:**
- głębokości peronu;
- kształtu korytarzy;
- liczby kondygnacji;
- dokładnej pozycji windy lub schodów wewnątrz stacji.

Niektóre regionalne usługi pobierania mogą wymagać bearer tokenu. Sekret pozostaje
poza repo i nie może pojawić się w URL-u manifestu.

### UrbIS Topo — linie tuneli

Metadane:

https://data.mobility.brussels/en/info/23248797-1974-497d-b176-2d5045bbe681/

Dataset `bm_urbis_topo:tunnel_line`, typ `BR04L`, jest publikowany jako **CC0**.

**Rola:** kontrola regionalnych obiektów tunelowych, portali i kontekstu powierzchniowego.

**Ograniczenie:** jest to ogólna warstwa tuneli w topografii UrbIS. Nie traktujemy jej
jako osi tunelu metra ani toru bez potwierdzenia zgodności obiektu z siecią STIB.

### LiDAR lotniczy 2021

Metadane federalnego katalogu:

https://data.gov.be/fr/datasets/ff1124e1-424e-11ee-b156-00090ffe0001

Paradigm publikuje trójwymiarową chmurę punktów z nalotu 2021 dla Regionu Brukselskiego,
w formacie LAS, na licencji **CC BY 4.0**.

**Rola:**
- wysokość i geometria powierzchni;
- kontekst budynków i infrastruktury naziemnej;
- kontrola portali i odkrytych odcinków;
- ground reference dla późniejszego T-112/T-212.

**Twarde ograniczenie:** lotniczy LiDAR nie obserwuje podziemnego toru. Nie używamy go
do „wyliczania” głębokości stacji ani tuneli, których sensor nie widział.

### UrbIS Digital Surface Model

Metadane:

https://data.gov.be/en/datasets/8c2d921e-6a53-11ed-bfb5-010101010000

DSM jest rastrową reprezentacją powierzchni i obiektów naziemnych dla Regionu.
Jest lżejszą warstwą wejściową niż pełna chmura punktów, gdy potrzebujemy tylko
kontekstu wysokościowego.

**Rola:**
- powierzchnia nad tunelem;
- osadzenie wejść/portali;
- szybkie generowanie kontekstu terenu.

**Ograniczenie:** DSM nie daje profilu pionowego podziemnego toru. Licencję i konkretny
endpoint pobierania odczytujemy z bieżących metadanych datasetu w momencie pobrania.

## OpenStreetMap

OSM pozostaje przydatny dla:
- `railway=subway`;
- relacji `route=subway`;
- rozjazdów i łącznic;
- `stop_position`, `platform`, `stop_area`;
- wejść do stacji;
- tagów `tunnel` i `layer`.

Nie używamy OSM jako jedynego źródła osi, jeśli istnieje oficjalna geometria STIB
lub regionalna. Zachowujemy atrybucję ODbL, timestamp danych i hash zapytania/
ekstraktu użytego przez pipeline.

### Dwie drogi do OSM: Overpass (podstawowa) i `/api/0.6/map` (ZAPASOWA)

> **Dopisane 2026-09-08 (6.B52), decyzja właściciela z tego samego dnia.** Wewnątrz
> klasy 4 tej hierarchii OSM ma **dwie drogi dostępu i nie są one równorzędne.**
> Wyboru dokonuje się **jawnie**, przełącznikiem `--osm-source` w
> `tools/track/crosscheck_alignment.py`, a wypis i pole `osm.source` w pliku wyniku
> nazywają drogę z osobna dla każdego przebiegu. Przełączenia automatycznego tu nie
> ma i to jest wybór: raport, który nie mówi, którą drogą poszedł, nie da się odnieść
> do tej hierarchii, a wygląda identycznie jak raport, który to mówi.

**Droga podstawowa — Overpass API.**

```
https://overpass-api.de/api/interpreter        way["railway"="subway"](bbox); out geom;
```

Jedno zapytanie, filtr po stronie serwera, `timestamp_osm_base` w odpowiedzi.
To jest droga właściwa i pozostaje domyślną wartością przełącznika.

**Droga zapasowa — surowe API OpenStreetMap.**

```
https://api.openstreetmap.org/api/0.6/map?bbox=west,south,east,north
```

*Kiedy jej wolno użyć.* Wyłącznie wtedy, gdy Overpass jest nieosiągalny — i to
**zmierzone**, nie założone. Pomiar z 08.09.2026 z kontenera agenta:
`overpass-api.de/api/status` → **HTTP 000 po 9,76 s** (`Recv failure: Connection
reset by peer`; proxy zapisało `ws_closed_mid_exchange` dla `overpass-api.de:443`),
`api.openstreetmap.org/api/0.6/capabilities` → **HTTP 200 po 0,72 s**,
`data.mobility.brussels/geoserver/…/bm_public_transport:Metro/items` → **HTTP 200
po 1,98 s, 215 439 B, 156 obiektów**. Jedno źródło leży, dwa stoją: „brak sieci"
nie jest w tym środowisku stanem zero-jedynkowym.

*Co daje.* Ten sam zbiór obiektów co zapytanie Overpassa **w tym samym prostokącie**:
way'e `railway=subway` z pełną geometrią i tagami `tunnel`/`layer`, w kształcie
odpowiedzi `out geom`, więc `--osm-file` w `surface_sections.py` czyta to bez
rozgałęzień. Do tego **`version` i `timestamp` każdego way'a**, których Overpass
w `out geom` nie podaje — a to jedyny przyrząd pozwalający odróżnić „droga zapasowa
pobrała co innego" od „OSM zmienił się od daty snapshotu".

*Czego NIE daje, i to jest tu ważniejsza połowa wpisu.*

1. **Nie ma języka zapytań.** Nie da się poprosić o `railway=subway`. Serwer odsyła
   całą zawartość prostokąta — ulice, budynki, tramwaj, perony — a filtr wykonuje się
   **lokalnie**, w `parse_osm_map_xml`. Każdy filtr przeniesiony na naszą stronę jest
   naszym błędem, gdy się pomyli; przy Overpassie tego ryzyka nie ma.
2. **Twardy limit obszaru: 50 000 węzłów na wywołanie.** Całe bbox jednego pakietu
   w jednym wywołaniu daje `HTTP 400 — You requested too many nodes (limit is 50000)`
   (zmierzone na pakiecie D, 2,77 s). Obszar trzeba więc dzielić na **kafle**; bok
   0,006° zmierzono na 8012 węzłów i 2,39 MB, czyli sześciokrotny zapas do limitu.
3. **Nieporównywalnie większy transfer.** Pakiet D: **30 kafli i 66 137 960 B** (66,1 MB)
   po to, żeby wydobyć **97 way'ów i 746 węzłów** metra. Zapytanie Overpassa o ten sam
   prostokąt zwraca same way'e metra. Stosunek nie jest tu szczegółem: pobranie w ten
   sposób **całej sieci** (bbox sześciu osi, 0,206° × 0,091°) wymagałoby przy tym
   kaflu **560 wywołań i około 1,2 GB** — i dlatego całą sieć tą drogą pobiera się
   **tylko po decyzji właściciela**, nie przy okazji. To cudza infrastruktura.
4. **Nie ma `timestamp_osm_base`.** Snapshot z tej drogi nie ma jednej daty odniesienia
   dla całego zbioru; ma tylko daty poszczególnych way'ów.

*Warunek powrotu.* Droga zapasowa znika z użycia, gdy
`https://overpass-api.de/api/status` odpowiada z tego środowiska **HTTP 200**. Warunek
jest sprawdzalny jednym poleceniem i ma być sprawdzony **przed** każdym użyciem
`--osm-source osm-api`:

```bash
curl -sS -o /dev/null -w '%{http_code} %{time_total}\n' --max-time 30 \
    https://overpass-api.de/api/status
```

*Provenance.* Snapshot z tej drogi **deklaruje** pole `osm_source: osm-api`, a
`surface_sections.py` czyta tę deklarację, zamiast nazywać każdy plik Overpassem.
`query_sha256` opisuje zapytanie, które NAPRAWDĘ wysłano — suma zapytania Overpassa
w wyniku pobrania z `/api/0.6/map` byłaby zdaniem nieprawdziwym. Atrybucja i licencja
bez zmian: **© OpenStreetMap contributors, ODbL 1.0**.

*Pozycja w hierarchii.* Bez zmian — **klasa 4**, poniżej oficjalnych danych STIB
i Regionu. Ta droga zmienia sposób dostępu do OSM, nie rangę OSM.

*Rejestr.* **Ten akapit jest przepisany 12.09.2026 (6.D53), a nie dopisany obok.**
Poprzednia wersja mówiła: „`data/network/sources.json` opisuje dostęp jako
`access.type = "osm_or_overpass"`, więc obie drogi mieszczą się w istniejącym wpisie
rejestru; czego rejestr nie zapisuje, to limity anonimowe tej konkretnej końcówki i to
jest zgłoszone jako osobna pozycja kolejki, a nie poprawione tutaj (`data/` jest tylko
do odczytu)". Ta pozycja to była 6.D53 i **jest domknięta**: rejestr wymienia dziś obie
końcówki osobno, w `access.endpoints`, każdą z jej `url`, `role` (`primary` /
`fallback`), `server_side_filter` i limitem — `node_limit_per_call = 50000` dla
`/api/0.6/map`, `null` dla Overpassa **z osobnym zdaniem, dlaczego go nie ma** (filtruje
serwer, więc rozmiar odpowiedzi zależy od zapytania, a nie od prostokąta). Dwa słowa
zostały na miejscu dla czytników sprzed tej pozycji, ale rozstrzyga lista.

Liczba limitu stoi **w dwóch miejscach świadomie** — w rejestrze i jako
`OSM_API_NODE_LIMIT` w `tools/track/crosscheck_alignment.py`, bo narzędzie musi
rozpoznać odmowę także bez rejestru pod ręką — i dlatego ma strażnika:
`test_osm_api_fallback.test_limit_koncowki_w_rejestrze_zgadza_sie_z_kodem_i_komunikat_NAZYWA_OBIE`
zestawia sześć par rejestr↔kod i przy rozjeździe wypisuje **obie** wartości. Wypis do
obejrzenia ręką:

```bash
python3 -c "import sys; sys.path.insert(0,'tools/track'); import crosscheck_alignment as X; print(*X.wiersze_limitow(), sep=chr(10))"
```

Zapis do `data/network/sources.json` był tu uprawniony **decyzją właściciela
z 10.09.2026**, dotyczącą tej jednej pozycji i tego jednego pliku; `data/` zostaje tylko
do odczytu wszędzie indziej.

Bramka: `tools/tests/test_osm_api_fallback.py`.

## Macierz źródło → zadanie

| zadanie | źródło podstawowe | źródła kontrolne | czego nie wolno wywnioskować |
|---|---|---|---|
| T-110 stacje/GTFS | STIB GTFS + Stop Details | NeTEx EPIP | liczby fizycznych stacji z samej liczby rekordów `stops.txt` |
| T-111 oś pozioma | STIB Shapefiles | INSPIRE Rails, UrbIS Metro, OSM | że najdokładniejsza wizualnie geometria jest prawdziwą osią toru |
| T-112 profil pionowy | zatwierdzone kotwice T-901 + dane powierzchniowe | LiDAR, DSM, UrbIS | głębokości tunelu z `niveau`, LiDAR lub DSM |
| R-004/T-211 stacje | tekstowe dane STIB + `metro_access` | UrbIS Metro | układu wnętrza/głębokości z samego punktu wejścia |
| T-212 powierzchnia/portal | `metro_access` + LiDAR/DSM | UrbIS Tunnel, OSM | geometrii podziemnej z danych powierzchniowych |

## Stan CBTC — ważna korekta historyczna

Na 31.08.2026 **CBTC na liniach 1 i 5 nie jest jeszcze publicznie uruchomionym systemem
na całej trasie**. Oficjalny stan i granice wiedzy są prowadzone w R-003 (#15).

Oficjalny komunikat z 02.07.2026:

https://stib.prezly.com/nouvelle-signalisation-metro-on-en-est-ou

Scenariusz historyczny 31.08.2026 nie może domyślnie startować jako `cbtc_future`.

## M7 — źródła techniczne

Oficjalna karta techniczna STIB:

https://stib.prezly.com/le-nouveau-metro-m7-est-arrive-a-bruxelles

Potwierdza m.in. długość 94 m, szerokość 2,70 m, podłogę 1,03 m, sześć członów,
układ drzwi, masę pustego składu około 170 t oraz 16 × 135 kW mocy trakcyjnej.

Szczegółowe rozdzielenie klas pochodzenia jest prowadzone w T-904 (#8). Nazwy klas
definiuje `docs/02-simulation.md`; do 10.09.2026 stała tu nazwa, której ten dokument
nie zna — powtórzona lista rozjechała się z definicją (6.D89).
Nie kopiujemy parametrów z repozytoriów fanowskich, jeżeli istnieje źródło STIB.

## Publiczne repozytoria referencyjne

- `lexag/OpenTrainER` — MIT, Godot, dane linii/pojazdów poza silnikiem. Dobra referencja
  dla separacji danych i symulatora; nie jest źródłem faktów o STIB.
- `VTTI-CSM/NeTrainSim` — GPL-3.0, sieciowy symulator pociągów i dynamika podłużna.
  Dobra referencja literatury/modeli; kodu GPL nie kopiujemy bez świadomej decyzji licencyjnej.
- `danito/stibgtfs2mqtt` — GPL-3.0, łączy realtime STIB z GTFS; referencja dla mapowania
  identyfikatorów/endpointów.
- `widged/stib-geojson` — brak jawnej licencji repo. **Reference only**; geometrię
  pobieramy z pierwotnych datasetów.

## Checklista dla agentów

Przed dodaniem nowego datasetu:

1. zapisz `id`, wydawcę, klasę źródła i rolę;
2. zapisz metadane URL i — jeśli potwierdzone — właściwy download/API URL;
3. zapisz licencję lub jawnie `see dataset metadata`;
4. zapisz częstotliwość aktualizacji, jeżeli wydawca ją deklaruje;
5. zapisz rodzaj dostępu i wymagania auth bez sekretów;
6. zapisz `checked_at` i dla zdarzeń historycznych także `as_of`;
7. zapisz ograniczenia interpretacji;
8. przy danych przestrzennych zapisz CRS wejścia;
9. przy danych pochodnych zapisz transformacje i SHA-256 wejścia/wyjścia zgodnie z T-114;
10. przy konflikcie nie poprawiaj danych „na oko” — wygeneruj raport rozbieżności.
