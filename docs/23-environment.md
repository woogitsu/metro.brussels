# Środowisko — co, w jakiej wersji i skąd

`doctor.sh` mówi, **czego brakuje**. Ten plik mówi, **skąd to wziąć**: dokładne
adresy, wersje, sumy kontrolne i polecenia, które zostały wykonane, a nie
przepisane z pamięci.

Powstał, bo świeża maszyna nie ma ani Blendera, ani .NET, ani Godota, a odtworzenie
tego zestawu ze zgadywania kosztuje pół sesji. Wszystkie liczby niżej są zmierzone
03.09.2026 na Ubuntu 24.04.4 LTS (noble), x86-64.

---

## 1. Zestaw minimalny — czym się różnią trzy poziomy

Nie wszystko jest potrzebne od razu. `doctor.sh` dzieli to na trzy poziomy i warto
tego podziału trzymać się przy instalacji:

| poziom | narzędzia | bez tego nie działa |
|---|---|---|
| baza | `python3` (3.11+), `git` | `tools/tests/test_all.py` — 1338 testów |
| rdzeń symulacji | .NET SDK 10.0 | `dotnet test tests/Sim.Tests` — 331 testów |
| zadania geometryczne | Blender | T-010, T-011, T-012, T-2xx |
| scena | Godot 4.7.2 mono + `xvfb` | T-400 |

Python i git są w każdym sensownym obrazie. Trzy pozostałe pozycje trzeba pobrać
i to one są treścią tego dokumentu.

## 2. Blender — dwie drogi, i one nie są równoważne

To jest jedyne miejsce w tym zestawie, gdzie wybór wersji ma konsekwencje, więc
opisane są obie drogi, a nie tylko ta wygodniejsza.

### 2.1 apt — 4.0.2, i CI już z niego NIE korzysta

> **Od 03.09.2026 CI bierze Blendera z tarballa, nie z apt.** Ta sekcja została
> przepisana, a nie dopisana obok, bo poprzednia wersja mówiła „tego używa CI"
> i to już nieprawda. Powód jest w punkcie 2.3: `apt` daje 4.0.2 do końca życia
> noble, a 4.0.2 renderuje **legacy EEVEE**, podczas gdy baseline projektu jest
> z EEVEE Next. Z apt zostały wyłącznie biblioteki systemowe.

```bash
export APT_CACHE_DIR="$HOME/.cache/metro-apt"
bash tools/ci/apt_install.sh --set blender        # albo --set blender-xvfb dla Godota
```

Zestawy pakietów leżą w `tools/ci/apt-packages/`. Po zmianie z 03.09.2026 instalują
**tylko biblioteki**:

| pakiet | wersja w noble | po co |
|---|---|---|
| `libegl1` | `1.7.0-1build1` | kontekst EGL do renderu headless |
| `libgl1-mesa-dri` | `25.2.8-0ubuntu0.24.04.2` | programowy sterownik GL |
| `libgl1` | `1.7.0-1build1` | tylko w `blender-xvfb`, pełny libGL dla Godota |
| `xvfb` | `2:21.1.12-1ubuntu1.6` | tylko w `blender-xvfb` |

Wypadły dwa pakiety i oba z powodem. `blender` — bo przychodzi z tarballa.
`python3-numpy` — bo był potrzebny **wyłącznie** dla Blendera z apt, który linkuje
się z systemowym Pythonem; tarball wozi własny Python 3.13 i numpy 2.3.4, a żaden
moduł w `tools/` ani `src/` nie importuje numpy poza Blenderem (sprawdzone grepem
po całym drzewie).

Gdyby ktoś chciał odtworzyć STARY zestaw — ten, którego CI używało do 02.09.2026 —
instalował on dodatkowo:

| pakiet | wersja w noble | po co |
|---|---|---|
| `blender` | `4.0.2+dfsg-1ubuntu8` | generatory geometrii — **zastąpione tarballem** |
| `python3-numpy` | `1:1.26.4+ds-6ubuntu1` | Blender z apt **nie ma własnego** numpy |

