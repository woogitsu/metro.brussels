# 6.D183 — na ekran dociera 22 napisy ze słowem, a rodzina z 6.D175 mogła znaleźć najwyżej 7 z nich

**12.09.2026**, na `3d278bb`. Wejście: `src/Game/FirstRun.cs`, `src/Game/UI/Hud.cs`,
`src/Game/SignallingHud.cs`, `src/Game/RunPlan.cs`, `src/Game/World/ChaseCameraAim.cs`,
`src/Game/Input/DriverActions.cs`, `src/Game/Input/DriverInput.cs`,
`src/Game/Input/EmergencyBrake.cs`, `tests/Game.Tests/UiTextTests.cs`.
Pozycja żądała: prześledzić **każdy** argument `Hud.Update` do źródeł i policzyć, ile
literałów tą drogą dociera na ekran — **niezależnie od tego, jak wyglądają**.

## 1. Przesłanka pozycji jest PRAWDZIWA i to jest zmierzone, nie założone

Pole „Skąd" mówi, że jedynym sprawdzalnym kryterium „tekst dla gracza" jest **droga
wywołania** do `_hud.Update`. Zdanie to jest prawdziwe **tylko wtedy**, gdy nic innego
po ekranie nie pisze. Skan wszystkich `\w+\.Text\s*=` w `src/Game/`:

```
przypisań `.Text =` w src/Game/: 7
poza ciałem Hud.Update:          0
```

Wszystkie siedem stoi w `Hud.Update`. **To pierwszy raz, kiedy ta przesłanka została
wykonana, a nie przyjęta** — i stoi odtąd jako bramka
`Kazde_przypisanie_Text_stoi_w_ciele_Hud_Update`, z dolnym ostrzem na sam skan, żeby
literówka we wzorcu nie dała „zero poza ciałem" z pustej listy.

Inaczej niż przy 6.D142, 6.D147 czy 6.D152, gdzie przesłanka pozycji padała —
tu **się utrzymała**.

## 2. GŁÓWNY WYNIK

Prześledzenie wszystkich **siedmiu** argumentów napisowych `Hud.Update`
(`nextStation`, `mode`, `station`, `signalling`, `view`, `emergency`, `help`) przez
**20 członów w 8 plikach**, plus samo ciało `Hud.Update`:

| liczba | co znaczy |
|---|---|
| **74** | literałów dociera na ekran drogą `Hud.Update` |
| **28** | z nich to KLUCZE katalogu — tym, co widzi gracz, jest wtedy wpis `UiText`, nie ten napis |
| **46** | to napisy stojące w KODZIE |
| **22** | z tych 46 niesie SŁOWO w rozumieniu bramki (`BezJednostek(BezDziur(l))` wobec `\p{L}{2,}`) |
| **7** | z tych 22 ma polski znak diakrytyczny |

**Odpowiedź pozycji: tekstu dla gracza wpisanego w kod jest 22, nie trzy i nie cztery.**

### 2.1. Dlaczego 6.D175 zobaczyło trzy

6.D175 mierzyło rodzinę **„literał z polskim znakiem diakrytycznym"** i odpowiedziało
„trzy ze 140". Odpowiedź była poprawna dla tej rodziny. Ale z 22 napisów docierających
na ekran znak diakrytyczny ma **siedem** — więc **tamta rodzina mogła znaleźć najwyżej
siedem, a piętnastu nie mogła znaleźć nigdy**, bez względu na to, jak dokładnie by
liczyła.

`koniec pakietu` z 6.D179 **nie był wyjątkiem, tylko przypadkiem większościowym.**
Piętnaście napisów bez znaku diakrytycznego, wszystkie na ekranie:

```
koniec pakietu
manual                                               (×2: pole i RunPlan.Mode)
from-telemetry · replay · telemetry · shot · line
bez sygnalizacji — przejazd bez blokad (podaj --signalling)
sygnalizacja: przed pierwszym krokiem
  PRZEKROCZENIE
  ATP HAMUJE: {decision.Action} {…:F2} m/s²
v_dop {…} km/h
autorytet {…} m ({authority.Reason}, blok {…})
, jeszcze {RemainingM:F1} m
```

