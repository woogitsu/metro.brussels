# Pakiety B–F — osie poziome i kontrola krzyżowa (T-111, ciąg dalszy)

Stan: **2026-09-01**. Wygenerowane przez `tools/track/build_alignment.py`,
sprawdzone `tools/track/crosscheck_alignment.py` i `tools/track/validate.py`.
Metoda jest ta sama co dla pakietu A (`reports/L1_A-crosscheck.md`); ten raport
opisuje **wyłącznie różnice, rozstrzygnięcia i zmierzone liczby**.

Powstałe pliki:

| pakiet | oś | provenance |
|---|---|---|
| B — Wschód 1 | `data/track/L1_B.json` | `L1_B.provenance.json` |
| C — Zachód 5 | `data/track/L5_C.json` | `L5_C.provenance.json` |
| D — Wschód 5 | `data/track/L5_D.json` | `L5_D.provenance.json` |
| E — Pierścień 2/6 | `data/track/L2_E.json` | `L2_E.provenance.json` |
| F — Północ 6 | `data/track/L6_F.json` | `L6_F.provenance.json` |

Pakiet A (`data/track/L1_A.json`) **nie został zmieniony**. Przebudowany nowym
narzędziem daje **bajt w bajt ten sam plik** (`cmp` bez różnic) — to jest dowód,
że uogólnienie nie ruszyło geometrii, a nie deklaracja.

---

## 1. Wynik

| pakiet | id | punktów | długość osi [m] | stacji | odstęp punktów [m] | R min [m] | R P05 [m] | R mediana [m] |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| A | `L1_A` | 447 | 6686,35 | 12 | 7,76–22,23 | 97,3 | 137,0 | 779,9 |
| B | `L1_B` | 340 | 5083,23 | 9 | 8,04–21,96 | 141,4 | 185,3 | 444,0 |
| C | `L5_C` | 361 | 5386,41 | 9 | 7,72–22,21 | 101,0 | 155,6 | 892,5 |
| D | `L5_D` | 258 | 3847,23 | 7 | 10,78–19,16 | 157,2 | 174,4 | 1216,7 |
| E | `L2_E` | 603 | 9020,77 | 17 | 7,58–22,40 | 113,0 | 160,0 | 1212,8 |
| F | `L6_F` | 299 | 4456,66 | 7 | 7,99–21,92 | 141,3 | 169,8 | 1048,7 |

Odchyłki próbkowania — **dwie różne wielkości**, mierzone w obie strony:

| pakiet | oś → łamana źródłowa (maks.) | łamana źródłowa → oś (maks.) | ubytek długości na cięciwach | NaN/Inf | Z ≠ 0 |
|---|---:|---:|---:|---:|---:|
| A | 0,000 m | 0,3065 m | 0,640 m | 0 | 0 |
| B | 0,000 m | 0,3060 m | 0,473 m | 0 | 0 |
| C | 0,000 m | 0,3685 m | 0,561 m | 0 | 0 |
| D | 0,000 m | 0,2689 m | 0,254 m | 0 | 0 |
| E | 0,000 m | 0,3207 m | 0,552 m | 0 | 0 |
| F | 0,000 m | 0,2559 m | 0,441 m | 0 | 0 |

Wiersz A jest przeliczony narzędziem, nie odczytany z `L1_A.provenance.json` —
skomitowana provenance pakietu A powstała przed wprowadzeniem drugiej miary i
**nie została przepisana** (patrz §12).

Pierwsza kolumna to miara używana dotąd: „czy punkty osi leżą na źródle". Przy
równomiernym próbkowaniu wychodzi zero **z definicji** i niczego nie dowodzi.
Druga kolumna (`source_offset_stats`, źródło zagęszczone co 1 m i mierzone
wobec osi) odpowiada na pytanie odwrotne: o ile cięciwa między próbkami ścina
wierzchołek łamanej. To ona jest realną odchyłką i dla wszystkich sześciu
pakietów mieści się poniżej **0,37 m**.

Walidator `tools/track/validate.py <oś> --line <linia>`: **0 błędów** dla każdej
z sześciu osi, po jednym ostrzeżeniu „brak głębokości" (świadome, patrz §8).

## 2. Nazwy plików — rozstrzygnięcie

