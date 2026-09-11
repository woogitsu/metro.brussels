# 6.D137 — koperta mówi dziś, czy wybrana masa jest przybliżona, i robi to dla obu wariantów

**11.09.2026**, na `13d6e57`. Pozycja: wypis `[KOPERTA]` nazywa masę AW0 po imieniu
i milczy o tym, że jest przybliżona — a przybliżenie dotyczy **jednego z dwóch**
wariantów, więc wiersz powtórzony bez rozróżnienia mówiłby nieprawdę o drugim.

## 1. Rozróżnienie, które trzeba było zrobić

| wariant | parametr | wpis rejestru | status | `approximate` |
|---|---|---|---|---|
| `AW0` | `aw0_kg` | `parameters.empty_mass_kg` | `spec` | **true** |
| `AW2` | `aw2_kg` | `reference_model.aw2_model_mass_kg` | `design_model` | — |

`AW0` jest przybliżona, bo źródło mówi „STIB states **approximately** 170 tonnes".
`AW2` przybliżona **nie jest** — jest świadomym założeniem symulatora, a to jest inna
rzecz niż niepewność źródła. Wiersz wypisany bez tego rozróżnienia mówiłby
o niepewności tam, gdzie źródła nie ma wcale.

## 2. Oba warianty mają WYKONANY przebieg

Rozkład syntetyczny (prawdziwy wymaga GTFS, którego w drzewie nie ma), `main()`
wołane przez CLI:

```
$ python3 tools/physics/schedule_envelope.py --timetable … --mass AW0 --out …
[KOPERTA] 3 odcinków, masa AW0 170000 kg, hamulec 1.10 m/s², zryw 0.75 m/s³
[KOPERTA] masa AW0 jest PRZYBLIŻONA (rejestr, approximate: true) — STIB states
          approximately 170 tonnes; retain approximation explicitly.

$ … --mass AW2 …
[KOPERTA] 3 odcinków, masa AW2 221940 kg, hamulec 1.10 m/s², zryw 0.75 m/s³
[KOPERTA] masa AW2 nie jest oznaczona jako przybliżona w rejestrze
```

Wypisy różnią się **dokładnie tym jednym zdaniem**. Zdanie stoi w **obu**, także
w przeczącym — milczenie byłoby nieodróżnialne od braku sprawdzenia, czyli ta sama
zasada, którą 6.D113 zapisało dla licznika bajtkodu, a 6.D132 rozwinęło.

Raport JSON niesie `mass_approximate` i `mass_approximate_note`, żeby zdanie nie
ginęło przy czytaniu pliku zamiast konsoli.

## 3. Skąd bierze się odpowiedź

Z **rejestru**, przez `braking.parametry_przyblizone` — czyli z tej samej tabeli
`PARAMETRY`, z której `params` buduje model. Własny zbiór nazw byłby drugą kopią wiedzy
„co jest przybliżone" i rozjechałby się przy pierwszej zmianie w `data/`. Kontrola
KN-2 mierzy to wprost.

## 4. Znalezione po drodze: cicha podmiana masy

`envelope` miało `mass_kg = cfg["aw0_kg"] if mass_key == "AW0" else cfg["aw2_kg"]`.
Każda nazwa spoza `"AW0"` — literówka `AWO`, pusty napis, `aw0` małymi literami —
dawała **po cichu masę obciążoną**. Z CLI to nie wychodziło (argparse dopuszcza dwie
wartości), ale `envelope` jest wołane też z testów i z kodu.

Dziś odwzorowanie stoi w `PARAMETR_MASY`, w **jednym** miejscu: czyta je i `envelope`,
i wypis o przybliżeniu, i `choices` w argparse. Nieznany wariant to `ValueError`,
nie cicha masa obciążona.

## 5. Kontrole negatywne

Baza `test_schedule_envelope.py`: **27/27** (było 22). `__pycache__` czyszczony przed
każdym przebiegiem, przywracanie przez `cp`, po każdej `md5sum -c` → `OK` na obu plikach.

