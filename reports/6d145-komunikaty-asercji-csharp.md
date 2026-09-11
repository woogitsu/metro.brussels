# 6.D145 — asercje C# bez komunikatu: 1381 z 2593, i trzecia klasa, która nazywa niewiedzę

**11.09.2026**, na `145c419`. Wejście: `tools/tests/csharp_assertions.py`,
`tools/tests/csharp_pins.py`, `tests/Sim.Tests/`, `tests/Game.Tests/`.
Pozycja: bramka liczy asercje bez komunikatu po stronie Pythona i zatrzymuje się
na granicy języka; po stronie C# nie liczył ich nikt.

## 1. Liczba, o którą pozycja prosiła

```
[KOMUNIKATY C#] tests/Game.Tests bez=350  z=429  nierozstrzygnietych=11 razem=790
[KOMUNIKATY C#] tests/Sim.Tests  bez=1031 z=711  nierozstrzygnietych=61 razem=1803
[KOMUNIKATY C#] RAZEM            bez=1381 z=1140 nierozstrzygnietych=72 razem=2593
```

**1381 asercji bez komunikatu w 49 plikach.** Zapadka per plik, w obie strony — wpis
wolno obniżyć, podnieść nie wolno, plik spoza listy ma mieć zero, a wpis, który zszedł
do zera, ma z listy wypaść.

Dla porównania strona pythonowa po 6.D144: **2255** asercji bez komunikatu. Razem
w repozytorium jest ich więc **3636**, a nie 2255 — i to jest pierwszy wynik tej
pozycji: granica języka ukrywała 38 % całości.

## 2. Trzy klasy, nie dwie, i trzecia jest treścią

Komunikat C# stoi jako **ostatni** argument i nie ma własnej składni — rozpoznaje się
go po TYPIE. Typu identyfikatora nie da się odczytać bez sprawdzacza typów, którego
to repozytorium nie ma i mieć nie będzie (ta sama granica, którą 6.D141 zapisało przy
rozwijaniu stałych).

| klasa | ile | skąd wiadomo |
|---|---:|---|
| **bez komunikatu** | 1381 | brak argumentu ponad obowiązkowe, albo trzeci argument rodziny `AreEqual` jest literałem liczbowym (tolerancja) |
| **z komunikatem** | 1140 | ostatni argument jest literałem napisowym, albo stoi w pozycji, w której MSTest ma **wyłącznie** `string message` |
| **nierozstrzygnięte** | 72 | `Assert.AreEqual(a, b, x)` z `x` będącym wyrażeniem — `x` może być tolerancją albo komunikatem |

**Trzy klasy sumują się do 2593 i jest to przybite**, bo inaczej asercja, której czytnik
nie rozumie, wypadłaby między klasy, a zapadka na „bez komunikatu" spadałaby razem
z jego niewiedzą i czytałaby się jako postęp. KN-5 mierzy dokładnie ten scenariusz.

**Dlaczego 122 wyrażeń jednak policzono jako komunikat.** Poza rodziną `AreEqual`
MSTest ma w pozycji nadmiarowej wyłącznie `string message` — więc wyrażenie, które
się KOMPILUJE, jest tam napisem. To jest ta sama droga rozumowania, którą 6.D141
zapisało dla `Assert.AreEqual(int, int, double)`: przeciążenia nie ma, więc taki
pin by się nie skompilował.

**Czego nie policzono, choć dałoby się częściowo.** Z 72 nierozstrzygniętych **30**
dałoby się rozstrzygnąć regułą na PIERWSZY argument (tolerancja wymaga, żeby oba
porównywane argumenty były zmiennoprzecinkowe; literał napisowy albo całkowity ją
wyklucza), a 2 wskazują na tolerancję. Nie zrobiono tego: reguła na argument
całkowity nie jest szczelna (`int` konwertuje się do `double`), a zamiana
zadeklarowanej niewiedzy na cichą heurystykę jest gorsza od niewiedzy. Zostaje
do osobnej pozycji.

## 3. Cięcie argumentów musiało dostać własną funkcję

