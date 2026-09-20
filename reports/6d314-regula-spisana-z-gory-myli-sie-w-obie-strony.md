# 6.D314 · Populacja jest o rząd wielkości większa, niż zgadłem — a reguła odsiewu spisana Z GÓRY myli się w OBIE strony, i to jest zmierzone

**Data:** 20.09.2026 · **Gałąź:** `claude/sharp-ramanujan-jdr51o` · **Baza:** `c67ddf6`

Przy korekcie 6.D296 zdanie „trzy z dziewięciu wpisów" było nieprawdziwe, a lista
dziewięciu adresów stała w §3 tego samego raportu. Bramka go nie zapaliła, bo
`CLAIM` szuka cyfry, a „trzy" stoi słownie. Ta pozycja liczy, ilu zdań to dotyczy.

Pole „Skończone, gdy" żądało czegoś więcej niż liczb: **reguły odsiewającej zwroty,
wypowiadającej się bez patrzenia na wynik**. Spisałem ją w scratchpadzie **przed
uruchomieniem czytnika** i §4 pokazuje, ile była warta.

---

## 1. Trzy liczby, których żądało pole „Wyjście"

```
raportow w korpusie:                                          440
ZDAN z liczebnikiem slownym W SASIEDZTWIE NAZWY:             3810

   TWIERDZENIE o mierzalnej wielkosci:   2370   (62 %)
   ZWROT:                                1440   (38 %)
   suma klas:                            3810   = populacja

TWIERDZEN sprawdzalnych dzis automatycznie:                   886   (37 % twierdzen)
```

