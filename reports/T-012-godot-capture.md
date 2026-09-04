# T-012, druga połowa: zrzuty z silnika idą przez tę samą kontrolę co rendery Blendera

**Zmierzone na commicie:** `4575195`

Stan: **2026-09-01**. Domyka `[~] T-012` z `docs/TASKS.md` — część Blenderowa weszła
z #27, część Godotowa czekała na T-400, który jest już w `main`.

---

## 1. Co było nie tak

`godot-first-run.yml` sprawdzał zrzuty tak:

```bash
test "$(ls renders/t400/*.png | wc -l)" -eq 5
```

**Czarna klatka 1280 × 720 z działającym HUD-em to też pięć plików.** I dokładnie tak
wygląda scena, w której symulacja liczy się poprawnie, a geometria się nie wczytała —
prędkość, kilometraż i nastawnik są na miejscu, świata nie ma.

To jest forma weryfikacji, którą `CLAUDE.md` §5 wymienia jako zakazaną: „skrypt
wykonał się bez błędu".

## 2. Pomiar zamiast założenia

Zamiast przyjąć progi, zmierzyłem klatkę bez geometrii (`--no-geometry`, sam HUD)
i pięć prawdziwych ujęć:

| ujęcie | ink | luma_std | poziomy |
|---|---:|---:|---:|
| **bez geometrii (sam HUD)** | **0,0127** | **0,0819** | **235** |
| `outside_2000m` (najsłabsze prawdziwe) | 0,5433 | 0,0895 | 210 |
| `chase_2000m` | 0,7102 | 0,0941 | 213 |
| `seam_c01_c02` | 0,8155 | 0,1192 | 212 |
| `cab_2000m` | 0,8236 | 0,1204 | 210 |
| `curve_R91_chase` | 0,8939 | 0,1061 | 213 |

Wnioski z tych liczb, wszystkie nieoczywiste:

- **`ink_fraction` jest jedynym wskaźnikiem, który tu rozróżnia**: 0,0127 wobec 0,5433,
  czyli **43-krotna różnica**. Próg 0,30 leży 24× nad pustką i 1,8× pod najsłabszym
  prawdziwym ujęciem.
- **`distinct_levels` wskazuje ODWROTNIE.** Klatka z samym HUD-em ma **235** poziomów
  jasności, a najbogatsza prawdziwa **213**. Próg „przynajmniej N poziomów", który
  pilnuje renderów Blenderowych, **przepuściłby pustkę i odrzucił geometrię**. Biały
  tekst na czerni to bogaty histogram; równomiernie oświetlona ściana tunelu to wąski.
- **`luma_std` nie rozróżnia**: 0,0819 pusta wobec 0,0894 najsłabszej prawdziwej —
  9 % różnicy, za mało na próg.

Dlatego zestaw `godot` w `tools/visual/cameras.json` opiera kontrolę na `ink_fraction`,
a dwa pozostałe progi ma nisko i **jawnie opisane jako kontrola „to nie jest jednolity
kolor", a nie jako rozróżnienie**.

## 3. Zrzuty są odtwarzalne co do bajtu

Dwa przebiegi tego samego ujęcia dały **identyczny sha256** i zerową różnicę:

```
3f397625a3841044  cab_2000m.png
3f397625a3841044  REPEAT_cab_2000m.png
{'mean_abs_diff': 0.0, 'p95_abs_diff': 0.0, 'max_abs_diff': 0.0, 'changed_fraction': 0.0, 'ssim': 1.0}
```

