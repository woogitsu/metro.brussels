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

1. `MIN_REPORTS` = **159**, czyli stan katalogu dziś. Liczba w tym akapicie zmieniała
   się **cztery razy w ciągu jednego wieczoru** i pełną listę wraz z tym, co każdą
   wartość unieważniło, nosi dziś komentarz samej stałej
   w `tools/tests/test_report_hygiene.py` — tam jest jej miejsce, bo tam stoi kod.
   Tutaj zostaje wniosek, a nie kronika.
   Gałąź powstała przy 153 raportach (152 na `a214ab9` plus ten raport) i tyle
   pierwotnie wpisała. Zanim doszła do `main`, weszły tam trzy pull requesty
   z własnymi raportami — #413, #414, #415 — więc w chwili scalenia stała była
   nieprawdziwa **o trzy**. Poprawną wartość odczytano z drzewa PO scaleniu `main`,
   na `e1fcfc1`, dwoma niezależnymi pomiarami: `ls reports/*.md | wc -l` → 156
   i `len(list(_reports()))` → 156.

   **To nie jest anegdota, tylko wynik.** Zapadka równościowa zaczerwieniła się
   dokładnie w miejscu, dla którego powstała, i to na własnym commicie autora —
   `test_every_constant_quoted_in_a_report_carries_the_value_from_the_code`
   wypisało: `zapadka-liczby-raportow.md:56: MIN_REPORTS mówi 153, kod 156`.
   Poprzednia litera reguły (`len(items) >= MIN_REPORTS`, stała 40) przepuściłaby
   153 bez jednego słowa i różnica rosłaby dalej. Dowodu, że nierówność bez sufitu
   starzeje się po cichu, nie trzeba było więc szukać: dostarczyła go ta sama
   zmiana, która ją usuwa.

   **I zestarzała się jeszcze DWA razy tego samego wieczoru.** Wartość 156 weszła do `main`
   z #416 i przestała być prawdziwa przy **pierwszym** raporcie dopisanym po niej
   (6.D43, `reports/pojemnosc-puli-ci.md`, katalog 157). Ta sama bramka wypisała
   wtedy to samo zdanie o jeden krok dalej — `MIN_REPORTS mówi 156, kod 157` —
   i znowu złapała to **zapadka, nie czyjaś czujność**. Wartość 157 padła
   natychmiast po niej, przy **następnym** raporcie (6.D54,
   `reports/wyrocznia-zielonosci-sys-exit.md`, katalog 158), tym samym zdaniem
   o jeszcze jeden krok dalej: `MIN_REPORTS mówi 157, kod 158`.

   **Trzy razy pod rząd jest mocniejszym argumentem niż pierwotne 112 pozycji
   różnicy**, i to jest właściwy wynik tej pozycji. Sto dwanaście dawało się
   opowiedzieć jako jedno zaniedbanie z przeszłości, które wystarczy raz nadgonić.
   Trzy rozjazdy w ciągu jednego wieczoru, przy trzech różnych zmianach, pokazują coś
   innego: **stała pilnująca katalogu, który rośnie, starzeje się MIĘDZY napisaniem
   commita a jego scaleniem** — w okresie, w którym autor już nic nie mierzy, bo
   uważa zadanie za skończone. Żadna dyscyplina po stronie autora tego nie załatwi,
   bo nie ma momentu, w którym miałby ją zastosować. Załatwia to wyłącznie warunek,
   który rozjazdu nie przepuszcza — i dlatego cena tej zapadki (każdy nowy raport
   wymusza podniesienie stałej i poprawienie każdego raportu, który ją cytuje) jest
   ceną, nie usterką.
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

