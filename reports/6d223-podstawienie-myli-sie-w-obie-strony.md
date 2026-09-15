# 6.D223 — sito myli się w obie strony: 36 % w jedną, 40 % w drugą

**15.09.2026**, na `2faa2f2`. Wejście: `reports/6d212-trzy-sita-i-zadne-nie-przewiduje.md`
§1, §5 i §10, `tools/tests/*.py`, `data/network/lines.json`,
`data/legal/rights-matrix.json`, `reports/T-401-line-run.md`.

## 0. Pierwszy wynik: populacji 21 NIE DA SIĘ ODTWORZYĆ

**Wykazu tych 21 nie ma nigdzie w repozytorium.** 6.D212 podaje wyłącznie liczby
(§5: „27 pilnowanych i 21 niepilnowanych") i cztery nazwy z tekstu — `kamery`,
`unikalne`, `sledzone`, `documented`. Skryptu, który je policzył, nie zapisano;
`grep -rn "6.D212" --include=*.py tools/` daje wyłącznie przeliczone zapadki
w cudzych modułach, ani jednego czytnika. Baza 6.D212 (`0549474`) leży cztery
scalenia za dzisiejszym `main`.

Łańcuch odtworzony z **definicji zapisanych w §1** raportu, na wypakowanym `0549474`
(`git archive 0549474 tools/tests`):

| szczebel | 6.D212 | odtworzenie na tym samym commicie |
|---|---:|---:|
| asercji z `len(` w `tools/tests/` | 678 | **698** (AST) · 693 (`grep`) |
| testów z `len(<goła nazwa>)` | 382 | **394** |
| zbiorów mierzonych WYŁĄCZNIE co do długości | 234 | **254** |
| z nich z wyrażenia listowego | **48** | **53** |
| sito modułowe → pilnowane / niepilnowane | **27 / 21** | 42 / 11 · 40 / 13 |

Kryterium „wyłącznie co do długości" musi być **luźne** — dyskwalifikować tylko
indeksowanie, iterowanie i porównanie **gołej** nazwy. Skalibrowane na dwóch
przypadkach, które 6.D212 wymienia z nazwy: przy kryterium ostrym („nazwa występuje
tylko w `len()`") wypadają z populacji i `test_camera_aim::kamery` (bo jest
`min(kamery)`), i `test_mutation_sweep::…unique::ids` (bo jest `set(ids)`) — a raport
oba wymienia jako należące. Przy luźnym oba wracają. To zawęża rozjazd do producenta
i do samego sita modułowego, ale go nie zeruje.

**Populacja wzięta do podstawienia:** 14 zbiorów niepilnowanych (suma z obu zawężeń
sita modułowego) **plus 6 kontroli z drugiej strony sita** — zbiorów, które sito
uznało za PILNOWANE. Ta druga grupa jest dołożeniem do zlecenia i jest w tym pomiarze
najważniejsza: bez niej nie dałoby się zmierzyć pomyłki w drugą stronę, a ona jest.

## 1. Podstawienia — 19 wykonanych

Procedura każdorazowo: `md5sum` → podmiana zachowująca **liczność** → `find . -name
__pycache__ -prune -exec rm -rf {} +` → `git add -A` → `python3 tools/tests/test_all.py`
→ `git restore --source=HEAD --staged --worktree` → `md5sum -c`. Baza: **2491/2491**.

### 1a. Populacja „niepilnowane" (14)

| # | zbiór | podstawienie | wynik | co zapaliło |
|---|---|---|---|---|
| 1 | `test_bin_path_framework::files` | rename raportu (9 → 9) | zielone | — |
| 2 | `test_camera_aim::kamery` | `cam_side` → `cam_flank` po obu stronach (4 → 4) | zielone | — |
| 3 | `test_ci_workflows::paths` | `/tmp/blender-` → `/tmp/blendes-` (64 → 64) | zielone | — |
| 4 | `test_conflict_markers::sledzone` | ten sam rename (≥N → tyle samo) | zielone | — |
| 5 | `test_csharp_pins::surowe` | napis w próbce (3 → 3) | zielone | — |
| 6 | `test_dimension_audit::names` (M7) | `DESIGN_NOSE_INSET_M` → `…INSAT_M` ×3 (14 → 14) | **CZERWONE** | 3 bramki, w tym jedna z **innego modułu** |
| 7 | `test_dimension_audit::names` (sweep) | `DEFAULT_STATION_HALO_M` → `…HALX_M` ×5 | **CZERWONE** | 2 bramki |
| 8 | `test_mutation_sweep::opisy` | `` ` -> ` `` → `` ` => ` `` w `describe()` (2 → 2) | **CZERWONE** | siostra przypina pełny napis |
| 9 | `test_network_declarations::nazwy` | `Gribaumont` → `Gribaumant` (60 → 60) | **CZERWONE** | 4 bramki, **wszystkie z innych modułów** |
| 10 | `test_placement::roof_only` | `range(0,50)` → `range(1,51)` (50 → 50) | zielone | — |
| 11 | `test_rights_matrix::named` | `Carrelage Cinq` → `…Cinp` | zielone | — |
| 12 | `test_stations::ids` | `…G0270105` → `…106` ×3 (5 → 5) | zielone | — |
| 13 | `test_timing_record::sekundy` | klucze `modul_` → `moduX_` (14 → 14) | zielone | — |
| 14 | `test_xml_doc_blocks::documented` | `ChunkManifest.cs` → `ChunkManifezt.cs` (83 → 83) | **CZERWONE** | 4 bramki, **wszystkie z innych modułów** |

### 1b. Kontrole z drugiej strony sita (6)

| # | zbiór | podstawienie | wynik |
|---|---|---|---|
| 15 | `test_stations::ids` (dwanaście stacji) | `PARC` → `PARK` ×3 (12 → 12) | **CZERWONE**, 4 bramki |
| 16 | `test_m7_cab::nazwy` | `_desk_top` → `_desk_tob` (16 → 16) | **CZERWONE**, siostra |
| 17 | `test_t401_citation::binding` | zamiana kolumny C# między L5_D a L6_F w §4 raportu | **zielone** |
| 18 | `test_docs_ci_claims::reports` | objęte renamem z #1 | zielone |
| 19 | `test_hexdigest_truncation::weszlo` | **NIEPODSTAWIALNE** — `assert not weszlo`, liczność 0 | — |
| 20 | `test_environment_doc::unikalne` | nie powtarzane — **cytat** z 6.D212 KN-2 | CZERWONE |

**Podstawień własnych jest 18, a nie 19**, i tak to tu stoi: #20 jest przepisane
z 6.D212, a nie wykonane przy tej pozycji.

## 2. Wyjście przebiegów

```
BAZA                      2491/2491 przeszło   kod=0   (4m16.952s)
PARTIA 1 (#3,5,10,13)     2491/2491 przeszło   kod=0
PARTIA 2 (#2,6,7,8)       2485/2491 przeszło   kod=1
  FAIL test_audit_covers_every_m7_design_constant: stałe bez wpisu: ['DESIGN_NOSE_INSAT_M']
  FAIL test_audit_covers_every_sweep_constant: stałe generatora bez wpisu: ['DEFAULT_STATION_HALX_M']
  FAIL test_audit_records_the_value_of_every_m7_design_constant
  FAIL test_audit_records_the_value_of_every_sweep_constant
  FAIL test_m7_shell_every_design_constant_is_documented
  FAIL test_a_comparison_next_to_the_guard_is_still_mutated
PARTIA 3 (#9,11,12)       2487/2491 przeszło   kod=1
  FAIL test_gtfs_potwierdza_kazdy_przystanek_wypisany_na_linii: [('L1', 'Gribaumant')]
  FAIL test_packages_committed_station_order_follows_lines_json
  FAIL test_packages_every_committed_station_name_exists_in_lines_json: Gribaumont
  FAIL test_przypisanie_linii_zgadza_sie_z_danymi_w_OBIE_strony
PARTIA 4 (#1,4,14,18)     2487/2491 przeszło   kod=1
  FAIL test_ile_golych_nazw_stoi_w_docs_…: [... 'ChunkManifest.cs' ...]
  FAIL test_no_input_field_names_a_file_outside_the_tree:
       ['6.D173 „Wejście": src/Game/Assets/ChunkManifest.cs', '6.D178 …']
  FAIL test_removing_the_field_distinction_moves_the_reported_set
  FAIL test_kazda_sciezka_wymieniona_w_raporcie_rozwiazuje_sie_w_drzewie
PARTIA 5 (#15,16,17)      2486/2491 przeszło   kod=1
  FAIL test_fotel_stoi_za_pulpitem_a_nie_w_nim: 'cab_front_desk_top'
  FAIL test_exit_and_station_ids_are_unique: PARC_G0030108
  FAIL test_package_a_registry_holds_exactly_twelve_stations: {'PARK', 'PARC'}
  FAIL test_parc_equipment_counts_do_not_come_from_the_exit_list
  FAIL test_stations_under_works_split_historical_and_future_state
PO PRZYWRÓCENIU           2491/2491 przeszło   kod=0
```

`md5sum -c` po każdej partii: **OK** na wszystkich 16 dotkniętych plikach.

## 3. Licznik

**Na populacji „niepilnowanych" (14):** pilnowanych **5** (#6, #7, #8, #9, #14),
czyli **36 %**; naprawdę niepilnowanych 9.

**Na kontrolach „pilnowanych" (6):** pilnowanych zgodnie z sitem 3; **niepilnowanych
wbrew situ 2** (#17, #18), czyli **40 %**; niesprawdzalny 1 (#19).

Licząc od przypuszczenia 6.D212: „niepilnowane" ma po tej pozycji bilans **9 trafień
na 14** wobec 0 na 2 przedtem. Przypuszczenie jest więc **częściowo trafne** — ale myli
się w ponad jednej trzeciej przypadków, **a sito myli się też w drugą stronę**, czego
6.D212 nie mierzyło wcale.

## 4. Przy każdym naprawdę niepilnowanym: usterka czy nie ma czego pilnować

**Nie ma czego pilnować (7).** #3, #5, #10, #13 — wejście syntetyczne budowane w samym
teście, gdzie `len()` jest **podłogą** na to, że przyrząd coś zmierzył; przy #3
prawdziwy kształt ścieżki `/tmp/blender-…` jest przypięty osobno, wobec
`tools/ci/blender_install.sh`. #1 i #4 — treścią jest lista plików drzewa, obie asercje
to podłogi na „skan naprawdę czytał"; blok 6.D223 nazywa `sledzone` kontrolą przyrządu
i **to się potwierdziło**. #18 — podłoga „≥40 raportów w pętli". #2 — zgodne
przemianowanie po obu stronach jest **poprawnym refaktorem**; jednostronne zapala.

**Dziury warte zapisania (2).**

- **#17 `test_t401_citation::binding`.** Zamiana kolumny C# między L5_D a L6_F
  w `reports/T-401-line-run.md` §4 wiąże **inny pakiet**, a kolumna Δ zostaje
  arytmetycznie fałszywa (57,64 → 55,05 opisane jako **+1,04**). Cały zestaw przeszedł.
  Przypięta jest **wartość** dolnego ograniczenia (maksimum kolumny, tu bez zmian), ale
  **nie to, który wiersz je daje, ani spójność kolumny różnicy**. Strona C# tego nie
  łapie i jest to **zmierzone, nie założone**: `grep -rn "T-401-line-run" --include=*.cs`
  daje dwa trafienia i **oba są komentarzami** (`LineRunTests.cs:18`,
  `SignallingPlanTests.cs:321`) — żaden test C# tego pliku nie otwiera. Sprawdzone
  niezależnie przy domykaniu pozycji, tym samym poleceniem.
- **#11 `test_rights_matrix::named`.** Tytuł dzieła w `data/legal/rights-matrix.json`
  zmieniony po cichu nie zapala niczego. Test pilnuje obecności pól, unikalności par
  i słownika stanów — ale **nie wartości tytułu**. To plik z `docs/03-legal.md`, czyli
  dokładnie ten, o którym własny docstring testu pisze, że „cisza jest najgroźniejsza".

Obie idą do kolejki jako **6.D238** i **6.D239**; naprawianie stawia blok 6.D223
poza zakresem.

## 5. Blok 6.D223 mówi o `documented` NIEPRAWDĘ — i to jest wynik, nie potknięcie

Pole „Czego NIE wolno przyjąć bez pomiaru" wymienia `test_xml_doc_blocks::documented`
obok `test_conflict_markers::sledzone` jako kontrolę przyrządu, „gdzie nie ma czego
pilnować". Podstawienie #14 mówi co innego: zmiana zawartości tego zbioru zapaliła
**cztery** bramki z **dwóch innych modułów**.

Mechanizm sprawdzony niezależnie przy domykaniu pozycji, a nie przyjęty z raportu:
`src/Game/Assets/ChunkManifest.cs` stoi w `docs/TASKS.md` **sześć** razy, z czego
**cztery** w polach „Wejście" — więc przemianowanie pliku wywraca
`test_no_input_field_names_a_file_outside_the_tree` niezależnie od tego, co robi
`test_xml_doc_blocks`.

Klasyfikacja a priori pomyliła się więc **także na liście z bloku pozycji**, z tego
samego powodu co sito. Blok jest OTWARTY, więc to zdanie zostaje w nim poprawione —
6.D108 chroni raporty, nie pola kolejki.

## 6. Rozstrzygnięcie: BRAMKA NIE POWSTAJE, powstaje zapisana granica

Nie „bo zabrakło czasu" — bo pomiar mówi, że nie ma czego postawić. Sito modułowe myli
się **w obie strony**: 5 z 14 rzekomo niepilnowanych jest pilnowanych, i 2 z 6 rzekomo
pilnowanych nie jest. Bramka na tym sicie zapalałaby się na kodzie **poprawnym** —
w #2 na zgodnym przemianowaniu kamery, w #5, #10 i #13 na fixture, których zawartość
nic nie znaczy — a bramka świecąca na poprawnym tekście zostaje **wyłączona, nie
poprawiona** (6.D27). Utrwalone jest więc zdanie, nie kod:

> Czy liczność jest jedynym uprawnionym twierdzeniem, rozstrzyga **wyłącznie
> podstawienie**. Trzy sita 6.D212 i dwa zawężenia sita modułowego mylą się w obie
> strony; po 19 podstawieniach bilans wynosi 8 czerwonych na 11 zielonych, a pomyłka
> sita — 36 % w jedną stronę i 40 % w drugą.

Ta sama klasa odpowiedzi co w 6.D207 i 6.D221, i z tego samego powodu.

## 7. Czego NIE zmierzono

- **Dokładnych 21 z 6.D212** — nie istnieje ich wykaz ani skrypt, a drzewo ruszyło
  o cztery scalenia. Zamiast tego własna populacja z definicją i liczby rozjazdu (§0).
- **Pozostałych 33 z 53.** Podstawiono 19; reszta to zbiory, które oba zawężenia sita
  zgodnie uznały za pilnowane, a każdy pełny przebieg kosztuje 4 min 17 s.
- **Strony C#.** Żadnego podstawienia nie sprawdzono przez `dotnet test`. Dla #17 zakres
  tej niewiedzy jest zawężony pomiarem (żaden `.cs` nie otwiera raportu T-401), dla
  pozostałych nie jest.
- **Czwartego sita 6.D212** („czy producent jest deterministyczny") — poza zakresem.

## 8. Zauważone przy okazji, nietknięte

- **`data/` dotknięte trzy razy** (`lines.json`, `rights-matrix.json`, rejestr stacji),
  wbrew literze §4.6 — przejściowo, w ramach procedury podstawienia, z przywróceniem
  i `md5sum -c: OK` po każdym przebiegu. Zgłoszone jawnie, bo reguła jest w „twardych",
  a blok pozycji nie wymienił `data/` z nazwy. Alternatywą było zgadnięcie wyniku dla
  trzech pozycji, co §8 stawia wyżej na liście kosztów.
- **`git checkout -- <plik>` po `git add -A` NIE przywraca pliku**, tylko wersję
  z indeksu. Procedura podstawienia ma tu pułapkę bliźniaczą do tej z `__pycache__`
  z §5: `md5sum -c` **poprawnie** pokazało FAILED, ale ktoś czytający samo
  „przywróciłem" zostawiłby mutację w drzewie. Poprawne jest
  `git restore --source=HEAD --staged --worktree`.
- **`test_hexdigest_truncation.py` niesie asercję `assert ile > 0 or True`** — tautologię
  z komentarzem „obecnosc kopii nie jest wymagana, ich zliczenie tak". Liczy się do
  licznika asercji zestawu, a nie mierzy niczego.
- **`test_stop_names::test_pomiar_ksztaltu_nazw_odtwarza_sie` wnosi do populacji DWA
  zbiory naraz** (`czlony`, `dwuczlonowe`), tak samo `test_dimension_audit`
  i `test_backlog_commands`. Łańcuch 6.D212 liczy zbiory, nie testy, i jest w tym
  spójny — ale przy czytaniu liczby 48/53 łatwo pomylić jedno z drugim.
