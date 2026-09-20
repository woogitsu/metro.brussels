# 6.D317 · Siedemdziesiąt jeden procent populacji wpada do klasy „reszta" — a kontrola przyrządu mierzy INNĄ POPULACJĘ niż pytanie

**Data:** 20.09.2026 · **Gałąź:** `claude/sharp-ramanujan-jdr51o` · **Baza:** `7d679f4`

6.D307 §7 zapisało, że w prozie pod `tools/` stoi 143 nazwy PascalCase w grawisach,
z czego 23 to dzisiejsze typy publiczne `src/`. Ta pozycja rozbija tę populację na
klasy rozłączne i sprawdza — a nie zakłada — że sumują się do całości.

Czytnik prozy jest **pożyczony**: `proza` z `test_message_claims.py`; typy publiczne
czytam `typy_publiczne(przedrostek="src/")`, **nie domyślnym zasięgiem**, bo tak każe
pole i tak rozstrzygnęło 6.D307 §1.

---

## 1. Populacja: 136, a nie 143 — i nie uzgadniam tej różnicy

```
NAZW PascalCase w grawisach w prozie tools/:  136
wystapien razem (para nazwa-plik):            202
typow publicznych src/ (przedrostek src/):    156
nazw pythonowych zadeklarowanych pod tools/: 4358
```

**Mój kształt PascalCase wymaga co najmniej DWÓCH członów** — `[A-Z][a-z0-9]+`
powtórzone — żeby `Data`, `Sim` czy `OK` nie wchodziły do populacji jako „nazwy
typu". 6.D307 podało 143; **różnicy siedmiu nie uzgadniam**, bo uzgadnianie
polegałoby na rozciąganiu mojego kształtu do cudzej liczby. Podaję swój kształt
jawnie, żeby różnicę dało się sprawdzić bez czytania mojego kodu.

## 2. Klasy z pola, w kolejności spisanej PRZED pomiarem

Kolejność jest treścią: pierwsza pasująca wygrywa, i zapisałem ją w pliku definicji,
zanim uruchomiłem czytnik — dokładnie dlatego, że przy 6.D315 kolejność klauzul
w implementacji rozjechała się z kolejnością w zapisie.

```
typ src/                      22
nazwa pythonowa tools/         4
typ frameworka .NET           14
sciezka albo nazwa pliku       0
reszta                        96
                             ---
SUMA                         136   = populacja    ZGADZA SIE
```

**Klasy sumują się do populacji** — pole żądało tego sprawdzenia, nie założenia,
i sprawdzenie wychodzi.

**Klasa „ścieżka albo nazwa pliku" jest PUSTA.** Pole wymienia ją jako jedną z pięciu
i ostrzega, że „grawis stoi też wokół ścieżek plików" — w tej populacji nie stoi ani
razu, bo ścieżka zawiera kropkę albo ukośnik, a mój kształt PascalCase ich nie
przepuszcza. Jest to klasa pusta **z konstrukcji mojego sita**, nie z własności
drzewa, i mówię to wprost zamiast raportować zero jako znalezisko.

## 3. GŁÓWNE ZNALEZISKO: „reszta" to 96 ze 136, czyli 71 % — więc ją rozbijam

Mój warunek obalenia, spisany przed pomiarem, brzmiał: **„jeśli »reszta« przekroczy
połowę populacji, rozbijam ją na podklasy i podaję ich liczności, bo jedna liczba
bez treści nie jest odpowiedzią na pytanie pola"**. Przekroczyła. Rozbijam:

```
skladowa albo metoda w `src/`/`tests/` (nie typ publiczny)   31
wyjatek albo typ WBUDOWANY Pythona                           19
reszta reszty                                                15
identyfikator POLSKI tego projektu                           14
klasa testowa C# (przyrostek Tests)                          13
wezel `ast` biblioteki standardowej                           4
                                                            ---
SUMA PODKLAS                                                 96   ZGADZA SIE
```

### 3.1 Największa podklasa nie jest typem — jest SKŁADOWĄ

Trzydzieści jeden nazw to **metody i właściwości**, nie typy: `AreEqual`,
`CollectionAssert`, `GetNode`, `GetProperty`, `ParseArguments`, `ToString`,
`TryGetProperty`, `RootElement`, `IntValue`, `TakeControl`, `WriteProvenanceBeside`.
Pole pyta o „nazwy PascalCase", a C# pisze PascalCase **także dla metod** — więc
populacja z definicji miesza dwie rzeczy, które starzeją się inaczej: typ znika przy
usunięciu klasy, metoda przy zmianie jednej sygnatury.

### 3.2 Dziewiętnaście nazw to WBUDOWANE wyjątki Pythona

`ValueError`, `KeyError`, `AssertionError`, `SystemExit`, `ZeroDivisionError`
i czternaście innych. Nie starzeją się **wcale** — są częścią języka. Bramka na
cytatach, gdyby powstała, musiałaby je odsiać, bo inaczej pilnowałaby CPythona.

