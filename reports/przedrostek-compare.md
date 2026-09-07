# Kształt wyjścia każdej odmowy `compare` (6.A27)

**Zmierzone 07.09.2026 na commicie:** `becc2742eb65bc7ced1de865fd448b814c192fcf`
(baza gałęzi `claude/6a27-przedrostek-compare`, czyli `main` po scaleniu #366).

## 1. Pozycja mówiła o dwóch odmowach. Jest ich cztery.

Wpis nazwał `różna liczba wierszy` i `nagłówki telemetrii nie zgadzają się z formatem
rdzenia`, a trzecią (`zła liczba kolumn`) wyłączył **warunkowo**: *„jeżeli pomiar pokaże,
że ona już przedrostek ma — wtedy pozycja dotyczy dwóch"*. Pomiar w ciele `Compare`:

```
Console.Error.WriteLine: 4
return 1;               : 4
```

Cztery, nie dwie:

| odmowa | stan przed |
|---|---|
| `różna liczba wierszy: N vs M` | `Console.Error` + `return 1` |
| `nagłówki telemetrii nie zgadzają się z formatem rdzenia` | `Console.Error` + `return 1` |
| `wiersz {i}: zła liczba kolumn` | `Console.Error` + `return 1` |
| `wiersz {i}: różna faza scenariusza (a vs b)` | `Console.Error` + `return 1` |

Warunek z pola „Poza zakresem" **nie zaszedł** — trzecia przedrostka nie miała — a o
czwartej wpis nie wiedział wcale. Pozycja objęła więc cztery.

## 2. Pomiar, o który prosiło pole „Wyjście": kto dopasowuje te komunikaty

Pole żądało sprawdzenia, czy któryś skrypt CI albo bramka nie dopasowuje dziś tych
komunikatów **bez** przedrostka — bo wtedy zmiana kształtu wywróciłaby przebieg, który
dziś działa. Przed zmianą:

```
tools:    0
.github:  0
docs:     5      ← wiersz i blok pozycji 6.A27 w docs/TASKS.md
reports:  4      ← proza reports/wartosc-nieliczbowa.md i reports/komorka-csv.md
src:      6      ← same odmowy w Program.cs
tests:    0
```

**Zero w `tools/` i zero w `.github/`.** Żadna bramka i żaden krok CI nie opierał się na
treści tych komunikatów, więc zmiana kształtu nie mogła niczego wywrócić — i to jest
liczba, którą pole „Skończone, gdy" kazało podać *„nawet jeśli wynosi zero"*.

Po zmianie `tools/` ma **5** dopasowań: to `ODMOWY_COMPARE` w bramce, którą ta pozycja
dopisała. Każde z nich przybija jedną z czterech treści — bo sam licznik
`Console.Error == 0` przechodziłby także wtedy, gdyby ktoś odmowę **usunął**, a odmowa
usunięta jest gorsza od odmowy bez przedrostka.

## 3. Wykonane próby wszystkich czterech dróg

```
$ compare d1.csv krotszy.csv
BŁĄD: różna liczba wierszy: 7641 vs 7638
kod=1

$ compare zlynag.csv zlynag.csv
BŁĄD: nagłówki telemetrii nie zgadzają się z formatem rdzenia
kod=1

$ compare malokol.csv d1.csv
BŁĄD: wiersz 5: zła liczba kolumn
kod=1

$ compare innafaza.csv d1.csv
BŁĄD: wiersz 5: różna faza scenariusza (INNA-FAZA vs traction)
kod=1

$ compare d1.csv d2.csv
[PORÓWNANIE] brake        max |Δ| = 0.000E+000 (wiersz 0) ok
[PORÓWNANIE] próg = 1.000E-009
kod=0
```

Kod wyjścia był dobry już przed zmianą — ujednoliciła go 6.A16. Zmienił się kształt:
przedrostek `BŁĄD: ` dodaje wspólny handler w `Main`, a te cztery odmowy go omijały.
Treści **nie zmieniono**, to pole „Poza zakresem".

## 4. Bramka, która meldowała zgodę zamiast pomiaru

`test_compare_refuses_through_the_common_handler` z 6.A16 żądał, żeby w ciele `Compare`
stały słowa `throw new ArgumentException`. Sprawdzone na drzewie **przed** tą pozycją:

```
--- STARA asercja z 6.A16, na drzewie PRZED 6.A27 ---
  'compare wymaga dwóch plików' in body        : True
  'throw new ArgumentException' in body        : True
  'return 2;' not in body                      : True
  => stara bramka: ZIELONA

--- a tymczasem w tym samym ciele ---
  Console.Error.WriteLine: 4
  return 1;               : 4
```

**Zdanie „choć jedna odmowa idzie handlerem" było prawdziwe i dlatego nic nie mierzyło.**
Cztery odmowy siedziały obok niego i wychodziły bez przedrostka. To ten sam gatunek
usterki, co 6.D30 (dwa martwe pola zgadzają się zawsze) i 6.B28 (dwa czytniki z jednym
błędem) — instrument raportujący zgodność zamiast pomiaru.

Asercja jest **przepisana, nie dopisana obok**: postać liczącą to zero `Console.Error`
i zero `return 1;` w ciele `Compare`, przy zachowanym końcowym werdykcie
`return failed ? 1 : 0;`, który odmową nie jest. Czytnik zdejmuje komentarze, bo akapity
wyjaśniające, **dlaczego** odmowa nie używa `Console.Error`, same te napisy zawierają —
a bramka zapalająca się na tekście, który ją wyjaśnia, zostaje wyłączona, nie naprawiona
(6.D27, 6.D30).

## 5. Kontrole negatywne — WYKONANE

**KN-1 — jedna odmowa cofnięta** do `Console.Error` + `return 1`:

```
FAIL test_compare_refuses_through_the_common_handler: 1 odmow w `compare` pisze na
     stderr wprost i omija wspolny handler, wiec wychodzi BEZ przedrostka `BŁĄD: `
FAIL test_every_compare_refusal_is_thrown_and_none_is_written_to_stderr: odmowa
     `nagłówki telemetrii nie zgadzają się z formatem rdzenia` nie jest rzucana wyjatkiem
2/4 przeszło

  Failed Zly_naglowek_telemetrii_ma_przedrostek_bledu
Failed!  - Failed: 1, Passed: 582, Total: 583
```

Bramka podaje **liczbę** (1), nie sam fakt, i nazywa **którą** odmowę. Po stronie C#
wywrócony dokładnie jeden test — ten, który tę drogę mierzy.

**KN-2 — stan przed 6.A27 w całości**, przeciwko starej asercji: wynik w §4. Stara
bramka **zielona** przy czterech odmowach omijających handler. Tego nie da się pokazać
inaczej niż wykonaniem, bo obie wersje asercji czytają ten sam plik i różnią się
wyłącznie tym, czy liczą.

## 6. Weryfikacja

```
$ dotnet test tests/Sim.Tests
Passed!  - Failed: 0, Passed: 589, Skipped: 0, Total: 589      (584 → 589)

$ python3 tools/tests/test_all.py test_runner_exit_codes.py
  4/4 przeszło                                                 (3 → 4)

$ python3 tools/tests/test_all.py
  1872/1872 przeszło
  RAZEM 77.052 s, 1872 testów, 99 modułów
kod: 0
```

Liczba **584 → 589**, nie 578 → 583: pierwszy pomiar zrobiłem na drzewie sprzed
scalenia #366 (6.A25, +6 testów C#), a ta gałąź stoi już na `main` z tamtą pozycją.
Podana jest liczba z drzewa, które idzie do scalenia; różnica ma nazwane źródło,
a nie jest wyrównana po cichu.

## 6a. Bramka 6.D28 zapaliła się na moich własnych testach

Pierwsza wersja czterech testów delegowała **wszystkie** asercje do pomocnika
`OdmowaMaWspolnyKsztalt`, więc dwa z nich miały ciała bez ani jednej asercji:

```
FAIL test_every_csharp_test_method_has_an_assertion_in_its_body: metoda testowa C#
     bez ani jednej asercji w tresci:
     RunnerCommandTests.Rozna_liczba_wierszy_ma_przedrostek_bledu;
     RunnerCommandTests.Zly_naglowek_telemetrii_ma_przedrostek_bledu
7/8 przeszło
```

Dwa pozostałe przeszły, bo miały w ciele dodatkowe `StringAssert.Contains`. Bramka
ma rację: test bez asercji w ciele przechodzi także wtedy, gdy pomocnik przestanie
cokolwiek sprawdzać. Poprawione podziałem, który **nie jest estetyczny**: pomocnik
sprawdza wyłącznie to, co wspólne (kod 1 i przedrostek na początku), a treść każdej
z czterech odmów asercjonuje jej własny test, w swoim ciele. To jest rzecz warta
zapisania osobno — w sesji, w której trzy razy trafiłem na instrument meldujący
zgodę zamiast pomiaru, obca bramka złapała ten sam wzorzec u mnie.

## 7. Czego świadomie nie zrobiono

- **Nie zmieniono treści ani kodów wyjścia** — pole „Poza zakresem"; 6.A16 rozstrzygnęła
  kody, a treści są cytowane w prozie dwóch raportów i w bloku pozycji.
- **Nie tknięto `Cell`** — odmowa zepsutej komórki z 6.A24 przedrostek ma, bo od początku
  rzuca wyjątek.
- **Nie ujednolicono kształtu poza `compare`.** Pomiar dotyczył jednej metody; audyt
  wszystkich `Console.Error` w `Program.cs` to inna pozycja niż naprawa czterech odmów,
  które ta wskazuje z nazwy.

## 8. Zauważone przy okazji, nie tknięte

**Wzorzec `„choć jedno wystąpienie istnieje"` jest w tym repozytorium powtarzalnym
kształtem usterki, nie przypadkiem.** Dziś trafiłem na niego trzeci raz w jednej sesji:
tutaj (`throw` istnieje, cztery `Console.Error` obok), w 6.A25 (test spełniony przez
komunikat o czymś innym — wpisane jako 6.A29) i w 6.A26 (reguła pierwszeństwa sceny
pilnowana wyłącznie komentarzem). Wspólna cecha: asercja na **obecność** czegoś dobrego
zamiast na **brak** czegoś złego. Nie dopisuję z tego zadania — pozycja wymyślona na
miejscu omija format z sekcji 6 `CLAUDE.md` — ale zapisuję, bo audyt asercji
`in body` / `Contains` w całym zestawie byłby zadaniem z pomiarem, nie z pomysłu.
