# Nagłówek §1.3 liczył tryby ręcznie — trzy liczby, policzone osobno, zgodne

**Zmierzone 06.09.2026 na commicie:** `74f5b4a`

**Rodzaj pracy:** naprawa jednego zdania plus bramka. Zmienione pliki:
`reports/droga-do-grywalnosci.md` (§1.3) i nowy `tools/tests/test_run_mode_claims.py`.
Ani jeden plik w `src/` nie został zmieniony.

## 1. Skąd usterka

Nagłówek `### 1.3` raportu `reports/droga-do-grywalnosci.md` mówił „Cztery tryby".
Liczba stała tam od pierwszej wersji sekcji i nigdy nie była wynikiem pomiaru —
6.C3 dopisał do tabeli szósty wiersz (`from-telemetry`) i **świadomie zostawił
nagłówek**, mówiąc wprost w przypisie pod tabelą, że liczba w nim nie jest jego
pomiarem. To ta sama rodzina usterki, którą już łapią `test_report_claims.py`
i `test_readme_claims.py`: liczba stojąca w jednym miejscu i nigdzie nie liczona
rozjeżdża się bezszelestnie, jeden wiersz na raz.

## 2. Pomiar — trzy liczby, trzy niezależne drogi

| skąd | jak policzone | wynik |
|---|---|---|
| kod | liczba odrębnych literałów w łańcuchu ternary właściwości `RunPlan.Mode` (`src/Game/RunPlan.cs`) | **[Z KODU]** |
| nagłówek | liczebnik słowny w `### 1.3` sekcji „droga do grywalności" | **[Z RAPORTU, przed poprawką]** cztery |
| tabela | liczba wierszy z nazwą trybu w grawisach pod tym nagłówkiem | **[Z RAPORTU]** |

`RunPlan.Mode` rozstrzyga tryb jednym łańcuchem `warunek ? "literał" : …`, gałąź po
gałęzi: `from-telemetry`, `replay`, `telemetry`, `shot`, `line`, `manual` — sześć
odrębnych literałów, żaden się nie powtarza. Tabela pod nagłówkiem ma dziś sześć
wierszy i ich nazwy w pierwszej kolumnie to **dokładnie ten sam zbiór sześciu
napisów**, ani jednego więcej, ani jednego mniej. Nagłówek przed poprawką podawał
cztery.

Dwie z trzech liczb (kod, tabela) już się zgadzały — rozjechał się wyłącznie
nagłówek, i to jest dokładnie to, co przewidywał przypis 6.C3.

## 3. Decyzja: poprawiony nagłówek, nie zdjęta liczba — i dlaczego

Pole „Skończone, gdy" tej pozycji dopuszcza dwa warianty i każe uzasadnić wybór
pomiarem, z przywołanym precedensem `CLAUDE.md` §2 (zdjęcie liczby testów narzędzi
z dokumentu, bo zaszywanie jej generowało rozjazd przy każdym nowym module).

Różnica między tamtym przypadkiem a tym jest w tym, **co chroni liczbę po naprawie**.
`CLAUDE.md` §2 nie miał żadnego automatycznego strażnika liczby testów narzędzi —
jedynym lekarstwem było przestać ją wpisywać. Tu istnieje jeden, dokładnie
identyfikowalny punkt prawdy w kodzie (`RunPlan.Mode` — jedyne miejsce, które w ogóle
nazywa tryb przebiegu), a nazwy w tabeli i liczba w nagłówku dają się z niego
wyprowadzić mechanicznie i porównać. To jest dokładnie sytuacja, w której pole
„Wyjście" każe dopisać bramkę zamiast zdejmować liczbę: **dała się policzyć z kodu**.

Wybrany wariant: nagłówek poprawiony na liczbę zgodną z kodem i tabelą, plus
`tools/tests/test_run_mode_claims.py`, który odtąd liczy wszystkie trzy przy każdym
przebiegu `tools/tests/test_all.py` i pada, gdy któraś się rozjedzie — w dowolną
stronę, także wtedy, gdy `RunPlan.Mode` dostanie kiedyś siódmą gałąź, a nikt nie
zaktualizuje ani tabeli, ani nagłówka.

## 4. Kontrola negatywna — wykonana, nie opisana

Dwie mutacje, każda uruchomiona i przywrócona osobno, na kopii roboczej tego
worktree:

```
$ sed -i 's/### 1.3 Sześć trybów,/### 1.3 Cztery tryby,/' reports/droga-do-grywalnosci.md
$ python3 -c "...test_code_header_and_table_agree_on_the_number_of_run_modes()..."
FAIL (oczekiwane): nagłówek §1.3 mówi 4 trybów, RunPlan.Mode zwraca 6, tabela §1.3 ma 6 wierszy — powinny być równe
```

```
$ sed -i 's/: LineMode ? "line" : "manual";/: LineMode ? "line" : ShotPath is null \&\& false ? "ghost" : "manual";/' src/Game/RunPlan.cs
$ python3 -c "...test_code_header_and_table_agree_on_the_number_of_run_modes()..."
FAIL (oczekiwane): tabela §1.3 wymienia [...bez ghost...], RunPlan.Mode zwraca [...z ghost...] — brakuje jej ['ghost']
```

Obie mutacje przywrócone (`diff` przed/po pusty), `python3 tools/tests/test_all.py`
zielone na drzewie bez mutacji: **1718/1718 przeszło**, `grep -cE '^\s*FAIL'` na tym
wyjściu daje **0**. `dotnet test tests/Game.Tests` (RunPlan.cs nietknięte przez to
zadanie poza kontrolą negatywną, przywrócone bajt w bajt): **205/205 przeszło**.

## 5. Czego ta pozycja nie robi

Nie dopisuje żadnego nowego trybu jazdy i nie zmienia zachowania `RunPlan.cs` —
to poza zakresem tej pozycji kolejki. Nie rusza żadnego innego wiersza
`docs/TASKS.md` ani żadnej innej liczby w `reports/droga-do-grywalnosci.md` poza
nagłówkiem §1.3 i przypisem pod tabelą, który go komentował.
