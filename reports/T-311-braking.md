# T-311 — hamowanie

**Zmierzone na commicie:** `9c94c1a` · **data:** 2026-09-01

Do tej pory hamulec był **poleceniem**: zadane opóźnienie z ograniczeniem zrywu,
niezależne od masy i przyczepności (`ServiceBrakingRun` z T-310, `TrainController`
z T-400). T-311 dokłada do tego trzy rzeczy — sufit przyczepnościowy, solver punktu
hamowania i drogę hamowania liczoną z oporami ruchu — i **nie dokłada ani jednej
liczby o M7 bez pokrycia w rejestrze**, poza jedną, która jest jawnym parametrem
o dwóch wariantach skrajnych.

Zakres: `docs/TASKS.md`, T-311. Model: `docs/02-simulation.md` §Hamowanie.
Audyt założeń: `docs/21-measured-vs-assumed.md` §4b.

---

## 0. Co zrobiłem, w jednym zdaniu

Dołożyłem do rdzenia sufit przyczepnościowy hamowania, solver punktu hamowania
z ograniczeniem zrywu i przebieg hamowania z oporami Davisa — wszystkie trzy
policzone dwiema niezależnymi drogami i wszystkie bez tknięcia `TrainController`,
więc przejazd z T-400 wychodzi **co do bajtu** taki sam jak na `origin/main`.

---

## 1. Co powstało

```
src/Sim/Physics/BrakingAssumptions.cs     katalog założeń hamowania (3 wpisy, wszystkie bez źródła)
src/Sim/Physics/BrakeAdhesionLimit.cs     sufit b_max = μ·f·g/λ, progi krytyczne f i μ
src/Sim/Physics/BrakingPointSolver.cs     wzór zamknięty s(b), t(b) i odwrotność s → b
src/Sim/Physics/BrakingEnergyAccount.cs   bilans energii hamowania + zamiana pracy oporów na metry
src/Sim/Train/BrakingRun.cs               przebieg z oporami; woła TrainController, nie kopiuje go
src/Sim.Runner/Program.cs                 nowe polecenie `braking` — tablice referencyjne
tools/physics/braking.py                  NIEZALEŻNA referencja tych samych liczb, czyta rejestr M7
tools/tests/test_braking.py               22 testy referencji + audyt założeń
tests/Sim.Tests/BrakingTests.cs           46 testów rdzenia (razem z regresją T-400)
tests/Sim.Tests/BrakingReference.cs       snapshot liczb Pythona na pełnej precyzji
docs/02-simulation.md                     §Hamowanie — równania modelu
docs/21-measured-vs-assumed.md            §4b — trzy założenia z uzasadnieniami
.github/workflows/sim-tests.yml           bramka: `diff` rdzenia z referencją Pythona
```

`data/vehicle/m7-spec.json` **nie został tknięty** (reguła 6). `TrainController`,
`TrainDynamics`, `ServiceBrakingRun`, `AccelerationRun` i `tools/physics/reference.py`
też nie — §5.

---

## 2. Sufit przyczepnościowy hamowania

`docs/02-simulation.md` daje ograniczenie przyczepnościowe **dla trakcji**:
`F ≤ μ · m · (4/6) · g`, i sam nazywa `4/6` legacy parametrem limitu adhezji.
Dla hamowania działa ten sam styk, ale **inny udział osi**: hamować może więcej osi,
niż jest napędzanych. Udziału osi hamowanych M7 nie ma w żadnym źródle, więc jest
jawnym `design_assumption` z dwoma wariantami skrajnymi.

Opóźnienie pudła: `b_max = μ · f · g / λ`, gdzie `λ = 1,08` — bo `TrainController`
zamienia opóźnienie na ruch przez masę efektywną. Kolumna „bez λ" pokazuje, ile
wychodzi przy zignorowaniu bezwładności wirującej; podaję obie, bo rozdziału tej
bezwładności na osie hamowane i niehamowane **też nie ma w danych**.

