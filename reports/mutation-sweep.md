# Przegląd mutacyjny bramek

**Snapshot na commicie:** `66b8301` (`main`, 04.09.2026)

Poprzedni snapshot stał na `737d592` (03.09.2026) i był o piętnaście scaleń wstecz —
w tym o większość ekstrakcji spod `bpy`, które ten sam raport wskazywał jako lekarstwo.
Liczby niżej pochodzą z **jednego przebiegu na jednym drzewie** i są odtwarzalne
poleceniem z sekcji „Jak to powtórzyć".

Narzędzie: `tools/tests/mutation_sweep.py`. Mutowany jest **kod pod testem**, nie testy.
Mutacja, która przeżyła, znaczy jedno z dwojga: brak pokrycia albo mutant równoważny.
Narzędzie nie zgaduje, które to.

## Czego ten przebieg NIE pokrywa, choć pozycja 5.1 tak brzmi

Pozycja 5.1 w `docs/TASKS.md` mówi „po jednej mutacji na każdą kontrolę
w `tools/ci/*.sh` i `tools/tests/test_*.py`". **To nie jest to, co robi to narzędzie**,
i rozjazd trzeba nazwać, zanim ktoś przeczyta liczby jako odpowiedź na tamto zdanie:

| pozycja 5.1 mówi | narzędzie robi |
|---|---|
| kontrole w `tools/ci/*.sh` | nic — mutuje wyłącznie Pythona; skrypty shellowe są nietknięte |
| kontrole w `tools/tests/test_*.py` | nic — mutuje **kod pod testem**, a testy pozostawia jako wyrocznię |
| „każdą kontrolę" | **pięć klas**: operatory porównań, progi liczbowe, łączniki logiczne, stałe w argumentach wywołań, akumulacja w przypisaniach augmentowanych |

**Trzeci wiersz jest przepisany 05.09.2026, a nie dopisany obok.** Do pozycji 6.D6 mówił
„wyłącznie **operatory porównań i progi liczbowe**; nie mutuje przypisań, wywołań ani
łączników logicznych" i to przestało być prawdą — pozycja 6.D6 domknęła ten rozjazd.
Wszystkie liczby w sekcjach „Wynik", „Kolejność triażu" i „Ocalałe, per plik" pochodzą
**sprzed** tej zmiany, ze starego zestawu dwóch klas; nowy zestaw jest zmierzony na
dwóch modułach w sekcji „Rozszerzony zestaw operatorów" niżej. Pierwsze dwa wiersze
tabeli stoją bez zmian: bramki shellowe i same testy nadal są nietknięte.

Wyjątkiem, i to pozornym, jest `tools/ci/assert_shot_metadata.py` — leży w `tools/ci`,
ale jest modułem Pythona i wchodzi do przebiegu jako kod pod testem, nie jako bramka.

To nie znaczy, że pozycja 5.1 jest zła. Znaczy, że **domyka ją tylko częściowo**:
mutowanie bramek shellowych i samych testów wymagałoby drugiego narzędzia i osobnej
wyroczni, bo dla testu wyrocznią byłby wtedy kod, a nie odwrotnie.

## Rozszerzony zestaw operatorów — pomiar 05.09.2026, gałąź `wiecej-operatorow-mutacji`

Pozycja 6.D6. Dwie zmiany naraz i obie są potrzebne osobno: doszły **trzy klasy
mutacji**, a ocalałe przestały być jedną kupką.

### Co doszło

| klasa | przykład | ile w drzewie `c1563d0` |
|---|---|---:|
| `operator` *(było)* | `a < b` → `a <= b` | 799 |
| `prog` *(było)* | `a < 1.5` → `a < 1.515` | 239 |
| `logika` | `a and b` → `a or b` | 344 |
| `argument` | `round(x, 3)` → `round(x, 4)` | 824 |
| `przypisanie` | `t += dt` → `t = dt` | 84 |

**1038 → 2290 mutacji** w całym drzewie, **985 → 1940** po odjęciu modułów
nieosiągalnych. Stary zestaw odtwarza `--operators operator,prog` i robi to **co do
identyfikatora**, nie „mniej więcej tyle samo": `test_legacy_kinds_are_a_subset_of_the_new_run`
porównuje listy `plik:wiersz:przesunięcie` pozycja po pozycji na całym drzewie.

Liczba 1038 nie kłóci się z 980 z nagłówka tego raportu: 980 zmierzono na `66b8301`,
1038 na `c1563d0`. To dryf drzewa przez kilkanaście scaleń, nie skutek zmiany
operatorów — obie liczby są ze **starego** zestawu dwóch klas.

`argument` mutuje stałą liczbową i flagę logiczną **stojącą w argumencie wywołania**,
a nie podmienia argumentu na wartość neutralną. Podmiana na `None` albo `0` daje
w Pythonie natychmiastowy `TypeError`, czyli mutanta zabijanego przez sam import
i niemówiącego nic o bramkach; przesunięcie liczby pyta o to samo, o co pyta `prog`,
tylko w miejscu, gdzie w tym repozytorium siedzą tolerancje (`abs_tol=`, `rel_tol=`,
`round(x, n)`) — a te były dotąd poza zasięgiem narzędzia.

### Ocalała ≠ nieprzetestowana

Mutacja przypisania albo argumentu wywołania trafia często w kod, do którego wykonanie
nigdy nie dochodzi: gałąź `if __name__ == "__main__"`, funkcja drukująca raport,
obsługa błędu. Taka mutacja przeżywa **nie dlatego, że bramka nie bramkuje, tylko
dlatego, że nikt jej nie odpalił** — a policzona razem z prawdziwą dziurą kieruje triaż
na kod, w którym nie ma czego naprawiać.