Schemat: **`L<numer linii STIB>_<litera pakietu>`**, czyli to samo co `L1_A`.

- `id` w pliku równa się nazwie pliku bez rozszerzenia;
- numer linii pochodzi z `LineCode` **faktycznie użytego wariantu**
  (`001m → L1`), a nie z nazwy pakietu;
- litera pakietu zostaje, bo pakiet ma odpowiadać dokładnie jednemu plikowi.

Kłopotliwy jest tylko pakiet E („Pierścień 2/6"). Rozstrzygnięcie: **`L2_E`**,
bo geometria pochodzi z `002m`. Nie jest to twierdzenie, że odcinek należy
wyłącznie do linii 2 — jest wręcz przeciwnie i zostało to **zmierzone**:
`006m` wariant 2 daje na całym pakiecie E odchyłkę **mediana 0,00 m, P95 0,00 m,
maks. 0,00 m** wobec `002m` wariant 2. To ta sama polilinia w dwóch rekordach.
Obie kandydatury są zapisane w `L2_E.provenance.json → selection.candidates`.

Odrzucone warianty nazwy:

- `L26_E` — sugerowałby dataset „linia 26", którego nie ma;
- `PKG_E` — zrywa z `L1_A` i gubi informację o linii;
- osobne pliki dla 2 i 6 — byłyby **bajtowo tym samym przebiegiem** zapisanym dwa
  razy, a przy tym udawałyby dwa niezależne pomiary.

Informacja „które linie tędy jeżdżą" należy do provenance i kontroli krzyżowej,
nie do nazwy pliku.

## 3. Wybór linii i wariantu — z danych, nie z listy

Dotąd `--line-code 001m --variante 1` było wpisane w domyślne argumenty. Teraz
`resolve_source()` przegląda **wszystkie** metrowe pary (LineCode, Variante) —
kody metra bierze z pola `Mode == 'M'` w `ACTU_STOPS`, nie ze zgadywania po
sufiksie — i zostawia te, które spełniają cztery mierzalne warunki: obie stacje
graniczne pakietu leżą na trasie, `StopOrder` rośnie od `from` do `to`, liczba
przystanków w wycinku równa się `stations` z `lines.json`, a geometria istnieje
jako jedna polilinia. Remis rozstrzyga najniższy `LineCode`, potem `Variante`.

| pakiet | kandydaci | wybrany | LineDir | StopOrder w wycinku |
|---|---|---|---|---|
| A | `001m/v1`, `005m/v1` | `001m` v1 | F | 1–12 |
| B | `001m/v1` | `001m` v1 | F | 13–21 |
| C | `005m/v2` | `005m` v2 | V | 20–28 |
| D | `005m/v1` | `005m` v1 | F | 22–28 |
| E | `002m/v2`, `006m/v2` | `002m` v2 | V | 1–17 |
| F | `006m/v2` | `006m` v2 | V | 20–26 |

Reguła „StopOrder musi rosnąć" jest tu **wymuszona przez sam format osi**:
kilometraż 0 ma leżeć na `package.from`, a wycinek liczony wstecz dawałby
malejący chainage. Konsekwencja jest realna i trzeba ją znać: pakiety C, E i F
leżą na **wariancie powrotnym** swojej linii, czyli fizycznie na drugim torze
niż A, B i D. Rozsunięcie wariantów jest zmierzone w §6.1 i wynosi ~3,2–4,8 m
mediany. Odwrócenie geometrii wariantu 1 zamiast tego byłoby drugim wyjściem;
odrzucone, bo oś przestałaby odpowiadać torowi, po którym jedzie się z `from`
do `to`, a właśnie ta zgodność jest potwierdzona przez OSM (§6.3).

## 4. Nazwy stacji — co nie zadziałało i dlaczego

`normalise` (bez akcentów, bez myślników, wielkimi literami) **nie wystarczył**
poza pakietem A. Dwie stacje pakietu B nie mają w `Descr_fr` zapisu, który
występuje w `lines.json`:

| STIB `Descr_fr` | `Descr_nl` | `Alpha_fr` | `Alpha_nl` | `lines.json` |
|---|---|---|---|---|
| `JOSEPH.-CHARLOTTE` | `JOSEPH.-CHARLOTTE` | `Joséphine-Charlotte` | `Joséphine-Charlotte` | `Joséphine-Charlotte` |
| `CRAINHEM` | `KRAAINEM` | `Crainhem` | `Kraainem` | `Kraainem\|Crainhem` |

Rozwiązanie **nie jest** słownikiem wyjątków wpisanym ręcznie: `stop_aliases()`
bierze wszystkie cztery pola nazwowe rekordu STIB, a `canonical_station_index()`
indeksuje **obie** połówki nazwy dwujęzycznej z `lines.json` (w `Kraainem|Crainhem`
pierwsza jest niderlandzka — kolejność języków w tym pliku nie jest stała).
Skrót `JOSEPH.` znika, bo `Alpha_fr` niesie pełną nazwę. Gdy żadne pole nie pasuje,
narzędzie **przerywa** i mówi, której stacji nie umie dopasować.

Kolejność stacji wobec `lines.json` jest sprawdzana przez walidator dla każdej osi:

| pakiet | wynik walidatora |
|---|---|
| A, B, D, E | `kolejność stacji zgodna z lines.json` |
| C, F | `kolejność stacji zgodna z lines.json, oś biegnie odwrotnie do kolejności z listy` |

`lines.json` wypisuje L5 od Erasme i L6 od Roi Baudouin, a pakiety C i F są
zdefiniowane w drugą stronę (Jacques Brel → Erasme, Belgica → Roi Baudouin).
Oś nie jest kierunkiem jazdy, więc zgodność z listą odwróconą jest tak samo
poprawna — ale dotąd walidator uznawał ją za **błąd**. Poprawka jest w
`tools/track/validate.py` i wypisuje, którą wersję dopasował, zamiast milczeć.

Niezależna kontrola pozycji stacji — te same `stop_id` w feedzie GTFS
(`data/network/stops.json`, WGS84) przeliczone do Lamberta i porównane z kotwicą
na osi:

| pakiet | dopasowanych po `stop_id` | mediana | maks. |
|---|---:|---:|---:|
| A | 12/12 | 0,04 m | 0,10 m |
| B | 9/9 | 0,06 m | 0,10 m |
| C | 9/9 | 0,04 m | **2,45 m** (Erasme) |
| D | 7/7 | 0,06 m | 0,10 m |
| E | 17/17 | 0,07 m | 0,10 m |
| F | 7/7 | 0,04 m | 0,08 m |

To kontrola **wewnętrzna STIB** (dwa pliki tego samego wydawcy), więc dowodzi
spójności identyfikatorów i pozycji, a nie poprawności wobec terenu. 2,45 m przy
Erasme to ta sama liczba, co `offset_from_axis_m = 2,518` — punkt przystanku nie
leży dokładnie na polilinii trasy, jedyny taki przypadek w sześciu pakietach.

## 5. Krok próbkowania — mierzony, nie odziedziczony

Łamana źródłowa jest zdigitalizowana różnie w różnych pakietach:

| pakiet | wierzchołków w wycinku | odstęp min | mediana | maks. | R min na źródle | R P05 na źródle |
|---|---:|---:|---:|---:|---:|---:|
| A | 345 | 0,42 m | 8,77 m | 416,41 m | 4,8 m | 84,4 m |
| B | 303 | 0,42 m | 10,53 m | 187,19 m | 16,5 m | 96,2 m |
| C | 275 | 1,49 m | 10,43 m | 368,90 m | 35,1 m | 117,0 m |
| D | 123 | 0,67 m | 14,16 m | 249,36 m | 152,5 m | 168,6 m |
| E | 307 | 0,22 m | 14,50 m | 325,35 m | 19,2 m | 117,1 m |
| F | 243 | 1,49 m | 10,04 m | 256,00 m | 18,5 m | 71,7 m |

Promienie 0,2–1,5-metrowych cięciw to **szum digitalizacji**, nie łuki toru — ta
sama obserwacja co na pakiecie A, potwierdzona na wszystkich pozostałych.

Przebieg kontrolny krokami 5 / 10 / 15 / 20 / 25 m dla każdego pakietu
(pełne wyjście w `tools/track/build_alignment.py --step …`):

| krok | maks. odstęp punktów | R min (najgorszy pakiet) | źródło → oś (najgorszy) |
|---:|---:|---:|---:|
| 5 m | 7,5 m | **60,5 m** (D) | 0,111 m |
| 10 m | 15,0 m | 92,8 m (C) | 0,235 m |
| **15 m** | **22,4 m** | **97,3 m** (A) | **0,369 m** |
| 20 m | 29,9 m | 98,8 m (A) | 0,538 m |
| 25 m | 36,9 m | 100,3 m (A) | 0,813 m |

Granice z `tools/track/validate.py` to `max_point_gap_m = 25` i
`min_radius_m = 90`. Kroki 20 i 25 m **łamią pierwszą** (odstęp dochodzi do
1,5 × kroku, bo próbka bliżej niż pół kroku od kotwicy stacji jest odrzucana),
a krok 5 m **łamie drugą na wszystkich sześciu pakietach** (60,5–80,2 m), bo
wpuszcza szum digitalizacji z powrotem do promieni. **15 m jest jedynym z badanych kroków,
który spełnia oba warunki na wszystkich sześciu pakietach** — i to jest powód,
dla którego zostaje, a nie „bo tak było w pakiecie A". Żaden pakiet nie wymaga
własnego kroku; odcinki naziemne (D) są zdigitalizowane **rzadziej**, nie gęściej.

## 6. Kontrola krzyżowa

### 6.1 Wewnątrz STIB — drugi wariant i druga linia

| pakiet | porównanie | mediana | P95 | maks. |
|---|---|---:|---:|---:|
| B | `001m` v2 | 3,27 m | 4,03 m | 4,58 m |
| C | `005m` v1 | 3,45 m | 8,53 m | 9,51 m |
| D | `005m` v2 | 3,16 m | 3,41 m | **51,98 m** |
| E | `002m` v1 | 3,27 m | 11,85 m | 25,75 m |
| E | `006m` v1 | 3,27 m | 11,85 m | 25,75 m |
| E | `006m` v2 | **0,00 m** | **0,00 m** | **0,00 m** |
| F | `006m` v1 | 4,77 m | 12,21 m | 16,91 m |

Powtarza się obraz z pakietu A: warianty tej samej linii są odsunięte o stałe
~3,2–4,8 m (dwa tory), a różne linie na wspólnym odcinku mają **identyczną**
geometrię (E: 2 i 6, zero co do trzeciego miejsca po przecinku). Maksimum
51,98 m na pakiecie D leży na pętli końcowej Herrmann-Debroux, gdzie warianty
się rozchodzą; 25,75 m na E — w rejonie Beekkant, tak samo jak na A.

### 6.2 UrbIS / Brussels Mobility (`bm_public_transport:Metro`, CC0)

156 obiektów (69 MS, 87 MT), poligony, WGS84 → EPSG:31370. **Miarą jest
pokrycie, nie odchyłka** — to poligony, nie oś toru.

| pakiet | w tunelu (MT) | w stacji (MS) | poza |
|---|---:|---:|---:|
| A | 57,3 % | 25,3 % | 17,4 % |
| B | 66,5 % | 25,9 % | 7,6 % |
| C | 68,7 % | 31,3 % | 0,0 % |
| D | 57,8 % | 22,9 % | 19,4 % |
| E | 54,1 % | 26,4 % | 19,6 % |
| F | 70,9 % | 27,8 % | 1,3 % |

Brak pokrycia **nie jest dowodem na nic** — warstwa regionalna ma własne
uproszczenia i miejscami wąskie obrysy biegnące tuż obok osi.

### 6.3 OpenStreetMap (ODbL) — po relacjach tras, nie po bboxie

Overpass jest z tego środowiska nadal nieosiągalny (`Connection reset by peer`
na `overpass-api.de`, HTTP 502 na `overpass.kumi.systems` i
`overpass.private.coffee`; `overpass.osm.ch` odpowiada, ale obsługuje wyłącznie
Szwajcarię i na Brukselę zwraca zero elementów). **Zwykłe API OSM
(`api.openstreetmap.org`) działa**, więc kontrola idzie przez relacje tras:
`tools/track/fetch_osm_routes.py` przelicza pierwszą stację osi do WGS84, bierze
mały wycinek `/api/0.6/map`, wyciąga lokalne way'e `railway=subway`, pyta o ich
relacje macierzyste i zostawia `route=subway` o `ref` zgodnym z linią osi.
Żaden identyfikator relacji nie jest wpisany w kod.

Dwie rzeczy, które to naprawia wobec zapytania bboxowego: stały bbox pnia z
`crosscheck_alignment.py` nie obejmował ani Stockel, ani Erasme, ani Roi
Baudouin (dla B–F dawałby ciche zero pokrycia — teraz bbox liczy się z osi), a
ekstrakt bboxowy mieszał linie biegnące obok siebie.

| pakiet | way | pokrycie (r = 50 m) | mediana | P95 | maks. |
|---|---:|---:|---:|---:|---:|
| A | 124 | 100,0 % | 0,94 m | 4,12 m | 5,93 m |
| B | 118 | 100,0 % | 0,77 m | 5,57 m | 18,05 m |
| C | 162 | 100,0 % | 0,82 m | 2,52 m | 4,55 m |
| D | 162 | 100,0 % | 1,00 m | 3,15 m | 4,41 m |
| E | 130 | 100,0 % | 1,35 m | 8,07 m | 14,09 m |
| F | 162 | 100,0 % | 0,72 m | 2,34 m | 4,64 m |

Osobno dla każdej relacji kierunkowej — to jest pomiar, który mówi, **na którym
torze leży oś**:

| pakiet | relacja OSM | mediana | P95 | maks. |
|---|---|---:|---:|---:|
| A | 58240 `Gare de l'Ouest → Stockel` | **0,97 m** | 4,65 m | 7,82 m |
| A | 7006075 `Stockel → Gare de l'Ouest` | 4,17 m | 8,77 m | 12,92 m |
| B | 58240 `Gare de l'Ouest → Stockel` | 3,16 m | 9,18 m | 20,02 m |
| B | 7006075 `Stockel → Gare de l'Ouest` | **1,81 m** | 8,22 m | 18,05 m |
| C | 58241 `Erasme → Herrmann-Debroux` | 4,00 m | 8,59 m | 10,21 m |
| C | 6996916 `Herrmann-Debroux → Erasme` | **0,86 m** | 2,97 m | 8,38 m |
| D | 58241 `Erasme → Herrmann-Debroux` | 2,41 m | 6,33 m | 7,99 m |
| D | 6996916 `Herrmann-Debroux → Erasme` | 2,19 m | 5,14 m | 6,53 m |
| E | 58242 `Simonis → Elisabeth` | 3,74 m | 12,62 m | 24,82 m |
| E | 7305691 `Elisabeth → Simonis` | **2,49 m** | 11,94 m | 22,66 m |
| F | 108101 `Roi Baudouin → Elisabeth` | 3,32 m | 10,97 m | 14,94 m |
| F | 7927168 `Elisabeth → Roi Baudouin` | **0,72 m** | 4,59 m | 12,36 m |

Mediana **0,97 m** dla pakietu A i relacji 58240 zgadza się co do centymetra z
liczbą podaną w `reports/L1_A-crosscheck.md`, choć tam liczono odsunięcie węzłów
OSM od osi, a tu punktów osi od way'ów OSM. To niezależne odtworzenie wyniku,
który wcześniej powstał ręcznie.

Pakiety C i F leżą **najbliżej relacji zgodnej z kierunkiem pakietu**
(HD → Erasme dla C, Elisabeth → Roi Baudouin dla F) — czyli wybór wariantu
powrotnego z §3 trafia w tor, po którym rzeczywiście jedzie się z `from` do `to`.
Pakiet B jest tu wyjątkiem: bliżej mu do relacji przeciwnej (1,81 m wobec 3,16 m).
Z tych danych **nie da się rozstrzygnąć**, czy to kwestia mapowania OSM na
odgałęzieniu Stockel, czy digitalizacji STIB — i nie jest to rozstrzygane.

## 7. Pakiet E jako pierścień — rozstrzygnięcie

**Pakiet E jest zwykłym, otwartym odcinkiem i kilometraż jest na nim liczbą
sensowną.** Nie wymaga traktowania pętlowego. Uzasadnienie jest pomiarowe:

1. Pełna linia `002m` v2 ma 10 299,9 m i **nie jest domknięta**: jej końce
   (Elisabeth 8471 i Simonis 8763) dzieli 96,3 m. Wariant v1 kończy się na innej
   parze peronów i tam odległość końców to 18,7 m. W żadnym z wariantów
   polilinia nie wraca do punktu startu.
2. Pakiet E kończy się na **Beekkant, kilometraż 9021,3 m**. Do Simonis zostaje
   jeszcze **1278,6 m** (Beekkant → Osseghem → Simonis), więc pakiet urywa się
   ponad kilometr przed miejscem, w którym pierścień mógłby się domknąć.
3. Odległość pierwszego punktu osi (Elisabeth) od ostatniego (Beekkant) to
   **1213 m w linii prostej** przy 9021 m długości osi — pakiet E to podkowa,
   nie pętla (potwierdza to rzut w planie, `build/L2_E.svg`).

Wniosek dla późniejszych zadań: linie 2 i 6 tworzą pierścień **jako sieć**, ale
żaden pojedynczy rekord `ACTU_LIGNES_BRUTES` nie jest zamkniętą krzywą, a pakiet
E nie obejmuje odcinka domykającego. Gdyby ktoś kiedyś chciał osi zamkniętej,
musiałby ją **skleić z dwóch źródeł** i wtedy dopiero pojawia się pytanie o
chainage modulo obwód. Dziś to pytanie nie występuje.

## 8. Simonis / Elisabeth — jawny wybór, nie ciche naprawianie

`docs/00-network-data.md` deklaruje 59 stacji metra; `lines.json` ma 60
unikalnych nazw, GTFS 60 kontenerów stacyjnych, a OSM 60 nazw. Źródłem różnicy
jest ta sama para, co w T-110: **Simonis i Elisabeth są w danych dwiema
osobnymi stacjami**.

Zmierzone odległości peronów w `ACTU_STOPS` (EPSG:31370):

| para | odległość |
|---|---:|
| Elisabeth 8472 ↔ Simonis 8764 | **18,7 m** |
| Elisabeth 8471 ↔ Simonis 8763 | 96,3 m |
| Elisabeth 8471 ↔ Elisabeth 8472 | 56,9 m |
| Simonis 8763 ↔ Simonis 8764 | 63,9 m |

Perony obu „stacji" stoją bliżej siebie niż własne perony każdej z nich. GTFS
mimo to trzyma je jako `station_id` 38 i 53, obie obsługiwane przez linie 2 i 6.
OSM osobno mapuje `Metro 2: turnaround at Simonis` (relacja 7756427) i
`Metro 2: turnaround at Elisabeth` (7756453) — czyli dwie pętle końcowe.

**Wybór:** pakiet E zaczyna się na **Elisabeth, peron `stop_id` 8471**, zgodnie
z `build_packages[E].from`, i kończy na Beekkant. Simonis **nie wchodzi** do
pakietu E ani do żadnego innego. Nie scalono Elisabeth z Simonis, nie usunięto
żadnej z nich i nie zmieniono `lines.json` — rozbieżność 60 vs 59 zostaje
zapisana jako fakt, bo jej rozstrzygnięcie („czy to jedna stacja z dwiema
nazwami") jest decyzją właściciela, nie skutkiem ubocznym budowy osi.

Konsekwencja policzalna: **Simonis i Osseghem nie należą do żadnego pakietu**
budowy. Poza pakietami zostaje pięć odcinków międzypakietowych:

| odcinek | linia | długość |
|---|---|---:|
| Merode → Montgomery | `001m` v1 | 708,9 m |
| Jacques Brel → Gare de l'Ouest | `005m` v1 | 593,8 m |
| Merode → Thieffry | `005m` v1 | 764,4 m |
| Beekkant → Osseghem → Simonis | `002m` v2 | 1278,6 m |
| Simonis → Belgica | `006m` v2 | 688,0 m |

Razem **4034 m**. Sześć pakietów daje 34 481 m osi, czyli sieć rozpisana na
pakiety ma ~38,5 km wobec 39,9 km deklarowanych w `docs/00-network-data.md`.
Nie „poprawiono" tego po cichu: `lines.json` definiuje pakiety tak, jak
definiuje, a domknięcie sieci jest osobną decyzją.

## 9. Gdzie model zamkniętej rury jest niewłaściwy

To jest **wejście dla T-210 i R-005 (#17), nie rozstrzygnięcie**.
`data/network/sources.json` mówi wprost, że pola poziomu w UrbIS wymagają
interpretacji, a dataset nigdzie nie definiuje, czym różni się `niveau = '0'`
od `niveau = '-'`. Poniżej jest **pomiar**, nie wniosek o terenie.

| pakiet | punktów w poligonach `niveau = 0` | udział | poligony | kilometraż |
|---|---:|---:|---|---|
| A | 18 / 447 | 4,0 % | Tunnel Beekkant – Gare de l'Ouest | 45–135, 690–840 m (240 m) |
| B | **0** / 340 | 0,0 % | — | — |
| C | 31 / 361 | 8,6 % | Station Erasme, Tunnel Erasme – Eddy Merckx | 4937–5386 m (449 m) |
| D | **97** / 258 | **37,6 %** | Pétillon–Hankar, Hankar–Delta, Beaulieu–Demey, Demey–Herrmann-Debroux | 704–1243, 1437–1452, 1512–1587, 2470–3144, 3323–3398 m (1377 m) |
| E | 12 / 603 | 2,0 % | Tunnel Delacroix – Clemenceau | 7762–7927 m (165 m) |
| F | 47 / 299 | 15,7 % | Station Pannenhuis, Tunnel Pannenhuis – Belgica | 60–748 m (688 m) |

Czytanie tego, ostrożnie:

- **D — model zamkniętej rury jest na pewno niewłaściwy.** Dwie niezależne
  przesłanki mówią to samo: `lines.json` wpisuje pakietowi D `unlocks: wiadukt`,
  a UrbIS znakuje `niveau = 0` na 37,6 % punktów, w tym na ciągłym odcinku
  673,6 m między Beaulieu a Demey. Do tego 19,4 % punktów pakietu D leży poza
  jakimkolwiek poligonem metra.
- **F — ciągły odcinek Belgica – Pannenhuis, kilometraż 60–748 m osi (688 m),
  razem ze stacją Pannenhuis**, jest oznaczony `niveau = 0`. Pannenhuis jest też
  wymieniony w `reports/L1_A-geometry.md` jako znany odcinek naziemny.
- **C — rejon Erasme, kilometraż 4937–5386 m (449 m, koniec osi)**, łącznie ze
  stacją. Ta sama uwaga.
- **E — Delacroix – Clemenceau, kilometraż 7762–7927 m (165 m)**, znów odcinek
  wymieniony w raporcie geometrii pakietu A.
- **B — sprzeczność, której nie rozstrzygam.** `lines.json` deklaruje pakietowi B
  `unlocks: odcinki naziemne`, a UrbIS **nie znakuje ani jednego punktu** jako
  `niveau = 0` (0 z 340). Jedno z dwóch: albo `unlocks` mówi o czymś innym niż
  pole `niveau`, albo warstwa regionalna tego nie zapisuje. 7,6 % punktów
  pakietu B leży poza poligonami, więc dane po prostu milczą.
- **A** — 18 punktów w dwóch przedziałach, razem 240 m z 6686 m: dokładnie ta
  sama liczba, co zmierzona w `reports/L1_A-geometry.md` (tam podana jako 3,6 %
  **długości**, tu jako 4,0 % **punktów** — to dwa sposoby liczenia tego samego
  pokrycia). Metoda odtwarza wcześniejszy wynik.

Czego **nie** zrobiono: nie wygenerowano tuneli, nie zmieniono profili, nie
podjęto decyzji, czy `niveau = 0` znaczy „na poziomie terenu". Przedziały
kilometrażu są w raportach `build/*-crosscheck.json`, gotowe jako wejście dla
generatora, który kiedyś będzie musiał przestać budować rurę.

## 10. Błąd wykryty przy okazji i naprawiony

`slice_polyline()` gubił **ostatni wierzchołek** wycinka, gdy wycinek kończył się
dokładnie na końcu polilinii. Pętla po segmentach dopisuje tylko początki
segmentów i cięcie wewnątrz segmentu, a przy `end == chain[-1]` żaden segment nie
spełnia warunku `c0 <= end < c1`. W kodzie stał po tej pętli martwy blok
`if not out or ...: pass` — ktoś to widział i nie dokończył.

Skutek był mierzalny i dotyczył pakietów kończących się na pętli końcowej linii:
oś pakietu D wychodziła **3760,40 m zamiast 3847,23 m** (brakowało 86,8 m) i miała
**zdublowany punkt** przy kotwicy Herrmann-Debroux (`min_point_gap_m = 0,00`),
bo kotwica wypadała poza skróconą łamaną. Po poprawce: 3847,23 m, najmniejszy
odstęp 10,78 m.

Kontrola regresji: pakiet A przebudowany po poprawce jest **bajtowo identyczny**
z wersją skomitowaną, a pakiety B i C dały te same długości przed i po zmianie
(5083,23 m i 5386,41 m). Testy `test_packages_slice_keeps_last_vertex_when_cut_is_at_polyline_end`
i `test_packages_resample_at_line_end_has_no_zero_gap` pilnują obu objawów.

## 11. Weryfikacja

```
python3 tools/tests/test_all.py        ->  347/347 przeszło
bash doctor.sh                          ->  0 pozycji do naprawienia
python3 tools/track/validate.py <oś> --line <linia>  ->  0 błędów × 6 osi
python3 tools/track/data_freshness.py  ->  13 przeterminowanych okien (patrz niżej)
```

Doszło 29 testów w `tools/tests/test_packages.py` — bez sieci, bez pytest, bez
archiwum STIB; dane syntetyczne tam, gdzie się da, gotowe artefakty tylko gdy
istnieją. Do `.github/workflows/python-tests.yml` doszedł krok, który waliduje
**każdą** oś z `data/track` i wymaga co najmniej sześciu.

**Okno ważności.** Wszystkie sześć osi pochodzi z tego samego archiwum, co
pakiet A: `Date_debut 02/03/2026 … Date_fin 28/08/2026`, pobranego 01.09.2026,
czyli **cztery dni po wygaśnięciu**. To nie jest błąd (`docs/09-data-provenance.md`
§ „Okno ważności"), ale żadnej z tych osi nie wolno nazywać „aktualną" bez
świeższego snapshotu.

## 12. Czego świadomie nie zrobiono

- **Tuneli i geometrii 3D** — to zakres T-210; §9 jest dla niego wejściem.
- **Profilu pionowego** — każda oś ma `vertical.status = "not_modelled"` i Z = 0.
  T-112 pozostaje zablokowane brakiem publicznych rzędnych główki szyny (T-901).
- **Głębokości stacji** — `depth_m: null` we wszystkich 61 stacjach sześciu
  pakietów, jak w pakiecie A.
- **`data/track/L1_A.provenance.json` nie został przepisany**, mimo że nowa
  wersja narzędzia dołożyłaby do niego pola `selection.candidates`,
  `selection.rule` i trzy statystyki. Sama oś jest identyczna bajtowo; przepisanie
  provenance pakietu A w zadaniu o pakietach B–F byłoby zmianą pliku spoza zakresu.
- **Odcinków międzypakietowych** (§8, 4034 m) — `lines.json` ich nie przypisuje
  do żadnego pakietu i nie jest moją decyzją to zmienić.
- **Rozstrzygnięcia Simonis/Elisabeth** — zmierzone i opisane, nieprzesądzone.
- **Rozjazdów, węzła Beekkant, układu tor-po-torze** — `ACTU_LIGNES_BRUTES` to
  trasy handlowe; ograniczenie jest to samo, co w pakiecie A.

## 13. Atrybucja

- STIB/MIVB — Open Data, dystrybucja Belgian Mobility, **CC BY 4.0**:
  `Source: STIB-MIVB - Open Data - 2026-09-01`.
- Brussels Mobility / Paradigm, warstwa `bm_public_transport:Metro` — **CC0**.
- OpenStreetMap contributors — **ODbL 1.0** (`api.openstreetmap.org`, relacje
  58240, 7006075, 58241, 6996916, 58242, 7305691, 7756427, 7756453, 108101,
  7927168).