**Koszt, zmierzony 03.09.2026 na czystym kontenerze:**

```
7 upgraded, 174 newly installed, 0 to remove and 193 not upgraded.
Need to get 200 MB of archives.
After this operation, 629 MB of additional disk space will be used.
Fetched 200 MB in 41s (4843 kB/s)
```

Komentarz na początku `apt_install.sh` podaje 162 pakiety i 190 MB — to pomiar
z 02.09.2026 na runnerze GitHuba i różnica jest normalnym dryfem lustra, nie błędem.
Tam samo pobranie zajmowało ponad 20 minut przy ~150 kB/s; tu 41 s. Dlatego ten skrypt
ma własne limity na gniazdo i cache `.deb` — nie jako obejście, tylko jako budżet,
który musi się zgadzać także na wolnym lustrze.

Ważny szczegół tej drogi: Blender z apt jest zlinkowany z **systemowym** Pythonem
(3.12.3 w noble), a nie z własnym. Dlatego `python3-numpy` jest na liście pakietów —
bez niego `import numpy` w `--background` pada. Systemowy `python3`, którym chodzą
testy narzędzi, może być zupełnie inną wersją (u nas 3.11.15) i to nie jest problem:
te dwa Pythony nigdy się nie spotykają.

### 2.2 Oficjalny tarball — 5.2.1 LTS

Kiedy potrzebna jest konkretna wersja, apt nic nie da: noble ma 4.0.2 i będzie miał
4.0.2 do końca życia wydania. Wtedy bierze się tarball wprost od Blender Foundation.

Katalog wydań: **<https://download.blender.org/release/>** — jeden podkatalog na
serię (`Blender5.0/`, `Blender5.1/`, `Blender5.2/`). Każdy zawiera plik
`blender-<wersja>.sha256`, i **z tego pliku bierze się sumę, nie z opisu na stronie.**

```bash
cd /tmp
curl -O https://download.blender.org/release/Blender5.2/blender-5.2.1.sha256
curl -fL --retry 4 -O https://download.blender.org/release/Blender5.2/blender-5.2.1-linux-x64.tar.xz
grep 'linux-x64' blender-5.2.1.sha256 | sha256sum -c -     # musi dać: OK

sudo mkdir -p /opt/blender
sudo tar -xJf blender-5.2.1-linux-x64.tar.xz -C /opt/blender
/opt/blender/blender-5.2.1-linux-x64/blender --version
```

Zmierzone:

```
blender-5.2.1-linux-x64.tar.xz   383 688 088 B (366 MiB), po rozpakowaniu 1,2 GB
sha256  a31f524fa99a527d3d52b7f5aaa68c34e1a19d5a1c9473f79c5cc610fd5b10e9
```

Ta droga **nie wymaga ani jednego pakietu apt** — tarball wozi własny Python 3.13.13
i własny numpy 2.3.4. Nie wymaga też `sudo`, jeśli rozpakuje się go do katalogu
domowego; `/opt` jest wyborem, nie warunkiem.

> **Rozpakowuj poza `workspace`.** Na self-hosted runnerze `actions/checkout` robi
> `git clean -ffdx`, a `-x` obejmuje pliki ignorowane — Blender w workspace zniknąłby
> przy każdym checkoucie. Tak samo jak Godot, który dlatego siedzi
> w `runner.tool_cache` (`.github/workflows/godot-first-run.yml`).

### 2.3 Którą wersję wybrać

Zmierzone 03.09.2026 w tym kontenerze. Kolumna 5.2.1 to pełny przebieg bramek CI;
kolumna 4.0.2 zawiera tylko to, co w tej sesji naprawdę na niej uruchomiłem —
puste pole znaczy „nie mierzone tutaj", nie „nie działa":

