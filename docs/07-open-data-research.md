# Otwarte źródła danych i research

Stan researchu: **31.08.2026**.

Ten dokument określa hierarchię źródeł dla danych, których nie ma jeszcze w `data/network/`. Maszynowy rejestr źródeł znajduje się w `data/network/sources.json`.

## Hierarchia źródeł

1. **STIB/MIVB Open Data i oficjalne publikacje STIB** — dane operacyjne, GTFS, przebieg linii, przystanki, stan wdrożeń i tabor.
2. **Brussels Mobility / Paradigm / UrbIS** — geometria tuneli i stacji, warstwy przestrzenne Regionu Brukselskiego.
3. **OpenStreetMap** — szczegóły torowe, rozjazdy, wejścia, perony i kontrola krzyżowa.
4. **Prasa branżowa / dokumentacja producenta** — parametry techniczne, jeśli źródło pierwotne nie jest publiczne.
5. **Wikipedia, fanowskie mapy i repozytoria GitHub** — wyłącznie trop lub kontrola, nigdy jedyne źródło faktu.

Jeżeli dwa źródła są sprzeczne, nie uśredniaj. Zapisz rozbieżność i preferuj źródło wyżej w hierarchii.

## STIB/MIVB Open Data

### Shapefiles — podstawowe źródło przebiegu sieci

Dataset `shapefiles-production`:
https://data.stib-mivb.brussels/explore/dataset/shapefiles-production/

STIB opisuje go jako dane zawierające podstawową strukturę przestrzenną sieci: **przebieg linii i pozycje przystanków** dla komercyjnych wariantów tras.

**Wniosek:** T-111 nie powinien budować osi wyłącznie z OSM. Najpierw pobieramy geometrię STIB, a OSM służy do doprecyzowania topologii torowej i kontroli.

### GTFS

Dataset `gtfs-files-production`:
https://data.stib-mivb.brussels/explore/dataset/gtfs-files-production/api/

Statyczny GTFS STIB jest również publikowany przez belgijski portal danych mobilności i według portalu aktualizowany codziennie:
https://data.belgianmobility.io/en/data.html?agency=stibmivb

GTFS jest źródłem prawdy dla kolejności przystanków i rozkładów, ale nie wystarcza do modelowania tunelu tor po torze.

### Stop Details i realtime

- `stop-details-production` — ID, nazwa FR/NL, geolokalizacja.
- `vehicle-position-rt-production` — pozycje pojazdów, odświeżanie co 20 s.
- `waiting-time-rt-production` — czasy oczekiwania, odświeżanie co 20 s.
- `travellers-information-rt-production` — prace, zdarzenia i zakłócenia.

Realtime może później służyć do kalibracji czasów przejazdu, postoju, częstotliwości i zachowania ruchu liniowego.

### Licencja STIB Open Data

Warunki:
https://data.stib-mivb.brussels/terms/terms-and-conditions.pdf

Licencja dopuszcza bezpłatne ponowne wykorzystanie informacji, także komercyjne, oraz ich adaptowanie i łączenie z własnym produktem. Wymaga wskazania STIB/MIVB jako źródła i daty ostatniej aktualizacji danych. Nie oznacza to automatycznej zgody na kopiowanie całej identyfikacji wizualnej, dzieł sztuki ani innych chronionych zasobów. Polityka projektu pozostaje w `docs/03-legal.md`.

## Brussels Mobility / Paradigm / UrbIS

### Warstwa `Metro`

https://data.mobility.brussels/en/info/Metro/

Warstwa jest wyciągiem obiektów UrbIS typu `MS` — stacja metra i `MT` — tunel metra. Jest publikowana przez Paradigm na licencji **CC0** i dostępna m.in. jako JSON, GeoPackage, CSV, SHP, WMS, WFS i OGC API Features.

OGC API Features:
https://data.mobility.brussels/geoserver/ogc/features/v1/collections/bm_public_transport%3AMetro/items

Nie traktuj pola poziomu względnego jako publicznej niwelety toru, dopóki nie zostanie to potwierdzone dla konkretnego obiektu.

## OpenStreetMap

OSM pozostaje przydatny dla `railway=subway`, relacji `route=subway`, rozjazdów i łącznic, `stop_position`, `platform`, `stop_area`, wejść do stacji oraz tagów `tunnel` i `layer`.

Nie używaj OSM jako jedynego źródła osi, jeśli istnieje oficjalna geometria STIB lub regionalna. Zachowuj wymagane przez ODbL przypisanie autorstwa.

## Stan CBTC — ważna korekta

Na 31.08.2026 **CBTC na liniach 1 i 5 nie jest jeszcze publicznie uruchomionym systemem na całej trasie**. STIB informuje, że instalacja jest zakończona na odgałęzieniach do Erasme/Erasmus i Stockel/Stokkel, ale trwa testowanie. Odcinek Jacques Brel–Merode ma zostać wyposażony do końca 2026, a odgałęzienie Herrmann-Debroux na początku 2027. Uruchomienie ma nastąpić po zakończeniu instalacji i testów na całych liniach 1 i 5.

Oficjalny komunikat z 02.07.2026:
https://stib.prezly.com/nouvelle-signalisation-metro-on-en-est-ou

## M7

Raport działalności STIB za 2025 potwierdza 36 M7 w ruchu na koniec 2025 i 43 zamówione:
https://2025.stib-activityreports.brussels/entreprise

STIB opisała w 2026 problem produkcyjny części kół M7 powodujący drgania i hałas:
https://www.stib-mivb.be/travel/works-and-projects/works-in-progress/metro-noise-and-vibrations

## Publiczne repozytoria referencyjne

- `lexag/OpenTrainER` — MIT, Godot, JSON dla linii i pojazdów, import OSM. Dobre źródło pomysłów dla pipeline'u danych; nie jest wzorcem fizyki ani sygnalizacji.
- `VTTI-CSM/NeTrainSim` — GPL-3.0, sieciowy symulator pociągów, dynamika podłużna i energia. Dobre źródło literatury/modeli; kodu GPL nie kopiujemy bez świadomej decyzji licencyjnej.
- `danito/stibgtfs2mqtt` — GPL-3.0, łączy realtime STIB z GTFS; referencja dla mapowania ID/endpointów.
- `widged/stib-geojson` — eksport danych STIB bez zadeklarowanej licencji repo. Nie używamy jako źródła; pobieramy bezpośrednio od STIB.

## Zasady dla agentów

- Każdy nowy fakt dostaje URL i datę sprawdzenia.
- Dane oficjalne pobieraj z pierwotnego endpointu, nie z mirroru GitHub.
- Nie commituj dużych dumpów GTFS/GeoPackage; trzymaj je w katalogach ignorowanych przez Git i generuj małe deterministyczne artefakty pochodne.
- Przy łączeniu STIB + OSM + UrbIS zapisuj provenance dla każdego wyniku.
- Jeżeli geometrie różnią się istotnie, nie wybieraj „ładniejszej” — zgłoś rozbieżność.
- Repozytorium publiczne bez licencji = **reference only**.
