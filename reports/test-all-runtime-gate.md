# Bramka na czas przebiegu `test_all.py` (6.D11)

**Zmierzone 06.09.2026 na commicie:** `045730bd639c771d59b6d3b876c4d390d85f16ad`

Zestaw ma dziś **1709** testów w **80** modułach (`| 6.D11 |` w `docs/TASKS.md` mówi
1638 i 62,8 s — obie liczby sprawdzone, obie nieaktualne; ten sam wiersz mówi wprost
„1638 jest już nieaktualne… dziś zestaw ma ich ponad 1700", co się zgadza). Po
dopisaniu tej pozycji (`test_suite_runtime_budget.py`, sześć testów) jest **1715**
testów w **81** modułach.

- **Zmierzone.** Cztery przebiegi CAŁEGO procesu `python3 tools/tests/test_all.py`
  z rzędu, ten sam kod, ta sama liczba testów (1709), na kontenerze DZIELONYM z innymi
  sesjami agenta: **66,20 / 68,45 / 68,96 / 77,04 s**. Trzy najdroższe moduły, stałe
  we wszystkich przebiegach: `test_station_layout.py` (**27,7 s**, 17 testów),
  `test_mutation_sweep.py` (**13,8 s**, 64 testy), `test_schedule_envelope.py`
  (**7,9 s**, 22 testy).
- **Wyliczone.** Próg bramki CI to `SUITE_RUNTIME_BUDGET_S = 150.0` w
  `tools/tests/test_suite_runtime_budget.py` — dwukrotność najwyższego zmierzonego
  przebiegu (77,04 s × 2 = 154,08 s), zaokrąglona w dół do liczby czytelnej. Bramka
  żyje w kroku CI (`.github/workflows/python-tests.yml`), **nie** w kodzie wyjścia
  `test_all.py` — powód jest w §5, i jest zmierzony, nie estetyczny.

## 1. Co jest mierzone, a czego nie

Mierzony jest czas ŚCIANY (wall-clock) całego procesu `python3 tools/tests/test_all.py`
— dokładnie to, co płaci krok CI `Run tool tests` przy każdym pull requeście, licząc
uruchomienie interpretera, importy `tools/blender`, `tools/track`, `tools/physics`,
`tools/data`, odkrycie i instrumentację AST wszystkich 80(81) modułów `test_*.py`
oraz samą pętlę wykonania testów. To NIE jest to samo, co licznik, który dopisano do
`main()` tego zadania: ten drugi liczy WYŁĄCZNIE pętlę testów, po tym jak `_discover()`
już skończyło import i instrumentację, i wypada niżej o czas tego importu —
zmierzone: 68,450 s ściany wobec 67,287 s z licznika wewnętrznego tego samego
przebiegu, różnica 1,16 s. Obie liczby są w tym raporcie, żeby czytelnik `test_all.py`
i czytelnik logu CI patrzyli na to samo źródło, a nie na dwie liczby o tej samej
nazwie.

Nie jest mierzony `dotnet test tests/Sim.Tests` (osobny job, `sim-tests.yml`, pozycja
6.D2) ani nic z Blendera/Godota — `test_all.py` jest z definicji zestawem bez nich.

## 2. Metoda pomiaru

```
S=$(date +%s.%N); python3 tools/tests/test_all.py > log 2>&1; E=$(date +%s.%N)
```
powtórzone cztery razy z rzędu, bez ŻADNEJ zmiany w drzewie między przebiegami. Maszyna
jest kontenerem Linux 6.18.44, 4 rdzenie, 15 GiB RAM, **dzielonym z innymi sesjami
agenta** — `ps aux` w trakcie serii pokazywał równolegle `dotnet build`/Roslyn z
sąsiedniego worktree i proces Godota (`--headless --line`) z jeszcze innego. To ten
sam rodzaj współdzielenia, co `reports/linecore-budget.md` §0 opisuje dla pozycji 5.7,
i ten sam powód, dla którego 6.D2 mówi o „różnym obciążeniu maszyny" zamiast zakładać
maszynę pustą.

Modułowy rozkład czasu pochodzi z instrumentacji dopisanej w `tools/tests/test_all.py`
(`main()`): `time.perf_counter()` wokół każdego wywołania testu, zsumowany per plik
źródłowy (`module_of`, lista równoległa do płaskiej listy `tests` — zachowana w tym
kształcie, bo `test_assertion_gate.py` sprawdza literalnie fragmenty `main()` i
`_discover()`, patrz §5).

## 3. Czas per moduł — WSZYSTKIE 81 modułów (po dopisaniu tej pozycji)

Zmierzone na jednym, w pełni zielonym przebiegu (`1715/1715 przeszło`), zaraz po
dopisaniu `tools/tests/test_suite_runtime_budget.py`. **Trzy najdroższe pogrubione.**

| moduł | czas (s) | testów |
|---|---:|---:|
| **`test_station_layout.py`** | **27,695** | 17 |
| **`test_mutation_sweep.py`** | **13,809** | 64 |
| **`test_schedule_envelope.py`** | **7,859** | 22 |
| `test_m7_report.py` | 6,211 | 43 |
| `test_platform_length_in_pipeline.py` | 3,056 | 4 |
| `test_ci_workflows.py` | 1,690 | 56 |
| `test_clearance_profile.py` | 1,042 | 88 |
| `test_chunks.py` | 0,830 | 51 |
| `test_sweep.py` | 0,813 | 35 |
| `test_shot_metadata_gate.py` | 0,765 | 31 |
| `test_all.py` | 0,635 | 45 |
| `test_visual.py` | 0,616 | 66 |
| `test_crs_convergence.py` | 0,470 | 19 |
| `test_docs_ci_claims.py` | 0,373 | 5 |
| `test_inspire_rail.py` | 0,328 | 37 |
| `test_clearance.py` | 0,247 | 16 |
| `test_backlog.py` | 0,200 | 26 |
| `test_braking.py` | 0,198 | 30 |
| `test_dotnet_version.py` | 0,187 | 26 |
| `test_m7_shell.py` | 0,162 | 21 |
| `test_detail_layout.py` | 0,151 | 33 |
| `test_report_claims.py` | 0,147 | 5 |
| `test_parameter_boundaries.py` | 0,136 | 28 |
| `test_godot_warning_gate.py` | 0,090 | 14 |
| `test_validate_axis.py` | 0,087 | 38 |
| `test_network_chainage.py` | 0,085 | 12 |
| `test_stations.py` | 0,068 | 22 |
| `test_tuning_constants.py` | 0,053 | 5 |
| `test_lod.py` | 0,051 | 75 |
| `test_dimension_audit.py` | 0,050 | 14 |
| `test_visual_gates.py` | 0,043 | 20 |
| `test_tunnel_manifest.py` | 0,042 | 39 |
| `test_report_hygiene.py` | 0,040 | 9 |
| `test_reference_snapshot.py` | 0,040 | 3 |
| `test_t401_citation.py` | 0,040 | 5 |
| `test_surface_sections.py` | 0,025 | 28 |
| `test_placement.py` | 0,024 | 29 |
| `test_packages.py` | 0,022 | 31 |
| `test_xml_doc_blocks.py` | 0,021 | 3 |
| `test_gtfs_stops.py` | 0,020 | 18 |
| `test_next_task.py` | 0,020 | 6 |
| `test_line_trace_gate.py` | 0,018 | 16 |
| `test_crosscheck_alignment.py` | 0,015 | 20 |
| `test_timetable.py` | 0,015 | 39 |
| `test_alignment.py` | 0,014 | 57 |
| `test_make_test_track.py` | 0,012 | 15 |
| `test_snapshot_source.py` | 0,008 | 9 |
| `test_blender_cli.py` | 0,008 | 10 |
| `test_streaming_fixture.py` | 0,007 | 8 |
| `test_tunnel_width.py` | 0,007 | 28 |
| `test_engine_version.py` | 0,004 | 6 |
| `test_axis_claims.py` | 0,004 | 3 |
| `test_assertion_gate.py` | 0,004 | 22 |
| `test_data_freshness.py` | 0,004 | 9 |
| `test_station_components.py` | 0,003 | 22 |
| `test_platform_dimensions.py` | 0,003 | 11 |
| `test_visual_identical_pixels.py` | 0,002 | 9 |
| `test_architecture_doc.py` | 0,002 | 4 |
| `test_readme_claims.py` | 0,002 | 4 |
| `test_fetchers.py` | 0,002 | 16 |
| `test_station_kit.py` | 0,002 | 23 |
| `test_png_pixels.py` | 0,002 | 4 |
| `test_render_engine.py` | 0,001 | 8 |
| `test_detail_markers.py` | 0,001 | 18 |
| `test_art_direction.py` | 0,001 | 10 |
| `test_vehicle_fit.py` | 0,001 | 12 |
| `test_line_calls_gate.py` | 0,001 | 7 |
| `test_audio_rights.py` | 0,001 | 9 |
| `test_rights_matrix.py` | 0,001 | 6 |
| `test_pr_template.py` | 0,001 | 8 |
| `test_profile_scan.py` | 0,000 | 39 |
| `test_crs.py` | 0,000 | 7 |
| `test_material_specs.py` | 0,000 | 16 |
| `test_suite_runtime_budget.py` | 0,000 | 6 |
| `test_glb_report.py` | 0,000 | 23 |
| `test_station_sections.py` | 0,000 | 4 |
| `test_capture_plan.py` | 0,000 | 28 |
| `test_camera_aim.py` | 0,000 | 20 |
| `test_lod_paths.py` | 0,000 | 5 |
| `test_marker_gates.py` | 0,000 | 3 |
| `test_scan_gates.py` | 0,000 | 12 |

RAZEM (licznik wewnętrzny, sama pętla testów): **68,605 s**, 1715 testów, 81 modułów.
Ściana tego samego przebiegu (mierzona z zewnątrz, krok CI): **70,028 s**.

**Trzy najdroższe razem = 49,363 s, czyli 71,9 % z 68,605 s RAZEM.** Reszta 78
modułów dzieli się resztą — mediana czasu modułu to rzędu **0,02 s**. To NIE jest
materiał na ratchet per-moduł: przyspieszanie `test_station_layout.py` czy
`test_mutation_sweep.py` jest **poza zakresem** tej pozycji (patrz `CLAUDE.md` §5 i
sekcja „Poza zakresem" niżej) i osobnym zadaniem, jeśli ktoś je kiedyś weźmie.

## 4. Skąd próg — arytmetyka, nie życzenie

```
najwyższy zmierzony przebieg  = 77,04 s
mnożnik                       = ×2      (patrz niżej dlaczego akurat tyle)
iloczyn                       = 154,08 s
próg w kodzie                 = 150,0 s  (zaokrąglone W DÓŁ, więc margines jest
                                          odrobinę WĘŻSZY niż ×2, nigdy szerszy)
```

Mnożnik ×2, a nie np. ×1,2 (sam rozrzut zmierzony na tej maszynie, 15,45 % względem
średniej), bo próg musi przeżyć DWIE rzeczy, których ta sesja nie zmierzyła, a nie
jedną:

1. **Prędkość maszyny właściciela.** CI chodzi na puli `woogitsu` (`CLAUDE.md` §9),
   nie na tym kontenerze. Ta sesja nie ma pomiaru z tamtej maszyny — może być
   szybsza, może wolniejsza, może mieć własny wzorzec współdzielenia (cztery
   runnery na czterech maszynach, ale poszczególne joby innych repozytoriów tej
   samej organizacji nadal dzielą sieć/dysk/harmonogram OS).
2. **Wzrost zestawu.** Ten sam wiersz `docs/TASKS.md`, który zleca tę pozycję, mówi
   „zestaw rośnie z każdym zadaniem — w tej sesji o kilkadziesiąt testów dziennie".
   Próg dostrojony tuż nad dzisiejszym maksimum (np. ×1,1) wymagałby przeliczania
   co kilka dni, czyli przestałby być bramką na REGRES i stałby się rytuałem
   przy każdym PR-ze, który dopisuje testy — dokładnie to, przed czym ostrzega
   uwaga zadania: „próg wpisany zbyt ciasno zapali się u niego na czerwono bez
   żadnego regresu".

Test `test_budget_stays_above_the_measured_maximum_with_a_real_margin` przybija to
jako bramkę: `SUITE_RUNTIME_BUDGET_S` musi zostać WYŻEJ niż `MEASURED_MAX_WALL_S`
(77,04) z marginesem > ×1,2 — więc przyszła edycja, która obetnie próg do czegoś
ciasnego, pada na tym teście, zanim padnie na czymkolwiek w CI.

## 5. Dlaczego bramka NIE jest w kodzie wyjścia `test_all.py`

`tools/tests/mutation_sweep.py` (plik zarezerwowany dla innej pozycji, nie dotknięty)
uruchamia cały zestaw jako podproces i czyta z niego DWIE rzeczy: linię
`N/M przeszło` (regex `SUMMARY`) i kod wyjścia. `run_suite` uznaje mutację za
**PRZEŻYTĄ** dokładnie wtedy, gdy `passed == total` **i** `returncode == 0`. Gdyby
`main()` w `test_all.py` zwracał 1 również przy przekroczeniu progu czasu, KAŻDE
spowolnienie maszyny podczas przemiatania mutacyjnego (a `mutation_sweep.py` odpala
ten sam zestaw setki razy pod rząd, równolegle na kilku robotnikach — dokładnie ten
scenariusz, który dziś generuje na tej maszynie kontencję) zamieniłoby się w falę
fałszywych **zabić** — tej samej rodziny usterki, co
`reports/wyrocznia-mutacyjna-falszywe-zabicia.md`, tylko odwróconej (tam fałszywe
przeżycie, tu byłaby fałszywa śmierć).

Dlatego: `test_all.py` wypisuje czas (§3) i **nic więcej** — kod wyjścia zależy
wyłącznie od poprawności testów, jak przed tym zadaniem. Sam próg i decyzja
„przekroczono/nie" żyją w kroku CI (`.github/workflows/python-tests.yml`, krok
`Run tool tests`), PO zakończeniu procesu:

```bash
budget="$(python3 -c "import sys; sys.path.insert(0,'tools/tests'); import test_suite_runtime_budget as B; print(B.SUITE_RUNTIME_BUDGET_S)")"
start=$(date +%s.%N)
python3 tools/tests/test_all.py
end=$(date +%s.%N)
elapsed=$(python3 -c "print(f'{$end - $start:.3f}')")
echo "czas sciany test_all.py: ${elapsed} s (prog ${budget} s)"
python3 -c "import sys; sys.exit(0 if float('$elapsed') <= float('$budget') else 1)" || {
  echo "::error::zestaw test_all.py przekroczyl prog czasu sciany: ${elapsed} s > ${budget} s"
  exit 1
}
```

`set -euo pipefail` na początku kroku jest tu obowiązkowe, nie ozdobne: bez niego, gdy
`python3 tools/tests/test_all.py` pada (testy nie przechodzą), bash leciałby DALEJ do
własnego porównania czasu i krok mógłby zameldować sukces czasu mimo nieudanych
testów — `test_ci_gate_step_is_a_comparison_that_can_exit_non_zero` w
`tools/tests/test_suite_runtime_budget.py` pilnuje, żeby ten wiersz nie zniknął.

Próg NIE jest wpisany w YAML-u z ręki: krok czyta go z
`tools/tests/test_suite_runtime_budget.py` (`SUITE_RUNTIME_BUDGET_S`), tego samego
pliku, który niesie uzasadnienie marginesu i który jest zarazem częścią zestawu
testów (sześć testów w §7). Jedno miejsce prawdy — `test_ci_gate_step_reads_this_files_constant_not_a_second_copy`
pilnuje, żeby YAML nie dostał kiedyś drugiej, ukrytej kopii liczby.

## 6. Kontrola negatywna — WYKONANA

**Próg obniżony pod zmierzony czas, dwa niezależne mechanizmy, oba złapały.**

### 6.1 Obniżenie stałej w drzewie (łapie to bramka asercji `test_suite_runtime_budget.py`)

`SUITE_RUNTIME_BUDGET_S` obniżone z 150,0 na 10,0 (poniżej KAŻDEGO zmierzonego
przebiegu z §0), pełny zestaw uruchomiony bez żadnej innej zmiany:

```
  FAIL test_budget_constant_is_a_sane_positive_number: 10.0
  FAIL test_budget_stays_above_the_measured_maximum_with_a_real_margin: (10.0, 77.04)

  1713/1715 przeszło
```

Kod wyjścia procesu: **1** (dwa niezaliczone testy). Stała przywrócona do 150,0 od razu
po pomiarze; `git diff` na tym pliku jest dziś pusty.

**Dlaczego to jest silniejsza kontrola niż sam krok bash.** Ten mechanizm łapie błąd
NAJWCZEŚNIEJ, jak się da — na etapie samego `test_all.py`, zanim krok CI w ogóle
dotrze do porównania czasu ściany. Ale właśnie dlatego NIE demonstruje bezpośrednio
porównania bash z §5 — więc osobno, kontrola 6.2.

### 6.2 Samo porównanie z kroku CI, na realnym zmierzonym czasie (bez dotykania drzewa)

Dokładnie ten sam jednowierszowy warunek, który stoi w `python-tests.yml`, wykonany
z realnym zmierzonym `elapsed` z §0 (68,450 s) i progiem celowo obniżonym poniżej
niego — bez zmiany żadnego pliku:

```
$ elapsed=68.450; budget=40.0
$ python3 -c "import sys; sys.exit(0 if float('$elapsed') <= float('$budget') else 1)"
$ echo "kod wyjscia bramki (elapsed=$elapsed, budget obnizony do $budget): $?"
kod wyjscia bramki (elapsed=68.450, budget obnizony do 40.0): 1
```

Kod wyjścia **1** — dokładnie ten kod, który krok CI zamienia na `exit 1` całego
joba. Razem 6.1 i 6.2 pokazują dwie NIEZALEŻNE warstwy tej samej ochrony: obniżenie
stałej poniżej udokumentowanego pomiaru pada na miejscu (6.1), a gdyby mimo to
przeszło, prawdziwe przekroczenie czasu i tak zatrzyma krok CI (6.2).

## 7. Weryfikacja pełnego zestawu po zmianie

```
$ python3 tools/tests/test_all.py | tail -3
  1715/1715 przeszło

$ echo krok bramki (bash z §5) na tym samym drzewie:
czas sciany test_all.py: 66.254 s (prog 150.0 s)
[kod wyjścia kroku: 0]
```

`tools/tests/test_suite_runtime_budget.py` dodaje **6** testów (`1709 → 1715`,
`80 → 81` modułów): stała progu i margines (2), granica porównania `over_budget`
(2), i że krok YAML naprawdę czyta tę stałą i naprawdę umie wywalić joba (2).

## 8. Poza zakresem — świadomie nietknięte

- **Przyspieszanie `test_station_layout.py`, `test_mutation_sweep.py` ani żadnego
  innego modułu.** `CLAUDE.md` §5 i treść tej pozycji zabraniają tego wprost —
  pozycja stawia miarę, nie optymalizuje. Moduł drogi jest wynikiem pomiaru (§3), nie
  okazją do przepisania go przy okazji.
- **Kasowanie albo pomijanie testu, żeby zmieścić się w progu.** Nie zrobiono niczego
  takiego; próg 150,0 s ma margines właśnie po to, żeby nikt tego nigdy nie musiał
  rozważać jako sposobu na zieloną bramkę.
- **Bramka na czas pojedynczego modułu (ratchet per plik).** Poza zakresem pola
  „Wyjście" tej pozycji, które mówi o czasie CAŁEGO przebiegu; per-moduł jest tu
  wyłącznie diagnostyką (§3), nie osobną bramką.
- **Raport „czas przeglądu mutacyjnego"**, o którym mówi treść zadania (65,0 s w
  ciepłym drzewie, 50,9 s w świeżym worktree, plik w katalogu `reports` nazwany od
  tego tytułu) — **nie istnieje w tym worktree** (`ls reports/` tego pliku nie widzi).
  Ten plik opisuje inny pomiar,
  z innego katalogu roboczego równoległej sesji, na zestawie ZMNIEJSZONYM zaślepką
  `mutation_sweep.py` (64 testy własnego narzędzia zdjęte) — czyli NIE tę samą rzecz,
  którą mierzy krok CI (który zaślepki nie stosuje i chodzi na pełnym drzewie). Dlatego
  ten raport nie przepisuje tamtej liczby, tylko mierzy od zera na pełnym,
  niezaślepionym zestawie — zgodnie z „Sprawdź, nie przepisuj" z treści zadania.
- **6.D2** (bliźniak po stronie C#/`src/Sim`) — osobna pozycja, nietknięta.
