# 6.D135 — jedna lista na dwie maszyny dawała margines nieprawdziwy dla obu

**11.09.2026**, na `9549df6`. Pozycja pytała, którą maszynę opisuje `POMIARY`, i kazała
przeliczyć `MARGIN` z tego, co zostanie.

## 1. Stan zastany

`MEASURED_MAX_WALL_S` wynosiło **107,331 s** i pochodziło z 07.09.2026, z przebiegu
o **95** modułach. Dziś modułów jest **122**. Pole opisowe każdego wpisu mówiło coś
o warunkach („host spokojny", „kontener dzielony"), ale **wolnym tekstem**, którego nie
da się policzyć — a `MEASURED_MAX_WALL_S` brało maksimum ze wszystkich wpisów naraz.

## 2. Pomiar z 11.09.2026

Runner, sześć przebiegów CI, wszystkie przy 122 modułach — czas ściany i stosunek
CPU/ściana wzięte z wiersza werdyktu w logu joba `tools`:

| PR | ściana | CPU/ściana | testów |
|---|---:|---:|---:|
| #524 | 89,518 s | 1,971 | 2315 |
| #525 | 92,119 s | 1,857 | 2320 |
| #526 | 97,863 s | 1,801 | 2326 |
| #527 | 100,654 s | 1,810 | 2330 |
| #529 | 109,420 s | 1,610 | 2335 |
| #528 | **116,404 s** | 1,599 | 2335 |

Kontener sesji, jeden przebieg na tym samym drzewie, maszyna spokojna, zmierzony przez
`resource.getrusage(RUSAGE_CHILDREN)` wokół `subprocess.run`:

```
SCIANA 170.685 s  CPU 169.185 s  stosunek 0.991
```

## 3. Co z tego wynika — i to jest sedno pozycji

**Kontener przekracza dziś próg o 14 %, a podłoga mierzalności go NIE zatrzymuje.**
Podłoga (6.D42, `MIERZALNOSC_MIN = 0,75`) powstała po to, żeby czas maszyny
**obciążonej** nie był porównywany z progiem — zmierzone wtedy stosunki to 0,451 i 0,444
pod obciążeniem wobec 0,987 na spokojnym kontenerze. Kontener **spokojny** leży więc
wysoko nad podłogą, a jego czas ściany urósł od tamtego dnia na tyle, że dziś jest ponad
progiem. `werdykt(170.685, 169.185)` daje:

```
(True, 'zestaw test_all.py przekroczyl prog czasu sciany: 170.685 s > 150.0 s
        przy stosunku CPU/sciana 0.991 (podloga mierzalnosci 0.75)
        — maszyna oddawala CPU, wiec to jest pomiar kodu')
```

Bramka na tym nie cierpi, bo chodzi **wyłącznie na runnerze** (`python-tests.yml`,
`runs-on: self-hosted`). Cierpiała **lista**: gdyby ten wpis wchodził do maksimum, próg
150 s byłby przekroczony przez sam **zapis pomiaru**, bez jednego regresu w kodzie.

Różnica nie jest rozrzutem jednej maszyny. Runner liczy zestaw **równolegle** (stosunek
powyżej jedynki, 1,599–1,971), kontener **szeregowo** (0,991). To dwa różne sposoby
wykonania tej samej pracy i jeden próg czasu **ściany** nie opisuje obu.

## 4. Co zostało zrobione

* `POMIARY` ma piąte pole — **maszynę z zamkniętej listy** (`runner` / `kontener`),
  zamiast wolnego tekstu;
* dopisanych **siedem** przebiegów z 11.09.2026: sześć runnera i jeden kontenera;
* `POMIARY_RUNNERA` filtruje listę, a `MEASURED_MAX_WALL_S` liczy maksimum **tylko
  z niej** — bo bramka porównuje wyłącznie na tej maszynie;
* wpis kontenerowy **zostaje w liście**, choć do marginesu nie wchodzi: jest po to, żeby
  było widać, czego margines NIE dotyczy.

`MARGIN` spada z **1,397** (150 / 107,331) na **1,289** (150 / 116,404) — i to jest
liczba prawdziwa, bo policzona wobec przebiegu porównywalnego z tym, który bramka ocenia.
Progu nie ruszam („Poza zakresem").

## 5. Kontrole negatywne

Baza `test_suite_runtime_budget.py`: **17/17** (było 14). `__pycache__` czyszczony przed
każdym przebiegiem, przywracanie przez `cp`, po każdej `md5sum -c` → `OK`.

| kontrola | zmiana | wynik |
|---|---|---|
| KN-1 | maksimum znów z całej listy | **15/17**, jeden komunikat PUSTY |
| KN-1b | to samo po dopisaniu komunikatu | **14/17**, trzy testy |
| KN-2 | wpis kontenerowy z 11.09 usunięty | **15/17**, dwa testy |
| KN-3 | pole maszyny zdjęte z jednego wpisu | **15/17**, dwa testy |
| KN-4 | stała kontenera rozjechana z wpisem | **14/17**, trzy testy |
| KN-5 | strażnik podłogi osłabiony w asercji | **17/17 ZIELONA — ZŁA KONTROLA** |
| KN-5b | podłoga podniesiona ponad 0,991 | **14/17**, trzy testy |

**KN-1 znalazła usterkę w moim własnym teście, zanim znalazł ją ktokolwiek inny.**
Asercja `MEASURED_MAX_WALL_S == max(...)` nie miała komunikatu i zapaliła się jako
`FAIL test_the_recorded_maximum_is_derived_not_typed_in:` — dwukropek i nic dalej, czyli
dokładnie ta usterka, o której jest 6.D127. Dopisany komunikat obniża wpis modułu
w `NIEME_ASERCJE` z 7 na 6, w tym samym commicie, a KN-1b powtarza tę samą kontrolę
na poprawionej wersji.

**KN-5 była ZŁĄ KONTROLĄ i zapisuję to jako błąd metody, nie jako wynik.** Osłabiłem
asercję (`assert True or …`) zamiast zmienić przedmiot pomiaru — ta sama pomyłka, którą
zapisałem przy 6.D129. KN-5b robi to dobrze: podnosi `MIERZALNOSC_MIN` ponad stosunek
kontenera, po czym strażnik zapala się z właściwym zdaniem.

## 6. Weryfikacja

```
  17/17 przeszło        test_suite_runtime_budget.py   (było 14)
  2338/2338 przeszło, 122 moduły, KOD=0, RAZEM 167.604 s
```

## 7. Czego nie zrobiłem

* **Nie ruszyłem progu** `SUITE_RUNTIME_BUDGET_S` ani nie przyspieszałem zestawu — oba
  wprost w „Poza zakresem".
* **Nie zmieniłem podłogi mierzalności.** Pomiar pokazuje, że spokojny kontener jej nie
  aktywuje, ale podniesienie jej odcięłoby też zdrowe przebiegi (KN-5b pokazuje, jak
  blisko), a to jest decyzja o innej bramce niż ta pozycja.
* **Nie dopisałem pomiarów kontenera z poprzednich dni.** Sześć przebiegów z 11.09.2026
  (145,75–150,84 s) zapisanych przy 6.D122 i 6.D123 nie ma zapisanego stosunku CPU/ściana,
  więc nie dałoby się powiedzieć, czy bramka by je porównała.
* **Nie zautomatyzowałem dopisywania pomiarów.** `tools/ci/timing_record.py` mówi wprost,
  że lista jest utrzymywana ręcznie; zmiana tego jest osobną pracą.
