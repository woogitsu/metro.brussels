# Bramki bez wykonanej kontroli negatywnej — pomiar dla wszystkich 80 modułów

**Zmierzone 06.09.2026 na commicie:** `045730bd639c771d59b6d3b876c4d390d85f16ad`

## 1. Liczby z treści 6.B15 są nieaktualne — oto zmierzone dziś

Blok zadania podawał **73 moduły, 33 z frazą „kontrola negatywna"**. Oba pomiary są
sprzed kilku godzin i już nieprawdziwe:

| polecenie | z treści zadania | zmierzone dziś (045730b) |
|---|---|---|
| `ls tools/tests/test_*.py \| wc -l` | 73 | **80** |
| `grep -rlEi "kontrola negatywna" tools/tests/test_*.py \| wc -l` | 33 | **34** |

Siedem modułów doszło od czasu tamtego pomiaru (nowe testy T-xxx w tej samej sesji).

## 2. Kryterium leksykalne ma dziurę, którą złapałem na sobie

Polecenie weryfikacji z zadania szuka dokładnie stringu `"kontrola negatywna"`
(mianownik, liczba pojedyncza). Polski odmienia: „kontrol**ę** negatywn**ą**",
„kontrol**i** negatywn**ej**", „kontrol**e** negatywn**e**", „**kontrole** negatywne
**dwie**". Rozszerzony wzorzec `kontrol\w*\s+negatywn\w*` (dowolna odmiana obu słów)
znajduje **trzy dodatkowe moduły**, których dosłowny string zadania NIE widzi:
`test_m7_report.py`, `test_next_task.py`, `test_readme_claims.py` — wszystkie trzy
mają w środku genuine, wykonane kontrole negatywne, tylko nazwane w innym przypadku
(„Kontrol**e** negatywn**e** parserów", „Punkt wyjścia dla wszystkich kontroli
negatywnych niżej").

To jest dokładnie ta rodzina usterki, przed którą ostrzega zadanie: **kryterium
leksykalne myli się w obie strony**. Poniższy pomiar używa więc DWÓCH sit:

1. **fraza (odmiana dowolna)** — `grep -rlEi "kontrol\w*\s+negatywn\w*"`,
2. **struktura** — dla modułów bez frazy: czytanie nazw `def test_*` i ciał testów
   pod kątem wzorca „zbudowane/spotkane złe wejście → assercja, że zostało złapane,
   odrzucone, albo że wartość świadomie ZOSTAŁA pusta/nieznana" (`rejects`, `refuses`,
   `catches`, `is_an_error`, `stays_empty`, `stays_unknown`, `is False`,
   `raise AssertionError`, `assert not …`, itd. — zestaw szerszy niż jedno słowo,
   bo pojedyncze słowo kluczowe też myli, co pokazuje §4).

