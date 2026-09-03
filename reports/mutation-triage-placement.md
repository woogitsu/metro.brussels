# Triaż ocalałych mutacji: `tools/blender/placement.py`

**Data:** 2026-09-03
**Poprzednie moduły:** `clearance.py` (#127), `clearance_profile.py` (#128),
`lod.py` (#130), `sweep.py` (#132)

`placement.py` osadza skład na osi trasy: ramki, kadry kontrolne, najgorszy promień,
offsety lokalne i przekroje pionowe. 20 ocalałych mutacji według raportu 5.1 — liczba
jest sprzed naprawy narzędzia i traktuję ją jako wskazówkę, nie pomiar (patrz #132).

**Metoda inna niż w poprzednich modułach.** Pełny przegląd repozytorium chodził w tle
i zajmował oba robotnicze drzewa, więc zamiast czekać, każdą mutację wstrzykiwałem
w źródło pojedynczo i uruchamiałem cały zestaw testów. To jest ta sama rygorystyczność
co przebieg zbiorczy — tylko ręcznie i na wybranych pozycjach.

## Usterka: martwy warunek, ten sam co w `clearance.py`

```python
if area2 < 1e-12 or ab * bc * ca == 0.0:
    return None
```

Druga połowa **nie mogła się nigdy wykonać**. Iloczyn boków zeruje się tylko wtedy, gdy
dwa z trzech punktów się pokrywają — a wtedy trójkąt ma zerowe pole i pierwszy warunek
już go odrzuca. Sprawdzone wykonaniem:

```
dwa punkty pokryte   area2=0  iloczyn=0.0  pierwszy=True  drugi=True
trzy współliniowe    area2=0  iloczyn=2.0  pierwszy=True  drugi=False
pierwszy=trzeci      area2=0  iloczyn=0.0  pierwszy=True  drugi=True
```

**Ta sama martwa połowa została usunięta z `clearance.circumradius` w #127.** Tutaj
przetrwała, bo nikt nie sprawdził drugiego wystąpienia. Usunięta.

**Martwy kod nie ma kontroli negatywnej i to nie jest niedopatrzenie tego triażu.**
Sprawdziłem: wstrzyknięcie *innego* martwego warunku (`or 1 == 2`) daje 698/698, czyli
zachowanie bez zmian — bo martwego kodu z definicji nie da się zaobserwować. Dlatego
znajduje go dopiero przegląd mutacyjny, jako mutację, która przeżywa.

## Pięć realnych dziur — każda zmierzona, nie wywnioskowana

| wiersz | mutacja | co się dzieje u mutanta | test |
|---|---|---|---|
| 30 | drugi `<=` → `<` | węzeł osi wpada do odcinka **następnego**: ta sama pozycja, ale `(index 1, t 0.0)` zamiast `(index 0, t 1.0)`, więc inna styczna i obrócona ramka | `..._node_belongs_to_the_segment_before_it` |
| 53 | `from_m < 0.0` → `<=` | kadr **całej osi od zera** kończy się wyjątkiem „okno wychodzi poza oś" — a to jest domyślne wywołanie renderu kontrolnego | `..._window_over_the_whole_axis_is_accepted` |
| 140 | `station < guard_m` → `<=` | stacja **dokładnie** na granicy strefy ochronnej wypada; zmierzone: odpowiedź przesuwa się z 134,862 m na 148,807 m przy tym samym promieniu | `..._station_exactly_at_the_guard_still_counts` |
| 169 | oba `<=` → `<` | **awaria cicha**: `local_offsets` startuje z `best = (0, 0, 0, inf)` i gdy żadna ramka nie przejdzie filtra, zwraca te ZERA. Punkt 2 m nad osią dostaje odpowiedź „leżysz na osi w kilometrażu zero" | `..._frame_exactly_at_the_window_edge_is_searched` |
| 263 | `<` → `<=` | przekrój o wysokości **równej** minimum uznany za zdegenerowany; render, który powinien się udać, przerywa się i wygląda to jak usterka geometrii, a nie progu | `..._section_exactly_at_the_minimum_is_not_degenerate` |

Wiersz 169 jest najgroźniejszy z całego zestawu, bo jego awaria **nie jest wyjątkiem
ani zerem w widocznym miejscu** — jest poprawnie wyglądającą trójką offsetów.

## Kontrole negatywne — sześć, wszystkie sprawdzone wykonaniem

```
30 węzeł do następnego odcinka     FAIL ..._node_belongs_to_the_segment_before_it   697/698
53 kadr od zera odrzucony          FAIL ..._window_over_the_whole_axis (2 testy)    696/698
140 stacja na granicy pomijana     FAIL ..._station_exactly_at_the_guard_still...   697/698
169 ramka na krańcu okna (a)       FAIL ..._frame_exactly_at_the_window_edge...     697/698
169 ramka na krańcu okna (b)       FAIL ..._frame_exactly_at_the_window_edge...     697/698
263 przekrój na minimum            FAIL ..._section_exactly_at_the_minimum...       697/698
```

Mutacja 53 wywraca **dwa** testy, w tym istniejący `..._axis_window_on_a_curve...` —
czyli kadr całej osi jest używany także gdzie indziej.

## Konwencja odwrotna niż w reszcie repozytorium

`frame_at` przypisuje węzeł do odcinka **poprzedniego** (`index = i, t = 1.0`).
Bloki sygnalizacji (`docs/15-classic-signalling.md`) i chunki streamowania używają
konwencji **półotwartej** `[start, end)`, w której granica należy do **następnego**.

Nie zmieniam tego — zmiana obróciłaby ramki w każdym węźle każdej osi i przeliczyła całą
geometrię. Zapisuję jako rozbieżność do rozstrzygnięcia razem z pozostałymi pytaniami
o konwencje (`docs/24-clearance-profile-decisions.md`, pozycja 8).

## Czego NIE uznałem za równoważne, choć nie umiałem odróżnić

Uczciwa różnica wobec poprzednich raportów. Dla dwóch pozycji **nie znalazłem wejścia,
które odróżnia mutanta** — ale to nie jest dowód równoważności, tylko brak dowodu:

| wiersz | mutacja | co próbowałem |
|---|---|---|
| 146 | `radius < best[1]` → `<=` | remis na minimalnym promieniu. Na łuku zdyskretyzowanym promienie różnią się na dalekich miejscach po przecinku, więc remisu nie udało się wywołać. Gdyby zaszedł, zmieniłby się **indeks**, nie wartość — a indeks jedzie do raportu jako kilometraż |
| 250 | `>` → `>=` | remis na wysokości przekroju przy poszerzaniu tolerancji. Opis funkcji mówi, że tolerancje 1 m i 2 m dają identyczne 5,50 m, więc remis jest realny — ale wtedy różni się tylko liczba wierzchołków w krotce, a nie zakres pionowy |

Reszta ocalałych to pasmo progów numerycznych (`1e-9`, `1e-12`) i strażniki geometrii
zdegenerowanej tej samej rodziny, co domknięte w `lod.py` i `sweep.py`.
