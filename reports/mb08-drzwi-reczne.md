# MB-08 — drzwi ręczne i odbiór Issue #26

**14.09.2026**, na `0ae0acf`, gałąź `claude/mb08-drzwi-reczne`. Wejście:
`src/Sim/Train/DoorCycle.cs`, `StationStop.cs`, `LineDrive.cs`,
`src/Sim/Line/LineCore.cs`, `src/Game/`, `InputMap`, kryteria Issue #26.

## 1. Co się zmieniło, w jednym zdaniu

Skład prowadzony przez CZŁOWIEKA dostaje na postoju drzwi **ręczne** — otwiera je
`D`, zamyka `F`, a między jednym a drugim drzwi stoją otwarte tak długo, jak chce
maszynista; skład prowadzony przez autopilota dostaje ten sam cykl automatyczny,
co przed tą pozycją, **co do bajtu**.

## 2. Rozstrzygnięcie, z którego wynika cała reszta: TRYB IDZIE ZA WŁAŚCICIELEM, ale zamraża się przy ZAKŁADANIU POSTOJU

Pole „Weryfikacja" MB-08 żąda dwóch rzeczy, które przy niestarannym połączeniu
wykluczają się nawzajem: żeby gracz miał drzwi ręczne **i** żeby „take/release
w czasie cyklu **nie resetowało drzwi**". Tryb zmieniany w każdym kroku razem
z właścicielem wymagałby przenoszenia stanu między dwiema różnymi maszynami faz,
a każde takie przeniesienie byłoby regułą wymyśloną na miejscu.

Wybrane rozwiązanie: `LineDrive.DoorControl` opisuje postój **NASTĘPNY**, a nie
bieżący. `LineCore` ustawia je w fazie 3 z właściciela sterowania, a `StationStop`
czyta je RAZ — w kroku, w którym postój powstaje. Trwający postój trzyma więc swój
tryb bez względu na to, ile razy sterowanie zmieni ręce, i warunek z pola
„Weryfikacja" jest spełniony **z definicji**, a nie przez osobny zabieg.

### 2a. Skutek uboczny, który musiał zostać rozwiązany: OSIEROCONE DRZWI

Maszynista może stanąć, otworzyć drzwi i **oddać sterowanie**. Jedyne polecenie
zamknięcia w trybie ręcznym pochodzi od człowieka, a człowieka już nie ma — bez
dodatkowej reguły skład stałby z otwartymi drzwiami do końca przejazdu, z zerowym
nastawnikiem, czyli **linia po prostu by stanęła**, i to bez ani jednego komunikatu.

Odpowiedzią jest pole „Wyjście" wzięte dosłownie („obsługa **tych samych reguł**
przez AI"): autopilot, który zastaje postój ręczny bez człowieka przy nastawniku,
**wciska te same dwa polecenia** — otwiera, gdy drzwi są zamknięte, i zamyka po
`PassengerExchangeSeconds`, czyli po tym samym założeniu scenariusza, którym rządzi
się jego własny cykl automatyczny. Nie jest to druga maszyna drzwi dla AI; to ta sama
maszyna z drugim palcem na przycisku.

### 2b. Druga rzecz, której nie dało się pominąć: ODJAZD BEZ OBSŁUGI

W trybie ręcznym drzwi startują ZAMKNIĘTE, więc trakcja jest wolna od pierwszego
kroku postoju i maszynista może po prostu odjechać. Bez warunku na to skład jechałby
dalej **gałęzią postoju** przez resztę osi: `_next` nigdy by się nie posunął,
hamowanie do następnej stacji nigdy nie zostałoby policzone, a przejazd nie skończyłby
się nigdy. Usterka byłaby cicha — HUD pokazywałby drzwi zamknięte, a skład jechał.

Warunek wymaga **ruchu**, nie samego położenia, i to jest pomiar, nie ostrożność.
Okno zatrzymania w `LineDrive` jest **jednostronne** (`chainage >= target -
StopWindowM`, bez ograniczenia od góry), więc skład, który przestrzelił peron o kilka
metrów, staje i dostaje normalny postój. Pierwsza wersja warunku pytała tylko
o położenie i zamykała taki postój **w tym samym kroku, w którym powstał** —
zmierzone na ręcznym przejeździe osi syntetycznej: trzy stacje, trzy postoje,
wszystkie zamknięte natychmiast, zatrzymanie na 2005,72 m przy stacji 2000,00 m
i oknie 5,00 m.

