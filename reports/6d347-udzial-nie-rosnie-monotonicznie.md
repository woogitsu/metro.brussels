# 6.D347 · Udział NIE rośnie monotonicznie — spada w 145 rewizjach na 455, czyli w co trzeciej

**Data:** 21.09.2026 · **Gałąź:** `claude/new-session-1xabcy` · **Baza:** `6ade0e2`

6.D337 przesunęło górną stronę pasma ułamka, bo przestawienie jednej pozycji na
WYKONANE przebiło je o dwa adresy — i **tempa tego wzrostu nie zmierzyło ani nie
udawało, że mierzy**. Ta pozycja mierzy tempo na całej historii `docs/TASKS.md`.

Definicje i sześć przewidywań stoją w `DEFINICJE.md`. **Kolejność ich spisania była
naruszona i jest to zapisane tam, a nie zatarte:** przyrząd powstał pierwszy,
przewidywania drugie — ale spisano je, gdy `out.txt` miał **zero bajtów**, czyli
w tej samej niewiedzy, w której powinny były powstać na początku.

---

## 1. Czytnik jest ten sam na każdej rewizji, a historia PRZYPIĘTA do bazy

Przyrząd pożycza `adresy_pola_w_wykonanych` i `wywolania_pola_w_wykonanych`
z `tools/tests/test_field_paths.py` — dokładnie te, które liczy bramka ułamka —
i podmienia wyłącznie **tekst** `docs/TASKS.md` na treść danej rewizji. Czytnik jest
jeden dla wszystkich 569 rewizji, więc mierzona jest zmiana **korpusu**, a nie zmiana
czytnika.

**Historia idzie od `BASE_SHA = 6ade0e2`, a nie od ruchomego `HEAD`, i to jest
poprawka wprowadzona W TRAKCIE pomiaru, nie od początku.** Pierwszy pełny przebieg
wziął `git log HEAD`, a w jego trakcie do `docs/TASKS.md` doszedł kolejny commit —
liczba rewizji urosła z 569 na 570, a „wierzchołek" przestał być tym, o którym mówi
pole tej pozycji. Repozytorium ruszyło się pod pomiarem. Przypięcie do bazy zamyka to
raz: ten sam przebieg uruchomiony jutro da te same liczby.

Historia brana **bez** `--follow`. Sprawdzone własnym przebiegiem, nie przyjęte:

```
$ git log --format=%H 6ade0e2 -- docs/TASKS.md | wc -l
569
$ git log --follow --format=%H 6ade0e2 -- docs/TASKS.md | wc -l
504
```

`--follow` ucina **sześćdziesiąt pięć** rewizji, a plik nigdy nie był przemianowany —
`git log --diff-filter=A` daje jeden commit dodający (`17c5b39`). Ułamki liczone jako `Fraction`, nie
`float`, a listy sortowane przed medianą — powód jest zmierzony w 6.D341.

## 2. Kontrola przyrządu ZDANA w obu połowach

```
"kontrola_obejrzane": 248,        "kontrola_razem": 1982,   "kontrola_248_1982_ok": true
"przed_d337_obejrzane": 246,      "przed_d337_razem": 1977, "kontrola_przed_d337_ok": true
```

Pole żądało **248 i 1982** na wierzchołku oraz **246 i 1977** na rewizji poprzedzającej
commit 6.D337. Oba wychodzą co do jedynki.

**Wcześniejszy szkic tego raportu twierdził, że połowa „na dzisiejszym wierzchołku"
jest NIESPEŁNIALNA, bo pole zapisało ruchomy punkt jako liczbę bezwzględną. To było
nieprawdą i akapit jest przepisany, a nie dopisany obok.** Tamten wniosek wyciągnąłem
z przebiegu **nieprzypiętego**, w którym „wierzchołek" oznaczał commit dopisany już po
otwarciu pozycji. Po przypięciu do bazy warunek jest spełnialny i spełniony. Wada była
w moim przyrządzie, nie w polu — i dokładnie tak brzmiał warunek obalenia P1 spisany
przed pomiarem.

## 3. GŁÓWNE ZNALEZISKO: udział NIE rośnie monotonicznie

```
"liczba_rewizji_w_ktorych_zmienil_sie_ulamek": 457,
"liczba_przyrostow_miedzy_rewizjami_zmiany": 455,
"liczba_spadkow": 145,
```

**Spadków jest 145 na 455 przyrostów, czyli 31,9 % — prawie co trzeci.**

Przewidywanie **P3 jest obalone**, a warunek obalenia spisałem przed pomiarem
i wypełniam go co do słowa: **mianownik potrafi rosnąć szybciej niż licznik, więc
wzrost nie jest jednokierunkowy.** Mechanizm jest zmierzony i prosty: licznik rośnie
tylko wtedy, gdy blok wymienia moduł w polu „Weryfikacja", a mianownik rośnie przy
**każdym** adresie w trzech polach — więc blok bogaty w adresy, a ubogi w wywołania,
udział **obniża**.

To jest sprostowanie do wymowy 6.D337. Tamten raport mówił, że udział rośnie, „bo
bloki nowsze wymieniają moduły częściej niż stare" — jako opis **kierunku** trendu się
broni (pomiar 6.D158 dawał 101/1276, czyli 7,92 %; na bazie tej pozycji jest 256/2005,
czyli 12,77 %), ale jako opis **kształtu** nie: w co trzeciej rewizji zmieniającej
udział idzie w dół.

## 4. Tempo: mediana jest o rząd mniejsza, niż wyglądała z dwóch punktów

