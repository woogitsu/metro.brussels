# T-401 · Przejazd linii z zatrzymaniem na każdej stacji

Stan: **2026-09-01**. Wyjście: `src/Sim/Train/LineRun.cs`, `src/Sim/Train/LineRunSettings.cs`,
`src/Sim.Runner` polecenie `line`, `tests/Sim.Tests/LineRunTests.cs`.
Domyka fragment „zostaje" z T-400 i przygotowuje T-320. Zależy od T-310, T-311, T-312, T-113.

---

## 1. Co zrobiłem

Przejazd całej osi, na której skład **zatrzymuje się na każdej stacji**: rozpęd, punkt
hamowania liczony solverem z T-311 i pełny cykl drzwi z T-312. Punkt hamowania nie jest
tu parametrem — maszynista jest zamknięty w pętli sprzężenia zwrotnego i w każdym kroku
pyta solvera, jakiego opóźnienia wymaga odległość do najbliższej stacji.

Dzięki temu czas jazdy między stacjami przestaje być liczbą wpisaną do scenariusza
i staje się **przewidywaniem modelu**, porównywalnym z rozkładem STIB zmierzonym
w T-113. `line --timetable` robi to porównanie automatycznie i **kończy się kodem 1**,
gdy model okaże się wolniejszy od rozkładu.

Rdzeń nie importuje Godota (reguła 9); `data/` nietknięte (reguła 6).

## 2. Weryfikacja — rzeczywiste wyjście

```
$ dotnet run --project src/Sim.Runner -- line --axis data/track/L1_A.json \
    --limit-kmh 72 --exchange-s 10.5 --load AW0 --timetable build/timetable.json
```

