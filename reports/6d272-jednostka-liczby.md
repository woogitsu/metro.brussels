# 6.D272 — rozjechanych ZERO, bo sito nie widzi tego, co pozycję wywołało

**Data:** 18.09.2026 · **Gałąź:** `claude/6d272-jednostka-liczby` · **Baza:** `3012eba`

## 1. Trzy liczby z pola „Wyjście"

| pytanie | odpowiedź |
|---|---|
| czytników odwzorowań wołalnych bez argumentu | **41** |
| z tego dało się policzyć | **24** |
| z dwiema RÓŻNYMI miarami (klucze ≠ elementy) | **22** |
| zdań prozy nazywających którąkolwiek miarę | **3** |
| z tego ROZJECHANYCH z miarą, którą liczy bramka | **0** |

Odrzucone po drodze: **16** czytników o wartościach, które zbiorami nie są
(odwzorowanie na liczbę albo napis — `len` dałby tam znaki, nie elementy;
`bloki_wykonane` dawało 712 777 „elementów", czyli znaki), **1** pusty
i **2** o miarach równych.

Trzy zdania, wszystkie zgodne z miarą swojej bramki:

* `test_dead_constants_csharp` — „ma dziś N deklaracji" i „razem N": ELEMENTY
  (396 przy 345 kluczach), bramka liczy `sum(len(v))`;
* `test_provenance_classes` — „Pole `status` stoi w N plikach JSON": KLUCZE
  (20 przy 36 elementach), bramka liczy `len()`;
* `test_tree_writes` — zdanie o zapadce `MAX_ZAPISOW_W_DRZEWIE`, która stoi dziś na 5:
  ELEMENTY (5 przy 2 kluczach), bramka liczy `sum(len(m))`. Zdanie niesie też
  dawną wartość, ale jako opis przeszłości.

**Teza tej pozycji w postaci ogólnej się nie potwierdziła.**

## 2. Dwa trafienia były ZBIEGIEM WARTOŚCI — czwarty raz w tej serii

Sito dopasowywało liczbę **po wartości w obrębie modułu**, nie po podmiocie zdania,
i dało dwa fałszywe alarmy, które odpadły dopiero po przeczytaniu zdań:

* `test_tree_walks` niesie pogrubione `3`, zgodne z liczbą elementów
  `wolne_rozstrzygalne_pomiarem` — ale to **odległość zapłonu w krokach**
  („od 3 do 113 kroków"), nie miara tego czytnika;
* `wszystkie_kopiowania` ma klucze 5 i elementy 7, a zdanie z tymi dwiema
  liczbami opisuje **historię zapadki** zapisów w drzewie, nie ten czytnik.

Jest to ten sam błąd co przy 6.D267 (luzy progów) i dwa razy przy 6.D268
(`2377` z asercjami C#, `44` z czytnikiem komunikatów) — **czwarty raz**, i za
każdym razem złapało go przeczytanie źródła, nie bramka. Dlatego bramka stoi
na **kotwicach zdań**, a nie na dopasowaniu wartości.

## 3. Instancja, która pozycję wywołała, jest dla tego sita NIEWIDZIALNA

To najważniejsze znalezisko i dotyczy **sprzężenia dwóch bramek**.

Liczby 132, 36 i 81 — jedyna zmierzona instancja tego kształtu, z 6.D269 —
stoją w `test_dead_constants.py` **bez pogrubienia**. Przy 6.D269 zapadka górna
`MAX_POGRUBIONYCH_BEZ_POKRYCIA` zapaliła się na nich i pogrubienie trzeba było
zdjąć, bo podnosić jej nie wolno. Census i to sito czytają **wyłącznie liczby
pogrubione** — więc zaspokojenie jednej bramki wyprowadziło te liczby z pola
widzenia drugiej.

Zdjęcie pogrubienia zdarzyło mi się w tej serii **sześć** razy (6.D260, 6.D262,
6.D264, 6.D269, 6.D270 i 6.D271). Każde z nich było poprawnym ruchem wobec
zapadki, która je wymusiła, i każde zmniejszało populację, którą widzi sito prozy.
Nie proponuję tu zmiany — okna ani wzorca pogrubienia nie wolno ruszać, to 6.D259
i jej pole „Poza zakresem". Zapisuję, bo liczba „rozjechanych zero" znaczy coś
innego, kiedy wiadomo, że jedyna znana instancja jest poza zasięgiem.

## 4. Kontrole

Przewidywania spisane przed przebiegami, na kopii pełnego drzewa, z czyszczonym
`__pycache__`, każda z asercją że mutacja wylądowała.

| mutacja | przewidziane | zmierzone |
|---|---|---|
| proza podaje DRUGĄ miarę (20 kluczy → 36 elementów) | czerwień z obiema miarami | `FAIL … proza mowi 36, a bramka obok liczy klucze, czyli 20 (druga miara: 36)` |
| stan bazowy (proza podaje miarę bramki) | zielono | `16/16 przeszło` |
| zdublowanie zdania z kotwicą | czerwień „kotwica łapie 2 zdań" | `FAIL … kotwica … lapie 2 zdan … przy dwoch czytnik bierze pierwsze` |

**Czwarty raz w tej serii kopia drzewa była niepełna.** Baza na kopii dała 21
czytników przy 22 w drzewie, bo `test_ci_workflows.kopie_listy_sonames` czyta
`.github/workflows/` — `FileNotFoundError`, policzony jako odrzucenie i milcząco
zmniejszający census. Kompletna kopia do kontroli w tym repozytorium to
`tools + src + tests + docs + reports + data + CLAUDE.md + .gitignore + .github`.

## 5. Koszt bramki był zmierzony i zbity dziesięciokrotnie

Pierwsza wersja wołała wszystkie 41 czytników, a robiła to w dwóch testach:

```
skan AST (sami kandydaci)            0,60 s
wywolanie 41 czytnikow               22,40 s
dwa testy = dwa przebiegi            45 s
zestaw:  263 s  ->  321 s            (+22 %)
```

Pamięć podręczna zbiła to do jednego przebiegu (301 s), ale dopiero przeniesienie
**censusu na kandydatów z AST** zdjęło koszt naprawdę: moduł z 28,7 s na **7,0 s**,
a zestaw na **281,7 s**. Kandydat z AST łapie nowy czytnik odwzorowania równie
dobrze — po prostu nie liczy mu obu miar, a te liczy się dla dwóch czytników spod
kotwic. Pełny przebieg został w `dwie_miary_czytnikow` i da się go wywołać na
żądanie; bramka go nie woła.

Droga połowa odpowiadała dokładnie za „rozjechanych **zero**", więc płaciłem
22 sekundy za zero.

## 6. Czego świadomie nie zrobiono

Okna, wzorca pogrubienia ani zapadki górnej nie ruszano — to 6.D259. Nie
ujednolicano jednostek w żadnym zdaniu, bo żadne nie było rozjechane.
Siedemnastu czytników bez ani jednego zdania prozy o ich mierze nie opisywano:
dwuznaczność jest tam dostępna, ale nieuruchomiona, a dopisywanie zdań tylko po to,
żeby je mieć, byłoby pracą bez zmierzonej potrzeby.
