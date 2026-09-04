# Triaż ocalałych mutacji — fizyka i rozkład

**Data pomiaru:** 2026-09-03

Cztery moduły: `tools/physics/braking.py`, `tools/physics/reference.py`,
`tools/physics/schedule_envelope.py`, `tools/track/timetable.py`.
Punkt wyjścia: przegląd mutacyjny na `main`, commit `737d592`.

Narzędzie: `tools/tests/mutation_sweep.py` z gałęzi `mutacje-raport-przeliczony`
(nie jest na `main` i nie jest w tym commicie — wchodzi jednym poleceniem
`git show mutacje-raport-przeliczony:tools/tests/mutation_sweep.py`).

---

## 0. Wynik, w jednym zdaniu

Z 29 ocalałych mutacji **16 to realne dziury** — dopisane testy je zabijają —
a **13 to mutanty równoważne albo nieosiągalne**, i te zostały opisane, a nie
„naprawione". Kodu produkcyjnego nie tknięto.

| moduł | ocalałych przed | ocalałych po | mutacji |
|---|---:|---:|---:|
| `tools/physics/schedule_envelope.py` | 9 | **5** | 10 |
| `tools/physics/braking.py` | 8 | **5** | 11 |
| `tools/physics/reference.py` | 5 | **3** | 8 |
| `tools/track/timetable.py` | 7 | **0** | 15 |
| **razem** | **29** | **13** | **44** |

---

## 1. Jak liczona jest kolumna „granica"

Zdanie „przepuściłem obie wersje przez baterię wejść i nie było różnic" **nic nie
znaczy**, jeśli bateria nie trafiła w punkt, w którym mutacja ma znaczenie. Losowe
wejścia z definicji nie trafiają w równość: `<` i `<=` różnią się wyłącznie przy
`a == b`, a dwie niezależnie wylosowane liczby zmiennoprzecinkowe równe nie są.

Dlatego klasyfikacja jest robiona **przez wykonanie**, w dwóch przebiegach:

1. **oryginał z sondą.** Mutowane porównanie jest w AST podmieniane na wywołanie,
   które zapisuje parę operandów i zwraca ten sam wynik. Bateria leci raz i daje
   trzy liczby: `wywołań` (ile razy porównanie się w ogóle wykonało),
   `granica` (ile razy operandy były **dokładnie równe**) i `przerzut` (ile razy
   operator oryginału i operator mutanta dały **różny wynik logiczny**).
2. **oryginał i mutant obok siebie** (`importlib` z dwóch źródeł, ten sam plik,
   dwie nazwy modułu). Ta sama bateria leci na obu i wyjścia są porównywane
   pozycja po pozycji, na pełnej precyzji (`repr`, nie tolerancja).

Odczyt:

| `przerzut` | `różnic` | znaczenie |
|---|---|---|
| 0 | 0 | **bateria nie dotknęła granicy** — wynik nie mówi nic; albo trzeba dobrać wejście, albo punkt jest nieosiągalny |
| > 0 | 0 | przesłanka **równoważności**: gałąź się przełącza i nie widać tego na wyjściu |
| > 0 | > 0 | zmiana jest obserwowalna — zostaje pytanie **jak duża** |

Bateria: przypadki brzegowe **konstruowane tak, żeby trafić w równość** (odległość
policzona jako `s_rozpędu + s_hamowania` dla zadanej prędkości, rozkład policzony
jako `fastest_time_s` dla zadanego sufitu, opóźnienie zadane jako
`adhesion_ceiling_mps2(...)` z tych samych argumentów, `math.nextafter` na jeden
bit obok) plus wejścia losowe z ustalonym ziarnem `20260903`. Bateria liczy od 339
do 1136 wielkości wyjściowych na moduł.

Ta droga do granicy jest jedyna sensowna dla liczb zmiennoprzecinkowych. Wariant
„stanę o epsilon od progu" nie działa: `abs((6700.0 + 0.01) - 6700.0)` daje
`0.010000000000218`, czyli **nad** progiem — różnica jest dokładna tylko wtedy, gdy
jedna strona jest zerem albo gdy próg jest potęgą dwójki. Wszystkie granice trafione
poniżej są albo **wyliczone tym samym wyrażeniem, co strona porównywana** (identyczne
operacje zmiennoprzecinkowe dają identyczny bit), albo są **równością liczb
całkowitych** (kroki pętli, sekundy GTFS), albo są **zerem**.

