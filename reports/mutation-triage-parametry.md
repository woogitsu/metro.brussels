# Triaż ocalałych mutacji — parametry geometrii i metadane

Stan: **2026-09-03**. Wejście: przegląd mutacyjny na `737d592`.
Wyjście: `tools/tests/test_parameter_boundaries.py` (28 testów).
Narzędzie pomiaru: `tools/tests/mutation_sweep.py` z gałęzi `mutacje-raport-przeliczony`
(nie jest częścią tej gałęzi — było użyte i skasowane przed commitem).

Siedem modułów liczy **parametry**, a nie kształty: przekroje tuneli, skrajnię M7,
kilometraże peronów i detali, okna ważności danych. Ocalało w nich **43 mutacje na 64**,
czyli dwie trzecie. `profiles.py` — z którego wynika, czy skład mieści się w tunelu —
miał najgorszy wynik: 11 na 13.

---

## 1. Wynik

| moduł | ocalałych przed | ocalałych po | zabitych nowymi testami |
|---|---|---|---|
| `tools/blender/profiles.py` | 11 / 13 | **1** | 10 |
| `tools/track/detail_layout.py` | 7 / 8 | **1** | 6 |
| `tools/track/network_chainage.py` | 6 / 7 | **0** | 6 |
| `tools/blender/m7_layout.py` | 6 / 17 | **1** | 5 |
| `tools/track/station_layout.py` | 5 / 7 | **1** | 4 |
| `tools/data/provenance.py` | 4 / 7 | **0** | 4 |
| `tools/track/data_freshness.py` | 4 / 5 | **0** | 4 |
| **razem** | **43 / 64** | **4** | **39** |

Cztery, które zostały, są **mutantami równoważnymi albo nieosiągalnymi** — każdy
z dowodem w sekcji 5. Nie są dziurą w pokryciu i nie da się ich zabić testem,
bo nie da się ich zaobserwować.

Rzeczywiste wyjście przemiatania po dopisaniu testów (7 przebiegów, po jednym na moduł,
narastająco):

```
[MUTACJE] rozstrzygniętych 13/13, zabitych 12, ocalałych 1, nierozstrzygniętych 0
[MUTACJE] rozstrzygniętych 20/21, zabitych 18, ocalałych 2, nierozstrzygniętych 1
[MUTACJE] rozstrzygniętych 27/28, zabitych 25, ocalałych 2, nierozstrzygniętych 1
[MUTACJE] rozstrzygniętych 44/45, zabitych 41, ocalałych 3, nierozstrzygniętych 1
[MUTACJE] rozstrzygniętych 51/52, zabitych 47, ocalałych 4, nierozstrzygniętych 1
[MUTACJE] rozstrzygniętych 58/59, zabitych 54, ocalałych 4, nierozstrzygniętych 1
[MUTACJE] rozstrzygniętych 63/64, zabitych 59, ocalałych 4, nierozstrzygniętych 1

  OCALAŁA  tools/blender/m7_layout.py:192 operator `>=` -> `>`
  OCALAŁA  tools/blender/profiles.py:33 operator `>` -> `>=`
  OCALAŁA  tools/track/detail_layout.py:61 operator `<=` -> `<`
  OCALAŁA  tools/track/station_layout.py:116 operator `<` -> `<=`
```

Jedyna **nierozstrzygnięta** to `detail_layout.py:49 <= -> <` — mutant nie kończy się,
tylko ginie od SIGKILL (patrz koniec sekcji 4). Na `main` liczyła się jako zabita
i tak samo liczy się tutaj; nie zmienia bilansu w żadną stronę.

Kontrolą negatywną wszystkich 39 nowych bramek jest to samo przemiatanie: ono dosłownie
wstrzykuje mutację, uruchamia `test_all.py`, sprawdza, że pada, i cofa zmianę. Trzy
testy przypinające liczby projektowe (sekcja 3) nie mają swojej mutacji, więc dostały
kontrolę wstrzykiwaną ręcznie — opis w opisie PR-a.

---

## 2. Jedna przyczyna, wszędzie ta sama

Każdy z 43 przypadków miał ten sam kształt: test podaje wartość **z dala od progu**,
więc sprawdza KIERUNEK nierówności, a nie sam próg. Przykłady z pomiaru:

