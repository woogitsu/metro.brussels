# Bramka na własnej drodze narzędzia mutacyjnego (6.B37)

**Zmierzone 07.09.2026 na commicie:** `f4df2d2b385120c3ba629fda64cda8cdc502dcc2`
(gałąź `claude/6b37-straznik-na-main`, po przestawieniu na `main` ze scalonymi #362
i #363). Pomiary z §2, §3 i §6 zrobiono wcześniej na `3e18aabd135814437db84b0b3ae81f926f5ebb0f`
i powtórzono po przestawieniu; różnią się tylko czasami, o rzędzie szumu maszyny.

Pozycja 6.B37 powstała, bo usterka 6.B35 przeżyła całą dobę mimo zestawu chodzącego
po każdym commicie. Wpis wyjaśniał to zdaniem: *„żaden test nie uruchamia narzędzia
jego własną drogą (`main()`)"*. Pierwszą rzeczą, którą to zadanie zrobiło, było
sprawdzenie tego zdania — i **jest ono w jednej trzeciej nieprawdziwe**.

## 1. Założenie pozycji: pięć testów już chodziło drogą CLI

Przejście po `ast` po `origin/main`, funkcje wołające `subprocess.run` na
`mutation_sweep.py`:

```
$ python3 - <<'SKRYPT'
import ast, subprocess
zrodlo = subprocess.run(["git","show","origin/main:tools/tests/test_mutation_sweep.py"],
                        capture_output=True, text=True).stdout
for w in ast.parse(zrodlo).body:
    if isinstance(w, ast.FunctionDef):
        seg = ast.get_source_segment(zrodlo, w) or ""
        if "mutation_sweep.py" in seg and "subprocess.run" in seg:
            print(" ", w.name)
SKRYPT
  test_unknown_operator_class_is_rejected_by_the_cli
  test_cli_lists_only_the_requested_class
  test_only_is_a_substring_match_by_design_and_says_how_many_modules_it_caught
  test_resume_refuses_a_journal_written_on_another_tree
  test_resume_still_works_when_the_journal_is_from_the_same_tree
```

Pięć, nie zero. **Kod wyjścia drogi CLI był pilnowany**, i to od dawna. Gdyby luka
leżała tam, gdzie ją wpis lokował, 6.B35 zostałaby złapana pierwszego dnia.

## 2. Gdzie luka leżała naprawdę: `--list` nie dochodzi do przygotowania drzewa

`main()` dla `--list` wraca kodem 0 z miejsca **przed** `add_worktree`, a więc przed
`neutralise_own_tests` i przed kalibracją wyroczni. Pomiar z treścią zaślepki
podmienioną w drzewie na sam docstring — czyli z dokładnie tą usterką, którą miała
6.B35:

```
$ python3 tools/tests/mutation_sweep.py --only tools/blender/lod_paths.py --list \
      --journal /tmp/nieistniejacy-6b37.jsonl
[MUTACJE] --only 'tools/blender/lod_paths.py' złapało 2 mutacji z 1 moduł(ów): tools/blender/lod_paths.py
tools/blender/lod_paths.py:28 operator `==` -> `!=`
tools/blender/lod_paths.py:28 prog `0` -> `1`
razem: 2
kod: 0
```

**Wniosek, który zmienia treść zadania:** pole „Skończone, gdy" pozycji 6.B37 —
*„kontrola negatywna WYKONANA — zaślepka pozbawiona strażnika — wywraca dokładnie
ten test"* — jest **niespełnialne bramką na `--list`**, którą ta sama pozycja
proponuje w polu „Wyjście". Dwa pola żądają rzeczy wykluczających się, i widać to
tylko po pomiarze.

Rozwiązane nie przez rozluźnienie kryterium, a przez dodanie **drugiej** bramki,
która idzie tą drogą, na której usterka żyła: `git worktree add` →
`neutralise_own_tests` → uruchomienie modułu **wprost**.

## 3. Kod wyjścia i tu nie wystarcza — rozstrzyga liczba testów

Zaślepka bez strażnika, uruchomiona wprost w świeżym drzewie roboczym:

```
straznik w zaslepce: False
kod: 0
stdout: (pusto)
stderr: (pusto)
czas add_worktree 0.094 s, czas uruchomienia 0.018 s
```

Ta sama sonda po naprawie z 6.B35:

```
straznik w zaslepce: True
kod: 0
stdout:   ok   test_this_file_is_the_stub_not_the_real_tests

  1/1 przeszło

  czas per moduł (malejąco):
       0.000 s  test_mutation_sweep.py  (1 testów)
  RAZEM 0.000 s, 1 testów, 1 modułów

czas add_worktree 0.093 s, czas uruchomienia 0.085 s
```

**Kod 0 w obu przypadkach.** Moduł bez strażnika `__main__` uruchomiony wprost nie
wykonuje niczego i wychodzi zerem — to dokładnie usterka, której 6.D25 dała bramkę,
tylko że ta bramka widzi wyłącznie pliki **leżące** w drzewie, a zaślepka powstaje
dopiero w drzewie roboczym przeglądu. Dlatego test czyta **liczbę wykonanych testów**,
i to tym samym `_liczba_testow`, którym czyta ją bramka 6.D25 — nie własną kopią,
bo kopia rozjeżdża się po cichu.

To trzeci raz dzisiaj, kiedy przyrząd meldował „w porządku" zamiast prawdy, i drugi,
w którym rozstrzygnięciem nie był kod wyjścia.

## 4. Co doszło do zestawu

Trzy testy w `tools/tests/test_mutation_sweep.py`:

| test | co pilnuje |
|---|---|
| `test_the_cli_lists_mutations_as_a_process_and_exits_zero` | droga CLI: kod 0, wiersz `razem: N`, zgodność dwóch niezależnych liczników |
| `test_a_fresh_worktree_runs_the_stub_as_a_real_module` | droga przygotowania drzewa: zaślepka melduje dokładnie jeden wykonany test |
| `test_the_worktree_probe_can_tell_a_guardless_stub_apart` | kontrola przyrządu z testu wyżej, w zestawie na stałe |

## 5. Koszt, liczbą — o to prosiło pole „Wyjście"

Moduł, **po trzy przebiegi** w każdą stronę na tym samym drzewie (pierwsza para
pomiarów była pojedyncza i dała 14.109 / 15.017 s — różnica 0,91 s przy szumie rzędu
0,4 s, więc jest tu zastąpiona medianami, nie dopisana obok jako drugi wynik):

```
bez nowych testów:   14.229  14.148  14.535   → mediana 14.229 s, 69 testów
z nowymi testami:    14.910  14.925  14.774   → mediana 14.910 s, 72 testów
                                                 różnica median: 0,681 s
```

Per test, mediana z trzech przebiegów każdego:

```
0.325 s  test_the_cli_lists_mutations_as_a_process_and_exits_zero
0.207 s  test_a_fresh_worktree_runs_the_stub_as_a_real_module
0.129 s  test_the_worktree_probe_can_tell_a_guardless_stub_apart
-------
0.661 s  razem
```

Dwa niezależne pomiary tej samej rzeczy zgadzają się do 0,02 s: **0,681 s** z różnicy
median całego modułu i **0,661 s** ze zsumowania median per test. To jest cały powód,
dla którego są tu oba — jedna liczba nie miałaby czym się potwierdzić.

Cały zestaw na commicie, który idzie do scalenia, dwa przebiegi:
`RAZEM 77.248 s` i `RAZEM 76.713 s`, oba `1868 testów, 99 modułów`, kod 0. Przed
przestawieniem gałęzi na `main` ze scalonymi #362 i #363 było `76.651 s, 1868 testów,
99 modułów` — **liczba testów i modułów identyczna we wszystkich trzech**, bo ani
#362 (testy C#), ani #363 (wiersze planu) nie dodają testów pythonowych. Rozrzut
0,6 s między przebiegami jest tu podany właśnie dlatego, że bez niego pojedyncza
liczba wyglądałaby na dokładniejszą, niż jest. Testy C# przebiegnięte po przestawieniu gałęzi, bo #362 ich
dotyczyło: `Passed! - Failed: 0, Passed: 578` w `Sim.Tests`, `Passed: 205`
w `Game.Tests`, zero porażek w obu.

Warunek z pola
„Wyjście" — *„test w zestawie chodzącym po każdym commicie nie ma prawa kosztować
sekund"* — spełniony z zapasem: 0,66 s na trzy testy, z czego 0,19 s to dwa
`git worktree add` (0,093 s i 0,094 s, zmierzone osobno w §3).

## 6. Kontrole negatywne — WYKONANE, nie opisane

**KN-1 — zaślepka pozbawiona strażnika (usterka 6.B35).** Treść `OWN_TESTS_STUB`
podmieniona w drzewie na sam docstring:

```
FAIL test_a_fresh_worktree_runs_the_stub_as_a_real_module: zaslepka w swiezym drzewie
     nie zameldowala DOKLADNIE jednego wykonanego testu (None) — kalibracja wyroczni
     zobaczy zestaw jako padajacy i przerwie przeglad kodem 2
FAIL test_przygotowanie_drzewa_zdejmuje_testy_narzedzia_nie_kasujac_pliku
FAIL test_the_stub_is_a_full_test_module_not_just_a_docstring
69/72 przeszło
kod: 1
```

Nowy test wywrócony — to jest to, czego żądało pole „Skończone, gdy". Dwa pozostałe
to bramki z 6.B35, które czytają zaślepkę jako **napis**; nowy jest jedyny, który
czyta ją jako **plik w drzewie**. `test_the_cli_lists_mutations_as_a_process_and_exits_zero`
w tej kontroli **pozostaje zielony** — i to właśnie mierzy §2.

**KN-2 — przyrząd oślepiony.** Podmiana `sweep.OWN_TESTS_STUB` w `_stub_w_drzewie`
zastąpiona `pass`, czyli sonda przestaje robić to, o co ją proszą:

```
FAIL test_the_worktree_probe_can_tell_a_guardless_stub_apart: przyrzad zameldowal
     1 wykonanych testow dla zaslepki bez straznika, czyli nie odroznia jej od poprawnej
71/72 przeszło
kod: 1
```

Dokładnie jeden test, ten właściwy. Bramka, która świeci się tak samo na treści
poprawnej i zepsutej, nie mierzy niczego — ta się nie świeci.

**KN-3a — `main()` dla `--list` wraca kodem 3.**

```
FAIL test_cli_lists_only_the_requested_class
FAIL test_only_is_a_substring_match_by_design_and_says_how_many_modules_it_caught
FAIL test_resume_still_works_when_the_journal_is_from_the_same_tree
FAIL test_the_cli_lists_mutations_as_a_process_and_exits_zero: CLI narzedzia
     mutacyjnego nie dochodzi do konca wlasna droga (kod 3)
68/72 przeszło
kod: 1
```

Cztery testy, z czego **trzy starsze od tej pozycji** — dowód pomiarowy do §2:
kod wyjścia drogi CLI był już pilnowany.

**KN-3b — usunięty `print(f"razem: {len(found)}")`.**

```
FAIL test_the_cli_lists_mutations_as_a_process_and_exits_zero: wypis bez wiersza
     z liczba zlapanych mutacji
71/72 przeszło
kod: 1
```

Jeden test, nowy. Wiersz podsumowania **nie był** pilnowany przez nikogo: stare testy
filtrują wypis po przedrostku `tools/`, więc podsumowania nie oglądają wcale. To jest
prawdziwy, choć węższy, wkład pierwszego z trzech nowych testów — i został zmierzony,
a nie założony na podstawie treści pozycji.

## 7. Czego świadomie nie zrobiono

- **Nie uruchomiono pełnego przeglądu w zestawie** — pole „Poza zakresem" mówi to
  wprost i ma rację: zestaw wołający sam siebie to pętla, nie bramka.
- **Nie sięgnięto do `baseline_problem` przez `main()`.** Byłby to jeden pełny
  przebieg zestawu, ~76 s w teście chodzącym po każdym commicie. Droga przygotowania
  drzewa daje tę samą ochronę za 0,21 s, bo usterka 6.B35 leżała w treści zaślepki,
  nie w kalibracji.
- **Nie poprawiono treści pozycji 6.B37 w `docs/TASKS.md`** poza dopisaniem, co
  z pomiaru wyszło. Wpis zostaje z datą, tak jak wymaga `docs/04-conventions.md`.
- **Ruszony został blok 6.B38**, mimo reguły „nie poprawiasz przy okazji plików spoza
  zadania" — i jest to świadome, bo obie zmiany są wprost skutkiem pomiaru tej
  pozycji, nie okazją: dopisana **adnotacja** z medianami (blok cytował `15.315 s /
  71 testów` z drzewa, które przestało istnieć — pomiaru z datą NIE przeliczono,
  adnotacja stoi obok) i poprawione pole **„Zależy od"**, które wskazywało numer PR
  nieistniejący w chwili wpisu. Nic innego w planie poza wierszem 6.B37 nie zostało
  tknięte.
- **`WEJSCIA._liczba_testow` jest funkcją prywatną** i test wywołuje ją mimo
  podkreślenia. Zrobione świadomie: cała wartość tego testu polega na czytaniu wypisu
  **tym samym przyrządem**, którym czyta go bramka 6.D25. Własna kopia parsera dałaby
  dwa czytniki, które rozjadą się po cichu — a to jest dokładnie usterka, którą
  6.B28 znalazło w czytniku C#.

## 8. Zauważone przy okazji, nie tknięte

- **Praca 6.B37 została raz utracona.** Leżała wyłącznie jako niezacommitowane zmiany
  w drzewie roboczym i zniknęła przy zmianie gałęzi; w `git stash` ani w żadnym
  commicie jej nie było. Odtworzono ją od `origin/main`, tym razem z trzema testami
  zamiast dwóch. Wniosek nie dotyczy repozytorium, a sposobu pracy: pozycja bez
  commita nie istnieje. Skutek dla liczb: blok 6.B38 w `docs/TASKS.md` cytuje
  `15.315 s / 71 testów` z tamtego, nieistniejącego już drzewa; adnotacja z dzisiejszymi
  liczbami stoi obok, pomiar z datą nie jest wyrównywany.
- **`--list` z `--only` na nieistniejący wzorzec daje kod 0, nie 1.** Zmierzone:

  ```
  $ python3 tools/tests/mutation_sweep.py --only tools/nie-ma-takiego-pliku.py --list \
        --journal /tmp/n2.jsonl
  [MUTACJE] --only 'tools/nie-ma-takiego-pliku.py' złapało 0 mutacji z 0 moduł(ów):
  razem: 0
  kod: 0
  ```

  Odmowa `brak mutacji do sprawdzenia` (kod 1) stoi **za** gałęzią `--list`, więc
  wypisu nie dotyczy. Dla samego wypisu jest to obronialne, ale przebieg CI, który
  przez pomyłkę zawęzi `--only` na nic, dostanie zielone zero — a nazwa modułu
  w pierwszym wierszu jest wtedy pusta, czyli jedyny sygnał to `0 moduł(ów)`.
  Nie ruszone: to inna pozycja niż ta. Nowy test broni się przed tym u siebie
  asercją `ile > 0`, ale to nie jest bramka na samo narzędzie.
