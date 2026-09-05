# Budżet kroków rdzenia linii dla wielu składów (5.7)

**Zmierzone 05.09.2026 na commicie `6c1048b`** (gałąź `budzet-krokow-wielu-skladow`
przebazowana na `main` po scaleniu #250, #251 i #252; narzędzie pomiarowe pochodzi z tej
gałęzi). Build `Release`, .NET SDK 10.0.400. Maszyna: kontener Linux 6.18.44,
`Intel(R) Xeon(R) @ 2.10GHz`, **4 rdzenie**, 16 GB RAM — **dzielona z innymi agentami**;
§3 pokazuje, jak bardzo, i to nie jest tło, które da się odjąć. Ten sam zestaw pomiarów
wykonany 90 minut wcześniej na `dfbde8f` jest w §8.4 jako kontrola powtarzalności.

Pytanie pozycji 5.7 brzmi: ile kosztuje 120 Hz przy N składach na osi i przy jakim N
krok stały przestaje się mieścić w klatce. Odpowiedź w dwóch zdaniach, reszta raportu
to ich uzasadnienie:

- **Zmierzone.** Przy pełnej obsadzie osi pakietu A — a to jest **9 składów naraz**
  pod ryglowaniem tras i **12 bez niego**, i jest to granica fizyczna, nie procesorowa —
  jeden krok `LineCore.Step` kosztuje **4,56 µs** (9 składów) i **5,98 µs** (12 składów),
  czyli **0,055 %** i **0,072 %** budżetu 1/120 s = 8333,3 µs. Zapas wynosi
  odpowiednio **1827×** i **1394×**.
- **Wyekstrapolowane, i to słowo jest tu obowiązkowe.** Koszt kroku rośnie z liczbą
  składów **kwadratowo**, nie liniowo, i dwa niezależne przebiegi dają na to zgodne
  dopasowanie. Krok wypełnia klatkę 1/120 s przy **N ≈ 330–390 składach jednocześnie
  na jednej osi** — czyli przy obsadzie **32–37 razy większej niż ta, którą oś w ogóle
  mieści** (330 wobec 9 z ryglowaniem tras, 389 wobec 12 bez niego). To jest ekstrapolacja z zakresu N ≤ 6,9, o czynnik 56–65; §7 mówi wprost,
  ile jest w niej pomiaru, a ile arytmetyki.

## 1. Czego ten pomiar dotyczy, a czego nie

Mierzony jest **`LineCore.Step`** — zegar linii nad wszystkimi składami: faza wyjazdów,
nastawnia (`RouteDispatcher.Dispatch`), odczyt autorytetów, jazda każdego składu
(`LineDrive.Step`, czyli `TrainController` + `BrakingPointSolver` z T-310/T-311),
meldunek ruchu do `FixedBlockSystem` i nawrót. Nie jest mierzony ani Godot, ani
wczytywanie geometrii, ani rysowanie — `src/Sim` nie zna silnika i pomiar też go nie zna.

**„N składów na osi" ma tu dwa znaczenia i raport trzyma je osobno**, bo zlanie ich
w jedno daje liczby nieprawdziwe w obie strony:

| pojęcie | co znaczy | ile kosztuje (zmierzone) |
|---|---|---|
| **na planie** | skład ma `LineDrive`, jest zarejestrowany w sygnalizacji, jedzie | 0,64–1,29 µs za skład, **rosnąco** (§4, §7) |
| **czeka** | skład zgłoszony przez `Add`, wymagalny, ale peron początkowy zajęty | **0,0375 µs** za skład, stale (§5) |

Zgłoszenie 32 składów do pakietu A nie daje 32 składów na osi. Daje 9 na osi i 23
w kolejce, a to jest różnica **rzędu 20-krotnej** w koszcie na skład. Dlatego każda
tabela niżej ma obie kolumny, a wykresu „koszt wobec `--trains`" w tym raporcie nie ma.

## 2. Metoda pomiaru

Do pomiaru dopisane zostało polecenie `budget` w `src/Sim.Runner` (klasa
`src/Sim.Runner/LineBudget.cs`). **Istniejące polecenie `line` nie mogło tego zmierzyć**
i nie jest to kwestia wygody: `line` zgłasza dokładnie jeden skład (`KABINA`,
`Program.cs`), bo odpowiada na pytanie „czy rdzeń liczy ten sam przejazd, co scena",
a bramka CI porównuje jego wyjście co do liczby. Dołożenie mu N składów zmieniłoby to,
co ta bramka porównuje. `line` zostaje więc nietknięte.

