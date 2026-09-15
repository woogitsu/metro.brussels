# 6.D224 — druga ślepa plamka tego samego sita, i obie się nakładają

**15.09.2026**, na `ded3fa0`. Wejście: `tests/Game.Tests/UiTextTests.cs`
(`NazwyWyliczeniowychWRdzeniu`, `CeleToStringBezArgumentu`, `NazwyDwuznaczneWRdzeniu`,
`DeklaracjaZmiennej`, `NieTyp`), `src/Sim/**/*.cs`,
`reports/6d213-trzy-wywolania-i-piec-nazw-dwuznacznych.md`.

## 1. Co pilnuje dziś sito rdzenia i czego nie widzi

Sito z 6.D213 pyta, czy w `src/Sim/` stoi `.ToString()` na wartości typu wyliczeniowego
— rdzeń nie ma ekranu (§4.9), więc angielski identyfikator szedłby do dziennika albo do
telemetrii. Deklaracje czyta wzorcem `Typ nazwa`.

**Deklaracji z typem WNIOSKOWANYM ten wzorzec nie widzi.** W `src/Sim/` słowo `var` pada
**536** razy w **57** plikach, tyle samo surowo i po masce `KodLeksykalnie`; **535** z nich
wiąże jedną nazwę, a 536-te (`ServiceDay.cs`, `foreach (var (moment, delta) in events)`)
rozkłada krotkę i żadnej nazwy pojedynczej nie deklaruje.

## 2. Wykaz, a nie liczba

Pod `var` kryje się w rdzeniu **dziesięć** wartości typu wyliczeniowego. Stoją wypisane
z nazwy w `VarOTypieWyliczeniowymWRdzeniu`, w kształcie `ścieżka | nazwa | typ | wzorzec
deklaracji`:

| plik | nazwa | typ |
|---|---|---|
| `src/Sim/Physics/VehicleRegistry.cs` | `status` | `ParameterStatus` |
| `src/Sim/Signalling/CbtcTestArea.cs` | `status` | `ParameterStatus` |
| `src/Sim/Signalling/FixedBlockSystem.cs` | `reason` | `AuthorityLimit` |
| `src/Sim/Signalling/SignallingPlan.cs` | `status` (×2, różne wzorce) | `ParameterStatus` |
| `src/Sim/Signalling/SignallingPlan.cs` | `variant` | `ProtectionVariant` |
| `src/Sim/Signalling/TrainProtection.cs` | `previous` | `ProtectionAction` |
| `src/Sim/Train/DoorCycle.cs` | `phase` | `DoorPhase` |
| `src/Sim/Train/LineDrive.cs` | `phase` | `DoorPhase` |
| `src/Sim/Train/StationStop.cs` | `phase` | `DoorPhase` |

**Czwarte pole jest warunkiem, żeby wykaz miał dziesięć pozycji, a nie dziewięć:** dwie
deklaracje `var status` w `SignallingPlan.cs` różnią się tylko wzorcem. **Numeru wiersza
w kluczu NIE MA świadomie** — zapalałby się przy każdym przesunięciu linii, czyli na
kodzie poprawnym (6.D27).

**Dziewięciu z dziesięciu wpisów nie da się z drzewa WYPROWADZIĆ.** Typ jest w nich typem
**zwracanym**: przez `ParameterStatusParser.Parse` (×4), przez wyrażenie `switch` (×1),
przez odczyt właściwości z innego pliku (×1), przez argument generyczny słownika
w `out var` (×1) i przez element kolekcji w `foreach` (×2). Jedyny kształt czytelny
wzorcem to `var nazwa = Wyliczenie.Człon` i w całym rdzeniu stoi on **raz** —
`FixedBlockSystem.cs`, `var reason = AuthorityLimit.EndOfLine`.

## 3. Najważniejsza liczba: obie plamki się NAKŁADAJĄ — 8 z 10

`NakladaniePlamek = 8`. Osiem z dziesięciu tych deklaracji nosi nazwę, którą **pierwsza**
plamka (`NazwyDwuznaczneWRdzeniu`) i tak odrzuca: `phase` ×3, `status` ×4, `variant` ×1.

**Cena domknięcia drugiej plamki wynosi więc 2 pozycje z 10 i ZERO usterek** — bo wywołań
`.ToString()` na którejkolwiek z tych dziesięciu nazw jest dziś **zero**. Nawet doskonałe
wnioskowanie typu — Roslyn, metadane, cokolwiek — pokazałoby situ **2 z 10**.

