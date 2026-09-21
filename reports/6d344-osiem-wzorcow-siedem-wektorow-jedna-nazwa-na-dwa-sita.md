# 6.D344 · Wzorców odsiewających adres jest OSIEM, a cudzy pożycza JEDEN moduł — i żadna z tych liczb nie odtwarza zdania, z którego pozycja wyszła

**Data:** 21.09.2026 · **Gałąź:** `claude/new-session-1xabcy` · **Baza:** `9e8c33a`

**POMIAR POWTÓRZONY PRZED COMMITEM** na bazie `6ade0e2` — odtwarza się co do jedynki: 164 wzorce widoczne, **8** odsiewających adres, **3** uniwersalne, **7** różnych wektorów, **1** moduł sięgający po cudzy wzorzec i **5** po własny, kontrola pary daje ROZLACZNE. Daty pomiaru NIE przepisuję na dzisiejszą.

**Jedno zdanie tego raportu zostało PRZEPISANE po przeglądzie, przed commitem**, i jest to zapisane w §4 razem z liczbą, która była w nim odwrócona. Przegląd wykonał osobny czytelnik, nie autor pomiaru.

6.D334 §3 zapisało, że dwa pomiary nazw w prozie odsiewają adresy i **każdy własnym
wzorcem**: jeden pożycza `ADRES_NIE_TWIERDZENIE`, drugi ma `ODSYLACZ_PLIKU` napisany
tuż pod pętlą, która liczy. Ta pozycja **liczy i porównuje kształty**; niczego nie
scala i żadnego wzorca nie przepisuje.

Definicje i sześć przewidywań spisałem **przed** pomiarem, w `DEFINICJE.md`. Przyrząd
jest zachowany razem z dwiema wcześniejszymi wersjami, bo ścieżka liczby przez te
wersje jest tu treścią, a nie zapleczem.

---

## 1. Kryterium jest ZACHOWANIE, nie kształt źródła — i to jest wybór z 6.D343

Wzorzec rozpoznaję po tym, **co dopasowuje na próbce**, a nie po tym, jak wygląda
w źródle. Powód stoi w 6.D343 §6: sito po kształcie źródła dało tam zero, bo część
wzorców w ogóle nie istnieje w źródle jako literał. Każdy wzorzec opisuję **wektorem
ośmiu odpowiedzi**, a nie słowem.

## 2. Trzy usterki przyrządu, wszystkie zgłoszone, żadna nie zaszyta

**Pierwsza — próbka bez grawisów.** Wersja pierwsza miała sześć kształtów i **żadnego
w grawisach**. `PATH_TOKEN` z `tools/tests/test_report_hygiene.py` jest zakotwiczony
na grawisach po obu stronach, więc wyszedł z wektorem samych zer i **wypadł z klasy
„odsiewa adres"** — mimo że odsiewa adresy i tylko adresy. To ograniczenie mojej
próbki, nie drzewa. Po dopisaniu dwóch kształtów w grawisach: **5 → 8**.

**Druga — „pożyczony" liczony po MIEJSCU DEFINICJI.** Klasyfikowałem wzorzec jako
pożyczony, gdy jego nazwa powstaje przez `X = M.Y`. Wyszło **zero pożyczonych na
osiem** — i jest to **tautologia mojej definicji**, a nie wynik: każdy wzorzec jest
gdzieś zdefiniowany na miejscu, więc w miejscu definicji zawsze jest „własny". Pole
pyta o **użycia**, więc wersja trzecia liczy sięganie po cudzy wzorzec między
modułami.

**Trzecia — „to samo" na próbce nie znaczy „to samo".** Nie nazywam pary kopią, gdy
wektory są równe; równość na ośmiu kształtach nie dowodzi równości w ogóle i mówię to
zamiast wyciągać mocniejszy wniosek, niż wolno. Stało to w `DEFINICJE.md` przed
pomiarem i §5 pokazuje, dlaczego było potrzebne.

## 3. Trzy liczby, których żądało pole

```
skompilowanych wzorcow widocznych w modulach: 164
   wzorcow ODSIEWAJACYCH ADRES:  8
   uniwersalnych (odsiane):      3

   modulow siegajacych po CUDZY wzorzec adresowy: 1
   modulow uzywajacych WLASNEGO:                  5
```

