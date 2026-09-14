# MB-04 — paczka, którą da się uruchomić bez repozytorium

**14.09.2026**, na `2542468`, gałąź `claude/mb04-paczka-gracza`. Wejście: `src/Game/FirstRun.cs`
(`RepoPath`, `BuildWorld`), `src/Game/project.godot`, `tools/ci/godot-version.txt`,
`.gitignore`, wynik MB-01…MB-03.

Pozycja domyka **M1**: od tej chwili trening da się oddać komuś, kto nie ma ani
checkoutu, ani Godota, ani Blendera.

## 1. Co weszło

| plik | co |
|---|---|
| `tools/release/package-playable.sh` | **nowy** — eksport, cztery sondy, wypisana lista zasobów, README gracza |
| `tools/ci/godot_templates_install.sh` | **nowy** — szablony eksportu po sumie SHA-512 **wydawcy** |
| `tools/ci/godot-version.txt` | trzecia linia `templates_sha512=` |
| `src/Game/export_presets.cfg` | **nowy**; `.gitignore` dostaje **nazwany wyjątek**, a nie skreślenie wiersza 31 |
| `src/Game/MetroBxl.Game.sln` | **nowy** — bez niego eksport pakuje ŹRÓDŁA C#, patrz §4 |
| `src/Game/FirstRun.cs` | `RepoPath` liczone od binarki, nowe `AssetsRoot()` i `DomyslnyZapisWejsc()`, wiersz `[ZAPISY]` |
| `tools/tests/test_player_package.py` | **nowy**, pięć asercji, pięć kontroli negatywnych |

## 2. Trzy rzeczy, które w paczce łamią się inaczej niż w checkoucie

Wszystkie trzy są **zmierzone własną sondą**, a nie wywnioskowane z dokumentacji.

### 2.1 `res://` w paczce jest NAPISEM PUSTYM

`ProjectSettings.GlobalizePath("res://")` zwraca w paczce `''`. Sonda: projekt
minimalny wyeksportowany `--export-pack`, uruchomiony `--main-pack` z **dwóch różnych
katalogów bieżących** — `res:// -> ''` w obu, przy poprawnym i bezwzględnym
`OS.get_executable_path()` oraz poprawnym `user://`.

Poprzednia wersja `RepoPath` skleiła z tej pustki `"../../" + relative`, czyli ścieżkę
**względną do katalogu bieżącego procesu**. Gracz klikający ikonę dostawał dwa poziomy
nad przypadkowym katalogiem. Dziś w paczce rozstrzyga binarka, a pusty wynik
`GlobalizePath` jest **warunkiem rozpoznania układu** — pytamy o tę jedną rzecz, która
się naprawdę różni.

### 2.2 `build/t400` to nazwa cudzego katalogu roboczego

Sam `RepoPath` nie wystarczył i **dowiedział się o tym dopiero pierwszy odbiór**:
paczka szukała manifestu pod
`…/MetroBXL/zasoby/build/t400/chunks/L1_A-chunks.json` i kończyła się `[ASSETS] brak
manifestu` z kodem 4. Ścieżka składała się poprawnie — niepoprawna była jej **treść**.

Odwrotna poprawka (dołożyć `build/t400/` w skrypcie pakującym) została **odrzucona**:
oddawałaby graczowi katalog o nazwie „build", a pierwsza zmiana katalogu wyjściowego
generatorów rozjechałaby paczkę z grą po cichu. Stąd `AssetsRoot()` obok `RepoPath()`.

### 2.3 `.glb` jest formatem IMPORTOWANYM, więc do `.pck` nie trafia

Dlatego `zasoby/` leży **obok binarki**, a nie pod `res://`. Przeniesienie ich do `.pck`
wymagałoby przemianowania 38 plików na rozszerzenie, którego Godot nie importuje,
i przepisania pola `file` w manifeście chunków.

## 3. Odbiór — PEŁNY, i to jest cała treść tej sekcji

Warunek z `docs/TASKS.md` brzmi: „uruchomić **rozpakowaną paczkę poza checkoutem**, ze
ścieżki ze spacjami, bez danych z repo, bez Godot Editora i bez Blendera; wykonać pełny
trening i ponowienie".

