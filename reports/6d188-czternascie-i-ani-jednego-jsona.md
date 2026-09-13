# 6.D188 — czternaście literałów traci wszystkie słowa, a płaskiego JSON-a nie ma wśród nich ani jednego

**13.09.2026**, na `6d284eb`. Wejście: `tests/Game.Tests/UiTextTests.cs`
(`BezDziur`, `SlowaWKodzie`, `Literaly`, `ZrodlaHud`),
`reports/6d180-jeden-napis-wielowierszowy.md` §6.

## 1. Czego pozycja żądała

Liczby literałów `src/Game/`, którym `BezDziur` zabiera **wszystkie** słowa (są przed,
nie ma po), oraz odpowiedzi, czy któryś z nich dociera na ekran — a jeśli tak, czy jest
tekstem dla gracza.

## 2. Dwie liczby

| | |
|---|---:|
| literałów w korpusie `src/Game/` | **480** |
| z tego z parą klamer | **124** |
| **tracących WSZYSTKIE słowa przez `BezDziur`** | **14** |
| z tych czternastu — na drodze `Hud.Update` | **4** |

Czternaście, w kolejności skanu:

```
DesignAssumptions.cs   {Name} = {Value:R} {Unit} — {Reason}
FirstRun.cs            /{_cabProtection.Protection.EmergencyBrakeMps2:F2} m/s²
FirstRun.cs            |Δ| = {drift:E3} m
FirstRun.cs            ({_axis.LengthM:F3} m), |Δ| = {drift:E3} m > {…:E3} m
FirstRun.cs            {result.TotalDistanceM:F2} m, {result.TotalSeconds:F2} s,
FirstRun.cs            {call.Name},{call.StopId},{call.ChainageM:R},{…}
FirstRun.cs            {call.StopErrorM:R},{call.ArrivalSeconds:R},{…}
DriverActions.cs       {binding.KeyName} {binding.Meaning}          ← na ekran
DriverActions.cs       {b.KeyName} {b.Meaning}                      ← na ekran
SignallingHud.cs       {ostrzezenie}{ingerencja}                    ← na ekran
TelemetryTrack.cs      '{DriveTelemetry.Header}'
TelemetryTrack.cs      '{line}' -> '{rebuilt}'
Hud.cs                 {speedKmh,6:F1} km/h     a = {…,6:F2} m/s²   ← na ekran
TunnelView.cs          {manifest.ProfileWidthM:F2}×{…:F2} m,
```

## 3. PRZESŁANKA POZYCJI PADŁA

Pole „Skąd" mówi, że `BezDziur` „dla literału niosącego płaski obiekt JSON zabiera
treść, o którą bramka pyta". **Mechanizm jest prawdziwy — ale w `src/Game/` nie ma go
ani razu.** Wśród czternastu nie ma **ani jednego** płaskiego obiektu JSON; we
wszystkich czternastu zabrane słowa są nazwami zmiennych z wnętrza dziur, czyli
dokładnie tym, co sito obiecuje zabierać (6.D99).

Odpowiedź na pytanie „czy któryś jest tekstem dla gracza": **cztery docierają na ekran
i ani jedno nie jest tekstem dla gracza.** Docierają jako SZABLONY — tym, co widzi
gracz, są wartości wstawione w dziury, a nie napis, który sito obejrzało.

## 4. Dlaczego `BezDziur` NIE MOŻE schować tekstu dla gracza

