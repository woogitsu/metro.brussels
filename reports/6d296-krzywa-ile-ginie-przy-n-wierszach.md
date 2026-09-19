# 6.D296 · Jeden kruchy dziś, ale dziewięć przy pięciu wierszach — i krzywa wyszła bez mutowania drzewa

**Data:** 19.09.2026 · **Gałąź:** `claude/sharp-ramanujan-jdr51o` · **Baza:** `bbb630a`

6.D284 zmierzyło, że na skraju okna stoi **jeden** wpis, ale ogon rozkładu odległości
jest długi, a praca dopisująca akapit dodaje kilka wierszy naraz, nie jeden. Ta pozycja
liczy krzywą.

---

## 1. Odpowiedź wychodzi z SAMYCH DYSTANSÓW — i to przeczytałem z kodu przed liczeniem

Dopisanie N wierszy między blokiem a pokryciem powiększa dystans tej pary **dokładnie
o N**. Wpis zostaje w klasie, dopóki choć jedna liczba pokrywająca mieści się w oknie.
Krzywa jest więc funkcją rozkładu odległości, a nie wynikiem symulacji:

> wpis ginie przy N  ⟺  każdy jego dystans `d` spełnia `d + N > SKRAJ_OKNA`

**Mutowania drzewa nie było.** Zapisałem to w przewidywaniach jako warunek obalenia:
gdybym musiał mutować, model byłby zły i to model szedłby do raportu zamiast liczb.
Nie musiałem.

Jest to druga pozycja z rzędu, w której odpowiedź dało się wyprowadzić z lektury kodu —
przy 6.D295 z dwóch krotek, tutaj z jednego zdania o oknie.

## 2. Krzywa i liczby, których żądało pole „Wyjście"

```
wpisow klasy `zbieg` z pokryciem: 56 | SKRAJ_OKNA: 20
kruchych DZIS (gina przy jednym wierszu): 1

N = 1: ginie  1, z tego DZIS NIEKRUCHYCH  0
N = 2: ginie  4, z tego DZIS NIEKRUCHYCH  3
N = 3: ginie  6, z tego DZIS NIEKRUCHYCH  5
N = 5: ginie  9, z tego DZIS NIEKRUCHYCH  8
```

**Zdanie „na skraju okna stoi jeden wpis" jest prawdziwe i myli.** Jeden — przy
dopisaniu jednego wiersza. Przy dwóch ginie **czworo**, przy pięciu **dziewięcioro**,
czyli co szósty wpis klasy. Dopisanie akapitu to w tym repozytorium typowo kilka
wierszy, więc liczbą opisującą realne ryzyko jest dziewięć, a nie jeden.

Kolumna „dziś niekruchych" jest tą, o którą pole pytało osobno, i pokazuje, że wzrost
nie bierze się z jednego znanego wpisu: przy pięciu wierszach **ośmioro z dziewięciorga**
to wpisy, których dzisiejsza bramka kruchości nie widzi.

## 3. Adresy

**N = 2** (gwiazdka: kruchy już dziś)

| | plik | wiersz | najbliższe | napis |
|---|---|---|---|---|
| | `test_bytecode_staleness.py` | 524 | 19 | `136` |
| | `test_dotnet_version.py` | 1561 | 19 | `2` |
| **\*** | `test_message_claims.py` | 1046 | 20 | `12` |
| | `test_message_claims.py` | 1047 | 19 | `1` |

**N = 3** — powyższe cztery oraz `mutation_sweep.py` w. 378 (najbl. 18, napis `0,224`)
i `test_mutation_sweep.py` w. 883 (najbl. 18, napis `15`).

**N = 5** — powyższe sześć oraz `test_bytecode_staleness.py` w. 516 (najbl. 17,
napis `147`), `test_report_claims.py` w. 1116 (najbl. 16, napis `1`)
i `test_suite_runtime_budget.py` w. 2363 (najbl. 16, napis `0,001`).

**Wpis kruchy dziś jest jeden i stoi w tym samym module, co bramka kruchości** —
`test_message_claims.py` w. 1046. To ta sama obserwacja, którą 6.D284 zapisało przy
`KRUCHE_ADRESY`; tutaj tylko potwierdzona z drugiej strony.

## 4. „Dopisanie N wierszy" NIE JEST jedną operacją

Spisałem to przed pomiarem, bo zmienia postać odpowiedzi. Skutek zależy od tego, **gdzie**
się dopisuje:

* wstawka między prozą a pokryciem po jednej stronie rusza **tylko tę parę**;
* wpis z pokryciem po **obu** stronach przeżyje wstawkę jednostronną, bo druga strona
  zostaje w oknie.

Rozkład stron: `('przed','za')` — **13**, `('za',)` — **33**, `('przed',)` — **10**.
Krzywa ma więc dwie gałęzie: górną (wstawka rusza każdą parę) i dolną (rusza jedną stronę).

```
   N   gorna   dolna
   1       1       1
   2       4       4
   3       6       6
   5       9       9
   8      18      16
  10      22      17
  15      29      21
  20      56      43
```

**Do N = 5 gałęzie są identyczne** — żaden wpis dwustronny nie ginie wcześniej niż przy
ośmiu wierszach. Liczby z §2 są więc jednoznaczne: dla N, o które pyta pole „Wyjście",
nie trzeba wybierać gałęzi.