Przebieg mierzy więc raz, **przed mutowaniem**, które wiersze zestaw testów naprawdę
wykonuje: jeden przebieg `test_all.py` z licznikiem wierszy wstrzykniętym przez
`sitecustomize` na `PYTHONPATH`, czyli tak, żeby licznik działał również
w podprocesach (część bramek chodzi przez `sys.executable`). Mierzone jest wykonanie
**wiersza**, nie zmutowanego podwyrażenia — „nieuruchomiona" jest przez to twarda,
a „wykonana" jest ograniczeniem z góry.

To **nie jest** ta sama rzecz co „nierozstrzygnięta". Nierozstrzygnięta mówi o wyroczni,
która nie doszła do końca; nieuruchomiona mówi o mutancie, do którego nie doszło
wykonanie. Nierozstrzygnięte są dodatkowo rozbite na dwa powody, bo i one mówią
o różnych rzeczach: **przekroczony czas** znaczy, że zestaw się zapętlił, czyli mutant
JEST obserwowalny, tylko nie w postaci, którą ta wyrocznia umie odczytać; **awaria poza
mutacją** (sygnał, OOM) nie mówi o mutancie nic.

### Zmierzone na dwóch modułach

Przebieg „przed" puszczony na `c1563d0` (`main`, przed tą pozycją), przebieg „po" na
`fcda419` — commicie tej gałęzi przed ostatnim `--amend`, różniącym się od scalanej
wersji dwoma wierszami prozy w `report()`. Żaden z tych commitów nie tyka
`braking.py` ani `crs.py`, więc drzewo pod mutacją jest po obu stronach identyczne —
i **wyrocznia też**: robotnik kasuje `tools/tests/test_mutation_sweep.py` z drzewa
roboczego w obu przebiegach, więc testy dopisane w tej pozycji nie wchodzą do
porównania.

| | `braking.py` przed | `braking.py` po | `crs.py` przed | `crs.py` po |
|---|---:|---:|---:|---:|
| mutacji | 11 | 23 | 14 | 29 |
| zabitych | 6 | 8 | 10 | 24 |
| **ocalałych razem** | **5** | **13** | **4** | **5** |
| — w tym mimo wykonania | *nie mierzone* | 5 | *nie mierzone* | 5 |
| — w tym nieuruchomionych | *nie mierzone* | 8 | *nie mierzone* | 0 |
| nierozstrzygniętych | 0 | 2 | 0 | 0 |

Per klasa, przebieg „po":

| klasa | `braking.py` zabite / ocalałe wykonane / nieuruchomione / nieroz. | `crs.py` zabite / ocalałe wykonane / nieuruchomione / nieroz. |
|---|---|---|
| `operator` | 6 / 3 / 1 / 0 | 8 / 2 / 0 / 0 |
| `prog` | 0 / 0 / 1 / 0 | 2 / 2 / 0 / 0 |
| `logika` | 0 / 1 / 0 / 1 | 1 / 0 / 0 / 0 |
| `argument` | 0 / 1 / 6 / 0 | 7 / 1 / 0 / 0 |
| `przypisanie` | 2 / 0 / 0 / 1 | 6 / 0 / 0 / 0 |

### Co z tego widać, czego wcześniej nie było widać

**1. Dwie z pięciu „ocalałych" `braking.py` z tego raportu to martwy kod, nie dziura
w bramce.** Sekcja „Ocalałe, per plik" wymienia dla `braking.py` wiersze 163, 165
i **287** (dwa razy). Licznik wierszy mówi, że **287 nie wykonuje się ani razu**: stoi
w `report()`, funkcji drukującej tabele na konsolę, której żaden test nie woła. Ta sama
funkcja daje kolejnych sześć nieuruchomionych z nowej klasy `argument` (wiersze 277,
278, 303, 304, 306, 307). Triaż `braking.py` prowadzony z tego raportu zaczynałby więc
od pisania testu na `print`.

**2. Nowa klasa `przypisanie` potrafi zabić, i to nie przypadkiem.** `braking.py:205`
i `:206` — zdjęcie akumulacji z `s += ds` i `resistance_per_kg += a_res * ds` — są
zabite przez zestaw; w `crs.py` zabitych jest **wszystkie sześć** (iteracje Helmerta
`x += xw - fx`, Newton `lon -= …`, szerokość autaliczna `phi += step`). Klasa, która
w drzewie daje tylko 84 mutacje, ma w tych dwóch modułach 8 zabitych na 9
rozstrzygniętych — trafia w pętle iteracyjne, czyli w miejsca, gdzie stary zestaw
mutował co najwyżej warunek stopu.

**3. Nowa klasa `logika` znajduje ocalałą tam, gdzie stary zestaw znajdował tylko
operatory.** `braking.py:163`, `if mid <= low or mid >= high:` — `or` → `and` przeżywa
wykonanie. W tym samym wierszu stary zestaw miał już dwie ocalałe (`<=` → `<`
i `>=` → `>`), więc to nie jest nowe miejsce, tylko **trzecia niesprawdzona rzecz
w miejscu, o którym raport twierdził, że wie o nim wszystko**.

**4. Dwie nierozstrzygnięte i obie z przekroczonego czasu, obie z nowych klas.**
`braking.py:200` (`and` → `or` w warunku pętli) i `braking.py:207` (`n += 1` → `n = 1`)
zawieszają `sim_brake`. Zmierzone wykonaniem, poza przeglądem, na wywołaniu
`sim_brake(200/3.6, 0.0, cfg, None, dt=1/120, limit_s=120)`:

```
=== BEZ MUTACJI (kontrola)
    wrocilo po 0.005 s: droga=6666.7 m, czas=120.0 s, krokow=14400
=== braking.py:207  n += 1  ->  n = 1
    NIE WROCILO w 25 s — petla nieskonczona
=== braking.py:200  and -> or
    NIE WROCILO w 25 s — petla nieskonczona
```

