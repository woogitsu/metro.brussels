# `--list` z pustym zbiorem: zielone zero i druga przyczyna, o której komunikat kłamał (6.B39)

**Zmierzone 07.09.2026 na commicie:** `b019436f608f3836a6c3ad0d2261815e5c1ed96f`
**Dotyczy:** `tools/tests/mutation_sweep.py`, `tools/tests/test_mutation_sweep.py`
**Poprzedni etap:** 6.B41 (`reports/pusty-zbior-przegladu.md`), 6.D18, 6.B37

## 1. Stan wyjściowy — WYKONANY, obie drogi

```
$ python3 tools/tests/mutation_sweep.py --only tools/nie-ma-takiego-pliku.py --list
[MUTACJE] --only 'tools/nie-ma-takiego-pliku.py' złapało 0 mutacji z 0 moduł(ów):
razem: 0
kod: 0

$ python3 tools/tests/mutation_sweep.py --only tools/nie-ma-takiego-pliku.py
[MUTACJE] --only 'tools/nie-ma-takiego-pliku.py' złapało 0 mutacji z 0 moduł(ów):
brak mutacji do sprawdzenia: --only 'tools/nie-ma-takiego-pliku.py' nie dopasowało ani jednego pliku
kod: 1
```

Ta sama literówka, ten sam stan, dwie różne odpowiedzi — bo odmowa z 6.B41 stoi **za**
gałęzią `--list`. Przebieg CI, który przez pomyłkę zawęził `--only`, dostawał zielone
zero i wygląd poprawnego przebiegu, który po prostu nie miał co robić.

## 2. Pomiar, którego żądało pole „Wyjście" — i on zmienił zakres poprawki

Pole pytało wprost: „czy odmowa ma być na pustym zbiorze MODUŁÓW, czy MUTACJI, bo to
nie to samo". Odpowiedź jest **zmierzona i twierdząca**, a przy okazji pokazuje **drugą
usterkę**, o której pozycja nie wiedziała.

### 2.1 Modułów bez ani jednej mutacji danej klasy jest od 2 do 36 na 63 cele

```
operator     modulow bez ani jednej mutacji tej klasy:   2
prog         modulow bez ani jednej mutacji tej klasy:  15
logika       modulow bez ani jednej mutacji tej klasy:  11
argument     modulow bez ani jednej mutacji tej klasy:   6
przypisanie  modulow bez ani jednej mutacji tej klasy:  36
```

Przy **pełnym** zestawie klas celów bez mutacji jest **zero z 63** — czyli gdyby patrzeć
tylko na domyślne wywołanie, rozróżnienie „moduły kontra mutacje" byłoby
nieobserwowalne i wyglądałoby na spór o zasady. Nie jest: wystarczy jedna klasa
operatorów, żeby stan „zawężenie trafiło, ale nic nie dało" stał się osiągalny jedną
komendą.

### 2.2 Komunikat mówił wtedy nieprawdę — WYKONANE

```
$ python3 tools/tests/mutation_sweep.py --only tools/blender/camera_aim.py --operators prog
[MUTACJE] --only 'tools/blender/camera_aim.py' złapało 0 mutacji z 0 moduł(ów):
brak mutacji do sprawdzenia: --only 'tools/blender/camera_aim.py' nie dopasowało ani jednego pliku
kod: 1
```

`tools/blender/camera_aim.py` **jest** celem i wzorzec dopasowuje go dokładnie. Zdanie
„nie dopasowało ani jednego pliku" jest fałszywe, a wiersz nagłówka mówi „0 moduł(ów)",
bo `pliki_przebiegu` wyprowadza się **ze zbioru mutacji** — zero mutacji znaczy tam
zawsze zero modułów, niezależnie od tego, ile plików wzorzec objął.

To jest ta sama rodzina usterki co 6.B41: **gałąź nazywająca przyczynę, która nie
zachodzi.** Tydzień po tamtej poprawce, w tym samym pliku, w innej gałęzi.

### 2.3 Czy cokolwiek polega na kodzie 0 przy zawężeniu bez trafień

```
roznych realnych wzorcow --only cytowanych w reports/ i docs/: 48
lapiacych ZERO celow:                                           1
   'tools/nie-ma-takiego-pliku.py' w ['docs/TASKS.md',
                                      'reports/pusty-zbior-przegladu.md',
                                      'reports/straznik-na-main.md']
```

