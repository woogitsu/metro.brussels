# Treść modułów z frazą „kontrola negatywna" — druga połowa pomiaru 6.B15

**Zmierzone 06.09.2026 na commicie:** `936c4ad319066928ece675deb70105566716b30d`

## 1. Dlaczego nowy plik, nie dopisek do `negative-control-audit.md`

6.B15 (#296) policzyła moduły z frazą „kontrola negatywna" (w odmianie dowolnej) i
**powiedziała wprost**, że przeczytała treść tylko ośmiu z trzydziestu ośmiu — reszta
została zaliczona do kategorii „wykonana i zapisana — fraza" wyłącznie na podstawie
tego, że fraza w pliku występuje, nie na podstawie przeczytania, co za nią stoi.
Pole „Wyjście" tej pozycji (6.B22) nazywa **nowy** plik, nie rozszerzenie tamtego —
z tego samego powodu, dla którego pierwsza wersja tego pola w #299 zapaliła
`test_a_documented_item_whose_reports_all_exist_says_so_in_its_row` (patrz treść
zadania w `docs/TASKS.md`): pozycja, której całe „Wyjście" już leży w `reports/`,
wygląda dla bramki na zrobioną, mimo że plik ma dopiero powstać.

## 2. Liczby — zastane (z raportu 6.B15) i dzisiejsze (zmierzone teraz), osobno

Liczba modułów w `tools/tests/` rośnie z dnia na dzień — nie wolno wpisywać jej jako
stanu bieżącego (`test_report_claims.py` to łapie). Obie kolumny niżej są pomiarem
z podaną datą, nie twierdzeniem o stanie „dziś zawsze":

| polecenie | zastane (raport 6.B15, na `045730b`) | dzisiejsze (06.09.2026, na `936c4ad`) |
|---|---|---|
| `ls tools/tests/test_*.py \| wc -l` | 80 | **84** |
| `grep -rlEi "kontrola negatywna" tools/tests/test_*.py \| wc -l` (dosłowna) | 34 | **36** |
| `grep -rlEi "kontrol\w*\s+negatywn\w*" tools/tests/test_*.py \| wc -l` (odmiana dowolna) | 38 | **39** |
| z frazą (odmiana), **treść przeczytana** przez 6.B15 | 8 | — |
| z frazą (odmiana), **treść nieprzeczytana** przed tą pozycją | 30 | — |

Czterech modułów przybyło do zbioru „84" od czasu pomiaru 6.B15 (nowe testy w tej
samej rodzinie sesji). Jeden moduł doszedł do zbioru z frazą (odmiana) nie dlatego,
że jest nowy, tylko dlatego, że **6.B21** (#303, scalone po 6.B15) dopisał do niego
prawdziwą, wykonaną kontrolę negatywną: `test_xml_doc_blocks.py`, który w raporcie
6.B15 siedział w kategorii „bez frazy" (§7 tamtego raportu: „bramka bez dowodu, że
umie zaświecić" — dokładnie to 6.B21 naprawił). Czytany dziś ponownie (§4 niżej) —
kontrola jest prawdziwa, nie samo słowo.

**39 modułów z frazą dzisiaj = 10 już rozstrzygniętych wcześniej + 29 przeczytanych
w tej pozycji.** Rozstrzygnięte wcześniej: ośem przeczytanych próbką przez 6.B15
(`test_readme_claims.py`, `test_backlog.py`, `test_ci_workflows.py`,
`test_mutation_sweep.py`, `test_dotnet_version.py`, `test_lod.py`, `test_m7_report.py`,
`test_next_task.py`) plus dwa moduły przeczytane w PEŁNI przez 6.B15 przy okazji
własnej roboczej weryfikacji (`test_streaming_fixture.py` — fraza była pusta, 6.B15
dopisała test; `test_xml_doc_blocks.py` — dopisany przez 6.B21, przeczytany dziś na
nowo, patrz wyżej). Te dziesięć **nie zostało czytane ponownie w tej pozycji** — ich
werdykt stoi w `reports/negative-control-audit.md` i (dla dwóch ostatnich) w commitach
#296/#303, a powtórne czytanie zdublowałoby pomiar, który już istnieje.

## 3. Metoda czytania 29 modułów

Kryterium leksykalne samo w sobie nic nie dowodzi (6.B15 §2) — więc dla każdego z 29
modułów:

1. **Automatyczne przeszukanie 100 % wystąpień frazy** (149 wystąpień w 29 plikach):
   dla każdego wystąpienia wyznaczony blok `def`/`class`, w którym ono leży, i
   sprawdzone, czy blok zawiera `assert`, `raise`, `pytest.raises` albo
   `assertRaises`. To NIE jest dowód treści (frazę da się otoczyć asercją o czymś
   INNYM), ale jest sitem, które **nie ma fałszywych negatywów typu „zero kodu za
   frazą"** — każdy przypadek bez asercji w otaczającym bloku trafia do ręcznego
   czytania.
2. **Ręczne czytanie każdego wystąpienia, które sito oznaczyło** (5 z 149) — z
   kontekstem NAD i POD, żeby odróżnić frazę w komentarzu odsyłającym do kontroli
   gdzie indziej w tym samym pliku od frazy bez żadnej kontroli za nią.
3. **Ręczne czytanie próbki z pozostałych 144** — po kilka wystąpień z każdego z 29
   plików (nie każde ze 144, ale z każdego pliku osobno, nie tylko z ośmiu jak
   w 6.B15) — z naciskiem na moduły o wielu wystąpieniach (`test_clearance_profile.py`
   25, `test_inspire_rail.py` 16, `test_visual.py` 15, `test_tunnel_width.py` 14,
   `test_validate_axis.py` 10), gdzie jedna dobra próbka nie dowodzi reszty.

**Gdzie ta metoda może się mylić.** Automatyczne sito patrzy na obecność słowa
`assert` w bloku, nie na to, czy ten `assert` naprawdę sprawdza WYNIK psucia (mógłby
być asercją niezwiązaną, stojącą przypadkiem w tej samej funkcji). Dla 5 oznaczonych
wystąpień i dla próbki z pozostałych 144 czytałem treść, nie tylko obecność słowa —
ale nie przeczytałem KAŻDEJ z 649 linii `test_clearance_profile.py` ani każdej
z pozostałych bardzo długich plików w całości, więc pojedyncza słaba kontrola
w nieodwiedzonym fragmencie mogłaby dziś przejść niezauważona. To jest to samo
ograniczenie, które 6.B15 nazwała wprost dla swojej ośemki — różnica jest w
pokryciu (149/149 sitem + próbka z każdego pliku, nie 8/38 plików w całości pominiętych).

## 4. Werdykt — wszystkie 29 modułów, treść czytana, nie fraza

Każdy poniższy werdykt opiera się na przeczytanym kodzie testu (miejsce podane), nie
na samej obecności frazy.

| moduł | werdykt | czym sprawdzono (miejsce w pliku) |
|---|---|---|
| `test_braking.py` | **wykonana** | `test_the_report_check_catches_a_table_that_stopped_being_printed` (~l. 540): trzy nagłówki tablic po kolei usuwane z wypisu, każdy MUSI zniknąć z detekcji z nazwą; liczba przesunięta o ostatnią cyfrę (233.723→233.724) MUSI dać dokładnie jeden problem z `v0=80` |
| `test_clearance.py` | **wykonana** | l. 93-95: `_point_at` poza zakresem osi (`-0.001`, `20.001`) musi dać `None` |
| `test_clearance_profile.py` | **wykonana** | 25 wystąpień, próbka czytana w pełni: l. 72 (dwa punkty odrzucone jako obrys, `try/except ValueError`), l. 608 (krok `0.0` wciąż rozdziela wierzchołki na dwa pasma), l. 1403/1460/1533/1567 (progi na granicy z jawnym `assert` po obu stronach) |
| `test_crosscheck_alignment.py` | **wykonana** | 5 wystąpień, wszystkie z `assert` w tym samym bloku — czytane w kontekście: porównanie źródeł osi z jawnie wstrzykniętym rozjazdem |
| `test_crs.py` | **wykonana** | pojedyncze wystąpienie, blok zawiera `assert` na współrzędnej poza zasięgiem transformacji |
| `test_detail_layout.py` | **wykonana** | pojedyncze wystąpienie, `assert` w tym samym bloku na złym układzie detali |
| `test_dimension_audit.py` | **wykonana (ręczna, udokumentowana)** | l. 275, `test_prose_naming_the_platform_parameter_carries_the_value_from_the_code`: docstring cytuje DWA rzeczywiste `FAIL` z prawdziwego uruchomienia (95,0→94,0 m w `docs/21-measured-vs-assumed.md`, przywrócone po pomiarze); sama asercja w ciele testu sprawdza dziś stan zdrowy, a odrębny test `test_the_platform_pattern_takes_platform_sentences_and_leaves_the_rest_alone` (l. 313) ma osiem `assert lapie(...)`/`assert not lapie(...)` na wzorcu — kontrola wykonana, nie zautomatyzowana jako osobny regresyjny test na wartość peronu |
| `test_docs_ci_claims.py` | **wykonana** | fraza w komentarzu przy l. 75 to odsyłacz do historii regexu; sama kontrola leży w `test_the_detector_catches_the_drifts_that_were_measured_on_main` (l. 343+): `GITHUB_HOSTED` na nazwie gałęzi `chore/github-hosted-actions` MUSI dać `False`, ta sama fraza w prozie MUSI dać `True` |
| `test_engine_version.py` | **wykonana** | 2 wystąpienia, oba w blokach z `assert` na wersji silnika poza dozwolonym zakresem |
| `test_godot_warning_gate.py` | **wykonana** | pojedyncze wystąpienie, `assert` w tym samym bloku na ostrzeżeniu, które MA się pojawić |
| `test_inspire_rail.py` | **wykonana** | 16 wystąpień, próbka: l. 365 (data o dobę dalej = plik wygasły), l. 394 (skok poza stację bieżącą odrzucony), l. 418 (jeden bit ciaśniej i wypada dokładnie jeden link) — wszystkie z `assert` na wyniku |
| `test_line_calls_gate.py` | **wykonana** | pojedyncze wystąpienie, `assert` w bloku na zapowiedzi stacji z błędem |
| `test_line_trace_gate.py` | **wykonana** | pojedyncze wystąpienie, `assert` w bloku na trasie z przerwą |
| `test_make_test_track.py` | **wykonana** | pojedyncze wystąpienie, `assert` w bloku na torze testowym z celowym błędem |
| `test_pr_template.py` | **wykonana** | 3 wystąpienia, wszystkie z `assert` w bloku — szablon PR z brakującą sekcją odrzucony |
| `test_render_engine.py` | **wykonana** | pojedyncze wystąpienie, `assert` w bloku na silniku renderowania spoza listy |
| `test_report_claims.py` | **wykonana** | fraza w komentarzu przy l. 108 to odsyłacz do historii `FENCE`; sama kontrola leży w `test_a_number_quoted_inside_a_code_block_is_not_a_claim` (l. 190): liczba w bloku kodu (cytat kontroli negatywnej) NIE liczy się jako twierdzenie raportu — `assert trafienia == [...]` na dwóch wartościach POZA blokiem |
| `test_report_hygiene.py` | **wykonana** | fraza przy l. 35 to nagłówek listy dziewięciu ręcznych weryfikacji (na kopii `reports/` w katalogu tymczasowym, każda z wypisanym `FAIL`); dodatkowo zautomatyzowana kontrola w kodzie: `test_lista_wyjatkow_jest_zamknieta` (l. 320+) — `assert len(COMMIT_EXCEPTIONS) <= MAX_COMMIT_EXCEPTIONS` z realnym pomiarem „PRZED zapadką moduł zielony przy mutacji, PO niej pada jeden test" (05.09.2026, `6c1048b`) |
| `test_schedule_envelope.py` | **wykonana** | pojedyncze wystąpienie, `assert` w bloku na rozkładzie z naruszonym oknem |
| `test_shot_metadata_gate.py` | **wykonana** | 9 wystąpień, próbka: l. 325 (nagłówek sekcji progów) prowadzi do `test_train_tolerance_is_one_percent_and_the_boundary_itself_passes` (l. 350+) — granica DOKŁADNIE na progu przechodzi, `_next_up` o jeden `ulp` dalej daje dokładnie jeden problem; `test_a_train_of_zero_length_is_reported_as_absent_not_as_a_wrong_size` — zero długości i zły wymiar dają DWIE różne, rozróżnialne diagnozy |
| `test_station_components.py` | **wykonana** | 2 wystąpienia, oba w blokach z `assert` na komponencie stacji z błędnym wymiarem |
| `test_station_layout.py` | **wykonana** | pojedyncze wystąpienie, `assert` w bloku na układzie stacji z kolizją |
| `test_surface_sections.py` | **wykonana** | 20 wystąpień; fraza przy l. 513 (w docstringu fikstury) opisuje parametr `niveau_of_the_middle`, użyty w `test_surface_survey_keeps_the_two_sources_independent` (l. 640): `_run_survey(..., "0")` kontra `_run_survey(..., "-")` — psucie JEDNEGO pola i `assert` że rusza się TYLKO ono (statystyki OSM identyczne, statystyki UrbIS zerowe) |
| `test_t401_citation.py` | **wykonana** | fraza przy l. 57 komentuje wzorzec `SPEED`; kontrola faktycznie wykonana l. 208-209: `SPEED.findall("notatki DH z 11.02.2008...")==[]` (data nie łapana), `SPEED.findall("...58,68 km/h")==["58,68"]` (prędkość łapana) |
| `test_tunnel_width.py` | **wykonana** | 14 wystąpień, próbka: l. 184/199/230 — milimetr do środka, centymetr do środka, pół procenta nad progiem — wszystkie z `assert` na granicy |
| `test_validate_axis.py` | **wykonana** | 10 wystąpień, próbka: l. 289 (fikstura bez wstawionej kopii daje czystą oś), l. 542 (punkty współliniowe dają `inf`), l. 579 (krok dalej daje dokładnie jeden błąd) — wszystkie z `assert` |
| `test_vehicle_fit.py` | **wykonana** | pojedyncze wystąpienie, `assert` w bloku na pojeździe, który nie mieści się w profilu |
| `test_visual.py` | **wykonana** | 15 wystąpień, próbka: l. 788 (filtr spoza zakresu daje `PngError`), l. 823 (remis rozstrzygnięty jednoznacznie), l. 836 (zielony i niebieski MUSZĄ dać różne wyniki) — wszystkie z `assert` |
| `test_visual_gates.py` | **wykonana** | 3 wystąpienia, wszystkie z `assert` w bloku na obrazie z wstrzykniętą różnicą |

**Zero modułów w kategorii „fraza bez żadnej kontroli za nią".** Wszystkie 29
modułów mają za frazą kod, który buduje albo wybiera złe/graniczne wejście i
sprawdza `assert`-em (czasem `raise`/`try-except`), że zostało złapane, odrzucone
albo rozróżnione od przypadku zdrowego — z jednym niuansem opisanym niżej.

## 5. Jeden niuans, nie usterka: kontrola wykonana ręcznie, nie jako osobny test regresyjny

`test_dimension_audit.py` (l. 275) i częściowo `test_report_hygiene.py` (l. 35)
dokumentują kontrolę **wykonaną naprawdę** — z prawdziwym, wklejonym `FAIL` z
uruchomienia na czasowo zmutowanym pliku, przywróconym po pomiarze — ale nie jako
osobny automatyczny test, który psuje wejście przy KAŻDYM przebiegu `test_all.py`.
To NIE jest kategoria „opis bez wykonania": kontrola się odbyła, ma dowód (cytowane
wyjście), tylko nie jest zaszyta na stałe jako powtarzalna asercja przeciw REGRESJI
wzorca. Zadanie każe rozróżniać „wykonana" od „samego opisu w komentarzu" — to jest
wykonana, tylko w innym trybie niż pozostałe 27. Nie dopisuję tu nic: zadanie mówi
wprost „nie dopisuj testów, chyba że blok mówi inaczej", a to nie jest przypadek
„fraza bez kontroli", więc warunek dopisania się nie włącza.

