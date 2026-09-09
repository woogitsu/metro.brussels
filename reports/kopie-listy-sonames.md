# Kopie listy sonames i bramka na ich zgodność (6.D44)

**Zmierzone 09.09.2026 na:** `d51b5df`.
**Przyrząd:** `git grep -l`, parser YAML-a po krokach wołających akcję sondującą,
oraz `python3 tools/tests/test_all.py test_ci_workflows.py`.

---

## 1. Ile jest kopii — i sprostowanie liczby z treści pozycji

Treść 6.D44 mówiła o **dziewięciu** kopiach: siedmiu workflowach, jednej akcji
składanej i jednym module testowym. **Pomiar daje inny podział**, i różnica jest
merytoryczna, nie rachunkowa.

Napis `libEGL.so.1` niesie w drzewie **trzynaście** plików:

```
.github/actions/probe-tools/action.yml
.github/workflows/blender-smoke.yml
.github/workflows/godot-first-run.yml
.github/workflows/m7-shell.yml
.github/workflows/material-style-smoke.yml
.github/workflows/station-details.yml
.github/workflows/tunnel-alignment.yml
.github/workflows/visual-regression.yml
docs/TASKS.md
reports/biblioteki-startowe-blendera.md
reports/pusta-wersja-blendera.md
reports/sonda-jednej-biblioteki.md
tools/tests/test_ci_workflows.py
```

**Kopią listy jest z tego siedem.** Kopią jest **niepusta wartość `libraries:`**
przekazywana akcji sondującej, bo to ona decyduje, o co job pyta `ldconfig`:

```yaml
libraries: libEGL.so.1 libGL.so.1 libX11.so.6 libXext.so.6 libXrender.so.1 libXfixes.so.3 libXi.so.6 libxkbcommon.so.0 libICE.so.6 libSM.so.6
```

