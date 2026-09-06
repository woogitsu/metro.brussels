# Ujednolicenie kodów wyjścia `Sim.Runner` (6.A16)

**Zmierzone 06.09.2026 na commicie:** `b45be99c072d87882ecf84f52129f891f324b1ee`

## 1. Decyzja i jej zakres

Właściciel wybrał 06.09.2026: **każda odmowa argumentowa kończy się kodem 1**, a **2**
zostaje wyłącznie dla „nie wiem, co uruchomić". Wariant rozdzielający znaczenia
(„1 = zła wartość, 2 = zły kształt wywołania") był osobną opcją i **nie został wybrany**,
więc trzecia wartość kodu wyjścia pozostaje poza zakresem.

Cztery pozycje zatrzymały się wcześniej dokładnie na tej granicy i przybiły stan testem,
zamiast go poprawić: 6.A10 (#302), 6.A11 (#307), 6.A13 (#313), 6.D20 (#312).

## 2. Co się zmieniło — jedno miejsce

`compare` było jedynym poleceniem sprawdzającym liczbę argumentów **ręcznie**
(`args.Length < 3`) i wracającym kodem 2. Teraz rzuca `ArgumentException`, więc idzie
tą samą drogą co wszystkie pozostałe odmowy.

Wyjątek, a nie `return 1`, i to jest istotne: dzięki temu komunikat dostaje ten sam
przedrostek `BŁĄD: `, co reszta. Ujednolica się nie tylko liczba, ale i kształt wyjścia.

```
$ dotnet run --project src/Sim.Runner -c Release -- compare
BŁĄD: compare wymaga dwóch plików
kod: 1

$ dotnet run --project src/Sim.Runner -c Release -- nie-ma-takiego
nieznane polecenie: nie-ma-takiego
kod: 2

$ dotnet run --project src/Sim.Runner -c Release
MetroBxl.Sim.Runner — konsolowy gospodarz rdzenia symulacji
kod: 2
```

Grep po `return 2;` w `src/Sim.Runner/Program.cs` daje dziś **dwa** wystąpienia —
gałąź pustych argumentów i `Unknown()`. Oba znaczą „nie wiem, co uruchomić".

## 3. Bramka, żeby to się nie rozjechało

`tools/tests/test_runner_exit_codes.py` czyta `Program.cs` jako tekst i pilnuje, że
`return 2` nie pojawi się w trzecim miejscu. Powód jest praktyczny: **trzecie miejsce
nie złamie żadnego istniejącego testu**, dopóki ktoś nie napisze mu własnego.
Ujednolicenie, którego nikt nie pilnuje, rozjeżdża się przy pierwszym nowym poleceniu.

Bramka sprawdza też drugi kierunek — że obie dozwolone ścieżki nadal **istnieją**.
Gdyby ktoś zamienił na 1 również je, pierwszy warunek przeszedłby na pustym zbiorze.

## 4. Kontrole negatywne — wykonane

```
KN-1  przywrócony kod 2 w compare
      FAIL test_both_allowed_paths_are_still_there: sciezek z kodem 2 jest 3, a powody sa dwa
      FAIL test_compare_refuses_through_the_common_handler: compare nadal odmawia
           z pominieciem wspolnego handlera
      FAIL test_exit_code_two_only_means_we_do_not_know_what_to_run
      Failed Compare_bez_dwoch_plikow_konczy_sie_kodem_jeden  (545/546)

KN-2  trzecie miejsce z kodem 2 — nowa, zmyślona odmowa argumentowa
      FAIL test_both_allowed_paths_are_still_there
      FAIL test_exit_code_two_only_means_we_do_not_know_what_to_run
```

KN-2 jest tu ważniejsza: dopisana metoda **nie miała żadnego testu C#**, więc bez bramki
czytającej źródło przeszłaby niezauważona.

## 5. Znalezisko z tej pozycji: test, który przestał być testem

Przy KN-1 zestaw C# przeszedł **545/545 mimo obecnego błędu**. Przyczyna nie była
w `compare`, tylko w moim własnym commicie: przepisując komentarz nad testem, wyciąłem
razem z nim atrybut `[TestMethod]`. Metoda została w pliku, wyglądała jak test, miała
asercje — i **nie była uruchamiana**.

Objawem nie był żaden `FAIL`. Objawem była liczba: **545 zamiast 546**, i to, że
mutacja, która miała wywrócić test, niczego nie wywróciła. Gdybym poprzestał na
„zestaw zielony", ta pozycja weszłaby z testem-atrapą.

```
przed naprawą, z mutacją:  Passed!  Failed: 0, Passed: 545, Total: 545
po naprawie,   z mutacją:  Failed!  Failed: 1, Passed: 545, Total: 546
po naprawie,   bez mutacji: Passed!  Failed: 0, Passed: 546, Total: 546
```

Zestaw narzędzi Pythona ma na to bramkę od #139 — `assertion_gate` liczy asercje
i nie pozwala testowi „przejść" bez ani jednej. Po stronie C# nic takiego nie ma:
test bez `[TestMethod]` jest **niewidzialny**, a jedynym śladem jest liczba testów,
której nikt nie pilnuje. Dopisane do kolejki jako **6.B27**; ta pozycja tego nie robi.

## 6. Weryfikacja

```
python3 tools/tests/test_all.py   ->  1768/1768 przeszło, kod wyjścia 0
dotnet test tests/Sim.Tests       ->  Passed! Failed: 0, Passed: 546, Total: 546
```

## 7. Poza zakresem

Trzecia wartość kodu wyjścia. Zmiana kodów wyjścia po stronie sceny (`src/Game`) —
`RunPlan` ma własną rodzinę odmów z kodem 9 i decyzja jej nie dotyczyła.
