# 6.D197 — jeden switch po wyliczeniu i jest nim ten już przybity

**13.09.2026**, na `91c509e`. Wejście: `src/Game/` (wszystkie pliki poza `.godot/`),
`src/Sim/` jako słownik typów wyliczeniowych, `tests/Game.Tests/UiTextTests.cs`
(sekcja 6.D185), `reports/6d185-nazwy-czlonow-na-ekranie.md` §3.

## 1. Odpowiedź: JEDEN, i bramka z 6.D185 jest CAŁYM ZBIOREM

W całym `src/Game/` (22 pliki `.cs`) są **dwa** konstrukty `switch`, **zero** etykiet
`case`/`default:` — i **dokładnie jeden switch po wartości wyliczeniowej**:
`FirstRun.Faza`, ten sam, który 6.D185 przybiło ręcznie.

Bramka z 6.D185 **nie jest próbką z większego zbioru. Jest całym zbiorem** dla tego
korpusu.

## 2. Przesłanka pozycji nie trzymała się co do OBU przykładów

Pozycja pisała, że `src/Game/` niesie co najmniej `ViewKind` (w `FirstRun.cs`)
i `ProtectionVariant` (w `src/Game/World/TunnelView.cs` oraz
`src/Game/Assets/ChunkManifest.cs`).

| przykład z pozycji | co jest naprawdę |
|---|---|
| `ViewKind` | switch stoi w `RunPlan.cs:619` i idzie po **NAPISIE**: `var view = Argument(arguments, "view") ?? "cab"`, a ramiona to literały `"chase"/"outside"/"inspect"` |
| `ProtectionVariant` | jego switch stoi w **`src/Sim/Signalling/SignallingPlan.cs:654`**, poza korpusem tej pozycji. Oba pliki wskazane przez pozycję **istnieją**, ale nazwy `ProtectionVariant` nie ma w nich **ani razu** — a jedyne wystąpienie liter `switch` w tej parze to klucz JSON `"switch_distance_m"` w `ChunkManifest.cs:204`, czyli literał |

**Pierwszy z nich jest przy tym trafieniem fałszywym, które projekt już raz zmierzył:**
`view` jest nazwą, pod którą w `src/` stoi również wartość `ViewKind`
(`RunHeader.cs:175`), więc rozstrzyganie typu **po nazwie zmiennej** daje tu fałsz —
i dokładnie to 6.D185 wpisało do `FalszyweTrafieniaSkanu` jako `RunPlan.cs:view`.
Skan tej pozycji rozstrzyga więc **po kształcie ramion** (`Typ.Człon =>`), nie po nazwie,
a KN-3 pokazuje, co się dzieje po przełączeniu na nazwę.

## 3. Rozstrzygnięcie: bramka JEDNA, bez uogólniania — i to nie jest zaniechanie

Pole pozycji ostrzegało wprost: **„uogólnić bramkę NIE jest odpowiedzią domyślną"**,
bo ramię domyślne bywa jedynym sensownym zachowaniem, a zapadka postawiona na `switch`,
który ma prawo mieć je żywe, byłaby sitem, które nic nie chroni.

Przy **jednym** wystąpieniu uogólnienie nie ma nad czym uogólniać. Zostaje więc
**liczba**: `SwitchyPoWyliczeniuWGame = 1`, `SwitchyWGameRazem = 2`,
`SwitchyInstrukcyjnychWGame = 0`. Gdy pojawi się drugi switch po wyliczeniu, asercja go
pokaże — i **dopiero wtedy jest o czym rozstrzygać**.

Trzy liczby, a nie jedna, bo „jeden po wyliczeniu" nie mówi nic o tym, ile switchy jest
w ogóle. Bez `SwitchyWGameRazem` skan, który przestałby cokolwiek znajdować, dałby jeden
i przeszedłby.

## 4. Sześć kontroli negatywnych, baza 262/262

| kontrola | podstawienie | wynik |
|---|---|---|
| KN-1 | drugi switch po wyliczeniu — **nie kompilował się** | — |
| KN-1b | to samo, składniowo poprawne | **6 czerwonych** |
| KN-2 | czytnik ślepy na postać wyrażeniową | 261/262 |
| KN-3 | rozstrzyganie po NAZWIE zmiennej zamiast po kształcie ramion | 261/262 |
| KN-4 | obcinacz komentarzy zdjęty | **262/262 ZIELONA** |
| KN-4b | słowo `switch` w komentarzu, po dołożeniu asercji | 261/262 |
| KN-5 | skan pomija `FirstRun.cs` (kontrola przyrządu) | 261/262 |

**KN-1b zapala SZEŚĆ testów, nie jeden** — bo dołożenie literałów do `src/Game/` rusza
przypięte liczby pięciu innych bramek. Drzewo jest tu gęściej zapadkowane, niż wygląda.

**KN-4 wyszła ZIELONA i sprawdziłem, dlaczego, zamiast dokładać asercję na wyczucie.**
Zmierzone na całym korpusie:

```
plikow .cs w src/Game/: 22
  postac wyrazeniowa : surowo 2, po masce 2
  postac instrukcyjna: surowo 0, po masce 0
```

