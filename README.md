# Metro BXL

Symulator metra brukselskiego. Szkielet przygotowany pod pracę z Claude Code.

## Start

```bash
bash doctor.sh
python3 tools/tests/test_all.py      # 15 testów bazowych
```

Następne zadanie: **T-010** z `docs/TASKS.md` — pierwsze rzeczywiste uruchomienie pipeline'u Blendera.

## Pipeline geometrii

```bash
python3 tools/track/make_test_track.py --out data/track/TEST.json
blender --background --python tools/blender/tunnel_sweep.py -- --centerline data/track/TEST.json --profile box_double --out build/TEST.glb
blender --background --python tools/blender/render_check.py -- --in build/TEST.glb --out renders/TEST
```

Obowiązkowo obejrzyj `renders/TEST_iso.png`, `_side.png`, `_inside.png`.

## Struktura

- `CLAUDE.md` — konstytucja pracy agentów
- `docs/` — architektura, symulacja, legal, research i roadmapa
- `data/network/lines.json` — bazowy snapshot sieci
- `data/network/sources.json` — rejestr źródeł, licencji i provenance
- `data/network/station-depths.csv` — wartości do T-901; agent ich nie zgaduje
- `tools/track/` — generator testowej osi i walidator
- `tools/blender/` — profile, generator tunelu i render kontrolny
- `tools/physics/` — model referencyjny dynamiki
- `tools/tests/` — testy regresyjne bez Blendera
- `.claude/skills/` — `track-data`, `blender-asset`, `sim-physics`
- `.github/workflows/` — CI narzędzi Pythona

## Źródła danych

Research z 31.08.2026: `docs/07-open-data-research.md`. Bazowa geometria trasy ma pochodzić z oficjalnych danych STIB, regionalne dane Brussels Mobility/Paradigm służą jako niezależna kontrola, a OSM jako źródło szczegółów torowych i kolejna kontrola.

## Stan

Narzędzia niewymagające Blendera zostały sprawdzone lokalnie. Skrypty `tunnel_sweep.py` i `render_check.py` wymagają pierwszego rzeczywistego uruchomienia w Blenderze w T-010. CBTC w scenariuszu historycznym 31.08.2026 jest traktowany jako system w trakcie wdrożenia/testów, nie jako pełna eksploatacja na całych liniach 1 i 5.
