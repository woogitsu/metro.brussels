# 6.D318 · Wymuszone są DWIE ze siedemdziesięciu — a trzy źródła gwarancji z pola dają w tym drzewie ZERO

**Data:** 20.09.2026 · **Gałąź:** `claude/new-session-1xabcy` · **Baza:** `07bb4e6`

6.D308 zmierzyło, że ze 102 kolizji nazw składników 32 zwracają różne typy i dlatego
psują skan po nazwie. Pozostałych **70** zwraca ten sam typ — i tamta pozycja zapisała
wprost (§8), że nikt nie sprawdził, czy to gwarancja, czy zbieg.

Odpowiedź: **gwarancję ma 2 z 70, a zbiegiem jest 68.** Ale liczba, dla której warto
było tę pozycję wziąć, jest inna: **trzy źródła gwarancji, które pole wymienia z nazwy
— interfejs, typ bazowy i generyk — dają w zasięgu `src/` po ZERO**, bo całe `src/`
ma **jeden** interfejs i **zero** publicznych typów generycznych.

---

## 1. Kontrola przyrządu — ZDANA co do wszystkich trzech liczb

Pole żąda, żeby klasy zsumowały się do **70**, czyli do liczby z 6.D308 (102 minus 32).

```
KONTROLA PRZYRZADU (cel 6.D308: 102 / 32 / 70)
   kolizji        : 102
   zlosliwych     : 32
   NIEZLOSLIWYCH  : 70
```

Suma jest **sprawdzona asercją w przyrządzie**, a nie odczytana z ekranu.

**Kalibracja kosztowała trzy przebiegi i to jest treść, nie anegdota.** Pierwszy
przyrząd dał 110 kolizji i 34 złośliwe. Dwie rzeczy go rozjeżdżały z 6.D308:

1. **Własność składnika szła po „ostatniej deklaracji typu przed pozycją"**, a nie po
   zagnieżdżeniu klamer — więc składnik typu zagnieżdżonego **prywatnego** wpadał do
   typu obejmującego. Zagnieżdżenie naprawia to co do jedynki.
2. **Składniki `const` wchodziły do populacji.** Bez nich wychodzi 102/32, z nimi 107/34.

Wariant kontrolny liczący tylko metody i właściwości (bez pól) daje **te same 102 i te
same 32** przy innej liczbie nazw (500 wobec 507) — **liczba, o którą pyta pozycja, jest
więc odporna na ten wybór, a mianownik nie.** Jest to ten sam kształt, który 6.D308
zmierzyło na przesłonięciach, a 6.D306 na czytnikach drzewa: **definicja rządzi
rankingiem i mianownikiem, a nie odpowiedzią.** Trzeci raz z rzędu.

## 2. MIANOWNIKA NIE UZGADNIAM i mówię, czego nie liczę

6.D308 podaje **527** różnych nazw składników publicznych i `ToString` w **45** typach.
Mój przyrząd, skalibrowany do 102/32, daje **507** nazw i `ToString` w **46** typach.

**`src/` nie ruszyło się ani o bajt** od bazy tamtej pozycji — `git diff 3c93a5d HEAD --
src/` jest pusty. Różnica jest więc **własnością przyrządu, nie drzewa**, i nie próbuję
jej uzgadniać: rozciąganie mojego kształtu do cudzej liczby dałoby zgodność bez wiedzy
(lekcja 7 z poprzedniej sesji, ten sam ruch co przy 6.D317 z populacją 136 wobec 143).

Czego **nie** liczę i co najprawdopodobniej tłumaczy dwadzieścia nazw różnicy: składników
`const`, składowych pozycyjnych rekordów (§6) i składników interfejsów zapisanych bez
słowa `public`. Na liczbę 102/32/70 żadne z tego nie wpływa — sprawdzone wariantem
kontrolnym wyżej.

## 3. CZYTANIE A — litera pola: trzy źródła, trzy zera

Klasy spisałem **przed pomiarem**, rozłączne, pierwsze pasujące wygrywa: INTERFEJS
(wspólny interfejs `src/` deklarujący tę nazwę) · TYP BAZOWY (wspólna klasa bazowa
`src/`) · GENERYK · BEZ WYMUSZENIA.

