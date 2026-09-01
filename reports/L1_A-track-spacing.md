# Pakiet A — zmierzony rozstaw torów z INSPIRE Rails (T-111)

Wygenerowane przez `tools/track/inspire_rail.py`. Stan: **2026-09-01**.
Odcinek: Gare de l'Ouest / Weststation → Merode, 12 stacji, 6686,35 m.

Pytanie zadania: czy `track_offsets: [-2.10, 2.10]` w `tools/blender/profiles.py`
— dziś czyste założenie projektowe bez źródła — da się zastąpić wartością zmierzoną.

**Odpowiedź: nie, jeszcze nie.** Liczba jest, jest powtarzalna i jest węższa niż
założenie, ale nie pochodzi z pomiaru infrastruktury. Uzasadnienie w sekcji „Werdykt".

## Wynik pomiaru

| wielkość | wartość |
|---|---:|
| rozstaw torów (odległość median) | **3,294 m** |
| pół rozstawu (odpowiednik `track_offsets`) | **±1,647 m** |
| rozrzut P05–P95 | 3,029–4,367 m |
| tor osi: mediana odsunięcia | 0,012 m (373 próbki, σ 0,116 m) |
| tor przeciwny: mediana odsunięcia | −3,282 m (382 próbki, σ 0,658 m) |
| próbki po niewłaściwej stronie osi | **0** |
| wartość projektowa w `profiles.py` | 4,20 m (±2,10 m) |
| różnica pomiar − projekt | **−0,91 m** |

Rozstaw jest liczony jako odległość median dwóch chmur odsunięć, a nie jako średnia
odległość punkt-punkt: wierzchołki obu polilinii nie są sparowane i mają różną gęstość,
więc parowanie po indeksie dałoby liczbę zależną od digitalizacji.

Znak odsunięcia jest liczony wzdłuż wektora „prawo" ramki RMF z `tools/blender/sweep.py`
(`rmf_frames(points)[i][2]`) — tej samej, na której `tunnel_sweep.py` stawia profil.
Zmierzone ±1,647 m i projektowe ±2,10 m są więc w tym samym układzie i wolno je porównywać.

### Rozstaw odcinek po odcinku

Jedna liczba na 6,7 km ukrywałaby węzeł Beekkant, więc mediana jest liczona także osobno
dla każdego linku toru przeciwnego:

| odcinek | próbek | mediana odsunięcia [m] | min | maks |
|---|---:|---:|---:|---:|
| Merode → Schuman | 22 | −4,38 | −7,16 | −2,59 |
| Schuman → Schuman (węzeł 8065) | 8 | −4,18 | −7,16 | −3,67 |
| Schuman → Maelbeek | 7 | −3,17 | −3,68 | −3,03 |
| Maelbeek → Arts-Loi | 5 | −3,11 | −3,88 | −2,95 |
| Arts-Loi → Parc | 23 | −3,30 | −3,88 | −2,95 |
| Parc → Gare Centrale | 35 | −3,18 | −3,34 | −3,01 |
| Gare Centrale → De Brouckère | 57 | −3,16 | −4,55 | −3,01 |
| De Brouckère → Sainte-Catherine | 53 | −3,30 | −3,60 | −3,03 |
| Sainte-Catherine → Comte de Flandre | 47 | −3,18 | −3,81 | −2,96 |
| Comte de Flandre → Étangs Noirs | 44 | −3,27 | −3,39 | −2,96 |
| Étangs Noirs → Beekkant | 58 | −3,96 | −4,39 | −3,15 |
| Beekkant → Gare de l'Ouest | 23 | −3,30 | −4,19 | −3,05 |

Dziesięć z dwunastu odcinków mieści się w 3,11–3,30 m. Odstają dwa skraje: rejon
Merode–Schuman (−4,2 do −4,4 m) i Étangs Noirs–Beekkant (−3,96 m), czyli dokładnie te
miejsca, w których pień się rozplata. **Rozstaw nie jest w tych danych stałą** i to jest
pierwszy powód, dla którego nie da się z niego zrobić jednej liczby projektowej.

## Dowód poprawności LAEA (EPSG:3035 → WGS84)

Transformacja jest w `tools/track/crs.py` (`wgs84_to_laea3035`, `laea3035_to_wgs84`,
`laea3035_to_lambert72`), czysty stdlib, odwrotność `q` przez Newtona zamiast szeregu
Snydera. Sprawdzona trzema niezależnymi sposobami.

### 1. Początek odwzorowania

```
laea3035_to_wgs84(4321000.0, 3210000.0) -> (10.0, 52.0)
wgs84_to_laea3035(10.0, 52.0)           -> (4321000.0, 3210000.0)
```

