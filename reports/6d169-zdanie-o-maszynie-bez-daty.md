# 6.D169 — zdanie o maszynie dostało datę, a przyrząd z pola „Weryfikacja" liczy WIERSZE, nie zdania

**Data:** 18.09.2026 · **Gałąź:** `claude/sharp-ramanujan-jdr51o` · **Baza:** `7c3d2fa`

Pozycja żądała dwóch rzeczy: imiennej listy zdań `docs/23-environment.md` mówiących
o konkretnej maszynie, z werdyktem przy każdym, oraz daty dopisanej przy tym zdaniu,
którego werdykt brzmi „nie niesie". Oba są niżej. Przy okazji wyszło, że **populacja
jest o jedno zdanie większa, niż widzi ją pole „Weryfikacja"**, i że pole
„Skończone, gdy" wpisało jedno zdanie do złej kolumny. Obie rozbieżności są tu
zapisane jako rozbieżności, a nie wciszone poprawieniem pola.

## 1. Co zostało zmienione w dokumencie

Jedno zdanie, w §1.1.1, wiersze 160–162 po zmianie:

```
Tego nie było w opisie pozycji 6.D48 i wyszło z pomiaru. Na tej maszynie — czyli
w kontenerze z 08.09.2026, a nie w dowolnym dzisiejszym —
`/root/.dotnet/dotnet` zgłasza **10.0.400**, a doctor melduje brak:
```

Data **nie jest zgadnięta**. Zdanie weszło commitem `4143e64` z **08.09.2026**
(`6.D48: dokument mówi, GDZIE narzędzia leżą — i pomiar poprawił pozycję dwa razy`),
odczytanym przez `git log -S'zgłasza **10.0.400**' -- docs/23-environment.md`. Ten sam
dzień podaje `reports/6d166-liczby-w-prozie.md` — ale jest tu odczytany z historii,
a nie przepisany z tamtego raportu.

Samej wersji SDK nie ruszono, bo pole „Poza zakresem" mówi o tym wprost: `10.0.400`
i `10.0.401` to dwa kontenery z dwóch dni i po 6.D108 **oba zdania są poprawne
w swoim dniu**.

## 2. Imienna lista — OSIEM zdań, nie siedem

Numery wierszy są dzisiejsze, czyli **po** zmianie z §1. Kolumna „akapit od" podaje
pierwszy wiersz akapitu, bo w tym dokumencie werdykt „niesie datę" rozstrzyga się
w akapicie, nie w wierszu.

| akapit od | zdanie (skrót) | niesie datę | w populacji |
|---|---|---|---|
| 32 | „Ta sekcja powstała 08.09.2026 … Blendera na tej maszynie nie ma" | tak, w zdaniu | tak |
| 85 | „Zmierzone 08.09.2026 w tym kontenerze, na czystym środowisku zmiennych" | tak, w zdaniu | tak |
| 143 | „W tym kontenerze stały dwa, założone ręką 08.09.2026 o 06:07" | tak, w zdaniu | tak |
| 160 | „Na tej maszynie — czyli w kontenerze z 08.09.2026 …" | **tak, od dziś** | tak |
| 255 | „Koszt, zmierzony 03.09.2026 na czystym kontenerze" | tak, w zdaniu | tak |
| 314 | „Zmierzone 03.09.2026 w tym kontenerze" | tak, w zdaniu | tak |
| 451 | „(zmierzone 04.09.2026 na tym kontenerze)" | tak, w zdaniu | tak |
| 474 | „pierwsze uruchomienie na czystej maszynie potrzebuje sieci na `restore`" | **nie** | **nie — maszyna DOWOLNA** |

Werdykt czytnika po zmianie: **osiem** zdań, **jedno** bez daty w akapicie — to ostatnie,
o maszynie dowolnej. Zdań o **konkretnej** maszynie bez daty jest **zero**.

## 3. Rozbieżność pierwsza: `grep -c` liczy wiersze, więc widzi siedem z ośmiu

Pole „Weryfikacja" podaje `grep -nic … = 7` i to się zgadza — ale siódemka nie jest
liczbą zdań. Akapit od wiersza 85 ma sformułowanie **rozcięte przez zawijanie**:

```
 85: **Czym sprawdzić — jedno polecenie na narzędzie.** Zmierzone 08.09.2026 w tym
 86: kontenerze, na **czystym środowisku zmiennych**: `PATH=/usr/bin:/bin`, bez
```

`w tym / kontenerze` stoi po obu stronach końca wiersza, więc dla `grep`, który dopasowuje
w obrębie wiersza, tego zdania **nie ma**. Czytnik składający akapit w jeden płaski
napis widzi je i dlatego mówi osiem.

