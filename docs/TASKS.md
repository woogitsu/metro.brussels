# Rozpiska zadań

`[ ]` do zrobienia · `[x]` zweryfikowane · **[CZŁOWIEK]** nie dla agenta.

**Źródłem prawdy o statusie są GitHub Issues**, nie ten plik. Ten plik jest mapą
zależności i zakresów. Statusy poniżej odzwierciedlają to, co **realnie leży w repo**
na dzień 01.09.2026 — zadanie jest odhaczone tylko wtedy, gdy jego artefakty istnieją
w `main` i przechodzą CI.

## Gotowe w szkielecie
- `[x]` **T-100** — walidator osi trasy
- `[x]` **T-001** — profile przekrojów z kontrolą skrajni M7
- `[x]` **T-002** — model referencyjny dynamiki M7
- `[x]` **T-003** — testy narzędzi

## Narzędzia

### [x] T-010 · Pierwsze uruchomienie Blendera
- **Wyjście:** `tools/ci/blender_smoke.sh`, workflow `blender-smoke.yml`
- **Weryfikacja:** generacja → render → obejrzenie trzech PNG, plus cztery testy negatywne

### [ ] T-011 · Rozstawianie detali wzdłuż osi
- **Zależy od:** T-010

### [~] T-012 · Zrzuty kontrolne i wykrywanie regresji
- **Zrobione:** część Blenderowa — canonical manifest kamer `tools/visual/cameras.json`,
  deterministyczny render, metryki, odrzucanie pustej klatki, `docs/17-visual-regression.md`
- **Zostaje:** przechwytywanie z Godota
- **Zależy od:** T-400 (tylko część Godotowa)

## Dane

### [x] T-110 · Pobranie i normalizacja GTFS STIB
- **Wyjście:** `tools/track/fetch_gtfs.py`, `tools/track/normalize_stops.py`, `data/network/stops.json`

### [x] T-111 · Oś pakietu A z oficjalnych danych + kontrola OSM
- **Wejście:** STIB Shapefiles, Brussels Mobility `Metro`, OSM, GTFS
- **Wyjście:** `tools/track/build_alignment.py`, `data/track/L1_A.json`, provenance
- **Weryfikacja:** `python3 tools/track/validate.py data/track/L1_A.json --line L1`
- **Wynik:** 447 punktów, 6686,35 m, 12 stacji; kontrola krzyżowa w `reports/L1_A-crosscheck.md`
- **Poza zakresem:** profil pionowy, szczegółowe rozjazdy Beekkant
- **Zależy od:** T-110

### [ ] T-112 · Profil pionowy pakietu A — **ZABLOKOWANE**
- **Blokada:** brak publicznych rzędnych główki szyny; dwa oficjalne źródła podają
  **sprzeczne** głębokości stacji (Schuman 15 m vs 17,42 m; Botanique 21,5 vs 20 m).
  Dopóki to trwa, tunel jest wariantem `flat-preview`, a generator odrzuca `--variant production`
- **Wejście:** oś + `station-depths.csv`
- **Skończone, gdy:** pochylenia interpolowanego profilu są 0–4%, a każda wygenerowana wartość ma `interpolated:true` i `design_assumption`
- **Zależy od:** T-111, T-901

### [ ] T-113 · Rozkład jazdy i służby
- **Zależy od:** T-110

## Geometria

### [x] T-210 · Tunel pakietu A z prawdziwej osi
- **Wyjście:** `tools/blender/sweep.py` + `tunnel_sweep.py`, `tools/ci/tunnel_alignment.sh`,
  `reports/L1_A-geometry.md`, `reports/L1_A-chunks.md`
- **Wynik:** 12 chunków, 6686,74 m, szczelina na szwie 0,000 mm, normalne do wnętrza,
  eksport per chunk z manifestem streamingowym
- **Uwaga:** wyłącznie wariant `flat-preview` — profil pionowy czeka na T-112

### [ ] T-211 · Zestaw wspólny elementów stacji — **ZABLOKOWANE**
- **Blokada:** brak długości i wysokości peronów, wyjść i komunikacji pionowej (R-004)
- **Zależy od:** T-010, R-004, R-005

### [ ] T-212 · Pierwsza stacja typowa — **ZABLOKOWANE**
- **Zależy od:** T-211 (samo zablokowane), T-210

### [x] T-220 · Bryła zewnętrzna M7
- **Wyjście:** `tools/blender/m7_shell.py`, `m7_layout.py`, `reports/M7-shell.md`
- **Wynik:** 94,0 m, 6 członów, 18 drzwi podwójnych na stronę; skrajnia w tunelu zmierzona
  na siatce i wzorem, zgodność 3,9 mm (`reports/M7-in-tunnel.md`)
- **Uwaga:** bez wózków — rozstaw czopów skrętu nie ma źródła

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

### [x] **[CZŁOWIEK]** T-904 · Weryfikacja parametrów M7
Wynik w `docs/08-m7-ground-truth.md` i `data/vehicle/m7-spec.json`; siedem wartości
ze statusem `spec`, reszta wymiarów pojazdu to jawne założenia projektowe.

### [ ] **[CZŁOWIEK]** T-905 · Nagrania dźwiękowe

## Czego brakuje w tej rozpisce

Poniższe zadania istnieją jako Issues, ale nie mają tu wpisu. Dopóki go nie mają,
**Issues są jedynym źródłem prawdy** o ich zakresie:

- **T-114** — proweniencja pobranych danych (`tools/data/provenance.py`, `docs/09`), **zrobione**;
- **R-002 … R-005** — ground truth źródeł, sygnalizacji, stacji i infrastruktury torowej;
- **T-901** — rzędne i głębokości pakietu A, blokuje T-112.

## Co blokuje co, w jednym miejscu

| brakująca dana | blokuje | gdzie szukać |
|---|---|---|
| rzędne główki szyny, głębokości stacji | T-112 → produkcyjny tunel | T-901, `data/network/station-depths.csv` |
| długości i wysokości peronów, wyjścia | T-211 → T-212 | R-004 |
| przekrój tunelu, geometria toru, trzecia szyna | wiarygodność wymiarów w `profiles.py` | R-005 |
| rozstaw czopów skrętu M7 | pełna skrajnia kinematyczna | brak źródła publicznego |

Zmierzone alternatywy dla wymiarów projektowych i powody, dla których **nie zostały
podstawione do kodu**: `docs/21-measured-vs-assumed.md`.
