# 6.D328 · Nadmiar robi OSIEMNAŚCIE procent nazw — a liczby 6.D317 nie odtwarza żadne z dwunastu odczytań jej własnej definicji

**Data:** 20.09.2026 · **Gałąź:** `claude/new-session-1xabcy` · **Baza:** `3254ce6`

6.D317 §1 zapisało, że w prozie pod `tools/` stoi **136** nazw PascalCase w grawisach
i **202** pary „nazwa w pliku", czyli średnio 1,49 pliku na nazwę. Pole pyta, co robi
ten nadmiar: garstka nazw cytowanych wszędzie czy wiele cytowanych po dwa razy.

Czytnik prozy jest **pożyczony** — `proza` z `test_message_claims.py`; typy publiczne
czytam `typy_publiczne(przedrostek="src/")` z `test_csharp_type_callers.py`, tak jak
6.D307 §1 i 6.D317.

---

## 1. Kontrola przyrządu NIE przechodzi — i to jest pierwsze znalezisko, nie usterka

Pole żąda, żeby suma po rozkładzie równała się **202**, a liczba wierszy — **136**.
Mój przyrząd, tym samym kształtem `(?:[A-Z][a-z0-9]+){2,}` co 6.D317, daje:

```
nazw=214  par=404  NADMIAR=190  (par/nazwę 1,888)   [cel 6.D317: 136 nazw, 202 pary]
```

Przewidywanie Z1, spisane przed pomiarem, brzmiało „kontrola nie przejdzie co do
jedynki". Nie przeszła — ale rozjazd jest **dwukrotny**, nie o jedynkę, i to wymagało
rozstrzygnięcia, zanim cokolwiek policzę dalej.

### 1.1 Drzewo się nie zmieniło — rozjazd siedzi w definicji

Pierwsza hipoteza była taka, że od 6.D317 przybyło prozy. **Zmierzona i obalona.**
Wystawiłem `git worktree` na bazie 6.D317 (`7d679f4`) i puściłem ten sam kształt na
obu drzewach, każde swoim własnym czytnikiem:

```
=== DZIŚ ===                   {"tools/tests": [214, 404], "tools/": [224, 450]}
=== BAZA 6.D317 (7d679f4) ===  {"tools/tests": [214, 404], "tools/": [224, 450]}
```

**Co do jedynki identyczne.** Dwadzieścia commitów prozy nie ruszyło ani nazwy, ani
pary — więc różnicy nie robi drzewo.

### 1.2 Dwanaście odczytań definicji 6.D317 i ani jedno nie daje 136/202

Definicja z 6.D317 ma trzy miejsca, w których da się ją przeczytać inaczej: katalog
(`tools/tests` czy całe `tools/`), dopasowanie (nazwa SZUKANA wewnątrz grawisu czy
grawis będący CAŁĄ nazwą) i rodzaj węzła (`proza` zwraca `komentarz` i `docstring`
osobno). Dwa razy dwa razy trzy — sprawdziłem wszystkie dwanaście:

```
wariant                                          nazw    par
CEL 6.D317                                        136    202
tools/tests · szukaj · oba                        214    404
tools/tests · szukaj · komentarz                  135    239
tools/tests · szukaj · docstring                  131    204
tools/tests · cały · oba                          126    191
tools/tests · cały · komentarz                     71    100
tools/tests · cały · docstring                     79    108
tools/ · szukaj · oba                             224    450
tools/ · szukaj · komentarz                       139    251
tools/ · szukaj · docstring                       140    240
tools/ · cały · oba                               133    220
tools/ · cały · komentarz                          73    107
tools/ · cały · docstring                          87    131
```

**Żaden wiersz nie trafia w parę 136/202, a dwa trafiają w jedną z liczb i chybiają
drugą**: `tools/tests · szukaj · docstring` daje 131 nazw przy 204 parach (pary
prawie na miejscu, nazw brak pięciu), a `tools/ · cały · oba` daje 133 nazwy przy
220 parach. To jest najbliżej, jak da się dojść, nie zmyślając trzynastego wariantu.

**Nie uzgadniam tej różnicy** — dokładnie z powodu, dla którego samo 6.D317 nie
uzgadniało swojej różnicy siedmiu z 6.D307: uzgadnianie polegałoby na rozciąganiu
mojego kształtu do cudzej liczby. Mówię zamiast tego, **czego nie liczę**: liczę parę
`(nazwa, plik)` odłożoną do zbioru, więc dwa wystąpienia tej samej nazwy w tym samym
pliku są jedną parą; czytam `proza()` z domyślnym katalogiem, czyli `tools/tests`,
a nie całe `tools/` — mimo że 6.D317 pisze „pod `tools/`", bo jego własna liczba jest
od obu tych odczytów dalej niż o połowę.

**Granica, którą to stawia:** liczba 136/202 z 6.D317 jest dziś **nieodtwarzalna**
z jego własnego opisu. Nie twierdzę, że jest nieprawdziwa — twierdzę, że raport nie
niesie tego, co trzeba, żeby ją sprawdzić, i że to jest koszt, który płaci następna
pozycja, a nie poprzednia.