```
   modul                              nazwa                      wektor
   test_field_paths                   BARE_TOKEN                 01000001
   test_field_paths                   MODULE_ARGUMENT            01001100
   test_field_paths                   PATH_TOKEN                 10000010
   test_machine_paragraphs            OZDOBNIK                   00000011
   test_prose_counts                  ODSYLACZ_PLIKU             11000000
   test_report_claims                 ADRES_NIE_TWIERDZENIE      11000011
   test_report_claims                 ZAKRES_W_GRAWISACH         00000010
   test_report_hygiene                PATH_TOKEN                 00000011

   ksztalty probki (kolejnosc bitow):
      0  sciezka z ukosnikiem i rozszerzeniem   1  nazwa z rozszerzeniem
      2  sciezka bez rozszerzenia               3  katalog zakonczony ukosnikiem
      4  bez jednego i drugiego                 5  kropka, ale nie rozszerzenie
      6  sciezka W GRAWISACH                    7  nazwa z rozszerzeniem W GRAWISACH
```

**Siedem różnych wektorów na osiem wzorców.** Podobieństwo zapisu nie przenosi się
tu na podobieństwo zachowania.

## 4. GŁÓWNE ZNALEZISKO: dwa różne wzorce noszą TĘ SAMĄ NAZWĘ i robią co innego

```
   test_field_paths     PATH_TOKEN   10000010
   test_report_hygiene  PATH_TOKEN   00000011
```

Nie mają ze sobą nic wspólnego poza nazwą:

* ten z `tools/tests/test_field_paths.py` **wymaga ukośnika** i grawisów nie chce —
  widzi `docs/TASKS.md` gołe i w grawisach, nie widzi gołej nazwy pliku;
* ten z `tools/tests/test_report_hygiene.py` **wymaga grawisów po obu stronach**
  i ukośnika nie wymaga — widzi wyłącznie to, co stoi w grawisach.

**Liczba w pierwszej wersji tego akapitu była odwrócona i jest przepisana, a nie
poprawiona po cichu.** Stało tu „rozłączne na sześciu z ośmiu pozycji"; sprawdzenie
pokazało coś przeciwnego — `10000010` wobec `00000011` różni się na **dwóch**
pozycjach (0 i 7) i zgadza się na **sześciu**. Przyrząd takiej liczby w ogóle nie
drukuje: podaje wyłącznie binarne `TO SAMO / ROZLACZNE`, więc liczba powstała
w prozie i nie miała pokrycia w niczym.

**Sama liczba zgodnych pozycji i tak przeceniałaby podobieństwo tych wzorców**, bo
pięć z sześciu zgód to zgoda na **niedopasowaniu** — oba wzorce po prostu nie widzą
ścieżki bez rozszerzenia, katalogu, zwykłego słowa ani kropki, która rozszerzeniem
nie jest. Rozstrzygają **trzy** kształty: ścieżkę gołą widzi tylko pierwszy, gołą
nazwę w grawisach tylko drugi, a ścieżkę w grawisach widzą obaj. Nazwa jest ta sama,
populacja, którą liczą, jest inna, i nic w drzewie tego nie mówi — nazwa sugeruje
jeden wzorzec tam, gdzie są dwa. **Nie jest to usterka**: każdy z nich pasuje do swojej bramki,
bo raporty piszą ścieżki w grawisach, a bloki kolejki nie zawsze. Jest to jednak
dokładnie kształt, przed którym ostrzegało pole — „dwa różne sita policzone jako
jedno powtórzone" — tylko odwrócony: tu **jedna nazwa przykrywa dwa sita**.

## 5. Para o identycznym wektorze jest JEDNA i NIE jest kopią

```
   wektor 00000011  (2 wzorcow, 1 para)
        test_machine_paragraphs.OZDOBNIK
        test_report_hygiene.PATH_TOKEN
```

Oba widzą wyłącznie kształty w grawisach i na mojej próbce są nierozróżnialne.
**Kopią nie są** i dlatego trzymam się definicji spisanej przed pomiarem: pierwszy
szuka ozdobnika w prozie maszynowej, drugi ścieżki w raporcie. Próbka o ośmiu
kształtach ich nie rozróżnia, bo **żaden z tych kształtów nie jest ozdobnikiem** —
i to jest granica pomiaru, nie wynik o drzewie.

