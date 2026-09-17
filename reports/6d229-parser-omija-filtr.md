# 6.D229 — wyjątek parsera JSON-a omija filtr `catch`: trzynaście miejsc, nie jedno

**Zmierzone 17.09.2026 na commicie:** `a91a83edc7356b6f9869b8c43583e93369b8fcdd`

Sonda: własny program konsolowy
z referencją do `src/Sim/Sim.csproj`, podający czterem loaderom cztery kształty wejścia
i sprawdzający, czy typ wyjątku mieści się w filtrach `catch` tego repozytorium.

## 1. Co pytano i co wyszło

Opis pozycji podawał **cztery próbki na jednym loaderze** (`SignallingPlan.FromJson`)
i liczbę „2 z 4 przelatują". **Ta liczba się zgadza** — przeliczona dziś daje to samo,
co do kształtu: `{{{` i napis pusty rzucają `JsonReaderException`, `{}` i dokument
opisujący obszar+tryb rzucają polski `FormatException`.

Nowe jest to, czego opis nie podawał: **loaderów z tą samą szczeliną jest pięć,
a miejsc wywołania trzynaście**.

## 2. Wykaz miejsc — stan PRZED łatką

Filtry, wobec których mierzono:

- `src/Sim.Runner/Program.cs:247` — `IOException or ArgumentException or FormatException or InvalidOperationException`
- `src/Game/FirstRun.cs:1034` i `:1061` — `ArgumentException or FormatException`

`JsonReaderException` (po `JsonException`, po `Exception`) nie stoi w żadnym z nich.

| # | miejsce wywołania | loader | osłona | kod wyjścia PRZED | język PRZED |
|---|---|---|---|---|---|
| 1 | `src/Game/FirstRun.cs:1032` | `SignallingPlan.FromJson` | filtr `:1034` | wyjątek w `_Ready` | angielski + stos |
| 2 | `src/Game/FirstRun.cs:720` | `TrackAxis.FromJson` | **brak `try`** | wyjątek w `_Ready` | angielski + stos |
| 3 | `src/Game/FirstRun.cs:1159` | `ChunkManifest.FromJson` | **brak `try`** | wyjątek w `_Ready` | angielski + stos |
| 4 | `src/Sim.Runner/Program.cs:711` | `TrackAxis.FromJson` | handler `:247` | 134 | angielski + stos |
| 5 | `src/Sim.Runner/Program.cs:712` | `SignallingPlan.FromFile` | handler `:247` | 134 | angielski + stos |
| 6 | `src/Sim.Runner/Program.cs:1046` | `TrackAxis.FromJson` | handler `:247` | 134 | angielski + stos |
| 7 | `src/Sim.Runner/Program.cs:1078` | `JsonDocument.Parse` wprost | handler `:247` | 134 | angielski + stos |
| 8 | `src/Sim.Runner/Program.cs:1118` | `TrackAxis.FromJson` | handler `:247` | 134 | angielski + stos |
| 9 | `src/Sim.Runner/Program.cs:1154` | `SignallingPlan.FromJson` | handler `:247` | 134 | angielski + stos |
| 10 | `src/Sim.Runner/Program.cs:1288` | `JsonDocument.Parse` wprost | handler `:247` | 134 | angielski + stos |
| 11 | `src/Sim.Runner/Program.cs:1683` | `ServiceDay.FromJson` | handler `:247` | 134 | angielski + stos |
| 12 | `src/Sim.Runner/Program.cs:1808` | `TrackAxis.FromJson` | handler `:247` | 134 | angielski + stos |
| 13 | `src/Sim.Runner/Program.cs:1809` | `SignallingPlan.FromJson` | handler `:247` | 134 | angielski + stos |

Kod 134 nie jest wywnioskowany z typu wyjątku — jest **zmierzony** przebiegiem CLI:

```
$ dotnet run --project src/Sim.Runner -- axis --axis <plik z `{{{`>
Unhandled exception. System.Text.Json.JsonReaderException: '{' is an invalid start of a
property name. Expected a '"'. LineNumber: 0 | BytePositionInLine: 1.
   at System.Text.Json.ThrowHelper.ThrowJsonReaderException(...)
KOD=134
```

To ta sama sygnatura, którą 6.A12 opisało dla `KeyNotFoundException`: kod 134 i stos.

**Poza wykazem, z powodem.** `ProtectionMode.cs:223` i `VehicleRegistry.cs:189` parsują
**zasób osadzony w assembly**, nie plik podany przez użytkownika — zepsuta składnia
znaczy tam zepsuty build, a nie zły plik wejściowy. `CbtcTestArea.FromJson` szczelinę ma
taką samą, ale w `src/` nie ma dziś ani jednego wywołania — woła go wyłącznie test.

## 3. Rozstrzygnięcie: poprawka idzie do parsowania, nie do filtrów

Pozycja zakazywała przyjmować bez pomiaru, że wystarczy dopisać `JsonException` do
filtru. Po pomiarze: **nie wystarcza, i to z dwóch niezależnych powodów.**

1. **Filtry nie pokrywają wszystkich miejsc.** Miejsca 2 i 3 nie mają `try` w ogóle.
   Dopisanie typu do trzech filtrów zostawiłoby je dokładnie tam, gdzie były, a są to
   dwa z trzech miejsc po stronie gry — czyli tam, gdzie zły plik podaje gracz.
2. **Filtr nie załatwia drugiej połowy usterki.** Tytuł pozycji mówi „po angielsku
   i ze stosem". Filtr zdejmuje stos, ale przepisuje `error.Message` .NET-a, więc wiersz
   odmowy dalej byłby po angielsku. Polski komunikat może powstać tylko tam, gdzie znana
   jest nazwa czytanego pliku — czyli w loaderze.

Poprawka jest więc jedna: `JsonDocument.Parse` w loaderach czytających pliki
użytkownika idzie przez `MetroBxl.Sim.JsonText.Parse`, które łapie `JsonException`
i podnosi `FormatException` z polskim wierszem, zachowując powód parsera jako
`InnerException`. `FormatException` stoi **już** we wszystkich trzech filtrach, więc
żaden kod wyjścia się nie zmienia — zmienia się to, że odmowa w ogóle powstaje.
To dokładnie ten sam ruch, który 6.A12 zrobiło dla `GetProperty` przez
`SignallingPlan.Required`; parsowanie zostało wtedy pominięte.

## 4. Stan PO łatce — ta sama sonda, to samo CLI

```
$ dotnet run --project src/Sim.Runner -- axis --axis <plik z `{{{`>
BŁĄD: oś trasy nie jest poprawnym JSON-em: '{' is an invalid start of a property name.
Expected a '"'. LineNumber: 0 | BytePositionInLine: 1.
KOD=1
```

Wszystkie trzynaście miejsc kończy się dziś polskim wierszem odmowy i kodem, który
temu miejscu przysługiwał wcześniej.

## 5. Czego ta łatka NIE zamyka — zmierzone, nie przemilczane

Sonda pokazała **drugą** szczelinę tej samej rodziny, której pozycja nie dotyczy:
`TrackAxis.FromJson` i `CbtcTestArea.FromJson` na dokumencie **składniowo poprawnym,
ale nie tym** (`{}`, dokument obszar+tryb) rzucają `KeyNotFoundException` — typ, którego
nie wymienia żaden z trzech filtrów. To jest wprost 6.A12, tyle że dla loaderów, do
których tamta poprawka nie dotarła: `SignallingPlan` dostał wtedy `Required()`,
`TrackAxis` i `CbtcTestArea` wołają `GetProperty` nago. Zakres 6.D229 mówi
o `JsonDocument.Parse`, więc te dwa loadery zostają nietknięte i są osobną pozycją.

## 6. Zapadki ruszone tą pozycją — i jedna, którą trzeba PRZELICZYĆ po scaleniu

Łatka dokłada jeden plik źródłowy, jeden plik testowy i jeden raport, więc rusza
dziewięć zapadek liczących drzewo. Wszystkie są **równościami przeliczonymi na drzewie**,
a nie podłogami z zapasem — taka jest ich klasa i pozycja jej nie zmienia:

**Tabela niżej podaje wartości DZISIEJSZE, a wartości z dnia pomiaru w osobnej
kolumnie — i nie jest to układ, tylko wymóg:** czytnik twierdzeń bierze PIERWSZĄ liczbę
stojącą po nazwie stałej, więc zapis „stara → nowa" czyta się jako twierdzenie o wartości
STAREJ. Liczby z dnia pomiaru są przy tym **nieaktualne**, bo między pomiarem a wdrożeniem
scalono 6.D231 i 6.D232, które ruszyły te same zapadki; wartości dzisiejsze są przeliczone
z drzewa po scaleniu, a nie złożone z dwóch stron.

| zapadka | plik | dziś | w dniu pomiaru |
|---|---|---|---|
| `ASERCJI_RAZEM` | `tools/tests/test_csharp_assertions.py` | **3188** | 3179 |
| `Z_KOMUNIKATEM_RAZEM` | `tools/tests/test_csharp_assertions.py` | **1741** | 1732 |
| rozkład pinów `tests/Sim.Tests` | `tools/tests/test_csharp_pins.py` | razem **480** | 478 |
| kotwice pinów `UiTextTests.cs` | `tools/tests/test_csharp_pins.py` | ósmy ruch numerów wiersza |
| rozkład literałów pod `src/` | `tools/tests/test_csharp_test_methods.py` | `zwykly` 1377 → 1384 |
| rozkład literałów pod `tests/` | `tools/tests/test_csharp_test_methods.py` | zwykły **4602**, interpolowany **792** | 4581 / 786 |
| `LiteralowWZasieguBramki` | `tests/Game.Tests/UiTextTests.cs` | 573 → 574 |
| `PozycjiStaregoCzytnika` | `tests/Game.Tests/UiTextTests.cs` | 614 → 615 |
| `LiteralowDotknietychZdejmowaniem` | `tests/Game.Tests/UiTextTests.cs` | 393 → 394 |

`ZAPADEK_RAZEM` w `tools/tests/test_tree_walks.py` **nie jest ruszane** — żadna nowa
zapadka nie powstaje.

**Zapadka liczby raportów wymagała ręki przy scalaniu — przewidziane w pomiarze
i potwierdzone przy wdrożeniu.** Pomiar tej pozycji stał na bazie, na której katalog
miał 368 plików, i ustawiał próg na 369. Ostrzeżenie zapisane wtedy brzmiało: wierzchołek
`main` mówi **to samo** co gałąź, a drzewo po scaleniu będzie miało o jeden więcej —
**zgodność stron nie znaczy poprawności sumy**, tak jak przy ósmym starciu opisanym
przy samej stałej.

**Tak się stało, tylko o dwa dalej.** Między pomiarem a wdrożeniem scalono 6.D231
i 6.D232, więc drzewo po scaleniu ma **372**, a nie 370. Wartość została policzona
na drzewie, nie złożona z pamięci:

```
$ ls reports/*.md | wc -l
372
```

**Ten akapit sam zapalił bramkę przy pierwszym przebiegu** i to jest część wyniku:
jego pierwsza wersja cytowała kształt `NAZWA = N` z wartością 369 — czyli twierdzeniem
o dzisiejszym kodzie, które przestało być prawdziwe w chwili scalenia. Czytnik
`test_ksztalt_w_jednych_grawisach_daje_SAME_CYTATY` zgłosił to jako rozjazd, którego
datowanie nie zwalnia. Akapit podaje dziś liczbę **poleceniem, które ją odczytuje**,
a nie kształtem, który czytnik weźmie za twierdzenie o stałej.
