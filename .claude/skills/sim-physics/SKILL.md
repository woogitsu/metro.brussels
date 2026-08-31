---
name: sim-physics
description: Model dynamiki pociągu, hamowania, drzwi, czasu postoju i sygnalizacji dla Metro BXL.
---

# Fizyka i symulacja

Przed kodem przeczytaj `docs/02-simulation.md` i uruchom `tools/physics/reference.py`.

Parametry mają klasy `spec`, `est`, `design`; nie awansuj oszacowań na fakty bez źródła. Krok symulacji jest stały: 1/120 s. Nic w `src/Sim/` nie importuje Godota.

Weryfikacja kodu musi zawierać rzeczywiste wyniki testów. Stan CBTC z 31.08.2026 to wdrożenie/testy, nie pełna eksploatacja na całych liniach 1 i 5.