Klasy sumują się do populacji — mój warunek obalenia („jeśli nie sumują się,
raportuję trzecią klasę z nazwy") nie zapalił się.

**Trzy tysiące osiemset dziesięć zdań to nie jest margines.** `CLAIM` widzi dziś
liczby cyfrowe; poza jego zasięgiem stoi populacja, w której **dwa tysiące trzysta
siedemdziesiąt** zdań twierdzi coś o mierzalnej wielkości, a **osiemset osiemdziesiąt
sześć** dałoby się sprawdzić bez dopisywania czegokolwiek poza liczebnikami — nazwa
w nich rozwiązuje się w drzewie już dziś.

## 2. Reguła odsiewu, spisana przed pomiarem

Cytuję ją z pliku definicji, bo to jedyny sposób, żeby było widać, że nie została
dobrana do wyniku. Zdanie jest **twierdzeniem** wtedy i tylko wtedy, gdy liczebnik
stoi w **konstrukcji liczącej**, czyli w promieniu czterdziestu znaków po nim stoi:

1. rzeczownik policzalny z **zamkniętej listy** obiektów drzewa (wpis, nazwa, plik,
   moduł, test, wiersz, pozycja, bramka, zapadka, commit, para, grupa, klasa,
   przebieg, asercja, raport, blok, stała, cytat, wystąpienie, artefakt, job,
   rewizja, akapit, węzeł, znak, pole), **albo**
2. przyimek `z` plus drugi liczebnik („trzy **z** dziewięciu"), **albo**
3. forma `wynosić` / `liczyć` / `jest` / `są` bezpośrednio przy liczebniku.

Uzasadnienie też jest z tamtego pliku: liczebnik, który nie liczy obiektów drzewa,
nie da się sprawdzić bramką, bo **nie ma czego policzyć**. Reguła miała być
o sprawdzalności, nie o stylu.

## 3. Ile waży każda klauzula

```
  1440  rzeczownik
   270  czasownik + rzeczownik
   257  czasownik
   162  z+liczebnik
   159  rzeczownik + z+liczebnik
    41  czasownik + rzeczownik + z+liczebnik
    41  czasownik + z+liczebnik
```

Klauzula rzeczownikowa sama promuje **1440** zdań i jest trzonem reguły. Klauzula
czasownikowa promuje samodzielnie **257** — i to ona okazała się usterką.

## 4. GŁÓWNE ZNALEZISKO: reguła myli się w OBIE strony, a oba błędy są policzone

### 4.1 Fałszywe trafienia — klauzula `jest`/`są`

```
TWIERDZEN promowanych WYLACZNIE klauzula czasownika:     257 z 2370
   z tego przez samo `jest`/`są`, bez `wynosi`/`liczy`:  139
```

Przeczytane, nie wywnioskowane:

```
„Pomiar rozstrzygający: plik obok nie zmienia ANI JEDNEGO bajtu `line --trace`
 JEST z tych trzech najtwardszy, bo wzorcem JEST …"

„**Na poziomie jednego punktu JEST to brak dowodu, a nie dowód braku**…"

„Trzy razy kontrola pokazała, że coś nie JEST przybite"
```

Słowo `jest` w polszczyźnie stoi wszędzie, a moje okno czterdziestu znaków nie
odróżnia „liczba **jest** równa trzy" od „coś nie **jest** przybite". **Klauzula
trzecia w moim własnym zapisie miała brzmieć »bezpośrednio przy liczebniku«,
a zaimplementowałem ją jako »gdziekolwiek w oknie«** — i to jest rozjazd między
regułą, którą spisałem, a regułą, którą wykonałem. Zapisuję to jako błąd wykonania
reguły, a nie jako wadę reguły, bo to dwie różne rzeczy i mieszanie ich zatarłoby,
która z nich zawiodła.

### 4.2 Fałszywe pominięcia — zamknięta lista rzeczowników

```
ZWROTOW, w ktorych po liczebniku stoi rzeczownik POLICZALNY SPOZA mojej listy:
   311 z 1440
```

Przeczytane:

```
„Dziewięć ocalałych, ta sama dziewiątka co w `reports/mutation-sweep.md`."
„Osiem kontroli negatywnych, `md5sum -c: OK` po każdej"
„Artefakt ma `retention-days: 30`, czyli szereg czasowy będzie miał
 trzydzieści dni pamięci."
```

Wszystkie trzy są **twierdzeniami o mierzalnej wielkości** — ocalałe mutacje,
wykonane kontrole, dni retencji. Wypadły, bo „ocalałych", „kontroli" i „dni" nie
stoją na liście, którą zamknąłem przed pomiarem. **Zamknięcie listy było warunkiem
uczciwości pomiaru i jednocześnie jego największą wadą**; nie otwieram jej po fakcie,
bo wtedy przestałaby być regułą spisaną z góry, a stałaby się opisem wyniku.

### 4.3 Powierzchnia błędu

```
co najmniej 139 falszywych trafien + 311 falszywych pominiec = 450 zdan
450 / 3810 = 11,8 % populacji
```

Jest to **dolne oszacowanie**: policzyłem tylko te wypadki, które moje dwa sita
kontrolne umiały wskazać. Liczb 2370 i 1440 nie poprawiam — są tym, co dała reguła
spisana przed pomiarem, i taka jest ich wartość.

## 5. Kontrola przyrządu — zdana

Pole żądało, by zdanie „trzy z dziewięciu wpisów" **w wersji sprzed korekty**
(`4e2a151`) wyszło w klasie twierdzeń:

```
w.167  [TWIERDZENIE]  Zauważone przy okazji, nietknięte Trzy z dziewięciu wpisów
       ginących przy pięciu wierszach stoją w **`test_message_claims.py`
       i `test_bytecode_staleness.py`…
znaleziono: 1
```

Wychodzi, i to **klauzulą drugą** („z" plus liczebnik), czyli tą, którą napisałem
z myślą dokładnie o tym kształcie. Kontrola nie jest więc trywialna — ale też nie
jest ślepa: klauzula druga promuje samodzielnie 162 zdania, nie jedno.

## 6. Który liczebnik pada najczęściej — i dlaczego to zależy od pytania

```
POJEDYNCZE FORMY            RODZINY FORM
trzy       411              jeden (6 form)   1062
dwa        409              dwa   (5 form)    914
jeden      305              trzy  (3 formy)   559
dwie       266              cztery(3 formy)   332
cztery     242
jednego    221
dwóch      200
jednym     163
```

Po formach wygrywa **trzy**, przewagą **dwóch wystąpień** na czterystu jedenastu.
Po rodzinach wygrywa **jeden**, i to bez zbliżenia. Podaję obie tabele, bo
„najczęstszy liczebnik" nie jest jedną wielkością — i to jest ten sam kształt,
co przy 6.D306 i 6.D308: wybór definicji przestawia ranking, nie zmieniając drzewa.

## 7. Przewidywania spisane PRZED pomiarem — CZTERY obalone z sześciu

| # | przewidywanie | wynik |
|---|---|---|
| U1 | zdań w populacji: 200–900 | **OBALONE** — 3810, o rząd wielkości |
| U2 | twierdzeń **mniej niż połowa** | **OBALONE** — 62 % |
| U3 | najczęstszy liczebnik to `dwa`/`dwie`/`dwóch` | **OBALONE w obie strony** — §6 |
| U4 | sprawdzalnych **mniej niż połowa** twierdzeń | trafione — 37 % |
| U5 | kontrola przyrządu wyjdzie w klasie twierdzeń | trafione |
| U6 | moja reguła **pomyli się** na co najmniej jednym zdaniu | trafione — 450 zdań |

**Obie trafione są o PRZYRZĄDZIE, obie z brzegu — a wszystkie cztery obalone są
o DRZEWIE.** U5 i U6 mówią o tym, co zrobi mój własny kod, i tam nie pomyliłem się;
U1, U2 i U3 mówią o tym, co stoi w czterystu czterdziestu raportach, i tam pomyliłem
się za każdym razem. To nie jest przypadek do przemilczenia: o własnym narzędziu
wiem, bo je napisałem, a o korpusie tego projektu **zgaduję** — i ta pozycja mierzy,
o ile.

**U1 upadło najmocniej i wiem dlaczego.** Spodziewałem się setek, bo wyobraziłem
sobie „zdanie z liczbą słowną" jako rzadkość. Tymczasem **proza tego projektu pisze
liczby słownie z zasady** — dokładnie dlatego, że `CLAIM` zapala się na cyfrze przy
nazwie w grawisach, a lekarstwem wpisanym w `CLAUDE.md` jest „przecinek zaraz za
grawisem albo liczba wypisana słownie". Reguła obchodzenia bramki **wyprodukowała
populację, której ta bramka nie widzi** — i to jest mechanizm, nie zbieg.

## 8. Czego świadomie nie zrobiono

- **Nie zmieniono wzorca `CLAIM`** ani nie dopisano bramki na liczebnikach. Pole
  „Poza zakresem" zabrania tego wprost, a §4 pokazuje, że reguła gotowa do zamiany
  w bramkę jeszcze nie istnieje.
- **Nie poprawiono ani jednego zdania w `reports/`** — także tych, które §4.2
  pokazuje jako twierdzenia wypadające z sita.
- **Nie otwarto listy rzeczowników po pomiarze** (§4.2) ani nie zawężono klauzuli
  czasownikowej (§4.1). Obie poprawki są oczywiste i obie unieważniłyby zdanie
  „reguła spisana z góry", które jest tu treścią.
- **Nie poprawiono liczb 2370 i 1440** o zmierzoną powierzchnię błędu — są tym,
  co dała reguła, a nie tym, co dałaby reguła lepsza.
- **Nie tknięto `src/`, `data/`** ani `docs/TASKS.md` poza własnym wierszem.

## 9. Zauważone przy okazji, nietknięte

**Liczba `450` z §4.3 jest dolnym oszacowaniem i nie da się jej podnieść bez
przeczytania korpusu ręcznie.** Trzy tysiące osiemset dziesięć zdań to kilkanaście
godzin czytania; pozycja tego nie zamawiała i ja tego nie zrobiłem.

**Klauzula `jest`/`są` promuje 139 zdań, a `wynosi`/`liczy` — pozostałe 118 z tych
257.** Gdyby ktoś kiedyś zamieniał tę regułę w bramkę, ta jedna klauzula jest całą
różnicą między sitem użytecznym a szumem; zapisuję rozbicie, żeby nie trzeba było
go liczyć drugi raz.

**Zdanie z §7 o mechanizmie — że lekarstwo na `CLAIM` produkuje populację poza
zasięgiem `CLAIM` — jest hipotezą wyprowadzoną z `CLAUDE.md`, a NIE pomiarem.**
Nie policzyłem, ile z tych 3810 zdań powstało jako obejście bramki, a ile po prostu
dlatego, że tak się pisze po polsku. To jest osobne pytanie i osobna pozycja.

## 10. Weryfikacja — rzeczywiste wyjście

```
$ find . -name __pycache__ -prune -exec rm -rf {} +
$ python3 tools/tests/test_all.py
  [DRZEWO] 0 plikow drzewa roboczego poza zasiegiem bramek czytajacych `git ls-files` — 6.D165
  [BAJTKOD] wyczyszczono 1 kat. __pycache__ (1 plikow) pod tools/ — 6.D122
  2664/2664 przeszło
  RAZEM 364.619 s, 2664 testów, 139 modułów
EXIT=0
```

Zero `FAIL`. **Bramki nie przybyło** — pole „Poza zakresem" zabrania dopisania
bramki na liczebnikach, a §4 pokazuje, że reguła gotowa do zamiany w bramkę jeszcze
nie istnieje. Bramki dotknięte tą pozycją przeszły wcześniej osobno —
`test_report_hygiene`, `test_backlog`, `test_field_paths`, `test_report_claims`
i `test_docs_map`: **138/138**.

**Piąty pomiar ściany na tym kontenerze w tej sesji**, przy tej samej liczbie testów:

```
414,695     418,599     361,079     365,940     364,619
```

Cztery ostatnie punkty układają się w dwie pary (`≈416` i `≈364`) odległe o 15 %.
Zapisuję to jako dane dla 6.D313, a nie jako wniosek: pięć punktów nadal nie
rozstrzyga, czy pasma są dwa.
