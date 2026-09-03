# Przegląd mutacyjny bramek

**Snapshot na commicie:** `8a4c55d`

Narzędzie: `tools/tests/mutation_sweep.py`. Mutowany jest **kod pod testem**,
nie testy. Mutacja, która przeżyła, znaczy jedno z dwojga: brak pokrycia albo
mutant równoważny — zmiana, której nie da się zaobserwować. Narzędzie nie zgaduje,
które to; każdą trzeba obejrzeć.

## Wynik

| | |
|---|---|
| mutacji | 961 |
| rozstrzygniętych | 961 |
| zabitych | 536 |
| **ocalałych** | **425** |
| **nierozstrzygniętych** | **0** |
| pokrycie (z rozstrzygniętych) | 55.8 % |

**Nierozstrzygnięta** znaczy, że przebieg testów nie doszedł do końca — ubity,
bez pamięci, błąd poza samą mutacją. Taki wynik NIE liczy się jako zabicie.
Pierwsza wersja tego narzędzia liczyła go właśnie tak i przez to zawyżała
pokrycie: kontrola wykazała, że 16 z 20 „zabić” z przebiegu pod presją pamięci
to w rzeczywistości mutacje ocalałe.

## Jak czytać ocalałe

Ocalała mutacja **nie jest** automatycznie usterką. Trzeba ją zakwalifikować
do jednej z trzech klas, a narzędzie tego nie zrobi za czytającego:

| klasa | co znaczy | co z tym zrobić |
|---|---|---|
| **realna dziura** | zmiana zmienia zachowanie, które ktoś kiedyś zobaczy, a żaden test tego nie sprawdza | dopisać test z kontrolą negatywną |
| **mutant równoważny** | zmiany nie da się zaobserwować (np. tolerancja `1e-12` przesunięta o procent) | zapisać jako równoważną, nie „naprawiać” |
| **remis bez znaczenia** | `<` kontra `<=` przy wyborze minimum: przy remisie obie gałęzie dają tę samą wartość | jak wyżej, chyba że liczy się INDEKS |

Rozróżnienie wymaga przeczytania kodu. Wpisanie mutanta równoważnego jako
usterki zawyża znalezisko dokładnie tak samo, jak liczenie zepsutego przebiegu
jako zabicia zawyżało pokrycie.

**Kolejność triażu:** od pliku o najwyższym UDZIALE ocalałych, nie od pliku
o największej ich liczbie. Wysoki udział znaczy, że testy tego modułu sprawdzają
co innego, niż deklarują; duża liczba przy niskim udziale znaczy tylko, że moduł
jest duży.

## Ocalałe, per plik

### `tools/blender/clearance.py` — 12

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 47 | prog | `0.0` | `0.001` |
| 47 | operator | `<=` | `<` |
| 50 | operator | `>=` | `>` |
| 66 | prog | `1e-12` | `1.01e-12` |
| 66 | operator | `<` | `<=` |
| 66 | prog | `0.0` | `0.001` |
| 92 | operator | `<` | `<=` |
| 92 | operator | `>` | `>=` |
| 95 | operator | `<=` | `<` |
| 95 | operator | `<=` | `<` |
| 97 | prog | `0.0` | `0.001` |
| 97 | operator | `<=` | `<` |

### `tools/blender/clearance_profile.py` — 72

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 91 | prog | `2` | `3` |
| 91 | operator | `<=` | `<` |
| 99 | operator | `>=` | `>` |
| 99 | prog | `0.0` | `0.001` |
| 99 | operator | `<=` | `<` |
| 104 | operator | `<=` | `<` |
| 104 | prog | `0.0` | `0.001` |
| 119 | prog | `0.0` | `0.001` |
| 169 | prog | `3` | `4` |
| 169 | operator | `<` | `<=` |
| 174 | operator | `>` | `>=` |
| 174 | prog | `0.0` | `0.001` |
| 181 | operator | `<` | `<=` |
| 185 | operator | `<=` | `<` |
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
| 324 | prog | `0.0` | `0.001` |
| 324 | operator | `<` | `<=` |
| 326 | operator | `<` | `<=` |
| 337 | operator | `<` | `<=` |
| 366 | operator | `<` | `<=` |
| 382 | prog | `0.0` | `0.001` |
| 382 | operator | `<=` | `<` |
| 385 | operator | `<=` | `<` |
| 385 | prog | `0.0` | `0.001` |
| 389 | prog | `1e-9` | `1.01e-09` |
| 389 | operator | `>` | `>=` |
| 400 | prog | `1e-6` | `1.0099999999999999e-06` |
| 400 | operator | `>` | `>=` |
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
| 580 | prog | `1e-9` | `1.01e-09` |
| 580 | operator | `<` | `<=` |
| 605 | prog | `3` | `4` |
| 605 | operator | `<` | `<=` |
| 640 | operator | `<` | `<=` |
| 640 | operator | `>` | `>=` |
| 643 | operator | `<=` | `<` |
| 643 | operator | `<=` | `<` |
| 653 | operator | `>` | `>=` |
| 679 | operator | `<` | `<=` |
| 679 | prog | `1e-12` | `1.01e-12` |
| 682 | prog | `3` | `4` |
| 682 | operator | `<` | `<=` |
| 692 | prog | `2` | `3` |
| 692 | operator | `<` | `<=` |
| 697 | operator | `!=` | `==` |
| 733 | operator | `<` | `<=` |
| 755 | operator | `<` | `<=` |

