# Zepsuta komórka CSV nazywa plik, wiersz i kolumnę (6.A24)

**Zmierzone 07.09.2026 na commicie:** `c1f5618689ac834fd40c8e815f838f89e443b409`
(gałąź `claude/6a24-komorka-csv`).

## 1. Skąd ta pozycja i dlaczego „nietknięta" nie znaczyło „dobra"

6.A14 przeszła po **jedenastu** drogach wartości opcji do liczby i jedną zostawiła
nietkniętą, wpisując ją jako **jedyne** usprawiedliwienie
w `tools/tests/test_runner_number_parsing.py`:

> `Compare` — rozbiór komórek CSV (`a[c]`, `b[c]`), nie wartości opcji — komunikat
> nazywający opcję byłby tu nieprawdą, bo zła komórka nie jest złą opcją.

Powód był prawdziwy i **nadal jest**. Ale nie wynikało z niego prawo do komunikatu
platformy: wynikał z niego tylko **inny nagłówek**. Do dziś zepsuta komórka kończyła
się tym samym zdaniem, które 6.A14 wyjęła z opcji — `The input string 'x' was not in
a correct format.` — bez pliku, bez wiersza i bez kolumny.

`compare` jest **wyrocznią parzystości** rdzenia i sceny; jego odmowa jest jedynym
śladem, jaki dostaje czytający, gdy jeden z dwóch plików jest zepsuty.

## 2. Stan po zmianie

```
$ compare build/d1.csv build/d2.csv        (zepsuta komorka 0 w wierszu 3)
BŁĄD: build/d2.csv: wiersz 3 (nagłówek to wiersz 0), kolumna 1 „step” — „abc” nie jest liczbą
kod=1

$ compare build/d1.csv build/d3.csv        (zepsuta komorka 4 w wierszu 10)
BŁĄD: build/d3.csv: wiersz 10 (nagłówek to wiersz 0), kolumna 5 „speed_mps” — „nie-liczba” nie jest liczbą

$ compare build/d2.csv build/d1.csv        (ten sam zepsuty plik, PIERWSZY argument)
BŁĄD: build/d2.csv: wiersz 3 (nagłówek to wiersz 0), kolumna 1 „step” — „abc” nie jest liczbą

$ compare build/d1.csv build/d1.csv        (dwa poprawne)
kod=0
```

Trzeci wiersz jest osobnym warunkiem, nie ozdobą: komunikat nazywa plik **zepsuty**,
nie pierwszy z wiersza poleceń. Poprawka wypisująca zawsze `args[1]` przeszłaby
pierwszy test, a czytający szukałby usterki w pliku, który jest w porządku — ma to
swój test i swoją kontrolę negatywną (KN-2).

**Numer wiersza jest powiedziany, nie zostawiony do zgadnięcia.** Pole „Skończone,
gdy" żądało tego wprost. Liczony jest indeks w tablicy wierszy pliku, gdzie nagłówek
ma numer **0** — tak samo jak w dwóch sąsiednich odmowach tej samej pętli („zła liczba
kolumn", „różna faza scenariusza"), więc trzy komunikaty tej pętli mówią o tym samym
numerze; nowy dopisuje do niego konwencję w nawiasie.

Nazwa kolumny bierze się z `DriveTelemetry.Header`, czyli z tego samego odczytu, który
stał niżej dla podsumowania — przesuniętego w górę, **bez drugiego pisarza**.

## 3. Bramka sama zażądała trzech rzeczy, i każda była słuszna

Ta pozycja nie dopisała ani jednego testu w Pythonie, ale zmieniła trzy rzeczy
w bramce z 6.A14 — i **każdą z nich zgłosiła bramka**, nie ja:

**(a) Lista usprawiedliwień opustoszała i wpis został zdjęty.**

```
FAIL test_the_allow_list_is_exact_in_both_directions: usprawiedliwienie dla Compare
     obiecuje 2 wystapien golego Parse, a jest 0
```

Kontrola w obie strony, wprowadzona przy 6.A14 właśnie po to, żeby wpis nie przeżył
stanu, który opisuje.

**(b) Próg liczby miejsc rozbioru zszedł z 6 na 5** — i jest to **jedyna zapadka
w tym repozytorium, która kiedykolwiek zeszła w dół**, więc jej komentarz nosi powód,
nie samą cyfrę: dwa gołe `Parse` zamieniły się w **jeden** pomocnik z `TryParse`,
czyli 2 + 4 = 6 stało się 0 + 5 = 5. Spadek nie jest zluzowaniem — gołe `Parse` zniknęły
z pliku **całkiem**, co pilnuje osobny test; ten próg pilnuje wyłącznie tego, żeby
literówka we wzorcu nie dawała zera znalezisk i zielono.

**(c) Test listy usprawiedliwień przechodził bez ani jednej asercji.**

```
FAIL test_the_allow_list_is_exact_in_both_directions: przeszedł bez wykonania ani
     jednej asercji — cichy skip zamiast testu
```