| bramka | Blender 4.0.2 | Blender 5.2.1 LTS |
|---|---|---|
| `tools/ci/blender_smoke.sh` (T-010) | — | **exit 0**, 181 s |
| `tools/ci/m7_shell_check.sh` (T-220) | — | **exit 0**, 122 s |
| `tools/ci/vehicle_clearance.sh` | — | **exit 0**, 291 s |
| `tools/ci/visual_smoke.sh` (T-012) | — | **exit 0**, 287 s |
| `tools/ci/tunnel_alignment.sh` (T-210) | — | **exit 0**, 544 s |
| `tunnel_sweep.py` na `data/track/L1_A.json` | raport OK | raport OK |
| `render_check.py` — trzy zrzuty | powstały | powstały, obejrzane |
| `tools/tests/test_all.py` | 692/692 | 692/692 |
| `dotnet test tests/Sim.Tests` | 289/289 | nie dotyczy Blendera |
| `doctor.sh` | wszystko `ok` | wszystko `ok` |

Kolumna 4.0.2 jest uboga nie dlatego, że coś tam pada, ale dlatego, że **tę wersję
pilnuje CI przy każdym pull requeście** i osobny pomiar lokalny niczego by nie dodał.
Pomiar był potrzebny dla 5.2.1, bo tej wersji nikt jeszcze nie sprawdził.

Raporty geometryczne z `tunnel_sweep.py` na `data/track/L1_A.json` są **identyczne
znak w znak** na obu wersjach — te same 9520 wierzchołków, 8088 ścian, ta sama
długość osi 6686,74 m, `normalne_na_zewnatrz=0`, `kontrole geometryczne: OK`.

Czego 5.2.1 **nie** psuje, a można się bać, że psuje:

- **Nie odwraca normalnych.** Sprawdzone wprost: z 24 386 wierzchołków ani jeden nie
  ma normalnej odwróconej co do znaku wobec 4.0.2 (0 przypadków `n5 == -n4`).
- **Nie zmienia geometrii.** Wielozbiór trójek (pozycja, normalna, UV) jest
  **identyczny** na obu wersjach: 24 322 unikalne trójki, 16 176 trójkątów.
  POSITION i TEXCOORD_0 zgadzają się co do bitu (73 158/73 158 wartości).
- **Nie unieważnia baseline'ów regresji wizualnej** — w repo nie ma ani jednego PNG
  (`git ls-files | grep '\.png$'` jest puste). Baseline powstaje w przebiegu.

Czego 5.2.1 **nie zachowuje**:

- **Bajty GLB nie są przenośne między wersjami Blendera.** Ten sam plik ma na obu
  ten sam rozmiar (888 000 B) i inną sumę: `e551e21e…` na 4.0.2, `6db5fbe7…` na 5.2.1.
  Różni się 113 410 bajtów. Przyczyna jest łagodna — eksporter glTF inaczej **porządkuje
  rozszczepione wierzchołki**, czyli te, które dzielą pozycję i różnią się normalną
  (patrz punkt wyżej: wielozbiór jest ten sam).

I tu jest dobra wiadomość, której łatwo nie zauważyć: **żadna bramka projektu na tym
nie stoi.** Zostało to rozstrzygnięte wcześniej, w PR #44, i jest wpisane w kod:

```
tools/ci/tunnel_alignment.sh:316   # Bajty GLB NIE są odtwarzalne — eksporter glTF nie gwarantuje kolejności bufora
tools/ci/tunnel_alignment.sh:317   # (ustalone w PR #44). Odtwarzalna jest geometria, i to sprawdza geometry_sha256.
tools/ci/m7_shell_check.sh:284     "bajtow {...} % — bajty nie sa kontrolowane"
```

Sumy `sha256`, które pojawiają się w manifestach, są sprawdzane **w obrębie jednego
przebiegu** — plik musi się zgadzać z tym, co zadeklarował jego własny manifest.
Determinizm sprawdza `geometry_sha256`, nie `sha256` pliku. Dlatego zmiana wersji
Blendera nie zapala żadnej bramki na czerwono, i to jest zmierzone, nie założone:
wszystkie pięć bramek wyszło z kodem 0.

