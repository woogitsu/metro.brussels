# Triaż osiągalnych mutacji z drugiej rundy ekstrakcji — trzy moduły

**Zmierzone 06.09.2026 na commicie:** `9a57130a10699d4a1362fc1cac08ed05b0ba3aa9`

Pozycja 6.B9 (#276, `reports/bpy-extraction-round-2.md`) wyciągnęła spod `bpy`
trzynaście funkcji do trzech nowych modułów (`station_sections.py`,
`marker_gates.py`, `material_specs.py`) i świadomie nie dopisała im testów —
celem było uczynić je **osiągalne** dla przeglądu mutacyjnego. Ten raport jest
tym pomiarem: ile z trzynastu funkcji naprawdę nie miało pokrycia, i ile
mutacji przeżywa dziś, po pierwszym pomiarze i po dopisanych testach.

## 0. Liczba z wiersza kolejki kontra liczba zmierzona

Wiersz `6.B14` w `docs/TASKS.md` mówi: „dziewięć funkcji w trzech nowych
modułach nie ma ani jednego testu bezpośredniego". Dosłownie to prawda —
przed tym zadaniem żaden plik w `tools/tests/` nie robił `import
station_sections`, `import marker_gates` ani `import material_specs` pod
własną nazwą. Ale „brak importu pod własną nazwą" to nie to samo, co „kod się
nigdy nie wykonuje", a to drugie jest tym, co naprawdę obchodzi przegląd
mutacyjny.

Powód: `station_kit.py` i `detail_markers.py` przypisują funkcje wyciągnięte
w #276 pod STARE nazwy —

```
straight_prism = SS.straight_prism
wall_offset_m = SS.wall_offset_m
slab_sections = SS.slab_sections
selected_platforms = SS.selected_platforms
side_tag = SS.side_tag
sweep_section = SS.sweep_section
```

— więc `SK.wall_offset_m` w `tools/tests/test_station_kit.py` i
`SS.wall_offset_m` w tym module to **dosłownie ten sam obiekt funkcji w
pamięci**. Mutacja w ciele `wall_offset_m` jest widoczna dla testu, który woła
`SK.wall_offset_m`, tak samo jak dla testu, który wołałby `SS.wall_offset_m`
wprost. To samo dotyczy `select_marks`, `side_sign`, `clearance_problems` w
`marker_gates.py`, przypisanych w `detail_markers.py`.

Zmierzone (sekcje 2–4 niżej, pełny zestaw pięciu klas): z trzynastu funkcji
**pięć** naprawdę nigdy się nie wykonuje pod dzisiejszym zestawem testów —
wszystkie cztery w `material_specs.py` (ten moduł nie ma żadnego pośredniego
mostu — `tools/tests/test_art_direction.py` czyta `material_test_scene.py`
jako tekst, nie importuje go) i `straight_prism` w `station_sections.py`
(jedyna funkcja tego modułu, której `main()` używa, ale której nie woła nic w
`tools/tests/`). Pozostałych **osiem** — `wall_offset_m`, `slab_sections`,
`selected_platforms`, `side_tag`, `sweep_section` w `station_sections.py` i
wszystkie trzy funkcje `marker_gates.py` — wykonuje się dziś w pełni, przez
alias, i mutacyjnie jest w większości już zabite (sekcje 3–4). Liczba z
wiersza kolejki i liczba zmierzona różnią się, bo mierzą dwie różne rzeczy;
tam, gdzie się rozjeżdżają, ten raport ufa pomiarowi.

## 1. Kalibracja wyroczni — rzeczywiste wyjście, dla wszystkich trzech modułów

Zanim którykolwiek wynik niżej cokolwiek znaczy, każdy z trzech przebiegów
zaczyna się drzewem BEZ mutacji, żeby upewnić się, że wyrocznia w ogóle ma
prawo mówić „zabita" (`baseline_problem`, naprawa z #268 opisana w
`reports/wyrocznia-mutacyjna-falszywe-zabicia.md`):

