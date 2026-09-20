# 6.D305 · Krzywa opisuje JEDNĄ populację — a skupienie, które pozycję wywołało, tłumaczy sama liczebność

**Data:** 20.09.2026 · **Gałąź:** `claude/sharp-ramanujan-jdr51o` · **Baza:** `faf7874`

6.D296 podało krzywą „ile wpisów klasy `zbieg` ginie przy dopisaniu N wierszy" jako
jedną liczbę na N. Ta pozycja pyta, czy ta liczba opisuje drzewo, czy jest **średnią
z dwóch różnych populacji** — bo adresy z §3 tamtego raportu wyglądały na skupione
w dwóch modułach.

**Odpowiedź: opisuje jedną populację.** Ale dojście do niej wymagało zadania pytania
o skupienie **dwa razy**, i te dwa razy dają odpowiedzi różniące się o rząd wielkości.

---

## 1. Przesłanka bloku była nieprawdziwa i została poprawiona PRZED tą pozycją

Blok i wiersz tabeli mówiły „**trzy** z dziewięciu wpisów stoją w `test_message_claims.py`
i `test_bytecode_staleness.py` — modułach o **najgęstszej prozie pomiarowej**". Oba
zdania zmierzyłem jako nieprawdziwe i poprawiłem osobnym commitem (PR #713): jest
**cztery**, po dwa w każdym, a „najgęstsza proza" jest fałszem we wszystkich mierzonych
miarach. Ta pozycja pracuje więc na przesłance poprawionej i **nie ma już czego
potwierdzać** — ma policzyć, czy skupienie w ogóle istnieje.

## 2. Tabela po modułach, której żądało pole „Wyjście"

```
kontrola przyrzadu: suma wpisow po modulach = 56  zapadka POKRYTYCH_ZBIEGIEM_CYFR = 56
modulow z wpisami klasy zbieg: 22
ginacych przy N=5 razem: 9

modul                               wpis  mediana  gin5      G1        G2
test_dead_constants_csharp.py         12      6.0     0     157    0.2259
test_suite_runtime_budget.py           8      4.5     1     687    0.2831
test_report_claims.py                  5     13.0     1     580    0.2477
test_mutation_sweep.py                 4      3.5     1     503    0.1426
test_report_hygiene.py                 4      3.5     0     630    0.3573
test_message_claims.py                 3     19.0     2     474    0.2531
mutation_sweep.py                      2     11.5     1     410    0.1942
test_assertion_gate.py                 2      5.5     0     497    0.2345
test_bytecode_staleness.py             2     18.0     2     174    0.1585
test_mass_copies.py                    2      2.5     0      31    0.1703
csharp_pins.py                         1     11.0     0      33    0.1107
csharp_test_methods.py                 1     13.0     0      69    0.1184
test_all.py                            1      6.0     0      97    0.1273
test_bin_path_framework.py             1      3.0     0      74    0.1460
test_csharp_assertions.py              1      7.0     0     273    0.3408
test_dotnet_version.py                 1     19.0     1     310    0.1711
test_field_paths.py                    1      4.0     0     916    0.3096
test_game_needle_specificity.py        1      4.0     0     227    0.2940
test_json_required.py                  1      2.0     0      54    0.1770
test_prose_counts.py                   1     15.0     0     400    0.2851
test_provenance_classes.py             1      2.0     0     120    0.1344
test_t401_citation.py                  1      6.0     0     100    0.2506
```

`G1` to liczba bloków `proza` w module, `G2` — ta sama liczba na wiersz pliku.
**Kontrola przyrządu z pola „Weryfikacja" zdana:** suma wpisów po modułach daje 56,
czyli dokładnie tyle, ile zapadka populacji, więc czytnik nie gubi modułu ani nie
liczy żadnego dwa razy. Suma ginących daje dziewięć — liczbę z §2 raportu 6.D296.

## 3. Rozstrzygnięcie o korelacji: NIE KORELUJE, i to samo we wszystkich miarach

Gęstość prozy **nie jest jedną wielkością**, więc policzyłem ją trzema sposobami.
Spisałem to przed pomiarem właśnie dlatego, że od wyboru miary mógł zależeć wynik.

```
G1 bloki             vs MEDIANA odleglosci: rho = +0.158  p = 0.4824  n = 22
G2 bloki/wiersz      vs MEDIANA odleglosci: rho = +0.032  p = 0.8918  n = 22
G4 wierszy pliku     vs MEDIANA odleglosci: rho = +0.202  p = 0.3659  n = 22
```

Próg postawiłem przed pomiarem: „koreluje" znaczy `|ρ| ≥ 0,5` przy `p < 0,05`.
**Żadna miara nie dochodzi nawet w połowie do progu po współczynniku, a żadne `p` nie
zbliża się do progu istotności.** Werdykt jest ten sam we wszystkich trzech, więc nie
trzeba mówić „zależy od miary" — a wielokrotność miar była w definicjach po to, żeby tę
możliwość **sprawdzić**, a nie założyć.

`ρ` liczone Spearmanem z poprawką na rangi wiązane, `p` z testu permutacyjnego na
20 000 losowań, ziarno 20260919.

## 4. TO SAMO PYTANIE O SKUPIENIE, ZADANE DWA RAZY — i odpowiedzi różnią się o rząd wielkości

To jest sedno tej pozycji i powód, dla którego warto ją było wziąć.

```
wpisow ogolem 56 ; ginacych 9 ; w parze 4
wpisow w parze: 5

(a) KOLOWY   — para nazwana z gory:              p = 0.00150
(b) NIEKOLOWY — najwieksza DOWOLNA para:         obserwacja 4, p = 0.70950
```

**(a) wygląda jak mocny dowód skupienia i jest bezwartościowy.** Te dwa moduły zostały
nazwane **dlatego**, że stoją w nich ginące wpisy; hipoteza zerowa, która ich nie zna,
odpowiada więc na pytanie, którego nikt nie zadał. To ta sama usterka mianownika, którą
6.D292 zmierzyło na nazwach wszechobecnych, przesunięta o krok: nie liczy się za dużo
wpisów, tylko **za mało modułów w hipotezie zerowej**.

**(b) jest odpowiedzią.** Przy losowym rozrzuceniu dziewięciu ginących po 56 wpisach —
z zachowaniem liczebności modułów i niczego więcej — **jakaś** para modułów zbiera
czworo lub więcej w **71 % losowań**. Obserwacja „cztery z dziewięciu w dwóch modułach"
jest więc dokładnie tym, czego liczebność każe się spodziewać.

Podaję obie liczby, a nie samą drugą, bo różnica między nimi jest treścią: `p = 0,0015`
i `p = 0,7095` opisują **tę samą obserwację**, a różni je wyłącznie to, czy moduły
nazwano przed losowaniem, czy po nim.

## 5. Odpowiedź na pytanie pola, wprost

**TAK, krzywa z 6.D296 opisuje jedną populację.** Nie jest średnią z dwóch.

Podstawa, w kolejności wagi:

1. mediana odległości pokrycia **nie rośnie z gęstością prozy** w żadnej z trzech miar
   (`ρ` od +0,032 do +0,202, `p` od 0,366 do 0,892, n = 22) — podział na „moduły gęste"
   i „resztę" nie daje dwóch rozkładów odległości;
2. obserwowane skupienie ginących jest **zgodne z liczebnością** (`p = 0,7095`);
3. przesłanka, która pozycję wywołała, została wcześniej zmierzona jako nieprawdziwa
   w obu członach.

Krzywej **nie rozbijam** i rozbicia nie proponuję.

## 6. Przewidywania spisane PRZED pomiarem

| # | przewidywanie | wynik |
|---|---|---|
| Q1 | rozstrzygnięcie: NIE KORELUJE | trafione |
| Q2 | moduł z największą liczbą wpisów `zbieg` to `test_message_claims.py` | **OBALONE** — `test_dead_constants_csharp.py` z dwunastoma; `test_message_claims.py` ma trzy i jest szósty |
| Q3 | modułów z wpisami: 15–35 | trafione (22) |
| Q4 | kontrola przyrządu (suma = 56) przejdzie | trafione |
| Q5 | krzywa opisuje jedną populację | trafione |
| Q6 | mediana w `test_message_claims.py` NIE będzie najwyższa | **OBALONE** — 19,0 jest najwyższa w zestawie |

**Oba obalenia są tym samym błędem:** patrzyłem na `test_message_claims.py` jak na
moduł wyjątkowy, bo to jego adresy widziałem wypisane przy 6.D296. Nie jest wyjątkowy
pod względem liczby wpisów (szósty z dwudziestu dwóch), a jest pod względem mediany —
czyli dokładnie odwrotnie, niż zgadłem w obu punktach.

I to jest **ta sama pułapka, w którą wpadł §9 raportu 6.D296**: patrzy się na moduł,
w którym stoi najdalszy wpis, widzi wysoką medianę i bierze ją za własność modułu.
Przewidywanie Q6 postawiłem, żeby tej pułapki uniknąć — i wpadłem w nią z drugiej
strony, zakładając, że skoro §9 się mylił, to mediana **nie** będzie wyjątkowa.

## 7. Czego świadomie nie zrobiono

- **Nie rozbito krzywej z 6.D296 na dwie** i nie zaproponowano rozbicia — pole zabrania,
  a pomiar nie daje po temu powodu.
- **Nie zmieniono `OKNO_PROZY`, `SKRAJ_OKNA` ani klas pokrycia**; nie przesunięto
  czyjejkolwiek prozy bliżej jej stałej.
- **Nie postawiono bramki** na korelacji ani na rozkładzie po modułach.
- **Nie policzono, czy przynależność do modułu tłumaczy odległość w ogóle** — to pytanie
  szersze niż gęstość prozy i pole go nie stawia; zapisane w §8.
- **Nie tknięto `src/`, `data/` ani prozy w `tools/tests/`.**

## 8. Zauważone przy okazji, nietknięte

1. **`test_dead_constants_csharp.py` ma 12 z 56 wpisów klasy `zbieg`** — ponad dwa razy
   więcej niż jakikolwiek inny moduł, przy zupełnie przeciętnej prozie. Jego mediana
   wynosi 6,0, czyli poniżej mediany całości, a ginie z niego przy pięciu wierszach
   **zero** wpisów. Kandydat na populację odstającą o wiele wyraźniejszy niż para
   z §9 raportu 6.D296 — i nikt na niego nie patrzył, bo nie stał na żadnej liście.
2. **Czternaście z dwudziestu dwóch modułów ma dokładnie jeden wpis.** Mediana z jednego
   wpisu jest tym wpisem, więc połowa punktów w korelacji z §3 nie jest medianą
   w żadnym użytecznym sensie. Werdykt tego nie potrzebuje (`p ≥ 0,366`), ale liczba
   punktów mówiących cokolwiek o rozkładzie **wewnątrz** modułu wynosi osiem, nie
   dwadzieścia dwa.
3. **W korpusie nie ma jednej, nazwanej definicji „liczby wierszy pliku"** — `split("\n")`
   i `splitlines()` różnią się o jeden na pliku kończącym się znakiem nowego wiersza,
   co przy G2 przesuwa moduł o jedno miejsce w rankingu. Każda bramka liczy po swojemu.
