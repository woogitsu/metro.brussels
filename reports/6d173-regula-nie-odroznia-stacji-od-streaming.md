# 6.D173 — kształt nie odróżnia `stacja` od `streaming`, więc reguła nie wchodzi

**12.09.2026**, na `0ad3e45`. Wejście: `tests/Game.Tests/UiTextTests.cs`
(`SlowaWKodzie`, `ZrodlaGry`, `KodBezKomentarzy`), `src/Game/**/*.cs`. Pozycja pyta
w tytule „reguła czy zakres?" — odpowiedź brzmi: **ani jedno, ani drugie w całości**,
i obie połowy są zmierzone.

## 1. Ile reguła obejmuje

Pomiar kodem bramki, na korpusie 348 zgłoszeń:

| reguła | objętych |
|---|---:|
| wąska `^[a-z_][a-z0-9_]*$` | **96** (całym plikiem) / **108** (wiersz po wierszu) |
| szeroka, z myślnikiem albo kropką | **123** |

Wszystkie 96 to **35 różnych wartości** i każda jest angielskim identyfikatorem:

```
arrived assets axis brake cab calls chase chunks collision file headless id inspect
jitter level line lods manifest manual name outside platforms profile replay shell
shot signalling streaming string telemetry throttle totals triangles variant view
```

Ani jednego polskiego słowa. **I to jest dokładnie miejsce, w którym najłatwiej
ogłosić, że reguła jest bezpieczna.**

## 2. Co reguła by przepuściła — i to jest odpowiedź pozycji

Pytanie nie brzmi „czy dziś coś przepuszcza", tylko „czy **umie** odróżnić
identyfikator od polskiego słowa". Zmierzone tą samą bramką, na sześciu polskich
słowach bez znaku diakrytycznego:

```
stacja :zglaszany=True :przepuscilaby=True
pociag :zglaszany=True :przepuscilaby=True
peron  :zglaszany=True :przepuscilaby=True
drzwi  :zglaszany=True :przepuscilaby=True
postoj :zglaszany=True :przepuscilaby=True
hamulec:zglaszany=True :przepuscilaby=True
```

Każde z tych sześciu jest **dziś przez bramkę zgłaszane**, a proponowana reguła
przepuściłaby **wszystkie**. Kształt nie ma czym odróżnić `streaming` od `stacja` —
obie są ciągiem małych liter bez spacji.

Pole „Skończone, gdy" tej pozycji mówi wprost: *jeśli przepuszcza cokolwiek — reguła
nie wchodzi*. **Reguła nie wchodzi.** Zero dzisiejszych przepuszczeń nie jest
argumentem za nią: mówi o tym, jakie napisy akurat stoją w korpusie, a nie o tym,
co sito potrafi.

## 3. Zakres zamiast kształtu — obejmuje 18 ze 108

Druga połowa pytania z tytułu. Jeżeli granicą ma być nie kształt napisu, tylko
**miejsce użycia** — czytanie JSON-a — to zmierzone wychodzi:

```
P173B|waskaWierszami=108|wKontekscieJson=18|poza=90
poza, przykłady: FirstRun.cs: manual, axis, assets, manifest, chunks, shell,
                 platforms, arrived, headless, engine, godot, resolution
```

Kontekst czytania JSON-a (`GetProperty`, `GetString`, `RootElement`) obejmuje
**18 ze 108**. Pozostałe **90** to w przeważającej części nazwy sekcji i trybów
w `FirstRun.cs`, które z JSON-em nie mają nic wspólnego.

Zakres jest więc **prawdziwy, ale wąski**: rozstrzyga 17 % rodziny i zostawia 90
pozycji bez odpowiedzi. Nie jest to porażka pomiaru — jest to wynik mówiący, że
rodzina „108 identyfikatorów" **nie jest jedną rodziną**, tylko dwiema: polami JSON
(18) i nazwami sekcji/trybów w `FirstRun.cs` (90).

## 4. Rozbieżność 96 kontra 108 potwierdza 6.D180 drugi raz

Ta sama reguła policzona całym plikiem daje **96**, a wiersz po wierszu — **108**.
Różnica 12 pojawia się tam, gdzie 6.D154 zmierzyło różnicę 13: w `FirstRun.cs`.
Jest to **drugie niezależne trafienie w to samo zjawisko**, tym razem przy liczeniu
czego innego. Wzmacnia to 6.D180 i nic w niej nie zmienia — rozstrzygnięcie, która
droga liczenia jest poprawna, nadal tam należy.

## 5. Czego nie zrobiłem

- **Nie dodałem żadnego sita do bramki.** Pozycja kończy się odpowiedzią „nie", a nie
  kodem. Wpisanie reguły, która przepuszcza `stacja`, byłoby cichym wyłączeniem
  bramki na całej rodzinie jednowyrazowych napisów — i wyglądałoby jak postęp.
- **Nie rozstrzygnąłem tych 90.** To osobna rodzina i osobne pytanie; wchodzi
  do kolejki jako 6.D181.
- **Nie sprawdzałem listy słów polskich** jako alternatywy. Projekt odrzucił listy
  nazw na rzecz reguł przy 6.D130 i ten powód nie zniknął: lista rośnie z każdym
  nowym napisem i jest drogą powrotną dla tego, co bramka miała wykluczyć.
