# 6.D289 · Ten sam skan poza rdzeniem — i jeden typ, którego skan zobaczyć NIE MOŻE

**Data:** 19.09.2026 · **Gałąź:** `claude/sharp-ramanujan-jdr51o` · **Baza:** `05daa4e`

6.D234 postawiło bramkę czytającą deklaracje **wyłącznie** z `src/Sim/` — warunek
`plik.startswith("src/Sim/")` stał wpisany w ciało `typy_publiczne`. Ta pozycja pyta,
co ten sam skan pokazuje na `src/Game/` i `src/Sim.Runner/`, i czy zasięg bramki ma
się rozszerzyć.

---

## 1. Sześć liczb, i trzy z rdzenia jako kontrola przyrządu

| katalog | plików `.cs` | typów publicznych | wołane z `src/` | wołane wyłącznie z `tests/` | nienazwane nigdzie |
|---|---|---|---|---|---|
| `src/Sim/` | 59 | **109** | 84 | **12** | **13** |
| `src/Game/` | 26 | **42** | 31 | **1** | **10** |
| `src/Sim.Runner/` | 2 | **5** | 2 | **2** | **1** |

**Kontrola przyrządu zdana co do cyfry:** wiersz `src/Sim/` daje **109 / 12 / 13**,
czyli liczby 6.D234 — a daje je **ten sam czytnik po parametryzacji**, nie kopia.

Czytnik pożyczony, nie napisany drugi raz: `typy_publiczne` i `rozklad_wolajacych`
dostały parametr `przedrostek` z domyślną wartością `RDZEN = "src/Sim/"`. Zawężenie
przestało być napisem w ciele, a stało się wartością domyślną. Powód jest zmierzony
dwa razy wcześniej — 6.D281 na czytniku biorącym korpus ze stałej modułowej i 6.D285
na czytniku przyjmującym ścieżkę argumentem: zawężenie w ciele znaczy, że pytanie
„co ten sam skan pokazuje gdzie indziej" wymaga DRUGIEJ KOPII, a druga kopia
rozjeżdża się z pierwszą.

Parametr zawęża **tylko stronę deklarującą**. Strona wołająca zostaje całym `src/`
i `tests/`, bo pytanie brzmi „czy ktokolwiek woła", a nie „czy woła sąsiad z katalogu".

## 2. Listy imienne

**`src/Game/`, wołane wyłącznie z `tests/`** — jeden: `ChaseFraming`
(`record struct`, `src/Game/World/ChaseCameraAim.cs`; nazwany w `tests/Game.Tests/ChaseCameraAimTests.cs`).

**`src/Game/`, nienazwane nigdzie poza własnym plikiem** — dziesięć:

| nazwa | rodzaj | plik | wystąpień we WŁASNYM pliku |
|---|---|---|---|
| `ChaseAvailability` | `record struct` | `src/Game/World/ChaseCameraAim.cs` | 3 |
| `ChunkLod` | `record struct` | `src/Game/Assets/ChunkManifest.cs` | 5 |
| `DriverBinding` | `record` | `src/Game/Input/DriverActions.cs` | 14 |
| **`FirstRun`** | `class` | `src/Game/FirstRun.cs` | **1** |
| `RunStart` | `record struct` | `src/Game/RunReset.cs` | 4 |
| `StreamWindow` | `record struct` | `src/Game/Assets/StreamingPlan.cs` | 5 |
| `StreamingDelta` | `record struct` | `src/Game/Assets/StreamingPlan.cs` | 3 |
| `TelemetrySample` | `record struct` | `src/Game/TelemetryTrack.cs` | 6 |
| `TrackFrame` | `record struct` | `src/Game/World/SceneAxis.cs` | 3 |
| `ViewAssumption` | `record struct` | `src/Game/DesignAssumptions.cs` | 22 |

**`src/Sim.Runner/`, wołane wyłącznie z `tests/`** — dwa: `LineBudgetRun`, `Program`.
**`src/Sim.Runner/`, nienazwane nigdzie** — jeden: `LineBudgetCensus`
(`class`, `src/Sim.Runner/LineBudget.cs`, 7 wystąpień we własnym pliku).

