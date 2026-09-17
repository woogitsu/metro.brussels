# 6.D262 — dziury nie było, a przyrząd znalazł dwanaście progów, których nie pilnuje nic

**Data:** 17.09.2026 · **Gałąź:** `claude/6d262-o-krok` · **Baza:** `b2c1bda`

## 1. Teza pozycji jest NIEPRAWDZIWA i pozycję tę napisałem ja, tej samej doby

Blok 6.D262 mówił, w polu „Weryfikacja":

> Kontrola negatywna: zdjęcie z zapadki jej JEDYNEJ asercji wprost, tak żeby został
> sam filtr, ma zapalić nową bramkę — **dziś przestawia klasę na `poza skanem`
> po cichu i to jest ta dziura.**

Ostatnie zdanie jest nieprawdą. Zmierzone przez wykonanie tej samej mutacji na
drzewie SPRZED tej pozycji (baza 6.D261, `MINIMUM_POWODU` pozbawione obu asercji
wprost, zostaje sam filtr):

```
DRZEWO SPRZED 6.D262:
FAIL test_kazda_zapadka_ma_klase_i_klasa_zgadza_sie_z_drzewem:
  zapadka zmieniła klasę (nazwa, było, jest):
  [('MINIMUM_POWODU', 'czesciowa', 'poza skanem')]
  20/21 przeszło
```

**Bramka klas łapała to od początku**, bo porównuje klasę z rejestrem, a klasa
się zmienia. Napisałem „po cichu", nie sprawdziwszy — i jest to dokładnie ten
kształt, który ta seria pozycji tropi: zdanie o stanie repozytorium, którego
nikt nie zmierzył.

## 2. Co pozycja jednak dała

### Obie liczby z pola „Wyjście"

Rozkład par `(twierdzących, odłożonych)` na 69 zapadkach:

| para | zapadek |
|---|---|
| (0, 0) | 1 |
| (0, 1) | 1 |
| (1, 0) | 48 |
| (2, 0) | 11 |
| (2, 1) | 1 |
| (3, 0) | 2 |
| (4, 0) | 3 |
| (12, 0) | 1 |
| (13, 1) | 1 |

**Czterdzieści osiem z sześćdziesięciu dziewięciu ma dokładnie jedno twierdzące
porównanie.** Liczba ta nie jest jednak alarmem, tylko kształtem rejestru: każda
nowa zapadka **rodzi się** w tym stanie, bo powstaje jako prawa strona jednej
podłogi. Dlatego stoi przy niej podłoga, a nie równość — równość czerwieniałaby
przy każdej nowej pozycji, czyli na pracy poprawnej (6.D27).

### Stan, którego pozycja szukała, istnieje DOKŁADNIE RAZ

Zapadki z porównaniem **odłożonym** są trzy, i tylko jedna ma zero twierdzących:

* zapadka odcisków w raporcie przeglądu mutacji — **zero** twierdzących, jedno
  odłożone; jedyne jej porównanie to gałąź bez `raise`. **To jest ten stan**,
  i jest on dziś jedyny;
* podłoga długości powodu w polach zadań — **dwa** twierdzące obok jednego
  odłożonego (filtr wyrażenia listowego);
* próg zapasu kolejki — **trzynaście** twierdzących obok jednego odłożonego,
  czyli najdalej od granicy z całego rejestru.

Zbiór ten stoi **przybity co do nazwy i liczby**, porównywany w obie strony (6.D243).

### Niezmiennik niezależny od klasy

Nowa asercja mówi: **zapadka bez ani jednego twierdzącego porównania musi mieć klasę
`poza skanem`**. Jest to warunek mocniejszy niż porównanie z rejestrem, bo nie pyta,
co w rejestrze stoi, tylko czy rejestr twierdzi o zapadce coś, czego nie mierzy nic.
Bramka klas łapie zmianę; ta łapie **niespójność**.

## 3. Znalezisko: dwanaście progów, których nie pilnuje NIC

**Znalazła je kontrola przyrządu, a nie pomiar, który ta pozycja planowała.**

Kontrola miała sprawdzić, że dwa czytniki zgadzają się co do drzewa. Padła przy
pierwszym przebiegu i wskazała dwanaście nazw:

```
MAX_AXIS_LENGTH_M   MAX_ECEF_RESIDUAL_M   MAX_GAP_M          MAX_MARKS
MAX_PLAUSIBLE_VERTICES   MAX_SEED_WAYS    MAX_TWIST_DEG      MINIMUM_ARTEFACT_BYTES
MIN_AXIS_POINTS     MIN_CENTERLINE_POINTS MIN_PLAUSIBLE_VERTICES  MIN_SENSIBLE_STEP_M
```