Dwa z nich — `bez sygnalizacji — przejazd bez blokad (podaj --signalling)`
i `sygnalizacja: przed pierwszym krokiem` — to napisy, które 6.D175 miało **w ręku**
jako rodzinę `SignallingHud`, a do swojej liczby „trzy" nie wliczyło, bo znaku
diakrytycznego nie mają. Myślnik `—` znakiem diakrytycznym nie jest.

### 2.2. Rodzina, o której nie wiedział nikt: `ChaseCameraAim.Reason`

Argument `view` idzie z `_viewLine`, a ten z `ChaseCameraAim.Reason` —
i **cała ta metoda buduje polskie zdania z literałów w kodzie**, z pominięciem
katalogu:

```
, jeszcze {RemainingM:F1} m
pasmo ukrycia z decyzji właściciela
kamera siedzi w skorupie składu
widok chase niedostępny — {powod};
dostępny po minięciu {FromChainageM:F1} m{ile}
```

**Pięć napisów, wszystkie widziane przez gracza, żaden nie był dotąd wymieniony
w żadnej pozycji.** Cztery mają znak diakrytyczny, więc stały w tamtych 140 — ale
6.D175 nie prześledziło argumentu `view` i dlatego ich nie znalazło. Nie jest to
usterka sita: jest to **skutek mierzenia rodziny zamiast drogi**.

## 3. Trasa, argument po argumencie

| argument | droga | literałów | z czego |
|---|---|---|---|
| `nextStation` | `UpdateHud()` → zmienna `name`; inaczej nazwa stacji z `data/network/` | 1 | `koniec pakietu` |
| `mode` | pole `_mode` ← `RunPlan.Mode` | 7 | 6 nazw trybów + domyślne `manual` |
| `station` | `StationLine()` → `UiText.Format`, `Faza()` → `UiText.Get` | 23 | **17 kluczy**, 6 formatów liczb |
| `signalling` | `SignallingLine()` → 4 stałe `SignallingHud` albo `SignallingHud.Line()` | 10 | 4 zdania + 6 członów szablonu |
| `view` | `_viewLine` ← `ChaseCameraAim.Reason` | 5 | 5 zdań po polsku, §2.2 |
| `emergency` | `EmergencyBrake.Notice()` → `UiText.Format` | 2 | 1 klucz, 1 format |
| `help` | `HelpLine()` → `DriverInput.Help` → `DriverActions.Help` / `BuildCoreDrivesHelp()` | 17 | 8 kluczy, 5 nazw klawiszy, 3 rozdzielacze, szablony |
| *(samo `Hud.Update`)* | szablony prędkości, pozycji i sterowania | 9 | 2 klucze, wiersz jednostek, formaty |

Suma **74**. Mapa stoi w `ZrodlaHud` i jest **wpisana, nie wyprowadzona** — prześledzenie
wartości przez pola, właściwości i metody w ośmiu plikach to analiza przepływu, a ta
wymaga rozbioru składni C#, czyli zależności, przed którą `CLAUDE.md` §8 każe przerwać.
Mapa nie jest jednak gołym twierdzeniem: pilnują jej dwie bramki z §1 i §5.

## 4. ZNALEZIONE PO DRODZE: na ekran docierają NAZWY CZŁONÓW WYLICZEŃ, a literałami nie są

Trzy miejsca wstawiają do napisu wartość `enum`, więc na HUD trafia **nazwa członu**:

| gdzie | typ | co widzi gracz |
|---|---|---|
| `SignallingHud.Line` — `({authority.Reason}, blok …)` | `AuthorityLimit` | `EndOfLine`, `OccupiedBlock`, `ReservedByOtherRoute`, `BlockNotReserved` |
| `SignallingHud.Line` — `ATP HAMUJE: {decision.Action}` | `ProtectionAction` | `None`, `ServiceIntervention`, `EmergencyIntervention` |
| `FirstRun.Faza` — gałąź `_ => phase.ToString()` | `DoorPhase` | nazwa członu, gdy dojdzie ósma faza |

**Dziesięć angielskich identyfikatorów na polskim HUD-zie** — i **żadna rodzina liczona
po literałach nie może ich zobaczyć, bo literałami nie są.** Dwa z trzech typów mieszkają
w `src/Sim/`, czyli **poza korpusem bramki**, który kończy się na `src/Game/`.

