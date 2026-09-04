# R-007 — długość i wysokość peronu: czego STIB nie publikuje

**Zmierzone na commicie:** `68e1c81`

Stan: **2026-09-02**. Pytanie: czy istnieje publiczne, kompatybilne licencyjnie źródło
długości i wysokości peronów stacji metra w Brukseli. Odblokowuje (albo nie) T-211 i T-212.

Wzorzec raportu: [`reports/R-006-line-speed.md`](R-006-line-speed.md) — tam też wynikiem
było „źródła nie ma", z dowodem.

---

## 1. Wynik, w jednym zdaniu

**Długości peronu nie podaje żadne publiczne źródło**, ale **wysokość peronu podaje sam
STIB**, a długość da się **dwustronnie ograniczyć**.

| dana | stan po R-007 |
|---|---|
| wysokość peronu nad główką szyny | **1,03 m**, `source_backed` z jednym zastrzeżeniem (§2) |
| długość peronu | **brak źródła**; udowodnione `94,0 m ≤ L ≤ obrys stacji`, najciaśniej Parc 109,1 m (§4) |

## 2. Wysokość peronu — znaleziona

STIB podaje to sam, w karcie technicznej M7, w dwóch niezależnych publikacjach:

> **„Hauteur du plancher : 1m03** contre 1m05 pour les M6 (le plancher des M7 sera donc
> 100 % plat, **à hauteur du quai**)"
>
> — STIB/MIVB, 2020-07-13, `stib_m7_press_kit_2020_07_13`
> — powtórzone 2021-05-26, `stib_m7_press_kit_2021_05_26`

i w treści obu: *„un plancher 100 % plat, à hauteur des quais"*.

Cytat zweryfikowany **niezależnie od researchu**, bezpośrednim pobraniem strony
2026-09-02. Repo ma już `floor_height_m = 1.03` ze statusem `spec`
(`data/vehicle/m7-spec.json`), więc obie strony równania są source-backed.

**Zastrzeżenie, które musi jechać razem z tą liczbą:** STIB **nie deklaruje, względem
czego** mierzy 1 m 03. Wysokość podłogi pojazdu szynowego podaje się konwencjonalnie nad
główką szyny i tak też repo interpretuje pole `floor_height_m`, ale to jest **konwencja
branżowa, nie zdanie STIB**. Status `source_backed` obejmuje wartość; nie obejmuje bazy
odniesienia.

Kontrola krzyżowa: OSM **nie zaprzecza** — po prostu milczy. Z 67 peronów metra w bboxie
pakietu A **żaden nie ma tagu `height`**. Wszystkie 39 wystąpień `height=0.76` w tym samym
bboxie to perony **SNCB** (`train=yes`) — belgijski standard kolejowy, nie metro. To jest
pułapka, w którą łatwo wpaść.

## 3. Długość peronu — czego dokładnie nie ma

Żaden dokument STIB, żadna warstwa Regionu, żaden feed INSPIRE i **żaden tag OSM** nie
podaje długości peronu dla ani jednej z 59 stacji.

Najbliżej są dwa zdania i oba są pośrednie:

**(a)** STIB, stibstories.be, 2021-09-16: *„Un train de cinq voitures s'adapte parfaitement
à la longueur du quai d'une station de métro. Un train avec quatre wagons est par contre
plus court de 18 mètres."* → wagon MX ≈ 18 m, skład pięciowagonowy ≈ **90 m**, który
„idealnie pasuje". To nie jest długość peronu — to stwierdzenie, że 90 m się mieści.

**(b)** STIB, 2026-07-02: *„les nouvelles rames de métro M7 circulent uniquement sur les
lignes 1 et 5"* → skład 94,0 m zatrzymuje się na wszystkich dwunastu stacjach pakietu A.