```
== CZYTANIE A — LITERA K2 (zasieg src/) ==
   INTERFEJS          0
   TYP BAZOWY         0
   GENERYK            0
   BEZ WYMUSZENIA    70
   SUMA              70
```

**Trzy zera nie są znaleziskiem o kolizjach — są znaleziskiem o drzewie.** Przeczytałem,
dlaczego wyszły, zamiast raportować zero:

```
interfejsow publicznych w calym src/ : 1   (ITrainBody, src/Game/World/TrainView.cs)
typow publicznych GENERYCZNYCH       : 0
typow z lista bazowa                 : 7   (6 x baza Godota, 1 x IEquatable<FixedStep>)
```

Przy 156 typach publicznych `src/` ma **jeden** interfejs i **ani jednego** generyka.
Co więcej, ten jeden interfejs **nie może dać ani jednej kolizji w tej populacji**:
`ITrainBody` implementują dwa typy **niepubliczne** (`CabBody`, `NodeBody`), a populacja
6.D308 liczy wyłącznie składniki typów publicznych. Klasa INTERFEJS była więc pusta
**z konstrukcji drzewa**, a nie z wyniku pomiaru — mówię to wprost, zamiast raportować
zero jako znalezisko (ten sam ruch co 6.D317 przy pustej klasie „ścieżka albo nazwa pliku").
Klasa „gwarancja z interfejsu" nie mogła w tym drzewie wyjść niepusta, a klasa
„gwarancja z generyka" nie ma nawet kandydata. **Pole ostrzegało przed czymś innym,
niż się okazało:** ostrzegało, że widzenie samego `interface` policzy za mało — a tu
za mało liczą **wszystkie trzy** klasy naraz, bo konstrukcje, o które pytają, w tym
kodzie po prostu nie występują.

## 4. CZYTANIE B — zasięg rozszerzony poza `src/`: wymuszone są DWIE

Zero w każdej klasie znaczyłoby tylko tyle, że sito jest za wąskie, więc powtórzyłem
pomiar z zasięgiem rozszerzonym na bazy i interfejsy **spoza** `src/` (BCL, Godot).
Podaję oba czytania, zamiast wybrać po cichu.

```
== CZYTANIE B — ZASIEG ROZSZERZONY ==
   INTERFEJS          0
   TYP BAZOWY         2
   GENERYK            0
   BEZ WYMUSZENIA    68
   SUMA              70
```

Wymuszone imiennie, bo są dwie:

| nazwa | typów | źródło wymuszenia |
|---|---|---|
| `ToString` | 46 | `override` w **46 z 46** — przesłonięcie `object.ToString()` |
| `_Ready` | 2 | `override` w **2 z 2** — punkt wejścia węzła Godota (`FirstRun`, `Hud`) |

**Kontrola przyrządu po nazwie, nie tylko po liczniku:** `ToString` MUSI wyjść jako
wymuszony i wychodzi — 46 na 46 deklaracji ma `override`. Gdyby klasyfikator gubił
`override`, największa kolizja niezłośliwa w drzewie wpadłaby do „bez wymuszenia"
i odpowiedź brzmiałaby 0 z 70.

**Ani jedno wymuszenie nie pochodzi z kodu tego projektu.** Oba źródła leżą poza
`src/`: jedno w bibliotece standardowej .NET, drugie w silniku. Odpowiedź na pytanie
pozycji, czytana dosłownie, brzmi więc: **w kodzie tego projektu gwarancji nie ma
ŻADNEJ.**

## 5. Klasa „bez wymuszenia" to 68 ze 70, czyli 97 % — więc ją rozbijam

Warunek obalenia spisałem przed pomiarem: rozbijam, gdy klasa przekroczy połowę. Tu
przekroczyła ją trzykrotnie. Rozbicie po **typie zwracanym**:

```
   typ PROSTY (double)       26
   typ PROJEKTU              15
   typ PROSTY (string)       11
   typ PROSTY (bool)          5
   typ PROSTY (long)          4
   typ PROSTY (void)          3
   typ PROSTY (int)           2
   KOLEKCJA                   2
   SUMA                      68
```

Typy proste dają **51 z 68, czyli 75 %**. Rozbicie po liczbie typów deklarujących:
50 nazw ma dwa typy, 10 ma trzy, a powyżej trzech stoi osiem nazw (`Describe` 4,
`DistanceM` 5, `Id` 5, `SpeedLimitMps` 5, `TimeSeconds` 5, `Steps` 6, `Finished` 7,
`LengthM` 7).

**Wniosek jest mocniejszy niż „zbieg".** Te 68 nazw zbiega się na tym samym typie nie
dlatego, że ktoś je zbiegł przypadkiem, tylko dlatego, że **słownik typów zwracanych
jest w tym drzewie ubogi**: `double` odpowiada za jedną trzecią całej klasy. Przy
ubogim słowniku zbieżność jest stanem domyślnym, a nie zdarzeniem — i dokładnie
dlatego jest krucha.

## 6. ŹRÓDŁO CZWARTE I PIĄTE — zamknięta lista trzech znowu nie wystarczyła

Pole wymienia trzy źródła wymuszenia. Pomiar znalazł dwa, których nie wymienia,
i żadne z nich nie jest gwarancją **typu**, tylko czymś, co działa tak samo:

**Czwarte: jednostka w nazwie.** Spośród 68 nazw bez wymuszenia **25** kończy się
przyrostkiem jednostkowym konwencji z `docs/04-conventions.md` (`M`, `Mps`, `Mps2`,
`Mps3`, `Kmh`, `Kg`, `Kwh`, `Seconds`, `J`, `N`, `Steps`), a z 26 nazw zwracających
`double` ma go **23**.

```
AxisLengthM, ChainageM, DistanceM, DwellRemainingSeconds, EffectiveMassKg,
FinalSpeedKmh, FinalSpeedMps, ForceN, HeadwaySteps, JerkMps3, LengthM, MassKg,
MaxBrakeDemandMps2, PassengerExchangeSeconds, PermittedSpeedMps, RearChainageM,
ResidualJ, RoofHeightM, ServiceBrakeMps2, SpeedKmh, SpeedLimitMps, StartChainageM,
Steps, TimeSeconds, TractionWorkKwh
```

`AxisLengthM` nie może zwrócić `string`, bo litera `M` w nazwie znaczy metry.
**Wymuszenie jest realne, tylko nie leży w systemie typów — leży w konwencji nazw,
której nie pilnuje żadna bramka** (zmierzone osobno przy 6.D310, pozycja 6.D320 pyta
o to wprost). Do klasy „wymuszone" tych 25 **nie przenoszę**: pytanie pola dotyczy
gwarancji, a konwencja gwarancją nie jest — jest silniejsza od zbiegu i słabsza od
`override`, więc podaję ją jako trzecią wartość, a nie doklejam do żadnej z dwóch.

**Piąte: składowe pozycyjne rekordów — niewidoczne dla przyrządu 6.D308.**

```
typow-rekordow ze skladowymi pozycyjnymi: 53
skladowych pozycyjnych razem            : 243
```

Dwieście czterdzieści trzy składowe publiczne, których wzorzec „wiersz zaczynający się
od `public`" nie widzi, bo stoją w nawiasie głowy rekordu. **Dwanaście** nazw z klasy
„bez wymuszenia" pada **także** jako składowa pozycyjna (`AxisId`, `Calls`, `ChainageM`,
`Command`, `DistanceM`, `Id`, `LengthM`, `PermittedSpeedMps`, `Reason`, `Status`,
`Steps`, `TimeSeconds`). Doliczenie ich podnosi populację ze 102 do **145** kolizji
i z 32 do **46** złośliwych — czyli **przyrząd 6.D308 widzi siedem dziesiątych
zjawiska**. Tej populacji do odpowiedzi **nie używam**, bo kontrola przyrządu żąda 70,
ale zapisuję liczbę, zamiast ją przemilczeć.