## 3. Bez przejęcia nie zmienia się ANI JEDEN BIT — zmierzone dwiema drogami

Nie „testy przechodzą", tylko bezpośrednie porównanie plików. Ślad przed zmianą
policzony na czystym `origin/main` (`git worktree`), po zmianie — na gałęzi.

```
$ for AXIS in L1_A L1_B L2_E L5_C L5_D L6_F; do
      dotnet run --project src/Sim.Runner -c Release --no-build -- line \
          --axis "data/track/$AXIS.json" --limit-kmh 72 --exchange-s 20 \
          --trace "$TRACES/$AXIS.csv" > /dev/null
  done
  515807 total
[SLAD] sześć osi zgadza się z wzorcem co do bajtu
kod=0

L1_A IDENTYCZNY
L1_B IDENTYCZNY
L2_E IDENTYCZNY
L5_C IDENTYCZNY
L5_D IDENTYCZNY
L6_F IDENTYCZNY
```

Druga droga — przez `LineCore` z planem sygnalizacji, czyli przez tę samą klasę,
której dotyczy zmiana właściciela:

```
$ dotnet run ... -- line --axis data/track/L1_A.json --limit-kmh 72 --exchange-s 20 \
      --signalling data/design/signalling/classic-2026.json --trace …
LineCore L1_A IDENTYCZNY CO DO BAJTU (101873 wierszy)
854feab0d296e7740a78af3a37d77c68  …/L1_A.przed.csv
854feab0d296e7740a78af3a37d77c68  …/L1_A.po.csv
```

**Pomiar był sprawdzony pod kątem własnej pustki**, bo raz już mnie to kosztowało
(MB-07: scena wczytywała stary DLL, a ja opisałem to jako zawieszenie kodu). Biblioteka
użyta przez runnera zawiera nowe symbole:

```
$ strings src/Sim.Runner/bin/Release/net10.0/MetroBxl.Sim.dll | grep -c "RequestOpen\|DoorRefusal"
2
$ ls -l --time-style=full-iso …/MetroBxl.Sim.dll
… 2026-09-14 15:10:52 …          (ślad policzony 15:11)
```

## 4. Blokada trakcji jest w obu trybach TA SAMA — i to jest liczba, nie zapewnienie

Główny test `ManualDoorsTests` nie pyta „czy w fazie otwartej nie wolno jechać".
Pyta, ile KROKÓW najkrótszy cykl ręczny trzyma nastawnik na zerze, i porównuje to
z cyklem automatycznym o zerowej wymianie pasażerów:

```
najkrótszy cykl ręczny            1021 kroków   (1020 faz stałych + 1 krok w fazie otwartej)
zablokowanych kroków              1020
StepsFor(MinimumDwellSeconds)     1020
```

Równość znaczy, że gracz nie dostał łagodniejszej reguły niż AI — dostał tę samą
regułę z innym źródłem czasu fazy otwartej. Fazę otwartą w trybie ręcznym kończy
WYŁĄCZNIE polecenie; `PassengerExchangeSeconds` nie ma tam wstępu, bo w tym trybie
długość tej fazy podaje człowiek, a podstawianie założenia scenariusza byłoby
udawaniem, że wie o niej ktoś jeszcze.

## 5. Kontrole negatywne — dziesięć, każda WYKONANA, `md5sum -c: OK` po każdej

