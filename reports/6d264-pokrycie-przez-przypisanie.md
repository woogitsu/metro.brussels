# 6.D264 — trzy czwarte „pokrycia" jest zbiegiem cyfr

**Data:** 18.09.2026 · **Gałąź:** `claude/6d264-pokrycie-przez-co` · **Baza:** `f6c0c50`

## 1. Obie liczby, których żądało pole „Wyjście"

```
pogrubionych liczb w prozie:                    286
z tego w wierszu z DATĄ (sito pomija):           47
zostaje:                                        239
bez pokrycia (zapadka górna):                   175
POKRYTYCH:                                       64
```

Z tych 64:

| co daje pokrycie | ile |
|---|---|
| PRZYPISANIE STAŁEJ w oknie | **15** |
| przypadkowe wystąpienie tej samej cyfry | **49** |

**Trzy czwarte „pokrycia" jest zbiegiem cyfr, a nie zapisem w kodzie.**

## 2. Przykłady, bo liczba sama nie pokazuje, jak to wygląda

Pokrycie przez **przypisanie** — liczba stoi obok stałej, która ją niesie:

```
test_assertion_gate.py:1906   [0,087]   KOSZT_PODPROCESU_S = 0.087
test_backlog.py:137           [6]       MINIMUM_DOCUMENTED_ITEMS = 6
test_field_paths.py:182       [60]      MIN_MODULE_NAMES = 60
test_runner_number_parsing.py [5]       MINIMUM_MIEJSC = 5
```

Pokrycie przez **zbieg cyfr** — ta sama cyfra stoi obok przypadkiem:

```
csharp_pins.py:202            [0]       while i < len(maska) and glebokosc > 0:
test_assertion_gate.py:1909   [1,0]     "NIE_Z_TEJ_RODZINY": 1,
test_dotnet_version.py:1537   [1]       "kod": 1,
```

Liczba uznana za pokrytą nie jest więc liczbą, której cokolwiek **pilnuje**; jest
liczbą, której ta sama cyfra gdzieś obok przypadkiem stoi.

## 3. Czego to NIE znaczy

**Nie znaczy, że zapadkę 175 trzeba podnieść** — podnieść zapadki górnej nie wolno,
a i tak nie o to chodzi. Znaczy, że słowo „pokrycie" opisuje w bramce z 6.D259
**dwie bardzo różne rzeczy** i dotąd nie było tego widać. Rozróżnienie jest od dziś
przybite dwiema równościami i porównywane z drzewem.

Równość, a nie podłoga: **każde przejście liczby z kupki „zbieg" do kupki
„przypisanie" jest poprawą**, którą chce się widzieć — liczba stanęła obok swojej
stałej. Przejście w drugą stronę znaczy, że stała zniknęła, a proza o niej została.

## 4. Cena bramki z 6.D259 — widoczna w tym samym akapicie, który ją opisuje

Pisząc docstring tej pozycji dołożyłem siedem pogrubionych liczb i **cztery z nich
nie miały pokrycia** — zapadka podskoczyła ze 175 na 179. Podnieść jej nie wolno,
więc zdjąłem pogrubienie z czterech, a zostawiłem przy dwóch (15 i 49), bo te stoją
obok stałych, które je niosą.

**To jest trzeci raz w tej serii, kiedy zapisanie wyniku pomiaru kosztuje zdjęcie
pogrubienia** (6.D260 i 6.D262 były wcześniejsze). Cena tamtej bramki jest więc
widoczna w tym samym akapicie, który ją opisuje — i jest to dokładnie ta różnica,
którą ta pozycja mierzy.

## 5. Kontrole negatywne — przewidywania spisane PRZED przebiegami

Wejście syntetyczne, bez dotykania drzewa (§4.6 nie jest tu potrzebne, bo nic
w repozytorium nie jest zmieniane).

Drzewo próbne: proza o `**7**`, `**8**` i `**9**`; `PROG = 7` (przypisanie),
`len(x) > 8` (zbieg cyfr), a `9` bez niczego.

```
BAZA                            {'przypisanie': 1, 'zbieg': 1, 'bez pokrycia': 1}
KN-a: PROG = 77                 {'przypisanie': 0, 'zbieg': 1, 'bez pokrycia': 2}
KN-b: len(x) > 88               {'przypisanie': 1, 'zbieg': 0, 'bez pokrycia': 2}
```

**Obie kupki ruszają się NIEZALEŻNIE**, i to jest mocniejsza postać kontroli, niż
żądało pole „Weryfikacja": zdjęcie przypisania nie rusza zbiegu, a zdjęcie zbiegu
nie rusza przypisania. Czytnik, który wrzucałby wszystko do jednej kupki, dałby
w obu przebiegach tę samą liczbę.

Trzecia asercja pilnuje zgodności z zapadką: ten czytnik i `pogrubione_bez_pokrycia`
muszą widzieć **tę samą** liczbę bez pokrycia, bo inaczej dwa czytniki mówiłyby
o dwóch różnych drzewach.

## 6. Weryfikacja

```
python3 tools/tests/test_all.py test_message_claims.py
  8/8 przeszło

python3 tools/tests/test_all.py
  2588/2588 przeszło
  RAZEM 262.856 s, 2588 testów, 131 modułów
```

## 7. Zauważone, nietknięte

- **Nie zmieniono żadnego progu ani okna.** Pole „Poza zakresem" zabrania wprost;
  ta pozycja mierzy, a nie luzuje.
- **Nie przepisywano prozy, której pomiar dotyczy** — poza zdjęciem pogrubienia
  z czterech liczb w docstringu, który sam dopisałem tym commitem.
- **49 liczb pokrytych zbiegiem cyfr nie zostało wypisanych z adresami.** Pole
  „Wyjście" żądało liczby, nie listy; lista 49 pozycji byłaby napisem (6.D243),
  dopóki nikt nie zdecyduje, co z nimi zrobić. Czytnik jest w kodzie i daje ją
  na żądanie.
