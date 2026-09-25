# 6.D344 — cztery sita adresów plików

**Data:** 25.09.2026 · **Baza:** `e04675d317c58b23ab68a05b209c5d1ee7d423c9`
Zakres: wzorce używane do odsiania albo wybrania **odsyłacza do pliku w prozie**
w czterech modułach wskazanych w pozycji. Nie liczę czytników ścieżek z wyniku
Git, polecenia `python3`, nazw modułów ani katalogów: mają inne wejście niż proza
z odsyłaczem. Skan składni `re.compile` w całym `tools/tests/` wskazał te
kandydatury; każdą sprawdziłem w miejscu wywołania.

## Trzy liczby

| miara | wynik |
|---|---:|
| wzorce odsiewające lub wybierające odsyłacz pliku z prozy | **4** |
| pożyczone przez kolejny pomiar nazw z istniejącego sita | **1** |
| napisane lokalnie dla swojego pomiaru | **3** |

| wzorzec | moduł | skąd i co faktycznie bierze |
|---|---|---|
| `ADRES_NIE_TWIERDZENIE` | `test_report_claims.py` | Pożyczony przez pomiar liczbowych twierdzeń z istniejącego sita; bierze także daty, numery zadań i PR, więc jest szerszy od adresów plików. |
| `ODSYLACZ_PLIKU` | `test_prose_counts.py` | Lokalny filtr końca nazwy z rozszerzeniem; ukośnik nie jest wymagany. |
| `PATH_TOKEN` | `test_field_paths.py` | Lokalny czytnik odsyłaczy w polach zadań; wymaga ukośnika i znanego rozszerzenia, nie wymaga grawisów. |
| `PATH_TOKEN` | `test_report_hygiene.py` | Lokalny czytnik raportów; wymaga grawisów i znanego rozszerzenia. |

`BARE_TOKEN` w `test_field_paths.py` nie jest piątym sitem prozy: buduje
**kontrolny kontrprzykład** gołej nazwy, której tamtejszy `PATH_TOKEN` celowo
nie widzi. `DIR_TOKEN` czyta katalogi, a `PY_TOOL_CALL` czyta polecenia. Wzorce
z `test_commit_claims.py` czytają ścieżki z diffu Git. Dwa lokalne wzorce
`zly`/`domkniety` w `test_field_paths.py` są próbkami negatywnymi granicy
jednego `PATH_TOKEN`, nie produkcyjnymi sitami.

## Porównanie na wspólnym wejściu

Każdy z czterech rzeczywistych obiektów `re.Pattern` uruchomiłem przez
`search()` na **tych samych** dziesięciu napisach. `1` oznacza trafienie.

| próbka | adres/twierdzenie | końcówka nazwy | pole zadania | raport |
|---|---:|---:|---:|---:|
| `plik.md` | 1 | 1 | 0 | 0 |
| `docs/TASKS.md` | 1 | 1 | 1 | 0 |
| `` `docs/TASKS.md` `` | 1 | 0 | 1 | 1 |
| `docs/TASKS.md:12` | 1 | 0 | 1 | 0 |
| `` `docs/TASKS.md:12` `` | 1 | 0 | 1 | 0 |
| `.github/workflows/python-tests.yml` | 1 | 0 | 1 | 0 |
| `reports/scene.glb` | 1 | 1 | 1 | 0 |
| docs/plan.csv (próbka syntetyczna) | 1 | 1 | 1 | 0 |
| `6.D168` | 1 | 0 | 0 | 0 |
| `README` | 0 | 0 | 0 | 0 |

| para | ten sam wynik na 10 próbkach? | wspólnych trafień | kontrprzykład |
|---|---|---:|---|
| adres/twierdzenie ↔ końcówka nazwy | nie | 4 | numer zadania |
| adres/twierdzenie ↔ pole zadania | nie | 7 | goła nazwa |
| adres/twierdzenie ↔ raport | nie | 1 | goła nazwa |
| końcówka nazwy ↔ pole zadania | nie | 3 | goła nazwa |
| końcówka nazwy ↔ raport | nie | 0 | goła nazwa i odsyłacz w grawisach |
| pole zadania ↔ raport | nie | 1 | odsyłacz bez grawisów |

**Wynik par: 0 z 6 daje identyczny wektor, 6 z 6 ma różny zasięg na tej
próbce.** Jedna para ma tu zerowy zbiór wspólnych trafień; pięć pozostałych
**nakłada się częściowo**, więc „różne” nie znaczy „matematycznie rozłączne”.
To pomiar na wejściu wzorcowym, nie dowód równoważności regexów dla dowolnego
napisu. Przede wszystkim goła nazwa z rozszerzeniem trafia w `ODSYLACZ_PLIKU`,
a nie trafia w `test_field_paths.PATH_TOKEN`, dokładnie jak wymaga kontrola
przyrządu. Nie scalam wzorców: ich różny zasięg chroni różne bramki.