Dokładnie, do bitu (test `test_inspire_laea_origin_maps_to_declared_centre`,
tolerancja 1e-9 stopnia i 1e-6 m).

### 2. Round-trip na punktach brukselskich

| punkt (lon, lat) | EPSG:3035 (E, N) | powrót — błąd |
|---|---|---:|
| 4,3517 / 50,8466 | 3 923 640,474 / 3 097 023,964 | 6,2e-11 m |
| 4,3200 / 50,8500 | 3 921 444,677 / 3 097 573,917 | 3,9e-9 m |
| 4,3900 / 50,8400 | 3 926 272,886 / 3 096 084,220 | 7,9e-10 m |
| 4,2000 / 50,9000 | 3 913 461,437 / 3 103 783,860 | 3,9e-9 m |

### 3. Przykład obliczeniowy EPSG Guidance Note 7-2 (metoda 9820)

| | E [m] | N [m] |
|---|---:|---:|
| publikowany dla 5°E / 50°N | 3 962 799,45 | 2 999 718,85 |
| ta implementacja | 3 962 799,451 | 2 999 718,853 |
| różnica | **0,001** | **0,003** |

Publikowane wartości są zaokrąglone do centymetra, więc różnica jest w całości
zaokrągleniem źródła. Test: `test_inspire_laea_matches_epsg_worked_example`.

### 4. Najmocniejszy test — geometria INSPIRE wobec skomitowanej osi

Łańcuch linków kierunku zgodnego z osią, przerzucony EPSG:3035 → WGS84 → EPSG:31370
i porównany z `data/track/L1_A.json` (po dodaniu `origin_source_crs`):

| miara | wartość |
|---|---:|
| punktów | 373 |
| mediana odległości od osi | **0,068 m** |
| P95 | 0,241 m |
| maksimum | **0,370 m** |

Na 6686 m osi maksymalna rozbieżność to 37 cm. Błąd w LAEA rzędu setek metrów albo
zamiana kolejności osi byłyby tu widoczne natychmiast.

### Pułapka kolejności osi

`gml:posList` w EPSG:3035 idzie w kolejności **northing, easting** — tak stanowi rejestr
EPSG i tak to zapisuje ten plik, bo `srsName` jest podany jako URI OGC. Odczytanie tego
jako (E, N) przenosi pierwszy wierzchołek pliku z 4,409°E / 50,838°N na
**−10,390°E / 56,866°N**, czyli na Atlantyk na zachód od Irlandii. Test
`test_inspire_posbags_swap_axis_order` pilnuje kolejności.

### Czego ten dowód NIE obejmuje

ETRS89 jest tu traktowane jak WGS84. To przybliżenie: układy rozjeżdżają się o ~2,5 cm
rocznie od 1989 r., czyli rzędu 0,8 m w 2026 r. Dla pomiaru **różnicy** dwóch geometrii
z tego samego pliku błąd znosi się do zera i rozstaw 3,294 m jest nim nietknięty. Dla
porównania z osią z innego źródła jest to systematyczne przesunięcie całej chmury —
i jest jedną ze składowych tych 0,068 m mediany.

## Jak filtrowane są linie

Ekstrakt geograficzny wokół pnia 1/5 zawiera także linie 2 i 6, które na odcinku
Gare de l'Ouest — Beekkant biegną w tym samym korytarzu i **przez te same dwie stacje**.
Wybór linków „po bliskości do osi" wciąga je do pomiaru i psuje rozkład odsunięć.

Dlatego linki są wybierane **topologicznie, nie geometrycznie**: przez przejście po
identyfikatorach przystanków (`gml:description` → „Link between stops X and Y") w
kolejności stacji pakietu A, wziętej wprost z `stop_id` w `data/track/L1_A.json`.
Przejście dopuszcza skok wewnątrz jednej stacji — na Schumanie kierunek powrotny idzie
8071 → 8065 → 8061, czyli dwa linki na jednej nazwie.

Przejście jest **jednoznaczne**: 1 ścieżka w przód (11 linków), 1 wstecz (12 linków),
zero brakujących przystanków. Gdyby ścieżek było więcej niż jedna, skrypt kończy się
statusem „niejednoznaczne przejście po stacjach" i nie podaje żadnej liczby.

### Dowód, że filtr działa

Rozkład odsunięć w koszach po 1 m. Mod to kosz ściśle większy od obu sąsiadów, niosący
co najmniej 1,5 % próbek — sam próg udziału nie wystarcza, bo jeden mod rozjeżdżony na
dwa sąsiednie kosze dałby fałszywe „cztery mody" (test
`test_inspire_modes_do_not_split_one_track_across_bin_edge`).