Tego nie ruszam: pole „Poza zakresem" 6.D183 zabrania zmiany zachowania HUD-u,
a `src/Sim/` nie jest nawet w jego wejściu. Wpisane jako **6.D185**.

## 5. Bramki — trzy, każda odpowiada na inne pytanie

| test | co pilnuje |
|---|---|
| `Kazde_przypisanie_Text_stoi_w_ciele_Hud_Update` | że droga na ekran jest JEDNA — przesłanka pozycji |
| `Kazdy_argument_napisowy_Hud_Update_ma_zrodlo` | że mapa nie zestarzała się — ósmy argument ją zapala |
| `Literaly_docierajace_na_ekran_droga_Hud_Update` | 74 / 28 / 22 / 7 oraz obecność pięciu znanych napisów |

Ostatnia sprawdza wprost to, czego żądało pole „Weryfikacja": **jeśli na liście nie ma
znanych napisów, prześledzenie pominęło argument.**

## 6. `CialoDeklaracji` — nowy czytnik ciała członu i powód, dla którego jest osobny

`CialoMetody` rozstrzyga formę po tym, co stoi pierwsze: `{` czy `;`. Na członie
`public static string Help { get; } = string.Join(…);` obie odpowiedzi są złe — `{`
stoi przed `;`, więc dostaje `{ get; }` i **gubi cały inicjalizator**, w którym stoi
szablon. `CialoDeklaracji` dokłada jedną regułę: po domknięciu klamry, jeśli zaraz za
nią stoi `=`, ciągnij do średnika na głębokości zero.

Średników i klamer szuka przez `PominNieNapis` i `CzytajLiteral` — **te same prymitywy,
które postawiło wczorajsze 6.D182**. Bez nich średnik ze środka napisu
(`"+0.00;-0.00;0.00"` w `BladZatrzymaniaFormat`) kończyłby deklarację w złym miejscu.
Jest to pierwszy pożytek z tamtej naprawy poza nią samą.

## 7. Kontrole negatywne — pięć, wszystkie czerwone

Baza: **243/243**. Każda zmienia **jedną** rzecz, po każdej `md5sum -c: OK`.

| | co zmienione | wynik |
|---|---|---|
| KN-1 | z mapy `ZrodlaHud` zdjęty jeden człon (`NotOnPlanYet`) | **242/243** |
| KN-2 | ciało `Hud.Update` podstawione puste | **242/243** |
| KN-3 | `CialoDeklaracji` bez ciągnięcia za `{ get; } =` | **242/243** |
| KN-4 | sito słowa bez `BezDziur`/`BezJednostek` | **242/243** |
| KN-5 | jeden argument zdjęty z `ArgumentyNapisoweHud` | **242/243** |

**KN-3 za pierwszym razem wyszła ZIELONA i nie znaczyła nic** — podstawienie nie weszło
przez cytowanie apostrofu w powłoce. **Jest to DRUGI raz w dwóch pozycjach pod rząd**
(przy 6.D182 tak samo padła KN-5) i dlatego stoi tu osobnym zdaniem, a nie w przypisie:
kontrola, której podstawienie nie weszło, wygląda **dokładnie** jak kontrola, której
mechanizm nie działa. Jedyne, co je rozróżnia, to `diff` z kopią roboczą robiony
**po podstawieniu, a przed przebiegiem** — i on je za każdym razem rozróżnił.

## 8. Czego świadomie nie zrobiłem

- **Nie przeniosłem niczego do katalogu `UiText`** — pole „Poza zakresem" zabrania
  wprost; to osobna robota, zależna od tej liczby.
- **Nie tknąłem `src/Game/`.** Wszystkie 22 napisy zostają tam, gdzie stoją.
- **Nie policzyłem nazw członów wyliczeń do 22** — nie są literałami, a pozycja pyta
  o literały. Stoją w §4 i w nowej pozycji.
- **Nie prześledziłem, które nazwy stacji z `data/network/` docierają przez
  `nextStation`** — to dane, nie kod, i pozycja o nie nie pyta.
