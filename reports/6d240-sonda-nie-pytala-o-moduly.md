# 6.D240 — zależność realna, zadeklarowana nigdzie: cztery joby naraz przy 2386/2389

**16.09.2026**, na `6ad172a`. Wejście: `.github/actions/probe-tools/action.yml`,
`.github/workflows/python-tests.yml`, `tools/ci/apt-packages/blender.txt`,
`tools/ci/apt-packages/blender-xvfb.txt`, `tools/tests/test_ci_workflows.py`.

## 1. Co się stało 15.09.2026

Cztery joby padły **jednocześnie**, na **trzech różnych maszynach puli**:

| check | maszyna | krok, w którym padł |
|---|---|---|
| `tools` | `github-runner-02` | `Run tool tests` |
| `visual-regression` | `github-runner-02` | `visual_smoke.sh`, sekcja `[VERIFY] testy narzędzi` |
| `tunnel-alignment (L1_A)` | `github-runner-03` | `tunnel_alignment.sh L1_A`, `[VERIFY] zestaw testów Pythona` |
| `station-details` | `github-runner-04` | `station_details.sh`, `[VERIFY] Python tool suite` |

W każdym z czterech logów te same sześć wierszy, znak w znak:

```
  FAIL <import>test_ci_workflows: ModuleNotFoundError: No module named 'yaml'
  FAIL <import>test_docs_ci_claims: ModuleNotFoundError: No module named 'yaml'
  FAIL <import>test_timing_record: ModuleNotFoundError: No module named 'yaml'
  FAIL test_the_engine_probe_compares_the_reported_version_with_the_pin: No module named 'yaml'
  FAIL test_the_probe_normalises_the_release_tag_the_way_the_engine_reports_it: No module named 'yaml'
  FAIL test_wszystkie_workflowy_biora_PELNA_historie: No module named 'yaml'

  2386/2389 przeszło
```

**2386 z 2389 przechodziło, a każdy z trzech upadków nazywał `yaml`.** Ponowienie
(jedno, zgodnie z regułą) dało wynik **identyczny** — to nie było migotanie.

## 2. Dwie rzeczy, które ten pomiar mówi, a których nie mówił żaden log

**Luka jest FLOTOWA, nie jednomaszynowa.** Trzy maszyny z czterech w puli. Gdyby
brakowało na jednej, ponowienie trafiłoby prędzej czy później na zdrową i sprawa
wyglądałaby na migotanie — czyli na coś, czego się nie naprawia.

**Brak wychodził po ośmiu minutach PRACY, nie w sondzie.** `station-details`
i `tunnel-alignment` zdążyły wcześniej **poprawnie wyrenderować** geometrię:

```
[NORMALNE] material orientacji przypisany do 37 obiektow
[NORMALNE] PERON_normals.png tylna_strona=0.13791
[WYNIK] pass — {'total': 7, 'pass': 0, 'fail': 0, 'new_baseline': 7}
```

Cała wartość sondy jest w **momencie**, a nie w tym, że w ogóle pyta.

## 3. Dlaczego nie złapała tego żadna bramka — mechanizm, nie domysł

`probe-tools` sondowała **wyłącznie** biblioteki współdzielone i polecenia:

```
WANT_LIBRARIES: libEGL.so.1 libGL.so.1 libX11.so.6 libXext.so.6 libXrender.so.1
                libXfixes.so.3 libXi.so.6 libxkbcommon.so.0 libICE.so.6 libSM.so.6
WANT_COMMANDS:  curl
```

Ani jednego **modułu Pythona**. A job `tools` z `python-tests.yml` nie miał **ani
sondy, ani kroku instalacji w ogóle** — jedyne, co robił przed zestawem, to
`command -v python3` i `python3 -m compileall`.

**To trzeci raz ta sama klasa.** `unzip` doszedł do kodu 127 (07.09.2026), `curl`
do 6.D77 (10.09.2026). Oba działały wyłącznie dlatego, że maszyny puli miały je
z innych powodów. PyYAML był czwartą taką zależnością i pierwszą, która nie jest
poleceniem — dlatego żaden istniejący kształt sondy nie mógł jej zobaczyć.

## 4. Co weszło

- **`python-modules`** — nowe wejście `probe-tools`. Sondą jest **import**
  (`python3 -c "import X"`), a nie `dpkg -l` ani `pip show`: pakiet zainstalowany,
  lecz niewidoczny dla TEGO interpretera, jest dla zestawu takim samym brakiem jak
  brak pakietu, a `test_all.py` woła dokładnie ten interpreter.
