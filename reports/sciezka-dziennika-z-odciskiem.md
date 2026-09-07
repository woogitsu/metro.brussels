# Nazwa dziennika obiecywała trzy rzeczy, a rozstrzygały cztery (6.B40)

**Zmierzone 07.09.2026 na commicie:** `96dc2fe9e424c669a9e607ae5029bc1c21877150`
**Dotyczy:** `tools/tests/mutation_sweep.py`, `tools/tests/test_mutation_sweep.py`
**Poprzedni etap:** 6.B32 (`reports/odcisk-tresci-dziennika.md`), 6.B19, 6.B41

## 1. Co było nie tak — i czym to NIE było

6.B32 dołożyło odcisk treści do **wpisu** dziennika, i odmowa od tamtej pory działa:
cudza treść nie wchodzi do wyniku. Nazwa **pliku** została jednak funkcją trzech
rzeczy — commita, klas operatorów i `--only` — więc dwa przebiegi na tym samym
commicie i różnej treści **dzieliły ścieżkę**:

```
czyste: /tmp/metro-mutacje-58804969c2a4.jsonl
brudne: /tmp/metro-mutacje-58804969c2a4.jsonl     <- ta sama nazwa
odcisk: 4e495be9c4159f96                          <- inna tresc
```

Skutek: przebieg `--dirty` na tym samym commicie kończył się **odmową zamiast
pomiaru** i wymagał podania `--journal` ręcznie. Docstring `default_journal`
obiecywał przy tym „trzy rzeczy, które rozstrzygają, CZEGO przebieg dotyczy", a
rozstrzygały już cztery — i to ta rozbieżność między obietnicą funkcji a jej
działaniem była właściwą treścią pozycji. **Odmowa z 6.B32 nie jest tu usterką i
zostaje niezależnie od nazwy** (pole „Poza zakresem").

## 2. Poprawka

Czwarty składnik znacznika: **odcisk całego przebiegu**, złożony z odcisków jego
plików przez nową funkcję `odcisk_przebiegu`. Osobną funkcję, nie wyrażenie w
`default_journal`, bo tej wartości pyta się dwóch rozmówców — nazwa dziennika (ta
pozycja) i nagłówek raportu (6.B42, jeszcze otwarta) — a dwa niezależne składania tej
samej listy rozjechałyby się po cichu. Ta sama zasada, dla której
`przyczyna_pustego_zbioru` jest jedna (6.B28, 6.B41).

Przebieg pusty ma odcisk **pusty**, nie `sha256("")`: zbiór bez plików nie ma czego
odróżniać, a odcisk pustego napisu byłby wartością, która **wyglądałaby jak
zmierzona**.

## 3. Dwie treści, dwie ścieżki — WYKONANE

```
=== A: drzewo czyste ===
odcisk pliku : fcb923b7000e0dca
odcisk przeb.: ebd663d489861bb7
dziennik     : /tmp/metro-mutacje-98217a984dee.jsonl

=== B: jeden znak zmieniony, BEZ commita ===
odcisk pliku : 4657e1519785c683
odcisk przeb.: 98fd780b4b9ae798
dziennik     : /tmp/metro-mutacje-7c3dae20e6b2.jsonl
```

Ten sam commit, to samo `--only`, te same klasy — **różne ścieżki**.

## 4. Wznowienie na treści niezmienionej nadal trafia w ten sam plik — WYKONANE

To jest połowa, którą poprawka musiała zachować, i pole „Wyjście" żądało sprawdzenia
dokładnie tego. Dwa pełne przebiegi pod rząd, bez zmiany treści:

```
=== przebieg 1 ===
[MUTACJE] 2 mutacji do policzenia, 2 robotników, commit 96dc2fe, klasy …,
          dziennik /tmp/metro-mutacje-98217a984dee.jsonl
[MUTACJE] rozstrzygniętych 2/2, zabitych 2, ocalałych 0 …
kod: 0

=== przebieg 2 ===
[MUTACJE] wznowienie z /tmp/metro-mutacje-98217a984dee.jsonl: 2 z 2 już policzonych
brak mutacji do sprawdzenia: wznowienie z /tmp/metro-mutacje-98217a984dee.jsonl
zastało wszystkie 2 już policzone — przebieg zrobił wszystko, o co go proszono
kod: 0
```

Ta sama nazwa w obu, wznowienie znalazło komplet, kod 0 — drogą, którą dołożyło 6.B41.

## 5. Ile dzienników zostaje w `/tmp` — liczba, o którą pytało pole „Wyjście"

Pole ostrzegało: „nazwa zmieniająca się przy każdym zapisie pliku zamienia wznowienie
w fikcję". Zmierzone: **jeden dziennik na każdy zapisany stan pliku**.

```
=== piec kolejnych zapisow pliku, sciezka domyslna po kazdym ===
  zapis 1: /tmp/metro-mutacje-bfdfe33c8336.jsonl
  zapis 2: /tmp/metro-mutacje-a2b3a628417e.jsonl
  zapis 3: /tmp/metro-mutacje-0b12176a5ca8.jsonl
  zapis 4: /tmp/metro-mutacje-4747e122589b.jsonl
  zapis 5: /tmp/metro-mutacje-9baa38a0faf2.jsonl
```

Rozmiar: dziennik dwóch mutacji ma **1074 B na 2 wpisy**, czyli **537 B na wpis**.
Dla największego realnego zawężenia (`--only tools/track/`, **782** mutacje — liczba
zmierzona przy 6.B39) daje to **około 420 kB** na dziennik; liczba wyprowadzona
z rozmiaru wpisu, nie z wykonanego przebiegu 782 mutacji, i jest tu tak oznaczona.

**Ostrzeżenie z pola okazuje się jednak nietrafione, i to jest wynik pomiaru, nie
opinia.** Wznowienie *w obrębie jednej treści* jest nietknięte (§4). Wznowienie
*przez* zmianę treści nie działało **już przed tą poprawką** — 6.B32 je odmawiało.
Poprawka zamienia więc odmowę na świeży dziennik; nie zabiera ani jednego wznowienia,
które wcześniej działało. Sprzątanie `/tmp` jest poza zakresem (pole „Poza zakresem").

## 6. Weryfikacja

```
$ python3 tools/tests/test_all.py; echo "kod: $?"
  1922/1922 przeszło
  RAZEM 73.850 s, 1922 testów, 101 modułów
kod: 0
```

Zestaw **1918 → 1922**, moduł `test_mutation_sweep.py` **95 → 99**.

## 7. Kontrole negatywne — i druga z nich znalazła usterkę w MOIM teście

**KN-1 — odcisk zdjęty ze znacznika nazwy:**

```
FAIL test_dwie_tresci_na_tym_samym_commicie_maja_rozne_dzienniki:
     /tmp/metro-mutacje-368a67c1b685.jsonl
  98/99 przeszło
```

**KN-2 — odcisk przebiegu liczony z samych WARTOŚCI, bez nazw plików. Przeszła
99/99.** Mój test tego nie łapał:

```
  99/99 przeszło          <- kontrola NIE zapalila bramki
```

Powód jest arytmetyczny. Test porównywał `{x: aaaa, y: bbbb}` z `{x: aaaa, y: cccc}`,
a te dwa różnią się także **multizbiorem wartości** — więc odcisk bez nazw plików też
je odróżniał. Asercja była prawdziwa i **nie rozstrzygająca**: dokładnie ta klasa
usterki, którą ta sesja tropiła cały dzień (6.A32, 6.A29, 6.A25, 6.A26, 6.A27).

Do złapania tej mutacji potrzebne są dwa słowniki o **tym samym** multizbiorze
wartości i innym przypisaniu do nazw. Po wzmocnieniu:

```
FAIL test_odcisk_przebiegu_sklada_PARY_a_nie_kolejnosc_i_nie_same_wartosci:
     ('803a4bf7e15a83e1', '803a4bf7e15a83e1')
  98/99 przeszło
```

Komunikat pokazuje dwa **identyczne** odciski — czyli własność, której stary test nie
mierzył wcale.

**KN-3 — pusty przebieg dostaje `sha256("")` zamiast odcisku pustego:**

```
FAIL test_pusty_przebieg_ma_odcisk_PUSTY_a_nie_odcisk_pustego_napisu:
  98/99 przeszło
```

Plik przywrócony po każdej z trzech i sprawdzony przez `cmp`.

## 8. Czego świadomie nie zrobiłem

- **Sprzątania starych dzienników z `/tmp` i zmiany katalogu** — pole „Poza zakresem".
  §5 podaje liczbę, żeby decyzja o sprzątaniu miała na czym stanąć.
- **Odmowy z 6.B32 nie tknąłem.** Działa i zostaje niezależnie od nazwy; nazwa ma
  sprawić, żeby nie musiała się odzywać przy pracy na brudnym drzewie.
- **Nie ruszyłem nagłówka raportu przeglądu** — to 6.B42, i `odcisk_przebiegu` jest
  tam gotowe do wzięcia. Nie wołam go stamtąd w tym commicie: byłoby to wykonanie
  cudzej pozycji przy okazji (`CLAUDE.md` §4.10).

## 9. Zauważone przy okazji, nietknięte

- **`ODCISK_ZNAKOW = 16` obowiązuje odcisk pliku, a znacznik nazwy ma 12** — dwie
  różne długości, obie wpisane osobno, żadna nie liczona z drugiej. Dziś bez skutku,
  bo znacznik jest skrótem z konkatenacji, nie z odcisku. Nie tknięte: byłaby to
  zmiana nazw wszystkich dzienników, czyli koszt bez zmierzonej korzyści.
- **Pozycja 6.B42 zakłada, że nagłówek raportu ma dostać „jeden odcisk całego
  przebiegu albo tabelę plik → odcisk", i pyta pomiarem, ile modułów ma typowy
  przebieg.** Po tym commicie pierwsza z tych dróg jest już policzona
  (`odcisk_przebiegu`), więc tamten pomiar dotyczy wyłącznie wyboru postaci, nie
  tego, czy da się ją policzyć.
