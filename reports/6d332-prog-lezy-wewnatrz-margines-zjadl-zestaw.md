# 6.D332 · Próg 440 s leży WEWNĄTRZ — a margines zjadł ZESTAW, nie maszyna, i to nie przyrostem testów

**Data:** 20.09.2026 · **Gałąź:** `claude/new-session-1xabcy` · **Baza:** `1a21e8a`

Przy PR #731 ten sam commit `139fbe6` dał w dwóch próbach tego samego przebiegu
**464,149 s** (czerwone) i **362,590 s** (zielone) — 101 sekund różnicy przy zerowej
różnicy treści. Ta pozycja **mierzy i rozdziela dwie przyczyny**. Zmiana progu jest
decyzją właściciela i jest wykluczona osobno; 6.D313 zmierzyło ciasnotę progu i go
nie ruszyło.

Źródło to samo, co wzorca i co 6.D313: artefakty `czas-zestawu` z `python-tests.yml`,
pobrane wprost z API po identyfikatorze. **Pobrałem wszystkie 570 niewygasłych, nie
próbkę** — 6.D313 miało ich 538.

---

## 1. Kontrola przyrządu ZDANA co do trzeciego miejsca

```
=== KONTROLA PRZYRZADU: przebieg 35514424835 ===
   proba 1: cpu=464.149 s  sciana=350.085  runner=metro-wsl-DOM-NEW-01  commit=139fbe6
   proba 2: cpu=362.590 s  sciana=256.860  runner=metro-wsl-DOM-NEW-01  commit=139fbe6
```

Pole żądało dokładnie tych dwóch liczb. **Obie próby padły na TEJ SAMEJ maszynie** —
czego pole nie żądało, a co przesądza, że rozrzut nie jest różnicą między maszynami.
To potwierdza niezależnie tytułowe zdanie 6.D313.

## 2. Trzy liczby, których żądało pole

### 2.1 Ile dołożył zestaw od dnia ustawienia progu

`SUITE_CPU_BUDGET_S = 440.0` weszło **14.09.2026**, commitem `2db590a`, i od tego dnia
nie było ruszane. Mediana dnia, liczona na artefaktach, nie szacowana:

```
   mediana CPU:    209.425  ->  357.408  s      (+147.983)
   testow:         2471     ->  2664
   CPU na test:    0.08475  ->  0.13416  s
```

**Zestaw dołożył +147,983 s CPU.** A rozbity na przyczyny — bo pole ostrzegało, żeby
odróżnić „zestaw urósł" od „ten sam zestaw chodził wolniej":

```
   gdyby tylko PRZYBYLO TESTOW przy dawnym koszcie:  225.782 s  (+16.357)
   reszta, czyli DROZSZY POJEDYNCZY TEST:                        +131.626 s
   RAZEM ZESTAW:                                                 +147.983 s
```

**Przyrost testów odpowiada za jedenaście procent, a za osiemdziesiąt dziewięć —
podrożenie pojedynczego testu.** Testów przybyło 193 (7,8 %), a koszt jednego wzrósł
o 58 %. To jest własność tego zestawu, a nie liczby testów: czytniki prozy, historii
gita i drzewa raportów pracują na korpusie, który rośnie szybciej niż sam zestaw.

### 2.2 Jaki jest dziś rozrzut CPU tego samego commita

Grupuję po **commicie**, nie po parze (liczba testów, liczba modułów) jak wzorzec
6.D313 — bo pytanie dotyczy rozrzutu TEGO SAMEGO przebiegu, a nie tego samego
rozmiaru zestawu:

```
   grup (commitow z >=2 probami): 5 ; prob w nich: 11
   mediana ilorazu: 1.280   maksimum: 2.166
      2.166  commit 7cfabea  prob=2  238.900 -> 517.499 s
      1.337  commit 4f3ed3a  prob=3  366.164 -> 489.566 s
      1.280  commit 139fbe6  prob=2  362.590 -> 464.149 s
      1.126  commit 9d97eda  prob=2  201.193 -> 226.537 s
      1.038  commit ca25d39  prob=2  206.802 -> 214.757 s
```

**Populacja jest mała i mówię to wprost: pięć grup, jedenaście prób.** Ponowienia są
w tym repozytorium rzadkie, więc rozrzut „tego samego commita" stoi na tylu pomiarach,
ile ich jest — nie dobieram do niego grup o innym kształcie, żeby liczba wyglądała
solidniej.

### 2.3 Werdykt

```
   margines w dniu ustawienia:  440.0 - 209.425 = 230.575 s
   margines dzis:               440.0 - 357.408 =  82.592 s
   iloraz, przy ktorym prog pada dzis: 1.2311

WERDYKT: prog 440.0 s lezy WEWNATRZ sumy mediany i rozrzutu (457.482 s).
```

**Próg leży WEWNĄTRZ, i to nie przy rozrzucie skrajnym, tylko przy MEDIANIE.**
Dzisiejsza mediana pomnożona przez medianę rozrzutu daje 457,482 s — o 17,482 s nad
progiem. Pada on przy ilorazie **1,2311**, a mediana rozrzutu wynosi 1,280. Czyli
**typowe ponowienie dzisiejszego commita przekracza próg**, a nie tylko wypadek.

Mnożę, a nie dodaję, i to jest treść, nie formalność: przyrost zestawu jest
addytywny (sekundy pracy), a rozrzut maszyny multiplikatywny (mnoży czas, nie pracę).
Zsumowanie ich dałoby liczbę, która nie opisuje żadnego przebiegu — pole ostrzegało
przed tym wprost.

