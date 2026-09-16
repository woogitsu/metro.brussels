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

## 8. Przegląd adwersaryjny własnej zmiany — cztery usterki, dwie krytyczne

Sekcja dopisana 16.09.2026, po przejrzeniu tej zmiany pod kątem „co w niej jest
zielone nad konfiguracją, dla której powstało". **Wszystkie cztery były moje i żadnej
nie znalazłem przy pisaniu.**

### 8.1. Czytnik kroku brał PIERWSZE wystąpienie nazwy — KRYTYCZNE

`_tekst_kroku_werdyktu()` szukał `text.index("Run tool tests")`. Krok o nazwie
zawierającej tę frazę wystarczy postawić **wyżej**, żeby czytnik oddawał jego treść.
Zmierzone podstawieniem: krok-atrapa `Sonda Run tool tests` przed krokiem prawdziwym,
a w prawdziwym `B.werdykt(maszyna=os.environ.get('RUNNER_NAME',''), …)` — czyli
dokładnie to, czego `test_krok_CI_NIE_podaje_nazwy_maszyny…` zabrania:

```
FAIL test_ci_gate_step_is_a_comparison_that_can_exit_non_zero
FAIL test_krok_ci_czyta_prog_CPU_z_tego_pliku_a_nie_z_drugiej_kopii
FAIL test_krok_ci_mierzy_czas_cpu_zestawu_a_nie_tylko_sciane
34/37 przeszło
```

**Bramka o nazwie maszyny była wśród ZIELONYCH.** Trzy czerwienie pochodzą od
starszych sąsiadek, które czytają krok po swojemu, i trafiły przypadkiem.

Asercja na jednokrotność stoi teraz **w czytniku**, nie w teście — inaczej każdy jego
użytkownik musiałby ją powtórzyć, a to jest druga kopia, przed którą broni 6.D213.
Ta sama mutacja daje po poprawce **32/37**, a bramka o nazwie maszyny czerwieni się
z własnym komunikatem.

### 8.2. Podłoga nie była przybita NICZYM — KRYTYCZNE

Podmiana `MIERZALNOSC_MIN` z `1.168` na `1.0` dawała **37/37 przeszło**. Przy 1,0
incydent `docker-runner-02` (0,992) leży już tylko **o 0,008** pod podłogą, a cały
akapit o „środku geometrycznym luki" staje się nieprawdą — po cichu. Liczba, którą da
się przesunąć bez zapalenia czegokolwiek, jest liczbą, o której proza mówi, a drzewo
nie wie.

`test_podloga_mierzalnosci_JEST_PRZYBITA_do_pomiaru_z_ktorego_wyszla` przybija ją do
**wyliczenia**, a nie do samej siebie: średnia geometryczna najniższego przebiegu
kalibracyjnego (1,3752) i przebiegu odmówionego (0,9916) wynosi **1,1677**. Dopisanie
nowego przebiegu do któregokolwiek zbioru **przelicza** podłogę zamiast ją unieważniać.
Ta sama mutacja daje po poprawce **37/39** z komunikatem podającym obie liczby.

### 8.3. Cisza wariantu (d) jest szersza, niż mówiła proza — LICZBĄ

Akapit nad stałą mówił, że na maszynie oddającej jeden rdzeń bramka MILKNIE, i to jest
prawda ogólna. Czego nie mówił: milknie także na przebiegu przekraczającym próg CPU
o **ćwierć**, bo o dopuszczeniu do porównania decyduje **wyłącznie stosunek**, a ten
może być niski przy CPU dowolnie wysokim.

| ściana | CPU | stosunek | % progu CPU | werdykt |
|---|---|---|---|---|
| 471,700 s | 550,400 s | **1,167** | **125 %** | `odrzuc=False` |

Pod starą podłogą 0,75 ten przebieg byłby **odrzucony**. Nie żądam, żeby tak nie było —
wariant (d) wybrał właściciel i cisza jest jego świadomą ceną. Żądam, żeby ta cena
stała w drzewie jako **przypadek z liczbami**, a nie jako zdanie o „maszynie oddającej
jeden rdzeń": pilnuje tego
`test_podloga_UCISZA_regres_ktory_stara_podloga_by_zlapala_i_to_jest_LICZBA`.

### 8.4. Trzy zdania stały się nieprawdą i nie zostały przepisane

Wszystkie trzy mówiły o podłodze **0,75** w czasie teraźniejszym i wszystkie są teraz
przepisane, a nie dopisane obok:

- akapit „kontener przekracza próg i podłoga go NIE zatrzymuje" — dziś **zatrzymuje**;
- pole opisowe wpisu `POMIARY` z 11.09.2026, niosące to samo zdanie;
- zdanie w `werdykt`, że kontener „przechodzi pierwszy warunek, wysoko nad podłogą 0,75"
  — dziś nie przechodzi **ani jednego**.

Czwarta poprawka jest o **położeniu**, nie o treści: deklaracja `0,75 -> 1,168` stała
**pod** całym wyprowadzeniem starej liczby, więc czytający od góry napotykał zdania
w czasie teraźniejszym o liczbie, której już nie ma. Marker przeszłości stoi teraz
na **szczycie** bloku. Jest to dokładnie ta pomyłka, przed którą `CLAUDE.md` §9
przestrzega przy własnym akapicie o etykietach runnera — i popełniłem ją w tym samym
commicie, w którym tamten akapit czytałem.

### 8.5. Czego NIE zrobiłem i dlaczego

`reports/mierzalnosc-czasu-zestawu.md` **nie został tknięty**, choć mówi o podłodze
0,75. Jest raportem z 09.09.2026 i w swoim dniu był prawdziwy, a **6.D108 zabrania
przepisywać raporty**. Zamiast tego moduł, który do niego odsyła w pięciu miejscach,
niesie teraz zdanie o tym, że odnośnik prowadzi do liczby poprzedniej, i wskazuje ten
raport jako miejsce wyprowadzenia dzisiejszej.

## 9. Weryfikacja

```
  2497/2497 przeszło
  RAZEM 210.675 s, 2497 testów, 126 modułów
```

Zapadka `ASERCJI_NAPISOWYCH_RAZEM` podniesiona 896 → **897** z powodem wpisanym
w komentarzu: doszła jedna asercja na komunikacie werdyktu, bez której nowy test byłby
zielony także wtedy, gdyby podłoga pomijała porównanie **milcząc**.

## 10. Zauważone przy okazji, nie tknięte

`POMIARY_RUNNERA` (89,5–116,4 s ściany) i `POMIARY_CPU_BIEZACEGO_DRZEWA`
(121,7–164,7 s) to **dwa rozłączne pasma** tej samej maszyny i tego samego joba,
rozdzielone wyłącznie warunkiem wejścia; `MARGIN` liczy się z uboższej. Zauważone
już przy 6.D205 i nadal otwarte.

Dziewiąte zdanie z listy obalonych — reguła doboru logów z
`tests/data/ci-logs/README.md` §95 — każe dopisać log z `docker-runner-*`, bo
przebieg spełnia **dwa z trzech** punktów obowiązkowych. Nie dopisałem go: wpis bez
logu i log bez wpisu zapalają tę samą bramkę, a wpisu nie wolno postawić bez
przeliczenia 6.D160 i 6.D162. To jest treść osobnej pozycji.
