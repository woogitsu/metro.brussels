# 6.D233 — osłona pola na czterech czytnikach, a piąty ZAWĘŻONY z powodu, który jest pomiarem

**Data:** 17.09.2026 · **Gałąź:** `claude/6d233-osloniety-getproperty` · **Baza:** `8565ba7`

## 1. Co padało

`GetProperty` na dokumencie **składniowo poprawnym, ale nie tym** rzuca
`KeyNotFoundException` — typ, którego nie wymienia żaden z trzech filtrów `catch`.
Zmierzone na CLI moją ręką, przed łatką:

```
$ … axis --axis <plik o treści {}>
Unhandled exception. System.Collections.Generic.KeyNotFoundException: The given key
was not present in the dictionary.
   at MetroBxl.Sim.Line.TrackAxis.FromJson(…) in src/Sim/Line/TrackAxis.cs:line 251
KOD=134
```

To ta sama rodzina co 6.D229, siedemnaście wierszy dalej w tym samym pliku: tamto
było o **parsowaniu** (`:234`), to jest o **polu** (`:251`).

## 2. Trzy osłony składają się, a nie zastępują

Konflikt z 6.D229 na `src/Sim.Runner/Program.cs` miał kształt „albo–albo": gałąź
6.D233 chciała `FromFile(path, JsonDocument.Parse)`, a `main` po 6.D229 miał
`JsonText.Parse(text, opis)`. **Wybranie którejkolwiek strony gubiło jedną osłonę.**
Złożone są trzy, bo każda łapie inne wejście:

| osłona | skąd | co łapie | co dokłada do komunikatu |
|---|---|---|---|
| `FromFile` | 6.D233 | — | **ścieżkę pliku** (jedyne miejsce, które ją zna) |
| `JsonText.Parse` | 6.D229 | zepsutą **składnię** | polski wiersz odmowy |
| `RequiredField` | 6.D233 | brak **pola** | nazwę pola i opis właściciela |

Zmierzone na CLI po złożeniu, cztery wejścia:

```
zepsuta składnia  BŁĄD: /tmp/…/zly.json: oś trasy nie jest poprawnym JSON-em: …   KOD=1
brak pola         BŁĄD: /tmp/…/pusty.json: oś nie ma wymaganego pola 'points'      KOD=1
manifest bez pola BŁĄD: /tmp/…/pusty.json: manifest chunków nie ma pola 'axis_length_m'  KOD=1
droga POPRAWNA    [OŚ] L1_A: punktów źródłowych=447 …                              KOD=0
```

**Trzeci wiersz jest poprawką z pomiaru, nie z projektu.** Przy odczycie pola stojącym
OBOK `FromFile`, a nie wewnątrz, komunikat gubił ścieżkę: `--manifest <plik {}>` mówiło
„manifest chunków nie ma wymaganego pola", a `--axis <ten sam plik>` nazwę pliku
podawało. Dwa komunikaty o tej samej klasie błędu, różniące się tym, czy da się
znaleźć winny plik. Odczyt przeniesiony do wnętrza osłony.

## 3. ZAWĘŻENIE ZAKRESU — piąty czytnik zostaje nietknięty

Pole „Wejście" wymienia pięć czytników. Osłonięte są **cztery**;
`src/Game/Assets/ChunkManifest.cs` (24 gołe odczyty) **zostaje**.

Powód jest zmierzony, nie ostrożnościowy: ten plik leży w `src/Game/`,
a `tests/Game.Tests/UiTextTests.cs` odtwarza tam pomiary 6.D173, 6.D181 i 6.D188 nad
**dzisiejszym** korpusem `src/Game/`. Osłonięcie tego jednego pliku zapala **sześć**
tych odtworzeń. Po wyjęciu `src/Game/` z zakresu `Game.Tests` daje **318/318**.

Zawężenie jest **strzeżone, nie deklarowane** (6.D243: lista wyjątków, której nikt nie
sprawdza, jest napisem): wpis stoi w `POZOSTALE_GOLE` **z liczbą 24**, a zbiór
porównywany jest w OBIE strony — osłonięcie tych odczytów bez zdjęcia wpisu zapali
bramkę tak samo, jak zapaliłby ją nowy goły odczyt gdzie indziej.

## 4. Trzy z sześciu to zwykłe zapadki, nie odtworzenia — i to zmienia rozmiar sprawy

Pomiar tej pozycji mówił o „sześciu zamrożonych odtworzeniach". Diff z commitem, na
którym liczby przypięto (`7771af3`), pokazuje co innego:

| stała | wtedy | dziś | co to jest |
|---|---|---|---|
| `LiteralowWZasieguBramki` | 480 | 574 | zapadka, rutynowo podnoszona |
| `PozycjiStaregoCzytnika` | 521 | 615 | zapadka, rutynowo podnoszona |
| `LiteralowDotknietychZdejmowaniem` | 335 | 394 | zapadka, rutynowo podnoszona |
| `ZgloszenWaskichWierszami` | **116** | **116** | odtworzenie — nie ruszone ani razu |
| `ZgloszenWaskichCalymPlikiem` | **104** | **104** | odtworzenie — nie ruszone ani razu |
| `WKontekscieCzytaniaJson` | **18** | **18** | odtworzenie — nie ruszone ani razu |

Trzy pierwsze podnosiło samo 6.D229 cztery godziny wcześniej. **Zamrożone są trzy,
nie sześć**, i tylko przy jednym z nich stoi zakaz poprawiania liczby.

## 5. WYNIK NEGATYWNY: migawka korpusu NIE przywraca przypiętych liczb