```
[LINIA] L1_A: 11 zatrzymań, 6686.69 m, 725.43 s, postoje 209.09 s, kroków 89333, koniec=arrived
[LINIA] limit 72.00 km/h, wymiana 10.5 s, hamulec 100 % służbowego, okno stacji 5.0 m, obciążenie AW0 170000 kg
[ZAŁOŻENIE] SpeedLimitMps = 20 — jedno ograniczenie na całą oś; speed_limits w data/track/*.json jest puste we wszystkich sześciu pakietach, a 80 km/h z rejestru M7 to prędkość konstrukcyjna pojazdu (design_model), nie prędkość dopuszczalna na torze
[ZAŁOŻENIE] PassengerExchangeSeconds = 10.5 — brak źródła (T-312). T-113 ogranicza od góry: postój rozkładowy minus cykl drzwi 8,5 s, czyli ≤ 10,5 s przy medianowym postoju 19 s
[ZAŁOŻENIE] BrakeUsageFraction = 1 — ułamek hamulca służbowego, przy którym maszynista zaczyna hamować; praktyka prowadzenia STIB nie jest publikowana
[ZAŁOŻENIE] StopWindowM = 5 — okno rozpoznania stacji przez pętlę, nie dokładność zatrzymania M7 — rzeczywisty błąd zatrzymania jest mierzony i wychodzi w StationCall.StopErrorM
[STACJA] Beekkant: przyjazd 43.27 s na 509.43 m (błąd -0.306 m), jazda 43.27 s na 509.43 m, szczyt 72.00 km/h
[STACJA] Étangs Noirs|Zwarte Vijvers: przyjazd 127.77 s na 1451.69 m (błąd -0.305 m), jazda 65.50 s na 942.26 m, szczyt 72.00 km/h
[STACJA] Comte de Flandre|Graaf van Vlaanderen: przyjazd 195.31 s na 2054.62 m (błąd -0.304 m), jazda 48.53 s na 602.92 m, szczyt 72.00 km/h
[STACJA] Sainte-Catherine|Sint-Katelijne: przyjazd 266.00 s na 2720.71 m (błąd -0.304 m), jazda 51.68 s na 666.09 m, szczyt 72.00 km/h
[STACJA] De Brouckère: przyjazd 323.83 s na 3130.07 m (błąd -0.294 m), jazda 38.82 s na 409.36 m, szczyt 69.83 km/h
[STACJA] Gare Centrale|Centraal Station: przyjazd 391.31 s na 3732.06 m (błąd -0.299 m), jazda 48.47 s na 601.99 m, szczyt 72.00 km/h
[STACJA] Parc|Park: przyjazd 445.70 s na 4075.95 m (błąd -0.296 m), jazda 35.38 s na 343.89 m, szczyt 65.07 km/h
[STACJA] Arts-Loi|Kunst-Wet: przyjazd 507.34 s na 4561.28 m (błąd -0.299 m), jazda 42.63 s na 485.33 m, szczyt 72.00 km/h
[STACJA] Maelbeek|Maalbeek: przyjazd 574.31 s na 5152.74 m (błąd -0.306 m), jazda 47.96 s na 591.46 m, szczyt 72.00 km/h
[STACJA] Schuman: przyjazd 627.11 s na 5467.68 m (błąd -0.303 m), jazda 33.79 s na 314.93 m, szczyt 62.75 km/h
[STACJA] Merode: przyjazd 725.43 s na 6686.69 m (błąd -0.300 m), jazda 79.32 s na 1219.01 m, szczyt 72.00 km/h
[LINIA] największy błąd zatrzymania: 0.306 m
[ROZKŁAD] Beekkant → Étangs Noirs|Zwarte Vijvers: model 65.50 s, rozkład 78 s, rezerwa +12.50 s
[ROZKŁAD] Étangs Noirs|Zwarte Vijvers → Comte de Flandre|Graaf van Vlaanderen: model 48.53 s, rozkład 58 s, rezerwa +9.47 s
[ROZKŁAD] Comte de Flandre|Graaf van Vlaanderen → Sainte-Catherine|Sint-Katelijne: model 51.68 s, rozkład 71 s, rezerwa +19.32 s
[ROZKŁAD] Sainte-Catherine|Sint-Katelijne → De Brouckère: model 38.82 s, rozkład 51 s, rezerwa +12.18 s
[ROZKŁAD] De Brouckère → Gare Centrale|Centraal Station: model 48.47 s, rozkład 61 s, rezerwa +12.53 s
[ROZKŁAD] Gare Centrale|Centraal Station → Parc|Park: model 35.38 s, rozkład 39 s, rezerwa +3.62 s
[ROZKŁAD] Parc|Park → Arts-Loi|Kunst-Wet: model 42.63 s, rozkład 51 s, rezerwa +8.37 s
[ROZKŁAD] Arts-Loi|Kunst-Wet → Maelbeek|Maalbeek: model 47.96 s, rozkład 54 s, rezerwa +6.04 s
[ROZKŁAD] Maelbeek|Maalbeek → Schuman: model 33.79 s, rozkład 45 s, rezerwa +11.21 s
[ROZKŁAD] Schuman → Merode: model 79.32 s, rozkład 90 s, rezerwa +10.68 s
[ROZKŁAD] dopasowanych odcinków: 10 z 10
```

```
$ dotnet test tests/Sim.Tests
Passed!  - Failed: 0, Passed: 205, Skipped: 0, Total: 205

$ python3 tools/tests/test_all.py
  406/406 przeszło
```

## 3. Model jest szybszy od rozkładu na wszystkich 49 odcinkach sieci

**Przeliczone 04.09.2026 na commicie `7d15987`.** Liczby w tej sekcji i w §4 zmieniły
się od pierwszej wersji raportu; przyczyna jest w §3a i nie jest usterką modelu.

Sześć pakietów, limit 72 km/h, wymiana pasażerów 10,5 s, AW0:

| pakiet | zatrzymań | droga | czas | kroków | odcinków dopasowanych | model wolniejszy |
|---|---:|---:|---:|---:|---:|---:|
| L1_A | 11 | 6686,05 m | 725,42 s | 89 332 | 10 z 10 | **0** |
| L1_B | 8 | 5082,93 m | 533,67 s | 66 321 | 7 z 7 | **0** |
| L2_E | 16 | 9020,47 m | 1029,59 s | 125 832 | 15 z 15 | **0** |
| L5_C | 8 | 5386,11 m | 548,78 s | 68 135 | 7 z 7 | **0** |
| L5_D | 6 | 3846,93 m | 396,76 s | 49 892 | 5 z 5 | **0** |
| L6_F | 6 | 4456,36 m | 427,57 s | 53 589 | 5 z 5 | **0** |

**49 z 49 odcinków dopasowanych** do rozkładu i na żadnym model nie jest wolniejszy.
Dopasowanie idzie po `stop_id`, nie po nazwie — patrz §6. Wniosek jest ten sam co
w pierwszej wersji; zmieniły się wyłącznie liczby.

Najciaśniejszy odcinek sieci przy 72 km/h to **Gare Centrale → Parc** z rezerwą
**+3,63 s** — i to nie jest ten sam odcinek, który wiąże limit prędkości (§4).
Przy pełnym limicie decyduje najkrótszy postój rozkładowy, a przy limicie obniżanym
decyduje odcinek najdłuższy; te dwa pytania mają różne odpowiedzi.

### 3a. Dlaczego te liczby różnią się od pierwszej wersji raportu

Pierwsza wersja podawała dla L1_A **6686,69 m i 89 333 kroków**. Dziś wychodzi
**6686,05 m i 89 332 kroki** — mniej o 0,64 m i o jeden krok. Wszystkie sześć pakietów
skróciło się o 0,25–0,64 m.

Powód ustalony **bisekcją po commitach**, a nie z domysłu:

```
543b303  T-401 (ten raport)                   6686.69 m, 89333 kroków
3c378d9  T-313 (bloki stałe i ochrona)        6686.05 m, 89332 kroki
da278ae  T-314                                6686.05 m, 89332 kroki
93b4c59  #112                                 6686.05 m, 89332 kroki
196c43f  T-320 trasa                          6686.05 m, 89332 kroki
90a8c31  T-320 LineDrive                      6686.05 m, 89332 kroki
ba93903  .NET 8 -> 10                         6686.05 m, 89332 kroki
HEAD     7d15987                              6686.05 m, 89332 kroki
```

