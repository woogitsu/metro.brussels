# 6.D306 · Trzydzieści dziewięć modułów, nie dwa — a mój pierwszy przyrząd mierzył czas DZIESIĘCIOKROTNIE ZA DUŻY

**Data:** 20.09.2026 · **Gałąź:** `claude/sharp-ramanujan-jdr51o` · **Baza:** `480e11d`

6.D297 zmierzyło, że dziewięć z trzynastu wołań `pozycje_pokrycia` idzie z tej samej
pary argumentów, i że pamięć w miejscu ścina ten moduł o czterdzieści pięć procent.
Pole pyta, ilu modułów zestawu to dotyczy — i dopuszcza wprost odpowiedź
„tylko te dwa, które już znamy".

**Nie te dwa. Trzydzieści dziewięć.** A po drodze wyszło coś, czego pole nie zakładało:
**mój pierwszy przyrząd podawał czasy dziesięciokrotnie za duże i złapałem to dopiero
przez porównanie z czasem całego modułu.**

---

## 1. Kontrola przyrządu, której żądało pole — ZDANA co do cyfry

Pole stawia warunek: `test_message_claims.py` ma wyjść z **trzynastoma wołaniami
i trzema parami**; jeśli przyrząd daje co innego, liczy źle także resztę.

```
pozycje_pokrycia             wolan=13   par=3   maxP=9
```

Zgadza się co do jednego z §1 raportu 6.D297. **Liczący arm przyrządu jest więc
zwalidowany na przypadku, który pozycję wywołał** — i to ma znaczenie dla §3, bo
drugi arm tego samego przyrządu okazał się zepsuty.

## 2. ODPOWIEDŹ: 39 modułów ze 138, czyli 87 % tych, które mają czytnik drzewa

```
modulow zestawu (bez test_all.py):                      138
  z >= 1 czytnikiem drzewa (deklaratywnie i wolanym):    45
  spelniajacych warunek pola (>1 wolanie z JEDNEJ pary): 39
  bez zadnego przejscia po drzewie:                      93
czytnikow z >1 wolaniem z jednej pary:                  123
czytnikow zadeklarowanych a NIGDY niewolanych:            4
```

Rzadkością jest sytuacja **odwrotna**: tylko sześć modułów z czytnikiem woła go
dokładnie raz na parę.

**Definicja ma dwa czytania i policzyłem oba, zamiast wybrać po cichu.** Czytanie
szerokie bierze każdą funkcję poziomu modułu sięgającą przejścia po drzewie; wąskie
odsiewa te, których koszt robi **podproces**, a nie drzewo (`doctor.sh`, `git`).
Różnica jest **prawie pusta**:

| | modułów z czytnikiem | spełnia warunek |
|---|---|---|
| szerokie | 45 | **39** |
| wąskie | 44 | **38** |

Z klasy wypada **jeden** moduł, `test_doctor_test_log.py`. Wybór czytania zmienia więc
czoło listy, a nie liczbę, o którą pole pyta.

## 3. USTERKA MOJEGO PRZYRZĄDU, ZŁAPANA NA WŁASNEJ LICZBIE

Pierwszy przebieg podał dla `test_tree_walks.py::_porownania_zapadek` **59,369 s**
czasu inkluzywnego. Ten moduł przebiega w **13,7 s**. Czytnik nie może kosztować
czterokrotności swojego modułu, więc liczba była nieprawdziwa — i tak to nazywam,
zamiast wpisać ją do raportu.

Pomiar wprost, w czystym procesie, bez owijek:

```
wolanie 1: 0.927 s
wolanie 2: 0.969 s
wolanie 3: 0.928 s
wszystkie 23 testy BEZ owijek: 13.647 s
```

**Prawdziwy koszt to 0,93 s na wołanie — sześćdziesiąt razy mniej, niż podał przyrząd.**

Przyczyna jest w samym przyrządzie: żeby policzyć **pary argumentów**, owijka wołała
`signature.bind` i `repr` przy **każdym** wywołaniu. Przy czytnikach chodzących
5 521 i 23 270 razy koszt tego wiązania przewyższa koszt mierzonej funkcji, a ponieważ
owijki są zagnieżdżone, ląduje w czasie **wołającego**, nie wołanego.

Drugi przebieg mierzy **wyłącznie czas**, bez wiązania i bez `repr`, z odejmowaniem
czasu wołań zagnieżdżonych. Kontrola: suma czasów własnych czytników nie może
przekroczyć czasu modułu.

```
test_tree_walks.py         suma wlasnych  13.595 s   modul 13.7 s   OK
test_dotnet_version.py     suma wlasnych  26.822 s   modul 47.6 s   OK
test_message_claims.py     suma wlasnych  26.664 s   modul 26.0 s   ROZJAZD
```

