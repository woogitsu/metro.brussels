# 6.D217 — zero literałów angielskich, dziewięć dziur z silnika i jedna szczelina

**15.09.2026**, na `9d5b6bd`. Wejście: `src/Game/FirstRun.cs` (`Abort` i jego wołający),
`src/Game/RunPlan.cs` (`Refusal`), `src/Game/Assets/GlbLoader.cs`,
`src/Game/DesignAssumptions.cs`, `src/Sim/Signalling/SignallingPlan.cs`,
`src/Sim/Train/InputLog.cs`, `tests/Game.Tests/UiTextTests.cs` (sekcja 6.D202:
`WierszeLogu`, `SlowaPolskieBezZnakow`, `WygladaPoPolsku`),
`reports/6d202-zero-wierszy-angielskich-i-dwadziescia-siedem-identyfikatorow.md` §8.

## 1. Liczby, których żądało pole „Wyjście"

| | |
|---|---:|
| wołających `Abort` (bez deklaracji) | **21** |
| z tego z własnymi słowami | **20**, wszystkie polskie |
| **bez własnych słów** | **1** — `FirstRun.cs:533` |
| `GD.PrintErr` razem / poza `Abort` | **3** / **2** |
| `GD.PushError` razem / poza `Abort` | **4** / **3** |
| **literałów angielskich w całej drodze błędu** | **0** |
| dziur niosących tekst **obcy** | **9**, wszystkie jednego typu |
| dziur niosących tekst **własny** | **5** |

**Liczby z pola „Skąd" trzymają się co do jednej:** `GD.PrintErr` 3 i `GD.PushError` 4 —
z tym że po jednym z każdej stoi **wewnątrz** `Abort` i niesie jego argument, nie własny
literał, więc drogą osobną jest 2 i 3.

## 2. Tekst obcy wchodzi WYŁĄCZNIE dziurą i jest jednym typem

Literałów angielskich nie ma ani jednego. Angielszczyzna przychodzi z interpolacji,
a każda taka dziura niesie **`Error` Godota**:

| wytwórca | ile |
|---|---:|
| `FileAccess.GetOpenError()` | **7** |
| wynik `DirAccess.MakeDir` (`FirstRun.cs:700`) | 1 |
| wynik `GltfDocument.AppendFromFile` (`GlbLoader.cs:39`) | 1 |

**To jest odpowiedź na pytanie pozycji o pochodzenie:** wszystkie dziewięć pochodzi
z silnika, wszystkie są tym samym typem, i przetłumaczyć się ich nie da bez mapy nazw
`ERR_*`, czyli bez decyzji, której w `docs/` nie ma (§8).

Dziury z tekstem **własnym** — `error.Message` (×3), out-param `TelemetryTrack.TryParse`,
`ViewAssumption.Reason` — prowadzą do literałów polskich w `src/Sim/` i `src/Game/`.

**Rozdzielenie tych dwóch zbiorów jest całą treścią pola „Skończone, gdy"**, bo tylko
o drugim da się cokolwiek rozstrzygnąć.

## 3. Jedyny komunikat bez własnych słów ma DWUDZIESTU SZEŚCIU wytwórców

`FirstRun.cs:533` to `Abort(plan.ExitCode, plan.Error!)` — ani jednego literału. Treść
przychodzi z `RunPlan.Refusal`, którego wołających jest **26**: 19 z własnym literałem
polskim i 7 przekazujących `error!` z `TryLong`/`TryDouble`, czyli z **dwóch** dalszych
literałów polskich. Za jednym wierszem bez słów stoi więc **21 różnych komunikatów**,
wszystkie polskie, i żaden skan `FirstRun.cs` ich nie widzi.

Pole przewidywało, że „wołających jest więcej" niż czterech wierszy z 6.D202. Jest ich
**dwadzieścia sześć** — rząd wielkości, nie kilka.

## 4. Drugi komunikat bez słów, innego rodzaju

