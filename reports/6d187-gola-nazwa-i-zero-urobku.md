# 6.D187 — gołych nazw jest 1331, bez odpowiednika 32, a urobek poszerzenia to ZERO usterek przy ośmiu wyjątkach

**13.09.2026**, na `7771af3`. Wejście: `tools/tests/test_field_paths.py`
(`PATH_TOKEN`, `MODULE_CALL`, `SPRAWDZONE_RECZNIE`), `docs/TASKS.md`, `docs/*.md`,
`reports/6d157-zly-adres-trzy-razy.md` §3.

## 1. Czego pozycja żądała

Dwóch liczb policzonych **przed** zmianą wzorca — ile gołych nazw plików stoi
w skanowanych dokumentach i ile z nich wskazuje coś, czego w drzewie nie ma — oraz
rozstrzygnięcia, czy poszerzenie `PATH_TOKEN` da się zrobić **bez listy wyjątków**.

Pole „Skąd" mówiło wprost: cztery z sześciu złych adresów 6.D157 stały **bez katalogu**,
a `PATH_TOKEN` żąda ukośnika, więc bramka złapała **zero z czterech**.

## 2. Pierwsza i druga liczba

Wzorzec gołej nazwy zbudowany z **alternatywy rozszerzeń wyciętej z `PATH_TOKEN`**,
a nie przepisanej obok — dwie listy tych samych rozszerzeń rozjechałyby się po cichu,
a rozjazd akurat tej pary znaczyłby, że jeden kształt widzi plik, którego drugi nie widzi.

| | |
|---|---:|
| wystąpień gołej nazwy w `docs/*.md` | **1331** |
| różnych nazw | **276** |
| **różnych bez odpowiednika w drzewie** | **32** |

**Trzydzieści dwie nazwy to nie trzydzieści dwie usterki**, i to jest pierwsza połowa
odpowiedzi. Rozkładają się na cztery rodziny, z których żadna nie jest błędem:

| rodzina | przykłady |
|---|---|
| nazwa zastępcza prozy | `PLIK.json`, `AXIS.csv`, `TEST.json`, `a.py`, `b.py`, `d1.csv`, `new.json`, `old.json`, `plik.md` |
| wytwór przebiegu (reguła 8 zabrania komitować) | `GODOT_metadata.json`, `_metadata.json`, `inspect.png`, `good_inside.png`, `czas-modulow.json`, `metro-mutacje.jsonl` |
| wytwór budowania | `Sim.AssemblyInfo.cs`, `v10.0.AssemblyAttributes.cs`, `runtimeconfig.json`, `Tests.cs` |
| plik CUDZY | `dotnet-install.sh`, `SHA512-SUMS.txt`, `stops.txt` (GTFS STIB) |

Zostają trzy: `test_all_self.py`, `test_glossary.py`, `test_physics_reference.py` — i te
trzy **są cytatami własnych poprawek**, o czym §4.

## 3. Te same liczby TAM, GDZIE BRAMKA NAPRAWDĘ PATRZY

Poszerzony `PATH_TOKEN` zapalałby się wyłącznie w **trzech polach skanowanych**
(`Wejście`, `Wyjście`, `Weryfikacja`), a nie w całych dokumentach:

| | wystąpień | różnych | bez odpowiednika |
|---|---:|---:|---:|
| pola WSZYSTKICH bloków | **244** | **88** | **10** (w 8 miejscach) |
| pola bloków **OTWARTYCH** | 12 | 7 | **0** |

**W polach bloków otwartych — jedynych, które są obietnicą o przyszłości — nie ma ani
jednej gołej nazwy bez odpowiednika.**

## 4. ROZSTRZYGNIĘCIE: nie poszerzamy, i to jest zmierzone, nie ostrożnościowe

Osiem miejsc, w których poszerzony wzorzec zapaliłby się dziś, przeczytane po kolei:

| miejsce | co tam stoi |
|---|---|
| 6.B1 / 6.B2 „Weryfikacja" `AXIS.json` | nazwa zastępcza w szablonie polecenia `--out AXIS.json` |
| 6.D1 „Wejście" `PLIK.csv`, „Weryfikacja" `AXIS.csv`, `AXIS.json` | trzy nazwy zastępcze w jednym szablonie |
| 6.D59 „Wyjście" `plik.md` | nazwa zastępcza w opisie KSZTAŁTU wyjścia |
| 6.D86 „Weryfikacja" `test_physics_reference.py` | **cytat własnej poprawki** |
| 6.D89 „Weryfikacja" `test_glossary.py` | **cytat własnej poprawki** |

Dwa ostatnie to nie adresy, tylko zdania, które **dokumentują naprawę tej samej usterki,
o której ta pozycja jest**:

```
Poprawione 10.09.2026 przy wykonaniu: pole wołało `test_physics_reference.py`,
modułu o tej nazwie w drzewie nie ma, a bramka pól tego nie widzi, bo nazwa stoi
bez katalogu — `PATH_TOKEN` żąda ukośnika.
```

**Dzisiejszy urobek poszerzenia to ZERO usterek przy ośmiu wyjątkach**, a dwa z tych
wyjątków musiałyby wyciszyć zapis naprawy. Lista wyjątków jest drogą powrotną dla tego,
co bramka miała wykluczyć — pole „Skąd" pozycji mówiło to samo, tyle że jako obawę;
tu jest to policzone.

## 5. Powód, dla którego poszerzenie nie dodałoby POKRYCIA

