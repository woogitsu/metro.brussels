# Triaż mutacji — `tools/track/inspire_rail.py`

**Gałąź:** `triaz-inspire-rail` · **stan wyjściowy:** commit `737d592` · **data:** 03.09.2026

Narzędzie: `tools/tests/mutation_sweep.py` z gałęzi `mutacje-raport-przeliczony`
(plik roboczy, **nie** jest częścią tego commita). Mutowany jest kod pod testem, nie testy.

## Liczby

| | przed | po |
|---|---|---|
| mutacji | 41 | 41 |
| rozstrzygniętych | 41 | 41 |
| zabitych | 11 | **39** |
| **ocalałych** | **30** | **2** |
| nierozstrzygniętych | 0 | 0 |
| pokrycie | 26,8 % | **95,1 %** |
| testów w `test_all.py` | 692 | 708 |

Obie ocalałe mutacje są **równoważne** i udowodniono to wykonaniem, nie czytaniem
(sekcja „Dowód równoważności"). Kod produkcyjny nie został zmieniony.

## Werdykty — wszystkie 30 mutacji ocalałych na wejściu

Kolumna „test" podaje test, który po zmianie zabija daną mutację (sprawdzone
przemiataniem, nie deklaracją).

| wiersz | mutacja | werdykt | uzasadnienie | test |
|---|---|---|---|---|
| 207 | `<` → `<=` | dziura | dzień równy `validTo` był jedyną nieprzetestowaną wartością; testy pytały o 2026-05-01 i 2026-09-01, mijając granicę z obu stron. Porównanie idzie na napisach ISO, więc granica jest dokładna | `..._validity_window_is_current_on_its_last_declared_day` |
| 244 | `==` → `!=` | dziura | gałąź „skok wewnątrz jednej stacji" (Schuman: 8071 → 8065 → 8061) nie była w ogóle wykonywana — dokument testowy nie miał dwóch węzłów pod jedną nazwą | `..._station_walk_allows_a_hop_inside_one_station` |
| 279 | `<=` → `<` | dziura | promień korytarza kontrolnego nie miał testu na wartości równej promieniowi. Próg wzięty **z samego pomiaru** (nie z literału dziesiętnego) daje dokładną granicę | `..._corridor_selection_keeps_a_link_exactly_on_its_radius` |
| 302 | `<=` → `<` | dziura | zerowy segment osi przestaje być pomijany → `ZeroDivisionError`. Żaden test nie podawał osi z powtórzonym wierzchołkiem | `..._projection_skips_only_a_truly_zero_length_segment` |
| 302 | `0.0` → `0.001` | dziura | próg zwyrodnienia podniesiony do 0,001 (3,2 cm długości) wycina z pomiaru krótkie, ale prawdziwe segmenty; oś dwucentymetrowa przestaje mieć jakikolwiek segment i `project_signed` zwraca `None` | jw. |
| 306 | `0.0` → `0.001` | dziura | obcięcie `t` zamienia się w ciche zaokrąglenie: punkt 5 cm za początkiem osi dostaje kilometraż 0,0 zamiast 0,05 | `..._projection_does_not_round_the_foot_to_the_segment_ends` |
| 306 | `1.0` → `1.01` | dziura | punkt metr za końcem osi dostaje kilometraż o metr większy od długości osi — pomiar poza osią udający pomiar na osi | jw. |
| 306 | `<` → `<=` | **równoważna** | wartość wyrażenia warunkowego dla `t == 0.0` jest ta sama obiema drogami; potwierdzone wykonaniem na 4570 wejściach, w tym 109 trafiających dokładnie w `t == 0.0` (33 z nich `-0.0`) | — |
| 306 | `>` → `>=` | **równoważna** | jw. dla `t == 1.0`, 25 trafień dokładnie w granicę | — |
| 309 | `<` → `<=` | dziura | w zewnętrznym klinie załamania osi oba sąsiednie segmenty dają ten sam spodek i **bit w bit** tę samą odległość; rozstrzygnięcie remisu decyduje o tym, która ramka RMF daje wektor „w prawo", czyli o znakowanym odsunięciu (10 m kontra 8,66 m) | `..._projection_keeps_the_first_of_two_equidistant_segments` |
| 334 | `<=` → `<` | dziura | flaga `beyond_axis` na progu 1e-3 od początku osi | `..._beyond_axis_flag_is_exact_on_both_thresholds` |
| 334 | `>=` → `>` | dziura | to samo od strony końca osi (`total - 1e-3`) | jw. |
| 334 | `1e-3` → `0.00101` | dziura | okno szerokości 5 µm; osiągalne tylko przy osi o długości będącej potęgą dwójki | jw. |
| 352 | `<` → `<=` | dziura | lewy koniec zakresu histogramu (−20 m) musi wpadać do zakresu | `..._histogram_range_is_left_closed_and_right_open` |
| 352 | `>=` → `>` | dziura | prawy koniec (+20 m) musi wypadać — inaczej zakres przestaje być półotwarty i próbka trafia do kosza spoza siatki | jw. |
| 375 | `<` → `<=` | dziura | kosz o udziale dokładnie `MODE_MIN_SHARE` decyduje o liczbie modów, a liczba modów jest w tym skrypcie testem filtra topologicznego. `3/200` to dokładnie ten sam bit co literał `0.015` — test sprawdza to wprost | `..._mode_share_threshold_is_inclusive` |
| 377 | `>` → `>=` (lewy sąsiad) | dziura | remis z sąsiednim koszem robi z jednego toru dwa mody; istniejący test używał 90 kontra 110, czyli mijał remis | `..._modes_reject_a_bin_tied_with_its_neighbour` |
| 377 | `>` → `>=` (prawy sąsiad) | dziura | jw., druga strona porównania | jw. |
| 402 | `<=` → `<` | dziura | próbka o odsunięciu równym `RUNNING_OFFSET_MAX_M` wypada z pomiaru i przesuwa medianę międzytorza | `..._running_filter_keeps_a_sample_exactly_at_its_limit` |
| 403 | `<` → `<=` | dziura | próbka dokładnie na osi wchodzi do lewej chmury i ciągnie jej medianę | `..._zero_offset_sample_belongs_to_neither_track` |
| 403 | `0.0` → `0.001` | dziura | próbki milimetrowe po dodatniej stronie trafiają **jednocześnie** do lewej i prawej chmury | jw. |
| 404 | `>` → `>=` | dziura | próbka na osi wchodzi do prawej chmury i zawyża `wrong_side_samples` | jw. |
| 404 | `0.0` → `0.001` | dziura | próbki z przedziału (0; 0,001] znikają z prawej chmury bez śladu w raporcie | jw. |
| 405 | `>=` → `>` | dziura | przy remisie liczności ten sam plik wejściowy dawał raz rozstaw 3,5 m, a raz 7 m | `..._side_choice_on_a_tie_takes_the_negative_side` |
| 432 | `==` → `!=` | dziura | `spacing_by_link` nie była wołana przez żaden test. Po mutacji tabela ma tyle samo wierszy, sensowne nazwy odcinków i wiarygodne liczby — tylko przypisane do niewłaściwych odcinków | `..._spacing_by_link_groups_rows_under_their_own_link` |
| 569 | `!=` → `==` (w przód) | dziura | `main` nie była wołana na snapshotcie GML; bramka niejednoznaczności przepuszczała odwrócenie warunku, a skrypt zwracał kod 0 i zdanie zamiast pomiaru | `..._main_measures_the_spacing_when_the_walk_is_unambiguous` |
| 569 | `!=` → `==` (wstecz) | dziura | jw., drugi człon warunku | jw. + `..._main_stops_on_an_ambiguous_walk_instead_of_measuring` |
| 569 | `1` → `2` (w przód) | dziura | jw., oczekiwana liczba ścieżek | jw. |
| 569 | `1` → `2` (wstecz) | dziura | jw. | jw. |
| 624 | `==` → `!=` | dziura | cała linia z rozstawem znikała z `stdout`, a plik wyjściowy pozostawał poprawny — awaria widoczna wyłącznie dla człowieka czytającego konsolę | `..._main_measures_the_spacing_when_the_walk_is_unambiguous` |