| szyna | μ | wariant | f | `b_max` [m/s²] | bez λ [m/s²] | 1,10 osiągalne? | 1,30 osiągalne? |
|---|---:|---|---:|---:|---:|:--:|:--:|
| sucha | 0,25 | wszystkie osie | 1,0000 | **2,2701** | 2,4517 | tak | tak |
| sucha | 0,25 | tylko napędne | 0,6667 | **1,5134** | 1,6344 | tak | tak |
| mokra | 0,13 | wszystkie osie | 1,0000 | **1,1804** | 1,2749 | tak | **NIE** |
| mokra | 0,13 | tylko napędne | 0,6667 | **0,7870** | 0,8499 | **NIE** | **NIE** |

**Sufit nie zależy od masy składu.** Masa skraca się w `F/(m·λ)`, więc AW0 i AW2 mają
ten sam sufit i różnią się wyłącznie siłą do przeniesienia (test
`Sufit_opoznienia_nie_zalezy_od_masy_a_sila_zalezy_liniowo`).

### 2.1 Progi krytyczne — przy jakim udziale osi i jakim μ model przestaje działać

`f_min = b · λ / (μ · g)`, `μ_min = b · λ / (f · g)`.

| żądanie | szyna | `f_min` | `μ_min` przy f = 1 | wniosek |
|---|---|---:|---:|---|
| służbowe 1,10 m/s² | sucha | 0,4846 | — | wystarczy niecała połowa osi |
| służbowe 1,10 m/s² | mokra | **0,9319** | 0,1211 | trzeba ponad **93 %** masy na osiach hamowanych |
| awaryjne 1,30 m/s² | sucha | 0,5727 | — | wystarczy 57 % osi |
| awaryjne 1,30 m/s² | mokra | **1,1013** | 0,1432 | **nieosiągalne przy każdym układzie hamulcowym** |

**To jest główny wynik tego zadania i był tylko podejrzeniem, dopóki go nie policzyłem.**
Przy μ = 0,13 hamowanie awaryjne 1,30 m/s² wymagałoby, żeby na osiach hamowanych
spoczywało 110 % masy składu. Takiego układu nie ma. Wniosek **nie zależy** od decyzji
o masach wirujących: bez współczynnika λ potrzebny udział to nadal 1,0197, a potrzebne
μ to 0,1326 — czyli więcej niż 0,13 z rejestru.

Do sprawdzenia ręcznie: `1,30 · 1,08 / (0,13 · 9,80665) = 1,404 / 1,274865 = 1,1013`.

**Czego to nie znaczy.** Nie znaczy, że M7 nie zahamuje na mokrej szynie. Znaczy, że
**trzy wartości `design_model` z `docs/02-simulation.md` — 1,30 m/s², μ = 0,13 i
implikowany udział osi — nie mogą być prawdziwe naraz.** Która z nich jest do
poprawienia, jest decyzją projektową (`CLAUDE.md` §8), a nie zmianą w rdzeniu; §6.

### 2.2 Druga, niezależna droga

Wzór na próg krytyczny sprawdzony **skanowaniem** udziału osi krokiem 10⁻⁶:

```
[SKAN] f_min ze wzoru = 0.931863739, ze skanu 1000000 kroków = 0.931864000, |Δ| = 2.608E-007
```

Rozjazd mieści się w jednym kroku skanu, czyli wzór i skan mówią to samo.

---

## 3. Solver punktu hamowania

To jest właściwy produkt zadania i to jest to, czego potrzebuje T-313.

`docs/02-simulation.md` ma ograniczenie zrywu 0,75 m/s³, więc **szkolne `v²/2a` jest
tu po prostu błędne**. Opóźnienie narasta od zera, więc droga ma dwie części:
narastanie zrywem (`t_r = b/j`) i odcinek o stałym opóźnieniu. Po scałkowaniu:

```
s(b) = (v₀² − v₁²) / (2b)  +  v₀·b / (2j)  −  b³ / (24 j²)
t(b) = (v₀ − v₁) / b       +  b / (2j)
```