Paczka skopiowana do `/root/Metro BXL — odbiór MB-04/` — **spacje i myślnik w nazwie**,
poza `/workspace` — i uruchomiona z katalogiem bieżącym `/`, czyli bez żadnego związku
z położeniem gry.

```
[WEJŚCIE] odtworzenie z /root/Metro BXL — odbiór MB-04/wejscie-gracza.log: 20000 kroków, 7 zmian klawiszy
[TUNEL] L1_A flat-preview: rezydentne 2/12 chunków w oknie [-206.0, 694.0] m, 2 siatek, wczytań 2 zwolnień 0, profil box_double 9.40×5.90 m, production_ready=False
[PERON] brył=48 góra płyty=1.031 m nad główką szyny, obwiednia 5456.1 x 1.03 x 1992.4 m
[SKŁAD] brył=11 długość=94.000 m szerokość=2.700 m dach=3.600 m nad główką szyny
[OŚ] L1_A: 1349 punktów, 6686.739 m, 12 stacji
[OŚ] manifest 6686.739 m vs oś z rdzenia 6686.739 m, |Δ| = 1.335E-005 m
[SESJA] zaliczone (AllTargetsServed): 2/2 celów, 156.842 s, 1357.513 m, ATP 0/0/0 | 8742 obsłużony błąd -0.023 m | 8292 obsłużony błąd -0.387 m
```

Wiersz `[SESJA]` jest **identyczny co do znaku** z wynikiem zmierzonym przy MB-02
w checkoucie. Komplet zasobów: 12 chunków w manifeście, 48 brył peronu, 11 brył M7,
oś 1349 punktów i 12 stacji, plan `classic-2026-L1_A` przeczytany. Ostrzeżeń
i błędów Godota: **0**.

### 3.1 „Bez danych z repo" NIE jest tu słowem — checkout został ZASŁONIĘTY

Zdanie „paczka nie czyta repozytorium" wygląda tak samo, gdy jest prawdą i gdy nikt go
nie sprawdził. Sprawdzenie: przebieg w **osobnej przestrzeni montowań**, z `tmpfs`
zamontowanym na `/workspace`.

```
[KN] plików w zasłoniętym /workspace: 0
[SESJA] zaliczone (AllTargetsServed): 2/2 celów, 156.842 s, 1357.513 m, ATP 0/0/0 | 8742 obsłużony błąd -0.023 m | 8292 obsłużony błąd -0.387 m
```

Katalog z repozytorium był **pusty**, a paczka dała ten sam wynik co do znaku.
Napis `/workspace` występuje w tym logu **raz** i jest to wiersz `[KN]` wypisany przez
samą kontrolę; z gry nie pochodzi ani jedno wystąpienie.

Ten sam przebieg zrobiony na **finalnej paczce**, z zapisem `ponowienie.log` (§3.2),
daje komplet: 12 chunków, 48 brył peronu, 11 brył M7, oś 1349 punktów i 12 stacji,
plan `classic-2026-L1_A`, `resetów=1` i ten sam wiersz `[SESJA]`, przy **zerze**
ostrzeżeń i błędów Godota.

### 3.2 Ponowienie — i dowód, że wynik jest z przejazdu PO resecie

Zapis `ponowienie.log`: sekwencja MB-02 dwa razy, rozdzielona wpisem `18900;reset`
(sesja pierwszego przejazdu kończy się na kroku 18 821). Przebieg:

```
[ODTWORZENIE] koniec: kroków=20100 t=167.500 s chainage=1451.513 m droga=1357.513 m klatek=65 sesja=39000 kroków resetów=1
[SESJA] zaliczone (AllTargetsServed): 2/2 celów, 156.842 s, 1357.513 m, ATP 0/0/0 | 8742 obsłużony błąd -0.023 m | 8292 obsłużony błąd -0.387 m
```

**Wiersz `[SESJA]` wychodzi RAZ i to jest poprawne**, a nie brak drugiego przejazdu:
w trybie odtworzenia wypisuje go `FinishReplayRun` na końcu **całego** zapisu, więc
mówi o stanie sesji po drugim przejeździe. `kroków=20100` to 39 000 − 18 900, czyli
licznik liczony **od resetu**.

