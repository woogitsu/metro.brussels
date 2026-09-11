# 6.D122 — obrona przed starym bajtkodem przeniesiona z pamięci do narzędzia

**Zmierzone 11.09.2026 na:** `8cb78a9`, kontener tej sesji.
**Przyrząd:** `tools/tests/tree_walk.py` (`wyczysc_bajtkod`), `tools/tests/test_all.py`,
`tools/tests/test_bytecode_staleness.py`, sześć przebiegów całego zestawu,
`CLAUDE.md` §5, `docs/06-worked-example.md`.

---

## 1. Co się zmieniło i dlaczego to nie jest wygoda

`test_all.py` kasuje każdy `__pycache__` pod `tools/` **przed własnymi importami
narzędzi** i mówi o tym jednym wierszem:

```
  [BAJTKOD] wyczyszczono 5 kat. __pycache__ (11 plikow) pod tools/ — 6.D122
```

6.D102 zmierzyło pułapkę i zapisało procedurę ręczną, ale zostawiło ją jako **jedyną**
obronę. Pułapka nie ogranicza się jednak do kontroli negatywnych: zwykła edycja modułu
narzędziowego i natychmiastowy przebieg zestawu mają **ten sam kształt** co mutacja —
ta sama sekunda, a przy poprawce w rodzaju `0.30` na `0.31` także ta sama długość.
CPython uznaje bajtkod za ważny po parze **(mtime źródła w sekundach, rozmiar)**, więc
ani jedno, ani drugie pole się nie rusza. Procedura, którą trzeba pamiętać, broni
wyłącznie tego, kto o niej pamiętał.

## 2. Położenie wywołania jest treścią, a nie stylem

Wywołanie stoi **przed** `import profiles, validate as V, reference as R, …`
w `test_all.py`. Przeniesione do `main()` byłoby spóźnione: te importy wykonują się
przy imporcie pliku, więc stary bajtkod narzędzi byłby już wczytany, a wiersz
`[BAJTKOD]` mówiłby o obronie, która niczego nie zmieniła — ta sama rodzina co 6.D27.

**Żaden inny test tego nie zobaczy**, bo wynik przebiegu jest w obu wariantach
identyczny. Dlatego pilnuje tego osobny test czytający kolejność z **AST**, a nie
z kolejności napisów: komentarz albo zdanie w dokumentacji modułu wyglądałyby przy
wyszukiwaniu napisu tak samo jak wywołanie. KN-1 to przybija.

## 3. Czas: sześć przebiegów, trzy pary — tak jak w 6.D102

| wariant | przebieg 1 | przebieg 2 | przebieg 3 | średnia |
|---|---|---|---|---|
| **z czyszczeniem** (każdy start zimny) | 145,753 s | 147,224 s | 147,247 s | **146,74 s** |
| **bez czyszczenia** (start ciepły) | 147,190 s | 148,671 s | 147,094 s | **147,65 s** |

Czyszczenie **nie kosztuje nic**: różnica średnich wynosi 0,91 s **na korzyść
czyszczenia**, przy rozrzucie wewnątrz wariantu 1,49 s (z) i 1,58 s (bez). To jest
powtórzenie wyniku 6.D102 (zimny 126,27 / 125,65 / 127,47 s, ciepły 127,17 / 127,49 /
125,25 s) na dzisiejszym, o 62 % większym zestawie. Przyczyna jest ta sama: moduły
testowe i tak kompilują się ze źródła przez `assertion_gate.load_instrumented`, więc
cache bajtkodu obejmuje wyłącznie moduły narzędziowe — czyli dokładnie te, które
wpadają w pułapkę.

**Zakaz z pola „Poza zakresem" pozycji 6.D102 chronił więc przed kosztem, którego nie
ma**, i to jest powód, dla którego ta pozycja mogła powstać. W CI pułapki zresztą nie
było: `actions/checkout` robi `git clean -ffdx`, a `__pycache__` stoi w `.gitignore`,
więc czyszczenie jest tam operacją na pustym katalogu.