## 2. Odpowiedź na pytanie pola, na mojej populacji

Nadmiar to **190** par ponad liczbę nazw. Rozkład zasięgu:

```
rozkład nazw:  1 plik=131 (61 %)   2 pliki=44   3+=39
nadmiar z klasy „2 pliki": 44   ·   z klasy „3+": 146
```

Narastająco, od nazwy o największym zasięgu:

```
  1 nazwa  wnosi  10 z 190 nadmiaru, czyli  5,3 %
  5 nazw   wnosi  46 z 190 nadmiaru, czyli 24,2 %
 10 nazw   wnosi  74 z 190 nadmiaru, czyli 38,9 %
 20 nazw   wnosi 108 z 190 nadmiaru, czyli 56,8 %
 39 nazw   wnosi 146 z 190 nadmiaru, czyli 76,8 %
```

**Odpowiedź brzmi: ani jedno, ani drugie z tego, co pole postawiło jako alternatywę.**
Nie robi go garstka — jedna nazwa to 5,3 %, pięć to ćwierć. I nie robią go „nazwy
cytowane po dwa razy" — cała klasa dwóch plików wnosi **44 ze 190**, czyli 23 %.
Robi go **klasa 3+: 39 nazw, czyli 18 % populacji, niosące 77 % nadmiaru**. Mediana
zasięgu jest równa **1,0** — połowa populacji nie uczestniczy w nadmiarze w ogóle.

## 3. Przewidywania — cztery trafione, jedno obalone, jedno połowicznie

| # | przewidywanie | wynik |
|---|---|---|
| Z1 | kontrola przyrządu nie przejdzie co do jedynki | **trafione**, ale rozjazd jest dwukrotny, nie o jedynkę (§1) |
| Z2 | większość nazw pada w DOKŁADNIE JEDNYM pliku | **trafione**: 131 z 214, czyli 61 % |
| Z3 | dziesiątka zdominowana przez nazwy BCL/Pythona | **połowicznie**: 7 z 10 to BCL/Python, 3 to typy `src/` |
| Z4 | typy `src/` mają zasięg MNIEJSZY niż „reszta" (mediana) | **OBALONE**, §3.1 |
| Z5 | człon jednoliterowy doda co najmniej jedną nazwę | **trafione**: 214 → 221 nazw, 404 → 412 par |
| Z6 | najliczniejsza nazwa ma zasięg większy niż 5 plików | **trafione**: 11 plików |

### 3.1 Z4 obalone — i mediana nie umiała tego pokazać

```
typ src/   nazw=48   mediana=1,0  średnia=1,98  max=11  w 1 pliku=27 (56 %)
reszta     nazw=166  mediana=1,0  średnia=1,86  max=11  w 1 pliku=104 (63 %)
```

Mediana jest w obu klasach **równa 1,0**, więc miara, którą Z4 sobie wybrało,
nie rozróżnia tych populacji w ogóle. Rozróżnia je średnia i udział nazw
jednoplikowych — i obie mówią przeciwnie, niż przewidywałem: typy `src/` mają zasięg
NIECO WIĘKSZY (1,98 do 1,86), a jednoplikowych jest wśród nich MNIEJ (56 % do 63 %).
Zapisuję to jako obalenie, a nie jako remis, bo warunek Z4 był kierunkowy.

### 3.2 Dziesiątka o największym zasięgu

```
FirstRun 11 (TYP src/) · ValueError 11 · AssertionError 10 · RunPlan 10 (TYP src/)
SystemExit 9 · UiTextTests 8 · LineCore 7 (TYP src/) · KeyError 6
ZeroDivisionError 6 · IndexError 6
```

Sufit zasięgu to **11 plików** i dzielą go dwie nazwy z różnych światów: typ tego
projektu i wyjątek wbudowany Pythona.

## 4. Usterka przyrządu, którą zgłaszam, a nie poprawiam po cichu

Pierwsza wersja miała filtr katalogowy `plik.startswith("tools/")` i zwracała
**zero nazw, zero par** dla obu katalogów. Nie jest to własność drzewa: `proza()`
zwraca w polu `plik` **samą nazwę pliku**, nie ścieżkę, więc przedrostek nie mógł
się dopasować nigdy. Filtr wyrzuciłem, a katalog zawężam wejściem `katalog=`
samego czytnika — jedynym miejscem, w którym czytnik to rozróżnia.

## 5. Czego świadomie nie zrobiłem

Nie dopisałem bramki. Ta pozycja mierzy kształt cudzej populacji i podaje granicę
odtwarzalności; nie ma tu progu, który miałby czego pilnować, a zapadka na liczbie
214 zestarzałaby się przy pierwszym dopisanym komentarzu.

Nie poprawiłem 6.D317. Raport jest zapisem pomiaru z konkretnego dnia; §1 mówi,
czego w nim brakuje, żeby liczbę dało się sprawdzić, i to jest właściwa forma.