`argumenty` z 6.D141 liczy głębokość wyłącznie po nawiasach okrągłych, więc
`CollectionAssert.AreEqual(new[] { "a", "b" }, x, "powód")` rozpada się jej na cztery
argumenty zamiast trzech. Doszła `argumenty_z_nawiasami`, licząca też `[` i `{`.

**Tamta została nietknięta i to jest zmierzone, nie założone**: na 2593 wywołaniach
obie funkcje różnią się w **28** i wszystkie 28 to `CollectionAssert.*`. Na
`Assert.AreEqual` — jedynej rodzinie, którą czyta `piny_liczbowe` — różnicy nie ma
ani jednej, a `piny` w ogóle nie tnie argumentów (patrzy na znak tuż za `(`).
**Liczby 6.D141 są więc tą poprawką nieruszone i nie trzeba ich przeliczać.**

Na klasę komunikatu te 28 wywołań wpływa w **14** przypadkach — KN-4.

Przy okazji bramka `test_zaden_rekurencyjny_glob_nie_omija_wspolnego_odsiania`
zapaliła się na moim `glob.glob(..., recursive=True)` i czytnik chodzi teraz po
`tree_walk.znajdz`, czyli po tym samym odsianiu `.gitignore` co reszta drzewa.
Na liczbach nie zmieniło to **nic** — 790 i 1803 przed podmianą i po niej — bo pod
`tests/` nie ma generowanych `.cs`; podmiana jest więc zachowaniem, a nie poprawką,
i gdyby kiedyś przestała być, zauważy to zapadka z sekcji 1.

## 4. Kontrole negatywne

Baza: **25/25** na parze modułów. Po każdej `cp` z kopii i `md5sum -c: OK` na czterech
plikach.

| | mutacja | wynik | co mówi |
|---|---|---|---|
| KN-1 | asercja bez komunikatu dopisana do pliku **z listy** | **23/25** | `[('BrakingTests.cs', 64, 63)]` — zapadka bije w górę |
| KN-2 | to samo w pliku **spoza listy** | **23/25** | `[('HudLayoutTests.cs', 1)]` — nowy plik zaczyna od zera |
| KN-3 | klasyfikator przestaje odróżniać tolerancję od komunikatu | **22/25** | **1381 → 1116**: 265 asercji zmieniłoby klasę bez ani jednego dopisanego zdania |
| KN-4 | cięcie po samych nawiasach okrągłych | **23/25** | **1381 → 1367**: 14 asercji źle zaklasyfikowanych |
| KN-5 | `StringAssert.Contains` zdjęte z tabeli arności | **22/25** | **2593 → 2377**: 216 asercji znika po cichu, a wpis jednego pliku spada do zera i czyta się jako postęp |

**KN-3 jest tą kontrolą, o którą prosiło pole „Skończone, gdy"**, i podaje cenę
pomyłki liczbą: czytnik liczący przecinki zamiast rozpoznawać kształt zbiłby zapadkę
o **265** pozycji, nie dopisując ani jednego komunikatu.

**KN-5 jest powodem, dla którego trzecia klasa i tabela arności istnieją.** Zdjęcie
jednej nazwy z tabeli usuwa 216 asercji z pomiaru — i bez `test_tabela_arnosci_…`
wyglądałoby to jak praca, którą ktoś wykonał.

## 5. Czego nie zrobiono

- **Nie dopisano ani jednego komunikatu do asercji C#** — pole „Poza zakresem" mówi
  to wprost. Ta pozycja miała je POLICZYĆ.
- **Nie ruszono `argumenty` ani liczb 6.D141** — patrz sekcja 3, różnica jest
  zmierzona i zerowa dla tamtej rodziny.
- **Nie rozstrzygnięto 72 nierozstrzygniętych** — patrz sekcja 2; potrzeba do tego
  typów, a nie kształtu.
- **Nie porównano kosztu z 6.D144.** Tamta pozycja zmierzyła koszt dopisania
  komunikatu w Pythonie (2,68 wiersza na asercję); czy w C# jest podobnie, nie
  wiadomo, a przeniesienie liczby przez granicę języka byłoby dokładnie tym, co
  ta pozycja tropi.
