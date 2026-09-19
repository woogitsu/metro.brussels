# 6.D300 · Dwie reguły, których 6.D291 nie napisało — klasa nieorzekalna schodzi o 44 %

**Data:** 19.09.2026 · **Gałąź:** `claude/sharp-ramanujan-jdr51o` · **Baza:** `d1097ac`

6.D291 §4 zostawiło w swoim slajsie trzy wpisy, których rozbiór składniowy nie umie
orzec, i zapisało decyzję: **dalej nie uszczelniam**, bo piąta poprawka musiałaby już
dobierać przypadki. Ta pozycja liczy to samo na całym korpusie i pyta, czy taka reguła
istnieje. **Istnieje, i są dwie.**

---

## 1. Populacja — dwie, bo kontrola przyrządu wymaga tej szerszej

Definicja spisana przed liczeniem mówiła o wyrażeniach `a - b` stojących
**składniowo w komunikacie** asercji (`wezel.msg`) w `tools/tests/*.py`. Nazywam ją
**P1**. Czytnik pożyczony: `komunikaty()` z `test_message_claims.py` zwraca sam węzeł
`ast.Assert`.

Pomiar pokazał od razu, że P1 **nie zawiera** dwóch z trzech wpisów nazwanych
w 6.D291 §4 — bo tam `a - b` stoi w **przypisaniu**, a do komunikatu trafia już
gotowa nazwa (`margines = NIEMIERZALNY_ROZSTEP - granica`, potem `%s` z `margines`).
Slajs 6.D291 sięgał przez jedno przypisanie, mój nie.

Nie zwężam wobec tego kontroli do tego, co akurat wyszło, i nie podmieniam definicji
po cichu: **podaję obie populacje**, a kontrolę przyrządu stosuję do tej, której ona
dotyczy.

* **P1 — wąska:** `a - b` składniowo w komunikacie.
* **P2 — szeroka:** P1 plus `a - b` w przypisaniu nazwy interpolowanej w komunikacie
  (jeden skok, dokładnie tak jak w 6.D291).

## 2. Trzy liczby, w czterech wariantach reguły

| wariant | razem | LICZBOWE | ZBIOROWE | NIEORZEKALNE | SPORNE |
|---|---|---|---|---|---|
| P1 wąska, reguła 6.D291 | 55 | 6 | 34 | **15** | 0 |
| P2 szeroka, reguła 6.D291 | 132 | 20 | 69 | **43** | 0 |
| P2 + rozpakowanie krotki | 132 | 21 | 69 | **42** | 0 |
| P2 + rozpakowanie + stałe modułu | 132 | 22 | 86 | **24** | 0 |

Klasa **SPORNA** — spełniająca oba warunki naraz — jest pusta we wszystkich czterech
wariantach. Liczyłem ją osobno, bo klasa, która się nie sumuje, byłaby gorsza niż
klasa pusta; nie ma jej.

## 3. Kontrola przyrządu — ZDANA na P2, i to jest jej właściwa populacja

| wpis z 6.D291 §4 | P1 | P2, reguła 6.D291 |
|---|---|---|
| `NIEMIERZALNY_ROZSTEP - granica` | poza populacją | **NIEORZEKALNE** |
| `notes['counting_rules']['unique_stop_names'] - …` | poza populacją | **NIEORZEKALNE** |
| `wszystkie - wolne` | **NIEORZEKALNE** | **NIEORZEKALNE** |

Wszystkie trzy wychodzą w klasie nieorzekalnej, gdy czytnik pracuje na tej samej
populacji i tą samą regułą, co tamta pozycja. Czytnik mierzy więc to, co 6.D291,
a nie coś innego.

## 4. ODPOWIEDŹ NA PYTANIE POLA: TAK, reguła istnieje — i są dwie

Pole pyta, czy klasa nieorzekalna daje się zmniejszyć regułą, **która nie dobiera
przypadków**, i dopuszcza odpowiedź „nie". Odpowiedź brzmi **tak**.

