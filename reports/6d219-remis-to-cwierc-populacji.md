# 6.D219 — remis to ćwierć populacji, a zachowuje się jak zdanie świeże

**15.09.2026**, na `dd52ba4`. Wejście: `tools/tests/test_report_claims.py`
(`zdanie_z_dnia_pomiaru`, `data_stalej`, `data_raportu`, `claims_in_reports`,
`wystapienia_w_jednych_grawisach`), `reports/*.md`,
`reports/6d209-cztery-cytaty-i-ani-jednego-twierdzenia.md` §4.

## 1. Ilu twierdzeń dotyczy remis

| klasa dat | kształt `CLAIM` | kształt `` `NAZWA = N` `` | razem | rozjechanych |
|---|---:|---:|---:|---:|
| **REMIS** (`data_raportu == data_stalej`) | **3** | **23** | **26** | **2** |
| `stała nowsza` — dziś **zwalniana** | 15 | 14 | 29 | **27** |
| `raport nowszy` — pilnowana | 38 | 8 | 46 | 1 |
| razem | 56 | 45 | 101 | 30 |

**Remis to 26 ze 101, czyli ćwierć populacji** — a dla kształtu `` `NAZWA = N` ``
**23 z 45, czyli ponad połowę**. Teza pola „Czego NIE wolno zrobić bez pomiaru"
(„jeśli tak pracuje każdy agent, remis jest regułą, a nie brzegiem") jest potwierdzona
na populacji jedenaście razy większej niż cztery przypadki z 6.D209.

Różnica między kształtami nie jest przypadkiem: `` `NAZWA = N` `` cytują głównie raporty
pisane **w commicie zapadki**, a `CLAIM` — raporty późniejsze (38 z 56 to „raport nowszy").

## 2. Rozstrzygnięcie: `>=` ZOSTAJE, remis NIE zwalnia

Powód jest ten, którego żądało pole — **oparty na tym, ile remisów jest rozjechanych**:

| klasa | wystąpień | rozjechanych | odsetek |
|---|---:|---:|---:|
| `stała nowsza` (**zwalniana**) | 29 | 27 | **93,1 %** |
| **REMIS** (**pilnowana**) | 26 | 2 | **7,7 %** |
| `raport nowszy` (pilnowana) | 46 | 1 | 2,2 % |

Mechanizm z 6.D108 istnieje po to, żeby zwalniać zdania, które **zestarzały się
w czasie** — i ta populacja jest w tabeli widoczna: 93,1 % rozjazdu. **Remis zachowuje
się jak populacja świeża** (7,7 %, blisko 2,2 % klasy „raport nowszy"), a nie jak
zestarzała. Zwolnienie go byłoby zwolnieniem zbioru, który w 92,3 % zgadza się dziś
z drzewem.

**Drugi powód, twardszy:** oba rozjechane remisy to **dokładnie ten przypadek, przed
którym ostrzega pole pozycji** — twierdzenie wpisane w commicie, który stałą ustawił:

```
6d156-zawezenie-szczelne-i-odrzucone.md   NIEROZSTRZYGNIETYCH   raport 72, kod 68
sciezki-w-polach-blokow.md                MAX_EXCEPTIONS        raport  2, kod  1
```

**Grawisów w tym cytacie nie ma i to jest wybór, nie niechlujstwo.** Zapis
``` `NAZWA = N` ``` wewnątrz grawisów jest dla `wystapienia_w_jednych_grawisach()`
twierdzeniem, **także w bloku kodu** — bo ten czytnik, inaczej niż `claims_in_reports()`,
bloków ogrodzonych nie pomija. Zacytowanie cudzego twierdzenia w jego własnym kształcie
zapaliłoby więc bramkę na tym raporcie. Rozjazd obu czytników wpisany jako **6.D230**.

Pod `>=` zostają złapane i skierowane do oceny człowieka (oba wylądowały
w `CYTATY_NIE_TWIERDZENIA` z uzasadnieniem 6.D209). Pod `>` zniknęłyby bez słowa.

## 3. Ile zmienia zamiana operatora — zmierzone, nie przewidziane

Podstawienie `d_stalej > d_raportu` → `>=` (czyli „remis zwalnia"), moduł uruchomiony
przed i po:

```
BAZA:     16/16 przeszło,  zwolnionych twierdzeń kształtu CLAIM: 15 z 56
MUTACJA:  15/16 przeszło,  zwolnionych twierdzeń kształtu CLAIM: 18 z 56
```

**Trzy twierdzenia kształtu `CLAIM` i 23 wystąpienia kształtu `` `NAZWA = N` ``
przestałyby być pilnowane** — czyli dokładnie zmierzona liczba remisów, o którą prosiło
pole „Weryfikacja".

## 4. Znalezisko, którego pozycja nie zamawiała: decyzja JEST przybita, tylko nie tam, gdzie się patrzy

Mutacja operatora zapala **dokładnie jeden test** i jest nim
`test_zdanie_datowane_nie_jest_pilnowane_a_zdanie_biezace_jest` — jego **trzeci blok**,
stawiający daty równe na **wejściu syntetycznym**:

```
FAIL test_zdanie_datowane_nie_jest_pilnowane_a_zdanie_biezace_jest:
     raport tknięty w tej samej chwili co stała ma nieść wartość NOWĄ
```

**Żadna bramka czytająca dzisiejsze raporty tej zmiany nie zauważa** — i nie może,
bo dziś remis nie daje ani jednej czerwieni. Decyzja o remisie jest więc pilnowana
**wyłącznie kontrolą przyrządu**, od 6.D108, i nikt tego nigdzie nie napisał: nazwa
tamtego testu mówi o zdaniu **datowanym**, a nie o remisie.

Ta pozycja nie dokłada więc drugiej bramki — **nazywa istniejącą**: decyzja dostaje
własny test z własną nazwą i obie gałęzie na wejściu syntetycznym, żeby następny agent
nie szukał jej w środku testu o czym innym.

## 5. Czego ta pozycja NIE robi i dlaczego

**Nie przybija populacji remisu.** Klasa „remis" zależy od `data_stalej`, a ta datuje
stałą commitem, który ostatnio ruszył jej **PLIK**, nie jej wiersz — czyli tą samą
ruchomością, którą 6.D209 zmierzyło na sobie. Widać ją dziś na żywo: 6.D209 wymieniło
14.09 cztery twarde rozjazdy, a `odsylacz-nie-jest-wartoscia.md` / `MINIMUM_CLAIMS`
jest dziś **zwolniony**, bo `test_report_claims.py` został od tamtej pory tknięty —
bez zmiany jednej cyfry w raporcie. Zapadka na 26 albo na 22 parach rozjechałaby się
tak samo, przy pierwszej edycji dowolnego modułu niosącego cytowaną stałą.

## 6. Kontrole negatywne

Baza: **16/16** w module. `md5sum -c` `OK` po każdej.

| | podstawienie | wynik |
|---|---|---|
| KN-1 | operator odwrócony (`>` → `>=`, remis zwalnia) | **15/16** — zapala WYŁĄCZNIE kontrola syntetyczna |
| KN-2 | nowy test na remisie oślepiony (obie gałęzie zamienione) | **czerwony** |
| KN-3 | remis syntetyczny: daty równe → pilnowane; raport cofnięty o dobę → zwolnione | **oba kierunki zgodne** |

**KN-1 jest tą, która nadaje sens całej pozycji:** zmiany kierunku nie łapie dziś żadna
bramka czytająca drzewo. Gdyby kontrola syntetyczna zniknęła przy jakimś refaktorze,
operator dałoby się odwrócić **bez ani jednej czerwieni** — a razem z nim zwolnić ćwierć
populacji twierdzeń.

## 7. Czego świadomie nie zrobiłem

- **Nie zmieniłem operatora** — pomiar mówi, że `>=` jest stroną poprawną.
- **Nie przybiłem liczby remisów** ani zbioru par (§5).
- **Nie poprawiałem liczb w raportach** (6.D108), w tym dwóch rozjechanych remisów.
- **Nie tknąłem `CLAIM` ani sposobu, w jaki `data_stalej` czyta git** — oba poza
  zakresem pola.

## 8. Zauważone, nie tknięte

- **Remis `TERAZ == TERAZ`** — raport i zapadka zmienione naraz w drzewie roboczym,
  przed commitem — jest **drugim kanałem** tej samej klasy i przy pracy agenta
  najczęstszym. Na dzisiejszym drzewie zmienionych plików jest zero, więc populacji nie
  da się policzyć bez sfabrykowania zmian; kierunek wynika jednak wprost z kodu i z KN-3.
- **Zbiór twardych rozjazdów z 6.D209 zmalał z 4 na 3** bez zmiany jednej cyfry
  w raporcie — wyłącznie przez tknięcie modułu, w którym stoi cytowana stała.
