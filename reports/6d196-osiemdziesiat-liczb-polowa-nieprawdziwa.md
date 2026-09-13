# 6.D196 — osiemdziesiąt liczb, trzydzieści przeliczalnych, połowa nieprawdziwa

**13.09.2026**, na `0c1e499`. Wejście: `docs/TASKS.md` (pola „Skąd" pozycji bez adnotacji
ZROBIONE), `tools/tests/test_backlog.py` (`open_items`), `tools/tests/test_report_claims.py`
(mechanizm datowania z 6.D108), `reports/6d184-obcinacz-z-siedemnastu-do-jednego.md`.

## 1. Trzy liczby, których pozycja żądała ze źródeł

Szesnaście pozycji otwartych, z tego **dwanaście** ma blok szczegółów z polem „Skąd".

| | |
|---|---:|
| liczb w polach „Skąd" | **80** (42 w prozie + 15 dat + 20 numerów pozycji + 2 numery PR + 1 `§`) |
| z nich **PRZELICZALNYCH** automatem | **30** |
| z tych przeliczalnych **NIEZGODNYCH z drzewem** | **15 — połowa** |

## 2. Rozjazd ma CZTERY przyczyny, a nie jedną

Pozycja zakładała starzenie się **w czasie**. Pomiar pokazał co innego:

| przyczyna | ile |
|---|---:|
| (a) **cudza pozycja domknęła podstawę** | **10** |
| (b) drzewo urosło | 1 |
| (c) **liczba była nieprawdziwa W CHWILI WPISANIA** | **4** |

**(a) jest najliczniejsza i przesuwa tezę pozycji.** Pole „Skąd" cytujące inną pozycję
starzeje się **w chwili, gdy tamta zostaje domknięta** — nie po dniach. 6.D184
zlikwidowało `KodBezKomentarzy` (2 liczby), 6.D191 przepisało trzy zdania rodziny
(7 liczb), 6.D193 dopisało brakujące asercje (1 liczba).

**(c) to kategoria, której teza pozycji NIE PRZEWIDUJE.** 6.D199 pisze o „**dwóch**
trafieniach `phase.ToString()`", a trzecie leży w `src/Game/UI/UiText.cs` **od
10.09.2026** — czyli było tam w dniu wpisania. Liczba powstała ze skanu **płytszego niż
zapisany**, bez podkatalogu `UI/`. Tak samo 6.D201: „cztery postacie literału" przy
**pięciu** w `tests/` (`$@"…"` w `RunHeaderTests.cs`), a w `src/` jest nawet szósta
(`$$"""`). To nie jest zestarzenie się — to jest **pomiar zrobiony źle i zapisany jako
fakt**.

## 3. Co się trzyma, a co nie — i to rozstrzyga, gdzie postawić bramkę

**Wszystkie 11 liczb przypiętych stałą w kodzie zgadza się co do jedynki.**
**Wszystkie 15 niezgodnych to liczby, których NIC NIE PILNUJE.**

Rozstrzygnięcie dla trzech grup, których żądało pole „Wyjście":

| grupa | ile | rozstrzygnięcie |
|---|---:|---|
| **NIE JEST POMIAREM** | 43 | poza zjawiskiem; policzone, żeby 80 miało przedmiot |
| **NIEPRZELICZALNA** | 7 | **zapisana granica** — automat nie policzy, czyja ręka dopisała siedem miejsc, ile razy odpalono sondę ani ile prób odtworzenia zjawiska było |
| **PRZELICZALNA** | 30 | **bramka tam, gdzie liczba NAZYWA STAŁĄ; datowanie w reszcie** |

## 4. Luka w mechanizmie z 6.D108, zmierzona

Twierdzenia o nazwanej stałej pilnuje `test_report_claims.CLAIM` — ale **tylko
w kształcie `` `NAZWA` `` … liczba**, bo wzorzec zakazuje grawisa w przerwie do liczby.
Kształt, w którym **nazwa i liczba stoją w JEDNEJ parze grawisów**, jest dla niego
niewidzialny:

```
`ZDAN_RODZINY_RAZEM = 19`     <- CLAIM nie widzi
`ZDAN_RODZINY_RAZEM` = 19     <- CLAIM widzi
```

Zmierzone: kształt niewidziany pada w `docs/TASKS.md` **33 razy** (22 z nazwą, którą
drzewo zna) i w `reports/` **41 razy** (35 z nazwą znaną) — czyli cała populacja, której
tamta bramka nie ogląda **także w plikach, które skanuje**.

W polach „Skąd" pozycji **otwartych** stoją dokładnie **dwa** takie twierdzenia — i oba
były **rozjechane, oba moje, oba napisane tego samego dnia**:

```
ROZJAZD  6.D203: `ZDAN_RODZINY_RAZEM = 19` -> w drzewie 23
ROZJAZD  6.D203: `ZDAN_BEZ_POKRYCIA = 10`  -> w drzewie 8
```

## 5. Rozstrzygnięciem jest DATOWANIE i zostało wykonane

Pole „Poza zakresem" zabrania poprawiania liczb. Pole „Skończone, gdy" wymienia jako
rozstrzygnięcie **datowanie**, i ono tu pasuje, bo obie liczby opisują stan sprzed
6.D191 — prawdziwie i dla tej pozycji istotnie. Pole „Skąd" 6.D203 mówi dziś obie rzeczy:
liczby z dnia wpisania **i** dzisiejsze (23 i 8), oraz to, że zmieniło je 6.D191, które
weszło do `main` **tego samego dnia**, w którym tamta pozycja powstała.