## 3. GŁÓWNE ZNALEZISKO: margines zjadł ZESTAW, a maszyna dołożyła resztę

Pole żądało powiedzenia, ile z marginesu zjadł zestaw, a ile maszyna — także gdy
jedna z wielkości wynosi zero.

```
   margines w dniu ustawienia progu:           230.575 s
   zjadl ZESTAW (addytywnie):                  147.983 s   = 64 %
   dokłada MASZYNA przy medianie rozrzutu:     100.074 s
                                              ---------
   razem                                       248.057 s   > 230.575 s
```

**Żadna z dwóch wielkości nie jest zerem i żadna sama nie wystarcza.** Zestaw zjadł
prawie dwie trzecie marginesu, ale zostawił 82,6 s — a zatrzymanie się na tym byłoby
nieprawdą, bo próg pada przy ilorazie 1,2311, czyli poniżej dzisiejszej mediany
rozrzutu. Czerwień bierze się z **obu naraz**: 248,057 s potrzeby przy 230,575 s
marginesu.

**Przewidywanie Z5 jest OBALONE i spełniam warunek spisany przed pomiarem.** Z5
mówiło, że maszyna zjada więcej niż zestaw. Zjada mniej: 100,074 s wobec 147,983 s.
**Próg zestarzał się więc z powodu PRACY, nie maszyny** — i to o 147,983 s, z czego
131,626 s to podrożenie pojedynczego testu, a nie przyrost ich liczby.

### 3.1 Maszyna nie pogorszyła się — pogorszyła się wobec niej praca

Stosunek CPU do ściany jest wskaźnikiem maszyny, a nie zestawu: mówi, ile rdzeni
przebieg naprawdę dostał.

```
   2026-09-11  mediana 1.847  max 2.091  (n=85)
   2026-09-14  mediana 1.520  max 1.775  (n=42)    <- dzien ustawienia progu
   2026-09-17  mediana 1.612  max 1.793  (n=41)
   2026-09-19  mediana 1.337  max 1.620  (n=58)
   2026-09-20  mediana 1.370  max 1.567  (n=48)
```

**Stosunek SPADŁ**, z 1,847 w szczycie do 1,370 dzisiaj — i jego maksimum spadło tak
samo (2,091 → 1,567). Maszyna nie jest dziś bardziej obciążona niż wtedy; jest mniej.
Zdanie „to maszyna" nie ma więc oparcia w żadnym z dwóch odczytów: ani w rozbiciu
marginesu z §3, ani w tym szeregu.

## 4. Przewidywania — cztery trafione, jedno obalone, jedno z zastrzeżeniem

| # | przewidywanie | wynik |
|---|---|---|
| Z1 | kontrola przejdzie co do trzeciego miejsca | **trafione** (§1) |
| Z2 | werdykt brzmi „leży WEWNĄTRZ" | **trafione**, i to przy medianie, nie przy maksimum |
| Z3 | przyrost zestawu dodatni, ale mniejszy niż 60 s | **OBALONE**: +147,983 s, czyli dwa i pół raza więcej |
| Z4 | rozrzut tego samego commita przekroczy 1,25 | **trafione**: mediana 1,280 |
| Z5 | maszyna zjada z marginesu więcej niż zestaw | **OBALONE**: 100,074 s wobec 147,983 s (§3) |
| Z6 | znajdzie się commit z trzema albo więcej próbami | **trafione**, ale **dokładnie jeden** — `4f3ed3a` |

**Z3 i Z5 padły z tej samej przyczyny**, którą zapisuję razem: obie stawiały na
maszynę i obie nie doceniły, jak szybko rośnie koszt jednego testu. Zapis „mniej niż
60 s" wziąłem z przyrostu liczby testów, bo to jedyna wielkość, którą widać w wyniku
zestawu — a ona odpowiada za 16 z 148 sekund.

## 5. Czego świadomie nie zrobiłem

- **Nie ruszyłem `SUITE_CPU_BUDGET_S` ani żadnej podłogi czasu.** Zapadki górne
  w tym projekcie wyłącznie się obniża, a pomiar mówiący, że próg jest ciasny,
  nie jest powodem, żeby go podnieść — jest powodem, żeby wiedzieć, co go zjada.
  Tak samo rozstrzygnęło 6.D313.
- **Nie przyspieszałem zestawu.** §2.1 mówi, gdzie siedzi koszt; co z tym zrobić,
  jest decyzją właściciela.
- **Nie zmieniłem workflowa**, nie tknąłem `src/` ani `data/`.
- **Nie dobrałem grup do rozrzutu.** Pięć grup to mało (§2.2) i tak to zapisuję,
  zamiast rozciągać definicję grupy, aż liczba zrobi się okazalsza.

## 6. Co zauważyłem przy okazji, ale nie tknąłem

`7cfabea` ma iloraz **2,166** przy dwóch próbach — 238,900 s wobec 517,499 s. Wyższa
z tych liczb stoi w drzewie jako `INCYDENT_DOCKER_CPU = 517.499`, czyli jest już
nazwana i opisana; niższa nie stoi nigdzie. Rozrzut tego jednego commita jest **sam
w sobie większy niż cały dzisiejszy margines** i gdyby wszedł do mediany grup,
werdykt z §2.3 nie zmieniłby się, tylko zrobił mocniejszy. Zapisuję, bo to jedyna
grupa, w której jedna próba jest w drzewie nazwana, a druga nie.
