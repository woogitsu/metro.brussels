# Metro BXL

Symulator metra brukselskiego. Szkielet przygotowany pod pracę z Claude Code.

## Start w trzech krokach

```bash
bash doctor.sh                       # co jest, czego brakuje
python3 tools/tests/test_all.py      # 25 testów narzędzi
```

Potem otwórz Claude Code w tym katalogu i zleć **T-010** z `docs/TASKS.md`.

## Sprawdzenie, czy pętla działa

```bash
python3 tools/track/make_test_track.py --out data/track/TEST.json

blender --background --python tools/blender/tunnel_sweep.py -- \
    --centerline data/track/TEST.json --profile box_double --out build/TEST.glb

blender --background --python tools/blender/render_check.py -- \
    --in build/TEST.glb --out renders/TEST
```

Otwórz `renders/TEST_iso.png`, `_side.png`, `_inside.png`.
Widzisz zakrzywiony tunel od środka — narzędzia działają.

## Co jest w środku

```
CLAUDE.md                     konstytucja — agent czyta przed każdym zadaniem
doctor.sh                     kontrola środowiska
docs/
  00-network-data.md          fakty o sieci — źródło prawdy
  01-architecture.md          moduły, krok czasowy, determinizm, wybór silnika
  02-simulation.md            równania + tablica referencyjna dla testów
  03-legal.md                 twarde blokady prawne
  04-conventions.md           jednostki, osie, nazewnictwo, git
  05-glossary.md              słownik FR/NL/PL do czytania źródeł STIB
  06-worked-example.md        wzorcowo wykonane zadanie + kontrprzykład
  07-open-data-research.md    oficjalne źródła STIB/UrbIS/OSM + repo referencyjne
  TASKS.md                    rozpiska zadań, w tym zadania dla człowieka
  TASK-TEMPLATE.md            format nowego zadania
data/network/
  lines.json                  4 linie, 59 stacji, tabor, zajezdnie, sygnalizacja
  sources.json                rejestr źródeł, ról i licencji danych
  station-depths.csv          do wypełnienia przez człowieka (T-901)
tools/
  blender/profiles.py         przekroje tuneli + kontrola skrajni (bez bpy, testowalne)
  blender/tunnel_sweep.py     zamiatanie profilu po osi trasy
  blender/render_check.py     oczy agenta — trzy ujęcia kontrolne
  track/validate.py           walidator osi trasy
  track/make_test_track.py    generator danych testowych, także zepsutych
  physics/reference.py        tablica referencyjna dynamiki M7
  tests/test_all.py           25 testów, bez Blendera i bez pytest
.claude/skills/               blender-asset · track-data · sim-physics
.github/workflows/             CI: kompilacja narzędzi + testy Pythona
```

## Jak zlecać pracę

Jedno zadanie na raz, po numerze:

> Zrób T-010. Trzymaj się CLAUDE.md. Na koniec pokaż rendery i opisz, co na nich jest.
> Jeśli czegoś nie masz w danych — przerwij i zapytaj, nie zgaduj.

Nie zlecaj „zrób fazę 1". Agent pracuje dobrze na zadaniach z jednym wyjściem
i jednym sposobem sprawdzenia.

## Stan

Wszystkie skrypty **poza dwoma dla Blendera** są uruchomione i przetestowane.
Research źródeł z 31.08.2026 jest zapisany w `docs/07-open-data-research.md`.
`tunnel_sweep.py` i `render_check.py` są sprawdzone tylko składniowo — w środowisku,
w którym powstawały, nie było Blendera. Ich pierwsze uruchomienie to zadanie T-010.
