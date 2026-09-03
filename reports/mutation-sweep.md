# Przegląd mutacyjny bramek

**Snapshot na commicie:** `737d592` (`main`, 03.09.2026)

Ta wersja raportu jest **przeliczona od zera**. Poprzednia deklarowała snapshot
`8a4c55d`, a leżała w commicie `5f6b68e` — czyli opisywała inne drzewo niż to,
w którym stała, i to o wersję narzędzia wstecz. Dwa „zabicia", które wypisywała,
sprawdziłem ręcznie: obie mutacje żyją. Liczby niżej pochodzą z jednego przebiegu
na jednym drzewie i są odtwarzalne poleceniem z sekcji „Jak to powtórzyć".

Narzędzie: `tools/tests/mutation_sweep.py`. Mutowany jest **kod pod testem**,
nie testy. Mutacja, która przeżyła, znaczy jedno z dwojga: brak pokrycia albo
mutant równoważny. Narzędzie nie zgaduje, które to.

## Wynik

| | |
|---|---|
| mutacji | 961 |
| rozstrzygniętych | 960 |
| zabitych | 216 |
| **ocalałych** | **744** |
| nierozstrzygniętych | 1 |
| pokrycie (z rozstrzygniętych) | 22.5 % |

Nierozstrzygnięta znaczy, że przebieg testów nie doszedł do końca — ubity,
bez pamięci, błąd poza samą mutacją. **Nie liczy się jako zabicie.** Tu jest jedna:

- `tools/track/detail_layout.py:49`, operator `<=` → `<` — **przekroczony czas**, i to
  nie z powodu obciążenia maszyny. Pierwsza wersja tego akapitu tak zgadywała; zgadła źle.

  Wiersz 49 to `if step_m <= 0.0: raise ValueError(...)`, czyli strażnik przed krokiem
  zerowym. Osłabienie go do `<` wpuszcza `step_m == 0.0` do pętli
  `while index * step_m <= length_m + SAME_PLACE_M`, gdzie lewa strona jest **zawsze
  zerem** — pętla nie kończy się nigdy. Sprawdzone wykonaniem:

  ```
  $ sed -i '49s/step_m <= 0.0/step_m < 0.0/' tools/track/detail_layout.py
  $ timeout 20 python3 -c "... D.hectometre_marks(500.0, 0.0)"
  kod wyjścia: 124        # zawisł
  ```

  **To nie jest luka w pokryciu.** Test `test_layout_hectometre_step_must_be_positive`
  woła dokładnie `hectometre_marks(500.0, 0.0)` i oczekuje `ValueError` — bramka istnieje
  i jest sprawdzana. To jest **ograniczenie narzędzia**: mutacja, która zamienia strażnik
  w pętlę nieskończoną, nie może zostać zaraportowana jako zabita, bo proces testów nigdy
  nie kończy pracy. Przemiatanie widzi tylko sygnał zabójczy i uczciwie mówi
  „nierozstrzygnięta".

  Wniosek na przyszłość: `nierozstrzygnięta` z przekroczonego czasu warto obejrzeć
  RĘCZNIE, zanim się ją odłoży — bywa, że kryje najmocniejszy dowód, jaki mutacja może
  dać, czyli że bez tego warunku program w ogóle się nie zatrzymuje. Osobno warto
  rozważyć niezależny ogranicznik liczby iteracji w `hectometre_marks` — decyzja
  właściciela, nie moja.

## Kontrola: dlaczego te liczby są tak inne od poprzednich

Poprzedni raport podawał 536 zabitych i 425 ocalałych, czyli pokrycie 55,8 %.
Tu wychodzi 216 zabitych i 744 ocalałe, czyli 22,5 %. Różnica jest na tyle duża,
że nie wolno jej po prostu wpisać — więc sprawdziłem ją ręcznie w obie strony.

**Kontrola ocalałej.** Wziąłem `tools/blender/profiles.py:33`, mutację progu
`2 → 3` w warunku domykania konturu, i wprowadziłem ją do źródła na `main`:

```
    if len(out)>3 and math.dist(out[0],out[-1])<=eps: out.pop()
  692/692 przeszło
```

Cały zestaw pozostaje zielony. Mutacja rzeczywiście żyje.

