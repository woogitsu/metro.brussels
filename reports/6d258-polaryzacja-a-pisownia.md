# 6.D258 — klasyfikator zapadek czytał PISOWNIĘ; głowy były dwie, nie jedna

**Data:** 17.09.2026 · **Gałąź:** `claude/6d258-polaryzacja-porownania` · **Baza:** `144a77a` (pomiar wykonany na `107d602`, czyli tej samej treści przed scaleniem #659)

## 1. Co twierdziła pozycja i co się od niej różni

Pozycja opisywała JEDNĄ bramkę: przepisanie `assert len(calls) >= MINIMUM_CALLERS`
na `if len(calls) < MINIMUM_CALLERS: raise AssertionError(...)` — zdanie o identycznym
znaczeniu — przestawiało klasę z `wolna` na `czesciowa` i zapalało
`test_kazda_zapadka_ma_klase_i_klasa_zgadza_sie_z_drzewem` komunikatem „doszedł
strażnik i wpis trzeba poprawić". Żaden strażnik nie dochodził.

Odtworzenie KN-1 na dzisiejszym drzewie pokazało, że bramki padają **dwie**:

```
18/20 przeszło

FAIL test_kazda_zapadka_ma_klase_i_klasa_zgadza_sie_z_drzewem:
  zapadka zmieniła klasę (nazwa, było, jest):
  [('MINIMUM_CALLERS', 'wolna', 'czesciowa')] — … doszedł i wpis trzeba poprawić
FAIL test_ktore_wolne_zapadki_sa_PRZESADZONE_ksztaltem_a_ktore_zmierzone:
  zapadka `wolna` dostała DRUGIE użycie:
  [('MINIMUM_CALLERS', [('test_platform_length_in_pipeline.py', 137, 'nosna'),
                        ('test_platform_length_in_pipeline.py', 140, 'inna')])]
```

Druga to **moja własna bramka z 6.D254**, napisana dobę wcześniej, i ma dokładnie ten
sam defekt w innym czytniku: `uzycia_zapadek` rozpoznaje komunikat wyłącznie jako
`ast.Assert.msg`, więc ten sam f-string przeniesiony do `raise AssertionError(...)`
przestaje być rolą `komunikat`, a staje się rolą `inna` — czyli „drugim użyciem",
o którym bramka mówi, że „werdykt przestał wynikać z kształtu". Nie przestał.
Zmieniła się pisownia.

**To jest treść tej pozycji, a nie przypis:** ten sam kształt usterki siedział
w dwóch czytnikach, a pozycja znała jeden. Gdyby poprawić tylko ten jeden, KN-1
nadal kończyłoby się czerwienią — i wyglądałoby to na niepowodzenie poprawki,
a nie na drugą głowę.

## 2. Ile jest czego w drzewie — pomiar przed poprawką

138 porównań `ast.Compare` niosących nazwę o kształcie zapadki, w czterech postaciach:

| postać zdania | ile | twierdzi? |
|---|---|---|
| `assert <cmp>` | 134 | tak, wprost |
| `assert not <cmp>` | 1 | tak, zaprzeczone |
| `if <cmp>:` bez `raise` w ciele | 2 | **nie** |
| filtr wyrażenia listowego | 1 | **nie** |
| `if <cmp>: … raise …` | **0** | tak, zaprzeczone |

Trzy nietwierdzące z nazwami:

```
mutation_sweep.py:1427   MAX_ODCISKOW_W_RAPORCIE   if …: wybór SZEROKOŚCI TABELI
test_backlog.py:1090     MINIMUM_READY_ITEMS       if …: wybór, KTÓRĄ asercję puścić
test_field_paths.py:1533 MINIMUM_POWODU            filtr zasilający `assert krotkie == []`
```

Ostatniej rubryki nie ma w drzewie ani razu — postać `if …: raise` istnieje wyłącznie
pod mutacją. Gałąź czytnika, która ją obsługuje, jest więc napisana po to, żeby
przepisanie asercji nie ruszało klasy, a nie dlatego, że coś tak dziś stoi.

## 3. Dlaczego „nie twierdzi nic", skoro dwa ostatnie kształty na wynik WPŁYWAJĄ

Wpływają. `MINIMUM_POWODU` w filtrze decyduje, co wpadnie do listy, którą asercja
dwa wiersze niżej porównuje z `[]`; `MINIMUM_READY_ITEMS` w gałęzi decyduje, która
z dwóch asercji się wykona. Ale **wpływają przez asercję stojącą DALEJ**, której
ten czytnik nie widzi i bez przejścia przepływu danych widzieć nie może.

Zaliczenie ich do strażników byłoby twierdzeniem mocniejszym niż pomiar: klasa
`przybita` znaczy „ruch o jeden PADA", a o gałęzi redakcyjnej tego nie wiadomo.
Przyrząd ma mówić o tym, co widzi — ten sam wybór co w 6.D254.

## 4. Jedyny werdykt, który poprawka rusza na dzisiejszym drzewie

```
PRZED:  przybitych 17, częściowych 3, WOLNYCH 42, poza skanem 1
PO:     przybitych 17, częściowych 3, WOLNYCH 41, poza skanem 2

ZMIENIONE: [('MAX_ODCISKOW_W_RAPORCIE', 'wolna', 'poza skanem')]
```

Jedyne porównanie tej zapadki to gałąź wybierająca szerokość tabeli, bez `raise`
w żadnej odnodze. Klasyfikator przestaje je widzieć, więc zapadka zostaje bez ani
jednego porównania — także bez **nośnego**. `wolna` mówiła „strażnika nie ma";
`poza skanem` mówi „nie ma też nośnego", i to drugie niesie prawdę, której pierwsze
nie niosło.

**Werdykt zachowania się nie zmienił** — pomiar mutacyjny z 6.D254 (8 → 1008 daje
133/133, bo granica `range(PRÓG + 1)` jedzie razem z progiem) zostaje w mocy. Zmieniła
się nazwa tego, co o zapadce wiadomo. Wpis wypadł z `ROZSTRZYGALNE_POMIAREM`, bo
tamten słownik opisuje wyłącznie klasę `wolna`; pomiar przeniesiony do komentarza
przy wpisie rejestru, żeby nie zginął razem ze słownikiem.

## 5. Klasa POZA_SKANEM ma od dziś DWA powody i każdy jest sprawdzany osobno

Bramka na tę klasę mówiła „jedyny taki dziś to `MIN_PATHS`" i sprawdzała jeden
kształt w drzewie. Członków jest dwóch, z różnych przyczyn:

| zapadka | powód | czy da się wciągnąć do skanu |
|---|---|---|
| `MIN_PATHS` | próg idzie do porównania **przez zmienną pętli** | tak, lepszym czytnikiem nazwy |
| `MAX_ODCISKOW_W_RAPORCIE` | jedyne porównanie **niczego nie twierdzi** | nie — nie ma czego czytać |

Lista nazw bez powodów byłaby napisem (6.D243), więc bramka jest **przepisana,
a nie dopisana obok**: sprawdza oba kształty w drzewie osobno, a drugi sprawdza
**polaryzacją**, a nie napisem — dopisanie `raise` do tamtej gałęzi ją zapali.

## 6. Komunikat: co dało się zrobić, a czego nie

Pole „Wyjście" żądało, żeby komunikat rozróżniał „zmieniła się TREŚĆ" od „zmieniła
się PISOWNIA". Komunikat twierdził dotąd PRZYCZYNĘ („doszedł strażnik"), a mierzył
wyłącznie klasę przed i po — i był nieprawdziwy w obie strony: przy przepisaniu
asercji mówił o strażniku, który nie doszedł, a o zmianie do `poza skanem`, dziś
możliwej, nie miał zdania w ogóle.

