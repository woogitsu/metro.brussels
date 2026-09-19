# 6.D299 · Skan po nazwie SKŁADNIKA myli się w 85 % — a jeden z siedmiu jest odbierany bez żadnej zmiennej

**Data:** 19.09.2026 · **Gałąź:** `claude/sharp-ramanujan-jdr51o` · **Baza:** `b8da52d`

6.D290 podało dwie miary „typu zwracanego": **wprost** — piętnaście z dwudziestu
czterech nienazwanych, **w opakowaniu** — dwadzieścia dwa. Różnicą jest siedem typów
zwracanych wyłącznie jako element kolekcji. Ta pozycja pyta, w jakiej postaci wołający
odbiera ten element, i czy któryś odbiera go poza czterema drogami z 6.D298.

---

## 1. Siódemka i jej producent

| typ elementu | producent | rodzaj |
|---|---|---|
| `BrakingReferenceRow` | `BrakingRun.ReferenceTable` | metoda |
| `CbtcDynamicTestSite` | `CbtcTestArea.DynamicTestSites` | właściwość |
| `RouteStation` | `LineRoute.Stations` | właściwość |
| `ServiceBlock` | `ServiceDay.Blocks` | właściwość |
| `SignallingAssumption` | `SignallingPlan.Assumptions` | właściwość |
| `TelemetrySample` | `TelemetryTrack.Samples` | właściwość |
| `ViewAssumption` | `DesignAssumptions.All` | właściwość statyczna |

## 2. ZNALEZISKO PRZYRZĄDU: pięć z siedmiu nazw składnika KOLIDUJE

Pierwszy przebieg przyrządu szukał po nazwie składnika i dał dla `RouteStation`
osiemdziesiąt wołań. **Prawie wszystkie były cudze.** Nazwa składnika nie
identyfikuje typu, bo deklaruje ją więcej niż jeden typ:

| nazwa składnika | ilu typów `src/` ją deklaruje | które |
|---|---|---|
| `Assumptions` | **4** | `BrakeAdhesionLimit`, `DriveScenario`, `LineRunSettings`, `SignallingPlan` |
| `All` | 2 | `BrakingAssumptions`, `DesignAssumptions` |
| `Blocks` | 2 | `ServiceDay`, `SignallingPlan` |
| `Samples` | 2 | `SpeedProfile`, `TelemetryTrack` |
| `Stations` | 2 | `LineRoute`, `TrackAxis` |
| `DynamicTestSites` | 1 | `CbtcTestArea` |
| `ReferenceTable` | 1 | `BrakingRun` |

Najkosztowniejszy przypadek: `axis.Stations` to `TrackAxis.Stations`, a ta zwraca
`AxisStation`, **nie** `RouteStation`. Siedemdziesiąt trzy wołania `.Stations`
w drzewie to cudzy typ.

Po związaniu odbiorcy z typem deklarującym liczby wyglądają tak:

```
przypisanych razem:  34
odrzuconych razem:  193   (odbiorca innego typu)
```

**Osiemdziesiąt pięć procent wołań, które znajduje skan po samej nazwie składnika,
należy do innego typu.** To nie jest szum na brzegu — to jest większość wyniku.

### Jak wiązany jest odbiorca — cztery kształty, wszystkie tekstowe