Ten jeden jest **umyślną atrapą** — dokładnie tym wzorcem opisano tę usterkę. Wywołań
narzędzia w `.github/workflows/` i w `tools/ci/**` jest **zero** (jedyne trafienie napisu
`mutation_sweep` w workflowach to komentarz). Nic wykonywalnego nie polega więc na
dzisiejszym kodzie 0.

## 3. Co robi poprawka

- Przebieg liczy **pliki docelowe dopasowane przez `--only`** (`dopasowane_cele`)
  niezależnie od tego, czy dały mutację. Bez tego licznika dwóch przyczyn nie da się
  odróżnić w ogóle.
- Wiersz nagłówka `--only` podaje **dwie** liczby: ile celów wzorzec dopasował i z ilu
  z nich wyszła choć jedna mutacja. Do dziś stała tam tylko druga.
- Gałąź `--list` przy pustym zbiorze i podanym `--only` idzie przez
  **`przyczyna_pustego_zbioru`** — ten sam przyrząd, co droga bez `--list`. Jeden
  przyrząd, bo dwa czytniki tych samych liczników rozjeżdżają się po cichu (6.B28).
- Przyrząd rozdziela dwie przyczyny na dwa zdania przy **tym samym** kodzie 1:
  zawężenie nietrafione i zawężenie trafione w plik bez mutacji w podanych klasach.

Poza zakresem, zgodnie z polem pozycji: **pusty zbiór bez `--only`** (odmowa dotyczy
zawężenia, nie przebiegu w ogóle) oraz zmiana dopasowania `--only` z podciągu na nazwę
pliku — to decyzja 6.D18 i ta pozycja jej nie rusza.

## 4. Stan po poprawce — WYKONANY

```
$ … --only tools/nie-ma-takiego-pliku.py --list
[MUTACJE] --only 'tools/nie-ma-takiego-pliku.py' dopasowało 0 plik(ów) docelowych i złapało 0 mutacji z 0 moduł(ów):
brak mutacji do sprawdzenia: --only 'tools/nie-ma-takiego-pliku.py' nie dopasowało ani jednego pliku
kod: 1

$ … --only tools/blender/camera_aim.py --operators prog --list
[MUTACJE] --only 'tools/blender/camera_aim.py' dopasowało 1 plik(ów) docelowych i złapało 0 mutacji z 0 moduł(ów):
brak mutacji do sprawdzenia: --only 'tools/blender/camera_aim.py' dopasowało 1 plik(ów) docelowych, ale żaden nie dał ani jednej mutacji w podanych klasach — zawężenie trafiło, klasy nie
kod: 1

$ … --only tools/blender/camera_aim.py --operators prog        (BEZ --list)
  → identyczny komunikat, identyczny kod
```

## 5. Kontrola ujemna z pola „Skończone, gdy" — WYKONANA, trzy kształty zawężenia

```
$ … --only tools/track/ --list
[MUTACJE] --only 'tools/track/' dopasowało 19 plik(ów) docelowych i złapało 782 mutacji z 19 moduł(ów): …
kod: 0  razem: 782

$ … --only sweep.py --list
[MUTACJE] --only 'sweep.py' dopasowało 2 plik(ów) docelowych i złapało 185 mutacji z 2 moduł(ów): tools/blender/sweep.py, tools/blender/tunnel_sweep.py
kod: 0  razem: 185

$ … --only tools/blender/lod_paths.py --list
[MUTACJE] --only 'tools/blender/lod_paths.py' dopasowało 1 plik(ów) docelowych i złapało 2 mutacji z 1 moduł(ów): tools/blender/lod_paths.py
kod: 0  razem: 2
```

Wszystkie trzy nadal kodem 0. Przy okazji widać cenę podciągu z 6.D18 teraz także
w **pierwszej** liczbie: `--only sweep.py` dopasowuje dwa cele, nie jeden.

## 6. Weryfikacja

```
$ python3 tools/tests/test_all.py; echo "kod: $?"
  1918/1918 przeszło
  RAZEM 73.087 s, 1918 testów, 101 modułów
kod: 0
```

Moduł `test_mutation_sweep.py`: **90 → 95** testów. Zestaw **1913 → 1918**.

## 7. Trzy kontrole negatywne — WYKONANE, każda wywraca INNY zbiór

**KN-1 — odmowa w `--list` zdjęta w całości.** Wraca dokładnie usterka:

```
FAIL test_obie_drogi_podaja_te_sama_przyczyne_tego_samego_stanu: (0, 1)
FAIL test_only_bez_trafien_z_lista_nie_konczy_sie_zerem: (0, "… razem: 0\n")
FAIL test_zawezenie_trafione_w_plik_bez_mutacji_nie_mowi_ze_nie_trafilo: (0, "… razem: 0\n")
  92/95 przeszło
```

