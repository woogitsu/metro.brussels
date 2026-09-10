# Pole zadania nazywa katalog i opcję: dwa kształty, których skan ścieżek nie widzi (6.D73)

**Zmierzone 10.09.2026 na:** `fa6d5c4`, kontener tej sesji.
**Przyrząd:** `tools/tests/test_field_paths.py`, `python3 tools/tests/test_all.py`,
pięć kontroli negatywnych wykonanych na kopii pliku z `md5sum -c` po każdym powrocie.

---

## 1. Co bramka pól widziała, a czego nie

`test_field_paths.py` sprawdza od 6.D32, czy ścieżka wymieniona w polu „Wejście",
„Wyjście" albo „Weryfikacja" rozwiązuje się w drzewie. Jej `PATH_TOKEN` żąda
**znanego rozszerzenia na ostatnim segmencie** — i to jest jedyny powód, dla którego
dwa kształty przechodziły przez nią niewidzialne:

- **katalog** rozszerzenia nie ma (`tools/ci/golden/`);
- **nazwa opcji** nie jest ścieżką w ogóle (`--at-m`).

Licznik obu stał na **sześciu** przypadkach, wszystkie w blokach już wykonanych.

## 2. Sześć przypadków, po jednym wierszu, z rozstrzygnięciem który kształt je łapie

Pole „Poza zakresem" pozycji 6.D73 wyklucza poprawianie tych sześciu pozycji („ich
zapis jest historyczny"), więc dowodem nie jest cisza w drzewie, tylko **wstawienie
każdego z powrotem jako mutacji do bloku otwartego**. Wykonane w
`test_each_of_the_six_measured_cases_lights_a_gate_when_put_back`:

| przypadek | pole | kształt, który się zapala | czy istniał przed 6.D73 |
|---|---|---|---|
| 6.D59 · plik pod `.github/workflows/` o nazwie, której nie ma | Wejście | ścieżka | **tak** |
| 6.A21 · `tools/ci/golden/` | Wejście | **katalog** | nie |
| 6.A21 · ten sam katalog w `git diff --stat` | Weryfikacja | **katalog** | nie |
| 6.B43 · `--at-m=96` | Weryfikacja | **opcja** | nie |
| 6.B43 · `--out=…` | Weryfikacja | **opcja** | nie |
| 6.D64 · `provenance.py` wskazany w `tools/track/` zamiast `tools/data/` | Wejście | ścieżka | **tak** |

Dwa z sześciu łapał skan, który był — i to jest wynik, a nie założenie: 6.D59
poprawiło `PATH_TOKEN` **także w tym pliku**, więc wiodąca kropka wchodzi. Cztery
nie miały czym zostać złapane.

Przybity jest też **rozkład**: każda z sześciu mutacji zapala **dokładnie jeden**
kształt. Bramka zgłaszająca wszystko przeszłaby samą pętlę „czy się zapaliło" i nie
przeszłaby tego wiersza.

## 3. Dlaczego bramki chodzą po blokach OTWARTYCH

Zapis pozycji wykonanej jest historią: jej „Weryfikacja" cytuje polecenie, którym coś
zmierzono, a narzędzie mogło się od tamtej pory zmienić — przepisanie tego cytatu
sfałszowałoby pomiar. To samo mówi wprost pole „Poza zakresem" pozycji 6.D73.

**Skutek uboczny tej decyzji jest taki, że obie nowe bramki na dzisiejszej kolejce
milczą** — 21 bloków otwartych, **5** katalogów i **18** poleceń, zero zgłoszeń.
Milcząca bramka jest zielona także wtedy, gdy wzorzec przestał cokolwiek łapać,
więc kontrola przyrządu jest **przybita do zamrożonych bloków**: `missing_directories`
na bloku 6.A21 musi dać `tools/ci/golden/` **trzy razy**, a `unknown_options` na
bloku 6.B43 dokładnie `['--at-m', '--out']` — i ani `--shot`, ani `--view`, które
scena zna.

**Progu po liczbie katalogów albo poleceń w otwartych blokach tu NIE MA i to jest
wybór.** Kolejka maleje z każdą scaloną pozycją, więc taki próg czerwieniałby od
sprzątania. Pierwsza wersja tej bramki miała `zbadane >= 20`, zapaliła się przy
**18** i to jest jedyny powód, dla którego ten akapit istnieje.

## 4. Kształt katalogu: dwa segmenty i ukośnik, obie rzeczy zmierzone

`DIR_TOKEN` żąda **co najmniej dwóch** segmentów. Wariant jednosegmentowy dał
w blokach otwartych zgłoszenie na `CPU/` ze zwrotu „stosunek CPU/ściana" (6.D93) —
wykonana kontrola negatywna KN-1, wypis dosłowny:

```
FAIL test_no_open_field_names_a_directory_that_is_not_in_the_tree:
  pole zadania nazywa katalog, którego w drzewie nie ma: [('6.D93', 'Weryfikacja', 'CPU/')]
```

Wykluczenie `$` odsiewa `$DOTNET_ROOT/host/fxr/`, czyli ścieżkę zbudowaną ze
zmiennej — o niej „nie istnieje" nie jest zdaniem prawdziwym.

Na całym `docs/TASKS.md` wzorzec widzi **52** katalogi, z tego **3** nieistniejące,
wszystkie trzy to `tools/ci/golden/` z bloku 6.A21.

## 5. Kształt opcji: dwa zawężenia, oba mierzone — i jedno z nich nic dziś nie zmienia

