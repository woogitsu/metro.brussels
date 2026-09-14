# MB-03 — HUD mówi, DLACZEGO pociąg nie rusza, a cel stoi przed kilometrażem

**14.09.2026**, na `dfcdfc4`. Wejście: `src/Game/UI/Hud.cs`, `src/Game/UI/UiText.cs`,
`src/Game/Scenes/FirstRun.tscn`, `src/Sim/Train/StationStop.cs`, `DoorCycle.cs`,
`src/Sim/Signalling/TrainProtection.cs`, `CabProtection.cs`, wynik MB-02.

## 1. Czym ta pozycja JEST, a czym nie — bo audyt się tu mylił

Audyt opisywał HUD jako „tekstowy diagnostyczny i pomoc klawiszową" i wyprowadzał
z tego potrzebę **dodania** celu i odległości. Pomiar mówi co innego i mówił to już
przy wpisywaniu pozycji: **obie te rzeczy były.** Wiersz `Position` niósł nazwę
następnej stacji i odległość, wiersz `Station` — odległość do punktu zatrzymania
z oknem ±, fazę drzwi, resztę postoju, błąd zatrzymania i liczniki.

Ta pozycja jest więc o **priorytecie**, nie o informacji. Co widać na pierwszy rzut
oka, co dopiero na postoju, a co jest współrzędną dewelopera.

## 2. Co weszło

| plik | co |
|---|---|
| `src/Game/UI/TractionBlock.cs` | **nowy**, bez Godota: `Blocked(…)` i `Line(…)` |
| `src/Game/UI/UiText.cs` | `hud.speed` + trzy klucze `hud.traction.*` |
| `src/Game/UI/Hud.cs` | dziewiąta etykieta `Traction`, argument `speedLimitKmh`, wiersz prędkości z katalogu |
| `src/Game/Scenes/FirstRun.tscn` | `Traction` pod `Speed`; `Station` **przed** `Position` |
| `src/Game/FirstRun.cs` | `TractionLine()` i jedna zmiana w wywołaniu `_hud.Update` |
| `tests/Game.Tests/TractionBlockTests.cs` | **nowy**, cztery metody |

## 3. Blokada trakcji ma DOKŁADNIE DWA źródła i to jest sprawdzone, nie założone

`grep` po całym `src/Sim/` pod obniżenie nastawnika daje dwa miejsca:

1. **Drzwi** — `StationStop.cs:84-86`, jedyne `requested with { Throttle = 0.0 }`;
   warunek w `DoorCycle.cs:151` (`phase == DoorPhase.Closed`).
2. **Ochrona pociągu** — `TrainProtection.cs:108-114`, ramiona `ServiceIntervention`
   i `EmergencyIntervention` podmieniają całe polecenie.

**Trzeciego nie ma, a ograniczenie prędkości nim NIE JEST:** `TrainController.Advance`
obcina PRĘDKOŚĆ po kroku (`TrainController.cs:128-130`) i nastawnika nie rusza.

