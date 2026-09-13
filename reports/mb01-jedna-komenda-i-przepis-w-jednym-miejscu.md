# MB-01 — jedna komenda, przepis w jednym miejscu, i środowisko, które nareszcie go wykonuje

**13.09.2026**, na `68d2695`. Wejście: `src/Game/RunPlan.cs`, `src/Game/FirstRun.cs`,
`src/Game/project.godot`, `.github/workflows/godot-first-run.yml` (krok
`Generate package A geometry`), generatory wołane w tym kroku.

## 1. Co weszło

- **`tools/dev/prepare-playable.sh`** — cały przepis generacji pakietu A, przeniesiony
  z workflowa razem z uzasadnieniami każdego parametru.
- **`tools/dev/play.sh`** — jedna komenda otwierająca trening: bez flag trybu (ręczny
  jest domyślny), z ATP i z zapisem wejść włączonymi jawnie.
- **`.github/workflows/godot-first-run.yml`** — krok przepisany na jedno wywołanie
  skryptu.
- **`tools/tests/test_playable_scripts.py`** — sześć bramek, w tym ta, o którą w tym
  zadaniu naprawdę chodzi.

## 2. Przepis stoi w JEDNYM miejscu i to jest sprawdzane, nie deklarowane

Do 13.09.2026 przepis generacji stał wyłącznie w YAML-u. Człowiek, który chciał
uruchomić trening u siebie, przepisywał stamtąd **cztery wywołania generatorów
i pięć jawnych parametrów**. **Dwa** z tych pięciu pominięte nie kończą się błędem —
dają geometrię, która **wygląda poprawnie i nią nie jest**:

- `--platform-length-m design` pominięte → perony **94,0 m** (dolna granica R-007)
  zamiast **95,0 m** (decyzja właściciela, T-212);
- `--component platform --component edge` pominięte → schody i antresole sięgające
  **8,30 m** pod strop profilu `box_double` na **4,70 m**.

**Pozostałe trzy — i ta różnica jest treścią §10, a nie przypisem.** `--platform-gap-m`
pominięty kończy się **głośno** (argparse `required=True`, kod wyjścia **2**, zmierzone),
a `--profile box_double` ma domyślną **dokładnie tę samą wartość**, więc dziś nie zmienia
nic. Pierwsze brzmienie tego akapitu mówiło „żaden nie ma wartości domyślnej, a pominięcie
żadnego nie kończy się błędem" i było nieprawdą w obu połowach.

Bramka `test_przepis_generacji_stoi_w_DOKLADNIE_JEDNYM_miejscu` porównuje cztery
wywołania generatorów w skrypcie z ich **nieobecnością w kodzie workflowa** — komentarze
wyjaśniające są przy tym odróżniane od kodu, co ma własną kontrolę syntetyczną. Gdyby
przepis wrócił do YAML-a obok wywołania skryptu, **oba by działały, CI byłoby zielone**,
a rozjazd wyszedłby dopiero wtedy, gdy ktoś zmieni jeden i nie zmieni drugiego.

## 3. Środowisko dostało Blendera i Godota — i to zmienia rodzaj dowodu

Do dziś każdy pomiar tej sesji był pomiarem **kodu**: bramki, liczby, kontrole
negatywne. Audyt zewnętrzny miał to samo ograniczenie i mówił o nim wprost.
Na polecenie właściciela zainstalowałem oba narzędzia przypiętymi skryptami repozytorium:

```
[BLENDER] sprawdzam sumę SHA-256
blender-5.2.1-linux-x64.tar.xz: OK
[BLENDER] gotowe: /root/_tool/metro-blender/5.2.1/blender-5.2.1-linux-x64/blender
Blender 5.2.1 LTS  build date: 2026-08-25

[GODOT] sprawdzam sumę SHA-512
Godot_v4.7.2-stable_mono_linux_x86_64.zip: OK
4.7.2.stable.mono.official.ed1daf0bf
```

**Skrypt uruchomiony naprawdę, nie tylko zbramkowany:**

```
[PERON] 48 brył, 3552 wierzchołków, 3456 ścian -> build/t400/L1_A-platforms.glb
[STACJA] brył per element: edge=24, platform=24
build/t400: L1_A.glb 887952 B · M7_shell.glb 149644 B · L1_A-platforms.glb 296124 B
build/t400/chunks: 12 chunków + manifest 71730 B
```