| selekcja | linków | mody rozkładu |
|---|---:|---|
| **filtr topologiczny** | 23 | **2**: −3,5 m (41,9 %) i +0,5 m (27,8 %) |
| kontrolna, po bliskości (60 m) | 41 | **4**: −14,5 m (1,9 %), −3,5 m (36,5 %), +0,5 m (24,9 %), +10,5 m (2,2 %) |

Histogram po filtrze (kosz [m] → liczność):

```
 -8..-7   5      -4..-3  316      0..+1  210
 -7..-6   3      -3..-2   12
 -6..-5   4      -2..-1    0   <- pusty kosz rozdzielający dwa tory
 -5..-4  42      -1..0   163
```

Dwie chmury są rozdzielone pustym koszem i **żadna próbka toru przeciwnego nie leży po
stronie toru osi** (`wrong_side_samples: 0`).

Linki, które wpuszcza selekcja korytarzowa, a odrzuca filtr — z medianą ich odsunięcia:

| link | odcinek | mediana [m] |
|---|---|---:|
| `link_5687448382` | Beekkant → Gare de l'Ouest (linia 2/6) | +14,51 |
| `link_5687438753` | Beekkant → Osseghem (linia 2/6) | −13,62 |
| `link_5683818743` | Gare de l'Ouest → Beekkant (linia 2/6) | +2,06 |
| `link_5687548744` | Osseghem → Beekkant (linia 2/6) | +5,11 |
| `link_5684028412` | Arts-Loi → Madou (linia 2/6) | −204,41 |
| `link_5680818071` | Montgomery → Merode (linia 1 spoza pakietu) | −5,09 |

To są właśnie te dwa dodatkowe mody na −14,5 m i +10,5 m.