Trzeci wiersz zmierzyłem jeszcze raz, tą samą drogą po obu stronach (moduł bez owijek
w tym samym procesie): **26,243 s**. Nadwyżka wynosi **0,42 s, czyli 1,6 %** — to koszt
samych owijek. **Czasy z drugiego przebiegu są więc dobre co do kilku procent, a nie
co do cyfry**, i tak je podaję.

**Zapisuję to jako pierwszą rzecz po odpowiedzi, bo różnica między „czytnik kosztuje
59 s" a „mój przyrząd kosztuje 59 s" jest całą różnicą między znaleziskiem a artefaktem.**
Złapała to nie bramka i nie oko, tylko **porównanie z liczbą, którą znałem skądinąd** —
czasem modułu z pola „Weryfikacja".

## 4. Czoło listy po czasie WŁASNYM czytnika

```
modul                              najdrozszy czytnik            wlasny  wolan   par  maxP
test_dotnet_version.py             _przebieg_doctora             26.680     15     4     6
test_message_claims.py             proza                         20.495     21     4    15
test_doctor_queue_claim.py         _doctor_w_kopii               20.378      3     3     1
test_csharp_type_callers.py        rozklad_wolajacych             6.887      7     5     2
test_prose_counts.py               wyliczenia_prozy               4.386      3     1     3
test_mutation_sweep.py             _docstringi                    2.991    601     1   601
test_bytecode_staleness.py         sekwencje_ucieczki             2.943      5     4     2
test_tree_walks.py                 wywolania_os_walk              2.911      4     1     4
test_tree_writes.py                miejsca_zapisu                 2.723    455   161     3
test_dead_constants.py             definicje                      2.434      5     1     5
test_report_claims.py              data_stalej                    2.321    263    79    14
test_digit_boundaries.py           literaly_wzorcow               2.280      3     1     3
```

Dwa czoła tej tabeli — `_przebieg_doctora` i `_doctor_w_kopii` — to funkcje z czytania
**szerokiego**: listują katalog, ale ich koszt robi `doctor.sh`. W czytaniu wąskim
znikają, i wtedy najdroższym czytnikiem zestawu jest `proza`.

## 5. Czas trzech modułów z czoła, po trzy przebiegi

Pole „Skończone, gdy" żąda czasu przebiegu dla trzech modułów z czoła. Trzy przebiegi
każdego, bo jedna liczba na maszynie dzielonej nie jest pomiarem:

```
test_tree_walks.py        23/23   14.027 / 13.720 / 13.672 s
test_dotnet_version.py    51/51   47.556 / 47.530 / 47.752 s
test_message_claims.py    21/21   26.024 / 26.194 / 26.015 s
```

Rozrzut: 0,355 s (2,6 %), 0,222 s (0,5 %), 0,179 s (0,7 %).

## 6. Skrajności, których pole nie zakładało

```
test_tree_walks.py         _wyjatki_bloku         wolan=5521  par=2941  maxP=2240
test_mutation_sweep.py     _docstringi            wolan= 601  par=   1  maxP= 601
test_report_claims.py      pliki_definicji        wolan= 263  par=   1  maxP= 263
test_tree_writes.py        _otwarcia_do_zapisu    wolan=23270 par=6518  maxP=  22
```

`_wyjatki_bloku` chodzi **pięć i pół tysiąca razy**, z czego **dwa tysiące dwieście
czterdzieści** z jednej pary argumentów. `_docstringi` i `pliki_definicji` mają
**jedną jedyną parę** na sześćset i dwieście sześćdziesiąt trzy wołania.

Szacowana oszczędność po wszystkich 123 czytnikach z powtórzeniami: **75,3 s**.
**To jest SZACUNEK, nie pomiar** — zakłada, że wołania jednej pary kosztują tyle samo,
a §3 pokazuje, jak łatwo w tej okolicy pomylić koszt funkcji z kosztem przyrządu.

## 7. Założenie pola „Skąd", które pomiar podważa

Pole mówi: „Przy 6.D283 ta sama pamięć ścięła inny moduł z trzydziestu jeden sekund na
siedem. **Przypadki są więc dwa.**"

**`test_commit_claims.py` nie ma ani jednego czytnika drzewa** — zmierzone:
zadeklarowanych zero. Ten moduł chodzi po `git log -p` **podprocesem**. Pod nazwą
„czytnik drzewa" pole zebrało **dwa różne mechanizmy**, a pamięć, która pomogła jednemu,
dotyczy w drugim czegoś innego.

Nie unieważnia to pozycji — **poszerza ją**: modułów, w których powtórzone wołanie
kosztuje, jest więcej niż tych, które chodzą po drzewie.

## 8. Przewidywania — i dlaczego siedem trafień NIC NIE ZNACZY

