# 6.D186 — trzynastka kluczy JSON-a: droga zmierzona, liczba poprawiona z 31 na 18

**13.09.2026**, na `37ce503`. Wejście: `reports/6d181-dziewiecdziesiat-nazw-w-umowie.md` §3,
`reports/6d180-jeden-napis-wielowierszowy.md` §2 i §8, `src/Game/FirstRun.cs`,
`tests/Game.Tests/UiTextTests.cs`.

## 1. Czego pozycja żądała

6.D181 §3 zapisało, że wśród 90 nazw stoi **„13 kluczy JSON-a, który program WYPISUJE"**,
i wyprowadziło stąd **„rodzina JSON-a liczy 31, nie 18"**. 6.D180 §8 pokazało, że nazwy,
które tamten raport wymienia, pochodzą z **jednego** napisu surowego — ale zapisało też
wprost: *„Czego NIE twierdzę: że 6.D181 liczyło wierszami. Jakim dokładnie skanem doszło
do swojej trzynastki, nie jest zmierzone"*. Ta pozycja miała tę granicę zdjąć.

## 2. Droga jest ZMIERZONA, a nie uprawdopodobniona

Pomiar kodem bramki (`SlowaWKodzie`, `SlowaWierszPoWierszu`), wąska reguła
`^[a-z_][a-z0-9_]*$` z 6.D173:

| | całym plikiem | wiersz po wierszu |
|---|---:|---:|
| zgłoszeń wąskiej reguły | **96** | **108** |
| w kontekście czytania JSON-a | 18 | 18 |
| poza nim | 78 | **90** |
| o kształcie klucza wypisywanego | **1** | **13** |

6.D181 §3 pisze: *„Wyszło 18 ze 108"* i wymienia 90 oraz 13. **Wszystkie cztery liczby
stoją po stronie WIERSZOWEJ i po żadnej innej** — liczba 108 na drodze całoplikowej nie
powstaje w ogóle, bo tam jest ich 96. Droga jest więc rozstrzygnięta: **6.D181 liczyło
wiersz po wierszu.**

Odtworzenie jest **co do jedynki** i to było żądanie pola „Weryfikacja": przyrząd, który
nie odtwarza liczb poprawianego pomiaru, mierzy co innego i nie ma prawa go korygować.

## 3. Trzynastka odtwarza się RAZEM z własnym trafieniem fałszywym

Trzynaście zgłoszeń drogi wierszowej to:

```
platforms  engine  resolution  view  steps  scene  vertices  faces
platforms  slabs   slabs       train bodies
```

Dwanaście z nich to kawałki napisu metadanych zrzutu (`FirstRun.cs:2232`), rozciętego
przez podział na wiersze. **Trzynaste — `platforms` z wiersza 883 — jest nazwą argumentu
wiersza poleceń**, `Argument("platforms")`, złapaną tylko dlatego, że gdzie indziej
w tym samym pliku stoi klucz `"platforms":`. W tabeli 6.D181 ta sama pozycja należy do
wiersza „argument wiersza poleceń | 39". **Kolizja nazw, policzona dwa razy.**

Że odtworzenie trafiło w ten sam zbiór, a nie w inny o tej samej liczności, sprawdza
osobna asercja żądająca obecności tego właśnie trafienia.