```
"mediana_przyrostu_float": 0.00015651232453879288,   ->  0,0157 punktu procentowego
"max_przyrostu_float":     0.0030968693016642235,    ->  0,3097 pp
"min_przyrostu_float":    -0.0030005249025901923,    -> -0,3001 pp
```

Mediana przyrostu na rewizję zmieniającą to **0,016 punktu procentowego** —
przewidywanie **P4 trafione**, dodatnia i mniejsza niż 0,1 pp.

**Największy skok jest 19,8 raza większy od mediany**, więc **P6 trafione**: wzrost nie
jest równomierny. Skrajności są przy tym niemal symetryczne (**+0,310 pp** wobec
**−0,300 pp**), co domyka obraz z §3: to nie jest wzrost z drobnymi wahaniami, tylko
**ruch w obie strony z przewagą jednej**.

Zestawienie z 6.D337 jest tu pouczające. Tamta pozycja widziała **dwa punkty** —
246/1977 i 248/1982 — i z różnicy między nimi nie dało się powiedzieć nic o tempie.
Dało się powiedzieć tylko tyle, że pasmo pękło, i tyle właśnie powiedziała.

## 5. Dwa przewidywania obalone poza P3

```
"liczba_rewizji_docs_tasks_md_w_historii": 569,
"liczba_rewizji_z_zerowym_mianownikiem": 1,
"liczba_rewizji_z_okreslonym_udzialem": 456,
```

**P2 obalone**: rewizji zmieniających jest **457 z 569, czyli 80,3 %** — nie „mniej niż
połowa". Warunek obalenia mówił, że wtedy „rewizja zmieniająca" nie jest użytecznym
sitem, i tak jest: cztery na pięć commitów w ten plik ruszają którąś z dwóch liczb.

**P5 obalone**: rewizja z zerowym mianownikiem jest **jedna**, nie więcej — i jest to
**dokładnie ten commit, który plik utworzył**. Sprawdzone osobno, bo zgodności nie
zakładam:

```
$ git log --diff-filter=A --format="%h %ad" --date=short 6ade0e2 -- docs/TASKS.md
17c5b39 2026-08-31

rewizja z zerowym mianownikiem: 17c5b39   obejrzane 0   razem 0
```

Zero w liczniku i mianowniku nie jest więc dziurą w danych ani wypadkiem — jest
**stanem pliku w chwili narodzin**, w której nie ma jeszcze ani jednego bloku
wykonanego. Bloki wykonane pojawiły się zaraz potem. Liczbę tę podaję, zamiast taką rewizję pominąć
milcząco albo przyjąć dla niej 0/0 = 0; było to zapisane w definicjach przed pomiarem,
a przyrząd **padł** na niej przy pierwszym przebiegu i to wymusiło osobną klasę.

## 6. Przewidywania — trzy trafione, trzy obalone

| # | przewidywanie | wynik |
|---|---|---|
| P1 | kontrola przejdzie na obu punktach | **trafione** — ale dopiero po przypięciu historii do bazy; wcześniejszy przebieg dawał fałszywy wynik na ruchomym wierzchołku (§2) |
| P2 | rewizji zmieniających mniej niż połowa | **OBALONE**: 80,3 % |
| P3 | udział rośnie monotonicznie, zero spadków | **OBALONE**: 145 spadków, co trzeci (§3) |
| P4 | mediana dodatnia i mniejsza niż 0,1 pp | **trafione**: 0,016 pp |
| P5 | rewizji z zerowym mianownikiem więcej niż jedna | **OBALONE**: jedna |
| P6 | największy skok co najmniej 10× mediany | **trafione**: 19,8× |

## 7. Czego świadomie nie zrobiłem

Nie zmieniłem szerokości pasma ułamka, nie ruszyłem reguły kandydatów, nie prostowałem
żadnej pozycji, nie tknąłem `src/` ani `data/`.

**Nie orzekam o przyczynie** ani spadków, ani skoków. Podaję kształt i tempo; która
decyzja projektowa je wywołała, jest innym pytaniem i innym przyrządem.

**Nie policzyłem udziału na rewizjach POZA `docs/TASKS.md`.** Commit, który nie rusza
tego pliku, nie zmienia ani licznika, ani mianownika — ale historia takich commitów
mówiłaby, ile czasu upływa między zmianami, a to jest inne pytanie.

## 8. Co zauważyłem przy okazji, ale nie tknąłem

**Przyrząd padł przy pierwszym przebiegu na `ZeroDivisionError`** — na rewizji, w której
bloków wykonanych jeszcze nie było, mianownik wynosi zero. Poprawka nie polegała na
pominięciu takiej rewizji ani na przyjęciu 0/0 = 0, tylko na **policzeniu ich osobno**;
dlatego w wyniku stoi `liczba_rewizji_z_zerowym_mianownikiem`. Gdyby pominąć je
milcząco, `liczba_rewizji_z_pomiarem` (569) i `liczba_rewizji_z_okreslonym_udzialem`
(456) byłyby tą samą liczbą i nikt by nie zauważył, że jedna rewizja nie ma udziału
**z definicji**, a nie z braku danych.

**Drugie znalezisko jest o pomiarach w tym repozytorium w ogóle, nie o tej pozycji:**
pomiar chodzący po historii przez kilkanaście minut **nie jest odporny na to, że
repozytorium się w tym czasie rusza**. Tu ruszyło — doszedł commit, liczba rewizji
wzrosła o jeden, a „wierzchołek" przestał znaczyć to, co znaczył przy otwarciu pozycji.
Przypięcie do bazy z pola „Baza" raportu zamyka to dla tej pozycji; ile innych
przyrządów w katalogach roboczych liczy od ruchomego `HEAD`, nie sprawdzałem.