```
$ python3 tools/tests/mutation_sweep.py --only station_sections.py
[MUTACJE] 15 mutacji do policzenia, 3 robotników, commit 51d324a,
          klasy operator,prog,logika,argument,przypisanie
[MUTACJE] kalibracja wyroczni: zestaw w drzewie BEZ mutacji
[MUTACJE] drzewo bazowe zielone, wyrocznia ma prawo mówić „zabita”
[MUTACJE] sonda pokrycia: jeden przebieg zestawu z licznikiem wierszy
[MUTACJE] wykonywanych wierszy dotyczy 14 z 15 mutacji; pozostałe 1 siedzą
          w kodzie, którego zestaw nie uruchamia

$ python3 tools/tests/mutation_sweep.py --only marker_gates.py --no-coverage
[MUTACJE] 9 mutacji do policzenia, 3 robotników, commit 51d324a,
          klasy operator,prog,logika,argument,przypisanie
[MUTACJE] kalibracja wyroczni: zestaw w drzewie BEZ mutacji
[MUTACJE] drzewo bazowe zielone, wyrocznia ma prawo mówić „zabita”
[MUTACJE] rozstrzygniętych 9/9, zabitych 9, ocalałych 0
          (w tym 0 nieuruchomionych), nierozstrzygniętych 0

$ python3 tools/tests/mutation_sweep.py --only material_specs.py --no-coverage
[MUTACJE] 10 mutacji do policzenia, 3 robotników, commit 51d324a,
          klasy operator,prog,logika,argument,przypisanie
[MUTACJE] kalibracja wyroczni: zestaw w drzewie BEZ mutacji
[MUTACJE] drzewo bazowe zielone, wyrocznia ma prawo mówić „zabita”
[MUTACJE] rozstrzygniętych 10/10, zabitych 0, ocalałych 10
          (w tym 0 nieuruchomionych), nierozstrzygniętych 0
```

Wszystkie trzy przebiegi mierzyły **BEZ** trzech nowych plików testowych z
tego zadania — `git worktree add HEAD` (którym `mutation_sweep.py` buduje
każde drzewo robocze) bierze ostatni COMMIT, nie niezacommitowany stan
katalogu roboczego, więc dopóki te pliki nie były jeszcze wcięte, każdy z
powyższych przebiegów mierzył wyłącznie to, co dziś jest w `main`.

## 2. Zestaw klas operatorów — dwa mianowniki, jawnie

Wszystkie trzy przebiegi wyżej użyły **domyślnego, pełnego zestawu pięciu
klas**: `operator,prog,logika,argument,przypisanie`. Podzbiór odpowiadający
staremu zestawowi (`operator,prog`, sprzed 05.09.2026) jest wyliczony **z
tych samych dzienników** filtrem po polu `rodzaj` — nie osobnym przebiegiem —
bo jest ścisłym podzbiorem i osobny przebieg dałby dokładnie te same wyniki
kosztem drugiego kompletu drzew roboczych na maszynie dzielonej z równoległym
zadaniem 6.B13 (patrz §7).

| moduł | mutacji, 5 klas | z tego `operator,prog` |
|---|---:|---:|
| `station_sections.py` | 15 | 12 |
| `marker_gates.py` | 9 | 9 |
| `material_specs.py` | 10 | 7 |

Liczby w kolumnach nie są porównywalne między sobą ani z liczbami z raportów
sprzed 05.09.2026 mierzonych jeszcze innym zestawem — każda kolumna ma swój
własny mianownik i sekcje 3–5 podają werdykt osobno dla obu.

## 3. `station_sections.py` — 15 mutacji (12 w zestawie `operator,prog`)

