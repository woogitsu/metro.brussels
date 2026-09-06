# Manifest proweniencji pisany tylko przy zmianie treści (6.D23)

**Zmierzone 06.09.2026 na commicie:** `7eda277a870ca34a26ed28a62f88189cf0fdb754`

## 1. Decyzja i jej zakres

Właściciel wybrał 06.09.2026 wariant **C** z `reports/zapisy-do-data.md` §3, spośród
czterech wypisanych tam z kosztem każdego. **`CLAUDE.md` §4.6 zostaje nietknięty**:
zmieniają się narzędzia, nie reguła, a `data/` pozostaje tylko do odczytu bez wyjątku.

Kryterium jest **wąskie i celowo takie**: nadpisanie zależy wyłącznie od
`content_sha256`, a nie od całego `diff_manifests`. Pytanie, czy zmiana **innych** pól
manifestu przy niezmienionej treści też ma nadpisywać plik, wariant C dopiero otwiera —
i należy do właściciela. Osobny test przybija ten zakres.

## 2. Jedna implementacja, nie dwie

`provenance.write_manifest_if_changed()` — obaj fetchowie ją wołają. Dwie kopie tej
samej reguły rozjechałyby się przy pierwszej zmianie; test pilnuje, że żaden fetcher
nie wrócił do bezwarunkowego `handle.write(P.canonical_json(manifest))`.

Komunikat konsolowy **nie jest ozdobą**: wariant C zabiera sygnał, który dawał
`git diff`. Bez niego przebieg bez zmian jest nieodróżnialny od przebiegu, którego
nie było.

## 3. Dwa przebiegi z rzędu na niezmienionym źródle

```
=== przebieg 1
[RAPORT] sha256=c8cf67efeaaea3340632c0202c308b07c1b65a66ee44c400beedaeb476529dbc
[RAPORT] manifest utworzony
kod: 0

=== przebieg 2, to samo źródło
[RAPORT] sha256=c8cf67efeaaea3340632c0202c308b07c1b65a66ee44c400beedaeb476529dbc
[RAPORT] manifest bez zmian: content_sha256 ten sam, plik nietkniety
kod: 0

suma manifestu po 1:  0dc1c58f1d0212ba48654dbece23dae43cd193823938eda603f6a6515f4fd6ca
suma manifestu po 2:  0dc1c58f1d0212ba48654dbece23dae43cd193823938eda603f6a6515f4fd6ca
mtime:                1788732477 vs 1788732477
```

**Równy `mtime` jest tu ważniejszy od równej sumy.** Zapis identycznych bajtów też
zmienia czas modyfikacji i też wygląda w narzędziach jak praca, której nie było.

Kontrola w drugą stronę — do archiwum dopisany `shapes.txt`, czyli zmieniona treść:

```
[RAPORT] manifest zmieniony
suma manifestu:  717eb76a264cfa0ba740602234129ea7a4cddb5cf898926c7d34794a29ebf348
```

`git status --short data/` — **puste** przed i po całym przebiegu.

## 4. Czego ten pomiar NIE pokazał, i dlaczego

Przebiegi wyżej użyły **syntetycznego** archiwum GTFS i manifestu w katalogu
tymczasowym, nie prawdziwego `data/network/gtfs-manifest.json`. Powód jest prosty
i nie jest wyborem: archiwum źródłowe leży poza repozytorium (`data/gtfs/` jest
gitignorowane, patrz `reports/zapisy-do-data.md`), a pobranie go z sieci jest poza
zakresem tej pozycji. Mechanizm jest ten sam — ta sama funkcja, ta sama gałąź kodu —
ale **na prawdziwym pliku z `data/` nie został tu wykonany** i mówię to wprost,
zamiast pozwolić, żeby wypis wyglądał na coś, czym nie jest.

## 5. Kontrole negatywne — wykonane

```
KN-1  powrót do zapisu bezwarunkowego
      FAIL test_the_same_content_leaves_the_file_untouched: zmieniony
      FAIL test_a_changed_side_field_alone_does_not_rewrite: zmieniony

KN-2  kryterium rozszerzone z content_sha256 na cały diff (status zamiast source_changed)
      FAIL test_a_changed_side_field_alone_does_not_rewrite: zmieniony
```

KN-2 jest tu istotniejsza: pilnuje **granicy, którą właściciel zostawił sobie**.
Rozszerzenie kryterium wygląda jak drobne ulepszenie i przeszłoby niezauważone.

## 6. Weryfikacja

```
python3 tools/tests/test_all.py  ->  1780/1780 przeszło, kod wyjścia 0
git status --short data/         ->  puste
```

Testy `--offline` z #315 (6.D14) pozostają zielone.

## 7. Poza zakresem

Wariant D (przeniesienie `retrieved_at` poza plik śledzony) — nie został wybrany.
Rozstrzygnięcie, czy zmiana innych pól manifestu ma nadpisywać plik — to pytanie
wariant C dopiero otwiera. Zmiana `build_alignment.py` i `normalize_stops.py`:
wariant **E** mówi, że dziedziczą stabilność po manifeście bez zmiany własnego kodu,
i tak zostaje.