## 7. Lista imienna klasy „bez wymuszenia" — 68 nazw

Pole żąda jej wprost, „także gdy jest pusta". Pusta nie jest. Kolumna druga to liczba
typów deklarujących, trzecia — wspólny typ zwracany, który przestanie być wspólny przy
pierwszym typie dopisanym obok.

| nazwa | typów | wspólny zwrot |
|---|---|---|
| `Adhesion` | 2 | `double` |
| `AtStation` | 2 | `bool` |
| `AxisId` | 2 | `string` |
| `AxisLengthM` | 2 | `double` |
| `BodyCount` | 2 | `int` |
| `Calls` | 2 | `IReadOnlyList<StationCall>` |
| `ChainageM` | 2 | `double` |
| `Command` | 2 | `DriverCommand` |
| `Cycle` | 2 | `DoorCycle` |
| `Describe` | 4 | `string` |
| `Digest` | 2 | `string` |
| `Dispatcher` | 2 | `RouteDispatcher` |
| `DistanceM` | 5 | `double` |
| `DropSamples` | 2 | `void` |
| `DwellRemainingSeconds` | 2 | `double` |
| `Dynamics` | 2 | `TrainDynamics` |
| `EffectiveMassFactor` | 2 | `double` |
| `EffectiveMassKg` | 2 | `double` |
| `EmergencyInterventions` | 2 | `long` |
| `Filter` | 2 | `DriverCommand` |
| `FinalSpeedKmh` | 2 | `double` |
| `FinalSpeedMps` | 2 | `double` |
| `Finished` | 7 | `bool` |
| `For` | 2 | `string` |
| `ForceN` | 2 | `double` |
| `HeadwaySteps` | 2 | `long` |
| `Help` | 2 | `string` |
| `Id` | 5 | `string` |
| `IsAdhesionLimited` | 2 | `bool` |
| `JerkMps3` | 2 | `double` |
| `LengthM` | 7 | `double` |
| `Line` | 3 | `string` |
| `MassKg` | 2 | `double` |
| `MaxBrakeDemandMps2` | 2 | `double` |
| `Mode` | 2 | `string` |
| `Model` | 3 | `VehicleModel` |
| `Outcome` | 2 | `RunOutcome` |
| `PassengerExchangeSeconds` | 2 | `double` |
| `PermittedSpeedMps` | 2 | `double` |
| `PlaceAt` | 2 | `void` |
| `PointAt` | 2 | `AxisPoint` |
| `ReachedTarget` | 2 | `bool` |
| `ReadEmbeddedJson` | 2 | `string` |
| `RearChainageM` | 2 | `double` |
| `Reason` | 3 | `string` |
| `RelativeResidual` | 3 | `double` |
| `RequestDoorClose` | 2 | `DoorRequestResult` |
| `RequestDoorOpen` | 2 | `DoorRequestResult` |
| `Reset` | 3 | `void` |
| `ResidualJ` | 3 | `double` |
| `RoofHeightM` | 2 | `double` |
| `Row` | 2 | `string` |
| `SchemaVersion` | 2 | `int` |
| `ServiceBrakeMps2` | 2 | `double` |
| `ServiceInterventions` | 2 | `long` |
| `Signalling` | 2 | `FixedBlockSystem` |
| `SpeedKmh` | 3 | `double` |
| `SpeedLimitMps` | 5 | `double` |
| `StartChainageM` | 2 | `double` |
| `State` | 3 | `DriveState` |
| `Status` | 3 | `ParameterStatus` |
| `Steps` | 6 | `long` |
| `Supervise` | 2 | `ProtectionDecision` |
| `TimeSeconds` | 5 | `double` |
| `TimeStep` | 2 | `FixedStep` |
| `TractionAllowed` | 2 | `bool` |
| `TractionWorkKwh` | 2 | `double` |
| `UnknownParameters` | 3 | `IReadOnlyList<string>` |