Tyle dawała lektura. Że wynik naprawdę pochodzi z przejazdu po resecie, a nie z
zatrzaśniętego wyniku pierwszego, rozstrzyga **kontrola negatywna**: mutacja ruszająca
wyłącznie **drugi** przejazd (hamowanie 33370 → 33800, czyli 14470 → 14900 licząc od
resetu).

```
[ODTWORZENIE] koniec: kroków=20100 t=167.500 s chainage=1523.179 m …  resetów=1
[SESJA] niezaliczone (TargetMissed): 1/2 celów, 133.025 s, 1363.055 m, ATP 0/0/0 | 8742 obsłużony błąd -0.023 m | 8292 pominięty błąd —
```

Gdyby `RunReset.Apply` nie zerowało zatrzasku sesji, ta mutacja **nie zmieniłaby
niczego** — wynik pierwszego przejazdu jest w obu zapisach ten sam.

### 3.3 Windows x64 — **NIEWYKONANE**, i tak zostaje zapisane

Pole „Uczciwość odbioru" wymaga wprost, żeby nie pomijać. Środowisko tej sesji to
Linux x86-64; maszyny z Windows nie ma, a `export_presets.cfg` ma dziś **jeden** preset
(`Linux`). Odbiór na docelowym targecie roboczym jest więc **niewykonany** — nie
„prawdopodobnie działa" i nie „powinno wystarczyć dołożyć preset".

## 4. Kod wyjścia zero NIE wystarcza — zmierzone

Bez `src/Game/MetroBxl.Game.sln` eksport kończy się **zerem**, wypisując przy tym
ostrzeżenie „no solution file was found", i pakuje **pełne źródła C#** zamiast
zaślepek. Kontrola negatywna (plik schowany, `md5sum -c: OK` po przywróceniu):

| stan | `MetroBXL.pck` | kod wyjścia skryptu |
|---|---|---|
| z `.sln` | **12 012 B** | 0 |
| bez `.sln` | **349 852 B** | **6** (sonda `grep` na logu eksportu) |

Czyli **29-krotnie** więcej, i to kodem, który miał zostać u mnie. Skrypt patrzący
wyłącznie na kod wyjścia oddałby graczowi cały kod z komentarzami i nie powiedziałby
ani słowa.

`.sln` powstał przez `dotnet new sln --format sln`, bo .NET 10 domyślnie tworzy
`.slnx`, którego Godot nie widzi — a wtedy plik istnieje i nic nie zmienia.

## 5. Brak `dotnet` daje SIGSEGV, a nie komunikat

Zmierzone przy pierwszym przebiegu skryptu, bo `dotnet` leży w `$HOME/.dotnet`, którego
nie ma w domyślnym `PATH`:

```
ERROR: sh: 1: dotnet: not found
ERROR: .NET: Failed to load hostfxr
handle_crash: Program crashed with signal 11
Dumping the backtrace. Please include this when reporting the bug on: …
```

Kod wyjścia: **134** (`Aborted`), nieodróżnialny od awarii eksportu; jedyne zdanie
mówiące, o co chodzi, stoi **w środku zrzutu stosu**, pod prośbą o zgłoszenie cudzego
buga. Skrypt ma dziś sondę, która zagląda do `$HOME/.dotnet`, a gdy i tam nie ma —
kończy się **kodem 7 i jednym zdaniem**.

## 6. README paczki obiecywało zapis, którego kod nie robił

Pierwsza wersja `CZYTAJ-TO-NAJPIERW.txt` głosiła, że „gra zapisuje naciśnięcia klawiszy
do katalogu użytkownika". Sprawdzenie: `_recorder` powstawał **wyłącznie** przy jawnym
`--input-log`, więc gracz uruchamiający paczkę dwukliknięciem nie zapisywał niczego.

Dołożony został **zapis**, a nie usunięta obietnica — bo pole „Skończone, gdy" pozycji
MB-04 wymaga wprost, żeby „logi trafiały do katalogu użytkownika". `DomyslnyZapisWejsc`
daje domyślną ścieżkę **tylko przejazdowi prowadzonemu z klawiatury**: zapis wejść
maszynisty z przejazdu, którego maszynista nie prowadził, byłby zapisem wejść,
których nikt nie wcisnął.