**Gdzie to kryterium może dalej zawodzić:** structural-grep to przybliżenie na
nazwach i słowach-kluczach, nie dowód semantyczny. Dwa moduły niżej (§5) pokazują
to wprost: `test_platform_dimensions.py` przeszedł drugie czytanie dopiero po tym,
jak zawiodło pierwsze (słowo-klucz nie złapało wzorca „stays_empty/stays_untouched").
Nie czytałem każdego z 80 modułów w pełni — dla ok. 40 z nich opieram się na nazwach
`def test_*` plus próbkowym czytaniu ciał (opisane w §3), nie na pełnym przeglądzie
każdej linii.

## 3. Metoda i wynik: 80 modułów, trzy kategorie, zero bez odpowiedzi

`bash doctor.sh --no-tests` (na tym środowisku): brak `dotnet`, brak `blender`,
brak `godot` — wszystkie trzy WARN/BRAK. Mimo to `python3 tools/tests/test_all.py`
(1710/1710, patrz §6) przechodzi **w całości, bez ani jednego `SKIP`** — potwierdzone
przez `grep -E "^\s*SKIP "` na pełnym wyjściu (zero trafień). Sprawdziłem też, które
moduły w ogóle odwołują się do `BLENDER_BIN`/`GODOT_BIN`/`DOTNET_BIN`/`subprocess`
wołający któreś z tych narzędzi (`test_ci_workflows.py`, `test_dotnet_version.py`)
— obie wołają WYŁĄCZNIE atrapy (fałszywe binarki podstawione przez `env=`), nie
prawdziwy Blender/Godot/.NET. **Wniosek: żaden z 80 modułów nie potrzebuje
niedostępnego tu narzędzia, więc kategoria „niewykonalna w tym środowisku" jest
dziś pusta.** To jest wynik pomiaru, nie założenie — stąd zerowa pozycja w tabeli
niżej.

| kategoria | liczba | kryterium |
|---|---|---|
| **wykonana i zapisana — fraza** | 38 | zawiera odmienioną frazę „kontrola negatywna" (§2), a próbkowe czytanie (8 z 38) potwierdza, że fraza opisuje NAPRAWDĘ wykonaną kontrolę, nie samo wspomnienie |
| **wykonana i zapisana — bez frazy** | 40 | brak frazy, ale struktura/treść testu pokazuje zbudowane złe/brakujące wejście i assercję, że zostało złapane albo świadomie zostawione puste |
| **niepotrzebna** | 2 | moduł sam deklaruje (i mutation-triage to potwierdza), że kontrola negatywna DLA TYCH SAMYCH funkcji leży w module siostrzanym |
| **niewykonalna w tym środowisku** | 0 | zmierzone — patrz akapit wyżej |
| **SUMA** | **80** | = `ls tools/tests/test_*.py \| wc -l` |

Żaden z 80 nie został bez odpowiedzi — pełna lista niżej.

### 3a. Wykonana i zapisana — fraza (38)

`test_backlog.py`, `test_braking.py`, `test_ci_workflows.py`, `test_clearance.py`,
`test_clearance_profile.py`, `test_crosscheck_alignment.py`, `test_crs.py`,
`test_detail_layout.py`, `test_dimension_audit.py`, `test_docs_ci_claims.py`,
`test_dotnet_version.py`, `test_engine_version.py`, `test_godot_warning_gate.py`,
`test_inspire_rail.py`, `test_line_calls_gate.py`, `test_line_trace_gate.py`,
`test_lod.py`, `test_m7_report.py`, `test_make_test_track.py`,
`test_mutation_sweep.py`, `test_next_task.py`, `test_pr_template.py`,
`test_readme_claims.py`, `test_render_engine.py`, `test_report_claims.py`,
`test_report_hygiene.py`, `test_schedule_envelope.py`, `test_shot_metadata_gate.py`,
`test_station_components.py`, `test_station_layout.py`, `test_surface_sections.py`,
`test_t401_citation.py`, `test_tunnel_width.py`, `test_validate_axis.py`,
`test_vehicle_fit.py`, `test_visual.py`, `test_visual_gates.py`,
`test_streaming_fixture.py` (dopisana dziś, patrz §5).

Próbka wykonanego czytania (8 z 38, w tym trzy znalezione tylko dzięki odmianie
z §2): `test_readme_claims.py` (`test_parsers_reject_a_mismatch` — sześć par
pozytyw/negatyw na każdym parserze), `test_backlog.py`, `test_ci_workflows.py`,
`test_mutation_sweep.py`, `test_dotnet_version.py`, `test_lod.py`,
`test_m7_report.py`, `test_next_task.py` — we wszystkich ośmiu fraza opisuje
faktyczny, zbudowany zły przypadek z assercją na wyniku, nie samo wspomnienie
słowa. Pozostałych 30 NIE czytałem w pełni — to jest miejsce, gdzie kryterium
frazowe może się mylić w drugą stronę (fraza jest, ale kontrola słaba); nie znalazłem
takiego przypadku, ale też go celowo nie szukałem poza tą ośemką.

### 3b. Wykonana i zapisana — bez frazy (40)

`test_alignment.py`, `test_all.py`, `test_architecture_doc.py`,
`test_art_direction.py`, `test_assertion_gate.py`, `test_audio_rights.py`,
`test_axis_claims.py`, `test_blender_cli.py`, `test_camera_aim.py`,
`test_capture_plan.py`, `test_chunks.py`, `test_crs_convergence.py`,
`test_data_freshness.py`, `test_detail_markers.py`, `test_fetchers.py`,
`test_glb_report.py`, `test_gtfs_stops.py`, `test_lod_paths.py`, `test_m7_shell.py`,
`test_material_specs.py`, `test_network_chainage.py`, `test_packages.py`,
`test_parameter_boundaries.py`, `test_placement.py`, `test_platform_dimensions.py`,
`test_platform_length_in_pipeline.py`, `test_png_pixels.py`, `test_profile_scan.py`,
`test_reference_snapshot.py`, `test_rights_matrix.py`, `test_scan_gates.py`,
`test_snapshot_source.py`, `test_station_kit.py`, `test_stations.py`, `test_sweep.py`,
`test_timetable.py`, `test_tuning_constants.py`, `test_tunnel_manifest.py`,
`test_visual_identical_pixels.py`, `test_xml_doc_blocks.py`.

Przykłady wykonanego czytania ciał testów (nie tylko nazw), z konkretnym miejscem:

- `test_data_freshness.py:85` `test_freshness_strict_mode_fails_only_on_expired` —
  buduje przeterminowane okno, woła `DF.main(...)` w trybie strict i łapie
  wyjątek przez `pytest`-owe `raises`-podobne `try/except`, sprawdzając treść
  komunikatu; osobno dowodzi, że BEZ przeterminowania zwraca `0`.
- `tools/tests/test_png_pixels.py:61,75` — dwa testy jawnie
  `raise AssertionError("plik bez nagłówka PNG przeszedł")` /
  `"PNG bez IDAT przeszedł"` wewnątrz `try/except`, czyli odwrócona asercja:
  test SAM PADA, jeśli funkcja pod testem NIE odrzuciła złego pliku.
- `test_visual_identical_pixels.py:82-100`
  `test_jeden_inny_piksel_zapala_bramke_mimo_ze_progi_go_przepuszczaja` — dosłownie
  „jeden inny piksel zapala bramkę, mimo że progi go przepuszczają": jeden przebieg
  daje `status="pass"`, drugi (ta sama różnica, ale żądanie zgodności co do bajtu)
  daje `status="fail"` i `identical_pixels is False`.
- `test_lod_paths.py` — `is_base_level(1) is False`, `is_base_level(2) is False`:
  dowód na gałąź negatywną prostej funkcji boolowskiej, nie tylko na `True`.
- `test_platform_dimensions.py` (patrz §5.1) — `test_schuman_stays_empty_because…`
  i `test_stations_the_eie_does_not_mention_stay_untouched`: to jest negatywna
  kontrola w drugą stronę — dowód, że rejestr ŚWIADOMIE NIE wypełnia pola, którego
  nie wolno mu zgadywać. Struktural-grep na słowach `reject/refuse/catch` tego nie
  widział; znalazłem to dopiero przy pełnym czytaniu pliku (patrz §5.1) — jawny
  przykład fałszywego negatywu opisanego w §2.
- `test_architecture_doc.py:98,109,127` — trzy `assert not <lista_rozbieżności>`
  (katalog wymyślony, katalog pominięty, artefakt budowy zażądany) — buduje
  faktyczne zbiory różnic i sprawdza ich pustość, nie samą obecność funkcji.

## 4. Dwa moduły „niepotrzebna" — i dlaczego to nie jest wymówka

**`test_marker_gates.py`.** Własny docstring modułu mówi wprost: „Ten plik nie
zamyka więc żadnej dziury (…) daje modułowi jeden test, który importuje go PO
NAZWIE, zamiast wyłącznie przez alias". `detail_markers.py` przypisuje
`clearance_problems = marker_gates.clearance_problems` (**ten sam obiekt funkcji**),
a `reports/mutation-triage-round-2-modules.md` §2 mierzy: wszystkie 9 mutacji tego
modułu ginie przez `test_detail_markers.py::test_zero_clearance_is_still_allowed_
but_a_hair_below_is_not` (ten test JEST kontrolą negatywną — `clearance_problems`
wołane dokładnie na granicy 0.0 i tuż pod nią). `test_marker_gates.py` sam niesie
tylko dwa testy „tuż pod milimetrem NIE jest problemem" (obie strony pozytywne)
i jeden test tożsamości obiektu — zero kontroli negatywnej WŁASNEJ, bo taka
istnieje już gdzie indziej i jest zmierzona.

**`test_station_sections.py`.** Ten sam wzorzec, ten sam commit-źródło
(`reports/mutation-triage-round-2-modules.md`, „9 z 15 mutacji ginie przez
`test_station_kit.py`"). Docstring: „Czego ten plik świadomie NIE dubluje" —
pięć z sześciu funkcji to alias tego samego obiektu, który testuje
`test_station_kit.py`; ten plik pokrywa wyłącznie `straight_prism` (funkcja bez
ŻADNEGO pośredniego pokrycia) i granicę `side == 0.0` w `slab_sections` — obie
ścieżki to **poprawne dane brzegowe**, nie złe wejście („zerowa długość nie
podnosi wyjątku, tylko daje zdegenerowaną bryłę" — to zamierzone zachowanie,
nie usterka do złapania). Kontrola negatywna dla aliasowanych funkcji
(`side` różne od `0`, `1`, `-1` itd.) leży w `test_station_kit.py` i jest
zmierzona tym samym raportem.

Obu **nie dopisałem** nic — dopisanie tu zdublowałoby kontrolę, która już
istnieje i jest zmierzona gdzie indziej, a zadanie wprost zabrania pisania nowych
bramek. Weryfikowalne bez czytania mojej oceny: `reports/mutation-triage-round-2-modules.md`.

## 5. Jedna kontrola dopisana — `test_streaming_fixture.py`

### 5.1 Dlaczego akurat ten, a nie `test_platform_dimensions.py`

Oba trafiły najpierw do „zero trafień" na pierwszym, węższym zestawie słów
kluczowych. Po pełnym przeczytaniu `test_platform_dimensions.py` okazało się, że
DWA jego testy (`test_schuman_stays_empty_because_two_official_sources_disagree`,
`test_stations_the_eie_does_not_mention_stay_untouched`) SĄ kontrolą negatywną —
dowodzą, że rejestr świadomie zostawia pole puste tam, gdzie źródła się kłócą albo
milczą, zamiast zgadywać. To przeniosło go do §3b.

`test_streaming_fixture.py` po tym samym czytaniu **naprawdę nic takiego nie miał**.
Własny akapit modułu ostrzega dosłownie: „Rozjazd między nimi [Pythonem i C#] nie
wywala niczego (…) i to wszystko" — moduł sam nazywa swoje ryzyko, ale żaden test
w nim nie sprawdzał, czy porównanie `assert resident == row["resident"]` (i
analogiczne dla okna, LOD, kolizji) w ogóle **potrafi** wykryć rozjazd, czy
zawsze przechodzi, bo oba źródła liczą to samo, tą samą ścieżką kodu. Dokładnie
taki był stan wyroczni mutacyjnej przed #268 (`reports/wyrocznia-mutacyjna-falszywe-zabicia.md`):
zielona, bo zepsuta.

### 5.2 Co dopisałem i jak to zweryfikowałem

Nowy test `test_a_planted_mismatch_in_the_fixture_actually_fails_the_comparison`
w `tools/tests/test_streaming_fixture.py`: bierze wiersz 0 wzorca, w PAMIĘCI (plik
na dysku nietknięty) dopisuje mu do `resident` chunk, którego pociąg naprawdę nie
ma na pokładzie, i sprawdza, że dokładnie ta sama pętla porównania co w
`test_python_reference_still_produces_every_row_of_the_fixture` to łapie.

**Kontrola negatywna kontroli negatywnej — wykonana osobno, przed commitem:**
podmieniłem `real_resident + ["ŻADEN_TAKI_CHUNK"]` na samo `real_resident`
(czyli usunąłem psucie) w kopii modułu wczytanej w pamięci i uruchomiłem nowy test:

```
OK - sabotowana wersja pada, jak powinna: porównanie NIE złapało dopisanego
chunku — pętla z testu wyżej jest bezzębna
```

Czyli: bez psucia nowy test SAM siebie łapie na tym, że nie miałby czego mierzyć
(pada z czytelnym komunikatem) — nowy test nie jest wpisany na sztywno pod jeden
wynik. Z prawdziwym psuciem (wersja, która trafiła do commita) test przechodzi:

```
checks: 3
OK - nowy test przeszedł i coś zasercjonował
```

## 6. Rzeczywiste wyjście weryfikacji (po dopisaniu testu, na drzewie roboczym)

```
$ python3 tools/tests/test_all.py 2>&1 | tail -5
  ok   test_every_summary_is_closed_in_its_own_block
  ok   test_no_member_carries_two_summary_blocks
  ok   test_xml_doc_scan_actually_reads_the_sources

  1710/1710 przeszło
ZIELONE

$ grep -rlEi "kontrola negatywna" tools/tests/test_*.py | wc -l
35
$ ls tools/tests/test_*.py | wc -l
80
```

1709 → **1710** (jeden nowy test), fraza dosłowna 34 → **35** (nowy test ją niesie),
wersja odmieniona 37 → **38**.

## 7. Świadomie nietknięte — do zrobienia osobno

- **`test_xml_doc_blocks.py`** ma słowa-strażniki przeciw pustemu skanowi
  (`test_xml_doc_scan_actually_reads_the_sources`), ale żaden test nie WSTRZYKUJE
  sztucznie zdublowanego/urwanego `<summary>` — oba testy detekcji
  (`test_no_member_carries_two_summary_blocks`,
  `test_every_summary_is_closed_in_its_own_block`) działają dziś na PRAWDZIWYM,
  aktualnie czystym `src/`, więc przechodzą również wtedy, gdyby licznik
  `<summary>`/`</summary>` miał błąd, którego żaden dzisiejszy plik nie ujawnia.
  Naprawa jest tania (dwa stringi C# zbudowane w locie, bez plików na dysku) —
  nie zrobiłem jej tylko dlatego, że jeden dopisany test na sesję to świadomy
  wybór z promptu („nie próbuj domknąć wszystkiego"), nie brak możliwości.
- **30 z 38 modułów w §3a** nie zostało przeczytanych w pełni, tylko sprawdzonych
  próbką ośmiu — jeśli któryś z pozostałych 30 ma frazę bez treści za nią, ten
  raport tego dziś nie łapie. Kandydatem do kontrolnego czytania w kolejnej
  sesji: moduły z jednym wystąpieniem frazy w pojedynczym zdaniu, bez przykładu
  liczb w treści (nie sprawdzałem, które to).
- **Kategoria „niewykonalna" wyszła pusta** — nie próbowałem tego obalić przez
  faktyczne wywołanie Blendera/Godota/.NET-a (i tak ich tu nie ma), tylko przez
  grep za wywołaniami; gdyby jakiś moduł wołał binarkę pośrednio (np. przez
  import modułu, który sam importuje `bpy` warunkowo), ten pomiar by tego nie
  złapał. `doctor.sh --no-tests` i pełny zielony przebieg `test_all.py` bez
  żadnego `SKIP` to jednak dowód mocniejszy niż grep za nazwą zmiennej.

## 8. Co zauważyłem obok, świadomie nietknięte

- `test_readme_claims.py` i `test_next_task.py` mają frazę tylko w formie
  odmienionej („Kontrole negatywne parserów", „kontroli negatywnych niżej") —
  dosłowna bramka z treści zadania (`grep -rlEi "kontrola negatywna"`) ich NIE
  widzi. Jeśli ktoś kiedyś postawi bramkę na liczbie 34/35 z §1, ten sam brak
  odmiany ją zmyli tak samo, jak zmylił blok zadania. Nie stawiam tu żadnej
  bramki (poza zakresem), tylko to zapisuję.
- `test_marker_gates.py` i `test_station_sections.py` (§4) to nie jedyne dwa
  moduły z rodziny „ekstrakcja spod `bpy`, alias na stare nazwy" — nie
  sprawdzałem systematycznie, czy są inne pary tego wzorca w `tools/tests/`
  poza tymi dwiema, które akurat wypadły w tym pomiarze na zero.
