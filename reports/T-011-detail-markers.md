# T-011 · Rozstawianie detali wzdłuż osi

**Zmierzone na commicie:** `c6eb1ca`

Stan: **2026-09-02**. Wyjście: `tools/track/detail_layout.py`,
`tools/blender/detail_markers.py`, `tools/blender/placement.py` (`marker_clearances`),
`tools/tests/test_detail_layout.py`. Na poprawionym kilometrażu stacji
(`reports/axis-station-chainage.md`).

---

## 1. Co zrobiłem

Rozstawianie znaczników wzdłuż osi, rozcięte na dwie części po linii, która w tym
projekcie decyduje o wszystkim: **co wychodzi z danych, a co jest założeniem**.

| moduł | co robi | ile założeń |
|---|---|---:|
| `tools/track/detail_layout.py` | liczy **kilometraże** — gdzie coś ma stanąć i dlaczego | **0** |
| `tools/blender/detail_markers.py` | buduje bryły: rozmiar, strona, odsunięcie | 4, wypisywane |

Pierwsza połowa nie ma **ani jednej** decyzji projektowej i testuje się bez Blendera.
Druga ma dokładnie cztery i **każda jest sprawdzana**, nie tylko zadeklarowana (§4).

## 2. Trzy rodzaje miejsc

```
$ python3 tools/track/detail_layout.py --axis data/track/L1_A.json \
    --out build/L1_A-details.json --brake-from-kmh 72

[DETALE] L1_A: 6686.4 m osi, 89 miejsc — brake 11, hectometre 66, station 12
[DETALE] punkt hamowania: 72 km/h, hamulec 1.10 m/s², zryw 0.75 m/s³ -> 196.39 m
[DETALE] zapisano build/L1_A-details.json
```

- **`hectometre`** — co 100 m od zera. Konwencja kolejowa, nie wybór.
- **`station`** — kilometraż z osi, z nazwą i `stop_id`. `stop_id` jest tu po to samo,
  co w T-113: żeby dało się złączyć z rozkładem po identyfikatorze, nie po nazwie.
- **`brake`** — punkt, w którym trzeba zacząć hamować. Liczony solverem z T-311,
  tym samym wzorem zamkniętym z ograniczeniem zrywu.

Z 67 wielokrotności stu metrów zostaje 66: hektometr w zerze przegrywa ze stacją
Gare de l'Ouest. Pierwszeństwo jest jawne — **stacja bije punkt hamowania, punkt
hamowania bije hektometr** — bo dwa znaczniki w jednym miejscu to dwa słupki w jednym
punkcie.

## 3. Punkt hamowania jest jedynym miejscem z założeniem — i nie ma domyślnego

`--brake-from-kmh` **nie ma wartości domyślnej**. Prędkość dopuszczalna na torze nie ma
źródła — to jest wynik R-006, gdzie prześledziłem 72 km/h do notatki prasowej z 2008 r.
Bez podanej prędkości narzędzie po prostu **nie stawia punktów hamowania**, zamiast
po cichu wybrać liczbę:

```python
assert report["brake_from_kmh"] is None
assert report["braking_distance_m"] is None   # None, nie 0.0
```

Zero znaczyłoby „hamowanie na zerowej drodze". `None` znaczy „nie liczyliśmy".

Punkt, który wypadłby **przed poprzednią stacją**, jest pomijany z podanym powodem,
a nie przesuwany w prawo. Przesunięcie udawałoby, że prędkość jest na tym odcinku
osiągalna; pominięcie mówi wprost, że odcinek jest za krótki.

## 4. Cztery założenia, które są sprawdzane

Rozmiar słupka, jego strona i odsunięcie od osi nie wychodzą z żadnych danych. Ale
**da się je sprawdzić**: słupek postawiony byle gdzie albo wchodzi w skrajnię pojazdu,
albo przebija ścianę tunelu.

```
[ZAŁOŻENIE] strona=right odsunięcie=2.10 m podstawa=-0.10 m przekrój=0.12x0.20 m
[ZAŁOŻENIE] wysokości: brake 1.00 m, hectometre 0.60 m, station 1.60 m
[LUZ] do skrajni pojazdu: +0.350 m
[LUZ] do ściany tunelu box_double: +1.100 m
```

Luz jest liczony w **najgorszym punkcie bryły**, nie w jej środku: o luz do skrajni
decyduje krawędź bliższa osi, o luz do ściany — dalsza i najwyższa. Liczenie od środka
zawyżałoby luz o pół szerokości słupka i przepuściło bryłę, która realnie wchodzi
w skrajnię; osobny test to przypina.

Skrypt **odmawia zapisu** przy ujemnym luzie. Obie kontrole negatywne działają:

```
$ ... --offset-m 1.60
[LUZ] do skrajni pojazdu: -0.150 m
BŁĄD: słupek wchodzi w skrajnię pojazdu o 0.150 m — zwiększ --offset-m

$ ... --offset-m 4.70
[LUZ] do ściany tunelu box_double: -0.100 m
BŁĄD: słupek przebija ścianę profilu box_double o 0.100 m — zmniejsz --offset-m

$ ls build/NEG1.glb build/NEG2.glb
żaden negatyw nie zapisał GLB
```

