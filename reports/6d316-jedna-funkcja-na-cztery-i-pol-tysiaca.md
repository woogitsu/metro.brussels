# 6.D316 · Jedna funkcja na cztery i pół tysiąca nie ma żadnej drogi wywołania — a pole i mój własny zapis pominęły dwie najważniejsze

**Data:** 20.09.2026 · **Gałąź:** `claude/sharp-ramanujan-jdr51o` · **Baza:** `5a80c08`

6.D306 przeszło sondą 138 modułów i znalazło cztery czytniki zadeklarowane, a nigdy
niewołane: dwa `main` (punkty wejścia, mają prawo) oraz `dwie_miary_czytnikow`
i `swiadkowie_klasy`. Ta pozycja pyta, czy woła je **cokolwiek w całym drzewie**,
od kiedy, i ile innych funkcji ma tę samą własność.

---

## 1. Dwie odpowiedzi imienne

### `dwie_miary_czytnikow` — NIE WOŁA GO NIC, i to jest odpowiedź pełna

Nic w `tools/`, nic w `*.sh`, nic w workflowach, żaden import ani atrybut.
Mój pierwszy przebieg zgłosił dla niej drogę `__main__` — **i to był fałszywy
alarm mojego czytnika**: `if __name__ == "__main__"` stoi w `test_prose_counts.py`
w wierszu **670**, a funkcja jest zdefiniowana w wierszu **1319**, czyli
**za** blokiem wejściowym. Znalazłem to czytaniem numerów wierszy, nie zaufaniem
własnemu wypisowi.

### `swiadkowie_klasy` — WOŁANE, ale tylko wtedy, gdy bramka ma paść

Jest wołane raz, w swoim własnym module, w wierszu 1334:

```python
swiadkowie = {n: swiadkowie_klasy(n) for n, _b, _j in inna_klasa}
assert inna_klasa == [], (
    "zapadka zmieniła klasę (nazwa, było, jest): %s. …
```

**Wywołanie stoi w wyrażeniu iterującym po `inna_klasa`, a następny wiersz
stwierdza, że `inna_klasa` jest pusta.** Dopóki bramka jest zielona, iteracja nie
ma po czym chodzić i funkcja nie wykonuje się **ani razu**. Uruchomi się wyłącznie
w przebiegu, w którym bramka i tak zapali się dwie linijki dalej.

**To rozstrzyga różnicę z 6.D306 i nie jest sprzecznością.** Tamta sonda mierzyła
czas **wykonania** czytników w trakcie przebiegu — dla niej „nigdy niewołane"
znaczyło „nigdy nie wykonane". Ta pozycja pyta o wołanie **w drzewie**. Obie liczby
są prawdziwe i opisują dwie różne rzeczy: `swiadkowie_klasy` jest **statycznie
wołane, dynamicznie nigdy**. Jest to ósma klasa, której nie ma w polu, i nazywam
ją, zamiast wpisywać funkcję do którejś z siedmiu.

## 2. GŁÓWNE ZNALEZISKO: funkcja użyta jako WARTOŚĆ, a nie jako wywołanie

Przeszedłem wszystkie **4486** funkcji poziomu modułu pod `tools/` siedmioma
drogami, które wypisałem w pliku definicji przed pomiarem. Bez żadnej z nich
zostało **sześć**:

```
polygon_perimeter_m                tools/blender/lod.py
bump                               tools/tests/assertion_gate.py
worker                             tools/tests/mutation_sweep.py
_fetch_url_that_refuses_to_fetch   tools/tests/test_fetchers.py
wezly_skladu_w_scenie              tools/tests/test_readme_claims.py
_odmowa_stalej                     tools/track/validate.py
```

Przeczytałem każdą z sześciu. **Pięć jest osiągalnych** — drogą, której nie
wymienia ani pole, ani mój zapis:

```
bump                              module.__dict__[BUMP] = bump
                                  (wstrzykniecie do przestrzeni nazw CUDZEGO modulu)
worker                            pool.submit(worker, slot, chunk, …)
                                  (przekazanie jako wartosc do puli procesow)
_fetch_url_that_refuses_to_fetch  GTFS.P.fetch_url = _fetch_url_that_refuses_to_fetch
                                  (podmiana atrybutu — monkeypatch)
wezly_skladu_w_scenie             "wielu skladow W SCENIE": (wezly_skladu_w_scenie, 1, …)
                                  (wartosc w slowniku)
_odmowa_stalej                    json.load(f, parse_constant=_odmowa_stalej)
                                  (argument wywolania cudzej funkcji)
```

**We wszystkich pięciu nazwa funkcji stoi bez nawiasu** — jest wartością, nie
wywołaniem. Każdy skan szukający `nazwa(` widzi je jako martwe, a one działają.