| # | przewidywanie | wynik |
|---|---|---|
| S1 | kontrola: 13 wołań / 3 pary | trafione |
| S2 | modułów z czytnikiem: 30–60 | trafione (45) |
| S3 | spełniających warunek: 20–45 | trafione (39) |
| S4 | udział powyżej połowy | trafione (87 %) |
| S5 | `test_commit_claims.py` NIE ma czytnika drzewa | trafione |
| S6 | najdroższy czytnik NIE w `test_message_claims.py` | trafione |
| S7 | oszczędność z czasu własnego mniejsza niż z inkluzywnego | **NIEROZSTRZYGALNE** — przyrząd inkluzywny okazał się nieważny, więc nie ma czego porównać |
| S8 | znajdzie się czytnik nigdy niewołany | trafione (cztery) |

**Siedem trafionych na osiem nie jest sukcesem przewidywania i mówię to wprost.**
Przewidywania spisałem przed **własnym** pomiarem, ale **po** przeczytaniu cudzego
pomiaru tych samych wielkości, który stał już w tej sesji. Przedziały S2 i S3 mieszczą
i tamte liczby, i moje. To jest ta sama uwaga, którą zapisałem przy 6.D303 o przedziale
„0–25": **trafienie mówi o szerokości przedziału i o tym, co już wiedziałem, a nie
o tym, że przewidziałem cokolwiek.**

Jedyna pozycja, która czegoś dowodzi, to S7 — i ona wyszła **nierozstrzygalna**,
bo przyrząd, o który pytała, trzeba było wyrzucić.

## 9. Czego świadomie nie zrobiono

- **Nie dopisano pamięci do żadnego czytnika** — pole zabrania, a 6.D297 nazwało to
  osobnym krokiem. **Lista jest listą KANDYDATÓW, nie zaleceń**, i to nie jest
  formalność: 6.D297 zmierzyło dwa warunki bezpieczeństwa (klucz musi nieść obie części
  pary; pamięć musi stać w ciele funkcji), a **żadnego z nich nie sprawdziłem dla
  trzydziestu dziewięciu modułów**.
- **Nie zmieniono `SUITE_RUNTIME_BUDGET_S` ani `SUITE_CPU_BUDGET_S`** — mimo że
  siedemdziesiąt pięć sekund z okładem szacowanej oszczędności byłoby kuszącym powodem.
  Progi opisują zestaw na runnerze, a szacunek nie jest pomiarem. Liczba stoi tu **słowem
  i to nie jest ozdoba**: `test_report_claims.py` przeczytał pierwszą wersję tego wiersza
  jako twierdzenie, że stała ma wartość siedemdziesiąt pięć i trzy dziesiąte, przy kodzie
  mówiącym czterysta czterdzieści — bo `CLAIM` czyta nazwę w grawisach i pierwszą liczbę
  za nią. **To samo zdarzyło się przy 6.D292 i 6.D297, czyli TRZECI raz, i za każdym razem
  na zdaniu o NIEZMIENIANIU progu.** Wyjątku do bramki nie dodaję — zdanie o tym, że
  czegoś nie ruszyłem, nie potrzebuje cyfry obok nazwy stałej.
- **Nie zmieniono żadnego czytnika** ani jego nazwy — 6.D297 §3 zmierzyło, że
  przemianowanie oślepia bramkę czytającą źródło po nazwie; dlatego przyrząd owija
  obiekt w `sys.modules`, a nie rusza źródła.
- **Nie poprawiono pola „Skąd"**, choć §7 pokazuje, że łączy dwa mechanizmy — pomiaru
  z datą się nie przelicza.
- **Nie tknięto `src/`, `data/` ani prozy w `tools/tests/`.**

## 10. Zauważone przy okazji, nietknięte

1. **Cztery czytniki są zadeklarowane i nigdy niewołane:** `main`
   w `test_bin_path_framework.py` i w `test_game_needle_specificity.py`,
   `dwie_miary_czytnikow` w `test_prose_counts.py`, `swiadkowie_klasy`
   w `test_tree_walks.py`. Dwa pierwsze to punkty wejścia i mają prawo nie być wołane
   z testów; dwa pozostałe nie.
2. **`test_tree_writes.py::_otwarcia_do_zapisu` chodzi 23 270 razy.** Czy pamięć
   o kluczu z sześciu tysięcy pięciuset osiemnastu par w ogóle się opłaca, ta pozycja
   nie pyta — koszt pamiętania może tu przewyższyć koszt liczenia, dokładnie tak jak
   przewyższył go koszt mierzenia w §3.
3. **Lista posortowana po LICZBIE wołań daje zupełnie inne czoło niż ta sama lista po
   koszcie.** `_docstringi` jest szósty po czasie i drugi po powtórzeniach.
