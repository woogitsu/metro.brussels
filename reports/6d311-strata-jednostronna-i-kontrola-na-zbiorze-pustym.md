# 6.D311 · Strata jest jednostronna CO DO NAZWY, mediana komunikatu scalenia wynosi ZERO — a kontrola pola przechodzi na zbiorze pustym

**Data:** 20.09.2026 · **Gałąź:** `claude/sharp-ramanujan-jdr51o` · **Baza:** `7d854d3`

6.D302 policzyło czterdzieści osiem par „scalenie plus jego własna gałąź" i znalazło
dwadzieścia jeden par, których połowy stoją w różnych klasach śladu. Ta pozycja pyta,
ile **nazw** ginie między jednym komunikatem a drugim — i pole „Czego NIE wolno
przyjąć bez pomiaru" każe liczyć w **obie** strony, bo squash skleja treść kilku
commitów i scalenie może nieść nazwy, których gałąź nie ma.

Czytnik nazw jest **pożyczony**, nie napisany drugi raz: `nazwy_modulow_i_zapadek`
z `tools/tests/test_commit_claims.py`, ten sam, którym `klasy_sladu` przypisuje klasy.
Pole żądało tego wprost, a 6.D309 pokazało w tej samej sesji, ile kosztuje własny
przejazd po cudzym pytaniu.

---

## 1. Sprostowanie przesłanki tej pozycji, wpisane razem z jej wykonaniem

Pola „Skąd" tej pozycji i jej wiersz w tabeli cytowały zdanie **nieprawdziwe**:
że kierunek rozjazdu klas jest **jednostronny**. Zdanie zostało zmierzone jako
nieprawda 19.09.2026 i poprawione w PR #713 w `reports/6d302-scalenie-i-jego-galaz.md`
§4 — ale korekta przeszła po raportach i po wierszach tabeli pozycji WYKONANYCH,
a **bloków sześciopolowych, które to zdanie cytują, nie tknęła**. Były to czwarte
i piąte wystąpienie tej samej nieprawdy. Poprawiam oba **w tym commicie**, bo jest
to przesłanka właśnie tej pozycji, a nie poboczne znalezisko.

Prawdą zmierzoną jest: kierunek **przeważający, dwadzieścia z dwudziestu jeden**,
a kontrprzykładem para `d3bd70811149` (scalenie w klasie `dotyczy`) i `07dc360acd8d`
(gałąź w klasie `nic_wspolnego`).

**Co ta pozycja mierzy niezależnie od tamtego sporu:** rozjazd klas jest tu wyłącznie
sitem wybierającym dwadzieścia jeden par z czterdziestu ośmiu. Liczby §2–§4 liczę
osobno na dwudziestu jeden i na wszystkich czterdziestu ośmiu, więc nie zależą od
tego, czy kierunek nazwać jednostronnym czy przeważającym.

## 2. Liczby, których żądało pole „Wyjście" — dwadzieścia jeden par o różnych klasach

```
scalenie      klasa          galaz         klasa            nS   nG  oba tylG tylS
083f192958a5  nic_wspolnego  b7eefec530ad  dotyczy           0    1    0    1    0
154ad30971e3  nic_wspolnego  436a4ea1b52f  dotyczy           0    2    0    2    0
2ffb0b00cce5  nic_wspolnego  a4041024e1e8  dotyczy           1    2    1    1    0
4e56958d7036  nic_wspolnego  3e69616c9862  dotyczy           0    1    0    1    0
5ae1b52d99b3  nic_wspolnego  e9fb9bff88a1  dotyczy           0    2    0    2    0
5b1405de6078  nic_wspolnego  1df5143aa673  dotyczy           0    1    0    1    0
64fefc23ba37  nic_wspolnego  773f6973ec33  dotyczy           0    1    0    1    0
665bd987a439  nic_wspolnego  57bb7ccef3fe  dotyczy           0    3    0    3    0
77108a09131f  nic_wspolnego  7d82933e273d  dotyczy           0    1    0    1    0
7bf506295338  nic_wspolnego  f716215c5ad9  dotyczy           0    1    0    1    0
82055442bc9d  nic_wspolnego  069306c25d65  dotyczy           0    2    0    2    0
96dc2fe9e424  nic_wspolnego  120e5de1131a  dotyczy           0    2    0    2    0
988eff1ae58d  nic_wspolnego  23f77e7def98  dotyczy           0    2    0    2    0
a39295828837  nic_wspolnego  49887ae14ef4  dotyczy           0    1    0    1    0
becc2742eb65  nic_wspolnego  6dc7c4c20286  dotyczy           0    1    0    1    0
c1f5618689ac  nic_wspolnego  7f7f4b2c6cf7  dotyczy           0    2    0    2    0
d3bd70811149  dotyczy        07dc360acd8d  nic_wspolnego     2    3    2    1    0
e8db22f07822  nic_wspolnego  3089415ce538  dotyczy           0    2    0    2    0
efccb6160f9e  nic_wspolnego  bbf63233b0f7  dotyczy           0    1    0    1    0
f259d5d4b2ca  nic_wspolnego  6e0d525b5fa8  dotyczy           0    2    0    2    0
f684e40a3af5  nic_wspolnego  cf0176343343  dotyczy           0    1    0    1    0

mediana nazw w SCALENIU: 0      mediana STRATY:    1   suma: 31
mediana nazw w GALEZI:   2      mediana PRZYROSTU: 0   suma:  0
rozklad straty: {1: 12, 2: 8, 3: 1}
par ze strata ZERO:    0 z 21
par z przyrostem ZERO: 21 z 21
```

