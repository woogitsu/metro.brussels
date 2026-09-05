# Triaż `tools/track/make_test_track.py` — pozycja 6.B8 była już zrobiona (5.8)

**Zmierzone 05.09.2026 na commicie:** `ec926a2`

Pozycja 6.B8 kolejki brzmi: „Triaż 2 ocalałych mutacji `tools/track/make_test_track.py`
— pierwszy wiersz tabeli «Kolejność triażu — po udziale» w `reports/mutation-sweep.md`,
udział 100 % (2 / 2)". Wziąłem ją do zrobienia i **pierwszy pomiar obalił jej założenie**:
ocalałych nie ma ani jednej.

Ten raport nie dokłada testów. Zapisuje pomiar, wskazuje, gdzie praca została wykonana,
i porządkuje dwa wpisy kolejki, które opisują stan sprzed tamtej pracy.

## 1. Pomiar — dwa przebiegi, żeby odróżnić dwie możliwe przyczyny

Zerowy wynik mógł pochodzić z dwóch źródeł: z **testów**, które w międzyczasie
dopisano, albo z **rozszerzenia zestawu operatorów** (#258 rozbiło dwie klasy na pięć,
więc mianownik przestał być porównywalny z raportem). Rozstrzyga to przebieg na
**starym** zestawie klas, czyli dokładnie tym, na którym powstał wiersz 2 / 2:

```
$ python3 tools/tests/mutation_sweep.py --only make_test_track.py --workers 2 \
      --operators operator,prog --journal build/mtt-stary-zestaw.jsonl \
      --json build/mtt-stary-zestaw.json
[MUTACJE] 2 mutacji do policzenia, 2 robotników, commit ec926a2, klasy operator,prog
[MUTACJE] wykonywanych wierszy dotyczy 2 z 2 mutacji; pozostałe 0 siedzą w kodzie,
          którego zestaw nie uruchamia
[MUTACJE] rozstrzygniętych 2/2, zabitych 2, ocalałych 0
```

Te same dwie mutacje, ten sam mianownik, wynik odwrotny. Przyczyną są więc **testy**,
a nie zmiana narzędzia pomiarowego.

Dla kompletu, na dzisiejszym pełnym zestawie pięciu klas:

```
$ python3 tools/tests/mutation_sweep.py --only make_test_track.py --workers 2
[MUTACJE] 13 mutacji do policzenia, klasy operator,prog,logika,argument,przypisanie
[MUTACJE] rozstrzygniętych 13/13, zabitych 13, ocalałych 0
```

## 2. Kto je zabija — z nazwy, nie z domysłu

`build/mtt-stary-zestaw.json` podaje przy każdej mutacji listę testów, które przy niej
padły:

| mutacja | ile testów padło | testy, które ją zabijają |
|---|---:|---|
| `make_test_track.py:19` `operator ==` → `!=` | 5 | `..._broken_axis_differs_from_the_good_one_at_exactly_two_points`, `..._broken_axis_is_rejected_for_the_reasons_it_was_built_for`, `..._dip_is_one_point_at_a_known_chainage_and_depth`, `..._stations_are_untouched_by_the_two_defects` |
| `make_test_track.py:19` `prog 130` → `131` | 4 | trzy pierwsze z powyższych |

Obie mutacje siedzą w tym samym wierszu 19 (`if broken and i == 130`) i obie zabija ta
sama para twierdzeń: **ile** punktów różni się między osią dobrą a zepsutą (dokładnie
dwa: 130 i 200) oraz **który** punkt jest zapadnięty i na jakim kilometrażu
(130, czyli 1040,0 m, głębokość −30,0 m).

## 3. Gdzie ta praca została wykonana

Commit **`f5126a3`**, „Testy jednostkowe dla dwóch modułów `tools/` pokrytych dotąd
tylko integracyjnie" — czyli **pozycja 5.8**, nie 6.B8. Jego wiadomość wymienia ten
moduł z tą samą liczbą, którą nosi wiersz 6.B8:

```
  tools/track/make_test_track.py   2 mutacje,  2 ocalałe  (100 %)
  tools/track/crs.py              14 mutacji,  8 ocalałych ( 57 %)
```

i opisuje dokładnie tę wyrocznię, której brakowało: „wyrocznią był walidator,
a `len(r.err) >= 3` przechodziło także wtedy, gdy `--broken` zapada 259 punktów zamiast
jednego albo zapada punkt 131 zamiast 130".

Innymi słowy: 5.8 i 6.B8 opisywały **tę samą pracę z dwóch stron** — 5.8 od strony
„moduł bez testu jednostkowego", 6.B8 od strony „moduł z ocalałymi mutacjami" — i jedno
wykonanie zamknęło obie. Żadna z nich nie została po tym zdjęta z kolejki.

## 4. Czego ten raport NIE robi

- **Nie dokłada testów.** Moduł ma je od `f5126a3`, a dopisanie drugiego kompletu do
  martwych już mutacji byłoby pracą wymyśloną na miejscu (`CLAUDE.md` §8).
- **Nie przepisuje `reports/mutation-sweep.md`.** Tamten raport jest datowanym pomiarem
  z `66b8301` i wiersz 2 / 2 był wtedy prawdą. Datowanego pomiaru się nie przelicza —
  ta zasada jest zapisana w `tools/tests/test_report_hygiene.py` i obowiązuje także
  wtedy, gdy nowy wynik jest przyjemniejszy.
- **Nie rozstrzyga o `crs.py`.** Ten sam commit wziął cztery z ośmiu jego ocalałych;
  pozostałe są przedmiotem 6.D5 („audyt dryfu pokrycia mutacyjnego po triażu"),
  a nie tej pozycji.

## 5. Co z tego wynika dla kolejki

- **6.B8 zostaje w tabeli z adnotacją**, tak jak 6.D6 i 6.B10: jest jedną z dwunastu
  pozycji z kompletem sześciu pól, a `MINIMUM_DOCUMENTED_ITEMS` wolno tylko podnosić,
  więc zdjęcie jej zbiłoby zapadkę.
- **5.8 wędruje do tabeli „Domknięte i zdjęte z kolejki"** — nie ma bloku sześciu pól,
  więc nie liczy się do zapadki, a jej miejsce po wykonaniu jest właśnie tam.

## 6. Weryfikacja — rzeczywiste wyjście

```
$ python3 tools/tests/test_all.py
  1596/1596 przeszło
```

Zestaw nie zmienia się ani o jeden test, i tak ma być: ta pozycja kończy się pomiarem
i porządkiem w planie, a nie kodem.