**Uwaga na wyjątek:** `link_5687328742` (Gare de l'Ouest 8732 → Beekkant 8742) leży na
osi z medianą **+0,02 m** i **nie jest** zanieczyszczeniem — Gare de l'Ouest ma pięć
węzłów metra, a 8732 i 8733 to dwa perony 1/5 wchodzące na ten sam tor do Beekkant.
Filtr po samej bliskości nie odróżniłby tego przypadku od linii 2/6; filtr topologiczny
w ogóle nie musi tego rozstrzygać, bo idzie po `stop_id` z osi.

## Co to źródło mówi, a czego nie

Dataset: `belgian_mobility_inspire_rails`,
`https://api-management-discovery-production.azure-api.net/api/datasets/stibmivb/static/rail`.
ZIP 378 482 B, `sha256 95e4aeaf…4fbc22`; w środku jeden `TN.RailTransportNetwork.gml`
3 370 448 B, `sha256 0462c839…c4cb`. Licencja **CC BY 4.0**, atrybucja
`Source: STIB-MIVB - Open Data`.

Zawartość, zweryfikowana parserem `xml.etree.ElementTree`:

| obiekt | liczba |
|---|---:|
| `tn-ra:RailwayLink` | 810 |
| `tn-ra:RailwayNode` | 791 (790 unikalnych kodów przystanku — kod `1695` powtórzony na dwóch peronach tramwajowych) |
| `tn-ra:RailwayLine` | 44, w tym **8 metra** (kody 1, 2, 5, 6 × dwa kierunki) |
| `tn-ra:RailwayLinkSequence` | 44 |
| linków metro-metro | 130 |

### Ograniczenia stwierdzone, nie przepisane z metadanych

1. **Brak wymiaru pionowego.** Każda geometria ma `srsDimension="2"`. Dataset **nie
   odblokowuje T-112** i nie wolno go do tego użyć.
2. **Warstwa topologiczna jest zepsuta.** `RailwayLinkSequence` niesie łącznie
   **1036 referencji `net:link xlink:href`, z których rozwiązuje się 0**. Wskazują na
   identyfikatory w rodzaju `#link_560011`, podczas gdy realne id mają postać
   `link_5655295532` albo `link_564002G4003G`. Powiązanie linia → linki trzeba więc
   zbudować inaczej — tu przez identyfikatory przystanków z `gml:description`.
3. **Okno ważności jest wygasłe.** Wszystkie linki deklarują
   `tn:validFrom 2026-03-02` … `tn:validTo 2026-06-28`, czyli okno zamknięte **65 dni
   przed** datą pobrania (2026-09-01). Portal deklaruje aktualizację tygodniową i mimo
   to serwuje snapshot z przeterminowanym oknem. Ten sam wzorzec zapisano wcześniej dla
   `stib_shapefiles`.
4. **To nie jest niezależne źródło.** Geometria kierunku zgodnego z osią pokrywa się
   z `ACTU_LIGNES_BRUTES` do 0,068 m mediany na 6686 m. Dodatkowo na 11 par przystanków
   pnia przypada dokładnie **jeden** `RailwayLink` na parę, a pnia używają zarówno
   linia 1, jak i linia 5 — czyli INSPIRE trzyma jedną geometrię na parę przystanków,
   a nie na linię i nie na tor. To ten sam graf tras handlowych w innym opakowaniu.
5. **Kolejność osi** `posList` to northing, easting (sekcja o LAEA).

## Werdykt: czy to wystarczy, żeby zmienić `track_offsets`

**Nie.** `tools/blender/profiles.py` **nie został ruszony** i nie powinien być ruszony
na podstawie tego raportu. Powody, w kolejności wagi:

1. **Zmierzono odległość dwóch polilinii tras handlowych, nie rozstaw torów.**
   Punkt 4 wyżej pokazuje, że INSPIRE nie jest niezależnym pomiarem infrastruktury —
   to ta sama geometria co shapefile STIB. Żadne z dostępnych źródeł nie publikuje
   rozstawu jako **wymiaru konstrukcyjnego**; wszystkie publikują przebieg trasy.
2. **Trzy źródła dają trzy różne liczby**, rozjeżdżone o 0,6 m, czyli o 18 % wartości:

   | źródło | rozstaw |
   |---|---:|
   | INSPIRE Rails (ten raport) | 3,29 m |
   | STIB `ACTU_LIGNES_BRUTES`, warianty 1 vs 2 (`reports/L1_A-crosscheck.md`) | 3,34 m |
   | OpenStreetMap, relacje tras (`reports/L1_A-crosscheck.md`) | 3,88 m |

   `docs/07-open-data-research.md` mówi wprost: przy sprzeczności **nie uśredniaj**.
   3,5 m „ze średniej" byłoby liczbą, której nie ma w żadnym źródle.
3. **Rozstaw nie jest w tych danych stały** — od 3,11 m do 4,38 m w medianach odcinków,
   z systematycznym rozszerzeniem na obu końcach pakietu. Wymiar projektowy musi być
   jedną liczbą; te dane jej nie zawierają.
4. **Dane są przeterminowane i pochodzą z zepsutej topologicznie warstwy.** To nie
   dyskwalifikuje pomiaru, ale dyskwalifikuje go jako podstawę wymiaru konstrukcyjnego.

### Co jednak z tego wynika dla R-005 (#17)

Wynik nie jest zerowy. Wszystkie trzy niezależne pomiary — 3,29 m, 3,34 m, 3,88 m —
leżą **poniżej** projektowych 4,20 m. Najbliższy z nich jest o 0,32 m węższy, najdalszy
o 0,91 m. Innymi słowy: założenie `±2,10 m` jest prawdopodobnie **za szerokie**,
i to konsekwentnie względem trzech różnych źródeł, a nie przypadkowo względem jednego.

To jest materiał do decyzji R-005, nie sama decyzja. Zmiana wymiaru projektowego na
wartość ze źródła należy do właściciela zadania.

Zauważone przy okazji, nietknięte: `box_double` ma półszerokość 4,70 m, więc zwężenie
`track_offsets` do ±1,65 m zmieniłoby margines skrajni po zewnętrznych stronach obu
torów. `tools/blender/clearance.py` i `tools/tests/test_clearance.py` liczą tę skrajnię
przy dzisiejszych ±2,10 m i wynik przestałby być aktualny — R-005 musi je przeliczyć razem.

## Odtworzenie

```bash
# z sieci, z manifestem provenance
python3 tools/track/inspire_rail.py --alignment data/track/L1_A.json \
    --out build/L1_A-track-spacing.json

# z lokalnego snapshotu, bez sieci
python3 tools/track/inspire_rail.py --gml-file build/TN.RailTransportNetwork.gml
```

Niedostępność źródła jest wynikiem, nie błędem: skrypt zapisuje status `niedostępne`
wraz z powodem i kończy się kodem 0, tak jak `crosscheck_alignment.py` i `tunnel_width.py`.
Pobranych ZIP-ów ani GML-i nie commitujemy.

## Atrybucja

- STIB/MIVB — Open Data, dystrybucja Belgian Mobility, **CC BY 4.0**:
  `Source: STIB-MIVB - Open Data - 2026-09-01`.
- OpenStreetMap contributors — **ODbL 1.0** (liczby przeniesione z `reports/L1_A-crosscheck.md`).