**Zdanie, które wolno mi z tego wyciągnąć, brzmi:** par nierozróżnialnych na tej
próbce jest jedna, a kopii w sensie zachowania **nie zmierzyłem ani jednej**.

## 6. Liczba z pola NIE odtwarza zdania, z którego pozycja wyszła — i mówię to wprost

6.D334 §3 mówi „jeden **pożycza** `ADRES_NIE_TWIERDZENIE`". Mój pomiar
międzymodułowy znajduje **jeden** moduł sięgający po cudzy wzorzec adresowy — ale
jest nim `test_digit_boundaries`, a nie żaden z dwóch pomiarów nazw w prozie.

Przeczytałem oba miejsca:

```
tools/tests/test_prose_counts.py:881   ODSYLACZ_PLIKU = re.compile(...)
tools/tests/test_prose_counts.py:906       if ODSYLACZ_PLIKU.search(nazwa):
tools/tests/test_report_claims.py:1833 ADRES_NIE_TWIERDZENIE = re.compile(
tools/tests/test_report_claims.py:1929     ... ADRES_NIE_TWIERDZENIE.sub(
```

**Oba są stałymi własnego modułu.** „Pożycza" znaczyło tam **sięgnięcie po stałą
z innego miejsca TEGO SAMEGO modułu**, postawioną wcześniej do innego celu — wobec
wzorca napisanego tuż pod pętlą, która go używa. To jest podział na **odległość
w module**, a nie na moduł. Mój pomiar mierzy drugie i nie odtwarza pierwszego;
podaję obie liczby i mówię, że opisują różne rzeczy, zamiast dopasować jedną do
drugiej. **Nigdy nie uzgadniam liczby cudzej pozycji ze swoją.**

## 7. Przewidywania — trzy trafione, trzy obalone

| # | przewidywanie | wynik |
|---|---|---|
| P1 | `ODSYLACZ_PLIKU` i `PATH_TOKEN` wyjdą jako para **rozłączna** | **trafione**: `11000000` wobec `10000010` |
| P2 | wzorców od pięciu do piętnastu | **trafione**: osiem |
| P3 | większość napisana na miejscu | **OBALONE jako pytanie, nie jako liczba**: w wersji drugiej wyszło 8 z 8, ale była to tautologia definicji (§2); po przeliczeniu na użycia jest 5 modułów z własnym i 1 z cudzym |
| P4 | co najmniej **dwie** pary o identycznym wektorze | **OBALONE**: jedna — i ta jedna nie jest kopią (§5) |
| P5 | co najmniej jedna para podobna w źródle okaże się rozłączna | **trafione, i mocniej niż zakładałem**: dwa wzorce o **identycznej nazwie** rozchodzą się na trzech rozstrzygających kształtach próbki (§4) |
| P6 | wzorców uniwersalnych będzie **zero** | **OBALONE**: trzy — i dlatego podaję ich liczbę osobno, tak jak zapowiadał warunek obalenia |

## 8. Czego świadomie nie zrobiłem

Nie scaliłem żadnych dwóch wzorców, nie przepisałem żadnego, nie postawiłem bramki
na powtórzeniu, nie tknąłem `src/` ani `data/` — wszystko to stoi w polu „Poza
zakresem".

**Nie orzekam, że którekolwiek dwa wzorce są równoważne.** Orzekam wyłącznie
o ośmiu kształtach próbki i tak było zapisane przed pomiarem.

**Nie wpisałem gołej nazwy pliku do żadnego pola bloku.** Pole tej pozycji ostrzegało
wprost, że bramka na gołych nazwach się na tym zapala; próbka wzorcowa stoi
w **kodzie przyrządu**, nie w prozie.

## 9. Co zauważyłem przy okazji, ale nie tknąłem

Trzy wzorce w tych modułach dopasowują **wszystkie osiem** kształtów próbki, łącznie
z napisem bez kropki i bez ukośnika. Odsiałem je jako uniwersalne i nie wliczam do
ośmiu — ale nie sprawdzałem, czy któraś bramka używa ich tam, gdzie chciała odsiać
adres. Byłoby to inne pytanie i inny przyrząd; zapisuję, bo wpadnięcie ścieżki
w sito uniwersalne wygląda w wyniku dokładnie tak samo jak odsianie jej sitem
właściwym.