**Drugie kłamstwo tego samego README wyszło przy sprawdzaniu pierwszego.** Napisałem
w nim ścieżkę `~/.local/share/godot/app_userdata/MetroBXL/`, **wyprowadzoną** z nazwy
binarki. Pomiar mówi co innego, bo Godot bierze `config/name`:

```
[ZAPISY] wejścia maszynisty -> /root/.local/share/godot/app_userdata/METRO BXL — pierwszy przejazd/zapisy/ostatni-przejazd.log
```

Stąd wiersz `[ZAPISY]` na starcie: gracz ma ścieżkę **przeczytać**, a nie wyprowadzać
z nazwy projektu — tak samo jak ja. Zapis do `user://` sprawdzony do końca, na paczce,
poza checkoutem:

```
[WEJŚCIE] 20000 kroków, 7 zmian klawiszy -> user://zapisy/probny.log
```

Plik (276 B) powstał i jego treść jest **co do znaku** sekwencją z wzorca wejściowego —
pełna droga tam i z powrotem, a nie samo powstanie pliku.

## 7. Bramka i jej pięć kontroli negatywnych

`tools/tests/test_player_package.py` istnieje, bo README paczki jest **drugim
egzemplarzem tabeli sterowania**; pierwszym jest `DriverActions.All`. Przy MB-01 taka
druga kopia stała w `tools/dev/play.sh` i **już była rozjechana** — tam dało się ją
usunąć, tutaj nie: binarka nie umie wypisać sobie README przed własnym zbudowaniem.

**Bramka złapała rozjazd od razu, na moim własnym tekście.** Napisałem „hamulec
awaryjny (w tym modelu = pełny służbowy)", a katalog mówi „hamulec awaryjny
(= pełny służbowy)".

Nazwa klawisza wyprowadzana jest z **kodu klawisza** (`(int)Key.…`), a nie z literału
obok niego: literał jest tym, co gra *wypisuje*, a kod tym, co gra *czyta*. Bramka
porównująca README z literałem przepuściłaby wiersz, w którym gra pisze „X", czyta
`Key.Z`, a README posłusznie powtarza „X".

Baza **5/5**, `md5sum -c: OK` po każdej, **ani jedna zielona**:

| KN | mutacja | czerwone |
|---|---|---|
| KN-1 | `X` → `Z` przy „wybieg" w README | 1/5 |
| KN-2 | wiersz Spacji usunięty z README | **2/5** |
| KN-3 | `zasoby` → `assets` w skrypcie | 1/5 |
| KN-4 | domyślny zapis wejść odpięty od `_inputLogPath` | 1/5 |
| KN-5 | `cp -r "$ZASOBY_SRC"/*` zamiast wypisanej listy | 1/5 |

**KN-1 jest powodem, dla którego asercje o klawiszach są dwie, a nie jedna**: zmiana
samej litery przy zachowanym opisie przechodzi „czy README mówi o tym działaniu"
w całości i zapala wyłącznie „czy litera obok jest tą, którą gra czyta".

### 3.4 Punkt 7 odbioru M1 sprawdzony na paczce

`docs/PLAYABILITY.md` §3 wymaga, żeby start bez potrzebnego zasobu dawał **zrozumiały
błąd, a nie pustą scenę**. Manifest chunków usunięty z rozpakowanej paczki:

```
kod wyjścia: 4
[ASSETS] brak manifestu /root/Metro BXL — odbiór MB-04/MetroBXL/zasoby/chunks/L1_A-chunks.json. Wygeneruj chunki (tools/blender/tunnel_sweep.py --chunk-dir ...) albo uruchom z --no-geometry.
```

Komunikat nazywa **bezwzględną ścieżkę w paczce**, więc mówi graczowi, którego pliku
brakuje i gdzie. Plik przywrócony, rozmiar zgodny (71 730 B).

## 7.1 BRAMKA SEKWENCJI UCIECZKI BYŁA NIEPOPRAWNA NA PYTHONIE 3.12+ — i to CI mnie o tym powiedziało