Odtwarzalność w obrębie 5.2.1 jest zachowana z zapasem: trzy przebiegi
`tunnel_sweep.py` dały **jedną** sumę (`sha256sum | sort -u` → 1 linia), a bramka
`tunnel_alignment.sh` zaraportowała `geometria identyczna w 12/12 chunkach; bajty GLB
identyczne w 12/12 (nie jest to wymagane)`. To ta sama własność, którą `m7_shell.py`
traci na obu wersjach — `reports/m7-glb-nondeterminism.md`.

**Decyzja podjęta 03.09.2026: CI chodzi na 5.2.1 LTS.** Podniesienie było technicznie
bezkosztowe — wszystkie bramki przechodzą, żadna nie stoi na bajtach GLB, w repo nie ma
baseline'ów do unieważnienia — ale było **zmianą wersji silnika**, więc czekało na
decyzję właściciela zgodnie z `CLAUDE.md` §8. Ta sekcja istnieje po to, żeby ta decyzja
miała liczby, a nie przeczucie.

### 2.5 Jak CI stawia Blendera po tej zmianie

Trzy rzeczy, z których każda ma swoją kontrolę negatywną w `tools/tests/test_ci_workflows.py`.

**Wersja i suma są w JEDNYM pliku** — `tools/ci/blender-version.txt`:

```
version=5.2.1
sha256=a31f524fa99a527d3d52b7f5aaa68c34e1a19d5a1c9473f79c5cc610fd5b10e9
```

Siedem kopii numeru w siedmiu workflowach to pięć okazji, żeby jedna została w tyle
i żeby baseline został porównany z klatką z innego silnika EEVEE. Test pilnuje, że
żaden workflow nie wpisuje numeru u siebie.

**Instalację robi `tools/ci/blender_install.sh`** i jest własną sondą: czyta pin,
porównuje z tym, co faktycznie stoi w katalogu, i pobiera tylko przy rozjeździe.
Zmierzone: pobranie i rozpakowanie ~15 s, drugie wywołanie **0,12 s**. Dlatego krok
w workflow NIE ma `if:` — bramkowanie z zewnątrz byłoby drugą, słabszą sondą obok mocnej.

**Sonda pyta o WERSJĘ, nie o obecność.** To jest sedno zmiany. `command -v blender`
na maszynie, która kiedykolwiek dostała Blendera z apt, znajduje 4.0.2 i uznaje
środowisko za gotowe — a to legacy EEVEE. Dowód, że nowa ścieżka to zamyka, wygląda tak:

```
$ blender --version | head -1
Blender 4.0.2                     <- to jest w PATH

$ BLENDER_BIN=$(bash tools/ci/blender_install.sh) bash tools/ci/blender_smoke.sh
Blender 5.2.1 LTS (hash 9e2066aef7ef built 2026-08-25 02:12:34)
blender_smoke EXIT=0              <- bramka pojechała na 5.2.1
```

**Skrypty wołają `${BLENDER_BIN:-blender}`**, nie gołego `blender` — ta sama konwencja,
którą `doctor.sh` ma już dla `GODOT_BIN`. Fallback na PATH zostaje, żeby uruchomienie
z ręki na maszynie z jednym Blenderem dalej działało.

**Katalog jest poza workspace**, w `RUNNER_TOOL_CACHE`, dokładnie jak Godot: `actions/checkout`
robi `git clean -ffdx`, a `-x` obejmuje pliki ignorowane, więc Blender w workspace
schodziłby z sieci (366 MB) raz na przebieg. Skrypt sam odmawia, gdy katalog docelowy
wypadnie w `GITHUB_WORKSPACE`.

### 2.4 Jedyny dług, jaki 5.2.1 pokazuje

Trzy ostrzeżenia, wszystkie te same i wszystkie o Blenderze **6.0**, nie 5:

```
tools/blender/tunnel_sweep.py:398  DeprecationWarning: 'Material.use_nodes' is expected to be removed in Blender 6.0
tools/blender/render_check.py:109  DeprecationWarning: 'World.use_nodes'    is expected to be removed in Blender 6.0
tools/blender/render_check.py:113  DeprecationWarning: 'Material.use_nodes' is expected to be removed in Blender 6.0
```

Pełna lista wystąpień w drzewie — cztery, o jedno więcej niż w ostrzeżeniach, bo
`m7_shell.py` importuje się tylko pod `bpy`:

```
tools/blender/tunnel_sweep.py:398
tools/blender/m7_shell.py:62
tools/blender/render_check.py:109
tools/blender/render_check.py:113
```

Na 5.x to ostrzeżenie, nie błąd. Na 6.0 będzie błąd i wtedy zniknie render, nie
tylko ostrzeżenie.

## 3. .NET SDK 10.0

**Ta sekcja jest przepisana 04.09.2026, a nie dopisana obok.** Poprzednia wersja
mówiła „SDK 8.0", `dotnet-sdk-8.0` i „zmierzone: 8.0.130" — to już nieprawda i było
nieprawdą od `ba93903`, czyli od podniesienia projektów na `net10.0`. Świeża maszyna
postawiona z tamtej wersji tego dokumentu wywracała się na
`NETSDK1045: The current .NET SDK does not support targeting .NET 10.0` (zmierzone
04.09.2026 na tym kontenerze). Pilnuje tego dziś
`tools/tests/test_dotnet_version.py::test_the_document_declares_the_same_sdk_major`.

CI pina `dotnet-version: '10.0.x'` przez `actions/setup-dotnet`
(`sim-tests.yml`, `blender-smoke.yml`, `godot-first-run.yml`). **Noble nie ma SDK 10
w repozytorium własnym** — `apt` daje najwyżej 8.0.x, więc apt tu nie wystarcza:

```bash
curl -fsSL https://dot.net/v1/dotnet-install.sh -o /tmp/dotnet-install.sh
bash /tmp/dotnet-install.sh --channel 10.0 --install-dir "$HOME/.dotnet"
export PATH="$HOME/.dotnet:$PATH"
dotnet --version        # zmierzone 04.09.2026: 10.0.400
```

`doctor.sh` sprawdza to twardo: czyta major z `<TargetFramework>` w `src/Sim/Sim.csproj`
i wymaga SDK **nie starszego**, więc SDK 8 na maszynie z tym drzewem jest wykrywany
jako brak, a nie jako ostrzeżenie.

Rdzeń w `src/Sim/` nie ma zależności NuGet, ale `tests/Sim.Tests` ma trzy pakiety —
**pierwsze uruchomienie na czystej maszynie potrzebuje sieci na `restore`**, potem
liczy się z cache. Warto ustawić `DOTNET_CLI_TELEMETRY_OPTOUT=1` i `DOTNET_NOLOGO=1`,
żeby log CI nie zaczynał się od powitania.

Alternatywa, gdy dystrybucja nie ma pakietu: skrypt `https://dot.net/v1/dotnet-install.sh`
(`--channel 8.0`). Na noble jest niepotrzebny.

## 4. Godot 4.7.2-stable mono

**Ta sekcja jest przepisana 04.09.2026, a nie dopisana obok.** Poprzednia mówiła
„4.3-stable" i — co gorsze — podawała jako CYTAT z `project.godot` treść, której
w tym pliku nie ma. Silnik został podniesiony w `60ea54f`; dokument stał obok trzy
dni, bo nie był jednym z miejsc pilnowanych przez `test_engine_version.py`. Jest nim
od 04.09.2026 (`test_the_document_declares_the_same_engine_version`).

Dwie rzeczy, które łatwo zrobić źle: wziąć wersję bez mono i położyć ją w workspace.

Wersję dyktuje `src/Game/project.godot`:

```
config/features=PackedStringArray("4.7", "C#", "Forward Plus")
```

i `GODOT_VERSION: 4.7.2-stable` w `.github/workflows/godot-first-run.yml`. Dystrybucje
**nie pakują wariantu mono**, więc apt tu nie pomoże:

```bash
GODOT_VERSION=4.7.2-stable
DIR=/opt/metro-godot/$GODOT_VERSION
sudo mkdir -p "$DIR"
curl -fsSL -o /tmp/godot-mono.zip \
  "https://github.com/godotengine/godot/releases/download/${GODOT_VERSION}/Godot_v${GODOT_VERSION}_mono_linux_x86_64.zip"
unzip -q /tmp/godot-mono.zip -d /tmp/godot-mono
sudo mv /tmp/godot-mono/Godot_v${GODOT_VERSION}_mono_linux_x86_64/* "$DIR"/

export GODOT_BIN="$DIR/Godot_v${GODOT_VERSION}_mono_linux.x86_64"
"$GODOT_BIN" --headless --version    # zmierzone: 4.7.2.stable.mono.official.ed1daf0bf
```

Rozmiar po rozpakowaniu: 162 MB. `GODOT_BIN` to **ta sama zmienna, o którą pyta
`doctor.sh`** i którą ustawia workflow — nie ma dwóch konwencji.

Zrzuty z Godota idą przez `xvfb-run -a "$GODOT_BIN" --rendering-driver opengl3`, więc
dla T-400 potrzebny jest zestaw `blender-xvfb`, nie `blender`.

### 4.1 Bez `DOTNET_ROOT` ten sam binarny plik nie startuje

`Godot_v4.7.2-stable_mono_linux.x86_64 --version` działa bez żadnej zmiennej .NET —
`--version` kończy proces, zanim silnik w ogóle sięgnie po mono. To jedyny powód,
dla którego ta usterka łatwo przechodzi niezauważona: sonda, która sprawdza samo
uruchomienie binarki, nic tu nie złapie (patrz `doctor.sh` niżej). Awaria pojawia się
dopiero, gdy Godot faktycznie ładuje scenę z C# — czyli w każdym prawdziwym
uruchomieniu `--path src/Game`, i tego właśnie dotyczy `godot-first-run.yml`.

**Zmierzone 06.09.2026, ten sam plik binarny, dwa przebiegi `--headless --path
src/Game` na zbudowanym `src/Game`:**

Bez `DOTNET_ROOT` i bez `dotnet` w `PATH` — silnik próbuje ustalić katalog SDK,
odpalając `dotnet` przez powłokę, nie znajduje go i pada sygnałem 11 w niecałą
sekundę (0,34 s), zanim padnie choć jeden wiersz o samej grze:

```
$ env -u DOTNET_ROOT -u DOTNET_INSTALL_DIR PATH="/usr/bin:/bin:/usr/local/bin" \
    "$GODOT_BIN" --headless --path src/Game --quit-after 3
Godot Engine v4.7.2.stable.mono.official.ed1daf0bf - https://godotengine.org

ERROR: sh: 1: dotnet: not found

   at: try_get_dotnet_root_from_command_line (modules/mono/mono_gd/gd_mono.cpp:122)
ERROR: .NET: One of the dependent libraries is missing. Typically when the `hostfxr`,
`hostpolicy` or `coreclr` dynamic libraries are not present in the expected locations.
   at: find_hostfxr (modules/mono/mono_gd/gd_mono.cpp:182)
Unable to load .NET runtime, specifically hostfxr.
ERROR: .NET: Failed to load hostfxr
   at: initialize (modules/mono/mono_gd/gd_mono.cpp:676)
handle_crash: Program crashed with signal 11
```

Z `DOTNET_ROOT="$HOME/.dotnet"` (i to samo dzieje się z `PATH` bez `dotnet` w ogóle —
sama zmienna wystarcza) silnik znajduje `$DOTNET_ROOT/host/fxr/<wersja>/libhostfxr.so`
bezpośrednio, bez odpalania `dotnet` przez powłokę, i idzie dalej do własnego kodu gry:

```
$ env DOTNET_ROOT="$HOME/.dotnet" PATH="/usr/bin:/bin:/usr/local/bin" \
    "$GODOT_BIN" --headless --path src/Game --quit-after 3
Godot Engine v4.7.2.stable.mono.official.ed1daf0bf - https://godotengine.org

[LIMIT] tryb ręczny: 72.00 km/h z planu classic-2026-L1_A (…)
ERROR: [ASSETS] brak manifestu …/build/t400/chunks/L1_A-chunks.json. Wygeneruj chunki
(tools/blender/tunnel_sweep.py --chunk-dir ...) albo uruchom z --no-geometry.
   at: void MetroBxl.Game.FirstRun.Abort(int, string) (res://FirstRun.cs:462)
```

Ten drugi przebieg pada z innego, niepowiązanego powodu (brak chunków geometrii — w
tym środowisku nie ma Blendera, więc `tools/blender/tunnel_sweep.py` się nie odpalił;
poza zakresem tej pozycji). Ważne jest miejsce awarii: `FirstRun.cs`, kod samej gry,
nie `gd_mono.cpp`. hostfxr się załadował.

**Wniosek, zmierzony, nie przypuszczony:** `DOTNET_ROOT` sam wystarcza — `dotnet` w
`PATH` jest zbędny, jeśli `DOTNET_ROOT` wskazuje katalog z `host/fxr/*/libhostfxr.so`
(dokładnie ten, który stawia `dotnet-install.sh` z sekcji 3, i dokładnie ten, na który
CI ustawia `DOTNET_ROOT` w `godot-first-run.yml`). Ustawiony, ale zły katalog (np.
literówka) NIE korzysta z tego skrótu i silnik z powrotem próbuje `dotnet` przez
powłokę — czyli awaria wygląda tak samo jak brak zmiennej w ogóle, ze wskazówką
`try_get_dotnet_root_from_command_line` w logu.