Zmiana wchodzi między `543b303` i `3c378d9`, ale **nie jest w kodzie rdzenia**:
w tym zakresie `src/Sim/Train/` i `src/Sim/Physics/` nie są tknięte. Zmieniły się
**dane osi**. Commit `4a03982` („Kilometraż stacji liczony na osi, która trafia do
pliku", #86) przeliczył kilometraże stacji na tej polilinii, która faktycznie leży
w pliku, zamiast na źródłowej przed przepróbkowaniem. Dla L1_A:

| stacja | przed #86 | po #86 |
|---|---:|---:|
| Beekkant | 509,74 | 509,73 |
| Étangs Noirs | 1452,00 | 1451,90 |
| Schuman | 5467,98 | 5467,35 |
| **Merode** (ostatnia) | **6686,99** | **6686,35** |

`length_m` osi to 6686,35 m, więc **przed #86 ostatnia stacja leżała 0,64 m ZA końcem
zadeklarowanej osi**. Po #86 leży dokładnie na nim. Skrócenie przejazdu o 0,64 m jest
więc dokładnie tą poprawką, a nie regresem — dane zrobiły się dokładniejsze.

Że stary plik był niespójny, mówi `tools/track/validate.py` puszczony na wersji
z `543b303`. Jest to **ostrzeżenie, nie błąd** — pierwsza wersja tego akapitu pisała
„przekroczenie", i to było za mocne:

```
$ python3 -c "... V.validate(L1_A z 543b303)"
PRZED #86  ok=True błędów=0 ostrzeżeń=2
     OSTRZ: rzut ostatniej stacji wypada 0.636 m za końcem osi (6686.99 m wobec
            6686.35 m); mieści się w ostatnim odcinku (14.99 m), ale kilometraż
            jest obcinany przy odczycie pozycji
DZIŚ       ok=True błędów=0 ostrzeżeń=1     (zostaje tylko brak głębokości stacji)
```

Ostrzeżenie samo nazywa mechanizm: kilometraż był **obcinany przy odczycie pozycji**.
Dlatego 0,636 m nie przekładało się na 0,636 m przejazdu — po #86 nie ma czego obcinać
i różnica wychodzi na 0,64 m drogi oraz jeden krok.

Stara wartość nie zniknęła: #86 dopisał do każdej stacji `source_chainage_m`
z kilometrażem źródłowym, więc obie liczby są w pliku i da się je porównać.

**Czego to NIE tłumaczy.** Limity z §4 przesunęły się po stronie C# o 0,02–0,27 km/h,
a po stronie Pythona o najwyżej 0,01 km/h. Przy odcinkach, których długości zmieniły
się o centymetry, asymetria tego rzędu nie wynika wprost z #86 i **nie ustaliłem jej
przyczyny**. Drugą możliwością jest metoda wyszukiwania limitu: pierwsza wersja raportu
nie zapisała swojej, więc nie da się jej powtórzić. Dzisiejsza jest opisana w §4 wprost,
żeby następny przebieg był porównywalny — i to jest cała nauka z tego miejsca.

## 4. Dwie niezależne implementacje wskazują te same sześć odcinków

T-113 liczy dolne ograniczenie prędkości liniowej **w Pythonie**, profilem idealnym:
rozpęd, jazda ustalona, hamowanie ze wzoru zamkniętego, przyjazd dokładnie na czas.
Tutaj liczy je **C#**, krok po kroku, pętlą sprzężenia zwrotnego, z hamulcem narastającym
przez ograniczenie zrywu i z oporami ruchu działającymi przez cały przejazd.

**Metoda po stronie C#, żeby dała się powtórzić:** bisekcja po `--limit-kmh`
w przedziale [40,00; 72,00] km/h, dwanaście połowień, kryterium to kod wyjścia
`line --timetable` (0 = cały pakiet mieści się w rozkładzie, 1 = model wolniejszy
na co najmniej jednym odcinku). Rozdzielczość wynikowa 0,01 km/h. Odcinek wiążący
wskazany osobno: przebieg o 0,02 km/h poniżej znalezionego limitu, pierwszy odcinek
z ujemną rezerwą. Po stronie Pythona: `tools/physics/schedule_envelope.py --mass AW0`,
najwyższe `min_top_speed_kmh` w pakiecie.

Najmniejszy limit prędkości, przy którym cały pakiet mieści się w rozkładzie
(04.09.2026, commit `7d15987`, `build/timetable.json` z feedu `2_20_20260831_010702`):

| pakiet | Python (T-113) | C# (ta pętla) | różnica | odcinek wiążący — Python | odcinek wiążący — C# |
|---|---:|---:|---:|---|---|
| L1_A | 57,41 | **58,09** | +0,68 | Schuman → Merode | Schuman → Merode |
| L1_B | 56,45 | **57,56** | +1,11 | Roodebeek → Vandervelde | Roodebeek → Vandervelde |
| L2_E | 57,47 | **58,49** | +1,02 | Ribaucourt → Yser | Ribaucourt → Yser |
| L5_C | 57,02 | **58,34** | +1,32 | Aumale → Saint-Guidon | Aumale → Saint-Guidon |
| L5_D | 57,64 | **58,68** | +1,04 | Beaulieu → Demey | Beaulieu → Demey |
| L6_F | 54,10 | **55,05** | +0,95 | Bockstael → Stuyvenbergh | Bockstael → Stuyvenbergh |

**Wszystkie sześć odcinków wiążących jest identycznych** — tak samo jak w pierwszej
wersji raportu, i to jest wynik, który się nie ruszył. Różnica ma jeden znak
i mieści się w 0,68–1,32 km/h. To jest cena prowadzenia po sprzężeniu zwrotnym zamiast
po profilu idealnym: maszynista, który reaguje, jest wolniejszy od profilu policzonego
z góry. Kierunek jest ten, którego się oczekuje; gdyby C# wyszło **szybsze** od profilu
idealnego, znaczyłoby to błąd w jednym z dwóch modeli.

Dolne ograniczenie prędkości liniowej dla sieci rośnie więc z **57,64 km/h** (Python,
wiąże Beaulieu → Demey) do **58,68 km/h** (C#, ten sam odcinek). Nadal jest to
ograniczenie **dolne i warunkowe** względem modelu rozpędzania i hamowania, a nie
pomiar prędkości dopuszczalnej — patrz `docs/21-measured-vs-assumed.md` §4d.

Koperta Pythona obejmuje **55 odcinków** rozkładowych, z czego 0 niewykonalnych;
pętla C# porównuje 49, bo liczy tylko odcinki między zatrzymaniami na osi pakietu.
Ta różnica jest z definicji zakresu, nie z niezgodności.

## 5. Trzy usterki sterowania, które wyszły dopiero na śladzie

Pierwsza wersja pętli dawała poprawnie wyglądające liczby — zatrzymania z błędem
0,001 m i sensowne czasy — i była **błędna**. Wyszło to dopiero po dołożeniu `--trace`
i obejrzeniu przebiegu krok po kroku.

**Usterka 1: próg hamowania sprawdzany również w trakcie hamowania.** Opory ruchu hamują
mocniej, niż zakłada wzór zamknięty z T-311 (ten jest czysto kinematyczny), więc wymagane
opóźnienie spadało poniżej progu, pętla wracała do nastawnika, odległość malała i hamulec
wracał. W śladzie:

```
    t= 86.12 v=  8.19 km/h polecenie=1.000 opóźnienie=1.1000
    t= 88.12 v=  3.11 km/h polecenie=0.000 opóźnienie=1.0938
    t= 90.12 v=  0.35 km/h polecenie=1.000 opóźnienie=0.9875
```

**3,12 s pełzania na 1,08 m** — trzy sekundy doliczone do czasu jazdy przez sterowanie,
nie przez fizykę. Próg wyzwala teraz hamowanie, ale nim nie steruje.

**Usterka 2: wzór zamknięty użyty do sterowania, a nie tylko do wyzwolenia.** Droga
hamowania z T-311 zawiera człon narastania hamulca zrywem **od zera**. Gdy hamulec już
działa, ten człon jest zaliczany drugi raz: solver kredytuje narastanie, które się właśnie
odbyło, żąda mniejszego opóźnienia, skład jedzie dalej, i tak w kółko. Skutkiem było
łagodne dojeżdżanie do peronu i **odcinek wolniejszy od rozkładu nawet przy 80 km/h**.
Próg używa teraz wzoru z narastaniem (bo odpowiada na pytanie „kiedy zacząć"), a samo
hamowanie prowadzi czysta kinematyka `v²/2d`.

**Usterka 3: polecenie hamulca mylone z opóźnieniem całkowitym.** Skład zwalnia też
oporami ruchu i składową pochylenia, niezależnie od nastawy. Polecenie dostaje więc
różnicę. Bez tego odjęcia skład hamował mocniej, niż prosił solver, i stawał przed
peronem — zmierzone **3,17 m przed Merode** przy 60 km/h.

Po trzech poprawkach największy błąd zatrzymania na pakiecie A wynosi **0,306 m** i nie
kumuluje się wzdłuż linii. Pozostała resztka to dyskretyzacja kroku 1/120 s.

Test regresyjny `Raz_zaczete_hamowanie_nie_wraca_do_trakcji` przypina usterkę 1. Pilnuje
przy tym właściwej rzeczy: zerowe polecenie hamulca samo w sobie regresją **nie jest** —
gdy opory wystarczają, odpuszczenie hamulca jest poprawną odpowiedzią serwa. Regresją
jest dopiero powrót nastawnika.

## 6. Złączenie po identyfikatorze, nie po nazwie

Pierwsza wersja porównania z rozkładem dopasowywała stacje po nazwie i trafiała
**6 z 10** odcinków pakietu A. Brakujące cztery to te, w których nazwa na osi ma
diakrytyk: `Étangs Noirs|Zwarte Vijvers`, `De Brouckère`. Normalizacja Unicode miała to
załatwić i **nie załatwiła**: `Sim.Runner.csproj` ma `InvariantGlobalization=true`,
w którym `Normalize(FormD)` jest pustą operacją.

Rozwiązaniem nie było naprawianie normalizacji, tylko **przestanie porównywać teksty**.
`AxisStation` niesie teraz `stop_id` z GTFS — ten sam identyfikator, którym rozkład
opisuje peron. Po zmianie: **10 z 10**. Ta sama zasada, którą stosuje już
`tools/track/timetable.py`: nazwy różnią się wielkością liter i wariantem językowym,
identyfikatory nie.

## 7. Czego świadomie nie zrobiłem

- **Nie wpisałem prędkości liniowej do `data/track/*.json`.** `data/` jest tylko do
  odczytu, a 58,75 km/h jest ograniczeniem dolnym warunkowym względem modelu. W polu
  `speed_limits` wyglądałoby dokładnie tak samo jak ograniczenie ze źródła STIB.
- **Nie wpisałem czasu wymiany pasażerów jako domyślnego.** `LineRunSettings` nie ma
  wartości domyślnych w konstruktorze — ta sama decyzja, co brak konstruktora
  bezargumentowego w `DoorCycle`. Użyte 10,5 s to **górny kres z T-113**, podany
  jawnie w wywołaniu i wypisany jako `[ZAŁOŻENIE]`, a nie stała w kodzie.
- **Nie dołożyłem oporów ruchu do solvera hamowania.** To jest zakres T-311 i tam była
  to świadoma decyzja: solver jest czysto kinematyczny. Skutek jest w tę stronę, w którą
  ma być — solver żąda mniejszego opóźnienia, niż skład potrafi, więc pomyłka kończy się
  zatrzymaniem **przed** peronem, a nie za nim.
- **Nie ruszyłem sceny Godota.** Pętla siedzi w rdzeniu, żeby dała się przetestować bez
  silnika; wpięcie jej do `src/Game` to osobny krok.
- **Nie modelowałem ograniczeń prędkości wzdłuż osi ani sygnalizacji.** Pierwsze nie ma
  źródła, drugie to T-313 (zablokowane przez R-003).

## 8. Co zauważyłem, ale nie tknąłem

- **Rozkład ma jeden odcinek wyraźnie ciaśniejszy od reszty**: Gare Centrale → Parc,
  343,89 m w 39 s, rezerwa 3,62 s przy 72 km/h wobec mediany ok. 11 s. Najkrótszy odcinek
  pakietu A ma najmniejszą rezerwę — to sugeruje, że rozkład jest układany na czas jazdy,
  a nie na stałą rezerwę procentową. Z jednego dnia i jednego pakietu nie da się tego
  rozstrzygnąć.
- **Chainage ostatniej stacji pakietu A (6686,99 m) jest większy niż `length_m`
  z pliku (6686,35 m)** — to różnica między łamaną źródłową a zagęszczoną, opisana już
  w T-111. Nie wpływa na ten przejazd, ale jest widoczna w wyjściu i warto, żeby ktoś
  kiedyś zdecydował, która długość jest tą „oficjalną".
- **`--timetable` czyta wyjście narzędzia z T-113**, które czeka w niescalonym PR #80.
  Samo polecenie `line` działa bez niego; bez #80 nie ma tylko czym wyprodukować
  `build/timetable.json`.