| wiersz | rodzaj | zmiana | przed | po | werdykt |
|---|---|---|---|---|---|
| 24 | argument | `sys.path.insert(0,…)` → `insert(1,…)` | ocalała | ocalała | **równoważna** |
| 25 | argument | `sys.path.insert(0,…)` → `insert(1,…)` | ocalała | ocalała | **równoważna** |
| 59 | operator | `<` → `<=` (`straight_prism`) | ocalała | ocalała | **równoważna** |
| 96 | operator | `side > 0` → `side >= 0` | ocalała | **zabita** | zabita nowym testem |
| 96 | prog | `side > 0` → `side > 1` | zabita | zabita | — |
| 97 | operator | `outer > inner` → `>=` | zabita | zabita | — |
| 100 | operator | `outer < inner` → `<=` | zabita | zabita | — |
| 121 | operator | `p["name"] == only_station` → `!=` | zabita | zabita | — |
| 133 | operator | `side > 0` → `>=` (`side_tag`) | zabita | zabita | — |
| 133 | prog | `side > 0` → `side > 1` (`side_tag`) | zabita | zabita | — |
| 135 | operator | `side < 0` → `<=` (`side_tag`) | zabita | zabita | — |
| 135 | prog | `side < 0` → `side < 1` (`side_tag`) | zabita | zabita | — |
| 143 | operator | `cursor < to_m - 1e-9` → `<=` | zabita | zabita | — |
| 145 | przypisanie | `cursor += step_m` → `cursor = step_m` | **nierozstrzygnięta** | nierozstrzygnięta | patrz §3d |
| 152 | operator | `<` → `<=` (`sweep_section`) | ocalała | ocalała | **równoważna** |

**9 zabitych, 5 ocalałych (przed), 1 nierozstrzygnięta.** Po dopisaniu jednego
testu: **10 zabitych, 4 ocalałe (wszystkie cztery — dowiedzione równoważne),
1 wciąż nierozstrzygnięta.**

### 3a. Jedyna prawdziwa dziura: `side > 0` przy `side == 0.0` dokładnie

Wszystkie istniejące wywołania `slab_sections` w `tools/tests/test_station_kit.py`
podają `side` równe `1.0` albo `-1.0` — nigdy zero. Funkcja sama nie odmawia
zera (w przeciwieństwie do `side_tag`, które robi to wprost), więc `side > 0`
naprawdę rozstrzyga o gałęzi także w tym punkcie, a żaden test go nie dotykał.

`tools/tests/test_station_sections.py::test_slab_sections_at_side_zero_takes_the_negative_branch_without_raising`
woła `slab_sections(0.5, 0.5, 10.0, 1.0, 1.0, 0.0)` i sprawdza, że wraca
poprawny przekrój bez wyjątku. Sprawdzone bezpośrednim wstawieniem mutanta
(kopia pliku z `if side > 0:` zamienionym na `if side >= 0:`, bez przechodzenia
przez `mutation_sweep.py`, żeby nie płacić drugiego pełnego przebiegu na
maszynie dzielonej z 6.B13):

```
$ python3 -c "
import sys; sys.path.insert(0,'tools/blender'); sys.path.insert(0,'tools/track')
import station_sections as SS
SS.slab_sections(0.5, 0.5, 10.0, 1.0, 1.0, 0.0)"
CAUGHT: AssertionError (1.0, 0.0)
```

Oryginał (`side > 0`, czyli `0.0 > 0.0` fałsz) idzie w gałąź `else` i zwraca
poprawny przekrój po stronie ujemnej. Mutant (`side >= 0`, czyli `0.0 >= 0.0`
prawda) idzie w gałąź `if` i tam `assert outer > inner` — `0.0 > 1.0` —
podnosi `AssertionError`. Test w `test_station_sections.py` sprawdza wprost,
że to NIE się dzieje na oryginale; na mutancie zestaw by padł.

### 3b. Cztery równoważne — dowód, nie deklaracja

**Wiersze 24 i 25** (`sys.path.insert(0, X)` → `insert(1, X)`, dwukrotnie, dla
`HERE` i dla katalogu `tools/track`). Kolejność między tymi dwoma wpisami a
tym, co było na `sys.path[0]` wcześniej, mogłaby coś zmienić WYŁĄCZNIE gdyby
istniał moduł o tej samej nazwie w obu miejscach na ścieżce. Sprawdzone
wyliczeniem, nie przypuszczeniem:

```
$ ls tools/track/*.py tools/blender/*.py | xargs -n1 basename | sort | uniq -d
(pusto)
```

Żadna nazwa pliku nie powtarza się między `tools/track/` a `tools/blender/`,
a to jedyne dwa katalogi, które te dwa wiersze dokładają. Bez kolizji nazwy
modułu żadne z kolejnych `import placement`, `import profiles`, `import
sweep` w tym samym pliku nie może rozstrzygnąć się inaczej zależnie od tego,
czy wstawka wylądowała na pozycji 0 czy 1.

**Wiersze 59 i 152** — ten sam wzorzec w dwóch miejscach:
```python
forward = SW.unit(SW.sub(points[min(index + 1, len(points) - 1)], points[index])) \
    if index + 1 < len(points) else (1.0, 0.0, 0.0)
```
`tools/tests/test_station_kit.py::test_sweep_forward_fallback_branch_is_dead_not_untested`
(istniejący test, nie ruszony w tym zadaniu) dowodzi za pomocą 24 000 wywołań
`placement.frame_at` na 6000 losowych osiach, że `index + 1 < len(points)`
jest ZAWSZE prawdziwe — `frame_at` przycina `index` do `len - 2`. Gałąź
`else` jest martwa w OBU miejscach, bo obie wołają ten sam `PL.frame_at`;
dowód nie jest specyficzny dla `sweep_section`, więc obejmuje `straight_prism`
bez potrzeby powtarzania pomiaru. Różnica `wykonana` między wierszem 59
(`false` — `straight_prism` nie miał żadnego wywołania przed tym zadaniem) a
152 (`true` — `sweep_section` jest wołany bez przerwy) nie zmienia werdyktu:
gałąź `else` nie wykonuje się w żadnym z dwóch miejsc, więc `<` → `<=` nie ma
czego zaobserwować.

### 3c. `straight_prism` dostał bezpośredni test, mimo że jego jedyna mutacja jest równoważna

`tools/tests/test_station_sections.py` dodaje trzy testy `straight_prism`
(dwa pierścienie we właściwych miejscach, domknięcie dwoma denkami,
zdegenerowana bryła przy `length_m=0`) — nie dlatego, że zabijają mutację 59
(nie zabijają, bo jest równoważna, §3b), tylko dlatego, że funkcja miała
ZERO wywołań w całym `tools/tests/` przed tym zadaniem, a `main()` jej używa.

### 3d. Wiersz 145 — nierozstrzygnięta, nie zabita i nie ocalała

Ten wiersz nigdy nie doszedł do pomiaru przez `mutation_sweep.py`: przebieg
z pełną sondą pokrycia trafił w zewnętrzny limit czasu narzędzia (1100 s)
zanim worker doszedł do tej jednej mutacji na 15 — zmierzone 14 z 15,
dziennik JSONL ma czternaście wpisów, piętnasty brakuje (patrz `[MUTACJE]…`
w §1 — sonda pokrycia zdążyła policzyć wszystkie 15 linii jako „wykonywane
14 z 15", ale sam przebieg mutacji padł na czasie przed policzeniem tej
jednej). To jest stan **nierozstrzygnięty**, nie „zabita" i nie „ocalała" —
zapisanie go jako którekolwiek z tych dwóch byłoby dokładnie tym
przemilczeniem, przez które wyrocznia kłamała przed #268.

Zamiast płacić drugi pełny przebieg narzędzia na maszynie dzielonej z 6.B13
wyłącznie dla jednej mutacji, sprawdziłem RĘCZNIE, bezpośrednim wykonaniem
(nie przez `mutation_sweep.py`), co by się stało:

```python
def sweep_section_mutant(...):
    ring_at = []
    cursor = from_m
    while cursor < to_m - 1e-9:
        ring_at.append(cursor)
        cursor = step_m          # mutowane: += -> =
        if len(ring_at) > 100000:
            raise RuntimeError("WOULD HANG: infinite loop confirmed")
    ...
```
Wywołane z dokładnie tymi parametrami, których `tools/tests/test_station_kit.py`
(`test_sweep_places_a_ring_at_both_ends_of_the_platform`) już używa —
`from_m=0.0, to_m=100.0, step_m=25.0` — wynik:
```
CONFIRMED HANG: WOULD HANG: infinite loop confirmed
```
`cursor` przestaje rosnąć (zostaje stałe `25.0`), warunek pętli `25.0 <
100.0 - 1e-9` jest wieczną prawdą. Pod prawdziwym `mutation_sweep.py`
oznaczałoby to `subprocess.run(..., timeout=300)` kończący się
`TimeoutExpired` w `run_suite`, czyli werdykt narzędzia **„nierozstrzygnięta"**
— nie „zabita" (bo zestaw nigdy nie doszedł do podsumowania) i nie „ocalała"
(bo to nie jest cichy sukces testów, tylko zawieszenie). Zapisuję to tutaj
jako nierozstrzygnięte i podpieram dowodem wykonania, zamiast zgadywać
etykietę — dokładnie to, o co proszą reguły tego zadania.

## 4. `marker_gates.py` — 9 mutacji, wszystkie zabite JUŻ PRZED tym zadaniem

Zaskoczenie tego pomiaru: pierwsze podejrzenie (próg `clearance_problems`
między `0.0` a `0.001` nietknięty żadnym testem) było **błędne**. Pomiar,
zrobiony PRZED dopisaniem czegokolwiek do `tools/tests/`, pokazuje 9 zabitych
na 9 — zero ocalałych, zero nierozstrzygniętych (§1).

Powód: `tools/tests/test_detail_markers.py::test_zero_clearance_is_still_allowed_but_a_hair_below_is_not`
zaczyna się od `DM.clearance_problems(0.0, 0.0, "box_double") == []` — punkt
DOKŁADNIE na granicy. Mutacja stałej `0.0` → `0.001` w `worst_gauge_m < 0.0`
przesuwa próg tak, że `0.0 < 0.001` jest PRAWDĄ — funkcja zgłasza problem
tam, gdzie test oczekuje pustej listy, i to konkretne porównanie pada. Nie
potrzeba wartości pośredniej między `0.0` a `0.001`, żeby to złapać: sam
punkt graniczny już wystarcza, bo mutacja przesuwa granicę TAK, że włącza
w nią ten punkt.

