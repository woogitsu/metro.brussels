# 6.D350 · Sumowań `float` po zbiorze jest pod `tools/` ZERO — a przeliczenie rosnąco i malejąco NIE łapie jedynego rozjazdu, który ktoś zaobserwował

**Data:** 23.09.2026 · **Gałąź:** `claude/6d350-suma-float-haszowanie` · **Baza:** `c4ef8a1`

6.D341 zmierzyło, że jego własny przyrząd, uruchomiony trzy razy na tych samych
danych, dał 74,418 / 74,418 / 74,417 s, i wskazało przyczynę: pętla po zbiorze
napisów i dodawanie `float`, które nie jest łączne. Ta pozycja pyta, ile miejsc pod
`tools/` sumuje tak samo i w ilu kolejność naprawdę zmienia wynik. **Liczy i wypisuje
imiennie; żadnego sumowania nie przepisuje.**

Trzy liczby, których żąda pole: **0 · 0 · 0**. Miejsc, które sumują `float` w pętli
po zbiorze albo po słowniku zbudowanym z takiej pętli, nie ma pod `tools/` ani
jednego; więc nie ma też takiego, w którym kolejność zmienia trzecie miejsce, i nie
ma bramki, która porównywałaby taki wynik z zapadką. **Zjawisko z 6.D341 nie dotyka
dziś ani jednego progu.**

Ale wynik, dla którego tę pozycję warto było wziąć, jest inny: **metoda, którą pole
przepisało — przeliczenie populacji rosnąco i malejąco — na jedynym zaobserwowanym
przypadku daje w obu kolejnościach tę samą wartość**, więc kontrola przyrządu
w brzmieniu pola nie przechodzi (§1). A przyczyna rozjazdu nie jest tam, gdzie pole
kazało jej szukać: nie w rzędach wielkości składników, tylko w tym, że **mediana
z parzystej liczby próbek trzycyfrowych stawia sumę dokładnie na granicy
zaokrąglenia** (§3).

Pomiar na Pythonie 3.11.15 w kontenerze; CI chodzi na 3.14. Kolejność zbioru
napisów zależy od ziarna haszowania w obu wersjach, więc klasa zjawiska jest ta
sama, ale konkretne ziarna i ich wyniki niżej są liczbami **tej** maszyny.

---

## 1. Kontrola przyrządu — w brzmieniu pola NIE PRZECHODZI

Pole żąda, żeby pętla z 6.D341 wyszła w klasie „kolejność zmienia trzecie miejsce",
sprawdzonej przeliczeniem tej samej populacji rosnąco i malejąco.

**Przyrządu 6.D341 w drzewie nie ma i w katalogu roboczym też go nie znalazłem.**
Pętlę odtworzyłem z opisu w `reports/6d341-osiemdziesiat-procent-przyrostu-robi-dziesiec-modulow.md`
(`for m in M0 | M1`, `sumy[klasa] += …`, mediana dnia po module, dni 14.09 i 20.09),
na tych samych artefaktach `czas-zestawu`, które odtworzono przy 6.D351 cięciem
20.09.2026 20:00 UTC. Odtworzenie zgadza się z 6.D332 i 6.D341 tam, gdzie da się to
sprawdzić — mediana ściany 133,272 → 253,407 s, n = 42 i 48, 126 modułów istniejących.

Najpierw to, co 6.D341 zaobserwowało — przebiegi z losowym ziarnem:

```
PYTHONHASHSEED=losowe  istnial=74.417  (repr 74.41749999999999)  doszedl=42.654
PYTHONHASHSEED=losowe  istnial=74.418  (repr 74.41750000000002)  doszedl=42.654
PYTHONHASHSEED=losowe  istnial=74.418  (repr 74.41750000000003)  doszedl=42.654
PYTHONHASHSEED=losowe  istnial=74.418  (repr 74.41750000000002)  doszedl=42.654
PYTHONHASHSEED=losowe  istnial=74.418  (repr 74.41750000000002)  doszedl=42.654
PYTHONHASHSEED=losowe  istnial=74.418  (repr 74.41750000000003)  doszedl=42.654
```

Rozjazd odtwarza się: ta sama populacja, 74,417 albo 74,418. A teraz metoda pola:

```
skladnikow=126  min=-0.014  max=17.4705
rosnaco  74.418  (repr 74.41750000000002)
malejaco 74.418  (repr 74.41750000000006)
fsum     74.418  (repr 74.4175)
trzecie miejsce ZMIENIA SIE: False
```

**Rosnąco i malejąco daje tę samą wartość, 74,418.** Obie kolejności lądują nad
granicą zaokrąglenia, a 74,417 bierze się z kolejności, która ląduje pod nią — i tej
ani rosnąca, ani malejąca nie trafia. Pętla, dla której rozjazd **zaobserwowano**,
w klasie „zmienia trzecie miejsce" według metody pola **nie wychodzi**. Mówię to
wprost, zamiast przyjąć kontrolę za zdaną.

Metoda, która kontrolę zdaje, to przeliczenie na wielu kolejnościach, a nie na
dwóch skrajnych:

```
istnial  n=126 fsum=74.4175 (74.418)  rosnaco 74.418  malejaco 74.418  | 10000 permutacji: {'74.417': 2642, '74.418': 7358}
doszedl  n= 13 fsum=42.6545 (42.654)  rosnaco 42.654  malejaco 42.655  | 10000 permutacji: {'42.654': 5647, '42.655': 4353}
```

i to samo przez ziarno haszowania, czyli przez tę kolejność, którą pętla dostaje
naprawdę — 200 ziaren, 0 … 199:

```
     47 istnial=74.417
    153 istnial=74.418
    119 doszedl=42.654
     81 doszedl=42.655
```

**Na tej maszynie co czwarte ziarno daje 74,417** (47 z 200). 6.D341 trafiło je raz
na trzy przebiegi, czyli mniej więcej tak często, jak to przewiduje ta proporcja.

Dla wyniku w drzewie wybór metody nie ma znaczenia, bo populacja miejsc, do których
by się stosowała, jest pusta (§2). Ma znaczenie dla każdego, kto tę metodę weźmie
do następnego pytania: **para rosnąco/malejąco jest podłogą, nie rozstrzygnięciem**
— wynik „różne" dowodzi chwiejności, wynik „równe" niczego nie dowodzi.

## 2. Trzy liczby, których żądało pole

**Skan konstrukcji**, AST każdego pliku `.py` pod `tools/`, z regułą jednego skoku
przez przypisanie w zasięgu z 6.D326 (przyrząd pozwala na łańcuch do trzech skoków):
`sum(…)` i `+=` w ciele pętli `for`, gdzie źródłem iteracji jest zbiór (literał,
składanie, `set()`/`frozenset()`, operator `| & - ^`, metody `union` i pokrewne,
adnotacja `set[…]`) albo widok słownika zbudowanego ze składania albo z pętli po
zbiorze.

```
UNIKALNYCH miejsc sumowania: 452   plikow: 109
   sum {'PEWNY': 64, 'NIE-FLOAT': 101, 'NIEROZSTRZ': 49, 'ZBIOR': 2}
   += {'NIEROZSTRZ': 46, 'NIE-FLOAT': 171, 'PEWNY': 19}
```

„NIE-FLOAT" to składnik, który z kształtu nie może być `float` (literał całkowity,
`len`, `count`, napis, bajty, lista). „PEWNY" to źródło o ustalonej kolejności
(lista, krotka, `sorted`, `range`, `zip` po takich). **Miejsc po zbiorze konstrukcja
znajduje trzy**, z czego skan drugi zalicza jedno do „NIE-FLOAT" już po kształcie
składnika:

| miejsce | co sumuje | typ składnika |
|---|---|---|
| `tools/tests/test_assertion_gate.py:372` | `NIEME_ASERCJE[n] for n in zaslepione` | liczba całkowita |
| `tools/tests/test_assertion_gate.py:1140` | `lista[n] for n in zaslepione` | liczba całkowita |
| `tools/tests/test_prose_counts.py:1121` | `1 for o in odciski if …` | liczba całkowita |