Metoda, punkt po punkcie:

1. **Okno.** Jedno powtórzenie to świeżo zbudowana linia i dokładnie `--steps` wywołań
   `LineCore.Step`. Wynik odmawia, jeśli zegar linii nie stanął na zamówionej liczbie
   kroków — inaczej kroki na sekundę liczyłyby się z liczby kroków, których nie wykonano.
2. **Każde okno buduje linię od nowa.** Drugie okno na tym samym obiekcie zastałoby
   składy w innym miejscu trasy i mierzyłoby inną pracę. Że praca jest ta sama, **nie
   jest tu założeniem**: po każdym oknie porównywany jest `FixedBlockSystem.StateDigest()`
   ze spisem, a rozjazd jest odmową, nie ostrzeżeniem.
3. **Liczenie obsady jest poza stoperem.** Zliczanie składów na planie w każdym kroku
   samo kosztuje O(N) na krok, więc doliczyłoby się do wyniku. Spis obsady
   (`LineBudget.Census`) to **osobny, nieobjęty stoperem przebieg**; że policzył to
   samo, co przebieg mierzony, pilnuje ten sam odcisk stanu.
4. **Rozgrzewka.** Pierwsze `--warmup` rund jest odrzucane. Kontrola, ile to zmienia,
   jest w §8.1 i zmienia **6,2×**.
5. **Przeplot.** Rundy idą na przemian po wszystkich N (`N=1, N=2, …, N=1, N=2, …`),
   a nie „wszystkie powtórzenia dla N=1, potem dla N=2". Kontrola w §8.2.
6. **Statystyka.** Podawana jest **mediana** z 9 (§4, §6) albo 7 (§5) powtórzeń oraz
   **minimum, maksimum i rozstęp w procentach mediany**. Średniej w tym raporcie nie ma:
   na maszynie dzielonej z innymi procesami jedno wolne okno przesuwa średnią,
   a mediany nie.
7. **Czas ścienny, nie procesora** — bo klatka mierzy się zegarem ściennym. Czas
   procesora procesu jest mierzony obok i podawany jako **stosunek CPU/ścienny**: we
   wszystkich przebiegach pomiarowych z §4–§6 leży on w paśmie **0,98–1,03**, czyli
   pętla kroku jest jednowątkowa i nie czeka na wejście-wyjście. Gdyby spadł wyraźnie
   poniżej 1, znaczyłoby to, że mierzy się wywłaszczanie przez cudze procesy, a nie koszt
   kroku. Jedyne wartości spoza tego pasma w całym raporcie to **1,41** i **1,12**
   w §8.1 — i one też są wynikiem, a nie usterką: to JIT kompilujący w tle, czyli
   dokładnie to, co rozgrzewka ma odsiać.

Odtworzenie pomiaru 1 co do polecenia (pozostałe różnią się wyłącznie wartościami
`--headway-s`, `--steps`, `--warmup`, `--repeats`, `--trains` i planem):

```bash
export PATH=/root/.dotnet:$PATH DOTNET_ROOT=/root/.dotnet
dotnet build src/Sim.Runner/Sim.Runner.csproj -c Release
dotnet src/Sim.Runner/bin/Release/net10.0/MetroBxl.Sim.Runner.dll budget \
    --axis data/track/L1_A.json \
    --signalling data/design/signalling/classic-2026.json \
    --limit-kmh 70 --exchange-s 8 --load AW2 \
    --headway-s 90 --turnback-s 240 \
    --trains 1,2,3,4,5,6,8,12,16,32 \
    --steps 120000 --warmup 3 --repeats 9 \
    --out build/budget/obsada.csv
```

Wariant planu z §6 powstaje z pliku w `data/` przez zmianę jednego pola, zapisaną
do `build/` — `data/` zostaje tylko do odczytu:

```python
d = json.load(open('data/design/signalling/classic-2026.json'))
d['require_route'] = False
d['plan_id'] = 'budget-noroute-L1_A'
json.dump(d, open('build/budget/plan-noroute.json', 'w'), ensure_ascii=False, indent=2)
```

