# Wzmianka nie jest odczytem (6.B34)

**Zmierzone 07.09.2026 na commicie:** `fdd5a9ba817ffc6bde3e14cd3242116b4767aba2`
(gałąź `claude/6b34-maska-martwych-stalych`).

**Adnotacja z tego samego dnia:** gałąź została po pomiarze przestawiona na `c1f5618`
(scalenia #354 — 6.A23 — i #355 — 6.B33). Zestaw przebiegł na nowej podstawie ponownie
i dał ten sam werdykt oraz tę samą deltę trzech testów: **1852 → 1855**, kod wyjścia 0.
Liczby z dnia pomiaru (1844 → 1847) nie są przeliczane.

## 1. Co było zepsute

`_odczyty` liczyło wystąpienia identyfikatora w **surowym** tekście, więc wzmianka
o stałej w komentarzu albo w literale napisowym liczyła się jako jej odczyt. Zmierzone
na wstrzykniętym wejściu, dwiema próbami:

```
stala wymieniona TYLKO w napisie      -> _odczyty daje 1  (wyglada na ZYWA)
stala wymieniona TYLKO w komentarzu   -> _odczyty daje 1  (wyglada na ZYWA)
```

Szczególnie kłopotliwy jest przypadek drugi: **komentarz wyjaśniający usunięcie**
stałej utrzymuje ją w stanie „żywa" na zawsze. Ten projekt takie komentarze pisze
regularnie — reguły i zdania się tu przepisuje, nie dopisuje obok — więc mechanizm nie
był teoretyczny.

## 2. To nie było przeoczenie 6.B31, tylko jej świadomy wybór — który się przeżył

Raport `reports/martwe-stale-csharp.md` mówi to wprost: kierunek pomyłki był wybrany
**świadomie**, bo fałszywy negatyw (martwa stała uznana za żywą) jest tańszą pomyłką
niż bramka zapalająca się na poprawnym kodzie, a odróżnienie wywołania od wzmianki
wymagało wtedy własnego rozbioru literałów.

**Od 6.B28 (#348) `maska()` już istnieje** — kopia źródła z komentarzami i literałami
zamienionymi na spacje znak w znak — więc koszt zniknął, a wraz z nim jedyny powód,
dla którego fałszywy negatyw miał zostać. To trzecie miejsce, w którym ta jedna funkcja
załatwia zupełnie inny problem: przejście po ciele klasy (6.B28), odróżnienie wywołania
od wzmianki dla `Assert.Fail` (6.B33) i tutaj.

## 3. Zmierzony skutek na drzewie: ZERO

```
deklaracji:          233   (roznych nazw: 193)
martwych PRZED maska:  0   []
martwych PO masce:     0   []
nazwy, ktore zmienily status:  []
```

Ani jedna stała w tym repozytorium nie jest dziś utrzymywana przy życiu samą wzmianką.
**Wartość tej poprawki jest więc wyłącznie zapobiegawcza** i dowodzi jej kontrola
dodatnia na wstrzykniętym wejściu, nie zmiana liczby — co jest tu powiedziane wprost,
żeby nikt nie czytał „zero martwych" jako zasługi tej pozycji.

## 4. Koszt, bo przy tej bramce koszt już raz był problemem

Pierwsza wersja bramki z 6.B31 kosztowała **20,7 s** i została przepisana na jedno
przejście z licznikiem (0,42 s w kontekście pełnego zestawu). Maska dokłada jedno
przejście po tych samych plikach, więc zmierzone zostało osobno — trzy przebiegi
każdego wariantu, na 124 plikach `.cs` i 1 615 998 znakach:

```
sam licznik odczytow, bez maski:   0.118, 0.121, 0.118 s
licznik odczytow z maska:          0.559, 0.573, 0.565 s
```

Czyli **+0,45 s** na przejście. Moduł w pełnym zestawie: **1,406 s**. Na zestawie
o czasie ~72 s to 0,6 % — mieści się bez dyskusji, ale liczba stoi tu, a nie w domysle,
bo przy tej konkretnej bramce raz już nie mieściła.

## 5. Kontrole negatywne — WYKONANE, dwie, po jednej na każdy kierunek

```
KN-1  maska zdjeta (powrot do surowego tekstu)
      FAIL test_a_mention_in_a_comment_is_not_a_read: stala wymieniona WYLACZNIE
           w komentarzu uznana za czytana: {}
      FAIL test_a_mention_in_a_string_is_not_a_read: stala wymieniona WYLACZNIE
           w napisie uznana za czytana: {}
      6/8 przeszlo

KN-2  maska ZBYT SZEROKA (cale zrodlo zamienione na spacje)
      FAIL test_a_real_read_still_counts: prawdziwy odczyt nie policzony — maska
           zdejmuje wiecej niz komentarze i literaly: {'ZmyslonaStala': [...]}
      FAIL test_every_unread_csharp_constant_is_justified: stala C#, ktorej nic
           w src/ ani tests/ nie czyta, bez wpisu w UZASADNIONE: Accel80Aw0DistanceM
           (tests/Sim.Tests/PythonReference.cs); … (dziesiatki nazw)
      6/8 przeszlo
```

**KN-2 jest tu równie ważny jak KN-1** i dlatego stoi obok niego: bez
`test_a_real_read_still_counts` trzy pozostałe testy byłyby zielone również dla maski
zdejmującej **za dużo** — a taka bramka zgłasza jako martwe stałe, które są czytane,
i zostaje wyłączona w pierwszym tygodniu. Drugi FAIL w KN-2 pokazuje rozmiar tej
pomyłki liczbą: nie jedna nazwa, a dziesiątki.

## 6. Weryfikacja

```
$ python3 tools/tests/test_dead_constants_csharp.py
  ok   test_a_declaration_line_is_not_counted_as_a_read
  ok   test_a_mention_in_a_comment_is_not_a_read
  ok   test_a_mention_in_a_string_is_not_a_read
  ok   test_a_real_read_still_counts
  ok   test_every_unread_csharp_constant_is_justified
  ok   test_no_justification_outlives_the_constant_it_describes
  ok   test_the_gate_sees_the_declarations_it_is_supposed_to_see
  ok   test_the_pattern_reads_the_shapes_this_repository_actually_uses
  8/8 przeszło

$ python3 tools/tests/test_all.py
  RAZEM 74.012 s, 1847 testów, 98 modułów
kod: 0
```

1847 = 1844 + **3** (trzy nowe testy w istniejącym module, bez nowego modułu).
Lista `UZASADNIONE` zostaje **pusta** — po masce nadal nie ma czego usprawiedliwiać.

## 7. Czego świadomie nie zrobiono

- **Nie tknięto odczytów poza C#** (`.tscn`, `.gd`, `*.sh`, `.github/`) — pole „Poza
  zakresem". 6.B31 zmierzyło tam **zero** odczytów i warunek zostaje, ale maska jest
  pisana dla składni C#: w skrypcie powłoki `#` jest komentarzem, którego nie zna,
  a nazwa w napisie shellowym może być prawdziwym użyciem. Maska tam byłaby zmianą
  znaczenia, nie poprawką.
- **Nie zmieniono `deklaracje()`** — deklaracja jest kodem, więc maska nic by tam nie
  wniosła, a jedno przejście mniej to 0,45 s mniej.
- **Nie ruszono `MINIMUM_DEKLARACJI`** — liczba deklaracji się nie zmieniła (233).

## 8. Co zauważone przy okazji, nietknięte

- **`_odczyty` bierze na wejściu słownik `{plik: treść}`, więc maskowanie da się wsunąć
  bez dotykania jego wnętrza** — i to jest zasługa kształtu, który 6.B31 wybrała
  z powodów wydajnościowych. Wtedy chodziło o 20,7 s; dziś ten sam kształt pozwolił
  zmienić znaczenie wejścia w jednym wierszu.
