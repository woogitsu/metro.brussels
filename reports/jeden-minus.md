# Człon z jednym minusem przechodził obok odmowy (6.A15)

**Zmierzone 07.09.2026 na commicie:** `681a4ce28d0f38ef7219d1d6cc81e02e462ead9d`
(gałąź `claude/6a15-jeden-minus`).

**Adnotacja z tego samego dnia:** gałąź została po pomiarze przestawiona na
`7dbea51` (scalenie #345 — dwie pozycje kolejki, `docs/TASKS.md` i zapadka bloków).
Oba zestawy przebiegły na nowej podstawie ponownie i dały **ten sam werdykt oraz te
same liczby testów** (1828 w narzędziach, 557 w C#); zmienił się wyłącznie czas
ścienny zestawu narzędzi, 68,176 s → **70,192 s**. Liczby z pomiaru nie są
przeliczane — ta adnotacja mówi, co powtórzono i z jakim wynikiem.

## 1. Stan wyjściowy

6.A11 (#307) dopisała odmowę nieznanej opcji i **sama wypisała tę dziurę** jako
nietkniętą. Zmierzone ponownie dziś:

```
-zmyslona 7                      kod=0  (cisza)
--zmyslona 7                     kod=1  BŁĄD: polecenie line nie zna opcji --zmyslona. Zna: …
```

Człon z jednym minusem kończył się **kodem 0**, dokładnie tak jak przed 6.A11 —
a więc dokładnie tak, jak `--coast-from-m X` przed 6.A11, na czym 6.D15 złapało
weryfikację spełniającą się przez niezrobienie zadania.

## 2. Czy rozszerzenie jest bezpieczne — ZMIERZONE, nie założone

Pole „Wyjście" tej pozycji żądało wprost pomiaru, a nie założenia: odmowa rozszerzona
na jeden minus mogłaby zjeść **wartość ujemną** albo **argument pozycyjny**. Trzy
pomiary, wszystkie na dzisiejszym drzewie:

```
$ # czlony z JEDNYM minusem w komendach Sim.Runner w repozytorium
     55  -c
      1  ->
```

`-c` występuje 55 razy i **ani razu nie dochodzi do programu**: stoi **przed**
separatorem `--`, czyli jest flagą `dotnet run`:

```
Sim.Runner -c Release --no-build -- \
Sim.Runner -c Release --no-build -- parity
```

`->` to strzałka w prozie. Dalej:

```
$ # wartosci ujemne w komendach
(pusto)
$ # argumenty pozycyjne w Program.cs
619:        var left = File.ReadAllLines(args[1]);
620:        var right = File.ReadAllLines(args[2]);
```

**Ani jednej wartości ujemnej** w całym repozytorium, a jedyne argumenty pozycyjne to
dwie **ścieżki** polecenia `compare` — które nie zaczynają się od minusa. Rozszerzenie
jest więc bezpieczne, i to jest wniosek z trzech pomiarów, nie z przekonania.

## 3. Co zrobione, i dlaczego goły minus jest wyjątkiem

Warunek zmienił się z `StartsWith("--")` na `StartsWith("-")`, z jednym wyjątkiem:
**goły minus** (`-`) przechodzi. To konwencja „standardowe wejście"; to repozytorium
jej nie używa, ale odmawianie jej byłoby odmową czegoś, co **nie jest pomyłką** —
a odmowa ma łapać pomyłki.

Wartość ujemna nadal przechodzi, bo człon po znanej opcji z wartością jest pomijany
razem z nią (`i++`). Sprawdzone wykonaniem:

```
$ line … --stop-window-m -5
BŁĄD: Okno stacji musi być skończone i dodatnie. (Parameter 'stopWindowM')
```

To jest **właściwa** odmowa — z walidacji dziedzinowej `LineRunSettings`, nie
z nieznanej opcji. Odmowa, która zjadłaby `-5` i zameldowała „nie znam opcji -5",
byłaby najgorszym możliwym wynikiem tej pozycji: zamianą jednej cichej dziury na
komunikat mówiący nieprawdę.

Sprawdzone też, że nic innego się nie zmieniło:

```
compare build/t1.csv build/t2.csv    kod=0   (dwie sciezki pozycyjne)
budget … --atp                       kod=0   (flaga nie zjada nastepnego czlonu)
line … (bez dodatkow)                kod=0
```

## 4. Bramka z 6.A11 wymagała przepisania, nie usunięcia

`test_runner_options.py` przybijał **literalnie** `StartsWith("--"` — bo taki był
warunek, gdy 6.A11 go pisała. Po tej zmianie asercja przestała opisywać kod.

Test jest **przepisany, a nie skasowany**, bo jego **intencja jest nadal aktualna**:
ścieżki polecenia `compare` nie zaczynają się od minusa, więc nadal przechodzą
nietknięte. Nowa wersja żąda warunku na jednym minusie **i** wyjątku dla gołego minusa,
czyli pilnuje obu rzeczy, które 6.A15 rozstrzygnęła.

**Przy pisaniu tej poprawki popełniłem czwarty raz dzisiaj ten sam błąd składniowy:**
polski cudzysłów otwierający `„` w napisie w podwójnych cudzysłowach zamyka napis
przedwcześnie. Zestaw pokazał to jako `FAIL <import>test_runner_options: SyntaxError`
— widoczne wyłącznie dzięki 6.D19, która sprawiła, że błąd importu ma wiersz `FAIL`,
a nie samą ciszę i kod wyjścia.

## 5. Kontrole negatywne — WYKONANE, trzy, każda topi swój test

```
KN-1  powrot do dwoch minusow (dziura z 6.A11 wraca)
      Failed Line_z_jednym_minusem_konczy_sie_kodem_jeden
      Failed!  - Failed: 1, Passed: 556, Total: 557

KN-2  goly minus przestaje byc wyjatkiem
      Failed Goly_minus_nie_jest_zglaszany_jako_nieznana_opcja
      Failed!  - Failed: 1, Passed: 556, Total: 557

KN-3  pomijanie wartosci po znanej opcji zdjete
      Failed Wartosc_ujemna_znanej_opcji_nie_jest_brana_za_opcje
      Failed!  - Failed: 1, Passed: 556, Total: 557
```

Każda mutacja wywraca **dokładnie jeden** test i **za każdym razem inny** — czyli trzy
testy mierzą trzy różne rzeczy, a nie jedną trzy razy. Liczba 557 nie spada w żadnej
z nich, co po nauczce z 6.B27 jest częścią kontroli.

## 6. Weryfikacja

```
$ dotnet test tests/Sim.Tests
Passed!  - Failed: 0, Passed: 557, Skipped: 0, Total: 557

$ python3 tools/tests/test_all.py
  RAZEM 68.176 s, 1828 testów, 97 modułów
kod: 0
```

557 = 554 + **3**.

## 7. Czego świadomie nie zrobiono

- **Form krótkich** (`-o` jako skrót `--out`) — pole „Poza zakresem". To nowa funkcja,
  nie domknięcie odmowy.
- **Nie tknięto postaci `--opcja=wartość`.** `--limit-kmh=72` nadal odmawia komunikatem
  o nieznanej opcji, co jest **mylące**, bo `--limit-kmh` runner zna. Wyszło to z tego
  samego sondowania co ta pozycja i stoi w kolejce jako **6.A22** — osobno, bo to
  poprawka komunikatu albo nowa postać argumentu, a nie domknięcie tej samej dziury.
- **Nie tknięto powtórzonej opcji.** `--limit-kmh 72 --limit-kmh 50` jedzie 72 i milczy;
  to **6.A23**, z tego samego pomiaru.
- **Nie zmieniono komunikatu odmowy.** Mówi „nie zna opcji -zmyslona", i to jest
  prawda — w odróżnieniu od przypadku z 6.A22.
