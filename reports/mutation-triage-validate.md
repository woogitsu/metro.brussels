# Triaż mutacji: `tools/track/validate.py` i `tools/track/crosscheck_alignment.py`

Data: 03.09.2026. Narzędzie: `tools/tests/mutation_sweep.py` (gałąź
`mutacje-raport-przeliczony`; **plik roboczy, nie jest na `main`** i nie wchodzi
do tego commita). Mutowany jest kod pod testem, nie testy.

## 0. Dlaczego akurat te dwa moduły

`validate.py` jest jedyną bramką, która mówi „ta oś nadaje się do geometrii", a
`crosscheck_alignment.py` jedynym miejscem w repo, które mówi „nasza oś zgadza się
z drugim źródłem" — jego wynik idzie do `*.provenance.json` i dalej jest cytowany
jako fakt. Oba miały udział ocalałych mutacji wyższy niż jakikolwiek inny moduł
w `tools/track`.

## 1. Wynik

| moduł | mutacji | ocalałych PRZED | ocalałych PO | zabitych **w tym kroku** | pokrycie przed → po |
|---|---|---|---|---|---|
| `tools/track/validate.py` | 36 | 23 | 2 | 21 | 36,1 % → 94,4 % |
| `tools/track/crosscheck_alignment.py` | 19 | 18 | 2 | 16 | 5,3 % → 89,5 % |
| **razem** | **55** | **41** | **4** | **37** | **25,5 % → 92,7 %** |

Kolumna „zabitych w tym kroku" liczy mutacje, które **przeżyły** stan wyjściowy
i padły po dopisaniu testów. Zabitych łącznie jest 34 i 17 — reszta padała już
wcześniej.

Wszystkie cztery pozostałe są **mutantami równoważnymi** — uzasadnienie w §4,
z wykonania, nie z lektury. Kodu produkcyjnego nie zmieniono: przegląd nie
znalazł usterki, znalazł brak pokrycia.

Dopisane testy: 11 w `tools/tests/test_validate_axis.py`, 20 w nowym
`tools/tests/test_crosscheck_alignment.py`. Zestaw: **723/723 przeszło**
(przed: 692/692).

## 2. Co się dało zrobić dopiero po trafieniu w próg

`>` różni się od `>=` **wyłącznie** w punkcie równości. Istniejące testy stały
obok progu (±1 %, ±0,5 m) i dlatego nie odróżniały jednego od drugiego —
mierzyły, że reguła istnieje, nie gdzie leży jej granica.

**Pułapka zmiennoprzecinkowa.** Naiwna fikstura „dokładnie na granicy" granicy
nie dotyka:

```
>>> (885.0 + 0.01) - 885.0
0.009999999999990905          # PONIŻEJ progu 0,01 — a nie na nim
```

Mantysa 0,01 jest nieparzysta na poziomie 2⁻⁵⁹, więc dla `total` rzędu setek
metrów żaden double nie leży od niego dokładnie o 0,01. Różnica jest dokładna
tylko wtedy, gdy jedna strona jest zerem albo gdy próg da się zapisać w
najmłodszych bitach obu stron. Każde takie obejście jest w kodzie testu opisane
w docstringu; poniżej skrót, bo to jest właściwa treść tego triażu:

| próg | jak trafiony dokładnie |
|---|---|
| `abs(d) < 1e-9` (`radius3`) | `2 · 5e-10` — mnożenie double'a przez dwa nie zmienia mantysy, więc wynik to co do bitu ten sam double, co stała `1e-9` |
| `drift > 0.01` (`length_m`) | łamana o **zerowej** długości: `abs(0.01 − 0.0)` jest dokładne, bo jedna strona to zero |
| `h < 1e-6` (pochylenie) | `math.dist((1e-6, 0), (0, 0))` to `hypot(1e-6, 0.0)` — zwraca argument bez arytmetyki |
| `g > 4.0` (pochylenie) | `0,6 / 15 · 100` daje w double dokładnie `4.0` (sprawdzone asercją w teście) |
| `rad < 90.0` (promień) | okrąg (±90, 0), (0, ±90): wyznacznik i liczniki na całkowitych wielokrotnościach 8100, dzielenie dokładne |
| `over > gaps[-1]` (rzut stacji) | `900.0 − 885.0` — obie liczby całkowite, różnica dokładna |
| `over > 0.01` (rzut stacji) | oś **14-milimetrowa** (2 mm + 12 mm): jedyny zakres, w którym 0,01 mieści się w najmłodszych bitach obu stron, a ostatni odcinek jest wciąż dłuższy niż 0,01 |
| `ch[0] < -0.01` | wprost: `ch[0]` jest porównywane ze stałą bez odejmowania |
| `d <= 50.0` (promień pokrycia) | punkt (50, 50) nad odcinkiem (0,0)–(100,0): `t` wychodzi 0,5, `math.dist` na różnicy (0, 50) zwraca `50.0` bez zaokrąglenia |
| `t > 1.0` (przycięcie rzutu) | `100,5 · 100 / 10000 = 1.005` — krótkie mantysy binarne |