**Odpowiedź na pytanie „ile innych funkcji ma tę samą własność": JEDNA.**

```
polygon_perimeter_m    tools/blender/lod.py
```

Nie ma jej nigdzie poza własną definicją — ani wywołania, ani wartości, ani
wzmianki w prozie, w shellu czy w workflowie.

## 3. Rozkład dróg na całej populacji

```
funkcji poziomu modulu pod tools/:  4486
   z tego `test_*`:                 2664
   pozostalych:                     1822

   2542  ODKRYCIE PO NAZWIE
    801  wlasny modul
    305  wlasny modul + atrybut modulu
    191  wywolanie z innego modulu + wlasny modul
    115  atrybut modulu
    113  ODKRYCIE PO NAZWIE + __main__
    103  wywolanie z innego modulu + wlasny modul + atrybut modulu
     99  wlasny modul + __main__
```

**Dwa tysiące pięćset czterdzieści dwie funkcje — 57 % populacji — są osiągalne
WYŁĄCZNIE przez odkrycie po nazwie.** `test_all.py` w wierszu 509 robi
`[(n, f) for n, f in sorted(vars(mod).items()) if n.startswith("test_") and callable(f)]`,
czyli nie woła ich po nazwie, tylko zbiera wszystko, co zaczyna się od `test_`.