* korytarz równoległy: testy podają 15 m (w środku) i 5000 m (poza). Próg brzmi 30 m
  i przechodzi zarówno jako `<`, jak i `<=`;
* okno ważności danych: testy podają −4 dni i +19 dni. Próg brzmi 0 i przechodzi
  zarówno z `<`, jak i z `<=`, a nawet z `days < 1`;
* skrajnia w tunelu: `fits_gauge` sprawdza punkty skrajni M7, która przy 0,30 m luzu
  sięga x = ±3,75 m — a ściana `box_double` stoi na ±4,70 m. Siatka 1102 wejść
  trafiła w granicę 20 razy i **ani razu** tam, gdzie pyta bramka.

**Wartość dokładnie równa progowi jest jedynym wejściem, które odróżnia `>` od `>=`.**

---

## 3. Jak klasyfikowano to, czego nie dało się zabić

Nie „przez przeczytanie kodu". Dla każdej mutacji wczytywano **oryginał i mutanta obok
siebie** (`importlib.util.spec_from_file_location`) i przepuszczano przez baterię wejść,
a obok — **trzeci wariant z sondą**: ten sam kod, w którym mutowane porównanie jest
opakowane w funkcję zapisującą, czy lewa strona była DOKŁADNIE równa prawej.

Trzeci wariant jest sednem. **„Zero różnic" nic nie znaczy, jeśli bateria nie trafiła
w punkt równości** — a losowe wejścia z definicji w niego nie trafiają. Dlatego każdy
wiersz tabeli niżej ma kolumnę „traf." — ile wejść baterii wylądowało dokładnie
na granicy.

### Pułapka zmiennoprzecinkowa

Granicę trzeba **skonstruować**, nie zadeklarować:

```
abs((6700.0 + 0.01) - 6700.0)  ->  0.010000000000218   # NAD progiem 0,01
abs((0.01) - 0.0)              ->  0.01                # dokładnie próg
```

Różnica jest dokładna tylko wtedy, gdy jedna strona jest zerem albo gdy próg jest
potęgą dwójki. Testy, które tak kombinują, mówią o tym w docstringu i **sprawdzają
asercją, że konstrukcja nadal jest dokładna** (np. `previous_at + SAME_PLACE_M == point`),
żeby nie zgniła po cichu przy zmianie liczb wokół.

### Progi niewidoczne dla przemiatania

Przemiatanie mutuje literały stojące w **porównaniach**, nie w przypisaniach. Stałe
wyciągnięte na poziom modułu i liczby w słowniku `PROFILES` są dla niego niewidzialne
i nie było ich w żadnej z 64 mutacji — a to one decydują o geometrii. Dopisany
`test_profiles_design_numbers_that_no_other_test_pins` przypina je **liczbą**:
`M7_WIDTH_M` 2,70, `M7_HEIGHT_M` 3,60, `M7_ROOF_CHAMFER_M` 0,35, `CLEARANCE_M` 0,30,
łuk `bore_single` (3,05 / 1,45 / −1,20 / 28 segmentów), `track_offsets` profilu
`station` i `platform_edge_x`.

Skąd te liczby: wszystkie trzy profile mają `source_level="design"`. To są **wartości
projektowe, nie pomiary STIB** — `docs/21-measured-vs-assumed.md` mówi wprost „Żaden
nie jest pomiarem STIB". Test nie twierdzi więc, że tak wygląda tunel w Brukseli;
twierdzi, że projekt nie zmieni się po cichu. Wymiary zewnętrzne i rozstaw torów
`box_double` pilnuje już `test_dimension_audit.py`; reszty nie pilnowało nic.

---

## 4. Tabela triażu

Kolumna „traf." = ile wejść baterii trafiło **dokładnie w granicę** mutowanego
porównania (pomiar sondą, nie deklaracja).

### `tools/blender/profiles.py` — 11 ocalałych