## 3a. Funkcja mieszka w `tree_walk.py`, i to rozstrzygnęła bramka, nie gust

Pierwsza wersja trzymała `_wyczysc_bajtkod` w `test_all.py`. Pełny przebieg odrzucił
to dwiema bramkami naraz:

```
FAIL test_no_tool_walks_the_tree_without_the_shared_filter:
  przejście po drzewie z pominięciem odsiania z `.gitignore`:
  [('tools/tests/test_all.py', 38)] — użyj `tree_walk.walk`
FAIL test_zaden_skan_nie_trzyma_wlasnej_kopii_listy_z_gitignore:
  [('tools/tests/test_all.py', 39, '__pycache__')]
```

Pierwszej **nie dało się** uciszyć wpisem: `MAX_WOLNO_WPROST` stoi na 2 i wolno ją
wyłącznie **obniżać**. Funkcja przeniosła się więc do `tree_walk.py`, który w
`WOLNO_WPROST` już stoi — zamiast kupować trzeci wyjątek.

Druga jest ciekawsza, bo dotyka sprzeczności prawdziwej, a nie formalnej: **`TW.walk`
nie nadaje się tu z definicji**, ponieważ odsiewa katalogi z `.gitignore`, a
`__pycache__` w `.gitignore` stoi — czyli odsiewa dokładnie to, czego ta funkcja
szuka. Jest to jedyne narzędzie w drzewie, którego **przedmiotem** jest katalog
pominięty. Stąd jawny wpis w `FILTRY_Z_WLASNEGO_POWODU` z tym powodem zapisanym
zdaniem; tamten słownik zapadki nie ma, bo przyjmuje wyłącznie wpisy z powodem.
KN-8 pokazuje, że bez tego wpisu bramka zapala się z powrotem.

## 4. Procedura ręczna zostaje — jako druga linia, nie jako zabytek

`CLAUDE.md` §5 i `docs/06-worked-example.md` są **przepisane, a nie dopisane obok**:
oba mówiły, że procedura ręczna jest jedyną obroną, i to przestało być prawdą. Samo
polecenie zostaje, z dwóch zmierzonych powodów:

* pułapka dotyczy także przebiegów, które **nie idą przez `test_all.py`** — własnego
  `python3 -c`, importu w konsoli, skryptu wołanego wprost z `tools/`;
* polecenie obejmuje **całe drzewo**, a zestaw sprząta wyłącznie `tools/`, bo tego
  żąda pole „Poza zakresem" tej pozycji.

Obecności polecenia w obu dokumentach pilnuje
`test_procedura_stoi_w_dokumentach_a_nie_tylko_w_raporcie` (KN-7).

## 5. Kontrola negatywna, która wyszła ZIELONA — i co z niej wynikło

**KN-4** zdjęła wartownię `if not getattr(sys, "_metro_bajtkod_wyczyszczony", None)`,
czyli pozwoliła czyszczeniu odpalić się przy **każdym** załadowaniu modułu. Wynik:
**12/12, zielono**.

Asercja, która miała tego pilnować, brzmiała `wynik.stdout.count("[BAJTKOD]") == 1`
i liczyła wiersze w przebiegu **jednego** modułu. W takim przebiegu `_discover`
chodzi wyłącznie po ścieżkach z `only`, więc `test_all.py` **nie jest ładowany po raz
drugi** — wypis pada raz z wartownią i bez niej. Asercja mierzyła coś, co zachodzi
zawsze, a komentarz nad nią mówił, że mierzy wartownię.

Zamknięte testem, który ładuje `test_all.py` drugi raz **naprawdę**, tą samą drogą co
`_discover` (`AG.load_instrumented` pod inną nazwą), z przekierowanym stdout — plus
asercją wstępną, że ten proces przeszedł już przez pierwsze czyszczenie, bo inaczej
test mierzyłby załadowanie pierwsze. Po tej zmianie ta sama mutacja wywraca test
(**KN-4b, 12/13**).

## 6. Błąd popełniony w trakcie: test, który uruchamiał sam siebie

