# Pakiet A — oś pozioma i kontrola krzyżowa (T-111)

Wygenerowane przez `tools/track/build_alignment.py` i `tools/track/crosscheck_alignment.py`.
Stan: **2026-09-01**. Odcinek: Gare de l'Ouest / Weststation → Merode, 12 stacji.

## Wynik

| wielkość | wartość |
|---|---:|
| długość osi | **6686,35 m** |
| punktów | 447 |
| wierzchołków źródłowych w wycinku | 345 |
| odstęp punktów | 7,76–22,23 m (krok próbkowania 15 m) |
| odchyłka próbkowania od polilinii źródłowej | **0,000 m** |
| odsunięcie kotwic stacyjnych od osi | mediana 0,000 m, maks. **0,000 m** |
| najmniejszy promień po próbkowaniu | 97 m |

Walidator `tools/track/validate.py data/track/L1_A.json --line L1`: **0 błędów**,
1 ostrzeżenie (brak głębokości — patrz sekcja o profilu pionowym).

Kilometraż stacji, liczony od kotwicy Gare de l'Ouest:

| # | stacja | chainage [m] | do następnej [m] |
|---:|---|---:|---:|
| 1 | Gare de l'Ouest / Weststation | 0,0 | 509,7 |
| 2 | Beekkant | 509,7 | 942,3 |
| 3 | Étangs Noirs / Zwarte Vijvers | 1452,0 | 602,9 |
| 4 | Comte de Flandre / Graaf van Vlaanderen | 2054,9 | 666,1 |
| 5 | Sainte-Catherine / Sint-Katelijne | 2721,0 | 409,4 |
| 6 | De Brouckère | 3130,4 | 602,0 |
| 7 | Gare Centrale / Centraal Station | 3732,4 | 343,8 |
| 8 | Parc / Park | 4076,2 | 485,4 |
| 9 | Arts-Loi / Kunst-Wet | 4561,6 | 591,5 |
| 10 | Maelbeek / Maalbeek | 5153,1 | 314,9 |
| 11 | Schuman | 5468,0 | 1219,0 |
| 12 | Merode | 6687,0 | — |

`docs/00-network-data.md` nie deklaruje długości pnia, więc 6686,35 m jest **nową
liczbą**, a nie potwierdzeniem ani zaprzeczeniem czegokolwiek. Kontrolą pośrednią jest
zgodność pełnych długości linii z dokumentacją: 12,480 km wobec deklarowanych 12,5 km
(L1), 10,291 wobec 10,3 (L2), 17,315 wobec 17,3 (L5), 15,515 wobec 15,5 (L6).

## Źródło bazowe

`ACTU_LIGNES_BRUTES` z pakietu shapefile'ów STIB/MIVB, rekord `LineCode=001m`,
`Variante=1`, kierunek `F`. Kotwice stacyjne z `ACTU_STOPS` tego samego datasetu,
w kolejności `StopOrder`.

Dataset jest **natywnie w EPSG:31370** (`.prj` = `Belge_Lambert_1972`), więc oś
powstaje bez żadnej transformacji układu. To dlatego wybrano to źródło, a nie GTFS
`shapes.txt`, który jest w WGS84 i wymagałby konwersji obarczonej niepewnością datum.

**Pułapka provenance:** archiwum deklaruje własne okno ważności
`Date_debut 02/03/2026 … Date_fin 28/08/2026` dla wszystkich 172 rekordów. Portal
deklaruje aktualizację tygodniową, ale w dniu pobrania (01.09.2026) serwuje snapshot,
którego okres ważności minął cztery dni wcześniej. Zapisane w `shapes-manifest.json`.

## Dlaczego oś jest próbkowana równomiernie

Polilinia źródłowa ma odstępy wierzchołków od **0,42 m**. Trzy kolejne punkty oddalone
o pół metra, z centymetrowym szumem poprzecznym, opisują okrąg o promieniu kilku metrów.
Statystyka promienia liczona wprost na wierzchołkach źródłowych:

| | minimum | P05 | mediana |
|---|---:|---:|---:|
| polilinia źródłowa | **4,8 m** | 84,4 m | — |
| po próbkowaniu co 15 m | **97,3 m** | 137,0 m | — |

Promień 4,8 m jest fizycznie niemożliwy dla metra i **nie jest łukiem toru** — to szum
digitalizacji trasy handlowej. Równomierne próbkowanie jest jawną transformacją zapisaną
w `L1_A.provenance.json`; punkty leżą dokładnie na polilinii źródłowej (odchyłka
**0,000 m**), więc nie jest to wygładzanie geometrii, tylko zmiana gęstości próbkowania.

Wniosek na przyszłość: **promienie łuków z tego datasetu nie są faktem konstrukcyjnym**
i nie wolno ich podawać jako parametrów toru.

## Kontrola krzyżowa

### Wewnątrz STIB — inne warianty i druga linia pnia