### 3.3 Czternaście to polskie identyfikatory tego projektu

`CzlonWyrazenia`, `KodBezKomentarzy`, `KorzenRepozytorium`, `LiteralowWZasieguBramki`,
`PostacieLiteralu`, `TylkoKod` — nazwy pisane PascalCase po polsku, w prozie, jako
nazwy pojęć wprowadzanych przez ten projekt. Nie są ani typem, ani metodą, ani
nazwą pythonową; są **terminami**.

## 4. Mój klasyfikator pomylił się w tej samej podklasie i mówię to zamiast poprawić

Reguła „polski identyfikator" ma dwa człony: znak diakrytyczny **albo** przedrostek
z listy, którą spisałem. Przedrostki `Minimum` i `Plan` wciągnęły trzy nazwy
**angielskie**:

```
MinimumSwitches          — angielskie
PlanLimitKmh             — angielskie
MinimumZgloszenToString  — mieszane, polsko-angielskie
```

Jest to **ten sam błąd przedrostka**, który 6.D312 zmierzyło na `BLENDER_BIN`
i który zapisałem tam jako powtórzenie usterki 6.D310. **Trzeci raz w tej sesji.**
Nie poprawiam liczby 14 — jest tym, co dała reguła spisana przed pomiarem — ale
mówię, że dwie z czternastu są angielskie, a jedna mieszana.

Osobno: `PascalCase` stoi w podklasie „reszta reszty" i **nie jest identyfikatorem
niczego** — jest nazwą konwencji zapisu, cytowaną w prozie o tej konwencji. Sito
składniowe nie odróżnia nazwy rzeczy od nazwy pojęcia o nazwach.

## 5. KONTROLA PRZYRZĄDU: NIE ODTWARZA SIĘ, i przyczyna jest w POPULACJI

Pole żądało, by `FirstRun` wyszedł jako typ `src/` **i w piętnastu plikach prozy**.

```
klasa:         typ src/        <- zgadza sie
plikow prozy:  1               <- 6.D307 zmierzylo pietnascie
```

Zmierzone wprost:

```
plikow pod tools/, ktore w OGOLE wymieniaja FirstRun:   16
z tego z `FirstRun` W GRAWISACH:                         1
z tego w PROZIE wg czytnika `proza`:                     1
```

**Piętnastka z 6.D307 liczyła wzmianki gdziekolwiek w pliku, a nie nazwy w grawisach
w prozie.** To są dwie różne populacje i obie liczby są prawdziwe o swoich
populacjach. Kontrola postawiona przez pole **nie da się spełnić przyrządem, którego
to samo pole żąda** — bo żądany przyrząd (`proza` plus grawis) widzi jeden plik,
a liczba kontrolna pochodzi z szerszego skanu.

Mówię to wprost zamiast raportować kontrolę jako niezdaną i przechodzić dalej: jej
litera jest niespełnialna, a jej treść — „czy czytnik widzi `FirstRun` jako typ
`src/`" — **jest spełniona**.

**To trzeci raz w tej sesji, gdy kontrola przyrządu nie odtwarza się z powodu
jednostki albo populacji**, nie z powodu usterki: 6.D312 (pliki wobec węzłów),
6.D316 (nazwa kolidująca z nazwą gałęzi) i teraz 6.D317.

## 6. Przewidywania spisane PRZED pomiarem

| # | przewidywanie | wynik |
|---|---|---|
| R1 | klasa „typ .NET" liczniejsza niż „typ `src/`" | **OBALONE** — 14 wobec 22 |
| R2 | „reszta" będzie największa | trafione — 96 ze 136 |
| R3 | luka `143 − 23 − 115 = 5` to nazwy pythonowe `tools/` | **NIEROZSTRZYGALNE** — §6.1 |
| R4 | w „reszcie" będą nazwy z cudzych narzędzi | trafione — §6.2 |
| R5 | kontrola przyrządu odtworzy się | **OBALONE** — §5 |
| R6 | moja zamknięta lista BCL okaże się niewystarczająca | trafione — §6.3 |

### 6.1 R3 jest nierozstrzygalne i tak je zapisuję, a nie jako pudło

Postawiłem je na arytmetyce z cudzych liczb (143 − 23 − 115), a moja populacja
liczy **136**, nie 143. Luki, o którą pytałem, **nie ma w mojej populacji**, więc
przewidywanie nie ma się o co oprzeć. Zapisałem przed pomiarem, że R3 nie jest
niezależne — i okazało się gorzej niż zależne: jest niesprawdzalne.

### 6.2 R4 trafione: cudze narzędzia w „reszcie"

