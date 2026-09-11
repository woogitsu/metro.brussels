# 6.D117 — trzeci kształt przejścia po drzewie: trzy miejsca, trzy własne reguły

**Zmierzone 11.09.2026 na:** `3fa2bec`, kontener tej sesji.
**Przyrząd:** `tools/tests/tree_walk.py` (`znajdz`), `tools/tests/test_tree_walks.py`
(`GLOB_WPROST`, skan po drzewie składni), trzy moduły wołające rekurencyjnego globa.

---

## 1. Liczba, której żąda wpis

Skan po drzewie składni całego `tools/` (nie grepem — `glob` pada też w prozie):

```
glob/iglob razem:                     28
z argumentem recursive:                3
Path.rglob:                            0

tools/tests/test_game_needle_specificity.py:184   recursive
tools/tests/test_sim_untested_members.py:59       recursive
tools/tests/test_xml_doc_blocks.py:53             recursive
```

Pozostałe 25 wywołań `glob` schodzi o **jeden poziom** i przejściem po drzewie nie
jest — dlatego rozpoznanie idzie po obecności argumentu `recursive`, a nie po nazwie
funkcji.

## 2. Rozstrzygnięcie dla każdego z trzech

Każde z trzech miało **własną** regułę odsiania — dokładnie ten kształt, który 6.D97
usunęło z przejść `os.walk`, tylko w trzecim kształcie przejścia:

| miejsce | własna reguła | rozstrzygnięcie |
|---|---|---|
| `test_game_needle_specificity.zrodla` | `.godot`, jedna pozycja | przepisane na `TW.znajdz` |
| `test_xml_doc_blocks._sources` | `obj/`, `bin/` | przepisane na `TW.znajdz` |
| `test_sim_untested_members._all_sim_cs_files` | brak (celowo) | **zostaje**, z powodem na jawnej liście |

`_all_sim_cs_files` ma z definicji widzieć `obj/` i `bin/`: jest pomiarem stanu PRZED
dla bramki, która pokazuje, ile plików odsiewa. Przepisanie zabrałoby jej punkt
odniesienia, a pole „Poza zakresem" wyklucza zmianę jej zachowania. `_sim_sources`,
czyli wejście właściwej bramki, idzie już przez `TW.znajdz`.

## 3. Wynik identyczny co do pliku

```
game.zrodla:        stare 22, nowe 22, identyczne: True
xml._sources:       stare 75, nowe 75, identyczne: True
sim._sim_sources:   stare 53, nowe 53, identyczne: True
```

Ta sama forma dowodu, co w 6.D97 (pięć liczników przed i po). **Ale cisza ma tu
warunek i ten warunek jest stanem katalogu:** `src/Game/obj/` i `src/Game/bin/` dziś
nie istnieją, więc reguła z jedną pozycją (`.godot`) dawała ten sam wynik co pełne
odsianie. Pod `src/Sim` taki plik **jest** — wygenerowany `Sim.AssemblyInfo.cs` w katalogu
budowania, 54 pliki wobec 53 — i tam różnica jest widoczna.

Dlatego bramka jest na **WOŁANIU**, a nie na wyniku: cisza, której warunkiem jest to,
co akurat leży na dysku, nie jest bramką. Ten sam powód stoi przy bramce `os.walk`
z 6.D74.

## 4. Co przybite

`tree_walk.znajdz(top, wzorzec)` — rekurencyjne szukanie plików z tym samym odsianiem,
co `walk`. Wynik posortowany i absolutny, żeby podmiana w miejscu wołania nie zmieniała
niczego poza odsianiem.

`GLOB_WPROST` — zamknięta lista miejsc, którym wolno wołać rekurencyjnego globa wprost,
z powodem dłuższym niż 40 znaków, zapadką i kontrolą gnicia (wpis bez wołania jest
zdaniem o repozytorium, które przestało być prawdziwe). Wzorzec wprost z listy `WOLNO_WPROST`
dla `os.walk`.

**Dwie stałe zniknęły razem z własną regułą:** `GAME_SOURCE_GLOB` (wzorzec `**/*.cs`)
i `GAME_SOURCE_SKIP` (`.godot`). Obie przestały być czytane, a martwa stała jest
zdaniem o repozytorium, które ktoś przeczyta i uzna za prawdziwe — złapała je bramka
`test_every_unread_constant_is_justified` w tym samym przebiegu.

