# 6.D174 — prefiks da się zmierzyć, miejsce użycia tą metodą nie

**12.09.2026**, na `b4274dd`. Wejście: `tests/Game.Tests/UiTextTests.cs`,
`src/Game/FirstRun.cs`, `src/Game/Assets/GlbLoader.cs`, `src/Game/TelemetryTrack.cs`.
Pozycja pyta, która z dwóch cech ma być granicą diagnostyki: **prefiks w nawiasie
kwadratowym** (cecha TEKSTU) czy **wywołanie wypisujące** (cecha MIEJSCA UŻYCIA).

## 1. Dróg wyjścia są trzy, nie jedna

Pierwsza rzecz sprawdzona, zanim cokolwiek policzyłem — bo przy 6.D181 zadeklarowałem
kontekst JSON-a jako sam odczyt i przez to zobaczyłem połowę rodziny:

```
$ grep -rhoE "GD\.[A-Za-z]+|Console\.[A-Za-z]+" src/Game --include=*.cs
     25 GD.Print
      4 GD.PushError
      2 GD.PrintErr
```

Zadeklarowanie samego `GD.Print` powtórzyłoby tamten błąd. Pomiar obejmuje wszystkie
trzy.

## 2. Prefiks: 75, i ta liczba nie zależy od niczego

| okno kontekstu | oba | prefiks bez wyjścia | **prefiks razem** |
|---:|---:|---:|---:|
| 1 | 12 | 63 | **75** |
| 3 | 25 | 50 | **75** |
| 8 | 25 | 50 | **75** |
| 15 | 28 | 47 | **75** |
| 30 | 32 | 43 | **75** |

Prefiks jest **cechą literału**, więc liczba jest ta sama niezależnie od tego, jak
szeroko patrzę wstecz. Kryterium jest mierzalne i powtarzalne.

## 3. Miejsce użycia: od 12 do 77, zależnie wyłącznie od tego, co wybiorę

| okno | wyjście bez prefiksu | **przez wyjście razem** |
|---:|---:|---:|
| 1 | 0 | **12** |
| 3 | 10 | **35** |
| 8 | 35 | **60** |
| 15 | 38 | **66** |
| 30 | 45 | **77** |

Liczba rośnie monotonicznie i **nie zbiega się**. Powód jest strukturalny, nie
techniczny: **wiersz nie jest jednostką instrukcji**. Wypisy w tym kodzie są sklejane
z kilku, czasem kilkunastu wierszy — prefiks stoi na pierwszym fragmencie, wywołanie
na początku instrukcji, a fragmenty dalsze nie mają ani jednego, ani drugiego:

```
prefiks bez wyjścia:   FirstRun.cs: [OŚ] nie da się otworzyć {axisPath}: …
                       FirstRun.cs: [LINIA] oś {_axis.Id} ma {_axis.Stations.Count} stacji,
wyjście bez prefiksu:  FirstRun.cs: {_replay.Entries.Count} zmian klawiszy
                       FirstRun.cs: kroki {_track.FirstStep}..{_track.LastStep}
```

Przy oknie wąskim gubię fragmenty dalsze; przy szerokim zaczynam łapać literały,
które z wypisem nie mają nic wspólnego — bo trzydzieści wierszy po `GD.Print` to już
zupełnie inny kod. **Każde okno daje inną odpowiedź i żadne nie jest uzasadnione.**

## 4. Odpowiedź pozycji

**Granicą może być prefiks.** Jest cechą tekstu, mierzalną dokładnie, niezależną od
metody skanowania — 75 wystąpień, niezmiennie.

**Granicą nie może być wywołanie wypisujące — nie dlatego, że jest złym kryterium,
tylko dlatego, że tej bramce nie da się go zmierzyć.** `SlowaWKodzie` pracuje na
tekście, a przypisanie literału do instrukcji wymaga rozbioru składni C#, czyli
narzędzia innej klasy niż wyrażenie regularne. Dopóki bramka czyta wiersze, „czy to
idzie do `GD.Print`" jest pytaniem bez powtarzalnej odpowiedzi.

Pole „Skończone, gdy" żądało trzech liczb. Dwie z nich istnieją (prefiks 75, część
wspólna przy oknie 1: 12), trzecia **nie jest liczbą, tylko przedziałem 12–77** —
i to jest wynik, a nie brak pomiaru.

## 5. Czego nie zrobiłem

- **Nie wybrałem prefiksu jako sita.** Pozycja miała rozstrzygnąć, **która cecha
  może być granicą**; wpisanie sita do bramki to decyzja o jej zakresie i osobna
  robota. Do tego prefiks obejmuje 75 z ~85 tej rodziny, więc kilkanaście wypisów
  zostałoby poza nim — to trzeba policzyć osobno.
- **Nie sięgnąłem po rozbiór składni C#.** Byłoby to dodanie zależności i zmiana
  klasy narzędzia; `CLAUDE.md` §8 każe się w takim miejscu zatrzymać i zapytać.
- **Liczba 361 zamiast 348** to znany skutek liczenia wiersz po wierszu (6.D180);
  proporcje w tabelach są nią policzone i nie mieszam ich z liczbą całoplikową.