### `tools/blender/detail_markers.py` — 6

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 77 | operator | `>` | `>=` |
| 118 | operator | `==` | `!=` |
| 156 | prog | `0.0` | `0.001` |
| 156 | operator | `<` | `<=` |
| 159 | operator | `<` | `<=` |
| 159 | prog | `0.0` | `0.001` |

### `tools/blender/glb_roundtrip.py` — 9

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 41 | operator | `==` | `!=` |
| 77 | operator | `==` | `!=` |
| 77 | prog | `0` | `1` |
| 77 | operator | `==` | `!=` |
| 77 | prog | `0` | `1` |
| 89 | operator | `>` | `>=` |
| 93 | operator | `>` | `>=` |
| 93 | operator | `<` | `<=` |
| 95 | operator | `<` | `<=` |

### `tools/blender/lod.py` — 69

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 91 | operator | `<=` | `<` |
| 91 | prog | `0.0` | `0.001` |
| 110 | prog | `0.0` | `0.001` |
| 110 | operator | `<=` | `<` |
| 113 | operator | `>` | `>=` |
| 113 | prog | `1.0` | `1.01` |
| 113 | operator | `<` | `<=` |
| 125 | operator | `<=` | `<` |
| 127 | operator | `<=` | `<` |
| 127 | prog | `0.0` | `0.001` |
| 127 | prog | `0.0` | `0.001` |
| 134 | operator | `<=` | `<` |
| 135 | operator | `>` | `>=` |
| 135 | prog | `0.0` | `0.001` |
| 137 | operator | `>` | `>=` |
| 137 | operator | `>` | `>=` |
| 137 | prog | `0.0` | `0.001` |
| 143 | operator | `!=` | `==` |
| 165 | operator | `>` | `>=` |
| 167 | operator | `<` | `<=` |
| 183 | prog | `0.0` | `0.001` |
| 183 | operator | `<=` | `<` |
| 186 | operator | `>` | `>=` |
| 186 | prog | `1.0` | `1.01` |
| 186 | operator | `<` | `<=` |
| 196 | prog | `0.0` | `0.001` |
| 196 | operator | `<=` | `<` |
| 199 | operator | `<` | `<=` |
| 201 | operator | `>` | `>=` |
| 201 | prog | `0.0` | `0.001` |
| 206 | prog | `0.0` | `0.001` |
| 206 | operator | `<=` | `<` |
| 216 | operator | `<` | `<=` |
| 265 | operator | `<` | `<=` |
| 265 | prog | `2` | `3` |
| 301 | operator | `>=` | `>` |
| 313 | operator | `!=` | `==` |
| 351 | operator | `<` | `<=` |
| 351 | operator | `<` | `<=` |
| 355 | operator | `==` | `!=` |
| 359 | prog | `0.0` | `0.001` |
| 359 | operator | `<=` | `<` |
| 388 | operator | `<` | `<=` |
| 395 | operator | `<=` | `<` |
| 395 | prog | `0.0` | `0.001` |
| 471 | operator | `<=` | `<` |
| 471 | operator | `<=` | `<` |
| 473 | operator | `<` | `<=` |
| 487 | operator | `>` | `>=` |
| 487 | prog | `0` | `1` |
| 519 | operator | `<=` | `<` |
| 528 | operator | `==` | `!=` |
| 547 | operator | `!=` | `==` |
| 552 | operator | `<=` | `<` |
| 554 | prog | `0` | `1` |
| 554 | operator | `<=` | `<` |
| 569 | operator | `==` | `!=` |
| 570 | operator | `!=` | `==` |
| 576 | operator | `>` | `>=` |
| 579 | operator | `<` | `<=` |
| 583 | prog | `0` | `1` |
| 583 | prog | `0` | `1` |
| 583 | operator | `<=` | `<` |
| 594 | operator | `>=` | `>` |
| 598 | prog | `0.0` | `0.001` |
| 601 | operator | `<=` | `<` |
| 603 | prog | `0.0` | `0.001` |
| 603 | operator | `<=` | `<` |
| 606 | operator | `>` | `>=` |

