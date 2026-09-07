# Ramka w ścieżce `bin/` a plik projektu — bramka (6.A31)

**Zmierzone 07.09.2026 na commicie:** `aa64156ce02d00c1396911623919bca6e088bfa8`
(baza gałęzi `claude/6a31-ramka-w-sciezce`, czyli `main` po scaleniu #373).

Bramka: `tools/tests/test_bin_path_framework.py`, 12 testów.
Adnotacje: `reports/T-311-braking.md` §5.1 i `reports/T-400-first-run.md` §3.1.

---

## 1. Skąd wzięła się pozycja i co w jej opisie było nieścisłe

Pozycja 6.A31 stoi na znalezisku zostawionym przy 6.A26 (§9
`reports/pomiar-rownosci.md`):

```
reports/T-311-braking.md:257    Sim.Runner/bin/Release/net8.0/…
reports/T-400-first-run.md:235  Sim.Runner/bin/Release/net8.0/…
reports/linecore-budget.md:91   Sim.Runner/bin/Release/net10.0/…
```

**Sprostowanie do tamtego zapisu, i to jest pierwsze ustalenie tej pozycji.** 6.A26
nazwało dwa pierwsze wystąpienia „komendami". Komendami nie są. Oba to wiersze
z **cytowanego wyjścia** `dotnet build`, postaci `Sim.Runner -> …dll`; wołaniem jest
tam nagłówek sekcji, a on żadnej ścieżki `bin/` nie nosi. Jedyna ścieżka `bin/` stojąca
w prawdziwej komendzie w całym drzewie to trzecia z tej listy —
`reports/linecore-budget.md:91` — i ona jest **zgodna**.

Rozróżnienie nie jest pedantyczne, bo od niego zależy wyrok. Cytat wyjścia jest
pomiarem z datą i przeliczać go nie wolno. Komenda jest przepisem do powtórzenia
i martwa ścieżka w niej jest awarią u każdego, kto ją wpisze. Bramka musi więc
rozdzielać jedno od drugiego, a nie liczyć „wystąpienia `net8.0`".

## 2. Pomiar na drzewie bazowym (`aa64156`, przed tym commitem)

Wypis `python3 tools/tests/test_bin_path_framework.py --inwentarz`, wykonany na
gałęzi przed dopisaniem adnotacji i tego raportu:

```
TargetFramework z src/Sim.Runner/Sim.Runner.csproj: net10.0

  ZGLOSZONA docs/TASKS.md:736                  net8.0 proza/cytat  Sim.Runner/bin/Release/net8.0
  ZGLOSZONA docs/TASKS.md:746                  net8.0 proza/cytat  Sim.Runner/bin/Release/net8.0
  ZGLOSZONA docs/TASKS.md:4052                 net8.0 proza/cytat  Sim.Runner/bin/Release/net8.0
  ZGLOSZONA docs/TASKS.md:4053                 net8.0 proza/cytat  Sim.Runner/bin/Release/net8.0
  zgodna  docs/TASKS.md:4054                 net10.0 proza/cytat  Sim.Runner/bin/Release/net10.0
  ZGLOSZONA reports/T-310-physics.md:247       net8.0 proza/cytat  src/Sim/bin/Release/net8.0
  ZGLOSZONA reports/T-310-physics.md:248       net8.0 proza/cytat  tests/Sim.Tests/bin/Release/net8.0
  ZGLOSZONA reports/T-311-braking.md:256       net8.0 proza/cytat  src/Sim/bin/Release/net8.0
  ZGLOSZONA reports/T-311-braking.md:257       net8.0 proza/cytat  src/Sim.Runner/bin/Release/net8.0
  ZGLOSZONA reports/T-311-braking.md:258       net8.0 proza/cytat  tests/Sim.Tests/bin/Release/net8.0
  ZGLOSZONA reports/T-400-first-run.md:234     net8.0 proza/cytat  src/Sim/bin/Release/net8.0
  ZGLOSZONA reports/T-400-first-run.md:235     net8.0 proza/cytat  src/Sim.Runner/bin/Release/net8.0
  ZGLOSZONA reports/T-400-first-run.md:236     net8.0 proza/cytat  tests/Sim.Tests/bin/Release/net8.0
  zgodna  reports/linecore-budget.md:91      net10.0 KOMENDA      src/Sim.Runner/bin/Release/net10.0
  zgodna  reports/mutacje-rdzen-sygnalizacji.md:695 net10.0 proza/cytat  .../src/Sim/bin/Debug/net10.0
  zgodna  reports/mutacje-rdzen-sygnalizacji.md:696 net10.0 proza/cytat  .../tests/Sim.Tests/bin/Debug/net10.0
  ZGLOSZONA reports/pomiar-rownosci.md:177     net8.0 proza/cytat  Sim.Runner/bin/Release/net8.0
  ZGLOSZONA reports/pomiar-rownosci.md:178     net8.0 proza/cytat  Sim.Runner/bin/Release/net8.0
  zgodna  reports/pomiar-rownosci.md:179     net10.0 proza/cytat  Sim.Runner/bin/Release/net10.0

  wszystkich sciezek `bin/…/netX.Y/`: 19 w 7 plikach
  zgodnych z net10.0: 5
  ZGLOSZONYCH (niezgodnych): 14
    z tego w polu „Weryfikacja": 0
    z tego w wierszu, ktory JEST komenda: 0
    z tego w prozie albo w cytacie wyjscia: 14
  usprawiedliwien na liscie: 14 (zapadka 14)
  BEZ usprawiedliwienia: 0
```

**Dwie liczby, o które pytała pozycja:**

| co | ile |
|---|---|
| ścieżek `bin/…/netX.Y/` w `reports/` i `docs/` | **19** w 7 plikach |
| z tego niezgodnych z `<TargetFramework>` (`net10.0`) | **14** |
| **z tego w polu „Weryfikacja"** | **0** |
| z tego w wierszu, który JEST komendą | **0** |
| z tego w prozie albo w cytacie wyjścia `dotnet build` | **14** |

Pozycja przewidywała trzy ścieżki i pytała, ile ich naprawdę jest. Jest ich
**czternaście**, w pięciu plikach: trzy trafienia więcej niż w 6.A26 tylko dlatego, że
tamten pomiar szukał wyłącznie wołań `Sim.Runner`, a `reports/T-310-physics.md` niesie
`src/Sim/…` i `tests/Sim.Tests/…` bez wiersza runnera (T-310 powstało, gdy runnera
jeszcze nie było). Do tego dwa cytaty w `reports/pomiar-rownosci.md`, dwa w polu „Skąd"
bloku 6.A31 i dwa w wierszach tabeli fazy 6.

**Groźnych jest zero.** Ani jedna niezgodna ścieżka nie stoi w polu „Weryfikacja"
i ani jedna nie stoi w wierszu, który jest wołaniem. To jest wynik pomiaru, nie
domysł — i to jest powód, dla którego oba twarde szczeble bramki mają **kontrolę
dodatnią na wejściu wstrzykniętym** (§5). Bramka, której zielony kolor bierze się
z pustego zbioru, nie jest zweryfikowana.

## 3. Co bramka robi

`TargetFramework` jest **wyprowadzany z pliku projektu**, nie wpisany z pamięci:

```python
PROJECT = os.path.join("src", "Sim.Runner", "Sim.Runner.csproj")

def target_framework(text=None):
    if text is None:
        text = _read(os.path.join(ROOT, PROJECT))
    match = re.search(r"<TargetFramework>\s*(net[0-9]+\.[0-9]+)\s*</TargetFramework>", text)
    return match.group(1) if match else None
```

Każde wystąpienie ścieżki `bin/…/netX.Y/` w `reports/**/*.md` i `docs/**/*.md` dostaje
wyrok na jednym z trzech szczebli:

| szczebel | co to jest | wyrok |
|---|---|---|
| 1 | ścieżka w polu „Weryfikacja" bloku `docs/TASKS.md` | twardy błąd, **bez usprawiedliwienia** |
| 2 | ścieżka w wierszu, który JEST wołaniem programu | twardy błąd, **bez usprawiedliwienia** |
| 3 | ścieżka w prozie albo w cytacie wyjścia `dotnet build` | pomiar z datą — usprawiedliwienie z powodem + adnotacja |

Szczebel 3 to na przykład `reports/T-311-braking.md` §5.1, gdzie cytat wyjścia
`dotnet build` z dnia pomiaru niesie trzy takie ścieżki naraz:

```
  Sim -> src/Sim/bin/Release/net8.0/MetroBxl.Sim.dll
  Sim.Runner -> src/Sim.Runner/bin/Release/net8.0/MetroBxl.Sim.Runner.dll
  Sim.Tests -> tests/Sim.Tests/bin/Release/net8.0/MetroBxl.Sim.Tests.dll
```

Tych liczb i tego cytatu **nie przeliczono** — pole „Poza zakresem" pozycji mówi to
wprost, a `CLAUDE.md` §4 tak samo. Oba raporty wskazane w polu „Wejście" dostały
adnotację, która mówi czytelnikowi, że katalog `net8.0` dziś nie powstaje, i wskazuje
bramkę oraz ten raport.

**Czego bramka nie ogląda, świadomie.** Wystąpień `netX.Y` bez segmentu `bin/`.
Wiersz `Passed! … - MetroBxl.Sim.Tests.dll (net8.0)` jest cytatem wyjścia
`dotnet test` o tym, na czym testy **wtedy** chodziły, a nie ścieżką do katalogu;
takich wierszy jest w `reports/` kilkanaście i zgłaszanie ich zamieniłoby bramkę
w szum. Granicę przybija `test_a_framework_without_a_bin_segment_is_out_of_scope`
na wejściu syntetycznym, w obie strony.

Bramka **nie uruchamia komend** i nie sprawdza, czy działają — to jest bramka na
spójność ścieżki z plikiem projektu, nie na wykonanie (pole „Poza zakresem").

## 4. Lista usprawiedliwień i jej zapadka

Czternaście zgłoszeń szczebla 3 stoi na zamkniętej liście `JUSTIFICATIONS`, klucz
**(ścieżka pliku, przedrostek ścieżki `bin/`)**. Klucz nie zawiera numeru wiersza,
bo numer przesuwa każdy commit dopisujący cokolwiek wyżej, a bramka zapalająca się
na tekście poprawnym zostaje wyłączona, nie naprawiona (6.D27, 6.A26).

Dwa testy pilnują listy, oba wzorem 6.D29 i 6.B34:

* `test_every_justification_still_describes_a_path_that_exists` — usprawiedliwienie
  nie przeżyje ścieżki, którą opisuje, a powód musi mieć co najmniej 40 znaków;
* `test_the_justification_list_stays_closed` — zapadka `MAX_JUSTIFICATIONS = 14`
  z obu stron: lista nie może urosnąć po cichu **ani** zapadka stać wyżej niż lista
  („miejsce na zapas" jest tym samym błędem, tylko odwróconym).

Cztery z czternastu wpisów dotyczą **tego raportu**, bo raport cytuje wyjście własnej
bramki i wstrzyknięte wejścia kontroli. **Bramka, która liczy także siebie, ma to
powiedzieć wprost** — zasada z 6.A26. Alternatywą byłby raport bez wklejonego wyjścia
weryfikacji, czego `CLAUDE.md` §5 zabrania.

## 5. Kontrole — WYKONANE

### 5.1 KD-1 (dodatnia, szczebel 1 + 2): komenda `net8.0` w polu „Weryfikacja"

W pole „Weryfikacja" bloku 6.A31 w `docs/TASKS.md` wstrzyknięty jeden wiersz:

```diff
   python3 tools/tests/test_all.py test_report_hygiene.py
+  dotnet src/Sim.Runner/bin/Release/net8.0/MetroBxl.Sim.Runner.dll budget --line L1
   python3 tools/tests/test_all.py
```

```
$ python3 tools/tests/test_all.py test_bin_path_framework.py
  ok   test_a_command_is_told_apart_from_quoted_build_output
  ok   test_a_framework_without_a_bin_segment_is_out_of_scope
  ok   test_a_matching_directory_is_never_reported
  FAIL test_every_stale_path_in_prose_is_justified: ścieżka z martwym `netX.Y` bez usprawiedliwienia i bez adnotacji: ['docs/TASKS.md:4077 src/Sim.Runner/bin/Release/net8.0 (net8.0)']
  FAIL test_no_command_cites_a_stale_framework_directory: komenda woła katalog, którego budowanie nie tworzy (net10.0): ['docs/TASKS.md:4077 src/Sim.Runner/bin/Release/net8.0 (net8.0)']
  FAIL test_no_verification_field_cites_a_stale_framework_directory: pole „Weryfikacja" cytuje katalog, którego budowanie nie tworzy (net10.0): ['docs/TASKS.md:4077 src/Sim.Runner/bin/Release/net8.0 (net8.0)']
  ok   test_the_justification_list_stays_closed
  ok   test_the_project_file_still_declares_a_target_framework
  ok   test_the_verdict_follows_the_project_file
  ok   test_the_verification_field_is_cut_the_same_way_as_in_backlog_commands
```

**Zgłoszona z plikiem i numerem wiersza — `docs/TASKS.md:4077` — na obu twardych
szczeblach naraz.** Plik przywrócony z kopii, `git status` czysty.

### 5.2 KD-2 (dodatnia, szczebel 2 sam): jedyna prawdziwa komenda, jeden znak zmiany

W `reports/linecore-budget.md:91` przestawiona **wyłącznie wersja ramki** w ścieżce
prawdziwego wołania:

```diff
-dotnet src/Sim.Runner/bin/Release/net10.0/MetroBxl.Sim.Runner.dll budget \
+dotnet src/Sim.Runner/bin/Release/net8.0/MetroBxl.Sim.Runner.dll budget \
```

```
  FAIL test_every_stale_path_in_prose_is_justified: ścieżka z martwym `netX.Y` bez usprawiedliwienia i bez adnotacji: ['reports/linecore-budget.md:91 src/Sim.Runner/bin/Release/net8.0 (net8.0)']
  FAIL test_no_command_cites_a_stale_framework_directory: komenda woła katalog, którego budowanie nie tworzy (net10.0): ['reports/linecore-budget.md:91 src/Sim.Runner/bin/Release/net8.0 (net8.0)']
  ok   test_no_verification_field_cites_a_stale_framework_directory
  8/12 przeszło
```

Ta kontrola jest **jednocześnie najostrzejszą kontrolą ujemną, jaką dało się tu
zrobić**: ten sam wiersz, ten sam plik, ta sama pozycja — różnica jednego znaku
w numerze wersji przenosi go z „zgodna" (§2, wypis bazowy) do zgłoszenia. Szczebel 1
został przy tym **zielony**, bo wiersz nie stoi w polu „Weryfikacja", i to jest
poprawne. Plik przywrócony.

### 5.3 KD-3 (dodatnia, szczebel 3): cytat wyjścia w pliku bez usprawiedliwienia

Do `reports/coasting.md` wstrzyknięty jeden wiersz cytatu `dotnet build`:

```diff
 Passed!  - Failed:     0, Passed:   546, Skipped:     0, Total:   546, Duration: 14 s - MetroBxl.Sim.Tests.dll (net10.0)
+  Sim.Tests -> tests/Sim.Tests/bin/Release/net8.0/MetroBxl.Sim.Tests.dll
```

```
  FAIL test_every_stale_path_in_prose_is_justified: ścieżka z martwym `netX.Y` bez usprawiedliwienia i bez adnotacji: ['reports/coasting.md:210 tests/Sim.Tests/bin/Release/net8.0 (net8.0)']
  ok   test_no_command_cites_a_stale_framework_directory
  ok   test_no_verification_field_cites_a_stale_framework_directory
  9/12 przeszło
```

Zapala się **tylko** szczebel 3, i to jest cała różnica między nim a KD-2: wiersz
`Sim.Tests -> …` komendą nie jest. Plik przywrócony.

### 5.4 KU (ujemna): ani jedna ścieżka `net10.0` nie jest zgłaszana

Na dzisiejszym drzewie jest **pięć** ścieżek `bin/…/net10.0/`, w tym jedna w prawdziwej
komendzie (`reports/linecore-budget.md:91`, `dotnet …budget`) i dwie z podpisem
`.../` (`reports/mutacje-rdzen-sygnalizacji.md`). W wypisie z §2 wszystkie pięć stoi
jako `zgodna` i żadna nie trafia do zgłoszeń. Bramka łapiąca ścieżkę **poprawną**
zostałaby wyłączona w tym samym tygodniu (6.D27).

Samo „nic się nie zgłasza" niczego nie dowodzi, więc kontrola została wykonana także
w drugą stronę — mutacja jednego operatora w bramce, `!=` na `==`:

```diff
-  "stale": ("net" + match.group("version")) != tfm,
+  "stale": ("net" + match.group("version")) == tfm,
```

```
  wszystkich sciezek `bin/…/netX.Y/`: 19 w 7 plikach
  zgodnych z net10.0: 14
  ZGLOSZONYCH (niezgodnych): 5
    z tego w polu „Weryfikacja": 0
    z tego w wierszu, ktory JEST komenda: 1
    z tego w prozie albo w cytacie wyjscia: 4
  BEZ usprawiedliwienia: 5
    docs/TASKS.md:4054 Sim.Runner/bin/Release/net10.0 (net10.0)
    reports/linecore-budget.md:91 src/Sim.Runner/bin/Release/net10.0 (net10.0)
    reports/mutacje-rdzen-sygnalizacji.md:695 .../src/Sim/bin/Debug/net10.0 (net10.0)
    reports/mutacje-rdzen-sygnalizacji.md:696 .../tests/Sim.Tests/bin/Debug/net10.0 (net10.0)
    reports/pomiar-rownosci.md:179 Sim.Runner/bin/Release/net10.0 (net10.0)
```

Zbiór zgłoszeń przeszedł dokładnie na te pięć ścieżek, a `7/12` testów zostało —
w tym `test_a_matching_directory_is_never_reported`, który jest bramką tej właśnie
własności. Operator przywrócony.

### 5.5 KP (kontrola przyrządu): wyrok idzie za plikiem projektu

`<TargetFramework>` w `src/Sim.Runner/Sim.Runner.csproj` podmieniony **tymczasowo**
z `net10.0` na `net8.0`, bez żadnej innej zmiany w drzewie:

```
$ python3 tools/tests/test_bin_path_framework.py --inwentarz
TargetFramework z src/Sim.Runner/Sim.Runner.csproj: net8.0

  zgodna  docs/TASKS.md:736                  net8.0 proza/cytat  Sim.Runner/bin/Release/net8.0
  ...
  ZGLOSZONA docs/TASKS.md:4054                 net10.0 proza/cytat  Sim.Runner/bin/Release/net10.0
  ...
  ZGLOSZONA reports/linecore-budget.md:91      net10.0 KOMENDA      src/Sim.Runner/bin/Release/net10.0
  ZGLOSZONA reports/mutacje-rdzen-sygnalizacji.md:695 net10.0 proza/cytat  .../src/Sim/bin/Debug/net10.0
  ZGLOSZONA reports/mutacje-rdzen-sygnalizacji.md:696 net10.0 proza/cytat  .../tests/Sim.Tests/bin/Debug/net10.0
  ZGLOSZONA reports/pomiar-rownosci.md:179     net10.0 proza/cytat  Sim.Runner/bin/Release/net10.0

  wszystkich sciezek `bin/…/netX.Y/`: 19 w 7 plikach
  zgodnych z net8.0: 14
  ZGLOSZONYCH (niezgodnych): 5
    z tego w polu „Weryfikacja": 0
    z tego w wierszu, ktory JEST komenda: 1
    z tego w prozie albo w cytacie wyjscia: 4
```

**14 zgłoszeń zamieniło się w 5, i to dokładnie te przeciwne.** Bez tej kontroli
„bramka wyprowadzająca `netX.Y` z pliku projektu" byłaby nieodróżnialna od stałej
`net10.0` wpisanej z pamięci — obie dają na dzisiejszym drzewie ten sam zbiór zgłoszeń.
Pilnuje tego na stałe `test_the_verdict_follows_the_project_file`. Plik projektu
przywrócony z kopii; `git diff src/` puste.

### 5.6 KW (kontrola wzorca): próg na łączną liczbę dopasowań

Wzorzec zepsuty jedną literą, `bin/` na `bim/`:

```diff
-    r"(?P<prefix>[A-Za-z0-9._+/-]*bin/(?:[A-Za-z0-9._+-]+/)*?net(?P<version>\d+\.\d+))(?=/)")
+    r"(?P<prefix>[A-Za-z0-9._+/-]*bim/(?:[A-Za-z0-9._+-]+/)*?net(?P<version>\d+\.\d+))(?=/)")
```

```
  ok   test_a_command_is_told_apart_from_quoted_build_output
  FAIL test_a_framework_without_a_bin_segment_is_out_of_scope:
  FAIL test_a_matching_directory_is_never_reported: []
  FAIL test_every_justification_still_describes_a_path_that_exists: usprawiedliwienie bez ścieżki, którą opisuje: [('docs/TASKS.md', 'Sim.Runner/bin/Release/net8.0'), ('reports/T-310-physics.md', 'src/Sim/bin/Release/net8.0'), ('reports/T-310-physics.md', 'tests/Sim.Tests/bin/Release/net8.0'), ('reports/T-311-braking.md', 'src/Sim.Runner/bin/Release/net8.0'), ('reports/T-311-braking.md', 'src/Sim/bin/Release/net8.0'), ('reports/T-311-braking.md', 'tests/Sim.Tests/bin/Release/net8.0'), ('reports/T-400-first-run.md', 'src/Sim.Runner/bin/Release/net8.0'), ('reports/T-400-first-run.md', 'src/Sim/bin/Release/net8.0'), ('reports/T-400-first-run.md', 'tests/Sim.Tests/bin/Release/net8.0'), ('reports/pomiar-rownosci.md', 'Sim.Runner/bin/Release/net8.0'), ('reports/ramka-w-sciezce.md', 'Sim.Runner/bin/Release/net8.0'), ('reports/ramka-w-sciezce.md', 'src/Sim.Runner/bin/Release/net8.0'), ('reports/ramka-w-sciezce.md', 'src/Sim/bin/Release/net8.0'), ('reports/ramka-w-sciezce.md', 'tests/Sim.Tests/bin/Release/net8.0')]
  ok   test_every_stale_path_in_prose_is_justified
  ok   test_no_command_cites_a_stale_framework_directory
  ok   test_no_verification_field_cites_a_stale_framework_directory
  ok   test_the_justification_list_stays_closed
  ok   test_the_project_file_still_declares_a_target_framework
  FAIL test_the_scan_sees_the_measured_number_of_paths: wzorzec złapał 0 ścieżek `bin/…/netX.Y/`, a 07.09.2026 było ich 29 — spadek znaczy zepsuty wzorzec, nie posprzątane drzewo
  FAIL test_the_verdict_follows_the_project_file: przy net10.0 bramka nie zgłasza niczego — nie ma czego porównywać
  ok   test_the_verification_field_is_cut_the_same_way_as_in_backlog_commands

  7/12 przeszło
```

**Trzy testy szczeblowe zostały ZIELONE** — `test_no_verification_field_…`,
`test_no_command_…` i `test_every_stale_path_in_prose_is_justified`. Zero dopasowań
to zero zgłoszeń, więc każdy z nich przechodzi bezmyślnie. To jest najczęstszy sposób,
w jaki bramka kłamie w stronę „wszystko w porządku", i **jedyny powód, dla którego
próg `MIN_PATHS_IN_TREE` istnieje osobno**. Wzorzec przywrócony.

## 6. Weryfikacja — rzeczywiste wyjście

### 6.1 `python3 tools/tests/test_all.py test_bin_path_framework.py`

```
  ok   test_a_command_is_told_apart_from_quoted_build_output
  ok   test_a_framework_without_a_bin_segment_is_out_of_scope
  ok   test_a_matching_directory_is_never_reported
  ok   test_every_justification_still_describes_a_path_that_exists
  ok   test_every_stale_path_in_prose_is_justified
  ok   test_no_command_cites_a_stale_framework_directory
  ok   test_no_verification_field_cites_a_stale_framework_directory
  ok   test_the_justification_list_stays_closed
  ok   test_the_project_file_still_declares_a_target_framework
  ok   test_the_scan_sees_the_measured_number_of_paths
  ok   test_the_verdict_follows_the_project_file
  ok   test_the_verification_field_is_cut_the_same_way_as_in_backlog_commands

  12/12 przeszło
```

### 6.2 `python3 tools/tests/test_all.py` — kod wyjścia

```
$ python3 tools/tests/test_all.py > /tmp/suite.txt 2>&1 ; echo "kod: $?"
kod: 0
$ grep -E '^\s*FAIL|^\s*SKIP|przeszło|RAZEM' /tmp/suite.txt
  1898/1898 przeszło
  RAZEM 74.979 s, 1898 testów, 100 modułów
```

**Kod wyjścia 0, zero `FAIL`, zero `SKIP`.** Patrzę na kod wyjścia, nie na grep — grep
po `FAIL` nie widzi modułu, który nie zaimportował się, a `test_all.main()` w takim
przypadku i tak zwraca 1 (`docs/TASKS.md`, 6.D15).

**Rozmiar zestawu zmierzony w obie strony, nie odjęty w głowie.** Przebieg z tym
plikiem odłożonym poza `tools/tests/`:

```
  1885/1886 przeszło
  RAZEM 71.350 s, 1886 testów, 99 modułów
```

czyli **1886 → 1898 testów, 99 → 100 modułów**. Ten sam przebieg dał przy okazji
niezamierzoną kontrolę cudzej bramki: po zabraniu pliku
`test_kazda_sciezka_wymieniona_w_raporcie_rozwiazuje_sie_w_drzewie`
z `test_report_hygiene.py` zgłosiło trzy ścieżki, których nie ma w drzewie —
dwie adnotacje i nagłówek tego raportu wskazują na bramkę, więc raport i bramka
muszą wejść jednym commitem. Weszły.


### 6.3 `dotnet test tests/Sim.Tests` — NIE wykonane, i to jest zapisane, nie pominięte

```
$ command -v dotnet || echo "dotnet: BRAK"
dotnet: BRAK
$ bash doctor.sh
  BRAK  dotnet SDK  -> zainstaluj .NET SDK 10.0+ (https://dotnet.microsoft.com/download)
  ...
Testy rdzenia symulacji:
  pomijam — brak dotnet
```

Ten commit nie zmienia ani jednego pliku `.cs` ani `.csproj` (`git diff --stat` niżej),
a pole „Weryfikacja" pozycji 6.A31 wymienia wyłącznie dwie komendy `test_all.py`.
Zapisuję to jednak wprost, bo „testy C# przeszły" byłoby tu zdaniem, którego nie
zmierzyłem. Podmiana `TargetFramework` z §5.5 była wyłącznie odczytem tekstowym —
niczego nie budowałem i niczym nie uruchamiałem.

## 7. Pomiar na drzewie, które idzie do scalenia

Bramka liczy także własny raport i **mówi to wprost** — zasada z 6.A26. Wypis
`python3 tools/tests/test_bin_path_framework.py --inwentarz` na drzewie, które idzie
do scalenia (baza `aa64156` plus ten commit):

```
  wszystkich sciezek `bin/…/netX.Y/`: 29 w 8 plikach
  zgodnych z net10.0: 7
  ZGLOSZONYCH (niezgodnych): 22
    z tego w polu „Weryfikacja": 0
    z tego w wierszu, ktory JEST komenda: 0
    z tego w prozie albo w cytacie wyjscia: 22
  usprawiedliwien na liscie: 14 (zapadka 14)
  BEZ usprawiedliwienia: 0
```

**Przyrost 19 → 29 jest rozliczony po plikach, nie zgadnięty:**

| plik | +ścieżek | z tego niezgodnych | dlaczego |
|---|---|---|---|
| `reports/ramka-w-sciezce.md` | +10 | 8 | cytat znaleziska 6.A26 (§1, 3), cytat `dotnet build` z T-311 (§3, 3), wstrzyknięte wejścia KD-1/KD-2/KD-3 (4) |
| `docs/TASKS.md` | 0 | 0 | wiersz 6.A31 przepisany, liczba cytatów ścieżki bez zmian |

Osiem z tych dziesięciu jest niezgodnych i stoi pod czterema kluczami
usprawiedliwień — po jednym na przedrostek, nie po jednym na wiersz. Dwa pozostałe
(`…net10.0/…`) są zgodne. **Zero w polu „Weryfikacja", zero w komendzie** także po
tym commicie: wstrzyknięte komendy stoją w raporcie jako wiersze płotka `diff`,
z wiodącym `+` albo `-`, więc `is_command` ich za wołania nie bierze — i to jest
własność zmierzona wypisem wyżej, nie założenie.

Próg `MIN_PATHS_IN_TREE` postawiony na **29**, `MIN_FILES_WITH_PATHS` na **8**,
zapadka `MAX_JUSTIFICATIONS` na **14** — wszystkie trzy na stanie faktycznym, żadna
„na zapas". Zapadka jest sprawdzana z obu stron, więc podniesienie jej bez wpisu
na liście wywraca `test_the_justification_list_stays_closed`.


## 8. Czego świadomie nie zrobiłem

* **Nie przeliczyłem ani jednego pomiaru** w `reports/T-310-physics.md`,
  `reports/T-311-braking.md`, `reports/T-400-first-run.md` i
  `reports/pomiar-rownosci.md`. Pole „Poza zakresem" pozycji mówi to wprost: te
  raporty mają datę i cytat wyjścia jest ich treścią, nie ozdobą.
* **Nie ruszyłem `<TargetFramework>`.** Podmiana w §5.5 była tymczasowa, plik
  przywrócony z kopii przed pierwszym commitem.
* **Nie sprawdzałem, czy komendy działają.** Bramka porównuje ścieżkę z plikiem
  projektu; wykonanie jest poza zakresem pozycji.
* **`reports/T-310-physics.md` nie dostało adnotacji**, choć niesie dwie niezgodne
  ścieżki. Pole „Wejście" pozycji wymienia trzy raporty i tego wśród nich nie ma,
  a `CLAUDE.md` §4.10 zabrania poprawiania przy okazji plików spoza zadania. Zgłoszenia
  z tego pliku stoją na liście usprawiedliwień z powodem i z tą przyczyną wypisaną.
* **Nie rozszerzyłem skanu poza `reports/` i `docs/`.** Tak mówi pole „Wyjście".
  Pomiar szerszy wykonałem osobno i jest w §9 — poza tymi dwoma katalogami nie ma dziś
  ani jednej ścieżki `bin/…/netX.Y/`, więc rozszerzenie skanu nie zmieniłoby dziś
  żadnej liczby.

## 9. Zauważone przy okazji, nietknięte

* **Poza `reports/` i `docs/` nie ma ani jednej takiej ścieżki.** `grep` po
  `tools/`, `src/`, `tests/`, `.github/` i plikach w korzeniu daje zero trafień —
  workflow i skrypty wołają runnera przez `dotnet run --project` albo przez
  `${GODOT_BIN}`/`${BLENDER_BIN}`, nigdy przez ścieżkę do DLL. Ryzyko, którego ta
  pozycja dotyczy, żyje więc dziś wyłącznie w prozie i w polach `docs/TASKS.md`.
* **`reports/mutacje-rdzen-sygnalizacji.md` cytuje ścieżki z przedrostkiem `.../`**,
  czyli obciętym przez narzędzie. Bramka bierze je poprawnie (segment `bin/` jest
  na miejscu), ale klucz usprawiedliwienia dla takiego wystąpienia nosiłby w sobie
  wielokropek. Dziś to bez znaczenia, bo te dwie ścieżki są zgodne.
* **`reports/T-400-stage-3b.md`, `reports/energy-balance.md`,
  `reports/negative-control-audit-tresc.md`, `reports/coasting.md`,
  `reports/typy-sim-bez-testu.md` i `reports/polecenia-runnera-bez-testu.md`** niosą
  `(net10.0)` w cytatach wyjścia `dotnet test` — bez segmentu `bin/`, więc świadomie
  poza zasięgiem tej bramki. Gdyby kiedyś ktoś chciał pilnować i tego, będzie to inna
  bramka i inna pozycja: te wiersze mówią, na czym testy **chodziły**, a nie gdzie
  leży katalog.
