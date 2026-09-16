# 6.D248 — `.strip()` zjadał pierwszy znak pierwszej ścieżki, a bramka raportów wychodziła przez to zielona

**16.09.2026**, na `5c3dc83`. Wejście: `tools/tests/test_report_claims.py` (`_git`,
`zmienione_w_drzewie`, `data_stalej`, `data_raportu`). Wyjście: `_git_surowy`,
`sciezki_ze_statusu`, przepisane `zmienione_w_drzewie`, bramka
`test_status_porcelain_NIE_gubi_pierwszego_znaku_pierwszej_sciezki`, ten raport.

---

## 1. Usterka, zmierzona na jednym poleceniu

```
$ echo "" >> tools/tests/test_all.py
$ python3 -c "import test_report_claims as R; print(sorted(R.zmienione_w_drzewie()))"
['ools/tests/test_all.py']
```

Brakuje wiodącego `t`. Mechanizm ma dwa piętra i oba są potrzebne, żeby usterka
powstała:

- `_git` kończy się na `wynik.stdout.strip()`;
- `git status --porcelain -z` zaczyna wpis pliku **niezaindeksowanego** od SPACJI
  (` M plik`), a `zmienione_w_drzewie` tnie `kawalek[3:]`.

`.strip()` zjada tę spację w **pierwszym** wpisie, więc `[3:]` obcina o znak za dużo.
Zmierzony kształt wyjścia, na repozytorium próbnym:

```
 M beta.txt^@R  delta.txt^@alfa.txt^@?? z spacja.txt^@
```

## 2. Druga usterka tej samej pętli, znaleziona przy okazji

Wpis `R` (zmiana nazwy) niesie ścieżkę nową we własnym polu, a **źródło w polu
NASTĘPNYM — bez kolumn `XY`**. Pętla, która tego pola nie konsumuje, bierze
`alfa.txt` za wpis statusu i wkłada do zbioru jego `[3:]`, czyli **`a.txt`**: ciąg,
którego w drzewie nie ma. Prawdziwego źródła nie wkłada wcale.

## 3. Kto to czyta i co się psuje

`zmienione_w_drzewie()` ma **dwóch** czytelników, obu w tym module, obu w gałęzi
`TERAZ` mechanizmu datowania 6.D108:

| miejsce | co się psuje | kierunek |
|---|---|---|
| `data_stalej` | stała podniesiona w drzewie, jeszcze nie w commicie, nie dostaje `TERAZ` | **fałszywy alarm** — raport prawdziwy w swoim dniu zgłaszany jako nieaktualny |
| `data_raportu` | raport tknięty w drzewie nie dostaje `TERAZ` | **cisza** — nieprawdziwa liczba przechodzi bez słowa |

Drugi kierunek jest groźniejszy i to on decyduje, czy 6.D108 w ogóle działa
w trybie, w którym agent go używa.

**Dlaczego przeżyło tak długo.** Runner robi `git clean -ffdx` przy checkoucie, więc
drzewo w przebiegu CI jest czyste i `zmienione_w_drzewie()` zwraca tam zbiór pusty.
Bramka psuła się dokładnie w tym trybie, w którym się z niej korzysta, i nigdy
w tym, w którym jest oglądana.

## 4. Dlaczego OSOBNA funkcja, a nie `_git` bez `.strip()`

`.strip()` w `_git` jest **nośne** dla czterech pozostałych wywołań:
`rev-parse --git-dir` sklejałby się z `\n` w ścieżkę nieistniejącą, a
`_data(_git("log", "-1", "--format=%cI", ...))` dostawałby ISO z ogonkiem, na którym
`datetime.fromisoformat` rzuca `ValueError`. Zamiana globalna naprawiłaby jedno
wywołanie i zepsuła trzy.

Odrzucone też: `.rstrip("\0")` (leczy objaw, zostawia pułapkę dla następnego, kto
dopisze `.strip()` „dla porządku") oraz `--porcelain` bez `-z` (git **cytuje** wtedy
ścieżki z nietypowymi znakami, więc ścieżka ze spacją wracałaby w innej postaci niż
ta, z którą jest potem porównywana przez `in`).

## 5. KN-1 OBALIŁA PRZEWIDYWANIE i to jest najcenniejsza rzecz w tej pozycji

Pierwsza wersja bramki wołała `git status` **własnym podprocesem** i podawała wynik
funkcji `sciezki_ze_statusu`.

*Przewidywanie przed przebiegiem: przywrócenie `.strip()` w `_git_surowy` zapala
bramkę, 20/21.*

```
--- KN-1:   21/21 przeszło
```