Pierwszy człon to szkolny wzór; dwa pozostałe są ceną zrywu i znikają przy `j → ∞`
(test `Przy_nieskonczonym_zrywie_wzor_zbiega_do_v2_przez_2a`: człon zrywu maleje
dokładnie jak `1/j`, iloraz 10,00 przy dziesięciokrotnym wzroście `j`).

### 3.1 Zryw stawia twardą granicę, o której warto wiedzieć

Powyżej `b = √(2 j Δv)` prędkość docelowa wypada jeszcze **w trakcie narastania**
hamulca, więc mocniejszy hamulec nie skraca już niczego. Najkrótsza droga, jaką
dopuszcza sam zryw 0,75 m/s³:

| v₀ [km/h] | 30 | 40 | 50 | 60 | 70 | 80 |
|---|---:|---:|---:|---:|---:|---:|
| minimum ze zrywu [m] | 26,189 | 40,321 | 56,350 | 74,074 | 93,344 | **114,044** |

```
[ZRYW] z 80 km/h przy zrywie 0.75 m/s³ nie da się stanąć krócej niż na 114.044 m
       (b progowe 5.7735 m/s²)
```

Poniżej tej drogi solver **nie zwraca liczby** — zgłasza wyjątek z podaną granicą.
„Prawie" nie jest odpowiedzią na pytanie o punkt hamowania.

### 3.2 Odwrotność: jakie opóźnienie na zadanej drodze

Bisekcja o stałej liczbie kroków (200), więc wynik jest deterministyczny co do bitu.

| v₀ → 0 | droga [m] | `b` wymagane [m/s²] | kontrola `s(b)` [m] | \|Δ\| |
|---|---:|---:|---:|---:|
| 80 km/h | 150 | 2,053974 | 150,000000 | 0 |
| 80 km/h | 200 | 1,372864 | 200,000000 | 0 |
| 80 km/h | 240 | 1,103519 | 240,000000 | 0 |
| 80 km/h | 300 | 0,859382 | 300,000000 | 0 |
| 80 km/h | 400 | 0,632050 | 400,000000 | 0 |