---

## 2. Realne dziury — 16 mutacji, wszystkie zabite

Kolumna „padło na" to **wykonana kontrola negatywna**: mutacja wstrzyknięta do kopii
drzewa, `tools/tests/test_all.py` uruchomiony, nazwa testu odczytana z jego wyjścia.

### `tools/physics/schedule_envelope.py`

| wiersz | mutacja | granica (wyw./równość/przerzut) | różnic | uzasadnienie | padło na |
|---|---|---|---|---|---|
| 55 | prog `0.0` → `0.001` | 29740 / 4 / 171 | 21/639 | Strażnik postoju przestaje być strażnikiem zera. Przy `v0 = 0,001 m/s` zwraca `(0, 0)` zamiast `3,44e-5 m` i `0,0516 s` — pociąg toczący się 3,6 mm/s dostaje drogę hamowania zerową. | `test_envelope_any_positive_speed_still_has_a_braking_distance` |
| 109 | `>` → `>=` | 188 / 4 / 4 | 4/639 | Odcinek, którego rozkład jest **równy co do bitu** czasowi granicznemu, wychodzi jako `None`: wpada do licznika `infeasible`, wypada z sortowania i nie może być odcinkiem wiążącym — a to on daje dolne ograniczenie prędkości sieci. Zmierzone: 200 m / 26,004 s daje `52,03 km/h` zamiast `None`. | `test_envelope_schedule_equal_to_the_floor_time_is_feasible_not_infeasible`, `test_envelope_minimum_speed_never_exceeds_a_speed_known_to_fit` |
| 114 | prog `0.0` → `0.001` | 6120 / 0 / 144 | 6/639 | Strażnik bisekcji przestaje pilnować dodatniości i zaczyna **ucinać wyszukiwanie**. Przy bardzo luźnym rozkładzie zwraca `0,0018310546875 km/h` zamiast `0,0005000000601 km/h` — wynik przestaje być najmniejszym sufitem mieszczącym się w rozkładzie, czyli przestaje być dolnym ograniczeniem. | `test_envelope_bisection_guard_does_not_truncate_a_very_loose_schedule` |
| 116 | `>` → `>=` | 6120 / 8 / 8 | 8/639 | **Najdroższa z całej czwórki.** Remis w bisekcji idzie na złą stronę. Na długim odcinku kosztuje to jeden krok bisekcji (`1,1e-10 km/h`), ale na krótkim czas przejazdu jest powyżej prędkości szczytowej trójkąta **płaski**, więc odrzucony remis wyrzuca całą tę półkę. Zmierzone: 200 m / 26,004 s wychodzi jako `90,00 km/h` zamiast `52,03 km/h` — **38 km/h** błędu w jedynym wyniku modułu. | `test_envelope_minimum_speed_never_exceeds_a_speed_known_to_fit` |

### `tools/physics/braking.py`

| wiersz | mutacja | granica | różnic | uzasadnienie | padło na |
|---|---|---|---|---|---|
| 200 | `<` → `<=` | 536971 / 24 / 24 | 24/1136 | Limit kroków całkowania wykonuje jeden krok za dużo. Widać to tylko wtedy, gdy pętla **kończy się na limicie**, a nie na zatrzymaniu — żaden dotychczasowy test takiego wejścia nie miał. Przy `limit_s = 120` to 14401 kroków zamiast 14400 i 0,185 m drogi doliczonej po końcu przebiegu. Granica jest tu równością `int`. | `test_braking_integration_stops_after_exactly_the_declared_number_of_steps` |
| 230 | `>=` → `>` | 24 / 2 / 2 | 2/1136 | `service_ok` przestaje znaczyć „sufit wystarcza" i zaczyna znaczyć „sufit przewyższa". Pole jest sprawdzane przez `test_braking_adhesion_table_verdicts_are_asserted_not_only_printed`, ale dla czterech wierszy z rejestru sufit **nigdy** nie jest równy zadaniu, a poza równością `>` i `>=` są nierozróżnialne. Bramka bez wejścia na granicy nie bramkuje granicy. | `test_braking_adhesion_verdict_is_inclusive_at_the_exact_ceiling` |
| 231 | `>=` → `>` | 24 / 2 / 2 | 2/1136 | To samo dla `emergency_ok`. To te dwa pola niosą główną konkluzję T-311. | `test_braking_adhesion_verdict_is_inclusive_at_the_exact_ceiling` |

