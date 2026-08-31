# Model symulacji

Kod w `src/Sim/` ma odtwarzać obecny **model projektowy**. Parametry mają provenance: `spec` = źródło techniczne, `est` = oszacowanie do weryfikacji, `design` = cel gry.

## Parametry M7

| parametr | wartość | pochodzenie |
|---|---:|---|
| człony | 6 | spec |
| długość | 94,0 m | spec |
| szerokość | 2,70 m | spec |
| pojemność AW2 | 742 | spec |
| prędkość maks. | 80 km/h | spec |
| człony napędne | 4 z 6 | spec |
| masa AW0 | 155,0 t | est |
| masa AW2 | 206,9 t | est |
| przyspieszenie maks. | 1,10 m/s² | design |
| hamowanie służbowe | 1,10 m/s² | design |
| hamowanie awaryjne | 1,30 m/s² | design |
| ograniczenie zrywu | 0,75 m/s³ | design |
| prędkość bazowa | 35 km/h | design |

## Opory ruchu

`r = 1.5 + 0.006·v + 0.00035·c·v²`, gdzie `v` w km/h, `c=1.40` w tunelu i `1.00` na powierzchni. Parametry są modelem projektowym do kalibracji.

## Trakcja

`F0 = 248,9 kN`; do 35 km/h siła stała, powyżej model stałej mocy. Ograniczenie przyczepnościowe: `F <= μ · m · 4/6 · g`. Przyjęto `μ=0,25` sucho i `0,13` mokro.

Referencję liczy `tools/physics/reference.py`.

## Drzwi i postój

Cykl: odblokowanie 0,5 s → otwieranie 2,0 s → wymiana pasażerów → sygnał zamykania 3,0 s → zamykanie 2,5 s → kontrola 0,5 s. Jazda zablokowana do potwierdzenia zamknięcia.

## Sygnalizacja

### Klasyczna
Blok stały, semafory przytorowe, ATP. Każda interwencja ma być poprzedzona ostrzeżeniem i zakończona jasnym wyjaśnieniem dla gracza.

### CBTC
Docelowy model: moving block, krzywa prędkości docelowej, jazda automatyczna i ATS. **Stan 31.08.2026 to wdrożenie i testy, nie pełna eksploatacja CBTC na całych liniach 1 i 5.** Scenariusz historyczny 2026 nie może automatycznie przełączać linii na moving block. Osobny tryb realizuje T-314.

## Czego nie symulujemy

Pojedynczych osi i sprężyn, termiki silników, zużycia klocków, pełnej elektryki trakcyjnej ani pogody na poziomie cząstek.
