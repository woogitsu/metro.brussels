# Przegląd mutacyjny bramek

**Snapshot na commicie:** `66b8301` (`main`, 04.09.2026)

Poprzedni snapshot stał na `737d592` (03.09.2026) i był o piętnaście scaleń wstecz —
w tym o większość ekstrakcji spod `bpy`, które ten sam raport wskazywał jako lekarstwo.
Liczby niżej pochodzą z **jednego przebiegu na jednym drzewie** i są odtwarzalne
poleceniem z sekcji „Jak to powtórzyć".

Narzędzie: `tools/tests/mutation_sweep.py`. Mutowany jest **kod pod testem**, nie testy.
Mutacja, która przeżyła, znaczy jedno z dwojga: brak pokrycia albo mutant równoważny.
Narzędzie nie zgaduje, które to.

## Czego ten przebieg NIE pokrywa, choć pozycja 5.1 tak brzmi

Pozycja 5.1 w `docs/TASKS.md` mówi „po jednej mutacji na każdą kontrolę
w `tools/ci/*.sh` i `tools/tests/test_*.py`". **To nie jest to, co robi to narzędzie**,
i rozjazd trzeba nazwać, zanim ktoś przeczyta liczby jako odpowiedź na tamto zdanie:

| pozycja 5.1 mówi | narzędzie robi |
|---|---|
| kontrole w `tools/ci/*.sh` | nic — mutuje wyłącznie Pythona; skrypty shellowe są nietknięte |
| kontrole w `tools/tests/test_*.py` | nic — mutuje **kod pod testem**, a testy pozostawia jako wyrocznię |
| „każdą kontrolę" | wyłącznie **operatory porównań i progi liczbowe**; nie mutuje przypisań, wywołań ani łączników logicznych |

Wyjątkiem, i to pozornym, jest `tools/ci/assert_shot_metadata.py` — leży w `tools/ci`,
ale jest modułem Pythona i wchodzi do przebiegu jako kod pod testem, nie jako bramka.

To nie znaczy, że pozycja 5.1 jest zła. Znaczy, że **domyka ją tylko częściowo**:
mutowanie bramek shellowych i samych testów wymagałoby drugiego narzędzia i osobnej
wyroczni, bo dla testu wyrocznią byłby wtedy kod, a nie odwrotnie.

## Wynik

| | ten przebieg (`66b8301`) | poprzedni (`737d592`) |
|---|---:|---:|
| mutacji w drzewie | 980 | 961 |
| pominiętych jako nieosiągalne | 51 | 148 |
| **policzonych** | **929** | **813** |
| rozstrzygniętych | 929 | 812 |
| zabitych | 661 | 213 |
| **ocalałych** | **268** | **599** |
| nierozstrzygniętych | **0** | 1 |
| **pokrycie kodu osiągalnego** | **71,2 %** | **26,2 %** |

Kolumna „poprzedni" jest przeliczona **na kodzie osiągalnym**, a nie przepisana
z tamtego podsumowania. Tamten raport podawał w tabeli głównej 961 mutacji, 216 zabitych
i 22,5 % pokrycia, bo wrzucał do jednej puli moduły, których nie da się zaimportować bez
Blendera — a ich mutacji nie da się zabić i sam raport pisał o tym w osobnej sekcji.
Uczciwe porównanie idzie po osiągalnych: 813 mutacji, z tego 599 ocalałych i **jedna
nierozstrzygnięta**, czyli 213 zabitych na 812 rozstrzygniętych — 26,2 %. Ta jedynka
jest tu istotna: nierozstrzygnięta nie jest zabiciem, więc odchodzi od licznika I od
mianownika, a nie tylko od jednego z nich. Kontrola zamknięcia: 213 zabitych osiągalnych
plus 3 zabite nieosiągalne (te trzy łapały testy czytające pliki jako TEKST) daje 216,
czyli dokładnie liczbę z tamtego podsumowania.

Różnica **26,2 % → 71,2 %** jest więc mierzona tą samą miarą po obu stronach.

## Skąd ta różnica, liczbą

Trzy rzeczy naraz, i każda daje się wskazać:

1. **Nieosiągalne zeszły z 148 mutacji na 51.** Ekstrakcje spod `bpy` przeniosły
   porównania i progi do modułów, które da się zaimportować, więc te same bramki
   są dziś w zasięgu testów. Największe ruchy: `m7_shell.py` 35 → 2,
   `tunnel_sweep.py` 35 → 6, `profile_vehicle.py` 26 → 7, `glb_roundtrip.py` 10 → 1,
   `place_vehicle.py` 7 → 1.

   `capture_blender.py` zeszło z 10 mutacji na **zero** i to jest inny przypadek,
   którego nie wolno wliczyć do tej samej kolumny: moduł nadal istnieje i nadal
   importuje `bpy`, więc nadal jest nieosiągalny. Po prostu nie ma już w nim ani
   jednego porównania ani progu, które to narzędzie mutuje — sprawdzone: nie ma go
   ani wśród pominiętych, ani wśród policzonych. Brak mutacji nie jest pokryciem.
2. **Zestaw testów urósł z 692 na 1333 pozycje**, a przyrost szedł głównie w progi
   i granice — czyli dokładnie w to, co to narzędzie mutuje.
3. **Zero nierozstrzygniętych, i to nie przez zniknięcie problemu.** Poprzedni
   przebieg miał jedną nierozstrzygniętą: mutacja strażnika `step_m <= 0.0`
   w `detail_layout.py` zamieniała go w pętlę nieskończoną, więc proces testów
   nigdy nie kończył pracy i narzędzie uczciwie mówiło „nie wiem". Tamten raport
   proponował wtedy niezależny ogranicznik liczby iteracji jako decyzję właściciela.

   **Ogranicznik jest.** `MAX_MARKS = int(MAX_AXIS_LENGTH_M / MIN_SENSIBLE_STEP_M)`
   = 40 000, sprawdzany wewnątrz pętli, jawnie opisany jako niezależny od strażnika.
   Skutek w tym przebiegu jest dokładnie taki, jaki miał być — obie mutacje strażnika
   (wiersz 78) i mutacja samego ogranicznika (wiersz 83) są **rozstrzygnięte
   i zabite**, każda przez test pisany na nią:

   ```
   detail_layout.py:78 prog `0.0` -> `0.001`     ZABITA
       test_layout_hectometre_grid_terminates_with_the_step_guard_removed
       test_detail_hectometre_step_of_a_millimetre_is_still_positive
   detail_layout.py:78 operator `<=` -> `<`      ZABITA
       test_layout_hectometre_grid_terminates_with_the_step_guard_removed
   detail_layout.py:83 operator `>=` -> `>`      ZABITA
       test_layout_hectometre_grid_stops_at_max_marks_and_says_so_with_numbers
   ```

   To jest najlepszy pojedynczy dowód, jaki ten przebieg daje: nierozstrzygnięta
   z przekroczonego czasu **kryła realną usterkę projektową**, została naprawiona,
   a naprawa jest dziś przybita testem, który mutacja wywraca.

Skok jest na tyle duży, że nie wolno go po prostu wpisać. Sprawdzony w obie strony,
wykonaniem, na źródle:

**Kontrola zabitej.** `tools/track/crs.py:306`, operator `<` → `<=`
(to strażnik zbieżności z progiem residuum):

```
$ python3 tools/tests/test_all.py
FAIL test_crs_convergence_residual_exactly_at_a_nonzero_tolerance_fails:
     residuum == tolerance_m == 0.4007257902994752 powinno być porażką
FAIL test_crs_convergence_residual_exactly_at_zero_tolerance_fails:
     residuum == tolerance_m == 0.0 powinno być porażką
  1331/1333 przeszło
```

Zabicie jest prawdziwe i pochodzi z **testu granicznego**, czyli takiego, który dotyka
progu dokładnie. Osłabienie `<` do `<=` wpuszcza residuum równe tolerancji jako wynik
zbieżny — i oba testy to nazywają.

**Kontrola ocalałej.** `tools/blender/clearance.py:47`, próg `0.0` → `0.001`:

```
$ python3 tools/tests/test_all.py
  1333/1333 przeszło
```

Cały zestaw pozostaje zielony. Mutacja rzeczywiście żyje.

## Pułapka odczytu: wiersz i operator NIE identyfikują mutacji