Decyzja właściciela brzmiała „zamrozić korpus w pliku-migawce". **Wykonane i zmierzone —
nie działa**, i to jest wynik warty zapisania, bo zamyka drogę, która wygląda na oczywistą.

Migawka zbudowana z `src/` na commicie pomiaru, **sprawdzona bajt w bajt** (22 pliki
`src/Game/`, zero różnic wobec `git cat-file`). Wynik: `ZgloszenWaskichWierszami` daje
**108** zamiast przypiętych **116**. Bez migawki, na dzisiejszym korpusie — 120.
Przypięta wartość leży **między** nimi.

Sprawdzone i **wykluczone** jako przyczyna, każde osobno:

- **Korpus** — `src/` jest IDENTYCZNY na 6.D173, 6.D186 i 6.D188 (`git diff --name-only`
  daje zero plików). Jedna migawka pokrywa wszystkie trzy pomiary.
- **Zbiór plików** — sonda w worktree na `7771af3` daje `ZrodlaGry().Count == 21`;
  migawka daje 21, nazwa w nazwę.
- **Każdy czytnik w łańcuchu** — `ZrodlaGry`, `ZgloszeniaWaskie`, `RozbiorJson`,
  `SlowaWierszPoWierszu`, `SlowaWKodzie`, `Literaly`, `SciezkaWezla`, `WzorzecSlowa`,
  `NazwyKlawiszy`, `BezJednostek`, `BezDziur` — wszystkie **bajtowo identyczne**
  z wersją z tamtego commita.
- **Katalog `UiText`** — urósł z 29 do 57 kluczy, a `SlowaWKodzie` odsiewa literały
  obecne w `UiText.Keys`. Wyglądało to na przyczynę i **nie jest**: z 28 nowych kluczy
  **ZERO** przechodzi wąską regułę `^[a-z_][a-z0-9_]*$`, więc żaden nie mógł wypaść
  z tej liczby.

Test przechodzi na swoim commicie (116) i nie przechodzi tu przy identycznych —
o ile umiem je zmierzyć — wejściach. **Przyczyna pozostaje nieustalona**, i dlatego
zawężenie zakresu z §3 jest tymczasowe, a nie rozstrzygnięciem. Migawka **nie wchodzi**
do tej gałęzi: 0,9 MB danych, które nie robią tego, po co powstały, byłoby ciężarem,
a nie zabezpieczeniem.

## 6. Kontrole

| mutacja | przewidziane | zmierzone |
|---|---|---|
| CLI na `{}` przed łatką — **konfiguracja, DLA KTÓREJ pozycja powstała** | kod 134, stos | **KOD=134**, `KeyNotFoundException`, `TrackAxis.cs:251` |
| CLI na `{}` po łatce | polska odmowa, kod 1 | **KOD=1**, `oś nie ma wymaganego pola 'points'` |
| **kontrola DODATNIA** — droga poprawna | zielone, kod 0 | **KOD=0**, `[OŚ] L1_A: punktów źródłowych=447 …` |
| osłonięcie `ChunkManifest.cs` (zawężenie cofnięte) | czerwone | **6 czerwieni** w `Game.Tests` |
| `src/Game/` poza zakresem | `Game.Tests` zielone | **318/318** |

Dwa wzorce przypięte w `UiTextTests.cs` wskazywały inicjator `root.GetProperty(`
i `element.GetProperty(`, które ta pozycja zmienia na `RequiredField`. Zaktualizowane —
deklaracja nie zniknęła i nie podwoiła się, zmienił się wyłącznie inicjator, a typ
zmiennej jest ten sam. To jest odpowiedź, której żąda komunikat tamtej bramki.

## 7. Zapadki

`ASERCJI_RAZEM` **3203**, `Z_KOMUNIKATEM_RAZEM` **1756**, piny **481/293/285**,
literały `src/` **1409/489**, literały `tests/` **4641**, `MODULOW_W_CALYM_DRZEWIE`
i `BAJTKOD_PO_COMPILEALL_PLIKI` o jeden (nowy moduł), `README` 58 → **59** plików
`.cs` w `src/Sim/`. Wszystkie przeliczone z drzewa — łatka mierzyła bazę sprzed
pięciu scaleń i ani jedna jej liczba nie była dziś prawdziwa.

`ZAPADEK_RAZEM` **bez zmian**: bramka stoi na ZBIORZE `{plik: liczba}` porównywanym
w obie strony, a nie na progu `MIN_`/`MAX_`, więc rejestr zapadek jej nie widzi
i widzieć nie ma po co.

## 8. Czego NIE zrobiono

- **`ChunkManifest.cs`** — §3. Idzie do kolejki razem z pytaniem o odtworzenia.
- **`VehicleRegistry.cs` i `ProtectionMode.cs`** (8 i 7 gołych odczytów) — czytają
  ground truth **osadzony w assembly**, nie plik gracza; brak pola jest tam usterką
  budowy, a polska odmowa byłaby skierowana do nikogo.
- **Zmiany w `tests/Game.Tests/UiTextTests.cs` poza dwoma wzorcami** — odtworzenia
  zostają nietknięte, bo ich liczb nie wolno poprawiać, a przyczyny rozbieżności
  nie ustalono.

## 9. Co zauważone przy okazji, nietknięte

- **`CbtcTestArea.FromJson` nie ma w `src/` ani jednego wołającego** — typ publiczny
  bez produkcyjnego użytkownika. To 6.D234.
- **Trzynasty odczyt w `CbtcTestArea.cs` stoi w dziurze interpolacji** (`$"…{root
  .GetProperty(…)}"`). Skan liczący całą interpolację za napis daje 12 zamiast 13;
  czytnik tej bramki dziury zostawia, bo **są kodem**, i ma na to kontrolę przyrządu.
