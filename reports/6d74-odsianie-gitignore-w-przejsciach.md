# Przejścia po drzewie a kopie pominięte w `.gitignore`: dwie liczby z piętnastu były nieprawdziwe (6.D74)

**Zmierzone 10.09.2026 na:** `50ea641`, kontener tej sesji.
**Przyrząd:** czternaście wywołań `os.walk` w `tools/`, kopia drzewa położona pod
`tools/build/kopia/` i `data/raw/kopia/`, `python3 tools/tests/test_all.py`,
pięć kontroli negatywnych z `md5sum -c` po każdym powrocie.

---

## 1. Co dokładnie było zepsute

Czternaście wywołań `os.walk` chodziło po drzewie i **żadne** nie wymieniało katalogu
z kopiami. Wpis 6.D74 mówił, że dziś nie nabiera się ani jedno, „bo wszystkie startują
z NAZWANEGO podkatalogu". Pomiar to zdanie **obalił**.

Kopia drzewa położona pod katalogiem, którego git nie widzi, a `os.walk` owszem:

```
tools/build/kopia/{tests,src,docs,reports}     (`build/` w .gitignore, wiersz 1)
data/raw/kopia/network                         (`data/raw/` w .gitignore)
```

Piętnaście liczb raportowanych przez skany, przed poprawką i po, przy tej samej kopii:

| skan | bez kopii | z kopią, przed | z kopią, po |
|---|---|---|---|
| `test_dead_constants.definicje` | 923 | **1523** | **923** |
| `data_freshness.data_files` | 26 | **31** | **26** |
| pozostałe trzynaście | — | bez zmiany | bez zmiany |

**Dwie liczby z piętnastu, nie zero.** Wpis pozycji spodziewał się zera — teza
„ochrona jest uboczna wobec nazewnictwa, ale dziś nic nie pada" jest prawdziwa
w pierwszej połowie i **nieprawdziwa w drugiej**. `test_dead_constants` startuje
z `tools/` i `src/`, więc kopia pod `tools/build/` leży wprost na jego drodze;
`data_freshness` startuje z `data/`, a `data/raw/` jest w `.gitignore` dokładnie
dlatego, że trzymają się tam pobrane dane robocze.

Trzynaście pozostałych stoi z dwóch różnych powodów i oba są wynikiem, nie
domniemaniem: albo startują poza `tools/` i `data/` (`docs`, `reports`, `src/Sim`),
albo zwracają **zbiór nazw**, w którym kopia nie wnosi ani jednej nowej —
`dead_constants.odczyty` (5352) i `dead_cs.deklaracje` (199) stały tak samo przed
poprawką, jak po niej.

## 2. Odsianie jest jedno i jest CZYTANE z `.gitignore`

`tools/tests/tree_walk.py`. Podpis i wynik jak w `os.walk`, żeby podmiana w miejscu
wołania była jednym słowem; lista `dirs` przycinana **w miejscu** (`dirs[:]`), bo
tylko tak `os.walk` dowiaduje się, żeby w gałąź nie wchodzić.

Lista bierze się z pliku, a nie z drugiej kopii tej samej wiedzy:

```
nazwy   : .godot .import .mono .venv TestResults __pycache__ bin build obj recordings renders
ścieżki : .claude/worktrees assets/audio/raw data/audio/raw data/gtfs data/observations data/raw
```

Że to nie jest ostrożność, pokazuje `BUILD_DIRS` w `test_readme_claims.py`: zna `bin`
i `obj`, a nie zna `build`, `renders` ani `.venv`. Przepisana lista rozjeżdża się
z `.gitignore` przy pierwszym wpisie, którego nikt nie przeniósł.

**Czego moduł NIE robi.** Nie jest implementacją `.gitignore`. Bierze wyłącznie wpisy
**katalogowe** — zakończone ukośnikiem — bo tylko one mogą odciąć gałąź; wzorce
plikowe (`*.pyc`, `*.blend1`) i zaprzeczenia (`!`) zostawia. Nie zna maski w nazwie
katalogu, a `test_the_real_gitignore_has_no_directory_pattern_with_a_star` pilnuje,
żeby wpis w rodzaju `tmp-*/` był **widoczny w commicie, który go dopisuje**, zamiast
przejść po cichu jako nazwa dosłowna.

## 3. Bramka jest na WOŁANIU, nie na wyniku

`test_no_tool_walks_the_tree_without_the_shared_filter` czyta drzewo składni i żąda,
żeby każde `os.walk` w `tools/` szło przez odsianie. Bramka na WYNIKU (czy liczby się
zgadzają) byłaby zielona dokładnie wtedy, gdy nikt akurat nie położył kopii — czyli
jej cisza zależałaby od stanu katalogu, a nie od kodu.

