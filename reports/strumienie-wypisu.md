# Strumienie wypisów runnera — pięć wierszy `[XXX]` przeniesionych na stdout

**Zmierzone 07.09.2026 na commicie:** `aa64156ce02d00c1396911623919bca6e088bfa8`

Pozycja 6.A30. Pole „Wyjście" tej pozycji żądało **najpierw dwóch pomiarów, potem
kierunku**, więc raport zaczyna się od pomiarów, a nie od opisu poprawki.

## 1. Co zrobiłem, w jednym zdaniu

Pięć wypisów informacyjnych `Sim.Runner` — `[RDZEŃ]` w `Drive` oraz `[LIMIT]`,
dwa `[ODTWORZENIE]` i `[ATP]` w `Replay` — idzie dziś na **stdout**, razem z całą
pozostałą rodziną `[XXX]`; na stderr zostały wyłącznie odmowy, a obu kierunków pilnuje
nowa bramka `tools/tests/test_runner_output_streams.py`.

## 2. Pomiar pierwszy: duplikat czy unikalny — **0 duplikatów, 5 unikalnych**

Pytanie pola „Wyjście": które z tych pięciu wierszy są duplikatem wiersza, który już
idzie na stdout (taki wolno usunąć), a które są unikalne (taki trzeba przenieść).

Metoda: cztery przebiegi runnera z rozdzielonymi strumieniami (`drive`, `replay`,
`replay --atp`, `line --signalling`), zebranie **wszystkich** wierszy stdout w jeden
zbiór i sprawdzenie każdego wiersza `[XXX]` ze stderr na przynależność do tego zbioru —
porównanie bajt w bajt, nie „podobnym kształtem".

```
wierszy na stdout ze WSZYSTKICH przebiegow: 33

wiersz [XXX] ze stderr                                 | identyczny wiersz jest na stdout?
drive       [RDZEŃ] package-a-first-run: kroków=38194 t=318.283 s chaina | UNIKALNY
replay      [LIMIT] tryb ręczny: 72.00 km/h z planu classic-2026-L1_A (d | UNIKALNY
replay      [ODTWORZENIE] tests/data/manual-keys.log: kroków=8880 t=74.0 | UNIKALNY
replay      [ODTWORZENIE] stacja Beekkant: postój od 41.475 s do 57.975  | UNIKALNY
replay-atp  [LIMIT] tryb ręczny: 72.00 km/h z planu classic-2026-L1_A (d | UNIKALNY
replay-atp  [ODTWORZENIE] tests/data/manual-overspeed.log: kroków=24000  | UNIKALNY
replay-atp  [ATP] ostrzeżeń=2118 ingerencji służbowych=0 awaryjnych=2118 | UNIKALNY
replay-atp  [ODTWORZENIE] stacja Beekkant: postój od 41.475 s do 57.975  | UNIKALNY

duplikatow: 0  unikalnych: 8
```

Osiem wierszy, bo pięć miejsc wypisu w kodzie daje osiem wierszy na trzech przebiegach
(`[LIMIT]` i `[ODTWORZENIE]` wychodzą i w `replay`, i w `replay --atp`). **Miejsc
wypisu jest pięć i wszystkie pięć są unikalne — żadnego nie wolno było skasować,
wszystkie pięć trzeba było przenieść.**

Najbliższym kandydatem na duplikat był `[ATP]`, bo ten znacznik naprawdę stał na obu
strumieniach jednego programu. Wiersze są jednak różne — inne pola i inna interpunkcja,
`line` na stdout wobec `replay --atp` na stderr:

```
[ATP] ostrzeżenia 0, ingerencje służbowe 0, awaryjne 0, największe żądanie 0.000 m/s² przy hamulcu służbowym 1.100 m/s²
[ATP] ostrzeżeń=2118 ingerencji służbowych=0 awaryjnych=2118 max żądanie=1.300 m/s² (hamulec służbowy 1.100 m/s²) tras zaryglowanych=5 odmów=0
```