**Decyzja właściciela wylądowała w geometrii, a nie tylko w parametrze** — sprawdzone
w wyjściu generatora, nie w wywołaniu:

```
Beekkant                     95.0 m
Étangs Noirs|Zwarte Vijvers  95.0 m
Comte de Flandre|Graaf van V 95.0 m
```

(Pierwszy peron ma 47,5 m, bo stacja stoi na kilometrażu 0,0 i mieści się połowa.)

## 4. Scena wczytała świeżą geometrię i przejechała pakiet A

Godot headless, na zasobach wygenerowanych minutę wcześniej:

```
[TUNEL] L1_A flat-preview: rezydentne 2/12 chunków w oknie [-206.0, 694.0] m, 2 siatek,
        wczytań 2 zwolnień 0, profil box_double 9.40×5.90 m, production_ready=False
[PERON] brył=48 góra płyty=1.031 m nad główką szyny
[SKŁAD] brył=11 długość=94.000 m szerokość=2.700 m dach=3.600 m nad główką szyny
[OŚ] manifest 6686.739 m vs oś z rdzenia 6686.739 m, |Δ| = 1.335E-005 m
[OŚ] L1_A: 1349 punktów, 6686.739 m, 12 stacji
[TELEMETRIA] 320 próbek -> build/t400/godot.csv
[PRZEJAZD] koniec: kroków=38194 t=318.283 s chainage=6653.791 m droga=6559.791 m
           klatek=319 powód=stopped
```

**Przy okazji potwierdzony na żywo pomiar 6.D202:** wiersze `[ZAŁOŻENIE widok]` mają
polski prefiks, **angielski identyfikator** i polskie uzasadnienie —
`CabEyeHeightM = 2.2 m — wysokość oka nad główką szyny; …`. Dokładnie tak, jak
zmierzyłem czytając kod, i po raz pierwszy **widziane w wyjściu**, a nie wywnioskowane.

## 5. Nazwany błąd zamiast pustej sceny — punkt 7 odbioru M1, wykonany

```
$ GODOT_BIN=/root/_tool/metro-godot/4.7.2-stable/godot \
      ASSETS_DIR=/tmp/nie-ma-takiego bash tools/dev/play.sh
[TRENING] brakuje zasobów, których scena nie zbuduje sama:
[TRENING]   /tmp/nie-ma-takiego/chunks/L1_A-chunks.json
[TRENING]   /tmp/nie-ma-takiego/M7_shell.glb
[TRENING]   /tmp/nie-ma-takiego/L1_A-platforms.glb
[TRENING] uruchom najpierw: bash tools/dev/prepare-playable.sh
kod wyjścia: 4
```

