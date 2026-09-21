# 6.D345 · Klauzula zdjęłaby TRZYNAŚCIE czytników, a `None` nie zdjąłby ani jednego — bo wyłącznie `None` nie zwraca ŻADEN

**Data:** 21.09.2026 · **Gałąź:** `claude/new-session-1xabcy` · **Baza:** `9d27100`

**PRZYRZĄD ZOSTAŁ UZUPEŁNIONY PO PRZEGLĄDZIE, PRZED COMMITEM.** Osobny czytelnik zaklasyfikował dwie liczby tego raportu — sumę zwrotów (320 wobec 322 z `ast.walk`) i liczbę czytników niosących `None` (28) — jako **dowód słabszy**, bo stały w prozie, a dało się je odtworzyć tylko z `wynik.json`, nie z wyjścia przyrządu. Zarzut był słuszny. Przyrząd drukuje je teraz wprost:

```
=== SUMA ZWROTOW: MOJA DEFINICJA WOBEC `ast.walk` ===
   najblizsza otaczajaca funkcja (moja definicja): 320
   ast.walk, czyli razem z zagniezdzonymi:          322
   roznica: 2
      _png       test_png_pixels.py   walk=2 wlasne=1
      _rowne     test_backlog.py      walk=2 wlasne=1

=== ILU CZYTNIKOW NIESIE KTORY PODRODZAJ STALEJ ===
   None           28
   inna stala     10
   logiczna       19
   zwrotow bedacych stala razem: 100
   czytnikow BEZ zadnej stalej:  148
```

Pomiar powtórzony przed commitem na bazie `e2141cb` — wszystkie liczby odtwarzają się co do jedynki. Daty pomiaru NIE przepisuję na dzisiejszą.

6.D336 §2 i §6 zmierzyło, że z 322 zwrotów w klasie nierozstrzygniętej **sto** to
węzeł `Constant`, i podało **trzynaście** czytników zwracających wyłącznie stałe jako
liczbę **pochodną z rozkładu zestawów rodzajów**, a nie z osobnego przejazdu. Ta
pozycja **liczy**; klauzuli do klasyfikatora nie dopisuje.

Definicje i sześć przewidywań spisałem **przed** pomiarem, w `DEFINICJE.md`. Przyrząd
jest zachowany.

---

## 1. Populację POŻYCZAM, a nie definiuję na nowo

Przyrząd importuje `przyrzad` z katalogu roboczego 6.D335 i bierze dokładnie ten sam
filtr, którego użyło 6.D336 — klasę `ZMIENNA SPOZA ZASIEGU`. **Populacja wychodzi
204, tyle samo co tam.** Dzięki temu rozbieżność, jeśli będzie, jest rozbieżnością
metody, a nie doboru zbioru.

```
populacja POZYCZONA z 6.D336 (ZMIENNA SPOZA ZASIEGU): 204
   z nich bez znalezionej funkcji: 0
   czytnikow ze zwrotem wartosci:  204
```

## 2. Cztery liczby, których żądało pole

```
   zwraca WYLACZNIE stale:              13
   z nich wylacznie `None`:              0
   MIESZA stala z innym ksztaltem:      43
   wariant A (stala jest ksztaltem):    klasa spada o 13
   wariant B (`None` to BRAK wartosci): klasa spada o 13
```

```
   zwrotow razem:                      320
   zwrotow bedacych stala:             100
   czytnikow BEZ zadnej stalej:        148
```

**Sto zwrotów-stałych zgadza się z 6.D336 co do jedynki.**

## 3. GŁÓWNE ZNALEZISKO: ostrzeżenie pola opisuje kształt, który JEST — ale nie tam, gdzie zmieniałby liczbę

Pole ostrzegało wprost: `return None` obok `return []` to dwa różne kształty
w jednej funkcji, a czytnik zwracający `None` w gałęzi pustej jest rozstrzygalny
dopiero wtedy, gdy `None` uzna się za **brak wartości**, a nie za kształt. Dlatego
policzyłem **dwa warianty** i spisałem je przed pomiarem.

**Wyszły równe: 13 i 13, różnica ZERO.** Powód jest ostry i nie jest przypadkiem:

```
   ROZKLAD PODRODZAJOW wsrod WYLACZNIE STALYCH
   logiczna                     11
   inna stala                    2
```

**Ani jeden czytnik nie zwraca wyłącznie `None`.** `None` w tej populacji nosi
**28 czytników** — ale **wszystkie** są w klasie mieszającej, czyli dokładnie
w kształcie, przed którym ostrzegało pole: `None` jest tam gałęzią pustą obok
gałęzi pełnej. Ostrzeżenie opisuje więc realny i częsty kształt, a mimo to
rozstrzygnięcie „czy `None` jest kształtem" **nie zmienia szukanej liczby o nic**,
bo cała klasa, której by dotyczyło, leży poza „wyłącznie stałymi".

