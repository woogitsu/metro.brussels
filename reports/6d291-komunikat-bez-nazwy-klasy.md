# 6.D291 · Usterka jest klasą, a populacja klasy wynosi ZERO — i to jest wynik

**Data:** 19.09.2026 · **Gałąź:** `claude/sharp-ramanujan-jdr51o` · **Baza:** `099422d`

Przy 6.D234 KN-1 (typ bez wołającego nigdzie) i KN-2 (typ wołany wyłącznie
z `tests/`) dały komunikat **identyczny**, choć to dwa różne zbiory i dwa różne
rozstrzygnięcia. Poprawiono to w tym samym commicie. Ta pozycja pyta, ilu asercji
w drzewie dotyczy ten sam kształt.

---

## 1. SLAJS ZDEFINIOWANY PRZED LICZENIEM — i to jest treść pozycji, nie wstęp

Pole „Wyjście" żąda liczby „policzonej ze slajsu **zdefiniowanego** (nie dobranego)".
Definicja stanęła więc w scratchpadzie **przed uruchomieniem czegokolwiek** i jest
przepisana tu bez zmian:

> Asercja należy do slajsu wtedy i tylko wtedy, gdy spełnia OBA warunki:
> **S1.** Ma komunikat, a w komunikacie interpoluje WARTOŚĆ KOLEKCYJNĄ.
> **S2.** Ta wartość powstaje z WIĘCEJ NIŻ JEDNEGO ŹRÓDŁA — w jej wyrażeniu (albo
> w przypisaniu, które ją tworzy, w tej samej funkcji) stoją co najmniej dwie różne
> nazwy będące kolekcjami.
>
> Asercja ze slajsu jest USTERKĄ wtedy i tylko wtedy, gdy TEKST komunikatu nie
> pozwala orzec, DO KTÓREGO ze źródeł należy wypisany element.

Trzy rzeczy definicja świadomie wyklucza, żeby nie dało się jej potem naciągnąć:
asercję bez komunikatu, asercję wypisującą LICZBĘ zamiast kolekcji, i asercję,
której kolekcja ma JEDNO źródło.

Zapisany był też warunek obalenia: **przypadek założycielski ma być w slajsie
i NIE ma być na liście usterek**; gdyby wyszło inaczej, poprawiam OPIS, nie wynik.

## 2. Liczby

| | |
|---|---|
| S1 — komunikat interpoluje kolekcję | **366** |
| S1 + S2 — slajs maszynowy | **16** |
| minus fałszywe trafienia znalezione CZYTANIEM | **13** |
| **usterek** (komunikat nie mówi, do której listy) | **0** |

Z trzynastu: **dwie** niosą nazwę klasy w PAYLOADZIE (maszyna umie to sprawdzić),
**jedenaście** nazywa ją w PROZIE komunikatu (maszyna nie umie).

## 3. Sito myliło się CZTERY RAZY — i każda pomyłka jest opisana, nie załatana

Nie jest to lista przypadków; to jest odpowiedź na pytanie z pola „Wyjście",
bo każda pomyłka nazywa granicę rozbioru składniowego.

**Pomyłka pierwsza — krotka argumentów wzięta za kolekcję.** `"%s %s" % (a, b)` ma
po prawej `ast.Tuple`, a mój test „czy to kolekcja" na krotce mówił TAK. Każdy
komunikat o dwóch argumentach wchodził do S1. **S1 dawało 760.** Poprawka: rozbicie
krotki formatowania na elementy.

**Pomyłka druga — warunek zawsze prawdziwy.** Napisałem `len(…) >= 2 or True`.
`or True` czyni całość prawdą niezależnie od lewej strony. Różnica i suma zbiorów
**rzeczywiście** mają dwa operandy z definicji, więc wynik był przypadkiem zgodny
z intencją — ale z powodu literówki, a nie z reguły. Przepisane na regułę wprost.

**Pomyłka trzecia — i to ją złapał PRZYPADEK ZAŁOŻYCIELSKI.** Po dwóch poprawkach
slajs liczył 27 asercji, a `test_csharp_type_callers.py` **w nim nie stał**. Zgodnie
z warunkiem obalenia spisanym przed pomiarem znaczyło to, że sito mierzy co innego,
niż mówi definicja. Powód: poprawiona wersja tamtej asercji buduje wartość jako
`listcomp + listcomp`, a `ast.Add` stał w mojej funkcji „czy z wielu źródeł"
i **nie stał** w funkcji „czy to kolekcja". Niezgodność dwóch moich własnych funkcji
wyrzucała ze slajsu dokładnie tę asercję, od której cała pozycja się zaczęła.

