---
name: blender-asset
description: Generowanie i weryfikacja zasobów 3D w Blenderze headless dla Metro BXL.
---

# Zasoby 3D

1. Zawsze `blender --background --python ...`.
2. Geometria proceduralnie z danych; bez ręcznego modelowania jako źródła prawdy.
3. Każde zadanie geometrii kończy się renderami `_iso`, `_side`, `_inside` i ich obejrzeniem.
4. Profile z `tools/blender/profiles.py` są **wartościami projektowymi**, nie pomiarami infrastruktury STIB.
5. 1 jednostka = 1 metr; eksport GLB; nie commituj `build/` ani `renders/`.
6. Dzieła sztuki, logo, fonty i identyfikacja STIB podlegają `docs/03-legal.md`.