### `tools/blender/m7_layout.py` — 2

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 192 | operator | `>=` | `>` |
| 228 | operator | `<` | `<=` |

### `tools/blender/m7_shell.py` — 22

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 82 | operator | `<=` | `<` |
| 88 | operator | `<=` | `<` |
| 88 | operator | `<=` | `<` |
| 244 | operator | `>` | `>=` |
| 246 | operator | `>` | `>=` |
| 254 | operator | `<=` | `<` |
| 255 | operator | `<=` | `<` |
| 289 | operator | `>` | `>=` |
| 291 | operator | `>` | `>=` |
| 293 | operator | `>` | `>=` |
| 295 | operator | `>` | `>=` |
| 301 | operator | `<` | `<=` |
| 301 | prog | `1000` | `1001` |
| 305 | operator | `>` | `>=` |
| 305 | prog | `0.0` | `0.001` |
| 310 | operator | `==` | `!=` |
| 320 | operator | `!=` | `==` |
| 322 | operator | `!=` | `==` |
| 328 | operator | `>` | `>=` |
| 371 | operator | `==` | `!=` |
| 384 | operator | `<=` | `<` |
| 422 | operator | `<` | `<=` |

### `tools/blender/place_vehicle.py` — 5

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 61 | operator | `==` | `!=` |
| 81 | operator | `<` | `<=` |
| 81 | operator | `<=` | `<` |
| 124 | operator | `<` | `<=` |
| 182 | operator | `<` | `<=` |

### `tools/blender/placement.py` — 20

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 30 | operator | `<=` | `<` |
| 32 | prog | `0.0` | `0.001` |
| 53 | operator | `>` | `>=` |
| 57 | operator | `<` | `<=` |
| 96 | operator | `<` | `<=` |
| 100 | prog | `1e-9` | `1.01e-09` |
| 100 | operator | `<` | `<=` |
| 140 | operator | `>` | `>=` |
| 146 | operator | `<` | `<=` |
| 156 | prog | `1e-12` | `1.01e-12` |
| 169 | operator | `<=` | `<` |
| 169 | operator | `<=` | `<` |
| 194 | prog | `0.0` | `0.001` |
| 197 | operator | `>` | `>=` |
| 204 | operator | `<` | `<=` |
| 221 | operator | `<` | `<=` |
| 225 | operator | `<=` | `<` |
| 228 | operator | `<=` | `<` |
| 250 | operator | `>` | `>=` |
| 263 | operator | `<` | `<=` |

### `tools/blender/profile_vehicle.py` — 17

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 90 | operator | `==` | `!=` |
| 172 | operator | `>` | `>=` |
| 202 | operator | `<` | `<=` |
| 202 | operator | `<=` | `<` |
| 237 | operator | `<=` | `<` |
| 273 | prog | `0` | `1` |
| 285 | operator | `==` | `!=` |
| 369 | operator | `>=` | `>` |
| 373 | prog | `1e-9` | `1.01e-09` |
| 373 | operator | `==` | `!=` |
| 373 | operator | `<` | `<=` |
| 391 | operator | `<=` | `<` |
| 431 | operator | `==` | `!=` |
| 515 | operator | `==` | `!=` |
| 519 | operator | `>` | `>=` |
| 522 | operator | `>` | `>=` |
| 531 | operator | `<` | `<=` |

### `tools/blender/profiles.py` — 8

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 32 | operator | `>` | `>=` |
| 33 | operator | `<=` | `<` |
| 33 | prog | `2` | `3` |
| 48 | operator | `<=` | `<` |
| 48 | operator | `<=` | `<` |
| 54 | operator | `<=` | `<` |
| 56 | operator | `<=` | `<` |
| 70 | operator | `>` | `>=` |

### `tools/blender/render_check.py` — 4

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 61 | prog | `1e-9` | `1.01e-09` |
| 61 | operator | `<` | `<=` |
| 82 | prog | `2` | `3` |
| 91 | operator | `>` | `>=` |

### `tools/blender/station_kit.py` — 5

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 96 | operator | `>` | `>=` |
| 112 | operator | `<` | `<=` |
| 121 | operator | `<` | `<=` |
| 189 | prog | `0` | `1` |
| 189 | operator | `>` | `>=` |

