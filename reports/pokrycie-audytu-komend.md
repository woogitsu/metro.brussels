# Pokrycie audytu komend z pól „Weryfikacja" — 233 komendy z 111 bloków (6.D33)

**Zmierzone 07.09.2026 na commicie:** `f684e40a3af52272f9cd1d32d241e9bf3abf644d`

Pozycja 6.D15 zebrała komendy z pól „Weryfikacja" i wydała im werdykty. Nie zostawiła
jednak liczby, ilu bloków tamten pomiar dotyczył **w treści raportu** — a bloków
przybywa. Ta pozycja mierzy, ile z tamtego pokrycia zostało, i rozstrzyga, czy da się
je przybić bramką. **Rozstrzygnięcie: nie da się, i bramki tu nie ma.** Powód jest
liczbą, nie zniechęceniem, i stoi w §7.

Pole „Wyjście" bloku 6.D33 żąda **najpierw liczby**. Kolejność sekcji jest z tego
powodu taka: co i jak zmierzono (§1), liczby (§2), rozbicie na cztery kategorie (§3),
wymienienie z nazwy tego, co nie jest uruchamialne (§4–§6), i dopiero potem kierunek
(§7).

## 1. Co jest jednostką pomiaru i czym mierzono

Kolektor jest cudzy i nietknięty: `tools/tests/backlog_commands.py` (6.D15). Czyta
bloki `##### <numer> ·` czytnikiem z `tools/tests/test_backlog.py`, wycina pole
„Weryfikacja" tą samą regułą cięcia i skleja wiersze płotka w komendy — kontynuacja `\`,
pętla `for … do … done` jako JEDNO polecenie, wiersz komentarza pominięty.

Jednostki są **dwie** i mieszanie ich jest tu głównym źródłem nieporozumienia:

- **wiersz komendy** — niepusty, niekomentarzowy wiersz wewnątrz płotka pola
  „Weryfikacja". W tej jednostce podana jest liczba **279** w bloku 6.D33;
- **komenda sklejona** — to, co da się wpisać do terminala jako jedno polecenie.