**Reguła A — rozpakowanie krotki jest przypisaniem.** `wszystkie, wolne =
int(liczby.group(1)), int(liczby.group(2))` wiąże obie nazwy z jawnymi liczbami.
Reguła jednego skoku z 6.D291 czytała tylko cel będący pojedynczą nazwą, więc
rozpakowania nie widziała. Wypowiada się bez patrzenia na wynik: *jeżeli lewa i prawa
strona przypisania są krotkami tej samej długości, każda nazwa po lewej wiąże się
z odpowiadającym jej wyrażeniem po prawej.* Efekt: 43 → 42.

**Reguła B — stała modułu jest przypisaniem w zasięgu.** `NIEMIERZALNY_ROZSTEP` stoi
na poziomie modułu, a reguła 6.D291 szukała przypisań wyłącznie w ciele funkcji.
Wypowiada się bez patrzenia na wynik: *jeżeli nazwa nie ma przypisania w funkcji,
a ma na poziomie modułu, bierze się to drugie.* Efekt: 42 → 24.

Razem **43 → 24, czyli o 44 % mniej**. Żadna z tych reguł nie wymienia pliku, testu
ani wartości; obie są zdaniami o składni Pythona, nie o zawartości tego drzewa.

**Co to mówi o 6.D291:** decyzja „dalej nie uszczelniam" była słuszna **jako decyzja
tamtej pozycji** — jej autor nie miał policzonego korpusu i nie mógł wiedzieć, czy
piąta poprawka byłaby regułą, czy doborem. Zdanie „piąta musiałaby już dobierać
przypadki" jest jednak **zmierzone jako nieprawdziwe**: piąta i szósta są regułami.
Liczby tamtej pozycji zostają, bo ich ta poprawka nie dotyczy — 3 z 16 w tamtym
slajsie było policzone regułą, którą tamta pozycja miała.

**Reguły nie dopisałem do żadnej bramki** i to jest zgodne z polem „Poza zakresem",
które zabrania bramki na kształcie wyrażenia. Pozycja liczy i nazywa; wdrożenie jest
osobnym krokiem.

## 5. Co zostaje nieorzekalne i dlaczego żadna reguła tego nie ruszy

Dwadzieścia cztery wpisy zostają, a ich kształt jest jednorodny: **oba operandy to
indeks albo atrybut**, czyli wartości, których typ zna dopiero wykonanie. Trzy
rodziny:

* **indeks w strukturze z JSON-a** — `notes['counting_rules']['unique_stop_names'] - …`
  (`test_network_declarations.py`), `widziane['const'] + widziane['static readonly'] - …`
  (`test_dead_constants_csharp.py`);
* **geometria po współrzędnych** — dziesięć wpisów w `test_clearance_profile.py`
  w rodzaju `ring[(i + 1) % count][0] - ring[i][0]`;
* **wynik wywołania** — `documented_paths() - real_paths()` (`test_architecture_doc.py`),
  `datetime.date.today() - poczatek` (`test_timing_record.py`).

Żadnej z tych trzech nie rozstrzyga składnia. Rozstrzygnęłoby dopiero wnioskowanie
o typach — a tego pole „Poza zakresem" zabrania wprost i słusznie: `a[0] - b[0]` może
być odejmowaniem liczb albo różnicą zbiorów i **żaden zapis w pliku tego nie mówi**.

Lista imienna wszystkich dwudziestu czterech stoi w wyjściu pomiaru w §2 tego raportu
poprzez wariant czwarty; tu wymieniam rodziny, bo to one są odpowiedzią, a nie same
adresy.

## 6. Przewidywania spisane PRZED pomiarem

