# `doctor.sh` mówi o kolejce to, co w niej stoi (10.09.2026)

**Zmierzone 10.09.2026 na:** `7de8a9a`, kontener tej sesji.
**Przyrząd:** `doctor.sh --no-tests` puszczony na drzewie z podmienionym
`docs/TASKS.md`, `tools/tests/test_backlog.py` (`open_items`, nowe
`pole_zaleznosci`, `czeka_na_wlasciciela`, `do_wziecia`), nowy
`tools/tests/test_doctor_queue_claim.py`.

---

## 1. Zdanie o zbiorze wypowiadane bez zajrzenia do zbioru

`doctor.sh:411` wypisywał:

```
  Kolejka faz 5 i 6 ma $queue_count pozycji do wzięcia, żadna nie wymaga decyzji właściciela.
```

Liczba pochodziła z pliku (`len(open_items(...))`). Druga połowa zdania — z niczego.
W tej samej policzonej kolejce stała **6.D53**, której pole „Zależy od" brzmi
dosłownie „decyzji właściciela o zapisie do `data/network/sources.json`".

Ta sama rodzina co 6.D27: przyrząd melduje sprawdzenie, którego nie zrobił. Szkoda
nie jest teoretyczna — `CLAUDE.md` §2 każe czytać doctora przed KAŻDYM zadaniem.

## 2. Pomiar pól „Zależy od" na dzisiejszej kolejce

```
  6.D53: decyzji właściciela o zapisie do `data/network/sources.json`.
  6.D95: brak.        6.D96: 6.D79.       6.D97: 6.D74.       6.D98: 6.D81.
  6.D99: 6.D83.       6.D100: brak.       6.D101: 6.D73.      6.D102: 6.D86.
  6.D103: 6.D85.      6.D104: 6.D87.      6.D105: 6.D89.      6.D106: brak.
```

**Jedna z trzynastu** czeka na człowieka. Pozostałe dwanaście wskazują numery innych
pozycji albo nie mają zależności.

## 3. Wypis po poprawce

```
  Kolejka faz 5 i 6 ma 13 pozycji, z czego 12 do wzięcia od ręki.
  Na decyzję właściciela czeka: 6.D53 — tej nie bierz.
```

Gdy nikt nie czeka, zdanie „żadna nie wymaga decyzji właściciela" wraca — ale jako
**wynik pomiaru**, a nie napis stały. Obie strony są sprawdzone (sekcja 5, KN-2).

`open_items` nietknięte, jak żąda pole „Poza zakresem": nowe funkcje biorą jego wynik
i dzielą go na dwie kupki po treści pól.

## 4. Bramka uruchamia PRAWDZIWEGO doctora, na podmienionym drzewie

Kontrola z pola „Skończone, gdy" żąda pozycji **syntetycznej**, a nie zmiany
w `docs/TASKS.md`. Drzewo do przebiegu powstaje z symlinków: wszystko poza `docs/`
linkowane do repozytorium, w `docs/` wszystko poza `TASKS.md`, a `TASKS.md` jest
kopią z dopiskiem. Doctor sprawdza kilkanaście ścieżek i przy braku którejkolwiek
kończy PRZED blokiem o kolejce, więc kopia częściowa nie odpowiedziałaby na pytanie
tego testu.

**Atrapa `dotnet` jest konieczna z tego samego powodu.** W kontenerze tej sesji SDK
nie stoi w `PATH`, więc doctor melduje „1 wymaganych pozycji do naprawienia" i do
bloku z kolejką **nie dochodzi**. Pierwszy przebieg tej bramki napisałem bez atrapy
i wypis nie zawierał ani słowa o kolejce — test przechodziłby, nie zmierzywszy
niczego, gdyby nie asercja „doctor nie doszedł do bloku o kolejce".

## 5. Sześć kontroli negatywnych, `md5sum -c: OK` po każdej