**Koniec krzywej sprawdza model:** przy N = 20 gałąź górna zabija wszystkie 56, i musi,
bo każdy dystans jest co najmniej jeden, więc `d + 20 > 20` zachodzi zawsze. Punkt
skrajny wychodzący poprawnie jest dowodem, że arytmetyka zgadza się z semantyką okna.

## 5. Usterka MOJEGO modelu, znaleziona i pusta

Pierwsza wersja gałęzi dolnej liczyła jako ginące **wyłącznie wpisy jednostronne** —
zakładałem, że dwustronny przeżyje wstawkę zawsze. To nieprawda: przeżyje tylko wtedy,
gdy druga strona **mieści się w oknie**, a pokrycie dalsze niż okno może stać w tuple
dystansów, skoro do klasy kwalifikuje najbliższe.

Poprawiłem model i przeliczyłem. **Wynik nie zmienił się o ani jeden wpis**:

```
dwustronnych, ktorych JEDNA strona stoi juz poza oknem: 0
```

Usterka jest więc **realna w regule i pusta w tej populacji** — latentna, nie czynna.
Zapisuję ją, bo poprawka niczego nie zmieniła, a nie dlatego, że coś zmieniła: to drugi
raz dzisiaj, po strażach czytnika przy 6.D293, kiedy przezorność wychodzi zerem.

## 6. Kontrole, obie z pola „Weryfikacja"

```
KONTROLA NEGATYWNA — wpis o najblizszym pokryciu DWA wiersze od bloku
ma NIE trafic do grupy ginacej przy N = 1:
  wpisow o odleglosci 2: 10 | z nich w grupie N=1: 0  (ma byc 0)

KONTROLA PRZYRZADU — wpis o odleglosci ROWNEJ szerokosci okna
ma trafic do KAZDEJ z grup:
  wpisow o odleglosci 20: 1
  test_message_claims.py w.1046  w grupach N = [1, 2, 3, 5]
```

Negatywna wykonana na **dziesięciu** wpisach, nie na jednym — populacja odległości równej
dwa liczy dziesięć pozycji i żadna nie wpada do grupy N = 1.

## 7. Przewidywania spisane PRZED pomiarem

| # | przewidywanie | wynik |
|---|---|---|
| 1 | wpisów w klasie: 56 | trafione |
| 2 | ginących przy N = 1: 1 (liczba z 6.D284) | trafione — kontrola wobec tamtej pozycji |
| 3 | ginących przy N = 2: 1–3 | **PUDŁO**, jest 4 |
| 4 | ginących przy N = 5: 3–8 | **PUDŁO**, jest 9 |
| 5 | ginących przy N = 10: 8–16 | **PUDŁO**, jest 22 |
| 6 | wpisów dwustronnych: 5–15 | trafione (13) |
| 7 | krzywa najszybsza w okolicy połowy okna | **PUDŁO** — najszybsza na KOŃCU |
| 8 | symulacja nie będzie potrzebna | trafione |

**Trzy pudła liczbowe, wszystkie w dół.** Wracam więc do skłonności z 6.D287–6.D290
po dniu, w którym przy 6.D291 pomyliłem się w górę, a przy 6.D293 w obie strony.

**Pudło siódme jest ciekawsze od trzech pozostałych**, bo dotyczyło kształtu, a nie
wielkości. Przewidziałem najszybszy przyrost w okolicy `N` równego połowie okna; licząc
przyrost na dopisany wiersz wychodzi: `1→2` po trzy, `3→5` po półtora, `5→8` po trzy,
`10→15` po jeden i cztery dziesiąte, a `15→20` po **pięć i cztery dziesiąte**. Krzywa
jest najstromsza **na samym końcu**, bo ogon rozkładu (15..20 wierszy) mieści dziewięć
wpisów naraz. Środek okna jest najpłaszczy — dokładnie odwrotnie, niż zgadłem.

## 8. Czego świadomie nie zrobiono

- **Nie zmieniono `OKNO_PROZY`, `MAX_POGRUBIONYCH_BEZ_POKRYCIA` ani klas pokrycia**
  (pole „Poza zakresem").
- **Nie przesunięto czyjejkolwiek prozy bliżej jej stałej** — ani jednego z dziewięciu
  wpisów z §3. Pole zabrania, a 6.D284 zapisało powód: liczba krucha nie jest usterką
  sama w sobie, usterką było to, że nikt o niej nie wiedział.
- **Nie postawiono bramki** na krzywej ani na progu N.
- **Nie rozszerzono `KRUCHE_ADRESY`** o wpisy ginące przy dwóch i pięciu wierszach.
  Byłaby to zmiana zachowania cudzej bramki, a pozycja ma policzyć krzywą.
- **Nie tknięto `src/`.**

## 9. Zauważone przy okazji, nietknięte

Trzy z dziewięciu wpisów ginących przy pięciu wierszach stoją w **`test_message_claims.py`
i `test_bytecode_staleness.py`** — modułach, w których proza pomiarowa jest najgęstsza.
Czy gęstość prozy koreluje z odległością pokrycia, ta pozycja nie pyta; gdyby korelowała,
ryzyko nie rozkładałoby się równo po drzewie i krzywa z §2 byłaby średnią z dwóch różnych
populacji.
