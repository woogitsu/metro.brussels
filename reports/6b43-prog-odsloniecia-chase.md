# Próg odsłonięcia widoku goniącego — dziewięć punktów, nie dwanaście (6.B43)

**Zmierzone 09.09.2026 na:** `6582eea`, kontener tej sesji.
**Przyrząd:** `xvfb-run -a godot --rendering-driver opengl3 --resolution 1280x720
--path src/Game -- --shot=… --at-chainage=… --view=chase`, ułamek pikseli policzony
przez `tools/visual/pngio.py` (`read_gray`), oraz `dotnet test tests/Game.Tests`.

---

## 1. Co zrobione

Próg odsłonięcia jest osobną stałą — `DesignAssumptions.ChaseRevealFromM = 110,0 m` —
a `ChaseCameraAim.Availability` bierze go jako **wymagany** parametr i liczy granicę
jako `max(długość składu, próg)`. Odmowa zrzutu i szósty wiersz HUD-u podają **jedną**
liczbę: 110,0 m. Pasmo 94..110 m, odsłonięte świadomie 05.09.2026, jest domknięte
decyzją właściciela z 07.09.2026.

## 2. Pomiar — i dlaczego punktów jest dziewięć, a nie dwanaście

Pole „Skończone, gdy" żądało pasma 90..112 m co 2 m, czyli **dwunastu** punktów.
Zmierzyć da się **dziewięć**, i powód jest tą samą regułą, którą pozycja rusza:

```
cel=90  kod=13  plik=BRAK
cel=92  kod=13  plik=BRAK
cel=94  kod=13  plik=BRAK
cel=96  kod=0   chainage=96.0 m
cel=98  kod=0   chainage=98.0 m
…
cel=112 kod=0   chainage=112.1 m
```

Trzy pierwsze punkty **odmawiają zrzutu kodem 13**, bo stara granica (`front >
94,0 m`) należy do pasma ukrycia — narzędziem, które samo jest tą regułą, nie da się
zmierzyć kadru pod nią. Nie jest to brak pomiaru: to pomiar mówiący, że pasma
90..94 m nie ma czym obejrzeć bez zdjęcia reguły, a zdjęcie reguły byłoby zmianą
przedmiotu pomiaru.

Ułamek pikseli o jasności ≥ 0,80 w **górnych 60 %** kadru (432 z 720 wierszy),
1280×720, ta sama miara co w 6.B11:

| kilometraż | jasnych pikseli | udział |
|---:|---:|---:|
| 90, 92, 94 | — | zrzut odmówiony (kod 13) |
| **96** | 258 084 | **46,67 %** |
| 98 | 0 | 0,00 % |
| 100 | 0 | 0,00 % |
| 102 | 0 | 0,00 % |
| 104 | 0 | 0,00 % |
| 106 | 0 | 0,00 % |
| 108 | 0 | 0,00 % |
| 110 | 0 | 0,00 % |
| 112 | 0 | 0,00 % |

**Dziura z 6.B11 jest szeroka na JEDEN punkt, nie na dwadzieścia metrów.** Tamta seria
miała 90 m → 0,0 %, 96 m → 42,0 %, 110 m → 0,0 % i wyglądała na 20-metrowe pasmo
o nieznanym kształcie. Gęstsza siatka mówi: jasny jest wyłącznie 96 m, a od 98 m
w górę jest zero na każdym punkcie. Liczba 46,67 % wobec 42,0 % z 05.09.2026 to ten
sam objaw na innym przebiegu — tam mierzony na `--line --limit-kmh=70`, tu na
`--shot --at-chainage`.

**Czyste pasmo zaczyna się więc na 98 m, a nie na 110 m** — i tego właśnie żądało
pole „Wyjście": *„jeżeli pomiar pokaże, że czyste pasmo zaczyna się wcześniej niż
110 m, liczba właściciela zostaje, a raport nazywa różnicę"*. Różnica wynosi
**12 m**. Liczba 110 m jest decyzją, nie wynikiem, i tak stoi zapisana przy stałej.

## 3. Co widzę na zrzutach — obejrzane, nie odczytane z metryki

Miara „0,00 % jasnych pikseli" nie odróżnia czystego kadru od **pustego**, więc trzy
zrzuty zostały obejrzane.

- **96 m** — kadr jest w trzech czwartych zajęty przez wielką, prawie białą płytę
  z zaokrąglonymi górnymi narożnikami: to tylna ściana pudła M7 zalana światłem
  reflektora, z jasnym rozbłyskiem w środku. Ściany tunelu widać wyłącznie przy
  krawędziach kadru, jako ciemnoszare kliny. HUD podaje `chainage 96.0 m / 6686.7 m`,
  `7.3 km/h`. Dokładnie ten obraz, dla którego pozycja istnieje.