**Kontrola zabicia.** Ten sam przebieg narzędzia na `tools/blender/tunnel_manifest.py`
(PR #142) dał 27 zabitych z 27, a na `tools/blender/m7_report.py` (PR #144) 22 z 31 —
czyli ścieżka „mutacja → czerwony test → zabita" działa i nie jest ślepa.

**Skąd więc tamte 536.** Poprzednie liczby deklarowały snapshot `8a4c55d`, a leżały
w commicie `5f6b68e`, i pochodziły z wersji narzędzia, o której ten sam raport pisał,
że liczyła przebiegi nierozstrzygnięte jako zabicia. Dwa konkretne „zabicia" z tamtej
listy sprawdziłem ręcznie wcześniej w tej sesji — obie mutacje żyją. Nie próbuję
odtworzyć tamtego przebiegu ani dociec, ile dokładnie zawyżał; stwierdzam tylko,
że **nie jest porównywalny** z tym i dlatego został zastąpiony, a nie dopisany obok.

## Podział, bez którego ten raport wprowadza w błąd

**Dziewięć modułów importuje `bpy` i przez to NIE DAJE SIĘ zaimportować
w `tools/tests/test_all.py`.** Ich mutacji nie da się zabić — nie dlatego, że nikt
nie napisał testu, tylko dlatego, że nie istnieje droga, którą test mógłby je
dotknąć. Wrzucanie ich do jednej puli z resztą zawyża liczbę „nieprzetestowanych
bramek" i psuje kolejność triażu.

| | plików | mutacji | ocalałych | udział |
|---|---:|---:|---:|---:|
| **osiągalne** (import bez Blendera działa) | 33 | 813 | 599 | 74 % |
| **nieosiągalne** (import wymaga `bpy`) | 9 | 148 | 145 | 98 % |
| razem | 42 | 961 | 744 | 77 % |

Różnica 98 % wobec 74 % nie jest oceną jakości tych modułów.
Jest miarą tego, ile z nich w ogóle da się dosięgnąć. Lekarstwem nie są tam testy,
tylko wyciągnięcie czystej logiki spod `bpy` — tak jak w PR #142 (`tunnel_sweep.py`)
i #144 (`m7_shell.py`).

### Moduły nieosiągalne

| plik | ocalałe / mutacje | udział |
|---|---:|---:|
| `tools/blender/m7_shell.py` | 35 / 35 | 100 % |
| `tools/blender/tunnel_sweep.py` | 35 / 35 | 100 % |
| `tools/blender/profile_vehicle.py` | 26 / 26 | 100 % |
| `tools/blender/glb_roundtrip.py` | 10 / 10 | 100 % |
| `tools/visual/capture_blender.py` | 10 / 10 | 100 % |
| `tools/blender/render_check.py` | 8 / 8 | 100 % |
| `tools/blender/station_kit.py` | 8 / 9 | 89 % |
| `tools/blender/place_vehicle.py` | 7 / 7 | 100 % |
| `tools/blender/detail_markers.py` | 6 / 8 | 75 % |

Trzy mutacje w tej grupie mimo wszystko padły (145 ocalałych z 148) — łapią je
testy, które czytają te pliki jako TEKST albo uruchamiają je podprocesem, a nie
importują. To jedyna droga, jaka tam dziś istnieje.

## Ocalałe w modułach osiągalnych — kolejność triażu

Kolejność jest po **udziale**, nie po liczbie. Wysoki udział znaczy, że testy
tego modułu sprawdzają co innego, niż deklarują; duża liczba przy niskim udziale
znaczy tylko, że moduł jest duży.

| plik | ocalałe / mutacje | udział | stan |
|---|---:|---:|---|
| `tools/track/fetch_osm_routes.py` | 9 / 9 | 100 % | — |
| `tools/track/crs.py` | 8 / 8 | 100 % | — |
| `tools/track/make_test_track.py` | 2 / 2 | 100 % | — |
| `tools/track/crosscheck_alignment.py` | 18 / 19 | 95 % | — |
| `tools/blender/clearance.py` | 12 / 13 | 92 % | triaż w #127 (13 → 6) |
| `tools/blender/clearance_profile.py` | 70 / 77 | 91 % | triaż w #128 (72 → 66) |
| `tools/physics/schedule_envelope.py` | 9 / 10 | 90 % | — |
| `tools/track/detail_layout.py` | 7 / 8 | 88 % | — |
| `tools/track/network_chainage.py` | 6 / 7 | 86 % | — |
| `tools/blender/profiles.py` | 11 / 13 | 85 % | — |
| `tools/track/surface_sections.py` | 24 / 29 | 83 % | — |
| `tools/track/build_alignment.py` | 57 / 69 | 83 % | triaż w #143 (57 → 39) |
| `tools/track/data_freshness.py` | 4 / 5 | 80 % | — |
| `tools/blender/sweep.py` | 63 / 79 | 80 % | triaż w #132 (63 → 37) |
| `tools/track/tunnel_width.py` | 22 / 28 | 79 % | — |
| `tools/blender/placement.py` | 32 / 42 | 76 % | triaż w #140 |
| `tools/track/inspire_rail.py` | 30 / 41 | 73 % | — |
| `tools/visual/framing.py` | 16 / 22 | 73 % | — |
| `tools/physics/braking.py` | 8 / 11 | 73 % | — |
| `tools/blender/lod.py` | 75 / 105 | 71 % | triaż w #130 (75 → 38) |
| `tools/track/station_layout.py` | 5 / 7 | 71 % | — |
| `tools/visual/compare.py` | 16 / 24 | 67 % | — |
| `tools/visual/pngio.py` | 25 / 38 | 66 % | — |
| `tools/track/validate.py` | 23 / 36 | 64 % | — |
| `tools/physics/reference.py` | 5 / 8 | 62 % | — |
| `tools/data/provenance.py` | 4 / 7 | 57 % | — |
| `tools/ci/assert_shot_metadata.py` | 16 / 33 | 48 % | — |
| `tools/track/timetable.py` | 7 / 15 | 47 % | — |
| `tools/blender/m7_layout.py` | 6 / 17 | 35 % | — |
| `tools/track/shapefile.py` | 6 / 17 | 35 % | — |
| `tools/track/normalize_stops.py` | 3 / 9 | 33 % | — |
| `tools/ci/assert_empty_frame_negative.py` | 0 / 4 | 0 % | — |
| `tools/data/snapshot_source.py` | 0 / 1 | 0 % | — |

Liczby w kolumnie „stan" są stanem PO scaleniu tamtych PR-ów; ten raport mierzy
`main`, więc ich jeszcze nie widzi. Podaję je, żeby nikt nie zaczynał triażu od
modułu, który ktoś już przerobił.

## Ocalałe, per plik

### `tools/blender/lod.py` — 75

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 72 | operator | `==` | `!=` |
| 91 | operator | `<=` | `<` |
| 91 | prog | `0.0` | `0.001` |
| 110 | operator | `<=` | `<` |
| 110 | prog | `0.0` | `0.001` |
| 113 | operator | `<` | `<=` |
| 113 | operator | `>` | `>=` |
| 113 | prog | `1.0` | `1.01` |
| 113 | prog | `0.0` | `0.001` |
| 125 | operator | `<=` | `<` |
| 127 | prog | `0.0` | `0.001` |
| 127 | prog | `0.0` | `0.001` |
| 134 | operator | `<=` | `<` |
| 135 | operator | `>` | `>=` |
| 135 | operator | `>` | `>=` |
| 135 | prog | `0.0` | `0.001` |
| 137 | operator | `>` | `>=` |
| 137 | prog | `0.0` | `0.001` |
| 167 | operator | `<` | `<=` |
| 183 | operator | `<=` | `<` |
| 183 | prog | `0.0` | `0.001` |
| 186 | operator | `<` | `<=` |
| 186 | operator | `>` | `>=` |
| 186 | prog | `1.0` | `1.01` |
| 186 | prog | `0.0` | `0.001` |
| 196 | operator | `<=` | `<` |
| 196 | prog | `0.0` | `0.001` |
| 199 | operator | `<` | `<=` |
| 199 | prog | `3` | `4` |
| 201 | operator | `>` | `>=` |
| 201 | prog | `0.0` | `0.001` |
| 206 | operator | `<=` | `<` |
| 206 | prog | `0.0` | `0.001` |
| 216 | operator | `<` | `<=` |
| 216 | prog | `1e-12` | `1.01e-12` |
| 265 | operator | `<` | `<=` |
| 265 | prog | `2` | `3` |
| 301 | operator | `>=` | `>` |
| 301 | prog | `3` | `4` |
| 311 | operator | `<` | `<=` |
| 351 | operator | `<` | `<=` |
| 351 | operator | `<` | `<=` |
| 359 | operator | `<=` | `<` |
| 359 | prog | `0.0` | `0.001` |
| 388 | operator | `<` | `<=` |
| 388 | operator | `<` | `<=` |
| 395 | operator | `<=` | `<` |
| 395 | prog | `0.0` | `0.001` |
| 471 | operator | `<=` | `<` |
| 471 | operator | `<=` | `<` |
| 473 | operator | `<` | `<=` |
| 480 | operator | `>=` | `>` |
| 487 | prog | `0` | `1` |
| 519 | operator | `<=` | `<` |
| 552 | operator | `<=` | `<` |
| 554 | operator | `<=` | `<` |
| 554 | operator | `>` | `>=` |
| 554 | prog | `0` | `1` |
| 576 | operator | `>` | `>=` |
| 579 | operator | `<` | `<=` |
| 583 | operator | `<=` | `<` |
| 583 | operator | `<=` | `<` |
| 583 | prog | `0` | `1` |
| 583 | prog | `0` | `1` |
| 585 | operator | `>` | `>=` |
| 586 | operator | `>` | `>=` |
| 594 | operator | `>=` | `>` |
| 598 | operator | `<` | `<=` |
| 598 | prog | `0.0` | `0.001` |
| 601 | operator | `<=` | `<` |
| 601 | prog | `0.0` | `0.001` |
| 603 | operator | `<=` | `<` |
| 603 | prog | `0.0` | `0.001` |
| 605 | operator | `>` | `>=` |
| 606 | operator | `>` | `>=` |

### `tools/blender/clearance_profile.py` — 70

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 91 | operator | `<=` | `<` |
| 91 | prog | `2` | `3` |
| 99 | operator | `<=` | `<` |
| 99 | prog | `0.0` | `0.001` |
| 104 | operator | `<=` | `<` |
| 104 | prog | `0.0` | `0.001` |
| 119 | prog | `0.0` | `0.001` |
| 169 | operator | `<` | `<=` |
| 169 | prog | `3` | `4` |
| 174 | operator | `>` | `>=` |
| 174 | prog | `0.0` | `0.001` |
| 181 | operator | `<` | `<=` |
| 185 | operator | `<=` | `<` |
| 185 | prog | `0.0` | `0.001` |
| 196 | operator | `<=` | `<` |
| 198 | operator | `>=` | `>` |
| 198 | prog | `0.9` | `0.909` |
| 200 | operator | `>=` | `>` |
| 200 | prog | `0.9` | `0.909` |
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
| 559 | operator | `>` | `>=` |
| 559 | operator | `<` | `<=` |
| 564 | operator | `<` | `<=` |
| 580 | operator | `<` | `<=` |
| 580 | prog | `1e-9` | `1.01e-09` |
| 605 | operator | `<` | `<=` |
| 605 | prog | `3` | `4` |
| 640 | operator | `<` | `<=` |
| 640 | operator | `>` | `>=` |
| 643 | operator | `<=` | `<` |
| 643 | operator | `<=` | `<` |
| 653 | operator | `>` | `>=` |
| 679 | operator | `<` | `<=` |
| 679 | prog | `1e-12` | `1.01e-12` |
| 682 | operator | `<` | `<=` |
| 682 | prog | `3` | `4` |
| 692 | operator | `<` | `<=` |
| 692 | prog | `2` | `3` |
| 733 | operator | `<` | `<=` |
| 755 | operator | `<` | `<=` |

### `tools/blender/sweep.py` — 63

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 54 | operator | `<=` | `<` |
| 54 | prog | `0.0` | `0.001` |
| 65 | operator | `>` | `>=` |
| 92 | operator | `<` | `<=` |
| 92 | prog | `3` | `4` |
| 92 | prog | `0.0` | `0.001` |
| 126 | operator | `<=` | `<` |
| 126 | prog | `0.0` | `0.001` |
| 130 | operator | `<` | `<=` |
| 130 | operator | `>` | `>=` |
| 130 | prog | `1.0` | `1.01` |
| 130 | prog | `0.0` | `0.001` |
| 143 | operator | `>` | `>=` |
| 143 | prog | `1e-9` | `1.01e-09` |
| 157 | operator | `<` | `<=` |
| 157 | prog | `2` | `3` |
| 161 | operator | `<` | `<=` |
| 161 | prog | `1e-9` | `1.01e-09` |
| 174 | operator | `<` | `<=` |
| 174 | prog | `1e-18` | `1.01e-18` |
| 204 | operator | `<` | `<=` |
| 204 | operator | `<` | `<=` |
| 204 | prog | `0.0` | `0.001` |
| 219 | operator | `<=` | `<` |
| 224 | operator | `>` | `>=` |
| 224 | prog | `1e-6` | `1.0099999999999999e-06` |
| 234 | operator | `>=` | `>` |
| 237 | operator | `>=` | `>` |
| 237 | operator | `<` | `<=` |
| 237 | operator | `<` | `<=` |
| 247 | operator | `>=` | `>` |
| 250 | operator | `<` | `<=` |
| 298 | operator | `<` | `<=` |
| 298 | prog | `2` | `3` |
| 300 | operator | `<=` | `<` |
| 345 | operator | `>` | `>=` |
| 345 | prog | `0.0` | `0.001` |
| 380 | operator | `>` | `>=` |
| 380 | prog | `0.0` | `0.001` |
| 386 | operator | `<` | `<=` |
| 410 | operator | `>` | `>=` |
| 410 | prog | `1e-9` | `1.01e-09` |
| 477 | operator | `<` | `<=` |
| 487 | operator | `>` | `>=` |
| 487 | operator | `>=` | `>` |
| 487 | prog | `1` | `2` |
| 528 | operator | `<` | `<=` |
| 571 | operator | `>=` | `>` |
| 571 | prog | `0.0` | `0.001` |
| 582 | operator | `<` | `<=` |
| 676 | operator | `>` | `>=` |
| 678 | operator | `>` | `>=` |
| 683 | operator | `<=` | `<` |
| 683 | prog | `0.0` | `0.001` |
| 685 | operator | `>` | `>=` |
| 687 | operator | `<=` | `<` |
| 687 | prog | `0` | `1` |
| 687 | prog | `0` | `1` |
| 690 | operator | `<=` | `<` |
| 690 | prog | `0.0` | `0.001` |
| 695 | operator | `>` | `>=` |
| 696 | operator | `>` | `>=` |
| 700 | operator | `>` | `>=` |

### `tools/track/build_alignment.py` — 57

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 85 | operator | `<=` | `<` |
| 85 | prog | `0.0` | `0.001` |
| 88 | operator | `>` | `>=` |
| 88 | operator | `<` | `<=` |
| 88 | prog | `0.0` | `0.001` |
| 88 | prog | `1.0` | `1.01` |
| 91 | operator | `<` | `<=` |
| 110 | operator | `<` | `<=` |
| 110 | operator | `>` | `>=` |
| 113 | operator | `<=` | `<` |
| 113 | operator | `<` | `<=` |
| 115 | operator | `<=` | `<` |
| 117 | operator | `<` | `<=` |
| 117 | operator | `<=` | `<` |
| 119 | operator | `>=` | `>` |
| 121 | operator | `>` | `>=` |
| 121 | prog | `1e-9` | `1.01e-09` |
| 125 | operator | `<` | `<=` |
| 125 | prog | `1e-6` | `1.0099999999999999e-06` |
| 138 | operator | `<=` | `<` |
| 138 | prog | `0` | `1` |
| 140 | operator | `>=` | `>` |
| 143 | operator | `<=` | `<` |
| 143 | operator | `<=` | `<` |
| 145 | operator | `<=` | `<` |
| 145 | prog | `0` | `1` |
| 165 | operator | `>` | `>=` |
| 183 | operator | `>` | `>=` |
| 221 | operator | `<` | `<=` |
| 221 | prog | `1e-9` | `1.01e-09` |
| 247 | operator | `==` | `!=` |
| 250 | prog | `1` | `2` |
| 261 | operator | `==` | `!=` |
| 347 | operator | `>=` | `>` |
| 377 | operator | `==` | `!=` |
| 397 | operator | `==` | `!=` |
| 398 | operator | `==` | `!=` |
| 404 | operator | `==` | `!=` |
| 410 | operator | `<` | `<=` |
| 431 | operator | `!=` | `==` |
| 440 | operator | `!=` | `==` |
| 450 | operator | `!=` | `==` |
| 477 | operator | `==` | `!=` |
| 478 | operator | `!=` | `==` |
| 500 | operator | `>` | `>=` |
| 500 | prog | `1` | `2` |
| 542 | operator | `==` | `!=` |
| 586 | operator | `==` | `!=` |
| 586 | operator | `==` | `!=` |
| 600 | operator | `<=` | `<` |
| 642 | operator | `==` | `!=` |
| 642 | prog | `0` | `1` |
| 646 | operator | `==` | `!=` |
| 646 | prog | `0` | `1` |
| 778 | operator | `!=` | `==` |
| 784 | operator | `>` | `>=` |
| 794 | operator | `!=` | `==` |

### `tools/blender/m7_shell.py` — 35

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 82 | operator | `<=` | `<` |
| 82 | operator | `<=` | `<` |
| 88 | operator | `<=` | `<` |
| 88 | operator | `<=` | `<` |
| 189 | operator | `==` | `!=` |
| 244 | operator | `>` | `>=` |
| 246 | operator | `>` | `>=` |
| 246 | prog | `0` | `1` |
| 254 | operator | `<=` | `<` |
| 255 | operator | `<=` | `<` |
| 287 | operator | `>` | `>=` |
| 289 | operator | `>` | `>=` |
| 291 | operator | `>` | `>=` |
| 291 | operator | `>` | `>=` |
| 293 | operator | `>` | `>=` |
| 295 | operator | `>` | `>=` |
| 297 | operator | `!=` | `==` |
| 301 | operator | `<` | `<=` |
| 301 | operator | `<` | `<=` |
| 301 | prog | `1000` | `1001` |
| 301 | prog | `500000` | `500001` |
| 305 | operator | `>` | `>=` |
| 305 | operator | `<=` | `<` |
| 305 | prog | `0.0` | `0.001` |
| 310 | operator | `==` | `!=` |
| 311 | operator | `==` | `!=` |
| 320 | operator | `!=` | `==` |
| 322 | operator | `!=` | `==` |
| 328 | operator | `>` | `>=` |
| 328 | operator | `==` | `!=` |
| 371 | operator | `==` | `!=` |
| 384 | operator | `==` | `!=` |
| 384 | operator | `<=` | `<` |
| 422 | operator | `<` | `<=` |
| 422 | operator | `>` | `>=` |

### `tools/blender/tunnel_sweep.py` — 35

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 119 | operator | `==` | `!=` |
| 119 | prog | `0` | `1` |
| 138 | operator | `==` | `!=` |
| 138 | prog | `0` | `1` |
| 272 | operator | `==` | `!=` |
| 276 | operator | `==` | `!=` |
| 276 | prog | `0` | `1` |
| 289 | operator | `==` | `!=` |
| 289 | prog | `0` | `1` |
| 325 | operator | `==` | `!=` |
| 329 | operator | `==` | `!=` |
| 356 | operator | `==` | `!=` |
| 356 | prog | `0` | `1` |
| 410 | operator | `<` | `<=` |
| 410 | prog | `2` | `3` |
| 417 | operator | `==` | `!=` |
| 418 | operator | `==` | `!=` |
| 419 | operator | `==` | `!=` |
| 419 | operator | `!=` | `==` |
| 421 | operator | `==` | `!=` |
| 438 | operator | `==` | `!=` |
| 594 | operator | `>` | `>=` |
| 596 | operator | `>` | `>=` |
| 603 | operator | `<` | `<=` |
| 603 | prog | `0.0` | `0.001` |
| 605 | operator | `<=` | `<` |
| 605 | prog | `0.0` | `0.001` |
| 607 | operator | `==` | `!=` |
| 607 | operator | `==` | `!=` |
| 607 | prog | `0` | `1` |
| 607 | prog | `0` | `1` |
| 609 | operator | `>` | `>=` |
| 619 | operator | `>` | `>=` |
| 621 | operator | `>` | `>=` |
| 621 | prog | `0.01` | `0.0101` |

### `tools/blender/placement.py` — 32

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 30 | operator | `<=` | `<` |
| 32 | operator | `<=` | `<` |
| 32 | prog | `0.0` | `0.001` |
| 53 | operator | `>` | `>=` |
| 57 | operator | `<` | `<=` |
| 57 | operator | `<` | `<=` |
| 96 | operator | `<` | `<=` |
| 96 | prog | `1e-9` | `1.01e-09` |
| 100 | operator | `<` | `<=` |
| 100 | prog | `1e-9` | `1.01e-09` |
| 140 | operator | `<` | `<=` |
| 140 | operator | `>` | `>=` |
| 146 | operator | `<` | `<=` |
| 156 | operator | `<` | `<=` |
| 156 | prog | `1e-12` | `1.01e-12` |
| 156 | prog | `0.0` | `0.001` |
| 169 | operator | `<=` | `<` |
| 169 | operator | `<=` | `<` |
| 173 | operator | `<` | `<=` |
| 194 | prog | `0.0` | `0.001` |
| 197 | operator | `<` | `<=` |
| 197 | operator | `>` | `>=` |
| 197 | prog | `1.0` | `1.01` |
| 204 | operator | `<` | `<=` |
| 221 | operator | `<` | `<=` |
| 221 | prog | `1e-9` | `1.01e-09` |
| 225 | operator | `<=` | `<` |
| 228 | operator | `<=` | `<` |
| 228 | prog | `1e-4` | `0.000101` |
| 250 | operator | `>` | `>=` |
| 263 | operator | `<` | `<=` |
| 305 | operator | `<=` | `<` |

### `tools/track/inspire_rail.py` — 30

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 207 | operator | `<` | `<=` |
| 244 | operator | `==` | `!=` |
| 279 | operator | `<=` | `<` |
| 302 | operator | `<=` | `<` |
| 302 | prog | `0.0` | `0.001` |
| 306 | operator | `>` | `>=` |
| 306 | operator | `<` | `<=` |
| 306 | prog | `0.0` | `0.001` |
| 306 | prog | `1.0` | `1.01` |
| 309 | operator | `<` | `<=` |
| 334 | operator | `<=` | `<` |
| 334 | operator | `>=` | `>` |
| 334 | prog | `1e-3` | `0.00101` |
| 352 | operator | `<` | `<=` |
| 352 | operator | `>=` | `>` |
| 375 | operator | `<` | `<=` |
| 377 | operator | `>` | `>=` |
| 377 | operator | `>` | `>=` |
| 402 | operator | `<=` | `<` |
| 403 | operator | `<` | `<=` |
| 403 | prog | `0.0` | `0.001` |
| 404 | operator | `>` | `>=` |
| 404 | prog | `0.0` | `0.001` |
| 405 | operator | `>=` | `>` |
| 432 | operator | `==` | `!=` |
| 569 | operator | `!=` | `==` |
| 569 | operator | `!=` | `==` |
| 569 | prog | `1` | `2` |
| 569 | prog | `1` | `2` |
| 624 | operator | `==` | `!=` |

### `tools/blender/profile_vehicle.py` — 26

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 90 | operator | `==` | `!=` |
| 172 | operator | `>` | `>=` |
| 202 | operator | `<=` | `<` |
| 202 | operator | `<` | `<=` |
| 202 | prog | `0` | `1` |
| 231 | operator | `>` | `>=` |
| 231 | prog | `0.0` | `0.001` |
| 237 | operator | `<=` | `<` |
| 273 | operator | `>` | `>=` |
| 273 | prog | `0` | `1` |
| 285 | operator | `==` | `!=` |
| 369 | operator | `<=` | `<` |
| 369 | operator | `>=` | `>` |
| 373 | operator | `==` | `!=` |
| 373 | operator | `<` | `<=` |
| 373 | prog | `0` | `1` |
| 373 | prog | `1e-9` | `1.01e-09` |
| 391 | operator | `<=` | `<` |
| 391 | operator | `<=` | `<` |
| 431 | operator | `==` | `!=` |
| 431 | operator | `!=` | `==` |
| 515 | operator | `==` | `!=` |
| 519 | operator | `>` | `>=` |
| 522 | operator | `==` | `!=` |
| 522 | operator | `>` | `>=` |
| 531 | operator | `<` | `<=` |

### `tools/visual/pngio.py` — 25

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 42 | operator | `<=` | `<` |
| 42 | operator | `<=` | `<` |
| 44 | operator | `<=` | `<` |
| 58 | prog | `1` | `2` |
| 61 | prog | `2` | `3` |
| 64 | prog | `3` | `4` |
| 66 | operator | `>=` | `>` |
| 68 | prog | `4` | `5` |
| 70 | operator | `>=` | `>` |
| 71 | operator | `>=` | `>` |
| 89 | operator | `<=` | `<` |
| 98 | operator | `==` | `!=` |
| 105 | prog | `3` | `4` |
| 121 | operator | `>=` | `>` |
| 121 | prog | `3` | `4` |
| 126 | operator | `>=` | `>` |
| 126 | prog | `3` | `4` |
| 148 | operator | `>` | `>=` |
| 148 | operator | `<` | `<=` |
| 148 | prog | `1.0` | `1.01` |
| 148 | prog | `0.0` | `0.001` |
| 165 | operator | `<` | `<=` |
| 165 | operator | `>` | `>=` |
| 165 | prog | `0.0` | `0.001` |
| 165 | prog | `1.0` | `1.01` |

### `tools/track/surface_sections.py` — 24

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 118 | operator | `<=` | `<` |
| 118 | operator | `<=` | `<` |
| 119 | operator | `<=` | `<` |
| 119 | operator | `<=` | `<` |
| 144 | operator | `>=` | `>` |
| 144 | operator | `>=` | `>` |
| 151 | operator | `>` | `>=` |
| 151 | prog | `1e-6` | `1.0099999999999999e-06` |
| 158 | operator | `>` | `>=` |
| 158 | operator | `<=` | `<` |
| 158 | operator | `<=` | `<` |
| 202 | operator | `<` | `<=` |
| 219 | operator | `!=` | `==` |
| 222 | operator | `!=` | `==` |
| 252 | operator | `<` | `<=` |
| 264 | operator | `<=` | `<` |
| 299 | operator | `==` | `!=` |
| 323 | operator | `==` | `!=` |
| 334 | operator | `==` | `!=` |
| 340 | operator | `==` | `!=` |
| 343 | operator | `==` | `!=` |
| 384 | operator | `!=` | `==` |
| 404 | operator | `==` | `!=` |
| 432 | operator | `==` | `!=` |

### `tools/track/validate.py` — 23

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 26 | operator | `<` | `<=` |
| 26 | prog | `1e-9` | `1.01e-09` |
| 57 | operator | `>` | `>=` |
| 67 | operator | `<` | `<=` |
| 67 | prog | `1e-6` | `1.0099999999999999e-06` |
| 69 | operator | `>` | `>=` |
| 70 | operator | `>` | `>=` |
| 71 | operator | `>=` | `>` |
| 71 | prog | `0` | `1` |
| 75 | operator | `<` | `<=` |
| 76 | operator | `<` | `<=` |
| 77 | operator | `>=` | `>` |
| 77 | operator | `!=` | `==` |
| 77 | prog | `0` | `1` |
| 107 | operator | `>` | `>=` |
| 110 | operator | `>` | `>=` |
| 114 | operator | `<` | `<=` |
| 117 | operator | `<` | `<=` |
| 122 | operator | `>` | `>=` |
| 122 | prog | `5` | `6` |
| 140 | operator | `<=` | `<` |
| 140 | operator | `<=` | `<` |
| 140 | prog | `5` | `6` |

### `tools/track/tunnel_width.py` — 22

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 48 | operator | `<` | `<=` |
| 48 | operator | `>` | `>=` |
| 48 | operator | `>` | `>=` |
| 61 | operator | `<` | `<=` |
| 61 | prog | `1e-12` | `1.01e-12` |
| 65 | operator | `<=` | `<` |
| 65 | operator | `<=` | `<` |
| 65 | operator | `<` | `<=` |
| 65 | operator | `>` | `>=` |
| 65 | prog | `1e-6` | `1.0099999999999999e-06` |
| 100 | operator | `<=` | `<` |
| 100 | prog | `0.0` | `0.001` |
| 104 | operator | `<` | `<=` |
| 104 | prog | `0.0` | `0.001` |
| 120 | operator | `<` | `<=` |
| 120 | prog | `1e-9` | `1.01e-09` |
| 172 | operator | `==` | `!=` |
| 194 | operator | `<` | `<=` |
| 199 | operator | `<` | `<=` |
| 199 | prog | `1e-9` | `1.01e-09` |
| 222 | operator | `<=` | `<` |
| 312 | operator | `==` | `!=` |

### `tools/track/crosscheck_alignment.py` — 18

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 69 | operator | `!=` | `==` |
| 69 | operator | `>` | `>=` |
| 69 | operator | `>` | `>=` |
| 71 | operator | `<` | `<=` |
| 78 | operator | `==` | `!=` |
| 80 | operator | `==` | `!=` |
| 153 | operator | `==` | `!=` |
| 154 | operator | `==` | `!=` |
| 233 | operator | `<=` | `<` |
| 246 | operator | `==` | `!=` |
| 264 | operator | `==` | `!=` |
| 289 | operator | `<=` | `<` |
| 289 | prog | `0` | `1` |
| 293 | operator | `<` | `<=` |
| 293 | operator | `>` | `>=` |
| 293 | prog | `1.0` | `1.01` |
| 317 | operator | `!=` | `==` |
| 321 | operator | `==` | `!=` |

### `tools/ci/assert_shot_metadata.py` — 16

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 126 | operator | `<=` | `<` |
| 126 | prog | `0.0` | `0.001` |
| 132 | operator | `>` | `>=` |
| 139 | operator | `>` | `>=` |
| 143 | prog | `0.0` | `0.001` |
| 166 | prog | `0` | `1` |
| 176 | operator | `>` | `>=` |
| 176 | prog | `1e-3` | `0.00101` |
| 178 | operator | `<=` | `<` |
| 178 | prog | `0.0` | `0.001` |
| 189 | operator | `<` | `<=` |
| 189 | operator | `>` | `>=` |
| 195 | operator | `>` | `>=` |
| 204 | operator | `>` | `>=` |
| 219 | operator | `>` | `>=` |
| 219 | prog | `1.0` | `1.01` |

### `tools/visual/compare.py` — 16

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 71 | operator | `>` | `>=` |
| 96 | operator | `>=` | `>` |
| 97 | operator | `>=` | `>` |
| 98 | operator | `>=` | `>` |
| 135 | operator | `>` | `>=` |
| 135 | prog | `0.02` | `0.0202` |
| 147 | prog | `0` | `1` |
| 185 | operator | `>` | `>=` |
| 186 | operator | `>` | `>=` |
| 187 | operator | `<` | `<=` |
| 248 | operator | `<=` | `<` |
| 258 | operator | `<=` | `<` |
| 325 | operator | `==` | `!=` |
| 326 | operator | `==` | `!=` |
| 329 | operator | `==` | `!=` |
| 374 | operator | `==` | `!=` |

### `tools/visual/framing.py` — 16

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 19 | operator | `<` | `<=` |
| 19 | prog | `1e-12` | `1.01e-12` |
| 48 | operator | `>` | `>=` |
| 92 | operator | `>=` | `>` |
| 164 | operator | `>` | `>=` |
| 168 | operator | `<=` | `<` |
| 256 | operator | `>` | `>=` |
| 256 | prog | `0.2` | `0.202` |
| 286 | operator | `>` | `>=` |
| 286 | operator | `<=` | `<` |
| 286 | operator | `<=` | `<` |
| 286 | prog | `0` | `1` |
| 289 | operator | `<=` | `<` |
| 289 | prog | `1e-9` | `1.01e-09` |
| 293 | operator | `<=` | `<` |
| 293 | operator | `<=` | `<` |

### `tools/blender/clearance.py` — 12

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 47 | operator | `<=` | `<` |
| 47 | prog | `0.0` | `0.001` |
| 50 | operator | `>=` | `>` |
| 66 | operator | `<` | `<=` |
| 66 | prog | `1e-12` | `1.01e-12` |
| 66 | prog | `0.0` | `0.001` |
| 92 | operator | `<` | `<=` |
| 92 | operator | `>` | `>=` |
| 95 | operator | `<=` | `<` |
| 95 | operator | `<=` | `<` |
| 97 | operator | `<=` | `<` |
| 97 | prog | `0.0` | `0.001` |

### `tools/blender/profiles.py` — 11

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 32 | operator | `>` | `>=` |
| 33 | operator | `<=` | `<` |
| 33 | operator | `>` | `>=` |
| 33 | prog | `2` | `3` |
| 48 | operator | `<=` | `<` |
| 48 | operator | `<=` | `<` |
| 54 | operator | `<=` | `<` |
| 54 | operator | `<=` | `<` |
| 56 | operator | `<=` | `<` |
| 56 | operator | `<=` | `<` |
| 70 | operator | `>` | `>=` |

### `tools/blender/glb_roundtrip.py` — 10

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 41 | operator | `==` | `!=` |
| 77 | operator | `==` | `!=` |
| 77 | operator | `==` | `!=` |
| 77 | prog | `0` | `1` |
| 77 | prog | `0` | `1` |
| 81 | operator | `!=` | `==` |
| 89 | operator | `>` | `>=` |
| 93 | operator | `<` | `<=` |
| 93 | operator | `>` | `>=` |
| 95 | operator | `<` | `<=` |

### `tools/visual/capture_blender.py` — 10

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 70 | operator | `>=` | `>` |
| 82 | operator | `!=` | `==` |
| 127 | operator | `==` | `!=` |
| 186 | operator | `!=` | `==` |
| 186 | prog | `3` | `4` |
| 231 | operator | `<=` | `<` |
| 231 | operator | `<=` | `<` |
| 233 | operator | `<=` | `<` |
| 233 | prog | `0.0` | `0.001` |
| 250 | operator | `!=` | `==` |

### `tools/physics/schedule_envelope.py` — 9

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 55 | operator | `<=` | `<` |
| 55 | prog | `0.0` | `0.001` |
| 57 | operator | `>=` | `>` |
| 90 | operator | `>` | `>=` |
| 100 | operator | `<=` | `<` |
| 109 | operator | `>` | `>=` |
| 114 | operator | `<=` | `<` |
| 114 | prog | `0.0` | `0.001` |
| 116 | operator | `>` | `>=` |

### `tools/track/fetch_osm_routes.py` — 9

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 81 | operator | `==` | `!=` |
| 81 | operator | `==` | `!=` |
| 88 | operator | `!=` | `==` |
| 88 | operator | `!=` | `==` |
| 90 | operator | `!=` | `==` |
| 101 | operator | `==` | `!=` |
| 104 | operator | `!=` | `==` |
| 108 | operator | `<` | `<=` |
| 108 | prog | `2` | `3` |

### `tools/blender/render_check.py` — 8

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 32 | operator | `==` | `!=` |
| 61 | operator | `<` | `<=` |
| 61 | prog | `1e-9` | `1.01e-09` |
| 82 | operator | `<` | `<=` |
| 82 | prog | `2` | `3` |
| 91 | operator | `>` | `>=` |
| 91 | prog | `0.995` | `1.00495` |
| 104 | operator | `==` | `!=` |

### `tools/blender/station_kit.py` — 8

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 95 | operator | `>` | `>=` |
| 96 | operator | `>` | `>=` |
| 99 | operator | `<` | `<=` |
| 112 | operator | `<` | `<=` |
| 121 | operator | `<` | `<=` |
| 182 | operator | `!=` | `==` |
| 189 | operator | `>` | `>=` |
| 189 | prog | `0` | `1` |

### `tools/physics/braking.py` — 8

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 163 | operator | `>=` | `>` |
| 163 | operator | `<=` | `<` |
| 165 | operator | `>` | `>=` |
| 200 | operator | `<` | `<=` |
| 230 | operator | `>=` | `>` |
| 231 | operator | `>=` | `>` |
| 287 | operator | `>` | `>=` |
| 287 | prog | `1.0` | `1.01` |

### `tools/track/crs.py` — 8

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 145 | operator | `<` | `<=` |
| 145 | operator | `<` | `<=` |
| 153 | operator | `<` | `<=` |
| 153 | prog | `1e-12` | `1.01e-12` |
| 234 | operator | `<` | `<=` |
| 234 | prog | `1e-14` | `1.0100000000000001e-14` |
| 244 | operator | `<` | `<=` |
| 244 | prog | `1e-12` | `1.01e-12` |

### `tools/blender/place_vehicle.py` — 7

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 61 | operator | `==` | `!=` |
| 81 | operator | `<=` | `<` |
| 81 | operator | `<` | `<=` |
| 81 | prog | `0` | `1` |
| 90 | operator | `==` | `!=` |
| 124 | operator | `<` | `<=` |
| 182 | operator | `<` | `<=` |

### `tools/track/detail_layout.py` — 7

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 49 | prog | `0.0` | `0.001` |
| 53 | operator | `<=` | `<` |
| 61 | operator | `<=` | `<` |
| 61 | prog | `0.0` | `0.001` |
| 63 | operator | `>=` | `>` |
| 80 | operator | `<=` | `<` |
| 121 | operator | `<=` | `<` |

### `tools/track/timetable.py` — 7

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 106 | operator | `<=` | `<` |
| 106 | operator | `<=` | `<` |
| 219 | operator | `<` | `<=` |
| 299 | operator | `!=` | `==` |
| 300 | operator | `!=` | `==` |
| 327 | operator | `>` | `>=` |
| 327 | prog | `0` | `1` |

### `tools/blender/detail_markers.py` — 6

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 77 | operator | `>` | `>=` |
| 118 | operator | `==` | `!=` |
| 156 | operator | `<` | `<=` |
| 156 | prog | `0.0` | `0.001` |
| 159 | operator | `<` | `<=` |
| 159 | prog | `0.0` | `0.001` |

### `tools/blender/m7_layout.py` — 6

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 145 | operator | `<` | `<=` |
| 192 | operator | `>=` | `>` |
| 226 | operator | `<` | `<=` |
| 226 | operator | `>` | `>=` |
| 228 | operator | `>` | `>=` |
| 228 | operator | `<` | `<=` |

### `tools/track/network_chainage.py` — 6

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 131 | operator | `>` | `>=` |
| 131 | prog | `2000.0` | `2020.0` |
| 159 | operator | `<=` | `<` |
| 160 | operator | `<` | `<=` |
| 163 | operator | `<` | `<=` |
| 168 | operator | `<=` | `<` |

### `tools/track/shapefile.py` — 6

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 25 | operator | `<` | `<=` |
| 25 | prog | `100` | `101` |
| 36 | operator | `<=` | `<` |
| 63 | operator | `<` | `<=` |
| 63 | prog | `32` | `33` |
| 68 | operator | `<` | `<=` |

### `tools/physics/reference.py` — 5

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 34 | operator | `<=` | `<` |
| 45 | operator | `<` | `<=` |
| 45 | prog | `300` | `301` |
| 52 | operator | `<` | `<=` |
| 52 | prog | `120` | `121` |

### `tools/track/station_layout.py` — 5

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 77 | operator | `<=` | `<` |
| 77 | operator | `<=` | `<` |
| 116 | operator | `<` | `<=` |
| 117 | operator | `>` | `>=` |
| 128 | operator | `<=` | `<` |

### `tools/data/provenance.py` — 4

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 75 | operator | `==` | `!=` |
| 91 | operator | `<` | `<=` |
| 91 | prog | `8` | `9` |
| 164 | operator | `!=` | `==` |

### `tools/track/data_freshness.py` — 4

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 109 | operator | `<` | `<=` |
| 109 | prog | `0` | `1` |
| 110 | operator | `<=` | `<` |
| 112 | operator | `>` | `>=` |

### `tools/track/normalize_stops.py` — 3

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 250 | operator | `==` | `!=` |
| 264 | operator | `>` | `>=` |
| 264 | prog | `10` | `11` |

### `tools/track/make_test_track.py` — 2

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 19 | operator | `==` | `!=` |
| 19 | prog | `130` | `131` |

## Jak to powtórzyć

```bash
git checkout 737d592
python3 tools/tests/mutation_sweep.py --workers 6 \
    --journal /tmp/mutacje.jsonl --json /tmp/mutacje.json
```

Dziennik JSONL jest dopisywany po każdej mutacji, więc przerwany przebieg da się
wznowić tym samym poleceniem. Mutacje powstają z AST w ustalonej kolejności
(plik, wiersz, kolumna), więc dwa przebiegi na tym samym drzewie dają tę samą listę
i te same identyfikatory.

Podział na osiągalne i nieosiągalne policzysz tak: dla każdego modułu
`python3 -c "import <nazwa>"` z katalogiem modułu jako `cwd`. Niezerowy kod wyjścia
znaczy „nieosiągalny". PR #141 wbudowuje to w samo narzędzie.