**Rodzaje w klasie „nienazwane":** `src/Sim/` — jedenaście `record struct` i dwie
`class`; `src/Game/` — osiem `record struct`, jeden `record`, jedna `class`;
`src/Sim.Runner/` — jedna `class`. Rozkład jest ten sam, co w rdzeniu, i to jest
pierwsza połowa odpowiedzi: zjawisko poza rdzeniem ma **w przeważającej części tę
samą przyczynę**, którą moduł nazywa od 6.D234 — wołający piszą `var`, więc nazwa
nie pada, a typ jest używany.

## 3. Znalezisko: skan nazywa „nienazwanym" PUNKT WEJŚCIA GRY

Dziewięć z dziesięciu typów `src/Game/` z klasy „nienazwane" żyje we własnym pliku,
od trzech do dwudziestu dwóch wystąpień. Dziesiąty ma **jedno**, czyli samą
deklarację, i jest nim `FirstRun`. Powód, dla którego nie ma ani jednego więcej,
leży poza zasięgiem skanu:

```
src/Game/project.godot:14        run/main_scene="res://Scenes/FirstRun.tscn"
src/Game/Scenes/FirstRun.tscn:8  [ext_resource type="Script" path="res://FirstRun.cs" id="1_root"]
src/Game/Scenes/FirstRun.tscn:22 [node name="FirstRun" type="Node3D"]
```

`FirstRun` jest **sceną główną gry**. Wiązanie robi silnik, w plikach, których skan
po `.cs` nigdy nie otwiera.

**Ślepota siedzi w KORZENIU sceny, a nie w całym katalogu — i to zmierzyłem osobno,
bo zdanie „skan nie widzi wiązań silnika" brzmi jak zdanie o `src/Game/`, a jest
zdaniem o jednym węźle.** Scena wiąże sześć skryptów; pięć pozostałych
(`TunnelView`, `TrainView`, `StationView`, `CabView`, `Hud`) wymienia z nazwy
**`FirstRun.cs`**, więc skan widzi dla nich wołającego. Niewidoczny jest dokładnie
ten jeden, którego jedynym wołającym jest silnik.

Ta sama rodzina w `src/Sim.Runner/`: **`Program` wychodzi jako „wołany wyłącznie
z testów"**, bo wołającym jest środowisko uruchomieniowe .NET, a nie żaden `.cs`.

`DriverBinding` jest przypadkiem trzecim i też nie jest długiem: konstruowany
czternaście razy we własnym pliku, a czyta go **bramka Pythona** —
`tools/tests/test_player_package.py:98` cięciem po napisie `new DriverBinding(`.

## 4. Rozstrzygnięcie o zasięgu: ZOSTAJE PRZY RDZENIU

Rozszerzenie jest dziś tanie i byłoby błędem. Zbiór przypięty dla tych katalogów
musiałby nieść **dwa punkty wejścia dwóch programów** — `FirstRun` jako „nienazwany
nigdzie" i `Program` jako „wołany wyłącznie z testów". Bramka orzekałaby wtedy o `.cs`
coś, co czyta się jako zdanie o programie, a to jest usterka, którą ten projekt tropi
od 6.D27.

**Różnica wobec rdzenia jest mierzalna, nie stylistyczna, i mieści się w jednej
liczbie.** W `src/Sim/` wszystkie trzynaście wpisów dzieli **jeden** mechanizm,
nazwany w module i sprawdzalny przez każdego czytelnika. W `src/Game/` ten sam
mechanizm pokrywa **dziewięć z dziesięciu**, a dziesiąty wymaga powodu **innej
klasy** — wiązania w pliku, którego przyrząd nie otwiera i sprawdzić nie umie.
Zbiór przypięty, którego część wpisów ma powód niesprawdzalny dla bramki, jest
słabszy od zbioru, w którym jeden powód pokrywa całość.