Wołania czytane są `ast`-em, nie grepem: w tym projekcie stoi kilka zdań **o**
`os.walk` w docstringach, w tym w samym `tree_walk.py`.

Dwa wyjątki, każdy z powodem i z zapadką `MAX_WOLNO_WPROST = 2`:

- `tools/tests/tree_walk.py` — to jest samo odsianie i nie ma jak owinąć siebie;
- `tools/tests/test_tree_walks.py` — kontrola różnicy puszcza **oba** przejścia po
  tym samym drzewie probnym i żąda, żeby wynik był różny. Przejście gołe jest tam
  **przedmiotem pomiaru**, a nie skrótem.

`test_the_direct_call_list_stays_closed_and_every_entry_is_still_used` żąda, żeby
każdy wpis nadal dotyczył istniejącego wołania. Wpis bez wołania jest zdaniem
o repozytorium, które przestało być prawdziwe — ta sama choroba, co martwa stała
z 6.B29.

## 4. Kontrola przyrządu, bo pusta lista jest zielona także wtedy, gdy skan oślepnie

`test_the_gate_is_looking_at_a_tree_that_still_has_walks_in_it` liczy wołania **przez**
odsianie (podłoga 14, dziś 15), żąda `tools/track/data_freshness.py` po nazwie i co
najmniej jedenastu plików z `tools/tests/`. Nazwa pliku z **innego** katalogu niż
`tools/tests/` jest tu istotna: bez niej zawężenie skanu do `tools/tests` byłoby
zielone (kontrola negatywna KN-5).

## 5. Pięć kontroli negatywnych, każda WYKONANA

`md5sum -c` po każdym przywróceniu: `OK`.

| kontrola | mutacja | wynik |
|---|---|---|
| KN-1 | jedno wołanie wraca na gołe `os.walk` | **czerwona** 5/7, nazywa plik i wiersz **oraz** rusza liczba skanu |
| KN-2 | odsianie przestaje przycinać gałęzie | **czerwona** 5/7, para gołe/odsiane daje ten sam wynik |
| KN-3 | wzorce biorą też wiersze plikowe | **czerwona** 5/7, `*.pyc` i `plik.txt` wchodzą jako katalogi |
| KN-4 | kontrola różnicy przestaje wołać `os.walk` | **czerwona** 5/7, wyjątek bez wołania zgłoszony |
| KN-5 | skan zawężony do `tools/tests` | **czerwona** 6/7, „nie widzi `tools/track/`" |

KN-1 zapala **dwie** bramki naraz i to jest jej wynik, nie skutek uboczny: bramka na
wołaniu i pomiar na drzewie probnym łapią tę samą mutację z dwóch stron.

## 6. Czego NIE zrobiłem

**Nie skasowałem żadnej kopii** i **nie tknąłem `.gitignore`** — jedno i drugie stoi
w polu „Poza zakresem". Kopie postawione na czas pomiaru (`tools/build/kopia`,
`data/raw/kopia`) zdjąłem po nim; obie leżały pod katalogami pominiętymi, więc
w `git status` nie było ich nigdy.
**Nie napisałem implementacji `.gitignore`** — §2 wyżej mówi, co moduł bierze i czego
nie bierze, a bramka na maskę pilnuje granicy zamiast ją przemilczać.
**Nie zdjąłem `BUILD_DIRS` z `test_readme_claims.py`** ani innych lokalnych filtrów:
są dziś nadmiarowe wobec odsiania, ale ich usunięcie jest zmianą w plikach spoza tej
pozycji (`CLAUDE.md` §4.10) i miałoby własną kontrolę negatywną.

## 7. Bramka trafiła do NOWEGO modułu, a nie do `test_scan_gates.py`

Pole „Wejście" i „Wyjście" pozycji wskazują `tools/tests/test_scan_gates.py`. Ten plik
testuje `tools/blender/scan_gates.py` — trzy predykaty **skanu luzu** (`should_refine`,
`should_verify`, `is_not_vehicle_tag`), a z przejściami po drzewie nie ma wspólnego
nic poza słowem „skan" w nazwie. Dopisanie tam bramki o `os.walk` uczyniłoby jego
docstring nieprawdziwym. Bramka leży więc w `tools/tests/test_tree_walks.py`, a to
zdanie stoi tutaj, żeby rozbieżność z polem była **zapisana, a nie przemilczana**.

## 8. Weryfikacja

```
python3 tools/tests/test_all.py test_tree_walks.py
  -> 7/7 przeszło

python3 tools/tests/test_all.py
  -> RAZEM 94,719 s, 2130 testów, 113 modułów, kod 0

kopia pod tools/build/kopia i data/raw/kopia, 15 liczb skanów:
  przed poprawką: 2 zmienione (definicje 923 -> 1523, data_files 26 -> 31)
  po poprawce:    0 zmienionych
```