## Dowód równoważności dla dwóch mutacji ocalałych

Obie dotyczą tego samego wyrażenia w `project_signed` (wiersz 306):

```python
t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
```

Czytanie kodu tu **nie wystarcza** i nie było podstawą werdyktu. Oryginał i mutant
zostały załadowane obok siebie (`importlib.util.spec_from_file_location` na pliku
tymczasowym ze zmutowanym źródłem) i przepuszczone przez tę samą baterię: patologie
dobrane ręcznie (`0.0`, `-0.0`, `1e-323`, punkty dokładnie na wierzchołku, za końcem
osi, `inf`, `-inf`, `NaN`) na pięciu osiach (prosta, załamana, z zerowym segmentem,
dwucentymetrowa, spinka do włosów) plus 4000 wejść losowych z ziarnem `20260903`,
a także 200 losowych linków przepuszczonych przez `offsets_for`. Wyniki porównywane
przez `repr`, żeby `-0.0` nie schowało się za `0.0`:

```
bateria: 4570 wywołań project_signed + 200 linków offsets_for

tools/track/inspire_rail.py:306 operator `<` -> `<=`
  project_signed: 4570 wejść, różnic 0
  offsets_for   : 200 linków, wyniki identyczne: True

tools/track/inspire_rail.py:306 operator `>` -> `>=`
  project_signed: 4570 wejść, różnic 0
  offsets_for   : 200 linków, wyniki identyczne: True
```

