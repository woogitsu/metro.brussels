# 6.D154 — 348 literałów to nie jedna sprawa, tylko osiem rodzin o różnych werdyktach

**12.09.2026**, na `5ba98be`. Wejście: `tests/Game.Tests/UiTextTests.cs` (helpery
`ZrodlaGry`, `KodBezKomentarzy`, `SlowaWKodzie`), `src/Game/**/*.cs`. Pozycja nie
zmienia bramki — jej wyjściem jest pomiar i rozbicie na rodziny, z których każda
dostaje własną pozycję w kolejce.

## 1. Liczba z pozycji odtwarza się co do jedynki — ale nie moją reimplementacją

Pomiar zrobiony **kodem samej bramki**, przez tymczasowy test w `Game.Tests`:

```
POMIAR|plikow=21|zglaszanych=348|wPlikach=16|
ChunkManifest.cs=20, GlbLoader.cs=2, StreamingPlan.cs=1, DesignAssumptions.cs=20,
FirstRun.cs=105, KeyNames.cs=1, RunHeader.cs=14, RunPlan.cs=142, SignallingHud.cs=9,
TelemetryTrack.cs=13, ChaseCameraAim.cs=9, PlatformFit.cs=1, SceneAxis.cs=1,
StationView.cs=4, TrainView.cs=2, TunnelView.cs=4
```

Suma per-plikowa daje dokładnie **348**.

**Najpierw policzyłem to w Pythonie i wyszło 446.** Różnica 98, z czego sam
`FirstRun.cs` 160 zamiast 105. Reimplementacja sita pomijała sita działające na
kontekście (ścieżki węzłów, dziury interpolacji, jednostki). Gdyby ta liczba weszła
do raportu, całe rozbicie stałoby na wartości, którą wyprodukował mój własny błąd —
i wyglądałaby dokładnie jak pomiar. Jest to ta sama lekcja, którą 6.D153 zapisało
dzień wcześniej: **pomiar o bramce robi się kodem bramki.**

**Jedna poprawka do treści pozycji**: zgłoszenia ma **16** plików, nie 21. Liczba 21
to wielkość korpusu.

## 2. Rozbicie na rodziny

Materiałem jest zrzut wszystkich zgłoszeń z plikiem i wierszem, klasyfikowany po
kontekście trzech wierszy wstecz (`throw` bywa w poprzednim wierszu — dlatego
pierwszy pomiar dawał `wThrow=0`).

| rodzina | ile | gdzie głównie | przykład |
|---|---:|---|---|
| pole JSON / identyfikator | **108** | RunPlan 66, FirstRun 22, ChunkManifest 18 | `"streaming"`, `"chunks"`, `"lods"` |
| wypis diagnostyczny | **85** | FirstRun 50, RunPlan 19, TelemetryTrack 8 | `[ASSETS] brak pliku: {absolutePath}` |
| **pozostałe — nierozstrzygnięte** | **48** | FirstRun 25, RunPlan 7, SignallingHud 6 | `"KABINA"`, `"data/track/L1_A.json"` |
| **TEKST POLSKI — kandydat do katalogu** | **46** | RunPlan 24, FirstRun 12, ChaseCameraAim 4 | `przejazd z zatrzymaniami wymaga co najmniej dwóch` |
| nazwa opcji CLI | **27** | RunPlan 26 | `"sample-every"`, `"steps-per-frame"` |
| proza założeń projektowych | **20** | DesignAssumptions 20 | `wysokość oka nad główką szyny; podłoga M7 …` |
| komunikat wyjątku (`throw`) | **19** | RunHeader 9, ChaseCameraAim 4 | `zasięg streamowania nie może być ujemny (…)` |
| węzeł sceny / zasób | **8** | FirstRun 8 | `"Tunnel"`, `"Train"`, `"res://"` |

## 3. Główny wynik: wśród 348 jest tekst, który bramka istnieje po to, żeby łapać

Pozycja zakładała, że 348 to „wypisy diagnostyczne, prozą opisane założenia
projektowe i nazwy pól JSON" — czyli rzeczy, których do katalogu się nie wkłada.
**To jest prawdą dla 259 z nich** (108 + 85 + 27 + 20 + 19). Nie jest prawdą dla
reszty. W `SignallingHud.cs` stoją wprost zdania widziane przez gracza:

```
public const string NotOnPlanYet    = "sygnalizacja: skład jeszcze nie wjechał na plan";
public const string WithoutProtection = "sygnalizacja: linia bez ochrony pociągu";
var ostrzezenie = decision.Overspeed ? "  PRZEKROCZENIE" : string.Empty;
```

To jest dokładnie rodzina, dla której katalog `UiText` powstał — a `SignallingHud.cs`
nie jest dziś przez bramkę skanowany w ogóle. **Rozstrzygnięcia wymaga więc nie
„co zrobić z 348", tylko osiem osobnych pytań o osiem rodzin** i one wchodzą do
kolejki po jednej.

Zastrzeżenie, którego nie przemilczam: rodzina „tekst polski" jest wyodrębniona
**po obecności polskiego znaku diakrytycznego**, więc wpadają w nią także komunikaty
diagnostyczne po polsku (np. `{Id} ({Variant}): … chunków`). Rozdzielenie „tekst dla
gracza" od „diagnostyka po polsku" wymaga przeczytania każdego z tych 46 w miejscu
użycia i jest treścią pozycji 6.D175, a nie tego raportu.

## 4. Zrzut daje 361, a bramka 348 — cała różnica jest w jednym pliku

```
suma autorytatywna: 348   suma zrzutu: 361

plik                  calo-plikowo  wierszami  roznica
  FirstRun.cs               105        118        +13

pliki zgodne: 15 z 16
```

Zrzut podaje `SlowaWKodzie` **pojedynczy wiersz**, a pomiar autorytatywny — cały plik.
Sita działające na kontekście rozstrzygają wtedy inaczej. **15 plików na 16 zgadza się
co do jedynki**, więc zrzut nadaje się na materiał do klasyfikacji; liczbą pozostaje
348. Sama rozbieżność zlokalizowana w `FirstRun.cs` jest osobną obserwacją i wchodzi
do kolejki jako 6.D180 — bramka licząca inaczej wiersz po wierszu niż całym plikiem
to nie jest rzecz, którą chce się odkryć przypadkiem.

## 5. Czego nie zrobiłem

- **Nie tknąłem bramki ani jej zakresu.** Pole „Wyjście" tej pozycji to pomiar;
  rozszerzenie skanu na kolejne pliki wymaga rozstrzygnięcia per rodzina, a te
  rozstrzygnięcia są dopiero wpisane.
- **Nie rozstrzygnąłem ani jednego z 348 literałów.** Klasyfikacja mówi, do której
  rodziny literał należy, a nie co się z nim ma stać.
- **Nie usunąłem tymczasowych testów pomiarowych z historii** — bo ich w historii
  nie ma: oba (`POMIAR_6D154`, `ZRZUT_6D154`) były wstawione, uruchomione i zdjęte
  w drzewie roboczym, a `md5sum -c` na `UiTextTests.cs` po każdym dał `OK`.
