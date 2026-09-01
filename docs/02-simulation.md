# Model symulacji

Kod w `src/Sim/` ma odtwarzać obecny **model projektowy**. Parametry mają provenance: `spec` = potwierdzone źródłem pierwotnym, `observed` = obserwacja operacyjna, `est` = oszacowanie historyczne do usunięcia/weryfikacji, `design_model` = świadome założenie symulatora.

Canonical ground truth M7: `data/vehicle/m7-spec.json`. Audyt: `docs/08-m7-ground-truth.md`.

## Parametry M7

| parametr | wartość | pochodzenie |
|---|---:|---|
| człony | 6 | `spec` STIB |
| długość | 94,0 m | `spec` STIB |
| szerokość | 2,70 m | `spec` STIB |
| wysokość podłogi | 1,03 m | `spec` STIB |
| pojemność manualna | 742 osób | `spec` STIB — to nie jest definicja AW2 |
| masa AW0 | ~170,0 t | `spec` STIB, wartość przybliżona |
| moc zainstalowana | 16 × 135 kW = 2160 kW | `spec` STIB |
| prędkość maks. używana przez model | 80 km/h | `design_model`, brak primary-source Vmax M7 w T-904 |
| napędzane 4/6 | 4/6 | `design_model`, tylko legacy parametr limitu adhezji |
| masa modelowa AW2 | 221,94 t | `design_model`: 170 t + 742 × 70 kg |
| przyspieszenie maks. | 1,10 m/s² | `design_model` |
| hamowanie służbowe | 1,10 m/s² | `design_model` |
| hamowanie awaryjne | 1,30 m/s² | `design_model` |
| ograniczenie zrywu | 0,75 m/s³ | `design_model` |

## Opory ruchu

`r = 1.5 + 0.006·v + 0.00035·c·v²`, gdzie `v` w km/h, `c=1.40` w tunelu i `1.00` na powierzchni. Wszystkie współczynniki są `design_model` do kalibracji; nie są parametrami CAF/STIB.

## Trakcja

Moc zainstalowana `2160 kW` jest source-backed `spec`. Charakterystyka siła–prędkość nie jest publicznie potwierdzona. Model zachowuje projektowe `F0 = 248,9 kN`, lecz region stałej mocy jest ograniczony do 2160 kW. Wynikowy punkt przejścia to około `31,24 km/h` i jest **pochodną modelu**, nie specyfikacją pojazdu.

Ograniczenie przyczepnościowe modelu: `F <= μ · m · (4/6) · g`; `4/6`, `μ=0,25` sucho i `0,13` mokro pozostają `design_model`.

Referencję liczy `tools/physics/reference.py`.

## Drzwi i postój

Cykl: odblokowanie 0,5 s → otwieranie 2,0 s → wymiana pasażerów → sygnał zamykania 3,0 s → zamykanie 2,5 s → kontrola 0,5 s. Czasy są `design_model`, dopóki brak źródła operacyjnego. Jazda zablokowana do potwierdzenia zamknięcia.

## Sygnalizacja

### Klasyczna
Blok stały, sygnalizacja przytorowa i abstrakcja ATP. Nie przypisywać STIB niepublikowanych granic bloków, aspektów i krzywych bezpieczeństwa.

### CBTC
Docelowy model: moving block, krzywa prędkości docelowej, jazda automatyczna i ATS. **Stan 31.08.2026 to wdrożenie i testy, nie pełna eksploatacja CBTC na całych liniach 1 i 5.** Scenariusz historyczny 2026 nie może automatycznie przełączać linii na moving block. Osobny tryb realizuje T-314.

## Czego nie symulujemy

Pojedynczych osi i sprężyn, termiki silników, zużycia klocków, pełnej elektryki trakcyjnej ani pogody na poziomie cząstek.