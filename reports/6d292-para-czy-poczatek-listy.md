# 6.D292 · Para wystarcza — ale kryterium, którym to sprawdzałem, wyrzuca z niej połowę

**Data:** 19.09.2026 · **Gałąź:** `claude/sharp-ramanujan-jdr51o` · **Baza:** `579c5a4`

`WSZECHOBECNE_NAZWY` liczy dwie nazwy — `MIN_REPORTS` i `test_all.py` — i została
przypięta przy 6.D283 **z lektury przykładów**, a nie z rozkładu. Ta pozycja pyta,
czy para wystarcza, czy jest początkiem listy.

Pole „Wyjście" podaje próg samo: nazwy stojące „w więcej niż jednej czwartej jednych
i drugich". Nie miałem tu więc swobody definiowania slajsu — i zapisuję to, żeby nie
przypisywać sobie dyscypliny tam, gdzie nie była potrzebna. Blok napisałem sam przy
6.D283, więc próg też jest mój.

---

## 1. Rozkład przy mianowniku, który podaje blok: CAŁY KORPUS

```
uniwersum: moduly 139 + zapadki 91 = 230
korpus: komunikatow 1033, raportow 418
prog (1/4): komunikaty 258.25 | raporty 104.50

powyzej progu W OBU NARAZ: 1
   test_all.py              kom  305 ( 29.5%) | rap  242 ( 57.9%)
   [para] MIN_REPORTS      kom  230 ( 22.3%) | rap   40 (  9.6%)  -> NIE PRZECHODZI
   [para] test_all.py      kom  305 ( 29.5%) | rap  242 ( 57.9%)  -> PRZECHODZI
```

**Nazwą przekraczającą próg w obu zbiorach jest JEDNA, i nie jest nią połowa pary.**
Nazwę **MIN_REPORTS** niesie 22,3 % komunikatów i 9,6 % raportów — poniżej progu
po obu stronach. Gdyby czytać kryterium z bloku dosłownie, wniosek brzmiałby: **zbiór jest
o jedną nazwę za duży**, a `MIN_REPORTS` trzeba zdjąć.

Ten wniosek jest nieprawdziwy, i pokazuje to następny pomiar.

## 2. Ten sam próg przy mianowniku, który bramka NAPRAWDĘ czyta

`WSZECHOBECNE_NAZWY` nie jest czytane nad całym repozytorium. Czyta je
`klasy_sladu`, i tylko wewnątrz populacji „commit zgłasza wykonaną kontrolę
**i** ma ślad w plikach". Ta populacja liczy dziś **481** commitów, nie 1033.

```
populacja bramki: 481 commitow
   [para] MIN_REPORTS      189 / 481 ( 39.3%)
   [para] test_all.py      220 / 481 ( 45.7%)
```

**W populacji, w której zbiór jest używany, obie nazwy przekraczają jedną czwartą
z zapasem.** Udział nazwy **MIN_REPORTS** skacze z 22,3 % na 39,3 %, bo populacja jest
zbudowana z commitów dopisujących raport — a każdy taki commit podnosi tę zapadkę.
Dokładnie to mówi komentarz przy stałej od 6.D283; czego tamten komentarz nie miał,
to liczby.

**Różnica między §1 a §2 nie jest niuansem — jest całą odpowiedzią tej pozycji.**
Ten sam próg, ta sama nazwa, dwa mianowniki, dwa przeciwne werdykty. Mianownik
„cały korpus" mierzy, jak często nazwa pada w repozytorium; mianownik „populacja
bramki" mierzy, jak mało informacji nazwa niesie **tam, gdzie decyduje**. Pytanie
o nazwę wszechobecną jest pytaniem drugiego rodzaju.

## 3. Najbliżsi kandydaci — w populacji bramki, nie w korpusie

| nazwa | w populacji bramki | udział |
|---|---|---|
| **MINIMUM_DETAIL_BLOCKS** | 82 / 481 | 17,0 % |
| `test_mutation_sweep.py` | 21 / 481 | 4,4 % |
| `test_backlog.py` | 21 / 481 | 4,4 % |
| `test_ci_workflows.py` | 16 / 481 | 3,3 % |
| `test_tree_walks.py` | 13 / 481 | 2,7 % |
| `test_report_claims.py` | 12 / 481 | 2,5 % |

