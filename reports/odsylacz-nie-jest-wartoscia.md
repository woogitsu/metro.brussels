# Odsyłacz do sekcji czytany jako wartość stałej (6.D27)

**Zmierzone 07.09.2026 na commicie:** `609591b80d5dc6d664598eb23fd19efd3b031d5d`
(gałąź `claude/6d27-odsylacz-nie-wartosc`).

## 1. Bramka zapaliła się na zdaniu poprawnym

Przy 6.D26 pisałem w raporcie sekcję „czego nie zrobiono" i postawiłem zdanie:

> Nie tknięto `SUITE_RUNTIME_BUDGET_S` — §4. Decyzja o czułości bramki.

Odpowiedź zestawu:

```
FAIL test_every_constant_quoted_in_a_report_carries_the_value_from_the_code:
raporty podają inną wartość niż kod: `SUITE_RUNTIME_BUDGET_S` mówi 4, kod 150.0
```

Numer sekcji jest liczbą, a wzorzec bierze **pierwszą liczbę w 40 znakach po nazwie
stałej**. Zdanie było prawdziwe, bramka nie.

To nie jest usterka kosmetyczna i nie dlatego się nią zająłem, że mnie zdenerwowała.
**Bramka, która świeci na poprawnym tekście, zostaje wyłączona, nie poprawiona** —
tego samego zdania użyłem dzień wcześniej w `test_suite_runtime_budget.py` jako powodu
wycięcia własnego docstringa ze skanowania. Obejściem, które wtedy zastosowałem, było
przepisanie **zdania**, nie naprawienie przyrządu; przy trzecim takim zdaniu ktoś
skreśli test.

## 2. Ile tego już było — i dlaczego przechodziło

```
twierdzen w sumie:                       82
z tego z odsylaczem w czlonie miedzy:
  §          3   nazwa-zajeta-drugi-raz.md:63  '`MIN_RADIUS_M` znika przy okazji — kolizja z §1'
                 nazwa-zajeta-drugi-raz.md:172 '`LOCATION_STATION`** — §6'
                 nazwa-zajeta-drugi-raz.md:176 '`TOLERANCE_M`** — §5'
```

Trzy wiersze **mojego własnego raportu z tego samego dnia** miały już ten kształt.
Przechodziły **wyłącznie przypadkiem** — żadna z tych trzech stałych nie trafia do
słownika wartości:

```
MIN_RADIUS_M             -> (nie ma w slowniku)   # usunieta przy 6.B25
LOCATION_STATION         -> (nie ma w slowniku)   # wartosc napisowa
TOLERANCE_M              -> (nie ma w slowniku)   # trzy definicje, dwie wartosci
SUITE_RUNTIME_BUDGET_S   -> '150.0'               # jednoznaczna -> zapalila sie
```

Różnica między zdaniem, które przeszło, i zdaniem, które padło, nie leży więc w zdaniu.
Leży w tym, czy stała obok akurat jest jednoznaczną liczbą.

## 3. `#` doszło z pomiaru, nie z przewidywania

Zwężenie obejmuje `§` **i** `#`. Drugiego nie dopisałem „na przyszłość":

```
$ # wiersze raportow z nazwa stalej I odsylaczem #NNN
wierszy: 4
   kolejka-uzupelnienie.md:42  Ten sam mechanizm złapał już raz `MINIMUM_DOCUMENTED_ITEMS`:
                               sprzężenie, które #274
```

To zdanie jest przepuszczane **dzisiaj** tylko dlatego, że między nazwą a `#274` stoi
przecinek — a przecinek był wykluczony wcześniej, z całkiem innego powodu (tabele
odwzorowań). Kształt istnieje w drzewie i jest o jeden przecinek od zapalenia bramki.

## 4. Cena zwężenia, powiedziana wprost

Zdanie „`STAŁA` (§4) to 30,0" przestaje być twierdzeniem, więc rozjazd **w nim**
byłby przemilczany. To ten sam wybór, który podjęto przy przecinku i strzałce, i ta
sama asymetria: przemilczane twierdzenie łapie próg `MINIMUM_CLAIMS` (bramka odmawia,
gdy twierdzeń jest za mało), a fałszywy alarm łapie tylko czyjaś cierpliwość.

Po zwężeniu bramka sprawdza **15** twierdzeń przy progu 10 — czyli zwężenie nie
zbliżyło się do granicy, przy której przestałaby cokolwiek mierzyć.

## 5. Kontrole negatywne — WYKONANE