| wiersz | mutacja | traf. | werdykt | uzasadnienie |
|---|---|---|---|---|
| 32 | `>` → `>=` | 1 / 12 | **dziura → test** | `_dedupe` scala punkty bliższe niż `eps`. Równo `eps` to jeszcze scalenie. Obrysy trzech profili nie mają ani jednej takiej pary, więc bez konstrukcji granicy nie da się tego zobaczyć. |
| 33 | `>` → `>=` | 4 / 12 | **równoważny** | Patrz dowód niżej. Cztery trafienia w granicę, zero różnic. |
| 33 | `2` → `3` | 4 / 12 | **dziura → test** | Warunek domknięcia ringu brzmi `len(out) > 2` — trójkąt już wolno domknąć. Zacommitowane profile mają kilkanaście do trzydziestu wierzchołków, więc różnicy nie widać. |
| 33 | `<=` → `<` | 4 / 12 | **dziura → test** | Ostatni punkt równo `eps` od pierwszego jest usuwany. Zdublowany wierzchołek dałby krawędź zerowej długości i zdegenerowaną ściankę w wyciągnięciu. |
| 48 | `<=` → `<` (lewa) | 20 / 1102 | **dziura → test** | Ściana tunelu należy do przekroju: punkt o x = −4,70 m w `box_double` jest wewnątrz. |
| 48 | `<=` → `<` (prawa) | 20 / 1102 | **dziura → test** | To samo po prawej, x = +4,70 m. |
| 54 | `<=` → `<` (lewa) | 4 / 1102 | **dziura → test** | Ta sama granica, drugie z trzech porównań, które ją trzymają (bramka po bbox). |
| 54 | `<=` → `<` (prawa) | 4 / 1102 | **dziura → test** | j.w., prawa strona. |
| 56 | `<=` → `<` (dół) | 6 / 1102 | **dziura → test** | Spód koryta (y = −1,20 m) należy do przekroju. |
| 56 | `<=` → `<` (góra) | 6 / 1102 | **dziura → test** | Sklepienie (y = 4,70 m dla `box_double`, 5,30 m dla `station`) należy do przekroju. |
| 70 | `>` → `>=` | 1 / 5 | **dziura → test** | `eps` bisekcji `min_clearance` jest tolerancją włącznie. Przy domyślnych 1,5 i 0,005 szerokość przedziału to 1,5/2ⁿ i **nigdy** nie zrówna się z progiem — granicę da się trafić tylko potęgą dwójki (`eps = 0,125`). |

**Dlaczego to jest najważniejszy moduł.** Sześć z tych mutacji dotyczy jednego pytania:
czy punkt leżący DOKŁADNIE na ścianie tunelu jest w tunelu. Odpowiedź „nie" nie
wywróciłaby żadnego testu, a `min_clearance` szuka przez bisekcję właśnie luzu,
przy którym skrajnia **dotyka** ściany — czyli odpowiedź zależałaby od tego, po której
stronie ostatniego bitu wypadnie środek przedziału.

### `tools/track/detail_layout.py` — 7 ocalałych

| wiersz | mutacja | traf. | werdykt | uzasadnienie |
|---|---|---|---|---|
| 49 | `0.0` → `0.001` | 1 / 11 | **dziura → test** | Próg kroku hektometrów brzmi „dodatni", nie „większy od milimetra". Jedyny istniejący test podaje zero, a zero leży po tej samej stronie obu wartości. |
| 53 | `<=` → `<` | 4 / 11 | **dziura → test** | Tolerancja `SAME_PLACE_M` na końcu osi jest włącznie: oś krótsza o centymetr od okrągłego hektometru wciąż go dostaje, bo `chainage_m` jest zapisany z dokładnością do centymetra. |
| 61 | `<=` → `<` | 1 / 11 | **równoważny** | Patrz dowód niżej. |
| 61 | `0.0` → `0.001` | 1 / 11 | **dziura → test** | Zerem jest POSTÓJ, a nie „prawie postój". Podmieniony próg po cichu kasowałby punkt hamowania dla prędkości pełzania. |
| 63 | `>=` → `>` | 2 / 11 | **remis → test wyboru gałęzi** | Przy opóźnieniu równym sufitowi plateau ma zerową długość i obie gałęzie są zgodne co do **4·10⁻¹⁶ m** (poniżej centymetra, do którego kilometraże są zaokrąglane). Test nie broni liczby, tylko konwencji „sufit należy do rampy". |
| 80 | `<=` → `<` | 1 / 3 | **dziura → test** | Punkt hamowania dokładnie centymetr za poprzednią stacją liczy się jako „na stacji" i jest pomijany z powodem. |
| 121 | `<=` → `<` | 2 / 5 | **dziura → test** | Scalanie znaczników: dokładnie `SAME_PLACE_M` to jeszcze jedno miejsce. To jest ten przypadek, w którym trzeba było zejść do zera — patrz sekcja 3. |