W `tools/visual/pngio.py:42` operator `<=` → `<` występuje **i jako zabita, i jako
ocalała** — bo w tym wierszu stoją dwa `<=` w różnych kolumnach i to dwie różne
mutacje. Identyfikatorem jest `plik:wiersz:przesunięcie`, nie `plik:wiersz`.
Czytając tabele niżej, nie da się więc powiedzieć „ta mutacja przeżyła" o samym
wierszu z operatorem, jeżeli wiersz zawiera dwa takie same operatory.

## Jak czytać ocalałe

Ocalała mutacja **nie jest** automatycznie usterką. Trzeba ją zakwalifikować do jednej
z trzech klas, a narzędzie tego nie zrobi za czytającego:

| klasa | co znaczy | co z tym zrobić |
|---|---|---|
| **realna dziura** | zmiana zmienia zachowanie, które ktoś kiedyś zobaczy, a żaden test tego nie sprawdza | dopisać test z kontrolą negatywną |
| **mutant równoważny** | zmiany nie da się zaobserwować (np. tolerancja `1e-12` przesunięta o procent) | zapisać jako równoważną, nie „naprawiać" |
| **remis bez znaczenia** | `<` kontra `<=` przy wyborze minimum: przy remisie obie gałęzie dają tę samą wartość | jak wyżej, chyba że liczy się INDEKS |

Rozróżnienie wymaga przeczytania kodu. Wpisanie mutanta równoważnego jako usterki
zawyża znalezisko dokładnie tak samo, jak liczenie zepsutego przebiegu jako zabicia
zawyżało pokrycie w poprzednich wersjach tego narzędzia.

## Moduły nieosiągalne — 51 mutacji w 9 plikach

Import tych modułów wymaga `bpy`, więc `tools/tests/test_all.py` nie ma jak ich
dotknąć. Ich mutacji nie da się zabić — nie dlatego, że nikt nie napisał testu,
tylko dlatego, że nie istnieje droga. Narzędzie **pomija je i mówi o tym wprost**;
`--include-unreachable` wlicza je razem z resztą i wtedy pokrycie schodzi pozornie.

| plik | mutacji dziś | mutacji na `737d592` |
|---|---:|---:|
| `tools/blender/material_test_scene.py` | 12 | — |
| `tools/blender/station_kit.py` | 11 | 8 |
| `tools/blender/detail_markers.py` | 9 | 6 |
| `tools/blender/profile_vehicle.py` | 7 | 26 |
| `tools/blender/tunnel_sweep.py` | 6 | 35 |
| `tools/blender/m7_shell.py` | 2 | 35 |
| `tools/blender/render_check.py` | 2 | 8 |
| `tools/blender/glb_roundtrip.py` | 1 | 10 |
| `tools/blender/place_vehicle.py` | 1 | 7 |

`material_test_scene.py` doszedł 04.09.2026 z T-902 i jest jedynym pozycją na tej
liście, która **urosła z nowej pracy**, a nie została po ekstrakcji. `station_kit.py`
i `detail_markers.py` też urosły — ich czysta logika wyszła do `tools/track/`,
a w module pod `bpy` zostało samo składanie scenki, którego przybyło.

Lekarstwem tutaj nie są testy, tylko dalsze wyciąganie logiki spod `bpy`.
Bramką na to, że te moduły w ogóle się wykonują, jest `tools/ci/*.sh`
(`test_ci_every_blender_generator_has_a_gate`) — i to jest jedyna droga, jaka tam
dziś istnieje.

## Kolejność triażu — po udziale, nie po liczbie

Wysoki udział znaczy, że testy tego modułu sprawdzają co innego, niż deklarują;
duża liczba przy niskim udziale znaczy tylko, że moduł jest duży.

