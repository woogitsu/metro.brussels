# 6.D114 — drugi argument, o którym zestaw milczał

**Zmierzone 11.09.2026 na:** `c00ebc8`, kontener tej sesji.
**Przyrząd:** `tools/tests/test_all.py` (`_sciezki_do_przebiegu`, `_discover`,
gałąź `__main__`), `tools/tests/test_module_entrypoints.py` — moduły piaskownicy
powstają w katalogu tymczasowym pod `tools/tests/`, drzewo nietknięte.

---

## 1. Usterka, zmierzona tak, jak się o niej dowiedziałem

Gałąź `__main__` kończyła się na `main(sys.argv[1])`. Wywołanie z czterema modułami
dawało wynik **pierwszego** i kod **zero** — czyli wynik, który *wygląda* jak wynik
tego, o co się prosiło. Nie znalazłem tego czytaniem kodu: przy 6.D101 wywołałem
zestaw z czterema modułami i wziąłem liczbę jednego za liczbę czterech.

To ta sama rodzina co usterka zamknięta przez 6.D25 — pusty przebieg kończący się
zerem — tylko w drugą stronę: tam cicho przechodził **brak** testów, tu cicho znika
**część** żądania.

## 2. Rozstrzygnięcie: uruchamiamy wszystkie, nie odmawiamy

Pole „Wyjście" dopuszcza oba, więc powód jest częścią wyniku.

Uruchomienie wielu modułów **nie jest nową zdolnością** tego pliku: przebieg bez
argumentu robi dokładnie to samo dla 120 modułów i idzie tą samą drogą — licznik
asercji, werdykt, kod wyjścia. Odmowa zostawiałaby więc bez odpowiedzi wywołanie,
które narzędzie umie obsłużyć, a które człowiek pisze odruchowo po pierwszej
czerwonej bramce. Cena jest zerowa: `_sciezki_do_przebiegu` zamienia jedną ścieżkę
na listę ścieżek, `_discover` chodzi po niej pętlą, która już tam była.

**Wyjątkiem jest powtórzenie: ten sam moduł dwa razy jest ODMOWĄ.** Nie z czystości:
policzyłby swoje testy dwa razy, a `N/M przeszło` jest liczbą, którą
`mutation_sweep.run_suite` czyta jako werdykt. Zawyżony mianownik jest błędem tego
samego rodzaju co ciche pominięcie argumentu i tak samo nie zostawia śladu.

## 3. Zachowanie po zmianie, cztery wywołania

```
[test_bytecode_staleness.py]                                  kod=0  RAZEM 7 testów, 1 modułów
[test_bytecode_staleness.py test_module_entrypoints.py]       kod=0  RAZEM 13 testów, 2 modułów
[test_bytecode_staleness.py test_bytecode_staleness.py]       kod=1  ValueError: modul podany dwa razy
[test_bytecode_staleness.py test_nie_ma_takiego.py]           kod=1  ValueError: nie ma takiego modulu testowego
```

## 4. Pomiar idzie po LICZBIE TESTÓW, nie po kodzie wyjścia

To jest treść, nie szczegół. Oba poprawne wywołania kończą się **zerem**, bo oba
moduły przechodzą — kod wyjścia nie odróżniłby cichego pominięcia od poprawnego
przebiegu i dlatego nie jest tu wyrocznią. Rozróżnia je dopiero mianownik: **2**
wobec **5** na module piaskownicy z dwoma i trzema testami.

Odmowa ma z kolei kod niezerowy i to ją odróżnia — więc obie połowy bramki mierzą
tym przyrządem, który w ich przypadku coś mówi.

## 5. Odmowa nie może zależeć od POZYCJI argumentu

Literówka w **drugiej** nazwie musi być odmową tak samo jak w pierwszej — inaczej
wystarczyłoby sprawdzać `argv[1]` i ciche pominięcie wróciłoby tylnymi drzwiami.
Osobny test, bo to osobna droga przez kod.

**Ten test złapał usterkę w samym sobie.** Pierwsza wersja podawała jako pierwszy
argument `test_module_entrypoints.py`, czyli **ten plik**. Przy działającym kodzie
odmowa przychodzi przed uruchomieniem czegokolwiek i było szybko — ale pod kontrolą
negatywną KN-1 zamieniało się to w uruchomienie tego pliku w podprocesie, który
uruchamia kolejne podprocesy. Kontrola nie skończyła się w 120 s i została przerwana
ręcznie. Dziś pierwszym argumentem jest moduł piaskownicy; ta sama rekursja jest
opisana w komentarzu przy teście o liczbie testów i dotyczy tego samego pliku.

## 6. Kontrole negatywne

`__pycache__` czyszczony przed każdym przebiegiem, po każdej `md5sum -c` na dwóch
plikach.

| # | co zepsute | wynik |
|---|---|---|
| KN-1 | gałąź `__main__` bierze znów jeden argument | **6/9, trzy testy** |
| KN-2 | powtórzony moduł przestaje być odmową | 8/9 |
| KN-3 | czytnik bierze tylko pierwszą nazwę z listy | **6/9, trzy testy** |

KN-1 i KN-3 dają ten sam obraz i to jest oczekiwane: obie zostawiają dokładnie to
zachowanie, które ta pozycja usuwa — wynik pierwszego modułu pod pytaniem o kilka.
Różnią się miejscem, w którym argument ginie (wiersz poleceń wobec czytnika), i to
jest powód, dla którego obie stoją tu osobno.

## 7. Weryfikacja

```
$ python3 tools/tests/test_all.py test_module_entrypoints.py
  9/9 przeszło          (było 6)

$ python3 tools/tests/test_all.py
  2254/2254 przeszło, 120 modułów
```

## 8. Czego nie zrobiłem

- **Nie dodałem żadnej opcji wiersza poleceń** (`--only`, `-k` i podobnych) ani nie
  zmieniałem sposobu liczenia testów — pole „Poza zakresem" wyklucza oba wprost.
- **Nie ruszyłem `main(only=...)` w roli, w jakiej wołają je `mutation_sweep.py`
  i `test_assertion_gate.py`**: pierwsze woła podproces bez argumentów, drugie
  `main()` wprost, a strażniki modułów podają jedną ścieżkę. Wszystkie trzy kształty
  dalej działają, bo `only` przyjmuje napis tak samo jak przedtem.
- **Nie zmieniłem tego, co widać przy odmowie**: leci `ValueError` z traceback'iem,
  tak samo jak przy nieznanym module od 6.D25. Ładniejszy komunikat byłby zmianą
  zachowania, o którą ta pozycja nie prosi.

## 9. Zauważone przy okazji

- **Kolejność modułów w wypisie jest kolejnością argumentów, a nie alfabetyczną.**
  Przy przebiegu całego zestawu porządek daje `AG.paths()`; przy wyborze ręcznym —
  człowiek. Nic tego nie pilnuje i nic nie musi, ale tabela czasów per moduł jest
  wtedy posortowana malejąco po czasie i te dwa porządki łatwo pomylić.
- **`_only_path` przyjmuje ścieżkę do dowolnego pliku `test_*.py`, także spoza
  `tools/tests/`** — tak wchodzą moduły piaskownicy. Przy liście argumentów znaczy
  to, że da się zmieszać moduły zestawu z modułami z katalogu tymczasowego; tak
  właśnie robią testy tej pozycji, więc jest to zdolność używana, nie tylko możliwa.
