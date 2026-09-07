# Trzy gałęzie, których nikt nie pilnował (6.D31)

**Zmierzone 07.09.2026 na commicie:** `aa9ea6b2c4121947f0c4f93acd307ef70fb0c725`
(gałąź `claude/6d31-galaz-bez-straznika`).

## 1. Skąd

6.D29 (#352) sklasyfikowała 18 metod testowych C#, u których **wszystkie** asercje
siedzą w bloku zagnieżdżonym, i świadomie nie zmieniła treści żadnej — jej zadaniem
była klasyfikacja. Trzy wyszły jako **(c): realna usterka bez żadnego strażnika**.
Ta pozycja je wzmacnia.

Wspólny kształt usterki: gałąź, w której siedzą asercje, zależy od danych
produkcyjnych albo od modelu, a **nic nie pilnuje, że kiedykolwiek zostanie
wchodzona**. Test przechodzi wtedy nie dlatego, że sprawdził, ale dlatego, że nie
miał czego sprawdzić — i nie mówi o tym ani słowa.

## 2. Wszystkie liczby niżej są ZMIERZONE, nie policzone z kodu

Pole „Wyjście" tej pozycji żądało tego wprost: *„licznik przybity do złej liczby jest
kolejną wyrocznią zepsutą w dobrą stronę"*. Każdy licznik wpisałem więc najpierw
z wartością `999`, uruchomiłem test i odczytałem prawdziwą liczbę z komunikatu
`Assert.AreEqual failed`. Trzy pomiary, po jednym na test:

```
Assert.AreEqual failed. Expected:<999>. Actual:<17>.  argumentów bez zależności
Assert.AreEqual failed. Expected:<999>. Actual:<3>.   argumentów z zależnością
Assert.AreEqual failed. Expected:<999>. Actual:<8>.   paskudnych wejść odrzuconych
Assert.AreEqual failed. Expected:<1>.   Actual:<2>.   odległości przy limicie planu
```

## 3. `RunPlanTests.EveryKnownArgumentIsAcceptedOnItsOwnOrNamesWhatItNeeds`

Wszystkie asercje stoją w pętli po `RunPlan.KnownArguments`. Opróżniona tablica dałaby
test zielony **bez ani jednej wykonanej asercji**. Dodane dwa liczniki i suma:

```
argumentów bez zależności:  17
argumentów z zależnością:    3      (line, limit-kmh, calls)
razem:                      20  ==  RunPlan.KnownArguments.Length
```

Trzecia asercja porównuje sumę z długością tablicy, więc argument dopisany bez
odwiedzenia przez pętlę też jest FAIL-em — nie tylko usunięty.

## 4. `RunPlanTests.NoInputThrows` — i znalezisko, którego nie było w planie

Wszystkie asercje poza `IsNotNull` stały w gałęzi `if (!plan.IsValid)`. Licznik
odrzuconych miał wyjść **9** na dziewięć paskudnych wejść. Wyszedł **8**:

```
Assert.AreEqual failed. Expected:<999>. Actual:<8>. paskudnych wejść odrzuconych;
   przyjęte: --telemetry=
```

**`--telemetry=` — pusta ścieżka — przechodzi jako plan POPRAWNY.** Wartość tej opcji
jest napisem i pustka nie wywraca żadnego rozbioru, więc scena pojechałaby z pustą
ścieżką pliku telemetrii. Ośmiu pozostałych wejść (`--sample-every=`, `--view=`,
`--at-chainage=1e999`, `----`, `=`, `--=1`, `--jitter=--`, `--at-chainage=`) rozbiór
odrzuca poprawnie.

**Nie poprawiam tego tutaj**: 6.D31 wzmacnia testy, a zmiana rozbioru argumentów sceny
jest zmianą jej zachowania. Fakt jest natomiast **przybity z imienia**:

```csharp
CollectionAssert.AreEqual(new[] { "--telemetry=" }, przyjete, …);
```

więc ani nie zniknie po cichu, ani nie będzie wyglądał na przeoczenie — a gdy ktoś to
naprawi, ta asercja zażąda zmiany listy razem z poprawką. Zgłoszone jako znalezisko
w §7.

## 5. `TrainProtectionTests.Predkosc_dopuszczalna_jest_odwrotnoscia_krzywej_z_T_311`

Dwie gałęzie, każda z własnymi asercjami, i nic nie pilnowało, że **którakolwiek** jest
wchodzona. Zmierzony podział pięciu odległości:

```
przy limicie planu (authority mieści limit):   2   (10 m, 50 m)
poniżej limitu (odwrotność krzywej hamowania): 3   (120 m, 300 m, 700 m)
```

Druga gałąź jest tym, o czym test mówi **w nazwie** — odwrotnością krzywej z T-311 —
więc jej ciche zniknięcie byłoby zniknięciem sensu testu, nie jego części.

## 6. Kontrole negatywne — WYKONANE, cztery

```
KN-1  KnownArguments zdjeta do jednego elementu
      Failed EveryKnownArgumentIsAcceptedOnItsOwnOrNamesWhatItNeeds
      Assert.AreEqual failed. Expected:<17>. Actual:<1>. argumentow bez zaleznosci

KN-2  RunPlan.IsValid zawsze true (rozbior przyjmuje wszystko)
      Failed NoInputThrows
      Assert.AreEqual failed. Expected:<8>. Actual:<0>. paskudnych wejsc odrzuconych;
        przyjete: --at-chainage= | --jitter=-- | --sample-every= | --view= | = |
                  --=1 | --telemetry= | ---- | --at-chainage=1e999

KN-3  PermittedSpeedMps zawsze na double.MaxValue (wszystkie odleglosci w pierwsza galaz)
      Failed Predkosc_dopuszczalna_jest_odwrotnoscia_krzywej_z_T_311
      Assert.IsTrue failed. 10 m: limit planu ma sie zmiescic w authority
      Failed Predkosc_dopuszczalna_spada_do_zera_na_koncu_authority   (siostrzany)

KN-3b liczniki podmienione miejscami
      Failed Predkosc_dopuszczalna_jest_odwrotnoscia_krzywej_z_T_311
      Assert.AreEqual failed. Expected:<2>. Actual:<3>. odleglosci przy limicie planu
```

**KN-3 i KN-3b są tu OBIE, bo mierzą różne rzeczy, i trzeba to powiedzieć wprost.**
KN-3 wywraca test, ale przez **własną asercję pierwszej gałęzi**, nie przez nowy
licznik — mutacja jest tak gruba, że łamie też sam warunek. Dowodu, że licznik jest
podłączony do właściwej gałęzi, dostarcza dopiero KN-3b: przestawienie inkrementacji
miejscami zmienia **tylko** liczby i wywraca dokładnie nową asercję. Bez KN-3b
zapisałbym „kontrola wykonana" o kontroli, która nie sprawdziła tego, co miała.

## 7. Weryfikacja

```
$ dotnet test tests/Sim.Tests
Passed!  - Failed: 0, Passed: 578, Skipped: 0, Total: 578

$ dotnet test tests/Game.Tests
Passed!  - Failed: 0, Passed: 205, Skipped: 0, Total: 205

$ python3 tools/tests/test_all.py
  RAZEM 75.398 s, 1864 testów, 99 modułów
kod: 0
```

**Liczby testów C# są bez zmiany** (578 + 205 = 783) i to jest zamierzone: liczniki
mieszkają wewnątrz trzech istniejących testów, a pole „Skończone, gdy" żądało, żeby
liczba nie spadła. Zestaw narzędzi też bez zmiany — ta pozycja nie dotyka `tools/`.

## 8. Czego świadomie nie zrobiono

- **Nie budowano bramki na ten wzorzec** — pole „Poza zakresem". 6.D29 zmierzyła, że
  bramka syntaktyczna zapaliłaby się na **15 z 18** przypadków poprawnych.
- **Nie tknięto pozostałych 15 metod** — mają uzasadnienia w raporcie 6.D29
  (`try`/`finally` bez `catch`, pętle po zbiorze zadanym w teście, gałąź pilnowana
  osobnym testem).
- **Nie poprawiono rozbioru `--telemetry=`** — to zmiana zachowania sceny, nie
  wzmocnienie testu. Zgłoszone niżej.

## 9. Co zauważone przy okazji, nietknięte

- **`--telemetry=` z pustą wartością przechodzi jako plan poprawny** (§4). Scena
  pojechałaby z pustą ścieżką pliku telemetrii; co się wtedy dzieje przy zapisie, nie
  jest zmierzone i tego nie sprawdzałem. Fakt jest przybity asercją, żeby nie zniknął
  po cichu.
- **Pozostałe osiem paskudnych wejść jest odrzucanych z kodem `UnknownArgument` albo
  `BadArgumentValue`** i komunikatem — czyli rodzina, do której `--telemetry=` należy,
  jako całość działa. To wzmacnia podejrzenie, że pustka jest przeoczeniem, a nie
  decyzją; ale rozstrzygnięcie należy do pozycji, która ten rozbiór ruszy.