Przeliczenie jednej na drugą jest zmierzone, nie założone: 297 wierszy sklejają się
w 233 komendy, bo **64 wiersze** wchłaniają kontynuacje `\` i pętle. Rozbicie
w §3 podaje obie liczby, żeby dało się je porównać z 279 bez zgadywania.

**Dwie pułapki przyrządu, obie ominięte świadomie.** Pierwsza: bloki kodu w polach
„Weryfikacja" są **wcięte** pod punktorem, więc wzorzec ogrodzenia zakotwiczony na
początku wiersza daje **zero komend ze 111 bloków** — zielone zero wyglądające na
czysty wynik. Kolektor 6.D15 tej kotwicy nie ma i dlatego jest tu użyty w całości.
Druga: wzmianka o narzędziu w prozie nie jest jego wywołaniem. Zmierzone na tym
drzewie: napis `mutation_sweep.py` występuje w `docs/TASKS.md` **117** razy, a wywołań
w polach „Weryfikacja" jest **37** — naiwny grep pokazałby tu liczbę trzykrotnie
zawyżoną. Licznik chodzi więc po polach i po płotkach, nigdy po całym pliku. To ta sama
pułapka, którą 6.A31 nazwało dla ścieżek `bin/`: wiersz cytowanego wyjścia i zdanie
z nazwą pliku wyglądają w grepie identycznie jak polecenie.

## 2. Liczby

| co | 06.09.2026 (6.D15) | 07.09.2026 (`a4a3975`, blok 6.D33) | 07.09.2026 (ten pomiar) |
|---|---|---|---|
| bloków szczegółów | — | 101 | **111** |
| bloków z polem „Weryfikacja" | **42** | 101 | **111** |
| wierszy komend | — | **279** | **297** |
| komend sklejonych | **83** (werdyktów 82) | — | **233** |
| napisów unikalnych | — | — | **103** |

Obie liczby z bloku 6.D33 przeliczone samodzielnie na świeżym `origin/main` i obie się
potwierdzają w swoich jednostkach: 101 bloków i 279 wierszy stoi na `a4a3975`
(odtworzone w osobnym worktree), a dziś jest 111 bloków i 297 wierszy. Różnica
279 → 297 to dziesięć nowych bloków, nie zmiana metody.

**Pomiar zaczął się na `2ffb0b0` i został powtórzony na `f684e40`**, bo w trakcie
weszły cztery scalenia, w tym #388 (6.D32) i #391. Trzy liczby wyżej są na obu commitach
**identyczne** (111 / 297 / 233), a z 233 napisów komend zmienił się **jeden**: 6.D32
poprawiło w bloku 6.A30 ścieżkę zapisu wejść. Skutek tej poprawki jest w §4 i nie jest
taki, jak można się spodziewać.

**Pokrycie audytu 6.D15, w każdej jednostce osobno:** 42 z 111 bloków (**38 %**),
82 z 233 komend (**35 %**), 82 z 297 wierszy (**28 %**). Liczba 29 % z bloku 6.D33
jest z tej ostatniej jednostki i po dziesięciu nowych blokach zeszła do 28 %.

## 3. Rozbicie na cztery kategorie

Kryterium jest jedno i to samo dla każdej pozycji: **komendę wpisano dosłownie
i sprawdzono, czym się kończy.** Nie „czy wygląda sensownie".

- **uruchamialna** — da się wpisać dosłownie i kończy się werdyktem narzędzia. Kod
  wyjścia różny od zera **nie** dyskwalifikuje: pola bloków 6.A11, 6.A14, 6.A15,
  6.A16, 6.A22, 6.A23, 6.A25, 6.B39 obiecują wprost **odmowę**, i odmowa jest ich
  werdyktem;
- **wymaga narzędzia nieobecnego** — Blender albo Godot, wprost albo przez `bpy`;
- **niewykonalna z winy zapisu** — zła ścieżka, brakujący argument, miejsce do
  wypełnienia;
- **nierozstrzygnięta** — nie doszła do werdyktu w budżecie tej sesji albo nie jest
  komendą, choć kolektor liczy ją jako komendę.

| kategoria | komend | wierszy | napisów unikalnych |
|---|---|---|---|
| **uruchamialna** | **207** | 260 | 79 |
| **wymaga narzędzia nieobecnego** | **10** | 13 | 10 |
| **niewykonalna z winy zapisu** | **9** | 14 | 7 |
| **nierozstrzygnięta** | **7** | 10 | 7 |
| RAZEM | **233** | **297** | 103 |

Środowisko pomiaru: brak Blendera, brak Godota (`doctor.sh` wypisuje dla obu `WARN`,
kod wyjścia 0), `dotnet` 10.0.400 obecny — więc **`dotnet` nie jest tu narzędziem
nieobecnym** i 30 wywołań `dotnet test tests/Sim.Tests` oraz 5 wywołań
`dotnet test tests/Game.Tests` liczy się do kategorii pierwszej z wykonanego
przebiegu, nie z założenia.

**Jedna rzecz odsiana świadomie i zmierzona osobno, bo inaczej zafałszowałaby
kategorię trzecią.** Katalog `build/` nie jest komitowany (`CLAUDE.md` §4.8), więc
w świeżym worktree go nie ma, a `Sim.Runner` sam go nie tworzy: trzynaście komend
kończyło się wtedy `BŁĄD: Could not find a part of the path …`. To nie jest usterka
zapisu pola — to zachowanie runnera. Po jednym `mkdir -p build build/trace` te same
komendy, puszczone **w kolejności płotka** (bloki 6.A17, 6.A20, 6.A24, 6.A27, 6.D1),
kończą się kodem 0. Dlatego stoją w kategorii pierwszej, a nie trzeciej.

**Kategoria pierwsza nie zawiera ani jednej komendy zaliczonej „bo pewnie działa".**
Najdroższe wywołania — przeglądy mutacyjne — są doprowadzone do werdyktu, każde
z osobnym przebiegiem i zmierzonym czasem ściennym (`date +%s.%N`, bo `/usr/bin/time`
w tym środowisku nie istnieje):

```
 3131.6 s  kod 0  6.D5   --only assert_shot_metadata.py --workers 2   (110 mutacji)
  906.2 s  kod 0  6.D5   --only crs.py --workers 2                    ( 29 mutacji)
  726.2 s  kod 0  6.B16  --only tools/track/detail_layout.py -w 4     ( 33 mutacji)
  617.6 s  kod 0  6.B14  --only tools/blender/station_sections.py -w4 ( 15 mutacji)
  448.9 s  kod 0  6.B8   --only make_test_track.py --workers 2        ( 13 mutacji)
  370.4 s  kod 0  6.B6   --only sweep.py --workers 4                  (117 mutacji)
  234.6 s  kod 0  6.B14  --only tools/blender/material_specs.py -w 4  ( 10 mutacji)
  222.3 s  kod 0  6.D26  for i in 1 2 3; do test_all.py | grep RAZEM  (trzy przebiegi)
  203.0 s  kod 0  6.B14  --only tools/blender/marker_gates.py -w 4    (  9 mutacji)
  114.1 s  kod 0  6.B35  --only tools/blender/lod_paths.py --workers 2 (  2 mutacje)
  107.2 s  kod 0  6.D17  bash doctor.sh
