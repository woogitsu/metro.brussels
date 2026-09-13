# MB-02 — przejazd gracza kończy się sam, a koniec sesji to nie koniec procesu

**13.09.2026**, na `199afb4`. Wejście: `src/Game/FirstRun.cs`, `src/Game/RunReset.cs`,
`src/Sim/Train/StationService.cs`, `StationStop.cs`, `RunRestart.cs`, `LineRun.cs`,
`docs/PLAYABILITY.md` §3, audyt grywalności §3.

## 1. Co weszło

| plik | co |
|---|---|
| `src/Sim/Train/TrainingSession.cs` | warunek końca przejazdu gracza; zatrzask wyniku; liczniki ATP po zboczu |
| `src/Sim/Train/TrainingResult.cs` | `TrainingEnding`, `TrainingTarget`, `TrainingResult` — fakty, nie punkty |
| `src/Game/UI/RunSummary.cs` | panel wyniku jako tekst, bez Godota |
| `src/Game/UI/UiText.cs` | osiem kluczy `summary.*` |
| `src/Game/UI/Hud.cs`, `src/Game/Scenes/FirstRun.tscn` | ósma etykieta, startuje ukryta |
| `src/Game/FirstRun.cs` | budowa sesji z osi, obserwacja na końcu kroku, gałąź panelu, wypis `[SESJA]` |
| `src/Sim/Train/RunRestart.cs`, `src/Game/RunReset.cs` | sesja w JEDNEJ liście „co obejmuje reset" |
| `tests/data/mb02-dwa-postoje.log` | wzorzec zapisu wejść na dwa postoje |
| `.github/workflows/godot-first-run.yml` | bramka punktu 6 odbioru M1 + jej kontrola negatywna |

## 2. Pułapka z audytu potwierdzona pomiarem — i jest GORSZA, niż audyt pisał

Audyt ostrzegał, że `_done` odcina `R` i `Esc`. Zmierzone: `_done` stoi
w `FirstRun.cs:350`, jego `return` w `_Process` na **`:1010`**, a odczyt klawiatury
dopiero na **`:1015-1030`**. `HandleViewKeys` (`:1495-1522`) jest **jedynym** czytnikiem
`DriverActions.Quit` (Esc), `Reset` (R) **oraz `ViewToggle` (C)** — więc `_done`
odciąłby **trzy** klawisze, nie dwa.

Rozwiązanie: koniec sesji zatrzymuje **ticki**, a nie klatki, i `_done` nie ustawia.
Gałąź stoi **za** odczytem klawiatury i przepuszcza klatkę, gdy `_resetPending` —
bo klatka reset tylko **zamawia**, a wykonuje go `StepOnce`. Bez tego wyjątku `R`
ustawiałoby zamówienie, którego nikt by nie odebrał.

Czasu spędzonego na panelu nikt nie nadrabia: `AdvanceBy` nie jest wtedy wołane, więc
akumulator kroków nie dostaje ani jednej sekundy tych klatek.

## 3. Cele idą po IDENTYFIKATORACH, a w kodzie stoi wyłącznie ICH LICZBA

`docs/PLAYABILITY.md` §3 żąda: „cele wyszukiwane po identyfikatorach z osi;
kilometraży nie kopiuje się do logiki". Decyzją projektową jest **liczba** celów
(`DesignAssumptions.TrainingTargets = 2`) i to, że są to pierwsze stacje za punktem
startowym; **które** to stacje, mówi `data/track/L1_A.json`. Wpisane `8742` i `8292`
byłyby drugą kopią danych i milczałyby po zmianie osi — pilnuje tego bramka
`CELE_SESJI_WYCHODZA_Z_OSI_A_NIE_STOJA_W_KODZIE`.

Konstruktor odrzuca **cel będący punktem startowym osi** i to jest najważniejsza z jego
czterech kontroli: `StationService` pomija stację o indeksie 0 (`:87-91`, `:155`), więc
taki cel nie trafiłby **ani** do `Calls`, **ani** do `Missed`. Sesja czekałaby na niego
bez końca, a wyglądałoby to na **zawieszoną grę**, nie na błędne zadanie.

## 4. Zdarzenie ATP to ZBOCZE — i `docs/PLAYABILITY.md` §3 jest z tego powodu PRZEPISANE

Plan mówił: „Liczniki ATP liczą **kroki interwencji**, nie incydenty". Decyzja
właściciela poszła w drugą stronę: **policz osobne zdarzenia**. Akapit jest przepisany,
a nie dopisany obok, bo plan i kod nie mogą mówić dwóch różnych rzeczy.

