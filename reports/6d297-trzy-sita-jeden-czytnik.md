# 6.D297 · Pamięć ścina moduł o 45 %, jest bezpieczna — a oczywista implementacja OŚLEPIA bramkę

**Data:** 19.09.2026 · **Gałąź:** `claude/sharp-ramanujan-jdr51o` · **Baza:** `4e2a151`

Trzy sita — `dystanse_pokrycia`, `pokrycie_dalekie` i `kruche_pokrycie` — wołają
`pozycje_pokrycia` osobno. 6.D284 zauważyło, że moduł urósł z 21,9 s przy dziewiętnastu
testach do 26,4 s przy dwudziestu jeden, i zapisało pytanie: **ile to kosztuje i czy
pamięć jest bezpieczna.**

---

## 1. Trzy liczby, których żądało pole „Wyjście"

```
testow w module: 21
wolan `pozycje_pokrycia` w jednym przebiegu modulu: 13
roznych par (katalog, korzen): 3
    9x  katalog=(domyslny)                     korzen=(domyslny)
    3x  katalog=/tmp/metro-wlosek-p45sixzk     korzen=/tmp/metro-wlosek-p45sixzk
    1x  katalog=/tmp/metro-pokrycie-jg5jafvn   korzen=/tmp/metro-pokrycie-jg5jafvn
```

| | przebieg 1 | przebieg 2 | przebieg 3 | średnia | rozrzut |
|---|---|---|---|---|---|
| **bez pamięci** | 27,94 s | 27,16 s | 28,08 s | 27,7 s | 0,92 s |
| **z pamięcią** | 15,33 s | 15,27 s | 15,22 s | 15,3 s | 0,11 s |

**Oszczędność: 12,4 s, czyli 45 %**, przy rozrzucie spadającym ośmiokrotnie.
Trzy przebiegi każdego wariantu, bo pozycja mierzy CZAS, a jedna liczba na maszynie
dzielonej nie jest pomiarem. Przebieg kontrolny po scaleniu bazy: **28,16 s** —
moduł jest między `bbb630a` a `4e2a151` bajtowo identyczny, więc liczby przenoszą się.

Liczby są **wyższe niż 26,4 s z 6.D284** i to nie jest regres: kontener tej sesji chodzi
wolniej od runnera (cały zestaw 340–350 s wobec około 126 s w dokumentach). Porównywalna
jest **różnica**, nie wartość bezwzględna.

## 2. Pamięć JEST bezpieczna — ale nie z powodu, który podaje blok

Wołań jest trzynaście z **trzech** różnych par `(katalog, korzeń)`: drzewo robocze
i dwa drzewa próbne kontroli przyrządu. Klucz `(katalog, korzeń)` rozdziela je wszystkie,
więc pamięć o takim kluczu **nie zmienia niczego, co czytnik zwraca** — zmierzone
przebiegiem: **21/21 zielone**.

Pole „Weryfikacja" żąda kontroli negatywnej: *pamięć z kluczem BEZ korzenia ma dać na
drzewie próbnym wynik drzewa roboczego*. **Zmierzyłem i ten warunek się nie potwierdza:**

```
klucz = katalog    ->  21/21 przeszło
klucz = jedno      ->  15/21 przeszło
      FAIL test_ile_POKRYCIA_daje_przypisanie_stalej_a_ile_zbieg_cyfr
      FAIL test_ile_par_CERTYFIKUJE_SIE_NAWZAJEM
      FAIL test_ile_pokrycia_WISI_NA_WLOSKU
```

Klucz **z samego katalogu jest zielony** — i to nie dlatego, że jest poprawny, tylko
dlatego, że w tym module `katalog` i `korzeń` **zawsze idą razem**: każda z trzech par
ma inny katalog, więc sam katalog wystarczy do ich rozdzielenia. Bezpieczeństwo jest tu
**przypadkiem populacji**, a nie własnością klucza, i tak to zapisuję.

Kluczem naprawdę niebezpiecznym jest ten, który **nie patrzy na argumenty w ogóle**
(jedno gniazdo). Wtedy drzewo próbne dostaje wynik drzewa roboczego, dokładnie jak
przewiduje intencja bloku — i zapala się sześć testów, w tym kontrole przyrządu
z drzewem próbnym, o które polu chodziło.

**Intencja kontroli jest więc słuszna, a jej zapisany warunek za słaby.** Prostuję to
w raporcie, a pola nie zmieniam: to pomiar z datą i zmiana pola zatarłaby ślad tego,
co pozycja sprawdzała.

## 3. USTERKA, KTÓRĄ ZŁAPAŁ ZESTAW, I NIEMAL OGŁOSIŁEM JĄ JAKO WYNIK

Pierwsza wersja pamięci miała kształt oczywisty: przemianować funkcję na
`_pozycje_pokrycia_bez_pamieci` i podstawić pod starą nazwę cienką obwolutę. Moduł dał
**19/21**, a ja miałem przed sobą gotowy nagłówek „pamięć jest niebezpieczna".

Nie jest. Padły dwa testy i drugi z nich nazywa przyczynę wprost:

```
FAIL test_sledzenie_wartosci_ZNA_skok_przez_odbiornik_metody_mutujacej:
  wycinek `pokrywajace[:2]` z `pozycje_pokrycia` — przypadek, ktory te pozycje
  wywolal — wystepuje w wyniku 0 razy zamiast raz
```

**Ta bramka czyta ŹRÓDŁO funkcji po nazwie.** Przemianowanie jej oślepiło:
wycinek, którego bramka szuka, stał odtąd w funkcji o innej nazwie. Usterka jest
w **implementacji pamięci**, nie w samym buforowaniu.

Pamięć napisana **w miejscu** — nazwa i ciało nietknięte, strażnik na początku, zapis
przed `return out` — daje **21/21 zielone** i tę samą oszczędność czasu.

Zapisuję to jako pierwszą rzecz po liczbach, bo różnica między „pamięć jest
niebezpieczna" a „mój sposób jej dopisania oślepia cudzą bramkę" jest całą różnicą
między błędnym wynikiem a prawdziwym ograniczeniem. **Ograniczenie brzmi: pamięć dla
`pozycje_pokrycia` wolno dopisać wyłącznie w ciele funkcji.**

## 4. Rozstrzygnięcie

**Pamięć jest bezpieczna i warta 12,4 s**, pod dwoma warunkami, oba zmierzone:

1. klucz niesie **obie** części — `(katalog, korzeń)`; klucz uboższy bywa zielony
   przypadkiem, a klucz pusty wywraca sześć testów;
2. pamięć stoi **w ciele funkcji**, bo nazwa `pozycje_pokrycia` jest czytana przez
   `test_sledzenie_wartosci_ZNA_skok_przez_odbiornik_metody_mutujacej`.

**Pamięci NIE dopisałem i to jest zgodne z polem „Dlaczego bez decyzji"**, które mówi
wprost: „dołożenie pamięci jest osobnym krokiem i wolno je zrobić dopiero, gdy ta
odpowiedź jest znana". Odpowiedź jest teraz znana; krok należy do osobnej pozycji.

## 5. Przewidywania spisane PRZED pomiarem

| # | przewidywanie | wynik |
|---|---|---|
| 1 | wołań: 6–14 | trafione (13) |
| 2 | różnych par: 2–3 | trafione (3) |
| 3 | bez pamięci: 24–30 s | trafione (27,7) |
| 4 | z pamięcią: 8–16 s | trafione (15,3) |
| 5 | klucz bez korzenia zapali kontrolę przyrządu | **OBALONE** — klucz z katalogu jest zielony; zapala dopiero klucz pusty |
| 6 | rozrzut z kilku przebiegów, liczby wyższe niż w 6.D284 | trafione |

Cztery trafione, jedno obalone — i **obalone jest to jedyne, które przepisałem z bloku
zamiast wyprowadzić z kodu**. Trzy pierwsze policzyłem z tego, co czytnik robi; piąte
przyjąłem na słowo pola „Weryfikacja" i właśnie ono nie wytrzymało pomiaru.

## 6. Czego świadomie nie zrobiono

- **Nie dopisano pamięci** — pole „Dlaczego bez decyzji" nazywa to osobnym krokiem.
- **Nie zmieniono klas pokrycia ani okna** (pole „Poza zakresem").
- **Nie zmieniono budżetu czasu zestawu** — ani `SUITE_RUNTIME_BUDGET_S`, ani
  `SUITE_CPU_BUDGET_S`. Skrócenie modułu o dwanaście sekund z okładem byłoby kuszącym
  powodem do obniżenia progu, a próg opisuje CAŁY zestaw na runnerze, nie ten moduł
  w tym kontenerze. Liczba jest tu wypisana słowem, i to nie jest ozdoba:
  `test_report_claims.py` przeczytał pierwszą wersję tego wiersza jako twierdzenie,
  że stała ma wartość dwanaście i cztery dziesiąte, przy kodzie mówiącym czterysta
  czterdzieści — bo `CLAIM` czyta nazwę w grawisach i pierwszą liczbę za nią. To samo
  zdarzyło się przy 6.D292; wzorzec został wtedy zostawiony bez wyjątku i słusznie,
  bo zdanie o NIEZMIENIANIU stałej nie potrzebuje żadnej cyfry obok jej nazwy.
- **Nie poprawiono pola „Weryfikacja" tej pozycji**, choć §2 pokazuje, że jego warunek
  jest za słaby — pomiaru z datą się nie przelicza.
- **Nie tknięto `src/`.**

## 7. Zauważone przy okazji, nietknięte

Dziewięć z trzynastu wołań idzie z pary domyślnej, czyli z drzewa roboczego. Gdyby
pamięć weszła, **dziewięć przebiegów czytnika zamieniłoby się w jeden** — a to znaczy,
że osiem dzisiejszych przebiegów liczy dokładnie to samo, co przebieg pierwszy.
Ile innych modułów tego zestawu ma tę samą własność, ta pozycja nie pyta; przy 6.D283
ta sama pamięć ścięła inny moduł z 31 s na 7 s, więc para przypadków jest już dwa.