```

Rozstęp jest tu istotny dla §6: **3,2 s na mutację** przy 117 mutacjach `sweep.py`
i **41 s na mutację** przy 15 mutacjach `station_sections.py`, bo koszt jednej
mutacji zależy od tego, ile modułów zestawu obejmuje jej pokrycie. Dlatego dwóch
przeglądów CAŁEGO drzewa (2035 mutacji) nie da się z tego wiarygodnie przeliczyć na
jedną liczbę i stoją w kategorii czwartej z widełkami, a nie z wynikiem.

## 4. Niewykonalne z winy zapisu — imiennie

**Ani jednej z nich ta pozycja nie poprawia.** Pole „Poza zakresem" bloku 6.D33 mówi
to wprost: pozycja je **liczy i nazywa**, a poprawka każdej należy do jej własnego
bloku. Ścieżki, których w drzewie nie ma, stoją niżej **bez grawisów** i to nie jest
niedbałość: `tools/tests/test_report_hygiene.py` żąda, żeby każda ścieżka w grawisach
rozwiązywała się w drzewie, a jej lista wyjątków jest pusta i ma taka zostać.
Kontrola tego wyboru WYKONANA: po założeniu grawisów na jedną z tych ścieżek w tym
właśnie raporcie bramka pada, a po ich zdjęciu wraca na zielono —

```
FAIL test_kazda_sciezka_wymieniona_w_raporcie_rozwiazuje_sie_w_drzewie: ścieżki,
których nie ma w drzewie: ['pokrycie-audytu-komend.md:196: data/keys/L1_A-manual.json']
  10/11 przeszło
  ... po zdjęciu grawisów: 11/11 przeszło