Test zgodności obu dróg pada z parą `(0, 1)` — czyli nazywa **rozjazd**, nie sam kod.

**KN-2 — odmowa zbudowana ZBYT SZEROKO** (warunek `not found` zdjęty, zostaje samo
`args.only`). To jest kontrola, o którą pole „Skończone, gdy" prosiło wprost, i pada
**sześć** testów, z czego **cztery są starsze od tej pozycji**:

```
FAIL test_cli_lists_only_the_requested_class
FAIL test_only_is_a_substring_match_by_design_and_says_how_many_modules_it_caught
FAIL test_only_z_trafieniami_nadal_konczy_sie_zerem: ('tools/track/', 1, … ValueError:
     przyczyna_pustego_zbioru wołana przy NIEPUSTYM zbiorze: zebrane=782 …)
FAIL test_resume_still_works_when_the_content_matches
FAIL test_resume_still_works_when_the_journal_is_from_the_same_tree
FAIL test_the_cli_lists_mutations_as_a_process_and_exits_zero
  89/95 przeszło
```

Warto zauważyć **czyj** to strażnik: `ValueError` przy niepustym zbiorze dołożyło
6.B41 dzień wcześniej, i to on złapał moją zbyt szeroką odmowę, zanim złapał ją
którykolwiek z moich testów.

**KN-3 — dwie przyczyny zlane z powrotem w jedną** (`if only and dopasowane_pliki`
zmienione na warunek nigdy niespełniony):

```
FAIL test_przyczyna_odroznia_zawezenie_nietrafione_od_trafionego_bez_mutacji
FAIL test_zawezenie_trafione_w_plik_bez_mutacji_nie_mowi_ze_nie_trafilo:
     brak mutacji do sprawdzenia: --only 'tools/blender/camera_aim.py' nie dopasowało ani jednego pliku
  93/95 przeszło
```

Wraca dokładnie to zdanie nieprawdziwe z §2.2. Plik przywrócony po każdej z trzech
kontroli i sprawdzony przez `cmp`.

## 8. Czego świadomie nie zrobiłem

- **Pustego zbioru bez `--only`** — pole „Poza zakresem" pozycji mówi o tym wprost.
  Przebieg bez zawężenia, który nie zebrał ani jednej mutacji, nadal wychodzi z `--list`
  zerem. Dziś jest to nieosiągalne (63 cele z 63 dają mutacje przy pełnym zestawie klas),
  ale zapisuję, że nieosiągalne nie znaczy niemożliwe.
- **Dopasowania `--only` po nazwie pliku zamiast po podciągu** — decyzja 6.D18
  z powodem wypisanym w kodzie.
- **Nie przeliczyłem liczb w bloku pozycji.** Blok podaje wyjście z 07.09.2026 i jest
  pomiarem z datą; nowe liczby stoją w wierszu tabeli i tutaj.

## 9. Zauważone przy okazji, nietknięte

- **Mój pierwszy pomiar „celów bez mutacji" dał 63 z 63 i był bezsensowny**, bo
  `targets()` zwraca ścieżki **bezwzględne**, a `Mutation.path` — względne, więc
  porównywałem dwa różne alfabety. Poprawne jest **0 z 63**. To trzeci raz w tej sesji,
  gdy mój własny przyrząd zameldował wynik, nie wykonawszy pomiaru; pierwsze dwa są
  w `reports/kolejka-uzupelnienie-drugie.md` §4.1. Wspólna cecha wszystkich trzech:
  **wynik wyglądał sensownie** („wszystkie" albo „zero" to liczby, które da się
  uzasadnić po fakcie).
- **Mój helper testowy nazywał się `_sweep_cli`, tak jak istniejący w tym samym pliku**,
  i przesłonił go. Złapał to zestaw (`FAIL test_the_cli_lists_mutations_as_a_process…:
  _sweep_cli() got an unexpected keyword argument 'journal_tag'`) przy pierwszym
  przebiegu, nie przegląd. Przezwany na `_sweep_6b39`.
- **`--only` przyjmuje dziś podciąg pusty** (`--only ""` jest fałszywe dla `args.only`,
  więc idzie drogą bez zawężenia) — zachowanie zgodne, ale nigdzie nie napisane.
  Nie tknięte: to nie pusty zbiór, a puste zawężenie, i byłaby to inna pozycja.