| plik | ocalałe / mutacje | udział |
|---|---:|---:|
| `tools/track/make_test_track.py` | 2 / 2 | 100 % |
| `tools/blender/clearance_profile.py` | 66 / 77 | 86 % |
| `tools/blender/placement.py` | 26 / 40 | 65 % |
| `tools/track/crs.py` | 8 / 14 | 57 % |
| `tools/track/build_alignment.py` | 39 / 69 | 57 % |
| `tools/blender/clearance.py` | 6 / 11 | 55 % |
| `tools/physics/schedule_envelope.py` | 5 / 10 | 50 % |
| `tools/blender/sweep.py` | 37 / 79 | 47 % |
| `tools/physics/braking.py` | 5 / 11 | 45 % |
| `tools/physics/reference.py` | 3 / 8 | 38 % |
| `tools/blender/lod.py` | 37 / 104 | 36 % |
| `tools/blender/m7_report.py` | 9 / 31 | 29 % |
| `tools/ci/assert_shot_metadata.py` | 6 / 39 | 15 % |
| `tools/track/station_layout.py` | 1 / 7 | 14 % |
| `tools/track/detail_layout.py` | 1 / 9 | 11 % |
| `tools/visual/pngio.py` | 4 / 38 | 11 % |
| `tools/track/crosscheck_alignment.py` | 2 / 19 | 11 % |
| `tools/blender/profiles.py` | 1 / 13 | 8 % |
| `tools/track/tunnel_width.py` | 2 / 28 | 7 % |
| `tools/blender/m7_layout.py` | 1 / 17 | 6 % |
| `tools/track/shapefile.py` | 1 / 17 | 6 % |
| `tools/track/validate.py` | 2 / 37 | 5 % |
| `tools/track/inspire_rail.py` | 2 / 41 | 5 % |
| `tools/visual/framing.py` | 1 / 22 | 5 % |
| `tools/track/surface_sections.py` | 1 / 29 | 3 % |

**Pełne pokrycie mają 15 pliki z 40** — ani jednej ocalałej mutacji:
`camera_aim.py`, `glb_report.py`, `profile_scan.py`, `tunnel_manifest.py`, `vehicle_fit.py`, `assert_empty_frame_negative.py`, `provenance.py`, `snapshot_source.py`, `data_freshness.py`, `fetch_osm_routes.py`, `network_chainage.py`, `normalize_stops.py`, `timetable.py`, `capture_plan.py`, `compare.py`.

## Jak to powtórzyć

```bash
git checkout 66b8301
python3 tools/tests/mutation_sweep.py --workers 4 \
    --journal /tmp/mutacje.jsonl --json /tmp/mutacje.json --out /tmp/sweep.md
```

Zmierzone na tej maszynie: 929 mutacji, 4 robotniki, **74 minuty** (07:23–08:37 UTC, ok. 12,6 mutacji
na minutę przy przebiegu suity 25 s). Dziennik JSONL jest dopisywany po każdej mutacji,
więc przerwany przebieg da się wznowić tym samym poleceniem. Mutacje powstają z AST
w ustalonej kolejności (plik, wiersz, kolumna), więc dwa przebiegi na tym samym drzewie
dają tę samą listę i te same identyfikatory.

Kontrole ręczne z sekcji „Skąd ta różnica" powtarza się skryptem, który wprowadza
mutację po `plik:wiersz:przesunięcie` z `mutacje.json`, uruchamia suitę i przywraca
plik — sprawdzając przy okazji, że przesunięcie faktycznie wskazuje na `bylo`.

## Ocalałe, per plik

### `tools/blender/clearance.py` — 6

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 47 | prog | `0.0` | `0.001` |
| 47 | operator | `<=` | `<` |
| 50 | operator | `>=` | `>` |
| 70 | operator | `<` | `<=` |
| 99 | operator | `<=` | `<` |
| 101 | prog | `0.0` | `0.001` |

