# 6.A5 · Bilans energii przejazdu z odzyskiem i bez

**Zmierzone 06.09.2026 na commicie:** `d48f5a1d79396208b2459c3f9090db11833097fa`

(Ten SHA jest commitem tej sesji na `claude/6a5-bilans-energii`, który już niósł kod
i testy z tego raportu — `src/` i `tests/` identyczne co do bajtu z tym, na czym
mierzono w sekcji 3. Ostatni `git commit --amend` tej sesji dopisał do tego samego
commita wyłącznie ten akapit, więc końcowy SHA na gałęzi różni się od powyższego
o ten jeden akapit — ten sam kompromis, który `tools/tests/test_report_hygiene.py`
świadomie akceptuje dla SHA po squash-merge: kształt pola się liczy, nie osiągalność
obiektu.)

Zakres: `docs/TASKS.md`, 6.A5. Model: `docs/02-simulation.md` §Hamowanie,
`docs/21-measured-vs-assumed.md` §4b. Wejście: `src/Sim/Physics/EnergyAccount.cs` (T-310),
`src/Sim/Physics/BrakingEnergyAccount.cs` (T-311, `reports/T-311-braking.md` §4.1),
`src/Sim/Train/LineRun.cs`, `src/Sim.Runner/Program.cs`.

---

## 0. Co zrobiłem, w jednym zdaniu

`LineRun`/`LineDrive` liczyły fizykę całego przejazdu z zatrzymaniami od T-401, ale nikt
nie sumował z niej energii — dołożyłem `TripEnergyAccount` (bilans CAŁEGO przejazdu,
druga niezależna droga do wyniku, na wzór T-310 i T-311) i polecenie `line` w
`Sim.Runner` teraz drukuje pracę trakcji i pracę hamulca w kWh, razem z netto z sieci
dla dwóch wariantów SKRAJNYCH odzysku — 0 % i 100 % — bez wpisywania jakiejkolwiek
sprawności odzysku, której karta M7 nie podaje.

---

## 1. Dlaczego osobny typ, a nie rozszerzenie `EnergyAccount`

`EnergyAccount` (T-310) zna tylko trakcję — pojedynczy rozruch bez hamowania.
`BrakingEnergyAccount` (T-311) zna tylko hamulec — pojedyncze hamowanie bez trakcji.
Przejazd liniowy robi oba na przemian, w jednej pętli, ze wspólnym postojem na każdej
stacji pośredniej: rozruch → wybieg → hamowanie → drzwi → rozruch... Dopisanie pracy
hamulca do `EnergyAccount` zmieniłoby znaczenie pola, które T-310 już opisał i przypiął
testem (`EnergyAccountTests.cs`); rozdzielenie na dwa osobne bilanse dla jednego
przejazdu policzyłoby energię kinetyczną między stacjami dwa razy. Stąd nowy typ,
`MetroBxl.Sim.Train.TripEnergyAccount` w `src/Sim/Train/LineRun.cs`, obok
`LineRunResult`, którego jest teraz polem (`Energy`).

Wyprowadzenie równania kroku jest tym samym rachunkiem co w `AccelerationRun` (T-310),
z dodatkowym członem hamulca w sile wypadkowej: kontroler liczy przyspieszenie jako
`(F_trakcji − F_oporu − F_pochylenia)/m_ef − b_hamulca`, więc siła wypadkowa WSZYSTKIEGO
to `forces.NetN − m_ef·b_hamulca`. Ten sam rachunek algebraiczny, który T-310 robi dla
samej trakcji, rozkłada iloczyn tej siły i przebytej drogi na zmianę energii
kinetycznej, człon dyskretyzacji i obcięcie — teraz sumowane po KAŻDYM kroku całego
przejazdu (jazda i postój jednakowo), a nie tylko po samym rozruchu. Kod:
`LineDrive.AccumulateEnergy` (`src/Sim/Train/LineDrive.cs`).

## 2. Dwa warianty skrajne odzysku — nie sprawność

`BrakingEnergyAccount.cs` mówi wprost: „To jest energia mechaniczna, nie odzysk. Karta
M7 potwierdza sam fakt hamowania odzyskowego i nic ponadto." Wpisanie jakiejkolwiek
liczby pomiędzy 0 a 100 % byłoby zmyśloną liczbą o taborze (`CLAUDE.md` §1 i §8) —
dokładnie tak, jak T-311 potraktowało udział osi hamowanych (`AllAxlesBrakedMassFraction`
i `PoweredAxlesBrakedMassFraction`, dwa warianty skrajne zamiast jednej liczby). Dlatego
`TripEnergyAccount.NetGridWorkKwh` przyjmuje wyłącznie `bool fullRecovery`:

- `false` (0 % odzysku) → netto = `TractionWorkKwh` (cały hamulec grzeje opory, nic nie
  wraca do sieci);
- `true` (100 % odzysku) → netto = `TractionWorkKwh − BrakeWorkKwh` (cała praca
  mechaniczna hamulca wraca do sieci).

Prawdziwa wartość M7 leży gdzieś w tym przedziale — i tyle da się dziś powiedzieć bez
zmyślania.

---

## 3. Weryfikacja — rzeczywiste wyjście

### 3.1 `dotnet build MetroBxl.sln -c Release`

```
Build succeeded.
    0 Warning(s)
    0 Error(s)
```

### 3.2 `dotnet test tests/Sim.Tests -c Release`

```
Passed!  - Failed:     0, Passed:   498, Skipped:     0, Total:   498, Duration: 13 s - MetroBxl.Sim.Tests.dll (net10.0)
```

### 3.3 `python3 tools/tests/test_all.py`

```
1638/1638 przeszło
```

### 3.4 `bash doctor.sh`

```
Testy narzędzi:
  ok    1638/1638 przeszło

Testy rdzenia symulacji:
  ok    498/498 przeszło

--------------------------------------------------
  Baza projektu jest gotowa. ...
exit=0
```

### 3.5 Polecenie z sekcji Weryfikacja zadania — pakiet A, L1_A

```
$ dotnet run --project src/Sim.Runner -c Release -- line --axis data/track/L1_A.json \
    --limit-kmh 72 --exchange-s 20 --trace build/energy-A.csv
```

```
[LINIA] ślad 101872 kroków -> build/energy-A.csv
[LINIA] L1_A: 11 zatrzymań, 6686.05 m, 820.42 s, postoje 313.59 s, kroków 101872, koniec=arrived
[LINIA] limit 72.00 km/h, wymiana 20.0 s, hamulec 100 % służbowego, okno stacji 5.0 m, obciążenie AW0 170000 kg
...
[LINIA] największy błąd zatrzymania: 0.307 m
[ENERGIA] E_trakcji = 142.4515 kWh, E_hamulca = 104.3574 kWh, opory = 39.900 MJ, pochylenie = 0.000 MJ, ΔE_kin = 0.000 MJ, dyskretyzacja = 349052.8 J, obcięcie = 96889720.4 J, reszta = -1.907E-006 J, względnie = 2.147E-015
[ENERGIA] netto z sieci przy odzysku 0%: 142.4515 kWh, przy odzysku 100%: 38.0941 kWh
```

Kod wyjścia: `0` (`koniec=arrived`). Względne niedomknięcie bilansu na CAŁYM przejeździe
(11 zatrzymań, 101 872 kroki, 6686,05 m) to **2,147·10⁻¹⁵** — poniżej progu z
`reports/T-310-physics.md` (`EnergyClosureTolerance = 1e-12` w
`tests/Sim.Tests/EnergyAndProfileTests.cs`), mimo że przejazd ma **kilkanaście razy
więcej kroków** niż pojedynczy rozruch, który ten próg ustalił. To jest druga,
niezależna droga do wyniku: rachunek sił po kroku i całkowanie ruchu mówią to samo.

**Pakiet A, obciążenie AW0, limit 72 km/h, wymiana 20 s — dwa warianty skrajne:**

| wariant odzysku | E_trakcji [kWh] | E_hamulca [kWh] | netto z sieci [kWh] |
|---|---:|---:|---:|
| 0 % (nic nie wraca) | 142,4515 | 104,3574 | **142,4515** |
| 100 % (wszystko wraca) | 142,4515 | 104,3574 | **38,0941** |

Prawdziwe zużycie sieciowe leży gdzieś między 38,09 a 142,45 kWh na ten przejazd —
przedział, nie punkt, bo sprawności odzysku nie ma w żadnym źródle.

### 3.6 Testy dodane dla `TripEnergyAccount` (`tests/Sim.Tests/EnergyAndProfileTests.cs`)

```
$ dotnet test tests/Sim.Tests -c Release --filter "FullyQualifiedName~EnergyAndProfileTests"
Passed!  - Failed:     0, Passed:    13, Skipped:     0, Total:    13, Duration: ~1 s - MetroBxl.Sim.Tests.dll (net10.0)
```

Konsola jednego z nich (oś syntetyczna, 3 stacje pośrednie, AW2, poziom):

