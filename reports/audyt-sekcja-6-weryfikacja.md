# Osiemnaście propozycji audytu wobec drzewa: dwie nowe, czternaście pokrytych, dwie odrzucone

**Zmierzone 09.09.2026 na:** `b53b806`, kontener tej sesji.
**Przyrząd:** sekcja 6.2 audytu zewnętrznego (`AUDYT-01` … `AUDYT-18`, plik wgrany
przez właściciela), `docs/TASKS.md` (`open_items`, `queue_row` z
`tools/tests/test_backlog.py`), drzewo repozytorium, `python3 tools/tests/test_all.py`.

---

## 1. Po co ten raport

Właściciel polecił: **zweryfikować każdą propozycję w drzewie i wpisać do kolejki
TYLKO potwierdzone pomiarem, a odrzucone wymienić z powodem.** Sam audyt stawia ten
sam warunek w sekcji 7: „Nowe propozycje są oddzielnymi zadaniami audytowymi; przed
włączeniem trzeba usunąć ewentualne duplikaty z dalszej części kolejki" — i wprost
mówi, że nie przeczytał całej kolejki.

Findingi `F-001` … `F-024` z sekcji 3 są już przerobione na wiersze `6.D65` … `6.D91`.
Propozycje z sekcji 6.2 stoją **na tych samych findingach**, więc pierwszym pytaniem
przy każdej nie jest „czy słuszna", tylko „czy w kolejce już nie stoi".

## 2. Werdykty, jeden wiersz na propozycję

