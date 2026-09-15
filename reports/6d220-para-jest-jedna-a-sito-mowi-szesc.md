# 6.D220 — par jest JEDNA, a sito naiwne mówi sześć

**15.09.2026**, na `4e32b35`. Wejście: `tests/Sim.Tests/DefaultArmAuditTests.cs`
(`Zebrane`, `Sklasyfikuj`, `PoczatkiSwitchy`, `Korpus`, `CzlonyNazwy`, `ZrodlaRdzenia`,
`PolykaneCzlony`), `src/Sim/**/*.cs`,
`reports/6d210-podzial-sie-rozszedl-w-jedna-dobe.md` §1 i §9,
`reports/6d211-dziesiec-nazw-zamiast-liczby-dziesiec.md`.

## 1. Liczba, której żądało pole „Wyjście": JEDNA

| | |
|---|---:|
| switchy po wyliczeniu w `src/Sim/` | **14** |
| grup (plik × wyliczenie) z więcej niż jednym switchem | **1** |
| **plików z dwiema PRZECIWNYMI decyzjami na tym samym wyliczeniu** | **1** |
| wyliczeń niosących obie decyzje gdziekolwiek w rdzeniu, bez względu na plik | 1 |

Jedyna para, w pełnym adresie:

| | |
|---|---|
| plik | `src/Sim/Signalling/TrainProtection.cs` |
| wyliczenie | `ProtectionAction` — `None`, `ServiceIntervention`, `EmergencyIntervention` |
| strona **rzucająca** | `Apply`, wiersz **108**, wyrażeniowy, pokrycie **3/3**, ramię `_ => throw` |
| strona **cicha** | `Supervise`, deklaracja **307**, switch **362**, instrukcyjny, pokrycie **2/3**, ramię `default: break;` |
| **zbiór rozejścia** | **`{None}`** — `Supervise` połyka, `Apply` obsługuje wprost |

**Dowód 6.D210 jest POJEDYNCZY, nie wzorcowy.** Tamta pozycja nazwała `TrainProtection.cs`
„najmocniejszym dowodem, że podział nie jest regułą projektu, tylko własnością miejsca" —
jest **jedynym**.

## 2. Obie decyzje są uzasadnione, i idą dalej: one się ze sobą NIE KŁÓCĄ

`Apply` jest **funkcją totalną** `ProtectionAction → DriverCommand`: każdy człon musi dać
nastawniki, więc nieznany człon jest błędem, a nie wartością domyślną. `_ => throw` jest
tu jedyną poprawną formą.

`Supervise` **nie liczy nic** — wypisuje zdarzenia do dziennika na przejściu stanu.
Zdarzenia o braku ingerencji nie ma, więc ramię byłoby puste.

**Rozstrzygające jest to, czego pole „Czego NIE wolno przyjąć bez pomiaru" kazało
poszukać:** strona rzucająca obsługuje `None` jako `ProtectionAction.None => requested`,
czyli **„przepuść bez zmiany"**. To jest ta sama semantyka, co połknięcie po stronie
cichej. **Strony zgadzają się co do `None` i różnią wyłącznie POSTACIĄ.**

Sprzeczności — miejsca, gdzie ciche ramię połyka człon, o który druga metoda w tym samym
pliku pyta wprost i **robi z nim co innego** — **nie ma ani jednej**.

## 3. Sito po bliskości mówi SZEŚĆ, i to jest zmierzony koszt drogi na skróty

Niezależny skan po bliskości — `switch`, a w promieniu 900 znaków człon jakiegokolwiek
z 19 wyliczeń rdzenia — daje **sześć** grup z więcej niż jednym switchem:

```
src/Sim/Physics/ParameterStatus.cs      | ParameterStatus      | switchy: 2
src/Sim/Physics/VehicleModel.cs         | RailCondition        | switchy: 2
src/Sim/Signalling/ProtectionMode.cs    | ProtectionModeStatus | switchy: 2
src/Sim/Signalling/SignallingPlan.cs    | BlockKind            | switchy: 2
src/Sim/Signalling/SignallingPlan.cs    | ProtectionVariant    | switchy: 2
src/Sim/Signalling/TrainProtection.cs   | ProtectionAction     | switchy: 2
```

Klasyfikator daje **jedną**. Różnica to w całości **switche po `string` i po `char`,
których ramiona zwracają człony wyliczenia** — `ParameterStatus.cs:32`,
`ProtectionMode.cs:33`, `SignallingPlan.cs:559` i `:574`, `DriverKeys.cs:141`,
`InputLog.cs:377`. Sito po bliskości ma więc na tym pytaniu **5 trafień fałszywych na 6**,
i to jest liczba, a nie ostrzeżenie.

**Kontrola przyrządu na populacji, żeby „14" nie było liczbą ze skanu, który oślepł:**
odrzuconych `switch` jest 7, wszystkie obejrzane po kolei i wszystkie po napisie albo po
znaku. Switchy po wyliczeniu **bez** ramienia domyślnego: **zero**, więc „brak ramienia"
jako trzecia decyzja nie tworzy dziś ani jednej dodatkowej pary.