### `tools/blender/clearance_profile.py` — 66

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 91 | operator | `<=` | `<` |
| 99 | operator | `<=` | `<` |
| 99 | prog | `0.0` | `0.001` |
| 104 | operator | `<=` | `<` |
| 104 | prog | `0.0` | `0.001` |
| 119 | prog | `0.0` | `0.001` |
| 174 | prog | `0.0` | `0.001` |
| 174 | operator | `>` | `>=` |
| 181 | operator | `<` | `<=` |
| 185 | prog | `0.0` | `0.001` |
| 196 | operator | `<=` | `<` |
| 198 | operator | `>=` | `>` |
| 198 | prog | `0.9` | `0.909` |
| 200 | prog | `0.9` | `0.909` |
| 200 | operator | `>=` | `>` |
| 217 | operator | `<` | `<=` |
| 237 | operator | `>` | `>=` |
| 240 | operator | `>` | `>=` |
| 248 | operator | `<` | `<=` |
| 324 | operator | `<` | `<=` |
| 324 | prog | `0.0` | `0.001` |
| 326 | operator | `<` | `<=` |
| 337 | operator | `<` | `<=` |
| 366 | operator | `<` | `<=` |
| 382 | operator | `<=` | `<` |
| 382 | prog | `0.0` | `0.001` |
| 385 | operator | `<=` | `<` |
| 385 | prog | `0.0` | `0.001` |
| 389 | operator | `>` | `>=` |
| 389 | prog | `1e-9` | `1.01e-09` |
| 400 | operator | `>` | `>=` |
| 400 | prog | `1e-6` | `1.0099999999999999e-06` |
| 403 | operator | `>` | `>=` |
| 403 | prog | `1e-6` | `1.0099999999999999e-06` |
| 406 | operator | `>` | `>=` |
| 424 | operator | `<=` | `<` |
| 428 | operator | `<=` | `<` |
| 465 | operator | `<` | `<=` |
| 466 | operator | `<` | `<=` |
| 466 | prog | `0.0` | `0.001` |
| 475 | operator | `<` | `<=` |
| 492 | operator | `<=` | `<` |
| 505 | operator | `<` | `<=` |
| 511 | operator | `<=` | `<` |
| 544 | operator | `<=` | `<` |
| 544 | prog | `0.0` | `0.001` |
| 559 | operator | `<` | `<=` |
| 559 | operator | `>` | `>=` |
| 564 | operator | `<` | `<=` |
| 580 | prog | `1e-9` | `1.01e-09` |
| 580 | operator | `<` | `<=` |
| 605 | operator | `<` | `<=` |
| 605 | prog | `3` | `4` |
| 640 | operator | `>` | `>=` |
| 640 | operator | `<` | `<=` |
| 643 | operator | `<=` | `<` |
| 643 | operator | `<=` | `<` |
| 653 | operator | `>` | `>=` |
| 679 | operator | `<` | `<=` |
| 679 | prog | `1e-12` | `1.01e-12` |
| 682 | prog | `3` | `4` |
| 682 | operator | `<` | `<=` |
| 692 | operator | `<` | `<=` |
| 692 | prog | `2` | `3` |
| 733 | operator | `<` | `<=` |
| 755 | operator | `<` | `<=` |

### `tools/blender/lod.py` — 37

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 107 | operator | `<=` | `<` |
| 107 | prog | `0.0` | `0.001` |
| 126 | prog | `0.0` | `0.001` |
| 129 | operator | `<` | `<=` |
| 129 | prog | `0.0` | `0.001` |
| 129 | operator | `>` | `>=` |
| 129 | prog | `1.0` | `1.01` |
| 143 | prog | `0.0` | `0.001` |
| 143 | prog | `0.0` | `0.001` |
| 151 | prog | `0.0` | `0.001` |
| 153 | prog | `0.0` | `0.001` |
| 183 | operator | `<` | `<=` |
| 199 | prog | `0.0` | `0.001` |
| 202 | operator | `<` | `<=` |
| 202 | prog | `0.0` | `0.001` |
| 202 | operator | `>` | `>=` |
| 202 | prog | `1.0` | `1.01` |
| 212 | operator | `<=` | `<` |
| 212 | prog | `0.0` | `0.001` |
| 217 | operator | `>` | `>=` |
| 217 | prog | `0.0` | `0.001` |
| 222 | prog | `0.0` | `0.001` |
| 232 | operator | `<` | `<=` |
| 232 | prog | `1e-12` | `1.01e-12` |
| 327 | operator | `<` | `<=` |
| 367 | operator | `<` | `<=` |
| 367 | operator | `<` | `<=` |
| 375 | operator | `<=` | `<` |
| 375 | prog | `0.0` | `0.001` |
| 404 | operator | `<` | `<=` |
| 404 | operator | `<` | `<=` |
| 411 | operator | `<=` | `<` |
| 411 | prog | `0.0` | `0.001` |
| 487 | operator | `<=` | `<` |
| 489 | operator | `<` | `<=` |
| 571 | operator | `>` | `>=` |
| 631 | prog | `0.0` | `0.001` |

### `tools/blender/m7_layout.py` — 1

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 192 | operator | `>=` | `>` |