**Baza jest podana przy każdej kontroli osobno i jest to konieczne, a nie pedantyczne:**
zestawy rosły W TRAKCIE tej pozycji, więc jedna liczba bazy dla wszystkich dziesięciu
byłaby nieprawdziwa dla ośmiu z nich — a to jest dokładnie ten błąd, za który MB-06
dostało osobny commit poprawkowy („liczba powtórzona w trzech miejscach musi być
w trzech miejscach ZMIERZONA albo w jednym, a w pozostałych dwóch ZACYTOWANA").

| kontrola | co podmieniono | baza | wynik |
|---|---|---|---|
| KN-1 | cykl ręczny rusza sam po zatrzymaniu | 647/647 | 1 czerwony (`Cykl_reczny_nie_rusza_sam…`) |
| KN-2 | `RequestOpen` przyjmuje na składzie w ruchu | 647/647 | 1 czerwony |
| KN-3 | faza otwarta kończy się po `PassengerExchangeSeconds` | 647/647 | 1 czerwony |
| KN-4 | tryb ręczny nie blokuje trakcji | 647/647 | **3 czerwone** |
| KN-5 | przywrócony skrót „wróć wprost, gdy skład jedzie" | 647/647 | 1 czerwony |
| KN-6 | gotowość do odjazdu oderwana od `TractionAllowed` | 303/303 | 2 czerwone |
| KN-7 | podpowiedź ma pierwszeństwo przed odmową | 303/303 | 1 czerwony |
| KN-8 | klawisze drzwi wypadają z `OnlyWithTheLine` | 303/303 | 1 czerwony |
| KN-9 | klawisz drzwi bez zbocza (`if (doorOpenKey)`) | 303/303 | **ZIELONA — patrz §6** |
| KN-9 bis | to samo, po dopisaniu bramki z §6 | 306/306 | 1 czerwony |
| KN-10 | wczesny powrót gubi stan klawiszy drzwi | 306/306 | 1 czerwony |

Baza rdzenia urosła 633 → **657** (KN-1…KN-5 padały przy 647, bo
`ManualDoorsOnLineTests` powstało po nich), baza warstwy gry 296 → **306**.

## 6. KN-9 WYSZŁA ZIELONA i została WYTŁUMACZONA POMIAREM, a nie załatana

Warunek `if (doorOpenKey && !_doorOpenKeyHeld)` zamieniony na `if (doorOpenKey)` —
czyli polecenie wysyłane w KAŻDEJ klatce, w której klawisz jest trzymany — dał
**303/303, kod 0**.

Powód jest dokładnie ten sam, co przy KN-4 pozycji MB-03: cały ten kod stoi
w `FirstRun`, klasie dziedziczącej po węźle Godota, której żaden test jednostkowy
nie zbuduje. Zieleń nie znaczyła „to nie jest usterka" — znaczyła „bramka tego nie
widzi". Że jest usterką, widać z arytmetyki HUD-u: przy trzymanym `D` pierwsze
polecenie przechodzi, a każde następne wraca odmową „drzwi są już otwarte", i to
ODMOWA ląduje w wierszu, bo ma pierwszeństwo przed podpowiedzią — gracz dostaje
komunikat o błędzie po czynności, która się UDAŁA.

Naprawa idzie tą samą drogą, co przy MB-03: **bramka leksykalna czytająca źródło**
(`tests/Game.Tests/HandleTrainKeysGateTests.cs`). Każdy klawisz czytany w
`HandleTrainKeys` musi mieć warunek `x && !_…Held`, przypisanie `_…Held = x;`
oraz zapamiętanie stanu **przed wczesnym powrotem**. Bramka ma własną kontrolę
przyrządu (skan MA widzieć wszystkie pięć odczytów), bo sito widzące zero przechodzi
pętlę zero razy i melduje zieleń tak samo, jak sito widzące wszystko.

Po bramce **KN-9 zapala się** (1 czerwony), a KN-10 — ta sama rodzina, drugi kształt
— też.

## 7. Dwa napisy HUD-u wyszły z `FirstRun` do pliku BEZ GODOTA

`src/Game/UI/DoorPrompt.cs`, ta sama decyzja i ten sam powód, co przy `TractionBlock`
(MB-03): napis złożony ze stanu przejazdu da się sprawdzić testem jednostkowym tylko
wtedy, gdy jego przeczytanie nie wymaga silnika. Stąd `DoorPromptTests` w ogóle mogą
istnieć, i stąd KN-6 i KN-7 są czerwone, a nie zielone.

**Sygnał gotowości do odjazdu z pola „Wyjście" NIE JEST osobnym stanem.** Pyta
o `DoorCycle.TractionAllowed`, czyli o ten sam predykat, którym rdzeń zeruje
nastawnik. Test tego nie sprawdza na jednej fazie — porównuje **zbiór** faz,
w których HUD pisze „można odjechać", ze zbiorem faz, w których rdzeń zwalnia
trakcję, i żąda równości. Pytanie postawione na jednej fazie miałoby tę samą
odpowiedź także wtedy, gdyby oba zdania rozjechały się w ósmej.

Z tego samego powodu `DoorPrompt.For` **nie jest** `switch`em po fazie: ramię domyślne
połknęłoby ósmą fazę po stronie „skrzydła w ruchu" bez pytania kogokolwiek.

## 8. `DwellRemainingSeconds` na postoju ręcznym zwraca NaN

Nie zero i nie liczbę. Zero znaczyłoby „już koniec", a liczba z
`PassengerExchangeSeconds` byłaby założeniem scenariusza podanym jako pomiar.
Widok ma na to **gałąź**, a nie formatowanie: trzeci wariant wiersza stacji
(`hud.station.doors-manual`) nie ma pola „jeszcze N s", bo nie ma czego w nim
wypisać — `NaN.ToString("F1")` to napis „NaN”.

## 9. Zapadki podniesione w TYM SAMYM commicie, każda z powodem

| zapadka | było → jest | powód |
|---|---|---|
| `checkedNames` (jednoliterowe) | 8 → 10 | `D`, `F` |
| `sprawdzone` (przypisania) | 10 → 12 | `door_open`, `door_close` |
| `NazwyKlawiszyWZasieguBramki` | +`D`, +`F` | zbiór, nie liczba; obie jednoliterowe, więc wniosek o nieosiągalnej kolizji zostaje |
| `LiteralowWZasieguBramki` | 557 → 573 | przeliczone przebiegiem |
| `PozycjiStaregoCzytnika` | 598 → 614 | ten sam korpus drugą drogą |
| `LiteralowNaEkranie` | 101 → 115 | dziewięć kluczy `DoorPrompt` + dwa klawisze |
| `KluczyKatalogunaEkranie` | 44 → 56 | jak wyżej |
| `LiteralowDotknietychZdejmowaniem` | 381 → 393 | większy korpus, **liczba werdyktów stoi na dwóch** |
| `SwitchyWGameRazem` | 3 → 4 | `DoorPrompt.Reason`; `DoorPrompt.For` świadomie nim NIE jest |
| `SwitchyPoWyliczeniuWGame` | 2 → 3 | jw.; rozstrzygnięcie z MB-02 (uogólnieniem jest RAMIĘ) zostaje |
| `SwitcheZCichymRamieniem` | +`DoorPrompt.cs:refusal` | drugi świadomy milczek, powód przy metodzie |
| `WyliczenWSrc` | 18 → 20 | `DoorControl`, `DoorRefusal` |
| `NazwPodWyliczeniem` | 25 → **35** | patrz niżej |
| `ToStringRegeksemPoSurowym` | 5 → 6 | `refusal.ToString()` |
| `ToStringLeksykalnieWGame` | 2 → 3 | jw.; relacja `leksykalnie < surowo` zostaje (3 < 6) |
| `ToStringNaWyliczeniuWGame` | 1 → 2 | jw. |
| `ToStringNaEkranieWGame` | 1 → 2 | oba idą NA EKRAN, do logu i telemetrii nadal ANI JEDNO |

### 9a. TEZA 6.D198 ZOSTAŁA OBALONA W POŁOWIE, i to jest wynik, a nie liczba

Po MB-06 brzmiała: „dwuznaczności nie potrzebują nowych typów, a nowe typy nie muszą
ich przynosić". Druga połowa właśnie padła. Dwa nowe typy przyniosły **dziesięć** nazw
(`Control`, `DoorControl`, `StopDoorControl`, `_control`, `control`, `Refusal`,
`_doorRefusal`, `refusal`, `_manualPhase`, `powodOdmowy`) — więcej niż wszystkie ruchy
tej liczby od 02.09.2026 razem wzięte.

Różnica wobec `ControlOwner` (zero nazw) i `TrainingEnding` (dwie) jest strukturalna:
tamte są ODCZYTEM stanu, a te dwa są ARGUMENTEM i WYNIKIEM — tryb wchodzi
konstruktorem i polem, powód odmowy wraca z metody i ląduje w polu widoku. **Typ,
który podróżuje, dostaje nazwę w każdym miejscu, przez które przechodzi.**

### 9b. Jedna nazwa lokalna kosztowała trzy bramki, zanim została zmieniona

Zmienna `powod` w `DoorPrompt.For` wciągnęła dziurę `{powod}` z `ChaseCameraAim`
na listę dziur z wyliczeniem na drodze `Hud.Update` i wywróciła trzy bramki, z których
ani jedna nie dotyczy drzwi. Nazwa `powodOdmowy` tego nie robi. Zapisane przy kodzie,
bo to nie jest gust — bramka dwuznacznych nazw z 6.D185 rozpoznaje je LEKSYKALNIE.

## 9c. ZESTAW NARZĘDZI WYSZEDŁ CZERWONY ZA PIERWSZYM RAZEM — 2451/2466, piętnaście bramek

Zapisuję to, bo najpierw ogłosiłem ten przebieg zielonym: odczytałem `kod=0`
z **opakowania** komendy, a nie z zestawu, i to była nieprawda o własnej pracy.
Zestaw kończy się kodem 0 także wtedy, gdy część modułów pada — liczba
`N/M przeszło` jest jedynym wiarygodnym odczytem.

Trzynaście z piętnastu to zwykłe zapadki do przeliczenia (wypisane w §9). Dwie
złapały coś więcej:

**(1) PIĘĆDZIESIĄT CZTERY ASERCJE BEZ KOMUNIKATU** w trzech nowych plikach
(`DoorPromptTests` 4, `ManualDoorsOnLineTests` 15, `ManualDoorsTests` 35). To ta
sama pomyłka, którą `test_lista_asercji_C_bez_komunikatu_moze_tylko_malec` złapała
mi przy MB-06 — tam na pięciu asercjach, tu o rząd wielkości więcej. Mechanizm jest
za każdym razem ten sam: pisząc nowy plik testowy przyjmuje się, że komunikat należy
się asercji „niejasnej", a `Assert.AreEqual(DoorRefusal.TrainMoving, result.Refusal)`
wygląda na jasną — dopóki nie padnie w cudzym przebiegu CI, gdzie widać samą nazwę
metody i dwie wartości bez zdania o tym, co miały znaczyć. **Komunikaty dopisane,
pliki NIE trafiły na listę wyjątków.**

**(2) IGŁA `otwarte` PRZESTAŁA BYĆ SYNTETYCZNA.** Bramka
`test_every_needle_matches_at_most_one_message_or_is_justified` pokazała, że napis
`"otwarte"` — wejście **syntetyczne** w teście czytnika dziur (`UiTextTests.cs`) —
pasuje od tej pozycji do **dwóch** komunikatów `src/Game/` naraz: `hud.door.open`
(„otwarte") i nowego `hud.doors.refusal.already-open` („drzwi są już otwarte").

Dało się to zdjąć obniżeniem zapadki `MAX_GAME_UNMATCHED_NEEDLES` z 48 na 47
i **byłoby to załatanie objawu**: igła nie zaczęła mierzyć drzewa, tylko przestała
być syntetyczna. Poprawione po stronie TESTU (`otwarte` → `rozsunięte`), a zapadka
została na 48 — z komentarzem, dlaczego NIE spadła.

## 10. Odbiór Issue #26 — każdy punkt ma dowód albo JASNO OPISANY BRAK

### 10.1 Minimalny flow użytkownika (dziewięć kroków)

| # | krok | stan | dowód |
|---|---|---|---|
| 1 | uruchom scenariusz | **jest** | `--line`, `RunPlan`, bramka `godot-first-run.yml` |
| 2 | linia działa autonomicznie z kilkoma składami | **jest** | MB-07, `--trains`, `LineCore` |
| 3 | kamera może przeskoczyć między pociągami | **jest** | MB-07, klawisz `N` |
| 4 | wybierz skład → take control | **jest** | MB-07, klawisz `T` |
| 5 | steruj traction/brake zgodnie z authority | **jest** | MB-06, `Supervisor` za oboma właścicielami |
| 6 | zatrzymaj się przy Parc/Park | **jest** | `LineDrive` okno zatrzymania, `StationCall` |
| 7 | obsłuż drzwi przez T-312 | **ta pozycja** | `D`/`F`, `ManualDoorsOnLineTests.Pelne_flow…` |
| 8 | odjedź; pozostałe składy nadal pod AI | **jest** | `LineCore` krokuje wszystkie składy |
| 9 | release control zwraca skład w bezpiecznym stanie | **jest** | MB-06 + §2a tego raportu |

### 10.2 Sterowanie

| pozycja | stan |
|---|---|
| traction increase/decrease | **jest** (`W`/`S`) |
| brake increase/decrease | **jest** (`S`) |
| emergency brake | **jest** (Spacja) — i jest to **pełny hamulec SŁUŻBOWY**; osobnego modelu awaryjnego NIE MA i ta pozycja go nie wprowadza (pole „Rzecz do rozliczenia OSOBNO") |
| door release/open/close tylko gdy state machine pozwala | **jest** (`D`/`F`, odmowa z powodem) |
| camera switch | **jest** (`C`) |
| take/release control | **jest** (`T`/`O`) |
| niezależność od układu klawiatury | **jest** — `physical_keycode` w `project.godot`, przybite `DriverActionsTests` |

### 10.3 HUD diagnostyczny (trzynaście pozycji)

| pozycja | stan |
|---|---|
| sim time | **BRAK** — HUD podaje kilometraż i stan, nie zegar symulacji; wiersz `[SESJA]` podaje czas dopiero na końcu przejazdu |
| train id / course id | **BRAK na ekranie** — identyfikator składu istnieje (`TrainIdAt`), ale HUD go nie wypisuje; obserwowany skład poznaje się po kamerze |
| speed m/s + km/h | **CZĘŚCIOWO** — HUD podaje km/h; m/s nie ma |
| chainage | **jest** (`hud.position`) |
| traction/brake command | **jest** (`hud.controls`) |
| current acceleration | **jest** (`hud.speed`, `a = … m/s²`) |
| target/permitted speed | **jest** (sufit w `hud.speed`, `v_dop` w wierszu sygnalizacji) |
| movement authority endpoint/distance | **jest** (wiersz sygnalizacji) |
| signalling mode | **jest** (wiersz sygnalizacji) |
| door state | **jest** (wiersz stacji, od tej pozycji także tryb i podpowiedź) |
| **platform side** | **BRAK, decyzja właściciela z 14.09.2026** — patrz §10.5 |
| timetable delta | **BRAK** — rozkład jest w T-320 (takt 5:10/5:40), a scena go nie zna |
| FPS / render stats osobno od sim tick rate | **BRAK** — scena nie wypisuje ani jednego wiersza o klatkach |

### 10.4 Weryfikacja funkcjonalna

| pozycja | stan |
|---|---|
| headless Sim i scena kończą tym samym stanem przy tych samych komendach | **jest** — `godot-first-run.yml` porównuje `--calls` i telemetrię co do bajtu |
| przejęcie/oddanie nie resetuje position/speed/course | **jest** — MB-06, test z tolerancją 0 |
| AI pozostałych składów działa w czasie prowadzenia | **jest** — MB-07 |
| nie można ominąć ATP przez input gracza | **jest** — MB-06 §1a: ochrona stoi ZA oboma właścicielami, w obu gałęziach |
| **drzwi nie otwierają się w ruchu** | **jest — ta pozycja**: `DoorRefusal.TrainMoving`, przybite w rdzeniu i na poziomie linii |
| kamera nie powoduje ticków Sim | **jest** — kroki liczy `StepOnce`, kamera tylko czyta |
| 30/60/120 FPS daje ten sam stan po tej samej liczbie ticków | **jest** — `DriverNotch` (krok, nie klatka), tabela w opisie klasy |
| brak importów Godota w `src/Sim/` | **jest** — krok bramki w `sim-tests.yml`, `grep` po całym katalogu |

### 10.5 Strona peronu — BRAK Z POWODEM, nie przeoczenie

Pole „Weryfikacja" MB-08 żądało **odmowy otwarcia po niewłaściwej stronie**. Tej
odmowy nie da się dziś wykonać, bo **danych o stronie peronu w tym repozytorium NIE
MA**, i jest to sprawdzone, a nie założone:

```
data/stations/package-a.json stacji: 12
   platform_configuration: {'value': None, 'status': 'unknown', 'source_ids': [],
     'reason': 'Ani GTFS, ani opisy tekstowe STIB nie orzekają o układzie peronów
     (island/side/interchange). Wymaga planu albo obserwacji terenowej.'}   × 12
```

Dwanaście stacji na dwanaście. `CLAUDE.md` §4.1 zabrania zgadywać dane o sieci —
strona peronu wpisana „na oko" wygląda dokładnie tak samo jak prawdziwa, dopóki ktoś
z Brukseli w to nie zagra. **Decyzja właściciela z 14.09.2026: zapisać jako brak
w odbiorze #26 i domknąć MB-08 bez tej odmowy.** Pole „Weryfikacja" pozycji jest z tego
powodu **przepisane**, a nie obchodzone — żądało rzeczy, której ta sieć nie może dać.

Odmowy, które zostają i działają: **w ruchu** (`TrainMoving`) i **poza blokiem
peronowym** (`OutsidePlatformWindow`).

## 11. Czego świadomie NIE zrobiłem

- **`replay` nie obejmuje poleceń drzwi**, i jest to ten sam powód, co przy MB-06
  („przybicie formatu bez wołającego byłoby przybiciem kształtu, którego nikt nie
  czyta"), tyle że tym razem **sprawdzony w kodzie**: gałąź `LineCore` w
  `FirstRun.StepOnce` nie woła `_recorder.Record` ANI RAZU, a `Sim.Runner replay`
  prowadzi skład przez `StationService`, który zna wyłącznie cykl automatyczny. Zapis
  wejść w wersji 3 miałby więc pisarza, którego nie ma, i czytelnika, który nie ma
  co z nim zrobić. Warunkiem wstępnym jest połączenie `--replay` z `--line`; wchodzi
  do kolejki jako osobna pozycja.
- **`StationService` zostaje wyłącznie automatyczny.** Tryb ręczny istnieje tam, gdzie
  istnieje WŁAŚCICIEL sterowania, czyli w `LineCore`. Przejazd ręczny kabiną nie ma
  `TakeControl`, więc nie ma tam czego przejmować ani komu oddawać drzwi.
- **Sceny nie uruchomiłem** — w tym środowisku nie ma Godota (`GODOT_BIN` puste,
  `command -v godot` nic nie zwraca), a `CLAUDE.md` §2 każe w takiej sytuacji
  powiedzieć o tym wprost, a nie obchodzić. Warstwę gry sprawdzają: `Game.Tests`
  (306/306), bramka leksykalna z §6 i job `godot-first-run` w CI.
- **Kolumny „czy kogokolwiek obsłużono" w `Calls` nie ma.** Stacja minięta w trybie
  ręcznym zostaje w `Calls` z czasem odjazdu, bo skład tam NAPRAWDĘ był i NAPRAWDĘ
  odjechał. Nowa kolumna zerwałaby bramkę `godot-first-run.yml`, która porównuje plik
  `--calls` rdzenia z plikiem sceny co do bajtu.

## 12. Co zauważyłem po drodze, a nie tknąłem

- **Okno zatrzymania w `LineDrive` jest JEDNOSTRONNE** (`chainage >= target -
  StopWindowM`), podczas gdy `StationService` ma je dwustronne
  (`WindowIsTwoSidedUnlikeTheAutopilot`). Dla autopilota nieszkodliwe — nigdy nie
  przestrzeliwuje — dla gracza znaczy, że można „obsłużyć" peron stojąc pięćdziesiąt
  metrów za nim. Poza zakresem tej pozycji; do kolejki.
- Wiersz pomocy pod autopilotem wymienia dziś **dziewięć** klawiszy i zaczyna być
  długi. `HelpSeparator` zakłada, że da się go przeczytać wzrokiem z fotela; przy
  dwunastu przypisaniach to założenie przestanie być prawdziwe.