Osobno: mutacja `49 <= → <` (nie w tabeli, na `main` liczona jako zabita) **zawiesza
proces**, zamiast wywrócić test. Istniejący `test_layout_hectometre_step_must_be_positive`
podaje krok zerowy, a mutant nie odrzuca go i wchodzi w nieskończoną pętlę
`while index * 0.0 <= length`, dopisując znaczniki do listy bez końca. Zmierzone
dwukrotnie: wywołanie wprost ubite po 20 s (kod 124), a w przeglądzie mutacyjnym wynik
**nierozstrzygnięty** — `<zabity sygnałem, kod -9>`, czyli SIGKILL od zjedzonej pamięci.
W CI to jest czerwony przebieg, więc mutacja jest wykrywana — ale przez śmierć procesu,
nie przez asercję. Patrz sekcja 6.

### `tools/track/network_chainage.py` — 6 ocalałych

| wiersz | mutacja | traf. | werdykt | uzasadnienie |
|---|---|---|---|---|
| 131 | `>` → `>=` | 1 | **dziura → test** | Limit dziury między pakietami brzmi „dalej niż 2 km". Dziura równa dokładnie 2 km jest tą, o której raport ma powiedzieć. |
| 131 | `2000.0` → `2020.0` | 1 | **dziura → test** | Istniejący test odrzucania podaje 50 km, więc przechodzi z każdym progiem między 100 m a 50 km. Test dokłada parę 2010 m, która rozdziela 2000 od 2020. |
| 159 | `<=` → `<` | 1 | **dziura → test** | `PARALLEL_M` jest granicą włącznie: 30,0 m to jeszcze wspólny korytarz (korytarz osi A). |
| 160 | `<` → `<=` | 1 | **dziura → test** | `DEFAULT_CONFLICT_M` jest granicą wyłącznie: 9,40 m to szerokość rury, więc rury się **stykają**, a nie przenikają (zakresy kolizji). |
| 163 | `<` → `<=` | 1 | **dziura → test** | To samo dla listy punktów kolizji i licznika `conflict_points`. |
| 168 | `<=` → `<` | 1 | **dziura → test** | Korytarz liczony od strony osi B — drugie miejsce z tym samym progiem, nietestowane osobno. |

Granice są tu dokładne bez sztuczek: rzut prostopadły punktu (x, 30) na oś y = 0 to
`hypot(0, 30)`, a cięciwa między (100, 0) i (2100, 0) to `hypot(2000, 0)`.

### `tools/blender/m7_layout.py` — 6 ocalałych

| wiersz | mutacja | traf. | werdykt | uzasadnienie |
|---|---|---|---|---|
| 145 | `<` → `<=` | 1 | **dziura → test** | Otwór drzwi równy krokowi to układ styk w styk — dopuszczony. Zacommitowany M7 ma krok 2,13 m przy otworze 1,60 m, więc pół metra luzu i granicy nie widać. |
| 192 | `>=` → `>` | 1 / 13 | **równoważny** | Patrz dowód niżej. |
| 226 | `<` → `<=` | 1 | **dziura → test** | Tolerancja 1e−9 m w kontroli skrajni jest włącznie — szerokość, lewa strona. |
| 226 | `>` → `>=` | 1 | **dziura → test** | j.w., prawa strona. |
| 228 | `<` → `<=` | 1 | **dziura → test** | j.w., spód pudła. |
| 228 | `>` → `>=` | 1 | **dziura → test** | j.w., dach. |

Granica dla 226/228 jest skonstruowana przez nadpisanie **jednego** wymiaru egzemplarza
`Layout` wartością policzoną tym samym wyrażeniem, którego użyje warunek
(`min(gy) - 1e-9` itd.). Negacja i dzielenie przez dwa są w IEEE 754 dokładne, więc
`-(max(gy) + 1e-9)` to co do bitu `min(gy) - 1e-9`. Prawdziwy M7 ma do skrajni zapas
0 m dokładnie — nigdy nanometr — i dlatego wszystkie cztery przechodziły.