## 5. Kontrole negatywne

`__pycache__` czyszczony przed każdym przebiegiem, po każdej `md5sum -c` na trzech
plikach.

| # | co zepsute | wynik |
|---|---|---|
| KN-1 | wraca rekurencyjny glob bez wpisu na liście | 12/13, z plikiem i wierszem |
| KN-2 | skan globów oślepiony | 11/13, dwa testy |
| KN-3 | `znajdz` przestaje odsiewać (goły `os.walk`) | **13/13 i 10/10 zielone na dwóch modułach; 2 FAIL-e na całym zestawie** |
| KN-4 | zapadka `MAX_GLOB_WPROST` podniesiona z 1 na 9 | **13/13 ZIELONA** |

**KN-3 jest najciekawsza i jej wynik zależy od tego, co się uruchomi.** Na modułach,
które ta pozycja zmienia, mutacja jest niewidoczna — bo pod `src/Game` nie ma dziś
gałęzi do odsiania. Widzi ją dopiero `test_sim_untested_members.py`, gdzie
`src/Sim/obj/` **jest**: `test_generated_files_are_excluded_from_the_count`
i `test_no_real_sim_member_is_missing_from_tests`. Czerwień na poziomie, który się
liczy — całego zestawu — więc odsianie jest przybite; ale gdyby ktoś kiedyś usunął tę
jedną bramkę, `znajdz` zostałoby bez kontroli.

**KN-4 wyszła zielona i to jest zachowanie ZASTANE, nie moje.** Zapadka jest
porównaniem `len(GLOB_WPROST) <= MAX_GLOB_WPROST`, więc samo podniesienie stałej nie
dodaje wpisu i nie zapala niczego — dokładnie tak samo zachowuje się sąsiednia
`MAX_WOLNO_WPROST`, dopisana w 6.D74. Nie robię tu wyjątku dla własnej listy: reguła „wolno tylko
obniżać" jest w tym repozytorium zdaniem dla człowieka, a nie bramką, i to jest
**wspólna cecha wszystkich zapadek tego pliku** — zmiana jej dla jednej byłaby
rozjazdem dwóch reguł pod jedną nazwą.

## 6. Weryfikacja

```
$ python3 tools/tests/test_all.py test_tree_walks.py
  13/13 przeszło          (było 10)

$ python3 tools/tests/test_all.py
  2257/2257 przeszło, 120 modułów
```

## 7. Czego nie zrobiłem

- **Nie zmieniłem zachowania `_all_sim_cs_files`** i nie przepisałem na `os.walk`
  niczego, co ma powód zostać — pole „Poza zakresem" wyklucza oba wprost.
- **Nie tknąłem 25 nierekurencyjnych wywołań `glob`**: schodzą o jeden poziom, więc
  gałęzi pominiętych nie mijają.
- **Nie dodałem `Path.rglob` do skanu jako kształtu, który wystąpił** — w drzewie nie
  ma ani jednego. Skan go nie zna i to jest ta sama reguła, co przy 6.D110: kształt
  niewystępujący jest hipotezą.

## 8. Zauważone przy okazji

- **Dwa testy `test_sim_untested_members.py` mają asercje z PUSTYM komunikatem.**
  W KN-3 zgłosiły się jako `FAIL test_generated_files_are_excluded_from_the_count:`
  — dwukropek i nic dalej. Są sprzed tej pozycji, więc ich nie ruszam (§4.10), ale
  czerwień bez zdania każe czytać kod zamiast komunikatu.
- **Wygenerowany `Sim.AssemblyInfo.cs` w katalogu budowania pod `src/Sim` istnieje
  po każdym lokalnym budowaniu** i jest jedynym plikiem, na którym dzisiejsze odsianie robi różnicę
  w tym drzewie. W CI `git clean -ffdx` sprząta go przed przebiegiem, więc tam
  różnicy nie widać wcale — pomiar „przed i po" zrobiony wyłącznie w CI pokazałby
  same zera i nie powiedziałby nic.