Nowy komunikat podaje **zmierzone miejsca i postacie** wszystkich porównań zapadki:

```
KN-b:  zapadka zmieniła klasę (nazwa, było, jest):
       [('MINIMUM_CALLERS', 'wolna', 'czesciowa')].
       Porownania tej zapadki w drzewie, z postacia zdania:
       {'MINIMUM_CALLERS': [('test_platform_length_in_pipeline.py', 137, 'wprost'),
                            ('test_platform_length_in_pipeline.py', 138, 'wprost')]}
```

Wiersz **nowy** znaczy, że zmieniła się treść; ten sam wiersz w **innej postaci**
znaczy, że zmieniła się pisownia.

**Czego bramka nie zrobi i to jest granica przyrządu, nie przeoczenie:** samego
rozstrzygnięcia nie postawi, bo do tego potrzebny byłby stan PRZED zmianą, a bramka
ma rejestr (klasę) i dzisiejsze drzewo. To ten sam kształt, który 6.D255 nazwało
czwartą nieprawdą nie do złapania. Zapisane w komunikacie wprost, żeby nikt nie
czytał milczenia jako rozstrzygnięcia.

## 7. Kontrole negatywne — przewidywania spisane PRZED przebiegami

Wszystkie mutacje na KOPII drzewa (§4.6), `__pycache__` czyszczony przed każdym
przebiegiem (6.D102), każda mutacja z asercją, że **wylądowała**.