Pierwsza wersja `test_zestaw_MOWI_ze_wyczyscil` wołała podproces
`test_all.py test_bytecode_staleness.py` — czyli moduł, **w którym stoi ten test**.
Podproces uruchamiał go od nowa, on odpalał kolejny podproces i tak bez końca; przebieg
trzeba było zabić. To ta sama pomyłka co w 6.D114, tylko z drugiej strony: tam zestaw
dostawał jako argument moduł, który właśnie sprawdzał wywołania zestawu.

Naprawione modułem **piaskownicy** pisanym do katalogu tymczasowego — `test_all.py`
przyjmuje ścieżkę do istniejącego pliku `test_*.py` spoza `AG.paths()` (6.D25), więc
podproces ma co uruchomić, a nic w drzewie się nie zmienia. Powód stoi w komentarzu
przy wywołaniu, żeby nikt nie „uprościł" tego z powrotem.

## 7. Kontrole negatywne — WYKONANE, nie opisane

`cp` na bok i `md5sum -c` po przywróceniu (nigdy `git checkout`), `__pycache__`
czyszczony przed każdym przebiegiem.

Wszystkie przebiegi po przeniesieniu funkcji liczone na dwóch modułach razem
(`test_bytecode_staleness.py` + `test_tree_walks.py`), baza **26/26**.

| kontrola | zmiana | wynik |
|---|---|---|
| KN-1 | wywołanie przeniesione ZA importy narzędzi | **25/26**, test kolejności z AST |
| KN-2 | czyszczenie chodzi po całym `ROOT` | **25/26**, kasuje spoza `tools/` |
| KN-3 | wypis `[BAJTKOD]` zdjęty | **25/26** |
| KN-4 | wartownia na `sys` zdjęta, przed dodaniem testu | **12/12 ZIELONA** — patrz §5 |
| KN-4b | to samo po dodaniu testu wartowni | **25/26** |
| KN-5 | funkcja nic nie kasuje | **24/26**, dwa testy |
| KN-6 | laboratorium przeniesione POZA `tools/` | **25/26** |
| KN-7 | procedura zdjęta z `CLAUDE.md` | **25/26** |
| KN-8 | wpis w `FILTRY_Z_WLASNEGO_POWODU` zdjęty | **25/26** |

Po każdej: `md5sum -c` → `OK` na sześciu plikach.

KN-6 jest tu warta zdania: laboratorium pułapki musi leżeć **pod `tools/`**, bo tam
i tylko tam funkcja czyści. Lab w korzeniu katalogu tymczasowego mierzyłby, że funkcja
nic nie robi, i wyglądałby dokładnie tak samo jak lab, w którym pułapki nie ma.

## 8. Czego nie zrobiłem

* **Nie ruszyłem sposobu liczenia testów** ani niczego poza `tools/` — oba wprost
  w polu „Poza zakresem".
* **Nie zdjąłem procedury ręcznej z dokumentów** — powody w §4, i to jest pole
  „Wyjście" tej pozycji, a nie moja ostrożność.
* **Nie tknąłem `mutation_sweep.py`**, który ma własne czyszczenie od 6.D113; te dwa
  mechanizmy nie kolidują, bo sweep czyści pojedynczy plik w drzewie roboczym, a ten
  kasuje katalogi przed startem procesu.
* **Nie zmieniłem `SUITE_RUNTIME_BUDGET_S`** — patrz niżej, to jest obserwacja, nie
  zadanie tej pozycji.

## 9. Zauważone przy okazji

`SUITE_RUNTIME_BUDGET_S` stoi na 150,0 s, a sześć dzisiejszych przebiegów dało
145,75–148,67 s. Margines wynosi więc **1,3 s w najgorszym z sześciu**, czyli mniej
niż rozrzut między przebiegami tego samego wariantu (1,58 s). Zapadka nie jest dziś
przekroczona i nic z tego nie wynika dla tej pozycji — ale najbliższy moduł dopisany
do zestawu przewróci ją na maszynie o tej wydajności. `MEASURED_MAX_WALL_S`, z którego
liczony jest margines, opisuje przebieg znacznie starszy i mniejszy.