To jest znalezisko tej samej rodziny co opisana niżej nierozstrzygnięta
z `detail_layout.py`, tylko o poziom głębiej: `sim_brake` **ma** ogranicznik kroków
(`max_steps`), ale ogranicznik przestaje ograniczać, gdy zmutowany zostaje licznik,
od którego zależy. Naprawa leży w kodzie pod testem i **nie należy do tej pozycji**.

**5. `crs.py` wypada odwrotnie niż `braking.py` i to też jest informacja.** 29 mutacji,
**zero nieuruchomionych**, zero nierozstrzygniętych, 24 zabite — moduł nie ma kodu,
którego zestaw nie dotyka, a nowe klasy zabijają w nim 14 mutacji z 15. Ta sama zmiana
narzędzia daje w jednym module „osiem ocalałych, których nikt nie uruchamia", a w drugim
„czternaście nowych zabić". Bez rozdzielenia ocalałych na dwie kupki oba moduły
wyglądałyby na pogorszone.

**6. Jedyna nowa ocalała w `crs.py` to podręcznikowy mutant równoważny.**
`crs.py:212`, `for _ in range(6)` → `range(7)` w odwrotności Helmerta. Docstring tej
funkcji mówi, że „iteracja schodzi do precyzji maszynowej"; siódmy obrót nie ma czego
poprawić, więc żaden test nie ma prawa tego zobaczyć. Kwalifikacja: **mutant
równoważny**, nie dziura — i warto ją zapisać, bo budżet iteracji jest wielkością,
której stary zestaw operatorów nie umiał tknąć w ogóle (to argument wywołania, nie
porównanie).

### Czego ten pomiar NIE obejmuje

Pełny przebieg na nowym zestawie **nie został wykonany**. To 1940 mutacji osiągalnych
wobec 985 w przebiegu z nagłówka; przy tempie tamtego przebiegu (12,6 mutacji na minutę,
4 robotniki) daje to ponad dwie i pół godziny maszyny, a przy dzisiejszym zestawie
testów — dłużej. Tabele „Wynik", „Kolejność triażu" i „Ocalałe, per plik" niżej
pochodzą więc **ze starego zestawu operatorów** i tak trzeba je czytać, dopóki ktoś
nie przeliczy całości.

## Wynik

| | ten przebieg (`66b8301`) | poprzedni (`737d592`) |
|---|---:|---:|
| mutacji w drzewie | 980 | 961 |
| pominiętych jako nieosiągalne | 51 | 148 |
| **policzonych** | **929** | **813** |
| rozstrzygniętych | 929 | 812 |
| zabitych | 661 | 213 |
| **ocalałych** | **268** | **599** |
| nierozstrzygniętych | **0** | 1 |
| **pokrycie kodu osiągalnego** | **71,2 %** | **26,2 %** |

Kolumna „poprzedni" jest przeliczona **na kodzie osiągalnym**, a nie przepisana
z tamtego podsumowania. Tamten raport podawał w tabeli głównej 961 mutacji, 216 zabitych
i 22,5 % pokrycia, bo wrzucał do jednej puli moduły, których nie da się zaimportować bez
Blendera — a ich mutacji nie da się zabić i sam raport pisał o tym w osobnej sekcji.
Uczciwe porównanie idzie po osiągalnych: 813 mutacji, z tego 599 ocalałych i **jedna
nierozstrzygnięta**, czyli 213 zabitych na 812 rozstrzygniętych — 26,2 %. Ta jedynka
jest tu istotna: nierozstrzygnięta nie jest zabiciem, więc odchodzi od licznika I od
mianownika, a nie tylko od jednego z nich. Kontrola zamknięcia: 213 zabitych osiągalnych
plus 3 zabite nieosiągalne (te trzy łapały testy czytające pliki jako TEKST) daje 216,
czyli dokładnie liczbę z tamtego podsumowania.

Różnica **26,2 % → 71,2 %** jest więc mierzona tą samą miarą po obu stronach.

## Skąd ta różnica, liczbą

Trzy rzeczy naraz, i każda daje się wskazać:

1. **Nieosiągalne zeszły z 148 mutacji na 51.** Ekstrakcje spod `bpy` przeniosły
   porównania i progi do modułów, które da się zaimportować, więc te same bramki
   są dziś w zasięgu testów. Największe ruchy: `m7_shell.py` 35 → 2,
   `tunnel_sweep.py` 35 → 6, `profile_vehicle.py` 26 → 7, `glb_roundtrip.py` 10 → 1,
   `place_vehicle.py` 7 → 1.

   `capture_blender.py` zeszło z 10 mutacji na **zero** i to jest inny przypadek,
   którego nie wolno wliczyć do tej samej kolumny: moduł nadal istnieje i nadal
   importuje `bpy`, więc nadal jest nieosiągalny. Po prostu nie ma już w nim ani
   jednego porównania ani progu, które to narzędzie mutuje — sprawdzone: nie ma go
   ani wśród pominiętych, ani wśród policzonych. Brak mutacji nie jest pokryciem.
2. **Zestaw testów urósł z 692 na 1333 pozycje**, a przyrost szedł głównie w progi
   i granice — czyli dokładnie w to, co to narzędzie mutuje.