### Kontrola przyrządu, syntetyczna — pięć postaci na drzewie próbnym

`test_czytnik_polaryzacji_widzi_ksztalt_ktory_ma_widziec`. Bez niej poprawka byłaby
nie do odróżnienia od czytnika, który po prostu przestał cokolwiek widzieć: taki
daje same `poza skanem` i **też** „nie zmienia klasy przy przepisaniu asercji".
To 6.D27 w czystej postaci, więc każda postać ma własny oczekiwany werdykt:

| postać | oczekiwane | wynik |
|---|---|---|
| `assert PRÓG <= len(x)` | `przybita` | zgodnie |
| `if len(x) > PRÓG: raise` | `przybita` | zgodnie |
| `if len(x) <= PRÓG: print(...)` | `poza skanem` | zgodnie |
| `assert not len(x) > PRÓG` | `przybita` | zgodnie |
| filtr `[x for x in l if len(x) < PRÓG]` | `poza skanem` | zgodnie |

Para pierwsza i druga jest treścią: **to samo zdanie dwoma sposobami musi dostać tę
samą klasę**. Przeszła za pierwszym przebiegiem.

### KN-1 — powtórzenie kontroli z 6.D254

Przewidywanie: **21/21, zielono**; `MINIMUM_CALLERS` zostaje `wolna`, bramka
`wolnych` też milczy.

```
MUTACJA WYLĄDOWAŁA: if=1 assert=0
  21/21 przeszło
```

Zgodnie z przewidywaniem, i obie głowy milczą — nie tylko ta, którą znała pozycja.

### KN-b — czy poprawka nie zamieniła bramki na milczącą

Dopisanie PRAWDZIWEGO strażnika `assert MINIMUM_CALLERS >= 2`.
Przewidywanie: klasa `wolna` → `czesciowa`, **czerwień**, komunikat z plikiem
i numerem wiersza.

```
MUTACJA WYLĄDOWAŁA: 1
  19/21 przeszło
FAIL test_kazda_zapadka_ma_klase_i_klasa_zgadza_sie_z_drzewem:
  [('MINIMUM_CALLERS', 'wolna', 'czesciowa')] … 137 'wprost', 138 'wprost'
FAIL test_ktore_wolne_zapadki_sa_PRZESADZONE_ksztaltem_a_ktore_zmierzone:
  [('MINIMUM_CALLERS', [(…, 137, 'nosna'), (…, 138, 'nosna')])]
```

Zgodnie z przewidywaniem. Obie bramki, które KN-1 uciszyło, zapalają się przy
prawdziwej zmianie treści — czyli uciszenie było wybiórcze, a nie globalne.

## 8. Weryfikacja

```
python3 tools/tests/test_all.py test_tree_walks.py
  21/21 przeszło

python3 tools/tests/test_all.py
  2572/2572 przeszło
  RAZEM 246.719 s, 2572 testów, 130 modułów
```

## 9. Zauważone, nietknięte

- `MINIMUM_READY_ITEMS` i `MINIMUM_POWODU` zachowały klasę mimo odłożenia po jednym
  porównaniu — obie mają dość asercji, żeby werdykt się nie ruszył. Gdyby któraś
  miała tylko to jedno, poprawka zmieniłaby werdykt na podstawie pomiaru, którego
  ten czytnik nie robi (przepływ danych do asercji stojącej dalej). Dziś to nie
  zachodzi; jest to warunek do sprawdzenia, gdy takie porównanie zostanie ostatnie.
- **Formę `if <cmp>: … else: raise` (wyjątek w ODNODZE, nie w ciele) napisałem
  najpierw źle i złapałem to przy pisaniu tego raportu, a nie bramką.** Pierwsza
  wersja czytnika oglądała wyłącznie `body`, więc takie zdanie dostawało werdykt
  „nie twierdzi nic" — a twierdzi, i to sam warunek, bez zaprzeczenia. W drzewie
  nie ma go ani razu, więc żadna liczba w tym raporcie by się nie ruszyła i usterka
  przeszlaby cały zestaw na zielono. Poprawione: `orelse` czytany na równi z `body`,
  z własnym przypadkiem w kontroli przyrządu (szósty). **Sama kontrola też złapała
  błąd, ale MÓJ, w niej samej:** pierwsza wersja przypadku stawiała dwa razy zdanie
  NOŚNE zamiast nośnego i strzegącego, więc żądała `przybita`, a czytnik słusznie
  dawał `wolna`. Zapis został poprawiony w fixture, nie w oczekiwaniu.
