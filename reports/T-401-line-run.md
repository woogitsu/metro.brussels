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

Sześć pakietów, limit 72 km/h, wymiana pasażerów 10,5 s, AW0:

| pakiet | zatrzymań | droga | czas | odcinków dopasowanych | model wolniejszy od rozkładu |
|---|---:|---:|---:|---:|---:|
| L1_A | 11 | 6686,69 m | 725,43 s | 10 z 10 | **0** |
| L1_B | 8 | 5083,40 m | 533,67 s | 7 z 7 | **0** |
| L2_E | 16 | 9021,01 m | 1029,60 s | 15 z 15 | **0** |
| L5_C | 8 | 5386,67 m | 548,87 s | 7 z 7 | **0** |
| L5_D | 6 | 3847,18 m | 396,73 s | 5 z 5 | **0** |
| L6_F | 6 | 4456,80 m | 427,53 s | 5 z 5 | **0** |

**49 z 49 odcinków dopasowanych** do rozkładu i na żadnym model nie jest wolniejszy.
Dopasowanie idzie po `stop_id`, nie po nazwie — patrz §6.

## 4. Dwie niezależne implementacje wskazują te same sześć odcinków

T-113 policzył dolne ograniczenie prędkości liniowej **w Pythonie**, profilem idealnym:
rozpęd, jazda ustalona, hamowanie ze wzoru zamkniętego, przyjazd dokładnie na czas.
Tutaj liczy je **C#**, krok po kroku, pętlą sprzężenia zwrotnego, z hamulcem narastającym
przez ograniczenie zrywu i z oporami ruchu działającymi przez cały przejazd.

Najmniejszy limit prędkości, przy którym cały pakiet mieści się w rozkładzie:

| pakiet | Python (T-113) | C# (ta pętla) | różnica | odcinek wiążący — Python | odcinek wiążący — C# |
|---|---:|---:|---:|---|---|
| L1_A | 57,41 | **58,36** | +0,95 | Schuman → Merode | Schuman → Merode |
| L1_B | 56,46 | **57,58** | +1,12 | Roodebeek → Vandervelde | Roodebeek → Vandervelde |
| L2_E | 57,47 | **58,75** | +1,28 | Ribaucourt → Yser | Ribaucourt → Yser |
| L5_C | 57,03 | **58,36** | +1,33 | Aumale → Saint-Guidon | Aumale → Saint-Guidon |
| L5_D | 57,65 | **58,75** | +1,10 | Beaulieu → Demey | Beaulieu → Demey |
| L6_F | 54,11 | **55,23** | +1,12 | Bockstael → Stuyvenbergh | Bockstael → Stuyvenbergh |

**Wszystkie sześć odcinków wiążących jest identycznych**, a różnica jest systematyczna
i ma jeden znak: 0,95–1,33 km/h. To jest cena prowadzenia po sprzężeniu zwrotnym zamiast
po profilu idealnym — maszynista, który reaguje, jest wolniejszy od profilu policzonego
z góry. Kierunek jest ten, którego się oczekuje; gdyby C# wyszło **szybsze** od profilu
idealnego, znaczyłoby to błąd w jednym z dwóch modeli.

Dolne ograniczenie prędkości liniowej dla sieci rośnie więc z 57,65 km/h (T-113)
do **58,75 km/h**. Nadal jest to ograniczenie **dolne i warunkowe** względem modelu
rozpędzania i hamowania, a nie pomiar prędkości dopuszczalnej — patrz
`docs/21-measured-vs-assumed.md` §4d.

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