3. **Zero nierozstrzygniętych, i to nie przez zniknięcie problemu.** Poprzedni
   przebieg miał jedną nierozstrzygniętą: mutacja strażnika `step_m <= 0.0`
   w `detail_layout.py` zamieniała go w pętlę nieskończoną, więc proces testów
   nigdy nie kończył pracy i narzędzie uczciwie mówiło „nie wiem". Tamten raport
   proponował wtedy niezależny ogranicznik liczby iteracji jako decyzję właściciela.

   **Ogranicznik jest.** `MAX_MARKS = int(MAX_AXIS_LENGTH_M / MIN_SENSIBLE_STEP_M)`
   = 40 000, sprawdzany wewnątrz pętli, jawnie opisany jako niezależny od strażnika.
   Skutek w tym przebiegu jest dokładnie taki, jaki miał być — obie mutacje strażnika
   (wiersz 78) i mutacja samego ogranicznika (wiersz 83) są **rozstrzygnięte
   i zabite**, każda przez test pisany na nią:

   ```
   detail_layout.py:78 prog `0.0` -> `0.001`     ZABITA
       test_layout_hectometre_grid_terminates_with_the_step_guard_removed
       test_detail_hectometre_step_of_a_millimetre_is_still_positive
   detail_layout.py:78 operator `<=` -> `<`      ZABITA
       test_layout_hectometre_grid_terminates_with_the_step_guard_removed
   detail_layout.py:83 operator `>=` -> `>`      ZABITA
       test_layout_hectometre_grid_stops_at_max_marks_and_says_so_with_numbers
   ```

   To jest najlepszy pojedynczy dowód, jaki ten przebieg daje: nierozstrzygnięta
   z przekroczonego czasu **kryła realną usterkę projektową**, została naprawiona,
   a naprawa jest dziś przybita testem, który mutacja wywraca.

Skok jest na tyle duży, że nie wolno go po prostu wpisać. Sprawdzony w obie strony,
wykonaniem, na źródle:

**Kontrola zabitej.** `tools/track/crs.py:306`, operator `<` → `<=`
(to strażnik zbieżności z progiem residuum):

```
$ python3 tools/tests/test_all.py
FAIL test_crs_convergence_residual_exactly_at_a_nonzero_tolerance_fails:
     residuum == tolerance_m == 0.4007257902994752 powinno być porażką
FAIL test_crs_convergence_residual_exactly_at_zero_tolerance_fails:
     residuum == tolerance_m == 0.0 powinno być porażką
  1331/1333 przeszło
```

Zabicie jest prawdziwe i pochodzi z **testu granicznego**, czyli takiego, który dotyka
progu dokładnie. Osłabienie `<` do `<=` wpuszcza residuum równe tolerancji jako wynik
zbieżny — i oba testy to nazywają.

**Kontrola ocalałej.** `tools/blender/clearance.py:47`, próg `0.0` → `0.001`:

```
$ python3 tools/tests/test_all.py
  1333/1333 przeszło
```

Cały zestaw pozostaje zielony. Mutacja rzeczywiście żyje.

## Pułapka odczytu: wiersz i operator NIE identyfikują mutacji

W `tools/visual/pngio.py:42` operator `<=` → `<` występuje **i jako zabita, i jako
ocalała** — bo w tym wierszu stoją dwa `<=` w różnych kolumnach i to dwie różne
mutacje. Identyfikatorem jest `plik:wiersz:przesunięcie`, nie `plik:wiersz`.
Czytając tabele niżej, nie da się więc powiedzieć „ta mutacja przeżyła" o samym
wierszu z operatorem, jeżeli wiersz zawiera dwa takie same operatory.

## Jak czytać ocalałe

Ocalała mutacja **nie jest** automatycznie usterką. Trzeba ją zakwalifikować do jednej
z czterech klas; pierwszą narzędzie rozstrzyga pomiarem od pozycji 6.D6, trzy pozostałe
zostają czytającemu:

| klasa | co znaczy | co z tym zrobić |
|---|---|---|
| **kod nieuruchomiony** | wiersz nie wykonał się w przebiegu bez mutacji ani razu — mierzone licznikiem wierszy, nie zgadywane | osobna sekcja w raporcie narzędzia; nie liczy się do pokrycia kodu wykonanego |
| **realna dziura** | zmiana zmienia zachowanie, które ktoś kiedyś zobaczy, a żaden test tego nie sprawdza | dopisać test z kontrolą negatywną |
| **mutant równoważny** | zmiany nie da się zaobserwować (np. tolerancja `1e-12` przesunięta o procent) | zapisać jako równoważną, nie „naprawiać" |
| **remis bez znaczenia** | `<` kontra `<=` przy wyborze minimum: przy remisie obie gałęzie dają tę samą wartość | jak wyżej, chyba że liczy się INDEKS |

Rozróżnienie wymaga przeczytania kodu. Wpisanie mutanta równoważnego jako usterki
zawyża znalezisko dokładnie tak samo, jak liczenie zepsutego przebiegu jako zabicia
zawyżało pokrycie w poprzednich wersjach tego narzędzia.

## Moduły nieosiągalne — 51 mutacji w 9 plikach

Import tych modułów wymaga `bpy`, więc `tools/tests/test_all.py` nie ma jak ich
dotknąć. Ich mutacji nie da się zabić — nie dlatego, że nikt nie napisał testu,
tylko dlatego, że nie istnieje droga. Narzędzie **pomija je i mówi o tym wprost**;
`--include-unreachable` wlicza je razem z resztą i wtedy pokrycie schodzi pozornie.

| plik | mutacji dziś | mutacji na `737d592` |
|---|---:|---:|
| `tools/blender/material_test_scene.py` | 12 | — |
| `tools/blender/station_kit.py` | 11 | 8 |
| `tools/blender/detail_markers.py` | 9 | 6 |
| `tools/blender/profile_vehicle.py` | 7 | 26 |
| `tools/blender/tunnel_sweep.py` | 6 | 35 |
| `tools/blender/m7_shell.py` | 2 | 35 |
| `tools/blender/render_check.py` | 2 | 8 |
| `tools/blender/glb_roundtrip.py` | 1 | 10 |
| `tools/blender/place_vehicle.py` | 1 | 7 |

