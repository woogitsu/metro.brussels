# Triaż mutacji ocalałych na `tools/track/detail_layout.py` — 19 wziętych po jednej

**Zmierzone 07.09.2026 na commicie:** `008e34e884ca0b685260af1b6cf6f6765d68ba5a`

**Adnotacja z tego samego dnia:** gałąź została po pomiarze przestawiona na `27e8ca0`
(scalenia #351–#358). Zestaw narzędzi przebiegł na nowej podstawie ponownie i dał ten
sam werdykt oraz tę samą deltę dziewięciu testów: **1852 → 1861**, kod wyjścia 0,
`test_detail_layout.py` 42 testy w 2,148 s. Liczby przeglądu mutacyjnego z dnia pomiaru
nie są przeliczane. **Usterka narzędzia z §1 stoi od tego czasu w kolejce jako 6.B35**
(#358) — potwierdzona niezależnie przy 6.B20 i przeze mnie na treści `OWN_TESTS_STUB`.

Pozycja 6.B16. Pole „Skąd” tej pozycji cytuje `reports/mutation-drift.md`: „8 ocalałych
z 9 mutacji — najgorszy stosunek w tabeli”. **Ten cytat nie zgadza się z treścią pliku,
który cytuje.** Wiersz `tools/track/detail_layout.py` w `reports/mutation-drift.md`
(kolumny: moduł, raport triażu, ocalałe po triażu, ocalałe dziś, Δ, mutacji wtedy,
mutacji dziś) brzmi:

```
| `tools/track/detail_layout.py` | parametry | 1 | 1 | 0 | 8 | 9 | `74008bf` dołożył 1 mutację, zabitą |
```

To jest **1 ocalała z 9**, nie 8 z 9 — i nigdzie w tym pliku nie stoi fraza „najgorszy
stosunek w tabeli”; `grep -n "najgorszy" reports/mutation-drift.md` daje zero trafień.
Ten sam plik dalej (§ „Dwadzieścia trzy moduły, w których liczba się nie zmieniła”)
liczy `detail_layout.py` właśnie do tej dwudziestki trzech modułów **bez rozjazdu** —
czyli sam siebie nie opisuje jako „najgorszy stosunek”. Zgadza się z tym
`reports/mutation-sweep.md` (`| tools/track/detail_layout.py | 1 / 9 | 11 % |`,
§ „`tools/track/detail_layout.py` — 1”, jedyna ocalała to wiersz 97 `<=`→`<`) oraz
`reports/mutation-triage-parametry.md` (03.09.2026: 7/8 → **1** po triażu). Nie zgaduję,
skąd wzięła się liczba 8/9 w treści pozycji — być może pomylenie kolumn „mutacji wtedy”
(8) i „mutacji dziś” (9) z liczbą ocalałych. **To jest zgłoszenie, nie cicha poprawka**:
`docs/TASKS.md` zachowuje oryginalne brzmienie pozycji (przepisywanie treści, którą
pozycja opisuje, byłoby dorabianiem liczby do formularza), a rozjazd stoi tutaj.

Powyższe dotyczy **legacy zestawu operatorów** (`operator, prog`), na którym powstały
wszystkie trzy cytowane raporty. Ten triaż mierzy **innym, szerszym zestawem** —
zob. § 0 niżej — więc i tak nie da się z niego wprost odtworzyć liczby „1 / 9”:
mianowniki są różne z założenia, nie z pomyłki.

## 0. Zestaw operatorów, na którym mierzono — i dlaczego liczby stąd nie są liczbami
   z `mutation-drift.md`

Ten triaż bierze **pełny, dzisiejszy domyślny zestaw pięciu klas** narzędzia
`tools/tests/mutation_sweep.py`: `operator, prog, logika, argument, przypisanie`
(stała `KINDS`, brak flagi `--operators` w poleceniu z § „Weryfikacja” tej pozycji).
`reports/mutation-drift.md`, `reports/mutation-sweep.md` i
`reports/mutation-triage-parametry.md` mierzyły **legacy zestawem dwóch klas**
(`operator, prog`) — to jest udokumentowana, świadoma decyzja tamtych raportów
(`mutation-drift.md` § u góry pliku), nie przeoczenie. Efekt: `--only
tools/track/detail_layout.py` łapie **33 mutacje** pełnym zestawem wobec **9**
zestawem legacy. Liczby „19 ocalałych”, „4 równoważne”, „15 zabitych nowymi testami”
niżej dotyczą **wyłącznie** zestawu pełnego i **nie są** porównywalne z „1 / 9” czy
„7 / 8” z raportów cytowanych wyżej — to inny mianownik, nie inny wynik pomiaru tego
samego zjawiska.

## 1. Usterka narzędzia, którą trzeba było obejść, żeby cokolwiek zmierzyć

Zanim doszło do jakiejkolwiek mutacji, kalibracja wyroczni (krok, który
`tools/tests/mutation_sweep.py` wykonuje PRZED każdym pomiarem — `main()`,
§ „kalibracja wyroczni”) **padała na czystym drzewie, bez żadnej mutacji**:

```
[MUTACJE] kalibracja wyroczni: zestaw w drzewie BEZ mutacji
[MUTACJE] PRZERWANE — zestaw PADA w czystym drzewie, bez żadnej mutacji (kod 1):
['test_every_module_delegates_to_the_one_runner:', 'test_every_test_module_can_be_run_directly:']
— dopóki tak jest, każda mutacja zostanie zapisana jako zabita, a przegląd nie mierzy niczego
```

Przyczyna: `neutralise_own_tests()` w `mutation_sweep.py` (6.D18 i wcześniej) zdejmuje
testy narzędzia z kopii roboczej, podmieniając `tools/tests/test_mutation_sweep.py` na
zaślepkę **bez strażnika `__main__`**. Pozycja 6.D25 (`a2a0d21`, dziś już scalona do
`main` jako `f259d5d`) dodała `tools/tests/test_module_entrypoints.py`, która wymaga,
żeby **każdy** `tools/tests/test_*.py` miał strażnik delegujący do
`test_all.main(__file__)` — i zaślepka `OWN_TESTS_STUB` w `mutation_sweep.py` nigdy nie
dostała tego strażnika. Dwie poprawne osobno zmiany (6.D18 i 6.D25) nie zostały
przetestowane RAZEM, bo 6.D25 nie uruchomiła kosztownego (kilkunastominutowego)
przeglądu mutacyjnego, żeby to zauważyć — i sama o tym mówi: „Kryterium sprawdzone
pętlą po wszystkich 91” liczyła pliki **w bieżącym drzewie**, nie w drzewie, które
`mutation_sweep.py` sam sobie kopiuje i okalecza.

**Skutek: na dzisiejszym `main` przegląd mutacyjny jest złamany dla KAŻDEGO modułu,
nie tylko dla `detail_layout.py`.** To jest większe niż ta pozycja i nie jest tu
naprawiane — `tools/tests/mutation_sweep.py` jest poza zakresem 6.B16 (§ Poza zakresem
w opisie pozycji: żadna zmiana wyniku, jaki liczy `detail_layout.py`; zmiana **innego**
modułu na dodatek nie ma tu uzasadnienia w zadaniu). Żeby jednak cokolwiek zmierzyć,
dodałem **lokalnie, w pamięci robotej sesji, NIGDY niecommitowany** strażnik do
`OWN_TESTS_STUB` (trzy linie: `if __name__ == "__main__": ... test_all.main(__file__)`),
zmierzyłem obiema stronami (§ 2 i § 5), a przed commitem cofnąłem `git checkout --
tools/tests/mutation_sweep.py` — commit tej pozycji **nie dotyka tego pliku**,
sprawdzone `git diff --stat HEAD~1` (patrz § 6). **To jest osobne zgłoszenie**, nie
naprawa: `tools/tests/mutation_sweep.py` potrzebuje własnej pozycji w `docs/TASKS.md`,
żeby ktoś commitował ten strażnik naprawdę.

## 2. Przegląd PRZED — rzeczywiste wyjście

```
$ python3 tools/tests/mutation_sweep.py --only tools/track/detail_layout.py --workers 4 \
      --journal /tmp/detail_layout_baseline.jsonl
[MUTACJE] --only 'tools/track/detail_layout.py' złapało 33 mutacji z 1 moduł(ów): tools/track/detail_layout.py
[MUTACJE] 33 mutacji do policzenia, 4 robotników, commit f259d5d, klasy operator,prog,logika,argument,przypisanie, dziennik /tmp/detail_layout_baseline.jsonl
[MUTACJE] kalibracja wyroczni: zestaw w drzewie BEZ mutacji
[MUTACJE] drzewo bazowe zielone, wyrocznia ma prawo mówić „zabita”
[MUTACJE] sonda pokrycia: jeden przebieg zestawu z licznikiem wierszy
[MUTACJE] wykonywanych wierszy dotyczy 26 z 33 mutacji; pozostałe 7 siedzą w kodzie, którego zestaw nie uruchamia
[MUTACJE] rozstrzygniętych 32/33, zabitych 13, ocalałych 19 (w tym 7 nieuruchomionych), nierozstrzygniętych 1
  OCALAŁA  tools/track/detail_layout.py:28 argument `0` -> `1`
  OCALAŁA  tools/track/detail_layout.py:29 argument `0` -> `1`
  OCALAŁA  tools/track/detail_layout.py:97 operator `<=` -> `<`
  OCALAŁA  tools/track/detail_layout.py:99 argument `0.0` -> `0.001`
  OCALAŁA  tools/track/detail_layout.py:119 argument `2` -> `3`
  OCALAŁA  tools/track/detail_layout.py:120 argument `2` -> `3`
  OCALAŁA  tools/track/detail_layout.py:121 argument `2` -> `3`
  OCALAŁA  tools/track/detail_layout.py:126 argument `2` -> `3`
  OCALAŁA  tools/track/detail_layout.py:128 argument `2` -> `3`
  OCALAŁA  tools/track/detail_layout.py:142 argument `2` -> `3`
  OCALAŁA  tools/track/detail_layout.py:173 argument `3` -> `4`
  OCALAŁA  tools/track/detail_layout.py:179 argument `2` -> `3`
  NIEURUCH. tools/track/detail_layout.py:191 argument `True` -> `False`
  NIEURUCH. tools/track/detail_layout.py:192 argument `True` -> `False`
  NIEURUCH. tools/track/detail_layout.py:210 argument `True` -> `False`
  NIEURUCH. tools/track/detail_layout.py:210 logika `or` -> `and`
  NIEURUCH. tools/track/detail_layout.py:212 argument `False` -> `True`
  NIEURUCH. tools/track/detail_layout.py:212 argument `True` -> `False`
  NIEURUCH. tools/track/detail_layout.py:212 argument `1` -> `2`
```

**19 ocalałych na 33** (12 wykonanych i przeżytych, 7 nieuruchomionych) plus **1
nierozstrzygnięta** (wiersz 91, § 4). 32/33 rozstrzygniętych + 1 nierozstrzygnięta = 33.

## 3. Trzy klasy — 15 zabijalnych, 4 równoważne, 0 pozostawionych bez werdyktu

| werdykt | ile | wiersze |
|---|---:|---|
| **zabita nowym testem** | 15 | 119, 120, 121, 126, 128, 142, 173, 179 (precyzja zaokrągleń) + 191, 192, 210 ×2, 212 ×3 (CLI, `main()`) |
| **równoważna, z dowodem** | 4 | 28, 29 (kolejność `sys.path.insert`), 97 (`<=`→`<` przy `speed_mps==0.0`), 99 (przesunięcie progu `v1` o 0,001 na granicy gałęzi) |
| **nierozstrzygnięta** (osobna kategoria, nie „ocalała”) | 1 | 91 (`index += 1` → `index = 1`) — § 4 |

Każda z 19 ocalałych ma poniżej werdykt z dowodem.

### 3a. Zabijalne — 8 mutacji precyzji zaokrągleń

Cztery pola liczą `round(x, 2)` **niezależnie** — jedna wspólna mutacja precyzji by ich
nie złapała naraz, bo wejścia muszą mieć niezerową trzecią cyfrę po przecinku w KAŻDYM
z osobna, inaczej `round(x, 2)` i `round(x, 3)` dają tę samą liczbę.

| wiersz | pole | wejście | `round(x,2)` | `round(x,3)` (mutant) |
|---|---|---|---:|---:|
| 119 | `skipped[...]["previous_station_at_m"]` | `previous.chainage_m = 0.123456` | 0.12 | 0.123 |
| 120 | `skipped[...]["would_be_at_m"]` | (patrz test) | −380.0 | −380.005 |
| 121 | `skipped[...]["chainage_m"]` | `station.chainage_m = 50.987654` | 50.99 | 50.988 |
| 126 | `marks[...]["chainage_m"]` | `station.chainage_m = 1234.567891`, `v=20` | 1038.18 | 1038.182 |
| 128 | `marks[...]["braking_distance_m"]` | jw. | 196.39 | 196.386 |
| 142 | stacja w `layout()`, pole `chainage_m` | `123.456789` | 123.46 | 123.457 |
| 173 | `survey()["axis_length_m"]` (precyzja **3**, nie 2!) | `length_m = 1234.56789` | 1234.568 | 1234.5679 (mutant: `round(x,4)`) |
| 179 | `survey()["braking_distance_m"]` | `v=72 km/h` | 196.39 | 196.386 |

Testy: `test_layout_skipped_brake_point_rounds_every_field_to_two_decimals_independently`,
`test_layout_kept_brake_point_rounds_chainage_and_distance_to_two_decimals`,
`test_layout_station_entry_chainage_rounds_to_two_decimals`,
`test_layout_survey_axis_length_rounds_to_three_decimals_not_two`,
`test_layout_survey_braking_distance_rounds_to_two_decimals` — w
`tools/tests/test_detail_layout.py`.

### 3b. Zabijalne — 7 mutacji w `main()` (CLI), wszystkie NIEURUCHOMIONE do tej pozycji

Osiem testów istniejących przed tą pozycją wołają funkcje modułu wprost — żaden nie
przechodzi przez `main()`. Stąd „NIEURUCH.” w § 2: sonda pokrycia widziała te wiersze
jako martwe dla zestawu, nie dlatego, że są bezpieczne.

| wiersz:przesunięcie | co | dowód zabicia |
|---|---|---|
| 191:8846 | `required=True` dla `--axis` | `parse_args(["--out", "x"])` → `SystemExit` |
| 192:8894 | `required=True` dla `--out` | `parse_args(["--axis", "x"])` → `SystemExit` |
| 210:9805 | `exist_ok=True` w `os.makedirs` | dwa wywołania `main()` do TEGO SAMEGO katalogu; mutant: `FileExistsError` |
| 210:9822 | `os.path.dirname(out) or "."` | `--out` w katalogu, który jeszcze nie istnieje; mutant liczy `dirname(out) and "."` = `"."` (bo `dirname(out)` jest zawsze prawdziwe — `out` jest zawsze złożone z `ROOT`), więc tworzy `.` zamiast prawdziwego katalogu docelowego i zapis pada `FileNotFoundError` |
| 212:9928 | `ensure_ascii=False` | plik zawiera dosłowne `ł` (`note`, pole zawsze obecne); mutant ucieka je jako `\uXXXX` |
| 212:9942 | `indent=1` | wiersz najwyższego poziomu zaczyna się od DOKŁADNIE jednej spacji; mutant: dwóch |
| 212:9955 | `sort_keys=True` | klucze najwyższego poziomu w kolejności alfabetycznej; mutant: kolejności wstawienia (`checked_at` przed `axis_id`) |

Testy: `test_main_requires_both_axis_and_out_arguments`,
`test_main_creates_missing_output_directories_and_writes_sorted_indented_utf8`,
`test_main_output_directory_may_already_exist`.

**Uwaga o 210:9822** — dowód, że mutacja jest OBSERWOWALNA, nie kosmetyczna: `out`
w `main()` zawsze przechodzi przez `os.path.join(ROOT, args.out)`, gdy `args.out` nie
jest bezwzględna — więc `os.path.dirname(out)` w praktyce **nigdy nie jest pusty**
(nawet dla `args.out == ""`, `os.path.dirname` zwraca `ROOT`, nie `""`). To znaczy, że
oryginalne `dirname(out) or "."` **zawsze** oblicza się do `dirname(out)`, a mutant
`dirname(out) and "."` **zawsze** oblicza się do `"."` — dwie stałe, ale RÓŻNE stałe,
więc `makedirs` tworzy inny katalog niż zamierzony za każdym razem, gdy katalog
docelowy jeszcze nie istnieje. To NIE jest martwy kod: to gałąź, która pod mutacją
zawsze robi złą rzecz, tylko dotąd nikt jej nie zawołał.

## 4. Nierozstrzygnięta — wiersz 91, i dlaczego to NIE jest „ocalała”

`index += 1` → `index = 1` w `hectometre_marks()`. Narzędzie zgłosiło:

```
"opis": "tools/track/detail_layout.py:91 przypisanie `+=` -> `=`",
"rozstrzygniete": false, "padly": ["<przekroczony czas>"], "ile_padlo": 1
```

Powód jest ten sam kształt usterki co przy strażniku `step_m` (już opisanym w
docstringu `MAX_MARKS` i przez istniejący test
`test_layout_hectometre_grid_terminates_with_the_step_guard_removed`), inna
przyczyna: gdyby `index` przestał sam siebie zwiększać, warunek pętli
`index * step_m <= length_m + SAME_PLACE_M` zostaje prawdziwy **na zawsze** — `index`
nigdy nie dochodzi do `MAX_MARKS`, więc ogranicznik, który miał kończyć pętlę, sam
nigdy się nie uruchamia. To jest gorsze niż brak samego strażnika `step_m` (tam kończy
`MAX_MARKS`; tu nie kończy nic).

Narzędzie nie mogło tego rozstrzygnąć własnym limitem 300 s na proces roboczy (pętla
się nie kończy — proces trzeba zabić z zewnątrz). Dopisałem osobny test,
`test_layout_hectometre_index_must_actually_advance_or_the_grid_never_ends`, tą samą
drogą co istniejący test strażnika `step_m`: mutacja siedzi w kopii źródła uruchomionej
w osobnym procesie z KRÓTKIM (2 s) limitem czasu — bo zawieszenia nie da się
zaobserwować w tym samym procesie, a 2 s starczają z zapasem (bez inkrementacji pętla
wykonuje miliony obrotów na sekundę). Kontrola negatywna w drugą stronę — że test NIE
jest fałszywym alarmem, tylko naprawdę rozróżnia mutanta od oryginału — wykonana osobno:

```
$ python3 -c "... uruchom TEN SAM sterownik na NIEZMUTOWANEJ kopii źródła, limit 2 s ..."
BEZ MUTACJI: zakonczylo sie, kod= 0 stdout= DOKONCZONE
```

Bez mutacji podproces kończy się natychmiast i normalnie — timeout łapie wyłącznie
kod z wstrzykniętą mutacją. Ten wiersz **nie wchodzi** do liczby „19 ocalałych” w § 2,
bo w klasyfikacji narzędzia nigdy nie był „ocalałą” — był i zostaje
**nierozstrzygniętą przez narzędzie, rozstrzygniętą ręcznie jako zawieszenie**, trzeci
stan, o którym `docs/TASKS.md` (6.B14) już raz pisał: „trzeci stan istnieje właśnie po
to, żeby go nie zgadywać”.

## 5. Równoważne — 4, każda z dowodem WYKONANYM i zapisem, czego szukałem

### 5a. Wiersze 28, 29 — kolejność `sys.path.insert(0, ...)` → `insert(1, ...)`

```python
sys.path.insert(0, os.path.join(ROOT, "tools", "physics"))   # 28
sys.path.insert(0, os.path.join(ROOT, "tools", "data"))       # 29
```

Pozycja w `sys.path` ma znaczenie tylko wtedy, gdy istnieje **inny** moduł o tej samej
nazwie (`braking` albo `provenance`) bliżej początku listy — inaczej import trafia
w ten sam plik niezależnie od pozycji `0` czy `1`. Szukałem takiego kolidującego
modułu dwiema drogami i nie znalazłem żadnego:

```
$ find . -name "braking.py" -o -name "provenance.py" | grep -v "\.git"
./tools/physics/braking.py
./tools/data/provenance.py
```

Po jednym pliku w całym repozytorium. I z zewnątrz repozytorium, na czystym
`sys.path` interpretera (bez wpisów tego projektu):

```
$ cd /tmp && python3 -c "import provenance" → ModuleNotFoundError
$ cd /tmp && python3 -c "import braking"    → ModuleNotFoundError
```

Żadnego pakietu o tej nazwie w `site-packages`. Czego szukałem, żeby to obalić:
kolidującego modułu `braking` albo `provenance` gdziekolwiek na ścieżce, którą Python
przeszukuje przy tym imporcie — w repozytorium i poza nim. Nie znalazłem żadnego, więc
`insert(0, ...)` i `insert(1, ...)` rozwiązują się w ten sam plik przy KAŻDYM wejściu,
jakie ten interpreter może dostać. Gdyby taki kolidujący moduł kiedyś powstał, ta
mutacja przestałaby być równoważna — dowód jest więc o **dzisiejszym** drzewie, nie
o module w oderwaniu od niego, tak jak wymaga to forma tego triażu.

### 5b. Wiersz 97 — `speed_mps <= 0.0` → `speed_mps < 0.0`

Jedyny punkt, w którym `<=` i `<` dają różną wartość logiczną, to `speed_mps == 0.0`
dokładnie — dla każdego innego wejścia oba warunki się zgadzają. Sprawdzone wykonaniem
obu gałęzi na tym jedynym punkcie:

```
$ python3 -c "... D.braking_distance_m(0.0, CFG['service'], CFG['jerk']) ..."
orig braking_distance_m(0.0,...) = 0.0
mutant  braking_distance_m(0.0,...) = 0.0
mutant  braking_distance_m(-0.0,...) = 0.0
```

Powód matematyczny: przy `speed_mps == 0.0`, mutant NIE wraca wcześnie, tylko liczy
`B.plateau_ceiling_mps2(0.0, 0.0, jerk) == sqrt(2·jerk·0) == 0.0`, warunek
`decel_mps2 >= 0.0` jest prawdziwy (hamulec ma dodatnie opóźnienie), więc wywołuje
`B.ramp_only_distance_m(0.0, 0.0, jerk)`, gdzie `tf = sqrt(2·(0−0)/jerk) == 0.0`
i wynik `0·0 − jerk·0³/6 == 0.0` — **ta sama wartość**, którą zwraca oryginalny
wczesny powrót. Czego szukałem, żeby to obalić: innego wejścia niż `speed_mps == 0.0`,
na którym `<=` i `<` się różnią — takiego wejścia nie ma z definicji operatorów
porównania na liczbach rzeczywistych.

### 5c. Wiersz 99 — `B.plateau_ceiling_mps2(speed_mps, 0.0, jerk)` → `..., 0.001, ...`

To jedyna z czterech, która wymagała przeszukania, nie tylko rachunku — mutacja zmienia
próg, przy którym `braking_distance_m()` przełącza się między dwoma wzorami
(`ramp_only_distance_m` i pełnym `braking_distance_m` z T-311), więc TEORETYCZNIE mogła
przesunąć granicę na tyle, żeby dać inny wynik. Policzyłem okno, w którym mutant
i oryginał wybierają RÓŻNE gałęzie (przy `CFG["service"]=1.10`, `CFG["jerk"]=0.75`):
`speed_mps` w przybliżeniu `[0.806668, 0.816667]` m/s — mniej niż 3 km/h. Przeszukałem
to okno gęsto, co 1 µm:

```
$ python3 -c "... skan 0.806668..0.82 co 1e-6 ..."
max diff in window: (9.368306130852488e-11, 0.8076660000000001,
                      0.7902068835692257, 0.7902068834755427)
round4 orig 0.7902 round4 mut 0.7902
round2 orig 0.79 round2 mut 0.79
```

Maksymalna różnica w CAŁYM oknie przełączenia gałęzi to **9,4 × 10⁻¹¹ m** — jedenaście
rzędów wielkości poniżej precyzji, jaką moduł kiedykolwiek wypisuje (`round(x, 2)`,
czyli centymetr; nawet `round(x, 4)`, którego moduł nigdze nie używa, tej różnicy by
nie odróżnił). Przyczyna matematyczna: `plateau_ceiling_mps2` to granica, w której obie
formuły z definicji dają tę SAMĄ wartość (ciągłość na złączeniu) — błąd wyboru złej
gałęzi tuż przy granicy jest więc rzędu `(v0 − v0_granica)ⁿ`, czyli mikroskopijny
dokładnie tam, gdzie mutacja może w ogóle coś przełączyć. Czego szukałem, żeby to
obalić: punktu w oknie przełączenia gałęzi (jedynym miejscu, gdzie mutacja może w ogóle
coś zmienić), w którym `round(wynik, 2)` — jedyna precyzja, jaką moduł kiedykolwiek
wypisuje — różni się między oryginałem a mutantem. Przeszukane w kroku 1 µm w całym
oknie (~10 000 punktów), różnicy takiej nie ma. Nie twierdzę, że różnica jest zerowa
co do bitu (nie jest — 9,4 × 10⁻¹¹ to realna, mierzalna liczba) — twierdzę, że jest
**nieobserwowalna przez żadne wyjście, jakie ten moduł kiedykolwiek produkuje**, co
jest definicją równoważności użytą w § 1 `reports/mutation-triage-sweep.md`.

## 6. Testy — dziewięć nowych, zestaw **1836 → 1845**

```
$ python3 tools/tests/test_all.py
  1836/1836 przeszło        (PRZED, na f259d5d)
  ...
  1845/1845 przeszło        (PO, na 008e34e)
```

Dziewięć nowych testów w `tools/tests/test_detail_layout.py`:
`test_layout_hectometre_index_must_actually_advance_or_the_grid_never_ends`,
`test_layout_skipped_brake_point_rounds_every_field_to_two_decimals_independently`,
`test_layout_kept_brake_point_rounds_chainage_and_distance_to_two_decimals`,
`test_layout_station_entry_chainage_rounds_to_two_decimals`,
`test_layout_survey_axis_length_rounds_to_three_decimals_not_two`,
`test_layout_survey_braking_distance_rounds_to_two_decimals`,
`test_main_requires_both_axis_and_out_arguments`,
`test_main_creates_missing_output_directories_and_writes_sorted_indented_utf8`,
`test_main_output_directory_may_already_exist`.

**Kontrole negatywne, wszystkie WYKONANE** (mutacja wstrzyknięta w prawdziwy plik,
`python3 tools/tests/test_all.py test_detail_layout.py`, przywrócenie `git checkout --`
po każdej, potwierdzona zieloność `41/42` → `42/42` albo `33/33` → `42/42` przed
pierwszą):

```
### 119 ###                                                    FAIL test_layout_skipped_brake_point_rounds_every_field_to_two_decimals_independently
### 120 ###                                                    FAIL test_layout_skipped_brake_point_rounds_every_field_to_two_decimals_independently
### 121 ###                                                    FAIL test_layout_skipped_brake_point_rounds_every_field_to_two_decimals_independently
### 126 ###                                                    FAIL test_layout_kept_brake_point_rounds_chainage_and_distance_to_two_decimals
### 128 ###                                                    FAIL test_layout_kept_brake_point_rounds_chainage_and_distance_to_two_decimals
### 142 ###                                                    FAIL test_layout_station_entry_chainage_rounds_to_two_decimals
### 173 ###                                                    FAIL test_layout_survey_axis_length_rounds_to_three_decimals_not_two
### 179 ###                                                    FAIL test_layout_survey_braking_distance_rounds_to_two_decimals
### 191 required True->False (--axis) ###                      FAIL test_main_requires_both_axis_and_out_arguments: brakujący argument powinien dać SystemExit: ['--out', 'raport.json']
### 192 required True->False (--out) ###                       FAIL test_main_requires_both_axis_and_out_arguments: brakujący argument powinien dać SystemExit: ['--axis', 'os.json']
### 210 exist_ok True->False ###                                FAIL test_main_output_directory_may_already_exist: [Errno 17] File exists: '/tmp/tmptnkxo_gp'
### 210 logika or->and ###                                     FAIL test_main_creates_missing_output_directories_and_writes_sorted_indented_utf8: [Errno 2] No such file or directory: '.../raport.json'
### 212 ensure_ascii False->True ###                            FAIL test_main_creates_missing_output_directories_and_writes_sorted_indented_utf8: znak spoza ASCII powinien stać w pliku wprost
### 212 sort_keys True->False ###                               FAIL test_main_creates_missing_output_directories_and_writes_sorted_indented_utf8: ['checked_at', 'axis_id', ...]  (kolejność wstawienia, nie alfabetu)
### 212 indent 1->2 ###                                         FAIL test_main_creates_missing_output_directories_and_writes_sorted_indented_utf8: list index out of range
```

Każda kontrola: mutacja wstrzyknięta jednym poleceniem `python3 /tmp/mutate_line.py
tools/track/detail_layout.py <wiersz> "<było>" "<jest>"`, uruchomiony
`tools/tests/test_all.py test_detail_layout.py`, zapisany FAIL, `git checkout --
tools/track/detail_layout.py`, potwierdzone `git status --short` puste. Dla wiersza 91 —
kontrola opisana osobno w § 4, bo mutacja nie daje FAIL-a w normalnym sensie (proces
się zawiesza), tylko `TimeoutExpired` w izolowanym podprocesie.

## 7. Przegląd PO — rzeczywiste wyjście

```
$ python3 tools/tests/mutation_sweep.py --only tools/track/detail_layout.py --workers 4 \
      --journal /tmp/detail_layout_after.jsonl
[MUTACJE] --only 'tools/track/detail_layout.py' złapało 33 mutacji z 1 moduł(ów): tools/track/detail_layout.py
[MUTACJE] 33 mutacji do policzenia, 4 robotników, commit 008e34e, klasy operator,prog,logika,argument,przypisanie, dziennik /tmp/detail_layout_after.jsonl
[MUTACJE] kalibracja wyroczni: zestaw w drzewie BEZ mutacji
[MUTACJE] drzewo bazowe zielone, wyrocznia ma prawo mówić „zabita”
[MUTACJE] sonda pokrycia: jeden przebieg zestawu z licznikiem wierszy
[MUTACJE] wykonywanych wierszy dotyczy 33 z 33 mutacji; pozostałe 0 siedzą w kodzie, którego zestaw nie uruchamia
[MUTACJE] rozstrzygniętych 32/33, zabitych 28, ocalałych 4 (w tym 0 nieuruchomionych), nierozstrzygniętych 1
  OCALAŁA  tools/track/detail_layout.py:28 argument `0` -> `1`
  OCALAŁA  tools/track/detail_layout.py:29 argument `0` -> `1`
  OCALAŁA  tools/track/detail_layout.py:97 operator `<=` -> `<`
  OCALAŁA  tools/track/detail_layout.py:99 argument `0.0` -> `0.001`
```

**19 → 4 ocalałe** (dokładnie te cztery z § 5, każda z dowodem równoważności — żadna
inna nie przeżyła). **Wykonywanych wierszy: 26 → 33 z 33** — nowe testy CLI domknęły
sondę pokrycia do 100 %, potwierdzając, że siedem mutacji w `main()` naprawdę było
nieuruchomionych, nie „bezpiecznych”. Nierozstrzygnięta pozostaje 1 (wiersz 91,
niezmieniona — § 4 rozstrzyga ją poza narzędziem).

## 8. Czy kilometraż wyszedł inaczej, niż mówią raporty T-011

**Nie.** `test_detail_the_report_table_is_read_and_covers_all_six_packages`,
`test_detail_every_package_axis_matches_the_report_count_by_count`,
`test_detail_hectometres_are_the_floor_of_the_axis_length`,
`test_detail_every_station_on_every_package_axis_carries_a_stop_id` i
`test_detail_without_a_declared_speed_no_axis_gets_a_single_brake_point` — pięć testów,
które porównują `tools/track/detail_layout.py` z tabelą `reports/T-011-details-BF.md`
§ 1 (457 miejsc na sześciu osiach) — przeszły **bez zmian** przed i po tej pozycji, tak
jak wszystkie pozostałe testy modułu. Moduł nie został ruszony — tylko testy wokół
niego — więc inny wynik byłby niespodzianką; ta sekcja to jego jawne wykluczenie, żeby
nie trzeba było się domyślać, czy ktoś sprawdził.

## 9. Zauważone przy okazji, nietknięte

- **`tools/tests/mutation_sweep.py` jest złamany dla każdego modułu na dzisiejszym
  `main`** (§ 1) — poza zakresem tej pozycji, ale wymaga własnego wpisu w
  `docs/TASKS.md`, bo bez obejścia (nigdy niecommitowanego) żaden przegląd mutacyjny
  się dziś nie policzy.
- **`docs/TASKS.md`, pozycja 6.B16, pole „Skąd”, cytuje liczbę, której cytowany plik
  nie zawiera** (§ powyżej nagłówka) — zostawione tekstowo nietknięte zgodnie z zasadą
  „datowanego zapisu się nie przelicza”, zgłoszone tutaj i w raporcie dla proszącego.
- Linie 101 i 102 (`0.0` → `0.001` w argumentach `ramp_only_distance_m` i
  `braking_distance_m`, oba z `v1=0.0` na stałe) były już **zabite** w przeglądzie
  PRZED tą pozycją — nie były częścią triażu, ale warto odnotować, że sąsiadują
  z równoważną mutacją 99 i mimo to mają pokrycie; nie sprawdzałem czym dokładnie,
  bo to poza zakresem tej pozycji.
