# Zapadka liczby raportów — ile raportów skan naprawdę czyta (6.D45)

**Zmierzone 08.09.2026 na commicie:** `a214ab9`

`MIN_REPORTS` w `tools/tests/test_report_hygiene.py` istnieje po to, żeby wskazanie
katalogu na pusty albo literówka w globie nie dały pustej pętli i zielonej bramki.
W dniu pomiaru stała mówiła **40**, a `reports/` miało **152** pliki `.md`. Ten raport
podaje, ile raportów każda z bramek tego modułu naprawdę czyta, o ile stała była za
stanem i co po zmianie wywraca zestaw, a co nie.

## 1. Stan zmierzony, nie zapamiętany

Pomiar wykonany na `a214ab9`, **przed** commitem 6.D45:

```
$ ls reports/*.md | wc -l
152
```

Pole „Skąd" pozycji 6.D45 mówi **140**, i to jest różnica warta zapisania, a nie
przemilczenia: wiersz tabeli powstał tego samego dnia, a katalog urósł o dwanaście
raportów, zanim pozycja została wzięta. Przesłanka pozycji przez to nie upada —
**rośnie**. Wiersz mówi „sto pozycji za stanem"; zmierzone jest **sto dwanaście**
(152 − 40), czyli skan mógł przestać czytać 74% katalogu i przejść na zielono. Liczba
wpisana w stałą jest wynikiem polecenia wyżej, powiększonym o ten jeden raport, który
commit 6.D45 dokłada — czyli **153**. Zapamiętanej wartości nie wpisuję tu w ogóle:
to, że wiersz tabeli zestarzał się w ciągu jednego dnia, jest dowodem, po co ta
zapadka ma stać na równości.

## 2. Ile raportów czyta która bramka

Zmierzone na drzewie z tym raportem już w katalogu (153 pliki `.md`), przez te same
funkcje, na których stoją bramki:

| co | ile | podłoga przed 6.D45 | zapas |
|---|---|---|---|
| plików `.md` w `reports/` | 153 | 40 | 113 |
| z datą pomiaru w nagłówku | 153 | 40 | 113 |
| z commitem pomiaru w nagłówku | 151 | 40 | 111 |
| z datą **i** commitem (`reference`) | 151 | 38 | 113 |
| z wierszem pola niosącym SHA | 148 | 40 | 108 |
| ścieżek w grawisach (`seen`) | 1392 | 500 | 892 |

Podłogą w pięciu z tych wierszy była stała `MIN_REPORTS`; w wierszu `reference` —
`MIN_REPORTS` pomniejszone o `MAX_COMMIT_EXCEPTIONS`; ostatni wiersz ma osobny próg,
wpisany wprost w bramkę ścieżek. Wartości z kolumny „podłoga" są wartościami z dnia
pomiaru, nie dzisiejszymi — dzisiejsze podaje kod.

Sześć asercji w sześciu testach niesie podłogę „skan czyta katalog" i **każda z nich
była nierównością bez sufitu**. To jest cała treść usterki: nierówność bez sufitu nie
starzeje się z hukiem, tylko po cichu — odległość między stałą a stanem rośnie
z każdym dopisanym raportem, a bramka przez cały czas świeci na zielono.

## 3. Co się zmieniło

1. `MIN_REPORTS` = **153**, czyli stan katalogu po tym commicie.
2. Nowy test `test_zapadka_liczby_raportow_nie_zostaje_za_katalogiem` pilnuje
   **równości** dwiema asercjami w przeciwnych kierunkach, na wzór
   `test_the_documented_ratchet_does_not_lag_behind_the_file` z
   `tools/tests/test_backlog.py`. Nowy raport nie przechodzi bez podniesienia stałej
   w tym samym commicie; zniknięcie raportu nie przechodzi wcale.
3. Podłoga w `test_zapis_o_naglowku_w_konwencjach_zgadza_sie_z_ksztaltem_z_raportow`
   jest **przekierowana, nie poluzowana**. Stała tam `sum(counts) >= MIN_REPORTS`,
   czyli 40 przy 148 raportach z wierszem pola (147 na `a214ab9`, przed dołożeniem
   tego raportu) — 108 raportów zapasu. Po podniesieniu
   `MIN_REPORTS` do stanu katalogu ta asercja zapaliłaby się na prawdzie o katalogu,
   nie na usterce: wiersza pola nie ma pięć raportów. Podłoga liczy się więc od stanu
   katalogu minus nowa zapadka `MAX_REPORTS_WITHOUT_FIELD_LINE` = 5, a sama zapadka
   jest pilnowana w obie strony. **Zapas zszedł ze 108 do zera.**