| propozycja | werdykt | podstawa w drzewie |
|---|---|---|
| AUDYT-01 · domknięty werdykt importu | **ZROBIONE** | `6.D65`, scalone dziś (#434); bramka żyje w `tools/tests/test_assertion_gate.py` |
| AUDYT-02 · asercje odporne na `-O` | **POKRYTE** przez `6.D71` (otwarte) | wiersz opisuje `compile(...)` bez `optimize`; zmierzone dziś ponownie: `python3 -O` gubi `assert False`, a ani `.github/`, ani `tools/`, ani `doctor.sh` nie wołają interpretera z `-O` |
| AUDYT-03 · liczbowa granica zaufania osi | **ZROBIONE** w części, reszta bez podstawy | `6.D66` (#437) wprowadziło odmowę przed rachunkiem; `validate.py` ma dziś `math.isfinite` z komunikatem nazywającym pole |
| AUDYT-04 · działająca identyfikacja pakietu | **POKRYTE** przez `6.D69` (otwarte) | `--package` istnieje z domyślnym `A`; wiersz kolejki nazywa dokładnie to samo |
| AUDYT-05 · bezpieczne usuwanie gałęzi | **POKRYTE** przez `6.D67` (otwarte) | ten sam workflow i ten sam `$sha` z planu |
| AUDYT-06 · zimny bootstrap Godota | **POKRYTE** przez `6.D68` + `6.D77` + `6.D88` (wszystkie otwarte) | suma kontrolna, `unzip` przed sondą, sonda na obecność zamiast wersji — trzy wiersze na sześć przypadków z propozycji |
| AUDYT-07 · odtwarzalny SDK i mapa akcji | **POKRYTE** przez `6.D79` + `6.D78` (otwarte) | zmierzone: `dotnet-version: '10.0.x'` w trzech workflowach |
| AUDYT-08 · jeden kontrakt obiegu | **POKRYTE** przez `6.D70` (otwarte) | `Finished` przy przyjeździe wobec dokumentacji nawrotu |
| AUDYT-09 · spójna lista współdzielonych stacji | **ZROBIONE** w części, **reszta NOWA** → `6.D92` | Madou dopisane dziś (#440) razem z bramką liczników i zgodności z GTFS; ale **kontroli wspólnej sekwencji L2/L6 nie ma** — sprawdzone w `test_network_declarations.py` i `test_packages.py` |
| AUDYT-10 · manifest praw egzekwuje typy | **POKRYTE** przez `6.D85` (otwarte) | ten sam test i ta sama luka |
| AUDYT-11 · status niwelety nie awansuje | **POKRYTE** przez `6.D80` (otwarte) | `IsVerticalModelled`, cztery drogi awansu |
| AUDYT-12 · hermetyczne testy bramki | **POŁOWA ZROBIONA**, połowa pokryta | F-017 domknięte przez `6.D76` (#436, bramka czyta AST); F-016 stoi jako `6.D84` |
| AUDYT-13 · teksty HUD poza prezentacją | **POKRYTE** przez `6.D83` (otwarte) | literały w `Hud.cs` |
| AUDYT-14 · HUD w kontrolowanych rozmiarach | **POKRYTE** przez `6.D82` (otwarte) | odsunięcie 900 px |
| AUDYT-15 · niezależny dowód orientacji | **ZROBIONE** | `6.D75` (#435): osobna klatka `_normals`, fixture 0,00000 wobec 0,99661 |
| AUDYT-16 · spójny opis stanu i doctor | **POKRYTE** przez `6.D81` + `6.D87` + `6.D89` + `6.D86` (otwarte) | cztery wiersze na pięć rozbieżności z propozycji; piąta (`§9` i etykiety runnera) jest **nieaktualna** — `CLAUDE.md` §9 opisuje dziś gołe `self-hosted`, zgodnie z drzewem |
| AUDYT-17 · raport gotowości pakietu | **ODRZUCONE** (z powodem, §4) | — |
| AUDYT-18 · rozdzielony raport czasów | **POŁOWA BEZ PODSTAWY**, reszta **NOWA** → `6.D93` | wyrocznia mutacyjna już dziś czyta wyłącznie `N/M przeszło` i kod wyjścia, więc czas na jej werdykt nie wpływa; artefaktu trendu natomiast **nie ma** — `python-tests.yml` nie ma ani jednego `upload-artifact` |

Podsumowanie liczbowe: **cztery** propozycje mają przedmiot już domknięty, **dziesięć**
stoi w kolejce pod innym numerem, **dwie** są częściowo domknięte i częściowo nowe,
**dwie** są odrzucone. Do kolejki wchodzą **dwie** nowe pozycje.

## 3. Dwie pozycje, które wchodzą — i pomiar, na którym stoją

### 6.D92 — wspólna sekwencja L2 i L6 nie jest przez nic porównywana

Zmierzone dziś przy dopisywaniu Madou: po dopisaniu wspólny odcinek zgadza się co do
pozycji, a **żaden test tego nie sprawdza**.

```
L2 odwrócone: 19 | L6[7:]: 19
pozycji: 19 | różnic: 0
```

Bramka postawiona dziś w `test_network_declarations.py` pilnuje liczników, powtórek,
zgodności `docs/00` i przypisania przystanku do linii wedle GTFS — ale nie porównuje
**dwóch linii ze sobą**. Usunięcie Madou z samej L6 razem z obniżeniem licznika
przechodzi więc dziś wszystkie cztery.

### 6.D93 — czas per moduł jest wypisywany i wyrzucany

`test_all.py:533` wypisuje „czas per moduł (malejąco)", a `python-tests.yml` nie ma
ani jednego kroku `upload-artifact`. Trend czasu istnieje więc wyłącznie w logach
pojedynczych przebiegów i w ręcznie utrzymywanej liście `POMIARY`.

Część propozycji AUDYT-18 o wyroczni mutacyjnej **nie ma dziś podstawy** i jest w tym
wierszu wypisana jako niepotrzebna: `mutation_sweep.run_suite` czyta z procesu zestawu
wyłącznie linię `N/M przeszło` i kod wyjścia, co jest zapisane w komentarzu kroku CI
od 6.D11. Dodanie opóźnienia nie może zmienić werdyktu mutanta, bo werdykt nie zależy
od czasu.

## 4. Dwie odrzucone, z powodem

**AUDYT-17 (raport gotowości lokalnego pakietu demonstracyjnego) — odrzucone.**
Nie dlatego, że propozycja jest zła, tylko dlatego, że wpis kolejki ma być pracą **do
wzięcia**, a ta nią dziś nie jest: propozycja sama deklaruje `Zależy od: AUDYT-04,
AUDYT-09, AUDYT-10, AUDYT-11`, czyli od **trzech wierszy, które są w kolejce otwarte**
(`6.D69`, `6.D85`, `6.D80`) i jednego domkniętego dziś. Nakład z propozycji to
`1–2 dni`, podczas gdy wiersze tej kolejki mają rozmiary `S` i `M`. Wpis powstanie,
gdy trzy pozycje, na których stoi, będą zamknięte — i wtedy jego „Skończone, gdy"
da się napisać liczbą, a nie zapowiedzią.

**Część AUDYT-03 o dwudziestu negatywach — odrzucone jako sformułowanie.**
Propozycja żąda „co najmniej 20 negatywów (5 klas wartości × 4 rodziny pól)". Liczba
20 jest iloczynem wymyślonym w propozycji, nie pomiarem czegokolwiek w tym drzewie:
`validate.py` odrzuca dziś wartości nieskończone i nieliczbowe **jednym** strażnikiem
z komunikatem nazywającym pole (`6.D66`), a `test_validate_axis.py` ma 42 testy.
Dopisanie dwudziestu przypadków po to, żeby zgadzała się liczba z cudzej propozycji,
byłoby pracą dla licznika, nie dla bramki. Gdyby pomiar pokazał **klasę wartości**,
która przechodzi — to jest pozycja; dziś takiej klasy nie znalazłem.

## 5. Czego w tej weryfikacji NIE zmierzyłem

**Nie sprawdziłem klatki `_normals` na tunelu z otwartymi końcami** (AUDYT-15 żąda,
by otwarte końce nie dawały fałszywego alarmu). Blender jest w tym kontenerze od
dzisiaj, więc pomiar jest wykonalny, ale nie należy do tej pozycji i **nie twierdzę,
że fałszywego alarmu nie ma** — twierdzę, że go nie mierzyłem.

**Nie weryfikowałem findingów F-001 … F-024 po raz drugi.** Poprzednia sesja
przerobiła je na wiersze `6.D65` … `6.D91`; ta weryfikacja dotyczy wyłącznie sekcji 6.2.

**Nie zmieniałem ani jednego wiersza `6.D65` … `6.D91`.** Tam, gdzie propozycja audytu
jest szersza od istniejącego wiersza (AUDYT-02 wobec `6.D71`, AUDYT-06 wobec trzech
wierszy), różnica jest opisana w tabeli §2, a nie dopisana do cudzego wpisu.
