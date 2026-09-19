# 6.D303 · Z rejestru nie wyszła ani jedna — ale poza rejestrem zniknęły trzy, a trzy commity je cytują

**Data:** 19.09.2026 · **Gałąź:** `claude/sharp-ramanujan-jdr51o` · **Baza:** `cb5b2f9`

6.D294 podało w wierszu „zapadki z komunikatu nieobecne w rejestrze" liczbę zero
i nazwało ją **własnością wzorca, nie drzewa**: `NAZWA_ZAPADKI` buduje się jako
alternatywa nazw z rejestru, więc nazwa, której dziś w nim nie ma, nie zostanie
wydobyta z żadnego dawnego komunikatu. Ta pozycja pyta, ile takich nazw jest.

---

## 1. Odpowiedź na pytanie zadane wprost: ZERO, i to nie jest artefakt przyrządu

```
rewizji pliku tools/tests/test_tree_walks.py: 42
nazw w rejestrze DZIS: 91
nazw kiedykolwiek w rejestrze: 91
nazw KIEDYS, nie dzis: 0
```

**Ani jedna nazwa nigdy nie wyszła z rejestru.** Pole „Skończone, gdy" dopuszczało
odpowiedź „o zero" wprost i to jest ta odpowiedź — ale zero, którego powód jest
zmierzony, a nie założony.

Kontrola, czy czytnik naprawdę widzi dawne rewizje (bo zero bywa też odpowiedzią
oślepłego przyrządu): rejestr rośnie **monotonicznie**, od trzydziestu ośmiu nazw
11.09.2026 do dziewięćdziesięciu jeden dzisiaj, i **w żadnej rewizji nie maleje**.

```
76aadbb54f 2026-09-19  91      42c7289f52 2026-09-12  40
a806a04554 2026-09-19  90      52a6feb269 2026-09-11  38
...                            e9a89a1d88 2026-09-11   0
113b4a84c7 2026-09-12  42      deb38f2fae 2026-09-10   0
```

Cztery najstarsze rewizje dają zero nie dlatego, że czytnik ich nie rozumie, tylko
dlatego, że **rejestru wtedy nie było** — w `deb38f2fae` plik ma `WOLNO_WPROST`,
`MAX_WOLNO_WPROST` i `DRZEWA`, a nazwy `ZAPADKI` nie ma wcale. Sprawdziłem to
w źródle trzech z nich, zamiast wnioskować z zera.

## 2. Trzecia liczba i wiersz (4) z 6.D294: też zero, i też przez konstrukcję

Skoro zbiór nazw zniknionych z rejestru jest pusty, to commitów populacji cytujących
taką nazwę jest **zero**, a wiersz (4) z 6.D294 zmieniłby się **o zero**.

Zapisuję to tak, jak 6.D294 zapisało swoje: **to zero jest gwarantowane przez
konstrukcję**, nie zmierzone na drzewie. Pusty zbiór nie ma czego dopasować.
Sekwencja „zero przez konstrukcję" ciągnie się więc o jedną pozycję dalej, niż
tamta pozycja sięgnęła — i dopiero §3 mówi, gdzie się urywa.

## 3. ZERO JEST ZAKRESOWE — poza rejestrem zniknęło dziesięć nazw, a trzy są cytowane

Rejestr `ZAPADKI` ma dziewięć dni; projekt jest starszy. Pytanie „czego dzisiejszy
słownik nie zna" ma więc drugą populację, o którą pole „Wejście" prosi wprost
(`git log -S` po nazwach stałych), a której rejestr nie obejmuje.

```
stalych KIEDYKOLWIEK usunietych z tools/tests/: 73
stalych obecnych DZIS:                         903
ZNIKNIETYCH (usuniete i nieobecne dzis):        10
   BUILD_DIRS  CHK_CALL  FAKE_BLENDER_VERSION  GAME_SOURCE_GLOB  GAME_SOURCE_SKIP
   KOTWICA_ZABLOKOWANA  MAX_POINT_GAP_M  MIN_POINT_GAP_M  MIN_RADIUS_M  QUEUE_ROW
```