```
KN-1  zwezenie zdjete (powrot do wzorca bez § i #)
      FAIL test_a_section_reference_next_to_a_constant_does_not_fail_the_gate:
      poprawne zdanie z odsylaczem uznane za rozjazd
      FAIL test_the_claim_pattern_takes_values_and_leaves_mapping_tables_alone

KN-2  prawdziwy rozjazd w raporcie (kopia `reports/`, dopisana bledna wartosc)
      stala uzyta w kontroli: MINIMUM_CLAIMS = 10
      rozjazdow znalezionych: 1
          ('MINIMUM_CLAIMS', '99999', '10')
```

**KN-2 jest tu ważniejsza od KN-1.** KN-1 dowodzi, że nowy test rozpoznaje usterkę,
którą naprawia. KN-2 dowodzi, że zwężenie **nie zjadło tego, po co ta bramka
istnieje** — bo najprostszym sposobem uciszenia fałszywego alarmu jest zwężenie
wzorca tak, żeby nie łapał już niczego, i taka zmiana byłaby zielona bez KN-2.

Ta sama para stoi też **w treści testu** i chodzi przy każdym przebiegu: zdanie
poprawne z `§`, zdanie poprawne z `#`, zdanie z prawdziwym rozjazdem (musi zostać
rozjazdem) i zdanie z właściwą wartością.

## 5a. Bramka złapała moje zdanie w raporcie o niej samej — i miała rację

Pierwsza wersja §7 tego pliku brzmiała tak — cytat stoi w bloku, bo blok jest w tej
bramce z definicji cytatem, nie twierdzeniem:

```
**Nie ruszono `MINIMUM_CLAIMS`.** 15 przy progu 10 — zapas jest, a próg jest bramką
na martwy wzorzec, nie na liczbę raportów.
```

Odpowiedź zestawu:

```
FAIL test_every_constant_quoted_in_a_report_carries_the_value_from_the_code:
raporty podają inną wartość niż kod:
['odsylacz-nie-jest-wartoscia.md:132: `MINIMUM_CLAIMS` mówi 15, kod 10']
```

**To jest trafienie prawdziwe, nie fałszywy alarm** — i różnica jest dokładnie tą,
o której jest ta pozycja. Tamta liczba **nie** była odsyłaczem: stała zaraz za nazwą
stałej, w miejscu, w którym raporty tego repozytorium podają wartość. Czytający miał prawo przeczytać ją jako `MINIMUM_CLAIMS = 15`, bo
sam napisałem, że taka jest konwencja. Zdanie było **niejasne**, nie bramka.

Poprawione zostało zdanie. Warto to zapisać z dwóch powodów: bo pokazuje, że zwężenie
z §4 nie uciszyło bramki tam, gdzie ma mówić, i bo dwa akapity wyżej naprawiam usterkę
polegającą na tym, że przy 6.D26 poprawiłem zdanie zamiast przyrządu. Tym razem
poprawka zdania jest właściwa — i różnicę między jednym a drugim przypadkiem można
wskazać: tam liczba była numerem sekcji, tu jest liczbą w miejscu wartości.

## 6. Weryfikacja

```
$ python3 tools/tests/test_report_claims.py
  6/6 przeszło
kod: 0
```

Wzorzec, oba kierunki, na zdaniach wziętych z prawdziwych raportów:

```
odsylacz do sekcji   -> []
odsylacz do PR       -> []
prawdziwe: obok      -> [('M7_WIDTH_M', ' ', '2,70')]
prawdziwe: rownosc   -> [('SLAB_GROWTH_STEPS', ' = ', '6')]
prawdziwe: dwukr.    -> [('PARALLEL_M', ' jest granica wlacznie: ', '30,0')]
prawdziwe: nawias    -> [('RUNNING_TUNNEL_MAX_M', ' (', '15,0')]
```

Wszystkie cztery postacie, w których raporty naprawdę podają wartość, przechodzą
nietknięte. Dopisany jest też przypadek odwrotny — `` `M7_WIDTH_M` 2,70 — szerzej
w §3 `` — bo sama obecność `§` w wierszu nie może unieważniać twierdzenia stojącego
**przed** nim.

## 7. Czego świadomie nie zrobiono

- **Nie tknięto `pkt`, `rozdz.`, `str.`** — pomiar §2 pokazuje **zero** wystąpień
  w tym drzewie. Wykluczanie form, których nie ma, jest zgadywaniem zasięgu, a każda
  wykluczona forma zwęża bramkę o twierdzenia, których już nie sprawdzi.
- **Nie przepisano trzech zdań z §2.** Są poprawne. Poprawianie zdań było właśnie tym
  obejściem, które ta pozycja usuwa.
- **Nie ruszono progu liczby twierdzeń** (stała `MINIMUM_CLAIMS`, wartość jak w §4).
  Zapas jest, a ten próg jest bramką na martwy wzorzec, nie na liczbę raportów.
- **Nie rozbierano markdownu na drzewo** — pole „Poza zakresem". To jest bramka na
  tekst i taka zostaje.