**Wyjścia niżej pochodzą z drzewa PRZED scaleniem `main`, gdzie katalog miał 153
raporty, i dlatego mówią 153 tam, gdzie kod mówi dziś 156.** Nie są przepisane pod
dzisiejszą liczbę świadomie: to wklejone wyjścia rzeczywistych przebiegów, a podmiana
liczby w cytowanym wyjściu zrobiłaby z nich wyjście zmyślone — czyli dokładnie to,
czego `CLAUDE.md` §5 zabrania, i to w pliku, którego cała treść polega na tym, że
wyjścia są prawdziwe. Zmienia się przy tym **tylko liczba stanu katalogu**; sam
kierunek każdej kontroli (o jeden w górę, równo, o jeden w dół, na starą wartość)
i liczba padających testów są od niej niezależne. Kontrolę na dzisiejszym drzewie,
przy 156, powtórzono dla wiersza „równo" — §5.

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

Na drzewie przed scaleniem `main`, przy 153 raportach:

```
$ python3 tools/tests/test_all.py test_report_hygiene.py
  15/15 przeszło
kod: 0
```

### Kontrole powtórzone na drzewie PO scaleniu `main`, przy 156 raportach

Powtórzone, bo stała musiała się zmienić razem ze stanem katalogu, a kontrola
wykonana na innej liczbie nie mówi o tej. `md5` pliku przed pierwszą mutacją
i po przywróceniu: `cfd2565f7e0dcf8906631a43d8791792` — ta sama, więc plik wrócił
co do bajtu. Po każdej mutacji `find tools -name __pycache__ -type d -exec rm -rf {} +`.

```
=== MIN_REPORTS=157 -> kod 1
  FAIL test_data_i_commit_stoja_w_naglowku_a_nie_gdziekolwiek_w_raporcie: tylko 156 raportów w pętli
  FAIL test_kazda_sciezka_wymieniona_w_raporcie_rozwiazuje_sie_w_drzewie: bramka przeszła tylko 156 raportów, a w `reports/` jest ich co najmniej 157 — skan przestał czytać katalog
  FAIL test_kazdy_raport_podaje_commit_na_ktorym_mierzono: bramka przeszła tylko 156 raportów, a w `reports/` jest ich co najmniej 157 — skan przestał czytać katalog
  FAIL test_kazdy_raport_podaje_date_pomiaru: bramka przeszła tylko 156 raportów, a w `reports/` jest ich co najmniej 157 — skan przestał czytać katalog
  FAIL test_konwencja_naglowka_jest_wyczytana_z_raportow_ktore_ja_juz_maja: tylko 156 raportów w pętli
  FAIL test_zapadka_liczby_raportow_nie_zostaje_za_katalogiem: raportów jest 156 przy `MIN_REPORTS` = 157 — któryś raport zniknął z `reports/` albo skan przestał go czytać
  FAIL test_zapis_o_naglowku_w_konwencjach_zgadza_sie_z_ksztaltem_z_raportow: tylko 156 raportów w pętli
  8/15 przeszło
=== MIN_REPORTS=155 -> kod 1
  FAIL test_zapadka_liczby_raportow_nie_zostaje_za_katalogiem: raportów w `reports/` jest 156, a `MIN_REPORTS` stoi na 155 — podnieś ją do 156 w tym samym commicie, w którym dopisujesz raport; zapadka, która została z tyłu, zwalnia skan z czytania różnicy
  14/15 przeszło
=== MIN_REPORTS=156 -> kod 0
  15/15 przeszło
md5 po przywroceniu: cfd2565f7e0dcf8906631a43d8791792
```

Kształt wyniku jest ten sam co na 153 i to jest sens powtórzenia: **o jeden w górę**
wywraca siedem testów (sześć podłóg „skan czyta katalog" i sam nowy test — nie da się
ich spełnić razem z zapadką wyprzedzającą katalog), **o jeden w dół** wywraca
**dokładnie jeden**, ten nowy, a jego komunikat podaje liczbę do wpisania. Kierunki
nie zależą od stanu katalogu; zależy od niego tylko liczba w komunikacie.

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
