# 6.D221 — jedno trafienie prawdziwe na trzydzieści pięć, a fałszywe robi własny czytnik

**15.09.2026**, na `2faa2f2`. Wejście: `docs/TASKS.md`, `src/Sim/**/*.cs`,
`src/Game/**/*.cs`, `tests/**/*.cs`, `tools/tests/test_field_paths.py` (`PATH_TOKEN`),
`tests/Sim.Tests/DefaultArmAuditTests.cs` (`KorpusMetody`),
`reports/6d211-dziesiec-nazw-zamiast-liczby-dziesiec.md` §6.

## 1. Populacja, zawężana krok po kroku

| | |
|---|---:|
| zdań niosących nazwę pliku `.cs` **i** nazwę w grawisach | **157** |
| par (plik, nazwa) | **341** |
| par różnych | 250 |
| plików `.cs` wymienionych w prozie, których nie ma w drzewie | **0** |

Nazwa równa nazwie bazowej pliku (`` `TrainProtection` `` przy `TrainProtection.cs`)
do par nie wchodzi — to odsyłacz do tego samego, nie twierdzenie o zawartości.

**Liczby z pola „Czego NIE wolno przyjąć bez pomiaru" są inne od moich i to jest
w porządku:** pole mówiło o 126 zdaniach i 486 parach, przelicznik zgrubny. Mój podział
na zdania jest inny i odsiewam nazwę bazową pliku. Rząd wielkości ten sam, wniosek pola
— „sito po samym kształcie dałoby lawinę trafień fałszywych" — potwierdzony.

## 2. Co te 341 par naprawdę jest

| klasa | par |
|---|---:|
| **metoda TEGO pliku** — zdanie poprawne | **124** |
| nazwa, której drzewo nie zna w ogóle | 93 |
| typ INNEGO pliku | 49 |
| **METODA INNEGO PLIKU — kandydat** | **45** (35 par różnych) |
| składowa TEGO pliku | 19 |
| typ TEGO pliku | 11 |