**Wszystkie trzy sumują liczby całkowite**, a dodawanie liczb całkowitych jest
łączne — kolejność nie zmienia tam niczego. Pierwsze z nich stoi przy zapadce
(komentarz nad nim mówi, że suma „ma dotyczyć tego samego zbioru modułów, o którym
mówi zapadka"), więc to jest dokładnie przypadek, przed którym pole ostrzegało:
**konstrukcja jest, zjawiska nie ma.**

**95 miejsc skan zostawia nierozstrzygniętych** — źródło iteracji to parametr
funkcji, wynik wywołania albo nazwa bez przypisania w zasięgu. Wypis wszystkich
95 przeczytałem: żadne źródło nie jest nazwą zbioru; to punkty, pierścienie
i ścianki geometrii (`zip(ring, ring[1:] + ring[:1])`), `range(…)`, listy z JSON-a,
kolekcje Blendera i liczniki. Do definicji prześledziłem **kilkanaście** tych, których
składnik może być `float` — każde, które dało się doprowadzić do definicji, kończy
się na liście, krotce, `sorted` albo dokumencie JSON. Parametry funkcji geometrii
(`windows`, pierścienie, punkty) i kolekcje Blendera zostały na poziomie wypisu,
tak samo jak miejsca, których składniki są w kształcie liczbami całkowitymi albo
bajtami.

**Sonda w czasie wykonania**, bo skan konstrukcji może przeoczyć zbiór podany przez
parametr: `sitecustomize` podmienia `sum` na czas pełnego przebiegu
`tools/tests/test_all.py` i dla każdego wywołania z pliku pod `tools/` zapisuje typ
iteratora (dla wyrażenia generującego — typ jego pierwszego źródła) i to, czy wśród
składników jest `float`. Najpierw kontrola na wejściu syntetycznym — zbiór trzech
floatów sumowany na dwa sposoby i lista liczb całkowitych:

```
{"rec": {"t.py:2|gen:set_iterator|True": 1, "t.py:2|set|True": 1, "t.py:2|list|False": 1}, ...}
```

Potem zestaw (kod wyjścia 0, `RAZEM 358.104 s, 2665 testów, 139 modułów`):

```
miejsc sum() wykonanych: 174  wywolan: 261705
  dict_values                  float=False  miejsc=29
  dict_values                  float=True  miejsc=1
  gen:ZipExtFile               float=False  miejsc=1
  gen:dict_itemiterator        float=False  miejsc=2
  gen:dict_keyiterator         float=False  miejsc=3
  gen:dict_valueiterator       float=False  miejsc=12
  gen:generator                float=False  miejsc=5
  gen:list_iterator            float=False  miejsc=80
  gen:list_iterator            float=True  miejsc=13
  gen:range_iterator           float=True  miejsc=2
  gen:set_iterator             float=False  miejsc=3
  gen:tuple_iterator           float=False  miejsc=1
  gen:tuple_iterator           float=True  miejsc=2
  gen:zip                      float=True  miejsc=7
  list                         float=False  miejsc=4
  list                         float=True  miejsc=9
zbiorowe z floatem: {}
--- zrodlo zbiorowe (wszystkie):
   tests/test_assertion_gate.py:1140|gen:set_iterator|False 1
   tests/test_assertion_gate.py:372|gen:set_iterator|False 1
   tests/test_prose_counts.py:1121|gen:set_iterator|False 1
--- float, zrodlo slownikowe:
   tests/test_curve_radius_axes.py:266|dict_values|True 1
```

**Sonda widzi po zbiorze dokładnie te trzy miejsca, które znalazł skan, i żadne nie
niesie `float`.** Jedyne sumowanie `float` po widoku słownika to
`tools/tests/test_curve_radius_axes.py:266`, a klucze tego słownika idą z krotki
`AXES` — kolejność jest ustalona w źródle.

Stąd trzy liczby:

```
sumujacych float po zbiorze (albo slowniku ze zbioru):   0
z nich kolejnosc zmienia trzecie miejsce:                 0
z nich w bramce porownujacej wynik z zapadka:             0
```

**Lista imienna ostatniej jest pusta — i to jest odpowiedź, a nie porażka pomiaru:**
zjawisko zaobserwowane w 6.D341 żyje wyłącznie w przyrządach pisanych poza drzewem.

## 3. Przyczyna rozjazdu to NIE rzędy wielkości, tylko granica zaokrąglenia

Pole ostrzegało, że różnica pojawia się, „gdy składniki mają bardzo różne rzędy
wielkości **i** jest ich dużo". Pomiar pokazuje, że **żaden z tych dwóch warunków
nie jest konieczny**: klasa „doszedł" ma **trzynaście** składników i też jest
chwiejna (81 z 200 ziaren daje 42,655, reszta 42,654).

Rozstrzyga co innego. `math.fsum` daje dokładne sumy **74,4175** i **42,6545** —
obie z piątką na czwartym miejscu, czyli **dokładnie na granicy zaokrąglenia do
trzech miejsc**. Błąd rzędu 10⁻¹⁴, który daje zmiana kolejności, wystarcza wtedy,
żeby przestawić trzecią cyfrę w jedną albo drugą stronę. Sumie o dokładnej wartości
choćby 74,4172 ta sama zmiana kolejności nie zrobiłaby nic.

Dlaczego suma ląduje na granicy, jest policzalne:

```
2026-09-14 modulow 126 mediana z 4. miejscem =5: 33 parzysta liczba probek u 126
2026-09-20 modulow 139 mediana z 4. miejscem =5: 39 parzysta liczba probek u 139
```

Artefakt zapisuje sekundy z trzema miejscami. Oba dni mają **parzystą** liczbę
artefaktów (42 i 48), więc mediana jest średnią dwóch wartości i w co czwartym
module kończy się piątką na czwartym miejscu. Różnice i sumy takich median są
wielokrotnościami 0,0005, więc **co druga suma trafia dokładnie w granicę**
i jest chwiejna przy każdej kolejności, która nie jest dokładna.

**Ta chwiejność jest więc własnością mediany z parzystej próby zaokrąglonej do
trzech miejsc, a nie liczby składników.** Pytanie „ile sumowań jest wrażliwych na
kolejność" w tym drzewie wychodzi zerem; pytanie „ile miejsc wypisuje do trzech
miejsc medianę z parzystej próby trzycyfrowej" jest innym pytaniem i go tu nie
liczę.

## 4. Czego świadomie nie zrobiłem

Nie przepisałem żadnego sumowania na `math.fsum` ani na `sorted`, nie ustawiłem
ziarna haszowania, nie ruszyłem żadnej zapadki, nie tknąłem `src/` ani `data/` —
wszystko to stoi w polu „Poza zakresem".

**Nie uznałem kontroli przyrządu za zdaną**, choć permutacje ją zdają: pole
przepisało metodę rosnąco/malejąco i w tym brzmieniu kontrola nie przechodzi (§1).
Podaję obie metody z ich wynikiem.

**Nie przepisałem na nowo przyrządu 6.D341 jako „tego samego".** Jest odtworzeniem
z opisu w raporcie; zgadza się z nim w medianach i w klasie „istniał", ale nie
wiem, czy jest z nim tożsamy w każdym szczególe.

Sondy nie rozciągnąłem na `+=` w pętlach: podmiana `sum` tego nie widzi, a śledzenie
każdego dodawania w zestawie zmieniłoby przyrząd w coś, czego koszt i poprawność
trzeba by osobno mierzyć. Te miejsca pokrywa wyłącznie skan konstrukcji i ręczne
przeczytanie wypisu (§2). Sonda nie widzi też kodu, którego zestaw nie wykonuje
(skrypty Blendera), i wyniku na Pythonie 3.14.

## 5. Co zauważyłem przy okazji, ale nie tknąłem

**Klasa „doszedł" z 6.D341 też jest chwiejna, a raport 6.D341 podaje ją jako
odtworzoną identycznie** („42,655 s klasy »doszedł«" we wszystkich powtórzeniach).
W odtworzonej pętli 119 z 200 ziaren daje **42,654**, a 81 — 42,655; w sześciu
przebiegach z losowym ziarnem w §1 wyszło sześć razy 42,654. Albo przyrząd 6.D341
różni się od odtworzenia w szczególe, który tę sumę stabilizuje, albo trzy przebiegi
trafiły trzy razy w 42,655 (przy proporcji 81/200 zdarza się to mniej więcej raz
na piętnaście). Rozstrzygnąć tego nie umiem bez tamtego przyrządu. Liczba 42,655
w raporcie 6.D341 nie jest przez to błędna — jest **jedną z dwóch wartości**, które
ten sam rachunek daje. Wniosek tamtego raportu (36 % przyrostu) nie zależy od
trzeciego miejsca.

Sama klasa „istniał" zmienia się wraz z 74,417 → 74,418 o 1,3·10⁻⁵ względnie, tak
jak podało 6.D341 — to zmierzyło ono dobrze.