Pozostałe sześć plików wymienia **jedną** nazwę w prozie:
`action.yml` w opisie wejścia jako przykład („np. `libEGL.so.1`") i w komentarzu
o dopasowaniu do pełnego pola nazwy; `test_ci_workflows.py` w docstringu
`_debian_package_for`; `docs/TASKS.md` i trzy raporty w zapisach pomiarów. **Żaden
z nich nie jest listą** i objęcie ich bramką zgodności byłoby fałszywym alarmem.

**Dzisiejszy stan: siedem kopii, jeden zestaw, dziesięć sonames, zgodne co do
znaku.** Żadna kopia nie różni się od pozostałych.

## 2. Osobno stoją dwie listy w formie POCHODNEJ

`tools/ci/apt-packages/blender.txt` i `blender-xvfb.txt` niosą **pakiety**, nie
sonames — forma pochodna, wyprowadzona regułą `_debian_package_for`
(`libEGL.so.1` → `libegl1`, `libX11.so.6` → `libx11-6`). Nie są kopiami listy
sonames i nie wchodzą do tej bramki, bo związek sonames↔pakiety jest **już
pilnowany**: `test_tool_installation_is_conditional_on_the_tool_being_missing`
sprawdza dla każdego workflow, że każdy sondowany soname mapuje się na pakiet
z zestawu apt, który ten sam workflow instaluje.

`blender.txt` ma przy tym **jedenaście** pakietów, nie dziesięć: dochodzi
`libgl1-mesa-dri`, który nie odpowiada żadnemu soname z domknięcia startowego
(`dpkg -L` nie daje ani jednego pliku `libGL.so`) i jest tam z innego powodu,
opisanego w nagłówku tamtego pliku.

## 3. Dlaczego istniejąca bramka tego nie widziała — zmierzone, nie wyczytane

Istniejąca bramka sprawdza **każdą kopię osobno, wobec jej własnego zestawu apt**.
Nie porównuje kopii **ze sobą**. Podzbiór przechodzi więc bez słowa, i to jest
zmierzone, a nie wywnioskowane z kodu.

Sonda w `blender-smoke.yml` zawężona z dziesięciu bibliotek do **jednej**:

```
=== ZESTAW na drzewie z zawezona sonda:
  59/59 przeszło
kod: 0
```

I cały zestaw, nie tylko ten moduł:

```
  2050/2050 przeszło
  RAZEM 135.523 s, 2050 testów, 109 modułów
KOD CALEGO ZESTAWU: 0
```

**Nic tego nie zobaczyło.** `libEGL.so.1` mapuje się na `libegl1`, a `libegl1`
w `blender.txt` stoi — więc bramka „sonduj to, co instalujesz" jest spełniona.
Job zameldowałby `libs = present` po znalezieniu **jednej** biblioteki z dziesięciu,
pominął krok instalacji i wywrócił się dopiero na pierwszym renderze.

**To ta sama rodzina co 6.D40, tylko o kopię dalej**, dokładnie jak mówi treść
pozycji: tam sonda pytała o jedną bibliotekę i mówiła prawdę o tej jednej, więc
instalacja nie odpalała się nigdy.

`md5` `blender-smoke.yml` przed mutacją i po przywróceniu:
`c2b97b3ce7df2ca6891aa9342dda1f38`.

## 4. Co dodano — para bramek, która zabezpiecza się wzajemnie

**`test_kazda_kopia_listy_sonames_niesie_TEN_SAM_zestaw`** zbiera wszystkie kopie
i żąda, żeby był **jeden** zestaw. Liczba kopii jest **pomiarem z drzewa**, nie
listą wpisaną w test — tego żąda pole „Skończone, gdy", a stała zestarzałaby się
przy pierwszym nowym workflowie i byłaby tą samą usterką, którą 6.D45 zmierzyło
na `MIN_REPORTS`.

Sonames są **sortowane**, więc kolejność w wartości `libraries:` jest nieistotna:
`ldconfig` jest pytany o każdą osobno, przestawienie dwóch nazw nie zmienia
zachowania, a bramka na kolejność zapalałaby się na zmianie bez skutku (6.D27).

**`test_kopii_listy_sonames_jest_TYLE_ILE_WOLA_AKCJI_SONDUJACEJ`** jest podłogą
pokrycia — i **nie jest stałą**. Powód jest konkretny: bramka wyżej przy **jednej**
kopii jest trywialnie zielona, bo jedna kopia to jeden zestaw. Gdyby skan przestał
widzieć sześć z siedmiu wywołań, zostałaby jedna kopia, jeden zestaw i zielono.
Podłoga liczy więc wywołania akcji sondującej **niezależnie**, prostym przejściem
po tekście, i porównuje z liczbą kopii zebranych przez parser YAML-a.

## 5. Kontrole negatywne — obie wykonane

### KN-1: jedna biblioteka usunięta z JEDNEJ kopii

```
FAIL test_kazda_kopia_listy_sonames_niesie_TEN_SAM_zestaw: kopie listy sonames NIE są zgodne — job, który sonduje jeden zestaw, a instaluje drugi, wywraca się dopiero przy pierwszym renderze:
  zestaw 1 (10 bibliotek), 6 kopii: blender-smoke.yml:blender-smoke, godot-first-run.yml:first-run, m7-shell.yml:m7-shell, material-style-smoke.yml:material-style, station-details.yml:station-details, visual-regression.yml:visual-regression
    libEGL.so.1 libGL.so.1 libICE.so.6 libSM.so.6 libX11.so.6 libXext.so.6 libXfixes.so.3 libXi.so.6 libXrender.so.1 libxkbcommon.so.0
  zestaw 2 (9 bibliotek), 1 kopii: tunnel-alignment.yml:tunnel-alignment
    libEGL.so.1 libGL.so.1 libICE.so.6 libX11.so.6 libXext.so.6 libXfixes.so.3 libXi.so.6 libXrender.so.1 libxkbcommon.so.0
  60/61 przeszło
kod: 1
```

**Padł DOKŁADNIE jeden test — ten nowy — i nic innego**, czego żądało pole
„Weryfikacja". Komunikat podaje oba zestawy, liczbę kopii każdego i **wskazuje
kopię, która się różni**.

`md5` `tunnel-alignment.yml` po przywróceniu: `595bab4977cbe103fc256ca5a5bc5200`,
ta sama.

### KN-2: zbieracz widzi 1 z 7 workflowów

Mutacja dotyczy **samego zbieracza**, nie workflowów, i to jest wybór: podłoga
chroni przed przyszłą zmianą zbieracza, więc kontrola musi taką zmianę odtworzyć.
Ten sam wzór, co kontrola „przyrząd zawężony" w 6.D45.

```
FAIL test_kopii_listy_sonames_jest_TYLE_ILE_WOLA_AKCJI_SONDUJACEJ: parser YAML-a zebrał 1 kopii listy sonames, a wywołań akcji sondującej jest w tekście 7 — skan przestał czytać część workflowów, a wtedy porównanie kopii ze sobą jest zielone nad rozjazdem w tych nieczytanych
  60/61 przeszło
kod: 1
```

**Przy tej mutacji pierwsza bramka została ZIELONA** — jedna kopia to jeden
zestaw, czyli trywialnie zgodne — i padła wyłącznie podłoga. To jest dowód, że
para nie jest nadmiarowa: każda z dwóch łapie coś, czego druga nie widzi.

`md5` `test_ci_workflows.py` po przywróceniu: `6ad6c8669626b379adadf0413693f8dc`.
Po każdej mutacji `find tools -name __pycache__ -type d -exec rm -rf {} +`, bo
mutacja nazwy biblioteki może mieć identyczną długość pliku — to przypadek z 6.D41.

## 6. Weryfikacja

```
$ python3 tools/tests/test_all.py test_ci_workflows.py
  61/61 przeszło
kod: 0
```

Pomiar bramki na dzisiejszym drzewie:

```
zestawow: 1
  10 sonames, 7 kopii: blender-smoke.yml:blender-smoke, godot-first-run.yml:first-run,
  m7-shell.yml:m7-shell, material-style-smoke.yml:material-style,
  station-details.yml:station-details, tunnel-alignment.yml:tunnel-alignment,
  visual-regression.yml:visual-regression
```

## 7. Czego świadomie nie zrobiłem

- **Nie sprowadziłem siedmiu kopii do jednej.** Zabrania tego pole „Poza zakresem":
  to zmiana kształtu workflowów i akcji składanej, czyli decyzja o tym, jak CI jest
  zbudowane. Ta pozycja daje bramkę na **zgodność** kopii, nie na ich liczbę.
- **Nie objąłem bramką list pakietów apt** — są formą pochodną, a związek
  sonames↔pakiety jest już pilnowany (§2).
- **Nie objąłem sześciu plików wymieniających nazwę w prozie** — nie są listami,
  a bramka na nich byłaby fałszywym alarmem (6.D27).
- **Nie dodałem bramki na kolejność** w wartości `libraries:` — kolejność nie
  zmienia zachowania, więc byłaby to bramka zapalająca się na zmianie bez skutku.
- **Usunąłem z pierwszej wersji własną asercję tautologiczną**
  (`len(kopie) >= 2 or len(kopie) == 1`), która była prawdziwa zawsze. Asercja
  niemogąca paść to ta sama rodzina usterek, którą ta pozycja tropi, tylko
  w miniaturze.

## 8. Zauważone przy okazji, nie tknięte

**Liczba „dziewięć" w treści pozycji nie była zła — liczyła co innego, niż nazywała.**
Dziewięć to liczba plików niosących **napis** `libEGL.so.1` w kodzie CI (siedem
workflowów + akcja + moduł testowy), a nie liczba **kopii listy**, która wynosi
siedem. Pozostałe cztery pliki z trzynastu to `docs/TASKS.md` i raporty, których
treść pozycji nie liczyła wcale. Jest to ta sama klasa nieporozumienia, którą 6.D43
zmierzyło na własnym liczniku równoległości: **przyrząd mierzy coś sąsiedniego
i nazywa to tym, czego szukano.** Nie zgłaszam osobnej pozycji, bo dotyczy jednego
pola jednej pozycji, a nie kodu — i bo poprawna liczba stoi już w bloku ZROBIONE.
