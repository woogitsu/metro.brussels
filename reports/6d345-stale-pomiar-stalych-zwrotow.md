# 6.D345 · Trzynaście funkcji ma tylko zwroty stałe; mieszanych jest siedemdziesiąt trzy

**Data pomiaru:** 25.09.2026. **Drzewo bazowe:** `0d5332353d383fa4a984a0842032bca5d6c1e983` (main po #799). **Przyrząd:** `tools/tests/constant_returns.sh`.

## 1. Co dokładnie policzono

Przyrząd pożycza `tree_walk.znajdz`, bierze pliki `*.py` bezpośrednio z
`tools/tests/`, funkcje modułowe poza `test_*` i `main`, a następnie ogląda ich
własne `return`/`yield` bez zwrotów funkcji zagnieżdżonych. W populacji zostają
funkcje z co najmniej jednym jawnym `return` o wartości `ast.Constant` albo
gołym `return` (implicit `None`). Nie zgaduje wartości wywołań ani nazw.

To **nowy, jawny census syntaktyczny**, a nie odtworzony klasyfikator 6.D315/326.
Tamten nie trafił do drzewa jako kod. Już 6.D326 §2 zanotowało, że jego populacja
961 różniła się od wcześniejszych 439, a klasa nierozstrzygnięta 428 od 140.
Dlatego 204 funkcje i 100 zwrotów z 6.D336 są **historycznym pomiarem innej
populacji**, a nie mianownikiem, do którego dopasowuję nowy skan.

## 2. Cztery liczby i kontrola sumy

| rozłączna klasa w bieżącym censusie | funkcje |
|---|---:|
| tylko stałe inne niż przypadek „wyłącznie `None`” | **12** |
| wyłącznie `None` | **1** |
| stała obok innego wyrażenia zwrotu, `yield` albo stałej innego rodzaju | **73** |
| **suma: funkcje z co najmniej jednym zwrotem stałej** | **86** |

Przyrząd naliczył **138 zwrotów stałej** w tych 86 funkcjach. Kontrola przyrządu
ma wartość `12 + 1 + 73 = 86` i jest sprawdzana asercją. Druga kontrola na
wejściu syntetycznym sprawdza, że `return None` obok `return []` wpada do
**mieszanych**, a nie do „tylko stałe”.

Gdyby pojedyncza klauzula rozpoznawała **kształt każdego rodzaju stałej**
(napis, bool, `None`) i wymagała jednakowego kształtu wszystkich zwrotów danej
funkcji, ten podzbiór zmniejszyłby się o **13**: dwanaście funkcji zwraca wyłącznie
wartości jednego rodzaju (`str` albo `bool`), jedna wyłącznie `None`.
W pozostałych 73 nadal stoi przynajmniej inne wyrażenie, więc jedna taka klauzula
nie wystarcza do przypisania kształtu całej funkcji. **To jest skutek dla
odtwarzalnego podzbioru 86, nie dowód, że historyczna klasa 204 zmalałaby
o 13.** Zbieżność z pochodną liczbą 13 z 6.D336 §6 nie przywraca brakującego
historycznego klasyfikatora.

## 3. Lista imienna mieszających

Kolumna po nazwie podaje liczbę zwrotów stałej oraz typy pozostałych wyrażeń
AST. `Name`, `Call` i `IfExp` są **nierozstrzygnięte co do wartości**; samo
współwystąpienie składni nie dowodzi różnego kształtu wartości. Bezpośrednie
`List` i `DictComp` pokazują m.in. przypadki, których nie wolno domknąć samym
`return None`.

```text
mixed	tools/tests/assertion_gate.py:97:_is_assertion_raise	constants=1	other=Compare
mixed	tools/tests/backlog_commands.py:97:verification_field	constants=1	other=IfExp
mixed	tools/tests/mutation_sweep.py:504:brudne_wyjasnienie	constants=2	other=BinOp
mixed	tools/tests/mutation_sweep.py:637:neutralise_own_tests	constants=1	other=Name
mixed	tools/tests/mutation_sweep.py:675:coverage_map	constants=2	other=Name
mixed	tools/tests/mutation_sweep.py:944:wczytaj_pokrycie	constants=5	other=DictComp
mixed	tools/tests/mutation_sweep.py:969:was_executed	constants=1	other=Compare
mixed	tools/tests/mutation_sweep.py:1037:baseline_problem	constants=1	other=JoinedStr,JoinedStr
mixed	tools/tests/mutation_sweep.py:1073:bajtkod_przykrywa_zrodlo	constants=4	other=BoolOp
mixed	tools/tests/mutation_sweep.py:1202:odcisk_przebiegu	constants=1	other=Subscript
mixed	tools/tests/test_assertion_gate.py:214:komunikat_nic_nie_mowi	constants=2	other=UnaryOp,BoolOp,UnaryOp
mixed	tools/tests/test_assertion_gate.py:244:asercje_bez_komunikatu	constants=1	other=Call
mixed	tools/tests/test_assertion_gate.py:751:_funkcja	constants=1	other=Name
mixed	tools/tests/test_audio_rights.py:144:_zgodny_typ	constants=1	other=Call
mixed	tools/tests/test_backlog.py:665:_section	constants=1	other=IfExp
mixed	tools/tests/test_backlog.py:755:pole_zaleznosci	constants=1	other=Call
mixed	tools/tests/test_ci_workflows.py:990:_paths_block	constants=1	other=Call
mixed	tools/tests/test_ci_workflows.py:1376:_runner_labels	constants=1	other=List,ListComp,Name,List
mixed	tools/tests/test_ci_workflows.py:1412:_runner_mismatch	constants=2	other=JoinedStr
mixed	tools/tests/test_ci_workflows.py:1495:_concurrency_fault	constants=1	other=JoinedStr,JoinedStr
mixed	tools/tests/test_ci_workflows.py:3913:_prawdziwy_elf_bez_biblioteki	constants=2	other=Tuple
mixed	tools/tests/test_ci_workflows.py:4024:bezwarunkowy_na_pull_request	constants=2	other=UnaryOp
mixed	tools/tests/test_csharp_test_methods.py:284:_sam_literal	constants=3	other=Name
mixed	tools/tests/test_dead_constants.py:72:_drzewo	constants=1	other=Call
mixed	tools/tests/test_digit_boundaries.py:89:_dopasowuje_cyfre	constants=2	other=Compare,BoolOp,Compare
mixed	tools/tests/test_digit_boundaries.py:120:_nazwa_wywolania	constants=1	other=IfExp,Attribute
mixed	tools/tests/test_dimension_audit.py:109:_row	constants=1	other=ListComp
mixed	tools/tests/test_docs_ci_claims.py:128:runner_labels	constants=1	other=List,ListComp,Name,List
mixed	tools/tests/test_docs_ci_claims.py:206:_looks_like_a_label	constants=1	other=BoolOp
mixed	tools/tests/test_dotnet_version.py:60:tfm_major	constants=1	other=IfExp
mixed	tools/tests/test_dotnet_version.py:137:pin_sdk	constants=1	other=Call
mixed	tools/tests/test_engine_version.py:104:minor	constants=1	other=IfExp
mixed	tools/tests/test_engine_version.py:181:cialo_sondy	constants=1	other=Call
mixed	tools/tests/test_field_paths.py:216:field_body	constants=1	other=IfExp
mixed	tools/tests/test_field_paths.py:275:accepted	constants=2	other=BoolOp
mixed	tools/tests/test_field_paths.py:390:_argparse_options	constants=1	other=Name
mixed	tools/tests/test_game_needle_specificity.py:379:_zamkniecie	constants=1	other=Name
mixed	tools/tests/test_game_needle_specificity.py:414:_igla_z_argumentu	constants=2	other=Call
mixed	tools/tests/test_gtfs_stops.py:28:_csv	constants=1	other=Call
mixed	tools/tests/test_hexdigest_truncation.py:127:_akapit_nad	constants=1	other=Call
mixed	tools/tests/test_message_claims.py:264:_docstring_wezel	constants=2	other=Attribute
mixed	tools/tests/test_message_claims.py:1089:_klasa_wierszy	constants=1	other=IfExp
mixed	tools/tests/test_message_claims.py:1676:_dokad_plynie	constants=10	other=Call
mixed	tools/tests/test_message_claims.py:1725:_przez_nazwe	constants=1	other=IfExp
mixed	tools/tests/test_module_entrypoints.py:92:_liczba_testow	constants=1	other=Call
mixed	tools/tests/test_network_declarations.py:63:_gtfs_routes	constants=1	other=Name
mixed	tools/tests/test_next_task.py:348:_akapit_kolejki	constants=1	other=Subscript
mixed	tools/tests/test_packages.py:42:_axis	constants=1	other=Call
mixed	tools/tests/test_packages.py:50:_provenance	constants=1	other=Call
mixed	tools/tests/test_pr_template.py:20:closing_keyword	constants=1	other=IfExp
mixed	tools/tests/test_readme_claims.py:104:ci_list_paragraph	constants=1	other=IfExp
mixed	tools/tests/test_readme_claims.py:113:readme_workflow_count	constants=1	other=Call
mixed	tools/tests/test_readme_claims.py:203:wezly_skladu_w_scenie	constants=1	other=Call
mixed	tools/tests/test_readme_claims.py:366:punkt_tekst	constants=1	other=BinOp
mixed	tools/tests/test_readme_claims.py:380:liczba_z_readme	constants=1	other=Call,Call
mixed	tools/tests/test_reference_snapshot.py:102:rozruch_z_dokumentu	constants=1	other=DictComp
mixed	tools/tests/test_report_claims.py:128:_same_number	constants=1	other=Compare
mixed	tools/tests/test_report_claims.py:214:_data	constants=1	other=IfExp
mixed	tools/tests/test_report_claims.py:363:data_z_commita	constants=2	other=IfExp
mixed	tools/tests/test_report_claims.py:382:data_stalej	constants=1	other=Name,Subscript
mixed	tools/tests/test_report_hygiene.py:1366:_header_field_line	constants=1	other=Call
mixed	tools/tests/test_run_mode_claims.py:71:header_mode_count	constants=1	other=Call
mixed	tools/tests/test_runner_number_parsing.py:106:metoda_dla_wiersza	constants=1	other=Call
mixed	tools/tests/test_suite_runtime_budget.py:1814:_stala_w_module	constants=1	other=Attribute
mixed	tools/tests/test_suite_runtime_budget.py:1827:_ksztalt_literalu	constants=2	other=Name,Name,IfExp,Name
mixed	tools/tests/test_t401_citation.py:106:_units	constants=1	other=
mixed	tools/tests/test_timing_record.py:47:_krok_zestawu	constants=1	other=Name
mixed	tools/tests/test_timing_record.py:54:_krok_artefaktu	constants=1	other=Name
mixed	tools/tests/test_tree_walks.py:98:polaryzacja_porownania	constants=4	other=IfExp,UnaryOp,Name
mixed	tools/tests/test_tree_writes.py:168:_tryb_zapisu	constants=1	other=Name
mixed	tools/tests/test_tree_writes.py:244:_cel_kopiowania	constants=3	other=Tuple,Tuple,Tuple
mixed	tools/tests/test_value_chains.py:150:dawna_wartosc	constants=1	other=Tuple
mixed	tools/tests/test_visual.py:762:_raises	constants=1	other=Name
```

## 4. Lista trzynastu kandydatów do zdjęcia

```text
assertion_gate.py:suite_verdict                 str
mutation_sweep.py:usun_bajtkod                bool
test_audio_rights.py:warunek_zachodzi         bool
test_ci_workflows.py:_sonda_pyta_o_sonames      bool
test_ci_workflows.py:_reaches_dotnet           bool
test_commit_claims.py:zglasza_wykonana_kontrole bool
test_data_thresholds.py:_podnosi_wyjatek       bool
test_data_thresholds.py:_zasila_liste          bool
test_fetchers.py:_refuses                    None
test_message_claims.py:_ma_licznik_z_calosci  bool
test_module_entrypoints.py:ma_straznik         bool
test_mutation_sweep.py:_bpy_na_poziomie_modulu bool
test_tree_walks.py:_wyjatki_bloku             bool
```

Żadna z trzynastu nie miesza rodzajów stałych we własnych zwrotach. Lista
odróżnia funkcje od pojedynczych zwrotów; `suite_verdict` ma cztery zwroty
napisowe, a `_bpy_na_poziomie_modulu` trzy logiczne.

## 5. Odtworzenie i granice

```bash
bash tools/tests/constant_returns.sh
python3 tools/tests/test_all.py test_value_chains.py
python3 tools/tests/test_all.py
```

Pierwsze polecenie wypisuje cztery liczby, sprawdza sumę i listę 86 imiennych
wierszy. Drugie jest weryfikacją wymaganą w pozycji 6.D345. Trzecie sprawdza
cały zestaw po dołączeniu raportu. Przyrząd nie zmienia `ksztalt_wezla`, reguły
skoku ani żadnego czytnika. Do porównania dokładnego spadku historycznej
klasy 204 potrzeba odtworzyć jej utracony klasyfikator i populację; liczby
z tego raportu nie udają takiego porównania.