### `tools/physics/reference.py`

| wiersz | mutacja | granica | różnic | uzasadnienie | padło na |
|---|---|---|---|---|---|
| 45 | prog `300` → `301` | 351604 / 0 / 8 | 8/339 | Limit czasu rozruchu. Każdy test zadaje 80 km/h, które model osiąga po ~25 s, więc limit nie bramkuje niczego. Przy 500 km/h opór Davisa zjada całą trakcję i przebieg kończy się **wyłącznie** na limicie: `t = 301,008 s`, `s = 13047,5 m` zamiast `300,008 s` i `12992,8 m`. | `test_reference_acceleration_run_stops_at_its_declared_time_limit` |
| 52 | prog `120` → `121` | 139470 / 0 / 8 | 8/339 | To samo po stronie hamowania. Zerowe opóźnienie nie zatrzymuje pociągu nigdy: `t = 121 s`, `s = 2688,9 m` zamiast `120 s` i `2666,7 m`. | `test_reference_braking_run_stops_at_its_declared_time_limit` |

### `tools/track/timetable.py`

| wiersz | mutacja | granica | różnic | uzasadnienie | padło na |
|---|---|---|---|---|---|
| 106 | `<=` → `<` (lewa) | 22 / 2 / 2 | 3/341 | `start_date` w GTFS jest **włączny**. Wzorzec ma okno 20260101–20261231 i pyta o 20260902, więc żadnego krańca nie dotyka. Wyłączny kraniec skasowałby pierwszy dzień każdej z 338 służb STIB. Granica jest porównaniem napisów `RRRRMMDD`, czyli ścisła. | `test_timetable_calendar_window_includes_both_of_its_end_dates` |
| 106 | `<=` → `<` (prawa) | 21 / 2 / 2 | 3/341 | To samo dla `end_date`. | `test_timetable_calendar_window_includes_both_of_its_end_dates` |
| 219 | `<` → `<=` | 198 / 26 / 26 | 25/341 | Kurs zaczynający się dokładnie w chwili końca poprzedniego to nadal **jeden pojazd**. Reguła jest pilnowana w `peak_concurrency` (`test_timetable_touching_trips_do_not_count_as_two`), ale w `block_summary` nie pilnował jej nikt. Styk czasów jest w rozkładzie normalny, więc mutacja zamienia każdy taki obieg w zgłoszony błąd feedu. Granica: sekundy całkowite. | `test_timetable_block_whose_trips_only_touch_has_no_overlap` |
| 299 | `!=` → `==` | 16 / 8 / 16 | 1/341 | **Luka we wzorcu, nie w asercji.** `terminus_non_zero` jest sprawdzane przez `test_timetable_does_not_count_a_trip_end_as_a_zero_dwell`, ale wzorzec ma cztery krańce w układzie 2 z postojem : 2 bez, więc obie wersje warunku dają 2. Na wzorcu asymetrycznym (3 : 1) oryginał daje 3, mutant 1. | `test_timetable_terminus_counter_counts_non_zero_dwells_not_zero_ones` |
| 300 | `!=` → `==` | 26 / 9 / 26 | 4/341 | `stop_times_with_dwell` nie było sprawdzane przez nic. Liczba idzie do noty raportu jako uzasadnienie zdania „postój da się z feedu wyczytać"; odwrócona liczy zatrzymania **bez** postoju (2 zamiast 4) i to samo zdanie znaczy odwrotność. | `test_timetable_counts_stop_times_that_have_a_dwell_not_those_without` |
| 327 | `>` → `>=` | 10 / 1 / 1 | 2/341 | Postój zerowy zaczyna się liczyć jako niezerowy. Wzorzec ma na przystankach pośrednich same postoje 20-sekundowe, więc granicy nie dotykał. | `test_timetable_zero_second_dwell_is_not_non_zero_and_one_second_is` |
| 327 | prog `0` → `1` | 10 / 1 / 1 | 2/341 | Postój jednosekundowy przestaje się liczyć. Wzorzec z postojami 0 s, 1 s i 20 s dotyka obu granic naraz. Granica: różnica sekund całkowitych. | `test_timetable_zero_second_dwell_is_not_non_zero_and_one_second_is` |

