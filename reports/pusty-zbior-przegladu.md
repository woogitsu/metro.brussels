# Pusty zbiór przeglądu nazywa swoją przyczynę (6.B41)

**Zmierzone 07.09.2026 na commicie:** `a4a3975f7b08dfddf8c5ae2a8eccb371abccada5`
(baza gałęzi `claude/6b41-pusty-zbior`, czyli `main` po scaleniu #377).

## 1. Co było zrobione, w jednym zdaniu

`tools/tests/mutation_sweep.py` ma jeden przyrząd — `przyczyna_pustego_zbioru` —
który nazywa **rzeczywistą** przyczynę pustego zbioru mutacji (wybór wywołania,
wznowienie, `--limit`, filtr nieosiągalnych) i **z tego samego miejsca** podaje kod
wyjścia: **0**, gdy zbiór opróżniło wznowienie, i **1** dla pozostałych przyczyn.

## 2. Usterka, zmierzona przed poprawką

Zmierzone przy 6.B32 (#373) i potwierdzone tutaj, drugim przebiegiem na czystym
drzewie z kompletnym dziennikiem:

```
[MUTACJE] wznowienie z /tmp/b32/dziennik.jsonl: 2 z 2 już policzonych
brak mutacji do sprawdzenia po odfiltrowaniu nieosiągalnych
kod=1
```

Filtr nieosiągalnych nie odsiał wtedy **niczego** — zbiór był pusty, bo wznowienie
policzyło wszystko. Dwie rzeczy naraz były nieprawdą:

1. **Komunikat** nazywał przyczynę, która nie zachodziła.
2. **Kod 1** mówił „awaria" o przebiegu, który zrobił całą robotę. Dla skryptu CI
   puszczającego przegląd w pętli do skutku to różnica między „gotowe" i „awaria".

Oba wychodziły z **tych samych trzech wierszy** w `main`, i dlatego to jedna pozycja.

### Mechanizm, czyli dlaczego kłamała gałąź DRUGA, a nie ta, która o tym decydowała

W `main` stały dwie gałęzie na pusty zbiór:

| gałąź | warunek | komunikat | kod |
|---|---|---|---|
| A, przed filtrem | `if not found and not done:` | `brak mutacji do sprawdzenia` | 1 |
| B, za filtrem | `if not found:` | `… po odfiltrowaniu nieosiągalnych` | 1 |

**Gałąź A nie kłamała — ona milczała, i to jej milczenie było mechanizmem usterki.**
Człon `and not done` znaczył „odezwij się tylko wtedy, gdy dziennik jest pusty", więc
przy zbiorze opróżnionym przez wznowienie (`done` niepuste) gałąź A przepuszczała
przebieg dalej, a odmowę wypisywała dopiero gałąź B — jedyna, jaka została, i mówiąca
o filtrze bez pytania, czy filtr cokolwiek odsiał. Sama gałąź A też nie nazywała
przyczyny wcale: `brak mutacji do sprawdzenia` jest prawdą o każdym pustym zbiorze
i nie mówi, który etap go opróżnił.

Dlatego poprawka jest w gałęzi A: warunek to dziś gołe `not found`, a odpowiedź na
pytanie „co go opróżniło" liczy jeden przyrząd dla obu gałęzi.

## 3. Pomiar, o który prosiło pole „Wyjście": kto polega na dzisiejszym kodzie 1

**Miejsca wykonywalne: ZERO.** W `.github/workflows/` jest dokładnie **jedno**
wystąpienie napisu `mutation_sweep` — komentarz w `.github/workflows/python-tests.yml`
(wiersz 52) o tym, że `run_suite` czyta wynik `test_all.py`. **Żaden workflow nie
uruchamia tego narzędzia**; nie robi tego też żaden `*.sh`, `Makefile` ani inny plik
poza `tools/tests/`. Żaden test w `tools/tests/test_mutation_sweep.py` nie oczekiwał
kodu 1 z tych gałęzi: dwa testy wznowienia (6.B19, 6.B32) chodzą przez `--list`, czyli
wychodzą kodem 0 **przed** oboma warunkami.

**Miejsca tekstowe: dziewięć**, wszystkie zapisy pomiaru, żadne nie jest bramką.
Skanowane po napisie `brak mutacji do sprawdzenia` w `reports/`, `docs/`
i `.github/workflows/`:

| plik i wiersz | gałąź | co mówi |
|---|---|---|
| `reports/odcisk-tresci-dziennika.md`:214 | B | §9 „zauważone, nie tknięte" — sam ten pomiar |
| `reports/straznik-na-main.md`:259 | A | odmowa (kod 1) stoi **za** gałęzią `--list` |
| `docs/TASKS.md`:743 | B | 6.B32 ZROBIONE, zapis znaleziska |
| `docs/TASKS.md`:749 | A | 6.B37 ZROBIONE, „zauważone przy okazji" |
| `docs/TASKS.md`:755 | A | 6.B39 OTWARTE — **przesłanka pozycji** |
| `docs/TASKS.md`:760 | B | wiersz 6.B41, czyli ta pozycja |
| `docs/TASKS.md`:3984 | A | blok 6.B37, to samo zdanie |
| `docs/TASKS.md`:3993 | A | blok 6.B37, pole „Wejście" |
| `docs/TASKS.md`:4200 | B | blok 6.B41, czyli ta pozycja |

Razem: `reports/` **2**, `docs/` **7**, `.github/workflows/` **0**. Skan liczy
`reports/` **bez tego raportu** — on sam nazywa oba komunikaty czternaście razy, więc
wliczony podnosiłby liczbę, którą ma opisywać. To samo miejsce w drzewie po commicie
daje 21 trafień; dziewięć to stan, który poprawka zastała.

**I ten pomiar wybrał kształt poprawki.** Cztery z dziewięciu miejsc dotyczą gałęzi B
i wszystkie są zapisem historycznym. Pięć dotyczy gałęzi A — a jedno z nich,
`docs/TASKS.md`:744, jest **przesłanką pozycji OTWARTEJ** (6.B39: `--list` z `--only`
pasującym do niczego kończy się kodem 0, „bo odmowa kodem 1 stoi ZA gałęzią `--list`").
Dlatego kod **1** zostaje wszędzie poza wznowieniem, a komunikat wszystkich czterech
przyczyn zaczyna się od tego samego napisu `brak mutacji do sprawdzenia` — te pięć
zapisów zostaje prawdziwych co do litery, a 6.B39 nie traci przesłanki.

## 4. Kolejność pytań jest tu całą rzeczą

Przy zbiorze opróżnionym przez wznowienie **każdy późniejszy licznik też jest zerem**.
Przyrząd pytający o filtr przed wznowieniem odpowiadałby więc „filtr" na każdy taki
przebieg — dokładnie to, co robiła gałąź B — i wyglądałby na działający, dopóki nikt
nie wznowiłby kompletnego dziennika. Pytania idą więc w kolejności etapów zawężania
w `main`: wybór wywołania → wznowienie → `--limit` → filtr nieosiągalnych. Pierwszy
etap, który zszedł do zera, jest przyczyną. Testy tej rodziny idą po **licznikach**,
nie po napisie, bo tylko licznikami da się tę kolejność przybić.

## 5. WYKONANE: cztery przyczyny, cztery komunikaty, dwa kody

### 5.1 Wznowienie policzyło wszystko — kod 0

Polecenie z pola „Weryfikacja", dwa razy pod rząd:

```
$ python3 tools/tests/mutation_sweep.py --only tools/blender/lod_paths.py \
      --journal /tmp/b41/d.jsonl --workers 2 --no-coverage
[MUTACJE] --only 'tools/blender/lod_paths.py' złapało 2 mutacji z 1 moduł(ów): tools/blender/lod_paths.py
[MUTACJE] 2 mutacji do policzenia, 2 robotników, commit 2728cd9, klasy operator,prog,logika,argument,przypisanie, dziennik /tmp/b41/d.jsonl
[MUTACJE] kalibracja wyroczni: zestaw w drzewie BEZ mutacji
[MUTACJE] drzewo bazowe zielone, wyrocznia ma prawo mówić „zabita”
[MUTACJE] rozstrzygniętych 2/2, zabitych 2, ocalałych 0 (w tym 0 nieuruchomionych), nierozstrzygniętych 0
kod=0

$ python3 tools/tests/mutation_sweep.py --only tools/blender/lod_paths.py \
      --journal /tmp/b41/d.jsonl --workers 2 --no-coverage
[MUTACJE] --only 'tools/blender/lod_paths.py' złapało 2 mutacji z 1 moduł(ów): tools/blender/lod_paths.py
[MUTACJE] wznowienie z /tmp/b41/d.jsonl: 2 z 2 już policzonych
brak mutacji do sprawdzenia: wznowienie z /tmp/b41/d.jsonl zastało wszystkie 2 już policzone — przebieg zrobił wszystko, o co go proszono
kod=0
```

Komunikat nazywa wznowienie i podaje dziennik oraz liczbę; kod jest **0**.

### 5.2 Filtr nieosiągalnych odsiał wszystko — dalej mówi o filtrze, kod 1

`tools/blender/glb_roundtrip.py` to wejście Blenderowe, którego zestaw testów nie
zaimportuje, więc filtr zabiera **wszystkie** jego mutacje. Dziennik jest pusty, więc
wznowienie nie ma tu nic do rzeczy:

```
$ python3 tools/tests/mutation_sweep.py --only tools/blender/glb_roundtrip.py \
      --journal /tmp/b41/filtr.jsonl --workers 2 --no-coverage
[MUTACJE] --only 'tools/blender/glb_roundtrip.py' złapało 14 mutacji z 1 moduł(ów): tools/blender/glb_roundtrip.py
[MUTACJE] 14 mutacji w 1 modułach, których zestaw testów nie potrafi zaimportować — nie mają jak zostać zabite:
    tools/blender/glb_roundtrip.py (14): ModuleNotFoundError: No module named 'bpy'
[MUTACJE] pominięte; --include-unreachable liczy je razem z resztą
brak mutacji do sprawdzenia po odfiltrowaniu nieosiągalnych: filtr odsiał wszystkie 14
kod=1
```

### 5.3 `--only` nie dopasowało pliku — kod 1

```
$ python3 tools/tests/mutation_sweep.py --only tools/nie-ma-takiego-pliku.py \
      --journal /tmp/b41/nic.jsonl --workers 2 --no-coverage
[MUTACJE] --only 'tools/nie-ma-takiego-pliku.py' złapało 0 mutacji z 0 moduł(ów): 
brak mutacji do sprawdzenia: --only 'tools/nie-ma-takiego-pliku.py' nie dopasowało ani jednego pliku
kod=1
```

Komunikat podaje **wzorzec**, bo jedynym sygnałem w wypisie było dotąd `0 moduł(ów)`
z pustą listą nazw (znalezisko 6.B37, przesłanka 6.B39).

### 5.4 `--limit` nie przepuścił niczego — kod 1

Trzecia przyczyna wymieniona w polu „Wyjście". Jest osiągalna tylko wartością ujemną
(`found[:-2]` na zbiorze dwuelementowym) — i to jest właśnie powód, żeby pytanie o nią
stało **za** pytaniem o wznowienie, a nie przed:

```
$ python3 tools/tests/mutation_sweep.py --only tools/blender/lod_paths.py \
      --journal /tmp/b41/lim.jsonl --limit -2 --workers 2 --no-coverage
[MUTACJE] --only 'tools/blender/lod_paths.py' złapało 2 mutacji z 1 moduł(ów): tools/blender/lod_paths.py
brak mutacji do sprawdzenia: --limit -2 nie przepuścił ani jednej z 2
kod=1
```

## 6. Kontrole negatywne, obie WYKONANE

### KN-1: poprawka zdjęta w całości (`tools/tests/mutation_sweep.py` z `main`)

```
FAIL test_przyczyna_pustego_zbioru_odmawia_przy_niepustym_zbiorze: module 'mutation_sweep' has no attribute 'przyczyna_pustego_zbioru'
FAIL test_pusty_zbior_po_wznowieniu_nie_klamie_o_filtrze_nieosiagalnych: module 'mutation_sweep' has no attribute 'przyczyna_pustego_zbioru'
FAIL test_pusty_zbior_z_filtru_nieosiagalnych_dalej_mowi_o_filtrze: module 'mutation_sweep' has no attribute 'przyczyna_pustego_zbioru'
FAIL test_pusty_zbior_z_limitu_nazywa_limit: module 'mutation_sweep' has no attribute 'przyczyna_pustego_zbioru'
FAIL test_pusty_zbior_z_only_nazywa_only_a_nie_wznowienie: module 'mutation_sweep' has no attribute 'przyczyna_pustego_zbioru'
FAIL test_wznowienie_ktore_policzylo_wszystko_konczy_sie_zerem: (1, "[MUTACJE] --only 'tools/blender/lod_paths.py' złapało 2 mutacji z 1 moduł(ów): tools/blender/lod_paths.py\n[MUTACJE] wznowienie z /tmp/tmpw2za09cq/dziennik.jsonl: 2 z 2 już policzonych\n", 'brak mutacji do sprawdzenia po odfiltrowaniu nieosiągalnych\n')
  84/90 przeszło
kod=1
```

Sześć z siedmiu nowych testów wywrócone, a ostatni wiersz **pokazuje samą usterkę**:
kod 1 i komunikat o filtrze przy zbiorze, który opróżniło wznowienie.

Siódmy — `test_filtr_nieosiagalnych_ktory_odsial_wszystko_konczy_sie_jedynka` —
**zostaje zielony, i to jest zamierzone**. On pilnuje przyczyny, która zmienić się nie
miała: przed poprawką i po niej filtr nieosiągalnych daje kod 1 i komunikat o filtrze.
Kontrola negatywna, która wywróciłaby także jego, znaczyłaby, że poprawka rusza coś,
czego pole „Poza zakresem" ruszać nie pozwala.

### KN-2: pytanie o wznowienie przestawione ZA pytanie o filtr

Kontrola na moją własną możliwą pomyłkę — bo bez niej **każda** kolejność pytań
przechodziłaby resztę testów:

```
FAIL test_pusty_zbior_po_wznowieniu_nie_klamie_o_filtrze_nieosiagalnych: (1, 'brak mutacji do sprawdzenia: --limit 0 nie przepuścił ani jednej z 0')
FAIL test_wznowienie_ktore_policzylo_wszystko_konczy_sie_zerem: (1, "[MUTACJE] --only 'tools/blender/lod_paths.py' złapało 2 mutacji z 1 moduł(ów): tools/blender/lod_paths.py\n[MUTACJE] wznowienie z /tmp/tmp5rwivlxg/dziennik.jsonl: 2 z 2 już policzonych\n", 'brak mutacji do sprawdzenia: --limit 0 nie przepuścił ani jednej z 0\n')
  88/90 przeszło
kod=1
```

Wywraca **dokładnie te dwa** testy, które kolejność przybijają; pozostałe pięć zostaje
zielonych. Odpowiedź jest przy tym trzecią z rzędu nieprawdą — `--limit 0` — co pokazuje
rzecz ogólniejszą od jednej pomyłki: przy zbiorze opróżnionym przez wznowienie **każde**
pytanie zadane wcześniej trafia w zero i każde odpowiada fałszywie.

## 7. Zestaw

```
$ python3 tools/tests/test_all.py test_mutation_sweep.py
  90/90 przeszło
  RAZEM 15.772 s, 90 testów, 1 modułów
kod=0

$ python3 tools/tests/test_all.py
  1910/1910 przeszło
  RAZEM 70.593 s, 1910 testów, 100 modułów
kod=0
```

`test_mutation_sweep.py` **83 → 90** testów, zestaw **1903 → 1910** (baza zmierzona
osobno, w drzewie `git worktree` na `origin/main`: `1903/1903, RAZEM 72.045 s,
100 modułów`).

**Koszt dwoma niezależnymi pomiarami, i tu one się zgadzają.** Suma median per test
(po trzy przebiegi każdy, w jednym procesie) to **0,632 s**: 0,316 s test drogi filtra
i 0,316 s test drogi wznowienia, oba przez podproces narzędzia, plus pięć testów
przyrządu po 0,000 s. Mediana czasu modułu daje 14,884 s → 15,772 s, czyli **0,888 s**.
Zgodność **0,256 s** przy rozrzucie trójki „po" 0,568 s (15,521 / 15,772 / 16,089 s)
i trójki „przed" 0,138 s (14,873 / 14,884 / 15,011 s) — dwie drogi do jednej liczby
mieszczą się w rozrzucie pomiaru grubszej z nich. Próg `SUITE_RUNTIME_BUDGET_S` to
150 s, więc 70,6 s zostaje z zapasem ponad dwukrotnym.

**Pierwszy pomiar tej pary NIE zgadzał się i został zastąpiony, nie dopisany obok.**
Na bazie sprzed dwóch rebase'ów mediana modułu dała 0,148 s przy tej samej sumie per
test 0,653 s — czterokrotny rozjazd. Powodem był pojedynczy odstrzał w trójce „po"
(14,766 / 14,942 / 15,572 s, rozrzut 0,81 s), który przeciągnął medianę w dół; przy
różnicy rzędu 0,6 s taki rozrzut nie ma czym niczego potwierdzić. Liczba per test była
w obu pomiarach ta sama do 0,02 s — i to ona jest wiążąca.

**Oba testy drogi narzędzia są tanie mimo braku `--list`** — i to nie przypadek, a
własność miejsca, w którym stoi gałąź: obie odmowy wychodzą **przed** `dirty_sources`,
przed sondą nieosiągalności (dla drogi wznowienia) i przed kalibracją wyroczni, więc nie
chodzi tu ani jedno `git worktree add`, ani jeden przebieg zestawu. Każdy z tych dwóch
testów asercją `"kalibracja" not in done.stdout` pilnuje, żeby tak zostało: gdyby ktoś
przesunął gałąź za kalibrację, test kosztowałby minutę i powiedziałby o tym, zanim
ktokolwiek zmierzy czas.

**Bramka zapasu kolejki: zielona, ale o włos i nie dzięki mnie.** Zamknięcie 6.B41
zdejmuje z kolejki jedną pozycję. Na bazie sprzed rebase'u na #377 (`9faf5a2`) zostawiało
to **11 pozycji przy progu 12** i `test_backlog.py` był wtedy czerwony dwoma
asercjami — zmierzone, nie przewidziane. Scalenie #376 dopisało do fazy 6 nowe pozycje,
więc na dzisiejszej bazie zapas po zamknięciu 6.B41 mieści się w progu i cały zestaw
wychodzi kodem 0. Kolejka **nie została uzupełniona w tym commicie**: to zadanie
właściciela, a wymyślanie pozycji na miejscu `CLAUDE.md` §8 zabrania wprost.

## 8. Czego świadomie nie zrobiono

- **Kody wyjścia pozostałych odmów przeglądu nie zostały tknięte** — kod 2 dla dziennika
  z innego drzewa (6.B19), z innej treści (6.B32) i dla brudnych plików. Pole „Poza
  zakresem" tej pozycji, rozstrzygnięte przy 6.B19 i 6.B32.
- **`--limit` z wartością ujemną nie dostał odmowy.** Nazwanie przyczyny to nie to samo,
  co odrzucenie wywołania; nowa odmowa jest zmianą interfejsu, o którą ta pozycja nie
  prosiła, a przyrząd i tak mówi dziś wprost, co się stało.
- **6.B39 nie została po drodze zrobiona.** Kod 1 dla `--only` pasującego do niczego
  zostaje, a `--list` nadal wychodzi kodem 0 przed obiema gałęziami — to jest osobna
  pozycja i jej przesłanka została nietknięta świadomie (§3).
- Dziewięć zapisów tekstowych z §3 nie zostało przepisanych. Osiem to zapisy pomiarów
  historycznych albo cudze pozycje; dziewiąty to wiersz 6.B41, który ten commit
  zamienia na `ZROBIONE`.

## 9. Zauważone przy okazji, nie tknięte

- **Docstring `test_every_real_target_except_the_blender_entry_points_is_reachable`
  podaje nieaktualne liczby.** Mówi „9 z 44 modułów `tools/` jest nieosiągalnych",
  a zmierzone dziś na tym drzewie: **10** modułów nieosiągalnych. Sama asercja jest
  na próg (`< len(targets()) // 2`) i przechodzi; nieaktualna jest proza obok niej.
  Dziesiąty to `tools/visual/capture_blender.py`, więc zdanie „wszystkie to wejścia
  Blenderowe" zostaje prawdą — nieprawdą jest liczba.
- **`main` czyta dziś `commit` z `git rev-parse --short HEAD`, a dziennik nie odróżnia
  przebiegu z gałęzi od przebiegu ze scalonego `main`.** Przy dwóch rebase'ach tej
  gałęzi w ciągu godziny każdy dawał inny skrót, więc dziennik z poprzedniej bazy
  odmawiał kodem 2 — poprawnie, ale komunikat mówi o „innym drzewie", nie o rebase,
  i szukanie przyczyny zajmuje chwilę.
