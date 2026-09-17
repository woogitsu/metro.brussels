# 6.D254 — klasa zapadki jest twierdzeniem o zachowaniu i nikt go dotąd nie sprawdził

**Data:** 17.09.2026 · **Gałąź:** `claude/6d254-klasa-zapadki` · **Baza:** `84ad273`

## 1. Co twierdzi rejestr i czego nigdy nie zmierzono

`tools/tests/test_tree_walks.py` trzyma `ZAPADKI` — 63 stałe progowe, każda z klasą.
Klasa jest **twierdzeniem o zachowaniu**: co się stanie, gdy ktoś ruszy zapadkę
w zakazaną stronę (`MAX_` wolno tylko obniżać, `MIN_`/`MINIMUM_` tylko podnosić).

| klasa | twierdzi |
|---|---|
| `przybita` | ruch o **jeden** zapala czerwień |
| `czesciowa` | ruch o jeden przechodzi, **daleki** zapala |
| `wolna` | **żaden** ruch nie zapala niczego |
| `poza skanem` | klasyfikator nic nie widzi, klasa nie twierdzi nic |

Klasę wylicza `klasa_zapadki` z **kształtu porównania** w drzewie. Do 17.09.2026
nikt nie postawił żadnego z tych 63 twierdzeń przed zachowaniem.

## 2. Pomiar

Każda zapadka ruszona w zakazaną stronę, uruchomione moduły, które nazwę widzą,
plik przywrócony. Przy każdej podmianie asercja, że mutacja **weszła** — bez niej
mutacja będąca no-opem jest nieodróżnialna od przejścia. `__pycache__` pod `tools/`
czyszczony przed każdym przebiegiem (6.D102).

Trzy ruchy: o **jeden**, o **ćwierć wartości** i **skrajny** (`MIN_` na zero,
`MAX_` na `+1000`). Trzeci doszedł, bo ruch o ćwierć nie sprawdza tego, co twierdzi
klasa `wolna`: przy podłodze 263 zejście do 198 mówi tylko, że zapas jest większy
niż ćwierć.

**Wynik: 63 z 63 zgodne — ani jedna klasa nie upadła.** Treścią tej pozycji jest to,
co wyszło zamiast rozbieżności, i w obu wypadkach jest to zdanie o tym, czego klasa
NIE mówi.

**Ten akapit jest przepisany, a nie dopisany obok, i miałem tu po drodze błąd.**
Po pierwszym przebiegu zapisałem, że dwie z trzech zapadek `czesciowa` upadły — bo
ruch o ćwierć wartości ich nie zapalił. Zapalił ruch dalszy. Klasa mówi „ruch o jeden
przechodzi, **daleki** zapala" i nie mówi, jak daleki, więc mój werdykt „upadła"
był werdyktem o **kroku, który wybrałem**, a nie o zapadce. Zwrócił mi na to uwagę
przebieg kontroli przyrządu; sprawdziłem granicę zapłonu własną ręką i zdanie
poniżej jest tym, co wyszło.

## 3. Klasa `czesciowa` się broni, ale nie mówi, o jakiej odległości mówi

| zapadka | wartość | pada przy | odległość zapłonu | czym jest strażnik |
|---|---|---|---|---|
| `MINIMUM_SUPPORTED_MAJOR` | 10 | **7** | **3** | `tfm_major('net8.0')` = 8, czyli prawdziwa wielkość z drzewa |
| `MINIMUM_POWODU` | 120 | **7** | **113** | napis `"bo tak"` z kontroli przyrządu, długość 7 |
| `MINIMUM_DOCUMENTED_ITEMS` | 6 | **0** | **6** (cały zakres) | warunek o KSZTAŁCIE stałej `0 < próg < próg doby pracy` |

Rzeczywiste wyjście, po jednym kroku aż do granicy:

```
MINIMUM_SUPPORTED_MAJOR=9  -> KOD=0   51/51 przeszło
MINIMUM_SUPPORTED_MAJOR=7  -> KOD=1   50/51 przeszło
   FAIL test_parsers_reject_what_they_should

MINIMUM_POWODU=119 -> KOD=0   43/43 przeszło
MINIMUM_POWODU=90  -> KOD=0   43/43 przeszło
MINIMUM_POWODU=8   -> KOD=0   43/43 przeszło
MINIMUM_POWODU=7   -> KOD=1   42/43 przeszło
   FAIL test_kazda_poprawka_zapisu_wykonanego_niesie_date_i_powod: [('X', '01.01.2026', ' bo tak')]

MINIMUM_DOCUMENTED_ITEMS=5 -> KOD=0   36/36 przeszło
MINIMUM_DOCUMENTED_ITEMS=3 -> KOD=0   36/36 przeszło
MINIMUM_DOCUMENTED_ITEMS=1 -> KOD=0   36/36 przeszło
MINIMUM_DOCUMENTED_ITEMS=0 -> KOD=1   35/36 przeszło
   FAIL test_the_ratchet_cannot_be_set_above_what_it_guards: podłoga zapasu stoi poza przedziałem
```

**Wszystkie trzy zachowują się zgodnie z klasą.** Wynikiem jest więc nie upadek klasy,
tylko jej **niesprawdzalność w praktyce**: odległość zapłonu wynosi od **3** do **113**
i klasa nie mówi o niej nic. Przyrząd z krokiem proporcjonalnym (ćwierć wartości)
wystawia dla tej jednej klasy **dwa różne werdykty** — `czesciowa` dla pierwszej
zapadki i `wolna` dla dwóch pozostałych — a różnicą jest wyłącznie to, jak duży krok
ktoś wybrał. Dlatego odległość jest odtąd **zapisana** w `ODLEGLOSC_ZAPLONU_CZESCIOWYCH`
i porównywana z rejestrem w obie strony, a nie domyślana przy każdym pomiarze.

**Do czego to prowadzi w treści, a nie tylko w metodzie:** przy dwóch z trzech
strażnikiem okazuje się **atrapa z kontroli przyrządu**, a nie drzewo — napis
`"bo tak"` i warunek o kształcie stałej. Klasa `czesciowa` mówi „strażnik mierzy INNĄ
populację" i ma rację; tyle że tą inną populacją jest wejście syntetyczne, więc zapadka
przejeżdża cały swój legalny zakres, zanim cokolwiek drgnie.

## 4. Czterdzieści z czterdziestu dwóch `wolna` to tautologia, nie pomiar

To jest drugi wynik pozycji i nie było go w jej opisie.

Zapadka używana wyłącznie jako prawa strona **jednej** podłogi `assert len(X) >= PRÓG`
jest `wolna` z **arytmetyki**: `len(X) >= 0` zachodzi przy każdej zawartości
repozytorium — także przy czytniku oślepionym do zera, czyli przy dokładnie tej
awarii, przed którą ta podłoga ma bronić (6.D27). Mutacja takiej zapadki nie
rozstrzyga niczego; jej jedyna treść to „nazwa nie jest użyta nigdzie indziej".

Czytnik `wolne_rozstrzygalne_pomiarem` liczy to z drzewa, a nie z ręki:

```
WOLNYCH w rejestrze: 42
PRZESADZONYCH ksztaltem: 40
ROZSTRZYGALNYCH pomiarem: 2
   MAX_ODCISKOW_W_RAPORCIE   porownan=1 innych uzyc=3
   MINIMUM_CLAIMS            porownan=2 innych uzyc=1
```

Obie „rozstrzygalne" zmierzono i obie wyszły `wolna`. `MAX_ODCISKOW_W_RAPORCIE`
jest tu pouczający: dwa testy budują wejście jako `range(PRÓG)` i `range(PRÓG + 1)`,
czyli **parę na granicy**, kształt najmocniejszy z możliwych — ale granica jedzie
razem z progiem, więc 8 → 1008 daje `133/133` i nie zapala nic.

## 5. Bramka klas nie milczy — mówi nieprawdę

Pole „Weryfikacja" pozycji zapowiadało: przepisanie jednej zapadki `wolna` na postać
`if populacja < PRÓG` ma zapalić bramkę klas, a „dziś przechodzi, i to jest ta dziura".
**Przewidziałem inaczej i zapisałem to przed przebiegiem:** bramka zapali się, bo
klasyfikator czyta relację od strony stałej, a `if len(x) < PRÓG` daje dla `MIN_`
kształt straży. Dziurą miała być treść komunikatu, nie cisza.