**Sito naiwne** („nazwa w grawisach obok pliku ma być w nim zadeklarowana") zapaliłoby
się na **217 z 341** par, czyli na dwóch trzecich — w tym na wszystkich 93 nazwach,
które nie są kodem, i na wszystkich 49 typach z innych plików.

## 3. Sito zawężone: 35 kandydatów, JEDNO trafienie prawdziwe

Zawężenie do „nazwa **jest** metodą w drzewie, ale **nie w tym pliku**" zbija populację
z 217 na **35 par różnych**. Obejrzałem wszystkie 35, zdanie po zdaniu.

**Prawdziwe jest JEDNO — to znane z 6.D210:**

> „**ZAUWAŻONE:** `TrainProtection.cs` ma **oba rodzaje naraz** — wyrażeniowy rzucający
> w `Apply` (3/3) i instrukcyjny cichy w `Replay` (2/3)"

**Trafień fałszywych: 34 z 35, czyli 97 %.** Dzielą się na trzy rodzaje, wszystkie
będące zdaniami **poprawnymi**:

- **pole „Wejście" wymienia plik i metodę INNEGO pliku obok siebie** — konwencja bloków
  (`` `src/Game/FirstRun.cs` (`UpdateHud`), `src/Game/UI/Hud.cs` ``); nazwa należy do
  pliku **przed** nią, nie po;
- **zdanie mówi o dwóch plikach naraz** — „`KorpusMetody` rozpoznaje deklarację po
  modyfikatorze dostępu, bo `Supervise` ma w `CabProtection.cs` wywołanie siedem wierszy
  pod deklaracją, a `Step` w `LineCore.cs` dwa dalej";
- **nazwa jest nazwą TESTU**, nie metody produkcyjnej —
  `Droga_hamowania_z_oporami_nie_zalezy_od_masy_skladu`.

## 4. Sito po konwencji — i tu fałszywe robi WŁASNY czytnik

Kształt `` `plik.cs` (`Nazwa`) `` — nazwa w nawiasie tuż po pliku, konwencja pól
„Wejście" — wygląda na precyzyjny: **153 pary**, z tego **22 rozjechane z drzewem**.

**Większość tych 22 to ślepota mojego czytnika deklaracji, nie kłamstwo prozy.**
Sprawdzone po kolei: `PostacieLiteralu` i `ZrodlaHud` stoją w pliku jako
`private static readonly (string, string, string)[] Nazwa =` — **typ zwracany zawiera
nawias**, a mój wzorzec niezachłanny zatrzymywał się na nim. `NazwyWyliczeniowychWRdzeniu`
i `PolykaneCzlony` mają deklarację wieloliniową. `LineCore`, `ViewKind`, `KnownOptions`
i dalsze są w pliku **używane**, a deklarowane gdzie indziej — i proza mówi o nich
poprawnie.

**`KorpusMetody` z drzewa tej ślepoty NIE MA** i to jest różnica warta zapisania: jego
wzorzec używa `[^;=\n]*` zachłannie, więc typ krotkowy przechodzi. Ślepota była moja,
w czytniku napisanym na jeden pomiar — i gdybym jej nie sprawdził, wpisałbym 22 rozjazdy
jako wynik.

## 5. Trafienia prawdziwe poza 6.D210: są, i są innej klasy

Pole „Skończone, gdy" żądało co najmniej jednego trafienia prawdziwego poza tym
z 6.D210 **albo zapisania, że innych nie ma**. **Są — trzy, i żadne nie jest tą samą
klasą:**

| nazwa w prozie | co jest w drzewie | klasa |
|---|---|---|
| `KszaltSciezkiWezla` (×3) | `SciezkaWezla` — **nazwy `KszaltSciezkiWezla` drzewo nie zna nigdzie** | nazwa, której nigdy nie było |
| `ReadTelemetry` | `ReadTelemetryTrack` | skrót nazwy, która w pliku JEST |
| `KodBezKomentarzy` | `KodBezKomentarzyDlaStaregoCzytnika` | skrót nazwy, która w pliku JEST |

**Wszystkie trzy stoją w blokach DOMKNIĘTYCH** (6.D173, 6.D179), czyli są zapisem
swojego dnia i poprawianiu nie podlegają (6.D108). Klasa z 6.D210 — nazwa metody
z **cudzego pliku** — pozostaje jedyną w swoim rodzaju: skrót i literówka mylą o nazwę,
a nie o miejsce.

## 6. Rozstrzygnięcie: bramka NIE powstaje

Trzy powody, każdy z liczbą:

1. **Sito naiwne zapala się na 217 z 341 par**, czyli na dwóch trzecich zdań
   **poprawnych**. Bramka świecąca na poprawnym tekście zostaje wyłączona, nie
   poprawiona (6.D27).
2. **Sito zawężone ma 34 trafienia fałszywe na 35**, czyli 97 %. Zawężenie przesuwa
   liczby, ale nie zmienia klasy odpowiedzi.
3. **Sito po konwencji ma trafienia fałszywe pochodzące z CZYTNIKA DEKLARACJI**, a nie
   z prozy. Żeby je usunąć, trzeba czytać deklaracje C# bez wzorca — czyli rozbiorem
   składni albo z metadanych, a to jest decyzja o zależności (§8), nie poprawka sita.

To jest ta sama odpowiedź, co w 6.D207 („odsiać się NIE DA") i z tego samego powodu:
**liczba trafień fałszywych jest tu częścią odpowiedzi, a nie kosztem ubocznym.**

## 7. Czego świadomie nie zrobiłem

- **Nie postawiłem bramki** — §6, trzy powody.
- **Nie poprawiłem ani jednego wiersza pozycji domkniętej**, w tym trzech wystąpień
  `KszaltSciezkiWezla` (6.D108 — są zapisem swojego dnia).
- **Nie tknąłem `KorpusMetody`** — jego ślepota to osobna pozycja (6.D231), a tu okazał
  się akurat odporniejszy od mojego czytnika.
- **Numerów wierszy nie oglądałem** — to 6.D208, domknięte.

## 8. Zauważone, nie tknięte

- **93 z 341 par to nazwy, których drzewo nie zna w ogóle** — słowa w grawisach, które
  kodem nie są. Ile z nich to nazwy z `tools/` (Python), a ile proza ubrana w grawisy,
  nie liczyłem.
- **Konwencja pola „Wejście" jest dwuznaczna:** `` `plik.cs` (`Nazwa`) `` znaczy raz
  „ta rzecz jest w tym pliku", a raz „ta rzecz jest tym, o co chodzi w tym pliku".
  Zdania z `LineCore` przy `FirstRun.cs` są poprawne w drugim znaczeniu i nieprawdziwe
  w pierwszym, a rozróżnia je wyłącznie czytelnik.