Najbliższy kandydat stoi na **17,0 %**, czyli wyraźnie pod progiem, a następny już
na 4,4 %. Między parą (39,3 % i 45,7 %) a resztą jest **przerwa ponad dwukrotna**,
i to ona rozstrzyga, a nie sam próg.

## 4. Ile commitów zmieniłoby klasę po dołożeniu nazwy

```
  wasko    baza: tylko_wszechobecne  42
     + MINIMUM_DETAIL_BLOCKS      ->  45 (+3)
     + test_mutation_sweep.py     ->  51 (+9)
     + test_backlog.py            ->  44 (+2)
     + test_ci_workflows.py       ->  43 (+1)
     + test_tree_walks.py         ->  43 (+1)
  szeroko  baza: tylko_wszechobecne  55
     + MINIMUM_DETAIL_BLOCKS      ->  60 (+5)
     + test_mutation_sweep.py     ->  66 (+11)
     + test_backlog.py            ->  57 (+2)
     + test_ci_workflows.py       ->  59 (+4)
     + test_tree_walks.py         ->  56 (+1)
```

**Kierunek zmiany jest treścią, nie szczegółem.** `tylko_wszechobecne` to podzbiór
klasy `dotyczy`: commity, których zgodność raportu z komunikatem opiera się WYŁĄCZNIE
na nazwach nic nieznaczących. Dołożenie nazwy do zbioru **przenosi commity z dowodu
do podejrzenia** — nie naprawia bramki, tylko osłabia to, co uznaje za związek.

Dlatego liczba ma sens tylko razem z udziałem. `test_mutation_sweep.py` przenosi
najwięcej (9 i 11), a stoi na 4,4 % — przeniósłby więc dziewięć commitów na podstawie
nazwy, która wszechobecna **nie jest**. `MINIMUM_DETAIL_BLOCKS`, jedyny kandydat
z dwucyfrowym udziałem, przenosi 3 i 5.

## 5. Kontrola negatywna, której żądało pole „Weryfikacja"

Żądanie brzmiało: nazwa dołożona do zbioru **musi zmienić** liczbę commitów zgodnych
wyłącznie przez nazwy wszechobecne — jeśli nie zmienia, zbiór nie jest czytany tam,
gdzie się wydaje.

**Zmieniła się przy każdej z pięciu nazw, w obu trybach — dziesięć par liczb, żadna
zerowa.** Kontrola jest więc zdana na pięciu punktach, a nie na jednym; najmniejsza
zmiana to +1, największa +11. Zbiór jest czytany dokładnie tam, gdzie miał być.

## 6. Rozstrzygnięcie: PARA WYSTARCZA

Zapisane z liczbą przy nim, jak żąda pole „Skończone, gdy":

**Para wystarcza, bo najbliższy kandydat stoi na 17,0 % w populacji bramki przy
39,3 % i 45,7 % dla pary — przerwa jest ponad dwukrotna — a jego dołożenie
przeniosłoby z dowodu do podejrzenia 3 commity wąsko i 5 szeroko.**

Rozstrzygnięcie **nie zmienia zbioru**: pole „Poza zakresem" zabrania tego nazwanym
słowem, a pozycja miała odpowiedzieć tylko, czy jest o czym decydować. Odpowiedź
brzmi: nie ma.

## 7. Co ta pozycja prostuje we własnym bloku

Pole „Wyjście" każe liczyć udział „w komunikatach i w raportach" bez powiedzenia,
**których**. Przy dosłownym odczytaniu (cały korpus) kryterium wyrzuca `MIN_REPORTS`
ze zbioru, do którego tamta pozycja go wpisała — czyli **obala samo siebie**.
Napisałem ten blok przy 6.D283 i próg jest mój, więc prostuję go tutaj, zamiast
dopasować pomiar do zdania.

Zdanie, które zostaje: **nazwa jest wszechobecna nie wtedy, gdy często pada
w repozytorium, tylko wtedy, gdy niesie mało informacji w populacji, w której
bramka po nią sięga.** Obie liczby są w §1 i §2 i można je porównać.

## 8. Przewidywania spisane PRZED pomiarem