## 3. Pomiar drugi: kto czyta te wiersze ZE STDERR — **1 miejsce, 0 kroków CI**

| gdzie | liczba | co dokładnie |
|---|---|---|
| testy C# (`result.StdErr`) | **1** | `tests/Sim.Tests/RunnerCommandTests.cs:77` — `StringAssert.Contains(result.StdErr, "[RDZEŃ]")` |
| kroki CI w `.github/workflows/` | **0** | — |

Polecenie z pola „Weryfikacja" pozycji, wykonane na drzewie **przed** zmianą:

```
$ grep -rn "StdErr" tests/Sim.Tests/ | grep -c "RDZEŃ\|ODTWORZENIE\|ATP\|LIMIT"
1
$ grep -rn "StdErr" tests/Sim.Tests/ | grep "RDZEŃ\|ODTWORZENIE\|ATP\|LIMIT"
tests/Sim.Tests/RunnerCommandTests.cs:77:        StringAssert.Contains(result.StdErr, "[RDZEŃ]");
```

**Zero po stronie CI nie jest domysłem, tylko wynikiem przejścia po wszystkich
wywołaniach runnera w `.github/workflows/`.** Każde z nich składa strumienie —
`2>&1 | tee <log>` albo `> <log> 2>&1` — i dopiero z tego złożonego logu wycina
wiersze `grep`-em. Trzy bramki, które te wiersze naprawdę czytają, i sposób złożenia
strumienia w każdej z nich:

| bramka w `.github/workflows/godot-first-run.yml` | wiersz | złożenie |
|---|---|---|
| „Manual run — the replayed input log must be the core's own drive" | 608 | `2>&1 \| tee build/t400/reczny/core.log` |
| „Manual mode — both sides must hold the same speed ceiling" | 742 | `2>&1 \| tee build/t400/limit/core.log` |
| „Cab protection — both sides must count ATP the same way" | 1010 | `2>&1 \| tee build/t400/atp-kabina/core.log` |

Log złożony z obu strumieni ma te wiersze przed zmianą i po zmianie, więc przeniesienie
nie zmienia wejścia ani jednej bramki CI. W `.github/workflows/sim-tests.yml` runner
woła się z `--trace` i `> /dev/null` albo z `braking > plik`, czyli po znaczniki ze
stderr nie sięga wcale.

**Wniosek z obu pomiarów: przeniesienie jest dobrym pomysłem.** Do poprawienia w tym
samym commicie było jedno miejsce, nie kilkanaście, a kierunek jest wskazany przez samą
przewagę: znaczników `[XXX]` wypisywanych z `Program.cs` jest **38** i przed zmianą
**33 stały na stdout**, a 5 na stderr.

## 4. Rzeczywiste wyjście weryfikacji

### 4.1 Pomiar strumieni przed i po — na tekście `src/Sim.Runner/Program.cs`

Czytnik zdejmuje komentarze (wzmianka w komentarzu nie jest wypisem) i skleja każdy
wypis przez wiersze do domknięcia nawiasów, bo marker stoi zwykle w drugim wierszu
`string.Create(Inv, $"…" + $"…")`.

```
PRZED: wypisow Console na stdout=52, na stderr=8; markerow [XXX] w wypisach stdout=33, stderr=5
PO:    wypisow Console na stdout=57, na stderr=3; markerow [XXX] w wypisach stdout=38, stderr=0
```

Trzy wypisy, które na stderr zostały, to dokładnie odmowy: `BŁĄD: ` z wspólnego
handlera, `nieznane polecenie:` i wiersz pomocy.

### 4.2 Pomiar strumieni przed i po — na WYKONANIU