Zawijania **nie poprawiono**, i to jest wybór. Zszycie tych dwóch wierszy podniosłoby
`grep -nic` do ośmiu, a pole „Weryfikacja" mówi „siedem trafień, jak dziś" — poprawka
przyrządu zapaliłaby więc kryterium, którego pilnuje. Liczbą, która ma nie spaść,
zostaje **7**; liczbą, która opisuje dokument, jest **8**.

Drugi szczegół tego samego przyrządu: wzorzec nie ma granic słowa, więc
`czystym kontenerze` (wiersz 255) trafia w gałąź `tym kontenerze` **wnętrzem wyrazu**.
Zmierzone wprost: `printf 'na czystym kontenerze\n' | grep -c "tym kontenerze"` daje
`1`, a z `\b` przed `tym` daje `0`. Na werdykt to nie wpływa — zdanie i tak jest
o maszynie i i tak niesie datę — ale zgodność pola z czytnikiem jest w tym wierszu
przypadkiem, a nie konstrukcją.

## 4. Rozbieżność druga: pole „Skończone, gdy" pomyliło KOLUMNĘ

Pole wylicza sześć zdań, które „datę niosą już", i wpisuje między nie wiersz 474
z nawiasem: „zdanie o maszynie DOWOLNEJ, nie o konkretnej". Nawias podaje powód
z **innej kolumny** niż nagłówek, pod którym stoi, i pomiar to rozstrzyga: akapit
474–477 daty **nie niesie w ogóle** — ani w zdaniu, ani w akapicie. Poprawny rozkład
tej listy to nie „sześć z datą, jedno bez", tylko **pięć z datą, jedno poza populacją,
jedno bez daty** (plus ósme, którego `grep` nie widział — §3).

Ma to skutek praktyczny, a nie tylko porządkowy: zdanie „pozycja jest skończona, gdy
tych bez daty jest **zero**" w dosłownym brzmieniu nie da się spełnić prawdziwie,
bo jedno zdanie zostanie bez daty na zawsze i **powinno**. Spełniona jest wersja
poprawiona: **zero zdań o konkretnej maszynie bez daty**.

## 5. Dlaczego zdanie o maszynie DOWOLNEJ zostaje bez daty

`Rdzeń w src/Sim/ nie ma zależności NuGet, ale tests/Sim.Tests ma trzy pakiety —
pierwsze uruchomienie na czystej maszynie potrzebuje sieci na restore` nie opisuje
dnia ani kontenera. Opisuje własność drzewa: ile projekt ma pakietów. Dopisanie daty
zawęziłoby zdanie prawdziwe o każdej czystej maszynie do zdania o jednej — czyli
**zepsułoby je**, zamiast je udatować.

Liczba w tym zdaniu została mimo to sprawdzona, bo to jedyna twarda liczba
w zdaniu, które zostawiam nietknięte: `tests/Sim.Tests/Sim.Tests.csproj` ma
**trzy** wiersze `PackageReference` (`Microsoft.NET.Test.Sdk`, `MSTest.TestAdapter`,
`MSTest.TestFramework`). Czwarte trafienie `grep -c PackageReference` to komentarz
`Sam projekt src/Sim nie ma ani jednego PackageReference.` Zdanie jest prawdziwe
i nie wymaga niczego.

## 6. Trzeci punkt pomiarowy, którego pozycja nie miała

Pozycja zestawia dwa kontenery: `docs/23` mówi **10.0.400** (08.09.2026),
`test_dotnet_version.py` notuje **10.0.401** (10.09.2026). W kontenerze tej sesji
(**18.09.2026**) jest coś trzeciego:

```
$ ls -d /root/.dotnet
ls: cannot access '/root/.dotnet': No such file or directory
$ command -v dotnet || echo "(pusto, kod 1)"
(pusto, kod 1)
```

Katalogu **nie ma w ogóle**, a nie „jest z inną wersją". To wzmacnia tezę pozycji
mocniej, niż ją stawiała: zdanie „na tej maszynie" bez daty starzeje się nie tylko
co do **wersji** narzędzia, ale co do jego **istnienia** — a czytelnik bez daty przy
zdaniu nie ma jak odróżnić opisu dnia od opisu stanu bieżącego i wyciągnie
z dokumentu wniosek o dysku, którego nigdy nie oglądał.

Do dokumentu tego **nie dopisano**. Pole „Wyjście" żąda daty, nie drugiego pomiaru,
a dołożenie stanu dzisiejszego kontenera do zdania o cudzym jest dokładnie tym, przed
czym ostrzega pole „Poza zakresem".

## 7. Kontrole, przewidywania spisane PRZED przebiegami