**Odpowiedź na pytanie, które pole kazało zadać wprost: ŻADNA.** Pole dopuszczało
tę odpowiedź („także gdy odpowiedź brzmi »żadna«") i to jest ta odpowiedź — zero
par o stratze zerowej wśród dwudziestu jeden. Każda z tych par gubi co najmniej
jedną nazwę.

## 3. Kierunek straty JEST jednostronny — i tym razem jest to policzone, a nie wyczytane z czoła listy

Pole ostrzegało, żeby jednostronności nie zakładać, i miało powód: 6.D302 zapisało
jednostronność, której nie policzyło, i to się okazało nieprawdą (§1). Tutaj liczę,
i wynik jest przeciwny do ostrzeżenia.

```
par, w ktorych nazwy SCALENIA sa PODZBIOREM nazw galezi: 48 z 48
suma nazw w galeziach: 71      suma nazw w scaleniach: 14
```

**W żadnej z czterdziestu ośmiu par komunikat scalenia nie niesie nazwy, której
nie ma w komunikacie gałęzi.** Przyrost wynosi zero nie „przeważająco", tylko
w całej populacji — i dlatego zapisuję to jako zdanie o zbiorach, a nie o większości.

Mechanizm widać po przeczytaniu jednej pary. Komunikat scalenia ma postać
`Scalenie #NNN: <tytuł pozycji>` plus streszczenie; komunikat gałęzi ma ten sam
tytuł i **całe uzasadnienie**, w którym padają nazwy modułów i zapadek. Scalenie
jest streszczeniem gałęzi, a nie sklejką kilku commitów — squash zdarzył się
wcześniej, po stronie gałęzi. Dlatego obawa pola („scalenie bywa dłuższe")
nie realizuje się w tym repozytorium ani raz.

Jedyne miejsce, w którym przyrost wychodzi niezerowy, to **wariant wąski** czytnika:
przy liczeniu nazw na oknie wokół kotwicy kontroli negatywnej, a nie na całym
komunikacie, para `d3bd70811149` daje przyrost jeden. To jest własność OKNA, nie
komunikatu — okno wycina z gałęzi inny kawałek tekstu niż ze scalenia. Podaję obie
liczby, żeby nie trzeba było zgadywać, którą policzono:

```
CALY KOMUNIKAT:        suma straty 31, suma przyrostu 0
OKNO WOKOL KONTROLI:   suma straty 28, suma przyrostu 1
```

## 4. Mediana komunikatu scalenia wynosi ZERO nazw

To jest liczba, której nie spodziewałem się wcale, i jest ostrzejsza niż sama strata.

```
scalen o ZERO nazw w calym komunikacie: 38 z 48
galezi   o ZERO nazw:                   11 z 48
par, w ktorych OBIE polowy nie nazywaja niczego: 11
maks nazw w galezi: 7
```

**Cztery piąte komunikatów scalenia nie wymienia ani jednej nazwy modułu ani
zapadki.** Strata mierzona w §2 jest więc w większości wypadków stratą **wszystkiego**,
a nie części: zbiór nazw scalenia jest pusty, a nie uboższy.

Wszystkie czterdzieści osiem par, dla porównania:

```
rozklad straty (48 par): {0: 13, 1: 20, 2: 11, 3: 2, 4: 1, 5: 1}
mediana straty: 1     suma: 57     par ze strata ZERO: 13 z 48
```

Trzynaście par o stratze zerowej rozkłada się tak: **jedenaście** to pary, w których
**obie** połowy nie nazywają niczego (strata zero przez pustkę), a **dwie** to pary,
w których zbiory są niepuste i **równe** — `69a0c0b60e0f` / `82dacc93d40d`
(po jednej nazwie) oraz `d949439319e0` / `c718134e56f1` (po dwie). Rozpisuję to,
bo „trzynaście par bez straty" i „dwie pary, w których scalenie naprawdę niesie
to samo co gałąź" są różnymi zdaniami o tym repozytorium.

## 5. KONTROLA PRZYRZĄDU: przechodzi w literze, a jej PRZESŁANKA jest obalona

Pole żądało, by para `ead62d2aa1ae` / `c705199f1bb7` miała stratę **zero**, „bo obie
jej połowy stoją w tej samej klasie". Wychodzi zero:

```
KONTROLA, para ead62d2aa1ae / c705199f1bb7:
   nS=0  nG=0  oba=0  tylkoG(STRATA)=0  tylkoS=0
   scalenie: []
   galaz:    []
```

**Mówię wprost, że to jest przejście na zbiorze pustym, zamiast raportować „zdana".**
Obie połowy nie nazywają NICZEGO, więc strata jest zerowa z tego samego powodu,
z którego zerowa jest różnica dwóch pustych zbiorów. Kontrola, która przechodzi
na pustym zbiorze, nie odróżnia czytnika działającego od oślepłego — ten sam kształt,
który 6.D303 §4 nazwał u siebie.

Gorzej: **przesłanka kontroli jest nieprawdziwa i to też jest zmierzone**, a nie
wydedukowane. Pole mówi „bo obie jej połowy stoją w tej samej klasie", czyli zakłada,
że ta sama klasa pociąga zerową stratę nazw. Nie pociąga:

```
par o TEJ SAMEJ klasie: 27
z tego ze strata NIEZEROWA: 14
   ef1ab97e2047  be7898102347  bez_raportu    strata=5
   e709f4953bd6  809e6f139831  nic_wspolnego  strata=4
   5c292a80d62b  6fc65bda8c22  bez_raportu    strata=3
   33f5b9b1118d  e3d06c160e4a  dotyczy        strata=2
   68aa7d6eab93  efc284edc96b  nic_wspolnego  strata=2
   e2382f7c9008  c4ff0915fc51  nic_wspolnego  strata=2
   a5aa464ba471  976f316b73d6  dotyczy        strata=1
   d51b5df1d56b  7d56e4d4a9ff  nic_wspolnego  strata=1
   9faf5a269111  e5367352638a  nic_wspolnego  strata=1
   527f509f0c40  d16207301b11  nic_wspolnego  strata=1
   a2293e65aba0  1f15ec5b8ef2  bez_raportu    strata=1
   dfbde8fa309e  25227a711533  bez_raportu    strata=1
   655c2365699b  9df11e3f4a63  bez_raportu    strata=1
   a589708c198c  8a708d96bca0  bez_raportu    strata=1
```

**Ponad połowa par o tej samej klasie gubi nazwy.** Powód widać po przeczytaniu
`klasy_sladu`: klasa `bez_raportu` — ta, w której stoi para kontrolna — jest
przypisywana, gdy commit nie dopisuje żadnego pliku w `reports/`, czyli **zanim
funkcja policzy jakąkolwiek nazwę**. Dla tej klasy „ta sama klasa" nie mówi o nazwach
nic. Dla dwóch pozostałych mówi tylko o **niepustości przecięcia komunikatu
z raportem**, a nie o równości zbiorów nazw dwóch komunikatów.

Pole przewidziało tę możliwość i kazało ją nazwać przed liczeniem reszty:
„jeśli przyrząd daje dla niej stratę niezerową, klasa i zbiór nazw rozjeżdżają się".
Przyrząd daje zero — więc litera jest spełniona — ale **rozjazd i tak istnieje**
i widać go na czternastu innych parach. Nazywam go tutaj, a §2–§4 liczę już
ze świadomością, że klasa i zbiór nazw są różnymi rzeczami.

## 6. Kontrola dodatnia — bo §5 nie wykonuje tej roboty

Skoro kontrola pola przechodzi na pustym zbiorze, pokazuję osobno, że czytnik
naprawdę widzi nazwy. Wypisane imiennie, a nie streszczone liczbą:

```
083f192958a5 [nic_wspolnego] -> []
b7eefec530ad [dotyczy]       -> ['test_all.py']

154ad30971e3 [nic_wspolnego] -> []
436a4ea1b52f [dotyczy]       -> ['MINIMUM_CLAIMS', 'test_lod.py']

d3bd70811149 [dotyczy]       -> ['MAX_REPORTS_WITHOUT_FIELD_LINE', 'MIN_REPORTS']
07dc360acd8d [nic_wspolnego] -> ['MAX_REPORTS_WITHOUT_FIELD_LINE',
                                 'MINIMUM_DOCUMENTED_ITEMS', 'MIN_REPORTS']

ef1ab97e2047 [bez_raportu]   -> ['MAX_COMMIT_EXCEPTIONS', 'MAX_DATE_EXCEPTIONS']
be7898102347 [bez_raportu]   -> ['MAX_COMMIT_EXCEPTIONS', 'MAX_DATE_EXCEPTIONS',
                                 'MINIMUM_DOCUMENTED_ITEMS', 'MIN_REPORTS',
                                 'test_all.py', 'test_backlog.py',
                                 'test_report_hygiene.py']
```

Ostatnia para jest najlepszym dowodem, że czytnik nie jest ślepy: znajduje siedem
nazw po stronie gałęzi i dwie po stronie scalenia, a dwie znalezione po stronie
scalenia **są podzbiorem** tych siedmiu. Gdyby czytnik oślepł, ostatnia para dałaby
zero i zero, tak jak para kontrolna.

Kontrola spójności, wykonana przy każdej z czterdziestu ośmiu par jako asercja
w kodzie pomiaru, a nie oględzinami: `|oba| + |tylko w gałęzi| + |tylko w scaleniu|`
ma równać się `|suma obu zbiorów|`. Nie zapaliła się ani razu — to był mój warunek
obalenia, spisany przed pomiarem.

## 7. Przewidywania spisane PRZED pomiarem — PIĘĆ obalonych z siedmiu

| # | przewidywanie | wynik |
|---|---|---|
| Z1 | mediana nazw w komunikacie scalenia: 1–6 | **OBALONE** — zero |
| Z2 | mediana nazw w komunikacie gałęzi: 1–6 | trafione (dwie) |
| Z3 | mediana straty: 1–3 | trafione (jeden) |
| Z4 | par ze stratą zero: 2–10 z 21 | **OBALONE** — żadna |
| Z5 | przyrost niezerowy w co najmniej pięciu parach | **OBALONE** — w żadnej |
| Z6 | kontrola przyrządu NIE da zera | **OBALONE** — daje zero |
| Z7 | gdzieś nazwy gałęzi są właściwym podzbiorem nazw scalenia | **OBALONE** — nigdzie |

**Z1, Z4, Z5 i Z7 upadły razem i z jednego powodu**, który nazywam, zamiast liczyć
cztery osobne pomyłki: wyobrażałem sobie komunikat scalenia jako **inny opis tej
samej pracy** — krótszy, może przestawiony, ale mówiący o tych samych modułach.
Jest nim **streszczenie tytułem**: bierze zdanie o pozycji i zostawia uzasadnienie
po stronie gałęzi, a nazwy modułów i zapadek stoją właśnie w uzasadnieniu. Przy tym
kształcie zbiór nazw scalenia MUSI być podzbiorem, i to zwykle pustym — więc Z5 i Z7
były wykluczone, zanim je zapisałem, a Z1 i Z4 przesunięte w jedną stronę.

**Z6 zapisałem przed pomiarem jako NIE-ŚLEPE i tak je liczę.** Postawiłem je po
przeczytaniu `klasy_sladu`, czyli była to dedukcja z kodu, nie przewidywanie
o drzewie. Dedukcja była **poprawna co do mechanizmu i błędna co do wyniku**: klasa
`bez_raportu` rzeczywiście nie ogląda nazw (§5), ale ta konkretna para ma po obu
stronach zbiór pusty, więc strata wychodzi zero mimo rozjazdu. Zapisuję jako pudło,
bo przewidziałem liczbę i liczba się nie zgodziła — a nie jako trafienie dlatego,
że rozumowanie stojące za nim potwierdziło się gdzie indziej.

**Z2 i Z3 trafione, i mówię wprost, ile to warte:** przedziały „1–6" i „1–3" są
szerokie, a dwa i jeden leżą w środku. To ta sama szerokość, którą 6.D303 §5
nazwało u siebie — nie sukces przewidywania, tylko jego luz.

## 8. Czego świadomie nie zrobiono

- **Nie przepisano ani jednego komunikatu.** Pole „Poza zakresem" zabrania tego wprost,
  a §4 mógłby kusić: trzydzieści osiem scaleń nie nazywa niczego.
- **Nie tknięto `klasy_sladu` ani `DIFF_SCALENIA`**, mimo że §5 pokazuje rozjazd
  klasy ze zbiorem nazw. Zmiana klasyfikacji byłaby zmianą cudzego pomiaru.
- **Nie zrewidowano rozstrzygnięcia 6.D279** o obecności scaleń w populacji.
  Tamto rozstrzygnięcie opiera się na zdaniu, że scalenia niosą ten sam komunikat
  co commity gałęzi, a §3 i §4 mierzą, że nazw nie niosą prawie wcale — ale pole
  „Dlaczego bez decyzji" mówi, że jest to **osobne pytanie**, i nie podejmuję go.
  Zapisane jako nowa pozycja kolejki.
- **Nie postawiono bramki** na stosunku nazw scalenia do nazw gałęzi.
- **Nie tknięto `src/`, `data/`** ani prozy w `tools/tests/`.

## 9. Zauważone przy okazji, nietknięte

**Nieprawda z 6.D302 żyła w PIĘCIU miejscach, a korekta z PR #713 poprawiła trzy.**
Poprawiłem czwarte i piąte w §1. Ogólniejsze: sprostowanie raportu i wiersza tabeli
nie dosięga **bloków sześciopolowych**, bo te cytują raport własnymi słowami,
a nie odsyłaczem. Żadna bramka nie łączy bloku z raportem, który blok cytuje.

**Para kontrolna tej pozycji i para kontrolna 6.D302 to ta sama para** —
`ead62d2aa1ae` / `c705199f1bb7`, odziedziczona z 6.D293. Dla tamtej pozycji była
kontrolą sensowną (obie połowy mają stać w jednej klasie i stoją), dla tej jest
przejściem na zbiorze pustym. **Kontrola przenosi się między pozycjami razem
z adresem, a nie razem z sensem** — i to jest ogólniejsze niż ta jedna para.

**Dwie pary, w których scalenie naprawdę niesie to samo co gałąź** (§4), mają obie
po stronie scalenia komunikat DŁUŻSZY niż `Scalenie #NNN: tytuł` — czyli ktoś
wpisał uzasadnienie także do scalenia. Ile scaleń ma komunikat dłuższy niż tytuł
i czy pokrywa się to z tymi dwiema, nie liczyłem.

## 10. Weryfikacja — rzeczywiste wyjście

Polecenie z pola „Weryfikacja" (`test_commit_claims.py`) plus cały zestaw, bo
pozycja podnosi cztery zapadki i dopisuje trzy bloki:

```
$ find . -name __pycache__ -prune -exec rm -rf {} +
$ python3 tools/tests/test_all.py
  [DRZEWO] 0 plikow drzewa roboczego poza zasiegiem bramek czytajacych `git ls-files` — 6.D165
  [BAJTKOD] wyczyszczono 1 kat. __pycache__ (1 plikow) pod tools/ — 6.D122
  ...
  2664/2664 przeszło
  RAZEM 414.695 s, 2664 testów, 139 modułów
EXIT=0
```

**Bramki nie przybyło** — pozycja LICZY, a pole „Poza zakresem" zabrania stawiania
bramki na stosunku nazw scalenia do nazw gałęzi. Liczba testów jest ta sama co przy
6.D310 (2664) i mówię to wprost, zamiast pokazywać wzrost, którego nie ma.

Pierwszy przebieg tego samego zestawu dał **2663/2664** i jeden `FAIL`:
`test_przebieg_MOWI_ile_plikow_lezy_poza_zasiegiem_bramek_czytajacych_gita`
zgłosił jeden plik nieśledzony — był to raport tej pozycji, jeszcze nie dodany do
indeksu. Zapisuję to zamiast pokazywać wyłącznie zielony przebieg: bramka złapała
dokładnie to, po co stoi, a nie usterkę pomiaru.