**Obcinacz nie ma tu czego zdjąć, i to jest zdanie o KONSTRUKTACH, nie o literach.**
Liter `switch` jest w `src/Game/` **trzy** wystąpienia: dwa konstrukty (`RunPlan.cs:619`,
`FirstRun.cs:1803`) i jeden klucz JSON w literale — `"switch_distance_m"`
w `ChunkManifest.cs:204`. Tego trzeciego **żaden z dwóch czytników nie bierze za konstrukt**,
bo po słowie stoi podkreślenie, a nie klamra ani nawias — więc maska nie ma czego zmienić
i obie liczby wychodzą równe. Zieleń jest **poprawna**, a nie usterkowa. Zamiast ją przemilczeć,
zrobiłem z tej bezczynności rzecz **sprawdzaną**: asercja porównuje skan po źródle surowym
ze skanem po zdjęciu komentarzy i powie, **kiedy obcinacz przestanie być bezczynny**.
KN-4b to potwierdza — pierwsze `switch` w komentarzu rozjeżdża obie liczby i zapala bramkę.

Jest to trzeci raz w tej sesji, gdy zielona kontrola okazuje się **przewidywalna
i wytłumaczona**, a nie przeoczona (po KN-7b z 6.D195 i KN-6 z 6.D196) — i pierwszy, gdy
z wyjaśnienia wyszła **nowa asercja**, a nie tylko zapisana granica.

## 5. Czego świadomie nie zrobiłem

- **Bramki nie uogólniłem** — pole „Dlaczego «uogólnić bramkę» NIE jest odpowiedzią
  domyślną" i pomiar mówiący, że wystąpienie jest jedno.
- **Ramion do istniejących switchy nie dodawałem**, zachowania HUD-u nie zmieniałem,
  `src/Sim/` nie ruszałem — wszystko z pola „Poza zakresem".
- **`src/Sim/` nie zabramkowałem**, choć tam mechanizm siedzi naprawdę (§6). Korpusem
  tej pozycji jest `src/Game/`, a poszerzenie bez pytania byłoby poszerzeniem pozycji.

## 6. Zauważone po drodze, nie tknięte — i to jest ważniejsze od samej odpowiedzi

- **`src/Sim/Train/DoorCycle.cs:104` jest BLIŹNIAKIEM `FirstRun.Faza` co do KSZTAŁTU,
  ale NIE co do ryzyka — i tę różnicę zmierzyłem, zamiast ją przyjąć.** Ten sam
  `DoorPhase`, te same siedem ramion, to samo martwe ramię domyślne. Ale ramię domyślne
  `Faza` zwraca `phase.ToString()` — **cicho**, angielską nazwą na HUD — a ramię
  `PhaseSeconds` **rzuca** `ArgumentOutOfRangeException`. Ósmy człon `DoorPhase` ożywiłby
  oba, tylko że w rdzeniu **głośno**, a w grze **po cichu**. Bramka 6.D185 stoi więc
  dokładnie tam, gdzie mechanizm jest niewidzialny, i **to nie jest przeoczenie rdzenia**.
- **Rozkład ramion domyślnych w `src/Sim/` pokrywa się z POSTACIĄ `switch`-a co do
  jednego wystąpienia — 12 na 12.** Zmierzone: **8 postaci wyrażeniowej**
  (`DavisResistance.cs:38`, `ParameterStatus.cs:42`, `VehicleModel.cs:173` i `:181`,
  `ProtectionMode.cs:42`, `SignallingPlan.cs:654`, `TrainProtection.cs:108`,
  `DoorCycle.cs:104`) — **wszystkie osiem z ramieniem RZUCAJĄCYM i wszystkie osiem
  z ramieniem martwym**; **4 postaci instrukcyjnej** (`LineCore.cs:667`,
  `CabProtection.cs:211`, `FixedBlockSystem.cs:541`, `TrainProtection.cs:362`) —
  **wszystkie cztery z `default: break;`, wszystkie cztery żywe**. Cichych ramion
  domyślnych po wyliczeniu jest w `src/Sim/` **zero**; jedyne w drzewie stoi
  w `src/Game/FirstRun.cs:1803` i jest świadome.
- **Trzy z czterech żywych ramion połykają po JEDNYM członie i żadna liczba tego nie
  mówi:** `LineCore.cs:667`, `CabProtection.cs:211` i `TrainProtection.cs:362` obsługują
  **2 z 3** członów `ProtectionAction` (`None` wpada do `default`), a
  `FixedBlockSystem.cs:541` — **7 z 17** członów `SignallingEventKind`, czyli połyka
  **dziesięć**. Liczby 10 nie ma zapisanej nigdzie, więc osiemnasty człon wpadnie tam
  bez śladu.
- **Sito „po nazwie" myli się w tym drzewie na dwa dalsze, jeszcze niezapisane sposoby:**
  `ParameterStatus.cs:32` i `ProtectionMode.cs:33` przełączają po napisie, a parametr
  nazywa się `status` przy istniejących typach `ParameterStatus` i `ProtectionModeStatus`.
  `FalszyweTrafieniaSkanu` wymienia sześć trafień, wszystkie z `src/Game/` — te dwa leżą
  w `src/Sim/` i tamta bramka ich nie widzi.
- **`WyliczeniaZrodel()` w `UiTextTests.cs` NIE używa maski.** Dziś daje wynik identyczny
  z czytnikiem maskującym — sprawdzone znak w znak — bo jego sito członów odrzuca wiersze
  komentarza zaczynające się od `/`. Ale komentarz członu w **tym samym wierszu**
  (`Dry, // sucha`) przesunąłby oba czytniki względem siebie. **Zmierzone przy okazji:
  czytanie z tekstu SUROWEGO psuje 3 z 16 wyliczeń, a w DWÓCH z trzech zachowuje LICZBĘ
  członów i psuje tylko NAZWY** — bramka porównująca same liczby przeszłaby na zielono.
