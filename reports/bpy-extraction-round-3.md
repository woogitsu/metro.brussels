# Trzecia runda wyciągania logiki spod `bpy` — `profile_vehicle.py` 7 → 2, `tunnel_sweep.py` 6 → 4

**Zmierzone 06.09.2026 na commicie:** `fc5db5ff09eb3257e18ac6d8aaa7c5811f32fa18`

Pozycja 6.B13 bierze dwa pliki, które przeszły już pierwszą rundę (`profile_vehicle.py`
26 → 7, `tunnel_sweep.py` 35 → 6) i zostały nietknięte przez drugą, bo tamta —
`reports/bpy-extraction-round-2.md` §3 — pokazała, że granicą do przecięcia jest
**wiersz**, nie funkcja. To, co zostało w tych dwóch plikach po pierwszej rundzie,
jest dokładnie tą klasą: pojedyncze porównania zamurowane w funkcjach, które poza tym
wołają `bpy`.

## 1. Mianownik

Zestaw operatorów jest ten sam, co w rundzie drugiej i z tego samego powodu: liczby
„7" i „6" w wierszu 6.B13 `docs/TASKS.md` pochodzą ze starego zestawu
(`--operators operator,prog`) i tylko na nim są porównywalne z tym, co mierzę teraz.

Zmierzone na czystym `HEAD` (przed jakąkolwiek zmianą tej pozycji), stary zestaw:

```
profile_vehicle.py:91  operator `==` -> `!=`
profile_vehicle.py:188 operator `>` -> `>=`
profile_vehicle.py:188 prog `0.0` -> `0.001`
profile_vehicle.py:224 operator `>` -> `>=`
profile_vehicle.py:224 prog `0` -> `1`
profile_vehicle.py:370 operator `==` -> `!=`
profile_vehicle.py:370 operator `!=` -> `==`
razem: 7

tunnel_sweep.py:82  operator `==` -> `!=`
tunnel_sweep.py:82  prog `0` -> `1`
tunnel_sweep.py:101 operator `==` -> `!=`
tunnel_sweep.py:101 prog `0` -> `1`
tunnel_sweep.py:223 operator `==` -> `!=`
tunnel_sweep.py:223 prog `0` -> `1`
razem: 6
```

Liczby z dokumentu i pomiar **zgadzają się dokładnie** — 7 i 6, bez rozjazdu.