Pięć raportów bez wiersza pola, z powodem widocznym w pliku:
`reports/R-006-line-speed.md` i `reports/T-401-line-run.md` nie mają SHA wcale (stoją
w `COMMIT_EXCEPTIONS`, powody tam), a `reports/mutacje-rdzen-sygnalizacji.md`,
`reports/mutation-triage-fizyka.md` i `reports/mutation-triage-parametry.md` nazywają
commity w **tabeli** przeglądu, nie w wierszu pola.

Zapadka `MAX_REPORTS_WITHOUT_FIELD_LINE` **nie jest bramką na kształt nagłówka** —
takiej być nie może, zmierzyło to 6.D38 (`reports/ksztalt-naglowka-raportu.md`),
a `docs/04-conventions.md` nazywa kształt zaleceniem, nie wymogiem. Kształtów wiersza
pola jest dziś **szesnaście** i wszystkie przechodzą; zapadka mówi tylko tyle, że
liczba nagłówków, których przyrząd nie umie przeczytać, nie rośnie **po cichu**.

## 4. Kontrole negatywne — wykonane

Po każdej mutacji `find tools -name __pycache__ -type d -exec rm -rf {} +`, bo mutacja
tej samej długości bajtowej w tym samym oknie mtime zostawia nieświeży `.pyc`
i weryfikacja czyta stary bajtkod — to przypadek z 6.D41. Suma `md5` pliku po każdym
przywróceniu: `160bcde4b7d0983478181b755a74dc94`, ta sama po każdej z siedmiu
kontroli. Kontrole zostały powtórzone na pliku w kształcie commitowanym — wyjścia
niżej są z tego drugiego przebiegu, nie z próby na wcześniejszej wersji komentarzy.

**A. `MIN_REPORTS` podniesione o jeden ponad stan katalogu** — pada siedem
testów: sześć podłóg i sam nowy test, bo zapadki wyprzedzającej katalog nie da się
spełnić razem z nimi.

```
FAIL test_zapadka_liczby_raportow_nie_zostaje_za_katalogiem: raportów jest 153 przy `MIN_REPORTS` = 154 — któryś raport zniknął z `reports/` albo skan przestał go czytać
8/15 przeszło
kod: 1
```

**B. `MIN_REPORTS` równe stanowi katalogu** — stan commitowany.

```
15/15 przeszło
kod: 0
```

**C. `MIN_REPORTS` obniżone o jeden pod stan katalogu** — pada **dokładnie jeden**
test, ten nowy.

```
FAIL test_zapadka_liczby_raportow_nie_zostaje_za_katalogiem: raportów w `reports/` jest 153, a `MIN_REPORTS` stoi na 152 — podnieś ją do 153 w tym samym commicie, w którym dopisujesz raport; zapadka, która została z tyłu, zwalnia skan z czytania różnicy
14/15 przeszło
kod: 1
```

**D. `MIN_REPORTS` cofnięte na wartość, którą miało przed tą poprawką** — pada
dokładnie ten sam jeden test i tym samym zdaniem. **Przed** tą zmianą ta wartość przechodziła cały moduł na zielono;
to jest usterka 6.D45 pokazana z jednej strony.

```
FAIL test_zapadka_liczby_raportow_nie_zostaje_za_katalogiem: raportów w `reports/` jest 153, a `MIN_REPORTS` stoi na 40 — podnieś ją do 153 w tym samym commicie, w którym dopisujesz raport; zapadka, która została z tyłu, zwalnia skan z czytania różnicy
14/15 przeszło
kod: 1
```

**E. `MAX_REPORTS_WITHOUT_FIELD_LINE` podniesione o jeden** — zapas zrobiony na przyszłe
nagłówki bez wiersza pola.

```
FAIL test_zapis_o_naglowku_w_konwencjach_zgadza_sie_z_ksztaltem_z_raportow: zapadka 6 stoi wyżej niż stan (5) — obniż ją do stanu faktycznego, inaczej robi zapas na przyszłe nagłówki bez wiersza pola
14/15 przeszło
kod: 1
```

**F. `MAX_REPORTS_WITHOUT_FIELD_LINE` obniżone o jeden** — podłoga podniesiona nad stan
katalogu.

```
FAIL test_zapis_o_naglowku_w_konwencjach_zgadza_sie_z_ksztaltem_z_raportow: tylko 148 raportów ma wiersz pola z SHA przy 153 w katalogu i zapadce 4 — przyrząd przestał czytać nagłówki
14/15 przeszło
kod: 1
```