## 4. Rozstrzygnięcie: BRAMKA NIE POWSTAJE — trzy powody, każdy zmierzony

**Powód pierwszy — zapalałaby się na kodzie POPRAWNYM.** Bramka „w `src/Sim/` nie ma pary
przeciwnych decyzji" albo „para jest dokładnie ta jedna" żąda, żeby druga taka para nie
powstała. Ale 6.D210 rozstrzygnęło, że podział jest **własnością miejsca**, a nie projektu
— więc drugi plik, w którym jedna metoda mapuje wyliczenie totalnie, a druga raportuje
wybrane człony, jest kodem **poprawnym i oczekiwanym**. Taka bramka zostałaby przy
pierwszym trafieniu wyłączona, nie poprawiona (6.D27).

**Powód drugi — jedyna rzecz warta pilnowania JEST JUŻ PILNOWANA, jako ZBIÓR i w obie
strony.** Wartością tej pozycji nie jest „czy para istnieje", tylko „co cicha strona
połyka". Dla jedynej pary zbiór rozejścia równa się `{None}` — czyli dokładnie zbiorowi,
który `Kazdy_swiadomy_filtr_ma_polykane_czlony_wypisane_Z_NAZWY` przybija wpisem 6.D211.
Ponieważ strona rzucająca ma pokrycie 3/3, **zbiór rozejścia jest RÓWNY zbiorowi
połykanemu**: nowa bramka nie dodałaby ani jednego twierdzenia.

**Powód trzeci — byłaby drugim czytnikiem tego samego faktu** (6.D213, które usunęło kopię
czytnika i uznało to za wynik).

Do tego: bramka stałaby dziś na zbiorze **jednoelementowym**, a po jakiejkolwiek zmianie
formy w `TrainProtection.cs` — na **pustym**, czyli wymagałaby własnej kontroli przyrządu,
żeby cokolwiek znaczyć (6.D159). Koszt realny, zysk zerowy.

**Zapisem tej pozycji jest więc LICZBA i GRANICA, nie zapadka.**

**Warunek powrotu do tej decyzji, wypisany:** sens miałaby dopiero para, w której **strona
rzucająca ma pokrycie CZĘŚCIOWE** — bo wtedy zbiór rozejścia przestaje być podzbiorem
zbioru połykanego. W drzewie jest dziś jeden switch o pokryciu częściowym i rzucający
(`StationStop.cs`, `DoorPhase`, 5/7), ale **bez pary w swoim pliku**.

## 5. Kontrole negatywne

| | podstawienie | wynik |
|---|---|---|
| KN-1 | nowy plik: `enum` + switch wyrażeniowy rzucający 3/3 + instrukcyjny cichy 2/3 | par **1 → 2**, rozejście `[Gamma]` |
| KN-2 | ten sam plik, ciche ramię zamienione na `throw` | par **wraca do 1**, a grup „>1 switch" zostaje **2** |
| KN-3 | para rozbita na dwa pliki | par **1** (grupowanie jest per-plik), „po typie" **1 → 2** |
| KN-4 | człon dopisany do `ProtectionAction` w drzewie | zapala **istniejącą** bramkę 6.D211 |

**KN-1 jest tą, o którą prosiło pole „Weryfikacja"**: para dołożona do `src/Sim/`
**wchodzi** do tej liczby. **KN-2 oddziela decyzję od samej wielokrotności** — bez niej
„1" znaczyłoby tyle, co licznik grup. **KN-4 jest powodem drugim, wykonanym**: to, co
warto pilnować, pilnuje już inna bramka.

## 6. Czego świadomie nie zrobiłem

- **Nie postawiłem bramki** — trzy powody w §4, każdy zmierzony.
- **Nie zmieniłem zachowania żadnego ramienia** ani nie ujednoliciłem decyzji w pliku;
  pole tego zabraniało, a §2 mówi, dlaczego nie byłoby czego ujednolicać.
- **Nie przybijałem podziału postaci** — rozstrzygnięte w 6.D210 jako granica zapisana.
- **`src/Game/` nietknięte** (6.D197, domknięte).

## 7. Zauważone, nie tknięte

- **`KorpusMetody` zwraca korpus NASTĘPNEJ metody, gdy szukana jest wyrażeniowa (`=>`).**
  Znajduje deklarację po modyfikatorze dostępu, a korpus wycina szukaniem pierwszej
  klamry — metoda wyrażeniowa własnej klamry nie ma. Zmierzone na `TrainProtection.cs`:
  pytanie o `BrakingDistanceM` (wiersz 290) i o `Supervise` (307) zwracają **ten sam napis
  o długości 3056 znaków**, oba przy `deklaracji = 1`, więc straż tego czytnika
  **przepuszcza to bez słowa**. Dziś nieszkodliwe — wszystkie cztery wpisy
  `PolykaneCzlony` nazywają metody klamrowe — ale wpis nazywający metodę wyrażeniową
  mierzyłby **cudzą metodę** i byłby zielony.
- **Sito po bliskości ma 5 trafień fałszywych na 6** (§3) — liczba warta zapamiętania
  przy każdej następnej pozycji, która sięgnie po skan bez klasyfikatora.