Na **pełnym** zestawie pięciu klas operatorów (`operator,prog,logika,argument,przypisanie`,
domyślny od #258) mianownik jest inny i NIE jest porównywalny z powyższym:

```
                        pełny zestaw (5 klas), przed -> po ekstrakcji
profile_vehicle.py      52 -> 47
tunnel_sweep.py          70 -> 68
```

Różnica (5 i 2) zgadza się z tym, co realnie wyszło z pliku — dokładnie tyle mutacji,
ile dziś mieszka w `scan_gates.py` i `lod_paths.py`. Zdecydowana większość z tego, co
ZOSTAJE w `profile_vehicle.py` na pełnym zestawie, to argumenty `round(x, N)` przy
budowaniu słownika raportu JSON w `main()` — formatowanie wyjścia, nie logika
decyzyjna, i poza zakresem tej pozycji (patrz §4). Te dwie liczby są tu wyłącznie
kontekstem — kryterium pozycji jest stary zestaw z tabeli wyżej.

## 2. Co zostało wyciągnięte

Wzorzec ten sam co przy trzynastu poprzednich modułach: moduł-rodzeństwo **bez**
`import bpy`, z którego skrypt sceny bierze gotowe wartości pod **starymi nazwami**
(`should_refine = SG.should_refine` itd.) — ekstrakcja nie zmieniła ani jednej nazwy
widocznej dla reszty pliku ani żadnego interfejsu CLI.

| nowy moduł | z czego | co zawiera |
|---|---|---|
| `tools/blender/scan_gates.py` | `profile_vehicle.py` | `should_refine`, `should_verify`, `is_not_vehicle_tag` |
| `tools/blender/lod_paths.py` | `tunnel_sweep.py` | `is_base_level`, `lod_output_path` |

| moduł | nieosiągalne przed | po | (stary zestaw operatorów) |
|---|---:|---:|---|
| `profile_vehicle.py` | 7 | **2** | |
| `tunnel_sweep.py` | 6 | **4** | |
| **RAZEM** | **13** | **6** | |

## 3. Co zostało i dlaczego zostaje — precedens, nie nowa decyzja

Cztery z sześciu pozostałych mutacji są tej samej klasy, którą `material_specs.py`
już nazwał „nierozerwalną z Blenderem": porównanie, którego WARTOŚĆ pochodzi z żywego
bloku danych Blendera, a nie z arytmetyki.

```
profile_vehicle.py:98  (było :91)  obj.type == "MESH"       w import_glb()
profile_vehicle.py:377 (było :370) o.type == "MESH"          w main(), przy filtrze sceny
tunnel_sweep.py:88     (było :82)  mesh.users == 0            w drop_object()
tunnel_sweep.py:229    (było :223) item.users == 0            w clear_scene()
```

`.type` i `.users` są właściwościami żywego obiektu/bloku danych Blendera — test
podstawiłby gołą wartość i sprawdziłby `"MESH" == "MESH"` albo `0 == 0`, nie
zachowanie Blendera. To nie jest nowe ustalenie tej rundy: `vehicle_fit.py` (runda
pierwsza) zostawia dokładnie ten sam `obj.type == "MESH"` w analogicznym miejscu
`place_vehicle.py` z tym samym uzasadnieniem, a `material_specs.py` (runda druga)
zostawia dokładnie ten sam `block.users == 0` w `material_test_scene.py`. Trzecia
runda nie odkrywa nowego kryterium — stosuje ten sam.

`profile_vehicle.py:370` (dziś `:377`) miał DWIE mutacje na jednej linii z dwóch
różnych powodów: `o.type == "MESH"` (zostaje, jak wyżej) i `o.get("metro_source")
!= "vehicle"` (czysty string, wyciągnięty jako `is_not_vehicle_tag`). To jest
dokładnie ilustracja z §3 raportu drugiej rundy: jedna linia, dwa różne pytania,
jedno bpy-bound i jedno nie — granica przebiega w środku wyrażenia, nie na granicy
funkcji ani pliku.

## 4. Czego ta runda nie zrobiła

- **Nie ruszyła pozostałych mutacji `profile_vehicle.py`/`tunnel_sweep.py` na pełnym
  zestawie pięciu klas** (47 i 68 — §1). Prawie wszystkie to argumenty `round(x, N)`
  przy budowaniu słownika raportu JSON w `main()` — formatowanie wyjścia, nie logika
  decyzyjna, i poza zakresem pozycji 6.B13, która mówi o starym zestawie operatorów
  i o „granicy wiersza" konkretnie dla predykatów, nie dla zaokrągleń w konstrukcji
  raportu.
- **Nie zmieniła zachowania ani jednej linii** — `should_refine`, `should_verify`,
  `is_not_vehicle_tag`, `is_base_level` i `lod_output_path` zwracają dokładnie to,
  co zwracały wyrażenia w miejscu, z którego zostały wyjęte; `lod_entries()` woła
  je w tej samej kolejności, dla tych samych argumentów.
- **Nie dopisała testów `material_test_scene.py`, `station_sections.py`,
  `marker_gates.py` ani `material_specs.py`** — poza zakresem, równolegle pracuje
  nad nimi inny agent.

## 5. Czego NIE zmierzyłem — przegląd mutacyjny nie domknął się w czasie tej sesji

To jest zdanie o pomiarze, nie o ekstrakcji: kod jest przeniesiony, re-eksportowany
i przetestowany bezpośrednio (§6); czego mi zabrakło, to **pełne** potwierdzenie
narzędziem `mutation_sweep.py`, że każda z pięciu mutacji `scan_gates.py` faktycznie
GINIE pod nowymi testami — nie tylko `lod_paths.py`.

Maszyna, na której liczyłem, była w tej sesji współdzielona z co najmniej dwiema
innymi równoległymi sesjami (`wt-a7`, `wt-b14`, plus osobne przebiegi kalibracyjne
w `/tmp/metro-mutacje-*`) — `uptime` pokazywał load average 6,9–8,7 na czterech
rdzeniach. Każdy przebieg `mutation_sweep.py` uruchamia pełny `test_all.py`
(1655 testów) w osobnym `git worktree` per mutacja; pod tym obciążeniem pojedynczy
taki przebieg regularnie przekraczał 90 s, mimo że w spokojnym środowisku trwa
pojedyncze sekundy.

Rzeczywiste wyjście, `--only tools/blender/lod_paths.py` (2 mutacje, `--no-coverage`,
`--timeout 90`, 4 robotników):

```
[MUTACJE] rozstrzygniętych 2/2, zabitych 2, ocalałych 0 (w tym 0 nieuruchomionych), nierozstrzygniętych 0
```

**Pełne, jednoznaczne potwierdzenie — obie mutacje `lod_paths.py` giną.**

Rzeczywiste wyjście, `--only tools/blender/scan_gates.py` (5 mutacji, te same flagi):

```
[MUTACJE] rozstrzygniętych 1/5, zabitych 1, ocalałych 0 (w tym 0 nieuruchomionych), nierozstrzygniętych 4
```

Jedna mutacja rozstrzygnięta i zabita: `scan_gates.py:61 != -> ==` (mutacja
`is_not_vehicle_tag`), zabita przez cztery testy naraz. Pozostałe cztery
(`scan_gates.py:33` operator i prog — `should_refine`; `scan_gates.py:43` operator
i prog — `should_verify`) mają w wyniku JSON `"padly": ["<przekroczony czas>"]` —
**nierozstrzygnięte z powodu czasu**, NIE ocalałe. Zapis JSON: `"przezyla": false`
z jednoczesnym `"rozstrzygniete": false` — narzędzie samo odmawia nazwania tego
zabójstwem, dokładnie zgodnie z własnym docstringiem (`sweep()`/`check_one`):
mutant, którego przebieg nie doszedł do końca w limicie czasu, nie jest ani
potwierdzony jako zabity, ani jako ocalały.

**Przy okazji tego przebiegu znalazłem prawdziwą lukę i ją zamknąłem, zanim
narzędzie zdążyło jej dotknąć:** oryginalne testy `test_scan_gates.py` sprawdzały
`should_refine`/`should_verify` tylko przy wartościach, które dają ten sam wynik
przed i po mutacji `prog` (np. `0.5 > 0.0` i `0.5 > 0.001` dają oba `True`) — więc
nawet przy pełnym rozstrzygnięciu te dwie mutacje **przeżyłyby**. Dodałem
`test_a_tiny_positive_step_still_refines` (`should_refine(0.0005)`) i
`test_count_of_exactly_one_still_verifies` (`should_verify(1)`) — wartości, które
leżą MIĘDZY starym a nowym progiem i dają różny wynik dla oryginału i mutanta.
Zestaw testów jest zielony z tymi dodatkami (§6), ale **nie zdążyłem przegonić
przez nie `mutation_sweep.py` jeszcze raz** — więc zabicie tych czterech mutacji
jest dziś potwierdzone ręczną analizą kodu testu, NIE przebiegiem narzędzia.
To jest różnica, którą CLAUDE.md każe nazwać wprost, a nie zamazać: „zaimplementowałem
zgodnie ze specyfikacją" nie jest weryfikacją.

**Co proponuję:** ponowny przebieg `mutation_sweep.py --only tools/blender/scan_gates.py`
(bez `--no-coverage`, z większym `--timeout`, na maszynie bez współbieżnych sesji)
jako pierwsza czynność następnej pozycji, która dotyka tego pliku, albo osobny
szybki przebieg, jeśli ktoś ma do niego dostęp wcześniej. Kod i testy są gotowe;
brakuje wyłącznie **potwierdzenia narzędziem**, nie zmiany w repo.

## 6. Weryfikacja — rzeczywiste wyjście

Import bez Blendera nadal wymaga `bpy` — jak przed ekstrakcją, bo skrypty scen
zostają skryptami scen:

```
$ python3 -c "import tools.blender.profile_vehicle" 2>&1 | head -3
Traceback (most recent call last):
  File "<string>", line 1, in <module>
  File "tools/blender/profile_vehicle.py", line 26, in <module>

$ python3 -c "import tools.blender.tunnel_sweep" 2>&1 | head -3
Traceback (most recent call last):
  File "<string>", line 1, in <module>
  File "tools/blender/tunnel_sweep.py", line 32, in <module>
```

Nowe moduły importują się bez Blendera:

```
$ python3 -c "import sys; sys.path.insert(0,'tools/blender'); import scan_gates; print('bez bpy: ok')"
bez bpy: ok

$ python3 -c "import sys; sys.path.insert(0,'tools/blender'); import lod_paths; print('bez bpy: ok')"
bez bpy: ok
```

Zestaw testów, czysty checkout:

```
$ python3 tools/tests/test_all.py
  1655/1655 przeszło
```

(1638 przed tą pozycją, +17 nowych testów: 12 w `test_scan_gates.py`, 5 w
`test_lod_paths.py`.)

Nieosiągalność, stary zestaw operatorów, PO ekstrakcji:

```
$ python3 tools/tests/mutation_sweep.py --operators operator,prog --only tools/blender/profile_vehicle.py
[MUTACJE] 2 mutacji w 1 modułach, których zestaw testów nie potrafi zaimportować — nie mają jak zostać zabite:
    tools/blender/profile_vehicle.py (2): ModuleNotFoundError: No module named 'bpy'

$ python3 tools/tests/mutation_sweep.py --operators operator,prog --only tools/blender/tunnel_sweep.py
[MUTACJE] 4 mutacji w 1 modułach, których zestaw testów nie potrafi zaimportować — nie mają jak zostać zabite:
    tools/blender/tunnel_sweep.py (4): ModuleNotFoundError: No module named 'bpy'
```

Osiągalność wyciągniętych funkcji (zestaw testów potrafi je teraz zaimportować i
wykonać) i zabicie ich mutacji — kalibracja wyroczni na czystym drzewie przeszła
w obu przebiegach (`[MUTACJE] drzewo bazowe zielone, wyrocznia ma prawo mówić
„zabita"`, warunek z uwagi 2 zlecenia o `neutralise_own_tests`); pełne wyjście
i to, czego zabrakło, jest w §5.