### `tools/blender/sweep.py` — 39

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 54 | prog | `0.0` | `0.001` |
| 54 | operator | `<=` | `<` |
| 92 | prog | `0.0` | `0.001` |
| 92 | prog | `3` | `4` |
| 126 | operator | `<=` | `<` |
| 130 | prog | `0.0` | `0.001` |
| 130 | operator | `<` | `<=` |
| 143 | operator | `>` | `>=` |
| 157 | prog | `2` | `3` |
| 157 | operator | `<` | `<=` |
| 161 | prog | `1e-9` | `1.01e-09` |
| 174 | operator | `<` | `<=` |
| 204 | operator | `<` | `<=` |
| 204 | prog | `0.0` | `0.001` |
| 219 | operator | `<=` | `<` |
| 224 | operator | `>` | `>=` |
| 234 | operator | `>=` | `>` |
| 237 | operator | `<` | `<=` |
| 237 | operator | `>=` | `>` |
| 247 | operator | `>=` | `>` |
| 298 | operator | `<` | `<=` |
| 345 | operator | `>` | `>=` |
| 380 | prog | `0.0` | `0.001` |
| 380 | operator | `>` | `>=` |
| 410 | prog | `1e-9` | `1.01e-09` |
| 410 | operator | `>` | `>=` |
| 487 | prog | `1` | `2` |
| 487 | operator | `>` | `>=` |
| 528 | operator | `<` | `<=` |
| 571 | prog | `0.0` | `0.001` |
| 571 | operator | `>=` | `>` |
| 678 | operator | `>` | `>=` |
| 683 | operator | `<=` | `<` |
| 685 | operator | `>` | `>=` |
| 687 | prog | `0` | `1` |
| 687 | operator | `<=` | `<` |
| 690 | prog | `0.0` | `0.001` |
| 695 | operator | `>` | `>=` |
| 700 | operator | `>` | `>=` |

### `tools/blender/tunnel_sweep.py` — 21

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 119 | operator | `==` | `!=` |
| 138 | prog | `0` | `1` |
| 138 | operator | `==` | `!=` |
| 276 | prog | `0` | `1` |
| 289 | prog | `0` | `1` |
| 325 | operator | `==` | `!=` |
| 356 | prog | `0` | `1` |
| 356 | operator | `==` | `!=` |
| 410 | prog | `2` | `3` |
| 417 | operator | `==` | `!=` |
| 419 | operator | `!=` | `==` |
| 419 | operator | `==` | `!=` |
| 438 | operator | `==` | `!=` |
| 594 | operator | `>` | `>=` |
| 603 | prog | `0.0` | `0.001` |
| 603 | operator | `<` | `<=` |
| 605 | prog | `0.0` | `0.001` |
| 607 | prog | `0` | `1` |
| 607 | operator | `==` | `!=` |
| 619 | operator | `>` | `>=` |
| 621 | operator | `>` | `>=` |

### `tools/ci/assert_shot_metadata.py` — 10

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 126 | prog | `0.0` | `0.001` |
| 132 | operator | `>` | `>=` |
| 143 | prog | `0.0` | `0.001` |
| 166 | prog | `0` | `1` |
| 176 | prog | `1e-3` | `0.00101` |
| 178 | operator | `<=` | `<` |
| 189 | operator | `>` | `>=` |
| 195 | operator | `>` | `>=` |
| 204 | operator | `>` | `>=` |
| 219 | operator | `>` | `>=` |

### `tools/data/provenance.py` — 3

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 91 | prog | `8` | `9` |
| 91 | operator | `<` | `<=` |
| 164 | operator | `!=` | `==` |

### `tools/physics/braking.py` — 5

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 163 | operator | `>=` | `>` |
| 163 | operator | `<=` | `<` |
| 200 | operator | `<` | `<=` |
| 231 | operator | `>=` | `>` |
| 287 | operator | `>` | `>=` |

### `tools/physics/reference.py` — 4

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 34 | operator | `<=` | `<` |
| 45 | prog | `300` | `301` |
| 45 | operator | `<` | `<=` |
| 52 | operator | `<` | `<=` |

### `tools/physics/schedule_envelope.py` — 5

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 55 | operator | `<=` | `<` |
| 90 | operator | `>` | `>=` |
| 109 | operator | `>` | `>=` |
| 114 | operator | `<=` | `<` |
| 116 | operator | `>` | `>=` |