**Sama pozycja 6.D203 przez to nie znika:** jej treścią jest **luka w bramce**
(`test_prose_counts.py` czyta cyfry, a tamte liczby stały słownie), a ta luka jest
nietknięta. Znika wyłącznie jej przykład.

**Warunek bramki jest ALTERNATYWĄ, nie zakazem:** twierdzenie wolno zostawić nieaktualne,
ale pole ma wtedy podać **dzisiejszą wartość obok**. Marker przeszłości tu nie wystarcza
i to jest zmierzone: `HISTORICAL_MARKERS` z `test_docs_ci_claims.py` zawiera „zmierzone",
a **tym słowem zaczyna się niemal każde pole „Skąd"** — warunek byłby spełniony zawsze,
czyli bramka nie pilnowałaby niczego.

## 6. Siedem kontroli negatywnych, baza 45/45

| kontrola | podstawienie | wynik |
|---|---|---|
| KN-1 | datowanie zdjęte (stan sprzed tej pozycji) | 44/45 |
| KN-2 | nowe rozjechane twierdzenie — **podstawienie NIE WESZŁO** | — |
| KN-2b | to samo, z poprawną kotwicą | 44/45 |
| KN-3 | czytnik ślepy na kształt `NAZWA = N` | **43/45** |
| KN-4 | skan wchodzi także na pozycje domknięte | 44/45 |
| KN-5 | pętla twierdzeń oślepiona | 44/45 |
| KN-6 | pole „Skąd" czytane do końca bloku | **45/45 ZIELONA** |
| KN-6b | to samo, po dołożeniu wejścia syntetycznego | 44/45 |

**KN-2 nie weszła, a moje sprawdzenie ją potwierdziło — i to jest osobne znalezisko.**
Podstawienie szukało kotwicy, której w pliku nie było, a `grep -q "MIN_REPORTS = 40"`
zwrócił prawdę, **bo ten napis już stał w drzewie**, w wierszu pozycji domkniętej.
Sprawdzenie podstawienia musi być specyficzne **dla podstawienia**, a nie dla napisu,
który przy okazji w nim występuje. Ten sam błąd popełniłem dziś przy 6.D191.

**KN-6 wyszła ZIELONA i wskazała mechanizm bezczynny.** Zawężenie pola „Skąd" do
najbliższego `- **` niczego dziś nie zmienia, bo żadna pozycja otwarta nie ma takiego
twierdzenia poza tym polem. Zawężenie jest **słuszne** — pozycja pyta o to pole i tylko
o nie — ale drzewo go **nie ćwiczy**, więc bez wejścia syntetycznego byłoby mechanizmem
bez kontroli (6.D159). Wejście dołożone, KN-6b czerwona.

## 7. Czego świadomie nie zrobiłem

- **Żadnej liczby w pozycjach nie poprawiłem** — pole „Poza zakresem" mówi wprost, że to
  jest praca po pomiarze. Datowanie dwóch liczb w 6.D203 nie jest poprawianiem: jest
  jednym z trzech rozstrzygnięć, których żąda pole „Skończone, gdy", i obie liczby
  zostają w polu **razem z dzisiejszymi**.
- **Rozmiarów `S`/`M` nie ruszałem** — to samo pole.
- **Bramki na liczby nieprzeliczalne nie dopisywałem** — to samo pole, i pomiar mówi,
  dlaczego: siedem z trzydziestu opisuje rzeczy, których automat nie policzy.
- **Mechanizmu z 6.D108 nie poszerzyłem na `reports/`**, choć zmierzyłem tam 41 trafień
  niewidzianego kształtu. Raporty są historią i mają własne datowanie po gicie; mieszanie
  dwóch mechanizmów w jednej pozycji byłoby jej poszerzeniem.

## 8. Zauważone po drodze, nie tknięte

- **6.D203 i 6.D207 były w całości nieaktualne w chwili powstania.** Obie opisują stan
  sprzed pozycji, które weszły do `main` **tego samego dnia** (6.D191, 6.D193). Kto
  wziąłby je z tabeli, zacząłby od pracy już zrobionej. Datowanie 6.D203 to naprawia;
  6.D207 („zero linii kodu pod zdaniem" wobec **20** dziś) zostaje, bo jego liczba nie
  nazywa stałej i bramka jej nie widzi — jest to przykład granicy z §3.
- **6.D168–6.D171 nie mają pól „Skąd" w ogóle.** `do_wziecia` liczy je do zapasu,
  `documented_items` ich nie widzi, a ich liczby (13 z 13 okien, 24/13/12 plików,
  21 z 275 raportów, 10.0.400 vs 10.0.401) są **poza każdym audytem, także tym**.
- **Trzynastka z 6.D168 się trzyma**, sprawdzone narzędziem: `data_freshness.py` daje
  dziś „przeterminowanych okien: 13", wszystkie z jedną datą `2026-08-28` i jednym
  pobraniem `2026-09-01`. To **jedna migawka STIB w trzynastu plikach**, a nie trzynaście
  niezależnych problemów — co zmienia kształt decyzji, o którą pytam właściciela.
  Ruchoma jest za to liczba dni: w polu stoi 15, dziś jest 16.
