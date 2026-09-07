# Wpis dziennika mutacyjnego nie wiedział, z jakiego drzewa pochodzi (6.B19)

**Zmierzone 07.09.2026 na commicie:** `7bf5062`
(gałąź `claude/6b19-dziennik-mutacji`).

**Adnotacja z tego samego dnia:** gałąź została po pomiarze przestawiona na `f259d5d`
(scalenie #347 — 6.A14, nowy moduł bramki i osiem testów C#). Zestaw narzędzi
przebiegł na nowej podstawie ponownie i dał **ten sam werdykt** oraz tę samą deltę
trzech testów: **1836 → 1839** testów w **98** modułach, kod wyjścia 0. Liczby z dnia
pomiaru (1828 → 1831) nie są przeliczane; ta adnotacja mówi, co powtórzono i z jakim
wynikiem.

## 1. Co było zepsute

Pozycja znaleziona przy 6.B17 (#289) i tam świadomie nietknięta — pole „Poza zakresem"
tamtej pozycji mówiło wprost: dotyczy **ścieżki** dziennika, nie tego, co się w nim
zapisuje.

Wpis powstający w `check_one` niósł `id`, `plik`, `wiersz`, `rodzaj`, `bylo`, `jest`
i wynik — **ale nie commit**. Identyfikatorem mutacji jest `plik:wiersz:przesunięcie
bajtowe` (`Mutation.id`), więc dwie różne mutacje z dwóch różnych drzew mogły mieć
**ten sam identyfikator**, jeśli przesunięcie wypadło tak samo. Miejsce wznawiania
w `main` dopasowywało wyłącznie po tym identyfikatorze:

```python
seen = {entry["id"] for entry in done}
found = [m for m in found if m.id not in seen]
```

Docstring przy tym miejscu twierdził, że „zmiana kodu między przebiegami nie przemyci
starego wyniku pod nową mutację" — i było to prawdą **tylko wtedy**, gdy zmiana
przesuwała offsety. Poprawka z #289 (`default_journal`) tego nie dotykała: ona pilnuje,
żeby dziennik nie mieszał **modułów** (przez hash commita w NAZWIE domyślnego pliku),
a nie żeby nie mieszał **drzew** wewnątrz dziennika podanego ręcznie przez `--journal`.
Kto poda własny `--journal` — a CLI to wprost dopuszcza — dostaje dziennik, którego
wpisy same w sobie nie niosą dowodu, na jakim kodzie powstały.

## 2. Poprawka

1. `check_one` przyjmuje teraz `commit` i zapisuje je w każdym wpisie, obok `id`
   (`tools/tests/mutation_sweep.py`, funkcja `check_one`). `worker` i `sweep` przekazują
   ten parametr dalej; `main` przekazuje commit policzony na starcie przebiegu
   (`git rev-parse --short HEAD`), ten sam, którego nazwa już używa `default_journal`.
2. `main` odmawia wznowienia, gdy dziennik niesie choć jeden wpis o **innym** commicie
   niż przebieg bieżący — kodem wyjścia 2, przed dotknięciem jakiejkolwiek mutacji.
   Wpis bez pola `commit` (dziennik sprzed tej poprawki) liczy się jako obcy z tego
   samego powodu, dla którego wpis bez pola `plik` liczy się jako obcy w istniejącej
   kontroli: nie da się go zweryfikować, a milcząca zgoda wpuściłaby cudzy wynik pod
   dzisiejszą mutację.
3. Kryterium „obcy plik" (#289) zostaje **osobnym, wcześniejszym** sprawdzeniem —
   commit i plik to dwa różne pytania i mieszanie ich w jeden warunek ukryłoby, który
   z dwóch powodów odmówił.

## 3. Kontrole negatywne — wykonane

### 3.1 Dziennik z innego drzewa — odmowa, kod wyjścia 2

Prawdziwy pokaz CLI (nie test jednostkowy): dziennik z wpisem opisującym commit
`deadbee`, uruchomiony na drzewie, którego HEAD to `7bf5062`:

```
$ python3 tools/tests/mutation_sweep.py --only tools/blender/lod_paths.py \
      --journal /tmp/b19-demo/dziennik.jsonl --list
[MUTACJE] --only 'tools/blender/lod_paths.py' złapało 2 mutacji z 1 moduł(ów): tools/blender/lod_paths.py
[MUTACJE] PRZERWANE — dziennik /tmp/b19-demo/dziennik.jsonl niesie 1 wpisów z innego drzewa: commit deadbee, a ten przebieg liczy na '7bf5062'.
  Identyfikator mutacji (plik:wiersz:przesunięcie bajtowe) nie niesie commita, więc wznowienie mogłoby po cichu podstawić wynik zapisany dla innego kodu pod dzisiejszą mutację.
  Podaj własny --journal na inną ścieżkę albo skasuj tamten plik.
KOD WYJSCIA: 2
```

Narzędzie **odmawia**, zamiast policzyć cudzy wynik jako swój.

### 3.2 Dziennik z TEGO SAMEGO drzewa — wznowienie działa

Kontrola pozytywna, obowiązkowa: bez niej odmowa mogłaby po prostu odrzucać wszystko
i przeszłaby 3.1 równie łatwo. Dziennik z **prawdziwym** identyfikatorem jednej
z dwóch mutacji modułu (`tools/blender/lod_paths.py:28:1362`, `operator`) i commitem
`7bf5062` — tym samym, co HEAD:

```
$ python3 tools/tests/mutation_sweep.py --only tools/blender/lod_paths.py \
      --journal /tmp/b19-demo/dziennik-swoj-prawdziwy-id.jsonl --list
[MUTACJE] --only 'tools/blender/lod_paths.py' złapało 2 mutacji z 1 moduł(ów): tools/blender/lod_paths.py
[MUTACJE] wznowienie z /tmp/b19-demo/dziennik-swoj-prawdziwy-id.jsonl: 1 z 2 już policzonych
tools/blender/lod_paths.py:28 prog `0` -> `1`
razem: 1
KOD WYJSCIA: 0
```

Wznowienie znalazło swój wpis (`operator`, już policzony) i zostawiło do sprawdzenia
tylko drugą mutację (`prog`) — dokładnie tak, jak przed tą poprawką, dla dziennika
z tego samego drzewa.

### 3.3 Mutacja A — wyłączona odmowa łapie dokładnie jeden test

Odmowa z `main` (blok `inny_commit`) zamieniona chwilowo na `inny_commit = []`:

```
  FAIL test_resume_refuses_a_journal_written_on_another_tree: ("[MUTACJE] --only 'tools/blender/lod_paths.py' złapało 2 mutacji z 1 moduł(ów): tools/blender/lod_paths.py\n[MUTACJE] wznowienie z /tmp/tmp1vtr6av_/dziennik.jsonl: 0 z 2 już policzonych\ntools/blender/lod_paths.py:28 operator `==` -> `!=`\ntools/blender/lod_paths.py:28 prog `0` -> `1`\nrazem: 2\n", '')
  67/68 przeszło
```

Drzewo przywrócone (`git diff` puste wobec pliku sprzed mutacji), zestaw z powrotem
zielony: **68/68 przeszło**.

### 3.4 Mutacja B — zdjęte pole `commit` z `check_one` łapie dokładnie jeden test

```
  FAIL test_check_one_records_the_commit_it_ran_on: 'commit'
  67/68 przeszło
```

Drzewo przywrócone, zestaw z powrotem zielony: **68/68 przeszło**.

## 4. Testy

Trzy nowe w `tools/tests/test_mutation_sweep.py`:

- `test_check_one_records_the_commit_it_ran_on` — wpis niesie `commit`, obok `id`.
- `test_resume_refuses_a_journal_written_on_another_tree` — pokaz z sekcji 3.1,
  odtworzony jako automatyczny test (kod wyjścia 2, komunikat o innym drzewie).
- `test_resume_still_works_when_the_journal_is_from_the_same_tree` — kontrola
  pozytywna z sekcji 3.2 (kod wyjścia 0, wznowienie działa).

Zestaw narzędzi: **1828 → 1831** (`python3 tools/tests/test_all.py`, ostatnie dwa
wiersze):

```
       0.000 s  test_lod_paths.py  (5 testów)
  RAZEM 69.517 s, 1831 testów, 97 modułów
```

Kod wyjścia: `0`. Linia podsumowania: `1831/1831 przeszło`.

## 5. Poza zakresem — świadomie

- **Sam identyfikator mutacji** (`plik:wiersz:przesunięcie bajtowe`) zostaje bez
  zmian. Zmiana na coś innego przeliczyłaby wszystkie dotychczasowe dzienniki
  i zerwałaby porównywalność z raportami triażu — te są datowanymi pomiarami
  i się ich nie przelicza (`reports/mutation-drift.md`).
- **Domyślna ścieżka dziennika** (`default_journal`) zostaje bez zmian — zrobiona
  w #289 (6.B17), hashuje commit razem z klasami i `--only` w NAZWIE pliku.
- **Drzewo robocze zmienione MIĘDZY przebiegami na TYM SAMYM commicie** (`--dirty`,
  ta sama wartość `git rev-parse --short HEAD`, inna zawartość mutowanego pliku)
  nie jest tu złapane — commit się nie zmienia, więc odmowa go nie widzi. Zostawiłem
  to nazwane w komentarzu przy miejscu wznawiania w `main`, bo dowiązanie identyfikatora
  do treści pliku (nie tylko do commita) byłoby już zmianą schematu identyfikatora —
  a to jest punkt wyżej, poza zakresem tej pozycji.

## 6. Zauważone przy okazji, nietknięte

- `dirty_sources` (strażnik brudnego drzewa) chroni przed dokładnie tym przypadkiem
  z punktu 5 ostatniego — ale tylko wtedy, gdy plik jest brudny WZGLĘDEM `HEAD`
  w chwili URUCHOMIENIA, nie względem stanu, w którym powstał stary wpis dziennika.
  Dwa kolejne przebiegi z `--dirty` na tym samym commicie, każdy z inną zawartością
  pliku, nie zostawiają śladu, po którym dałoby się je odróżnić po fakcie.
