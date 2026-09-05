# T-400 — etap 3b: scena zatrzymuje się na stacjach i przejeżdża całą linię

**Zmierzone na commicie:** `619b179` (scalenie #212) · **data:** 2026-09-04
**Scalone PR-y tego etapu:** [#210](https://github.com/matmaxalez/metro.brussels/pull/210)
(`stacje-w-scenie`, commit `cb7321e`) i
[#212](https://github.com/matmaxalez/metro.brussels/pull/212)
(`scena-przejazd-linii`, commit `32588a8`).

Ten raport powstał **po** scaleniu i to jest jego jedyny powód. Etap 3b był zrobiony
i zmierzony, ale dowód leżał wyłącznie w treści commitów i w opisach PR-ów — a w tym
projekcie to osobna klasa rozjazdu: praca wykonana, weryfikacja poza `reports/`.
Etapy 1, 2 i 3a mają swoje raporty (`T-400-first-run.md`, `T-012-godot-capture.md`,
wpis 3a w `docs/TASKS.md`); 3b nie miał.

**Skąd pochodzi każda liczba w tym raporcie.** Dwa źródła i nic więcej:

| oznaczenie | znaczenie |
|---|---|
| **[URUCHOMIONE]** | wynik **mojego** uruchomienia w tym środowisku, wklejony |
| **[PRZEPISANE]** | liczba z treści commitu albo z opisu #210 / #212, **nie** wykonana przeze mnie |

Środowisko pomiaru: .NET SDK **10.0.400**, Godot **4.7.2-stable mono**
(`/opt/metro-godot/4.7.2-stable`), Blender **5.2.1 LTS** (hash `9e2066aef7ef`),
zrzuty pod `xvfb-run` ze sterownikiem `opengl3` (llvmpipe).
Wariant geometrii: **`flat-preview`, nieprodukcyjny** — `data/track/L1_A.json` ma
`vertical.status = "not_modelled"`, cała oś leży na Z = 0 (jak w etapie 1).

Pliki wyjściowe: `build/t400/raport/`. **Nic z nich nie jest komitowane** (reguła 8).

---

## 1. Co powstało

Etap 3b to **dwa widoki tej samej linii**, w dwóch PR-ach, w tej kolejności:

### 1.1 #210 — `StationService`, tryb ręczny

Do #210 rdzeń przejeżdżał pakiet A z jedenastoma zatrzymaniami (`LineDrive`, T-401),
a scena Godota jechała 6,56 km bez jednego postoju: cykl drzwi istniał w rdzeniu od
T-312, tylko **scena go nie wołała**. `docs/TASKS.md` mówił o tym wprost jako o tym, co
w T-400 zostaje.

| plik | co robi | +/− |
|---|---|---|
| `src/Sim/Train/StationService.cs` | **nowy.** Rozpoznanie zatrzymania, cykl drzwi, blokada trakcji i rejestr wywołań dla składu prowadzonego **ręcznie**. Czysta klasa, zero Godota (reguła 9) | +232 |
| `tests/Sim.Tests/StationServiceTests.cs` | **nowy.** 13 testów tej klasy | +317 |
| `src/Game/FirstRun.cs` | `Filter` wołany w `StepOnce`; pętla szukająca najbliższej stacji usunięta z `UpdateHud` | +92 −7 |
| `src/Game/UI/Hud.cs` | czwarty wiersz HUD, startuje **ukryty** | +22 −5 |
| `src/Game/Scenes/FirstRun.tscn` | węzeł `Hud/Panel/Rows/Station` | +3 |
| `src/Game/DesignAssumptions.cs` | `StationStopWindowM = 5,0 m`, `PassengerExchangeSeconds = 8,0 s` — oba jako `design_assumption` z ograniczeniem od góry | +31 |
| `README.md` | stan warstwy silnika | +6 −2 |

Trzy rzeczy odróżniają tę klasę od autopilota `LineDrive`, i każda wynika z tego, że po
drugiej stronie siedzi człowiek:

1. **Okno zatrzymania jest dwustronne.** `LineDrive` wymaga tylko
   `chainage >= cel − okno`, bez ograniczenia z góry — dla autopilota, który staje
   z błędem 0,31 m, ten warunek nigdy nie wychodzi poza peron. Dla gracza wychodzi
   natychmiast: skład zatrzymany 200 m za stacją otworzyłby drzwi w tunelu.
   `StationService` wymaga `|chainage − cel| <= okno`.
2. **Minięta stacja jest minięta na zawsze.** `DriverCommand` ma nastawnik i hamulec,
   nie ma kierunku, więc reguła musi być monotoniczna — inaczej zależałaby od tego,
   co gracz zrobi potem.
3. **Granica okna należy do stacji** — zatrzymanie dokładnie na `cel + okno` jest
   wywołaniem, minięta jest od `cel + okno + ε`. Wybór jawny, obie strony przybite
   osobnymi testami.

Obsługa stacji jest **wyłącznie w trybie ręcznym** i to nie jest oszczędność: przebieg
skryptowy odtwarza `ScenarioDrive` z rdzenia, a jego telemetria jest porównywana
z rdzeniem co do bitu (`reports/T-400-first-run.md` §3.7, próg 0). Scenariusz T-400 nie
ma zatrzymań, więc nie ma tam czego blokować.

### 1.2 #212 — tryb `--line`, linia prowadzona rdzeniem

#210 skończył się zdaniem „nie przejechałem sceny ręcznie" — tryb ręczny czyta
klawiaturę przez `IsPhysicalKeyPressed`, a headless nie ma czego nacisnąć. #212 zamyka
tę dziurę z drugiej strony i bierze dosłownie zdanie przewodnie
`docs/01-architecture.md`: *„Linia jest symulacją, która działa bez gracza. Kabina jest
jednym z jej widoków."* W trybie `--line` skład prowadzi **rdzeń** (`LineDrive`),
a scena tylko patrzy — i **to jest pierwszy przebieg tego projektu, który da się
obejrzeć stojący przy peronie z otwartymi drzwiami**.

| plik | co robi | +/− |
|---|---|---|
| `src/Sim/Line/TrackAxis.cs` | **`CoversChord`** — czysty predykat „czy cięciwa ma na tej osi niezerową długość" | +29 |
| `src/Game/World/TrainView.cs` | bryła całkiem poza osią zostaje **ukryta**, nie postawiona gdziekolwiek | +12 −1 |
| `src/Game/World/SceneAxis.cs` | `CabPoint` przycina kilometraż **przed** oknem cięciwy | +9 −1 |
| `src/Game/RunPlan.cs` | `--line`, `--limit-kmh` (wymagane z `--line`), `--calls`, celowanie migawki w peron | +84 −2 |
| `src/Game/FirstRun.cs` | pętla trybu `--line`, kolejność warunków w `StepOnce`, wypis zatrzymań | +216 −10 |
| `src/Game/DesignAssumptions.cs` | `LineBrakeUsageFraction` | +15 |
| `src/Sim.Runner/Program.cs` | `line --calls PLIK.csv` — zatrzymania w postaci maszynowej | +23 −1 |
| `src/Sim/Train/LineDrive.cs` | dokumentacja jednostronnego okna (znalezisko z #210) | +18 |
| `tools/ci/assert_line_calls_match.py` | **nowa bramka**: zatrzymania sceny vs rdzenia, próg **zerowy** | +85 |
| `tools/tests/test_line_calls_gate.py` | **nowe.** Testy samej bramki | +97 |
| `tests/Game.Tests/RunPlanTests.cs` | argumenty trybu linii | +122 −4 |
| `tests/Game.Tests/SceneAxisTests.cs` | kamera przed początkiem osi | +36 |
| `tests/Sim.Tests/TrackAxisTests.cs` | `CoversChord` | +29 |
| `.github/workflows/godot-first-run.yml` | trzy nowe kroki: przejazd linią, kontrola negatywna bramki, migawka z peronu | +69 |

Razem etap 3b: **19 różnych plików** (21 zmian plikowych — `DesignAssumptions.cs`
i `FirstRun.cs` zmieniają się w obu PR-ach), **+1547 / −33**, dwa commity,
dwie gałęzie.

---

## 2. Zgodność sceny z rdzeniem — moje uruchomienie

Pytanie tej sekcji nie brzmi „czy oba przebiegi się nie wywróciły". Dwa przebiegi
kończące się kodem 0 mogą różnić się liczbą obsłużonych stacji, a tego z kodu wyjścia
nie widać. Porównywane są **zatrzymania**, kolumna po kolumnie, przy progu **zerowym**.

### 2.1 Rdzeń · `Sim.Runner` — **[URUCHOMIONE]**

```
$ dotnet run --project src/Sim.Runner --configuration Release -- line \
    --axis data/track/L1_A.json --limit-kmh 70 --exchange-s 8 --load AW2 \
    --brake-usage 1.0 --stop-window-m 5 --calls build/t400/raport/core-calls.csv

[LINIA] 11 zatrzymań -> build/t400/raport/core-calls.csv
[LINIA] L1_A: 11 zatrzymań, 6686.05 m, 733.14 s, postoje 181.59 s, kroków 89958, koniec=arrived
[LINIA] limit 70.00 km/h, wymiana 8.0 s, hamulec 100 % służbowego, okno stacji 5.0 m, obciążenie AW2 221940 kg
[STACJA] Beekkant: przyjazd 45.98 s na 509.43 m (błąd -0.303 m), jazda 45.98 s na 509.43 m, szczyt 70.00 km/h
[STACJA] Étangs Noirs|Zwarte Vijvers: przyjazd 131.48 s na 1451.60 m (błąd -0.300 m), jazda 69.00 s na 942.17 m, szczyt 70.00 km/h
[STACJA] Comte de Flandre|Graaf van Vlaanderen: przyjazd 199.54 s na 2054.48 m (błąd -0.301 m), jazda 51.55 s na 602.88 m, szczyt 70.00 km/h
[STACJA] Sainte-Catherine|Sint-Katelijne: przyjazd 270.85 s na 2720.45 m (błąd -0.304 m), jazda 54.80 s na 665.97 m, szczyt 70.00 km/h
[STACJA] De Brouckère: przyjazd 328.87 s na 3129.64 m (błąd -0.301 m), jazda 41.51 s na 409.19 m, szczyt 65.51 km/h
[STACJA] Gare Centrale|Centraal Station: przyjazd 396.88 s na 3731.55 m (błąd -0.301 m), jazda 51.50 s na 601.91 m, szczyt 70.00 km/h
[STACJA] Parc|Park: przyjazd 451.23 s na 4075.35 m (błąd -0.306 m), jazda 37.85 s na 343.81 m, szczyt 61.12 km/h
[STACJA] Arts-Loi|Kunst-Wet: przyjazd 513.25 s na 4560.65 m (błąd -0.304 m), jazda 45.51 s na 485.29 m, szczyt 70.00 km/h
[STACJA] Maelbeek|Maalbeek: przyjazd 580.73 s na 5152.11 m (błąd -0.305 m), jazda 50.98 s na 591.47 m, szczyt 70.00 km/h
[STACJA] Schuman: przyjazd 633.38 s na 5467.04 m (błąd -0.306 m), jazda 36.14 s na 314.93 m, szczyt 58.98 km/h
[STACJA] Merode: przyjazd 733.14 s na 6686.05 m (błąd -0.304 m), jazda 83.25 s na 1219.00 m, szczyt 70.00 km/h
[LINIA] największy błąd zatrzymania: 0.306 m
```

### 2.2 Scena · Godot headless — **[URUCHOMIONE]**

```
$ "$GODOT_BIN" --headless --path src/Game -- --line --limit-kmh=70 \
    --calls=".../build/t400/raport/scene-calls.csv"

[TUNEL] L1_A flat-preview: rezydentne 2/12 chunków w oknie [-206.0, 694.0] m, 2 siatek, wczytań 2 zwolnień 0, profil box_double 9.40×5.90 m, production_ready=False
[SKŁAD] brył=11 długość=94.000 m szerokość=2.700 m dach=3.600 m nad główką szyny
[OŚ] manifest 6686.739 m vs oś z rdzenia 6686.739 m, |Δ| = 1.335E-005 m
[OŚ] L1_A: 1349 punktów, 6686.739 m, 12 stacji
[LINIA] L1_A: 11 zatrzymań, 6686.05 m, 733.14 s, postoje 181.59 s, kroków 89958, koniec=arrived
[STACJA] Beekkant: przyjazd 45.98 s na 509.43 m (błąd -0.303 m), jazda 45.98 s na 509.43 m, szczyt 70.00 km/h
... (jedenaście wierszy identycznych z §2.1) ...
[STACJA] Merode: przyjazd 733.14 s na 6686.05 m (błąd -0.304 m), jazda 83.25 s na 1219.00 m, szczyt 70.00 km/h
[STACJE] 11 zatrzymań -> .../build/t400/raport/scene-calls.csv
```

### 2.3 Bramka · `assert_line_calls_match.py` — **[URUCHOMIONE]**

```
$ python3 tools/ci/assert_line_calls_match.py \
    build/t400/raport/core-calls.csv build/t400/raport/scene-calls.csv --expect-calls 11

[LINIA] chainage_m     max |Δ| = 0.000E+00
[LINIA] stopped_at_m   max |Δ| = 0.000E+00
[LINIA] stop_error_m   max |Δ| = 0.000E+00
[LINIA] arrival_s      max |Δ| = 0.000E+00
[LINIA] departure_s    max |Δ| = 0.000E+00
[LINIA] scena i rdzeń: 11 zatrzymań, wszystkie kolumny identyczne
exit=0
```

**Tabela max |Δ| po kolumnach zatrzymań — z mojego uruchomienia:**

| kolumna | max \|Δ\| scena ↔ rdzeń | próg bramki |
|---|---:|---:|
| `chainage_m` | 0,000E+00 | 0 |
| `stopped_at_m` | 0,000E+00 | 0 |
| `stop_error_m` | 0,000E+00 | 0 |
| `arrival_s` | 0,000E+00 | 0 |
| `departure_s` | 0,000E+00 | 0 |

Zgodność jest w rzeczywistości **mocniejsza od tego, co ta tabela pokazuje**, i to też
zmierzyłem: oba pliki są identyczne **co do bajtu**, nie tylko co do wartości kolumn.

```
$ diff build/t400/raport/core-calls.csv build/t400/raport/scene-calls.csv && echo IDENTYCZNE
IDENTYCZNE

$ sha256sum build/t400/raport/core-calls.csv build/t400/raport/scene-calls.csv
d1ed5c70852def2d83dc542fcdc524773087de715d138ac521f0efad1b2f0e5f  core-calls.csv
d1ed5c70852def2d83dc542fcdc524773087de715d138ac521f0efad1b2f0e5f  scene-calls.csv
```

Dwa pliki, jeden odcisk. Sam odcisk nie zastępuje bramki — bramka nazywa **którą**
kolumnę psuje rozjazd i o ile, a `sha256sum` mówi tylko „nie tak samo". Ale przy zgodnym
wyniku jest to dowód o klasę silniejszy: nie różni się ani formatowanie liczb, ani
kolejność wierszy.

### 2.4 Skąd biorą się liczby zbiorcze — **[URUCHOMIONE]**

Trzy liczby z nagłówka przejazdu dają się rozłożyć na czynniki, więc rozłożyłem, żeby
nie stały w raporcie jako wynik bez sprawdzenia:

```
liczba zatrzymań: 11
postój na zatrzymanie: min 16.50833 max 16.50833
suma postojów: 181.59167 s
11 x 16.5 = 181.50 s
błąd zatrzymania: min -0.3060 max -0.2999  max|.| 0.3060
```

- **11 zatrzymań** = 12 stacji pakietu A minus pierwsza, która jest punktem startowym,
  nie wywołaniem (`_next` startuje od 1, tak samo w `LineDrive` i w `StationService`).
- **Postój 16,50833 s**, nie 16,5 s. Cykl drzwi to 8,5 s faz stałych + 8,0 s wymiany
  pasażerów = 16,5 s, czyli 1980 kroków przy 1/120 s — a postój kończy się na kroku
  **1981**, bo warunek jest sprawdzany po kroku, nie przed nim. 1981/120 = 16,50833 s.
- **Postoje razem 181,59 s** = 11 × 16,50833, nie 11 × 16,5 = 181,5 s. Różnica 0,09 s
  to wyłącznie ta dyskretyzacja, jedenaście razy jeden krok.
- **Błąd zatrzymania jest systematycznie ujemny** (−0,2999 do −0,3060 m): autopilot staje
  konsekwentnie ok. 0,30 m **przed** celem, w jedenastu zatrzymaniach z jedenastu.
  To nie jest szum, tylko właściwość rozwiązania punktu hamowania — i właśnie dlatego
  okno rozpoznania stacji jest szersze od tego błędu o dwa rzędy wielkości.

### 2.5 Testy — **[URUCHOMIONE]**

```
$ dotnet test tests/Sim.Tests --configuration Release
Passed!  - Failed:     0, Passed:   345, Skipped:     0, Total:   345, Duration: 2 s - MetroBxl.Sim.Tests.dll (net10.0)

$ dotnet test tests/Game.Tests --configuration Release
Passed!  - Failed:     0, Passed:    84, Skipped:     0, Total:    84, Duration: 184 ms - MetroBxl.Game.Tests.dll (net10.0)

$ python3 tools/tests/test_all.py
  1462/1462 przeszło

$ dotnet build MetroBxl.sln --configuration Release
Build succeeded.
    0 Warning(s)
    0 Error(s)
```

Geometria, którą wczytuje scena, powstała **tu i teraz** z generatora, nie z kopii —
Blender 5.2.1, `tunnel_sweep.py` (12 chunków, 16 176 trójkątów LOD 0, szczelina na szwie
**0,000 mm** po wszystkich dziewięciu parach poziomów LOD) i `m7_shell.py`
(11 brył, re-import GLB `max_delta=0.0 m`).

---

## 3. Trzy usterki znalezione uruchomieniem, nie lekturą

Wszystkie trzy opisuje #212. Żadnej z nich nie widać w kodzie przy czytaniu — każda
wychodzi dopiero wtedy, gdy przejazd faktycznie startuje na pierwszej stacji.
Wspólny mianownik dwóch z nich jest jeden i warto go nazwać osobno: **przejazd linią
startuje na kilometrażu 0, a skład ma 94 m długości, więc jego ogon leży 94 m przed
początkiem osi.** Wszystkie wcześniejsze przebiegi tego projektu zaczynały się na
kilometrażu 94,0 m dokładnie po to, żeby cały skład stał na osi — `DriveScenario`
mówi o tym wprost w komentarzu. Przy przejeździe całą linią to obejście przestaje
istnieć, bo start jest tam, gdzie stoi pierwsza stacja.

### 3.1 `zerowa cięciwa` — trzynaście wyjątków na przebieg **[PRZEPISANE]**

**Mechanizm.** `TrackAxis.PointAt` **przycina** kilometraż do zakresu osi. Dwa różne
kilometraże leżące oba przed początkiem osi dają więc **ten sam punkt** — a z dwóch
identycznych punktów nie da się zbudować cięciwy ani ramki odniesienia. Widok składu
pytał o taką cięciwę dla każdej bryły, która leżała jeszcze przed osią; przy jedenastu
bryłach M7 wychodziło z tego **trzynaście wyjątków na przebieg** (liczba przepisana
z #212 — jej nie odtworzyłem, patrz §7).

**Naprawa.** Nowy `TrackAxis.CoversChord(fromM, toM)` odpowiada na to pytanie **czystą
funkcją**, w rdzeniu, nie w widoku — bo pytanie dotyczy **zasięgu osi**, a nie
rysowania, i dzięki temu daje się sprawdzić bez silnika (`tests/Sim.Tests`, +29).
`TrainView.PlaceAt` **ukrywa** bryłę, której oś nie pokrywa, zamiast stawiać ją
gdziekolwiek: `body.Node.Visible = covered`. Bryła wjeżdża na oś i pojawia się sama.
Kamera kabinowa dostała przycięcie kilometraża **przed** oknem cięciwy
(`SceneAxis.CabPoint`), bo oko maszynisty wypada na −1,8 m i całe okno [−2,8; −0,8]
leży przed początkiem osi.

Ukrycie, a nie podstawienie zastępczego położenia, jest tu jedyną odpowiedzią, która
nie zmyśla geometrii: osi w tym miejscu po prostu nie ma.

**Co zmierzyłem sam** — **[URUCHOMIONE]** — w pełnym przebiegu linią (89 958 kroków,
158 wierszy logu):

```
$ grep -c "zerowa cięciwa" build/t400/raport/scene-line.log
0
$ grep -c "^ERROR" build/t400/raport/scene-line.log
0
```

Zero wyjątków `zerowa cięciwa` i zero błędów. Zostało natomiast dziesięć ostrzeżeń
z tego samego korzenia, o których nie mówi żaden z dwóch PR-ów — §8.1.

### 3.2 Scena jechała 80 km/h **[URUCHOMIONE — liczba odtworzona]**

**Mechanizm.** To nie był błąd arytmetyczny, tylko **wzięcie jednej wielkości za drugą**,
i jest to dokładnie ten rodzaj pomyłki, przed którym broni cały rejestr statusów tego
projektu. Scena brała ograniczenie prędkości z `DriveScenario.PackageAFirstRun`, a ten
woła `Units.KmhToMps(model.DesignMaxSpeedKmh)` — czyli **prędkość konstrukcyjną
pojazdu M7**, nie prędkość **dopuszczalną na torze**. Pierwsza jest faktem o taborze
z rejestru; druga nie ma w tym repozytorium żadnego źródła (`speed_limits` w
`data/track/*.json` jest puste we wszystkich sześciu pakietach — odnotowane już
w `reports/T-400-first-run.md` §8.3 jako dziura w danych, którą widać dopiero wtedy,
gdy ktoś spróbuje pojechać).

**Naprawa.** `--limit-kmh` jest **wymagane** z `--line`. Nie ma wartości domyślnej,
bo każda byłaby zgadniętym faktem o brukselskim torze. Komunikat odmowy wypisuje to,
co o tej liczbie **wiadomo**, i podaje jej dwa znane ograniczenia:

```
$ "$GODOT_BIN" --headless --path src/Game -- --line --calls=...
ERROR: [ARGUMENT] --line wymaga --limit-kmh: prędkość dopuszczalna na torze NIE MA
źródła (R-006), a scenariusz T-400 podaje 80 km/h, czyli prędkość KONSTRUKCYJNĄ M7.
Znane ograniczenia: od dołu 58,68 km/h z rozkładu T-401, od góry 80 km/h z rejestru pojazdu
exit=9
```

**Skutek liczbowy pomyłki, odtworzony przeze mnie.** #212 podaje, że bez tego argumentu
przejazd trwał 724,94 s wobec 733,14 s rdzenia. Sprawdziłem to, podając rdzeniowi
80 km/h zamiast 70 km/h:

```
$ dotnet run --project src/Sim.Runner -c Release --no-build -- line \
    --axis data/track/L1_A.json --limit-kmh 80 --exchange-s 8 --load AW2 \
    --brake-usage 1.0 --stop-window-m 5
[LINIA] L1_A: 11 zatrzymań, 6686.05 m, 724.94 s, postoje 181.59 s, kroków 88974, koniec=arrived
```

**724,94 s odtworzyło się co do setnej sekundy** — i to jest ładna miara tej usterki:
różnica **8,20 s na 733 s (1,1 %)** przy dziesięcioprocentowej różnicy w prędkości
dopuszczalnej. Gdyby ktoś porównywał te przebiegi „z tolerancją kilku sekund", pomyłka
w wielkości fizycznej przeszłaby niezauważona. Bramka ma dlatego próg zerowy.

### 3.3 `--line --shot` wisiał do timeoutu 400 s i nie tworzył pliku **[URUCHOMIONE — naprawa potwierdzona]**

**Mechanizm.** Kolejność dwóch warunków w `StepOnce`. Sprawdzany był najpierw
`_scriptedMode`, a dopiero potem `_line`. Przy zrzucie z przejazdu linią **oba tryby są
włączone**, a `_scripted` jest wtedy nullem — pętla nie miała więc czym wykonać kroku
i przewijanie do zadanego kilometraża nigdy nie dobiegało końca. Proces nie padał;
**czekał**, i to jest najgorszy wariant, bo niczego nie wypisuje.

Reguła, którą z tego wyciągnięto i zapisano w kodzie: **warunek na sterownik
(kto prowadzi skład) musi iść przed warunkiem na sposób zapisu wyniku (telemetria czy
migawka).** Te dwie rzeczy są niezależne i traktowanie ich jako jednej listy wyklucza
kombinacje, które mają sens.

**Naprawa potwierdzona pomiarem** — **[URUCHOMIONE]**:

```
$ time xvfb-run -a "$GODOT_BIN" --rendering-driver opengl3 --resolution 1280x720 \
    --path src/Game -- --line --limit-kmh=70 \
    --shot=".../LINIA_outside_Beekkant2.png" --at-chainage=509.73 --view=outside

real    0m1.197s
[ZRZUT] .../LINIA_outside_Beekkant2.png 1280x720 err=Ok widok=Outside kroków=5818 chainage=509.4 m v=0.0 km/h
```

**1,20 s** wobec timeoutu 400 s, plik powstał, prędkość w chwili migawki zerowa.
Dwa niezależne przebiegi tego samego zrzutu dają ten sam obraz **co do bajtu**:

```
$ sha256sum LINIA_outside_Beekkant.png LINIA_outside_Beekkant2.png
4a222329a70035920ff1e423ac2f7d7289752af3721a24db88e417f9d2a1d240  LINIA_outside_Beekkant.png
4a222329a70035920ff1e423ac2f7d7289752af3721a24db88e417f9d2a1d240  LINIA_outside_Beekkant2.png
```

### 3.4 Celowanie migawki w peron — dwie próby, obie opisane w kodzie **[PRZEPISANE]**

Nie jest to czwarta usterka, ale należy do tej samej klasy: warunek, który wyglądał
poprawnie, dawał zły kadr.

| próba | co robiła | dlaczego zawiodła |
|---|---|---|
| tylko kilometraż | „stań, gdy chainage >= 509,73" | przekręcała **cały postój (16,5 s)** i łapała skład odjeżdżający, bo skład staje 0,30 m **przed** celem, czyli warunku nie spełnia w chwili zatrzymania |
| kilometraż + otwarte drzwi | „stań, gdy drzwi są otwarte" | przeskakiwała o **jedną stację dalej** (1451,6 m), bo nie wiązała otwartych drzwi z **tą** stacją |

Warunek mówi teraz trzy rzeczy naraz: **skład stoi, drzwi są otwarte, i to jest ta
stacja.** Bramka CI sprawdza oba końce tego warunku maszynowo — `v=0.0 km/h`
i `chainage=509.4 m` w logu migawki.

---

## 4. Co widać na zrzucie z peronu — mój opis

Plik: `build/t400/raport/LINIA_outside_Beekkant.png`, 1280 × 720, 126 677 bajtów,
kamera `outside` (26 m przed czołem, na sąsiednim torze, −4,20 m w bok, 2,60 m nad
główką szyny), krok 5818, chainage 509,4 m. **Obejrzałem go narzędziem `Read`**;
poniżej to, co na nim widzę, a nie to, co o nim pisze #212.

**Geometria.** Kadr wypełnia wnętrze tunelu `box_double` widziane wzdłuż osi: podłoga,
dwie ściany i strop zbiegają się do środka obrazu. Prawa górna część kadru ma wyraźną
przekątną krawędź biegnącą od prawego górnego narożnika w dół — to styk stropu ze
ścianą, i jest **asymetryczny**, tak jak być powinien, bo kamera nie stoi na osi tunelu,
tylko na sąsiednim torze.

**Skład.** W środku kadru stoi jasny blok — czoło M7 — z **widocznym ścięciem
lewego górnego narożnika** (ośmiobok obrysu pudła). Blok ma jednolite cieniowanie:
zmierzona luminancja czołowej ściany to **100–101** na 255, płasko, bez gradientu, co
jest poprawne dla płaskiej powierzchni oświetlonej z jednego kierunku. Za czołem widać
**człony uciekające w perspektywie** i **serię jasnych pionowych pasów** — przeguby
i wycięcia drzwi, w które wpada światło reflektora. Zmierzyłem ich rozstaw w wierszu
y = 352: kolejne pasy wypadają na x = 635, 641, 647, 650, 653, 656, 660, czyli odstępy
6, 6, 3, 3, 3, 4 px. **Malejący odstęp jest skrótem perspektywicznym** — dowód, że to
kolejne człony jednego składu w głąb kadru, a nie powtórzony wzór na jednej płaszczyźnie.
Gdyby skład był jedną sztywną bryłą, tych pasów by nie było wcale.

**Oświetlenie.** Obraz jest ciemny (mediana luminancji **78** na 255 w obszarze nad
HUD-em, maksimum **179**, ani jednego piksela ≥ 250). Wokół składu widać rozmytą
poświatę na ścianach, podłodze i stropie — reflektor czołowy o zasięgu 70 m świeci
**w głąb tunelu, przed skład**, więc rozświetla powierzchnie za nim, a nie kamerę.
To odróżnia ten kadr od przypadku, w którym kamera siedziałaby w geometrii (§5.2):
tam mediana wychodzi 212 i 5,6 % pikseli jest wyprane do 255.

**Skład stoi w świetle tunelu, nie w ścianie.** Wokół obrysu pudła widać ciemniejszą
przestrzeń tunelu po wszystkich stronach — nie ma miejsca, w którym pudło przechodziłoby
przez powierzchnię ściany albo stropu.

**HUD, cztery wiersze, czytelne wprost z obrazu:**

```
 0.0 km/h    a =  0.00 m/s²
chainage  509.4 m / 6686.7 m    Beekkant za 0 m
ciąg .......... 0.00   hamulec ########## 1.00   [shot]
DRZWI otwarte  jeszcze 14.0 s  błąd zatrzymania -0.30 m   obsłużone 1
```

Cztery liczby z tego HUD-u dają się sprawdzić przeciwko rdzeniowi i wszystkie się
zgadzają:

| co widzę na obrazie | z czym się zgadza |
|---|---|
| `0.0 km/h`, `a = 0.00 m/s²` | skład **stoi** — bramka CI wymaga w logu `v=0.0 km/h` |
| `ciąg 0.00` przy `hamulec 1.00` | **blokada trakcji działa**: nastawnik wyzerowany, choć hamulec jest pełny. To jest reguła z `docs/02-simulation.md`, widoczna na obrazie |
| `błąd zatrzymania -0.30 m` | rdzeń podaje −0,30326 m dla Beekkant (`core-calls.csv`, wiersz 1) |
| `DRZWI otwarte jeszcze 14.0 s` | krok 5818 = 48,48 s, przyjazd 45,975 s → **2,5 s** postoju za sobą, czyli dokładnie 0,5 s odryglowania + 2,0 s otwierania. Zostaje 16,5 − 2,5 = **14,0 s**. Faza `Open` zaczyna się co do kroku tam, gdzie ma |
| `obsłużone 1` | Beekkant to pierwsze wywołanie stacji przebiegu (pierwsza stacja pakietu jest punktem startowym, nie wywołaniem) |

**Czego na tym obrazie nie ma, a spodziewałbym się na peronie.** Nie ma peronu.
Podłoga tunelu biegnie pod składem bez przerwania: zmierzyłem kolumnę pikseli pod
składem (x = 640, y od 400 do 500) — luminancja przechodzi 60 → 69 → 85 → 116 → 128 →
102 → 89 → 83 → 80 → 77 → 75, czyli gładki gradient poświaty reflektora, **bez skoku
i bez krawędzi**. Krawędź peronu — a R-007 daje jej wysokość **1,03 m nad główką
szyny**, `source_backed` — dałaby na tej kolumnie wyraźną nieciągłość, i to na wysokości
porównywalnej z prześwitem pod pudłem (0,95 m). Nie ma jej, bo peronu w scenie nie ma
— §5.1.

Nie ma też **żadnego brandingu**: materiały to neutralne szarości, HUD jest gołym
tekstem, nie ma logo, mapy sieci, piktogramów ani wystroju STIB/MIVB
(`docs/03-legal.md`).

---

## 5. Czego nie ma — *stan 04.09.2026; §5.1–5.3 zamknięte, patrz tabela*

Trzy rzeczy poniżej były **znane i nazwane**, dwie z nich stały w kolejce fazy 6.
Żadna nie blokowała tego, co etap 3b miał dowieść, i żadna nie była przemilczana.

> **Ta sekcja jest przepisana, a nie dopisana obok — stan sprawdzony 05.09.2026 na
> `9f4ae98`.** Poprzednia wersja mówiła w czasie teraźniejszym „czego **nie ma**",
> a **wszystkie trzy pozycje zostały od tamtej pory domknięte**. Raport, który
> zostawia taką listę bez daty i bez stanu, wygląda jak opis dzisiejszego repozytorium
> i wysyła następną sesję do pracy leżącej w `main`; usterkę tej rodziny #240 wycięło
> z `docs/TASKS.md` i nie ma powodu, żeby przeżyła tutaj. Opisy niżej zostają w całości,
> bo to one tłumaczą, co dokładnie było naprawiane i po czym poznano, że jest źle.
>
> | poz. | stan na `9f4ae98` | czym |
> |---|---|---|
> | **5.1** peronu nie ma w scenie | **zamknięta** #223 | `src/Game/World/StationView.cs` — perony pakietu A z jednego GLB od `tools/blender/station_kit.py`, plus `src/Game/World/PlatformFit.cs` (pomiary bez silnika) i `tests/Game.Tests/PlatformFitTests.cs`. Zdanie „w `src/Game/World/` nie ma trzeciego widoku" jest więc dziś fałszywe: są cztery |
> | **5.2** kamera w geometrii, 6.B11 | **zamknięta** #226 + #236 | KIERUNEK: `src/Game/World/ChaseCameraAim.cs` i bramka `tools/ci/assert_no_godot_warnings.py`. GEOMETRIA: decyzja właściciela z 05.09.2026 — widok `chase` jest niedostępny, dopóki cały skład nie wjedzie na oś, a `--shot --view=chase` w tym paśmie odmawia kodem 13 |
> | **5.3** `TrainView.PlaceAt` bez testu, 6.B12 | **zamknięta** #217 | decyzja o widoczności wyszła z silnika do funkcji czystej `TrainLayout`, granicą jest `ITrainBody`; `dotnet test tests/Game.Tests` → 97/97 |
>
> **Poprawka liczby, i to jest część tego samego znaleziska.** §5.2 niżej podaje
> „kamera obserwacyjna siedzi wewnątrz geometrii przez pierwsze **~106 m**" i wyprowadza
> to z rachunku 94 + 12. **Ta liczba jest nieprawdziwa** i rozstrzygnął to pomiar
> z 05.09.2026 zapisany w `docs/TASKS.md` (wiersz 6.B11): 106,0 m to kilometraż, od
> którego kamera odzyskuje pełne 12,0 m odstępu, a **nie** koniec pasma w geometrii.
> W skorupie kamera siedzi przez **0..94,0 m** (długość M7, `data/vehicle/m7-spec.json`,
> status `spec`), a kierunek jest nieokreślony przez **0..47,0 m**. Ułamek pikseli
> jaśniejszych niż 0,80 w górnych 60 % kadru, `--line --limit-kmh=70`: 20 m → 0,1 %,
> 48 m → 56,4 %, 50 m → 38,3 %, 90 m → 0,0 %, 96 m → 42,0 %, 110 m → 0,0 %,
> 2000 m → 0,0 %. Rachunek 94 + 12 był rachunkiem na odstępie kamery, a przedstawiono
> go jako pomiar pasma — i tak właśnie liczba stojąca w prozie dryfuje w ciszy.

### 5.1 Na stacji nie ma peronu w scenie

Zrzut z §4 nazywa się „z peronu Beekkant" i to jest nazwa **kilometraża**, nie
geometrii. Skład stoi w miejscu, w którym ma stać, drzwi przechodzą cykl, HUD podaje
błąd zatrzymania — a **za drzwiami jest goła rura tunelu**.

Nie jest tak, że tej geometrii nie ma w repozytorium. **T-212 jest zrobione i scalone**
(#137, `reports/T-212-station.md`): `tools/track/station_components.py` liczy schody,
windę, antresolę, korytarz i portal, a `tools/blender/station_kit.py` zamienia je na
siatki. Peron ma **95,0 m** (decyzja właściciela z 04.09.2026).

Czego brakuje, to **wstawienia tego do przejazdu**. Potwierdziłem to wprost:

```
$ grep -rniE "peron|platform|station_kit|Station\.glb" src/Game --include=*.cs --include=*.tscn
(trafienia wyłącznie w komentarzach i w opisach założeń — ani jednego wczytania zasobu)
```

Scena wczytuje dwa rodzaje geometrii i tylko dwa: chunki tunelu (`TunnelView`)
i skorupę M7 (`TrainView`). W `src/Game/World/` nie ma trzeciego widoku.

### 5.2 Kamera obserwacyjna siedzi wewnątrz geometrii przez pierwsze ~106 m

Pozycja **6.B11** kolejki fazy 6. To jest ta sama przyczyna co usterka §3.1, tylko po
stronie kamery, i **jedyna z trzech, która nie została naprawiona w #212**: kamera
`chase` stoi 12 m za ogonem, ogon jest 94 m przed początkiem osi, więc kilometraż
kamery przycina się do zera i kamera ląduje **w powłoce tunelu**. 94 + 12 = 106 m
przejazdu, przez które kadr jest bezużyteczny.

**Zmierzyłem to sam** — **[URUCHOMIONE]** — dwoma zrzutami tej samej kamery, jeden
w strefie usterki, drugi poza nią:

```
$ ... --line --limit-kmh=70 --shot=.../LINIA_chase_20m.png   --at-chainage=20   --view=chase
[ZRZUT] LINIA_chase_20m.png   1280x720 err=Ok widok=Chase kroków=  750 chainage=  20.0 m v=23.0 km/h
$ ... --line --limit-kmh=70 --shot=.../LINIA_chase_2000m.png --at-chainage=2000 --view=chase
[ZRZUT] LINIA_chase_2000m.png 1280x720 err=Ok widok=Chase kroków=22738 chainage=2000.0 m v=39.4 km/h
```

Statystyka luminancji obszaru nad HUD-em (co czwarty piksel, y < 500):

| zrzut | min | mediana | max | pikseli ≥ 250 |
|---|---:|---:|---:|---:|
| `LINIA_chase_20m.png` | 85 | **212** | 255 | **5,6 %** |
| `LINIA_chase_2000m.png` | 50 | 72 | 128 | 0,0 % |
| `LINIA_outside_Beekkant.png` (§4, dla porównania) | 47 | 78 | 179 | 0,0 % |

**Obejrzałem `LINIA_chase_20m.png` narzędziem `Read`.** Widzę na nim jasnoszarą,
niemal jednolitą płaszczyznę wypełniającą cały kadr, z **wypraną do bieli plamą**
w środku, mniej więcej okrągłą, o średnicy ok. 200 px — to reflektor składu świecący
w powierzchnię, która jest **kilka centymetrów przed obiektywem**. Nie ma na tym obrazie
ani składu, ani przekroju tunelu, ani żadnej krawędzi geometrii: kamera jest
**po wewnętrznej stronie** powłoki i widzi wyłącznie jej wnętrze z bliska. Jedyne, co
się czyta, to HUD: `23.0 km/h`, `a = 1.02 m/s²`, `chainage 20.0 m / 6686.7 m`,
`Beekkant za 490 m`, `ciąg ########## 1.00`, `obsłużone 0`. Ten sam kadr z kilometraża
2000 m jest poprawny — ciemny, z widocznym tunelem i składem.

Naprawa wymaga **decyzji**, której nie ma w dokumentach: czy kamera ma być przyciągana
do minimalnego kilometraża (jak `SceneAxis.CabPoint`, wzorzec jest już w repozytorium),
czy ukrywana do chwili, gdy cały skład wjedzie na oś. Oba warianty siedzą w warstwie
widoku i żaden nie dotyka danych o sieci — dlatego 6.B11 jest w kolejce jako zadanie,
a nie jako pytanie do właściciela.

### 5.3 `TrainView.PlaceAt` nie ma ani jednego testu

Pozycja **6.B12** kolejki. Mutacja `body.Node.Visible = covered` → `= true`
**przeżyła** przegląd przy #212 — jedyna z ośmiu, patrz §6.2. Powód jest strukturalny,
nie z niedopatrzenia: `PlaceAt` wymaga **wczytanego GLB pod silnikiem**, a `dotnet test`
silnikiem nie jest.

Autor #212 nie udawał, że tę linię przybił. Zmierzył jej wpływ zrzutami — z kamery
kabinowej i zewnętrznej różnica **0 bajtów na 3 687 120**, z kamery obserwacyjnej
**64 761 bajtów (1,76 %)** — i napisał wprost, że obie klatki z tej kamery są białą
plamą, czyli że nie umiał zbudować kadru, w którym brak tej linii byłby widoczny jako
różnica **między klatką poprawną i niepoprawną**. To jest uczciwy wynik: „wpływa na
render, ale nie mam kadru, który to rozstrzyga", a nie „przetestowane".

Warto zauważyć, dlaczego te dwie pozycje kolejki są sprzężone: **6.B11 jest przyczyną,
dla której 6.B12 nie dało się przybić zrzutem.** Kadr, w którym widoczność brył ma
znaczenie, to właśnie kadr z kamery obserwacyjnej na początku przejazdu — a ta kamera
jest tam w geometrii. Naprawa 6.B11 najprawdopodobniej odblokowuje mierzalną kontrolę
dla 6.B12; lekarstwo z opisu 6.B12 (wyciągnięcie decyzji o widoczności do funkcji
czystej, tak jak `StreamingPlan` w #174) jest jednak niezależne i mocniejsze.

### 5.4 Reszta, poza kolejką

Stan każdego wiersza sprawdzony ponownie 05.09.2026 na `9f4ae98` — poprzednia wersja
tej tabeli miała tylko dwie kolumny i czytała się jako lista braków dzisiejszych,
a trzy z pięciu pozycji już nie są brakami:

| brakuje | dlaczego (04.09.2026) | stan 05.09.2026 |
|---|---|---|
| **wiele składów na linii** | T-320 (`LineCore`, dyspozytor); tryb `--line` prowadzi **jeden** skład | `src/Sim/Line/LineCore.cs` istnieje wraz z `RouteDispatcher` i `LineCoreTests`; w **scenie** tryb `--line` nadal prowadzi jeden skład, więc brak zwęził się do warstwy widoku |
| **przejęcie składu w ruchu** | nie ma czego przejmować, dopóki nie ma drugiego składu | otwarte |
| **sygnalizacja w kabinie** | T-313 jest w rdzeniu, ale HUD nie pokazuje ani prędkości dopuszczalnej, ani autorytetu jazdy | **zamknięte** #215 — `src/Game/UI/Hud.cs` ma dziś wiersz „prędkość dopuszczalna, autorytet i powód jego końca" |
| **przejazd ręczny obejrzany** | tryb ręczny czyta klawiaturę przez `IsPhysicalKeyPressed`; headless nie ma czego nacisnąć | **zamknięte** #239 — `--input-log` zapisuje wciśnięcia **po numerze kroku** (`src/Sim/Train/InputLog.cs`), `--replay` je odtwarza, więc przejazd ręczny da się dziś uruchomić headless i porównać |
| **drugi pakiet w scenie** | przy `vertical.status = not_modelled` cała sieć leży na Z = 0, więc pakiety A i E przenikają się w planie w rejonie Arts-Loi (`reports/network-chainage.md`) | otwarte |

---

## 6. Kontrole negatywne

**Poniższe tabele są w całości PRZEPISANE** z opisów #210 i #212. Nie wykonałem tych
mutacji — wprowadzenie ich wymagałoby zmiany plików w `src/` i `tools/`, a to zadanie
ma zakres jednego pliku w `reports/`. Podaję je, bo bez nich raport mówiłby „testy
przechodzą" i nie mówiłby, czy te testy cokolwiek kontrolują.

Jedną kontrolę negatywną **wykonałem sam** i jest wyraźnie oddzielona — §6.3.

### 6.1 #210 — sześć mutacji, sześć zabitych **[PRZEPISANE]**

| mutacja | skutek |
|---|---|
| okno jednostronne jak w `LineDrive` | `FAIL` ×2 |
| minięcie nigdy nie zachodzi | `FAIL` ×3 |
| blokada trakcji usunięta | `FAIL` ×5 |
| pierwsza stacja liczy się jako wywołanie | `FAIL` ×10 |
| brak czasu odjazdu | `FAIL` ×1 |
| drzwi otwierają się przy 1,0 m/s | `FAIL` ×1 |

Ostatnia jest w tej tabeli najważniejsza, bo **przeżyła pierwszą wersję zestawu** —
i #210 nazywa to znaleziskiem, nie ozdobą. Żaden test nie podawał składu **w ruchu**
w oknie stacji, więc zestaw nie sprawdzał wcale reguły, która jest treścią
`StationStop`: *„zatrzymanie liczy się od PRĘDKOŚCI ZERO, nie od kilometrażu peronu"*.
Dopisany test celuje w 1,0 m/s, w `double.Epsilon` i w zero. To jest wzorcowy przypadek
tego, po co kontrola negatywna istnieje: zestaw był zielony i **nie kontrolował
swojej głównej reguły**.

### 6.2 #212 — osiem mutacji, siedem zabitych **[PRZEPISANE]**

| mutacja | skutek |
|---|---|
| `CoversChord` zawsze prawda | `FAIL ...CoversChordSaysWhenAChordHasNoLength...` |
| przycięcie kamery usunięte | `FAIL ...CabPointBeforeTheAxisStartUsesTheFirstChord...` |
| limit przestaje być wymagany | `FAIL` ×3 |
| zrzut wyłącza tryb linii (stara postać) | `FAIL ...LineModeRefusesTelemetryButAcceptsAShot` |
| próg bramki rozluźniony do metra | `FAIL ...catches_a_millimetre_in_any_numeric_column` |
| zero zatrzymań przechodzi | `FAIL ...refuses_a_run_with_no_calls_at_all` |
| liczba zatrzymań nie jest sprawdzana | `FAIL ...checks_the_expected_count_of_calls` |
| `Visible = covered` → `= true` | **PRZEŻYŁA** — §5.3 |

### 6.3 Kontrola negatywna bramki — **wykonana przeze mnie [URUCHOMIONE]**

Tę jedną wykonałem, bo nie wymaga zmiany ani jednego pliku źródłowego: psuje
**dane wyjściowe** w `build/`, tak samo jak krok `Negative control of the line
comparison` w workflow. Bramka, która mówi „ok" także wtedy, gdy nic nie sprawdza,
jest bezużyteczna — więc zepsułem jedną liczbę o **milimetr**:

```
$ python3 - (kopia scene-calls.csv z jedną zmienioną liczbą)
psuję wiersz 1, kolumna 3 (stopped_at_m): 509.4267375359308 -> 509.42773753593076

$ python3 tools/ci/assert_line_calls_match.py \
    build/t400/raport/core-calls.csv build/t400/raport/scene-calls-bad.csv --expect-calls 11
[LINIA] chainage_m     max |Δ| = 0.000E+00
[LINIA] stopped_at_m   max |Δ| = 1.000E-03
[LINIA] stop_error_m   max |Δ| = 0.000E+00
[LINIA] arrival_s      max |Δ| = 0.000E+00
[LINIA] departure_s    max |Δ| = 0.000E+00
BŁĄD: stopped_at_m: max |Δ| = 1.000E-03, a próg jest ZEROWY
exit=1
```

**Wykryte, z nazwaniem kolumny i wartości.** Bramka nie tylko odrzuca — mówi
**która** z pięciu kolumn się rozjechała i o ile. Milimetr na 509 m to 2·10⁻⁶
względnie; rozjazd „rzędu centymetrów", który dałaby prawdziwa różnica w prowadzeniu
składu, jest o cztery rzędy wielkości większy.

---

## 7. Rozbieżności z liczbami z PR-ów

Zgodnie z regułą, którą ten projekt stosuje do własnych dokumentów: liczba, która się
nie odtworzyła, **jest wypisana**, a nie po cichu podmieniona.

| liczba | źródło | u mnie | ocena |
|---|---|---|---|
| 11 zatrzymań, 6686,05 m, 733,14 s, postoje 181,59 s, 89 958 kroków | #212 | **identycznie** | odtworzone |
| wszystkie pięć kolumn max \|Δ\| = 0,000E+00 | #212 | **identycznie** (i dodatkowo zgodność co do bajtu) | odtworzone |
| błąd zatrzymania Beekkant −0,3033 m | #212 | **−0,30326 m** | odtworzone |
| przejazd przy 80 km/h = 724,94 s | #212 | **724,94 s** | odtworzone |
| migawka: `v=0.0 km/h`, `chainage=509.4 m`, 5818 kroków | #212 | **identycznie** | odtworzone |
| `dotnet test tests/Sim.Tests` → 345 | #212 | **345** | odtworzone |
| `dotnet test tests/Game.Tests` → 84 | #212 | **84** | odtworzone |
| **`tools/tests/test_all.py` → 1439/1439** | #212 | **1462/1462** | **NIE ODTWORZONE** ↓ |
| **`tools/tests/test_all.py` → 1432/1432** | opis #210 | **1462/1462** | **NIE ODTWORZONE** ↓ |
| **`tools/tests/test_all.py` → 1426/1426** | commit `cb7321e` (#210) | **1462/1462** | **NIE ODTWORZONE** ↓ |
| **`dotnet test tests/Sim.Tests` → 344** | #210 | **345** | **NIE ODTWORZONE** ↓ |
| **13 wyjątków `zerowa cięciwa`** | #212 | **0** (po naprawie) | **NIE ODTWORZONE Z ZAŁOŻENIA** ↓ |

**Liczba testów narzędzi.** Trzy różne liczby w dwóch dokumentach i czwarta u mnie.
Dwie z nich są **wzajemnie sprzeczne w obrębie #210**: commit mówi 1426, a opis PR-a
1432 — jeden z tych dwóch zapisów jest nieprawdziwy i nie wiem który, bo oba pochodzą
z tego samego zadania. Mój wynik 1462 różni się od wszystkich trzech i to **nie jest
regresja**: liczba testów narzędzi rośnie z każdym scaleniem, a między #210 i moim
pomiarem weszły do `main` co najmniej #137 (T-212, +22 testy komponentów stacji),
#211 i #213. Wzrost 1439 → 1462 to +23. **Żaden test nie pada** — 1462/1462.
Nie zmieniam tych liczb w PR-ach; odnotowuję, że **liczba testów zliczana bez podania
commitu jest w tym repozytorium liczbą nietrwałą** i nie nadaje się do porównywania
między raportami.

**344 → 345 w `Sim.Tests`.** Odtwarza się dokładnie tak, jak powinno: #210 dodał
13 testów `StationServiceTests` i zamknął się na 344, #212 dodał jeden test
`CoversChord` i zamknął się na 345. Mierzę 345, czyli stan po obu — zgodnie
z commitem, na którym mierzę.

**Trzynaście wyjątków `zerowa cięciwa`.** Tej liczby **nie da się u mnie odtworzyć
z założenia** i mówię to wprost, żeby nie wyglądała na potwierdzoną: jest to pomiar
stanu **przed** naprawą, a naprawa jest scalona. Odtworzenie wymagałoby wycofania
`CoversChord` i przycięcia w `SceneAxis.CabPoint`, czyli zmiany plików w `src/`, której
to zadanie nie obejmuje. Co zmierzyłem: **zero** takich wyjątków i **zero** wierszy
`ERROR` w pełnym przebiegu linią. Sama liczba 13 pozostaje **[PRZEPISANA]**.

---

## 8. Zauważone przy okazji, nie tknięte — *cztery z pięciu zamknięte, patrz tabela*

Ten raport nie zmieniał ani jednego pliku poza sobą. Poniższe pięć rzeczy zauważyłem
przy pomiarze 04.09.2026 i **żadnej wtedy nie poprawiłem** — na tych plikach pracowały
wówczas inne gałęzie.

> **Ta sekcja jest przepisana, a nie dopisana obok — stan sprawdzony 05.09.2026 na
> `9f4ae98`.** Gałęzie, o których mówi zdanie wyżej, scaliły się i **cztery z pięciu
> pozycji przestały być prawdziwe**. Każda z nich jest sformułowana w czasie
> teraźniejszym („wypisuje", „nie jest włączone", „są nieaktualne"), więc bez tej
> tabeli sekcja czyta się jak lista otwartych usterek dzisiejszego drzewa:
>
> | poz. | stan | czym, sprawdzone lekturą |
> |---|---|---|
> | **8.1** dziesięć ostrzeżeń `colinear` | **zamknięta** #226 | `src/Game/World/ChaseCameraAim.cs` podstawia kierunek osi tam, gdzie kamera i cel wypadają w jednym punkcie; liczba ostrzeżeń na przebieg `--line` zeszła do zera i pilnuje tego bramka `tools/ci/assert_no_godot_warnings.py`. Kryterium „naprawa 6.B11 powinna zejść z dziesięciu ostrzeżeń do zera", postawione w tym punkcie, zostało użyte dokładnie jako kryterium |
> | **8.2** nagłówek mówi 80,0 km/h w `--line` | **zamknięta** #220 | składanie wiersza `[PRZEJAZD]` wyszło do `src/Game/RunHeader.cs`, czyli do pliku bez Godota; `RunHeader.SpeedLimitMps` bierze limit z `LineCore`/`LineDrive`, a dla `lineMode` bez prowadzenia z rdzenia **rzuca wyjątkiem** zamiast wpisać 80 km/h ze scenariusza. `FirstRun.SpeedLimitMps` jest dziś jedną linią delegującą tam |
> | **8.3** osierocony `<summary>` | **zamknięta** #222 i #224 | `src/Sim/Line/TrackAxis.cs`: `CoversChord` ma jeden blok, `MaxDeviationFromSourceM` ma swój własny plus `<returns>`. Zdanie „generowanie dokumentacji XML nie jest włączone" jest **osobno nieprawdziwe**: `src/Sim/Sim.csproj` i `src/Game/MetroBxl.Game.csproj` mają dziś `<GenerateDocumentationFile>true</GenerateDocumentationFile>`, a CS1570–CS1574 i CS1591 są w `WarningsAsErrors`. Dokumentacji pilnuje więc kompilator, nie skan tekstowy — i to jest dokładnie ten drugi wniosek, który ten punkt podpowiadał |
> | **8.4** dwie liczby o peronie | **zamknięta** #222 | komentarz przy `DesignAssumptions.StationStopWindowM` podaje dziś peron 95,0 m z odsyłaczem do `tools/track/station_components.py: DESIGN_PLATFORM_LENGTH_M`, dolne ograniczenie 94,0 m nazwane wprost długością składu M7, a udział liczony do **połowy peronu 47,5 m**: „5,0 m to 10,5 % tej połowy — jedna podstawa, ta sama w obu zdaniach". Obie usterki wskazane w punkcie 8.4 zostały poprawione tak, jak je opisał |
> | **8.5** `doctor.sh` nie uruchomiony | **zostaje jako zapis** | to nie jest usterka repozytorium, tylko oświadczenie o przebiegu tamtej sesji, i przepisywać go nie ma czego |

### 8.1 Dziesięć ostrzeżeń `Target and up vectors are colinear` na przebieg linią

Nowe, nie ma tego w żadnym z dwóch PR-ów. W pełnym przebiegu `--line` **[URUCHOMIONE]**:

```
$ grep -c "colinear" build/t400/raport/scene-line.log
10
$ grep -c "_Ready"   build/t400/raport/scene-line.log     # miejsce wywołania
1
$ grep -c "_Process" build/t400/raport/scene-line.log
9
```

Wszystkie dziesięć pochodzą z jednego miejsca: `FirstRun.PlaceEverything()`, wiersz 664,
czyli `_chase.LookAtFromPosition(position, middle, Vector3.Up)` — **kamera
obserwacyjna**. Warunek „cel i wektor góry są współliniowe" znaczy, że pozycja kamery
i punkt, na który patrzy, mają **tę samą rzutową pozycję w planie** i różnią się tylko
wysokością. Zachodzi to dokładnie wtedy, gdy `behind` przycina się do zera **i** punkt
środka składu też przycina się do zera: kamera patrzy wówczas pionowo w dół albo w górę.

Jest to więc **ten sam korzeń co 6.B11** (§5.2), zapisany w logu, nie tylko widoczny
na obrazie — dziesięć ostrzeżeń to dokładnie pierwsze klatki przejazdu, zanim skład
wjedzie na oś. Dopisuję to tutaj, bo **6.B11 opisuje objaw wizualny** („klatka wychodzi
białą plamą"), a ten pomiar daje temu samemu zjawisku **kontrolę maszynową**: naprawa
6.B11 powinna zejść z dziesięciu ostrzeżeń do zera, i to jest kryterium, które da się
sprawdzić bez oglądania obrazka. Nie dopisuję tego do `docs/TASKS.md` — to plik
wspólny i zmienia go równolegle inne zadanie.

### 8.2 Nagłówek przejazdu wypisuje limit **80,0 km/h** także w trybie `--line`

**[URUCHOMIONE]**, pierwsze wiersze mojego przebiegu z `--limit-kmh=70`:

```
[PRZEJAZD] tryb=line widok=Cab scenariusz=package-a-first-run krok=1/120 s masa=221940 kg limit=80.0 km/h
...
[STACJA] Beekkant: ... szczyt 70.00 km/h
```

Przejazd **jedzie 70 km/h** — wszystkie jedenaście wierszy `[STACJA]` podają szczyt
≤ 70,00 km/h, a czas 733,14 s zgadza się co do setnej z rdzeniem liczonym przy 70 km/h.
Sam nagłówek jest jednak nieprawdziwy: `FirstRun.LogHeader` wypisuje
`Units.MpsToKmh(_scenario.SpeedLimitMps)`, czyli limit **scenariusza T-400**, a w trybie
`--line` prowadzenie nie bierze limitu ze scenariusza, tylko z `--limit-kmh`.

To jest **ten sam rodzaj pomyłki, który #212 naprawiał jako usterkę nr 2** — prędkość
konstrukcyjna pojazdu podana tam, gdzie chodzi o prędkość dopuszczalną na torze —
tylko że tym razem nie w prowadzeniu, a w wypisie. Prowadzenia to nie dotyczy, więc nie
jest to usterka symulacji; jest to **jedyna liczba w logu, która kłamie**, i to dokładnie
w tym miejscu, w które ktoś zajrzy, gdy będzie sprawdzał, z jaką prędkością jechał
przebieg. Naprawa jest jednowierszowa, ale leży w `src/Game/FirstRun.cs`, którego
to zadanie nie dotyka.

### 8.3 `CoversChord` odziedziczył cudzy komentarz XML, a `MaxDeviationFromSourceM` swój stracił

`src/Sim/Line/TrackAxis.cs`, wiersze 185–217. Nowy predykat wszedł **między** komentarz
`<summary>` należący do `MaxDeviationFromSourceM` i samą tę metodę:

```csharp
    /// <summary>
    /// Największa odległość punktu zagęszczonej osi od łamanej źródłowej — miara tego,
    /// ile interpolacja dołożyła do przebiegu STIB. Odpowiednik
    /// <c>tools/blender/sweep.py: max_deviation</c>; na pakiecie A wychodzi 0,1064 m.
    /// </summary>
    /// <summary>
    /// Czy cięciwa od <paramref name="fromM"/> do <paramref name="toM"/> ma na tej osi
    /// niezerową długość.
    ...
    /// </summary>
    public bool CoversChord(double fromM, double toM)
    ...
    public double MaxDeviationFromSourceM()
```

Skutek: `CoversChord` ma **dwa** bloki `<summary>` (pierwszy opisuje coś innego),
a `MaxDeviationFromSourceM` nie ma **żadnego**. Kompilacja tego nie zauważa —
`dotnet build MetroBxl.sln` daje 0 ostrzeżeń, bo generowanie dokumentacji XML nie jest
włączone. Wyłącznie kosmetyka, ale kosmetyka wprowadzająca w błąd czytającego, i po tym
poznać, że blok wklejono, a nie napisano na miejscu.

### 8.4 Dwie liczby o peronie w `DesignAssumptions.cs` są nieaktualne albo błędne

`src/Game/DesignAssumptions.cs`, wiersze 80–82, uzasadnienie okna zatrzymania:

> *„peron w generatorze ma 94,0 m (R-007 daje kontrolę górną 109,1 m), więc okno
> szersze niż połowa peronu pozwalałoby otworzyć drzwi poza krawędzią.
> 5,0 m to 5,3 % połowy peronu."*

Dwie rzeczy:

1. **94,0 m to już nieprawda.** `reports/T-212-station.md` zapisuje decyzję właściciela
   z 04.09.2026: peron ma **95,0 m** (zmiana z 110 m). Ta sama data co #210. Wartość
   94,0 m jest długością **składu M7**, nie peronu — i to jest zbieżność, która ułatwia
   pomyłkę, bo obie liczby są prawdziwe, tylko o czym innym.
2. **5,3 % jest źle policzone.** 5,0 m / 94,0 m = 5,3 % — ale to jest udział
   w **całym** peronie, nie w jego połowie. Wobec połowy peronu (47,0 m) wychodzi
   **10,6 %**; wobec połowy peronu 95,0 m z T-212 — **10,5 %**. Zdanie miesza więc
   dwie podstawy w jednym rachunku.

Wniosek o samym oknie **się nie zmienia**: 5,0 m jest bezpiecznie mniejsze od połowy
peronu przy każdej z tych liczb, i o rząd wielkości większe od mierzonego błędu
zatrzymania 0,31 m. Zmienia się tylko to, czy uzasadnienie w kodzie mówi prawdę.

### 8.5 `doctor.sh` nie został przeze mnie uruchomiony

CLAUDE.md §2 każe zaczynać od `bash doctor.sh`. W tym środowisku nie mogłem tego zrobić
i mówię to wprost, zamiast pominąć milczeniem: sesja pracuje w izolowanym worktree,
a mechanizm izolacji odmawia uruchomienia skryptu, który sam wywołuje `git`
(*„refusing to run it — a worktree-isolated agent's git operations must target its own
worktree"*). Zamiast tego wykonałem **wszystkie** kontrole, które `doctor.sh` opakowuje,
osobno i z wklejonym wyjściem: `dotnet build MetroBxl.sln`, `dotnet test tests/Sim.Tests`
(345/345), `dotnet test tests/Game.Tests` (84/84) i `python3 tools/tests/test_all.py`
(1462/1462) — §2.5. Trzy narzędzia, których `doctor.sh` szuka, są obecne i wszystkie
trzy zostały użyte w tym raporcie: .NET 10.0.400, Godot 4.7.2 mono i Blender 5.2.1.

---

## 9. Zakres tego raportu

**Co ten raport robi:** zapisuje w `reports/` wynik etapu 3b, który do tej pory istniał
tylko w treści commitów `cb7321e` i `32588a8` oraz w opisach #210 i #212.

**Czego nie robi:**

- **nie zmienia ani jednego pliku poza sobą.** Nie dotyka `src/`, `tests/`, `tools/`,
  `docs/`, `data/`, `README.md` ani `.github/` — także tam, gdzie §8 opisuje rzeczy
  warte poprawienia. Na tych plikach pracują teraz inne gałęzie;
- **nie odhacza T-400 w `docs/TASKS.md`.** Wpis o etapie 3b jest już tam przepisany
  (#213); odhaczenie całego zadania należy do właściciela i wymaga etapów, których nie
  ma (T-320, T-212 w scenie);
- **nie dopisuje pozycji do kolejki fazy 6.** Znalezisko z §8.1 jest kontrolą maszynową
  dla istniejącej pozycji 6.B11, nie nową pozycją; §8.2, §8.3 i §8.4 są odnotowane tutaj
  i nikt ich sobie nie przypisał;
- **nie odtwarza stanu przed naprawami.** Trzy usterki z §3 są naprawione i scalone;
  odtworzenie ich objawów wymagałoby wycofania zmian w `src/`. Gdzie się dało, zmierzyłem
  **skutek liczbowy** usterki bez cofania kodu (§3.2, 724,94 s) albo **potwierdzenie
  naprawy** (§3.1, §3.3).