| kontrola | mutacja | wynik |
|---|---|---|
| KN-1 | doctor wraca do zdania stałego | **czerwona** 2/4 |
| KN-2 | doctor ostrzega ZAWSZE, także gdy nikt nie czeka | **czerwona** 3/4 |
| KN-3 | szukane słowo zepsute (czytnik nie rozpoznaje niczego) | **czerwona** 0/4 |
| KN-4 | czytnik pola gubi drugą linię złamanego zdania | **czerwona** 3/4 |
| KN-5 | doctor liczy wolne pozycje jako WSZYSTKIE otwarte | **zielona** — nikt nie porównywał liczb |
| KN-5b | ta sama mutacja, po dodaniu asercji na arytmetykę | **czerwona** 3/4 |
| KN-6 | kotwica przestawiona na pozycję niezablokowaną | **czerwona** 2/4 |

**KN-5 wyszła zielona i to jest znalezisko o moich własnych bramkach.** Po podmianie
`do_wziecia` na `open_items` doctor wypisywał:

```
  Kolejka faz 5 i 6 ma 13 pozycji, z czego 13 do wzięcia od ręki.
  Na decyzję właściciela czeka: 6.D53 — tej nie bierz.
```

Zdanie sprzeczne samo ze sobą — trzynaście z trzynastu do wzięcia, a jedna
zablokowana — i **żadna z trzech bramek go nie widziała**, bo każda patrzyła na inną
połowę wypisu. Doszła asercja porównująca arytmetykę wiersza z długością nazwanej
listy; KN-5b na tej samej mutacji daje 3/4.

**KN-2 mierzy kierunek PRZECIWNY do KN-1 i dlatego stoi osobno**: pierwsza pyta, czy
ostrzeżenie się pojawia, gdy trzeba, druga — czy znika, gdy nie trzeba. Ostrzeżenie
wypisywane zawsze nie niesie informacji i przeszłoby bramkę zbudowaną tylko w jedną
stronę.

**KN-6 pilnuje kotwicy przed zgnilizną w drugą stronę:** gdyby 6.D53 kiedyś została
odblokowana, testy mają PAŚĆ i kazać przeliczyć kotwicę, a nie przejść dlatego, że
lista zrobiła się pusta.

## 6. Weryfikacja

```
python3 tools/tests/test_all.py test_doctor_queue_claim.py
  -> 4/4 przeszło

python3 tools/tests/test_all.py
  -> RAZEM 114,190 s, 2186 testów, 118 modułów, kod 0
  -> 2186/2186 przeszło

doctor.sh --no-tests (z atrapą dotnet, na dzisiejszym drzewie):
  Kolejka faz 5 i 6 ma 13 pozycji, z czego 12 do wzięcia od ręki.
  Na decyzję właściciela czeka: 6.D53 — tej nie bierz.
```

Zestaw **2182 → 2186**, moduły **117 → 118**. Zapadka `MIN_REPORTS` została w tym
commicie podniesiona ze dwustu trzynastu na dwieście czternaście — słownie, bo
`test_report_claims.py` czyta pierwszą liczbę po nazwie stałej jako twierdzenie o jej
bieżącej wartości.

## 7. Czego świadomie nie zrobiłem

Nie ruszyłem `open_items` ani kolejności brania pozycji — pole „Poza zakresem"
wyklucza jedno i drugie. Nie zdejmowałem wiersza o kolejce: pomiar pokazał, że
rozróżnienie DA SIĘ zrobić bez drugiego czytnika `docs/TASKS.md` w powłoce, bo
`test_backlog` już czyta ten plik i wystarczyło dodać mu dwie funkcje. Nie zmieniałem
pola „Zależy od" żadnej pozycji.

## 8. Zauważone i nietknięte

**Rozpoznanie idzie po słowie „właściciel" w polu „Zależy od" i to jest heurystyka.**
Zmierzone: dziś w całym `docs/TASKS.md` nie ma ani jednego pola „Zależy od", w którym
to słowo znaczyłoby co innego — ale pole zależne od człowieka, opisane bez tego słowa
(„czeka na odpowiedź STIB"), nie zostanie rozpoznane. Bramka łapie kształt, który
w tym repozytorium wystąpił; nowego nie przewidzi.

**Wolnych pozycji jest dokładnie dwanaście, czyli tyle, ile wynosi
`MINIMUM_READY_ITEMS`** — ale zapadka liczy `open_items`, czyli trzynaście, więc nie
zapala się. Jeżeli próg ma mówić o pozycjach DO WZIĘCIA, a nie o wpisanych, to jest
osobna decyzja i osobna pozycja; tutaj jej nie podejmuję.