```
=== ZNACZNIKI [XXX] PER STRUMIEN (PRZED) ===
--- drive: stdout ---
--- drive: stderr ---
      1 [RDZEŃ]
--- replay: stdout ---
--- replay: stderr ---
      1 [LIMIT]
      2 [ODTWORZENIE]
--- replay-atp: stdout ---
--- replay-atp: stderr ---
      1 [ATP]
      1 [LIMIT]
      2 [ODTWORZENIE]
--- line: stdout ---
      1 [ATP]
      2 [ENERGIA]
      3 [LINIA]
     11 [ODCINEK]
     11 [STACJA]
      1 [SYGNALIZACJA]
      4 [ZAŁOŻENIE]
--- line: stderr ---
0
```

```
=== ZNACZNIKI [XXX] PER STRUMIEN (PO) ===
--- drive: stdout ---
      1 [RDZEŃ]
--- drive: stderr --- (wierszy: 0)
--- replay: stdout ---
      1 [LIMIT]
      2 [ODTWORZENIE]
--- replay: stderr --- (wierszy: 0)
--- replay-atp: stdout ---
      1 [ATP]
      1 [LIMIT]
      2 [ODTWORZENIE]
--- replay-atp: stderr --- (wierszy: 0)
--- line: stdout ---
      1 [ATP]
      2 [ENERGIA]
      3 [LINIA]
     11 [ODCINEK]
     11 [STACJA]
      1 [SYGNALIZACJA]
      4 [ZAŁOŻENIE]
--- line: stderr --- (wierszy: 0)
```

To jest pomiar, którego żądało pole „Skończone, gdy": **żaden znacznik `[XXX]` nie
występuje dziś na obu strumieniach**, bo stderr nie ma ani jednego.

### 4.3 `2>/dev/null` nie traci ani jednego wiersza `[XXX]`

```
=== KONTROLA: przebieg z 2>/dev/null nie traci ani jednego wiersza [XXX] ===
-- replay --atp z 2>&1 (log zlozony, jak w CI):
4
-- to samo z 2>/dev/null:
4
-- drive z 2>/dev/null:
1
```

### 4.4 Telemetria jest bit w bit ta sama — zmienił się strumień, nie przejazd

```
=== KONTROLA: telemetria bit w bit ta sama przed i po ===
drive.csv: IDENTYCZNE co do bajtu
replay.csv: IDENTYCZNE co do bajtu
replay-atp.csv: IDENTYCZNE co do bajtu
```

### 4.5 Odmowy nadal na stderr — pole „Poza zakresem"

```
=== KONTROLA: odmowy NADAL na stderr (6.A16, 6.A27 — poza zakresem) ===
compare z jednym plikiem: kod 1
  stdout: []
  stderr: BŁĄD: compare wymaga dwóch plików
nieznane polecenie: kod 2
  stdout: []
  stderr (2 pierwsze wiersze):
    nieznane polecenie: nie-ma-takiego-polecenia
    MetroBxl.Sim.Runner — konsolowy gospodarz rdzenia symulacji
replay bez --signalling: kod 1
  stdout: []
  stderr: BŁĄD: replay wymaga --signalling PLIK.json: prędkość dopuszczalną tryb ręczny bierze z planu sygnalizacji, a scenariusz podaje 80 km/h — prędkość konstrukcyjną M7, nie ograniczenie na torze
```

### 4.6 Zestaw narzędzi i testy C#

```
$ python3 tools/tests/test_all.py
KOD WYJSCIA: 0
  1889/1889 przeszło
  RAZEM 71.678 s, 1889 testów, 100 modułów
```

```
$ dotnet test tests/Sim.Tests
Passed!  - Failed:     0, Passed:   589, Skipped:     0, Total:   589, Duration: 27 s - MetroBxl.Sim.Tests.dll (net10.0)
```

Zestaw narzędzi **1886 → 1889** testów i **99 → 100** modułów (nowa bramka ma trzy
testy). Testy C# **589 → 589**: asercja w istniejącej metodzie została przepisana
i wzmocniona drugą, nowej metody nie ma.

## 5. Kontrole negatywne — WYKONANE

### KN-1: każdy z pięciu wierszy cofnięty na stderr, po jednym