Ten moduł nie dostaje więc żadnej nowej mutacji do zabicia. Dodany
`tools/tests/test_marker_gates.py` (trzy testy) nie zamyka dziury — importuje
moduł PO WŁASNEJ NAZWIE (`import marker_gates as MG`) zamiast wyłącznie przez
alias w `detail_markers.py`, i sprawdza wprost (`DM.select_marks is
MG.select_marks` itd.), że alias naprawdę wskazuje na te same obiekty — czyli
że argument z §0 („to jest ten sam obiekt funkcji") jest dowiedziony, nie
tylko czytany ze źródła.

## 5. `material_specs.py` — 10 mutacji, wszystkie ocalałe przed tym zadaniem, 9 zabitych po

Ten moduł nie ma ŻADNEGO mostu: cztery funkcje siedziały wewnątrz
`material_test_scene.py`, obok `import bpy`, a jedyny istniejący test tamtego
pliku (`tools/tests/test_art_direction.py`) czyta go jako TEKST (`open(GENERATOR
).read()`), nie importuje. Stąd 10/10 ocalałych w §1 — zgodne z oczekiwaniem,
nie niespodzianka.

`tools/tests/test_material_specs.py` (16 testów) dodaje bezpośrednie pokrycie
wszystkich czterech funkcji. Sprawdzone wstawieniem każdej z dziesięciu
mutacji z osobna do kopii modułu i uruchomieniem tego zestawu testów na niej
(metoda jak w §3a — bezpośrednie wykonanie, nie przez `mutation_sweep.py`,
z tego samego powodu oszczędności czasu na maszynie dzielonej):

| wiersz | rodzaj | zmiana | po nowych testach |
|---|---|---|---|
| 33 | logika | `or` → `and` (`artefact_is_missing`) | zabita |
| 33 | operator | `<=` → `<` (próg rozmiaru pliku) | zabita |
| 43 | argument | `.get("alpha", 1.0)` → domyślne `1.01` | **równoważna** |
| 43 | operator | `< 1.0` → `<= 1.0` (`is_transparent`) | zabita |
| 43 | prog | `< 1.0` → `< 1.01` | zabita |
| 54 | operator | `==` → `!=` (`is_glass`) | zabita |
| 67 | operator | `!=` → `==` (trigger duplikatów) | zabita |
| 68 | prog | `count(i) > 1` → `> 2` | zabita |
| 68 | operator | `count(i) > 1` → `>= 1` | zabita |
| 68 | logika | `and i` → `or i` | zabita |

**9 z 10 zabitych.** Jedyna ocalała — argument domyślny `.get("alpha", 1.0)`
→ `1.01` — jest **równoważna**, i to jest sprawdzalne bez reszty kodu:
domyślna wartość wchodzi do porównania `< 1.0` WYŁĄCZNIE gdy klucza `alpha`
nie ma, a `1.0 < 1.0` i `1.01 < 1.0` dają dokładnie to samo — `False`. Zanim
zapisałem ten werdykt, spróbowałem obu granic (`{}`, brakujący klucz, wartość
dokładnie progowa) — żadna nie odróżnia domyślnej `1.0` od `1.01`, bo obie
nie są mniejsze niż próg porównania. Różnica ujawniłaby się dopiero, gdyby
razem z tym zmienił się też próg porównania (`43 prog`) — a to już osobna,
zabita mutacja.

## 6. Podsumowanie liczb

| moduł | zabitych przed | ocalałych przed | nierozstrzygniętych przed | zabitych po | ocalałych po (równoważne) | nierozstrzygniętych po |
|---|---:|---:|---:|---:|---:|---:|
| `station_sections.py` (15) | 9 | 5 | 1 | 10 | 4 | 1 |
| `marker_gates.py` (9) | 9 | 0 | 0 | 9 | 0 | 0 |
| `material_specs.py` (10) | 0 | 10 | 0 | 9 | 1 | 0 |
| **razem (34)** | **18** | **15** | **1** | **28** | **5** | **1** |

W zestawie `operator,prog` (12 + 9 + 7 = 28 mutacji, §2) mianownik jest inny,
bo wiersz 145 (klasa `przypisanie`) w ogóle do niego nie należy — więc
„nierozstrzygnięta" z tabeli wyżej znika z tego zestawienia, nie zmienia
werdyktu:

| stan | przed | po |
|---|---:|---:|
| zabita | 18 | 26 |
| ocalała (równoważna) | 10 | 2 |
| nierozstrzygnięta | 0 | 0 |
| **razem** | **28** | **28** |

Dziesięć ocalałych „przed" w tym zestawie to: 59, 96-operator, 152 (wszystkie
trzy ze `station_sections.py`) plus siedem z `material_specs.py` (cała jego
podlista klasy `operator`/`prog`, bo przed tym zadaniem moduł nie miał ani
jednego testu). Po dopisaniu testów zostają dwie — 59 i 152, obie dowiedzione
równoważne w §3b.

## 7. Czego świadomie nie zrobiłem i dlaczego

