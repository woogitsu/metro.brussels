# Triaż ocalałych mutacji `tools/blender/sweep.py` — 36 wziętych po jednej

**Zmierzone 05.09.2026 na commicie:** `7a817df`

Pozycja 6.B6 mówi o **37 / 79** ocalałych, za `reports/mutation-sweep.md` ze snapshotu
`66b8301`. Pierwszy dzisiejszy pomiar dał **36**, i to nie jest rozbieżność narzędzia:
mutację z wiersza 54 (`unit`, próg `0.0` → `0.001`) zabił w międzyczasie któryś
z dopisanych testów. Raport z `66b8301` był prawdą w dniu pomiaru i zostaje nietknięty —
datowanego pomiaru się nie przelicza.

Ten raport bierze te 36 po jednej. Każda dostaje werdykt poparty wykonaniem: kopią modułu
z wstawioną mutacją, puszczoną obok oryginału na tym samym wejściu.

## 0. Wyrocznia, bez której ten pomiar byłby fikcją

Przegląd puszczony przed południem meldowałby 100 % zabić niezależnie od kodu — narzędzie
miało zepsutą wyrocznię (`reports/wyrocznia-mutacyjna-falszywe-zabicia.md`, scalenie #268).
Wszystkie liczby niżej pochodzą z przebiegów PO naprawie, z kalibracją:

```
[MUTACJE] kalibracja wyroczni: zestaw w drzewie BEZ mutacji
[MUTACJE] drzewo bazowe zielone, wyrocznia ma prawo mówić „zabita”
[MUTACJE] wykonywanych wierszy dotyczy 79 z 79 mutacji; pozostałe 0 siedzą w kodzie,
          którego zestaw nie uruchamia
[MUTACJE] rozstrzygniętych 79/79, zabitych 43, ocalałych 36 (w tym 0 nieuruchomionych)
```

## 1. Trzy klasy, nie jedna

| klasa | ile | co ją definiuje |
|---|---:|---|
| **zabijalna** | 22 | istnieje wejście, na którym mutant daje inny wynik — i jest ono w teście |
| **równoważna** | 4 | żadne wejście nie odróżnia mutanta od oryginału |
| **nierozstrzygnięta** | 10 | progi `1e-9` i `1e-18` na normach wektorów; nie znalazłem wejścia rozstrzygającego i nie twierdzę, że go nie ma |

Trzecia klasa jest osobna świadomie. „Nie znalazłem" i „nie istnieje" to dwa różne zdania
i raport, który je zlepia, kłamie w wygodną stronę.

## 2. Zabijalne — 22, każda z wejściem rozstrzygającym

Poniżej wyjście skryptu porównującego oryginał z **kopią modułu**, w której siedzi
mutacja. Nie modelowałem funkcji: podmieniany jest prawdziwy plik.

### 2a. Progi udające granice zera

| mutacja | oryginał | mutant |
|---|---|---|
| 92 `catmull_rom` `0.0` → `0.001` | `4001` punktów | `3` punkty |
| 126 `point_to_polyline` `0.0` → `0.001` | `1.0` | `1.000112` |
| 204 `chunk_boundaries` `0.0` → `0.001` | `[(0.0, 0.0005), (0.0005, 1000.0)]` | `[(0.0, 1000.0)]` |
| 690 `manifest_problems` `0.0` → `0.001` | `[]` | `['T_c00: zakres chainage nie rośnie']` |

Wspólny wzorzec: warunek `x <= 0.0` znaczy „niedodatni", a nie „mniejszy niż milimetr".
Najgroźniejsza jest 92 — krok 0,5 mm cicho zwracałby łamaną **bez wygładzenia**,
nieodróżnialną w manifeście od wygładzonej. W 126 pułapka jest gorsza, bo `seg` to
**kwadrat** długości: próg 0,001 wycina segmenty krótsze niż ~3,16 cm, czyli dokładnie te,
z których składa się łuk o małym promieniu.

### 2b. Ostrość porównania, która produkuje chunk o zerowej długości

| mutacja | oryginał | mutant |
|---|---|---|
| 204 lewy `<` → `<=` | `[(0.0, 1000.0)]` | `[(0.0, 0.0), (0.0, 1000.0)]` |
| 204 prawy `<` → `<=` | `[(0.0, 1000.0)]` | `[(0.0, 1000.0), (1000.0, 1000.0)]` |
| 224 `>` → `>=` | `[0.0]` | `[0.0, 1e-06]` |
| 250 `<` → `<=` | `[100.0]` | `[]` |
| 386 `<` → `<=` | `[]` | `[[0, 1, 2, 3]]` |
| 683 `>` → `>=` | `[]` | `['pierwszy chunk zaczyna się w 1e-06 m, nie w 0']` |

Dwie stacje symetryczne wobec zera dają cięcie dokładnie w zerze; stacja za końcem osi —
cięcie dokładnie na `total_m`. W obu przypadkach mutant dokłada chunk o **zerowej
długości**, czyli obiekt, którego nie da się wczytać ani zwolnić.

### 2c. Pojedyncze, każda z innym skutkiem

| mutacja | oryginał | mutant | skutek |
|---|---|---|---|
| 65 `dedupe` `>` → `>=` | `[(0.0, 0.0, 0.0)]` | dwa punkty | segment o zerowej długości w `rmf_frames` |
| 130 próg `0.0` → `0.001` | `0.0` | `0.05` | rzut z pierwszego promila odcinka klamrowany do zera |
| 130 próg `1.0` → `1.01` | `0.5` | `1.42e-14` | rzut przepuszczony do 1 % **za** koniec odcinka |
| 237 lewy `<` → `<=` | `110.0` | `90.0` | cięcie na krawędzi dzielonego odcinka |
| 237 prawy `<` → `<=` | `None` | `110.0` | to samo z drugiej strony |
| 380 `>` → `>=` | `0` | `1` | ściana **styczna** liczona jako wywrócona |
| 410 `>` → `>=` | `(0.0, 0.0)` | `(1999999999.9999998, …)` | szum UV wchodzi do pomiaru gęstości |
| 477 `<` → `<=` | `0` | `1` | remis rozstrzygany na ramkę późniejszą |
| 487 `>` → `>=` | `[10]` | `IndexError` | funkcja wywraca się na liście jednoelementowej |
| 487 prog `1` → `2` | `[0]` | `[0, 0]` | wynik przestaje być ściśle rosnący |
| 224 prog `1e-6` → `1.01e-6` | `[0.0, 1.005e-06]` | `[0.0]` | cięcie zlepione z sąsiednim |

### 2d. Osobno: mutacja 219, o której repozytorium twierdziło, że jest równoważna

Docstring `test_chunk_a_span_exactly_at_the_cap_is_not_split` niósł zdanie:

> **Mutacja 219 `<=` -> `<` jest równoważna i ten test tego nie zmienia.** Napisałem go
> w przekonaniu, że ją zabije; nie zabija — sprawdzone wykonaniem, mutant daje 730/730.

Rachunek był dobry do połowy. Przy równości `pieces = ceil(1)`, więc `range(1, 1)` jest
puste i pętla nic nie dokłada — to prawda. Przeoczony został **`break` tuż za tą pętlą**:

```python
for a, b in zip(edges, edges[1:]):
    if b - a <= max_chunk_m:
        continue                      # mutant tu NIE wychodzi
    pieces = int(math.ceil((b - a) / max_chunk_m))
    for k in range(1, pieces): ...    # puste, zgadza się
    out.sort()
    break                             # ale TU wychodzi z całej pętli
```

Mutant przelatuje przez pustą pętlę, trafia na `break`, wychodzi z przeglądu krawędzi,
a że `changed` zostało `False` — kończy się także `while`. **Wszystko za odcinkiem równym
limitowi zostaje niepodzielone.**

```
oryginał : [100.0, 183.33333333333331, 266.66666666666663]
mutant   : [100.0]
```

Oś 350 m przy limicie chunka 100 m: mutant zostawia ogon 250 m, dwa i pół raza ponad limit.
Stary test tego nie mógł zobaczyć, bo w obu jego przypadkach odcinek równy limitowi był
**jedyny** — za nim nie było czego pominąć. Docstring jest **przepisany**, nie dopisany
obok, i cytuje ten pomiar.

### 2e. Wiersz 130 — cztery literały i pomyłka, którą wykrył dopiero przebieg

Ten wiersz zasługuje na osobny akapit, bo pierwsza wersja testu na niego **nie zabiła
niczego**, choć wszystkie pomiary jednostkowe wychodziły na „ROZJAZD":

```
        t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
             ^12        ^23           ^33        ^44
```

Przypiąłem **wartości klamry** (kolumny 12 i 33). Narzędzie mutuje **progi** (23 i 44) —
mówią to przesunięcia w dzienniku, `…:130:4614` i `…:130:4635`, i mówią jednoznacznie,
bo `plik:wiersz` by tu nie wystarczyło: cztery mutacje w jednym wierszu. Test był
poprawny i bezużyteczny naraz — sprawdzał zachowanie, którego żadna z mierzonych
mutacji nie dotyka.

To jest praktyczny powód, dla którego kryterium pozycji żąda rozróżniania par po
`plik:wiersz:przesunięcie`, a `reports/mutation-sweep.md` ma na to osobną sekcję
„Pułapka odczytu". Koszt pomyłki: jeden pełny przebieg przeglądu, czyli około czterdziestu
minut.

## 3. Równoważne — 4, każda z powodem

| mutacja | powód |
|---|---|
| 130 ostrość `<` → `<=` | przy `t == 0.0` obie gałęzie dają `0.0`; zmierzone: `1.0` wobec `1.0` |
| 130 ostrość `>` → `>=` | przy `t == 1.0` obie gałęzie dają `1.0`; to samo |
| 589 `high_m < low_m` | przy równości zamiana `low_m, high_m = high_m, low_m` jest tożsamością |
| 703 `seam > 0` | wiersz stoi za strażnikiem `abs(seam) > seam_tolerance_m`, więc `seam == 0` nigdy tam nie dociera przy tolerancji nieujemnej (domyślna `1e-6`) |

Dla dwóch pierwszych to jest rachunek potwierdzony wykonaniem, dla 589 — pomiar na 25
parach `(low, high)`, w tym pięciu z równością, zero rozjazdów. Dla 703 — czytanie
strażnika; wystarcza, bo tolerancja ujemna nie ma sensu i nie występuje.

## 4. Nierozstrzygnięte — 10, i dlaczego nie udaję, że wiem

| mutacje | wspólny próg |
|---|---|
| 143 ×2 (`tangents`) | `norm(s) > 1e-9` na sumie dwóch wersorów |
| 161 ×2 (`rmf_frames`) | `norm(right) < 1e-9` |
| 174 ×2 (`rmf_frames`) | `c2 < 1e-18`, czyli `|v2| ≈ 1e-9` |
| 345 ×2 (`_needs_flip`) | `dot(normal, midpoint) > 0.0` |
| 380 prog `0.0` → `0.001` | iloczyn skalarny w paśmie (0; 0,001] |
| 410 prog `1e-9` → `1.01e-9` | rozpiętość UV w paśmie 1e-9…1,01e-9 |

Wszystkie sześć rodzin wymagają albo trafienia w próg co do bitu na wielkości liczonej
przez trzy kolejne operacje zmiennoprzecinkowe, albo skonstruowania geometrii, której
iloczyn skalarny wypada w paśmie o szerokości tysięcznej. Próbowałem i nie znalazłem —
i to jest cała treść tego wiersza. **Nie twierdzę, że są równoważne**: mutacja 219 wyżej
jest dowodem, ile kosztuje takie twierdzenie postawione o jeden krok za wcześnie.

Cztery z tych dziesięciu (143 ×2 i 345 ×2) siedzą w funkcjach, które do dziś **nie mają
ani jednego wywołania w żadnym teście** — `tangents` i `_needs_flip` są dotykane wyłącznie
pośrednio, przez `rmf_frames` i `build_chunk_from_rings`. Czy to jest przyczyna, czy tylko
zbieg okoliczności, tego nie rozstrzygam: pasmo progu jest tu tak wąskie, że test
bezpośredni też mógłby go nie trafić. Sam brak pokrycia jest odnotowany w §7.

## 5. Testy — dziewiętnaście, wszystkie z jawnym progiem

Dziesięć w `tools/tests/test_sweep.py`, dziewięć w `tools/tests/test_chunks.py`.

Każdy podaje próg **jawnie w argumencie**, nigdy przez wartość domyślną. To nie jest
ostrożność stylistyczna: blok 6.B6 wyklucza ruszanie ośmiu stałych generatora
z `docs/21-measured-vs-assumed.md` §4, a test w rodzaju `assert SW.DEFAULT_MIN_CHUNK_M
== 120.0` przypinałby liczbę zamiast granicy. Cztery mutowane wiersze biorą taką stałą
jako domyślny argument (219 → `DEFAULT_MAX_CHUNK_M`, 237 → `DEFAULT_STATION_HALO_M`,
250 → `DEFAULT_MIN_CHUNK_M`, 386 → `DEGENERATE_AREA_M2`) i w każdym z nich test podaje
próg z ręki.

## 6. Weryfikacja — rzeczywiste wyjście

```
$ python3 tools/tests/mutation_sweep.py --only sweep.py --workers 4 \
      --operators operator,prog --journal build/b6-po2.jsonl
[MUTACJE] kalibracja wyroczni: zestaw w drzewie BEZ mutacji
[MUTACJE] drzewo bazowe zielone, wyrocznia ma prawo mówić „zabita”
[MUTACJE] wykonywanych wierszy dotyczy 79 z 79 mutacji; pozostałe 0 siedzą w kodzie,
          którego zestaw nie uruchamia
[MUTACJE] rozstrzygniętych 79/79, zabitych 65, ocalałych 14 (w tym 0 nieuruchomionych),
          nierozstrzygniętych 0
  OCALAŁA  tools/blender/sweep.py:130 operator `<` -> `<=`
  OCALAŁA  tools/blender/sweep.py:130 operator `>` -> `>=`
  OCALAŁA  tools/blender/sweep.py:143 operator `>` -> `>=`
  OCALAŁA  tools/blender/sweep.py:143 prog `1e-9` -> `1.01e-09`
  OCALAŁA  tools/blender/sweep.py:161 operator `<` -> `<=`
  OCALAŁA  tools/blender/sweep.py:161 prog `1e-9` -> `1.01e-09`
  OCALAŁA  tools/blender/sweep.py:174 operator `<` -> `<=`
  OCALAŁA  tools/blender/sweep.py:174 prog `1e-18` -> `1.01e-18`
  OCALAŁA  tools/blender/sweep.py:345 operator `>` -> `>=`
  OCALAŁA  tools/blender/sweep.py:345 prog `0.0` -> `0.001`
  OCALAŁA  tools/blender/sweep.py:380 prog `0.0` -> `0.001`
  OCALAŁA  tools/blender/sweep.py:410 prog `1e-9` -> `1.01e-09`
  OCALAŁA  tools/blender/sweep.py:589 operator `<` -> `<=`
  OCALAŁA  tools/blender/sweep.py:703 operator `>` -> `>=`

$ python3 tools/tests/test_all.py
  1620/1620 przeszło
```

**36 → 14 ocalałych, udział modułu 45,6 % → 17,7 %.** Kryterium pozycji („poniżej 20 %,
czyli najwyżej 15 z 79") jest spełnione z zapasem jednej mutacji.

Ocalała czternastka to dokładnie cztery równoważne z §3 i dziesięć nierozstrzygniętych
z §4 — czyli żadna z 22 zabijalnych nie przeżyła, i żadna z pozostałych nie zginęła
przypadkiem.

## 7. Zauważone przy okazji, nie tknięte

- **Dziewięć funkcji `sweep.py` nie ma ani jednego wywołania w testach**: `scale`, `cross`,
  `polyline_length`, `tangents`, `ring_positions`, `_needs_flip`, `face_normal`,
  `face_area`, `_nearest_ring`. Cztery z nich niosą siedem z ocalałych. `_nearest_ring`
  dostaje test w tym commicie, reszta zostaje.
- **`reports/mutation-sweep.md` ma dziś jedną liczbę nieaktualną** (37 zamiast 36 dla tego
  modułu) i to jest normalne: jest datowanym snapshotem, nie stanem bieżącym. Rozjazd tej
  klasy jest przedmiotem pozycji 6.D5, która go już zmierzyła.