**Kolejność ramion jest kolejnością filtrów, a nie gustem.** `FirstRun.StepOnce` woła
filtr stacji, a ochronę **ostatnią** — z jawnym uzasadnieniem w komentarzu (kryterium
Issue #26: „nie można ominąć ATP przez input gracza"). Gdy blokują obie, poleceniem
kontrolera rządzi ochrona, więc to ona jest nazywana. Odwrotna kolejność kazałaby
graczowi zamknąć drzwi, podczas gdy hamuje za niego ATP.

**Dlaczego to nie jest drugie źródło prawdy.** `TractionBlock` niczego nie liczy: pyta
dwóch właścicieli o ich stan **z tego samego kroku** i wybiera nazwę. Że jego odpowiedź
zgadza się z tym, co filtry naprawdę robią, nie jest twierdzeniem — jest bramką, która
**uruchamia oba filtry** na siatce 7 faz × 3 reakcje = 21 par (20 z blokadą)
i porównuje wyniki. Uproszczonego `v²/2a` nie ma nigdzie; pole „Czego NIE wolno zrobić"
zakazywało go wprost.

## 4. Pięć kontroli negatywnych, baza 285/618 — i JEDNA ZIELONA, która znalazła lukę

| kontrola | podstawienie | wynik |
|---|---|---|
| KN-1 | zamieniona kolejność ramion (drzwi przed ATP) | 279/284 |
| KN-2 | `Blocked` bez ramienia ATP | 283/284 |
| KN-3 | jeden znak w `hud.traction.doors` (ta sama długość) | 283/284 |
| KN-4 | `_traction.Visible = true` — wiersz widoczny ZAWSZE | **284/284 ZIELONA** |
| KN-4b | to samo, po dołożeniu bramki | **284/285** |
| KN-5 | wiersz prędkości wraca do ciała `Hud.Update` | 276/284 |

`md5sum -c` na trzech plikach po każdej: `OK`.

### 4.1. KN-4 — „milczenie znaczy jedź" nie było pilnowane przez nic

Kontrola podstawiła wiersz blokady widoczny przez cały przejazd i **zestaw został
zielony**. Powód jest zmierzony, a nie domyślony: wszystkie przypisania `Visible` stoją
w węźle Godota, którego żaden test jednostkowy nie zbuduje — to samo ograniczenie, które
wypchnęło z `FirstRun` `RunReset`, `RunHeader` i `RunPlan`, a którego **nie da się**
wypchnąć dla polityki widoczności, bo ona jest właśnie ustawianiem pól węzła.

**Dlaczego to nie jest kosmetyka.** W tej pozycji milczenie wiersza ZNACZY „jedź" —
wiersz pojawia się wtedy i tylko wtedy, gdy gracz ciągnie i nic się nie dzieje. Wiersz
widoczny zawsze zajmuje pasmo pierwsze, nie niosąc niczego, czyli odbiera całej pozycji
jej treść.

Doszła bramka leksykalna — jedyna droga, jaka tu jest: **każdy wiersz, który może
milczeć, chowa się po długości WŁASNEGO napisu**, a trzy widoczne zawsze (`_speed`,
`_position`, `_controls`) są wymienione **z nazwy**, żeby lista nie mogła opisywać
dowolnego podzbioru. Po niej KN-4 zapala się: 284/285.

## 5. Trzy zapadki SPADŁY i każdy spadek jest wynikiem pożądanym

Wiersz prędkości był do tego dnia **jedynym**, który składał się interpolacją wprost
w ciele `Hud.Update` — czyli jedynym, który omijał katalog. Po przeniesieniu do `UiText`:

| zapadka | było | jest | dlaczego spadła |
|---|---|---|---|
| `DziurNaEkranie` | 20 | **18** | dwie dziury interpolacji zniknęły, a na ich miejsce weszły pola szablonu, czyli literały |
| `LiteralowZKlamra` | 129 | **128** | ten literał przestał istnieć w kodzie |
| `ZabranychWszystkieSlowa` | 14 | **13** | zostawiał po zdjęciu jednostek samo `a`, więc tracił ostatnie słowo |
| `ZabranychNaDrodzeNaEkran` | 4 | **3** | ten sam literał; trzy, które zostają, to dziury złożone wyłącznie z interpolacji |
| `WerdyktowZabranychPrzezZdejmowanie` | 2 | **1** | zostaje `Esc`, czyli NAZWA KLAWISZA, a nie tekst dla gracza |

Zapadki równościowe pokazują te spadki i to jest ich treść: gdyby ktoś złożył wiersz
prędkości z powrotem w kodzie, liczby wróciłyby i testy by o tym powiedziały (KN-5).

### 5.1. Jedna bramka wymagała PRZEPISANIA, nie przeliczenia

`Zdejmowanie_jednostek_kosztuje_dwa_werdykty…` szukała „drugiego z dwóch" przez
`zabrane.Single(l => l != "Esc")` i sprawdzała, że stoi on w ciele `Hud.Update`.
Drugiego nie ma — `Single` **rzucałby wyjątkiem** zamiast powiedzieć, co się zmieniło.

Pytanie zostało to samo, tylko zadane właściwej stronie: wiersz prędkości ma dalej nieść
symbol przyspieszenia i nic poza nim ponad słowa katalogu. Bierzemy go stamtąd, gdzie
teraz mieszka, i sprawdzamy, że do ciała `Hud.Update` nie wrócił.

**Resztka brzmi `ufita`, i to jest wynik przyrządu, a nie oczekiwanie.** `sufit` traci
literę `s`, bo `s` **jest jednostką** i sito zjada ją także w środku wyrazu; do tego
skleja się `a` od `a =`. Wpisanie `sufita` byłoby zgadywaniem.

**Słowo brzmi `sufit`, nie `limit`, i to nie jest wybór estetyczny:** to słowo, którego
repozytorium już używa na tę wielkość (wiersz `[LIMIT] … sufit maszynisty`).

## 6. Rzeczywiste wyjście weryfikacji

```
$ dotnet test tests/Game.Tests   → 285/285
$ dotnet test tests/Sim.Tests    → 618/618
$ python3 tools/tests/test_all.py
  RAZEM …, 2461 testów, 125 modułów
  2461/2461 przeszło
```

Scena z dziewięcioma wierszami HUD-u przejeżdża pakiet A bez ani jednego ostrzeżenia:

```
[ODTWORZENIE] koniec: kroków=20000 t=166.667 s chainage=1451.513 m droga=1357.513 m
[SESJA] zaliczone (AllTargetsServed): 2/2 celów, 156.842 s, 1357.513 m, ATP 0/0/0 …
[OSTRZEŻENIA] run.log: 0 spoza listy, 0 środowiskowych
```

**Co ten przebieg dowodzi, a czego NIE:** dowodzi, że scena z nową etykietą działa
i że MB-02 nie ucierpiało. **Nie dowodzi niczego o wyglądzie HUD-u** — HUD nie trafia
do logu, a klatki są osobnym problemem (§7).

## 7. Czego świadomie NIE zrobiłem — trzy rzeczy z pola „Wyjście"

1. **Oględzin rzeczywistych klatek w 1280×720 i 1920×1080.** Pole „Weryfikacja" żąda
   ich wprost i **nie da się ich dziś wykonać**: `--shot` przełącza przebieg w tryb
   SKRYPTOWY (`RunPlan.cs` → `Mode = "shot"`), a w nim `_stations` w ogóle nie powstaje
   i wiersz pomocy jest ukryty świadomie; `--shot` nie łączy się też z `--replay`.
   Klatki możliwe headless **nie pokazują tego, co ta pozycja zmienia** — ani mnie bez
   ekranu, ani CI. Czy `--shot` ma działać w trybie ręcznym (i co to robi z progami
   `tools/visual/compare.py --set godot`), jest **decyzją właściciela** i tak ją zapisuję.
2. **Panelu pauzy.** Pauzy nie ma — nie było jej w kryteriach MB-02 i wymaga nowego
   klawisza.
3. **Przełącznika diagnostyki.** Wymaga nowego klawisza, czyli nowego wiersza
   w `DriverActions.All`, nowego przypisania w `project.godot` i przeliczenia
   `DriverActionsTests`. **Wybór klawisza jest decyzją właściciela** (`CLAUDE.md` §8),
   więc pasmo trzecie jest dziś ustawione KOLEJNOŚCIĄ, a nie schowane.

**Pole „Skończone, gdy" mówi też: „nowy gracz wykonuje pierwszą próbę bez czytania
README".** To jest kryterium playtestu i nie zamknie go żaden agent — tak je oznaczam.

## 8. Zauważone po drodze, nie tknięte

- **`PlikowWZasieguBramki` (21) i `RoznychLiteralowWZasieguBramki` (362) to dolne
  ostrza**, więc nowy plik ich nie zapala i wpisane liczby starzeją się po cichu.
  Po tej zmianie jest **22 pliki**; liczby różnych nie mierzyłem, bo próg tego nie żąda.
- **Najdłuższe wiersze treningu to `Controls` (do 166 znaków z hamulcem awaryjnym)
  i `Signalling` (do 150), a żaden z nich nie zawija** — zawija `Position`, `Station`,
  `Traction` i `Summary`. Po przesunięciu obu do pasma trzeciego pytanie zmienia sens,
  więc odpowiedź na nie należy do kroku z oględzinami.
- **Pomiar 6.D82 i `HudLayoutTests.cs:168` stoją na `Name` (37 znaków), a trening bierze
  `DisplayName`**, którego maksimum w `data/track/` to **18 znaków**
  (`Hotel Des Monnaies`). Bramka szerokości mierzy więc przypadek, którego tryb ręczny
  nie osiąga.