**G. przyrząd przestaje czytać część nagłówków** — kontrola, dla której to
przekierowanie w ogóle powstało. `_header_field_line` zawężony z `**` do
`**Zmierzone`, czyli przestaje widzieć wiersz pola o innej etykiecie:

```
FAIL test_zapis_o_naglowku_w_konwencjach_zgadza_sie_z_ksztaltem_z_raportow: tylko 140 raportów ma wiersz pola z SHA przy 153 w katalogu i zapadce 5 — przyrząd przestał czytać nagłówki
14/15 przeszło
kod: 1
```

Na **tym samym** zepsutym przyrządzie stara podłoga `sum(counts) >= MIN_REPORTS` przy
`MIN_REPORTS = 40` jest zielona — zmierzone, nie przewidziane:

```
prefiks '**'           -> z wierszem pola: 148   bez:   5   stara podłoga (>=40): ZIELONA   nowa (>= 148): ZIELONA
prefiks '**Zmierzone'  -> z wierszem pola: 140   bez:  13   stara podłoga (>=40): ZIELONA   nowa (>= 148): CZERWONA
```

Zielona zostaje też kontrola detektora (punkt 7 w docstringu modułu), bo jej literał
zaczyna się od `**Zmierzone`. Trzynastu nieczytanych nagłówków nie zobaczyłby więc
nikt — i to jest odpowiedź na pytanie, czy przekierowanie sprawdza więcej, czy mniej.

## 5. Weryfikacja całego zestawu

```
$ python3 tools/tests/test_all.py test_report_hygiene.py
  15/15 przeszło
kod: 0
```

## 6. Czego świadomie nie zrobiłem

- **Nie przemianowałem `MIN_REPORTS`.** Nazwa z przedrostkiem minimum przy warunku
  równościowym wygląda na niezgodność, ale rola podłogi w sześciu asercjach zostaje
  bez zmian, a wzorzec tej pozycji — `MINIMUM_DETAIL_BLOCKS` w
  `tools/tests/test_backlog.py` — nosi ten sam przedrostek, będąc pilnowany na
  równość. Przemianowanie ruszyłoby `docs/TASKS.md` i dwa raporty, nie zmieniając
  ani jednej asercji.
- **Nie ruszyłem progu `seen >= 500`** w bramce ścieżek, choć ma dokładnie ten sam
  kształt problemu: zmierzony przy 623 trafieniach w 48 raportach, dziś trafień jest
  **1392**, czyli zapas 892. Pole „Wyjście" 6.D45 mówi o `MIN_REPORTS`, a to jest
  osobna stała w osobnej bramce; zgłaszam ją niżej.
- **Nie kasowałem ani nie scalałem raportów, żeby liczby się zgodziły** — pole „Poza
  zakresem" 6.D45 zabrania tego wprost.
- **Nie ruszyłem `COMMIT_EXCEPTIONS`** — to samo pole zabrania.
- **Nie przeliczyłem żadnej liczby w datowanym raporcie.**
  `reports/ksztalt-naglowka-raportu.md` §10 podaje „`MIN_REPORTS = 40` przy 140
  raportach" i zostaje z tą liczbą; dostał **adnotację** z datą, bo pomiaru z datą się
  nie przelicza (`docs/04-conventions.md`).

## 7. Zauważone przy okazji, nie tknięte

- **`seen >= 500` w `test_kazda_sciezka_wymieniona_w_raporcie_rozwiazuje_sie_w_drzewie`**
  ma zapas 892 przy 1392 trafieniach. Ta bramka ma wykrywać literówkę we wzorcu
  ścieżki; przy takim zapasie wzorzec mógłby przestać łapać dwie trzecie ścieżek
  i przejść. To jest ta sama rodzina co 6.D45 i osobna pozycja, nie ta.
- **Pole „Wejście" 6.D45 podaje „obie asercje w wierszach 249 i 263"**, a w dniu
  wykonania stały w 334 i 348. Numer wiersza starzeje się przy każdym dopisanym
  akapicie, dlatego w nowym komentarzu przy stałej nie ma ani jednego numeru wiersza,
  tylko nazwy testów.
- **`docs/04-conventions.md` nie ma „zapisu o zapadkach"**, na który powołuje się pole
  „Wejście" tej pozycji. Reguła „zapadkę wolno tylko podnosić" stoi wyłącznie
  w komentarzach przy stałych (`MAX_COMMIT_EXCEPTIONS` tutaj,
  `MINIMUM_DOCUMENTED_ITEMS` i `MINIMUM_DETAIL_BLOCKS` w `tools/tests/test_backlog.py`).
  Dopisanie jej do konwencji jest zmianą dokumentu, którego ta pozycja nie ma w polu
  „Wyjście", więc go nie ruszam.