## 8. Przewidywania spisane PRZED pomiarem

| # | przewidywanie | wynik |
|---|---|---|
| P1 | klasy zsumują się do 70 za pierwszym przyrządem | **PUDŁO** — pierwszy dał 110/34, kalibracja zajęła trzy przebiegi (§1) |
| P2 | „bez wymuszenia" w przedziale 35–60 | **PUDŁO** — 68, i pudło jest w tę stronę, że nie doceniłem |
| P3 | INTERFEJS poniżej 10 | trafione, ale **jałowo**: 0, bo interfejs w `src/` jest jeden |
| P4 | TYP BAZOWY poniżej 5 | trafione (0 / 2) |
| P5 | GENERYK będzie największy ze źródeł wymuszonych | **PUDŁO co do mechanizmu** — 0, bo generyków publicznych `src/` nie ma wcale |
| P6 | w „bez wymuszenia" dominują `string`/`double`/`int`/`bool` | trafione — proste dają 51 z 68 (75 %) |
| P7 | zamknięta lista trzech źródeł okaże się niewyczerpująca | **trafione PO RAZ ÓSMY z rzędu** — §6 |

**P3 i P4 podaję jako trafione JAŁOWO, a nie po prostu trafione**, i to jest wybór.
Oba przedziały postawiłem, myśląc o tym, że gwarancji będzie mało; wyszły zera, ale
z powodu, którego nie przewidziałem — nie „mało gwarancji", tylko „brak konstrukcji,
z której gwarancja mogłaby powstać". Trafiona liczba przy chybionym mechanizmie to
ten sam kształt, który 6.D289 nazwało „najciekawszym pudłem".

