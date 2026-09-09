# Dwie długości odcisku, które nie były tą samą wielkością (6.D36)

**Zmierzone 09.09.2026 na:** `dba5737`, kontener tej sesji.
**Przyrząd:** `grep` po `tools/` i `src/`, `git log -S`, `tools/tests/mutation_sweep.py`,
nowy moduł `tools/tests/test_hexdigest_truncation.py`,
`python3 tools/tests/test_all.py`.

---

## 1. Co pozycja podejrzewała

Trzy obcięcia odcisku w całym drzewie: dwa przez stałą `ODCISK_ZNAKOW`, jedno przez
literał. Pozycja nazwała to „dwiema długościami tej samej wielkości, z których żadna
nie jest liczona z drugiej", i kazała rozstrzygnąć **pomiarem**, czy warto z tego
robić bramkę — z uwagą, że przy trzech wystąpieniach bramka może być droższa
od problemu.

## 2. Pomiary

Trzy obcięcia potwierdzone na dzisiejszym drzewie, wszystkie w jednym pliku:

```
obcięć hexdigest RAZEM: 3
  przez STALA:  tools/tests/mutation_sweep.py:462  [:ODCISK_ZNAKOW]
                tools/tests/mutation_sweep.py:961  [:ODCISK_ZNAKOW]
  przez LITERAL: tools/tests/mutation_sweep.py:1008 [:12]
```

**Pierwszy skan dał jednak inne liczby i to jest pierwszy wynik tej pozycji.**
`grep` po `.` zwrócił sześć literałów i dwanaście obcięć przez stałą:

```
      6   12
     12   ODCISK_ZNAKOW
```

Nadwyżka to `.claude/worktrees/` — pięć pełnych kopii drzewa, pominiętych
w `.gitignore` i niewidocznych w `git status`. Każda liczba z takiego skanu jest
przemnożona przez liczbę kopii, a ta zmienia się sama.

Historia literału, z `git log -S`:

| co | wartość |
|---|---|
| wszedł | 06.09.2026, `16cc5d8` (6.B17) |
| commitów w repozytorium razem | 763 |
| commitów, które przeżył | 292 |
| stała `ODCISK_ZNAKOW` powstała | później, w 6.B32 |

Kolejność jest tu istotna: literał był **pierwszy**, stała przyszła po nim i dla
innej wielkości. Wrażenie „dwóch zapisów jednej liczby" powstało dopiero z tego
zestawienia, a nie z jednej decyzji.

Nazwy dzienników stojące w drzewie:

```
9 różnych nazw, każda o znaczniku długości 12
```

## 3. Rozstrzygnięcie: to NIE jest jedna wielkość

Pomiar odwrócił tezę pozycji. Dwanaście i szesnaście nie są dwoma zapisami tej
samej liczby, bo **obcinają dwa różne odciski o różnej odporności na kolizję**:

- `ODCISK_ZNAKOW` obcina odcisk **treści**, który służy do **porównania**. Kolizja
  podstawia wynik policzony dla innej treści pod dzisiejszą mutację, a odmowa
  z 6.B32 stoi na tej właśnie wartości — więc nie może być jednocześnie jej
  kontrolą. Druga linia obrony: **żadna**.
- znacznik obcina odcisk składany na **nazwę pliku**. Kolizja daje dwóm przebiegom
  wspólną ścieżkę, a to jest dokładnie sytuacja, którą odmowa z 6.B32 **łapie**, bo
  porównuje odcisk zapisany we wpisie, nie w nazwie. Druga linia obrony: **jest**.

Dlatego reguła „jedna długość dla wszystkich" byłaby błędem, nie porządkiem:
zapaliłaby się na dwóch przypadkach zrobionych dobrze.

## 4. Uzasadnienie liczby, o które prosiła pozycja

Dwanaście znaków szesnastkowych to **48 bitów**, czyli 281 474 976 710 656
wartości. Szansa przypadkowej kolizji (paradoks urodzin, `n(n-1)/2·2^48`):

| różnych przebiegów | szansa kolizji |
|---|---|
| 9 (stan drzewa) | 1,3 · 10⁻¹³ |
| 100 | 1,8 · 10⁻¹¹ |
| 751 | 1,0 · 10⁻⁹ |
| 23 727 | 1,0 · 10⁻⁶ |

Progu jednej milionowej ta długość dosięga przy **23 727** różnych przebiegach —
liczbie o trzy rzędy wyższej od wszystkiego, co to repozytorium widziało. Przy
dziewięciu dziennikach zapas jest ośmiorzędowy. **Podniesienie 12 do 16
przenazwałoby wszystkie istniejące dzienniki i pomiar nie daje po to powodu**;
pozycja wprost zostawiała tę decyzję osobno i tak zostaje.

## 5. Co powstało

Literał zniknął, ale nie przez podmianę na inną liczbę — przez **nazwę
z uzasadnieniem**: `ZNACZNIK_ZNAKOW` stoi w `tools/tests/mutation_sweep.py`
obok `ODCISK_ZNAKOW`, z akapitem, który mówi 48 bitów, podaje próg z tabeli wyżej
i **wyjaśnia, czemu ta liczba NIE jest równa tamtej**. To ostatnie zdanie jest tu
najważniejsze: bez niego pierwsza osoba, która zauważy różnicę, „naprawi" ją
do zgodności.

