---
name: track-data
description: Budowa osi trasy metra z oficjalnych danych STIB/MIVB i Regionu Brukselskiego, z OSM jako źródłem szczegółów i kontroli.
---

# Dane trasy

Priorytet: **STIB Shapefiles/GTFS → Brussels Mobility/Paradigm → OSM → źródła wtórne**. Pełny rejestr: `data/network/sources.json` i `docs/07-open-data-research.md`.

Pracuj w EPSG:31370 (Lambert 72), 1 jednostka = 1 metr. Origin sceny ustaw w Gare de l'Ouest.

Format `data/track/<PAKIET>.json`: `id`, `crs`, `points [[x,y,z]]`, `stations` z kilometrażem, opcjonalne `speed_limits`.

Nie ma zweryfikowanej publicznej niwelety toru w rejestrze projektu. Głębokości pochodzą z T-901. Każdy interpolowany profil jest modelem projektowym i musi mieć provenance/`design_assumption`.

Walidacja obowiązkowa:
`python3 tools/track/validate.py data/track/L1_A.json --line L1`

Nie pobieraj mirroru GitHub, jeśli istnieje oficjalny dataset producenta danych. Zachowuj atrybucję STIB i ODbL dla OSM.
