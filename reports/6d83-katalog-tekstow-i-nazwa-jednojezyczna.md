# Teksty interfejsu bez kluczy, nazwa dwujęzyczna nieparsowana (6.D83)

**Zmierzone 10.09.2026 na:** `e12094c`, kontener tej sesji, Godot 4.7.2-stable mono.
**Przyrząd:** przejście po `src/Game` wzorcami, `dotnet test tests/Game.Tests`
i `tests/Sim.Tests`, dwa zrzuty z silnika, pięć kontroli negatywnych z `md5sum -c`
po każdym powrocie.

---

## 1. Pomiar wyjściowy, przeliczony niezależnie

```
literały w Hud.cs                                        14
  z tego ścieżki węzłów sceny                             7
  nazwy właściwości motywu                                3
  szablony wierszy niosące SŁOWA                          3
słowa językowe w tych szablonach                          4   chainage, za, ciąg, hamulec
literały zastępcze w scenie                               7
wywołania Tr( / TranslationServer / .Tr( w src/Game       0
pliki katalogu tekstów (*.po, *.translation)              0
sekcja [internationalization] w project.godot           brak
```

Nazwy stacji **są** brane z danych i **są** dwujęzyczne, ale nigdzie nie było podziału
po separatorze: na ekranie stała dosłownie nazwa złączona kreską.

## 2. Dane mają gotowe pola jednojęzyczne — sprawdzone, a nie założone

```
stacji na sześciu osiach            61
bez `name_fr`                        0
bez `name_nl`                        0
nazw z separatorem `|`              27      (pozostałe 34 identyczne w obu językach)
```

Separator niesie **mniejszość** nazw — i to jest powód, dla którego usterka wyglądała
na drobiazg: przy 34 stacjach z 61 nic nie było widać.

## 3. Nazwa do pokazania jest WYBRANA, a nie parsowana

`AxisStation` dostał `NameFr`, `NameNl` i `DisplayName`. **Nie ma tu podziału po
`|`** — pole „Wyjście" mówi wprost „brana z gotowych pól jednojęzycznych, a nie
parsowana z separatora". Przy braku pola jednojęzycznego `DisplayName` zwraca **całą**
nazwę, a nie jej kawałek; osobny test pilnuje właśnie tego (KN-5 wywraca go
jednolinijkową mutacją `Name.Split('|')[0]`).

