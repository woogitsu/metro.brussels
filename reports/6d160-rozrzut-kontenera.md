# 6.D160 — kontener nie dostaje progu, a teza „n=1 to liczba z ręki" jest obalona

**13.09.2026**, na `5a6a01c`. Wejście: `tools/tests/test_suite_runtime_budget.py`,
`reports/6d149-prog-a-maszyna.md`, `reports/mierzalnosc-czasu-zestawu.md`.

Pozycja weszła z tezą: kontener ma na dzisiejszym drzewie **jeden** pomiar, a próg
z jednego pomiaru byłby liczbą wpisaną z ręki. Sześć powtórzeń tę tezę **obala**.

## 1. Sześć powtórzeń na jednym drzewie

Mierzone tym samym przyrządem, co krok CI „Run tool tests" w
`.github/workflows/python-tests.yml`: wbudowane `times` przed i po, `date +%s.%N`
na ścianie, CPU liczone funkcją `cpu_dzieci` z mierzonego modułu. Przed każdym
przebiegiem czyszczony `__pycache__` całego drzewa. Drzewo: 124 moduły, 2414 testów,
za każdym razem `2414/2414 przeszło`.

| przebieg | ściana | CPU | CPU/ściana |
|---:|---:|---:|---:|
| 1 | **171,842 s** | 169,689 s | 0,987 |
| 2 | 170,788 s | 168,669 s | 0,988 |
| 3 | 170,018 s | 167,867 s | 0,987 |
| 4 | 171,500 s | 169,407 s | 0,988 |
| 5 | **167,402 s** | 165,301 s | 0,987 |
| 6 | 171,467 s | 169,349 s | 0,988 |

Minimum 167,402 s, maksimum 171,842 s, średnia 170,503 s, odchylenie 1,508 s.
**Rozrzut: 2,65 %.** Wszystkie stosunki CPU/ściana leżą wysoko nad podłogą
mierzalności, więc to są pomiary kodu, nie zajętej maszyny.

Dla porównania sześć przebiegów **runnera** z 11.09.2026 rozrzuca się o **30,03 %**
(89,518–116,404 s). Kontener jest od maszyny, dla której próg naprawdę wyprowadzono,
**jedenastokrotnie stabilniejszy**.

## 2. Teza pozycji, obalona

**Rekord padł na przebiegu PIERWSZYM i nie ruszył się już ani razu.**

| po ilu przebiegach | maksimum |
|---:|---:|
| 1 | 171,842 s |
| 2–6 | 171,842 s |

`max(n=1)` i `max(n=6)` to **ta sama liczba**. Próg zbudowany tak jak runnerowy —
maksimum razy ten sam zapas — wypada **221,4 s** niezależnie od tego, czy weźmie się
jeden przebieg, czy sześć. Zapas nad najwolniejszym zmierzonym to 28,86 %, a sześć
przebiegów różni się o 2,65 %; zapas jest od rozrzutu **dziesięciokrotnie** szerszy.

Liczba powtórzeń **nie jest** więc tym, co czyniło taki próg wpisanym z ręki.

## 3. Czym jest naprawdę: dryf drzewa

Ta sama lista mówi, co zestarzało `MEASURED_MAX_WALL_S`, wpisane 05.09.2026 z ręki
jako 77,04 — i to nie było „za mało przebiegów":

| kiedy | modułów | ściana, maszyna spokojna |
|---|---:|---:|
| 07.09.2026 | 93 | 76,518 s |
| 07.09.2026 | 95 | 83,083 s |
| 11.09.2026 | 122 | 170,685 s |
| 13.09.2026 | 124 | 170,503 s (średnia z sześciu) |

| co | ile |
|---|---:|
| rozrzut POWTÓRZEŃ, to samo drzewo | 2,65 % |
| dryf DRZEWA, 93 → 124 modułów | 122,83 % |
| dryf większy od rozrzutu | **46,3 raza** |