Przewidywanie **P5 jest obalone**, a warunek obalenia spisałem przed pomiarem
i wypełniam go co do słowa: **ostrzeżenie pola opisuje rozróżnienie bez wpływu na
liczbę.** Nie znaczy to, że ostrzeżenie było zbędne — bez policzenia obu wariantów
nie dałoby się tego powiedzieć, a z jednym wariantem liczba 13 wyglądałaby na wybór.

## 4. Liczba pochodna z 6.D336 pokrywa się z osobnym przejazdem

```
   6.D336 podalo 13 czytnikow zwracajacych wylacznie stale (liczba POCHODNA
   z rozkladu zestawow rodzajow). Osobny przejazd daje 13.
```

Przewidywanie **P6 jest obalone** — zakładałem, że liczba pochodna z rozkładu
zestawów nie pokryje się z przejazdem. Pokryła się, i jest to **zdanie mocniejsze,
niż się spodziewałem**: rozkład zestawów rodzajów niósł tę informację dokładnie,
a nie w przybliżeniu.

## 5. ROZBIEŻNOŚĆ, KTÓREJ NIE UZGADNIAM: 320 zwrotów wobec 322

Moja suma zwrotów wynosi **320**, a 6.D336 podało **322**. Nie dopasowuję swojej
liczby do tamtej; nazywam przyczynę, bo ją zmierzyłem:

```
ast.walk (jak 6.D336): 322   najblizsza funkcja (moje): 320
   _png      test_png_pixels.py    walk=2 wlasne=1
   _rowne    test_backlog.py       walk=2 wlasne=1
```

`ast.walk(fn)` schodzi **do funkcji zagnieżdżonych**, więc zwrot domknięcia liczy się
tam do funkcji zewnętrznej. Moja definicja, spisana przed pomiarem, przypisuje zwrot
do **najbliższej otaczającej** funkcji — bo domknięcie doklejałoby swój kształt
cudzemu czytnikowi. **Dwa czytniki w całej populacji mają funkcję zagnieżdżoną
ze zwrotem**, i to jest cała różnica.

Obie liczby są poprawne pod swoimi definicjami. Liczby stałych to nie zmienia:
w obu podejściach wychodzi **100**, bo żaden z tych dwóch zwrotów zagnieżdżonych
nie jest stałą — sprawdziłem.

## 6. Przewidywania — cztery trafione, dwa obalone

| # | przewidywanie | wynik |
|---|---|---|
| P1 | kontrola przejdzie: `wyłącznie` + `miesza` = czytniki z choć jedną stałą | **trafione**: 13 + 43 = 56 |
| P2 | wyłącznie stałych od dziesięciu do trzydziestu | **trafione**: trzynaście |
| P3 | większość z nich zwraca wartości logiczne, nie `None` | **trafione, i skrajnie**: 11 z 13 logicznych, `None` zero |
| P4 | mieszających więcej niż wyłącznie stałych | **trafione**: 43 wobec 13 |
| P5 | wariant A i B różnią się o co najmniej pięć | **OBALONE**: różnica zero (§3) |
| P6 | moja liczba **nie** wyjdzie równa trzynastu z 6.D336 | **OBALONE**: wyszła równa (§4) |

## 7. Czego świadomie nie zrobiłem

Nie dopisałem klauzuli do klasyfikatora kształtu, nie zmieniłem żadnego czytnika,
nie postawiłem bramki, nie tknąłem `src/` ani `data/` — wszystko to stoi w polu
„Poza zakresem".

**Nie uzgodniłem swojej liczby zwrotów z liczbą 6.D336.** §5 podaje obie, nazywa
różnicę definicji i wskazuje dwa czytniki, które ją robią.

**Nie rozstrzygałem, który wariant jest właściwy.** Pytanie, czy `None` jest
kształtem, jest decyzją o klasyfikatorze; podaję obie liczby i to, że są równe.

## 8. Co zauważyłem przy okazji, ale nie tknąłem

**Sto czterdzieści osiem czytników z 204 nie zwraca ani jednej stałej** — czyli
klauzula o stałej, nawet dopisana, zostawiłaby klasę nierozstrzygniętą większą, niż
wygląda z liczby stu zwrotów. Sto zwrotów-stałych skupia się w **56 czytnikach**,
z czego 43 i tak zostają nierozstrzygnięte, bo mieszają. Liczba zwrotów i liczba
czytników mówią tu dwie różne rzeczy i łatwo wziąć jedną za drugą — zapisuję to,
bo tytuł tej pozycji („sto zwrotów to stała") brzmi jak zdanie o czytnikach, a jest
zdaniem o zwrotach.