---

## 3. Mutanty równoważne i nieosiągalne — 13 mutacji, bez testu

Wpisanie mutanta równoważnego jako usterki zawyża znalezisko dokładnie tak samo,
jak liczenie zepsutego przebiegu jako zabicia zawyżało pokrycie. Poniżej jest
napisane, **dlaczego** każda z tych trzynastu została tak zakwalifikowana, i jaka
liczba za tym stoi.

### 3a. Bateria trafia w granicę, wyjście się nie zmienia

| plik:wiersz | mutacja | granica | uzasadnienie |
|---|---|---|---|
| `braking.py:163` | `<=` → `<` | 7680 / 76 / **76** | Strażnik zbieżności bisekcji `mid <= low`. Przerzut następuje 76 razy i **ani razu** nie zmienia wyjścia: po osiągnięciu równości `mid == low` dalsze obroty pętli przypisują tę samą wartość, a pętla i tak jest ograniczona z góry przez `steps`. Różnic: 0/1136. |
| `braking.py:163` | `>=` → `>` | 7604 / 60 / **60** | To samo dla `mid >= high`. Różnic: 0/1136. |
| `schedule_envelope.py:55` | `<=` → `<` | 29740 / 4 / **4** | Przy `v0 == 0` obie gałęzie dają `(0.0, 0.0)`: mutant wpada do warunku plateau, gdzie sufit wynosi `sqrt(0) = 0`, a droga z samego zrywu przy zerowej prędkości też jest zerem. Różnic: 0/639. Dla `v0 < 0` mutant rzuca `math domain error`, ale ujemna prędkość nie jest w dziedzinie tego modułu i nie powstaje w żadnym wywołaniu. |

### 3b. Różnica jest obserwowalna, ale ma rozmiar szumu zaokrągleń

| plik:wiersz | mutacja | zmierzona różnica | uzasadnienie |
|---|---|---|---|
| `braking.py:165` | `>` → `>=` | maks. **1,5e-14 m/s² = 17 ulp** na 3000 losowaniach | Remis w bisekcji solvera punktu hamowania. Zmierzone dla dróg z tablicy referencyjnej: 1–2 ulp (`s=240 m`: `1,1035188875716144` kontra `...46`). Kontrola przez wzór odwrotny trzyma się dla obu wersji **daleko poniżej** tolerancji `1e-9`, którą moduł sam sobie stawia w `test_solver_is_the_inverse_of_the_distance_formula`. Przypinanie tego bit w bit byłoby przypinaniem zaokrągleń biblioteki matematycznej, a nie fizyki: oryginał odtwarza zadaną drogę co do bitu tylko w **1809 z 2000** losowań, więc nawet on nie ma tej własności zawsze. |
| `reference.py:34` | `<=` → `<` | **1 ulp**, `2,9e-11 N` na `248900 N` | Punkt przejścia `F0 → P/v`. Przy `v == base_speed_ms()` oryginał zwraca `248900.0`, mutant `248899.99999999997`, bo `P/(P/F0)` nie jest dokładnie `F0`. Analitycznie obie gałęzie są w tym punkcie tożsame; różnica jest wyłącznie zaokrągleniem dzielenia. Prędkość przejścia `31,2415 km/h` z `docs/02-simulation.md` jest pilnowana osobno przez `test_m7_transition_speed_is_derived_from_power_and_force` i `test_m7_registry_matches_reference_transition`. |
| `schedule_envelope.py:57` | `>=` → `>` | maks. **2,8e-14 m** na drodze 114,04 m; czas identyczny co do bitu | Wybór między wzorem zamkniętym a wzorem „sam zryw" **dokładnie na suficie plateau**. W tym punkcie oba wzory są tożsame analitycznie: dla `b = √(2jΔv)` i `v1 = 0` wzór zamknięty daje `b³/(3j²)` i wzór na sam zryw daje `b³/(3j²)` — ta sama tożsamość, którą pilnuje istniejący `test_distance_at_the_plateau_ceiling_equals_the_ramp_only_distance`. Różnica jest resztką kolejności działań. |
| `schedule_envelope.py:90` | `>` → `>=` | **1,1e-10 km/h** (jeden krok bisekcji, `120/2³⁹`) | Remis w `peak_speed_kmh`. `s_rozpędu + s_hamowania` rośnie z prędkością **ściśle**, więc remis kosztuje dokładnie jeden krok bisekcji i nic więcej — inaczej niż w `minimum_top_speed_kmh` (wiersz 116), gdzie funkcja celu ma płaską półkę i ten sam remis kosztuje 38 km/h. Ta różnica między dwoma pozornie identycznymi mutacjami jest głównym powodem, dla którego triaż wymaga wykonania, a nie czytania. |
| `schedule_envelope.py:100` | `<=` → `<` | **7e-12 do 2,8e-11 s** na czasach 14–88 s | Odcinek **dokładnie** równy sumie drogi rozpędu i hamowania: człon jazdy jednostajnej ma wtedy zerową długość, więc obie gałęzie liczą to samo zdarzenie fizyczne. Mutant idzie okrężną drogą przez `peak_speed_kmh`, która zbiega do tej samej prędkości z dokładnością jednego kroku bisekcji. Względnie `1e-12`. |

