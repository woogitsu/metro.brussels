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
uruchomić trening u siebie, przepisywał **sześć poleceń i pięć jawnych parametrów,
z których żaden nie ma wartości domyślnej**. Pierwsza literówka nie kończyła się błędem
— dawała geometrię, która **wygląda poprawnie i nią nie jest**:

- `--platform-length-m design` pominięte → perony **94,0 m** (dolna granica R-007)
  zamiast **95,0 m** (decyzja właściciela, T-212);
- `--component platform --component edge` pominięte → schody i antresole sięgające
  **8,30 m** pod strop profilu `box_double` na **4,70 m`.

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
$ ASSETS_DIR=/tmp/nie-ma-takiego bash tools/dev/play.sh
[TRENING] brakuje zasobów, których scena nie zbuduje sama:
[TRENING]   /tmp/nie-ma-takiego/chunks/L1_A-chunks.json
[TRENING]   /tmp/nie-ma-takiego/M7_shell.glb
[TRENING]   /tmp/nie-ma-takiego/L1_A-platforms.glb
[TRENING] uruchom najpierw: bash tools/dev/prepare-playable.sh
kod wyjścia: 4
```

Kod **4**, osobny od kodu błędu Godota — wołający je odróżni.

## 6. Siedem kontroli negatywnych, baza 6/6

| kontrola | podstawienie | wynik |
|---|---|---|
| KN-1 | przepis WRACA do workflowa obok wywołania skryptu | 5/6 |
| KN-2 | `--platform-length-m design` zdjęte z przepisu | 5/6 |
| KN-3 | `play.sh` bez `--signalling` (ATP) | 5/6 |
| KN-4 | `play.sh` z `--line` (autopilot udający trening) | 5/6 |
| KN-5 | bit wykonania zdjęty ze skryptu | 5/6 |
| KN-6 | czytnik komentarzy bierze WSZYSTKO za kod (kontrola przyrządu) | 5/6 |
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
