# 6.D295 · Różnica jest NIEOSIĄGALNA, a nie nieobecna — i widać to w dwóch krotkach

**Data:** 19.09.2026 · **Gałąź:** `claude/sharp-ramanujan-jdr51o` · **Baza:** `95c13a6`

Przy 6.D284 kontrola KN-4 przeliczyła odległość pokrycia od `od` zamiast od `wiersz`
i **nie zmieniła ani jednej liczby**: w populacji pokrycia (23 wpisy) te dwa pola
okazały się równe. Ta pozycja pyta, czy `proza` w ogóle potrafi zwrócić wpis,
w którym są różne.

---

## 1. Odpowiedź stoi w KODZIE, więc czytam kod PRZED policzeniem

Pole „Wyjście" żąda liczby dla całego drzewa, a potem — jeśli zero — sprawdzenia,
czy istnieje kształt prozy, przy którym różnica powstaje. Kolejność jest tu treścią:
**gdybym najpierw policzył, dostałbym zero i musiał zgadywać, czy to fakt
o korpusie.** `proza` buduje krotkę w dwóch gałęziach i obie mieszczą się w czterech
wierszach:

```python
out.append((nazwa, token.start[0], token.string, "komentarz",
            token.start[0], token.end[0]))
...
out.append((nazwa, dokument.lineno, dokument.value, "docstring",
            dokument.lineno, dokument.end_lineno or dokument.lineno))
```

Krotka ma kształt `(plik, wiersz, tekst, rodzaj, od, do)`. W gałęzi komentarza
`wiersz` i `od` to **to samo wyrażenie** `token.start[0]`, policzone dwa razy.
W gałęzi docstringu — **to samo wyrażenie** `dokument.lineno`, policzone dwa razy.

**Nie ma ścieżki, która przypisywałaby im cokolwiek różnego.** Różnica nie jest więc
rzadka ani zależna od kształtu prozy: jest **nieosiągalna**, i wynika to z dwóch
literałów krotki, a nie z żadnego pomiaru.

## 2. Liczba dla całego drzewa

```
wpisow proza: 14679
wiersz != od : 0
do != od     : 2055
po rodzaju   : {'komentarz': 11836, 'docstring': 2843}
```

**Zero na czternastu tysiącach sześciuset siedemdziesięciu dziewięciu wpisach**, a nie
na dwudziestu trzech z populacji pokrycia. Pole „Wyjście" żądało właśnie tej liczby —
„w całym drzewie, nie tylko w populacji pokrycia" — i różnica rzędu wielkości między
23 a 14 679 jest powodem, dla którego żądało.

## 3. Krotka NIE jest zdegenerowana — i to jest kontrola, bez której liczba nie znaczy nic

Gdyby `proza` zwracała trzy równe pola, zero z §2 mówiłoby tylko tyle, że czytnik jest
zepsuty. Nie jest:

**`do` różni się od `od` w 2055 wpisach** — wszystkie to docstringi, najdłuższy liczy
**139 wierszy** (`test_report_hygiene.py`, w. 2..140). Komentarze mają `do == od`
zawsze, bo token `COMMENT` z definicji nie przekracza wiersza.

Krotka niesie więc **dwie** różne wartości wierszowe, nie trzy: `wiersz`/`od` to jedna
liczba zapisana dwukrotnie, a `do` jest drugą, prawdziwie niezależną. KN-4 przy 6.D284
mutowała pole **w jego własnego bliźniaka** — i dlatego nie mogła zmienić niczego.

## 4. Kontrola: PRÓBA napisania prozy, która różnicę wytwarza

Pole „Weryfikacja" mówi: proza o kształcie, który różnicę wytwarza, ma dać `wiersz`
różny od `od`, a **jeśli nie da się takiego napisać, jest to odpowiedź i trzeba ją
zapisać z powodem**. Powód mam z §1, ale próbę wykonałem mimo to — argument o kodzie
bez próby jest tańszy, niż powinien być.

Drzewo próbne z sześcioma kształtami: docstring modułu wielowierszowy z pustą linią
w środku, trzy komentarze z rzędu, docstring klasy poprzedzony pustą linią po
nagłówku, komentarz z wcięciem, docstring metody stojący **po** komentarzu, docstring
funkcji o **wielowierszowym nagłówku**.

```
rodzaj      wiersz    od    do              poczatek
docstring        1     1     4  wiersz==od  Docstring modulu.
komentarz        5     5     5  wiersz==od  # komentarz jednowierszowy
komentarz        6     6     6  wiersz==od  # komentarz
komentarz        7     7     7  wiersz==od  # w trzech
komentarz        8     8     8  wiersz==od  # wierszach z rzedu
docstring       13    13    13  wiersz==od  Docstring klasy POPRZEDZONY pust
komentarz       16    16    16  wiersz==od  # komentarz z wcieciem
docstring       17    17    17  wiersz==od  Docstring metody stojacy PO kome
docstring       24    24    27  wiersz==od  Docstring funkcji, ktorej naglow

wpisow z `wiersz` roznym od `od`   : 0
wpisow wielowierszowych (`do`!=`od`): 5
```

