# 6.D141 — pinów liczbowych jest 627, a porównań dokładnych dziesięć razy więcej, niż mówi licznik

**11.09.2026**, na `888a190`. Pozycja: `csharp_pins.py` liczy piny, których wartością
oczekiwaną jest **literał napisowy** (44 + 74 = 118). `Assert.AreEqual(9.40, …)`
i `Assert.AreEqual(4L, …)` są pinami wpisanymi z ręki tak samo, a nie liczy ich nikt.

## 1. Pomiar

| | `Game.Tests` | `Sim.Tests` | razem |
|---|---:|---:|---:|
| pinów liczbowych | 186 | 441 | **627** |
| z tolerancją | 98 | 179 | 277 |
| bez tolerancji | 88 | 262 | 350 |
| zmiennoprzecinkowych | 104 | 187 | 291 |
| …**bez tolerancji** | 6 | 8 | **14** |
| całkowitych | 82 | 254 | 336 |
| …**z tolerancją** | 0 | 0 | **0** |
| tolerancja zapisana jako `0.0` | 18 | 114 | **132** |

Pinów liczbowych jest **pięć razy więcej** niż napisowych.

## 2. Dwa wnioski, które nie są statystyką

**Tolerancja jest wyłącznie rzeczą zmiennoprzecinkową — zero na 336 pinów całkowitych.**
Nie jest to zwyczaj ani przypadek: `Assert.AreEqual(int, int, double)` **nie ma
przeciążenia**, więc pin całkowity z tolerancją nie skompilowałby się. Zapadka z obu
stron na tym zerze pilnuje, żeby zdanie zostało prawdziwe — a gdyby przestało, znaczyłoby
albo że czytnik bierze za tolerancję coś, co nią nie jest, albo że ktoś przeszedł
na `double`.

**Porównań dokładnych na liczbie zmiennoprzecinkowej jest 146, nie 14.** Czternaście nie
ma trzeciego argumentu wcale, a **132 podaje tolerancję zapisaną jako `0.0`**, czyli
deklaruje dokładność jawnie:

```csharp
Assert.AreEqual(0.0, cab.State.DistanceM, 0.0);
Assert.AreEqual(ceiling, PoweredOnly.AchievableDecelerationMps2(2.0 * ceiling, mu), 0.0);
```

Sam licznik „bez tolerancji" byłby więc **dziesięciokrotnie zaniżony** — i jest to
dokładnie ten kształt, który projekt tropi od 6.D27: liczba mówiąca o czymś węższym,
niż sugeruje jej nazwa.

## 3. Rozstrzygnięcie: własny licznik, nie tabela kategorii

Pole „Wyjście" pytało, czy piny liczbowe wchodzą do tej samej tabeli `KATEGORIE`, co
napisowe. **Nie.** Tabela z jednym wierszem na pin ma sens przy 44 pozycjach — przy
**627** byłaby dłuższa od kodu, który opisuje, i rozjeżdżałaby się przy każdej zmianie
liczby. Piny liczbowe dostają **rozkład**: osiem liczb na katalog, przybitych równością,
i wypis w `main()`:

```
[PINY] tests/Sim.Tests: 441 liczbowych — 179 z tolerancja, 262 bez
        zmiennoprzecinkowych 187, z nich BEZ tolerancji 8
        calkowitych 254, z nich Z tolerancja 0 (Assert.AreEqual(int,int,double) nie ma przeciazenia)
        tolerancja zapisana jako 0,0: 114 — porownan DOKLADNYCH razem: 122
```

## 4. Kontrole negatywne

Baza `test_csharp_pins.py`: **10/10** (było 5). `__pycache__` czyszczony przed każdym
przebiegiem, przywracanie przez `cp`, po każdej `md5sum -c` → `OK` na dwóch plikach.

| kontrola | zmiana | wynik |
|---|---|---|
| KN-1 | trzeci argument brany bez sprawdzenia, czy jest liczbą | **6/10**, cztery testy |
| KN-2 | cięcie argumentów po oryginale zamiast po masce | **10/10 ZIELONA** |
| KN-2b | to samo po poprawce wejścia syntetycznego | **9/10** |
| KN-3 | rozróżnienie zmiennoprzecinkowe/całkowite zdjęte | **8/10**, dwa testy |
| KN-4 | tolerancja `0.0` liczona jak każda inna | **8/10**, dwa testy |
| KN-5 | wzorzec liczby bez przyrostków typu (`4L`, `1e-3f`) | **7/10**, trzy testy |

**KN-2 wyszła zielona i poprawiła moje wejście syntetyczne, nie kod.** Napisałem probę
`Assert.AreEqual(2.5, g("x, y"), 1e-3)` — przecinek wewnątrz zagnieżdżonego wywołania
stoi na **głębokości 2**, a tam licznik nawiasów radzi sobie bez maski. Dopiero napis
na głębokości 1 (`Assert.AreEqual(2.5, "x, y".Length, 1e-3)`) rozstrzyga; KN-2b jest
czerwona i pokazuje tolerancję `None` zamiast `1e-3`.

**KN-5 jest warta zdania**: bez przyrostków typu znika **44 pinów** w warstwie gry
(186 → 142), bo `4L`, `1e-3f` i `2u` przestają być liczbami. Przyrostek nie jest
szczegółem wzorca — jest jedną trzecią materiału.

## 5. Pułapka po drodze

Pierwsza wersja kontroli syntetycznej wołała czytnik napisowy **poza** blokiem
`with tempfile.TemporaryDirectory()`. Katalog już nie istniał, `glob` zwracał pustą
listę, a test mierzył **brak plików zamiast braku pinów** — i zgłosił to jako
`czytnik napisowy zobaczył co innego niż jeden napis: []`.

## 6. Weryfikacja

```
  10/10 przeszło        test_csharp_pins.py   (było 5)
  2361/2361 przeszło, 123 moduły, KOD=0
```

## 7. Czego nie zrobiłem

* **Nie zdjąłem ani nie przepisałem żadnego pinu**, w tym żadnego z 14 porównań
  dokładnych bez tolerancji — wprost w „Poza zakresem". Pozycja mierzy i rozstrzyga.
* **Nie rozwijam stałych.** `Assert.AreEqual(OCZEKIWANY, x)` z `const double` nie jest
  tu pinem, choć nim jest; wymagałoby to drzewa składni C#, którego repozytorium nie ma
  i mieć nie będzie (6.D85, 6.D131).
* **Nie oceniam, czy 132 tolerancje `0.0` są w porządku.** Dokładne porównanie
  zmiennoprzecinkowe bywa poprawne — gdy obie strony liczy ten sam kod tą samą drogą —
  i rozstrzygnięcie per asercja jest pracą liniową w ich liczbie, czyli osobną pozycją.
* **Nie objąłem czytnikiem `Assert.AreNotEqual` ani `Assert.IsTrue(x == y)`.** Pierwsze
  nie niesie wartości oczekiwanej w tym sensie, drugie wymagałoby parsowania wyrażenia.
