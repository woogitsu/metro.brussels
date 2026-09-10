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
| przyspieszenie rozruchu (wynik modelu) | 1,342 m/s² AW0 / 1,025 m/s² AW2 | **pochodna**, nie sufit — patrz niżej |
| hamowanie służbowe | 1,10 m/s² | `design_model` |
| hamowanie awaryjne | 1,30 m/s² | `design_model` |
| ograniczenie zrywu | 0,75 m/s³ | `design_model` |

### Przyspieszenie jest WYNIKIEM, nie parametrem — 6.D86

Do 10.09.2026 stało w tej tabeli `przyspieszenie maks. | 1,10 m/s² | design_model`.
Liczba **nie występuje w kodzie ani w danych pojazdu**, żaden test jej nie czytał,
a w modelu nie ma żadnego obcięcia, które by ją egzekwowało. Przyspieszenie rozruchu
wychodzi z siły, mas i oporów:

    a(0) = (F0 − Davis(0)) / (m · 1,08)

    AW0   (248 900 − 2 502) N / (170 000 · 1,08) kg  =  1,342 m/s²
    AW2   (248 900 − 3 266) N / (221 940 · 1,08) kg  =  1,025 m/s²

Deklarowane 1,10 nie było żadną z tych dwóch wartości — leżało między nimi. Sufit
przyczepnościowy **nie wiąże**: `μ·m·(4/6)·g` daje 277,9 kN (AW0) i 362,7 kN (AW2),
czyli więcej niż `F0 = 248,9 kN`, więc to siła rozruchowa rozstrzyga, a nie tarcie.
Mnożnik `1,08` to masa efektywna (bezwładność wirujących mas).

**Obcięcia w kodzie NIE MA i ta pozycja go nie wprowadza.** Wartość projektowa
przyspieszenia jest w `data/vehicle/m7-spec.json` wpisana wprost jako nieznana
(`unknown_parameters`: „source-backed maximum acceleration"), więc jej wybór jest
decyzją właściciela, a nie skutkiem ubocznym poprawki w dokumencie.

Liczby wyżej pilnuje `tools/tests/test_reference_snapshot.py`, licząc je z modelu
i porównując z tą tabelą — osobno od pytania, czy sam model się zmienił.

## Opory ruchu

`r = 1.5 + 0.006·v + 0.00035·c·v²`, gdzie `v` w km/h, `c=1.40` w tunelu i `1.00` na powierzchni. Wszystkie współczynniki są `design_model` do kalibracji; nie są parametrami CAF/STIB.

## Trakcja

Moc zainstalowana `2160 kW` jest source-backed `spec`. Charakterystyka siła–prędkość nie jest publicznie potwierdzona. Model zachowuje projektowe `F0 = 248,9 kN`, lecz region stałej mocy jest ograniczony do 2160 kW. Wynikowy punkt przejścia to około `31,24 km/h` i jest **pochodną modelu**, nie specyfikacją pojazdu.

Ograniczenie przyczepnościowe modelu: `F <= μ · m · (4/6) · g`; `4/6`, `μ=0,25` sucho i `0,13` mokro pozostają `design_model`.

Referencję liczy `tools/physics/reference.py`.

## Hamowanie

Wartości projektowe (1,10 / 1,30 m/s², zryw 0,75 m/s³) są `design_model` i nie mają
źródła pierwotnego. T-311 dokłada do nich trzy rzeczy i **żadna nie wprowadza nowej
liczby o M7**:

1. **Sufit przyczepnościowy** `b_max = μ · f · g / λ`, gdzie `f` to udział masy na
   osiach hamowanych. Udziału `f` **nie ma w żadnym źródle**, więc jest jawnym
   `design_assumption` o dwóch wariantach skrajnych: 1,0 (hamują wszystkie osie) i
   4/6 (hamują tylko osie napędne). Sufit nie zależy od masy składu.
2. **Solver punktu hamowania** z ograniczeniem zrywu, wzorem zamkniętym:
   `s(b) = (v₀² − v₁²)/(2b) + v₀·b/(2j) − b³/(24 j²)` i `t(b) = (v₀ − v₁)/b + b/(2j)`.
   Powyżej `b = √(2 j Δv)` droga przestaje zależeć od opóźnienia — zostaje sam zryw.
3. **Droga hamowania z oporami Davisa**, liczona tym samym `TrainController`, który
   prowadzi skład w grze. Opory skracają drogę i to skrócenie domyka się z bilansem
   energii.

Rozdziału hamulca elektrodynamicznego i pneumatycznego, charakterystyki zanikania ED
i krzywych bezpieczeństwa STIB **nie modelujemy** — nie ma ich w rejestrze źródeł.

Tablice referencyjne: `reports/T-311-braking.md`. Referencję liczy
`tools/physics/braking.py`, niezależnie od `src/Sim`.

## Drzwi i postój

Cykl: odblokowanie 0,5 s → otwieranie 2,0 s → wymiana pasażerów → sygnał zamykania 3,0 s → zamykanie 2,5 s → kontrola 0,5 s. Czasy są `design_model`, dopóki brak źródła operacyjnego. Jazda zablokowana do potwierdzenia zamknięcia.

## Sygnalizacja

### Klasyczna
Blok stały, sygnalizacja przytorowa i abstrakcja ATP. Nie przypisywać STIB niepublikowanych granic bloków, aspektów i krzywych bezpieczeństwa.

### CBTC
Docelowy model: moving block, krzywa prędkości docelowej, jazda automatyczna i ATS. **Stan 31.08.2026 to wdrożenie i testy, nie pełna eksploatacja CBTC na całych liniach 1 i 5.** Scenariusz historyczny 2026 nie może automatycznie przełączać linii na moving block. Osobny tryb realizuje T-314.

## Czego nie symulujemy

Pojedynczych osi i sprężyn, termiki silników, zużycia klocków, pełnej elektryki trakcyjnej ani pogody na poziomie cząstek.