`GlbLoader.cs:39` — `$"[ASSETS] {absolutePath}: AppendFromFile -> {error}"` — **literał
ma**, ale jego jedyne „słowo" to nazwa metody Godota. Po polsku nie jest i po angielsku
też nie, bo nie jest zdaniem. Oba miejsca stoją więc na liście z **powodem**, a nie jako
liczba „dwa" (6.D131).

## 5. Sito po znaku diakrytycznym myli się tu na DZIEWIĘCIU z dwudziestu dziewięciu

6.D202 zmierzyło dla logu przejazdu **3 z 25** (12 %). Dla drogi błędu jest to
**9 z 29** (31 %), i nie jest to przypadek: droga błędu nazywa **argumenty i pliki**
(`--limit-kmh`, `.glb`, `[ASSETS]`), więc jej zdania są krótkie i techniczne — a krótkie
polskie zdanie techniczne często nie ma ani jednego ogonka („[SYGNALIZACJA] {} nie jest
planem", „[ASSETS] brak pliku", „[ARGUMENT] nieznany argument").

Lista `SlowaPolskieBezZnakow` rośnie o **dwanaście** słów, każde dobrane tak, żeby nie
było podciągiem zwykłego słowa angielskiego — dlatego stoi `nieznan`, a nie `nie`:
to drugie siedzi w `denied` i uznałoby komunikat **angielski** za polski.

**Cena wypisana z nazwy:** komunikat angielski zawierający którykolwiek z tych podciągów
przejdzie jako polski. Dziś takiego nie ma, a gdy powstanie, złapie go bramka rozdzielająca
źródła dziur — bo tekst obcy wchodzi tu wyłącznie dziurą.

## 6. Szczelina znaleziona po drodze, nie naprawiona tutaj

`ReadSignallingPlan` łapie `when (error is ArgumentException or FormatException)`.
`SignallingPlan.FromJson` woła `JsonDocument.Parse`, a ten przy **zepsutej składni**
rzuca `JsonReaderException`, który do tego filtru **nie należy**. Zmierzone na czterech
próbkach:

| wejście | wyjątek | filtr łapie |
|---|---|---|
| `{{{` | `JsonReaderException` | **NIE** |
| `{}` | `FormatException` (polski) | tak |
| `{"area_id":…}` | `FormatException` (polski) | tak |
| napis pusty | `JsonReaderException` | **NIE** |

Dla porównania `InputLog.Parse` na tych samych kształtach rzuca **zawsze**
`FormatException` z polskim komunikatem — bo jest własnym czytnikiem tekstu, a nie
nakładką na `System.Text.Json`.

Skutek: `--signalling` na pliku o zepsutej składni kończy się **angielskim komunikatem
.NET-a i stosem wywołań**, zamiast polskim wierszem `[SYGNALIZACJA] … nie jest planem`.
Jest to ta sama rodzina co 6.A12 (`KeyNotFoundException`), domknięta wtedy dla
`GetProperty` przez `Required()`, ale **samo parsowanie nigdy nie zostało owinięte**.

**Nie naprawiam tego tutaj:** pozycja pyta o język i pochodzenie, a nie o zachowanie,
a „zmiana zachowania `Abort`" stoi w jej polu „Poza zakresem". Wpisane jako **6.D229**.

## 7. Kontrole negatywne

Baza: **316/316** w `Game.Tests`, **662/662** w `Sim.Tests`, **2488/2488** w zestawie.
`md5sum -c` `OK` po każdej.

| | podstawienie | wynik |
|---|---|---|
| KN-1 | sito deklaracji `Abort` zdjęte | **ZIELONE — luka mojej bramki** |
| KN-1b | to samo, po usunięciu drugiego mechanizmu | **1 czerwony** (22 zamiast 21) |
| KN-2 | komunikat **angielski** dopisany do drogi błędu | **1 czerwony** |
| KN-3 | jedna odmowa `RunPlan` przepisana na angielską | **1 czerwony** |
| KN-4 | fabryka `Refusal` przemianowana (czytnik oślepiony) | **1 czerwony** |
| KN-5 | klucz źródeł po samej NAZWIE dziury | **1 czerwony** (10 zamiast 9) |

**KN-1 zmieniła bramkę, a nie tylko ją potwierdziła.** Pierwsza wersja odsiewała
deklarację `Abort` **dwoma mechanizmami naraz** — wyprzedzeniem ujemnym we wzorcu
i osobnym warunkiem — więc zdjęcie warunku wyszło zielone i czytało się jako „bramka
tego nie łapie". Łapała, tylko drugim. Wyprzedzenie poszło, bo było **węższe**:
wypisywało `private void` z nazwy i przepuściłoby deklarację `private static void`
albo `internal`. Po jego usunięciu KN-1b zapala.

**KN-5 jest tą, którą bramka złapała u mnie przed werdyktem.** Klucz po samej nazwie
dziury policzył dziewięć dziur obcych jako dziesięć, bo `{error}` stoi w drodze błędu
**dwa razy i za każdym razem znaczy co innego**: w `GlbLoader.cs:39` to `Error` Godota,
a w `FirstRun.cs:1089` nasz out-param. Dokładnie ta sama pomyłka, którą 6.D213 zmierzyło
na `string status`. Kluczem jest od tej pozycji **para (plik, wyrażenie)**.

Pełne przebiegi:

```
$ dotnet test tests/Game.Tests
Passed!  - Failed: 0, Passed: 316, Skipped: 0, Total: 316

$ dotnet test tests/Sim.Tests
Passed!  - Failed: 0, Passed: 662, Skipped: 0, Total: 662

$ python3 tools/tests/test_all.py
  2488/2488 przeszło
```

## 8. Czytnik jest JEDEN, wydzielony, a nie napisany obok

`WierszeLogu` z 6.D202 i droga błędu potrzebują dokładnie tego samego czytania — po
źródle bez komentarzy i bez literałów innych niż argument — i różnią się **wyłącznie
nazwą wywołania**. Wspólne `Wywolania(wzorzec)` jest więc wydzielone, a `WierszeLogu`
woła je z `GD\.Print\s*\(`. Druga kopia rozjechałaby się przy pierwszej poprawce, a 6.D213
usunęło już jedną taką kopię w tym samym pliku. Że wydzielenie niczego nie zmieniło,
pokazuje przebieg **313/313** natychmiast po nim, przed dopisaniem czegokolwiek.

Czytnik zwraca teraz **dziury osobno** i to też jest treść, nie wygoda: pytanie „skąd
ten angielski" nie ma odpowiedzi w szablonie, tylko w dziurze.

## 9. Czego świadomie nie zrobiłem

- **Nie przetłumaczyłem niczego** — pole tego zabraniało, a dziewięć dziur obcych to
  `Error` Godota, czyli mapa nazw i decyzja właściciela.
- **Nie zmieniłem zachowania `Abort`.**
- **Nie owinąłem `JsonDocument.Parse`** — §6, wpisane jako 6.D229.
- **Nie tknąłem wierszy `GD.Print`** (to 6.D202, domknięte).

## 10. Zauważone, nie tknięte

- **`RunPlan.cs` ma 26 wołających `Refusal`, a `FirstRun.cs` 21 wołających `Abort`** —
  droga błędu ma więc dwa piętra o zbliżonej wielkości, a bramka języka patrzy dziś na
  oba, tylko drugie przez jedno jedyne wywołanie. Ile pięter ma cała gra, nie liczyłem.
- **`src/Sim.Runner/` ma własną drogę błędu i jest poza korpusem tej pozycji** — tak samo
  jak było poza korpusem 6.D202, i tak samo nikt jej nie policzył (6.D214 §8 zauważyło
  ten katalog przy innym pytaniu).