| # | przewidywanie | wynik |
|---|---|---|
| 1 | nazw w uniwersum: 200–400 | trafione (230) |
| 2 | powyżej progu w komunikatach: 2–5 | **PUDŁO**, jedna |
| 3 | powyżej progu w raportach: 3–8 | **PUDŁO**, jedna |
| 4 | powyżej progu w obu naraz: 2–3 | **PUDŁO**, jedna — i nie jest nią cała para |
| 5 | trzecią nazwą będzie `test_backlog.py` albo `MINIMUM_DETAIL_BLOCKS` | trzeciej nazwy NIE MA; ale `MINIMUM_DETAIL_BLOCKS` jest najbliższym kandydatem, a `test_backlog.py` trzecim |
| 6 | dla nazwy tuż za progiem mniej niż 10 commitów zmieni klasę | trafione (3 i 5) |
| 7 | kontrola negatywna zmieni liczbę | trafione, na pięciu nazwach |

**Trzy pudła z siedmiu, wszystkie w tę samą stronę: spodziewałem się szerszej
czołówki, niż jest.** To ta sama skłonność co przy 6.D287–6.D290, tylko tutaj
dotyczy rozkładu, a nie populacji.

Przewidywanie 5 **nie jest trafieniem** i nie zapisuję go jako trafienie: pytałem,
która nazwa będzie trzecia, a trzeciej nie ma. To, że obie wytypowane nazwy stoją
w czołówce kandydatów, jest o innym pytaniu niż to, które zadałem.

## 8a. Dlaczego nazwy zapadek stoją tu miejscami BEZ grawisów

Pierwsza wersja tego raportu zapaliła
`test_every_constant_quoted_in_a_report_carries_the_value_from_the_code`. Wzorzec
`CLAIM` czyta nazwę stałej w grawisach, po której w tym samym wierszu stoi liczba,
jako **twierdzenie o wartości tej stałej** — a w tym raporcie liczba obok nazwy jest
CZĘSTOŚCIĄ jej występowania. Podłoga raportów stoi dziś na 419; procenty z §1 i §3
nie mówią o niej nic.

**Bramka ma rację, że pyta, i nie ma jak tego rozstrzygnąć**, bo różnica siedzi
w sensie zdania, a nie w jego kształcie. Poprawiłem więc zapis, nie bramkę: tam,
gdzie tuż za nazwą idzie procent, nazwa stoi wytłuszczona zamiast w grawisach.
Wyjątku do listy nie dopisałem — uciszyłby wzorzec także tam, gdzie miałby rację.

Odwrócenie kolejności (liczba przed nazwą) **nie pomaga i sprawdziłem to
przebiegiem**: wzorzec patrzy od nazwy w PRAWO, więc „nazwę X niesie 22,3 %" trafia
tak samo jak „X stoi w 22,3 %". Pierwsza poprawka poszła właśnie tą drogą i dała
pięć czerwieni zamiast czterech, bo akapit tłumaczący problem sam reprodukował
kształt, który opisuje.

Jest to ta sama rodzina co §7: raport o zapadkach jest tekstem, w którym nazwa
zapadki bywa PRZEDMIOTEM, a nie CYTATEM — i piszący musi to rozróżnić za bramkę.

## 9. Czego świadomie nie zrobiono

- **Nie zmieniono `WSZECHOBECNE_NAZWY`** — pole „Poza zakresem" zabrania, a pomiar
  i tak mówi, że nie ma czego zmieniać.
- **Nie zmieniono `MIN_SLAD_*`** ani żadnej zapadki tej rodziny.
- **Nie postawiono bramki** na rozkładzie częstości: pole „Wyjście" żąda trzech liczb
  i listy, nie sita w drzewie.
- **Nie poprawiono progu w bloku 6.D292.** Prostuję go w §7 prozą, bo zmiana pola
  „Wyjście" w pozycji, którą właśnie wykonuję, zacierałaby ślad tego, co pozycja
  mierzyła — a to jest dokładnie rodzina usterek, którą 6.D288 opisało na cudzym
  zdaniu.
- **Nie tknięto `src/`.**

## 10. Zauważone przy okazji, nietknięte

Nazwę **MINIMUM_DETAIL_BLOCKS** niesie 17,0 % commitów populacji bramki, a w całym
korpusie 11,5 % — i rośnie przy każdym uzupełnieniu kolejki, których samego 19.09.2026 było
trzy. Jest to zapadka o dynamice podobnej do `MIN_REPORTS`: podnosi ją nie treść
pozycji, tylko sam fakt dopisania bloku. Czy próg jednej czwartej przekroczy
i kiedy — ta pozycja nie pyta, bo odpowiedź zależy od tempa uzupełnień, a nie od
stanu drzewa.
