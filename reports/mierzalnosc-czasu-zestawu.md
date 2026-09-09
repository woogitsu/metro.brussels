# Który sygnał mierzalności odróżnia wolny kod od zajętej maszyny (6.D42)

**Zmierzone 09.09.2026 na:** `cb9322c` (kontener sesji, 4 rdzenie) oraz `4f79c4e`
(runner `metro-wsl-DOM-NEW-*`, job `tools`).
**Przyrząd:** `python3 tools/tests/test_all.py` w podprocesie z `resource.RUSAGE_CHILDREN`,
`/proc/loadavg`, API GitHub Actions (19 jobów `tools` z 100 ostatnich przebiegów),
`tools/tests/test_suite_runtime_budget.py`, `.github/workflows/python-tests.yml`.

---

## 1. Pytanie

Bramka czasu ściany porównuje **jedną liczbę** z progiem 150,0 s i nie wie, czy ta
liczba w ogóle dała się zmierzyć. 08.09.2026 ten sam zestaw dał 335,668 s przy
dwunastu jobach naraz i 102 s na pustej puli — komunikat kazał wtedy szukać
spowolnienia w kodzie, a mówił o obciążeniu maszyny.

Wpis 6.D42 postawił warunek: **najpierw zmierzyć**, jaki sygnał jest dostępny, bo
wybranie go bez pomiaru dałoby drugą bramkę tej samej rodziny, tylko z inną liczbą
wpisaną z ręki.

## 2. Kandydat 1 — drugi przebieg zestawu. NIE ODRÓŻNIA

Ten kandydat jest w wpisie pierwszy, bo bliźniacza bramka kosztu kroku
(`tools/ci/assert_linecore_budget.py`, 6.D41) używa właśnie rozstępu powtórzeń.
Pomiar mówi, że **tutaj to nie działa**:

```
maszyna spokojna    91,742 s i 91,858 s   ->  rozstęp 0,116 s = 0,13 %
maszyna obciążona  203,882 s i 207,215 s  ->  rozstęp 3,333 s = 1,63 %
```

Dwa wolne przebiegi wyglądają na **spójne**. Rozstęp rośnie z 0,13 % do 1,63 %, ale
oba są małe i nie ma między nimi progu, który by je rozdzielił bez fałszywych alarmów.
Powód jest strukturalny: `budget` powtarza przejazd dziewięć razy **w jednym procesie
i w tym samym stanie maszyny**, więc jego rozstęp mierzy zmienność chwilową; dwa
przebiegi zestawu pod stałym obciążeniem są po prostu dwa razy wolne.

**Koszt: tyle, co pierwszy przebieg** — 92 s na spokojnej maszynie, 205 s pod
obciążeniem. Najdroższy z czterech kandydatów i jedyny, który niczego nie mówi.

## 3. Kandydat 2 — `/proc/loadavg`. Odróżnia, ale jest średnią z minuty

```
maszyna spokojna    loadavg przed startem 0,02 i 0,84
maszyna obciążona   loadavg przed startem 4,20 i 9,10
koszt: 1000 odczytów = 0,0102 s, czyli 10 µs na odczyt
```

Odróżnia i jest praktycznie darmowy. Wada jest w definicji: to średnia z ostatniej
minuty, więc odczyt na starcie joba opisuje to, co działo się **przed** nim, a nie
w jego trakcie. Widać to w danych: pierwszy przebieg na spokojnej maszynie miał
`przed 0,02`, a drugi `przed 0,84` — bo podniósł go pierwszy przebieg.

## 4. Kandydat 3 — liczba równoległych jobów. NIE ODRÓŻNIA w zmierzonym zakresie

Zmierzone na **prawdziwym runnerze**, nie rozumowaniem: 19 jobów `tools`
z ostatnich 100 przebiegów, czas ściany z ich własnych logów, współbieżność
policzona z nakładania się okien `started_at`–`completed_at`.

```
czas ściany:  min 45,081  max 67,742  mediana 52,373
korelacja Pearsona (liczba równoległych vs czas ściany):  r = 0,088  przy n = 19
równoległych na TYM SAMYM runnerze:  min 0, max 0  (we wszystkich 19 przypadkach)
```

Dwie rzeczy naraz. Po pierwsze: w dzisiejszej puli job `tools` **ani razu** nie dzielił
maszyny z innym jobem, więc licznik „ilu nas jest na tej maszynie" ma wariancję zero
i nie może niczego odróżnić. Po drugie: współbieżność na całej puli (1–4) nie tłumaczy
rozrzutu 45–68 s, bo korelacja jest praktycznie zerowa.