**P7 jest ósmym trafieniem z rzędu na przewidywaniu o mnie samym.** 6.D317 zapisało
po siódmym, że zamknięta lista przestaje być w tym projekcie przewidywaniem i staje
się przyrządem do mierzenia własnej niewiedzy. Ósme trafienie tego nie zmienia —
**potwierdza**, i dlatego P7 zostaje w tabeli jako wynik, a nie jako zasługa.

## 9. Czego świadomie nie zrobiono

- **Nie przemianowano niczego i nie dopisano ani jednego interfejsu.** Pole nazywa
  to decyzją projektową; §3 pokazuje, że dopisanie interfejsu byłoby tu zmianą
  architektury drzewa, w którym interfejsów praktycznie nie ma.
- **Nie postawiono bramki na wyniku.** Pole zabrania, a §5 mówi, dlaczego byłoby to
  przedwczesne: 68 pozycji klasy kruchej to nie jest lista usterek.
- **Nie napisano analizatora symboli** — ta sama granica, którą 6.D299 wyceniło,
  a 6.D308 obejrzało.
- **Nie uzgodniono mianownika 507 ze 527** ani `ToString` 46 z 45 (§2).
- **Nie użyto populacji 145/46 ze składowymi pozycyjnymi** do odpowiedzi, mimo że
  jest szersza — kontrola przyrządu żąda 70 (§6).
- **Nie przeniesiono 25 nazw z jednostką do klasy „wymuszone"** (§6).
- **Nie tknięto `src/` ani `data/`.**

## 10. Zauważone przy okazji, nietknięte

1. **`src/` ma jeden interfejs publiczny i zero typów generycznych przy 156 typach.**
   Nie jest to usterka i nie jest przedmiotem tej pozycji, ale jest to własność, która
   unieważnia **całą** klasę pytań o „gwarancję z systemu typów" w tym drzewie —
   i warto ją znać, zanim ktoś postawi następną pozycję na tym samym założeniu.
2. **243 składowe pozycyjne rekordów są niewidoczne dla każdego wzorca liniowego
   szukającego `public`.** Dotyczy to nie tylko przyrządu 6.D308: ten sam kształt
   wzorca stoi w `tools/tests/test_csharp_type_callers.py` i w
   `tools/tests/test_dead_constants_csharp.py`.
3. **`Finished` i `LengthM` mają po siedem typów deklarujących i po jednym typie
   zwracanym.** Są to dwie najbardziej kruche pozycje listy z §7: przy siedmiu
   deklaracjach prawdopodobieństwo, że ósma dopisze inny typ, jest największe,
   a żaden mechanizm temu nie zapobiega.
4. **Kontener tej sesji dostał klon PŁYTKI (51 commitów) i to ZAPALA dziewięć bramek,
   które o kolizjach nie mówią nic.** Pierwszy pełny przebieg dał 2654/2664 z awariami
   czytników historii („czytnik oslepl albo historia zostala przepisana", „klon płytki
   albo commit graniczny"); po pogłębieniu klonu do pełnych 1060 commitów **ten sam
   zestaw na tym samym drzewie daje 2664/2664 i kod 0**. Dziesiąta awaria była moim
   własnym raportem jako plikiem nieśledzonym i znika przy `git add`. Zapisuję to,
   bo różnica nie jest własnością gałęzi ani bramek, tylko środowiska — a czytana
   bez tej wiedzy wygląda dokładnie jak regres.