### `tools/blender/m7_report.py` — 9

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 46 | operator | `<=` | `<` |
| 46 | operator | `<=` | `<` |
| 52 | operator | `<=` | `<` |
| 52 | operator | `<=` | `<` |
| 85 | operator | `>` | `>=` |
| 87 | operator | `>` | `>=` |
| 95 | operator | `<=` | `<` |
| 96 | operator | `<=` | `<` |
| 169 | operator | `>` | `>=` |

### `tools/blender/placement.py` — 26

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 32 | operator | `<=` | `<` |
| 32 | prog | `0.0` | `0.001` |
| 53 | operator | `>` | `>=` |
| 57 | operator | `<` | `<=` |
| 57 | operator | `<` | `<=` |
| 96 | operator | `<` | `<=` |
| 96 | prog | `1e-9` | `1.01e-09` |
| 100 | operator | `<` | `<=` |
| 100 | prog | `1e-9` | `1.01e-09` |
| 140 | operator | `>` | `>=` |
| 146 | operator | `<` | `<=` |
| 164 | operator | `<` | `<=` |
| 164 | prog | `1e-12` | `1.01e-12` |
| 181 | operator | `<` | `<=` |
| 202 | prog | `0.0` | `0.001` |
| 205 | operator | `<` | `<=` |
| 205 | operator | `>` | `>=` |
| 205 | prog | `1.0` | `1.01` |
| 212 | operator | `<` | `<=` |
| 229 | operator | `<` | `<=` |
| 229 | prog | `1e-9` | `1.01e-09` |
| 233 | operator | `<=` | `<` |
| 236 | prog | `1e-4` | `0.000101` |
| 236 | operator | `<=` | `<` |
| 258 | operator | `>` | `>=` |
| 313 | operator | `<=` | `<` |

### `tools/blender/profiles.py` — 1

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 33 | operator | `>` | `>=` |

### `tools/blender/sweep.py` — 37

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 54 | prog | `0.0` | `0.001` |
| 65 | operator | `>` | `>=` |
| 92 | prog | `0.0` | `0.001` |
| 126 | prog | `0.0` | `0.001` |
| 130 | operator | `>` | `>=` |
| 130 | operator | `<` | `<=` |
| 130 | prog | `0.0` | `0.001` |
| 130 | prog | `1.0` | `1.01` |
| 143 | operator | `>` | `>=` |
| 143 | prog | `1e-9` | `1.01e-09` |
| 161 | operator | `<` | `<=` |
| 161 | prog | `1e-9` | `1.01e-09` |
| 174 | operator | `<` | `<=` |
| 174 | prog | `1e-18` | `1.01e-18` |
| 204 | operator | `<` | `<=` |
| 204 | prog | `0.0` | `0.001` |
| 204 | operator | `<` | `<=` |
| 219 | operator | `<=` | `<` |
| 224 | operator | `>` | `>=` |
| 224 | prog | `1e-6` | `1.0099999999999999e-06` |
| 237 | operator | `<` | `<=` |
| 237 | operator | `<` | `<=` |
| 250 | operator | `<` | `<=` |
| 345 | operator | `>` | `>=` |
| 345 | prog | `0.0` | `0.001` |
| 380 | operator | `>` | `>=` |
| 380 | prog | `0.0` | `0.001` |
| 386 | operator | `<` | `<=` |
| 410 | prog | `1e-9` | `1.01e-09` |
| 410 | operator | `>` | `>=` |
| 477 | operator | `<` | `<=` |
| 487 | operator | `>` | `>=` |
| 487 | prog | `1` | `2` |
| 582 | operator | `<` | `<=` |
| 676 | operator | `>` | `>=` |
| 683 | prog | `0.0` | `0.001` |
| 696 | operator | `>` | `>=` |

### `tools/ci/assert_shot_metadata.py` — 6

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 84 | operator | `<=` | `<` |
| 84 | operator | `<=` | `<` |
| 183 | prog | `0.0` | `0.001` |
| 200 | prog | `0.0` | `0.001` |
| 242 | operator | `>` | `>=` |
| 242 | prog | `1e-3` | `0.00101` |

### `tools/physics/braking.py` — 5

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 163 | operator | `<=` | `<` |
| 163 | operator | `>=` | `>` |
| 165 | operator | `>` | `>=` |
| 287 | operator | `>` | `>=` |
| 287 | prog | `1.0` | `1.01` |