**Granica tego pomiaru stoi tu razem z nim:** incydent z 335 s miał **dwanaście**
jobów naraz, czyli wartość spoza zmierzonego przedziału. Pomiar mówi, że w zakresie
1–4 ten sygnał nie działa; nie mówi, że nie zadziałałby przy dwunastu.

## 5. Kandydat 4 — stosunek CPU do ściany. TO JEST TEN SYGNAŁ

Kandydata nie było we wpisie; wyszedł z pytania „co w tym pomiarze jest niezmienne".

```
                     ściana        CPU dzieci    CPU/ściana
maszyna spokojna     91,742 s      90,522 s      0,987
                     91,858 s      90,741 s      0,988
maszyna obciążona   203,882 s      91,855 s      0,451
                    207,215 s      91,939 s      0,444
runner, job tools     53,517 s      70,804 s      1,323
runner, job tools     52,503 s      71,46 s*      1,361
```

**Czas CPU jest niemal niezmienny** — 90,522 → 91,939 s, czyli +1,5 % — gdy ściana
rośnie 2,2×. Stosunek spada z 0,99 do 0,45. Koszt sygnału: **zero**, bo `times` jest
wbudowane w powłokę i liczy się i tak.

**Runner jest POWYŻEJ JEDYNKI i to nie jest błąd odczytu.** 53,517 s ściany przy
70,804 s CPU znaczy, że zestaw dostaje tam więcej niż jeden rdzeń na sekundę ściany —
w kontenerze sesji nie dostaje. Podłoga nie może więc być „bliska jedynce"; musi leżeć
pod najniższym zmierzonym przebiegiem **bez** obciążenia (0,987) i nad najwyższym
**pod** obciążeniem (0,451). Środek przedziału to 0,719, wybrane **0,75**.

`*` — CPU drugiego przebiegu jest **wyliczone** z ilorazu i ściany, a nie odczytane:
wpięcie werdyktu zastąpiło wypis surowego CPU wypisem stosunku. Wypis surowej liczby
jest w tym samym commicie przywrócony, żeby następny log niósł oba.

**Runner ma dwa pomiary (n = 2), oba z tej pozycji:** `1,323` z przebiegu, który
wprowadził sam wypis (53,517 s ściany, 70,804 s CPU), i `1,361` z przebiegu, który
wpiął już werdykt (52,503 s ściany). Rozrzut między nimi to 2,9 %, obie wartości leżą
1,8× nad podłogą. Dwa pomiary to nadal mało i tak to tu stoi — ale nie jeden.

**Kierunek błędu jest bezpieczny i to jest część wyboru.** Za wysoka podłoga NIE
czerwieni CI — pomija porównanie i mówi o tym w logu. Za niska przepuszcza wolny
przebieg do porównania, czyli zachowuje się jak bramka sprzed tej zmiany. Fałszywy
alarm, który wyłącza bramki (6.D27), jest tu niemożliwy z konstrukcji.

## 6. Co powstało

`werdykt(elapsed_s, cpu_s)` w `tools/tests/test_suite_runtime_budget.py` zwraca parę
„czy odrzucić" i komunikat. Krok CI woła **jego**, a nie porównuje liczb po swojemu.
Sprawdzone na wszystkich zmierzonych przypadkach:

```
runner        (53,517; 70,804)  -> False, "czas sciany 53.517 s w progu 150.0 s, stosunek CPU/sciana 1.323"
kontener      (91,742; 90,522)  -> False, "… w progu …, stosunek CPU/sciana 0.987"
obciążony    (203,882; 91,855)  -> False, "stosunek CPU/sciana 0.451 … NIE JEST porownywany z progiem"
incydent 08.09 (335,668; 70,8)  -> False, "stosunek CPU/sciana 0.211 … NIE JEST porownywany z progiem"
kod naprawdę wolny (200; 200)   -> True,  "przekroczyl prog czasu sciany: 200.000 s > 150.0 s przy stosunku 1.000"
```

Ostatni wiersz jest tym, który odróżnia tę zmianę od wyłączenia bramki.

## 7. Kontrole negatywne — wykonane