„Zero różnic" znaczyłoby tyle co nic, gdyby bateria nigdy nie dotknęła mutowanej
granicy, więc policzono też trafienia:

```
policzonych t: 7323
t == 0.0 dokładnie: 109 (w tym -0.0: 33)
t == 1.0 dokładnie: 25
t == NaN: 192
```

Granica jest osiągana ponad sto razy i mimo to wynik jest identyczny: dla `t == 0.0`
obie drogi przez wyrażenie warunkowe dają `0.0`, dla `t == 1.0` — `1.0`. Werdykt:
**mutanty równoważne**, nie brak pokrycia. Nie dopisano dla nich testu, bo nie da się
napisać testu, który by je odróżnił.

## Usterka znaleziona przy okazji — NIE naprawiona w tym commicie

`project_signed` indeksuje `frames[index]` numerem segmentu **osi**, a `SW.rmf_frames`
zwraca ramki dla osi **po deduplikacji** (`sweep.dedupe`, `eps=1e-6`). Gdy oś ma
powtórzony wierzchołek, obie listy przestają być równoległe:

```
os 4 ramki 3
bez duplikatu: (50.0, 3.5, 3.5)
z duplikatem : (50.0, 3.0310889132455356, 3.5)
```

Odsunięcie jest liczone ramką sąsiedniego segmentu, więc znakowana wartość — ta sama,
którą raport zestawia z `track_offsets` — wychodzi cicho zła. Przy dwóch powtórzonych
wierzchołkach z rzędu jest gorzej i zależnie od danych:

```
IndexError: list index out of range   # inspire_rail.py:310, right = frames[index][2]
```

**Dziś nic to nie psuje:** `data/track/L1_A.json` ma 447 punktów, zero powtórzeń,
najkrótszy segment 7,76 m. Usterka jest utajona i uaktywni ją dopiero oś z powtórzonym
punktem — a `load_alignment` niczego nie deduplikuje.

Nie ruszam tego w tym commicie z trzech powodów: to nie mieści się w zakresie zadania
(triaż mutacji), naprawa jest decyzją projektową (deduplikować oś przy wczytaniu czy
indeksować ramki inaczej — dwie różne odpowiedzi dla `tunnel_sweep.py`), a reguła 10
z `CLAUDE.md` mówi wprost: jedno zadanie, jedna gałąź, jeden commit, bez poprawiania
przy okazji. Do osobnego zadania.