### `tools/track/build_alignment.py` — 35

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 85 | prog | `0.0` | `0.001` |
| 85 | operator | `<=` | `<` |
| 88 | operator | `>` | `>=` |
| 91 | operator | `<` | `<=` |
| 110 | operator | `<` | `<=` |
| 113 | operator | `<=` | `<` |
| 113 | operator | `<` | `<=` |
| 115 | operator | `<=` | `<` |
| 117 | operator | `<=` | `<` |
| 121 | operator | `>` | `>=` |
| 125 | prog | `1e-6` | `1.0099999999999999e-06` |
| 125 | operator | `<` | `<=` |
| 138 | prog | `0` | `1` |
| 140 | operator | `>=` | `>` |
| 143 | operator | `<=` | `<` |
| 145 | operator | `<=` | `<` |
| 183 | operator | `>` | `>=` |
| 221 | prog | `1e-9` | `1.01e-09` |
| 221 | operator | `<` | `<=` |
| 247 | operator | `==` | `!=` |
| 347 | operator | `>=` | `>` |
| 377 | operator | `==` | `!=` |
| 398 | operator | `==` | `!=` |
| 404 | operator | `==` | `!=` |
| 431 | operator | `!=` | `==` |
| 440 | operator | `!=` | `==` |
| 477 | operator | `==` | `!=` |
| 478 | operator | `!=` | `==` |
| 542 | operator | `==` | `!=` |
| 586 | operator | `==` | `!=` |
| 600 | operator | `<=` | `<` |
| 642 | prog | `0` | `1` |
| 646 | operator | `==` | `!=` |
| 778 | operator | `!=` | `==` |
| 784 | operator | `>` | `>=` |

### `tools/track/crosscheck_alignment.py` — 11

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 69 | operator | `>` | `>=` |
| 69 | operator | `>` | `>=` |
| 71 | operator | `<` | `<=` |
| 80 | operator | `==` | `!=` |
| 153 | operator | `==` | `!=` |
| 233 | operator | `<=` | `<` |
| 246 | operator | `==` | `!=` |
| 289 | prog | `0` | `1` |
| 293 | operator | `>` | `>=` |
| 317 | operator | `!=` | `==` |
| 321 | operator | `==` | `!=` |

### `tools/track/crs.py` — 5

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 145 | operator | `<` | `<=` |
| 145 | operator | `<` | `<=` |
| 234 | operator | `<` | `<=` |
| 244 | prog | `1e-12` | `1.01e-12` |
| 244 | operator | `<` | `<=` |

### `tools/track/data_freshness.py` — 2

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 109 | prog | `0` | `1` |
| 110 | operator | `<=` | `<` |

### `tools/track/detail_layout.py` — 4

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 53 | operator | `<=` | `<` |
| 61 | prog | `0.0` | `0.001` |
| 63 | operator | `>=` | `>` |
| 121 | operator | `<=` | `<` |

### `tools/track/fetch_osm_routes.py` — 4

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 81 | operator | `==` | `!=` |
| 81 | operator | `==` | `!=` |
| 104 | operator | `!=` | `==` |
| 108 | operator | `<` | `<=` |

### `tools/track/inspire_rail.py` — 12

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 117 | operator | `==` | `!=` |
| 242 | operator | `==` | `!=` |
| 279 | operator | `<=` | `<` |
| 302 | operator | `<=` | `<` |
| 306 | prog | `1.0` | `1.01` |
| 309 | operator | `<` | `<=` |
| 352 | operator | `>=` | `>` |
| 375 | operator | `<` | `<=` |
| 403 | prog | `0.0` | `0.001` |
| 404 | operator | `>` | `>=` |
| 569 | operator | `!=` | `==` |
| 569 | prog | `1` | `2` |

### `tools/track/make_test_track.py` — 1

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 19 | prog | `130` | `131` |

### `tools/track/network_chainage.py` — 1

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 160 | operator | `<` | `<=` |

### `tools/track/normalize_stops.py` — 1

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 264 | prog | `10` | `11` |

### `tools/track/station_layout.py` — 1

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 117 | operator | `>` | `>=` |

### `tools/track/surface_sections.py` — 5

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 119 | operator | `<=` | `<` |
| 158 | operator | `<=` | `<` |
| 219 | operator | `!=` | `==` |
| 299 | operator | `==` | `!=` |
| 404 | operator | `==` | `!=` |

### `tools/track/timetable.py` — 1

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 106 | operator | `<=` | `<` |

### `tools/track/tunnel_width.py` — 1

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 61 | prog | `1e-12` | `1.01e-12` |

### `tools/track/validate.py` — 3

| wiersz | rodzaj | było | jest |
|---|---|---|---|
| 26 | operator | `<` | `<=` |
| 69 | operator | `>` | `>=` |
| 107 | operator | `>` | `>=` |