### 3c. Punkt przerzutu jest nieosiągalny — `przerzut = 0`

| plik:wiersz | mutacja | granica | uzasadnienie |
|---|---|---|---|
| `braking.py:287` | `>` → `>=` | 4 / 0 / **0** | Warunek dopisujący „NIEOSIAGALNE przy kazdym ukladzie osi" w wydruku `report()`. `f_min` przyjmuje dla rejestru cztery wartości: `0,4846`, `0,5727`, `0,9319`, `1,1013`. Żadna nie jest równa 1, więc `>` i `>=` dają ten sam wydruk. Osiągnięcie granicy wymagałoby zmiany `data/vehicle/m7-spec.json`, a `data/` jest tylko do odczytu (reguła 6). |
| `braking.py:287` | prog `1.0` → `1.01` | 4 / 0 / **0** | Ten sam warunek. Żadna z czterech wartości nie leży w przedziale `[1,0; 1,01)`, więc próg można w tym zakresie przesuwać bez śladu. Równoważność jest **warunkowa względem obecnych liczb w rejestrze** i przestałaby obowiązywać, gdyby któraś z nich się zmieniła — to jest powód, dla którego nie jest to „nic", tylko wpis w tej tabeli. |
| `reference.py:45` | `<` → `<=` | 351604 / 0 / **0** | Limit `t < 300`. Czas narasta o `1/120` s w pętli, więc `t` **nigdy nie jest dokładnie równe** `300.0` — zmierzone zatrzymanie wypada na `300,0083333332248`. Bez równości `<` i `<=` są nierozróżnialne. Odróżnia się od siostrzanej mutacji progu (`300 → 301`), która jest realną dziurą i została zabita. |
| `reference.py:52` | `<` → `<=` | 139470 / 0 / **0** | Limit `t < 120`, ten sam mechanizm: zmierzone `120,00000000004157`. |
| `schedule_envelope.py:114` | `<=` → `<` | 6120 / 0 / **0** | Strażnik `mid <= 0.0` w bisekcji. `mid = 0,5·(low + high)` startuje z `low = 0`, `high = sufit > 0` i jest dodatnie w każdym z 40 obrotów, więc warunek nie zachodzi **nigdy** — jest to gałąź martwa i obie wersje operatora są w niej martwe tak samo. Siostrzana mutacja progu (`0.0 → 0.001`) martwa nie jest, bo ożywia gałąź, i została zabita. |

---

## 4. Rzeczywiste wyjście weryfikacji

Zestaw testów po zmianie:

```
$ python3 tools/tests/test_all.py
  ...
  ok   test_visual_yaw_rotates_the_forward_direction_around_world_up

  705/705 przeszło
```

Przed zmianą było 692 testy; doszło 13.