Złapał to `assertion_gate` (#139), gdy lista opustoszała: pętla `for` po pustym
słowniku nie wykonuje ciała, więc test stał się cichym skipem. Przepisany na asercję
**bezwarunkową** — zbiór metod z gołym `Parse` ma być dokładnie zbiorem kluczy listy —
która działa również dla listy pustej i pilnuje obu kierunków naraz.

## 4. Jeden pisarz końcówki, dwa nagłówki

Bramka zapaliła się też na **czwartej** rzeczy i również miała rację:

```
FAIL test_one_writer_of_the_message: koncowka komunikatu tez ma miec jednego pisarza
```

Zdanie „«x» nie jest liczbą" pojawiło się w dwóch miejscach — w `NotANumber` (opcja)
i w `Cell` (komórka). Nagłówek **musi** być inny, bo zła komórka nie jest złą opcją,
ale zdanie o tym, że wartość nie jest liczbą, jest jedno: wydzielone do
`NieJestLiczba(text)`, wołane przez oba. Ta sama zasada, która przy 6.A20 wydzieliła
`Provenance`, a przy 6.A22 `Nieznana`.

Przy okazji licznik pisarzy dostał `_kod_bez_komentarzy`: docstring `NieJestLiczba`
**wyjaśnia** tę treść, więc licznik szukający zdania w surowym tekście widział dwóch
tam, gdzie jest jeden. Bramka zapalająca się na poprawnym tekście zostaje wyłączona,
nie naprawiona — ten sam warunek, który ma `test_runner_options.py`.

## 5. Kontrole negatywne — WYKONANE, pięć

```
KN-1  powrot do golego double.Parse w Compare
      Failed Zepsuta_komorka_nazywa_plik_wiersz_i_kolumne
      Failed Zepsuta_komorka_nazywa_zepsuty_plik_a_nie_pierwszy
      Failed Numer_i_nazwa_kolumny_ida_z_pozycji_w_wierszu
      Failed!  - Failed: 3, Passed: 575, Total: 578
      + bramka: FAIL test_no_option_value_reaches_a_bare_parse
                FAIL test_the_allow_list_is_exact_in_both_directions   (6/8)

KN-2  komunikat zawsze o args[1]
      Failed Zepsuta_komorka_nazywa_plik_wiersz_i_kolumne
      Failed!  - Failed: 1, Passed: 577, Total: 578
      bramka: 8/8 — kształt kodu jest ten sam, wywraca to dopiero test uruchamiający

KN-3  numer i nazwa kolumny zaszyte na pierwszej
      Failed Numer_i_nazwa_kolumny_ida_z_pozycji_w_wierszu
      Failed!  - Failed: 1, Passed: 577, Total: 578

KN-4  nieaktualny wpis wraca na liste usprawiedliwien
      FAIL test_the_allow_list_is_exact_in_both_directions: metody z golym Parse: [],
           a lista usprawiedliwien mowi ['Compare']                    (7/8)

KN-5  prog podniesiony na 6 (stan faktyczny 5)
      FAIL test_parse_site_count_is_above_the_floor: miejsc rozbioru liczby jest 5
           przy progu 6                                                (7/8)
```

**KN-2 mówi to samo, co KN-2 przy 6.A22, i dlatego jest tu wypisany**: bramka
czytająca tekst widzi **kształt**, nie zachowanie — wywrócił ją dopiero test
uruchamiający `Program.Main`. To argument, dla którego obie istnieją.

**KN-5 pilnuje progu w drugą stronę**: zapadka wyższa od stanu faktycznego pada przy
pierwszym przebiegu, więc nie da się jej „zostawić na zapas" po zamianie miejsca
rozbioru na inne.

## 6. Weryfikacja

```
$ dotnet test tests/Sim.Tests
Passed!  - Failed: 0, Passed: 578, Skipped: 0, Total: 578        (574 + 4)

$ python3 tools/tests/test_all.py
  RAZEM 72.267 s, 1852 testów, 99 modułów
kod: 0
```

Liczba testów Pythona **bez zmiany** (1852) — ta pozycja żadnego nie dopisuje, tylko
przepisuje trzy istniejące w bramce z 6.A14; cztery nowe są po stronie C#, gdzie
odmowa jest uruchamiana.

## 7. Czego świadomie nie zrobiono

- **Nie tknięto rozbioru nagłówka** (`left[0]` wobec `DriveTelemetry.Header`) — pole
  „Poza zakresem". Ma już własną odmowę i własny komunikat.
- **Nie tknięto tolerancji na brakującą kolumnę** — inna klasa błędu pliku, z własną
  odmową („zła liczba kolumn") w tej samej pętli.
- **Nie dopisano konwencji numeru wiersza do dwóch sąsiednich komunikatów.** Liczą ten
  sam indeks, więc są spójne z nowym; dopisanie im nawiasu byłoby zmianą tekstu poza
  zakresem tej pozycji. Zauważone, nie tknięte.

## 8. Co zauważone przy okazji, nietknięte

- **Odmowa różnej liczby wierszy i złej liczby kolumn wraca `return 1`, a nie wyjątkiem** —
  czyli te dwie nie idą przez wspólny handler i nie dostają przedrostka `BŁĄD:`,
  w odróżnieniu od nowej odmowy komórki i od wszystkiego, co ujednoliciła 6.A16.
  Widać to w wyjściu: `różna liczba wierszy: 5 vs 7` bez przedrostka. Nie jest to ta
  pozycja i nie dopisuję zadania z głowy — zapisane tutaj, żeby nie zginęło.
