# Droga do grywalności — M1 i M2

**Ten dokument jest planem produktu, nie opisem stanu.** Powstał z audytu zewnętrznego
z 13.09.2026, wykonanego na snapshocie `main` o SHA
`c2a5f9d76a9b4bc401b6ec08eeabf18c21fdbb97`. Wprowadzony do repozytorium pozycją MB-00.

**Czym ten dokument NIE jest.** Nie jest playtestem: audyt wykonano czytając kod i CI,
bez uruchomienia Godota, Blendera i .NET, i mówi o tym wprost. Nie jest też zbiorem
faktów o STIB — reguły treningu z sekcji 4 są **decyzjami projektowymi tego planu**
i mają być tak zapisywane, gdy wejdą do kodu.

**Zastąpił on `reports/droga-do-grywalnosci.md` jako plan.** Tamten raport zostaje
historią (raporty są historią — 6.D108) i **czyta się dziś myląco**: jego §1.2 podaje
`DriverInput.Poll` i zdanie „pomoc o sterowaniu: stała istnieje i nie jest wołana przez
nic", a oba są nieaktualne od #239 i #249. G-1…G-5 z tamtego raportu **nie są dzisiaj
kolejką do wykonania** — G-5 jest zamknięte bramką „Cab under signalling — the scene and
the core must protect identically".

**Twierdzenia audytu o kodzie zostały SPRAWDZONE wobec dzisiejszego drzewa, a nie
przyjęte na słowo** — sekcja 8 tego dokumentu wypisuje, co się potwierdziło, a co nie.

---

## 1. Wniosek

**Najkrótsza droga to domknięcie istniejącego ręcznego przejazdu: prosty start, dwa
postoje, czytelne prowadzenie, wynik i ponowna próba.** Rdzeń fizyki i duża część
integracji już istnieją. Nie zaczyna się od przepisywania symulacji, pełnej sieci ani
dalszego rozbudowywania aparatu audytowego.

Zielony workflow **nie dowodzi**, że nowy gracz potrafi zacząć i skończyć przejazd.

## 2. Dwa kamienie milowe

| | co to jest | kryterium |
|---|---|---|
| **M1** | grywalny trening jednym M7 | zamknięta, powtarzalna sesja: start → dwa postoje → wynik → ponów |
| **M2** | autonomiczna linia z przejęciem sterowania | kilka składów, wspólna sygnalizacja, ręczne drzwi, take/release |

**M1 jest etapem pośrednim i NIE zamyka Issue #26.** Pełne kryteria #26 ocenia się
dopiero przy M2. Zasada projektu zostaje: **linia działa bez gracza, kabina jest jej
widokiem** — gracz obserwuje ruch, wybiera skład, przejmuje go bez teleportacji,
obsługuje postoje i oddaje sterowanie AI.

## 3. Kontrakt M1 — „Pierwsze dwa postoje"

**Wszystko w tej sekcji to DECYZJE PROJEKTOWE, nie odczytane fakty.**

- Jeden M7, istniejąca oś `L1_A`, istniejący ręczny punkt startu — zachowany, a nie
  zastąpiony dowolnym spawnem.
- Dwa cele: **Beekkant**, potem **Étangs Noirs / Zwarte Vijvers**. Cele wyszukiwane
  **po identyfikatorach z osi**; kilometraży nie kopiuje się do logiki.
- ATP włączone, istniejący `classic-2026` z jawnym statusem założeń. Limit modelowy
  **nie jest** podawany jako potwierdzona prędkość eksploatacyjna STIB.
- Drzwi automatyczne według istniejącego cyklu. Gracz prowadzi i hamuje; HUD wyjaśnia
  blokadę odjazdu.
- Czas treningu **do pomiaru w playteście**. Fizyki nie zmienia się, żeby zmieścić się
  w arbitralnym czasie.

**Warunek zakończenia.** Udana sesja kończy się po obsłudze drugiego celu, gdy drzwi są
zamknięte i skład stoi. Porażka: minięcie wymaganego celu według **istniejącej** reguły
`StationService`. Samo ostrzeżenie ATP **nie kończy** sesji. Zakazane: teleportowanie na
peron, automatyczne „trafienie" w cel, nieskończone oczekiwanie po ostatniej stacji.
Warunek końca ma być **domenowy i odtwarzalny z logu wejść**.