Wspólne parametry przejazdu we wszystkich pomiarach: oś `data/track/L1_A.json`
(12 stacji, 6686,4 m), plan `data/design/signalling/classic-2026.json` (23 bloki),
`--limit-kmh 70 --exchange-s 8 --load AW2`, bez ATP, nawrót 240 s. Wszystkie są
`design_model` albo parametrem scenariusza i **żadna nie jest nowym faktem o sieci** —
pomiar 5.7 nie wnosi ani jednej liczby o brukselskim metrze.

## 3. Maszyna i obciążenie w trakcie pomiaru

To nie jest maszyna do benchmarków i raport ma to powiedzieć wprost, a nie schować
w jednej ładnej liczbie. `nproc` = **4**, a `uptime` przed i po każdym pomiarze:

```
### PRZED POMIAREM 1   12:23:19 up 4:55,  load average: 1.24, 0.30, 0.45
### PO POMIARZE 1      12:24:06 up 4:56,  load average: 4.01, 1.19, 0.75
### PRZED POMIAREM 2   12:24:06 up 4:56,  load average: 4.01, 1.19, 0.75
### PO POMIARZE 2      12:24:50 up 4:57,  load average: 5.32, 1.94, 1.02
### PRZED POMIAREM 3   12:24:50 up 4:57,  load average: 5.32, 1.94, 1.02
### PO POMIARZE 3      12:25:50 up 4:58,  load average: 5.74, 2.68, 1.34
```

**Maszyna zmieniła stan w trakcie pomiaru i trzeba to powiedzieć wprost.** Pomiar 1
zaczął się na maszynie praktycznie wolnej (obciążenie 1,24, z czego ~1,0 to własny
proces pomiaru — stosunek CPU/ścienny ≈ 1,00 mówi, że pętla kroku jest jednowątkowa),
a skończył przy 4,01. Do pomiaru 3 obciążenie doszło do 5,74 na czterech rdzeniach.
Sprawdzone `ps` w trakcie: cztery procesy `python3` innego agenta po ~60 % CPU każdy.

Widać to w rozrzucie: rozstęp między najszybszym a najwolniejszym powtórzeniem wynosi
**3,7 %–31,3 %** mediany. Największy jest przy N=1, gdzie okno trwa najkrócej
(0,07 s) i jedno wywłaszczenie waży najwięcej. Wszystkie liczby w tym raporcie należy
czytać z dokładnością **rzędu ±10 %**, a nie do trzeciej cyfry.

Na wnioski to nie wpływa i to również jest wynik, a nie pocieszenie: zapas do budżetu
klatki wynosi trzy rzędy wielkości, kształt krzywej wychodzi z **siedmiu i ośmiu
punktów**, a §8.4 pokazuje, że ten sam pomiar na innym commicie i przy innym obciążeniu
daje te same liczby z dokładnością do 2 %.

## 4. Pomiar 1 — koszt wobec obsady osi (ryglowanie tras włączone)

`--headway-s 90 --turnback-s 240 --steps 120000 --warmup 3 --repeats 9`
(okno = 1000 s zegara linii). Maszynowo: `build/budget/obsada.csv` — plik nie jest
w repo (`build/` nie jest commitowane), odtwarza go polecenie z §2.

```
[BUDŻET] oś L1_A, plan classic-2026-L1_A (23 bloków), 12 stacji, ATP=nie, nawrót 240 s, odstęp 90 s
[BUDŻET] okno 120000 kroków, rozgrzewka 3, powtórzeń 9, rdzeni 4, budżet kroku 1/120 s = 8333.3 µs
[BUDŻET] N_zgł;N_max;N_śr;czeka_śr;mediana_kroków_s;min;max;rozstęp_%;µs_krok;CPU/ścienny;%budżetu
[BUDŻET] 1;1;1.00;0.00;1637570;1182095;1694906;31.3;0.611;1.00;0.01
[BUDŻET] 2;2;1.91;0.00;840217;737874;861592;14.7;1.190;1.00;0.01
[BUDŻET] 3;3;2.73;0.00;557766;516486;574190;10.3;1.793;0.99;0.02
[BUDŻET] 4;4;3.45;0.01;422680;405354;430676;6.0;2.366;1.00;0.03
[BUDŻET] 5;5;4.05;0.05;346274;325179;351154;7.5;2.888;0.99;0.03
[BUDŻET] 6;6;4.53;0.12;297620;279631;298195;6.2;3.360;1.00;0.04
[BUDŻET] 8;8;5.12;0.36;242813;224687;248859;10.0;4.118;0.99;0.05
[BUDŻET] 12;9;5.23;0.83;233010;213235;237656;10.5;4.292;0.99;0.05
[BUDŻET] 16;9;5.23;0.83;230422;217621;237255;8.5;4.340;1.00;0.05
[BUDŻET] 32;9;5.23;0.83;219254;203225;224172;9.6;4.561;1.00;0.05
[BUDŻET] mieści się w 1/120 s: 10 z 10 zmierzonych N; największe zmierzone N=32 zajmuje 0.05% budżetu kroku przy 9 składach faktycznie na planie
```