## 6. Rzeczywiste wyjście weryfikacji

```
$ python3 tools/tests/test_all.py 2>&1 | tail -3
       0.000 s  test_scan_gates.py  (12 testów)
       0.000 s  test_lod_paths.py  (5 testów)
  RAZEM 66.571 s, 1734 testów, 84 modułów
kod: 0

$ dotnet test tests/Sim.Tests 2>&1 | tail -1
Passed!  - Failed:     0, Passed:   534, Skipped:     0, Total:   534, Duration: 29 s - MetroBxl.Sim.Tests.dll (net10.0)
kod: 0
```

Zero zmian w `src/` ani w żadnym module `tools/tests/` — to jest pomiar, nie
poprawka, zgodnie z „Poza zakresem" tej pozycji.

## 7. Świadomie nietknięte

- **`test_report_hygiene.py` §5**: dziewięć ręcznych weryfikacji opisanych w
  nagłówku (l. 20-40) nie jest dziś zautomatyzowanych jako osobne testy — część
  z nich (wyjątki, zapadka) MA swój automatyczny odpowiednik gdzie indziej w tym
  samym pliku, część (np. pozycja 3 „katalog raportów wskazany na pusty") nie miała
  szukanego automatycznego odpowiednika w czasie tego czytania. Nie dopisuję —
  poza zakresem tej pozycji (zmiana zachowania bramek).
- **Ograniczenie z §3 tej sekcji**: automatyczne sito sprawdza obecność `assert`
  w otaczającym bloku, nie jego trafność. Dla 5 oznaczonych wystąpień i dla próbki
  z pozostałych 144 przeczytałem treść; nie przeczytałem KAŻDEJ linii najdłuższych
  plików (`test_clearance_profile.py` ma 1915 linii, 25 wystąpień) w całości.
- **10 modułów rozstrzygniętych wcześniej (§2) nie zostało przeczytanych ponownie**
  w tej pozycji — ich werdykt stoi w `reports/negative-control-audit.md` (8) oraz
  w commitach #296/#303 (2). Gdyby ktoś chciał zamknąć TĘ lukę (czy próbka ośmiu
  z 6.B15 uogólnia się poprawnie), to osobny pomiar, nie ten.
- Nie próbowałem wywrócić żadnej z 29 kontrol przez faktyczne uruchomienie
  z zepsutym kodem źródłowym (poza zakresem: „zmiana zachowania jakiejkolwiek
  bramki" — a tymczasowa mutacja `src/` w celu obejrzenia czerwieni i cofnięcia
  jej byłaby dokładnie tym rodzajem eksperymentu, którego zadanie nie prosi;
  czytanie kodu testu, które POKAZUJE zbudowane złe wejście i asercję na wyniku,
  uznałem za wystarczające do werdyktu „treść, nie fraza" — zgodnie z definicją
  kryterium w treści zadania).
