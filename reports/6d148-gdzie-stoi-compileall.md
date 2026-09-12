# 6.D148 — krok `compileall` stoi w jednym workflow i to jest podział pracy, nie asymetria

**12.09.2026**, na `a7bc72c`. Wejście: `.github/workflows/*.yml`,
`tools/tests/test_ci_workflows.py`. Pozycja: `grep -l compileall` daje jeden plik
z dziesięciu; rozstrzygnąć, czy to asymetria do wyrównania, czy podział pracy.

## 1. Rozstrzygnięcie: podział pracy — i decyduje o tym jedna liczba

**`python-tests.yml` jest jednym z DWÓCH workflowów, które ruszają na każdym pull
requeście bez filtra `paths`.** Drugim jest `sim-tests.yml`. Pozostałe siedem ma
filtry ścieżek, a `prune-merged-branches.yml` chodzi wyłącznie ręcznie
(`workflow_dispatch`).

Kompilacja całego `tools/` dzieje się więc **na każdym PR**, niezależnie od tego,
które z pozostałych ośmiu wybierze filtr. Skopiowanie kroku do tamtych nie dodałoby
ani jednego pokrycia, a kosztowałoby 0,33 s razy osiem.

Jeden z dziesięciu wygląda na asymetrię dopóty, dopóki nie zapyta się, **który**.

## 2. Wejście pozycji jest nieprawdziwe

Pole „Dlaczego" mówiło: „dziewięć pozostałych workflowów w ogóle nie musi importować
`tools/`". Zmierzone: **dziewięć z dziesięciu ten kod WYKONUJE.**

| workflow | wykonuje kod z `tools/` | bezwarunkowy na PR |
|---|---|---|
| `blender-smoke.yml` | tak (`tools/ci/blender_smoke.sh`) | nie |
| `godot-first-run.yml` | tak (`tools/blender/*.py` wprost) | nie |
| `m7-shell.yml` | tak (`tools/ci/m7_shell_check.sh`) | nie |
| `material-style-smoke.yml` | tak (`tools/ci/material_style.sh`) | nie |
| **`prune-merged-branches.yml`** | **nie** | nie (ręczny) |
| `python-tests.yml` | tak (`tools/tests/test_all.py`) | **tak** |
| `sim-tests.yml` | tak (`tools/ci/assert_*.py`) | **tak** |
| `station-details.yml` | tak (`tools/ci/station_details.sh`) | nie |
| `tunnel-alignment.yml` | tak (`tools/ci/tunnel_alignment.sh`) | nie |
| `visual-regression.yml` | tak (`tools/ci/visual_smoke.sh`) | nie |

Osiem z nich robi to **przez skrypt powłoki**, który dopiero woła Pythona —
`blender_smoke.sh` uruchamia `tunnel_sweep.py`, `render_check.py`,
`make_test_track.py`, `capture_plan.py` i `test_all.py`; pozostałe podobnie.
Jedyny, który `tools/` nie dotyka wcale, rozmawia z API GitHuba i kasuje scalone
gałęzie.

**Czego to NIE zmienia:** uruchomienie konkretnego modułu nie jest kompilacją
wszystkich. Wartość kroku `compileall` polega na złapaniu błędu składni w module,
którego żaden job nie importuje — i właśnie dlatego liczy się, w ilu workflowach
stoi, a nie ile z nich dotyka `tools/`.

## 3. Co doszło do bramki

- `test_krok_compileall_stoi_dokladnie_w_jednym_workflow` — równością, nie progiem.
- **`test_krok_compileall_stoi_w_workflow_BEZWARUNKOWYM`** — to jest rozstrzygnięcie
  wykonane zamiast opisanego. Pilnuje rzeczy, która może zmienić się po cichu:
  dopisanie filtra `paths` do `python-tests.yml` zamienia kompilację `tools/`
  z bezwarunkowej w warunkową, **nie ruszając ani jednego wiersza kroku**.
- `test_dla_kazdego_workflow_wiadomo_czy_uruchamia_kod_z_tools` — dziesięć i dziewięć,
  przybite.
- Kontrola przyrządu na dwóch pułapkach czytnika, niżej.

## 4. Pułapka YAML-a, którą musi znać ten czytnik

**`on:` w YAML-u jest wartością logiczną, nie napisem.** `yaml.safe_load` zamienia
klucz `on:` na `True`:

```
klucze: ['name', True, 'permissions', 'jobs']
```

`dokument["on"]` rzuca więc `KeyError` na każdym workflow — a bramka, która ten
wyjątek złapie i pójdzie dalej, zamelduje „brak wyzwalaczy" dla wszystkich dziesięciu
i **będzie zielona**. KN-5 wykonuje ten przypadek wprost.

## 5. Kontrole negatywne

Baza: **80/80**. Po każdej `cp` z kopii i `md5sum -c: OK` na trzech plikach.

| | mutacja | wynik | co mówi |
|---|---|---|---|
| KN-1 | filtr `paths` dopisany do `python-tests.yml` | **76/80** | kompilacja staje się warunkowa i bramka to nazywa |
| KN-2 | krok `compileall` zdjęty z jedynego workflow | **79/80** | `stoi w [], a pomiar dał ['python-tests.yml']` |
| KN-3 | krok dopisany do drugiego workflow | **79/80** | `['blender-smoke.yml', 'python-tests.yml']` |
| KN-4 | ciało czytane z CAŁEGO pliku, nie z `run:` | **80/80 ZIELONA** | **zawężenie nie jest dziś load-bearing — patrz niżej** |
| KN-4b | to samo, po dopisaniu wejścia syntetycznego | **79/80** | mechanizm przybity, choć drzewo go nie odróżnia |
| KN-5 | czytnik pyta o `dokument["on"]` | **78/80** | pułapka z sekcji 4 |

### KN-4 zielona i co z niej wynikło

Czytanie całego pliku zamiast samych `run:` **nie zmienia odpowiedzi na dzisiejszych
dziesięciu plikach**: jedyny workflow, który kodu z `tools/` nie wykonuje, nie
wymienia `tools/` także nigdzie indziej. Zawężenie do `run:` jest więc dziś
**ubezpieczeniem, nie zmierzoną koniecznością** — ta sama sytuacja, co przy
kolejności `Jednostki` (6.D115) i przy odsianiu z 6.D147.

Zostaje, bo kosztuje zero, a workflow filtrowany na `tools/**` i nieuruchamiający
stamtąd niczego jest kształtem najzupełniej możliwym. Ale zdanie o nim ma mówić,
ile jest warte — i sam mechanizm dostał **wejście syntetyczne** w kontroli przyrządu,
żeby nie był deklaracją bez pokrycia. KN-4b pokazuje, że po tym dopisaniu zdjęcie
zawężenia już się zapala.

## 6. Czego nie zrobiono

- **Nie dopisano kroku `compileall` do żadnego workflow** — sekcja 1 mówi, dlaczego
  nie ma po co.
- **Nie ruszono kolejności kroków ani nie dodano jobów** — pole „Poza zakresem".
- **Nie zmierzono, ile Pythona z `tools/` uruchamia każdy workflow z osobna.**
  Sekcja 2 podaje po jednym przykładzie na workflow; pełne rozwinięcie wymagałoby
  śledzenia wywołań przez skrypty powłoki, a pytanie pozycji było inne.
- **Nie sprawdzono, czy `sim-tests.yml` powinien mieć filtr `paths`.** Jest dziś
  bezwarunkowy i to podpiera rozstrzygnięcie z sekcji 1; czy tak ma zostać, jest
  pytaniem o tamten workflow, nie o ten krok.