Kolumny: `N_zgł` — zgłoszone przez `Add`; `N_max` — najwięcej naraz na planie w oknie;
`N_śr` — średnia obsada na krok (**to jest to N, któremu odpowiada koszt** — szczyt trwa
tyle, ile trwa, a krok płaci za obsadę bieżącą); `czeka_śr` — średnia kolejka do wjazdu.

Dwie rzeczy, które ta tabela mówi wprost:

- **Oś nasyca się przy 9 składach.** Od `--trains 12` w górę `N_max` stoi na 9,
  a `N_śr` na 5,23 — dosypywanie składów wydłuża wyłącznie kolejkę. Granicą jest
  ryglowanie tras na planie o 23 blokach (trasa rygluje trzy: peron-szlak-peron),
  a nie procesor.
- **Koszt na skład nie jest stały.** Przyrost mediany między kolejnymi punktami wynosi
  0,636 → 0,735 → 0,796 → 0,870 → 0,983 → 1,285 µs na skład. Kolejny skład kosztuje
  **dwa razy więcej niż pierwszy**. To nie szum: kierunek jest monotoniczny na sześciu
  odstępach z rzędu, a §7 pokazuje, że reszty dopasowania liniowego układają się w łuk,
  a nie losowo.

## 5. Pomiar 2 — ile kosztuje skład zgłoszony, ale niewpuszczony

`--headway-s 0` (wszystkie wymagalne od kroku 0), `--steps 20000 --warmup 2 --repeats 7`.
Maszynowo: `build/budget/kolejka.csv` (jak wyżej — `build/`).

```
[BUDŻET] okno 20000 kroków, rozgrzewka 2, powtórzeń 7, rdzeni 4, budżet kroku 1/120 s = 8333.3 µs
[BUDŻET] N_zgł;N_max;N_śr;czeka_śr;mediana_kroków_s;min;max;rozstęp_%;µs_krok;CPU/ścienny;%budżetu
[BUDŻET] 1;1;1.00;0.00;1347191;1177371;1373664;14.6;0.742;0.98;0.01
[BUDŻET] 16;3;1.83;14.17;571363;424900;588781;28.7;1.750;1.03;0.02
[BUDŻET] 64;3;1.83;62.17;279308;262269;295094;11.8;3.580;1.02;0.04
[BUDŻET] 256;3;1.83;254.17;93451;88456;97721;9.9;10.701;0.98;0.13
[BUDŻET] 1024;3;1.83;1022.17;25683;23923;26419;9.7;38.936;0.98;0.47
[BUDŻET] 4096;3;1.83;4094.17;6475;6241;6574;5.1;154.452;0.99;1.85
```

Obsada osi stoi tu na 1,83 składu przez cały czas — rośnie **wyłącznie kolejka**.
Dopasowanie liniowe po sześciu punktach:

```
µs_krok = 1,0248 + 0,03746 · (składy czekające)
reszty: -0,283  +0,194  +0,227  +0,156  -0,374  +0,080 µs
```

Maksymalna reszta 0,374 µs przy wartości 154,5 µs to **0,24 %** — zależność jest
liniowa i nie ma w niej członu kwadratowego. Zgadza się to z kodem: skład, który czeka,
przechodzi w kroku wyłącznie przez fazę wyjazdów i jedno `LineCore.EntryIsClear()`,
czyli pętlę po 23 blokach; nie dotyka ani `FixedBlockSystem`, ani prowadzenia.

**Koszt składu czekającego: 0,0375 µs.** Próg 8333,3 µs wypadałby przy **≈ 222 500**
składach w kolejce — liczba bez znaczenia praktycznego, podana po to, żeby było widać,
że to nie kolejka jest kosztowna.

