# 6.D346 · Rozpakowanie i `+=` poza regułą jednego skoku

**Data:** 25.09.2026. **Baza bieżąca:** `eeafacb9b23c56f57418d89f2b0ec3e7ebbdc259` (main po #802). **Przyrząd:** `tools/tests/hidden_assignments.sh`.

## 1. Populacje i jednostki

Przyrząd pożycza `tree_walk.znajdz` i czyta skommitowane `*.py` bezpośrednio
pod `tools/tests/`. Pierwsza populacja to **wszystkie instrukcje AST**, także
w testach i funkcjach zagnieżdżonych. „Rozpakowanie” oznacza `ast.Assign` z co
najmniej jednym celem `ast.Tuple` albo `ast.List`; `+=` oznacza `ast.AugAssign`
z operatorem `ast.Add`. Drugą populacją są **pary (funkcja modułowa niebędąca
`test_*` ani `main`, goła nazwa w `return`)**, w których ta nazwa jest wiązana
rozpakowaniem albo `+=` w tej samej funkcji. Zwrotów z funkcji zagnieżdżonych
nie przypisuje się funkcji zewnętrznej.

| miara | wynik |
|---|---:|
| instrukcje z rozpakowaniem | **788** |
| cele rozpakowania w tych instrukcjach | **792** |
| instrukcje `+=` | **315** |
| z tych `+=` z prostym celem `Name` | **274** |
| pary czytnik/nazwa zwracana dotknięte tymi instrukcjami | **26** |
| pary z rozpakowaniem / `+=` | **12 / 14** |
| miejsca przypisania dla tych 26 par | **30** |
| kształt możliwy do odczytania bez następnego skoku / nadal nieznany | **25 / 1** |

Kontrola rozłączności jest jawna: **12 + 14 = 26** par, a **25 + 1 = 26**.
Nie ma pary obecnej po obu stronach. Cztery dodatkowe miejsca względem 26 par
wynikają z powtórzonych `+=` tej samej nazwy.

## 2. Co znaczy „bez następnego skoku”

Dla rozpakowania przyrząd rzutuje literalną krotkę/listę po tej samej pozycji
co nazwa: `out, n = [], 0` daje `out: list`, `n: int`. Wynik wywołania
`out, n = read()` pozostaje nieznany. Dla `+=` bierze bezpośrednią wcześniejszą
inicjalizację nazwy i sprawdza zgodność: lista pozostaje listą przy udanym
`+=`, licznik ma inicjalizację `int` i argument `int` (`1`, `len(...)` albo
`sum(1 for ...)`). Znane typy zwrotu wbudowanych `len` i `sorted` nie wymagają
skoku do funkcji w drzewie. Przyrząd **nie wykonuje wywołań i nie analizuje
przepływu sterowania**; wynik dotyczy widocznego kształtu przypisania, a nie
gwarancji, że każdy przebieg dochodzi do tego miejsca.

Kontrole syntetyczne przyrządu sprawdzają obie strony rozpakowania literalnego
oraz to, że `out, n = read()` nie dostaje kształtu przez zgadywanie wyniku
wywołania.

## 3. Lista imienna 26 par

| funkcja w `tools/tests/` | zwracana nazwa | wiązanie | wynik bez skoku |
|---|---|---|---|
| `assertion_gate.py::_mark_except_guards` | `marked` | `+=` | `int` |
| `mutation_sweep.py::worker` | `done` | `+=` | `int` |
| `mutation_sweep.py::naglowek_odciskow` | `out` | `+=` | `list` |
| `test_assertion_gate.py::zdania_rodziny` | `out` | rozpakowanie | `list` |
| `test_ci_workflows.py::_shared_machine_files` | `found` | `+=` | `list` |
| `test_crs_convergence.py::_package_points_in_lambert72` | `points` | `+=` | `list` |
| `test_dead_constants.py::wiazan_domyslnych` | `ile` | `+=` | `int` |
| `test_digit_boundaries.py::_tokeny` | `out` | rozpakowanie | `list` |
| `test_docs_ci_claims.py::paragraphs` | `blocks` | rozpakowanie | `list` |
| `test_docs_ci_claims.py::documents` | `found` | `+=` | `list` |
| `test_expected_exception.py::ile_wystapien` | `ile` | `+=` | `int` |
| `test_field_paths.py::_code_lines` | `out` | rozpakowanie | `list` |
| `test_field_paths.py::adresy_rozne_w_polu` | `ile` | `+=` | `int` |
| `test_game_needle_specificity.py::wywolania` | `ile` | `+=` | `int` |
| `test_inspire_rail.py::_load_axis` | `axis` | rozpakowanie | **nieznany** |
| `test_machine_paragraphs.py::akapity` | `out` | rozpakowanie | `list` |
| `test_message_claims.py::_akapity_prozy` | `out` | rozpakowanie | `list` |
| `test_message_claims.py::gole_w_prozie_pomiarowej` | `out` | rozpakowanie | `list` |
| `test_message_claims.py::zdan_ogloszonych_pomiarem` | `ile` | `+=` | `int` |
| `test_parameter_boundaries.py::_clothoid` | `points` | rozpakowanie | `list` |
| `test_placement.py::_bent_axis` | `points` | `+=` | `list` |
| `test_readme_claims.py::osie_plaskie` | `ile` | `+=` | `int` |
| `test_report_claims.py::_same_przelaczniki_ksztaltu` | `zostaje` | rozpakowanie | `list` |
| `test_report_claims.py::punkty_sekcji` | `out` | rozpakowanie | `list` |
| `test_runner_options.py::_sklej_kontynuacje` | `out` | rozpakowanie | `list` |
| `test_tool_refusals.py::wszystkie_asserty` | `znalezione` | `+=` | `list` |

**Jedyny nieznany:** `test_inspire_rail.py::_load_axis` robi
`axis, provenance = IR.load_alignment(path)` i zwraca `axis`. Wyrażenie po
prawej jest wywołaniem; bez skoku do `tools/track/inspire_rail.py` i
`IR.load_alignment` kształtu pierwszego elementu nie ma w lokalnym wyrażeniu.
Rozszerzenie reguły o samo rozpakowanie
przeniosłoby tę parę z „nie widzę przypisania” do „widzę i nadal nie wiem”.

## 4. Historyczna kontrola 18 **nie przechodzi** dla tej populacji

6.D336 §2.2 podało **11 + 7 = 18** nazw w klasie 44 gołych nazw pochodzących
z tamtego klasyfikatora. Dzisiejszy szeroki census daje **12 + 14 = 26**.
Uruchomiłem ten sam przyrząd także na bazowym drzewie raportu 6.D336,
`5bfa8f1`: tam daje **786 instrukcji rozpakowania, 790 celów, 311 `+=`
i nadal 26 par (12 + 14)**. Rozbieżności 26 wobec 18 **nie wyjaśnia** więc
przyrost kodu od tamtego commita. Wyjaśnienia trzeba szukać w wyborze
historycznej klasy 204, której klasyfikator nie został utrwalony jako kod
(6.D345 i otwarta 6.D373). Nie dobieram filtra do liczby 18 i nie nazywam
26 ponownym pomiarem tamtej klasy. Historyczna kontrola członkostwa pozostaje
niezdana; wynik tego raportu dotyczy wyłącznie jawnej populacji z §1.

## 5. Odtworzenie i granica zmiany

```bash
bash tools/tests/hidden_assignments.sh
python3 tools/tests/test_all.py test_value_chains.py test_tree_walks.py
python3 tools/tests/test_all.py
```

Pierwsze polecenie wypisuje liczby i imienne pary; skan używa wyłącznie drzewa.
Drugie jest testem z pola pozycji. Trzecie sprawdza cały zestaw. Nie
zmieniono reguły skoku, `ksztalt_wezla`, żadnego czytnika, `src/` ani `data/`.
