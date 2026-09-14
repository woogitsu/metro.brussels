# 6.D210 — podział rozszedł się w jedną dobę, więc przybita jest inna rzecz

**14.09.2026**, na `7f15917`. Wejście: `src/Sim/**/*.cs`, `src/Game/FirstRun.cs`
(`Faza`), `tests/Game.Tests/UiTextTests.cs` (sekcje 6.D185 i 6.D197),
`reports/6d197-jeden-switch-i-to-ten-juz-przybity.md` §6.

## 1. Tabela czternastu switchy, której żądało pole „Wyjście"

| postać | miejsce | wyliczenie | pokrycie | ramię domyślne | żywotność |
|---|---|---|---:|---|---|
| wyrażeniowy | `Physics/DavisResistance.cs:38` | `TrackEnvironment` | 2/2 | `throw` | martwe |
| wyrażeniowy | `Physics/ParameterStatus.cs:42` | `ParameterStatus` | 4/4 | `throw` | martwe |
| wyrażeniowy | `Physics/VehicleModel.cs:173` | `TrainLoad` | 2/2 | `throw` | martwe |
| wyrażeniowy | `Physics/VehicleModel.cs:181` | `RailCondition` | 2/2 | `throw` | martwe |
| wyrażeniowy | `Signalling/ProtectionMode.cs:42` | `ProtectionModeStatus` | 3/3 | `throw` | martwe |
| wyrażeniowy | `Signalling/SignallingPlan.cs:654` | `ProtectionVariant` | 2/2 | `throw` | martwe |
| wyrażeniowy | `Signalling/TrainProtection.cs:108` | `ProtectionAction` | 3/3 | `throw` | martwe |
| wyrażeniowy | `Train/DoorCycle.cs:104` | `DoorPhase` | 7/7 | `throw` | martwe |
| wyrażeniowy | `Train/DoorControl.cs:75` | `DoorRefusal` | 6/6 | `throw` | martwe |
| **wyrażeniowy** | **`Train/StationStop.cs:252`** | `DoorPhase` | **5/7** | `throw` | **ŻYWE** |
| instrukcyjny | `Signalling/FixedBlockSystem.cs:541` | `SignallingEventKind` | 7/17 | `break;` | żywe |
| instrukcyjny | `Signalling/TrainProtection.cs:362` | `ProtectionAction` | 2/3 | `break;` | żywe |
| instrukcyjny | `Signalling/CabProtection.cs:211` | `ProtectionAction` | 2/3 | `break;` | żywe |
| instrukcyjny | `Line/LineCore.cs:881` | `ProtectionAction` | 2/3 | `break;` | żywe |

**10 wyrażeniowych, wszystkie rzucające. 4 instrukcyjne, wszystkie ciche.
9 martwych, 5 żywych.**

## 2. Para „postać ↔ martwota" ROZESZŁA SIĘ, i to w ciągu jednej doby

6.D197 zmierzyło 13.09.2026 zgodność **co do jednego wystąpienia**: osiem wyrażeniowych
— wszystkie rzucające i wszystkie **martwe**; cztery instrukcyjne — wszystkie ciche
i wszystkie **żywe**. Wyglądało to na regułę projektu.

Dzień później `StationStop.NextManualPhase` (MB-08, ten sam dzień) jest **wyrażeniowy,
rzucający i ŻYWY**: pokrywa **5 z 7** członów `DoorPhase` i rzuca dla pozostałych dwóch
świadomie — „Ta faza nie kończy się z upływem czasu". Kombinacji tej 13.09.2026
w drzewie **nie było**.

**To jest odpowiedź na pytanie pozycji.** Podział postaci nie jest regułą projektu, tylko
kształtem, który akurat wyszedł — i przestał wychodzić po jednym dniu pracy. Zapadka na
nim kazałaby dziś albo ją podnieść, albo przepisać regułę, a chroniłaby przed niczym
nazwanym. **Podział zostaje zapisany, nie przybity** — tak samo jak przy 6.D197.

Trzyma się natomiast para **postać ↔ treść ramienia**: 10/10 i 4/4. Ta zgodność też
jednak nie jest przybita, bo nie da się powiedzieć, przed czym miałaby bronić: rzucające
ramię w switchu instrukcyjnym nie jest usterką, tylko inną decyzją.

## 3. Co JEST przybite i dlaczego akurat to

**Ramię domyślne jednocześnie CICHE i MARTWE.** Cichy filtr przy pełnym pokryciu nie
odsiewa niczego, a gdy ktoś dopisze człon do wyliczenia, ten sam filtr połknie go **bez
słowa** — i dopiero wtedy zacznie szkodzić. Jest to jedyna z czterech kombinacji
(cisza × martwota), o której da się powiedzieć, przed czym bramka broni.

Dziś takich ramion jest **zero**, więc bramka stoi na zbiorze pustym i sama z siebie nic
nie znaczy (6.D27). Obok niej stoi więc **kontrola przyrządu na wejściu syntetycznym**,
która żąda, żeby klasyfikator trafił we **wszystkie cztery** kombinacje — łącznie z tą,
której w drzewie nie ma.

## 4. Co to znaczy dla 6.D185 — sprawdzone, nie przyjęte

