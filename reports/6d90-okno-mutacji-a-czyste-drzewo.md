# Okno mutacji a czyste drzewo: teza pozycji obalona, zjawisko znalezione gdzie indziej (10.09.2026)

**Zmierzone 10.09.2026 na:** `c724001`, kontener tej sesji.
**Przyrząd:** sonda `git status --porcelain` odpytywana co 50 ms przez cały przebieg
zestawu, `tools/tests/mutation_sweep.py` (`targets`, `check_one`, `collect`),
nowy `tools/tests/test_tree_writes.py`, `python3 tools/tests/test_all.py`.

---

## 1. Czego pozycja szukała, a co pomiar zastał

Wpis 6.D90 brzmiał: **narzędzie mutacyjne brudzi `data/` W MIEJSCU**, więc równoległa
kontrola czystości widzi naruszenie reguły 6, którego nikt nie popełnił. Obserwacja
z 09.09.2026 była prawdziwa (`M data/track/L1_A.json` w `git status`), ale przypisanie
jej narzędziu mutacyjnemu **nie wytrzymało pomiaru**.

Dwie niezależne przyczyny, każda wystarczająca:

- **`targets()` nie zagląda do `data/`.** Chodzi po `tools/` i bierze wyłącznie `.py`
  (`mutation_sweep.py:318`). Żaden plik danych nie ma jak zostać wybrany do mutacji.
- **`check_one` nie pisze do drzewa wołającego.** Otwiera
  `os.path.join(worktree, mutation.path)`, a `worktree` to kopia z
  `git worktree add --detach HEAD` stojąca w `tempfile.TemporaryDirectory(prefix=
  "metro-mutacje-")` — czyli poza repozytorium.

Pomiar bezpośredni, przebieg `--only tools/track/crs.py --limit 3` (kalibracja wyroczni
plus trzy mutacje, 3/3 zabite, 512 s), z sondą co 50 ms przez cały czas:

```
=== brud w data/ w trakcie przebiegu:
0 próbek
```

Ten sam wynik dla pełnego przebiegu zestawu (2158 testów): **zero** próbek z czymkolwiek
z `data/`. Pole „Skończone, gdy" pozycji — „pełny przebieg narzędzia nie pokazuje ani
jednego pliku z `data/` jako zmodyfikowanego w żadnym momencie, sprawdzone pomiarem
w trakcie, a nie po" — jest więc spełnione **dziś, bez żadnej zmiany**, i to jest
pierwszy wynik tej pozycji.

## 2. Zjawisko jednak istnieje, tylko na innym pliku

Ta sama sonda, rozszerzona z `data/` na całe drzewo, złapała w trakcie przebiegu
zestawu co innego:

```
=== próbek z brudem: 14
     11  M tools/blender/lod_paths.py
      2 ?? tools/tests/test_dwa_lvplhgrt/
      1 ?? tools/tests/test_pusty_fmn6qkuv/
```

**11 próbek po 50 ms to około pół sekundy**, przez które plik ŚLEDZONY jest w drzewie
zmieniony. Sprawcą są trzy kontrole z `tools/tests/test_mutation_sweep.py` — 6.B32
i dwie z 6.B38 — które dopisują tekst do `tools/blender/lod_paths.py` i przywracają go
w `finally`. Przywrócenie działa, więc po przebiegu nie widać nic; w oknie widać
naruszenie reguły 6, którego nikt nie popełnił. To jest **dokładnie mechanizm z pola
„Skąd" pozycji 6.D90**, tylko o innym pliku i o innym sprawcy.

Dwa katalogi `??` to piaskownice, które MUSZĄ stać w `tools/tests/`, bo mierzą
zachowanie `test_all._discover()`. Nie są śledzone i nie są tu naprawiane.

## 3. Sonda nie wystarczy, i to też jest pomiar

Skan drzewa składni po wszystkich modułach testowych znalazł **siedem** miejsc zapisu
w **trzech** modułach. Sonda przez cały przebieg pokazała **jeden plik**. Różnica nie
jest sprzecznością: pozostałe okna są krótsze niż 50 ms.

Przyrząd oparty na próbkowaniu meldowałby więc czystość, której nie sprawdził — ta sama
rodzina usterki, którą projekt tropi od 6.D27. Dlatego bramka jest **statyczna**,
a sonda została użyta raz, do znalezienia zjawiska, i jest opisana tutaj, a nie wpisana
do zestawu.

## 4. Co zostało zrobione

