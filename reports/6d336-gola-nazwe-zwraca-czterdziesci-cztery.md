# 6.D336 · Gołą nazwę zwraca CZTERDZIEŚCI CZTERY z dwustu czterech — nazwa klasy opisuje piątą część tego, co obejmuje

**Data:** 20.09.2026 · **Gałąź:** `claude/new-session-1xabcy` · **Baza:** `5bfa8f1`

6.D326 §4 zmierzyło, że z 428 czytników o nierozstrzygniętym kluczu **204 zwracają
zmienną spoza zasięgu funkcji** — i nazwało tę klasę `ZMIENNA SPOZA ZASIEGU`. Ta
pozycja **liczy** i reguły skoku z 6.D309 nie zmienia.

---

## 1. Kontrola przyrządu ZDANA — trzy podklasy sumują się do 204

```
populacja: 204   [6.D326: 204]

=== TRZY PODKLASY ===
   ARGUMENT              6
   ZMIENNA Z PETLI       7
   GLOBALNA            191
   SUMA                204   (populacja 204)   ZGADZA SIĘ
```

Suma jest **sprawdzona, a nie założona**, i wychodzi. Ale wychodzi **z konstrukcji**:
„globalna" jest trzecią klauzulą, czyli klasą resztkową, a pierwsza pasująca wygrywa.
§2 pokazuje, co do tej reszty wpada.

## 2. GŁÓWNE ZNALEZISKO: 160 z 204 nie zwraca żadnej gołej nazwy

Pole dzieli populację na argument, globalną i zmienną z pętli — czyli zakłada, że
w `return` stoi **nazwa**. Policzyłem, co tam stoi naprawdę:

```
=== RODZAJE WEZLA W `return` (wszystkie zwroty, 204 czytnikow) ===
   Constant          100        Attribute          11
   Name               54        Compare            11
   Subscript         42         BoolOp              9
   IfExp             39         Call                7
   BinOp             31         UnaryOp             5
   JoinedStr         12         Lambda              1
   SUMA zwrotow     322
```

```
czytnikow ZWRACAJACYCH gola nazwe:                 44
czytnikow NIEZWRACAJACYCH ani jednej golej nazwy: 160
razem: 204
```

**Nazwa stoi w pięćdziesięciu czterech z trzystu dwudziestu dwóch zwrotów, czyli
w jednym na sześć.** Klasa nazwana `ZMIENNA SPOZA ZASIEGU` obejmuje więc w większości
czytniki, w których **żadnej zmiennej w zwrocie nie ma**:

```
--- Constant     _bpy_na_poziomie_modulu       return True / return False / return None
--- Subscript    _apt_set_of                   return found[0]
--- IfExp        _declared_set                 return match.group(1) if match else None
--- BinOp        _doctor_z_atrapa              return wynik.stdout + wynik.stderr
--- JoinedStr    _concurrency_fault            return f'ziarno nie jest napisem: {group!r}'
```

Nie jest to zarzut wobec 6.D326: ta klasa powstała jako **gałąź `else`** w przejeździe
po łańcuchu — „nie ma klucza, nie ma dokąd skoczyć" — i taka jest dosłownie. Nazwa
`ZMIENNA SPOZA ZASIEGU` mówi jednak o **przyczynie, której nie zmierzono**, i to ta
nazwa weszła do pola tej pozycji jako założenie.

### 2.1 Sensowny podział dotyczy czterdziestu czterech, nie dwustu czterech

Trzy podklasy z pola, ograniczone do czytników, które **naprawdę zwracają nazwę**:

```
   ARGUMENT              6
   ZMIENNA Z PETLI       7
   GLOBALNA             31
                       ---
   RAZEM                44
```

Pozostałe **160** wpada do „globalnej" wyłącznie dlatego, że jest ona klauzulą
ostatnią. Podaję obie liczby — 191 i 31 — zamiast jednej, bo pierwsza jest
własnością mojej kolejności klauzul, a druga własnością drzewa.

### 2.2 Czym są te 44, przeczytane pełnym przeglądem funkcji

```
   NAZWA MODULOWA               12
   ROZPAKOWANIE KROTKI          11
   NIGDZIE W TYM PLIKU           9
   AUGASSIGN                     7
   PETLA                         6
```