**Ogrodzenie.** Skan czyta wyłącznie wiersze z bloków ogrodzonych. Zmierzone na całym
`docs/TASKS.md`: **200** wystąpień wywołania narzędzia w polach, z tego **199**
w blokach ogrodzonych i **1** w prozie — pole „Wyjście" bloku 6.A26 niesie
`--path src/Game` w środku zdania.

**Kontrola negatywna KN-2 wyszła ZIELONA i zostaje tu wypisana, bo to jest wynik.**
Zdjęcie ogrodzenia nie zmieniło ani jednego zgłoszenia na dzisiejszej treści: to
jedno prozaiczne wystąpienie nie ma za sobą żadnej nazwy opcji. Zawężenie pilnuje
więc KSZTAŁTU, który w drzewie **jest**, a nie trafienia, które w nim **jest**.
Kontrola przepisana na to zdanie z 6.A26 z **dopisaną** nazwą opcji zapala się
poprawnie i wtedy KN-2 czerwienieje (KN-2b) — pierwsza wersja kontroli używała
zdania „`git log --follow` jako narzędzie", w którym nie ma wywołania narzędzia
pythonowego, więc nie mierzyła ogrodzenia wcale.

**Drzewo składni, nie grep.** Lista opcji, które narzędzie naprawdę parsuje, idzie
z wywołań `add_argument`. Grep po napisie `--nazwa` łapie też komentarze, teksty
pomocy i flagi CUDZYCH poleceń. Zmierzone na **15** narzędziach wołanych dziś z pól:
w **pięciu** grep widzi więcej niż argparse.

```
tools/ci/assert_linecore_budget.py    o 13 więcej   --axis, --coast-from-m, --limit-kmh, …
tools/tests/test_runner_options.py    o 12 więcej   --atp, --calls, --headless, …
tools/tests/mutation_sweep.py         o  6 więcej   --detach, --porcelain, --quiet, …
tools/ci/assert_shot_metadata.py      o  3 więcej   --allow-new-baseline, --baseline, --metrics
tools/tests/test_all.py               o  1 więcej   --help
```

Kontrola stoi na `assert_shot_metadata.py --metrics`: napis jest w pliku,
`add_argument` go nie dostaje. Wariant grepowy przyjmuje tę komendę w milczeniu
(KN-3 zielona na pierwszej wersji kontroli, czerwona po jej dopisaniu — KN-3b).

## 6. Pięć kontroli negatywnych, każda WYKONANA

`md5sum -c` po każdym przywróceniu: `OK`.

| kontrola | mutacja | wynik |
|---|---|---|
| KN-1 | `DIR_TOKEN` na jeden segment | **czerwona**, 14/16, fałszywy alarm na `CPU/` |
| KN-2 | zdjęte ogrodzenie, stara kontrola prozy | **zielona** — kontrola nic nie mierzyła |
| KN-2b | zdjęte ogrodzenie, kontrola prozy przepisana | **czerwona**, 15/16 |
| KN-3 | opcje z grepa, bez kontroli na `--metrics` | **zielona** — kontroli brakowało |
| KN-3b | opcje z grepa, po dopisaniu kontroli | **czerwona**, 15/16 |
| KN-4 | `DIR_TOKEN` przestaje łapać cokolwiek | **czerwona**, 13/16, kotwica 6.A21 pada |
| KN-5 | `SCENE_CALL` wskazuje nieistniejącą ścieżkę | **czerwona**, 13/16, kotwica 6.B43 pada |

KN-2 i KN-3 są tu wypisane **razem ze swoim zielonym wynikiem**, bo to one nazwały
dwie własne słabości kontroli, a nie ostrożność ani druga para oczu.

## 7. Poprawka do pola „Wejście" pozycji 6.D73 — ta sama usterka, o której ona jest

Wpis 6.D73 wskazuje `tools/tests/test_backlog.py` jako miejsce, gdzie stoi „skan pól
i wyjątki ścieżek". Skan przeprowadził się do `tools/tests/test_field_paths.py` przy
6.D32 (#388), więc pole nazywa adres, pod którym tej rzeczy nie ma. Pozycja tropiąca
pola nazywające coś niewykonalnego sama takie pole ma — i jest to siódmy przypadek
tego wzorca, nie ozdoba narracji. Poprawione w tym samym commicie; sam wzorzec go
nie łapie, bo `test_backlog.py` w drzewie **jest** — usterką jest treść nawiasu,
a nie ścieżka.

## 8. Czego NIE zrobiłem

**Nie poprawiłem sześciu pozycji** — pole „Poza zakresem" pozycji 6.D73 wyklucza to
wprost. `tools/ci/golden/` w 6.A21 i `--at-m` w 6.B43 stoją nietknięte i są dziś
**kotwicami** kontroli przyrządu; poprawienie ich rozbroiłoby obie bramki.
**Nie rozszerzyłem `PATH_TOKEN`** o katalogi: 6.D33 zmierzyło, że taki wariant daje
2 zgłoszenia na 4 trafienia (dokłada urwany na gwiazdce fragment maski
`tools/tests/test_*.py` z 6.B15), a osobny wzorzec z ukośnikiem na końcu tego nie robi.
**Nie tknąłem** progów `MIN_PATHS` ani listy `EXCEPTIONS`.

## 9. Weryfikacja

```
python3 tools/tests/test_all.py test_field_paths.py
  -> 16/16 przeszło

python3 tools/tests/test_all.py
  -> RAZEM 93,459 s, 2123 testów, 112 modułów, kod 0
```

Zestaw urósł z **2119** do **2123** testów; modułów bez zmiany, bo bramki dopisały
się do istniejącego `test_field_paths.py`.