`SafeLoader` (PyYAML), `GodotSharp` i `GetNode` (Godot), `EmbeddedResource`,
`TargetFramework`, `GenerateDocumentationFile` (MSBuild), `TemporaryDirectory`
i cztery węzły `ast` (biblioteka standardowa), `DirectoryInfo` (.NET BCL).

### 6.3 R6 trafione po raz siódmy — i to już nie jest przewidywanie, tylko wzór

Moja zamknięta lista BCL miała czterdzieści nazw i **nie objęła** `DirectoryInfo`,
`SafeLoader`, `TemporaryDirectory`, `MultiPolygon` — wszystkie cztery wpadły do
„reszty reszty". Zamknięta lista zawiodła przy 6.D314 (rzeczowniki), 6.D315 (trzy
wartości klucza) i teraz tutaj.

**Siedem trafień z rzędu na przewidywaniu o mnie samym znaczy, że przestaje to być
przewidywanie.** Zapisuję wniosek: **lista spisana z góry jest w tym projekcie
narzędziem do MIERZENIA WŁASNEJ NIEWIEDZY, a nie do klasyfikowania.** Jej wartość
leży w tym, ile z niej wypadnie, a nie w tym, ile złapie.

## 7. Czego świadomie nie zrobiono

- **Nie poprawiono czyjejkolwiek prozy** ani jednego cytatu.
- **Nie postawiono bramki na cytatach.** Pole zabrania, a §3 pokazuje, dlaczego
  byłoby to przedwczesne: 19 nazw z populacji to wbudowane wyjątki Pythona, które
  nie starzeją się wcale, a 31 to składowe, które starzeją się inaczej niż typy.
- **Nie zmieniono `RDZEN` ani domyślnego przedrostka `typy_publiczne`.**
- **Nie uzgodniono populacji 136 ze 143 z 6.D307** — kształt PascalCase podaję
  jawnie zamiast rozciągać go do cudzej liczby.
- **Nie poprawiono liczby 14 w podklasie „identyfikator polski"**, choć §4 pokazuje
  w niej dwie nazwy angielskie: jest tym, co dała reguła spisana przed pomiarem.
- **Nie tknięto `src/`** ani `data/`.

## 8. Zauważone przy okazji, nietknięte

**Populacja miesza typy ze składowymi, a pole tego nie rozróżnia.** Trzydzieści jeden
nazw z 96 to metody i właściwości. Każda bramka postawiona na „nazwie PascalCase
w grawisach" pilnowałaby obu naraz, a starzeją się w różnym tempie i z różnych
powodów.

**Czternaście polskich terminów w PascalCase to konwencja, której nie pilnuje nic.**
`KodBezKomentarzy` i `TylkoKod` są nazwami pojęć wprowadzonych przez ten projekt
w prozie bramek; nie mają odpowiednika w kodzie i nie muszą mieć. Ile ich jest poza
tą populacją — w prozie bez grawisów — nie liczyłem.

**Liczba wystąpień (202) jest o 66 większa od liczby nazw (136)**, czyli średnio
1,49 pliku na nazwę. Rozkład tego nadmiaru — czy jest kilka nazw cytowanych
wszędzie, czy wiele cytowanych dwa razy — nie policzyłem; pole prosiło o klasy, nie
o rozkład wystąpień.

## 9. Weryfikacja — rzeczywiste wyjście

```
$ find . -name __pycache__ -prune -exec rm -rf {} +
$ python3 tools/tests/test_all.py
  [DRZEWO] 0 plikow drzewa roboczego poza zasiegiem bramek czytajacych `git ls-files` — 6.D165
  [BAJTKOD] wyczyszczono 1 kat. __pycache__ (1 plikow) pod tools/ — 6.D122
  2664/2664 przeszło
  RAZEM 370.011 s, 2664 testów, 139 modułów
EXIT=0
```

Zero `FAIL`. **Bramki nie przybyło** — pole „Poza zakresem" zabrania stawiania bramki
na cytatach, a §3 pokazuje, dlaczego byłoby to dziś przedwczesne. Bramki dotknięte
tą pozycją przeszły wcześniej osobno — `test_report_hygiene`, `test_backlog`,
`test_field_paths`, `test_report_claims`, `test_docs_map` i `test_message_claims`:
**159/159**.

**Uzupełnienie kolejki było OBOWIĄZKOWE i jest wykonane.** Zapas udokumentowany
zszedł po tej pozycji **do progu dwunastu**, co `CLAUDE.md` §8 traktuje jako wyzwalacz
(precedens 6.D310: 12 = próg → dopisana pozycja). Dopisane **6.D327** i **6.D328**;
zapas wynosi **czternaście**.

**Ósmy pomiar ściany na tym kontenerze w tej sesji:**

```
414,695   418,599   361,079   365,940   364,619   369,370   375,942   370,011
```

Sześć ostatnich mieści się w paśmie 361–376 s. Dane dla 6.D313, nie wniosek.