| kontrola | zmiana | wynik |
|---|---|---|
| KN-1 | wiersz o przybliżeniu wypisywany zawsze, bez rozróżnienia | **26/27** |
| KN-2 | flaga rozpoznawana po nazwie wariantu, nie z rejestru | **26/27** |
| KN-3 | powrót do wyrażenia warunkowego w `klucz_masy` | **26/27** |
| KN-4 | raport bez flagi, wypis zostaje | **25/27**, dwa testy |
| KN-5 | argparse z własną listą wariantów | **26/27** |

KN-2 jest tu najważniejsza: podstawia rejestr probny z **odwróconymi** flagami
(AW0 bez przybliżenia, AW2 z nim) i żąda, żeby odpowiedź się odwróciła. Bez niej test
przeszedłby tak samo na funkcji rozpoznającej przybliżenie po napisie `"AW0"` — czyli
mierzącej własną nazwę zamiast danych.

KN-3 odtwarza usterkę z §4: po powrocie do wyrażenia warunkowego `klucz_masy("AWO")`
znów daje `aw2_kg` bez słowa.

## 6. Weryfikacja

```
  27/27 przeszło        test_schedule_envelope.py   (było 22)
  2346/2346 przeszło, 122 moduły, KOD=0, RAZEM 168.471 s
  Passed!  - Failed: 0, Passed: 601   (dotnet test tests/Sim.Tests)
```

## 7. Uzupełnienie kolejki w tym samym commicie

Domknięcie 6.D137 zbija kolejkę z dwunastu pozycji DO WZIĘCIA na **jedenaście**, czyli
poniżej progu z `CLAUDE.md` §8. Uzupełnienie idzie tym samym commitem — z tej samej
arytmetyki, co przy 6.D96, 6.D102, 6.D125 i 6.D131.

| nowa | skąd |
|---|---|
| 6.D147 · trzy ostrzeżenia składni w `tools/` | z 6.D136, 112 wierszy w logu |
| 6.D148 · krok `compileall` w jednym workflow z dziesięciu | z 6.D136, „czego nie zrobiłem" |
| 6.D149 · podłoga nie broni przed spokojną maszyną nad progiem | z 6.D135, KN-5b |
| 6.D150 · `station-depths.csv` poza zasięgiem skanu | z 6.D134, „czego nie zrobiłem" |
| 6.D151 · 17 z 21 wolnych zapadek to progi `MIN_` | z 6.D133, rozkład klas |
| 6.D152 · lista pomiarów utrzymywana ręcznie | z 6.D135, `timing_record.py` |

**Cztery z sześciu wyszły z pola „Czego nie zrobiłem" poprzednich pozycji** — czyli
z granic, które sam nazwałem zamiast przemilczeć. `MINIMUM_DETAIL_BLOCKS`, podniesiona
z 219 na 225, wartością z `len(detail_sections(...))` na pliku po edycji.

Pozycji DO WZIĘCIA po uzupełnieniu: **18**.

## 8. Czego nie zrobiłem

* **Nie propagowałem niepewności przez model** i nie ruszałem wartości w `data/` —
  oba wprost w „Poza zakresem". Wypis mówi, że liczba jest przybliżona; **o ile**,
  nie mówi, bo rejestr tego nie podaje.
* **Nie dopisałem zdania o przybliżeniu do pozostałych wypisów fizyki.** `braking.report()`
  ma swój wiersz od 6.D124 i mówi o parametrach rejestru; `schedule_envelope` mówi
  o wybranej masie. To dwa różne zdania i scalenie ich wymagałoby jednego wypisu dla
  dwóch narzędzi.
* **Nie zbudowałem przebiegu na prawdziwym rozkładzie.** Wymaga GTFS-a STIB, którego
  w drzewie nie ma; przebieg syntetyczny dotyka tego samego kodu i tego samego wypisu.