```
pakiet testowy poziom: E_trakcji = 68.5827 kWh, E_hamulca = 27.0613 kWh, opory = 23.339 MJ, pochylenie = 0.000 MJ, ΔE_kin = 0.000 MJ, dyskretyzacja = 96922.5 J, obcięcie = 126040922.6 J, reszta = 8.956E-006 J, względnie = 2.601E-014
```

### 3.7 Kontrola negatywna — WYKONANA, nie opisana

Odwrócony znak członu hamulca w `LineDrive.AccumulateEnergy`
(`netAll = forces.NetN - (...)` → `+ (...)`), czyli dokładnie ten błąd, który zepsułby
bilans, gdyby praca hamulca miała zły znak w rachunku sił. Rzeczywiste wyjście PRZED
odwróceniem z powrotem:

```
  Failed Bilans_energii_calego_przejazdu_z_zatrzymaniami_domyka_sie [186 ms]
  Error Message:
   Assert.IsTrue failed. bilans nie domyka się: 5.659E-001
  Standard Output Messages:
 pakiet testowy poziom: E_trakcji = 68.5827 kWh, E_hamulca = 27.0613 kWh, opory = 23.339 MJ, pochylenie = 0.000 MJ, ΔE_kin = 0.000 MJ, dyskretyzacja = 96922.5 J, obcięcie = 320882196.4 J, reszta = -1.948E+008 J, względnie = 5.659E-001

  Failed Bilans_calego_przejazdu_domyka_sie_takze_na_pochyleniu [113 ms]
  Error Message:
   Assert.IsTrue failed. pod górę: 3.472E-001

Total tests: 13
     Passed: 11
     Failed: 2
```

Względne niedomknięcie skoczyło z **2,6·10⁻¹⁴** do **5,66·10⁻¹**, czyli o piętnaście
rzędów wielkości — dokładnie tak zapaliła się bramka, którą miała zapalić. Mutacja
cofnięta, `dotnet test --filter "FullyQualifiedName~EnergyAndProfileTests"` z powrotem
`13/13`.

---

## 4. Czego świadomie nie zrobiłem i dlaczego

- **Sprawności odzysku.** Poza zakresem twardo (§2 wyżej i `docs/TASKS.md` 6.A5).
  Karta M7 potwierdza sam fakt hamowania odzyskowego i nic ponadto — 4/6, 60 %, 70 %,
  cokolwiek pomiędzy 0 a 100 % byłoby liczbą wymyśloną o taborze.
- **Podziału na hamulec elektrodynamiczny i pneumatyczny** oraz progu zanikania ED przy
  niskiej prędkości — to samo ograniczenie źródeł co w T-311, nie zmienione tym
  zadaniem.
- **Sprawności przetwornic, silników i przekładni, poboru potrzeb własnych.**
  `TractionWorkKwh` jest energią mechaniczną na obwodzie kół — dokładnie tak samo
  zastrzeżone w `EnergyAccount.cs` od T-310 i nietknięte tu.
- **CLI-owej flagi wyboru wariantu odzysku.** Oba warianty skrajne liczą się i drukują
  ZAWSZE razem (`Program.cs`, polecenie `line`) — jak referencja tunel/powierzchnia
  w `BrakingRun.ReferenceTable` z T-311 — więc nie ma parametru, którym dałoby się po
  cichu wpisać trzecią, wymyśloną wartość.

## 5. Co zauważyłem przy okazji, ale nie tknąłem

- `LineDrive.Step()` woła `_controller.Advance(...)` z `out _`, odrzucając rozbicie sił
  (`StepForces`) w obu miejscach, w których to robi — musiałem to zmienić na `out var
  forces`, żeby zebrać energię, ale poza tym zachowaniem kroku nie tknąłem: ślad
  (`trace`) i wynik pętli wychodzą bit w bit takie same jak przed tą zmianą (żaden test
  regresji `Ten_sam_przejazd_dwa_razy_daje_te_same_liczby_co_do_bitu` ani żaden test
  `LineCoreTests.cs` porównujący ślad rdzenia ze sceną nie poruszył się).
- `reports/T-401-line-run.md` §2 i §3 w przeszłości rozjeżdżały się ze sobą (patrz
  historia w samym pliku) — nie dotykałem tego raportu, bo jest poza zakresem 6.A5,
  ale warto wiedzieć, że praktyka „przelicz i wklej rzeczywiste wyjście" tam już raz
  zawiodła z tego samego powodu, przed którym ostrzega ten task (liczby z dokumentów
  bywają nieaktualne).