**Wynik M1 to fakty, nie punkty:** ukończono/pominięto cel, obsłużone stacje 0–2, błąd
zatrzymania na każdej, czas w czasie symulacji, informacja o interwencji ochrony.
Bez punktacji, gwiazdek i kar. Liczniki ATP liczą **kroki interwencji**, nie incydenty —
nie wyświetla się ich jako „liczby wykroczeń" bez ustalenia semantyki.

**Odbiór M1 — siedem punktów:**
1. Gracz uruchamia właściwy tryb **bez wpisywania argumentów**.
2. Widzi, jak ruszyć i gdzie zatrzymać pociąg.
3. Ręcznie wykonuje oba postoje; przy otwartych drzwiach nie odjeżdża.
4. Widzi wynik **bez zamykania aplikacji**.
5. „Ponów" daje świeżą sesję, także po porażce.
6. Replay tego samego wejścia daje **ten sam wynik i stan po tej samej liczbie ticków**.
7. Start bez potrzebnego zasobu daje **zrozumiały błąd**, nie pustą scenę.

## 4. Kolejność prac

| # | zadanie | widoczny rezultat | zależy od |
|---|---|---|---|
| 0 | **MB-00** ustalenie aktywnej kolejki i baseline | wiadomo, co kończyć i kiedy przestać | — |
| 1 | **MB-01** jeden start treningu | można od razu prowadzić właściwy tryb | MB-00 |
| 2 | **MB-02** sesja, koniec, wynik i ponów | istnieje kompletna pętla gry | MB-01 |
| 3 | **MB-03** HUD treningowy | gracz rozumie, co ma zrobić | MB-02 |
| 4 | **MB-04** paczka i playtest | M1 bez środowiska developerskiego | MB-03 |
| 5 | **MB-05** integracja kanonicznej kabiny | wrażenie siedzenia w pojeździe | MB-03 |
| 6 | **MB-06** wspólne źródło komend AI/gracza | bezpieczne przejęcie składu w rdzeniu | M1 |
| 7 | **MB-07** wiele widoków i take/release | działająca linia widoczna w grze | MB-06 |
| 8 | **MB-08** ręczna obsługa drzwi i odbiór #26 | flow stop–drzwi–odjazd | MB-07 |

**M1 blokują MB-00–04.** Kabina (MB-05) jest wartościowa, ale **nie opóźnia** pierwszego
testu kompletnej pętli. Największe ryzyko logiczne: **MB-02 i MB-06**.

Terminów ten dokument nie podaje i podawać nie będzie: brakuje pomiaru eksportu,
ręcznego playtestu i kosztu integracji `LineDrive`.

## 5. Zmiana polityki kolejki — i dlaczego jest jawna

