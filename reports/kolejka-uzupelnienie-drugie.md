# Drugie uzupełnienie kolejki 07.09.2026 — pięć pozycji z pomiaru, nie z pomysłu

**Zmierzone 07.09.2026 na commicie:** `a4a3975f7b08dfddf8c5ae2a8eccb371abccada5`
**Dotyczy:** `docs/TASKS.md`, `tools/tests/test_backlog.py`
**Po co:** zapas policzony na stan **po** scaleniach, nie przed — bo licznik zapasu
opada od wykonywania pracy.

## 1. Dlaczego teraz, a nie po zapaleniu bramki

Po scaleniu #375 (6.A32) i #377 (6.A31) kolejka miała **14 pozycji do wzięcia**.
Dwa zadania są w robocie u agentów (6.A30 — PR #378, i 6.B41), a ich scalenie zbije
zapas do **dwunastu, czyli równo do progu** `MINIMUM_READY_ITEMS`. Następne domknięcie
po nich zapaliłoby `test_the_queue_holds_at_least_a_day_of_work` — i to na czerwonym
zestawie w cudzym pull requeście, czyli w miejscu, gdzie naprawa jest najdroższa.

`docs/TASKS.md` mówi o tym wprost i z tego samego powodu: zapas liczy się **na stan po**.
`CLAUDE.md` §8 dodaje drugą połowę: „Gdy kolejka zejdzie poniżej dwunastu pozycji,
pierwszym zadaniem jest jej uzupełnienie".

```
przed tym commitem:        14 pozycji do wzięcia, 101 bloków
po tym commicie:           19 pozycji do wzięcia, 106 bloków
po scaleniu #378 i 6.B41:  17 pozycji do wzięcia
```

## 2. Skąd wzięło się pięć pozycji

Żadna nie jest wymyślona na miejscu — zadania wymyślonego, bo skończyła się kolejka,
nie bierze się nigdy (`CLAUDE.md` §8). Każda ma źródło i liczbę:

| pozycja | skąd | liczba |
|---|---|---|
| **6.A33** | `reports/audyt-asercji.md` §7 nazwał ten pomiar **rozstrzygającym** i świadomie go nie wykonał | **16 z 68** igieł niejednoznacznych; najgorsza `line` w **11** komunikatach |
| **6.D32** | dwie ścieżki, których nie ma w drzewie — jedna z mojego pomiaru, druga znaleziona **niezależnie** przez agenta 6.A30 | **387 / 40 / 149** ścieżek w trzech polach, **2** usterki, **4** poprawne wyjątki |
| **6.D33** | 6.D15 nie zostawiło bramki, więc pokrycie audytu opada samo | audyt objął **82** komendy z **42** bloków; dziś jest **279** komend w **101** blokach, czyli **29 %** |
| **6.D34** | `reports/audyt-asercji.md` §7: „o tamtych 53 asercjach ten raport nie mówi nic" | **63** asercje kształtu `Contains` w **7** plikach `Game.Tests` |
| **6.D35** | to samo zdanie §7 nazywa `InputLogTests.cs` testem Godota | plik leży w `tests/Sim.Tests/`, `namespace MetroBxl.Sim.Tests`, **0** odwołań do Godota w pliku projektu |

## 3. Pomiar 6.A33 — swoistość igły

```
komunikatow wielowyrazowych w Program.cs: 209
igiel roznych w RunnerCommandTests.cs:     68   niejednoznacznych: 16
   11 komunikatow zawiera: 'line'
   10 komunikatow zawiera: 'budget'
    9 komunikatow zawiera: '--limit-kmh'
    8 komunikatow zawiera: 'step'
    6 komunikatow zawiera: '[BUDŻET]'
    6 komunikatow zawiera: '[LINIA]'
```

To jest dokładnie ta własność, którą 6.A32 wskazało jako rozstrzygającą: nie **kształt**
asercji, a **swoistość igły**. `StringAssert.Contains(err, "line")` przechodzi przy
odmowie o czymkolwiek — i przechodziłby także wtedy, gdyby odmowa mówiła o zupełnie
innym błędzie, co jest dosłownie usterką 6.A29.

Powód, dla którego to jest wykonalne, choć 6.A32 nie było: rodzina komunikatów jest
**zamknięta** — 209 literałów w jednym pliku. 6.A32 pytało o kształt asercji w całym
zestawie, gdzie żadnej zamkniętej rodziny nie ma, i dlatego jego przyrząd łapał 0 z 4.

## 4. Pomiar 6.D32 — ścieżki w polach bloków

```
Wejście      sciezek  387  nieistniejacych 1
      6.B5  ['tools/track/profile_scan.py']
Wyjście      sciezek   40  nieistniejacych 2
      6.B44 ['tools/track/vertical_profile.py']
      6.B8  ['tools/tests/test_test_track_fixture.py']
Weryfikacja  sciezek  149  nieistniejacych 3
      6.A30 ['data/keys/L1_A-manual.json']
      6.B39 ['tools/nie-ma-takiego-pliku.py']
      6.B44 ['tools/track/vertical_profile.py']
```

**Usterki są dwie**, nie sześć, i to rozróżnienie jest całą treścią pozycji:

- **6.B5** cytuje w „Wejściu" tools/track/profile_scan.py (bez grawisów — bo tego pliku nie ma, o to w tej pozycji chodzi); plik leży
  w `tools/blender/profile_scan.py`. Agent, który weźmie 6.B5, pójdzie pod adres,
  którego nie ma.
- **6.A30** cytuje w „Weryfikacji" data/keys/L1_A-manual.json (bez grawisów, z tego samego powodu); katalogu `data/keys`
  nie ma w drzewie **wcale** — zapisy wejść leżą w `tests/data/`. Znalazł to
  niezależnie agent wykonujący 6.A30, próbując wykonać pole „Weryfikacja" własnego
  bloku, i weryfikację zrobił na plikach istniejących.

**Cztery pozostałe są poprawne, każda z innego powodu** — i dlatego bramka „każda
ścieżka musi istnieć" zgłaszałaby cztery poprawne pozycje na dwie usterki, czyli
zostałaby wyłączona w tym samym tygodniu (6.D27):

1. plik, który pozycja ma **wytworzyć**, w polu „Wyjście" (6.B8, 6.B44);
2. ten sam plik w komendzie, **która go tworzy** (6.B44, pole „Weryfikacja");
3. ścieżka **celowo nieistniejąca**, bo o nią w teście chodzi (6.B39).

### 4.1 Mój własny przyrząd zgłosił trzy pozycje, których nie ma

Zapisane, bo to dokładnie ta klasa usterki, którą ta sesja tropiła cały dzień.
Pierwsza wersja wzorca ścieżki miała alternatywę rozszerzeń w kolejności
`…|py|cs|json|…`, więc `.cs` dopasowywało się do **przedrostka** `.csproj` i `.csv`:

```
6.A31 ['src/Sim.Runner/Sim.Runner.cs']       ← naprawde Sim.Runner.csproj
6.B21 ['src/Sim/Sim.cs']                     ← naprawde Sim.csproj
6.B44 ['data/network/station-depths.cs']     ← naprawde station-depths.csv
```

Trzy „znaleziska", z których żadne nie istnieje. Poprawione przez uporządkowanie
alternatywy od najdłuższej i domknięcie `(?![A-Za-z0-9])`. Gdybym policzył raz
i uwierzył, pozycja 6.D32 niosłaby liczbę **5 usterek** zamiast 2 — i wyglądałaby
dokładnie tak samo wiarygodnie.

Drugi przyrząd tego samego commita padł podobnie: pierwsza wersja licznika komend
szukała `^```` na początku wiersza, a bloki kodu w polach „Weryfikacja" są
**wcięte** pod punktorem. Wynik: **0 komend z 101 bloków** — zielone zero, które
wyglądałoby na czysty rezultat. Prawdziwa liczba to **279**.

### 4.2 Bramka higieny raportów złapała ten raport, i miała rację w trzech miejscach

Pierwsze uruchomienie `test_report_hygiene.py` po napisaniu tego pliku:

```
FAIL test_kazda_sciezka_wymieniona_w_raporcie_rozwiazuje_sie_w_drzewie:
ścieżki, których nie ma w drzewie: [
  'kolejka-uzupelnienie-drugie.md:77: tools/track/profile_scan.py',
  'kolejka-uzupelnienie-drugie.md:80: data/keys/L1_A-manual.json',
  'kolejka-uzupelnienie-drugie.md:175: reports/komendy-z-pol-weryfikacji.md']
  10/11 przeszło
```

Wyjście jest przytoczone **ze zdjętymi grawisami wokół trzech ścieżek**, i nie jest to
kosmetyka: pierwsza wersja tej sekcji cytowała komunikat dosłownie, a bramka zapaliła
się po raz drugi — na własnym komunikacie o błędzie, przytoczonym w raporcie o tym
błędzie. Zmierzone: `1902/1903 przeszło`, kod 1. Wzorzec bierze tokeny w grawisach
niezależnie od tego, czy stoją w zdaniu, czy w cudzysłowie cytatu, i to jest zachowanie
poprawne — raport nie ma jak powiedzieć bramce, że tym razem tylko powtarza.

Trzecia pozycja jest **moim błędem, nie znaleziskiem**: raport 6.D15 nazywa się
`reports/komendy-weryfikacji.md`, a ja wpisałem nazwę dłuższą, której nikt nigdy nie
nadał. Poprawione w **dwóch** miejscach — w tym raporcie i w polu „Wejście" bloku
6.D33. I to jest rzecz warta zapisania: bramka, którą pozycja **6.D32 proponuje dla
pól bloków**, złapałaby to natychmiast; dziś nie ma jej i wpis wszedłby do kolejki
z nazwą pliku, którego nie ma. Ta pozycja uzasadniła się w commicie, który ją dopisuje.

Dwie pierwsze pozycje są odwrotnie — to **są** znaleziska §4 i ich nieistnienie jest
całą treścią. `PATH_EXCEPTIONS` w tamtej bramce jest **pustym słownikiem** i to jest
jej wartość: jedno trafienie na 48 raportów i ~1500 tokenów. Otwieranie go po raz
pierwszy dla własnego raportu byłoby dokładnie tym osłabieniem bramki, którego
`CLAUDE.md` zabrania. Obie ścieżki są więc w prozie zapisane **bez grawisów**,
z powodem podanym na miejscu, a w bloku pomiarowym §4 zostają nietknięte — bramka
czyta tokeny w grawisach, więc wyjście pomiaru jest poza jej zasięgiem z założenia,
nie przez obejście.

## 5. Weryfikacja — wykonana

```
$ python3 tools/tests/test_all.py; echo "kod: $?"
  1903/1903 przeszło
  RAZEM 71.510 s, 1903 testów, 100 modułów
kod: 0
```

Liczniki odczytane z bramki, nie policzone ręcznie:

```
open:   19 ['5.6', '6.A19', '6.A21', '6.A30', '6.A33', '6.B26', '6.B38', '6.B39',
            '6.B40', '6.B41', '6.B42', '6.B43', '6.B44', '6.C4', '6.D24', '6.D32',
            '6.D33', '6.D34', '6.D35']
blocks: 106   zapadka: 106
nowe bez bloku: []
```

## 6. Trzy kontrole negatywne — WYKONANE

Każda wywróciła dokładnie jeden test; plik przywrócony i sprawdzony przez `cmp`.

**KN-1 — zapadka zostawiona na 101 przy 106 blokach:**

```
FAIL test_the_documented_ratchet_does_not_lag_behind_the_file: bloków z kompletem
sześciu pól jest 106, a zapadka stoi na 101 — podnieś ją do 106 w tym samym commicie,
w którym dopisujesz blok
  25/26 przeszło
```

**KN-2 — blok 6.D33 wycięty przy zapadce 106:**

```
FAIL test_the_documented_ratchet_does_not_lag_behind_the_file: bloków jest 105 przy
zapadce 106 — któryś zniknął albo stracił jedno z sześciu pól
  25/26 przeszło
```

**KN-3 — wiersz 6.A33 przeniesiony do „Czego agent nie ruszy bez decyzji".** Ta
kontrola mierzy coś innego niż dwie pierwsze: czy da się **zaspokoić próg zapasu
pozycją, której agent nie może wziąć**. Nie da się, i to w obie strony naraz — licznik
opada, a bramka zapala:

```
open przed 19, po przeniesieniu do sekcji decyzji 18
FAIL test_blocked_work_is_not_counted_as_queue: pozycje z sekcji decyzji właściciela
wpadają do licznika kolejki
  25/26 przeszło
```

## 7. Czego ten commit świadomie nie zrobił

- **Nie wykonał żadnej z pięciu pozycji.** To jest uzupełnienie zapasu, nie praca
  z niego. Każda ma komplet sześciu pól i czeka.
- **Nie poprawił dwóch złych ścieżek** z §4, choć poprawka jest jednowierszowa.
  Należą do 6.D32 razem z bramką, która pilnuje, żeby trzecia nie doszła po cichu —
  poprawka bez bramki byłaby naprawieniem objawu.
- **Nie przeliczył żadnego cudzego pomiaru.** `reports/audyt-asercji.md`
  i `reports/komendy-weryfikacji.md` są pomiarami z datą; pozycje 6.D33 i 6.D35
  przewidują dla nich **adnotację**, nie poprawkę (`docs/04-conventions.md`).
- **Nie obniżył progu.** `MINIMUM_READY_ITEMS` zostaje na 12.

## 8. Co zauważone przy okazji, nietknięte

- **`reports/audyt-asercji.md` §7 mówi „53 asercje", a szerszy wzorzec daje 63**
  w `Game.Tests`. Różnica jest definicją, nie sprzecznością — tamten raport liczył
  asercje **gołe** (bez licznika i bez asercji na brak w tym samym ciele), a ja
  liczyłem wszystkie kształtu `Contains`. Zapisane w bloku 6.D34 razem z tą różnicą,
  bo bez niej wyglądałoby to na rozjazd.
- **Trzy najliczniejsze pliki C# po moim wzorcu to `RunnerCommandTests.cs` (87),
  `RunPlanTests.cs` (20) i `TelemetryTrackTests.cs` (19)** — czyli runner jest
  pierwszy, i to z przewagą czterokrotną. Zdanie §7 tamtego raportu („trzy
  najliczniejsze to testy Godota") dotyczy węższej definicji; to jest **osobna sprawa**
  od 6.D35, która dotyczy wyłącznie tego, że `InputLogTests.cs` w `Game.Tests` nie leży.