To odróżnia je od eksportu glTF, który **nie jest** odtwarzalny bajtowo (PR #44).

**Odtwarzalność między maszynami też jest już zmierzona** — pierwszy przebieg CI na
runnerze GitHuba (Mesa 25.2.8, inna maszyna, inna wersja sterownika) dał **te same
rozmiary wszystkich pięciu plików co do bajtu**:

| ujęcie | ten kontener | runner GitHuba | ink (tu / tam) |
|---|---:|---:|---|
| `cab_2000m` | 139 984 B | 139 984 B | 0,8236 / 0,8236 |
| `chase_2000m` | 92 686 B | 92 686 B | 0,7102 / 0,7102 |
| `outside_2000m` | 121 077 B | 121 077 B | 0,5433 / 0,5433 |
| `curve_R91_chase` | 98 895 B | 98 895 B | 0,8939 / 0,8939 |
| `seam_c01_c02` | 139 841 B | 139 841 B | 0,8155 / 0,8155 |

Klatka negatywna również: 0,01272 / 0,08194 / 235 poziomów w obu miejscach.

Baseline jest więc wykonalny i **będzie miał sens** — ale **nie jest jeszcze zapisany**,
bo `--accept-baseline` nigdy nie dzieje się automatycznie (T-012). Progi różnicowe
(`mean_abs_diff`, `ssim_min`) są przepisane z zestawu `vehicle` i pozostają
**nieprzetestowane** do czasu zatwierdzenia baseline'u — dwa identyczne obrazy nie
sprawdzają progu różnicy.

## 4. Metadane, bo obraz tego nie wykryje

Metryka obrazowa nie zauważy przesunięcia całej sceny — kamera jedzie razem z nią.
To jest ta sama pułapka, którą `compare.py` opisuje dla Blendera, więc rozwiązanie
jest to samo: scena Godota zapisuje obok zrzutu `GODOT_metadata.json` w tym samym
kształcie, jakiego oczekuje `check_geometry`.

```json
{
 "engine": "godot", "engine_version": "4.3-stable (official)",
 "manifest_version": "L1_A/flat-preview", "resolution": [1280, 720],
 "last_shot": {"view": "Cab", "chainage_m": 976.180, "steps": 6343},
 "scene": {
  "bbox_min": [-4.4386, -1.2000, -910.3813],
  "bbox_max": [5448.1050, 4.7000, 1076.5525],
  "size_m": [5452.5435, 5.9000, 1986.9338],
  "mesh_objects": 12, "vertices": 48528, "faces": 16176,
  "chunks_loaded": 12, "chunks_declared": 12, "axis_length_m": 6686.739
 }
}
```

Wysokość obwiedni **5,9000 m** zgadza się co do czwartego miejsca z wysokością profilu
`box_double` — czyli bbox liczony w Godocie opisuje tę samą geometrię, którą wypuścił
generator, a nie coś przeskalowanego przy imporcie.

Plik jest **jeden na prefiks** i kolejne ujęcia go nadpisują. Pole `scene` jest dla
wszystkich pięciu identyczne i to ono jest tu treścią; pole opisujące ostatnie ujęcie
nazywa się `last_shot` właśnie po to, żeby nikt nie odczytał go jako opisu całego
zestawu.

## 5. Zestaw, którego Blender nie może wyrenderować

`godot` ma pole `"renderer": "godot"` i kamery **bez** geometrii — bo kamery są
w scenie Godota, a nie w manifeście. `capture_blender.py` odmawia takiego zestawu
wprost:

```
BŁĄD: zestaw godot jest renderowany przez 'godot', nie przez Blendera — tu nie ma czego renderować
```

Bez tej odmowy Blender wygenerowałby z niego klatki domyślną kamerą i nikt by nie
zauważył, że to nie są te ujęcia.

## 6. Weryfikacja — rzeczywiste wyjście

Ścieżka pozytywna:

```
  new-baseline cab_2000m  ink=0.8236 std=0.1204
  new-baseline chase_2000m ink=0.7102 std=0.0941
  new-baseline outside_2000m ink=0.5433 std=0.0895
  new-baseline curve_R91_chase ink=0.8939 std=0.1061
  new-baseline seam_c01_c02 ink=0.8155 std=0.1192
  new-baseline geometria
[WYNIK] pass — {'total': 6, 'pass': 0, 'fail': 0, 'new_baseline': 6}
exit=0
```

Kontrola negatywna — pięć klatek z samym HUD-em:

```
  fail cab_2000m       ink=0.0127 std=0.0819  <- obraz pusty/jednorodny: poziomy=235
  fail chase_2000m     ink=0.0127 std=0.0819  <- obraz pusty/jednorodny: poziomy=235
  fail outside_2000m   ink=0.0127 std=0.0819  <- obraz pusty/jednorodny: poziomy=235
  fail curve_R91_chase ink=0.0127 std=0.0819  <- obraz pusty/jednorodny: poziomy=235
  fail seam_c01_c02    ink=0.0127 std=0.0819  <- obraz pusty/jednorodny: poziomy=235
[WYNIK] fail — {'total': 6, 'pass': 0, 'fail': 6, 'new_baseline': 0}
exit=1
```

Kontrola negatywna jest **w workflow**, nie tylko tutaj: krok „Negative control of the
screenshot check" renderuje klatkę `--no-geometry` i wywraca job, gdyby ta klatka
przeszła kontrolę zawartości.

```
$ python3 tools/tests/test_all.py
  372/372 przeszło
```

Pięć nowych testów w `tools/tests/test_visual.py`, bez Godota i bez Blendera —
sprawdzają, że próg leży **między** zmierzoną pustką a zmierzonym minimum, że zestaw
jest oznaczony jako silnikowy i że kontrola **nie opiera się** na `distinct_levels`.

## 7. Co widziałem na zrzutach

**`cab_2000m`** — wnętrze tunelu uciekające w głąb, HUD: 80,0 km/h, a = 0,36 m/s²,
chainage 2000,1 / 6686,7 m, „Comte de Flandre za 55 m", nastawnik 1,00, hamulec 0,00.
Kadr asymetryczny: więcej ściany po prawej niż po lewej, zgodnie z odsunięciem toru.

**`outside_2000m`** — skład widziany z sąsiedniego toru: człony M7 z wyciętymi otworami
drzwiowymi, wyraźnie węższy od tunelu, oświetlony reflektorem od czoła.

**`NEG_no_geometry`** — czarna klatka z **działającym** HUD-em: te same poprawne liczby,
zero świata. To jest dokładnie ta klatka, którą stary `wc -l` przyjmował.

## 8. Czego świadomie nie zrobiono

- **Nie zapisano baseline'u**, mimo że odtwarzalność między maszynami okazała się
  bajtowa (§3). `--accept-baseline` nigdy nie dzieje się automatycznie (T-012), a
  zatwierdzenie pierwszego baseline'u to osobna, jawna decyzja — nie skutek uboczny
  zielonego przebiegu.
- **Nie ruszono fizyki ani parytetu T-400.** Zmiana w `src/Game/` tylko dopisuje plik
  metadanych; `TrainController` i telemetria są nietknięte.
- **Nie dodano ujęć.** Pięć istniejących pochodzi z T-400 i mają uzasadnienie
  w `reports/T-400-first-run.md`; dobieranie nowych bez pytania, na co mają odpowiadać,
  byłoby mnożeniem klatek, nie kontroli.
- **Nie porównano zrzutów Godota z renderami Blendera tej samej geometrii.** Kuszące,
  ale to dwa różne modele oświetlenia i materiałów — różnica nie znaczyłaby nic.
