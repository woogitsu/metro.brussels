# T-320: zakres odtwarzania rozkładu na osi pakietu A

**Pomiar 24.09.2026 na `d583065`**, lokalny Windows, .NET 10, plan `classic-2026-L1_A`. To jest próba jednej osi i syntetycznych wyjazdów co 310 s, nie odtworzenie doby GTFS.

## Stan wejścia

`ServiceDay.FromJson` oraz `Sim.Runner service-day` odczytują z T-113 `duties.rows`, `block_id` i `trip_windows` i osobno liczą obiegi oraz szczyt służby. `LineCore.Add(id, releaseStep)` przyjmuje wiele składów, ale nie korzysta z `ServiceDay`; `Sim.Runner line` dodaje jeden skład, a `budget` wiele składów w stałym odstępie. `build/timetable.json` i archiwum GTFS nie były dostępne lokalnie podczas pomiaru. Sam JSON generatora zawiera zagregowane okna kursów w obiegach i zagregowane statystyki linii, lecz okna nie mają identyfikatora kursu, kierunku, przystanków ani przypisania do pakietu A. Nie da się więc z tego pliku wyznaczyć dokładnych wyjazdów na tę oś bez sięgnięcia do źródłowego GTFS i jawnego mapowania.

Liczby **48 kursów jednocześnie** i **71 obiegów** z T-113 obejmują całą sieć metra. Nie są oczekiwaną obsadą jednej osi L1_A. T-113 podaje 7 jednoczesnych kursów linii 1 w kierunku 0 na **całej linii**, nie tylko na pakiecie A.

## Pomiar jednej osi

Użyto 2 604 000 kroków przy 120 Hz (21 700 s = 6 h 1 min 40 s), planu 23 bloków, 12 stacji, limitu 70 km/h, postoju 8 s, obciążenia AW2 i odstępu 310 s (mediana T-113 dla L1). Liczba zgłoszonych składów jest oddzielona od liczby składów faktycznie na osi.

| Zgłoszone składy | Nawrót | Maksimum na osi | Średnio czeka | Koszt kroku |
|---:|---:|---:|---:|---:|
| 7 | wyłączony | 3 | 6,46 | 0,176 µs |
| 48 | wyłączony | 3 | 30,23 | 1,169 µs |
| 71 | wyłączony | 3 | 33,11 | 1,721 µs |
| 7 | 240 s | 7 | 0,00 | 2,188 µs |
| 48 | 240 s | 11 | 21,94 | 4,291 µs |
| 71 | 240 s | 11 | 25,56 | 4,721 µs |

Bez nawrotu skład po dojeździe zajmuje końcowy peron, więc przepływ się blokuje. 240 s jest **zmierzonym minimum nawrotu GTFS**, ale nawrót na Merode, końcu pakietu, pozostaje założeniem projektowym. Wyniku wariantu z nawrotem nie wolno przedstawiać jako rzeczywistego ruchu STIB. Koszt czasu jest tylko orientacyjnym pomiarem pojedynczej próby na współdzielonym komputerze; rozstrzygające są stany składów, nie mikrosekundy.

Reprodukcja z katalogu repozytorium (oba warianty `--turnback-s`):

```text
dotnet run --project src/Sim.Runner/Sim.Runner.csproj -c Release -- budget --axis data/track/L1_A.json --signalling data/design/signalling/classic-2026.json --limit-kmh 70 --exchange-s 8 --load AW2 --headway-s 310 --turnback-s 0 --trains 7,48,71 --steps 2604000 --warmup 0 --repeats 1
dotnet run --project src/Sim.Runner/Sim.Runner.csproj -c Release -- budget --axis data/track/L1_A.json --signalling data/design/signalling/classic-2026.json --limit-kmh 70 --exchange-s 8 --load AW2 --headway-s 310 --turnback-s 240 --trains 7,48,71 --steps 2604000 --warmup 0 --repeats 1
```

## Luka do kryterium T-320

Odtworzenie 48/71 wymaga modelu **wielu osi sieci**, mapowania każdego kursu i obiegu z feedu do osi oraz rozstrzygnięcia granic pakietów i zajętości peronów. Obecny `ServiceDay` weryfikuje obiegi czasowo, ale nie steruje `LineCore`; obecny `LineCore` symuluje jedną oś. Dokładny pomiar rozkładowej obsady samego pakietu A wymaga źródłowych kursów GTFS z przystankami i godzinami, których zagregowany `build/timetable.json` nie przenosi. Z tego powodu nie dodano adaptera ani polityki dyspozytora na podstawie niepełnych danych.