**Jedenaście nazw dostaje wartość przez ROZPAKOWANIE KROTKI** (`out, ile = …`),
a siedem przez `+=`. Reguła jednego skoku z 6.D309 ogląda `ast.Assign` z celem
`ast.Name` — ani rozpakowanie, ani `AugAssign` tym nie są. **To są przypisania
w zasięgu, których reguła nie widzi**, a nie zmienne spoza zasięgu; osiemnaście
z czterdziestu czterech.

## 3. Dwie podliczby, których żądało pole

### 3.1 Globalne trafiające w stałą modułową o jawnym kształcie: ZERO

```
=== PODLICZBA 1: globalne trafiajace w STALA MODULOWA o jawnym ksztalcie ===
   0 z 191
```

**Dwanaście** zwracanych nazw jest nazwą modułową — `KSZTALT_C`, `KSZTALT_D`,
`KSZTALT_E` w `test_suite_runtime_budget.py`, `TERAZ` w `test_report_claims.py` —
ale **ani jedna z nich nie ma jawnego kształtu** w rozumieniu `ksztalt_wezla`:
wartością przypisania modułowego jest tam wywołanie (`re.compile`, `datetime.now`),
czyli dokładnie ten węzeł, którego klasyfikator nie rozstrzyga.

Pole żądało tej liczby także wtedy, gdy wynosi zero, i mówiło, co by to znaczyło.
**Wynosi zero, więc skok przez stałą modułową nie dałby nic** — przewidywanie R3
jest obalone, a warunek obalenia spisałem przed pomiarem i wypełniam go tutaj.

### 3.2 Zmienne z pętli rozstrzygalne w tej samej funkcji: JEDNA z siedmiu

```
=== PODLICZBA 2: zmienne z petli ROZSTRZYGALNE w tej samej funkcji ===
   1 z 7
      queue_row                        line           for      ELEMENT LISTA
```

Sześć pozostałych iteruje po wyrażeniu, którego kształtu elementu też nie da się
rozstrzygnąć bez skoku — czyli podklasa „z pętli" nie jest tańsza od „argumentu",
wbrew temu, co pole zakładało.

## 4. Przewidywania — jedno trafione, pięć obalonych

| # | przewidywanie | wynik |
|---|---|---|
| R1 | suma wyjdzie równo 204 | **trafione** (§1) |
| R2 | najliczniejszą podklasą będzie ARGUMENT | **OBALONE**: sześć, czyli najmniejsza |
| R3 | globalnych w stałą modułową co najmniej pięć | **OBALONE**: zero (§3.1) |
| R4 | zmiennych z pętli rozstrzygalnych więcej niż połowa | **OBALONE**: jedna z siedmiu |
| R5 | GLOBALNA będzie najmniejsza z trzech | **OBALONE**: największa, i to jako klasa resztkowa |
| R6 | jakaś nazwa jest i argumentem, i celem pętli | **OBALONE**: zero |

**Pięć obaleń z sześciu i wszystkie z jednego założenia**: że klasa
`ZMIENNA SPOZA ZASIEGU` mówi o zmiennych. Mówi o gałęzi `else`, a zmienna stoi
w zwrocie jednego czytnika na pięć.

## 5. Czego świadomie nie zrobiłem

Nie zmieniłem reguły skoku z 6.D309, nie czytałem wywołujących, nie przepisałem
żadnego czytnika, nie tknąłem `src/` ani `data/` — wszystko to stoi w polu „Poza
zakresem".

**Nie rozszerzyłem reguły skoku o rozpakowanie krotki i `AugAssign`**, choć §2.2
pokazuje, że osiemnaście z czterdziestu czterech nazw dostaje wartość właśnie tak.
Jest to zmiana reguły, a ta pozycja liczy.

**Nie przepisałem nazwy klasy `ZMIENNA SPOZA ZASIEGU`** ani w 6.D326, ani w polu tej
pozycji. §2 mówi liczbą, czego ta nazwa nie obejmuje.

## 6. Co zauważyłem przy okazji, ale nie tknąłem

Sto zwrotów to `Constant` — `return None`, `return True`, `return False`. Ich kształt
jest **znany bez żadnego skoku** i jedna klauzula w `ksztalt_wezla` zdjęłaby je
z klasy nierozstrzygniętych. Klasa 204 spadłaby wtedy o tyle, ile czytników zwraca
wyłącznie stałe — trzynaście według rozkładu zestawów rodzajów. Dopisanie tej
klauzuli jest zmianą klasyfikatora, więc go nie dopisuję; zapisuję liczbę, żeby
następna pozycja nie zaczynała od zera.