- **`python3-yaml`** w `blender.txt`, `blender-xvfb.txt` i w **nowym** zestawie
  `tools/ci/apt-packages/python.txt`.
- **Job `tools` dostał pierwszą w swojej historii sondę i warunkową instalację.**
- **`MODULY_Z_PAKIETOW`** — tabela moduł → pakiet. **Nie jest tożsamościowa ani
  razu** (`yaml` → `python3-yaml`), inaczej niż `POLECENIA_Z_PAKIETOW`, gdzie
  tożsamościowe są dwa wpisy z trzech. Reguły mechanicznej świadomie nie ma:
  trafiałaby w PyYAML i myliła się na pierwszym module o innej nazwie pakietu.

## 5. Bramka, a nie sama poprawka konfiguracji

Poprawka gasi dzisiejszy pożar. Bez bramki nowy workflow wołający zestaw wchodzi
bez sondy i awaria wraca tą samą drogą.

`test_kazdy_workflow_uruchamiajacy_zestaw_SONDUJE_jego_zaleznosci` czyta zależności
**z AST**, nie z listy wpisanej do testu: `import yaml` w komentarzu albo w napisie
nie jest importem, a `from yaml import safe_load` jest. Odsiew idzie po
`sys.stdlib_module_names`, czyli po wiedzy interpretera, a nie po drugiej liście nazw.

Zmierzone: skan widzi **134** pliki `tools/tests/*.py` i oddaje **dokładnie jedną**
zależność spoza stdlib — `yaml`.

**Czego ta bramka NIE robi, i to jest wypisane, a nie przemilczane:** nie sprawdza,
czy pakiet jest na maszynie. Tego z repozytorium sprawdzić się nie da. Sprawdza, że
job **spyta, zanim zacznie pracę**.

## 6. Kontrole negatywne — pięć, każda z przewidywaniem PRZED przebiegiem

| | mutacja | przewidywanie | wynik |
|---|---|---|---|
| KN-1 | sonda modułu zdjęta z `blender-smoke.yml` | nowa bramka, nazywając ten workflow | **86/87, dokładnie tak** |
| KN-2 | `python3-yaml` zdjęty z `python.txt` | bramka „sonda pyta o to, czego zestaw nie instaluje” | **86/87, dokładnie tak** |
| KN-3 | pętla sondująca moduły zastąpiona `true` | **NIE WIEM — to było pytanie** | **87/87 ZIELONE** |
| KN-4 | sonda zawsze `missing` | przebieg pierwszy i trzeci | **87/88, przebieg pierwszy** |
| KN-5 | `python-tests.yml` cofnięty do stanu z 15.09 | nowa bramka na jobie `tools` | **81/88, SIEDEM bramek** |

### KN-3 obaliła przewidywanie i jest najcenniejsza

Oślepienie pętli sondującej moduły **wewnątrz akcji** przeszło **87/87 na zielono**.
Napis w pliku zostawał — opis wejścia, komentarz, wszystko — a sonda meldowała
`present` nad brakującym modułem. Bramka pytająca „czy w akcji stoi `python3 -c`"
przeszłaby tę mutację tak samo.

Domknięte bramką na **WYKONANIE** ciała sondy, nie na napis: `_uruchom_sonde` bierze
ciało kroku z akcji, uruchamia je w `bash` z podstawionym `GITHUB_OUTPUT` i czyta
`libs=`. Trzy przebiegi, bo dwa pierwsze osobno nic nie znaczą — sonda zawsze-`missing`
przeszłaby drugi, zawsze-`present` pierwszy:

```
moduł istniejący (`yaml`)           -> present
moduł losowy, nieistniejący         -> missing
listy puste                         -> present
```

Po tej bramce ta sama mutacja zapala:

```
FAIL test_sonda_modulow_NAPRAWDE_sonduje_a_nie_tylko_o_tym_pisze: sonda melduje
`present` dla modułu 'metro_bxl_modul_ktorego_nie_ma_bf69123934b34a08', którego NIE
MA — pętla sondująca moduły nie wykonuje się, więc instalacja nie odpali się nigdy
```

### KN-5 pokazuje, ile dziś kosztowałby stan z 15.09

Siedem bramek, w tym nowa, nazywająca winowajcę z imienia:

```
FAIL test_kazdy_workflow_uruchamiajacy_zestaw_SONDUJE_jego_zaleznosci:
  python-tests.yml:tools uruchamia zestaw testów, a nie sonduje jego zależności yaml
```

## 7. Dwie bramki złapały mnie przed werdyktem

Obie u mnie, obie słusznie, i obie są tą samą klasą, którą projekt tropi:

- **Mój czytnik zależności brał własne moduły projektu za obce.** `wlasne` liczyło
  tylko `tools/tests/*.py`, więc `braking`, `sweep`, `validate` i sześćdziesiąt innych
  modułów z `tools/track/` i `tools/blender/` wyszły jako „zależności spoza stdlib".
  Meldował **63** zamiast jednej. Gdyby nie zapaliła się nowa bramka, ta ślepota
  **stałaby się wynikiem** — dokładnie 6.D221, gdzie 22 „rozjazdy" okazały się wadą
  czytnika autora.
- **Przejście szło `os.walk` zamiast `tree_walk.walk`** — złapało
  `test_no_tool_walks_the_tree_without_the_shared_filter` (6.D36).

## 8. Weryfikacja

```
python3 tools/tests/test_all.py test_ci_workflows.py
  88/88 przeszło

python3 tools/tests/test_all.py
  2493/2493 przeszło,  RAZEM 207.595 s, 2493 testów, 126 modułów

dotnet test tests/Sim.Tests    Passed! - Failed: 0, Passed: 662, Total: 662
dotnet test tests/Game.Tests   Passed! - Failed: 0, Passed: 318, Total: 318
```

## 9. Rozluźnienie sufitu, wypisane wprost

Sufit joba `tools` idzie **15 → 35 minut**, i jest to rozluźnienie, a nie poprawka.
Powód jest wymuszony: `test_ci_step_budget_covers_a_slow_mirror` żąda, żeby po kroku
instalacji zostało jeszcze 10 minut, a sufit kroku musi pomieścić własny
`INSTALL_TIMEOUT_S` instalatora (1500 s). Stąd 25 na krok i 35 na job.

**Ochrona nie znika i to jest sprawdzalne:** czasu zestawu pilnuje osobno
`SUITE_CPU_BUDGET_S` z `tools/tests/test_suite_runtime_budget.py`, sprawdzany po
zakończeniu procesu — i to on, a nie sufit joba, jest tu bramką. Instalacja odpala się
wyłącznie przy braku, więc w zwykłym przebiegu job kończy się jak dotąd.

## 10. Czego świadomie nie zrobiłem

- **Nie zainstalowałem niczego na maszynach właściciela.** `CLAUDE.md` §8 mówi, że
  dodanie zależności jest miejscem, w którym się zatrzymuję i pytam; to jest zmiana
  w provisioningu cudzych maszyn, nie w repozytorium. Właściciel dostał osobny,
  wykonalny przepis.
- **Nie tknąłem `POLECENIA_Z_PAKIETOW`** — moduły dostały własną tabelę, bo nazwa
  modułu i nazwa pakietu to dwie różne rzeczy.
- **Nie sonduję WERSJI modułów.** Dziś żadna bramka wersji PyYAML nie wymaga,
  a sonda wersji byłaby zapadką do utrzymywania bez powodu.
- **Nie poszerzyłem sondy o `.NET` ani Godota** — oba mają własne instalatory będące
  własnymi sondami.

## 11. Co zauważyłem przy okazji, ale nie tknąłem

- **`MODULY_Z_PAKIETOW` nie jest tożsamościowa ani razu**, a `POLECENIA_Z_PAKIETOW`
  jest w dwóch wpisach z trzech. Znaczy to, że reguła mechaniczna, która dla poleceń
  jest kuszące i prawie zawsze poprawna, dla modułów jest od początku nie do napisania.
- **Sonda nie ma kontroli przyrządu na gałąź bibliotek ani poleceń.** KN-3 pokazała
  ją dla modułów; dla `ldconfig` i `command -v` nadal stoi wyłącznie
  `assert "ldconfig" in body`, czyli bramka na NAPIS. `_uruchom_sonde` jest już
  napisana i przyjmuje oba wejścia, więc domknięcie tego jest tanie — ale to osobna
  pozycja, nie przypis do tej.
- **Żaden workflow nie sprawdza, czy interpreter, który sonduje, jest tym samym,
  który uruchamia zestaw.** Dziś to ten sam `python3` z `PATH`, ale nic tego nie
  pilnuje.