To jest **siódma droga**, której pole nie wymienia („import, `doctor.sh`, linia
poleceń, inny moduł") i której ja też nie wypisałem w definicji. Zapowiedziałem
w zapisie, że **jeśli znajdę siódmą, dopiszę ją do raportu jako klasę z nazwy** —
dopisuję. Mój pierwszy przebieg bez niej zgłosił **2661 funkcji „bez wołającego"**,
z czego 2659 to były zwykłe testy.

## 4. KONTROLA PRZYRZĄDU: NIE DA SIĘ JEJ SPEŁNIĆ W ZAPISANEJ POSTACI

Pole żądało, by `main` z `test_bin_path_framework.py` wyszedł jako **wołany
z linii poleceń**. Zmierzone:

```
if __name__ == "__main__":
    if "--inwentarz" in sys.argv:
        raise SystemExit(main())
    import test_all
    raise SystemExit(test_all.main(__file__))
```

`main()` wykonuje się **wyłącznie z flagą `--inwentarz`**, a przeszukanie całego
drzewa (`*.py`, `*.sh`, `*.yml`) po słowie `inwentarz` **nie znajduje ani jednego
miejsca**, które tę flagę podaje. Nic w tym repozytorium nie woła tej funkcji;
jest osiągalna wyłącznie przez człowieka, który sam wpisze polecenie.

**Gorzej: kontroli nie da się rozstrzygnąć żadnym szukaniem po nazwie**, bo `main`
jest jednocześnie nazwą **domyślnej gałęzi** tego repozytorium. Mój czytnik zgłosił
dla niej drogę `shell/workflow`, a źródłem było

```
.github/workflows/python-tests.yml:5:    branches: [main]
```

czyli wiersz o gałęzi, nie o funkcji. **Kontrola „przeszła" u mnie dwa razy
z rzędu z fałszywego powodu**, zanim przeczytałem, co ją spełniło. Nazywam to
wprost, zamiast raportować ją jako zdaną: jest to kontrola postawiona na nazwie
kolidującej z nazwą gałęzi, więc jej litera jest niespełnialna, a jej treść
(„czy coś to woła") rozstrzyga się dopiero czytaniem — i rozstrzyga się na NIE.

## 5. Przewidywania spisane PRZED pomiarem

| # | przewidywanie | wynik |
|---|---|---|
| S1 | `dwie_miary_czytnikow` nie jest wołane przez nic | trafione — ale §5.1 |
| S2 | `swiadkowie_klasy` **jest** wołane spoza swojego modułu | **OBALONE** — z wewnątrz |
| S3 | innych funkcji bez wołającego: 5–40 | **rozstrzygnięte w obie strony** |
| S4 | większość z nich ma podkreślenie na początku | **OBALONE** — dwie z sześciu |
| S5 | kontrola przyrządu zda się | **niespełnialna w literze** — §4 |
| S6 | znajdę drogę, której pole nie wymienia | trafione — **dwie** |

### 5.1 S1 nie było niezależne i mówię to drugi raz

Zapisałem przed pomiarem, że S1 powtarza tezę 6.D306 §10, więc jego trafienie
nie jest dowodem niczego poza tym, że tamta sonda miała rację. Wartość miało
wyłącznie **S2** — i S2 upadło.

### 5.2 S2 upadło i to jest najbardziej pouczające z sześciu

Przewidziałem, że `swiadkowie_klasy` okaże się wołane **spoza** modułu, bo 6.D306
samo nazwało swoją granicę jako „wołania wewnątrz własnego modułu". Z tego
wywnioskowałem, że wołanie musi być gdzie indziej. **Wniosek był zły, bo granica
tamtej sondy była inna, niż przeczytałem**: jej ograniczeniem był **czas
wykonania**, a nie zasięg pliku. Funkcja jest wołana dokładnie tam, gdzie sonda
patrzyła — tylko się nie wykonuje.

### 5.3 S3 jest rozstrzygnięte w obie strony i tak je zapisuję

Po **regule spisanej** (siedem dróg) bez wołającego zostaje **sześć** — trafienie.
Po **przeczytaniu tych sześciu** zostaje **jedna** — pudło, bo jeden jest poniżej
przedziału 5–40. Przewidywanie nie mówiło, czy liczyć po sicie, czy po czytaniu,
i to jest jego wada, nie zasługa. Ta sama usterka co przy Y4 w 6.D310 i V4
w 6.D313: **przedział bez jednostki nie jest przewidywaniem**.

## 6. Czego świadomie nie zrobiono

- **Nie usunięto żadnej funkcji** ani nie dopisano jej wołającego — pole zabrania
  wprost, także dla `polygon_perimeter_m`, jedynej bez żadnej drogi.
- **Nie zmieniono żadnej bramki** ani `test_all.py`.
- **Nie rozstrzygnięto, czy `swiadkowie_klasy` powinien zostać.** Funkcja, która
  wykonuje się wyłącznie przy padającej bramce, jest kosztem zerowym i wartością
  dodatnią w dniu awarii; ocena tego jest decyzją, nie pomiarem.
- **Nie dopisano ósmej ani dziewiątej drogi do żadnego narzędzia** — nazwałem je
  w raporcie, a ich wpisanie do czyjegoś skanu jest osobnym krokiem.
- **Nie tknięto `src/`** ani `data/`.

## 7. Zauważone przy okazji, nietknięte

**Pięć z sześciu „martwych" funkcji żyje przez przekazanie jako wartość**, a to
znaczy, że każdy skan tego repozytorium szukający `nazwa(` ma tę samą ślepą plamę.
Ile bramek liczy wołania wzorcem z nawiasem, nie policzyłem.

**`polygon_perimeter_m` stoi w `tools/blender/lod.py`**, czyli w narzędziu
geometrii, a nie w bramce. Od kiedy nie ma wołającego — nie sprawdziłem, bo pole
prosi o datę tylko dla dwóch nazwanych czytników, a ta nie jest jedną z nich.

**Szesnaście modułów pod `tools/` używa `getattr` albo `globals()`.** Wypisałem tę
liczbę, bo droga „wywołanie przez mapę nazw" była w mojej definicji i żadnej
funkcji przez nią nie znalazłem — ale szesnaście miejsc, w których mogłaby się
ukryć, zostaje nieprzeczytanych.

## 8. Weryfikacja — rzeczywiste wyjście

```
$ find . -name __pycache__ -prune -exec rm -rf {} +
$ python3 tools/tests/test_all.py
  [DRZEWO] 0 plikow drzewa roboczego poza zasiegiem bramek czytajacych `git ls-files` — 6.D165
  [BAJTKOD] wyczyszczono 1 kat. __pycache__ (1 plikow) pod tools/ — 6.D122
  2664/2664 przeszło
  RAZEM 375.942 s, 2664 testów, 139 modułów
EXIT=0
```

Zero `FAIL`. **Bramki nie przybyło** — pole „Poza zakresem" zabrania usuwania
czytników, dopisywania im wołających i zmiany którejkolwiek bramki. Bramki
dotknięte tą pozycją przeszły wcześniej osobno — `test_report_hygiene`,
`test_backlog`, `test_field_paths`, `test_report_claims`, `test_docs_map`,
`test_prose_counts` i `test_tree_walks`: **177/177**.

**Liczba 2664 w wyjściu zestawu i liczba 2664 funkcji `test_*` z §3 to ta sama
liczba, i to nie jest zbieg okoliczności** — zestaw wykonuje dokładnie te funkcje,
które odkrywa po nazwie. Zgodność obu liczb jest **niezależnym potwierdzeniem**,
że siódma droga z §3 jest policzona poprawnie: gdyby mój czytnik widział o jedną
funkcję `test_*` za dużo albo za mało, liczby by się rozjechały.

**Siódmy pomiar ściany na tym kontenerze w tej sesji:**

```
414,695   418,599   361,079   365,940   364,619   369,370   375,942
```