`material_test_scene.py` doszedł 04.09.2026 z T-902 i jest jedynym pozycją na tej
liście, która **urosła z nowej pracy**, a nie została po ekstrakcji. `station_kit.py`
i `detail_markers.py` też urosły — ich czysta logika wyszła do `tools/track/`,
a w module pod `bpy` zostało samo składanie scenki, którego przybyło.

Lekarstwem tutaj nie są testy, tylko dalsze wyciąganie logiki spod `bpy`.
Bramką na to, że te moduły w ogóle się wykonują, jest `tools/ci/*.sh`
(`test_ci_every_blender_generator_has_a_gate`) — i to jest jedyna droga, jaka tam
dziś istnieje.

## Kolejność triażu — po udziale, nie po liczbie

Wysoki udział znaczy, że testy tego modułu sprawdzają co innego, niż deklarują;
duża liczba przy niskim udziale znaczy tylko, że moduł jest duży.

> **Ta kolejka jest nieaktualna dla dwóch pierwszych pozycji `clearance*`, i jest tu
> przepisana, a nie dopisana obok.** Tabela niżej jest zdjęciem drzewa `66b8301`
> z 04.09.2026, a jednocześnie **listą tego, co robić dalej** — i w tej drugiej roli
> kłamie, bo `clearance_profile.py` przeszedł od tamtego przebiegu **dwa pełne
> triaże**: etap drugi (66 → 49) i etap trzeci (45 → 17), oba rozpisane
> w `reports/mutation-triage-clearance.md`. Wiersz „66 / 77 | 86 %" wskazywał więc
> jako najpilniejszy moduł, który jest dziś jednym z lepiej pokrytych.
>
> **Zmierzone ponownie 05.09.2026 na `9f4ae98`**, tym samym narzędziem i tą samą
> miarą, 4 robotników:
>
> ```
> $ python3 tools/tests/mutation_sweep.py --only clearance_profile.py --workers 4 \
>       --journal /tmp/cp.jsonl --json /tmp/cp.json
> [MUTACJE] 77 mutacji do policzenia, 4 robotników, commit 9f4ae98
> [MUTACJE] rozstrzygniętych 77/77, zabitych 61, ocalałych 16, nierozstrzygniętych 0
> ```
>
> | `tools/blender/clearance_profile.py` | ocalałe / mutacje | udział |
> |---|---:|---:|
> | `66b8301`, ten raport | 66 / 77 | 86 % |
> | `9f4ae98`, dziś | **16 / 77** | **20,8 %** |
>
> Z 86 % na 20,8 % — moduł spada z drugiego miejsca kolejki poniżej połowy tabeli.
> Sekcja „Ocalałe, per plik" niżej wymienia dla niego 66 wierszy i **żaden z nich nie
> jest listą do zrobienia**; jest to zapis punktu wyjścia obu triaży i dlatego zostaje
> nieprzeliczony. Szesnaście dzisiejszych ocalałych jest rozpisanych po jednej
> — dziewięć zmierzonych równoważności i pytania do właściciela — w `docs/24` i w §„Etap
> trzeci" tamtego raportu.
>
> **Różnica 17 (tamten raport) wobec 16 (dziś) nie jest szumem pomiaru.** Etap trzeci
> mierzył na `68da7da` i podawał 76 mutacji; dziś jest ich 77, bo po nim weszły
> `82cc22e` (próg wypukłości, pozycja 13 z `docs/24`) i `df36903` (dziewięć pozycji
> `docs/24` rozstrzygniętych). Przebieg jest deterministyczny — mutacje powstają z AST
> w ustalonej kolejności — więc dwa przebiegi na `9f4ae98` dadzą te same 16.
>
> **Kontrola przy okazji, bo dotyczy wiarygodności tej tabeli:** w dzienniku tego
> przebiegu **ani jedno** z 61 zabić nie pochodzi od
> `test_ci_blender_installer_refuses_a_tarball_whose_checksum_does_not_match` —
> policzone wprost po polu `padly`, 0 wpisów na 77. Ten test produkował fałszywe
> zabicia przy trzech robotnikach do czasu #207; przy czterech robotnikach na
> dzisiejszym drzewie nie produkuje ich wcale.
>
> **Pozostałych wierszy tej tabeli NIE przeliczałem** i nie wolno ich czytać jako
> stanu dzisiejszego: `clearance.py`, `placement.py`, `build_alignment.py` i reszta
> mają własne raporty triażu w `reports/mutation-triage-*.md`, każdy z własną datą
> i własnym commitem. Przeliczenie całej tabeli to nowy pełny przebieg (929 mutacji,
> 74 minuty), czyli osobne zadanie, a nie akapit w cudzym.

| plik | ocalałe / mutacje | udział |
|---|---:|---:|
| `tools/track/make_test_track.py` | 2 / 2 | 100 % |
| `tools/blender/clearance_profile.py` | 66 / 77 (dziś 16 / 77) | 86 % |
| `tools/blender/placement.py` | 26 / 40 | 65 % |
| `tools/track/crs.py` | 8 / 14 | 57 % |
| `tools/track/build_alignment.py` | 39 / 69 | 57 % |
| `tools/blender/clearance.py` | 6 / 11 | 55 % |
| `tools/physics/schedule_envelope.py` | 5 / 10 | 50 % |
| `tools/blender/sweep.py` | 37 / 79 | 47 % |
| `tools/physics/braking.py` | 5 / 11 | 45 % |
| `tools/physics/reference.py` | 3 / 8 | 38 % |
| `tools/blender/lod.py` | 37 / 104 | 36 % |
| `tools/blender/m7_report.py` | 9 / 31 | 29 % |
| `tools/ci/assert_shot_metadata.py` | 6 / 39 | 15 % |
| `tools/track/station_layout.py` | 1 / 7 | 14 % |
| `tools/track/detail_layout.py` | 1 / 9 | 11 % |
| `tools/visual/pngio.py` | 4 / 38 | 11 % |
| `tools/track/crosscheck_alignment.py` | 2 / 19 | 11 % |
| `tools/blender/profiles.py` | 1 / 13 | 8 % |
| `tools/track/tunnel_width.py` | 2 / 28 | 7 % |
| `tools/blender/m7_layout.py` | 1 / 17 | 6 % |
| `tools/track/shapefile.py` | 1 / 17 | 6 % |
| `tools/track/validate.py` | 2 / 37 | 5 % |
| `tools/track/inspire_rail.py` | 2 / 41 | 5 % |
| `tools/visual/framing.py` | 1 / 22 | 5 % |
| `tools/track/surface_sections.py` | 1 / 29 | 3 % |