Kod **4**, osobny od kodu błędu Godota — wołający je odróżni. **`GODOT_BIN` stoi
w poleceniu i to jest poprawka** (§10): pierwsza wersja transkryptu go pomijała, a bez
niego skrypt wychodzi kodem **3** („nie ma Godota"), bo silnik leży poza `PATH`
(`runner.tool_cache`, `CLAUDE.md` §9). Liczba 4 była prawdziwa, polecenie —
nieodtwarzalne jak zapisane.

## 6. Siedem kontroli negatywnych, baza 6/6

| kontrola | podstawienie | wynik |
|---|---|---|
| KN-1 | przepis WRACA do workflowa obok wywołania skryptu | 5/6 |
| KN-2 | `--platform-length-m design` zdjęte z przepisu | 5/6 w tym module; wywraca też `test_platform_length_in_pipeline.py` |
| KN-3 | `play.sh` bez `--signalling` (ATP) | 5/6 |
| KN-4 | `play.sh` z `--line` (autopilot udający trening) | 5/6 |
| KN-5 | bit wykonania zdjęty ze skryptu | 5/6 |
| KN-6 | czytnik komentarzy bierze WSZYSTKO za kod (kontrola przyrządu) | **4/6** po poprawce, 5/6 przed |
| KN-7 | kod wyjścia braku zasobów zmieniony na ogólny | 5/6 |

`md5sum -c` na czterech plikach po każdej: `OK`. **Ani jedna zielona.**

**KN-3 i KN-4 są tu najważniejsze i obie mówią o tym samym:** scena bez ATP i scena
z autopilotem **wyglądają identycznie** jak trening. Pierwsza nie chroni, w drugiej
klawisze prowadzenia nie sterują pociągiem — i jednego ani drugiego nie widać z okna.

## 7. Trzy bramki zapaliły się na przeniesieniu i każda słusznie

Przeniesienie przepisu do `tools/dev/` zapaliło trzy istniejące bramki, które o nim
nie wiedziały. Każda została **naprawiona w miejscu, którego naprawdę dotyczyła**:

- `test_pipeline_platforms_measure_the_owner_decision` liczyła wołających
  `station_layout.py` w `tools/ci/` i workflowach — **korpus poszerzony o `tools/dev/`**,
  bo przepis tam teraz stoi. Jej treść (obaj wołający podają `--platform-length-m
  design`) zostaje bez zmian.
- `test_workflow_actually_runs_the_metadata_gate` porównywała pozycje `--chunk-manifest`
  i `--manifest` w jednym pliku. **Asercja przepisana**: warunek jest ten sam (krok
  wytwarzający manifest przed krokiem czytającym), tylko wytwarza go teraz skrypt.
- `test_zdanie_o_liczbie_modulow_zgadza_sie_z_katalogiem` — 124 → 125 modułów, razem
  z liczbami w `docs/06-worked-example.md` (203 → 204 pliki bajtkodu).

## 8. Czego świadomie nie zrobiłem

- **Nie uruchomiłem treningu w oknie.** Godot jest, ale ekranu nie ma; `play.sh` wykonuje
  `exec` na trybie interaktywnym. Sprawdzone jest wszystko poza samym oknem: generacja,
  wczytanie zasobów, przejazd headless, ścieżka błędu. **Punkty 2–5 odbioru M1 pozostają
  niewykonane po mojej stronie** i tak są oznaczone.
- **Nie zmieniłem żadnej geometrii ani zachowania sceny.** MB-01 jest o uruchamianiu.
- **Nie dotknąłem trybów `replay`, `telemetry` ani `shot`** — pole „Poza zakresem".

## 9. Zauważone po drodze, nie tknięte

- **`[TUNEL] … production_ready=False`** — manifest chunków niesie tę flagę i scena ją
  wypisuje przy każdym uruchomieniu, także w treningu. Dla gracza jest to komunikat
  bez znaczenia, a dla autora informacja, że wariant to `flat-preview`. Nikt nie
  rozstrzygnął, czy ma zostać w wyjściu grywalnym.
- **`[PERON] obwiednia 5456.1 x 1.03 x 1992.4 m`** — obwiednia wszystkich 48 brył razem,
  więc liczby opisują rozrzut peronów po całej osi, a nie żaden peron. Czyta się jak
  wymiar obiektu i nie jest nim.
- **Przejazd telemetryczny kończy się na 6653,791 m przy osi 6686,739 m** — 32,9 m przed
  końcem, `powód=stopped`. To jest scenariusz `package-a-first-run` z hamowaniem od
  6420 m, więc zachowanie jest zamierzone; ale **`--telemetry` nie dojeżdża do ostatniej
  stacji** i nie jest tym samym co przejazd treningowy, którego MB-02 ma dać koniec.

## 10. Przegląd własnej zmiany wywrócił pięć zdań i JEDNĄ bramkę

Po napisaniu tego raportu przepuściłem MB-01 przez przegląd adwersaryjny — jedyne
zadanie: znaleźć w nim zdania, które nie są prawdą. Znalazł pięć. Cztery to były moje
słowa, piąte to była **bramka, która pilnowała nie tego czytnika, co trzeba**. Poprawki
są tutaj, a nie dopisane obok pierwotnego brzmienia, bo raport, który zostawia fałsz
i dokleja sprostowanie, czyta się potem jako dwa równorzędne zdania.

**(1) „Pięć parametrów, z których żaden nie ma wartości domyślnej, a pominięcie żadnego
nie kończy się błędem" — nieprawda w OBU połowach.** Zmierzone w argparse:

| parametr | co robi pominięcie | rodzina |
|---|---|---|
| `--platform-length-m design` | `default=None` → `resolve_platform_length_m` oddaje **94,0 m** jako dolną granicę R-007, z nazwanym powodem i bez ostrzeżenia | **cicha** |
| `--component platform --component edge` | `action="append"` bez domyślnej; pomoc mówi „Bez tego budowane są wszystkie" → antresola 8,30 m pod stropem 4,70 m | **cicha** |
| `--platform-gap-m 0.08` | `required=True` (`station_kit.py:76`) → argparse przerywa, Blender wychodzi **kodem 2** | **głośna** |
| `--profile box_double` | `default="box_double"` (`tunnel_sweep.py:51`) — **ta sama wartość** | **bezczynna dziś** |

Zdanie przeczyło samo sobie dwa wiersze dalej: „pominięte daje perony 94,0 m" jest
przecież opisem **wartości domyślnej**. Powód istnienia skryptu zostaje ten sam, tylko
teraz jest wąski i prawdziwy: **dwa parametry z pięciu**, nie pięć z pięciu.

**(2) „Sześć poleceń generatora" — cztery.** Sześć wychodziło z doliczenia
`set -euo pipefail` i `ls … | sed`. Liczba stała w trzech miejscach (skrypt, workflow,
raport) i w żadnym nie była liczbą generatorów, a tak się czytała.

**(3) Transkrypt `play.sh` był NIEODTWARZALNY jak zapisany.** Wklejone polecenie nie
miało `GODOT_BIN`, a bez niego skrypt wychodzi kodem **3** („nie ma Godota"), nie **4**.
Liczba 4 była prawdziwa i nadal jest — ale polecenie obok niej nie było tym, które ją
dało. To jest dokładnie ten rodzaj wklejki, przed którym `CLAUDE.md` §5 ostrzega:
wygląda jak rzeczywiste wyjście, bo nim jest, tylko nie tego polecenia.

**(4) Kontrola przyrządu KN-6 pilnowała CZYTNIKA, KTÓREGO NOŚNA ASERCJA NIE UŻYWA —
i to było usterką w bramce, nie w zdaniu o niej.** `test_przepis_generacji_stoi_w_DOKLADNIE
_JEDNYM_miejscu` miała po stronie workflowa **własny filtr inline**
(`not w.lstrip().startswith("#")`), a `_bez_komentarzy` czytało wyłącznie skrypt.
Zmierzone: zepsucie `_bez_komentarzy` (zwraca całość) wywracało **tylko** kontrolę
syntetyczną — 5/6, a bramka jednego miejsca zostawała **zielona**. Czyli dwie kopie tej
samej wiedzy, dokładnie to, czego ta bramka broni w przepisie generacji.

Naprawione tam, gdzie leżało: strona workflowa idzie teraz przez `_bez_komentarzy`.
**Po poprawce KN-6 zapala DWA testy zamiast jednego — 4/6, nie 5/6** — i drugim z nich
jest nośna bramka, na wierszu komentarza `# liczy tools/track/station_layout.py`
(`godot-first-run.yml:20`). Kontrola przyrządu od teraz naprawdę kontroluje przyrząd.

**(5) „5/6" przy KN-2 było liczone tylko w obrębie jednego modułu.** Zdjęcie
`--platform-length-m design` wywraca także `test_platform_length_in_pipeline.py`, czego
tabela nie odnotowywała. Liczba w tabeli jest teraz opisana zakresem.

**Poprawione przy okazji, bo było tą samą usterką: `play.sh` wypisywał WŁASNY wiersz
sterowania.** „Spacja hamulec · R reset" — a gra nazywa spację „hamulec awaryjny
(= pełny służbowy)" (`src/Game/UI/UiText.cs:114`), a `R` — „od nowa". Druga kopia napisów
interfejsu, rozjechana **w chwili, w której powstała**, i bez ani jednej bramki nad sobą.
Katalog `UiText` istnieje dokładnie po to (6.D83), a HUD pokazuje z niego wiersz
sterowania. Wiersz z powłoki usunięty; powód stoi w skrypcie.

**Czego ten przegląd NIE podważył:** ani jednej liczby z pomiarów. Rozmiary plików,
48 brył, 3552 wierzchołki, 95,0 m peronów, oś 6686,739 m, `|Δ|` 1,335E-05 m, 38 194
kroki, kody wyjścia 3 i 4, 124→125 modułów, 204 pliki bajtkodu i wszystkie siedem
kontroli negatywnych zostały odtworzone niezależnie i zgadzają się co do cyfry. Padły
**wyłącznie zdania, które opisywały pomiar, zamiast go przytaczać** — i to jest ten sam
wzorzec, który ten projekt tropi od 6.D27.