Pięć osobnych przebiegów całego zestawu, w każdym cofnięty JEDEN wypis:

```
######## KN-1.443: wiersz 443 ([RDZEŃ]) cofniety na stderr ########
  kod zestawu narzedzi: 1
    FAIL test_every_line_moved_by_6a30_is_on_stdout: wiersz przeniesiony przez 6.A30 zniknal ze stdout: [RDZEŃ] {scenario.Id}:
    FAIL test_no_information_line_of_the_runner_goes_to_stderr: wypisy z markerem `[XXX]` na stderr: wiersz 443 [RDZEŃ]. Znacznik, ktory raz idzie na stdout, a raz na stderr, psuje rozpoznanie jednym wzorcem `grep`, a `2>/dev/null` usuwa wtedy czesc WYNIKU, nie diagnostyki (6.A30). Na stderr naleza wylacznie odmowy.
    1887/1889 przeszło
######## KN-1.633: wiersz 633 ([LIMIT]) cofniety na stderr ########
  kod zestawu narzedzi: 1
    FAIL test_every_line_moved_by_6a30_is_on_stdout: wiersz przeniesiony przez 6.A30 zniknal ze stdout: [LIMIT] tryb ręczny:
    FAIL test_no_information_line_of_the_runner_goes_to_stderr: wypisy z markerem `[XXX]` na stderr: wiersz 633 [LIMIT]. …
    1887/1889 przeszło
######## KN-1.737: wiersz 737 ([ODTWORZENIE]-koniec) cofniety na stderr ########
  kod zestawu narzedzi: 1
    FAIL test_every_line_moved_by_6a30_is_on_stdout: wiersz przeniesiony przez 6.A30 zniknal ze stdout: [ODTWORZENIE] {keysPath}:
    FAIL test_no_information_line_of_the_runner_goes_to_stderr: wypisy z markerem `[XXX]` na stderr: wiersz 737 [ODTWORZENIE]. …
    1887/1889 przeszło
######## KN-1.755: wiersz 755 ([ATP]) cofniety na stderr ########
  kod zestawu narzedzi: 1
    FAIL test_every_line_moved_by_6a30_is_on_stdout: wiersz przeniesiony przez 6.A30 zniknal ze stdout: [ATP] ostrzeżeń=
    FAIL test_no_information_line_of_the_runner_goes_to_stderr: wypisy z markerem `[XXX]` na stderr: wiersz 755 [ATP]. …
    1887/1889 przeszło
######## KN-1.766: wiersz 766 ([ODTWORZENIE]-stacja) cofniety na stderr ########
  kod zestawu narzedzi: 1
    FAIL test_every_line_moved_by_6a30_is_on_stdout: wiersz przeniesiony przez 6.A30 zniknal ze stdout: [ODTWORZENIE] stacja {call.Name}:
    FAIL test_no_information_line_of_the_runner_goes_to_stderr: wypisy z markerem `[XXX]` na stderr: wiersz 766 [ODTWORZENIE]. …
    1887/1889 przeszło
```

Za każdym razem czerwienieje **dokładnie nowa bramka**, i to komunikatem, który nazywa
NUMER WIERSZA i ZNACZNIK, a nie samą liczbę wypisów. Reszta zestawu — 1887 z 1889 —
zostaje zielona.

Po stronie C# ta sama kontrola pokazuje, **dlaczego bramka po stronie Pythona była
konieczna**, a nie tylko ładna:

```
######## KN-1.443 po stronie C#: [RDZEŃ] cofniety na stderr ########
  rc=1
    Failed Drive_bez_argumentow_konczy_sie_kodem_zero [25 ms]
  Failed!  - Failed:     1, Passed:   588, Skipped:     0, Total:   589

######## KN-1.633 po stronie C#: [LIMIT] cofniety na stderr ########
  rc=0
  Passed!  - Failed:     0, Passed:   589, Skipped:     0, Total:   589
```