Trzy z dziesięciu mają **kształt zapadki**: `MIN_RADIUS_M`, `MIN_POINT_GAP_M`,
`MAX_POINT_GAP_M`. Droga zniknięcia wszystkich trzech to **SKASOWANA**, nie
przemianowana ani przeniesiona — usunął je commit `e3d06c1` („6.B25: martwa stała
usunięta, a drugi próg przestał być kopią walidatora"), a dziś żadna z trzech nie
stoi po lewej stronie przypisania.

Gdzie padają dziś — rozpisuję osobno, bo wspólne to nie jest, i ten akapit jest
przepisany, a nie dopisany obok. Pierwsza wersja mówiła o wszystkich trzech naraz
(„ich nazwy padają wyłącznie w prozie i w liście kontrolnej"), a prawdą jest to
wyłącznie o pierwszej z nich. `MIN_RADIUS_M` pada w czterech plikach: lista
kontrolna `test_constant_names.py`, asercja `test_dead_constants.py` oraz proza
`test_clearance_profile.py` i `test_packages.py`. `MIN_POINT_GAP_M` wraz
z `MAX_POINT_GAP_M` padają natomiast raz, razem, w jednej krotce przepisanych
nazw w `test_constant_names.py:149` — w prozie ani razu.

I tu zero się urywa:

```
commitow populacji cytujacych KTORAKOLWIEK ze znikietych nazw: 5
   33f5b9b1118d ['MIN_RADIUS_M']        e3d06c160e4a ['MIN_RADIUS_M']
   7368ad95bdd8 ['FAKE_BLENDER_VERSION'] e44b5aa40e6a ['MIN_RADIUS_M']
   911a2dc29816 ['BUILD_DIRS']
z tego cytujacych nazwe o KSZTALCIE ZAPADKI: 3
```

**Słownik sięgający wstecz zmieniłby wiersz (4) o zero, gdyby sięgał tylko po
rejestr — i o TRZY, gdyby znał także nazwy o kształcie zapadki, które do rejestru
nigdy nie weszły.** To jest liczba, dla której ta pozycja istnieje.

## 4. Kontrola przyrządu

Pole żądało, by nazwa stojąca w rejestrze DZIŚ nie wyszła w żadnej z czterech klas
zniknięcia. Nie wychodzi — ale **spełnienie jest trywialne**, bo wszystkie cztery
klasy są puste, i mówię to wprost zamiast raportować „zdana". Kontrola, która
przechodzi na pustym zbiorze, nie odróżnia czytnika działającego od oślepłego;
tę robotę wykonuje dopiero monotoniczny wzrost rejestru z §1 i odczytanie źródła
trzech najstarszych rewizji.

## 5. Przewidywania spisane PRZED pomiarem

| # | przewidywanie | wynik |
|---|---|---|
| 1 | nazw kiedyś-w-rejestrze-nie-dziś: 0–25 | trafione (0) |
| 2 | najliczniejsza droga: `PRZENIESIONA` albo `SKASOWANA` | nierozstrzygalne na rejestrze (zbiór pusty); na populacji szerszej wszystkie trzy to `SKASOWANA` |
| 3 | commitów populacji cytujących: 0–10 | trafione (0 na rejestrze, 5 na szerszej) |
| 4 | wiersz (4) zmieniłby się o tyle, ile wynosi (3) | trafione |
| 5 | dzisiejsza nazwa nie wyjdzie w żadnej klasie | trafione, ale trywialnie — §4 |
| 6 | rewizji pliku: 40–300 | trafione (42) |

Pięć trafionych, jedno nierozstrzygalne — i **żadne nie jest obalone po raz
pierwszy od czterech pozycji**. Powód jest prosty i wart zapisania: tym razem
przedziały były szerokie, bo nie miałem z czego ich zawęzić, a nie dlatego, że
wiedziałem więcej. Przewidywanie 1 z przedziałem „0–25" trafiłoby w zero i w każdą
inną odpowiedź poniżej dwudziestu pięciu; nie jest to sukces przewidywania, tylko
jego szerokość, i tak to liczę.

## 6. Czego świadomie nie zrobiono

- **Nie zmieniono rejestru `ZAPADKI`** ani wzorca `NAZWA_ZAPADKI` — pole
  „Poza zakresem" mówi wprost, że poszerzenie słownika o nazwy historyczne jest
  decyzją, którą te liczby mają dopiero **przygotować**.
- **Nie przepisano żadnego dawnego komunikatu.**
- **Nie tknięto `src/`** ani prozy w `tools/tests/`.
- **Nie policzono dróg zniknięcia dla siedmiu nazw spoza kształtu zapadki**
  (`BUILD_DIRS`, `CHK_CALL`, `FAKE_BLENDER_VERSION`, `GAME_SOURCE_GLOB`,
  `GAME_SOURCE_SKIP`, `KOTWICA_ZABLOKOWANA`, `QUEUE_ROW`) — pole pyta o zapadki,
  a te nimi nie są. Stoją tu z nazwy, żeby następna pozycja nie musiała ich szukać.

## 7. Zauważone przy okazji, nietknięte

Nazwa `MIN_RADIUS_M`, martwa jako stała od pozycji 6.B25, pada dziś w **czterech**
plikach testów, a nie w trzech — ten akapit jest przepisany, bo pierwsza wersja
liczyła pliki ręcznie i jeden przeoczyła. Dwa użycia stoją w kodzie (lista
kontrolna `test_constant_names.py` i asercja `test_dead_constants.py`, oba
zamierzone — pilnują, by nazwa nie wróciła), a dwa w **prozie** opisującej dawny
pomiar: `test_clearance_profile.py` i `test_packages.py`. Przeoczony był ten
ostatni, a jego komentarz `#:` dopisał **ten sam commit** `e3d06c1`, który stałą
usunął. Proza jest datowana i prawdziwa. Pytanie, którego ta pozycja nie zadaje:
ile nazw stałych pada dziś w prozie `tools/tests/` bez żadnego
przypisania w drzewie — czyli ile cytatów opisuje coś, czego już nie ma. Dla trzech
nazw z §3 odpowiedź jest znana; dla reszty z dziewięciuset trzech nie liczył jej nikt.