Przegląd mutacyjny, ten sam zestaw czterech modułów, przed i po:

```
$ for f in tools/physics/schedule_envelope.py tools/physics/braking.py \
           tools/physics/reference.py tools/track/timetable.py; do
      python3 tools/tests/mutation_sweep.py --only $f --workers 4 --journal /tmp/after.jsonl
  done

plik                                         przed      po  mutacji
tools/physics/braking.py                         8       5       11
tools/physics/reference.py                       5       3        8
tools/physics/schedule_envelope.py               9       5       10
tools/track/timetable.py                         7       0       15
RAZEM                                           29      13       44
```

Kontrole negatywne, wykonane — każda mutacja wstrzyknięta osobno do kopii drzewa,
`test_all.py` uruchomiony, nazwa testu odczytana z jego wyjścia:

```
tools/physics/braking.py:200 operator `<` -> `<=`
    padlo 1: test_braking_integration_stops_after_exactly_the_declared_number_of_steps
tools/physics/braking.py:230 operator `>=` -> `>`
    padlo 1: test_braking_adhesion_verdict_is_inclusive_at_the_exact_ceiling
tools/physics/braking.py:231 operator `>=` -> `>`
    padlo 1: test_braking_adhesion_verdict_is_inclusive_at_the_exact_ceiling
tools/physics/reference.py:45 prog `300` -> `301`
    padlo 1: test_reference_acceleration_run_stops_at_its_declared_time_limit
tools/physics/reference.py:52 prog `120` -> `121`
    padlo 1: test_reference_braking_run_stops_at_its_declared_time_limit
tools/physics/schedule_envelope.py:55 prog `0.0` -> `0.001`
    padlo 1: test_envelope_any_positive_speed_still_has_a_braking_distance
tools/physics/schedule_envelope.py:109 operator `>` -> `>=`
    padlo 2: test_envelope_minimum_speed_never_exceeds_a_speed_known_to_fit,
             test_envelope_schedule_equal_to_the_floor_time_is_feasible_not_infeasible
tools/physics/schedule_envelope.py:114 prog `0.0` -> `0.001`
    padlo 1: test_envelope_bisection_guard_does_not_truncate_a_very_loose_schedule
tools/physics/schedule_envelope.py:116 operator `>` -> `>=`
    padlo 1: test_envelope_minimum_speed_never_exceeds_a_speed_known_to_fit
tools/track/timetable.py:106 operator `<=` -> `<`   (lewa granica okna)
    padlo 1: test_timetable_calendar_window_includes_both_of_its_end_dates
tools/track/timetable.py:106 operator `<=` -> `<`   (prawa granica okna)
    padlo 1: test_timetable_calendar_window_includes_both_of_its_end_dates
tools/track/timetable.py:219 operator `<` -> `<=`
    padlo 1: test_timetable_block_whose_trips_only_touch_has_no_overlap
tools/track/timetable.py:299 operator `!=` -> `==`
    padlo 1: test_timetable_terminus_counter_counts_non_zero_dwells_not_zero_ones
tools/track/timetable.py:300 operator `!=` -> `==`
    padlo 1: test_timetable_counts_stop_times_that_have_a_dwell_not_those_without
tools/track/timetable.py:327 prog `0` -> `1`
    padlo 1: test_timetable_zero_second_dwell_is_not_non_zero_and_one_second_is
tools/track/timetable.py:327 operator `>` -> `>=`
    padlo 1: test_timetable_zero_second_dwell_is_not_non_zero_and_one_second_is
```

Ocalałe po zmianie to **dokładnie** te trzynaście, które sekcja 3 opisuje jako
równoważne albo nieosiągalne. Żadna mutacja nie zmieniła klasyfikacji po dopisaniu
testów — to jest kontrola samej klasyfikacji.

---

## 5. Czego świadomie nie zrobiłem

**Kodu produkcyjnego nie tknąłem.** Żadna z 29 ocalałych mutacji nie ujawniła
usterki w module pod testem — ujawniły luki w bramkach, a to jest co innego. Cztery
z nich są lukami we **wzorcach testowych**, nie w asercjach (`timetable.py:106`,
`299`, `327` i `braking.py:230/231`): asercja stała i była poprawna, tylko żadne
wejście nie doprowadzało jej do granicy.