Wszystkie mają kształt zapadki, wszystkie są porównywane **w `tools/tests/`**, czyli
wewnątrz zasięgu skanu — ale docierają tam przez `moduł.NAZWA`, a `_porownania_zapadek`
czyta po stronie stałej wyłącznie `ast.Name`. Są więc w **żadnym** rejestrze, nie mają
klasy i nie pilnuje ich nic.

6.D254 nazwało tę ślepotę, ale na dwóch nazwach, które w rejestrze **już były**. Tu
widać jej pełny koszt: dwanaście progów całkowicie poza rejestrem, wśród nich
`MAX_MARKS`, `MAX_GAP_M` i `MIN_AXIS_POINTS` — czyli progi geometrii toru, nie
narzędziowe drobiazgi.

Dwanaście stałych mieszka w **siedmiu plikach** pod `tools/track/`
i `tools/blender/` — sprawdzone wyszukaniem każdej z osobna, bo pierwsza wersja
tego zdania nazywała katalog `tools/detail/`, którego w drzewie **nie ma**, i złapała
to bramka na nazwy katalogów w polach zadań.

**Zbiór jest PRZYBITY, a nie naprawiony.** Naprawa znaczy rozszerzenie rejestru
o stałe spoza `tools/tests/`, a to jest decyzja o **zasięgu** `ZAPADKI`, nie pomiar.
Zapisane jako pozycja **6.D266**; dopóki tam stoi, bramka pilnuje, żeby lista nie
rosła po cichu, i żeby żadna z dwunastu nie trafiła do rejestru bez zdjęcia wpisu.

## 4. Kontrole negatywne — przewidywania spisane PRZED przebiegami

Mutacje na KOPII drzewa (§4.6), `__pycache__` czyszczony (6.D102), każda z asercją,
że **wylądowała**.

### KN — zdjęcie zapadce jej jedynych asercji wprost

Przewidywanie: bramka czerwona, zapadka w zbiorze bez twierdzących.

```
MUTACJA: dwa wiersze `MINIMUM_POWODU` zamienione na literał, zostaje sam filtr

FAIL test_ile_zapadek_jest_O_KROK_od_wypadniecia_z_klasyfikacji:
  zapadka bez ani jednego TWIERDZACEGO porownania ma klase inna niz `poza skanem`:
  [('MINIMUM_POWODU', 'czesciowa')] — rejestr mowi o niej cos, czego nie mierzy nic
FAIL test_kazda_zapadka_ma_klase_i_klasa_zgadza_sie_z_drzewem:
  [('MINIMUM_POWODU', 'czesciowa', 'poza skanem')]
  21/23 przeszło
```

Zgodnie z przewidywaniem — ale **ta sama mutacja na drzewie sprzed tej pozycji też
kończy się czerwienią** (§1), więc nowa bramka nie zamyka dziury, tylko dokłada
diagnozę.

### Kontrola przyrządu — dwa czytniki, jedno drzewo

To ona znalazła dwanaście progów z §3. Sprawdza trzy rzeczy: że różnica między
licznikiem a klasyfikatorem jest **dokładnie** znanym zbiorem, że idzie **tylko
w jedną stronę** (licznik czyta ściśle więcej kształtów), i że żaden z dwunastu
progów nie trafił po cichu do rejestru.

Padła też drugi raz, wcześniej: pierwsza wersja licznika czytała `ast.walk` po całym
węźle porównania i liczyła przez to `assert len(x) <= PRÓG + 1` oraz `range(PRÓG)`
w argumencie — czyli więcej, niż widzi klasyfikator. Definicja członu została
**pożyczona** z `_porownania_zapadek`, a nie napisana drugi raz (6.D213).

## 5. Weryfikacja

```
python3 tools/tests/test_all.py test_tree_walks.py
  23/23 przeszło

python3 tools/tests/test_all.py
  2584/2584 przeszło
  RAZEM 252.750 s, 2584 testów, 131 modułów
```

## 6. Zauważone, nietknięte

- **Nie naprawiono ślepoty na `moduł.NAZWA`** — to jest zmiana zasięgu rejestru
  i decyzja, nie pomiar. Pozycja 6.D266.
- **Nie ruszono żadnej z dwunastu stałych** — leżą w `tools/track/` i `tools/detail/`,
  poza zakresem tej pozycji.
- **Podłoga na „o krok" stoi na 40 przy zmierzonych 48** — zapas jest tu potrzebny
  nie na wzrost, tylko na spadek: zapadka przechodząca z jednym porównaniem do dwóch
  (bo ktoś dopisał strażnika) **opuszcza** ten zbiór, więc liczba może maleć przy
  pracy poprawnej.