Cofnięcie `[RDZEŃ]` wywraca **dokładnie jeden** test C#. Cofnięcie `[LIMIT]` nie
wywraca **żadnego** — wszystkie 589 zielone. Cztery z pięciu tych wierszy nie ma po
stronie C# ani jednego strażnika i nie miałoby go dalej.

### KN-2: wiersz USUNIĘTY, a nie przeniesiony

```
######## KN-2: wiersz [ATP] USUNIETY, a nie przeniesiony (755-761) ########
  kod zestawu: 1
    FAIL test_every_line_moved_by_6a30_is_on_stdout: wiersz przeniesiony przez 6.A30 zniknal ze stdout: [ATP] ostrzeżeń=
    1888/1889 przeszło
```

Sam licznik „zero markerów na stderr" byłby po takim skasowaniu **zielony** — dlatego
bramka wymienia każdy z pięciu wierszy z nazwy. Pada tu jeden test i jest to inny test
niż w KN-1.

### KN-3: drugi kierunek — odmowa przeniesiona na stdout

```
######## KN-3: odmowa `BŁĄD: ` przeniesiona na stdout (drugi kierunek) ########
              Console.Out.WriteLine("BŁĄD: " + exception.Message);
  kod zestawu: 1
    FAIL test_refusals_still_go_to_stderr: odmowa zeszla ze stderr: "BŁĄD: "
    1888/1889 przeszło
```

Bez tej asercji „zero markerów na stderr" byłoby spełnione także przez plik, który
przeniósł na stdout RAZEM z nimi odmowy — a te na stderr należą i to rozstrzygnęły
6.A16 oraz 6.A27 (`reports/kody-wyjscia-runnera.md`, `reports/przedrostek-compare.md`).

### KN-4: przyrząd oślepiony

Czytnik wypisów w bramce wskazany na wzorzec, którego w pliku nie ma
(`Console\.NieMaTakiego`):

```
    FAIL test_every_line_moved_by_6a30_is_on_stdout: wiersz przeniesiony przez 6.A30 zniknal ze stdout: [RDZEŃ] {scenario.Id}:
    FAIL test_no_information_line_of_the_runner_goes_to_stderr: czytnik wypisow znalazl 0 markerow na stdout, a ma ich byc co najmniej 30 — przyrzad jest oslepiony i bramka orzekalaby o pustym zbiorze
    FAIL test_refusals_still_go_to_stderr: w `Program.cs` nie ma ani jednego wypisu na stderr — odmowy tez
    0/3 przeszło
```

Bramka, która nie widzi wypisów, meldowałaby „zero markerów na stderr" i byłaby zielona
na pustym zbiorze. Wszystkie trzy asercje to łapią.

### KN-5: bramka zapaliła się na moim własnym progu

To jest kontrola, której nie planowałem, i dlatego jest tu wypisana. Pierwsza wersja
bramki miała próg kontroli przyrządu ustawiony na **dokładną** liczbę z dnia pomiaru
(38 markerów na stdout). Przy KN-1 zapalała się wtedy **na progu**, zanim doszła do
asercji o strumieniu:

```
    FAIL test_no_information_line_of_the_runner_goes_to_stderr: czytnik wypisow znalazl 37 markerow na stdout, a ma ich byc co najmniej 38 — bramka orzekalaby o pustym zbiorze
```

Bramka mówiła więc „przyrząd nie widzi", kiedy prawdą było „wiersz idzie na zły
strumień" — komunikat o czym innym niż usterka. Próg jest **przepisany, nie dopisany
obok**: 30, czyli tyle, żeby odróżniać czytnik oślepiony od działającego, a nie żeby
liczyć wypisy. Liczbę wypisów pilnuje osobna asercja, po nazwie i po treści. Wyjście
wyżej (KN-1) jest już z wersji po tej poprawce.

## 6. Czego świadomie nie zrobiłem

- **Nie zmieniłem treści ani jednego wypisu i nie ruszyłem tego, które polecenia je
  produkują** — pole „Poza zakresem". Zmienił się wyłącznie strumień; §4.4 pokazuje
  telemetrię bit w bit tę samą.