Powtórzenia zmniejszają niepewność, która jest **czterdzieści sześć razy mniejsza**
od tej, która naprawdę rusza maksimum. Żadna ich liczba dryfu nie naprawia, bo mierzą
co innego.

## 4. Rozstrzygnięcie: kontener progu NIE dostaje

Nie dlatego, że nie dałoby się go wyprowadzić — dałoby się, i punkt 2 pokazuje, że
byłby tą samą liczbą przy jednym przebiegu i przy sześciu. Dlatego, że **nie zmieniłby
ani jednego werdyktu**, a starzałby się dryfem jak ten, który 6.D26 z tego pliku
usuwało.

**Po pierwsze, nie miałby kogo pytać.** W całym drzewie `werdykt` woła jedno miejsce
produkcyjne: krok „Run tool tests" w `.github/workflows/python-tests.yml`, a ten
workflow ma `runs-on: self-hosted`. Woła go **bez** argumentu `maszyna`, czyli zawsze
o runnerze. Argument istnieje dla pomiarów spoza CI (6.D149) i żadna automatyka go
nie podaje.

**Po drugie, byłby bezczynny wobec całego zapisu.** Próg 221,4 s wobec ośmiu
przebiegów kontenera w liście:

```
prog hipotetyczny = 221.438 s
2026-09-05    77.040 s  -> nad progiem: False
2026-09-07    76.518 s  -> nad progiem: False
2026-09-07   102.122 s  -> nad progiem: False
2026-09-07    83.083 s  -> nad progiem: False
2026-09-07   107.331 s  -> nad progiem: False
2026-09-11   170.685 s  -> nad progiem: False
2026-09-13 (szesc)  max  171.842 s  -> nad progiem: False
```

**Po trzecie, jedyny przebieg kontenera nad tą liczbą jest odrzucany wcześniej i nie
przez próg.** Incydent z 08.09.2026 (335,668 s) ma stosunek CPU/ściana 0,211, czyli
odpowiada mu podłoga mierzalności, zanim próg zostanie w ogóle zapytany. Liczone
`werdykt`, nie opowiedziane:

```
werdykt(335.668, 70.8, budget_s=221.438) -> (False,
  'stosunek CPU/sciana 0.211 jest ponizej podlogi 0.75, wiec czas sciany
   335.668 s NIE JEST porownywany z progiem 221.43826672622936 s — ten pomiar
   nie mowi nic o kodzie, tylko o maszynie, na ktorej go zrobiono')
```

## 5. Co weszło do kodu

Sześć wpisów do `POMIARY` (zapis pomiaru, nie druga kopia liczb) i dwa testy, które
pilnują obu połówek rozstrzygnięcia — bo obie są zdaniami o liczbach, które mogą się
ruszyć. Wartości progu i podłogi **nietknięte**: `SUITE_RUNTIME_BUDGET_S` to nadal
150,0, `MIERZALNOSC_MIN` to nadal 0,75, a `MEASURED_MAX_WALL_S` nadal 116,404, bo
bierze wyłącznie przebiegi runnera i tych nie ruszałem.

## 6. Tautologia, którą znalazłem we WŁASNYM teście, zanim wyszedł z pozycji

Pierwsza wersja testu progu hipotetycznego liczyła go z **tej samej listy**, na której
potem szukała przekroczeń:

```
kontenerowe = [... wszystkie wpisy kontenera ...]
prog_hipotetyczny = max(kontenerowe) * MARGIN
nad_progiem = [s for s in kontenerowe if s > prog_hipotetyczny]
```

Przy zapasie większym od jedynki `max(L) * zapas` **nie jest przekraczalne przez żaden
element `L`**. Asercja nie mogła zapalić się nigdy — czyli byłaby kontrolą pustą
z konstrukcji, tą samą rodziną, którą projekt tropi od 6.D27. Poprawka: próg liczony
z sześciu powtórzeń, sprawdzany na wszystkich wpisach kontenera.

Że poprawka coś zmienia, zmierzone **parą na identycznym wejściu** — wpis kontenera
250 s dopisany do listy (250 s dobrane tak, żeby strażnik incydentu trzymał w obu
wersjach, więc różnica pochodzi z samej asercji, a nie ze strażnika):