**Warunek zmiany, zapisany po to, żeby werdykt dał się obalić:** zasięg rozszerza
się wtedy i tylko wtedy, gdy czytnik nauczy się czytać wiązania silnika
(`*.tscn`, `project.godot`) oraz konwencję punktu wejścia — czyli gdy powód każdego
wpisu stanie się sprawdzalny tak samo jak w rdzeniu. Sam wzrost liczby typów w tych
katalogach takim powodem **nie jest**. Zapisane jako pozycja kolejki, żeby warunek
nie był życzeniem w raporcie.

## 5. Dlaczego werdykt dostaje ASERCJĘ, a nie akapit

Rozstrzygnięcie z §4 stoi na jednym zdaniu o drzewie. Zdanie w prozie, którego nikt
nie sprawdza, starzeje się po cichu — zmierzyła to pozycja domknięta godzinę
wcześniej tego samego dnia, gdzie takie zdanie przestało być prawdziwe **cztery
godziny i czterdzieści siedem minut** po zapisaniu i wróciło po dziesięciu dniach
jako nowa pozycja kolejki, bo korektę zastosowano do jednego z dwóch nosicieli.
Zostawienie tu werdyktu bez opieki byłoby powtórzeniem tamtej usterki o jedną
pozycję dalej.

Dwie bramki, obie o PRZESŁANCE, nie o objawie:

* `test_skan_po_nazwie_NIE_WIDZI_wiazania_silnika_i_to_jest_powod_zasiegu` — trzy
  fakty: `FirstRun` jest typem publicznym `src/Game/`, wychodzi skanowi jako
  „nienazwany nigdzie", a `project.godot` i `FirstRun.tscn` mówią, dlaczego.
* `test_slepota_siedzi_w_KORZENIU_sceny_a_nie_w_calym_katalogu` — kontrola do tamtej:
  skryptów sceny niewidocznych dla skanu ma być dokładnie jeden, ten w korzeniu.

**To nie jest rozszerzenie censusu na `src/Game/`:** nie ma tu podłogi liczby typów
tego katalogu ani przypiętego zbioru jego nazw. Jest sprawdzenie zdania, z którego
wynika decyzja, żeby censusu nie rozszerzać.

## 6. Kontrole negatywne — na KOMPLETNEJ kopii drzewa z `.git`, baza 10/10

| KN | mutacja | przewidziane | wynik |
|---|---|---|---|
| KN-1 | klasa `FirstRun` przemianowana | 8/10 | **8/10**, obie bramki, komunikaty jak przewidziano |
| KN-2 | `typeof(FirstRun)` dopisane w `RunReset.cs` | 8/10 | **8/10**, `FirstRun` wychodzi z `niewolane` |
| KN-3 | `run/main_scene` wskazuje inną scenę | 9/10 | **9/10**, tylko pierwsza bramka |
| KN-4 | `TunnelView` zdjęty z `FirstRun.cs` i z `UiTextTests.cs` | 9/10 | **9/10**, `slepe` daje `['FirstRun', 'TunnelView']` |
| KN-5 | parametryzacja cofnięta (`src/Sim/` z powrotem w ciele) | 8/10 | **8/10**, obie bramki mierzą wtedy rdzeń |
| KN-5b | ta sama mutacja **bez** dwóch nowych bramek | — | **8/8, ZIELONE** |