```

— więc zapis bez grawisów jest tu wymogiem bramki, nie stylistyką. Wyjście powyżej
jest przytoczone **ze zdjętymi grawisami wokół ścieżki**, i to też nie jest kosmetyka:
pierwsza wersja tego akapitu cytowała komunikat dosłownie i bramka zapaliła się po raz
drugi — na własnym komunikacie o błędzie, przytoczonym w raporcie o tym błędzie.
Grawisy w płotku bramka widzi tak samo jak w prozie, bo skan idzie po wierszach.
To samo zdarzyło się 07.09.2026 przy `reports/kolejka-uzupelnienie-drugie.md`.

| blok | komenda | zmierzone |
|---|---|---|
| 6.A21 | git diff --stat tools/ci/golden/ | zła ścieżka — katalogu tools/ci/golden nie ma w drzewie; wzorce śladu leżą w `tests/data/golden-trace`, kod 128 |
| 6.A30 | dotnet run --project src/Sim.Runner -c Release -- replay --keys tests/data/manual-keys.log 2>/dev/null | brakujący argument — `BŁĄD: replay wymaga --signalling PLIK.json`, kod 1; ścieżkę poprawiło 6.D32 (#388), brak opcji został |
| 6.B18 | python3 tools/tests/mutation_sweep.py --only tools/visual/compare.py --operators operator,prog --workers 1 --journal <własny dziennik> | miejsce do wypełnienia — nawiasu ostrokątnego nie da się wpisać, powłoka kończy kodem 2 |
| 6.B32 (×2) | python3 tools/tests/mutation_sweep.py --only tools/blender/lod_paths.py --journal /tmp/b32/dziennik.jsonl | zła ścieżka — katalogu `/tmp/b32` nie ma, narzędzie go nie tworzy; po 118 s pracy `FileNotFoundError`, kod 1 |
| 6.B41 (×2) | python3 tools/tests/mutation_sweep.py --only tools/blender/lod_paths.py --journal /tmp/b41/d.jsonl --workers 2 --no-coverage | zła ścieżka — katalogu `/tmp/b41` nie ma, narzędzie go nie tworzy; po 121 s pracy `FileNotFoundError`, kod 1 |
| 6.C4 | python3 tools/ci/assert_shot_metadata.py build/inspect.png | brakujące argumenty — program żąda `--metadata` i `--axis`, a członu pozycyjnego nie bierze wcale, kod 2 |
| 6.D9 | python3 tools/ci/png_pixels_sha256.py <dwa PNG z dwóch przebiegów tej samej sceny> | miejsce do wypełnienia — nawiasu ostrokątnego nie da się wpisać, powłoka kończy kodem 2 |

Siedem napisów dzieli się tak: **cztery są nowe** (nie ma ich ani w audycie 6.D15,
ani w pomiarze 6.D32), **jeden zmienił powód w trakcie tej sesji**, a **dwa** to
miejsca do wypełnienia, które 6.D15 wymieniło z nazwy i przybiło bramką (§7.3).
Cztery nowe składają się na trzy znaleziska:

1. **6.A21 — katalog wzorców, którego nie ma.** Blok cytuje tools/ci/golden zarówno
   w polu „Wejście", jak i w komendzie. `tools/ci/assert_line_trace.py` ma
   `--golden` z domyślną wartością `tests/data/golden-trace`, i tam te wzorce leżą
   (sześć osi plus manifest). Komenda kończy się kodem **128**:
   `fatal: ambiguous argument 'tools/ci/golden/': unknown revision or path not in the
   working tree`. Pomiar 6.D32 tej ścieżki nie widzi, i to jest zdanie o jego wzorcu,
   nie o jego staranności: wzorzec bierze tokeny ze **znanym rozszerzeniem**, a to jest
   katalog. Rozstrzygnięcie należy do 6.D32, bo to jego pole.
2. **6.B32 i 6.B41 — katalog dziennika, którego nikt nie tworzy.** Oba bloki podają
   `--journal` w katalogu pod `/tmp`, którego w czystej powłoce nie ma.
   `mutation_sweep.py` nie tworzy katalogu i nie odmawia na wejściu: liczy **118 s**
   (6.B32) i **121 s** (6.B41), a potem wywala `FileNotFoundError` z pełnego
   tracebacku, w robotniku. Po jednym `mkdir -p` obie kończą się kodem 0
   (`rozstrzygniętych 2/2, zabitych 2`) w ok. 126 s — czyli **jedyną usterką jest
   ścieżka**, a nazwa opcji `--no-coverage`, którą można było podejrzewać, istnieje
   i działa. Zmierzone osobno w obie strony, żeby nie zlać dwóch powodów w jeden.
3. **6.C4 — brak dwóch wymaganych opcji.** `tools/ci/assert_shot_metadata.py` żąda
   `--metadata` i `--axis`, a członu pozycyjnego nie przyjmuje wcale, więc komenda
   z pola jest odrzucana przez `argparse` **niezależnie** od tego, czy PNG istnieje.
   Audyt 6.D15 wpisał ją do kategorii „wymaga narzędzia, którego tu nie ma" z powodem
   „nie ma czego czytać, dopóki poprzednia nie da PNG" — i to jest prawda, tylko nie
   cała. Tamtego werdyktu **nie przeliczam**: to pomiar z datą. Podaję własny, o innym
   kryterium, i mówię, czym się różni.

**Czwarty napis, 6.A30, jest najciekawszy z całej tej siódemki, bo pokazuje, że
poprawka ścieżki nie musi być poprawką komendy.** Pomiar zaczął się, gdy blok cytował
data/keys/L1_A-manual.json — katalog, którego nie ma wcale, i jedną z dwóch usterek
pomiaru 6.D32. W trakcie tej sesji 6.D32 weszło do `main` (#388) i tę ścieżkę
poprawiło na `tests/data/manual-keys.log`, który istnieje. Komenda z pola **nadal się
nie wpisuje**, tylko z innego powodu:

```
$ dotnet run --project src/Sim.Runner -c Release -- replay --keys tests/data/manual-keys.log
BŁĄD: replay wymaga --signalling PLIK.json: prędkość dopuszczalną tryb ręczny bierze
z planu sygnalizacji, a scenariusz podaje 80 km/h — prędkość konstrukcyjną M7, nie
ograniczenie na torze
kod wyjścia: 1
```

Usterka przeszła z rodziny „zła ścieżka" do rodziny „brakujący argument", i **żadna
bramka na ścieżki jej nie zobaczy** — plik z pola istnieje. To jest zdanie o granicy
bramki 6.D32, nie o jej wykonaniu. Blok 6.A30 jest ZROBIONY, więc jego pole jest
zapisem historycznym i poprawka nadal należy do niego, nie tutaj.

Pozostałe dwa napisy (6.B18, 6.D9) to miejsca do wypełnienia, które audyt 6.D15
wymienił z nazwy i **przybił bramką** — o tym w §7.3.

## 5. Wymaga narzędzia nieobecnego — imiennie

| blok | komenda | zmierzone |
|---|---|---|
| 6.B13 | python3 tools/tests/mutation_sweep.py --only tools/blender/profile_vehicle.py --workers 4 | 47 mutacji nieosiągalnych — `ModuleNotFoundError: No module named 'bpy'`, kod 1 |
| 6.B13 | python3 tools/tests/mutation_sweep.py --only tools/blender/tunnel_sweep.py --workers 4 | 68 mutacji nieosiągalnych — brak modułu `bpy`, kod 1 |
| 6.B43 | $GODOT_BIN --path src/Game -- --shot --view=chase --at-m=96 --out=build/chase-96.png | zmienna `GODOT_BIN` pusta, Godota nie ma w `PATH` — kod 127 |
| 6.B9 | bash tools/ci/blender_smoke.sh          # ta sama geometria, suma SHA-256 przed i po | skrypt sam odmawia: `BŁĄD: wymagane polecenie 'blender' nie jest dostępne w PATH`, kod 127 |
| 6.C3 | "$GODOT_BIN" --headless --path src/Game -- --no-geometry --line --limit-kmh=72 --telemetry=build/ref.csv | zmienna `GODOT_BIN` pusta — kod 127 |
| 6.C3 | "$GODOT_BIN" --headless --path src/Game -- --no-geometry --from-telemetry=build/ref.csv --telemetry=build/echo.csv | zmienna `GODOT_BIN` pusta — kod 127 |
| 6.C3 | dotnet run --project src/Sim.Runner -- compare build/ref.csv build/echo.csv --tolerance 0 | porównuje dwa pliki, które produkują poprzednie dwa wywołania Godota — kod 1, brak wejścia |
| 6.C4 | "$GODOT_BIN" --headless --path src/Game -- --shot=build/inspect.png --view=inspect --at-chainage=2521.1 | zmienna `GODOT_BIN` pusta — kod 127 |
| 6.C4 | "$GODOT_BIN" --headless --path src/Game -- --view=zmyslony | zmienna `GODOT_BIN` pusta — kod 127 |
| 6.D9 | "$BLENDER_BIN" --background --python tools/visual/capture_blender.py -- --help | zmienna `BLENDER_BIN` pusta, Blendera nie ma w `PATH` — kod 127 |

Dwie rzeczy w tej tabeli warto powiedzieć wprost, bo nie widać ich z komendy.
Pierwsza: dwa wywołania z bloku 6.B13 nie wołają Blendera — wołają
`tools/tests/mutation_sweep.py` na plikach, których zestaw testów nie potrafi
**zaimportować** bez `bpy`. Narzędzie mówi to samo z siebie i kończy kodem 1
(`brak mutacji do sprawdzenia po odfiltrowaniu nieosiągalnych: filtr odsiał
wszystkie 47`), więc klasyfikacja jest z pomiaru, nie z nazwy katalogu: sweep na
`tools/blender/lod_paths.py`, `station_sections.py`, `marker_gates.py`
i `material_specs.py` przechodzi na zielono, bo te moduły wyszły spod `bpy`.
Druga: `dotnet run … compare build/ref.csv build/echo.csv --tolerance 0` z bloku 6.C3
jest wywołaniem runnera, ale porównuje dwa pliki, które produkują **dwa poprzedzające
je przebiegi Godota**. Puszczona w kolejności płotka kończy się kodem 1 na braku
wejścia. To ta sama zależność, którą 6.D15 nazwało dla 6.C4.

## 6. Nierozstrzygnięte — imiennie, z powodem

| blok | komenda | zmierzone |
|---|---|---|
| 6.A24 | rows = open("build/d1.csv").read().splitlines() | wiersz ciała heredoku — kolektor liczy go jako komendę, a komendą nie jest |
| 6.A24 | rows[3] = ",".join(["abc"] + rows[3].split(",")[1:]) | wiersz ciała heredoku — jw. |
| 6.A24 | open("build/d2.csv", "w").write("\n".join(rows) + "\n") | wiersz ciała heredoku — jw. |
| 6.A24 | EOF | znacznik końca heredoku — kolektor liczy go jako komendę |
| 6.B44 | python3 tools/track/vertical_profile.py --axis data/track/L1_A.json --depths data/network/station-depths.csv --out build/L1_A-vertical.json | narzędzie, które pozycja 6.B44 ma dopiero wytworzyć — dziś go w drzewie nie ma, kod 2 |
| 6.B9 | python3 tools/tests/mutation_sweep.py --workers 4 --journal build/bpy-po.jsonl --json build/bpy-po.json | **2035** mutacji całego drzewa; zmierzona przepustowość tego narzędzia na tym drzewie waha się od 3,2 s do 41 s na mutację, czyli werdykt od ok. 1,8 h do ok. 23 h — poza budżetem tej sesji |
| 6.D6 | python3 tools/tests/mutation_sweep.py --workers 4 --journal build/ops-po.jsonl --json build/ops-po.json --out build/ops-po.md | **2035** mutacji całego drzewa, jw. — poza budżetem tej sesji |

Cztery z tych pozycji to **usterka kolektora, nie pola**, i jest to znalezisko tego
pomiaru. Blok 6.A24 ma w płotku heredok:

```
dotnet run --project src/Sim.Runner -c Release -- drive --out build/d1.csv
python3 - <<'EOF'
rows = open("build/d1.csv").read().splitlines()
rows[3] = ",".join(["abc"] + rows[3].split(",")[1:])
open("build/d2.csv", "w").write("\n".join(rows) + "\n")
EOF
dotnet run --project src/Sim.Runner -c Release -- compare build/d1.csv build/d2.csv
dotnet test tests/Sim.Tests
```

Kolektor nie zna heredoku, więc rozbija **jedną** komendę na **pięć**: otwarcie,
trzy wiersze ciała i `EOF`. Puszczone osobno dają `/bin/sh: 1: Syntax error: "("
unexpected` i `/bin/sh: 1: EOF: not found`, a wpisane w całości działają. Pole jest
poprawne; to licznik zawyża o cztery i o tyle samo zaniża kategorię pierwszą. Poprawka
kolektora nie jest tą pozycją — jest osobną pracą na `tools/tests/backlog_commands.py`
i wymaga własnej kontroli negatywnej, bo reguła sklejania ma już trzy testy w
`tools/tests/test_backlog_commands.py`.

Piąta pozycja, 6.B44, jest **poprawnym zapisem niewykonalnym dziś**: komenda woła
narzędzie, które ta pozycja ma dopiero wytworzyć. Ta klasa jest w bloku 6.D32
wymieniona z nazwy jako jeden z trzech rodzajów wyjątku.

## 7. Bramki NIE MA, i to jest wynik zmierzony

Pole „Wyjście" bloku 6.D33 dopuszcza trzy kierunki: bramkę na liczbę pokrytych
komend, adnotację w raporcie 6.D15 albo **nic**. Wybór miał wyjść z liczb i wyszedł.
Kandydatów było trzech i **każdy odpada z innego, wykonanego powodu** — a dwóch
z nich nie trzeba było nawet pisać, bo już stoją w drzewie.

### 7.1 Bramka na pokrycie audytu — pada na tekście POPRAWNYM

Przyrząd napisany i uruchomiony na trzech wejściach: dzisiejszym `docs/TASKS.md`
z `origin/main`, tym samym plikiem z dopisanym **poprawnym** blokiem
(`python3 tools/tests/test_all.py` w polu „Weryfikacja") i tym samym plikiem
z blokiem, którego komenda ma **złą ścieżkę**. Dwa warianty progu: A — „każda komenda
jest objęta audytem" (`n <= 82`), B — zapadka na dzisiejszą różnicę (`n - 82 <= 151`).
WYKONANE:

```
dzisiejsza liczba komend: 233  audyt 6.D15: 82  roznica: 151