### `tools/track/station_layout.py` — 5 ocalałych

| wiersz | mutacja | traf. | werdykt | uzasadnienie |
|---|---|---|---|---|
| 77 | `<=` → `<` (lewa) | 1 | **dziura → test** | Łuk leżący dokładnie na krawędzi peronu należy do peronu. Kilometraże próbek są ułamkami z zagęszczania osi, więc żaden test nie podał ich jako granic przedziału. |
| 77 | `<=` → `<` (prawa) | 1 | **dziura → test** | j.w., koniec peronu. |
| 116 | `<` → `<=` | 0 | **nieosiągalny** | Patrz dowód niżej. |
| 117 | `>` → `>=` | 1 | **dziura → test** | Peron kończący się dokładnie na tolerancji nie jest raportowany jako przycięty. |
| 128 | `<=` → `<` | 1 | **dziura → test** | `within_footprint` też ma tolerancję włącznie: nanometr ponad obrys jeszcze się mieści. |

### `tools/data/provenance.py` — 4 ocalałe

| wiersz | mutacja | traf. | werdykt | uzasadnienie |
|---|---|---|---|---|
| 75 | `==` → `!=` | — | **dziura → test** | Żaden test nie podawał **zepsutego** JSON-a. Przy odwróconym warunku gałąź się nie odpala i uszkodzony ładunek przechodzi jako dobry, a CSV bywa parsowany jako JSON. |
| 91 | `<` → `<=` | 1 | **dziura → test** | Osiem bajtów to najmniejszy ładunek PBF, który jeszcze może być prawdziwy (czterobajtowa długość + początek bloku). Długość jest całkowita, więc granica jest dokładna bez sztuczek. |
| 91 | `8` → `9` | 1 | **dziura → test** | To samo wejście rozdziela oba progi. |
| 164 | `!=` → `==` | — | **dziura → test** | `content_sha256` miał test, `final_url` nie. To po tym polu poznaje się przekierowanie źródła pod inny adres. |

### `tools/track/data_freshness.py` — 4 ocalałe

| wiersz | mutacja | traf. | werdykt | uzasadnienie |
|---|---|---|---|---|
| 109 | `<` → `<=` | 1 | **dziura → test** | Dzień wygaśnięcia jest jeszcze ważny — okno kończy się z jego końcem. |
| 109 | `0` → `1` | 1 | **dziura → test** | To samo wejście (zero dni) rozdziela oba progi. |
| 110 | `<=` → `<` | 1 | **dziura → test** | `WARN_DAYS` jest granicą włącznie: dokładnie 30 dni to jeszcze „kończy się". |
| 112 | `>` → `>=` | 1 | **dziura → test** | Pobranie W DNIU wygaśnięcia to jeszcze nie pobranie PO wygaśnięciu. To jest dokładnie ostrzeżenie z `sources.json`, więc ma być rozstrzygnięte, a nie prawie rozstrzygnięte. |

---

## 5. Cztery, które zostały — z dowodami

Mutant równoważny wpisany jako usterka zawyża znalezisko dokładnie tak samo, jak
liczenie zepsutego przebiegu jako zabicia zawyżało pokrycie. Poniżej dowody, a nie
przypuszczenia.

### `profiles.py:33` — `len(out) > 2` → `len(out) >= 2`

Warunki różnią się **wyłącznie** przy `len(out) == 2`. Ale przy dwóch punktach
`out[1]` trafił tam dlatego, że `math.dist(out[1], out[0]) > eps` (wiersz 32) —
a to jest ta sama odległość, którą wiersz 33 porównuje z `eps` w drugą stronę
(`math.dist(out[0], out[-1]) <= eps`). Drugi człon koniunkcji jest więc przy
`len(out) == 2` **zawsze fałszywy** i pierwszy nie ma na co wpłynąć.

Pomiar: 4 trafienia w granicę na 18 wykonań, **0 różnic** na 12 wejściach baterii.

### `detail_layout.py:61` — `speed_mps <= 0.0` → `speed_mps < 0.0`