Ta pozycja przeszła u mnie 2466/2466 i **padła w CI, na ośmiu jobach naraz**. Padał
jeden test, `test_zrodla_tools_nie_niosa_ani_jednej_zlej_sekwencji_ucieczki`, meldując
pięć złych sekwencji ucieczki w `tools/tests/test_player_package.py` — moim własnym,
nowym pliku.

**Te pięć literałów jest POPRAWNE i nie wolno ich „naprawiać".** Wszystkie są postaci
`rf"..."`, czyli surowe; `\w` i `\$` w regexie to dokładnie to, czego regex chce.
CPython na runnerze nie ma do nich zastrzeżeń — `compileall` w kroku obok przeszedł
bez jednego ostrzeżenia.

**Niepoprawny był CZYTNIK bramki.** Chodził po `ast`, brał dla każdego literału
`ast.get_source_segment` i odsiewał literały surowe po prefiksie **w tym fragmencie**.
Do 3.11 części f-stringa dziedziczyły pozycję całego literału, więc fragment zawierał
`rf"` i odsianie działało. Od 3.12 (**PEP 701**) każdy kawałek tekstu f-stringa ma
własne `lineno/col_offset`, wskazujące sam tekst **bez prefiksu** — wzorzec odsiewający
przestawał trafiać.

Zmierzone na tym drzewie, czterema interpreterami:

| interpreter | trafień | kod |
|---|---|---|
| 3.11.15 | **0** | 0 |
| 3.12.3 | **5** | 1 |
| 3.13.12 | **5** | 1 |
| 3.14.0rc2 | **5** | 1 |

**Runner ma 3.14.4, a to drzewo miało 3.11.15 — i ta różnica jest całą przyczyną,
dla której bramka była zielona u mnie i czerwona w CI.** Od tej pozycji uruchamiam
zestaw na `/usr/bin/python3.13`, czyli po stronie PEP 701; sprawdzam obie wersje.

**Poprawka: czytnikiem jest `tokenize`, nie `ast.get_source_segment`.** Tokenizer podaje
prefiks tam, gdzie on w źródle naprawdę stoi, i robi to tak samo na obu epokach —
**bez ani jednego rozgałęzienia po `sys.version_info`**: do 3.11 cały f-string to jeden
`STRING` z prefiksem, od 3.12 to `FSTRING_START` (niosący `rf"`), `FSTRING_MIDDLE`
(sam tekst) i `FSTRING_END`, a te nazwy po prostu nie padają na 3.11. Gałąź nietestowana
na danej wersji cicho by nie działała — tego właśnie unikamy.

**Wariant „badać cały `JoinedStr` raz" został odrzucony POMIAREM, nie argumentem.**
Zaimplementowany i uruchomiony: na dzisiejszym drzewie daje zero trafień, ale wnosi
**nową klasę fałszywego alarmu dokładnie na tych wersjach, dla których robimy
poprawkę** — od 3.12 ukośnik jest legalny w polu podstawienia, więc skan po całym
fragmencie czyta KOD podstawienia jak tekst napisu i zapala się na
`f"{re.sub(r'\d', '', s)}"`. Wersja z tokenizerem daje tam zero.