| # | przewidywanie | wynik |
|---|---|---|
| 1 | `a - b` w komunikatach: 20–80 | trafione (P1: 55) |
| 2 | LICZBOWE to większość, 60–85 % | **OBALONE** — 10,9 % |
| 3 | ZBIOROWE: 2–12 | **OBALONE** — 34 |
| 4 | NIEORZEKALNE: 4–20 | trafione (15) |
| 5 | SPORNE: 0–2 | trafione (0) |
| 6 | trzy wpisy 6.D291 w klasie nieorzekalnej | trafione na P2; dwa są poza P1 |
| 7 | reguły bez dobierania przypadków NIE MA | **OBALONE** — są dwie, §4 |
| 8 | udział inny niż 3/16 ze slajsu 6.D291 | trafione dla P1 i P2 — z zastrzeżeniem niżej |

Cztery trafione, trzy obalone. **Przewidywania 2 i 3 są obalone razem i z tego samego
powodu**: założyłem, że odejmowanie w komunikacie testu to głównie arytmetyka.
Jest odwrotnie — sześćdziesiąt dwa procent to **różnica zbiorów**, bo dominującym
idiomem tych bramek jest „co jest tu, a nie tam", wypisywane w obie strony. Nie
policzyłem tego przed pomiarem, tylko zgadłem z nazwy operatora.

**Zastrzeżenie do ósmego, spisane przed pomiarem i honorowane teraz:** po obu
poprawkach udział wynosi 18,2 %, a slajs 6.D291 miał 18,8 %. To jest **zbieg**,
a nie potwierdzenie przenoszalności — jedna liczba na jednym slajsie nie jest regułą,
a wariant, w którym te dwie liczby są sobie bliskie, jest inny niż wariant, którym
mierzyła tamta pozycja.

## 7. Czego świadomie nie zrobiono

- **Nie poprawiono ani jednej asercji** — pole „Poza zakresem".
- **Nie postawiono bramki na kształcie wyrażenia** — pole zabrania, a §4 mówi, że
  wdrożenie reguł A i B jest osobnym krokiem.
- **Nie napisano analizatora typów** — §5 pokazuje, że tylko on ruszyłby resztę.
- **Nie zmieniono liczb 6.D291** — jego 3 z 16 było policzone regułą, którą tamta
  pozycja miała; poprawiam jego **zdanie o regule**, nie jego pomiar.
- **Nie tknięto `data/` ani `src/`.**

## 8. Zauważone przy okazji, nietknięte

Reguła B przesunęła siedemnaście wpisów nie do klasy liczbowej, tylko do
**zbiorowej** (69 → 86): to są przypięte zbiory modułowe, `frozenset` i `set`, do
których bramki odejmują dzisiejszy stan drzewa. Znaczy to, że klasa nieorzekalna
w 6.D291 była w większości nie „odejmowaniem liczb", jak tamta pozycja opisała trzy
swoje wpisy, tylko **różnicą zbiorów, której reguła nie sięgała przez granicę
zasięgu**. Ile bramek tego zestawu odejmuje dzisiejsze drzewo od przypiętego zbioru
modułowego i ile z nich wypisuje różnicę w obie strony, ta pozycja nie pyta.

## 9. Zapadka, którą ten commit MUSIAŁ obniżyć

Dopisanie tego raportu zaczerwieniło
`test_podloga_sciezek_na_raport_jest_ZABOKSOWANA_pomiarami`:

```
FAIL test_podloga_sciezek_na_raport_jest_ZABOKSOWANA_pomiarami: drzewo daje 6.00
sciezki na raport przy podlodze 5 — zapas zszedl ponizej jednej pelnej sciezki
(2560 trafien wobec 2562 wymaganych)
```

Różnica wynosiła **dwa trafienia**. Komunikat bramki żąda obniżenia
`SCIEZEK_NA_RAPORT_MIN` w tym samym commicie — zrobiłem to **po przeliczeniu obu
brzegów**, a nie na słowo komunikatu:

| K | brzeg od dołu (`checked*K > zawezony`) | brzeg od góry (`seen >= checked*(K+1)`) |
|---|---|---|
| 3 | **nie** — 1281 < 1666 | tak |
| 4 | **tak** — 1708 > 1666 | **tak** — 2560 ≥ 2135 |
| 5 | tak | **nie** — 2560 < 2562 |