Trzy z czterech złych adresów 6.D157 — `test_physics_reference.py` (6.D86),
`test_glossary.py` (6.D89), `test_all_self.py` (6.D102) — stały jako **goły argument
`test_all.py`**, czyli w kształcie, który `MODULE_CALL` czyta **od 6.D101**. Czwarty
(`test_scan_gates.py`, 6.D74) w drzewie jest, a „czy moduł zawiera bramkę, o której
pole mówi" wyklucza jego własne pole „Poza zakresem".

Kontrola **dodatnia** na wejściu syntetycznym, bo w drzewie nie ma dziś ani jednej
takiej nazwy do złapania — odtworzony jest tekst pola 6.D86 **sprzed** poprawki:

```
missing_modules({"6.D86-SPRZED": ...}) == [("6.D86-SPRZED", "Weryfikacja",
                                            "test_physics_reference.py")]
```

Druga strona, też syntetyczna: ta sama nazwa **w prozie** wywołaniem nie jest i złapana
nie zostaje — czyli reguła wywołań nie zapala się na adnotacji dokumentującej poprawkę,
a poszerzony `PATH_TOKEN` by się zapalił.

**Klasa usterek z 6.D157 jest więc już pokryta, tylko regułą INNEGO KSZTAŁTU** — tą,
która czyta WYWOŁANIE, a nie napis o kształcie pliku. Poszerzenie wzorca ścieżek nie
dodaje pokrycia, a dokłada osiem wyjątków.

**Czego NIE twierdzę:** że nie istnieje klasa gołych nazw poza zasięgiem obu reguł.
Twierdzę tylko tyle, ile zmierzyłem — że na dzisiejszym drzewie nie ma jej ani jednego
przypadku, a wszystkie osiem zapaleń ma powód spoza rodziny „zły adres".

## 6. Sześć kontroli negatywnych, baza 37/37

| kontrola | podstawienie | wynik |
|---|---|---|
| KN-1 | domknięcie wzorca bez ukośnika | 36/37 — **za drugim podejściem** |
| KN-2 | poprzednik bez ukośnika (ogony ścieżek wchodzą jako gołe nazwy) | **33/37** |
| KN-3 | rozszerzenia przepisane obok zamiast wycięte z `PATH_TOKEN` | 35/37 |
| KN-4 | goła nazwa nieistniejąca dopisana do pola bloku OTWARTEGO | 34/37 |
| KN-5 | jeden wpis zdjęty z listy sklasyfikowanych | 36/37 |
| KN-6 | `MODULE_CALL` zepsuty — teza „ta klasa jest już łapana" traci podstawę | **27/37** |

### KN-1 wyszła ZIELONA i powiedziała prawdę o moim wzorcu

Ukośnik w domknięciu `(?![A-Za-z0-9/])` jest **bezczynny na dzisiejszym drzewie**:
jego zdjęcie nie ruszyło ani jednej z liczb tej sekcji. Powód jest strukturalny — ogon
ścieżki odcina już **poprzednik** `(?<![A-Za-z0-9_./-])`, a nazwa z rozszerzeniem
stojąca jako PIERWSZY segment ścieżki w tym repozytorium nie pada ani razu.

Przyczyna z katalogu zielonych kontroli jest tu czwarta — **mechanizm naprawdę
bezczynny**. Naprawą nie było zdjęcie domknięcia, tylko **uczynienie jego bezczynności
widoczną**: próbka syntetyczna `reference.py/dalej`, na której obie wersje wzorca
dają różne wyniki. Ta sama decyzja i ten sam powód, co przy `RootElement` w 6.D186 —
**druga taka kontrola w dwóch pozycjach pod rząd**.

## 7. Czego świadomie nie zrobiłem

- **`PATH_TOKEN` nie został zmieniony ani o znak** — pozycja pytała, czy da się go
  poszerzyć, a odpowiedź brzmi „nie i dlaczego".
- **Adresów znalezionych po drodze nie poprawiałem** — pole „Poza zakresem" mówi
  wprost, że to osobna robota. Ani jeden zresztą nie jest dziś zły.
- **`SPRAWDZONE_RECZNIE` nie tknięte** — to samo pole.

## 8. Zauważone po drodze, nie tknięte

- **Trzeci próg okazał się zbędny i został zdjęty przed commitem.** Napisałem
  najpierw `MIN_GOLYCH_ROZNYCH = 250`, po czym wyszło, że jest ściśle słabszy od
  równości `GOLYCH_BEZ_ODPOWIEDNIKA`: ta liczy się **ze zbioru różnych nazw**, więc
  zapadnięcie się tego zbioru rusza ją pierwsze. Trzecia wolna zapadka mówiąca to samo
  słabiej kosztuje wpis w `test_tree_walks.ZAPADKI` i nie daje nic. Zapadek jest więc
  **44, nie 45**, a wolnych **23, nie 24**.
- Lista rozszerzeń stała dotąd **wyłącznie w `PATH_TOKEN`**; każdy inny kształt, który
  jej potrzebuje, musiałby ją przepisać. `BARE_TOKEN` bierze ją z tamtego wzorca
  wycięciem, ale nie jest to mechanizm ogólny — trzeci kształt, gdyby powstał, znów
  stanąłby przed tym wyborem.
- `SHA512-SUMS.txt` i `dotnet-install.sh` (`docs/23-environment.md`) to nazwy plików
  CUDZYCH, pobieranych przy instalacji. Bramka istnienia nie ma o nich zdania i mieć
  nie może — ale nie ma też w dokumencie niczego, co by je od nazw własnych odróżniało.