| porównanie | długość | mediana | P95 | maks. |
|---|---:|---:|---:|---:|
| `005m` var 1 (linia 5, ten sam kierunek) | 6686,3 m | **0,00 m** | 0,00 m | 10,65 m |
| `001m` var 2 (linia 1, powrót) | 6697,4 m | 3,34 m | 4,20 m | 45,46 m |
| `005m` var 2 (linia 5, powrót) | 6697,4 m | 3,34 m | 4,20 m | 45,46 m |

Linie 1 i 5 mają na pniu **identyczną geometrię** (mediana 0,00 m) — dataset duplikuje
tę samą polilinię per linia. To potwierdza, że `ACTU_LIGNES_BRUTES` reprezentuje trasy
handlowe, a nie infrastrukturę.

Warianty powrotne są odsunięte o **stałe ~3,3 m**. Czy to fizyczny rozstaw torów, czy
offset kartograficzny — **z tych danych nie da się rozstrzygnąć** i nie zakładamy tego.
Maksimum 45,46 m występuje w rejonie węzła Beekkant, gdzie warianty rozchodzą się.

### UrbIS / Brussels Mobility (`bm_public_transport:Metro`, CC0)

156 obiektów (69 MS stacji, 87 MT tuneli), poligony, WGS84 → EPSG:31370 własną
transformacją.

| miara | wartość |
|---|---:|
| punkty osi wewnątrz poligonu tunelu (MT) | 57,3 % |
| punkty osi wewnątrz poligonu stacji (MS) | 25,3 % |
| **razem wewnątrz obiektów metra** | **82,6 %** |
| poza | 17,4 % |

UrbIS `Metro` to poligony, nie oś toru, więc jedyną sensowną miarą jest pokrycie, a nie
odchyłka liniowa. 17,4 % poza poligonami nie oznacza błędu osi: warstwa regionalna ma
własne uproszczenia i miejscami wąskie obrysy biegnące równolegle tuż obok osi.

### OpenStreetMap (ODbL)

Overpass API jest **niedostępny z tego środowiska** — trzy próby, za każdym razem
`Connection reset by peer` na `overpass-api.de`. Kontrola została wykonana na snapshocie
pobranym 2026-09-01T10:29:56Z (`timestamp_osm_base` z odpowiedzi), 94 way
`railway=subway`.

| miara | wartość |
|---|---:|
| pokrycie osi ekstraktem (promień 50 m) | 57,9 % |
| odchyłka na pokrytym odcinku — mediana | **3,22 m** |
| P95 | 15,71 m |
| maksimum | 45,59 m |

Pokrycie i odchyłka są raportowane **osobno**, bo punkty poza zasięgiem ekstraktu dawały
setki metrów i zamazywały realny wynik. Mediana 3,22 m odpowiada mniej więcej połowie
rozstawu torów: OSM mapuje tory pojedynczo, a oś STIB jest osią trasy handlowej. **To nie
jest błąd żadnego ze źródeł** i nie podlega uśrednianiu.

### INSPIRE Rails — nie jest niezależną kontrolą

Research wykazał, że `TN.RailTransportNetwork.gml` po transformacji z EPSG:3035 zgadza
się z shapefile'em STIB do **0,1 m na 6687 m**. To ta sama geometria w innym opakowaniu.
Zapis w `docs/07-open-data-research.md`, który traktuje INSPIRE jako niezależną kontrolę
infrastruktury, jest w tym punkcie zbyt optymistyczny.

## Profil pionowy — świadomie nie modelowany

Oś jest wyłącznie pozioma. Współrzędna Z to zero, jawnie oznaczone w polu `vertical`
jako `not_modelled`. Research T-901 wykazał, że publicznie **nie istnieją rzędne główki
szyny** dla żadnej z 12 stacji pakietu A. Dostępne są wyłącznie dwie sprzeczne ze sobą
liczby „głębokości peronu pod powierzchnią" z komunikacji projektu Metro 3 dla 6 z 12
stacji — a to inna wielkość niż `depth_m` z `station-depths.csv` i bez zdefiniowanego
punktu odniesienia. T-112 pozostaje zablokowany.

## Czego z tych danych NIE wolno wyprowadzić

- **układu tor-po-torze** — dataset zawiera trasy handlowe; linie 1 i 5 mają identyczną
  polilinię, a warianty powrotne są przesunięte o stałą wartość;
- **geometrii rozjazdów**, w tym węzła Beekkant — przecięcia wariantów są punktowe;
- **promieni łuków jako parametru konstrukcyjnego** — patrz sekcja o próbkowaniu;
- **profilu pionowego, spadków i głębokości** — brak źródła;
- **rozstawu torów** — 3,3 m między wariantami nie jest udokumentowane jako wymiar
  fizyczny;
- **długości i geometrii peronów** — `ACTU_STOPS` daje punkt, nie oś peronu.

## Atrybucja

- STIB/MIVB — Open Data, dystrybucja Belgian Mobility, **CC BY 4.0**:
  `Source: STIB-MIVB - Open Data - 2026-09-01`.
- Brussels Mobility / Paradigm, warstwa `bm_public_transport:Metro` — **CC0**.
- OpenStreetMap contributors — **ODbL 1.0**.