To jest odpowiedź na pytanie właściciela z 6.D224 („bramka zostaje na źródle, plamki
zapisane") wyrażona liczbą, a nie zdaniem: decyzja kosztuje dwie pozycje, nie dziesięć.

**Zależność idzie też w drugą stronę i to jest pomiar, nie domysł.** Druga plamka
częściowo **wytwarza** pierwszą: `DeklaracjaZmiennej` bierze `var` za nazwę typu, a `var`
nie stoi w `NieTyp`, więc każda nazwa zadeklarowana przez `var` ląduje w koszyku „inne
typy". Podstawienie: gdyby `var` dopisać do `NieTyp`, nazw dwuznacznych byłoby **4, nie
5** (odpadłaby `expected`, dwuznaczna **wyłącznie** przez `ProtectionMode.cs`
`var expected = ForHistoricalDate(date)`, gdzie typem jest klasa), a jednoznacznych
**20 zamiast 19**. Podstawienia nie wykonano — `NazwyDwuznaczneWRdzeniu` jest przybite
przy 6.D213 i jego zmiana jest osobną decyzją, nie skutkiem ubocznym.

## 4. Podłogi na 536 NIE MA, i to jest wynik kontroli negatywnej

Napisana najpierw, wzorem `MinimumToStringWRdzeniu`, i **obalona pomiarem**: zamiana
`var phase = _stop.Phase;` w `LineDrive.cs` na `DoorPhase phase = _stop.Phase;` — czyli
**dokładnie ta poprawka, na którą ta pozycja wskazuje** — daje 535 i zapala podłogę
komunikatem „czytnik przestał czytać", który jest wtedy nieprawdą. 6.D27, więc podłoga
wyleciała. Liczba 536 stoi w komentarzu jako **pomiar**, nie jako zapadka.

`MinimumToStringWRdzeniu` tej wady nie ma, bo tamtych wywołań przybywa razem z kodem
i nikt ich celowo nie usuwa; **`var`-y usuwa się celowo**.

Zamiast podłogi stoją dwa mocniejsze sprawdzenia oślepnięcia: równość „surowo == po
masce" oraz dziesięć wzorców wykazu, z których każdy musi trafić **dokładnie raz**.

## 5. Kontrole negatywne

Baza: `dotnet test tests/Game.Tests` **318/318**.

| KN | co podstawiono | przewidywanie | wynik rzeczywisty |
|---|---|---|---|
| KN-1 | `KnProba.cs`: `var knFaza = Zrodlo(); return knFaza.ToString();` | **zielone** — plamka jest prawdziwa | **zielone**, `Passed: 4` |
| KN-2 | to samo z typem **jawnym** | czerwone | **czerwone**: `` `.ToString()` na wartości typu wyliczeniowego w `src/Sim/`: knFaza `` |
| KN-3 | `var knFaza = DoorPhase.Open;` dołożone do `src/Sim/` | czerwone (przybity zbiór) | **czerwone**, zbiór rozjechał się z wykazem |
| KN-4 | skreślenie wpisu StationStop | czerwone | **czerwone**: `Expected:<8>. Actual:<7>` |
| KN-5 | `var phase` → `DoorPhase phase` w `LineDrive.cs` | czerwone, z komunikatem o wpisie | **czerwone** na wpisie — **ale w pierwszej wersji patcha zapaliła najpierw podłoga 536**, i to jest powód, dla którego podłogi w patchu nie ma |
| KN-6 | skreślenie wpisu **razem** z obniżeniem `NakladaniePlamek` na 7 | ? | **zielone** — nazwana granica, §6 |
| KN-7 | `var knTekst = new StringBuilder(); return knTekst.ToString();` | zielone (kod poprawny) | **zielone**, `Passed: 3` |

**Dwie kontrole powtórzone niezależnie przy domykaniu pozycji, na dzisiejszym drzewie:**

- **KN-A** (= KN-4): skreślenie wpisu StationStop →
  `Failed: 1, Passed: 317`, `Assert.AreEqual failed. Expected:<8>. Actual:<7>.
  nakładanie się obu ślepych plamek wynosi dziś 7 z 9, a przybite jest 8`.
  `md5sum -c` po przywróceniu: **OK**.
- **KN-B** (= KN-3, wzmocniona): plik KnProba6D224 dołożony do `src/Sim/Train/` z treścią
  `var knFaza = DoorPhase.Open; return knFaza.ToString();` →
  `Failed: 1, Passed: 317`, `zbiór var-ów … rozjechał się z wykazem: z wykazu
  [FixedBlockSystem.cs|reason|AuthorityLimit], z drzewa [FixedBlockSystem.cs|reason|
  AuthorityLimit, KnProba6D224.cs|knFaza|DoorPhase]`.

  **KN-B jest zarazem dowodem samej plamki, i to jest jej najważniejsza własność:**
  ten plik niesie `.ToString()` na wartości wyliczeniowej w `src/Sim/`, a zapaliła się
  **wyłącznie nowa bramka**. Stare sito milczało. Liczba usterek, które dziś
  przepuszcza, jest więc zmierzona jednym przebiegiem, a nie wywnioskowana z wykazu.

## 6. Granica, zmierzona i nazwana

**KN-6 jest wynikiem, a nie porażką.** Dziewięciu z dziesięciu wpisów nie da się z drzewa
wyprowadzić — można tylko sprawdzić, że nadal tam stoją. Skreślenie jednego z tych
dziewięciu **razem** z obniżeniem liczby przechodzi na zielono.

Nie jest to wada do naprawienia wzorcem: **gdyby dało się to policzyć, plamka nie byłaby
ślepa.** Jedyny wpis, który drzewo potwierdza samo, to
`FixedBlockSystem.cs|reason|AuthorityLimit` — i ten jest porównywany jako zbiór, więc
KN-3 zapala.

**Druga granica, też nazwana:** `TrainProtection.cs` ma **dwa** `var previous` — ten
z wykazu (`ProtectionAction`, wiersz 359) i drugi, `bool`, z `_lastDoorRelease`
(wiersz 426). Sprawdzenie `.ToString()` jest zawężone do **pliku** wpisu, więc wywołanie
na tym drugim zapaliłoby bramkę niesłusznie. Gdy to nastąpi, wpis dostaje **nazwany
wyjątek**, a bramka **nie** jest wyłączana — tak stoi w komentarzu przy niej.

## 7. Weryfikacja

```
python3 tools/tests/test_all.py     ->  2491/2491 przeszło, 126 modułów
dotnet test tests/Game.Tests         ->  Passed: 318, Failed: 0   (baza 316)
dotnet test tests/Sim.Tests          ->  Passed: 662, Failed: 0   (nietknięte)
```

## 8. Zapadki

| zapadka | ruch |
|---|---|
| `ASERCJI_RAZEM` **3170** | z 3155, czyli +15, wszystkie z komunikatem |
| `Z_KOMUNIKATEM_RAZEM` **1723** | z 1708, czyli +15 |
| `ROZKLAD_LICZBOWYCH["tests/Game.Tests"]` | `razem` 237 → 240, `bez_tolerancji` 134 → 137, `calkowite` 128 → 131 |
| `ROZKLAD_POSTACI["tests"]` | `zwykly` 4511 → 4562, `$` 769 → 783, `@` 76 → 88, `$@` 6 → 7 |
| `BEZ_KOMUNIKATU_RAZEM`, `NIEROZSTRZYGNIETYCH`, `tolerancja_zero` | **nie drgnęły** |

Werbatim rośnie o **dwanaście**: dziesięć wpisów wykazu (ukośnik jest treścią wzorca)
i dwa `Regex` czytnika. `NakladaniePlamek` do rozkładu pinów **nie wchodzi** i to jest
treść, a nie przeoczenie: stoi jako stała, więc w asercji nie ma literału.

## 9. Czego NIE zrobiono

- **Nie zaproponowano Roslyna, metadanych ani żadnej zależności.** Decyzja właściciela
  (6.D224: „zostaje na źródle, plamki zapisane") jest wiążąca. Zapisany jest wyłącznie
  jej koszt: **2 pozycje z 10, 0 usterek**.
- **Nie ruszono `NazwyDwuznaczneWRdzeniu` ani `NieTyp`**, choć zmierzono, że dopisanie
  `var` do `NieTyp` zmniejsza pierwszą plamkę z 5 nazw do 4. To 6.D213, domknięte.
- **Nie ujednolicano oczekiwań** ani nie dokładano piątej postaci literału.
- **`src/Sim/` nietknięte** — zero zmian w rdzeniu; pliki z kontroli negatywnych
  usunięte, `md5sum -c` na `UiTextTests.cs` po każdej: OK.

## 10. Zauważone przy okazji, nietknięte

- **`TrackAxis.cs:245` ma `out var status`** (`JsonElement`), a `ProtectionMode.cs:199`
  `var expected` (klasa) — obie nazwy z wykazu, oba **nie** wyliczenia. Wzorzec ich nie
  odróżnia od wyliczeniowych, co jest kolejnym dowodem, że wykaz musi być ręczny.
- **Łańcuch komentarzy historycznych w `test_csharp_test_methods.py` urywa się na
  6.D215 (4438);** wpis 6.D217, który podniósł liczby do 4511/769/76, komentarza nie
  zostawił. Historii, której nikt nie widział, tu się nie dopisuje.
- **`test_all.py` wypisuje po drodze `BLAD: koszt kroku 15.500 us przekracza prog
  14.000 us` i `BLAD: rozstep powtorzen 115.9 %`** — wypisy testów wydajnościowych,
  które same siebie unieważniają na tej maszynie; zestaw kończy się kodem 0 i zero FAIL.
