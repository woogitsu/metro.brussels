# 6.D180 — całą różnicę robi JEDEN napis wielowierszowy, a poprawne jest liczenie całym plikiem

**12.09.2026**, na `9421ed5`. Wejście: `src/Game/FirstRun.cs`,
`tests/Game.Tests/UiTextTests.cs` (`SlowaWKodzie`, `BezDziur`, `BezJednostek`),
`reports/6d154-rodziny-348-literalow.md` §4. Pozycja żądała wskazania **literału albo
literałów** odpowiedzialnych za różnicę i rozstrzygnięcia, **która droga liczenia jest
poprawna** — a pole „Skończone, gdy" mówiło wprost: *co do literału, a nie co do pliku*.

## 1. Różnica wynosi DWANAŚCIE, a nie trzynaście — i to jest skutek 6.D182

Pozycja zapisała `105` wobec `118`. Dziś jest `106` wobec `118`: wczorajsza naprawa
czytnika literałów przesunęła stronę „całym plikiem" o jeden, bo widzi ona odtąd napis
surowy jako **jeden literał**, a nie jako urwany kawałek. Strona „wierszami" nie drgnęła
i **drgnąć nie mogła** — tam rozcina podział na wiersze, a nie czytnik.

## 2. GŁÓWNY WYNIK: różnica ma JEDEN powód i jest nim JEDEN literał

`src/Game/FirstRun.cs:2232` niesie napis surowy `$$"""` długości czterdziestu wierszy —
metadane JSON zrzutu. Czytany **w całości** jest jednym literałem; czytany **wierszami**
rozpada się, bo cudzysłów zamykający nazwę pola paruje się z otwierającym jego wartość:

```
"engine": "godot",          czytany wierszem  →  "engine"  i  "godot"
                            czytany w całości →  TREŚĆ jednego napisu
```

Rozbicie różnicy, zmierzone kodem bramki:

| | ile | co |
|---|---|---|
| widzi **tylko droga wierszowa** | **14** | `engine`, `godot`, `{{Engine.GetVersionInfo()[`, `resolution`, `view`, `steps`, `scene`, `vertices`, `faces`, `platforms`, `slabs`, `slabs`, `train`, `bodies` |
| widzi **tylko droga całoplikowa** | **2** | ten napis surowy w całości oraz `string` — literał z jego dziury interpolacji |

`14 − 2 = 12`, czyli dokładnie różnica `118 − 106`.

**I to jest wyjaśnienie, a nie sama liczba: każde z tych czternastu zgłoszeń jest
KAWAŁKIEM tego jednego napisu, który droga wierszowa gubi.** Stoi to w bramce jako
pętla `najdluzszy.Contains(kawalek)` — nie jako zdanie w raporcie.

## 3. ROZSTRZYGNIĘCIE: poprawne jest liczenie CAŁYM PLIKIEM

Napisu wielowierszowego **nie da się** czytać wiersz po wierszu: rozcina go **sam podział
na wiersze**, niezależnie od czytnika. Droga wierszowa melduje `engine` i `godot` jako dwa
literały, choć w pliku obie te nazwy są **treścią jednego napisu** — a to jest twierdzenie
o kodzie, które jest po prostu nieprawdziwe.

Droga całoplikowa nie ma odpowiadającej wady: żaden z 21 plików korpusu nie zawiera
konstrukcji, którą czytałaby gorzej.

**`SlowaWKodzie` zostaje nietknięte i to jest zgodne z polem „Poza zakresem"** — zakaz
obowiązywał „dopóki nie wiadomo, która droga jest poprawna", a droga poprawna to ta,
którą bramka już chodzi. Nie ma czego zmieniać.

## 4. Na pozostałych plikach obie drogi zgadzają się CO DO ZERA, nie „co do jedynki"

Pozycja mówiła, że na pozostałych plikach liczby są „równe co do jedynki". Zmierzone dziś
na całym korpusie:

```
ChunkManifest.cs   20/20   GlbLoader.cs      2/2    StreamingPlan.cs    1/1
DesignAssumptions  20/20   FirstRun.cs   106/118    DriverActions.cs    0/0
DriverInput.cs      0/0    EmergencyBrake.cs 0/0    KeyNames.cs         1/1
RunHeader.cs       14/14   RunPlan.cs    140/140    RunReset.cs         0/0
SignallingHud.cs    9/9    TelemetryTrack.cs 13/13  Hud.cs              0/0
ChaseCameraAim.cs   9/9    PlatformFit.cs    1/1    SceneAxis.cs        1/1
StationView.cs      4/4    TrainView.cs      2/2    TunnelView.cs       4/4
```

**Dwadzieścia plików na dwadzieścia jeden daje różnicę ZERO.** „Co do jedynki" sugerowało
szum na wielu plikach; szumu nie ma żadnego. Różnica jest własnością jednej konstrukcji
w jednym pliku, i to jest mocniejsze zdanie niż to, które pozycja postawiła.

## 5. HIPOTEZA POZYCJI JEST NIEPRAWDZIWA — zmierzone, nie odrzucone z ręki

Pole „Skąd" podejrzewało *„literał sklejany przez kilka wierszy, na którym `BezDziur`
rozstrzyga inaczej dla fragmentu niż dla całości"*, i samo nazwało to **hipotezą do
sprawdzenia, nie do przyjęcia**. Sprawdzona na wejściu syntetycznym:

```csharp
var sklejany = "var s = \"pierwszy człon \"\n    + \"drugi człon\";";
// całym plikiem: 2      wierszami: 2      RÓŻNICY NIE MA
```

Literał sklejany przez `+` **nie robi żadnej różnicy**, bo każdy jego człon zaczyna się
i kończy w tym samym wierszu. `BezDziur` nie ma z tą różnicą nic wspólnego. Prawdziwym
powodem jest napis **wielowierszowy**, czyli konstrukcja, której pozycja nie podejrzewała.

## 6. Wejście syntetyczne — i klamra zagnieżdżona, która okazała się konieczna

Pole „Weryfikacja" żądało kontroli pokazującej **mechanizm, a nie liczbę**. Pierwsza
wersja wejścia syntetycznego brzmiała `{ "stacja": "peron" }` i **wyszła zielona
fałszywie**: strona całoplikowa dała **zero**, bo `BezDziur` zdejmuje `[{][^{}]*[}]`,
czyli **cały płaski obiekt JSON**. Porównanie byłoby wtedy zgodnością zera z dwójką
z niewłaściwego powodu.

Wejście ma dziś klamrę **zagnieżdżoną** — `{ "scene": { "peron": 1 } }` — tak jak
prawdziwy napis w `FirstRun.cs`, więc `BezDziur` zdejmuje tylko wnętrze i słowo zostaje.
Konieczność tej klamry stoi w komentarzu przy wejściu, a **KN-4 mierzy ją wprost**:
zdjęcie zagnieżdżenia zapala test.

## 7. Kontrole negatywne — cztery, wszystkie czerwone

Baza: **245/245**. Każda zmienia **jedną** rzecz, po każdej `md5sum -c: OK`.

| | co zmienione | wynik |
|---|---|---|
| KN-1 | droga wierszowa podmieniona na całoplikową | **243/245** — 2 czerwone |
| KN-2 | czytnik literałów z powrotem na stary wzorzec | **241/245** — 4 czerwone |
| KN-3 | gubiony napis wybierany jako NAJKRÓTSZY zamiast najdłuższego | **244/245** |
| KN-4 | wejście syntetyczne bez klamry zagnieżdżonej | **244/245** |

### 7.1. Pierwsza KN-3 była ZIELONA — i to nie było odkrycie, tylko mój błąd konstrukcji

Pierwsza wersja KN-3 **wyłączała asercję** (`true || najdluzszy.Contains(…)`) i wyszła
zielona. Podstawienie **weszło** — `diff` to potwierdził — więc przez chwilę wyglądało to
jak „asercja jest bezczynna".

**Nie jest. Wyłączenie przechodzącej asercji nie może niczego zapalić z definicji** —
`true || X` przechodzi zawsze, więc taka kontrola nie testuje niczego i zielona jest
tautologicznie. Kontrola negatywna musi **fałszować twierdzenie**, a nie wyłączać zdanie,
które je sprawdza. Poprawiona KN-3 podstawia **najkrótszy** gubiony napis zamiast
najdłuższego — wtedy kawałki przestają być jego fragmentami i asercja zapala się, jak ma.

Zapisane tutaj, bo to **trzeci raz w tej sesji**, kiedy zielona kontrola negatywna
znaczyła coś innego, niż wyglądała (6.D182 KN-5 i 6.D183 KN-3 — tam podstawienie nie
weszło; tu weszło, ale kontrola była pusta). Dwie różne pułapki, ten sam objaw.

## 8. Znalezione po drodze: „13 kluczy JSON-a" z 6.D181 to kawałki JEDNEGO literału

6.D181 zapisało w §3, że wśród 90 nazw stoi **„13 kluczy JSON-a, który program
WYPISUJE"**, i wymieniło `"engine":`, `"resolution":`, `"scene":`, `"vertices":`,
`"faces":`, `"platforms":`, `"slabs":`, `"train":`, `"bodies":`, `"last_shot":` —
wyciągając stąd wniosek, że **„rodzina JSON-a liczy 31, nie 18"**.

Dziewięć z tych dziesięciu nazw to **dokładnie** pozycje z kolumny „tylko droga
wierszowa" w §2, czyli **kawałki jednego napisu surowego**, a nie osobne literały.
Dziesiąta (`last_shot`) też w nim stoi, tylko odpada w `SlowaWKodzie` na sicie
identyfikatorów.

**Czego NIE twierdzę:** że 6.D181 liczyło wierszami. Jakim dokładnie skanem doszło do
swojej trzynastki, nie jest zmierzone, a różnica między „wiem" a „bardzo prawdopodobne"
jest w tym projekcie treścią. Twierdzę tylko tyle, ile zmierzyłem: **nazwy, które
6.D181 wymienia, pochodzą z jednego literału**, więc liczenie ich jako trzynastu kluczy
liczy kawałki. Przeliczenie tamtej trzydziestki jedynki to osobna pozycja — **6.D186**.

## 9. Czego świadomie nie zrobiłem

- **Nie tknąłem `SlowaWKodzie`** — §3 mówi dlaczego: poprawna droga to ta, którą bramka
  już chodzi.
- **Nie przeliczyłem „rodziny JSON-a" z 6.D181** — §8, osobna pozycja.
- **Nie zmieniłem `BezDziur`**, choć §6 pokazuje, że zdejmuje on płaski obiekt JSON
  w całości. Jest to zachowanie, którego pozycja nie dotyczy, i zmiana sita przy okazji
  pozycji o czymś innym jest dokładnie tym, czego zakazuje reguła 10 `CLAUDE.md`.