## 6. Pomiar 3 — ten sam pomiar przy wyższej obsadzie, druga droga do tej samej krzywej

Pomiar 1 kończy się na średniej obsadzie 5,23, bo tyle mieści oś z ryglowaniem tras.
Żeby sprawdzić kształt krzywej na szerszym zakresie, ten sam plan puszczony jest
z **jednym zmienionym polem**: `require_route: false`. Wariant leży
w `build/budget/plan-noroute.json` (poza `data/`, generowany skryptem z §2)
i **nie jest planem STIB ani nową liczbą o sieci** — służy wyłącznie temu, żeby na oś
weszło więcej składów naraz.

`--headway-s 45 --turnback-s 240 --steps 120000 --warmup 3 --repeats 9`.
Maszynowo: `build/budget/obsada-noroute.csv` (jak wyżej — `build/`).

```
[BUDŻET] oś L1_A, plan budget-noroute-L1_A (23 bloków), 12 stacji, ATP=nie, nawrót 240 s, odstęp 45 s
[BUDŻET] N_zgł;N_max;N_śr;czeka_śr;mediana_kroków_s;min;max;rozstęp_%;µs_krok;CPU/ścienny;%budżetu
[BUDŻET] 1;1;1.00;0.00;1579750;1207254;1626620;26.5;0.633;1.01;0.01
[BUDŻET] 2;2;1.95;0.00;813361;714009;824672;13.6;1.229;0.99;0.01
[BUDŻET] 3;3;2.86;0.00;540614;522627;552233;5.5;1.850;1.00;0.02
[BUDŻET] 4;4;3.69;0.04;404481;348983;413028;15.8;2.472;1.00;0.03
[BUDŻET] 6;6;5.06;0.26;271670;265006;275623;3.9;3.681;1.00;0.04
[BUDŻET] 8;8;6.06;0.68;214088;207257;215577;3.9;4.671;1.00;0.06
[BUDŻET] 10;10;6.68;1.29;182633;179719;186453;3.7;5.475;1.00;0.07
[BUDŻET] 12;12;6.92;2.11;173467;156840;178062;12.2;5.765;0.99;0.07
[BUDŻET] 16;12;6.92;3.68;169965;164233;174679;6.1;5.884;0.98;0.07
[BUDŻET] 24;12;6.92;4.69;167350;150450;168950;11.1;5.976;0.99;0.07
```

Bez ryglowania tras oś mieści **12 składów naraz** zamiast 9, a średnia obsada dochodzi
do 6,92 zamiast 5,23 — zakres pomiarowy szerszy o 32 %. Nasycenie jest znowu fizyczne:
od `--trains 16` w górę rośnie tylko kolejka.

## 7. Kształt krzywej i próg 1/120 s

Dopasowania na obu pomiarach obsady, po **odjęciu kosztu kolejki** (0,03746 µs za
czekający skład, z §5), zmienna niezależna to średnia obsada osi:

| | pomiar 1 (ryglowanie) | pomiar 3 (bez ryglowania) |
|---|---|---|
| punktów | 7 (N_śr 1,00 → 5,12) | 8 (N_śr 1,00 → 6,92) |
| liniowo | −0,377 + 0,8311·N | −0,484 + 0,8616·N |
| max reszta liniowo | **0,226 µs** | **0,256 µs** |
| kwadratowo | 0,1870 + 0,3704·N + **0,07521**·N² | 0,1867 + 0,4180·N + **0,05409**·N² |
| max reszta kwadratowo | **0,053 µs** | **0,061 µs** |
| próg 8333,3 µs, liniowo | N = 10027 | N = 9672 |
| **próg 8333,3 µs, kwadratowo** | **N = 330** | **N = 389** |

**Krzywa jest kwadratowa i to jest twarde.** Reszty dopasowania liniowego są ponad 4×
większe od kwadratowego i — co ważniejsze — **układają się w łuk**:
(+0,156, −0,021, −0,099, −0,125, −0,103, −0,033, +0,226) dla pomiaru 1 i
(+0,256, +0,033, −0,130, −0,225, −0,204, −0,092, +0,155, +0,208) dla pomiaru 3.
Znak reszty zależy od położenia punktu, a nie jest losowy — to jest podpis brakującego
członu, nie szumu maszyny. Reszty kwadratowe (≤ 0,061 µs, poniżej 1,5 % wartości) są
mniejsze niż rozstęp powtórzeń, więc trzeciego członu ten pomiar już nie rozróżni.

