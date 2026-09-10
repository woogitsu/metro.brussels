# Uzupełnienie kolejki na progu dwunastu pozycji (10.09.2026)

**Zmierzone 10.09.2026 na:** `e73680b`, kontener tej sesji.
**Przyrząd:** `tools/tests/test_backlog.py` (`open_items`, `detail_sections`,
`missing_fields`), `bash doctor.sh --no-tests`, `python3 tools/tests/test_all.py`.

---

## 1. Dlaczego teraz

Po scaleniu #471 kolejka faz 5 i 6 miała **dokładnie dwanaście** pozycji otwartych,
czyli tyle, ile wynosi `MINIMUM_READY_ITEMS`. `CLAUDE.md` §8: „Gdy kolejka zejdzie
poniżej dwunastu pozycji, **pierwszym zadaniem jest jej uzupełnienie**, nie
zatrzymanie się." Wzięcie następnej pozycji zbiłoby licznik do jedenastu i zapaliło
`test_backlog`, więc uzupełnienie było jedyną robotą, którą wolno było zacząć.

**Efektywnie było ich jedenaście, nie dwanaście.** W liczonych dwunastu stoi **6.D53**,
której pole „Zależy od" brzmi dosłownie „decyzji właściciela o zapisie do
`data/network/sources.json`". Ta rozbieżność jest treścią jednej z nowych pozycji
(6.D95) i została zauważona właśnie przy tym liczeniu.

## 2. Skąd wzięło się sześć nowych pozycji

**Żadna nie została wymyślona na miejscu.** Wszystkie sześć wyrosły z pomiarów
zrobionych w tej sesji przy innych zadaniach i zapisanych wtedy jako „zauważone
i nietknięte" — czyli z materiału, który już istniał w raportach i w wierszach
`docs/TASKS.md`, a nie z przeglądania kodu w poszukiwaniu czegokolwiek.

| pozycja | skąd, i przy czym zmierzona |
|---|---|
| 6.D95 | wypis `doctor.sh:411` wobec pola „Zależy od" pozycji 6.D53 — zauważone przy 6.D73 i potwierdzone dziś |
| 6.D96 | 6.D79 §3: pin 10.0.402 przy zainstalowanym 10.0.401 → `dotnet --version` kod **155** |
| 6.D97 | 6.D74: cztery lokalne filtry zostały po wspólnym odsianiu, trzy są uboższą kopią `.gitignore` |
| 6.D98 | 6.D81: dziesięć wywołań `chk_*`, **sześć** uruchamia program, **cztery** to wyrażenie powłoki |
| 6.D99 | 6.D83: katalog objął `Hud.Update`, ale cztery inne miejsca składają wiersze tego samego panelu |
| 6.D100 | 6.D33: kolektor liczy heredok bloku 6.A24 jako **pięć** komend zamiast jednej |

**Ani jedna nie wymaga decyzji właściciela**, i to jest sprawdzone polem „Zależy od"
każdej z nich, a nie deklaracją: 6.D95 i 6.D100 nie zależą od niczego, pozostałe
cztery od pozycji już scalonych (6.D74, 6.D79, 6.D81, 6.D83).

## 3. Wypis doctora pokazuje usterkę 6.D95 na żywo

```
  Baza projektu jest gotowa. Rozpiska nie ma odblokowanego zadania z numerem,
  więc zgodnie z CLAUDE.md §8 bierzesz pierwszą pozycję z kolejki faz 5 i 6:
    6.D53 · `sources.json` opisuje dostęp do OSM dwoma słowami `osm_or_overpass` …
  Kolejka faz 5 i 6 ma 18 pozycji do wzięcia, żadna nie wymaga decyzji właściciela.
```

Doctor w jednym oddechu wskazuje 6.D53 jako pozycję do wzięcia i ogłasza, że żadna
nie wymaga decyzji — a 6.D53 wymaga dokładnie jej. **Ten wypis nie jest hipotezą
zapisaną w nowej pozycji, tylko jej dowodem**, i dlatego stoi tutaj dosłownie.

## 4. Co sprawdziłem przed wpisaniem, żeby nie wpisać nieprawdy

Każde zdanie „Skąd" zostało odtworzone na dzisiejszym drzewie, a nie przepisane
z pamięci:

```
doctor.sh:411                        napis stały — potwierdzone grepem
6.D53 „Zależy od"                    „decyzji właściciela o zapisie do data/network/sources.json"
BUILD_DIRS w test_readme_claims.py   {"bin", "obj"} — bez `build`, `renders`, `.venv`
trzy lokalne filtry katalogów        test_dead_constants.py:56, ..._csharp.py:76, mutation_sweep.py:322
Sim.Runner tworzy katalog wyjściowy  TAK (Program.cs:1690) — dlatego NIE wpisałem tego do kolejki
```

**Ostatni wiersz jest tu istotny.** Kandydatem na siódmą pozycję była notatka z 6.D33
mówiąca, że `Sim.Runner` nie tworzy katalogu wyjściowego i trzynaście komend pada po
przebiegu. Sprawdzenie pokazało `Directory.CreateDirectory` w `Program.cs:1690`, więc
albo notatka opisywała stan sprzed poprawki, albo dotyczyła innej ścieżki — i pozycji
o tym **nie ma**, bo nie umiem dziś powiedzieć, która z tych dwóch rzeczy jest prawdą.
Wpisanie jej „na wszelki wypadek" dałoby polu „Skąd" zdanie, którego nikt nie zmierzył.

## 5. Zapadki

`MINIMUM_DETAIL_BLOCKS` stoi dziś na **179**: w tym commicie została podniesiona
ze stu sześćdziesięciu siedmiu na sto siedemdziesiąt trzy, bo bloków przybyło sześć,
a drugie tego samego dnia uzupełnienie kolejki dołożyło następnych sześć. `MINIMUM_READY_ITEMS`
**bez zmiany** (12): jest progiem, poniżej którego nie wolno zejść, a nie licznikiem
stanu — podniesienie go do osiemnastu zamieniłoby próg w wymaganie i kazałoby
uzupełniać kolejkę po każdym scaleniu.

Dwa raporty cytujące starą wartość (`pusta-wersja-blendera.md`,
`sonda-jednej-biblioteki.md`) mają przepisany **wyłącznie akapit o stanie bieżącym**;
liczby w ich blokach pomiarowych zostają przy swoich datach.

## 6. Weryfikacja

```
python3 tools/tests/test_all.py
  -> RAZEM 97,575 s, 2143 testów, 113 modułów, kod 0

pozycji otwartych:  12 -> 18
bloków szczegółów: 167 -> 173
komplet sześciu pól w każdym z sześciu nowych bloków: potwierdzony
  (test_backlog.missing_fields dla 6.D95 … 6.D100 zwraca pustą listę)
```
