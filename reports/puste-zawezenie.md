# `--only ""` robił pełny przegląd w milczeniu (6.D37)

**Zmierzone 07.09.2026 na commicie:** `2ffb0b00cce5a66d688647ccb603c1011416aa6f`
**Dotyczy:** `tools/tests/mutation_sweep.py`, `tools/tests/test_mutation_sweep.py`
**Rodzina:** 6.B39 (pusty zbiór), 6.B41, 6.D18

## 1. Stan wyjściowy — WYKONANY

```
$ python3 tools/tests/mutation_sweep.py --only "" --list
tools/visual/pngio.py:257 argument `2` -> `3`
razem: 2346
kod: 0
```

Pusty napis jest fałszywy dla `if args.only`, więc nie wchodził **ani** filtr, **ani**
wiersz „dopasowało N plików docelowych", **ani** odmowa z 6.B39. Przebieg robił pełny
przegląd i wyglądał przy tym na zawężony — bo wołający o zawężenie prosił.

Liczbowo: **2346 mutacji zamiast 2** dla typowego triażu jednego modułu, czyli
**1173×** więcej pracy.

**Ta sama rodzina co 6.B39, odwrócona.** Tam zbiór był pusty, a przebieg wychodził
zerem, wyglądając na poprawny; tu zbiór jest pełny, a przebieg wygląda na zawężony.
W obu przypadkach robi co innego, niż czytający sądzi, i w obu milczy.

## 2. Pomiar, którego żądało pole „Wyjście" — i on rozstrzygnął na odmowę

Pole pytało, czy ma być odmowa, czy wystarczy wiersz w wypisie, i kazało to
rozstrzygnąć jednym pomiarem: **czy istnieje w drzewie choć jedno wywołanie podające
`--only` z wartością mogącą być pusta.** Odpowiedź: **dwa**, i mają RÓŻNE zachowanie.

```
reports/mutation-drift.md:455        python3 … --only "$m" --workers 4 …
reports/mutation-triage-fizyka.md:173  python3 … --only $f --workers 4 …
```

Obie to prawdziwe pętle po modułach. Zmierzone zachowanie każdej przy pustej zmiennej:

| postać | co się dzieje | kod |
|---|---|---|
| `--only "$m"` → `--only ""` | **pełny przegląd, 2346 mutacji, w milczeniu** | **0** |
| `--only $f` → argument znika | argparse **JUŻ odmawia**: `expected one argument` | **2** |

```
$ python3 tools/tests/mutation_sweep.py --only --workers 4 --list
mutation_sweep.py: error: argument --only: expected one argument
kod: 2
```

**Druga postać jest więc chroniona od zawsze, pierwsza nie była przez nic** — i to jest
cały powód, dla którego pozycja kończy się odmową, a nie wierszem w wypisie.

## 3. Poprawka i wybór kodu wyjścia

Odmowa idzie przez `parser.error()`, więc kod jest **2**, nie 1. Uzasadnienie nie jest
estetyczne: `--only ""` to **błędne wywołanie**, a nie „nie ma czego liczyć"
(`KOD_NIC_DO_LICZENIA`, gdzie zbiór jest pusty z powodu, który przebieg umie nazwać —
tam należy 6.B39 i 6.B41). Ten sam kod daje argparse dla **drugiej postaci tej samej
pomyłki**. Jedna pomyłka, jeden kod, niezależnie od tego, czy cudzysłów ocalał.

Warunek to `"--only" in sys.argv and not args.only`, a **nie** sama fałszywość
`args.only` — bo obie sytuacje dają pusty napis, a tylko jedna jest pomyłką. Przebieg
bez `--only` wcale jest normalnym wołaniem (`reports/` wywołuje go **siedem** razy) i
zostaje niezmieniony.

## 4. Stan po poprawce — WYKONANY, obie drogi

```
$ python3 tools/tests/mutation_sweep.py --only "" --list
mutation_sweep.py: error: --only '' nie jest zawężeniem: pusty wzorzec przepuszcza
WSZYSTKIE 63 plików docelowych, czyli robi pełny przegląd. Jeżeli chodziło o przebieg
bez zawężenia — nie podawaj --only wcale; jeżeli wzorzec bierze się z podstawienia
zmiennej, sprawdź, czy nie jest pusta.
kod: 2

$ python3 tools/tests/mutation_sweep.py --list          (bez --only wcale)
razem: 2346
kod: 0
```

## 5. Weryfikacja

```
$ python3 tools/tests/test_all.py; echo "kod: $?"
  1934/1934 przeszło
  RAZEM 72.786 s, 1934 testów, 101 modułów
kod: 0
```

Zestaw **1931 → 1934**, moduł `test_mutation_sweep.py` **108 → 111**.

## 6. Trzy kontrole negatywne — WYKONANE, każda na innym zbiorze

**KN-1 — odmowa zdjęta w całości:**