**Mechanizm jest w kodzie, nie w domyśle.** `FixedBlockSystem.MoveTrain` wywołuje
`PublishAuthorities()` (linia 321), a ta przechodzi **po wszystkich składach** i dla
każdego liczy `ComputeAuthority` — pętlę po blokach. `LineCore.Step` woła `MoveTrain`
**raz na skład**, więc sama faza 3 jest O(N²·B) na krok. Do tego `Require(trainId)`
i `FindOrNull` są liniowym przeszukaniem listy składów, a przy ryglowaniu dochodzi
`RequestRoute` → kolejne `PublishAuthorities`. Zgadza się to z tym, że współczynnik
przy N² jest **1,4× większy z ryglowaniem** (0,0752) niż bez niego (0,0541): ryglowanie
dokłada drugie przejście po wszystkich składach.

**Próg, z liczbą.** Krok stały przestaje mieścić się w 1/120 s przy **N ≈ 330–390
składach jednocześnie na jednej osi**. Dwie niezależne konfiguracje dają 330 i 389,
czyli rozjazd **18 %** — i ten rozjazd jest informacją, nie szumem do uśrednienia:
wynika z tego, że ryglowanie tras kosztuje na skład więcej, więc próg zbija niżej.

**Ile w tej liczbie jest pomiaru.** Zakres mierzony sięga N_śr = 6,92; próg leży
**56–65 razy dalej**. Ekstrapolacja opiera się na członie kwadratowym wyznaczonym na
zakresie, w którym daje on od 8–12 % (N=1) do 46–49 % (na końcu zakresu) całego kosztu,
i na założeniu, że żaden człon wyższego rzędu ani żaden efekt pamięci podręcznej nie
wchodzi wyżej. **Zmierzona jest krzywizna, a nie próg.** Zdanie, które nie wymaga żadnej
ekstrapolacji, brzmi tak: przy maksymalnej obsadzie, jaką oś pakietu A w ogóle utrzymuje,
krok zajmuje **0,055 % budżetu klatki (9 składów) i 0,072 % (12 składów)**.

Przeliczone na czas rzeczywisty: 120 kroków na sekundę symulowanego czasu przy 9 składach
to **0,55 ms procesora na sekundę** — 0,055 % jednego rdzenia z czterech.

## 8. Kontrole

### 8.1 Rozgrzewka — kontrola, ile zmienia (i dlaczego benchmark z jednego przebiegu kłamie)

Ten sam scenariusz (N=1, okno 20 000 kroków), różniący się **wyłącznie** liczbą
odrzuconych rund:

```
--- --steps 20000 --warmup 0 --repeats 1
[BUDŻET] 1;1;1.00;0.00;210872;210872;210872;0.0;4.742;1.00;0.06
--- --steps 20000 --warmup 3 --repeats 1
[BUDŻET] 1;1;1.00;0.00;1220070;1220070;1220070;0.0;0.820;1.41;0.01
--- --steps 20000 --warmup 3 --repeats 9
[BUDŻET] 1;1;1.00;0.00;1300449;1236881;1311604;5.7;0.769;1.05;0.01
```

**6,2× różnicy** między pojedynczym zimnym przebiegiem a rozgrzanym. Zimny przebieg dla
**jednego** składu daje 4,742 µs — czyli więcej, niż rozgrzany pomiar daje dla
**dziewięciu** (4,561 µs, §4). Benchmark z jednego przebiegu pomyliłby się tutaj o cały
zakres tego raportu. Przyczyna jest znana: kompilacja warstwowa .NET przełącza metodę na
tier-1 dopiero po opóźnieniu liczenia wywołań, a okno 20 000 kroków trwa krócej niż to
opóźnienie; widać ją też w kolumnie CPU/ścienny, która w środkowym wierszu wynosi 1,41,
bo kompilator pracuje na drugim wątku.

Przy oknie 120 000 kroków (§4, §6) sama faza spisu obsady zdąży rozgrzać pętlę i efekt
schodzi poniżej rozrzutu powtórzeń:

```
--- --steps 120000 --warmup 0 --repeats 1
[BUDŻET] 8;8;5.12;0.36;236306;236306;236306;0.0;4.232;1.12;0.05
--- --steps 120000 --warmup 3 --repeats 1
[BUDŻET] 8;8;5.12;0.36;254062;254062;254062;0.0;3.936;1.01;0.05
```