Nie jest to zbieg okoliczności na dzisiejszym drzewie, tylko własność strukturalna.
Treścią dziury jest **kod C#**, a jedyną drogą, którą tekst dla człowieka mógłby się
w niej znaleźć, jest **literał zagnieżdżony** — a te `Literaly` zwraca **osobno**
(akapit „Literały z dziur interpolacji ZWRACANE SĄ TEŻ"). Zdjęcie dziury nie zabiera
więc korpusowi ani jednego napisu; zabiera tylko jego kopię stojącą wewnątrz szablonu.

Populacja, w której cokolwiek innego mogłoby stać — pary klamer z cudzysłowem
w środku — liczy w całym korpusie **trzy**:

```
FirstRun.cs   {Engine.GetVersionInfo()["string"]}
RunPlan.cs    {string.Join(" --", KnownArguments)}
RunPlan.cs    {string.Join(", ", KnownViews)}
```

Wszystkie trzy są wywołaniami C#, a ich zagnieżdżone literały (`string`, ` --`, `, `)
**stoją w korpusie osobno** — bramka to sprawdza, a nie zakłada.

Druga strona pokazana na wejściu syntetycznym, bo drzewo jej nie rozdziela (nie ma
dziś ani jednej dziury z polskim napisem w środku):
`$"stan: {(x ? "otwarte" : "zamknięte")}"` daje **dwa osobne** zgłoszenia, w tym
`otwarte`.

## 5. Gdzie mechanizm NAPRAWDĘ mógłby ugryźć — i dlaczego nie gryzie

`BezDziur` to `[{][^{}]*[}]`, czyli zdejmuje **wyłącznie pary najgłębsze**. Płaski
`{ "stacja": "peron" }` jest sam dla siebie najgłębszy i znika w całości. Nosicielem
takiej konstrukcji może być tylko napis surowy `$$"""`, w którym klamry są **treścią**,
a nie interpolacją — a takich w `src/Game/` jest **jeden**: metadane zrzutu
z `FirstRun.cs`. Wszystkie **31** nazw kluczy tego napisu leży **poza** najgłębszymi
parami (tymi są dziury), więc `BezDziur` nie zabiera **ani jednej**: 31 przed, 31 po.

Kontrola na wejściu syntetycznym, wprost z pola „Skąd" pozycji:

```
{ "stacja": "peron" }            → 0 zgłoszeń   (płaski: znika w całości)
{ "scene": { "peron": 1 } }      → 1 zgłoszenie (zagnieżdżony: zostaje)
```

## 6. Sześć kontroli negatywnych, baza 3/3

| kontrola | podstawienie | wynik |
|---|---|---|
| KN-1 | `BezDziur` z leniwym `.*?` zamiast `[^{}]*` | 2/3 |
| KN-2 | jeden literał zdjęty z listy docierających na ekran | 2/3 |
| KN-3 | jeden poziom zagnieżdżenia zdjęty z napisu metadanych | 2/3 — **za drugim podejściem** |
| KN-4 | `Take(0)` w nagłówku pętli po zagnieżdżonych | 2/3 — **za TRZECIM podejściem** |
| KN-5 | jedna para klamer z cudzysłowem zdjęta z listy | 2/3 |
| KN-6 | sito „niesie słowo" bez `BezJednostek` | 2/3 |

### KN-3: zdanie „bo klamry są zagnieżdżone" było za słabe

Zdjęcie z napisu metadanych **jednego** poziomu zagnieżdżenia nie ruszyło niczego —
pozostałe poziomy wystarczyły. Nośna nie jest liczba poziomów, tylko **ile nazw kluczy
leży poza najgłębszymi parami**. Naprawą był pin na tę liczbę (31 przed, 31 po), a nie
przeredagowanie zdania.

### KN-4: asercja na DŁUGOŚĆ LISTY nie pilnuje LICZBY OBROTÓW

Pierwszy raz kontrola wyszła zielona, bo pętla po `ZagniezdzoneWKlamrach` z `Take(0)`
nie wykonywała się wcale, a testu nie miał co zapalić. Dołożyłem asercję na długość
listy — i kontrola wyszła zielona **drugi raz**, bo `Take(0)` długości listy nie zmienia.
Czerwona jest dopiero przy **liczniku obrotów**.

**To jest osobna lekcja od tej z 6.D186 i 6.D187.** Tam zielona kontrola znaczyła
„mechanizm naprawdę bezczynny". Tutaj znaczy „asercja mierzy sąsiada tego, co miała
mierzyć" — i pierwsza poprawka trafiła w tego samego sąsiada drugi raz. Rodzina znana
z `test_lista_wyjatkow_filtrow_nie_gnije`, tyle że tam pustą pętlę pilnuje asercja
o pustości zbioru, a nie licznik.

## 6a. Znalezione po drodze: `maska()` bierze `@"""` za napis SUROWY

Trzy nowe metody testowe **nie były w ogóle widziane** przez bramki czytające ciało
klasy. Przyczyną okazała się linia, którą sam postawiłem dzień wcześniej przy 6.D187:

```csharp
Regex.IsMatch(zrodla, @"Argument\([^)]*""" + nazwa + @"""\)")
```

`maska()` w `tools/tests/test_csharp_test_methods.py` bierze `@"""` za napis
**surowy** (trzy cudzysłowy), szuka domknięcia `"""`, którego nie ma, i maskuje
**wszystko do końca pliku**. Zmierzone na wejściu syntetycznym:

```
x = @"""a"; {}   ->  'x =           '   (klamry zniknęły)
x = @"a"""; {}   ->  'x =       ; {}'   (poprawnie)
```

**Jest to dokładnie ta awaria, dla której `maska()` powstała przy 6.B28** — wyrocznia
zepsuta w stronę „wszystko w porządku", tylko innym wejściem. Dopóki po tej linii nie
było nic, nie było też skutku; trzy metody dopisane niżej wpadły w połkniętą resztę.

**Złapało to porównanie DWÓCH ODCZYTÓW, nie bramka na atrybut:**
`test_the_shape_covers_every_test_attribute` zestawia `source.count` (818)
z czytnikiem strukturalnym (815).

W tej pozycji postawiłem **obejście** — wzorzec przepisany na zwykły napis
z uciekanymi cudzysłowami, z komentarzem mówiącym dlaczego. **Czytnika nie tknąłem**:
to inny moduł i inna robota, wpisana jako **6.D200**.

Drobiazg z tego samego miejsca: pierwsza wersja komentarza cytowała nazwę atrybutu
dosłownie i **podniosła `atrybuty_w_plikach` o jeden**, bo tamten czytnik liczy jego
wystąpienia w TEKŚCIE. Cytat zdjęty, powód zapisany w komentarzu.

## 7. Czego świadomie nie zrobiłem

- **`BezDziur` nie zmieniony ani o znak** — pole „Poza zakresem" mówi wprost, że
  dopóki nie wiadomo, ilu literałów to dotyczy, zmiana sita jest zgadywaniem. Teraz
  wiadomo: czternastu, i żadnemu nie zabiera tekstu dla gracza. **Powód do zmiany
  zniknął razem z pomiarem.**
- **`src/Game/` nie tknięte** — to samo pole.

## 8. Zauważone po drodze, nie tknięte

- `DesignAssumptions.cs` niesie `{Name} = {Value:R} {Unit} — {Reason}` — szablon, który
  na ekran nie dociera (nie ma go w mapie `ZrodlaHud`), ale jest wypisywany do logu
  przejazdu. Czy założenia projektowe mają być po polsku, jest decyzją właściciela
  i pozycji na to nie zakładam.
- Z czternastu **siedem** stoi w `FirstRun.cs`, a z tych siedmiu **trzy** to szablony
  CSV telemetrii. Sito zabiera im wszystko i ma rację: nazwa kolumny nie jest tekstem
  dla gracza. Gdyby kiedyś powstała bramka na nagłówki CSV, musiałaby czytać je
  z innego miejsca niż `SlowaWKodzie`.