**Druga postać tej samej usterki, opisana w `6.D17` przy 6.C3 (#297), nie
odtworzona tutaj z braku brakującego assembly do zademonstrowania**: gdy silnik
znajdzie hostfxr, ale zabraknie konkretnego zestawu (assembly) w załadowanej scenie,
proces potrafi zawiesić się bez żadnego wiersza na stdout aż do wypalenia limitu
czasu joba — czyli objaw ("cisza") nie wskazuje przyczyny tak samo jak sygnał 11 nie
wskazywał brakującego `DOTNET_ROOT`, dopóki nie przeczyta się `stderr`.

Stąd `export DOTNET_ROOT="$HOME/.dotnet"` (albo katalog, do którego trafiło SDK) jest
**wymagany obok `GODOT_BIN`**, nie opcjonalny — patrz sekcja 5.

## 5. Zmienne środowiskowe

Cztery, i tylko trzy z nich są opcjonalne w tym sensie, że bez nich też się zbuduje —
tylko gorzej. Czwarta, `DOTNET_ROOT`, jest wymagana od chwili, gdy w grę wchodzi
Godot mono (sekcja 4.1): bez niej ten sam binarny plik, który przed chwilą podał
`--version`, pada sygnałem 11 albo wisi bez wyjścia, gdy tylko dotknie sceny z C#.

```bash
export BLENDER_BIN="$(bash tools/ci/blender_install.sh)"
export GODOT_BIN=/opt/metro-godot/4.7.2-stable/Godot_v4.7.2-stable_mono_linux.x86_64
export DOTNET_ROOT="$HOME/.dotnet"
export DOTNET_CLI_TELEMETRY_OPTOUT=1
export DOTNET_NOLOGO=1
```

`BLENDER_BIN` i `GODOT_BIN` są tymi dwiema, o które `doctor.sh` pyta wprost — i o które
pyta **tak samo jak CI**, a nie o coś innego. Doctor porównuje przy tym wersję Blendera
z pinem, więc rozjazd „u mnie ok, w CI czerwono" widać u siebie:

```
  WARN  blender w wersji z pinu (5.2.1, jest 4.0.2)  -> CI wymaga 5.2.1; uruchom tools/ci/blender_install.sh
```

Od 06.09.2026 `doctor.sh` pyta też, czy Godot znajdzie hostfxr — nie samą obecnością
binarki (to sprawdza `--version`, które nie łapie braku `DOTNET_ROOT`, patrz sekcja
4.1), tylko czy `DOTNET_ROOT` wskazuje katalog z `host/fxr/*/libhostfxr.so` albo czy
`dotnet` jest w `PATH`. Bez żadnego z dwóch:

```
  WARN  godot .NET hostfxr  -> ustaw DOTNET_ROOT na katalog SDK z host/fxr/*/libhostfxr.so (np. $HOME/.dotnet) albo dodaj dotnet do PATH — inaczej Godot mono pada sygnałem 11 (Failed to load hostfxr) albo wisi bez wyjścia przy starcie sceny z C#
```

## 6. Kontrola, że to naprawdę stoi

Jedno polecenie, i ono ma pokazać liczby, nie opinię:

```bash
bash doctor.sh
```

Wyjście na kompletnym środowisku (03.09.2026):

```
Wymagane dla bazy:
  ok    python3
  ok    git

Wymagane dla rdzenia symulacji (T-310 jest zrobione, src/Sim istnieje):
  ok    dotnet SDK

Wymagane dopiero przez konkretne zadania:
  ok    blender w PATH
  ok    blender headless
  ok    godot (/opt/metro-godot/4.7.2-stable/Godot_v4.7.2-stable_mono_linux.x86_64)

Testy narzędzi:
  ok    692/692 przeszło

Testy rdzenia symulacji:
  ok    289/289 przeszło
```

`doctor.sh` sprawdza `blender --version` i `blender --background --python-expr 'pass'`
**osobno**, bo Blender potrafi być w PATH i nie umieć wystartować headless — to dwie
różne awarie i mieszanie ich daje mylącą diagnozę.

Czego `doctor.sh` **nie** sprawdza i co trzeba zrobić samemu, jeśli zadanie dotyczy
geometrii: obejrzeć zrzuty. `CLAUDE.md` §5 nie jest w tej sprawie uprzejmy i ma powód —
skrypt bez błędu potrafi wyprodukować pustą scenę.

## 7. Skąd co pochodzi — jednym spojrzeniem

| co | wersja | źródło |
|---|---|---|
| Blender (CI) | 4.0.2+dfsg-1ubuntu8 | `apt`, noble/universe, przez `tools/ci/apt_install.sh --set blender` |
| Blender (LTS) | 5.2.1 LTS | <https://download.blender.org/release/Blender5.2/blender-5.2.1-linux-x64.tar.xz> |
| suma Blendera | — | <https://download.blender.org/release/Blender5.2/blender-5.2.1.sha256> |
| .NET SDK | 10.0.400 | <https://dot.net/v1/dotnet-install.sh> `--channel 10.0`; `apt` w noble daje najwyżej 8.0.x |
| Godot mono | 4.7.2-stable | <https://github.com/godotengine/godot/releases/download/4.7.2-stable/Godot_v4.7.2-stable_mono_linux_x86_64.zip> |
| numpy dla Blendera z apt | 1.26.4 | `apt`, `python3-numpy` |
| numpy w tarballu 5.2.1 | 2.3.4 | w środku tarballa, nic nie trzeba |
| `xvfb` | 21.1.12 | `apt`, zestaw `blender-xvfb` |

Dane sieci i taboru **nie są** częścią środowiska i nie pobiera się ich stąd —
hierarchia źródeł jest w `docs/07-open-data-research.md`, rejestr w
`data/network/sources.json`.