### `tools/physics/reference.py` — 3

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 34 | operator | `<=` | `<` |
| 45 | operator | `<` | `<=` |
| 52 | operator | `<` | `<=` |

### `tools/physics/schedule_envelope.py` — 5

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 55 | operator | `<=` | `<` |
| 57 | operator | `>=` | `>` |
| 90 | operator | `>` | `>=` |
| 100 | operator | `<=` | `<` |
| 114 | operator | `<=` | `<` |

### `tools/track/build_alignment.py` — 39

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 88 | operator | `<` | `<=` |
| 88 | operator | `>` | `>=` |
| 114 | operator | `<` | `<=` |
| 117 | operator | `<=` | `<` |
| 119 | operator | `<=` | `<` |
| 121 | operator | `<=` | `<` |
| 123 | operator | `>=` | `>` |
| 125 | operator | `>` | `>=` |
| 125 | prog | `1e-9` | `1.01e-09` |
| 142 | operator | `<=` | `<` |
| 147 | operator | `<=` | `<` |
| 147 | operator | `<=` | `<` |
| 149 | operator | `<=` | `<` |
| 225 | operator | `<` | `<=` |
| 225 | prog | `1e-9` | `1.01e-09` |
| 351 | operator | `>=` | `>` |
| 381 | operator | `==` | `!=` |
| 401 | operator | `==` | `!=` |
| 402 | operator | `==` | `!=` |
| 408 | operator | `==` | `!=` |
| 414 | operator | `<` | `<=` |
| 435 | operator | `!=` | `==` |
| 444 | operator | `!=` | `==` |
| 454 | operator | `!=` | `==` |
| 481 | operator | `==` | `!=` |
| 482 | operator | `!=` | `==` |
| 504 | operator | `>` | `>=` |
| 504 | prog | `1` | `2` |
| 546 | operator | `==` | `!=` |
| 590 | operator | `==` | `!=` |
| 590 | operator | `==` | `!=` |
| 604 | operator | `<=` | `<` |
| 646 | operator | `==` | `!=` |
| 646 | prog | `0` | `1` |
| 650 | operator | `==` | `!=` |
| 650 | prog | `0` | `1` |
| 782 | operator | `!=` | `==` |
| 788 | operator | `>` | `>=` |
| 798 | operator | `!=` | `==` |

### `tools/track/crosscheck_alignment.py` — 2

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 293 | operator | `>` | `>=` |
| 293 | operator | `<` | `<=` |

### `tools/track/crs.py` — 8

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 152 | operator | `>=` | `>` |
| 152 | prog | `0.0` | `0.001` |
| 163 | operator | `<` | `<=` |
| 172 | operator | `>` | `>=` |
| 300 | operator | `<` | `<=` |
| 300 | prog | `1e-12` | `1.01e-12` |
| 419 | operator | `<` | `<=` |
| 419 | prog | `1e-12` | `1.01e-12` |

### `tools/track/detail_layout.py` — 1

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 97 | operator | `<=` | `<` |

### `tools/track/inspire_rail.py` — 2

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 306 | operator | `<` | `<=` |
| 306 | operator | `>` | `>=` |

### `tools/track/make_test_track.py` — 2

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 19 | operator | `==` | `!=` |
| 19 | prog | `130` | `131` |

### `tools/track/shapefile.py` — 1

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 36 | operator | `<=` | `<` |

### `tools/track/station_layout.py` — 1

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 116 | operator | `<` | `<=` |

### `tools/track/surface_sections.py` — 1

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 158 | operator | `<=` | `<` |

### `tools/track/tunnel_width.py` — 2

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 199 | operator | `<` | `<=` |
| 199 | prog | `1e-9` | `1.01e-09` |

### `tools/track/validate.py` — 2

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 97 | prog | `0` | `1` |
| 97 | operator | `>=` | `>` |

### `tools/visual/framing.py` — 1

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 92 | operator | `>=` | `>` |

### `tools/visual/pngio.py` — 4

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 42 | operator | `<=` | `<` |
| 240 | prog | `0.0` | `0.001` |
| 240 | operator | `>` | `>=` |
| 240 | operator | `<` | `<=` |