To jest cała różnica między „dobrałem ładny odstęp" a „odstęp mieści się między
skrajnią a ścianą, i oto o ile".

Kontrola luzu początkowo mieszkała w skrypcie Blenderowym, czyli była **nietestowalna**.
Przeniosłem ją do `placement.py` jako `marker_clearances` — czysty Python, bez `bpy`,
zgodnie z podziałem, który ten projekt stosuje wszędzie indziej.

## 5. Pusty render, mimo że skrypt przeszedł bez błędu

Pierwszy render kontrolny wyszedł **całkowicie pusty**, choć skrypt zakończył się
kodem 0 i zapisał GLB o rozmiarze 98 308 B. To jest dokładnie przypadek, przed którym
ostrzega `CLAUDE.md` §5, i gdybym poprzestał na „skrypt się wykonał", oddałbym nic.

Geometria była na miejscu — sprawdziłem to osobno:

```
OBIEKTY 89  WIERZ 2136  ŚCIANY 1068
BBOX [-2.03, -1070.16, -0.1] [5447.17, 907.81, 1.5]
ROZMIAR [5449.2, 1977.97, 1.6]
```

Przyczyną było kadrowanie: `render_check.py` obejmuje całą obwiednię, więc słupek
0,2 m w kadrze 5,4 km ma **0,03 piksela**. Dlatego skrypt dostał `--from-m` / `--to-m`.
Przy oknie 400 m widać sześć punktów, ale nadal po pół piksela; dopiero okno 45 m
daje słupki o realnej wielkości.

## 6. Weryfikacja — rzeczywiste wyjście

```
$ python3 tools/tests/test_all.py
  446/446 przeszło          (25 nowych)

$ blender --background --python tools/blender/detail_markers.py -- \
    --axis data/track/L1_A.json --layout build/L1_A-details.json \
    --profile box_double --out build/L1_A-markers.glb

[ZNACZNIKI] L1_A: 89 słupków (cała oś) — brake 11, hectometre 66, station 12
[LUZ] do skrajni pojazdu: +0.350 m
[LUZ] do ściany tunelu box_double: +1.100 m
[ZNACZNIKI] zapisano build/L1_A-markers.glb (98308 B)
```

### Co widzę na renderach

Okno 3695–3740 m, czyli hektometr 3,7 i stacja Gare Centrale (3731,85 m):

| render | co widzę |
|---|---|
| `NEAR_iso.png` | dwa słupki stojące wzdłuż osi, **wyraźnie różnej wysokości** — niższy to hektometr (0,60 m), wyższy tabliczka stacyjna (1,60 m). Rodzaje rozróżnialne bez koloru, o co chodziło, bo render kontrolny jest w skali szarości |
| `NEAR_side.png` | oba słupki pionowe, podstawy na tym samym poziomie, prawy wyraźnie wyższy. Żaden się nie przechyla, więc obrót z cięciwy jest poprawny |
| `WIN_iso.png` (okno 400 m) | sześć punktów ułożonych wzdłuż jednej linii, w odstępach zgodnych z hektometrami — rozstawienie idzie po osi, a nie po prostej |
| `MARKERS_iso.png` (cała oś) | **pusto** — i to jest opisany wyżej wynik kadrowania, nie brak geometrii |

## 7. Czego świadomie nie zrobiłem

- **Nie modelowałem wyglądu.** Słupek jest prostopadłościanem. Kierunek artystyczny to
  T-902 i decyzja estetyczna, której `CLAUDE.md` §8 zabrania mi podejmować.
- **Nie ma napisów.** Tabliczka stacyjna nie nosi nazwy stacji jako geometrii — tekst
  w 3D to font, czyli licencja, czyli `docs/03-legal.md`. Nazwa jest w danych układu.
- **Nie ruszałem trzeciej szyny, koryt kablowych ani oświetlenia.** To był drugi
  i trzeci wariant tego zadania w pytaniu do właściciela; oba czekają na R-005 (#35)
  i T-902 (#39).
- **Nie wpiąłem znaczników do sceny Godota ani do pipeline'u T-210.** Generator stoi
  osobno; wpięcie to osobny krok, po decyzji, czy znaczniki mają być własnym chunkiem,
  czy częścią tunelu.

## 8. Co zauważyłem, ale nie tknąłem

- **`render_check.py` nie nadaje się do drobnych detali** i nie ma jak tego powiedzieć
  wołającemu — pusty render wygląda identycznie jak brak geometrii. `tools/visual/`
  ma kamery ograniczone zasięgiem (`depth_m`, `slab_radius_m`) zrobione dokładnie na to;
  zestaw kamer dla detali byłby naturalnym następnym krokiem.
- **Odsunięcie 2,10 m ma zapas 0,35 m do skrajni i 1,10 m do ściany** — to zostawia
  sporo miejsca, ale nie wiem, ile go realnie potrzeba, bo nie znam przekroju kanału
  kablowego ani wymagań STIB na skrajnię obsługową. Po R-005 tę liczbę trzeba przeliczyć.
- **Hektometry liczą się od początku PAKIETU, nie od początku linii.** Dla pakietu A
  zero wypada na Gare de l'Ouest. Prawdziwy kilometraż STIB ma własne zero, którego
  repo nie zna — i to jest kolejna pozycja do R-005 albo do kontaktu ze STIB.
