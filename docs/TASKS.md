# Rozpiska zadań

`[ ]` do zrobienia · `[x]` zweryfikowane · **[CZŁOWIEK]** nie dla agenta.

## Gotowe w szkielecie
- `[x]` **T-100** — walidator osi trasy
- `[x]` **T-001** — profile przekrojów z kontrolą skrajni M7
- `[x]` **T-002** — model referencyjny dynamiki M7
- `[x]` **T-003** — testy narzędzi

## Narzędzia

### [ ] T-010 · Pierwsze uruchomienie Blendera
- **Wejście:** `tools/blender/tunnel_sweep.py`, `render_check.py`, testowa oś
- **Wyjście:** `build/TEST.glb`, trzy rendery kontrolne
- **Weryfikacja:** generacja → render → obejrzenie trzech PNG
- **Skończone, gdy:** widać ciągły zakrzywiony tunel, a `_inside` pokazuje wnętrze
- **Poza zakresem:** materiały, prawdziwa trasa
- **Zależy od:** nic

### [ ] T-011 · Rozstawianie detali wzdłuż osi
- **Zależy od:** T-010

### [ ] T-012 · Zrzuty z gry dla agenta
- **Zależy od:** T-400

## Dane

### [ ] T-110 · Pobranie i normalizacja GTFS STIB
- **Wejście:** `data/network/sources.json`
- **Wyjście:** `tools/track/fetch_gtfs.py`, `data/network/stops.json`
- **Weryfikacja:** check liczby stacji, dat feedu i różnic nazw/ID
- **Skończone, gdy:** 59 stacji ma współrzędne i provenance
- **Poza zakresem:** pełne rozkłady
- **Zależy od:** nic

### [ ] T-111 · Oś pakietu A z oficjalnych danych + kontrola OSM
- **Wejście:** STIB Shapefiles, Brussels Mobility `Metro`, OSM, GTFS
- **Wyjście:** `tools/track/build_alignment.py`, `data/track/L1_A.json`, provenance
- **Weryfikacja:** `python3 tools/track/validate.py data/track/L1_A.json --line L1`
- **Skończone, gdy:** 12 stacji jest w poprawnej kolejności, bazowa geometria pochodzi z STIB, a różnice OSM/UrbIS są opisane
- **Poza zakresem:** profil pionowy, szczegółowe rozjazdy Beekkant
- **Zależy od:** T-110

### [ ] T-112 · Profil pionowy pakietu A
- **Wejście:** oś + `station-depths.csv`
- **Skończone, gdy:** pochylenia interpolowanego profilu są 0–4%, a każda wygenerowana wartość ma `interpolated:true` i `design_assumption`
- **Zależy od:** T-111, T-901

### [ ] T-113 · Rozkład jazdy i służby
- **Zależy od:** T-110

## Geometria

### [ ] T-210 · Tunel pakietu A z prawdziwej osi
- **Zależy od:** T-111, T-010

### [ ] T-211 · Zestaw wspólny elementów stacji
- **Zależy od:** T-010

### [ ] T-212 · Pierwsza stacja typowa
- **Zależy od:** T-211, T-210

### [ ] T-220 · Bryła zewnętrzna M7
- **Zależy od:** T-010

## Symulacja

### [ ] T-310 · Trakcja i opory ruchu
- **Wejście:** `docs/02-simulation.md`, `tools/physics/reference.py`
- **Wyjście:** `src/Sim/Physics/` + testy
- **Zależy od:** nic

### [ ] T-311 · Hamowanie
- **Zależy od:** T-310

### [ ] T-312 · Drzwi i czas postoju
- **Zależy od:** T-310

### [ ] T-313 · Sygnalizacja klasyczna
- **Zależy od:** T-311

### [ ] T-314 · CBTC + ATS jako osobny tryb
- **Wejście:** zweryfikowany stan wdrożenia z `sources.json`
- **Skończone, gdy:** tryb CBTC nie jest aktywny w scenariuszu historycznym 31.08.2026 bez potwierdzenia pełnego uruchomienia STIB
- **Zależy od:** T-313

### [ ] T-320 · Rdzeń linii — wiele składów naraz
- **Zależy od:** T-313, T-113

## Silnik

### [ ] T-400 · Scena Godota i pierwszy przejazd
- **Zależy od:** T-210, T-212, T-320

## Zadania dla człowieka

### [ ] **[CZŁOWIEK]** T-901 · Głębokości stacji pakietu A
Wypełnić `data/network/station-depths.csv`; agent nie zgaduje.

### [ ] **[CZŁOWIEK]** T-902 · Kierunek artystyczny tunelu

### [ ] **[CZŁOWIEK]** T-903 · Kontakt ze STIB w sprawie marki/oznaczeń/sztuki

### [ ] **[CZŁOWIEK]** T-904 · Weryfikacja parametrów M7

### [ ] **[CZŁOWIEK]** T-905 · Nagrania dźwiękowe