- **98 m** — kadr czyta się jako tunel: rura schodzi do punktu zbiegu, widać oba
  chodniki i strop, a tylna ściana pudła jest szarym prostokątem w środku kadru,
  zajmującym może czwartą część wysokości. Jasnych pikseli zero, ale kadr **nie jest
  pusty** — i to jest różnica, której metryka nie widzi.
- **106 m** i **112 m** — obrazy prawie identyczne: pudło małe, wyśrodkowane, cały
  przekrój tunelu i oba chodniki czytelne. Identyczność nie jest przypadkiem —
  odstęp kamery to `front − 94 − 12` przycięte do zera, więc pełne 12,0 m odstępu
  jest osiągnięte już na 106 m i dalej się nie zmienia. To potwierdza liczbę 106 m
  z 6.B11 jako prawdę o **kadrze**, nie o dostępności.

## 4. Kształt zmiany

`max(długość składu, próg)`, a nie sam próg, i to nie jest ozdoba: gdyby skład był
kiedyś dłuższy niż próg, granicą musi zostać długość składu — inaczej kamera wróciłaby
do wnętrza skorupy, czyli do usterki zamkniętej 05.09.2026. Próg odsuwa granicę
**dalej, nigdy bliżej**, i ma na to własny test.

Parametr `revealFromM` jest **wymagany**, bez wartości domyślnej. Domyślna równa
długości składu przywróciłaby po cichu stan sprzed tej pozycji w każdym miejscu,
które o próg nie zapyta — czyli byłaby tą samą usterką, którą ta pozycja zamyka,
tylko czekającą na następnego wołającego.

**Powód odmowy rozdzielony na dwie połowy pasma.** Zdanie „kamera siedzi w skorupie
składu" było prawdziwe, dopóki pasmo kończyło się na długości składu. Po odsunięciu
granicy na 110 m to samo zdanie na 96..110 m **byłoby nieprawdziwe**: kamera jest już
za ogonem (przy czole 100 m odstęp wynosi 6,0 m, co przybija istniejący test).
`ChaseAvailability` dostało więc czwarte pole (`TrainLengthM`) — do NAZWANIA powodu,
nie do policzenia granicy — a zdanie mówi „pasmo ukrycia z decyzji właściciela" tam,
gdzie powodem jest decyzja.

## 5. Weryfikacja — wyjścia wklejone

```
$ xvfb-run -a godot … --shot=…/po-96.png --at-chainage=96 --view=chase
96 m kod: 13
[ZRZUT] widok chase niedostępny — pasmo ukrycia z decyzji właściciela; dostępny po minięciu 110.0 m, jeszcze 14.0 m; zrzut na 96.0 m nie powstaje — kadr byłby płytą pudła, a plik nazywałby się chase
plik: BRAK

$ xvfb-run -a godot … --shot=…/po-112.png --at-chainage=112 --view=chase
kod: 0
[ZRZUT] …/po-112.png 1280x720 err=Ok widok=Chase kroków=712 chainage=112.1 m v=21.9 km/h

$ dotnet test tests/Game.Tests
Passed!  - Failed: 0, Passed: 215, Skipped: 0, Total: 215

$ dotnet test tests/Sim.Tests
Passed!  - Failed: 0, Passed: 593, Skipped: 0, Total: 593

$ python3 tools/tests/test_all.py
  2059/2059 przeszło
  RAZEM 129.481 s, 2059 testów, 109 modułów
KOD ZESTAWU: 0
```

Założenie wypisuje się w przebiegu razem z pozostałymi:

```
[ZAŁOŻENIE widok] ChaseRevealFromM = 110 m — kilometraż, po minięciu którego odsłania się
widok goniący; DECYZJA właściciela z 07.09.2026, nie wynik pomiaru — pomiar co 2 m
z 09.09.2026 mówi, że czysty kadr zaczyna się już na 98 m …
```

## 6. Kontrola negatywna — i jej drugi przebieg, który wykrył słabą asercję

Pole „Skończone, gdy" żądało: powrót progu do długości składu wywraca test na nową
granicę. Mutacja `ChaseRevealFromM = 110.0` → `94.0`:

```
  Failed TheChaseViewIsUnavailableUntilTheRevealThreshold
  Failed TheBandBoundaryIsTheOwnerDecisionAndNotTheRegisteredTrainLength
  Failed TheRemainingDistanceCountsDownToTheBoundary
  Failed AnUnavailableViewSaysWhyAndFromWhere
  Failed TheReasonNamesTheRightCauseInEachHalfOfTheBand
Failed!  - Failed: 5, Passed: 210
```

Pięć testów, wszystkie o nowej granicy, ani jednego niepowiązanego. **Ale test
o rozejściu twierdzeń przeszedł** — i to jest znalezisko tej kontroli, nie jej wynik
uboczny: przy progu równym długości składu pasmo rozejścia `(94,0; 94,0]` jest
**puste**, warunek fałszywy na każdym punkcie i cała pętla po 0..300 m przechodzi.
Test o rozejściu był więc zielony nad stanem, w którym rozejścia nie ma.

