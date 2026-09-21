# 6.D339 · Więcej niż jeden zapis ma TYLKO sekunda — a po odjęciu mianowników ułamka ma ich DWA, nie trzy

**Data:** 20.09.2026 · **Gałąź:** `claude/new-session-1xabcy` · **Baza:** `4e6b275`

**Daty pomiaru NIE przepisuję na dzisiejszą: liczby poniżej zmierzono 20.09.2026 na bazie `4e6b275` i to jest ich data.**

**POMIARU NIE POWTÓRZYŁEM DZIŚ i mówię o tym wprost, zamiast napisać, że powtórzyłem.** Przyrząd, który te liczby policzył, **nie został zachowany** — w katalogu roboczym tej pozycji leży jego wyjście, a nie kod. Odtworzenie liczb wymagałoby napisania czytnika od nowa, a czytnik napisany od nowa mierzy własną definicję, nie tamtą: doraźna próba, którą zrobiłem przed commitem, dała `m` 664 zamiast 189 i `s` 80 zamiast 7, bo liczyła każde wystąpienie identyfikatora, a nie deklaracje przesiane sitem z 6.D330. Obala to **mój doraźny licznik**, a nie liczby poniżej — i właśnie dlatego nie wpisuję jego wyniku jako sprawdzenia.

Jest to dokładnie ta wada, którą 6.D337 policzyło w siedemdziesięciu jeden raportach: liczba bez dowodu, z którego dałoby się ją odtworzyć. Zapisuję ją przy własnym raporcie, bo inaczej ten raport byłby siedemdziesiątym drugim.

6.D330 §4 zmierzyło, że sekunda pada w nazwach jako `S` (7), `Seconds` (20)
i `Second` (4), a metr wyłącznie jako `M` (189). Ta pozycja **liczy i wypisuje
imiennie**; ujednolicenie zapisu jest decyzją właściciela i jest wykluczone.

---

## 1. Kontrola przyrządu ZDANA

```
   sekunda                s(7), second(4), seconds(20)
   metr                   m(189)
```

Sekunda z trzema zapisami, metr z jednym — obie liczby z 6.D330 §4 odtworzone
co do jedynki.

## 2. ODPOWIEDŹ NA PYTANIE ZADANE WPROST: jedna jednostka, nie kilka

```
=== JEDNOSTKI Z WIECEJ NIZ JEDNYM ZAPISEM: 1 ===
   sekunda                s(7), second(4), seconds(20)
```