- **Nie przepuściłem §3a i §5 przez `mutation_sweep.py` po dopisaniu testów.**
  Maszyna jest dzielona z równolegle działającym zadaniem 6.B13, które w tym
  samym oknie czasowym uruchamiało własne przebiegi `mutation_sweep.py`
  (widoczne w `ps aux` jako procesy w `wt-b13` i w jego własnych katalogach
  roboczych `/tmp/metro-mutacje-*`). Pierwszy pełny przebieg z sondą pokrycia
  na `station_sections.py` przekroczył zewnętrzny limit 1100 s i został
  zabity, mimo że dziennik JSONL (zapisywany przyrostowo, `fsync` po każdym
  wpisie) zdążył złapać 14 z 15 wyników. Dla pozostałych dwóch modułów
  przełączyłem się na `--no-coverage`, co skróciło przebieg z ponad
  osiemnastu minut do niecałych dziesięciu. Zamiast płacić kolejny pełny
  przebieg (rzędu kilkunastu minut na tej maszynie) wyłącznie po to, żeby
  potwierdzić DWIE konkretne, już ręcznie sprawdzone zmiany (§3a, §5),
  zweryfikowałem je bezpośrednim wykonaniem zmutowanego kodu — pokazane w
  obu sekcjach, z komendami i wynikiem.
- **Wiersz 145 zostaje nierozstrzygnięty**, nie „zabity naprawą" — patrz §3d.
  Nie jest to zmiana zachowania (poza zakresem zadania), tylko rzetelne
  nazwanie stanu, do którego przebieg realnie doszedł.
- **Nie ruszyłem `profile_vehicle.py` ani `tunnel_sweep.py`** — jawnie poza
  zakresem, zajmuje się nimi równolegle 6.B13.
- **Nie zmieniłem zachowania żadnego z trzech modułów.** Wszystkie nowe testy
  opisują kod, jaki jest dziś; żaden test nie ujawnił błędu wartego zgłoszenia
  właścicielowi.
- **Nie dopisywałem do `test_station_kit.py` ani `test_detail_markers.py`.**
  Trzy nowe pliki są nowe, po jednym na moduł, zgodnie z zadaniem.

## 8. Co zauważyłem przy okazji, ale nie tknąłem

- `mutation_sweep.py --journal` domyślnie pisze do WSPÓLNEJ ścieżki
  `tempfile.gettempdir()/metro-mutacje.jsonl` — na maszynie, na której w tej
  samej sesji działał równolegle inny agent (6.B13) uruchamiający ten sam
  skrypt, dwa niezależne przebiegi bez jawnego `--journal` dopisywałyby do
  TEGO SAMEGO pliku i mieszałyby swoje wyniki. Obszedłem to własnym
  `--journal` w `scratchpad/`, ale narzędzie samo tego nie sygnalizuje — nie
  jest to bug tej pozycji, tylko obserwacja dla właściciela.
- Klasyfikacja mutacji „równoważna" w tym module jest w trzech na pięć
  przypadków (24, 25, 59/152) tego samego rodzaju: kod bootstrapujący albo
  gałąź, której wejście danych nigdy nie osiąga — nie arytmetyka progowa, jak
  w poprzednich rundach (`reports/mutation-triage-sweep.md`,
  `reports/mutation-triage-m7-report.md`). Może to być wzorzec wart
  sprawdzenia w kolejnych rundach ekstrakcji: moduły powstałe z wycięcia
  funkcji spod `bpy` dziedziczą też martwe gałęzie oryginału.

## 9. Weryfikacja — rzeczywiste wyjście

```
$ python3 tools/tests/test_all.py 2>&1 | tail -5
  ok   test_every_summary_is_closed_in_its_own_block
  ok   test_no_member_carries_two_summary_blocks
  ok   test_xml_doc_scan_actually_reads_the_sources

  1661/1661 przeszło
```

Sprawdzone przez brak linii `^\s*FAIL`, nie przez obecność słowa „przeszło":

```
WYNIK=$(python3 tools/tests/test_all.py 2>&1)
echo "$WYNIK" | grep -qE "^\s*FAIL" && echo CZERWONE || echo ZIELONE
ZIELONE
```

1638 testów sprzed tej pozycji + 23 nowe (16 w `test_material_specs.py`,
4 w `test_station_sections.py`, 3 w `test_marker_gates.py`) = 1661.