- Cztery kontrole w `test_mutation_sweep.py` (5 miejsc zapisu) przeniesione na **kopię**:
  `_cele_na_boku()` kopiuje cel do katalogu tymczasowego i przestawia `sweep.ROOT`.
  Wariant `z_gitem=True` zakłada tam repozytorium syntetyczne, bo kontrola 6.B32
  o brudnym drzewie pyta `git diff --name-only HEAD` i bez `.git` nie odpowiedziałaby
  na własne pytanie. Pole „Wyjście" pozycji dawało znacznik jako wariant awaryjny,
  „jeśli kopia jest niewykonalna" — jest wykonalna, więc znacznika nie ma.
- Trzy bramki w `test_mutation_sweep.py`: cele nie wychodzą poza `tools/**.py`, okno
  mutacji nie rusza drzewa głównego **w trakcie** (obserwator siedzi w atrapie
  `run_suite`, czyli jest wołany dokładnie wtedy, gdy mutacja stoi zastosowana),
  oraz kontrola PRZYRZĄDU: ten sam obserwator skierowany na repozytorium syntetyczne,
  które naprawdę się brudzi, brud widzi.
- Nowy moduł `tools/tests/test_tree_writes.py`: żaden test nie pisze do pliku
  zbudowanego ze ścieżki repozytorium, poza jawną listą DŁUGU. Zapadka
  `MAX_ZAPISOW_W_DRZEWIE` stoi na **5** i wolno jej wyłącznie maleć.

Po przeniesieniu, ta sama sonda na pełnym przebiegu:

```
=== próbek z brudem: 3
      2 ?? tools/tests/test_pusty_cb4_9sx7/
      1 ?? tools/tests/test_dwa_825y0hi1/
```

`M tools/blender/lod_paths.py` znika: **11 próbek → 0**.

## 5. Dwie kontrole negatywne wyszły ZIELONE i obie nazwały słabość moich bramek

**KN-1 (zielona).** Mutacja „`targets()` chodzi także po `data/`" nie zapaliła nic:
funkcja filtruje po `.py`, a w `data/` plików `.py` nie ma. Asercja o `data/` była więc
w tej postaci **niefalsyfikowalna**. Powtórzona jako **KN-1b** — `targets()` chodzi po
`data/` ORAZ bierze `.json` — zaświeciła 112/114. Asercja zostaje, bo mówi to, o co pyta
pozycja, ale wiadomo teraz, że prawdziwą jej treścią jest filtr rozszerzenia.

**KN-3 (zielona).** Przywrócenie jednej z kontroli 6.B38 do zapisu w drzewie głównym
przeszło bramkę bez mrugnięcia. Powód: zapis siedzi w pomocniku `_z_dopiskiem(cel, ...)`,
gdzie `cel` jest **parametrem**, a nazwa `ROOT` pada dopiero u wołającego. Skan patrzył
wyłącznie na wyrażenie w samym `open`, więc omijał dokładnie tę postać, dla której
powstał. Skan dostał drugi kształt — pomocnik piszący swój parametr, wynik przypisany
do WOŁANIA — i **KN-3b** na tej samej mutacji daje 2/4.

## 6. Osiem kontroli negatywnych, `md5sum -c: OK` po każdej

Cache bajtkodu czyszczony przed każdym przebiegiem (powód z 6.D86).

| kontrola | mutacja | wynik |
|---|---|---|
| KN-1 | `targets()` chodzi także po `data/` | **zielona** — filtr `.py` przesądza sam |
| KN-1b | `targets()` chodzi po `data/` i bierze `.json` | **czerwona** 112/114, dwie bramki |
| KN-2 | `check_one` nie przywraca pliku (zdjęte `finally`) | **czerwona** 112/114, dwie bramki |
| KN-3 | jedna kontrola 6.B38 wraca do zapisu w drzewie | **zielona** — skan nie widział pomocnika |
| KN-3b | ta sama mutacja, skan po rozszerzeniu | **czerwona** 2/4 |
| KN-4 | zapadka podniesiona z pięciu na sześć | **czerwona** 3/4 |
| KN-5 | wpis DŁUGU mówi 2 miejsca zamiast 3 | **czerwona** 2/4, dwie bramki |
| KN-6 | wzorzec `ROOT` nie łapie niczego | **czerwona** 1/4, w tym kontrola przyrządu |