- **Nie ruszyłem `BŁĄD: ` ani `nieznane polecenie:`** — pole „Poza zakresem"; one na
  stderr należą (6.A16, 6.A27). KN-3 pilnuje, żeby tam zostały.
- **Nie ruszyłem `src/Game/FirstRun.cs`.** Scena wypisuje `[ODTWORZENIE]`, `[LIMIT]`
  i `[ATP]` przez `GD.Print`, czyli na stdout, więc po tej zmianie obie strony
  porównania stoją na tym samym strumieniu i nie było czego poprawiać.
- **Nie uzupełniałem kolejki zadań** — nie mój zakres w tym zleceniu.
  `tools/tests/test_backlog.py` przeszedł, więc próg dwunastu pozycji nie jest naruszony.
- **Nie tknąłem `docs/TASKS.md` poza jednym wierszem tabeli fazy 6** — wiersz `6.A30`,
  zgodnie ze zleceniem.

## 7. Zauważone przy okazji, nie tknięte

**Liczby w bloku pozycji 6.A30 nie zgadzają się z przeliczeniem, i to nie zmienia
wniosku.** Blok mówi „wypisów `[XXX]` jest **52**: **47** na stdout i **5** na
stderr". Przeliczone dzisiaj na tym samym pliku: **5 na stderr zgadza się co do
sztuki i co do numeru wiersza**, ale po stronie stdout wychodzi **33** miejsca wypisu
z markerem (38 wystąpień markera w tych wypisach), a **52** to liczba WSZYSTKICH
wywołań `Console.*WriteLine` na stdout — z telemetrią, nagłówkami CSV i wierszami bez
markera. Kierunek poprawki był ten sam przy każdej z tych liczb, bo rozstrzygał go
stosunek 33 do 5, a nie 47 do 5. Nie poprawiam liczby w bloku: pomiar z bloku jest
zapisem datowanym, a nowy stoi w tabeli fazy 6 razem z wpisem „ZROBIONE".

**Pole „Weryfikacja" pozycji cytuje ścieżkę, której w drzewie nie ma.** Polecenie
z bloku brzmi

```
dotnet run --project src/Sim.Runner -c Release -- replay --keys data/keys/L1_A-manual.json 2>/dev/null
```

a katalogu `data/keys` nie ma wcale; zapisy wejść leżą w `tests/data/` jako
`manual-keys.log`, `manual-keys-limit.log`, `manual-keys-reset.log`
i `manual-overspeed.log`. Weryfikację wykonałem na istniejących plikach i tak też
podaję ją w §4. Ścieżki w bloku nie poprawiam — to nie ten wiersz zlecenia, a bramka
`tools/tests/test_report_hygiene.py` pilnuje ścieżek w `reports/`, nie w `docs/TASKS.md`.

**`replay` i `drive` bez `--out` piszą telemetrię na stdout i teraz mieszają się z nią
wiersze `[XXX]`.** Przed zmianą wiersz podsumowania szedł na stderr, więc
`Sim.Runner drive > core.csv` dawał czysty CSV. Po zmianie na końcu takiego pliku
stanie jeszcze jeden wiersz. Zmierzone: **ani jedno wywołanie w repozytorium nie
korzysta z tej drogi** — wszystkie kroki CI podają `--out`, a `compare` czyta pliki,
nie strumień; testy C# `Run("drive")` i `Run("replay")` czytają stdout jako tekst, nie
jako CSV. Rozwiązaniem, którego świadomie **nie** wprowadziłem, byłby strumień
zależny od obecności `--out` — to znaczy dokładnie ten sam „raz tu, raz tam", który ta
pozycja likwiduje. Gdyby czysty CSV na stdout miał być kontraktem, właściwą postacią
jest osobna decyzja właściciela: albo `--out -`, albo wymóg `--out`, i to jest pozycja
z pomiarem, nie poprawka przy okazji.
