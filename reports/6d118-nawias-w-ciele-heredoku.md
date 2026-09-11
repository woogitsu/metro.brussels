# 6.D118 — nawias ostrokątny w ciele heredoku: co da się odróżnić, a co nie

**Zmierzone 11.09.2026 na:** `5aed94b`, kontener tej sesji.
**Przyrząd:** `tools/tests/backlog_commands.py` (`PLACEHOLDER`, `has_placeholder`,
`commands`, `_join`), `tools/tests/test_backlog_commands.py`; `docs/TASKS.md` czytany,
nietknięty.

---

## 1. Pytanie, które stawia wpis

Od 6.D100 kolektor skleja z komendą także **ciało heredoku**, a ciało bywa programem
— w 6.A24 są to trzy wiersze Pythona. W programie `<` jest operatorem. Czy da się
odróżnić `<plan>` od `a < b` i od `x <- y`?

Odpowiedź: **tak, gdy operator jest otoczony spacjami; nie, gdy nie jest.** Obie połowy
są zmierzone i obie są zapisane — druga też, bo granica przemilczana wygląda jak
granica, której nie ma.

## 2. Pierwsza reguła, którą sprawdziłem, była NIEPRAWDĄ

Naturalne zawężenie brzmi „miejsce do wypełnienia nie ma w środku białych znaków":

```python
PLACEHOLDER = re.compile(r"<[^<>\s]+>")
```

Na drzewie daje to:

```
bloków z miejscem (stara reguła):  2     ['6.B18', '6.D9']
bloków z miejscem (ta reguła):     0
```

Oba dzisiejsze miejsca **mają w środku spacje**: `<dwa PNG z dwóch przebiegów tej samej
sceny>` i `<własny dziennik>`. Reguła odrzuciłaby więc jedyne dwa prawdziwe przypadki
i naruszyła warunek odbioru („zbiór bloków niezmieniony"). Jest to KN-2 niżej.

## 3. Reguła, która zostaje

```python
PLACEHOLDER = re.compile(r"<[^<>\s](?:[^<>]*[^<>\s])?>")
```

Po `<` **znak niebiały**, przed `>` **znak niebiały**, w środku bez nawiasów. Werdykty
na wejściu syntetycznym:

| wejście | werdykt |
|---|---|
| `<plan>`, `<x>` | miejsce |
| `<dwa PNG z dwóch przebiegów tej samej sceny>` | miejsce |
| `a < b`, `a < b > c`, `if a < b and b > c:` | **nie** |
| `x <- y` | **nie** |
| `cmd < wejscie > wyjscie` | **nie** |
| `python3 x.py 2>&1 \| tail -3` | **nie** |

Zbiór bloków z miejscem do wypełnienia: **6.D9 i 6.B18 przed i po**, czyli warunek
odbioru spełniony.

## 4. Czego reguła NIE rozstrzyga — i to jest wynik, nie przeoczenie

```
if (a<b) return a>b;      ->  MIEJSCE  (fałszywie)
if (a < b) return a > b;  ->  nie
```

Porównanie **bez spacji** z późniejszym `>` w tym samym wierszu nadal czyta się jako
miejsce do wypełnienia: po `<` stoi znak niebiały i przed `>` też. Odróżnienie
wymagałoby rozbioru składni języka, którym akurat jest ciało heredoku — a kolektor
poleceń nie wie, jaki to język, i wiedzieć nie ma.

Granica jest więc zapisana **w docstringu modułu** (tego żąda pole „Skończone, gdy")
i przybita osobnym testem, który nie żąda poprawy, tylko widoczności: przesunięcie
granicy w którąkolwiek stronę zapala go z komunikatem mówiącym, że to zmiana
do opisania.

## 5. Kontrola idzie CAŁĄ drogą, nie po samym wzorcu

`test_cialo_heredoku_z_operatorem_przechodzi_CALA_droga` buduje płotek z heredokiem,
którego ciałem jest Python z `if a < b and b > c:`, przepuszcza go przez `commands`
i dopiero potem pyta `has_placeholder`. Test na samym wzorcu nie powiedziałby, czy
ciało w ogóle **dochodzi** do pytania — a dochodzi dopiero od 6.D100. Asercja na
obecność ciała w komendzie stoi przed asercją o werdykcie właśnie po to.

Druga strona tej samej pary: miejsce do wypełnienia **w ciele** ma zostać zauważone.

## 6. Kontrole negatywne

`__pycache__` czyszczony przed każdym przebiegiem, po każdej `md5sum -c` na dwóch
plikach.

| # | co zepsute | wynik |
|---|---|---|
| KN-1 | wzorzec wraca do `<[^>]+>` | 14/17, dwa testy |
| KN-2 | wzorzec bez białych znaków w środku | **13/17, trzy testy** |
| KN-3 | ciało heredoku przestaje być sklejane z komendą | **13/17, cztery testy** |

**KN-2 jest tą, która obala „oczywistą" poprawkę:** wywraca nie tylko nową kontrolę,
ale i `test_the_blocks_with_placeholders_are_the_ones_the_measurement_named`
z komunikatem `bloki z miejscem do wypełnienia: [], spodziewane: ['6.B18', '6.D9']`.

**KN-3 pokazała najpierw usterkę w SOBIE.** Pierwsza wersja podmieniała
`def _join(parts, ciala):` — sygnatura ma domyślny argument (`ciala=None`), więc
`str.replace` nie trafiło i nic nie zmieniło. Kontrola wyszła **zielona 17/17**
i przez chwilę wyglądała jak wynik. Poprawiona (podmiana `ciala = ciala or {}`) zapala
cztery testy — wszystkie sprzed tej pozycji, z 6.D100. Wniosek na przyszłość:
podmiana bez asercji na trafienie kotwicy jest kontrolą, która mierzy siebie.

## 7. Weryfikacja

```
$ python3 tools/tests/test_all.py test_backlog_commands.py
  17/17 przeszło          (było 14)

$ python3 tools/tests/test_all.py
  2260/2260 przeszło, 120 modułów
```

## 8. Czego nie zrobiłem

- **Nie zmieniłem treści bloku 6.A24** i nie rozszerzałem `PLACEHOLDER` o kształty
  spoza nawiasu ostrokątnego — pole „Poza zakresem" wyklucza oba wprost.
- **Nie dodałem rozbioru składni ciała heredoku.** To jedyna droga do rozstrzygnięcia
  przypadku z §4, kosztuje parser na język i nie należy do zakresu tej pozycji.
- **Nie tknąłem `KNOWN_PLACEHOLDER_BLOCKS`**: zbiór miał zostać niezmieniony i został.

## 9. Zauważone przy okazji

- **`has_placeholder` nie wie, czy komenda jest z heredokiem**, bo dostaje gotowy
  napis. Reguła musi więc działać tak samo dla wiersza poleceń i dla programu —
  i to jest powód, dla którego nie da się jej zawęzić „tylko w ciele".
- **Wzorzec z §3 dopuszcza w środku wszystko poza nawiasami**, więc `<a href="x">`
  z HTML-a byłby miejscem do wypełnienia. W `docs/TASKS.md` HTML-a nie ma; gdyby
  kiedyś był, ta reguła wymagałaby przeliczenia, a ten wiersz jest po to, żeby
  wiadomo było, gdzie szukać.
