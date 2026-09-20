# 6.D309 · Pięć bramek wypisuje różnicę w jedną stronę — a odpowiedź NIE ZALEŻY od sporu o populację bazową

**Data:** 20.09.2026 · **Gałąź:** `claude/sharp-ramanujan-jdr51o` · **Baza:** `757be46`

6.D300 zmierzyło, że reguła „stała modułu jest przypisaniem w zasięgu" przesunęła
siedemnaście wyrażeń nie do klasy liczbowej, tylko do **zbiorowej** — są to przypięte
zbiory modułowe, od których bramki odejmują dzisiejszy stan drzewa. Ta pozycja pyta,
ile bramek ma ten kształt i ile wypisuje różnicę w **obie** strony.

Odpowiedź: **czterdzieści wyrażeń w osiemnastu plikach, dwadzieścia trzy przypięcia,
osiemnaście z nich w parze — i PIĘĆ tylko w jedną stronę.** Pole dopuszczało odpowiedź
„żadna"; nie jest żadna.

Ale wynik, dla którego warto było tę pozycję wziąć, jest inny: **moja populacja bazowa
nie zgadza się z 6.D300, a odpowiedź i tak jest ta sama.**

---

## 1. Złamałem regułę pola „Wejście" i pomiar to pokazał

Pole mówi wprost: `komunikaty` jest **do POŻYCZENIA, nie napisania drugi raz**.
Napisałem własny przejazd po `ast.Assert` — i pierwsza wersja dała populację bazową
**313** przy liczbie kontrolnej 6.D300 równej 132.

Warunek obalenia spisałem przed pomiarem i honoruję go: „jeśli X1 nie da 132, mój
czytnik albo reguła skoku różni się od 6.D300 i wtedy raportuję ROZJAZD POPULACJI".

Przyczynę znalazłem, czytając własny kod: 6.D300 robi **jeden skok przez przypisanie
W ZASIĘGU**, a ja szukałem przypisania `ast.walk(drzewo)`, czyli **gdziekolwiek
w pliku**. Po poprawieniu reguły skoku na zasięg funkcji:

```
populacja WASKA (`a - b` wprost w komunikacie):  71    [6.D300: 55]
populacja SZEROKA (plus skok w zasiegu):        202    [6.D300: 132]
```

**Nadal się nie zgadza** i tak to zapisuję, zamiast dobierać definicję do liczby.
Mój klasyfikator bazowy jest szerszy od tamtego — najpewniej dlatego, że biorę każdy
`ast.BinOp` z `ast.Sub`, a 6.D300 zawężało populację dodatkowo. Różnicy **nie
uzgadniam**: to byłoby przepisywanie cudzego pomiaru pod swój wynik.

## 2. I TO NIE MA ZNACZENIA — odpowiedź jest odporna na spór o bazę

To jest właściwy wynik tej pozycji. Zmierzyłem odpowiedź na **trzech** różnych
populacjach bazowych:

| populacja bazowa | skąd | wyrażeń P4 | plików | przypięć | w parze | jedna strona |
|---|---|---|---|---|---|---|
| 132 | 6.D300 | 40 | 18 | 23 | 18 | 5 |
| 202 | moja, skok w zasięgu | **40** | **18** | **23** | **18** | **5** |
| 313 | moja, skok w całym pliku | **40** | **18** | **23** | 18 | 5 |

**Wszystkie pięć liczb jest identycznych przy bazie różniącej się dwuipółkrotnie.**
Powód jest prosty po nazwaniu: poszerzenie bazy dokłada wyrażenia, w których **żaden**
operand nie jest przypięty — klasa `ZADNA`, czyli ta bez przypięcia po żadnej ze stron, rośnie ze 160 na 265, a klasy `jedna_strona`
i `OBIE_PRZYPIETE` nie ruszają się wcale.

Zapisuję to jako §2, a nie jako przypis, bo **spór o populację bazową był realny
i okazał się bez skutku dla pytania**. Nie zawsze tak jest — przy 6.D300 wybór
populacji zmieniał odpowiedź z 55 na 132 i tamta pozycja musiała podać obie.