Doszła asercja na **niepustość** pasma (64 punkty = 16,0 m / 0,25 m), po czym ta sama
mutacja wywraca **sześć** testów:

```
  Failed TheChaseViewIsUnavailableUntilTheRevealThreshold
  Failed TheBandBoundaryIsTheOwnerDecisionAndNotTheRegisteredTrainLength
  Failed AvailabilityNoLongerAgreesWithTheFramingAndThatIsTheWholePoint
  Failed TheRemainingDistanceCountsDownToTheBoundary
  Failed AnUnavailableViewSaysWhyAndFromWhere
  Failed TheReasonNamesTheRightCauseInEachHalfOfTheBand
Failed!  - Failed: 6, Passed: 209
```

`md5` `src/Game/DesignAssumptions.cs` przed mutacją i po każdym przywróceniu:
`162a4a4eff0a8e6b8a981d99b269a620`.

**Druga asercja zaostrzona przy okazji, z tego samego powodu.** Test odmowy żądał, żeby
zdanie na granicy nie zawierało słowa „jeszcze", i przechodził **wyłącznie dlatego**,
że tekst powodu tego słowa nie zawierał — czyli pilnował sufiksu przez cechę zdania
obok. Dziś pyta o `"jeszcze 0.0"` wprost i dodatkowo żąda, żeby zdanie KOŃCZYŁO SIĘ
kilometrażem.

## 7. Dwie własne pomyłki, obie złapane pomiarem

- **Pierwsze zamiatanie dało dwanaście razy kod 134 i zero plików.** Powód: `nohup
  bash` nie odziedziczył `DOTNET_ROOT`, więc Godot nie znalazł hostfxr —
  `sh: 1: dotnet: not found` → `Failed to load hostfxr` → kod **134**. Rozpoznane
  w jednym spojrzeniu, bo tę sygnaturę zmierzyłem trzy godziny wcześniej w 6.D24
  (`reports/6d24-biblioteka-natywna.md`): log mówi `signal 11`, a powłoka widzi 134.
  Bez tamtego pomiaru byłoby to zgadywanie.
- **Zrzut na 96 m raz „przeszedł" po zmianie i nie powinien.** Powód: kontrola
  negatywna zbudowała `MetroBxl.Game.dll` z progiem 94,0 m, a przywrócenie źródła
  **nie przebudowuje** DLL-a, z którego scena startuje. Artefakt na dysku był starszy
  od źródła i to on odpowiadał na pytanie. Po `dotnet build src/Game` odmowa wróciła
  z kodem 13. Zapisuję, bo to najtańsza możliwa wersja tej pułapki: pomiar mierzył
  intencję, nie stan.

## 8. Czego świadomie nie zrobiłem

- **Nie ruszyłem liczby 110 m.** Pomiar mówi 98 m; 110 m jest decyzją właściciela
  z 07.09.2026 i pole „Wyjście" żąda, żeby decyzja została, a raport nazwał różnicę.
- **Nie tknąłem kompozycji kadru goniącego** — odstępu, wysokości, punktu celowania.
  Pozycja rusza granicę dostępności, nie estetykę (pole „Poza zakresem").
- **Nie mierzyłem pasma pod 94 m gęściej**, bo nie da się: zrzut odmawia kodem 13,
  a zdjęcie reguły na czas pomiaru zmieniłoby przedmiot pomiaru. 6.B11 zmierzyło je
  inną drogą (`--line`) i te liczby zostają jej pomiarem.
- **Nie zmieniłem `data/vehicle/m7-spec.json`** ani niczego w `data/`.

## 9. Zauważone przy okazji, nie tknięte

**Pole „Weryfikacja" tej pozycji podawało polecenie w formie, której runner nie zna:**
`$GODOT_BIN --path src/Game -- --shot --view=chase --at-m=96 --out=build/chase-96.png`.
Scena czyta `--shot=PLIK` (ścieżka w tej samej opcji, nie osobne `--out`) i
`--at-chainage=X`, nie `--at-m=X`; `--shot` bez wartości i `--at-m` nie istnieją.
Bramka pól tego nie łapie, bo nazwy opcji nie są ścieżkami — czyli jest to **trzeci
wariant** tej samej rodziny co martwe pole z 6.D59 (ścieżka od kropki) i katalog
z 6.A21 (brak rozszerzenia). Licznik wzorca „pole podaje coś, czego nie da się
wykonać, a bramka tego nie widzi" stoi po tej pozycji na **sześciu**; zgłoszenie
wchodzi do kolejki przy najbliższym jej uzupełnieniu, razem z pomiarem z 6.A21 §8.
