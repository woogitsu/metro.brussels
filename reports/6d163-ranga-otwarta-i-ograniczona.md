# 6.D163 — cztery rangi, dwie otwarte, i jedną dopisałem dzień wcześniej

**13.09.2026**, na `4d2a12d`. Wejście: `tools/tests/test_suite_runtime_budget.py`
(`POMIARY`), `tools/tests/test_timing_record.py` (`WPISOW_Z_DOPISKIEM`), pozostałe
listy pomiarów w `tools/tests/`, `reports/zapis-czasu-zestawu.md`.

## 1. Ile innych list pomiarów jest w drzewie — zero

Pole „Wejście" kazało policzyć „pozostałe listy pomiarów w `tools/tests/`". Skan
strukturalny przez wspólny filtr drzewa szukał przypisań, których elementy są krotkami
zaczynającymi się od daty ISO — to jest kształt wpisu pomiaru. Znalazł **jedną** listę:
tę samą, o której pozycja mówi.

Szersze kryterium (krotki z opisem dłuższym niż 25 znaków) dokłada `SZESC_PRZYPADKOW`
z `test_field_paths.py` i `POMIARY_BRAKOW` z `test_readme_claims.py`, ale **żadna
z nich nie zapisuje przebiegów** — pierwsza jest tablicą przypadków bramki, druga mapą
braków w danych. Rangi nie niosą.

Odpowiedź na „ile ich jest gdzie indziej" brzmi więc **zero**, i jest policzona,
a nie założona.

## 2. Cztery opisy z rangą, ale to są dwie różne rzeczy

| wpis | słowo | rodzaj |
|---|---|---|
| 2026-09-05, 77,040 s | „najwyższy z czterech przebiegów tamtej sesji" | **ograniczona** — zbiór zamknięty |
| 2026-09-07, 107,331 s | „najwyższy zmierzony w kontenerze **do 11.09**" | **ograniczona** — odcięta datą |
| 2026-09-11, 116,404 s | „, NAJWYŻSZY na runnerze" | **OTWARTA** |
| 2026-09-13, 167,402 s | „, NAJNIŻSZY" | **OTWARTA** |

**Rozróżnienie, na którym stoi cała ta pozycja.** Ranga ograniczona mówi o zbiorze,
który się już nie zmieni — czterech przebiegach tamtej sesji albo o stanie na dany
dzień. Takie zdanie jest o przeszłości i zostanie prawdziwe na zawsze. Ranga otwarta
mówi „najwyższy z tej listy" i **przestaje być prawdziwa przy pierwszym wpisie, który
ją bije, nie zmieniając ani znaku**.

Dwie ograniczone zostają, z powodem zapisanym przy każdej. Dwie otwarte zdjęte.

## 3. Obie otwarte szkodziły inaczej, i drugą dopisałem sam

**„, NAJWYŻSZY na runnerze"** powtarzało to, co `MEASURED_MAX_WALL_S` z tej samej
listy liczy — druga kopia liczby, rodzina 6.B28. Czekała na pierwszy wolniejszy
przebieg runnera.

**„, NAJNIŻSZY"** przy wpisie 167,402 s było **już nieprawdziwe w dniu, w którym to
sprawdzono**. Najniższy pomiar kontenera w liście to **76,518 s** z 07.09.2026; wpis
z dopiskiem jest od niego ponad dwa razy wolniejszy. Czytany jako „najniższy z tych
sześciu powtórzeń" był prawdziwy, czytany jako zdanie o liście — fałszywy, a nic
w tekście tych dwóch odczytów nie rozróżniało.

Dopisałem go **dzień wcześniej, przy 6.D160**, w tej samej sesji, która potem tę
pozycję wzięła. Jest to więc dokładnie ten mechanizm, o którym pozycja mówi („zdania
tej rodziny mogą stać w drzewie i nikt ich nie policzył") — z tą różnicą, że autorem
jednego z dwóch przypadków jestem ja, a między dopisaniem a znalezieniem minęła doba.

## 4. Co weszło do kodu

Oba dopiski zdjęte. `WPISOW_Z_DOPISKIEM` w `test_timing_record.py` zeszło z **1 na 0**
— dokładnie tak, jak komentarz przy tej stałej przewidywał („poprawką jest zejście tej
liczby do zera, nie rozluźnienie porównania"). Akapit przy niej jest przepisany,
a nie dopisany obok, bo opisywał stan, którego już nie ma.

Doszła bramka, która nie wpuści nowej rangi otwartej: każdy opis ze słowem rangi musi
stać na liście rozstrzygniętych, z powodem. Wzorzec bierze **superlatyw**, a nie każde
porównanie — „wolniejszy niż tamten" jest zdaniem o dwóch przebiegach i zostaje
prawdziwe, „najwolniejszy" jest zdaniem o całym zbiorze i starzeje się razem z nim.

Wartości pomiarów i próg **nietknięte** — „Poza zakresem".

## 5. Kontrole negatywne

Baza: **35/35**. Po każdej `cp` z kopii roboczej i `md5sum -c: OK`. Przed każdym
przebiegiem czyszczony `__pycache__`; po każdym podstawieniu `diff` z kopią roboczą
i `assert` na jednym wystąpieniu.

| | mutacja | wynik | co mówi |
|---|---|---|---|
| KN-1 | ranga otwarta wraca do wpisu | **33/35** | zapala DWIE bramki: nową i tę z 6.D152 |
| KN-2 | wzorzec przestaje widzieć superlatywy | **34/35** | druga strona porównania nie jest ozdobą |
| KN-3 | wpis skreślony z listy rozstrzygniętych | **34/35** | lista musi być pełna, nie tylko niepusta |
| KN-4 | wzorzec bierze też zwykłe porównanie | **34/35** | wąskość wzorca jest mierzona, nie deklarowana |

KN-2 jest tu warta uwagi: pierwsza wersja testu porównywała posortowane listy jedną
asercją i przy tej mutacji wypisywała `[]`, czyli komunikat, z którego nie dało się
odczytać, co się stało. Rozdzieliłem ją na dwie — „ranga bez rozstrzygnięcia"
i „rozstrzygnięcie bez rangi" — i dopiero druga mówi wprost, że wzorzec oślepł.

## 6. Czego nie zrobiono

- **Nie tknięto wartości pomiarów ani progu** — „Poza zakresem".
- **Nie zdjęto rang ograniczonych.** Obie są zdaniami o przeszłości i nowy pomiar ich
  nie obali; zdejmowanie ich byłoby kasowaniem informacji, a nie usuwaniem usterki.
- **Nie dopisano bramki na inne listy pomiarów** — punkt 1 mówi, że innych nie ma,
  więc nie ma czego pilnować. Gdy powstanie druga taka lista, ta bramka jej nie
  zobaczy, i to jest zapisane w jej docstringu.

## 7. Co zauważone przy okazji, nietknięte

Wzorzec rangi ogląda wyłącznie `POMIARY`. Gdyby ktoś założył drugą listę przebiegów
w innym module, nowa bramka milczałaby — nie dlatego, że lista jest czysta, tylko
dlatego, że jej nie widzi. Dziś to nie szkodzi, bo skan z punktu 1 mówi, że drugiej
listy nie ma; jest to jednak ta sama zależność od dzisiejszego kształtu drzewa, którą
6.D159 znalazło przy bramce położenia modułów.
