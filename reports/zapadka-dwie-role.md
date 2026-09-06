# Jedna stała niosła dwie sprzeczne role — i wykonanie pracy wywracało zestaw

**Zmierzone 06.09.2026 na commicie:** `154ad30`

Scalenie #272 naprawiło to, że zapadka zapasu liczyła pracę już skończoną. Naprawa
była dobra i **wprowadziła drugi defekt**, którego wtedy nie było widać: od tej chwili
domknięcie udokumentowanej pozycji **obniża licznik**, więc bramka zapala się
dlatego, że pracę wykonano.

Ten raport zapisuje, jak to wyszło, dlaczego nie da się tego obejść dyscypliną,
i co rozdzielenie dwóch ról naprawdę zmienia.

## 1. Jak wyszło — dwa razy tego samego wieczoru

| kiedy | co domknięto | licznik | bramka |
|---|---|---|---|
| #273 | 6.D4 dostaje adnotację `ZROBIONE` | 11 → 10 | czerwona |
| #274 | 6.B2 dostaje adnotację `ZROBIONE` | 11 → 10 | czerwona |

Za pierwszym razem uznałem, że bramka działa zgodnie z regułą zapasu („poniżej progu
pierwszym zadaniem jest uzupełnienie") i uzupełniłem kolejkę, dopisując blok dla 6.A3.
Zgłosiłem przy tym wątpliwość i zostawiłem ją właścicielowi.

Za drugim razem rozstrzygnęła arytmetyka, nie wątpliwość.

## 2. Dlaczego to defekt, a nie surowa reguła

Pozycji **do wzięcia i bez bloku** zostały **dwie**: 5.6 i 6.B5. Przy czym 6.B5 czeka
na decyzję o pakietach C, D i F — jej pozostała część jest zablokowana, więc
udokumentowanie jej byłoby opisaniem pracy, której nie wolno wziąć.

Zostaje realnie **jedna**. Po jej zużyciu bramki **nie dałoby się już spełnić**:
domknięta praca nie dałaby się zacommitować, bo zestaw byłby czerwony, a jedynym
lekarstwem byłoby napisanie bloku dla pozycji, której nie ma.

Bramka, której da się zadośćuczynić tylko przez chwilę, przestaje być bramką i staje
się przeszkodą do obejścia. A obejście jest tu jedno i znane: przestać adnotować
pozycje jako zrobione — czyli wrócić dokładnie do stanu, który #272 naprawiał.

## 3. Sprzeczność była w tym, że jedna liczba mierzyła dwie rzeczy

| rola | jak się zachowuje | czego pilnuje |
|---|---|---|
| **zapadka** | rośnie przez pisanie, maleje przez kasowanie | żeby blok nie zniknął po cichu |
| **zapas** | rośnie przez pisanie, **maleje przez wykonanie pracy** | żeby agent miał co brać |

„Wolno tylko podnosić" jest zdaniem sensownym dla pierwszej i **bezsensownym** dla
drugiej. Do 06.09.2026 obie role niosła stała `MINIMUM_DOCUMENTED_ITEMS`.

Po rozdzieleniu:

- **`MINIMUM_DETAIL_BLOCKS = 19`** — zapadka na liczbę napisanych bloków, niezależnie
  od tego, czy pozycja jest już zrobiona. Skasowanie bloku zapala bramkę; dopisanie
  dwudziestego wymusza podniesienie stałej w tym samym commicie.
- **`MINIMUM_DOCUMENTED_ITEMS = 6`** — podłoga alarmowa zapasu pozycji do wzięcia.
  Wolno jej opadać. Zapala się, gdy zapas naprawdę cienieje, a nie przy każdym
  domkniętym zadaniu.

Docelowa wielkość zapasu nadal wynosi **12** (`MINIMUM_READY_ITEMS`, próg doby pracy)
i odległość do niej nie znika po cichu: akapit o niedoborze musi stać w `docs/TASKS.md`,
dopóki zapas jest poniżej progu. Ten warunek też się zmienił — patrzy teraz na
**pomiar**, a nie na dwie stałe wpisane w plik testu, bo po rozdzieleniu porównanie
stałych byłoby zawsze prawdziwe, czyli martwe.

## 4. Co ta zmiana traci, a czego nie

**Nie traci ochrony przed kasowaniem bloków.** Przeniosła się na
`MINIMUM_DETAIL_BLOCKS` i jest tam **ściślejsza**: stara zapadka nie widziała
skasowania bloku pozycji już zrobionej, bo taka pozycja i tak nie liczyła się do
zapasu. Nowa widzi każdy.

**Traci automatyczny przymus uzupełniania kolejki przy każdym domknięciu.** To jest
świadome: przymus był realizowany przez czerwony zestaw, czyli przez blokowanie
commita z wykonaną pracą. Zostaje przymus miękki — akapit o niedoborze — i twardy
próg, gdy zapas zejdzie do sześciu.

## 5. Kontrole negatywne — obie WYKONANE

**Zapadka bloków** — skasowany blok `##### 6.C4`:

```
FAIL test_the_documented_ratchet_does_not_lag_behind_the_file: bloków jest 18
     przy zapadce 19 — któryś zniknął albo stracił jedno z sześciu pól
```

**Podłoga zapasu** — podniesiona z powrotem do progu doby pracy, czyli przywrócenie
starego zachowania:

```
FAIL test_the_documented_reserve_does_not_regress: pozycji z kompletem sześciu pól
     jest 11 przy zapadce 12
FAIL test_the_ratchet_cannot_be_set_above_what_it_guards: podłoga zapasu stoi poza
     przedziałem (0, próg doby pracy)
FAIL test_the_reserve_floor_falls_when_work_is_done_and_the_ratchet_does_not: podłoga
     zapasu zrównana z progiem doby pracy — domknięcie udokumentowanej pozycji znowu
     będzie wywracać zestaw
```

Trzecia bramka jest nowa i mówi wprost, czego pilnuje: **podłoga zrównana z progiem
przywraca defekt**. Bez niej ktoś podniósłby ją „dla porządku" i wróciłby do punktu
wyjścia, nie wiedząc o tym.

Do tego test na sztucznym planie z jedną pozycją, sprawdzający obie strony naraz:
adnotowanie jej jako `ZROBIONE` **zmniejsza zapas o jeden i nie zmienia liczby
bloków**. Sztuczny plan, a nie `docs/TASKS.md`, żeby test nie zależał od tego, ile
pozycji stoi dziś w kolejce.

## 6. Czego ten commit nie zrobił

- **Nie zdjął z kolejki ani jednej pozycji z adnotacją `ZROBIONE`.** Teraz już nic
  tego nie blokuje — nie liczą się do zapasu, a bloki liczy osobna zapadka. Ale gdzie
  mają wylądować, to osobna decyzja i osobne porządkowanie.
- **Nie ruszył progu doby pracy.** `MINIMUM_READY_ITEMS` zostaje na dwunastu; zmiana
  dotyczy tego, **jak** się go pilnuje, nie **ile** wynosi.

## 7. Weryfikacja — rzeczywiste wyjście

```
$ python3 tools/tests/test_all.py
  1628/1628 przeszło
```