Bramki tu nie ma i nie powstaje — pole „Poza zakresem" mówi, że bramka na kształcie
zapalałaby się na akapitach poprawnych, czyli byłaby bramką wyłączaną zamiast
naprawianą (6.D27). Kontrolowany jest więc **czytnik** i **pole „Weryfikacja"**.
Wszystkie cztery na PEŁNEJ kopii drzewa, z `.git`; korzeń podawany czytnikowi WPROST
argumentem; `__pycache__` czyszczony przed każdym przebiegiem.

| kontrola | co zmienione na kopii | przewidziane | zmierzone | zgodne |
|---|---|---|---|---|
| KN-1 | data z §1 cofnięta | kopia 2 bez daty, drzewo robocze 1 | kopia **2** (w. 160 i 473), drzewo **1** | tak |
| KN-2 | zdanie z w. 160 SKASOWANE zamiast udatowane | `grep -nic` = 6 | **6** | tak |
| KN-3 | dopisane NOWE zdanie o maszynie bez daty | czytnik 2 zamiast 1 | **2** (w. 474 i 755) | tak |
| KN-4 | zapadka raportów podniesiona do `MIN_REPORTS` = 403, ale pliku raportu NIE MA | `test_report_hygiene.py` czerwony | **9/18**, kod **1** | tak |

Wyjście KN-1, obie strony jednym przebiegiem:

```
=== KN-1 (kopia, data cofnieta) ===
ZDAN=8  GREP_LINII=7  BEZ_DATY_W_AKAPICIE=2
  bez daty, akapit od w.160: Na tej maszynie `/root/.dotnet/dotnet` zgłasza **10.0.400**, a doctor melduje brak:
  bez daty, akapit od w.473: Rdzeń w `src/Sim/` nie ma zależności NuGet, ale `tests/Sim.Tests` ma trzy pakiety — **pier
=== KN-1 (drzewo robocze, data JEST) ===
ZDAN=8  GREP_LINII=7  BEZ_DATY_W_AKAPICIE=1
  bez daty, akapit od w.474: Rdzeń w `src/Sim/` nie ma zależności NuGet, ale `tests/Sim.Tests` ma trzy pakiety — **pier
```

Wyjście KN-4:

```
FAIL test_podloga_sciezek_na_raport_jest_ZABOKSOWANA_pomiarami: bramka przeszła tylko 402 raportów, a w `reports/` jest ich co najmniej 403 — skan przestał czytać katalog
FAIL test_zapadka_liczby_raportow_nie_zostaje_za_katalogiem: raportów jest 402 przy `MIN_REPORTS` = 403 — któryś raport zniknął z `reports/` albo skan przestał go czytać
FAIL test_zapis_o_naglowku_w_konwencjach_zgadza_sie_z_ksztaltem_z_raportow: tylko 402 raportów w pętli
  9/18 przeszło
```

### Co KN-2 pokazało PONAD przewidywanie

Przewidywanie mówiło tylko o `grep`. Czytnik na skasowanym zdaniu podał
`ZDAN=7 GREP_LINII=6 BEZ_DATY_W_AKAPICIE=1` — czyli **licznik „bez daty" wyszedł
DOKŁADNIE TAKI SAM jak po poprawnym udatowaniu**. Skasowanie zdania i dopisanie mu
daty są dla tego licznika nieodróżnialne; odróżnia je dopiero liczba populacji
(8 zdań / 7 wierszy). Dlatego pole „Weryfikacja" pilnuje `grep -nic`, a nie liczby
zdań bez daty, i dlatego ta siódemka jest w tej pozycji przyrządem, a nie ozdobą.

## 8. Czego świadomie nie zrobiono

* **Nie skasowano ani jednego zdania.** `grep -nic` przed zmianą i po niej: **7** i **7**.
* **Nie poprawiono wersji SDK** — pole „Poza zakresem", §1.
* **Nie zszyto zawijania w wierszach 85–86** — podniosłoby `grep` do ośmiu, §3.
* **Nie dopisano daty przy zdaniu o maszynie dowolnej** — zepsułoby zdanie, §5.
* **Nie dopisano trzeciego pomiaru do `docs/23`** — §6.
* **Nie napisano bramki** — pole „Poza zakresem" i 6.D27.
* **Nie ruszono `tools/tests/test_dotnet_version.py`** ani jego noty z 10.09.2026.

## 9. Zauważone przy okazji, nietknięte

* Wzorzec z pola „Weryfikacja" nie ma granic słowa i łapie `czystym kontenerze`
  wnętrzem wyrazu (§3). Nietknięte, bo zmiana wzorca zmienia liczbę, której pole
  pilnuje.
* `docs/23-environment.md` ma **149** akapitów i tylko osiem z nich mówi o maszynie —
  reszta opisuje projekt. Rozdział między „opisem dnia" a „opisem projektu" jest
  w tym dokumencie robiony ręcznie i niczym niepilnowany; to jest ta sama luka,
  z której wyszła ta pozycja, tyle że w skali całego pliku.