Różnica występuje wyłącznie przy `speed_mps == 0.0`, a wtedy gałąź zapasowa
(`ramp_only_distance_m(0.0, 0.0, jerk)`) też zwraca `0.0`. Obie ścieżki dają tę
samą liczbę.

Pomiar: 1 trafienie w granicę, **0 różnic** na 11 wejściach (w tym prędkości
0,0005, 0,001, 0,5, 2, 20 m/s i ujemna).

### `m7_layout.py:192` — `distance >= NOSE_LENGTH` → `distance > NOSE_LENGTH`

Przy `distance == DESIGN_NOSE_LENGTH_M` gałąź zapasowa liczy
`ratio = 1.0 - distance / DESIGN_NOSE_LENGTH_M = 1.0 - 1.0 = 0.0`, więc zwraca
`(INSET * 0.0, DROP * 0.0)` = `(0.0, 0.0)` — dokładnie to, co gałąź wczesnego wyjścia.

Pomiar: 1 trafienie w granicę na 612 wykonań, **0 różnic** na 13 wejściach
(w tym `x = NOSE`, `x = length - NOSE` i 401 przekrojów wzdłuż całej długości).

### `station_layout.py:116` — `raw_from < -1e-9` → `raw_from <= -1e-9`

Tu nie chodzi o równoważność, tylko o **nieosiągalność granicy**.
`raw_from = centre - platform_length_m / 2.0`. Żeby wynik był ujemny i bliski zeru,
`centre` musi leżeć blisko połowy peronu — a wtedy odejmowanie jest dokładne
(twierdzenie Sterbenza) i wynik jest **całkowitą wielokrotnością ostatniego bitu**
liczb rzędu połowy peronu. Peron nie może być krótszy od składu M7 (94 m, sprawdzane
wierszem 92), więc połowa peronu wynosi co najmniej 47 m, gdzie ostatni bit to 2⁻⁴⁷.

```
1e-9 / 2**-47 = 140737.488355328     # nie jest liczbą całkowitą
1e-9 / 2**-46 =  70368.744177664     # dla dłuższych peronów — też nie
```

Sprawdzone też wykonaniem: dla trzech kolejnych liczb zmiennoprzecinkowych wokół
`47.0 - 1e-9` różnica wynosi −1,0000036·10⁻⁹, −9,999965·10⁻¹⁰ i −9,999894·10⁻¹⁰.
**Żadna nie jest równa −1e−9.** Granicy nie da się trafić żadnym dopuszczalnym
wejściem, więc nie da się napisać testu, który by tę mutację zabił.

---

## 6. Czego świadomie nie zrobiono

**Nie zmieniono ani jednej linii kodu produkcyjnego.** Wszystkie 39 zabitych mutacji
padły od nowych testów, nie od poprawek. Trzy rzeczy zauważone przy okazji, nietknięte:

1. **`hectometre_marks` nie ma niezależnego ogranicznika pętli.** Gdy warunek wejściowy
   przepuści krok zerowy, `while index * step_m <= length_m + SAME_PLACE_M` kręci się
   w nieskończoność. Dziś nie przepuszcza, więc to nie jest usterka — ale odróżnia
   „test wykrył" od „proces zawisł", a te dwie rzeczy w CI wyglądają inaczej.
   Naprawa (np. ograniczenie liczby znaczników) to zmiana kodu produkcyjnego, więc
   nie należy do tego zadania.
2. **`endpoint_gaps(axes, conflict_m)` nie używa `conflict_m`.** Parametr jest
   przekazywany przez wszystkie wywołania i przez testy, i nie wpływa na nic.
3. **`station_layout.layout` zapisuje `round(radius, 2) if radius else None`.**
   Sprawdzanie prawdziwości zamiast `is not None` zamieniłoby promień 0 na `None`.
   Promień zero nie występuje w danych i wystąpić nie może, więc to jest pułapka
   na przyszłość, a nie błąd dzisiaj.

Nie dopisywano też testów do mutacji, które przemiatanie już zabija — ani nie dublowano
`test_tuning_constants.py` i `test_dimension_audit.py`, które pilnują innej warstwy tych
samych modułów (domyślnych wartości CLI i zgodności kodu z dokumentem audytu).