**Zielono.** Bramka pisana na tę usterkę nie obejmowała jej ani trochę — bo usterka
siedzi w **ODCZYCIE**, a tamta droga odczyt omijała. Jest to ta sama rodzina co 6.D27,
tylko od strony, z której łatwiej ją przeoczyć: test nie zapalał się na poprawnym
kodzie, tylko **nie zapalał się na zepsutym**, i wyglądał przy tym dokładnie tak samo.

Poprawka: bramka podmienia `ROOT` na katalog próbny i woła **prawdziwe**
`zmienione_w_drzewie()`, tym samym idiomem, którym ten moduł podmienia `REPORTS`.

## 6. Pięć kontroli negatywnych — po poprawce bramki

| mutacja | wynik | co powiedział komunikat |
|---|---|---|
| KN-1 `.strip()` z powrotem | **20/21** | `['lfa.txt']` |
| KN-2 `wpis[3:]` → `wpis[2:]` | **20/21** | `[' alfa.txt']` |
| KN-3 bez konsumpcji pola źródłowego | **20/21** | `['delta.txt', 'ma.txt']` |
| KN-4 `split("\0")` → `split("\n")` | **20/21** | `['alfa.txt\x00']` |
| KN-5 parser zwraca pusty zbiór | **20/21** | `[]` |

Każda czerwień jest **rozróżnialna po komunikacie** — to nie jest pięć razy ta sama
asercja. Po każdej plik przywrócony z kopii, nie przez `git checkout --`:
`tools/tests/test_report_claims.py: OK`.

## 7. Kod POPRAWNY, na którym bramka mogłaby się zapalić (6.D27)

`git status` woła tu kod **produkcyjny**, do którego żadne `-c` podane przy
`init`/`add` nie dociera — obrona przez `-c` byłaby pozorna. Bramka przypina więc
konfigurację **lokalnie w repozytorium próbnym** (`status.showUntrackedFiles`,
`status.renames`, `core.quotePath`, `core.excludesFile`, `user.*`), bo lokalna bije
globalną i czyta ją każde wywołanie gita w tym katalogu.

Zmierzone, na kodzie poprawnym, z wrogim `~/.gitconfig`
(`showUntrackedFiles = no`, `renames = false`, `quotePath = true`):

```
  21/21 przeszło
```

Asercje stoją dodatkowo na **zbiorze ścieżek**, nie na literach statusu — dzięki temu
`status.renames=false`, który zamienia `R` na parę `D`+`A`, zmienia KSZTAŁT wyjścia,
a nie treść, i bramki nie zapala.

**Droga, której NIE zablokowałem, wypisana zamiast przemilczana:** `GIT_DIR` albo
`GIT_WORK_TREE` w środowisku przekierowałyby gita poza repozytorium próbne. Przebieg
z takim środowiskiem wywraca w tym zestawie znacznie więcej niż tę jedną bramkę, więc
objaw byłby czytelny.

## 8. Weryfikacja

```
  2505/2505 przeszło
  RAZEM 216.504 s, 2505 testów, 127 modułów
```

Zapadka `ASERCJI_NAPISOWYCH_RAZEM` stoi po tej pozycji na **903** (poprzednio o pięć
mniej), z powodem przy stałej: pięć asercji
kształtu `"plik.txt" in zbior`, wszystkie na ZACHOWANIU (zbiór jest wynikiem wywołania),
dwie z nich w drugą stronę — czy w zbiorze NIE MA śmiecia z pola źródłowego.

## 9. Zauważone, nietknięte

- **Ta sama rodzina jest o kilkadziesiąt wierszy wyżej:**
  `_git("show", f"HEAD:{wzgledna}").splitlines()` w `_wartosc_w_HEAD`. `.strip()`
  obcina tam wiodące białe znaki **pierwszego wiersza pliku**, więc stała zdefiniowana
  z wcięciem w pierwszym wierszu przestałaby być widziana w HEAD. Dziś taki plik się
  nie zdarza, ale mechanizm jest ten sam: `.strip()` na wyjściu, w którym brzeg coś
  znaczy.
- **Nie mierzyłem, ile twierdzeń w raportach przeszło przez tę dziurę w przeszłości.**
  Na czystym drzewie usterka się nie objawia, więc pytanie wymaga przejścia po historii
  i jest osobnym zadaniem.
- Dwa istniejące testy tego modułu (`test_stala_podniesiona_W_DRZEWIE…`,
  `test_raport_tkniety_w_drzewie…`) podstawiają `_PAMIEC["zmienione"]` i dlatego nie
  mogły tej usterki złapać. Ich docstringi mówią, że wejście syntetyczne jest
  „z konieczności" — konieczność była prawdziwa tylko do połowy.