**Nie przypinałem różnic rzędu ulp.** Pięć mutacji z sekcji 3b **daje** obserwowalną
różnicę i dałoby się je zabić porównaniem bit w bit. Nie zrobiłem tego: taki test
pilnowałby kolejności działań i zaokrągleń `libm`, a nie modelu, i byłby pierwszą
rzeczą, która pęknie przy zmianie platformy. Rozmiary tych różnic są w tabeli, żeby
następna osoba nie musiała ich mierzyć od nowa.

**Nie zmieniałem `data/vehicle/m7-spec.json`** (reguła 6). Dwie mutacje z
`braking.py:287` są nieosiągalne właśnie dlatego, że wartości `f_min` z rejestru
omijają próg — do ich zabicia trzeba by rejestr podmienić. `report()` nie przyjmuje
konfiguracji jako argumentu (woła `params()` samo), więc nie da się tego obejść
podstawieniem słownika, tak jak zrobiłem to dla `adhesion_table`.

**Nie tknąłem `src/Sim/`**, żadnego workflow CI ani `docs/`.

---

## 6. Co zauważyłem przy okazji, a czego nie ruszałem

**`report()` w `braking.py` nie jest wykonywane przez żaden test.** Cztery wywołania
warunku z wiersza 287 w mojej baterii pochodzą z niej samej, nie z zestawu.
Funkcja drukuje trzy tablice referencyjne T-311 i mogłaby przestać się składać bez
skutku dla CI. To jest osobne zadanie, nie triaż.

**`minimum_top_speed_kmh` na krótkim odcinku goni szum.** Powyżej prędkości
szczytowej trójkąta `fastest_time_s` powinno być stałe, ale wychodzi płaskie
dopiero do ok. `1e-11 s`: `peak_speed_kmh` jest wołane z różnym sufitem, więc
z różną siatką bisekcji. Skutek: dla 200 m i rozkładu 26,004 s funkcja zwraca
`52,033 km/h`, podczas gdy sama prędkość szczytowa trójkąta wynosi `51,760 km/h` —
`0,27 km/h` rozjazdu wziętego wyłącznie z zaokrągleń. Wynik nadal jest poprawnym
dolnym ograniczeniem (jest **wyższy** od prawdziwego minimum, więc bezpieczny
w stronę, w którą moduł ma być zachowawczy), ale nie jest tym, co deklaruje
docstring. Dlatego test `test_envelope_minimum_speed_never_exceeds_a_speed_known_to
_fit` przypina implikację („sufit, który dowozi rozkład, ogranicza wynik od góry"),
a nie liczbę. **Nie rozstrzygam, czy to usterka do naprawy, czy dopuszczalna cena
bisekcji** — to decyzja projektowa, której nie ma w dokumentach.

**Rozbieżność `docs/02-simulation.md` kontra model przyspieszenia jest już
zapisana i nadal otwarta** — `reports/T-310-physics.md` §9.1 i
`reports/T-311-braking.md` §7.2 mówią wprost, że dokument deklaruje
„przyspieszenie maks. 1,10 m/s²", a model tego nie egzekwuje (przy `F0 = 248,9 kN`
i masie efektywnej AW0 183,6 t rozruch startuje z `1,342 m/s²`). Potwierdziłem to
przy okazji triażu i **nie rozstrzygam, która strona jest prawdą** — to decyzja
projektowa z `CLAUDE.md` §8, opisana już w obu tamtych raportach. Nie jest to
znalezisko tego zadania.

Poza tym punktem **nie znalazłem żadnej rozbieżności między kodem tych czterech
modułów a `docs/02-simulation.md`**: wzory drogi i czasu hamowania, sufit plateau,
współczynniki Davisa `1,5 / 0,006 / 0,00035` z mnożnikami `1,40` i `1,00`,
`F0 = 248,9 kN`, moc `2160 kW`, punkt przejścia `31,2415 km/h`, masy `170 t` i
`221,94 t`, opóźnienia `1,10` i `1,30 m/s²`, zryw `0,75 m/s³` i współczynnik mas
wirujących `1,08` zgadzają się z dokumentem i z `data/vehicle/m7-spec.json`.
