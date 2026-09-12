# 6.D172 — obrona przed cudzym dziennikiem objęła przebiegi kolejne, a nie równoległe

**12.09.2026**, na `113b4a8`. Wejście: `tools/tests/test_mutation_sweep.py`,
log joba `tunnel-alignment (L1_B)` z PR #553. Pozycja wyszła z czerwonego CI
na cudzym PR-ze — moim własnym — a nie z kolejki.

## 1. Jak się znalazła

`tunnel-alignment (L1_B)` w PR #553 padł:

```
FAIL test_only_bez_trafien_z_lista_nie_konczy_sie_zerem:
[MUTACJE] PRZERWANE — dziennik /tmp/metro-mutacje-6b39-nieistniejacy.jsonl trzyma inny przebieg.
```

Diff tamtego PR-a obejmował `docs/TASKS.md`, jeden raport i trzy moduły testowe —
`test_mutation_sweep.py` nie był wśród nich i nic z tamtej zmiany tego testu nie
wykonuje.

## 2. Odmowa zadziałała poprawnie; wadliwa była nazwa

Komunikat pochodzi z mechanizmu odcisku treści wprowadzonego w 6.B32: dziennik
niesie odcisk przebiegu, a przebieg o innym odcisku odmawia zamiast dopisać się do
cudzego pliku. **To jest zachowanie żądane i ono zadziałało.**

Obronę, którą stałe nazwy miały dać, opisuje docstring `_sweep_cli` — i opisuje ją
trafnie:

> Dziennik na sciezke, ktorej nie ma: przebieg z domyslnym dziennikiem czytalby plik
> zostawiony przez czyjs poprzedni pomiar i moglby na nim odmowic (6.B19), czyli test
> padalby od stanu maszyny, nie od kodu.

Rozumowanie jest poprawne co do joty. Objęło jednak wyłącznie przebiegi **kolejne** —
„czyjś **poprzedni** pomiar". Przebieg **równoległy** nie mieści się w tym zdaniu,
a od 02.09.2026 całe CI chodzi na jednym runnerze właściciela (`CLAUDE.md` §9), więc
joby dzielą `/tmp`.

## 3. Czasy jobów: nakładały się prawie w całości

```
tunnel-alignment (L1_A)  10:50:55Z -> 10:56:56Z  success
tunnel-alignment (L1_B)  10:50:56Z -> 10:57:06Z  failure
material-style           10:50:55Z -> 10:52:10Z  success
```

Macierz startuje trzy joby w odstępie sekundy i wykonuje je obok siebie przez sześć
minut, na tej samej maszynie.

## 4. Odtworzone celowo — i pierwsza próba NIE odtworzyła

To jest tu najważniejsze, bo zmienia treść diagnozy.

**Próba pierwsza** — dwa równoległe przebiegi całego modułu, identyczne:

```
kod przebiegu A: 0   kod przebiegu B: 0
  132/132 przeszło
  132/132 przeszło
```

Nic nie padło. Gdybym na tym poprzestał, zapisałbym „nie odtworzyłem". A wynik jest
**poprawny i wymagany**: ta sama treść daje ten sam odcisk, więc dzienniki są zgodne —
tego właśnie żąda `test_ta_sama_tresc_trafia_w_ten_sam_dziennik`.

**Próba druga** — dwa równoległe przebiegi o **różnej** treści, jedna ścieżka:

```
ITERACJA 5 — ODTWORZONE: [MUTACJE] PRZERWANE — dziennik … trzyma inny przebieg.
ITERACJA 6 — ODTWORZONE: [MUTACJE] PRZERWANE — dziennik … trzyma inny przebieg.
odtworzen: 6 z 6
```

**Sześć na sześć.** Warunkiem nie jest więc pech co do milisekundy, tylko dwa
równoległe procesy o różnej treści przebiegu — a moduł woła `_sweep_6b39`
**dziewięć razy** z różnymi argumentami, wszystkie w jeden plik. Wystarczy, żeby
wywołania dwóch jobów się przepletły.

**To poprawia zdanie, które sam napisałem w komentarzu na PR #553.** Stało tam, że
awaria „zależy od nałożenia się czasów" — brzmi jak rzadki zbieg okoliczności.
Zmierzone jest inaczej: przy nakładających się jobach kolizja jest **regułą**, a nie
wyjątkiem, a zielone przebiegi wcześniejszych PR-ów brały się stąd, że wywołania nie
trafiły w siebie. Zielone ponowienie na #553 też niczego nie dowiodło — job chodził
wtedy sam, więc brak kolizji był zgodny z każdą hipotezą.

## 5. Poprawka

Pięć miejsc (wiersze 328, 348, 364, 2045, 2733 sprzed zmiany) dostaje ścieżkę
z `_dziennik_testu`, która dokłada `os.getpid()`.

**PID, a nie licznik ani znacznik czasu**, i to jest wybór: nazwa ma być **stała
w obrębie procesu** — inaczej wznowienie w obrębie jednego testu zgubiłoby plik,
a `test_ta_sama_tresc_trafia_w_ten_sam_dziennik` opisuje dokładnie tę własność —
i **różna między procesami**, bo dwa joby na jednej maszynie to dwa procesy.

## 6. Kontrole

| kontrola | wynik |
|---|---|
| dwa równoległe moduły, treść ta sama, PO poprawce | **132/132 i 132/132**, osobne pliki (`…-785.jsonl`, `…-786.jsonl`) |
| dwa równoległe przebiegi, treść RÓŻNA, PRZED poprawką | **6 odmów na 6** |
| dwa równoległe przebiegi, treść RÓŻNA, PO poprawce | **0 odmów na 6** |

Pierwsza z nich **nie jest kontrolą rozstrzygającą i jest to tu napisane wprost**:
ta konfiguracja przechodziła także przed poprawką. Rozstrzyga dopiero para druga
i trzecia — ta sama pętla, ta sama różnica treści, jedyna zmiana to ścieżka.

## 7. Czego nie zrobiłem

- **Nie tknąłem mechanizmu odmowy.** Działa i ma działać; 6.B32 i 6.B40 zostają.
- **Nie sprzątam dzienników po przebiegu.** Pliki `/tmp/metro-mutacje-*-<pid>.jsonl`
  zostają tam, gdzie zostawały dotąd. Sprzątanie to osobna decyzja — a na trwałym
  runnerze wymaga rozstrzygnięcia, kto i kiedy je usuwa, żeby nie skasować cudzego
  przebiegu w locie. Zapisane, nie zrobione po cichu.
- **Nie szukałem innych stałych ścieżek w `/tmp`** poza tym modułem. Ten sam kształt
  może być gdzie indziej; to pomiar na inną pozycję.