**Pomyłka czwarta, najważniejsza — `-` jest RÓŻNICĄ ZBIORÓW i ODEJMOWANIEM LICZB.**
AST ich nie odróżnia bez znajomości typów. Do slajsu wchodziły `required - 1`,
`len(wszystkie) - len(zostalo)`, `SUITE_RUNTIME_BUDGET_S - MEASURED_MAX_WALL_S`,
`checked - datowane`. Poprawka dwuczęściowa: `-` liczy się za różnicę zbiorów tylko
wtedy, gdy żaden operand nie jest jawnie liczbą, a „jawnie liczba" idzie przez JEDNO
przypisanie — tak samo, jak „jest kolekcją" szło przez nie od początku. **Brak tej
symetrii był całą usterką:** `zapas = BUDGET - MAX_WALL` i `checked = 0` są liczbami
o wiersz wyżej.

Przebieg liczb przez cztery poprawki: **760 → 377 → 378 → 371 → 366** dla S1
oraz **31 → 27 → 28 → 21 → 16** dla slajsu.

**Liczba slajsu 31 → 27 ukryła podmianę składu**, tak samo jak przy 6.D284: część
wpisów wyszła, część weszła, a sama liczba spadła o cztery. Dlatego listy imienne
są w tym raporcie przy każdej liczbie, a nie tylko suma.

## 4. Gdzie sito ZOSTAŁO nieszczelne — i dlaczego nie uszczelniam dalej

Po czwartej poprawce w slajsie stoją **trzy** wpisy, które czytanie wskazuje jako
odejmowanie liczb, a AST nie umie tego orzec, bo oba operandy są nieprzezroczyste:

| wpis | wyrażenie | czym jest naprawdę |
|---|---|---|
| `test_linecore_budget_gate.py:731` | `NIEMIERZALNY_ROZSTEP - granica` | odejmowanie liczb |
| `test_network_declarations.py:204` | `rules['unique_stop_names'] - rules['unique_stations']` | odejmowanie liczb |
| `test_doctor_queue_claim.py:137` | `wszystkie - wolne` (obie z `int(…)` po regule) | odejmowanie liczb |

**Dalej nie uszczelniam i to jest decyzja, nie zaniechanie.** Punkt 11 przewidywań
brzmiał: „nie zwężę definicji slajsu po zobaczeniu liczby; jeśli liczba wyjdzie
niewygodna, zostaje niewygodna". Cztery dotychczasowe poprawki usuwały **błędy
reguły** — każda ma powód dający się wypowiedzieć bez patrzenia na wynik. Piąta
musiałaby już dobierać przypadki. Trzy fałszywe trafienia na szesnaście to
**zmierzona skuteczność sita**, którą podaję, zamiast ukryć.

Slajs prawdziwy wynosi więc **13**, a slajs maszynowy **16**.

## 5. Usterek jest ZERO — lista imienna trzynastu

Każda z trzynastu nazywa klasę albo kierunek różnicy. Wzorce, jakie stosują:

**Obie strony wypisane osobno** — `test_data_thresholds.py:213` („tylko tu %s;
tylko tam %s"), `test_message_claims.py:1825` („w drzewie, a nie na liście: %s /
na liście, a nie w drzewie: %s"), `test_mutation_sweep.py:950` („tylko sonda: … ,
tylko import: …"), `test_report_hygiene.py:1131` („we wzorcu, brak w kodzie: … /
w kodzie, brak we wzorcu: …").

**Kierunek nazwany w zdaniu** — `test_ci_workflows.py:1311` („CI woła argumenty,
których scena nie zna"), `test_field_paths.py:1249`, `test_tree_walks.py:1297`
(„różnica ma iść TYLKO w jedną stronę"), `test_provenance_classes.py:839` i `:846`,
`test_message_claims.py:371` (nazywa nawet listę docelową: „dopisz do `WYJATKI`"),
`test_csharp_pins.py:193` (dwie asercje, każda ze swoją klasą).

**Klasa w payloadzie, nie w prozie** — `test_csharp_type_callers.py:203`
(przypadek założycielski, pary `(nazwa, "tylko testy")`) oraz
`test_dead_constants_csharp.py:373` (wypisuje cały rozkład per gałąź).

**Przypadek założycielski jest w slajsie i nie jest usterką** — warunek obalenia
z §1 spełniony w obie strony.

## 6. Kontrole negatywne — i KN-1 jest ODPOWIEDZIĄ, nie sprawdzianem

Plik wszedł do historii już w postaci poprawionej (poprawka i pierwsza wersja
powstały w jednym commicie `8c0fd72`), więc wersji sprzed poprawki w gicie nie ma.
Kontrola jest więc **syntetyczna**, wykonana na kopii drzewa narzędzi.

```
BAZA (komunikat NAZYWA klase, w payloadzie)          S1=366 slajs=16 | zalozycielski w slajsie: True
KN-1 (postac SPRZED poprawki: klasa znika)           S1=366 slajs=16 | zalozycielski w slajsie: True
KN-2 (kolekcja z JEDNEGO zrodla)                     S1=366 slajs=15 | zalozycielski w slajsie: False
po przywroceniu                                      S1=366 slajs=16 | zalozycielski w slajsie: True
```

**KN-2 zachowuje się tak, jak zaprojektowano:** kolekcja z jednego źródła wypada
ze slajsu, 16 → 15. Warunek S2 niesie treść.

**KN-1 daje wynik IDENTYCZNY z bazą — i to jest wynik tej pozycji.** Odtworzyłem
postać sprzed poprawki, czyli **jedyną znaną usterkę tej klasy**, i sito nie
odróżniło jej od postaci poprawionej ani jedną cyfrą. Usterka i jej naprawa są dla
maszyny nierozróżnialne.

## 7. Rozstrzygnięcie o sicie, z powodem

**Slajs — TAK, maszynowo, z błędem nazwanym.** S1 i S2 są własnościami składni: AST
widzi interpolację i widzi, ile nazw kolekcyjnych stoi w wyrażeniu. Błąd wynosi
3 z 16 i pochodzi z jednego miejsca — wieloznaczności `-`.

**Usterka — NIE, maszynowo.** Dowodzi tego KN-1, a nie rozumowanie. Powód jest
głębszy niż jeden przypadek: **naprawa ma dwie legalne postacie**, a maszyna widzi
tylko jedną z nich. Klasę można wpisać do PAYLOADU (jak w przypadku założycielskim
i w `test_dead_constants_csharp.py`) — wtedy automat może sprawdzić, że w wyrażeniu
stoi literał napisowy. Można ją też nazwać w PROZIE komunikatu — i tak robi
**jedenaście z trzynastu**. Zdania „tylko tu / tylko tam" żaden automat nie orzeknie
za poprawne, bo poprawność jest własnością języka, nie składni.

Pole „Wyjście" dopuszcza wprost odpowiedź „nie da się i dlaczego". To jest ta
odpowiedź, z liczbą przy każdej połowie.

## 8. Przewidywania spisane PRZED pomiarem

| # | przewidywanie | wynik |
|---|---|---|
| 1 | S1: 40–90 | **PUDŁO**, jest 366 |
| 2 | slajs: 12–30 | trafione (16 maszynowo, 13 po czytaniu) |
| 3 | usterek: 3–10 | **PUDŁO**, jest 0 |
| 4 | założycielski w slajsie, nie na liście usterek | trafione — po trzech poprawkach sita |
| 5 | maszynowo: NIE dla usterki, TAK z błędem dla S1/S2 | trafione, a KN-1 to udowodniła |
| 6 | pierwsza wersja sita się pomyli | trafione **cztery razy** |
| 7 | co najmniej jedna „usterka" okaże się nie usterką | trafione — wszystkie |

**Pudło trzecie jest pierwszym dziś w DRUGĄ stronę.** Przy 6.D287, 6.D288, 6.D289
i 6.D290 moje przedziały wychodziły za niskie; tutaj za wysoki. Spodziewałem się
kilku usterek, bo kształt jest tani do napisania — a zmierzyłem zero. Wniosek nie
brzmi „klasa nie istnieje": klasa istnieje i została zmierzona przy 6.D234 na żywym
przypadku. Brzmi **„klasa istnieje, a populacja dziś wynosi zero"**, i te dwa zdania
nie są tym samym.

## 9. Czego świadomie nie zrobiono

- **Nie poprawiono ani jednego cudzego komunikatu** (pole „Poza zakresem").
- **Nie zmieniono treści żadnej asercji.**
- **NIE POSTAWIONO BRAMKI na kształcie komunikatu** — pole „Poza zakresem" zabrania
  tego wprost. Zapisuję to osobno, bo po 6.D289, gdzie werdykt dostał asercję, miałem
  odruch odwrotny; tam bramki nie zabraniało żadne pole, tutaj zabrania nazwanym
  słowem. Sito i obie kontrole zostały w scratchpadzie.
- **Nie uszczelniono sita piąty raz** — §4, z powodem spisanym przed pomiarem.
- **Nie dotknięto `data/`.**

## 10. Zauważone przy okazji, nietknięte

Dwa z trzynastu niosą klasę w payloadzie, jedenaście w prozie. Gdyby projekt chciał
kiedyś tę własność pilnować maszynowo, musiałby najpierw **rozstrzygnąć, że payload
jest postacią obowiązującą** — czyli zmienić jedenaście cudzych komunikatów. Jest to
decyzja projektowa o koszcie w cudzych plikach, a nie pomiar, więc ta pozycja jej
nie podejmuje i nie zapisuje jako zadania.