Semantyka jest mechaniczna i przez to nie wymaga rozstrzygania przy każdym nowym
rodzaju ingerencji: **zdarzeniem jest zbocze predykatu**. Konsekwencja wypisana wprost,
żeby nie była niespodzianką — eskalacja służbowa → awaryjna daje **jedno** zdarzenie
ingerencji (predykat nie zgasł) i **jedno** awaryjne.

**Liczniki kroków w `CabProtection` zostają nietknięte.** Odpowiadają na inne pytanie
(„ile przejazdu spędzono nad limitem") i tylko one na nie odpowiadają: dziesięć sekund
nad limitem to jedno zdarzenie i 1200 kroków. Obie liczby są prawdziwe.

## 5. Dwanaście kontroli negatywnych, baza 618/281 — i TRZY ZIELONE, każda wytłumaczona

| kontrola | podstawienie | wynik |
|---|---|---|
| KN-1 | `IsFinite(DepartureSeconds)` → `!= double.NaN` (zawsze prawda) | **618 ZIELONA** |
| KN-1b | warunek `IsFinite` zdjęty całkiem | **618 ZIELONA** |
| KN-1c | strażnik `AtStation` zdjęty, `IsFinite` zostaje | **618 ZIELONA** |
| KN-2 | zbocze → krok (licznik rośnie w każdym kroku predykatu) | 615/618 |
| KN-3 | `Reset()` nie czyści pamięci zboczy | **615 ZIELONA**, po poprawce **617/618** |
| KN-4 | zatrzask wyniku zdjęty | **615 ZIELONA**, po poprawce **617/618** |
| KN-5 | kontrola punktu startowego zdjęta z konstruktora | 614/615 |
| KN-6 | minięcie celu nie kończy sesji | 614/615 |
| KN-7…KN-12 | bramki leksykalne wpięcia (patrz `TrainingWiringTests`) | zapalają się każda osobno |

`md5sum -c` na trzech plikach po każdej: `OK`.

### 5.1. KN-1/1b/1c — dwa warunki opisują TEN SAM fakt, i każdy z osobna wystarcza

Trzy kontrole, trzy zielenie. Zmierzone, nie wywnioskowane: `stations.AtStation` gaśnie
dokładnie wtedy, gdy `StationStop` domyka cykl — czyli **w tym samym kroku**, w którym
`StationService` wpisuje `DepartureSeconds`. Strażnik prędkości i wpis wywołania to
dwa odczyty jednego faktu.

**Redundancja zostaje**, bo kontrakt M1 mówi o „drzwiach zamkniętych **i** składzie
stojącym", a `AtStation` jest dosłownie pierwszą połową tego zdania. Ale przestaje być
martwa: doszedł test, który przechodzi **cały cykl drzwi krok po kroku** (ponad 1400
kroków przy wymianie 4,0 s) i w **każdym** sprawdza, że `!AtStation` równa się
`IsFinite(DepartureSeconds)`. Gdyby `StationService` kiedyś rozdzielił te stany, jeden
z warunków stałby się nośny — i dowiem się o tym z bramki, a nie z zachowania gry.

KN-1b i KN-1c **zostają zielone także po tej poprawce** i to jest poprawne: każdy
z warunków sam wystarcza, więc zdjęcie jednego niczego nie psuje. Nowy test nie pilnuje
ich z osobna — pilnuje **zgodności**, bo to ona jest tu jedyną rzeczą, która może pęknąć.

### 5.2. KN-3 — test resetu czyścił pamięć zboczy PRZEBIEGIEM TESTU, nie `Reset()`

Kontrola zdjęła zerowanie `_overspeedHeld`/`_interveningHeld`/`_emergencyHeld`
i zestaw został zielony. Powód, zmierzony: stary test resetował sesję **po postoju**,
a postój obserwowany jest z `protection = null`, co samo gasi predykat. Pamięć zbocza
była więc czyszczona po drodze, a `Reset()` nie miał czego czyścić.

Nowy test resetuje **w środku trwającej ingerencji** — czyli dokładnie wtedy, kiedy
gracz naciska `R`, bo ATP hamuje. Po poprawce KN-3 zapala się: **617/618**.

### 5.3. KN-4 — test zatrzasku obserwował skład W RUCHU i nie dochodził do zatrzasku

Kontrola zdjęła zatrzask (`if (_result is not null) return;`) i zestaw został zielony.
Powód: stary test wołał `Observe` po zakończeniu sesji na składzie **jadącym**, a wtedy
`Observe` wychodzi na strażniku prędkości, **zanim** dojdzie do przeliczenia wyniku.
Ten test nie ćwiczył zatrzasku ani razu.

Nowy test trzyma skład **stojący na peronie ostatniego celu** — tam, gdzie zostawia go
koniec sesji i gdzie gracz czyta panel — i wykonuje 600 obserwacji. Bez zatrzasku
`TotalSeconds` rosłoby o każdą klatkę patrzenia na wynik. Po poprawce: **617/618**.

**Jest to trzeci raz w tej sesji, gdy zielona kontrola okazuje się przewidywalna
i wytłumaczona, a nie przeoczona — i pierwszy, gdy z wyjaśnień wyszły TRZY nowe
asercje naraz**, a nie jedna.

## 6. Przejazd wykonany NAPRAWDĘ, a nie opisany

```
$ GODOT_BIN=… godot --headless --path src/Game -- \
      --assets=$PWD/build/t400 \
      --signalling=$PWD/data/design/signalling/classic-2026.json \
      --replay=$PWD/tests/data/mb02-dwa-postoje.log --steps-per-frame=600

[SESJA] zaliczone (AllTargetsServed): 2/2 celów, 156.842 s, 1357.513 m, ATP 0/0/0 \
        | 8742 obsłużony błąd -0.023 m | 8292 obsłużony błąd -0.387 m
```

Wiersz `[SESJA]` wyszedł **dokładnie raz** przy 20 000 kroków zapisu, z czego 1179
kroków przypada **po** zakończeniu sesji.

Kontrola negatywna tej bramki — zapis przycięty do 15 000 kroków, czyli urwany, gdy
skład jeszcze hamuje do drugiego celu:

```
[ODTWORZENIE] koniec: kroków=15000 t=125.000 s chainage=1320.222 m …
[SESJA] trwa: cele 8742, 8292, obsłużonych 1
```

**Przycięcie do 8880 kroków — zasięgu `manual-keys.log` — okazało się mutacją
NIEWAŻNĄ**, i to jest pomiar, nie domysł: czytnik zapisu odrzuca ją wcześniej
(„Wpis 5 obowiązuje od kroku 8900, a przejazd ma 8880 kroków"). Kontrola padłaby wtedy
na walidacji pliku, a nie na warunku końca sesji, i nie mówiłaby nic o tym, co miała
sprawdzić. Stąd 15 000.

## 7. Wzorzec zapisu jest NOWY, bo starego nie da się do tego użyć

`manual-keys.log` kończy się 8880 krokami na **569,701 m**, czyli tuż za pierwszym
celem: obsługuje **jeden cel z dwóch** i sesja przy nim nie kończy się nigdy. Żadne
przycięcie ani rozciągnięcie tego nie zmieni.

Krok hamowania **14470 jest wynikiem trzech pomiarów**, nie upodobania:
14000 → czoło 1373,179 m (78,7 m przed celem), 14300 → 1423,179 m (28,7 m przed),
14500 → błąd **+4,613 m**, czyli w oknie ±5,000 m, ale **0,387 m od jego krawędzi**.
Wzorzec stojący 0,387 m od granicy przewracałby się przy pierwszej zmianie modelu
trakcji i wyglądałoby to na usterkę sesji, a nie na przesunięcie fizyki. 14470 daje
**−0,387 m**, czyli 4,6 m zapasu po każdej stronie.

## 8. Trzy rzeczy, których nie da się wypchnąć z węzła — i co z nimi zrobiłem

`FirstRun` jest węzłem Godota, więc żaden test jednostkowy go nie wywoła. Wiedza
wychodzi z niego od 6.D99 (`RunReset`, `RunHeader`, `RunPlan`), ale **kolejność
i warunki w ciele metody** wypchnąć się nie dają: gdzie w kroku stoi `Observe`, że
koniec sesji nie ustawia `_done`, i że reset przekazuje sesję do `RunReset.Apply`.

`tests/Game.Tests/TrainingWiringTests.cs` czyta więc **źródło** — tak samo jak
`UiTextTests` od 6.D83 i z tego samego powodu. Nie udaje przy tym, że sprawdza
zachowanie: zachowanie sprawdza przebieg w CI, a te bramki sprawdzają, że dwie rzeczy
niewidoczne w telemetrii nie rozjadą się po cichu.

## 9. Rozstrzygnięcie, które 6.D197 ODŁOŻYŁO — bo drugi switch po wyliczeniu właśnie się pojawił

6.D197 zmierzyło, że w `src/Game/` jest **jeden** switch po wartości wyliczeniowej,
i zapisało: „gdy pojawi się drugi, asercja go pokaże — i dopiero wtedy jest o czym
rozstrzygać". `RunSummary.Naglowek` jest tym drugim.

Rozstrzygnięcie: uogólnieniem **nie jest liczba, tylko RAMIĘ DOMYŚLNE.** 6.D197
zmierzyło na `src/Sim/`, że wszystkie osiem switchy postaci wyrażeniowej ma ramię
**rzucające**, a jedyne ramię **ciche** w całym drzewie stoi w `FirstRun.Faza` i jest
świadome. `RunSummary.Naglowek` rzuca — dołącza więc do rodziny większej, a nie zakłada
drugiej. Doszła lista `SwitcheZCichymRamieniem` z jednym wpisem i asercja, która
zapala się na każdym nowym milczku.

## 10. Zapadki podniesione w tym samym commicie

`ASERCJI_RAZEM` = 2868 (było 2756) i `Z_KOMUNIKATEM_RAZEM` = 1419 (było 1307);
`BEZ_KOMUNIKATU_RAZEM` (
**nie drgnęło ani o jeden**) — bramka zapaliła się na 43 asercjach bez powodu
i wszystkie 43 powód dostały. `PINY_RDZENIA` = 76 (było 74), rozkład pinów liczbowych
rdzenia 441 → 458 i gry 215 → 216; rozkład sześciu postaci literału w `src/` i `tests/`;
`MAX_GAME_UNMATCHED_NEEDLES` = 46 (było 31) i `MIN_GAME_NEEDLES` = 84 (było 65); dwadzieścia liczb
w `UiTextTests.cs`; pięć kotwic pinów przesuniętych o trzy wiersze; README 53 → 55.

**Jedna z nich poszła w stronę, która nie jest przeliczeniem:** `ZeSlowemNaEkranie`
urosło 22 → 24, ale **liczba napisów DLA GRACZA została 22**. Dwa nowe literały to
człony komunikatu **wyjątku** z `RunSummary.Naglowek` — ten tekst na ekran nie dociera,
tylko przerywa klatkę. Skan liczy je, bo `Naglowek` stoi na mapie `ZrodlaHud`, czyli
jest to trafienie **fałszywe** tej samej rodziny co `FalszyweTrafieniaSkanu` z 6.D185.
Doszła lista `NieDocierajaceNaEkran`, która je odejmuje, i kontrola przyrządu tej listy:
wpis, którego skan nie widzi, odejmowałby zero i wyglądałby na działający.

## 11. Czego świadomie nie zrobiłem

- **Pauzy nie ma.** Pole „Skończone, gdy" jej nie wymienia, a wymagałaby nowego klawisza,
  czyli nowego wpisu w `InputMap` i decyzji właściciela o tym, który to klawisz.
  Preambuła pozycji ją opisuje, ale opis własności to nie kryterium odbioru.
- **Okna nie widziałem.** Godot jest, ekranu nie ma. Punkty 2–5 odbioru M1 zostają
  niewykonane po mojej stronie; punkt 6 dostał bramkę CI i jest wykonany.
- **`FirstRun` nie został przebudowany** — pole „Poza zakresem" mówi to wprost.
  Gałąź panelu to dziewięć wierszy w `_Process` i jedno pole.
- **Punktacji, kar i gwiazdek nie ma.** `docs/PLAYABILITY.md` §3: wynik to fakty.

## 12. Zauważone po drodze, nie tknięte

- **`StationService.Filter` po `Finished` zwraca polecenie BEZ FILTRA** (`:223-226`),
  a `Approach` oddaje `NaN` (`:194-197`). Za ostatnią stacją osi cykl drzwi i blokada
  trakcji przestają więc istnieć. Dla MB-02 nieszkodliwe — trening kończy się dziesięć
  stacji wcześniej — ale dla MB-07 i MB-08 to otwarta gałąź.
- **`StationService.Filter` wpisuje co najwyżej JEDNĄ stację do `Missed` na wywołanie**
  (`:241-250`, `return` zaraz po `_next++`). Nigdzie nieopisane; test przeskakujący dwa
  perony jednym krokiem musi o tym wiedzieć.
- **`StationStop.Filter` posuwa licznik postoju niezależnie od prędkości** (`:79-82`),
  więc drzwi domykają się także na składzie w ruchu. Wykorzystane w testach jako
  właściwość, ale nikt tego nie rozstrzygnął jako zamierzone.
- **Równość `record struct` z `NaN` nie zachowuje się jak operator `==`:**
  syntetyzowana równość idzie przez `EqualityComparer<double>.Default`, który traktuje
  `NaN` jako równy `NaN`. Projekt nie opiera się na tym w żadną stronę — wynik porównuje
  się przez `ToString()` — ale zdanie „record struct z NaN nie będzie równy sam sobie"
  jest **nieprawdą** i nie zostało w tym commicie nigdzie użyte.