```
KN-1b FAIL test_zaden_cel_mutacji_nie_lezy_poza_kodem_narzedzi:
      /workspace/metro.brussels/data/audio/audio-manifest.schema.json
KN-2  FAIL test_okno_mutacji_nie_rusza_drzewa_glownego_W_TRAKCIE_a_nie_po: x = 2
      FAIL test_obserwator_okna_widzi_brud_tam_gdzie_brud_jest:
      po zamknięciu okna plik nie wrócił do stanu z HEAD
KN-3b FAIL test_zadna_kontrola_nie_pisze_do_pliku_sledzonego_poza_lista_dlugu:
      {'test_mutation_sweep.py': [(2514, 'test_pamiec_uniewaznia_sie_takze_...',
      '_z_dopiskiem(cel, ...)')]}
KN-4  FAIL test_zapadka_stoi_na_zmierzonej_liczbie: miejsc zapisu jest 5,
      a zapadka stoi na 6 — obniż ją do 5
KN-5  FAIL test_lista_dlugu_nie_gnije: test_dotnet_version.py: miejsc jest 3,
      a lista mówi 2
KN-6  FAIL test_skan_widzi_ksztalt_ktory_ma_widziec: []
      FAIL test_zapadka_stoi_na_zmierzonej_liczbie: miejsc zapisu jest 0
```

**KN-6 jest osobno od KN-4, choć obie ruszają tę samą bramkę**, bo mierzą przeciwne
tryby cichej awarii: KN-4 pyta, czy zapadki nie da się podnieść razem z nowym zapisem,
a KN-6 — czy wyzerowany wynik skanu na pewno nie przechodzi jako „czysto".

## 7. Bramka po drodze nie kończyła się w 110 s

Pierwsza wersja skanu czytała wyrażenia przez `ast.get_source_segment`, który przy
KAŻDYM wywołaniu dzieli źródło na wiersze. Wywołań jest jedno na przypisanie w całym
katalogu testów, więc moduł nie skończył się w 110 s i został ubity. `ast.unparse` daje
napis znormalizowany, w którym `ROOT` stoi tak samo, i moduł chodzi **4,07 s**.

## 8. Weryfikacja

```
python3 tools/tests/test_all.py test_tree_writes.py
  -> 4/4 przeszło, 4,067 s

python3 tools/tests/test_all.py test_mutation_sweep.py
  -> 114/114 przeszło

python3 tools/tests/test_all.py
  -> RAZEM 104,550 s, 2162 testów, 115 modułów, kod 0
  -> 2162/2162 przeszło
```

Zestaw **2155 → 2162**, moduły **114 → 115**. `MIN_REPORTS` stoi na **209**,
podniesiona ze dwustu ośmiu — zapis słowny, bo bramka `test_report_claims.py`
bierze pierwszą liczbę po nazwie stałej za twierdzenie o jej wartości.

## 9. Czego świadomie nie zrobiłem

**Pięciu miejsc zapisu w `test_dotnet_version.py` i `test_provenance_classes.py` nie
naprawiłem.** Mają ten sam kształt co naprawione i weszły do drzewa w tej samej sesji
(6.D79 i 6.D89 — obie moje), ale żaden z tych plików nie należy do pozycji 6.D90,
a `CLAUDE.md` §4.10 mówi „jedno zadanie = jedna gałąź". Stoją na liście DŁUGU z powodem
i z zapadką, która pozwala jej wyłącznie maleć, i są zapisane niżej jako zauważone.

Nie ruszyłem zbioru mutacji ani sposobu liczenia wyników (pole „Poza zakresem").
Nie dopisałem znacznika okna mutacji — pole „Wyjście" daje go tylko wtedy, gdy kopia
jest niewykonalna, a jest wykonalna. Nie tknąłem dwóch piaskownic `??` w `tools/tests/`:
one MUSZĄ tam stać, bo mierzą `test_all._discover()`, i nie są śledzone.

Nie ustaliłem, **co** zmieniło `data/track/L1_A.json` 09.09.2026. Wiadomo, czego to nie
było; sprawcy nie wskazuję, bo materiału już nie ma, a zgadywanie w tym miejscu byłoby
dokładnie tym, co ta pozycja prostuje.

## 10. Zauważone i nietknięte

- `tools/tests/test_dotnet_version.py`: trzy zapisy do `global.json` w drzewie głównym.
- `tools/tests/test_provenance_classes.py`: dwa zapisy do `docs/02-simulation.md`.
- Bramka nie łapie zapisu przez `shutil`, `os.replace`, `pathlib.Path.write_text`
  ani przez podproces — dziś w drzewie nie ma ani jednego takiego, ale to jest zdanie
  o dzisiejszym drzewie, nie o kształcie bramki.
