# Audyt kolejki — sześć pozycji opisywało stan sprzed pracy, która już weszła

**Zmierzone 05.09.2026 na commicie:** `9b4d26d`

`docs/TASKS.md` mówi wprost: „**Aktualizacja tej listy jest częścią pracy, nie dodatkiem
do niej.** Pozycja zrobiona znika stąd i pojawia się jako wpis z sześcioma polami wyżej
w tym pliku". To zdanie nie miało **żadnej bramki**, a w jednej sesji 05.09.2026 sześć
pozycji okazało się wykonanych i nadal stojących w kolejce jak otwarte.

Ten raport zapisuje, które to były, po czym je poznano, i co teraz tego pilnuje.

## 1. Jak to wyszło — najdroższym z możliwych sposobów

Cztery z sześciu nie wyszły z przeglądu planu, tylko z **wzięcia pozycji do zrobienia**:
agent czytał opis, zaczynał pracę i dopiero pomiar obalał jej założenie.

| pozycja | co mówiła kolejka | co pokazał pomiar |
|---|---|---|
| 6.B8 | „2 ocalałe mutacje, udział 100 %" | 2 / 2 **zabite** na tym samym zestawie klas; 13 / 13 na pełnym |
| 6.D5 | audyt dryfu do zrobienia | `reports/mutation-drift.md` istnieje, obejmuje **28** modułów zamiast 12 |
| 6.B3 | „LOD tuneli pakietów B–F" | LOD dla B i E **istnieje** od T-210; C czeka na decyzję właściciela, D i F na model |
| 5.8 | „dwa moduły bez testu jednostkowego" | `f5126a3` dał oba, i to on zabił mutacje z 6.B8 |

Dwie pozostałe wyszły ze skanu historii, już po tamtych czterech:

| pozycja | dowód |
|---|---|
| 5.1 | `reports/mutation-sweep.md`, snapshot na `66b8301` (scalenie **#184**) |
| 5.2 | commit `470632d`, „**Pozycja 5.2**: rozjazd snapshotów wobec data/", wynik w `reports/snapshot-drift.md` |

**Koszt.** Dwa pełne zadania w tej sesji (6.B8 i to) skończyły się pomiarem i porządkiem
w planie zamiast kodem. To nie jest strata — 6.B8 dało twardy dowód, że moduł jest
pokryty — ale jest to praca, której nie trzeba by wykonywać, gdyby wiersz mówił prawdę.

## 2. Co zostało poprawione i dlaczego różnie

Rozstrzyga jedno: czy pozycja liczy się do zapadki `MINIMUM_DOCUMENTED_ITEMS`.

| pozycja | co z nią zrobiono | powód |
|---|---|---|
| 6.D5 | **adnotacja w wierszu**, zostaje w tabeli | jedna z dwunastu z kompletem sześciu pól; zdjęcie zbiłoby zapadkę, a tę wolno tylko podnosić |
| 6.B8 | to samo (#266) | to samo |
| 5.1, 5.2, 5.8 | **do tabeli domknięć** | brak bloku sześciu pól, więc do zapadki się nie liczą |
| 6.B3 | **nie ruszone** | jedyny przypadek wymagający oceny, nie odczytu: część pakietów czeka na decyzję właściciela. Zgłoszone, nie przeklasyfikowane |

Kolejka pracy po tej sesji: **26 pozycji** (było 31 na początku dnia), udokumentowanych
**12** przy zapadce 12.

## 3. Bramka — co łapie, a czego nie

`test_a_documented_item_whose_reports_all_exist_says_so_in_its_row`
w `tools/tests/test_backlog.py`.

**Łapie:** pozycję udokumentowaną, której pole **Wyjście** nazywa raporty, i wszystkie
te raporty już leżą w `reports/`, a wiersz tabeli o tym milczy. Wtedy albo praca jest
zrobiona i wiersz ma to mówić, albo pole **Wyjście** obiecuje plik znaczący co innego
niż to, co powstało — jedno i drugie jest usterką planu.

Na dzisiejszym drzewie warunek spełniają trzy pozycje: 6.B8, 6.D5 i 6.D6. Wszystkie trzy
mają adnotację, więc bramka jest zielona; przed tą poprawką 6.D5 jej nie miało i bramka
by ją wskazała:

```
kolejka opisuje stan sprzed pracy, która już weszła — wiersz ma dostać adnotację
„ZROBIONE w #NNN” albo wyjść do tabeli domknięć: ['6.D5: reports/mutation-drift.md już istnieje']
```

**Nie łapie, i to jest granica, nie przeoczenie:**

- **pozycji bez bloku sześciu pól.** 5.1 i 5.2 były właśnie takie — ich dowodem był
  commit, nie plik. Tej klasy nie da się sprawdzić tanio i uczciwie: „commit nazywa
  numer pozycji" trafiałoby też w commity, które ją tylko **cytują** (skan historii
  z tej sesji dał 12 trafień na 28 pozycji, w większości przez wiersze tabeli
  przepisane do treści commita);
- **pozycji, których wyjściem jest kod bez raportu** — większość pasma A i C;
- **pozycji, której raport rozszerza plik już istniejący.** To jedyne źródło fałszywego
  trafienia i ma tanie lekarstwo: pole **Wyjście** ma wtedy nazwać nowy plik albo sekcję,
  a nie cały istniejący raport. Czyli dokumentację, która i tak jest lepsza.

## 4. Czego ten audyt świadomie nie zrobił

- **Nie przeszedł pozycja po pozycji przez wszystkie 26.** Skan mechaniczny objął
  wszystkie, ale rozstrzygnięcie „zrobione czy nie" wymaga czytania cudzej intencji
  wszędzie tam, gdzie wyjściem jest kod. Bramka zawęża to do klasy, którą da się
  sprawdzić maszynowo, a reszta zostaje ryzykiem — nazwanym, zamiast przemilczanym.
- **Nie ruszył 6.B3.** Jego przeklasyfikowanie do „Czego agent nie ruszy bez decyzji"
  jest oceną, nie odczytem, i należy do właściciela.
- **Nie przepisał żadnego raportu triażu.** Datowanego pomiaru się nie przelicza.

## 5. Weryfikacja — rzeczywiste wyjście

```
$ python3 tools/tests/test_all.py
  1598/1598 przeszło

$ python3 -c "…test_backlog…"
praca: 26 | udokumentowanych: 12 | zapadka: 12
```