Wiersz „240 m" wart jest osobnego spojrzenia: `b = 1,1035` m/s² wobec projektowego
hamowania służbowego 1,10 m/s². Punkt hamowania z T-400 (chainage 6420,0 m, dobrany
ręcznie „na oko" do zmierzonej drogi 240,5 m) był więc trafiony z dokładnością do
0,3 % — ale dopiero teraz jest to policzone, a nie zgadnięte.

### 3.3 Solver kontra sufit — kiedy żądanie przestaje być wykonalne

Połączenie §2 i §3. Dla każdego przypadku: wymagane opóźnienie i to, czy mieści się
pod sufitem przyczepnościowym.

| v₀ [km/h] | droga [m] | `b` wymagane | sucho, f = 4/6 | mokro, f = 1 | mokro, f = 4/6 |
|---:|---:|---:|:--:|:--:|:--:|
| 50 | 150 | 0,6707 | OK | OK | OK |
| 50 | 250 | 0,3915 | OK | OK | OK |
| 60 | 150 | 0,9994 | OK | OK | **NIE** |
| 60 | 200 | 0,7234 | OK | OK | OK |
| 70 | 150 | 1,4365 | OK | **NIE** | **NIE** |
| 70 | 200 | 1,0111 | OK | OK | **NIE** |
| 80 | 150 | 2,0540 | **NIE** | **NIE** | **NIE** |
| 80 | 200 | 1,3729 | OK | **NIE** | **NIE** |
| 80 | 250 | 1,0530 | OK | OK | **NIE** |

Sufity: sucho f = 4/6 → 1,5134; mokro f = 1 → 1,1804; mokro f = 4/6 → 0,7870 m/s².

### 3.4 Druga, niezależna droga: wzór zamknięty vs całkowanie krokiem stałym

Wzór jest analityczny, model krokowy jest numeryczny. Muszą się spotkać przy `dt → 0`,
i to **liniowo**, bo schemat jest pierwszego rzędu:

```
[ZBIEŻNOŚĆ] dt = 1/120 s:   krokowo 240.479420 m, wzór 240.664595 m, błąd 0.185175 m
[ZBIEŻNOŚĆ] dt = 1/1200 s:  krokowo 240.646076 m, wzór 240.664595 m, błąd 0.018518 m
[ZBIEŻNOŚĆ] dt = 1/12000 s: krokowo 240.662743 m, wzór 240.664595 m, błąd 0.001852 m
```

Iloraz błędów 10,000 i 10,000 — zbieżność dokładnie pierwszego rzędu. Test wymaga
ilorazu 10 ± 0,05, więc wywróci się, gdy wzór i model przestaną być tą samą fizyką.

**Praktyczna konsekwencja dla T-313:** wzór zawyża drogę o 0,185 m na 240 m przy kroku
rdzenia. To zawyżenie działa po stronie bezpiecznej (każe hamować wcześniej) i jest
o rząd wielkości mniejsze od skrócenia, jakie dają opory ruchu (§4).

---

## 4. Droga hamowania z oporami — tablica referencyjna

Hamulec służbowy 1,10 m/s², zryw 0,75 m/s³, krok 1/120 s, AW2, poziom.
„Bez oporów" to model kinematyczny z T-310; tunel `c = 1,40`, powierzchnia `c = 1,00`.

| v₀ [km/h] | wzór [m] | bez oporów [m] | tunel [m] | powierzchnia [m] | skrócenie tunel [m] | skrócenie pow. [m] | z bilansu energii tunel / pow. [m] |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 30 | 37,578 | 37,509 | 36,928 | 36,950 | 0,581 | 0,559 | 0,574 / 0,552 |
| 40 | 64,166 | 64,074 | 62,969 | 63,034 | 1,104 | 1,040 | 1,096 / 1,032 |
| 50 | 97,769 | 97,653 | 95,760 | 95,910 | 1,893 | 1,743 | 1,883 / 1,734 |
| 60 | 138,386 | 138,247 | 135,216 | 135,516 | 3,031 | 2,732 | 3,018 / 2,721 |
| 70 | 186,018 | 185,856 | 181,241 | 181,779 | 4,615 | 4,077 | 4,599 / 4,064 |
| 80 | 240,665 | 240,479 | **233,723** | **234,617** | **6,757** | **5,863** | **6,738 / 5,847** |

Wiersz 80 km/h w tunelu odtwarza liczby zmierzone w T-400 (`reports/T-400-first-run.md`
§3.6): 240,479 m → 233,723 m, skrócenie 6,757 m, z bilansu 6,738 m, rozjazd 0,019 m.
Reszta tablicy jest nowa.

**Droga hamowania z oporami nie zależy od masy składu** — i to jest wynik, nie
niedopatrzenie. Davis liczy się na tonę, więc opóźnienie od oporów to
`r · g / (1000 · λ)` i masa skraca się tak samo, jak w suficie przyczepnościowym:

```
[MASA] AW0 233.722779495 m, AW2 233.722779495 m, |Δ| = 0.000E+000 m
```

### 4.1 Bilans energii — druga droga, także na pochyleniu

`½·m_ef·(v₀² − v_k²) = W_oporów + W_hamulca + W_pochylenia + W_dyskretyzacji`

```
[BILANS] pochylenie  0.0%: s = 233.723 m, ..., reszta = -4.235E-008 J, względnie = 7.155E-016
[BILANS] pochylenie  3.0%: s = 188.287 m, ..., reszta =  1.760E-007 J, względnie = 2.974E-015
[BILANS] pochylenie -3.0%: s = 307.968 m, ..., reszta = -8.453E-008 J, względnie = 1.428E-015
[POCHYLENIE] poziom 233.723 m, −3% 307.968 m, +3% 188.287 m
```

Domknięcie do precyzji `double` w każdym z trzech przypadków. Pochylenie w bilansie
jest nowe wobec T-400, który miał tylko przypadek poziomy.

**Ten test coś złapał.** Pierwsza wersja `BrakingRun` podawała kontrolerowi prędkość
początkową jako ograniczenie prędkości. Na pochyleniu −3 % składowa ciężaru przewyższa
opóźnienie hamulca, zanim ten narośnie zrywem, więc skład przez ~1 s **przyspiesza** —
a obcięcie do prędkości startowej zjadało tę część ruchu i bilans przestawał się
domykać: reszta względna **2,979·10⁻³** zamiast 10⁻¹⁶. Ograniczenie prędkości jest
sprawą sygnalizacji, nie hamowania; przebieg dostaje teraz `double.MaxValue`
i powód jest opisany w kodzie w miejscu, w którym działa.

---

## 5. Weryfikacja — rzeczywiste wyjście

### 5.1 `dotnet build MetroBxl.sln --configuration Release`

```
  Sim -> src/Sim/bin/Release/net8.0/MetroBxl.Sim.dll
  Sim.Runner -> src/Sim.Runner/bin/Release/net8.0/MetroBxl.Sim.Runner.dll
  Sim.Tests -> tests/Sim.Tests/bin/Release/net8.0/MetroBxl.Sim.Tests.dll

Build succeeded.
    0 Warning(s)
    0 Error(s)
```

### 5.2 `dotnet test tests/Sim.Tests` — było 127, jest 173

```
Passed!  - Failed:     0, Passed:   173, Skipped:     0, Total:   173, Duration: 521 ms - MetroBxl.Sim.Tests.dll (net8.0)
```

### 5.3 `python3 tools/tests/test_all.py` — było 367, jest 389

```
  389/389 przeszło
```

### 5.4 `bash doctor.sh`

```
Testy narzędzi:
  ok    389/389 przeszło

Testy rdzenia symulacji:
  ok    173/173 przeszło

--------------------------------------------------
  Baza projektu jest gotowa. Następne zadanie: T-010.
  1 narzędzi opcjonalnych brakuje; instaluj je dopiero przed zadaniem, które ich wymaga.

exit=0
```

(Brakujące narzędzie opcjonalne to Godot — jak w T-400. Zadanie nie dotyka sceny.)

### 5.5 Rdzeń kontra niezależna referencja Pythona — co do bajtu

`src/Sim.Runner braking` i `tools/physics/braking.py` liczą te same tablice dwiema
niezależnymi drogami. Porównanie całego wyjścia:

```
$ dotnet run --project src/Sim.Runner -c Release -- braking > /tmp/braking_core.txt
$ python3 tools/physics/braking.py > /tmp/braking_reference.txt
$ diff -u /tmp/braking_reference.txt /tmp/braking_core.txt && echo IDENTYCZNE
IDENTYCZNE
```

Wewnątrz testów rozjazd jest zmierzony osobno, na pełnej precyzji:

```
[TABLICA] największy rozjazd z referencją Pythona = 0.000E+000 m
```

Zero, nie „małe epsilon" — mimo że kontroler w C# składa siły i dzieli przez masę
efektywną, a referencja składa opóźnienia. Próg w teście to i tak 10⁻⁹ m, bo na
zgodność co do bitu przy różnej kolejności działań nie wolno liczyć jako na regułę.

Ta sama para jest **bramką w CI** (`.github/workflows/sim-tests.yml`, krok
„Braking reference matches the core byte for byte") — `diff` wywraca job.

### 5.6 Parytet T-400 — zero rozjazdu wobec `origin/main`

`CLAUDE.md` i brief wymagają, żeby przejazd z T-400 został co do bitu. Dowód jest
liczbowy: ten sam scenariusz policzony binarką z `origin/main` i binarką z tej gałęzi.

```
$ git worktree add …/mainwt origin/main
$ dotnet run --project …/mainwt/src/Sim.Runner -c Release -- drive --out build/t311/core_main.csv
$ dotnet run --project src/Sim.Runner       -c Release -- drive --out build/t311/core_t311.csv

$ sha256sum build/t311/core_main.csv build/t311/core_t311.csv
8183100f0cced5bd5a088b00b2e50afc79726479329598204f1095d77fc953d4  build/t311/core_main.csv
8183100f0cced5bd5a088b00b2e50afc79726479329598204f1095d77fc953d4  build/t311/core_t311.csv
```

Ten sam odcisk, który stoi w `reports/T-400-first-run.md` §3.7 dla przejazdu w Godocie.

```
$ dotnet run --project src/Sim.Runner -c Release -- compare \
      build/t311/core_main.csv build/t311/core_t311.csv --tolerance 0
[PORÓWNANIE] wierszy=320 identyczne co do bajtu=TAK
[PORÓWNANIE] step         max |Δ| = 0.000E+000 (wiersz 0) ok
[PORÓWNANIE] t_s          max |Δ| = 0.000E+000 (wiersz 0) ok
[PORÓWNANIE] chainage_m   max |Δ| = 0.000E+000 (wiersz 0) ok
[PORÓWNANIE] distance_m   max |Δ| = 0.000E+000 (wiersz 0) ok
[PORÓWNANIE] speed_mps    max |Δ| = 0.000E+000 (wiersz 0) ok
[PORÓWNANIE] speed_kmh    max |Δ| = 0.000E+000 (wiersz 0) ok
[PORÓWNANIE] accel_mps2   max |Δ| = 0.000E+000 (wiersz 0) ok
[PORÓWNANIE] throttle     max |Δ| = 0.000E+000 (wiersz 0) ok
[PORÓWNANIE] brake        max |Δ| = 0.000E+000 (wiersz 0) ok
[PORÓWNANIE] próg = 0.000E+000
```

```
$ dotnet run --project src/Sim.Runner -c Release -- parity
[PARYTET] Aw0: kroki 3023 vs 3023 (==), droga 337.478 m vs 337.478 m (co do bitu)
[PARYTET] Aw2: kroki 3998 vs 3998 (==), droga 447.920 m vs 447.920 m (co do bitu)
[HAMOWANIE] kinematyczne (T-310) 240.479 m / 20.933 s, kontroler z oporami 233.723 m / 20.450 s,
            różnica 6.757 m = praca oporów Davisa
```

Do tego test, który przypina to na stałe, żeby przyszła zmiana w hamowaniu nie
przesunęła przejazdu po cichu:

```
[T-400] kroków = 38194, chainage = 6653.791185780133 m, powód = stopped
```

### 5.7 Kontrola negatywna — test, który nie pada, niczego nie dowodzi

Zepsute **dwa miejsca** w modelu hamowania: sufit przyczepnościowy bez współczynnika
mas wirujących (`/ EffectiveMassFactor` usunięte) i wzór zamknięty z `48` zamiast `24`
w mianowniku członu zrywu.

```
$ git diff --stat
 src/Sim/Physics/BrakeAdhesionLimit.cs | 2 +-
 src/Sim/Physics/BrakingPointSolver.cs | 2 +-
 2 files changed, 2 insertions(+), 2 deletions(-)

$ dotnet test tests/Sim.Tests
Failed!  - Failed:    19, Passed:   154, Skipped:     0, Total:   173
```

**19 testów ze 173.** Które:

```
Czas_ze_wzoru_zgadza_sie_z_rozbiciem_na_fazy
Droga_maleje_monotonicznie_wraz_z_opoznieniem
Droga_ze_wzoru_zamknietego_zgadza_sie_z_referencja_co_do_bitu
Prog_krytyczny_jest_odwrotnoscia_sufitu (0.4 / 0.8 / 1.1 / 1.3 / 2.0)
Prog_krytyczny_zgadza_sie_ze_skanem_udzialu_osi
Solver_i_droga_sa_wzajemnie_odwrotne (150 / 200 / 240 / 300 / 400 m)
Sufit_opoznienia_nie_zalezy_od_masy_a_sila_zalezy_liniowo
Sufit_przyczepnosciowy_obcina_zadanie_i_wydluza_droge
Sufit_przyczepnosciowy_zgadza_sie_z_referencja_co_do_bitu
Tablica_referencyjna_zgadza_sie_z_referencja_Pythona
Wzor_zamkniety_jest_granica_modelu_krokowego_przy_dt_do_zera
```

Bramka CI też to łapie — i pokazuje **liczbę**, nie tylko czerwony krzyżyk:

```
$ diff -u /tmp/b_ref.txt /tmp/b_core.txt
-dry   0.25   all-axles           1.0000    2.2701            2.4517   tak   tak
+dry   0.25   all-axles           1.0000    2.4517            2.4517   tak   tak
-wet   0.13   powered-axles-only  0.6667    0.7870            0.8499   NIE   NIE
+wet   0.13   powered-axles-only  0.6667    0.8499            0.8499   NIE   NIE
diff exit=1
```

Osobno zepsuta referencja Pythona (sufit przemnożony o 2 %), żeby było widać, że
22 nowe testy narzędzi też gryzą, a nie tylko liczą się do sumy:

```
  FAIL test_adhesion_ceiling_does_not_depend_on_train_mass: 170000.0
  FAIL test_ceiling_and_critical_fraction_are_mutual_inverses: (0.4, 0.25)
  FAIL test_critical_fraction_matches_an_independent_scan: (0.91323, 0.9318637392444453)
  386/389 przeszło
```

Wycofanie zmiany:

```
$ git checkout -- src/Sim/Physics/BrakeAdhesionLimit.cs src/Sim/Physics/BrakingPointSolver.cs \
                  tools/physics/braking.py
$ git diff
$ git diff --stat | wc -l
0

$ dotnet test tests/Sim.Tests
Passed!  - Failed:     0, Passed:   173, Skipped:     0, Total:   173
$ python3 tools/tests/test_all.py | tail -1
  389/389 przeszło
```

### 5.8 CI na `ubuntu-latest` (PR #78)

`CLAUDE.md` §9: `queued` nie jest weryfikacją. Wyjście zakończonego joba `Sim core tests`
(`.github/workflows/sim-tests.yml`), razem z nowym krokiem bramkującym:

```
Test Run Successful.
Total tests: 173
     Passed: 173
 Total time: 3.8877 Seconds

Build succeeded.
    0 Warning(s)
    0 Error(s)

src/Sim: brak odwołań do Godota
src/Sim: zero PackageReference
tablice hamowania: rdzeń == referencja, co do bajtu
```

`Python tool tests` — success (389/389). Pozostałe workflow (`Blender smoke`,
`Godot first run`, `Tunnel alignment`, `Visual regression`, `M7 shell`) nie dotyczą
tego zadania i nie zostały tknięte; ich stan jest widoczny na PR.

---

## 6. Czego świadomie nie zrobiłem

1. **Rozdziału hamulca elektrodynamicznego i pneumatycznego — nie ma i nie będzie
   bez źródła.** W rejestrze nie ma proporcji ED/P, progu zanikania ED przy niskiej
   prędkości ani sprawności odzysku. Karta M7 potwierdza **sam fakt** hamowania
   odzyskowego i nic ponadto. Model, który dzieli siłę hamowania na dwa człony
   z wymyśloną proporcją, wygląda dokładnie tak samo jak model prawdziwy — a to jest
   sytuacja opisana w regule 1. `BrakingEnergyAccount.BrakeWorkJ` jest **całą** pracą
   hamulca, bez rozbicia.
2. **Krzywych bezpieczeństwa STIB.** `docs/02-simulation.md` wprost zabrania
   przypisywania STIB niepublikowanych krzywych i aspektów. Solver z §3 daje T-313
   surową geometrię hamowania; margines bezpieczeństwa, czas reakcji i kształt krzywej
   nadzoru to decyzja, a nie obliczenie.
3. **Nie wpiąłem sufitu przyczepnościowego w `TrainController`.** Wymagałoby to
   wybrania **jednego** udziału osi hamowanych i wpisania go na stałe — czyli
   podjęcia za właściciela repo decyzji o liczbie bez pokrycia. Sufit jest opcjonalnym
   argumentem `BrakingRun` i osobnym modelem. Warto wiedzieć, że **na suchej szynie
   wpięcie go nie zmieniłoby niczego** (test `Na_suchej_szynie_sufit_nie_zmienia_drogi_hamowania`
   pokazuje zgodność co do bitu dla obu wariantów), więc przejazd z T-400 wyglądałby
   identycznie; różnica pojawia się dopiero na mokrym torze.
4. **Nie zmieniłem 1,30 m/s², μ = 0,13 ani 4/6 w rejestrze.** §2.1 pokazuje, że te
   trzy liczby nie mogą być prawdziwe naraz, ale `data/` jest tylko do odczytu
   (reguła 6), a wybór, którą z nich poprawić, jest decyzją projektową.
   **To jest pozycja do rozstrzygnięcia przez właściciela.**
5. **Nie ruszałem `TrainController.Advance`, `TrainDynamics`, `ServiceBrakingRun`
   ani `tools/physics/reference.py`.** Parytet T-400 jest w §5.6 dowiedziony liczbowo,
   a nie zadeklarowany.
6. **Nie dodałem hamulca postojowego.** `TrainController` wciąż nie odtacza się
   w tył wyłącznie przez obcięcie prędkości do zera — komentarz w kodzie odsyłał do
   T-311, ale hamulec postojowy jest stanem pojazdu i mechaniką postoju, czyli
   materiałem T-312, a nie modelem hamowania. Zostawiłem to bez zmiany i bez
   przepisywania komentarza, żeby nie ruszać pliku spoza zakresu.
7. **Nie dotykałem `tools/visual/`, `tools/ci/tunnel_alignment.sh`,
   `tools/ci/vehicle_clearance.sh`, `tools/blender/profile_vehicle.py`** ani `data/`.
   Nie zamykałem żadnego Issue i nie ruszałem PR-ów.

---

## 7. Zauważone przy okazji, nie tknięte

1. **Punkt hamowania w `DriveScenario.PackageAFirstRun` jest dobrany ręcznie.**
   Chainage 6420,0 m z komentarzem „dobrany do zmierzonej drogi hamowania 240,5 m".
   Solver z §3 policzyłby go teraz z osi i prędkości. Przepisanie scenariusza
   zmieniłoby jednak przejazd z T-400, czyli dokładnie tę liczbę, której brief
   kazał pilnować — więc zostawiłem, a wynik odnotowałem w §3.2.
2. **`docs/02-simulation.md` deklaruje „przyspieszenie maks. 1,10 m/s²", a model daje
   1,342 m/s² dla AW0.** Zgłoszone już w `reports/T-310-physics.md` §9.1 i nadal
   otwarte. T-311 dokłada do tego bliźniaczą obserwację po stronie hamowania (§2.1):
   ten sam dokument deklaruje 1,30 m/s² awaryjnego przy μ = 0,13, czego przyczepność
   nie przenosi. Obie rozbieżności dotyczą tego samego zestawu `design_model`
   i sensownie byłoby rozstrzygnąć je razem.
3. **Sufit przyczepnościowy dla trakcji i dla hamowania używa dwóch różnych
   znaczeń tego samego 4/6.** W `TractionModel` jest to udział masy na osiach
   napędnych; w `BrakeAdhesionLimit` — wariant „hamują tylko osie napędne".
   Liczba ta sama, znaczenie inne; opisałem to w obu miejscach, ale gdyby R-005
   przyniósł kiedyś prawdziwy układ napędu i hamulca, są to dwa różne parametry
   i trzeba je rozdzielić.
4. **`doctor.sh` nadal kończy się zdaniem „Następne zadanie: T-010"**, choć T-010
   i pakiet T-2xx są zrobione. Odnotowane już w T-310 §9.2; nadal poza zakresem.
5. **Bezpiecznik pętli `BrakingRun` to 120 s, jak w `ServiceBrakingRun`.** Na
   pochyleniu stromszym niż ok. −10 % przy hamowaniu służbowym skład nie zatrzyma się
   w ogóle i przebieg skończy się `RunOutcome.TimeLimit`. Jest to zachowanie poprawne
   i jawne, ale żaden odcinek sieci nie ma dziś profilu pionowego (`not_modelled`),
   więc nie ma na czym tego sprawdzić na prawdziwych danych — dopiero T-112.