1 dzisiejszy main (POPRAWNY)
   komend: 233
   WARIANT A (n <= 82):            CZERWONA  -> 233 komend nieobjetych audytem: 151 ponad 0
   WARIANT B (n - 82 <= 151):      ZIELONA

2 main + nowy POPRAWNY blok
   komend: 234
   WARIANT A (n <= 82):            CZERWONA  -> 234 komend nieobjetych audytem: 152 ponad 0
   WARIANT B (n - 82 <= 151):      CZERWONA  -> nieobjetych 152 przy zapadce 151

3 main + blok z komenda ze ZLA sciezka
   komend: 234
   WARIANT A (n <= 82):            CZERWONA  -> 234 komend nieobjetych audytem: 152 ponad 0
   WARIANT B (n - 82 <= 151):      CZERWONA  -> nieobjetych 152 przy zapadce 151
```

**Wariant A jest czerwony na dzisiejszym, poprawnym `main`** — nie da się go
wprowadzić, bo bramka, której nie da się spełnić w commicie wprowadzającym, nie jest
bramką. **Wariant B jest zielony dziś i czerwienieje na wejściu 2 dokładnie tak samo
jak na wejściu 3**: ten sam komunikat, ta sama liczba, zero różnicy. Czułość ma
100 %, swoistość **0 %** — nie odróżnia dopisania poprawnego bloku od dopisania
zepsutej komendy, bo mierzy tylko **ile komend jest**, a to rośnie od pisania kolejki.
To jest ta sama arytmetyka, którą #274 rozplątywało dla zapasu pozycji: wielkość,
która rośnie od wykonywania pracy, nie może stać pod zapadką „wolno tylko w jedną
stronę". Bramka zapalająca się na dobrym zapisie zostaje wyłączona w tym samym
tygodniu (6.D27), więc jej się nie pisze.

### 7.2 Bramka na istnienie ścieżki w komendzie — ISTNIEJE OD #388, i nie widzi tej usterki

Kategoria trzecia jest w połowie rodziną „zła ścieżka", więc bramka na istnienie
ścieżki wyglądałaby tu naturalnie. **Ona już jest**: pozycja 6.D32 weszła do `main`
w trakcie tej sesji (#388) i przyniosła `tools/tests/test_field_paths.py`, dwanaście
testów, trzy szczeble, zamkniętą listę wyjątków z zapadką na jeden. Zestaw jest
zielony (`12/12 przeszło`), a mimo tego usterka z 6.A21 stoi w drzewie.

Skan komend z pól „Weryfikacja" **wzorcem tej bramki** i wzorcem szerszym,
dopuszczającym katalog bez rozszerzenia:

```
wzorzec 6.D32 (test_field_paths.PATH_TOKEN): tokenow 156, nieistniejacych 2
    6.B39  tools/nie-ma-takiego-pliku.py
    6.B44  tools/track/vertical_profile.py

