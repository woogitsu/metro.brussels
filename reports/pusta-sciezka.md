# Pusta ścieżka przechodziła jako plan poprawny (6.A28)

**Zmierzone 07.09.2026 na commicie:** `8dc5af5aaf135d0ac50149ad179fad6fb6e1a2a8`
(baza gałęzi `claude/6a28-pusta-sciezka`, czyli `main` po scaleniu #369).

## 1. Pomiar, o który prosiło pole „Wyjście": ile opcji przyjmuje pustkę

Pole żądało rozstrzygnięcia **pomiarem**, bo od niego zależało, czy poprawka jest jedna
i wspólna, czy dziewięć osobnych. Rozbiór wywołany dla każdej opcji ścieżkowej osobno,
przez test w `Game.Tests` (Godota w tym kontenerze nie ma — pole „Weryfikacja" na to
pozwala wprost):

```
telemetry        kod=0 valid=True Argument=[]
shot             kod=0 valid=True Argument=[]
replay           kod=0 valid=True Argument=[]
from-telemetry   kod=0 valid=True Argument=[]
axis             kod=0 valid=True Argument=[]
manifest         kod=0 valid=True Argument=[]
calls            kod=9 valid=False Argument=[] [ARGUMENT] --calls ma sens tylko z --line…
signalling       kod=0 valid=True Argument=[]
input-log        kod=0 valid=True Argument=[]
assets           kod=0 valid=True Argument=[]
przyjetych pustych sciezek: 9 z 10
```

**Dziewięć z dziesięciu**, a dziesiąta (`--calls`) była odrzucana z powodu
**niezwiązanego z pustką** — wymaga `--line`. Warunek z pola „Wyjście" („jeżeli
wszystkie, poprawka jest jedna i wspólna") zaszedł: poprawką jest jedna lista
`RunPlan.PathArguments` i jedna pętla w `Parse`.

**Dziesięć, nie dziewięć — wpis o jednej nie wiedział.** Wymieniał `--telemetry`,
`--shot`, `--replay`, `--from-telemetry`, `--axis`, `--manifest`, `--calls`,
`--signalling`, `--input-log`. Dziesiąta to `--assets`, której wartość jest ścieżką
katalogu (`Argument("assets") ?? RepoPath("build/t400")` w `FirstRun`).

## 2. Mechanizm — dlaczego pustka nie była tylko brzydka

```
--telemetry=      Argument=[] dlugosc=0 HasFlag=True TelemetryPath=[]
```

`TelemetryPath` wychodziło **napisem pustym, nie `null`**. Warunek
`_telemetryPath is not null` w scenie był więc **prawdziwy**: scena zbierała wiersze
telemetrii przez cały przejazd i próbowała je zapisać pod pustą nazwą. To jest różnica
między „opcja jest ignorowana" i „opcja jest brana pod uwagę z bezsensowną wartością";
druga rzecz kosztuje cały przejazd.

## 3. Czego NIE zmierzyłem, i dlaczego to jest tu napisane

Pole „Co jest, a co nie jest tu problemem" żądało sprawdzenia, **co scena robi** przy
zapisie do pustej ścieżki — usterka cicha (plik pod dziwną nazwą) czy głośna (wyjątek).
Zapis idzie przez Godota:

```csharp
using var file = FileAccess.Open(_telemetryPath, FileAccess.ModeFlags.Write);
if (file is null)
{
    Abort(ExitTelemetryWriteFailed, $"[TELEMETRIA] nie da się zapisać {_telemetryPath}: …");
```

Czyli **zachowanie zależy od tego, co `Godot.FileAccess.Open` zwraca dla napisu
pustego** — a Godota w tym kontenerze nie ma. **Nie zgaduję.** Dla porównania,
`System.IO.File.WriteAllLines("")` w .NET 10 rzuca (zmierzone osobnym programem):

```
ArgumentException: The value cannot be an empty string. (Parameter 'path')
```

ale to jest inna biblioteka i nie wolno z niej wnioskować o Godocie. Pytanie „cicha czy
głośna" zostaje więc **niezmierzone** — i ta pozycja czyni je **bezprzedmiotowym**,
bo plan jest odrzucany przed jakimkolwiek przejazdem. Gdyby kiedyś ktoś odmowę cofnął,
pytanie wraca i będzie wymagało przebiegu na maszynie z Godotem.

## 4. Co doszło

Jedna lista i jedna pętla w `Parse`, postawiona **przed** sprawdzeniem zależności
między argumentami i przed parserami liczbowymi — bo odmowa ma padać przed przejazdem,
nie przy zapisie wyniku. `IsNullOrWhiteSpace`, nie `Length == 0`: `--telemetry=" "`
jest tą samą usterką, tylko trudniejszą do zauważenia w wierszu poleceń.

Pięć testów w `RunPlanTests`: pętla po całej liście, wariant z samymi białymi znakami,
kontrola drugiego kierunku (wartość niepusta nadal przechodzi, dla każdej opcji),
przybicie listy (dziesięć pozycji, każda w `KnownArguments`, bez powtórzeń)
i przybicie mechanizmu z §2.

## 5. `NoInputThrows` zmieniony RAZEM z poprawką

Pole „Skończone, gdy" tego żądało wprost. Liczba **8 → 9** i lista `przyjete` z
`{ "--telemetry=" }` na pustą — **przepisane, nie dopisane obok**:

```
przed:  Assert.AreEqual failed. Expected:<8>. Actual:<9>. paskudnych wejść odrzuconych; przyjęte:
po:     Passed!  - Failed: 0, Passed: 210, Total: 210
```

Lista pusta, a nie skasowana asercja: `CollectionAssert.AreEqual` na pustym zbiorze jest
asercją **bezwarunkową** i wywraca się, gdy rozbiór zacznie cokolwiek z tej dziewiątki
przyjmować. Skasowanie zostawiłoby test z samym licznikiem, a licznik nie mówi **które**
wejście przeszło.

## 6. Kontrole negatywne — WYKONANE

**KN-1 — sprawdzenie pustki zdjęte** (stan przed tą pozycją):

```
  Failed NoInputThrows
  Failed KazdaOpcjaSciezkowaOdmawiaPustejWartosci
  Failed OpcjaSciezkowaOdmawia_takze_samych_bialych_znakow
  Failed Pusta_sciezka_nie_dochodzi_do_TelemetryPath
Failed!  - Failed: 4, Passed: 206, Total: 210
```

Cztery testy, w tym `NoInputThrows` — **starszy od tej pozycji**.
`Lista_opcji_sciezkowych…` zostaje zielony i tak ma być: lista dalej istnieje, zdjęte
jest jej **użycie**, a to są dwie różne rzeczy.

**KN-2 — odmowa zbudowana zbyt szeroko** (`path is not null` zamiast
`IsNullOrWhiteSpace`, czyli odmowa dla **każdej** wartości ścieżkowej):

```
Failed!  - Failed: 27, Passed: 183, Total: 210
```

Dwadzieścia siedem testów, w tym `EveryKnownArgumentIsAcceptedOnItsOwnOrNamesWhatItNeeds`,
`TelemetryPathSwitchesTheModeAndMakesTheRunScripted` i cała rodzina limitów. To jest
dowód, że kontrola drugiego kierunku istnieje **niezależnie od moich nowych testów** —
odmowa zbyt szeroka nie mogła tu przejść niezauważona.

**KN-3 — lista okrojona o jedną pozycję** (`assets` usunięte):

```
  Failed Lista_opcji_sciezkowych_jest_podzbiorem_znanych_i_ma_dziesiec_pozycji
Failed!  - Failed: 1, Passed: 209, Total: 210
```

Dokładnie jeden test, ten właściwy. Bez niego pętla z §4 byłaby zielona **na mniejszym
zbiorze** — i to jest cały powód, dla którego liczba jest przybita.

## 7. Weryfikacja

```
$ dotnet test tests/Game.Tests
Passed!  - Failed: 0, Passed: 210, Skipped: 0, Total: 210      (205 → 210)
```

## 8. Czego świadomie nie zrobiono

- **Nie tknięto `KnownArguments`** — pole „Poza zakresem". `PathArguments` jest listą
  osobną i mówi o **kształcie wartości**, nie o tym, czy argument jest znany.
- **Nie tknięto wartości nieliczbowych ani nieistniejących ścieżek** — osobne klasy
  błędu, tak jak mówi pole „Poza zakresem". Ta pozycja dotyczy pustki.
- **Nie dopisano bramki po stronie Pythona** na listę `PathArguments`, mimo że
  pierwsza wersja komentarza w kodzie ją **obiecywała**. Obietnica została z kodu
  usunięta i zastąpiona nazwą testu C#, który to naprawdę robi — dokładnie ta usterka,
  którą 6.A26 dziś naprawiło w §10 raportu 6.A22, i nie ma powodu wprowadzać jej z
  powrotem. Drugi czytnik jednej listy rozjeżdża się po cichu (6.B28).
- **Nie sprawdzono zachowania Godota** — §3, z powodem.

## 9. Zauważone przy okazji, nie tknięte

**Pierwsza wersja mojego testu żądała, żeby `--calls=` szło inną drogą, i padła.**
Założyłem, że odmowa zależności (`--calls` wymaga `--line`) stoi przed sprawdzeniem
pustki. Przebieg pokazał odwrotnie: sprawdzenie pustki jest wcześniej, więc wszystkie
dziesięć odmawia z powodu **właściwego** i każda nazywa swoją opcję. Test jest
poprawiony według pomiaru, a nie pomiar według testu — i asercja została jako pusta
lista, żeby przesunięcie tej kolejności w przyszłości było widoczne.