**Żaden kształt nie wytwarza różnicy, a `do` zmienia się swobodnie** — od 1 do 27
na tym drzewie i do 168 na pełnym. Kontrola jest więc wykonana, nie tylko wywnioskowana,
i jej wynik zgadza się z odczytem kodu.

## 5. Rozstrzygnięcie

**Różnica NIE jest osiągalna.** Nie „nie występuje w dzisiejszym korpusie" i nie
„występuje rzadko" — nie istnieje wejście, dla którego `proza` zwróciłaby `wiersz`
różny od `od`, bo oba pola są tym samym wyrażeniem zapisanym dwukrotnie.

Konsekwencja dla 6.D284: KN-4 tamtej pozycji **nie mogła niczego zmierzyć**. Jej wynik
(„zero wpisów z różnicą przy 23 z pokryciem") był prawdziwy i bezużyteczny naraz —
mierzył równość dwóch kopii jednej liczby. Tamta pozycja zapisała to jako otwarte
pytanie i miała rację, że zapisała; odpowiedź brzmi: kontrola była pusta z konstrukcji.

**Czego ta pozycja NIE rozstrzyga:** czy `proza` powinna mieć trzy pola wierszowe
zamiast dwóch — czyli czy `wiersz` i `od` mają się kiedykolwiek rozjechać. To byłaby
zmiana sposobu budowania okna, a pole „Poza zakresem" zabrania jej nazwanym słowem.

## 6. CZWARTY RAZ TEGO SAMEGO DNIA, i dlatego zapisuję to osobno

Zero, które jest własnością przyrządu, a nie drzewa, wyszło dziś **cztery razy**:

| pozycja | zero albo komplet | z czego wynikał |
|---|---|---|
| 6.D292 | ten sam próg, dwa przeciwne werdykty | mianownik szerszy niż populacja bramki |
| 6.D293 | `WYNIK_KONTROLI` trafia w 113/113 | wzorzec szerszy niż pytanie |
| 6.D294 | zapadek nieobecnych: 0 | słownik zamknięty nad dzisiejszym rejestrem |
| 6.D295 | `wiersz` różny od `od`: 0 | **dwa pola z jednego wyrażenia** |

Trzy pierwsze wymagały pomiaru, żeby rozpoznać przyczynę. **Ten jeden dało się
przeczytać z kodu w minutę** — i to jest różnica, którą warto zapamiętać: zanim
policzę zero, opłaca się sprawdzić, czy czytnik potrafi zwrócić cokolwiek innego.

## 7. Przewidywania spisane PRZED pomiarem

Przewidywanie postawiłem po przeczytaniu kodu, a przed uruchomieniem czegokolwiek,
i zapisuję to jawnie, bo zmienia wagę trafienia: **nie zgadywałem liczby, tylko
wyprowadziłem ją z dwóch wierszy `proza`.**

| # | przewidywanie | wynik |
|---|---|---|
| 1 | `wiersz != od` w całym drzewie: **zero, bo to samo wyrażenie** | trafione, 0 z 14 679 |
| 2 | kontroli nie da się napisać tak, by dała różnicę | trafione na sześciu kształtach |
| 3 | `do` będzie się różnić — krotka nie jest zdegenerowana | trafione, 2055 |
| 4 | komentarze będą miały `do == od` zawsze | trafione, wszystkie 11 836 |

Cztery z czterech, ale **żadne z nich nie jest zgadnięciem** — wszystkie wyszły
z lektury czterech wierszy kodu. Dzień, w którym moje przedziały mylą się w obie
strony, kończy się pozycją, w której przedziałów nie było potrzeba.

## 8. Czego świadomie nie zrobiono

- **Nie zmieniono `OKNO_PROZY`** ani sposobu budowania okna (pole „Poza zakresem").
- **Nie scalono `wiersz` z `od`** w jedno pole, choć §1 pokazuje, że są tym samym.
  Byłaby to zmiana krotki, którą czyta kilka czytników; pole zabrania.
- **Nie poprawiono KN-4 w 6.D284.** Tamta kontrola jest pomiarem z datą i zostaje;
  ta pozycja mówi, co znaczyła, a nie przepisuje jej.
- **Nie postawiono bramki** na równości `wiersz == od` — byłaby bramką na literale,
  który stoi dwa wiersze od niej samej.
- **Nie tknięto `src/`.**

## 9. Zauważone przy okazji, nietknięte

Komentarzy jest **11 836**, docstringów **2843** — czyli korpus prozy tego projektu
w ponad czterech piątych składa się z komentarzy. Wszystkie bramki liczące „prozę
pomiarową" ważą więc komentarz i docstring tak samo, choć docstring bywa
stuczterdziestowierszowy, a komentarz nigdy nie przekracza wiersza. Czy to waży na
którejkolwiek z tych bramek, ta pozycja nie pyta.