```
FAIL test_dwie_postacie_tej_samej_pomylki_daja_ten_sam_kod
FAIL test_only_z_pustym_wzorcem_jest_odmowa_a_nie_pelny_przeglad
  109/111 przeszło
```

**KN-2 — odmowa ZBYT SZEROKA** (warunek na samej fałszywości `args.only`, bez pytania,
czy `--only` w ogóle podano). Pada **dokładnie jeden** test i jest to ten, który
pilnuje drogi pełnego przebiegu:

```
FAIL test_przebieg_BEZ_only_zostaje_niezmieniony
  110/111 przeszło
```

To jest kontrola z pola „Skończone, gdy": bez niej odmowa zbudowana na fałszywości
przeszłaby test z KN-1 i **zablokowała każdy przebieg pełny** — czyli tę drogę, którą
`reports/` woła siedem razy.

**KN-3 — zmieniony TYLKO kod wyjścia** (2 → 1), komunikat nadal wymieniający `--only`.
Pierwsza wersja tej kontroli zmieniła przy okazji treść komunikatu i wywróciła dwa
testy, co nie izolowało kodu; powtórzona poprawnie pada na **jednym**:

```
FAIL test_dwie_postacie_tej_samej_pomylki_daja_ten_sam_kod
  110/111 przeszło
```

Plik przywrócony po każdej z trzech i sprawdzony przez `cmp`.

## 7. Czego świadomie nie zrobiłem

- **Nie ruszyłem przebiegu bez `--only`** — to normalne wołanie, i 6.B39 zostawiło je
  poza zakresem z tego samego powodu.
- **Nie poprawiłem dwóch pętli w `reports/`.** Są datowanymi pomiarami
  (`docs/04-conventions.md`), a odmowa działa niezależnie od tego, jak je zapisano —
  to zresztą jest jej sens: chroni każde przyszłe wywołanie, nie te dwa.
- **Nie zmieniłem dopasowania `--only` z podciągu na nazwę pliku** (6.D18).
- **Nie tknąłem odmów z 6.B39 i 6.B41** ani stałej `KOD_NIC_DO_LICZENIA`.

## 8. Zauważone przy okazji, nietknięte

**Bramka twierdzeń o stałych (6.D4) zapaliła się na TYM raporcie, i był to fałszywy
alarm trzeciego kształtu.** Pierwsze uruchomienie:

```
FAIL test_every_constant_quoted_in_a_report_carries_the_value_from_the_code:
raporty podają inną wartość niż kod: ['puste-zawezenie.md:135:
KOD_NIC_DO_LICZENIA mówi 6, kod 1']
```

Zdanie brzmiało „Nie tknąłem KOD_NIC_DO_LICZENIA ani odmów z 6.B39 i 6.B41" —
cytuję je **bez grawisów wokół nazwy stałej**, bo wzorzec bierze tylko nazwy
w grawisach, a cytat dosłowny zapaliłby bramkę po raz drugi: raport o fałszywym
alarmie odtworzyłby ten alarm. Zmierzone — pierwsza wersja tej sekcji cytowała
dosłownie i dostała `1933/1934 przeszło`, kod 1. Wzorzec
wziął pierwszą liczbę po nazwie stałej, a była nią **szóstka z odsyłacza `6.B39`**.
To dokładnie ta rodzina fałszywych alarmów, którą 6.D27 zamknęło dla `§` i `#`:
zwężenie zabroniło stawiać między nazwą a liczbą przecinka, strzałki, grawisu i znaku
odsyłacza — ale **numer pozycji `6.B39` nie jest żadnym z tych znaków**, więc przechodzi.

**Bramki nie tknąłem** i to jest decyzja, nie przeoczenie: `tools/tests/test_report_claims.py`
nie stoi w polu „Wejście" tej pozycji, a `CLAUDE.md` §4.10 zabrania poprawiania przy
okazji plików spoza zadania. Przestawiłem własne zdanie („Nie tknąłem odmów z 6.B39
i 6.B41 ani stałej `KOD_NIC_DO_LICZENIA`"), co usuwa alarm bez ruszania czyjejkolwiek
bramki. Samo znalezisko zostaje tu zapisane, bo trzeci kształt tego fałszywego alarmu
jest materiałem na osobną pozycję — z własnym pomiarem, ile zdań w `reports/` ma
nazwę stałej przed odsyłaczem do numeru pozycji.

**`--only` z samymi spacjami (`--only " "`) nie jest pustym napisem, więc przechodzi
przez nową odmowę** i dopasowuje zero plików, kończąc się odmową z 6.B39 — czyli
poprawnie, ale inną drogą i z innym kodem (1, nie 2). Nie tknięte: `" "` nie jest
wynikiem podstawienia pustej zmiennej, a wszystkie zmierzone postacie tej pomyłki dają
napis pusty albo brak argumentu. Zapisuję, bo trzeci wariant tej samej pomyłki
istnieje i ma trzeci kod.
