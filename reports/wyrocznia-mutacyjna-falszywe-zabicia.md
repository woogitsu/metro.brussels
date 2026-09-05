# Przegląd mutacyjny meldował 100 % zabić, bo zestaw padał także bez mutacji

**Zmierzone 05.09.2026 na commicie:** `8c3f752`

Od 05.09.2026, godz. 09:07, narzędzie `tools/tests/mutation_sweep.py` zapisywało **każdą**
mutacji jako zabitą, niezależnie od tego, czy jakikolwiek test ją widzi. Wynik takiego
przebiegu to `31/31 zabitych, 0 ocalałych` — czyli liczba, która wygląda jak sukces
i dlatego nie budzi podejrzeń.

Ten raport zapisuje mechanizm, dowód wykonania, zasięg skażenia i to, co teraz tego
pilnuje.

## 1. Mechanizm — trzy rzeczy, z których każda z osobna była poprawna

1. `add_worktree()` przygotowywał drzewo robocze i **kasował** z niego
   `tools/tests/test_mutation_sweep.py`. Powód był dobry: testy narzędzia mierzą
   narzędzie, nie kod pod testem, a przy tym dominują czas przebiegu.
2. Commit `809e6f1` („Raporty w `reports/` nie niosą już liczb, które przestały być
   prawdziwe", 05.09.2026 09:07) dodał bramkę
   `test_kazda_sciezka_wymieniona_w_raporcie_rozwiazuje_sie_w_drzewie`: każda ścieżka
   wymieniona w raporcie ma się rozwiązywać w drzewie.
3. `reports/mutation-drift.md` (wiersze 22, 396, 406) i `reports/mutation-sweep.md`
   (wiersz 100) wymieniają z nazwy właśnie `tools/tests/test_mutation_sweep.py`.

Złożenie: od `809e6f1` zestaw pada w **każdym** drzewie roboczym, **bez żadnej mutacji**.
Wyrocznia narzędzia brzmi „zestaw padł, czyli mutacja została wykryta" — i to zdanie
przestało być prawdziwe, bo jego założenie („zestaw nie pada bez mutacji") przestało
zachodzić.

Żaden z trzech kroków nie był błędem. Błędem był brak pomiaru ich złożenia.

## 2. Dowód — dwa wykonania, nie rozumowanie

**Pierwsze: zestaw pada w czystym drzewie.** Kopia `HEAD` bez ani jednej mutacji,
z samą kasacją pliku, którą robiło przygotowanie drzewa:

```
FAIL test_kazda_sciezka_wymieniona_w_raporcie_rozwiazuje_sie_w_drzewie:
     ścieżki, których nie ma w drzewie: ['mutation-drift.md:22: `tools/tests/test_mutation_sweep.py`',
     'mutation-drift.md:396: …', 'mutation-drift.md:406: …', 'mutation-sweep.md:100: …']
  1539/1540 przeszło
```

**Drugie: mutacja zaliczona jako zabita w rzeczywistości przeżywa.** Wiersz 46
`tools/blender/m7_report.py`, wstawiony ręcznie w czystej kopii `HEAD`:

```
BYLO:             if start - 1e-9 <= nose_end <= end + 1e-9:
JEST:             if start - 1e-9 < nose_end <= end + 1e-9:
  1598/1598 przeszło
```

Zestaw jest zielony, czyli mutacja **przeżyła**. Przegląd z 05.09.2026 20:10 zapisał ją
jako zabitą, wskazując jako zabójcę dokładnie tę bramkę ścieżek — jedyny test, który
padał, i padał niezależnie od mutacji.

## 3. Zasięg skażenia — co trzeba przeliczyć, a czego nie

Skażony jest **każdy przebieg po `809e6f1`**, czyli po 05.09.2026 09:07. Wcześniejsze
pomiary są nietknięte, bo bramki jeszcze nie było.

| przebieg | co meldował | stan |
|---|---|---|
| `m7_report.py`, klasy `operator,prog` | 31 / 31 zabitych, 0 ocalałych | **fałszywy**, mierzony ponownie |
| `make_test_track.py`, klasy `operator,prog` | 2 / 2 zabite | **potwierdzony** naprawionym narzędziem, patrz niżej |
| `reports/mutation-sweep.md`, `reports/mutation-drift.md` | — | sprzed bramki, nietknięte |

Przemiar `make_test_track.py` naprawionym narzędziem:

```
[MUTACJE] 2 mutacji do policzenia, 1 robotników, commit 8c3f752, klasy operator,prog
[MUTACJE] kalibracja wyroczni: zestaw w drzewie BEZ mutacji
[MUTACJE] drzewo bazowe zielone, wyrocznia ma prawo mówić „zabita”
[MUTACJE] rozstrzygniętych 2/2, zabitych 2, ocalałych 0 (w tym 0 nieuruchomionych)
```

Wniosek raportu `reports/mutation-triage-make-test-track.md` — że obie mutacje zabijają
testy z `f5126a3` — **stoi**. Nieprawdziwa była w nim wyłącznie liczba „5 testów padło"
przy pierwszej mutacji: piątym była ta bramka, która padała zawsze. Datowanego pomiaru
się nie przelicza, więc tamten raport zostaje, a sprostowanie jest tutaj.

## 4. Naprawa — dwie warstwy, bo przyczyna i klasa to co innego

**Warstwa pierwsza, przyczyna.** `neutralise_own_tests()` zastępuje treść pliku
zaślepką z samym docstringiem, zamiast plik kasować. Testy narzędzia znikają tak samo
skutecznie — a ścieżka, którą cytują raporty, zostaje.

**Warstwa druga, klasa.** `baseline_problem()`: przed pomiarem przegląd puszcza zestaw
w drzewie **bez mutacji** i przerywa, jeśli nie jest zielone. To obrona niezależna od
przyczyny — złapałaby zarówno to, jak i awarię z 02.09.2026, gdy zestaw ubijał OOM
i 16 z 20 „zabić" okazało się ocalałymi. Kosztuje jeden przebieg zestawu na cały
przegląd: 3 % przy 31 mutacjach, poniżej dwóch promili przy sześciuset.

Sama warstwa pierwsza byłaby naprawą jednego zdarzenia. Sama druga zostawiałaby
narzędzie niezdatne do użytku, ale głośne. Dopiero obie razem znaczą „mierzy i wie,
kiedy nie mierzy".

## 5. Bramki

W `tools/tests/test_mutation_sweep.py`:

- `test_przygotowanie_drzewa_zdejmuje_testy_narzedzia_nie_kasujac_pliku` — po
  przygotowaniu plik **istnieje**, nie ma w nim ani jednego `def test_`, a żaden inny
  plik nie jest ruszony;
- `test_ten_plik_jest_wymieniony_w_raportach_wiec_nie_wolno_go_kasowac` — mierzy na
  drzewie, że zaślepka wciąż ma powód. Gdy przestanie, test to powie, zamiast pozwolić
  ostrożności trwać jako obrzędowi po nieaktualnym zdarzeniu;
- `test_przeglad_odmawia_pomiaru_gdy_czyste_drzewo_nie_jest_zielone` — trzy przypadki
  `baseline_problem`, w tym drzewo **zielone**, które musi dać `None`. Bez tego
  przypadku funkcja zwracająca zawsze komunikat przechodziłaby trzy czwarte testu
  i zatrzymywała każdy przegląd świata.

### Kontrola negatywna — WYKONANA

Przywrócona stara kasacja pliku, przegląd puszczony normalnie:

```
[MUTACJE] 2 mutacji do policzenia, 1 robotników, commit 8c3f752, klasy operator,prog
[MUTACJE] kalibracja wyroczni: zestaw w drzewie BEZ mutacji
[MUTACJE] PRZERWANE — zestaw PADA w czystym drzewie, bez żadnej mutacji (kod 1):
['test_kazda_sciezka_wymieniona_w_raporcie_rozwiazuje_sie_w_drzewie:'] — dopóki tak jest,
każda mutacja zostanie zapisana jako zabita, a przegląd nie mierzy niczego
```

Bez naprawy warstwy drugiej ten sam przebieg wypisałby `rozstrzygniętych 2/2, zabitych 2`
i nie powiedziałby nic.

## 6. Czego ten raport świadomie nie robi

- **Nie przelicza raportów sprzed `809e6f1`.** Nie są skażone i datowanego pomiaru się
  nie przelicza.
- **Nie zmienia bramki ścieżek z `809e6f1`.** Bramka jest poprawna i to ona ujawniła
  problem, choć nie tam, gdzie celowała. Osłabienie jej byłoby naprawą objawu.
- **Nie rozstrzyga o pozycji 6.B7.** Prawdziwa liczba ocalałych mutacji
  `tools/blender/m7_report.py` wymaga przebiegu na naprawionym narzędziu i jest
  przedmiotem tamtej pozycji, nie tej naprawy.

## 7. Weryfikacja — rzeczywiste wyjście

```
$ python3 tools/tests/test_all.py
  1601/1601 przeszło
```

Trzy testy więcej niż na `8c3f752` (1598) — dokładnie te trzy bramki z sekcji 5.