Mutacja: `assert len(calls) >= MINIMUM_CALLERS` przepisane na
`if len(calls) < MINIMUM_CALLERS: raise AssertionError(...)`. Znaczenie identyczne.

```
FAIL test_kazda_zapadka_ma_klase_i_klasa_zgadza_sie_z_drzewem: zapadka zmieniła klasę
(nazwa, było, jest): [('MINIMUM_CALLERS', 'wolna', 'czesciowa')] — zmiana W STRONĘ
`wolna` znaczy, że komuś ubył strażnik; w stronę `przybita`, że doszedł i wpis trzeba
poprawić
  16/17 przeszło
KOD=1
```

Żaden strażnik nie doszedł — doszła inna **pisownia tego samego zdania**. A komunikat
każe „poprawić wpis", czyli wpisać do rejestru straż, której nie ma. To jest dosłownie
tytuł pozycji, tylko wejściem od drugiej strony, niż zakładał jej autor.

## 6. Cytat wartości w raporcie nie jest strażą — zmierzone po obu stronach commita

Podejrzenie było takie, że mutacja w drzewie roboczym **sama wyłącza** jedyną bramkę
międzymodułową, która mogłaby ją złapać: `data_stalej` z `test_report_claims.py`
zwraca `TERAZ`, gdy plik jest brudny i wartość różni się od `HEAD`, a twierdzenie
raportu starszego niż stała jest zwalniane (6.D108). Gdyby tak było, cały pomiar
`wolna` byłby o tyle słabszy.

Nie zostało to przy tym — zostało **zmierzone po drugiej stronie commita**.
`MINIMUM_CLAIMS` obniżone 10 → 9 i **zacommitowane** (drzewo czyste, `git status`
puste, `data_stalej` czyta historię, a nie drzewo):

```
29/29 przeszło
KOD=0
```

Stała jest cytowana w dwóch raportach (`reports/odsylacz-nie-jest-wartoscia.md:87`,
`reports/report-claims-audit.md:81`) i mimo to obniżenie przechodzi. Zwolnienie nie
bierze się więc z brudnego drzewa, tylko z porównania dat — a stała ruszona **dziś**
jest nowsza od każdego raportu, który ją cytuje. **Cytat w `reports/` nie jest strażą
zapadki w żadnym układzie.** To nie jest usterka 6.D108, tylko jego zaprojektowane
działanie; jest to natomiast granica tego, co klasa `wolna` może znaczyć.

## 7. Bramki i kontrole negatywne

Trzy nowe bramki w `tools/tests/test_tree_walks.py`. Klas **nie ruszam** — pole
„Poza zakresem" zabrania tego wprost; pozycja liczy i nazywa.

| kontrola | przewidziane | zmierzone |
|---|---|---|
| KN-2 zdjęcie wpisu o zapadce z drugim użyciem | czerwone, z nazwą i miejscami | `MINIMUM_CLAIMS` + trzy wiersze z rolami, **19/20** |
| KN-3 wpis o zapadce bez drugiego użycia | czerwone, gałąź „zniknięte" | `['MIN_NEEDLES']`, **19/20** |
| KN-4 zdjęcie zapadki z listy zmierzonych odległości zapłonu | czerwone, nazwie brakującą | `['MINIMUM_POWODU']`, **19/20** — ale patrz niżej |
| KN-5 kontrola przyrządu na wejściu syntetycznym | czytnik widzi cztery role osobno | zielone |
| KN-6 próg zapłonu podniesiony do wartości zapadki | czerwone, bo to znaczy czerwień już dziś | `zapłon przy 120, a wartość w drzewie 120`, **19/20** |