Pole „Skąd" kazało sprawdzić, a nie przyjąć, że `DoorCycle.cs:104` jest bliźniakiem
`FirstRun.Faza` co do kształtu, ale nie co do ryzyka. **Sprawdzone: tak.** Oba biorą
`DoorPhase`, oba mają siedem ramion, oba mają pełne pokrycie — ale `PhaseSeconds` rzuca,
a `Faza` zwraca `phase.ToString()` po cichu. Bramka 6.D185 stoi tam, gdzie mechanizm jest
niewidzialny, i **nie jest luką w rdzeniu**: w `src/Sim/` nie ma dziś ani jednego
cichego ramienia przy pełnym pokryciu, a od tej pozycji pilnuje tego test.

## 5. Dwie pomyłki własnego przyrządu, obie złapane przed werdyktem

Zapisuję je, bo obie dałyby liczbę „głębszą niż zapisana" — dokładnie to, co 6.D208
znalazło u mnie w dwóch cudzych polach.

1. **Okno 45 wierszy zamiast korpusu switcha.** Pierwszy skan czytał stałą liczbę
   wierszy od `switch`, przez co `TrainProtection.cs:362` wyszedł jako
   `SignallingEventKind` (3/17) zamiast `ProtectionAction` (2/3) — okno zahaczało
   o sąsiedni kod. Poprawka: domykanie klamry.
2. **Liczenie członów po CAŁYM korpusie zamiast po etykietach.** `StationStop.cs:252`
   wyszedł jako 7/7, bo ramiona mają `DoorPhase` **po obu stronach** strzałki
   (`DoorPhase.Unlocking => DoorPhase.Opening`). Pokrycie liczy się z **lewej** strony;
   po poprawce 5/7 — i to jest właśnie ten kontrprzykład, na którym stoi cała sekcja 2.

**Druga pomyłka zmieniłaby werdykt**, a nie tylko liczbę: przy 7/7 podział trzymałby się
14/14 i „przybić" wyglądałoby na odpowiedź.

Liczba **14** została potwierdzona dwoma niezależnymi przyrządami: sondą w Pythonie
i bramką w C#.

## 6. Kontrole negatywne

Baza: **2/2** w `DefaultArmAuditTests`. Po każdej `md5sum -c` na obu plikach: `OK`.

| | podstawienie | wynik |
|---|---|---|
| KN-1 | ramię **ciche i martwe** dołożone do `src/Sim/` | **czerwone**, komunikat nazywa plik i wyliczenie |
| KN-2 | ramię **rzucające** i martwe dołożone tam samo | **zielone** — bramka milczy, tak jak ma |
| KN-3 | klasyfikator oślepiony na ciszę | **czerwone** na kontroli przyrządu |

**KN-2 jest tą kontrolą, o którą prosiło pole „Weryfikacja"** — „ciche ramię dołożone do
`src/Sim/` **zapala** ją, a rzucające nie". Para KN-1/KN-2 różni się **jedną rzeczą**:
treścią ramienia domyślnego.

## 7. Czego świadomie nie zrobiłem

- **Nie zmieniłem zachowania żadnego ramienia domyślnego** — pole „Poza zakresem".
- **Nie dopisałem członu do żadnego wyliczenia** (to samo pole).
- **Nie tknąłem `src/Game/`** (to 6.D197, domknięte) ani liczb połkniętych członów
  (to 6.D211, otwarte).
- **Nie przybiłem podziału postaci** — sekcja 2 mówi, dlaczego; nie przybiłem też
  tabeli czternastu wierszy, bo rośnie z każdym nowym `switch`-em, a dwa doszły w jeden
  dzień.

## 8. Kolejka — domknięcie zbiło zapas, a pomiar dał nową pozycję

Domknięcie 6.D210 zeszło zapas **udokumentowany** do **11** przy progu 12. `CLAUDE.md`
§8 każe wtedy najpierw uzupełnić kolejkę, **a pozycji wymyślonej na miejscu nie bierze
się nigdy** — więc nowa wyszła z sekcji 9 tego raportu: **6.D220**, o parze przeciwnych
decyzji na tym samym wyliczeniu w jednym pliku. Podłoga na liczbę bloków szczegółów
poszła tym samym commitem o jeden w górę.

## 9. Zauważone, nie tknięte

- **`TrainProtection.cs` ma oba rodzaje naraz**: wyrażeniowy rzucający w `Apply`
  (3/3) i instrukcyjny cichy w `Replay` (2/3), na tym samym `ProtectionAction`.
  Ten sam plik, ten sam typ, dwie przeciwne decyzje o ramieniu domyślnym — i obie są
  uzasadnione. Jest to najmocniejszy dowód, że podział nie jest regułą **projektu**,
  tylko własnością **miejsca**; nie liczyłem, ile jeszcze plików ma taką parę.
- **Trzy z czterech switchy instrukcyjnych biorą `ProtectionAction` i wszystkie trzy
  pokrywają 2 z 3** — połykają `None`. Ile to kosztuje, mierzy 6.D211 i tutaj nie jest
  liczone.
- **Klasyfikator nie odróżnia `throw` od `throw` z pustym komunikatem** ani nie czyta
  ramion `when`. Pierwszego nie potrzebuje (pyta o ciszę), drugiego w `src/Sim/` dziś
  nie ma — ale nie jest to nigdzie sprawdzone.