`ast.parse` **zostaje**, ale wyłącznie jako przyrząd kontrolny — odpowiada na inne
pytanie („czy moduł w ogóle się parsuje"), którego sam tokenizer nie umie zadać, bo
jest leksykalny i `def f(:` przechodzi przez niego bez sprzeciwu. Wyłapywanie modułów
nieparsowalnych to połowa tej bramki (KN-1 z 6.D147).

**Bramka złapała przy okazji mnie samego:** przepisując funkcję, zgubiłem prefiks `r`
przy jej własnych docstringach i natychmiast zameldowała `\d`, `\|` i `\.` w moim
nowym tekście. CPython potwierdził to niezależnie `SyntaxWarning`-iem.

**Trzy kontrole negatywne, wszystkie na kopii, `md5sum -c: OK` po każdej:**

| KN | mutacja | 3.11.15 | 3.13.12 |
|---|---|---|---|
| KN-A | `"zle \d tutaj"` bez prefiksu `r` | 1 trafienie | 1 trafienie |
| KN-B | `f"zle {1} \w tutaj"` bez prefiksu `r` | 1 trafienie | 1 trafienie |
| KN-C | `rf"zewn \w {f'wewn \q'} koniec"` — zewnętrzny surowy, **wewnętrzny nie** | 0 (składnia nie istnieje na 3.11; plik ląduje w `nieparsowalne`) | **1 trafienie** |

KN-C jest tu treścią, a nie ozdobą: pokazuje, że stos surowości działa, i że zdolność
tej bramki **rośnie** z wersją interpretera zamiast na niej padać.

Na całym drzewie po poprawce: **0 trafień, 205 modułów, 0 nieparsowalnych** na 3.11.15
i na 3.13.12. `MAX_SEKWENCJI_UCIECZKI = 0` i `MINIMUM_MODULOW_SKANOWANYCH = 100`
zostają bez zmiany.

## 8. Czego świadomie NIE zrobiłem

- **Odbioru na Windows x64** — §3.3, oznaczone jako niewykonane.
- **Nie dołożyłem presetu Windows „na wszelki wypadek".** Preset, którego nikt nigdy
  nie uruchomił, wygląda w `export_presets.cfg` dokładnie tak samo jak działający.
- **Nie wstawiłem paczki ani `build/` do Gita** (reguła 8 `CLAUDE.md`).
- **Nie tknąłem `docs/03-legal.md` ani niczego o publikacji** — poza zakresem pozycji.

## 9. Co zauważyłem po drodze, ale zostawiłem

- `L1_A.glb` (887 952 B) jest generowany i **nie jest przez scenę czytany** — scena
  jedzie chunkami. Do paczki nie wchodzi, ale w `build/t400` powstaje przy każdym
  przebiegu. Pozycja dla pasma A, po domknięciu M1.
- `godot.csv` (32 757 B) leży w `build/t400` obok zasobów, choć jest **telemetrią CI**,
  a nie zasobem. W paczce wyglądałby jak zapis cudzego przejazdu.
- Paczka waży **159 MB**, z czego binarka 73,7 MB, a `.pck` 12 kB. Reszta to runtime
  .NET. Nie ruszam tego w tej pozycji.
- **Uruchomienie Godota na tym drzewie wytwarza 24 pliki `*.cs.uid`** — i to MB-04
  jest pierwszą pozycją, która je wywołuje, bo pierwszą, która uruchamia eksporter
  na checkoucie. Do drzewa **nie weszły**; `.gitignore` dostał wiersz `*.cs.uid`,
  żeby robocza kopia nie zostawała brudna po każdym pakowaniu.

  **To zapis stanu zastanego, nie rozstrzygnięcie sporu**, i tak stoi w samym
  `.gitignore`. Zmierzone w dniu wpisu: śledzonych `*.uid` jest w repozytorium
  **zero**, a `src/Game/Scenes/FirstRun.tscn` nie odwołuje się do ani jednego
  `uid://` — scena ładuje się bez nich, a `git clean -ffdx` z `actions/checkout`
  kasuje je w CI przy każdym przebiegu. Projekt Godot zaleca coś przeciwnego i przy
  pierwszym `uid://` w scenie ten wiersz trzeba będzie zdjąć; wpisanie do drzewa
  dwudziestu czterech plików, do których dziś nic nie sięga, byłoby jednak zmianą
  o CAŁYM drzewie przemyconą jako skutek uboczny pakowania. **Sprawdzone, że wiersz
  niczego nie psuje:** eksport po jego dodaniu daje ten sam `.pck` o **12 012 B**.
- **Komunikat `[ASSETS] brak manifestu` odsyła gracza do `tools/blender/tunnel_sweep.py`**,
  czyli do narzędzia, którego w paczce nie ma i mieć nie będzie. Ścieżkę brakującego
  pliku podaje poprawnie, więc komunikat jest użyteczny — ale drugie zdanie jest radą
  dla dewelopera wydaną graczowi. Pozycja dla pasma A, po domknięciu M1; przy aktywnym
  kamieniu milowym pobocznego znaleziska się nie bierze (`CLAUDE.md` §8).