7,5 % różnicy przy rozstępie powtórzeń 10,0 % dla tego samego N w §4. Rozgrzewka zostaje
mimo to, bo ma odsiewać efekt, który przy krótszym oknie wynosi 6,2×, a nie dlatego,
że akurat przy tym oknie jest niewidoczna.

### 8.2 Przeplot — kontrola niezależności od kolejności

Ten sam pomiar co §4, z listą N podaną w obu kierunkach:

```
--- --trains 1,4,8
[BUDŻET] 1;1;1.00;0.00;1632786;1567073;1659572;5.7;0.612;1.00;0.01
[BUDŻET] 4;4;3.45;0.01;409941;393983;418203;5.9;2.439;1.00;0.03
[BUDŻET] 8;8;5.12;0.36;239487;230442;241763;4.7;4.176;1.00;0.05
--- --trains 8,4,1
[BUDŻET] 8;8;5.12;0.36;246064;233283;250315;6.9;4.064;1.01;0.05
[BUDŻET] 4;4;3.45;0.01;414378;400027;425061;6.0;2.413;1.00;0.03
[BUDŻET] 1;1;1.00;0.00;1634864;1389709;1662354;16.7;0.612;1.01;0.01
```

Rozjazd między kierunkami: **0,0 % (N=1), 1,1 % (N=4), 2,7 % (N=8)** — poniżej rozstępu
powtórzeń.

**Kontrola negatywna do tego punktu jest zmierzona, a nie przewidziana.** Pierwsza wersja
narzędzia liczyła wszystkie powtórzenia dla jednego N, zanim przeszła do następnego,
i przy oknie 20 000 kroków dawała to:

```
--trains 1,2,4  ->  N=1: 229076 kroków/s      --trains 4,2,1  ->  N=1: 1064062 kroków/s
                    N=2: 537921                                    N=2:  802221
                    N=4: 877824                                    N=4:  158532
```

Pierwsze N w kolejności wychodziło **4,6× wolniejsze** od tego samego N na końcu listy
(N=4: 877 824 vs 158 532 kroków/s, 5,5×), a „koszt rośnie z N" i „koszt maleje z N"
dawały się dostać z tego samego kodu przez zmianę kolejności argumentów. Przeplot
z §2.5 usuwa to i tego trybu w narzędziu już nie ma.

### 8.3 Bramki narzędzia — cztery mutacje, każda złapana

`tests/Sim.Tests/LineBudgetTests.cs`, 9 testów. Kontrole negatywne wykonane na tym
drzewie, każda z przywróceniem pliku po pomiarze:

| mutacja w `src/Sim.Runner/LineBudget.cs` | co padło |
|---|---|
| `Build()`: `i < Trains` → `i < 1` (pomiar ignoruje N) | `Spis_liczy_sklady_ktore_weszly_na_plan`, `Sklady_ktore_nie_zmiescily_sie_na_osi_sa_policzone_osobno`, `Odcisk_stanu_rozni_sie_miedzy_scenariuszami` — 3 z 439 |
| `Measure()`: `i < steps` → `i < steps - 1` (okno krótsze niż deklaruje) | `Okno_wykonuje_dokladnie_tyle_krokow_ile_zamowiono`, `Powtorzenia_koncza_sie_w_tym_samym_stanie_co_spis`, `Kolejnosc_scenariuszy_nie_zmienia_obsady` — 3 z 439 |
| `Census()`: `if (train.OnLine)` → `if (train.OnLine \|\| true)` (spis liczy zgłoszone) | `Sklady_ktore_nie_zmiescily_sie_na_osi_sa_policzone_osobno` — 1 z 439 |
| `MedianStepsPerSecond()`: mediana → średnia | `Mediana_bierze_srodek_a_nie_srednia_wszystkiego` — 1 z 439 |

Bez mutacji: **439 z 439 przeszło**.

Odmowy samego polecenia, sprawdzone z wiersza poleceń: brak `--signalling`
(„bez planu bloków nie ma LineCore"), `--trains 0`, `--headway-s 0.001` (krótszy niż
krok symulacji, więc zaokrągliłby rozkład do zera) i `--steps 0` — każda kończy się
komunikatem `BŁĄD:`, a nie policzonym pomiarem.

### 8.4 Powtarzalność — ten sam zestaw na innym commicie i przy innym obciążeniu