Godne odnotowania, bo tłumaczy, czemu `godot` w tabeli 6.D181 stoi osobno („wartość
w JSON-ie | 1"): sito `"nazwa":` go nie łapie — w napisie stoi `"engine": "godot"`, więc
`godot` jest wartością, nie kluczem. Zgodność jest tu ścisła, a nie przybliżona.

## 4. ROZSTRZYGNIĘCIE: 31 → 18

6.D180 rozstrzygnęło, że poprawne jest liczenie **całym plikiem** — napisu
wielowierszowego nie da się czytać wierszami, bo rozcina go sam podział na wiersze.

Tą drogą zgłoszeń o kształcie klucza wypisywanego jest **jedno**, a i ono kluczem nie
jest: to ten sam `Argument("platforms")`. **Rodzina „klucz JSON-a wypisywanego" liczy
wśród zgłoszeń ZERO.** Do osiemnastu nie dochodzi więc nic.

**Rodzina JSON-a liczy 18** — dokładnie tyle, ile podało 6.D173. Poprawka 6.D181 była
sama błędna.

## 5. Teza ZOSTAJE, ale jej powód jest inny

Teza 6.D181 brzmiała: *„deklaracja była węższa niż rodzina"*. **Zostaje prawdziwa.**
Przyrząd melduje „kontekst JSON-a", a sprawdza wyłącznie CZYTANIE, choć program JSON
również wypisuje — i niemało: napis metadanych niesie **31 różnych kluczy w 35
wystąpieniach**.

**Zmienia się POWÓD, dla którego ich nie widać, i to jest główny wynik tej pozycji.**
Nie chodzi o regułę kontekstu. Te 31 kluczy **nie jest zgłoszeniami żadnej reguły**:
cały napis metadanych jest JEDNYM literałem długości 1697 znaków i czterdziestu wierszy,
a taki literał kształtu identyfikatora nie ma. **Poszerzenie reguły z „czytania" na
„czytanie i wypisywanie" znalazłoby ZERO, a nie trzynaście.**

Z 31 nazw kluczy w korpusie zgłoszeń padają **dwie** — `platforms` i `view` — i obie
jako nazwy argumentów wiersza poleceń (`Argument("platforms")` w `FirstRun.cs`,
`Argument(arguments, "view")` w `RunPlan.cs`). Żadna jako klucz.

**Dwie trzydzieści jedynki, bez związku.** Kluczy w napisie jest 31, a 6.D181 policzyło
rodzinę JSON-a też na 31 (18 + 13). Zbieżność jest przypadkowa — tamta liczba powstała
z kawałków tego samego napisu policzonych po wierszach, a nie z jego kluczy — i stoi
w bramce wypisana, żeby nikt nie wyprowadził z niej wniosku.

## 6. Znalezione po drodze: z trzech markerów „kontekstu JSON-a" niesie liczbę JEDEN

Kontekst czytania 6.D173 to trzy markery. Ich udział, zmierzony osobno:

| marker | zgłoszeń |
|---|---:|
| `GetProperty` | **18** |
| `GetString` | 8 |
| `RootElement` | **0** |

`GetProperty` daje sam całą osiemnastkę. Osiem `GetString` to te same osiem —
`chunk.GetProperty("id").GetString()` ma oba markery w jednym wierszu. `RootElement`
pada w `src/Game/` raz, jako `var root = document.RootElement;`, a w tym wierszu nie ma
ani jednego literału.

**„Kontekst JSON-a" jest więc w praktyce wierszem z `GetProperty`.** Nie jest to powód,
by dwa pozostałe markery usunąć — jutro plik może być czytany przez `RootElement` wprost
— ale jest powodem, by ich bezczynność była **widoczna**, a nie domniemana. Stąd bramka
z tabelą udziałów.

## 7. Sześć kontroli negatywnych, baza 4/4, ani jedna zielona na końcu

| kontrola | podstawienie | wynik |
|---|---|---|
| KN-1 | czytnik wierszowy podmieniony na całoplikowy w bramce odtworzenia | 3/4 |
| KN-2 | `RootElement` zdjęty z listy markerów | 3/4 — **za drugim podejściem** |
| KN-3 | sito kształtu klucza bez dwukropka | 2/4 |
| KN-4 | jeden klucz (`chunks_declared`) zdjęty z napisu metadanych | 3/4 |
| KN-5 | nazwa argumentu `platforms` zmieniona na `perony` | **1/4** |
| KN-6 | wąska reguła poszerzona o wielkie litery | 2/4 |

### KN-2 wyszła ZIELONA za pierwszym razem i powiedziała prawdę o mojej bramce

Zdjęcie `RootElement` z listy markerów nie ruszało żadnej liczby, więc marker dało się
usunąć **bez jednego czerwonego testu**. Przyczyna z katalogu zielonych kontroli jest tu
czwarta — **mechanizm naprawdę bezczynny**: marker nie łapie dziś ani jednego zgłoszenia,
więc jego obecność albo nieobecność nie ma na co wpłynąć. Nie jest to ani podstawienie,
które nie weszło (diff to pokazał), ani kontrola pusta z konstrukcji, ani tautologia —
KN-1 i KN-3 na tej samej bramce idą czerwono.

Naprawą nie było usunięcie markera, tylko **zmierzenie i przybicie jego udziału**:
tabela `UdzialMarkerow` liczy każdy marker z listy `MarkeryCzytaniaJson` z osobna, więc
zdjęcie któregokolwiek zmienia długość tabeli i zapala test. Po tym KN-2 jest czerwona.

## 8. Czego świadomie nie zrobiłem

- **`SlowaWKodzie`, `BezDziur` ani żadnego sita nie tknąłem** — pole „Poza zakresem".
- **`src/Game/` nie zmieniłem** — to samo pole. Napis metadanych zostaje jaki jest;
  pozycja pytała, ile jest kluczy, a nie jak je zapisać.
- **Raportu 6.D181 nie przepisałem** — pole „Poza zakresem" mówi wprost, że miejscem
  korekty jest wpis w `docs/TASKS.md`. Wpis 6.D181 dostał jedno zdanie odsyłające tutaj,
  żeby liczba 31 nie stała tam bez znaku.

## 9. Zauważone po drodze, nie tknięte

- Wąska reguła 6.D173 (`^[a-z_][a-z0-9_]*$`) do 13.09.2026 **nie stała w żadnym pliku** —
  żyła wyłącznie w treści raportów. Każde jej odtworzenie było więc przepisywaniem wzorca
  z tekstu, czyli tą samą reimplementacją, która przy 6.D179 dała **446** zamiast 348.
  Teraz stoi jako stała `WaskaRegulaKsztaltu`.
- Sito „kształt klucza" (`"nazwa":` gdziekolwiek w pliku) jest **plikowe, nie
  miejscowe** — dlatego łapie `Argument("platforms")`. Sito miejscowe wymagałoby wiedzy,
  w którym literale stoi zgłoszenie, a tej `SlowaWKodzie` nie zwraca. Zostawione jako
  jest i opisane, bo jego wada jest tu **treścią pomiaru**, a nie przeszkodą.