**KN-4 przy pierwszym podejściu wyszło ZIELONE i było to nieprawdą.** Kotwica końcowa
cięcia trafiła w `MINIMUM_DOCUMENTED_ITEMS` stojące w **rejestrze `ZAPADKI`**,
czternaście tysięcy znaków wyżej niż kotwica początkowa (`i=25211, j=11820`), więc
cięcie nie usunęło wpisu, tylko powieliło fragment pliku. Słownik został nietknięty,
a `20/20 przeszło` mówiło o drzewie **bez mutacji**. Złapała to asercja „mutacja
ZASTOSOWANA", nie oczy. Zostawiam ten przebieg w raporcie zamiast podmienić go po
cichu na udany: to trzeci raz tego samego kształtu w ciągu doby, a kształt brzmi
**mutacja, która się nie zastosowała, wygląda identycznie jak bramka, która przepuszcza**.

KN-5 jest obowiązkowa, nie ozdobna: bez niej literówka we wzorcu dałaby zero
„rozstrzygalnych" i zieleń — stan **nieodróżnialny** od drzewa, w którym każda
zapadka jest jednostronną podłogą. Sprawdza cztery role osobno, bo trzy decydują
o podziale: nazwa w `Assert.msg` **nie** liczy się jako użycie (jest liczona wyłącznie
przy padzie), a `moduł.NAZWA` **liczy się** — i to jest cały powód, dla którego ten
czytnik stoi obok `_porownania_zapadek`, który widzi wyłącznie `ast.Name`.

## 8. Czego NIE zrobiono

- **Nie poprawiono żadnej klasy w `ZAPADKI` — i po pomiarze nie ma czego poprawiać.**
  Wszystkie 63 klasy zgadzają się z zachowaniem. To, że dwie `czesciowa` stoją na
  strażniku mierzącym atrapę z kontroli przyrządu, jest zdaniem o tych BRAMKACH,
  a nie o wpisie w rejestrze, i poprawia się je po stronie bramki, nie klasy.
- **Nie ruszono `klasa_zapadki`**, choć wiadomo już, że czyta pisownię, nie treść.
  Poprawka polaryzacji to zmiana bramki, czyli osobna pozycja z sześcioma polami.
- **Nie ruszono `ZAPADEK_RAZEM` ani żadnej wartości progu** — też poza zakresem.
- **Nie rozszerzono selektora modułów** o bramki czytające liczby ze źródeł regexem
  (`test_report_claims.py`). Dla trzech zapadek pomiar tej drogi nie uruchomił;
  że i tak by nie zapaliła, wynika z §6, ale dla nich jest to wywód, nie pomiar.

## 9. Co zauważone przy okazji, nietknięte

- **Trzynaście stałych o kształcie zapadki leży poza rejestrem i rejestr nie mówi
  o nich nawet „poza skanem".** Są definiowane poza `tools/tests/` i wchodzą do testów
  wyłącznie jako `moduł.NAZWA` — m.in. `MAX_GAP_M` (dziewięć użyć w
  `test_tunnel_manifest.py`), `MAX_MARKS`, `MIN_SENSIBLE_STEP_M`, `MAX_ECEF_RESIDUAL_M`.
  Część z nich jest przybita równością mocniej niż niejedna pozycja rejestru.
- **Komentarz `#:` przy podłogach w `test_dead_constants_csharp.py` niesie liczby
  o dobę starsze niż docstring kilkanaście wierszy niżej** (`const` 304 / `static
  readonly` 85 / razem 389 obok „dziś 44 z 390") i nikt tego nie porównuje.
- **`reports/6d225-dziura-interpolacji.md:166` przypisuje podłodze deklaracji C#
  wartość dwustu, a w drzewie stoi dziś trzysta trzydzieści** — nieprawdziwe wobec
  kodu już dziś, bez żadnej mutacji, i zwolnione datowaniem 6.D108. Zgodne z regułą,
  ale warte osobnego spojrzenia. Liczby stoją tu SŁOWNIE i nazwa stałej nie pada
  obok cyfry, bo kształt `NAZWA = N` w raporcie jest czytany przez
  `test_report_claims.py` jako TWIERDZENIE AUTORA o stanie drzewa — ten akapit
  zapalił tę bramkę przy pierwszym przebiegu i to jest jego własna historia.
- **Czwarta klasa prosi się sama:** „podłoga, której ruch w dół jest logicznie
  bezskutkowy" to co innego niż „zapadka bez strażnika", a rejestr zapisuje obie
  słowem `wolna`. Czterdzieści pozycji na czterdzieści dwie to nie margines.