**Wszystkie pięć zgodne z przewidywaniem spisanym przed przebiegami**, łącznie z KN-4,
który zaznaczyłem jako najmniej pewny („nie wiem, czy `TunnelView` wpadnie do
`niewolane`, czy do `tylko_testy`").

**Para KN-5 / KN-5b jest dowodem, że parametryzacja niesie treść, a nie wygodę:**
ta sama mutacja daje czerwień z nowymi bramkami i **zieleń** bez nich.

## 7. Usterka przyrządu kontroli, złapana i nazwana

Pierwsza wersja pętli kontrolnej przywracała drzewo przez `git checkout -- .`.
Kopia ma `.git` na scalonym `main`, a zmiany modułu były w tej rundzie **jeszcze
niezacommitowane** — więc przywracanie **kasowało obie nowe bramki**. Objaw jest
cichy i wygląda na sukces: przebieg wypisał `8/8 przeszło`, czyli liczbę mniejszą
o dwa testy, których już nie było. Gdybym czytał samą liczbę czerwonych, a nie
mianownik, uznałbym KN-2 za wykonane na module, który go nie zawierał.

Poprawka: przywracanie **kopią z osobnego drzewa pristine**, nie przez gita.
`rsync` w tym kontenerze nie istnieje, więc `cp -a` po uprzednim `rm -rf`.

## 8. Przewidywania spisane PRZED pomiarem

| # | przewidywanie | wynik |
|---|---|---|
| 2 | `src/Game/` typów publicznych 20–40 | **PUDŁO**, jest 42 — tuż poza przedziałem |
| 3 | `src/Game/` tylko testy 0–2 | trafione (1) |
| 4 | `src/Game/` nienazwanych 10–25 | liczba trafiona (10), **MECHANIZM NIETRAFIONY** |
| 5 | `src/Sim.Runner/` typów 5–20 | trafione (5), przy dolnym krańcu |
| 6 | `src/Sim.Runner/` tylko testy 0–3 | trafione (2) |
| 7 | `src/Sim.Runner/` nienazwanych 2–8 | **PUDŁO**, jest 1 |
| 8 | werdykt „zostaje przy rdzeniu" dla `src/Game/` | trafione — ale z innego powodu |

**Przewidywanie 4 jest najciekawszym pudłem tej pozycji, bo liczba się zgodziła.**
Napisałem, że dziesiątka weźmie się z węzłów Godota podpiętych w `.tscn`, których
skan po nazwie nie widzi. Tak jest dla **jednego** z dziesięciu. Pozostałe dziewięć
to ta sama rodzina `record struct` konsumowanych przez `var`, którą 6.D234 opisało
w rdzeniu. Liczba trafiona przy mechanizmie chybionym jest gorsza od pudła
w liczbie: wyglądałaby na potwierdzenie tezy, gdybym nie wypisał rodzajów
i wystąpień we własnym pliku.

Przewidywanie 8 trafiło co do werdyktu, a nie co do powodu: spodziewałem się, że
odrzucę rozszerzenie, bo zbiór byłby w większości fałszywymi trafieniami. Mierzone
jest coś innego — fałszywymi trafieniami są tam **wszystkie**, tak samo jak
w rdzeniu, a różnicę robi **sprawdzalność powodu**.

## 9. Czego świadomie nie zrobiono

- **Nie usunięto i nie podłączono ani jednego typu** (pole „Poza zakresem").
- **Nie zmieniono wzorca `TYP` ani maski literałów** — rozbiór deklaracji nietknięty.
- **Nie rozszerzono censusu** na żaden z dwóch katalogów: nie ma podłogi liczby typów
  ani przypiętego zbioru dla `src/Game/` i `src/Sim.Runner/`.
- **Nie dotknięto `data/`.**
- **Nie rozstrzygnięto, czy `Program` i `FirstRun` mają dostać wpisy z powodem** —
  to byłoby rozszerzenie zasięgu, czyli dokładnie to, co §4 odrzuca.
- **Nie dopisano usprawiedliwienia do dwóch nowych asercji napisowych.** Stoją na
  NAPISIE i nie mają wymówki, którą mają wpisy wyżej w łańcuchu
  `ASERCJI_NAPISOWYCH_RAZEM`: tamte literały są wynikiem rozbioru, a te dwa są
  wierszami konfiguracji przepisanymi z plików. Tak ma być — przedmiotem asercji
  jest to, co te dwa pliki mówią.

## 10. Zauważone przy okazji, nietknięte

`tools/tests/test_player_package.py:98` czyta źródło C# **cięciem po napisie**
`new DriverBinding(`. Jest to czwarta droga, którą typ bywa „używany" bez padania
z nazwy w `.cs` — obok `var`, wiązania silnika i punktu wejścia. Skan po nazwie jej
nie widzi i ta pozycja o nią nie pyta.
