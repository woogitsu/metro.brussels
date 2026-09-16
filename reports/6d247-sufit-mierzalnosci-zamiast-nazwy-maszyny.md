# 6.D247 — sufit mierzalności zamiast nazwy maszyny

**16.09.2026**, na `bac8789`. Wejście: `tools/tests/test_suite_runtime_budget.py`
(`MIERZALNOSC_MIN`, `MASZYNA_PROGU`, `werdykt`, `POMIARY`,
`POMIARY_CPU_BIEZACEGO_DRZEWA`), `.github/workflows/python-tests.yml` (krok
„Run tool tests"), log joba `tools` z PR #633. Wyjście: podłoga 0,75 → 1,168,
pięć przepisanych bramek, dwie nowe, ten raport.

---

## 1. Co się stało

Job `tools` padł na `docker-runner-02` **przy zestawie zielonym w całości**:

```
  2497/2497 przeszło
  RAZEM 518.283 s, 2498 testów, 127 modułów
czas CPU zestawu: 517.499 s (prog 440.0 s)
##[error]zestaw test_all.py przekroczyl prog czasu CPU: 517.499 s > 440.0 s
```

Stosunek CPU/ściana **0,992**. Ten sam commit bywa zielony w **159 s ściany** na
`metro-wsl-DOM-NEW-*`.

## 2. Dlaczego nie zatrzymał tego warunek maszyny z 6.D149

Krok CI woła:

```bash
B.werdykt(float(sys.argv[1]), float(sys.argv[2]))
```

**Dwa argumenty.** `maszyna` zostaje przy wartości domyślnej `MASZYNA_PROGU`, więc
gałąź `if maszyna != MASZYNA_PROGU` **nie wykonuje się w CI ani razu**. Nic w kroku
nie czyta `RUNNER_NAME`. Rozstrzygnięcie 6.D149 broniło wyłącznie wywołań wewnątrz
modułu testowego — a w CI, czyli tam, gdzie miało działać, było gałęzią martwą
przez siedem dni.

To jest ta sama rodzina co 6.D27, tylko od drugiej strony: **przyrząd nie melduje
sprawdzenia, którego nie zrobił — on go po prostu nie robi, a komentarz obok mówi,
że robi.**

## 3. Skąd 1,168

Materiał kalibracyjny i incydent rozdzielają się bez reszty:

| zbiór | CPU/ściana |
|---|---|
| `POMIARY_RUNNERA`, 8 wpisów, `metro-wsl` | 1,599 – 1,971 |
| `POMIARY_CPU_BIEZACEGO_DRZEWA`, 8 artefaktów | 1,375 – 1,695 |
| kontener sesji, 7 wpisów | 0,987 – 0,991 |
| `docker-runner-02`, PR #633 | **0,992** |

Luka między najniższym przebiegiem kalibracyjnym (1,375) a incydentem (0,992) wynosi
**×1,386**; środek geometryczny to **1,168**.

**Zmierzone:** przy tej podłodze incydent jest **odmówiony z komunikatem**, a
**wszystkie osiem** przebiegów kalibracyjnych jest nadal **porównywanych**.

## 4. Co ta podłoga zmienia — pytanie, nie tylko liczbę

Do 16.09.2026 podłoga odpowiadała na pytanie „czy maszyna oddawała rdzenie" i
rozdzielała kontener obciążony (0,451) od spokojnego (0,987). Robiła to poprawnie
i robi nadal — ale **przestało to wystarczać**: maszyna spokojna oddająca **jeden**
rdzeń (0,992) jest od maszyny kalibracyjnej starą podłogą nieodróżnialna.

Dziś podłoga odpowiada na pytanie **„czy ten pomiar wolno postawić obok tego progu"**.
Brzegami są pasma kalibracji, nie stany obciążenia — i tak są dziś zapisane w
`test_podloga_mierzalnosci_lezy_miedzy_zmierzonymi_stanami_maszyny`.

## 5. Dlaczego nie nazwa maszyny, i dlaczego nie podniesienie progu

**Nazwa jest zakazana.** `CLAUDE.md` §9 mówi wprost: „Runnera nie wybiera się po
nazwie". Podłoga nie wymienia żadnej nazwy i nie mówi nic o liczebności puli —
mierzy wyłącznie liczbę, którą krok i tak liczy i i tak wypisuje.

**Podniesienie progu zmierzono i odrzucono.** `SUITE_CPU_BUDGET_S` stoi dziś na
**440,0** s, a okno, w którym wolno mu leżeć, wynosi od 392,95 do 441,08 s; wartość pokrywająca
`docker-runner-*` musi być **17,3 % ponad sufitem** tego okna, czyli zrywa regułę
marginesu 6.D11. Zapas nad `metro-wsl` urósłby 1,942 → 2,295 — bramka przestałaby
widzieć regres kodu do **+129 %**.

**Dopisanie nowej puli do `POMIARY` też zmierzono:** **dziesięć** padających asercji
w trzech modułach.

## 6. Czego ten wariant NIE robi — wypisane, nie przemilczane

**Na maszynie oddającej jeden rdzeń bramka milknie.** Prawdziwy regres kodu, który
trafi na `docker-runner-*`, przejdzie niezauważony — tak samo, jak dziś przechodzi
każdy przebieg kontenera. Wybór między fałszywym alarmem a ciszą został podjęty
świadomie i jest **decyzją właściciela z 16.09.2026**, nie wnioskiem agenta.

**Granica liczby, razem z nią: n = 1.** Pod podłogą stoi jeden przebieg
`docker-runner-*`. Stara 0,75 miała n = 2 i też to mówiła.

## 7. Kontrole negatywne — cztery, przewidywania zapisane przed przebiegiem

Baza modułu **37/37**. `md5sum -c` **OK** po każdej.

| # | mutacja | przewidywanie | wynik |
|---|---|---|---|
| KN-1 | podłoga cofnięta do 0,75 | 33/37 | **32/37** |
| KN-2 | podłoga podniesiona absurdalnie do 3,0 | 34/37 | **31/37** |
| KN-3 | krok CI dostaje `maszyna=` | 36/37 | **36/37** |
| KN-4 | jak KN-2, ale z drugą stroną nowej bramki zdjętą | 37/37 | **32/37** |

**KN-1 i KN-2 są parą i dopiero razem coś mówią.** Pierwsza pokazuje, że bez
podniesienia podłogi incydent nadal jest odrzucany; druga — że podłoga za wysoka
ucisza maszynę, którą próg opisuje. Bramka musi zapalać się w **obie** strony,
bo kierunek błędu jest tu cichy.

**KN-4 obaliła przewidywanie i jest przez to najważniejsza.** Spodziewałem się, że
bez drugiej strony nowej bramki mutacja „podłoga 3,0" przejdzie bez śladu. Wyszło
**32/37** — bo tę wartość łapią też cztery bramki starsze. Rozstrzygające jest więc
nie „ile", tylko **różnica**: KN-2 dała **31/37**, KN-4 **32/37**, czyli dokładnie
**jedna** bramka mniej, i jest nią właśnie ta druga strona. Bez porównania tych dwóch
liczb wniosek „ta asercja jest potrzebna" byłby nieuzasadniony.

KN-3 pilnuje, żeby nikt nie „naprawił" martwej gałęzi przez dopisanie nazwy maszyny
do kroku — czego §9 zabrania.

## 8. Weryfikacja

```
  2495/2495 przeszło
  RAZEM 222.264 s, 2495 testów, 126 modułów
```

## 9. Zauważone przy okazji, nie tknięte

`POMIARY_RUNNERA` (89,5–116,4 s ściany) i `POMIARY_CPU_BIEZACEGO_DRZEWA`
(121,7–164,7 s) to **dwa rozłączne pasma** tej samej maszyny i tego samego joba,
rozdzielone wyłącznie warunkiem wejścia; `MARGIN` liczy się z uboższej. Zauważone
już przy 6.D205 i nadal otwarte.

Dziewiąte zdanie z listy obalonych — reguła doboru logów z
`tests/data/ci-logs/README.md` §95 — każe dopisać log z `docker-runner-*`, bo
przebieg spełnia **dwa z trzech** punktów obowiązkowych. Nie dopisałem go: wpis bez
logu i log bez wpisu zapalają tę samą bramkę, a wpisu nie wolno postawić bez
przeliczenia 6.D160 i 6.D162. To jest treść osobnej pozycji.
