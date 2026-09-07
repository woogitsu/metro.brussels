# Reszta czasu przeglądu mutacyjnego (6.B20)

**Zmierzone 07.09.2026 na commicie:** `f394e0908afe7d2bf68fc6f6164948e57d377113`
**Maszyna:** 4 rdzenie (`nproc`), **współdzielona z innymi agentami przez cały pomiar**
— `uptime`/`/proc/loadavg` skakało 1,8–6,9 na 4 rdzeniach w trakcie przebiegów. Obciążenie
zapisane osobno przy każdym pomiarze niżej; to NIE jest „maszyna wolna" z 6.B17/6.B18,
więc bezwzględne liczby tego raportu i tamtego nie są bezpośrednio porównywalne —
tylko proporcje i metoda są.
**Metoda:** w odróżnieniu od 6.B18 (które zmierzyło CZĘŚCI osobno, w OSOBNYCH
uruchomieniach, i samo powiedziało, że suma się nie domyka), ten pomiar woła prawdziwe
funkcje `tools/tests/mutation_sweep.py` (`add_worktree`, `baseline_problem`,
`coverage_map`, `sweep`) **w jednym ciągłym procesie Pythona**, w tej samej kolejności,
w jakiej robi to `main()`, i znaczy `time.monotonic()` między każdym wywołaniem. Suma
odcinków jednego takiego procesu zgadza się z jego całkowitym czasem **z definicji**
(to te same znaczniki czasu) — pytanie, które zostaje, to gdzie te sekundy idą, nie
czy się zgadzają.