**Pełne pokrycie mają 15 pliki z 40** — ani jednej ocalałej mutacji:
`camera_aim.py`, `glb_report.py`, `profile_scan.py`, `tunnel_manifest.py`, `vehicle_fit.py`, `assert_empty_frame_negative.py`, `provenance.py`, `snapshot_source.py`, `data_freshness.py`, `fetch_osm_routes.py`, `network_chainage.py`, `normalize_stops.py`, `timetable.py`, `capture_plan.py`, `compare.py`.

## Jak to powtórzyć

```bash
git checkout 66b8301
python3 tools/tests/mutation_sweep.py --workers 4 \
    --journal /tmp/mutacje.jsonl --json /tmp/mutacje.json --out /tmp/sweep.md
```

Na drzewie po scaleniu pozycji 6.D6 to polecenie daje **nowy, pięcioklasowy** zestaw.
Żeby powtórzyć dokładnie liczby z tego raportu, trzeba zawęzić klasy:

```bash
python3 tools/tests/mutation_sweep.py --workers 4 --operators operator,prog \
    --journal /tmp/mutacje.jsonl --json /tmp/mutacje.json --out /tmp/sweep.md
```

Zmierzone na tej maszynie: 929 mutacji, 4 robotniki, **74 minuty** (07:23–08:37 UTC, ok. 12,6 mutacji
na minutę przy przebiegu suity 25 s). Dziennik JSONL jest dopisywany po każdej mutacji,
więc przerwany przebieg da się wznowić tym samym poleceniem. Mutacje powstają z AST
w ustalonej kolejności (plik, wiersz, kolumna), więc dwa przebiegi na tym samym drzewie
dają tę samą listę i te same identyfikatory.

Kontrole ręczne z sekcji „Skąd ta różnica" powtarza się skryptem, który wprowadza
mutację po `plik:wiersz:przesunięcie` z `mutacje.json`, uruchamia suitę i przywraca
plik — sprawdzając przy okazji, że przesunięcie faktycznie wskazuje na `bylo`.

## Ocalałe, per plik

### `tools/blender/clearance.py` — 6

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 47 | prog | `0.0` | `0.001` |
| 47 | operator | `<=` | `<` |
| 50 | operator | `>=` | `>` |
| 70 | operator | `<` | `<=` |
| 99 | operator | `<=` | `<` |
| 101 | prog | `0.0` | `0.001` |

### `tools/blender/clearance_profile.py` — 66 *(na `66b8301`; dziś 16 — patrz „Kolejność triażu")*

Lista niżej jest **punktem wyjścia dwóch triaży**, nie listą do zrobienia. Numery
wierszy odnoszą się do drzewa `66b8301` i po `82cc22e` oraz `df36903` nie wskazują już
tych samych miejsc w pliku.

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 91 | operator | `<=` | `<` |
| 99 | operator | `<=` | `<` |
| 99 | prog | `0.0` | `0.001` |
| 104 | operator | `<=` | `<` |
| 104 | prog | `0.0` | `0.001` |
| 119 | prog | `0.0` | `0.001` |
| 174 | prog | `0.0` | `0.001` |
| 174 | operator | `>` | `>=` |
| 181 | operator | `<` | `<=` |
| 185 | prog | `0.0` | `0.001` |
| 196 | operator | `<=` | `<` |
| 198 | operator | `>=` | `>` |
| 198 | prog | `0.9` | `0.909` |
| 200 | prog | `0.9` | `0.909` |
| 200 | operator | `>=` | `>` |
| 217 | operator | `<` | `<=` |
| 237 | operator | `>` | `>=` |
| 240 | operator | `>` | `>=` |
| 248 | operator | `<` | `<=` |
| 324 | operator | `<` | `<=` |
| 324 | prog | `0.0` | `0.001` |
| 326 | operator | `<` | `<=` |
| 337 | operator | `<` | `<=` |
| 366 | operator | `<` | `<=` |
| 382 | operator | `<=` | `<` |
| 382 | prog | `0.0` | `0.001` |
| 385 | operator | `<=` | `<` |
| 385 | prog | `0.0` | `0.001` |
| 389 | operator | `>` | `>=` |
| 389 | prog | `1e-9` | `1.01e-09` |
| 400 | operator | `>` | `>=` |
| 400 | prog | `1e-6` | `1.0099999999999999e-06` |
| 403 | operator | `>` | `>=` |
| 403 | prog | `1e-6` | `1.0099999999999999e-06` |
| 406 | operator | `>` | `>=` |
| 424 | operator | `<=` | `<` |
| 428 | operator | `<=` | `<` |
| 465 | operator | `<` | `<=` |
| 466 | operator | `<` | `<=` |
| 466 | prog | `0.0` | `0.001` |
| 475 | operator | `<` | `<=` |
| 492 | operator | `<=` | `<` |
| 505 | operator | `<` | `<=` |
| 511 | operator | `<=` | `<` |
| 544 | operator | `<=` | `<` |
| 544 | prog | `0.0` | `0.001` |
| 559 | operator | `<` | `<=` |
| 559 | operator | `>` | `>=` |
| 564 | operator | `<` | `<=` |
| 580 | prog | `1e-9` | `1.01e-09` |
| 580 | operator | `<` | `<=` |
| 605 | operator | `<` | `<=` |
| 605 | prog | `3` | `4` |
| 640 | operator | `>` | `>=` |
| 640 | operator | `<` | `<=` |
| 643 | operator | `<=` | `<` |
| 643 | operator | `<=` | `<` |
| 653 | operator | `>` | `>=` |
| 679 | operator | `<` | `<=` |
| 679 | prog | `1e-12` | `1.01e-12` |
| 682 | prog | `3` | `4` |
| 682 | operator | `<` | `<=` |
| 692 | operator | `<` | `<=` |
| 692 | prog | `2` | `3` |
| 733 | operator | `<` | `<=` |
| 755 | operator | `<` | `<=` |