| mutacja | skutek |
|---|---|
| podłoga podniesiona nad przebieg bez obciążenia (1,5) | `FAIL …lezy_miedzy_zmierzonymi_stanami…: podłoga 1.5 jest nad zmierzonym przebiegiem bez obciążenia 0.987`, 12/14 |
| podłoga zsunięta pod przebieg POD obciążeniem (0,40) | `FAIL …: podłoga 0.4 jest pod zmierzonym przebiegiem POD obciążeniem 0.451`, 13/14 |
| `werdykt` odrzuca także przebieg niemierzalny | `FAIL test_werdykt_odmawia_porownania…` na przypadku 335,668 s, 13/14 |
| krok CI wraca do gołego porównania z progiem | `FAIL …liczy_werdykt_modulem…: krok nie woła werdykt z tego modułu` **oraz** `FAIL …mierzy_czas_cpu…: krok liczy werdykt, ale go nie wypisuje`, 12/14 |
| komunikat werdyktu gubi stosunek | `FAIL …mierzy_czas_cpu…: komunikat werdyktu (niemierzalny) nie niesie stosunku`, 13/14 |
| jeden odczyt `times` zamiast dwóch | `FAIL …: jeden odczyt nie daje różnicy`, 10/11 (kontrola z pierwszej połowy pozycji) |
| czytnik bierze PIERWSZY wiersz `times` | `FAIL …: czytnik zwrócił 0.002 … czyta czas samej powłoki`, 10/11 |

`md5sum -c` po każdej: `OK` dla `tools/tests/test_suite_runtime_budget.py`
i `.github/workflows/python-tests.yml`.

## 8. Dwie rzeczy, które złapały mnie same, i obie zostają zapisane

**Bramka prozy.** Komentarz przy podłodze napisałem najpierw jako „a wobec runnera
margines wynosi 1,76x". Zapaliła się bramka z 6.D26:
`proza podaje mnoznik 1.76, a MARGIN = 1.3975`. Zdanie było prawdziwe o **innym**
marginesie niż ten, którego bramka pilnuje, i właśnie dlatego jest przeformułowane,
a nie obronione: plik, w którym „margines" znaczy dwie różne rzeczy, jest gorszy od
pliku bez tej liczby.

**Bramka na własnym kroku.** Wpięcie `werdykt` usunęło z YAML-a literał `CPU/sciana`,
na który patrzyła bramka dopisana godzinę wcześniej — i ona padła. Nie została
osłabiona: jest **przekierowana** na to, że krok wypisuje komunikat werdyktu, plus
sprawdza dodatkowo, że **każda z trzech gałęzi** werdyktu ten stosunek w komunikacie
niesie. Po przekierowaniu sprawdza więcej niż przed nim.

**Trzecia rzecz złapała mnie przed pushem, nie po nim:** wywołanie `werdykt` wpisane
w YAML jako wieloliniowy `python3 -c` rozjechało blok scalarny i **jedenaście** bramek
CI padło naraz z `while scanning a simple key`. Zestaw pokazał to lokalnie; poprawka
to złożenie wywołania w jedną linię, tak jak sąsiednie.

## 9. Weryfikacja

```
  14/14 przeszło       test_suite_runtime_budget.py
  RAZEM 2087 testów, 111 modułów, kod 0

Passed!  - Failed: 0, Passed: 593, Skipped: 0, Total: 593, Duration: 28 s - MetroBxl.Sim.Tests.dll (net10.0)
```

Zestaw przed pozycją: 2082 testów, 111 modułów. Rdzeń symulacji jest tu uruchomiony
**lokalnie po raz pierwszy w tej sesji**: .NET SDK 10.0.401 doszedł do kontenera
09.09.2026 decyzją właściciela, więc `dotnet test tests/Sim.Tests` przestał być
wyłącznie wynikiem z runnera. Ta pozycja rdzenia nie tyka, ale pętla weryfikacji
z `CLAUDE.md` §5 jest od teraz wykonywana w całości.

## 10. Czego świadomie nie zrobiono

**Progu 150,0 s nie tknięto** — pole „Poza zakresem" wpisu; jego podniesienie byłoby
osłabieniem bramki, nie naprawą pomiaru.

**Nie zamieniono budżetu ściany na budżet CPU**, choć pomiar podsuwa, że to jest
mocniejsza konstrukcja: czas CPU jest niemal niezmienny wobec obciążenia, więc próg
postawiony na nim nie potrzebowałby sygnału mierzalności w ogóle. Wymaga to jednak
nowej liczby progu i pomiaru na obu maszynach (kontener 90,5 s, runner 70,8 s — CPU
nie jest przenośne między maszynami), a wpis tej pozycji trzymał próg dla właściciela.
Zapisane jako kandydat na osobną pozycję.

**Nie serializowano jobów CI** — to pozycja 6.D43.