**Więcej niż jeden zapis ma dokładnie jedna jednostka z dziewiętnastu.**
Przewidywanie N2 („co najmniej trzy") jest **obalone**, a warunek obalenia
spisałem przed pomiarem i wypełniam go: **sekunda jest wypadkiem, a nie wzorcem.**
Nie rozciągam pojęcia „zapisu", żeby liczba urosła — `mm`, `km`, `m2`, `us`, `ms`
liczę jako **inne jednostki** (mili-, kilo-, kwadratowy), a nie jako drugi zapis
metra czy sekundy, i mówię o tym wyborze wprost, bo przy innym zaliczeniu
odpowiedź brzmiałaby inaczej.

Pełny rozkład dziewiętnastu zapisów:

```
metr           m     189 | m/s²        mps2  11 | metr (mili)  mm     5
sekunda        seconds 20| metr na s   mps    9 | m/s³         mps3   3
               s       7 | dżul        j      9 | kWh          kwh    2
               second   4| km/h        kmh    8 | procent      percent 2
kilogram       kg      7 | stopień     deg    5 | niuton       n      2
                         |                       | wat          w      2
                         |                       | sekunda (µ)  us     2
                         |                       | piksel       px     1
                         |                       | metr kw.     m2     1
```

## 3. GŁÓWNE ZNALEZISKO: wszystkie cztery `Second` to MIANOWNIK, nie przyrostek

Pole ostrzegało, że `Second` po przyimku `Per` nie jest przyrostkiem jednostki
wielkości, tylko mianownikiem ułamka, i że klasa, która tego nie rozróżni, policzy
gramatykę jako rozjazd zapisu. **Ostrzeżenie sprawdziło się w komplecie:**

```
=== MIANOWNIK UŁAMKA (po `Per` albo `_per_`) ===
   sekunda   second   ControlNotchRatePerSecond
   sekunda   second   RatePerSecond
   sekunda   second   StepsPerSecond
   sekunda   second   _ratePerSecond
   kilogram  kg       resistance_per_kg
   RAZEM: 5
```

**Cztery z czterech wystąpień `Second` stoją po `Per`.** Nie ma ani jednego
`…Second` oznaczającego wielkość w sekundach.

**Po odjęciu mianowników sekunda ma DWA zapisy, nie trzy:** `S` (7) i `Seconds`
(20). Przewidywanie N3 trafione, i trafione co do litery — „większość" okazała się
całością.

## 4. Zapis dzieli się po korpusach, i to ostro

```
   zapis      razem   src/   tools/
   seconds       20     20        0
   s              7      2        5
```

**`Seconds` nie pada w `tools/` ani razu, a `S` pada tam w pięciu nazwach na
siedem.** Przewidywanie N4 („`src/` woli słowo, `tools/` skrót") trafione — i to
nie jako tendencja, tylko jako podział prawie rozłączny.

Nazwy imiennie:

* **`Seconds` (20, wszystkie `src/`):** `CarrySeconds`, `CheckSeconds`,
  `CloseSeconds`, `ClosingWarningSeconds`, `CpuSeconds`, `DefaultTimeLimitSeconds`,
  `DwellRemainingSeconds`, `DwellSeconds`, `HeadwaySeconds`, `MinimumDwellSeconds`,
  `OpenSeconds`, `PassengerExchangeSeconds`, `SpanSeconds`, `TimeSeconds`,
  `UnlockSeconds`, `WallSeconds`, `_departedAtSeconds`, `_passengerExchangeSeconds`,
  `_turnbackSeconds`, `timeLimitSeconds`.
* **`S` (7, z czego 5 w `tools/`):** `FirstDepartureS`, `LastArrivalS` (`src/`);
  `KOSZT_PODPROCESU_S`, `OSM_API_SLEEP_S`, `SUITE_CPU_BUDGET_S`,
  `SUITE_RUNTIME_BUDGET_S`, `limit_s` (`tools/`).

**Podział pokrywa się z konwencją nazewniczą, a nie z niechlujstwem:** `src/` pisze
PascalCase i słowo się w nim mieści, `tools/` pisze `ALLCAPS_Z_PODKRESLENIEM`
i `_S` jest tam naturalnym zakończeniem. Nie jest to jednak reguła zapisana
nigdzie — `docs/04-conventions.md` nie mówi o zapisie jednostki ani słowem.

## 5. Przewidywania — cztery trafione, dwa obalone

| # | przewidywanie | wynik |
|---|---|---|
| N1 | kontrola przyrządu przejdzie | **trafione** (§1) |
| N2 | jednostek z więcej niż jednym zapisem co najmniej trzy | **OBALONE**: jedna (§2) |
| N3 | większość drugich zapisów sekundy to mianownik | **trafione**: cztery z czterech (§3) |
| N4 | zapis dzieli się po korpusach | **trafione**, podział prawie rozłączny (§4) |
| N5 | metr zostanie przy jednym zapisie | **trafione**: `M` 189, i to po dołożeniu `tools/` |
| N6 | jakaś jednostka ma drugi zapis o jednym wystąpieniu | **OBALONE**: najmniejszy drugi zapis to `second` z czterema, a i ten jest mianownikiem |

## 6. Czego świadomie nie zrobiłem

Nie ujednoliciłem zapisu, nie przemianowałem żadnej nazwy, nie postawiłem bramki na
zapisie jednostki, nie tknąłem `docs/04-conventions.md`, `src/` ani `data/` —
wszystko to stoi w polu „Poza zakresem".

**Nie zaliczyłem przedrostków jako drugiego zapisu** (§2). Przy zaliczeniu
odwrotnym metr miałby cztery zapisy (`m`, `mm`, `km`, `m2`), a sekunda pięć —
i odpowiedź na pytanie pola brzmiałaby „większość jednostek". Wybór stoi tutaj
jawnie, żeby dało się go sprawdzić bez czytania mojego kodu.

## 7. Co zauważyłem przy okazji, ale nie tknąłem

`resistance_per_kg` jest **jedynym** mianownikiem ułamka zapisanym po polsku-
pythonowemu (`_per_`), przy czterech zapisanych po angielsku-c-sharpowemu (`Per`).
Jest też jedyną nazwą, w której mianownik stoi na ostatnim członie, a licznik
w ogóle nie pada — „opór na kilogram" nie mówi, opór czego. Nie jest to usterka
i nie pilnuje tego żadna bramka.