### `tools/blender/lod.py` — 37

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 107 | operator | `<=` | `<` |
| 107 | prog | `0.0` | `0.001` |
| 126 | prog | `0.0` | `0.001` |
| 129 | operator | `<` | `<=` |
| 129 | prog | `0.0` | `0.001` |
| 129 | operator | `>` | `>=` |
| 129 | prog | `1.0` | `1.01` |
| 143 | prog | `0.0` | `0.001` |
| 143 | prog | `0.0` | `0.001` |
| 151 | prog | `0.0` | `0.001` |
| 153 | prog | `0.0` | `0.001` |
| 183 | operator | `<` | `<=` |
| 199 | prog | `0.0` | `0.001` |
| 202 | operator | `<` | `<=` |
| 202 | prog | `0.0` | `0.001` |
| 202 | operator | `>` | `>=` |
| 202 | prog | `1.0` | `1.01` |
| 212 | operator | `<=` | `<` |
| 212 | prog | `0.0` | `0.001` |
| 217 | operator | `>` | `>=` |
| 217 | prog | `0.0` | `0.001` |
| 222 | prog | `0.0` | `0.001` |
| 232 | operator | `<` | `<=` |
| 232 | prog | `1e-12` | `1.01e-12` |
| 327 | operator | `<` | `<=` |
| 367 | operator | `<` | `<=` |
| 367 | operator | `<` | `<=` |
| 375 | operator | `<=` | `<` |
| 375 | prog | `0.0` | `0.001` |
| 404 | operator | `<` | `<=` |
| 404 | operator | `<` | `<=` |
| 411 | operator | `<=` | `<` |
| 411 | prog | `0.0` | `0.001` |
| 487 | operator | `<=` | `<` |
| 489 | operator | `<` | `<=` |
| 571 | operator | `>` | `>=` |
| 631 | prog | `0.0` | `0.001` |

### `tools/blender/m7_layout.py` — 1

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 192 | operator | `>=` | `>` |

### `tools/blender/m7_report.py` — 9

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 46 | operator | `<=` | `<` |
| 46 | operator | `<=` | `<` |
| 52 | operator | `<=` | `<` |
| 52 | operator | `<=` | `<` |
| 85 | operator | `>` | `>=` |
| 87 | operator | `>` | `>=` |
| 95 | operator | `<=` | `<` |
| 96 | operator | `<=` | `<` |
| 169 | operator | `>` | `>=` |

### `tools/blender/placement.py` — 26

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 32 | operator | `<=` | `<` |
| 32 | prog | `0.0` | `0.001` |
| 53 | operator | `>` | `>=` |
| 57 | operator | `<` | `<=` |
| 57 | operator | `<` | `<=` |
| 96 | operator | `<` | `<=` |
| 96 | prog | `1e-9` | `1.01e-09` |
| 100 | operator | `<` | `<=` |
| 100 | prog | `1e-9` | `1.01e-09` |
| 140 | operator | `>` | `>=` |
| 146 | operator | `<` | `<=` |
| 164 | operator | `<` | `<=` |
| 164 | prog | `1e-12` | `1.01e-12` |
| 181 | operator | `<` | `<=` |
| 202 | prog | `0.0` | `0.001` |
| 205 | operator | `<` | `<=` |
| 205 | operator | `>` | `>=` |
| 205 | prog | `1.0` | `1.01` |
| 212 | operator | `<` | `<=` |
| 229 | operator | `<` | `<=` |
| 229 | prog | `1e-9` | `1.01e-09` |
| 233 | operator | `<=` | `<` |
| 236 | prog | `1e-4` | `0.000101` |
| 236 | operator | `<=` | `<` |
| 258 | operator | `>` | `>=` |
| 313 | operator | `<=` | `<` |

### `tools/blender/profiles.py` — 1

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 33 | operator | `>` | `>=` |