Reguła zapasu z `CLAUDE.md` §8 („poniżej dwunastu pozycji DO WZIĘCIA — pierwszym
zadaniem jest uzupełnienie kolejki") jest **realnie egzekwowana** przez
`tools/tests/test_backlog.py` i działa. Jej skutkiem ubocznym jest jednak to, że każde
poboczne znalezisko natychmiast staje się pracą — a wtedy praca nigdy nie dochodzi do
kamienia milowego.

**Zmiana:** przy **aktywnym kamieniu milowym** priorytet mają pozycje odblokowujące jego
odbiór. Poboczne znaleziska zapisuje się **krótko** i nie generują one automatycznie
pracy przed ukończeniem M1. Próg zapasu zostaje — zmienia się **kolejność brania**,
a nie obowiązek uzupełniania.

Reguła i jej test zmieniają się **razem, w jednym commicie**, i jest to jawna część
MB-00, a nie ukryte obejście bramki. Bramek się nie omija i nie wyłącza.

## 6. Co odłożone do czasu M1/M2

Pełne cztery linie i łączenie pakietów · produkcyjny profil pionowy · finalny wystrój
stacji, schody i antresole niewidoczne z kabiny · pasażerowie 3D, ekonomia, kariera,
multiplayer · pełne audio STIB i branded art · nowe perturbacje ruchu i rozbudowany
dyspozytor · generalny refaktor `FirstRun` · audyty bez związku z blokadą bieżącego
kamienia milowego.

**Brak pełnych rzędnych nie blokuje istniejącego technicznego przejazdu jednym
pakietem.** Wariant `partial-vertical` jest osobną, zaakceptowaną drogą; nie miesza się
nowej geometrii pionowej z płaską fizyką bez zgodnego profilu i weryfikacji.
`data/` nie zmienia się bez jawnego zakresu zadania.

## 7. Weryfikacja każdej zmiany na tej ścieżce

1. **Test domenowy na realne zachowanie**, które da się zepsuć: końcowy postój, minięcie
   celu, reset, blokada drzwi, przejęcie.
2. Istniejące wymagane zestawy i CI gałęzi. **Progów telemetrii nie obniża się**, żeby
   ukryć regresję.
3. Dla UI i świata: **rzeczywisty obraz z renderera i oględziny**. Tryb `--shot` jest
   techniczny i nie zastępuje widoku z interaktywnego treningu.
4. Krótki zapis: co gracz może teraz zrobić, wykonane polecenia i wyniki, czego nie
   sprawdzono, następny numer MB.

**Nie buduje się osobnego systemu mierzącego liczbę zdań, raportów albo asercji w tym
planie.** Nowy test broni konkretnego zachowania gry albo procesu dostarczenia.

## 8. Co z audytu sprawdzone, a co PADŁO

Snapshot audytu (`c2a5f9d`) jest od dzisiejszego `main` starszy o **jeden commit
i dziewiętnaście minut**, a ten commit nie rusza ani jednego pliku w `src/`, `data/`,
`.github/` ani `tools/blender/`. Osiem twierdzeń o stanie kodu sprawdzono po kolei
i **wszystkie osiem jest aktualne**:

| twierdzenie audytu | wynik | dowód |
|---|---|---|
| brak końca ręcznego przejazdu | **aktualne** | `FirstRun.cs:988-1060`; `_done = true` tylko w czterech `Finish*`, żaden nie dotyczy trybu ręcznego |
| `_done` odcina `R`/`Esc` | **aktualne** | `FirstRun.cs:1010` `if (_done) return;` stoi PRZED odczytem klawiatury w `:1015-1030` |
| kabina niewpięta | **aktualne** | `grep m7_cab` w `src/Game/**` — zero trafień |
| jeden `TrainView` | **aktualne** | `FirstRun.tscn:32`, `FirstRun.cs:362`; scena bierze `_lineCore.Trains[0]` (`:1117`, `:1690`) |
| `placeholders.json` to metadane | **aktualne** | `data/audio/` = dwa pliki, oba `.json`, zero nagrań; zero `AudioStream` w `src/` |
| ścieżki poza `res://` | **aktualne** | `FirstRun.cs:477-481` `RepoPath` = `res://` + `../../` |
| reguła zapasu egzekwowana | **aktualne** | `test_backlog.py:70`, `:694-698`, `:914` |
| HUD diagnostyczny | **patrz niżej — PADŁO CO DO TREŚCI** |

**PADŁO: „HUD nie mówi graczowi, co ma zrobić".** Audyt opisuje HUD jako „tekstowy
diagnostyczny i pomoc klawiszowa" i buduje na tym MB-03. Pomiar mówi co innego:
**wiersz `Position` już dziś niesie nazwę następnej stacji i odległość do niej**
(`UiText.cs:74` — `„chainage {0} m / {1} m     {2} za {3} m"`), a **wiersz `Station`
niesie odległość do punktu zatrzymania razem z oknem ± i komunikatem
`„  W OKNIE — zatrzymaj się"`** (`UiText.cs:90-91`, składany w `FirstRun.StationLine()`,
`:1721-1793`). Do tego fazę drzwi, resztę postoju, błąd zatrzymania i licznik
obsłużonych oraz miniętych stacji.

**Co to zmienia dla MB-03:** zadaniem nie jest **dodanie** celu i odległości, bo są.
Zadaniem jest **priorytet informacji** — co widać na pierwszy rzut oka, co dopiero po
zatrzymaniu i co trafia do osobnej diagnostyki. Wpis MB-03 jest z tego powodu przepisany
wobec brzmienia audytu, a nie powtórzony.

**Drugie ustalenie, którego audyt nie miał:** `export_presets.cfg` nie tylko nie istnieje
— jest **jawnie w `.gitignore:31`**, w sekcji „wszystko, co silnik generuje obok
projektu". MB-04 musi więc zmienić także `.gitignore`, a nie tylko dołożyć plik.
