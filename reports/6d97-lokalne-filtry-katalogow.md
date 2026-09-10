# Lokalne filtry katalogów zdjęte na rzecz wspólnego odsiania (10.09.2026)

**Zmierzone 10.09.2026 na:** `bd0bc92`, kontener tej sesji.
**Przyrząd:** skan drzewa składni po plikach chodzących po drzewie (nowa bramka
w `tools/tests/test_tree_walks.py`), liczniki pięciu skanów przed i po,
`python3 tools/tests/test_all.py`.

---

## 1. Filtrów było PIĘĆ, nie trzy — i znalazła je bramka, nie wpis

Wpis 6.D97 nazywał cztery miejsca: trzy kopie listy z `.gitignore` i jeden filtr
własny. Bramka napisana pod tę pozycję zgłosiła **pięć** kopii i jeden fałszywy alarm:

```
tools/tests/test_readme_claims.py:48        BUILD_DIRS = {"bin", "obj"}            (z wpisu)
tools/tests/test_dead_constants.py:56       "__pycache__" in katalog               (z wpisu)
tools/tests/test_dead_constants_csharp.py:76 os.sep+"obj" … or os.sep+"bin" …      (z wpisu)
tools/tests/test_architecture_doc.py:42     ARTEFAKTY = {"bin","obj",".vs","node_modules"}
tools/tests/test_sim_untested_members.py:54 _is_generated: "obj" in parts or "bin" in parts
tools/tests/test_tree_walks.py:170          "build"  ← FAŁSZYWY ALARM, dane testu parsera
```

Dwa ostatnie okazały się czymś innym, niż wyglądały, i to jest główny wynik pozycji.

## 2. Piąty filtr nie jest kopią i zostaje

`test_sim_untested_members._is_generated` **nie odsiewa katalogu z przejścia** —
klasyfikuje ścieżki pochodzące z `glob.glob(**/*.cs)`, żeby moduł mógł policzyć stan
PRZED (z plikami generowanymi, dziś jeden taki) i PO (bez nich). Zdjęcie go zabrałoby
**pomiar**, nie duplikat. Stoi więc na jawnej, zamkniętej liście `FILTRY_Z_WLASNEGO_POWODU`
z tym powodem, a nie w kodzie bez wyjaśnienia.

Czwarty, `ARTEFAKTY` w `test_architecture_doc.py`, jest kopią **częściową**: `bin` i `obj`
stoją w `.gitignore`, a `.vs` i `node_modules` nie. Zdjęte zostały dwa pierwsze; dwa
pozostałe zostają, bo odsiewa je reguła tego dokumentu, nie reguła repozytorium.

Szósty, `os.sep + "tests" in base` w `mutation_sweep.py`, jest niewidoczny dla bramki
i to jest poprawne: `tests` w `.gitignore` **nie stoi** i stać nie powinno — katalog
jest śledzony. Odsiewa go reguła narzędzia („mutujemy kod pod testem, nigdy testów").

## 3. Fałszywy alarm wymusił zawężenie skanu

Pierwsza wersja zgłosiła `build` z wiersza 170 `test_tree_walks.py` — napisu, który
jest **wejściem syntetycznym** testu parsera `.gitignore`, a nie filtrem. Skan pomija
teraz wnętrza funkcji `test_*`: filtry mieszkają w pomocnikach i na poziomie modułu,
fixture w testach. Zawężenie jest sprawdzone kontrolą negatywną (KN-4).

## 4. Pięć liczników przed i po — wszystkie identyczne

```
core_files()          53 → 53
_pliki_python()      192 → 192
_pliki() C#          128 → 128
targets()             67 → 67
real_paths()          12 → 12
```

To jest dokładnie pole „Skończone, gdy": zdjęcie kopii nie rusza ani jednej
raportowanej liczby, bo `TW.walk` odsiewał te katalogi już wcześniej.

## 5. Sześć kontroli negatywnych, `md5sum -c: OK` po każdej

| kontrola | mutacja | wynik |
|---|---|---|
| KN-1 | zdjęty filtr NIEOBJĘTY `.gitignore` (`tests` w `mutation_sweep`) | **czerwona**, `targets()` 67 → **192**, cztery bramki |
| KN-2 | wraca `BUILD_DIRS` do `test_readme_claims` | **czerwona** 9/10 |
| KN-3 | wracają `bin`/`obj` do `ARTEFAKTY` | **czerwona** 9/10 |
| KN-4 | skan przestaje pomijać wnętrza `test_*` | **czerwona** 9/10, fixture znów zgłaszany |
| KN-5 | nazwy katalogów wpisane na sztywno zamiast z `.gitignore` | **czerwona** 9/10 |
| KN-5b | lista z `.gitignore` kurczy się o `bin` | **czerwona** 8/10, dwie bramki |
| KN-6 | wpis wyjątku bez pokrycia w drzewie | **czerwona** 9/10 |

**KN-1 jest tą kontrolą, o którą prosi pole „Skończone, gdy", i wypada najmocniej:**
zdjęcie filtru na `tests` podnosi `targets()` z 67 na **192** i wywraca cztery bramki
`test_mutation_sweep.py`, w tym `test_tests_are_never_targets`. Filtr, który został,
jest więc nośny — nie jest resztką po 6.D74.

**KN-5 i KN-5b mierzą dwie różne rzeczy i dlatego stoją osobno.** Pierwsza wpisuje
nazwy na sztywno w samej bramce; zapala się, ale częściowo **sama na sobie** — wpisany
zbiór jest literałem w tym samym pliku. Druga zabiera `bin` ze zbioru czytanego
z `.gitignore` i zapala kontrolę przyrządu tam, gdzie należy: „`bin` zniknęło z listy
katalogów czytanej z `.gitignore` — bramka wyżej przestała widzieć kopię akurat tego
katalogu". To ta druga dowodzi, że lista NIE jest wpisana z ręki.

## 6. Weryfikacja

```
python3 tools/tests/test_all.py test_tree_walks.py
  -> 10/10 przeszło

python3 tools/tests/test_all.py
  -> RAZEM 121,597 s, 2193 testów, 118 modułów, kod 0
  -> 2193/2193 przeszło
```

Zestaw **2190 → 2193**, moduły bez zmiany (118). Zapadka `MIN_REPORTS`, podniesiona ze
dwustu piętnastu na dwieście szesnaście.

## 7. Czego świadomie nie zrobiłem

Nie tknąłem `.gitignore` ani nie rozszerzałem wspólnego odsiania o wzorce plikowe —
pole „Poza zakresem" wyklucza jedno i drugie. Nie zdjąłem `_is_generated` ani filtru
na `tests`: oba odsiewają z własnego powodu, co jest w pozycji zapisane jako warunek,
a nie jako wyjątek wynegocjowany po fakcie.

## 8. Zauważone i nietknięte

**`glob.glob(**, recursive=True)` jest trzecim kształtem przejścia po drzewie i stoi
poza wspólnym odsianiem.** Bramka z 6.D74 pilnuje `os.walk`, ta pozycja dołożyła skan
kopii listy katalogów — ale `test_sim_untested_members._all_sim_cs_files` chodzi po
drzewie `glob`em i `.gitignore` go nie dotyczy. Tam jest to zamierzone (patrz §2), ale
kształt jest ogólny i dziś nikt go nie liczy.