### `tools/blender/sweep.py` — 37

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 54 | prog | `0.0` | `0.001` |
| 65 | operator | `>` | `>=` |
| 92 | prog | `0.0` | `0.001` |
| 126 | prog | `0.0` | `0.001` |
| 130 | operator | `>` | `>=` |
| 130 | operator | `<` | `<=` |
| 130 | prog | `0.0` | `0.001` |
| 130 | prog | `1.0` | `1.01` |
| 143 | operator | `>` | `>=` |
| 143 | prog | `1e-9` | `1.01e-09` |
| 161 | operator | `<` | `<=` |
| 161 | prog | `1e-9` | `1.01e-09` |
| 174 | operator | `<` | `<=` |
| 174 | prog | `1e-18` | `1.01e-18` |
| 204 | operator | `<` | `<=` |
| 204 | prog | `0.0` | `0.001` |
| 204 | operator | `<` | `<=` |
| 219 | operator | `<=` | `<` |
| 224 | operator | `>` | `>=` |
| 224 | prog | `1e-6` | `1.0099999999999999e-06` |
| 237 | operator | `<` | `<=` |
| 237 | operator | `<` | `<=` |
| 250 | operator | `<` | `<=` |
| 345 | operator | `>` | `>=` |
| 345 | prog | `0.0` | `0.001` |
| 380 | operator | `>` | `>=` |
| 380 | prog | `0.0` | `0.001` |
| 386 | operator | `<` | `<=` |
| 410 | prog | `1e-9` | `1.01e-09` |
| 410 | operator | `>` | `>=` |
| 477 | operator | `<` | `<=` |
| 487 | operator | `>` | `>=` |
| 487 | prog | `1` | `2` |
| 582 | operator | `<` | `<=` |
| 676 | operator | `>` | `>=` |
| 683 | prog | `0.0` | `0.001` |
| 696 | operator | `>` | `>=` |

### `tools/ci/assert_shot_metadata.py` — 6

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 84 | operator | `<=` | `<` |
| 84 | operator | `<=` | `<` |
| 183 | prog | `0.0` | `0.001` |
| 200 | prog | `0.0` | `0.001` |
| 242 | operator | `>` | `>=` |
| 242 | prog | `1e-3` | `0.00101` |

### `tools/physics/braking.py` — 5

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 163 | operator | `<=` | `<` |
| 163 | operator | `>=` | `>` |
| 165 | operator | `>` | `>=` |
| 287 | operator | `>` | `>=` |
| 287 | prog | `1.0` | `1.01` |

### `tools/physics/reference.py` — 3

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 34 | operator | `<=` | `<` |
| 45 | operator | `<` | `<=` |
| 52 | operator | `<` | `<=` |

### `tools/physics/schedule_envelope.py` — 5

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 55 | operator | `<=` | `<` |
| 57 | operator | `>=` | `>` |
| 90 | operator | `>` | `>=` |
| 100 | operator | `<=` | `<` |
| 114 | operator | `<=` | `<` |

### `tools/track/build_alignment.py` — 39

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 88 | operator | `<` | `<=` |
| 88 | operator | `>` | `>=` |
| 114 | operator | `<` | `<=` |
| 117 | operator | `<=` | `<` |
| 119 | operator | `<=` | `<` |
| 121 | operator | `<=` | `<` |
| 123 | operator | `>=` | `>` |
| 125 | operator | `>` | `>=` |
| 125 | prog | `1e-9` | `1.01e-09` |
| 142 | operator | `<=` | `<` |
| 147 | operator | `<=` | `<` |
| 147 | operator | `<=` | `<` |
| 149 | operator | `<=` | `<` |
| 225 | operator | `<` | `<=` |
| 225 | prog | `1e-9` | `1.01e-09` |
| 351 | operator | `>=` | `>` |
| 381 | operator | `==` | `!=` |
| 401 | operator | `==` | `!=` |
| 402 | operator | `==` | `!=` |
| 408 | operator | `==` | `!=` |
| 414 | operator | `<` | `<=` |
| 435 | operator | `!=` | `==` |
| 444 | operator | `!=` | `==` |
| 454 | operator | `!=` | `==` |
| 481 | operator | `==` | `!=` |
| 482 | operator | `!=` | `==` |
| 504 | operator | `>` | `>=` |
| 504 | prog | `1` | `2` |
| 546 | operator | `==` | `!=` |
| 590 | operator | `==` | `!=` |
| 590 | operator | `==` | `!=` |
| 604 | operator | `<=` | `<` |
| 646 | operator | `==` | `!=` |
| 646 | prog | `0` | `1` |
| 650 | operator | `==` | `!=` |
| 650 | prog | `0` | `1` |
| 782 | operator | `!=` | `==` |
| 788 | operator | `>` | `>=` |
| 798 | operator | `!=` | `==` |

### `tools/track/crosscheck_alignment.py` — 2

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 293 | operator | `>` | `>=` |
| 293 | operator | `<` | `<=` |

### `tools/track/crs.py` — 8

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 152 | operator | `>=` | `>` |
| 152 | prog | `0.0` | `0.001` |
| 163 | operator | `<` | `<=` |
| 172 | operator | `>` | `>=` |
| 300 | operator | `<` | `<=` |
| 300 | prog | `1e-12` | `1.01e-12` |
| 419 | operator | `<` | `<=` |
| 419 | prog | `1e-12` | `1.01e-12` |

### `tools/track/detail_layout.py` — 1

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 97 | operator | `<=` | `<` |

### `tools/track/inspire_rail.py` — 2

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 306 | operator | `<` | `<=` |
| 306 | operator | `>` | `>=` |

### `tools/track/make_test_track.py` — 2

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 19 | operator | `==` | `!=` |
| 19 | prog | `130` | `131` |

### `tools/track/shapefile.py` — 1

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 36 | operator | `<=` | `<` |

### `tools/track/station_layout.py` — 1

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 116 | operator | `<` | `<=` |

### `tools/track/surface_sections.py` — 1

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 158 | operator | `<=` | `<` |

### `tools/track/tunnel_width.py` — 2

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 199 | operator | `<` | `<=` |
| 199 | prog | `1e-9` | `1.01e-09` |

### `tools/track/validate.py` — 2

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 97 | prog | `0` | `1` |
| 97 | operator | `>=` | `>` |

### `tools/visual/framing.py` — 1

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 92 | operator | `>=` | `>` |

### `tools/visual/pngio.py` — 4

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 42 | operator | `<=` | `<` |
| 240 | prog | `0.0` | `0.001` |
| 240 | operator | `>` | `>=` |
| 240 | operator | `<` | `<=` |
