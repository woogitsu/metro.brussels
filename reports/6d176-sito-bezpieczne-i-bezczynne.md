# 6.D176 — sito jest bezpieczne i BEZCZYNNE, a rodzina liczy 87, nie 27

**12.09.2026**, na `75d83df`. Wejście: `src/Game/RunPlan.cs`, `src/Game/FirstRun.cs`,
`tests/Game.Tests/UiTextTests.cs`. Pozycja pytała o dwie rzeczy: czy sito po kształcie
wchodzi, i czy nazwy opcji należą do tej samej sprawy co tekst interfejsu.

## 1. Rodzina liczy 87, a nie 27 — i to jest ustalenie z 6.D181

Pozycja mówi o **27** nazwach opcji. 6.D181 zmierzyło, że jednowyrazowe nazwy
(`axis`, `line`, `shot`, `manifest`, `shell`, `calls`, `replay`, `signalling`) to
**ta sama rodzina**, tylko nierozpoznana przez wzorzec, bo nie mają myślnika. Jest
ich **60**. Rodzina liczy więc **87** i odpowiadam dla całych 87.

## 2. Sito po kształcie jest bezpieczne — zero fałszywych trafień

Wzorzec `[a-z][a-z0-9]*(-[a-z0-9]+)+` łapie na dzisiejszym korpusie **27 wystąpień,
7 różnych nazw**:

```
at-chainage  from-telemetry  input-log  limit-kmh  no-geometry  sample-every  steps-per-frame
```

**Każda jest nazwą opcji.** Żadne trafienie nie jest czymś innym — to była pierwsza
połowa pola „Skończone, gdy" i jest spełniona.

Kontrola żądana w polu „Weryfikacja": wzorzec zastosowany do `"limit-kmh w kabinie"`
daje **`False`** — żąda całego literału, nie podciągu.

## 3. Sito obejmuje 27 z 87, a druga reguła 58 — razem 70

| reguła | obejmuje |
|---|---:|
| kształt z myślnikiem | **27** |
| akcesor (`Argument(`, `HasFlag(`, `arguments.ContainsKey(`, `TryDouble(arguments`) | **58** |
| część wspólna | 15 |
| **suma** | **70** |

**Siedemnaście zostaje poza obiema** i są to jednowyrazowe nazwy stojące w **listach**:

```
telemetry  shot  jitter  view  axis  assets  manifest  shell
platforms  line  calls  signalling  replay
```

Kształt ich nie odróżni — 6.D173 zmierzyło to na sześciu polskich słowach
(`stacja`, `pociag`, `peron`, `drzwi`, `postoj`, `hamulec`), które wzorzec
identyfikatora przepuszcza co do jednego. Akcesor ich nie widzi, bo wiersz listy
żadnego wywołania nie zawiera.

## 4. Główny wynik: sito byłoby dziś BEZCZYNNE

To jest rzecz, której pozycja nie zakładała, a która rozstrzyga o jej odpowiedzi.

Bramka **nie skanuje sitem słów całego `src/Game/`**. Skanuje: `Hud.cs`, trzy metody
`FirstRun.cs` (`StationLine`, `Faza`, `HelpLine`), tablicę `Nazwy` z `KeyNames.cs`
oraz `DriverActions.cs` i `EmergencyBrake.cs`.

- `RunPlan.cs` — gdzie stoi **26 z 27** trafień — **nie występuje w `UiTextTests.cs`
  ani razu**.
- Dwudzieste siódme, `no-geometry` w `FirstRun.cs:874`, stoi w metodzie
  `BuildWorld()`, a nie w żadnej z trzech skanowanych.

**Żaden z 27 literałów nie leży dziś w zasięgu sita.** Dopisanie wzorca nie zmieniłoby
ani jednego werdyktu — byłoby kodem, który wygląda jak ochrona i nie chroni niczego,
dopóki ktoś nie rozszerzy zakresu.

Odpowiedź na pierwszą połowę pytania brzmi więc: **sito może wejść i jest bezpieczne,
ale nie ma po co wchodzić przed decyzją o zakresie** — a ta decyzja jest tym, co
6.D175 pokazało jako ryzykowne (137 na 140 literałów z polskim znakiem to diagnostyka
i proza; rozszerzenie skanu bez rozstrzygnięcia rodzin zgłosiłoby je wszystkie).

## 5. Druga połowa: nie, to nie ta sama sprawa

Katalog `UiText` jest katalogiem tekstu docierającego do gracza. Kryterium ustaliło
6.D175 i jest sprawdzalne: napis dociera przez `_hud.Update(…)`.

**Żadna nazwa opcji tą drogą nie idzie.** Nazwy opcji są umową z człowiekiem
wpisującym polecenie — czyta je, więc nie są „niczyim tekstem", ale czyta je
w pomocy wiersza poleceń, nie na ekranie kabiny. Katalog dla nich **nie istnieje**
i ta pozycja go nie tworzy.

## 6. Czego nie zrobiłem

- **Nie dopisałem sita.** Sekcja 4: byłoby bezczynne. Zapisanie tego jest
  odpowiedzią, a dopisanie kodu udawałoby postęp.
- **Nie rozszerzyłem zakresu bramki** — to osobna decyzja, obciążona wynikiem 6.D175.
- **Nie scaliłem wpisów 6.D176 i 6.D181.** Odpowiadam dla 87 pozycji, bo tyle liczy
  rodzina, ale scalenie wierszy w tabeli zmienia kolejkę i należy do właściciela.
- **Nie sprawdzałem, czy pomoc CLI jest gdziekolwiek tłumaczona** — pole „Poza
  zakresem" pozycji wyklucza to wprost.