**Dlaczego francuska, i to nie z gustu.** Pole `name` ma w danych postać `FR|NL`, więc
francuska jest **pierwszą z pary tak, jak zapisało ją źródło**. Wybór stoi w JEDNEJ
linijce; przełącznik języka i drugi język są w polu „Poza zakresem" tej pozycji
(„robi miejsce, nie treść").

**`Name` zostaje nietknięta i to jest warunek, nie ostrożność.** Po niej idą ślady
przejazdu i porównanie wywołań scena–rdzeń (`assert_line_trace.py`, `--calls`),
których wzorce są przybite sumą SHA-256. Podmiana nazwy tam przeliczyłaby wzorce jako
**skutek uboczny zmiany w interfejsie** — dokładnie to, czego zabrania
`tools/ci/assert_line_trace.py`.

## 4. Katalog tekstów: jeden język, brak klucza jest błędem

`src/Game/UI/UiText.cs` — dwa szablony wierszy, polski jako domyślny, napisy
przeniesione **co do znaku** (razem z angielskim `chainage`, bo zmiana brzmienia
byłaby treścią, a nie miejscem).

**Formatowanie liczb zostało w kodzie** i to jest granica postawiona świadomie:
szablon niesie słowa i kolejność pól, a `F1`, `F0`, `F2`, szerokości pól i jednostki
(`km/h`, `m`, `m/s²`) zostają tam, gdzie były — pole „Skończone, gdy" żąda tego
wprost. Wpuszczenie formatów do katalogu znaczyłoby, że tłumacz może zmienić liczbę
miejsc po przecinku.

**`UiText.Get` rzuca przy braku klucza**, zamiast zwrócić jego nazwę. Katalog
wyświetlający `hud.position` wygląda na ekranie jak usterka tekstu i tak też zostaje
zgłoszony — po dwóch dniach i przez kogoś innego. Tego wprost żąda pole
„Skończone, gdy".

## 5. Zrzut PO, OBEJRZANY

800 x 600, kadr z kabiny przy km 2054 (`Comte de Flandre|Graaf van Vlaanderen`):
wiersz pozycji czyta się
`chainage 2054.1 m / 6686.7 m   Comte De Flandre za 1 m` — **jednojęzycznie i w jednej
linii**, bez zawinięcia, które przy nazwie dwujęzycznej było konieczne (6.D82).

**Dwie pozycje zdjęły ten sam objaw z dwóch stron**, i wpis 6.D83 mówił to z góry
(„Jeden objaw, dwie przyczyny"): 6.D82 dał panelowi szerokość widoku i zawijanie,
6.D83 skrócił napis o połowę. **Zawijanie zostaje i nie jest przez to martwe**:
`Comte De Flandre` mieści się dziś w jednej linii, ale wiersz niesie też kilometraż
i długość osi, więc dłuższa nazwa albo dłuższa oś wrócą pod tę samą granicę. Poprawka
6.D82 przestała być WIDOCZNA na tym kadrze — nie przestała działać, i to jest różnica,
którą warto tu zapisać, zamiast uznać jedną z dwóch pozycji za zbędną.

`tools/ci/assert_no_godot_warnings.py` na obu logach: **0 spoza listy**, 2 środowiskowe.

## 6. Pięć kontroli negatywnych, każda WYKONANA

`md5sum -c` po każdym przywróceniu: `OK`.

| kontrola | mutacja | wynik |
|---|---|---|
| KN-1 | `DisplayName` wraca do nazwy dwujęzycznej | **czerwona** 598/600 |
| KN-2 | używany klucz znika z katalogu | **czerwona** 222/224 (kompletność + martwy wpis) |
| KN-3 | literał językowy wraca do `Hud.cs` (`"brak stacji"`) | **czerwona** 223/224 |
| KN-4 | `Get` zwraca nazwę klucza zamiast rzucać | **czerwona** 223/224 |
| KN-5 | `DisplayName` parsuje separator (`Name.Split('\|')[0]`) | **czerwona** 598/600 |

KN-5 jest tą, która odróżnia **wybór** od **parsowania**: mutacja daje na prawdziwych
danych ten sam wynik co poprawka (bo `name_fr` zgadza się z pierwszym członem), a pada
dopiero na osi bez pola jednojęzycznego — `Expected:<Alfa|Beta>. Actual:<Alfa>`.

## 7. Zapadka podniesiona, z powodem

`MAX_GAME_UNMATCHED_NEEDLES` stoi dziś na **19**, podniesiona z szesnastu. Trzy nowe igły są z założenia bez
dopasowania w komunikatach `src/Game`, bo **nie są komunikatami**:
`hud.nie-ma-takiego` to klucz celowo nieistniejący, a `Panel/Rows` i `font_size` to
ścieżka węzła i nazwa właściwości motywu — obie są **kontrolą przyrządu** skanu
literałów, który ma je widzieć, żeby było co odsiewać. Wzmocnienie tych igieł nie ma
sensu: nie opisują zdania dla człowieka.

## 8. Czego NIE zrobiłem

**Nie dodałem drugiego języka i niczego nie przetłumaczyłem** — pole „Poza zakresem".
**Nie tknąłem `data/`** ani odczytem poza istniejącym, ani zapisem (§4.6).
**Nie przeniosłem do katalogu tekstów z `FirstRun.cs`** (`StationLine`, `Faza`,
`HelpLine`) ani z `DriverActions`/`EmergencyBrake`. Pole „Wejście" tej pozycji wymienia
`Hud.cs`, scenę, `project.godot`, dane osi i `TrackAxis.cs` — `FirstRun.cs` nie jest
tam wymieniony, a te metody składają kilkadziesiąt zdań i mają własne bramki.
W `FirstRun.cs` zmieniłem **trzy słowa**: `approach.Name` → `approach.DisplayName`
w dwóch miejscach i `station.Name` → `station.DisplayName` w trzecim, bo bez tego
nazwa jednojęzyczna nie doszłaby do HUD-u wcale.
**Nie tknąłem siedmiu literałów zastępczych w scenie.** Są tekstem dla EDYTORA, nie
dla gracza: `Hud._Ready` ustawia widoczność, a `Update` podmienia treść przy pierwszej
klatce. Ich przeniesienie do katalogu byłoby wpisem, którego nikt nie czyta.

## 9. Weryfikacja

```
dotnet test tests/Game.Tests
  -> Passed!  Failed: 0, Passed: 224, Total: 224      (przed zmianą: 219)

dotnet test tests/Sim.Tests
  -> Passed!  Failed: 0, Passed: 600, Total: 600      (przed zmianą: 597)

python3 tools/tests/test_all.py
  -> RAZEM 95,608 s, 2143 testów, 113 modułów, kod 0
```

Zrzuty leżą w `build/d83/` i **nie są commitowane** (`build/` ignorowane, §4.8).
