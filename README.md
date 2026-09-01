# Metro BXL

Symulator prowadzenia pociągu na rzeczywistej sieci metra STIB/MIVB w Brukseli.
Cztery linie, 59 stacji, 39,9 km, tabor M7, przejście z sygnalizacji klasycznej na CBTC.

Zasada architektoniczna, z której wynika cała reszta:

> **Linia jest symulacją, która działa bez gracza. Kabina jest jednym z jej widoków.**

Reguły pracy: `CLAUDE.md`. Architektura: `docs/01-architecture.md`.

## Start

```bash
bash doctor.sh                       # kontrola środowiska i testów
python3 tools/tests/test_all.py      # testy narzędzi, bez Blendera i bez sieci
```

## Stan: co działa, a czego nie ma

**Działa i jest zweryfikowane wizualnie:**

- pipeline Blendera — generacja, render kontrolny, wykrywanie regresji, odrzucanie pustej klatki;
- oś pozioma pakietu A (Gare de l'Ouest — Merode, 12 stacji, 6686 m) z oficjalnej geometrii STIB;
- proceduralny tunel pakietu A: 12 chunków, szczelina na szwie 0,000 mm, normalne do wnętrza;
- eksport per chunk plus manifest streamingowy dla Godota;
- proceduralna skorupa M7: 94,0 m, 6 członów, 18 drzwi podwójnych na stronę;
- skrajnia M7 w tunelu, mierzona **dwiema niezależnymi drogami** zgodnymi do 3,9 mm.

**Czego nie ma i dlaczego:**

- **kodu gry.** `src/` jest pusty. Nie ma projektu Godota, rdzenia fizyki ani kabiny.
  Najkrótsza droga do pierwszego przejazdu to T-310 (#20) i T-400 (#26);
- **profilu pionowego.** Brak publicznych rzędnych główki szyny, a dwa oficjalne źródła
  podają sprzeczne głębokości stacji. Cały tunel jest wariantem `flat-preview` na Z = 0,
  a generator **odrzuca** `--variant production`. Zablokowane: T-112 (#10);
- **stacji.** Brak długości peronów, wyjść i komunikacji pionowej. Zablokowane: R-004 (#16);
- **toru, trzeciej szyny, rozjazdów.** Zablokowane: R-005 (#17).

Pełny audyt tego, co jest faktem o brukselskim metrze, a co decyzją projektową:
**`docs/21-measured-vs-assumed.md`**.

## Pipeline geometrii

Każdy z tych skryptów kończy się nieprzechodzącym statusem, jeżeli geometria jest zła.
Wszystkie chodzą na GitHub-hosted `ubuntu-latest`.

```bash
bash tools/ci/blender_smoke.sh       # T-010: generacja + render + testy negatywne
bash tools/ci/visual_smoke.sh        # T-012: determinizm, regresja, pusta klatka
bash tools/ci/m7_shell_check.sh      # T-220: skorupa M7 i jej wymiary
bash tools/ci/tunnel_alignment.sh    # T-210: tunel pakietu A, chunki, manifest
bash tools/ci/vehicle_clearance.sh   # skrajnia M7 w tunelu, pomiar na siatce
```

Pojedyncze wywołania:

```bash
# tunel z rzeczywistej osi, z podziałem na chunki
blender --background --python tools/blender/tunnel_sweep.py -- \
  --centerline data/track/L1_A.json --profile box_double --name L1_A \
  --out build/L1_A.glb --metrics build/L1_A-metrics.json \
  --chunk-dir build/chunks --chunk-manifest build/chunks/L1_A-chunks.json

# render kontrolny wg canonical manifestu kamer
blender --background --python tools/visual/capture_blender.py -- \
  --in build/L1_A.glb --set alignment --prefix L1_A --out renders \
  --centerline data/track/L1_A.json
```

**Rendery trzeba obejrzeć.** Metryka automatyczna nie zastępuje oględzin — jednolita
szara klatka przechodzi kontrolę „nie jest pusta". Szczegóły: `docs/17-visual-regression.md`.

## Struktura

| ścieżka | co tam jest |
|---|---|
| `CLAUDE.md` | konstytucja pracy agentów |
| `docs/` | architektura, symulacja, konwencje, legal, research, audyt wymiarów |
| `reports/` | raporty z wykonanych zadań, z rzeczywistymi wynikami weryfikacji |
| `data/network/` | snapshot sieci, rejestr źródeł i licencji, głębokości do T-901 |
| `data/track/` | oś pakietu A i jej provenance |
| `data/vehicle/` | specyfikacja M7 |
| `tools/track/` | pobieranie i budowa danych trasy, transformacje CRS, kontrole krzyżowe |
| `tools/blender/` | profile, generator tunelu, skorupa M7, osadzenie pojazdu, skrajnia |
| `tools/visual/` | canonical manifest kamer, kadrowanie, porównanie renderów |
| `tools/ci/` | pipeline'y weryfikacyjne, jeden na zadanie |
| `tools/tests/` | testy bez Blendera i bez sieci |
| `src/` | **pusty** — rdzeń symulacji jeszcze nie istnieje |

Skille w `.claude/skills/`: `blender-asset`, `track-data`, `sim-physics`.

## Zasady, które łatwo złamać przez przypadek

1. **Nie zgaduj danych o sieci.** Hierarchia źródeł: oficjalne STIB → oficjalne dane
   Regionu/Paradigm → OSM → źródła wtórne. Czego nie da się potwierdzić — pytasz.
2. **Nie modeluj ręcznie tego, co da się wygenerować.** Każdy zasób 3D powstaje przez
   skrypt w `tools/blender/`.
3. **1 jednostka = 1 metr.** Wszędzie.
4. **`src/Sim/` nie importuje Godota.** Rdzeń ma się kompilować i testować bez silnika.
5. **Nie commituj** `build/`, `renders/`, plików > 10 MB.
6. **`queued` nie jest weryfikacją.** Zadanie jest zweryfikowane po zielonym jobie
   i sprawdzeniu artefaktów.

## Źródła danych

Rejestr maszynowy: `data/network/sources.json` — URL, licencja, atrybucja, ograniczenia
i data sprawdzenia dla każdego źródła. Hierarchia i uzasadnienia:
`docs/07-open-data-research.md`. Provenance pobranych danych: `docs/09-data-provenance.md`.

Bazowa geometria trasy pochodzi z oficjalnych danych STIB, regionalne dane Brussels
Mobility/Paradigm służą jako niezależna kontrola, OSM jako źródło szczegółów torowych
i kolejna kontrola. **Rozbieżności między źródłami są liczone i zapisywane, nigdy
uśredniane.**

## Zastrzeżenie

CBTC w scenariuszu historycznym 31.08.2026 jest traktowany jako system w trakcie
wdrożenia i testów, nie jako pełna eksploatacja na całych liniach 1 i 5.

Projekt nie używa brandingu, logotypów, map, piktogramów ani dzieł sztuki STIB/MIVB.
Zasady: `docs/03-legal.md`.