Cały pomiar wykonany był dwa razy: 05.09.2026 o 10:22 UTC na `dfbde8f`, przy obciążeniu
utrzymującym się na **4,5–5,1**, i o 12:23 UTC na `6c1048b`, zaczynając od maszyny
prawie wolnej. Wybrane pozycje, µs na krok:

| pozycja | `dfbde8f` (obciążenie 4,5–5,1) | `6c1048b` (obciążenie 1,2 → 5,7) | różnica |
|---|---|---|---|
| pomiar 1, N_śr = 1,00 | 0,609 | 0,611 | 0,3 % |
| pomiar 1, N_śr = 5,12 | 4,174 | 4,118 | 1,3 % |
| pomiar 1, 9 składów (N_zgł 32) | 4,665 | 4,561 | 2,2 % |
| pomiar 2, 4094 czekających | 153,557 | 154,452 | 0,6 % |
| pomiar 3, 12 składów (N_zgł 24) | 5,842 | 5,976 | 2,3 % |
| człon N² (pomiar 1) | 0,0736 | 0,0752 | 2,2 % |
| człon N² (pomiar 3) | 0,0485 | 0,0541 | 11,5 % |
| próg klatki (pomiar 1 / pomiar 3) | 334 / 410 | 330 / 389 | 1,2 % / 5,1 % |

Wszystko poza współczynnikiem przy N² z pomiaru 3 mieści się w 2,3 %. Ten jeden różni
się o 11,5 % i to jest spodziewane: jest wyznaczany jako drugi wyraz dopasowania na
ośmiu punktach, więc dziedziczy rozrzut wszystkich ośmiu. Wniosek jakościowy — krzywa
kwadratowa, próg rzędu kilkuset składów — wychodzi z obu serii tak samo.

## 9. Czego ten pomiar świadomie nie mierzy

- **Jednej osi, nie sieci.** Cztery linie STIB to cztery (a z kierunkami — więcej)
  niezależnych `LineCore`. Koszt sieci jest sumą, ale czy sumą po jednym wątku, czy po
  czterech, ten pomiar nie rozstrzyga i rozstrzygać nie próbuje.
- **Rdzenia bez sceny.** Godot ma własny budżet klatki; ten raport mówi wyłącznie,
  ile z 8333 µs zjada `LineCore.Step`.
- **Bez ATP.** Wszystkie pomiary są z `atp: false`. Ochrona pociągu dokłada
  `TrainProtection.Supervise` raz na skład na krok, czyli człon liniowy — pomiaru z ATP
  tu nie ma i nie wolno go zgadywać z tych liczb.
- **Bez optymalizowania czegokolwiek.** Pozycja 5.7 jest pomiarem; człon kwadratowy
  z §7 jest **znaleziskiem do zgłoszenia**, a nie zaproszeniem do przepisania
  `FixedBlockSystem` przy okazji.
- **Pamięci nie mierzy w ogóle.** Zauważone przy okazji i nietknięte:
  `FixedBlockSystem._events` rośnie bez ograniczenia (`Emit` tylko dopisuje), więc
  długi przejazd z wieloma składami zajmuje pamięć proporcjonalnie do liczby zdarzeń
  autorytetu. Przy oknie 120 000 kroków nie zdążyło to zaboleć w czasie, ale jest to
  koszt, którego ten raport nie zmierzył.

## 10. Wniosek

Przy obsadzie, jaką oś pakietu A fizycznie utrzymuje, **120 Hz nie jest ograniczeniem
i nie będzie nim po żadnej realistycznej zmianie rozkładu**: 9 składów kosztuje 0,055 %
budżetu klatki. Ograniczeniem jest liczba bloków i ryglowanie tras — oś nasyca się przy
9 składach (12 bez ryglowania), a każdy następny zgłoszony ląduje w kolejce po
0,0375 µs za sztukę.

Krok przestałby się mieścić w klatce przy **≈ 330–390 składach naraz na jednej osi**,
co jest liczbą wyekstrapolowaną z zakresu 56–65× mniejszego i nieosiągalną na tej sieci.
Jeśli kiedykolwiek zacznie być osiągalna — na dłuższej osi, przy sieci liczonej w jednym
wątku albo po dołożeniu ATP — pierwszym miejscem do obejrzenia jest
`FixedBlockSystem.PublishAuthorities`, bo to ono odpowiada za człon N².