Analizatora symboli pozycja pisać nie wolno (pole „Poza zakresem"), więc odbiorcę
wiążę czterema kształtami tekstowymi w obrębie pliku:

1. deklaracja z nazwą typu, także niewymagalną: `LineRoute route`, `TelemetryTrack? _track`;
2. `var x = new D(…)` albo `var x = D.…`;
3. `out D x`;
4. `var x = Pomocnik()`, gdy `Pomocnik` jest **w tym pliku** zadeklarowany jako
   zwracający `D`.

Kształt czwarty dopisałem po pomiarze, bo bez niego `SignallingAssumption` miał
**zero** wołań przy dziesięciu odrzuconych — a dwa z tych dziesięciu to
`var plan = PackageAPlan()`, czyli odbiorca właściwego typu. Kształt trzeci i drugi
też są poprawkami po pomiarze; kształt pierwszy w wersji bez `?` gubił `_track`.
**Każda z tych poprawek ma nazwany przypadek, który ją wymusił**, i żadna nie została
dobrana pod liczbę.

Czego te kształty **nie** widzą: odbiorcy przekazanego przez łańcuch wywołań spoza
pliku. Granica jest znana i nieusunięta — usunęłoby ją dopiero to, czego pole „Poza
zakresem" zabrania.

## 3. Postać odbioru, dla każdego z siedmiu

Klasy ustalone przed liczeniem, z jedną poprawką kolejności opisaną w §4:

* **V** — element odbiera coś **niejawnie typowanego**: `foreach (var x in …)`,
  `var x = …`, parametr lambdy.
* **E** — **żadnej zmiennej ani lambdy**: składowa czytana wprost z wyrażenia,
  `day.Blocks[0].Trips`.
* **N** — wołający po element **nie sięga**: samo `.Count`, przekazanie dalej.

| typ elementu | kolizja nazwy | wołań | postacie odbioru |
|---|---|---|---|
| `BrakingReferenceRow` | nie | 3 | V1 `foreach` z `var` ×1, V4 `var` z wyrażenia ×2 |
| `CbtcDynamicTestSite` | nie | 2 | V1 ×1, V4 ×1 |
| `RouteStation` | TAK | 7 | **E3 indeksowanie i składowa wprost ×4**, V4 ×3 |
| `ServiceBlock` | TAK | 3 | **E3 ×3 — i nic więcej** |
| `SignallingAssumption` | TAK | 2 | V1 ×1, V4 ×1 |
| `TelemetrySample` | TAK | 12 | E3 ×3, N6 ×7, V4 ×2 |
| `ViewAssumption` | TAK | 5 | V1 ×3, V4 ×2 |

Postaci, których **nie znalazłem**: dekonstrukcja `foreach (var (a, b) in …)`,
wzorzec pozycyjny w `switch`/`is`, `foreach` z wypisaną nazwą typu. Przy wzorcu
pozycyjnym mówię „nie znalazłem wzorcem", a nie „nie ma": to granica przyrządu,
tak jak zapisałem w warunku przed pomiarem.

## 4. Odpowiedź na pytanie pola „Skończone, gdy": klasa PIĄTA, dla JEDNEGO z siedmiu

```
ma postac V (cos niejawnie typowanego odbiera element): 6  z 7
ma postac E (ZADNEJ zmiennej ani lambdy):               3  z 7
WYLACZNIE E — poza droga `var` z 6.D298:                1  z 7   ServiceBlock
wylacznie N — nigdy nie siega po element:               0  z 7
```

`ServiceBlock` jest odbierany **wyłącznie** jako `day.Blocks[0].LastArrivalS` —
indeksowanie i składowa wprost, bez ani jednej zmiennej. To **nie jest** droga
`var`: żadna zmienna nie powstaje, więc nie ma czego typować niejawnie. Nazwa typu
nie pada nie dlatego, że ktoś napisał `var`, tylko dlatego, że **nikt nie napisał
nic**.

**Przewidziałem zero takich przypadków i to przewidywanie jest OBALONE.**

Czego to **nie** podważa: rozstrzygnięcia 6.D298 o pokryciu. Tamta pozycja definiowała
czwartą drogę po stronie **producenta** — „typ stoi w pozycji zwracanej publicznego
składnika innego typu" — i `ServiceBlock` tę definicję spełnia. Obalona jest **glosa**,
którą droga nosi w nazwie: „wołający piszą `var`". Dla jednego z siedmiu wołający nie
pisze `var`.

**Szukałem zdania do poprawienia w kodzie i nie znalazłem.** Komentarz przy
`NIEWOLANE_PO_NAZWIE` w `tools/tests/test_csharp_type_callers.py` mówi „wołający piszą
`var`" o **dwóch wymienionych z nazwy** typach (`BrakingRunResult`, `RegistryEntry`),
a nie o siódemce — więc jest prawdziwy i zostaje nietknięty. Glosa, która nie
wytrzymała pomiaru, stoi w prozie pozycji kolejki, a nie w bramce.

## 5. Kontrola przyrządu — zdana

Pole „Weryfikacja" żąda, by typ zwracany pojedynczo i konsumowany przez `var` wyszedł
w klasie `var`, a nie w nowej. Wyszedł: `BrakingReferenceRow` i `CbtcDynamicTestSite`
— oba o **jednoznacznej** nazwie składnika, więc wiązanie odbiorcy ich nie dotyczy —
mają wyłącznie postaci V. Czytnik odtworzył przypisanie, które 6.D234 zrobiło ręką.

```
python3 tools/tests/test_all.py test_csharp_type_callers.py
  10/10 przeszło
```

## 6. Przewidywania spisane PRZED pomiarem

| # | przewidywanie | wynik |
|---|---|---|
| 1 | `foreach` z `var` dominuje, 5–7 z siedmiu | **pudło** — 4 z siedmiu |
| 2 | dekonstrukcja 0–1 | trafione (0) |
| 3 | indeksowanie 2–5 | trafione (3) |
| 4 | LINQ 1–4 | trafione (4) |
| 5 | wzorzec pozycyjny 0 | trafione, z zastrzeżeniem granicy przyrządu |
| 6 | każdy z siedmiu ma wołającego | trafione — ale dopiero po czwartym kształcie wiązania |
| 7 | zero poza czterema drogami 6.D298 | **OBALONE** — jeden, `ServiceBlock` |
| 8 | co najmniej jeden typ ma więcej niż jedną postać | trafione (sześć z siedmiu) |
| 9 | wołających z `tests/` więcej niż z `src/` dla ≥ 4 z siedmiu | trafione (6 z 7) |

Siedem trafionych, jedno pudło, jedno obalone. **Obalone jest to, które przepisałem
z wyniku poprzedniej pozycji zamiast wyprowadzić z kodu** — dokładnie ten sam kształt
pomyłki co przy 6.D297, gdzie obalone okazało się jedyne przewidywanie przepisane
z bloku. Dwa razy z rzędu myli się to, czego nie policzyłem sam.

## 7. Czego świadomie nie zrobiono

- **Nie usunięto ani nie podłączono żadnego typu** — pozycja LICZY.
- **Nie napisano analizatora symboli**, choć §2 pokazuje dokładnie, ile kosztuje jego
  brak. Pole „Poza zakresem" zabrania, a granica jest opisana, nie ukryta.
- **Nie zmieniono rozbioru deklaracji** — `TYP` pożyczony, nietknięty.
- **Nie poprawiono komentarza przy `NIEWOLANE_PO_NAZWIE`** — §4 mówi dlaczego:
  sprawdziłem go i jest prawdziwy.
- **Nie tknięto `data/` ani `src/`.**

## 8. Zauważone przy okazji, nietknięte

Cztery typy deklarują składnik `Assumptions`, a każdy zwraca **inny** typ elementu
(`BrakingAssumption`, `ScenarioAssumption` dwa razy, `SignallingAssumption`). Żadna
bramka nie liczy dziś, ile nazw składników publicznych `src/` koliduje między typami
ani ile z tych kolizji zwraca różne typy. Przy 6.D298 zmierzyłem, że pomylenie
przypięcia z cytatem zmienia odpowiedź dziesięciokrotnie; tutaj pomylenie składnika
z cudzym składnikiem o tej samej nazwie zmienia ją **sześciokrotnie** (34 wobec 227).
Ile takich kolizji jest w całym `src/`, ta pozycja nie pyta.