Te dwa zdania są ze sobą w napięciu (90 m „idealnie", a jeździ 94 m) i żadne nie jest
wymiarem. **Nie uśredniam.**

## 4. Ograniczenie, które da się udowodnić

### Dolne: 94,0 m

Skład M7 ma 94,0 m (`data/vehicle/m7-spec.json`, `spec`) i kursuje wyłącznie na liniach
1 i 5, czyli na całym pakiecie A. Peron krótszy od składu jest sprzeczny z ruchem bez
selektywnego otwierania drzwi, którego STIB nie stosuje.

**Nie dotyczy peronów 3 i 4 w Arts-Loi** (poziom −1, linie 2/6) — tam M7 nie wjeżdża.

### Górne: obrys stacji z UrbIS

Poligony `MS` z `urbis_metro_station_polygons` (CC0) to obrysy stacji. Peron nie może być
dłuższy od bryły stacji. Rozciągłość poligonu rzutowana na lokalny kierunek osi:

| stacja | obrys wzdłuż osi | perony OSM |
|---|---:|---|
| Gare de l'Ouest | 171,4 **(nieważne)** | 94,1 94,1 94,5 94,5 |
| Beekkant | 163,3 | 94,8 94,8 |
| Étangs Noirs | 161,3 | 94,7 94,8 |
| Comte de Flandre | 197,3 | 94,8 94,8 |
| Sainte-Catherine | 187,8 | 94,5 94,6 |
| De Brouckère | 191,4 | 94,7 94,7 |
| Gare Centrale | 125,0 | 94,7 94,8 |
| **Parc** | **109,1** | 93,5 93,7 |
| Arts-Loi | 126,1 | 93,7 93,8 95,8 95,8 |
| Maelbeek | 175,0 | 95,4 95,8 |
| Schuman | 224,9 | 111,6 111,6 |
| Merode | 186,6 | 95,2 97,2 |

**Kontrola, że górne ograniczenie w ogóle obowiązuje:** 24 z 28 peronów OSM mieści się
w całości wewnątrz odpowiadającego poligonu. Wyjątek: **Gare de l'Ouest**, gdzie 0 z 7
wierzchołków leży wewnątrz — poligon nie obejmuje całego kompleksu, więc **tam
ograniczenie nie obowiązuje** i tak jest zapisane w `sources.json`.

### Czego pomiar OSM nie znaczy

26 z 28 peronów mieści się w **94,76 ± 0,78 m**. Kuszące, ale:

- **dwa pomiary (Parc 93,5 i 93,7) leżą PONIŻEJ długości składu 94,0 m.** Peron w Parc nie
  jest za krótki — to mierzy **błąd obrysu OSM: co najmniej ±0,5 m**. Dwa miejsca po
  przecinku byłyby nadużyciem;
- **Schuman 111,6 m** ma najsłabszą możliwą proweniencję: changeset z 2017, `source=knowledge`
  („z pamięci mapowicza");
- geometrię 28 peronów założyło **dwóch mapowiczów** w latach 2016–2017. Proweniencja jest
  **niejednorodna**: `survey` dla pięciu stacji, `URBISfr numerical imagery` dla trzech,
  `knowledge` dla czterech.

## 5. Decyzja właściciela (2026-09-02)

1. **Wysokość peronu: `source_backed` z zastrzeżeniem z §2.**
2. **Długość peronu: zostaje `unknown` w danych.** T-211 dostaje **jawny parametr
   generatora** o wartości domyślnej **94,0 m = długość składu** (fakt STIB), a **nie**
   94,76 m (pomiar OSM, klasa niżej w hierarchii). Peron długości składu jest najkrótszym
   peronem zgodnym z ruchem i najmniej zmyślonym wyborem, jaki mamy.
3. Górne ograniczenie z UrbIS zostaje jako **kontrola**: generator dający peron dłuższy niż
   obrys stacji jest na pewno błędny. Najciaśniejszy przypadek: **Parc, 109,1 m**.
4. **Schuman zostaje otwarty.** 111,6 m z `source=knowledge` wobec 94,8 gdzie indziej to
   albo prawda o dłuższym peronie, albo błąd mapowicza.

## 6. „125 metrów średnio, niektóre 170" — ślad prowadzi donikąd

Liczba, którą znajdzie każdy, kto poszuka (fr.wikipedia). Prześledzona wyszukiwaniem
binarnym po **1238 rewizjach**:

```
PIERWSZA REWIZJA ZE ZDANIEM:
 revid 20307960, user "Ghost dog", timestamp 2007-09-02T09:47:34Z, comment ""
```

Wstawiona 2007-09-02, **z pustym opisem edycji i bez żadnego źródła**. Dziewiętnaście lat
później nadal bez przypisu. Przypis, który dziś przy niej stoi, to **nota redaktora**
z 2010, w której autor sam się waha.

Klasa: `secondary_reference`, **poniżej OSM**. Sprzeczna z pomiarem o ~30 %.

**Hipoteza, dlaczego akurat te liczby:** rozciągłości poligonów **stacji** dla pakietu A
dają średnią **168,3 m** i maksimum 224,9 m — bliżej „125 średnio, niektóre 170" niż
jakikolwiek peron. Ktoś, kto w 2007 patrzył na plany, mógł podać długość **bryły stacji,
nie peronu**. Nie twierdzę tego; zapisuję, bo pasuje liczbowo.

## 7. Co sprawdzono i czego tam nie ma

| źródło | odpowiedź | peron? |
|---|---|---|
| STIB: plany dzielnicowe, „version verbale" | 200 / **404 ×4** | nie |
| STIB: plany 3D (Gare Centrale, Schuman) | 200, 3,2 MB / 2,1 MB | nie — zero słowa „quai" |
| STIB: GTFS static | 200, 14,5 MB | **brak `pathways.txt` i `levels.txt`** |
| STIB: Shapefiles, StopDetails | 200 | nie — punkty, zero pól wymiarowych |
| STIB: statystyki 2025/2008/2017 | 200 ×3 | „quai" pada **raz w trzech dokumentach** |
| **Paradigm: katalog OGC, 276 kolekcji** | 200, 1,66 MB | **0 trafień** na `quai\|perron\|platform\|kaai` |
| **Paradigm: WFS, 274 typy** | 200, 246 kB | **0 trafień** |
| `bm_public_transport:metro_access` | **nie ma w katalogu** | warstwa zniknęła (R-004 notował 401) |
| `bm_urbis_topo:pt_stop_line` | 200, 1386 obiektów | nie — naziemne wysepki, mediana **5,1 m** |
| **INSPIRE Rails STIB** | 200, 378 kB | **0 wystąpień ciągu `Platform`** |
| **Schemat INSPIRE TN-RA 5.0** | 200 | **nie ma obiektu peronu w ogóle** — tylko `numberOfPlatforms` (integer) |
| NeTEx EPIP | **404** (w R-004 było 401) | — |
| OSM: 67 peronów metra | 200 | **0/67 z `length`, 0/67 z `height`** |

## 8. Co wyszło przy okazji

**(a) Głębokości peronów pięciu stacji.** EIE Métro 3, Livre III Station Colignon
(`metro3_eie_livre3_colignon`, s. ~275):

> *„A titre d'exemple, la profondeur des quais par rapport au niveau de la surface est
> d'environ **11 m** pour les stations **De Brouckère** et **Arts-Loi**, **15 m** pour la
> station **Schuman**, **19 m** pour la station **Parc** et **21,5 m** pour la station
> **Botanique**. […] Cette dernière est actuellement la station la plus profonde du réseau."*

Wpisane do `data/network/station-depths.csv` decyzją właściciela, ze statusem `estimated`
i z pełną notatką o dwóch przekształceniach: źródło podaje głębokość **peronu**, a plik
chce rzędnej **główki szyny** (różnica = wysokość peronu z §2), i mówi „environ" w zdaniu
porównawczym, nie w tabeli pomiarowej.

**Schuman zostaje pusty** — 15 m potwierdza jedną stronę znanego konfliktu (15 m vs
17,42 m), a rejestr nie wybiera zwycięzcy.

Dodatkowo: **żadna istniejąca stacja metra w Brukseli nie jest głębsza niż 21,5 m**
(Botanique, poza pakietem A).

**(b) Livre III „Généralités Stations" jest pustym plikiem.** `HTTP 200`,
`Content-Length: 0`, `Last-Modified: 2022-07-24`. Tom EIE, który powinien opisywać ogólne
parametry stacji, nie został nigdy wgrany. To jedyny znany publiczny dokument, który mógłby
podać długość peronu wprost.

**(c) STIB ma 25 martwych linków „version verbale", nie 4.** R-004 zauważył cztery, bo
tylko te są w pakiecie A. Żywych jest 44 z 59. Dodatkowo link „Yser version verbale"
wskazuje na plik `Veeweyde(Veeweide).pdf`.

**(d) `bm_urbis_topo:pt_stop_line` to nie perony szynowe.** Mediana 5,1 m, maksimum 21,4 m.
Zmierzone, żeby nikt w przyszłości nie wziął tej warstwy za warstwę peronów.