Przedział to dziś `{4}`: jedna wartość, tak samo jak przy poprzedniej zmianie.
Obniżenie **nie osłabia** kontroli — brzeg od dołu nadal czerwienieje na zawężeniu
kontrolnym, a nowa podłoga żąda 1708 trafień wobec 500 z zapadki, którą zastąpiła.

**Akapitu przy stałej NIE przepisałem, i to jest wynik sprawdzenia, nie pominięcie.**
Stoi tam zdanie „5 je łapie, a 4 już nie", które dziś byłoby nieprawdą jako zdanie
o drzewie — ale **nie jest zdaniem o dzisiejszym drzewie**: cały akapit otwiera
nagłówek „Zmierzone 12.09.2026 na 288 raportach", więc jest datowanym pomiarem
i jako taki pozostaje prawdziwy. Rachunek dla dzisiejszych 427 raportów stoi w tym
paragrafie, a ogniwo łańcucha przy stałej na niego wskazuje.

## 10. Dlaczego przepisanie tamtego akapitu WYCOFAŁEM — i co przy tym zmierzyłem

Pierwsza wersja tej poprawki przepisywała akapit przy stałej. Zaczerwieniło to
**pięć dalszych bramek**, z których żadna nie dotyczy podłogi: obie zapadki górne
prozy (pogrubionych bez pokrycia 180 przy 175, gołych w prozie pomiarowej 262 przy
259) i trzy census pokrycia w `test_message_claims.py`. Zapadek górnych wolno
wyłącznie obniżać, więc nie było wyjścia „podnieś i jedź dalej".

Przy próbie doprowadzenia census do zgody z drzewem natrafiłem na rzecz, której nie
szukałem i która jest najciekawszym ubocznym wynikiem tej pozycji: **te zapadki nie
mają punktu stałego — mają cykl o długości dwa.** Pętla ustawiająca każdą zapadkę na
wartość zmierzoną i mierząca od nowa nie zbiega; oscyluje:

```
iter 0: zbieg=56 przypisanie=15 klasy={'kod': 12, 'proza': 43, 'mieszane': 1}
iter 1: zbieg=55 przypisanie=16 klasy={'kod': 12, 'proza': 42, 'mieszane': 1}
iter 2: zbieg=56 przypisanie=15 ...
iter 3: zbieg=55 przypisanie=16 ...
```

Powód jest zrozumiały, gdy się go zobaczy: **wpisana wartość zapadki jest liczbą
w module, który tę samą klasę liczb mierzy.** Liczba stojąca obok swojej stałej
liczy się jako „pokryta przypisaniem"; ta sama liczba wpisana o wiersz dalej bywa
„pokryta zbiegiem". Ustawienie zapadki przesuwa więc jeden wpis między dwiema
klasami, a to zmienia liczbę, którą trzeba wpisać.

Wycofałem wobec tego całe przepisywanie prozy i zostawiłem w commicie **wyłącznie
zmianę wartości i ogniwo łańcucha**. Cały zestaw jest wtedy zielony bez ruszania
ani jednej zapadki census — bo prozy, którą one mierzą, nikt nie tknął.

**Druga rzecz, zmierzona przy okazji i zgodna z 6.D296 co do mechanizmu:** moje
pierwsze ogniwa łańcucha miały po kilka wierszy i **wypchnęły dwie pogrubione liczby
poza okno pokrycia** ich własnych stałych (`**12**` i `**1**`). 6.D296 policzyło
dobę wcześniej, że dopisanie pięciu wierszy zabija co szósty wpis klasy `zbieg`;
zobaczyłem to na własnym commicie. Ogniwo, które tu został, ma **jeden wiersz**.

Czego ta pozycja z tym **nie** robi: nie zmienia żadnej z tych zapadek, nie dopisuje
bramki na cykl i nie rozstrzyga, czy cykl jest usterką, czy własnością. Zapisuję go
jako pomiar; rozstrzygnięcie wymaga decyzji, której ta pozycja nie ma.