| wersja | wynik |
|---|---|
| naprawiona | **czerwona**: „prog hipotetyczny 221.438 s zapalilby sie na przebiegach [250.0]" |
| tautologiczna | **zielona** |

## 7. Kontrole negatywne

Baza: **21/21**. Po każdej `cp` z kopii roboczej i `md5sum -c: OK`. Przed każdym
przebiegiem czyszczony `__pycache__`; po każdym podstawieniu `diff` z kopią roboczą
i `assert` na dokładnie jednym wystąpieniu wzorca.

| | mutacja | wynik | co mówi |
|---|---|---|---|
| KN-1 | jeden z sześciu przebiegów rozjeżdża się (167,402 → 240,0) | **19/21** | rozrzut i pokrycie zapasem są mierzone, nie deklarowane |
| KN-2 | jedno z sześciu powtórzeń usunięte | **20/21** | liczba powtórzeń jest pilnowana, tak jak żąda pole „Weryfikacja" |
| KN-3 | stosunek jednego powtórzenia pod podłogą (0,987 → 0,700) | **20/21** | połowa o mierzalności nie jest ozdobą |
| KN-4 | dopisany wolny przebieg kontenera spoza sześciu (300 s) | **19/21** | próg hipotetyczny widzi wpis, którego nie zbudował |
| KN-5 | incydent 08.09 dostaje CPU rzędu ściany (70,8 → 300,0) | **20/21** | zdanie o podłodze przed progiem jest wykonywane, nie opisane |

## 8. Kolejka

Domknięcie tej pozycji zbija zapas o jeden. Uzupełnienie stoi w `docs/TASKS.md`
razem z zamknięciem.

## 9. Czego nie zrobiono

- **Nie utworzono progu dla kontenera** — to jest rozstrzygnięcie pozycji, z trzema
  powodami z punktu 4, a nie pominięcie.
- **Nie zmieniono progu runnera ani podłogi mierzalności** — „Poza zakresem", i nic
  w tym pomiarze tego nie wymagało.
- **Nie dopisano pomiaru runnera z dzisiaj do `POMIARY`.** Job `tools` przebiegu PR
  #571 zmierzył 104,530 s ściany przy 190,157 s CPU (stosunek 1,819) na 124 modułach.
  Jest to **siódmy** przebieg runnera i pierwszy, który NIE ustanowił nowego maksimum
  (116,404 s zostaje). Nie wszedł do listy, bo liczba przebiegów runnera jest dziś
  pilnowana wpisem „sześć" wiążącym się z pomiarem z 11.09.2026, a ta sama liczba stoi
  w prozie raportu z 6.D149, który jest historią i przepisywaniu nie podlega.
  Podniesienie tego wymaga własnej pozycji — wpisanej niżej w `docs/TASKS.md`.
- **Nie przyspieszono zestawu** — poza zakresem pozycji.

## 10. Co zauważone przy okazji, nietknięte

- **Podłoga mierzalności jest na tym kontenerze prawie ślepa na lekkie obciążenie.**
  W przebieg 1 wszedł mój własny zapętlony proces powłoki (ok. 40 s jednego rdzenia),
  w przebieg 2 — ośmiosekundowy przebieg jednego modułu bramek. Stosunki wyszły 0,987
  i 0,988, czyli **nie do odróżnienia** od czterech pozostałych, a przebieg 2 okazał
  się w dodatku szybszy od przebiegu 1. Zestaw liczy się szeregowo, więc proces na
  innym rdzeniu nie zabiera mu czasu. Podłoga łapie obciążenie ciężkie (0,451 przy
  ośmiu procesach, 09.09.2026) i to jej wystarcza tam, gdzie pracuje — na runnerze.
  Zapisane, bo gdyby kiedyś ktoś chciał użyć stosunku CPU/ściana jako miary „czy
  kontener był spokojny", ta liczba mu na to nie odpowie.