## 3. Tabela: wszystkie 41 mutacji, które przeżyły stan wyjściowy

Werdykt „**zabita**" znaczy: po dopisaniu testu przebieg `mutation_sweep.py` na
zacommitowanym drzewie zgłasza ją jako zabitą. Nie „powinna być zabita".

### `tools/track/validate.py`

| wiersz | mutacja | werdykt | uzasadnienie |
|---|---|---|---|
| 26 | `abs(d) < 1e-9` → `<=` | zabita | `d` równe dokładnie 1e-9 to jeszcze łuk (R = 0,5 m), nie prosta; mutant zwraca `inf`, czyli „nie ma sprawy" |
| 26 | `1e-9` → `1.01e-09` | zabita | jw. — ten sam próg, ta sama fikstura |
| 57 | `drift > 0.01` → `>=` | zabita | rozjazd równy rozdzielczości zapisu nie jest błędem; mutant zgłasza błąd na zgodnym pliku |
| 67 | `h < 1e-6` → `<=` | zabita | odcinek 1 µm ma dostać policzone pochylenie; mutant przeskakuje odcinek o pochyleniu 100 % bez słowa |
| 67 | `1e-6` → `1.0099999999999999e-06` | zabita | jw. |
| 69 | `g > abs(worst_g)` → `>=` | zabita | przy remisie raportowany ma być **pierwszy** odcinek; numer punktu idzie do komunikatu, więc remis nie jest tu obojętny |
| 70 | `g > 4.0` → `>=` | zabita | 4 % to wartość dopuszczalna (`docs/TASKS.md`, T-112: „pochylenia 0–4%"), nie przekroczenie |
| 71 | `worst_i >= 0` → `>` | zabita | oś, której najostrzejszy odcinek jest **pierwszy**, traci cały wiersz o pochyleniu |
| 71 | `0` → `1` | zabita | jw. |
| 75 | `rad < worst_r` → `<=` | zabita | jak 69, tylko dla promienia: przy remisie ma wygrać pierwszy indeks |
| 76 | `rad < 90.0` → `<=` | zabita | 90 m to promień dopuszczalny; mutant zgłasza błąd na łuku granicznym |
| 77 | `worst_r != inf` → `==` | zabita | warunek jest spełniony **zawsze**, gdy `worst_ri >= 0`, więc odwrócenie kasuje wiersz „najmniejszy promień" z każdego raportu |
| 77 | `worst_ri >= 0` → `>` | **równoważna** | §4.1 |
| 77 | `0` → `1` | **równoważna** | §4.1 |
| 107 | `over > gaps[-1]` → `>=` | zabita | przekroczenie równe ostatniemu odcinkowi to jeszcze artefakt rzutowania (ostrzeżenie), nie stacja poza osią (błąd) |
| 110 | `over > 0.01` → `>=` | zabita | rzut przesunięty o rozdzielczość zapisu ma milczeć; mutant ostrzega o każdym pliku |
| 114 | `ch[0] < -gaps[0]` → `<=` | zabita | symetria progu z 107 po drugiej stronie osi |
| 117 | `ch[0] < -0.01` → `<=` | zabita | symetria progu z 110 |
| 122 | `len(missing) > 5` → `>=` | zabita | wielokropek przy **pełnej** liście — komunikat kłamie, że coś uciął |
| 122 | `5` → `6` | zabita | lista ucięta **bez** znaku, że jest ucięta — kłamie w drugą stronę |
| 140 | `5 <= kmh` → `<` | zabita | 5 km/h (manewrowa) to wartość prawidłowa; mutant odrzuca poprawny plik |
| 140 | `kmh <= 80` → `<` | zabita | 80 km/h jw. |
| 140 | `5` → `6` | zabita | jw., dolna granica |

### `tools/track/crosscheck_alignment.py`

| wiersz | mutacja | werdykt | uzasadnienie |
|---|---|---|---|
| 69 | `(y1 > y) != (y2 > y)` → `(y1 >= y) …` | zabita | warunek jest **jedyną** ochroną przed dzieleniem przez `y2 - y1 == 0`; punkt na wysokości krawędzi poziomej wywala moduł `ZeroDivisionError` |
| 69 | `… != (y2 > y)` → `… >= y` | zabita | jw., druga strona |
| 69 | `!=` → `==` | zabita | jw. — odwrócenie łapie dokładnie krawędzie poziome |
| 71 | `x < xin` → `<=` | zabita | punkt na lewej krawędzi ma być wewnątrz; przy `<=` wypada poza **każdy** poligon, choć leży w stykających się |
| 78 | `kind == "Polygon"` → `!=` | zabita | warstwa z samych `Polygon` daje zero pierścieni, czyli ciche „0 % osi w tunelu" zamiast błędu |
| 80 | `kind == "MultiPolygon"` → `!=` | zabita | jw. |
| 153 | `hit["niveau"] == "0"` → `!=` | zabita | przedziały kilometrażu „prawdopodobnie naziemne" opisywałyby odcinki **podziemne**; to wejście dla R-005 |
| 154 | `hit["niveau"] == "0"` → `!=` | zabita | jw., dla listy nazw poligonów |
| 233 | `d <= 50.0` → `<` | zabita | punkt oddalony dokładnie o promień pokrycia jeszcze się liczy |
| 246 | `e.get("type") == "way"` → `!=` | zabita | filtr wybierałby „wszystko oprócz way'ów"; odchyłka liczona od geometrii, która nie jest torem |
| 264 | `route.get("id") == relation` → `!=` | zabita | kierunkowi podpinana jest nazwa **sąsiedniego** kierunku; raport wygląda tak samo i jest nieprawdziwy |
| 289 | `seg <= 0` → `<` | zabita | powtórzony wierzchołek (w OSM normalny po scaleniu way'ów) → `ZeroDivisionError` w środku kontroli |
| 289 | `0` → `1` | zabita | odcinki krótsze niż 1 m przestają być rzutowane; różnica rzędu całej mierzonej odchyłki |
| 293 | `1.0` → `1.01` | zabita | rzut nie jest przycinany do końca odcinka → odchyłka **0,0 m tam, gdzie jej nie ma** |
| 293 | `t < 0` → `<=` | **równoważna** | §4.2 |
| 293 | `t > 1.0` → `>=` | **równoważna** | §4.2 |
| 317 | `entry["status"] != "ok"` → `==` | zabita | źródło sprawdzone dostaje jednolinijkowe „ok" bez ani jednej liczby, a pominięte wpada w gałąź szczegółów i wywala moduł |
| 321 | `name == "urbis"` → `!=` | zabita | UrbIS trafia do gałęzi OSM → `KeyError` |

## 4. Cztery równoważne — klasyfikacja z wykonania

Metoda: oryginał i mutant ładowane obok siebie (`importlib.util.spec_from_file_location`
na pliku tymczasowym z zastosowaną mutacją), ta sama bateria wejść przez oba,
porównywany **pełny** wynik. Bateria: patologie wypisane z ręki + losowe z ziarnem
`20260903`. Skrypt: `rownowaznosc.py` (roboczy, poza repo).

**Kontrola negatywna samej metody.** „Zero różnic" znaczy coś tylko wtedy, gdy
narzędzie w ogóle umie różnicę zobaczyć. Ta sama bateria puszczona przez mutacje,
o których wiemy, że są obserwowalne:

```
    tools/track/validate.py:76 operator `<` -> `<=`
  76 < -> <=: wejść 133, różnic 2
    tools/track/crosscheck_alignment.py:289 operator `<=` -> `<`
  289 <= -> <: wejść 411, różnic 54
```

**I od razu ograniczenie tej metody, bo jest istotne:** ta sama bateria dała
**zero** różnic dla `validate.py:70 > → >=` i `crosscheck_alignment.py:293
1.0 → 1.01`, które oba są obserwowalne i oba zostały zabite dopisanymi testami.
Losowa bateria nie trafia w punkty równości — z definicji. Dlatego poniższe
werdykty **nie opierają się na braku różnic w baterii**, tylko na wyczerpaniu
dziedziny.

### 4.1 `validate.py:77` — `worst_ri >= 0` → `> 0` oraz → `>= 1`

`worst_ri` jest przypisywane **wyłącznie** wewnątrz `for i in range(1, len(pts)-1)`
(wiersz 73) i poza tym ma wartość początkową `-1`. Jego dziedzina to więc
`{-1} ∪ [1, ∞)` — **zero jest nieosiągalne**. Na tej dziedzinie `>= 0`, `> 0`
i `>= 1` dzielą ją identycznie.

Sonda po całej baterii potwierdza dziedzinę:

```
   zaobserwowane worst_ri: [-1, 1, 2, 3, 4, 5, 6, 7, 8, 9]
   czy 0 wystąpiło: False
   77 >= -> >: wejść 133, różnic 0
   77 0 -> 1: wejść 133, różnic 0
```

To nie jest usterka, tylko nadmiarowość: warunek `worst_ri >= 0` jest napisany
symetrycznie do `worst_i >= 0` w wierszu 71, gdzie zero **jest** osiągalne
(pętla pochylenia leci od 0). Zostawione bez zmian — ujednolicanie tego byłoby
zmianą kodu produkcyjnego bez powodu i poza zakresem zadania.

### 4.2 `crosscheck_alignment.py:293` — `t < 0` → `<=` oraz `t > 1.0` → `>=`

Wyrażenie: `t = 0.0 if t < 0 else (1.0 if t > 1.0 else t)`.

Obie mutacje różnią się od oryginału **tylko** w punkcie równości, a w punkcie
równości obie gałęzie dają tę samą wartość: dla `t == 0.0` oryginał przepuszcza
`t`, mutant wpisuje `0.0`; dla `t == 1.0` oryginał przepuszcza `t`, mutant
wpisuje `1.0`. Sonda po 2013 wartościach `t` (w tym `0.0`, `-0.0`, `1.0`,
`nextafter` w obie strony od obu, denormale, nieskończoności):

```
   `t<0` -> `t<=0`: różnic (z uwzględnieniem znaku zera): 1 [-0.0]
   `t>1.0` -> `t>=1.0`: różnic (z uwzględnieniem znaku zera): 0 []
```

Jedyny przypadek, w którym cokolwiek się różni, to `t == -0.0`. **Jest
osiągalny** — punkt dokładnie w wierzchołku `a` odcinka biegnącego w stronę
malejących `x` i `y` daje licznik `-0.0`:

```
   t = -0.0   math.copysign(1,t) = -1.0
   po przycięciu: oryginał -0.0 mutant 0.0 -> RÓŻNE bity
   odległość: oryginał 0.0 mutant 0.0 -> identyczna: True
```

Różnica ginie na wyjściu i ginie **z powodu, który da się nazwać**, a nie
przypadkiem: `t` jest użyte wyłącznie w `a + t·d`, gdzie `(-0.0)·d` i `0.0·d`
różnią się co najwyżej znakiem zera, a dodanie zera dowolnego znaku nie zmienia
wartości; ostatni krok to `math.dist`, które zwraca moduł i znak zera kasuje.
Nawet w najgorszym przypadku (`a` z ujemnym zerem w obu współrzędnych) punkt
rzutu wychodzi `(0.0, 0.0)` wobec `(-0.0, -0.0)`, a `math.dist` z obu daje `0.0`.
Przemiatanie 20 000 wejść dobranych tak, żeby trafiać w `-0.0`:

```
   trafień t==-0.0: 3693, różnic na wyjściu: 0
```

Werdykt: **równoważne**, z zastrzeżeniem, że równoważność opiera się na tym, iż
`t` nie wycieka poza `_distance_to_polyline`. Gdyby kiedyś zaczęło — na przykład
gdyby moduł raportował kilometraż rzutu — obie mutacje przestałyby być
równoważne i ten akapit trzeba będzie przeczytać jeszcze raz.

## 5. Czego świadomie nie zrobiono

* **Nie zmieniono ani jednego wiersza kodu produkcyjnego.** Przegląd nie znalazł
  usterki. Wszystkie 37 zabitych mutacji to brak pokrycia, nie błędy — kod
  zachowywał się poprawnie, po prostu nikt tego nie sprawdzał.
* Nie ujednolicono nadmiarowego `worst_ri >= 0` (§4.1) — to zmiana kosmetyczna
  poza zakresem zadania.
* Nie mutowano innych modułów; przegląd ograniczony do dwóch wskazanych.
* `tools/tests/mutation_sweep.py` i `rownowaznosc.py` są narzędziami roboczymi
  i **nie wchodzą do repozytorium**.

## 6. Zauważone przy okazji, nie tknięte

* `validate.py:138–140` sięga do `sl["from_m"]`, `sl["to_m"]` i `sl["kmh"]`
  wprost, bez `.get`. Ograniczenie prędkości z literówką w nazwie pola nie da
  komunikatu walidatora, tylko `KeyError` z traceback — czyli walidator, który
  ma nazywać błędy w pliku, sam się na tym pliku wywala. Nie ruszane: to zmiana
  zachowania kodu produkcyjnego, a zadanie tego nie obejmuje.
* `crosscheck_urbis` liczy `niveau0` dwa razy i dwiema różnymi drogami —
  raz przez sumę po `niveau_hits` (wiersz 157), raz przez `niveau0_flags`
  (wiersz 153). Obie muszą dać ten sam wynik i dziś dają; nic tego nie pilnuje
  poza dopisanym testem, który sprawdza obie liczby na tej samej fiksturze.
* `point_in_ring` przyjmuje pierścień jako listę krotek, a `polygon_rings`
  zwraca listy dwuelementowe z GeoJSON-a — działa, bo indeksowanie jest takie
  samo, ale typy w tym module nie są jednorodne.