**Adnotacja z tego samego dnia:** gałąź została po pomiarze przestawiona na `c1f5618`
(scalenia #351 — 6.A22 — #352, #353, #354 — 6.A23 — i #355 — 6.B33). Zestaw narzędzi
przebiegł na nowej podstawie ponownie: **1852 testów, 99 modułów, kod wyjścia 0** —
dwa FAIL-e podłogi zapasu, widoczne w §7 przy pomiarze, na nowej podstawie nie
występują, bo zapas został uzupełniony osobnymi commitami (#350, #353). Czasy faz
przeglądu nie są przeliczane: to datowany pomiar na maszynie współdzielonej i jego
warunki są opisane wyżej.

**Blokator z §1 stoi w kolejce jako 6.B35, a brak strażnika na `main()` jako 6.B37**
(#358). Potwierdziłem blokator osobno, na treści `OWN_TESTS_STUB`: to sam docstring,
bez strażnika `__main__` i bez delegacji do `test_all`.

## 1. Blokator, którego dzisiaj nie da się ominąć wołaniem CLI wprost

Zanim jakikolwiek pomiar fazowy, kontrola: prawdziwe polecenie z linii komend.

```
$ python3 tools/tests/mutation_sweep.py --only tools/blender/lod_paths.py \
    --workers 1 --timeout 300 --journal /tmp/b20-smoke.jsonl
[MUTACJE] --only 'tools/blender/lod_paths.py' złapało 2 mutacji z 1 moduł(ów): tools/blender/lod_paths.py
[MUTACJE] 2 mutacji do policzenia, 1 robotników, commit f394e09, klasy operator,prog,logika,argument,przypisanie, dziennik /tmp/b20-smoke.jsonl
[MUTACJE] kalibracja wyroczni: zestaw w drzewie BEZ mutacji
[MUTACJE] PRZERWANE — zestaw PADA w czystym drzewie, bez żadnej mutacji (kod 1):
  ['test_the_documented_shortfall_is_written_down_while_it_lasts:',
   'test_the_queue_holds_at_least_a_day_of_work:',
   'test_every_module_delegates_to_the_one_runner:',
   'test_every_test_module_can_be_run_directly:']
  — dopóki tak jest, każda mutacja zostanie zapisana jako zabita, a przegląd nie mierzy niczego
total=58.772 s   rc=2
```

**Dziś `main()` NIGDY nie dochodzi do sondy pokrycia ani do robotników.** Kalibracja
wyroczni (`baseline_problem`) ma dwa niezależne, prawdziwe powody, żeby być czerwona
w KAŻDYM drzewie roboczym, jakie stworzy `add_worktree`:

1. **Zapas kolejki w `docs/TASKS.md` jest pod progiem** — `test_the_queue_holds_at_least_a_day_of_work`
   i `test_the_documented_shortfall_is_written_down_while_it_lasts` (`tools/tests/test_backlog.py`).
   To środowiskowe, niezwiązane z narzędziem mutacyjnym; poza zakresem tej pozycji
   (patrz §9).
2. **Zaślepka `neutralise_own_tests` łamie nową bramkę 6.D25.** `OWN_TESTS_STUB`
   (wiersz 415 `mutation_sweep.py`) to sam docstring — bez strażnika
   `if __name__ == "__main__"` i bez `test_all.main(__file__)`. `tools/tests/test_module_entrypoints.py`,
   dopisane w 6.D25 (`a2a0d21`, scalone **07.09.2026, PO 6.B18** — sprawdzone
   `git merge-base --is-ancestor`), wymaga strażnika w KAŻDYM `test_*.py` i sprawdza,
   że deleguje do wspólnego przebiegacza. Zaślepka nie ma ani jednego, ani drugiego,
   więc `test_every_module_delegates_to_the_one_runner` i `test_every_test_module_can_be_run_directly`
   padają w KAŻDYM drzewie z `add_worktree` — na stałe, nie tylko dziś. W prawdziwym
   repozytorium (bez zaślepki) te same dwa testy przechodzą — sprawdzone: `python3
   tools/tests/test_all.py` w katalogu głównym tego worktree nie wypisuje żadnego
   z tych dwóch w liście `FAIL` (§8).

To jest **realna, nowa usterka** (nie coś, co ten pomiar wymyślił, żeby ominąć wygodę):
od scalenia 6.D25 narzędzie `mutation_sweep.py`, wołane wprost, zawsze kończy się
kodem 2 po ~58 s, zanim policzy jedną mutację. Zgłaszam to jako znalezisko (§9) —
poprawka wykracza poza Wejście/Wyjście tej pozycji (nie jest w nich wymieniony ani
`test_module_entrypoints.py`, ani `test_backlog.py`), więc jej nie dotykam.

**Dlaczego reszta tego raportu mimo to ma liczby.** Żeby wypełnić pole „Tabela mutacji
na minutę" i domknąć rachunek czasu, którego żąda 6.B20, poniższe pomiary wołają TE
SAME funkcje (`add_worktree`, `baseline_problem`, `coverage_map`, `sweep`) bezpośrednio,
z pominięciem WYŁĄCZNIE gałęzi `if problem is not None: return 2` w `main()` — reszta
kodu, w tej samej kolejności, na tym samym drzewie. To zmienia **interpretację
werdyktów** (zabita/ocalała jest bez znaczenia, gdy baza już pada — dokładnie usterka,
przed którą `baseline_problem` broni, patrz jej docstring), ale **nie zmienia czasu
żadnej fazy**: `coverage_map` i `sweep` uruchamiają dokładnie ten sam zestaw testów
w dokładnie tym samym drzewie, niezależnie od tego, czy wynik `baseline_problem` został
odczytany, czy zignorowany. Sterownik: `tools/tests/mutation_sweep.py` zaimportowany
jako moduł (`importlib`), wołany z jednego skryptu pomiarowego — kod źródłowy
narzędzia jest nietknięty.

## 2. Pełny, ciągły przebieg — 1, 2 i 4 robotników

Moduł: `tools/blender/lod_paths.py`, **2 mutacje** (ten sam moduł co w 6.B18 — sprawdzone
`--list` przed pomiarem, liczba się nie zmieniła). Jeden przebieg na każdą liczbę
robotników, znaczniki czasu z jednego procesu:

### workers=1

```
loadavg przed: 1.89 2.47 2.46      loadavg po: 5.27 4.93 3.63
    0.0003 s  setup (collect + filtr --only)
    0.0864 s  worktree bazowe: git worktree add
   58.1318 s  kalibracja wyroczni: zestaw w drzewie BEZ mutacji + worktree remove
  426.6183 s  sonda pokrycia: zestaw z licznikiem wierszy + add/remove worktree
  115.4736 s  robotnicy: 2 mutacje SEKWENCYJNIE (1 worker) + add/remove worktree
------------------------------------------------------------
  600.3104 s  SUMA CZĘŚCI
  600.3111 s  CAŁKOWITY CZAS PRZEBIEGU (time.monotonic, start->koniec)
    0.0007 s  RÓŻNICA (0,00012 % całości)
```

### workers=2

```
loadavg przed: 5.25 4.93 3.64      loadavg po: 2.88 3.87 3.84
    0.0001 s  setup
    0.0790 s  worktree bazowe
   60.8151 s  kalibracja wyroczni
  416.7404 s  sonda pokrycia
   57.5483 s  robotnicy: 2 mutacje na 2 workerach RÓWNOLEGLE
------------------------------------------------------------
  535.1829 s  SUMA CZĘŚCI
  535.1834 s  CAŁKOWITY CZAS PRZEBIEGU
    0.0005 s  RÓŻNICA (0,00009 % całości)
```

### workers=4

```
loadavg przed: 2.89 3.86 3.84      loadavg po: 2.88 2.97 3.37
    0.0002 s  setup
    0.1077 s  worktree bazowe
   57.7937 s  kalibracja wyroczni
  416.7471 s  sonda pokrycia
   59.6120 s  robotnicy: 2 mutacje — TYLKO 2 z 4 gniazd niepuste (§4)
------------------------------------------------------------
  534.2607 s  SUMA CZĘŚCI
  534.2612 s  CAŁKOWITY CZAS PRZEBIEGU
    0.0005 s  RÓŻNICA (0,00009 % całości)
```

## 3. Skończone, gdy: suma się zgadza

**Tak, z dokładnością ≤0,0007 s na przebieg (≤0,00013 % całości), we wszystkich trzech
pomiarach.** To nie jest zbieg okoliczności — to konsekwencja metody: skoro odcinki są
znacznikami TEGO SAMEGO procesu `time.monotonic()`, ich suma równa się różnicy
pierwszego i ostatniego znacznika z dokładnością do rozdzielczości zegara. Reszta
0,0005–0,0007 s to czas między ostatnim znacznikiem (`sweep_done`) a wyjściem z bloku
`with tempfile.TemporaryDirectory()` (sprzątanie katalogu tymczasowego) plus odczyt
`time.monotonic()` po nim — nazwane, nie zgadywane.

**To domyka literalne kryterium 6.B20**, ale nie odtwarza obserwacji „ponad 20 minut"
sprzed 6.B18: trzy pełne przebiegi dają **534,3–600,3 s (8,9–10,0 min)**, średnio
**9,28 min**. Zostaje **10–11 minut**, których ten pomiar NIE tłumaczy względem tamtej
historycznej liczby — i uczciwa odpowiedź jest taka sama jak w 6.B18: nazwane wprost,
nie dociągnięte. Różnica wobec 6.B18 jest w tym, CO dokładnie się domyka: 6.B18 nie
domykało własnej sumy (~6,2 min) do własnej obserwacji; ten pomiar domyka sumę
odcinków JEDNEGO przebiegu do CAŁKOWITEGO czasu TEGO SAMEGO przebiegu — a to jest
dokładnie pole, o które prosi „Skończone, gdy" tej pozycji. Możliwe wytłumaczenia
pozostałej różnicy do „ponad 20 minut" (maszyna z historycznego zdarzenia mogła być
mocniej obciążona niż dzisiejsza; obserwacja mogła obejmować więcej niż jedno
wywołanie, np. przerwane i wznowione) są nazwane jako **hipotezy**, nie jako wynik —
nie mam z tamtego dnia ani commita, ani logu, który by je rozstrzygnął.

## 4. Dlaczego workers=2 i workers=4 wypadają tak samo

`sweep()` dzieli mutacje round-robin na `workers` list i woła robotnika TYLKO dla
niepustej listy (`if chunk`, `mutation_sweep.py` w. 744-745). Z **2** mutacjami:
`--workers 4` tworzy listy `[m0], [m1], [], []` — **dwa** gniazda są od razu puste,
więc czwarty i trzeci robotnik nigdy nie startują. `workers=4` na tym module **nie
jest** czterokrotną równoległością — jest, mechanicznie, tym samym co `workers=2`.
Zmierzone: 57,55 s (w=2) wobec 59,61 s (w=4) w pełnym przebiegu — różnica mieści się
w rozrzucie obciążenia maszyny (§5), nie w liczbie aktywnych wątków. Tabela mutacji na
minutę w §6 pokazuje to samo zjawisko liczbami.

## 5. Powtórzenia fazy robotników — rozrzut

Kalibracja i sonda pokrycia NIE zależą od liczby robotników (zmierzone: 416,7–426,6 s
niezależnie od `--workers`, patrz §2) — powtarzanie ich nie dodaje informacji, tylko
zużywa czas. Faza robotników policzona osobno jeszcze **dwa razy** na każdą liczbę
robotników (`sweep()` wołane wprost, bez kalibracji/sondy przed nią), żeby dać rozrzut:

```
                    rep0 (pełny przebieg)   rep1        rep2       rozrzut (max-min)
workers=1 [s]       115,474                116,902     116,428    1,43 s  (1,2 %)
workers=2 [s]        57,548                 59,609      62,441    4,89 s  (8,2 %)
workers=4 [s]        59,612                 58,842      66,253    7,41 s (12,0 %)
```

loadavg przy rep1/rep2 (1 min): w=1 1,78→2,69; w=2 2,69→2,96; w=4 2,96→3,38;
w=1(rep2) 3,38→4,64; w=2(rep2) 4,64→5,61; w=4(rep2) 5,61→6,94 — **rosnąco przez cały
przebieg**, maszyna coraz bardziej obciążona przez inne sesje. Rozrzut rośnie z liczbą
robotników (1,2 % przy w=1 do 12,0 % przy w=4) — spójne z tym, że więcej wątków tego
narzędzia konkuruje mocniej o te same, coraz bardziej zajęte rdzenie. **Trzy przebiegi
to nie jest duża próba**; rozrzut jest podany jako informacja o warunkach pomiaru, nie
jako precyzyjny błąd statystyczny.

## 6. Tabela: mutacje na minutę przy 1, 2 i 4 robotnikach

Dwie kolumny, bo pytają o dwie różne rzeczy: **sama faza robotników** (co dostaje
uruchomienie już rozgrzane, po kalibracji i sondzie) i **cały przebieg** (co dostaje
ktoś, kto woła narzędzie od zera).

| robotnicy | mutacji/min — SAMA faza robotników (średnia z 3 powt., §5) | mutacji/min — CAŁY przebieg (1 pomiar, §2) |
|---|---|---|
| 1 | 1,03 (2 mut. / 116,3 s śr.) | 0,20 (2 mut. / 600,3 s) |
| 2 | 2,00 (2 mut. / 59,9 s śr.) | 0,22 (2 mut. / 535,2 s) |
| 4 | 1,95 (2 mut. / 61,6 s śr.) | 0,22 (2 mut. / 534,3 s) |

**workers=2 i workers=4 są nierozróżnialne w obu kolumnach** — mechanika z §4, nie
błąd pomiaru. Podwojenie z 1 do 2 robotników prawie podwaja przepustowość SAMEJ fazy
robotników (1,03 → 2,00 mutacji/min, +94 %), ale w przeliczeniu na CAŁY przebieg
poprawia go tylko o 12 % (0,1999 → 0,2243 mutacji/min) — bo kalibracja i sonda (§2, razem
474,6–484,8 s, **80,8–89,3 % całkowitego czasu każdego przebiegu**) nie skalują się
z liczbą robotników w ogóle. Dodanie robotników przyspiesza dokładnie tę część
przeglądu, która na tym module jest najmniejsza.

## 8. Weryfikacja: `python3 tools/tests/test_all.py`, na prawdziwym drzewie (nie w worktree)

```
$ python3 tools/tests/test_all.py
       0.000 s  test_lod_paths.py  (5 testów)
  RAZEM 71.373 s, 1841 testów, 98 modułów
EXIT=1
  FAIL test_the_documented_shortfall_is_written_down_while_it_lasts: zapas udokumentowany to 11 przy progu 12, a plan o tym milczy
  FAIL test_the_queue_holds_at_least_a_day_of_work: kolejka ma 11 pozycji przy progu 12; pierwszym zadaniem jest uzupełnienie fazy 6, nie zatrzymanie się
```

**Dokładnie te dwa `FAIL` i żaden inny** — w szczególności `test_every_module_delegates_to_the_one_runner`
i `test_every_test_module_can_be_run_directly` (z 6.D25) **przechodzą** tutaj, bo
`tools/tests/test_mutation_sweep.py` w prawdziwym drzewie ma swój strażnik. Padają
WYŁĄCZNIE wewnątrz drzew z `add_worktree`, gdzie ten sam plik jest zaślepką — to
potwierdza rozpoznanie z §1 osobnym, niezależnym wywołaniem, a nie samą lekturą kodu.
Te dwa `FAIL` są stanem repozytorium sprzed tej pozycji (`git fetch origin main` na
starcie, przed jakąkolwiek zmianą) — 6.B20 nie dodała ani nie usunęła testu; delta
testów: **0** (1841 przed i po, bo Wyjście tej pozycji to raport, nie kod).

## 9. Znalezione, ale nietknięte

- **Blokator z §1 (6.D25 kontra `neutralise_own_tests`) jest realny i trwały**, nie
  tylko dzisiejszy — dotyka KAŻDE wywołanie `mutation_sweep.py` przez `main()`, na
  każdym commicie po `a2a0d21`. Nie jest w Wejściu/Wyjściu tej pozycji
  (`test_module_entrypoints.py` ani `test_backlog.py` nie są tam wymienione) i naprawa
  zmieniałaby albo zaślepkę (ryzyko: znów zawyży pokrycie, dokładnie usterka, przed
  którą broni `neutralise_own_tests` — patrz jej docstring), albo bramkę 6.D25, albo
  próg kolejki — trzy różne decyzje, żadna nie należy do pomiaru. Zgłaszam to jako
  gotowy do wzięcia wpis kolejki, nie naprawiam.
- **Zapas `docs/TASKS.md` jest pod progiem `MINIMUM_READY_ITEMS`** (`test_the_queue_holds_at_least_a_day_of_work`
  pada na starcie, §1 wyżej) — to osobna, dobrze opisana w CLAUDE.md §8 procedura
  (uzupełnienie kolejki), nie coś, co 6.B20 ma naprawiać przy okazji.
- **Sonda pokrycia dziś kosztuje 1,53–1,57× więcej niż ekstrapolacja z 6.B18** (416,7–426,6 s
  wobec ~272 s) — adnotacja dodana do `reports/czas-przegladu-mutacyjnego.md` (nie
  przeliczam tamtych liczb, patrz Twarde wymagania #4). Najbardziej prawdopodobny
  powód: 6.B18 mierzyło na maszynie z obciążeniem 0,46 (opisanym wprost w jej nagłówku)
  i EKSTRAPOLOWAŁO z przebiegu uciętego po 210 s; ten pomiar dokończył sondę do końca
  (żaden `coverage_map` nie zwrócił `None`) na maszynie z obciążeniem 1,8–6,9.