Bramka powstała mimo ostrzeżenia z pozycji, i liczba, która o tym zdecydowała,
jest jedna: literał przeżył **292 commity**, a `tools/tests/test_dead_constants.py`
pilnuje dokładnie odwrotnego kierunku — stałej, której nikt nie czyta. Tamta bramka
uzasadnia się zdaniem, które stosuje się tu dosłownie: martwa stała jest zdaniem
o repozytorium, które ktoś przeczyta i uzna za prawdziwe. Literał nie jest zdaniem
o niczym — i dlatego przeżył 292 commity, a nie dlatego, że był nieszkodliwy.

Bramka NIE wymaga równości długości (patrz §3). Wymaga nazwy i uzasadnienia
z liczbą.

## 6. Weryfikacja

```
  7/7 przeszło
  RAZEM 103.924 s, 2066 testów, 110 modułów
```

Zestaw przed pozycją: 2059 testów, 109 modułów.

## 7. Kontrole negatywne — wykonane

| mutacja | skutek |
|---|---|
| literał przywrócony w miejsce stałej | `FAIL test_zadne_obciecie_hexdigest_nie_idzie_przez_literal`, 6/7 |
| stała bez akapitu nad definicją | `FAIL test_kazda_stala_obcinajaca_ma_przy_sobie_uzasadnienie_z_liczba`, 6/7 |
| akapit bez ani jednej cyfry, sama proza | ten sam test, 6/7 |
| korzenie skanu podmienione na korzeń repozytorium | dwa testy, 5/7 — w tym trafienia w kopiach |
| podłoga skanu wyzerowana | `FAIL test_podloga_nie_jest_wyzerowana`, 6/7 |
| wzorzec zawężony tak, że nie łapie nic | dwa testy, 5/7 |

Kontrola czwarta powiedziała więcej, niż miała:

```
FAIL test_skan_nie_liczy_kopii_z_katalogow_ignorowanych: skan wszedl do kopii
  z katalogu ignorowanego: 15 trafien pod .claude/worktrees
FAIL test_zadne_obciecie_hexdigest_nie_idzie_przez_literal: obciecia hexdigest
  przez literal: '.claude/worktrees/agent-a1ff8a5d4b896b3d2/tools/tests/mutation_sweep.py:1008  [:12]'
```

Kopie niosą **stary numer wiersza i stary literał**, bo powstały przed tą poprawką.
Skan liczący wystąpienia raportowałby więc usterkę już naprawioną w drzewie — i to
jest drugi, mocniejszy powód, żeby żaden nie zaglądał tam nigdy.

Po każdej kontroli `md5sum -c`: `OK` dla obu plików.

## 8. Bramka zapaliła się na sobie i to jest osobny wynik

Pierwsza wersja modułu padła na własnym tekście: opis wzorca w komentarzu **był**
wzorcem, a próbka do samosprawdzenia, składana z kawałków, i tak zostawiała
w pliku dopasowanie. To fałszywy alarm na poprawnej treści, czyli rodzina, którą
6.D27 nazwało jako powód wyłączania bramek.

Poprawione trzy rzeczy, z czego trzecia jest istotniejsza od dwóch pierwszych:
komentarz opisuje wzorzec słowami zamiast go pokazywać, próbka rozrywa samo
wywołanie, a test samosprawdzenia pyta teraz o **zero trafień**, nie o zero
literałów. Stara wersja przeciek **przepuściła**, bo fragment z konkatenacji nie
jest literałem dziesiętnym, choć wzorzec już go łapał — test opisywał więc coś
węższego niż jego własna nazwa. Wzmocnienie, nie osłabienie.

## 9. Czego świadomie nie zrobiono

Nie zmieniono `ODCISK_ZNAKOW` — ma pomiar i uzasadnienie, a pozycja wyklucza to
wprost. Nie przenazwano istniejących dzienników. Nie podniesiono długości znacznika,
bo §4 nie daje po to powodu.

Nie dopisano pomiaru do listy przebiegów w `tools/tests/test_suite_runtime_budget.py`:
dzisiejszy czas jest niższy od najwyższego już zapisanego, więc nie zacieśniłby
marginesu ani o krok, a plik jest poza zakresem tej pozycji.

## 10. Co zauważone przy okazji, nie tknięte

Dziesięć modułów bramkowych chodzi po drzewie przez `os.walk`, i **żaden nie wyklucza
kopii z katalogu ignorowanego**. Nie daje się dziś nabrać ani jeden — ale wyłącznie
dlatego, że wszystkie startują z **nazwanego podkatalogu** (`tools`, `src`, `docs`,
`reports`), a kopie leżą pod `.claude/`. Ochrona jest więc uboczna wobec
nazewnictwa: jedno przejście liczone od korzenia repozytorium wywróciłoby wszystkie
dziesięć naraz, i dokładnie to zrobił pierwszy skan tej pozycji, opisany w §2.
Nic tego nie pilnuje. Pozycja na najbliższe uzupełnienie kolejki, nie zmiana
przy okazji.