wzorzec szerszy (takze katalog bez rozszerzenia): tokenow 222, nieistniejacych 4
    6.A21  tools/ci/golden
    6.B15  tools/tests/test_
    6.B39  tools/nie-ma-takiego-pliku.py
    6.B44  tools/track/vertical_profile.py
```

Dwa trafienia bramki są zapisem POPRAWNYM i ona to wie: 6.B39 ma jawny wpis
w `EXCEPTIONS` z powodem, a 6.B44 woła narzędzie, które sama pozycja ma wytworzyć
(mechanizm `in_own_output`). Zgłoszeń zero, i to jest prawidłowy stan tej bramki.
**Niewidoczna jest dla niej tylko jedna rzecz — i to właśnie ta z 6.A21**: jej
`PATH_TOKEN` wymaga na ostatnim segmencie znanego rozszerzenia, a tools/ci/golden
jest katalogiem.

Rozszerzenie wzorca **nie jest tu poprawką po drodze i nie robię go**, z trzech
powodów, z których dwa są zmierzone. Wzorzec szerszy dokłada trafienie 6.B15, czyli
urwany na gwiazdce fragment maski `tools/tests/test_*.py` — a docstring tamtej bramki
mówi wprost, że glob odpada **świadomie**, bo „nie istnieje" nie jest o globie zdaniem
prawdziwym. Dalej: 2 zgłoszenia na 4 trafienia to gorszy stosunek niż dzisiejsze
0 na 2, więc zmiana pogarsza swoistość bramki, która właśnie została przyjęta.
I trzeci powód, niezmierzony, bo regulaminowy: to jest cudza bramka, świeżo scalona,
a `CLAUDE.md` §4.10 mówi, że nie poprawia się przy okazji plików spoza zadania.
Usterka jest tu **nazwana i policzona**, i to jest cały zakres tej pozycji.

### 7.3 Bramka na miejsca do wypełnienia — też już istnieje, i to poprawia tezę bloku

Zdanie „6.D15 nie zostawiło bramki", z którego wychodzi blok 6.D33, jest prawdziwe
o **pokryciu werdyktów** i nieprawdziwe o miejscach do wypełnienia. 6.D15 zostawiło
kolektor `tools/tests/backlog_commands.py` i dwie bramki w
`tools/tests/test_backlog_commands.py`:
`test_every_block_with_a_fence_yields_at_least_one_command` oraz
`test_the_blocks_with_placeholders_are_the_ones_the_measurement_named` — ta druga
trzyma **zbiór**, nie liczbę, więc poprawienie bloku z nawiasem zapala ją z nazwą
bloku, którego nie ma na liście. Trzecia kategoria z §4 jest więc już w tej jednej
podrodzinie pilnowana, a dopisanie drugiej bramki na to samo byłoby dubletem.

### 7.4 Co z tego zostaje

Zostaje **adnotacja**, i tylko ona: `reports/komendy-weryfikacji.md` dostaje w
nagłówku zdanie, ilu bloków dotyczył tamten pomiar. Werdykty 6.D15 zostają
**nieprzeliczone** — to pomiar z datą (`docs/04-conventions.md`), a ich wartością jest
właśnie to, co wyszło tamtego dnia. Ta pozycja kończy się bez ani jednego nowego testu
i bez ani jednej zmiany w `tools/`, i jest to wynik dopuszczony wprost przez pole
„Skończone, gdy" — ten sam, którym tego dnia skończyły się 6.A32 i 6.D35.

Zestaw narzędzi przed i po: **1957 → 1957** testów, **103 → 103** modułów, kod
wyjścia **0** — zmierzone dwa razy, raz na `origin/main` i raz na tej gałęzi. (Na
`2ffb0b0`, gdzie pomiar się zaczynał, było 1931 testów w 101 modułach; różnicę
wniosły scalenia #388 i #389, nie ta pozycja.)

## 8. Zauważone przy okazji, nietknięte

- **Audyt 6.D15 ma w sobie różnicę jednej komendy.** Jego §1 cytuje
  `komend zebranych: 83`, a §2 sumuje werdykty do **82** i mówi „Suma 82". Której
  komendy brakuje, z raportu nie wynika. Nie przeliczam tego i nie poprawiam — to
  pomiar z datą — ale liczba, którą blok 6.D33 nazywa „82", ma w źródle dwie wersje.
- **`Sim.Runner` nie tworzy katalogu wyjściowego.** Trzynaście komend z pól
  „Weryfikacja" kończy się na świeżym klonie `BŁĄD: Could not find a part of the
  path …`, bo `build/` nie jest komitowany. Odmowa jest czytelna, ale przychodzi
  **po** przebiegu: `budget … --out build/z-wybiegiem.csv` liczy 11 s, wypisuje pięć
  wierszy `[BUDŻET]` i dopiero na końcu odmawia zapisu. Osobna sprawa i osobna
  decyzja (tworzyć katalog czy odmawiać na wejściu), więc jej nie ruszam.
- **`mutation_sweep.py` wywala traceback zamiast odmowy, gdy katalog dziennika nie
  istnieje** — i robi to po ponad dwóch minutach liczenia. Sprawdzenie ścieżki
  dziennika przed kalibracją wyroczni kosztowałoby jeden `os.makedirs`. To nie jest
  ta pozycja: dotyczy kodu narzędzia, nie zapisu pola.
- **Zawężenie `--only` dopasowuje podciąg, nie nazwę pliku** — a w polach
  „Weryfikacja" stoi **25** wywołań z `--only` w **16** różnych argumentach, w tym
  cztery podane samą nazwą pliku bez katalogu. Wywołanie z bloku 6.B6
  (`--only sweep.py`) obejmuje dwa moduły, `tools/blender/sweep.py` i
  `tools/blender/tunnel_sweep.py`, i tylko dlatego nie kończy się jak 6.B13, że
  pierwszy z nich wyszedł spod `bpy`. Znalezisko jest cudze — nazwał je już §4
  raportu 6.D15 — i nadal prawdziwe.

## 9. Jak to powtórzyć

```bash
# liczba bloków, komend i miejsc do wypełnienia — kolektor 6.D15, bez zmian
python3 tools/tests/backlog_commands.py | tail -4
# zestaw narzędzi, wyrocznią jest KOD WYJŚCIA, nie liczba dopasowań grepa
python3 tools/tests/test_all.py; echo "kod: $?"
```

Rozbicie z §3 wymaga wpisania każdej z 103 unikalnych komend i odczytania kodu
wyjścia; przyrządu do tego **nie zostawiam w** `tools/tests/`, bo nie jest ani bramką,
ani jej biblioteką, a martwy kod w tym katalogu jest osobną usterką (6.B34). Metoda
jest wyżej opisana na tyle, żeby dała się powtórzyć: komendy z kolektora, każda
puszczona dosłownie, kod wyjścia i wypis jako werdykt, a przy porażce drugi przebieg
**w kolejności płotka** — bo dopiero on odróżnia brak stanu od usterki zapisu.