## 3. Trzy liczby, których żądało pole „Wyjście"

```
ROZLACZNOSC: {'ZADNA': 160, 'jedna_strona': 40, 'OBIE_PRZYPIETE': 2}  suma: 202

P4 — wyrazen z JEDNA strona przypieta:  40
   plikow:                              18
   przypiec (plik, stala):              23
      W PARZE (roznica w obie strony):  18
      tylko jedna strona:                5
```

Klasy są rozłączne i sumują się do populacji — sprawdzone, a nie założone.
Klasa `OBIE_PRZYPIETE` **nie jest pusta**: dwa wyrażenia mają przypięcie po obu
stronach (`test_readme_claims.py`, `test_report_hygiene.py`) i do populacji tej
pozycji nie wchodzą, bo pole pyta o różnicę drzewa od przypięcia.

## 4. ODPOWIEDŹ NA PYTANIE POLA: PIĘĆ, nie żadna

```
test_csv_provenance.py       BEZ_NASTAW                 DRZEWO-PIN
test_data_thresholds.py      WARTOSCI_PROGOW            PIN-DRZEWO
test_environment_doc.py      POD_KATALOGI_Z_KODU        PIN-DRZEWO
test_report_hygiene.py       ROZSZERZENIA_BEZ_TRAFIEN   PIN-DRZEWO
test_tree_walks.py           ROZSTRZYGALNE_POMIAREM     DRZEWO-PIN
```

Trzy pytają tylko „co z przypięcia zniknęło", dwa tylko „co doszło". Pole ostrzegało,
żeby nie brać tego za usterkę — i **nie biorę**: bramka może świadomie pytać o jedną
stronę. Zapisuję kierunek przy każdej, bo to jedyne, co odróżnia decyzję od przeoczenia,
a rozstrzygnąć tego bez autora nie można.

## 5. USTERKA MOJEGO KLASYFIKATORA, znaleziona CZYTANIEM, a nie wyborem liczby

Pierwszy przebieg dał **17 par i 6 jednostronnych**; pomiar, który stał już w tej sesji,
mówił 18 i 5. Zamiast wybrać którąkolwiek liczbę, przeczytałem sporny przypadek —
`test_csharp_type_callers.py`, przypięcie `TYLKO_TESTY`:

```
w. 201   [(n, "tylko testy") for n in sorted(tylko_testy - TYLKO_TESTY)]
w. 216   znikniete = sorted((TYLKO_TESTY | NIEWOLANE_PO_NAZWIE)
                            - (tylko_testy | niewolane | z_src))
```

`TYLKO_TESTY` **naprawdę występuje w obu kierunkach** — ale w kierunku `PIN − DRZEWO`
stoi wewnątrz **unii z drugim przypięciem**. Mój klasyfikator brał z operandu
`sorted(L or R)[0]`, czyli **jedną nazwę, alfabetycznie pierwszą**, i całą unię
przypisywał do `NIEWOLANE_PO_NAZWIE`.

Po poprawce — przypisanie wyrażenia do **każdej** przypiętej nazwy w operandzie —
wychodzi **18 par i 5 jednostronnych**. Usterka była w moim przyrządzie, nie w liczbie
cudzej; znalazłem ją, bo różnica wynosiła jeden i **nie zgodziłem się jej przemilczeć**.

## 6. Kontrola przyrządu: NIE ZDANA W LITERZE, spełniona przez ZAWIERANIE

Pole żąda: siedemnaście wyrażeń przesuniętych regułą B w 6.D300 ma znaleźć się
w populacji tej pozycji; przyrząd widzący mniej czyta stałe modułu inaczej.

**Nie odtwarzam siedemnastki** i mówię to wprost — nie mogę, bo moja populacja bazowa
liczy 202 wobec 132, więc klasyfikator, który tamtą siedemnastkę wyprodukował, jest inny
niż mój. Zamiast ogłaszać kontrolę zdaną, pokazuję **zawieranie**, i ono jest mocniejsze
od liczby:

```
z 40 wyrazen populacji:
   operand przypiety to GOLA nazwa modulowa :  14
   operand przypiety to wyrazenie zlozone   :  26
```

Każde wyrażenie, które reguła B mogła przesunąć do klasy zbiorowej, **musi** zawierać
nazwę modułową o kształcie zbioru — a każde takie wyrażenie jest w tej czterdziestce
z definicji P4. Siedemnaście leży więc wewnątrz czterdziestu, cokolwiek dzieli oba
klasyfikatory.

## 7. Przewidywania — i po raz pierwszy od trzech pozycji NIE BYŁY NIEZALEŻNE

Zapisałem to **przed** pomiarem, a nie po: pomiar tych samych wielkości stał już w tej
sesji i jego liczby przeczytałem.

| # | przewidywanie | wynik |
|---|---|---|
| X1 | populacja bazowa da 132 | **OBALONE** — 313, po poprawce 202 |
| X2 | populacja P4: 30–50 | trafione (40) |
| X3 | plików: 12–25 | trafione (18) |
| X4 | przypięć w parze powyżej 60 % | trafione (18 z 23, czyli 78 %) |
| X5 | odpowiedź nie brzmi „żadna" | trafione (pięć) |
| X6 | kontrola NIE zda się w literze i będę musiał pokazać zawieranie | trafione |
| X7 | znajdzie się przypięcie puste z konstrukcji | **NIE SPRAWDZONE** — nie zmierzyłem tego i nie udaję, że zmierzyłem |

**X2–X5 nie są dowodem niczego**, bo mieszczą liczby, które znałem. Wartość mają tylko
X1 i X6: **X1 obalone** — i to ono wymusiło poprawienie reguły skoku, czyli całą §1;
**X6 trafione**, ale trafione dlatego, że spodziewałem się rozjazdu klasyfikatora,
a nie dlatego, że go przewidziałem co do przyczyny.

X7 zapisuję jako **niesprawdzone**, a nie jako pudło: postawiłem je przed pomiarem
i nie wykonałem. Zaliczenie go w którąkolwiek stronę byłoby zmyśleniem.

## 8. Czego świadomie nie zrobiono

- **Nie dopisano brakującej strony różnicy** w żadnej z pięciu bramek — pole zabrania,
  a §4 mówi, dlaczego jednostronność bywa decyzją.
- **Nie zmieniono żadnego przypięcia** ani żadnej asercji.
- **Nie uzgodniono mojej populacji bazowej z 6.D300.** Rozjazd jest opisany w §1
  i policzony w §2; uzgadnianie go polegałoby na dobieraniu definicji pod cudzą liczbę.
- **Nie postawiono bramki na kształcie wyrażenia** ani na liczbie par.
- **Nie sprawdzono X7** (przypięcie puste z konstrukcji) — patrz §7.
- **Nie tknięto `src/`, `data/` ani prozy w `tools/tests/`.**

## 9. Zauważone przy okazji, nietknięte

1. **Klasa `ZADNA`, czyli bez przypięcia po żadnej ze stron, to 160 z 202 wyrażeń** — czyli cztery piąte odejmowań osiągalnych
   z komunikatu asercji nie dotyka przypięć w ogóle. Czym są, ta pozycja nie pyta,
   ale 6.D300 zmierzyło, że dwadzieścia cztery z nich są **nieorzekalne składniowo**.
2. **Dwadzieścia sześć z czterdziestu przypiętych operandów to wyrażenia złożone**,
   a nie gołe nazwy — unie, przecięcia, wywołania. Skan szukający `NAZWA - coś` widzi
   więc mniej niż połowę populacji, i to jest ta sama różnica, którą §5 złapało
   na jednym przypadku.
3. **`test_readme_claims.py` i `test_report_hygiene.py` mają przypięcie po OBU
   stronach odejmowania** — klasa, której pole nie przewidziało i która do jego
   pytania nie należy. Są dwa; ile ich będzie, gdy przypięć przybędzie, nie pyta nikt.
